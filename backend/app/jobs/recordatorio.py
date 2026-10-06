"""Job: VIERNES 14:00 — notifica a cada CM que tenga semanas sin capturar
(especificación, secciones 4 y 8). La fecha límite es viernes 15:00; esta
notificación llega una hora antes."""
import datetime as dt
import logging

from sqlalchemy import cast, Date

from app.database import SessionLocal
from app.dates import most_recent_saturday
from app.models import Campana, Cliente, Notificacion, Semana

logger = logging.getLogger("jobs.recordatorio")


def recordatorio_captura() -> None:
    db = SessionLocal()
    try:
        hoy = dt.date.today()
        inicio_actual = most_recent_saturday(hoy)

        pendientes = (
            db.query(Cliente.cm_id, Cliente.nombre, Campana.nombre)
            .join(Campana, Campana.cliente_id == Cliente.id)
            .join(Semana, Semana.campana_id == Campana.id)
            .filter(
                Campana.estado == "activa",
                Semana.inicio == inicio_actual,
                Semana.editable.is_(True),
                Semana.mensajes.is_(None),
            )
            .all()
        )

        por_cm: dict[int, list[str]] = {}
        for cm_id, cliente_nombre, campana_nombre in pendientes:
            por_cm.setdefault(cm_id, []).append(f"{cliente_nombre} — {campana_nombre}")

        creadas = 0
        for cm_id, campanas in por_cm.items():
            ya_avisado_hoy = (
                db.query(Notificacion)
                .filter(
                    Notificacion.usuario_id == cm_id,
                    Notificacion.tipo == "recordatorio_captura",
                    cast(Notificacion.creado_en, Date) == hoy,
                )
                .first()
            )
            if ya_avisado_hoy:
                continue

            if len(campanas) == 1:
                mensaje = f"Te falta capturar la semana de {campanas[0]}. La fecha límite es hoy a las 3:00 pm."
            else:
                lista = "; ".join(campanas)
                mensaje = f"Te faltan {len(campanas)} campañas por capturar esta semana: {lista}. La fecha límite es hoy a las 3:00 pm."

            db.add(Notificacion(usuario_id=cm_id, tipo="recordatorio_captura", mensaje=mensaje))
            creadas += 1

        db.commit()
        logger.info("recordatorio_captura: %s CMs notificados", creadas)
    except Exception:
        db.rollback()
        logger.exception("recordatorio_captura falló")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    recordatorio_captura()
