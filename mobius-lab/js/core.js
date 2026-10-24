/* Möbius Universe Lab — shared core: math, band geometry, topology, UI, charts, camera. */
(function () {
  'use strict';
  const ML = (window.ML = window.ML || {});
  ML.modes = {};
  ML.order = [];
  ML.register = function (mode) { ML.modes[mode.id] = mode; ML.order.push(mode.id); };

  // ------------------------------------------------------------------ math
  const TAU = Math.PI * 2;
  ML.TAU = TAU;
  ML.clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
  ML.lerp = (a, b, t) => a + (b - a) * t;
  ML.smooth = (t) => t * t * (3 - 2 * t);
  ML.gauss = function () {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * v);
  };
  ML.wrapAngle = (a) => { a %= TAU; if (a > Math.PI) a -= TAU; if (a < -Math.PI) a += TAU; return a; };
  ML.fmt = function (x, d) {
    if (!isFinite(x)) return '—';
    const ax = Math.abs(x);
    if (ax >= 1e6) return (x / 1e6).toFixed(1) + 'M';
    if (ax >= 1e4) return (x / 1e3).toFixed(1) + 'K';
    return x.toFixed(d === undefined ? 0 : d);
  };
  ML.pct = (x, d) => (x * 100).toFixed(d === undefined ? 0 : d) + '%';

  // ------------------------------------------------------------------ colors
  ML.hex2rgb = function (h) {
    h = h.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  };
  ML.rgba = function (h, a) { const c = ML.hex2rgb(h); return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; };
  ML.cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  // Shared colors for canvases (kept in sync with the CSS tokens).
  ML.C = {
    ink: '#0e1016', panel: '#151925', panel2: '#1c2130', hair: '#2a3144',
    fg: '#ece8f1', fg2: '#aab0c4', muted: '#747c93',
    paper: '#f28cb1', paperDeep: '#d9668f', rule: '#6f8cff', tape: '#f3c96e',
    s1: '#3987e5', s2: '#d95926', s3: '#199e70', crit: '#d03b3b', good: '#0ca30c', warn: '#fab219',
    // paper colours for cut pieces (the construction-paper set)
    pieces: ['#f28cb1', '#8fb4ff', '#f3c96e', '#86dcb4', '#c7a6ff', '#ff9f80'],
  };

  // ------------------------------------------------------------------ band geometry (three.js coords, y up)
  // Core circle radius R in the xz-plane. Cross direction rotates n/2 turns per lap:
  // dir(t) = cos(nt/2)·radial + sin(nt/2)·ŷ.   P(t,s) = core(t) + s·dir(t)
  ML.band = {
    P(t, s, n, R, o) {
      const a = (n * t) / 2, ca = Math.cos(a), sa = Math.sin(a), ct = Math.cos(t), st = Math.sin(t);
      o[0] = R * ct + s * ca * ct; o[1] = s * sa; o[2] = R * st + s * ca * st; return o;
    },
    dir(t, n, o) {
      const a = (n * t) / 2, ca = Math.cos(a), sa = Math.sin(a);
      o[0] = ca * Math.cos(t); o[1] = sa; o[2] = ca * Math.sin(t); return o;
    },
    Pt(t, s, n, R, o) {
      const a = (n * t) / 2, ap = n / 2, ca = Math.cos(a), sa = Math.sin(a), ct = Math.cos(t), st = Math.sin(t);
      o[0] = -R * st + s * (-ap * sa * ct - ca * st);
      o[1] = s * ap * ca;
      o[2] = R * ct + s * (-ap * sa * st + ca * ct);
      return o;
    },
    normal(t, s, n, R, o) {
      const pt = ML.band.Pt(t, s, n, R, [0, 0, 0]), ps = ML.band.dir(t, n, [0, 0, 0]);
      const x = pt[1] * ps[2] - pt[2] * ps[1], y = pt[2] * ps[0] - pt[0] * ps[2], z = pt[0] * ps[1] - pt[1] * ps[0];
      const l = Math.hypot(x, y, z) || 1; o[0] = x / l; o[1] = y / l; o[2] = z / l; return o;
    },
  };

  // ------------------------------------------------------------------ topology: exact linking number & writhe of polygons
  // Klenin & Langowski (2000): solid angle subtended by two segments; sums to an exact integer for closed curves.
  function segOmega(a0, a1, a2, b0, b1, b2, c0, c1, c2, d0, d1, d2) {
    const r13x = c0 - a0, r13y = c1 - a1, r13z = c2 - a2;
    const r14x = d0 - a0, r14y = d1 - a1, r14z = d2 - a2;
    const r23x = c0 - b0, r23y = c1 - b1, r23z = c2 - b2;
    const r24x = d0 - b0, r24y = d1 - b1, r24z = d2 - b2;
    function cr(ax, ay, az, bx, by, bz, out) {
      let x = ay * bz - az * by, y = az * bx - ax * bz, z = ax * by - ay * bx;
      const l = Math.hypot(x, y, z);
      if (l < 1e-14) return false;
      out[0] = x / l; out[1] = y / l; out[2] = z / l; return true;
    }
    const n1 = segOmega.n1, n2 = segOmega.n2, n3 = segOmega.n3, n4 = segOmega.n4;
    if (!cr(r13x, r13y, r13z, r14x, r14y, r14z, n1)) return 0;
    if (!cr(r14x, r14y, r14z, r24x, r24y, r24z, n2)) return 0;
    if (!cr(r24x, r24y, r24z, r23x, r23y, r23z, n3)) return 0;
    if (!cr(r23x, r23y, r23z, r13x, r13y, r13z, n4)) return 0;
    const as = (u, v) => Math.asin(ML.clamp(u[0] * v[0] + u[1] * v[1] + u[2] * v[2], -1, 1));
    const om = as(n1, n2) + as(n2, n3) + as(n3, n4) + as(n4, n1);
    const r34x = d0 - c0, r34y = d1 - c1, r34z = d2 - c2;
    const r12x = b0 - a0, r12y = b1 - a1, r12z = b2 - a2;
    const sx = r34y * r12z - r34z * r12y, sy = r34z * r12x - r34x * r12z, sz = r34x * r12y - r34y * r12x;
    const sg = sx * r13x + sy * r13y + sz * r13z;
    return sg > 0 ? om : sg < 0 ? -om : 0;
  }
  segOmega.n1 = [0, 0, 0]; segOmega.n2 = [0, 0, 0]; segOmega.n3 = [0, 0, 0]; segOmega.n4 = [0, 0, 0];

  ML.topo = {
    // A, B: flat arrays [x,y,z,...] of closed polygons
    linking(A, B) {
      const na = A.length / 3, nb = B.length / 3;
      let s = 0;
      for (let i = 0; i < na; i++) {
        const i2 = (i + 1) % na;
        const a0 = A[3 * i], a1 = A[3 * i + 1], a2 = A[3 * i + 2], b0 = A[3 * i2], b1 = A[3 * i2 + 1], b2 = A[3 * i2 + 2];
        for (let j = 0; j < nb; j++) {
          const j2 = (j + 1) % nb;
          s += segOmega(a0, a1, a2, b0, b1, b2, B[3 * j], B[3 * j + 1], B[3 * j + 2], B[3 * j2], B[3 * j2 + 1], B[3 * j2 + 2]);
        }
      }
      return s / (4 * Math.PI);
    },
    writhe(A) {
      const n = A.length / 3;
      let s = 0;
      for (let i = 0; i < n; i++) {
        const i2 = (i + 1) % n;
        for (let j = i + 2; j < n; j++) {
          if (i === 0 && j === n - 1) continue;
          const j2 = (j + 1) % n;
          s += segOmega(A[3 * i], A[3 * i + 1], A[3 * i + 2], A[3 * i2], A[3 * i2 + 1], A[3 * i2 + 2],
            A[3 * j], A[3 * j + 1], A[3 * j + 2], A[3 * j2], A[3 * j2 + 1], A[3 * j2 + 2]);
        }
      }
      return (2 * s) / (4 * Math.PI);
    },
    // (2,n) torus knot names for odd n
    torusName(n) {
      const a = Math.abs(n);
      if (a <= 1) return 'unknot';
      if (a === 3) return 'trefoil (3₁)';
      if (a === 5) return 'cinquefoil (5₁)';
      if (a === 7) return 'septafoil (7₁)';
      return 'torus knot T(2,' + a + ')';
    },
  };

  // ------------------------------------------------------------------ DOM / UI builders
  function el(tag, attrs, kids) {
    const e = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      const v = attrs[k];
      if (v === undefined || v === null || v === false) continue;
      if (k === 'class') e.className = v;
      else if (k === 'html') e.innerHTML = v;
      else if (k === 'text') e.textContent = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? '' : v);
    }
    if (kids) (Array.isArray(kids) ? kids : [kids]).forEach((c) => c != null && e.append(c));
    return e;
  }
  ML.el = el;

  ML.ui = {
    head(parent, title, lede) {
      const h = el('header', { class: 'pm-head' }, [el('h2', { text: title }), lede ? el('p', { html: lede }) : null]);
      parent.append(h); return h;
    },
    block(parent, title) {
      const b = el('section', { class: 'blk' });
      if (title) b.append(el('h3', { text: title }));
      parent.append(b); return b;
    },
    slider(parent, o) {
      const out = el('output', { for: o.id });
      const inp = el('input', { type: 'range', id: o.id, min: o.min, max: o.max, step: o.step, value: o.value });
      const fmt = o.fmt || ((v) => String(v));
      const wrap = el('div', { class: 'ctl' }, [el('label', { class: 'ctl-top', for: o.id }, [el('span', { text: o.label }), out]), inp]);
      const upd = () => { out.textContent = fmt(+inp.value); };
      inp.addEventListener('input', () => { upd(); o.onInput && o.onInput(+inp.value); });
      upd(); parent.append(wrap);
      return { el: wrap, input: inp, get: () => +inp.value, set(v) { inp.value = v; upd(); } };
    },
    seg(parent, o) {
      const btns = [];
      const box = el('div', { class: 'seg', role: 'group', 'aria-label': o.label });
      let val = o.value;
      const sync = () => btns.forEach((b) => b.setAttribute('aria-pressed', String(b._v === val)));
      o.options.forEach(([v, lbl, title]) => {
        const b = el('button', { type: 'button', id: o.id + '-' + String(v).replace(/^-/, 'neg').replace(/[^a-z0-9]/gi, ''), title: title || null, text: lbl });
        b._v = v;
        b.addEventListener('click', () => { val = v; sync(); o.onChange && o.onChange(v); });
        btns.push(b); box.append(b);
      });
      sync();
      const wrap = el('div', { class: 'ctl' }, [o.label ? el('div', { class: 'ctl-top' }, [el('span', { text: o.label })]) : null, box]);
      parent.append(wrap);
      return { el: wrap, get: () => val, set(v) { val = v; sync(); } };
    },
    toggle(parent, o) {
      const inp = el('input', { type: 'checkbox', id: o.id, role: 'switch' });
      inp.checked = !!o.value;
      inp.addEventListener('change', () => o.onChange && o.onChange(inp.checked));
      const lab = el('label', { class: 'tog', for: o.id }, [el('span', { text: o.label }), inp]);
      parent.append(lab);
      return { el: lab, get: () => inp.checked, set(v) { inp.checked = !!v; } };
    },
    buttons(parent, list) {
      const row = el('div', { class: 'row' });
      const out = list.map((b) => {
        const e = el('button', { type: 'button', class: 'btn' + (b.primary ? ' primary' : ''), id: b.id, text: b.label, title: b.title || null });
        e.addEventListener('click', b.onClick);
        row.append(e); return e;
      });
      parent.append(row); return out;
    },
    readouts(parent, rows) {
      const dl = el('dl', { class: 'ro' });
      const map = {};
      rows.forEach(([k, label]) => {
        const dd = el('dd');
        dl.append(el('dt', { text: label }), dd);
        map[k] = dd;
      });
      parent.append(dl);
      const last = {};
      return {
        el: dl,
        set(k, v) { if (last[k] !== v) { last[k] = v; map[k].textContent = v; } },
        html(k, v) { if (last[k] !== v) { last[k] = v; map[k].innerHTML = v; } },
        meter(k, text, frac) {
          const key = text + '|' + Math.round(frac * 200);
          if (last[k] === key) return; last[k] = key;
          map[k].innerHTML = text + '<div class="meter"><i style="width:' + (ML.clamp(frac, 0, 1) * 100).toFixed(1) + '%"></i></div>';
        },
      };
    },
    callout(parent, html) { const c = el('div', { class: 'callout', html }); parent.append(c); return c; },
    ideas(parent, html, open) {
      const d = el('details', { class: 'ideas' }, [el('summary', { text: 'Your idea ↔ real physics' }), el('div', { class: 'ideas-body', html })]);
      if (open) d.open = true;
      parent.append(d); return d;
    },
  };

  // ------------------------------------------------------------------ canvases & charts
  ML.dpr = () => Math.min(window.devicePixelRatio || 1, 2);
  ML.fitCanvas = function (cv, w, h) {
    const d = ML.dpr();
    const W = Math.max(1, Math.round(w * d)), H = Math.max(1, Math.round(h * d));
    if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
    const ctx = cv.getContext('2d');
    ctx.setTransform(d, 0, 0, d, 0, 0);
    return ctx;
  };

  let tipEl = null;
  ML.tooltip = function (html, x, y) {
    if (!tipEl) {
      tipEl = el('div', { role: 'status' });
      Object.assign(tipEl.style, {
        position: 'fixed', zIndex: 50, pointerEvents: 'none', background: ML.C.panel2, color: ML.C.fg,
        border: '1px solid ' + ML.C.hair, borderRadius: '6px', padding: '6px 8px', font: '500 12px/1.35 ' + "'IBM Plex Mono', monospace",
        boxShadow: '0 6px 18px rgba(0,0,0,.35)', maxWidth: '240px',
      });
      document.body.append(tipEl);
    }
    if (!html) { tipEl.hidden = true; return; }
    tipEl.hidden = false; tipEl.innerHTML = html;
    const r = tipEl.getBoundingClientRect();
    let lx = x + 14, ly = y - r.height - 10;
    if (lx + r.width > window.innerWidth - 8) lx = x - r.width - 14;
    if (ly < 8) ly = y + 16;
    tipEl.style.left = lx + 'px'; tipEl.style.top = ly + 'px';
  };
  ML.attachHover = function (cv, fn) {
    cv.addEventListener('pointermove', (e) => {
      const r = cv.getBoundingClientRect();
      const h = fn(e.clientX - r.left, e.clientY - r.top, r.width, r.height);
      ML.tooltip(h, e.clientX, e.clientY);
    });
    cv.addEventListener('pointerleave', () => ML.tooltip(null));
  };

  // rounded-top bar path (4px data end, square at baseline)
  ML.barPath = function (ctx, x, y, w, h) {
    const r = Math.min(4, w / 2, Math.abs(h));
    ctx.beginPath();
    if (h >= 0) { // grows upward from baseline y+h... (y is top)
      ctx.moveTo(x, y + h); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h);
    }
    ctx.closePath();
  };

  // Sparkline: one series, area wash, 2px line, ringed end dot.
  ML.spark = function (cv, vals, color, opts) {
    opts = opts || {};
    const r = cv.getBoundingClientRect();
    const w = r.width || 300, h = r.height || 36;
    const ctx = ML.fitCanvas(cv, w, h);
    ctx.clearRect(0, 0, w, h);
    if (vals.length < 2) return;
    let lo = opts.min !== undefined ? opts.min : Infinity, hi = opts.max !== undefined ? opts.max : -Infinity;
    if (opts.min === undefined || opts.max === undefined) for (const v of vals) { if (opts.min === undefined) lo = Math.min(lo, v); if (opts.max === undefined) hi = Math.max(hi, v); }
    if (hi - lo < 1e-9) hi = lo + 1;
    const pad = 5;
    const X = (i) => pad + (i / (vals.length - 1)) * (w - 2 * pad);
    const Y = (v) => h - pad - ((v - lo) / (hi - lo)) * (h - 2 * pad);
    ctx.strokeStyle = ML.C.hair; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad, h - pad + 0.5); ctx.lineTo(w - pad, h - pad + 0.5); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(X(0), Y(vals[0]));
    for (let i = 1; i < vals.length; i++) ctx.lineTo(X(i), Y(vals[i]));
    ctx.lineTo(X(vals.length - 1), h - pad); ctx.lineTo(X(0), h - pad); ctx.closePath();
    ctx.fillStyle = ML.rgba(color, 0.1); ctx.fill();
    ctx.beginPath(); ctx.moveTo(X(0), Y(vals[0]));
    for (let i = 1; i < vals.length; i++) ctx.lineTo(X(i), Y(vals[i]));
    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
    const ex = X(vals.length - 1), ey = Y(vals[vals.length - 1]);
    ctx.beginPath(); ctx.arc(ex, ey, 4, 0, TAU); ctx.fillStyle = color; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = ML.C.panel; ctx.stroke();
  };

  // Histogram: one series. bins = array of counts. labels: {left, mid, right} under the axis.
  ML.hist = function (cv, bins, color, opts) {
    opts = opts || {};
    const r = cv.getBoundingClientRect();
    const w = r.width || 300, h = r.height || 120;
    const ctx = ML.fitCanvas(cv, w, h);
    ctx.clearRect(0, 0, w, h);
    const padL = 6, padR = 6, padT = 8, padB = 20;
    const n = bins.length;
    let mx = 0; for (const b of bins) mx = Math.max(mx, b);
    const iw = w - padL - padR, ih = h - padT - padB;
    const slot = iw / n, bw = Math.min(24, Math.max(1, slot - 2));
    // gridlines
    ctx.strokeStyle = ML.C.hair; ctx.lineWidth = 1;
    for (let g = 1; g <= 2; g++) { const y = Math.round(padT + ih - (g / 2) * ih) + 0.5; ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - padR, y); ctx.stroke(); }
    if (mx > 0) {
      ctx.fillStyle = color;
      for (let i = 0; i < n; i++) {
        const bh = (bins[i] / mx) * ih;
        if (bh <= 0) continue;
        const x = padL + i * slot + (slot - bw) / 2;
        ML.barPath(ctx, x, padT + ih - bh, bw, bh); ctx.fill();
      }
    }
    ctx.strokeStyle = '#3a4258'; ctx.beginPath(); ctx.moveTo(padL, padT + ih + 0.5); ctx.lineTo(w - padR, padT + ih + 0.5); ctx.stroke();
    if (opts.marks) {
      ctx.fillStyle = ML.C.muted; ctx.font = '500 11px "IBM Plex Mono", monospace'; ctx.textBaseline = 'top';
      opts.marks.forEach(([f, txt]) => {
        const x = padL + f * iw;
        ctx.textAlign = f < 0.05 ? 'left' : f > 0.95 ? 'right' : 'center';
        ctx.fillText(txt, x, padT + ih + 5);
      });
    }
    return { padL, padR, padT, padB, iw, ih, slot, n, w, h };
  };

  // ------------------------------------------------------------------ paper textures (the pink lined index cards)
  // Atlas: top half (v 0.5..1) = ruled face, bottom half (v 0..0.5) = blank back.
  ML.paperAtlas = function (opts) {
    opts = opts || {};
    const W = 512, H = 256;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const g = cv.getContext('2d', { willReadFrequently: true });
    const base = opts.base || '#ffffff';
    g.fillStyle = base; g.fillRect(0, 0, W, H);
    // paper grain
    const img = g.getImageData(0, 0, W, H), d = img.data;
    for (let i = 0; i < d.length; i += 4) { const k = (Math.random() - 0.5) * 14; d[i] += k; d[i + 1] += k; d[i + 2] += k; }
    g.putImageData(img, 0, 0);
    // ruled lines across the strip on the top half
    g.strokeStyle = opts.line || 'rgba(50,62,150,0.85)'; g.lineWidth = 3;
    const nLines = opts.lines || 4;
    for (let i = 0; i < nLines; i++) {
      const x = ((i + 0.5) / nLines) * W;
      g.beginPath(); g.moveTo(x, 4); g.lineTo(x + 1, H / 2 - 4); g.stroke();
    }
    // slightly deeper tone on the blank back so faces read differently
    g.fillStyle = 'rgba(120,40,70,0.10)'; g.fillRect(0, H / 2, W, H / 2);
    const tex = new THREE.CanvasTexture(cv);
    tex.wrapS = THREE.RepeatWrapping; tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.anisotropy = 4;
    return tex;
  };

  // ------------------------------------------------------------------ orbit camera (no dependency)
  class Orbit {
    constructor(dom, o) {
      o = o || {};
      this.dom = dom;
      this.target = new THREE.Vector3(0, 0, 0);
      this.theta = o.theta !== undefined ? o.theta : 0.6;
      this.phi = o.phi !== undefined ? o.phi : 1.0;
      this.radius = o.radius || 4;
      this.minR = o.minR || 1.2; this.maxR = o.maxR || 14;
      this.enabled = false;
      this.anim = null;
      this.autoSpin = 0;
      this.onClick = null;
      this.pointers = new Map();
      this.moved = 0;
      this._bind();
    }
    _bind() {
      const d = this.dom;
      d.addEventListener('pointerdown', (e) => {
        if (!this.enabled) return;
        d.setPointerCapture(e.pointerId);
        this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
        this.moved = 0; this.anim = null;
        if (this.pointers.size === 2) { const p = [...this.pointers.values()]; this.pinch = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); }
      });
      d.addEventListener('pointermove', (e) => {
        if (!this.enabled || !this.pointers.has(e.pointerId)) return;
        const prev = this.pointers.get(e.pointerId);
        const dx = e.clientX - prev.x, dy = e.clientY - prev.y;
        this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
        this.moved += Math.abs(dx) + Math.abs(dy);
        if (this.pointers.size === 1) {
          this.theta += dx * 0.008; this.phi = ML.clamp(this.phi - dy * 0.008, 0.05, Math.PI - 0.05);
        } else if (this.pointers.size === 2) {
          const p = [...this.pointers.values()];
          const dist = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y);
          if (this.pinch) this.radius = ML.clamp(this.radius * (this.pinch / dist), this.minR, this.maxR);
          this.pinch = dist;
        }
      });
      const up = (e) => {
        if (!this.pointers.has(e.pointerId)) return;
        this.pointers.delete(e.pointerId);
        if (this.pointers.size === 0 && this.moved < 6 && this.onClick && this.enabled) {
          const r = d.getBoundingClientRect();
          this.onClick(e.clientX - r.left, e.clientY - r.top, r.width, r.height);
        }
        if (this.pointers.size < 2) this.pinch = 0;
      };
      d.addEventListener('pointerup', up); d.addEventListener('pointercancel', up);
      d.addEventListener('wheel', (e) => {
        if (!this.enabled) return;
        e.preventDefault();
        this.radius = ML.clamp(this.radius * Math.exp(e.deltaY * 0.0012), this.minR, this.maxR);
      }, { passive: false });
    }
    animateTo(t, dur) {
      let dth = ML.wrapAngle((t.theta !== undefined ? t.theta : this.theta) - this.theta);
      this.anim = { t: 0, dur: dur || 1.1, from: { theta: this.theta, phi: this.phi, radius: this.radius },
        to: { theta: this.theta + dth, phi: t.phi !== undefined ? t.phi : this.phi, radius: t.radius !== undefined ? t.radius : this.radius } };
    }
    update(dt) {
      if (this.anim) {
        const a = this.anim; a.t += dt;
        const k = ML.smooth(Math.min(1, a.t / a.dur));
        this.theta = ML.lerp(a.from.theta, a.to.theta, k);
        this.phi = ML.lerp(a.from.phi, a.to.phi, k);
        this.radius = ML.lerp(a.from.radius, a.to.radius, k);
        if (a.t >= a.dur) this.anim = null;
      } else if (this.autoSpin && this.pointers.size === 0) this.theta += this.autoSpin * dt;
    }
    // aspect: on tall (portrait) views pull back so the whole object stays in frame
    apply(cam, aspect) {
      const r = this.radius * (aspect ? Math.max(1, 1.2 / aspect) : 1), s = Math.sin(this.phi);
      cam.position.set(this.target.x + r * s * Math.cos(this.theta), this.target.y + r * Math.cos(this.phi), this.target.z + r * s * Math.sin(this.theta));
      cam.up.set(0, 1, 0);
      cam.lookAt(this.target);
    }
  }
  ML.Orbit = Orbit;

  // Render one free camera, or four views (top / front / side / free) like four monitors.
  ML.quadCams = null;
  ML.render3D = function (renderer, scene, cam, quad, w, h, dist) {
    if (!quad) {
      renderer.setScissorTest(false);
      renderer.setViewport(0, 0, w, h);
      cam.aspect = w / h; cam.updateProjectionMatrix();
      renderer.render(scene, cam);
      return;
    }
    if (!ML.quadCams) ML.quadCams = [0, 1, 2].map(() => new THREE.PerspectiveCamera(35, 1, 0.05, 100));
    const hw = Math.floor(w / 2), hh = Math.floor(h / 2);
    const d = dist || 5.2;
    const views = [
      [ML.quadCams[0], [0, d, 0.0001], 0, hh],
      [ML.quadCams[1], [0, 0, d], hw, hh],
      [ML.quadCams[2], [d, 0, 0], 0, 0],
      [cam, null, hw, 0],
    ];
    renderer.setScissorTest(true);
    for (const [c, pos, x, y] of views) {
      if (pos) { c.position.set(pos[0], pos[1], pos[2]); c.up.set(0, pos[1] > 0 ? 0 : 1, pos[1] > 0 ? -1 : 0); c.lookAt(0, 0, 0); }
      c.aspect = hw / hh; c.updateProjectionMatrix();
      renderer.setViewport(x, y, hw, hh); renderer.setScissor(x, y, hw, hh);
      renderer.render(scene, c);
    }
    renderer.setScissorTest(false);
  };
  // returns {camera, ndc} for a click at css coords inside the stage
  ML.pickView = function (cam, quad, x, y, w, h) {
    if (!quad) return { cam, nx: (x / w) * 2 - 1, ny: -(y / h) * 2 + 1 };
    const col = x < w / 2 ? 0 : 1, row = y < h / 2 ? 0 : 1;
    const lx = x - col * (w / 2), ly = y - row * (h / 2);
    const nx = (lx / (w / 2)) * 2 - 1, ny = -(ly / (h / 2)) * 2 + 1;
    const c = row === 0 ? ML.quadCams[col] : col === 0 ? ML.quadCams[2] : cam;
    return { cam: c, nx, ny };
  };

  // Labels and dividers for the four-monitor view (labels top-right of each quarter, clear of the HUD title).
  ML.quadHud = function () {
    const q = ML.el('div', { class: 'quadlines' });
    [['Top', '8px', 'calc(50% + 8px)'], ['Front', '8px', '8px'], ['Side', 'calc(50% + 8px)', 'calc(50% + 8px)'], ['Free', 'calc(50% + 8px)', '8px']]
      .forEach(([t, top, right]) => q.append(ML.el('span', { class: 'quadlbl', text: t, style: 'top:' + top + ';right:' + right })));
    q.hidden = true;
    return q;
  };

  // Shared lighting rig for the 3D paper scenes.
  ML.paperLights = function (scene) {
    scene.add(new THREE.HemisphereLight(0xe6e0ff, 0x241a2c, 0.62));
    const key = new THREE.DirectionalLight(0xfff4ea, 0.62); key.position.set(3, 5, 4); scene.add(key);
    const rim = new THREE.DirectionalLight(0x8fa6ff, 0.3); rim.position.set(-4, -2, -3); scene.add(rim);
  };
  ML.floorGrid = function (scene, y) {
    const g = new THREE.Group();
    const mat = new THREE.LineBasicMaterial({ color: 0x2a3144, transparent: true, opacity: 0.55 });
    for (let r = 0.5; r <= 3; r += 0.5) {
      const pts = [];
      for (let i = 0; i <= 96; i++) { const a = (i / 96) * TAU; pts.push(new THREE.Vector3(r * Math.cos(a), y, r * Math.sin(a))); }
      g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mat));
    }
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * TAU;
      g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0.5 * Math.cos(a), y, 0.5 * Math.sin(a)), new THREE.Vector3(3 * Math.cos(a), y, 3 * Math.sin(a))]), mat));
    }
    scene.add(g); return g;
  };
})();
