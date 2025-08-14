from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction, models
from django.utils import timezone
from .models import Organization, UserRole, OrganizationInvitation
from .forms import OrganizationForm, UserRoleForm, OrganizationInvitationForm, BulkInviteForm

def is_super_admin(user):
    """Check if user is a super admin in any organization"""
    return user.organization_roles.filter(role='super_admin', is_active=True).exists()

def is_org_admin(user):
    """Check if user is an organization admin"""
    return user.organization_roles.filter(role='org_admin', is_active=True).exists()

def is_staff_member(user):
    """Check if user is a staff member"""
    return user.organization_roles.filter(role='staff', is_active=True).exists()

def can_manage_users(user, organization):
    """Check if user can manage users in the given organization"""
    if is_super_admin(user):
        return True
    
    # Check if user is org_admin of this specific organization
    return user.organization_roles.filter(
        organization=organization,
        role='org_admin',
        is_active=True
    ).exists()

@login_required
@user_passes_test(is_super_admin)
def organization_list(request):
    organizations = Organization.objects.all().order_by('-created_at')
    
    # Obtener información sobre los permisos del usuario
    user_permissions = {}
    for org in organizations:
        user_permissions[org.id] = {
            'can_manage_users': can_manage_users(request.user, org),
            'can_edit': is_super_admin(request.user),
        }
    
    return render(request, 'organizations/organization_list.html', {
        'organizations': organizations,
        'user_permissions': user_permissions
    })

@login_required
@user_passes_test(is_super_admin)
def create_organization(request):
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            organization = form.save()
            messages.success(request, f'Organization "{organization.name}" created successfully!')
            return redirect('organizations:organization_list')
    else:
        form = OrganizationForm()
    
    return render(request, 'organizations/organization_form.html', {
        'form': form,
        'title': 'Create New Organization'
    })

@login_required
@user_passes_test(is_super_admin)
def edit_organization(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, f'Organization "{organization.name}" updated successfully!')
            return redirect('organizations:organization_list')
    else:
        form = OrganizationForm(instance=organization)
    
    return render(request, 'organizations/organization_form.html', {
        'form': form,
        'organization': organization,
        'title': f'Edit {organization.name}'
    })

@login_required
@user_passes_test(is_super_admin)
def organization_detail(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    user_roles = UserRole.objects.filter(organization=organization).select_related('user')
    
    return render(request, 'organizations/organization_detail.html', {
        'organization': organization,
        'user_roles': user_roles
    })

@login_required
def manage_user_roles(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    
    # Verificar permisos
    if not can_manage_users(request.user, organization):
        messages.error(request, "No tienes permisos para gestionar usuarios en esta organización.")
        return redirect('organizations:organization_list')
    
    if request.method == 'POST':
        form = UserRoleForm(request.POST)
        if form.is_valid():
            user_role = form.save(commit=False)
            user_role.organization = organization
            user_role.assigned_by = request.user
            user_role.save()
            messages.success(request, f'User role assigned successfully!')
            return redirect('organizations:manage_user_roles', org_id=org_id)
    else:
        form = UserRoleForm()
    
    user_roles = UserRole.objects.filter(organization=organization).select_related('user')
    
    # Calcular estadísticas
    total_users = user_roles.count()
    active_users = user_roles.filter(is_active=True).count()
    staff_members = user_roles.filter(role__in=['staff', 'org_admin', 'super_admin']).count()
    regular_members = user_roles.filter(role='member').count()
    
    return render(request, 'organizations/manage_user_roles.html', {
        'organization': organization,
        'form': form,
        'user_roles': user_roles,
        'total_users': total_users,
        'active_users': active_users,
        'staff_members': staff_members,
        'regular_members': regular_members,
    })

@login_required
@user_passes_test(is_super_admin)
def delete_user_role(request, role_id):
    user_role = get_object_or_404(UserRole, id=role_id)
    organization = user_role.organization
    
    if request.method == 'POST':
        user_role.delete()
        messages.success(request, 'User role deleted successfully!')
        return redirect('organizations:manage_user_roles', org_id=organization.id)
    
    return render(request, 'organizations/delete_user_role_confirm.html', {
        'user_role': user_role
    })

@login_required
@user_passes_test(is_super_admin)
def invite_user(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    
    if request.method == 'POST':
        form = OrganizationInvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.organization = organization
            invitation.invited_by = request.user
            invitation.save()
            messages.success(request, 'Invitation sent successfully!')
            return redirect('organizations:organization_detail', org_id=org_id)
    else:
        form = OrganizationInvitationForm()
    
    return render(request, 'organizations/invite_user.html', {
        'form': form,
        'organization': organization
    })

@login_required
@user_passes_test(is_super_admin)
def bulk_invite(request):
    """Invite multiple users by email domain"""
    if request.method == 'POST':
        form = BulkInviteForm(request.POST)
        if form.is_valid():
            organization = form.cleaned_data['organization']
            email_domain = form.cleaned_data['email_domain']
            role = form.cleaned_data['role']
            
            # Find all users with that email domain
            users = User.objects.filter(email__endswith=f'@{email_domain}')
            
            if not users.exists():
                messages.warning(request, f'No users found with email domain @{email_domain}')
                return redirect('organizations:bulk_invite')
            
            # Assign roles to users
            assigned_count = 0
            with transaction.atomic():
                for user in users:
                    # Check if user already has a role in this organization
                    if not UserRole.objects.filter(user=user, organization=organization).exists():
                        UserRole.objects.create(
                            user=user,
                            organization=organization,
                            role=role,
                            assigned_by=request.user,
                            assigned_at=timezone.now()
                        )
                        assigned_count += 1
            
            if assigned_count > 0:
                messages.success(request, f'Successfully assigned {role} role to {assigned_count} users from @{email_domain}')
            else:
                messages.info(request, f'All users from @{email_domain} already have roles in {organization.name}')
            
            return redirect('organizations:organization_list')
    else:
        form = BulkInviteForm()
    
    # Get recent bulk invitations for display
    recent_invitations = []
    
    return render(request, 'organizations/bulk_invite.html', {
        'form': form,
        'recent_invitations': recent_invitations
    })

@login_required
@user_passes_test(is_super_admin)
def user_management(request):
    """Overview of all users and their roles across organizations"""
    organizations = Organization.objects.filter(is_active=True).prefetch_related('user_roles__user')
    
    # Get user statistics
    total_users = User.objects.count()
    users_with_roles = UserRole.objects.values('user').distinct().count()
    users_without_roles = total_users - users_with_roles
    
    # Get role distribution
    role_distribution = UserRole.objects.values('role').annotate(
        count=models.Count('role')
    )
    
    return render(request, 'organizations/user_management.html', {
        'organizations': organizations,
        'total_users': total_users,
        'users_with_roles': users_with_roles,
        'users_without_roles': users_without_roles,
        'role_distribution': role_distribution
    })

def accept_invitation(request, token):
    invitation = get_object_or_404(OrganizationInvitation, token=token)
    
    if invitation.status != 'pending':
        messages.error(request, 'This invitation has already been processed.')
        return redirect('login')
    
    if invitation.expires_at < timezone.now():
        messages.error(request, 'This invitation has expired.')
        return redirect('login')
    
    if request.method == 'POST':
        # Process invitation acceptance
        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        messages.success(request, 'Invitation accepted successfully!')
        return redirect('login')
    
    return render(request, 'organizations/accept_invitation.html', {
        'invitation': invitation
    })
