from django.shortcuts import render
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    School, Group, Student, StudentGroup, StudentParent,
    ContributionEvent, ContributionTier, StudentContribution, ReminderLog, PaymentHistory
)
from .serializers import (
    SchoolSerializer, GroupSerializer, StudentSerializer, StudentGroupSerializer,
    StudentParentSerializer, ContributionEventSerializer, ContributionTierSerializer,
    StudentContributionSerializer, ReminderLogSerializer, PaymentHistorySerializer,
    StudentContributionDetailSerializer, PaymentConfirmationSerializer, PaymentReconciliationSerializer,
    PaymentTrackingStatisticsSerializer
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


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing groups (classes, clubs, etc.)
    """
    queryset = Group.objects.select_related('school', 'teacher').prefetch_related('students')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group_type', 'is_active', 'school', 'teacher']
    search_fields = ['name', 'description', 'school__name']
    ordering_fields = ['name', 'created_at', 'student_count']
    ordering = ['school__name', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see groups they're assigned to
        if user.role == 'teacher':
            queryset = queryset.filter(teacher=user)
        # Parents can only see groups their children are in
        elif user.role == 'parent':
            student_ids = StudentParent.objects.filter(parent=user).values_list('student_id', flat=True)
            queryset = queryset.filter(students__id__in=student_ids).distinct()
        
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
            StudentGroup.objects.create(
                student=student,
                group=group,
                academic_year=request.data.get('academic_year', '2024-2025'),
                term=request.data.get('term', '')
            )
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
            student_group = StudentGroup.objects.get(student_id=student_id, group=group)
            student_group.delete()
            return Response({'message': 'Student removed from group successfully'})
        except StudentGroup.DoesNotExist:
            return Response({'error': 'Student not in group'}, status=status.HTTP_404_NOT_FOUND)


class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing students
    """
    queryset = Student.objects.select_related('school').prefetch_related('groups', 'parents')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'is_active', 'school', 'admission_date']
    search_fields = ['first_name', 'last_name', 'student_id', 'school__name']
    ordering_fields = ['first_name', 'last_name', 'admission_date', 'created_at']
    ordering = ['school__name', 'first_name', 'last_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see students in their assigned groups
        if user.role == 'teacher':
            group_ids = Group.objects.filter(teacher=user).values_list('id', flat=True)
            student_ids = StudentGroup.objects.filter(group_id__in=group_ids).values_list('student_id', flat=True)
            queryset = queryset.filter(id__in=student_ids)
        # Parents can only see their own children
        elif user.role == 'parent':
            student_ids = StudentParent.objects.filter(parent=user).values_list('student_id', flat=True)
            queryset = queryset.filter(id__in=student_ids)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        """Get all groups a student belongs to"""
        student = self.get_object()
        groups = student.groups.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def parents(self, request, pk=None):
        """Get all parents of a student"""
        student = self.get_object()
        parents = student.parents.all()
        from accounts.serializers import UserSerializer
        serializer = UserSerializer(parents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def contributions(self, request, pk=None):
        """Get all contributions for a student"""
        student = self.get_object()
        contributions = student.contributions.all()
        serializer = StudentContributionSerializer(contributions, many=True)
        return Response(serializer.data)


class StudentGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student-group relationships
    """
    queryset = StudentGroup.objects.select_related('student', 'group')
    serializer_class = StudentGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'academic_year', 'term', 'group', 'student']
    search_fields = ['student__first_name', 'student__last_name', 'group__name']
    ordering_fields = ['joined_date', 'created_at']
    ordering = ['-joined_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see relationships for their groups
        if user.role == 'teacher':
            group_ids = Group.objects.filter(teacher=user).values_list('id', flat=True)
            queryset = queryset.filter(group_id__in=group_ids)
        # Parents can only see relationships for their children
        elif user.role == 'parent':
            student_ids = StudentParent.objects.filter(parent=user).values_list('student_id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class StudentParentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student-parent relationships
    """
    queryset = StudentParent.objects.select_related('student', 'parent')
    serializer_class = StudentParentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['relationship', 'is_primary_contact', 'is_emergency_contact', 'receives_notifications']
    search_fields = ['parent__first_name', 'parent__last_name', 'student__first_name', 'student__last_name']
    ordering_fields = ['created_at']
    ordering = ['student__first_name', 'parent__first_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Parents can only see their own relationships
        if user.role == 'parent':
            queryset = queryset.filter(parent=user)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class ContributionEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing contribution events
    """
    queryset = ContributionEvent.objects.select_related('school', 'created_by').prefetch_related('groups', 'tiers')
    serializer_class = ContributionEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'participation_type', 'is_active', 'is_published', 'school']
    search_fields = ['name', 'description', 'school__name']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admin users can see all events
        if user.role == 'admin':
            return queryset
        # Teachers can only see events for their groups
        elif user.role == 'teacher':
            group_ids = Group.objects.filter(teacher=user).values_list('id', flat=True)
            queryset = queryset.filter(groups__id__in=group_ids).distinct()
        # Parents can only see events for their children's groups
        elif user.role == 'parent':
            student_ids = StudentParent.objects.filter(parent=user).values_list('student_id', flat=True)
            group_ids = StudentGroup.objects.filter(student_id__in=student_ids).values_list('group_id', flat=True)
            queryset = queryset.filter(groups__id__in=group_ids).distinct()
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        # Allow admin users to create/edit events
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        """Set the created_by field to the current user and school based on user's school"""
        user = self.request.user
        
        # Get the user's school (assuming admin users are associated with a school)
        # For now, we'll get the first school or create a default one
        try:
            school = School.objects.first()
            if not school:
                # Create a default school if none exists
                school = School.objects.create(
                    name="Default School",
                    address="Default Address",
                    city="Nairobi",
                    county="Nairobi",
                    phone_number="+254700000000",
                    email="admin@school.com"
                )
        except Exception as e:
            # If there's any issue, create a default school
            school = School.objects.create(
                name="Default School",
                address="Default Address",
                city="Nairobi",
                county="Nairobi",
                phone_number="+254700000000",
                email="admin@school.com"
            )
        
        serializer.save(created_by=user, school=school)

    @action(detail=True, methods=['get'])
    def student_contributions(self, request, pk=None):
        """Get all student contributions for an event"""
        event = self.get_object()
        contributions = event.student_contributions.all()
        serializer = StudentContributionSerializer(contributions, many=True)
        return Response(serializer.data)

    def _create_student_contributions_for_event(self, event):
        """Helper method to create contribution records for all students in assigned groups"""
        if not event.groups.exists():
            return 0, 0
        
        # Get all students from assigned groups
        student_ids = StudentGroup.objects.filter(
            group__in=event.groups.all(),
            is_active=True
        ).values_list('student_id', flat=True).distinct()
        
        students = Student.objects.filter(id__in=student_ids, is_active=True)
        total_students = students.count()
        
        created_count = 0
        for student in students:
            # Check if contribution already exists
            contribution, created = StudentContribution.objects.get_or_create(
                student=student,
                event=event,
                defaults={
                    'amount_required': event.amount,
                    'payment_status': 'pending'
                }
            )
            if created:
                created_count += 1
        
        return total_students, created_count

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish an event to make it visible to parents and create student contributions"""
        event = self.get_object()
        
        # Check if event has groups assigned
        if not event.groups.exists():
            return Response({
                'error': 'Cannot publish event without assigned groups'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create student contributions if they don't exist
        total_students, created_count = self._create_student_contributions_for_event(event)
        
        # Publish the event
        event.is_published = True
        event.save()
        
        return Response({
            'message': 'Event published successfully',
            'total_students': total_students,
            'created_contributions': created_count,
            'existing_contributions': total_students - created_count
        })

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish an event to hide it from parents"""
        event = self.get_object()
        event.is_published = False
        event.save()
        return Response({'message': 'Event unpublished successfully'})

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for an event"""
        event = self.get_object()
        
        # Get contribution statistics
        total_students = event.groups.aggregate(
            total=Count('students', distinct=True)
        )['total'] or 0
        
        contributions = event.student_contributions.all()
        total_contributions = contributions.count()
        paid_contributions = contributions.filter(payment_status='paid').count()
        partial_contributions = contributions.filter(payment_status='partial').count()
        pending_contributions = contributions.filter(payment_status='pending').count()
        
        total_amount_required = contributions.aggregate(
            total=Sum('amount_required')
        )['total'] or 0
        
        total_amount_paid = contributions.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        payment_rate = (total_amount_paid / total_amount_required * 100) if total_amount_required > 0 else 0
        
        return Response({
            'total_students': total_students,
            'total_contributions': total_contributions,
            'paid_contributions': paid_contributions,
            'partial_contributions': partial_contributions,
            'pending_contributions': pending_contributions,
            'total_amount_required': total_amount_required,
            'total_amount_paid': total_amount_paid,
            'payment_rate': round(payment_rate, 2),
            'is_overdue': event.is_overdue,
            'days_until_due': event.days_until_due
        })

    @action(detail=True, methods=['post'])
    def assign_groups(self, request, pk=None):
        """Assign groups to an event"""
        event = self.get_object()
        group_ids = request.data.get('group_ids', [])
        
        if not group_ids:
            return Response({'error': 'No group IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        groups = Group.objects.filter(id__in=group_ids, school=event.school)
        event.groups.set(groups)
        
        return Response({
            'message': f'Assigned {groups.count()} groups to event',
            'assigned_groups': [group.name for group in groups]
        })

    @action(detail=True, methods=['post'])
    def create_student_contributions(self, request, pk=None):
        """Create contribution records for all students in assigned groups"""
        event = self.get_object()
        
        if not event.groups.exists():
            return Response({'error': 'No groups assigned to this event'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the helper method to create contributions
        total_students, created_count = self._create_student_contributions_for_event(event)
        
        return Response({
            'message': f'Created {created_count} student contribution records',
            'total_students': total_students,
            'created_contributions': created_count
        })


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
    ordering_fields = ['amount', 'created_at']
    ordering = ['amount']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see tiers for events in their groups
        if user.role == 'teacher':
            group_ids = Group.objects.filter(teacher=user).values_list('id', flat=True)
            event_ids = ContributionEvent.objects.filter(groups__id__in=group_ids).values_list('id', flat=True)
            queryset = queryset.filter(event_id__in=event_ids)
        # Parents can only see tiers for events in their children's groups
        elif user.role == 'parent':
            student_ids = StudentParent.objects.filter(parent=user).values_list('student_id', flat=True)
            group_ids = StudentGroup.objects.filter(student_id__in=student_ids).values_list('group_id', flat=True)
            event_ids = ContributionEvent.objects.filter(groups__id__in=group_ids).values_list('id', flat=True)
            queryset = queryset.filter(event_id__in=event_ids)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]


class StudentContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student contributions
    """
    queryset = StudentContribution.objects.select_related('student', 'event', 'tier', 'updated_by', 'confirmed_by')
    serializer_class = StudentContributionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'event__event_type', 'event__school', 'payment_date']
    search_fields = ['student__first_name', 'student__last_name', 'event__name', 'transaction_id']
    ordering_fields = ['payment_date', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see contributions for their students
        if user.role == 'teacher':
            group_ids = Group.objects.filter(teacher=user).values_list('id', flat=True)
            student_ids = StudentGroup.objects.filter(group_id__in=group_ids).values_list('student_id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        # Parents can only see contributions for their children
        elif user.role == 'parent':
            student_ids = StudentParent.objects.filter(parent=user).values_list('student_id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update_payment']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StudentContributionDetailSerializer
        return StudentContributionSerializer

    @action(detail=True, methods=['post'])
    def update_payment(self, request, pk=None):
        """Update payment information for a contribution"""
        contribution = self.get_object()
        user = request.user
        
        # Only parents can update their children's payments
        if user.role != 'parent':
            return Response({'error': 'Only parents can update payments'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if this parent is authorized for this student
        if not StudentParent.objects.filter(parent=user, student=contribution.student).exists():
            return Response({'error': 'Not authorized for this student'}, status=status.HTTP_403_FORBIDDEN)
        
        amount_paid = request.data.get('amount_paid')
        payment_method = request.data.get('payment_method')
        transaction_id = request.data.get('transaction_id')
        notes = request.data.get('notes', '')
        
        if amount_paid is not None:
            contribution.amount_paid = amount_paid
            contribution.payment_date = timezone.now()
            contribution.payment_method = payment_method or 'manual'
            contribution.transaction_id = transaction_id or ''
            contribution.notes = notes
            contribution.updated_by = user
            contribution.update_payment_status()
            contribution.save()
            
            return Response({
                'message': 'Payment updated successfully',
                'payment_status': contribution.payment_status,
                'amount_remaining': contribution.amount_remaining,
                'payment_percentage': contribution.payment_percentage
            })
        
        return Response({'error': 'Amount paid is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """Manually confirm a payment (admin/teacher only)"""
        contribution = self.get_object()
        user = request.user
        
        # Only admins and teachers can confirm payments
        if user.role not in ['admin', 'teacher']:
            return Response({'error': 'Only admins and teachers can confirm payments'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PaymentConfirmationSerializer(data=request.data)
        if serializer.is_valid():
            notes = serializer.validated_data.get('notes', '')
            amount_confirmed = serializer.validated_data.get('amount_confirmed')
            
            # Confirm the payment
            contribution.confirm_payment(user, notes)
            
            # Create payment history record
            PaymentHistory.objects.create(
                contribution=contribution,
                amount=amount_confirmed or contribution.amount_paid,
                payment_method='manual',
                status='completed',
                payment_date=timezone.now(),
                processed_at=timezone.now(),
                notes=f"Manually confirmed by {user.full_name}. {notes}",
                created_by=user
            )
            
            return Response({
                'message': 'Payment confirmed successfully',
                'payment_status': contribution.payment_status,
                'confirmed_by': user.full_name,
                'confirmed_at': contribution.confirmed_at
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def payment_history(self, request, pk=None):
        """Get payment history for a contribution"""
        contribution = self.get_object()
        payment_history = contribution.payment_history.all().order_by('-payment_date')
        serializer = PaymentHistorySerializer(payment_history, many=True)
        
        return Response({
            'contribution_id': contribution.id,
            'total_required': contribution.amount_required,
            'total_paid': contribution.amount_paid,
            'payment_status': contribution.payment_status,
            'last_payment_date': contribution.payment_date,
            'payment_method': contribution.payment_method,
            'transaction_id': contribution.transaction_id,
            'payment_history': serializer.data
        })

    @action(detail=True, methods=['post'])
    def add_payment_transaction(self, request, pk=None):
        """Add a new payment transaction"""
        contribution = self.get_object()
        user = request.user
        
        # Only admins and teachers can add payment transactions
        if user.role not in ['admin', 'teacher']:
            return Response({'error': 'Only admins and teachers can add payment transactions'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PaymentHistorySerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(contribution=contribution, created_by=user)
            
            return Response({
                'message': 'Payment transaction added successfully',
                'payment_id': payment.id,
                'contribution_status': contribution.payment_status,
                'amount_remaining': contribution.amount_remaining
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_confirm_payments(self, request):
        """Bulk confirm multiple payments"""
        user = request.user
        
        # Only admins and teachers can bulk confirm payments
        if user.role not in ['admin', 'teacher']:
            return Response({'error': 'Only admins and teachers can bulk confirm payments'}, status=status.HTTP_403_FORBIDDEN)
        
        contribution_ids = request.data.get('contribution_ids', [])
        notes = request.data.get('notes', '')
        
        if not contribution_ids:
            return Response({'error': 'No contribution IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        contributions = StudentContribution.objects.filter(id__in=contribution_ids)
        confirmed_count = 0
        
        for contribution in contributions:
            if not contribution.confirmed_by:  # Only confirm unconfirmed payments
                contribution.confirm_payment(user, notes)
                confirmed_count += 1
        
        return Response({
            'message': f'Successfully confirmed {confirmed_count} payments',
            'total_requested': len(contribution_ids),
            'confirmed_count': confirmed_count
        })

    @action(detail=False, methods=['get'])
    def payment_statistics(self, request):
        """Get payment statistics for contributions"""
        user = request.user
        
        # Get queryset based on user role
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_contributions = queryset.count()
        paid_contributions = queryset.filter(payment_status='paid').count()
        confirmed_contributions = queryset.filter(payment_status='confirmed').count()
        partial_contributions = queryset.filter(payment_status='partial').count()
        pending_contributions = queryset.filter(payment_status='pending').count()
        overdue_contributions = queryset.filter(payment_status='overdue').count()
        
        total_amount_required = queryset.aggregate(total=Sum('amount_required'))['total'] or 0
        total_amount_paid = queryset.aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Payment method breakdown
        payment_methods = queryset.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount_paid')
        ).exclude(payment_method='')
        
        return Response({
            'total_contributions': total_contributions,
            'paid_contributions': paid_contributions,
            'confirmed_contributions': confirmed_contributions,
            'partial_contributions': partial_contributions,
            'pending_contributions': pending_contributions,
            'overdue_contributions': overdue_contributions,
            'total_amount_required': total_amount_required,
            'total_amount_paid': total_amount_paid,
            'payment_rate': (total_amount_paid / total_amount_required * 100) if total_amount_required > 0 else 0,
            'payment_methods': list(payment_methods)
        })


class PaymentHistoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payment history
    """
    queryset = PaymentHistory.objects.select_related('contribution__student', 'contribution__event', 'created_by')
    serializer_class = PaymentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'payment_date', 'contribution__event']
    search_fields = ['contribution__student__first_name', 'contribution__student__last_name', 'transaction_id']
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see payments for their students
        if user.role == 'teacher':
            group_ids = Group.objects.filter(teacher=user).values_list('id', flat=True)
            student_ids = StudentGroup.objects.filter(group_id__in=group_ids).values_list('student_id', flat=True)
            queryset = queryset.filter(contribution__student_id__in=student_ids)
        # Parents can only see payments for their children
        elif user.role == 'parent':
            student_ids = StudentParent.objects.filter(parent=user).values_list('student_id', flat=True)
            queryset = queryset.filter(contribution__student_id__in=student_ids)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update payment transaction status"""
        payment = self.get_object()
        user = request.user
        
        # Only admins and teachers can update payment status
        if user.role not in ['admin', 'teacher']:
            return Response({'error': 'Only admins and teachers can update payment status'}, status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(PaymentHistory.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        payment.status = new_status
        payment.notes = f"{payment.notes}\n{timezone.now().strftime('%Y-%m-%d %H:%M')}: Status updated to {new_status} by {user.full_name}. {notes}"
        payment.save()
        
        return Response({
            'message': 'Payment status updated successfully',
            'new_status': payment.status,
            'contribution_status': payment.contribution.payment_status
        })

    @action(detail=False, methods=['get'])
    def reconciliation_report(self, request):
        """Generate payment reconciliation report"""
        user = request.user
        
        # Only admins and teachers can access reconciliation reports
        if user.role not in ['admin', 'teacher']:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get filter parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        event_id = request.query_params.get('event_id')
        group_id = request.query_params.get('group_id')
        payment_method = request.query_params.get('payment_method')
        
        # Build queryset
        queryset = self.get_queryset()
        
        if start_date:
            queryset = queryset.filter(payment_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__date__lte=end_date)
        if event_id:
            queryset = queryset.filter(contribution__event_id=event_id)
        if group_id:
            queryset = queryset.filter(contribution__student__groups__id=group_id)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Calculate reconciliation data
        total_transactions = queryset.count()
        completed_transactions = queryset.filter(status='completed').count()
        failed_transactions = queryset.filter(status='failed').count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        completed_amount = queryset.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        
        # Payment method breakdown
        method_breakdown = queryset.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            completed_amount=Sum('amount', filter=Q(status='completed'))
        )
        
        # Daily breakdown
        daily_breakdown = queryset.values('payment_date__date').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            completed_amount=Sum('amount', filter=Q(status='completed'))
        ).order_by('payment_date__date')
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_transactions': total_transactions,
                'completed_transactions': completed_transactions,
                'failed_transactions': failed_transactions,
                'success_rate': (completed_transactions / total_transactions * 100) if total_transactions > 0 else 0,
                'total_amount': total_amount,
                'completed_amount': completed_amount,
                'reconciliation_rate': (completed_amount / total_amount * 100) if total_amount > 0 else 0
            },
            'payment_methods': list(method_breakdown),
            'daily_breakdown': list(daily_breakdown)
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get payment tracking statistics"""
        user = request.user
        
        # Only admins and teachers can access statistics
        if user.role not in ['admin', 'teacher']:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get queryset
        queryset = self.get_queryset().filter(payment_date__range=[start_date, end_date])
        
        # Calculate statistics
        total_transactions = queryset.count()
        completed_transactions = queryset.filter(status='completed').count()
        failed_transactions = queryset.filter(status='failed').count()
        total_amount_processed = queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_amount_completed = queryset.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        
        # Payment method breakdown
        payment_method_breakdown = queryset.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            completed_amount=Sum('amount', filter=Q(status='completed'))
        )
        
        # Daily transactions
        daily_transactions = queryset.values('payment_date__date').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            completed_amount=Sum('amount', filter=Q(status='completed'))
        ).order_by('payment_date__date')
        
        # Calculate averages
        average_transaction_amount = total_amount_processed / total_transactions if total_transactions > 0 else 0
        success_rate = (completed_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        return Response({
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days
            },
            'total_transactions': total_transactions,
            'completed_transactions': completed_transactions,
            'failed_transactions': failed_transactions,
            'total_amount_processed': total_amount_processed,
            'total_amount_completed': total_amount_completed,
            'success_rate': success_rate,
            'average_transaction_amount': average_transaction_amount,
            'payment_method_breakdown': list(payment_method_breakdown),
            'daily_transactions': list(daily_transactions)
        })


class ParentDashboardViewSet(viewsets.ViewSet):
    """
    Parent-specific dashboard endpoints
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        return [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Get parent dashboard summary"""
        user = request.user
        
        if user.role != 'parent':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get parent's children
        children = Student.objects.filter(
            parents=user,
            is_active=True
        ).select_related('school')
        
        # Get all contributions for children
        contributions = StudentContribution.objects.filter(
            student__in=children
        ).select_related('student', 'event', 'tier')
        
        # Calculate summary statistics
        total_events = contributions.values('event').distinct().count()
        total_required = contributions.aggregate(total=Sum('amount_required'))['total'] or 0
        total_paid = contributions.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_remaining = total_required - total_paid
        
        # Payment status breakdown
        status_breakdown = contributions.values('payment_status').annotate(
            count=Count('id'),
            amount=Sum('amount_required')
        )
        
        # Recent contributions (last 5)
        recent_contributions = contributions.order_by('-updated_at')[:5]
        
        # Upcoming due dates (next 7 days)
        upcoming_deadline = timezone.now() + timedelta(days=7)
        upcoming_contributions = contributions.filter(
            event__due_date__lte=upcoming_deadline,
            payment_status__in=['pending', 'partial']
        ).select_related('event')
        
        return Response({
            'children_count': children.count(),
            'total_events': total_events,
            'total_required': total_required,
            'total_paid': total_paid,
            'total_remaining': total_remaining,
            'payment_percentage': (total_paid / total_required * 100) if total_required > 0 else 0,
            'status_breakdown': list(status_breakdown),
            'recent_contributions': StudentContributionSerializer(recent_contributions, many=True).data,
            'upcoming_contributions': StudentContributionSerializer(upcoming_contributions, many=True).data,
            'children': [
                {
                    'id': child.id,
                    'name': child.full_name,
                    'school': child.school.name,
                    'contributions_count': contributions.filter(student=child).count()
                }
                for child in children
            ]
        })

    @action(detail=False, methods=['get'])
    def children_contributions(self, request):
        """Get all contributions for parent's children"""
        user = request.user
        
        if user.role != 'parent':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get filter parameters
        child_id = request.query_params.get('child_id')
        payment_status = request.query_params.get('payment_status')
        event_type = request.query_params.get('event_type')
        
        # Get parent's children
        children = Student.objects.filter(parents=user, is_active=True)
        if child_id:
            children = children.filter(id=child_id)
        
        # Get contributions
        contributions = StudentContribution.objects.filter(
            student__in=children
        ).select_related('student', 'event', 'tier')
        
        # Apply filters
        if payment_status:
            contributions = contributions.filter(payment_status=payment_status)
        
        if event_type:
            contributions = contributions.filter(event__event_type=event_type)
        
        # Order by due date
        contributions = contributions.order_by('event__due_date')
        
        return Response({
            'contributions': StudentContributionSerializer(contributions, many=True).data,
            'children': [
                {
                    'id': child.id,
                    'name': child.full_name,
                    'school': child.school.name
                }
                for child in children
            ]
        })

    @action(detail=False, methods=['get'])
    def payment_methods(self, request):
        """Get available payment methods"""
        return Response({
            'payment_methods': [
                {
                    'id': 'mpesa_stk',
                    'name': 'MPESA STK Push',
                    'description': 'Pay directly via MPESA',
                    'icon': 'mobile'
                },
                {
                    'id': 'mpesa_ussd',
                    'name': 'MPESA USSD',
                    'description': 'Pay via USSD code',
                    'icon': 'phone'
                },
                {
                    'id': 'bank_transfer',
                    'name': 'Bank Transfer',
                    'description': 'Transfer to school account',
                    'icon': 'bank'
                },
                {
                    'id': 'cash',
                    'name': 'Cash Payment',
                    'description': 'Pay at school office',
                    'icon': 'money'
                }
            ]
        })


class ReminderLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing reminder logs
    """
    queryset = ReminderLog.objects.select_related('student', 'parent', 'event', 'created_by')
    serializer_class = ReminderLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['reminder_type', 'status', 'created_at', 'sent_at']
    search_fields = ['parent__first_name', 'parent__last_name', 'student__first_name', 'student__last_name', 'event__name']
    ordering_fields = ['sent_at', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Teachers can only see reminders for their students
        if user.role == 'teacher':
            group_ids = Group.objects.filter(teacher=user).values_list('id', flat=True)
            student_ids = StudentGroup.objects.filter(group_id__in=group_ids).values_list('student_id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        # Parents can only see their own reminders
        elif user.role == 'parent':
            queryset = queryset.filter(parent=user)
        
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
