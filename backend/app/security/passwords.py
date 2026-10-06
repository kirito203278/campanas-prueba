"""Hash de contraseñas de la app (bcrypt) y generación de credenciales
seguras para el alta de CMs/admins (especificación, sección 2)."""
import re
import secrets
import string
import unicodedata

import bcrypt

_SYMBOLS = "!@#$%^&*-_=+?"
_PASSWORD_LENGTH = 18


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def generate_secure_password(length: int = _PASSWORD_LENGTH) -> str:
    """Contraseña aleatoria CSPRNG con mayúsculas, minúsculas, números y
    símbolos garantizados, 16+ caracteres (especificación, sección 2)."""
    if length < 16:
        length = 16
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, _SYMBOLS]
    # Garantiza al menos un carácter de cada clase.
    chars = [secrets.choice(pool) for pool in pools]
    all_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + _SYMBOLS
    chars += [secrets.choice(all_chars) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def slugify_username_part(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return normalized


def build_username(nombre: str, apellido: str | None, rol: str, existing_usernames: set[str]) -> str:
    """Deriva el username a partir del nombre ('luz.hernandez'); si hay
    colisión agrega el rol o un sufijo numérico para garantizar unicidad."""
    nombre_slug = slugify_username_part(nombre)
    apellido_slug = slugify_username_part(apellido) if apellido else ""

    base = f"{nombre_slug}.{apellido_slug}" if apellido_slug else nombre_slug
    candidate = base
    if candidate not in existing_usernames:
        return candidate

    candidate = f"{base}.{rol}"
    if candidate not in existing_usernames:
        return candidate

    n = 2
    while f"{base}{n}" in existing_usernames:
        n += 1
    return f"{base}{n}"
