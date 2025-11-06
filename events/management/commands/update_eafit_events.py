from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from events.models import Event, EventRegistration
from organizations.models import Organization, UserRole
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Updates EAFIT events: changes November dates to December, sets random capacities (1-70), and creates 16 users with registrations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting EAFIT events update...'))
        
        # 1. Find EAFIT organization
        try:
            eafit_org = Organization.objects.get(name__icontains='eafit')
            self.stdout.write(self.style.SUCCESS(f'Found organization: {eafit_org.name}'))
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR('EAFIT organization not found. Please create it first.'))
            return
        except Organization.MultipleObjectsReturned:
            eafit_org = Organization.objects.filter(name__icontains='eafit').first()
            self.stdout.write(self.style.WARNING(f'Multiple EAFIT organizations found. Using: {eafit_org.name}'))
        
        # 2. Get all events from EAFIT
        eafit_events = Event.objects.filter(organization=eafit_org)
        self.stdout.write(self.style.NOTICE(f'Found {eafit_events.count()} events in EAFIT'))
        
        # 3. Change November dates to December (any year)
        updated_dates = 0
        for event in eafit_events:
            if event.date.month == 11:  # November
                # Change to December, keep the same day and time
                try:
                    new_date = event.date.replace(month=12)
                    event.date = new_date
                    event.save()
                    updated_dates += 1
                    self.stdout.write(f'  Updated date for: {event.title} -> {event.date.strftime("%B %d, %Y %H:%M")}')
                except ValueError:
                    # Handle case where day doesn't exist in December (e.g., Nov 31)
                    # Move to last day of December
                    from calendar import monthrange
                    last_day = monthrange(event.date.year, 12)[1]
                    new_date = event.date.replace(month=12, day=min(event.date.day, last_day))
                    event.date = new_date
                    event.save()
                    updated_dates += 1
                    self.stdout.write(f'  Updated date for: {event.title} -> {event.date.strftime("%B %d, %Y %H:%M")}')
        
        if updated_dates == 0:
            self.stdout.write(self.style.WARNING('No events found in November to update to December'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated_dates} events from November to December'))
        
        # 4. Set random capacities between 1 and 70
        updated_capacities = 0
        for event in eafit_events:
            random_capacity = random.randint(1, 70)
            # Make sure capacity is not less than current registrations
            current_registrations = event.registrations.count()
            if random_capacity < current_registrations:
                random_capacity = current_registrations
            
            event.max_capacity = random_capacity
            event.save()
            updated_capacities += 1
            self.stdout.write(f'  Updated capacity for: {event.title} -> {random_capacity}')
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_capacities} event capacities'))
        
        # 5. Create 16 users with @eafit.edu.co
        self.stdout.write(self.style.NOTICE('Creating 16 users...'))
        created_users = []
        
        first_names = ['Ana', 'Carlos', 'María', 'Juan', 'Laura', 'Diego', 'Sofia', 'Andrés', 
                      'Camila', 'Sebastian', 'Valentina', 'Nicolas', 'Isabella', 'Mateo', 
                      'Daniela', 'Alejandro']
        last_names = ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Pérez', 'Sánchez', 
                     'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Cruz', 'Morales', 'Ortiz']
        
        for i in range(16):
            first_name = first_names[i]
            last_name = last_names[i]
            username = f'{first_name.lower()}.{last_name.lower()}{i+1}'
            email = f'{username}@eafit.edu.co'
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                self.stdout.write(f'  User {username} already exists, skipping creation')
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='eafit123',  # Default password
                    first_name=first_name,
                    last_name=last_name
                )
                self.stdout.write(f'  Created user: {username} ({email})')
            
            # Assign user to EAFIT organization as member
            if not UserRole.objects.filter(user=user, organization=eafit_org).exists():
                UserRole.objects.create(
                    user=user,
                    organization=eafit_org,
                    role='member',
                    is_active=True
                )
                self.stdout.write(f'  Assigned {username} to EAFIT as member')
            
            created_users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'Created/updated {len(created_users)} users'))
        
        # 6. Register users to various events
        self.stdout.write(self.style.NOTICE('Registering users to events...'))
        total_registrations = 0
        
        for user in created_users:
            # Each user registers to 2-5 random events
            num_registrations = random.randint(2, 5)
            available_events = list(eafit_events)
            random.shuffle(available_events)
            
            registrations_count = 0
            for event in available_events:
                if registrations_count >= num_registrations:
                    break
                
                # Check if event has capacity
                if event.registrations.count() < event.max_capacity:
                    # Check if user is already registered
                    if not EventRegistration.objects.filter(user=user, event=event).exists():
                        EventRegistration.objects.create(user=user, event=event)
                        registrations_count += 1
                        total_registrations += 1
                        self.stdout.write(f'  {user.username} registered to: {event.title}')
            
            self.stdout.write(f'  {user.username} registered to {registrations_count} events')
        
        self.stdout.write(self.style.SUCCESS(f'Created {total_registrations} event registrations'))
        self.stdout.write(self.style.SUCCESS('EAFIT events update completed successfully!'))

