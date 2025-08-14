from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Organization(models.Model):
    """Modelo para representar una organización"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Configuración de la organización
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

class UserRole(models.Model):
    """Modelo para definir roles de usuario dentro de una organización"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('org_admin', 'Organization Administrator'),
        ('staff', 'Staff Member'),
        ('member', 'Regular Member'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_roles')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_roles'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'organization')
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
    
    def __str__(self):
        return f"{self.user.username} - {self.role} at {self.organization.name}"
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    @property
    def is_org_admin(self):
        return self.role == 'org_admin'
    
    @property
    def is_staff(self):
        return self.role == 'staff'
    
    @property
    def is_member(self):
        return self.role == 'member'

class OrganizationInvitation(models.Model):
    """Modelo para manejar invitaciones a organizaciones"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    email = models.EmailField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    role = models.CharField(max_length=20, choices=UserRole.ROLE_CHOICES, default='member')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.organization.name}"
    
    class Meta:
        verbose_name = "Organization Invitation"
        verbose_name_plural = "Organization Invitations"
