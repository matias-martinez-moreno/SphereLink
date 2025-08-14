from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from organizations.models import Organization, UserRole

class Command(BaseCommand):
    help = 'Create the first super administrator and default organization'

    def handle(self, *args, **options):
        # Crear usuario super admin si no existe
        username = 'superadmin'
        email = 'admin@spherelink.com'
        password = 'admin123456'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created super admin user: {username}')
            )
        
        # Crear organización por defecto si no existe
        org_name = 'SphereLink University'
        if Organization.objects.filter(name=org_name).exists():
            self.stdout.write(
                self.style.WARNING(f'Organization {org_name} already exists')
            )
            organization = Organization.objects.get(name=org_name)
        else:
            organization = Organization.objects.create(
                name=org_name,
                description='Default organization for SphereLink platform',
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created organization: {org_name}')
            )
        
        # Asignar rol de super admin al usuario
        if UserRole.objects.filter(user=user, organization=organization).exists():
            self.stdout.write(
                self.style.WARNING(f'User role already exists for {username}')
            )
        else:
            UserRole.objects.create(
                user=user,
                organization=organization,
                role='super_admin',
                assigned_by=user
            )
            self.stdout.write(
                self.style.SUCCESS(f'Assigned super_admin role to {username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuper Admin created successfully!\n'
                f'Username: {username}\n'
                f'Password: {password}\n'
                f'Email: {email}\n'
                f'Organization: {org_name}\n'
                f'Role: Super Administrator'
            )
        )
