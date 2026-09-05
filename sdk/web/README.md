# AppAI Web SDK

Embed AppAI into any web application with three script tags. The SDK opens a WebSocket connection to the AppAI Hub, renders an in-page chat sidebar, draws visual step-by-step overlay guidance, and requests user consent before any screen capture or document access.

---

## Quick Start

### 1. Add the SDK to your HTML page

```html
<!-- 1. Stylesheet (optional — styles are injected automatically if omitted) -->
<link rel="stylesheet" href="/path/to/appai/styles.css">

<!-- 2. Overlay engine and consent dialogs -->
<script src="/path/to/appai/overlay.js"></script>
<script src="/path/to/appai/consent.js"></script>

<!-- 3. Main SDK (exposes window.AppAI) — must be last -->
<script src="/path/to/appai/appai-sdk.js"></script>
```

Add the three tags just before `</body>`. The SDK is a self-contained IIFE — no bundler, no npm required.

---

### 2. Initialise the SDK

Call `AppAI.init()` once the page has loaded:

```html
<script>
  document.addEventListener('DOMContentLoaded', function () {
    AppAI.init({
      appId:    'my-billing-app',   // your application identifier
      userId:   'user_4291',        // unique id for the current user
      userName: 'Alice Johnson',    // displayed in the chat header
    });
  });
</script>
```

A chat sidebar appears on the right side of the page and connects to the Hub automatically.

---

### 3. Tell AppAI when the screen changes

Call `AppAI.setScreen()` whenever the user navigates to a different view so the assistant can provide contextually relevant help:

```javascript
// Plain JavaScript
AppAI.setScreen('Dashboard');

// React — in your router's onRouteChange callback
useEffect(() => {
  AppAI.setScreen(routeName);
}, [routeName]);

// Vue — in the router's afterEach hook
router.afterEach((to) => {
  AppAI.setScreen(to.name);
});

// Angular — in your router events subscription
router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(e => {
  AppAI.setScreen(e.urlAfterRedirects);
});
```

---

### 4. Connect to an enterprise / self-hosted Hub

Point the SDK at your own Hub instance using the `hubUrl` option:

```javascript
AppAI.init({
  appId:   'my-app',
  userId:  'user123',
  hubUrl:  'wss://appai.company.local',   // secure WebSocket
});
```

The URL scheme `ws://` works for local development; use `wss://` in production.

---

### 5. Send a query programmatically

Trigger a query from your own UI elements (e.g., a help button):

```javascript
document.getElementById('help-btn').addEventListener('click', () => {
  AppAI.sendQuery('How do I generate a monthly report?');
});
```

---

## Configuration Reference

Pass these options to `AppAI.init(config)`:

| Option | Type | Default | Description |
|---|---|---|---|
| `appId` | `string` | **required** | Unique identifier for your application registered with the Hub |
| `userId` | `string` | **required** | Unique identifier for the current logged-in user |
| `userName` | `string` | `'You'` | Display name shown in the chat header subtitle |
| `hubUrl` | `string` | `'ws://localhost:7788'` | WebSocket base URL of the AppAI Hub (no trailing slash) |
| `role` | `string` | `'app_user'` | User role hint sent to the Hub for personalisation |

---

## Public API

| Method | Description |
|---|---|
| `AppAI.init(config)` | Initialise the SDK. Returns the `AppAISDK` instance. |
| `AppAI.setScreen(name)` | Notify AppAI of the current screen / route name. |
| `AppAI.sendQuery(text)` | Programmatically submit a query to the assistant. |

---

## Hub Message Protocol

The SDK communicates with the Hub over WebSocket using JSON messages.

### Outbound (SDK → Hub)

| `type` | Key fields | Description |
|---|---|---|
| `register_session` | `app_id`, `user_id`, `user_name`, `role` | Sent immediately after connection |
| `query` | `session_id`, `text`, `screen`, `url`, `title` | User question |
| `context_update` | `session_id`, `url`, `title`, `screen`, `idle_ms`, `visible_errors` | Sent every 3 s |
| `screen_change` | `session_id`, `screen`, `url`, `title` | Sent on `setScreen()` call |
| `consent_response` | `granted` (bool), `scope` (`once`\|`session`) | Reply to screenshot consent request |
| `document_content` | `filename`, `mime_type`, `content` | File content after user picks a document |
| `hint_accepted` | `message_id` | User clicked "Yes, show me" on a hint bubble |
| `hint_dismissed` | `message_id` | User clicked "Not now" on a hint bubble |
| `feedback` | `session_id`, `message_id`, `rating`, `reason` | Negative feedback (👎) on an assistant message |
| `guidance_completed` | `session_id` | All overlay steps finished |

### Inbound (Hub → SDK)

| `type` | Key fields | Description |
|---|---|---|
| `session_created` | `session_id` | Hub confirms session; SDK stores the ID |
| `response` | `message`, `steps[]`, `overlay_mode`, `message_id` | Assistant reply with optional guided steps |
| `proactive_hint` | `message`, `message_id` | Non-intrusive hint bubble shown in chat |
| `consent_request` | `consent_type` (`screenshot`\|`document`) | Hub asks the user for permission |
| `error` | `message` | Error description shown in chat |

### `steps[]` object shape

```jsonc
{
  "label":       "Click the Export button",   // short action label
  "description": "Click the blue Export button in the toolbar",
  "target_id":   "export-btn",                // element id or CSS selector
  "style":       "arrow_point",               // overlay style (see below)
}
```

---

## Overlay Styles

The `style` field of a step controls how the target element is highlighted:

| Style | Visual | Best for |
|---|---|---|
| `pulse_ring` | Animated pulsing blue circle | Icon buttons, FABs |
| `glow_box` | Glowing blue border rectangle | Form fields, cards |
| `arrow_point` | Bobbing downward arrow | Menu items, links |
| `drop_zone` | Dashed green border + tint | File upload areas |
| `spotlight` | Dark overlay with cut-out | Focused task guidance |
| `step_badge` | Numbered blue circle badge | Multi-step sequences |

---

## Responsive Behaviour

| Screen width | Chat panel | Float button |
|---|---|---|
| ≥ 768 px | Fixed 380px right sidebar, always visible | Hidden |
| < 768 px | Hidden by default (slides in from right) | Shown (bottom-right) |

---

## File Structure

```
sdk/web/
├── appai-sdk.js   Main SDK — IIFE, exposes window.AppAI
├── overlay.js     AppAIOverlay — visual step guidance engine
├── consent.js     AppAIConsent — screenshot & document consent dialogs
├── styles.css     All CSS for chat panel, overlays, and modals
└── README.md      This file
```

---

## Browser Support

| Browser | Minimum version |
|---|---|
| Chrome / Edge | 88+ |
| Firefox | 85+ |
| Safari | 14+ |
| Mobile Safari (iOS) | 14.5+ |

The SDK uses `WebSocket`, `fetch` (not used directly), `requestAnimationFrame`, `canvas`, and CSS custom properties — all available in any modern browser without polyfills.

---

## Security Notes

- **No data leaves without consent.** Screenshots and documents are only sent after explicit user approval via the consent dialog.
- **XSS protection.** All user-supplied text is escaped before insertion into the DOM. Hub `message` fields are rendered with a minimal safe-Markdown parser.
- **Content Security Policy.** If your app has a strict CSP, add your Hub's WebSocket URL to `connect-src` and `wss:` as appropriate.

---

## License

Copyright © 2026 AppAI. All rights reserved.
