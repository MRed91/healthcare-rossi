from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, AppointmentStatus, Doctor, Patient
from app.schemas import DayCount, DoctorCount, StatsOut
from app.security import require_admin

router = APIRouter(prefix="/api/stats", tags=["Statistiche"], dependencies=[Depends(require_admin)])


@router.get("", response_model=StatsOut, summary="Statistiche della clinica")
def get_stats(db: Session = Depends(get_db)):
    def count_by_status(status: AppointmentStatus) -> int:
        return db.scalar(
            select(func.count()).select_from(Appointment).where(Appointment.status == status)
        )

    today = date.today()
    horizon = today + timedelta(days=7)
    rows = db.execute(
        select(func.date(Appointment.scheduled_at), func.count())
        .where(
            Appointment.status == AppointmentStatus.BOOKED,
            Appointment.scheduled_at >= datetime.combine(today, datetime.min.time()),
            Appointment.scheduled_at < datetime.combine(horizon, datetime.min.time()),
        )
        .group_by(func.date(Appointment.scheduled_at))
    ).all()
    counts = {date.fromisoformat(str(day)): count for day, count in rows}
    next_days = [
        DayCount(day=today + timedelta(days=offset), count=counts.get(today + timedelta(days=offset), 0))
        for offset in range(7)
    ]

    per_doctor = [
        DoctorCount(doctor=f"{last_name} {first_name}", specialization=specialization, count=count)
        for last_name, first_name, specialization, count in db.execute(
            select(Doctor.last_name, Doctor.first_name, Doctor.specialization, func.count(Appointment.id))
            .join(Appointment, Appointment.doctor_id == Doctor.id)
            .where(Appointment.status != AppointmentStatus.CANCELLED)
            .group_by(Doctor.id)
            .order_by(func.count(Appointment.id).desc())
        ).all()
    ]

    return StatsOut(
        total_patients=db.scalar(select(func.count()).select_from(Patient)),
        active_appointments=db.scalar(
            select(func.count()).select_from(Appointment).where(
                Appointment.status == AppointmentStatus.BOOKED,
                Appointment.scheduled_at >= datetime.now(),
            )
        ),
        completed_appointments=count_by_status(AppointmentStatus.COMPLETED),
        cancelled_appointments=count_by_status(AppointmentStatus.CANCELLED),
        next_days=next_days,
        per_doctor=per_doctor,
    )
