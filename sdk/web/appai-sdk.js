/**
 * AppAI Web SDK — appai-sdk.js
 *
 * Self-contained IIFE. Exposes window.AppAI global.
 * Connects to the AppAI Hub via WebSocket, renders a chat sidebar,
 * draws visual guidance overlays, manages consent dialogs, and
 * streams live context updates every 3 seconds.
 *
 * Dependencies (include BEFORE this file):
 *   — overlay.js  (AppAIOverlay class)
 *   — consent.js  (AppAIConsent class)
 *   — styles.css  (optional – styles injected automatically if absent)
 *
 * Quick start:
 *   AppAI.init({ appId: 'myapp', userId: 'user123', userName: 'Alice' });
 */

(function () {
  'use strict';

  // =========================================================================
  // Utility helpers
  // =========================================================================

  /**
   * Generates a short random ID for messages and sessions.
   * @returns {string}
   */
  function uid() {
    return Math.random().toString(36).slice(2, 10);
  }

  /**
   * Returns a formatted HH:MM timestamp string for the current local time.
   * @returns {string}
   */
  function timeLabel() {
    const d = new Date();
    return d.getHours().toString().padStart(2, '0') + ':' +
           d.getMinutes().toString().padStart(2, '0');
  }

  /**
   * Escapes < > & characters to prevent XSS when inserting user-supplied text.
   * @param {string} str
   * @returns {string}
   */
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /**
   * Simple Markdown → HTML converter for assistant message bubbles.
   * Supports: **bold**, *italic*, `code`, newlines → <br>.
   * @param {string} text
   * @returns {string}
   */
  function markdownToHtml(text) {
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g,     '<em>$1</em>');
    html = html.replace(/`(.+?)`/g,       '<code style="background:#f3f4f6;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // =========================================================================
  // AppAISDK class
  // =========================================================================

  class AppAISDK {
    /**
     * @param {Object} config
     * @param {string} config.appId    - Your application identifier
     * @param {string} config.userId   - Unique user identifier
     * @param {string} [config.hubUrl] - WebSocket base URL (default: ws://localhost:7788)
     * @param {string} [config.userName] - Display name shown in the chat header
     * @param {string} [config.role]   - User role hint (default: 'app_user')
     */
    constructor(config) {
      this.config = {
        hubUrl:   'ws://localhost:7788',
        role:     'app_user',
        userName: 'You',
        ...config,
      };

      /** @type {string|null} Session ID received from the Hub after registration */
      this.sessionId = null;

      /** @type {WebSocket|null} Active WebSocket connection */
      this.ws = null;

      /** @type {AppAIOverlay|null} Overlay engine instance */
      this.overlay = null;

      /** @type {AppAIConsent|null} Consent dialog manager */
      this.consent = null;

      /** @type {HTMLElement|null} Chat panel root element */
      this.chatPanel = null;

      /** @type {HTMLElement|null} Messages container */
      this._messagesEl = null;

      /** @type {HTMLElement|null} Status dot in header */
      this._statusDot = null;

      /** @type {HTMLElement|null} Floating toggle button (mobile) */
      this._floatBtn = null;

      /** @type {number} Current step index during guided walk-through */
      this.currentStep = 0;

      /** @type {Array<Object>} Steps received from the Hub */
      this.overlaySteps = [];

      /** @type {number|null} setInterval handle for context stream */
      this.contextInterval = null;

      /** @type {string} Current screen name (set by host app via setScreen()) */
      this.lastScreen = '';

      /** @type {number} Milliseconds elapsed since last user interaction */
      this.idleTimer = 0;

      /** @type {number|null} setInterval handle for idle tracking */
      this.idleInterval = null;

      /** @type {number} WebSocket reconnect attempt count */
      this._reconnectCount = 0;

      /** @type {number|null} setTimeout handle for reconnect delay */
      this._reconnectTimeout = null;

      /** @type {boolean} Prevents concurrent reconnect attempts */
      this._intentionalClose = false;

      /** @type {boolean} Whether "session allowed" was granted for screenshots */
      this._screenshotSessionAllowed = false;

      // Reset idle timer on any user interaction
      this._resetIdle = () => { this.idleTimer = 0; };
    }

    // =========================================================================
    // Initialisation
    // =========================================================================

    /**
     * init()
     *
     * Entry point. Call once after loading the SDK.
     * 1. Ensures styles.css is linked.
     * 2. Instantiates overlay and consent helpers.
     * 3. Builds the chat panel.
     * 4. Opens the WebSocket connection.
     * 5. Starts context streaming + idle tracking.
     */
    init() {
      this._injectStyles();
      this._initHelpers();
      this._buildChatPanel();
      this._connectWebSocket();
      this._startContextStream();
      this._startIdleTracking();
    }

    /**
     * _injectStyles()
     *
     * Links styles.css relative to this script tag, or injects minimal inline
     * styles when the CSS file cannot be resolved.
     */
    _injectStyles() {
      // If already linked (host loaded styles.css), skip
      if (document.querySelector('link[href*="appai"]') ||
          document.getElementById('appai-sdk-styles')) return;

      // Try to resolve styles.css from the same directory as this script
      const thisScript = document.querySelector('script[src*="appai-sdk"]');
      if (thisScript) {
        const src = thisScript.getAttribute('src');
        const dir = src.substring(0, src.lastIndexOf('/') + 1);
        const link = document.createElement('link');
        link.rel  = 'stylesheet';
        link.id   = 'appai-sdk-styles';
        link.href = dir + 'styles.css';
        document.head.appendChild(link);
      }
    }

    /**
     * _initHelpers()
     *
     * Creates AppAIOverlay and AppAIConsent instances.
     * Falls back gracefully if the classes aren't on the page.
     */
    _initHelpers() {
      if (typeof AppAIOverlay !== 'undefined') {
        this.overlay = new AppAIOverlay();
        this.overlay.init();
      } else {
        console.warn('[AppAI] overlay.js not found — overlay features disabled.');
      }

      if (typeof AppAIConsent !== 'undefined') {
        this.consent = new AppAIConsent();
      } else {
        console.warn('[AppAI] consent.js not found — consent dialogs disabled.');
      }
    }

    // =========================================================================
    // WebSocket
    // =========================================================================

    /**
     * _connectWebSocket()
     *
     * Opens a WebSocket to {hubUrl}/ws/{appId}/{userId}.
     * On open:  sends a register_session message.
     * On message: routes to _handleMessage().
     * On close:   schedules a reconnect after 3 s (unless intentional).
     */
    _connectWebSocket() {
      const { hubUrl, appId, userId, userName, role } = this.config;
      const url = `${hubUrl}/ws/${appId}/${userId}`;

      this._setStatus('connecting');

      try {
        this.ws = new WebSocket(url);
      } catch (err) {
        console.error('[AppAI] WebSocket construction failed:', err);
        this._scheduleReconnect();
        return;
      }

      this.ws.onopen = () => {
        console.log('[AppAI] Connected to Hub.');
        this._reconnectCount = 0;
        this._setStatus('connected');

        // Register this session with the Hub
        this._send({
          type:      'register_session',
          app_id:    appId,
          user_id:   userId,
          user_name: userName,
          role:      role,
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._handleMessage(data);
        } catch (err) {
          console.error('[AppAI] Failed to parse message:', err, event.data);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('[AppAI] WebSocket error:', err);
        this._setStatus('disconnected');
      };

      this.ws.onclose = (event) => {
        console.warn(`[AppAI] WebSocket closed (code ${event.code}).`);
        this._setStatus('disconnected');
        if (!this._intentionalClose) {
          this._scheduleReconnect();
        }
      };
    }

    /**
     * _scheduleReconnect()
     *
     * Waits 3 seconds then tries to re-open the WebSocket.
     * Uses exponential back-off up to 30 s.
     */
    _scheduleReconnect() {
      if (this._reconnectTimeout) return;
      const delay = Math.min(3000 * Math.pow(1.5, this._reconnectCount), 30000);
      this._reconnectCount++;
      console.log(`[AppAI] Reconnecting in ${Math.round(delay / 1000)}s…`);

      this._reconnectTimeout = setTimeout(() => {
        this._reconnectTimeout = null;
        this._connectWebSocket();
      }, delay);
    }

    /**
     * _send(payload)
     *
     * JSON-serialises payload and sends it over the WebSocket.
     * Silently discards the message if the socket is not open.
     *
     * @param {Object} payload
     */
    _send(payload) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(payload));
      }
    }

    /**
     * _handleMessage(data)
     *
     * Routes inbound Hub messages to the appropriate handler.
     *
     * Supported types:
     *   session_created  → saves sessionId, shows welcome message
     *   response         → renders assistant reply + overlay steps
     *   proactive_hint   → shows a non-intrusive hint bubble
     *   consent_request  → triggers a consent dialog
     *   error            → shows error in chat
     *
     * @param {Object} data - Parsed JSON from the Hub
     */
    _handleMessage(data) {
      switch (data.type) {

        case 'session_created':
          this.sessionId = data.session_id;
          console.log('[AppAI] Session created:', this.sessionId);
          this._addChatMessage('assistant',
            '👋 Hi! I\'m AppAI, your in-app assistant. How can I help you today?',
            uid()
          );
          break;

        case 'response':
          // Remove typing indicator if present
          this._removeTypingIndicator();

          // Render the main reply text
          if (data.message) {
            this._addChatMessage('assistant', data.message, data.message_id || uid());
          }

          // Render steps list if provided
          if (data.steps && data.steps.length > 0) {
            this._showStepList(data.steps);
            // Start overlay guidance
            const mode = data.overlay_mode || 'step_by_step';
            this._startOverlay(data.steps, mode);
          }
          break;

        case 'proactive_hint':
          if (data.message) {
            this._addChatMessage('hint', data.message, data.message_id || uid());
          }
          break;

        case 'consent_request':
          this._handleConsentRequest(data);
          break;

        case 'error':
          this._removeTypingIndicator();
          this._addChatMessage('assistant',
            `⚠️ ${data.message || 'Something went wrong. Please try again.'}`,
            uid()
          );
          break;

        default:
          console.warn('[AppAI] Unknown message type:', data.type, data);
      }
    }

    /**
     * _handleConsentRequest(data)
     *
     * Routes a consent_request from the Hub to the appropriate dialog.
     * Supported consent_type: 'screenshot' | 'document'
     *
     * @param {Object} data
     */
    _handleConsentRequest(data) {
      if (!this.consent) return;

      if (data.consent_type === 'screenshot') {
        // If the user already allowed for this session, proceed immediately
        if (this._screenshotSessionAllowed) {
          this._send({ type: 'consent_response', granted: true, scope: 'session' });
          return;
        }

        this.consent.showScreenshotConsent(
          /* onAllow */        () => this._send({ type: 'consent_response', granted: true,  scope: 'once' }),
          /* onAllowSession */ () => {
            this._screenshotSessionAllowed = true;
            this._send({ type: 'consent_response', granted: true, scope: 'session' });
          },
          /* onDeny */         () => this._send({ type: 'consent_response', granted: false })
        );

      } else if (data.consent_type === 'document') {
        this.consent.showDocumentConsent(
          /* onChooseFile */ (file) => {
            const reader = new FileReader();
            reader.onload = (e) => {
              this._send({
                type:      'document_content',
                filename:  file.name,
                mime_type: file.type,
                content:   e.target.result,
              });
            };
            reader.readAsText(file);
          },
          /* onDeny */ () => this._send({ type: 'consent_response', granted: false })
        );
      }
    }

    // =========================================================================
    // Query + Context
    // =========================================================================

    /**
     * _sendQuery(text)
     *
     * Sends a user question to the Hub and shows a typing indicator.
     *
     * @param {string} text - User's message text
     */
    _sendQuery(text) {
      if (!text || !text.trim()) return;
      const trimmed = text.trim();

      // Show the user's message in the chat
      this._addChatMessage('user', trimmed, uid());

      // Show typing indicator
      this._showTypingIndicator();

      // Clear previous overlay guidance
      if (this.overlay) this.overlay.clearAll();
      this.overlaySteps = [];
      this.currentStep  = 0;

      this._send({
        type:       'query',
        session_id: this.sessionId,
        text:       trimmed,
        screen:     this.lastScreen,
        url:        window.location.href,
        title:      document.title,
      });
    }

    /**
     * _startContextStream()
     *
     * Sends a context_update message to the Hub every 3 seconds with:
     *   - Current URL and page title
     *   - Current screen name (set by the host app)
     *   - Idle time in milliseconds
     *   - Array of visible error messages detected on the page
     */
    _startContextStream() {
      if (this.contextInterval) clearInterval(this.contextInterval);

      this.contextInterval = setInterval(() => {
        // Only send if connected
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        const ctx = {
          type:           'context_update',
          session_id:     this.sessionId,
          url:            window.location.href,
          title:          document.title,
          screen:         this.lastScreen,
          idle_ms:        this.idleTimer,
          visible_errors: this._detectErrors(),
          timestamp:      new Date().toISOString(),
        };

        this._send(ctx);
      }, 3000);
    }

    /**
     * _startIdleTracking()
     *
     * Increments idleTimer every second and resets it on any user interaction.
     */
    _startIdleTracking() {
      // Listen for any interaction to reset idle counter
      ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart'].forEach(evt => {
        document.addEventListener(evt, this._resetIdle, { passive: true });
      });

      if (this.idleInterval) clearInterval(this.idleInterval);
      this.idleInterval = setInterval(() => {
        this.idleTimer += 1000;
      }, 1000);
    }

    /**
     * _detectErrors()
     *
     * Scans the page for elements that typically contain error messages and
     * returns their visible text content.
     *
     * Checks: .error, .alert-danger, [role=alert], .toast-error,
     *         .notification-error, [data-testid*="error"]
     *
     * @returns {string[]} Array of error text strings (max 5)
     */
    _detectErrors() {
      const selectors = [
        '.error',
        '.alert-danger',
        '[role="alert"]',
        '.toast-error',
        '.notification-error',
        '[data-testid*="error"]',
        '.field-error',
        '.form-error',
      ];

      const errors = [];

      selectors.forEach(sel => {
        try {
          document.querySelectorAll(sel).forEach(el => {
            const text = el.innerText?.trim();
            if (text && text.length > 0 && text.length < 300) {
              errors.push(text);
            }
          });
        } catch (_) { /* skip invalid selectors */ }
      });

      // Deduplicate and limit
      return [...new Set(errors)].slice(0, 5);
    }

    // =========================================================================
    // Chat Panel DOM
    // =========================================================================

    /**
     * _buildChatPanel()
     *
     * Creates the entire chat sidebar DOM and appends it to document.body.
     * Structure:
     *   .appai-chat-panel
     *     .appai-chat-header
     *     .appai-messages
     *     .appai-input-area
     *
     * Also creates the floating toggle button for mobile / collapsed state.
     */
    _buildChatPanel() {
      /* ── Root panel ── */
      const panel = document.createElement('div');
      panel.className = 'appai-chat-panel';
      panel.id = 'appai-chat-panel';

      /* ── Header ── */
      const header = this._buildHeader();
      panel.appendChild(header);

      /* ── Messages ── */
      const messages = document.createElement('div');
      messages.className = 'appai-messages';
      messages.id = 'appai-messages';
      panel.appendChild(messages);
      this._messagesEl = messages;

      /* ── Input area ── */
      const inputArea = this._buildInputArea();
      panel.appendChild(inputArea);

      document.body.appendChild(panel);
      this.chatPanel = panel;

      /* ── Floating toggle button ── */
      const floatBtn = document.createElement('button');
      floatBtn.className = 'appai-float-btn';
      floatBtn.title = 'Open AppAI';
      floatBtn.innerHTML = '💬';
      floatBtn.addEventListener('click', () => this._togglePanel(true));
      document.body.appendChild(floatBtn);
      this._floatBtn = floatBtn;

      // Show float button on mobile by default
      this._applyResponsiveState();
      window.addEventListener('resize', () => this._applyResponsiveState());
    }

    /**
     * _buildHeader()
     *
     * Creates the blue gradient header with logo, title, status dot,
     * and a collapse (×) button.
     *
     * @returns {HTMLElement}
     */
    _buildHeader() {
      const header = document.createElement('div');
      header.className = 'appai-chat-header';

      /* Left section: logo + title stack */
      const left = document.createElement('div');
      left.className = 'appai-chat-header-left';

      const logo = document.createElement('div');
      logo.className = 'appai-logo';
      logo.innerHTML = '🤖';

      const titles = document.createElement('div');

      const titleEl = document.createElement('div');
      titleEl.className = 'appai-header-title';
      titleEl.textContent = 'AppAI Assistant';

      const subtitleEl = document.createElement('div');
      subtitleEl.className = 'appai-header-subtitle';
      subtitleEl.textContent = this.config.userName
        ? `Helping ${this.config.userName}`
        : 'Powered by AppAI Hub';

      titles.appendChild(titleEl);
      titles.appendChild(subtitleEl);
      left.appendChild(logo);
      left.appendChild(titles);

      /* Right section: status dot + close button */
      const actions = document.createElement('div');
      actions.className = 'appai-header-actions';

      const dot = document.createElement('div');
      dot.className = 'appai-status-dot connecting';
      dot.title = 'Connecting…';
      this._statusDot = dot;

      const closeBtn = document.createElement('button');
      closeBtn.className = 'appai-icon-btn';
      closeBtn.title = 'Minimise';
      closeBtn.innerHTML = '✕';
      closeBtn.addEventListener('click', () => this._togglePanel(false));

      actions.appendChild(dot);
      actions.appendChild(closeBtn);

      header.appendChild(left);
      header.appendChild(actions);
      return header;
    }

    /**
     * _buildInputArea()
     *
     * Creates the bottom bar with a text input and a Send button.
     * Pressing Enter (without Shift) also submits the query.
     *
     * @returns {HTMLElement}
     */
    _buildInputArea() {
      const area = document.createElement('div');
      area.className = 'appai-input-area';

      const input = document.createElement('input');
      input.type        = 'text';
      input.className   = 'appai-input';
      input.placeholder = 'Ask me anything…';
      input.maxLength   = 500;
      input.id          = 'appai-query-input';

      const sendBtn = document.createElement('button');
      sendBtn.className = 'appai-send-btn';
      sendBtn.title     = 'Send';
      sendBtn.innerHTML = '&#10148;'; // ➤

      const submit = () => {
        const text = input.value.trim();
        if (!text) return;
        this._sendQuery(text);
        input.value = '';
        input.focus();
      };

      sendBtn.addEventListener('click', submit);
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          submit();
        }
      });

      area.appendChild(input);
      area.appendChild(sendBtn);
      return area;
    }

    // =========================================================================
    // Chat messages
    // =========================================================================

    /**
     * _addChatMessage(role, text, messageId)
     *
     * Appends a message bubble to the messages container and scrolls to bottom.
     *
     * @param {'user'|'assistant'|'hint'} role
     * @param {string} text       - Message text (Markdown supported for assistant)
     * @param {string} messageId  - Unique ID used for feedback tracking
     */
    _addChatMessage(role, text, messageId) {
      if (!this._messagesEl) return;

      const wrapper = document.createElement('div');
      wrapper.className = `appai-message appai-message-${role}`;
      wrapper.dataset.messageId = messageId;

      const bubble = document.createElement('div');
      bubble.className = 'appai-bubble';

      if (role === 'user') {
        bubble.textContent = text;
      } else {
        // Assistant & hint messages support minimal Markdown
        bubble.innerHTML = markdownToHtml(text);
      }

      wrapper.appendChild(bubble);

      /* ── Hint action buttons ── */
      if (role === 'hint') {
        const actions = document.createElement('div');
        actions.className = 'appai-hint-actions';

        const yesBtn = document.createElement('button');
        yesBtn.className = 'appai-hint-btn appai-hint-btn-yes';
        yesBtn.textContent = 'Yes, show me';
        yesBtn.addEventListener('click', () => {
          wrapper.remove();
          // Ask Hub to elaborate on the hint
          this._send({ type: 'hint_accepted', message_id: messageId });
        });

        const noBtn = document.createElement('button');
        noBtn.className = 'appai-hint-btn appai-hint-btn-no';
        noBtn.textContent = 'Not now';
        noBtn.addEventListener('click', () => {
          wrapper.remove();
          this._send({ type: 'hint_dismissed', message_id: messageId });
        });

        actions.appendChild(yesBtn);
        actions.appendChild(noBtn);
        wrapper.appendChild(actions);
      }

      /* ── Meta row: timestamp + feedback button ── */
      const meta = document.createElement('div');
      meta.className = 'appai-message-meta';

      const ts = document.createElement('span');
      ts.className   = 'appai-timestamp';
      ts.textContent = timeLabel();
      meta.appendChild(ts);

      if (role === 'assistant') {
        const fbBtn = document.createElement('button');
        fbBtn.className = 'appai-feedback-btn';
        fbBtn.title     = 'This response was unhelpful';
        fbBtn.textContent = '👎';
        fbBtn.addEventListener('click', () => this._sendFeedback(messageId, 'unhelpful'));
        meta.appendChild(fbBtn);
      }

      wrapper.appendChild(meta);
      this._messagesEl.appendChild(wrapper);

      // Auto-scroll to latest message
      requestAnimationFrame(() => {
        this._messagesEl.scrollTop = this._messagesEl.scrollHeight;
      });
    }

    /**
     * _showTypingIndicator()
     *
     * Inserts an animated three-dot typing indicator into the messages area.
     * Only one indicator exists at a time.
     */
    _showTypingIndicator() {
      if (document.getElementById('appai-typing')) return;

      const el = document.createElement('div');
      el.className = 'appai-typing';
      el.id = 'appai-typing';
      el.innerHTML = '<span></span><span></span><span></span>';

      this._messagesEl.appendChild(el);
      requestAnimationFrame(() => {
        this._messagesEl.scrollTop = this._messagesEl.scrollHeight;
      });
    }

    /**
     * _removeTypingIndicator()
     *
     * Removes the typing indicator if it exists.
     */
    _removeTypingIndicator() {
      const el = document.getElementById('appai-typing');
      if (el) el.remove();
    }

    /**
     * _showStepList(steps)
     *
     * Renders all steps as a numbered list card in the chat panel.
     * Steps are displayed as:  ① Click the File menu
     *
     * @param {Array<Object>} steps - Array of step objects from the Hub
     *   Each step: { label, target_id, style, description }
     */
    _showStepList(steps) {
      if (!this._messagesEl || !steps?.length) return;

      const card = document.createElement('div');
      card.className = 'appai-step-list';
      card.id = 'appai-step-list';

      const title = document.createElement('div');
      title.className   = 'appai-step-list-title';
      title.textContent = `${steps.length} Steps to follow`;
      card.appendChild(title);

      const circledNums = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩'];

      steps.forEach((step, i) => {
        const item = document.createElement('div');
        item.className = 'appai-step-item';
        item.id = `appai-step-item-${i}`;

        const badge = document.createElement('div');
        badge.className   = 'appai-step-badge-inline';
        badge.textContent = (i + 1).toString();

        const label = document.createElement('span');
        const prefix = circledNums[i] || `${i + 1}.`;
        label.textContent = `${prefix} ${step.label || step.description || ''}`;

        item.appendChild(badge);
        item.appendChild(label);
        card.appendChild(item);
      });

      this._messagesEl.appendChild(card);
      requestAnimationFrame(() => {
        this._messagesEl.scrollTop = this._messagesEl.scrollHeight;
      });
    }

    /**
     * _updateStepList(stepIndex, status)
     *
     * Updates the visual state of a step in the step list card.
     *
     * @param {number} stepIndex
     * @param {'active'|'done'} status
     */
    _updateStepList(stepIndex, status) {
      const items = document.querySelectorAll('.appai-step-item');
      items.forEach((item, i) => {
        item.classList.remove('active', 'done');
        if (i < stepIndex)         item.classList.add('done');
        else if (i === stepIndex)  item.classList.add('active');
      });
    }

    // =========================================================================
    // Overlay guidance
    // =========================================================================

    /**
     * _startOverlay(steps, mode)
     *
     * Begins visual guidance overlay for a list of steps.
     *
     * mode: 'step_by_step'  — shows one step at a time; advances when the
     *                          user clicks/interacts near the target element.
     *       'all_at_once'   — renders all step overlays simultaneously.
     *
     * @param {Array<Object>} steps
     * @param {string} mode
     */
    _startOverlay(steps, mode) {
      if (!this.overlay || !steps?.length) return;

      this.overlaySteps = steps;
      this.currentStep  = 0;
      this.overlay.clearAll();

      if (mode === 'all_at_once') {
        steps.forEach((step, i) => {
          this.overlay.highlight(
            step.target_id  || step.selector || '',
            step.style      || 'glow_box',
            step.label      || step.description || '',
            i + 1
          );
        });
      } else {
        // step_by_step: show first step, listen for interaction
        this._showCurrentStep();
      }
    }

    /**
     * _showCurrentStep()
     *
     * Renders the overlay for the current step and attaches a one-time
     * interaction listener to auto-advance when the user acts on the target.
     */
    _showCurrentStep() {
      if (!this.overlay) return;
      const step = this.overlaySteps[this.currentStep];
      if (!step) {
        // All steps done
        this.overlay.clearAll();
        this.overlay.showCompletion();
        return;
      }

      this.overlay.clearAll();
      this.overlay.highlight(
        step.target_id  || step.selector || '',
        step.style      || 'arrow_point',
        step.label      || step.description || '',
        this.currentStep + 1
      );

      // Update step list highlight
      this._updateStepList(this.currentStep, 'active');

      // Auto-advance: listen for a click/input near the target element
      this._attachStepAdvanceListener(step);
    }

    /**
     * _attachStepAdvanceListener(step)
     *
     * Listens for a click or input event on (or near) the target element.
     * Calls _advanceStep() when the user performs the expected action.
     *
     * @param {Object} step
     */
    _attachStepAdvanceListener(step) {
      const targetId = step.target_id || step.selector || '';

      // Find the target element
      let targetEl = document.getElementById(targetId);
      if (!targetEl) {
        try { targetEl = document.querySelector(targetId); } catch (_) {}
      }

      if (!targetEl) {
        // If target not found, allow manual advance via a chat message
        return;
      }

      const handler = () => {
        targetEl.removeEventListener('click', handler);
        targetEl.removeEventListener('input', handler);
        targetEl.removeEventListener('change', handler);
        // Small delay so the user sees the interaction before advancing
        setTimeout(() => this._advanceStep(), 400);
      };

      targetEl.addEventListener('click',  handler, { once: true });
      targetEl.addEventListener('input',  handler, { once: true });
      targetEl.addEventListener('change', handler, { once: true });
    }

    /**
     * _advanceStep()
     *
     * Marks the current step as done and advances to the next one.
     * Shows a completion animation after the last step.
     */
    _advanceStep() {
      // Mark current step done in the list
      this._updateStepList(this.currentStep, 'done');

      this.currentStep++;

      if (this.currentStep >= this.overlaySteps.length) {
        // All done
        if (this.overlay) {
          this.overlay.clearAll();
          this.overlay.showCompletion();
        }
        this._send({ type: 'guidance_completed', session_id: this.sessionId });
        return;
      }

      // Show next step
      this._showCurrentStep();
    }

    // =========================================================================
    // Feedback
    // =========================================================================

    /**
     * _sendFeedback(messageId, reason)
     *
     * Sends a negative feedback signal to the Hub for a specific message.
     * Also briefly highlights the feedback button to confirm receipt.
     *
     * @param {string} messageId
     * @param {string} reason    - e.g. 'unhelpful'
     */
    _sendFeedback(messageId, reason) {
      this._send({
        type:       'feedback',
        session_id: this.sessionId,
        message_id: messageId,
        rating:     'negative',
        reason:     reason,
      });

      // Visual confirmation: find and temporarily disable the button
      const msg = this._messagesEl.querySelector(`[data-message-id="${messageId}"]`);
      const btn = msg ? msg.querySelector('.appai-feedback-btn') : null;
      if (btn) {
        btn.textContent = '✓';
        btn.disabled = true;
        btn.style.color = '#10b981';
      }
    }

    // =========================================================================
    // Public API methods
    // =========================================================================

    /**
     * setScreen(screenName)
     *
     * Host apps call this whenever the view changes so AppAI can provide
     * contextually relevant guidance.
     *
     * @param {string} screenName - e.g. 'Dashboard', 'Invoice Form'
     *
     * @example
     *   AppAI.setScreen('Dashboard');
     */
    setScreen(screenName) {
      if (screenName === this.lastScreen) return;
      this.lastScreen = screenName;

      // Notify Hub immediately (don't wait for the 3-second interval)
      this._send({
        type:       'screen_change',
        session_id: this.sessionId,
        screen:     screenName,
        url:        window.location.href,
        title:      document.title,
      });
    }

    // =========================================================================
    // UI helpers
    // =========================================================================

    /**
     * _togglePanel(show)
     *
     * Shows or hides the chat panel and toggles the floating button.
     *
     * @param {boolean} show
     */
    _togglePanel(show) {
      if (!this.chatPanel) return;

      if (show) {
        this.chatPanel.classList.remove('appai-collapsed');
        this.chatPanel.classList.add('appai-open');
        if (this._floatBtn) this._floatBtn.style.display = 'none';
        // Focus input
        const input = document.getElementById('appai-query-input');
        if (input) input.focus();
      } else {
        this.chatPanel.classList.add('appai-collapsed');
        this.chatPanel.classList.remove('appai-open');
        if (this._floatBtn && window.innerWidth < 768) {
          this._floatBtn.style.display = 'flex';
        }
      }
    }

    /**
     * _applyResponsiveState()
     *
     * On screens < 768px: collapses the panel and shows the float button.
     * On larger screens: ensures the panel is visible.
     */
    _applyResponsiveState() {
      if (window.innerWidth < 768) {
        const isOpen = this.chatPanel?.classList.contains('appai-open');
        if (!isOpen) {
          if (this.chatPanel) this.chatPanel.classList.add('appai-collapsed');
          if (this._floatBtn) this._floatBtn.style.display = 'flex';
        }
      } else {
        if (this.chatPanel) {
          this.chatPanel.classList.remove('appai-collapsed');
          this.chatPanel.classList.remove('appai-open');
        }
        if (this._floatBtn) this._floatBtn.style.display = 'none';
      }
    }

    /**
     * _setStatus(state)
     *
     * Updates the connection status dot in the chat header.
     *
     * @param {'connecting'|'connected'|'disconnected'} state
     */
    _setStatus(state) {
      if (!this._statusDot) return;
      this._statusDot.className = `appai-status-dot ${state}`;
      const labels = {
        connecting:   'Connecting…',
        connected:    'Connected',
        disconnected: 'Disconnected — retrying…',
      };
      this._statusDot.title = labels[state] || state;
    }
  }

  // =========================================================================
  // Public window.AppAI global
  // =========================================================================

  window.AppAI = {
    /**
     * AppAI.init(config)
     *
     * Initialises the SDK. Call once per page load.
     *
     * @param {Object} config
     * @param {string} config.appId      - Required. Your application id.
     * @param {string} config.userId     - Required. Current user's id.
     * @param {string} [config.userName] - User's display name.
     * @param {string} [config.hubUrl]   - WebSocket hub base URL.
     * @param {string} [config.role]     - User role hint.
     * @returns {AppAISDK}
     *
     * @example
     *   AppAI.init({ appId: 'billing-app', userId: 'u_42', userName: 'Alice' });
     */
    init(config) {
      const sdk = new AppAISDK(config);
      sdk.init();
      window._appAIInstance = sdk;
      return sdk;
    },

    /**
     * AppAI.setScreen(name)
     *
     * Tells AppAI the current screen / view. Call on every route change.
     *
     * @param {string} name
     *
     * @example
     *   AppAI.setScreen('Invoice Form');
     */
    setScreen(name) {
      window._appAIInstance?.setScreen(name);
    },

    /**
     * AppAI.sendQuery(text)
     *
     * Programmatically sends a query as if the user typed it.
     *
     * @param {string} text
     *
     * @example
     *   AppAI.sendQuery('How do I export a PDF?');
     */
    sendQuery(text) {
      window._appAIInstance?._sendQuery(text);
    },
  };

})();
