from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from settings.models import SystemSettings, AppConfiguration, FeatureFlag
from notifications.models import NotificationSettings

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize default system settings and configurations'

    def handle(self, *args, **options):
        self.stdout.write('Initializing default settings...')
        
        # Create default system settings
        system_settings = [
            {
                'key': 'maintenance_mode',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Enable maintenance mode for the entire system',
                'is_public': True
            },
            {
                'key': 'max_file_size_mb',
                'value': '10',
                'setting_type': 'integer',
                'description': 'Maximum file upload size in MB',
                'is_public': True
            },
            {
                'key': 'session_timeout_minutes',
                'value': '30',
                'setting_type': 'integer',
                'description': 'Default session timeout in minutes',
                'is_public': True
            },
            {
                'key': 'default_currency',
                'value': 'KES',
                'setting_type': 'string',
                'description': 'Default currency for the system',
                'is_public': True
            },
            {
                'key': 'approval_required_by_default',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Whether events require approval by default',
                'is_public': True
            },
            {
                'key': 'payment_required_by_default',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Whether events require payment by default',
                'is_public': True
            },
            {
                'key': 'sms_enabled',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Enable SMS notifications',
                'is_public': True
            },
            {
                'key': 'email_enabled',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Enable email notifications',
                'is_public': True
            },
            {
                'key': 'push_notifications_enabled',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Enable push notifications',
                'is_public': True
            },
            {
                'key': 'auto_approval_enabled',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Enable automatic approval for certain events',
                'is_public': True
            },
            {
                'key': 'payment_reminder_days',
                'value': '[3, 7, 14]',
                'setting_type': 'json',
                'description': 'Days before due date to send payment reminders',
                'is_public': True
            },
            {
                'key': 'max_approval_attempts',
                'value': '3',
                'setting_type': 'integer',
                'description': 'Maximum PIN approval attempts before lockout',
                'is_public': True
            },
            {
                'key': 'approval_lockout_minutes',
                'value': '30',
                'setting_type': 'integer',
                'description': 'Minutes to lockout after max approval attempts',
                'is_public': True
            }
        ]
        
        for setting_data in system_settings:
            setting, created = SystemSettings.objects.get_or_create(
                key=setting_data['key'],
                defaults=setting_data
            )
            if created:
                self.stdout.write(f'Created system setting: {setting.key}')
            else:
                self.stdout.write(f'System setting already exists: {setting.key}')
        
        # Create default app configurations
        app_configs = [
            # General configurations
            {
                'category': 'general',
                'key': 'app_name',
                'value': 'ChuoPay',
                'setting_type': 'string',
                'description': 'Application name',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'general',
                'key': 'app_version',
                'value': '1.0.0',
                'setting_type': 'string',
                'description': 'Application version',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'general',
                'key': 'support_email',
                'value': 'support@chuopay.com',
                'setting_type': 'string',
                'description': 'Support email address',
                'is_required': True,
                'is_sensitive': False
            },
            
            # Security configurations
            {
                'category': 'security',
                'key': 'password_min_length',
                'value': '8',
                'setting_type': 'integer',
                'description': 'Minimum password length',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'security',
                'key': 'password_require_special_chars',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Require special characters in passwords',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'security',
                'key': 'session_timeout_minutes',
                'value': '30',
                'setting_type': 'integer',
                'description': 'Session timeout in minutes',
                'is_required': True,
                'is_sensitive': False
            },
            
            # Payment configurations
            {
                'category': 'payment',
                'key': 'mpesa_enabled',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Enable MPESA payments',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'payment',
                'key': 'payment_timeout_minutes',
                'value': '15',
                'setting_type': 'integer',
                'description': 'Payment session timeout in minutes',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'payment',
                'key': 'auto_confirm_payments',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Automatically confirm payments',
                'is_required': True,
                'is_sensitive': False
            },
            
            # Notification configurations
            {
                'category': 'notification',
                'key': 'sms_provider',
                'value': 'africas_talking',
                'setting_type': 'string',
                'description': 'SMS provider (twilio, africas_talking)',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'notification',
                'key': 'email_provider',
                'value': 'smtp',
                'setting_type': 'string',
                'description': 'Email provider (smtp, sendgrid)',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'notification',
                'key': 'notification_batch_size',
                'value': '100',
                'setting_type': 'integer',
                'description': 'Number of notifications to send in a batch',
                'is_required': True,
                'is_sensitive': False
            },
            
            # Approval configurations
            {
                'category': 'approval',
                'key': 'signature_required',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Require digital signatures for approvals',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'approval',
                'key': 'pin_required',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Require PIN for non-smartphone users',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'approval',
                'key': 'document_expiry_days',
                'value': '30',
                'setting_type': 'integer',
                'description': 'Days before approval documents expire',
                'is_required': True,
                'is_sensitive': False
            },
            
            # Analytics configurations
            {
                'category': 'analytics',
                'key': 'analytics_enabled',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Enable analytics tracking',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'analytics',
                'key': 'data_retention_days',
                'value': '365',
                'setting_type': 'integer',
                'description': 'Days to retain analytics data',
                'is_required': True,
                'is_sensitive': False
            },
            
            # Integration configurations
            {
                'category': 'integration',
                'key': 'firebase_enabled',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Enable Firebase integration',
                'is_required': True,
                'is_sensitive': False
            },
            {
                'category': 'integration',
                'key': 'webhook_enabled',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Enable webhook notifications',
                'is_required': True,
                'is_sensitive': False
            }
        ]
        
        for config_data in app_configs:
            config, created = AppConfiguration.objects.get_or_create(
                category=config_data['category'],
                key=config_data['key'],
                defaults=config_data
            )
            if created:
                self.stdout.write(f'Created app config: {config.category}.{config.key}')
            else:
                self.stdout.write(f'App config already exists: {config.category}.{config.key}')
        
        # Create default feature flags
        feature_flags = [
            {
                'name': 'advanced_analytics',
                'description': 'Enable advanced analytics features',
                'flag_type': 'boolean',
                'is_enabled': False
            },
            {
                'name': 'beta_features',
                'description': 'Enable beta features for testing',
                'flag_type': 'percentage',
                'is_enabled': True,
                'percentage': 10
            },
            {
                'name': 'new_ui',
                'description': 'Enable new user interface',
                'flag_type': 'boolean',
                'is_enabled': False
            },
            {
                'name': 'auto_payments',
                'description': 'Enable automatic payment processing',
                'flag_type': 'boolean',
                'is_enabled': False
            },
            {
                'name': 'bulk_operations',
                'description': 'Enable bulk operations for admins',
                'flag_type': 'user_list',
                'is_enabled': True
            }
        ]
        
        for flag_data in feature_flags:
            flag, created = FeatureFlag.objects.get_or_create(
                name=flag_data['name'],
                defaults=flag_data
            )
            if created:
                self.stdout.write(f'Created feature flag: {flag.name}')
            else:
                self.stdout.write(f'Feature flag already exists: {flag.name}')
        
        # Create notification settings for existing users
        users_without_settings = User.objects.filter(notification_settings__isnull=True)
        for user in users_without_settings:
            NotificationSettings.objects.create(user=user)
            self.stdout.write(f'Created notification settings for user: {user.full_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized default settings!')
        )
