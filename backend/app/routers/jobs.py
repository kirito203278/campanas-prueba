"""Endpoint para disparar los jobs programados desde un cron externo (p. ej.
cron-job.org), para hosting gratuito donde el proceso "duerme" por
inactividad y no hay garantía de que esté vivo a la hora exacta del job.
La propia llamada despierta el proceso y ejecuta el job en el mismo golpe.

Protegido con un secreto compartido (header X-Jobs-Secret), no con JWT de
usuario: quien llama es un servicio externo, no una persona con sesión.
Los 4 jobs ya son seguros de correr más de una vez el mismo día (filtran
por estado/fecha), así que no hay riesgo de duplicar efectos por tener
APScheduler y este endpoint activos a la vez — este es un respaldo
adicional, no un reemplazo del scheduler interno.
"""
import hmac

from fastapi import APIRouter, Header, HTTPException, status

from app.config import get_settings
from app.jobs.cierre_ciclo import cerrar_ciclo
from app.jobs.cierre_semana import cerrar_semana
from app.jobs.purga_no_renovados import purgar_no_renovados
from app.jobs.recordatorio import recordatorio_captura

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

JOBS = {
    "cierre_semana": cerrar_semana,
    "recordatorio_captura": recordatorio_captura,
    "cierre_ciclo": cerrar_ciclo,
    "purga_no_renovados": purgar_no_renovados,
}


@router.post("/run/{nombre}")
def run_job(nombre: str, x_jobs_secret: str = Header(default="")):
    settings = get_settings()
    if not hmac.compare_digest(x_jobs_secret, settings.jobs_secret):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Secreto inválido")

    job = JOBS.get(nombre)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job no encontrado")

    job()
    return {"ok": True, "job": nombre}
