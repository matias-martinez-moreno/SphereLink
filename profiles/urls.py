from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('', views.my_profile, name='my_profile'),
    path('profile/', views.my_profile, name='my_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-photo/', views.change_photo, name='change_photo'),
    path('profile/<int:user_id>/', views.view_user_profile, name='view_user_profile'),
]
