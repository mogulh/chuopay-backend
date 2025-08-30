from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import mpesa_views
from . import analytics_views

router = DefaultRouter()
router.register(r'schools', views.SchoolViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'students', views.StudentViewSet)
router.register(r'contribution-events', views.ContributionEventViewSet)
router.register(r'contribution-tiers', views.ContributionTierViewSet)
router.register(r'student-contributions', views.StudentContributionViewSet)
router.register(r'payment-reminders', views.PaymentReminderViewSet)

app_name = 'contributions'

urlpatterns = [
    path('', include(router.urls)),
    # MPESA endpoints
    path('mpesa/initiate-stk-push/', mpesa_views.initiate_stk_push, name='initiate-stk-push'),
    path('mpesa/callback/', mpesa_views.mpesa_callback, name='mpesa-callback'),
    path('mpesa/check-status/<str:checkout_request_id>/', mpesa_views.check_payment_status, name='check-payment-status'),
    path('mpesa/payment-history/<int:contribution_id>/', mpesa_views.get_payment_history, name='get-payment-history'),
    # Analytics endpoints
    path('analytics/dashboard/', analytics_views.analytics_dashboard, name='analytics-dashboard'),
    path('analytics/overview/', analytics_views.overview_statistics, name='overview-statistics'),
    path('analytics/trends/', analytics_views.trends_data, name='trends-data'),
    path('analytics/breakdown/', analytics_views.breakdown_data, name='breakdown-data'),
    path('analytics/top-performers/', analytics_views.top_performers, name='top-performers'),
    path('analytics/payment-analytics/', analytics_views.payment_analytics, name='payment-analytics'),
    path('analytics/financial-reports/', analytics_views.financial_reports, name='financial-reports'),
    path('analytics/export/', analytics_views.export_report, name='export-report'),
]
