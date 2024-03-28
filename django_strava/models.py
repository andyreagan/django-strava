# Create your models here.
from django.contrib.auth.models import User
from django.db import models


class StravaToken(models.Model):
    """Adds a token to a django User."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=1024)
    refresh_token = models.CharField(max_length=1024)
    expires_in = models.IntegerField(null=True)
    expires_at = models.IntegerField(null=True)

    def __str__(self):
        return self.user.username


class StravaAthlete(models.Model):
    """Wraps around the API for an athletes summary:

    https://developers.strava.com/docs/reference/#api-models-SummaryAthlete"""

    user = models.OneToOneField(StravaToken, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(null=True)
    all_data_fetched_initial = models.BooleanField(default=False)
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=1024, null=True)
    firstname = models.CharField(max_length=1024, null=True)
    lastname = models.CharField(max_length=1024, null=True)
    city = models.CharField(max_length=1024, null=True)
    state = models.CharField(max_length=1024, null=True)
    country = models.CharField(max_length=1024, null=True)
    sex = models.CharField(max_length=2, null=True)
    premium = models.BooleanField(default=False)
    # 'created_at': '2011-09-01T00:30:24Z',
    # 'updated_at': '2018-06-07T01:11:19Z',
    # 'badge_type_id': 1,
    profile_medium = models.URLField(max_length=1024, null=True)
    profile = models.URLField(max_length=1024, null=True)
    # 'friend': None,
    # 'follower': None,
    email = models.EmailField(max_length=1024, null=True)

    def __str__(self):
        return "%s %s (%s)" % (self.firstname, self.lastname, self.username)


class Activity(models.Model):
    """
    Based on:
    https://developers.strava.com/docs/reference/#api-models-SummaryActivity

    TODO: pull an activity summary, and an activity detail to see all possible fields.
    """

    athlete = models.ForeignKey(StravaAthlete, on_delete=models.CASCADE)

    # required
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=1024)
    type = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    elapsed_time = models.IntegerField()
    fetched_detail = models.BooleanField(default=False)
    fetched_streams = models.BooleanField(default=False)

    # change to date
    start_date_local = models.DateTimeField(null=True)

    # the others, changed a few int -> float:
    elev_high = models.FloatField(null=True)
    average_temp = models.FloatField(null=True)
    total_photo_count = models.IntegerField(null=True)
    athlete_count = models.IntegerField(null=True)
    has_heartrate = models.BooleanField(default=False)
    total_elevation_gain = models.FloatField(null=True)
    average_cadence = models.FloatField(null=True)
    max_heartrate = models.FloatField(null=True)
    kudos_count = models.IntegerField(null=True)
    max_speed = models.FloatField(null=True)
    utc_offset = models.FloatField(null=True)
    gear_id = models.CharField(max_length=1024, null=True)
    location_country = models.CharField(max_length=1024, null=True)
    visibility = models.CharField(max_length=1024, null=True)
    comment_count = models.IntegerField(null=True)
    commute = models.BooleanField(default=False)
    private = models.BooleanField(default=False)
    moving_time = models.IntegerField(null=True)
    start_latitude = models.FloatField(null=True)
    start_longitude = models.FloatField(null=True)
    end_latitude = models.FloatField(null=True)
    end_longitude = models.FloatField(null=True)
    distance = models.FloatField(null=True)
    upload_id = models.IntegerField(null=True)
    average_speed = models.FloatField(null=True)
    elev_low = models.FloatField(null=True)
    timezone = models.CharField(max_length=1024, null=True)
    calories = models.FloatField(null=True)
    device_name = models.CharField(max_length=1024, null=True)
    description = models.TextField(null=True)
    trainer = models.BooleanField(default=False)
    achievement_count = models.IntegerField(null=True)
    pr_count = models.IntegerField(null=True)
    perceived_exertion = models.FloatField(null=True)
    flagged = models.BooleanField(default=False)
    average_heartrate = models.FloatField(null=True)
    manual = models.BooleanField(default=False)
    prefer_perceived_exertion = models.BooleanField(default=False, null=True)
    photo_count = models.IntegerField(null=True)
    has_kudoed = models.BooleanField(default=False)
    workout_type = models.IntegerField(null=True)
    average_watts = models.FloatField(null=True)
    kilojoules = models.FloatField(null=True)
    device_watts = models.BooleanField(default=False)
    max_watts = models.FloatField(null=True)
    weighted_average_watts = models.FloatField(null=True)

    # things I won't both to collect:
    # heartrate_opt_out = models.BooleanField(default=False)
    # display_hide_heartrate_option = models.BooleanField(default=False)
    # resource_state = models.IntegerField(null=True)
    # external_id = models.CharField(max_length=1024, null=True)
    # upload_id_str = models.CharField(max_length=1024, null=True)
    # from_accepted_tag = models.BooleanField(default=False)
    # embed_token = models.CharField(max_length=1024, null=True)

    # things with datatypes that I won't store:
    # {k for k, v in example_data.items() if type(v) == list}
    # {'available_zones',
    #  'best_efforts',
    #  'end_latlng',
    #  'laps',
    #  'segment_efforts',
    #  'splits_metric',
    #  'splits_standard',
    #  'start_latlng'}
    # {k for k, v in example_data.items() if type(v) == dict}
    # {'athlete', 'gear', 'map', 'photos', 'similar_activities'}

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-start_date"]

    """
    Based on:
    https://developers.strava.com/docs/reference/#api-models-StreamSet

    Should be returned by:
    https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams
    """

    # could store the streams as binary numpy objects
    # see: https://stackoverflow.com/questions/46699238/how-to-make-a-numpy-array-field-in-django
    # binaryfield ref: https://docs.djangoproject.com/en/3.1/ref/models/fields/#binaryfield
    # could alternatively store them as JSON
    # https://docs.djangoproject.com/en/3.1/ref/models/fields/#jsonfield
    # will be simplest to stuff in the JSON
    # the numpy arrays could be faster in/out and doing computation

    # need at least time and distance
    time = models.JSONField(null=True)
    distance = models.JSONField(null=True)
    latlng = models.JSONField(null=True)
    altitude = models.JSONField(null=True)
    heartrate = models.JSONField(null=True)
    cadence = models.JSONField(null=True)
    watts = models.JSONField(null=True)
    temp = models.JSONField(null=True)

    # what is this one (maybe a boolean?):
    # - moving
    # don't need the smooths, compute them if necessary:
    # - velocity_smooth
    # - grade_smooth


    def get_example_data(user_index=0, n_activities=30):
        all_keys = set()
        example_data = dict()
        athlete = User.objects.all()[user_index].stravatoken.stravaathlete
        data = {"access_token": athlete.user.access_token}
        for a in athlete.activity_set.all()[:n_activities]:
            activity_id = a.id
            url = (
            f"https://www.strava.com/api/v3/activities/{activity_id}"
            + "?"
            + urllib.parse.urlencode({"include_all_efforts": False})
            )
            r = requests.get(url, data=data)
            activity = r.json()
            # print(activity)
            # print(keys - set(activity.keys()))
            # print(set(activity.keys()) - keys)
            all_keys = all_keys | set(activity.keys())
            for key in all_keys:
                if key in (activity.keys()) and key not in example_data:
                    example_data[key] = activity[key]

            {k: (v, type(v)) for k, v in example_data.items() if type(v) not in {list, dict, type(None)}}

            print('\n'.join([f'{k} = models.'+{int: 'IntegerField(null=True)', float: 'FloatField(null=True)', bool: 'BooleanField(default=False)', str: 'CharField(max_length=1024, null=True)'}[type(v)] for k, v in example_data.items() if type(v) not in {list, dict, type(None)}]))


class WebhookEvent(models.Model):
    class ObjectType(models.IntegerChoices):
        activity = 1
        athlete = 2

    class AspectType(models.IntegerChoices):
        create = 1
        update = 2
        delete = 3

    object_type = models.IntegerField(
        choices=ObjectType.choices, help_text='Always either "activity" or "athlete."'
    )
    aspect_type = models.IntegerField(
        choices=AspectType.choices, help_text='Always "create," "update," or "delete."'
    )
    object_id = models.BigIntegerField(
        help_text="For activity events, the activity's ID. For athlete events, the athlete's ID."
    )
    updates = models.JSONField(null=True)
    # updates = models.CharField(max_length=1000)
    owner_id = models.BigIntegerField(help_text="The athlete's ID.")
    subscription_id = models.IntegerField(
        help_text="The push subscription ID that is receiving this event."
    )
    event_time = models.BigIntegerField(help_text="The time that the event occurred.")
    processed = models.BooleanField(default=False)
