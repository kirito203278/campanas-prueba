"""Consolidación de mensuales de un cliente a través de todas sus campañas
(especificación, sección 9-b): "el reporte formal del cliente consolida por
default todas sus campañas del ciclo, que es como el cliente lo entiende".
Compartido entre el panel admin (vista "Todas") y el reporte mensual en PDF.
"""
import datetime as dt
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.metrics import calcular_rendimiento_ciclo
from app.models import Cliente, Mensual, Semana


@dataclass
class MesConsolidado:
    periodo_inicio: dt.date
    periodo_fin: dt.date
    mensajes_total: int
    gasto_total: float
    costo_por_mensaje: float
    presupuesto: float
    sobrante: float
    rendimiento: str | None


@dataclass
class SemanaConsolidadaData:
    inicio: dt.date
    fin: dt.date
    mensajes: int
    costo_por_resultado: float | None
    importe_gastado: float


def mensuales_consolidados_de_cliente(db: Session, cliente: Cliente, limite: int = 3) -> list[MesConsolidado]:
    campana_ids = [c.id for c in cliente.campanas]
    if not campana_ids:
        return []

    mensuales = db.query(Mensual).filter(Mensual.campana_id.in_(campana_ids)).order_by(Mensual.periodo_inicio.desc()).all()
    campana_por_id = {c.id: c for c in cliente.campanas}

    por_periodo: dict[dt.date, dict] = defaultdict(lambda: {"fin": None, "mensajes": 0, "gasto": 0.0, "presupuesto": 0.0, "campana_ref": None})
    for m in mensuales:
        acc = por_periodo[m.periodo_inicio]
        acc["fin"] = m.periodo_fin
        acc["mensajes"] += m.mensajes_total
        acc["gasto"] += float(m.gasto_total)
        acc["presupuesto"] += float(m.presupuesto)
        acc["campana_ref"] = acc["campana_ref"] or campana_por_id.get(m.campana_id)

    resultado = []
    for periodo in sorted(por_periodo, reverse=True)[:limite]:
        acc = por_periodo[periodo]
        costo_por_mensaje = (acc["gasto"] / acc["mensajes"]) if acc["mensajes"] else 0.0
        sobrante = acc["presupuesto"] - acc["gasto"]
        rendimiento = None
        if acc["campana_ref"] is not None:
            rendimiento = calcular_rendimiento_ciclo(db, acc["campana_ref"], costo_por_mensaje, [])
        resultado.append(MesConsolidado(
            periodo_inicio=periodo, periodo_fin=acc["fin"], mensajes_total=acc["mensajes"],
            gasto_total=round(acc["gasto"], 2), costo_por_mensaje=round(costo_por_mensaje, 2),
            presupuesto=round(acc["presupuesto"], 2), sobrante=round(sobrante, 2), rendimiento=rendimiento,
        ))
    return resultado


def semanas_consolidadas_de_cliente(db: Session, cliente: Cliente) -> list[SemanaConsolidadaData]:
    """Suma, por fecha de inicio, las semanas del ciclo en curso de todas las
    campañas ACTIVAS del cliente (sección 9-b: útil si se cerró una campaña
    y se abrió otra dentro del mismo ciclo, que para el cliente fue una sola)."""
    campana_ids = [c.id for c in cliente.campanas if c.estado == "activa"]
    if not campana_ids:
        return []

    semanas = db.query(Semana).filter(Semana.campana_id.in_(campana_ids)).order_by(Semana.inicio).all()
    por_semana: dict[dt.date, dict] = defaultdict(lambda: {"fin": None, "mensajes": 0, "importe": 0.0})
    for s in semanas:
        acc = por_semana[s.inicio]
        acc["fin"] = s.fin
        acc["mensajes"] += s.mensajes or 0
        acc["importe"] += float(s.importe_gastado or 0)

    resultado = []
    for inicio in sorted(por_semana):
        acc = por_semana[inicio]
        costo = (acc["importe"] / acc["mensajes"]) if acc["mensajes"] else None
        resultado.append(SemanaConsolidadaData(
            inicio=inicio, fin=acc["fin"], mensajes=acc["mensajes"],
            costo_por_resultado=round(costo, 2) if costo is not None else None,
            importe_gastado=round(acc["importe"], 2),
        ))
    return resultado
