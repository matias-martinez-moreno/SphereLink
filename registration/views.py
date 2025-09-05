from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from organizations.models import UserRole

def login_view(request):
    """
    Vista de inicio de sesión principal
    - Verifica credenciales del usuario
    - Para superadmin: solo verifica contraseña, no requiere organización
    - Para otros usuarios: verifica que pertenezcan a una organización activa
    - Redirige según el rol del usuario (super_admin va a organizations, otros a events)
    """
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('/events/dashboard/')
    
    # Limpiar mensajes existentes al cargar la página de login (solo en GET)
    if request.method == 'GET':
        try:
            storage = messages.get_messages(request)
            storage.used = True
            if hasattr(request, 'session'):
                request.session['_messages'] = []
        except:
            pass
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Autenticar usuario con las credenciales proporcionadas
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # CASO ESPECIAL: Si es superadmin, permitir acceso inmediato
            if user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}! Access as Super Administrator")
                return redirect('organizations:organization_list')
            
            # Para usuarios NO superadmin: verificar que pertenezcan a una organización activa
            user_roles = UserRole.objects.filter(
                user=user, 
                is_active=True,
                organization__is_active=True
            ).select_related('organization')
            
            if user_roles.exists():
                # Usuario tiene acceso a al menos una organización
                login(request, user)
                
                # Determinar el rol más alto del usuario para personalizar el mensaje
                # Si tiene múltiples roles, priorizar super_admin
                role = user_roles.first()
                
                # Verificar si tiene rol super_admin en alguna organización
                has_super_admin = user_roles.filter(role='super_admin').exists()
                
                if has_super_admin:
                    # Si tiene super_admin, usar ese rol para el mensaje
                    super_admin_role = user_roles.filter(role='super_admin').first()
                    role_name = super_admin_role.get_role_display()
                    org_name = super_admin_role.organization.name
                else:
                    # Si no tiene super_admin, usar el primer rol
                    role_name = role.get_role_display()
                    org_name = role.organization.name
                
                messages.success(request, f"Welcome back, {user.username}! Access as {role_name} in {org_name}")
                
                # Redirigir según el rol del usuario
                # SOLO super_admin va a organizaciones, staff y member van a eventos
                if has_super_admin:
                    # Super admins van al panel de organizaciones
                    return redirect('organizations:organization_list')
                else:
                    # Staff y Member van al dashboard de eventos
                    return redirect('/events/dashboard/')
            else:
                # Usuario no tiene acceso a ninguna organización activa
                # Esto puede suceder si todas sus organizaciones están desactivadas
                messages.error(request, "Your account doesn't have access to any active organization. Contact the administrator.")
        else:
            # Credenciales inválidas
            messages.error(request, "Invalid username or password. Please try again.")
    
    # Renderizar el formulario de login (GET) o con errores (POST)
    return render(request, 'registration/login.html')

def logout_view(request):
    """
    Vista de cierre de sesión
    - Cierra la sesión del usuario actual
    - Limpia todos los mensajes existentes
    - Redirige a la página de login
    - Muestra mensaje de confirmación
    """
    # Limpiar todos los mensajes existentes antes del logout
    try:
        storage = messages.get_messages(request)
        storage.used = True
        if hasattr(request, 'session'):
            request.session['_messages'] = []
    except:
        pass
    
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('/')
