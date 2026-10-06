"""Validación de secretos al arrancar (corrige el riesgo de desplegar con
secretos débiles/placeholder)."""
import base64
import secrets

import pytest
from pydantic import ValidationError

from app.config import Settings

BUENOS = dict(
    database_url="postgresql://u:p@localhost/db",
    jwt_secret=secrets.token_urlsafe(48),
    huella_secret=secrets.token_urlsafe(48),
    jobs_secret=secrets.token_urlsafe(24),
    aes_key_b64=base64.b64encode(secrets.token_bytes(32)).decode(),
)


def _settings(**over):
    datos = {**BUENOS, **over}
    return Settings(_env_file=None, **datos)


def test_config_valida_acepta_secretos_fuertes():
    s = _settings()
    assert s.jwt_secret and s.aes_key_b64
    # normaliza el esquema de la URL a psycopg2
    assert s.database_url.startswith("postgresql+psycopg2://")


def test_rechaza_jwt_secret_corto():
    with pytest.raises(ValidationError):
        _settings(jwt_secret="corto")


def test_rechaza_huella_secret_corto():
    with pytest.raises(ValidationError):
        _settings(huella_secret="corto")


def test_rechaza_jobs_secret_corto():
    with pytest.raises(ValidationError):
        _settings(jobs_secret="123")


def test_rechaza_aes_invalida_no_32_bytes():
    with pytest.raises(ValidationError):
        _settings(aes_key_b64=base64.b64encode(secrets.token_bytes(16)).decode())


def test_rechaza_aes_no_base64():
    with pytest.raises(ValidationError):
        _settings(aes_key_b64="esto-no-es-base64-valido-$$$")
