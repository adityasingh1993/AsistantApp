/**
 * AppAI Web SDK — consent.js
 *
 * Provides the AppAIConsent class for displaying privacy-first consent dialogs
 * before the SDK accesses sensitive resources (screenshots, local documents).
 *
 * Usage:
 *   Include AFTER appai-sdk.js.
 *   The SDK instantiates this automatically; you rarely call it directly.
 */

/* global AppAIConsent */

class AppAIConsent {
  constructor() {
    /** @type {HTMLElement|null} Currently open modal backdrop */
    this._currentModal = null;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Public consent dialogs
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * showScreenshotConsent(onAllow, onAllowSession, onDeny)
   *
   * Displays a modal dialog asking the user to permit a one-time or
   * per-session screenshot before the SDK captures the screen.
   *
   * @param {Function} onAllow        - Called when user clicks "Allow Once"
   * @param {Function} onAllowSession - Called when user clicks "Allow for this session"
   * @param {Function} onDeny         - Called when user clicks "No, thanks" or backdrop
   */
  showScreenshotConsent(onAllow, onAllowSession, onDeny) {
    const modal = this._createModal(
      '📸',
      'AppAI wants to take a screenshot',
      'To better help you, AppAI would like to see your current screen. ' +
      'This screenshot will only be used to answer your question and won\'t be stored.',
      [
        {
          label:   'Allow Once',
          classes: 'appai-btn-primary',
          action:  () => { this._closeModal(modal); onAllow && onAllow(); },
        },
        {
          label:   'Allow for this session',
          classes: 'appai-btn-secondary',
          action:  () => { this._closeModal(modal); onAllowSession && onAllowSession(); },
        },
        {
          label:   'No, thanks',
          classes: 'appai-btn-ghost',
          action:  () => { this._closeModal(modal); onDeny && onDeny(); },
        },
      ]
    );

    return modal;
  }

  /**
   * showDocumentConsent(onChooseFile, onDeny)
   *
   * Displays a modal with a hidden <input type="file"> triggered by a button.
   * The chosen file object is passed to onChooseFile; nothing is uploaded.
   *
   * @param {Function} onChooseFile - Called with the chosen File object
   * @param {Function} onDeny       - Called when user clicks "Not now" or backdrop
   */
  showDocumentConsent(onChooseFile, onDeny) {
    // Build a custom body node that includes the file picker
    const bodyHtml =
      'AppAI will read this document <strong>locally</strong> to help answer your question. ' +
      'It won\'t leave your machine or be stored beyond this session.';

    // Create modal without a preset file button — we add it in the buttons array
    const fileInputId = 'appai-file-' + Date.now();

    const modal = this._createModal(
      '📄',
      'Share a document with AppAI',
      bodyHtml,
      [
        {
          label:   'Choose File…',
          classes: 'appai-btn-primary',
          action:  () => {
            // Trigger the hidden file input
            const input = modal.querySelector('#' + fileInputId);
            if (input) input.click();
          },
        },
        {
          label:   'Not now',
          classes: 'appai-btn-ghost',
          action:  () => { this._closeModal(modal); onDeny && onDeny(); },
        },
      ]
    );

    // Inject the hidden file input inside the modal
    const fileInput = document.createElement('input');
    fileInput.type   = 'file';
    fileInput.id     = fileInputId;
    fileInput.className = 'appai-file-input';
    fileInput.accept = '.pdf,.txt,.csv,.json,.md,.docx,.xlsx';
    fileInput.style.display = 'none';

    fileInput.addEventListener('change', () => {
      const file = fileInput.files && fileInput.files[0];
      this._closeModal(modal);
      if (file) {
        onChooseFile && onChooseFile(file);
      } else {
        onDeny && onDeny();
      }
    });

    const card = modal.querySelector('.appai-modal');
    if (card) card.appendChild(fileInput);

    return modal;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Private helpers
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * _createModal(icon, title, bodyHtml, buttons)
   *
   * Creates and injects a fully styled modal card into the DOM.
   * The backdrop closes the dialog (triggers the last button's action = deny).
   *
   * @param {string} icon     - Emoji or short text for the icon area
   * @param {string} title    - Modal heading
   * @param {string} bodyHtml - innerHTML for the body paragraph (supports simple tags)
   * @param {Array}  buttons  - [{label, classes, action}]
   * @returns {HTMLElement}   - The backdrop element
   */
  _createModal(icon, title, bodyHtml, buttons) {
    // Close any existing modal first
    if (this._currentModal) {
      this._closeModal(this._currentModal);
    }

    /* ── Backdrop ── */
    const backdrop = document.createElement('div');
    backdrop.className = 'appai-modal-backdrop';
    backdrop.setAttribute('role', 'dialog');
    backdrop.setAttribute('aria-modal', 'true');

    /* ── Card ── */
    const card = document.createElement('div');
    card.className = 'appai-modal';

    /* ── Icon ── */
    const iconEl = document.createElement('div');
    iconEl.className = 'appai-modal-icon';
    iconEl.textContent = icon;

    /* ── Title ── */
    const titleEl = document.createElement('h2');
    titleEl.className = 'appai-modal-title';
    titleEl.textContent = title;

    /* ── Body ── */
    const bodyEl = document.createElement('p');
    bodyEl.className = 'appai-modal-body';
    bodyEl.innerHTML = bodyHtml; // safe because content is SDK-controlled

    /* ── Footer (buttons) ── */
    const footer = document.createElement('div');
    footer.className = 'appai-modal-footer';

    buttons.forEach(({ label, classes, action }) => {
      const btn = document.createElement('button');
      btn.className = classes;
      btn.textContent = label;
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        action();
      });
      footer.appendChild(btn);
    });

    card.appendChild(iconEl);
    card.appendChild(titleEl);
    card.appendChild(bodyEl);
    card.appendChild(footer);
    backdrop.appendChild(card);

    // Clicking the backdrop (outside the card) triggers the last action (deny)
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        const denyAction = buttons[buttons.length - 1]?.action;
        if (denyAction) denyAction();
      }
    });

    // Trap Escape key
    const keyHandler = (e) => {
      if (e.key === 'Escape') {
        const denyAction = buttons[buttons.length - 1]?.action;
        if (denyAction) denyAction();
        document.removeEventListener('keydown', keyHandler);
      }
    };
    document.addEventListener('keydown', keyHandler);
    backdrop._keyHandler = keyHandler; // store for cleanup

    // Inject inline styles if styles.css not present
    this._ensureModalStyles();

    document.body.appendChild(backdrop);
    this._currentModal = backdrop;

    // Focus the first button for accessibility
    requestAnimationFrame(() => {
      const firstBtn = footer.querySelector('button');
      if (firstBtn) firstBtn.focus();
    });

    return backdrop;
  }

  /**
   * _closeModal(modal)
   *
   * Removes the modal backdrop from the DOM with a brief fade-out.
   *
   * @param {HTMLElement} modal - The backdrop element returned by _createModal
   */
  _closeModal(modal) {
    if (!modal || !modal.parentNode) return;

    // Clean up keyboard listener
    if (modal._keyHandler) {
      document.removeEventListener('keydown', modal._keyHandler);
    }

    modal.style.transition = 'opacity 0.18s ease';
    modal.style.opacity    = '0';

    setTimeout(() => {
      if (modal.parentNode) modal.parentNode.removeChild(modal);
    }, 200);

    if (this._currentModal === modal) {
      this._currentModal = null;
    }
  }

  /**
   * _ensureModalStyles()
   *
   * Injects minimal modal CSS if the main styles.css is not on the page.
   * Called internally before any modal is shown.
   */
  _ensureModalStyles() {
    if (document.getElementById('appai-consent-styles')) return;

    const css = `
      /* AppAI Consent injected styles */
      .appai-modal-backdrop {
        position:fixed;inset:0;background:rgba(0,0,0,.5);
        z-index:100001;display:flex;align-items:center;justify-content:center;
        animation:_appai-fadein-modal .2s ease;backdrop-filter:blur(2px);
      }
      .appai-modal {
        background:#fff;border-radius:16px;
        box-shadow:0 20px 60px rgba(0,0,0,.2);
        padding:28px 28px 24px;max-width:420px;
        width:calc(100% - 48px);
        animation:_appai-modal-in .25s cubic-bezier(.34,1.56,.64,1) forwards;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
      }
      .appai-modal-icon {
        width:48px;height:48px;border-radius:12px;background:#eff6ff;
        display:flex;align-items:center;justify-content:center;
        font-size:24px;margin-bottom:16px;
      }
      .appai-modal-title { font-size:17px;font-weight:700;color:#111827;margin-bottom:8px;letter-spacing:-.02em; }
      .appai-modal-body  { font-size:13.5px;color:#6b7280;line-height:1.6;margin-bottom:20px; }
      .appai-modal-footer { display:flex;flex-direction:column;gap:8px; }
      .appai-btn-primary   { padding:10px 18px;background:#2563eb;color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;width:100%; }
      .appai-btn-primary:hover   { background:#1d4ed8; }
      .appai-btn-secondary { padding:10px 18px;background:#f3f4f6;color:#374151;border:none;border-radius:10px;font-size:14px;font-weight:500;cursor:pointer;width:100%; }
      .appai-btn-secondary:hover { background:#e5e7eb; }
      .appai-btn-ghost     { padding:8px 18px;background:none;color:#6b7280;border:none;font-size:13px;cursor:pointer;width:100%; }
      .appai-btn-ghost:hover     { color:#111827; }
      .appai-file-input    { display:none; }
      @keyframes _appai-fadein-modal { from{opacity:0;} to{opacity:1;} }
      @keyframes _appai-modal-in {
        from { opacity:0; transform:scale(.92) translateY(8px); }
        to   { opacity:1; transform:scale(1)   translateY(0);   }
      }
    `;

    const style = document.createElement('style');
    style.id = 'appai-consent-styles';
    style.textContent = css;
    document.head.appendChild(style);
  }
}
