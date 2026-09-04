# AppAI — Implementation Plan

**Version:** 2.0  
**Status:** Design Complete — Ready for Development  
**Last Updated:** September 2026

---

## The Core Idea

Build a **universal, embeddable AI assistant agent** that can attach itself to *any* Qt desktop app or web-framework app. It acts like an intelligent co-pilot that:

- **Reads your app's source code** to deeply understand every feature, form, dialog, and workflow
- **Visually guides users on the live UI** — draws overlays, highlights, arrows, and step-by-step pointers *directly on the app window*
- **Proactively helps** — doesn't wait to be asked, recognizes when a user is stuck and acts
- **Scales across any number of apps and users** via a centralized Hub architecture

---

## All Design Decisions — Confirmed ✅

| Decision | Confirmed Choice |
|---|---|
| **Knowledge base source** | App source code (primary) + optional external docs (PDF, HTML, MD, URLs) |
| **App crawling** | Source code parsed at registration time (static) — no runtime crawling needed |
| **UI guidance style** | Visual overlay drawn directly on the live app window |
| **Overlay navigation** | Step-by-step (default) with toggle to all-steps-at-once tour |
| **Steps in chat** | Full step list always shown in chat panel upfront, in both overlay modes |
| **Action execution** | Guide only — agent shows where to click, user performs the action |
| **Screenshot access** | Consent-first — always ask before capturing; discard after use |
| **Private doc access** | Consent-first — always ask; session-only unless user says "remember" |
| **Connectivity model** | AppAI Hub — one central service serving all apps and all users |
| **Local LLM (primary)** | Ollama (easiest setup) + vLLM (for self-hosted GPU deployments) |
| **Cloud LLM (optional)** | OpenAI API + Anthropic Claude API — config toggle, requires explicit consent |
| **Scalability model** | Hub & Spoke — one Hub, isolated per-app KBs, isolated per-user sessions |

---

## Privacy & Consent — Core Principle

> The agent **never silently captures screenshots or reads private documents**.  
> Every sensitive action requires explicit user permission, in plain language, before it happens.

### Screenshot Permission Flow

`
Agent:  "To better understand what you're seeing, may I take a
         screenshot? It will only be used to answer your question
         and won't be stored anywhere."

         [Allow Once]   [Allow for this session]   [No, thanks]
`

- **Allow Once** — captures one frame, used in one LLM prompt, then discarded
- **Allow for session** — no more asking until the app restarts
- **No thanks** — agent works from text description only; never retries without asking

Screenshots are **never saved to disk** and **never sent to any external server**.

### Private Document Permission Flow

`
Agent:  "A user manual or internal doc might help here.
         Would you like to share one? I'll read it locally —
         it won't leave your machine or be stored beyond this session."

         [Choose a file...]   [Not now]
`

- Read and embedded locally into a session-only temporary knowledge base
- Discarded when session ends (unless user explicitly says "remember this doc")

### Consent Config (User-Controlled)

`yaml
# ~/.appai/consent.yaml
screenshot_permission: ask_every_time   # ask_every_time | session | never
doc_access_permission: ask_every_time
clipboard_permission: never
cloud_llm_consent: not_confirmed        # must be explicitly confirmed by admin
`

### Actions That Always Require Consent

| Action | Policy |
|---|---|
| Take a screenshot | ✅ Always ask first |
| Read a file from disk | ✅ Always ask first |
| Access clipboard | ✅ Always ask first |
| Send data to cloud LLM | ✅ Admin warning at setup + explicit confirmation |
| Persist any user data | ✅ Always ask first |

---

## Scalability Architecture — Hub & Spoke Model

> **Key decision:** One sidecar per app does not scale.  
> 10 apps = 10 LLM processes in RAM = wasted resources.  
> The solution is a **single AppAI Hub** that all apps connect to.

### What's Shared vs What's Isolated

| Resource | Shared Across Apps | Isolated |
|---|---|---|
| LLM instance | ✅ One for all apps | — |
| Embedding model | ✅ One for all | — |
| App Knowledge Base | — | ✅ Per app (App1_KB ≠ App2_KB) |
| User conversation | — | ✅ Per (user_id × app_id) |
| Overlay state | — | ✅ Per user session |

### Hub Architecture

`
App1 SDK ──┐
App2 SDK ──┤
App3 SDK ──┤── WebSocket ──▶ ┌─────────────────────────────────┐
...        │                 │          AppAI HUB               │
App10 SDK ─┘                 │                                 │
                             │  App Registry  Session Manager  │
User sessions ──────────────▶│  App1_KB       App2_KB  ...    │
                             │  ONE shared LLM (Ollama/vLLM)  │
                             └─────────────────────────────────┘
`

### Two Deployment Modes (Same SDK — Only hub_url Changes)

#### Mode 1 — Local Hub

`
[One Machine]
  ├── App1.exe ──┐
  ├── App2.exe ──┼── ws://localhost:7788 ──▶ AppAI Hub
  └── App3.exe ──┘                               │
                                    ┌────────────┼────────────┐
                                    ▼            ▼            ▼
                                 Ollama      ChromaDB      SQLite
`

Best for: development, small teams (<10 users), fully offline environments.

#### Mode 2 — Enterprise Server

`
[Machine A]  App1, App2 ──┐
[Machine B]  App3, App5 ──┼── wss://appai.company.local ──▶ Load Balancer
[Machine N]  ...          ┘                                       │
                                           ┌──────────────────────┼─────────┐
                                           ▼           ▼                    ▼
                                     Hub Cluster    vLLM (GPU)    Qdrant + Redis
`

Best for: organizations, 10+ apps, 50+ users.

### Scalability Growth Path

| Stage | Apps | Users | LLM | Vector Store | Session Store |
|---|---|---|---|---|---|
| 1 — Starter | 1–3 | 1–10 | Ollama | ChromaDB | SQLite |
| 2 — Growing | 5–10 | 10–50 | Ollama / vLLM | ChromaDB | Redis |
| 3 — Enterprise | 10–30 | 50–500 | vLLM (GPU) | Qdrant | Redis |
| 4 — Large Scale | 30+ | 500+ | vLLM Cluster | Qdrant Cluster | Redis Cluster |

**The SDK in every app stays identical across all stages.**

### Registering a New App

`ash
appai register \
  --app-name "BillingApp" \
  --source-path ./billing-app/src \
  --docs-path ./billing-app/docs   # optional

# Hub parses source, builds KB, app is ready for all users
`

---

## How the Core Capabilities Work

### A. Source Code as Knowledge Base

Parsed once at registration time. Far richer than runtime crawling — captures all possible states.

| App Type | Files Parsed |
|---|---|
| Qt C++ | .ui, .cpp, .h, .qrc, CMakeLists.txt |
| Qt QML | .qml, .js |
| PyQt / PySide | .py |
| React / Vue | .jsx, .tsx, .vue |
| HTML / Web | .html, .js, route configs |

**Extracted knowledge:**
- Every UI widget with ID, label, tooltip, type, and screen location
- Every menu item, toolbar action, dialog
- Form fields + their validation rules and required state
- Signal → slot connections (what triggers what in Qt)
- Business logic flows (what happens when user does X)
- All error messages and the conditions that cause them
- Navigation paths between screens

**Output:** An AppManifest (SQLite) + vector-embedded knowledge in ChromaDB/Qdrant

---

### B. Visual UI Overlay Guidance System

The agent doesn't just tell users what to do — it **shows them** on the live app window.

#### Qt Implementation

`
QWidget (Overlay Window):
  - Qt::WindowStaysOnTopHint   → always above the app
  - Qt::FramelessWindowHint    → no window border/title
  - WA_TransparentForMouseEvents → clicks pass through to real app
  - QPainter draws: rings, arrows, spotlights, step numbers
`

#### Web Implementation

`
<div> injected at z-index: 99999:
  - CSS clip-path spotlight (dims all except target)
  - Animated border/glow on target elements
  - Floating tooltip bubbles with step text
`

#### Overlay Styles

| Style | Trigger |
|---|---|
| Pulsing Ring | "Click this button" |
| Glowing Box | "Fill in this field" |
| Animated Arrow | "Navigate to this menu" |
| Spotlight | Full focus on one area |
| Drop Zone Indicator | "Drop your file here" |
| Step Number Badge | Multi-step workflows ①②③ |
| Error Pointer | Points to field causing an error |

#### Overlay Protocol (JSON)

`json
{
  "type": "overlay_guide",
  "mode": "step_by_step",
  "steps": [
    {
      "step": 1,
      "target_id": "menuFile",
      "target_type": "qt_widget",
      "style": "pulse_ring",
      "label": "Step 1: Click the File menu",
      "wait_for": "menu_open"
    },
    {
      "step": 2,
      "target_id": "actionExport",
      "target_type": "qt_action",
      "style": "arrow_point",
      "label": "Step 2: Click Export",
      "wait_for": "dialog_open"
    }
  ]
}
`

#### Step Flow

`
1. User asks a question
2. Agent returns: chat message (all steps listed) + overlay_steps JSON
3. Chat panel shows all steps immediately (both modes)
4. Overlay starts on Step 1
5. User performs action → SDK detects it → advances to Step 2
6. Repeats until all steps done → ✅ confirmation shown
`

---

## Full System Architecture

`
┌───────────────────────────────────────────────────────────────────┐
│                        HOST APPLICATION                            │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  VISUAL OVERLAY LAYER (Transparent — clicks pass through)   │  │
│  │  ● Pulsing rings  ➜ Arrows  ■ Spotlights  ⬚ Drop zones    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────┐   ┌────────────────────────────────┐    │
│  │   HOST APP CODE       │   │  CHAT PANEL (SDK-rendered)     │    │
│  │  Qt Widgets / React  │◀─▶│  • All steps shown upfront     │    │
│  │  Vue / Any framework │   │  • Step-by-step or tour mode   │    │
│  └──────────────────────┘   │  • Proactive hint bubbles      │    │
│                              └────────────────────────────────┘    │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  AppAI SDK (thin — ~300 lines per platform)                  │  │
│  │  • WebSocket client    • Consent manager                     │  │
│  │  • UI event stream     • Widget ID → coordinate resolver     │  │
│  │  • Overlay renderer    • Screenshot capture (on consent)     │  │
│  └───────────────────────────────┬─────────────────────────────┘  │
└───────────────────────────────────┼────────────────────────────────┘
                                    │ WebSocket
                                    ▼
┌───────────────────────────────────────────────────────────────────┐
│                         AppAI HUB                                  │
│                                                                    │
│  ┌──────────────┐  ┌────────────────┐  ┌───────────────────────┐  │
│  │ App Registry │  │ Session Manager│  │  Proactive Engine     │  │
│  └──────────────┘  └────────────────┘  └───────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  AGENT CORE                                                  │  │
│  │  Query Processor → Overlay Planner → Response Builder        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  KNOWLEDGE BASE ENGINE                                       │  │
│  │  Source Code Parser → App Manifest → Vector Store (RAG)      │  │
│  │  Doc Ingestion (on consent) → Session-only KB                │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  LLM ROUTER (config-driven)                                  │  │
│  │  Ollama (local) │ vLLM (self-hosted) │ OpenAI │ Claude       │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
`

---

## Proactive Trigger Rules

| User Situation | Agent Action |
|---|---|
| Idle on a form > 10s | "Looks like you're filling the Invoice form. Need help?" |
| Hover over a disabled button | "This button is disabled because the Name field is empty" |
| Drag a file near the app | Instantly shows drop zone indicator overlay |
| Validation error visible | Arrow points to the problematic field + explains why |
| Complex screen, first visit | "This is the Report Builder. Want a quick orientation?" |
| Same error repeated twice | "Would you like me to walk you through this step by step?" |

---

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Hub Framework | Python 3.11+ / FastAPI / asyncio | Best for AI/ML ecosystem |
| LLM Orchestration | LangChain | RAG pipeline, prompt management, LLM abstraction |
| Source Code Parser | Tree-sitter (AST) | Multi-language: C++, Python, JS, QML, Vue |
| Vector Store (local) | ChromaDB | Zero-config, local files |
| Vector Store (enterprise) | Qdrant | Distributed, clusterable |
| Session Store (local) | In-memory Python dict | Simple, no deps |
| Session Store (enterprise) | Redis | Scalable, cross-instance |
| Structured Store | SQLite (local) / PostgreSQL (enterprise) | App Manifest storage |
| Local LLM | Ollama (primary) | Llama3, Mistral, Qwen, Phi |
| Self-hosted LLM | vLLM | GPU-optimized, high concurrency |
| Cloud LLM (opt-in) | OpenAI API / Anthropic Claude | Requires explicit consent |
| Embeddings | nomic-embed-text via Ollama | 100% local |
| Qt SDK | C++ (QWidget overlay + WS client) | |
| Web SDK | JavaScript (div overlay + WS client) | |
| Communication | WebSocket / WSS (JSON protocol) | |
| Config | YAML | One file to switch everything |
| Auth (enterprise) | JWT + API keys | |

---

## Phased Development Roadmap

### Phase 1 — Core Foundation (Weeks 1–4)
- [ ] AppAI Hub skeleton (FastAPI + WebSocket server)
- [ ] App Registry + Session Manager
- [ ] LLM Router (Ollama + OpenAI + Claude)
- [ ] Qt SDK: WebSocket client + basic chat panel
- [ ] End-to-end: user asks question, gets answer from one test app

### Phase 2 — Source Code Intelligence (Weeks 5–8)
- [ ] Source code parser: Qt (.ui, .qml, .cpp, .py)
- [ ] Source code parser: Web (.jsx, .tsx, .vue, .html)
- [ ] App Manifest builder + SQLite storage
- [ ] RAG pipeline (LangChain + ChromaDB)
- [ ] External doc ingestion (PDF, HTML, Markdown, URLs)
- [ ] Incremental re-parsing on code update

### Phase 3 — Visual Overlay System (Weeks 9–12)
- [ ] Qt transparent overlay window (QWidget-based)
- [ ] Overlay styles: pulse ring, arrow, spotlight, drop zone, step badge, error pointer
- [ ] Overlay Planner: widget name → QAccessible coordinate resolution
- [ ] Step-by-step advance logic: detect user action → move to next step
- [ ] All-steps-at-once tour mode (toggle)
- [ ] Web JavaScript overlay (div + CSS animations)
- [ ] Overlay ↔ Chat panel sync: all steps shown in chat at query time

### Phase 4 — Proactive Intelligence (Weeks 13–16)
- [ ] Live context tracker (current screen, idle time, error state)
- [ ] Proactive trigger rule engine
- [ ] Non-intrusive hint bubble UI in chat panel
- [ ] Drag-file detection + instant drop zone overlay
- [ ] User preference: disable / configure proactive hints

### Phase 5 — Enterprise & Scalability (Weeks 17–20)
- [ ] vLLM integration + GPU server setup guide
- [ ] Enterprise auth (JWT + API keys)
- [ ] Qdrant integration (replaces ChromaDB)
- [ ] Redis session store (replaces in-memory)
- [ ] Admin CLI: register apps, view status, manage users
- [ ] Load testing + performance tuning
- [ ] Deployment runbook (local and enterprise modes)
