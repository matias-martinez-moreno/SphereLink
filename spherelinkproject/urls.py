from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('events.urls')),  # Esto conecta las URLs de events
    path('accounts/', include('django.contrib.auth.urls')) # Necesario para la autentificación
]
