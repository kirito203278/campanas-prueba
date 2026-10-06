"""Registro de los jobs programados (especificación, secciones 4, 5 y 8):
  * Sábado 00:00   -> cierre de semana
  * Viernes 14:00  -> recordatorio de captura
  * Diario 12:00   -> cierre de ciclo por fecha de renovación
  * Diario 12:10   -> purga de clientes con 1 año o más en "No renovados"
"""
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.jobs.cierre_ciclo import cerrar_ciclo
from app.jobs.cierre_semana import cerrar_semana
from app.jobs.purga_no_renovados import purgar_no_renovados
from app.jobs.recordatorio import recordatorio_captura

logger = logging.getLogger("jobs.scheduler")

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.tz))

    scheduler.add_job(cerrar_semana, CronTrigger(day_of_week="sat", hour=0, minute=0),
                       id="cierre_semana", replace_existing=True)
    scheduler.add_job(recordatorio_captura, CronTrigger(day_of_week="fri", hour=14, minute=0),
                       id="recordatorio_captura", replace_existing=True)
    scheduler.add_job(cerrar_ciclo, CronTrigger(hour=12, minute=0),
                       id="cierre_ciclo", replace_existing=True)
    scheduler.add_job(purgar_no_renovados, CronTrigger(hour=12, minute=10),
                       id="purga_no_renovados", replace_existing=True)

    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler iniciado (tz=%s)", settings.tz)
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
