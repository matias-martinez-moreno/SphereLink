from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'date', 'location', 'duration', 'is_official', 'created_by', 'created_at')
    list_filter = ('event_type', 'is_official', 'date', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'location', 'requirements')
    date_hierarchy = 'date'
    list_editable = ('event_type', 'duration', 'is_official')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'event_type', 'is_official')
        }),
        ('Event Details', {
            'fields': ('date', 'location', 'duration', 'requirements')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
