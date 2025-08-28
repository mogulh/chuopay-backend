from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('auth/firebase-login/', views.FirebaseLoginView.as_view(), name='firebase_login'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/phone-login/', views.PhoneLoginView.as_view(), name='phone_login'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Phone verification endpoints
    path('auth/send-verification/', views.SendVerificationCodeView.as_view(), name='send_verification'),
    path('auth/verify-code/', views.VerifyCodeView.as_view(), name='verify_code'),
    path('auth/resend-verification/', views.resend_verification_code, name='resend_verification'),
    
    # User management endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('current-user/', views.current_user_view, name='current_user'),
] 