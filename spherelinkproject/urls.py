from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('registration.urls')),  # Login en la raíz
    path('events/', include('events.urls')),  # Events en /events/
    path('profiles/', include('profiles.urls')),  # Profiles en /profiles/
    path('organizations/', include('organizations.urls')),  # Organizations en /organizations/
]

# Configuración para servir archivos de medios
# En desarrollo: Django sirve los archivos directamente
# En producción: configurar el servidor web (nginx/apache) para servir /media/
# O usar Django para servir si no hay servidor web configurado
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
