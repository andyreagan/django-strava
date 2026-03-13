"""
Minimal URL configuration for the test suite.

Mounts django-strava's URL patterns under /strava/ so that the test
client can exercise the views without needing a full host project.
"""

from django.http import HttpResponse
from django.urls import include, path


def _home(request):
    return HttpResponse("home")


urlpatterns = [
    path("", _home, name="home"),
    path("strava/", include("django_strava.urls")),
]
