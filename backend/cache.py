"""SQLite-backed TTL cache for external API responses."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """Simple key-value cache with time-to-live stored in SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if not expired."""
        now = time.time()
        with self._connect() as conn:
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

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store value with TTL."""
        expires_at = time.time() + ttl_seconds
        payload = json.dumps(value, default=str)
        with self._connect() as conn:
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

    def delete(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
            conn.commit()

    def purge_expired(self) -> int:
        """Remove expired entries and return count deleted."""
        now = time.time()
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (now,),
            )
            conn.commit()
            return cursor.rowcount
