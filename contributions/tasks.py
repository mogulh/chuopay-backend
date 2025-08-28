import logging
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import PaymentHistory
from .mpesa_service import MPESAService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_mpesa_payment_status(self, payment_history_id):
    """
    Check MPESA payment status and update accordingly
    """
    try:
        # Get payment history
        payment_history = PaymentHistory.objects.get(id=payment_history_id)
        
        # Skip if already processed
        if payment_history.status in ['completed', 'failed', 'cancelled']:
            return f"Payment {payment_history_id} already processed with status: {payment_history.status}"
        
        # Initialize MPESA service
        mpesa_service = MPESAService()
        
        # Check status
        status_data = mpesa_service.check_payment_status(payment_history.external_id)
        
        # Process status update
        result_code = status_data.get('ResultCode')
        
        if result_code == 0:
            # Payment successful
            payment_history.status = 'completed'
            payment_history.external_status = 'success'
            payment_history.processed_at = timezone.now()
            payment_history.external_response = status_data
            payment_history.save()
            
            # Update contribution amount paid
            contribution = payment_history.contribution
            contribution.amount_paid += payment_history.amount
            contribution.save()
            
            logger.info(f"Payment {payment_history_id} completed successfully")
            return f"Payment {payment_history_id} completed successfully"
            
        elif result_code == 1:
            # Payment failed
            payment_history.status = 'failed'
            payment_history.external_status = 'failed'
            payment_history.processed_at = timezone.now()
            payment_history.external_response = status_data
            payment_history.notes = f"Payment failed: {status_data.get('ResultDesc', 'Unknown error')}"
            payment_history.save()
            
            logger.warning(f"Payment {payment_history_id} failed")
            return f"Payment {payment_history_id} failed"
            
        else:
            # Still pending, retry later
            if self.request.retries < self.max_retries:
                raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff
            else:
                # Max retries reached, mark as failed
                payment_history.status = 'failed'
                payment_history.external_status = 'timeout'
                payment_history.processed_at = timezone.now()
                payment_history.external_response = status_data
                payment_history.notes = "Payment status check timed out after max retries"
                payment_history.save()
                
                logger.error(f"Payment {payment_history_id} timed out after max retries")
                return f"Payment {payment_history_id} timed out after max retries"
                
    except PaymentHistory.DoesNotExist:
        logger.error(f"Payment history {payment_history_id} not found")
        return f"Payment history {payment_history_id} not found"
    except ValidationError as e:
        logger.error(f"Validation error for payment {payment_history_id}: {str(e)}")
        return f"Validation error for payment {payment_history_id}: {str(e)}"
    except Exception as e:
        logger.error(f"Error checking payment {payment_history_id}: {str(e)}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            return f"Error checking payment {payment_history_id}: {str(e)}"


@shared_task
def cleanup_pending_payments():
    """
    Clean up payments that have been pending for too long
    """
    try:
        # Find payments that have been pending for more than 24 hours
        cutoff_time = timezone.now() - timezone.timedelta(hours=24)
        pending_payments = PaymentHistory.objects.filter(
            status='pending',
            payment_method='mpesa_stk',
            created_at__lt=cutoff_time
        )
        
        for payment in pending_payments:
            payment.status = 'cancelled'
            payment.notes = "Payment cancelled due to timeout (24 hours)"
            payment.save()
            
            logger.info(f"Cancelled pending payment {payment.id} due to timeout")
        
        return f"Cancelled {pending_payments.count()} pending payments"
        
    except Exception as e:
        logger.error(f"Error in cleanup_pending_payments: {str(e)}")
        return f"Error in cleanup_pending_payments: {str(e)}"


@shared_task
def retry_failed_payments():
    """
    Retry failed payments that might have been temporary failures
    """
    try:
        # Find failed payments from the last hour that might be retryable
        cutoff_time = timezone.now() - timezone.timedelta(hours=1)
        failed_payments = PaymentHistory.objects.filter(
            status='failed',
            payment_method='mpesa_stk',
            created_at__gte=cutoff_time,
            external_status__in=['timeout', 'network_error']
        )
        
        for payment in failed_payments:
            # Reset status to pending for retry
            payment.status = 'pending'
            payment.external_status = 'retrying'
            payment.notes = "Retrying payment after previous failure"
            payment.save()
            
            # Schedule status check
            check_mpesa_payment_status.delay(payment.id)
            
            logger.info(f"Scheduled retry for payment {payment.id}")
        
        return f"Scheduled retry for {failed_payments.count()} failed payments"
        
    except Exception as e:
        logger.error(f"Error in retry_failed_payments: {str(e)}")
        return f"Error in retry_failed_payments: {str(e)}" 