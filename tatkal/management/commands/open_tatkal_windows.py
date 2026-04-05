from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from inventory.models import Schedule
from tatkal.models import TatkalConfig, TatkalQuota

class Command(BaseCommand):
    help = 'Opens tatkal windows for upcoming schedules based on configuration'

    def handle(self, *args, **options):
        now = timezone.now()
        # Look ahead up to 24 hours just to grab potential schedules
        lookahead_limit = now + timedelta(hours=24)
        
        # We assume schedule.journey_date & departure_time make up the departure datetime
        # Since Schedule stores date and time separately:
        today = now.date()
        tomorrow = lookahead_limit.date()

        schedules = Schedule.objects.filter(journey_date__in=[today, tomorrow], status='SCHEDULED')

        opened_count = 0
        for schedule in schedules:
            import datetime
            dep_dt = timezone.make_aware(datetime.datetime.combine(schedule.journey_date, schedule.departure_time))
            time_until_dep = dep_dt - now
            minutes_until_dep = int(time_until_dep.total_seconds() / 60)

            if minutes_until_dep < 0:
                continue # Already departed

            # Try to find operator config
            config = None
            window_minutes = getattr(settings, 'TATKAL_DEFAULT_WINDOW_MINUTES', 120)
            quota_seats = 5

            # Attempt to map bus to operator. We'll do a loose match or use defaults.
            # If your Bus model has a ForeignKey to Operator, access it via schedule.bus.operator
            if hasattr(schedule.bus, 'operator') and schedule.bus.operator:
                config = TatkalConfig.objects.filter(operator=schedule.bus.operator).first()
            
            if config:
                window_minutes = config.window_minutes_before
                quota_seats = config.quota_seats

            if minutes_until_dep <= window_minutes:
                # Time to open the window
                quota, created = TatkalQuota.objects.get_or_create(
                    schedule=schedule,
                    source='internal',
                    source_trip_id=str(schedule.id),
                    defaults={
                        'is_open': True,
                        'opened_at': now,
                        'seats_allocated': quota_seats,
                        'seats_booked': 0
                    }
                )
                if not created and not quota.is_open:
                    quota.is_open = True
                    quota.opened_at = now
                    quota.save()
                    opened_count += 1
                elif created:
                    opened_count += 1
                    
        self.stdout.write(self.style.SUCCESS(f'Successfully opened {opened_count} tatkal windows.'))
