/**
 * AppAI Web SDK — overlay.js
 *
 * Provides the AppAIOverlay class which draws visual guidance elements
 * (pulse rings, glow boxes, arrows, drop zones, spotlight, step badges)
 * directly onto the page without interfering with click events.
 *
 * Usage:
 *   Include AFTER appai-sdk.js (or any time before init is called).
 *   The SDK instantiates this automatically.
 */

/* global AppAIOverlay */

class AppAIOverlay {
  constructor() {
    /** @type {HTMLElement|null} Top-level container for all overlay elements */
    this.overlayContainer = null;

    /** @type {Array<HTMLElement>} Currently active overlay DOM nodes */
    this.activeElements = [];

    /** @type {HTMLCanvasElement|null} Canvas used for spotlight rendering */
    this._spotlightCanvas = null;

    /** @type {boolean} Whether CSS animations have been injected */
    this._stylesInjected = false;
  }

  /**
   * init() — Creates the full-screen overlay container and injects CSS animations.
   * Must be called once before any highlight() calls.
   */
  init() {
    // Inject keyframe animations via a <style> tag if not already done
    if (!this._stylesInjected) {
      this._injectAnimationStyles();
      this._stylesInjected = true;
    }

    // Create the overlay container if it doesn't exist yet
    if (!this.overlayContainer) {
      const container = document.createElement('div');
      container.className = 'appai-overlay-container';
      container.id = 'appai-overlay-root';

      // Make sure all children pass clicks through to the page
      container.style.cssText = [
        'position:fixed',
        'top:0',
        'left:0',
        'width:100%',
        'height:100%',
        'pointer-events:none',
        'z-index:99999',
      ].join(';');

      document.body.appendChild(container);
      this.overlayContainer = container;
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Public API
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * highlight(targetId, style, label, stepNum)
   *
   * Finds a DOM element by id or CSS selector and draws an overlay over it.
   *
   * @param {string} targetId  - Element id (plain) or any CSS selector
   * @param {string} style     - 'pulse_ring' | 'glow_box' | 'arrow_point' |
   *                             'drop_zone' | 'spotlight' | 'step_badge'
   * @param {string} label     - Tooltip text shown near the element
   * @param {number} stepNum   - Step number displayed on the badge
   */
  highlight(targetId, style, label, stepNum) {
    if (!this.overlayContainer) this.init();

    // Resolve the target element — try by id first, then as a selector
    let el = document.getElementById(targetId);
    if (!el) {
      try { el = document.querySelector(targetId); } catch (_) { /* ignore */ }
    }
    if (!el) {
      console.warn(`[AppAI Overlay] Target not found: "${targetId}"`);
      return;
    }

    const rect = el.getBoundingClientRect();

    switch (style) {
      case 'pulse_ring':  this._drawPulseRing(rect, label, stepNum); break;
      case 'glow_box':    this._drawGlowBox(rect, label, stepNum);   break;
      case 'arrow_point': this._drawArrow(rect, label, stepNum);     break;
      case 'drop_zone':   this._drawDropZone(rect, label);           break;
      case 'spotlight':   this._drawSpotlight(rect, label);          break;
      case 'step_badge':  this._drawStepBadge(rect, label, stepNum); break;
      default:            this._drawGlowBox(rect, label, stepNum);   break;
    }
  }

  /**
   * clearAll() — Removes every overlay element from the DOM.
   */
  clearAll() {
    this.activeElements.forEach(el => el.remove());
    this.activeElements = [];

    // Also remove spotlight canvas if present
    if (this._spotlightCanvas) {
      this._spotlightCanvas.remove();
      this._spotlightCanvas = null;
    }
  }

  /**
   * showCompletion() — Displays a ✅ Done banner that fades out automatically.
   */
  showCompletion() {
    const banner = document.createElement('div');
    banner.className = 'appai-completion';
    banner.textContent = '✅ Done! All steps completed.';
    document.body.appendChild(banner);

    // Remove banner after animation (fadein 0.3s + hold + fadeout 0.4s = ~2.2s)
    setTimeout(() => banner.remove(), 2300);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Private draw methods
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * _drawPulseRing(rect, label, stepNum)
   *
   * Draws an animated pulsing circle (blue #2563EB) that scales 1→1.3→1
   * centered on the target element.  Works best on icon / button targets.
   *
   * @param {DOMRect} rect
   * @param {string}  label
   * @param {number}  stepNum
   */
  _drawPulseRing(rect, label, stepNum) {
    const size = Math.max(rect.width, rect.height) + 16; // padding around element
    const cx   = rect.left + rect.width / 2;
    const cy   = rect.top  + rect.height / 2;

    const ring = document.createElement('div');
    ring.className = 'appai-pulse-ring appai-overlay-element';
    ring.style.cssText = [
      `width:${size}px`,
      `height:${size}px`,
      `top:${cy - size / 2}px`,
      `left:${cx - size / 2}px`,
      'position:fixed',
    ].join(';');

    this.overlayContainer.appendChild(ring);
    this.activeElements.push(ring);

    // Step badge top-left
    if (stepNum !== undefined) {
      this.activeElements.push(
        this._createStepBadge(rect.left - 6, rect.top - 6, stepNum)
      );
    }

    // Tooltip
    if (label) {
      this.activeElements.push(
        this._createTooltip(cx, cy - size / 2, label, stepNum)
      );
    }
  }

  /**
   * _drawGlowBox(rect, label, stepNum)
   *
   * Draws a glowing blue border rectangle over the target element.
   * Box-shadow animates between two opacity levels to create a breathing glow.
   *
   * @param {DOMRect} rect
   * @param {string}  label
   * @param {number}  stepNum
   */
  _drawGlowBox(rect, label, stepNum) {
    const PAD = 4; // extra padding around the element

    const box = document.createElement('div');
    box.className = 'appai-glow-box appai-overlay-element';
    box.style.cssText = [
      `top:${rect.top - PAD}px`,
      `left:${rect.left - PAD}px`,
      `width:${rect.width + PAD * 2}px`,
      `height:${rect.height + PAD * 2}px`,
      'position:fixed',
      'border-radius:6px',
    ].join(';');

    this.overlayContainer.appendChild(box);
    this.activeElements.push(box);

    if (stepNum !== undefined) {
      this.activeElements.push(
        this._createStepBadge(rect.left - PAD, rect.top - PAD, stepNum)
      );
    }

    if (label) {
      this.activeElements.push(
        this._createTooltip(
          rect.left + rect.width / 2,
          rect.top - PAD,
          label,
          stepNum
        )
      );
    }
  }

  /**
   * _drawArrow(rect, label, stepNum)
   *
   * Draws a downward-pointing animated CSS arrow above the target element.
   * The arrow bobs up and down (translateY 0 → -6px → 0).
   *
   * @param {DOMRect} rect
   * @param {string}  label
   * @param {number}  stepNum
   */
  _drawArrow(rect, label, stepNum) {
    const cx = rect.left + rect.width / 2;

    const wrapper = document.createElement('div');
    wrapper.className = 'appai-arrow appai-overlay-element';
    wrapper.style.cssText = [
      `top:${rect.top - 52}px`,
      `left:${cx - 8}px`, // 8 = half of arrow head width
      'position:fixed',
    ].join(';');

    const shaft = document.createElement('div');
    shaft.className = 'appai-arrow-shaft';

    const head = document.createElement('div');
    head.className = 'appai-arrow-head';

    wrapper.appendChild(shaft);
    wrapper.appendChild(head);

    this.overlayContainer.appendChild(wrapper);
    this.activeElements.push(wrapper);

    if (stepNum !== undefined) {
      this.activeElements.push(
        this._createStepBadge(rect.left, rect.top - 60, stepNum)
      );
    }

    if (label) {
      this.activeElements.push(
        this._createTooltip(cx, rect.top - 56, label, stepNum)
      );
    }
  }

  /**
   * _drawDropZone(rect, label)
   *
   * Draws a dashed green border (#10B981) with a light green tint over the
   * target — used for file-upload / drag-and-drop guidance.
   *
   * @param {DOMRect} rect
   * @param {string}  label
   */
  _drawDropZone(rect, label) {
    const PAD = 6;

    const dz = document.createElement('div');
    dz.className = 'appai-drop-zone appai-overlay-element';
    dz.style.cssText = [
      `top:${rect.top - PAD}px`,
      `left:${rect.left - PAD}px`,
      `width:${rect.width + PAD * 2}px`,
      `height:${rect.height + PAD * 2}px`,
      'position:fixed',
    ].join(';');

    this.overlayContainer.appendChild(dz);
    this.activeElements.push(dz);

    if (label) {
      const cx = rect.left + rect.width / 2;
      this.activeElements.push(
        this._createTooltip(cx, rect.top - PAD, label, undefined)
      );
    }
  }

  /**
   * _drawSpotlight(rect, label)
   *
   * Dims the entire page with a semi-transparent black overlay (rgba 0,0,0,0.7)
   * and cuts a transparent "hole" over the target element using canvas compositing.
   *
   * @param {DOMRect} rect
   * @param {string}  label
   */
  _drawSpotlight(rect, label) {
    // Remove any existing spotlight canvas
    if (this._spotlightCanvas) {
      this._spotlightCanvas.remove();
    }

    const canvas = document.createElement('canvas');
    canvas.className = 'appai-spotlight-canvas';
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    canvas.style.cssText = [
      'position:fixed',
      'top:0', 'left:0',
      'pointer-events:none',
      'z-index:99999',
    ].join(';');

    const ctx = canvas.getContext('2d');

    // Fill entire canvas with dark overlay
    ctx.fillStyle = 'rgba(0,0,0,0.72)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Cut out a rounded rectangle for the target element
    const PAD = 8;
    const R   = 10; // corner radius
    const x   = rect.left - PAD;
    const y   = rect.top  - PAD;
    const w   = rect.width  + PAD * 2;
    const h   = rect.height + PAD * 2;

    ctx.globalCompositeOperation = 'destination-out';
    ctx.beginPath();
    ctx.moveTo(x + R, y);
    ctx.lineTo(x + w - R, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + R);
    ctx.lineTo(x + w, y + h - R);
    ctx.quadraticCurveTo(x + w, y + h, x + w - R, y + h);
    ctx.lineTo(x + R, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - R);
    ctx.lineTo(x, y + R);
    ctx.quadraticCurveTo(x, y, x + R, y);
    ctx.closePath();
    ctx.fill();

    ctx.globalCompositeOperation = 'source-over';

    document.body.appendChild(canvas);
    this._spotlightCanvas = canvas;
    this.activeElements.push(canvas);

    // Tooltip below the spotlight hole
    if (label) {
      const cx = rect.left + rect.width / 2;
      this.activeElements.push(
        this._createTooltip(cx, rect.bottom + PAD + 8, label, undefined, 'below')
      );
    }
  }

  /**
   * _drawStepBadge(rect, label, stepNum)
   *
   * Draws only a step badge overlay (no highlight box).
   * Useful when called from highlight() with style='step_badge'.
   *
   * @param {DOMRect} rect
   * @param {string}  label
   * @param {number}  stepNum
   */
  _drawStepBadge(rect, label, stepNum) {
    this.activeElements.push(
      this._createStepBadge(rect.left - 8, rect.top - 8, stepNum)
    );

    if (label) {
      const cx = rect.left + rect.width / 2;
      this.activeElements.push(
        this._createTooltip(cx, rect.top - 8, label, stepNum)
      );
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Helper element factories
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * _createTooltip(x, y, label, stepNum, position)
   *
   * Creates a floating tooltip bubble positioned above or below (x, y).
   *
   * @param {number} x         - Horizontal center of the tooltip
   * @param {number} y         - Top edge of the target (tooltip is placed above)
   * @param {string} label     - Tooltip text
   * @param {number} stepNum   - If defined, prepended as "Step N: "
   * @param {string} position  - 'above' (default) | 'below'
   * @returns {HTMLElement}
   */
  _createTooltip(x, y, label, stepNum, position = 'above') {
    const tip = document.createElement('div');
    tip.className = `appai-tooltip ${position}`;

    const text = stepNum !== undefined ? `Step ${stepNum}: ${label}` : label;
    tip.textContent = text;

    // Temporarily attach to measure width
    tip.style.cssText = 'visibility:hidden;position:fixed;top:-1000px;left:-1000px;';
    document.body.appendChild(tip);

    const tipRect = tip.getBoundingClientRect();
    const tipW    = tipRect.width;
    const tipH    = tipRect.height;

    // Clamp x so tooltip stays within the viewport
    let left = x - tipW / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tipW - 8));

    let top;
    if (position === 'below') {
      top = y + 4;
    } else {
      top = y - tipH - 10;
      if (top < 4) { // flip below if no room above
        top = y + 8;
        tip.classList.remove('above');
        tip.classList.add('below');
      }
    }

    tip.style.cssText = [
      `top:${top}px`,
      `left:${left}px`,
      'position:fixed',
      'visibility:visible',
    ].join(';');

    this.overlayContainer.appendChild(tip);
    return tip;
  }

  /**
   * _createStepBadge(x, y, stepNum)
   *
   * Creates a blue circle with a white step number at position (x, y).
   *
   * @param {number} x
   * @param {number} y
   * @param {number} stepNum
   * @returns {HTMLElement}
   */
  _createStepBadge(x, y, stepNum) {
    const badge = document.createElement('div');
    badge.className = 'appai-step-badge-overlay';
    badge.textContent = stepNum;
    badge.style.cssText = [
      `top:${y}px`,
      `left:${x}px`,
      'position:fixed',
    ].join(';');

    this.overlayContainer.appendChild(badge);
    return badge;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CSS injection
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * _injectAnimationStyles()
   *
   * Injects a <style> tag with all overlay-specific CSS animations.
   * Called once during init().  Skipped if styles.css is already on the page.
   */
  _injectAnimationStyles() {
    // If the host page already loaded styles.css, skip injection
    const existing = document.querySelector('link[href*="appai"]');
    if (existing) return;

    const css = `
      /* AppAI Overlay injected styles */
      .appai-overlay-container { position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999; }
      .appai-pulse-ring { position:fixed; border-radius:50%; border:3px solid #2563EB;
        animation: _appai-pulse-ring 1.5s ease-in-out infinite; }
      .appai-glow-box { position:fixed; border:2px solid #2563EB; border-radius:6px;
        box-shadow: 0 0 0 4px rgba(37,99,235,.25), 0 0 16px rgba(37,99,235,.2);
        animation: _appai-glow 2s ease-in-out infinite; }
      .appai-arrow { position:fixed; display:flex; flex-direction:column; align-items:center;
        animation: _appai-bob 1s ease-in-out infinite; pointer-events:none; }
      .appai-arrow-shaft { width:3px; height:28px; background:#2563EB; border-radius:2px; }
      .appai-arrow-head  { width:0; height:0;
        border-left:8px solid transparent; border-right:8px solid transparent;
        border-top:12px solid #2563EB; }
      .appai-drop-zone { position:fixed; border:2px dashed #10B981; border-radius:8px;
        background:rgba(16,185,129,.06); animation: _appai-dash-offset 1s linear infinite; }
      .appai-step-badge-overlay { position:fixed; width:26px; height:26px;
        border-radius:50%; background:#2563EB; color:#fff; font-size:12px; font-weight:700;
        display:flex; align-items:center; justify-content:center;
        box-shadow:0 2px 8px rgba(37,99,235,.4); pointer-events:none; }
      .appai-tooltip { position:fixed; background:#1f2937; color:#fff;
        padding:7px 12px; border-radius:8px; font-size:12.5px; font-weight:500;
        box-shadow:0 4px 12px rgba(0,0,0,.25); pointer-events:none;
        line-height:1.4; max-width:240px; white-space:normal; font-family:inherit; }
      .appai-tooltip::after { content:''; position:absolute; width:8px; height:8px;
        background:#1f2937; transform:rotate(45deg); }
      .appai-tooltip.above::after { bottom:-4px; left:50%; margin-left:-4px; }
      .appai-tooltip.below::after { top:-4px; left:50%; margin-left:-4px; }
      .appai-completion { position:fixed; top:20px; left:50%; transform:translateX(-50%);
        background:#10b981; color:#fff; padding:12px 24px; border-radius:40px;
        font-size:15px; font-weight:600; box-shadow:0 4px 16px rgba(16,185,129,.4);
        z-index:100000; animation:_appai-fadein .3s ease, _appai-fadeout .4s ease 1.8s forwards;
        pointer-events:none; font-family:inherit; }
      @keyframes _appai-pulse-ring {
        0%   { transform:scale(1);   opacity:1; }
        60%  { transform:scale(1.3); opacity:0.6; }
        100% { transform:scale(1);   opacity:1; }
      }
      @keyframes _appai-glow {
        0%,100% { box-shadow:0 0 0 4px rgba(37,99,235,.25),0 0 16px rgba(37,99,235,.2); }
        50%      { box-shadow:0 0 0 6px rgba(37,99,235,.35),0 0 24px rgba(37,99,235,.3); }
      }
      @keyframes _appai-bob {
        0%,100% { transform:translateY(0); }
        50%     { transform:translateY(-6px); }
      }
      @keyframes _appai-dash-offset {
        0%   { background-position:0 0, 100% 0, 100% 100%, 0 100%; }
        100% { background-position:20px 0, 100% 20px, calc(100% - 20px) 100%, 0 calc(100% - 20px); }
      }
      @keyframes _appai-fadein  { from{opacity:0;} to{opacity:1;} }
      @keyframes _appai-fadeout { from{opacity:1;} to{opacity:0;} }
    `;

    const style = document.createElement('style');
    style.id = 'appai-overlay-styles';
    style.textContent = css;
    document.head.appendChild(style);
  }
}
