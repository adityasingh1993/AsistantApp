# AppAI — High-Level Design Document (HLD)

**Project Name:** AppAI — Intelligent Proactive App Assistant  
**Version:** 2.0  
**Status:** Design Approved — Ready for Development  
**Prepared By:** Engineering Team  
**Last Updated:** September 2026  
**Audience:** Project Managers, Architects, Developers, Stakeholders

---

## Table of Contents

1. [Business Problem & Motivation](#1-business-problem--motivation)
2. [Product Vision & Goals](#2-product-vision--goals)
3. [Who Uses This System](#3-who-uses-this-system)
4. [What AppAI Does — In Plain Language](#4-what-appai-does--in-plain-language)
5. [Key Features & Capabilities](#5-key-features--capabilities)
6. [System Context — Big Picture](#6-system-context--big-picture)
7. [Architecture — Component Overview](#7-architecture--component-overview)
8. [Component Descriptions](#8-component-descriptions)
9. [How It All Works — Data Flows](#9-how-it-all-works--data-flows)
10. [Deployment Modes](#10-deployment-modes)
11. [Scalability Plan](#11-scalability-plan)
12. [Technology Stack](#12-technology-stack)
13. [Security & Privacy Model](#13-security--privacy-model)
14. [Design Principles](#14-design-principles)
15. [Risks & Mitigations](#15-risks--mitigations)
16. [Team & Roles](#16-team--roles)
17. [Milestones & Delivery Plan](#17-milestones--delivery-plan)
18. [Success Metrics](#18-success-metrics)
19. [Glossary](#19-glossary)

---

## 1. Business Problem & Motivation

### The Problem

Modern desktop and web applications are becoming increasingly complex. Users — whether they are internal employees, field operators, or external customers — often struggle to:

- Discover features that exist in the application but are hard to find
- Complete multi-step workflows without making mistakes
- Understand why an error occurred and how to fix it
- Get help quickly without leaving the application to search documentation or raise a support ticket

Traditional solutions to this problem include:

| Traditional Approach | Why It Falls Short |
|---|---|
| Static user manuals / PDFs | Out of date, hard to search, users don't read them |
| In-app tooltips | Static text, not context-aware, require manual maintenance |
| Video tutorials | Can't answer specific user questions in real time |
| Help desk / support tickets | Slow, expensive, disrupts user workflow |
| Generic chatbots | Not aware of the specific application's features or the user's current screen |

### The Opportunity

The rise of large language models (LLMs) and AI agents makes it possible to build a **truly intelligent, context-aware assistant** that:

- Lives inside the application itself
- Understands the application's complete feature set (by reading its source code)
- Knows exactly what the user is looking at right now
- Can visually point to the exact button, field, or menu the user needs to interact with
- Proactively offers help before the user even asks
- Works privately on the company's own infrastructure — no data sent to external services

### Why Now

- Local AI models (running on standard hardware without internet) have become capable enough to provide high-quality assistance
- The cost of building this infrastructure has dropped dramatically
- Companies are investing heavily in productivity tools that reduce training time and support costs

---

## 2. Product Vision & Goals

### Vision Statement

> **AppAI makes every application self-teaching.** Any user — technical or non-technical — can walk up to any of our applications and accomplish any task with the help of an intelligent, visually-guided AI assistant that knows the application inside and out.

### Strategic Goals

| Goal | Description |
|---|---|
| **Reduce support burden** | Users self-serve common tasks without raising support tickets |
| **Accelerate onboarding** | New users become productive faster with in-app guidance |
| **Improve feature adoption** | Users discover and use features they didn't know existed |
| **Protect data privacy** | All AI processing happens on-premise — no user data sent to cloud |
| **Scale across all apps** | One platform serves all current and future applications with minimal integration effort |

---

## 3. Who Uses This System

### Stakeholders & Their Relationship to AppAI

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AppAI STAKEHOLDERS                              │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │  END USERS   │  │  DEVELOPERS  │  │  IT ADMINS / DEVOPS       │  │
│  │              │  │              │  │                           │  │
│  │ People who   │  │ Teams who    │  │ People who deploy and     │  │
│  │ use the apps │  │ build the    │  │ maintain the AppAI Hub    │  │
│  │ day-to-day   │  │ apps and     │  │ server and manage which   │  │
│  │              │  │ register     │  │ apps are connected        │  │
│  │ They see:    │  │ them with    │  │                           │  │
│  │ • Chat panel │  │ AppAI        │  │ They manage:              │  │
│  │ • Overlays   │  │              │  │ • Hub deployment          │  │
│  │ • Step guides│  │ They do:     │  │ • App registration        │  │
│  └──────────────┘  │ • Add SDK    │  │ • LLM configuration       │  │
│                    │ • Register   │  │ • User access             │  │
│                    │   source code│  └───────────────────────────┘  │
│                    └──────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### User Personas

**Persona 1 — Ravi (Field Operator)**
> Ravi uses the Inventory Management App. He knows his job well but struggles with the app's bulk export feature. Previously, he'd call the helpdesk. With AppAI, he types "how do I export this month's stock report" and a glowing arrow walks him through each step — he never leaves the app.

**Persona 2 — Meena (New Joiner)**
> Meena joined last week. She's on the Invoice Generation screen for the first time. AppAI notices she's been idle for 15 seconds and proactively says "It looks like you're creating your first invoice. Would you like a quick walkthrough?" She clicks yes, and a step-by-step tour begins.

**Persona 3 — Arjun (Developer)**
> Arjun's team built the Billing App. He registers it with AppAI by running one command pointing to the source code. From that point, all users of Billing App get AI assistance automatically.

---

## 4. What AppAI Does — In Plain Language

Think of AppAI as a **knowledgeable colleague sitting next to the user**, who:

1. **Has read every page of the application's manual** (by analyzing the source code)
2. **Can see exactly what the user is looking at** (current screen, open dialogs, active fields)
3. **Answers questions in real time** via a chat panel inside the app
4. **Doesn't just explain — physically points** at the button, menu, or field the user needs
5. **Speaks up when it sees the user struggling** — before the user asks for help
6. **Respects the user's privacy** — always asks before looking at their screen or files
7. **Works completely offline** — no internet required, no data sent outside the building

### What It Looks Like for the User

```
┌──────────────────────────────────────────────────────────┐
│                    BILLING APPLICATION                    │
│                                                          │
│  ┌────────────────────┐                                  │
│  │ File  Edit  Reports│◀── Pulsing glow: "Step 1:        │
│  └────────────────────┘    Click the File menu"          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                   Main Workspace                  │   │
│  │                                                   │   │
│  │                                                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────┐           │
│  │  🤖 AppAI Assistant                      │           │
│  │                                           │           │
│  │  You: How do I export an invoice as PDF?  │           │
│  │                                           │           │
│  │  AppAI: Here's how to export as PDF:      │           │
│  │  ① Click the File menu (top-left)         │← shown    │
│  │  ② Click Export                           │  in chat  │
│  │  ③ Choose "PDF" from the format list      │  all at   │
│  │  ④ Click the Export button                │  once     │
│  │                                           │           │
│  │  I'm highlighting Step ① on screen now.   │           │
│  │  Complete it and I'll move to the next.   │           │
│  │                                           │           │
│  │  [Type a question...]           [Send]    │           │
│  └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Key Features & Capabilities

### Feature 1 — Source Code Intelligence
AppAI is given access to the application's source code files during setup. It reads and understands:
- Every screen, form, dialog, and page in the application
- Every button, menu item, and toolbar action — what it does and where it leads
- All workflows (what happens after each step)
- All error messages and what triggers them
- Keyboard shortcuts, field validation rules, and required fields

**Why this matters:** Unlike generic chatbots that make up answers, AppAI's knowledge is grounded in the actual application — it can never hallucinate a feature that doesn't exist.

---

### Feature 2 — Visual Overlay Guidance
When a user asks how to do something, AppAI doesn't just tell them — it **shows them** by drawing visual indicators directly on the application window:

| Indicator | What It Looks Like | Used When |
|---|---|---|
| Pulsing Ring | Animated glowing circle around a button | "Click this button" |
| Glowing Box | Highlighted border around a form field | "Fill in this field" |
| Animated Arrow | Moving arrow pointing to a menu/item | "Navigate here" |
| Spotlight | Screen darkened except for the target area | Deep focus on one area |
| Drop Zone | Dashed animated border on a file drop area | "Drop your file here" |
| Step Number | Badge showing "① ② ③" in sequence | Multi-step workflows |

The overlay is **transparent to clicks** — the user can interact with the application normally while the highlights are showing.

---

### Feature 3 — Step-by-Step & Tour Modes
Users can choose how they want guidance delivered:

- **Step-by-step (default):** One highlight appears at a time. When the user completes the step, the next highlight appears automatically
- **All-at-once tour:** All steps are numbered and visible simultaneously — good for experienced users who just need a quick reminder

In both modes, the **complete list of steps is always shown in the chat panel** upfront so users know exactly what's coming.

---

### Feature 4 — Proactive Assistance
AppAI doesn't wait to be asked. It watches for situations where users might be struggling:

| Situation | What AppAI Does |
|---|---|
| User idle for 10+ seconds on a complex form | Offers a friendly prompt: "Need help with this form?" |
| User hovering over a disabled button | Explains why it's disabled and what to do first |
| User drags a file near the application | Instantly shows where to drop it |
| User encounters a validation error | Points to the exact field causing the problem |
| User visits a complex screen for the first time | Offers a quick orientation tour |
| User repeats the same mistake twice | Gently suggests a step-by-step walkthrough |

Proactive messages appear as **non-intrusive hint bubbles** at the bottom of the chat panel. Users can always dismiss them.

---

### Feature 5 — External Document Support
In addition to source code, AppAI can ingest optional external knowledge:
- PDF user manuals
- HTML documentation pages
- Internal knowledge base articles (Markdown)
- Website URLs

When external docs are provided, AppAI combines them with the source code knowledge for even richer answers.

---

### Feature 6 — Consent-Driven Screenshot & File Access
If a user is reporting a visual problem on screen, AppAI may need to see it. But it will **always ask first**:

> *"To better understand what you're seeing, may I take a screenshot? It will only be used to answer your question and won't be stored anywhere."*
> **[Allow Once] [Allow for this session] [No, thanks]**

Screenshots are used in memory for one answer only and then discarded. They are never saved and never sent to any external service.

The same consent flow applies to any private document the user may want to share.

---

### Feature 7 — Privacy-First, Local AI
All AI processing happens on your own infrastructure:
- The AI model runs on your server or machine (using Ollama or vLLM)
- No user questions, answers, or screenshots are ever sent to OpenAI, Google, or any cloud service — unless you explicitly configure a cloud backend
- All knowledge bases are stored locally in your own database
- Works fully offline — no internet connection required

Cloud AI (OpenAI, Claude) is available as an opt-in option for teams who prefer it, with a clear one-time warning that data will leave the premises.

---

## 6. System Context — Big Picture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ORGANIZATION'S ENVIRONMENT                        │
│                                                                           │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│   │  Billing App │    │ Inventory App│    │  HR Portal   │    ... more   │
│   │  (Qt Desktop)│    │  (Qt Desktop)│    │  (Web App)   │    apps      │
│   │              │    │              │    │              │               │
│   │  + AppAI SDK │    │  + AppAI SDK │    │  + AppAI SDK │               │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│          └──────────────────┬┘─────────────────┘                         │
│                             │  Secure connection (local network)          │
│                             ▼                                             │
│              ┌──────────────────────────────┐                            │
│              │         AppAI HUB            │                            │
│              │   (Central AI Service)        │                            │
│              │                              │                            │
│              │  Understands all apps        │                            │
│              │  Handles all users           │                            │
│              │  One AI model, shared        │                            │
│              └──────────────┬───────────────┘                            │
│                             │                                             │
│              ┌──────────────┼──────────────┐                             │
│              ▼              ▼              ▼                             │
│         AI Model        Knowledge       User Sessions                    │
│         (Ollama /        Bases           (one per                        │
│          vLLM)          (one per app)    user × app)                     │
│                                                                           │
│   ─────────────────────────────────────────────────────────              │
│   Everything above stays inside your organization's network              │
│   ─────────────────────────────────────────────────────────              │
│                                                                           │
│              ┌──────────────────────────────┐                            │
│              │  OPTIONAL: Cloud LLM         │  ← Only if configured      │
│              │  (OpenAI / Anthropic Claude)  │    User warned explicitly  │
│              └──────────────────────────────┘                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Architecture — Component Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                            HOST APPLICATION                                  ║
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐ ║
║  │                    VISUAL OVERLAY LAYER                                 │ ║
║  │  Transparent window drawn on top of the app (invisible to mouse clicks) │ ║
║  │  ● Pulsing rings   ➜ Arrows   ■ Spotlights   ⬚ Drop zones   ① Numbers │ ║
║  └────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║  ┌──────────────────────────┐     ┌────────────────────────────────────┐   ║
║  │     HOST APP CODE         │     │     AI CHAT PANEL (SDK)            │   ║
║  │  (Qt Widgets / React /   │◀───▶│  • Shows all steps in chat upfront │   ║
║  │   Vue / any web framework)│     │  • Receives user questions         │   ║
║  └──────────────────────────┘     │  • Shows proactive hints            │   ║
║                                   └────────────────────────────────────┘   ║
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐ ║
║  │                    AppAI SDK  (Thin Integration Layer)                  │ ║
║  │                                                                         │ ║
║  │  This is the ONLY code added to the host application.                   │ ║
║  │  It is intentionally small (~300–500 lines) and non-invasive.           │ ║
║  │                                                                         │ ║
║  │  • Connects to AppAI Hub via WebSocket (like a phone call)              │ ║
║  │  • Sends live screen context (what screen is open, what user did)       │ ║
║  │  • Draws overlays based on instructions from the Hub                    │ ║
║  │  • Shows consent dialogs before any screenshot or file access           │ ║
║  └──────────────────────────────────┬──────────────────────────────────────┘ ║
╚═════════════════════════════════════╪══════════════════════════════════════════╝
                                      │
                         Secure WebSocket Connection
                         (local network or localhost)
                                      │
╔═════════════════════════════════════╪══════════════════════════════════════════╗
║                            AppAI HUB (Central Service)                       ║
║                                      │                                        ║
║  ┌───────────────────────────────────▼──────────────────────────────────┐    ║
║  │                        CONNECTION MANAGER                             │    ║
║  │  Accepts connections from all apps simultaneously.                    │    ║
║  │  Routes each message to the correct session and knowledge base.       │    ║
║  └───────────────────────────────────────────────────────────────────────┘    ║
║                                                                                ║
║  ┌───────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   ║
║  │    APP REGISTRY        │  │  SESSION MANAGER  │  │  PROACTIVE ENGINE    │   ║
║  │                        │  │                  │  │                      │   ║
║  │  Stores details of all │  │  Tracks one      │  │  Monitors live       │   ║
║  │  registered apps:      │  │  conversation    │  │  context and fires   │   ║
║  │  • Name & ID           │  │  per user        │  │  hints when users    │   ║
║  │  • Source code location│  │  per application │  │  appear stuck        │   ║
║  │  • Knowledge base ID   │  │                  │  │                      │   ║
║  └───────────────────────┘  └──────────────────┘  └──────────────────────┘   ║
║                                                                                ║
║  ┌────────────────────────────────────────────────────────────────────────┐   ║
║  │                          AGENT CORE                                     │   ║
║  │                                                                         │   ║
║  │  The brain that handles each user query:                                │   ║
║  │                                                                         │   ║
║  │  1. Retrieves relevant info from the app's knowledge base               │   ║
║  │  2. Combines it with the user's current screen context                  │   ║
║  │  3. Sends it to the AI model for a response                             │   ║
║  │  4. Converts the AI response into chat text + overlay instructions      │   ║
║  └────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                ║
║  ┌────────────────────────────────────────────────────────────────────────┐   ║
║  │                       KNOWLEDGE BASE ENGINE                             │   ║
║  │                                                                         │   ║
║  │  ┌────────────────────────┐   ┌───────────────────────────────────┐    │   ║
║  │  │  SOURCE CODE PARSER    │   │  VECTOR DATABASE                  │    │   ║
║  │  │                        │   │  (AI-searchable knowledge store)  │    │   ║
║  │  │  Reads the app's code  │──▶│                                   │    │   ║
║  │  │  files at setup time   │   │  App 1 Knowledge  [isolated]      │    │   ║
║  │  │  and extracts:         │   │  App 2 Knowledge  [isolated]      │    │   ║
║  │  │  • All UI elements     │   │  App 3 Knowledge  [isolated]      │    │   ║
║  │  │  • All workflows       │   │  ...                              │    │   ║
║  │  │  • All error messages  │   └───────────────────────────────────┘    │   ║
║  │  │  • All features        │                                             │   ║
║  │  └────────────────────────┘   ┌───────────────────────────────────┐    │   ║
║  │                               │  DOCUMENT INGESTION               │    │   ║
║  │  ┌────────────────────────┐   │  (on user consent only)           │    │   ║
║  │  │  APP MANIFEST STORE    │   │                                   │    │   ║
║  │  │                        │   │  PDF manuals, HTML docs,          │    │   ║
║  │  │  Structured map of     │   │  Markdown articles, URLs          │    │   ║
║  │  │  every widget, screen, │   └───────────────────────────────────┘    │   ║
║  │  │  and action, with      │                                             │   ║
║  │  │  screen coordinates    │                                             │   ║
║  │  └────────────────────────┘                                             │   ║
║  └────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                ║
║  ┌────────────────────────────────────────────────────────────────────────┐   ║
║  │                           LLM ROUTER                                    │   ║
║  │                                                                         │   ║
║  │  A single switch to choose the AI backend. Configured by IT admin.     │   ║
║  │                                                                         │   ║
║  │  ┌────────────────┐  ┌────────────────┐  ┌──────────┐  ┌──────────┐   │   ║
║  │  │ Ollama (Local) │  │  vLLM (Server) │  │  OpenAI  │  │  Claude  │   │   ║
║  │  │  Llama3        │  │  Any model     │  │  GPT-4o  │  │  Sonnet  │   │   ║
║  │  │  Mistral       │  │  on GPU server │  │  (Cloud) │  │  (Cloud) │   │   ║
║  │  │  Qwen / Phi    │  │  (self-hosted) │  │          │  │          │   │   ║
║  │  │  ← DEFAULT     │  │                │  │  ⚠ Data  │  │  ⚠ Data  │   │   ║
║  │  │  100% private  │  │  100% private  │  │  leaves  │  │  leaves  │   │   ║
║  │  └────────────────┘  └────────────────┘  └──────────┘  └──────────┘   │   ║
║  └────────────────────────────────────────────────────────────────────────┘   ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Component Descriptions

### 8.1 AppAI SDK

**What it is:** A small software package added to each host application during development.

**What it does:**
- Maintains a constant connection to the AppAI Hub (like a phone always on a call)
- Sends updates about what the user is currently doing (current screen, idle time, errors visible)
- Receives instructions from the Hub (overlay steps, chat messages, proactive hints)
- Draws visual highlights on the application window
- Shows consent dialogs before taking any screenshot or reading any file
- Renders the chat panel inside the application UI

**How big is it?** Approximately 300–500 lines of code for the Qt version. It does not affect application performance.

**Who adds it?** The application development team — it's a one-time integration per application.

---

### 8.2 AppAI Hub

**What it is:** The central AI service that powers everything. Runs as a background service on a server or a local machine.

**What it does:**
- Accepts connections from all registered applications simultaneously
- Maintains a separate, isolated conversation for each user of each application
- Receives user questions and current context
- Searches the relevant application's knowledge base for the most useful information
- Sends the question, context, and knowledge to the AI model
- Converts the AI model's answer into:
  - A natural-language chat response shown in the chat panel
  - Structured overlay instructions (which widget to highlight, with which style, in which order)
- Monitors user activity patterns and triggers proactive hints
- Logs nothing sensitive — no conversation history stored beyond the session unless explicitly requested

---

### 8.3 App Registry

**What it is:** A catalogue of all applications connected to AppAI.

**What it stores for each app:**
- Application name and unique ID
- Location of the application's knowledge base
- Source code location (used during registration/updates)
- Registration date and last update date

**Who manages it?** IT administrators via the AppAI Admin CLI or future dashboard.

---

### 8.4 Session Manager

**What it is:** Tracks the ongoing conversation between each user and each application.

**What it maintains per session:**
- The full conversation history (user questions + AppAI answers)
- The user's current screen context (updated in real time)
- The user's last 5 actions (to understand intent)
- Proactive state (has a hint already been shown for this situation?)

**Isolation:** Session data for User A on App 1 is completely separate from User B on App 1, and from User A on App 2. There is no cross-contamination.

---

### 8.5 Knowledge Base Engine

**What it is:** The system that transforms an application's source code into a searchable AI knowledge base.

**Sub-components:**

| Sub-component | What It Does |
|---|---|
| Source Code Parser | Reads `.ui`, `.qml`, `.cpp`, `.py`, `.jsx`, `.vue`, `.html` files and extracts structured knowledge about every UI element, workflow, and feature |
| App Manifest Store | Stores a structured map of the application (every widget, its label, its location on screen, what it does) in a local database |
| Document Ingestion | Processes external documents (PDF manuals, HTML pages, Markdown articles) when provided |
| Embedding Engine | Converts all extracted text into a numerical format that allows the AI to search it by meaning (not just keywords) |
| Vector Database | Stores all embedded knowledge in a searchable database, with one isolated space per application |

**When does it run?** Once during initial app registration, and again whenever the application's source code is updated.

---

### 8.6 Proactive Engine

**What it is:** A background monitor that watches user activity and decides when to proactively offer help.

**Trigger rules (examples):**

| What the Engine Sees | What It Does |
|---|---|
| User idle > 10 seconds on a form | Shows: "Looks like you're filling the Invoice form. Need help?" |
| User hovers over a greyed-out button | Shows: "This button is disabled because the Date field is empty" |
| User drags a file near the window | Instantly shows the correct drop zone with animation |
| User gets a validation error | Points to the exact problematic field and explains why |
| User opens a complex screen for the first time | Offers a quick orientation: "This is the Report Builder. Want a quick tour?" |
| User repeats the same error twice | Suggests a step-by-step walkthrough |

All proactive hints are non-intrusive — they appear as small suggestion bubbles. Users can always dismiss them or say "not now."

---

### 8.7 Visual Overlay Engine

**What it is:** The part of the SDK that draws visual guidance directly on the application window.

**How it works technically:**
- **Qt apps:** A transparent window with no border and no background sits on top of the application window. It intercepts no clicks (user can still interact with the app normally). Animated graphics are drawn on it.
- **Web apps:** A transparent `<div>` element is injected at the highest z-index. CSS animations create the visual effects.

**What it can draw:**

| Visual | Description | Use Case |
|---|---|---|
| Pulsing Ring | Animated circle glowing around an element | "Click this button" |
| Glowing Box | Highlighted rectangle around a form field | "Fill in this field" |
| Animated Arrow | Moving arrow pointing to a UI element | "Navigate to this menu" |
| Spotlight | Full-screen dim with the target area lit | Focus on one specific area |
| Drop Zone Indicator | Dashed animated border on a drop target | "Drop your file here" |
| Step Number Badge | ①②③ numbered sequence | Multi-step workflow |
| Error Pointer | Red arrow pointing to an error source | "This field is causing the error" |

---

### 8.8 LLM Router

**What it is:** A configuration-driven switch that decides which AI model to use.

**Supported backends:**

| Backend | Type | Privacy | Best For |
|---|---|---|---|
| **Ollama** | Local (on machine) | ✅ 100% private | Development, small teams, offline use |
| **vLLM** | Self-hosted server | ✅ 100% private | Enterprise, multi-user, GPU-accelerated |
| **OpenAI GPT** | Cloud API | ⚠ Data leaves premises | Teams comfortable with cloud AI |
| **Anthropic Claude** | Cloud API | ⚠ Data leaves premises | Teams comfortable with cloud AI |

Switching backends requires changing one line in the configuration file. The rest of the system is unaffected.

---

## 9. How It All Works — Data Flows

### Flow 1 — App Registration (One-Time Setup)

This happens once per application, done by the development team.

```
Step 1: Developer runs:
        appai register --app-name "BillingApp" --source ./src

Step 2: AppAI Hub reads all source code files
        → Identifies all screens, widgets, menus, forms, dialogs, workflows
        → Extracts labels, tooltips, error messages, keyboard shortcuts

Step 3: All extracted knowledge is converted into
        searchable AI embeddings and stored in the Vector Database
        under a new isolated collection: "BillingApp"

Step 4: A structured App Manifest is saved:
        Every widget and its screen coordinates, every action and where it leads

Step 5: BillingApp is added to the App Registry
        → From this point, all BillingApp users automatically get AI assistance
```

**Time taken:** Typically 2–10 minutes depending on codebase size.

---

### Flow 2 — User Asks a Question (Real-Time)

This is the core interaction that happens every time a user types a question.

```
User types: "How do I export this report as a PDF?"
               │
               │ SDK sends to Hub:
               │  {
               │    app: "BillingApp",
               │    user: "ravi.kumar",
               │    question: "How do I export this report as a PDF?",
               │    current_screen: "Report Dashboard",
               │    last_actions: ["opened report", "selected date range"]
               │  }
               ▼
         Hub: Session Manager loads Ravi's conversation history
               ▼
         Hub: Knowledge Base Engine searches BillingApp's KB
              → Finds: "Export feature: File > Export > Reports > PDF option"
              → Finds: "ExportDialog widget at toolbar, requires date range first"
              → Finds: "PDF export requires a report to be open"
               ▼
         Hub: Builds AI prompt:
              "You are the BillingApp assistant.
               User is on Report Dashboard, has selected a date range.
               Relevant info: [knowledge base results]
               Question: How do I export as PDF?"
               ▼
         Hub: AI Model generates response:
              "To export as PDF, follow these steps:
               Step 1: Click File in the top menu
               Step 2: Hover over Export
               Step 3: Click Report
               Step 4: In the dialog, select PDF format
               Step 5: Click Export
               Widget targets: menuFile, actionExport, actionReport,
                               dialogExport.formatPDF, dialogExport.btnExport"
               ▼
         Hub: Overlay Planner converts widget names to overlay instructions:
              Step 1: pulse_ring on menuFile → "Click File"
              Step 2: arrow_point on actionExport → "Click Export"
              Step 3: arrow_point on actionReport → "Click Report"
              Step 4: highlight_box on formatPDF → "Select PDF"
              Step 5: pulse_ring on btnExport → "Click Export"
               ▼
         Hub sends back to SDK:
              {
                chat_message: "Here's how to export as PDF:\n①Click File...",
                overlay_steps: [step1, step2, step3, step4, step5]
              }
               ▼
         SDK:
              → Chat panel shows all 5 steps as a list immediately
              → Overlay begins on Step 1: pulsing ring appears on File menu
               ▼
         User clicks File menu
               ▼
         SDK detects the action → advances overlay to Step 2
               ▼
         ... continues until Step 5 is complete ...
               ▼
         Overlay disappears. Chat shows: "✅ Done! Report exported."
```

**Total time for Hub response:** Typically 1–3 seconds with a local LLM.

---

### Flow 3 — Proactive Hint

This happens without the user asking anything.

```
SDK sends context update every few seconds:
  {
    app: "BillingApp",
    user: "meena.sharma",
    screen: "Invoice Creation Form",
    idle_ms: 15000,
    visible_errors: ["customerAddress: This field is required"]
  }
     │
     ▼
Hub: Proactive Engine evaluates rules:
  Rule matched: "idle > 10s AND form has visible errors"
     │
     ▼
Hub generates proactive message:
  "I noticed the Customer Address field is required and appears empty.
   This is likely preventing you from saving. Would you like me to show you?"
     │
     ▼
SDK shows hint bubble at bottom of chat panel.
     │
User clicks [Yes, show me]
     │
     ▼
Normal query flow begins, pointing to the Address field
```

---

### Flow 4 — Screenshot Consent Flow

```
User describes a problem that requires visual context to diagnose.
     │
Hub determines a screenshot would help.
     │
Hub sends consent request to SDK.
     │
SDK shows dialog on screen:
  ┌─────────────────────────────────────────────────────────┐
  │  🔒 AppAI wants to take a screenshot                    │
  │                                                         │
  │  To better help you, AppAI would like to see your       │
  │  current screen. This screenshot will:                  │
  │  • Only be used to answer this question                 │
  │  • NOT be saved to disk                                 │
  │  • NOT be sent to any external service                  │
  │                                                         │
  │  [Allow Once]  [Allow for this session]  [No, thanks]  │
  └─────────────────────────────────────────────────────────┘
     │
     ├── User clicks [Allow Once]
     │     → SDK takes screenshot (one frame)
     │     → Sends to Hub (in memory only)
     │     → Hub includes in AI prompt for visual analysis
     │     → Response generated
     │     → Screenshot discarded from memory
     │
     └── User clicks [No, thanks]
           → Hub proceeds without screenshot
           → Asks user to describe what they see in text
```

---

### Flow 5 — New App Registration After Code Update

```
Developer updates the BillingApp source code (new features added, UI changed).
     │
Developer runs:
  appai update --app-name "BillingApp" --source ./src
     │
Hub:
  → Re-parses changed source files only (incremental)
  → Updates the App Manifest with new/changed widgets
  → Re-embeds changed knowledge into the Vector Database
  → Old knowledge for unchanged parts is kept as-is
     │
Result: BillingApp's knowledge base is now up to date.
        All existing user sessions continue uninterrupted.
```

---

## 10. Deployment Modes

### Mode 1 — Local Hub (Single Machine)

**Best for:** Development teams, small offices (up to ~10 users), fully offline environments

```
Single Machine
 │
 ├── Billing App (Qt)    ─┐
 ├── Inventory App (Qt)  ─┤── connects to ──▶  AppAI Hub
 ├── HR Portal (Web)     ─┘                    (localhost:7788)
 │                                                    │
 │                                       ┌────────────┼────────────┐
 │                                       ▼            ▼            ▼
 │                                    Ollama       ChromaDB      SQLite
 │                                 (AI Model)  (Vector Store) (App Manifests)
 │                                (localhost:   (local files)  (local files)
 │                                  11434)
 │
 └── All data stays on this machine. Works completely offline.
```

**Startup:** IT admin installs AppAI Hub and Ollama on the machine. Apps automatically connect when launched.

---

### Mode 2 — Enterprise Server (Many Users, Many Apps)

**Best for:** Organizations with 50+ users, multiple offices, multiple applications

```
User Machine A    BillingApp ─────────┐
User Machine B    InventoryApp ────── ┤
User Machine C    BillingApp ─────── ┤── HTTPS ──▶  Company Network
User Machine D    HRPortal ───────── ┘
...N machines                                           │
                                                        ▼
                                              ┌──────────────────┐
                                              │  Load Balancer   │
                                              └────────┬─────────┘
                                                       │
                                        ┌──────────────┼──────────────┐
                                        ▼              ▼              ▼
                                  Hub Instance 1  Hub Instance 2  Hub Instance N
                                        │
                           ┌────────────┼────────────┐
                           ▼            ▼            ▼
                         vLLM         Qdrant        Redis
                      (GPU Server)  (Distributed  (Session
                                   Vector Store)    State)
```

**What changes for the apps?** Only one configuration line:
```yaml
# On each user's machine, in the app's config
hub_url: wss://appai.yourcompany.local   # instead of ws://localhost:7788
```
Everything else — the SDK, the app code — stays identical.

---

## 11. Scalability Plan

AppAI is designed to grow without requiring changes to the applications themselves.

| Stage | Scale | Typical Setup | Upgrade Path |
|---|---|---|---|
| **Stage 1 — Starter** | 1–3 apps, 1–10 users | Local Hub on one machine, Ollama | Add more apps via `appai register` |
| **Stage 2 — Growing** | 5–10 apps, 10–50 users | Dedicated server, Ollama or vLLM | Move Hub to server, apps point to server URL |
| **Stage 3 — Enterprise** | 10–30 apps, 50–500 users | Hub cluster, vLLM on GPU, Qdrant, Redis | Scale Hub instances behind load balancer |
| **Stage 4 — Large Scale** | 30+ apps, 500+ users | Distributed cluster | Add Hub instances and GPU nodes |

**Key scalability property:** The SDK in every application **never changes** between stages. Only the Hub deployment is upgraded.

### What Scales Automatically

- **App Knowledge Bases:** Each new app registered adds one isolated collection to the Vector Database — no impact on other apps
- **User Sessions:** The Session Manager handles thousands of concurrent sessions; Redis provides horizontal scaling
- **AI Model:** vLLM is specifically designed for high-concurrency AI inference on GPU hardware

---

## 12. Technology Stack

### Why These Technologies

| Technology | What It Is | Why Chosen |
|---|---|---|
| **Python + FastAPI** | Hub programming language & web framework | Best-in-class for AI/ML applications; fast async performance |
| **LangChain** | AI orchestration library | Provides RAG pipeline, prompt management, LLM abstraction |
| **Tree-sitter** | Source code parser | Multi-language AST parser — handles Qt, C++, Python, JavaScript, Vue, React in one tool |
| **ChromaDB** | Local vector database | Zero-configuration, runs on any machine, perfect for local hub mode |
| **Qdrant** | Distributed vector database | Enterprise-grade, supports clustering for large-scale deployments |
| **Redis** | In-memory session store | Industry standard for fast, scalable session management |
| **Ollama** | Local LLM runtime | Simplest way to run AI models locally; supports Llama3, Mistral, Qwen, Phi |
| **vLLM** | GPU-optimized LLM server | Best performance for concurrent multi-user inference on GPU hardware |
| **WebSocket** | Real-time communication protocol | Works for both Qt and web apps; low latency; bidirectional |
| **Qt C++ (SDK)** | Qt application SDK | Native performance; uses Qt's built-in accessibility API for widget discovery |
| **JavaScript (SDK)** | Web application SDK | Universal for all web frameworks; no dependencies required |

### Full Stack Table

| Layer | Local Mode | Enterprise Mode |
|---|---|---|
| Hub Language | Python 3.11+ | Same |
| Hub Framework | FastAPI + asyncio | Same |
| Real-time Comm. | WebSocket (ws://) | WebSocket over TLS (wss://) |
| AI Orchestration | LangChain | Same |
| Source Parser | Tree-sitter | Same |
| AI Model (Local) | Ollama | vLLM on GPU Server |
| AI Model (Cloud, opt-in) | OpenAI / Anthropic | Same |
| Embeddings | nomic-embed-text (via Ollama) | Same or OpenAI text-embedding-3 |
| Vector Store | ChromaDB | Qdrant |
| Structured Store | SQLite | PostgreSQL |
| Session Store | In-memory (Python) | Redis |
| Load Balancer | None needed | Nginx or HAProxy |
| TLS/SSL | Not required (localhost) | Required (company certificate) |
| Authentication | App API Key | JWT tokens + Role-Based Access Control |

---

## 13. Security & Privacy Model

### Data Classification

| Data Type | Where It Lives | Who Can Access It | Retention |
|---|---|---|---|
| App source code | Hub's local disk | Hub only (no users) | Persistent (used to rebuild KB) |
| App knowledge base (embeddings) | Vector Database (ChromaDB/Qdrant) | Hub only | Persistent |
| User conversation history | Session Manager (memory) | Hub only, for current session | Session-only (discarded at end) |
| Screenshot (if consented) | In Hub memory only | Hub + AI model, for one response | Immediately discarded after response |
| Private document (if consented) | Session-only KB | Hub only, for current session | Session-only (unless user says "remember") |
| User identity | Passed from host app's auth system | Hub session manager | Session-only |

### Data Never Leaves The Network (Unless Configured)

By default, with Ollama or vLLM as the AI backend:
- No user questions leave the premises
- No screenshots leave the premises
- No application source code leaves the premises
- No knowledge base data leaves the premises

If OpenAI or Claude is configured as the backend, the following data is sent to their API:
- The user's question
- Relevant excerpts from the knowledge base (not the full source code)
- The screenshot (if consented)

Users are warned about this at setup time and must confirm before a cloud backend is activated.

### Consent Architecture

```
CONSENT MANAGER (in SDK)
│
├── Screenshot requests
│    → Always shows dialog
│    → Three options: Allow Once | Allow for session | No
│    → Default: Allow Once (most restrictive)
│
├── Private file requests
│    → Always shows file picker dialog with explanation
│    → User must actively choose the file
│    → No silent access ever
│
├── Clipboard requests
│    → Always shows dialog
│    → Default: Never (disabled unless user consents)
│
└── Cloud LLM data transfer
     → Shown as a warning during initial Hub setup
     → Requires explicit admin confirmation
     → Stored in consent.yaml on the machine
```

### Application Isolation

Each application's data is completely isolated from every other application:
- Separate vector store collection per app
- Separate session namespace per app
- Hub cannot return App 2's knowledge in response to an App 1 query (enforced at the data layer)

### Authentication

| Mode | Auth Method |
|---|---|
| Local Hub | Apps connect via localhost; no external access possible |
| Enterprise Hub | Each app SDK uses a unique API key; users identified by the host app's own authentication system |

---

## 14. Design Principles

These are the non-negotiable rules that govern every decision in AppAI:

| # | Principle | What It Means |
|---|---|---|
| 1 | **Privacy-first** | Local LLM by default; cloud is always opt-in and clearly signalled |
| 2 | **Consent-first** | The agent never captures screenshots or reads private documents without explicit user approval |
| 3 | **Guide, don't act** | AppAI shows users where to click and what to do; it never clicks, fills, or navigates on their behalf |
| 4 | **App-isolated** | Each application's knowledge base and user sessions are completely isolated from all other applications |
| 5 | **Zero-friction integration** | Applications only add a thin SDK (one WebSocket client + one overlay renderer). No major refactoring required |
| 6 | **Always show all steps in chat** | Even in step-by-step overlay mode, the complete list of steps is always displayed in the chat panel upfront |
| 7 | **Horizontally scalable** | The same Hub codebase and same app SDK works from 1 app to 100+ apps by upgrading infrastructure, not code |
| 8 | **Backend-agnostic** | Switching AI models (Ollama → vLLM → OpenAI) requires changing one configuration value — nothing else |

---

## 15. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Local LLM quality insufficient for complex queries | Medium | High | Evaluate multiple models (Llama3, Mistral, Qwen) during PoC; have cloud fallback ready |
| R2 | Source code parsing misses features (incomplete extraction) | Medium | Medium | Comprehensive parser test suite; allow manual KB corrections via admin CLI |
| R3 | Widget ID resolution fails (overlay points to wrong element) | Medium | Medium | Fallback to text description ("Click the blue Export button in the top-right") when coordinate resolution fails |
| R4 | Slow AI response time with local LLM | High (initially) | Medium | Use smaller quantized models (Q4); implement streaming responses; show "thinking..." indicator |
| R5 | Users find proactive hints intrusive | Medium | Low | Conservative trigger thresholds; easy dismiss; user can disable proactive hints entirely in settings |
| R6 | App code changes break knowledge base | High | Medium | Implement incremental re-parsing on code update; version-aware KB; admin notified when re-registration needed |
| R7 | SDK integration breaks existing app stability | Low | High | SDK runs in a separate thread; any SDK crash is isolated and does not affect the host app |
| R8 | User data leakage between app sessions | Very Low | Very High | Enforced at data layer: session namespace = (user_id + app_id); Hub validates app_id on every request |
| R9 | vLLM GPU server unavailable (enterprise) | Low | Medium | Automatic fallback to Ollama on the local machine if Hub server unreachable |

---

## 16. Team & Roles

### Core Development Team

| Role | Count | Responsibilities |
|---|---|---|
| **Backend Engineer (Hub)** | 2 | AppAI Hub, LLM Router, Knowledge Base Engine, Session Manager, Proactive Engine |
| **Qt SDK Engineer** | 1 | Qt C++ SDK (WebSocket client, overlay QWidget, consent dialogs, chat panel) |
| **Web SDK Engineer** | 1 | JavaScript SDK (WebSocket client, overlay div, consent dialogs, chat panel) |
| **AI/ML Engineer** | 1 | Source code parser (Tree-sitter), RAG pipeline, prompt engineering, LLM evaluation |
| **DevOps / Infra** | 1 | Hub deployment, Ollama/vLLM setup, Qdrant, Redis, monitoring |
| **QA Engineer** | 1 | Integration testing across apps, overlay accuracy testing, consent flow testing |

### Project Oversight

| Role | Responsibilities |
|---|---|
| **Project Manager** | Sprint planning, milestone tracking, stakeholder communication, risk monitoring |
| **Product Owner** | Feature prioritization, user story definition, acceptance criteria |
| **Solution Architect** | Technical governance, design reviews, cross-team integration sign-off |

---

## 17. Milestones & Delivery Plan

### Phase 1 — Foundation (Weeks 1–4)
**Goal:** Working end-to-end pipeline with one test application

| Task | Owner | Duration |
|---|---|---|
| AppAI Hub skeleton (WebSocket server, App Registry, Session Manager) | Backend | 2 weeks |
| LLM Router (Ollama + OpenAI + Claude) | Backend / AI | 1 week |
| Qt SDK — WebSocket client + basic chat panel | Qt SDK | 2 weeks |
| Basic RAG pipeline (LangChain + ChromaDB) | AI/ML | 1 week |
| End-to-end test: one Qt app registered, user asks question, gets answer | All | 1 week |

**Milestone:** User can ask a question in a test Qt app and get a relevant AI answer from the app's knowledge base.

---

### Phase 2 — Knowledge Base & Source Parsing (Weeks 5–8)
**Goal:** Deep source code understanding for Qt and web apps

| Task | Owner | Duration |
|---|---|---|
| Source code parser (Qt .ui, .qml, .cpp, .py) | AI/ML | 2 weeks |
| Source code parser (React .jsx/.tsx, Vue .vue, HTML) | AI/ML | 1 week |
| App Manifest builder + SQLite storage | Backend | 1 week |
| External document ingestion (PDF, HTML, Markdown) | AI/ML | 1 week |
| Incremental re-parsing (update on code change) | Backend | 1 week |

**Milestone:** Registering a real Qt application produces a rich, accurate knowledge base covering all features.

---

### Phase 3 — Visual Overlay System (Weeks 9–12)
**Goal:** Step-by-step visual guidance on live application window

| Task | Owner | Duration |
|---|---|---|
| Qt transparent overlay window (QWidget-based) | Qt SDK | 2 weeks |
| Overlay styles: pulse ring, arrow, spotlight, drop zone, step badge | Qt SDK | 1 week |
| Overlay Planner (widget name → coordinates via QAccessible) | Backend + Qt SDK | 1 week |
| Step advance logic (detect user action → move to next step) | Qt SDK | 1 week |
| Web JS overlay (div-based, CSS animations) | Web SDK | 2 weeks |
| Toggle: step-by-step ↔ all-steps-at-once | Qt SDK + Web SDK | 1 week |

**Milestone:** User asks a question in a real Qt app and visual overlays guide them step-by-step to complete the task.

---

### Phase 4 — Proactive Intelligence (Weeks 13–16)
**Goal:** Agent acts without being asked

| Task | Owner | Duration |
|---|---|---|
| Live context tracker (current screen, idle time, error state) | Qt SDK + Backend | 1 week |
| Proactive trigger rule engine | Backend | 1 week |
| Hint UI (non-intrusive bubble in chat panel) | Qt SDK + Web SDK | 1 week |
| Drag-file detection + instant drop zone overlay | Qt SDK | 1 week |
| User preference: disable/configure proactive hints | Qt SDK + Backend | 1 week |

**Milestone:** Agent proactively offers help when user is idle on a form, gets an error, or drags a file.

---

### Phase 5 — Enterprise & Polish (Weeks 17–20)
**Goal:** Production-ready, multi-user deployment

| Task | Owner | Duration |
|---|---|---|
| vLLM integration and testing | Backend / DevOps | 1 week |
| Enterprise authentication (JWT + API keys) | Backend | 1 week |
| Qdrant integration (replaces ChromaDB for enterprise) | Backend | 1 week |
| Redis session store (replaces in-memory for enterprise) | Backend | 1 week |
| Admin CLI / dashboard (register apps, view status) | Backend | 1 week |
| Performance tuning, load testing | DevOps + QA | 1 week |
| Documentation and deployment runbook | All | 1 week |

**Milestone:** AppAI Hub deployed on enterprise server, serving 10 applications and 50+ concurrent users with acceptable response times.

---

### Summary Timeline

```
Week:   1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17   18   19   20
        ├────────────────────┤├───────────────────────┤├──────────────────────┤├─────────────────┤├────────────────────┤
Phase:       Phase 1                Phase 2                  Phase 3               Phase 4            Phase 5
             Foundation           Knowledge Base           Visual Overlay         Proactive        Enterprise
             & Core Hub           & Source Parser           & Guidance          Intelligence        & Polish
```

---

## 18. Success Metrics

### User Experience Metrics

| Metric | Target | How Measured |
|---|---|---|
| Query response time (local LLM) | < 3 seconds | Hub latency logging |
| Overlay accuracy | > 95% correct widget highlighting | QA test suite across registered apps |
| Proactive hint relevance | > 80% rated "helpful" by users | In-app feedback button |
| User task completion rate with AppAI | > 90% for guided tasks | Session completion tracking |

### Adoption Metrics

| Metric | Target | Timeline |
|---|---|---|
| Apps registered on AppAI Hub | 10 apps | End of Phase 5 |
| Active users per day | 50+ | 1 month post-launch |
| Queries answered per day | 200+ | 1 month post-launch |
| Support tickets reduced | 30% reduction | 3 months post-launch |

### Technical Metrics

| Metric | Target |
|---|---|
| SDK integration time per new Qt app | < 1 day |
| App registration time (source parsing) | < 10 minutes for a 100k-line codebase |
| Hub uptime | > 99.5% |
| Concurrent user sessions | 100+ on enterprise setup |

---

## 19. Glossary

| Term | Plain-English Definition |
|---|---|
| **AppAI Hub** | The central AI service that runs on a server or machine and powers all applications' AI assistant capabilities |
| **AppAI SDK** | A small software package added to each application. It connects the app to the Hub and renders overlays and the chat panel |
| **Visual Overlay** | Transparent animated graphics drawn on top of the application window to guide users — like highlighting, arrows, and numbered steps |
| **Knowledge Base (KB)** | A searchable AI database built from an application's source code. Each application has its own isolated knowledge base |
| **RAG (Retrieval-Augmented Generation)** | The technique of searching a knowledge base for relevant information, then including that information in the AI prompt to get accurate, grounded answers |
| **Vector Database** | A special type of database that stores knowledge in a way that allows searching by meaning (not just keywords). ChromaDB and Qdrant are the two used in this system |
| **Embedding** | The process of converting text (like a widget label or a paragraph from a manual) into a numerical format that a vector database can search |
| **LLM (Large Language Model)** | The AI model that understands and generates natural language. Examples: Llama3, Mistral (local), GPT-4o (OpenAI), Claude (Anthropic) |
| **Ollama** | A tool that makes it easy to run AI models locally on a standard machine without a GPU or internet connection |
| **vLLM** | A high-performance tool for running AI models on a GPU server, optimized for handling many users simultaneously |
| **App Manifest** | A structured document listing every screen, button, menu, form, and action in an application — with their screen coordinates. Created by the source code parser |
| **Session** | An individual user's conversation with AppAI for a specific application. User A's session is completely separate from User B's session |
| **Proactive Engine** | The part of AppAI that watches what users are doing and offers help without being asked |
| **Source Code Parser** | The component that reads the application's code files and extracts knowledge about the UI, features, and workflows |
| **Tree-sitter** | The technology used to read and understand source code files in multiple programming languages (C++, Python, JavaScript, etc.) |
| **WebSocket** | A communication protocol that allows the app (SDK) and the Hub to exchange messages in real time — like a persistent phone call |
| **Sidecar** | The pattern of running a supporting service (the Hub) as a separate process alongside the main application |
| **Hub & Spoke** | The architecture where one central Hub serves multiple applications, like a wheel hub serving multiple spokes |
| **Consent-first** | The design principle that the AI must always ask the user before performing any sensitive action (screenshot, file read, etc.) |
| **Quantized model** | A compressed version of an AI model that runs faster and uses less memory, with minimal quality reduction — used for local LLM deployment |
