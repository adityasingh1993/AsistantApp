# AppAI — Sprint 0: Pre-Development Checklist & Day 1 Plan

**Date:** September 2026  
**Status:** Ready to Build ✅

---

## Final Confirmed Decisions (Complete Set)

| Decision | Choice |
|---|---|
| Knowledge base source | App source code + optional external docs |
| UI guidance style | Visual overlay on live app window |
| Overlay navigation | Step-by-step (default) + all-at-once toggle |
| Steps in chat | Always shown upfront in chat panel |
| Action execution | Guide only |
| Screenshot / doc access | Consent-first |
| Connectivity | AppAI Hub (centralized) |
| Local LLM | Ollama — **Qwen 2.5 7B** (primary) |
| Self-hosted LLM | vLLM (enterprise/GPU) |
| Cloud LLM | OpenAI + Anthropic (opt-in) |
| Scalability | Hub & Spoke |
| RBAC | 5 roles: super_admin, app_admin, developer, support_agent, app_user |
| Code confidentiality | 3-layer enforcement (prompt + filter + KB tagging) |
| Admin dashboard | Separate React web UI |
| Support team | support_agent role + escalation + knowledge gap loop |
| **Pilot platform** | **Web app first** (then Qt 5/6) |
| **Qt versions to support** | **Qt 5.x and Qt 6.x** (both) |

---

## Phase 1 Adjusted Plan — Web App First

Since we're starting with a **web app** as the pilot, Phase 1 and 3 are reordered
to build the Web SDK and web overlay before the Qt SDK.

### Phase 1 — Core Foundation + Web SDK (Weeks 1–4)

**Week 1–2: AppAI Hub Skeleton**
- [ ] FastAPI app with asyncio WebSocket server
- [ ] App Registry (SQLite — register/list apps)
- [ ] Session Manager (in-memory, keyed by user_id + app_id)
- [ ] LLM Router skeleton (Qwen 2.5 7B via Ollama)
- [ ] Basic RAG pipeline (LangChain + ChromaDB)
- [ ] Health check endpoint

**Week 2–3: Web SDK (JavaScript)**
- [ ] WebSocket client (connects to Hub, handles reconnect)
- [ ] Chat panel UI (embedded sidebar — HTML/CSS/JS, no framework dep)
- [ ] All-steps-in-chat display
- [ ] Consent dialog component (screenshot, doc access)
- [ ] User registration flow (name + email → app_user role)

**Week 3–4: Web Overlay Engine**
- [ ] Transparent div overlay (z-index: 99999)
- [ ] Overlay styles: pulse ring, glow box, animated arrow, drop zone, step badge
- [ ] Step-by-step advance (detect DOM event → advance to next step)
- [ ] All-at-once tour mode toggle
- [ ] Widget ID → DOM coordinate resolver

**Week 4: End-to-End Integration**
- [ ] Pilot web app instrumented with Web SDK
- [ ] User asks question → Hub retrieves KB → LLM answers → overlay guides
- [ ] Demo: full guided walkthrough on a real web app feature

**Phase 1 Milestone:** A real web app user can ask a question and be
visually guided step-by-step to complete a task. ✅

---

### Phase 2 — Source Code Intelligence (Weeks 5–8)
*(No change from original plan)*

- [ ] Source code parser: Web (.jsx, .tsx, .vue, .html, routes)
- [ ] Source code parser: Qt (.ui, .qml, .cpp, .py) — for upcoming Qt phase
- [ ] App Manifest builder + SQLite storage
- [ ] External doc ingestion (PDF, HTML, Markdown, URLs)
- [ ] Incremental re-parsing on code update
- [ ] KB content_type tagging (ui_description / source_code / user_doc / workflow)

---

### Phase 3 — Qt SDK (Weeks 9–12)
*(Moved after Web SDK — now focused on Qt 5 + Qt 6 both)*

- [ ] Qt SDK architecture (shared core + Qt5/Qt6 compatibility layer)
- [ ] WebSocket client (QtWebSockets — available in Qt 5.3+ and Qt 6)
- [ ] Chat panel widget (QDockWidget or floating QWidget)
- [ ] Qt transparent overlay window (WA_TransparentForMouseEvents)
- [ ] Overlay styles matching Web SDK (pulse ring, arrow, spotlight, drop zone)
- [ ] QAccessible integration → widget ID to screen coordinate resolver
- [ ] Step-by-step advance (QEvent filter on target widgets)
- [ ] Qt 5 / Qt 6 compatibility testing

---

### Phase 4 — RBAC + Admin Dashboard (Weeks 13–16)

- [ ] JWT authentication for Hub API
- [ ] 5-role RBAC implementation (super_admin, app_admin, developer, support_agent, app_user)
- [ ] Role-gated LLM prompt system
- [ ] Response Safety Filter (post-LLM code stripping for non-developer roles)
- [ ] Admin Dashboard frontend (React + TypeScript)
  - App Management panel
  - User Management panel (role assignment)
  - KB Management panel
  - System Configuration panel
- [ ] Support Panel
  - Ticket list + ticket detail view
  - Knowledge Gap report
  - Flagged responses queue

---

### Phase 5 — Proactive Intelligence (Weeks 17–18)

- [ ] Live context tracker (current screen, idle time, visible errors)
- [ ] Proactive trigger engine (rule-based)
- [ ] Non-intrusive hint bubble in chat panel
- [ ] Drag-file detection + instant drop zone overlay
- [ ] User preference: configure / disable proactive hints

---

### Phase 6 — Support Workflows + Escalation (Weeks 19–20)

- [ ] Escalation ticket auto-creation (conversation transcript + context)
- [ ] 👎 "This didn't help" feedback button + feedback collection
- [ ] Knowledge Gap auto-detection + report
- [ ] Support agent KB correction workflow
- [ ] External ticketing webhook (Jira / Freshdesk / Zendesk — config-driven)

---

### Phase 7 — Enterprise & Hardening (Weeks 21–24)

- [ ] vLLM integration + GPU server setup guide
- [ ] Qdrant integration (replaces ChromaDB for enterprise)
- [ ] Redis session store
- [ ] Load testing (100 concurrent sessions)
- [ ] Security audit (consent flows, RBAC enforcement, code filter)
- [ ] Deployment runbook (local + enterprise)
- [ ] Developer documentation

---

## Environment Setup — Day 1 Checklist

### Every Developer Machine
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed (for Web SDK + Admin Dashboard)
- [ ] Ollama installed: https://ollama.ai
- [ ] Pull Qwen 2.5 7B model: ollama pull qwen2.5:7b
- [ ] Git configured with SSH access to github.com:adityasingh1993/AsistantApp.git
- [ ] Docker Desktop installed (for ChromaDB + future Redis/Qdrant)

### Verify Ollama is working
ollama run qwen2.5:7b "Hello, explain what you are in one sentence"

### Repository Setup
git clone git@github.com:adityasingh1993/AsistantApp.git

---

## Proposed Repository Structure (Full Project)

``
AsistantApp/
├── docs/                         # HLD, implementation plan, sprint notes
├── appai-hub/                    # Python FastAPI Hub (core service)
│   ├── core/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── websocket_server.py   # WebSocket connection handler
│   │   ├── session_manager.py    # User session tracking
│   │   └── app_registry.py       # Registered apps store
│   ├── kb/
│   │   ├── parser/               # Source code parsers (Tree-sitter)
│   │   ├── ingestion.py          # Doc ingestion pipeline
│   │   ├── retriever.py          # Hybrid RAG retriever
│   │   └── manifest_store.py     # App manifest SQLite store
│   ├── llm/
│   │   ├── router.py             # LLM backend abstraction
│   │   ├── ollama_backend.py
│   │   ├── vllm_backend.py
│   │   ├── openai_backend.py
│   │   └── anthropic_backend.py
│   ├── overlay/
│   │   └── planner.py            # Widget ID → overlay step mapping
│   ├── proactive/
│   │   └── engine.py             # Proactive trigger rules
│   ├── support/
│   │   ├── tickets.py            # Escalation ticket management
│   │   └── knowledge_gaps.py     # Gap detection + reporting
│   ├── auth/
│   │   ├── rbac.py               # Role-based access control
│   │   └── jwt_handler.py
│   └── config/
│       └── appai.config.yaml     # Master config file
│
├── sdk/
│   ├── web/                      # JavaScript Web SDK
│   │   ├── appai-sdk.js          # Core SDK (WebSocket + chat panel)
│   │   ├── overlay.js            # Web overlay engine
│   │   ├── consent.js            # Consent dialog manager
│   │   └── appai-sdk.min.js      # Minified production build
│   └── qt/                       # C++ Qt SDK
│       ├── AppAIClient.h/.cpp    # WebSocket client
│       ├── AppAIOverlay.h/.cpp   # Transparent overlay window
│       ├── AppAIChatPanel.h/.cpp # Chat panel widget
│       ├── ConsentDialog.h/.cpp  # Consent dialogs
│       └── CMakeLists.txt
│
├── admin-dashboard/              # React + TypeScript Admin UI
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Apps.tsx
│   │   │   ├── Users.tsx
│   │   │   ├── KnowledgeBase.tsx
│   │   │   ├── Support.tsx
│   │   │   ├── Config.tsx
│   │   │   └── Health.tsx
│   │   └── components/
│   └── package.json
│
└── README.md
``

---

## Week 1 — Sprint 1 Story List

| Story | Owner | Points |
|---|---|---|
| Setup Python project structure for Hub | Backend | 2 |
| FastAPI app + WebSocket server skeleton | Backend | 3 |
| App Registry (SQLite CRUD) | Backend | 2 |
| Session Manager (in-memory) | Backend | 2 |
| Ollama LLM Router (Qwen 2.5 7B) | AI/ML | 3 |
| ChromaDB integration + basic RAG | AI/ML | 3 |
| Web SDK: WebSocket client + chat panel scaffold | Web SDK | 3 |
| Pilot web app: add Web SDK integration | Web SDK | 2 |
| Dev environment setup docs | DevOps | 1 |

**Total: ~21 points — achievable in 1 week with 2-3 developers**

---

## Definition of Done for Phase 1

A demo where:
1. The pilot web app has the AppAI Web SDK embedded
2. A user types: "How do I [do something in the app]?"
3. The Hub retrieves relevant info from the app's knowledge base
4. Qwen 2.5 7B generates a step-by-step answer
5. The chat panel shows all steps
6. The web overlay animates on the correct UI elements
7. The user follows the steps and completes the task

---

## Open Technical Decisions for Sprint 1

These are small decisions the team should make in Week 1:

1. **Chat panel placement**: floating sidebar (right side) or embedded as part of the page?
2. **Web SDK distribution**: single JS file (CDN-style, easiest) or npm package?
3. **Qt SDK CMakeLists**: separate static library or header-only integration?
4. **Hub port**: 7788 for WebSocket server, 7789 for admin API — confirm no conflicts
