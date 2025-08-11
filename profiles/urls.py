from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_profile, name='my_profile'),
    path('profile/', views.my_profile, name='my_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
