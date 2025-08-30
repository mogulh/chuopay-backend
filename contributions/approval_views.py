"""
Views for the approval system with e-signatures and document management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta
import hashlib
import secrets
import json
from PIL import Image
import io

from .models import (
    EventApproval, ParentApprovalPin, EventDocument, DocumentSignature,
    DigitalCertificate, SchoolLetterhead, ContributionEvent, Student, User
)
from .serializers import (
    EventApprovalSerializer, ParentApprovalPinSerializer, EventDocumentSerializer,
    DocumentSignatureSerializer, DigitalCertificateSerializer, SchoolLetterheadSerializer,
    ApprovalRequestSerializer, PinVerificationSerializer, DocumentGenerationSerializer,
    LetterheadUploadSerializer, SignatureUploadSerializer, DocumentSigningSerializer
)


class EventApprovalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing event approvals"""
    queryset = EventApproval.objects.all()
    serializer_class = EventApprovalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'admin':
            # Admins can see all approvals
            return EventApproval.objects.all()
        elif user.role == 'teacher':
            # Teachers can see approvals for their groups
            teacher_groups = user.assigned_groups.all()
            return EventApproval.objects.filter(
                student__groups__in=teacher_groups
            ).distinct()
        else:
            # Parents can only see their own approvals
            return EventApproval.objects.filter(parent=user)
    
    @action(detail=False, methods=['post'])
    def request_approval(self, request):
        """Request approval for an event"""
        serializer = ApprovalRequestSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    event = ContributionEvent.objects.get(
                        id=serializer.validated_data['event_id']
                    )
                    student = Student.objects.get(
                        id=serializer.validated_data['student_id']
                    )
                    
                    # Check if parent is authorized for this student
                    if not student.parents.filter(id=request.user.id).exists():
                        return Response(
                            {'error': 'You are not authorized to approve for this student'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    
                    # Check if approval already exists
                    approval, created = EventApproval.objects.get_or_create(
                        event=event,
                        student=student,
                        parent=request.user,
                        defaults={
                            'approval_method': serializer.validated_data['approval_method'],
                            'expires_at': timezone.now() + timedelta(days=30),
                            'ip_address': self.get_client_ip(request),
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        }
                    )
                    
                    if not created:
                        return Response(
                            {'error': 'Approval request already exists'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Handle signature data
                    if 'signature_data' in serializer.validated_data:
                        approval.signature_data = serializer.validated_data['signature_data']
                        # Generate signature hash
                        signature_string = json.dumps(serializer.validated_data['signature_data'])
                        approval.signature_hash = hashlib.sha256(signature_string.encode()).hexdigest()
                    
                    # Handle PIN verification
                    if 'approval_pin' in serializer.validated_data:
                        try:
                            pin_obj = ParentApprovalPin.objects.get(parent=request.user)
                            is_valid, message = pin_obj.verify_pin(serializer.validated_data['approval_pin'])
                            if not is_valid:
                                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
                            approval.pin_used = True
                        except ParentApprovalPin.DoesNotExist:
                            return Response(
                                {'error': 'No approval PIN set for this parent'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    
                    # Add notes if provided
                    if 'approval_notes' in serializer.validated_data:
                        approval.approval_notes = serializer.validated_data['approval_notes']
                    
                    # Approve the request
                    approval.approve(
                        approval_method=serializer.validated_data['approval_method'],
                        signature_data=serializer.validated_data.get('signature_data'),
                        pin_used='approval_pin' in serializer.validated_data
                    )
                    
                    # Generate digital certificate if needed
                    self.generate_digital_certificate(approval)
                    
                    return Response(
                        EventApprovalSerializer(approval).data,
                        status=status.HTTP_201_CREATED
                    )
                    
            except (ContributionEvent.DoesNotExist, Student.DoesNotExist):
                return Response(
                    {'error': 'Event or student not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def verify_pin(self, request, pk=None):
        """Verify PIN for approval"""
        serializer = PinVerificationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                approval = self.get_object()
                
                # Check if parent is authorized
                if approval.parent != request.user:
                    return Response(
                        {'error': 'You are not authorized to verify this approval'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Verify PIN
                try:
                    pin_obj = ParentApprovalPin.objects.get(parent=request.user)
                    is_valid, message = pin_obj.verify_pin(serializer.validated_data['pin'])
                    
                    if is_valid:
                        approval.approve(approval_method='pin', pin_used=True)
                        return Response({'message': 'Approval successful'})
                    else:
                        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
                        
                except ParentApprovalPin.DoesNotExist:
                    return Response(
                        {'error': 'No approval PIN set for this parent'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except EventApproval.DoesNotExist:
                return Response(
                    {'error': 'Approval not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get pending approvals for the user"""
        user = request.user
        
        if user.role == 'parent':
            queryset = EventApproval.objects.filter(
                parent=user,
                status='pending'
            )
        elif user.role in ['admin', 'teacher']:
            queryset = self.get_queryset().filter(status='pending')
        else:
            queryset = EventApproval.objects.none()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def approved_events(self, request):
        """Get approved events for the user"""
        user = request.user
        
        if user.role == 'parent':
            queryset = EventApproval.objects.filter(
                parent=user,
                status='approved'
            )
        else:
            queryset = self.get_queryset().filter(status='approved')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def generate_digital_certificate(self, approval):
        """Generate digital certificate for approval"""
        try:
            # Create or get existing certificate
            certificate, created = DigitalCertificate.objects.get_or_create(
                user=approval.parent,
                certificate_type='parent',
                status='active',
                defaults={
                    'certificate_id': secrets.token_hex(32),
                    'public_key': secrets.token_hex(64),
                    'private_key_hash': hashlib.sha256(secrets.token_hex(32).encode()).hexdigest(),
                    'expires_at': timezone.now() + timedelta(days=365),
                    'issued_by': User.objects.filter(role='admin').first()
                }
            )
            
            # Update approval with certificate data
            approval.certificate_data = {
                'certificate_id': certificate.certificate_id,
                'issued_at': certificate.issued_at.isoformat(),
                'expires_at': certificate.expires_at.isoformat(),
                'issuer': certificate.issued_by.full_name if certificate.issued_by else 'System'
            }
            approval.certificate_hash = hashlib.sha256(
                json.dumps(approval.certificate_data).encode()
            ).hexdigest()
            approval.save()
            
            # Increment certificate usage
            certificate.increment_usage()
            
        except Exception as e:
            # Log error but don't fail the approval
            print(f"Error generating digital certificate: {e}")
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ParentApprovalPinViewSet(viewsets.ModelViewSet):
    """ViewSet for managing parent approval PINs"""
    queryset = ParentApprovalPin.objects.all()
    serializer_class = ParentApprovalPinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'admin':
            return ParentApprovalPin.objects.all()
        else:
            return ParentApprovalPin.objects.filter(parent=user)
    
    @action(detail=False, methods=['post'])
    def set_pin(self, request):
        """Set approval PIN for parent"""
        pin = request.data.get('pin')
        
        if not pin or len(pin) != 6 or not pin.isdigit():
            return Response(
                {'error': 'PIN must be exactly 6 digits'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pin_obj, created = ParentApprovalPin.objects.get_or_create(
                parent=request.user
            )
            pin_obj.set_pin(pin)
            
            return Response({
                'message': 'PIN set successfully',
                'is_locked': pin_obj.is_locked
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def verify_pin(self, request):
        """Verify PIN for testing"""
        pin = request.data.get('pin')
        
        if not pin:
            return Response(
                {'error': 'PIN is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pin_obj = ParentApprovalPin.objects.get(parent=request.user)
            is_valid, message = pin_obj.verify_pin(pin)
            
            return Response({
                'is_valid': is_valid,
                'message': message,
                'is_locked': pin_obj.is_locked,
                'attempts_remaining': pin_obj.max_attempts - pin_obj.current_attempts
            })
            
        except ParentApprovalPin.DoesNotExist:
            return Response(
                {'error': 'No PIN set for this parent'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def reset_pin(self, request):
        """Reset PIN (admin only)"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can reset PINs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        parent_id = request.data.get('parent_id')
        if not parent_id:
            return Response(
                {'error': 'Parent ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            parent = User.objects.get(id=parent_id, role='parent')
            pin_obj = ParentApprovalPin.objects.get(parent=parent)
            pin_obj.current_attempts = 0
            pin_obj.locked_until = None
            pin_obj.save()
            
            return Response({'message': 'PIN reset successfully'})
            
        except (User.DoesNotExist, ParentApprovalPin.DoesNotExist):
            return Response(
                {'error': 'Parent or PIN not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class SchoolLetterheadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing school letterheads"""
    queryset = SchoolLetterhead.objects.all()
    serializer_class = SchoolLetterheadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role and school"""
        user = self.request.user
        
        if user.role == 'admin':
            # Admins can see all letterheads
            return SchoolLetterhead.objects.all()
        else:
            # Teachers and parents can only see their school's letterheads
            return SchoolLetterhead.objects.filter(school=user.school)
    
    @action(detail=False, methods=['post'])
    def upload_letterhead(self, request):
        """Upload a new letterhead"""
        serializer = LetterheadUploadSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Get school from user
                school = request.user.school
                
                # Process the uploaded file
                uploaded_file = serializer.validated_data['file']
                
                # Validate file type
                allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf']
                if uploaded_file.content_type not in allowed_types:
                    return Response(
                        {'error': 'Invalid file type. Only PNG, JPG, and PDF files are allowed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate file size (max 5MB)
                if uploaded_file.size > 5 * 1024 * 1024:
                    return Response(
                        {'error': 'File size too large. Maximum size is 5MB'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create letterhead
                letterhead = SchoolLetterhead.objects.create(
                    school=school,
                    name=serializer.validated_data['name'],
                    letterhead_type=serializer.validated_data['letterhead_type'],
                    department=serializer.validated_data.get('department', ''),
                    file=uploaded_file,
                    file_type=uploaded_file.content_type,
                    file_size=uploaded_file.size,
                    is_default=serializer.validated_data.get('is_default', False),
                    uploaded_by=request.user
                )
                
                # Process image dimensions if it's an image
                if uploaded_file.content_type.startswith('image/'):
                    try:
                        with Image.open(uploaded_file) as img:
                            letterhead.width = img.width
                            letterhead.height = img.height
                            letterhead.save()
                    except Exception as e:
                        print(f"Error processing image dimensions: {e}")
                
                return Response(
                    SchoolLetterheadSerializer(letterhead).data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set letterhead as default"""
        letterhead = self.get_object()
        
        try:
            # Set as default
            letterhead.is_default = True
            letterhead.save()
            
            return Response({'message': 'Letterhead set as default'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EventDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing event documents"""
    queryset = EventDocument.objects.all()
    serializer_class = EventDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'admin':
            return EventDocument.objects.all()
        elif user.role == 'teacher':
            return EventDocument.objects.filter(
                created_by=user
            )
        else:
            # Parents can see documents for their children's events
            return EventDocument.objects.filter(
                event__student_contributions__student__parents=user
            ).distinct()
    
    @action(detail=False, methods=['post'])
    def generate_document(self, request):
        """Generate document for an event"""
        serializer = DocumentGenerationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                event = ContributionEvent.objects.get(
                    id=serializer.validated_data['event_id']
                )
                
                # Check permissions
                if request.user.role not in ['admin', 'teacher']:
                    return Response(
                        {'error': 'Only admins and teachers can generate documents'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Get letterhead if specified
                letterhead = None
                if 'letterhead_id' in serializer.validated_data:
                    letterhead = SchoolLetterhead.objects.get(
                        id=serializer.validated_data['letterhead_id']
                    )
                
                # Create document
                document = EventDocument.objects.create(
                    event=event,
                    school=event.school,
                    letterhead=letterhead,
                    title=serializer.validated_data['title'],
                    document_type=serializer.validated_data['document_type'],
                    content_template=serializer.validated_data['content_template'],
                    requires_parent_signature=serializer.validated_data.get('requires_parent_signature', True),
                    requires_admin_signature=serializer.validated_data.get('requires_admin_signature', True),
                    created_by=request.user
                )
                
                return Response(
                    EventDocumentSerializer(document).data,
                    status=status.HTTP_201_CREATED
                )
                
            except ContributionEvent.DoesNotExist:
                return Response(
                    {'error': 'Event not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sign_document(self, request, pk=None):
        """Sign document by admin"""
        document = self.get_object()
        
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can sign documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        signature_image = request.FILES.get('signature_image')
        stamp_image = request.FILES.get('stamp_image')
        
        if not signature_image and not stamp_image:
            return Response(
                {'error': 'Signature or stamp image is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            document.sign_by_admin(
                admin_user=request.user,
                signature_image=signature_image,
                stamp_image=stamp_image
            )
            
            return Response({
                'message': 'Document signed successfully',
                'document': EventDocumentSerializer(document).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def generate_personalized_content(self, request, pk=None):
        """Generate personalized content for a specific student and parent"""
        document = self.get_object()
        
        student_id = request.query_params.get('student_id')
        parent_id = request.query_params.get('parent_id')
        
        if not student_id or not parent_id:
            return Response(
                {'error': 'Student ID and Parent ID are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
            parent = User.objects.get(id=parent_id, role='parent')
            
            # Check if parent is authorized for this student
            if not student.parents.filter(id=parent.id).exists():
                return Response(
                    {'error': 'Parent is not authorized for this student'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            personalized_content = document.generate_document_content(student, parent)
            
            return Response({
                'content': personalized_content,
                'student_name': student.full_name,
                'parent_name': parent.full_name,
                'event_name': document.event.name
            })
            
        except (Student.DoesNotExist, User.DoesNotExist):
            return Response(
                {'error': 'Student or parent not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DocumentSignatureViewSet(viewsets.ModelViewSet):
    """ViewSet for managing document signatures"""
    queryset = DocumentSignature.objects.all()
    serializer_class = DocumentSignatureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        
        if user.role == 'admin':
            return DocumentSignature.objects.all()
        else:
            return DocumentSignature.objects.filter(signer=user)
    
    @action(detail=True, methods=['post'])
    def verify_signature(self, request, pk=None):
        """Verify a signature (admin only)"""
        signature = self.get_object()
        
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can verify signatures'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            signature.verify_signature(verified_by=request.user)
            
            return Response({
                'message': 'Signature verified successfully',
                'signature': DocumentSignatureSerializer(signature).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
