from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from .models import (
    School, Group, Student, StudentGroup, StudentParent,
    ContributionEvent, StudentContribution, PaymentHistory
)

User = get_user_model()


class PaymentTrackingTestCase(TestCase):
    """
    Test cases for payment tracking and status management
    """
    
    def setUp(self):
        """Set up test data"""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            address="123 Test Street",
            city="Test City",
            county="Test County",
            phone_number="+254700000000"
        )
        
        # Create users
        self.admin_user = User.objects.create_user(
            phone_number='+254700000001',
            first_name='Admin',
            last_name='User',
            role='admin',
            password='testpass123'
        )
        
        self.teacher_user = User.objects.create_user(
            phone_number='+254700000002',
            first_name='Teacher',
            last_name='User',
            role='teacher',
            password='testpass123'
        )
        
        self.parent_user = User.objects.create_user(
            phone_number='+254700000003',
            first_name='Parent',
            last_name='User',
            role='parent',
            password='testpass123'
        )
        
        # Create group
        self.group = Group.objects.create(
            name="Test Class",
            description="Test class description",
            group_type="class",
            school=self.school,
            teacher=self.teacher_user
        )
        
        # Create student
        self.student = Student.objects.create(
            first_name="Test",
            last_name="Student",
            date_of_birth="2010-01-01",
            gender="male",
            school=self.school,
            student_id="ST001",
            admission_date="2020-01-01"
        )
        
        # Create student-group relationship
        self.student_group = StudentGroup.objects.create(
            student=self.student,
            group=self.group,
            academic_year="2024-2025"
        )
        
        # Create student-parent relationship
        self.student_parent = StudentParent.objects.create(
            student=self.student,
            parent=self.parent_user,
            relationship="father",
            is_primary_contact=True
        )
        
        # Create contribution event
        self.event = ContributionEvent.objects.create(
            name="Test Event",
            description="Test event description",
            event_type="field_trip",
            school=self.school,
            amount=Decimal('1000.00'),
            currency="KES",
            due_date=timezone.now() + timezone.timedelta(days=30),
            created_by=self.admin_user
        )
        
        # Assign group to event
        self.event.groups.add(self.group)
        
        # Create student contribution
        self.contribution = StudentContribution.objects.create(
            student=self.student,
            event=self.event,
            amount_required=Decimal('1000.00'),
            payment_status='pending'
        )
    
    def test_payment_status_updates(self):
        """Test that payment status updates correctly based on amounts"""
        # Test initial status
        self.assertEqual(self.contribution.payment_status, 'pending')
        self.assertEqual(self.contribution.amount_paid, 0)
        
        # Test partial payment
        self.contribution.amount_paid = Decimal('500.00')
        self.contribution.update_payment_status()
        self.assertEqual(self.contribution.payment_status, 'partial')
        
        # Test full payment
        self.contribution.amount_paid = Decimal('1000.00')
        self.contribution.update_payment_status()
        self.assertEqual(self.contribution.payment_status, 'paid')
        
        # Test overdue status
        self.event.due_date = timezone.now() - timezone.timedelta(days=1)
        self.event.save()
        self.contribution.amount_paid = 0
        self.contribution.update_payment_status()
        self.assertEqual(self.contribution.payment_status, 'overdue')
    
    def test_manual_payment_confirmation(self):
        """Test manual payment confirmation"""
        # Confirm payment
        self.contribution.confirm_payment(self.admin_user, "Test confirmation")
        
        # Check confirmation fields
        self.assertEqual(self.contribution.confirmed_by, self.admin_user)
        self.assertIsNotNone(self.contribution.confirmed_at)
        self.assertEqual(self.contribution.confirmation_notes, "Test confirmation")
        self.assertEqual(self.contribution.payment_status, 'confirmed')
    
    def test_payment_history_creation(self):
        """Test payment history creation and contribution updates"""
        # Create payment history
        payment = PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('500.00'),
            payment_method='mpesa_stk',
            transaction_id='TXN123456',
            status='completed',
            payment_date=timezone.now(),
            processed_at=timezone.now(),
            notes='Test payment',
            created_by=self.admin_user
        )
        
        # Check that contribution was updated
        self.contribution.refresh_from_db()
        self.assertEqual(self.contribution.amount_paid, Decimal('500.00'))
        self.assertEqual(self.contribution.payment_status, 'partial')
        # Note: payment_method and transaction_id are not automatically updated from PaymentHistory
        # They need to be set manually or through a different mechanism
    
    def test_payment_history_update(self):
        """Test payment history update affects contribution"""
        # Create initial payment
        payment = PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('500.00'),
            payment_method='mpesa_stk',
            status='completed',
            created_by=self.admin_user
        )
        
        # Update payment amount
        payment.amount = Decimal('750.00')
        payment.save()
        
        # Check that contribution was updated
        self.contribution.refresh_from_db()
        self.assertEqual(self.contribution.amount_paid, Decimal('750.00'))
    
    def test_payment_percentage_calculation(self):
        """Test payment percentage calculation"""
        # Test 0% payment
        self.assertEqual(self.contribution.payment_percentage, 0)
        
        # Test 50% payment
        self.contribution.amount_paid = Decimal('500.00')
        self.contribution.save()
        self.assertEqual(self.contribution.payment_percentage, 50.0)
        
        # Test 100% payment
        self.contribution.amount_paid = Decimal('1000.00')
        self.contribution.save()
        self.assertEqual(self.contribution.payment_percentage, 100.0)
    
    def test_amount_remaining_calculation(self):
        """Test amount remaining calculation"""
        # Test full amount remaining
        self.assertEqual(self.contribution.amount_remaining, Decimal('1000.00'))
        
        # Test partial payment
        self.contribution.amount_paid = Decimal('300.00')
        self.contribution.save()
        self.assertEqual(self.contribution.amount_remaining, Decimal('700.00'))
        
        # Test no amount remaining
        self.contribution.amount_paid = Decimal('1000.00')
        self.contribution.save()
        self.assertEqual(self.contribution.amount_remaining, Decimal('0.00'))
    
    def test_payment_history_properties(self):
        """Test payment history properties"""
        # Create completed payment
        completed_payment = PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('500.00'),
            status='completed',
            created_by=self.admin_user
        )
        
        # Create failed payment
        failed_payment = PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('200.00'),
            status='failed',
            created_by=self.admin_user
        )
        
        # Test properties
        self.assertTrue(completed_payment.is_completed)
        self.assertFalse(completed_payment.is_failed)
        
        self.assertFalse(failed_payment.is_completed)
        self.assertTrue(failed_payment.is_failed)
    
    def test_get_payment_history(self):
        """Test getting payment history for a contribution"""
        # Create multiple payments
        PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('300.00'),
            status='completed',
            created_by=self.admin_user
        )
        
        PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('400.00'),
            status='completed',
            created_by=self.admin_user
        )
        
        PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('300.00'),
            status='completed',
            created_by=self.admin_user
        )
        
        # Get payment history
        history = self.contribution.get_payment_history()
        
        # Check that we got 3 payments
        self.assertEqual(history.count(), 3)
        
        # Check total amount
        total_amount = sum(payment.amount for payment in history)
        self.assertEqual(total_amount, Decimal('1000.00'))
