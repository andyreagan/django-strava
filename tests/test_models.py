"""
Tests for django_strava models.

Covers field existence, __str__ representations, model relationships,
WebhookEvent integer-choice mappings, and the save_activity_from_dict
helper – all without hitting the real Strava API.
"""

import datetime

import pytz
from django.contrib.auth.models import User
from django.test import TestCase

from django_strava.models import Activity, StravaAthlete, StravaToken, WebhookEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(username="testathlete"):
    return User.objects.create_user(username=username, password="pw")


def make_token(user):
    return StravaToken.objects.create(
        user=user,
        access_token="acc_abc123",
        refresh_token="ref_xyz789",
        expires_in=21600,
        expires_at=9999999999,
    )


def make_athlete(token, strava_id=42):
    return StravaAthlete.objects.create(
        user=token,
        id=strava_id,
        firstname="Test",
        lastname="Athlete",
        username="testathlete",
    )


def make_activity(athlete, activity_id=1001):
    return Activity.objects.create(
        athlete=athlete,
        id=activity_id,
        name="Morning Run",
        type="Run",
        start_date=datetime.datetime(2024, 1, 15, 7, 0, 0, tzinfo=pytz.UTC),
        elapsed_time=3600,
    )


# ---------------------------------------------------------------------------
# StravaToken
# ---------------------------------------------------------------------------


class StravaTokenModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.token = make_token(self.user)

    def test_str_returns_username(self):
        self.assertEqual(str(self.token), "testathlete")

    def test_fields_stored_correctly(self):
        t = StravaToken.objects.get(user=self.user)
        self.assertEqual(t.access_token, "acc_abc123")
        self.assertEqual(t.refresh_token, "ref_xyz789")
        self.assertEqual(t.expires_in, 21600)
        self.assertEqual(t.expires_at, 9999999999)

    def test_one_to_one_with_user(self):
        # Attempting to create a second token for the same user should fail.
        with self.assertRaises(Exception):
            StravaToken.objects.create(
                user=self.user,
                access_token="other",
                refresh_token="other",
            )

    def test_token_deleted_with_user(self):
        self.user.delete()
        self.assertEqual(
            StravaToken.objects.filter(access_token="acc_abc123").count(), 0
        )


# ---------------------------------------------------------------------------
# StravaAthlete
# ---------------------------------------------------------------------------


class StravaAthleteModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.token = make_token(self.user)
        self.athlete = make_athlete(self.token)

    def test_str_returns_full_name_and_username(self):
        self.assertEqual(str(self.athlete), "Test Athlete (testathlete)")

    def test_primary_key_is_strava_id(self):
        a = StravaAthlete.objects.get(pk=42)
        self.assertEqual(a.firstname, "Test")

    def test_optional_fields_default_to_none(self):
        a = StravaAthlete.objects.get(pk=42)
        self.assertIsNone(a.city)
        self.assertIsNone(a.state)
        self.assertIsNone(a.country)
        self.assertFalse(a.premium)
        self.assertFalse(a.all_data_fetched_initial)

    def test_reverse_relation_from_token(self):
        # StravaToken → StravaAthlete via the OneToOneField named 'user'
        self.assertEqual(self.token.stravaathlete, self.athlete)

    def test_athlete_deleted_with_token(self):
        self.token.delete()
        self.assertEqual(StravaAthlete.objects.filter(id=42).count(), 0)


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------


class ActivityModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.token = make_token(self.user)
        self.athlete = make_athlete(self.token)
        self.activity = make_activity(self.athlete)

    def test_str_returns_name(self):
        self.assertEqual(str(self.activity), "Morning Run")

    def test_required_fields_stored(self):
        a = Activity.objects.get(pk=1001)
        self.assertEqual(a.name, "Morning Run")
        self.assertEqual(a.type, "Run")
        self.assertEqual(a.elapsed_time, 3600)

    def test_default_boolean_flags(self):
        a = Activity.objects.get(pk=1001)
        self.assertFalse(a.fetched_detail)
        self.assertFalse(a.fetched_streams)
        self.assertFalse(a.commute)
        self.assertFalse(a.private)
        self.assertFalse(a.trainer)
        self.assertFalse(a.manual)

    def test_optional_numeric_fields_default_to_none(self):
        a = Activity.objects.get(pk=1001)
        self.assertIsNone(a.distance)
        self.assertIsNone(a.average_speed)
        self.assertIsNone(a.max_heartrate)
        self.assertIsNone(a.calories)

    def test_json_stream_fields_default_to_none(self):
        a = Activity.objects.get(pk=1001)
        self.assertIsNone(a.time)
        self.assertIsNone(a.latlng)
        self.assertIsNone(a.heartrate)

    def test_json_stream_fields_accept_lists(self):
        self.activity.time = [0, 1, 2, 3]
        self.activity.heartrate = [140, 145, 150, 148]
        self.activity.latlng = [[42.3, -71.1], [42.31, -71.11]]
        self.activity.save()
        a = Activity.objects.get(pk=1001)
        self.assertEqual(a.time, [0, 1, 2, 3])
        self.assertEqual(a.heartrate[2], 150)

    def test_ordering_newest_first(self):
        make_activity(self.athlete, activity_id=1002)
        Activity.objects.filter(pk=1002).update(
            start_date=datetime.datetime(2024, 2, 1, 7, 0, 0, tzinfo=pytz.UTC)
        )
        ids = list(Activity.objects.values_list("pk", flat=True))
        self.assertEqual(ids[0], 1002)

    def test_activity_deleted_with_athlete(self):
        self.athlete.delete()
        self.assertEqual(Activity.objects.filter(pk=1001).count(), 0)

    def test_multiple_activities_per_athlete(self):
        make_activity(self.athlete, activity_id=1002)
        make_activity(self.athlete, activity_id=1003)
        self.assertEqual(self.athlete.activity_set.count(), 3)


# ---------------------------------------------------------------------------
# WebhookEvent
# ---------------------------------------------------------------------------


class WebhookEventModelTest(TestCase):
    def _make_event(self, object_type=1, aspect_type=1, **kwargs):
        defaults = dict(
            object_type=object_type,
            aspect_type=aspect_type,
            object_id=1360128428,
            owner_id=134815,
            subscription_id=120475,
            event_time=1516126040,
            updates={"title": "Messy"},
        )
        defaults.update(kwargs)
        return WebhookEvent.objects.create(**defaults)

    def test_create_event_saved(self):
        event = self._make_event()
        self.assertIsNotNone(event.pk)
        self.assertEqual(WebhookEvent.objects.count(), 1)

    def test_processed_defaults_to_false(self):
        event = self._make_event()
        self.assertFalse(event.processed)

    def test_object_type_choices(self):
        self.assertEqual(WebhookEvent.ObjectType.activity, 1)
        self.assertEqual(WebhookEvent.ObjectType.athlete, 2)

    def test_aspect_type_choices(self):
        self.assertEqual(WebhookEvent.AspectType.create, 1)
        self.assertEqual(WebhookEvent.AspectType.update, 2)
        self.assertEqual(WebhookEvent.AspectType.delete, 3)

    def test_updates_json_field_stored_as_dict(self):
        event = self._make_event(updates={"title": "New Title", "type": "Ride"})
        saved = WebhookEvent.objects.get(pk=event.pk)
        self.assertEqual(saved.updates["title"], "New Title")
        self.assertEqual(saved.updates["type"], "Ride")

    def test_updates_can_be_null(self):
        event = self._make_event(updates=None)
        saved = WebhookEvent.objects.get(pk=event.pk)
        self.assertIsNone(saved.updates)

    def test_choice_label_round_trip(self):
        """Simulate how views.py maps string → int for object/aspect types."""
        obj_map = {v.lower(): k for k, v in WebhookEvent.ObjectType.choices}
        asp_map = {v.lower(): k for k, v in WebhookEvent.AspectType.choices}

        self.assertEqual(obj_map["activity"], 1)
        self.assertEqual(obj_map["athlete"], 2)
        self.assertEqual(asp_map["create"], 1)
        self.assertEqual(asp_map["update"], 2)
        self.assertEqual(asp_map["delete"], 3)


# ---------------------------------------------------------------------------
# save_activity_from_dict helper
# ---------------------------------------------------------------------------


class SaveActivityFromDictTest(TestCase):
    """Tests for the views.save_activity_from_dict utility."""

    def setUp(self):
        self.user = make_user("runner")
        self.token = make_token(self.user)
        self.athlete = make_athlete(self.token, strava_id=99)

    def _base_activity_dict(self, activity_id=5001):
        return {
            "id": activity_id,
            "name": "Easy Ride",
            "type": "Ride",
            "start_date": "2024-03-10T08:00:00Z",
            "start_date_local": "2024-03-10T09:00:00Z",
            "elapsed_time": 7200,
            "distance": 45000.0,
            "moving_time": 7000,
            "total_elevation_gain": 350.5,
            "average_speed": 6.25,
            "max_speed": 12.1,
            "kudos_count": 3,
        }

    def test_saves_activity_to_db(self):
        from django_strava.views import save_activity_from_dict

        save_activity_from_dict(self._base_activity_dict(), self.athlete)
        self.assertEqual(Activity.objects.filter(pk=5001).count(), 1)

    def test_fields_populated_correctly(self):
        from django_strava.views import save_activity_from_dict

        save_activity_from_dict(self._base_activity_dict(), self.athlete)
        a = Activity.objects.get(pk=5001)
        self.assertEqual(a.name, "Easy Ride")
        self.assertEqual(a.type, "Ride")
        self.assertEqual(a.elapsed_time, 7200)
        self.assertAlmostEqual(a.distance, 45000.0)

    def test_latlng_flattened(self):
        from django_strava.views import save_activity_from_dict

        data = self._base_activity_dict(activity_id=5002)
        data["start_latlng"] = [42.36, -71.06]
        data["end_latlng"] = [42.37, -71.07]
        save_activity_from_dict(data, self.athlete)
        a = Activity.objects.get(pk=5002)
        self.assertAlmostEqual(a.start_latitude, 42.36)
        self.assertAlmostEqual(a.start_longitude, -71.06)
        self.assertAlmostEqual(a.end_latitude, 42.37)
        self.assertAlmostEqual(a.end_longitude, -71.07)

    def test_empty_latlng_not_flattened(self):
        from django_strava.views import save_activity_from_dict

        data = self._base_activity_dict(activity_id=5003)
        data["start_latlng"] = []
        data["end_latlng"] = []
        save_activity_from_dict(data, self.athlete)
        a = Activity.objects.get(pk=5003)
        self.assertIsNone(a.start_latitude)
        self.assertIsNone(a.end_latitude)

    def test_extra_api_fields_are_ignored(self):
        from django_strava.views import save_activity_from_dict

        data = self._base_activity_dict(activity_id=5004)
        data["resource_state"] = 3  # not a model field
        data["embed_token"] = "tok123"  # not a model field
        save_activity_from_dict(data, self.athlete)  # should not raise
        self.assertEqual(Activity.objects.filter(pk=5004).count(), 1)
