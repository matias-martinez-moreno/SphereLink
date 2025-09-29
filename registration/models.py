from django.db import models
from django.utils import timezone

class ContactMessage(models.Model):
    """
    Model to store contact messages from users who need help with login or account issues
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    email = models.EmailField(help_text="User's email address")
    subject = models.CharField(max_length=200, default="Login/Account Help Request")
    message = models.TextField(help_text="Description of the issue or help needed")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for administrators")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
    
    def __str__(self):
        return f"Contact from {self.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
