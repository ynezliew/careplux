from django.urls import path
from . import views

urlpatterns = [
    path('rest/v1/calendar/init/', views.google_calendar_init_view, name='google_calendar_init'),
    path('rest/v1/calendar/redirect/', views.google_calendar_redirect_view, name='google_calendar_redirect'),
    path('rest/v1/calendar/events/', views.get_calendar_events_view, name='get_calendar_events'),
    path('google_calendar_webhook/', views.google_calendar_webhook, name='google_calendar_webhook'),
    path('start-watch/', views.start_watch, name='start-watch'),
]
