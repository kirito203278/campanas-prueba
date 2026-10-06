from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Usuario
from app.schemas import LoginRequest, TokenResponse, UserOut
from app.security.jwt import create_access_token
from app.security.passwords import verify_password
from app.security.rate_limit import bloqueado, limpiar_intentos, registrar_intento_fallido

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    # Detrás de un reverse proxy el IP real viene en X-Forwarded-For.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "desconocido"


def _rate_key(request: Request, username: str) -> str:
    """Clave de rate limit por (IP, usuario). Antes se usaba solo el username,
    lo que permitía que un tercero bloqueara la cuenta de un CM legítimo
    fallando a propósito 5 veces con su usuario. Con la IP en la clave, el
    bloqueo afecta solo a quien está fallando, no a la víctima desde su IP."""
    return f"{_client_ip(request)}|{username.lower()}"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    rate_key = _rate_key(request, payload.username)
    if bloqueado(rate_key):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                             "Demasiados intentos fallidos. Espera unos minutos e intenta de nuevo")

    user = db.query(Usuario).filter_by(username=payload.username).one_or_none()
    if user is None or not user.activo or not verify_password(payload.password, user.password_hash):
        registrar_intento_fallido(rate_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos")

    limpiar_intentos(rate_key)
    token = create_access_token(user_id=user.id, rol=user.rol, solo_lectura=user.solo_lectura)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: Usuario = Depends(get_current_user)):
    return UserOut.model_validate(user)
