from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient
from app.schemas import Page, PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/api/patients", tags=["Pazienti"])


def get_patient_or_404(patient_id: int, db: Session) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Paziente non trovato")
    return patient


def check_unique_fields(db: Session, fiscal_code: str | None, email: str | None, exclude_id: int | None = None):
    if fiscal_code is not None:
        query = select(Patient).where(Patient.fiscal_code == fiscal_code)
        if exclude_id is not None:
            query = query.where(Patient.id != exclude_id)
        if db.scalar(query):
            raise HTTPException(status_code=409, detail="Esiste già un paziente con questo codice fiscale")
    if email is not None:
        query = select(Patient).where(Patient.email == email)
        if exclude_id is not None:
            query = query.where(Patient.id != exclude_id)
        if db.scalar(query):
            raise HTTPException(status_code=409, detail="Esiste già un paziente con questa email")


@router.get("", response_model=Page[PatientOut], summary="Elenco pazienti")
def list_patients(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, description="Ricerca per nome o cognome"),
    db: Session = Depends(get_db),
):
    query = select(Patient)
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(Patient.first_name.ilike(pattern), Patient.last_name.ilike(pattern)))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(Patient.last_name, Patient.first_name).offset((page - 1) * size).limit(size)
    ).all()
    return Page(items=items, total=total, page=page, size=size)


@router.get("/{patient_id}", response_model=PatientOut, summary="Dettaglio paziente")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return get_patient_or_404(patient_id, db)


@router.post("", response_model=PatientOut, status_code=201, summary="Registra un nuovo paziente")
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    check_unique_fields(db, data.fiscal_code, data.email)
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.patch("/{patient_id}", response_model=PatientOut, summary="Aggiorna un paziente")
def update_patient(patient_id: int, data: PatientUpdate, db: Session = Depends(get_db)):
    patient = get_patient_or_404(patient_id, db)
    changes = data.model_dump(exclude_unset=True)
    check_unique_fields(db, changes.get("fiscal_code"), changes.get("email"), exclude_id=patient_id)
    for field, value in changes.items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=204, summary="Elimina un paziente")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = get_patient_or_404(patient_id, db)
    db.delete(patient)
    db.commit()
