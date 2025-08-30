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
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # Relationships
    parents = models.ManyToManyField(User, related_name='children', limit_choices_to={'role': 'parent'})
    groups = models.ManyToManyField(Group, related_name='students')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')
    
    # Contact information
    phone_number = models.CharField(max_length=13, blank=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True)
    
    # Academic information
    admission_date = models.DateField()
    current_class = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_enrolled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['first_name', 'last_name']
    
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
    
    # Dynamic approval and payment configuration
    requires_approval = models.BooleanField(default=True, help_text="Does this event require parent approval?")
    requires_payment = models.BooleanField(default=True, help_text="Does this event require payment?")
    approval_before_payment = models.BooleanField(default=True, help_text="Must approval come before payment?")
    
    # Deadlines
    approval_deadline = models.DateTimeField(blank=True, null=True, help_text="When approval expires")
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
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('other', 'Other'),
    ]
    
    # Relationships
    event = models.ForeignKey(ContributionEvent, on_delete=models.CASCADE, related_name='student_contributions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='contributions')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_contributions')
    
    # Payment information
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    amount_required = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    
    # Tier selection (if applicable)
    selected_tier = models.ForeignKey(ContributionTier, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    # Notes and confirmation
    confirmation_notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='confirmed_contributions',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_contributions'
        verbose_name = 'Student Contribution'
        verbose_name_plural = 'Student Contributions'
        unique_together = ['event', 'student']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.event.name}"
    
    @property
    def amount_remaining(self):
        return self.amount_required - self.amount_paid
    
    @property
    def is_fully_paid(self):
        return self.amount_paid >= self.amount_required
    
    @property
    def payment_percentage(self):
        if self.amount_required > 0:
            return (self.amount_paid / self.amount_required) * 100
        return 0
    
    def confirm_payment(self, confirmed_by_user, notes=''):
        """Confirm the payment"""
        self.is_confirmed = True
        self.confirmed_by = confirmed_by_user
        self.confirmed_at = timezone.now()
        self.confirmation_notes = notes
        self.save()


class PaymentReminder(models.Model):
    """
    Model for tracking payment reminders
    """
    REMINDER_TYPE_CHOICES = [
        ('due_date', 'Due Date'),
        ('overdue', 'Overdue'),
        ('partial', 'Partial Payment'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    # Relationships
    contribution = models.ForeignKey(StudentContribution, on_delete=models.CASCADE, related_name='reminders')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_reminders')
    
    # Reminder details
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    message = models.TextField()
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_notes = models.TextField(blank=True)
    
    # Created by
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_reminders',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_reminders'
        verbose_name = 'Payment Reminder'
        verbose_name_plural = 'Payment Reminders'
        ordering = ['-scheduled_at']
    
    def __str__(self):
        return f"Reminder to {self.parent.full_name} for {self.event.name}"
    
    @property
    def is_delivered(self):
        return self.status in ['sent', 'delivered']
    
    @property
    def is_failed(self):
        return self.status == 'failed'
