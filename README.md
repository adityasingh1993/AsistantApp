# AppAI — Intelligent Proactive App Assistant

> A universal, embeddable AI assistant platform for Qt desktop and web-framework applications.

AppAI attaches to any app, understands its structure by parsing source code, and provides real-time proactive guidance to end users — including **visual overlay guidance** that highlights exactly where to click, fill, or drop files on the live application UI.

---

## Key Features

- 🔍 **Source Code Intelligence** — Parses Qt (.ui, .qml, .cpp, .py) and Web (.jsx, .vue, .html) source to deeply understand every feature, form, dialog, and workflow
- 🖼️ **Visual UI Overlay** — Draws transparent animated highlights, arrows, step numbers, and drop-zone indicators directly on the live app window
- 🤖 **Proactive Assistance** — Detects when users are stuck and offers help before they even ask
- 🔒 **Privacy-First** — Local LLM (Ollama / vLLM) by default; OpenAI / Claude available as opt-in cloud backends
- ✅ **Consent-Driven** — Never captures screenshots or reads private documents without explicit user permission
- 🏗️ **Hub Architecture** — One centralized AppAI Hub serves all apps and all users; scales from a single machine to an enterprise server cluster

---

## Documentation

| Document | Description |
|---|---|
| [High-Level Design (HLD)](docs/AppAI_HLD.md) | Full system architecture, component breakdown, data flows, deployment modes, tech stack, and security model |
| [Implementation Plan](docs/implementation_plan.md) | Design decisions, confirmed choices, scalability architecture, and development roadmap |

---

## Planned Project Structure

```
AsistantApp/
├── docs/                        # Design documents (HLD, implementation plan)
├── appai-hub/                   # AppAI Hub — central Python/FastAPI service
│   ├── core/                    # Agent core, session manager, app registry
│   ├── kb/                      # Knowledge base engine, source parser, RAG
│   ├── llm/                     # LLM router (Ollama, vLLM, OpenAI, Claude)
│   ├── overlay/                 # Overlay planner (widget ID to step mapping)
│   └── proactive/               # Proactive trigger engine
├── sdk/
│   ├── qt/                      # Qt C++ SDK (WebSocket client + overlay QWidget)
│   └── web/                     # JavaScript SDK (WebSocket client + div overlay)
├── config/                      # appai.config.yaml templates
└── README.md
```

---

## Architecture Overview

```
Qt/Web App + SDK  ──── WebSocket ────▶  AppAI Hub
                                            │
                             ┌──────────────┼──────────────┐
                             ▼              ▼              ▼
                       Knowledge Base    LLM Router    Session Mgr
                       (per-app RAG)   (Ollama/vLLM)  (per-user)
```

---

## Deployment Modes

| Mode | Use Case | LLM | Vector Store |
|---|---|---|---|
| Local Hub | Dev / small team | Ollama (localhost) | ChromaDB |
| Enterprise Server | Many users, many apps | vLLM (GPU server) | Qdrant + Redis |

---

## Status

> 🚧 **Design Phase** — Architecture and HLD finalized. Development starting soon.
