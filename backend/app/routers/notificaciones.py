"""Notificaciones en la app (especificación, sección 8, capa 1). El frontend
sondea este endpoint y usa la Web Notifications API del navegador para la
notificación nativa del sistema (capa 2) mientras la app esté abierta."""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Notificacion, Usuario

router = APIRouter(prefix="/api/notificaciones", tags=["notificaciones"])


class NotificacionOut(BaseModel):
    id: int
    tipo: str
    mensaje: str
    leida: bool
    creado_en: dt.datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[NotificacionOut])
def listar(solo_no_leidas: bool = False, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Notificacion).filter_by(usuario_id=user.id)
    if solo_no_leidas:
        q = q.filter_by(leida=False)
    return q.order_by(Notificacion.creado_en.desc()).limit(50).all()


@router.post("/{notificacion_id}/leer", response_model=NotificacionOut)
def marcar_leida(notificacion_id: int, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.get(Notificacion, notificacion_id)
    if notif is None or notif.usuario_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificación no encontrada")
    notif.leida = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/leer-todas")
def marcar_todas_leidas(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notificacion).filter_by(usuario_id=user.id, leida=False).update({Notificacion.leida: True})
    db.commit()
    return {"ok": True}
