from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from contributions.models import School, Group, Student, ContributionEvent, StudentContribution, PaymentHistory
from contributions.analytics_service import AnalyticsService
from decimal import Decimal
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Test analytics functionality and generate sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--generate-data',
            action='store_true',
            help='Generate sample analytics data'
        )
        parser.add_argument(
            '--test-analytics',
            action='store_true',
            help='Test analytics calculations'
        )
        parser.add_argument(
            '--time-range',
            type=str,
            default='30d',
            help='Time range for analytics (7d, 30d, 90d, 1y)'
        )

    def handle(self, *args, **options):
        if options.get('generate_data'):
            self.generate_sample_data()
        elif options.get('test_analytics'):
            self.test_analytics(options.get('time_range'))
        else:
            self.stdout.write(self.style.ERROR('Please specify --generate-data or --test-analytics'))

    def generate_sample_data(self):
        """Generate sample data for analytics testing"""
        self.stdout.write("Generating sample analytics data...")
        
        # Create or get school
        school, created = School.objects.get_or_create(
            name='Test School',
            defaults={
                'address': 'Test Address',
                'phone_number': '254700000000',
                'email': 'test@school.com'
            }
        )
        
        # Create or get admin user
        admin_user, created = User.objects.get_or_create(
            phone_number='254700000000',
            defaults={
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Create groups
        groups = []
        group_names = ['Class 6A', 'Class 6B', 'Class 7A', 'Class 7B', 'Drama Club', 'Sports Team']
        for name in group_names:
            group, created = Group.objects.get_or_create(
                name=name,
                school=school,
                defaults={'description': f'Test {name}'}
            )
            groups.append(group)
        
        # Create students
        students = []
        for i in range(20):
            student, created = Student.objects.get_or_create(
                name=f'Student {i+1}',
                school=school,
                defaults={'parent_phone': f'25470000000{i:02d}'}
            )
            students.append(student)
        
        # Create events
        events = []
        event_data = [
            ('Field Trip', 5000, 30),
            ('Sports Equipment', 2000, 15),
            ('Library Books', 1500, 20),
            ('Science Lab', 8000, 45),
            ('Art Supplies', 3000, 25),
            ('Computer Lab', 12000, 60),
        ]
        
        for name, amount, days_ago in event_data:
            due_date = datetime.now().date() - timedelta(days=days_ago)
            event, created = ContributionEvent.objects.get_or_create(
                name=name,
                school=school,
                defaults={
                    'description': f'Test {name}',
                    'amount_required': Decimal(amount),
                    'due_date': due_date,
                    'is_published': True
                }
            )
            events.append(event)
        
        # Create contributions and payments
        payment_methods = ['mpesa_stk', 'mpesa_ussd', 'bank_transfer', 'cash', 'manual']
        statuses = ['completed', 'pending', 'failed']
        
        for event in events:
            # Assign students to event
            for student in students[:random.randint(10, 15)]:
                contribution, created = StudentContribution.objects.get_or_create(
                    student=student,
                    event=event,
                    defaults={
                        'amount_required': event.amount_required,
                        'amount_paid': Decimal('0.00'),
                        'payment_status': 'pending'
                    }
                )
                
                # Create some payments
                if random.random() > 0.3:  # 70% chance of having payments
                    payment_amount = event.amount_required * Decimal(random.uniform(0.5, 1.0))
                    payment_date = datetime.now() - timedelta(days=random.randint(1, 30))
                    
                    payment = PaymentHistory.objects.create(
                        contribution=contribution,
                        amount=payment_amount,
                        payment_method=random.choice(payment_methods),
                        status=random.choice(statuses),
                        payment_date=payment_date,
                        created_by=admin_user,
                        transaction_id=f'PAY_{random.randint(100000, 999999)}'
                    )
                    
                    # Update contribution
                    if payment.status == 'completed':
                        contribution.amount_paid = payment_amount
                        contribution.payment_status = 'paid' if payment_amount >= event.amount_required else 'partial'
                        contribution.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Generated sample data: {School.objects.count()} schools, {Group.objects.count()} groups, {Student.objects.count()} students, {ContributionEvent.objects.count()} events, {StudentContribution.objects.count()} contributions, {PaymentHistory.objects.count()} payments')
        )

    def test_analytics(self, time_range):
        """Test analytics calculations"""
        self.stdout.write(f"Testing analytics with time range: {time_range}")
        
        # Get first admin user
        try:
            admin_user = User.objects.filter(role='admin').first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('No admin user found. Please create one first.'))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return
        
        # Initialize analytics service
        analytics_service = AnalyticsService(
            user=admin_user,
            time_range=time_range
        )
        
        # Test overview statistics
        self.stdout.write("Testing overview statistics...")
        overview = analytics_service.get_overview_statistics()
        self.stdout.write(f"Overview: {overview}")
        
        # Test trends data
        self.stdout.write("Testing trends data...")
        trends = analytics_service.get_trends_data()
        self.stdout.write(f"Trends: {len(trends['daily_collections'])} daily collections, {len(trends['weekly_collections'])} weekly collections, {len(trends['monthly_collections'])} monthly collections")
        
        # Test breakdown data
        self.stdout.write("Testing breakdown data...")
        breakdown = analytics_service.get_breakdown_data()
        self.stdout.write(f"Breakdown: {len(breakdown['by_event_type'])} event types, {len(breakdown['by_payment_method'])} payment methods, {len(breakdown['by_status'])} statuses")
        
        # Test top performers
        self.stdout.write("Testing top performers...")
        top_performers = analytics_service.get_top_performers()
        self.stdout.write(f"Top performers: {len(top_performers['events'])} events, {len(top_performers['groups'])} groups")
        
        # Test payment analytics
        self.stdout.write("Testing payment analytics...")
        payment_analytics = analytics_service.get_payment_analytics()
        self.stdout.write(f"Payment analytics: {payment_analytics['success_rate']}% success rate, {payment_analytics['total_transactions']} total transactions")
        
        # Test financial reports
        self.stdout.write("Testing financial reports...")
        financial_reports = analytics_service.get_financial_reports()
        self.stdout.write(f"Financial reports: {len(financial_reports['monthly_revenue'])} months, {len(financial_reports['outstanding_by_event'])} events with outstanding amounts")
        
        self.stdout.write(self.style.SUCCESS("Analytics testing completed successfully!")) 