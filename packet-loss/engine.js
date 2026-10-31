/* Packet Loss · engine.js
   Canvas renderer, theme tokens, adaptive layout, drawing primitives and the
   timeline player. The script and every scene live in scenes.js.
   Each frame is a pure function of time, so the player can seek anywhere and
   render-video.cjs can export frame-exact video. */
(function () {
  'use strict';
  const PL = (window.PL = window.PL || {});

  /* ---------------- math ---------------- */
  const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  const E = {
    lin: (t) => t,
    io: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    out: (t) => 1 - Math.pow(1 - t, 3),
    in: (t) => t * t * t,
    back: (t) => {
      const c1 = 1.70158, c3 = c1 + 1;
      return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
    },
    sine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  };
  const seg = (t, a, b, ease) => (ease || E.io)(clamp((t - a) / (b - a || 1e-6)));
  const fadeIO = (t, a, b, f = 0.3) => Math.min(seg(t, a, a + f, E.lin), 1 - seg(t, b - f, b, E.lin));
  function rng(seed) {
    let s = seed >>> 0;
    return function () {
      s = (s + 0x6d2b79f5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const quad = (p0, p1, p2, t) => {
    const u = 1 - t;
    return [u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]];
  };

  /* ---------------- theme ---------------- */
  const TOKENS = {
    bg: '--c-bg', raise: '--c-raise', grid: '--c-grid', rule: '--c-rule', line: '--c-line', lineHi: '--c-line-hi',
    ink: '--c-ink', dim: '--c-dim', faint: '--c-faint', warm: '--c-warm', gold: '--c-gold', yes: '--c-yes',
    no: '--c-no', power: '--c-power', dead: '--c-dead',
  };
  const P = {};
  function readPalette() {
    const cs = getComputedStyle(document.documentElement);
    for (const k in TOKENS) P[k] = (cs.getPropertyValue(TOKENS[k]) || '').trim() || '#888888';
  }
  const rgbaCache = new Map();
  function rgba(hex, a) {
    const key = hex + '|' + a;
    let v = rgbaCache.get(key);
    if (v) return v;
    let h = String(hex || '#888888').replace('#', '');
    if (h.length === 3) h = h.split('').map((ch) => ch + ch).join('');
    const n = parseInt(h.slice(0, 6), 16) || 0;
    v = 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + clamp(a) + ')';
    if (rgbaCache.size > 4000) rgbaCache.clear();
    rgbaCache.set(key, v);
    return v;
  }
  const F = {
    mono: '"Martian Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace',
    sans: '"Atkinson Hyperlegible", "Segoe UI", system-ui, -apple-system, sans-serif',
    serif: '"Newsreader", Georgia, "Times New Roman", serif',
  };
  const font = (fam, size, wt = 400, it = false) =>
    (it ? 'italic ' : '') + wt + ' ' + Math.round(size * 10) / 10 + 'px ' + (F[fam] || F.sans);

  /* ---------------- canvas + layout ---------------- */
  const stageEl = document.getElementById('stage');
  const cv = document.getElementById('cv');
  const ctx = cv.getContext('2d');
  const bgCv = document.createElement('canvas');
  const bgCtx = bgCv.getContext('2d');
  const RM = /^#render-(land|port)$/.exec(location.hash || '');
  const forced = RM ? RM[1] : null;
  let W = 1920, H = 1080, ORIENT = 'land', SC = 1, curScale = 1, lastW = 0;
  const L = {};

  function computeLayout() {
    if (ORIENT === 'land') {
      Object.assign(L, {
        header: { x: 96, y: 36, w: 1728, h: 150 },
        main: { x: 96, y: 196, w: 1000, h: 680 },
        side: { x: 1150, y: 196, w: 674, h: 680 },
        cap: { x: 96, y: 904, w: 1728, h: 150 },
        sideMode: 'tall',
      });
    } else {
      const capH = 238, capY = H - capH - 24, mainY = 214, mainH = 647;
      const sideY = mainY + mainH + 20, sideH = capY - 18 - sideY;
      Object.assign(L, {
        header: { x: 64, y: 30, w: 952, h: 180 },
        main: { x: 64, y: mainY, w: 952, h: mainH },
        side: { x: 64, y: sideY, w: 952, h: sideH },
        cap: { x: 64, y: capY, w: 952, h: capH },
        sideMode: sideH >= 600 ? 'tall' : 'wide',
      });
    }
  }

  function buildBg() {
    bgCv.width = cv.width;
    bgCv.height = cv.height;
    const g = bgCtx;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.fillStyle = P.bg;
    g.fillRect(0, 0, bgCv.width, bgCv.height);
    g.setTransform(SC, 0, 0, SC, 0, 0);
    g.lineWidth = 1 / SC;
    g.strokeStyle = P.grid;
    g.beginPath();
    for (let x = 0; x <= W; x += 40) { g.moveTo(x, 0); g.lineTo(x, H); }
    for (let y = 0; y <= H; y += 40) { g.moveTo(0, y); g.lineTo(W, y); }
    g.stroke();
  }

  function resize(force) {
    const r = stageEl.getBoundingClientRect();
    const cw = Math.max(1, r.width);
    if (!force && !forced && Math.abs(cw - lastW) < 1) return;
    lastW = cw;
    let ch;
    if (forced) {
      ORIENT = forced;
      ch = Math.max(1, r.height);
    } else {
      ORIENT = cw < 760 ? 'port' : 'land';
      if (ORIENT === 'land') ch = Math.round((cw * 9) / 16);
      else {
        const avail = Math.max(480, (window.innerHeight || 800) - 140);
        ch = Math.round((cw * clamp((1080 * avail) / cw, 1600, 1920)) / 1080);
      }
      stageEl.style.height = ch + 'px';
    }
    if (ORIENT === 'land') { W = 1920; H = 1080; } else { W = 1080; H = Math.round((1080 * ch) / cw); }
    const dpr = forced ? 1 : Math.min(2, window.devicePixelRatio || 1);
    cv.width = Math.max(1, Math.round(cw * dpr));
    cv.height = Math.max(1, Math.round(ch * dpr));
    SC = cv.width / W;
    computeLayout();
    buildBg();
    wrapCache.clear();
    needDraw = true;
    if (PL.onLayout) PL.onLayout(ORIENT);
  }

  function withLocal(bx, lw, lh, fn) {
    const s = Math.min(bx.w / lw, bx.h / lh);
    const ox = bx.x + (bx.w - lw * s) / 2, oy = bx.y + (bx.h - lh * s) / 2;
    const prev = curScale;
    ctx.save();
    ctx.translate(ox, oy);
    ctx.scale(s, s);
    curScale = prev * s;
    try { fn(s); } finally { curScale = prev; ctx.restore(); }
  }

  /* ---------------- text ---------------- */
  function setFont(o) {
    ctx.font = font(o.fam || 'sans', o.size || 30, o.wt || 400, !!o.it);
    ctx.letterSpacing = (o.track || 0) + 'px';
  }
  function measure(s, o = {}) {
    ctx.save();
    setFont(o);
    const w = ctx.measureText(String(s)).width;
    ctx.restore();
    return w;
  }
  function txt(s, x, y, o = {}) {
    if (s == null || s === '') return 0;
    s = String(s);
    ctx.save();
    let size = o.size || 30;
    setFont(o);
    if (o.maxW) {
      const w0 = ctx.measureText(s).width;
      if (w0 > o.maxW) {
        size = Math.max(o.min || 10, (size * o.maxW) / w0);
        setFont(Object.assign({}, o, { size }));
      }
    }
    ctx.textAlign = o.align || 'left';
    ctx.textBaseline = o.base || 'alphabetic';
    ctx.fillStyle = o.color || P.ink;
    if (o.a != null) ctx.globalAlpha *= clamp(o.a);
    ctx.fillText(s, x, y);
    const w = ctx.measureText(s).width;
    ctx.restore();
    return w;
  }
  const wrapCache = new Map();
  function wrap(s, maxW, o = {}) {
    const key = s + '|' + maxW + '|' + (o.fam || 'sans') + (o.size || 30) + (o.wt || 400) + (o.it ? 1 : 0);
    const hit = wrapCache.get(key);
    if (hit) return hit;
    ctx.save();
    setFont(o);
    const words = String(s).split(/\s+/);
    const lines = [];
    let cur = '';
    for (const wd of words) {
      const test = cur ? cur + ' ' + wd : wd;
      if (cur && ctx.measureText(test).width > maxW) { lines.push(cur); cur = wd; } else cur = test;
    }
    if (cur) lines.push(cur);
    ctx.restore();
    wrapCache.set(key, lines);
    return lines;
  }
  function para(s, x, y, maxW, o = {}) {
    const lines = wrap(s, maxW, o);
    const lh = (o.lh || 1.28) * (o.size || 30);
    lines.forEach((ln_, i) => txt(ln_, x, y + i * lh, o));
    return lines.length * lh;
  }
  // rich text runs: [[text, {sub, sup, bar, it, wt, color, fam}], ...]
  function rich(runs, x, y, o = {}) {
    const base = o.size || 40;
    const parts = runs.map(([s, st]) => {
      st = st || {};
      const small = st.sub || st.sup;
      const so = {
        fam: st.fam || o.fam || 'serif', it: st.it != null ? st.it : o.it != null ? o.it : true,
        wt: st.wt || o.wt || 400, size: small ? base * 0.62 : base * (st.scale || 1),
        color: st.color || o.color || P.ink, a: o.a,
      };
      return { s, st, so, w: measure(s, so) };
    });
    const total = parts.reduce((a, p) => a + p.w, 0);
    let cx = o.align === 'center' ? x - total / 2 : o.align === 'right' ? x - total : x;
    for (const p of parts) {
      const yy = y + (p.st.sub ? base * 0.24 : p.st.sup ? -base * 0.4 : 0);
      txt(p.s, cx, yy, p.so);
      if (p.st.bar) ln(cx + p.w * 0.12, y - base * 0.72, cx + p.w * 0.92, y - base * 0.72, p.so.color, Math.max(1.5, base * 0.05));
      cx += p.w;
    }
    return total;
  }

  /* ---------------- shapes ---------------- */
  function rr(x, y, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  function box(x, y, w, h, o = {}) {
    if (w <= 0 || h <= 0) return;
    rr(x, y, w, h, o.r != null ? o.r : 10);
    if (o.fill) { ctx.fillStyle = o.fill; ctx.fill(); }
    if (o.stroke) {
      ctx.strokeStyle = o.stroke;
      ctx.lineWidth = o.lw || 2;
      if (o.dash) ctx.setLineDash(o.dash);
      ctx.stroke();
      if (o.dash) ctx.setLineDash([]);
    }
  }
  function ln(x1, y1, x2, y2, color, lw = 2, dash) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.lineCap = 'round';
    if (dash) ctx.setLineDash(dash);
    ctx.stroke();
    if (dash) ctx.setLineDash([]);
  }
  function dot(x, y, r, fill, stroke, lw = 2) {
    if (r <= 0) return;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
  }
  function ring(x, y, r, a, color, lw = 2.5) {
    if (r <= 0 || a <= 0) return;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(color, a);
    ctx.lineWidth = lw;
    ctx.stroke();
  }
  function arrowHead(x, y, ang, size, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(ang);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-size, -size * 0.55);
    ctx.lineTo(-size, size * 0.55);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.restore();
  }
  function arrow(x1, y1, x2, y2, color, lw = 2.5, head = 14, dash) {
    const a = Math.atan2(y2 - y1, x2 - x1);
    ln(x1, y1, x2 - Math.cos(a) * head * 0.6, y2 - Math.sin(a) * head * 0.6, color, lw, dash);
    arrowHead(x2, y2, a, head, color);
  }
  function quadPath(p0, p1, p2, p, color, lw = 2.5, dash, head) {
    if (p <= 0) return;
    const N = 48;
    ctx.beginPath();
    for (let i = 0; i <= N; i++) {
      const q = quad(p0, p1, p2, (i / N) * p);
      if (i) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.lineCap = 'round';
    if (dash) ctx.setLineDash(dash);
    ctx.stroke();
    ctx.setLineDash([]);
    if (head) {
      const a = quad(p0, p1, p2, Math.max(0, p - 0.03)), b = quad(p0, p1, p2, p);
      arrowHead(b[0], b[1], Math.atan2(b[1] - a[1], b[0] - a[0]), head, color);
    }
  }
  function polyPath(pts, p, color, lw = 2.5, dash, head) {
    if (p <= 0 || pts.length < 2) return;
    const segs = [];
    let total = 0;
    for (let i = 1; i < pts.length; i++) {
      const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      segs.push(l);
      total += l;
    }
    let remain = total * clamp(p);
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    let last = pts[0], prev = pts[0];
    for (let i = 1; i < pts.length && remain > 0; i++) {
      const l = segs[i - 1], f = Math.min(1, remain / l);
      const x = lerp(pts[i - 1][0], pts[i][0], f), y = lerp(pts[i - 1][1], pts[i][1], f);
      ctx.lineTo(x, y);
      prev = pts[i - 1];
      last = [x, y];
      remain -= l;
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    if (dash) ctx.setLineDash(dash);
    ctx.stroke();
    ctx.setLineDash([]);
    if (head) arrowHead(last[0], last[1], Math.atan2(last[1] - prev[1], last[0] - prev[0]), head, color);
  }
  function cross(x, y, s, color, lw = 4) {
    ln(x - s, y - s, x + s, y + s, color, lw);
    ln(x - s, y + s, x + s, y - s, color, lw);
  }

  /* ---------------- figures ---------------- */
  function person(x, y, s = 1, o = {}) {
    const col = o.color || P.warm, fa = o.fillA != null ? o.fillA : 0.14, lw = 2.5 * (o.lw || 1);
    ctx.save();
    if (o.a != null) ctx.globalAlpha *= clamp(o.a);
    ctx.beginPath();
    ctx.moveTo(x - 34 * s, y + 50 * s);
    ctx.lineTo(x - 34 * s, y - 2 * s);
    ctx.quadraticCurveTo(x - 34 * s, y - 32 * s, x, y - 32 * s);
    ctx.quadraticCurveTo(x + 34 * s, y - 32 * s, x + 34 * s, y - 2 * s);
    ctx.lineTo(x + 34 * s, y + 50 * s);
    ctx.fillStyle = rgba(col, fa);
    ctx.fill();
    ctx.strokeStyle = col;
    ctx.lineWidth = lw;
    ctx.lineJoin = 'round';
    ctx.stroke();
    dot(x, y - 60 * s, 21 * s, rgba(col, fa), col, lw);
    if (o.label) txt(o.label, x, y + 50 * s + 36, { fam: 'mono', size: o.labelSize || 20, wt: 600, color: P.dim, align: 'center', track: 3 });
    ctx.restore();
  }
  const cellColor = (i) => (i < 3 ? P.gold : P.warm);
  function packetGeom(cx, cy, w) {
    const h = w * 0.44, x = cx - w / 2, y = cy - h / 2, hh = h * 0.32, pad = w * 0.045, gap = w * 0.016;
    const cw = (w - pad * 2 - gap * 7) / 8, ch = h - hh - pad * 1.25;
    return { x, y, w, h, hh, pad, gap, cw, ch };
  }
  function cellPos(cx, cy, w, i) {
    const g = packetGeom(cx, cy, w);
    return [g.x + g.pad + i * (g.cw + g.gap) + g.cw / 2, g.y + g.hh + g.pad * 0.55 + g.ch / 2];
  }
  function packet(cx, cy, w, o = {}) {
    if (w <= 0) return;
    const g = packetGeom(cx, cy, w);
    ctx.save();
    if (o.a != null) ctx.globalAlpha *= clamp(o.a);
    if (o.sy != null && o.sy !== 1) { ctx.translate(cx, cy); ctx.scale(o.sx || 1, o.sy); ctx.translate(-cx, -cy); }
    const stroke = o.stroke || P.warm;
    if (o.glow) {
      ctx.shadowColor = rgba(P.warm, 0.6 * clamp(o.glow));
      ctx.shadowBlur = 24 * clamp(o.glow, 0, 1.5) * Math.max(0.5, w / 200) * curScale;
    }
    rr(g.x, g.y, g.w, g.h, g.h * 0.16);
    ctx.fillStyle = o.fill || P.raise;
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.shadowColor = 'transparent';
    ctx.strokeStyle = stroke;
    ctx.lineWidth = Math.max(1.4, w / 105);
    ctx.stroke();
    ln(g.x + g.h * 0.12, g.y + g.hh, g.x + g.w - g.h * 0.12, g.y + g.hh, rgba(stroke, 0.55), Math.max(1, w / 220));
    if (w >= 150 && o.header !== false) {
      const fs = Math.min(22, w * 0.052);
      txt('DST ' + (o.dst || '?'), g.x + g.pad, g.y + g.hh * 0.68, { fam: 'mono', size: fs, wt: 600, color: P.dim, maxW: g.w - g.pad * 2 });
    } else if (o.header !== false) {
      for (let k = 0; k < 3; k++) dot(g.x + g.pad + k * w * 0.05 + w * 0.02, g.y + g.hh * 0.52, Math.max(1, w * 0.012), rgba(stroke, 0.6));
    }
    for (let i = 0; i < 8; i++) {
      const c = o.cells ? o.cells[i] : null;
      if (c && c.hide) continue;
      const x = g.x + g.pad + i * (g.cw + g.gap), y = g.y + g.hh + g.pad * 0.55;
      ctx.save();
      if (c && c.a != null) ctx.globalAlpha *= clamp(c.a);
      rr(x, y, g.cw, g.ch, g.cw * 0.2);
      ctx.fillStyle = (c && c.color) || o.cellColor || cellColor(i);
      ctx.fill();
      ctx.restore();
    }
    ctx.restore();
  }
  function cell(x, y, cw, ch, color, a = 1) {
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    rr(x - cw / 2, y - ch / 2, cw, ch, cw * 0.2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.restore();
  }
  function stamp(s, x, y, p, color, size = 40, rot = -0.06) {
    if (p <= 0) return;
    const k = E.out(clamp(p * 1.3)), sc = lerp(1.9, 1, k), a = clamp(p * 2.6);
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.scale(sc, sc);
    ctx.globalAlpha *= a;
    const tr = Math.round(size * 0.12);
    ctx.font = font('mono', size, 800);
    ctx.letterSpacing = tr + 'px';
    const w = ctx.measureText(s).width - tr, padX = size * 0.55, h = size * 1.55;
    rr(-w / 2 - padX, -h / 2, w + padX * 2, h, size * 0.2);
    ctx.fillStyle = rgba(color, 0.12);
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(3, size * 0.09);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(s, tr / 2, size * 0.05);
    ctx.restore();
  }

  /* ---------------- gates: OUT × INTACT × SIDEWAYS × UPWARD ---------------- */
  const GATES = ['OUT', 'INTACT', 'SIDEWAYS', 'UPWARD'];
  function gateTile(x, y, w, h, name, v, p, o) {
    const col = v ? P.yes : P.no, on = p > 0;
    box(x, y, w, h, { r: 10, stroke: on ? rgba(col, 0.35 + 0.55 * p) : P.rule, lw: 2, fill: on ? rgba(col, 0.1 * p) : null });
    txt(name, x + w / 2, y + (o.labelY || 28), { fam: 'sans', wt: 700, size: o.ls || 17, color: P.dim, align: 'center', track: 1.2, maxW: w - 12 });
    if (on) txt(String(v), x + w / 2, y + h - (o.digitPad || 18), { fam: 'mono', wt: 800, size: o.ds || 46, color: col, align: 'center', a: clamp(p * 2) });
    else txt('–', x + w / 2, y + h - (o.digitPad || 18) - 4, { fam: 'mono', size: (o.ds || 46) * 0.7, color: P.faint, align: 'center' });
  }
  function gatesRow(x, y, vals, p, o = {}) {
    const tw = o.tw || 108, th = o.th || 100, gx = o.gx || 26;
    let cx = x;
    for (let i = 0; i < 4; i++) {
      gateTile(cx, y, tw, th, GATES[i], vals[i], clamp((p - i * 0.17) / 0.17), o);
      cx += tw;
      if (i < 3) { txt('×', cx + gx / 2, y + th * 0.66, { fam: 'serif', size: 32, color: P.faint, align: 'center' }); cx += gx; }
    }
    const pp = clamp((p - 0.74) / 0.26), prod = vals.every(Boolean) ? 1 : 0, col = prod ? P.yes : P.no;
    txt('=', cx + 20, y + th * 0.66, { fam: 'serif', size: 34, color: P.dim, align: 'center' });
    const pw = o.pw || 60, px = cx + 40;
    box(px, y, pw, th, { r: 10, stroke: pp > 0 ? col : P.rule, lw: pp > 0 ? 3 : 2, fill: pp > 0 ? rgba(col, 0.16 * pp) : null });
    if (pp > 0) txt(String(prod), px + pw / 2, y + th - (o.digitPad || 18), { fam: 'mono', wt: 800, size: (o.ds || 46) * 1.06, color: col, align: 'center', a: clamp(pp * 2) });
    return px + pw;
  }
  function gatesGrid(x, y, vals, p, o = {}) {
    const tw = o.tw || 136, th = o.th || 66, g = o.g || 14;
    const oo = Object.assign({ ls: 19, ds: 32, labelY: 25, digitPad: 10 }, o);
    for (let i = 0; i < 4; i++) {
      const cx = x + (i % 2) * (tw + g), cy = y + Math.floor(i / 2) * (th + g);
      gateTile(cx, cy, tw, th, GATES[i], vals[i], clamp((p - i * 0.17) / 0.17), oo);
    }
    const pp = clamp((p - 0.74) / 0.26), prod = vals.every(Boolean) ? 1 : 0, col = prod ? P.yes : P.no;
    const by = y + 2 * (th + g), bw = tw * 2 + g, bh = o.bh || 48;
    box(x, by, bw, bh, { r: 10, stroke: pp > 0 ? col : P.rule, lw: pp > 0 ? 3 : 2, fill: pp > 0 ? rgba(col, 0.14 * pp) : null });
    txt('PRODUCT', x + 16, by + bh / 2 + 7, { fam: 'sans', size: 19, wt: 700, color: P.dim, track: 1.2 });
    if (pp > 0) txt('= ' + prod, x + bw - 16, by + bh / 2 + 12, { fam: 'mono', wt: 800, size: 32, color: col, align: 'right', a: clamp(pp * 2) });
    return by + bh;
  }

  /* ---------------- bin icons ---------------- */
  function binIcon(key, x, y, s, col) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.strokeStyle = col;
    ctx.fillStyle = col;
    ctx.lineWidth = 2.6;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    switch (key) {
      case 'inward': // electrical ground: the signal is shunted away
        ctx.moveTo(0, -15); ctx.lineTo(0, -1);
        ctx.moveTo(-14, -1); ctx.lineTo(14, -1);
        ctx.moveTo(-9, 6); ctx.lineTo(9, 6);
        ctx.moveTo(-4, 13); ctx.lineTo(4, 13);
        ctx.stroke();
        break;
      case 'sealed': // padlock
        rr(-12, -3, 24, 18, 4); ctx.stroke();
        ctx.beginPath(); ctx.arc(0, -3, 7.5, Math.PI, 0); ctx.stroke();
        dot(0, 6, 2.2, col);
        break;
      case 'sold': // coin
        ctx.arc(0, 0, 14, 0, Math.PI * 2); ctx.stroke();
        ctx.font = font('mono', 16, 800); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('$', 0, 1);
        break;
      case 'bent': // arrow that rises, then turns back down
        ctx.moveTo(-13, 13); ctx.lineTo(-13, -10); ctx.lineTo(8, -10); ctx.lineTo(8, 4); ctx.stroke();
        arrowHead(8, 13, Math.PI / 2, 9, col);
        break;
      case 'unsent': // circle with a slash
        ctx.arc(0, 0, 14, 0, Math.PI * 2);
        ctx.moveTo(-10, 10); ctx.lineTo(10, -10); ctx.stroke();
        break;
      case 'sideways': // three people linked
        ctx.moveTo(-14, 0); ctx.lineTo(14, 0); ctx.stroke();
        dot(-14, 0, 4.5, col); dot(0, 0, 4.5, col); dot(14, 0, 4.5, col);
        break;
      case 'delivered': // up into the bar
        ctx.moveTo(-14, -14); ctx.lineTo(14, -14);
        ctx.moveTo(0, 14); ctx.lineTo(0, -2); ctx.stroke();
        arrowHead(0, -7, -Math.PI / 2, 9, col);
        break;
      default:
        break;
    }
    ctx.restore();
  }

  /* ---------------- timeline + player ---------------- */
  let SCENES = [], TOTAL = 1, now = 0, playing = false, speed = 1, lastTs = 0, needDraw = true, ended = false;
  const capDur = (s) => (s ? clamp(0.9 + s.length / 19, 3.2, 11) : 2.5);

  function buildTimeline() {
    let T = 0;
    SCENES.forEach((sc, i) => {
      sc.i = i;
      const beats = (sc.beats || []).map((b) => (typeof b === 'string' ? { text: b } : Object.assign({}, b)));
      let bt = sc.lead != null ? sc.lead : 0.7;
      beats.forEach((b) => { b.start = bt; b.dur = b.dur || capDur(b.text); bt += b.dur; });
      sc.beats = beats;
      sc.B = beats.map((b) => b.start);
      sc.dur = Math.max(sc.minDur || 0, bt + (sc.tail != null ? sc.tail : 0.5));
      sc.start = T;
      T += sc.dur;
    });
    TOTAL = T;
  }
  function sceneAt(gt) {
    for (let i = SCENES.length - 1; i >= 0; i--) if (gt >= SCENES[i].start) return SCENES[i];
    return SCENES[0];
  }
  function activeBeat(sc, t) {
    const bs = sc.beats;
    for (let i = bs.length - 1; i >= 0; i--) {
      if (t >= bs[i].start) {
        const last = i === bs.length - 1;
        if (!last && t >= bs[i].start + bs[i].dur) return null;
        return { b: bs[i], end: last ? sc.dur : bs[i].start + bs[i].dur };
      }
    }
    return null;
  }

  function drawHeader(sc) {
    const h = L.header, land = ORIENT === 'land';
    if (sc.eyebrow) txt(sc.eyebrow, h.x, h.y + (land ? 44 : 50), { fam: 'mono', size: land ? 21 : 25, wt: 600, color: P.dim, track: 3 });
    if (sc.title) txt(sc.title, h.x, h.y + (land ? 122 : 128), { fam: 'serif', it: true, size: land ? 62 : 60, color: P.ink, maxW: h.w, min: 34 });
  }
  function drawCaption(sc, t) {
    const ab = activeBeat(sc, t);
    if (!ab || !ab.b.text) return;
    const a = Math.min(seg(t, ab.b.start, ab.b.start + 0.25, E.lin), 1 - seg(t, ab.end - 0.22, ab.end, E.lin));
    if (a <= 0) return;
    const c = L.cap, land = ORIENT === 'land';
    let size = land ? 40 : 44;
    const maxW = land ? 1640 : c.w, maxLines = land ? 3 : 4;
    let lines = wrap(ab.b.text, maxW, { fam: 'sans', size });
    while (lines.length > maxLines && size > 28) { size -= 2; lines = wrap(ab.b.text, maxW, { fam: 'sans', size }); }
    const lh = size * 1.3;
    ctx.save();
    ctx.globalAlpha = a;
    lines.forEach((l, i) => txt(l, c.x, c.y + size + 6 + i * lh, { fam: 'sans', size, color: P.ink }));
    ctx.restore();
  }
  function drawFrame(gt) {
    gt = clamp(gt, 0, Math.max(0, TOTAL - 1e-4));
    const sc = sceneAt(gt), t = gt - sc.start;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.drawImage(bgCv, 0, 0);
    ctx.setTransform(SC, 0, 0, SC, 0, 0);
    curScale = SC;
    const first = sc.i === 0, last = sc.i === SCENES.length - 1;
    const fin = first ? 1 : seg(t, 0, 0.45, E.lin), fout = last ? 1 : 1 - seg(t, sc.dur - 0.35, sc.dur, E.lin);
    ctx.save();
    ctx.globalAlpha = Math.min(fin, fout);
    if (sc.header !== false) drawHeader(sc);
    sc.draw(t, sc, gt);
    ctx.restore();
    drawCaption(sc, t);
  }

  /* ---------------- UI wiring ---------------- */
  const $ = (id) => document.getElementById(id);
  const ui = { pp: $('pp'), time: $('time'), scrub: $('scrub'), ticks: $('ticks'), chapters: $('chapters'), speed: $('speed'), big: $('bigplay'), bigLabel: $('bigplay-label'), bigTime: $('bigplay-time') };
  const SPEEDS = [1, 1.25, 1.5, 2, 0.75];
  let scrubbing = false, lastUi = 0;
  const fmt = (s) => { s = Math.max(0, Math.floor(s)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
  PL.fmt = fmt;

  function setPlaying(v) {
    if (v && now >= TOTAL - 0.05) now = 0;
    playing = v;
    ended = false;
    lastTs = performance.now();
    if (ui.pp) { ui.pp.setAttribute('aria-label', v ? 'Pause' : 'Play'); ui.pp.dataset.state = v ? 'playing' : 'paused'; }
    if (ui.big) ui.big.hidden = v;
    needDraw = true;
  }
  function seek(t) { now = clamp(t, 0, TOTAL - 0.001); needDraw = true; }
  function syncUI(force) {
    const ts = performance.now();
    if (!force && ts - lastUi < 90) return;
    lastUi = ts;
    if (ui.time) ui.time.textContent = fmt(now) + ' / ' + fmt(TOTAL);
    if (ui.scrub && !scrubbing) {
      ui.scrub.value = String(Math.round((now / TOTAL) * 1000));
      ui.scrub.style.setProperty('--p', ((now / TOTAL) * 100).toFixed(2) + '%');
    }
    if (ui.chapters) {
      const sc = sceneAt(now);
      const idx = String(sc.chapterIndex != null ? sc.chapterIndex : sc.i);
      if (ui.chapters.value !== idx) ui.chapters.value = idx;
    }
  }
  function tick(ts) {
    if (playing) {
      const dt = Math.min(0.1, Math.max(0, (ts - lastTs) / 1000));
      now += dt * speed;
      if (now >= TOTAL) {
        now = TOTAL - 0.001;
        setPlaying(false);
        ended = true;
        if (ui.bigLabel) ui.bigLabel.textContent = 'Play again';
      }
      needDraw = true;
    }
    lastTs = ts;
    if (needDraw) { drawFrame(now); needDraw = false; syncUI(); }
    requestAnimationFrame(tick);
  }
  function buildControls() {
    if (ui.chapters) {
      ui.chapters.innerHTML = '';
      SCENES.forEach((sc, i) => {
        if (sc.chapterOf != null) return;
        const op = document.createElement('option');
        op.value = String(i);
        op.textContent = fmt(sc.start) + '  ' + (sc.chapter || sc.eyebrow || 'Scene ' + (i + 1));
        ui.chapters.appendChild(op);
      });
      ui.chapters.addEventListener('change', () => { const sc = SCENES[+ui.chapters.value]; if (sc) seek(sc.start + 0.05); syncUI(true); });
    }
    if (ui.ticks) {
      ui.ticks.innerHTML = '';
      SCENES.forEach((sc) => {
        if (!sc.tick) return;
        const i = document.createElement('i');
        i.style.left = ((sc.start / TOTAL) * 100).toFixed(3) + '%';
        ui.ticks.appendChild(i);
      });
    }
    if (ui.bigTime) ui.bigTime.textContent = fmt(TOTAL);
    if (ui.pp) ui.pp.addEventListener('click', () => setPlaying(!playing));
    if (ui.big) ui.big.addEventListener('click', () => setPlaying(true));
    cv.addEventListener('click', () => setPlaying(!playing));
    if (ui.speed) ui.speed.addEventListener('click', () => {
      const i = (SPEEDS.indexOf(speed) + 1) % SPEEDS.length;
      speed = SPEEDS[i];
      ui.speed.textContent = speed + '×';
      ui.speed.setAttribute('aria-label', 'Playback speed ' + speed + ' times');
    });
    if (ui.scrub) {
      ui.scrub.addEventListener('input', () => { scrubbing = true; seek((+ui.scrub.value / 1000) * TOTAL); ui.scrub.style.setProperty('--p', +ui.scrub.value / 10 + '%'); if (ui.time) ui.time.textContent = fmt(now) + ' / ' + fmt(TOTAL); });
      ui.scrub.addEventListener('change', () => { scrubbing = false; syncUI(true); });
    }
    stageEl.addEventListener('keydown', (e) => {
      if (e.key === ' ' || e.key === 'k' || e.key === 'K') { e.preventDefault(); setPlaying(!playing); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); seek(now + 5); syncUI(true); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); seek(now - 5); syncUI(true); }
      else if (e.key === 'Home') { e.preventDefault(); seek(0); syncUI(true); }
    });
  }

  async function loadFonts() {
    if (!document.fonts || !document.fonts.load) return;
    const faces = [
      '400 30px "Atkinson Hyperlegible"', '700 30px "Atkinson Hyperlegible"',
      '400 30px "Martian Mono"', '500 30px "Martian Mono"', '600 30px "Martian Mono"', '700 30px "Martian Mono"', '800 30px "Martian Mono"',
      'italic 400 30px "Newsreader"', '400 30px "Newsreader"',
    ];
    const all = Promise.all(faces.map((f) => document.fonts.load(f).catch(() => null)));
    await Promise.race([all, new Promise((r) => setTimeout(r, forced ? 25000 : 3500))]);
    wrapCache.clear();
    needDraw = true;
  }

  function onTheme() {
    readPalette();
    rgbaCache.clear();
    buildBg();
    needDraw = true;
    if (forced) drawFrame(now);
  }

  PL.start = async function (scenes) {
    SCENES = scenes;
    buildTimeline();
    if (forced) {
      document.documentElement.classList.add('render');
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    readPalette();
    resize(true);
    if (PL.onBuilt) PL.onBuilt(SCENES, TOTAL);
    if (!forced) buildControls();
    drawFrame(0);
    syncUI(true);
    window.addEventListener('resize', () => resize(false));
    if (window.ResizeObserver && stageEl.parentElement) new ResizeObserver(() => resize(false)).observe(stageEl.parentElement);
    const mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
    if (mq && mq.addEventListener) mq.addEventListener('change', onTheme);
    new MutationObserver(onTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    await loadFonts();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { wrapCache.clear(); needDraw = true; });
    drawFrame(now);
    if (forced) {
      window.__PL.ready = true;
    } else {
      requestAnimationFrame((ts) => { lastTs = ts; tick(ts); });
    }
  };

  window.__PL = {
    ready: false,
    get total() { return TOTAL; },
    scenes() { return SCENES.map((s) => ({ id: s.id, start: s.start, dur: s.dur, B: s.B })); },
    seek(t) { now = t; drawFrame(t); return true; },
    frame(t, q) { now = t; drawFrame(t); return cv.toDataURL('image/jpeg', q || 0.94); },
  };

  Object.assign(PL, {
    clamp, lerp, E, seg, fadeIO, rng, quad, P, L, F, font, rgba, ctx,
    txt, measure, wrap, para, rich, rr, box, ln, dot, ring, arrowHead, arrow, quadPath, polyPath, cross,
    person, packet, packetGeom, cellPos, cell, cellColor, stamp, gatesRow, gatesGrid, binIcon, withLocal, GATES,
    orient: () => ORIENT, W: () => W, H: () => H, curScale: () => curScale,
    isRender: () => !!forced, seek, setPlaying,
  });
})();
