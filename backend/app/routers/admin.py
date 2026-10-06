"""Gestión de cuentas por la administradora (especificación, sección 2 y 6):
alta de CM con credenciales generadas y mostradas una sola vez, reseteo de
contraseñas, alta de otros admins (con opción de solo lectura)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.bitacora import registrar
from app.database import get_db
from app.deps import require_admin, require_admin_write
from app.models import Usuario
from app.schemas import (
    CreateAdminRequest,
    CreateCMRequest,
    CreatedCredentialsResponse,
    ResetPasswordResponse,
    UsuarioListItem,
)
from app.security.passwords import build_username, generate_secure_password, hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _existing_usernames(db: Session) -> set[str]:
    return {row[0] for row in db.query(Usuario.username).all()}


def _crear_usuario(db: Session, admin: Usuario, *, nombre: str, apellido: str | None,
                    rol: str, solo_lectura: bool, accion: str) -> CreatedCredentialsResponse:
    username = build_username(nombre, apellido, rol, _existing_usernames(db))
    password = generate_secure_password()

    usuario = Usuario(
        nombre=f"{nombre} {apellido}".strip() if apellido else nombre,
        username=username,
        password_hash=hash_password(password),
        rol=rol,
        solo_lectura=solo_lectura,
        activo=True,
        primer_ingreso=True,
    )
    db.add(usuario)
    db.flush()

    registrar(db, usuario_id=admin.id, accion=accion,
              detalle={"usuario_creado_id": usuario.id, "username": username, "rol": rol})
    db.commit()
    db.refresh(usuario)

    return CreatedCredentialsResponse(
        id=usuario.id, nombre=usuario.nombre, username=usuario.username,
        password=password, rol=usuario.rol, solo_lectura=usuario.solo_lectura,
    )


@router.post("/cms", response_model=CreatedCredentialsResponse, status_code=status.HTTP_201_CREATED)
def crear_cm(payload: CreateCMRequest, admin: Usuario = Depends(require_admin_write), db: Session = Depends(get_db)):
    return _crear_usuario(db, admin, nombre=payload.nombre, apellido=payload.apellido,
                           rol="cm", solo_lectura=False, accion="alta_cm")


@router.get("/cms", response_model=list[UsuarioListItem])
def listar_cms(admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).filter_by(rol="cm").order_by(Usuario.nombre).all()


@router.post("/admins", response_model=CreatedCredentialsResponse, status_code=status.HTTP_201_CREATED)
def crear_admin(payload: CreateAdminRequest, admin: Usuario = Depends(require_admin_write), db: Session = Depends(get_db)):
    return _crear_usuario(db, admin, nombre=payload.nombre, apellido=payload.apellido,
                           rol="admin", solo_lectura=payload.solo_lectura, accion="alta_admin")


@router.get("/admins", response_model=list[UsuarioListItem])
def listar_admins(admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).filter_by(rol="admin").order_by(Usuario.nombre).all()


@router.post("/usuarios/{usuario_id}/reset-password", response_model=ResetPasswordResponse)
def resetear_password(usuario_id: int, admin: Usuario = Depends(require_admin_write), db: Session = Depends(get_db)):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    password = generate_secure_password()
    usuario.password_hash = hash_password(password)
    registrar(db, usuario_id=admin.id, accion="reset_password",
              detalle={"usuario_id": usuario.id, "username": usuario.username})
    db.commit()

    return ResetPasswordResponse(id=usuario.id, username=usuario.username, password=password)
