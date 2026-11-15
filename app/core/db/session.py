"""Database connection and LangGraph checkpointer initialization."""

from __future__ import annotations

import sqlite3
from typing import Any
from urllib.parse import urlparse

from app.core.config import get_settings

_sqlite_conn: sqlite3.Connection | None = None
_checkpointer: Any = None


def get_sqlite_connection() -> sqlite3.Connection:
    """Return a thread-safe SQLite connection configured for concurrent access."""
    global _sqlite_conn
    if _sqlite_conn is None:
        settings = get_settings()
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        _sqlite_conn = sqlite3.connect(
            database=db_path,
            check_same_thread=False,
            timeout=10.0,
        )
        # Enable Write-Ahead Logging (WAL) and foreign keys for high-performance concurrency
        _sqlite_conn.execute("PRAGMA journal_mode=WAL;")
        _sqlite_conn.execute("PRAGMA foreign_keys=ON;")
        _sqlite_conn.execute("PRAGMA busy_timeout=5000;")
    return _sqlite_conn


def get_checkpointer():
    """Factory that returns the appropriate LangGraph checkpointer based on configuration."""
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    settings = get_settings()
    db_url = settings.DATABASE_URL

    if db_url.startswith("postgresql") or db_url.startswith("postgres"):
        from langgraph.checkpoint.postgres import PostgresSaver
        _checkpointer = PostgresSaver.from_conn_string(db_url)
        _checkpointer.setup()
    else:
        from langgraph.checkpoint.sqlite import SqliteSaver
        conn = get_sqlite_connection()
        _checkpointer = SqliteSaver(conn=conn)
        _checkpointer.setup()

    return _checkpointer

