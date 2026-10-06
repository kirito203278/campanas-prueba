"""Configuración central de la aplicación, leída de variables de entorno.

Los secretos NO tienen valor por defecto: la app se niega a arrancar si falta
alguno o si es débil. Esto evita el riesgo de desplegar en producción con un
JWT firmable por cualquiera o con una clave AES inválida (antes el backend
arrancaba igual con 'changeme-dev-secret'). Genera valores reales con:
    python -c "import secrets, base64; \
print('JWT_SECRET=' + secrets.token_urlsafe(48)); \
print('HUELLA_SECRET=' + secrets.token_urlsafe(32)); \
print('JOBS_SECRET=' + secrets.token_urlsafe(24)); \
print('AES_KEY_B64=' + base64.b64encode(secrets.token_bytes(32)).decode())"
"""
import base64
import binascii
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos (requerida).
    database_url: str

    # JWT (secreto requerido; algoritmo y expiración con default razonable).
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12  # 12 horas

    # Cifrado AES-GCM de credenciales de cuentas publicitarias.
    # Clave de 32 bytes codificada en base64 (AES-256). Requerida.
    aes_key_b64: str

    # Huella de cuentas publicitarias (HMAC), separada de la clave AES. Requerida.
    huella_secret: str

    # Secreto para disparar los jobs programados desde un cron externo
    # (POST /api/jobs/run/{nombre}). Requerido.
    jobs_secret: str

    # Orígenes permitidos por CORS, separados por coma.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Nombre de la agencia para el reporte PDF
    agencia_nombre: str = "INNquietus"

    # Sembrado de datos de prueba
    seed_on_start: bool = False
    force_seed: bool = False

    # Zona horaria del negocio (para los jobs programados)
    tz: str = "America/Mexico_City"

    # Constantes de negocio (antes eran literales dispersos en el código).
    # Días en "No renovados" tras los cuales el job de purga elimina al cliente.
    purga_no_renovados_dias: int = 365
    # Plazo para "continuar" con la última campaña de un cliente no renovado
    # en vez de empezar de cero ("borrón y cuenta nueva").
    continuar_no_renovado_dias: int = 60

    @field_validator("database_url")
    @classmethod
    def _normalizar_url_bd(cls, v: str) -> str:
        for prefijo in ("postgres://", "postgresql://"):
            if v.startswith(prefijo):
                return "postgresql+psycopg2://" + v[len(prefijo):]
        return v

    @field_validator("jwt_secret", "huella_secret")
    @classmethod
    def _secreto_fuerte_32(cls, v: str, info) -> str:
        if len(v) < 32 or v.startswith("__"):
            raise ValueError(f"{info.field_name.upper()} debe tener al menos 32 caracteres "
                             "(genera uno aleatorio; no uses el placeholder de .env.example)")
        return v

    @field_validator("jobs_secret")
    @classmethod
    def _jobs_fuerte(cls, v: str) -> str:
        if len(v) < 16 or v.startswith("__"):
            raise ValueError("JOBS_SECRET debe tener al menos 16 caracteres")
        return v

    @field_validator("aes_key_b64")
    @classmethod
    def _aes_valida(cls, v: str) -> str:
        try:
            ok = len(base64.b64decode(v, validate=True)) == 32
        except (binascii.Error, ValueError):
            ok = False
        if not ok:
            raise ValueError("AES_KEY_B64 debe ser una clave de 32 bytes en base64 (AES-256). "
                             'Genera una con: python -c "import secrets,base64;'
                             'print(base64.b64encode(secrets.token_bytes(32)).decode())"')
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
