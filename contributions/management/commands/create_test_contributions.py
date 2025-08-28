from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from contributions.models import (
    School, Group, Student, StudentGroup, StudentParent,
    ContributionEvent, ContributionTier, StudentContribution
)
from django.db.models import Sum, Count

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test student contributions for parent dashboard'

    def handle(self, *args, **options):
        self.stdout.write('Creating test student contributions...')
        
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
        
        # Get parent users
        try:
            parent1 = User.objects.get(phone_number='+254700000003')
            parent2 = User.objects.get(phone_number='+254700000004')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Parent users not found. Run create_test_data first.'))
            return
        
        # Get events
        events = ContributionEvent.objects.filter(school=school)
        if not events.exists():
            self.stdout.write(self.style.ERROR('No events found. Run create_test_events first.'))
            return
        
        # Get students
        students = Student.objects.filter(school=school, is_active=True)
        if not students.exists():
            self.stdout.write(self.style.ERROR('No students found. Run create_test_data first.'))
            return
        
        # Create test contributions with different payment statuses
        contribution_data = [
            # Alice Johnson (Parent 1) - Paid contributions
            {
                'student': students.get(first_name='Alice'),
                'event': events.get(name='Field Trip to National Museum'),
                'amount_required': 2500.00,
                'amount_paid': 2500.00,
                'payment_status': 'paid',
                'payment_date': timezone.now() - timedelta(days=5),
                'payment_method': 'mpesa_stk',
                'transaction_id': 'MPESA123456',
                'notes': 'Paid via MPESA STK Push'
            },
            {
                'student': students.get(first_name='Alice'),
                'event': events.get(name='School Uniform Payment'),
                'amount_required': 3500.00,
                'amount_paid': 3500.00,
                'payment_status': 'paid',
                'payment_date': timezone.now() - timedelta(days=2),
                'payment_method': 'cash',
                'transaction_id': '',
                'notes': 'Paid at school office'
            },
            # Bob Smith (Parent 1) - Partial payment
            {
                'student': students.get(first_name='Bob'),
                'event': events.get(name='Field Trip to National Museum'),
                'amount_required': 2500.00,
                'amount_paid': 1500.00,
                'payment_status': 'partial',
                'payment_date': timezone.now() - timedelta(days=3),
                'payment_method': 'mpesa_ussd',
                'transaction_id': 'MPESA789012',
                'notes': 'Partial payment via USSD'
            },
            {
                'student': students.get(first_name='Bob'),
                'event': events.get(name='School Uniform Payment'),
                'amount_required': 3500.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            },
            # Charlie Brown (Parent 2) - Pending payments
            {
                'student': students.get(first_name='Charlie'),
                'event': events.get(name='Field Trip to National Museum'),
                'amount_required': 2500.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            },
            {
                'student': students.get(first_name='Charlie'),
                'event': events.get(name='School Uniform Payment'),
                'amount_required': 3500.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            },
            # Diana Wilson (Parent 2) - Mixed status
            {
                'student': students.get(first_name='Diana'),
                'event': events.get(name='Field Trip to National Museum'),
                'amount_required': 2500.00,
                'amount_paid': 2500.00,
                'payment_status': 'paid',
                'payment_date': timezone.now() - timedelta(days=1),
                'payment_method': 'bank_transfer',
                'transaction_id': 'BANK456789',
                'notes': 'Bank transfer completed'
            },
            {
                'student': students.get(first_name='Diana'),
                'event': events.get(name='School Uniform Payment'),
                'amount_required': 3500.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            },
            # Textbook payments (all pending)
            {
                'student': students.get(first_name='Alice'),
                'event': events.get(name='Textbook Payment'),
                'amount_required': 5000.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            },
            {
                'student': students.get(first_name='Bob'),
                'event': events.get(name='Textbook Payment'),
                'amount_required': 5000.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            },
            {
                'student': students.get(first_name='Charlie'),
                'event': events.get(name='Textbook Payment'),
                'amount_required': 5000.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            },
            {
                'student': students.get(first_name='Diana'),
                'event': events.get(name='Textbook Payment'),
                'amount_required': 5000.00,
                'amount_paid': 0.00,
                'payment_status': 'pending',
                'payment_date': None,
                'payment_method': '',
                'transaction_id': '',
                'notes': ''
            }
        ]
        
        created_count = 0
        for contribution_data in contribution_data:
            contribution, created = StudentContribution.objects.get_or_create(
                student=contribution_data['student'],
                event=contribution_data['event'],
                defaults={
                    **contribution_data,
                    'updated_by': admin_user
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    f'Created contribution: {contribution.student.full_name} - '
                    f'{contribution.event.name} ({contribution.payment_status})'
                )
            else:
                self.stdout.write(
                    f'Contribution already exists: {contribution.student.full_name} - '
                    f'{contribution.event.name}'
                )
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} student contributions!'))
        
        # Show summary by parent
        self.stdout.write('\nSummary by Parent:')
        
        for parent in [parent1, parent2]:
            children = Student.objects.filter(parents=parent, is_active=True)
            contributions = StudentContribution.objects.filter(student__in=children)
            
            total_required = contributions.aggregate(total=Sum('amount_required'))['total'] or 0
            total_paid = contributions.aggregate(total=Sum('amount_paid'))['total'] or 0
            payment_percentage = (total_paid / total_required * 100) if total_required > 0 else 0
            
            self.stdout.write(f'\n{parent.full_name}:')
            self.stdout.write(f'  Children: {children.count()}')
            self.stdout.write(f'  Total Required: KES {total_required:,.2f}')
            self.stdout.write(f'  Total Paid: KES {total_paid:,.2f}')
            self.stdout.write(f'  Payment Rate: {payment_percentage:.1f}%')
            
            # Status breakdown
            status_counts = contributions.values('payment_status').annotate(count=Count('id'))
            for status in status_counts:
                self.stdout.write(f'  {status["payment_status"].title()}: {status["count"]}') 