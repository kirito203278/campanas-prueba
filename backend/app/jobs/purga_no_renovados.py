"""Job: DIARIO 12:10 — clientes en 'No renovados' que llevan un año o más
sin volver se eliminan por completo (mismo efecto que la rama 'borrar' de
POST /cm/clientes/{id}/no-renovar): se borra el cliente en cascada
(campañas, semanas, observaciones, mensuales) y, si su cuenta publicitaria
queda huérfana, también se borra.
"""
import datetime as dt
import logging

from app.database import SessionLocal
from app.models import ArchivoNoRenovado, Cliente, CuentaPublicitaria

logger = logging.getLogger("jobs.purga_no_renovados")

LIMITE_PURGA_DIAS = 365


def purgar_no_renovados() -> None:
    db = SessionLocal()
    try:
        hoy = dt.date.today()
        clientes = db.query(Cliente).filter_by(estado="no_renovado").all()

        purgados = 0
        for cliente in clientes:
            ultimo = (
                db.query(ArchivoNoRenovado)
                .filter_by(cliente_id=cliente.id)
                .order_by(ArchivoNoRenovado.archivado_en.desc())
                .first()
            )
            if ultimo is None or (hoy - ultimo.archivado_en.date()).days < LIMITE_PURGA_DIAS:
                continue

            cuenta_id = cliente.cuenta_id
            db.query(ArchivoNoRenovado).filter_by(cliente_id=cliente.id).delete(synchronize_session=False)
            db.delete(cliente)
            db.flush()
            if cuenta_id is not None:
                otros = db.query(Cliente).filter_by(cuenta_id=cuenta_id).count()
                if otros == 0:
                    db.query(CuentaPublicitaria).filter_by(id=cuenta_id).delete()
            purgados += 1

        db.commit()
        logger.info("purga_no_renovados: %s clientes eliminados", purgados)
    except Exception:
        db.rollback()
        logger.exception("purga_no_renovados falló")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    purgar_no_renovados()
