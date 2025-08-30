"""
Document generation service for creating PDFs with signatures and letterheads
"""
import os
import hashlib
import json
from datetime import datetime
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PIL import Image
import qrcode

from .models import EventDocument, SchoolLetterhead, DocumentSignature


class DocumentGenerator:
    """Service for generating PDF documents with signatures and letterheads"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT
        ))
        
        # Signature style
        self.styles.add(ParagraphStyle(
            name='Signature',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor=colors.darkblue
        ))
    
    def generate_approval_document(self, document, student, parent, approval=None):
        """Generate a complete approval document with letterhead and signatures"""
        try:
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content
            story = []
            
            # Add letterhead if available
            if document.letterhead and document.letterhead.file:
                story.extend(self.add_letterhead(document.letterhead, doc))
            
            # Add document title
            story.append(Paragraph(document.title, self.styles['CustomTitle']))
            story.append(Spacer(1, 20))
            
            # Add personalized content
            content = document.generate_document_content(student, parent)
            story.extend(self.parse_content_to_paragraphs(content))
            
            # Add signature sections
            story.extend(self.add_signature_sections(document, student, parent, approval))
            
            # Add verification information
            story.extend(self.add_verification_info(document, approval))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Generate document hash
            document_hash = hashlib.sha256(pdf_content).hexdigest()
            
            # Save document file
            filename = f"document_{document.id}_{student.id}_{parent.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            document.document_file.save(filename, ContentFile(pdf_content))
            document.document_hash = document_hash
            document.save()
            
            return document
            
        except Exception as e:
            print(f"Error generating document: {e}")
            raise
    
    def add_letterhead(self, letterhead, doc):
        """Add letterhead to document"""
        story = []
        
        try:
            # For now, add letterhead as text
            # In production, you'd process the actual letterhead image
            story.append(Paragraph(f"<b>{letterhead.school.name}</b>", self.styles['CustomSubtitle']))
            story.append(Paragraph(letterhead.school.address, self.styles['CustomBody']))
            story.append(Spacer(1, 20))
            
        except Exception as e:
            print(f"Error adding letterhead: {e}")
        
        return story
    
    def parse_content_to_paragraphs(self, content):
        """Parse content text into paragraphs"""
        paragraphs = []
        
        # Split content by double newlines to get paragraphs
        content_paragraphs = content.split('\n\n')
        
        for para in content_paragraphs:
            if para.strip():
                paragraphs.append(Paragraph(para.strip(), self.styles['CustomBody']))
                paragraphs.append(Spacer(1, 12))
        
        return paragraphs
    
    def add_signature_sections(self, document, student, parent, approval):
        """Add signature sections to document"""
        story = []
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("SIGNATURE SECTIONS", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 20))
        
        # Parent signature section
        if document.requires_parent_signature:
            story.append(Paragraph("Parent/Guardian Signature:", self.styles['Signature']))
            story.append(Spacer(1, 10))
            
            # Add signature line
            story.append(Paragraph("_" * 50, self.styles['CustomBody']))
            story.append(Paragraph(f"Name: {parent.full_name}", self.styles['CustomBody']))
            story.append(Paragraph(f"Phone: {parent.phone_number}", self.styles['CustomBody']))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['CustomBody']))
            story.append(Spacer(1, 20))
            
            # Add approval information if available
            if approval:
                story.append(Paragraph(f"Approval Method: {approval.approval_method}", self.styles['CustomBody']))
                story.append(Paragraph(f"Approved At: {approval.approved_at.strftime('%B %d, %Y at %I:%M %p')}", self.styles['CustomBody']))
                story.append(Spacer(1, 20))
        
        # Admin signature section
        if document.requires_admin_signature and document.admin_signed_by:
            story.append(Paragraph("Administrator Signature:", self.styles['Signature']))
            story.append(Spacer(1, 10))
            
            # Add signature line
            story.append(Paragraph("_" * 50, self.styles['CustomBody']))
            story.append(Paragraph(f"Name: {document.admin_signed_by.full_name}", self.styles['CustomBody']))
            story.append(Paragraph(f"Title: Administrator", self.styles['CustomBody']))
            story.append(Paragraph(f"Date: {document.admin_signed_at.strftime('%B %d, %Y')}", self.styles['CustomBody']))
            story.append(Spacer(1, 20))
        
        return story
    
    def add_verification_info(self, document, approval):
        """Add verification information to document"""
        story = []
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("DOCUMENT VERIFICATION", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 20))
        
        # Document information
        story.append(Paragraph(f"Document ID: {document.id}", self.styles['CustomBody']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.styles['CustomBody']))
        story.append(Paragraph(f"Document Hash: {document.document_hash}", self.styles['CustomBody']))
        
        # Approval information
        if approval:
            story.append(Paragraph(f"Approval ID: {approval.id}", self.styles['CustomBody']))
            story.append(Paragraph(f"Approval Hash: {approval.signature_hash}", self.styles['CustomBody']))
            if approval.certificate_hash:
                story.append(Paragraph(f"Certificate Hash: {approval.certificate_hash}", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        
        # QR code for verification (placeholder)
        story.append(Paragraph("Scan QR code below for verification:", self.styles['CustomBody']))
        story.append(Paragraph("[QR Code Placeholder]", self.styles['CustomBody']))
        
        return story
    
    def generate_signature_image(self, signature_data, width=400, height=200):
        """Generate signature image from canvas data"""
        try:
            # Create a white background
            image = Image.new('RGB', (width, height), 'white')
            
            # Parse signature data (assuming it's a list of points)
            if isinstance(signature_data, str):
                signature_data = json.loads(signature_data)
            
            if isinstance(signature_data, list) and len(signature_data) > 0:
                # Draw signature lines
                from PIL import ImageDraw
                draw = ImageDraw.Draw(image)
                
                for i in range(len(signature_data) - 1):
                    point1 = signature_data[i]
                    point2 = signature_data[i + 1]
                    
                    if 'x' in point1 and 'y' in point1 and 'x' in point2 and 'y' in point2:
                        draw.line(
                            [(point1['x'], point1['y']), (point2['x'], point2['y'])],
                            fill='black',
                            width=2
                        )
            
            # Convert to bytes
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            return ContentFile(buffer.getvalue(), name=f'signature_{hashlib.md5(str(signature_data).encode()).hexdigest()[:8]}.png')
            
        except Exception as e:
            print(f"Error generating signature image: {e}")
            return None
    
    def create_verification_qr_code(self, document, approval):
        """Create QR code for document verification"""
        try:
            # Create verification data
            verification_data = {
                'document_id': document.id,
                'document_hash': document.document_hash,
                'approval_id': approval.id if approval else None,
                'approval_hash': approval.signature_hash if approval else None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(json.dumps(verification_data))
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            return ContentFile(buffer.getvalue(), name=f'qr_code_{document.id}.png')
            
        except Exception as e:
            print(f"Error creating QR code: {e}")
            return None


class DocumentTemplateService:
    """Service for managing document templates"""
    
    @staticmethod
    def get_default_templates():
        """Get default document templates"""
        return {
            'approval_form': {
                'title': 'Event Participation Approval Form',
                'content_template': """
This document serves as an official approval form for student participation in the event: {{event_name}}.

EVENT DETAILS:
Event Name: {{event_name}}
Event Description: {{event_description}}
Event Date: {{event_date}}
Amount Required: {{event_amount}} {{currency}}
Due Date: {{due_date}}

STUDENT INFORMATION:
Student Name: {{student_name}}
Student ID: {{student_id}}
Class: {{student_class}}

PARENT/GUARDIAN INFORMATION:
Parent Name: {{parent_name}}
Contact Phone: {{parent_phone}}

SCHOOL INFORMATION:
School Name: {{school_name}}
School Address: {{school_address}}

By signing this document, I confirm that:
1. I have read and understood the event details
2. I approve my child's participation in this event
3. I agree to the payment terms and conditions
4. I understand the school's policies and procedures

I hereby give my consent for my child to participate in the above-mentioned event.
                """.strip()
            },
            'consent_form': {
                'title': 'Parental Consent Form',
                'content_template': """
CONSENT FORM FOR STUDENT PARTICIPATION

I, {{parent_name}}, hereby give my consent for my child {{student_name}} to participate in the following event:

Event: {{event_name}}
Date: {{event_date}}
Location: To be announced
Cost: {{event_amount}} {{currency}}

I understand that:
- This event is organized by {{school_name}}
- All school rules and regulations apply during the event
- The school will take reasonable care to ensure student safety
- I am responsible for any additional costs not covered by the event fee

Emergency Contact Information:
Name: {{parent_name}}
Phone: {{parent_phone}}

I confirm that all information provided is accurate and complete.
                """.strip()
            },
            'payment_agreement': {
                'title': 'Payment Agreement',
                'content_template': """
PAYMENT AGREEMENT

This agreement is between {{school_name}} and {{parent_name}} regarding payment for the event: {{event_name}}.

AGREEMENT DETAILS:
Event: {{event_name}}
Student: {{student_name}}
Amount: {{event_amount}} {{currency}}
Due Date: {{due_date}}

PAYMENT TERMS:
1. Payment is due by {{due_date}}
2. Late payments may incur additional charges
3. Payment can be made through the school's payment system
4. Receipts will be provided for all payments

I agree to make the payment as specified above and understand the payment terms and conditions.

Parent/Guardian Signature: _________________
Date: _________________
                """.strip()
            },
            'liability_waiver': {
                'title': 'Liability Waiver',
                'content_template': """
LIABILITY WAIVER AND RELEASE

I, {{parent_name}}, as the parent/guardian of {{student_name}}, hereby acknowledge and agree to the following terms regarding participation in the event: {{event_name}}.

RELEASE OF LIABILITY:
I understand that participation in this event involves inherent risks and I voluntarily assume all risks associated with such participation. I hereby release, discharge, and hold harmless {{school_name}}, its employees, agents, and representatives from any and all claims, damages, injuries, or losses arising from my child's participation in this event.

MEDICAL AUTHORIZATION:
I authorize the school to seek emergency medical treatment for my child if necessary during the event. I understand that I will be contacted as soon as possible in case of emergency.

I have read and understood this waiver and voluntarily agree to its terms.

Parent/Guardian Signature: _________________
Date: _________________
                """.strip()
            }
        }
    
    @staticmethod
    def get_template_by_type(template_type):
        """Get specific template by type"""
        templates = DocumentTemplateService.get_default_templates()
        return templates.get(template_type, templates['approval_form'])
