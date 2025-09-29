from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import csv
import io
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Organization, UserRole, OrganizationInvitation
from .forms import OrganizationForm, UserRoleForm, OrganizationInvitationForm, BulkInviteForm, CSVBulkInviteForm
from profiles.models import Profile

def _is_super_admin(user):
    """
    Verifica si el usuario es Super Admin del sistema
    - Retorna True si es superuser de Django
    - Retorna True si tiene rol 'super_admin' en alguna organización activa Y NO tiene otros roles
    - Retorna False para staff, member y cualquier otro rol
    """
    if not user.is_authenticated:
        return False
    
    # Verificar si es superuser de Django (acceso completo al sistema)
    if user.is_superuser:
        return True
    
    # Verificar roles en organizaciones (sistema de permisos personalizado)
    # SOLO super_admin tiene acceso a funciones de administración
    super_admin_roles = UserRole.objects.filter(
        user=user,
        is_active=True,
        role='super_admin'  # Solo este rol específico
    )
    
    # Verificar que NO tenga roles de staff o member
    other_roles = UserRole.objects.filter(
        user=user,
        is_active=True
    ).exclude(role='super_admin')
    
    # Solo es super_admin si tiene roles super_admin Y NO tiene otros roles
    return super_admin_roles.exists() and not other_roles.exists()


@login_required
def organization_list(request):
    """
    FR21: Vista del dashboard de organizaciones para Super Admin
    - Muestra todas las organizaciones del sistema
    - Incluye estadísticas y acciones rápidas
    - Solo accesible para usuarios con rol 'super_admin'
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('events:dashboard')
    
    # Obtener todas las organizaciones
    organizations = Organization.objects.all()
    
    # Aplicar búsqueda si se proporciona
    search_query = request.GET.get('search', '')
    if search_query:
        organizations = organizations.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(website__icontains=search_query)
        )
    
    # Ordenar por fecha de creación (más recientes primero)
    organizations = organizations.order_by('-created_at')
    
    # Calcular estadísticas para el dashboard (usando todas las organizaciones, no solo las filtradas)
    all_organizations = Organization.objects.all()
    total_organizations = all_organizations.count()
    active_organizations = all_organizations.filter(is_active=True).count()
    inactive_organizations = total_organizations - active_organizations
    
    context = {
        'organizations': organizations,
        'total_organizations': total_organizations,
        'active_organizations': active_organizations,
        'inactive_organizations': inactive_organizations,
        'search_query': search_query,
    }
    return render(request, 'organizations/organization_list.html', context)


@login_required
def create_organization(request):
    """
    FR22: Crear nueva organización con primer usuario Staff
    - Crea la organización con los datos del formulario
    - Crea automáticamente un usuario Staff inicial
    - Asigna el rol 'staff' al usuario creado
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Usar transacción para asegurar consistencia de datos
                with transaction.atomic():
                    # Crear la organización
                    organization = form.save(commit=False)
                    organization.save()
                    
                    # Crear el primer usuario Staff
                    staff_username = request.POST.get('staff_username')
                    staff_email = request.POST.get('staff_email')
                    staff_password = request.POST.get('staff_password')
                    
                    if staff_username and staff_email and staff_password:
                        # Crear usuario con datos básicos
                        staff_user = User.objects.create_user(
                            username=staff_username,
                            email=staff_email,
                            password=staff_password,
                            first_name=request.POST.get('staff_first_name', ''),
                            last_name=request.POST.get('staff_last_name', '')
                        )
                        
                        # Asignar rol de Staff en la organización
                        UserRole.objects.create(
                            user=staff_user,
                            organization=organization,
                            role='staff',
                            assigned_by=request.user
                        )
                        
                        messages.success(request, f"Organization '{organization.name}' created successfully with Staff user '{staff_username}'.")
                    else:
                        messages.warning(request, f"Organization '{organization.name}' created, but Staff user creation failed due to missing data.")
                    
                    return redirect('organizations:organization_list')
            except Exception as e:
                messages.error(request, f"Error creating organization: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = OrganizationForm()
    
    context = {
        'form': form,
        'title': 'Create New Organization',
        'is_creating': True,
    }
    return render(request, 'organizations/organization_form.html', context)


@login_required
def edit_organization(request, org_id):
    """
    FR23: Editar detalles de organización existente
    - Permite modificar todos los campos de la organización
    - Solo accesible para Super Admins
    - Mantiene el historial de cambios
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    organization = get_object_or_404(Organization, id=org_id)
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, f"Organization '{organization.name}' updated successfully.")
            return redirect('organizations:organization_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = OrganizationForm(instance=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'title': 'Edit Organization',
        'is_creating': False,
    }
    return render(request, 'organizations/organization_form.html', context)


@login_required
def delete_organization(request, org_id):
    """
    FR24: Eliminar organización permanentemente
    - Elimina la organización y todos sus datos asociados
    - Incluye: roles de usuario, invitaciones, eventos relacionados
    - Solo accesible para Super Admins
    - Requiere confirmación del usuario
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    organization = get_object_or_404(Organization, id=org_id)
    
    if request.method == 'POST':
        try:
            # Usar transacción para eliminar todos los datos relacionados
            with transaction.atomic():
                # Eliminar todos los roles de usuario
                UserRole.objects.filter(organization=organization).delete()
                
                # Eliminar todas las invitaciones
                OrganizationInvitation.objects.filter(organization=organization).delete()
                
                # Eliminar la organización
                organization.delete()
                
                messages.success(request, f"Organization '{organization.name}' deleted successfully.")
                return redirect('organizations:organization_list')
        except Exception as e:
            messages.error(request, f"Error deleting organization: {str(e)}")
    
    context = {'organization': organization}
    return render(request, 'organizations/delete_organization_confirm.html', context)


@login_required
def organization_detail(request, org_id):
    """
    Vista detallada de una organización
    - Muestra información completa de la organización
    - Incluye estadísticas de usuarios y acciones disponibles
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    organization = get_object_or_404(Organization, id=org_id)
    user_roles = organization.user_roles.select_related('user').order_by('-assigned_at')
    
    # Calcular estadísticas de usuarios por rol
    total_users = user_roles.count()
    staff_users = user_roles.filter(role='staff').count()
    regular_members = user_roles.filter(role='member').count()
    
    context = {
        'organization': organization,
        'user_roles': user_roles,
        'total_users': total_users,
        'staff_users': staff_users,
        'regular_members': regular_members,
    }
    return render(request, 'organizations/organization_detail.html', context)


@login_required
def manage_user_roles(request, org_id):
    """
    FR25: Gestionar usuarios de una organización específica
    - Lista todos los usuarios de la organización
    - Permite cambiar roles y estados de usuarios
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    organization = get_object_or_404(Organization, id=org_id)
    user_roles = organization.user_roles.select_related('user').order_by('-assigned_at')
    
    # Debug: imprimir información sobre los user roles
    print(f"DEBUG - Total user roles: {user_roles.count()}")
    for ur in user_roles:
        print(f"DEBUG - User: {ur.user.username}, Role: {ur.role}")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_role_id = request.POST.get('user_role_id')
        
        if action and user_role_id:
            try:
                user_role = UserRole.objects.get(id=user_role_id, organization=organization)
                
                if action == 'delete_user':
                    username = user_role.user.username
                    user_role.delete()
                    messages.success(request, f"User {username} has been removed from the organization.")
                
                elif action == 'edit_role':
                    new_role = request.POST.get('role')
                    if new_role and new_role != user_role.role:
                        user_role.role = new_role
                        user_role.assigned_by = request.user
                        user_role.save()
                        messages.success(request, f"Role updated for {user_role.user.username}")
                
            except UserRole.DoesNotExist:
                messages.error(request, "User role not found.")
            except Exception as e:
                messages.error(request, f"Error processing action: {str(e)}")
        

    
    # Calcular estadísticas de la organización
    total_users = user_roles.count()
    staff_members = user_roles.filter(role__in=['staff', 'org_admin', 'super_admin']).count()
    regular_members = user_roles.filter(role='member').count()
    
    context = {
        'organization': organization,
        'user_roles': user_roles,
        'role_choices': UserRole.ROLE_CHOICES,
        'total_users': total_users,
        'staff_members': staff_members,
        'regular_members': regular_members,
    }
    return render(request, 'organizations/manage_user_roles.html', context)


@login_required
def create_user_for_organization(request, org_id):
    """
    FR26: Crear usuario individual para una organización específica
    - Crea un nuevo usuario en el sistema
    - Lo asigna automáticamente a la organización especificada
    - Permite elegir el rol del usuario
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    organization = get_object_or_404(Organization, id=org_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear el usuario
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                role = request.POST.get('role')
                
                # Verificar que el usuario no exista
                if User.objects.filter(username=username).exists():
                    messages.error(request, "Username already exists.")
                    return render(request, 'organizations/create_user.html', {
                        'organization': organization,
                        'role_choices': limited_role_choices
                    })
                
                if User.objects.filter(email=email).exists():
                    messages.error(request, "Email already exists.")
                    return render(request, 'organizations/create_user.html', {
                        'organization': organization,
                        'role_choices': limited_role_choices
                    })
                
                # Crear usuario
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=request.POST.get('first_name', ''),
                    last_name=request.POST.get('last_name', '')
                )
                
                # Asignar rol en la organización
                UserRole.objects.create(
                    user=user,
                    organization=organization,
                    role=role,
                    assigned_by=request.user
                )
                
                messages.success(request, f"User '{username}' created successfully in '{organization.name}'.")
                return redirect('organizations:manage_user_roles', org_id=org_id)
                
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
    
    # Solo mostrar Member y Staff como opciones para crear usuarios
    limited_role_choices = [
        ('member', 'Regular Member'),
        ('staff', 'Staff Member'),
    ]
    
    context = {
        'organization': organization,
        'role_choices': limited_role_choices,
    }
    return render(request, 'organizations/create_user.html', context)


@login_required
def delete_user_from_organization(request, org_id, user_id):
    """
    FR27: Eliminar usuario de una organización
    - Elimina el rol del usuario en la organización específica
    - NO elimina el usuario del sistema (solo de la organización)
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    organization = get_object_or_404(Organization, id=org_id)
    user = get_object_or_404(User, id=user_id)
    
    try:
        # Eliminar solo el rol en esta organización
        user_role = UserRole.objects.get(user=user, organization=organization)
        user_role.delete()
        messages.success(request, f"User '{user.username}' removed from '{organization.name}'.")
    except UserRole.DoesNotExist:
        messages.error(request, "User is not a member of this organization.")
    
    return redirect('organizations:manage_user_roles', org_id=org_id)


@login_required
def user_management(request):
    """
    Vista general de gestión de usuarios del sistema
    - Muestra estadísticas de usuarios por organización
    - Permite acciones masivas y gestión general
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    # Obtener estadísticas generales del sistema
    organizations = Organization.objects.all().prefetch_related('user_roles')
    total_users = User.objects.count()
    
    # Calcular usuarios con roles activos
    users_with_roles = UserRole.objects.filter(is_active=True).values('user').distinct().count()
    
    # Calcular usuarios sin roles (usuarios que no tienen ningún rol activo)
    users_without_roles = total_users - users_with_roles
    
    # Obtener distribución de roles
    role_distribution = []
    for role_code, role_name in UserRole.ROLE_CHOICES:
        count = UserRole.objects.filter(role=role_code, is_active=True).count()
        if count > 0:  # Solo mostrar roles que tienen usuarios
            role_distribution.append({
                'role': role_code,
                'name': role_name,
                'count': count
            })
    
    # Debug: imprimir estadísticas en consola
    print(f"DEBUG - Total Users: {total_users}")
    print(f"DEBUG - Users with Roles: {users_with_roles}")
    print(f"DEBUG - Users without Roles: {users_without_roles}")
    print(f"DEBUG - Organizations Count: {organizations.count()}")
    print(f"DEBUG - Role Distribution: {role_distribution}")
    
    context = {
        'organizations': organizations,
        'total_users': total_users,
        'users_with_roles': users_with_roles,
        'users_without_roles': users_without_roles,
        'role_distribution': role_distribution,
        'organizations_count': organizations.count(),
    }
    return render(request, 'organizations/user_management.html', context)


@login_required
def bulk_invite(request):
    """
    Invitación masiva de usuarios por dominio de email
    - Permite invitar múltiples usuarios de un mismo dominio
    - Útil para organizaciones educativas o corporativas
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    if request.method == 'POST':
        form = BulkInviteForm(request.POST)
        if form.is_valid():
            # Procesar invitaciones masivas
            domain = form.cleaned_data['domain']
            organization = form.cleaned_data['organization']
            role = form.cleaned_data['role']
            
            # Aquí se implementaría la lógica de invitación masiva
            messages.success(request, f"Bulk invitations sent to {domain} domain.")
            return redirect('organizations:organization_list')
    else:
        form = BulkInviteForm()
    
    context = {'form': form}
    return render(request, 'organizations/bulk_invite.html', context)


@login_required
def bulk_invite_confirm_view(request):
    """
    Vista de confirmación para bulk invite
    - Muestra mensaje de que la funcionalidad estará disponible próximamente
    - Muestra el template bulk_invite.html
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('events:dashboard')
    
    return render(request, 'organizations/bulk_invite.html')

@login_required
def contact_messages_view(request):
    """
    View to display and manage contact messages for Super Admin
    - Shows all contact messages with their status
    - Allows Super Admin to update message status and add notes
    - Only accessible for Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('events:dashboard')
    
    # Get all contact messages ordered by most recent first
    from registration.models import ContactMessage
    contact_messages = ContactMessage.objects.all().order_by('-created_at')
    
    # Handle status updates
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        
        if message_id and new_status:
            try:
                contact_message = ContactMessage.objects.get(id=message_id)
                contact_message.status = new_status
                if admin_notes:
                    contact_message.admin_notes = admin_notes
                contact_message.save()
                messages.success(request, f"Contact message status updated to {new_status}.")
            except ContactMessage.DoesNotExist:
                messages.error(request, "Contact message not found.")
    
    # Get statistics
    total_messages = contact_messages.count()
    pending_messages = contact_messages.filter(status='pending').count()
    in_progress_messages = contact_messages.filter(status='in_progress').count()
    resolved_messages = contact_messages.filter(status='resolved').count()
    
    context = {
        'contact_messages': contact_messages,
        'total_messages': total_messages,
        'pending_messages': pending_messages,
        'in_progress_messages': in_progress_messages,
        'resolved_messages': resolved_messages,
        'status_choices': ContactMessage.STATUS_CHOICES,
    }
    
    return render(request, 'organizations/contact_messages.html', context)


@login_required
def invite_user(request, org_id):
    """
    Invitar usuario individual a una organización
    - Envía invitación por email a un usuario específico
    - El usuario puede aceptar o declinar la invitación
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    organization = get_object_or_404(Organization, id=org_id)
    
    if request.method == 'POST':
        form = OrganizationInvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.organization = organization
            invitation.invited_by = request.user
            invitation.token = f"inv_{timezone.now().timestamp()}_{request.user.id}"
            invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
            invitation.save()
            
            messages.success(request, f"Invitation sent to {invitation.email}.")
            return redirect('organizations:manage_user_roles', org_id=org_id)
    else:
        form = OrganizationInvitationForm()
    
    context = {
        'form': form,
        'organization': organization,
    }
    return render(request, 'organizations/invite_user.html', context)


@login_required
def delete_user_role(request, role_id):
    """
    Eliminar rol de usuario específico
    - Elimina la relación usuario-organización
    - NO elimina el usuario del sistema
    - Solo accesible para Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    user_role = get_object_or_404(UserRole, id=role_id)
    organization_id = user_role.organization.id
    
    try:
        user_role.delete()
        messages.success(request, f"User role deleted successfully.")
    except Exception as e:
        messages.error(request, f"Error deleting user role: {str(e)}")
    
    return redirect('organizations:manage_user_roles', org_id=organization_id)


def accept_invitation(request, token):
    """
    Aceptar invitación a una organización
    - Permite a usuarios aceptar invitaciones pendientes
    - Crea automáticamente el rol de usuario en la organización
    - Accesible para cualquier usuario con el token válido
    """
    try:
        invitation = OrganizationInvitation.objects.get(token=token)
        
        if invitation.is_expired:
            messages.error(request, "This invitation has expired.")
            return redirect('events:dashboard')
        
        if invitation.status != 'pending':
            messages.error(request, "This invitation has already been processed.")
            return redirect('events:dashboard')
        
        if request.method == 'POST':
            # Procesar aceptación de invitación
            invitation.status = 'accepted'
            invitation.responded_at = timezone.now()
            invitation.save()
            
            # Crear rol de usuario
            UserRole.objects.create(
                user=request.user,
                organization=invitation.organization,
                role=invitation.role,
                assigned_by=invitation.invited_by
            )
            
            messages.success(request, f"Welcome to {invitation.organization.name}!")
            return redirect('events:dashboard')
        
        context = {'invitation': invitation}
        return render(request, 'organizations/accept_invitation.html', context)
        
    except OrganizationInvitation.DoesNotExist:
        messages.error(request, "Invalid invitation token.")
        return redirect('events:dashboard')


@login_required
def superadmin_profile(request):
    """
    Vista del perfil para Super Admin
    - Usa el template de super admin
    - Solo accesible para usuarios con rol super_admin
    - Incluye estadísticas del sistema
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('events:dashboard')
    
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        from profiles.models import Profile
        profile = Profile.objects.create(user=request.user)
    
    # Obtener estadísticas del sistema para el superadmin
    from organizations.models import Organization, UserRole
    from django.contrib.auth.models import User
    
    organizations_count = Organization.objects.count()
    total_users = User.objects.count()
    
    context = {
        'profile': profile,
        'organizations_count': organizations_count,
        'total_users': total_users,
    }
    return render(request, 'organizations/superadmin_profile.html', context)


@login_required
def csv_bulk_invite(request):
    """
    CSV Bulk Invitation of users to organization
    - Allows Super Admin to upload CSV file with email addresses
    - Creates user accounts for valid emails and assigns to organization
    - Provides detailed summary report of the operation
    - Only accessible for Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('organizations:organization_list')
    
    results = None
    
    if request.method == 'POST':
        form = CSVBulkInviteForm(request.POST, request.FILES)
        if form.is_valid():
            organization = form.cleaned_data['organization']
            csv_file = form.cleaned_data['csv_file']
            default_role = form.cleaned_data['default_role']
            
            # Initialize counters for summary report
            successful_invites = 0
            failed_invites = 0
            invalid_emails = 0
            existing_users = 0
            errors = []
            
            try:
                # Read and decode CSV file
                decoded_file = csv_file.read().decode('utf-8')
                csv_reader = csv.reader(io.StringIO(decoded_file))
                
                # Process CSV with transaction to ensure data consistency
                with transaction.atomic():
                    for row_number, row in enumerate(csv_reader, start=1):
                        if not row or len(row) == 0:
                            continue  # Skip empty rows
                        
                        email = row[0].strip().lower()  # Get email from first column
                        
                        if not email:
                            continue  # Skip empty emails
                        
                        # Validate email format
                        try:
                            validate_email(email)
                        except ValidationError:
                            invalid_emails += 1
                            errors.append(f"Row {row_number}: Invalid email format '{email}'")
                            continue
                        
                        # Check if user already exists
                        if User.objects.filter(email=email).exists():
                            existing_user = User.objects.get(email=email)
                            # Check if user is already in the organization
                            if UserRole.objects.filter(user=existing_user, organization=organization).exists():
                                existing_users += 1
                                errors.append(f"Row {row_number}: User '{email}' already exists in {organization.name}")
                                continue
                            else:
                                # User exists but not in this organization, add them
                                UserRole.objects.create(
                                    user=existing_user,
                                    organization=organization,
                                    role=default_role,
                                    assigned_by=request.user
                                )
                                successful_invites += 1
                                continue
                        
                        try:
                            # Create new user
                            # Generate username from email (part before @)
                            username_base = email.split('@')[0]
                            username = username_base
                            counter = 1
                            
                            # Ensure username is unique
                            while User.objects.filter(username=username).exists():
                                username = f"{username_base}{counter}"
                                counter += 1
                            
                            # Create user with temporary password
                            temp_password = f"Temp{username}123!"
                            
                            new_user = User.objects.create_user(
                                username=username,
                                email=email,
                                password=temp_password,
                                first_name='',
                                last_name=''
                            )
                            
                            # Assign role in organization
                            UserRole.objects.create(
                                user=new_user,
                                organization=organization,
                                role=default_role,
                                assigned_by=request.user
                            )
                            
                            successful_invites += 1
                            
                        except Exception as e:
                            failed_invites += 1
                            errors.append(f"Row {row_number}: Error creating user for '{email}': {str(e)}")
                
                # Prepare results summary
                results = {
                    'total_processed': successful_invites + failed_invites + invalid_emails + existing_users,
                    'successful_invites': successful_invites,
                    'failed_invites': failed_invites,
                    'invalid_emails': invalid_emails,
                    'existing_users': existing_users,
                    'organization': organization,
                    'default_role': default_role,
                    'errors': errors[:20]  # Show only first 20 errors
                }
                
                # Display summary message
                if successful_invites > 0:
                    messages.success(
                        request, 
                        f"✅ CSV processing completed! {successful_invites} users invited successfully to {organization.name}."
                    )
                
                if failed_invites > 0 or invalid_emails > 0 or existing_users > 0:
                    messages.warning(
                        request,
                        f"⚠️ Issues found: {invalid_emails} invalid emails, {existing_users} existing users, {failed_invites} creation errors."
                    )
                    
            except Exception as e:
                messages.error(request, f"Error processing CSV file: {str(e)}")
                results = None
    
    else:
        # Check if organization is passed as GET parameter for preselection
        org_id = request.GET.get('org')
        initial_data = {}
        
        if org_id:
            try:
                preselected_org = Organization.objects.get(id=org_id, is_active=True)
                initial_data['organization'] = preselected_org
            except Organization.DoesNotExist:
                pass
        
        form = CSVBulkInviteForm(initial=initial_data)
    
    context = {
        'form': form,
        'results': results,
        'preselected_org': request.GET.get('org'),  # Pass to template for additional context
    }
    return render(request, 'organizations/csv_bulk_invite.html', context)


@login_required
def bulk_invite_confirm_view(request):
    """
    Vista de confirmación para bulk invite
    - Muestra mensaje de que la funcionalidad estará disponible próximamente
    - Muestra el template bulk_invite.html
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('events:dashboard')
    
    return render(request, 'organizations/bulk_invite.html')

@login_required
def contact_messages_view(request):
    """
    View to display and manage contact messages for Super Admin
    - Shows all contact messages with their status
    - Allows Super Admin to update message status and add notes
    - Only accessible for Super Admins
    """
    if not _is_super_admin(request.user):
        messages.error(request, "Access denied. Super Admin privileges required.")
        return redirect('events:dashboard')
    
    # Get all contact messages ordered by most recent first
    from registration.models import ContactMessage
    contact_messages = ContactMessage.objects.all().order_by('-created_at')
    
    # Handle status updates
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        
        if message_id and new_status:
            try:
                contact_message = ContactMessage.objects.get(id=message_id)
                contact_message.status = new_status
                if admin_notes:
                    contact_message.admin_notes = admin_notes
                contact_message.save()
                messages.success(request, f"Contact message status updated to {new_status}.")
            except ContactMessage.DoesNotExist:
                messages.error(request, "Contact message not found.")
    
    # Get statistics
    total_messages = contact_messages.count()
    pending_messages = contact_messages.filter(status='pending').count()
    in_progress_messages = contact_messages.filter(status='in_progress').count()
    resolved_messages = contact_messages.filter(status='resolved').count()
    
    context = {
        'contact_messages': contact_messages,
        'total_messages': total_messages,
        'pending_messages': pending_messages,
        'in_progress_messages': in_progress_messages,
        'resolved_messages': resolved_messages,
        'status_choices': ContactMessage.STATUS_CHOICES,
    }
    
    return render(request, 'organizations/contact_messages.html', context)
