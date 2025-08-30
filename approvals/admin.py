from django.contrib import admin
from .models import (
    EventApproval, ParentApprovalPin, EventDocument, DocumentSignature,
    DigitalCertificate, SchoolLetterhead
)


@admin.register(EventApproval)
class EventApprovalAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'event', 'status', 'approval_method', 'requested_at', 'approved_at']
    list_filter = ['status', 'approval_method', 'requested_at', 'approved_at']
    search_fields = ['parent__first_name', 'parent__last_name', 'student__first_name', 'student__last_name', 'event__name']
    readonly_fields = ['signature_hash', 'certificate_hash', 'ip_address', 'user_agent']
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'student', 'parent', 'status', 'approval_method')
        }),
        ('Signature Information', {
            'fields': ('signature_image', 'signature_data', 'signature_hash'),
            'classes': ('collapse',)
        }),
        ('PIN Information', {
            'fields': ('approval_pin', 'pin_used'),
            'classes': ('collapse',)
        }),
        ('Digital Certificate', {
            'fields': ('certificate_data', 'certificate_hash'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'approved_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('approval_notes', 'rejection_reason', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ParentApprovalPin)
class ParentApprovalPinAdmin(admin.ModelAdmin):
    list_display = ['parent', 'is_active', 'is_locked', 'current_attempts', 'usage_count', 'last_used']
    list_filter = ['is_active', 'current_attempts']
    search_fields = ['parent__first_name', 'parent__last_name', 'parent__phone_number']
    readonly_fields = ['pin_hash', 'salt', 'usage_count', 'last_used']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('parent', 'is_active')
        }),
        ('PIN Security', {
            'fields': ('pin_hash', 'salt', 'max_attempts', 'current_attempts', 'locked_until'),
            'classes': ('collapse',)
        }),
        ('Usage Tracking', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SchoolLetterhead)
class SchoolLetterheadAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'letterhead_type', 'department', 'is_active', 'is_default', 'uploaded_by']
    list_filter = ['letterhead_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'school__name', 'department']
    readonly_fields = ['file_type', 'file_size', 'width', 'height']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('school', 'name', 'letterhead_type', 'department')
        }),
        ('File Information', {
            'fields': ('file', 'file_type', 'file_size', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'is_default', 'uploaded_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EventDocument)
class EventDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'school', 'document_type', 'status', 'created_by', 'created_at']
    list_filter = ['document_type', 'status', 'requires_parent_signature', 'requires_admin_signature', 'created_at']
    search_fields = ['title', 'event__name', 'school__name', 'created_by__first_name', 'created_by__last_name']
    readonly_fields = ['document_hash', 'version', 'admin_signed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'school', 'title', 'document_type', 'status')
        }),
        ('Content', {
            'fields': ('content_template', 'final_content', 'letterhead'),
            'classes': ('collapse',)
        }),
        ('File Information', {
            'fields': ('document_file', 'document_hash'),
            'classes': ('collapse',)
        }),
        ('Admin Signature', {
            'fields': ('admin_signature', 'admin_stamp', 'admin_signed_by', 'admin_signed_at'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('requires_parent_signature', 'requires_admin_signature', 'is_mandatory'),
            'classes': ('collapse',)
        }),
        ('Versioning', {
            'fields': ('version', 'parent_version', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentSignature)
class DocumentSignatureAdmin(admin.ModelAdmin):
    list_display = ['signer', 'document', 'signature_type', 'is_verified', 'signed_at', 'verified_at']
    list_filter = ['signature_type', 'is_verified', 'signed_at', 'verified_at']
    search_fields = ['signer__first_name', 'signer__last_name', 'document__title']
    readonly_fields = ['signature_hash', 'certificate_hash', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('document', 'signer', 'approval', 'signature_type')
        }),
        ('Signature Data', {
            'fields': ('signature_image', 'signature_data', 'signature_hash'),
            'classes': ('collapse',)
        }),
        ('Digital Certificate', {
            'fields': ('certificate_data', 'certificate_hash'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verified_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('signed_at', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DigitalCertificate)
class DigitalCertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'user', 'certificate_type', 'status', 'is_valid', 'issued_by', 'issued_at']
    list_filter = ['certificate_type', 'status', 'issued_at', 'expires_at']
    search_fields = ['certificate_id', 'user__first_name', 'user__last_name', 'issued_by__first_name', 'issued_by__last_name']
    readonly_fields = ['certificate_id', 'public_key', 'private_key_hash', 'usage_count', 'last_used']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('certificate_id', 'user', 'certificate_type', 'status')
        }),
        ('Certificate Data', {
            'fields': ('public_key', 'private_key_hash'),
            'classes': ('collapse',)
        }),
        ('Validity', {
            'fields': ('issued_at', 'expires_at', 'issued_by'),
            'classes': ('collapse',)
        }),
        ('Usage Tracking', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
    )
