"""
Minimal Django settings for running the django-strava test suite.
"""

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django_strava",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# django_strava.apps.StravaConfig declares label = 'strava', so migrations live
# under that label – point Django at them explicitly.
MIGRATION_MODULES = {
    "strava": "django_strava.migrations",
}

# URL conf required for the test client even if we don't hit all views
ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# Strava OAuth settings – placeholder values, views are tested with mocks
STRAVA_CLIENT_ID = "fake-client-id"
STRAVA_CLIENT_SECRET = "fake-client-secret"  # noqa: S105

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
