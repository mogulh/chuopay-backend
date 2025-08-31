from django.core.management.base import BaseCommand
from contributions.models import School, SchoolSection
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default sections (Primary, Secondary, Nursery) for existing schools'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            help='Create sections for a specific school ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create sections for all schools',
        )

    def handle(self, *args, **options):
        if options['school_id']:
            schools = School.objects.filter(id=options['school_id'])
        elif options['all']:
            schools = School.objects.all()
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --school-id or --all')
            )
            return

        if not schools.exists():
            self.stdout.write(
                self.style.ERROR('No schools found')
            )
            return

        # Default sections to create
        default_sections = [
            {
                'name': 'nursery',
                'display_name': 'Nursery School',
                'description': 'Early childhood education section'
            },
            {
                'name': 'primary',
                'display_name': 'Primary School',
                'description': 'Primary education section (Grades 1-8)'
            },
            {
                'name': 'secondary',
                'display_name': 'Secondary School',
                'description': 'Secondary education section (Grades 9-12)'
            }
        ]

        for school in schools:
            self.stdout.write(f'Creating sections for school: {school.name}')
            
            for section_data in default_sections:
                section, created = SchoolSection.objects.get_or_create(
                    school=school,
                    name=section_data['name'],
                    defaults={
                        'display_name': section_data['display_name'],
                        'description': section_data['description'],
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Created section: {section.display_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  - Section already exists: {section.display_name}')
                    )

        self.stdout.write(
            self.style.SUCCESS('Successfully created default sections!')
        )

