from django.contrib import admin
from django.db.models import Count
from .models import (
    School, Group, Student, StudentGroup, StudentParent,
    ContributionEvent, ContributionTier, StudentContribution, ReminderLog, PaymentHistory
)
from django.utils import timezone


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """
    Admin for School model
    """
    list_display = ['name', 'city', 'county', 'phone_number', 'currency', 'created_at']
    list_filter = ['city', 'county', 'currency', 'created_at']
    search_fields = ['name', 'city', 'county', 'phone_number', 'email']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'address', 'city', 'county')}),
        ('Contact Information', {'fields': ('phone_number', 'email', 'website')}),
        ('Settings', {'fields': ('currency', 'timezone')}),
        ('Media', {'fields': ('logo',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Admin for Group model
    """
    list_display = ['name', 'school', 'group_type', 'teacher', 'student_count', 'is_active', 'created_at']
    list_filter = ['group_type', 'is_active', 'school', 'created_at']
    search_fields = ['name', 'description', 'school__name']
    ordering = ['school__name', 'name']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description', 'group_type')}),
        ('Relationships', {'fields': ('school', 'teacher')}),
        ('Settings', {'fields': ('is_active', 'max_students')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'student_count']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """
    Admin for Student model
    """
    list_display = ['full_name', 'student_id', 'school', 'gender', 'age', 'is_active', 'admission_date']
    list_filter = ['gender', 'is_active', 'school', 'admission_date', 'created_at']
    search_fields = ['first_name', 'last_name', 'student_id', 'school__name']
    ordering = ['school__name', 'first_name', 'last_name']
    
    fieldsets = (
        ('Basic Information', {'fields': ('first_name', 'last_name', 'date_of_birth', 'gender')}),
        ('School Information', {'fields': ('school', 'student_id', 'admission_date', 'is_active')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')}),
        ('Medical Information', {'fields': ('medical_conditions', 'allergies')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'age']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('school')


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    """
    Admin for StudentGroup model
    """
    list_display = ['student', 'group', 'academic_year', 'term', 'is_active', 'joined_date']
    list_filter = ['is_active', 'academic_year', 'term', 'joined_date', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'group__name']
    ordering = ['-joined_date']
    
    fieldsets = (
        ('Relationships', {'fields': ('student', 'group')}),
        ('Academic Information', {'fields': ('academic_year', 'term')}),
        ('Status', {'fields': ('is_active', 'joined_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentParent)
class StudentParentAdmin(admin.ModelAdmin):
    """
    Admin for StudentParent model
    """
    list_display = ['parent', 'student', 'relationship', 'is_primary_contact', 'is_emergency_contact', 'receives_notifications']
    list_filter = ['relationship', 'is_primary_contact', 'is_emergency_contact', 'receives_notifications', 'receives_sms', 'receives_email', 'created_at']
    search_fields = ['parent__first_name', 'parent__last_name', 'student__first_name', 'student__last_name']
    ordering = ['student__first_name', 'parent__first_name']
    
    fieldsets = (
        ('Relationships', {'fields': ('student', 'parent', 'relationship')}),
        ('Contact Preferences', {'fields': ('is_primary_contact', 'is_emergency_contact')}),
        ('Notification Preferences', {'fields': ('receives_notifications', 'receives_sms', 'receives_email')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContributionEvent)
class ContributionEventAdmin(admin.ModelAdmin):
    """
    Admin for ContributionEvent model
    """
    list_display = ['name', 'school', 'event_type', 'amount', 'currency', 'participation_type', 'due_date', 'is_active', 'is_published', 'student_count']
    list_filter = ['event_type', 'participation_type', 'is_active', 'is_published', 'school', 'created_at']
    search_fields = ['name', 'description', 'school__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description', 'event_type')}),
        ('School and Groups', {'fields': ('school', 'groups')}),
        ('Financial Information', {'fields': ('amount', 'currency', 'has_tiers')}),
        ('Participation Rules', {'fields': ('participation_type',)}),
        ('Dates', {'fields': ('due_date', 'event_date')}),
        ('Status', {'fields': ('is_active', 'is_published')}),
        ('Created By', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'student_count']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('school', 'created_by')
    
    def student_count(self, obj):
        """Get the number of students in the event's groups"""
        return obj.groups.aggregate(
            total=Count('students', distinct=True)
        )['total'] or 0
    student_count.short_description = 'Students'
    
    actions = ['publish_events', 'unpublish_events', 'create_student_contributions']
    
    def publish_events(self, request, queryset):
        """Publish selected events"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} events published successfully.')
    publish_events.short_description = "Publish selected events"
    
    def unpublish_events(self, request, queryset):
        """Unpublish selected events"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} events unpublished successfully.')
    unpublish_events.short_description = "Unpublish selected events"
    
    def create_student_contributions(self, request, queryset):
        """Create student contribution records for selected events"""
        from .models import StudentContribution, StudentGroup
        
        total_created = 0
        for event in queryset:
            if not event.groups.exists():
                continue
                
            # Get all students from assigned groups
            student_ids = StudentGroup.objects.filter(
                group__in=event.groups.all(),
                is_active=True
            ).values_list('student_id', flat=True).distinct()
            
            students = Student.objects.filter(id__in=student_ids, is_active=True)
            
            for student in students:
                contribution, created = StudentContribution.objects.get_or_create(
                    student=student,
                    event=event,
                    defaults={
                        'amount_required': event.amount,
                        'payment_status': 'pending'
                    }
                )
                if created:
                    total_created += 1
        
        self.message_user(request, f'{total_created} student contribution records created successfully.')
    create_student_contributions.short_description = "Create student contributions for selected events"


@admin.register(ContributionTier)
class ContributionTierAdmin(admin.ModelAdmin):
    """
    Admin for ContributionTier model
    """
    list_display = ['name', 'event', 'amount', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at', 'event__event_type']
    search_fields = ['name', 'description', 'event__name']
    ordering = ['event__name', 'name']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description', 'amount', 'is_default')}),
        ('Event', {'fields': ('event',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['set_as_default', 'remove_default']
    
    def set_as_default(self, request, queryset):
        """Set selected tiers as default for their events"""
        updated = 0
        for tier in queryset:
            # Remove default from other tiers in the same event
            ContributionTier.objects.filter(event=tier.event, is_default=True).update(is_default=False)
            # Set this tier as default
            tier.is_default = True
            tier.save()
            updated += 1
        
        self.message_user(request, f'{updated} tiers set as default successfully.')
    set_as_default.short_description = "Set selected tiers as default"
    
    def remove_default(self, request, queryset):
        """Remove default status from selected tiers"""
        updated = queryset.update(is_default=False)
        self.message_user(request, f'{updated} tiers removed from default successfully.')
    remove_default.short_description = "Remove default status from selected tiers"


@admin.register(StudentContribution)
class StudentContributionAdmin(admin.ModelAdmin):
    """
    Admin for StudentContribution model
    """
    list_display = ['student', 'event', 'amount_required', 'amount_paid', 'payment_status', 'payment_date', 'confirmed_by', 'updated_at']
    list_filter = ['payment_status', 'event__event_type', 'event__school', 'payment_date', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'event__name', 'transaction_id']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Relationships', {'fields': ('student', 'event', 'tier')}),
        ('Payment Information', {'fields': ('amount_required', 'amount_paid', 'payment_status')}),
        ('Payment Details', {'fields': ('payment_date', 'payment_method', 'transaction_id')}),
        ('Manual Confirmation', {'fields': ('confirmed_by', 'confirmed_at', 'confirmation_notes')}),
        ('Notes', {'fields': ('notes',)}),
        ('Updated By', {'fields': ('updated_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'amount_remaining', 'payment_percentage', 'confirmed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'event', 'tier', 'updated_by', 'confirmed_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only for new objects
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        obj.update_payment_status()
    
    actions = ['confirm_payments', 'bulk_update_status']
    
    def confirm_payments(self, request, queryset):
        """Manually confirm selected payments"""
        confirmed_count = 0
        for contribution in queryset:
            if not contribution.confirmed_by:
                contribution.confirm_payment(request.user, "Bulk confirmation via admin")
                confirmed_count += 1
        
        self.message_user(request, f'{confirmed_count} payments confirmed successfully.')
    confirm_payments.short_description = "Confirm selected payments"
    
    def bulk_update_status(self, request, queryset):
        """Bulk update payment status"""
        new_status = request.POST.get('new_status')
        if new_status:
            updated = queryset.update(payment_status=new_status)
            self.message_user(request, f'{updated} contributions updated to {new_status} status.')
        else:
            self.message_user(request, 'Please select a new status.', level='ERROR')
    bulk_update_status.short_description = "Update payment status"


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """
    Admin for PaymentHistory model
    """
    list_display = ['contribution', 'amount', 'payment_method', 'status', 'payment_date', 'created_by', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_date', 'created_at']
    search_fields = ['contribution__student__first_name', 'contribution__student__last_name', 'transaction_id', 'external_id']
    ordering = ['-payment_date']
    
    fieldsets = (
        ('Contribution', {'fields': ('contribution',)}),
        ('Payment Details', {'fields': ('amount', 'payment_method', 'transaction_id', 'status')}),
        ('Payment Metadata', {'fields': ('payment_date', 'processed_at')}),
        ('External Service', {'fields': ('external_id', 'external_status', 'external_response')}),
        ('Notes and Metadata', {'fields': ('notes', 'metadata')}),
        ('Created By', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'is_completed', 'is_failed']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contribution__student', 'contribution__event', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_cancelled']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected payments as completed"""
        updated = queryset.update(status='completed', processed_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as completed.')
    mark_as_completed.short_description = "Mark as completed"
    
    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed"""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = "Mark as failed"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected payments as cancelled"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} payments marked as cancelled.')
    mark_as_cancelled.short_description = "Mark as cancelled"


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    """
    Admin for ReminderLog model
    """
    list_display = ['parent', 'student', 'event', 'reminder_type', 'status', 'sent_at', 'created_at']
    list_filter = ['reminder_type', 'status', 'created_at', 'sent_at']
    search_fields = ['parent__first_name', 'parent__last_name', 'student__first_name', 'student__last_name', 'event__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Recipients', {'fields': ('student', 'parent', 'event')}),
        ('Reminder Details', {'fields': ('reminder_type', 'message', 'status')}),
        ('Delivery Information', {'fields': ('sent_at', 'delivered_at', 'delivery_error')}),
        ('External Service', {'fields': ('external_id', 'external_status')}),
        ('Created By', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'parent', 'event', 'created_by')
