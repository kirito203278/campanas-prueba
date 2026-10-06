"""Configuración central de la aplicación, leída de variables de entorno."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos
    database_url: str = "postgresql+psycopg2://campanas:campanas@db:5432/campanas"

    # JWT
    jwt_secret: str = "changeme-dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12  # 12 horas

    # Cifrado AES-GCM de credenciales de cuentas publicitarias.
    # Debe ser una clave de 32 bytes codificada en base64 (AES-256).
    aes_key_b64: str = "0" * 44  # placeholder inválido a propósito; se exige en prod

    # Huella de cuentas publicitarias (HMAC), separada de la clave AES
    huella_secret: str = "changeme-dev-huella-secret"

    # Secreto para disparar los jobs programados desde un cron externo
    # (POST /api/jobs/run/{nombre}), para hosting donde el proceso puede
    # estar dormido a la hora exacta del job.
    jobs_secret: str = "changeme-dev-jobs-secret"

    # Orígenes permitidos por CORS, separados por coma. En desarrollo son
    # los del servidor de Vite; en producción se configura con el dominio
    # real (el frontend se sirve desde el propio backend, mismo origen,
    # pero CORS igual aplica si algo lo consume desde otro origen).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Nombre de la agencia para el reporte PDF
    agencia_nombre: str = "INNquietus"

    # Sembrado de datos de prueba
    seed_on_start: bool = False
    force_seed: bool = False

    # Zona horaria del negocio (para los jobs programados)
    tz: str = "America/Mexico_City"


@lru_cache
def get_settings() -> Settings:
    return Settings()
