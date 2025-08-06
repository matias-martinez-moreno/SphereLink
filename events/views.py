from django.shortcuts import render
from django.http import HttpResponse

def login_view(request):
    return render(request, 'events/login.html')

def register_view(request):
    return render(request, 'events/register.html')

def dashboard_view(request):
    return render(request, 'events/dashboard.html')

def create_event_view(request):
    return render(request, 'events/create_event.html')

def profile_view(request):
    return render(request, 'events/profile.html')

def logout_view(request):
    return HttpResponse("Logout Page (under construction)")
