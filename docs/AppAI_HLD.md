# AppAI — High-Level Design (HLD)

**Version:** 1.0  
**Status:** Under Review  
**Date:** September 2026

---

## 1. Executive Summary

AppAI is a **universal, proactive AI assistant platform** that embeds into any Qt desktop or web-framework application. It understands an application's structure by parsing its source code, builds an isolated knowledge base per app, and provides real-time AI-powered guidance to end users — including **visual overlay guidance** that highlights exactly where to click, fill, or drop files on the live application UI.

The system is **privacy-first** (local LLM by default), **consent-driven** (never captures screenshots or reads docs without asking), and **infinitely scalable** via a centralized Hub architecture that serves any number of apps and users from a single deployment.

---

## 2. System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL WORLD                                    │
│                                                                              │
│   Developers               End Users              Admins                    │
│  (register apps,          (use apps with         (configure Hub,            │
│   provide source code)     AI assistance)         manage apps/users)        │
└──────────────┬─────────────────────┬──────────────────────┬─────────────────┘
               │                     │                      │
               ▼                     ▼                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              AppAI PLATFORM                                  │
│                                                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────────────┐ │
│   │  Qt App  │  │  Qt App  │  │  Web App │  │   AppAI Admin Dashboard    │ │
│   │  + SDK   │  │  + SDK   │  │  + SDK   │  │   (register, monitor, cfg) │ │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────────────────────────┘ │
│        └─────────────┴─────────────┘                                        │
│                         │ WebSocket / WSS                                    │
│                         ▼                                                    │
│              ┌───────────────────────┐                                       │
│              │      AppAI HUB        │  ← Core of the platform               │
│              └───────────────────────┘                                       │
│                         │                                                    │
│          ┌──────────────┼──────────────┐                                     │
│          ▼              ▼              ▼                                     │
│     Knowledge       LLM Backend    Session &                                 │
│       Store        (Local/Cloud)   Auth Store                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Architecture — Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HOST APPLICATION                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   VISUAL OVERLAY ENGINE (SDK)                        │    │
│  │   [Pulsing Ring] [Arrow Pointer] [Spotlight] [Drop Zone] [Step #]   │    │
│  │   Transparent QWidget (Qt) / Injected <div> (Web) — always on top   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────┐   ┌─────────────────────────────────┐     │
│  │        HOST APP CODE          │   │    CHAT PANEL (SDK-rendered)    │     │
│  │  (Qt Widgets / React / Vue)   │◀─▶│    [Ask me anything...]        │     │
│  │                               │   │    [Step list in chat]         │     │
│  └──────────────────────────────┘   └─────────────────────────────────┘     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        AppAI SDK (Thin Layer)                        │    │
│  │  • WebSocket Client        • Consent Manager                         │    │
│  │  • UI Event Stream         • Widget ID → Screen Coordinate Resolver  │    │
│  │  • Overlay Renderer        • Screenshot Capture (on consent)         │    │
│  └───────────────────────────────────────┬─────────────────────────────┘    │
└──────────────────────────────────────────┼──────────────────────────────────┘
                                           │
                            WebSocket / WSS (JSON protocol)
                                           │
┌──────────────────────────────────────────▼──────────────────────────────────┐
│                              AppAI HUB                                       │
│                                                                              │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │  WebSocket      │  │  App Registry    │  │  Session Manager         │   │
│  │  Server         │  │                  │  │                          │   │
│  │  (FastAPI /     │  │  • app_id        │  │  session_id              │   │
│  │   asyncio)      │  │  • app_name      │  │  = (user_id + app_id)   │   │
│  │                 │  │  • kb_collection │  │  • conversation history  │   │
│  │  Routes each    │  │  • source_path   │  │  • current screen ctx   │   │
│  │  connection to  │  │  • manifest_path │  │  • proactive state      │   │
│  │  right session  │  └──────────────────┘  └──────────────────────────┘   │
│  └─────────────────┘                                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         AGENT CORE                                   │    │
│  │                                                                      │    │
│  │  ┌───────────────┐  ┌────────────────┐  ┌────────────────────────┐  │    │
│  │  │  Proactive    │  │  Query         │  │  Overlay Planner       │  │    │
│  │  │  Engine       │  │  Processor     │  │                        │  │    │
│  │  │               │  │                │  │  Converts LLM answer   │  │    │
│  │  │  Watches live │  │  RAG retrieve  │  │  into structured       │  │    │
│  │  │  context,     │  │  → LLM prompt  │  │  overlay steps with    │  │    │
│  │  │  fires hints  │  │  → response    │  │  target widget IDs     │  │    │
│  │  └───────────────┘  └────────────────┘  └────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    KNOWLEDGE BASE ENGINE                             │    │
│  │                                                                      │    │
│  │  ┌───────────────────────┐    ┌──────────────────────────────────┐  │    │
│  │  │  Source Code Parser   │    │  Vector Store                    │  │    │
│  │  │  (Tree-sitter AST)    │───▶│  ChromaDB (local)                │  │    │
│  │  │                       │    │  Qdrant (enterprise)             │  │    │
│  │  │  .ui / .qml / .cpp    │    │                                  │  │    │
│  │  │  .py / .jsx / .vue    │    │  Collection per app:             │  │    │
│  │  │  .html / routes       │    │  appai::app1::kb                 │  │    │
│  │  └───────────────────────┘    │  appai::app2::kb ...             │  │    │
│  │                               └──────────────────────────────────┘  │    │
│  │  ┌───────────────────────┐    ┌──────────────────────────────────┐  │    │
│  │  │  Doc Ingestion        │    │  App Manifest Store              │  │    │
│  │  │  (PDF/HTML/MD/URLs)   │───▶│  SQLite — per app:              │  │    │
│  │  │  [on user consent]    │    │  widgets, routes, actions,       │  │    │
│  │  └───────────────────────┘    │  widget_id → UI coordinates      │  │    │
│  │                               └──────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         LLM ROUTER                                   │    │
│  │                                                                      │    │
│  │      config: provider = ollama | vllm | openai | anthropic          │    │
│  │                                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐  │    │
│  │  │    Ollama    │  │    vLLM      │  │  OpenAI    │  │ Anthropic│  │    │
│  │  │  (localhost) │  │ (GPU server) │  │  API       │  │ Claude   │  │    │
│  │  │  Llama3      │  │  any model   │  │  GPT-4o    │  │ Sonnet   │  │    │
│  │  │  Mistral     │  │  (self-host) │  │            │  │          │  │    │
│  │  │  Qwen / Phi  │  │              │  │            │  │          │  │    │
│  │  └──────────────┘  └──────────────┘  └────────────┘  └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Descriptions

### 4.1 AppAI SDK (Client-Side, Embedded in Host App)

The **only code that touches the host application**. Intentionally thin (~300–500 lines).

| Sub-component | Responsibility |
|---|---|
| WebSocket Client | Connects to AppAI Hub, sends/receives JSON messages |
| UI Event Stream | Publishes widget focus changes, navigation, user actions |
| Widget Resolver | Maps widget IDs/names → live screen coordinates (via QAccessible / DOM) |
| Overlay Renderer | Draws transparent highlight windows on top of the app (Qt: QWidget, Web: div) |
| Chat Panel | Renders the assistant conversation UI (embedded sidebar or floating window) |
| Consent Manager | Intercepts any sensitive action (screenshot, file read) and shows consent dialog |
| Screenshot Capture | Takes a single screenshot only after explicit user approval |

---

### 4.2 AppAI Hub

The **brain and central orchestrator** of the platform. Runs as a standalone service.

| Sub-component | Responsibility |
|---|---|
| WebSocket Server | Accepts connections from all app SDKs; handles multiplexing |
| App Registry | Stores metadata for every registered app (name, source path, KB collection ID) |
| Session Manager | Maintains one session per `(user_id, app_id)` — conversation history, current screen context, proactive state |
| Agent Core | Orchestrates the full query pipeline: retrieve → augment → generate → respond |
| Query Processor | Builds the final LLM prompt (user query + KB chunks + live context + conversation history) |
| Overlay Planner | Parses LLM response to extract step-by-step UI guidance; maps natural language locations to widget IDs |
| Proactive Engine | Monitors live context events; fires proactive hints based on trigger rules (idle, error, drag, first visit) |
| LLM Router | Abstracts all LLM backends behind a single interface; switches based on config |

---

### 4.3 Knowledge Base Engine

Runs inside the Hub. Builds and serves per-app knowledge.

| Sub-component | Responsibility |
|---|---|
| Source Code Parser | AST-based parser (Tree-sitter) for Qt (.ui, .qml, .cpp, .h, .py) and Web (.jsx, .tsx, .vue, .html) |
| App Manifest Builder | Extracts: widget tree, menus, dialogs, routes, forms, signals/slots, error messages, workflows |
| Doc Ingestion Pipeline | Processes PDFs, HTML pages, Markdown files, and URLs into text chunks (on user consent) |
| Embedding Engine | Converts text chunks to vector embeddings (local: nomic-embed-text via Ollama; cloud: text-embedding-3) |
| Vector Store | ChromaDB (local/small-scale) or Qdrant (enterprise). One collection per app |
| App Manifest Store | SQLite database. Stores structured app metadata including widget ID ↔ coordinate mappings |
| Retriever | Hybrid search: vector similarity + BM25 keyword; enriched with current app context |

---

### 4.4 LLM Router

Config-driven abstraction over all supported LLM backends.

```yaml
# appai.config.yaml
llm:
  provider: ollama          # ollama | vllm | openai | anthropic
  model: llama3.1:8b
  base_url: http://localhost:11434
  # For vLLM:
  # provider: vllm
  # base_url: http://gpu-server:8000
  # model: mistral-7b-instruct
  # For OpenAI/Claude:
  # api_key: sk-...
```

---

### 4.5 Visual Overlay Engine

Renders **real-time visual guidance** directly on the host app window.

| Overlay Style | Use Case |
|---|---|
| Pulsing Ring | "Click this button" |
| Glowing Box | "Fill in this form field" |
| Animated Arrow | "Navigate to this menu" |
| Spotlight | Dims all except target area — deep focus |
| Drop Zone Indicator | Animated dashed border — "Drop your file here" |
| Step Number Badge | Multi-step workflows with numbered sequence |
| Error Pointer | Points to the field/area causing an error |

Steps are presented in two modes (user toggleable):
- **Step-by-step** (default): One highlight at a time, advances when user acts
- **All-at-once tour**: All steps numbered and visible simultaneously

All steps are **also listed in the chat panel** upfront so users can read ahead.

---

## 5. Data Flows

### 5.1 App Registration Flow (One-Time Setup)

```
Developer
   │
   │  appai register --app-name "InvoiceApp" --source ./src --docs ./docs
   ▼
AppAI Hub — Registration Handler
   │
   ├─▶ Source Code Parser
   │       │  Parses .ui, .qml, .cpp, .py / .jsx, .vue, .html
   │       ▼
   │   App Manifest (widgets, routes, actions, forms, error msgs, workflows)
   │       │
   │       ├─▶ SQLite (structured manifest + widget coordinates)
   │       └─▶ Embedding Engine ──▶ Vector Store (ChromaDB/Qdrant)
   │
   ├─▶ Doc Ingestion Pipeline (if --docs provided)
   │       │  PDF/HTML/MD chunked + embedded
   │       └─▶ Vector Store (same collection as app KB)
   │
   └─▶ App Registry
           Stores: { app_id, app_name, collection_id, manifest_path }

Result: InvoiceApp is ready. All users can now get AI assistance for it.
```

---

### 5.2 User Query Flow (Real-Time Assistance)

```
User types: "How do I export a report as PDF?"
   │
   ▼
AppAI SDK (in App)
   │  Sends: { type: "query", app_id: "invoiceapp", user_id: "alice",
   │           text: "How do I export a report as PDF?",
   │           context: { current_screen: "Dashboard", last_actions: [...] } }
   ▼
AppAI Hub — WebSocket Server
   │
   ▼
Session Manager
   │  Loads: Alice × InvoiceApp session (conversation history, screen context)
   ▼
Agent Core — Query Processor
   │
   ├─▶ Retriever
   │       Query: "export report PDF" + context: "user is on Dashboard"
   │       → Hybrid search on InvoiceApp KB
   │       → Returns top-K relevant chunks:
   │         ["File > Export > Report dialog...", "ExportDialog accepts PDF/Excel...",
   │          "exportButton widget at toolbar position...", ...]
   │
   ├─▶ LLM Prompt Builder
   │       System: "You are AppAI assistant for InvoiceApp. Guide the user step by step."
   │       Context: [KB chunks] + [conversation history] + [current screen: Dashboard]
   │       User: "How do I export a report as PDF?"
   │
   ├─▶ LLM Router → Ollama (llama3.1:8b)
   │       Response: Step-by-step answer + widget IDs for each step
   │
   └─▶ Overlay Planner
           Parses response → structured overlay steps:
           Step 1: target=menuFile, style=pulse_ring, label="Click File"
           Step 2: target=actionExport, style=arrow_point, label="Click Export"
           Step 3: target=dialogExport.pdfRadio, style=highlight_box, label="Select PDF"
           Step 4: target=dialogExport.btnOk, style=pulse_ring, label="Click Export"
   │
   ▼
Hub sends back:
   { type: "response",
     chat_message: "Here's how to export a report as PDF:\n1. Click File...\n2. ...",
     overlay_steps: [ {step:1, target_id:..., style:..., label:...}, ... ],
     overlay_mode: "step_by_step"   ← user can toggle to "all_at_once"
   }
   │
   ▼
AppAI SDK (in App)
   ├─▶ Chat Panel: Shows full step list as chat message
   └─▶ Overlay Renderer: Starts step-by-step overlay on App window
           → Waits for user to act → advances to next step → ✅ done
```

---

### 5.3 Proactive Trigger Flow

```
AppAI SDK streams live context every N seconds:
   { type: "context_update", screen: "InvoiceForm",
     idle_ms: 12000, last_action: "focused on customerName field",
     visible_errors: ["addressField: required"] }
   │
   ▼
Proactive Engine evaluates trigger rules:
   Rule: idle > 10s AND form has visible errors → fire hint

   ▼
Hub generates proactive message:
   "I noticed the Address field is required and empty.
    Would you like me to show you where to find the customer's address?"

   ▼
SDK shows non-intrusive hint bubble (bottom of chat panel)
User can: [Yes, show me] or [Not now] or [Dismiss]
```

---

### 5.4 Screenshot Consent Flow

```
Agent determines screenshot would help diagnose user's problem
   │
   ▼
Hub sends:
   { type: "consent_request", action: "screenshot",
     reason: "To see the exact error on your screen" }
   │
   ▼
SDK shows consent dialog:
   "May I take a screenshot to better help you?
    It stays on your machine and won't be stored."
   [Allow Once] [Allow for session] [No thanks]
   │
   ├── User allows → SDK captures screenshot → sends to Hub (base64)
   │       Hub passes to LLM for visual analysis → responds
   │       Screenshot discarded after response
   │
   └── User declines → Hub proceeds without screenshot
           Agent asks user to describe what they see instead
```

---

### 5.5 Private Doc Ingestion Flow

```
Agent thinks a private doc might help
   │
   ▼
Hub sends:
   { type: "consent_request", action: "doc_access",
     reason: "A user manual might have info about this feature" }
   │
   ▼
SDK shows consent dialog:
   "Would you like to share a document? I'll read it locally."
   [Choose file...] [Not now]
   │
   ├── User selects file → SDK reads file → sends content to Hub
   │       Hub chunks + embeds into session-temporary KB
   │       Used for current session only → discarded at session end
   │       (Unless user says "remember this" → added to app's persistent KB)
   │
   └── User declines → Hub proceeds with existing KB only
```

---

## 6. Deployment Modes

### Mode 1 — Local Hub (Small Team / Single Machine)

```
[Single Machine]
 ├── Qt App 1 (SDK) ──┐
 ├── Qt App 2 (SDK) ──┤
 ├── Web App 1 (SDK) ─┼──── ws://localhost:7788 ────▶ AppAI Hub
 └── Qt App N (SDK) ──┘                                    │
                                                ┌──────────┴──────────┐
                                                ▼                     ▼
                                           Ollama                 ChromaDB
                                        (localhost:11434)        (local files)
                                        Llama3 / Mistral         SQLite manifest
```

**Best for:** Development, small teams (< 10 users), offline environments

---

### Mode 2 — Enterprise Server (Multi-User / Multi-App)

```
[Machine A]  App1, App2 ──┐
[Machine B]  App3, App7 ──┤
[Machine C]  App1, App5 ──┼── wss://appai.company.local ──▶ Load Balancer
[Machine N]  ...          ┘                                      │
                                              ┌──────────────────┼────────────────┐
                                              ▼                  ▼                ▼
                                        Hub Instance 1    Hub Instance 2    Hub Instance N
                                              │
                                   ┌──────────┼────────────┐
                                   ▼          ▼            ▼
                                vLLM       Qdrant        Redis
                              (GPU node)  (vector DB)  (sessions)
```

**Best for:** Organizations, 10+ apps, 50+ users, production deployments

---

### Scalability Path

| Stage | Apps | Users | LLM | Vector Store | Session Store |
|---|---|---|---|---|---|
| 1 — Local | 1–3 | 1–5 | Ollama | ChromaDB | SQLite |
| 2 — Small Server | 5–10 | 10–50 | Ollama / vLLM | ChromaDB | SQLite / Redis |
| 3 — Enterprise | 10–30 | 50–500 | vLLM (GPU) | Qdrant | Redis |
| 4 — Large Scale | 30+ | 500+ | vLLM Cluster | Qdrant Cluster | Redis Cluster |

**The SDK in every app stays identical across all stages.**

---

## 7. Technology Stack

| Layer | Local Mode | Enterprise Mode |
|---|---|---|
| Hub Framework | Python + FastAPI + asyncio | Same |
| WebSocket | `websockets` / FastAPI WebSocket | Same + Nginx/Caddy WSS termination |
| LLM | Ollama (Llama3, Mistral, Qwen) | vLLM (any model, GPU-accelerated) |
| Cloud LLM (optional) | OpenAI API / Anthropic Claude | Same |
| LLM Orchestration | LangChain | Same |
| Embeddings | nomic-embed-text (Ollama) | nomic or text-embedding-3 (OpenAI) |
| Vector Store | ChromaDB | Qdrant |
| Structured Store | SQLite | PostgreSQL |
| Session Store | In-memory (Python dict) | Redis |
| Source Parser | Tree-sitter (multi-language AST) | Same |
| Qt SDK | C++ (QWidget overlay + WS client) | Same |
| Web SDK | JavaScript (div overlay + WS client) | Same |
| Load Balancer | — | Nginx / HAProxy |
| Config | YAML | YAML + env vars |
| Auth | App API Key (simple) | JWT + RBAC |

---

## 8. Security & Privacy Model

### Data Residency
- **Local Mode**: All data (source code, embeddings, conversations) stays on the machine. Zero network egress.
- **Enterprise Mode**: Data stays within the private network/server. Only moves to cloud if OpenAI/Claude backend is explicitly configured.

### Consent Gates (Non-Negotiable)
Every sensitive action requires explicit user consent before execution:

| Action | Gate |
|---|---|
| Screenshot capture | In-app consent dialog, every time (or session permission) |
| Private file read | In-app consent dialog with file picker |
| Clipboard access | In-app consent dialog |
| Sending data to cloud LLM | One-time warning at setup + config confirmation |
| Persistent storage of session data | Explicit "remember this" trigger by user |

### App Isolation
- Each app's knowledge base is a separate collection in the vector store
- Cross-app queries are not possible by design
- Session data for `(user_id, app_id)` is completely isolated from other pairs

### Authentication
- **Local Mode**: Hub listens on localhost only; no auth needed
- **Enterprise Mode**: Each app SDK uses an API key to authenticate with the Hub; users identified by user_id passed from the host app's own auth system

---

## 9. Key Design Principles

| Principle | Implementation |
|---|---|
| **Privacy-first** | Local LLM + local vector store by default; cloud is opt-in |
| **Consent-first** | Every sensitive action gated behind an explicit user approval dialog |
| **App-isolated** | Each app's KB, sessions, and overlays are completely independent |
| **Zero-friction integration** | Apps only add a thin SDK (WebSocket client + overlay renderer) |
| **Guide-only** | Agent shows where to act; never clicks or fills on behalf of user |
| **Horizontally scalable** | Same Hub codebase scales from 1 app to 100 apps by upgrading infra |
| **Backend-agnostic** | One YAML line to switch between Ollama, vLLM, OpenAI, or Claude |
| **Incrementally adoptable** | Start local, migrate to enterprise server when needed; SDK never changes |

---

## 10. Component Responsibility Matrix

| Component | Who Builds | Language | Deployed On |
|---|---|---|---|
| AppAI Hub | Core team | Python | Server / localhost |
| LLM Router | Core team | Python | Inside Hub |
| Knowledge Base Engine | Core team | Python | Inside Hub |
| Source Code Parser | Core team | Python (Tree-sitter) | Inside Hub |
| Proactive Engine | Core team | Python | Inside Hub |
| Overlay Planner | Core team | Python | Inside Hub |
| Qt SDK | Core team | C++ | Compiled into Qt app |
| Web SDK | Core team | JavaScript | Bundled with web app |
| Ollama | Third-party | — | localhost |
| vLLM | Third-party | — | GPU Server |
| ChromaDB / Qdrant | Third-party | — | localhost / Server |
| Redis | Third-party | — | Server |

---

## 11. Open Items / Future Considerations

| Item | Priority | Notes |
|---|---|---|
| Multi-language UI | Medium | Overlay labels & chat in user's language |
| Voice input to agent | Low | Speech-to-text → existing query pipeline |
| App update detection | High | Re-parse source code when app version changes, update KB |
| User feedback loop | Medium | "Was this helpful?" → fine-tune proactive triggers |
| Analytics dashboard | Low | Admin view: which features users ask about most |
| Offline embedding model | High | nomic-embed-text via Ollama — fully offline |
| Plugin system | Low | Allow custom proactive trigger rules per app |
