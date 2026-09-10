from pathlib import Path

from pgvector.psycopg import register_vector
from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.core.config import settings

_pool: ConnectionPool | None = None
_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _configure_connection(conn: Connection) -> None:
    try:
        register_vector(conn)
    except Exception:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        register_vector(conn)


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=8,
            kwargs={"autocommit": True},
            configure=_configure_connection,
            open=False,
        )
        _pool.open()
    return _pool


def _run_sql_script(sql: str) -> None:
    statements = [part.strip() for part in sql.split(";") if part.strip()]
    import psycopg

    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        for statement in statements:
            conn.execute(statement)


def init_db() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    _run_sql_script(_SCHEMA_PATH.read_text(encoding="utf-8"))
    get_pool()


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
