from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user__date_joined',)
