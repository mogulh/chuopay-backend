**Technical Product Requirements Document (Technical PRD)**

**Product Name:** Chuopay
**Audience:** Engineering & Technical Team
**Version:** 1.0
**Owner:** \[Lead Engineer / CTO]
**Date:** \[Insert Date]

---

### **1. Objective**

This document outlines the technical specifications, system architecture, APIs, infrastructure, and security protocols for the Chuopay fintech application, which facilitates parent-to-school financial transactions for non-official expenses.

---

### **2. Architecture Overview**

* **Frontend:**

  * Mobile App: Flutter (Android-first with iOS roadmap)
  * Web Dashboard (School Admins): ReactJS / Next.js

* **Backend:**

  * Framework: Django REST Framework (Python)
  * API-driven microservices architecture
  * Authentication: JWT with role-based access control (RBAC)

* **Database:**

  * PostgreSQL for relational data (users, transactions, schools)
  * Redis for caching and session handling

* **Payments Integration:**

  * M-Pesa API (STK push, B2C, C2B)
  * Future: Flutterwave, card payments

---

### **3. Core Modules**

* **User Module:**

  * Roles: Parent, Student, Teacher-Agent, Admin
  * KYC verification (ID upload + phone verification)
  * Linked accounts for multiple students and co-parents

* **Wallet Module:**

  * Parent wallet top-up and balance
  * Transaction ledger with status and history
  * Withdrawal approval by teacher

* **Request System:**

  * Students submit itemized fund requests
  * Parents approve or deny with notes

* **School Admin Module:**

  * Monitor payments by category
  * Exportable reports (CSV, PDF)
  * Agent management (assign/remove)

---

### **4. APIs**

* **Authentication:** `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`
* **Wallet:** `/api/wallet/topup`, `/api/wallet/balance`, `/api/wallet/history`
* **Requests:** `/api/request/submit`, `/api/request/approve`, `/api/request/status`
* **School Admin:** `/api/admin/transactions`, `/api/admin/agents`, `/api/admin/export`
* **Multi-User Access:** `/api/student/share_access`, `/api/student/switch`, `/api/student/invite_guardian`

All APIs require token authentication and follow RESTful design principles.

---

### **5. Infrastructure & DevOps**

* **Cloud Provider:** AWS / GCP
* **Containerization:** Docker + Docker Compose
* **CI/CD:** GitHub Actions + Docker Hub + Railway/Render/Heroku (for staging)
* **Monitoring:** Prometheus + Grafana or Sentry for error logging

---

### **6. Security Protocols**

* **Encryption:** HTTPS (TLS 1.2+), AES-256 at rest
* **Data Protection:** All PII encrypted in DB
* **2FA:** Optional for parents, required for admin users
* **Rate Limiting:** Prevent abuse of sensitive endpoints (auth, payments)

---

### **7. Milestones for Tech Team**

* **Week 1-2:** Setup repo, CI/CD, base Django/Flutter boilerplates
* **Week 3-4:** Build auth, user roles, wallet
* **Week 5-6:** Integrate M-Pesa, test STK and C2B flows
* **Week 7-8:** Student requests + teacher verification module
* **Week 9-10:** School admin dashboard + reporting
* **Week 11-12:** Security testing, bug fixing, staging launch

---

### **8. Testing Strategy**

* **Unit Tests:** Coverage >90% for backend logic
* **Integration Tests:** Payment flows, request handling
* **Manual QA:** UI testing on real Android devices
* **Security Audit:** By third-party auditor before launch

---

### **9. Risks and Dependencies**

* M-Pesa API rate limits and approval delays
* Device compatibility for student-facing app
* Reliance on external KYC/ID verification service

---

### **10. User Stories**

**Parent:**

* As a parent, I want to top up my Chuopay wallet using M-Pesa so that I can fund my child’s school needs.
* As a parent, I want to receive notifications when my child submits a request so I can approve or decline promptly.
* As a parent, I want to view my transaction history so I can track how funds are being used.
* As a parent, I want to manage multiple students in different schools so I can use one account for all children.
* As a parent, I want to switch between student profiles from a single dashboard so I don’t need to log out and back in.
* As a parent, I want to invite a co-parent to access a student’s profile with permissions so that we can share responsibility without sharing credentials.

**Student:**

* As a student, I want to submit a money request with item details so that I can buy needed school items.
* As a student, I want to track the status of my request so I know when the money is available.

**Teacher-Agent:**

* As a teacher-agent, I want to view withdrawal requests and verify the student’s identity so I can release funds safely.
* As a teacher-agent, I want to see which parents have approved disbursements for students so I can manage funds correctly.

**School Admin:**

* As a school admin, I want to view all incoming transactions so I can reconcile unofficial payments.
* As a school admin, I want to export reports in CSV or PDF format so I can submit them to accounting or auditors.
* As a school admin, I want to assign or remove teacher-agents to ensure responsible fund handling.

---

**Prepared by:** \[Lead Engineer Name]
**Approved by:** \[CTO Name]
**Date:** \[Insert Date]

