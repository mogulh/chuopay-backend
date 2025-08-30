from rest_framework import serializers
from .models import (
    EventApproval, ParentApprovalPin, EventDocument, DocumentSignature,
    DigitalCertificate, SchoolLetterhead
)


class EventApprovalSerializer(serializers.ModelSerializer):
    """Serializer for event approvals"""
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    can_pay = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = EventApproval
        fields = [
            'id', 'event', 'student', 'parent', 'status', 'approval_method',
            'parent_name', 'student_name', 'event_name', 'can_pay', 'is_expired',
            'signature_image', 'signature_data', 'signature_hash',
            'approval_pin', 'pin_used', 'certificate_data', 'certificate_hash',
            'requested_at', 'approved_at', 'expires_at', 'approval_notes',
            'rejection_reason', 'ip_address', 'user_agent', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'parent_name', 'student_name', 'event_name', 'can_pay', 'is_expired',
            'signature_hash', 'certificate_hash', 'requested_at', 'approved_at',
            'ip_address', 'user_agent', 'created_at', 'updated_at'
        ]


class ParentApprovalPinSerializer(serializers.ModelSerializer):
    """Serializer for parent approval PINs"""
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ParentApprovalPin
        fields = [
            'id', 'parent', 'parent_name', 'is_active', 'max_attempts',
            'current_attempts', 'locked_until', 'last_used', 'usage_count',
            'is_locked', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'parent_name', 'is_locked', 'current_attempts', 'locked_until',
            'last_used', 'usage_count', 'created_at', 'updated_at'
        ]


class SchoolLetterheadSerializer(serializers.ModelSerializer):
    """Serializer for school letterheads"""
    school_name = serializers.CharField(source='school.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    
    class Meta:
        model = SchoolLetterhead
        fields = [
            'id', 'school', 'school_name', 'name', 'letterhead_type', 'department',
            'file', 'file_type', 'file_size', 'width', 'height', 'is_active',
            'is_default', 'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'school_name', 'file_type', 'file_size', 'width', 'height',
            'uploaded_by_name', 'created_at', 'updated_at'
        ]


class EventDocumentSerializer(serializers.ModelSerializer):
    """Serializer for event documents"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    admin_signed_by_name = serializers.CharField(source='admin_signed_by.full_name', read_only=True)
    letterhead_name = serializers.CharField(source='letterhead.name', read_only=True)
    
    class Meta:
        model = EventDocument
        fields = [
            'id', 'event', 'school', 'letterhead', 'title', 'document_type', 'status',
            'event_name', 'school_name', 'created_by_name', 'admin_signed_by_name',
            'letterhead_name', 'content_template', 'final_content', 'document_file', 
            'document_hash', 'admin_signature', 'admin_stamp', 'admin_signed_at', 
            'admin_signed_by', 'requires_parent_signature', 'requires_admin_signature', 
            'is_mandatory', 'version', 'parent_version', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'event_name', 'school_name', 'created_by_name', 'admin_signed_by_name',
            'letterhead_name', 'document_hash', 'admin_signed_at', 'version', 'created_at', 'updated_at'
        ]


class DocumentSignatureSerializer(serializers.ModelSerializer):
    """Serializer for document signatures"""
    signer_name = serializers.CharField(source='signer.full_name', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)
    
    class Meta:
        model = DocumentSignature
        fields = [
            'id', 'document', 'signer', 'approval', 'signature_type',
            'signer_name', 'document_title', 'verified_by_name',
            'signature_image', 'signature_data', 'signature_hash',
            'certificate_data', 'certificate_hash', 'signed_at',
            'ip_address', 'user_agent', 'is_verified', 'verified_at',
            'verified_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'signer_name', 'document_title', 'verified_by_name',
            'signature_hash', 'certificate_hash', 'signed_at', 'ip_address',
            'user_agent', 'verified_at', 'created_at', 'updated_at'
        ]


class DigitalCertificateSerializer(serializers.ModelSerializer):
    """Serializer for digital certificates"""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.full_name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = DigitalCertificate
        fields = [
            'id', 'certificate_type', 'user', 'user_name', 'issued_by_name',
            'certificate_id', 'public_key', 'issued_at', 'expires_at', 'status',
            'issued_by', 'usage_count', 'last_used', 'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'issued_by_name', 'certificate_id', 'issued_at',
            'usage_count', 'last_used', 'is_valid', 'created_at', 'updated_at'
        ]


# Request/Response Serializers
class ApprovalRequestSerializer(serializers.Serializer):
    """Serializer for requesting event approval"""
    event_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    approval_method = serializers.ChoiceField(choices=EventApproval.APPROVAL_METHOD_CHOICES)
    signature_data = serializers.JSONField(required=False)
    approval_pin = serializers.CharField(max_length=6, required=False)
    approval_notes = serializers.CharField(required=False)


class PinVerificationSerializer(serializers.Serializer):
    """Serializer for PIN verification"""
    pin = serializers.CharField(max_length=6)
    approval_id = serializers.IntegerField()


class DocumentGenerationSerializer(serializers.Serializer):
    """Serializer for document generation"""
    event_id = serializers.IntegerField()
    document_type = serializers.ChoiceField(choices=EventDocument.DOCUMENT_TYPE_CHOICES)
    title = serializers.CharField(max_length=200)
    content_template = serializers.CharField()
    letterhead_id = serializers.IntegerField(required=False)
    requires_parent_signature = serializers.BooleanField(default=True)
    requires_admin_signature = serializers.BooleanField(default=True)


class LetterheadUploadSerializer(serializers.Serializer):
    """Serializer for letterhead upload"""
    name = serializers.CharField(max_length=100)
    letterhead_type = serializers.ChoiceField(choices=SchoolLetterhead.LETTERHEAD_TYPE_CHOICES)
    department = serializers.CharField(max_length=50, required=False)
    file = serializers.FileField()
    is_default = serializers.BooleanField(default=False)


class SignatureUploadSerializer(serializers.Serializer):
    """Serializer for signature upload"""
    signature_data = serializers.JSONField(required=False)
    signature_image = serializers.ImageField(required=False)
    approval_id = serializers.IntegerField()


class DocumentSigningSerializer(serializers.Serializer):
    """Serializer for document signing"""
    signature_image = serializers.ImageField(required=False)
    stamp_image = serializers.ImageField(required=False)
    signature_data = serializers.JSONField(required=False)
