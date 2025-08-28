from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, UserProfileSerializer, PhoneVerificationSerializer,
    VerifyCodeSerializer, FirebaseAuthSerializer, UserRegistrationSerializer,
    ChangePasswordSerializer, UpdateProfileSerializer, LoginSerializer
)
from .models import UserProfile
from .firebase_auth import authenticate_user_with_firebase, send_verification_code

User = get_user_model()


class SendVerificationCodeView(generics.CreateAPIView):
    """
    Send verification code to phone number
    """
    serializer_class = PhoneVerificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response({
            'message': 'Verification code sent successfully',
            'phone_number': result['phone_number'],
            'verification_code': result['verification_code'],  # For demo purposes only
            'expires_at': result['expires_at']
        }, status=status.HTTP_200_OK)


class VerifyCodeView(generics.CreateAPIView):
    """
    Verify phone verification code
    """
    serializer_class = VerifyCodeSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Mark user as verified if they exist
        phone_number = serializer.validated_data['phone_number']
        try:
            user = User.objects.get(phone_number=phone_number)
            user.is_phone_verified = True
            user.save()
        except User.DoesNotExist:
            pass
        
        return Response({
            'message': 'Phone number verified successfully',
            'phone_number': phone_number
        }, status=status.HTTP_200_OK)


class FirebaseLoginView(generics.CreateAPIView):
    """
    Login using Firebase ID token
    """
    serializer_class = FirebaseAuthSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        # Login user
        login(request, user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class UserRegistrationView(generics.CreateAPIView):
    """
    Register new user
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.CreateAPIView):
    """
    Traditional login with phone number and password
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Create or get token
        token, created = Token.objects.get_or_create(user=user)
        
        # Login user
        login(request, user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class PhoneLoginView(generics.CreateAPIView):
    """
    Login using phone number after verification (no password required)
    """
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(phone_number=phone_number)
            
            # Check if phone is verified
            if not user.is_phone_verified:
                return Response({
                    'error': 'Phone number not verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Login user
            login(request, user)
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout user
    """
    # Delete token
    try:
        request.user.auth_token.delete()
    except:
        pass
    
    # Logout user
    logout(request)
    
    return Response({
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.profile
    
    def get(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        
        return Response({
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Change user password
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        # Check old password
        if not user.check_password(old_password):
            return Response({
                'error': 'Invalid old password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    List users (admin only)
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.all()
        elif user.is_teacher():
            # Teachers can only see users in their assigned groups
            # This will be implemented when groups are created
            return User.objects.filter(role='parent')
        else:
            return User.objects.none()


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, and delete user (admin only)
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.all()
        elif user.is_teacher():
            # Teachers can only see users in their assigned groups
            return User.objects.filter(role='parent')
        else:
            return User.objects.none()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    """
    Get current user information
    """
    user = request.user
    
    return Response({
        'user': UserSerializer(user).data,
        'profile': UserProfileSerializer(user.profile).data if hasattr(user, 'profile') else None
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_code(request):
    """
    Resend verification code
    """
    phone_number = request.data.get('phone_number')
    
    if not phone_number:
        return Response({
            'error': 'Phone number is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    result = send_verification_code(phone_number)
    
    if result['success']:
        return Response({
            'message': 'Verification code resent successfully',
            'phone_number': phone_number,
            'verification_code': result['verification_code'],  # For demo purposes only
            'expires_at': result['expires_at']
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'error': 'Failed to send verification code'
        }, status=status.HTTP_400_BAD_REQUEST)
