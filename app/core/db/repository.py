"""Thread and session metadata repository — PostgreSQL backend."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Generator

import psycopg

from app.core.db.session import get_connection_pool


@contextmanager
def _get_conn() -> Generator[psycopg.Connection, None, None]:
    """Borrow a connection from the pool and return it when done."""
    pool = get_connection_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


class ThreadRepository:
    """Repository handling CRUD operations for chat thread metadata."""

    def __init__(self) -> None:
        self.init_db()

    def init_db(self) -> None:
        """Create the metadata tables if they don't already exist."""
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_threads (
                        thread_id TEXT PRIMARY KEY,
                        chat_name TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chat_threads_updated
                    ON chat_threads(updated_at DESC)
                """)
            conn.commit()

    def upsert_thread(self, thread_id: str, chat_name: str) -> None:
        """Insert or update a thread title."""
        now = datetime.now(UTC)
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_threads (thread_id, chat_name, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (thread_id) DO UPDATE SET
                        chat_name  = EXCLUDED.chat_name,
                        updated_at = EXCLUDED.updated_at
                """, (str(thread_id), chat_name, now, now))
            conn.commit()

    def get_thread_name(self, thread_id: str) -> str | None:
        """Fetch the title for a single thread."""
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT chat_name FROM chat_threads WHERE thread_id = %s",
                    (str(thread_id),),
                )
                row = cur.fetchone()
        return row[0] if row else None

    def get_all_thread_names(self) -> list[str]:
        """Fetch all existing thread names (used to avoid naming collisions)."""
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT chat_name FROM chat_threads")
                return [row[0] for row in cur.fetchall()]

    def list_threads(self, thread_ids: list[str] | None = None) -> dict[str, str]:
        """List thread_id → chat_name mappings, optionally filtered by thread IDs."""
        with _get_conn() as conn:
            with conn.cursor() as cur:
                if thread_ids:
                    cur.execute("""
                        SELECT thread_id, chat_name
                        FROM chat_threads
                        WHERE thread_id = ANY(%s)
                        ORDER BY updated_at DESC
                    """, (list(thread_ids),))
                else:
                    cur.execute("""
                        SELECT thread_id, chat_name
                        FROM chat_threads
                        ORDER BY updated_at DESC
                    """)
                return {row[0]: row[1] for row in cur.fetchall()}

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread from the metadata store."""
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_threads WHERE thread_id = %s",
                    (str(thread_id),),
                )
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted

