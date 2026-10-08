# MediCare – Healthcare Management System (OPD & Clinic Management)

A beginner-friendly, complete digital Healthcare Management System designed for Outpatient Department (OPD) and Clinic Administration. Built with Python 3, Flask, and SQLite.

---

## 1. Project Purpose

This project is an academic mini project for an Outpatient Department (OPD) / Clinic Management System. It manages the complete patient outpatient lifecycle:
```
Patient Registration → Doctor Selection → Appointment Booking → Doctor Consultation → Prescription → Billing → Patient History
```
It eliminates duplicate bookings, keeps patient records permanently in an SQLite database, and provides role-based access for Patients, Doctors, and Administrators.

---

## 2. Technologies Used

- **Language:** Python 3 (Python 3.10+)
- **Backend Framework:** Flask (3.0+)
- **Database:** SQLite3 (`medicare.db`, built-in Python `sqlite3` module)
- **Templating:** Jinja2
- **Frontend:** Pure HTML5, CSS3, and basic vanilla JavaScript
- **Theme:** Clean white & teal healthcare UI with responsive layout and printable styles

---

## 3. Key Features

### Patient Role
- **Permanent Registration:** Stores demographics, phone, email, address, blood group, emergency contact in SQLite and auto-generates sequential Patient ID (`PAT001`, `PAT002`...).
- **Doctor Directory:** Browse physicians with real-time specialization filtering.
- **Appointment Booking:** Select doctor, date, and time slot with conflict detection (prevents booking an already reserved slot).
- **Appointment Management:** View upcoming/completed appointments, cancel scheduled appointments.
- **Patient Profile:** View and update personal information directly in SQLite.
- **Medical History:** Read-only access to doctor-created consultation records, diagnosis, and notes.
- **Digital Prescriptions (℞):** View and print electronic prescriptions with clinic header, diagnosis, medicine table, and doctor advice.
- **Billing:** View consultation fee invoices with one-click simulated payment ("Mark as Paid").

### Doctor Role
- **Doctor Console:** Displays today's queue, upcoming visits, completed consultations, and total patients.
- **Queue Management:** See appointments assigned specifically to the logged-in physician.
- **Clinical Consultation Desk:** View patient details, blood group, reason for visit, and medical history.
- **Assessment & Rx Builder:** Enter symptoms, diagnosis, clinical notes, and dynamically add/remove prescribed medicines (name, dosage, frequency, duration, instructions).
- **Automated Workflow:** Completing a consultation updates appointment to `Completed`, archives consultation, generates digital Rx, and creates an OPD bill.

### Administrator Role
- **Executive Dashboard:** Real-time metrics on total patients, doctors, appointments, completed visits, and pending bills.
- **Doctor CRUD:** Add new doctors, edit credentials/schedules, delete doctors.
- **Patient Directory:** Comprehensive listing of all registered patients.
- **Master Appointment Registry:** Full overview of all clinic bookings with status tracking.
- **Financial Ledger:** Track all invoices, fee collections, and payment statuses.

---

## 4. Database Schema (`medicare.db`)

The system uses a relational SQLite database with 7 interconnected tables:

1. **`users`**
   - `id` (INTEGER PRIMARY KEY)
   - `username` (TEXT UNIQUE)
   - `password_hash` (TEXT)
   - `role` (TEXT: 'PATIENT', 'DOCTOR', 'ADMIN')
   - `created_at` (TIMESTAMP)

2. **`patients`**
   - `patient_id` (TEXT PRIMARY KEY, e.g. 'PAT001')
   - `user_id` (INTEGER FOREIGN KEY)
   - `name`, `age`, `gender`, `dob`, `phone`, `email`, `address`, `blood_group`, `emergency_contact`, `created_at`

3. **`doctors`**
   - `doctor_id` (TEXT PRIMARY KEY, e.g. 'DOC001')
   - `user_id` (INTEGER FOREIGN KEY)
   - `name`, `specialization`, `qualification`, `experience`, `phone`, `email`, `consultation_fee`, `available_days`, `available_time`

4. **`appointments`**
   - `appointment_id` (TEXT PRIMARY KEY, e.g. 'APT001')
   - `patient_id` (TEXT FOREIGN KEY)
   - `doctor_id` (TEXT FOREIGN KEY)
   - `appointment_date`, `time_slot`, `reason`, `status` ('Scheduled', 'Completed', 'Cancelled'), `created_at`

5. **`consultations`**
   - `consultation_id` (TEXT PRIMARY KEY, e.g. 'CON001')
   - `appointment_id` (TEXT FOREIGN KEY)
   - `patient_id` (TEXT FOREIGN KEY)
   - `doctor_id` (TEXT FOREIGN KEY)
   - `symptoms`, `diagnosis`, `doctor_notes`, `advice`, `created_at`

6. **`prescriptions`**
   - `prescription_id` (TEXT PRIMARY KEY, e.g. 'PRE001')
   - `consultation_id`, `appointment_id`, `patient_id`, `doctor_id`, `date`, `medicines_json`, `instructions`, `created_at`

7. **`bills`**
   - `bill_id` (TEXT PRIMARY KEY, e.g. 'BILL001')
   - `appointment_id`, `patient_id`, `doctor_id`, `consultation_fee`, `date`, `payment_status` ('Pending', 'Paid'), `created_at`

---

## 5. Folder Structure

```
medicare/
├── app.py                     # Main Flask application with all routes and database logic
├── init_db.py                 # Standalone script to initialize/reset medicare.db
├── medicare.db                # SQLite database file (pre-populated with demo data)
├── requirements.txt           # Minimal Python dependencies (Flask, Werkzeug)
├── README.md                  # Comprehensive documentation and run guide
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Base layout with navbar, footer, and flash messages
│   ├── index.html             # Homepage / Landing page
│   ├── login.html             # Role-based login with demo quick-fill buttons
│   ├── register.html          # Patient registration form
│   ├── dashboard.html         # Unified dashboard for Patient and Doctor
│   ├── doctors.html           # Doctor directory with specialization filter
│   ├── appointment.html       # Appointment booking form with conflict check
│   ├── appointments.html      # Appointment list with cancel action
│   ├── profile.html           # Patient profile view & edit
│   ├── consultation.html      # Doctor clinical desk with dynamic prescription builder
│   ├── prescription.html      # Printable digital prescription (℞)
│   ├── medical_history.html   # Chronological read-only consultation history
│   ├── bills.html             # Billing invoice list with "Mark as Paid" action
│   └── admin.html             # Admin portal (metrics, doctor CRUD, patients, bills)
│
└── static/
    ├── css/
    │   └── style.css          # Clean healthcare theme styling
    └── js/
        └── script.js          # Helper scripts (dynamic medicine rows, demo quick-fill)
```

---

## 6. Installation Guide

### Prerequisites
- Python 3.10 or higher installed on your computer.

### Step 1: Open Terminal / Command Prompt
Navigate to the `medicare` project directory:
```bash
cd medicare
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 7. How to Run the Application

Start the Flask server:
```bash
python app.py
```

Then open your browser and navigate to:
```
http://127.0.0.1:5000
```

*Note:* `medicare.db` is automatically created and seeded if it does not exist. You can also re-initialize it anytime by running `python init_db.py`.

---

## 8. Demo Login Credentials

For demonstration, academic presentations, and testing:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full administrative control, Doctor CRUD, metrics |
| **Doctor** | `doctor1` | `doctor123` | Dr. Arun Kumar (General Medicine) |
| **Doctor** | `doctor2` | `doctor123` | Dr. Priya Sharma (Cardiology) |
| **Patient** | `patient1` | `patient123` | Rahul Sharma (ID: PAT001) |
| **Patient** | `patient2` | `patient123` | Sunita Patel (ID: PAT002) |

---

## 9. Academic Mini-Project Demonstration Workflow

1. **Sign In as Patient (`patient1` / `patient123`)**:
   - Check Dashboard metrics.
   - Click **Book Appointment**, select Dr. Priya Sharma (Cardiology) on an upcoming date and time slot.
   - The system checks for conflicting bookings in SQLite, creates `APT003`, and saves it.

2. **Sign In as Doctor (`doctor2` / `doctor123`)**:
   - See the new appointment in Today's Queue.
   - Click **Consult** to open the clinical desk.
   - Review patient details (Age: 34, Blood: O+).
   - Enter symptoms, diagnosis, advice, and add prescribed medications.
   - Click **Complete Consultation**.
   - Appointment status updates to `Completed`, Rx `PRE002` is saved, and Bill `BILL002` is generated.

3. **Sign Back In as Patient (`patient1`)**:
   - Open **Medical History** to see the recorded consultation.
   - Click **View Prescription** and use **Print Prescription**.
   - Open **Bills & Receipts** and click **Mark as Paid** to simulate payment collection.

4. **Sign In as Admin (`admin` / `admin123`)**:
   - View updated hospital statistics, total patients, completed visits, and revenue collected.
   - Add a new doctor or manage existing faculty.
