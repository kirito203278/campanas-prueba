"""Cierre de ciclo: archiva el mensual (inmutable), borra semanas/observaciones
de ESA campaña y la deja 'vencida' con aviso al CM."""
import datetime as dt

import pytest

from app.jobs.cierre_ciclo import cerrar_ciclo_campana
from app.models import Mensual, Notificacion, Observacion, Semana


def test_cerrar_ciclo_calcula_y_archiva_el_mensual(db, crear_usuario, fabrica):
    cm = crear_usuario("Kori", "kori")
    cliente = fabrica.cliente(cm, nombre="BTW Amigos")
    camp = fabrica.campana(cliente, tipo="local", presupuesto=3500)
    fabrica.semana(camp, dt.date(2026, 1, 3), mensajes=100, costo=10, importe=1000)
    fabrica.semana(camp, dt.date(2026, 1, 10), mensajes=200, costo=10, importe=2000)
    db.add(Observacion(campana_id=camp.id, texto="nota", autor_id=cm.id))
    db.flush()

    mensual = cerrar_ciclo_campana(db, camp)
    db.flush()

    assert mensual.mensajes_total == 300
    assert float(mensual.gasto_total) == 3000.0
    assert float(mensual.costo_por_mensaje) == 10.0
    assert float(mensual.sobrante) == 500.0          # 3500 - 3000
    assert mensual.origen == "calculado"
    # la campaña queda vencida y bloqueada
    assert camp.estado == "vencida"
    # se borran semanas y observaciones de esa campaña
    assert db.query(Semana).filter_by(campana_id=camp.id).count() == 0
    assert db.query(Observacion).filter_by(campana_id=camp.id).count() == 0
    # se avisa al CM
    aviso = db.query(Notificacion).filter_by(usuario_id=cm.id, tipo="vencimiento").first()
    assert aviso is not None


def test_mensual_es_inmutable_no_se_puede_editar(db, crear_usuario, fabrica):
    cm = crear_usuario("Kori", "kori")
    camp = fabrica.campana(fabrica.cliente(cm))
    fabrica.semana(camp, dt.date(2026, 1, 3), mensajes=100, costo=10, importe=1000)
    mensual = cerrar_ciclo_campana(db, camp)
    db.flush()

    # el trigger de la base rechaza cualquier UPDATE sobre mensuales
    mensual.gasto_total = 1
    with pytest.raises(Exception):
        db.flush()
