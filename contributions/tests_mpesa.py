import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import School, Group, Student, ContributionEvent, StudentContribution, PaymentHistory
from .mpesa_service import MPESAService

User = get_user_model()


class MPESAServiceTestCase(TestCase):
    """Test cases for MPESAService"""
    
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            phone_number='254700000000',
            password='testpass123',
            role='admin'
        )
        
        self.school = School.objects.create(
            name='Test School',
            address='Test Address',
            phone_number='254700000000',
            email='test@school.com'
        )
        
        self.group = Group.objects.create(
            name='Test Class',
            school=self.school,
            description='Test class description'
        )
        
        self.student = Student.objects.create(
            name='Test Student',
            school=self.school,
            parent_phone='254700000000'
        )
        
        self.event = ContributionEvent.objects.create(
            name='Test Event',
            description='Test event description',
            school=self.school,
            amount_required=Decimal('100.00'),
            due_date='2024-12-31',
            is_published=True
        )
        
        self.contribution = StudentContribution.objects.create(
            student=self.student,
            event=self.event,
            amount_required=Decimal('100.00'),
            amount_paid=Decimal('0.00')
        )
    
    def test_phone_number_formatting(self):
        """Test phone number formatting"""
        mpesa_service = MPESAService()
        
        # Test various phone number formats
        test_cases = [
            ('0700000000', '254700000000'),
            ('+254700000000', '254700000000'),
            ('254700000000', '254700000000'),
            ('700000000', '254700000000'),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(input_phone=input_phone):
                result = mpesa_service.format_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_phone_number_validation(self):
        """Test phone number validation"""
        mpesa_service = MPESAService()
        
        # Valid phone numbers
        valid_numbers = ['0700000000', '+254700000000', '254700000000']
        for phone in valid_numbers:
            with self.subTest(phone=phone):
                result = mpesa_service.validate_phone_number(phone)
                self.assertEqual(result, '254700000000')
        
        # Invalid phone numbers
        invalid_numbers = ['123', 'abc', '25470000000', '2547000000000']
        for phone in invalid_numbers:
            with self.subTest(phone=phone):
                with self.assertRaises(Exception):
                    mpesa_service.validate_phone_number(phone)
    
    @patch('contributions.mpesa_service.requests.get')
    def test_get_access_token(self, mock_get):
        """Test getting MPESA access token"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {'access_token': 'test_token_123'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        mpesa_service = MPESAService()
        token = mpesa_service.get_access_token()
        
        self.assertEqual(token, 'test_token_123')
        mock_get.assert_called_once()
    
    @patch('contributions.mpesa_service.requests.post')
    @patch('contributions.mpesa_service.MPESAService.get_access_token')
    def test_initiate_stk_push(self, mock_get_token, mock_post):
        """Test STK Push initiation"""
        # Mock access token
        mock_get_token.return_value = 'test_token_123'
        
        # Mock successful STK Push response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'CheckoutRequestID': 'ws_CO_123456789',
            'MerchantRequestID': '29115-34620561-1',
            'ResponseCode': '0',
            'ResponseDescription': 'Success'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        mpesa_service = MPESAService()
        result = mpesa_service.initiate_stk_push(
            phone_number='254700000000',
            amount=50.0,
            contribution_id=self.contribution.id
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['checkout_request_id'], 'ws_CO_123456789')
        self.assertEqual(result['merchant_request_id'], '29115-34620561-1')
        
        # Check that payment history was created
        payment_history = PaymentHistory.objects.get(
            contribution=self.contribution,
            payment_method='mpesa_stk'
        )
        self.assertEqual(payment_history.status, 'pending')
        self.assertEqual(payment_history.external_id, 'ws_CO_123456789')
    
    def test_process_callback_success(self):
        """Test successful callback processing"""
        # Create a pending payment
        payment_history = PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('50.00'),
            payment_method='mpesa_stk',
            status='pending',
            external_id='ws_CO_123456789',
            created_by=self.user
        )
        
        # Mock callback data
        callback_data = {
            'CheckoutRequestID': 'ws_CO_123456789',
            'ResultCode': 0,
            'ResultDesc': 'The service request is processed successfully.',
            'Amount': 50.0,
            'MpesaReceiptNumber': 'MPESA123456',
            'TransactionDate': '20241201120000'
        }
        
        mpesa_service = MPESAService()
        result = mpesa_service.process_callback(callback_data)
        
        self.assertTrue(result['success'])
        
        # Check that payment was updated
        payment_history.refresh_from_db()
        self.assertEqual(payment_history.status, 'completed')
        self.assertEqual(payment_history.transaction_id, 'MPESA123456')
        self.assertIsNotNone(payment_history.processed_at)
        
        # Check that contribution amount was updated
        self.contribution.refresh_from_db()
        self.assertEqual(self.contribution.amount_paid, Decimal('50.00'))
    
    def test_process_callback_failure(self):
        """Test failed callback processing"""
        # Create a pending payment
        payment_history = PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('50.00'),
            payment_method='mpesa_stk',
            status='pending',
            external_id='ws_CO_123456789',
            created_by=self.user
        )
        
        # Mock callback data for failure
        callback_data = {
            'CheckoutRequestID': 'ws_CO_123456789',
            'ResultCode': 1,
            'ResultDesc': 'Insufficient funds',
            'Amount': 50.0,
            'TransactionDate': '20241201120000'
        }
        
        mpesa_service = MPESAService()
        result = mpesa_service.process_callback(callback_data)
        
        self.assertFalse(result['success'])
        
        # Check that payment was updated
        payment_history.refresh_from_db()
        self.assertEqual(payment_history.status, 'failed')
        self.assertIsNotNone(payment_history.processed_at)


class MPESAAPITestCase(APITestCase):
    """Test cases for MPESA API endpoints"""
    
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(
            phone_number='254700000000',
            password='testpass123',
            role='admin'
        )
        
        self.school = School.objects.create(
            name='Test School',
            address='Test Address',
            phone_number='254700000000',
            email='test@school.com'
        )
        
        self.group = Group.objects.create(
            name='Test Class',
            school=self.school,
            description='Test class description'
        )
        
        self.student = Student.objects.create(
            name='Test Student',
            school=self.school,
            parent_phone='254700000000'
        )
        
        self.event = ContributionEvent.objects.create(
            name='Test Event',
            description='Test event description',
            school=self.school,
            amount_required=Decimal('100.00'),
            due_date='2024-12-31',
            is_published=True
        )
        
        self.contribution = StudentContribution.objects.create(
            student=self.student,
            event=self.event,
            amount_required=Decimal('100.00'),
            amount_paid=Decimal('0.00')
        )
    
    @patch('contributions.mpesa_service.MPESAService.initiate_stk_push')
    def test_initiate_stk_push_api(self, mock_initiate):
        """Test STK Push API endpoint"""
        # Mock successful response
        mock_initiate.return_value = {
            'success': True,
            'checkout_request_id': 'ws_CO_123456789',
            'merchant_request_id': '29115-34620561-1',
            'payment_history_id': 1,
            'message': 'STK Push sent successfully'
        }
        
        url = reverse('contributions:initiate-stk-push')
        data = {
            'contribution_id': self.contribution.id,
            'phone_number': '254700000000',
            'amount': 50.0
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['checkout_request_id'], 'ws_CO_123456789')
    
    def test_initiate_stk_push_missing_fields(self):
        """Test STK Push API with missing fields"""
        url = reverse('contributions:initiate-stk-push')
        data = {
            'contribution_id': self.contribution.id,
            # Missing phone_number and amount
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_initiate_stk_push_invalid_contribution(self):
        """Test STK Push API with invalid contribution ID"""
        url = reverse('contributions:initiate-stk-push')
        data = {
            'contribution_id': 99999,  # Non-existent ID
            'phone_number': '254700000000',
            'amount': 50.0
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_mpesa_callback(self):
        """Test MPESA callback endpoint"""
        # Create a pending payment
        payment_history = PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('50.00'),
            payment_method='mpesa_stk',
            status='pending',
            external_id='ws_CO_123456789',
            created_by=self.user
        )
        
        url = reverse('contributions:mpesa-callback')
        callback_data = {
            'CheckoutRequestID': 'ws_CO_123456789',
            'ResultCode': 0,
            'ResultDesc': 'The service request is processed successfully.',
            'Amount': 50.0,
            'MpesaReceiptNumber': 'MPESA123456',
            'TransactionDate': '20241201120000'
        }
        
        response = self.client.post(
            url,
            json.dumps(callback_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that payment was updated
        payment_history.refresh_from_db()
        self.assertEqual(payment_history.status, 'completed')
    
    def test_get_payment_history(self):
        """Test getting payment history"""
        # Create payment history
        PaymentHistory.objects.create(
            contribution=self.contribution,
            amount=Decimal('50.00'),
            payment_method='mpesa_stk',
            status='completed',
            transaction_id='MPESA123456',
            created_by=self.user
        )
        
        url = reverse('contributions:get-payment-history', args=[self.contribution.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['payment_history']), 1)
        self.assertEqual(response.data['payment_history'][0]['amount'], 50.0) 