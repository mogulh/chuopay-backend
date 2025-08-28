from django.contrib import admin
from .models import (
    NotificationTemplate, NotificationSchedule, NotificationLog,
    SMSCredits, NotificationSettings
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """
    Admin for NotificationTemplate model
    """
    list_display = ['name', 'template_type', 'is_active', 'max_length', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'content', 'subject']
    ordering = ['template_type', 'name']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'template_type', 'subject', 'content')}),
        ('Settings', {'fields': ('is_active', 'max_length')}),
        ('Variables', {'fields': ('variables',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationSchedule)
class NotificationScheduleAdmin(admin.ModelAdmin):
    """
    Admin for NotificationSchedule model
    """
    list_display = ['name', 'schedule_type', 'template', 'is_active', 'last_run', 'next_run', 'created_at']
    list_filter = ['schedule_type', 'is_active', 'recurring_type', 'created_at']
    search_fields = ['name', 'description', 'template__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description')}),
        ('Schedule Settings', {'fields': ('schedule_type', 'scheduled_time', 'recurring_type', 'recurring_interval')}),
        ('Template and Filters', {'fields': ('template', 'event_types', 'payment_statuses', 'days_before_due')}),
        ('Status', {'fields': ('is_active', 'last_run', 'next_run')}),
        ('Created By', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_run', 'next_run']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'created_by')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """
    Admin for NotificationLog model
    """
    list_display = ['recipient', 'notification_type', 'status', 'sent_at', 'cost', 'created_at']
    list_filter = ['notification_type', 'status', 'created_at', 'sent_at']
    search_fields = ['recipient__first_name', 'recipient__last_name', 'student__first_name', 'student__last_name', 'event__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Recipients', {'fields': ('recipient', 'student', 'event')}),
        ('Notification Details', {'fields': ('notification_type', 'template', 'subject', 'message')}),
        ('Status and Delivery', {'fields': ('status', 'sent_at', 'delivered_at', 'delivery_error')}),
        ('External Service', {'fields': ('external_id', 'external_status')}),
        ('Cost Tracking', {'fields': ('cost', 'currency')}),
        ('Schedule', {'fields': ('schedule',)}),
        ('Created By', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'delivery_time']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipient', 'student', 'event', 'template', 'schedule', 'created_by'
        )


@admin.register(SMSCredits)
class SMSCreditsAdmin(admin.ModelAdmin):
    """
    Admin for SMSCredits model
    """
    list_display = ['credit_type', 'amount', 'cost', 'currency', 'provider', 'created_by', 'created_at']
    list_filter = ['credit_type', 'currency', 'provider', 'created_at']
    search_fields = ['transaction_id', 'notes', 'created_by__first_name', 'created_by__last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Details', {'fields': ('amount', 'credit_type', 'cost', 'currency')}),
        ('Provider Information', {'fields': ('provider', 'transaction_id')}),
        ('Notes', {'fields': ('notes',)}),
        ('Created By', {'fields': ('created_by',)}),
        ('Timestamp', {'fields': ('created_at',)}),
    )
    
    readonly_fields = ['created_at']


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """
    Admin for NotificationSettings model
    """
    list_display = ['user', 'receives_notifications', 'receives_sms', 'receives_email', 'receives_push', 'created_at']
    list_filter = ['receives_notifications', 'receives_sms', 'receives_email', 'receives_push', 'payment_reminders', 'event_updates', 'general_announcements', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone_number']
    ordering = ['user__first_name']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('General Preferences', {'fields': ('receives_notifications', 'receives_sms', 'receives_email', 'receives_push', 'receives_in_app')}),
        ('Specific Notifications', {'fields': ('payment_reminders', 'event_updates', 'general_announcements')}),
        ('Timing Preferences', {'fields': ('quiet_hours_start', 'quiet_hours_end')}),
        ('Frequency Preferences', {'fields': ('max_notifications_per_day',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
