from rest_framework import serializers
from .models import (
    NotificationTemplate, NotificationSchedule, NotificationLog,
    SMSCredits, NotificationSettings
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'content',
            'variables', 'is_active', 'max_length', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NotificationScheduleSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = NotificationSchedule
        fields = [
            'id', 'name', 'description', 'schedule_type', 'scheduled_time',
            'recurring_type', 'recurring_interval', 'template', 'template_name',
            'event_types', 'payment_statuses', 'days_before_due', 'is_active',
            'last_run', 'next_run', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['last_run', 'next_run', 'created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'recipient', 'recipient_name', 'student', 'student_name',
            'event', 'event_name', 'notification_type', 'template', 'template_name',
            'subject', 'message', 'status', 'sent_at', 'delivered_at',
            'external_id', 'external_status', 'delivery_error', 'cost', 'currency',
            'schedule', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'sent_at', 'delivered_at', 'external_id', 'external_status',
            'delivery_error', 'created_at', 'updated_at'
        ]


class SMSCreditsSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = SMSCredits
        fields = [
            'id', 'amount', 'credit_type', 'cost', 'currency', 'provider',
            'transaction_id', 'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['created_at']


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'receives_notifications', 'receives_sms', 'receives_email',
            'receives_push', 'receives_in_app', 'payment_reminders',
            'event_updates', 'general_announcements', 'quiet_hours_start',
            'quiet_hours_end', 'max_notifications_per_day', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# Additional serializers for API responses
class StudentReminderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    student_id = serializers.CharField()
    parent_name = serializers.CharField()
    parent_phone = serializers.CharField()
    payment_status = serializers.CharField()
    contribution_count = serializers.IntegerField()


class ReminderRequestSerializer(serializers.Serializer):
    students = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of student IDs to send reminders to"
    )
    message = serializers.CharField(
        max_length=160,
        help_text="SMS message content (max 160 characters)"
    )
    reminder_type = serializers.ChoiceField(
        choices=['payment', 'upcoming', 'overdue'],
        default='payment',
        help_text="Type of reminder to send"
    )


class ReminderResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    result = serializers.DictField() 