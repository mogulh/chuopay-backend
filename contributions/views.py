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
            queryset = queryset.filter(students__parents=user).distinct()
        
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
            queryset = queryset.filter(students__parents=user).distinct()
        
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
            queryset = queryset.filter(parents=user)
        
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
                groups__students__parents=user
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
            queryset = queryset.filter(event__groups__students__parents=user).distinct()
        
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
