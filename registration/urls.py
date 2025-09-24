from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('refresh-session/', views.refresh_session, name='refresh_session'),
    path('check-session/', views.check_session_status, name='check_session'),
]