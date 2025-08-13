from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required # Necesidad de logins
from django.contrib.auth import logout, login # Salida y verificaciones
from django.contrib.auth.forms import AuthenticationForm # verificacion

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user() # <-- Obtiene el usuario del formulario validado
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})

@login_required
def dashboard_view(request):
    return render(request, 'events/dashboard.html')

@login_required
def create_event_view(request):
    return render(request, 'events/create_event.html')

@login_required
def profile_view(request):
    return render(request, 'events/profile.html')

def logout_view(request):
    logout(request)
    return redirect('login')
