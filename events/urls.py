from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('events/', views.events_list_view, name='events_list'),
    path('event/<int:event_id>/', views.event_detail_view, name='event_detail'),
    path('my_events/', views.my_events_view, name='my_events'),
    path('register/<int:event_id>/', views.register_event_view, name='register_event'),
    path('unregister/<int:event_id>/', views.unregister_event_view, name='unregister_event'),
    path('create_event/', views.create_event_view, name='create_event'),
    path('edit_event/<int:event_id>/', views.edit_event_view, name='edit_event'),
    path('delete_event/<int:event_id>/', views.delete_event_view, name='delete_event'),
    path('event/<int:event_id>/registrations/', views.event_registrations_view, name='event_registrations'),
    path('event/<int:event_id>/export_attendees/', views.export_attendees_csv, name='export_attendees'),
    # Comment URLs
    path('event/<int:event_id>/comment/', views.post_comment, name='post_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    # Calendar URLs
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/<int:year>/<int:month>/<int:day>/events/', views.calendar_day_events, name='calendar_day_events'),
]
