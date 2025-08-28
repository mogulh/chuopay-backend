from django.db import models


class Indexes:
    """
    Database indexes for performance optimization
    """
    
    # Student indexes
    class StudentIndexes:
        student_id = models.Index(fields=['student_id'], name='idx_student_student_id')
        school_active = models.Index(fields=['school', 'is_active'], name='idx_student_school_active')
        admission_date = models.Index(fields=['admission_date'], name='idx_student_admission_date')
    
    # Group indexes
    class GroupIndexes:
        school_type = models.Index(fields=['school', 'group_type'], name='idx_group_school_type')
        teacher_active = models.Index(fields=['teacher', 'is_active'], name='idx_group_teacher_active')
    
    # StudentGroup indexes
    class StudentGroupIndexes:
        student_group = models.Index(fields=['student', 'group'], name='idx_studentgroup_student_group')
        academic_year = models.Index(fields=['academic_year'], name='idx_studentgroup_academic_year')
        active_year = models.Index(fields=['is_active', 'academic_year'], name='idx_studentgroup_active_year')
    
    # StudentParent indexes
    class StudentParentIndexes:
        student_parent = models.Index(fields=['student', 'parent'], name='idx_studentparent_student_parent')
        relationship = models.Index(fields=['relationship'], name='idx_studentparent_relationship')
        primary_contact = models.Index(fields=['is_primary_contact'], name='idx_studentparent_primary')
    
    # ContributionEvent indexes
    class ContributionEventIndexes:
        school_active = models.Index(fields=['school', 'is_active'], name='idx_event_school_active')
        due_date = models.Index(fields=['due_date'], name='idx_event_due_date')
        event_type = models.Index(fields=['event_type'], name='idx_event_type')
        published_active = models.Index(fields=['is_published', 'is_active'], name='idx_event_published_active')
    
    # StudentContribution indexes
    class StudentContributionIndexes:
        student_event = models.Index(fields=['student', 'event'], name='idx_contribution_student_event')
        payment_status = models.Index(fields=['payment_status'], name='idx_contribution_payment_status')
        event_status = models.Index(fields=['event', 'payment_status'], name='idx_contribution_event_status')
        payment_date = models.Index(fields=['payment_date'], name='idx_contribution_payment_date')
    
    # ReminderLog indexes
    class ReminderLogIndexes:
        recipient_status = models.Index(fields=['recipient', 'status'], name='idx_reminder_recipient_status')
        event_status = models.Index(fields=['event', 'status'], name='idx_reminder_event_status')
        sent_date = models.Index(fields=['sent_at'], name='idx_reminder_sent_date')
        notification_type = models.Index(fields=['notification_type'], name='idx_reminder_type')
    
    # NotificationLog indexes
    class NotificationLogIndexes:
        recipient_type = models.Index(fields=['recipient', 'notification_type'], name='idx_notification_recipient_type')
        status_date = models.Index(fields=['status', 'created_at'], name='idx_notification_status_date')
        external_id = models.Index(fields=['external_id'], name='idx_notification_external_id')
    
    # NotificationSchedule indexes
    class NotificationScheduleIndexes:
        active_next_run = models.Index(fields=['is_active', 'next_run'], name='idx_schedule_active_next')
        schedule_type = models.Index(fields=['schedule_type'], name='idx_schedule_type')
    
    # User indexes (from accounts app)
    class UserIndexes:
        phone_number = models.Index(fields=['phone_number'], name='idx_user_phone')
        role_active = models.Index(fields=['role', 'is_active'], name='idx_user_role_active')
        firebase_uid = models.Index(fields=['firebase_uid'], name='idx_user_firebase_uid') 