"""
main.py
AppAI Hub — FastAPI application entry point.

Exposes:
  - HTTP REST endpoints for app management, session listing, and KB ingestion.
  - WebSocket endpoint at /ws/{app_id}/{user_id}.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 7788 --reload
"""

import logging
import os
from pathlib import Path

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Internal modules ──────────────────────────────────────────────────────────
from core.app_registry import AppRegistry
from core.session_manager import SessionManager
from core.websocket_server import WebSocketServer
from llm.router import LLMRouter
from kb.retriever import KBRetriever
from kb.manifest_store import ManifestStore
from overlay.planner import OverlayPlanner

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("appai.hub")

# ── Config ────────────────────────────────────────────────────────────────────
_CONFIG_PATH = Path(__file__).parent / "config" / "appai.config.yaml"

with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
    _CONFIG = yaml.safe_load(_f)

_STORAGE_CFG = _CONFIG.get("storage", {})
_KB_CFG = _CONFIG.get("knowledge_base", {})

# Ensure data directory exists
_DATA_DIR = Path(_STORAGE_CFG.get("sqlite_path", "./data/appai.db")).parent
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Singletons ────────────────────────────────────────────────────────────────
app_registry = AppRegistry(db_path=_STORAGE_CFG.get("sqlite_path", "./data/appai.db"))
session_manager = SessionManager()
llm_router = LLMRouter(config_path=str(_CONFIG_PATH))
kb_retriever = KBRetriever(
    chromadb_path=_KB_CFG.get("chromadb_path", "./data/chromadb"),
    embedding_model=_KB_CFG.get("embedding_model", "nomic-embed-text"),
    embedding_base_url=_KB_CFG.get("embedding_base_url", "http://localhost:11434"),
)
manifest_store = ManifestStore(db_path=_STORAGE_CFG.get("sqlite_path", "./data/appai.db"))
overlay_planner = OverlayPlanner(manifest_store=manifest_store)
ws_server = WebSocketServer(
    app_registry=app_registry,
    session_manager=session_manager,
    llm_router=llm_router,
    kb_retriever=kb_retriever,
    overlay_planner=overlay_planner,
)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AppAI Hub",
    version="1.0.0",
    description="AI assistant platform hub — WebSocket + REST API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialise databases and print config summary."""
    await app_registry.initialize_db()
    await manifest_store.initialize_db()

    provider = _CONFIG.get("llm", {}).get("provider", "ollama")
    model = _CONFIG.get("llm", {}).get("model", "?")
    logger.info("=" * 60)
    logger.info("AppAI Hub started")
    logger.info("  LLM provider : %s  model=%s", provider, model)
    logger.info("  ChromaDB     : %s", _KB_CFG.get("chromadb_path"))
    logger.info("  SQLite       : %s", _STORAGE_CFG.get("sqlite_path"))
    logger.info("=" * 60)

# ── Pydantic request/response models ─────────────────────────────────────────

class AppRegisterRequest(BaseModel):
    name: str
    description: str = ""
    source_path: str = ""
    docs_path: str = ""

class KBAddDocumentRequest(BaseModel):
    content: str
    content_type: str = "user_doc"   # ui_description | source_code | user_doc | workflow | error_message
    source: str = "manual"

# ── HTTP Endpoints ────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    """Service health check."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "llm_provider": _CONFIG.get("llm", {}).get("provider", "ollama"),
    }


@app.post("/api/apps/register", tags=["apps"])
async def register_app(req: AppRegisterRequest):
    """Register a new app with the Hub."""
    registered = await app_registry.register_app(
        name=req.name,
        description=req.description,
        source_path=req.source_path,
        docs_path=req.docs_path,
    )
    return registered


@app.get("/api/apps", tags=["apps"])
async def list_apps():
    """List all registered apps."""
    return await app_registry.list_apps()


@app.get("/api/apps/{app_id}", tags=["apps"])
async def get_app(app_id: str):
    """Get details for a single app."""
    app_data = await app_registry.get_app(app_id)
    if app_data is None:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")
    return app_data


@app.get("/api/sessions", tags=["admin"])
async def list_sessions():
    """List all active sessions (admin endpoint)."""
    sessions = session_manager.get_active_sessions()
    # Strip conversation history for the listing response
    return [
        {k: v for k, v in s.items() if k != "conversation_history"}
        for s in sessions
    ]


@app.post("/api/kb/{app_id}/add_document", tags=["knowledge_base"])
async def add_kb_document(app_id: str, req: KBAddDocumentRequest):
    """
    Add a document to an app's knowledge base.

    content_type options: ui_description | source_code | user_doc | workflow | error_message
    """
    # Verify app exists
    app_data = await app_registry.get_app(app_id)
    if app_data is None:
        raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")

    await kb_retriever.add_documents(
        app_id=app_id,
        documents=[{
            "content": req.content,
            "metadata": {
                "content_type": req.content_type,
                "source": req.source,
            },
        }],
    )
    return {"status": "added", "app_id": app_id, "content_type": req.content_type}


# ── WebSocket Endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws/{app_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, app_id: str, user_id: str):
    """
    Main WebSocket endpoint.

    Apps connect here and exchange JSON messages according to the
    AppAI Hub WebSocket protocol.
    """
    try:
        await ws_server.handle_connection(websocket, app_id, user_id)
    except WebSocketDisconnect:
        logger.info("Client disconnected: app=%s user=%s", app_id, user_id)
