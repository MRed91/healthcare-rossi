from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, AppointmentStatus, Doctor, Patient, User, UserRole
from app.scheduling import check_doctor_conflict, check_patient_conflict, clinic_day_bounds, validate_slot
from app.schemas import AppointmentCreate, AppointmentOut, Page
from app.security import get_current_user, require_admin

router = APIRouter(prefix="/api/appointments", tags=["Prenotazioni"])


def get_appointment_or_404(appointment_id: int, db: Session) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Prenotazione non trovata")
    return appointment


def check_ownership(appointment: Appointment, user: User):
    if user.role != UserRole.ADMIN and appointment.patient_id != user.patient_id:
        raise HTTPException(status_code=403, detail="Non puoi operare su prenotazioni di altri pazienti")


@router.get("", response_model=Page[AppointmentOut], summary="Elenco prenotazioni")
def list_appointments(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    doctor_id: int | None = None,
    day: date | None = Query(default=None, description="Filtra per giornata"),
    status: AppointmentStatus | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Appointment)
    if user.role != UserRole.ADMIN:
        query = query.where(Appointment.patient_id == user.patient_id)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if day:
        opening, closing = clinic_day_bounds(day)
        query = query.where(Appointment.scheduled_at >= opening, Appointment.scheduled_at < closing)
    if status:
        query = query.where(Appointment.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(Appointment.scheduled_at).offset((page - 1) * size).limit(size)
    ).all()
    return Page(items=items, total=total, page=page, size=size)


@router.get("/{appointment_id}", response_model=AppointmentOut, summary="Dettaglio prenotazione")
def get_appointment(appointment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appointment = get_appointment_or_404(appointment_id, db)
    check_ownership(appointment, user)
    return appointment


@router.post("", response_model=AppointmentOut, status_code=201, summary="Crea una prenotazione")
def create_appointment(data: AppointmentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.ADMIN:
        if data.patient_id is None:
            raise HTTPException(status_code=422, detail="patient_id obbligatorio per l'amministrazione")
        patient_id = data.patient_id
        if db.get(Patient, patient_id) is None:
            raise HTTPException(status_code=404, detail="Paziente non trovato")
    else:
        if data.patient_id is not None and data.patient_id != user.patient_id:
            raise HTTPException(status_code=403, detail="Non puoi prenotare per altri pazienti")
        patient_id = user.patient_id

    doctor = db.get(Doctor, data.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Medico non trovato")

    validate_slot(doctor, data.scheduled_at)
    check_doctor_conflict(db, doctor, data.scheduled_at)
    check_patient_conflict(db, patient_id, doctor, data.scheduled_at)

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor.id,
        scheduled_at=data.scheduled_at,
        reason=data.reason,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut, summary="Annulla una prenotazione")
def cancel_appointment(appointment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appointment = get_appointment_or_404(appointment_id, db)
    check_ownership(appointment, user)
    if appointment.status != AppointmentStatus.BOOKED:
        raise HTTPException(status_code=409, detail="Si possono annullare solo prenotazioni attive")
    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/complete", response_model=AppointmentOut, summary="Segna una visita come completata",
             dependencies=[Depends(require_admin)])
def complete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = get_appointment_or_404(appointment_id, db)
    if appointment.status != AppointmentStatus.BOOKED:
        raise HTTPException(status_code=409, detail="Si possono completare solo prenotazioni attive")
    appointment.status = AppointmentStatus.COMPLETED
    db.commit()
    db.refresh(appointment)
    return appointment
