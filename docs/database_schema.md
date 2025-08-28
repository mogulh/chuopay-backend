# Database Schema Documentation

## Overview

This document describes the database schema for the Chuopay School Contribution Management Platform. The schema is designed to support multi-school operations with comprehensive user management, student tracking, contribution events, and notification systems.

## Core Entities

### 1. User Management (accounts app)

#### User

- **Purpose**: Custom user model with phone-based authentication
- **Key Fields**:
  - `phone_number`: Primary identifier (Kenyan format: +254XXXXXXXXX)
  - `role`: admin, teacher, parent
  - `firebase_uid`: Firebase authentication ID
  - `is_phone_verified`: Phone verification status
- **Relationships**: One-to-many with students (as parents)

#### UserProfile

- **Purpose**: Extended user information
- **Key Fields**:
  - `date_of_birth`, `gender`, `address`
  - `emergency_contact_*`: Emergency contact details
  - `notification_preferences`: JSON field for notification settings
  - `language_preference`: en/sw (English/Swahili)

#### PhoneVerification

- **Purpose**: SMS verification codes
- **Key Fields**:
  - `phone_number`, `verification_code`
  - `is_used`, `expires_at`
- **Security**: 6-digit codes with 10-minute expiration

### 2. School Management (contributions app)

#### School

- **Purpose**: Multi-school support
- **Key Fields**:
  - `name`, `address`, `city`, `county`
  - `currency`: Default currency (KES)
  - `timezone`: School timezone
- **Relationships**: One-to-many with groups, students, events

#### Group

- **Purpose**: Organize students (classes, clubs, activities)
- **Key Fields**:
  - `name`, `description`, `group_type`
  - `teacher`: Assigned teacher (optional)
  - `max_students`: Capacity limit
- **Types**: class, club, sport, activity, other
- **Relationships**: Many-to-many with students, events

#### Student

- **Purpose**: Student information and relationships
- **Key Fields**:
  - `first_name`, `last_name`, `date_of_birth`, `gender`
  - `student_id`: School's internal ID
  - `admission_date`, `is_active`
  - `medical_conditions`, `allergies`
- **Relationships**:
  - Many-to-many with groups (through StudentGroup)
  - Many-to-many with parents (through StudentParent)

#### StudentGroup

- **Purpose**: Student-group relationship with academic context
- **Key Fields**:
  - `joined_date`, `is_active`
  - `academic_year`, `term`
- **Constraints**: Unique per student-group-academic_year

#### StudentParent

- **Purpose**: Student-parent relationship with contact preferences
- **Key Fields**:
  - `relationship`: father, mother, guardian, etc.
  - `is_primary_contact`, `is_emergency_contact`
  - `receives_notifications`, `receives_sms`, `receives_email`
- **Constraints**: Unique per student-parent

### 3. Contribution Management (contributions app)

#### ContributionEvent

- **Purpose**: Payment requests and events
- **Key Fields**:
  - `name`, `description`, `event_type`
  - `amount`, `currency`
  - `has_tiers`: Optional payment tiers
  - `participation_type`: mandatory/optional
  - `due_date`, `event_date`
  - `is_active`, `is_published`
- **Types**: field_trip, fundraiser, uniform, textbook, activity, exam, other
- **Relationships**: Many-to-many with groups

#### ContributionTier

- **Purpose**: Optional payment tiers (e.g., with/without snacks)
- **Key Fields**:
  - `name`, `description`, `amount`
  - `is_default`: Default tier selection
- **Relationships**: Many-to-one with ContributionEvent

#### StudentContribution

- **Purpose**: Track individual student payments
- **Key Fields**:
  - `amount_required`, `amount_paid`
  - `payment_status`: pending, partial, paid, overdue, cancelled
  - `payment_date`, `payment_method`, `transaction_id`
  - `notes`
- **Calculated Fields**:
  - `amount_remaining`: amount_required - amount_paid
  - `payment_percentage`: (amount_paid / amount_required) \* 100
- **Relationships**: Many-to-one with Student, ContributionEvent, ContributionTier

#### ReminderLog

- **Purpose**: Track reminder notifications
- **Key Fields**:
  - `reminder_type`: sms, email, push, in_app
  - `message`, `status`
  - `sent_at`, `delivered_at`
  - `external_id`, `external_status`
- **Relationships**: Many-to-one with Student, User (parent), ContributionEvent

### 4. Notification System (notifications app)

#### NotificationTemplate

- **Purpose**: Reusable notification templates
- **Key Fields**:
  - `name`, `template_type`
  - `subject` (for email), `content`
  - `variables`: JSON field for available placeholders
  - `max_length` (for SMS)
- **Types**: sms, email, push, in_app

#### NotificationSchedule

- **Purpose**: Automated notification scheduling
- **Key Fields**:
  - `schedule_type`: immediate, scheduled, recurring
  - `scheduled_time`, `recurring_type`, `recurring_interval`
  - `event_types`, `payment_statuses`: Filter criteria
  - `days_before_due`: Days before event due date
- **Relationships**: Many-to-one with NotificationTemplate

#### NotificationLog

- **Purpose**: Track all sent notifications
- **Key Fields**:
  - `notification_type`, `status`
  - `sent_at`, `delivered_at`
  - `cost`, `currency` (for SMS billing)
  - `external_id`, `external_status`
- **Relationships**: Many-to-one with User, Student, ContributionEvent, NotificationTemplate, NotificationSchedule

#### SMSCredits

- **Purpose**: Track SMS billing and credits
- **Key Fields**:
  - `amount`: Number of SMS credits
  - `credit_type`: purchase, usage, refund, bonus
  - `cost`, `currency`
  - `provider`, `transaction_id`

#### NotificationSettings

- **Purpose**: User notification preferences
- **Key Fields**:
  - `receives_*`: General notification preferences
  - `payment_reminders`, `event_updates`, `general_announcements`
  - `quiet_hours_start`, `quiet_hours_end`
  - `max_notifications_per_day`

## Database Indexes

### Performance Optimization

The schema includes comprehensive indexes for common query patterns:

#### User Indexes

- `phone_number`: Fast phone number lookups
- `role_active`: Filter users by role and status
- `firebase_uid`: Firebase authentication

#### Student Indexes

- `student_id`: School's internal ID lookups
- `school_active`: Filter students by school and status
- `admission_date`: Date-based queries

#### Group Indexes

- `school_type`: Filter groups by school and type
- `teacher_active`: Teacher's assigned groups

#### Contribution Indexes

- `student_event`: Individual student contributions
- `payment_status`: Payment status queries
- `event_status`: Event-based payment status
- `due_date`: Overdue payment tracking

#### Notification Indexes

- `recipient_status`: User notification status
- `status_date`: Delivery tracking
- `external_id`: External service integration

## Data Integrity

### Constraints

- **Unique Constraints**:
  - User: `phone_number`, `firebase_uid`
  - Student: `student_id`
  - StudentGroup: `student`, `group`, `academic_year`
  - StudentParent: `student`, `parent`
  - StudentContribution: `student`, `event`
  - NotificationTemplate: `name`, `template_type`

### Foreign Key Relationships

- **Cascade Deletes**: School deletion removes all related data
- **Set Null**: Teacher removal from group
- **Restrict**: Prevent deletion of users with contributions

### Validation Rules

- **Phone Numbers**: Kenyan format (+254XXXXXXXXX)
- **Amounts**: Positive decimal values
- **Dates**: Logical date ordering (admission ≤ current ≤ due_date)
- **Status Transitions**: Valid payment status changes

## Scalability Considerations

### Multi-School Support

- All entities include school relationship
- Data isolation between schools
- School-specific settings (currency, timezone)

### Performance

- Comprehensive indexing strategy
- Efficient query patterns
- Pagination support for large datasets

### Security

- Role-based access control
- Phone number verification
- Audit trails for sensitive operations

## Migration Strategy

### Phase 1: Core Models

1. User authentication system
2. School and group management
3. Student and parent relationships

### Phase 2: Contribution System

1. Event creation and management
2. Payment tracking
3. Tier system implementation

### Phase 3: Notification System

1. Template management
2. Scheduling system
3. Delivery tracking

### Phase 4: Advanced Features

1. Analytics and reporting
2. Multi-language support
3. Advanced notification preferences
