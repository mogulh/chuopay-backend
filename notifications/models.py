from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class NotificationTemplate(models.Model):
    """
    Template for notifications (SMS, Email, Push)
    """
    TEMPLATE_TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    subject = models.CharField(max_length=200, blank=True)  # For email
    content = models.TextField(help_text="Template content with placeholders like {student_name}, {event_name}, etc.")
    
    # Template variables
    variables = models.JSONField(default=dict, blank=True, help_text="Available variables for this template")
    
    # Settings
    is_active = models.BooleanField(default=True)
    max_length = models.PositiveIntegerField(blank=True, null=True, help_text="Maximum length for SMS")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        unique_together = ['name', 'template_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class NotificationSchedule(models.Model):
    """
    Schedule for sending notifications
    """
    SCHEDULE_TYPE_CHOICES = [
        ('immediate', 'Immediate'),
        ('scheduled', 'Scheduled'),
        ('recurring', 'Recurring'),
    ]
    
    RECURRING_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Schedule settings
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='immediate')
    scheduled_time = models.DateTimeField(blank=True, null=True)
    recurring_type = models.CharField(max_length=20, choices=RECURRING_CHOICES, blank=True)
    recurring_interval = models.PositiveIntegerField(default=1, help_text="Every X days/weeks/months")
    
    # Template and recipients
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='schedules')
    
    # Filter criteria
    event_types = models.JSONField(default=list, blank=True)
    payment_statuses = models.JSONField(default=list, blank=True)
    days_before_due = models.PositiveIntegerField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)
    
    # Created by
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_schedules',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_schedules'
        verbose_name = 'Notification Schedule'
        verbose_name_plural = 'Notification Schedules'
    
    def __str__(self):
        return f"{self.name} ({self.get_schedule_type_display()})"


class NotificationLog(models.Model):
    """
    Log of all notifications sent
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Recipient information
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    student = models.ForeignKey('contributions.Student', on_delete=models.CASCADE, related_name='notifications')
    event = models.ForeignKey('contributions.ContributionEvent', on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    # Status and delivery
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    # External service information
    external_id = models.CharField(max_length=100, blank=True)
    external_status = models.CharField(max_length=50, blank=True)
    delivery_error = models.TextField(blank=True)
    
    # Cost tracking (for SMS)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default='KES')
    
    # Schedule information
    schedule = models.ForeignKey(NotificationSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_notifications',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_logs'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type.upper()} to {self.recipient.full_name} - {self.status}"
    
    @property
    def is_delivered(self):
        return self.status in ['sent', 'delivered']
    
    @property
    def is_failed(self):
        return self.status == 'failed'
    
    @property
    def delivery_time(self):
        if self.sent_at and self.delivered_at:
            return self.delivered_at - self.sent_at
        return None


class SMSCredits(models.Model):
    """
    Track SMS credits for billing
    """
    CREDIT_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('usage', 'Usage'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus'),
    ]
    
    amount = models.IntegerField(help_text="Number of SMS credits")
    credit_type = models.CharField(max_length=20, choices=CREDIT_TYPE_CHOICES)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    
    # Provider information
    provider = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='credit_transactions',
        limit_choices_to={'role': 'admin'}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sms_credits'
        verbose_name = 'SMS Credits'
        verbose_name_plural = 'SMS Credits'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.credit_type} - {self.amount} credits ({self.cost} {self.currency})"


class NotificationSettings(models.Model):
    """
    User notification preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    # General preferences
    receives_notifications = models.BooleanField(default=True)
    receives_sms = models.BooleanField(default=True)
    receives_email = models.BooleanField(default=False)
    receives_push = models.BooleanField(default=True)
    receives_in_app = models.BooleanField(default=True)
    
    # Specific notification types
    payment_reminders = models.BooleanField(default=True)
    event_updates = models.BooleanField(default=True)
    general_announcements = models.BooleanField(default=True)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    
    # Frequency preferences
    max_notifications_per_day = models.PositiveIntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_settings'
        verbose_name = 'Notification Settings'
        verbose_name_plural = 'Notification Settings'
    
    def __str__(self):
        return f"Settings for {self.user.full_name}"
    
    @property
    def is_in_quiet_hours(self):
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:  # Quiet hours span midnight
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end
