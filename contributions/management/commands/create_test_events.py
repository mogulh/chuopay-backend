from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from contributions.models import School, Group, ContributionEvent, ContributionTier

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test contribution events'

    def handle(self, *args, **options):
        self.stdout.write('Creating test contribution events...')
        
        # Get the test school
        try:
            school = School.objects.get(name='Test School')
        except School.DoesNotExist:
            self.stdout.write(self.style.ERROR('Test School not found. Run create_test_data first.'))
            return
        
        # Get admin user
        try:
            admin_user = User.objects.get(phone_number='+254700000000')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user not found. Run create_test_data first.'))
            return
        
        # Get groups
        groups = Group.objects.filter(school=school)
        if not groups.exists():
            self.stdout.write(self.style.ERROR('No groups found. Run create_test_data first.'))
            return
        
        # Create test events
        events_data = [
            {
                'name': 'Field Trip to National Museum',
                'description': 'Educational field trip to the National Museum of Kenya. Includes transportation, lunch, and guided tour.',
                'event_type': 'field_trip',
                'amount': 2500.00,
                'has_tiers': True,
                'participation_type': 'optional',
                'due_date': timezone.now() + timedelta(days=14),
                'event_date': timezone.now() + timedelta(days=21),
                'is_active': True,
                'is_published': True,
                'tiers': [
                    {'name': 'Basic Package', 'description': 'Transportation and lunch only', 'amount': 2000.00, 'is_default': True},
                    {'name': 'Premium Package', 'description': 'Transportation, lunch, and souvenir', 'amount': 2500.00, 'is_default': False},
                ]
            },
            {
                'name': 'School Uniform Payment',
                'description': 'Payment for new school uniforms for the academic year.',
                'event_type': 'uniform',
                'amount': 3500.00,
                'has_tiers': False,
                'participation_type': 'mandatory',
                'due_date': timezone.now() + timedelta(days=7),
                'event_date': None,
                'is_active': True,
                'is_published': True,
                'tiers': []
            },
            {
                'name': 'Science Fair Contribution',
                'description': 'Contribution for materials and supplies for the annual science fair.',
                'event_type': 'activity',
                'amount': 1500.00,
                'has_tiers': True,
                'participation_type': 'optional',
                'due_date': timezone.now() + timedelta(days=10),
                'event_date': timezone.now() + timedelta(days=30),
                'is_active': True,
                'is_published': False,
                'tiers': [
                    {'name': 'Standard Contribution', 'description': 'Basic materials contribution', 'amount': 1000.00, 'is_default': True},
                    {'name': 'Enhanced Contribution', 'description': 'Premium materials and snacks', 'amount': 1500.00, 'is_default': False},
                ]
            },
            {
                'name': 'Textbook Payment',
                'description': 'Payment for required textbooks for the new term.',
                'event_type': 'textbook',
                'amount': 5000.00,
                'has_tiers': False,
                'participation_type': 'mandatory',
                'due_date': timezone.now() + timedelta(days=5),
                'event_date': None,
                'is_active': True,
                'is_published': True,
                'tiers': []
            }
        ]
        
        for event_data in events_data:
            tiers_data = event_data.pop('tiers')
            
            # Create or get the event
            event, created = ContributionEvent.objects.get_or_create(
                name=event_data['name'],
                school=school,
                defaults={
                    **event_data,
                    'created_by': admin_user
                }
            )
            
            if created:
                self.stdout.write(f'Created event: {event.name}')
                
                # Assign all groups to the event
                event.groups.set(groups)
                
                # Create tiers if specified
                for tier_data in tiers_data:
                    tier, tier_created = ContributionTier.objects.get_or_create(
                        event=event,
                        name=tier_data['name'],
                        defaults=tier_data
                    )
                    if tier_created:
                        self.stdout.write(f'  - Created tier: {tier.name} (KES {tier.amount})')
            else:
                self.stdout.write(f'Event already exists: {event.name}')
        
        self.stdout.write(self.style.SUCCESS('Test contribution events created successfully!'))
        self.stdout.write('\nCreated Events:')
        for event in ContributionEvent.objects.filter(school=school):
            self.stdout.write(f'- {event.name} (KES {event.amount}) - {event.get_event_type_display()}')
            if event.has_tiers:
                for tier in event.tiers.all():
                    self.stdout.write(f'  * {tier.name}: KES {tier.amount}') 