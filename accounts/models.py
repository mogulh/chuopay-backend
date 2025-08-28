from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def create_user(self, phone_number, first_name, last_name, role='parent', password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        
        user = self.model(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, first_name, last_name, role='admin', password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(phone_number, first_name, last_name, role, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model with role-based access control
    """
    objects = UserManager()
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
    ]
    
    # Remove username field and use phone number as primary identifier
    username = None
    email = models.EmailField(unique=True, blank=True, null=True)
    
    # Phone number validation for Kenyan format
    phone_regex = RegexValidator(
        regex=r'^\+254\d{9}$',
        message="Phone number must be in format: '+254XXXXXXXXX'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=13,
        unique=True,
        help_text="Phone number in format: +254XXXXXXXXX"
    )
    
    # User role and profile information
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='parent')
    is_phone_verified = models.BooleanField(default=False)
    firebase_uid = models.CharField(max_length=128, unique=True, blank=True, null=True)
    
    # Profile information
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use phone number as username field
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone_number})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_parent(self):
        return self.role == 'parent'


class UserProfile(models.Model):
    """
    Extended user profile information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Additional profile information
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        blank=True
    )
    
    # Address information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=13, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    language_preference = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('sw', 'Swahili'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.full_name}"


class PhoneVerification(models.Model):
    """
    Model for storing phone verification codes
    """
    phone_number = models.CharField(max_length=13)
    verification_code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'phone_verifications'
        verbose_name = 'Phone Verification'
        verbose_name_plural = 'Phone Verifications'
    
    def __str__(self):
        return f"Verification for {self.phone_number}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
