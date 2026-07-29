from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Appointment, AppointmentStatus, Doctor


def clinic_day_bounds(day: date) -> tuple[datetime, datetime]:
    settings = get_settings()
    opening = datetime(day.year, day.month, day.day, settings.clinic_open_hour)
    closing = datetime(day.year, day.month, day.day, settings.clinic_close_hour)
    return opening, closing


def validate_slot(doctor: Doctor, start: datetime):
    if start.weekday() > 4:
        raise HTTPException(status_code=422, detail="La clinica è chiusa nel fine settimana")
    if start < datetime.now():
        raise HTTPException(status_code=422, detail="Non è possibile prenotare nel passato")

    opening, closing = clinic_day_bounds(start.date())
    duration = timedelta(minutes=doctor.visit_duration_minutes)
    if start < opening or start + duration > closing:
        raise HTTPException(status_code=422, detail="Orario fuori dall'apertura della clinica")

    offset = (start - opening).total_seconds() / 60
    if offset % doctor.visit_duration_minutes != 0:
        raise HTTPException(status_code=422, detail="L'orario non corrisponde a uno slot valido per questo medico")


def booked_appointments(db: Session, doctor_id: int, day: date) -> list[Appointment]:
    opening, closing = clinic_day_bounds(day)
    return list(db.scalars(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.scheduled_at >= opening,
            Appointment.scheduled_at < closing,
        )
    ))


def check_doctor_conflict(db: Session, doctor: Doctor, start: datetime):
    duration = timedelta(minutes=doctor.visit_duration_minutes)
    for existing in booked_appointments(db, doctor.id, start.date()):
        if abs(existing.scheduled_at - start) < duration:
            raise HTTPException(status_code=409, detail="Il medico ha già una prenotazione in questo orario")


def check_patient_conflict(db: Session, patient_id: int, doctor: Doctor, start: datetime):
    opening, closing = clinic_day_bounds(start.date())
    end = start + timedelta(minutes=doctor.visit_duration_minutes)
    same_day = db.scalars(
        select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.scheduled_at >= opening,
            Appointment.scheduled_at < closing,
        )
    )
    for existing in same_day:
        existing_end = existing.scheduled_at + timedelta(minutes=existing.doctor.visit_duration_minutes)
        if existing.scheduled_at < end and start < existing_end:
            raise HTTPException(status_code=409, detail="Il paziente ha già una prenotazione in questo orario")


def free_slots(db: Session, doctor: Doctor, day: date) -> list[datetime]:
    if day.weekday() > 4:
        return []
    opening, closing = clinic_day_bounds(day)
    duration = timedelta(minutes=doctor.visit_duration_minutes)
    busy = [a.scheduled_at for a in booked_appointments(db, doctor.id, day)]
    now = datetime.now()

    slots = []
    current = opening
    while current + duration <= closing:
        if current > now and all(abs(b - current) >= duration for b in busy):
            slots.append(current)
        current += duration
    return slots
