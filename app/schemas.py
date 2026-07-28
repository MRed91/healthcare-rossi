import re
from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import AppointmentStatus, UserRole

FISCAL_CODE_RE = re.compile(r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$")

T = TypeVar("T")


def normalize_fiscal_code(value: str) -> str:
    value = value.strip().upper()
    if not FISCAL_CODE_RE.fullmatch(value):
        raise ValueError("codice fiscale non valido")
    return value


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


class PatientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    fiscal_code: str
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    birth_date: date

    @field_validator("fiscal_code")
    @classmethod
    def check_fiscal_code(cls, value: str) -> str:
        return normalize_fiscal_code(value)


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    fiscal_code: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    birth_date: date | None = None

    @field_validator("fiscal_code")
    @classmethod
    def check_fiscal_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_fiscal_code(value)


class PatientOut(PatientBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DoctorBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    specialization: str = Field(min_length=1, max_length=50)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    visit_duration_minutes: int = Field(default=30, ge=10, le=120)


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    specialization: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    visit_duration_minutes: int | None = Field(default=None, ge=10, le=120)


class DoctorOut(DoctorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RegisterIn(PatientBase):
    password: str = Field(min_length=8, max_length=72)


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    patient: PatientOut | None

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(BaseModel):
    doctor_id: int
    scheduled_at: datetime
    reason: str | None = Field(default=None, max_length=200)
    patient_id: int | None = None

    @field_validator("scheduled_at")
    @classmethod
    def strip_timezone(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=None)


class AppointmentOut(BaseModel):
    id: int
    scheduled_at: datetime
    reason: str | None
    status: AppointmentStatus
    doctor: DoctorOut
    patient: PatientOut

    model_config = ConfigDict(from_attributes=True)
