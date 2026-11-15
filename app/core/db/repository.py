"""Thread and session metadata repository."""

from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timezone

from app.core.db.session import get_sqlite_connection


class ThreadRepository:
    """Repository handling CRUD operations for chat thread metadata."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self._conn = conn or get_sqlite_connection()
        self.init_db()

    def init_db(self) -> None:
        """Create the metadata tables if they don't already exist."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_threads (
                thread_id TEXT PRIMARY KEY,
                chat_name TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_threads_updated 
            ON chat_threads(updated_at DESC)
        """)
        self._conn.commit()

    def upsert_thread(self, thread_id: str, chat_name: str) -> None:
        """Insert or update a thread title."""
        now = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO chat_threads (thread_id, chat_name, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET
                chat_name = excluded.chat_name,
                updated_at = excluded.updated_at
        """, (str(thread_id), chat_name, now, now))
        self._conn.commit()

    def get_thread_name(self, thread_id: str) -> Optional[str]:
        """Fetch the title for a single thread."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT chat_name FROM chat_threads WHERE thread_id = ?
        """, (str(thread_id),))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_all_thread_names(self) -> List[str]:
        """Fetch all existing thread names (used to avoid naming collisions)."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT chat_name FROM chat_threads")
        return [row[0] for row in cursor.fetchall()]

    def list_threads(self, thread_ids: Optional[List[str]] = None) -> Dict[str, str]:
        """List thread_id to chat_name mappings, optionally filtered by thread IDs."""
        cursor = self._conn.cursor()
        if thread_ids:
            placeholders = ",".join("?" for _ in thread_ids)
            cursor.execute(f"""
                SELECT thread_id, chat_name 
                FROM chat_threads 
                WHERE thread_id IN ({placeholders})
                ORDER BY updated_at DESC
            """, tuple(thread_ids))
        else:
            cursor.execute("""
                SELECT thread_id, chat_name 
                FROM chat_threads 
                ORDER BY updated_at DESC
            """)
        return {row[0]: row[1] for row in cursor.fetchall()}

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread from the metadata store."""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM chat_threads WHERE thread_id = ?", (str(thread_id),))
        self._conn.commit()
        return cursor.rowcount > 0

