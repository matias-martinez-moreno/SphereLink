from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import csv
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from .models import Event, EventRegistration, EventComment
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
    - Includes comments for the event
    """
    event = get_object_or_404(Event, id=event_id)
    user_registered = False
    
    # Check if user is registered for this event
    if request.user.is_authenticated:
        user_registered = event.registrations.filter(user=request.user).exists()
    
    # Get comments for this event (ordered by most recent first)
    comments = event.comments.select_related('author').all()
    
    context = {
        'event': event,
        'event_types': Event.EVENT_TYPES,
        'is_staff_user': _is_staff_user(request.user),
        'user_registered': user_registered,
        'comments': comments,
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


@login_required
@require_POST
def post_comment(request, event_id):
    """
    Post a new comment on an event
    - Only authenticated users can post comments
    - Comment content is required and limited to 1000 characters
    - Returns JSON response for AJAX handling
    """
    event = get_object_or_404(Event, id=event_id)
    content = request.POST.get('content', '').strip()
    
    # Validate comment content
    if not content:
        return JsonResponse({
            'success': False,
            'error': 'Comment content cannot be empty.'
        })
    
    if len(content) > 1000:
        return JsonResponse({
            'success': False,
            'error': 'Comment content cannot exceed 1000 characters.'
        })
    
    try:
        # Create the comment
        comment = EventComment.objects.create(
            event=event,
            author=request.user,
            content=content
        )
        
        # Return success response with comment data
        return JsonResponse({
            'success': True,
            'message': 'Comment posted successfully.',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.username,
                'created_at': comment.formatted_created_at,
                'can_delete': comment.can_be_deleted_by(request.user)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error posting comment: {str(e)}'
        })


@login_required
@require_POST
def delete_comment(request, comment_id):
    """
    Delete a comment from an event
    - Only event creator, staff users, or comment author can delete
    - Returns JSON response for AJAX handling
    """
    comment = get_object_or_404(EventComment, id=comment_id)
    
    # Check if user has permission to delete this comment
    if not comment.can_be_deleted_by(request.user):
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to delete this comment.'
        })
    
    try:
        # Delete the comment
        comment.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Comment deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting comment: {str(e)}'
        })


@login_required
def calendar_view(request):
    """
    Interactive calendar view for events
    - Shows monthly view with navigation controls
    - Highlights days with events
    - Allows clicking on days to view event details
    """
    # Get month and year from URL parameters, default to current month
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Validate month and year
    if month < 1 or month > 12:
        month = timezone.now().month
    if year < 2020 or year > 2030:
        year = timezone.now().year
    
    # Create date objects for the current month
    current_date = datetime(year, month, 1)
    prev_month = current_date - timedelta(days=1)
    next_month = current_date + timedelta(days=32)
    next_month = next_month.replace(day=1)
    
    # Check if user wants to see all events
    show_all = request.GET.get('show_all', 'false').lower() == 'true'
    
    # Debug: Print request info
    print(f"DEBUG CALENDAR - User: {request.user.username}")
    print(f"DEBUG CALENDAR - Is authenticated: {request.user.is_authenticated}")
    print(f"DEBUG CALENDAR - Is superuser: {request.user.is_superuser}")
    print(f"DEBUG CALENDAR - Show all: {show_all}")
    print(f"DEBUG CALENDAR - Year: {year}, Month: {month}")
    print(f"DEBUG CALENDAR - Request path: {request.path}")
    print(f"DEBUG CALENDAR - Request GET params: {request.GET}")
    
    # Get events for the current month based on user role
    if request.user.is_superuser and show_all:
        # Super Admin can see all system events only when explicitly requested
        print("DEBUG CALENDAR - Using superuser all events query")
        events = Event.objects.filter(
            date__year=year,
            date__month=month
        ).order_by('date')
    else:
        # ALL users (including super admin) see ONLY events they are registered for
        print("DEBUG CALENDAR - Using registered events query")
        events = Event.objects.filter(
            date__year=year,
            date__month=month,
            registrations__user=request.user
        ).distinct().order_by('date')
        
        # Debug: Print user and events info
        print(f"DEBUG CALENDAR - Events found: {events.count()}")
        for event in events:
            print(f"DEBUG CALENDAR - Event: {event.title} on {event.date}")
    
    # Group events by day
    events_by_day = {}
    for event in events:
        day = event.date.day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)
    
    # Generate calendar grid
    first_day, last_day = monthrange(year, month)
    first_weekday = datetime(year, month, 1).weekday()
    
    # Create calendar matrix
    calendar_days = []
    
    # Add empty cells for days before the first day of the month
    for i in range(first_weekday):
        calendar_days.append(None)
    
    # Add days of the month
    for day in range(1, last_day + 1):
        calendar_days.append({
            'day': day,
            'has_events': day in events_by_day,
            'events': events_by_day.get(day, []),
            'is_today': (year == timezone.now().year and 
                        month == timezone.now().month and 
                        day == timezone.now().day)
        })
    
    # Add empty cells for days after the last day of the month
    while len(calendar_days) % 7 != 0:
        calendar_days.append(None)
    
    # Group days into weeks
    weeks = []
    for i in range(0, len(calendar_days), 7):
        weeks.append(calendar_days[i:i+7])
    
    context = {
        'year': year,
        'month': month,
        'current_date': current_date,
        'prev_month': prev_month,
        'next_month': next_month,
        'weeks': weeks,
        'events_by_day': events_by_day,
        'month_names': [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ],
        'weekday_names': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    }
    
    return render(request, 'events/calendar.html', context)


@login_required
def calendar_day_events(request, year, month, day):
    """
    AJAX endpoint to get events for a specific day
    - Returns JSON with events for the requested day
    - Used for popup/modal display
    """
    try:
        # Validate date
        date_obj = datetime(int(year), int(month), int(day))
        
        # Check if user wants to see all events
        show_all = request.GET.get('show_all', 'false').lower() == 'true'
        
        # Get events for the specific day based on user role
        if request.user.is_superuser and show_all:
            # Super Admin can see all system events only when explicitly requested
            events = Event.objects.filter(
                date__year=year,
                date__month=month,
                date__day=day
            ).order_by('date')
        else:
            # ALL users (including super admin) see ONLY events they are registered for
            events = Event.objects.filter(
                date__year=year,
                date__month=month,
                date__day=day,
                registrations__user=request.user
            ).distinct().order_by('date')
        
        # Format events for JSON response
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'time': event.time,
                'location': event.location,
                'event_type': event.get_event_type_display(),
                'is_official': event.is_official,
                'url': f'/events/event/{event.id}/',
                'description': event.description[:100] + '...' if len(event.description) > 100 else event.description
            })
        
        return JsonResponse({
            'success': True,
            'date': date_obj.strftime('%B %d, %Y'),
            'events': events_data
        })
        
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid date provided'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error retrieving events: {str(e)}'
        })