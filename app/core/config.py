from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Centro Medico Rossi"
    app_description: str = (
        "Centro Medico basato su API REST per la gestione delle prenotazioni di visite mediche "
        "di una clinica privata. Project Work CdS L-31."
    )
    app_version: str = "1.0"
    debug: bool = True
    database_url: str = "sqlite:///./clinica.db"
    secret_key: str = "chiave-di-sviluppo-da-sostituire-in-produzione"
    access_token_expire_minutes: int = 60
    clinic_open_hour: int = 9
    clinic_close_hour: int = 18
    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
