from django.shortcuts import render
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    School, SchoolSection, Group, Student,
    ContributionEvent, ContributionTier, StudentContribution, PaymentReminder
)
from .serializers import (
    SchoolSerializer, SchoolSectionSerializer, GroupSerializer, StudentSerializer,
    ContributionEventSerializer, ContributionTierSerializer,
    StudentContributionSerializer, PaymentReminderSerializer
)


class AdminDashboardViewSet(viewsets.ViewSet):
    """
    Admin dashboard API endpoints for section-specific views
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def my_sections(self, request):
        """Get all sections for the authenticated admin"""
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Access denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Admin can see all sections in their school
        sections = SchoolSection.objects.filter(school=user.school).select_related('school', 'section_head')
        serializer = SchoolSectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def section_dashboard(self, request):
        """Get dashboard data for a specific section"""
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Access denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'section_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            section = SchoolSection.objects.get(
                id=section_id,
                school=user.school
            )
        except SchoolSection.DoesNotExist:
            return Response({'error': 'Section not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get section's groups
        groups = section.groups.all()
        
        # Get section's students
        students = section.students.all()
        
        # Get section's events
        events = ContributionEvent.objects.filter(section=section)
        
        # Get section's contributions
        contributions = StudentContribution.objects.filter(
            student__section=section
        ).select_related('event', 'student', 'parent')
        
        # Calculate statistics
        total_students = students.count()
        active_students = students.filter(is_active=True).count()
        total_groups = groups.count()
        total_events = events.count()
        active_events = events.filter(is_active=True, is_published=True).count()
        
        total_contributions = contributions.count()
        paid_contributions = contributions.filter(payment_status='paid').count()
        pending_contributions = contributions.filter(payment_status='pending').count()
        total_amount_paid = contributions.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        total_amount_required = contributions.aggregate(
            total=Sum('amount_required')
        )['total'] or 0
        
        # Get recent events
        recent_events = events.order_by('-created_at')[:5]
        
        # Get recent contributions
        recent_contributions = contributions.order_by('-created_at')[:5]
        
        # Get top performing groups
        top_groups = groups.annotate(
            student_count=Count('students'),
            contribution_count=Count('students__contributions')
        ).order_by('-student_count')[:3]
        
        dashboard_data = {
            'section': SchoolSectionSerializer(section).data,
            'statistics': {
                'total_students': total_students,
                'active_students': active_students,
                'inactive_students': total_students - active_students,
                'total_groups': total_groups,
                'total_events': total_events,
                'active_events': active_events,
                'total_contributions': total_contributions,
                'paid_contributions': paid_contributions,
                'pending_contributions': pending_contributions,
                'total_amount_paid': float(total_amount_paid),
                'total_amount_required': float(total_amount_required),
                'payment_percentage': (paid_contributions / total_contributions * 100) if total_contributions > 0 else 0,
                'collection_rate': (total_amount_paid / total_amount_required * 100) if total_amount_required > 0 else 0
            },
            'recent_events': ContributionEventSerializer(recent_events, many=True).data,
            'recent_contributions': StudentContributionSerializer(recent_contributions, many=True).data,
            'top_groups': GroupSerializer(top_groups, many=True).data
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def section_students(self, request):
        """Get all students for a specific section"""
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Access denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'section_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            section = SchoolSection.objects.get(
                id=section_id,
                school=user.school
            )
        except SchoolSection.DoesNotExist:
            return Response({'error': 'Section not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get section's students
        students = section.students.all().select_related('school', 'section').prefetch_related('groups', 'parents')
        
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def section_groups(self, request):
        """Get all groups for a specific section"""
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Access denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'section_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            section = SchoolSection.objects.get(
                id=section_id,
                school=user.school
            )
        except SchoolSection.DoesNotExist:
            return Response({'error': 'Section not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get section's groups
        groups = section.groups.all().select_related('teacher', 'section')
        
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def section_events(self, request):
        """Get all events for a specific section"""
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Access denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'section_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            section = SchoolSection.objects.get(
                id=section_id,
                school=user.school
            )
        except SchoolSection.DoesNotExist:
            return Response({'error': 'Section not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get section's events
        events = ContributionEvent.objects.filter(
            section=section
        ).select_related('school', 'section', 'created_by').prefetch_related('groups').order_by('-created_at')
        
        serializer = ContributionEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def section_contributions(self, request):
        """Get all contributions for a specific section"""
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Access denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'section_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            section = SchoolSection.objects.get(
                id=section_id,
                school=user.school
            )
        except SchoolSection.DoesNotExist:
            return Response({'error': 'Section not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get section's contributions
        contributions = StudentContribution.objects.filter(
            student__section=section
        ).select_related('event', 'student', 'parent', 'selected_tier').order_by('-created_at')
        
        serializer = StudentContributionSerializer(contributions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def section_analytics(self, request):
        """Get analytics data for a specific section"""
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Access denied. Admin role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'section_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            section = SchoolSection.objects.get(
                id=section_id,
                school=user.school
            )
        except SchoolSection.DoesNotExist:
            return Response({'error': 'Section not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get contributions for the section
        contributions = StudentContribution.objects.filter(student__section=section)
        
        # Monthly contribution trends
        from django.db.models.functions import TruncMonth
        monthly_trends = contributions.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_amount=Sum('amount_paid'),
            count=Count('id')
        ).order_by('month')
        
        # Payment method breakdown
        payment_methods = contributions.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount_paid')
        ).order_by('-total_amount')
        
        # Event performance
        event_performance = ContributionEvent.objects.filter(section=section).annotate(
            total_contributions=Count('student_contributions'),
            paid_contributions=Count('student_contributions', filter=Q(student_contributions__payment_status='paid')),
            total_amount=Sum('student_contributions__amount_paid')
        ).order_by('-total_amount')
        
        analytics_data = {
            'section': SchoolSectionSerializer(section).data,
            'monthly_trends': list(monthly_trends),
            'payment_methods': list(payment_methods),
            'event_performance': ContributionEventSerializer(event_performance, many=True).data
        }
        
        return Response(analytics_data)


class ParentDashboardViewSet(viewsets.ViewSet):
    """
    Parent dashboard API endpoints for child-specific views
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def my_children(self, request):
        """Get all children for the authenticated parent"""
        user = request.user
        if user.role != 'parent':
            return Response({'error': 'Access denied. Parent role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        children = Student.objects.filter(studentparent__parent=user).select_related('school', 'section')
        serializer = StudentSerializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def child_dashboard(self, request):
        """Get dashboard data for a specific child"""
        user = request.user
        if user.role != 'parent':
            return Response({'error': 'Access denied. Parent role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        child_id = request.query_params.get('child_id')
        if not child_id:
            return Response({'error': 'child_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            child = Student.objects.get(
                id=child_id,
                studentparent__parent=user
            )
        except Student.DoesNotExist:
            return Response({'error': 'Child not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get child's groups
        groups = child.groups.all()
        
        # Get events for child's groups
        events = ContributionEvent.objects.filter(
            groups__in=groups
        ).distinct()
        
        # Get child's contributions
        contributions = StudentContribution.objects.filter(
            student=child,
            parent=user
        ).select_related('event', 'selected_tier')
        
        # Calculate statistics
        total_contributions = contributions.count()
        paid_contributions = contributions.filter(payment_status='paid').count()
        pending_contributions = contributions.filter(payment_status='pending').count()
        total_amount_paid = contributions.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        # Get upcoming events
        upcoming_events = events.filter(
            due_date__gte=timezone.now(),
            is_active=True,
            is_published=True
        ).order_by('due_date')[:5]
        
        # Get recent contributions
        recent_contributions = contributions.order_by('-created_at')[:5]
        
        dashboard_data = {
            'child': StudentSerializer(child).data,
            'groups': GroupSerializer(groups, many=True).data,
            'statistics': {
                'total_contributions': total_contributions,
                'paid_contributions': paid_contributions,
                'pending_contributions': pending_contributions,
                'total_amount_paid': float(total_amount_paid),
                'payment_percentage': (paid_contributions / total_contributions * 100) if total_contributions > 0 else 0
            },
            'upcoming_events': ContributionEventSerializer(upcoming_events, many=True).data,
            'recent_contributions': StudentContributionSerializer(recent_contributions, many=True).data
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def child_events(self, request):
        """Get all events for a specific child"""
        user = request.user
        if user.role != 'parent':
            return Response({'error': 'Access denied. Parent role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        child_id = request.query_params.get('child_id')
        if not child_id:
            return Response({'error': 'child_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            child = Student.objects.get(
                id=child_id,
                studentparent__parent=user
            )
        except Student.DoesNotExist:
            return Response({'error': 'Child not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get events for child's groups
        events = ContributionEvent.objects.filter(
            groups__in=child.groups.all()
        ).distinct().order_by('-created_at')
        
        serializer = ContributionEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def child_contributions(self, request):
        """Get all contributions for a specific child"""
        user = request.user
        if user.role != 'parent':
            return Response({'error': 'Access denied. Parent role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        child_id = request.query_params.get('child_id')
        if not child_id:
            return Response({'error': 'child_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            child = Student.objects.get(
                id=child_id,
                studentparent__parent=user
            )
        except Student.DoesNotExist:
            return Response({'error': 'Child not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get child's contributions
        contributions = StudentContribution.objects.filter(
            student=child,
            parent=user
        ).select_related('event', 'selected_tier').order_by('-created_at')
        
        serializer = StudentContributionSerializer(contributions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def child_groups(self, request):
        """Get all groups for a specific child"""
        user = request.user
        if user.role != 'parent':
            return Response({'error': 'Access denied. Parent role required.'}, status=status.HTTP_403_FORBIDDEN)
        
        child_id = request.query_params.get('child_id')
        if not child_id:
            return Response({'error': 'child_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            child = Student.objects.get(
                id=child_id,
                studentparent__parent=user
            )
        except Student.DoesNotExist:
            return Response({'error': 'Child not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get child's groups
        groups = child.groups.all()
        
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)


class SchoolViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing schools
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'county', 'currency']
    search_fields = ['name', 'city', 'county', 'phone_number', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class SchoolSectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing school sections
    """
    queryset = SchoolSection.objects.select_related('school', 'section_head')
    serializer_class = SchoolSectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'is_active', 'school']
    search_fields = ['display_name', 'description', 'school__name']
    ordering_fields = ['name', 'display_name', 'created_at']
    ordering = ['school__name', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see sections they manage
        if user.role == 'teacher':
            queryset = queryset.filter(section_head=user)
        # Parents can only see sections their children belong to
        elif user.role == 'parent':
            queryset = queryset.filter(students__studentparent__parent=user).distinct()
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing groups (classes, clubs, etc.)
    """
    queryset = Group.objects.select_related('school', 'section', 'teacher')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group_type', 'is_active', 'school', 'section']
    search_fields = ['name', 'description', 'school__name', 'section__display_name']
    ordering_fields = ['name', 'group_type', 'created_at']
    ordering = ['school__name', 'section__name', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see groups in their managed sections
        if user.role == 'teacher':
            queryset = queryset.filter(
                section__in=user.managed_sections.all()
            )
        # Parents can only see groups their children belong to
        elif user.role == 'parent':
            queryset = queryset.filter(studentgroup__student__studentparent__parent=user).distinct()
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get all students in a group"""
        group = self.get_object()
        students = group.students.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_student(self, request, pk=None):
        """Add a student to a group"""
        group = self.get_object()
        student_id = request.data.get('student_id')
        
        try:
            student = Student.objects.get(id=student_id)
            group.students.add(student)
            return Response({'message': 'Student added to group successfully'})
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_student(self, request, pk=None):
        """Remove a student from a group"""
        group = self.get_object()
        student_id = request.data.get('student_id')
        
        try:
            student = Student.objects.get(id=student_id)
            group.students.remove(student)
            return Response({'message': 'Student removed from group successfully'})
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get group statistics"""
        group = self.get_object()
        
        total_students = group.students.count()
        active_students = group.students.filter(is_active=True).count()
        
        statistics = {
            'total_students': total_students,
            'active_students': active_students,
            'inactive_students': total_students - active_students,
            'capacity_utilization': (total_students / group.max_students * 100) if group.max_students else 0
        }
        
        return Response(statistics)


class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing students
    """
    queryset = Student.objects.select_related('school', 'section').prefetch_related('parents', 'groups')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'is_active', 'is_enrolled', 'school', 'section']
    search_fields = ['first_name', 'last_name', 'student_id', 'school__name', 'section__display_name']
    ordering_fields = ['first_name', 'last_name', 'admission_date', 'created_at']
    ordering = ['first_name', 'last_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see students in their assigned groups within their managed sections
        if user.role == 'teacher':
            queryset = queryset.filter(
                groups__teacher=user,
                section__in=user.managed_sections.all()
            ).distinct()
        # Parents can only see their own children
        elif user.role == 'parent':
            queryset = queryset.filter(studentparent__parent=user)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['get'])
    def contributions(self, request, pk=None):
        """Get all contributions for a student"""
        student = self.get_object()
        contributions = student.contributions.all()
        serializer = StudentContributionSerializer(contributions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        """Get all groups a student belongs to"""
        student = self.get_object()
        groups = student.groups.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)


class ContributionEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing contribution events
    """
    queryset = ContributionEvent.objects.select_related('school', 'section', 'created_by').prefetch_related('groups')
    serializer_class = ContributionEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'participation_type', 'is_active', 'is_published', 'school', 'section']
    search_fields = ['name', 'description', 'school__name', 'section__display_name']
    ordering_fields = ['name', 'due_date', 'event_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see events for their managed sections
        if user.role == 'teacher':
            queryset = queryset.filter(
                section__in=user.managed_sections.all()
            )
        # Parents can only see events for their children's sections
        elif user.role == 'parent':
            queryset = queryset.filter(
                groups__studentgroup__student__studentparent__parent=user
            ).distinct()
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['get'])
    def contributions(self, request, pk=None):
        """Get all contributions for an event"""
        event = self.get_object()
        contributions = event.student_contributions.all()
        serializer = StudentContributionSerializer(contributions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get event statistics"""
        event = self.get_object()
        
        total_students = event.groups.aggregate(
            total=Count('students', distinct=True)
        )['total'] or 0
        
        total_contributions = event.student_contributions.count()
        paid_contributions = event.student_contributions.filter(payment_status='paid').count()
        total_amount_paid = event.student_contributions.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        statistics = {
            'total_students': total_students,
            'total_contributions': total_contributions,
            'paid_contributions': paid_contributions,
            'pending_contributions': total_contributions - paid_contributions,
            'total_amount_paid': float(total_amount_paid),
            'payment_percentage': (paid_contributions / total_contributions * 100) if total_contributions > 0 else 0
        }
        
        return Response(statistics)


class ContributionTierViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing contribution tiers
    """
    queryset = ContributionTier.objects.select_related('event')
    serializer_class = ContributionTierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_default', 'event']
    search_fields = ['name', 'description', 'event__name']
    ordering_fields = ['name', 'amount', 'created_at']
    ordering = ['event__name', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see tiers for events in their assigned groups
        if user.role == 'teacher':
            queryset = queryset.filter(event__groups__teacher=user).distinct()
        # Parents can only see tiers for events in their children's groups
        elif user.role == 'parent':
            queryset = queryset.filter(event__groups__studentgroup__student__studentparent__parent=user).distinct()
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class StudentContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student contributions
    """
    queryset = StudentContribution.objects.select_related(
        'event', 'student', 'parent', 'selected_tier', 'confirmed_by'
    )
    serializer_class = StudentContributionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'payment_method', 'is_confirmed', 'event', 'student', 'parent']
    search_fields = ['student__first_name', 'student__last_name', 'event__name', 'parent__first_name', 'parent__last_name']
    ordering_fields = ['amount_paid', 'amount_required', 'payment_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see contributions for events in their assigned groups
        if user.role == 'teacher':
            queryset = queryset.filter(event__groups__teacher=user).distinct()
        # Parents can only see their own contributions
        elif user.role == 'parent':
            queryset = queryset.filter(parent=user)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """Confirm a payment"""
        contribution = self.get_object()
        notes = request.data.get('notes', '')
        
        contribution.confirm_payment(
            confirmed_by_user=request.user,
            notes=notes
        )
        
        serializer = self.get_serializer(contribution)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get contribution statistics"""
        user = self.request.user
        queryset = self.get_queryset()
        
        total_contributions = queryset.count()
        paid_contributions = queryset.filter(payment_status='paid').count()
        total_amount_paid = queryset.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        statistics = {
            'total_contributions': total_contributions,
            'paid_contributions': paid_contributions,
            'pending_contributions': total_contributions - paid_contributions,
            'total_amount_paid': float(total_amount_paid),
            'payment_percentage': (paid_contributions / total_contributions * 100) if total_contributions > 0 else 0
        }
        
        return Response(statistics)


class PaymentReminderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payment reminders
    """
    queryset = PaymentReminder.objects.select_related(
        'contribution', 'parent', 'created_by'
    )
    serializer_class = PaymentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['reminder_type', 'status', 'parent', 'created_by']
    search_fields = ['parent__first_name', 'parent__last_name', 'contribution__event__name']
    ordering_fields = ['scheduled_at', 'sent_at', 'created_at']
    ordering = ['-scheduled_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see reminders for events in their assigned groups
        if user.role == 'teacher':
            queryset = queryset.filter(contribution__event__groups__teacher=user).distinct()
        # Parents can only see their own reminders
        elif user.role == 'parent':
            queryset = queryset.filter(parent=user)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
