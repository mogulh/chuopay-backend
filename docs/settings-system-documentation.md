# Settings System Documentation

## Overview

The Settings System provides comprehensive configuration management for the ChuoPay application. It includes system-wide settings, school-specific settings, feature flags, user preferences, and application configurations.

## Features

- **System Settings**: Global application settings with caching
- **School Settings**: School-specific configurations
- **Feature Flags**: A/B testing and feature rollout management
- **User Preferences**: Individual user settings and preferences
- **App Configurations**: Categorized application settings
- **Bulk Operations**: Efficient batch updates
- **Caching**: Performance optimization with Redis cache
- **Type Safety**: Strongly typed settings with validation
- **Access Control**: Role-based permissions

## Models

### 1. SystemSettings

Global system-wide settings accessible to all users.

**Fields:**

- `key` (CharField): Unique setting identifier
- `value` (TextField): Setting value
- `setting_type` (CharField): Data type (string, integer, boolean, json, float)
- `description` (TextField): Setting description
- `is_public` (BooleanField): Whether non-admin users can read
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp
- `updated_by` (ForeignKey): User who last updated

**Methods:**

- `get_value()`: Returns typed value
- `set_value(value)`: Sets value with type conversion
- `get_setting(key, default)`: Class method for cached retrieval
- `set_setting(key, value, ...)`: Class method for setting values

### 2. SchoolSettings

School-specific settings with access control.

**Fields:**

- `school` (ForeignKey): Associated school
- `key` (CharField): Setting key
- `value` (TextField): Setting value
- `setting_type` (CharField): Data type
- `description` (TextField): Setting description
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp
- `updated_by` (ForeignKey): User who last updated

### 3. FeatureFlag

Feature flags for A/B testing and gradual rollouts.

**Fields:**

- `name` (CharField): Unique flag name
- `description` (TextField): Flag description
- `flag_type` (CharField): Type (boolean, percentage, user_list)
- `is_enabled` (BooleanField): Whether flag is active
- `percentage` (IntegerField): Percentage for percentage-based flags
- `enabled_users` (ManyToManyField): Users for user_list flags
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp
- `updated_by` (ForeignKey): User who last updated

**Methods:**

- `is_enabled_for_user(user)`: Check if flag is enabled for specific user

### 4. UserPreferences

Individual user preferences and settings.

**Fields:**

- `user` (OneToOneField): Associated user
- `theme` (CharField): UI theme (light, dark, auto)
- `language` (CharField): Language preference
- `timezone` (CharField): Timezone preference
- `email_notifications` (BooleanField): Email notification preference
- `sms_notifications` (BooleanField): SMS notification preference
- `push_notifications` (BooleanField): Push notification preference
- `in_app_notifications` (BooleanField): In-app notification preference
- `dashboard_layout` (JSONField): Dashboard widget layout
- `default_view` (CharField): Default dashboard view
- `profile_visibility` (CharField): Profile visibility setting
- `default_payment_method` (CharField): Preferred payment method
- `auto_pay_enabled` (BooleanField): Auto-payment preference
- `two_factor_enabled` (BooleanField): 2FA status
- `session_timeout` (IntegerField): Session timeout in minutes
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp

### 5. AppConfiguration

Categorized application configurations.

**Fields:**

- `category` (CharField): Configuration category
- `key` (CharField): Configuration key
- `value` (TextField): Configuration value
- `setting_type` (CharField): Data type
- `description` (TextField): Configuration description
- `is_required` (BooleanField): Whether configuration is required
- `is_sensitive` (BooleanField): Whether value contains sensitive data
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp
- `updated_by` (ForeignKey): User who last updated

## API Endpoints

### System Settings

#### List System Settings

```
GET /api/settings/system-settings/
```

**Query Parameters:**

- `setting_type`: Filter by setting type
- `is_public`: Filter by public status
- `search`: Search in key and description
- `ordering`: Sort by field

**Response:**

```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "key": "maintenance_mode",
      "value": "false",
      "typed_value": false,
      "setting_type": "boolean",
      "description": "Enable maintenance mode",
      "is_public": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "updated_by": 1,
      "updated_by_name": "Admin User"
    }
  ]
}
```

#### Get System Setting

```
GET /api/settings/system-settings/{id}/
```

#### Create System Setting

```
POST /api/settings/system-settings/
```

**Request Body:**

```json
{
  "key": "new_setting",
  "value": "true",
  "setting_type": "boolean",
  "description": "New setting description",
  "is_public": false
}
```

#### Update System Setting

```
PUT /api/settings/system-settings/{id}/
PATCH /api/settings/system-settings/{id}/
```

#### Delete System Setting

```
DELETE /api/settings/system-settings/{id}/
```

#### Bulk Update System Settings

```
POST /api/settings/system-settings/bulk_update/
```

**Request Body:**

```json
{
  "settings": [
    {
      "key": "setting1",
      "value": "new_value1",
      "setting_type": "string"
    },
    {
      "key": "setting2",
      "value": "true",
      "setting_type": "boolean"
    }
  ]
}
```

#### Get Public Settings

```
GET /api/settings/system-settings/public_settings/
```

#### Clear Setting Cache

```
POST /api/settings/system-settings/{id}/clear_cache/
```

### School Settings

#### List School Settings

```
GET /api/settings/school-settings/
```

**Query Parameters:**

- `school`: Filter by school ID
- `setting_type`: Filter by setting type
- `search`: Search in key, description, and school name
- `ordering`: Sort by field

#### Get School Settings by School

```
GET /api/settings/school-settings/by_school/?school_id=1
```

**Response:**

```json
[
  {
    "school_id": 1,
    "school_name": "Sample School",
    "settings": [
      {
        "key": "school_theme",
        "value": "blue",
        "setting_type": "string",
        "description": "School theme color"
      }
    ]
  }
]
```

#### Bulk Update School Settings

```
POST /api/settings/school-settings/bulk_update/
```

**Request Body:**

```json
{
  "school_id": 1,
  "settings": [
    {
      "key": "school_setting1",
      "value": "value1"
    }
  ]
}
```

### Feature Flags

#### List Feature Flags

```
GET /api/settings/feature-flags/
```

#### Get Feature Flag Details

```
GET /api/settings/feature-flags/{id}/
```

**Response:**

```json
{
  "id": 1,
  "name": "beta_features",
  "description": "Enable beta features",
  "flag_type": "percentage",
  "is_enabled": true,
  "percentage": 10,
  "enabled_users_count": 5,
  "enabled_users": [
    {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone_number": "+1234567890"
    }
  ]
}
```

#### Get Active Feature Flags

```
GET /api/settings/feature-flags/active_flags/
```

#### Get User Feature Flags

```
GET /api/settings/feature-flags/user_flags/
```

**Response:**

```json
[
  {
    "name": "beta_features",
    "is_enabled": true,
    "is_enabled_for_user": true,
    "flag_type": "percentage",
    "percentage": 10
  }
]
```

#### Add User to Feature Flag

```
POST /api/settings/feature-flags/{id}/add_user/
```

**Request Body:**

```json
{
  "user_id": 1
}
```

#### Remove User from Feature Flag

```
POST /api/settings/feature-flags/{id}/remove_user/
```

**Request Body:**

```json
{
  "user_id": 1
}
```

### User Preferences

#### Get My Preferences

```
GET /api/settings/user-preferences/my_preferences/
```

#### Get Settings Summary

```
GET /api/settings/user-preferences/settings_summary/
```

**Response:**

```json
{
  "preferences": {
    "id": 1,
    "user": 1,
    "user_name": "John Doe",
    "theme": "auto",
    "language": "en",
    "timezone": "UTC",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "in_app_notifications": true,
    "dashboard_layout": {},
    "default_view": "overview",
    "profile_visibility": "school_only",
    "default_payment_method": "",
    "auto_pay_enabled": false,
    "two_factor_enabled": false,
    "session_timeout": 30
  },
  "enabled_features": ["beta_features"],
  "notification_settings": {
    "receives_notifications": true,
    "receives_sms": true,
    "receives_email": false,
    "receives_push": true,
    "receives_in_app": true,
    "payment_reminders": true,
    "event_updates": true,
    "general_announcements": true
  }
}
```

### App Configurations

#### List App Configurations

```
GET /api/settings/app-configurations/
```

#### Get Configurations by Category

```
GET /api/settings/app-configurations/by_category/?category=security
```

**Response:**

```json
{
  "security": [
    {
      "key": "password_min_length",
      "value": 8,
      "setting_type": "integer",
      "description": "Minimum password length",
      "is_required": true,
      "is_sensitive": false
    }
  ]
}
```

#### Get Public Configurations

```
GET /api/settings/app-configurations/public_configs/
```

### General Settings Endpoints

#### Settings Summary

```
GET /api/settings/summary/
```

**Response:**

```json
{
  "system_settings_count": 15,
  "school_settings_count": 25,
  "feature_flags_count": 5,
  "active_feature_flags_count": 3,
  "configurations_count": 20
}
```

#### User Feature Flags

```
GET /api/settings/user-feature-flags/
```

## Usage Examples

### Python Usage

#### Getting System Settings

```python
from settings.models import SystemSettings

# Get a setting with caching
maintenance_mode = SystemSettings.get_setting('maintenance_mode', default=False)
max_file_size = SystemSettings.get_setting('max_file_size_mb', default=10)

# Set a setting
SystemSettings.set_setting(
    key='maintenance_mode',
    value=True,
    setting_type='boolean',
    description='Enable maintenance mode',
    is_public=True,
    user=request.user
)
```

#### Feature Flags

```python
from settings.models import FeatureFlag

# Check if feature is enabled for user
if FeatureFlag.objects.get(name='beta_features').is_enabled_for_user(user):
    # Show beta features
    pass
```

#### User Preferences

```python
from settings.models import UserPreferences

# Get or create user preferences
preferences, created = UserPreferences.objects.get_or_create(
    user=user,
    defaults={'theme': 'auto', 'language': 'en'}
)

# Update preferences
preferences.theme = 'dark'
preferences.save()
```

### Frontend Usage

#### React Hook Example

```javascript
import { useState, useEffect } from "react";

const useSystemSetting = (key, defaultValue) => {
  const [value, setValue] = useState(defaultValue);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/settings/system-settings/?key=${key}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.results.length > 0) {
          setValue(data.results[0].typed_value);
        }
        setLoading(false);
      });
  }, [key]);

  return [value, loading];
};

// Usage
const [maintenanceMode, loading] = useSystemSetting("maintenance_mode", false);
```

#### Feature Flag Hook

```javascript
const useFeatureFlag = (flagName) => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/settings/user-feature-flags/")
      .then((response) => response.json())
      .then((flags) => {
        const flag = flags.find((f) => f.name === flagName);
        setIsEnabled(flag?.is_enabled_for_user || false);
        setLoading(false);
      });
  }, [flagName]);

  return [isEnabled, loading];
};

// Usage
const [betaEnabled, loading] = useFeatureFlag("beta_features");
```

## Management Commands

### Initialize Default Settings

```bash
python manage.py init_settings
```

This command creates default system settings, app configurations, and feature flags.

## Security Considerations

1. **Access Control**: Settings have role-based access control
2. **Sensitive Data**: Sensitive configurations are hidden in admin
3. **Validation**: All settings are validated before saving
4. **Caching**: System settings are cached for performance
5. **Audit Trail**: All changes are tracked with user and timestamp

## Performance Optimization

1. **Caching**: System settings are cached for 5 minutes
2. **Database Indexing**: Proper indexes on frequently queried fields
3. **Bulk Operations**: Efficient batch updates for multiple settings
4. **Lazy Loading**: Related objects are loaded only when needed

## Error Handling

The settings system includes comprehensive error handling:

1. **Validation Errors**: Proper validation with descriptive messages
2. **Type Conversion**: Safe type conversion with fallbacks
3. **Cache Failures**: Graceful degradation when cache is unavailable
4. **Database Errors**: Proper exception handling for database operations

## Monitoring and Logging

1. **Setting Changes**: All setting modifications are logged
2. **Cache Hits/Misses**: Cache performance is monitored
3. **Feature Flag Usage**: Feature flag access is tracked
4. **Error Tracking**: All errors are logged for debugging

## Future Enhancements

1. **Environment-Specific Settings**: Different settings for dev/staging/prod
2. **Setting Dependencies**: Settings that depend on other settings
3. **Setting Validation Rules**: Custom validation rules for settings
4. **Setting Templates**: Predefined setting templates for common configurations
5. **Setting Import/Export**: Bulk import/export of settings
6. **Setting Versioning**: Version control for setting changes
7. **Setting Rollback**: Ability to rollback setting changes
8. **Setting Notifications**: Notify users when relevant settings change
