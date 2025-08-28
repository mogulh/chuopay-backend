from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class School(models.Model):
    """
    School model for multi-school support
    """
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=13)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    
    # School settings
    currency = models.CharField(max_length=3, default='KES')
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schools'
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
    
    def __str__(self):
        return self.name


class Group(models.Model):
    """
    Group model for organizing students (classes, clubs, etc.)
    """
    GROUP_TYPE_CHOICES = [
        ('class', 'Class'),
        ('club', 'Club'),
        ('sport', 'Sport'),
        ('activity', 'Activity'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPE_CHOICES, default='class')
    
    # School relationship
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='groups')
    
    # Teacher assignment (optional)
    teacher = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_groups',
        limit_choices_to={'role': 'teacher'}
    )
    
    # Group settings
    is_active = models.BooleanField(default=True)
    max_students = models.PositiveIntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'groups'
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        unique_together = ['name', 'school']
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"
    
    @property
    def student_count(self):
        return self.students.count()


class Student(models.Model):
    """
    Student model linked to parents and groups
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    # Basic information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # School and group relationships
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')
    groups = models.ManyToManyField(Group, through='StudentGroup', related_name='students')
    
    # Parent relationships (many-to-many)
    parents = models.ManyToManyField(User, through='StudentParent', related_name='children')
    
    # Student information
    student_id = models.CharField(max_length=50, unique=True, help_text="School's internal student ID")
    admission_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Contact information
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=13, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Medical information
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class StudentGroup(models.Model):
    """
    Through model for Student-Group relationship with additional fields
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    # Relationship details
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Academic information
    academic_year = models.CharField(max_length=9, help_text="Format: 2023-2024")
    term = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_groups'
        verbose_name = 'Student Group'
        verbose_name_plural = 'Student Groups'
        unique_together = ['student', 'group', 'academic_year']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.group.name}"


class StudentParent(models.Model):
    """
    Through model for Student-Parent relationship with additional fields
    """
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('grandparent', 'Grandparent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Relationship details
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    is_primary_contact = models.BooleanField(default=False)
    is_emergency_contact = models.BooleanField(default=False)
    
    # Contact preferences
    receives_notifications = models.BooleanField(default=True)
    receives_sms = models.BooleanField(default=True)
    receives_email = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_parents'
        verbose_name = 'Student Parent'
        verbose_name_plural = 'Student Parents'
        unique_together = ['student', 'parent']
    
    def __str__(self):
        return f"{self.parent.full_name} - {self.student.full_name} ({self.relationship})"


class ContributionEvent(models.Model):
    """
    Contribution event model for managing payment requests
    """
    EVENT_TYPE_CHOICES = [
        ('field_trip', 'Field Trip'),
        ('fundraiser', 'Fundraiser'),
        ('uniform', 'Uniform'),
        ('textbook', 'Textbook'),
        ('activity', 'Activity'),
        ('exam', 'Exam'),
        ('other', 'Other'),
    ]
    
    PARTICIPATION_CHOICES = [
        ('mandatory', 'Mandatory'),
        ('optional', 'Optional'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    
    # School and group relationships
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='contribution_events')
    groups = models.ManyToManyField(Group, related_name='contribution_events')
    
    # Financial information
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='KES')
    
    # Optional tiers (e.g., with/without snacks)
    has_tiers = models.BooleanField(default=False)
    
    # Participation rules
    participation_type = models.CharField(max_length=20, choices=PARTICIPATION_CHOICES, default='mandatory')
    
    # Dates
    due_date = models.DateTimeField()
    event_date = models.DateTimeField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    
    # Created by
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_events',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contribution_events'
        verbose_name = 'Contribution Event'
        verbose_name_plural = 'Contribution Events'
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"
    
    @property
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    @property
    def days_until_due(self):
        delta = self.due_date - timezone.now()
        return delta.days


class ContributionTier(models.Model):
    """
    Optional tiers for contribution events (e.g., with/without snacks)
    """
    event = models.ForeignKey(ContributionEvent, on_delete=models.CASCADE, related_name='tiers')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contribution_tiers'
        verbose_name = 'Contribution Tier'
        verbose_name_plural = 'Contribution Tiers'
        unique_together = ['event', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.event.name}"


class StudentContribution(models.Model):
    """
    Model for tracking individual student contributions
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('confirmed', 'Confirmed'),  # Added for manual confirmation
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='contributions')
    event = models.ForeignKey(ContributionEvent, on_delete=models.CASCADE, related_name='student_contributions')
    tier = models.ForeignKey(ContributionTier, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment information
    amount_required = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment details
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Manual confirmation fields
    confirmed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='confirmed_contributions',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    confirmed_at = models.DateTimeField(blank=True, null=True)
    confirmation_notes = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Updated by
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='updated_contributions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_contributions'
        verbose_name = 'Student Contribution'
        verbose_name_plural = 'Student Contributions'
        unique_together = ['student', 'event']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.event.name}"
    
    @property
    def amount_remaining(self):
        return self.amount_required - self.amount_paid
    
    @property
    def payment_percentage(self):
        if self.amount_required > 0:
            return (self.amount_paid / self.amount_required) * 100
        return 0
    
    def update_payment_status(self):
        """Update payment status based on amounts and confirmation"""
        if self.confirmed_by and self.confirmed_at:
            self.payment_status = 'confirmed'
        elif self.amount_paid >= self.amount_required:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        elif self.event.is_overdue:
            self.payment_status = 'overdue'
        else:
            self.payment_status = 'pending'
        self.save()
    
    def confirm_payment(self, confirmed_by, notes=''):
        """Manually confirm a payment"""
        self.confirmed_by = confirmed_by
        self.confirmed_at = timezone.now()
        self.confirmation_notes = notes
        self.payment_status = 'confirmed'
        self.save()
    
    def get_payment_history(self):
        """Get all payment transactions for this contribution"""
        return self.payment_history.all().order_by('-payment_date')


class PaymentHistory(models.Model):
    """
    Model for tracking individual payment transactions
    """
    PAYMENT_METHOD_CHOICES = [
        ('mpesa_stk', 'MPESA STK Push'),
        ('mpesa_ussd', 'MPESA USSD'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash Payment'),
        ('manual', 'Manual Entry'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Related contribution
    contribution = models.ForeignKey(
        StudentContribution, 
        on_delete=models.CASCADE, 
        related_name='payment_history'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment metadata
    payment_date = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # External service information
    external_id = models.CharField(max_length=100, blank=True)
    external_status = models.CharField(max_length=50, blank=True)
    external_response = models.JSONField(blank=True, null=True)
    
    # Notes and metadata
    notes = models.TextField(blank=True)
    metadata = models.JSONField(blank=True, null=True)
    
    # Created by
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='payment_transactions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_history'
        verbose_name = 'Payment History'
        verbose_name_plural = 'Payment History'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.contribution.student.full_name} - {self.amount} ({self.payment_method})"
    
    def save(self, *args, **kwargs):
        """Override save to update contribution amounts"""
        is_new = self.pk is None
        old_amount = 0
        
        if not is_new:
            try:
                old_payment = PaymentHistory.objects.get(pk=self.pk)
                old_amount = old_payment.amount
            except PaymentHistory.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Update contribution amounts
        contribution = self.contribution
        if is_new and self.status == 'completed':
            contribution.amount_paid += self.amount
        elif not is_new and self.status == 'completed':
            contribution.amount_paid = contribution.amount_paid - old_amount + self.amount
        
        contribution.update_payment_status()
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'cancelled']


class ReminderLog(models.Model):
    """
    Model for tracking reminder notifications
    """
    REMINDER_TYPE_CHOICES = [
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
    ]
    
    # Recipient information
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reminders')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    event = models.ForeignKey(ContributionEvent, on_delete=models.CASCADE, related_name='reminders')
    
    # Reminder details
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Delivery information
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivery_error = models.TextField(blank=True)
    
    # External service information
    external_id = models.CharField(max_length=100, blank=True)
    external_status = models.CharField(max_length=50, blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_reminders',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reminder_logs'
        verbose_name = 'Reminder Log'
        verbose_name_plural = 'Reminder Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reminder to {self.parent.full_name} for {self.event.name}"
    
    @property
    def is_delivered(self):
        return self.status in ['sent', 'delivered']
    
    @property
    def is_failed(self):
        return self.status == 'failed'
