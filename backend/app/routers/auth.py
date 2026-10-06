from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Usuario
from app.schemas import LoginRequest, TokenResponse, UserOut
from app.security.jwt import create_access_token
from app.security.passwords import verify_password
from app.security.rate_limit import bloqueado, limpiar_intentos, registrar_intento_fallido

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if bloqueado(payload.username):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                             "Demasiados intentos fallidos. Espera unos minutos e intenta de nuevo")

    user = db.query(Usuario).filter_by(username=payload.username).one_or_none()
    if user is None or not user.activo or not verify_password(payload.password, user.password_hash):
        registrar_intento_fallido(payload.username)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos")

    limpiar_intentos(payload.username)
    token = create_access_token(user_id=user.id, rol=user.rol, solo_lectura=user.solo_lectura)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: Usuario = Depends(get_current_user)):
    return UserOut.model_validate(user)
