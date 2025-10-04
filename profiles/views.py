from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProfileForm, PhotoForm
from .models import Profile


def my_profile(request):
    """
    Vista del perfil del usuario - Solo muestra el perfil regular
    - Verifica que el usuario esté autenticado
    - Crea automáticamente un perfil si no existe
    - Incluye información del rol y organización del usuario
    """
    if request.user.is_authenticated:
        try:
            # Intentar obtener el perfil existente del usuario
            profile = request.user.profile
        except Profile.DoesNotExist:
            # Si el perfil no existe, lo creamos automáticamente
            # Esto asegura que todos los usuarios tengan un perfil
            profile = Profile.objects.create(user=request.user)
        
        # Obtener información del rol y organización del usuario
        from organizations.models import UserRole
        
        # Para superadmin, mostrar información especial
        if request.user.is_superuser:
            user_role_info = {
                'role': 'Super Administrator',
                'organization': 'System Platform',
                'is_superuser': True
            }
        else:
            # Para usuarios normales, obtener su rol en organizaciones
            try:
                user_role = UserRole.objects.filter(
                    user=request.user, 
                    is_active=True,
                    organization__is_active=True
                ).select_related('organization').first()
                
                if user_role:
                    user_role_info = {
                        'role': user_role.get_role_display(),
                        'organization': user_role.organization.name,
                        'is_superuser': False
                    }
                else:
                    user_role_info = {
                        'role': 'No Role Assigned',
                        'organization': 'No Organization',
                        'is_superuser': False
                    }
            except:
                user_role_info = {
                    'role': 'Unknown',
                    'organization': 'Unknown',
                    'is_superuser': False
                }
        
        context = {
            'profile': profile,
            'user_role_info': user_role_info
        }
        
        return render(request, 'profiles/my_profile.html', context)
    else:
        # Si no está autenticado, redirigir al login
        # No se permite ver perfiles sin autenticación
        return redirect('login')


def edit_profile(request):
    """
    Vista para editar el perfil del usuario
    - Solo usuarios autenticados pueden editar su perfil
    - Crea automáticamente un perfil si no existe
    - Procesa el formulario y guarda los cambios
    """
    if not request.user.is_authenticated:
        # Verificar autenticación antes de permitir edición
        return redirect('login')
    
    try:
        # Intentar obtener el perfil existente
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Crear perfil si no existe (caso de usuarios antiguos)
        profile = Profile.objects.create(user=request.user)
    
    if request.method == "POST":
        # Procesar formulario de edición
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Guardar cambios y redirigir al perfil
            form.save()
            return redirect('profiles:my_profile')
        # Si hay errores, se muestran automáticamente en el template
    else:
        # Mostrar formulario con datos actuales
        form = ProfileForm(instance=profile)

    return render(request, 'profiles/edit_profile.html', {'form': form})


def view_user_profile(request, user_id):
    """
    Vista para ver el perfil de otro usuario
    - Solo usuarios autenticados pueden ver perfiles de otros
    - Muestra información pública del perfil
    - Incluye información del rol y organización del usuario
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Obtener el usuario cuyo perfil se quiere ver
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    
    try:
        # Obtener el perfil del usuario
        profile = user.profile
    except Profile.DoesNotExist:
        # Crear perfil si no existe
        profile = Profile.objects.create(user=user)
    
    # Obtener información del rol y organización del usuario
    from organizations.models import UserRole
    
    # Para superadmin, mostrar información especial
    if user.is_superuser:
        user_role_info = {
            'role': 'Super Administrator',
            'organization': 'System Platform',
            'is_superuser': True
        }
    else:
        # Para usuarios normales, obtener su rol en organizaciones
        try:
            user_role = UserRole.objects.filter(
                user=user, 
                is_active=True,
                organization__is_active=True
            ).select_related('organization').first()
            
            if user_role:
                user_role_info = {
                    'role': user_role.get_role_display(),
                    'organization': user_role.organization.name,
                    'is_superuser': False
                }
            else:
                user_role_info = {
                    'role': 'No Role Assigned',
                    'organization': 'No Organization',
                    'is_superuser': False
                }
        except:
            user_role_info = {
                'role': 'Unknown',
                'organization': 'Unknown',
                'is_superuser': False
            }
    
    context = {
        'profile': profile,
        'user_role_info': user_role_info,
        'viewed_user': user,
        'is_own_profile': request.user == user
    }
    
    return render(request, 'profiles/view_user_profile.html', context)

def change_photo(request):
    """
    Vista simple para cambiar solo la foto del perfil
    - Solo usuarios autenticados pueden cambiar su foto
    - Crea automáticamente un perfil si no existe
    - Procesa solo el campo de foto
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == "POST":
        form = PhotoForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('organizations:superadmin_profile')
    else:
        form = PhotoForm(instance=profile)

    return render(request, 'profiles/change_photo.html', {'form': form})
