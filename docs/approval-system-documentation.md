# Approval System Documentation

## Overview

The Approval System is a comprehensive solution for managing event approvals with e-signatures, document generation, and digital certificates. It supports both smartphone and non-smartphone users through multiple approval methods.

## Features

### Core Features

- **Event Approval Management**: Parents must approve events before payment
- **E-Signature System**: Digital signatures with verification
- **Document Generation**: Automated PDF generation with letterheads
- **PIN-based Approval**: For parents without smartphones
- **Digital Certificates**: Cryptographic verification
- **Letterhead Management**: School branding integration

### Dynamic Configuration

- **Approval + Payment**: Both required
- **Approval Only**: No payment needed
- **Payment Only**: Direct payment without approval
- **Optional Approval**: Flexible approval requirements

## Database Models

### EventApproval

Tracks parent approvals for events with signature and PIN support.

### ParentApprovalPin

Manages secure 6-digit PINs for parent approvals.

### EventDocument

Generates and stores official documents with templates.

### DocumentSignature

Tracks document signatures with verification.

### DigitalCertificate

Manages cryptographic certificates for signature verification.

### SchoolLetterhead

Handles school letterhead uploads and management.

## API Endpoints

### Event Approvals

#### Request Approval

```http
POST /api/contributions/approvals/request_approval/
```

**Request Body:**

```json
{
  "event_id": 1,
  "student_id": 1,
  "approval_method": "signature",
  "signature_data": {...},
  "approval_pin": "123456",
  "approval_notes": "Optional notes"
}
```

**Response:**

```json
{
  "id": 1,
  "event": 1,
  "student": 1,
  "parent": 1,
  "status": "approved",
  "approval_method": "signature",
  "can_pay": true,
  "approved_at": "2024-01-15T10:30:00Z"
}
```

#### Verify PIN

```http
POST /api/contributions/approvals/{id}/verify_pin/
```

**Request Body:**

```json
{
  "pin": "123456",
  "approval_id": 1
}
```

#### Get Pending Approvals

```http
GET /api/contributions/approvals/pending_approvals/
```

#### Get Approved Events

```http
GET /api/contributions/approvals/approved_events/
```

### Parent Approval PINs

#### Set PIN

```http
POST /api/contributions/approval-pins/set_pin/
```

**Request Body:**

```json
{
  "pin": "123456"
}
```

#### Verify PIN

```http
POST /api/contributions/approval-pins/verify_pin/
```

**Request Body:**

```json
{
  "pin": "123456"
}
```

#### Reset PIN (Admin Only)

```http
POST /api/contributions/approval-pins/reset_pin/
```

**Request Body:**

```json
{
  "parent_id": 1
}
```

### School Letterheads

#### Upload Letterhead

```http
POST /api/contributions/letterheads/upload_letterhead/
```

**Request Body (multipart/form-data):**

```json
{
  "name": "Official Letterhead",
  "letterhead_type": "official",
  "department": "Administration",
  "file": "letterhead.png",
  "is_default": true
}
```

#### Set Default Letterhead

```http
POST /api/contributions/letterheads/{id}/set_default/
```

### Event Documents

#### Generate Document

```http
POST /api/contributions/documents/generate_document/
```

**Request Body:**

```json
{
  "event_id": 1,
  "document_type": "approval_form",
  "title": "Event Approval Form",
  "content_template": "Document template with placeholders...",
  "letterhead_id": 1,
  "requires_parent_signature": true,
  "requires_admin_signature": true
}
```

#### Sign Document (Admin)

```http
POST /api/contributions/documents/{id}/sign_document/
```

**Request Body (multipart/form-data):**

```json
{
  "signature_image": "signature.png",
  "stamp_image": "stamp.png"
}
```

#### Generate Personalized Content

```http
GET /api/contributions/documents/{id}/generate_personalized_content/?student_id=1&parent_id=1
```

### Document Signatures

#### Verify Signature (Admin)

```http
POST /api/contributions/document-signatures/{id}/verify_signature/
```

## User Flows

### 1. Event Creation Flow

1. **Admin/Teacher creates event**

   - Sets approval requirements
   - Configures payment settings
   - Sets deadlines

2. **System generates documents**

   - Creates approval documents
   - Applies school letterhead
   - Generates personalized content

3. **System creates approval requests**
   - For all eligible parents
   - Sends notifications

### 2. Parent Approval Flow

1. **Parent receives notification**

   - Views event details
   - Reviews required documents

2. **Parent chooses approval method**

   - **Digital Signature**: Draw on canvas or upload
   - **PIN**: Enter 6-digit code
   - **Both**: Signature + PIN for security

3. **System validates and processes**

   - Verifies signature/PIN
   - Generates digital certificate
   - Updates approval status

4. **Parent can now pay**
   - Payment enabled after approval
   - Document generated with signatures

### 3. Document Generation Flow

1. **System creates personalized document**

   - Replaces placeholders with data
   - Applies school letterhead
   - Adds signature sections

2. **Admin signs document**

   - Adds digital signature
   - Applies official stamp
   - Sets document as official

3. **Parent signature added**

   - When parent approves
   - Document updated with signatures

4. **Final document generated**
   - PDF with all signatures
   - QR code for verification
   - Digital certificate attached

### 4. PIN Management Flow

1. **Parent sets up PIN**

   - 6-digit numeric PIN
   - Securely hashed and stored
   - Salt added for security

2. **PIN used for approval**

   - Enter PIN to approve
   - Attempt limiting (3 tries)
   - 30-minute lockout on failure

3. **Admin can reset PIN**
   - Unlock locked PINs
   - Reset attempt counters
   - Emergency access

## Security Features

### Signature Security

- Cryptographic hashing of signature data
- Timestamp and IP tracking
- Digital certificates for verification
- Signature integrity checks

### PIN Security

- Salted hash storage
- Attempt limiting (3 attempts)
- 30-minute lockout period
- Admin override capabilities

### Document Security

- Document hashing for integrity
- Digital watermarking
- Certificate-based verification
- Audit trail for all signatures

## File Storage

### Directory Structure

```
media/
├── letterheads/
│   └── {school_id}/
├── signatures/
│   ├── {user_id}/
│   └── admin/
├── event_documents/
│   └── {event_id}/
├── document_signatures/
└── admin_signatures/
```

### File Types Supported

- **Letterheads**: PNG, JPG, PDF
- **Signatures**: PNG, JPG
- **Documents**: PDF
- **Stamps**: PNG with transparency

## Configuration

### Event Configuration

```python
# Event settings
requires_approval = True
requires_payment = True
approval_before_payment = True
approval_deadline = datetime
```

### Document Templates

- **approval_form**: Standard approval form
- **consent_form**: Parental consent
- **payment_agreement**: Payment terms
- **liability_waiver**: Legal waiver

### Letterhead Types

- **official**: Main school letterhead
- **department**: Department-specific
- **event**: Event-specific
- **stamp**: Digital stamps

## Error Handling

### Common Errors

- **Invalid PIN**: Wrong PIN entered
- **PIN Locked**: Too many failed attempts
- **No PIN Set**: Parent hasn't set PIN
- **Unauthorized**: Not authorized for student
- **Document Not Found**: Document doesn't exist

### Error Responses

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": "Additional details"
}
```

## Monitoring & Analytics

### Metrics Tracked

- Approval rates by method
- PIN usage statistics
- Document generation counts
- Signature verification rates
- Error rates and types

### Audit Trail

- All approval actions logged
- Signature verification history
- Document access tracking
- PIN usage logs

## Future Enhancements

### Planned Features

- **USSD Integration**: PIN-based approval via USSD
- **Biometric Signatures**: Fingerprint/face recognition
- **Blockchain Storage**: Immutable signature storage
- **Multi-language Support**: Multiple language templates
- **Advanced Analytics**: Detailed reporting dashboard

### Technical Improvements

- **Real-time Notifications**: WebSocket support
- **Mobile App**: Native mobile application
- **API Rate Limiting**: Enhanced security
- **Caching**: Performance optimization
- **CDN Integration**: Global document delivery

## Implementation Notes

### Dependencies

- **ReportLab**: PDF generation
- **Pillow**: Image processing
- **qrcode**: QR code generation
- **cryptography**: Digital certificates

### Performance Considerations

- **Async Processing**: Background document generation
- **File Compression**: Optimized storage
- **Caching**: Frequently accessed data
- **CDN**: Global file delivery

### Legal Compliance

- **Data Retention**: 7+ years for legal documents
- **Privacy Protection**: PII encryption
- **Audit Requirements**: Complete audit trails
- **GDPR Compliance**: Data protection regulations
