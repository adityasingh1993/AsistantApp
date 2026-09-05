"""
kb/manifest_store.py
SQLite store for app widget manifests (UI element maps).

The manifest allows the OverlayPlanner to resolve step text to concrete
widget IDs that the AppAI SDK can highlight in the client application.
"""

import logging
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)


class ManifestStore:
    """
    Async SQLite store for app_widgets records.

    Table schema (app_widgets):
        id           TEXT PRIMARY KEY
        app_id       TEXT NOT NULL
        widget_id    TEXT NOT NULL      — SDK-side element identifier
        label        TEXT NOT NULL      — Human-readable label (for fuzzy matching)
        widget_type  TEXT               — e.g. "button", "menu", "input"
        screen       TEXT               — which screen this widget lives on
        description  TEXT
        x            REAL               — bounding box (optional, for layout hints)
        y            REAL
        width        REAL
        height       REAL
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize_db(self):
        """Create the app_widgets table if it does not already exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS app_widgets (
                    id          TEXT PRIMARY KEY,
                    app_id      TEXT NOT NULL,
                    widget_id   TEXT NOT NULL,
                    label       TEXT NOT NULL,
                    widget_type TEXT,
                    screen      TEXT,
                    description TEXT,
                    x           REAL,
                    y           REAL,
                    width       REAL,
                    height      REAL
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_app_widgets_app_id ON app_widgets(app_id)"
            )
            await db.commit()
        logger.info("ManifestStore: DB initialised at %s", self.db_path)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row, cursor) -> dict:
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    # ── public API ───────────────────────────────────────────────────────────

    async def upsert_widget(
        self,
        app_id: str,
        widget_id: str,
        label: str,
        widget_type: str = "",
        screen: str = "",
        description: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
    ):
        """
        Insert or replace a widget record.

        Uses widget_id + app_id as the logical unique key.  If the widget
        already exists it is replaced (SQLite REPLACE semantics).
        """
        import uuid
        record_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            # Check for existing record to preserve id
            async with db.execute(
                "SELECT id FROM app_widgets WHERE app_id = ? AND widget_id = ?",
                (app_id, widget_id),
            ) as cur:
                row = await cur.fetchone()
                if row:
                    record_id = row[0]

            await db.execute(
                """
                INSERT OR REPLACE INTO app_widgets
                    (id, app_id, widget_id, label, widget_type, screen,
                     description, x, y, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (record_id, app_id, widget_id, label, widget_type, screen,
                 description, x, y, width, height),
            )
            await db.commit()

    async def find_widget_by_label(
        self, app_id: str, label: str
    ) -> Optional[dict]:
        """
        Fuzzy-match a widget by label using SQL LIKE.

        Searches for widgets whose label contains any word from the query
        (case-insensitive).  Returns the first match or None.
        """
        # Tokenise the label into keywords and try each
        keywords = [w.strip() for w in label.lower().split() if len(w.strip()) > 2]

        async with aiosqlite.connect(self.db_path) as db:
            for keyword in keywords:
                async with db.execute(
                    "SELECT * FROM app_widgets WHERE app_id = ? AND LOWER(label) LIKE ?",
                    (app_id, f"%{keyword}%"),
                ) as cur:
                    row = await cur.fetchone()
                    if row:
                        return self._row_to_dict(row, cur)
        return None

    async def get_all_widgets(self, app_id: str) -> list[dict]:
        """Return all widgets for an app."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM app_widgets WHERE app_id = ?", (app_id,)
            ) as cur:
                rows = await cur.fetchall()
                return [self._row_to_dict(r, cur) for r in rows]
