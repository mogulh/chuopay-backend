import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from .models import (
    StudentContribution, PaymentHistory, ContributionEvent, 
    Student, Group, School
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service class for handling analytics calculations and data aggregation
    """
    
    def __init__(self, user=None, school=None, time_range='30d'):
        self.user = user
        self.school = school
        self.time_range = time_range
        self.start_date = self._get_start_date()
        self.end_date = timezone.now()
    
    def _get_start_date(self):
        """Get start date based on time range"""
        end_date = timezone.now()
        
        if self.time_range == '7d':
            return end_date - timedelta(days=7)
        elif self.time_range == '30d':
            return end_date - timedelta(days=30)
        elif self.time_range == '90d':
            return end_date - timedelta(days=90)
        elif self.time_range == '1y':
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=30)
    
    def get_overview_statistics(self):
        """Get overview statistics"""
        try:
            # Get base queryset
            contributions = self._get_contributions_queryset()
            payments = self._get_payments_queryset()
            
            # Calculate totals
            total_contributions = contributions.count()
            total_amount_required = contributions.aggregate(
                total=Sum('amount_required')
            )['total'] or Decimal('0.00')
            
            total_amount_paid = contributions.aggregate(
                total=Sum('amount_paid')
            )['total'] or Decimal('0.00')
            
            total_remaining = total_amount_required - total_amount_paid
            
            # Calculate collection rate
            collection_rate = 0
            if total_amount_required > 0:
                collection_rate = (total_amount_paid / total_amount_required) * 100
            
            # Calculate average payment time
            completed_payments = payments.filter(status='completed')
            avg_payment_time = completed_payments.aggregate(
                avg_time=Avg(F('processed_at') - F('payment_date'))
            )['avg_time']
            
            avg_payment_days = 0
            if avg_payment_time:
                avg_payment_days = avg_payment_time.days
            
            # Calculate overdue amount
            overdue_contributions = contributions.filter(
                event__due_date__lt=timezone.now().date(),
                payment_status__in=['pending', 'partial']
            )
            overdue_amount = overdue_contributions.aggregate(
                total=Sum('amount_required') - Sum('amount_paid')
            )['total'] or Decimal('0.00')
            
            return {
                'total_contributions': total_contributions,
                'total_collected': float(total_amount_paid),
                'total_remaining': float(total_remaining),
                'collection_rate': round(float(collection_rate), 2),
                'average_payment_time': avg_payment_days,
                'overdue_amount': float(overdue_amount)
            }
            
        except Exception as e:
            logger.error(f"Error calculating overview statistics: {str(e)}")
            return {
                'total_contributions': 0,
                'total_collected': 0,
                'total_remaining': 0,
                'collection_rate': 0,
                'average_payment_time': 0,
                'overdue_amount': 0
            }
    
    def get_trends_data(self):
        """Get trends data for charts"""
        try:
            payments = self._get_payments_queryset().filter(
                status='completed',
                payment_date__range=[self.start_date, self.end_date]
            )
            
            # Daily collections
            daily_collections = payments.annotate(
                date=TruncDate('payment_date')
            ).values('date').annotate(
                amount=Sum('amount')
            ).order_by('date')
            
            # Weekly collections
            weekly_collections = payments.annotate(
                week=TruncWeek('payment_date')
            ).values('week').annotate(
                amount=Sum('amount')
            ).order_by('week')
            
            # Monthly collections
            monthly_collections = payments.annotate(
                month=TruncMonth('payment_date')
            ).values('month').annotate(
                amount=Sum('amount')
            ).order_by('month')
            
            return {
                'daily_collections': [
                    {
                        'date': item['date'].strftime('%Y-%m-%d'),
                        'amount': float(item['amount'])
                    }
                    for item in daily_collections
                ],
                'weekly_collections': [
                    {
                        'week': item['week'].strftime('%Y-W%U'),
                        'amount': float(item['amount'])
                    }
                    for item in weekly_collections
                ],
                'monthly_collections': [
                    {
                        'month': item['month'].strftime('%Y-%m'),
                        'amount': float(item['amount'])
                    }
                    for item in monthly_collections
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends data: {str(e)}")
            return {
                'daily_collections': [],
                'weekly_collections': [],
                'monthly_collections': []
            }
    
    def get_breakdown_data(self):
        """Get breakdown data by various categories"""
        try:
            contributions = self._get_contributions_queryset()
            payments = self._get_payments_queryset()
            
            # Breakdown by event type
            by_event_type = contributions.values('event__name').annotate(
                count=Count('id'),
                amount=Sum('amount_paid')
            ).order_by('-amount')
            
            # Breakdown by payment method
            by_payment_method = payments.filter(status='completed').values('payment_method').annotate(
                count=Count('id'),
                amount=Sum('amount')
            ).order_by('-amount')
            
            # Breakdown by status
            by_status = contributions.values('payment_status').annotate(
                count=Count('id'),
                amount=Sum('amount_paid')
            ).order_by('-amount')
            
            return {
                'by_event_type': [
                    {
                        'event_type': item['event__name'],
                        'count': item['count'],
                        'amount': float(item['amount'])
                    }
                    for item in by_event_type
                ],
                'by_payment_method': [
                    {
                        'method': item['payment_method'],
                        'count': item['count'],
                        'amount': float(item['amount'])
                    }
                    for item in by_payment_method
                ],
                'by_status': [
                    {
                        'status': item['payment_status'],
                        'count': item['count'],
                        'amount': float(item['amount'])
                    }
                    for item in by_status
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating breakdown data: {str(e)}")
            return {
                'by_event_type': [],
                'by_payment_method': [],
                'by_status': []
            }
    
    def get_top_performers(self):
        """Get top performing events and groups"""
        try:
            contributions = self._get_contributions_queryset()
            
            # Top performing events
            top_events = contributions.values('event__name').annotate(
                total_amount=Sum('amount_required'),
                collected_amount=Sum('amount_paid'),
                student_count=Count('student', distinct=True)
            ).annotate(
                collection_rate=(F('collected_amount') / F('total_amount') * 100)
            ).filter(
                total_amount__gt=0
            ).order_by('-collection_rate')[:10]
            
            # Top performing groups
            top_groups = contributions.values('student__groups__name').annotate(
                total_amount=Sum('amount_required'),
                collected_amount=Sum('amount_paid'),
                student_count=Count('student', distinct=True)
            ).annotate(
                collection_rate=(F('collected_amount') / F('total_amount') * 100)
            ).filter(
                total_amount__gt=0,
                student__groups__name__isnull=False
            ).order_by('-collection_rate')[:10]
            
            return {
                'events': [
                    {
                        'name': item['event__name'],
                        'collection_rate': round(float(item['collection_rate']), 2),
                        'total_amount': float(item['total_amount'])
                    }
                    for item in top_events
                ],
                'groups': [
                    {
                        'name': item['student__groups__name'],
                        'collection_rate': round(float(item['collection_rate']), 2),
                        'student_count': item['student_count']
                    }
                    for item in top_groups
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating top performers: {str(e)}")
            return {
                'events': [],
                'groups': []
            }
    
    def get_payment_analytics(self):
        """Get detailed payment analytics"""
        try:
            payments = self._get_payments_queryset()
            
            # Payment success rate
            total_payments = payments.count()
            successful_payments = payments.filter(status='completed').count()
            success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
            
            # Average transaction amount
            avg_amount = payments.filter(status='completed').aggregate(
                avg=Avg('amount')
            )['avg'] or 0
            
            # Payment method distribution
            method_distribution = payments.values('payment_method').annotate(
                count=Count('id'),
                total_amount=Sum('amount'),
                success_count=Count('id', filter=Q(status='completed'))
            )
            
            # Time-based analysis
            hourly_distribution = payments.filter(status='completed').extra(
                select={'hour': "EXTRACT(hour FROM payment_date)"}
            ).values('hour').annotate(
                count=Count('id'),
                amount=Sum('amount')
            ).order_by('hour')
            
            return {
                'success_rate': round(success_rate, 2),
                'average_amount': float(avg_amount),
                'total_transactions': total_payments,
                'successful_transactions': successful_payments,
                'method_distribution': list(method_distribution),
                'hourly_distribution': list(hourly_distribution)
            }
            
        except Exception as e:
            logger.error(f"Error calculating payment analytics: {str(e)}")
            return {
                'success_rate': 0,
                'average_amount': 0,
                'total_transactions': 0,
                'successful_transactions': 0,
                'method_distribution': [],
                'hourly_distribution': []
            }
    
    def get_financial_reports(self):
        """Get financial reports and summaries"""
        try:
            contributions = self._get_contributions_queryset()
            payments = self._get_payments_queryset()
            
            # Monthly revenue
            monthly_revenue = payments.filter(
                status='completed',
                payment_date__range=[self.start_date, self.end_date]
            ).annotate(
                month=TruncMonth('payment_date')
            ).values('month').annotate(
                revenue=Sum('amount')
            ).order_by('month')
            
            # Outstanding amounts by event
            outstanding_by_event = contributions.filter(
                payment_status__in=['pending', 'partial']
            ).values('event__name').annotate(
                total_required=Sum('amount_required'),
                total_paid=Sum('amount_paid')
            ).annotate(
                outstanding=F('total_required') - F('total_paid')
            ).order_by('-outstanding')
            
            # Cash flow analysis
            cash_flow = payments.filter(
                status='completed',
                payment_date__range=[self.start_date, self.end_date]
            ).annotate(
                date=TruncDate('payment_date')
            ).values('date').annotate(
                inflow=Sum('amount')
            ).order_by('date')
            
            return {
                'monthly_revenue': [
                    {
                        'month': item['month'].strftime('%Y-%m'),
                        'revenue': float(item['revenue'])
                    }
                    for item in monthly_revenue
                ],
                'outstanding_by_event': [
                    {
                        'event_name': item['event__name'],
                        'total_required': float(item['total_required']),
                        'total_paid': float(item['total_paid']),
                        'outstanding': float(item['outstanding'])
                    }
                    for item in outstanding_by_event
                ],
                'cash_flow': [
                    {
                        'date': item['date'].strftime('%Y-%m-%d'),
                        'inflow': float(item['inflow'])
                    }
                    for item in cash_flow
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating financial reports: {str(e)}")
            return {
                'monthly_revenue': [],
                'outstanding_by_event': [],
                'cash_flow': []
            }
    
    def _get_contributions_queryset(self):
        """Get base contributions queryset with filters"""
        queryset = StudentContribution.objects.select_related(
            'student', 'event', 'student__school'
        ).filter(
            created_at__range=[self.start_date, self.end_date]
        )
        
        if self.school:
            queryset = queryset.filter(student__school=self.school)
        
        if self.user:
            if self.user.role == 'teacher':
                # Teachers see only their groups
                group_ids = Group.objects.filter(teacher=self.user).values_list('id', flat=True)
                student_ids = Student.objects.filter(groups__id__in=group_ids).values_list('id', flat=True)
                queryset = queryset.filter(student_id__in=student_ids)
            elif self.user.role == 'parent':
                # Parents see only their children
                student_ids = Student.objects.filter(parents=self.user).values_list('id', flat=True)
                queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset
    
    def _get_payments_queryset(self):
        """Get base payments queryset with filters"""
        queryset = PaymentHistory.objects.select_related(
            'contribution__student', 'contribution__event', 'contribution__student__school'
        ).filter(
            payment_date__range=[self.start_date, self.end_date]
        )
        
        if self.school:
            queryset = queryset.filter(contribution__student__school=self.school)
        
        if self.user:
            if self.user.role == 'teacher':
                # Teachers see only their groups
                group_ids = Group.objects.filter(teacher=self.user).values_list('id', flat=True)
                student_ids = Student.objects.filter(groups__id__in=group_ids).values_list('id', flat=True)
                queryset = queryset.filter(contribution__student_id__in=student_ids)
            elif self.user.role == 'parent':
                # Parents see only their children
                student_ids = Student.objects.filter(parents=self.user).values_list('id', flat=True)
                queryset = queryset.filter(contribution__student_id__in=student_ids)
        
        return queryset 