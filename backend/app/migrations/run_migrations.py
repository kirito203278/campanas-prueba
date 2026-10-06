"""Runner de migraciones minimalista.

Aplica, en orden alfabético, los archivos .sql de migrations/sql que aún no
se hayan aplicado, y registra cada uno en la tabla schema_migrations. El
archivo 001_init.sql es el esquema canónico de esquema_base_datos.sql,
copiado tal cual: esa es la fuente de verdad del modelo de datos.
"""
import sys
import time
from pathlib import Path

import psycopg2

from app.config import get_settings

SQL_DIR = Path(__file__).parent / "sql"


def _wait_for_db(dsn: str, attempts: int = 30, delay: float = 1.0) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            conn = psycopg2.connect(dsn)
            conn.close()
            return
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"No se pudo conectar a la base de datos tras {attempts} intentos: {last_error}")


def _to_psycopg2_dsn(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+psycopg2://", "postgresql://")


def run_migrations() -> None:
    settings = get_settings()
    dsn = _to_psycopg2_dsn(settings.database_url)
    _wait_for_db(dsn)

    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename    TEXT PRIMARY KEY,
                    applied_en  TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT filename FROM schema_migrations")
            applied = {row[0] for row in cur.fetchall()}

        pending = sorted(p for p in SQL_DIR.glob("*.sql") if p.name not in applied)
        if not pending:
            print("Sin migraciones pendientes.")
            return

        for path in pending:
            print(f"Aplicando migración {path.name} ...")
            sql = path.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))
            conn.commit()
            print(f"  OK: {path.name}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR aplicando migraciones: {exc}", file=sys.stderr)
        sys.exit(1)
