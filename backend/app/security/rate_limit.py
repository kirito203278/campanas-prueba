"""Límite de intentos fallidos de login, en memoria del proceso — igual que
el scheduler (backend/app/jobs/scheduler.py), asume un solo proceso de
uvicorn, que es como corre este sistema. Protege contra fuerza bruta sin
depender de nada externo (Redis, etc.)."""
import datetime as dt
import threading

LIMITE_INTENTOS = 5
VENTANA = dt.timedelta(minutes=15)

_intentos: dict[str, list[dt.datetime]] = {}
_lock = threading.Lock()


def _vigentes(historial: list[dt.datetime], ahora: dt.datetime) -> list[dt.datetime]:
    return [t for t in historial if ahora - t < VENTANA]


def registrar_intento_fallido(username: str) -> None:
    ahora = dt.datetime.now(dt.timezone.utc)
    with _lock:
        historial = _vigentes(_intentos.get(username, []), ahora)
        historial.append(ahora)
        _intentos[username] = historial


def limpiar_intentos(username: str) -> None:
    with _lock:
        _intentos.pop(username, None)


def bloqueado(username: str) -> bool:
    ahora = dt.datetime.now(dt.timezone.utc)
    with _lock:
        vigentes = _vigentes(_intentos.get(username, []), ahora)
        _intentos[username] = vigentes
        return len(vigentes) >= LIMITE_INTENTOS
