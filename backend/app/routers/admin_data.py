"""Panel de la administradora (especificación, sección 6): navegación de
solo lectura CMs -> clientes -> campañas, con semáforo, gráficas y la vista
consolidada "Todas". La migración de cartera al eliminar un CM vive aquí
también. Todo de solo lectura para cualquier admin (incluidos los de
solo_lectura); solo la baja/migración de CM exige escritura.
"""
import datetime as dt
import io
import re
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.bitacora import registrar
from app.config import get_settings
from app.consolidacion import mensuales_consolidados_de_cliente, semanas_consolidadas_de_cliente
from app.database import get_db
from app.dates import dentro_de_ventana_habilitacion
from app.deps import require_admin, require_admin_write
from app.metrics import calcular_rendimiento_semana
from app.models import Campana, Cliente, Mensual, Notificacion, Semana, Usuario
from app.reports.reporte_mensual_pdf import generar_pdf_reporte_mensual
from app.reports.reporte_semanal_pdf import generar_pdf_reporte_semanal
from app.schemas_admin import (
    CampanaDetalleAdmin,
    CampanaResumenAdmin,
    ClienteAdminDetalle,
    ClienteAdminItem,
    CMConCartera,
    MensualAdmin,
    MensualConsolidado,
    MigrarCMIn,
    MigrarCMOut,
    SemanaAdmin,
    SemanaConsolidada,
)
router = APIRouter(prefix="/api/admin", tags=["admin-data"])


def _get_campana_admin_or_404(db: Session, campana_id: int) -> Campana:
    campana = db.get(Campana, campana_id)
    if campana is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaña no encontrada")
    return campana


def _costo_actual_y_semaforo(db: Session, campana: Campana) -> tuple[float | None, str | None]:
    ultima = (
        db.query(Semana)
        .filter(Semana.campana_id == campana.id, Semana.costo_por_resultado.isnot(None))
        .order_by(Semana.inicio.desc())
        .first()
    )
    if ultima is None:
        return None, None
    previas = (
        db.query(Semana)
        .filter(Semana.campana_id == campana.id, Semana.inicio < ultima.inicio)
        .order_by(Semana.inicio)
        .all()
    )
    semaforo = calcular_rendimiento_semana(db, campana, ultima, previas)
    return float(ultima.costo_por_resultado), semaforo


# ------------------------------------------------------------------- CMs
@router.get("/cms/cartera", response_model=list[CMConCartera])
def listar_cms_con_cartera(admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    cms = db.query(Usuario).filter_by(rol="cm").order_by(Usuario.activo.desc(), Usuario.nombre).all()
    out = []
    for cm in cms:
        total = db.query(Cliente).filter_by(cm_id=cm.id, estado="activo").count()
        out.append(CMConCartera(id=cm.id, nombre=cm.nombre, username=cm.username, activo=cm.activo, total_clientes=total))
    return out


@router.get("/cms/{cm_id}/clientes", response_model=list[ClienteAdminItem])
def listar_clientes_de_cm(cm_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    clientes = db.query(Cliente).filter_by(cm_id=cm_id, estado="activo").order_by(Cliente.nombre).all()
    return [
        ClienteAdminItem(id=c.id, nombre=c.nombre, estado=c.estado, total_campanas=len(c.campanas))
        for c in clientes
    ]


@router.post("/cms/{cm_id}/baja", response_model=MigrarCMOut)
def dar_de_baja_cm(cm_id: int, payload: MigrarCMIn,
                    admin: Usuario = Depends(require_admin_write), db: Session = Depends(get_db)):
    origen = db.get(Usuario, cm_id)
    if origen is None or origen.rol != "cm":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CM de origen no encontrado")

    total_clientes = db.query(Cliente).filter_by(cm_id=cm_id).count()

    # Sin cartera no hay nada que migrar; exigir un CM destino en ese caso
    # bloqueaba la baja sin ninguna razón real.
    if total_clientes == 0:
        origen.activo = False
        registrar(db, usuario_id=admin.id, accion="baja_cm_sin_cartera",
                  detalle={"cm_origen_id": origen.id, "cm_origen_username": origen.username})
        db.commit()
        return MigrarCMOut(clientes_migrados=0, cm_origen=origen.nombre, cm_destino="—")

    if payload.migrar_a_cm_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                             "Este CM tiene clientes en su cartera; elige un CM destino para migrarla")
    if cm_id == payload.migrar_a_cm_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes migrar la cartera a la misma cuenta")

    destino = db.get(Usuario, payload.migrar_a_cm_id)
    if destino is None or destino.rol != "cm" or not destino.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CM de destino no encontrado o inactivo")

    # Migra toda la cartera: clientes, y por relación (FK) sus campañas,
    # semanas, observaciones y cuentas publicitarias los siguen automáticamente.
    migrados = db.query(Cliente).filter_by(cm_id=cm_id).update({Cliente.cm_id: destino.id}, synchronize_session=False)
    origen.activo = False

    registrar(db, usuario_id=admin.id, accion="migrar_cm", detalle={
        "cm_origen_id": origen.id, "cm_origen_username": origen.username,
        "cm_destino_id": destino.id, "cm_destino_username": destino.username,
        "clientes_migrados": migrados,
    })
    db.commit()

    return MigrarCMOut(clientes_migrados=migrados, cm_origen=origen.nombre, cm_destino=destino.nombre)


# -------------------------------------------------------------- clientes
@router.get("/clientes/{cliente_id}", response_model=ClienteAdminDetalle)
def detalle_cliente_admin(cliente_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

    campanas = []
    for camp in cliente.campanas:
        costo_actual, semaforo = _costo_actual_y_semaforo(db, camp)
        campanas.append(CampanaResumenAdmin(
            id=camp.id, nombre=camp.nombre, tipo=camp.tipo, estado=camp.estado,
            costo_actual=costo_actual, semaforo=semaforo,
        ))

    return ClienteAdminDetalle(
        id=cliente.id, nombre=cliente.nombre, estado=cliente.estado,
        cm_id=cliente.cm_id, cm_nombre=cliente.cm.nombre, campanas=campanas,
    )


# --------------------------------------------------------------- campañas
@router.get("/campanas/{campana_id}", response_model=CampanaDetalleAdmin)
def detalle_campana_admin(campana_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    campana = _get_campana_admin_or_404(db, campana_id)
    return CampanaDetalleAdmin(
        id=campana.id, cliente_id=campana.cliente_id, nombre=campana.nombre, paquete=campana.paquete,
        tipo=campana.tipo, presupuesto=float(campana.presupuesto), presupuesto_esquema=campana.presupuesto_esquema,
        formato_post=campana.formato_post, formato_3d=campana.formato_3d, formato_boton=campana.formato_boton,
        formato_otro=campana.formato_otro, lugar=campana.lugar, fecha_inicio=campana.fecha_inicio,
        fecha_renovacion=campana.fecha_renovacion, estado=campana.estado,
    )


@router.get("/campanas/{campana_id}/semanas", response_model=list[SemanaAdmin])
def semanas_campana_admin(campana_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    _get_campana_admin_or_404(db, campana_id)
    return db.query(Semana).filter_by(campana_id=campana_id).order_by(Semana.inicio).all()


@router.post("/semanas/{semana_id}/habilitar-edicion", response_model=SemanaAdmin)
def habilitar_edicion_semana(semana_id: int, admin: Usuario = Depends(require_admin_write), db: Session = Depends(get_db)):
    """Le da al CM 2 horas para editar una semana ya cerrada. Solo se puede
    otorgar entre el sábado 8:00 y el viernes 15:00 siguiente (hora local),
    sin prórroga; el cierre normal semanal (sábado 00:00) no cambia."""
    semana = db.get(Semana, semana_id)
    if semana is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Semana no encontrada")
    if semana.editable:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta semana ya está abierta, no necesita permiso especial")

    ahora_utc = dt.datetime.now(dt.timezone.utc)
    ahora_local = ahora_utc.astimezone(ZoneInfo(get_settings().tz))
    if not dentro_de_ventana_habilitacion(ahora_local):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                             "Fuera de la ventana permitida para habilitar ediciones (sábados 8:00 a viernes 15:00)")

    semana.edicion_habilitada_hasta = ahora_utc + dt.timedelta(hours=2)
    db.add(Notificacion(
        usuario_id=semana.campana.cliente.cm_id, tipo="sistema",
        mensaje=f"Un administrador habilitó la edición de la semana del {semana.inicio.strftime('%d/%m/%Y')} "
                f"al {semana.fin.strftime('%d/%m/%Y')} por 2 horas.",
    ))
    registrar(db, usuario_id=admin.id, accion="habilitar_edicion_semana",
              detalle={"semana_id": semana.id, "campana_id": semana.campana_id})
    db.commit()
    db.refresh(semana)
    return semana


@router.get("/campanas/{campana_id}/mensuales", response_model=list[MensualAdmin])
def mensuales_campana_admin(campana_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    _get_campana_admin_or_404(db, campana_id)
    return (
        db.query(Mensual)
        .filter_by(campana_id=campana_id)
        .order_by(Mensual.periodo_inicio.desc())
        .limit(3)  # regla dura 6: comparación de hasta 3 meses en panel admin
        .all()
    )


# ------------------------------------------------------- vista consolidada
@router.get("/clientes/{cliente_id}/semanas-consolidadas", response_model=list[SemanaConsolidada])
def semanas_consolidadas(cliente_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    """Especificación, sección 9-b: opción "Todas" que suma las campañas del
    cliente en el ciclo en curso (útil si se cerró una y se abrió otra)."""
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

    semanas = semanas_consolidadas_de_cliente(db, cliente)
    return [SemanaConsolidada(**vars(s)) for s in semanas]


@router.get("/clientes/{cliente_id}/mensuales-consolidados", response_model=list[MensualConsolidado])
def mensuales_consolidados(cliente_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

    meses = mensuales_consolidados_de_cliente(db, cliente, limite=3)
    return [MensualConsolidado(**vars(m)) for m in meses]


# --------------------------------------------------------- reporte mensual
@router.get("/clientes/{cliente_id}/reporte-mensual")
def reporte_mensual_pdf(cliente_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    """Especificación, sección 6: reporte mensual formal en PDF, consolidado
    por cliente (sección 9-b), para entregar al cliente final."""
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

    meses = mensuales_consolidados_de_cliente(db, cliente, limite=3)
    if not meses:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                             "Este cliente todavía no tiene ningún mes cerrado para reportar")

    campanas_nombres = [c.nombre for c in cliente.campanas]
    buffer = io.BytesIO()
    generar_pdf_reporte_mensual(cliente.nombre, campanas_nombres, meses, buffer)
    buffer.seek(0)

    slug = re.sub(r"[^a-z0-9]+", "-", cliente.nombre.lower()).strip("-")
    periodo = meses[0].periodo_inicio.strftime("%Y-%m")
    filename = f"reporte-{slug}-{periodo}.pdf"

    registrar(db, usuario_id=admin.id, accion="generar_reporte_mensual",
              detalle={"cliente_id": cliente.id, "cliente_nombre": cliente.nombre, "periodo": periodo})
    db.commit()

    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/clientes/{cliente_id}/reporte-semanal")
def reporte_semanal_pdf(cliente_id: int, admin: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    """Reporte semanal en PDF, en lenguaje para el cliente final, consolidado
    por cliente (sección 9-b)."""
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

    semanas = semanas_consolidadas_de_cliente(db, cliente)
    semanas_con_datos = [s for s in semanas if s.mensajes > 0 or s.importe_gastado > 0]
    if not semanas_con_datos:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                             "Este cliente todavía no tiene ninguna semana capturada para reportar")

    campanas_nombres = [c.nombre for c in cliente.campanas]
    buffer = io.BytesIO()
    generar_pdf_reporte_semanal(cliente.nombre, campanas_nombres, semanas_con_datos, buffer)
    buffer.seek(0)

    slug = re.sub(r"[^a-z0-9]+", "-", cliente.nombre.lower()).strip("-")
    periodo = semanas_con_datos[-1].inicio.strftime("%Y-%m-%d")
    filename = f"reporte-semanal-{slug}-{periodo}.pdf"

    registrar(db, usuario_id=admin.id, accion="generar_reporte_semanal",
              detalle={"cliente_id": cliente.id, "cliente_nombre": cliente.nombre, "periodo": periodo})
    db.commit()

    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
