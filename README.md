# Hostel Complaint Management System (HCMS)

A professional, robust, and secure platform designed to streamline grievance redressal within institutional hostels. HCMS provides a seamless bridge between Students, Wardens, Faculty members, and Master Administrators.

---

## 🚀 System Overview

HCMS is built with a focus on **Security, Dynamic Flexibility, and Resilience**. It replaces traditional paper-based or static systems with a dynamic "ticket-based" approach, ensuring every complaint is tracked, categorized, and resolved efficiently.

---

## 🎭 User Roles & Dashboards

### 👨‍🎓 1. Student Portal
The entry point for students to manage their hostel life and voice concerns.
- **Google OAuth Login**: Mandatory authentication using institutional domains (`@mitsgwl.ac.in`).
- **Profile Management**: Automatic extraction of name and enrollment number from Google profiles upon first login.
- **Dynamic Complaint Submission**: 
  - Students select from categories (e.g., Electricity, Water, Sanitation).
  - The system dynamically generates fields (dropdowns, text areas, or image uploads) based on the category selected.
- **Ticket Tracking**: Real-time status updates (Pending → In Progress → Resolved) via a clean, unified dashboard.

### 💂‍♂️ 2. Warden Portal
The operational core for managing specific hostel wings.
- **Pre-approval System**: Wardens upload lists of "Allowed Students" via CSV or manual entry.
- **Grievance Resolution**: Access to a dedicated dashboard to update ticket statuses and review dynamic details submitted by students.
- **Category Builder**: A powerful tool for Wardens to define *what* questions students must answer for specific complaints (e.g., adding a "Floor Number" requirement for 'Sanitation' issues).

### 👨‍🏫 3. Faculty Portal
Access for departmental faculty members.
- **Restricted Access**: Dedicated dashboard for faculty-specific tasks and viewing department-related notifications.
- **Secure Onboarding**: Faculty are added to the system via the Master Admin's pre-approved list.

### 👑 4. Master Admin Console
The supreme control center for institutional-level management.
- **Dynamic Staff Management**: Add/Edit Wardens and Faculty members.
- **Hostel Maintenance**: Create and manage hostels, with the ability to toggle hostels as "Active" or "Inactive". 
- **Database Search**: Query the entire system database (Staff, Students, Complaints) bypassing standard restrictions for administrative oversight.
- **Ticket Override Console**: Direct manual control to alter ticket statuses or erase records if necessary.

---

## 🛡️ Security & Architecture Features

### 🔐 1. Bulletproof Authentication
- **Dynamic Admin Control**: Admin priveleges are managed via a `.env` file. Adding or removing an email from the `ADMIN_EMAILS` variable instantly grants or revokes access across the database and UI.
- **Domain Enforcement**: Strict validation ensures only permitted email domains (`@mitsgwalior.in`, `@mitsgwl.ac.in`) can enter the system.
- **Silent Cleanup**: If an admin's access is revoked in the `.env`, their `AdminProfile` record is automatically deleted from the database upon their next interaction, leaving no "ghost" accounts.

### 🕵️ 2. URL Obfuscation (Ghost Routing)
- To prevent URL guessing (ID or Email scraping), the system uses a secure **`url_key`** for routing. 
- Example: Instead of `.../edit-warden/warden@email.com/`, the URL displays a random 8-character token like `.../edit-warden/a7G2f9K1/`, keeping identity data private.

### 💾 3. Hardened Database Design
The database is built on **PostgreSQL** with customized primary keys to prevent data duplication:
- **Students**: Use `enrollment_number` as the Primary Key.
- **Wardens**: Use `email` as the Primary Key for pre-approvals.
- **Safe Wrappers**: Every database query in the authentication pipeline is wrapped in safety logic. The system will **never crash** even if tables or columns are missing; it gracefully redirects to a safe landing page.

---

## 🛠️ Technical Stack

- **Backend**: Django 5.2.7 (Python)
- **Frontend**: Vanilla HTML5, Modern CSS (Glassmorphism & Dark Mode), Javascript
- **Database**: PostgreSQL
- **Security**: Python-Decouple (Environment management), Social-Auth-App-Django (Google OAuth 2.0)

---

## ⚙️ Environment Configuration (`.env`)

Management is simplified via a centralized environment file:
```env
# Google OAuth
GOOGLE_CLIENT_ID=your_id
GOOGLE_SECRET_KEY=your_secret

# Master Admins (Comma-separated)
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com

# Database (Production)
DB_NAME=hostel_portal
DB_USER=postgres
DB_PASSWORD=your_password
