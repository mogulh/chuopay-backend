from django.shortcuts import render
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    SystemSettings, SchoolSettings, FeatureFlag, 
    UserPreferences, AppConfiguration
)
from .serializers import (
    SystemSettingsSerializer, SchoolSettingsSerializer, FeatureFlagSerializer,
    FeatureFlagDetailSerializer, UserPreferencesSerializer, AppConfigurationSerializer,
    BulkSystemSettingsSerializer, BulkSchoolSettingsSerializer,
    SettingsSummarySerializer, FeatureFlagStatusSerializer, UserSettingsSummarySerializer
)
from notifications.models import NotificationSettings


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing system-wide settings
    """
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['setting_type', 'is_public']
    search_fields = ['key', 'description']
    ordering_fields = ['key', 'created_at', 'updated_at']
    ordering = ['key']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Allow authenticated users to read public settings
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Non-admin users can only see public settings
        if not user.is_staff:
            queryset = queryset.filter(is_public=True)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update multiple settings"""
        serializer = BulkSystemSettingsSerializer(data=request.data)
        if serializer.is_valid():
            settings_data = serializer.validated_data['settings']
            updated_settings = []
            
            for setting_data in settings_data:
                setting, created = SystemSettings.objects.get_or_create(
                    key=setting_data['key'],
                    defaults={
                        'setting_type': setting_data.get('setting_type', 'string'),
                        'description': setting_data.get('description', ''),
                        'is_public': setting_data.get('is_public', False),
                        'updated_by': request.user
                    }
                )
                
                setting.set_value(setting_data['value'])
                setting.updated_by = request.user
                setting.save()
                updated_settings.append(setting)
            
            # Clear cache for updated settings
            for setting in updated_settings:
                cache.delete(f'system_setting_{setting.key}')
            
            return Response({
                'message': f'Successfully updated {len(updated_settings)} settings',
                'updated_count': len(updated_settings)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def public_settings(self, request):
        """Get all public settings"""
        settings = self.get_queryset().filter(is_public=True)
        serializer = self.get_serializer(settings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def clear_cache(self, request, pk=None):
        """Clear cache for a specific setting"""
        setting = self.get_object()
        cache.delete(f'system_setting_{setting.key}')
        return Response({'message': f'Cache cleared for setting: {setting.key}'})


class SchoolSettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing school-specific settings
    """
    queryset = SchoolSettings.objects.select_related('school', 'updated_by')
    serializer_class = SchoolSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['school', 'setting_type']
    search_fields = ['key', 'description', 'school__name']
    ordering_fields = ['key', 'created_at', 'updated_at']
    ordering = ['school__name', 'key']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by user's access level
        if user.role == 'admin':
            return queryset
        elif user.role == 'teacher':
            # Teachers can see settings for schools they work at
            return queryset.filter(school__teachers=user)
        elif user.role == 'parent':
            # Parents can see settings for schools their children attend
            return queryset.filter(school__students__parents=user).distinct()
        else:
            return queryset.none()
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update multiple school settings"""
        serializer = BulkSchoolSettingsSerializer(data=request.data)
        if serializer.is_valid():
            school_id = serializer.validated_data['school_id']
            settings_data = serializer.validated_data['settings']
            updated_settings = []
            
            for setting_data in settings_data:
                setting, created = SchoolSettings.objects.get_or_create(
                    school_id=school_id,
                    key=setting_data['key'],
                    defaults={
                        'setting_type': setting_data.get('setting_type', 'string'),
                        'description': setting_data.get('description', ''),
                        'updated_by': request.user
                    }
                )
                
                setting.set_value(setting_data['value'])
                setting.updated_by = request.user
                setting.save()
                updated_settings.append(setting)
            
            return Response({
                'message': f'Successfully updated {len(updated_settings)} school settings',
                'updated_count': len(updated_settings)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_school(self, request):
        """Get settings grouped by school"""
        school_id = request.query_params.get('school_id')
        if school_id:
            settings = self.get_queryset().filter(school_id=school_id)
        else:
            settings = self.get_queryset()
        
        # Group by school
        schools_data = {}
        for setting in settings:
            school_name = setting.school.name
            if school_name not in schools_data:
                schools_data[school_name] = {
                    'school_id': setting.school.id,
                    'school_name': school_name,
                    'settings': []
                }
            
            schools_data[school_name]['settings'].append({
                'key': setting.key,
                'value': setting.get_value(),
                'setting_type': setting.setting_type,
                'description': setting.description
            })
        
        return Response(list(schools_data.values()))


class FeatureFlagViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing feature flags
    """
    queryset = FeatureFlag.objects.prefetch_related('enabled_users', 'updated_by')
    serializer_class = FeatureFlagSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['flag_type', 'is_enabled']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FeatureFlagDetailSerializer
        return FeatureFlagSerializer
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active_flags(self, request):
        """Get all active feature flags"""
        flags = self.queryset.filter(is_enabled=True)
        serializer = self.get_serializer(flags, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_flags(self, request):
        """Get feature flags status for current user"""
        user = request.user
        flags = self.queryset.filter(is_enabled=True)
        
        user_flags = []
        for flag in flags:
            user_flags.append({
                'name': flag.name,
                'is_enabled': flag.is_enabled,
                'is_enabled_for_user': flag.is_enabled_for_user(user),
                'flag_type': flag.flag_type,
                'percentage': flag.percentage if flag.flag_type == 'percentage' else None
            })
        
        return Response(user_flags)
    
    @action(detail=True, methods=['post'])
    def add_user(self, request, pk=None):
        """Add a user to the enabled users list"""
        flag = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            from accounts.models import User
            user = User.objects.get(id=user_id)
            flag.enabled_users.add(user)
            return Response({'message': f'User {user.full_name} added to feature flag {flag.name}'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_user(self, request, pk=None):
        """Remove a user from the enabled users list"""
        flag = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            from accounts.models import User
            user = User.objects.get(id=user_id)
            flag.enabled_users.remove(user)
            return Response({'message': f'User {user.full_name} removed from feature flag {flag.name}'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class UserPreferencesViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user preferences
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserPreferences.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's preferences"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': 'auto',
                'language': 'en',
                'timezone': 'UTC'
            }
        )
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def settings_summary(self, request):
        """Get comprehensive settings summary for current user"""
        # Get or create preferences
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': 'auto',
                'language': 'en',
                'timezone': 'UTC'
            }
        )
        
        # Get enabled features
        enabled_features = []
        for flag in FeatureFlag.objects.filter(is_enabled=True):
            if flag.is_enabled_for_user(request.user):
                enabled_features.append(flag.name)
        
        # Get notification settings
        notification_settings, created = NotificationSettings.objects.get_or_create(
            user=request.user
        )
        
        summary = {
            'preferences': UserPreferencesSerializer(preferences).data,
            'enabled_features': enabled_features,
            'notification_settings': {
                'receives_notifications': notification_settings.receives_notifications,
                'receives_sms': notification_settings.receives_sms,
                'receives_email': notification_settings.receives_email,
                'receives_push': notification_settings.receives_push,
                'receives_in_app': notification_settings.receives_in_app,
                'payment_reminders': notification_settings.payment_reminders,
                'event_updates': notification_settings.event_updates,
                'general_announcements': notification_settings.general_announcements,
            }
        }
        
        return Response(summary)


class AppConfigurationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing application configurations
    """
    queryset = AppConfiguration.objects.select_related('updated_by')
    serializer_class = AppConfigurationSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'setting_type', 'is_required', 'is_sensitive']
    search_fields = ['key', 'description']
    ordering_fields = ['category', 'key', 'created_at', 'updated_at']
    ordering = ['category', 'key']
    
    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get configurations grouped by category"""
        category = request.query_params.get('category')
        if category:
            configs = self.queryset.filter(category=category)
        else:
            configs = self.queryset
        
        # Group by category
        categories_data = {}
        for config in configs:
            if config.category not in categories_data:
                categories_data[config.category] = []
            
            categories_data[config.category].append({
                'key': config.key,
                'value': config.get_value(),
                'setting_type': config.setting_type,
                'description': config.description,
                'is_required': config.is_required,
                'is_sensitive': config.is_sensitive
            })
        
        return Response(categories_data)
    
    @action(detail=False, methods=['get'])
    def public_configs(self, request):
        """Get non-sensitive configurations for authenticated users"""
        configs = self.queryset.filter(is_sensitive=False)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)


# General settings endpoints
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def settings_summary(request):
    """Get summary of all settings for dashboard"""
    summary = {
        'system_settings_count': SystemSettings.objects.count(),
        'school_settings_count': SchoolSettings.objects.count(),
        'feature_flags_count': FeatureFlag.objects.count(),
        'active_feature_flags_count': FeatureFlag.objects.filter(is_enabled=True).count(),
        'configurations_count': AppConfiguration.objects.count(),
    }
    
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_feature_flags(request):
    """Get feature flags status for current user"""
    user = request.user
    flags = FeatureFlag.objects.filter(is_enabled=True)
    
    user_flags = []
    for flag in flags:
        user_flags.append({
            'name': flag.name,
            'is_enabled': flag.is_enabled,
            'is_enabled_for_user': flag.is_enabled_for_user(user),
            'flag_type': flag.flag_type,
            'percentage': flag.percentage if flag.flag_type == 'percentage' else None
        })
    
    return Response(user_flags)
