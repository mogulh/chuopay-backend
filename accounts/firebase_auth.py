import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class FirebaseAuth:
    """
    Firebase Authentication utility class
    """
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Initialize Firebase Admin SDK if not already initialized
            if not firebase_admin._apps:
                # Use service account key if available, otherwise use default credentials
                if hasattr(settings, 'FIREBASE_SERVICE_ACCOUNT_KEY'):
                    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
                else:
                    cred = credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred)
            
            self.auth = auth
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise
    
    def verify_id_token(self, id_token):
        """
        Verify Firebase ID token and return user info
        """
        try:
            decoded_token = self.auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Failed to verify Firebase ID token: {e}")
            raise ValidationError("Invalid Firebase ID token")
    
    def get_user_by_uid(self, uid):
        """
        Get Firebase user by UID
        """
        try:
            user_record = self.auth.get_user(uid)
            return user_record
        except Exception as e:
            logger.error(f"Failed to get Firebase user by UID {uid}: {e}")
            return None
    
    def create_custom_token(self, uid, additional_claims=None):
        """
        Create custom token for client-side authentication
        """
        try:
            custom_token = self.auth.create_custom_token(uid, additional_claims)
            return custom_token
        except Exception as e:
            logger.error(f"Failed to create custom token for UID {uid}: {e}")
            raise
    
    def verify_phone_number(self, phone_number, verification_code):
        """
        Verify phone number with verification code
        Note: This is a simplified implementation. In production, you'd use Firebase Phone Auth
        """
        try:
            # In a real implementation, you'd verify with Firebase Phone Auth
            # For now, we'll use a simple verification
            from .models import PhoneVerification
            from django.utils import timezone
            
            verification = PhoneVerification.objects.filter(
                phone_number=phone_number,
                verification_code=verification_code,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
            
            if verification:
                verification.is_used = True
                verification.save()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to verify phone number {phone_number}: {e}")
            return False


def get_or_create_user_from_firebase(firebase_user_data):
    """
    Get or create Django user from Firebase user data
    """
    try:
        firebase_uid = firebase_user_data.get('uid')
        phone_number = firebase_user_data.get('phone_number')
        
        if not firebase_uid or not phone_number:
            raise ValidationError("Firebase UID and phone number are required")
        
        # Try to get existing user by Firebase UID
        user = User.objects.filter(firebase_uid=firebase_uid).first()
        
        if not user:
            # Try to get user by phone number
            user = User.objects.filter(phone_number=phone_number).first()
            
            if user:
                # Update existing user with Firebase UID
                user.firebase_uid = firebase_uid
                user.is_phone_verified = True
                user.save()
            else:
                # Create new user
                user = User.objects.create(
                    firebase_uid=firebase_uid,
                    phone_number=phone_number,
                    first_name=firebase_user_data.get('display_name', '').split()[0] if firebase_user_data.get('display_name') else '',
                    last_name=' '.join(firebase_user_data.get('display_name', '').split()[1:]) if firebase_user_data.get('display_name') else '',
                    is_phone_verified=True,
                    role='parent'  # Default role
                )
        
        return user
    except Exception as e:
        logger.error(f"Failed to get or create user from Firebase: {e}")
        raise


def authenticate_user_with_firebase(id_token):
    """
    Authenticate user using Firebase ID token
    """
    try:
        firebase_auth = FirebaseAuth()
        decoded_token = firebase_auth.verify_id_token(id_token)
        
        # Get or create user from Firebase data
        user = get_or_create_user_from_firebase(decoded_token)
        
        return user
    except Exception as e:
        logger.error(f"Failed to authenticate user with Firebase: {e}")
        return None


def send_verification_code(phone_number):
    """
    Send verification code to phone number
    Note: This is a simplified implementation. In production, you'd integrate with SMS service
    """
    try:
        import random
        from django.utils import timezone
        from datetime import timedelta
        from .models import PhoneVerification
        
        # Generate 6-digit verification code
        verification_code = str(random.randint(100000, 999999))
        
        # Create verification record
        expires_at = timezone.now() + timedelta(minutes=10)
        
        PhoneVerification.objects.create(
            phone_number=phone_number,
            verification_code=verification_code,
            expires_at=expires_at
        )
        
        # In production, you'd send SMS here
        # For demo purposes, we'll return the code
        logger.info(f"Verification code for {phone_number}: {verification_code}")
        
        return {
            'success': True,
            'verification_code': verification_code,  # For demo purposes only
            'expires_at': expires_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send verification code to {phone_number}: {e}")
        return {
            'success': False,
            'error': str(e)
        } 