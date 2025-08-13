from django.contrib import admin

# Necesario para crear usuarios con toda la información
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

#previenir errores de registro duplicado
admin.site.unregister(User)

# Registar modelo
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass