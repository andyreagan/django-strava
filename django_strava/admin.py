from django.contrib import admin

# Register your models here.
from .models import Activity, StravaAthlete, StravaToken, WebhookEvent

admin.site.register(StravaToken)
admin.site.register(StravaAthlete)
admin.site.register(Activity)
admin.site.register(WebhookEvent)
