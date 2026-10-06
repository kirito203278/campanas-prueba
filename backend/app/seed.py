"""Datos de prueba tomados de la especificación (prompt_arranque, fase 1).

Crea los CMs KORI, SARAY, URIEL, ALONDRA, FATIMA y LUZ (con cuenta de CM y
cuenta de admin separadas, como indica el comentario de esquema_base_datos.sql
sobre 'luz.cm' / 'luz.admin'), más algunos clientes de ejemplo con sus
campañas (datos generales completos: paquete, tipo, presupuesto, formato,
lugar, fechas, cuenta publicitaria vinculada).

No se siembran datos de captura (mensajes, costos, observaciones ni
mensuales): el sistema arranca desde cero, como en un lanzamiento real. Cada
campaña sí recibe la fila vacía de "semana en curso", igual que cuando se
crea una campaña real desde la interfaz — es el contenedor donde el CM
captura, no un dato de prueba.

Idempotente: si ya hay usuarios en la base no hace nada, salvo que se pase
FORCE_SEED=true.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.dates import most_recent_saturday, week_range_for
from app.models import Campana, Cliente, CuentaPublicitaria, Semana, Usuario
from app.security.crypto import compute_huella, encrypt_value
from app.security.passwords import build_username, generate_secure_password, hash_password

CREDENTIALS_OUT = Path(__file__).resolve().parent.parent / "seed_credentials.txt"


def create_user(db: Session, existing_usernames: set[str], nombre: str, apellido: str | None,
                 rol: str, solo_lectura: bool, credentials_log: list[str]) -> Usuario:
    username = build_username(nombre, apellido, rol, existing_usernames)
    existing_usernames.add(username)
    password = generate_secure_password()
    usuario = Usuario(
        nombre=f"{nombre} {apellido}".strip() if apellido else nombre,
        username=username,
        password_hash=hash_password(password),
        rol=rol,
        solo_lectura=solo_lectura,
        activo=True,
        primer_ingreso=True,
        creado_en=dt.datetime.now(dt.timezone.utc),
    )
    db.add(usuario)
    db.flush()
    credentials_log.append(f"{username:<20} {password}   (rol={rol}{'/solo_lectura' if solo_lectura else ''})")
    return usuario


def get_or_create_cuenta(db: Session, usuario_cuenta: str, password_cuenta: str) -> CuentaPublicitaria:
    huella = compute_huella(usuario_cuenta, password_cuenta)
    cuenta = db.query(CuentaPublicitaria).filter_by(huella=huella).one_or_none()
    if cuenta:
        return cuenta
    cuenta = CuentaPublicitaria(
        usuario_enc=encrypt_value(usuario_cuenta),
        password_enc=encrypt_value(password_cuenta),
        huella=huella,
        creado_en=dt.datetime.now(dt.timezone.utc),
    )
    db.add(cuenta)
    db.flush()
    return cuenta


def build_campana(cliente: Cliente, nombre: str, tipo: str, paquete: str, presupuesto: float,
                   fecha_inicio: dt.date, fecha_renovacion: dt.date, lugar: str) -> Campana:
    return Campana(
        cliente=cliente,
        nombre=nombre,
        paquete=paquete,
        tipo=tipo,
        presupuesto=presupuesto,
        presupuesto_esquema="mensual",
        formato_post=True,
        formato_3d=False,
        formato_boton=tipo == "nacional",
        formato_otro=False,
        lugar=lugar,
        fecha_inicio=fecha_inicio,
        fecha_renovacion=fecha_renovacion,
        estado="activa",
        creado_en=dt.datetime.now(dt.timezone.utc),
    )


def _crear_campana_con_semana_actual(db: Session, cliente: Cliente, nombre: str, tipo: str, paquete: str,
                                      presupuesto: float, fecha_inicio: dt.date, fecha_renovacion: dt.date,
                                      lugar: str) -> Campana:
    campana = build_campana(cliente, nombre, tipo, paquete, presupuesto, fecha_inicio, fecha_renovacion, lugar)
    db.add(campana)
    db.flush()
    inicio, fin = week_range_for(dt.date.today())
    db.add(Semana(campana_id=campana.id, inicio=inicio, fin=fin, editable=True))
    return campana


def seed() -> None:
    settings = get_settings()
    db = SessionLocal()
    credentials_log: list[str] = []
    try:
        if db.query(Usuario).count() > 0 and not settings.force_seed:
            print("Ya existen usuarios; se omite el seed (usa FORCE_SEED=true para forzar).")
            return

        existing_usernames: set[str] = set()
        today = dt.date.today()
        current_saturday = most_recent_saturday(today)

        # ---- Usuarios: CMs + Luz (cm y admin) -----------------------------
        kori = create_user(db, existing_usernames, "Kori", None, "cm", False, credentials_log)
        saray = create_user(db, existing_usernames, "Saray", None, "cm", False, credentials_log)
        create_user(db, existing_usernames, "Uriel", None, "cm", False, credentials_log)
        create_user(db, existing_usernames, "Alondra", None, "cm", False, credentials_log)
        create_user(db, existing_usernames, "Fatima", None, "cm", False, credentials_log)
        luz_cm = Usuario(
            nombre="Luz", username="luz.cm", password_hash=hash_password(_luz_password(credentials_log, "luz.cm", "cm")),
            rol="cm", solo_lectura=False, activo=True, primer_ingreso=True,
            creado_en=dt.datetime.now(dt.timezone.utc),
        )
        luz_admin = Usuario(
            nombre="Luz", username="luz.admin", password_hash=hash_password(_luz_password(credentials_log, "luz.admin", "admin")),
            rol="admin", solo_lectura=False, activo=True, primer_ingreso=True,
            creado_en=dt.datetime.now(dt.timezone.utc),
        )
        db.add_all([luz_cm, luz_admin])
        db.flush()

        # ---- Cuenta publicitaria compartida (sección 9-a: Novedades / BTW Amigos) ----
        cuenta_compartida = get_or_create_cuenta(db, "novedades_ads", "N0ved@des2026!")

        novedades = Cliente(cm_id=kori.id, cuenta=cuenta_compartida, nombre="Novedades",
                             estado="activo", creado_en=dt.datetime.now(dt.timezone.utc))
        btw_amigos = Cliente(cm_id=kori.id, cuenta=cuenta_compartida, nombre="BTW Amigos",
                              estado="activo", creado_en=dt.datetime.now(dt.timezone.utc))
        db.add_all([novedades, btw_amigos])
        db.flush()

        _crear_campana_con_semana_actual(
            db, novedades, "LOCAL ADV - NOVEDADES", "local", "Estándar", 6000.0,
            current_saturday - dt.timedelta(weeks=5), current_saturday + dt.timedelta(weeks=6),
            "Mazatlán, Culiacán",
        )
        _crear_campana_con_semana_actual(
            db, btw_amigos, "LOCAL ADV - BTW AMIGOS", "local", "Básico", 3500.0,
            current_saturday - dt.timedelta(weeks=3), current_saturday + dt.timedelta(weeks=8),
            "Culiacán",
        )

        # ---- Saray: Ferretería El Tornillo ---------------------------------
        ferreteria = Cliente(cm_id=saray.id, nombre="Ferretería El Tornillo", estado="activo",
                              creado_en=dt.datetime.now(dt.timezone.utc))
        db.add(ferreteria)
        db.flush()

        _crear_campana_con_semana_actual(
            db, ferreteria, "NACIONAL ADV - FERRETERIA", "nacional", "Campaña", 9000.0,
            current_saturday - dt.timedelta(weeks=4), current_saturday + dt.timedelta(weeks=5),
            "Nacional",
        )

        # ---- Luz (como CM): Clínica Vital ----------------------------------
        clinica = Cliente(cm_id=luz_cm.id, nombre="Clínica Vital", estado="activo",
                           creado_en=dt.datetime.now(dt.timezone.utc))
        db.add(clinica)
        db.flush()

        _crear_campana_con_semana_actual(
            db, clinica, "LOCAL ADV - CLINICA VITAL", "local", "VIP", 12000.0,
            current_saturday - dt.timedelta(weeks=6), current_saturday + dt.timedelta(weeks=3),
            "Mazatlán",
        )

        # Los CM con cartera ya sembrada no son "nuevos": se saltan la
        # pantalla de bienvenida. Uriel, Alondra y Fátima se quedan con
        # primer_ingreso=True y sin clientes para poder probar ese flujo.
        kori.primer_ingreso = False
        saray.primer_ingreso = False
        luz_cm.primer_ingreso = False

        db.commit()

        _write_credentials_file(credentials_log)
        print(f"Seed completo. Credenciales guardadas en {CREDENTIALS_OUT} (no se versiona).")
        print("\n".join(credentials_log))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _luz_password(credentials_log: list[str], username: str, rol: str) -> str:
    password = generate_secure_password()
    credentials_log.append(f"{username:<20} {password}   (rol={rol})")
    return password


def _write_credentials_file(lines: list[str]) -> None:
    header = (
        "Credenciales de prueba generadas por seed.py — SOLO DESARROLLO.\n"
        "Cada contraseña se muestra una sola vez, igual que en el flujo real de alta de CM.\n\n"
    )
    CREDENTIALS_OUT.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    seed()
