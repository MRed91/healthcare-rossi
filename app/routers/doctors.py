from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor
from app.scheduling import free_slots
from app.schemas import DoctorCreate, DoctorOut, DoctorUpdate, Page
from app.security import require_admin

router = APIRouter(prefix="/api/doctors", tags=["Medici"])


def get_doctor_or_404(doctor_id: int, db: Session) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Medico non trovato")
    return doctor


def check_unique_email(db: Session, email: str | None, exclude_id: int | None = None):
    if email is None:
        return
    query = select(Doctor).where(Doctor.email == email)
    if exclude_id is not None:
        query = query.where(Doctor.id != exclude_id)
    if db.scalar(query):
        raise HTTPException(status_code=409, detail="Esiste già un medico con questa email")


@router.get("", response_model=Page[DoctorOut], summary="Elenco medici")
def list_doctors(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    specialization: str | None = Query(default=None, description="Filtra per specializzazione"),
    db: Session = Depends(get_db),
):
    query = select(Doctor)
    if specialization:
        query = query.where(func.lower(Doctor.specialization) == specialization.lower())
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(Doctor.last_name, Doctor.first_name).offset((page - 1) * size).limit(size)
    ).all()
    return Page(items=items, total=total, page=page, size=size)


@router.get("/specializations", response_model=list[str], summary="Elenco specializzazioni disponibili")
def list_specializations(db: Session = Depends(get_db)):
    rows = db.scalars(select(Doctor.specialization).distinct().order_by(Doctor.specialization)).all()
    return rows


@router.get("/{doctor_id}", response_model=DoctorOut, summary="Dettaglio medico")
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    return get_doctor_or_404(doctor_id, db)


@router.get("/{doctor_id}/slots", response_model=list[datetime], summary="Orari liberi del medico in una giornata")
def list_free_slots(
    doctor_id: int,
    day: date = Query(description="Giornata richiesta, formato AAAA-MM-GG"),
    db: Session = Depends(get_db),
):
    doctor = get_doctor_or_404(doctor_id, db)
    return free_slots(db, doctor, day)


@router.post("", response_model=DoctorOut, status_code=201, summary="Inserisce un nuovo medico",
             dependencies=[Depends(require_admin)])
def create_doctor(data: DoctorCreate, db: Session = Depends(get_db)):
    check_unique_email(db, data.email)
    doctor = Doctor(**data.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.patch("/{doctor_id}", response_model=DoctorOut, summary="Aggiorna un medico",
              dependencies=[Depends(require_admin)])
def update_doctor(doctor_id: int, data: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = get_doctor_or_404(doctor_id, db)
    changes = data.model_dump(exclude_unset=True)
    check_unique_email(db, changes.get("email"), exclude_id=doctor_id)
    for field, value in changes.items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=204, summary="Elimina un medico",
               dependencies=[Depends(require_admin)])
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = get_doctor_or_404(doctor_id, db)
    db.delete(doctor)
    db.commit()
