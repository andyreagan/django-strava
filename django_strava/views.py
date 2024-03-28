import datetime
import json
import logging
import urllib
import pytz
import threading
import copy

import requests
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpRequest, Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from main import settings
from .models import Activity, StravaAthlete, StravaToken, WebhookEvent

# reference on the strava handshake:
# https://developers.strava.com/docs/authentication/
# reference on subscribing to webhooks:
# https://developers.strava.com/docs/webhooks/
# reference on rate limits:
# https://developers.strava.com/docs/rate-limits/

# using threading for background tasks, could also do https://python-rq.org/

# Get an instance of a logger
logger = logging.getLogger(__name__)


def print_debug(_, debug=settings.DEBUG):
    logging.info(_)
    if debug:
        print(_)


def refresh_access_token(st: StravaToken) -> None:
    data = {
        "client_id": settings.STRAVA_CLIENT_ID,
        "client_secret": settings.STRAVA_CLIENT_SECRET,
        "refresh_token": st.refresh_token,
        "grant_type": "refresh_token",
    }

    # r = requests.post("https://www.strava.com/api/v3/oauth/token", data=data)
    r = requests.post("https://www.strava.com/oauth/token", data=data)
    # rather than raise an application error, pass that error back to the user:
    # r.raise_for_status()
    if r.status_code != requests.codes.ok:
        print_debug(f"Error in strava oauth handshake: {r.text}")

    response = r.json()
    print_debug(response)
    for key in {"access_token", "expires_at", "refresh_token"}:
        if key not in response:
            print_debug(f"No {key} in returned response: {response}.")
            return None

    st.access_token = response['access_token']
    st.expires_at = response['expires_at']
    st.refresh_token = response['refresh_token']
    # not confident we'll get this one back...
    if 'expires_in' in response:
        st.expires_in = response['expires_in']

    st.save()


def login(request: HttpRequest) -> HttpResponseRedirect:
    '''
    Redirect to authenticate to with Strava.
    '''
    data = {
        "client_id": settings.STRAVA_CLIENT_ID,
        "redirect_uri": "https://dashboard.aws.andyreagan.com/strava/success",
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "activity:read_all",
        "state": "",
    }
    if settings.DEBUG:
        data["redirect_uri"] = "http://localhost:8000/strava/success"
    return HttpResponseRedirect(
        "https://www.strava.com/oauth/authorize" + "?" + urllib.parse.urlencode(data)
    )


def save_activity_from_dict(activity: dict, athlete: StravaAthlete) -> None:
    '''
    Save an activity to an athlete's profile.
    Activity dict must contain the required fields of Activity model:
    - id: int
    - name: char
    - type: char
    - start_date: datetime
    - elapsed_time: int
    '''
    model_fields = {field.name for field in Activity._meta.get_fields()}
    activity["athlete"] = athlete

    # fix up dates
    # parse them both as UTC to start
    activity["start_date"] = datetime.datetime.strptime(
        activity["start_date"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=pytz.UTC)
    activity["start_date_local"] = datetime.datetime.strptime(
        activity["start_date_local"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=pytz.UTC)
    # then compute the offset and set that instead
    # there may be a utc_offset in the activity response, but I won't rely on it
    activity["start_date_local"] = activity["start_date_local"].replace(tzinfo=datetime.timezone(activity["start_date_local"] - activity["start_date"]))

    # flatten lat/long
    if 'start_latlng' in activity and type(activity.get('start_latlng')) == list and len(activity.get('start_latlng')) == 2:
        activity['start_latitude'] = activity['start_latlng'][0]
        activity['start_longitude'] = activity['start_latlng'][1]
    if 'end_latlng' in activity and type(activity.get('end_latlng')) == list and len(activity.get('end_latlng')) == 2:
        activity['end_latitude'] = activity['end_latlng'][0]
        activity['end_longitude'] = activity['end_latlng'][1]

    activity_fields = set(activity.keys())

    s = Activity(
        **{field: activity[field] for field in (model_fields & activity_fields)}
    )
    s.save()

    activity_missing = (model_fields - activity_fields)
    activity_extra = (activity_fields - model_fields)
    logger.info(f"{activity_missing=}")
    logger.info(f"{activity_extra=}")


def save_activities_from_response(activity_list: list, athlete: StravaAthlete) -> None:
    '''
    '''
    for activity in activity_list:
        save_activity_from_dict(activity, athlete)


def get_athlete_activities(athlete: StravaAthlete, max_requests: int=10) -> None:
    per_page = 200
    refresh_access_token(athlete.user)
    data = {
        "access_token": athlete.user.access_token,
    }

    more_activities = True
    i = 0
    while more_activities and (i < max_requests):
        i += 1
        url = (
            "https://www.strava.com/api/v3/athlete/activities"
            + "?"
            + urllib.parse.urlencode({"per_page": per_page, "page": i})
        )
        r = requests.get(url, data=data)
        activity_list = r.json()
        save_activities_from_response(activity_list, athlete)
        more_activities = len(activity_list) == per_page


def get_single_activity(owner_id: int, activity_id: int) -> None:
    athlete = StravaAthlete.objects.get(id=owner_id)
    refresh_access_token(athlete.user)
    data = {
        "access_token": athlete.user.access_token,
    }
    url = (
        f"https://www.strava.com/api/v3/activities/{activity_id}"
        + "?"
        + urllib.parse.urlencode({"include_all_efforts": False})
    )
    r = requests.get(url, data=data)
    activity = r.json()
    print_debug(activity)
    save_activity_from_dict(activity, athlete)


def success(request: HttpRequest) -> HttpResponse:
    if "code" not in request.GET:
        raise Http404 (f"No access code returned: {request.GET}.")

    data = {
        "client_id": settings.STRAVA_CLIENT_ID,
        "client_secret": settings.STRAVA_CLIENT_SECRET,
        "code": request.GET["code"],
        "grant_type": "authorization_code",
    }
    r = requests.post("https://www.strava.com/oauth/token", data=data)
    # rather than raise an application error, pass that error back to the user:
    # r.raise_for_status()
    if r.status_code != requests.codes.ok:
        raise Http404 (f"Error in strava oauth handshake: {r.text}")

    athlete = r.json()
    if "access_token" not in athlete:
        raise Http404 (f"No access token returned response: {athlete}.")

    # update these
    request.user.first_name = athlete["athlete"]["firstname"]
    request.user.last_name = athlete["athlete"]["lastname"]
    # request.user.email = athlete["athlete"]["email"]
    request.user.save()

    # update the token too
    (s, created) = StravaToken.objects.get_or_create(user=request.user)
    s.access_token = athlete.get("access_token")
    s.refresh_token = athlete.get("refresh_token")
    s.expires_in = athlete.get("expires_in")
    s.expires_at = athlete.get("expires_at")
    s.save()

    # save user
    fields = [x.name for x in StravaAthlete._meta.get_fields()]
    d = {f: athlete["athlete"][f] for f in fields if f in athlete["athlete"]}
    d["user"] = s
    (ath, created) = StravaAthlete.objects.get_or_create(**d)

    ath.save()
    # get_athlete_activities(ath, max_requests=1)
    t = threading.Thread(target=get_athlete_activities, args=[ath, 100])
    t.setDaemon(True)
    t.start()

    return render(request, "strava/success.html", athlete)


@csrf_exempt
def webhook(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        logger.info(request.body)
        d = json.loads(request.body, strict=False)
        d["object_type"] = {v.lower(): k for k, v in WebhookEvent.ObjectType.choices}[
            d["object_type"]
        ]
        d["aspect_type"] = {v.lower(): k for k, v in WebhookEvent.AspectType.choices}[
            d["aspect_type"]
        ]
        w = WebhookEvent(**d)
        w.save()
        # pass the event id rather than the object (why?)
        t = threading.Thread(target=fetch_or_update,args=[w.id])
        t.setDaemon(True)
        t.start()
        return HttpResponse("")
    elif request.method == "GET":
        logger.info(request.GET)
        request.GET["hub.mode"] == "subscribe"
        challenge = request.GET["hub.challenge"]
        request.GET["hub.verify_token"] == "herecomescooldad"

        return JsonResponse({"hub.challenge": challenge})
    else:
        logger.error(request)
        raise Http404 ("Only know how to respond to GET and POST requests.")


def fetch_or_update(w_id: int) -> None:
    w = WebhookEvent.objects.get(id=w_id)
    if w.object_type == 1:  # activity = 1
        if w.aspect_type == 1:  # create = 1
            print_debug("create, so go get the activity")
            # go get the activity
            get_single_activity(owner_id=w.owner_id, activity_id=w.object_id)
            # TODO: run any other background tasks (refresh stats, etc)
        elif w.aspect_type == 2:  # update = 2
            print_debug("update, so go get the activity")
            # go fetch the activity from the db
            # update if we have it
            activities = Activity.objects.filter(id=w.object_id)
            if len(activities) == 1:
                print_debug("found it")
                activity = activities[0]
                model_fields = {field.name for field in Activity._meta.get_fields()}
                updates =  copy.deepcopy(w.updates)
                if 'title' in updates:
                    updates['name'] = updates['title']
                for k, v in updates.items():
                    if k in model_fields:
                        print_debug(f"setting field {k} in activity id {w.object_id}")
                        setattr(activity, k, v)
                    else:
                        print_debug(f"can't set field {k} in activity id {w.object_id}")
                        pass
                activity.save()
            else: # else go get it
                print_debug("it was an update, but we didn't have it, so go get it")
                get_single_activity(owner_id=w.owner_id, activity_id=w.object_id)
        else:  # delete = 3
            activities = Activity.objects.filter(id=w.object_id)
            if len(activities) == 1:
                activity = activities[0]
                activity.delete()
        w.processed = True
        w.save()
    else:  # athlete = 1
        pass


def activity(request: HttpRequest, activity_id: int) -> HttpResponse:
    this_activity = request.user.stravatoken.stravaathlete.activity_set.get(id=activity_id)
    activity_dict = {x.name: x.value_from_object(this_activity) for x in Activity._meta.get_fields()}
    return render(request, "strava/activity.html", {"activity": this_activity, "activity_dict": activity_dict})
