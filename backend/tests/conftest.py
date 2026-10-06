"""Infraestructura de pruebas del sistema de Campañas.

Patrón tomado del sistema de Control de Clientes: se crea una base PostgreSQL
efímera por corrida, se corren las migraciones y cada test trabaja dentro de
una transacción que se revierte al terminar. Si no hay un Postgres escuchando,
las pruebas que tocan base de datos se saltan (las unitarias puras siguen
corriendo).

Levanta un Postgres con:  docker compose up -d db
(o define TEST_DATABASE_URL=postgresql://user:pass@host:puerto/postgres)
"""
import atexit
import base64
import os
import secrets
import uuid

import psycopg2
import pytest

# Secretos fuertes para que la configuración (ahora validada al arrancar) no
# rechace el arranque durante las pruebas.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))
os.environ.setdefault("HUELLA_SECRET", secrets.token_urlsafe(48))
os.environ.setdefault("JOBS_SECRET", secrets.token_urlsafe(24))
os.environ.setdefault("AES_KEY_B64", base64.b64encode(secrets.token_bytes(32)).decode())


def _find_server() -> str | None:
    candidatos = [
        os.getenv("TEST_DATABASE_URL"),
        "postgresql://demo:demo@localhost:5434/postgres",
        "postgresql://campanas:campanas@localhost:5433/postgres",
        "postgresql://postgres:postgres@localhost:5432/postgres",
    ]
    for url in candidatos:
        if not url:
            continue
        raw = url.replace("postgresql+psycopg2://", "postgresql://")
        try:
            psycopg2.connect(raw).close()
            return raw
        except psycopg2.OperationalError:
            continue
    return None


_SERVER = _find_server()
_DB_READY = False

if _SERVER:
    _DBNAME = f"camp_test_{uuid.uuid4().hex[:8]}"
    _admin = psycopg2.connect(_SERVER)
    _admin.autocommit = True
    with _admin.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{_DBNAME}"')
    _admin.close()
    _base, _, _ = _SERVER.rpartition("/")
    _RAW_URL = f"{_base}/{_DBNAME}"
    os.environ["DATABASE_URL"] = "postgresql+psycopg2://" + _RAW_URL.split("://", 1)[1]

    @atexit.register
    def _drop_test_db() -> None:
        try:
            a = psycopg2.connect(_SERVER)
            a.autocommit = True
            with a.cursor() as cur:
                cur.execute(f'DROP DATABASE IF EXISTS "{_DBNAME}" WITH (FORCE)')
            a.close()
        except Exception:
            pass

    from app.migrations.run_migrations import run_migrations

    run_migrations()
    _DB_READY = True
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://x:x@localhost/x")


from app.security import rate_limit  # noqa: E402


@pytest.fixture(autouse=True)
def _limpiar_rate_limit():
    rate_limit.reiniciar_todo()


@pytest.fixture
def db():
    if not _DB_READY:
        pytest.skip("No hay un PostgreSQL de pruebas escuchando (docker compose up -d db)")
    from sqlalchemy.orm import Session

    from app.database import engine

    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    yield session
    session.close()
    trans.rollback()
    conn.close()


@pytest.fixture
def api(db):
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)  # sin 'with': no dispara el lifespan (no arranca el scheduler)
    app.dependency_overrides.clear()


@pytest.fixture
def crear_usuario(db):
    from app.models import Usuario
    from app.security import passwords

    def _crear(nombre, username, rol="cm", solo_lectura=False, activo=True, password="Clave-de-prueba-123"):
        u = Usuario(nombre=nombre, username=username, rol=rol, solo_lectura=solo_lectura, activo=activo,
                    primer_ingreso=True, password_hash=passwords.hash_password(password))
        db.add(u)
        db.flush()
        u._password = password
        return u

    return _crear


@pytest.fixture
def auth(api):
    def _auth(u, ip="10.0.0.1"):
        r = api.post("/api/auth/login", json={"username": u.username, "password": u._password},
                     headers={"X-Forwarded-For": ip})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _auth


@pytest.fixture
def fabrica(db):
    import datetime as dt
    from decimal import Decimal

    from app.models import Campana, Cliente, Semana

    class F:
        def cliente(self, cm, nombre="Cliente Demo", estado="activo"):
            c = Cliente(cm_id=cm.id, nombre=nombre, estado=estado)
            db.add(c)
            db.flush()
            return c

        def campana(self, cliente, *, nombre="LOCAL ADV", tipo="local", paquete=None,
                    presupuesto=3500, estado="activa", renov=None):
            hoy = dt.date.today()
            camp = Campana(cliente_id=cliente.id, nombre=nombre, tipo=tipo, paquete=paquete,
                           presupuesto=Decimal(presupuesto), presupuesto_esquema="mensual",
                           fecha_inicio=hoy - dt.timedelta(days=30),
                           fecha_renovacion=renov or hoy, estado=estado)
            db.add(camp)
            db.flush()
            return camp

        def semana(self, campana, inicio, *, mensajes=None, costo=None, importe=None, editable=True):
            s = Semana(campana_id=campana.id, inicio=inicio, fin=inicio + dt.timedelta(days=6),
                       mensajes=mensajes, costo_por_resultado=costo, importe_gastado=importe, editable=editable)
            db.add(s)
            db.flush()
            return s

    return F()
