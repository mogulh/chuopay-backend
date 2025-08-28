from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile, PhoneVerification

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin for User model
    """
    model = User
    list_display = ['phone_number', 'first_name', 'last_name', 'role', 'is_phone_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_phone_verified', 'is_active', 'created_at']
    search_fields = ['phone_number', 'first_name', 'last_name', 'email']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'profile_picture')}),
        ('Permissions', {'fields': ('role', 'is_phone_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Firebase', {'fields': ('firebase_uid',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin for UserProfile model
    """
    list_display = ['user', 'gender', 'city', 'county', 'created_at']
    list_filter = ['gender', 'city', 'county', 'language_preference', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone_number', 'city', 'county']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Information', {'fields': ('date_of_birth', 'gender')}),
        ('Address', {'fields': ('address', 'city', 'county')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')}),
        ('Preferences', {'fields': ('notification_preferences', 'language_preference')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    """
    Admin for PhoneVerification model
    """
    list_display = ['phone_number', 'verification_code', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['phone_number']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Verification Details', {'fields': ('phone_number', 'verification_code', 'is_used')}),
        ('Timestamps', {'fields': ('expires_at', 'created_at')}),
    )
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        """
        Only show recent verifications
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Only show verifications from the last 24 hours
        cutoff_time = timezone.now() - timedelta(hours=24)
        return super().get_queryset(request).filter(created_at__gte=cutoff_time)
