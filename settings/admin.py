from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SystemSettings, SchoolSettings, FeatureFlag, 
    UserPreferences, AppConfiguration
)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'typed_value', 'setting_type', 'is_public', 'updated_by', 'updated_at']
    list_filter = ['setting_type', 'is_public', 'created_at', 'updated_at']
    search_fields = ['key', 'description', 'value']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['key']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'value', 'setting_type', 'description')
        }),
        ('Access Control', {
            'fields': ('is_public',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def typed_value(self, obj):
        """Display the typed value"""
        try:
            value = obj.get_value()
            if isinstance(value, bool):
                return format_html(
                    '<span style="color: {};">{}</span>',
                    'green' if value else 'red',
                    '✓' if value else '✗'
                )
            elif isinstance(value, (dict, list)):
                return format_html('<code>{}</code>', str(value)[:50] + '...' if len(str(value)) > 50 else str(value))
            else:
                return str(value)
        except:
            return format_html('<span style="color: red;">Error</span>')
    
    typed_value.short_description = 'Value'


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = ['school', 'key', 'typed_value', 'setting_type', 'updated_by', 'updated_at']
    list_filter = ['school', 'setting_type', 'created_at', 'updated_at']
    search_fields = ['key', 'description', 'value', 'school__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['school__name', 'key']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('school', 'key', 'value', 'setting_type', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def typed_value(self, obj):
        """Display the typed value"""
        try:
            value = obj.get_value()
            if isinstance(value, bool):
                return format_html(
                    '<span style="color: {};">{}</span>',
                    'green' if value else 'red',
                    '✓' if value else '✗'
                )
            elif isinstance(value, (dict, list)):
                return format_html('<code>{}</code>', str(value)[:50] + '...' if len(str(value)) > 50 else str(value))
            else:
                return str(value)
        except:
            return format_html('<span style="color: red;">Error</span>')
    
    typed_value.short_description = 'Value'


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['name', 'flag_type', 'is_enabled', 'percentage', 'enabled_users_count', 'updated_by', 'updated_at']
    list_filter = ['flag_type', 'is_enabled', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    filter_horizontal = ['enabled_users']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'flag_type', 'is_enabled')
        }),
        ('Configuration', {
            'fields': ('percentage', 'enabled_users'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def enabled_users_count(self, obj):
        """Display count of enabled users"""
        count = obj.enabled_users.count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'gray',
            count
        )
    
    enabled_users_count.short_description = 'Enabled Users'


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'language', 'timezone', 'two_factor_enabled', 'updated_at']
    list_filter = ['theme', 'language', 'two_factor_enabled', 'auto_pay_enabled', 'created_at', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['user__first_name', 'user__last_name']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('UI/UX Preferences', {
            'fields': ('theme', 'language', 'timezone')
        }),
        ('Notification Preferences', {
            'fields': (
                'email_notifications', 'sms_notifications', 
                'push_notifications', 'in_app_notifications'
            )
        }),
        ('Dashboard Preferences', {
            'fields': ('dashboard_layout', 'default_view'),
            'classes': ('collapse',)
        }),
        ('Privacy & Security', {
            'fields': ('profile_visibility', 'two_factor_enabled', 'session_timeout')
        }),
        ('Payment Preferences', {
            'fields': ('default_payment_method', 'auto_pay_enabled'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AppConfiguration)
class AppConfigurationAdmin(admin.ModelAdmin):
    list_display = ['category', 'key', 'typed_value', 'setting_type', 'is_required', 'is_sensitive', 'updated_by', 'updated_at']
    list_filter = ['category', 'setting_type', 'is_required', 'is_sensitive', 'created_at', 'updated_at']
    search_fields = ['key', 'description', 'value']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['category', 'key']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'key', 'value', 'setting_type', 'description')
        }),
        ('Security', {
            'fields': ('is_required', 'is_sensitive')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def typed_value(self, obj):
        """Display the typed value"""
        try:
            value = obj.get_value()
            if obj.is_sensitive:
                return format_html('<span style="color: red;">***HIDDEN***</span>')
            elif isinstance(value, bool):
                return format_html(
                    '<span style="color: {};">{}</span>',
                    'green' if value else 'red',
                    '✓' if value else '✗'
                )
            elif isinstance(value, (dict, list)):
                return format_html('<code>{}</code>', str(value)[:50] + '...' if len(str(value)) > 50 else str(value))
            else:
                return str(value)
        except:
            return format_html('<span style="color: red;">Error</span>')
    
    typed_value.short_description = 'Value'
