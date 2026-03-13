"""
Tests for django_strava views.

The Strava OAuth flow and API calls are mocked with unittest.mock so that no
real network requests are made.  Each view is exercised via Django's test
client configured against the minimal URL conf in tests/urls.py.
"""

import datetime
import json
from unittest.mock import MagicMock, patch

import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from django_strava.models import Activity, StravaAthlete, StravaToken, WebhookEvent


# ---------------------------------------------------------------------------
# Helpers shared across test cases
# ---------------------------------------------------------------------------


def make_user(username="cyclist", password="pass"):
    return User.objects.create_user(username=username, password=password)


def make_token(user):
    return StravaToken.objects.create(
        user=user,
        access_token="acc_test",
        refresh_token="ref_test",
        expires_in=21600,
        expires_at=9999999999,
    )


def make_athlete(token, strava_id=7):
    return StravaAthlete.objects.create(
        user=token,
        id=strava_id,
        firstname="Cy",
        lastname="Clist",
        username="cyclist",
    )


def make_activity(athlete, activity_id=101):
    return Activity.objects.create(
        athlete=athlete,
        id=activity_id,
        name="Test Ride",
        type="Ride",
        start_date=datetime.datetime(2024, 6, 1, 8, 0, 0, tzinfo=pytz.UTC),
        elapsed_time=5400,
    )


# ---------------------------------------------------------------------------
# URL resolution
# ---------------------------------------------------------------------------


class UrlResolutionTest(TestCase):
    def test_login_url_resolves(self):
        url = reverse("stravalogin")
        self.assertEqual(url, "/strava/login")

    def test_success_url_resolves(self):
        url = reverse("stravasuccess")
        self.assertEqual(url, "/strava/success")

    def test_activity_url_resolves(self):
        url = reverse("stravaactivitypage", kwargs={"activity_id": 42})
        self.assertEqual(url, "/strava/activity/42/")

    def test_webhook_url_exists(self):
        from django.urls import resolve

        match = resolve("/strava/webhook")
        self.assertEqual(match.func.__name__, "webhook")


# ---------------------------------------------------------------------------
# login view
# ---------------------------------------------------------------------------


class LoginViewTest(TestCase):
    def test_login_redirects_to_strava(self):
        response = self.client.get(reverse("stravalogin"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("strava.com/oauth/authorize", response["Location"])

    def test_login_redirect_contains_client_id(self):
        response = self.client.get(reverse("stravalogin"))
        # pyproject sets STRAVA_CLIENT_ID = "fake-client-id" in test settings
        self.assertIn("fake-client-id", response["Location"])

    def test_login_redirect_includes_scope(self):
        response = self.client.get(reverse("stravalogin"))
        self.assertIn("activity%3Aread_all", response["Location"])


# ---------------------------------------------------------------------------
# success view
# ---------------------------------------------------------------------------


class SuccessViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_success_without_code_raises_404(self):
        response = self.client.get(reverse("stravasuccess"))
        self.assertEqual(response.status_code, 404)

    @patch("django_strava.views.requests.post")
    @patch("django_strava.views.threading.Thread")
    def test_success_with_valid_code_renders_template(self, mock_thread, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "new_acc",
                "refresh_token": "new_ref",
                "expires_in": 21600,
                "expires_at": 9999999999,
                "athlete": {
                    "id": 55,
                    "firstname": "New",
                    "lastname": "User",
                    "username": "newuser",
                    "city": None,
                    "state": None,
                },
            },
        )
        # setDaemon is called on the thread; mock the full chain
        mock_thread.return_value = MagicMock()

        response = self.client.get(reverse("stravasuccess"), {"code": "auth_code_123"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "strava/success.html")

    @patch("django_strava.views.requests.post")
    def test_success_with_failed_oauth_raises_404(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=401,
            text="Unauthorized",
        )
        response = self.client.get(reverse("stravasuccess"), {"code": "bad_code"})
        self.assertEqual(response.status_code, 404)

    @patch("django_strava.views.requests.post")
    def test_success_with_missing_access_token_raises_404(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"error": "invalid_grant"},
        )
        response = self.client.get(reverse("stravasuccess"), {"code": "code_xyz"})
        self.assertEqual(response.status_code, 404)

    @patch("django_strava.views.requests.post")
    @patch("django_strava.views.threading.Thread")
    def test_success_creates_strava_token(self, mock_thread, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "tok_new",
                "refresh_token": "ref_new",
                "expires_in": 3600,
                "expires_at": 9999999999,
                "athlete": {
                    "id": 66,
                    "firstname": "A",
                    "lastname": "B",
                    "username": "ab",
                    "city": None,
                    "state": None,
                },
            },
        )
        mock_thread.return_value = MagicMock()

        self.client.get(reverse("stravasuccess"), {"code": "code_ok"})
        self.assertTrue(StravaToken.objects.filter(user=self.user).exists())

    @patch("django_strava.views.requests.post")
    @patch("django_strava.views.threading.Thread")
    def test_success_creates_strava_athlete(self, mock_thread, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "tok_new2",
                "refresh_token": "ref_new2",
                "expires_in": 3600,
                "expires_at": 9999999999,
                "athlete": {
                    "id": 77,
                    "firstname": "Jane",
                    "lastname": "Doe",
                    "username": "janedoe",
                    "city": None,
                    "state": None,
                },
            },
        )
        mock_thread.return_value = MagicMock()

        self.client.get(reverse("stravasuccess"), {"code": "code_ok2"})
        self.assertTrue(StravaAthlete.objects.filter(id=77).exists())


# ---------------------------------------------------------------------------
# activity view
# ---------------------------------------------------------------------------


class ActivityViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.token = make_token(self.user)
        self.athlete = make_athlete(self.token)
        self.activity = make_activity(self.athlete)
        self.client.force_login(self.user)

    def test_activity_page_returns_200(self):
        response = self.client.get(
            reverse("stravaactivitypage", kwargs={"activity_id": 101})
        )
        self.assertEqual(response.status_code, 200)

    def test_activity_page_uses_correct_template(self):
        response = self.client.get(
            reverse("stravaactivitypage", kwargs={"activity_id": 101})
        )
        self.assertTemplateUsed(response, "strava/activity.html")

    def test_activity_page_contains_name(self):
        response = self.client.get(
            reverse("stravaactivitypage", kwargs={"activity_id": 101})
        )
        self.assertContains(response, "Test Ride")

    def test_activity_page_for_missing_activity_raises_error(self):
        response = self.client.get(
            reverse("stravaactivitypage", kwargs={"activity_id": 99999})
        )
        # DoesNotExist propagates as a 500 in test mode (no catch-all in urls)
        self.assertIn(response.status_code, [404, 500])


# ---------------------------------------------------------------------------
# webhook view
# ---------------------------------------------------------------------------


class WebhookViewTest(TestCase):
    WEBHOOK_URL = "/strava/webhook"

    def _post_event(self, payload):
        return self.client.post(
            self.WEBHOOK_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )

    @patch("django_strava.views.threading.Thread")
    def test_post_creates_webhook_event(self, mock_thread):
        mock_thread.return_value = MagicMock()
        payload = {
            "object_type": "activity",
            "aspect_type": "create",
            "object_id": 111111,
            "owner_id": 999,
            "subscription_id": 1,
            "event_time": 1600000000,
            "updates": {},
        }
        response = self._post_event(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 1)

    @patch("django_strava.views.threading.Thread")
    def test_post_stores_correct_integer_choices(self, mock_thread):
        mock_thread.return_value = MagicMock()
        payload = {
            "object_type": "athlete",
            "aspect_type": "update",
            "object_id": 222222,
            "owner_id": 999,
            "subscription_id": 1,
            "event_time": 1600000001,
            "updates": {"title": "Renamed"},
        }
        self._post_event(payload)
        event = WebhookEvent.objects.first()
        self.assertEqual(event.object_type, WebhookEvent.ObjectType.athlete)
        self.assertEqual(event.aspect_type, WebhookEvent.AspectType.update)

    @patch("django_strava.views.threading.Thread")
    def test_post_stores_updates_as_json(self, mock_thread):
        mock_thread.return_value = MagicMock()
        payload = {
            "object_type": "activity",
            "aspect_type": "update",
            "object_id": 333333,
            "owner_id": 999,
            "subscription_id": 1,
            "event_time": 1600000002,
            "updates": {"title": "Evening Run"},
        }
        self._post_event(payload)
        event = WebhookEvent.objects.first()
        self.assertEqual(event.updates["title"], "Evening Run")

    def test_get_webhook_returns_challenge(self):
        response = self.client.get(
            self.WEBHOOK_URL,
            {
                "hub.mode": "subscribe",
                "hub.challenge": "abc123",
                "hub.verify_token": "herecomescooldad",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["hub.challenge"], "abc123")

    def test_unsupported_method_raises_404(self):
        response = self.client.put(
            self.WEBHOOK_URL, data="{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# fetch_or_update helper (background task logic, no real API calls)
# ---------------------------------------------------------------------------


class FetchOrUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user("runner2")
        self.token = make_token(self.user)
        self.athlete = make_athlete(self.token, strava_id=77)

    def _make_event(self, object_type, aspect_type, object_id, updates=None):
        return WebhookEvent.objects.create(
            object_type=object_type,
            aspect_type=aspect_type,
            object_id=object_id,
            owner_id=77,
            subscription_id=1,
            event_time=1600000000,
            updates=updates or {},
        )

    def test_delete_event_removes_existing_activity(self):
        from django_strava.views import fetch_or_update

        make_activity(self.athlete, activity_id=201)
        event = self._make_event(
            object_type=WebhookEvent.ObjectType.activity,
            aspect_type=WebhookEvent.AspectType.delete,
            object_id=201,
        )
        fetch_or_update(event.id)
        self.assertEqual(Activity.objects.filter(pk=201).count(), 0)

    def test_delete_event_marks_processed(self):
        from django_strava.views import fetch_or_update

        make_activity(self.athlete, activity_id=202)
        event = self._make_event(
            object_type=WebhookEvent.ObjectType.activity,
            aspect_type=WebhookEvent.AspectType.delete,
            object_id=202,
        )
        fetch_or_update(event.id)
        event.refresh_from_db()
        self.assertTrue(event.processed)

    def test_update_event_renames_existing_activity(self):
        from django_strava.views import fetch_or_update

        make_activity(self.athlete, activity_id=203)
        event = self._make_event(
            object_type=WebhookEvent.ObjectType.activity,
            aspect_type=WebhookEvent.AspectType.update,
            object_id=203,
            updates={"title": "Renamed Ride"},
        )
        fetch_or_update(event.id)
        a = Activity.objects.get(pk=203)
        self.assertEqual(a.name, "Renamed Ride")

    def test_update_event_marks_processed(self):
        from django_strava.views import fetch_or_update

        make_activity(self.athlete, activity_id=204)
        event = self._make_event(
            object_type=WebhookEvent.ObjectType.activity,
            aspect_type=WebhookEvent.AspectType.update,
            object_id=204,
            updates={"title": "New Name"},
        )
        fetch_or_update(event.id)
        event.refresh_from_db()
        self.assertTrue(event.processed)

    @patch("django_strava.views.get_single_activity")
    def test_create_event_triggers_api_fetch(self, mock_get):
        from django_strava.views import fetch_or_update

        event = self._make_event(
            object_type=WebhookEvent.ObjectType.activity,
            aspect_type=WebhookEvent.AspectType.create,
            object_id=999,
        )
        fetch_or_update(event.id)
        mock_get.assert_called_once_with(owner_id=77, activity_id=999)

    @patch("django_strava.views.get_single_activity")
    def test_update_event_fetches_when_activity_missing(self, mock_get):
        from django_strava.views import fetch_or_update

        # No Activity with id=888 in DB → should fall back to API fetch
        event = self._make_event(
            object_type=WebhookEvent.ObjectType.activity,
            aspect_type=WebhookEvent.AspectType.update,
            object_id=888,
            updates={"title": "Ghost"},
        )
        fetch_or_update(event.id)
        mock_get.assert_called_once_with(owner_id=77, activity_id=888)
