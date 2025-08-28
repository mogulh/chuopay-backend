# Product Requirements Document (PRD) with User Flows  
## MVP: Unofficial Payments Tracking System for Schools

*

## 1. Overview

*Product Name:* School Unofficial Payments Tracker (SUPT)  
*Purpose:* Build a transparent, easy-to-use SaaS platform for Kenyan schools to track unofficial payments such as trips and extracurricular fees, empowering parents and school administrators.  
*Tech Stack:* Backend - Django with PostgreSQL; Frontend - Next.js  
*Authentication:* Unified login enabling parents to view all children’s payments across multiple schools.

*

## 2. Goals

- Provide schools with event-based payment request creation including due dates, recurrence, and approval workflows.  
- Allow parents to receive notifications, view, and pay for unofficial charges per child.  
- Offer consolidated payments overview for parents with children in different schools and sections.  
- Clearly track payment status per event and generate administrative reports.

*

## 3. Key Features

### 3.1. Roles & Permissions

| Role          | Capabilities                                        |
|---------------|----------------------------------------------------|
| Parent        | View children list; view event payments per child; receive notifications; make payments |
| School Admin  | Manage school, sections, student groups; create/approve/publish payment events; view reports |
| Teacher       | Create payment events; submit for admin approval; view approvals status |

### 3.2. Authentication

- Single sign-on system with JWT tokens.  
- Parent accounts link to multiple children across different schools and sections.

### 3.3. Payment Events

- Event creation with: name, description, student group(s), amount, mandatory flag, due date, recurrence option (one-time, monthly, per term).  
- Approval workflow for teacher-submitted events.  
- Event publishing triggers notifications to parents.  
- Event payments tracked per student with status (Pending, Partial, Paid).  
- Receipt generation on payment.

### 3.4. Notifications & Deadlines

- Automated reminders before and after event due dates.  
- Overdue payments flagged visually on dashboards.  
- Admin override for deadlines.

*

## 4. User Flows

### 4.1. Parent User Flow

1. *Login* → Single parent authentication.  
2. *Children List View* → See all children’s schools, sections, unpaid payment counts, and totals.  
3. *Select Child* → Click on a child to see their detailed payment events.  
4. *View Child Events* → List all active and historical payment events with due dates, amounts, statuses.  
5. *Make Payment or Download Receipt* → Option to pay for outstanding events or review paid events with receipts.  
6. *Switch Child* → Easily switch to another child’s payment events via button/dropdown.

*

### 4.2. School Admin User Flow

1. *Login* → Admin authentication with role-based access.  
2. *School Settings* → Manage school profile, sections, and student groups.  
3. *Event Creation* → Create a payment event assigning to student groups, with amounts, mandatory status, due date, recurrence.  
4. *Approve Teacher Events* → Review and approve/reject events submitted by teachers.  
5. *Publish Event* → Publish events to notify parents and start payment tracking.  
6. *View Reports* → Generate payment reports by event, section, group with overdue highlights.

*

### 4.3. Teacher User Flow

1. *Login* → Teacher authentication.  
2. *Create Payment Event* → Populate event details and submit for admin approval.  
3. *Track Approval Status* → Monitor events’ approval status and respond to admin feedback.

*

## 5. System Architecture

- *Backend:* Django REST Framework handles APIs for authentication, events, payments, notifications.  
- *Database:* PostgreSQL with relational tables for Users, Schools, Sections, Students, Payment Events, Payments, Notifications.  
- *Frontend:* Next.js React app with three themed dashboards for Parents, Admins, Teachers.  
- *Notifications:* Email/in-app push via external service (e.g., SendGrid).  
- *Security:* JWT for session management, RBAC, encrypted data transmission.

*

## 6. Timeline (10 Weeks)

| Week | Milestones                                   |
|-------|---------------------------------------------|
| 1     | Finalize PRD and system design               |
| 2-4   | Backend API development (users, schools, events, approvals, payments, deadlines) |
| 5-7   | Frontend development (dashboards, event workflows, notifications UI) |
| 8     | Notification system and reminders integration |
| 9     | Testing, bug fixing, and stakeholder review  |
| 10    | MVP Launch and pilot onboarding               |

*

This PRD with detailed user flows will guide development of your MVP with clear navigation and role-based tasks, ensuring focus on key school unofficial payments problems while meeting your tech stack and authentication needs. 
