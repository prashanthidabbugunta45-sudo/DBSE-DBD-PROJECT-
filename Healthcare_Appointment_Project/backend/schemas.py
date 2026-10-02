from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from datetime import date, time


# =========================================
# AUTH
# =========================================
class PatientRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    phone: str
    date_of_birth: date
    age: int
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_number: Optional[str] = None


class PatientLogin(BaseModel):
    login_identifier: Optional[str] = None
    login_id: Optional[str] = None
    password: str

    @model_validator(mode="before")
    @classmethod
    def normalize_login_identifier(cls, data):
        if isinstance(data, dict):
            if data.get("login_identifier") is None and data.get("login_id") is not None:
                data["login_identifier"] = data["login_id"]
            if data.get("login_id") is None and data.get("login_identifier") is not None:
                data["login_id"] = data["login_identifier"]
        return data


class AdminLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    patient_id: Optional[str] = None
    full_name: Optional[str] = None


# =========================================
# APPOINTMENTS
# =========================================
class AppointmentBook(BaseModel):
    doctor_id: int
    specialization_id: int
    appointment_date: date
    appointment_time: str
    reason: str


class AppointmentStatusUpdate(BaseModel):
    status: str


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    reason: Optional[str] = None


class DoctorCreate(BaseModel):
    full_name: str
    specialization_id: int
    qualification: Optional[str] = None
    experience_years: int = 0
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    consultation_fee: Optional[float] = None


class AvailabilitySlot(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str
    is_available: bool = True


class HolidayCreate(BaseModel):
    holiday_date: date
    reason: str


# =========================================
# PAYMENTS
# =========================================
class PaymentRequest(BaseModel):
    appointment_id: int
    payment_method: str