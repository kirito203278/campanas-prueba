"""Job: SÁBADO 00:00 — rellena en 0 (en vez de dejarlas en blanco) las
semanas que nunca se capturaron, bloquea la semana que terminó y crea la
fila de la semana nueva en cada campaña activa (especificación, sección 4)."""
import datetime as dt
import logging

from app.database import SessionLocal
from app.dates import week_range_for
from app.models import Campana, Semana

logger = logging.getLogger("jobs.cierre_semana")


def cerrar_semana() -> None:
    db = SessionLocal()
    try:
        hoy = dt.date.today()
        inicio_actual, fin_actual = week_range_for(hoy)

        vencidas_filtro = (Semana.editable.is_(True), Semana.fin < inicio_actual)

        sin_capturar = (
            db.query(Semana)
            .filter(*vencidas_filtro, Semana.mensajes.is_(None))
            .update({Semana.mensajes: 0, Semana.costo_por_resultado: 0, Semana.importe_gastado: 0},
                    synchronize_session=False)
        )
        bloqueadas = (
            db.query(Semana)
            .filter(*vencidas_filtro)
            .update({Semana.editable: False}, synchronize_session=False)
        )

        campanas_activas = db.query(Campana).filter_by(estado="activa").all()
        creadas = 0
        for campana in campanas_activas:
            existe = db.query(Semana).filter_by(campana_id=campana.id, inicio=inicio_actual).one_or_none()
            if existe is None:
                db.add(Semana(campana_id=campana.id, inicio=inicio_actual, fin=fin_actual, editable=True))
                creadas += 1

        db.commit()
        logger.info("cierre_semana: %s semanas rellenadas en 0, %s bloqueadas, %s semanas nuevas creadas",
                     sin_capturar, bloqueadas, creadas)
    except Exception:
        db.rollback()
        logger.exception("cierre_semana falló")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cerrar_semana()
