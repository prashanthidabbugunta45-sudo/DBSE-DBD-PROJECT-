"""
Raw SQL query helpers. All database reads/writes go through here.
"""
try:
    from .database import get_connection
except ImportError:
    from database import get_connection


# =========================================
# PATIENTS
# =========================================
def create_patient(patient_id, full_name, dob, age, gender, phone, email,
                   address, ec_name, ec_number, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO patients
            (patient_id, full_name, date_of_birth, age, gender, phone, email,
             address, emergency_contact_name, emergency_contact_number, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (patient_id, full_name, dob, age, gender, phone, email,
              address, ec_name, ec_number, password_hash))
        conn.commit()
        return patient_id
    finally:
        cursor.close()
        conn.close()


def get_patient_by_login(login_id):
    """Find patient by patient_id OR email."""
    login_id = login_id.strip()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM patients
            WHERE patient_id = %s OR LOWER(email) = LOWER(%s)
            LIMIT 1
        """, (login_id, login_id))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_patient_by_email(email):
    email = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM patients WHERE LOWER(email) = %s", (email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_patient_by_phone(phone):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM patients WHERE phone = %s", (phone,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_patients():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT patient_id, full_name, email, phone, age, gender,
                   address, created_at
            FROM patients
            ORDER BY created_at DESC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# =========================================
# ADMINS
# =========================================
def get_admin_by_email(email):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM admins WHERE LOWER(email) = LOWER(%s)", (email.strip(),))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_admin_by_login(identifier):
    """Accept either an email address or an ADM-style Admin ID (e.g. ADM001)."""
    import re
    identifier = identifier.strip()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        match = re.fullmatch(r"ADM0*(\d+)", identifier, re.IGNORECASE)
        if match:
            cursor.execute("SELECT * FROM admins WHERE admin_id = %s", (int(match.group(1)),))
        else:
            cursor.execute("SELECT * FROM admins WHERE LOWER(email) = LOWER(%s)", (identifier,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# =========================================
# SPECIALIZATIONS & DOCTORS
# =========================================
def get_all_specializations():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM specializations ORDER BY name")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_doctors_by_specialization(spec_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT d.doctor_id, d.full_name, d.qualification, d.experience_years,
                   d.phone, d.email, d.bio, d.consultation_fee,
                   GROUP_CONCAT(DISTINCT da.day_of_week
                       ORDER BY FIELD(da.day_of_week, 'Monday', 'Tuesday', 'Wednesday',
                                      'Thursday', 'Friday', 'Saturday', 'Sunday')
                       SEPARATOR ', ') AS available_days,
                   TIME_FORMAT(MIN(da.start_time), '%%H:%%i') AS available_from,
                   TIME_FORMAT(MAX(da.end_time), '%%H:%%i') AS available_to
            FROM doctors d
            LEFT JOIN doctor_availability da
                ON da.doctor_id = d.doctor_id AND da.is_available = TRUE
            WHERE d.specialization_id = %s AND d.is_active = TRUE
            GROUP BY d.doctor_id
            ORDER BY d.full_name
        """, (spec_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_doctors():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT d.*, s.name AS specialization
            FROM doctors d
            JOIN specializations s ON d.specialization_id = s.specialization_id
            ORDER BY d.full_name
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def create_doctor(full_name, specialization_id, qualification, experience_years,
                  phone, email, bio, consultation_fee=500.00):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO doctors
            (full_name, specialization_id, qualification, experience_years,
             phone, email, bio, consultation_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, specialization_id, qualification, experience_years,
              phone, email, bio, consultation_fee))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def update_doctor(doctor_id, full_name, specialization_id, qualification,
                  experience_years, phone, email, bio, is_active, consultation_fee=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if consultation_fee is None:
            cursor.execute("""
                UPDATE doctors
                SET full_name = %s, specialization_id = %s, qualification = %s,
                    experience_years = %s, phone = %s, email = %s, bio = %s,
                    is_active = %s
                WHERE doctor_id = %s
            """, (full_name, specialization_id, qualification, experience_years,
                  phone, email, bio, is_active, doctor_id))
        else:
            cursor.execute("""
                UPDATE doctors
                SET full_name = %s, specialization_id = %s, qualification = %s,
                    experience_years = %s, phone = %s, email = %s, bio = %s,
                    is_active = %s, consultation_fee = %s
                WHERE doctor_id = %s
            """, (full_name, specialization_id, qualification, experience_years,
                  phone, email, bio, is_active, consultation_fee, doctor_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def add_doctor_availability(doctor_id, day_of_week, start_time, end_time, is_available=True):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, is_available)
            VALUES (%s, %s, %s, %s, %s)
        """, (doctor_id, day_of_week, start_time, end_time, is_available))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def delete_doctor_availability(availability_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM doctor_availability WHERE availability_id = %s", (availability_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def get_doctor_availability(doctor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT availability_id, doctor_id, day_of_week,
                   TIME_FORMAT(start_time, '%%H:%%i') AS start_time,
                   TIME_FORMAT(end_time, '%%H:%%i') AS end_time, is_available
            FROM doctor_availability
            WHERE doctor_id = %s
            ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday',
                           'Thursday', 'Friday', 'Saturday', 'Sunday'),
                     start_time
        """, (doctor_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_doctor_by_id(doctor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT d.*, s.name AS specialization
            FROM doctors d
            JOIN specializations s ON d.specialization_id = s.specialization_id
            WHERE d.doctor_id = %s
        """, (doctor_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def is_doctor_available(doctor_id, appointment_date, appointment_time=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 1
            FROM doctor_availability
            WHERE doctor_id = %s
              AND day_of_week = DAYNAME(%s)
              AND is_available = TRUE
        """
        params = [doctor_id, appointment_date]
        if appointment_time is not None:
            query += " AND start_time <= %s AND end_time > %s"
            params.extend([appointment_time, appointment_time])
        query += " LIMIT 1"
        cursor.execute(query, tuple(params))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


# =========================================
# HOLIDAYS
# =========================================
def get_holidays():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM holidays")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_holiday_by_date(date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM holidays WHERE holiday_date = %s", (date,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def create_holiday(holiday_date, reason, admin_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO holidays (holiday_date, reason, created_by)
            VALUES (%s, %s, %s)
        """, (holiday_date, reason, admin_id))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def delete_holiday(holiday_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM holidays WHERE holiday_id = %s", (holiday_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


# =========================================
# APPOINTMENTS
# =========================================
def get_booked_slots(doctor_id, date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT slot_number, appointment_time
            FROM appointments
            WHERE doctor_id = %s
              AND appointment_date = %s
              AND status NOT IN ('Cancelled', 'No Show')
        """, (doctor_id, date))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def create_appointment(patient_id, doctor_id, spec_id, date, time, slot_num, reason):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO appointments
            (patient_id, doctor_id, specialization_id, appointment_date,
             appointment_time, slot_number, reason, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Booked')
        """, (patient_id, doctor_id, spec_id, date, time, slot_num, reason))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_appointment_by_id(appt_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT a.*, d.full_name AS doctor_name, d.consultation_fee,
                   s.name AS specialization, p.full_name AS patient_name
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN specializations s ON a.specialization_id = s.specialization_id
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.appointment_id = %s
        """, (appt_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_patient_appointment_by_id(appt_id, patient_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT a.*, d.full_name AS doctor_name, d.consultation_fee,
                   s.name AS specialization, p.full_name AS patient_name
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN specializations s ON a.specialization_id = s.specialization_id
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.appointment_id = %s AND a.patient_id = %s
        """, (appt_id, patient_id))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_appointments_by_patient(patient_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT a.appointment_id, a.doctor_id, a.appointment_date,
                   TIME_FORMAT(a.appointment_time, '%%H:%%i') AS appointment_time,
                   a.slot_number, a.status, a.reason,
                   d.full_name AS doctor_name,
                   s.name AS specialization,
                   pay.payment_status
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN specializations s ON a.specialization_id = s.specialization_id
            LEFT JOIN payments pay ON pay.appointment_id = a.appointment_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """, (patient_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_active_patient_appointments_on_date(patient_id, appointment_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT appointment_id, doctor_id, appointment_time, slot_number
            FROM appointments
            WHERE patient_id = %s
              AND appointment_date = %s
              AND status NOT IN ('Cancelled', 'No Show',
                                 'Visited – Appointment Not Completed')
        """, (patient_id, appointment_date))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_patient_appointments_with_doctor(patient_id, doctor_id):
    """Used to highlight a patient's own appointments on that doctor's calendar."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT appointment_date, status
            FROM appointments
            WHERE patient_id = %s AND doctor_id = %s
              AND status != 'Cancelled'
        """, (patient_id, doctor_id))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_appointments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT a.appointment_id, a.appointment_date,
                   TIME_FORMAT(a.appointment_time, '%H:%i') AS appointment_time,
                   a.slot_number, a.status, a.reason,
                   p.full_name AS patient_name,
                   d.full_name AS doctor_name,
                   s.name AS specialization
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN specializations s ON a.specialization_id = s.specialization_id
            ORDER BY a.appointment_date ASC, a.appointment_time ASC, a.slot_number ASC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def update_appointment_status(appt_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE appointments SET status = %s WHERE appointment_id = %s
        """, (new_status, appt_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def update_appointment_reschedule(appt_id, patient_id, appointment_date, appointment_time, slot_num, reason):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE appointments
            SET appointment_date = %s, appointment_time = %s,
                slot_number = %s, reason = %s
            WHERE appointment_id = %s AND patient_id = %s
              AND status = 'Booked'
        """, (appointment_date, appointment_time, slot_num, reason, appt_id, patient_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def cancel_appointment(appt_id, patient_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE appointments
            SET status = 'Cancelled'
            WHERE appointment_id = %s AND patient_id = %s
              AND status IN ('Booked', 'Confirmed')
        """, (appt_id, patient_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


# =========================================
# NOTIFICATIONS
# =========================================
def create_notification(patient_id, appointment_id, title, message, notif_type):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO notifications
            (patient_id, appointment_id, title, message, notification_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (patient_id, appointment_id, title, message, notif_type))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_notifications_by_patient(patient_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT notification_id, title, message, notification_type,
                   is_read, created_at
            FROM notifications
            WHERE patient_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (patient_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def mark_notification_read(notification_id, patient_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE notification_id = %s AND patient_id = %s
        """, (notification_id, patient_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


# =========================================
# PAYMENTS
# =========================================
def create_payment(appt_id, patient_id, receipt_no, amount, method, status):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO payments
            (appointment_id, patient_id, receipt_number, amount,
             payment_method, payment_status, payment_date)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (appt_id, patient_id, receipt_no, amount, method, status))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def check_payment_exists(appt_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM payments
            WHERE appointment_id = %s AND payment_status = 'Success'
        """, (appt_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_payment_by_id(payment_id, patient_id=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM payments WHERE payment_id = %s"
        params = [payment_id]
        if patient_id is not None:
            query += " AND patient_id = %s"
            params.append(patient_id)
        cursor.execute(query, tuple(params))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_payment_by_appointment(appointment_id, patient_id=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM payments WHERE appointment_id = %s"
        params = [appointment_id]
        if patient_id is not None:
            query += " AND patient_id = %s"
            params.append(patient_id)
        cursor.execute(query, tuple(params))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_payment_by_receipt(receipt_number):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, pt.full_name AS patient_name, pt.email AS patient_email,
                   a.appointment_date, TIME_FORMAT(a.appointment_time, '%%H:%%i') AS appointment_time, a.reason,
                   d.full_name AS doctor_name, s.name AS specialization
            FROM payments p
            JOIN patients pt ON p.patient_id = pt.patient_id
            JOIN appointments a ON p.appointment_id = a.appointment_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN specializations s ON a.specialization_id = s.specialization_id
            WHERE p.receipt_number = %s
        """, (receipt_number,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_payments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, pt.full_name AS patient_name
            FROM payments p
            JOIN patients pt ON p.patient_id = pt.patient_id
            ORDER BY p.created_at DESC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_payments_by_patient(patient_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, a.appointment_date, TIME_FORMAT(a.appointment_time, '%%H:%%i') AS appointment_time,
                   d.full_name AS doctor_name, s.name AS specialization
            FROM payments p
            JOIN appointments a ON p.appointment_id = a.appointment_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN specializations s ON a.specialization_id = s.specialization_id
            WHERE p.patient_id = %s
            ORDER BY p.created_at DESC
        """, (patient_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# =========================================
# ADMIN STATS
# =========================================
def get_admin_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS c FROM patients")
        patients = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) AS c FROM doctors WHERE is_active = TRUE")
        doctors = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) AS c FROM appointments")
        appointments = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT COUNT(*) AS c FROM appointments
            WHERE appointment_date = CURDATE()
        """)
        today = cursor.fetchone()["c"]

        return {
            "total_patients": patients,
            "total_doctors": doctors,
            "total_appointments": appointments,
            "today_appointments": today,
        }
    finally:
        cursor.close()
        conn.close()