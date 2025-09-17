from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deletes events that have already passed.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting to delete expired events...'))
        
        expired_events = Event.objects.filter(date__lt=timezone.now())
        
        if not expired_events.exists():
            self.stdout.write(self.style.SUCCESS('No expired events found.'))
            return

        count = expired_events.count()
        
        try:
            expired_events.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} expired event(s).'))
            logger.info(f"Successfully deleted {count} expired events.")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred while deleting events: {e}'))
            logger.error(f"An error occurred during expired event deletion: {e}", exc_info=True)
