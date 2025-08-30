from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'system-settings', views.SystemSettingsViewSet)
router.register(r'school-settings', views.SchoolSettingsViewSet)
router.register(r'feature-flags', views.FeatureFlagViewSet)
router.register(r'user-preferences', views.UserPreferencesViewSet, basename='user-preferences')
router.register(r'app-configurations', views.AppConfigurationViewSet)

app_name = 'settings'

urlpatterns = [
    path('', include(router.urls)),
    
    # General settings endpoints
    path('summary/', views.settings_summary, name='settings-summary'),
    path('user-feature-flags/', views.user_feature_flags, name='user-feature-flags'),
]
