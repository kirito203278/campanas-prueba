"""Job: DIARIO 12:00 — campañas con fecha_renovacion = hoy (especificación,
secciones 5 y 11-4):
  1) calcula y archiva el mensual del ciclo que termina,
  2) borra semanales y observaciones SOLO de esa campaña,
  3) la campaña pasa a 'vencida' y queda bloqueada hasta que el CM resuelva
     la renovación (ver endpoints /cm/campanas/{id}/renovar y
     /cm/clientes/{id}/no-renovar).
"""
import datetime as dt
import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.metrics import calcular_rendimiento_ciclo
from app.models import Campana, Mensual, Notificacion, Observacion, Semana

logger = logging.getLogger("jobs.cierre_ciclo")


def cerrar_ciclo_campana(db: Session, campana: Campana) -> Mensual:
    """Reutilizable: hace el archivado/borrado/bloqueo de UNA campaña. No
    hace commit; el llamador controla la transacción."""
    semanas = db.query(Semana).filter_by(campana_id=campana.id).order_by(Semana.inicio).all()

    mensajes_total = sum(s.mensajes or 0 for s in semanas)
    gasto_total = sum(float(s.importe_gastado or 0) for s in semanas)
    costo_por_mensaje = (gasto_total / mensajes_total) if mensajes_total else 0.0
    sobrante = float(campana.presupuesto) - gasto_total
    rendimiento = calcular_rendimiento_ciclo(db, campana, costo_por_mensaje, semanas)

    mensual = Mensual(
        campana_id=campana.id,
        periodo_inicio=campana.fecha_inicio,
        periodo_fin=campana.fecha_renovacion,
        mensajes_total=mensajes_total,
        gasto_total=round(gasto_total, 2),
        costo_por_mensaje=round(costo_por_mensaje, 2),
        presupuesto=campana.presupuesto,
        sobrante=round(sobrante, 2),
        rendimiento=rendimiento,
        origen="calculado",
    )
    db.add(mensual)

    db.query(Observacion).filter_by(campana_id=campana.id).delete(synchronize_session=False)
    db.query(Semana).filter_by(campana_id=campana.id).delete(synchronize_session=False)

    campana.estado = "vencida"

    cm_id = campana.cliente.cm_id
    db.add(Notificacion(
        usuario_id=cm_id, tipo="vencimiento",
        mensaje=f"La campaña \"{campana.nombre}\" de {campana.cliente.nombre} llegó a su fecha de renovación. "
                f"Confirma si el cliente renovó o no para poder seguir capturando.",
    ))

    return mensual


def cerrar_ciclo() -> None:
    db = SessionLocal()
    try:
        hoy = dt.date.today()
        campanas = db.query(Campana).filter(Campana.estado == "activa", Campana.fecha_renovacion == hoy).all()

        for campana in campanas:
            cerrar_ciclo_campana(db, campana)

        db.commit()
        logger.info("cierre_ciclo: %s campañas cerradas", len(campanas))
    except Exception:
        db.rollback()
        logger.exception("cierre_ciclo falló")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cerrar_ciclo()
