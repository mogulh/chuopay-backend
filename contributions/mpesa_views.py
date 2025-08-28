import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .mpesa_service import MPESAService
from .models import StudentContribution, PaymentHistory
from .serializers import StudentContributionSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_stk_push(request):
    """
    Initiate MPESA STK Push payment
    """
    try:
        data = request.data
        contribution_id = data.get('contribution_id')
        phone_number = data.get('phone_number')
        amount = data.get('amount')
        
        # Validate required fields
        if not all([contribution_id, phone_number, amount]):
            return Response({
                'success': False,
                'message': 'Missing required fields: contribution_id, phone_number, amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate contribution exists
        try:
            contribution = StudentContribution.objects.get(id=contribution_id)
        except StudentContribution.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Contribution not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize MPESA service
        mpesa_service = MPESAService()
        
        # Validate phone number
        try:
            formatted_phone = mpesa_service.validate_phone_number(phone_number)
        except ValidationError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate amount
        try:
            amount_decimal = float(amount)
            if amount_decimal <= 0:
                raise ValueError("Amount must be greater than 0")
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if amount is within contribution limits
        remaining_amount = contribution.amount_required - contribution.amount_paid
        if amount_decimal > remaining_amount:
            return Response({
                'success': False,
                'message': f'Amount exceeds remaining contribution amount (KES {remaining_amount})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initiate STK Push
        result = mpesa_service.initiate_stk_push(
            phone_number=formatted_phone,
            amount=amount_decimal,
            contribution_id=contribution_id
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        logger.error(f"MPESA STK Push validation error: {str(e)}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"MPESA STK Push error: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while processing the payment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """
    Handle MPESA callback/webhook
    """
    try:
        # Get callback data
        callback_data = json.loads(request.body.decode('utf-8'))
        logger.info(f"MPESA callback received: {callback_data}")
        
        # Initialize MPESA service
        mpesa_service = MPESAService()
        
        # Process callback
        result = mpesa_service.process_callback(callback_data)
        
        # Return success response to MPESA
        response_data = {
            "ResultCode": 0,
            "ResultDesc": "Success"
        }
        
        return JsonResponse(response_data, status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in MPESA callback")
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": "Invalid JSON"
        }, status=400)
    except ValidationError as e:
        logger.error(f"MPESA callback validation error: {str(e)}")
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"MPESA callback error: {str(e)}")
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": "Internal server error"
        }, status=500)


@api_view(['GET'])
def check_payment_status(request, checkout_request_id):
    """
    Check payment status using MPESA API
    """
    try:
        # Initialize MPESA service
        mpesa_service = MPESAService()
        
        # Check status
        status_data = mpesa_service.check_payment_status(checkout_request_id)
        
        return Response({
            'success': True,
            'status_data': status_data
        }, status=status.HTTP_200_OK)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Payment status check error: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while checking payment status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_payment_history(request, contribution_id):
    """
    Get payment history for a contribution
    """
    try:
        # Get contribution
        try:
            contribution = StudentContribution.objects.get(id=contribution_id)
        except StudentContribution.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Contribution not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get payment history
        payment_history = PaymentHistory.objects.filter(
            contribution=contribution
        ).order_by('-created_at')
        
        # Serialize data
        history_data = []
        for payment in payment_history:
            history_data.append({
                'id': payment.id,
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'status': payment.status,
                'transaction_id': payment.transaction_id,
                'external_id': payment.external_id,
                'payment_date': payment.payment_date.isoformat(),
                'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
                'notes': payment.notes,
                'external_response': payment.external_response
            })
        
        return Response({
            'success': True,
            'contribution_id': contribution_id,
            'payment_history': history_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get payment history error: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving payment history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 