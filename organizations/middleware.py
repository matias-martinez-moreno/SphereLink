from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class SuperAdminRedirectMiddleware(MiddlewareMixin):
    """
    Middleware para redirigir usuarios Super Admin a la vista de organizaciones
    cuando acceden a ciertas URLs
    - SOLO super_admin es redirigido
    - Staff y Member pueden acceder al dashboard de eventos normalmente
    """
    
    def process_request(self, request):
        # Solo procesar si el usuario está autenticado
        if not request.user.is_authenticated:
            return None
        
        # Verificar si es Super Admin
        is_super_admin = self._is_super_admin(request.user)
        
        # SOLO si es Super Admin y está en el dashboard, redirigir a organizaciones
        # Staff y Member pueden acceder al dashboard sin problemas
        if is_super_admin and request.path == '/events/dashboard/':
            return redirect('organizations:organization_list')
        
        return None
    
    def _is_super_admin(self, user):
        """
        Verifica si el usuario es Super Admin
        - Retorna True solo para super_admin
        - Staff y Member retornan False
        """
        # Verificar si es superuser de Django
        if user.is_superuser:
            return True
        
        # Verificar roles en organizaciones - SOLO super_admin
        # Importar aquí para evitar problemas de importación circular
        try:
            from .models import UserRole
            
            # Verificar que NO tenga roles de staff o member
            super_admin_roles = UserRole.objects.filter(
                user=user,
                is_active=True,
                role='super_admin'  # Solo este rol específico
            )
            
            other_roles = UserRole.objects.filter(
                user=user,
                is_active=True
            ).exclude(role='super_admin')
            
            # Solo es super_admin si tiene roles super_admin Y NO tiene otros roles
            return super_admin_roles.exists() and not other_roles.exists()
        except:
            return False


class MessageCleanupMiddleware(MiddlewareMixin):
    """
    Middleware para limpiar mensajes automáticamente
    - Limpia mensajes antiguos en ciertas rutas
    - Evita acumulación de mensajes entre sesiones
    """
    
    def process_request(self, request):
        # Limpiar mensajes en rutas específicas
        cleanup_paths = [
            '/',  # Login page
            '/login/',
            '/logout/',
        ]
        
        if any(request.path.startswith(path) for path in cleanup_paths):
            # Solo limpiar en GET requests para estas rutas
            if request.method == 'GET':
                self._clear_messages(request)
        
        return None
    
    def _clear_messages(self, request):
        """
        Función para limpiar mensajes de forma segura
        """
        try:
            # Limpiar storage de mensajes
            storage = messages.get_messages(request)
            storage.used = True
            
            # Limpiar sesión de mensajes
            if hasattr(request, 'session'):
                request.session['_messages'] = []
                
        except Exception:
            # Ignorar cualquier error que pueda ocurrir
            pass
