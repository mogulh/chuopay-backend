import requests
import json
import base64
import hashlib
import time
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import PaymentHistory, StudentContribution


class MPESAService:
    """
    Service class for handling MPESA API interactions
    """
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.business_short_code = settings.MPESA_BUSINESS_SHORT_CODE
        self.passkey = settings.MPESA_PASSKEY
        self.environment = settings.MPESA_ENVIRONMENT
        
        # API URLs
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """
        Get MPESA API access token
        """
        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Create credentials
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('access_token')
            
        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Failed to get MPESA access token: {str(e)}")
        except KeyError:
            raise ValidationError("Invalid response from MPESA API")
    
    def generate_password(self, timestamp):
        """
        Generate MPESA API password
        """
        data_to_encode = f"{self.business_short_code}{self.passkey}{timestamp}"
        encoded_string = base64.b64encode(data_to_encode.encode()).decode()
        return encoded_string
    
    def initiate_stk_push(self, phone_number, amount, contribution_id, reference=None):
        """
        Initiate STK Push payment
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Generate password
            password = self.generate_password(timestamp)
            
            # Prepare request data
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Format phone number (remove + and add 254 if needed)
            formatted_phone = self.format_phone_number(phone_number)
            
            # Create reference
            if not reference:
                reference = f"CONT_{contribution_id}_{int(time.time())}"
            
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": formatted_phone,
                "PartyB": self.business_short_code,
                "PhoneNumber": formatted_phone,
                "CallBackURL": f"{settings.BASE_URL}/api/contributions/mpesa/callback/",
                "AccountReference": reference,
                "TransactionDesc": f"School Contribution Payment - {reference}"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Create payment history record
            payment_history = PaymentHistory.objects.create(
                contribution_id=contribution_id,
                amount=amount,
                payment_method='mpesa_stk',
                transaction_id=data.get('CheckoutRequestID', ''),
                status='pending',
                external_id=data.get('CheckoutRequestID', ''),
                external_response=data,
                notes=f"STK Push initiated for {formatted_phone}",
                created_by_id=1  # System user
            )
            
            # Schedule status check after 2 minutes
            from .tasks import check_mpesa_payment_status
            check_mpesa_payment_status.apply_async(
                args=[payment_history.id],
                countdown=120  # 2 minutes
            )
            
            return {
                'success': True,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'merchant_request_id': data.get('MerchantRequestID'),
                'payment_history_id': payment_history.id,
                'message': 'STK Push sent successfully'
            }
            
        except requests.exceptions.RequestException as e:
            raise ValidationError(f"STK Push failed: {str(e)}")
        except Exception as e:
            raise ValidationError(f"STK Push error: {str(e)}")
    
    def format_phone_number(self, phone_number):
        """
        Format phone number for MPESA API
        """
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone_number))
        
        # If it starts with 0, replace with 254
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        
        # If it starts with +, remove it
        if phone.startswith('+'):
            phone = phone[1:]
        
        # If it doesn't start with 254, add it
        if not phone.startswith('254'):
            phone = '254' + phone
        
        return phone
    
    def process_callback(self, callback_data):
        """
        Process MPESA callback/webhook
        """
        try:
            # Extract data from callback
            checkout_request_id = callback_data.get('CheckoutRequestID')
            result_code = callback_data.get('ResultCode')
            result_desc = callback_data.get('ResultDesc')
            amount = callback_data.get('Amount')
            mpesa_receipt_number = callback_data.get('MpesaReceiptNumber')
            transaction_date = callback_data.get('TransactionDate')
            
            # Find payment history record
            try:
                payment_history = PaymentHistory.objects.get(
                    external_id=checkout_request_id,
                    payment_method='mpesa_stk'
                )
            except PaymentHistory.DoesNotExist:
                raise ValidationError(f"Payment history not found for {checkout_request_id}")
            
            # Update payment status based on result code
            if result_code == 0:
                # Success
                payment_history.status = 'completed'
                payment_history.external_status = 'success'
                payment_history.transaction_id = mpesa_receipt_number
                payment_history.processed_at = timezone.now()
                payment_history.external_response = callback_data
                payment_history.save()
                
                # Update contribution amount paid
                contribution = payment_history.contribution
                contribution.amount_paid += payment_history.amount
                contribution.save()
                
                return {
                    'success': True,
                    'message': 'Payment processed successfully',
                    'payment_history_id': payment_history.id
                }
            else:
                # Failed
                payment_history.status = 'failed'
                payment_history.external_status = 'failed'
                payment_history.processed_at = timezone.now()
                payment_history.external_response = callback_data
                payment_history.notes = f"Payment failed: {result_desc}"
                payment_history.save()
                
                return {
                    'success': False,
                    'message': f'Payment failed: {result_desc}',
                    'payment_history_id': payment_history.id
                }
                
        except Exception as e:
            raise ValidationError(f"Callback processing error: {str(e)}")
    
    def check_payment_status(self, checkout_request_id):
        """
        Check payment status using MPESA API
        """
        try:
            access_token = self.get_access_token()
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Status check failed: {str(e)}")
    
    def validate_phone_number(self, phone_number):
        """
        Validate phone number format
        """
        formatted_phone = self.format_phone_number(phone_number)
        
        # Check if it's a valid Kenyan phone number
        if not formatted_phone.startswith('254'):
            raise ValidationError("Invalid phone number format")
        
        if len(formatted_phone) != 12:
            raise ValidationError("Invalid phone number length")
        
        return formatted_phone 