from rest_framework import serializers
from .models import (
    School, Group, Student, StudentGroup, StudentParent,
    ContributionEvent, ContributionTier, StudentContribution, ReminderLog, PaymentHistory,
    EventApproval, ParentApprovalPin, EventDocument, DocumentSignature, DigitalCertificate, SchoolLetterhead
)
from accounts.models import User


class SchoolSerializer(serializers.ModelSerializer):
    """
    Serializer for School model
    """
    class Meta:
        model = School
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group model
    """
    school_name = serializers.CharField(source='school.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'student_count']


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student model
    """
    school_name = serializers.CharField(source='school.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'full_name', 'age']


class StudentGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentGroup model
    """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = StudentGroup
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class StudentParentSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentParent model
    """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    
    class Meta:
        model = StudentParent
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ContributionTierSerializer(serializers.ModelSerializer):
    """
    Serializer for ContributionTier model
    """
    class Meta:
        model = ContributionTier
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ContributionEventSerializer(serializers.ModelSerializer):
    """
    Serializer for contribution events with approval configuration
    """
    school_name = serializers.CharField(source='school.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    groups_count = serializers.SerializerMethodField()
    approvals_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ContributionEvent
        fields = [
            'id', 'name', 'description', 'event_type', 'school', 'school_name',
            'amount', 'currency', 'has_tiers', 'participation_type',
            'requires_approval', 'requires_payment', 'approval_before_payment',
            'approval_deadline', 'due_date', 'event_date', 'is_active', 'is_published',
            'created_by', 'created_by_name', 'groups_count', 'approvals_count',
            'documents_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'school_name', 'created_by_name', 'groups_count', 'approvals_count',
            'documents_count', 'created_at', 'updated_at'
        ]
    
    def get_groups_count(self, obj):
        return obj.groups.count()
    
    def get_approvals_count(self, obj):
        return obj.approvals.count()
    
    def get_documents_count(self, obj):
        return obj.documents.count()


class PaymentHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentHistory model
    """
    student_name = serializers.CharField(source='contribution.student.full_name', read_only=True)
    event_name = serializers.CharField(source='contribution.event.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PaymentHistory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'is_completed', 'is_failed']


class StudentContributionSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentContribution model
    """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    tier_name = serializers.CharField(source='tier.name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    confirmed_by_name = serializers.CharField(source='confirmed_by.full_name', read_only=True)
    amount_remaining = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_percentage = serializers.FloatField(read_only=True)
    payment_history_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentContribution
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'amount_remaining', 'payment_percentage', 'payment_history_count']
    
    def get_payment_history_count(self, obj):
        return obj.payment_history.count()


class ReminderLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ReminderLog model
    """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = ReminderLog
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# Nested serializers for detailed views
class GroupDetailSerializer(GroupSerializer):
    """
    Detailed serializer for Group with nested students
    """
    students = StudentSerializer(many=True, read_only=True)
    
    class Meta(GroupSerializer.Meta):
        fields = list(GroupSerializer.Meta.fields) + ['students']


class StudentDetailSerializer(StudentSerializer):
    """
    Detailed serializer for Student with nested groups and parents
    """
    groups = GroupSerializer(many=True, read_only=True)
    parents = serializers.SerializerMethodField()
    
    class Meta(StudentSerializer.Meta):
        fields = list(StudentSerializer.Meta.fields) + ['groups', 'parents']
    
    def get_parents(self, obj):
        from accounts.serializers import UserSerializer
        parents = obj.parents.all()
        return UserSerializer(parents, many=True).data


class ContributionEventDetailSerializer(ContributionEventSerializer):
    """
    Detailed serializer for ContributionEvent with nested tiers
    """
    tiers = ContributionTierSerializer(many=True, read_only=True)
    
    class Meta(ContributionEventSerializer.Meta):
        fields = list(ContributionEventSerializer.Meta.fields) + ['tiers']


class StudentContributionDetailSerializer(StudentContributionSerializer):
    """
    Detailed serializer for StudentContribution with nested payment history
    """
    payment_history = PaymentHistorySerializer(many=True, read_only=True)
    
    class Meta(StudentContributionSerializer.Meta):
        fields = '__all__'


# Bulk operation serializers
class BulkStudentAssignmentSerializer(serializers.Serializer):
    """
    Serializer for bulk student assignment to groups
    """
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of student IDs to assign"
    )
    group_id = serializers.IntegerField(
        help_text="ID of the group to assign students to"
    )
    academic_year = serializers.CharField(
        max_length=9,
        default='2024-2025',
        help_text="Academic year (format: 2024-2025)"
    )
    term = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Term (optional)"
    )


class BulkStudentRemovalSerializer(serializers.Serializer):
    """
    Serializer for bulk student removal from groups
    """
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of student IDs to remove"
    )
    group_id = serializers.IntegerField(
        help_text="ID of the group to remove students from"
    )


# Payment tracking serializers
class PaymentConfirmationSerializer(serializers.Serializer):
    """
    Serializer for manual payment confirmation
    """
    confirmed_by = serializers.IntegerField(help_text="ID of the user confirming the payment")
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Confirmation notes")
    amount_confirmed = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Amount being confirmed"
    )


class PaymentReconciliationSerializer(serializers.Serializer):
    """
    Serializer for payment reconciliation
    """
    start_date = serializers.DateField(help_text="Start date for reconciliation period")
    end_date = serializers.DateField(help_text="End date for reconciliation period")
    event_id = serializers.IntegerField(required=False, help_text="Specific event ID to reconcile")
    group_id = serializers.IntegerField(required=False, help_text="Specific group ID to reconcile")
    payment_method = serializers.CharField(required=False, help_text="Filter by payment method")


# Statistics serializers
class GroupStatisticsSerializer(serializers.Serializer):
    """
    Serializer for group statistics
    """
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    male_students = serializers.IntegerField()
    female_students = serializers.IntegerField()
    average_age = serializers.FloatField()
    contribution_events_count = serializers.IntegerField()
    total_contributions = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_contributions = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_rate = serializers.FloatField()


class SchoolStatisticsSerializer(serializers.Serializer):
    """
    Serializer for school statistics
    """
    total_students = serializers.IntegerField()
    total_groups = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_parents = serializers.IntegerField()
    active_contribution_events = serializers.IntegerField()
    total_contributions_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_contributions_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    overall_payment_rate = serializers.FloatField()


class PaymentTrackingStatisticsSerializer(serializers.Serializer):
    """
    Serializer for payment tracking statistics
    """
    total_transactions = serializers.IntegerField()
    completed_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()
    total_amount_processed = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount_completed = serializers.DecimalField(max_digits=10, decimal_places=2)
    success_rate = serializers.FloatField()
    average_transaction_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method_breakdown = serializers.DictField()
    daily_transactions = serializers.ListField() 


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