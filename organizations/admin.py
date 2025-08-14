from django.contrib import admin
from .models import Organization, UserRole, OrganizationInvitation

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'logo')
        }),
        ('Contact Information', {
            'fields': ('website', 'address', 'phone', 'email')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'assigned_at')
    list_filter = ('role', 'is_active', 'organization', 'assigned_at')
    search_fields = ('user__username', 'user__email', 'organization__name')
    readonly_fields = ('assigned_at',)
    
    fieldsets = (
        ('User & Organization', {
            'fields': ('user', 'organization', 'role')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Assignment', {
            'fields': ('assigned_by', 'assigned_at')
        }),
    )

@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'organization', 'role', 'status', 'invited_by', 'created_at')
    list_filter = ('status', 'role', 'organization', 'created_at')
    search_fields = ('email', 'organization__name', 'invited_by__username')
    readonly_fields = ('token', 'created_at')
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('email', 'organization', 'role')
        }),
        ('Status', {
            'fields': ('status', 'responded_at')
        }),
        ('Technical', {
            'fields': ('token', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
