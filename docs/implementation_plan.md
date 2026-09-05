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
| **Code confidentiality** | Source code is used internally only — never exposed to non-developer users |
| **User management** | Self-registration as app_user by default; admin assigns roles via dashboard |
| **Admin Dashboard** | Separate web UI for app config, user management, KB management, system health |

---

## Code Confidentiality Policy

> [!IMPORTANT]
> AppAI has access to the application's full source code as its knowledge base.
> This access is **strictly internal**. The agent uses it to *understand* how the app
> works — it **never reveals source code, class names, function names, file paths,
> internal logic, or any developer-level detail** to regular (non-developer) users.

### The Rule

The agent behaves like a **knowledgeable support expert** who happens to have read
the full technical documentation — but only surfaces what is relevant and appropriate
for the user's role.

| What Agent Knows (internally) | What Agent Tells app_user |
|---|---|
| `MainWindow::onExportClicked()` triggers `ExportDialog` | "Click File > Export to open the export screen" |
| `customerAddress` field has `QLineEdit::setRequired(true)` | "The Customer Address field is required" |
| `InvoiceService::generatePDF()` calls `PDFRenderer` | "The app will generate and save your PDF automatically" |
| File path: `/src/billing/invoice_dialog.cpp` | ❌ Never revealed |
| Signal: `exportCompleted(bool success)` | ❌ Never revealed |
| SQL query in `InvoiceRepo::fetchAll()` | ❌ Never revealed |

### How It's Enforced

**Layer 1 — System Prompt (LLM level):**
Every LLM prompt includes a role-based instruction:

```
[For app_user role]
SYSTEM: You are a helpful assistant for {app_name}.
You have deep knowledge of how this application works.
STRICT RULES:
- NEVER mention source code, file names, class names, function names,
  or any internal implementation details.
- NEVER reveal database queries, API endpoints, or internal architecture.
- Speak only in terms of what the user sees and interacts with on screen.
- If asked about internals, say: "I'm not able to share technical details,
  but I can help you accomplish what you need."

[For developer role]
SYSTEM: You are a technical assistant for {app_name}.
You may reference internal implementation details when relevant.
```

**Layer 2 — Response Filter (post-LLM):**
Before any response is sent to a non-developer user, it passes through a
**Content Safety Filter** that:
- Detects and strips code blocks (` ``` `)
- Removes patterns matching file paths (`./src/...`, `.cpp`, `.py`, `.h`)
- Removes class/function signatures (`ClassName::method()`, `def func_name`)
- Removes SQL-like patterns
- Logs any filter trigger for admin audit

**Layer 3 — KB Retrieval Filter:**
When searching the knowledge base for a non-developer user, the retriever
excludes chunks tagged as `content_type: source_code` and only returns
chunks tagged as `content_type: ui_description` or `content_type: user_doc`.

```
KB Chunk Tags:
  content_type: source_code    → visible to: developer, super_admin only
  content_type: ui_description → visible to: all roles
  content_type: user_doc       → visible to: all roles
  content_type: error_message  → visible to: all roles
  content_type: workflow       → visible to: all roles
```

---

## Role-Based Access Control (RBAC)

### User Roles

| Role | Who | Permissions |
|---|---|---|
| `super_admin` | Platform owner / IT lead | Full access: all apps, all users, all config, all KB content, developer-level AI responses |
| `app_admin` | App-specific admin | Manage assigned apps: register, configure, view KB, manage users of those apps |
| `developer` | App developer / technical user | Full technical AI responses (sees code references), access KB, re-trigger parsing |
| `support_agent` | Helpdesk / support team | Review conversation logs, manage escalation tickets, flag bad AI responses, add docs to KB — no source code access |
| `app_user` | End users of the application | Use the AI assistant only; responses always code-free; no config access |

### Role Assignment Flow

```
New user opens the app
        │
        ▼
AppAI SDK shows: "Register to get AI assistance"
        │
User fills name + email → registered as app_user (default, immediate access)
        │
        ▼
Admin Dashboard notifies admin: "New user registered: user@company.com"
        │
Admin reviews and optionally upgrades role:
  app_user → support_agent  (for helpdesk / support team members)
  app_user → developer      (for technical team members)
  app_user → app_admin      (for team leads / app owners)
        │
        ▼
User's next session automatically uses their assigned role
```

### Role-Gated AI Behavior

```
Same question: "Why is the Export button not working?"

app_user gets:
  "The Export button requires a date range to be selected first.
   Please set the Start Date and End Date fields, then try again."

support_agent gets (reviewing a ticket):
  Same user-friendly response as app_user + conversation context
  panel showing: screen state, idle time, prior steps attempted.
  No code references shown.

developer gets:
  "The Export button is gated by validateDateRange() in ExportController.
   It checks that startDate and endDate are both non-null and that
   startDate < endDate. The signal exportReady(bool) is emitted only
   when this validation passes. Check invoice_controller.cpp:L142."
```

---

## Support Team — Workflows & Tooling

### The Three Support Scenarios

**Scenario 1 — AI Succeeds (No Human Involved)**
User asks → AI answers → overlay guides → task complete. Support team never involved.
This should be the majority (target: 80%+) of interactions.

**Scenario 2 — AI Cannot Resolve → Escalation to Human**

```
User follows AI steps but is still stuck, or AI says "I don't have enough
information to help with this specific case."
        │
        ▼
AI offers graceful escalation:
  "I've done my best but I think a human should look at this.
   Would you like me to raise a support ticket? I'll include our
   full conversation so they'll have full context immediately."

   [Yes, raise a ticket]   [Let me try something else]
        │
        ▼  (if user agrees)
Ticket created automatically containing:
  • User identity + app name + current screen + timestamp
  • Full AI conversation transcript (all questions + all answers)
  • Screenshot (only if user had already consented earlier in the session)
  • AI's last known diagnosis of the issue
  • Steps user already attempted (from overlay history)
        │
        ▼
Support agent picks up the ticket in Support Dashboard.
Has full context immediately — no "can you describe the problem again."
```

**Scenario 3 — User Flags a Bad AI Response**

```
After any AI response, user can click 👎 "This didn't help"
        │
        ▼
AI asks: "Sorry about that. What was wrong with my answer?"
  [Wrong information]  [Missing steps]  [Doesn't apply to my situation]
        │
        ▼
Feedback logged to Support Dashboard as a "flagged response"
        │
        ▼
Support agent reviews: sees the question, the AI's answer, and the user's feedback
        │
  If it's a knowledge gap (AI didn't know):
        → Agent adds a doc/note to the KB covering the missing topic
        → Next user who asks the same question gets a correct answer
        → Ticket auto-closes as "KB updated"

  If it's an AI error (AI gave wrong info despite having KB):
        → Agent flags for LLM prompt review
        → Engineering team tunes the prompt or KB chunk for that topic
```

---

### Knowledge Gap Report — The Feedback Loop

The most valuable thing support teams contribute is **making the AI smarter over time**.

AppAI automatically tracks every question it couldn't answer well:

```
Knowledge Gap Report (visible in Support Dashboard):

  "How do I bulk upload invoices?"         → asked 8 times, no good AI answer
  "Where is the archive feature?"          → asked 5 times, AI said "I don't know"
  "How to change the fiscal year setting?" → asked 3 times, wrong answer flagged

  [+ Add KB Doc for this topic]   ← support agent can attach a doc directly
```

**The loop:**
```
User asks question AI can't answer
        │
        ▼
AI escalates or gives partial answer → user flags it
        │
        ▼
Support agent sees it in Knowledge Gap Report
        │
        ▼
Agent adds a document, note, or KB correction
        │
        ▼
AI answers the question correctly for the next user
        │
        ▼
No more escalation tickets for that topic ✅
```

Over time, the AI handles more and more cases independently, reducing support team workload.

---

### Support Agent Dashboard Panel

A dedicated **Support Panel** accessible to `support_agent` and `app_admin` roles:

```
┌────────────────────────────────────────────────────────────┐
│  🤖 AppAI Admin — Support View        [Priya Support ▼]    │
├───────────┬────────────────────────────────────────────────┤
│           │                                                 │
│  🎫 Tickets│  Open Tickets (12)           [Assigned to me] │
│           │  ┌───────┬─────────────┬──────┬──────────────┐ │
│  🧠 Gaps  │  │ #1042 │ ravi.kumar  │ Bill │ Waiting 2h   │ │
│           │  │ #1041 │ meena.s     │ HR   │ Waiting 45m  │ │
│  👎 Flagged│  │ #1040 │ arjun.k     │ Inv  │ In Progress  │ │
│           │  └───────┴─────────────┴──────┴──────────────┘ │
│  📋 History│                                                │
│           │  🧠 Knowledge Gaps (Top unanswered questions)   │
│           │  ┌─────────────────────────────┬───────┬──────┐ │
│           │  │ Question                    │ Count │      │ │
│           │  ├─────────────────────────────┼───────┼──────┤ │
│           │  │ Bulk upload invoices?        │  8    │[Fix] │ │
│           │  │ Archive feature location?    │  5    │[Fix] │ │
│           │  │ Change fiscal year setting?  │  3    │[Fix] │ │
│           │  └─────────────────────────────┴───────┴──────┘ │
└───────────┴────────────────────────────────────────────────┘
```

**Ticket detail view** (when support agent opens a ticket):

```
Ticket #1042 — ravi.kumar — BillingApp — Opened 2h ago

Current Screen: Invoice Export Dialog
Last 5 Actions: [opened report] [set date range] [clicked Export] 
                [got error] [clicked Export again]

Conversation Transcript:
  User:   "How do I export this report as PDF?"
  AppAI:  "Step 1: Click File > Export..." [full steps shown]
  User:   "I did all that but I get error: Permission denied"
  AppAI:  "This may be a folder permission issue on your machine..."
  User:   "Still not working"
  AppAI:  [raised ticket]

Screenshot: [attached — user consented]

[Reply to User]  [Resolve]  [Mark as Knowledge Gap]  [Escalate to Dev]
```

---

### Support Agent Permissions Summary

| Capability | support_agent | app_admin | developer |
|---|---|---|---|
| View conversation transcripts | ✅ | ✅ | ✅ |
| Manage escalation tickets | ✅ | ✅ | ❌ |
| View Knowledge Gap report | ✅ | ✅ | ❌ |
| Add docs to KB | ✅ | ✅ | ✅ |
| Flag/review bad AI responses | ✅ | ✅ | ❌ |
| View source code KB chunks | ❌ | ❌ | ✅ |
| Register/configure apps | ❌ | ✅ | ❌ |
| Manage user roles | ❌ | ✅ (own apps) | ❌ |
| Access system config | ❌ | ❌ | ❌ |

---

### Ticket Integration (Optional — Enterprise)

For organizations that already have a helpdesk system (Jira, Freshdesk, Zendesk):
- AppAI can push tickets to the external system via webhook
- Conversation transcript + context attached automatically
- Two-way sync: resolving the ticket in Jira also marks it resolved in AppAI

```yaml
# appai.config.yaml
support:
  ticketing:
    provider: jira           # jira | freshdesk | zendesk | internal
    webhook_url: https://company.atlassian.net/rest/api/3/issue
    api_key: ${JIRA_API_KEY}
    project_key: SUPPORT
```

---


## Admin Dashboard

A separate **web-based admin portal** — independent of the host applications.
Accessible only to `super_admin` and `app_admin` roles.

### Dashboard Sections

#### 1. App Management
- Register a new application (source path, docs path, app name)
- View all registered apps with status (KB healthy / needs re-indexing)
- Trigger manual re-parse / KB rebuild for an app
- View KB statistics: total chunks, last indexed, index size
- Enable / disable an app (remove from active registry without deleting KB)
- Configure per-app settings (proactive hints on/off, overlay styles, LLM override)

#### 2. User Management
- View all registered users across all apps
- View role per user per app (a user can be `developer` for App1 but `app_user` for App2)
- Assign / change roles
- Approve or reject pending registrations (if approval mode is enabled)
- Revoke user access
- View last active timestamp and session count per user

#### 3. Knowledge Base Management
- Browse KB content per app (filtered by content_type)
- Add external documents (PDF, HTML, MD, URL) to an app's KB
- Delete specific KB chunks (e.g., outdated docs)
- View embedding health and re-embed if needed

#### 4. System Configuration
- LLM backend: switch between Ollama / vLLM / OpenAI / Claude
- Test LLM connection and response latency
- Configure Ollama / vLLM server URL and model name
- Embedding model configuration
- Hub WebSocket port and TLS settings

#### 5. Audit Logs
- All consent events (screenshot allowed/denied, doc shared)
- All role changes (who changed whose role, when)
- Content Safety Filter triggers (when a response was filtered)
- App registration and re-index events
- User registration events

#### 6. System Health
- Hub process status (uptime, active connections, requests/sec)
- LLM backend status (latency, availability)
- Vector store status (ChromaDB / Qdrant health)
- Active sessions (currently connected users per app)
- Resource usage (CPU, RAM, disk)

### Admin Dashboard — Tech Stack

| Component | Technology |
|---|---|
| Frontend | React + TypeScript (web app) |
| Backend API | FastAPI (Python) — extends Hub with admin API routes |
| Auth | JWT — admin tokens have elevated scope |
| Charts / Metrics | Recharts or Chart.js |
| Audit Log Store | SQLite (local) / PostgreSQL (enterprise) |

### Admin Dashboard — Access

```
URL: http://localhost:7789/admin   (local mode)
     https://appai.company.local/admin   (enterprise mode)

Login: email + password (admin accounts only)
       No self-registration — admin accounts created by super_admin only
```

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
