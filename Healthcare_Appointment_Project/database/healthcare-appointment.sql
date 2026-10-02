/* =========================================================
   CAREPLUS HEALTHCARE APPOINTMENT SCHEDULING SYSTEM
   COMPLETE DATABASE
   MySQL 8.0+
========================================================= */


/* =========================================================
   1. CREATE DATABASE
========================================================= */

CREATE DATABASE IF NOT EXISTS healthcare_appointment_db;

USE healthcare_appointment_db;


/* =========================================================
   2. ADMINS
========================================================= */

CREATE TABLE IF NOT EXISTS admins (

    admin_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(150) NOT NULL UNIQUE,

    password_hash VARCHAR(255) NOT NULL,

    role VARCHAR(20) NOT NULL DEFAULT 'admin',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);


/* =========================================================
   3. SPECIALIZATIONS
========================================================= */

CREATE TABLE IF NOT EXISTS specializations (

    specialization_id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100) NOT NULL UNIQUE,

    description VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);


/* =========================================================
   4. PATIENTS
========================================================= */

CREATE TABLE IF NOT EXISTS patients (

    patient_id VARCHAR(20) PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    date_of_birth DATE NOT NULL,

    age INT NOT NULL,

    gender VARCHAR(20),

    phone VARCHAR(20) NOT NULL UNIQUE,

    email VARCHAR(150) NOT NULL UNIQUE,

    address TEXT,

    emergency_contact_name VARCHAR(100),

    emergency_contact_number VARCHAR(20),

    password_hash VARCHAR(255) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP

);


/* =========================================================
   5. DOCTORS
========================================================= */

CREATE TABLE IF NOT EXISTS doctors (

    doctor_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,

    specialization_id INT NOT NULL,

    qualification VARCHAR(255),

    experience_years INT DEFAULT 0,

    phone VARCHAR(20),

    email VARCHAR(150),

    bio TEXT,

    consultation_fee DECIMAL(10,2) NOT NULL DEFAULT 500.00,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_doctor_specialization

        FOREIGN KEY (specialization_id)

        REFERENCES specializations(specialization_id)

        ON UPDATE CASCADE

        ON DELETE RESTRICT

);


/* =========================================================
   6. DOCTOR AVAILABILITY
========================================================= */

CREATE TABLE IF NOT EXISTS doctor_availability (

    availability_id INT AUTO_INCREMENT PRIMARY KEY,

    doctor_id INT NOT NULL,

    day_of_week ENUM(
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    ) NOT NULL,

    start_time TIME NOT NULL,

    end_time TIME NOT NULL,

    is_available BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_availability_doctor

        FOREIGN KEY (doctor_id)

        REFERENCES doctors(doctor_id)

        ON UPDATE CASCADE

        ON DELETE CASCADE,

    UNIQUE (
        doctor_id,
        day_of_week,
        start_time,
        end_time
    )

);


/* =========================================================
   7. HOLIDAYS
========================================================= */

CREATE TABLE IF NOT EXISTS holidays (

    holiday_id INT AUTO_INCREMENT PRIMARY KEY,

    holiday_date DATE NOT NULL UNIQUE,

    reason VARCHAR(255) NOT NULL,

    created_by INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_holiday_admin

        FOREIGN KEY (created_by)

        REFERENCES admins(admin_id)

        ON UPDATE CASCADE

        ON DELETE SET NULL

);


/* =========================================================
   8. APPOINTMENTS
========================================================= */

CREATE TABLE IF NOT EXISTS appointments (

    appointment_id INT AUTO_INCREMENT PRIMARY KEY,

    patient_id VARCHAR(20) NOT NULL,

    doctor_id INT NOT NULL,

    specialization_id INT NOT NULL,

    appointment_date DATE NOT NULL,

    appointment_time TIME NOT NULL,

    slot_number INT NOT NULL,

    reason TEXT,

    status ENUM(

        'Booked',

        'Confirmed',

        'Completed',

        'Visited – Appointment Not Completed',

        'Cancelled',

        'No Show'

    ) NOT NULL DEFAULT 'Booked',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,


    CONSTRAINT fk_appointment_patient

        FOREIGN KEY (patient_id)

        REFERENCES patients(patient_id)

        ON UPDATE CASCADE

        ON DELETE RESTRICT,


    CONSTRAINT fk_appointment_doctor

        FOREIGN KEY (doctor_id)

        REFERENCES doctors(doctor_id)

        ON UPDATE CASCADE

        ON DELETE RESTRICT,


    CONSTRAINT fk_appointment_specialization

        FOREIGN KEY (specialization_id)

        REFERENCES specializations(specialization_id)

        ON UPDATE CASCADE

        ON DELETE RESTRICT,


    /* Only slots 1 to 10 are allowed */

    CONSTRAINT chk_slot_number

        CHECK (slot_number BETWEEN 1 AND 10),


    /* Same doctor cannot have same slot for an active status. Including
       `status` means a new 'Booked' row can reuse a slot that a prior
       'Cancelled' row occupied, while still blocking two simultaneous
       active bookings for the same doctor/date/slot. */
    UNIQUE (
        doctor_id,
        appointment_date,
        slot_number,
        status
    )

);


/* =========================================================
   9. NOTIFICATIONS
========================================================= */

CREATE TABLE IF NOT EXISTS notifications (

    notification_id INT AUTO_INCREMENT PRIMARY KEY,

    patient_id VARCHAR(20),

    admin_id INT,

    appointment_id INT,

    title VARCHAR(150) NOT NULL,

    message TEXT NOT NULL,

    notification_type VARCHAR(50) NOT NULL,

    is_read BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_notification_patient

        FOREIGN KEY (patient_id)

        REFERENCES patients(patient_id)

        ON UPDATE CASCADE

        ON DELETE CASCADE,


    CONSTRAINT fk_notification_admin

        FOREIGN KEY (admin_id)

        REFERENCES admins(admin_id)

        ON UPDATE CASCADE

        ON DELETE CASCADE,


    CONSTRAINT fk_notification_appointment

        FOREIGN KEY (appointment_id)

        REFERENCES appointments(appointment_id)

        ON UPDATE CASCADE

        ON DELETE CASCADE

);


/* =========================================================
   10. PAYMENTS
========================================================= */

CREATE TABLE IF NOT EXISTS payments (

    payment_id INT AUTO_INCREMENT PRIMARY KEY,

    appointment_id INT NOT NULL,

    patient_id VARCHAR(20) NOT NULL,

    receipt_number VARCHAR(50) NOT NULL UNIQUE,

    amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    payment_method VARCHAR(50) NOT NULL DEFAULT 'Demo Payment',

    payment_status ENUM(

        'Pending',

        'Success',

        'Failed'

    ) NOT NULL DEFAULT 'Pending',

    payment_date TIMESTAMP NULL,


    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_payment_appointment

        FOREIGN KEY (appointment_id)

        REFERENCES appointments(appointment_id)

        ON UPDATE CASCADE

        ON DELETE RESTRICT,


    CONSTRAINT fk_payment_patient

        FOREIGN KEY (patient_id)

        REFERENCES patients(patient_id)

        ON UPDATE CASCADE

        ON DELETE RESTRICT,


    CONSTRAINT chk_payment_amount

        CHECK (amount >= 0)

);


/* =========================================================
   11. INDEXES
========================================================= */

CREATE INDEX idx_patient_email
ON patients(email);


CREATE INDEX idx_patient_phone
ON patients(phone);


CREATE INDEX idx_doctor_specialization
ON doctors(specialization_id);


CREATE INDEX idx_appointment_date
ON appointments(appointment_date);


CREATE INDEX idx_appointment_doctor_date
ON appointments(
    doctor_id,
    appointment_date
);


CREATE INDEX idx_appointment_patient
ON appointments(patient_id);


CREATE INDEX idx_appointment_status
ON appointments(status);


CREATE INDEX idx_notification_patient
ON notifications(patient_id);


CREATE INDEX idx_notification_admin
ON notifications(admin_id);


/* =========================================================
   12. SPECIALIZATION DATA
========================================================= */

INSERT IGNORE INTO specializations
(name, description)
VALUES

(
    'Cardiology',
    'Heart and cardiovascular care'
),

(
    'Dermatology',
    'Skin, hair and nail care'
),

(
    'Neurology',
    'Brain and nervous system care'
),

(
    'Orthopedics',
    'Bone, joint and muscle care'
),

(
    'Ophthalmology',
    'Eye and vision care'
),

(
    'Dentistry',
    'Dental and oral healthcare'
),

(
    'General Medicine',
    'General healthcare and checkups'
);


/* =========================================================
   13. SAMPLE DOCTORS
========================================================= */

INSERT IGNORE INTO doctors
(
    full_name,
    specialization_id,
    qualification,
    experience_years,
    phone,
    email,
    bio
)

SELECT
    'Dr. Arjun Sharma',
    specialization_id,
    'MBBS, MD Cardiology',
    12,
    '9000000001',
    'arjun.sharma@careplus.com',
    'Experienced cardiologist providing cardiovascular care.'
FROM specializations
WHERE name = 'Cardiology';


INSERT IGNORE INTO doctors
(
    full_name,
    specialization_id,
    qualification,
    experience_years,
    phone,
    email,
    bio
)

SELECT
    'Dr. Priya Mehta',
    specialization_id,
    'MBBS, MD Dermatology',
    9,
    '9000000002',
    'priya.mehta@careplus.com',
    'Experienced dermatologist specializing in skin care.'
FROM specializations
WHERE name = 'Dermatology';


INSERT IGNORE INTO doctors
(
    full_name,
    specialization_id,
    qualification,
    experience_years,
    phone,
    email,
    bio
)

SELECT
    'Dr. Rahul Verma',
    specialization_id,
    'MBBS, DM Neurology',
    11,
    '9000000003',
    'rahul.verma@careplus.com',
    'Neurologist specializing in nervous system care.'
FROM specializations
WHERE name = 'Neurology';


INSERT IGNORE INTO doctors
(
    full_name,
    specialization_id,
    qualification,
    experience_years,
    phone,
    email,
    bio
)

SELECT
    'Dr. Sneha Rao',
    specialization_id,
    'MBBS, MS Orthopedics',
    10,
    '9000000004',
    'sneha.rao@careplus.com',
    'Orthopedic specialist providing bone and joint care.'
FROM specializations
WHERE name = 'Orthopedics';


INSERT IGNORE INTO doctors
(
    full_name,
    specialization_id,
    qualification,
    experience_years,
    phone,
    email,
    bio
)

SELECT
    'Dr. Ananya Patel',
    specialization_id,
    'MBBS, MS Ophthalmology',
    8,
    '9000000005',
    'ananya.patel@careplus.com',
    'Eye specialist providing vision and eye care.'
FROM specializations
WHERE name = 'Ophthalmology';


INSERT IGNORE INTO doctors
(
    full_name,
    specialization_id,
    qualification,
    experience_years,
    phone,
    email,
    bio
)

SELECT
    'Dr. Karan Shah',
    specialization_id,
    'BDS, MDS',
    7,
    '9000000006',
    'karan.shah@careplus.com',
    'Dentist providing comprehensive dental care.'
FROM specializations
WHERE name = 'Dentistry';


INSERT IGNORE INTO doctors
(
    full_name,
    specialization_id,
    qualification,
    experience_years,
    phone,
    email,
    bio
)

SELECT
    'Dr. Neha Kapoor',
    specialization_id,
    'MBBS, MD',
    13,
    '9000000007',
    'neha.kapoor@careplus.com',
    'General medicine specialist for routine healthcare.'
FROM specializations
WHERE name = 'General Medicine';


/* =========================================================
   14. DOCTOR AVAILABILITY
========================================================= */

/* Monday */

INSERT IGNORE INTO doctor_availability
(doctor_id, day_of_week, start_time, end_time)

SELECT doctor_id, 'Monday', '09:00:00', '11:30:00'
FROM doctors;


/* Tuesday */

INSERT IGNORE INTO doctor_availability
(doctor_id, day_of_week, start_time, end_time)

SELECT doctor_id, 'Tuesday', '09:00:00', '11:30:00'
FROM doctors;


/* Wednesday */

INSERT IGNORE INTO doctor_availability
(doctor_id, day_of_week, start_time, end_time)

SELECT doctor_id, 'Wednesday', '09:00:00', '11:30:00'
FROM doctors;


/* Thursday */

INSERT IGNORE INTO doctor_availability
(doctor_id, day_of_week, start_time, end_time)

SELECT doctor_id, 'Thursday', '09:00:00', '11:30:00'
FROM doctors;


/* Friday */

INSERT IGNORE INTO doctor_availability
(doctor_id, day_of_week, start_time, end_time)

SELECT doctor_id, 'Friday', '09:00:00', '11:30:00'
FROM doctors;


/* Saturday */

INSERT IGNORE INTO doctor_availability
(doctor_id, day_of_week, start_time, end_time)

SELECT doctor_id, 'Saturday', '09:00:00', '11:30:00'
FROM doctors;


/* =========================================================
   15. CHECK DATABASE
========================================================= */

SHOW TABLES;


/* =========================================================
   16. CHECK SPECIALIZATIONS
========================================================= */

SELECT *
FROM specializations;


/* =========================================================
   17. CHECK DOCTORS
========================================================= */

SELECT
    d.doctor_id,
    d.full_name,
    s.name AS specialization,
    d.qualification,
    d.experience_years,
    d.is_active

FROM doctors d

JOIN specializations s
    ON d.specialization_id = s.specialization_id;


/* =========================================================
   18. CHECK AVAILABILITY
========================================================= */

SELECT
    da.availability_id,
    d.full_name AS doctor,
    da.day_of_week,
    da.start_time,
    da.end_time,
    da.is_available

FROM doctor_availability da

JOIN doctors d
    ON da.doctor_id = d.doctor_id

ORDER BY
    d.full_name,
    da.day_of_week;
    
   /* =========================================================
   19. SEED ADMIN ACCOUNTS
========================================================= */

INSERT IGNORE INTO admins (full_name, email, password_hash, role) VALUES
('Super Admin', 'admin1@careplus.com', '$2b$12$Av4Gy2czANQTIq0nP6OQY.k9S4XffHiLihrLXv/USfdLtot4bcGAq', 'admin'),
('Admin Two', 'admin2@careplus.com', '$2b$12$Av4Gy2czANQTIq0nP6OQY.k9S4XffHiLihrLXv/USfdLtot4bcGAq', 'admin');
    
   