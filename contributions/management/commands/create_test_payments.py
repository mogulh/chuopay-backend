from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from contributions.models import (
    School, Group, Student, StudentGroup, StudentParent,
    ContributionEvent, StudentContribution, PaymentHistory
)
from decimal import Decimal
import random
from datetime import timedelta
from django.db import models

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test payment data for testing payment tracking system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            help='School ID to create payments for (optional)',
        )
        parser.add_argument(
            '--event-id',
            type=int,
            help='Event ID to create payments for (optional)',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of payment transactions to create (default: 50)',
        )

    def handle(self, *args, **options):
        school_id = options.get('school_id')
        event_id = options.get('event_id')
        count = options.get('count')

        # Get or create test data
        if school_id:
            school = School.objects.get(id=school_id)
        else:
            school = School.objects.first()
            if not school:
                self.stdout.write(self.style.ERROR('No schools found. Please create a school first.'))
                return

        # Get events
        if event_id:
            events = ContributionEvent.objects.filter(id=event_id)
        else:
            events = ContributionEvent.objects.filter(school=school, is_published=True)

        if not events.exists():
            self.stdout.write(self.style.ERROR('No published events found. Please create and publish events first.'))
            return

        # Get contributions
        contributions = StudentContribution.objects.filter(event__in=events)
        if not contributions.exists():
            self.stdout.write(self.style.ERROR('No student contributions found. Please create student contributions first.'))
            return

        # Get users for creating payments
        users = User.objects.filter(role__in=['admin', 'teacher'])
        if not users.exists():
            self.stdout.write(self.style.ERROR('No admin or teacher users found.'))
            return

        # Payment methods
        payment_methods = ['mpesa_stk', 'mpesa_ussd', 'bank_transfer', 'cash', 'manual']
        statuses = ['completed', 'pending', 'failed', 'cancelled']

        created_count = 0
        for i in range(count):
            # Select random contribution
            contribution = random.choice(contributions)
            
            # Generate payment amount (partial or full)
            if random.random() < 0.7:  # 70% chance of full payment
                amount = contribution.amount_required
            else:
                # Partial payment
                amount = contribution.amount_required * Decimal(random.uniform(0.1, 0.9))

            # Generate payment date (within last 30 days)
            days_ago = random.randint(0, 30)
            payment_date = timezone.now() - timedelta(days=days_ago)

            # Select status (mostly completed)
            if random.random() < 0.8:  # 80% completed
                status = 'completed'
                processed_at = payment_date
            else:
                status = random.choice(['pending', 'failed', 'cancelled'])
                processed_at = None

            # Create payment history
            payment = PaymentHistory.objects.create(
                contribution=contribution,
                amount=amount,
                payment_method=random.choice(payment_methods),
                transaction_id=f"TXN{random.randint(100000, 999999)}",
                status=status,
                payment_date=payment_date,
                processed_at=processed_at,
                notes=f"Test payment {i+1}",
                created_by=random.choice(users)
            )

            # Update contribution if payment is completed
            if status == 'completed':
                contribution.amount_paid += amount
                contribution.payment_date = payment_date
                contribution.payment_method = payment.payment_method
                contribution.transaction_id = payment.transaction_id
                contribution.update_payment_status()
                contribution.save()

            created_count += 1

            if (i + 1) % 10 == 0:
                self.stdout.write(f'Created {i + 1} payment transactions...')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} payment transactions for {contributions.count()} contributions'
            )
        )

        # Print summary
        total_payments = PaymentHistory.objects.count()
        completed_payments = PaymentHistory.objects.filter(status='completed').count()
        total_amount = PaymentHistory.objects.filter(status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        self.stdout.write(f'\nPayment Summary:')
        self.stdout.write(f'Total payments: {total_payments}')
        self.stdout.write(f'Completed payments: {completed_payments}')
        self.stdout.write(f'Success rate: {(completed_payments/total_payments*100):.1f}%')
        self.stdout.write(f'Total amount processed: {total_amount}') 