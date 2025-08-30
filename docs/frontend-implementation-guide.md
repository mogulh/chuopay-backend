# Frontend Implementation Guide - Approval System

## Overview

This guide provides the necessary endpoints, flows, and UI/UX recommendations for implementing the approval system frontend.

## Required Endpoints

### Base URL

```
https://your-api-domain.com/api/contributions/
```

### Authentication

All endpoints require authentication via Bearer token:

```
Authorization: Bearer <access_token>
```

## Core Endpoints

### 1. Event Approvals

#### Get Pending Approvals

```http
GET /approvals/pending_approvals/
```

**Response:**

```json
[
  {
    "id": 1,
    "event": 1,
    "student": 1,
    "parent": 1,
    "status": "pending",
    "approval_method": "signature",
    "parent_name": "John Doe",
    "student_name": "Jane Doe",
    "event_name": "Field Trip to Museum",
    "can_pay": false,
    "is_expired": false,
    "requested_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-02-15T10:30:00Z"
  }
]
```

#### Request Approval

```http
POST /approvals/request_approval/
```

**Request Body:**

```json
{
  "event_id": 1,
  "student_id": 1,
  "approval_method": "signature",
  "signature_data": {
    "points": [
      { "x": 100, "y": 50 },
      { "x": 150, "y": 60 }
    ]
  },
  "approval_notes": "Optional notes"
}
```

#### Verify PIN for Approval

```http
POST /approvals/{id}/verify_pin/
```

**Request Body:**

```json
{
  "pin": "123456",
  "approval_id": 1
}
```

#### Get Approved Events

```http
GET /approvals/approved_events/
```

### 2. Parent Approval PINs

#### Set PIN

```http
POST /approval-pins/set_pin/
```

**Request Body:**

```json
{
  "pin": "123456"
}
```

#### Verify PIN

```http
POST /approval-pins/verify_pin/
```

**Request Body:**

```json
{
  "pin": "123456"
}
```

**Response:**

```json
{
  "is_valid": true,
  "message": "PIN verified successfully",
  "is_locked": false,
  "attempts_remaining": 3
}
```

### 3. Event Documents

#### Generate Document

```http
POST /documents/generate_document/
```

**Request Body:**

```json
{
  "event_id": 1,
  "document_type": "approval_form",
  "title": "Event Approval Form",
  "content_template": "Document template...",
  "letterhead_id": 1,
  "requires_parent_signature": true,
  "requires_admin_signature": true
}
```

#### Get Personalized Content

```http
GET /documents/{id}/generate_personalized_content/?student_id=1&parent_id=1
```

**Response:**

```json
{
  "content": "Personalized document content...",
  "student_name": "Jane Doe",
  "parent_name": "John Doe",
  "event_name": "Field Trip"
}
```

#### Sign Document (Admin)

```http
POST /documents/{id}/sign_document/
```

**Request Body (multipart/form-data):**

```json
{
  "signature_image": "file",
  "stamp_image": "file"
}
```

### 4. School Letterheads

#### Upload Letterhead

```http
POST /letterheads/upload_letterhead/
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

#### Get Letterheads

```http
GET /letterheads/
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "Official Letterhead",
    "letterhead_type": "official",
    "department": "Administration",
    "file": "/media/letterheads/1/letterhead.png",
    "is_default": true,
    "is_active": true
  }
]
```

## Required User Flows

### 1. Parent Dashboard Flow

#### Screen: Pending Approvals

- **Purpose**: Show all pending approvals for parent
- **Data Source**: `GET /approvals/pending_approvals/`
- **Actions**:
  - View approval details
  - Choose approval method
  - Navigate to approval form

#### Screen: Approval Form

- **Purpose**: Complete approval process
- **Components**:
  - Event details display
  - Document preview
  - Approval method selection
  - Signature canvas
  - PIN input field
  - Submit button

#### Screen: PIN Setup

- **Purpose**: Set up approval PIN
- **Data Source**: `POST /approval-pins/set_pin/`
- **Components**:
  - PIN input (6 digits)
  - Confirm PIN input
  - Security notice
  - Submit button

### 2. Admin Dashboard Flow

#### Screen: Event Management

- **Purpose**: Manage events and approvals
- **Data Source**: `GET /approvals/` (filtered by admin)
- **Actions**:
  - View all approvals
  - Generate documents
  - Sign documents
  - Reset PINs

#### Screen: Document Generation

- **Purpose**: Create documents for events
- **Data Source**: `POST /documents/generate_document/`
- **Components**:
  - Event selection
  - Document type selection
  - Template editor
  - Letterhead selection
  - Preview button

#### Screen: Document Signing

- **Purpose**: Sign documents as admin
- **Data Source**: `POST /documents/{id}/sign_document/`
- **Components**:
  - Document preview
  - Signature upload
  - Stamp upload
  - Sign button

### 3. Teacher Dashboard Flow

#### Screen: Class Approvals

- **Purpose**: View approvals for assigned classes
- **Data Source**: `GET /approvals/` (filtered by teacher groups)
- **Actions**:
  - View approval status
  - Generate reports
  - Send reminders

## UI/UX Requirements

### 1. Signature Canvas Component

#### Requirements:

- **Canvas Size**: 400x200px minimum
- **Drawing Tools**: Pen with adjustable thickness
- **Colors**: Black pen on white background
- **Actions**: Clear, Undo, Save
- **Data Format**: Array of points with x,y coordinates

#### Implementation:

```javascript
// Signature canvas component
class SignatureCanvas {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.ctx = this.canvas.getContext("2d");
    this.points = [];
    this.isDrawing = false;
  }

  startDrawing(e) {
    this.isDrawing = true;
    this.addPoint(e);
  }

  draw(e) {
    if (!this.isDrawing) return;
    this.addPoint(e);
    this.drawLine();
  }

  stopDrawing() {
    this.isDrawing = false;
  }

  addPoint(e) {
    const rect = this.canvas.getBoundingClientRect();
    const point = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
    this.points.push(point);
  }

  drawLine() {
    if (this.points.length < 2) return;

    const lastPoint = this.points[this.points.length - 2];
    const currentPoint = this.points[this.points.length - 1];

    this.ctx.beginPath();
    this.ctx.moveTo(lastPoint.x, lastPoint.y);
    this.ctx.lineTo(currentPoint.x, currentPoint.y);
    this.ctx.stroke();
  }

  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.points = [];
  }

  getSignatureData() {
    return this.points;
  }
}
```

### 2. PIN Input Component

#### Requirements:

- **Input Type**: Numeric only
- **Length**: Exactly 6 digits
- **Masking**: Show as dots/asterisks
- **Validation**: Real-time validation
- **Security**: Auto-clear on blur

#### Implementation:

```javascript
// PIN input component
class PINInput {
  constructor(container) {
    this.container = container;
    this.pin = "";
    this.maxLength = 6;
    this.createInput();
  }

  createInput() {
    this.input = document.createElement("input");
    this.input.type = "password";
    this.input.maxLength = this.maxLength;
    this.input.placeholder = "Enter 6-digit PIN";
    this.input.addEventListener("input", this.handleInput.bind(this));
    this.input.addEventListener("blur", this.handleBlur.bind(this));
    this.container.appendChild(this.input);
  }

  handleInput(e) {
    const value = e.target.value.replace(/\D/g, "");
    this.pin = value;
    this.input.value = value;
  }

  handleBlur() {
    // Auto-clear after delay for security
    setTimeout(() => {
      this.input.value = "";
    }, 1000);
  }

  getPIN() {
    return this.pin;
  }

  isValid() {
    return this.pin.length === this.maxLength;
  }
}
```

### 3. Document Preview Component

#### Requirements:

- **Format**: PDF viewer
- **Zoom**: Zoom in/out functionality
- **Download**: Download option
- **Print**: Print functionality
- **Responsive**: Mobile-friendly

#### Implementation:

```javascript
// Document preview component
class DocumentPreview {
  constructor(container, documentUrl) {
    this.container = container;
    this.documentUrl = documentUrl;
    this.createViewer();
  }

  createViewer() {
    // Use PDF.js or similar library
    this.viewer = document.createElement("iframe");
    this.viewer.src = this.documentUrl;
    this.viewer.style.width = "100%";
    this.viewer.style.height = "600px";
    this.viewer.style.border = "1px solid #ccc";
    this.container.appendChild(this.viewer);
  }

  download() {
    const link = document.createElement("a");
    link.href = this.documentUrl;
    link.download = "document.pdf";
    link.click();
  }

  print() {
    const printWindow = window.open(this.documentUrl);
    printWindow.print();
  }
}
```

## Error Handling

### 1. Network Errors

```javascript
// API error handler
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(endpoint, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Request failed");
    }

    return await response.json();
  } catch (error) {
    showError(error.message);
    throw error;
  }
}
```

### 2. Validation Errors

```javascript
// Form validation
function validateApprovalForm(data) {
  const errors = {};

  if (!data.event_id) {
    errors.event_id = "Event is required";
  }

  if (!data.student_id) {
    errors.student_id = "Student is required";
  }

  if (!data.approval_method) {
    errors.approval_method = "Approval method is required";
  }

  if (data.approval_method === "signature" && !data.signature_data) {
    errors.signature_data = "Signature is required";
  }

  if (data.approval_method === "pin" && !data.approval_pin) {
    errors.approval_pin = "PIN is required";
  }

  return errors;
}
```

## State Management

### 1. Approval State

```javascript
// Approval state management
class ApprovalState {
  constructor() {
    this.pendingApprovals = [];
    this.approvedEvents = [];
    this.currentApproval = null;
    this.loading = false;
    this.error = null;
  }

  async loadPendingApprovals() {
    this.loading = true;
    try {
      const data = await apiCall("/approvals/pending_approvals/");
      this.pendingApprovals = data;
    } catch (error) {
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  async requestApproval(approvalData) {
    this.loading = true;
    try {
      const data = await apiCall("/approvals/request_approval/", {
        method: "POST",
        body: JSON.stringify(approvalData),
      });
      this.currentApproval = data;
      await this.loadPendingApprovals();
      return data;
    } catch (error) {
      this.error = error.message;
      throw error;
    } finally {
      this.loading = false;
    }
  }
}
```

### 2. PIN State

```javascript
// PIN state management
class PINState {
  constructor() {
    this.pin = "";
    this.isLocked = false;
    this.attemptsRemaining = 3;
  }

  async setPIN(pin) {
    try {
      const data = await apiCall("/approval-pins/set_pin/", {
        method: "POST",
        body: JSON.stringify({ pin }),
      });
      return data;
    } catch (error) {
      throw error;
    }
  }

  async verifyPIN(pin) {
    try {
      const data = await apiCall("/approval-pins/verify_pin/", {
        method: "POST",
        body: JSON.stringify({ pin }),
      });

      this.isLocked = data.is_locked;
      this.attemptsRemaining = data.attempts_remaining;

      return data;
    } catch (error) {
      throw error;
    }
  }
}
```

## Responsive Design

### 1. Mobile-First Approach

```css
/* Mobile styles */
.approval-form {
  padding: 1rem;
}

.signature-canvas {
  width: 100%;
  max-width: 400px;
  height: 200px;
}

.pin-input {
  width: 100%;
  max-width: 200px;
}

/* Tablet styles */
@media (min-width: 768px) {
  .approval-form {
    padding: 2rem;
  }

  .signature-canvas {
    width: 400px;
  }
}

/* Desktop styles */
@media (min-width: 1024px) {
  .approval-form {
    padding: 3rem;
  }
}
```

### 2. Touch-Friendly Interface

```css
/* Touch-friendly buttons */
.btn {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
}

/* Touch-friendly inputs */
input,
select,
textarea {
  min-height: 44px;
  font-size: 16px;
  padding: 12px;
}
```

## Performance Optimization

### 1. Lazy Loading

```javascript
// Lazy load components
const ApprovalForm = lazy(() => import("./components/ApprovalForm"));
const DocumentPreview = lazy(() => import("./components/DocumentPreview"));

// Lazy load data
async function loadApprovalData(id) {
  const approval = await apiCall(`/approvals/${id}/`);
  const document = await apiCall(`/documents/${approval.document_id}/`);
  return { approval, document };
}
```

### 2. Caching

```javascript
// Cache frequently accessed data
class Cache {
  constructor() {
    this.cache = new Map();
    this.ttl = 5 * 60 * 1000; // 5 minutes
  }

  set(key, value) {
    this.cache.set(key, {
      value,
      timestamp: Date.now(),
    });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.value;
  }
}
```

## Testing Requirements

### 1. Unit Tests

- Signature canvas functionality
- PIN validation
- Form validation
- API error handling

### 2. Integration Tests

- Complete approval flow
- Document generation
- PIN management
- Error scenarios

### 3. E2E Tests

- Parent approval process
- Admin document management
- PIN setup and verification
- Mobile responsiveness

## Security Considerations

### 1. Input Validation

- Sanitize all user inputs
- Validate file uploads
- Check file types and sizes

### 2. Data Protection

- Encrypt sensitive data
- Secure token storage
- Auto-logout on inactivity

### 3. Error Handling

- Don't expose sensitive information in errors
- Log errors securely
- Provide user-friendly error messages
