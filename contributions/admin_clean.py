from django.contrib import admin
from django.db.models import Count
from .models import (
    School, Group, Student,
    ContributionEvent, ContributionTier, StudentContribution, PaymentReminder
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
        ('School Information', {'fields': ('school', 'student_id', 'admission_date', 'current_class', 'is_active', 'is_enrolled')}),
        ('Contact Information', {'fields': ('phone_number', 'email', 'address')}),
        ('Relationships', {'fields': ('parents', 'groups')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'age']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('school')


@admin.register(ContributionEvent)
class ContributionEventAdmin(admin.ModelAdmin):
    """
    Admin for ContributionEvent model
    """
    list_display = ['name', 'school', 'event_type', 'amount', 'currency', 'participation_type', 'is_active', 'is_published', 'due_date']
    list_filter = ['event_type', 'participation_type', 'is_active', 'is_published', 'school', 'created_at']
    search_fields = ['name', 'description', 'school__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description', 'event_type')}),
        ('Relationships', {'fields': ('school', 'groups', 'created_by')}),
        ('Financial Information', {'fields': ('amount', 'currency', 'has_tiers')}),
        ('Participation Rules', {'fields': ('participation_type', 'requires_approval', 'requires_payment', 'approval_before_payment')}),
        ('Deadlines', {'fields': ('approval_deadline', 'due_date', 'event_date')}),
        ('Status', {'fields': ('is_active', 'is_published')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('school', 'created_by')


@admin.register(ContributionTier)
class ContributionTierAdmin(admin.ModelAdmin):
    """
    Admin for ContributionTier model
    """
    list_display = ['name', 'event', 'amount', 'is_default', 'created_at']
    list_filter = ['is_default', 'event__event_type', 'created_at']
    search_fields = ['name', 'description', 'event__name']
    ordering = ['event__name', 'name']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description')}),
        ('Relationships', {'fields': ('event',)}),
        ('Financial Information', {'fields': ('amount', 'is_default')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentContribution)
class StudentContributionAdmin(admin.ModelAdmin):
    """
    Admin for StudentContribution model
    """
    list_display = ['student', 'event', 'parent', 'amount_paid', 'amount_required', 'payment_status', 'is_confirmed', 'created_at']
    list_filter = ['payment_status', 'payment_method', 'is_confirmed', 'event__event_type', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'event__name', 'parent__first_name', 'parent__last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Relationships', {'fields': ('event', 'student', 'parent')}),
        ('Payment Information', {'fields': ('amount_paid', 'amount_required', 'payment_status', 'payment_method', 'selected_tier')}),
        ('Payment Details', {'fields': ('transaction_id', 'payment_reference', 'payment_date')}),
        ('Confirmation', {'fields': ('is_confirmed', 'confirmed_by', 'confirmed_at', 'confirmation_notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'amount_remaining', 'payment_percentage']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event', 'student', 'parent', 'confirmed_by')


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    """
    Admin for PaymentReminder model
    """
    list_display = ['parent', 'contribution', 'reminder_type', 'status', 'scheduled_at', 'sent_at', 'created_by']
    list_filter = ['reminder_type', 'status', 'scheduled_at', 'sent_at', 'created_at']
    search_fields = ['parent__first_name', 'parent__last_name', 'contribution__event__name']
    ordering = ['-scheduled_at']
    
    fieldsets = (
        ('Relationships', {'fields': ('contribution', 'parent', 'created_by')}),
        ('Reminder Details', {'fields': ('reminder_type', 'message', 'scheduled_at')}),
        ('Status', {'fields': ('status', 'sent_at', 'delivery_notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('contribution', 'parent', 'created_by')
