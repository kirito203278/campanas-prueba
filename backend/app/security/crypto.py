"""Cifrado AES-GCM de las credenciales de cuentas publicitarias
(especificación, sección 2; esquema, tabla cuentas_publicitarias).

La clave vive en la variable de entorno AES_KEY_B64 (32 bytes, base64 ->
AES-256). Nunca se guarda en el repositorio ni en la base de datos.
"""
import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

_NONCE_LEN = 12  # 96 bits, tamaño recomendado para GCM


def _get_aesgcm() -> AESGCM:
    settings = get_settings()
    key = base64.b64decode(settings.aes_key_b64)
    if len(key) != 32:
        raise RuntimeError(
            "AES_KEY_B64 debe decodificar a 32 bytes (AES-256). "
            "Genera una con: python -c \"import secrets,base64;print(base64.b64encode(secrets.token_bytes(32)).decode())\""
        )
    return AESGCM(key)


def encrypt_value(plaintext: str) -> str:
    aesgcm = _get_aesgcm()
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_value(token: str) -> str:
    aesgcm = _get_aesgcm()
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:_NONCE_LEN], raw[_NONCE_LEN:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def compute_huella(usuario: str, password: str) -> str:
    """Hash de unicidad de una cuenta publicitaria, sin necesidad de
    descifrar (esquema, columna cuentas_publicitarias.huella)."""
    settings = get_settings()
    mensaje = f"{usuario.strip().lower()}:{password}".encode("utf-8")
    return hmac.new(settings.huella_secret.encode("utf-8"), mensaje, hashlib.sha256).hexdigest()
