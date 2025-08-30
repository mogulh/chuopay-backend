from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SystemSettings, SchoolSettings, FeatureFlag, 
    UserPreferences, AppConfiguration
)
from contributions.models import School

User = get_user_model()

class SystemSettingsSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    class Meta:
        model = SystemSettings
        fields = [
            'id', 'key', 'value', 'typed_value', 'setting_type', 'description',
            'is_public', 'created_at', 'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        return obj.get_value()
    
    def validate_key(self, value):
        """Validate setting key format"""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Key must contain only letters, numbers, underscores, and hyphens")
        return value.lower()


class SchoolSettingsSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    school_name = serializers.CharField(source='school.name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    class Meta:
        model = SchoolSettings
        fields = [
            'id', 'school', 'school_name', 'key', 'value', 'typed_value',
            'setting_type', 'description', 'created_at', 'updated_at',
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        return obj.get_value()
    
    def validate_key(self, value):
        """Validate setting key format"""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Key must contain only letters, numbers, underscores, and hyphens")
        return value.lower()


class FeatureFlagSerializer(serializers.ModelSerializer):
    enabled_users_count = serializers.SerializerMethodField()
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    class Meta:
        model = FeatureFlag
        fields = [
            'id', 'name', 'description', 'flag_type', 'is_enabled',
            'percentage', 'enabled_users_count', 'created_at', 'updated_at',
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_enabled_users_count(self, obj):
        return obj.enabled_users.count()
    
    def validate_percentage(self, value):
        """Validate percentage is between 0 and 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Percentage must be between 0 and 100")
        return value


class FeatureFlagDetailSerializer(FeatureFlagSerializer):
    """Detailed serializer that includes enabled users"""
    enabled_users = serializers.SerializerMethodField()
    
    class Meta(FeatureFlagSerializer.Meta):
        fields = FeatureFlagSerializer.Meta.fields + ['enabled_users']
    
    def get_enabled_users(self, obj):
        return [
            {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'phone_number': user.phone_number
            }
            for user in obj.enabled_users.all()
        ]


class UserPreferencesSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserPreferences
        fields = [
            'id', 'user', 'user_name', 'theme', 'language', 'timezone',
            'email_notifications', 'sms_notifications', 'push_notifications',
            'in_app_notifications', 'dashboard_layout', 'default_view',
            'profile_visibility', 'default_payment_method', 'auto_pay_enabled',
            'two_factor_enabled', 'session_timeout', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate_session_timeout(self, value):
        """Validate session timeout is reasonable"""
        if value < 5 or value > 1440:  # 5 minutes to 24 hours
            raise serializers.ValidationError("Session timeout must be between 5 and 1440 minutes")
        return value
    
    def validate_dashboard_layout(self, value):
        """Validate dashboard layout is valid JSON"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Dashboard layout must be a valid JSON object")
        return value


class AppConfigurationSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    class Meta:
        model = AppConfiguration
        fields = [
            'id', 'category', 'key', 'value', 'typed_value', 'setting_type',
            'description', 'is_required', 'is_sensitive', 'created_at',
            'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        return obj.get_value()
    
    def validate_key(self, value):
        """Validate configuration key format"""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Key must contain only letters, numbers, underscores, and hyphens")
        return value.lower()


# Bulk operation serializers
class BulkSystemSettingsSerializer(serializers.Serializer):
    settings = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of settings to update"
    )
    
    def validate_settings(self, value):
        """Validate bulk settings data"""
        for setting in value:
            if 'key' not in setting:
                raise serializers.ValidationError("Each setting must have a 'key' field")
            if 'value' not in setting:
                raise serializers.ValidationError("Each setting must have a 'value' field")
        return value


class BulkSchoolSettingsSerializer(serializers.Serializer):
    school_id = serializers.IntegerField(help_text="School ID")
    settings = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of settings to update"
    )
    
    def validate_school_id(self, value):
        """Validate school exists"""
        try:
            School.objects.get(id=value)
        except School.DoesNotExist:
            raise serializers.ValidationError("School does not exist")
        return value
    
    def validate_settings(self, value):
        """Validate bulk settings data"""
        for setting in value:
            if 'key' not in setting:
                raise serializers.ValidationError("Each setting must have a 'key' field")
            if 'value' not in setting:
                raise serializers.ValidationError("Each setting must have a 'value' field")
        return value


# Response serializers for specific endpoints
class SettingsSummarySerializer(serializers.Serializer):
    """Summary of all settings for dashboard"""
    system_settings_count = serializers.IntegerField()
    school_settings_count = serializers.IntegerField()
    feature_flags_count = serializers.IntegerField()
    active_feature_flags_count = serializers.IntegerField()
    configurations_count = serializers.IntegerField()


class FeatureFlagStatusSerializer(serializers.Serializer):
    """Feature flag status for a specific user"""
    name = serializers.CharField()
    is_enabled = serializers.BooleanField()
    is_enabled_for_user = serializers.BooleanField()
    flag_type = serializers.CharField()
    percentage = serializers.IntegerField(required=False)


class UserSettingsSummarySerializer(serializers.Serializer):
    """Summary of user's settings and preferences"""
    preferences = UserPreferencesSerializer()
    enabled_features = serializers.ListField(child=serializers.CharField())
    notification_settings = serializers.DictField()
