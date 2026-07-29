from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.database import Base, engine
from app.routers import appointments, auth, doctors, patients

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> FastAPI:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
    )

    @app.get("/health", tags=["Sistema"], summary="Verifica stato del servizio")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    app.include_router(auth.router)
    app.include_router(patients.router)
    app.include_router(doctors.router)
    app.include_router(appointments.router)

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()
