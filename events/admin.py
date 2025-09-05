from django.contrib import admin
from .models import Event, EventRegistration

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'date', 'location', 'created_by', 'is_official', 'max_capacity', 'current_registrations', 'is_full')
    list_filter = ('event_type', 'is_official', 'date', 'created_by')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at', 'current_registrations', 'available_spots', 'is_full', 'registration_percentage')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'date', 'duration', 'location')
        }),
        ('Event Details', {
            'fields': ('event_type', 'requirements', 'image', 'is_official', 'max_capacity')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
        ('Statistics', {
            'fields': ('current_registrations', 'available_spots', 'is_full', 'registration_percentage'),
            'classes': ('collapse',)
        }),
    )
    
    def current_registrations(self, obj):
        return obj.current_registrations
    current_registrations.short_description = 'Current Registrations'
    
    def available_spots(self, obj):
        return obj.available_spots
    available_spots.short_description = 'Available Spots'
    
    def is_full(self, obj):
        return obj.is_full
    is_full.boolean = True
    is_full.short_description = 'Is Full'
    
    def registration_percentage(self, obj):
        return f"{obj.registration_percentage:.1f}%"
    registration_percentage.short_description = 'Registration %'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at')
    list_filter = ('registered_at', 'event__event_type')
    search_fields = ('user__username', 'user__email', 'event__title')
    readonly_fields = ('registered_at',)
