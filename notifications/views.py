from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    NotificationTemplate, NotificationSchedule, NotificationLog, 
    SMSCredits, NotificationSettings
)
from .serializers import (
    NotificationTemplateSerializer, NotificationScheduleSerializer,
    NotificationLogSerializer, SMSCreditsSerializer, NotificationSettingsSerializer
)


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notification templates
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    @action(detail=True, methods=['post'])
    def test_template(self, request, pk=None):
        """Test a template with sample data"""
        template = self.get_object()
        
        # Sample data for testing
        sample_data = {
            'student_name': 'John Doe',
            'event_name': 'Field Trip',
            'amount': '5,000',
            'due_date': '2024-01-15',
            'school_name': 'Sample School'
        }
        
        # Replace placeholders in template
        message = template.content
        for key, value in sample_data.items():
            message = message.replace(f'{{{key}}}', str(value))
        
        return Response({
            'template': template.name,
            'message': message,
            'length': len(message),
            'sample_data': sample_data
        })


class NotificationScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notification schedules
    """
    queryset = NotificationSchedule.objects.all()
    serializer_class = NotificationScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run a schedule immediately"""
        schedule = self.get_object()
        
        # This would trigger the actual notification sending
        # For now, we'll just update the last_run timestamp
        schedule.last_run = timezone.now()
        schedule.save()
        
        return Response({
            'message': f'Schedule "{schedule.name}" executed successfully',
            'last_run': schedule.last_run
        })


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing notification logs
    """
    queryset = NotificationLog.objects.select_related('recipient', 'student', 'event', 'template')
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter based on user role
        if user.role == 'parent':
            queryset = queryset.filter(recipient=user)
        elif user.role == 'teacher':
            # Teachers can see notifications for their assigned groups
            from contributions.models import Group
            teacher_groups = Group.objects.filter(teacher=user)
            student_ids = teacher_groups.values_list('students__id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get notification statistics"""
        user = request.user
        queryset = self.get_queryset()
        
        # Filter by date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)
        
        stats = {
            'total_sent': queryset.count(),
            'successful': queryset.filter(status__in=['sent', 'delivered']).count(),
            'failed': queryset.filter(status='failed').count(),
            'pending': queryset.filter(status='pending').count(),
            'by_type': {},
            'by_status': {},
            'daily_totals': []
        }
        
        # Breakdown by notification type
        for notification_type, _ in NotificationLog.NOTIFICATION_TYPE_CHOICES:
            count = queryset.filter(notification_type=notification_type).count()
            if count > 0:
                stats['by_type'][notification_type] = count
        
        # Breakdown by status
        for status, _ in NotificationLog.STATUS_CHOICES:
            count = queryset.filter(status=status).count()
            if count > 0:
                stats['by_status'][status] = count
        
        # Daily totals for the last 7 days
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            count = queryset.filter(
                created_at__date=date.date()
            ).count()
            stats['daily_totals'].append({
                'date': date.date().isoformat(),
                'count': count
            })
        
        return Response(stats)


class SMSCreditsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing SMS credits
    """
    queryset = SMSCredits.objects.all()
    serializer_class = SMSCreditsSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current SMS credit balance"""
        total_purchased = SMSCredits.objects.filter(
            credit_type='purchase'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        total_used = SMSCredits.objects.filter(
            credit_type='usage'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        balance = total_purchased - total_used
        
        return Response({
            'balance': balance,
            'total_purchased': total_purchased,
            'total_used': total_used
        })


class NotificationSettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user notification settings
    """
    serializer_class = NotificationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationSettings.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


# SMS Service Integration
class SMSService:
    """
    Service class for handling SMS sending
    """
    
    @staticmethod
    def send_sms(phone_number, message, user=None):
        """
        Send SMS using configured provider
        For now, this is a mock implementation
        In production, this would integrate with Twilio, Africa's Talking, etc.
        """
        try:
            # Mock SMS sending
            # In production, this would make an API call to the SMS provider
            
            # Create notification log entry
            if user:
                notification_log = NotificationLog.objects.create(
                    recipient=user,
                    notification_type='sms',
                    message=message,
                    status='sent',
                    sent_at=timezone.now(),
                    external_id=f'SMS_{int(timezone.now().timestamp())}',
                    created_by=user
                )
                
                # Deduct SMS credits
                SMSCredits.objects.create(
                    amount=1,
                    credit_type='usage',
                    cost=1.0,  # Mock cost
                    created_by=user
                )
                
                return {
                    'success': True,
                    'message': 'SMS sent successfully',
                    'notification_id': notification_log.id
                }
            
            return {
                'success': True,
                'message': 'SMS sent successfully (mock)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'SMS sending failed: {str(e)}'
            }
    
    @staticmethod
    def send_bulk_sms(recipients, message, created_by):
        """
        Send bulk SMS to multiple recipients
        """
        results = []
        success_count = 0
        failure_count = 0
        
        for recipient in recipients:
            result = SMSService.send_sms(
                phone_number=recipient.get('phone'),
                message=message,
                user=recipient.get('user')
            )
            
            if result['success']:
                success_count += 1
            else:
                failure_count += 1
            
            results.append({
                'recipient': recipient.get('name', 'Unknown'),
                'phone': recipient.get('phone'),
                'result': result
            })
        
        return {
            'total': len(recipients),
            'success_count': success_count,
            'failure_count': failure_count,
            'results': results
        }


# API Views for SMS functionality
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from contributions.models import Student, StudentContribution, ContributionEvent
from contributions.serializers import StudentSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_payment_reminder(request):
    """
    Send payment reminder to parents
    """
    try:
        data = request.data
        student_ids = data.get('students', [])
        message = data.get('message', '')
        reminder_type = data.get('reminder_type', 'payment')
        
        if not student_ids or not message:
            return Response({
                'error': 'Students and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get students and their parents
        students = Student.objects.filter(id__in=student_ids).select_related('school')
        recipients = []
        
        for student in students:
            # Get parents for this student
            parents = student.parents.all()
            for parent in parents:
                if parent.phone_number:
                    recipients.append({
                        'user': parent,
                        'name': f"{parent.first_name} {parent.last_name}",
                        'phone': parent.phone_number,
                        'student': student
                    })
        
        if not recipients:
            return Response({
                'error': 'No valid recipients found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send SMS to all recipients
        result = SMSService.send_bulk_sms(
            recipients=recipients,
            message=message,
            created_by=request.user
        )
        
        return Response({
            'message': 'Reminders sent successfully',
            'result': result
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to send reminders: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_students_for_reminders(request):
    """
    Get students that need reminders based on filters
    """
    try:
        reminder_type = request.query_params.get('type', 'payment')
        group_id = request.query_params.get('group_id')
        
        # Base queryset
        students = Student.objects.select_related('school')
        
        # Filter by group if specified
        if group_id:
            students = students.filter(groups__id=group_id)
        
        # Filter by payment status
        if reminder_type == 'overdue':
            students = students.filter(
                contributions__payment_status='overdue'
            ).distinct()
        elif reminder_type == 'upcoming':
            students = students.filter(
                contributions__payment_status='pending'
            ).distinct()
        else:  # payment due
            students = students.filter(
                contributions__payment_status__in=['pending', 'partial']
            ).distinct()
        
        # Add parent information
        students_data = []
        for student in students:
            parents = student.parents.all()
            for parent in parents:
                if parent.phone_number:
                    students_data.append({
                        'id': student.id,
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'student_id': student.student_id,
                        'parent_name': f"{parent.first_name} {parent.last_name}",
                        'parent_phone': parent.phone_number,
                        'payment_status': student.contributions.first().payment_status if student.contributions.exists() else 'pending',
                        'contribution_count': student.contributions.count()
                    })
                    break  # Only include first parent for now
        
        return Response({
            'students': students_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to get students: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
