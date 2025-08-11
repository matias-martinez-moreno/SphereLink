from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # raíz es login
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create-event/', views.create_event_view, name='create_event'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('events/', views.events_list_view, name='events_list'),
    path('my_events/', views.my_events_view, name='my_events'),
    path('event/<int:event_id>/', views.event_detail_view, name='event_detail'),
]
