/* Möbius Universe Lab — app shell: tabs, panels, render loop, resize, hash routing. */
(function () {
  'use strict';
  const ML = window.ML;
  const $ = (s) => document.querySelector(s);
  const app = (ML.app = { current: null, w: 1, h: 1, renderer: null });

  function getRenderer() {
    if (app.renderer || !window.THREE) return app.renderer;
    try {
      const r = new THREE.WebGLRenderer({ canvas: app.gl, antialias: true });
      r.setPixelRatio(ML.dpr());
      r.setClearColor(0x0e1016, 1);
      r.setSize(app.w, app.h, false);
      app.renderer = r;
    } catch (e) { app.renderer = null; }
    return app.renderer;
  }
  app.getRenderer = getRenderer;

  function drawBrand() {
    const cv = $('#brandmark'), g = cv.getContext('2d');
    const W = cv.width, H = cv.height;
    g.clearRect(0, 0, W, H);
    const quads = [];
    const N = 90, n = 1, R = 1, w = 0.42, rx = 1.05, rz = 0.35;
    const P = [0, 0, 0], Q = [0, 0, 0];
    const proj = (p) => {
      // rotate about x then z for a 3/4 view
      let y = p[1] * Math.cos(rx) - p[2] * Math.sin(rx), z = p[1] * Math.sin(rx) + p[2] * Math.cos(rx), x = p[0];
      const x2 = x * Math.cos(rz) - y * Math.sin(rz), y2 = x * Math.sin(rz) + y * Math.cos(rz);
      return [W / 2 + x2 * W * 0.33, H / 2 - y2 * H * 0.33, z];
    };
    for (let i = 0; i < N; i++) {
      const t0 = (i / N) * ML.TAU, t1 = ((i + 1) / N) * ML.TAU;
      const a = proj(ML.band.P(t0, -w, n, R, P)), b = proj(ML.band.P(t0, w, n, R, Q));
      const c = proj(ML.band.P(t1, w, n, R, P)), d = proj(ML.band.P(t1, -w, n, R, Q));
      const cross = (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0]);
      quads.push({ pts: [a, b, c, d], z: (a[2] + b[2] + c[2] + d[2]) / 4, front: cross > 0 });
    }
    quads.sort((p, q) => p.z - q.z);
    for (const q of quads) {
      g.beginPath(); q.pts.forEach((p, k) => (k ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]))); g.closePath();
      g.fillStyle = q.front ? '#f28cb1' : '#a8466b'; g.fill();
      g.strokeStyle = q.front ? '#f28cb1' : '#a8466b'; g.lineWidth = 0.6; g.stroke();
    }
  }

  function setMode(id, fromHash) {
    const m = ML.modes[id] || ML.modes[ML.order[0]];
    if (app.current === m) return;
    if (app.current) {
      app.current.exit && app.current.exit(app);
      app.current._panel.hidden = true; app.current._hud.hidden = true;
    }
    app.current = m;
    document.querySelectorAll('.tab').forEach((t) => t.setAttribute('aria-selected', String(t.dataset.mode === m.id)));
    if (!m._built) {
      m.buildPanel(m._panel); m.buildHud && m.buildHud(m._hud);
      m._built = true;
    }
    m._panel.hidden = false; m._hud.hidden = false;
    const is3d = m.kind === '3d';
    app.gl.hidden = !is3d; app.c2d.hidden = is3d;
    if (is3d && !getRenderer()) {
      m._panel.prepend(ML.el('div', { class: 'callout', html: '<b>3D view unavailable.</b> This browser could not start WebGL, so this tab cannot draw. The Universe, Stretched Strip and Helix Shot tabs still work.' }));
    }
    if (!m._inited) { m.init && m.init(app); m._inited = true; }
    m.enter && m.enter(app);
    m.resize && m.resize(app.w, app.h);
    app.panel.scrollTop = 0;
    if (!fromHash && location.hash !== '#' + m.id) {
      try { history.replaceState(null, '', '#' + m.id); } catch (e) { /* sandboxed */ }
    }
  }
  app.setMode = setMode;

  function onResize() {
    const r = app.stage.getBoundingClientRect();
    app.w = Math.max(1, Math.floor(r.width)); app.h = Math.max(1, Math.floor(r.height));
    if (app.renderer) app.renderer.setSize(app.w, app.h, false);
    if (app.current && app.current.resize) app.current.resize(app.w, app.h);
  }

  let last = performance.now();
  function loop(now) {
    requestAnimationFrame(loop);
    const dt = Math.min(0.05, Math.max(0.001, (now - last) / 1000));
    last = now;
    if (document.hidden || !app.current) return;
    try { app.current.frame(dt, now / 1000); } catch (e) {
      if (!app._errShown) { app._errShown = true; console.error(e); }
    }
  }

  function boot() {
    app.stage = $('#stage'); app.gl = $('#gl'); app.c2d = $('#c2d'); app.hud = $('#hud'); app.panel = $('#panel');
    app.reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    drawBrand();
    const tabs = $('#tabs');
    ML.order.forEach((id) => {
      const m = ML.modes[id];
      const b = ML.el('button', { class: 'tab', role: 'tab', type: 'button', 'data-mode': id, id: 'tab-' + id, text: m.tab, 'aria-selected': 'false' });
      b.addEventListener('click', () => setMode(id));
      tabs.append(b);
      m._panel = ML.el('section', { class: 'pm', id: 'panel-' + id, role: 'tabpanel', 'aria-labelledby': 'tab-' + id, hidden: true });
      m._hud = ML.el('div', { class: 'hud', id: 'hud-' + id, hidden: true });
      app.panel.append(m._panel); app.hud.append(m._hud);
    });
    if (!window.THREE) console.warn('three.js did not load; 3D tabs disabled.');
    const r = app.stage.getBoundingClientRect();
    app.w = Math.max(1, Math.floor(r.width)); app.h = Math.max(1, Math.floor(r.height));
    if ('ResizeObserver' in window) new ResizeObserver(onResize).observe(app.stage);
    else window.addEventListener('resize', onResize);
    const h = (location.hash || '').replace('#', '');
    setMode(ML.modes[h] ? h : ML.order[0], true);
    window.addEventListener('hashchange', () => { const k = location.hash.replace('#', ''); if (ML.modes[k]) setMode(k, true); });
    requestAnimationFrame(loop);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
