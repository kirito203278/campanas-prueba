"""Utilidades de fecha del ciclo semanal (especificación, sección 4):
la semana operativa va de sábado a viernes."""
import datetime as dt


def most_recent_saturday(d: dt.date) -> dt.date:
    offset = (d.weekday() - 5) % 7  # weekday(): Mon=0 ... Sat=5, Sun=6
    return d - dt.timedelta(days=offset)


def week_range_for(d: dt.date) -> tuple[dt.date, dt.date]:
    inicio = most_recent_saturday(d)
    return inicio, inicio + dt.timedelta(days=6)


def dentro_de_ventana_habilitacion(momento_local: dt.datetime) -> bool:
    """El admin solo puede habilitar edición de una semana pasada entre el
    sábado 8:00 y el viernes 15:00 siguiente (hora local). Fuera de esa
    ventana (viernes 15:00 a sábado 8:00) no, sin prórroga."""
    dia, hora = momento_local.weekday(), momento_local.time()  # weekday(): Mon=0 ... Fri=4, Sat=5
    if dia == 4 and hora >= dt.time(15, 0):
        return False
    if dia == 5 and hora < dt.time(8, 0):
        return False
    return True
