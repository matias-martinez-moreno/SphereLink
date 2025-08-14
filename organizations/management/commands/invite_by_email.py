from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from organizations.models import Organization, UserRole
import re
from django.db import models

class Command(BaseCommand):
    help = 'Invite users to an organization by email domain'

    def add_arguments(self, parser):
        parser.add_argument('organization_name', type=str, help='Name of the organization')
        parser.add_argument('email_domain', type=str, help='Email domain (e.g., eafit.edu.co)')
        parser.add_argument('role', type=str, choices=['member', 'staff', 'org_admin'], help='Role to assign')
        parser.add_argument('--create-users', action='store_true', help='Create users if they don\'t exist')

    def handle(self, *args, **options):
        org_name = options['organization_name']
        email_domain = options['email_domain']
        role = options['role']
        create_users = options['create_users']

        try:
            # Buscar la organización
            organization = Organization.objects.get(name=org_name)
            self.stdout.write(f"Found organization: {organization.name}")
        except Organization.DoesNotExist:
            raise CommandError(f'Organization "{org_name}" does not exist')

        # Buscar usuarios existentes con ese dominio de email
        existing_users = User.objects.filter(email__endswith=f'@{email_domain}')
        
        if not existing_users.exists():
            self.stdout.write(
                self.style.WARNING(f'No users found with email domain @{email_domain}')
            )
            return

        self.stdout.write(f"Found {existing_users.count()} users with domain @{email_domain}")

        # Asignar roles a usuarios existentes
        assigned_count = 0
        for user in existing_users:
            # Verificar si ya tiene un rol en esta organización
            if UserRole.objects.filter(user=user, organization=organization).exists():
                self.stdout.write(
                    self.style.WARNING(f'User {user.username} already has a role in {organization.name}')
                )
                continue

            # Crear el rol
            UserRole.objects.create(
                user=user,
                organization=organization,
                role=role,
                assigned_by=User.objects.filter(is_superuser=True).first()
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Assigned {role} role to {user.username} ({user.email})')
            )
            assigned_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned roles to {assigned_count} users')
        )

        # Mostrar resumen
        total_users = UserRole.objects.filter(organization=organization).count()
        self.stdout.write(f"Total users in {organization.name}: {total_users}")
        
        # Mostrar distribución de roles
        role_distribution = UserRole.objects.filter(organization=organization).values('role').annotate(
            count=models.Count('role')
        )
        
        self.stdout.write("\nRole distribution:")
        for role_info in role_distribution:
            self.stdout.write(f"  {role_info['role']}: {role_info['count']} users")
