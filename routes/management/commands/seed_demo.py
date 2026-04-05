from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from routes.models import Route, Bus, Stop, Fare
from conductors.models import Conductor

class Command(BaseCommand):
    help = 'Seeds demo data for Coimbatore bus routes, stops, and fares'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing data...')
        Fare.objects.all().delete()
        Stop.objects.all().delete()
        Bus.objects.all().delete()
        Route.objects.all().delete()
        Conductor.objects.all().delete()

        # Users for Conductors
        u1, _ = User.objects.get_or_create(username='conductor1', defaults={'first_name': 'Ramesh'})
        if not u1.check_password('demo1234'):
            u1.set_password('demo1234')
            u1.save()

        u2, _ = User.objects.get_or_create(username='conductor2', defaults={'first_name': 'Suresh'})
        if not u2.check_password('demo1234'):
            u2.set_password('demo1234')
            u2.save()

        # Admin user
        admin_user, admin_created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True, 'email': 'admin@test.com'})
        if admin_created:
            admin_user.set_password('admin123')
            admin_user.save()

        # Create Routes in Coimbatore
        route1 = Route.objects.create(name='Gandhipuram to Ukkadam', description='Via Town Hall')
        route2 = Route.objects.create(name='Vadavalli to Singanallur', description='Via R.S. Puram, Railway Station')

        self.stdout.write('Created Routes')

        # Buses (5 total as requested)
        bus1 = Bus.objects.create(bus_number='TN 38 A 0001', route=route1)
        bus2 = Bus.objects.create(bus_number='TN 38 A 0002', route=route1)
        bus3 = Bus.objects.create(bus_number='TN 38 B 0003', route=route1)
        bus4 = Bus.objects.create(bus_number='TN 38 C 0004', route=route2)
        bus5 = Bus.objects.create(bus_number='TN 38 C 0005', route=route2)

        self.stdout.write('Created 5 Buses')

        # Conductors
        Conductor.objects.create(user=u1, employee_id='C-001', bus=bus1)
        Conductor.objects.create(user=u2, employee_id='C-002', bus=bus4)

        self.stdout.write('Created Conductors')

        # Stops for Route 1 (Gandhipuram to Ukkadam)
        route1_stops_data = [
            ('Gandhipuram', 'காந்திபுரம்'),
            ('Cross Cut Road', 'குறுக்கு வீதி'),
            ('Town Hall', 'டவுன்ஹால்'),
            ('Oppanakara Street', 'ஒப்பணக்கார வீதி'),
            ('Railway Station', 'ரயில் நிலையம்'),
            ('Ukkadam', 'உக்கடம்'),
        ]
        r1_stops = []
        for idx, (en, ta) in enumerate(route1_stops_data):
            r1_stops.append(Stop.objects.create(route=route1, name=en, name_tamil=ta, order=idx+1))

        # Stops for Route 2 (Vadavalli to Singanallur)
        route2_stops_data = [
            ('Vadavalli', 'வடவள்ளி'),
            ('Bharathiar University', 'பாரதியார் பல்கலைக்கழகம்'),
            ('Lawley Road', 'லாலி ரோடு'),
            ('R.S. Puram', 'ஆர்.எஸ்.புரம்'),
            ('Railway Station', 'ரயில் நிலையம்'),
            ('Ramanathapuram', 'ராமநாதபுரம்'),
            ('Singanallur', 'சிங்காநல்லூர்'),
        ]
        r2_stops = []
        for idx, (en, ta) in enumerate(route2_stops_data):
            r2_stops.append(Stop.objects.create(route=route2, name=en, name_tamil=ta, order=idx+1))

        self.stdout.write('Created Stops')

        # Generate Fares: Base ₹5 + ₹5/stop increment (Distance based)
        fares_created = 0
        def create_fares_for_stops(stops_list):
            count = 0
            for i, from_stop in enumerate(stops_list):
                for j, to_stop in enumerate(stops_list):
                    if i < j:
                        # Forward journey
                        distance = to_stop.order - from_stop.order
                        amount = 5.0 + (distance - 1) * 5.0 if distance > 0 else 5.0
                        Fare.objects.create(from_stop=from_stop, to_stop=to_stop, amount=amount)
                        count += 1
            return count

        fares_created += create_fares_for_stops(r1_stops)
        fares_created += create_fares_for_stops(r2_stops)

        self.stdout.write(f'Created {fares_created} Fares successfully')
        self.stdout.write(self.style.SUCCESS('Seed complete!'))
