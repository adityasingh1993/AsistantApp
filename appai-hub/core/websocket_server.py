"""
core/websocket_server.py
Core WebSocket connection handler for AppAI Hub.

Manages the full lifecycle of a single WebSocket connection:
  - Session registration
  - Query processing (KB retrieval → LLM → Overlay planning)
  - Context updates with proactive hint evaluation
  - Feedback logging
  - Consent response processing

Message protocol is JSON over WebSocket (see architecture docs).
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Minimum gap between proactive hints (seconds) to avoid spamming the user.
_HINT_COOLDOWN_SECONDS = 30

# Idle threshold (ms) after which a proactive hint may be triggered.
_IDLE_HINT_MS = 10_000


class WebSocketServer:
    """
    Handles all WebSocket traffic for a single client connection.

    Each call to handle_connection() is an independent asyncio coroutine
    managing one app_id / user_id pair.

    Args:
        app_registry:    AppRegistry instance.
        session_manager: SessionManager instance.
        llm_router:      LLMRouter instance.
        kb_retriever:    KBRetriever instance.
        overlay_planner: OverlayPlanner instance.
    """

    def __init__(self, app_registry, session_manager, llm_router,
                 kb_retriever, overlay_planner):
        self.app_registry = app_registry
        self.session_manager = session_manager
        self.llm_router = llm_router
        self.kb_retriever = kb_retriever
        self.overlay_planner = overlay_planner

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    async def _send(ws: WebSocket, payload: dict):
        """Serialise and send a JSON payload over the WebSocket."""
        await ws.send_text(json.dumps(payload))

    @staticmethod
    async def _send_error(ws: WebSocket, message: str):
        await WebSocketServer._send(ws, {"type": "error", "message": message})

    # ── main connection handler ───────────────────────────────────────────────

    async def handle_connection(self, websocket: WebSocket, app_id: str, user_id: str):
        """
        Accept and handle a WebSocket connection for app_id / user_id.

        Runs until the client disconnects or a protocol error occurs.
        """
        await websocket.accept()
        logger.info("WS connected: app=%s user=%s", app_id, user_id)

        # Verify the app exists
        app = await self.app_registry.get_app(app_id)
        if app is None or not app.get("is_active"):
            await self._send_error(websocket, f"App '{app_id}' not found or inactive.")
            await websocket.close()
            return

        current_session: Optional[dict] = None

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON payload.")
                    continue

                msg_type = msg.get("type")

                if msg_type == "register_session":
                    current_session = await self._handle_register_session(
                        websocket, msg, app_id, user_id
                    )

                elif msg_type == "query":
                    session = self._resolve_session(msg, current_session)
                    if session is None:
                        await self._send_error(websocket, "Invalid or missing session_id.")
                        continue
                    await self._handle_query(websocket, msg, session, app)

                elif msg_type == "context_update":
                    session = self._resolve_session(msg, current_session)
                    if session:
                        await self._handle_context_update(websocket, msg, session)

                elif msg_type == "feedback":
                    session = self._resolve_session(msg, current_session)
                    if session:
                        await self._handle_feedback(websocket, msg, session)

                elif msg_type == "consent_response":
                    session = self._resolve_session(msg, current_session)
                    if session:
                        await self._handle_consent_response(websocket, msg, session)

                else:
                    await self._send_error(websocket, f"Unknown message type: {msg_type!r}")

        except Exception as exc:
            logger.warning("WS connection closed for app=%s user=%s: %s", app_id, user_id, exc)
        finally:
            if current_session:
                self.session_manager.close_session(current_session["session_id"])
            logger.info("WS disconnected: app=%s user=%s", app_id, user_id)

    def _resolve_session(self, msg: dict, current_session: Optional[dict]) -> Optional[dict]:
        """
        Resolve the session from either the message session_id field or
        the current_session stored for this connection.
        """
        session_id = msg.get("session_id")
        if session_id:
            return self.session_manager.get_session(session_id)
        return current_session

    # ── message handlers ─────────────────────────────────────────────────────

    async def _handle_register_session(
        self, ws: WebSocket, msg: dict, app_id: str, user_id: str
    ) -> dict:
        """
        Create a new session and reply with session_created.

        The role defaults to 'app_user' if not supplied by the client.
        """
        role = msg.get("role", "app_user")
        session_id = self.session_manager.create_session(app_id, user_id, role)
        session = self.session_manager.get_session(session_id)

        await self._send(ws, {
            "type": "session_created",
            "session_id": session_id,
            "role": role,
        })
        logger.info("Session registered: %s role=%s", session_id, role)
        return session

    async def _handle_query(
        self, ws: WebSocket, msg: dict, session: dict, app: dict
    ):
        """
        Full RAG + LLM + Overlay pipeline for a user query.

        Steps:
          1. Extract query text and update context if provided.
          2. Retrieve relevant KB chunks (role-filtered).
          3. Generate LLM response with system prompt + history + KB.
          4. Build overlay steps from the response.
          5. Send response message.
          6. Persist assistant message to session history.
        """
        query_text = msg.get("text", "").strip()
        if not query_text:
            await self._send_error(ws, "Query text is empty.")
            return

        # Optionally update context from the query message
        if "context" in msg:
            self.session_manager.update_context(session["session_id"], msg["context"])
            session = self.session_manager.get_session(session["session_id"])

        role = session["role"]
        app_id = session["app_id"]
        current_context = session.get("current_context", {})

        # 1. Save user message
        self.session_manager.add_message(session["session_id"], "user", query_text)

        # 2. Retrieve KB context
        #    cloud_safe=True forces source_code chunk exclusion when the active
        #    LLM backend is a cloud provider (OpenAI, Anthropic).
        #    This ensures code never leaves the machine without explicit consent.
        cloud_safe = self.llm_router.is_cloud_provider()
        kb_chunks = await self.kb_retriever.retrieve(
            app_id=app_id,
            query=query_text,
            role=role,
            n_results=5,
            cloud_safe=cloud_safe,
        )
        kb_context = "\n\n---\n\n".join(kb_chunks) if kb_chunks else ""

        # 3. Build conversation history for the LLM
        history = self.session_manager.get_conversation_history(session["session_id"])
        # Convert to simple {role, content} dicts for the router
        lm_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in history
        ]

        # 4. Generate LLM response
        llm_response = await self.llm_router.generate(
            messages=lm_messages,
            role=role,
            app_name=app.get("name", "AppAI"),
            app_context=current_context,
            kb_context=kb_context,
        )

        # 5. Build overlay steps
        overlay_steps = await self.overlay_planner.build_overlay_steps(app_id, llm_response)

        # 6. Determine overlay_mode
        overlay_mode = "step_by_step" if overlay_steps else "none"

        # 7. Assign message_id and save assistant reply
        message_id = self.session_manager.add_message(
            session["session_id"], "assistant", llm_response
        )

        # 8. Send response
        await self._send(ws, {
            "type": "response",
            "message_id": message_id,
            "chat_message": llm_response,
            "overlay_steps": overlay_steps,
            "overlay_mode": overlay_mode,
        })

    async def _handle_context_update(self, ws: WebSocket, msg: dict, session: dict):
        """
        Update the session's UI context and evaluate proactive triggers.
        """
        context = msg.get("context", {})
        self.session_manager.update_context(session["session_id"], context)
        # Re-fetch updated session
        session = self.session_manager.get_session(session["session_id"])
        await self._check_proactive_triggers(ws, session)

    async def _handle_feedback(self, ws: WebSocket, msg: dict, session: dict):
        """
        Log user feedback for a specific message.

        Currently logs to the application logger.  In a production system
        this would be persisted to the feedback SQLite table or forwarded
        to a ticketing system.
        """
        logger.info(
            "Feedback received: session=%s message_id=%s rating=%s reason=%s",
            session["session_id"],
            msg.get("message_id"),
            msg.get("rating"),
            msg.get("reason"),
        )

    async def _handle_consent_response(self, ws: WebSocket, msg: dict, session: dict):
        """
        Process the user's response to a consent_request.

        If granted=True and screenshot data is present, it would be forwarded
        to the support ticketing pipeline.  Placeholder logic for Phase 1.
        """
        action = msg.get("action")
        granted = msg.get("granted", False)
        data = msg.get("data")

        if granted and data:
            logger.info(
                "Consent granted for action=%s session=%s — data received",
                action, session["session_id"],
            )
            # TODO: forward screenshot data to support ticket pipeline
        else:
            logger.info(
                "Consent denied / no data for action=%s session=%s",
                action, session["session_id"],
            )

    # ── proactive hints ───────────────────────────────────────────────────────

    async def _check_proactive_triggers(self, ws: WebSocket, session: dict):
        """
        Evaluate simple rules to send proactive hints to the user.

        Rules:
          1. idle_ms > 10 000 AND current screen differs from last known →
             hint about the current screen's primary action.
          2. errors list is non-empty AND no hint sent in the last
             _HINT_COOLDOWN_SECONDS → hint about the error.

        Rate-limited by last_hint_at to avoid spamming.
        """
        context = session.get("current_context", {})
        idle_ms = context.get("idle_ms", 0)
        screen = context.get("screen", "")
        errors = context.get("errors", [])

        # Rate-limit: skip if a hint was sent recently
        last_hint_at = session.get("last_hint_at")
        if last_hint_at:
            elapsed = (datetime.utcnow() - datetime.fromisoformat(last_hint_at)).total_seconds()
            if elapsed < _HINT_COOLDOWN_SECONDS:
                return

        hint_message = None

        # Rule 1: idle user on a new screen
        if idle_ms > _IDLE_HINT_MS and screen:
            hint_message = (
                f"It looks like you're on the **{screen}** screen. "
                "Would you like a quick guide on what you can do here?"
            )

        # Rule 2: errors detected (takes priority over idle hint)
        if errors:
            error_summary = "; ".join(str(e) for e in errors[:3])
            hint_message = (
                f"I noticed some errors: {error_summary}. "
                "Would you like help resolving them?"
            )

        if hint_message:
            hint_id = str(uuid.uuid4())
            await self._send(ws, {
                "type": "proactive_hint",
                "message": hint_message,
                "hint_id": hint_id,
            })
            self.session_manager.mark_hint_sent(session["session_id"])
            logger.info(
                "Proactive hint sent: session=%s hint_id=%s",
                session["session_id"], hint_id,
            )
