"""
Management command para configurar TODA la base de datos de producción
Ejecuta: python manage.py setup_production_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from organizations.models import Organization, UserRole
from events.models import Event, EventRegistration
from profiles.models import Profile
from registration.models import ContactMessage
from events.models import EventComment, Notification
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Configura toda la base de datos de producción: organizaciones, usuarios, eventos y registros'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Elimina todos los datos antes de crear nuevos (CUIDADO: elimina todo)',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('⚠ ELIMINANDO TODOS LOS DATOS...'))
            # Eliminar en orden para respetar foreign keys
            Notification.objects.all().delete()
            EventComment.objects.all().delete()
            EventRegistration.objects.all().delete()
            Event.objects.all().delete()
            ContactMessage.objects.all().delete()
            UserRole.objects.all().delete()
            Profile.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()
            Organization.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Base de datos limpiada'))
        
        self.stdout.write(self.style.SUCCESS('\n=== CONFIGURANDO BASE DE DATOS DE PRODUCCIÓN ===\n'))
        
        # 1. CREAR ORGANIZACIÓN EAFIT
        self.stdout.write(self.style.NOTICE('1. Creando organización EAFIT...'))
        org, created = Organization.objects.get_or_create(
            name="EAFIT University",
            defaults={
                "description": "Higher Education Institution focused on technology and innovation",
                "website": "https://www.eafit.edu.co",
                "address": "Carrera 49 #7 Sur-50, Medellín, Colombia",
                "phone": "+57 4 261-9500",
                "email": "info@eafit.edu.co",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Organización "{org.name}" creada'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Organización "{org.name}" ya existe'))
        
        # 2. CREAR SUPERADMIN
        self.stdout.write(self.style.NOTICE('\n2. Creando superadmin...'))
        superadmin, created = User.objects.get_or_create(
            username='superadmin',
            defaults={
                'email': 'spherelinkevents@gmail.com',
                'first_name': 'Matias',
                'last_name': 'Martinez',
                'is_superuser': True,
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            superadmin.set_password('admin123')
            superadmin.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Superadmin creado: {superadmin.username} / admin123'))
        else:
            # Actualizar contraseña si ya existe
            if not superadmin.check_password('admin123'):
                superadmin.set_password('admin123')
                superadmin.save()
            self.stdout.write(self.style.WARNING(f'⚠ Superadmin "{superadmin.username}" ya existe'))
        
        # 3. CREAR STAFF1
        self.stdout.write(self.style.NOTICE('\n3. Creando staff1...'))
        staff1, created = User.objects.get_or_create(
            username='staff1',
            defaults={
                'email': 'staff1@eafit.edu.co',
                'first_name': 'Carolina',
                'last_name': 'Zapata',
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            staff1.set_password('staff123')
            staff1.save()
        else:
            if not staff1.check_password('staff123'):
                staff1.set_password('staff123')
                staff1.save()
        
        # Crear perfil para staff1
        Profile.objects.get_or_create(
            user=staff1,
            defaults={'bio': 'EAFIT STAFF.'}
        )
        
        # Asignar rol staff
        UserRole.objects.get_or_create(
            user=staff1,
            organization=org,
            defaults={'role': 'staff', 'is_active': True}
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Staff creado: {staff1.username} / staff123'))
        
        # 4. CREAR MEMBER1
        self.stdout.write(self.style.NOTICE('\n4. Creando member1...'))
        member1, created = User.objects.get_or_create(
            username='member1',
            defaults={
                'email': 'tomas@eafit.edu.co',
                'first_name': 'Tomás',
                'last_name': 'Giraldo',
                'is_staff': False,
                'is_active': True,
            }
        )
        if created:
            member1.set_password('member123')
            member1.save()
        else:
            if not member1.check_password('member123'):
                member1.set_password('member123')
                member1.save()
        
        # Crear perfil para member1
        Profile.objects.get_or_create(user=member1)
        
        # Asignar rol member
        UserRole.objects.get_or_create(
            user=member1,
            organization=org,
            defaults={'role': 'member', 'is_active': True, 'assigned_by': staff1}
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Member creado: {member1.username} / member123'))
        
        # 5. CREAR 16 USUARIOS ADICIONALES
        self.stdout.write(self.style.NOTICE('\n5. Creando 16 usuarios adicionales...'))
        users_data = [
            ('ana.garcia1', 'Ana', 'García', 'ana.garcia1@eafit.edu.co'),
            ('carlos.rodriguez2', 'Carlos', 'Rodríguez', 'carlos.rodriguez2@eafit.edu.co'),
            ('maria.martinez3', 'María', 'Martínez', 'maria.martinez3@eafit.edu.co'),
            ('juan.lopez4', 'Juan', 'López', 'juan.lopez4@eafit.edu.co'),
            ('laura.gonzalez5', 'Laura', 'González', 'laura.gonzalez5@eafit.edu.co'),
            ('diego.perez6', 'Diego', 'Pérez', 'diego.perez6@eafit.edu.co'),
            ('sofia.sanchez7', 'Sofia', 'Sánchez', 'sofia.sanchez7@eafit.edu.co'),
            ('andres.ramirez8', 'Andrés', 'Ramírez', 'andres.ramirez8@eafit.edu.co'),
            ('camila.torres9', 'Camila', 'Torres', 'camila.torres9@eafit.edu.co'),
            ('sebastian.flores10', 'Sebastian', 'Flores', 'sebastian.flores10@eafit.edu.co'),
            ('valentina.rivera11', 'Valentina', 'Rivera', 'valentina.rivera11@eafit.edu.co'),
            ('nicolas.gomez12', 'Nicolas', 'Gómez', 'nicolas.gomez12@eafit.edu.co'),
            ('isabella.diaz13', 'Isabella', 'Díaz', 'isabella.diaz13@eafit.edu.co'),
            ('mateo.cruz14', 'Mateo', 'Cruz', 'mateo.cruz14@eafit.edu.co'),
            ('daniela.morales15', 'Daniela', 'Morales', 'daniela.morales15@eafit.edu.co'),
            ('alejandro.ortiz16', 'Alejandro', 'Ortiz', 'alejandro.ortiz16@eafit.edu.co'),
        ]
        
        created_users = [staff1, member1]  # Incluir usuarios ya creados
        
        for username, first_name, last_name, email in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_staff': False,
                    'is_active': True,
                }
            )
            if created:
                user.set_password('eafit123')
                user.save()
                self.stdout.write(f'  ✓ Usuario creado: {username}')
            else:
                if not user.check_password('eafit123'):
                    user.set_password('eafit123')
                    user.save()
                self.stdout.write(f'  ⚠ Usuario {username} ya existe')
            
            # Crear perfil (usar get_or_create para evitar errores)
            Profile.objects.get_or_create(user=user)
            
            # Asignar a organización
            UserRole.objects.get_or_create(
                user=user,
                organization=org,
                defaults={'role': 'member', 'is_active': True}
            )
            
            created_users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(created_users)} usuarios listos'))
        
        # 6. CREAR EVENTOS
        self.stdout.write(self.style.NOTICE('\n6. Creando eventos...'))
        events_data = [
            {
                'title': 'Basketball Night',
                'description': 'We are short of three players to complete the team for a basketball tournament',
                'location': 'University Sports Center',
                'event_type': 'sports',
                'is_official': True,
                'max_capacity': 28,
                'duration': 180,
                'requirements': 'Basketball shoes',
                'date': timezone.now() + timedelta(days=30),
            },
            {
                'title': 'Morning Yoga Session',
                'description': 'Start your day with a relaxing yoga class to improve focus and flexibility.',
                'location': 'Wellness Center',
                'event_type': 'wellness',
                'is_official': True,
                'max_capacity': 14,
                'duration': 40,
                'requirements': 'Comfortable clothing, water bottle',
                'date': timezone.now() + timedelta(days=35),
            },
            {
                'title': 'AI and Machine Learning Workshop',
                'description': 'Learn basic AI and ML concepts in this hands-on workshop for beginners.',
                'location': 'Computer Lab 101',
                'event_type': 'academic',
                'is_official': True,
                'max_capacity': 35,
                'duration': 120,
                'requirements': 'Laptop with Python installed',
                'date': timezone.now() + timedelta(days=40),
            },
            {
                'title': 'Music Festival',
                'description': 'Share your music in this talent contest for students.',
                'location': 'main square',
                'event_type': 'other',
                'is_official': True,
                'max_capacity': 56,
                'duration': 180,
                'requirements': 'Being registered 2 weeks before',
                'date': timezone.now() + timedelta(days=25),
            },
            {
                'title': 'Football Match',
                'description': 'Friendly football match between students. All skill levels welcome. Refreshments provided.',
                'location': 'Football Field',
                'event_type': 'sports',
                'is_official': True,
                'max_capacity': 50,
                'duration': 120,
                'requirements': 'Football cleats, team registration',
                'date': timezone.now() + timedelta(days=32),
            },
            {
                'title': 'Mental Health Talk',
                'description': 'Learn tips on managing stress and staying positive during the semester.',
                'location': 'Block 20',
                'event_type': 'wellness',
                'is_official': True,
                'max_capacity': 17,
                'duration': 60,
                'requirements': 'None',
                'date': timezone.now() + timedelta(days=38),
            },
            {
                'title': 'Career Fair EAFIT 2025-2',
                'description': 'Meet companies offering internships and job opportunities.',
                'location': 'Block 20',
                'event_type': 'other',
                'is_official': True,
                'max_capacity': 48,
                'duration': 250,
                'requirements': 'be in at least the sixth semester',
                'date': timezone.now() + timedelta(days=45),
            },
            {
                'title': 'Real Madrid vs Barcelona Match Night',
                'description': 'We are going to watch the football match Real Madrid against Barcelona in Room 201, Block 33. There will be snacks and soft drinks. Come with your friends and enjoy the game.',
                'location': 'Block 33-402',
                'event_type': 'sports',
                'is_official': False,
                'max_capacity': 9,
                'duration': 200,
                'requirements': 'Respect the room and keep it clean',
                'date': timezone.now() + timedelta(days=42),
            },
        ]
        
        created_events = []
        for event_data in events_data:
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                organization=org,
                defaults={
                    **{k: v for k, v in event_data.items() if k != 'title'},
                    'created_by': staff1,
                }
            )
            if created:
                self.stdout.write(f'  ✓ Evento creado: {event.title}')
            else:
                self.stdout.write(f'  ⚠ Evento "{event.title}" ya existe')
            created_events.append(event)
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(created_events)} eventos creados'))
        
        # 7. REGISTRAR USUARIOS A EVENTOS
        self.stdout.write(self.style.NOTICE('\n7. Registrando usuarios a eventos...'))
        total_registrations = 0
        
        for user in created_users[2:]:  # Excluir staff1 y member1 de registros aleatorios
            num_registrations = random.randint(2, 5)
            available_events = list(created_events)
            random.shuffle(available_events)
            
            registrations_count = 0
            for event in available_events:
                if registrations_count >= num_registrations:
                    break
                
                if event.registrations.count() < event.max_capacity:
                    # Usar get_or_create para evitar duplicados
                    registration, created = EventRegistration.objects.get_or_create(
                        user=user,
                        event=event
                    )
                    if created:
                        registrations_count += 1
                        total_registrations += 1
        
        # Registrar staff1 y member1 a algunos eventos
        if created_events:
            EventRegistration.objects.get_or_create(user=staff1, event=created_events[0])
            EventRegistration.objects.get_or_create(user=member1, event=created_events[1])
            total_registrations += 2
        
        self.stdout.write(self.style.SUCCESS(f'✓ {total_registrations} registros creados'))
        
        # RESUMEN FINAL
        self.stdout.write(self.style.SUCCESS('\n=== CONFIGURACIÓN COMPLETADA ===\n'))
        self.stdout.write(self.style.SUCCESS('Usuarios creados:'))
        self.stdout.write(self.style.SUCCESS('  - superadmin / admin123 (Super Admin)'))
        self.stdout.write(self.style.SUCCESS('  - staff1 / staff123 (Staff)'))
        self.stdout.write(self.style.SUCCESS('  - member1 / member123 (Member)'))
        self.stdout.write(self.style.SUCCESS('  - 16 usuarios adicionales / eafit123 (Members)'))
        self.stdout.write(self.style.SUCCESS(f'\nOrganizaciones: {Organization.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Eventos: {Event.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Registros: {EventRegistration.objects.count()}'))
        self.stdout.write(self.style.WARNING('\n⚠ IMPORTANTE: Cambia las contraseñas después del primer login'))

