"""
core/app_registry.py
SQLite-backed registry that tracks every app connected to the AppAI Hub.

Uses aiosqlite for fully async I/O.  The registry is the source of truth
for app metadata and is consulted at session-creation time.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)


class AppRegistry:
    """
    Async SQLite-backed registry for registered apps.

    Table schema (apps):
        id              TEXT PRIMARY KEY   — UUID string
        name            TEXT NOT NULL
        description     TEXT
        kb_collection_id TEXT             — ChromaDB collection name
        source_path     TEXT             — path to source code directory
        docs_path       TEXT             — path to user-docs directory
        created_at      TEXT             — ISO-8601 timestamp
        is_active       INTEGER          — 1=active, 0=inactive
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize_db(self):
        """Create the `apps` table if it does not already exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS apps (
                    id               TEXT PRIMARY KEY,
                    name             TEXT NOT NULL,
                    description      TEXT,
                    kb_collection_id TEXT,
                    source_path      TEXT,
                    docs_path        TEXT,
                    created_at       TEXT NOT NULL,
                    is_active        INTEGER NOT NULL DEFAULT 1
                )
            """)
            await db.commit()
        logger.info("AppRegistry: DB initialised at %s", self.db_path)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row, cursor) -> dict:
        """Convert an aiosqlite Row to a plain dict using column names."""
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    # ── public API ───────────────────────────────────────────────────────────

    async def register_app(
        self,
        name: str,
        description: str = "",
        source_path: str = "",
        docs_path: str = "",
    ) -> dict:
        """
        Insert a new app record and return it as a dict.

        The kb_collection_id is derived from the app id so ChromaDB
        collections stay stable across restarts.
        """
        app_id = str(uuid.uuid4())
        kb_collection_id = f"app_{app_id.replace('-', '_')}"
        created_at = datetime.utcnow().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO apps (id, name, description, kb_collection_id,
                                  source_path, docs_path, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (app_id, name, description, kb_collection_id,
                 source_path, docs_path, created_at),
            )
            await db.commit()

        logger.info("Registered app '%s' with id=%s", name, app_id)
        return {
            "id": app_id,
            "name": name,
            "description": description,
            "kb_collection_id": kb_collection_id,
            "source_path": source_path,
            "docs_path": docs_path,
            "created_at": created_at,
            "is_active": True,
        }

    async def get_app(self, app_id: str) -> Optional[dict]:
        """Return an app dict by id, or None if not found."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM apps WHERE id = ?", (app_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return self._row_to_dict(row, cursor)

    async def list_apps(self) -> list[dict]:
        """Return all registered apps as a list of dicts."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM apps ORDER BY created_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_dict(r, cursor) for r in rows]

    async def update_app_status(self, app_id: str, is_active: bool):
        """Activate or deactivate an app."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE apps SET is_active = ? WHERE id = ?",
                (1 if is_active else 0, app_id),
            )
            await db.commit()
        logger.info("App %s is_active set to %s", app_id, is_active)
