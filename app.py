"""
=============================================================================
MediCare – Healthcare Management System
Outpatient Department (OPD) & Clinic Management System

Technology Stack:
- Python 3
- Flask
- SQLite (built-in sqlite3)
- HTML, CSS, Vanilla JavaScript

Workflow:
Patient Registration -> Doctor Selection -> Appointment Booking ->
Doctor Consultation -> Prescription -> Billing -> Patient History

Easy setup for College Demonstration:
    pip install -r requirements.txt
    python app.py
    Open: http://127.0.0.1:5000
=============================================================================
"""

import os
import sqlite3
import json
from datetime import datetime, date
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g
)

# Optional Werkzeug password hashing with simple fallback for beginners
try:
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    import hashlib
    def generate_password_hash(password):
        return 'sha256$' + hashlib.sha256(password.encode('utf-8')).hexdigest()
    def check_password_hash(p_hash, password):
        if p_hash.startswith('sha256$'):
            return p_hash == 'sha256$' + hashlib.sha256(password.encode('utf-8')).hexdigest()
        return p_hash == password

def verify_password(stored_hash, candidate_password):
    """Verifies candidate password against stored hash or plain password for demo."""
    if stored_hash == candidate_password:
        return True
    if stored_hash.startswith('sha256$'):
        import hashlib
        return stored_hash == 'sha256$' + hashlib.sha256(candidate_password.encode('utf-8')).hexdigest()
    try:
        from werkzeug.security import check_password_hash
        return check_password_hash(stored_hash, candidate_password)
    except Exception:
        return stored_hash == candidate_password


# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'medicare-college-project-secret-key-2026'

# Path to SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_connection():
    """
    Connect to the SQLite database.
    row_factory = sqlite3.Row enables dict-like column access: row['column_name'].
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates all required SQLite tables automatically if they do not exist,
    and seeds sample doctors, patients, and admin accounts.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (id, name, email, password, role)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT,
            password TEXT NOT NULL,
            password_hash TEXT,
            role TEXT NOT NULL, -- 'patient', 'doctor', 'admin'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Patients Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            user_id INTEGER,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            dob TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            emergency_contact TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # 3. Doctors Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id TEXT PRIMARY KEY,
            doctor_id TEXT,
            user_id INTEGER,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            qualification TEXT NOT NULL,
            experience TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            consultation_fee REAL NOT NULL,
            available_days TEXT NOT NULL,
            available_time TEXT NOT NULL,
            clinic_room TEXT DEFAULT 'OPD Room 101',
            status TEXT DEFAULT 'Available',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # 4. Appointments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            appointment_id TEXT,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Scheduled', -- 'Scheduled', 'Completed', 'Cancelled'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    """)

    # 5. Consultations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id TEXT PRIMARY KEY,
            consultation_id TEXT,
            appointment_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            doctor_notes TEXT,
            advice TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id),
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    """)

    # 6. Prescriptions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id TEXT PRIMARY KEY,
            prescription_id TEXT,
            consultation_id TEXT,
            appointment_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            date TEXT NOT NULL,
            diagnosis TEXT,
            medicine TEXT NOT NULL,
            dosage TEXT NOT NULL,
            instructions TEXT,
            doctor_advice TEXT,
            medicines_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id),
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    """)

    # 7. Bills Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id TEXT PRIMARY KEY,
            bill_id TEXT,
            appointment_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            consultation_fee REAL NOT NULL,
            date TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'Paid'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id),
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    """)

    conn.commit()

    # Check if doctors are populated
    cursor.execute("SELECT COUNT(*) FROM doctors")
    doc_count = cursor.fetchone()[0]

    if doc_count == 0:
        print("[MediCare] Seeding initial sample doctors, patients, and accounts into SQLite database...")
        
        # 1. Admin Account
        admin_hash = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO users (name, email, username, password, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Hospital Administrator', 'admin@medicare.com', 'admin', 'admin123', admin_hash, 'admin'))

        # 2. Realistic Sample Doctors requested in brief:
        # Dr. Anjali Sharma – General Medicine
        # Dr. Rahul Kumar – Cardiology
        # Dr. Priya Reddy – Dermatology
        # Dr. Arjun Rao – Orthopedics
        # Dr. Sneha Patel – Pediatrics
        # Dr. Vikram Singh – ENT
        demo_doctors = [
            ('DOC001', 'Dr. Anjali Sharma', 'General Medicine', 'MBBS, MD (Medicine)', '12 Years', '+91 98765 11001', 'anjali.sharma@medicare.com', 'doctor1', 40.0, 'Mon, Tue, Wed, Thu, Fri', '09:00 AM - 01:00 PM', 'OPD Room 101'),
            ('DOC002', 'Dr. Rahul Kumar', 'Cardiology', 'MD, DM (Cardiology), FACC', '15 Years', '+91 98765 11002', 'rahul.kumar@medicare.com', 'doctor2', 70.0, 'Mon, Wed, Fri', '10:00 AM - 02:00 PM', 'OPD Room 102'),
            ('DOC003', 'Dr. Priya Reddy', 'Dermatology', 'MD (Dermatology), DNB', '9 Years', '+91 98765 11003', 'priya.reddy@medicare.com', 'doctor3', 50.0, 'Tue, Thu, Sat', '02:00 PM - 05:30 PM', 'OPD Room 103'),
            ('DOC004', 'Dr. Arjun Rao', 'Orthopedics', 'MS (Ortho), M.Ch', '14 Years', '+91 98765 11004', 'arjun.rao@medicare.com', 'doctor4', 60.0, 'Mon, Tue, Thu, Fri', '09:30 AM - 01:30 PM', 'OPD Room 104'),
            ('DOC005', 'Dr. Sneha Patel', 'Pediatrics', 'MD (Pediatrics), DCH', '8 Years', '+91 98765 11005', 'sneha.patel@medicare.com', 'doctor5', 45.0, 'Mon, Wed, Thu, Sat', '10:00 AM - 03:00 PM', 'OPD Room 105'),
            ('DOC006', 'Dr. Vikram Singh', 'ENT', 'MS (ENT), DLO', '11 Years', '+91 98765 11006', 'vikram.singh@medicare.com', 'doctor6', 50.0, 'Tue, Wed, Fri, Sat', '09:00 AM - 01:00 PM', 'OPD Room 106'),
        ]

        doc_pass_hash = generate_password_hash('doctor123')
        for doc_id, name, spec, qual, exp, ph, email, u_name, fee, days, t_slot, room in demo_doctors:
            cursor.execute("""
                INSERT INTO users (name, email, username, password, password_hash, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, email, u_name, 'doctor123', doc_pass_hash, 'doctor'))
            u_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO doctors (id, doctor_id, user_id, name, specialization, qualification, experience, phone, email, consultation_fee, available_days, available_time, clinic_room, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, doc_id, u_id, name, spec, qual, exp, ph, email, fee, days, t_slot, room, 'Available'))

        # 3. Sample Patient Account
        pat_pass_hash = generate_password_hash('patient123')
        cursor.execute("""
            INSERT INTO users (name, email, username, password, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('John Doe', 'patient@medicare.com', 'patient1', 'patient123', pat_pass_hash, 'patient'))
        pat_u_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO patients (id, patient_id, user_id, name, age, gender, dob, phone, email, address, blood_group, emergency_contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('PAT001', 'PAT001', pat_u_id, 'John Doe', 32, 'Male', '1994-04-12', '+1 (555) 234-5678', 'patient@medicare.com', '742 Evergreen Terrace, Springfield', 'O+', '+1 (555) 999-0000'))

        # Sample Completed Consultation and Prescription for John Doe
        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO appointments (id, appointment_id, patient_id, doctor_id, appointment_date, time_slot, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('APT001', 'APT001', 'PAT001', 'DOC001', today_str, '10:00 AM', 'Persistent dry cough and mild seasonal allergy', 'Completed'))

        cursor.execute("""
            INSERT INTO consultations (id, consultation_id, appointment_id, patient_id, doctor_id, symptoms, diagnosis, doctor_notes, advice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('CON001', 'CON001', 'APT001', 'PAT001', 'DOC001', 'Dry cough for 3 days, mild nasal congestion', 'Acute Upper Respiratory Tract Irritation', 'Chest clear on auscultation, throat mildly hyperemic', 'Drink warm water with honey, avoid cold beverages, follow medication regimen'))

        meds_data = [
            {"name": "Cetirizine 10 mg", "dosage": "1 tablet", "frequency": "Once daily at night", "duration": "5 days", "instructions": "After dinner"},
            {"name": "Dextromethorphan Syrup", "dosage": "10 ml", "frequency": "Twice daily", "duration": "4 days", "instructions": "After meals"}
        ]

        cursor.execute("""
            INSERT INTO prescriptions (id, prescription_id, consultation_id, appointment_id, patient_id, doctor_id, date, diagnosis, medicine, dosage, instructions, doctor_advice, medicines_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('PRE001', 'PRE001', 'CON001', 'APT001', 'PAT001', 'DOC001', today_str, 'Acute Upper Respiratory Tract Irritation', 'Cetirizine 10 mg, Dextromethorphan Syrup', 'As prescribed', 'Follow with warm water', 'Rest and hydration advised', json.dumps(meds_data)))

        cursor.execute("""
            INSERT INTO bills (id, bill_id, appointment_id, patient_id, doctor_id, consultation_fee, date, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('BILL001', 'BILL001', 'APT001', 'PAT001', 'DOC001', 40.0, today_str, 'Paid'))

        conn.commit()

    conn.close()


# Initialize database automatically on startup
init_db()


# =============================================================================
# HELPER DECORATORS & FUNCTIONS
# =============================================================================

def get_current_user():
    """Returns the current user dict from session or None."""
    if 'user_id' not in session:
        return None
    return {
        'id': session.get('user_id'),
        'name': session.get('name'),
        'email': session.get('email'),
        'role': session.get('role', 'patient'),
        'patient_id': session.get('patient_id'),
        'doctor_id': session.get('doctor_id')
    }


# =============================================================================
# ROUTES & VIEWS
# =============================================================================

# 1. Landing Page
@app.route('/')
def index():
    """
    Renders the MediCare healthcare homepage.
    Preserves exact branding, hero section, OPD workflow card, and services.
    """
    conn = get_db_connection()
    doctors = conn.execute("SELECT * FROM doctors LIMIT 6").fetchall()
    conn.close()
    return render_template('index.html', doctors=doctors)


# 2. User Authentication: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login using Flask sessions.
    Supports role selection: patient, doctor, admin.
    """
    if request.method == 'POST':
        login_input = request.form.get('username', '').strip() or request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'patient').strip().lower()

        if not login_input or not password:
            flash("Please enter your credentials.", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        # Find user matching email OR username, and case-insensitive role
        user = conn.execute("""
            SELECT * FROM users 
            WHERE (LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?))
              AND LOWER(role) = LOWER(?)
        """, (login_input, login_input, role)).fetchone()

        if user and verify_password(user['password_hash'] or user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role'].upper()

            # Store role-specific IDs in session
            if session['role'] == 'PATIENT':
                pat = conn.execute("SELECT * FROM patients WHERE user_id = ? OR email = ?", (user['id'], user['email'])).fetchone()
                if pat:
                    session['patient_id'] = pat['id']
                else:
                    session['patient_id'] = 'PAT001'
            elif session['role'] == 'DOCTOR':
                doc = conn.execute("SELECT * FROM doctors WHERE user_id = ? OR email = ?", (user['id'], user['email'])).fetchone()
                if doc:
                    session['doctor_id'] = doc['id']
                else:
                    session['doctor_id'] = 'DOC001'

            conn.close()
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            flash("Invalid email or password.", "danger")
            return render_template('login.html')

    return render_template('login.html')


# 3. Patient Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registers a new patient and stores details permanently in SQLite.
    Generates a unique Patient ID (e.g. PAT002).
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', 'Male')
        dob = request.form.get('dob', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        blood_group = request.form.get('blood_group', 'O+')
        emergency_contact = request.form.get('emergency_contact', '').strip()
        username = request.form.get('username', '').strip() or email.split('@')[0]
        password = request.form.get('password', '').strip()

        if not all([name, age, phone, email, password]):
            flash("Please fill all required fields.", "danger")
            return render_template('register.html')

        conn = get_db_connection()
        # Check if email/username already registered
        existing = conn.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?)", (email, username)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email or username already exists. Please login.", "warning")
            return redirect(url_for('login'))

        # Generate unique Patient ID
        count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        patient_id = f"PAT{str(count + 1).zfill(3)}"

        pass_hash = generate_password_hash(password)

        # 1. Insert into users
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, username, password, password_hash, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, username, password, pass_hash, 'patient'))
        user_id = cursor.lastrowid

        # 2. Insert into patients
        cursor.execute("""
            INSERT INTO patients (id, patient_id, user_id, name, age, gender, dob, phone, email, address, blood_group, emergency_contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, patient_id, user_id, name, int(age), gender, dob, phone, email, address, blood_group, emergency_contact))

        conn.commit()
        conn.close()

        # Log in newly registered patient
        session.clear()
        session['user_id'] = user_id
        session['name'] = name
        session['email'] = email
        session['role'] = 'PATIENT'
        session['patient_id'] = patient_id

        flash(f"Registration successful! Your Patient ID is {patient_id}.", "success")
        return redirect(url_for('dashboard'))

    return render_template('register.html')


# 4. Logout
@app.route('/logout')
def logout():
    """Clears user session and returns to homepage."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('index'))


# 5. Quick Role Switcher (Convenient for evaluator presentations)
@app.route('/switch-role/<role>')
def switch_role(role):
    """
    Instantly switches role to PATIENT, DOCTOR, or ADMIN
    for smooth college project demonstrations.
    """
    role = role.lower()
    conn = get_db_connection()
    if role == 'admin':
        admin = conn.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1").fetchone()
        if admin:
            session.clear()
            session['user_id'] = admin['id']
            session['name'] = admin['name']
            session['email'] = admin['email']
            session['role'] = 'ADMIN'
    elif role == 'doctor':
        doc = conn.execute("SELECT * FROM doctors LIMIT 1").fetchone()
        if doc:
            session.clear()
            session['user_id'] = doc['user_id']
            session['name'] = doc['name']
            session['email'] = doc['email']
            session['role'] = 'DOCTOR'
            session['doctor_id'] = doc['id']
    else: # patient
        pat = conn.execute("SELECT * FROM patients LIMIT 1").fetchone()
        if pat:
            session.clear()
            session['user_id'] = pat['user_id']
            session['name'] = pat['name']
            session['email'] = pat['email']
            session['role'] = 'PATIENT'
            session['patient_id'] = pat['id']
    conn.close()
    flash(f"Switched role to {session.get('role', 'PATIENT')}.", "info")
    return redirect(url_for('dashboard'))


# 6. Doctors Directory
@app.route('/doctors')
def doctors():
    """
    Retrieves doctors from SQLite.
    Includes filtering by specialization.
    """
    selected_spec = request.args.get('specialization', 'All')
    conn = get_db_connection()

    # Get distinct specializations
    specs = [row['specialization'] for row in conn.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization").fetchall()]

    if selected_spec and selected_spec != 'All':
        doc_list = conn.execute("SELECT * FROM doctors WHERE specialization = ? ORDER BY name", (selected_spec,)).fetchall()
    else:
        doc_list = conn.execute("SELECT * FROM doctors ORDER BY name").fetchall()

    conn.close()
    return render_template('doctors.html', doctors=doc_list, specializations=specs, selected_specialization=selected_spec)


# 7. Book Appointment
@app.route('/book-appointment', methods=['GET', 'POST'], endpoint='book_appointment')
@app.route('/appointment', methods=['GET', 'POST'], endpoint='appointment')
@app.route('/appointment/book', methods=['GET', 'POST'], endpoint='appointment_book')
def book_appointment():
    """
    Appointment booking workflow.
    Validates availability and prevents double booking of doctor's time slot.
    """
    conn = get_db_connection()
    min_date = date.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        # Ensure user is logged in as a patient; if not, use demo patient
        if 'user_id' not in session or session.get('role') != 'PATIENT':
            pat = conn.execute("SELECT * FROM patients LIMIT 1").fetchone()
            if pat:
                session['user_id'] = pat['user_id']
                session['name'] = pat['name']
                session['role'] = 'PATIENT'
                session['patient_id'] = pat['id']
            else:
                conn.close()
                flash("Please log in as a patient to book an appointment.", "warning")
                return redirect(url_for('login', role='PATIENT'))

        patient_id = session.get('patient_id')
        doctor_id = request.form.get('doctor_id', '').strip()
        apt_date = request.form.get('appointment_date', '').strip()
        time_slot = request.form.get('time_slot', '').strip()
        reason = request.form.get('reason', '').strip()

        if not all([doctor_id, apt_date, time_slot, reason]):
            flash("Please fill all required fields.", "danger")
            doctors_list = conn.execute("SELECT * FROM doctors").fetchall()
            conn.close()
            return render_template('appointment.html', doctors=doctors_list, min_date=min_date, selected_doctor_id=doctor_id)

        # Conflict Detection: Prevent booking the exact same doctor and slot on that date
        conflict = conn.execute("""
            SELECT id FROM appointments 
            WHERE doctor_id = ? AND appointment_date = ? AND time_slot = ? AND status != 'Cancelled'
        """, (doctor_id, apt_date, time_slot)).fetchone()

        if conflict:
            flash(f"This time slot ({time_slot} on {apt_date}) is already booked for this doctor. Please choose a different slot.", "warning")
            doctors_list = conn.execute("SELECT * FROM doctors").fetchall()
            conn.close()
            return render_template('appointment.html', doctors=doctors_list, min_date=min_date, selected_doctor_id=doctor_id)

        # Generate unique Appointment ID (e.g. APT002)
        count = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        appointment_id = f"APT{str(count + 1).zfill(3)}"

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (id, appointment_id, patient_id, doctor_id, appointment_date, time_slot, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Scheduled')
        """, (appointment_id, appointment_id, patient_id, doctor_id, apt_date, time_slot, reason))

        conn.commit()
        conn.close()

        flash(f"Appointment booked successfully! Your Appointment ID is {appointment_id}.", "success")
        return redirect(url_for('dashboard'))

    # GET request
    selected_doc = request.args.get('doctor_id', '')
    doctors_list = conn.execute("SELECT * FROM doctors").fetchall()
    conn.close()
    return render_template('appointment.html', doctors=doctors_list, min_date=min_date, selected_doctor_id=selected_doc)


# 8. User Dashboard (Role-Governed)
@app.route('/dashboard')
def dashboard():
    """
    Renders appropriate dashboard based on user role (PATIENT, DOCTOR, ADMIN).
    Displays appointments, statistics, prescriptions, and bills from SQLite.
    """
    if 'user_id' not in session:
        # Default to Patient John Doe for seamless demonstration if accessed directly
        return redirect(url_for('switch_role', role='patient'))

    role = session.get('role', 'PATIENT')
    conn = get_db_connection()

    if role == 'PATIENT':
        patient_id = session.get('patient_id', 'PAT001')
        patient = conn.execute("SELECT * FROM patients WHERE id = ? OR patient_id = ?", (patient_id, patient_id)).fetchone()

        # Appointments
        appointments = conn.execute("""
            SELECT a.*, a.id as appointment_id, d.name as doctor_name, d.specialization, d.consultation_fee
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id OR a.doctor_id = d.doctor_id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC, a.time_slot DESC
        """, (patient_id,)).fetchall()

        upcoming_count = sum(1 for a in appointments if a['status'] == 'Scheduled')
        completed_count = sum(1 for a in appointments if a['status'] == 'Completed')

        prescriptions = conn.execute("SELECT COUNT(*) FROM prescriptions WHERE patient_id = ?", (patient_id,)).fetchone()[0]
        bills = conn.execute("SELECT COUNT(*) FROM bills WHERE patient_id = ?", (patient_id,)).fetchone()[0]

        conn.close()
        return render_template('dashboard.html',
                               patient=patient,
                               appointments=appointments,
                               upcoming_count=upcoming_count,
                               completed_count=completed_count,
                               prescriptions_count=prescriptions,
                               bills_count=bills)

    elif role == 'DOCTOR':
        doctor_id = session.get('doctor_id', 'DOC001')
        doctor = conn.execute("SELECT * FROM doctors WHERE id = ? OR doctor_id = ?", (doctor_id, doctor_id)).fetchone()

        today_str = date.today().strftime('%Y-%m-%d')
        appointments = conn.execute("""
            SELECT a.*, a.id as appointment_id, p.name as patient_name, p.age, p.gender, p.blood_group, p.phone
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id OR a.patient_id = p.patient_id
            WHERE a.doctor_id = ?
            ORDER BY a.appointment_date ASC, a.time_slot ASC
        """, (doctor_id,)).fetchall()

        today_count = sum(1 for a in appointments if a['appointment_date'] == today_str and a['status'] == 'Scheduled')
        upcoming_count = sum(1 for a in appointments if a['status'] == 'Scheduled')
        completed_count = sum(1 for a in appointments if a['status'] == 'Completed')
        total_patients = len(set(a['patient_id'] for a in appointments))

        conn.close()
        return render_template('dashboard.html',
                               doctor=doctor,
                               appointments=appointments,
                               today_count=today_count,
                               upcoming_count=upcoming_count,
                               completed_count=completed_count,
                               total_patients=total_patients)

    else: # ADMIN
        conn.close()
        return redirect(url_for('admin'))


# 9. My Appointments
@app.route('/appointments', endpoint='appointments')
@app.route('/my-appointments', endpoint='my_appointments')
def appointments():
    """Lists appointments for the logged-in patient or doctor."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    role = session.get('role')

    if role == 'PATIENT':
        patient_id = session.get('patient_id')
        apt_list = conn.execute("""
            SELECT a.*, a.id as appointment_id, d.name as doctor_name, d.specialization, d.consultation_fee
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id OR a.doctor_id = d.doctor_id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC
        """, (patient_id,)).fetchall()
    else:
        doctor_id = session.get('doctor_id')
        apt_list = conn.execute("""
            SELECT a.*, a.id as appointment_id, p.name as patient_name, p.phone, p.blood_group, p.age, p.gender
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id OR a.patient_id = p.patient_id
            WHERE a.doctor_id = ?
            ORDER BY a.appointment_date DESC
        """, (doctor_id,)).fetchall()

    conn.close()
    return render_template('appointments.html', appointments=apt_list)


# 10. Cancel Appointment
@app.route('/cancel-appointment/<appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancels a scheduled appointment."""
    conn = get_db_connection()
    conn.execute("UPDATE appointments SET status = 'Cancelled' WHERE id = ? OR appointment_id = ?", (appointment_id, appointment_id))
    conn.commit()
    conn.close()
    flash(f"Appointment {appointment_id} has been cancelled.", "info")
    return redirect(url_for('dashboard'))


# 11. Doctor Consultation Desk
@app.route('/consultation/<appointment_id>', methods=['GET', 'POST'])
def consultation(appointment_id):
    """
    Clinical consultation workflow for doctors.
    Records symptoms, diagnosis, and notes into SQLite consultations.
    Creates digital prescription and automated bill.
    Updates appointment status to 'Completed'.
    """
    conn = get_db_connection()

    apt = conn.execute("""
        SELECT a.*, a.id as appointment_id, p.name as patient_name, p.id as patient_id, p.age, p.gender, p.blood_group, p.phone,
               d.name as doctor_name, d.id as doctor_id, d.specialization, d.qualification, d.consultation_fee
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id OR a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.id OR a.doctor_id = d.doctor_id
        WHERE a.id = ? OR a.appointment_id = ?
    """, (appointment_id, appointment_id)).fetchone()

    if not apt:
        conn.close()
        flash("Appointment record not found.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        symptoms = request.form.get('symptoms', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()
        doctor_notes = request.form.get('doctor_notes', '').strip()
        advice = request.form.get('advice', '').strip()

        # Medicine array from builder
        med_names = request.form.getlist('med_name[]')
        med_dosages = request.form.getlist('med_dosage[]')
        med_freqs = request.form.getlist('med_frequency[]')
        med_durations = request.form.getlist('med_duration[]')
        med_instructions = request.form.getlist('med_instructions[]')

        medicines_list = []
        for i in range(len(med_names)):
            if med_names[i].strip():
                medicines_list.append({
                    'name': med_names[i].strip(),
                    'dosage': med_dosages[i].strip() if i < len(med_dosages) else '',
                    'frequency': med_freqs[i].strip() if i < len(med_freqs) else '',
                    'duration': med_durations[i].strip() if i < len(med_durations) else '',
                    'instructions': med_instructions[i].strip() if i < len(med_instructions) else ''
                })

        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor = conn.cursor()

        # 1. Create Consultation
        c_count = conn.execute("SELECT COUNT(*) FROM consultations").fetchone()[0]
        con_id = f"CON{str(c_count + 1).zfill(3)}"

        cursor.execute("""
            INSERT INTO consultations (id, consultation_id, appointment_id, patient_id, doctor_id, symptoms, diagnosis, doctor_notes, advice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (con_id, con_id, apt['appointment_id'], apt['patient_id'], apt['doctor_id'], symptoms, diagnosis, doctor_notes, advice))

        # 2. Create Prescription
        p_count = conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
        pre_id = f"PRE{str(p_count + 1).zfill(3)}"
        med_summary = ", ".join(m['name'] for m in medicines_list) if medicines_list else "Standard regimen"

        cursor.execute("""
            INSERT INTO prescriptions (id, prescription_id, consultation_id, appointment_id, patient_id, doctor_id, date, diagnosis, medicine, dosage, instructions, doctor_advice, medicines_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pre_id, pre_id, con_id, apt['appointment_id'], apt['patient_id'], apt['doctor_id'], today_str, diagnosis, med_summary, "Per schedule", "Follow doctor guidance", advice, json.dumps(medicines_list)))

        # 3. Create Bill automatically
        b_count = conn.execute("SELECT COUNT(*) FROM bills").fetchone()[0]
        bill_id = f"BILL{str(b_count + 1).zfill(3)}"

        cursor.execute("""
            INSERT INTO bills (id, bill_id, appointment_id, patient_id, doctor_id, consultation_fee, date, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (bill_id, bill_id, apt['appointment_id'], apt['patient_id'], apt['doctor_id'], apt['consultation_fee'], today_str))

        # 4. Mark Appointment as Completed
        cursor.execute("UPDATE appointments SET status = 'Completed' WHERE id = ? OR appointment_id = ?", (appointment_id, appointment_id))

        conn.commit()
        conn.close()

        flash("Consultation completed! Prescription and billing invoice generated.", "success")
        return redirect(url_for('prescription', prescription_id=pre_id))

    patient = {
        'patient_id': apt['patient_id'],
        'name': apt['patient_name'],
        'age': apt['age'],
        'gender': apt['gender'],
        'blood_group': apt['blood_group'],
        'phone': apt['phone']
    }
    doctor = {
        'doctor_id': apt['doctor_id'],
        'name': apt['doctor_name'],
        'specialization': apt['specialization'],
        'qualification': apt['qualification'],
        'consultation_fee': apt['consultation_fee']
    }
    conn.close()
    return render_template('consultation.html', appointment=apt, patient=patient, doctor=doctor)


# 12. Digital Prescription View & Print
@app.route('/prescription/<prescription_id>')
def prescription(prescription_id):
    """
    Renders an official digital prescription sheet (℞) with print capabilities.
    """
    conn = get_db_connection()
    pre = conn.execute("""
        SELECT pr.*, pr.id as prescription_id,
               p.name as patient_name, p.id as patient_id, p.age, p.gender, p.blood_group,
               d.name as doctor_name, d.specialization, d.qualification,
               c.diagnosis, c.advice as consultation_advice
        FROM prescriptions pr
        JOIN patients p ON pr.patient_id = p.id OR pr.patient_id = p.patient_id
        JOIN doctors d ON pr.doctor_id = d.id OR pr.doctor_id = d.doctor_id
        LEFT JOIN consultations c ON pr.consultation_id = c.id OR pr.consultation_id = c.consultation_id
        WHERE pr.id = ? OR pr.prescription_id = ?
    """, (prescription_id, prescription_id)).fetchone()

    if not pre:
        conn.close()
        flash("Prescription record not found.", "warning")
        return redirect(url_for('dashboard'))

    medicines = []
    if pre['medicines_json']:
        try:
            medicines = json.loads(pre['medicines_json'])
        except Exception:
            medicines = [{'name': pre['medicine'], 'dosage': pre['dosage'], 'frequency': 'As directed', 'duration': '5 days', 'instructions': pre['instructions']}]

    doctor = {'name': pre['doctor_name'], 'specialization': pre['specialization'], 'qualification': pre['qualification']}
    patient = {'name': pre['patient_name'], 'patient_id': pre['patient_id'], 'age': pre['age'], 'gender': pre['gender'], 'blood_group': pre['blood_group']}
    consultation_data = {'diagnosis': pre['diagnosis'], 'advice': pre['doctor_advice'] or pre['consultation_advice']}

    conn.close()
    return render_template('prescription.html', prescription=pre, doctor=doctor, patient=patient, consultation=consultation_data, medicines=medicines)


# 13. Prescriptions List
@app.route('/prescriptions')
def prescriptions():
    """Lists all digital prescriptions issued for patient."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    patient_id = session.get('patient_id')

    pre_list = conn.execute("""
        SELECT pr.*, pr.id as prescription_id, d.name as doctor_name, d.specialization
        FROM prescriptions pr
        JOIN doctors d ON pr.doctor_id = d.id OR pr.doctor_id = d.doctor_id
        WHERE pr.patient_id = ?
        ORDER BY pr.date DESC
    """, (patient_id,)).fetchall()

    conn.close()
    return render_template('medical_history.html', prescriptions=pre_list)


# 14. Billing & Invoices
@app.route('/billing', endpoint='billing')
@app.route('/bills', endpoint='bills')
def billing():
    """Displays itemized consultation bills with payment status."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    role = session.get('role')

    if role == 'PATIENT':
        patient_id = session.get('patient_id')
        bills_list = conn.execute("""
            SELECT b.*, b.id as bill_id, d.name as doctor_name, d.specialization
            FROM bills b
            JOIN doctors d ON b.doctor_id = d.id OR b.doctor_id = d.doctor_id
            WHERE b.patient_id = ?
            ORDER BY b.date DESC
        """, (patient_id,)).fetchall()
    elif role == 'DOCTOR':
        doctor_id = session.get('doctor_id')
        bills_list = conn.execute("""
            SELECT b.*, b.id as bill_id, p.name as patient_name, p.id as patient_id
            FROM bills b
            JOIN patients p ON b.patient_id = p.id OR b.patient_id = p.patient_id
            WHERE b.doctor_id = ?
            ORDER BY b.date DESC
        """, (doctor_id,)).fetchall()
    else: # ADMIN
        bills_list = conn.execute("""
            SELECT b.*, b.id as bill_id, p.name as patient_name, p.id as patient_id, d.name as doctor_name, d.specialization
            FROM bills b
            JOIN patients p ON b.patient_id = p.id OR b.patient_id = p.patient_id
            JOIN doctors d ON b.doctor_id = d.id OR b.doctor_id = d.doctor_id
            ORDER BY b.date DESC
        """).fetchall()

    conn.close()
    return render_template('billing.html', bills=bills_list)


# 15. Mark Bill as Paid
@app.route('/pay-bill/<bill_id>', methods=['POST'])
@app.route('/billing/pay/<bill_id>', methods=['POST'])
def pay_bill(bill_id):
    """Marks an OPD consultation bill as paid."""
    conn = get_db_connection()
    conn.execute("UPDATE bills SET payment_status = 'Paid' WHERE id = ? OR bill_id = ?", (bill_id, bill_id))
    conn.commit()
    conn.close()
    flash(f"Payment received for invoice {bill_id}. Status updated to Paid.", "success")
    return redirect(url_for('billing'))


# 16. Patient Profile
@app.route('/profile')
def profile():
    """Displays registered patient profile information."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE id = ? OR patient_id = ?", (session.get('patient_id'), session.get('patient_id'))).fetchone()
    conn.close()
    return render_template('profile.html', patient=patient)


# 17. Medical History
@app.route('/medical-history')
def medical_history():
    """Displays full history of visits, diagnoses, and prescriptions."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    patient_id = session.get('patient_id')
    pre_list = conn.execute("""
        SELECT pr.*, pr.id as prescription_id, d.name as doctor_name, d.specialization
        FROM prescriptions pr
        JOIN doctors d ON pr.doctor_id = d.id OR pr.doctor_id = d.doctor_id
        WHERE pr.patient_id = ?
        ORDER BY pr.date DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return render_template('medical_history.html', prescriptions=pre_list)


# 18. Admin Dashboard
@app.route('/admin')
def admin():
    """Hospital administration console for doctors, patients, and bookings."""
    conn = get_db_connection()
    total_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    total_doctors = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    total_appointments = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    completed_appointments = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'Completed'").fetchone()[0]
    pending_bills = conn.execute("SELECT COUNT(*) FROM bills WHERE payment_status = 'Pending'").fetchone()[0]

    doctors = conn.execute("SELECT * FROM doctors ORDER BY name").fetchall()
    patients = conn.execute("SELECT * FROM patients ORDER BY name").fetchall()
    appointments = conn.execute("""
        SELECT a.*, a.id as appointment_id, p.name as patient_name, d.name as doctor_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id OR a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.id OR a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC
    """).fetchall()

    conn.close()
    return render_template('admin.html',
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           total_appointments=total_appointments,
                           completed_appointments=completed_appointments,
                           pending_bills=pending_bills,
                           doctors=doctors,
                           patients=patients,
                           appointments=appointments)


# 19. Admin Add Doctor
@app.route('/admin/add-doctor', methods=['POST'])
def add_doctor():
    """Adds a new doctor to SQLite."""
    name = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    qualification = request.form.get('qualification', '').strip()
    experience = request.form.get('experience', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    fee = float(request.form.get('consultation_fee', 50.0))
    days = request.form.get('available_days', 'Mon, Wed, Fri').strip()
    time_slot = request.form.get('available_time', '09:00 AM - 01:00 PM').strip()

    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    doc_id = f"DOC{str(count + 1).zfill(3)}"

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO doctors (id, doctor_id, name, specialization, qualification, experience, phone, email, consultation_fee, available_days, available_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available')
    """, (doc_id, doc_id, name, specialization, qualification, experience, phone, email, fee, days, time_slot))
    conn.commit()
    conn.close()

    flash(f"Doctor {name} ({doc_id}) added successfully.", "success")
    return redirect(url_for('admin'))


# 20. Admin Delete Doctor
@app.route('/admin/delete-doctor/<doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    """Deletes a doctor from SQLite."""
    conn = get_db_connection()
    conn.execute("DELETE FROM doctors WHERE id = ? OR doctor_id = ?", (doctor_id, doctor_id))
    conn.commit()
    conn.close()
    flash(f"Doctor {doctor_id} deleted successfully.", "info")
    return redirect(url_for('admin'))


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Default port: 5000 (or PORT env var if configured)
    port = int(os.environ.get('PORT', 5000))
    print(f"==================================================")
    print(f" MediCare – Healthcare Management System")
    print(f" Running on http://127.0.0.1:{port}")
    print(f" Database: {DB_PATH}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
