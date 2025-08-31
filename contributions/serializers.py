from rest_framework import serializers
from .models import (
    School, SchoolSection, Group, Student,
    ContributionEvent, ContributionTier, StudentContribution, PaymentReminder
)
from accounts.models import User


class SchoolSerializer(serializers.ModelSerializer):
    """
    Serializer for School model
    """
    sections_count = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = [
            'id', 'name', 'address', 'city', 'county', 'phone_number', 
            'email', 'website', 'logo', 'currency', 'timezone', 
            'created_at', 'updated_at', 'sections_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_sections_count(self, obj):
        return obj.sections.count()


class SchoolSectionSerializer(serializers.ModelSerializer):
    """
    Serializer for SchoolSection model
    """
    school_name = serializers.CharField(source='school.name', read_only=True)
    section_head_name = serializers.CharField(source='section_head.full_name', read_only=True)
    groups_count = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()
    effective_currency = serializers.CharField(read_only=True)
    effective_timezone = serializers.CharField(read_only=True)
    
    class Meta:
        model = SchoolSection
        fields = [
            'id', 'school', 'school_name', 'name', 'display_name', 'description',
            'currency', 'timezone', 'effective_currency', 'effective_timezone',
            'is_active', 'section_head', 'section_head_name',
            'groups_count', 'students_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_groups_count(self, obj):
        return obj.groups.count()
    
    def get_students_count(self, obj):
        return obj.students.count()


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group model
    """
    school_name = serializers.CharField(source='school.name', read_only=True)
    section_name = serializers.CharField(source='section.display_name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'description', 'group_type', 'school', 'school_name',
            'section', 'section_name', 'teacher', 'teacher_name', 'is_active',
            'max_students', 'student_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student model
    """
    school_name = serializers.CharField(source='school.name', read_only=True)
    section_name = serializers.CharField(source='section.display_name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    groups_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'student_id', 
            'date_of_birth', 'gender', 'age', 'school', 'school_name',
            'section', 'section_name', 'phone_number', 'email', 'address',
            'admission_date', 'current_class', 'is_active', 'is_enrolled',
            'groups_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_groups_count(self, obj):
        return obj.groups.count()


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
    
    class Meta:
        model = ContributionEvent
        fields = [
            'id', 'name', 'description', 'event_type', 'school', 'school_name',
            'amount', 'currency', 'has_tiers', 'participation_type',
            'requires_approval', 'requires_payment', 'approval_before_payment',
            'approval_deadline', 'due_date', 'event_date', 'is_active', 'is_published',
            'groups', 'created_by', 'created_by_name', 'groups_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'school_name', 'created_by_name', 'groups_count',
            'created_at', 'updated_at'
        ]
    
    def get_groups_count(self, obj):
        return obj.groups.count()


class StudentContributionSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentContribution model
    """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    confirmed_by_name = serializers.CharField(source='confirmed_by.full_name', read_only=True)
    amount_remaining = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = StudentContribution
        fields = [
            'id', 'event', 'event_name', 'student', 'student_name', 'parent', 'parent_name',
            'amount_paid', 'amount_required', 'amount_remaining', 'payment_status',
            'payment_method', 'selected_tier', 'transaction_id', 'payment_reference',
            'payment_date', 'confirmation_notes', 'is_confirmed', 'confirmed_by',
            'confirmed_by_name', 'confirmed_at', 'payment_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'event_name', 'student_name', 'parent_name', 'amount_remaining',
            'confirmed_by_name', 'payment_percentage', 'created_at', 'updated_at'
        ]


class PaymentReminderSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentReminder model
    """
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    event_name = serializers.CharField(source='contribution.event.name', read_only=True)
    student_name = serializers.CharField(source='contribution.student.full_name', read_only=True)
    
    class Meta:
        model = PaymentReminder
        fields = [
            'id', 'contribution', 'parent', 'parent_name', 'reminder_type', 'message',
            'scheduled_at', 'sent_at', 'status', 'delivery_notes', 'created_by',
            'created_by_name', 'event_name', 'student_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'parent_name', 'created_by_name', 'event_name', 'student_name',
            'sent_at', 'created_at', 'updated_at'
        ]
