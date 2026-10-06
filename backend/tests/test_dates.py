"""Calendario de la semana operativa (sábado→viernes) y ventana de edición."""
import datetime as dt

from app.dates import dentro_de_ventana_habilitacion, most_recent_saturday, week_range_for


def test_sabado_mas_reciente():
    # miércoles 2026-10-07 -> sábado previo 2026-10-03
    assert most_recent_saturday(dt.date(2026, 10, 7)) == dt.date(2026, 10, 3)
    # un sábado se devuelve a sí mismo
    assert most_recent_saturday(dt.date(2026, 10, 3)) == dt.date(2026, 10, 3)


def test_rango_de_semana_sabado_a_viernes():
    inicio, fin = week_range_for(dt.date(2026, 10, 7))
    assert inicio == dt.date(2026, 10, 3)   # sábado
    assert fin == dt.date(2026, 10, 9)      # viernes
    assert inicio.weekday() == 5 and fin.weekday() == 4


def test_ventana_habilitacion_cerrada_viernes_tarde():
    # viernes 15:00 en adelante: fuera de ventana
    viernes_tarde = dt.datetime(2026, 10, 9, 15, 0)
    assert dentro_de_ventana_habilitacion(viernes_tarde) is False


def test_ventana_habilitacion_cerrada_sabado_madrugada():
    sabado_temprano = dt.datetime(2026, 10, 10, 7, 59)
    assert dentro_de_ventana_habilitacion(sabado_temprano) is False


def test_ventana_habilitacion_abierta_entre_semana():
    miercoles = dt.datetime(2026, 10, 7, 10, 0)
    assert dentro_de_ventana_habilitacion(miercoles) is True
