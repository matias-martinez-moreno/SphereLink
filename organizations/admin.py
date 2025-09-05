from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Organization, UserRole, OrganizationInvitation

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'updated_at', 'user_count']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'email']
    readonly_fields = ['created_at', 'updated_at', 'user_count']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website', 'address')
        }),
        ('Media', {
            'fields': ('logo',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_count(self, obj):
        return obj.user_count
    user_count.short_description = 'Users'

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_active', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'is_active', 'assigned_at', 'organization']
    search_fields = ['user__username', 'user__email', 'organization__name']
    readonly_fields = ['assigned_at']
    autocomplete_fields = ['user', 'organization', 'assigned_by']
    fieldsets = (
        ('User Assignment', {
            'fields': ('user', 'organization', 'role')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Assignment Details', {
            'fields': ('assigned_at', 'assigned_by'),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'role', 'status', 'invited_by', 'created_at', 'expires_at']
    list_filter = ['role', 'status', 'created_at', 'expires_at', 'organization']
    search_fields = ['email', 'organization__name', 'invited_by__username']
    readonly_fields = ['token', 'created_at', 'responded_at']
    autocomplete_fields = ['organization', 'invited_by']
    fieldsets = (
        ('Invitation Details', {
            'fields': ('email', 'organization', 'role')
        }),
        ('Status', {
            'fields': ('status', 'token')
        }),
        ('Timing', {
            'fields': ('created_at', 'expires_at', 'responded_at'),
            'classes': ('collapse',)
        }),
        ('Inviter', {
            'fields': ('invited_by',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'invited_by')


# Personalizar el admin de User para eliminar grupos
class CustomUserAdmin(UserAdmin):
    # Eliminar grupos de los fieldsets
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Eliminar grupos de add_fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

# Desregistrar el UserAdmin por defecto y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
