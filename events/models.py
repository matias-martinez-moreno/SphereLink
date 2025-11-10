from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    EVENT_TYPES = [
        ('sports', 'Sports'),
        ('wellness', 'Wellness'),
        ('academic', 'Academic'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    duration = models.IntegerField(help_text='Duration in minutes', default=60)
    requirements = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='other')
    is_official = models.BooleanField(default=False, help_text='Evento oficial de la institución')
    max_capacity = models.PositiveIntegerField(default=100, help_text='Maximum number of participants')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, null=True, blank=True, help_text='Organization that owns this event')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def time(self):
        return self.date.strftime("%H:%M")
    
    @property
    def formatted_date(self):
        return self.date.strftime("%B %d, %Y")
    
    @property
    def current_registrations(self):
        """Returns the current number of registrations"""
        return self.registrations.count()
    
    @property
    def available_spots(self):
        """Returns the number of available spots"""
        return max(0, self.max_capacity - self.current_registrations)
    
    @property
    def is_full(self):
        """Returns True if the event is full"""
        return self.current_registrations >= self.max_capacity
    
    @property
    def registration_percentage(self):
        """Returns the event occupancy percentage"""
        if self.max_capacity == 0:
            return 0
        return (self.current_registrations / self.max_capacity) * 100

class EventRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')  # Prevents duplicate registrations

    def __str__(self):
        return f"{self.user.username} registered for {self.event.title}"


class EventComment(models.Model):
    """
    Model for comments on events
    - Any authenticated user can post comments
    - Event creator and Staff users can delete comments
    - Comments are displayed with author name and timestamp
    - Users can reply to comments (parent_comment field)
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_comments')
    content = models.TextField(max_length=1000, help_text='Comment content (max 1000 characters)')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Most recent comments first
        verbose_name = 'Event Comment'
        verbose_name_plural = 'Event Comments'

    def __str__(self):
        return f"{self.author.username} commented on {self.event.title}"

    @property
    def formatted_created_at(self):
        """Returns formatted creation timestamp"""
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")

    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent_comment is not None

    @property
    def is_event_owner_comment(self):
        """Check if this comment is from the event owner"""
        return self.author == self.event.created_by

    def can_be_deleted_by(self, user):
        """
        Check if a user can delete this comment
        - Event creator can delete any comment on their event
        - Staff users can delete any comment
        - Comment author can delete their own comment
        """
        if not user.is_authenticated:
            return False
        
        # Comment author can delete their own comment
        if self.author == user:
            return True
            
        # Event creator can delete any comment on their event
        if self.event.created_by == user:
            return True
            
        # Staff users can delete any comment
        from organizations.models import UserRole
        staff_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
            role__in=['staff', 'org_admin', 'super_admin']
        )
        return staff_roles.exists() or user.is_superuser


class Notification(models.Model):
    """
    Model for user notifications
    - Shows when someone replies to user's comments
    - Small dot indicator in profile
    """
    NOTIFICATION_TYPES = [
        ('comment_reply', 'Comment Reply'),
        ('event_update', 'Event Update'),
        ('registration_confirmed', 'Registration Confirmed'),
        ('unregistration_confirmed', 'Unregistration Confirmed'),
        ('event_registration', 'Event Registration'),
        ('event_created', 'Event Created'),
        ('event_deleted', 'Event Deleted'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPES, default='comment_reply')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_event = models.ForeignKey('Event', on_delete=models.CASCADE, null=True, blank=True)
    related_comment = models.ForeignKey('EventComment', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"