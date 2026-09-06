# AppAI â€” Sprint 0 â†’ Sprint 1: Progress Tracker

**Date:** September 2026
**Status:** ðŸŸ¢ Phase 1 Complete â€” Phase 2 (Source Code Intelligence) is Next


---

## âœ… What's Been Built

| Deliverable | Status | Commit |
|---|---|---|
| AppAI Hub â€” FastAPI + WebSocket server | âœ… Done | `2d8d83a` |
| App Registry (SQLite) | âœ… Done | `2d8d83a` |
| Session Manager (in-memory) | âœ… Done | `2d8d83a` |
| LLM Router (config-driven, 4 backends) | âœ… Done | `2d8d83a` |
| Ollama backend (Qwen 2.5 7B) | âœ… Done | `2d8d83a` |
| OpenAI backend | âœ… Done | `2d8d83a` |
| Anthropic Claude backend | âœ… Done | `2d8d83a` |
| **llama.cpp backend** (server + embedded) | âœ… Done | `5c90652` |
| ChromaDB RAG retriever (role-filtered) | âœ… Done | `2d8d83a` |
| App Manifest / Widget store (SQLite) | âœ… Done | `2d8d83a` |
| Overlay Planner (LLM text â†’ step JSON) | âœ… Done | `2d8d83a` |
| RBAC module (5 roles + permissions) | âœ… Done | `2d8d83a` |
| Health check + HTTP API endpoints | âœ… Done | `2d8d83a` |
| Web SDK â€” WebSocket client + backoff reconnect | âœ… Done | `775f3ab` |
| Web SDK â€” Chat panel sidebar (responsive) | âœ… Done | `775f3ab` |
| Web SDK â€” Overlay engine (6 styles) | âœ… Done | `775f3ab` |
| Web SDK â€” Consent dialogs | âœ… Done | `775f3ab` |
| Web SDK â€” Context streaming (idle, errors) | âœ… Done | `775f3ab` |
| Demo app â€” BillingPro (invoice system) | âœ… Done | `89cf1f0` |
| Hub startup script (`start_hub.ps1`) | âœ… Done | `89cf1f0` |
| KB seed script (`seed_demo.py`) | âœ… Done | `89cf1f0` |
| Python dependencies installed | âœ… Done | (local) |

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
| **Primary LLM** | **llama.cpp** (server mode, `localhost:8080`) |
| Local LLM alternative | Ollama â€” Qwen 2.5 7B |
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

## Phase 1 Adjusted Plan â€” Web App First

Since we're starting with a **web app** as the pilot, Phase 1 and 3 are reordered
to build the Web SDK and web overlay before the Qt SDK.

### Phase 1 â€” Core Foundation + Web SDK (Weeks 1â€“4)

**Week 1â€“2: AppAI Hub Skeleton**
- [x] FastAPI app with asyncio WebSocket server
- [ ] App Registry (SQLite â€” register/list apps)
- [x] Session Manager (in-memory, keyed by user_id + app_id)
- [x] LLM Router (Ollama + OpenAI + Anthropic + llama.cpp)
- [x] Basic RAG pipeline (LangChain + ChromaDB)
- [x] Health check endpoint

**Week 2â€“3: Web SDK (JavaScript)**
- [x] WebSocket client (connects to Hub, handles reconnect)
- [ ] Chat panel UI (embedded sidebar â€” HTML/CSS/JS, no framework dep)
- [x] All-steps-in-chat display
- [x] Consent dialog component (screenshot, doc access)
- [ ] User registration flow (name + email â†’ app_user role)

**Week 3â€“4: Web Overlay Engine**
- [x] Transparent div overlay (z-index: 99999)
- [x] Overlay styles: pulse ring, glow box, animated arrow, drop zone, step badge
- [ ] Step-by-step advance (detect DOM event â†’ advance to next step)
- [x] All-at-once tour mode toggle
- [ ] Widget ID â†’ DOM coordinate resolver

**Week 4: End-to-End Integration**
- [x] Pilot web app instrumented with Web SDK
- [ ] User asks question â†’ Hub retrieves KB â†’ LLM answers â†’ overlay guides
- [x] Demo: full guided walkthrough on a real web app feature

**Phase 1 Milestone:** A real web app user can ask a question and be
visually guided step-by-step to complete a task. âœ…

---

### Phase 2 — Source Code Intelligence (In Progress)

- [x] Python source code parser (`.py` AST: classes, methods, docstrings, Qt signals, routes)
- [x] CMake build parser (`CMakeLists.txt`: targets, Qt modules, dependencies, `.ui` form lists)
- [x] Qt Designer UI form parser (`.ui` XML: widgets, labels, screens)
- [x] Codebase ingestion coordinator (`CodeIngestor` + `/api/kb/{app_id}/ingest_source` endpoint)
- [x] KB `content_type` tagging (`source_code` vs `ui_description` / `workflow`)
- [ ] Source code parser: Web (.jsx, .tsx, .vue, .html, routes)
- [ ] External doc ingestion (PDF, HTML, Markdown, URLs)
- [ ] Incremental re-parsing on code update

---

### Phase 3 â€” Qt SDK (Weeks 9â€“12)
*(Moved after Web SDK â€” now focused on Qt 5 + Qt 6 both)*

- [ ] Qt SDK architecture (shared core + Qt5/Qt6 compatibility layer)
- [ ] WebSocket client (QtWebSockets â€” available in Qt 5.3+ and Qt 6)
- [ ] Chat panel widget (QDockWidget or floating QWidget)
- [ ] Qt transparent overlay window (WA_TransparentForMouseEvents)
- [ ] Overlay styles matching Web SDK (pulse ring, arrow, spotlight, drop zone)
- [ ] QAccessible integration â†’ widget ID to screen coordinate resolver
- [ ] Step-by-step advance (QEvent filter on target widgets)
- [ ] Qt 5 / Qt 6 compatibility testing

---

### Phase 4 â€” RBAC + Admin Dashboard (Weeks 13â€“16)

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

### Phase 5 â€” Proactive Intelligence (Weeks 17â€“18)

- [ ] Live context tracker (current screen, idle time, visible errors)
- [ ] Proactive trigger engine (rule-based)
- [ ] Non-intrusive hint bubble in chat panel
- [ ] Drag-file detection + instant drop zone overlay
- [ ] User preference: configure / disable proactive hints

---

### Phase 6 â€” Support Workflows + Escalation (Weeks 19â€“20)

- [ ] Escalation ticket auto-creation (conversation transcript + context)
- [ ] ðŸ‘Ž "This didn't help" feedback button + feedback collection
- [ ] Knowledge Gap auto-detection + report
- [ ] Support agent KB correction workflow
- [ ] External ticketing webhook (Jira / Freshdesk / Zendesk â€” config-driven)

---

### Phase 7 â€” Enterprise & Hardening (Weeks 21â€“24)

- [ ] vLLM integration + GPU server setup guide
- [ ] Qdrant integration (replaces ChromaDB for enterprise)
- [ ] Redis session store
- [ ] Load testing (100 concurrent sessions)
- [ ] Security audit (consent flows, RBAC enforcement, code filter)
- [ ] Deployment runbook (local + enterprise)
- [ ] Developer documentation

---

## Environment Setup â€” Day 1 Checklist

### Every Developer Machine
- [x] Python 3.11+ installed
- [x] Node.js 18+ installed (for Web SDK + Admin Dashboard)
- [ ] Ollama installed: https://ollama.ai
- [ ] Pull Qwen 2.5 7B model: ollama pull qwen2.5:7b
- [x] Git configured with SSH access to github.com:adityasingh1993/AsistantApp.git
- [ ] Docker Desktop installed (for ChromaDB + future Redis/Qdrant)

### Verify Ollama is working
ollama run qwen2.5:7b "Hello, explain what you are in one sentence"

### Repository Setup
git clone git@github.com:adityasingh1993/AsistantApp.git

---

## Proposed Repository Structure (Full Project)

``
AsistantApp/
â”œâ”€â”€ docs/                         # HLD, implementation plan, sprint notes
â”œâ”€â”€ appai-hub/                    # Python FastAPI Hub (core service)
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ main.py               # FastAPI app entry point
â”‚   â”‚   â”œâ”€â”€ websocket_server.py   # WebSocket connection handler
â”‚   â”‚   â”œâ”€â”€ session_manager.py    # User session tracking
â”‚   â”‚   â””â”€â”€ app_registry.py       # Registered apps store
â”‚   â”œâ”€â”€ kb/
â”‚   â”‚   â”œâ”€â”€ parser/               # Source code parsers (Tree-sitter)
â”‚   â”‚   â”œâ”€â”€ ingestion.py          # Doc ingestion pipeline
â”‚   â”‚   â”œâ”€â”€ retriever.py          # Hybrid RAG retriever
â”‚   â”‚   â””â”€â”€ manifest_store.py     # App manifest SQLite store
â”‚   â”œâ”€â”€ llm/
â”‚   â”‚   â”œâ”€â”€ router.py             # LLM backend abstraction
â”‚   â”‚   â”œâ”€â”€ ollama_backend.py
â”‚   â”‚   â”œâ”€â”€ vllm_backend.py
â”‚   â”‚   â”œâ”€â”€ openai_backend.py
â”‚   â”‚   â””â”€â”€ anthropic_backend.py
â”‚   â”œâ”€â”€ overlay/
â”‚   â”‚   â””â”€â”€ planner.py            # Widget ID â†’ overlay step mapping
â”‚   â”œâ”€â”€ proactive/
â”‚   â”‚   â””â”€â”€ engine.py             # Proactive trigger rules
â”‚   â”œâ”€â”€ support/
â”‚   â”‚   â”œâ”€â”€ tickets.py            # Escalation ticket management
â”‚   â”‚   â””â”€â”€ knowledge_gaps.py     # Gap detection + reporting
â”‚   â”œâ”€â”€ auth/
â”‚   â”‚   â”œâ”€â”€ rbac.py               # Role-based access control
â”‚   â”‚   â””â”€â”€ jwt_handler.py
â”‚   â””â”€â”€ config/
â”‚       â””â”€â”€ appai.config.yaml     # Master config file
â”‚
â”œâ”€â”€ sdk/
â”‚   â”œâ”€â”€ web/                      # JavaScript Web SDK
â”‚   â”‚   â”œâ”€â”€ appai-sdk.js          # Core SDK (WebSocket + chat panel)
â”‚   â”‚   â”œâ”€â”€ overlay.js            # Web overlay engine
â”‚   â”‚   â”œâ”€â”€ consent.js            # Consent dialog manager
â”‚   â”‚   â””â”€â”€ appai-sdk.min.js      # Minified production build
â”‚   â””â”€â”€ qt/                       # C++ Qt SDK
â”‚       â”œâ”€â”€ AppAIClient.h/.cpp    # WebSocket client
â”‚       â”œâ”€â”€ AppAIOverlay.h/.cpp   # Transparent overlay window
â”‚       â”œâ”€â”€ AppAIChatPanel.h/.cpp # Chat panel widget
â”‚       â”œâ”€â”€ ConsentDialog.h/.cpp  # Consent dialogs
â”‚       â””â”€â”€ CMakeLists.txt
â”‚
â”œâ”€â”€ admin-dashboard/              # React + TypeScript Admin UI
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â”‚   â”œâ”€â”€ Apps.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ Users.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ KnowledgeBase.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ Support.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ Config.tsx
â”‚   â”‚   â”‚   â””â”€â”€ Health.tsx
â”‚   â”‚   â””â”€â”€ components/
â”‚   â””â”€â”€ package.json
â”‚
â””â”€â”€ README.md
``

---

## Week 1 â€” Sprint 1 Story List

| Story | Owner | Points |
|---|---|---|
| Setup Python project structure for Hub | Backend | 2 | ✅ Done
| FastAPI app + WebSocket server skeleton | Backend | 3 | ✅ Done
| App Registry (SQLite CRUD) | Backend | 2 | ✅ Done
| Session Manager (in-memory) | Backend | 2 | ✅ Done
| LLM Router (Ollama + OpenAI + Anthropic + llama.cpp) | AI/ML | 3 | ✅ Done
| ChromaDB integration + basic RAG | AI/ML | 3 | ✅ Done
| Web SDK: WebSocket client + chat panel + overlay | Web SDK | 3 | ✅ Done
| Pilot web app: BillingPro with full SDK integration | Web SDK | 2 | ✅ Done
| Dev environment + startup + seed scripts | DevOps | 1 | ✅ Done

**Total: ~21 points â€” achievable in 1 week with 2-3 developers**

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

**All decisions resolved:**

1. ✅ **Chat panel placement**: Right-side floating sidebar, 380px wide, collapses to 💬 button on mobile
2. ✅ **Web SDK distribution**: Single JS file, CDN-style (appai-sdk.js) — no bundler needed
3. ⏳ **Qt SDK CMakeLists**: To be decided in Phase 3
4. **Hub port**: 7788 for WebSocket server, 7789 for admin API â€” confirm no conflicts
