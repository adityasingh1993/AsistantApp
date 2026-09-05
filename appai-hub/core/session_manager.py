"""
core/session_manager.py
In-memory session manager for AppAI Hub.

Each session tracks conversation history, current UI context, and metadata
for one (app_id, user_id) pair.  Sessions are keyed by a UUID session_id.

Note: This is a single-process in-memory store.  For multi-process
deployments, replace with a Redis-backed implementation.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Maximum conversation turns kept in context window sent to the LLM.
MAX_HISTORY = 10


class SessionManager:
    """Thread-safe (asyncio single-threaded) in-memory session store."""

    def __init__(self):
        # Dict[session_id: str, session: dict]
        self._sessions: dict[str, dict] = {}

    # ── session lifecycle ────────────────────────────────────────────────────

    def create_session(self, app_id: str, user_id: str, role: str) -> str:
        """
        Create a new session and return its session_id (UUID string).

        Each session carries:
          - session_id     : unique identifier
          - app_id         : the registered app this session belongs to
          - user_id        : caller-supplied user identifier
          - role           : RBAC role string (e.g. 'app_user')
          - conversation_history: list of {role, content, message_id} dicts
          - current_context: latest UI context dict from context_update messages
          - created_at     : ISO-8601 creation timestamp
          - last_active    : ISO-8601 last-activity timestamp
          - last_hint_at   : timestamp of last proactive hint (for rate-limiting)
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        self._sessions[session_id] = {
            "session_id": session_id,
            "app_id": app_id,
            "user_id": user_id,
            "role": role,
            "conversation_history": [],
            "current_context": {},
            "created_at": now,
            "last_active": now,
            "last_hint_at": None,
        }
        logger.info("Session created: %s  app=%s user=%s role=%s",
                    session_id, app_id, user_id, role)
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """Return the session dict or None if it does not exist."""
        return self._sessions.get(session_id)

    def close_session(self, session_id: str):
        """Remove the session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Session closed: %s", session_id)

    # ── mutations ────────────────────────────────────────────────────────────

    def update_context(self, session_id: str, context_dict: dict):
        """
        Replace the session's current_context with the provided dict.
        Also bumps last_active to now.
        """
        session = self._sessions.get(session_id)
        if session is None:
            logger.warning("update_context: unknown session %s", session_id)
            return
        session["current_context"] = context_dict
        session["last_active"] = datetime.utcnow().isoformat()

    def add_message(self, session_id: str, role: str, content: str) -> str:
        """
        Append a message to conversation history.

        Args:
            session_id: target session
            role:       'user' or 'assistant'
            content:    message text

        Returns:
            message_id (UUID string) for later reference (e.g. feedback)
        """
        session = self._sessions.get(session_id)
        if session is None:
            logger.warning("add_message: unknown session %s", session_id)
            return ""
        message_id = str(uuid.uuid4())
        session["conversation_history"].append({
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        session["last_active"] = datetime.utcnow().isoformat()
        return message_id

    def mark_hint_sent(self, session_id: str):
        """Record when a proactive hint was last sent (for rate-limiting)."""
        session = self._sessions.get(session_id)
        if session:
            session["last_hint_at"] = datetime.utcnow().isoformat()

    # ── queries ──────────────────────────────────────────────────────────────

    def get_conversation_history(self, session_id: str) -> list[dict]:
        """
        Return the last MAX_HISTORY messages for the session.

        Returns an empty list if the session is not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return []
        return session["conversation_history"][-MAX_HISTORY:]

    def get_active_sessions(self) -> list[dict]:
        """Return a snapshot list of all active session dicts."""
        return list(self._sessions.values())
