"""Registro de auditoría (esquema, tabla bitacora). Las acciones destructivas
o sensibles siempre dejan rastro: borrado permanente, migración de CM,
cambios de contraseña, alta de cuentas (especificación, sección 11-7)."""
from sqlalchemy.orm import Session

from app.models import Bitacora


def registrar(db: Session, *, usuario_id: int | None, accion: str, detalle: dict | None = None) -> None:
    db.add(Bitacora(usuario_id=usuario_id, accion=accion, detalle=detalle))
