# Dayflow Final Hackathon Product

# Dayflow — HR Management System

> **A unified Human Resource Management System for employees and administrators**

Dayflow is a web-based HR management system designed to bring everyday employee and administrative operations into one platform.

The current version is designed as a **local, working prototype** consisting of an HTML/JavaScript frontend, a Python/Flask backend, and a SQL database.

The project is structured so that the current local implementation can later be extended into a cloud-hosted version where multiple employees and administrators can access the same live database from different devices.

---

## 1. Project Overview

Dayflow aims to simplify the management of:

* Employee accounts
* Employee profiles
* Authentication
* Attendance
* Leave requests
* Payroll and salary information
* Administrative operations
* Employee records
* HR-related information

Instead of maintaining separate systems for attendance, employee information, leave management, and payroll, Dayflow provides a single interface.

The application has two primary user roles:

```text
Employee
   │
   ├── Profile
   ├── Attendance
   ├── Leave
   ├── Salary
   └── Personal information

Admin
   │
   ├── Employee management
   ├── Attendance monitoring
   ├── Leave management
   ├── Payroll management
   ├── Salary modification
   └── Administrative information
```

---

# 2. Current Architecture

The current application follows a basic three-layer architecture:

```text
┌──────────────────────────────┐
│          FRONTEND            │
│      HTML / CSS / JS         │
└──────────────┬───────────────┘
               │
               │ HTTP requests
               ▼
┌──────────────────────────────┐
│           BACKEND            │
│       Python / Flask         │
│                              │
│ Authentication               │
│ Business logic               │
│ Attendance processing        │
│ Leave processing             │
│ Payroll processing           │
└──────────────┬───────────────┘
               │
               │ SQL queries
               ▼
┌──────────────────────────────┐
│          DATABASE            │
│             SQL              │
│                              │
│ Employees                    │
│ Attendance                   │
│ Leave                        │
│ Payroll                      │
│ Other HR records             │
└──────────────────────────────┘
```

This separation is intentional.

The frontend is responsible primarily for presentation and user interaction.

The Python backend is responsible for processing requests and enforcing application logic.

The database is responsible for persistent storage.

---

# 3. Project Structure

The project is organized as follows:

```text
Dayflow/
│
├── frontend/
│   └── index.html
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── run_dayflow.bat
│
└── README.md
```

## `frontend/`

Contains the user-facing Dayflow interface.

### `index.html`

Contains the frontend interface, styling, and client-side interaction logic.

The frontend communicates with the Python backend rather than treating browser storage as the permanent database.

---

## `backend/`

Contains the Python application.

### `app.py`

The Flask application responsible for handling backend requests and connecting the frontend with the database.

The backend is responsible for operations such as:

* Authentication
* User handling
* Employee information
* Attendance
* Leave requests
* Payroll information
* Administrative operations
* Database interaction

### `requirements.txt`

Contains the Python packages required to run the backend.

### `.env.example`

Example environment configuration.

For a real deployment, sensitive credentials should be stored in environment variables rather than committed to GitHub.

---

## `database/`

Contains the SQL database definition and initial data.

### `schema.sql`

Defines the database structure.

### `seed.sql`

Provides initial/demo data for development and demonstration purposes.

---

## `run_dayflow.bat`

Windows convenience script intended to make starting the project easier.

---

# 4. Employee Features

## 4.1 Employee Login

Employees can authenticate using their generated Dayflow login credentials.

The application separates employee and administrator access.

An employee should not be able to simply select the administrator interface and gain administrative privileges.

Role information is handled by the backend rather than relying solely on what the user selects in the browser.

---

# 5. Employee ID Generation

Dayflow supports automatic generation of employee login IDs based on the project's employee-ID convention.

The intended structure is:

```text
OI + first two letters of first name
   + first two letters of last name
   + joining year
   + joining serial number
```

Conceptually:

```text
OIXXYYYYYYNNN
```

Where:

```text
OI       → Dayflow organization prefix
XX       → first two letters of first name
YY       → first two letters of last name
YYYY     → joining year
NNN      → joining serial number
```

The exact generated value depends on the employee information supplied when the account is created.

---

# 6. Password System

A newly created account can receive a system-generated initial password.

The user can subsequently change their password.

### Important

The generated/demo credentials included with the development version are intended only for local testing.

They must be changed before using Dayflow with real employee information.

A production deployment should additionally implement stronger password policies, password-reset mechanisms, account lockout/rate limiting, and secure session management.

---

# 7. Employee Dashboard

After authentication, employees can access their personal HR dashboard.

The dashboard is intended to provide a central location for:

* Employee information
* Attendance
* Leave information
* Salary information
* Profile information
* Other HR-related records

The objective is to eliminate the need for employees to contact HR for routine information that can be displayed directly through the system.

---

# 8. Employee Profiles

Dayflow provides employee profile information in a card-oriented interface.

Employee information can include basic details such as:

* Name
* Employee ID
* Department
* Designation
* Joining information
* Contact information
* Profile information

The exact information displayed depends on the data stored in the database.

---

# 9. Personal Profile

Employees have access to their own profile.

The profile area is designed to provide access to information such as:

### Basic information

* Name
* Employee ID
* Department
* Designation
* Joining date

### Private information

Depending on the implementation/data available:

* Contact details
* Personal information
* Other employee information

### Professional information

* Resume/CV information
* Job role
* Department
* Designation

### Salary information

Employees can view salary-related information that is permitted for their account.

---

# 10. Attendance System

Attendance is one of the central Dayflow features.

The original concept considered browser-based facial recognition. However, browser camera access and reliable facial recognition introduce additional technical, privacy, and deployment requirements.

The current implementation therefore uses a simpler **office attendance verification approach**.

The purpose is to provide a reliable hackathon demonstration without depending on a local machine's camera, browser permissions, or a facial-recognition model.

---

## Attendance Flow

The conceptual workflow is:

```text
Employee enters office
        ↓
Employee opens Dayflow
        ↓
Employee accesses Attendance
        ↓
Office verification mechanism
        ↓
Backend validates request
        ↓
Attendance record created
        ↓
Employee sees attendance status
```

Attendance information is stored through the backend/database rather than being permanently maintained only in browser state.

---

# 11. Attendance Records

Employees can view their attendance history.

Records may contain information such as:

* Date
* Attendance status
* Check-in information
* Verification information

The system should prevent obvious duplicate attendance submissions for the same employee/day where the backend rules enforce this.

---

# 12. Leave Management

Employees can submit leave requests.

A leave request can contain information such as:

* Employee
* Leave type
* Start date
* End date
* Reason
* Request status

The request can then be reviewed by an administrator.

Typical states include:

```text
Pending
   ↓
Approved

or

Pending
   ↓
Rejected
```

The admin may also provide a reviewer comment depending on the implementation.

---

# 13. Admin Interface

Administrators receive a different interface from employees.

The admin interface is intended to provide greater visibility and control over the organization's HR data.

Typical administrative functionality includes:

* Employee management
* Attendance monitoring
* Leave management
* Salary/payroll management
* Employee information
* HR overview
* Administrative controls

The separation between employee and administrator functionality is a core part of the application.

---

# 14. Admin Employee Management

Administrators can view employee information through the administrative interface.

The employee overview is intended to provide a quick understanding of:

* Employee identity
* Department
* Designation
* Attendance status
* Leave information
* Salary information
* Other HR data

This provides the basis for expanding Dayflow into a larger HR operations dashboard.

---

# 15. Admin Attendance Monitoring

Administrators can monitor employee attendance records.

This allows HR/management to inspect attendance information without requiring individual employees to manually provide their records.

Future versions can expand this into:

* Attendance analytics
* Monthly attendance reports
* Late-arrival tracking
* Early departure tracking
* Absence analysis
* Department-level attendance statistics
* Exportable attendance reports

---

# 16. Payroll and Salary Management

Payroll is one of the more flexible parts of the Dayflow design.

Administrators should be able to modify employee compensation rather than having salary represented as one fixed number.

A salary structure can contain multiple components.

For example:

```text
Basic Salary
+ HRA
+ Allowances
+ Bonus
+ Overtime
----------------
Gross Salary
- Deductions
----------------
Net Salary
```

Possible components include:

* Basic salary
* Monthly wage
* HRA
* Allowances
* Bonus
* Overtime
* Deductions
* Other salary components

---

# 17. Salary Flexibility

The purpose of the payroll structure is to allow administrators to represent different compensation models.

For example:

### Employee A

```text
Basic Salary
HRA
Transport Allowance
Performance Bonus
```

### Employee B

```text
Basic Salary
HRA
Overtime
Shift Allowance
Deductions
```

This is more flexible than storing only:

```text
salary = 50000
```

Instead, salary can be represented as a collection of components.

This approach also makes future payroll expansion easier.

---

# 18. Salary Revisions

Salary changes should be treated as meaningful HR events rather than simply overwriting the previous value.

A future production implementation should maintain:

```text
Previous salary
      ↓
Salary revision
      ↓
New salary
      ↓
Effective date
```

This allows organizations to maintain historical payroll information.

---

# 19. Admin Salary Access

Salary information is sensitive.

Therefore, salary-related functionality should be restricted to authorized administrators.

Employees should only be able to access their own permitted salary information.

An employee should not be able to modify:

* Their salary
* Another employee's salary
* Payroll records
* Salary components
* Administrative payroll settings

These permissions must ultimately be enforced by the backend.

---

# 20. Database

The database provides persistent storage for Dayflow.

The SQL structure is designed around HR-related entities rather than storing the entire application state in the browser.

Conceptually:

```text
Users / Employees
       │
       ├────────── Attendance
       │
       ├────────── Leave
       │
       ├────────── Payroll
       │
       └────────── Profile information
```

This allows the project to move from a local demonstration to a cloud database without completely redesigning the application.

---

# 21. Running Dayflow Locally

## Requirements

Install:

* Python 3
* Git
* A modern web browser

Python should be available from the terminal.

Check:

```bash
python --version
```

If your system uses `python3`:

```bash
python3 --version
```

---

# 22. Clone the Repository

Clone your GitHub repository:

```bash
git clone YOUR_REPOSITORY_URL
```

Enter the project:

```bash
cd Dayflow
```

If your repository uses a different directory name, enter that directory instead.

---

# 23. Create a Virtual Environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# 24. Install Dependencies

Move into the backend:

```bash
cd backend
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Then return to the project root when required:

```bash
cd ..
```

---

# 25. Database Setup

The project contains:

```text
database/
├── schema.sql
└── seed.sql
```

`schema.sql` defines the database structure.

`seed.sql` contains development/demo data.

The backend is designed to initialize/use the database as described by the supplied project configuration.

If you modify the database schema manually, ensure that the backend queries are updated accordingly.

---

# 26. Start the Backend

From the backend directory:

```bash
cd backend
python app.py
```

The Flask development server should start.

The local application is then normally accessible through the localhost address displayed by Flask.

For example:

```text
http://127.0.0.1:5000
```

Open that address in a browser.

---

# 27. Windows Shortcut

For Windows development, the project also contains:

```text
run_dayflow.bat
```

This is intended to simplify starting the application.

If the batch file does not work on a particular machine, use the manual Python commands described above.

---

# 28. Demo Workflow

For a hackathon demonstration, the recommended sequence is:

### Step 1 — Open Dayflow

Start the Flask backend and open the application in the browser.

### Step 2 — Employee Login

Log in using one of the seeded employee accounts.

### Step 3 — Employee Dashboard

Demonstrate:

* Employee profile
* Attendance
* Leave
* Salary
* Personal information

### Step 4 — Attendance

Demonstrate the office attendance verification flow.

### Step 5 — Leave

Create a leave request.

### Step 6 — Logout

Log out of the employee account.

### Step 7 — Admin Login

Log in as an administrator.

### Step 8 — Employee Management

Show employee information.

### Step 9 — Leave Approval

Open the pending leave request and approve/reject it.

### Step 10 — Payroll

Open an employee's salary information.

Modify a salary component.

Demonstrate how the resulting compensation changes.

This is one of the strongest demonstrations of the system's backend/database architecture.

---

# 29. Important Development Limitation

The current version is primarily a **hackathon/local prototype**.

It should not be treated as a production HR platform without additional security, infrastructure, testing, and compliance work.

In particular, the current project should not be populated with real employee information unless appropriate production security controls have been implemented.

---

# 30. Attendance Limitations

The current attendance mechanism is intentionally simpler than a full biometric system.

Potential limitations include:

* Office verification may not prove the physical identity of the employee by itself.
* A shared attendance code could potentially be shared.
* Browser/device location cannot always be trusted as a security boundary.
* Network conditions can affect requests.
* Duplicate or repeated submissions need server-side validation.
* Time-zone differences need to be handled explicitly in a multi-location deployment.
* Attendance corrections require an administrative workflow in a production system.

---

# 31. Facial Recognition Limitation

The project originally considered camera-based facial recognition.

A production facial-recognition system would require considerably more than simply opening a browser camera.

It would require considerations including:

* Camera permissions
* Browser compatibility
* Face detection
* Face matching
* Employee enrollment
* Image/template storage
* Spoof/liveness detection
* Lighting conditions
* Multiple faces
* Privacy
* Consent
* Data protection
* False positives
* False negatives

Therefore, the current attendance approach deliberately avoids making the hackathon dependent on unreliable browser camera functionality.

A future version could introduce biometric verification as an optional attendance mechanism rather than making it the only way to record attendance.

---

# 32. Authentication Limitations

The current authentication system is designed for demonstration/development.

A production implementation should additionally include:

* Strong password policy
* Password reset
* Email verification
* Account lockout/rate limiting
* Secure session handling
* Session expiration
* Multi-factor authentication
* Audit logging
* CSRF protection
* Secure cookie configuration
* HTTPS
* Secure secret management

---

# 33. Payroll Edge Cases

Payroll systems become complicated quickly.

Important cases for future implementation include:

### Salary changes during a month

If an employee's salary changes halfway through a month, the system must determine whether to:

* Prorate the salary
* Apply the new salary from the next payroll cycle
* Split the payroll period

### Leave without pay

Unpaid leave may affect net salary.

### Overtime

Overtime may require:

```text
Hours worked
×
Overtime rate
=
Overtime compensation
```

### Bonuses

Bonuses may be:

* One-time
* Monthly
* Quarterly
* Performance-based

### Deductions

Deductions may include multiple categories.

### Negative net salary

The system should prevent invalid payroll calculations where deductions exceed allowable compensation unless a legitimate payroll policy supports such a scenario.

---

# 34. Leave Edge Cases

Possible edge cases include:

* Employee requests overlapping leave
* Employee requests leave for a past date
* Employee submits duplicate requests
* Leave exceeds available balance
* Admin approves an already rejected request
* Admin rejects an already approved request
* Employee cancels a request
* Employee's leave balance changes after approval

A production implementation should explicitly define rules for each case.

---

# 35. Attendance Edge Cases

Important cases include:

* Employee submits attendance twice
* Employee attempts attendance outside permitted hours
* Employee changes device time
* Network disconnects after submitting attendance
* Two requests arrive simultaneously
* Employee attempts attendance after leaving the office
* Employee forgets to check in
* Employee forgets to check out
* Employee works remotely
* Employee travels between office locations

These should be handled through backend rules rather than frontend validation alone.

---

# 36. Database Edge Cases

Potential issues include:

* Duplicate employee IDs
* Duplicate email addresses
* Deleted employees with historical attendance
* Salary history being overwritten
* Missing foreign-key relationships
* Partial transactions
* Database corruption
* Concurrent updates
* Database migration issues

Production deployment should use database backups, migrations, transactions, and monitoring.

---

# 37. Security Considerations

Dayflow handles sensitive information including employee identity, attendance, and salary.

A production deployment should therefore use:

```text
HTTPS
+
Secure authentication
+
Role-based authorization
+
Password hashing
+
Environment secrets
+
Database access controls
+
Audit logs
+
Backups
+
Input validation
```

Never commit real:

* Passwords
* API keys
* Database credentials
* Secret keys
* Employee personal information

to GitHub.

The `.env.example` file is intended to document configuration without exposing real secrets.

---

# 38. Current vs Future Architecture

## Current version

```text
Employee/Admin Browser
          ↓
     Local Flask
          ↓
      Local SQL
```

This is suitable for:

* Development
* Testing
* Hackathon demonstration
* Local evaluation

---

# 39. Future Online Version

The `online-version` Git branch is intended to evolve Dayflow into a cloud-based application.

The target architecture is:

```text
                Internet
                   │
        ┌──────────┴──────────┐
        │                     │
   Employee                Admin
        │                     │
        └──────────┬──────────┘
                   ↓
             Web Frontend
                   ↓
              Flask API
                   ↓
             Cloud Database
```

The important change is that the database will no longer live only on the demonstration machine.

Multiple devices will be able to access the same backend.

For example:

```text
Laptop A
Employee 1
      │
      ├──────────────┐
                     ↓
                 Cloud API
                     ↓
                Cloud SQL
                     ↑
                     │
      ┌──────────────┘
      │
Laptop B
Admin
```

An administrator changing an employee's salary would therefore update the central database.

The employee could then see that updated information from another device.

---

# 40. Future Online-Version Goals

The planned cloud version can introduce:

* Cloud-hosted frontend
* Cloud-hosted Flask backend
* Managed SQL database
* HTTPS
* Production authentication
* Role-based authorization
* Multi-device access
* Secure environment variables
* Database backups
* Automated deployments
* Audit logs
* Better attendance verification
* Advanced analytics
* Payroll history
* Notification system
* Email integration
* Optional biometric attendance
* Multiple office locations

---

# 41. Git Branch Strategy

The repository uses two important development directions.

## `main`

Contains the stable hackathon/local version.

Avoid making risky experimental changes here immediately before a demonstration.

## `online-version`

Contains the future cloud-oriented implementation.

Create/update the branch using:

```bash
git checkout main
git pull origin main

git checkout -b online-version

git push -u origin online-version
```

After that, cloud development can happen independently.

---

# 42. Recommended Git Workflow

Before starting work:

```bash
git checkout main
git pull origin main
```

Switch to the online branch:

```bash
git checkout online-version
```

After making changes:

```bash
git status
git add .
git commit -m "Describe your change"
git push
```

For example:

```bash
git add .
git commit -m "Connect payroll module to cloud database"
git push
```

---

# 43. Troubleshooting

## Python command not found

Try:

```bash
python3 --version
```

If Python is installed but not detected, ensure Python has been added to your system PATH.

---

## Flask does not start

Make sure the virtual environment is active:

```powershell
venv\Scripts\activate
```

Then reinstall dependencies:

```bash
pip install -r backend/requirements.txt
```

---

## Port already in use

Another application may already be using the Flask port.

Stop the other process or configure Flask to use another port.

---

## Database errors

Check:

* Database configuration
* Schema
* Environment variables
* File permissions
* SQL initialization
* Backend configuration

---

## Frontend loads but buttons do not work

Check that:

1. The Flask backend is running.
2. The browser is accessing the application through the backend.
3. The API requests are reaching Flask.
4. The browser developer console does not show JavaScript errors.
5. The backend terminal does not show request errors.

---

# 44. Development Philosophy

Dayflow is intentionally being developed incrementally.

The current goal is not to claim that every enterprise HR feature has already been solved.

Instead, the project demonstrates a foundation that can evolve:

```text
Prototype
   ↓
Working Backend
   ↓
Persistent Database
   ↓
Cloud Deployment
   ↓
Production Security
   ↓
Scalable HR Platform
```

This allows the project to remain understandable while providing a clear path toward a production-grade system.

---

# 45. Hackathon Vision

The long-term vision for Dayflow is to make HR operations less fragmented.

Instead of:

```text
Attendance spreadsheet
       +
Leave email
       +
Payroll spreadsheet
       +
Employee records
       +
Manual HR communication
```

Dayflow aims to provide:

```text
                 DAYFLOW
                    │
       ┌────────────┼────────────┐
       │            │            │
   Attendance     Leave       Payroll
       │            │            │
       └────────────┼────────────┘
                    │
             Employee Profile
                    │
             Administrative
                 Dashboard
```

The current application is the foundation for that system.

The online version is the next stage: transforming the local HR management prototype into an accessible, multi-user cloud platform.

---

# 46. Disclaimer

This repository represents a hackathon/prototype implementation.

It is not intended to be used as a production HR, payroll, biometric, or employee-data management system without additional security review, testing, legal/compliance review, infrastructure hardening, and operational controls.

Do not use real sensitive employee information in the development/demo environment.

---

# 47. Quick Start

For the shortest possible setup:

```bash
git clone YOUR_REPOSITORY_URL
cd Dayflow

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r backend/requirements.txt

cd backend
python app.py
```

Then open the local address shown by Flask in your browser.

---

## Dayflow

**Current stage:** Hackathon prototype

**Architecture:** HTML/JavaScript → Python/Flask → SQL

**Next stage:** Cloud-hosted multi-user HR platform

**Development branch:** `online-version`
