from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class EventApproval(models.Model):
    """
    Model for tracking event approvals by parents
    """
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    APPROVAL_METHOD_CHOICES = [
        ('signature', 'Digital Signature'),
        ('pin', 'PIN Code'),
        ('both', 'Signature and PIN'),
    ]
    
    # Relationships
    event = models.ForeignKey('contributions.ContributionEvent', on_delete=models.CASCADE, related_name='approvals')
    student = models.ForeignKey('contributions.Student', on_delete=models.CASCADE, related_name='event_approvals')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_approvals')
    
    # Approval details
    status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approval_method = models.CharField(max_length=20, choices=APPROVAL_METHOD_CHOICES, default='signature')
    
    # Signature information
    signature_image = models.ImageField(upload_to='signatures/', blank=True, null=True)
    signature_data = models.JSONField(blank=True, null=True, help_text="Canvas signature data")
    signature_hash = models.CharField(max_length=64, blank=True, help_text="SHA256 hash of signature for verification")
    
    # PIN information
    approval_pin = models.CharField(max_length=6, blank=True, help_text="Parent's approval PIN")
    pin_used = models.BooleanField(default=False)
    
    # Digital certificate
    certificate_data = models.JSONField(blank=True, null=True, help_text="Digital certificate information")
    certificate_hash = models.CharField(max_length=64, blank=True, help_text="Certificate verification hash")
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Notes
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # IP and device information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'event_approvals'
        verbose_name = 'Event Approval'
        verbose_name_plural = 'Event Approvals'
        unique_together = ['event', 'student', 'parent']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.parent.full_name} - {self.event.name} ({self.status})"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def can_pay(self):
        return self.status == 'approved' and not self.is_expired
    
    def approve(self, approval_method='signature', signature_data=None, pin_used=False):
        """Approve the event participation"""
        self.status = 'approved'
        self.approval_method = approval_method
        self.approved_at = timezone.now()
        
        if signature_data:
            self.signature_data = signature_data
            # Generate signature hash for verification
            import hashlib
            signature_string = str(signature_data)
            self.signature_hash = hashlib.sha256(signature_string.encode()).hexdigest()
        
        if pin_used:
            self.pin_used = True
        
        self.save()
    
    def reject(self, reason=''):
        """Reject the event participation"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()


class ParentApprovalPin(models.Model):
    """
    Model for storing parent approval PINs
    """
    parent = models.OneToOneField(User, on_delete=models.CASCADE, related_name='approval_pin')
    
    # PIN information (hashed)
    pin_hash = models.CharField(max_length=128, help_text="Hashed PIN for security")
    salt = models.CharField(max_length=32, help_text="Salt for PIN hashing")
    
    # PIN settings
    is_active = models.BooleanField(default=True)
    max_attempts = models.PositiveIntegerField(default=3)
    current_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    
    # Usage tracking
    last_used = models.DateTimeField(blank=True, null=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'parent_approval_pins'
        verbose_name = 'Parent Approval PIN'
        verbose_name_plural = 'Parent Approval PINs'
    
    def __str__(self):
        return f"PIN for {self.parent.full_name}"
    
    def set_pin(self, pin):
        """Set a new PIN with proper hashing"""
        import hashlib
        import secrets
        
        # Generate salt
        self.salt = secrets.token_hex(16)
        
        # Hash PIN with salt
        pin_with_salt = f"{pin}{self.salt}"
        self.pin_hash = hashlib.sha256(pin_with_salt.encode()).hexdigest()
        
        # Reset attempts
        self.current_attempts = 0
        self.locked_until = None
        self.is_active = True
        
        self.save()
    
    def verify_pin(self, pin):
        """Verify PIN and handle attempts"""
        import hashlib
        
        # Check if PIN is locked
        if self.locked_until and timezone.now() < self.locked_until:
            return False, "PIN is temporarily locked"
        
        # Hash the provided PIN
        pin_with_salt = f"{pin}{self.salt}"
        provided_hash = hashlib.sha256(pin_with_salt.encode()).hexdigest()
        
        if provided_hash == self.pin_hash:
            # Success - reset attempts and update usage
            self.current_attempts = 0
            self.last_used = timezone.now()
            self.usage_count += 1
            self.save()
            return True, "PIN verified successfully"
        else:
            # Failed attempt
            self.current_attempts += 1
            if self.current_attempts >= self.max_attempts:
                # Lock PIN for 30 minutes
                self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
                self.save()
                return False, "PIN locked due to too many failed attempts"
            else:
                self.save()
                return False, f"Invalid PIN. {self.max_attempts - self.current_attempts} attempts remaining"
    
    @property
    def is_locked(self):
        return self.locked_until and timezone.now() < self.locked_until


class SchoolLetterhead(models.Model):
    """
    Model for managing school letterheads
    """
    LETTERHEAD_TYPE_CHOICES = [
        ('official', 'Official'),
        ('department', 'Department'),
        ('event', 'Event-specific'),
        ('stamp', 'Digital Stamp'),
    ]
    
    school = models.ForeignKey('contributions.School', on_delete=models.CASCADE, related_name='letterheads')
    name = models.CharField(max_length=100)
    letterhead_type = models.CharField(max_length=20, choices=LETTERHEAD_TYPE_CHOICES, default='official')
    department = models.CharField(max_length=50, blank=True)
    
    # File information
    file = models.FileField(upload_to='letterheads/')
    file_type = models.CharField(max_length=10, blank=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    
    # Dimensions
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Metadata
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='uploaded_letterheads',
        limit_choices_to={'role': 'admin'}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'school_letterheads'
        verbose_name = 'School Letterhead'
        verbose_name_plural = 'School Letterheads'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"
    
    def save(self, *args, **kwargs):
        # Set as default if this is the first letterhead for the school
        if not SchoolLetterhead.objects.filter(school=self.school).exists():
            self.is_default = True
        
        # Ensure only one default letterhead per school
        if self.is_default:
            SchoolLetterhead.objects.filter(school=self.school).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)


class EventDocument(models.Model):
    """
    Model for generating and storing event documents
    """
    DOCUMENT_TYPE_CHOICES = [
        ('approval_form', 'Approval Form'),
        ('consent_form', 'Consent Form'),
        ('payment_agreement', 'Payment Agreement'),
        ('liability_waiver', 'Liability Waiver'),
        ('custom', 'Custom Document'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Relationships
    event = models.ForeignKey('contributions.ContributionEvent', on_delete=models.CASCADE, related_name='documents')
    school = models.ForeignKey('contributions.School', on_delete=models.CASCADE, related_name='event_documents')
    letterhead = models.ForeignKey(SchoolLetterhead, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Document information
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Content
    content_template = models.TextField(help_text="Document template with placeholders")
    final_content = models.TextField(blank=True, help_text="Generated document content")
    
    # File storage
    document_file = models.FileField(upload_to='event_documents/', blank=True, null=True)
    document_hash = models.CharField(max_length=64, blank=True, help_text="File hash for verification")
    
    # Admin signature/stamp
    admin_signature = models.ImageField(upload_to='admin_signatures/', blank=True, null=True)
    admin_stamp = models.ImageField(upload_to='admin_stamps/', blank=True, null=True)
    admin_signed_at = models.DateTimeField(blank=True, null=True)
    admin_signed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='signed_documents',
        limit_choices_to={'role': 'admin'}
    )
    
    # Document settings
    requires_parent_signature = models.BooleanField(default=True)
    requires_admin_signature = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=True)
    
    # Versioning
    version = models.PositiveIntegerField(default=1)
    parent_version = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='child_versions'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_documents',
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'event_documents'
        verbose_name = 'Event Document'
        verbose_name_plural = 'Event Documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.event.name}"
    
    def generate_document_content(self, student, parent):
        """Generate personalized document content"""
        # Replace placeholders with actual data
        content = self.content_template
        
        # Event placeholders
        content = content.replace('{{event_name}}', self.event.name)
        content = content.replace('{{event_description}}', self.event.description)
        content = content.replace('{{event_amount}}', str(self.event.amount))
        content = content.replace('{{event_date}}', self.event.event_date.strftime('%B %d, %Y') if self.event.event_date else 'TBD')
        content = content.replace('{{due_date}}', self.event.due_date.strftime('%B %d, %Y'))
        
        # Student placeholders
        content = content.replace('{{student_name}}', student.full_name)
        content = content.replace('{{student_id}}', student.student_id)
        content = content.replace('{{student_class}}', ', '.join([g.name for g in student.groups.all()]))
        
        # Parent placeholders
        content = content.replace('{{parent_name}}', parent.full_name)
        content = content.replace('{{parent_phone}}', parent.phone_number)
        
        # School placeholders
        content = content.replace('{{school_name}}', self.school.name)
        content = content.replace('{{school_address}}', self.school.address)
        
        return content
    
    def sign_by_admin(self, admin_user, signature_image=None, stamp_image=None):
        """Sign document by admin"""
        self.admin_signed_by = admin_user
        self.admin_signed_at = timezone.now()
        
        if signature_image:
            self.admin_signature = signature_image
        
        if stamp_image:
            self.admin_stamp = stamp_image
        
        self.save()


class DocumentSignature(models.Model):
    """
    Model for tracking document signatures
    """
    SIGNATURE_TYPE_CHOICES = [
        ('parent', 'Parent Signature'),
        ('admin', 'Admin Signature'),
        ('witness', 'Witness Signature'),
    ]
    
    # Relationships
    document = models.ForeignKey(EventDocument, on_delete=models.CASCADE, related_name='signatures')
    signer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_signatures')
    approval = models.ForeignKey(EventApproval, on_delete=models.CASCADE, related_name='document_signatures', blank=True, null=True)
    
    # Signature details
    signature_type = models.CharField(max_length=20, choices=SIGNATURE_TYPE_CHOICES)
    signature_image = models.ImageField(upload_to='document_signatures/')
    signature_data = models.JSONField(blank=True, null=True)
    signature_hash = models.CharField(max_length=64, help_text="Signature verification hash")
    
    # Digital certificate
    certificate_data = models.JSONField(blank=True, null=True)
    certificate_hash = models.CharField(max_length=64, blank=True)
    
    # Timestamp and location
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_signatures'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'document_signatures'
        verbose_name = 'Document Signature'
        verbose_name_plural = 'Document Signatures'
        ordering = ['-signed_at']
    
    def __str__(self):
        return f"{self.signer.full_name} - {self.document.title}"
    
    def verify_signature(self, verified_by):
        """Verify the signature"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.verified_by = verified_by
        self.save()


class DigitalCertificate(models.Model):
    """
    Model for managing digital certificates for signature verification
    """
    CERTIFICATE_TYPE_CHOICES = [
        ('parent', 'Parent Certificate'),
        ('admin', 'Admin Certificate'),
        ('system', 'System Certificate'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    # Certificate information
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='digital_certificates')
    
    # Certificate data
    certificate_id = models.CharField(max_length=64, unique=True, help_text="Unique certificate identifier")
    public_key = models.TextField(help_text="Public key for verification")
    private_key_hash = models.CharField(max_length=128, help_text="Hashed private key")
    
    # Validity
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Issuer information
    issued_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='issued_certificates',
        limit_choices_to={'role': 'admin'}
    )
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'digital_certificates'
        verbose_name = 'Digital Certificate'
        verbose_name_plural = 'Digital Certificates'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.user.full_name}"
    
    @property
    def is_valid(self):
        return self.status == 'active' and timezone.now() < self.expires_at
    
    def revoke(self, reason=''):
        """Revoke the certificate"""
        self.status = 'revoked'
        self.save()
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save()
