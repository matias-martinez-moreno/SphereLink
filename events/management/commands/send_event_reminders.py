# This command has been disabled - email reminders are no longer used
# Registration confirmations are now sent immediately when users register

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'This command has been disabled. Registration confirmations are sent immediately when users register.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('This command has been disabled.'))
        self.stdout.write(self.style.NOTICE('Registration confirmations are now sent immediately when users register for events.'))
