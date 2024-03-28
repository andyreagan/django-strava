from django.test import TestCase


# Create your tests here.
def test_webhook():
    import json

    from .models import WebhookEvent

    response_text = """{
        "aspect_type": "update",
        "event_time": 1516126040,
        "object_id": 1360128428,
        "object_type": "activity",
        "owner_id": 134815,
        "subscription_id": 120475,
        "updates": {
            "title": "Messy"
        }
    }"""
    d = json.loads(response_text)
    d["object_type"] = {v.lower(): k for k, v in WebhookEvents.ObjectType.choices}[
        d["object_type"]
    ]
    d["aspect_type"] = {v.lower(): k for k, v in WebhookEvents.AspectType.choices}[
        d["aspect_type"]
    ]
    w = WebhookEvent(**d)
    w.save()
