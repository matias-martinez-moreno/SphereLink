from django import forms
from django.utils import timezone
from .models import Event

class EventForm(forms.ModelForm):
    """
    Form for creating and editing events
    - Includes all necessary fields for an event
    - The is_official field is only shown for staff users
    - Uses custom widgets with Bootstrap CSS classes
    """
    class Meta:
        model = Event
        # Exclude fields that should not be filled by the user
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '4',
                'placeholder': 'Duration in minutes (minimum 4)'
            }),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'max_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '4',
                'placeholder': 'Enter maximum number of participants (minimum 4)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Custom form initialization
        - Receives current user to determine permissions
        - Hides is_official field for non-staff users
        - Maintains standard form functionality
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show is_official field for staff and super_admin
        # This controls which users can mark events as official
        if not user or not self._is_staff_user(user):
            self.fields.pop('is_official', None)
    def clean_title(self):
        """
        Validation for event title
        - Must have at least 4 characters
        """
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 4:
            raise forms.ValidationError("Title must be at least 4 characters long.")
        return title
    
    def clean_description(self):
        """
        Validation for event description
        - Must have at least 4 characters
        """
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 4:
            raise forms.ValidationError("Description must be at least 4 characters long.")
        return description
    
    def clean_location(self):
        """
        Validation for event location
        - Must have at least 4 characters
        """
        location = self.cleaned_data.get('location', '').strip()
        if len(location) < 4:
            raise forms.ValidationError("Location must be at least 4 characters long.")
        return location
    
    def clean_duration(self):
        """
        Validation for event duration
        - Must be at least 4 minutes
        """
        duration = self.cleaned_data.get('duration')
        if duration is not None and duration < 4:
            raise forms.ValidationError("Duration must be at least 4 minutes.")
        return duration
    
    def clean_date(self):
        """
        Validation for event date
        - Cannot be a date in the past
        """
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("The event date cannot be in the past.")
        return date

    
    def clean_max_capacity(self):
        """
        Custom validation for maximum capacity
        - Must be at least 4 participants
        """
        max_capacity = self.cleaned_data.get('max_capacity')
        
        if max_capacity is not None:
            if max_capacity < 4:
                raise forms.ValidationError("Maximum capacity must be at least 4 participants.")
            
            # If editing, verify it's not less than current registrations
            if self.instance and self.instance.pk:
                current_registrations = self.instance.current_registrations
                if max_capacity < current_registrations:
                    raise forms.ValidationError(
                        f"Cannot reduce capacity below current registrations ({current_registrations} participants)."
                    )
        
        return max_capacity
    
    def _is_staff_user(self, user):
        """
        Check if user has staff role or higher
        - Returns True if user is Django superuser
        - Returns True if user has staff, org_admin or super_admin role in any organization
        - Returns False if not authenticated or has no permissions
        """
        if not user.is_authenticated:
            return False
        
        # Check if user is Django superuser (full system access)
        if user.is_superuser:
            return True
        
        # Check roles in organizations (custom permission system)
        # Only users with administrative roles can mark events as official
        from organizations.models import UserRole
        staff_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
            role__in=['staff', 'org_admin', 'super_admin']
        )
        return staff_roles.exists()
