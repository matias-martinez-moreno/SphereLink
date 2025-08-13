from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from .models import Event
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
    # Obtener parámetros de búsqueda y filtros
    search_query = request.GET.get('search', '')
    event_type = request.GET.get('type', '')
    
    # Filtrar eventos
    events = Event.objects.all().order_by('date')
    
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Obtener tipos de eventos para el filtro
    event_types = Event.EVENT_TYPES
    
    context = {
        'events': events,
        'search_query': search_query,
        'selected_type': event_type,
        'event_types': event_types,
        'total_events': events.count(),
    }
    return render(request, 'events/dashboard.html', context)

@login_required
def create_event_view(request):
    return render(request, 'events/create_event.html')

@login_required
def profile_view(request):
    return render(request, 'profiles/my_profile.html')
def my_events_view(request):
    return render(request, 'events/my_events.html')
def logout_view(request):
    logout(request)
    return redirect('login')

def events_list_view(request):
    events = Event.objects.filter(date__gte=timezone.now()).order_by('date')
    return render(request, 'events/events_list.html', {'events': events})
def event_detail_view(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        context = {
            'event': event,
            'event_types': Event.EVENT_TYPES,
        }
        return render(request, 'events/event_detail.html', context)
    except Event.DoesNotExist:
        return HttpResponse(f"<h1>Evento no encontrado</h1><p>El evento con ID {event_id} no existe en la base de datos.</p><a href='/dashboard/'>Volver al Dashboard</a>", status=404)
    except Exception as e:
        return HttpResponse(f"<h1>Error</h1><p>Error al cargar el evento: {str(e)}</p><a href='/dashboard/'>Volver al Dashboard</a>", status=500)
