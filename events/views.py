from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from .models import Event

def login_view(request):
    return render(request, 'events/login.html')

def register_view(request):
    return render(request, 'events/register.html')

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

def create_event_view(request):
    return render(request, 'events/create_event.html')

def profile_view(request):
    return render(request, 'events/profile.html')

def logout_view(request):
    return HttpResponse("Logout Page (under construction)")

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
