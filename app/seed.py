from datetime import date, datetime, time, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Appointment, AppointmentStatus, Doctor, Patient, User, UserRole
from app.security import hash_password


def create_users(db):
    if db.query(User).first():
        return 0
    users = [User(email="admin@centromedicorossi.it", hashed_password=hash_password("admin123!"),
                  role=UserRole.ADMIN)]
    for patient in db.query(Patient).all():
        users.append(User(email=patient.email, hashed_password=hash_password("paziente123!"),
                          role=UserRole.PATIENT, patient_id=patient.id))
    db.add_all(users)
    db.commit()
    return len(users)


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Doctor).first():
            created = create_users(db)
            if created:
                print(f"Database già popolato, aggiunti {created} utenti")
            else:
                print("Database già popolato, nessuna modifica")
            return

        doctors = [
            Doctor(first_name="Marco", last_name="Bianchi", specialization="Cardiologia",
                   email="m.bianchi@centromedicorossi.it", phone="0651234501", visit_duration_minutes=30),
            Doctor(first_name="Laura", last_name="Ferrari", specialization="Dermatologia",
                   email="l.ferrari@centromedicorossi.it", phone="0651234502", visit_duration_minutes=20),
            Doctor(first_name="Andrea", last_name="Russo", specialization="Ortopedia",
                   email="a.russo@centromedicorossi.it", phone="0651234503", visit_duration_minutes=30),
            Doctor(first_name="Elena", last_name="Greco", specialization="Oculistica",
                   email="e.greco@centromedicorossi.it", phone="0651234504", visit_duration_minutes=20),
            Doctor(first_name="Paolo", last_name="Moretti", specialization="Medicina generale",
                   email="p.moretti@centromedicorossi.it", phone="0651234505", visit_duration_minutes=15),
        ]

        patients = [
            Patient(first_name="Mario", last_name="Verdi", fiscal_code="VRDMRA85M01H501Z",
                    email="mario.verdi@example.com", phone="3331112201", birth_date=date(1985, 8, 1)),
            Patient(first_name="Giulia", last_name="Bianco", fiscal_code="BNCGLI90D45F839K",
                    email="giulia.bianco@example.com", phone="3331112202", birth_date=date(1990, 4, 5)),
            Patient(first_name="Luca", last_name="Ferraro", fiscal_code="FRRLCU78T10L219P",
                    email="luca.ferraro@example.com", phone="3331112203", birth_date=date(1978, 12, 10)),
            Patient(first_name="Sara", last_name="Esposito", fiscal_code="SPSSRA95E52A662W",
                    email="sara.esposito@example.com", birth_date=date(1995, 5, 12)),
        ]

        db.add_all(doctors + patients)
        db.flush()

        appointments = [
            Appointment(patient=patients[0], doctor=doctors[0],
                        scheduled_at=datetime.combine(date.today() + timedelta(days=3), time(10, 0)),
                        reason="Visita di controllo"),
            Appointment(patient=patients[1], doctor=doctors[1],
                        scheduled_at=datetime.combine(date.today() + timedelta(days=5), time(16, 20)),
                        reason="Controllo nei"),
            Appointment(patient=patients[2], doctor=doctors[0],
                        scheduled_at=datetime.combine(date.today() - timedelta(days=7), time(9, 30)),
                        reason="Elettrocardiogramma", status=AppointmentStatus.COMPLETED),
        ]

        db.add_all(appointments)
        db.commit()
        created = create_users(db)
        print(f"Inseriti {len(doctors)} medici, {len(patients)} pazienti, "
              f"{len(appointments)} appuntamenti, {created} utenti")
        print("Credenziali di prova: admin@centromedicorossi.it / admin123! - "
              "mario.verdi@example.com / paziente123!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
