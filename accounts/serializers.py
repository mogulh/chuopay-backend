from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, PhoneVerification
from .firebase_auth import authenticate_user_with_firebase, send_verification_code

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name', 
            'full_name', 'role', 'is_phone_verified', 'profile_picture',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_phone_verified', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PhoneVerificationSerializer(serializers.Serializer):
    """
    Serializer for phone verification
    """
    phone_number = serializers.CharField(max_length=13)
    
    def validate_phone_number(self, value):
        """
        Validate phone number format
        """
        if not value.startswith('+254'):
            raise serializers.ValidationError("Phone number must start with +254")
        if len(value) != 13:
            raise serializers.ValidationError("Phone number must be 13 characters long")
        return value
    
    def create(self, validated_data):
        """
        Send verification code to phone number
        """
        phone_number = validated_data['phone_number']
        result = send_verification_code(phone_number)
        
        if not result['success']:
            raise serializers.ValidationError("Failed to send verification code")
        
        # Add verification code to validated_data for demo purposes
        validated_data['verification_code'] = result['verification_code']
        validated_data['expires_at'] = result['expires_at']
        
        return validated_data


class VerifyCodeSerializer(serializers.Serializer):
    """
    Serializer for verifying phone verification code
    """
    phone_number = serializers.CharField(max_length=13)
    verification_code = serializers.CharField(max_length=6)
    
    def validate(self, data):
        """
        Validate verification code
        """
        from .firebase_auth import FirebaseAuth
        
        firebase_auth = FirebaseAuth()
        phone_number = data['phone_number']
        verification_code = data['verification_code']
        
        is_valid = firebase_auth.verify_phone_number(phone_number, verification_code)
        
        if not is_valid:
            raise serializers.ValidationError("Invalid verification code")
        
        return data


class FirebaseAuthSerializer(serializers.Serializer):
    """
    Serializer for Firebase authentication
    """
    id_token = serializers.CharField()
    
    def validate_id_token(self, value):
        """
        Validate Firebase ID token
        """
        user = authenticate_user_with_firebase(value)
        
        if not user:
            raise serializers.ValidationError("Invalid Firebase ID token")
        
        return value
    
    def create(self, validated_data):
        """
        Authenticate user with Firebase
        """
        id_token = validated_data['id_token']
        user = authenticate_user_with_firebase(id_token)
        
        if not user:
            raise serializers.ValidationError("Authentication failed")
        
        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'phone_number', 'email', 'first_name', 'last_name', 
            'role', 'password', 'confirm_password'
        ]
    
    def validate(self, data):
        """
        Validate registration data
        """
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        
        return data
    
    def create(self, validated_data):
        """
        Create new user
        """
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()
    
    def validate(self, data):
        """
        Validate password change data
        """
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError("New passwords do not match")
        
        return data


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    phone_number = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        """
        Validate login credentials
        """
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        try:
            user = User.objects.get(phone_number=phone_number)
            if not user.check_password(password):
                raise serializers.ValidationError("Invalid credentials")
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")
        
        data['user'] = user
        return data 