from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'registration'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('refresh-session/', views.refresh_session, name='refresh_session'),
    path('check-session/', views.check_session_status, name='check_session'),
    path('contact-admin/', views.contact_admin, name='contact_admin'),
    
    # Password Reset URLs - Using Custom Class Views
    path('reset-password/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),
    
    path('reset-password/done/', 
         views.CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    
    path('reset-password-confirm/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    
    path('reset-password-complete/', 
         views.CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
]