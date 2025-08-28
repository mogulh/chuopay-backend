from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.NotificationTemplateViewSet)
router.register(r'schedules', views.NotificationScheduleViewSet)
router.register(r'logs', views.NotificationLogViewSet)
router.register(r'sms-credits', views.SMSCreditsViewSet)
router.register(r'settings', views.NotificationSettingsViewSet, basename='notification-settings')

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
    path('send-reminder/', views.send_payment_reminder, name='send-reminder'),
    path('students-for-reminders/', views.get_students_for_reminders, name='students-for-reminders'),
] 