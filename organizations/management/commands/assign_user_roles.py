from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from organizations.models import Organization, UserRole

class Command(BaseCommand):
    help = 'Asigna roles a usuarios existentes en organizaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nombre de usuario específico para asignar rol'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['super_admin', 'org_admin', 'staff', 'member'],
            default='member',
            help='Rol a asignar (default: member)'
        )
        parser.add_argument(
            '--organization',
            type=str,
            default='Test Organization',
            help='Nombre de la organización (default: Test Organization)'
        )

    def handle(self, *args, **options):
        username = options['username']
        role_type = options['role']
        org_name = options['organization']

        # Obtener o crear la organización
        try:
            org = Organization.objects.get(name=org_name)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Organización encontrada: {org.name}')
            )
        except Organization.DoesNotExist:
            org = Organization.objects.create(
                name=org_name,
                description='Organización de prueba para testing',
                email='test@example.com',
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Organización creada: {org.name}')
            )

        if username:
            # Asignar rol a un usuario específico
            try:
                user = User.objects.get(username=username)
                self.assign_role_to_user(user, org, role_type)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ Usuario {username} no encontrado')
                )
        else:
            # Asignar roles a usuarios de prueba comunes
            test_users = [
                ('staff1', 'staff'),
                ('member1', 'member'),
                ('superadmin', 'super_admin')
            ]
            
            for test_username, test_role in test_users:
                try:
                    user = User.objects.get(username=test_username)
                    self.assign_role_to_user(user, org, test_role)
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Usuario {test_username} no encontrado')
                    )

        # Mostrar resumen
        self.show_summary(org)

    def assign_role_to_user(self, user, organization, role_type):
        """Asigna un rol a un usuario en una organización"""
        try:
            # Verificar si ya existe un rol
            existing_role = UserRole.objects.get(user=user, organization=organization)
            
            if existing_role.role != role_type:
                existing_role.role = role_type
                existing_role.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Rol actualizado para {user.username}: {role_type}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ {user.username} ya tiene el rol {role_type}')
                )
                
        except UserRole.DoesNotExist:
            # Crear nuevo rol
            UserRole.objects.create(
                user=user,
                organization=organization,
                role=role_type,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Rol creado para {user.username}: {role_type}')
            )

    def show_summary(self, organization):
        """Muestra un resumen de todos los roles en la organización"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN DE ROLES EN LA ORGANIZACIÓN')
        self.stdout.write('='*50)
        
        roles = UserRole.objects.filter(organization=organization).select_related('user')
        
        if roles.exists():
            for role in roles:
                status = '✓ Activo' if role.is_active else '✗ Inactivo'
                self.stdout.write(
                    f'  {role.user.username}: {role.role} - {status}'
                )
        else:
            self.stdout.write('  No hay roles asignados en esta organización')
        
        self.stdout.write('='*50)
