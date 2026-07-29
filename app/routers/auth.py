from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, User, UserRole
from app.routers.patients import check_unique_fields
from app.schemas import LoginOut, RegisterIn, UserOut
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Autenticazione"])


@router.post("/register", response_model=UserOut, status_code=201, summary="Registrazione di un nuovo paziente")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    check_unique_fields(db, data.fiscal_code, data.email)
    if db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(status_code=409, detail="Esiste già un utente con questa email")

    patient = Patient(**data.model_dump(exclude={"password"}))
    db.add(patient)
    db.flush()
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.PATIENT,
        patient_id=patient.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=LoginOut, summary="Login con email e password")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email o password errati")
    return LoginOut(access_token=create_access_token(user))


@router.get("/me", response_model=UserOut, summary="Profilo dell'utente autenticato")
def me(user: User = Depends(get_current_user)):
    return user
