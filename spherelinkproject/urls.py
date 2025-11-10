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

# Configuración para servir archivos de medios (desarrollo y producción)
# En producción, asegúrate de configurar el servidor web para servir /media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # En producción, el servidor web (nginx/apache) debe servir /media/
    # Pero Django también puede servirlo si es necesario
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
