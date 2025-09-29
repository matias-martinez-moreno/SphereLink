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
    Main events dashboard view
    - For Super Admin: shows all system events
    - For Staff and Member: shows only events from their organization
    - Allows search and filtering by type
    - Orders events by date (most recent first)
    """
    # Get search parameters and filters from user
    search_query = request.GET.get('search', '')
    event_type = request.GET.get('type', '')
    
    # Determine which events to show based on user role
    if request.user.is_superuser:
        # Super Admin sees all system events
        events = Event.objects.all().order_by('-date')
        user_organization = None
        is_super_admin = True
    else:
        # Staff and Member see events from their organization
        from organizations.models import UserRole
        
        # Get user's active organization
        user_role = UserRole.objects.filter(
            user=request.user,
            is_active=True,
            organization__is_active=True
        ).first()
        
        if user_role:
            # Show events from user's organization (including those they created)
            events = Event.objects.filter(
                organization=user_role.organization
            ).order_by('-date')
            user_organization = user_role.organization
            is_super_admin = False
        else:
            # User without active organization - show events without organization
            # This includes events created by users who don't belong to any organization
            events = Event.objects.filter(
                organization__isnull=True
            ).order_by('-date')
            user_organization = None
            is_super_admin = False
    
    # Apply search filter if specified
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply event type filter if specified
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Get event types for frontend filter
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
    """Redirect to the real profile in the profiles app"""
    return redirect('profiles:my_profile')

def events_list_view(request):
    """
    Future events list view
    - Shows only events that haven't occurred yet
    - Ordered by date ascending
    """
    events = Event.objects.filter(date__gte=timezone.now()).order_by('date')
    return render(request, 'events/events_list.html', {'events': events})


def event_detail_view(request, event_id):
    """
    Detailed view of a specific event
    - Shows all event information
    - Indicates if the current user is registered
    - Includes event types for the frontend
    """
    event = get_object_or_404(Event, id=event_id)
    user_registered = False
    
    # Check if user is registered for this event
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
    Authenticated user's events view
    - Shows events created by the user
    - Shows events the user is registered for
    - Includes information about staff permissions
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
    View to register user for an event
    - Verifies user is authenticated
    - Prevents duplicate registrations
    - Redirects to event detail after registration
    """
    user = request.user
    event = get_object_or_404(Event, id=event_id)

    # Check that the event hasn't expired
    if event.date < timezone.now():
        messages.error(request, "This event has already passed and you cannot register for it.")
        return redirect('events:event_detail', event_id=event_id)

    # Check if already registered to avoid duplicates
    already_registered = event.registrations.filter(user=user).exists()

    if already_registered:
        messages.info(request, "You are already registered for this event.")
    else:
        # Create user registration for the event
        event.registrations.create(user=user)
        messages.success(request, "You have successfully registered for the event.")

    return redirect('events:event_detail', event_id=event_id)


@login_required
def unregister_event_view(request, event_id):
    """
    View to cancel event registration
    - Removes user registration
    - Only works if user was registered
    - Redirects to my events after cancellation
    """
    user = request.user
    event = get_object_or_404(Event, id=event_id)

    try:
        # Find and delete the registration
        registration = EventRegistration.objects.get(event=event, user=user)
        registration.delete()
        messages.success(request, f"You have successfully unregistered from the event '{event.title}'.")
    except EventRegistration.DoesNotExist:
        messages.warning(request, "You were not registered for this event.")

    return redirect('events:my_events')

@login_required
def create_event_view(request):
    """
    View to create a new event
    - Only authenticated users can create events
    - Staff events are automatically marked as official
    - Automatically assigns user's organization to the event
    - Uses EventForm with validations
    """
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_event = form.save(commit=False)
            new_event.created_by = request.user
            
            # Automatically assign user's organization to the event
            from organizations.models import UserRole
            user_role = UserRole.objects.filter(
                user=request.user,
                is_active=True,
                organization__is_active=True
            ).first()
            
            if user_role:
                new_event.organization = user_role.organization
                # Event will automatically appear in organization dashboard
            
            # Automatically mark as official if user is staff
            if _is_staff_user(request.user):
                new_event.is_official = True
            else:
                new_event.is_official = False
            
            new_event.save()
            return redirect('events:my_events')
        # Form errors are automatically displayed in the template
        pass
    else:
        form = EventForm(user=request.user)

    return render(request, 'events/create_event.html', {'form': form, 'is_staff_user': _is_staff_user(request.user)})

def _is_staff_user(user):
    """
    Check if user has staff role or higher
    - Returns True if user is Django superuser
    - Returns True if user has staff, org_admin or super_admin role in any organization
    - Returns False if not authenticated or has no permissions
    """
    if not user.is_authenticated:
        return False
    
    # Check if user is Django superuser (full access)
    if user.is_superuser:
        return True
    
    # Check roles in organizations (custom permission system)
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
    View to edit an existing event
    - Only the event creator can edit it
    - Uses the same form as creation
    - Maintains change history
    """
    event = get_object_or_404(Event, id=event_id)

    # Check permissions: only creator can edit
    if event.created_by != request.user:
        messages.error(request, "You don't have permission to edit this event.")
        return redirect('events:my_events')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event, user=request.user)
        if form.is_valid():
            updated_event = form.save(commit=False)
            
            # Assign user's organization to event if it doesn't have one
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
    View to delete an event
    - Only creator or staff users can delete
    - Requires confirmation before deletion
    - Permanently deletes the event and its registrations
    """
    event = get_object_or_404(Event, id=event_id)

    # Check permissions: creator or staff
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

    # Show confirmation before deleting the event
    return render(request, 'events/delete_event_confirm.html', {'event': event})

@login_required
def event_registrations_view(request, event_id):
    """
    View to show registrations for a specific event
    - Only the event creator can see this information
    - Shows list of registered participants
    - Includes occupancy statistics
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Check permissions: only creator can view registrations
    if event.created_by != request.user:
        messages.error(request, "You don't have permission to view registrations for this event.")
        return redirect('events:my_events')
    
    # Get all event registrations
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
    Export a CSV file of all registered attendees for an event
    - Only accessible to the event creator or staff users
    - The CSV contains 'Name' and 'Email' of each registered user
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