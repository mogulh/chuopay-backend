from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from contributions.models import StudentContribution, PaymentHistory
from contributions.mpesa_service import MPESAService


class Command(BaseCommand):
    help = 'Test MPESA integration functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contribution-id',
            type=int,
            help='Contribution ID to test with'
        )
        parser.add_argument(
            '--phone-number',
            type=str,
            default='254700000000',
            help='Phone number to test with (default: 254700000000)'
        )
        parser.add_argument(
            '--amount',
            type=float,
            default=10.0,
            help='Amount to test with (default: 10.0)'
        )
        parser.add_argument(
            '--test-callback',
            action='store_true',
            help='Test callback processing'
        )

    def handle(self, *args, **options):
        contribution_id = options.get('contribution_id')
        phone_number = options.get('phone_number')
        amount = options.get('amount')
        test_callback = options.get('test_callback')

        if test_callback:
            self.test_callback_processing()
        else:
            self.test_stk_push(contribution_id, phone_number, amount)

    def test_stk_push(self, contribution_id, phone_number, amount):
        """Test STK Push initiation"""
        self.stdout.write("Testing MPESA STK Push integration...")
        
        # Get contribution
        if contribution_id:
            try:
                contribution = StudentContribution.objects.get(id=contribution_id)
            except StudentContribution.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Contribution {contribution_id} not found')
                )
                return
        else:
            # Get first available contribution
            contribution = StudentContribution.objects.first()
            if not contribution:
                self.stdout.write(
                    self.style.ERROR('No contributions found. Please create contributions first.')
                )
                return
        
        self.stdout.write(f"Using contribution: {contribution.id} - {contribution.event.name}")
        self.stdout.write(f"Phone number: {phone_number}")
        self.stdout.write(f"Amount: KES {amount}")
        
        # Initialize MPESA service
        try:
            mpesa_service = MPESAService()
            
            # Test phone number validation
            self.stdout.write("Testing phone number validation...")
            formatted_phone = mpesa_service.validate_phone_number(phone_number)
            self.stdout.write(f"Formatted phone number: {formatted_phone}")
            
            # Test STK Push initiation
            self.stdout.write("Testing STK Push initiation...")
            result = mpesa_service.initiate_stk_push(
                phone_number=formatted_phone,
                amount=amount,
                contribution_id=contribution.id
            )
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"STK Push initiated successfully!")
                )
                self.stdout.write(f"Checkout Request ID: {result['checkout_request_id']}")
                self.stdout.write(f"Merchant Request ID: {result['merchant_request_id']}")
                self.stdout.write(f"Payment History ID: {result['payment_history_id']}")
                
                # Show payment history
                payment_history = PaymentHistory.objects.get(id=result['payment_history_id'])
                self.stdout.write(f"Payment Status: {payment_history.status}")
                self.stdout.write(f"External ID: {payment_history.external_id}")
                
            else:
                self.stdout.write(
                    self.style.ERROR(f"STK Push failed: {result.get('message', 'Unknown error')}")
                )
                
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f"Validation error: {str(e)}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            )

    def test_callback_processing(self):
        """Test callback processing"""
        self.stdout.write("Testing MPESA callback processing...")
        
        # Get a pending payment
        pending_payment = PaymentHistory.objects.filter(
            status='pending',
            payment_method='mpesa_stk'
        ).first()
        
        if not pending_payment:
            self.stdout.write(
                self.style.ERROR('No pending MPESA payments found. Please initiate a payment first.')
            )
            return
        
        self.stdout.write(f"Testing callback for payment: {pending_payment.id}")
        self.stdout.write(f"External ID: {pending_payment.external_id}")
        
        # Create mock callback data
        mock_callback = {
            "CheckoutRequestID": pending_payment.external_id,
            "ResultCode": 0,  # Success
            "ResultDesc": "The service request is processed successfully.",
            "Amount": float(pending_payment.amount),
            "MpesaReceiptNumber": f"MPESA{pending_payment.id:06d}",
            "TransactionDate": "20241201120000",
            "PhoneNumber": "254700000000"
        }
        
        # Initialize MPESA service
        try:
            mpesa_service = MPESAService()
            
            # Process callback
            result = mpesa_service.process_callback(mock_callback)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS("Callback processed successfully!")
                )
                self.stdout.write(f"Payment History ID: {result['payment_history_id']}")
                
                # Refresh payment history
                pending_payment.refresh_from_db()
                self.stdout.write(f"New Status: {pending_payment.status}")
                self.stdout.write(f"Processed At: {pending_payment.processed_at}")
                
            else:
                self.stdout.write(
                    self.style.ERROR(f"Callback processing failed: {result.get('message', 'Unknown error')}")
                )
                
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f"Validation error: {str(e)}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            ) 