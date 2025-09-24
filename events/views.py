from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import csv
from django.db.models import Q
from django.utils import timezone
from .models import Event, EventRegistration
from .forms import EventForm

@login_required
def dashboard_view(request):
    """
    Vista principal del dashboard de eventos
    - Para Super Admin: muestra todos los eventos del sistema
    - Para Staff y Member: muestra solo eventos de su organización
    - Permite búsqueda y filtrado por tipo
    - Ordena eventos por fecha (más recientes primero)
    """
    # Obtener parámetros de búsqueda y filtros del usuario
    search_query = request.GET.get('search', '')
    event_type = request.GET.get('type', '')
    
    # Determinar qué eventos mostrar según el rol del usuario
    if request.user.is_superuser:
        # Super Admin ve todos los eventos del sistema
        events = Event.objects.all().order_by('-date')
        user_organization = None
        is_super_admin = True
    else:
        # Staff y Member ven eventos de su organización
        from organizations.models import UserRole
        
        # Obtener la organización activa del usuario
        user_role = UserRole.objects.filter(
            user=request.user,
            is_active=True,
            organization__is_active=True
        ).first()
        
        if user_role:
            # Mostrar eventos de la organización del usuario (incluyendo los que creó)
            events = Event.objects.filter(
                organization=user_role.organization
            ).order_by('-date')
            user_organization = user_role.organization
            is_super_admin = False
        else:
            # Usuario sin organización activa - mostrar eventos sin organización
            # Esto incluye eventos creados por usuarios que no pertenecen a ninguna organización
            events = Event.objects.filter(
                organization__isnull=True
            ).order_by('-date')
            user_organization = None
            is_super_admin = False
    
    # Aplicar filtro de búsqueda si se especifica
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Aplicar filtro por tipo de evento si se especifica
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Obtener tipos de eventos para el filtro del frontend
    event_types = Event.EVENT_TYPES
    
    context = {
        'events': events,
        'search_query': search_query,
        'selected_type': event_type,
        'event_types': event_types,
        'total_events': events.count(),
        'is_staff_user': _is_staff_user(request.user),
        'user_organization': user_organization,
        'is_super_admin': is_super_admin,
    }
    return render(request, 'events/dashboard.html', context)

def profile_view(request):
    """Redirige al perfil real en la app de profiles"""
    return redirect('profiles:my_profile')

def events_list_view(request):
    """
    Vista de lista de eventos futuros
    - Muestra solo eventos que aún no han ocurrido
    - Ordenados por fecha ascendente
    """
    events = Event.objects.filter(date__gte=timezone.now()).order_by('date')
    return render(request, 'events/events_list.html', {'events': events})


def event_detail_view(request, event_id):
    """
    Vista detallada de un evento específico
    - Muestra toda la información del evento
    - Indica si el usuario actual está registrado
    - Incluye tipos de eventos para el frontend
    """
    event = get_object_or_404(Event, id=event_id)
    user_registered = False
    
    # Verificar si el usuario está registrado en este evento
    if request.user.is_authenticated:
        user_registered = event.registrations.filter(user=request.user).exists()
    
    context = {
        'event': event,
        'event_types': Event.EVENT_TYPES,
        'is_staff_user': _is_staff_user(request.user),
        'user_registered': user_registered,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def my_events_view(request):
    """
    Vista de eventos del usuario autenticado
    - Muestra eventos creados por el usuario
    - Muestra eventos en los que el usuario está registrado
    - Incluye información sobre permisos de staff
    """
    user = request.user
    created_events = Event.objects.filter(created_by=user).order_by('-created_at')
    registered_events = Event.objects.filter(registrations__user=user).order_by('-date')
    
    context = {
        'created_events': created_events,
        'registered_events': registered_events,
        'is_staff_user': _is_staff_user(user),
    }
    return render(request, 'events/my_events.html', context)


@login_required
def register_event_view(request, event_id):
    """
    Vista para registrar usuario en un evento
    - Verifica que el usuario esté autenticado
    - Previene registros duplicados
    - Redirige al detalle del evento después del registro
    """
    user = request.user
    event = get_object_or_404(Event, id=event_id)

    # Verificar que el evento no haya expirado
    if event.date < timezone.now():
        messages.error(request, "This event has already passed and you cannot register for it.")
        return redirect('events:event_detail', event_id=event_id)

    # Verificar si ya está registrado para evitar duplicados
    already_registered = event.registrations.filter(user=user).exists()

    if already_registered:
        messages.info(request, "You are already registered for this event.")
    else:
        # Crear inscripción del usuario al evento
        event.registrations.create(user=user)
        messages.success(request, "You have successfully registered for the event.")

    return redirect('events:event_detail', event_id=event_id)


@login_required
def unregister_event_view(request, event_id):
    """
    Vista para cancelar registro en un evento
    - Elimina la inscripción del usuario
    - Solo funciona si el usuario estaba registrado
    - Redirige a mis eventos después de la cancelación
    """
    user = request.user
    event = get_object_or_404(Event, id=event_id)

    try:
        # Buscar y eliminar la inscripción
        registration = EventRegistration.objects.get(event=event, user=user)
        registration.delete()
        messages.success(request, f"You have successfully unregistered from the event '{event.title}'.")
    except EventRegistration.DoesNotExist:
        messages.warning(request, "You were not registered for this event.")

    return redirect('events:my_events')

@login_required
def create_event_view(request):
    """
    Vista para crear un nuevo evento
    - Solo usuarios autenticados pueden crear eventos
    - Los eventos de staff se marcan automáticamente como oficiales
    - Asigna automáticamente la organización del usuario al evento
    - Usa el formulario EventForm con validaciones
    """
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_event = form.save(commit=False)
            new_event.created_by = request.user
            
            # Asignar automáticamente la organización del usuario al evento
            from organizations.models import UserRole
            user_role = UserRole.objects.filter(
                user=request.user,
                is_active=True,
                organization__is_active=True
            ).first()
            
            if user_role:
                new_event.organization = user_role.organization
                # El evento aparecerá automáticamente en el dashboard de la organización
            
            # Marcar automáticamente como oficial si es staff
            if _is_staff_user(request.user):
                new_event.is_official = True
            else:
                new_event.is_official = False
            
            new_event.save()
            return redirect('events:my_events')
        # Los errores del formulario se muestran automáticamente en el template
        pass
    else:
        form = EventForm(user=request.user)

    return render(request, 'events/create_event.html', {'form': form, 'is_staff_user': _is_staff_user(request.user)})

def _is_staff_user(user):
    """
    Verifica si el usuario tiene rol de staff o superior
    - Retorna True si es superuser de Django
    - Retorna True si tiene rol staff, org_admin o super_admin en alguna organización
    - Retorna False si no está autenticado o no tiene permisos
    """
    if not user.is_authenticated:
        return False
    
    # Verificar si es superuser de Django (acceso completo)
    if user.is_superuser:
        return True
    
    # Verificar roles en organizaciones (sistema de permisos personalizado)
    from organizations.models import UserRole
    staff_roles = UserRole.objects.filter(
        user=user,
        is_active=True,
        role__in=['staff', 'org_admin', 'super_admin']
    )
    return staff_roles.exists()


@login_required
def edit_event_view(request, event_id):
    """
    Vista para editar un evento existente
    - Solo el creador del evento puede editarlo
    - Usa el mismo formulario que la creación
    - Mantiene el historial de cambios
    """
    event = get_object_or_404(Event, id=event_id)

    # Verificar permisos: solo el creador puede editar
    if event.created_by != request.user:
        messages.error(request, "You don't have permission to edit this event.")
        return redirect('events:my_events')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event, user=request.user)
        if form.is_valid():
            updated_event = form.save(commit=False)
            
            # Asignar la organización del usuario al evento si no tiene una
            if not updated_event.organization:
                from organizations.models import UserRole
                user_role = UserRole.objects.filter(
                    user=request.user,
                    is_active=True,
                    organization__is_active=True
                ).first()
                
                if user_role:
                    updated_event.organization = user_role.organization
            
            updated_event.save()
            messages.success(request, "Event updated successfully.")
            return redirect('events:my_events')
    else:
        form = EventForm(instance=event, user=request.user)

    return render(request, 'events/edit_event.html', {'form': form, 'event': event, 'is_staff_user': _is_staff_user(request.user)})


@login_required
def delete_event_view(request, event_id):
    """
    Vista para eliminar un evento
    - Solo el creador o usuarios staff pueden eliminar
    - Requiere confirmación antes de eliminar
    - Elimina permanentemente el evento y sus registros
    """
    event = get_object_or_404(Event, id=event_id)

    # Verificar permisos: creador o staff
    if not (event.created_by == request.user or _is_staff_user(request.user)):
        messages.error(request, "You don't have permission to delete this event.")
        return redirect('events:my_events')

    if request.method == 'POST':
        try:
            event_title = event.title
            event.delete()
            messages.success(request, f"Event '{event_title}' deleted successfully.")
            return redirect('events:my_events')
        except Exception as e:
            messages.error(request, f"Error deleting event: {str(e)}")
            return redirect('events:my_events')

    # Mostrar confirmación antes de eliminar el evento
    return render(request, 'events/delete_event_confirm.html', {'event': event})

@login_required
def event_registrations_view(request, event_id):
    """
    Vista para mostrar los registros de un evento específico
    - Solo el creador del evento puede ver esta información
    - Muestra lista de participantes registrados
    - Incluye estadísticas de ocupación
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Verificar permisos: solo el creador puede ver los registros
    if event.created_by != request.user:
        messages.error(request, "You don't have permission to view registrations for this event.")
        return redirect('events:my_events')
    
    # Obtener todos los registros del evento
    registrations = event.registrations.select_related('user').order_by('registered_at')
    
    context = {
        'event': event,
        'registrations': registrations,
        'total_registrations': event.current_registrations,
        'available_spots': event.available_spots,
        'is_full': event.is_full,
        'registration_percentage': event.registration_percentage,
    }
    return render(request, 'events/event_registrations.html', context)
@login_required
def export_attendees_csv(request, event_id):
    """
    Export a CSV file of all registered attendees for an event.
    - Only accessible to the event creator or staff users.
    - The CSV contains 'Name' and 'Email' of each registered user.
    """
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # Permission check: must be creator or staff
    if not (event.created_by == user or _is_staff_user(user)):
        messages.error(request, "You don't have permission to export attendees for this event.")
        return redirect('events:event_detail', event_id=event.id)

    # Set up the HTTP response for CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.title}_attendees.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Name', 'Email'])

    # Write data rows
    registrations = event.registrations.select_related('user').all()
    for registration in registrations:
        writer.writerow([registration.user.get_full_name(), registration.user.email])

    return response