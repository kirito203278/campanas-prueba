from __future__ import annotations

import datetime as dt
import random
from decimal import Decimal

from sqlalchemy.orm import Session

from app.bitacora import registrar
from app.database import SessionLocal
from app.dates import most_recent_saturday
from app.jobs.cierre_ciclo import cerrar_ciclo_campana
from app.metrics import _nivel_por_costo, obtener_umbrales
from app.models import (ArchivoNoRenovado, Campana, Cliente, Mensual, Notificacion, Observacion, Semana, Usuario)
from app.security.passwords import hash_password
from app.seed import get_or_create_cuenta

UTC = dt.timezone.utc

USUARIOS = [
    ("Kori", "kori", "cm", False, "Kori-Demo-2026"),
    ("Saray", "saray", "cm", False, "Saray-Demo-2026"),
    ("Uriel", "uriel", "cm", False, "Uriel-Demo-2026"),
    ("Alondra", "alondra", "cm", False, "Alondra-Demo-2026"),
    ("Fátima", "fatima", "cm", False, "Fatima-Demo-2026"),
    ("Luz", "luz.cm", "cm", False, "Luz-Demo-2026"),
    ("Luz", "luz.admin", "admin", False, "Admin-Demo-2026"),
    ("Lectura Demo", "lectura.demo", "admin", True, "Lectura-Demo-2026"),
]

CUENTA_COMPARTIDA = ("novedades_ads", "N0ved@des2026!")

# cm, cliente, cuenta, (tipo_cuenta, metodo_pago, forma_pago), campañas
# campaña: (nombre, tipo, paquete, presupuesto, formatos, lugar, dias_para_renovar, perfil, perfiles_meses_previos)
CLIENTES = [
    ("kori", "Novedades", "compartida", ("Empresarial", "Tarjeta", "Mensual"), [
        ("LOCAL ADV - NOVEDADES", "local", "Estándar", 6000, "post", "Mazatlán, Culiacán", 12, "bueno", ["regular", "bueno"])]),
    ("kori", "BTW Amigos", "compartida", ("Empresarial", "Tarjeta", "Mensual"), [
        ("LOCAL ADV - BTW AMIGOS", "local", "Básico", 3500, "post,boton", "Culiacán", 5, "mixto_sube", ["bueno"])]),
    ("kori", "Pizzería Don Marco", "propia", ("Personal", "Transferencia", "Mensual"), [
        ("LOCAL ADV - PIZZERIA", "local", "Estándar", 5000, "post,3d", "Mazatlán", 20, "regular", ["regular", "bajo", "regular"]),
        ("NACIONAL ADV - PIZZERIA", "nacional", "Campaña", 9000, "post,boton", "Nacional", 8, "bueno", ["bueno"])]),
    ("kori", "Gimnasio Fuerza Total", "propia", ("Empresarial", "Depósito", "Mensual"), [
        ("LOCAL ADV - GIMNASIO", "local", "VIP", 8000, "post,3d,boton", "Mazatlán", 0, "bajo", ["regular", "bajo"])]),
    ("saray", "Ferretería El Tornillo", "propia", ("Empresarial", "Tarjeta", "Mensual"), [
        ("NACIONAL ADV - FERRETERIA", "nacional", "Campaña", 9000, "post,boton", "Nacional", 17, "bueno", ["bueno", "regular"])]),
    ("saray", "Boutique Aurora", "propia", ("Personal", "Tarjeta", "Mensual"), [
        ("LOCAL ADV - BOUTIQUE", "local", "Básico", 3000, "post", "Culiacán", 0, "regular", ["bueno"])]),
    ("saray", "Óptica Visión Clara", "propia", ("Empresarial", "Transferencia", "Mensual"), [
        ("LOCAL ADV - OPTICA", "local", "Estándar", 5500, "post,3d", "Mazatlán, Los Mochis", 24, "caida", ["bueno", "bueno"])]),
    ("uriel", "Clínica Dental Sonríe", "propia", ("Empresarial", "Tarjeta", "Mensual"), [
        ("LOCAL ADV - DENTAL", "local", "VIP", 10000, "post,3d", "Mazatlán", 3, "bueno", ["bueno", "regular"])]),
    ("uriel", "Panadería La Espiga", "propia", ("Personal", "Depósito", "Mensual"), [
        ("LOCAL ADV - PANADERIA", "local", "Básico", 3200, "post", "Culiacán", 14, "mixto_baja", ["bajo"])]),
    ("uriel", "Joyería Brillante", "propia", ("Empresarial", "Tarjeta", "Mensual"), [
        ("LOCAL ADV - JOYERIA", "local", "Estándar", 6500, "post,3d", "Mazatlán", 9, "regular", ["regular", "bueno"]),
        ("NACIONAL ADV - JOYERIA", "nacional", "Campaña", 12000, "post,boton", "Nacional", 26, "mixto_sube", [])]),
    ("alondra", "Inmobiliaria Hogar Dulce", "propia", ("Empresarial", "Transferencia", "Mensual"), [
        ("NACIONAL ADV - INMOBILIARIA", "nacional", "Campaña", 15000, "post,3d,boton", "Nacional", 11, "regular", ["bueno", "regular"])]),
    ("alondra", "Escuela de Idiomas Polyglot", "propia", ("Empresarial", "Tarjeta", "Mensual"), [
        ("LOCAL ADV - IDIOMAS", "local", "Estándar", 4800, "post", "Culiacán", 6, "bueno", ["bueno"])]),
    ("alondra", "Veterinaria PatiTas", "propia", ("Personal", "Depósito", "Mensual"), [
        ("LOCAL ADV - VETERINARIA", "local", "Básico", 3000, "post", "Mazatlán", 22, "bajo", [])]),
    ("luz.cm", "Clínica Vital", "propia", ("Empresarial", "Tarjeta", "Mensual"), [
        ("LOCAL ADV - CLINICA VITAL", "local", "VIP", 12000, "post,3d,boton", "Mazatlán", 15, "bueno", ["bueno", "bueno", "regular"])]),
    ("luz.cm", "Restaurante El Marinero", "propia", ("Empresarial", "Transferencia", "Mensual"), [
        ("LOCAL ADV - MARINERO", "local", "Estándar", 5200, "post,3d", "Mazatlán", 4, "mixto_sube", ["regular"])]),
    ("luz.cm", "Florería Jazmín", "propia", ("Personal", "Depósito", "Mensual"), [
        ("LOCAL ADV - FLORERIA", "local", "Básico", 2800, "post", "Culiacán", 19, "regular", [])]),
]

NO_RENOVADOS = [
    ("saray", "Zapatería El Paso", 20, ("LOCAL ADV - ZAPATERIA", "local", "Estándar", 4500, "post", "Culiacán")),
    ("uriel", "Papelería Escolar", 70, ("LOCAL ADV - PAPELERIA", "local", "Básico", 3000, "post", "Mazatlán")),
    ("alondra", "Refaccionaria Del Valle", 370, ("NACIONAL ADV - REFACCIONARIA", "nacional", "Campaña", 9000, "post,boton", "Nacional")),
]

OBSERVACIONES = [
    "El cliente pidió reforzar los fines de semana; se subió el presupuesto diario.",
    "Cambiamos el creativo principal por uno nuevo; esperar 3 días para ver el efecto.",
    "Muchos mensajes de curiosos sin intención de compra: ajustar la segmentación por edad.",
    "Buena respuesta con el formato de video corto. Mantener la próxima semana.",
    "El cliente comentó que le llegan más pedidos por WhatsApp que por Messenger.",
    "Se pausó un anuncio con bajo rendimiento y se duplicó el que mejor funciona.",
    "Pendiente: el cliente enviará fotos nuevas del local para renovar el material.",
]

CPR = {
    "local": {"bueno": (12, 18), "regular": (21, 28), "bajo": (31, 38)},
    "nacional": {"bueno": (9, 13), "regular": (15, 18), "bajo": (21, 26)},
}


def _costos(rnd: random.Random, tipo: str, perfil: str, n: int) -> list[float]:
    r = CPR[tipo]
    if perfil in r:
        a, b = r[perfil]
        return [round(rnd.uniform(a, b), 2) for _ in range(n)]
    ini, fin = (r["bueno"][0] + 2, r["bajo"][1] - 3) if perfil == "mixto_sube" else (r["bajo"][1] - 3, r["bueno"][0] + 2)
    if perfil == "caida":
        return [round(rnd.uniform(*r["bueno"]), 2) for _ in range(n)]
    pasos = max(n - 1, 1)
    return [round(ini + (fin - ini) * i / pasos + rnd.uniform(-1, 1), 2) for i in range(n)]


def _crear_usuarios(db: Session) -> dict[str, Usuario]:
    usuarios: dict[str, Usuario] = {}
    for nombre, username, rol, ro, password in USUARIOS:
        u = Usuario(nombre=nombre, username=username, password_hash=hash_password(password), rol=rol,
                    solo_lectura=ro, activo=True, primer_ingreso=True, creado_en=dt.datetime.now(UTC))
        db.add(u)
        usuarios[username] = u
    db.flush()
    return usuarios


def _crear_campana(db: Session, rnd: random.Random, cliente: Cliente, cm: Usuario, spec, hoy: dt.date,
                   sabado: dt.date) -> Campana:
    nombre, tipo, paquete, presupuesto, formatos, lugar, dias, perfil, previos = spec
    renovacion = hoy + dt.timedelta(days=dias)
    inicio = renovacion - dt.timedelta(days=30)
    fmts = set(formatos.split(","))
    campana = Campana(cliente_id=cliente.id, nombre=nombre, paquete=paquete, tipo=tipo, presupuesto=presupuesto,
                      presupuesto_esquema="mensual", formato_post="post" in fmts, formato_3d="3d" in fmts,
                      formato_boton="boton" in fmts, formato_otro=False, lugar=lugar, fecha_inicio=inicio,
                      fecha_renovacion=renovacion, estado="activa", creado_en=dt.datetime.now(UTC))
    db.add(campana)
    db.flush()

    cfg = obtener_umbrales(db, tipo, paquete)
    for m in range(len(previos), 0, -1):
        perfil_mes = previos[m - 1]
        fin = inicio - dt.timedelta(days=1 + 30 * (m - 1))
        ini = fin - dt.timedelta(days=29)
        gasto = round(presupuesto * rnd.uniform(0.88, 1.02), 2)
        cpm = _costos(rnd, tipo, perfil_mes if perfil_mes in CPR[tipo] else "regular", 1)[0]
        mensajes = int(gasto / cpm)
        costo = round(gasto / mensajes, 2)
        db.add(Mensual(campana_id=campana.id, periodo_inicio=ini, periodo_fin=fin, mensajes_total=mensajes,
                       gasto_total=gasto, costo_por_mensaje=costo, presupuesto=presupuesto,
                       sobrante=round(presupuesto - gasto, 2), rendimiento=_nivel_por_costo(cfg, costo),
                       origen="manual" if m == len(previos) else "calculado"))

    primer = most_recent_saturday(inicio)
    inicios = []
    d = primer
    while d <= sabado:
        inicios.append(d)
        d += dt.timedelta(days=7)
    costos = _costos(rnd, tipo, perfil, len(inicios))
    base = 70 if tipo == "local" else 150
    for i, ini in enumerate(inicios):
        es_actual = ini == sabado
        semana = Semana(campana_id=campana.id, inicio=ini, fin=ini + dt.timedelta(days=6), editable=es_actual)
        mensajes = int(base * rnd.uniform(0.7, 1.3))
        if perfil == "caida" and i == len(inicios) - 2:
            mensajes = int(base * 0.4)
        capturada = (not es_actual) or rnd.random() < 0.5
        if capturada:
            semana.mensajes = mensajes
            semana.costo_por_resultado = Decimal(str(costos[i]))
            semana.importe_gastado = Decimal(str(round(mensajes * costos[i], 2)))
            semana.capturado_por = cm.id
            semana.actualizado_en = dt.datetime.combine(min(ini + dt.timedelta(days=5), hoy), dt.time(18, 0), tzinfo=UTC)
        db.add(semana)

    for texto in rnd.sample(OBSERVACIONES, k=rnd.randint(1, 3)):
        db.add(Observacion(campana_id=campana.id, texto=texto, autor_id=cm.id,
                           creado_en=dt.datetime.now(UTC) - dt.timedelta(days=rnd.randint(0, 20))))
    db.flush()
    return campana


def seed_demo() -> None:
    db = SessionLocal()
    try:
        if db.query(Usuario).count() > 0:
            print("Ya existen usuarios; se omite el seed de demostración.")
            return
        rnd = random.Random(2026)
        hoy = dt.date.today()
        sabado = most_recent_saturday(hoy)
        usuarios = _crear_usuarios(db)
        admin = usuarios["luz.admin"]
        cuenta_compartida = get_or_create_cuenta(db, *CUENTA_COMPARTIDA)

        clientes: dict[str, Cliente] = {}
        cm_con_cartera: set[str] = set()
        por_cobrar_captura: dict[str, int] = {}
        vencidas: list[Campana] = []
        for cm_user, nombre, cuenta, (tipo_cuenta, metodo, forma), campanas in CLIENTES:
            cm = usuarios[cm_user]
            slug = "".join(ch for ch in nombre.lower() if ch.isalnum())[:14]
            cta = cuenta_compartida if cuenta == "compartida" else get_or_create_cuenta(db, f"{slug}_ads", f"Ads-{slug}-2026!")
            cliente = Cliente(cm_id=cm.id, cuenta=cta, nombre=nombre, estado="activo", tipo_cuenta=tipo_cuenta,
                              metodo_pago=metodo, forma_pago=forma, creado_en=dt.datetime.now(UTC))
            db.add(cliente)
            db.flush()
            clientes[nombre] = cliente
            cm_con_cartera.add(cm_user)
            for spec in campanas:
                campana = _crear_campana(db, rnd, cliente, cm, spec, hoy, sabado)
                actual = db.query(Semana).filter_by(campana_id=campana.id, inicio=sabado).one()
                if actual.mensajes is None:
                    por_cobrar_captura[cm_user] = por_cobrar_captura.get(cm_user, 0) + 1
                if spec[6] == 0:
                    vencidas.append(campana)

        for campana in vencidas:
            cerrar_ciclo_campana(db, campana)
        db.flush()

        for cm_user, nombre, dias, spec_campana in NO_RENOVADOS:
            cm = usuarios[cm_user]
            nombre_c, tipo, paquete, presupuesto, formatos, lugar = spec_campana
            cliente = Cliente(cm_id=cm.id, nombre=nombre, estado="no_renovado", tipo_cuenta="Empresarial",
                              metodo_pago="Transferencia", forma_pago="Mensual", creado_en=dt.datetime.now(UTC))
            db.add(cliente)
            db.flush()
            fin = hoy - dt.timedelta(days=dias)
            fmts = set(formatos.split(","))
            campana = Campana(cliente_id=cliente.id, nombre=nombre_c, paquete=paquete, tipo=tipo, presupuesto=presupuesto,
                              presupuesto_esquema="mensual", formato_post="post" in fmts, formato_3d=False,
                              formato_boton="boton" in fmts, formato_otro=False, lugar=lugar,
                              fecha_inicio=fin - dt.timedelta(days=30), fecha_renovacion=fin, estado="vencida")
            db.add(campana)
            db.flush()
            cfg = obtener_umbrales(db, tipo, paquete)
            for m in (1, 0):
                f_fin = fin - dt.timedelta(days=30 * m)
                gasto = round(presupuesto * rnd.uniform(0.9, 1.0), 2)
                cpm = _costos(rnd, tipo, "regular", 1)[0]
                mensajes = int(gasto / cpm)
                costo = round(gasto / mensajes, 2)
                db.add(Mensual(campana_id=campana.id, periodo_inicio=f_fin - dt.timedelta(days=30), periodo_fin=f_fin,
                               mensajes_total=mensajes, gasto_total=gasto, costo_por_mensaje=costo, presupuesto=presupuesto,
                               sobrante=round(presupuesto - gasto, 2), rendimiento=_nivel_por_costo(cfg, costo),
                               origen="manual" if m == 1 else "calculado"))
            db.add(ArchivoNoRenovado(cliente_id=cliente.id, cm_id=cm.id, motivo="No renovó el servicio",
                                     archivado_en=dt.datetime.now(UTC) - dt.timedelta(days=dias)))

        for cm_user in cm_con_cartera:
            usuarios[cm_user].primer_ingreso = False
            cm = usuarios[cm_user]
            db.add(Notificacion(usuario_id=cm.id, tipo="sistema", leida=True,
                                mensaje="Bienvenida al sistema. Aquí verás tus avisos de captura y de renovación."))
            if por_cobrar_captura.get(cm_user):
                db.add(Notificacion(usuario_id=cm.id, tipo="recordatorio_captura", leida=False,
                                    mensaje=f"Tienes {por_cobrar_captura[cm_user]} campaña(s) con la semana sin capturar."))

        for nombre, username, rol, ro, _ in USUARIOS:
            registrar(db, usuario_id=admin.id, accion="alta_usuario",
                      detalle={"username": username, "rol": rol, "solo_lectura": ro})
        registrar(db, usuario_id=admin.id, accion="migrar_cm",
                  detalle={"de": "ex-cm", "a": "kori", "clientes_migrados": 2})
        registrar(db, usuario_id=usuarios["kori"].id, accion="renovar_campana",
                  detalle={"cliente": "Pizzería Don Marco"})
        registrar(db, usuario_id=admin.id, accion="generar_reporte_mensual", detalle={"cliente": "Clínica Vital"})

        db.commit()
        print(f"Datos de demostración listos: {len(CLIENTES) + len(NO_RENOVADOS)} clientes, "
              f"{len(USUARIOS)} usuarios (ver README.md para las contraseñas).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
