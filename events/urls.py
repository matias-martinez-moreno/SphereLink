from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # raíz es login
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create-event/', views.create_event_view, name='create_event'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
