from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login, name='stravalogin'),
    path('success', views.success, name='stravasuccess'),
    path('activity/<int:activity_id>/', views.activity, name='stravaactivitypage'),
    path('webhook', views.webhook),
]
