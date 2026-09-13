import os
from datetime import date, datetime, time, timedelta

os.environ["DATABASE_URL"] = "sqlite:///./test_clinica.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Appointment, AppointmentStatus, Doctor, Patient, User, UserRole
from app.security import hash_password

ADMIN_EMAIL = "admin@test.it"
ADMIN_PASSWORD = "admin123!"
PATIENT_EMAIL = "mario.verdi@test.it"
PATIENT_PASSWORD = "paziente123!"

# bcrypt è volutamente lento: gli hash delle utenze di prova si calcolano una volta sola
ADMIN_HASH = hash_password(ADMIN_PASSWORD)
PATIENT_HASH = hash_password(PATIENT_PASSWORD)


def next_weekday(days_ahead: int = 1) -> date:
    day = date.today() + timedelta(days=days_ahead)
    while day.weekday() > 4:
        day += timedelta(days=1)
    return day


def past_weekday(days_back: int = 30) -> date:
    day = date.today() - timedelta(days=days_back)
    while day.weekday() > 4:
        day -= timedelta(days=1)
    return day


def slot_at(day: date, hour: int, minute: int = 0) -> str:
    return datetime.combine(day, time(hour, minute)).isoformat()


@pytest.fixture(scope="session", autouse=True)
def rimuovi_database_di_test():
    yield
    engine.dispose()
    if os.path.exists("test_clinica.db"):
        os.remove("test_clinica.db")


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed(db):
    # Un medico da 30 minuti e uno da 15: durate diverse per verificare il calcolo degli slot
    cardiologo = Doctor(first_name="Marco", last_name="Bianchi", specialization="Cardiologia",
                        email="m.bianchi@test.it", visit_duration_minutes=30)
    generico = Doctor(first_name="Paolo", last_name="Moretti", specialization="Medicina generale",
                      email="p.moretti@test.it", visit_duration_minutes=15)
    mario = Patient(first_name="Mario", last_name="Verdi", fiscal_code="VRDMRA85M01H501Z",
                    email=PATIENT_EMAIL, birth_date=date(1985, 8, 1))
    giulia = Patient(first_name="Giulia", last_name="Bianco", fiscal_code="BNCGLI90D45F839K",
                     email="giulia.bianco@test.it", birth_date=date(1990, 4, 5))
    db.add_all([cardiologo, generico, mario, giulia])
    db.flush()

    db.add_all([
        User(email=ADMIN_EMAIL, hashed_password=ADMIN_HASH, role=UserRole.ADMIN),
        User(email=PATIENT_EMAIL, hashed_password=PATIENT_HASH,
             role=UserRole.PATIENT, patient_id=mario.id),
    ])
    db.commit()

    return {
        "cardiologo": cardiologo.id,
        "generico": generico.id,
        "mario": mario.id,
        "giulia": giulia.id,
    }


@pytest.fixture
def client(seed):
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def admin_headers(client):
    return {"Authorization": f"Bearer {login(client, ADMIN_EMAIL, ADMIN_PASSWORD)}"}


@pytest.fixture
def patient_headers(client):
    return {"Authorization": f"Bearer {login(client, PATIENT_EMAIL, PATIENT_PASSWORD)}"}


@pytest.fixture
def booked(client, seed, admin_headers, db):
    # Una visita già completata in passato, utile per storico e statistiche
    past = Appointment(
        patient_id=seed["mario"], doctor_id=seed["cardiologo"],
        scheduled_at=datetime.combine(past_weekday(), time(10, 0)),
        reason="Elettrocardiogramma", status=AppointmentStatus.COMPLETED,
    )
    db.add(past)
    db.commit()

    res = client.post("/api/appointments", headers=admin_headers, json={
        "doctor_id": seed["cardiologo"],
        "patient_id": seed["mario"],
        "scheduled_at": slot_at(next_weekday(), 10),
        "reason": "Visita di controllo",
    })
    assert res.status_code == 201
    return res.json()
