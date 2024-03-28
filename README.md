# django-strava

django-strava is a Django strava App

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "strava" to your INSTALLED_APPS setting like this:

```
INSTALLED_APPS = [
    ...,
    "django_strava",
]
```

2. Include the strava URLconf in your project urls.py like this:

```
path("strava/", include("django_strava.urls")),
```

3. Run ``python manage.py migrate`` to create the models.

4. Visit the ``/strava/login`` URL to sign in with strava.
