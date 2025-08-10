from django.shortcuts import render, redirect , get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from .models import Event,EventRegistration
from .forms import EventForm

def login_view(request):
    return render(request, 'events/login.html')

def register_view(request):
    return render(request, 'events/register.html')

def dashboard_view(request):
    # Obtener parámetros de búsqueda y filtros
    search_query = request.GET.get('search', '')
    event_type = request.GET.get('type', '')
    
    # Filtrar eventos
    events = Event.objects.all().order_by('-date')
    
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
    event = get_object_or_404(Event, id=event_id)
    user_registered = False
    if request.user.is_authenticated:
        user_registered = event.registrations.filter(user=request.user).exists()
    context = {
        'event': event,
        'event_types': Event.EVENT_TYPES,
        'user_registered': user_registered,
    }
    return render(request, 'events/event_detail.html', context)

@login_required
def my_events_view(request):
    user = request.user
    created_events = Event.objects.filter(created_by=user).order_by('-created_at')
    registered_events = Event.objects.filter(registrations__user=user).order_by('-date')
    
    context = {
        'created_events': created_events,
        'registered_events': registered_events,
    }
    return render(request, 'events/my_events.html', context)


def register_event_view(request, event_id):
    user = request.user
    if not user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para inscribirte en un evento.")
        return redirect('login')
    
    event = get_object_or_404(Event, id=event_id)

    
    already_registered = event.registrations.filter(user=user).exists()

    if already_registered:
        messages.info(request, "Ya estás inscrito en este evento.")
    else:
        # Crear inscripción
        event.registrations.create(user=user)
        messages.success(request, "Te has inscrito correctamente en el evento.")

    return redirect('event_detail', event_id=event_id)


@login_required
def unregister_event_view(request, event_id):
    user = request.user
    event = get_object_or_404(Event, id=event_id)

    try:
        registration = EventRegistration.objects.get(event=event, user=user)
        registration.delete()
        messages.success(request, f"Te has desinscrito correctamente del evento '{event.title}'.")
    except EventRegistration.DoesNotExist:
        messages.warning(request, "No estabas registrado en este evento.")

    return redirect('my_events')
@login_required
def create_event_view(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            new_event = form.save(commit=False)
            new_event.created_by = request.user
            new_event.is_official = False
            new_event.save()
            return redirect('my_events')
        else:
            print(form.errors)  # <- Para depurar errores
    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})


def edit_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Verificar que el usuario actual sea el creador del evento
    if event.created_by != request.user:
        messages.error(request, "No tienes permiso para editar este evento.")
        return redirect('my_events')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Evento actualizado correctamente.")
            return redirect('my_events')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


@login_required
def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.created_by != request.user:
        messages.error(request, "No tienes permiso para eliminar este evento.")
        return redirect('my_events')

    if request.method == 'POST':
        event.delete()
        messages.success(request, "Evento eliminado correctamente.")
        return redirect('my_events')

    # Opcional: mostrar una confirmación antes de eliminar
    return render(request, 'events/delete_event_confirm.html', {'event': event})