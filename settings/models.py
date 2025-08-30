from django.db import models
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
import json

User = get_user_model()

class SystemSettings(models.Model):
    """
    Global system-wide settings
    """
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('float', 'Float'),
    ]
    
    key = models.CharField(max_length=100, unique=True, help_text="Setting key (e.g., 'maintenance_mode')")
    value = models.TextField(help_text="Setting value")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True, help_text="Description of what this setting controls")
    is_public = models.BooleanField(default=False, help_text="Whether this setting can be read by non-admin users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_system_settings')
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    def get_value(self):
        """Get the typed value based on setting_type"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'json':
            return json.loads(self.value)
        else:
            return self.value
    
    def set_value(self, value):
        """Set the value with proper type conversion"""
        if self.setting_type == 'json' and not isinstance(value, str):
            self.value = json.dumps(value)
        else:
            self.value = str(value)
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value with caching"""
        cache_key = f'system_setting_{key}'
        value = cache.get(cache_key)
        
        if value is None:
            try:
                setting = cls.objects.get(key=key)
                value = setting.get_value()
                cache.set(cache_key, value, 300)  # Cache for 5 minutes
            except cls.DoesNotExist:
                value = default
                cache.set(cache_key, value, 300)
        
        return value
    
    @classmethod
    def set_setting(cls, key, value, setting_type='string', description='', is_public=False, user=None):
        """Set a setting value"""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'setting_type': setting_type,
                'description': description,
                'is_public': is_public,
                'updated_by': user
            }
        )
        
        setting.set_value(value)
        setting.updated_by = user
        setting.save()
        
        # Clear cache
        cache.delete(f'system_setting_{key}')
        
        return setting


class SchoolSettings(models.Model):
    """
    School-specific settings
    """
    school = models.ForeignKey('contributions.School', on_delete=models.CASCADE, related_name='settings')
    key = models.CharField(max_length=100, help_text="Setting key")
    value = models.TextField(help_text="Setting value")
    setting_type = models.CharField(max_length=20, choices=SystemSettings.SETTING_TYPES, default='string')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'school_settings'
        verbose_name = 'School Setting'
        verbose_name_plural = 'School Settings'
        unique_together = ['school', 'key']
        ordering = ['school', 'key']
    
    def __str__(self):
        return f"{self.school.name} - {self.key}: {self.value}"
    
    def get_value(self):
        """Get the typed value based on setting_type"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'json':
            return json.loads(self.value)
        else:
            return self.value
    
    def set_value(self, value):
        """Set the value with proper type conversion"""
        if self.setting_type == 'json' and not isinstance(value, str):
            self.value = json.dumps(value)
        else:
            self.value = str(value)


class FeatureFlag(models.Model):
    """
    Feature flags for enabling/disabling features
    """
    FLAG_TYPES = [
        ('boolean', 'Boolean'),
        ('percentage', 'Percentage'),
        ('user_list', 'User List'),
    ]
    
    name = models.CharField(max_length=100, unique=True, help_text="Feature flag name")
    description = models.TextField(help_text="Description of what this feature flag controls")
    flag_type = models.CharField(max_length=20, choices=FLAG_TYPES, default='boolean')
    is_enabled = models.BooleanField(default=False, help_text="Whether the feature is enabled")
    percentage = models.IntegerField(default=0, help_text="Percentage of users who should see this feature (0-100)")
    enabled_users = models.ManyToManyField(User, blank=True, related_name='enabled_features')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'feature_flags'
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({'Enabled' if self.is_enabled else 'Disabled'})"
    
    def is_enabled_for_user(self, user):
        """Check if feature is enabled for a specific user"""
        if not self.is_enabled:
            return False
        
        if self.flag_type == 'boolean':
            return self.is_enabled
        elif self.flag_type == 'percentage':
            # Simple hash-based percentage check
            user_hash = hash(f"{user.id}_{self.name}") % 100
            return user_hash < self.percentage
        elif self.flag_type == 'user_list':
            return user in self.enabled_users.all()
        
        return False


class UserPreferences(models.Model):
    """
    User-specific preferences and settings
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # UI/UX Preferences
    theme = models.CharField(max_length=20, choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ], default='auto')
    language = models.CharField(max_length=10, default='en', help_text="Language code (e.g., 'en', 'sw')")
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Notification Preferences (extends notification settings)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    
    # Dashboard Preferences
    dashboard_layout = models.JSONField(default=dict, help_text="Dashboard widget layout")
    default_view = models.CharField(max_length=50, default='overview', help_text="Default dashboard view")
    
    # Privacy Settings
    profile_visibility = models.CharField(max_length=20, choices=[
        ('public', 'Public'),
        ('private', 'Private'),
        ('school_only', 'School Only'),
    ], default='school_only')
    
    # Payment Preferences
    default_payment_method = models.CharField(max_length=50, blank=True, help_text="Default payment method preference")
    auto_pay_enabled = models.BooleanField(default=False, help_text="Enable automatic payments")
    
    # Security Settings
    two_factor_enabled = models.BooleanField(default=False)
    session_timeout = models.IntegerField(default=30, help_text="Session timeout in minutes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.full_name}"


class AppConfiguration(models.Model):
    """
    Application configuration settings
    """
    CONFIG_CATEGORIES = [
        ('general', 'General'),
        ('security', 'Security'),
        ('payment', 'Payment'),
        ('notification', 'Notification'),
        ('approval', 'Approval'),
        ('analytics', 'Analytics'),
        ('integration', 'Integration'),
    ]
    
    category = models.CharField(max_length=20, choices=CONFIG_CATEGORIES, default='general')
    key = models.CharField(max_length=100, help_text="Configuration key")
    value = models.TextField(help_text="Configuration value")
    setting_type = models.CharField(max_length=20, choices=SystemSettings.SETTING_TYPES, default='string')
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False, help_text="Whether this configuration is required")
    is_sensitive = models.BooleanField(default=False, help_text="Whether this contains sensitive data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'app_configurations'
        verbose_name = 'App Configuration'
        verbose_name_plural = 'App Configurations'
        unique_together = ['category', 'key']
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.category} - {self.key}: {self.value}"
    
    def get_value(self):
        """Get the typed value based on setting_type"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'json':
            return json.loads(self.value)
        else:
            return self.value
    
    def set_value(self, value):
        """Set the value with proper type conversion"""
        if self.setting_type == 'json' and not isinstance(value, str):
            self.value = json.dumps(value)
        else:
            self.value = str(value)
