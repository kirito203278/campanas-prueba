"""Métricas de rendimiento (especificación, sección 7). PROVISIONALES: los
umbrales viven en la tabla metricas_config, no en código, para poder
sustituirlos por los reales sin tocar el backend.
"""
from sqlalchemy.orm import Session

from app.models import Campana, MetricaConfig, Semana

NIVELES = ("bueno", "regular", "bajo")


def obtener_umbrales(db: Session, tipo: str, paquete: str | None) -> MetricaConfig | None:
    if paquete:
        cfg = db.query(MetricaConfig).filter_by(tipo=tipo, paquete=paquete, activo=True).one_or_none()
        if cfg:
            return cfg
    return db.query(MetricaConfig).filter_by(tipo=tipo, paquete=None, activo=True).one_or_none()


def _nivel_por_costo(cfg: MetricaConfig, costo: float) -> str:
    if costo <= float(cfg.umbral_bueno):
        return "bueno"
    if costo <= float(cfg.umbral_regular):
        return "regular"
    return "bajo"


def _degradar(nivel: str) -> str:
    idx = min(NIVELES.index(nivel) + 1, len(NIVELES) - 1)
    return NIVELES[idx]


def calcular_rendimiento_semana(db: Session, campana: Campana, semana: Semana, semanas_previas: list[Semana]) -> str | None:
    """Semáforo semanal: costo por resultado contra la tabla, más alerta si
    los mensajes caen >= X% contra el promedio de semanas previas del ciclo
    (especificación, sección 7)."""
    if semana.costo_por_resultado is None:
        return None
    cfg = obtener_umbrales(db, campana.tipo, campana.paquete)
    if cfg is None:
        return None
    nivel = _nivel_por_costo(cfg, float(semana.costo_por_resultado))

    previas_con_datos = [s for s in semanas_previas if s.mensajes is not None]
    if previas_con_datos and semana.mensajes is not None:
        promedio = sum(s.mensajes for s in previas_con_datos) / len(previas_con_datos)
        if promedio > 0:
            caida_pct = (promedio - semana.mensajes) / promedio * 100
            if caida_pct >= float(cfg.caida_mensajes_alerta_pct):
                nivel = _degradar(nivel)
    return nivel


def calcular_rendimiento_ciclo(db: Session, campana: Campana, costo_por_mensaje: float, semanas_ordenadas: list[Semana]) -> str | None:
    """Mensual: costo por mensaje del ciclo contra la tabla, ponderado con la
    tendencia (si las últimas dos semanas empeoran, baja un grado)."""
    cfg = obtener_umbrales(db, campana.tipo, campana.paquete)
    if cfg is None:
        return None
    nivel = _nivel_por_costo(cfg, costo_por_mensaje)

    costos = [float(s.costo_por_resultado) for s in semanas_ordenadas if s.costo_por_resultado is not None]
    if len(costos) >= 3 and costos[-1] > costos[-2] > costos[-3]:
        nivel = _degradar(nivel)
    return nivel
