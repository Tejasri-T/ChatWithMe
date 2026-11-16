"""Database connection and LangGraph checkpointer initialization."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg_pool import ConnectionPool

from app.core.config import get_settings

_pg_pool: ConnectionPool | None = None
_checkpointer: Any = None


def get_connection_pool() -> ConnectionPool:
    """Return a shared psycopg connection pool for PostgreSQL."""
    global _pg_pool
    if _pg_pool is None:
        settings = get_settings()
        # psycopg pool expects a plain postgresql:// URL (not the +psycopg variant)
        conninfo = settings.DATABASE_URL_RAW or settings.DATABASE_URL.replace(
            "postgresql+psycopg://", "postgresql://"
        )
        _pg_pool = ConnectionPool(
            conninfo=conninfo,
            min_size=2,
            max_size=10,
            open=True,
        )
    return _pg_pool


def get_connection() -> psycopg.Connection:
    """Borrow a connection from the pool."""
    return get_connection_pool().getconn()


def release_connection(conn: psycopg.Connection) -> None:
    """Return a connection to the pool."""
    get_connection_pool().putconn(conn)


def get_checkpointer():
    """Factory that returns the LangGraph PostgreSQL checkpointer.

    setup() runs CREATE INDEX CONCURRENTLY which cannot run inside a
    transaction block. We therefore run it on a dedicated autocommit
    connection, then hand the shared pool to the long-lived checkpointer.
    """
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    from langgraph.checkpoint.postgres import PostgresSaver

    settings = get_settings()
    conninfo = settings.DATABASE_URL_RAW or settings.DATABASE_URL.replace(
        "postgresql+psycopg://", "postgresql://"
    )

    # Run migrations on a short-lived autocommit connection so that
    # CREATE INDEX CONCURRENTLY doesn't hit the "inside transaction" error.
    with psycopg.connect(conninfo, autocommit=True) as setup_conn:
        saver = PostgresSaver(conn=setup_conn)
        saver.setup()

    # Build the persistent checkpointer backed by the shared pool.
    pool = get_connection_pool()
    _checkpointer = PostgresSaver(conn=pool)

    return _checkpointer

