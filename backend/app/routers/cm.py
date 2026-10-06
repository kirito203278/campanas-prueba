"""Panel del CM (especificación, sección 3). Regla dura 1: toda consulta
filtra por cm_id = usuario autenticado; nunca se confía en un id que venga
del cliente para decidir alcance."""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import io
import re

from app.bitacora import registrar
from app.consolidacion import mensuales_consolidados_de_cliente, semanas_consolidadas_de_cliente
from app.database import get_db
from app.dates import week_range_for
from app.deps import require_cm
from app.metrics import calcular_rendimiento_ciclo
from app.models import ArchivoNoRenovado, Campana, Cliente, CuentaPublicitaria, Mensual, Observacion, Semana, Usuario
from app.reports.reporte_mensual_pdf import generar_pdf_reporte_mensual
from app.reports.reporte_semanal_pdf import generar_pdf_reporte_semanal
from app.schemas_cm import (
    CampanaDetalle,
    CampanaResumen,
    ClienteCreadoOut,
    ClienteDetalle,
    ClienteListItem,
    ClienteLoteCampanaIn,
    ClienteLoteRequest,
    ClienteLoteResultado,
    CuentaIn,
    CuentaOut,
    EliminarClienteIn,
    EstadoCMOut,
    FilaConfirmacionOut,
    FilaErrorOut,
    MensualManualIn,
    MensualOut,
    NoRenovadoItem,
    NoRenovarClienteIn,
    ObservacionIn,
    ObservacionOut,
    RenombrarClienteIn,
    RenovarCampanaIn,
    SemanaOut,
    SemanaUpdateIn,
)
from app.security.crypto import compute_huella, decrypt_value, encrypt_value

router = APIRouter(prefix="/api/cm", tags=["cm"])


# ------------------------------------------------------------------ helpers
def _get_cliente_or_404(db: Session, cm_id: int, cliente_id: int) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None or cliente.cm_id != cm_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    return cliente


def _get_campana_or_404(db: Session, cm_id: int, campana_id: int) -> Campana:
    campana = db.get(Campana, campana_id)
    if campana is None or campana.cliente.cm_id != cm_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaña no encontrada")
    return campana


LIMITE_CONTINUAR_DIAS = 60  # bajo este plazo desde que se archivó, se puede "continuar" con la última campaña


def _ultimo_archivo_no_renovado(db: Session, cliente_id: int) -> ArchivoNoRenovado | None:
    return (
        db.query(ArchivoNoRenovado)
        .filter_by(cliente_id=cliente_id)
        .order_by(ArchivoNoRenovado.archivado_en.desc())
        .first()
    )


def _puede_continuar(db: Session, cliente_id: int) -> bool:
    ultimo = _ultimo_archivo_no_renovado(db, cliente_id)
    if ultimo is None:
        return False
    return (dt.date.today() - ultimo.archivado_en.date()).days < LIMITE_CONTINUAR_DIAS


def _ensure_semana_actual(db: Session, campana: Campana) -> None:
    inicio, fin = week_range_for(dt.date.today())
    existe = db.query(Semana).filter_by(campana_id=campana.id, inicio=inicio).one_or_none()
    if existe is None:
        db.add(Semana(campana_id=campana.id, inicio=inicio, fin=fin, editable=True))


# -------------------------------------------------------------------- estado
@router.get("/estado", response_model=EstadoCMOut)
def estado(cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    total = db.query(Cliente).filter_by(cm_id=cm.id).count()
    return EstadoCMOut(primer_ingreso=cm.primer_ingreso, total_clientes=total)


@router.post("/comenzar", response_model=EstadoCMOut)
def comenzar(cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cm.primer_ingreso = False
    db.commit()
    total = db.query(Cliente).filter_by(cm_id=cm.id).count()
    return EstadoCMOut(primer_ingreso=False, total_clientes=total)


# ------------------------------------------------------------------ clientes
@router.get("/clientes", response_model=list[ClienteListItem])
def listar_clientes(cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    clientes = db.query(Cliente).filter_by(cm_id=cm.id, estado="activo").order_by(Cliente.nombre).all()
    out = []
    for c in clientes:
        activas = sum(1 for camp in c.campanas if camp.estado == "activa")
        vencidas = sum(1 for camp in c.campanas if camp.estado == "vencida")
        out.append(ClienteListItem(id=c.id, nombre=c.nombre, estado=c.estado,
                                    campanas_activas=activas, campanas_vencidas=vencidas))
    return out


@router.get("/clientes/{cliente_id}", response_model=ClienteDetalle)
def detalle_cliente(cliente_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    campanas = [CampanaResumen(id=c.id, nombre=c.nombre, tipo=c.tipo, estado=c.estado) for c in cliente.campanas]
    return ClienteDetalle(id=cliente.id, nombre=cliente.nombre, estado=cliente.estado, campanas=campanas)


@router.patch("/clientes/{cliente_id}", response_model=ClienteDetalle)
def renombrar_cliente(cliente_id: int, payload: RenombrarClienteIn,
                       cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    cliente.nombre = payload.nombre.strip()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya tienes otro cliente con ese nombre")
    db.refresh(cliente)
    campanas = [CampanaResumen(id=c.id, nombre=c.nombre, tipo=c.tipo, estado=c.estado) for c in cliente.campanas]
    return ClienteDetalle(id=cliente.id, nombre=cliente.nombre, estado=cliente.estado, campanas=campanas)


@router.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, payload: EliminarClienteIn,
                      cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    if payload.confirmacion_nombre.strip() != cliente.nombre:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                             "El nombre escrito no coincide con el del cliente; no se eliminó nada")

    nombre = cliente.nombre
    cuenta_id = cliente.cuenta_id
    db.delete(cliente)
    db.flush()

    if cuenta_id is not None:
        otros = db.query(Cliente).filter_by(cuenta_id=cuenta_id).count()
        if otros == 0:
            db.query(CuentaPublicitaria).filter_by(id=cuenta_id).delete()

    registrar(db, usuario_id=cm.id, accion="borrar_cliente",
              detalle={"cliente_id": cliente_id, "nombre": nombre})
    db.commit()
    return {"eliminado": True}


# ---------------------------------------------------------- alta múltiple
@router.post("/clientes/lote", response_model=ClienteLoteResultado, status_code=status.HTTP_201_CREATED)
def alta_multiple_clientes(payload: ClienteLoteRequest,
                            cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    nombres_existentes = {n for (n,) in db.query(Cliente.nombre).filter_by(cm_id=cm.id).all()}

    # --- 1) Validación de campos obligatorios y nombres duplicados --------
    errores: list[FilaErrorOut] = []
    nombres_en_lote: set[str] = set()
    for idx, fila in enumerate(payload.clientes):
        fila_errores: list[str] = []
        nombre = fila.nombre.strip()
        if not nombre:
            fila_errores.append("El nombre del cliente es obligatorio")
        elif nombre in nombres_existentes:
            fila_errores.append(f"Ya tienes un cliente llamado '{nombre}'")
        elif nombre in nombres_en_lote:
            fila_errores.append(f"'{nombre}' está repetido dentro de este mismo lote")
        else:
            nombres_en_lote.add(nombre)

        if fila_errores:
            errores.append(FilaErrorOut(index=idx, nombre=fila.nombre, errores=fila_errores))

    if errores:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail={"errores": [e.model_dump() for e in errores]})

    # --- 2) Detección de cuentas publicitarias ya existentes (sección 9-a) -
    confirmaciones: list[FilaConfirmacionOut] = []
    for idx, fila in enumerate(payload.clientes):
        huella = compute_huella(fila.cuenta.usuario, fila.cuenta.password)
        cuenta = db.query(CuentaPublicitaria).filter_by(huella=huella).one_or_none()
        if cuenta and not fila.confirmar_vinculo:
            cliente_existente = db.query(Cliente).filter_by(cuenta_id=cuenta.id).first()
            confirmaciones.append(FilaConfirmacionOut(
                index=idx, nombre=fila.nombre,
                cliente_existente=cliente_existente.nombre if cliente_existente else "otro cliente",
            ))

    if confirmaciones:
        raise HTTPException(status.HTTP_409_CONFLICT,
                             detail={"confirmaciones_requeridas": [c.model_dump() for c in confirmaciones]})

    # --- 3) Todo válido: crear en una sola transacción ---------------------
    creados: list[ClienteCreadoOut] = []
    try:
        for fila in payload.clientes:
            huella = compute_huella(fila.cuenta.usuario, fila.cuenta.password)
            cuenta = db.query(CuentaPublicitaria).filter_by(huella=huella).one_or_none()
            if cuenta is None:
                cuenta = CuentaPublicitaria(
                    usuario_enc=encrypt_value(fila.cuenta.usuario),
                    password_enc=encrypt_value(fila.cuenta.password),
                    huella=huella,
                )
                db.add(cuenta)
                db.flush()

            cliente = Cliente(cm_id=cm.id, cuenta_id=cuenta.id, nombre=fila.nombre.strip(), estado="activo",
                               tipo_cuenta=fila.tipo_cuenta, metodo_pago=fila.metodo_pago, forma_pago=fila.forma_pago)
            db.add(cliente)
            db.flush()

            campana = Campana(
                cliente_id=cliente.id,
                nombre=fila.campana.nombre,
                paquete=fila.campana.paquete,
                tipo=fila.campana.tipo,
                presupuesto=fila.campana.presupuesto,
                presupuesto_esquema=fila.campana.presupuesto_esquema,
                formato_post=fila.campana.formato_post,
                formato_3d=fila.campana.formato_3d,
                formato_boton=fila.campana.formato_boton,
                formato_otro=fila.campana.formato_otro,
                lugar=fila.campana.lugar,
                fecha_inicio=fila.campana.fecha_inicio,
                fecha_renovacion=fila.campana.fecha_renovacion,
                estado="activa",
            )
            db.add(campana)
            db.flush()

            _ensure_semana_actual(db, campana)

            creados.append(ClienteCreadoOut(cliente_id=cliente.id, nombre=cliente.nombre, campana_id=campana.id))

        registrar(db, usuario_id=cm.id, accion="alta_clientes_lote",
                  detalle={"clientes": [c.nombre for c in creados]})
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ClienteLoteResultado(creados=creados)


# ----------------------------------------------------------- datos de cuenta
@router.get("/clientes/{cliente_id}/cuenta", response_model=CuentaOut)
def obtener_cuenta(cliente_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    if cliente.cuenta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este cliente no tiene una cuenta vinculada")
    return CuentaOut(usuario=decrypt_value(cliente.cuenta.usuario_enc),
                      password=decrypt_value(cliente.cuenta.password_enc),
                      tipo_cuenta=cliente.tipo_cuenta, metodo_pago=cliente.metodo_pago, forma_pago=cliente.forma_pago)


@router.put("/clientes/{cliente_id}/cuenta", response_model=CuentaOut)
def actualizar_cuenta(cliente_id: int, payload: CuentaIn,
                       cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    nueva_huella = compute_huella(payload.usuario, payload.password)
    cuenta_actual = cliente.cuenta

    cliente.tipo_cuenta = payload.tipo_cuenta
    cliente.metodo_pago = payload.metodo_pago
    cliente.forma_pago = payload.forma_pago

    if cuenta_actual is not None and cuenta_actual.huella == nueva_huella:
        db.commit()
        return CuentaOut(usuario=payload.usuario, password=payload.password,
                          tipo_cuenta=cliente.tipo_cuenta, metodo_pago=cliente.metodo_pago, forma_pago=cliente.forma_pago)

    cuenta_destino = db.query(CuentaPublicitaria).filter_by(huella=nueva_huella).one_or_none()
    if cuenta_destino is not None:
        cliente.cuenta_id = cuenta_destino.id
    else:
        compartida = cuenta_actual is not None and (
            db.query(Cliente).filter(Cliente.cuenta_id == cuenta_actual.id, Cliente.id != cliente.id).count() > 0
        )
        if cuenta_actual is not None and not compartida:
            cuenta_actual.usuario_enc = encrypt_value(payload.usuario)
            cuenta_actual.password_enc = encrypt_value(payload.password)
            cuenta_actual.huella = nueva_huella
        else:
            nueva_cuenta = CuentaPublicitaria(
                usuario_enc=encrypt_value(payload.usuario),
                password_enc=encrypt_value(payload.password),
                huella=nueva_huella,
            )
            db.add(nueva_cuenta)
            db.flush()
            cliente.cuenta_id = nueva_cuenta.id

    cuenta_anterior_id = cuenta_actual.id if cuenta_actual else None
    db.commit()

    if cuenta_anterior_id is not None:
        huerfana = db.query(Cliente).filter_by(cuenta_id=cuenta_anterior_id).count() == 0
        if huerfana:
            db.query(CuentaPublicitaria).filter_by(id=cuenta_anterior_id).delete()
            db.commit()

    return CuentaOut(usuario=payload.usuario, password=payload.password,
                      tipo_cuenta=cliente.tipo_cuenta, metodo_pago=cliente.metodo_pago, forma_pago=cliente.forma_pago)


# --------------------------------------------------------------- campañas
@router.get("/clientes/{cliente_id}/campanas", response_model=list[CampanaResumen])
def listar_campanas(cliente_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    return [CampanaResumen(id=c.id, nombre=c.nombre, tipo=c.tipo, estado=c.estado) for c in cliente.campanas]


@router.get("/campanas/{campana_id}", response_model=CampanaDetalle)
def detalle_campana(campana_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    campana = _get_campana_or_404(db, cm.id, campana_id)
    return CampanaDetalle(
        id=campana.id, cliente_id=campana.cliente_id, nombre=campana.nombre, paquete=campana.paquete,
        tipo=campana.tipo, presupuesto=float(campana.presupuesto), presupuesto_esquema=campana.presupuesto_esquema,
        formato_post=campana.formato_post, formato_3d=campana.formato_3d, formato_boton=campana.formato_boton,
        formato_otro=campana.formato_otro, lugar=campana.lugar, fecha_inicio=campana.fecha_inicio,
        fecha_renovacion=campana.fecha_renovacion, estado=campana.estado,
    )


# ---------------------------------------------------------------- semanas
@router.get("/campanas/{campana_id}/semanas", response_model=list[SemanaOut])
def listar_semanas(campana_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    campana = _get_campana_or_404(db, cm.id, campana_id)
    semanas = db.query(Semana).filter_by(campana_id=campana.id).order_by(Semana.inicio).all()
    return semanas


@router.put("/semanas/{semana_id}", response_model=SemanaOut)
def actualizar_semana(semana_id: int, payload: SemanaUpdateIn,
                       cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    semana = db.get(Semana, semana_id)
    if semana is None or semana.campana.cliente.cm_id != cm.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Semana no encontrada")
    ahora = dt.datetime.now(dt.timezone.utc)
    tiene_permiso_temporal = semana.edicion_habilitada_hasta is not None and ahora < semana.edicion_habilitada_hasta
    if not semana.editable and not tiene_permiso_temporal:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta semana ya cerró y quedó bloqueada")

    semana.mensajes = payload.mensajes
    semana.costo_por_resultado = payload.costo_por_resultado
    semana.importe_gastado = payload.importe_gastado
    semana.capturado_por = cm.id
    semana.actualizado_en = dt.datetime.now(dt.timezone.utc)
    db.commit()
    db.refresh(semana)
    return semana


# ------------------------------------------------------------ observaciones
@router.get("/campanas/{campana_id}/observaciones", response_model=list[ObservacionOut])
def listar_observaciones(campana_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    campana = _get_campana_or_404(db, cm.id, campana_id)
    return db.query(Observacion).filter_by(campana_id=campana.id).order_by(Observacion.creado_en.desc()).all()


@router.post("/campanas/{campana_id}/observaciones", response_model=ObservacionOut, status_code=status.HTTP_201_CREATED)
def crear_observacion(campana_id: int, payload: ObservacionIn,
                       cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    campana = _get_campana_or_404(db, cm.id, campana_id)
    if campana.estado != "activa":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta campaña está vencida; resuelve la renovación primero")
    obs = Observacion(campana_id=campana.id, texto=payload.texto.strip(), autor_id=cm.id)
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


# ----------------------------------------------------------------- mensuales
@router.get("/campanas/{campana_id}/mensuales", response_model=list[MensualOut])
def listar_mensuales(campana_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    campana = _get_campana_or_404(db, cm.id, campana_id)
    return (
        db.query(Mensual)
        .filter_by(campana_id=campana.id)
        .order_by(Mensual.periodo_inicio.desc())
        .limit(2)  # regla dura 6: comparación de hasta 2 meses en panel CM
        .all()
    )


@router.post("/campanas/{campana_id}/mensuales/manual", response_model=MensualOut, status_code=status.HTTP_201_CREATED)
def capturar_mensual_manual(campana_id: int, payload: MensualManualIn,
                             cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    """Especificación, sección 5: el mensual del mes anterior a que la
    campaña entrara al sistema se captura a mano, una sola vez, solo si la
    campaña no tiene ningún mensual todavía. El trigger de la base también
    lo exige; aquí se valida antes para dar un mensaje claro."""
    campana = _get_campana_or_404(db, cm.id, campana_id)
    existe = db.query(Mensual).filter_by(campana_id=campana.id).first()
    if existe is not None:
        raise HTTPException(status.HTTP_409_CONFLICT,
                             "Esta campaña ya tiene un mensual registrado; la captura manual solo aplica una vez")

    costo_por_mensaje = (payload.gasto_total / payload.mensajes_total) if payload.mensajes_total else 0.0
    sobrante = float(campana.presupuesto) - payload.gasto_total
    rendimiento = calcular_rendimiento_ciclo(db, campana, costo_por_mensaje, [])

    mensual = Mensual(
        campana_id=campana.id, periodo_inicio=payload.periodo_inicio, periodo_fin=payload.periodo_fin,
        mensajes_total=payload.mensajes_total, gasto_total=round(payload.gasto_total, 2),
        costo_por_mensaje=round(costo_por_mensaje, 2), presupuesto=campana.presupuesto,
        sobrante=round(sobrante, 2), rendimiento=rendimiento, origen="manual",
    )
    db.add(mensual)
    db.commit()
    db.refresh(mensual)
    return mensual


# ------------------------------------------------- vencimiento y renovación
@router.post("/campanas/{campana_id}/renovar", response_model=CampanaDetalle)
def renovar_campana(campana_id: int, payload: RenovarCampanaIn,
                     cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    campana = _get_campana_or_404(db, cm.id, campana_id)
    if campana.estado != "vencida":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta campaña no está vencida")
    if payload.fecha_renovacion <= campana.fecha_renovacion:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                             "La nueva fecha de renovación debe ser posterior a la anterior")

    cliente = campana.cliente
    if cliente.estado == "no_renovado":
        if not _puede_continuar(db, cliente.id):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Pasaron más de 2 meses desde que este cliente no renovó; usa 'Crear campaña nueva' en vez de continuar con la anterior",
            )
        cliente.estado = "activo"

    hoy = dt.date.today()
    campana.fecha_inicio = hoy
    campana.fecha_renovacion = payload.fecha_renovacion
    campana.estado = "activa"
    _ensure_semana_actual(db, campana)

    registrar(db, usuario_id=cm.id, accion="renovar_campana",
              detalle={"campana_id": campana.id, "nueva_fecha_renovacion": str(payload.fecha_renovacion)})
    db.commit()
    db.refresh(campana)
    return CampanaDetalle(
        id=campana.id, cliente_id=campana.cliente_id, nombre=campana.nombre, paquete=campana.paquete,
        tipo=campana.tipo, presupuesto=float(campana.presupuesto), presupuesto_esquema=campana.presupuesto_esquema,
        formato_post=campana.formato_post, formato_3d=campana.formato_3d, formato_boton=campana.formato_boton,
        formato_otro=campana.formato_otro, lugar=campana.lugar, fecha_inicio=campana.fecha_inicio,
        fecha_renovacion=campana.fecha_renovacion, estado=campana.estado,
    )


@router.post("/clientes/{cliente_id}/no-renovar")
def no_renovar_cliente(cliente_id: int, payload: NoRenovarClienteIn,
                        cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    tiene_vencida = any(c.estado == "vencida" for c in cliente.campanas)
    if not tiene_vencida:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este cliente no tiene ninguna campaña vencida")

    if payload.accion == "borrar":
        if payload.confirmacion_nombre != cliente.nombre:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                 "El nombre escrito no coincide con el del cliente; no se eliminó nada")
        nombre = cliente.nombre
        cuenta_id = cliente.cuenta_id
        db.delete(cliente)
        db.flush()
        if cuenta_id is not None:
            otros = db.query(Cliente).filter_by(cuenta_id=cuenta_id).count()
            if otros == 0:
                db.query(CuentaPublicitaria).filter_by(id=cuenta_id).delete()
        registrar(db, usuario_id=cm.id, accion="borrar_cliente_no_renovado",
                  detalle={"cliente_id": cliente_id, "nombre": nombre})
        db.commit()
        return {"resultado": "eliminado"}

    cliente.estado = "no_renovado"
    db.add(ArchivoNoRenovado(cliente_id=cliente.id, cm_id=cm.id, motivo=payload.motivo))
    registrar(db, usuario_id=cm.id, accion="archivar_no_renovado",
              detalle={"cliente_id": cliente.id, "nombre": cliente.nombre})
    db.commit()
    return {"resultado": "conservado"}


@router.post("/clientes/{cliente_id}/reactivar", response_model=CampanaDetalle, status_code=status.HTTP_201_CREATED)
def reactivar_cliente(cliente_id: int, payload: ClienteLoteCampanaIn,
                       cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    """Trae de vuelta a un cliente de 'No renovados' con una campaña nueva
    desde cero. Si pasaron 2 meses o más desde que se archivó, es 'borrón y
    cuenta nueva': se borran sus campañas vencidas (y con ellas su historial
    de semanas/mensuales); si no, esas campañas se quedan como historial."""
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)
    if cliente.estado != "no_renovado":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este cliente no está en 'No renovados'")

    se_purgo_historial = not _puede_continuar(db, cliente.id)
    if se_purgo_historial:
        for vieja in list(cliente.campanas):
            db.delete(vieja)
        db.flush()

    nueva = Campana(
        cliente_id=cliente.id, nombre=payload.nombre, paquete=payload.paquete, tipo=payload.tipo,
        presupuesto=payload.presupuesto, presupuesto_esquema="mensual",
        formato_post=payload.formato_post, formato_3d=payload.formato_3d, formato_boton=payload.formato_boton,
        formato_otro=payload.formato_otro, lugar=payload.lugar, fecha_inicio=payload.fecha_inicio,
        fecha_renovacion=payload.fecha_renovacion, estado="activa",
    )
    db.add(nueva)
    cliente.estado = "activo"
    db.flush()
    _ensure_semana_actual(db, nueva)

    registrar(db, usuario_id=cm.id, accion="reactivar_cliente",
              detalle={"cliente_id": cliente.id, "nombre": cliente.nombre, "historial_purgado": se_purgo_historial})
    db.commit()
    db.refresh(nueva)
    return CampanaDetalle(
        id=nueva.id, cliente_id=nueva.cliente_id, nombre=nueva.nombre, paquete=nueva.paquete,
        tipo=nueva.tipo, presupuesto=float(nueva.presupuesto), presupuesto_esquema=nueva.presupuesto_esquema,
        formato_post=nueva.formato_post, formato_3d=nueva.formato_3d, formato_boton=nueva.formato_boton,
        formato_otro=nueva.formato_otro, lugar=nueva.lugar, fecha_inicio=nueva.fecha_inicio,
        fecha_renovacion=nueva.fecha_renovacion, estado=nueva.estado,
    )


@router.get("/no-renovados", response_model=list[NoRenovadoItem])
def listar_no_renovados(cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    clientes = db.query(Cliente).filter_by(cm_id=cm.id, estado="no_renovado").order_by(Cliente.nombre).all()
    out = []
    for c in clientes:
        vencidas = [camp for camp in c.campanas if camp.estado == "vencida"]
        ultima = max(vencidas, key=lambda camp: camp.fecha_renovacion) if vencidas else None
        out.append(NoRenovadoItem(
            id=c.id, nombre=c.nombre,
            campanas=[CampanaResumen(id=camp.id, nombre=camp.nombre, tipo=camp.tipo, estado=camp.estado) for camp in c.campanas],
            puede_continuar=_puede_continuar(db, c.id) and ultima is not None,
            ultima_campana=CampanaResumen(id=ultima.id, nombre=ultima.nombre, tipo=ultima.tipo, estado=ultima.estado) if ultima else None,
        ))
    return out


# ------------------------------------------------------- reportes en PDF
@router.get("/clientes/{cliente_id}/reporte-mensual")
def reporte_mensual_pdf(cliente_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    """Especificación, sección 6: el CM también puede generar el reporte
    mensual formal de sus propios clientes."""
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)

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

    registrar(db, usuario_id=cm.id, accion="generar_reporte_mensual",
              detalle={"cliente_id": cliente.id, "cliente_nombre": cliente.nombre, "periodo": periodo})
    db.commit()

    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/clientes/{cliente_id}/reporte-semanal")
def reporte_semanal_pdf(cliente_id: int, cm: Usuario = Depends(require_cm), db: Session = Depends(get_db)):
    """Reporte semanal en PDF, en lenguaje para el cliente final."""
    cliente = _get_cliente_or_404(db, cm.id, cliente_id)

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

    registrar(db, usuario_id=cm.id, accion="generar_reporte_semanal",
              detalle={"cliente_id": cliente.id, "cliente_nombre": cliente.nombre, "periodo": periodo})
    db.commit()

    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
