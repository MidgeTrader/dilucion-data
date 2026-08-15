"""SQLite-backed TTL cache for external API responses.

Uses a thread-local persistent SQLite connection so that uvicorn's thread
pool doesn't trip the "SQLite objects created in a thread can only be used
in that same thread" error.  WAL journal mode enables safe concurrent reads.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """Simple key-value cache with time-to-live stored in SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Thread-local storage: one connection per thread per instance
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Return the thread's persistent connection, creating it lazily."""
        conn: Optional[sqlite3.Connection] = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        """Ensure schema exists in the calling thread."""
        self._get_conn()

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if not expired."""
        now = time.time()
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if not row:
                return None
            value, expires_at = row
            if expires_at < now:
                conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
                conn.commit()
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in cache for key=%s", key)
                return None
        except sqlite3.OperationalError as exc:
            logger.warning("Cache get failed for key=%s: %s", key, exc)
            return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store value with TTL."""
        expires_at = time.time() + ttl_seconds
        payload = json.dumps(value, default=str)
        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO cache (cache_key, value, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    value = excluded.value,
                    expires_at = excluded.expires_at
                """,
                (key, payload, expires_at),
            )
            conn.commit()
        except sqlite3.OperationalError as exc:
            logger.warning("Cache set failed for key=%s: %s", key, exc)

    def delete(self, key: str) -> None:
        try:
            conn = self._get_conn()
            conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
            conn.commit()
        except sqlite3.OperationalError as exc:
            logger.warning("Cache delete failed for key=%s: %s", key, exc)

    def purge_expired(self) -> int:
        """Remove expired entries and return count deleted."""
        now = time.time()
        try:
            conn = self._get_conn()
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (now,),
            )
            conn.commit()
            return cursor.rowcount
        except sqlite3.OperationalError as exc:
            logger.warning("Cache purge failed: %s", exc)
            return 0
