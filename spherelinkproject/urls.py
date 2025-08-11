from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('events.urls')),  # Esto conecta las URLs de events
    path('profiles/', include('profiles.urls')),
    path('profile/', include('profiles.urls')),


]

# Configuración para servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
