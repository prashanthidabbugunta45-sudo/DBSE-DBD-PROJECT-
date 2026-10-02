"""
CarePlus Healthcare Appointment Scheduling System
FastAPI Backend
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date, timedelta
import random
import string

try:
    from .database import get_connection
    from . import models, schemas
    from .auth_utils import (
        hash_password,
        verify_password,
        create_access_token,
        get_current_patient,
        get_current_admin,
    )
except ImportError:
    from database import get_connection
    import models
    import schemas
    from auth_utils import (
        hash_password,
        verify_password,
        create_access_token,
        get_current_patient,
        get_current_admin,
    )

app = FastAPI(title="CarePlus API", version="1.0.0")

# =========================================
# CORS
# =========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================
# HELPERS
# =========================================
TIME_SLOTS = [
    "09:00:00", "09:15:00", "09:30:00", "09:45:00", "10:00:00",
    "10:15:00", "10:30:00", "10:45:00", "11:00:00", "11:15:00"
]
MAX_SLOTS_PER_DAY = 10
APPOINTMENT_FEE = 500.00


def generate_patient_id():
    """Generate a unique Patient ID like P202600123."""
    year = datetime.now().year
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        return f"P{year}{str(count + 1).zfill(5)}"
    finally:
        cursor.close()
        conn.close()


def generate_receipt_number():
    """Generate a unique receipt number."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.digits, k=4))
    return f"RCPT-{ts}-{rand}"


def parse_time_str(t: str):
    """Accept '09:00' or '09:00:00' and return a time object."""
    if len(t) == 5:
        t = t + ":00"
    return datetime.strptime(t, "%H:%M:%S").time()


# =========================================
# ROOT
# =========================================
@app.get("/")
def root():
    return {"message": "CarePlus API is running", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# =========================================
# AUTHENTICATION
# =========================================
@app.post("/auth/register")
def register_patient(payload: schemas.PatientRegister):
    # Check duplicates
    if models.get_patient_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if models.get_patient_by_phone(payload.phone):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    patient_id = generate_patient_id()
    pwd_hash = hash_password(payload.password)

    try:
        models.create_patient(
            patient_id=patient_id,
            full_name=payload.full_name,
            dob=payload.date_of_birth,
            age=payload.age,
            gender=payload.gender,
            phone=payload.phone,
            email=payload.email,
            address=payload.address,
            ec_name=payload.emergency_contact_name,
            ec_number=payload.emergency_contact_number,
            password_hash=pwd_hash,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    return {
        "message": "Registration successful",
        "patient_id": patient_id,
        "patient_name": payload.full_name,
    }


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login_patient(payload: schemas.PatientLogin):
    patient = models.get_patient_by_login(payload.login_id)
    if not patient:
        raise HTTPException(status_code=401, detail="Invalid Patient ID/email or password.")

    if not verify_password(payload.password, patient["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid Patient ID/email or password.")

    token = create_access_token({
        "sub": patient["patient_id"],
        "role": "patient",
        "name": patient["full_name"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "patient_id": patient["patient_id"],
        "full_name": patient["full_name"],
    }


@app.get("/auth/me")
def current_patient(user=Depends(get_current_patient)):
    patient = models.get_patient_by_login(user["patient_id"])
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.pop("password_hash", None)
    return patient


@app.post("/auth/admin/login", response_model=schemas.TokenResponse)
def login_admin(payload: schemas.AdminLogin):
    admin = models.get_admin_by_login(payload.email)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin ID/email or password")

    if not verify_password(payload.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid admin ID/email or password")

    token = create_access_token({
        "sub": str(admin["admin_id"]),
        "role": "admin",
        "name": admin["full_name"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "full_name": admin["full_name"],
    }


# =========================================
# DOCTORS
# =========================================
@app.get("/doctors/specializations")
def list_specializations():
    return models.get_all_specializations()


@app.get("/doctors")
def list_doctors():
    return models.get_all_doctors()


@app.get("/doctors/by-specialization/{spec_id}")
def doctors_by_spec(spec_id: int):
    return models.get_doctors_by_specialization(spec_id)


@app.get("/doctors/{doctor_id}")
def doctor_profile(doctor_id: int):
    doctor = models.get_doctor_by_id(doctor_id)
    if not doctor or not doctor["is_active"]:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@app.get("/doctors/{doctor_id}/availability")
def doctor_availability(doctor_id: int):
    doctor = models.get_doctor_by_id(doctor_id)
    if not doctor or not doctor["is_active"]:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return models.get_doctor_availability(doctor_id)


# =========================================
# APPOINTMENTS
# =========================================
@app.get("/appointments/calendar/{doctor_id}")
def doctor_calendar(doctor_id: int, user=Depends(get_current_patient)):
    """Return next 30 days availability for a doctor, highlighting the
    logged-in patient's own appointments with this doctor."""
    doctor = models.get_doctor_by_id(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    holidays = {str(h["holiday_date"]): h["reason"] for h in models.get_holidays()}

    patient_status_by_date = {}
    for appt in models.get_patient_appointments_with_doctor(user["patient_id"], doctor_id):
        appt_date = str(appt["appointment_date"])
        status = appt["status"]
        if status in ("Booked", "Confirmed"):
            patient_status_by_date[appt_date] = "My Upcoming Appointment"
        elif status == "Visited – Appointment Not Completed":
            patient_status_by_date[appt_date] = "Visited – Appointment Not Completed"
        elif status in ("Completed", "No Show"):
            patient_status_by_date.setdefault(appt_date, "Previous Visit")

    today = date.today()
    result = []

    for i in range(30):
        d = today + timedelta(days=i)
        d_str = d.isoformat()
        patient_status = patient_status_by_date.get(d_str)

        if d_str in holidays:
            result.append({
                "date": d_str,
                "status": "Holiday",
                "reason": holidays[d_str],
                "booked": 0,
            })
            continue

        if not models.is_doctor_available(doctor_id, d_str):
            result.append({
                "date": d_str,
                "status": patient_status or "Unavailable",
                "booked": 0,
            })
            continue

        booked = models.get_booked_slots(doctor_id, d_str)
        booked_count = len(booked)

        if patient_status:
            status = patient_status
        elif booked_count >= MAX_SLOTS_PER_DAY:
            status = "Full"
        else:
            status = "Available"

        result.append({
            "date": d_str,
            "status": status,
            "booked": booked_count,
        })

    return result


@app.get("/appointments/available-slots/{doctor_id}/{appt_date}")
def available_slots(doctor_id: int, appt_date: str,
                    user=Depends(get_current_patient)):
    """Return available time slots for a doctor on a date."""
    doctor = models.get_doctor_by_id(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    try:
        requested_date = date.fromisoformat(appt_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid appointment date") from exc
    if requested_date < date.today():
        raise HTTPException(status_code=400, detail="Appointment date cannot be in the past")

    holiday = models.get_holiday_by_date(appt_date)
    if holiday:
        raise HTTPException(status_code=400, detail=f"Hospital closed: {holiday['reason']}")
    if not models.is_doctor_available(doctor_id, appt_date):
        raise HTTPException(status_code=400, detail="Doctor is not available on this date")

    booked = models.get_booked_slots(doctor_id, appt_date)
    booked_slots = {b["slot_number"] for b in booked}
    patient_appointments = models.get_active_patient_appointments_on_date(
        user["patient_id"], appt_date
    )
    patient_booked_slots = {
        appointment["slot_number"] for appointment in patient_appointments
    }

    available = []
    slot_options = []
    for idx, t in enumerate(TIME_SLOTS):
        slot_num = idx + 1
        doctor_booked = slot_num in booked_slots
        patient_booked = slot_num in patient_booked_slots
        if not doctor_booked and not patient_booked:
            available.append(t[:5])  # Return HH:MM
        slot_options.append({
            "time": t[:5],
            "available": not doctor_booked and not patient_booked,
            "reason": "already booked by you" if patient_booked else (
                "already booked" if doctor_booked else None
            ),
        })

    return {
        "doctor_id": doctor_id,
        "date": appt_date,
        "available_slots": available,
        "slot_options": slot_options,
        "patient_booked_times": [t[:5] for idx, t in enumerate(TIME_SLOTS) if (idx + 1) in patient_booked_slots],
        "booked": len(booked),
        "remaining": MAX_SLOTS_PER_DAY - len(booked),
    }


@app.post("/appointments/book")
def book_appointment(payload: schemas.AppointmentBook,
                     user=Depends(get_current_patient)):
    patient_id = user["patient_id"]

    # Validate
    doctor = models.get_doctor_by_id(payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if not doctor["is_active"]:
        raise HTTPException(status_code=400, detail="Doctor is not currently available")
    if doctor["specialization_id"] != payload.specialization_id:
        raise HTTPException(status_code=400, detail="Doctor does not match the selected specialization")
    if payload.appointment_date < date.today():
        raise HTTPException(status_code=400, detail="Appointment date cannot be in the past")

    holiday = models.get_holiday_by_date(payload.appointment_date.isoformat())
    if holiday:
        raise HTTPException(status_code=400, detail=f"Hospital closed: {holiday['reason']}")

    booked = models.get_booked_slots(payload.doctor_id, payload.appointment_date.isoformat())
    if len(booked) >= MAX_SLOTS_PER_DAY:
        raise HTTPException(status_code=400, detail="This date is fully booked (10/10)")

    # Find slot number
    try:
        time_obj = parse_time_str(payload.appointment_time)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid time format")

    time_str = time_obj.strftime("%H:%M:%S")
    if time_str not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="Time slot not valid")
    if not models.is_doctor_available(
        payload.doctor_id,
        payload.appointment_date.isoformat(),
        time_str,
    ):
        raise HTTPException(status_code=400, detail="Doctor is not available at this time")

    slot_num = TIME_SLOTS.index(time_str) + 1

    patient_appointments = models.get_active_patient_appointments_on_date(
        patient_id,
        payload.appointment_date.isoformat(),
    )
    for appointment in patient_appointments:
        if appointment["doctor_id"] == payload.doctor_id:
            raise HTTPException(
                status_code=400,
                detail="You already have an active appointment with this doctor on this date",
            )
        if appointment["slot_number"] == slot_num:
            raise HTTPException(
                status_code=400,
                detail="This time is already booked by you on the selected date",
            )

    # Check clash
    for b in booked:
        if b["slot_number"] == slot_num:
            raise HTTPException(status_code=400, detail="This slot is already booked")

    # Create appointment
    try:
        appt_id = models.create_appointment(
            patient_id=patient_id,
            doctor_id=payload.doctor_id,
            spec_id=payload.specialization_id,
            date=payload.appointment_date.isoformat(),
            time=time_str,
            slot_num=slot_num,
            reason=payload.reason,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")

    # Notification
    try:
        models.create_notification(
            patient_id=patient_id,
            appointment_id=appt_id,
            title="Appointment Booked",
            message=f"Your appointment with {doctor['full_name']} on "
                    f"{payload.appointment_date.isoformat()} at {time_str[:5]} "
                    f"is booked. Please complete payment.",
            notif_type="booking",
        )
    except Exception:
        pass

    return {
        "message": "Appointment booked successfully",
        "appointment_id": appt_id,
        "slot_number": slot_num,
        "appointment_time": time_str,
    }


@app.get("/appointments/my")
def my_appointments(user=Depends(get_current_patient)):
    return models.get_appointments_by_patient(user["patient_id"])


@app.get("/appointments/{appt_id}")
def my_appointment_detail(appt_id: int, user=Depends(get_current_patient)):
    appointment = models.get_patient_appointment_by_id(appt_id, user["patient_id"])
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@app.put("/appointments/{appt_id}")
def update_my_appointment(appt_id: int, payload: schemas.AppointmentUpdate,
                          user=Depends(get_current_patient)):
    """Reschedule the date/time and/or edit the reason of a not-yet-paid appointment."""
    patient_id = user["patient_id"]
    appt = models.get_patient_appointment_by_id(appt_id, patient_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt["status"] != "Booked":
        raise HTTPException(
            status_code=400,
            detail="Only appointments awaiting payment can be updated. Cancel and rebook instead.",
        )

    new_date = payload.appointment_date or appt["appointment_date"]
    new_time_raw = payload.appointment_time or str(appt["appointment_time"])
    new_reason = payload.reason if payload.reason is not None else appt["reason"]

    reschedule_requested = bool(payload.appointment_date or payload.appointment_time)
    if not reschedule_requested:
        rows = models.update_appointment_reschedule(
            appt_id, patient_id, appt["appointment_date"], appt["appointment_time"],
            appt["slot_number"], new_reason,
        )
        if rows == 0:
            raise HTTPException(status_code=400, detail="Could not update appointment")
        return {"message": "Appointment updated successfully"}

    doctor = models.get_doctor_by_id(appt["doctor_id"])
    if not doctor or not doctor["is_active"]:
        raise HTTPException(status_code=400, detail="Doctor is not currently available")
    if new_date < date.today():
        raise HTTPException(status_code=400, detail="Appointment date cannot be in the past")

    holiday = models.get_holiday_by_date(new_date.isoformat() if hasattr(new_date, "isoformat") else new_date)
    if holiday:
        raise HTTPException(status_code=400, detail=f"Hospital closed: {holiday['reason']}")

    try:
        time_obj = parse_time_str(new_time_raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid time format")
    time_str = time_obj.strftime("%H:%M:%S")
    if time_str not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="Time slot not valid")

    new_date_str = new_date.isoformat() if hasattr(new_date, "isoformat") else new_date
    if not models.is_doctor_available(appt["doctor_id"], new_date_str, time_str):
        raise HTTPException(status_code=400, detail="Doctor is not available at this time")

    slot_num = TIME_SLOTS.index(time_str) + 1

    patient_appointments = models.get_active_patient_appointments_on_date(patient_id, new_date_str)
    for other in patient_appointments:
        if other["appointment_id"] == appt_id:
            continue
        if other["doctor_id"] == appt["doctor_id"]:
            raise HTTPException(status_code=400, detail="You already have an active appointment with this doctor on this date")
        if other["slot_number"] == slot_num:
            raise HTTPException(status_code=400, detail="This time is already booked by you on the selected date")

    booked = models.get_booked_slots(appt["doctor_id"], new_date_str)
    for b in booked:
        if b["slot_number"] == slot_num:
            raise HTTPException(status_code=400, detail="This slot is already booked")
    if len(booked) >= MAX_SLOTS_PER_DAY and new_date_str != str(appt["appointment_date"]):
        raise HTTPException(status_code=400, detail="This date is fully booked (10/10)")

    rows = models.update_appointment_reschedule(appt_id, patient_id, new_date_str, time_str, slot_num, new_reason)
    if rows == 0:
        raise HTTPException(status_code=400, detail="Could not update appointment")

    try:
        models.create_notification(
            patient_id=patient_id,
            appointment_id=appt_id,
            title="Appointment Updated",
            message=f"Your appointment has been updated to {new_date_str} at {time_str[:5]}.",
            notif_type="update",
        )
    except Exception:
        pass

    return {"message": "Appointment updated successfully", "slot_number": slot_num, "appointment_time": time_str}


@app.delete("/appointments/cancel/{appt_id}")
def cancel_my_appointment(appt_id: int, user=Depends(get_current_patient)):
    appt = models.get_appointment_by_id(appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt["patient_id"] != user["patient_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    rows = models.cancel_appointment(appt_id, user["patient_id"])
    if rows == 0:
        raise HTTPException(status_code=400,
                            detail="Cannot cancel (already cancelled/completed)")

    try:
        models.create_notification(
            patient_id=user["patient_id"],
            appointment_id=appt_id,
            title="Appointment Cancelled",
            message=f"Your appointment with {appt['doctor_name']} on "
                    f"{appt['appointment_date']} has been cancelled.",
            notif_type="cancellation",
        )
    except Exception:
        pass

    return {"message": "Appointment cancelled successfully"}


# =========================================
# NOTIFICATIONS
# =========================================
@app.get("/notifications/my")
def my_notifications(user=Depends(get_current_patient)):
    return models.get_notifications_by_patient(user["patient_id"])


@app.put("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, user=Depends(get_current_patient)):
    rows = models.mark_notification_read(notification_id, user["patient_id"])
    if rows == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


# =========================================
# PAYMENTS
# =========================================
@app.post("/payments/pay")
def make_payment(payload: schemas.PaymentRequest,
                 user=Depends(get_current_patient)):
    patient_id = user["patient_id"]

    appt = models.get_appointment_by_id(payload.appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt["patient_id"] != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    existing = models.check_payment_exists(payload.appointment_id)
    if existing:
        return {
            "message": "Payment already completed",
            "receipt_number": existing["receipt_number"],
            "amount": float(existing["amount"]),
            "payment_status": existing["payment_status"],
        }

    receipt_no = generate_receipt_number()
    fee = float(appt.get("consultation_fee") or APPOINTMENT_FEE)
    try:
        models.create_payment(
            appt_id=payload.appointment_id,
            patient_id=patient_id,
            receipt_no=receipt_no,
            amount=fee,
            method=payload.payment_method,
            status="Success",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment failed: {str(e)}")

    # Auto-confirm appointment
    try:
        models.update_appointment_status(payload.appointment_id, "Confirmed")
        models.create_notification(
            patient_id=patient_id,
            appointment_id=payload.appointment_id,
            title="Payment Successful",
            message=f"Payment of ₹{fee} received. "
                    f"Receipt: {receipt_no}. Appointment confirmed.",
            notif_type="payment",
        )
    except Exception:
        pass

    return {
        "message": "Payment successful",
        "receipt_number": receipt_no,
        "amount": fee,
        "payment_status": "Success",
    }


@app.get("/payments/my")
def my_payments(user=Depends(get_current_patient)):
    return models.get_payments_by_patient(user["patient_id"])


@app.get("/payments/{payment_id}")
def payment_detail(payment_id: int, user=Depends(get_current_patient)):
    payment = models.get_payment_by_id(payment_id, user["patient_id"])
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@app.get("/payments/appointment/{appointment_id}")
def appointment_payment(appointment_id: int, user=Depends(get_current_patient)):
    payment = models.get_payment_by_appointment(appointment_id, user["patient_id"])
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@app.get("/payments/receipt/{receipt_number}")
def payment_receipt(receipt_number: str, user=Depends(get_current_patient)):
    payment = models.get_payment_by_receipt(receipt_number)
    if not payment or payment["patient_id"] != user["patient_id"]:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return payment


# =========================================
# ADMIN
# =========================================
@app.get("/admin/dashboard")
def admin_dashboard(admin=Depends(get_current_admin)):
    return models.get_admin_dashboard_stats()


@app.get("/admin/appointments")
def admin_all_appointments(admin=Depends(get_current_admin)):
    return models.get_all_appointments()


@app.get("/admin/patients")
def admin_all_patients(admin=Depends(get_current_admin)):
    return models.get_all_patients()


@app.get("/admin/doctors")
def admin_all_doctors(admin=Depends(get_current_admin)):
    return models.get_all_doctors()


@app.post("/admin/doctors")
def admin_create_doctor(payload: schemas.DoctorCreate,
                        admin=Depends(get_current_admin)):
    try:
        doctor_id = models.create_doctor(
            payload.full_name, payload.specialization_id, payload.qualification,
            payload.experience_years, payload.phone, payload.email, payload.bio,
            payload.consultation_fee if payload.consultation_fee is not None else 500.00,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not create doctor: {exc}") from exc
    return {"message": "Doctor created", "doctor_id": doctor_id}


@app.put("/admin/doctors/{doctor_id}")
def admin_update_doctor(doctor_id: int, payload: schemas.DoctorCreate,
                        admin=Depends(get_current_admin)):
    rows = models.update_doctor(
        doctor_id, payload.full_name, payload.specialization_id,
        payload.qualification, payload.experience_years, payload.phone,
        payload.email, payload.bio, True, payload.consultation_fee,
    )
    if rows == 0:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"message": "Doctor updated"}


@app.post("/admin/doctors/{doctor_id}/availability")
def admin_add_availability(doctor_id: int, payload: schemas.AvailabilitySlot,
                           admin=Depends(get_current_admin)):
    if not models.get_doctor_by_id(doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")
    availability_id = models.add_doctor_availability(
        doctor_id, payload.day_of_week, payload.start_time, payload.end_time, payload.is_available,
    )
    return {"message": "Availability added", "availability_id": availability_id}


@app.delete("/admin/availability/{availability_id}")
def admin_delete_availability(availability_id: int, admin=Depends(get_current_admin)):
    rows = models.delete_doctor_availability(availability_id)
    if rows == 0:
        raise HTTPException(status_code=404, detail="Availability slot not found")
    return {"message": "Availability slot deleted"}


@app.get("/admin/holidays")
def admin_all_holidays(admin=Depends(get_current_admin)):
    return models.get_holidays()


@app.post("/admin/holidays")
def admin_create_holiday(payload: schemas.HolidayCreate,
                         admin=Depends(get_current_admin)):
    try:
        holiday_id = models.create_holiday(
            payload.holiday_date.isoformat(), payload.reason, admin["admin_id"]
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not create holiday: {exc}") from exc
    return {"message": "Holiday created", "holiday_id": holiday_id}


@app.delete("/admin/holidays/{holiday_id}")
def admin_delete_holiday(holiday_id: int, admin=Depends(get_current_admin)):
    rows = models.delete_holiday(holiday_id)
    if rows == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return {"message": "Holiday deleted"}


@app.get("/admin/payments")
def admin_all_payments(admin=Depends(get_current_admin)):
    return models.get_all_payments()


@app.put("/admin/appointments/{appt_id}/status")
def admin_update_status(appt_id: int, payload: schemas.AppointmentStatusUpdate,
                        admin=Depends(get_current_admin)):
    allowed = {
        "Booked", "Confirmed", "Completed",
        "Visited – Appointment Not Completed",
        "Cancelled", "No Show"
    }
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status value")

    appt = models.get_appointment_by_id(appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    rows = models.update_appointment_status(appt_id, payload.status)
    if rows == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")

    try:
        if payload.status in ("Visited – Appointment Not Completed", "No Show"):
            models.create_notification(
                patient_id=appt["patient_id"],
                appointment_id=appt_id,
                title="Previous Appointment Not Completed",
                message="Your previous appointment was not completed. "
                        "You can select another available date to book a new appointment.",
                notif_type="rebooking",
            )
        else:
            models.create_notification(
                patient_id=appt["patient_id"],
                appointment_id=appt_id,
                title="Appointment Status Updated",
                message=f"Your appointment status has been updated to '{payload.status}'.",
                notif_type="status",
            )
    except Exception:
        pass

    return {"message": "Status updated", "status": payload.status}


# =========================================
# RUN
# =========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)