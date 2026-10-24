/* Tiny DOM toolkit: element builder, tooltips, modals, toasts. */
(function (AG) {
  'use strict';
  const UI = (AG.UI = AG.UI || {});

  // h('div.card#id', {attrs}, ...children). Attrs: on:{event:fn}, style:{}, class, html.
  function h(tag, attrs) {
    const kids = Array.prototype.slice.call(arguments, 2);
    const m = /^([a-z0-9-]*)(.*)$/i.exec(tag);
    const el = document.createElement(m[1] || 'div');
    m[2].replace(/([.#])([^.#]+)/g, function (_, k, v) {
      if (k === '.') el.classList.add(v);
      else el.id = v;
      return '';
    });
    if (attrs != null && (typeof attrs !== 'object' || attrs instanceof Node || Array.isArray(attrs))) {
      kids.unshift(attrs);
      attrs = null;
    }
    if (attrs) {
      for (const k in attrs) {
        const v = attrs[k];
        if (v == null || v === false) continue;
        if (k === 'on') for (const ev in v) el.addEventListener(ev, v[ev]);
        else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
        else if (k === 'class') { for (const c of String(v).split(/\s+/)) if (c) el.classList.add(c); }
        else if (k === 'html') el.innerHTML = v;
        else if (k === 'dataset') Object.assign(el.dataset, v);
        else if (typeof v === 'boolean') { if (v) el.setAttribute(k, ''); el[k] = v; }
        else el.setAttribute(k, v);
      }
    }
    append(el, kids);
    return el;
  }
  function append(el, kids) {
    for (const k of kids) {
      if (k == null || k === false) continue;
      if (Array.isArray(k)) append(el, k);
      else el.appendChild(k instanceof Node ? k : document.createTextNode(String(k)));
    }
  }
  UI.h = h;
  UI.append = append;
  UI.clear = function (el) {
    while (el.firstChild) el.removeChild(el.firstChild);
    return el;
  };

  // ------------------------------------------------------------ tooltips
  // Any element with data-tip (and optional data-tip-title) gets a tooltip.
  let tipEl = null, tipFor = null, tipTimer = 0;
  function showTip(target) {
    const text = target.getAttribute('data-tip');
    if (!text) return;
    if (!tipEl) {
      tipEl = h('div.tip', { role: 'tooltip' });
      document.body.appendChild(tipEl);
    }
    UI.clear(tipEl);
    const title = target.getAttribute('data-tip-title');
    if (title) tipEl.appendChild(h('b', title)), tipEl.appendChild(h('br'));
    tipEl.appendChild(document.createTextNode(text));
    tipEl.hidden = false;
    const r = target.getBoundingClientRect();
    const tw = tipEl.offsetWidth, th = tipEl.offsetHeight;
    let x = r.left + r.width / 2 - tw / 2;
    let y = r.top - th - 8;
    if (y < 8) y = r.bottom + 8;
    x = Math.max(8, Math.min(window.innerWidth - tw - 8, x));
    tipEl.style.left = x + 'px';
    tipEl.style.top = y + 'px';
    tipFor = target;
  }
  function hideTip() {
    if (tipEl) tipEl.hidden = true;
    tipFor = null;
  }
  UI.hideTip = hideTip;
  UI.initTips = function () {
    document.addEventListener('pointerover', function (e) {
      const t = e.target.closest && e.target.closest('[data-tip]');
      if (t && t !== tipFor) {
        showTip(t);
        clearTimeout(tipTimer);
        if (e.pointerType === 'touch') tipTimer = setTimeout(hideTip, 2600);
      } else if (!t && tipFor) hideTip();
    });
    document.addEventListener('pointerdown', function (e) {
      const t = e.target.closest && e.target.closest('[data-tip]');
      if (!t) hideTip();
    });
    window.addEventListener('scroll', hideTip, true);
  };

  // ---------------------------------------------------------------- modal
  UI.modal = function (content, opts) {
    opts = opts || {};
    const back = h('div.modal-back');
    const box = h('div.modal' + (opts.wide ? '.wide' : ''), { role: 'dialog', 'aria-modal': 'true' });
    const close = function () {
      if (!back.parentNode) return;
      back.parentNode.removeChild(back);
      document.removeEventListener('keydown', onKey);
      if (opts.onClose) opts.onClose();
    };
    const onKey = function (e) { if (e.key === 'Escape' && opts.dismissable !== false) close(); };
    if (opts.dismissable !== false) {
      box.appendChild(h('button.btn.icon.ghost.close', { 'aria-label': 'Close', on: { click: close } }, '✕'));
      back.addEventListener('click', function (e) { if (e.target === back) close(); });
      document.addEventListener('keydown', onKey);
    }
    if (opts.title) box.appendChild(h('h3.mt', opts.title));
    append(box, [typeof content === 'function' ? content(close) : content]);
    back.appendChild(box);
    document.body.appendChild(back);
    const f = box.querySelector('.btn.primary') || box.querySelector('button:not(.close)');
    if (f && opts.focus !== false) setTimeout(function () { try { f.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }, 30);
    return { close, box };
  };

  let toastTimer = 0;
  UI.toast = function (text) {
    let t = document.querySelector('.toast');
    if (!t) { t = h('div.toast', { role: 'status' }); document.body.appendChild(t); }
    t.textContent = text;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.hidden = true; }, 2600);
  };

  UI.reducedMotion = function () {
    try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
  };
  UI.wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
})(globalThis.AG = globalThis.AG || {});
