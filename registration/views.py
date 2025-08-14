from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from organizations.models import UserRole

def login_view(request):
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('/events/dashboard/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar que el usuario pertenezca a una organización activa
            user_roles = UserRole.objects.filter(
                user=user, 
                is_active=True,
                organization__is_active=True
            ).select_related('organization')
            
            if user_roles.exists():
                # Usuario tiene acceso a al menos una organización
                login(request, user)
                
                # Determinar el rol más alto del usuario
                role = user_roles.first()
                role_name = role.get_role_display()
                org_name = role.organization.name
                
                messages.success(request, f"¡Bienvenido de vuelta, {user.username}! Acceso como {role_name} en {org_name}")
                
                # Redirigir según el rol
                if role.role == 'super_admin':
                    return redirect('organizations:organization_list')
                else:
                    return redirect('/events/dashboard/')
            else:
                # Usuario no tiene acceso a ninguna organización
                messages.error(request, "Tu cuenta no tiene acceso a ninguna organización activa. Contacta al administrador.")
        else:
            messages.error(request, "Usuario o contraseña inválidos. Por favor intenta de nuevo.")
    
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('/')
