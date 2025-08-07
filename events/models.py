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
    is_official = models.BooleanField(default=False, help_text='Evento oficial publicado por staff')
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
