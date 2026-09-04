# AppAI — Intelligent Proactive App Assistant: System Design

> **Status**: Design Discussion Phase — Awaiting Feedback Before Development

---

## The Core Idea

Build a **universal, embeddable AI assistant agent** that can attach itself to *any* Qt desktop app or web-framework app. It acts like an intelligent co-pilot that:

- **Reads your app's source code** to deeply understand every feature, form, dialog, and workflow
- **Visually guides users on the live UI** — draws overlays, highlights, arrows, and step-by-step pointers *directly on the app window*
- **Proactively helps** — doesn't wait to be asked, recognizes when a user is stuck and acts

> **Confirmed design decisions so far:**
> - ✅ App source code will be provided as the primary knowledge base
> - ✅ Visual UI overlay guidance is required (show where to click, drop, etc.)
> - ✅ Local LLM first (privacy), with OpenAI/Claude as switchable backends
> - ✅ **Consent-first**: Agent must always ask before taking a screenshot or accessing any private document

---

## Privacy & Consent — Core Principle

> [!IMPORTANT]
> The agent **never silently captures screenshots or reads private documents**. Every such action requires explicit user permission, asked in plain language, before it happens.

### Screenshot Permission Flow

When the agent determines a screenshot would help it understand the user's current problem:

```
Agent:  "To better understand what you're seeing, may I take a
         screenshot of the current screen? It will only be used
         to answer your question and won't be stored anywhere."

         [Allow Once]   [Allow for this session]   [No, thanks]
```

- **Allow Once** — takes one screenshot, then asks again next time
- **Allow for this session** — no more asking until app restarts
- **No thanks** — agent works from text description only, no screenshot

Screenshots are **never saved to disk** and **never sent to any server**. Used only in the current LLM reasoning context, then discarded.

### Private Document Permission Flow

When the agent thinks a private doc would help answer a question:

```
Agent:  "I think a user manual or internal doc might help here.
         Would you like to share one with me? I'll read it locally —
         it won't leave your machine or be stored beyond this session."

         [Choose a file...]   [Not now]
```

- Document is read and embedded locally into a **session-only** temporary knowledge base
- Discarded when session ends (unless user explicitly says "remember this doc")

### Permissions the Agent Will NEVER Act On Without Asking

| Action | Policy |
|---|---|
| Take a screenshot | ✅ Always ask first |
| Read a file from disk | ✅ Always ask first |
| Access clipboard | ✅ Always ask first |
| Send data to cloud LLM (OpenAI/Claude) | ✅ Warn at setup + require confirmation |
| Store any user data persistently | ✅ Always ask first |

### Consent Config (User-Controlled)

```yaml
# ~/.appai/consent.yaml
screenshot_permission: ask_every_time   # ask_every_time | session | never
doc_access_permission: ask_every_time
clipboard_permission: never
cloud_llm_consent: confirmed            # set only after user explicitly approves
```

---

## All Design Decisions — Confirmed ✅

| Decision | Choice |
|---|---|
| Knowledge base source | App source code (primary) + optional external docs |
| UI guidance style | Visual overlay on live app window |
| Overlay navigation | **Step-by-step** (default) with option to switch to **all-steps-at-once** tour |
| All steps visible in chat | ✅ Yes — full step list always shown in chat panel upfront |
| Action execution | **Guide only** — agent shows where to click, user does the clicking |
| Screenshot/doc access | **Consent-first** — always ask before capturing or reading |
| Local LLM | **Ollama** (primary) + **vLLM** (for self-hosted/deployed AI servers) |
| Cloud LLM fallback | OpenAI API + Anthropic Claude API (config toggle) |
| Connectivity model | **AppAI Hub** (centralized, serves all apps + all users — see below) |

---

## Scalability Architecture — Hub & Spoke Model

> [!IMPORTANT]
> **Key insight**: Running one sidecar per app doesn't scale. 10 apps = 10 processes = wasted resources and no shared intelligence. The right approach is a **single AppAI Hub** that all apps connect to.

### The Problem With "One Sidecar Per App"

```
❌ Bad — doesn't scale:

App1 ──▶ Agent Process 1 (own LLM, own KB)
App2 ──▶ Agent Process 2 (own LLM, own KB)
App3 ──▶ Agent Process 3 (own LLM, own KB)
...
App10 ▶ Agent Process 10 (own LLM, own KB)

= 10 LLM instances loaded in RAM 😱
= Knowledge bases cannot share anything
= User sessions isolated in wrong places
```

### ✅ The Right Approach — AppAI Hub

```
App1 SDK ──┐
App2 SDK ──┤
App3 SDK ──┤                ┌─────────────────────────────────┐
App4 SDK ──┼── WebSocket ──▶│         AppAI HUB               │
App5 SDK ──┤                │                                 │
...        │                │  ┌─────────────────────────┐   │
App10 SDK ─┘                │  │    App Registry         │   │
                            │  │  App1_KB  App2_KB ...   │   │
User sessions ─────────────▶│  │    (isolated per app)   │   │
(any user, any app)         │  └─────────────────────────┘   │
                            │                                 │
                            │  ┌─────────────────────────┐   │
                            │  │   Session Manager       │   │
                            │  │  (1 session/user/app)   │   │
                            │  └─────────────────────────┘   │
                            │                                 │
                            │  ┌─────────────────────────┐   │
                            │  │   ONE Shared LLM        │   │
                            │  │   (Ollama / vLLM)       │   │
                            │  └─────────────────────────┘   │
                            └─────────────────────────────────┘
```

**What's shared:** LLM instance, embedding model, infrastructure
**What's isolated:** Per-app knowledge base, per-user conversation session

---

### Two Deployment Modes

The Hub design supports two modes — same SDK, just change `hub_url` in config:

#### Mode 1 — Local Hub (Small Teams / Developer Setup)

```
[User's Machine]
  ├── App1.exe  ──┐
  ├── App2.exe  ──┤── WebSocket ──▶  AppAI Hub (localhost:7788)
  ├── App3.exe  ──┘                     │
  │                                     ├── Ollama (localhost:11434)
  │                                     ├── ChromaDB (local files)
  │                                     └── SQLite (app manifests)
```

- All 10 apps connect to the **same local Hub** on `localhost`
- One Ollama instance shared — only one LLM loaded in RAM
- One knowledge base per app, all stored locally
- Works fully offline — zero cloud dependency

#### Mode 2 — Enterprise Server (Many Users + Many Apps)

```
[User Machine 1]  App1, App2 ──┐
[User Machine 2]  App3, App5 ──┤
[User Machine 3]  App1, App7 ──┼── HTTPS/WSS ──▶  AppAI Server
[User Machine N]  ...          ┘                       │
                                          ┌────────────┴─────────────┐
                                          │   AppAI Hub Cluster      │
                                          │  (multiple Hub instances) │
                                          │   + Load Balancer        │
                                          └────────────┬─────────────┘
                                                       │
                                       ┌───────────────┼───────────────┐
                                       ▼               ▼               ▼
                                  vLLM Server    Qdrant DB       Redis
                                  (GPU node)   (vector store)  (sessions)
```

- Hub runs on a **central server** (on-premise or private cloud)
- vLLM on GPU server handles concurrent users efficiently
- Qdrant replaces ChromaDB for distributed vector storage
- Redis handles session state across Hub instances
- All apps across all users connect to the same server

---

### How the Hub Handles 10 Apps × N Users

```
Hub receives: WebSocket connection from App3, User Alice
  → looks up App3 in App Registry
  → loads App3_KnowledgeBase context
  → creates/resumes session: {app: App3, user: Alice}
  → routes LLM query with App3 KB + Alice's conversation history

Hub receives: WebSocket connection from App1, User Bob
  → looks up App1 in App Registry
  → loads App1_KnowledgeBase context
  → creates/resumes session: {app: App1, user: Bob}
  → routes LLM query with App1 KB + Bob's conversation history
  (Alice's session is completely separate)
```

**Knowledge Base isolation:** Each app's KB is a separate ChromaDB/Qdrant collection — `appai::app1::kb`, `appai::app2::kb`, etc. They never mix.

**Session isolation:** Each `(user_id, app_id)` pair is a separate session. Alice using App3 cannot see Bob using App3.

---

### Scalability Growth Path

```
Stage 1:  1-3 apps, 1-5 users     → Local Hub, Ollama, SQLite
Stage 2:  5-10 apps, 10-50 users  → Local Hub or small server, Ollama/vLLM, ChromaDB
Stage 3:  10+ apps, 50+ users     → Hub Cluster, vLLM on GPU, Qdrant, Redis
Stage 4:  Enterprise              → Multi-region Hubs, HA setup, monitoring
```

Each stage uses the **same SDK in the apps** — only the Hub deployment changes.

---

### Adding a New App — Zero Friction

```bash
# Register new app with the Hub (one-time setup)
appai register \
  --app-name "BillingApp" \
  --source-path ./billing-app/src \
  --docs-path ./billing-app/docs

# Hub auto-parses source, builds KB, makes it available
# All users of BillingApp can now get AI assistance
```

The app itself only needs the **thin AppAI SDK** added — no other changes.

## How the Two New Capabilities Work

### A. Source Code as Knowledge Base

Rather than only crawling the running app at runtime, we **parse the app's source code at setup time** to build a far richer understanding.

**What gets parsed:**

| App Type | Files Analyzed |
|---|---|
| Qt C++ | `.ui` (widget layouts), `.cpp/.h` (logic, signals/slots), `.qrc` (resources), `CMakeLists.txt` |
| Qt/QML | `.qml` (component tree, bindings, states), `.js` (logic) |
| PyQt/PySide | `.py` (widget setup, event handlers) |
| React/Vue | `.jsx/.tsx/.vue` (components, props, routes) |
| HTML/Web | `.html`, `.js`, route configs |

**What the parser extracts:**
- All UI widgets/components with their IDs, labels, tooltips
- Every menu item, toolbar button, dialog
- Form fields + their validation rules
- Signal→slot connections (what triggers what)
- Business logic flows (what happens when user does X)
- Error messages and their causes
- Feature names and their locations in the UI hierarchy

**Result:** A rich `AppKnowledgeBase` — far superior to runtime crawling alone, because it captures *all* possible states, not just what's currently visible.

---

### B. Visual UI Overlay Guidance System

This is the feature that makes AppAI feel like a **human is sitting next to the user pointing at the screen**.

#### How it works (Qt Apps):

```
User asks: "How do I export a report as PDF?"
                    │
                    ▼
     Agent looks up source code knowledge:
     "ExportDialog opened from File > Export > Report
      triggered by MainWindow::onExportClicked()
      Widget ID: exportButton, geometry: (x:120, y:45)"
                    │
                    ▼
     Agent sends overlay instruction to SDK:
     { step: 1, target: "menuBar.File", style: "pulse_ring", label: "Click File" }
     { step: 2, target: "menu.Export", style: "arrow_point", label: "Then click Export" }
     { step: 3, target: "menuExport.Report", style: "highlight_box", label: "Then click Report" }
                    │
                    ▼
     Qt Overlay Window draws on screen:
     ┌─────────────────────────────────┐
     │  ┌──────────────────────────┐   │
     │  │ [File]●  Edit  View  Help│   │← pulsing ring on "File"
     │  └──────────────────────────┘   │
     │                                 │
     │   💬 "Step 1: Click the File   │
     │      menu in the top-left"      │
     └─────────────────────────────────┘
```

#### Overlay Techniques:

**For Qt Apps — Transparent Overlay Window:**
```
QWidget with:
  - Qt::WindowStaysOnTopHint  → always on top
  - Qt::FramelessWindowHint   → no window border
  - WA_TransparentForMouseEvents → clicks pass through to the real app
  - Semi-transparent background
  - QPainter draws: glowing rectangles, animated arrows, step numbers, tooltips
```

**For Web Apps — JavaScript Overlay Layer:**
```
A <div> injected at z-index: 99999 with:
  - CSS clip-path spotlight effect (darken everything except target)
  - Animated border/glow on target elements
  - Floating tooltip bubbles with step instructions
  - (Similar to how Shepherd.js / Intro.js work, but AI-driven)
```

#### Visual Styles Available:

| Style | When Used |
|---|---|
| **Pulsing Ring** | "Click this button" |
| **Glowing Box** | "Look at this area / fill this form" |
| **Animated Arrow** | "Drag/drop here" |
| **Spotlight** | Dim everything except the target area |
| **Step Number Badge** | Multi-step workflows (1→2→3) |
| **Drop Zone Indicator** | "Drop your file here" with animated dashed border |
| **Error Pointer** | Points to the field causing an error |

#### Step-by-Step Flow:
```
1. User asks a question
2. Agent generates a list of UI steps with target widget IDs
3. SDK resolves widget IDs → screen coordinates (via QAccessible / DOM)
4. Overlay appears on Step 1
5. User performs the action
6. SDK detects the action was performed (event listener)
7. Overlay advances to Step 2
8. Repeats until task is complete
9. Overlay disappears with a ✅ confirmation
```

---

## Full System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      HOST APPLICATION                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              VISUAL OVERLAY LAYER                        │  │
│  │  (Transparent Qt window / JS div — always on top)        │  │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────────────────┐ │  │
│  │  │ Pulsing  │  │  Arrow    │  │  Step tooltip bubble   │ │  │
│  │  │  Ring    │  │  Pointer  │  │  "Click here to Export"│ │  │
│  │  └──────────┘  └───────────┘  └────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Qt / Web │───▶│  AppAI SDK   │───▶│  Chat Sidebar Panel  │  │
│  │   App    │    │ (thin layer) │    │  (Ask me anything)   │  │
│  └──────────┘    └──────┬───────┘    └──────────────────────┘  │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │  WebSocket
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AppAI AGENT CORE (Sidecar)                    │
│                                                                  │
│ ┌─────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│ │ Source Code │  │  Knowledge     │  │  Proactive Engine      │ │
│ │  Parser     │  │  Base (RAG)    │  │  + Overlay Planner     │ │
│ │             │  │                │  │                        │ │
│ │ .ui / .qml  │  │ App Manifest   │  │ Live Context:          │ │
│ │ .cpp / .py  │  │ + External Docs│  │  current screen        │ │
│ │ .jsx / .vue │  │ (ChromaDB)     │  │  user intent           │ │
│ └──────┬──────┘  └──────┬─────────┘  │  next best action      │ │
│        └────────────────▼────────────┴────────────────────────┘ │
│                    ┌────────────────────┐                        │
│                    │   LLM Orchestrator  │                       │
│                    └────────┬───────────┘                        │
└─────────────────────────────┼────────────────────────────────────┘
                              │
         ┌────────────────────┼──────────────────────┐
         ▼                    ▼                       ▼
  ┌─────────────┐    ┌──────────────┐      ┌──────────────────┐
  │  Local LLM  │    │   OpenAI     │      │  Anthropic       │
  │  (Ollama)   │    │   API        │      │  Claude API      │
  └─────────────┘    └──────────────┘      └──────────────────┘
```

---

## Source Code Parser Pipeline

```
Source Code Files
      │
      ▼
┌──────────────────┐
│  Language Parser  │  ← Detects Qt/Web project type automatically
│  (Tree-sitter /  │
│   AST-based)     │
└────────┬─────────┘
         │
         ├──▶ UI Element Extractor   → widget IDs, labels, geometries
         ├──▶ Route/Page Extractor   → all screens and navigation paths
         ├──▶ Action Extractor       → buttons, menus, their triggers
         ├──▶ Form Extractor         → fields, validators, required fields
         ├──▶ Error Message Extractor→ all error strings and their conditions
         └──▶ Workflow Graph Builder → "doing A leads to B leads to C"
                    │
                    ▼
           AppManifest.json  ──▶  ChromaDB (vector indexed)
```

---

## Overlay Message Protocol

The SDK and agent communicate overlay instructions as structured JSON:

```json
{
  "type": "overlay_guide",
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
    },
    {
      "step": 3,
      "target_id": "dropZoneImport",
      "target_type": "qt_widget",
      "style": "drop_zone_indicator",
      "label": "Step 3: Drop your PDF file here",
      "wait_for": "file_dropped"
    }
  ]
}
```

---

## Proactive Triggers

| User Situation | Agent Response |
|---|---|
| Idle on a form > 10s | "Looks like you're filling the Invoice form. Need help?" |
| Hover over a disabled button | "This button is disabled because the Name field is empty" |
| Drag a file near the app | Instantly shows drop zone indicator |
| Gets a validation error | Arrow points to the problematic field + explains why |
| Opens a complex dialog for the first time | Auto-starts a quick tour overlay |
| Repeating the same error | "Would you like me to walk you through this step by step?" |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Core | Python (FastAPI) |
| Source Code Parser | Tree-sitter (multi-language AST) |
| LLM Orchestration | LangChain |
| Vector Store | ChromaDB (local) |
| Embeddings | nomic-embed-text (local Ollama) |
| Qt SDK | C++ QWidget overlay + WebSocket client |
| Web SDK | JavaScript + CSS overlay + WebSocket client |
| Communication | WebSocket (JSON protocol) |
| Knowledge Store | SQLite + ChromaDB |
| Config | YAML |
| Local LLM | Ollama (Llama3 / Mistral / Qwen) |
| Cloud LLM | OpenAI / Anthropic (config toggle) |

---

## Phased Development Roadmap

### Phase 1 — Core Foundation
- [ ] Agent sidecar (Python/FastAPI + WebSocket server)
- [ ] LLM router (Ollama + OpenAI + Claude)
- [ ] Qt SDK with WebSocket client
- [ ] Basic chat panel UI

### Phase 2 — Source Code Intelligence
- [ ] Source code parser (Tree-sitter, Qt .ui XML, QML)
- [ ] AppManifest builder
- [ ] RAG pipeline (ChromaDB + LangChain)
- [ ] External doc ingestion (PDF, HTML, Markdown, URLs)

### Phase 3 — Visual Overlay System
- [ ] Qt transparent overlay window
- [ ] Overlay styles (pulse ring, arrow, spotlight, drop zone)
- [ ] Step-by-step advance logic (wait for user action)
- [ ] Web JS overlay for web apps

### Phase 4 — Proactive Intelligence
- [ ] Live context tracker (current screen, user actions)
- [ ] Proactive trigger engine
- [ ] Idle detection + proactive prompts
- [ ] Drag-file detection + instant drop zone overlay

### Phase 5 — Polish & Multi-App
- [ ] Config dashboard (YAML + GUI)
- [ ] Multi-app support
- [ ] Overlay animations + smooth UX
- [ ] Performance tuning for local LLM latency
