"""Semáforo de rendimiento contra los umbrales definitivos (migración 005):
Local bueno 0-19 / regular 20-29 / bajo >=30; con penalización por caída de
mensajes."""
import datetime as dt

from app.metrics import calcular_rendimiento_ciclo, calcular_rendimiento_semana


def _semana(inicio, mensajes, costo):
    from app.models import Semana
    return Semana(inicio=inicio, fin=inicio + dt.timedelta(days=6), mensajes=mensajes, costo_por_resultado=costo)


def test_niveles_local_por_umbral(db, crear_usuario, fabrica):
    cm = crear_usuario("Kori", "kori")
    camp = fabrica.campana(fabrica.cliente(cm), tipo="local")
    s_bueno = _semana(dt.date(2026, 1, 3), 100, 10)
    s_regular = _semana(dt.date(2026, 1, 3), 100, 25)
    s_bajo = _semana(dt.date(2026, 1, 3), 100, 35)
    assert calcular_rendimiento_semana(db, camp, s_bueno, []) == "bueno"
    assert calcular_rendimiento_semana(db, camp, s_regular, []) == "regular"
    assert calcular_rendimiento_semana(db, camp, s_bajo, []) == "bajo"


def test_nacional_tiene_umbral_mas_estricto(db, crear_usuario, fabrica):
    cm = crear_usuario("Kori", "kori")
    camp = fabrica.campana(fabrica.cliente(cm), tipo="nacional")
    # costo 17: para local sería 'regular', para nacional (bueno 0-14) es 'bajo'/'regular'
    s = _semana(dt.date(2026, 1, 3), 100, 17)
    assert calcular_rendimiento_semana(db, camp, s, []) == "regular"  # nacional regular 15-19


def test_penalizacion_por_caida_de_mensajes(db, crear_usuario, fabrica):
    cm = crear_usuario("Kori", "kori")
    camp = fabrica.campana(fabrica.cliente(cm), tipo="local")
    previas = [_semana(dt.date(2026, 1, 3), 100, 10), _semana(dt.date(2026, 1, 10), 100, 10)]
    # costo 10 => 'bueno', pero los mensajes caen de 100 a 50 (-50%) => degrada a 'regular'
    actual = _semana(dt.date(2026, 1, 17), 50, 10)
    assert calcular_rendimiento_semana(db, camp, actual, previas) == "regular"


def test_rendimiento_ciclo_degrada_si_tres_semanas_empeoran(db, crear_usuario, fabrica):
    cm = crear_usuario("Kori", "kori")
    camp = fabrica.campana(fabrica.cliente(cm), tipo="local")
    semanas = [_semana(dt.date(2026, 1, 3), 100, 10), _semana(dt.date(2026, 1, 10), 100, 12),
               _semana(dt.date(2026, 1, 17), 100, 15)]
    # costo por mensaje del ciclo 10 => 'bueno', pero 3 semanas monotónicamente peores => 'regular'
    assert calcular_rendimiento_ciclo(db, camp, 10.0, semanas) == "regular"
