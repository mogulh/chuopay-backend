import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied
from .analytics_service import AnalyticsService
from .models import School
from django.utils import timezone

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_dashboard(request):
    """
    Get comprehensive analytics data for the dashboard
    """
    try:
        # Get parameters
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        
        # Get school if specified
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Initialize analytics service
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        # Get all analytics data
        overview = analytics_service.get_overview_statistics()
        trends = analytics_service.get_trends_data()
        breakdown = analytics_service.get_breakdown_data()
        top_performers = analytics_service.get_top_performers()
        payment_analytics = analytics_service.get_payment_analytics()
        financial_reports = analytics_service.get_financial_reports()
        
        return Response({
            'overview': overview,
            'trends': trends,
            'breakdown': breakdown,
            'top_performers': top_performers,
            'payment_analytics': payment_analytics,
            'financial_reports': financial_reports,
            'time_range': time_range,
            'school': {
                'id': school.id,
                'name': school.name
            } if school else None
        })
        
    except Exception as e:
        logger.error(f"Error in analytics dashboard: {str(e)}")
        return Response(
            {'error': 'An error occurred while fetching analytics data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overview_statistics(request):
    """
    Get overview statistics only
    """
    try:
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        overview = analytics_service.get_overview_statistics()
        
        return Response(overview)
        
    except Exception as e:
        logger.error(f"Error in overview statistics: {str(e)}")
        return Response(
            {'error': 'An error occurred while fetching overview statistics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trends_data(request):
    """
    Get trends data for charts
    """
    try:
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        trends = analytics_service.get_trends_data()
        
        return Response(trends)
        
    except Exception as e:
        logger.error(f"Error in trends data: {str(e)}")
        return Response(
            {'error': 'An error occurred while fetching trends data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def breakdown_data(request):
    """
    Get breakdown data by categories
    """
    try:
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        breakdown = analytics_service.get_breakdown_data()
        
        return Response(breakdown)
        
    except Exception as e:
        logger.error(f"Error in breakdown data: {str(e)}")
        return Response(
            {'error': 'An error occurred while fetching breakdown data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_performers(request):
    """
    Get top performing events and groups
    """
    try:
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        top_performers = analytics_service.get_top_performers()
        
        return Response(top_performers)
        
    except Exception as e:
        logger.error(f"Error in top performers: {str(e)}")
        return Response(
            {'error': 'An error occurred while fetching top performers data'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_analytics(request):
    """
    Get detailed payment analytics
    """
    try:
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        payment_analytics = analytics_service.get_payment_analytics()
        
        return Response(payment_analytics)
        
    except Exception as e:
        logger.error(f"Error in payment analytics: {str(e)}")
        return Response(
            {'error': 'An error occurred while fetching payment analytics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_reports(request):
    """
    Get financial reports and summaries
    """
    try:
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        financial_reports = analytics_service.get_financial_reports()
        
        return Response(financial_reports)
        
    except Exception as e:
        logger.error(f"Error in financial reports: {str(e)}")
        return Response(
            {'error': 'An error occurred while fetching financial reports'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_report(request):
    """
    Export analytics report as CSV/Excel
    """
    try:
        report_type = request.query_params.get('type', 'overview')
        time_range = request.query_params.get('time_range', '30d')
        school_id = request.query_params.get('school_id')
        format_type = request.query_params.get('format', 'csv')
        
        # Only admins and teachers can export reports
        if request.user.role not in ['admin', 'teacher']:
            raise PermissionDenied("Only admins and teachers can export reports")
        
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                return Response(
                    {'error': 'School not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        analytics_service = AnalyticsService(
            user=request.user,
            school=school,
            time_range=time_range
        )
        
        # Get data based on report type
        if report_type == 'overview':
            data = analytics_service.get_overview_statistics()
        elif report_type == 'trends':
            data = analytics_service.get_trends_data()
        elif report_type == 'breakdown':
            data = analytics_service.get_breakdown_data()
        elif report_type == 'top_performers':
            data = analytics_service.get_top_performers()
        elif report_type == 'payment_analytics':
            data = analytics_service.get_payment_analytics()
        elif report_type == 'financial_reports':
            data = analytics_service.get_financial_reports()
        else:
            return Response(
                {'error': 'Invalid report type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For now, return JSON response
        # In a real implementation, you would generate CSV/Excel files
        return Response({
            'report_type': report_type,
            'time_range': time_range,
            'format': format_type,
            'data': data,
            'exported_at': timezone.now().isoformat()
        })
        
    except PermissionDenied as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.error(f"Error in export report: {str(e)}")
        return Response(
            {'error': 'An error occurred while exporting the report'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 