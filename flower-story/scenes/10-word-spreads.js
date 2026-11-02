/* ==========================================================================
   10 · Word Gets Around — Part Two opens on a little mountain town drawn as a
   dollhouse cross-section. Gossip about the flower (and the narrator's
   lunatic grin) hops room to room and phone to phone, inflating as it goes,
   until it reaches three of the hikers on a bench: "where do we get one?"
   The camera tilts up into a time-lapse sky ("A few days later…") and back
   down onto the shopfront of Embarrassment’s Flowers, pushing in toward the
   door (scene 11 opens inside).

   This file also defines window.TownKit — the shopfront, gossip icons, the
   town backdrop and small helpers — reused by scene 12 (The Parking Lot).
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;

  /* ======================================================================
     TownKit — shared town art for scenes 10 and 12. Pure functions of their
     arguments; offscreen caches hold only static art.
     ====================================================================== */
  const TK = {};
  TK.C = {
    stucco: '#efe3cf', stucco2: '#e3d2b7', trim: '#3b2a25', trim2: '#56403a',
    awnG: '#4f7a5a', awnC: '#f3e7d8', sign: '#f2a59e', door: '#3e6b4d', door2: '#4f7f5f',
    brass: '#cda24c', roof: '#5a4450', roof2: '#735a68', plinth: '#cbbfae',
  };
  /** the two flowers of Part Two */
  TK.TULIP = { kind: 'tulip', colors: { petal: '#ff8a3d', tip: '#ffd36b', inner: '#c2410c' } };
  TK.WILD = { kind: 'wild', droop: 0.5, dust: 1, colors: { petal: '#d8c25a', tip: '#efe2a0', inner: '#a08a2a' } };

  const poly = (g, p) => { g.beginPath(); g.moveTo(p[0], p[1]); for (let i = 2; i < p.length; i += 2) g.lineTo(p[i], p[i + 1]); g.closePath(); };
  const rect = (g, c, x, y, w, h) => { g.fillStyle = c; g.fillRect(x, y, w, h); };
  const circ = (g, c, x, y, r) => { g.fillStyle = c; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); };
  const ell = (g, c, x, y, rx, ry, rot = 0) => { g.fillStyle = c; g.beginPath(); g.ellipse(x, y, rx, ry, rot, 0, TAU); g.fill(); };
  const rrect = (g, c, x, y, w, h, r) => { g.fillStyle = c; Art.roundRect(g, x, y, w, h, r); g.fill(); };
  TK.poly = poly; TK.rect = rect; TK.circ = circ; TK.ell = ell; TK.rrect = rrect;

  /** smooth monotone path through keys [[t, v], ...] (eases in/out at the ends, never overshoots) */
  TK.path = (t, keys) => {
    const n = keys.length;
    if (t <= keys[0][0]) return keys[0][1];
    if (t >= keys[n - 1][0]) return keys[n - 1][1];
    let i = 0;
    while (i < n - 2 && t > keys[i + 1][0]) i++;
    const slope = (a, b) => (keys[b][1] - keys[a][1]) / (keys[b][0] - keys[a][0]);
    const tan = (j) => {
      if (j <= 0 || j >= n - 1) return 0;
      const d0 = slope(j - 1, j), d1 = slope(j, j + 1);
      return d0 * d1 <= 0 ? 0 : (2 * d0 * d1) / (d0 + d1);
    };
    const t0 = keys[i][0], h = keys[i + 1][0] - t0, u = (t - t0) / h;
    const v0 = keys[i][1], v1 = keys[i + 1][1], m0 = tan(i) * h, m1 = tan(i + 1) * h;
    const u2 = u * u, u3 = u2 * u;
    return (2 * u3 - 3 * u2 + 1) * v0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * v1 + (u3 - u2) * m1;
  };
  /** world → screen for a camera {x, y, z} (same mapping as Art.cam) */
  TK.toScreen = (c, x, y) => ({ x: (x - c.x) * c.z + W / 2, y: (y - c.y) * c.z + H / 2 });
  /** parallax camera for a layer at depth factor p (1 = main layer), aligned at the rest camera */
  TK.layer = (c, rest, p, ax, ay) => ({ x: ax + (c.x - rest.x) * p, y: ay + (c.y - rest.y) * p, zoom: 1 + (c.z - 1) * p });
  TK.toScreenL = (lc, x, y) => ({ x: (x - lc.x) * lc.zoom + W / 2, y: (y - lc.y) * lc.zoom + H / 2 });

  /** offscreen canvas drawn once (static art), sc = resolution multiplier */
  TK.cached = (key, w, h, sc, fn) => {
    const c = Art.canvas('tk:' + key + ':' + sc, w * sc, h * sc);
    const sig = key + '|' + c.width + 'x' + c.height;
    if (c._tkSig !== sig) {
      const x = c.getContext('2d');
      x.setTransform(1, 0, 0, 1, 0, 0);
      x.clearRect(0, 0, c.width, c.height);
      x.setTransform(sc, 0, 0, sc, 0, 0);
      fn(x);
      c._tkSig = sig;
    }
    return c;
  };
  /** current film-units → backing-pixels scale of a context (for picking cache resolution) */
  TK.pxScale = (ctx) => { const m = ctx.getTransform(); return Math.hypot(m.a, m.b); };
  /** quantised cache resolution for an effective on-screen scale (few levels → few canvases) */
  TK.res = (eff) => (eff > 1.3 ? 2 : eff > 0.9 ? 1.4 : eff > 0.55 ? 1 : 0.6);

  /* ---------------- gossip icons ---------------- */
  TK.flowerIcon = (g, x, y, r, rot = 0) => {
    g.save();
    g.translate(x, y);
    g.rotate(rot);
    for (let i = 0; i < 5; i++) {
      g.save();
      g.rotate((i / 5) * TAU);
      ell(g, '#cf1a5f', 0, -r * 0.5, r * 0.36, r * 0.52);
      ell(g, '#ff8db0', 0, -r * 0.72, r * 0.17, r * 0.22);
      g.restore();
    }
    circ(g, '#ffc23d', 0, 0, r * 0.31);
    circ(g, '#d68a1a', r * 0.06, r * 0.08, r * 0.13);
    g.restore();
  };
  /** the narrator's head with a giant lunatic grin */
  TK.grinIcon = (g, x, y, r, t = 0) => {
    Art.head(g, x, y + r * 0.2, r * 0.74, 'me', { smile: 1, open: 0.62, eyes: 'sparkle', blink: 0, browUp: 0.5 }, { turn: 1, t, seed: 5 });
  };
  /** a round chat bubble holding an icon ('flower' | 'grin') */
  TK.iconBubble = (g, x, y, r, icon, o = {}) => {
    const a = o.alpha === undefined ? 1 : o.alpha;
    const sc = o.sc === undefined ? 1 : o.sc;
    if (a <= 0.003 || sc <= 0.01) return;
    g.save();
    g.globalAlpha *= a;
    g.translate(x, y);
    g.scale(sc, sc);
    g.shadowColor = 'rgba(20,10,20,0.28)';
    g.shadowBlur = 12;
    g.shadowOffsetY = 4;
    g.fillStyle = '#fffaf1';
    const ta = o.tail === undefined ? 2.3 : o.tail;
    g.beginPath();
    g.arc(0, 0, r, 0, TAU);
    g.moveTo(Math.cos(ta - 0.45) * r * 0.85, Math.sin(ta - 0.45) * r * 0.85);
    g.lineTo(Math.cos(ta) * r * 1.42, Math.sin(ta) * r * 1.42);
    g.lineTo(Math.cos(ta + 0.45) * r * 0.85, Math.sin(ta + 0.45) * r * 0.85);
    g.fill();
    g.shadowColor = 'transparent';
    if (icon === 'flower') TK.flowerIcon(g, 0, 0, r * 0.64, o.rot || 0);
    else if (icon === 'grin') TK.grinIcon(g, 0, 0, r * 0.7, o.t || 0);
    g.restore();
  };
  /** an icon bubble hopping along an arc from a to b during [t0, t1], with a landing ping */
  TK.hop = (g, t, t0, t1, a, b, icon, o = {}) => {
    if (!a || !b || t < t0 || t > t1 + 0.5) return;
    const r = o.r || 24, arc = o.arc === undefined ? 150 : o.arc;
    const pos = (k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k) - Math.sin(k * Math.PI) * arc });
    if (t <= t1) {
      const k = U.ease(t, t0, t1, 'inOutSine');
      g.save();
      for (let i = 1; i <= 7; i++) {
        const kk = k - i * 0.04;
        if (kk <= 0.03) break;
        const p = pos(kk);
        g.globalAlpha = 0.65 * (1 - i / 8);
        circ(g, '#fffaf1', p.x, p.y, Math.max(1.2, 5.2 - i * 0.6));
      }
      g.restore();
      const p = pos(k), q = pos(Math.min(1, k + 0.02));
      const sc = k < 0.18 ? 0.4 + 0.6 * U.E.outBack(k / 0.18) : k > 0.86 ? lerp(1, 0.3, (k - 0.86) / 0.14) : 1;
      TK.iconBubble(g, p.x, p.y, r, icon, { sc, t, tail: Math.atan2(q.y - p.y, q.x - p.x) + Math.PI, rot: (k - 0.5) * 0.8 });
    }
    const lp = U.prog(t, t1 - 0.02, t1 + 0.45);
    if (lp > 0 && lp < 1) {
      g.save();
      g.globalAlpha = (1 - lp) * (o.pingAlpha === undefined ? 1 : o.pingAlpha);
      g.strokeStyle = o.ping || '#fff3c4';
      g.lineWidth = 3;
      g.beginPath(); g.arc(b.x, b.y, 8 + lp * 40, 0, TAU); g.stroke();
      g.lineWidth = 2.6;
      g.lineCap = 'round';
      for (let i = 0; i < 5; i++) {
        const an = -Math.PI / 2 + (i - 2) * 0.5, r0 = 18 + lp * 26, r1 = r0 + 11;
        g.beginPath(); g.moveTo(b.x + Math.cos(an) * r0, b.y + Math.sin(an) * r0); g.lineTo(b.x + Math.cos(an) * r1, b.y + Math.sin(an) * r1); g.stroke();
      }
      g.restore();
    }
  };
  /** a phone for Art.person holdF/holdB (hand-local units). glow 0..1 lights the screen */
  TK.phone = (glow = 0, o = {}) => (c) => {
    c.save();
    c.rotate(o.rot === undefined ? -0.3 : o.rot);
    rrect(c, '#1d2027', -7, -25, 15, 28, 3.5);
    c.fillStyle = U.mix('#34445f', '#e6f5ff', clamp(glow));
    Art.roundRect(c, -5.2, -23, 11.4, 22, 2.4);
    c.fill();
    if (glow > 0.02) Art.glow(c, 0.5, -12, 46, '#a9d8ff', glow * 0.5);
    c.restore();
  };

  /* ---------------- sky & far backdrop ---------------- */
  /** screen-space sky; hy = screen y of the bright horizon band (moves with tilts) */
  TK.sky = (g, P, hy) => {
    const top = hy - 840;
    if (top > 0) rect(g, P.sky[0], 0, 0, W, top + 1);
    const gr = g.createLinearGradient(0, top, 0, hy);
    gr.addColorStop(0, P.sky[0]);
    gr.addColorStop(0.55, P.sky[1]);
    gr.addColorStop(1, P.sky[2]);
    g.fillStyle = gr;
    const y0 = Math.max(0, top);
    if (hy > y0) g.fillRect(0, y0, W, hy - y0);
    if (hy < H) rect(g, P.sky[2], 0, hy, W, H - hy);
  };
  /** far mountains + THE summit, in layer coordinates designed for the rest frame */
  TK.backdrop = (g, P, o = {}) => {
    const t = o.t || 0, y = o.y === undefined ? 520 : o.y;
    const x0 = -500, x1 = W + 500;
    Art.ridge(g, { seed: 21, y: y - 30, amp: 200, color: U.mix(P.far, P.sky[1], 0.42), x0, x1, step: 12 });
    const tip = Art.summit(g, { x: o.sx === undefined ? 1360 : o.sx, y: y + 40, h: o.sh || 380, w: o.sw || 640, P, glow: o.glow === undefined ? 0.4 : o.glow, t });
    Art.fog(g, { y: y + 30, h: 170, color: P.fog, alpha: 0.5 });
    Art.ridge(g, { seed: 8, y: y + 80, amp: 110, color: U.mix(P.mid, P.far, 0.25), x0, x1, step: 12 });
    Art.fog(g, { y: y + 100, h: 120, color: P.fog, alpha: 0.32 });
    return tip;
  };

  /* ---------------- background town (rooftop view) ---------------- */
  /** a small house façade. (x, y) = bottom-left */
  TK.house = (g, h) => {
    const { x, y, w } = h, hh = h.h, rh = h.rh, ov = Math.max(5, w * 0.08);
    const c = h.c || { wall: h.wall, roof: h.roof, roofL: U.shade(h.roof, 0.18), brick: '#8d5847', frame: U.shade(h.wall, -0.42), glass: '#56677d', lit: '#f6d48e', door: U.shade(h.wall, -0.5), shade: 'rgba(40,25,30,0.11)' };
    if (h.chimney) rect(g, c.brick, x + w * 0.66, y - hh - rh * 0.82, w * 0.11, rh * 0.64);
    rect(g, c.wall, x, y - hh, w, hh);
    g.fillStyle = c.shade;
    g.fillRect(x, y - hh * 0.22, w, hh * 0.22);
    g.fillRect(x + w * 0.7, y - hh, w * 0.3, hh);
    g.fillStyle = c.roof;
    poly(g, [x - ov, y - hh + 3, x + w / 2, y - hh - rh, x + w + ov, y - hh + 3]);
    g.fill();
    g.fillStyle = c.roofL;
    poly(g, [x - ov, y - hh + 3, x + w / 2, y - hh - rh, x + w / 2 + 2, y - hh - rh + 6, x - ov + 6, y - hh + 3]);
    g.fill();
    for (const wn of h.wins) {
      rect(g, c.frame, wn.x - wn.w / 2 - 1.5, wn.y - wn.h / 2 - 1.5, wn.w + 3, wn.h + 3);
      rect(g, wn.lit ? c.lit : c.glass, wn.x - wn.w / 2, wn.y - wn.h / 2, wn.w, wn.h);
    }
    if (h.door) rect(g, c.door, x + w * 0.5 - 6, y - 22, 12, 22);
  };
  const stripData = {};
  /** generate (once) a deterministic hillside of houses; tiers back → front */
  TK.townStrip = (key, o) => {
    if (stripData[key]) return stripData[key];
    const r = U.rng(o.seed || 7);
    const walls = o.walls || ['#efe0c4', '#e9c9a0', '#cfdde2', '#d6e2c4', '#f0cfc0', '#e8dcc6', '#c8d2e6', '#f3e6b0'];
    const roofs = o.roofs || ['#8a4b40', '#6e4a52', '#5c5a68', '#9a5a3c', '#73504a', '#7d6050'];
    const tiers = [];
    for (const tier of o.tiers) {
      const houses = [], trees = [];
      let x = tier.x0 + r() * 30;
      while (x < tier.x1) {
        const w = lerp(tier.wMin, tier.wMax, r()), hh = lerp(tier.hMin, tier.hMax, r());
        const by = tier.y(x + w / 2);
        const hs = { x, y: by, w, h: hh, wall: walls[Math.floor(r() * walls.length)], roof: roofs[Math.floor(r() * roofs.length)], chimney: r() < 0.45, rh: Math.min(w * 0.46, 22 + r() * 24), door: r() < 0.5, wins: [] };
        const rows = Math.max(1, Math.floor(hh / 36)), cols = Math.max(1, Math.round(w / 34));
        const ww = Math.min(12, w / (cols * 2.4)), wh = ww * 1.3;
        for (let ri = 0; ri < rows; ri++) for (let ci = 0; ci < cols; ci++) {
          if (hs.door && ri === rows - 1 && ci === Math.floor(cols / 2) && rows > 1) continue;
          hs.wins.push({ x: x + (ci + 0.5) * w / cols, y: by - hh + 11 + wh / 2 + ri * 34, w: ww, h: wh, lit: r() < 0.06 });
        }
        houses.push(hs);
        const gap = lerp(tier.gapMin === undefined ? 8 : tier.gapMin, tier.gapMax === undefined ? 46 : tier.gapMax, r());
        if (gap > 26 && r() < 0.75) trees.push({ x: x + w + gap / 2, y: tier.y(x + w + gap / 2) + 2, h: lerp(40, 78, r()) * (tier.treeK || 1) });
        x += w + gap;
      }
      tiers.push({ houses, trees, tier });
    }
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity;
    for (const T of tiers) for (const hs of T.houses) { x0 = Math.min(x0, hs.x - 30); x1 = Math.max(x1, hs.x + hs.w + 30); y0 = Math.min(y0, hs.y - hs.h - hs.rh - 50); }
    const S = { tiers, x0, x1, y0, y1: o.bottom || 900, ground: o.ground || ['#7f9c78', '#6d8c68', '#5f7f5c'] };
    S.wins = [];
    for (const T of tiers) for (const hs of T.houses) for (const wn of hs.wins) S.wins.push(wn);
    stripData[key] = S;
    return S;
  };
  /** draw a strip as vectors (no offscreen canvas: big cached images force Chrome to flush the
      recording mid-frame). Atmospheric haze is baked into the colours, accumulating with
      distance: tier i is mixed toward hazeC by 1 − Π(1 − haze[j]) for j ≥ i.
      vx0/vx1 = visible x-range in strip coordinates (cull). */
  TK.drawStrip = (g, S, key, o = {}) => {
    const hz = o.haze || [0], hc = o.hazeC || '#e8f0e8';
    const sig = hz.join(',') + hc;
    if (S._sig !== sig) {
      // precompute hazed colours (pure function of the inputs)
      S.tiers.forEach((T, ti) => {
        let keep = 1;
        for (let j = ti; j < S.tiers.length; j++) keep *= 1 - (hz[Math.min(j, hz.length - 1)] || 0);
        const k = 1 - keep, mx = (c) => U.mix(c, hc, k);
        const col = S.ground[Math.min(ti, S.ground.length - 1)];
        T.c = { ground: mx(col), tree: mx(U.shade(col, -0.3)), treeL: mx(U.shade(col, -0.12)) };
        for (const hs of T.houses) hs.c = { wall: mx(hs.wall), roof: mx(hs.roof), roofL: mx(U.shade(hs.roof, 0.18)), brick: mx('#8d5847'), frame: mx(U.shade(hs.wall, -0.42)), glass: mx('#56677d'), lit: mx('#f6d48e'), door: mx(U.shade(hs.wall, -0.5)), shade: U.rgba('#28191e', 0.11 * (1 - k)) };
      });
      S._sig = sig;
    }
    const vx0 = o.vx0 === undefined ? -1e9 : o.vx0, vx1 = o.vx1 === undefined ? 1e9 : o.vx1;
    S.tiers.forEach((T) => {
      g.fillStyle = T.c.ground;
      g.beginPath();
      const a = Math.max(S.x0, Math.floor(vx0 / 24) * 24 - 24), b = Math.min(S.x1 + 24, vx1 + 48);
      g.moveTo(a, S.y1);
      for (let px = a; px <= b; px += 24) g.lineTo(px, T.tier.y(px) + 4);
      g.lineTo(b, S.y1);
      g.closePath();
      g.fill();
      for (const tr of T.trees) if (tr.x > vx0 - 60 && tr.x < vx1 + 60) Art.pine(g, tr.x, tr.y, tr.h, T.c.tree, { light: T.c.treeL });
      for (const hs of T.houses) if (hs.x + hs.w > vx0 - 40 && hs.x < vx1 + 40) TK.house(g, hs);
    });
  };

  /** a cast-iron street lamp. (x, y) = foot */
  TK.lamp = (g, x, y, s, o = {}) => {
    const c = o.color || '#2d3836';
    g.save();
    g.translate(x, y);
    g.scale(s, s);
    rrect(g, c, -10, -30, 20, 30, 4);
    rect(g, c, -4, -300, 8, 274);
    rect(g, U.shade(c, 0.15), -7, -150, 14, 8);
    rect(g, c, -16, -306, 32, 7);
    g.fillStyle = o.lit ? '#ffe7ad' : '#dfe8e6';
    poly(g, [-12, -306, 12, -306, 16, -350, -16, -350]);
    g.fill();
    g.fillStyle = c;
    poly(g, [-21, -348, 21, -348, 0, -370]);
    g.fill();
    circ(g, c, 0, -373, 4);
    g.restore();
    if (o.lit) Art.glow(g, x, y - 328 * s, 90 * s, '#ffd98a', 0.5 * o.lit);
  };

  /* ---------------- the flower shop ----------------
     local units: origin = bottom centre of the façade; at s = 1 the door is
     406 tall, so people drawn at the same scale fit through it. */
  TK.SHOP = { w: 600, peak: 1056 };
  function potShape(g, x, y, w, h, c) {
    g.fillStyle = c;
    poly(g, [x - w * 0.38, y, x + w * 0.38, y, x + w * 0.5, y - h * 0.82, x - w * 0.5, y - h * 0.82]);
    g.fill();
    rrect(g, U.shade(c, 0.12), x - w * 0.56, y - h, w * 1.12, h * 0.24, 3);
    g.fillStyle = 'rgba(0,0,0,0.18)';
    poly(g, [x - w * 0.38, y, x - w * 0.12, y, x - w * 0.2, y - h * 0.8, x - w * 0.5, y - h * 0.8]);
    g.fill();
  }
  TK.pot = potShape;
  const LEAF = ['#3f7a45', '#4f8f4c', '#5f9d55', '#2f6a3f', '#6aa35a', '#3a6f52', '#78ad62'];
  function foliage(g, x, y, kind, s, seed) {
    const col = (i) => LEAF[Math.floor(U.hash(i, seed) * LEAF.length)];
    if (kind === 'leafy' || kind === 'bloom') {
      for (let i = 0; i < 7; i++) {
        const a = -1.35 + (i / 6) * 2.7 + (U.hash(i, seed + 1) - 0.5) * 0.3;
        const L = (20 + U.hash(i, seed + 2) * 16) * s;
        g.save(); g.translate(x, y); g.rotate(a); ell(g, col(i), 0, -L * 0.55, L * 0.25, L * 0.55); g.restore();
      }
      if (kind === 'bloom') {
        const fc = ['#f48fb1', '#ffd36b', '#ffffff', '#ff8a5c', '#d98be6', '#ff6f7d'][Math.floor(U.hash(seed, 3) * 6)];
        for (let i = 0; i < 7; i++) circ(g, fc, x + (U.hash(i, seed + 5) - 0.5) * 30 * s, y - (16 + U.hash(i, seed + 6) * 18) * s, 3.8 * s);
      }
    } else if (kind === 'spike') {
      for (let i = 0; i < 5; i++) {
        const L = (42 + U.hash(i, seed) * 30) * s;
        g.save(); g.translate(x + (i - 2) * 3.5 * s, y); g.rotate((i - 2) * 0.17);
        g.fillStyle = i % 2 ? '#4e7f3e' : '#64965a';
        g.beginPath(); g.moveTo(-4.5 * s, 0); g.quadraticCurveTo(-5 * s, -L * 0.6, 0, -L); g.quadraticCurveTo(5 * s, -L * 0.6, 4.5 * s, 0); g.fill();
        g.restore();
      }
    } else if (kind === 'round') {
      for (let i = 0; i < 5; i++) circ(g, col(i), x + (U.hash(i, seed) - 0.5) * 22 * s, y - (8 + U.hash(i, seed + 1) * 14) * s, (9 + U.hash(i, seed + 2) * 6) * s);
    } else if (kind === 'trail') {
      for (let i = 0; i < 10; i++) {
        const side = i % 2 ? 1 : -1, k = Math.floor(i / 2);
        ell(g, col(i), x + side * (10 + k * 1.5) * s, y + (k * 11 - 6) * s, 5 * s, 7.5 * s, side * 0.4);
      }
      for (let i = 0; i < 4; i++) ell(g, col(i + 3), x + (i - 1.5) * 9 * s, y - 6 * s, 6 * s, 8 * s, (i - 1.5) * 0.4);
    } else if (kind === 'monstera') {
      for (let i = 0; i < 4; i++) {
        const a = -0.95 + i * 0.62, L = (38 + U.hash(i, seed) * 14) * s;
        g.save(); g.translate(x, y); g.rotate(a);
        g.strokeStyle = '#3d6b3a'; g.lineWidth = 2.5 * s;
        g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -L * 0.7); g.stroke();
        ell(g, i % 2 ? '#2f6d40' : '#3b7f4a', 0, -L, L * 0.42, L * 0.36);
        g.strokeStyle = '#3b2b23'; g.lineWidth = 2 * s;
        for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(sx * L * 0.1, -L); g.lineTo(sx * L * 0.42, -L * 1.05); g.stroke(); }
        g.restore();
      }
    } else if (kind === 'cactus') {
      rrect(g, '#5d8f55', x - 7 * s, y - 40 * s, 14 * s, 40 * s, 7 * s);
      rrect(g, '#5d8f55', x + 4 * s, y - 30 * s, 12 * s, 7 * s, 3 * s);
      rrect(g, '#5d8f55', x + 10 * s, y - 40 * s, 7 * s, 16 * s, 3.5 * s);
      circ(g, '#ff8fb0', x, y - 42 * s, 3.5 * s);
    }
  }
  TK.foliage = foliage;
  /** a potted plant: (x, y) = pot bottom centre */
  function potted(g, x, y, kind, s, seed, potC) {
    const pw = (24 + U.hash(seed, 9) * 14) * s, ph = (20 + U.hash(seed, 10) * 10) * s;
    foliage(g, x, y - ph * 0.9, kind, s, seed);
    potShape(g, x, y, pw, ph, potC || ['#c66a43', '#e6d8c2', '#9fb39a', '#c98a5a', '#7f9fbf', '#d9a07a'][Math.floor(U.hash(seed, 11) * 6)]);
  }
  TK.potted = potted;
  function shopWindowDisplay(g, x0, y0, x1, y1) {
    const w = x1 - x0, h = y1 - y0;
    g.save();
    g.beginPath(); g.rect(x0, y0, w, h); g.clip();
    const gr = g.createLinearGradient(0, y0, 0, y1);
    gr.addColorStop(0, '#6e5241'); gr.addColorStop(0.55, '#55402f'); gr.addColorStop(1, '#3a2b22');
    g.fillStyle = gr; g.fillRect(x0, y0, w, h);
    // the shop beyond: back shelves with plant silhouettes, warm light
    g.globalAlpha = 0.45;
    rect(g, '#2e221b', x0, y0 + 120, w, 6);
    for (let i = 0; i < 11; i++) potted(g, x0 + 14 + i * (w / 11), y0 + 120, ['round', 'leafy', 'spike'][i % 3], 0.55, 300 + i, '#8a5a40');
    g.globalAlpha = 1;
    Art.glow(g, x0 + w * 0.7, y0 + h * 0.35, 220, '#ffcf8a', 0.18);
    // hanging planters
    for (const [hx, hl, sd] of [[x0 + 64, 70, 41], [x0 + w - 70, 54, 42]]) {
      g.strokeStyle = '#d9c6a8'; g.lineWidth = 1.5;
      g.beginPath(); g.moveTo(hx - 10, y0); g.lineTo(hx, y0 + hl); g.lineTo(hx + 10, y0); g.stroke();
      foliage(g, hx, y0 + hl + 6, 'trail', 1.1, sd);
      potShape(g, hx, y0 + hl + 16, 30, 18, '#e9dcc6');
    }
    // shelves
    const sh1 = y0 + 138, sh2 = y0 + 226;
    rect(g, '#8a6248', x0, sh1, w, 7); rect(g, 'rgba(0,0,0,0.25)', x0, sh1 + 7, w, 5);
    rect(g, '#8a6248', x0, sh2, w, 7); rect(g, 'rgba(0,0,0,0.25)', x0, sh2 + 7, w, 5);
    const n1 = 7;
    for (let i = 0; i < n1; i++) potted(g, x0 + 22 + i * ((w - 40) / (n1 - 1)), sh1, ['bloom', 'leafy', 'cactus', 'round', 'bloom', 'spike', 'leafy'][i], 0.78, 60 + i);
    for (let i = 0; i < 6; i++) potted(g, x0 + 30 + i * ((w - 56) / 5), sh2, ['leafy', 'bloom', 'round', 'leafy', 'bloom', 'round'][i], 0.95, 80 + i);
    foliage(g, x0 + 40, sh1 + 10, 'trail', 0.9, 91);
    foliage(g, x0 + w - 50, sh2 + 10, 'trail', 0.9, 92);
    // floor level: the big ones
    potted(g, x0 + 46, y1, 'monstera', 1.35, 101, '#e6d8c2');
    potted(g, x0 + 128, y1, 'spike', 1.15, 102, '#c66a43');
    potted(g, x0 + 196, y1, 'bloom', 1.3, 103, '#7f9fbf');
    potted(g, x0 + 262, y1, 'leafy', 1.25, 104, '#c98a5a');
    g.restore();
    // glass: sheen + streaks
    g.save();
    g.beginPath(); g.rect(x0, y0, w, h); g.clip();
    const sh = g.createLinearGradient(x0, y0, x1, y1);
    sh.addColorStop(0, 'rgba(225,238,248,0.22)'); sh.addColorStop(0.5, 'rgba(225,238,248,0.04)'); sh.addColorStop(1, 'rgba(225,238,248,0.12)');
    g.fillStyle = sh; g.fillRect(x0, y0, w, h);
    g.fillStyle = 'rgba(255,255,255,0.11)'; poly(g, [x0 + 30, y1, x0 + 86, y1, x0 + 230, y0, x0 + 174, y0]); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.07)'; poly(g, [x0 + 112, y1, x0 + 132, y1, x0 + 276, y0, x0 + 256, y0]); g.fill();
    g.restore();
  }
  function upperWindow(g, cx, yTop, yBot) {
    const C = TK.C, w = 148, h = yBot - yTop;
    for (const sx of [-1, 1]) {
      const xs = sx < 0 ? cx - w / 2 - 44 : cx + w / 2 + 10;
      rect(g, '#4f7a5a', xs, yTop + 2, 34, h - 4);
      g.strokeStyle = U.shade('#4f7a5a', -0.28); g.lineWidth = 2;
      for (let yy = yTop + 14; yy < yBot - 8; yy += 11) { g.beginPath(); g.moveTo(xs + 5, yy); g.lineTo(xs + 29, yy + 3); g.stroke(); }
    }
    rect(g, C.trim, cx - w / 2 - 8, yTop - 8, w + 16, h + 16);
    const gg = g.createLinearGradient(0, yTop, 0, yBot);
    gg.addColorStop(0, '#c0d4df'); gg.addColorStop(1, '#6e8596');
    g.fillStyle = gg; g.fillRect(cx - w / 2, yTop, w, h);
    // curtains tied back
    g.fillStyle = '#fbf6ee';
    g.beginPath(); g.moveTo(cx - w / 2, yTop); g.lineTo(cx - w / 2 + 44, yTop); g.quadraticCurveTo(cx - w / 2 + 20, yTop + h * 0.45, cx - w / 2 + 14, yTop + h * 0.55); g.quadraticCurveTo(cx - w / 2 + 26, yTop + h * 0.8, cx - w / 2 + 30, yBot); g.lineTo(cx - w / 2, yBot); g.closePath(); g.fill();
    g.beginPath(); g.moveTo(cx + w / 2, yTop); g.lineTo(cx + w / 2 - 44, yTop); g.quadraticCurveTo(cx + w / 2 - 20, yTop + h * 0.45, cx + w / 2 - 14, yTop + h * 0.55); g.quadraticCurveTo(cx + w / 2 - 26, yTop + h * 0.8, cx + w / 2 - 30, yBot); g.lineTo(cx + w / 2, yBot); g.closePath(); g.fill();
    rect(g, '#f2a59e', cx - w / 2 + 8, yTop + h * 0.53, 12, 5); rect(g, '#f2a59e', cx + w / 2 - 20, yTop + h * 0.53, 12, 5);
    rect(g, C.trim, cx - 3, yTop, 6, h); rect(g, C.trim, cx - w / 2, yTop + h * 0.42, w, 6);
    g.fillStyle = 'rgba(255,255,255,0.14)'; poly(g, [cx - w / 2 + 50, yBot, cx - w / 2 + 72, yBot, cx + 10, yTop, cx - 12, yTop]); g.fill();
    // sill + flower box with geraniums
    rect(g, '#e9dcc8', cx - w / 2 - 14, yBot + 8, w + 28, 8);
    rrect(g, '#6a4a3a', cx - w / 2 - 6, yBot + 16, w + 12, 26, 3);
    for (let i = 0; i < 10; i++) ell(g, LEAF[i % LEAF.length], cx - w / 2 + 2 + i * (w / 9), yBot + 14 - U.hash(i, 77) * 6, 11, 8, U.hash(i, 78) - 0.5);
    for (let i = 0; i < 7; i++) {
      const fx = cx - w / 2 + 10 + i * (w / 6.3), fy = yBot + 2 - U.hash(i, 79) * 10;
      for (let j = 0; j < 5; j++) circ(g, i % 3 === 1 ? '#f48fb1' : '#e5484d', fx + Math.cos(j * 1.3) * 5, fy + Math.sin(j * 1.3) * 4, 3.6);
    }
  }
  function shopStatic(g) {
    const C = TK.C;
    // gable wall + walls
    g.fillStyle = C.stucco;
    poly(g, [-300, -876, 0, -1022, 300, -876]); g.fill();
    const wg = g.createLinearGradient(0, -1022, 0, 0);
    wg.addColorStop(0, '#f6eddd'); wg.addColorStop(0.6, C.stucco); wg.addColorStop(1, '#e5d5bc');
    g.fillStyle = wg; g.fillRect(-300, -880, 600, 880);
    for (let i = 0; i < 30; i++) ell(g, U.rgba('#cdb898', 0.1 + U.hash(i, 53) * 0.08), -285 + U.hash(i, 51) * 570, -860 + U.hash(i, 52) * 840, 10 + U.hash(i, 54) * 28, 5 + U.hash(i, 55) * 12);
    for (let i = 0; i < 8; i++) {
      const yy = -582 - i * 36, ww = i % 2 ? 20 : 32;
      rect(g, '#e4d4bb', -300, yy - 33, ww, 32); rect(g, '#e4d4bb', 300 - ww, yy - 33, ww, 32);
    }
    // roof band along the gable
    const L = [-338, -862], A = [0, -1028], R = [338, -862], th = 34;
    g.fillStyle = C.roof;
    poly(g, [L[0], L[1], A[0], A[1], R[0], R[1], R[0], R[1] - th, A[0], A[1] - th - 6, L[0], L[1] - th]); g.fill();
    g.strokeStyle = U.shade(C.roof, -0.3); g.lineWidth = 2.5;
    for (const f of [0.36, 0.68]) { g.beginPath(); g.moveTo(L[0], L[1] - th * f); g.lineTo(A[0], A[1] - (th + 6) * f); g.lineTo(R[0], R[1] - th * f); g.stroke(); }
    g.strokeStyle = C.roof2; g.lineWidth = 3;
    g.beginPath(); g.moveTo(L[0], L[1] - th); g.lineTo(A[0], A[1] - th - 6); g.lineTo(R[0], R[1] - th); g.stroke();
    g.strokeStyle = '#f3e7d8'; g.lineWidth = 7;
    g.beginPath(); g.moveTo(L[0] + 8, L[1] - 2); g.lineTo(A[0], A[1] + 2); g.lineTo(R[0] - 8, R[1] - 2); g.stroke();
    // scalloped bargeboard trim
    for (const side of [-1, 1]) for (let i = 1; i < 11; i++) {
      const k = i / 11, px = lerp(A[0], side < 0 ? L[0] : R[0], k), py = lerp(A[1], L[1], k) + 7;
      circ(g, '#f3e7d8', px, py, 5);
    }
    circ(g, C.trim, 0, -1068, 6);
    // attic round window
    circ(g, C.trim, 0, -946, 30); circ(g, '#8fa8bb', 0, -946, 22);
    rect(g, C.trim, -2.5, -968, 5, 44); rect(g, C.trim, -22, -948.5, 44, 5);
    g.fillStyle = 'rgba(255,255,255,0.25)'; g.beginPath(); g.arc(0, -946, 17, -2.6, -1.5); g.lineTo(0, -946); g.fill();
    // cornice under the gable
    rect(g, C.trim2, -312, -884, 624, 14);
    // upper floor
    for (const wx of [-150, 150]) upperWindow(g, wx, -806, -626);
    // sign
    rect(g, C.trim2, -310, -584, 620, 14);
    rrect(g, C.trim, -290, -572, 580, 98, 7);
    g.strokeStyle = U.rgba('#f2a59e', 0.5); g.lineWidth = 2.5; Art.roundRect(g, -279, -561, 558, 76, 5); g.stroke();
    g.save();
    g.font = Art.font(64, 'hand', 700);
    g.textAlign = 'center'; g.textBaseline = 'middle';
    const text = 'Embarrassment’s Flowers';
    const k = Math.min(1, 452 / g.measureText(text).width);
    g.translate(4, -521); g.scale(k, k);
    g.fillStyle = '#170f0d'; g.fillText(text, 2.5, 3.5);
    g.fillStyle = C.sign; g.fillText(text, 0, 0);
    g.restore();
    for (const sx of [-1, 1]) {
      ell(g, '#5f9d55', sx * 252 - sx * 8, -508, 9, 4, sx * 0.6);
      ell(g, '#5f9d55', sx * 252 + sx * 6, -506, 8, 4, -sx * 0.6);
      TK.flowerIcon(g, sx * 252, -526, 15, sx * 0.25);
    }
    // shopfront woodwork
    rect(g, C.trim2, -308, -476, 616, 12);
    rect(g, C.trim, -300, -464, 28, 464);
    rect(g, C.trim, 44, -464, 28, 464);
    rect(g, C.trim, 256, -464, 44, 464);
    rect(g, C.plinth, -300, -30, 600, 30);
    g.strokeStyle = 'rgba(80,60,50,0.25)'; g.lineWidth = 1.5;
    for (let x = -300; x < 300; x += 50) { g.beginPath(); g.moveTo(x, -30); g.lineTo(x, 0); g.stroke(); }
    rect(g, 'rgba(255,255,255,0.25)', -300, -30, 600, 3);
    // the window
    rect(g, C.trim, -272, -446, 316, 364);
    shopWindowDisplay(g, -260, -434, 32, -100);
    rect(g, C.trim, -118, -434, 8, 334);
    rect(g, C.trim, -260, -374, 292, 7);
    rect(g, '#6d5043', -278, -100, 328, 14);
    rect(g, 'rgba(255,255,255,0.18)', -278, -100, 328, 3);
    rect(g, C.trim, -272, -86, 316, 56);
    rrect(g, C.trim2, -258, -78, 136, 40, 3); rrect(g, C.trim2, -106, -78, 136, 40, 3);
    // door frame + transom
    rect(g, C.trim, 72, -454, 184, 454);
    rect(g, '#5d4a3d', 84, -444, 160, 28);
    rect(g, 'rgba(255,255,255,0.12)', 84, -444, 160, 9);
    // brass number plaque
    ell(g, C.brass, 278, -246, 13, 16);
    g.save(); g.font = Art.font(20, 'serif', 700); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = C.trim; g.fillText('7', 278, -245); g.restore();
    // doormat
    rrect(g, '#8a6a4a', 92, -6, 144, 8, 3);
  }
  function shopDoorway(g, t) {
    g.save();
    g.beginPath(); g.rect(84, -406, 160, 406); g.clip();
    const gr = g.createLinearGradient(0, -406, 0, 0);
    gr.addColorStop(0, '#6b4c3a'); gr.addColorStop(1, '#3a2a22');
    g.fillStyle = gr; g.fillRect(84, -406, 160, 406);
    rect(g, '#2e221c', 84, -260, 160, 6);
    for (let i = 0; i < 4; i++) potted(g, 104 + i * 40, -260, ['leafy', 'bloom', 'round', 'spike'][i], 0.75, 400 + i);
    Art.glow(g, 180, -230, 200, '#ffd08a', 0.2);
    g.fillStyle = '#b98c60';
    poly(g, [84, 0, 244, 0, 244, -58, 84, -58]); g.fill();
    g.strokeStyle = 'rgba(80,50,30,0.35)'; g.lineWidth = 1.5;
    for (let i = 1; i < 5; i++) { g.beginPath(); g.moveTo(84, -i * 12); g.lineTo(244, -i * 12); g.stroke(); }
    rect(g, 'rgba(30,20,15,0.35)', 84, -60, 160, 6);
    g.restore();
  }
  function shopDoor(g, open, t) {
    const C = TK.C, x0 = 84, w = 160, y0 = -406, y1 = 0;
    const a = clamp(open) * 1.3, ca = Math.cos(a), sa = Math.sin(a);
    const eye = -290, f = 1 / (1 + sa * 0.32), fx = x0 + w * ca;
    const P = (u, v) => {
      const yt = lerp(y0, eye + (y0 - eye) * f, u), yb = lerp(y1, eye + (y1 - eye) * f, u);
      return [lerp(x0, fx, u), lerp(yt, yb, v)];
    };
    const quad = (u0, v0, u1, v1) => {
      const p = [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)];
      g.beginPath(); g.moveTo(p[0][0], p[0][1]); for (let i = 1; i < 4; i++) g.lineTo(p[i][0], p[i][1]); g.closePath();
    };
    const dk = -0.3 * clamp(open * 2.5);
    g.fillStyle = U.shade(C.door, dk); quad(0, 0, 1, 1); g.fill();
    g.fillStyle = U.shade(C.door2, dk); quad(0.06, 0.03, 0.94, 0.6); g.fill();
    // glass panes 2 × 3
    for (let i = 0; i < 2; i++) for (let j = 0; j < 3; j++) {
      const u0 = 0.12 + i * 0.39, v0 = 0.06 + j * 0.172;
      g.fillStyle = open > 0.05 ? '#3b3530' : '#4c3d33'; quad(u0, v0, u0 + 0.35, v0 + 0.152); g.fill();
      g.fillStyle = 'rgba(255,255,255,0.12)'; quad(u0, v0, u0 + 0.12, v0 + 0.152); g.fill();
    }
    // the hanging OPEN card behind the glass
    if (open < 0.05) {
      g.strokeStyle = '#d9c6a8'; g.lineWidth = 1.2;
      const a1 = P(0.38, 0.08), a2 = P(0.62, 0.08), c1 = P(0.32, 0.15), c2 = P(0.68, 0.15);
      g.beginPath(); g.moveTo(a1[0], a1[1]); g.lineTo(c1[0], c1[1]); g.moveTo(a2[0], a2[1]); g.lineTo(c2[0], c2[1]); g.stroke();
      g.fillStyle = '#f3e7d8'; quad(0.28, 0.15, 0.72, 0.22); g.fill();
      const m = P(0.5, 0.185);
      g.save(); g.font = Art.font(19, 'sans', 900); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = C.door; g.fillText('OPEN', m[0], m[1] + 1); g.restore();
    }
    // lower panel + kick plate
    g.fillStyle = U.shade(C.door, dk - 0.12); quad(0.14, 0.66, 0.86, 0.9); g.fill();
    g.fillStyle = U.shade(C.door2, dk); quad(0.18, 0.68, 0.82, 0.88); g.fill();
    g.fillStyle = U.shade(C.brass, dk); quad(0.04, 0.94, 0.96, 0.99); g.fill();
    // handle
    const hp = P(0.88, 0.5);
    g.fillStyle = U.shade(C.brass, dk);
    g.beginPath(); g.ellipse(hp[0], hp[1], 5 * Math.max(0.35, ca), 22, 0, 0, TAU); g.fill();
    circ(g, U.shade(C.brass, 0.35 + dk), hp[0] - 1, hp[1] - 8, 2.2);
  }
  function shopAwning(g, t, wind) {
    const C = TK.C, xl = -292, xr = 262, yt = -462, yb = -398, n = 13, flare = 18, val = 32;
    g.fillStyle = 'rgba(40,25,20,0.20)';
    g.fillRect(xl, yb + val - 4, xr - xl, 40);
    for (let i = 0; i < n; i++) {
      const u0 = i / n, u1 = (i + 1) / n;
      g.fillStyle = i % 2 ? C.awnC : C.awnG;
      poly(g, [lerp(xl, xr, u0), yt, lerp(xl, xr, u1), yt, lerp(xl - flare, xr + flare, u1), yb, lerp(xl - flare, xr + flare, u0), yb]);
      g.fill();
    }
    const sg = g.createLinearGradient(0, yt, 0, yb);
    sg.addColorStop(0, 'rgba(30,20,20,0.28)'); sg.addColorStop(0.5, 'rgba(30,20,20,0.05)'); sg.addColorStop(1, 'rgba(255,250,235,0.10)');
    g.fillStyle = sg;
    poly(g, [xl, yt, xr, yt, xr + flare, yb, xl - flare, yb]); g.fill();
    for (let i = 0; i < n; i++) {
      const bx0 = lerp(xl - flare, xr + flare, i / n), bx1 = lerp(xl - flare, xr + flare, (i + 1) / n);
      const wob = Math.sin(t * 1.9 + i * 0.8) * 1.4 * wind;
      g.fillStyle = i % 2 ? U.shade(C.awnC, -0.05) : U.shade(C.awnG, -0.1);
      g.beginPath();
      g.moveTo(bx0, yb); g.lineTo(bx1, yb);
      g.lineTo(bx1 + wob, yb + val - 9);
      g.arc((bx0 + bx1) / 2 + wob, yb + val - 9, (bx1 - bx0) / 2, 0, Math.PI);
      g.closePath();
      g.fill();
    }
    rect(g, U.rgba(C.trim, 0.55), xl - flare, yb - 2, xr - xl + flare * 2, 4);
    rect(g, '#2a2421', xl - 6, yt - 4, xr - xl + 12, 7);
  }
  function shopBell(g, t, swing) {
    const C = TK.C;
    g.strokeStyle = '#2a2421'; g.lineWidth = 3; g.lineCap = 'round';
    g.beginPath(); g.moveTo(266, -360); g.quadraticCurveTo(250, -366, 246, -354); g.stroke();
    g.beginPath(); g.arc(262, -366, 6, 0.5, 4.2); g.stroke();
    g.save();
    g.translate(246, -352);
    g.rotate(swing);
    g.strokeStyle = '#6b5a3a'; g.lineWidth = 2;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 6); g.stroke();
    g.fillStyle = C.brass;
    g.beginPath(); g.moveTo(-4, 6); g.quadraticCurveTo(-5, 18, -12, 27); g.lineTo(12, 27); g.quadraticCurveTo(5, 18, 4, 6); g.closePath(); g.fill();
    rrect(g, U.shade(C.brass, -0.2), -13, 25, 26, 4, 2);
    g.fillStyle = 'rgba(255,255,255,0.45)'; g.fillRect(-4, 10, 2.5, 13);
    circ(g, '#7a5a2a', Math.sin(swing * 3) * 3, 30, 3);
    g.restore();
  }
  function shopLantern(g, lit) {
    g.strokeStyle = '#2a2421'; g.lineWidth = 3;
    g.beginPath(); g.moveTo(58, -350); g.lineTo(58, -366); g.stroke();
    rect(g, '#2a2421', 46, -350, 24, 4);
    g.fillStyle = lit > 0.05 ? U.mix('#f1e7cf', '#ffe2a2', lit) : '#efe7d6';
    poly(g, [48, -346, 68, -346, 70, -312, 46, -312]); g.fill();
    rect(g, '#2a2421', 57, -346, 2, 34);
    poly(g, [42, -312, 74, -312, 66, -304, 50, -304]); g.fillStyle = '#2a2421'; g.fill();
    poly(g, [44, -346, 72, -346, 58, -362]); g.fill();
  }
  /**
   * The shopfront of Embarrassment’s Flowers. (x, y) = bottom centre of the
   * façade on the pavement, s = scale (people at the same s fit the door).
   * o = { doorOpen 0..1, bell (swing amplitude, decays), bellT (time of the
   *       last ring), wind, lit (lantern), between(ctx) — drawn after the
   *       door and before the awning (people in the doorway) }
   * returns anchors in the caller's coordinates.
   */
  TK.shopfront = (ctx, x, y, s, t, o = {}) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    shopStatic(ctx);
    const open = clamp(o.doorOpen || 0);
    if (open > 0.002) shopDoorway(ctx, t);
    shopDoor(ctx, open, t);
    ctx.restore();
    if (o.between) o.between(ctx);
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    shopAwning(ctx, t, o.wind === undefined ? 1 : o.wind);
    const bt = t - (o.bellT === undefined ? -99 : o.bellT);
    const swing = (o.bell || 0) * (bt >= 0 ? Math.sin(bt * 16) * Math.exp(-bt * 2.2) : 0) + Math.sin(t * 1.3) * 0.03;
    shopBell(ctx, t, swing);
    shopLantern(ctx, o.lit || 0);
    ctx.restore();
    if (o.lit) Art.glow(ctx, x + 58 * s, y - 328 * s, 70 * s, '#ffd98a', 0.45 * o.lit);
    const P = (lx, ly) => ({ x: x + lx * s, y: y + ly * s });
    return { door: Object.assign(P(164, 0), { w: 160 * s, h: 406 * s, x0: x + 84 * s, x1: x + 244 * s, top: y - 406 * s }), window: P(-114, -270), sign: P(0, -521), bell: P(246, -330), peak: P(0, -1072) };
  };

  /* ---------------- townsfolk ---------------- */
  TK.LOOK = {
    barista: { name: 'barista', skin: '#e2a985', hair: '#5a2e22', hairStyle: 'bun', shirt: '#f2e6d2', shirt2: '#cbb99e', pants: '#3d3a46', shoes: '#2c2626', apron: '#7a4a32', height: 0.95 },
    granny: { name: 'granny', skin: '#f0cdb4', hair: '#dedad3', hairStyle: 'bun', shirt: '#9a7fb8', shirt2: '#e6dcf2', pants: '#5b5368', shoes: '#4a3a3a', glasses: true, height: 0.88 },
    teen: { name: 'teen', skin: '#c48a64', hair: '#2b1c17', hairStyle: 'long', shirt: '#f0a93c', shirt2: '#ffe2a8', pants: '#3b4a6b', shoes: '#e8e8e8', hood: true, height: 0.9 },
    dad: { name: 'dad', skin: '#f0c39e', hair: '#7a5a3a', hairStyle: 'short', shirt: '#c0504d', shirt2: '#f0c4c0', pants: '#3a3f4a', shoes: '#2a2a2a', beard: '#7a5a3a', height: 1.02 },
  };

  window.TownKit = TK;

  /* ======================================================================
     Scene 10 — the town
     ====================================================================== */
  const D = 18.8;
  const GY = 880;                       // street level in town-world units
  const REST = { x: 1000, y: 520, z: 1 };
  const P0 = U.mixDeep(Art.TOD.morning, Art.TOD.golden, 0.16);

  // beats (local seconds)
  const T = {
    tell: [1.3, 2.5], b1: [2.4, 4.6], hopA: [4.3, 4.9], b2: [5.15, 7.4], hopB: [7.2, 7.8],
    b3: [8.0, 10.2], fan: [9.75, 10.65], hopC: [10.25, 10.85], b4: [11.05, 13.2],
    tiltUp: [12.95, 14.3], lapse: [14.1, 15.8], tiltDown: [15.55, 16.95], push: [16.3, 18.8],
  };
  const SWITCH = 14.95;                  // town → shop street (only sky is in frame then)
  const TILT = 1340;

  const NARR = [
    [1.5, 4.3, 'Word gets around about the flower'],
    [4.7, 9.8, 'and how I smiled like a lunatic when I talked about it.'],
    [14.2, 17.6, 'A few days later…'],
  ];

  // town camera: x, zoom, and the screen y of the street line
  const CX = [[0, 1090], [1.0, 1030], [2.3, 410], [4.4, 460], [5.8, 800], [7.2, 850], [8.5, 1235], [9.8, 1280], [10.5, 1420], [11.8, 1800], [13.1, 1830]];
  const CZ = [[0, 0.74], [1.0, 0.77], [2.3, 1.2], [4.4, 1.2], [5.8, 1.22], [7.2, 1.2], [8.5, 1.2], [9.8, 1.12], [10.5, 0.94], [11.8, 1.2], [13.1, 1.21]];
  const CG = [[0, 905], [7.2, 905], [8.5, 972], [9.8, 958], [10.5, 905], [13.1, 905]];
  const townCam = (t) => {
    const z = TK.path(t, CZ), x = TK.path(t, CX), gy = TK.path(t, CG);
    return { x, y: GY - (gy - 540) / z, z };
  };
  const tiltAt = (t) => (t < SWITCH ? U.ease(t, T.tiltUp[0], T.tiltUp[1], 'inOutCubic') : 1 - U.ease(t, T.tiltDown[0], T.tiltDown[1], 'inOutCubic')) * TILT;

  // time-lapse palette: morning → golden → dusk → night → dawn → morning
  const LAPSE = [[0, P0], [0.2, Art.TOD.golden], [0.34, Art.TOD.dusk], [0.5, Art.TOD.night], [0.66, Art.TOD.dawn], [0.84, P0], [1, P0]];
  function paletteAt(t) {
    const k = U.prog(t, T.lapse[0], T.lapse[1]);
    if (k <= 0 || k >= 1) return P0;
    for (let i = 1; i < LAPSE.length; i++) if (k <= LAPSE[i][0]) return U.mixDeep(LAPSE[i - 1][1], LAPSE[i][1], U.smooth((k - LAPSE[i - 1][0]) / (LAPSE[i][0] - LAPSE[i - 1][0])));
    return P0;
  }

  /* ---------------- hillside town behind the main street ---------------- */
  const HILL = TK.townStrip('town10', {
    seed: 1010, bottom: 980, ground: ['#a3b49a', '#93a88b', '#84a07d'],
    tiers: [
      { x0: -700, x1: 2700, y: (x) => 610 - 18 * Math.sin(x * 0.0021 + 1.2) - x * 0.03, wMin: 34, wMax: 58, hMin: 26, hMax: 44, gapMin: 18, gapMax: 90, treeK: 0.6 },
      { x0: -700, x1: 2700, y: (x) => 668 - 16 * Math.sin(x * 0.0027 + 0.3) - x * 0.025, wMin: 44, wMax: 76, hMin: 34, hMax: 60, gapMin: 16, gapMax: 80, treeK: 0.8 },
      { x0: -700, x1: 2700, y: (x) => 730 - 14 * Math.sin(x * 0.003 + 2.1) - x * 0.02, wMin: 56, wMax: 96, hMin: 44, hMax: 80, gapMin: 14, gapMax: 70, treeK: 1 },
    ],
  });
  const HILL_HAZE = { haze: [0.5, 0.32, 0.18], hazeC: P0.fog };
  // five hillside windows that receive the fan-out: picked by where they land on screen at the
  // fan-out moment (between the square's tree and the town hall, above the planters)
  const FAN = (() => {
    const hl = TK.layer(townCam(T.fan[0] + 0.3), REST, 0.42, 960, 540);
    const cand = [];
    for (const wn of HILL.wins) {
      const p = TK.toScreenL(hl, wn.x, wn.y);
      if (p.x > 1320 && p.x < 1680 && p.y > 470 && p.y < 700) cand.push({ wn, x: p.x });
    }
    cand.sort((a, b) => a.x - b.x);
    const out = [];
    for (let i = 0; i < 5 && cand.length; i++) out.push(cand[Math.min(cand.length - 1, Math.round(i * (cand.length - 1) / 4))].wn);
    return out.filter((w, i) => out.indexOf(w) === i);
  })();
  const fanOn = (t, i) => U.prog(t, T.fan[0] + i * 0.12 + 0.42, T.fan[0] + i * 0.12 + 0.6);

  /* ---------------- dollhouse cross-section helpers ---------------- */
  const SLAB = '#4b372e';
  function patternTile(kind) {
    const c = Art.canvas('tk:pat:' + kind, 28, 28);
    if (c._tkPat) return c;
    const g = c.getContext('2d');
    g.clearRect(0, 0, 28, 28);
    if (kind === 'rose') {
      for (const [x, y] of [[7, 7], [21, 21]]) { for (let i = 0; i < 4; i++) circ(g, '#e8a3a8', x + Math.cos(i * 1.57) * 2.2, y + Math.sin(i * 1.57) * 2.2, 2); circ(g, '#c96a75', x, y, 1.4); ell(g, '#9fbf8f', x + 4, y + 3, 2.2, 1.1, 0.6); }
    } else if (kind === 'stripe') {
      rect(g, 'rgba(255,255,255,0.22)', 0, 0, 9, 28); rect(g, 'rgba(120,90,160,0.10)', 14, 0, 3, 28);
    } else if (kind === 'tile') {
      g.strokeStyle = 'rgba(70,110,150,0.35)'; g.lineWidth = 1;
      g.strokeRect(0.5, 0.5, 13, 13); g.strokeRect(14.5, 14.5, 13, 13); g.strokeRect(14.5, 0.5, 13, 13); g.strokeRect(0.5, 14.5, 13, 13);
      circ(g, 'rgba(70,110,150,0.4)', 7, 7, 2); circ(g, 'rgba(70,110,150,0.4)', 21, 21, 2);
    }
    c._tkPat = true;
    return c;
  }
  function roomBack(g, x0, x1, yTop, yFloor, o) {
    const fb = 24;
    rect(g, o.wall, x0, yTop, x1 - x0, yFloor - yTop);
    if (o.paper) {
      g.save();
      g.fillStyle = g.createPattern(patternTile(o.paper), 'repeat');
      g.translate(x0, yTop);
      g.fillRect(0, 0, x1 - x0, yFloor - fb - yTop);
      g.restore();
    }
    if (o.wain) {
      rect(g, o.wain, x0, yFloor - fb - o.wainH, x1 - x0, o.wainH);
      g.strokeStyle = U.shade(o.wain, -0.2); g.lineWidth = 2;
      for (let x = x0 + 20; x < x1; x += 34) { g.beginPath(); g.moveTo(x, yFloor - fb - o.wainH + 8); g.lineTo(x, yFloor - fb - 4); g.stroke(); }
      rect(g, U.shade(o.wain, 0.18), x0, yFloor - fb - o.wainH - 5, x1 - x0, 6);
    }
    const fg = g.createLinearGradient(0, yFloor - fb, 0, yFloor);
    fg.addColorStop(0, U.shade(o.floor, -0.12)); fg.addColorStop(1, U.shade(o.floor, 0.08));
    g.fillStyle = fg; g.fillRect(x0, yFloor - fb, x1 - x0, fb);
    g.strokeStyle = U.rgba(U.shade(o.floor, -0.4), 0.45); g.lineWidth = 1.2;
    for (let x = x0 + 8; x < x1; x += 30) { g.beginPath(); g.moveTo(x, yFloor - fb); g.lineTo(x - 6 - (x - (x0 + x1) / 2) * 0.02, yFloor); g.stroke(); }
    rect(g, U.shade(o.wall, -0.32), x0, yFloor - fb - 7, x1 - x0, 7);
    const ag = g.createLinearGradient(0, yTop, 0, yTop + 70);
    ag.addColorStop(0, 'rgba(30,18,10,0.30)'); ag.addColorStop(1, 'rgba(30,18,10,0)');
    g.fillStyle = ag; g.fillRect(x0, yTop, x1 - x0, 70);
    for (const [xa, dir] of [[x0, 1], [x1, -1]]) {
      const sg = g.createLinearGradient(xa, 0, xa + dir * 26, 0);
      sg.addColorStop(0, 'rgba(30,18,10,0.28)'); sg.addColorStop(1, 'rgba(30,18,10,0)');
      g.fillStyle = sg; g.fillRect(Math.min(xa, xa + dir * 26), yTop, 26, yFloor - yTop);
    }
  }
  function wallCut(g, x, w, yTop, yBot, ext) {
    rect(g, ext, x, yTop, w, yBot - yTop);
    g.strokeStyle = U.shade(ext, -0.42); g.lineWidth = 2;
    for (let y = yTop + 12; y < yBot; y += 13) { g.beginPath(); g.moveTo(x + 2, y); g.lineTo(x + w - 2, y); g.stroke(); }
    rect(g, U.shade(ext, -0.5), x, yTop, 2.5, yBot - yTop);
    rect(g, U.shade(ext, -0.5), x + w - 2.5, yTop, 2.5, yBot - yTop);
  }
  function slab(g, x0, x1, y, h) {
    rect(g, SLAB, x0, y, x1 - x0, h);
    rect(g, 'rgba(255,235,210,0.22)', x0, y, x1 - x0, 2.5);
  }
  function foundation(g, x0, x1) {
    rect(g, '#9b9184', x0, -16, x1 - x0, 16);
    g.strokeStyle = 'rgba(50,40,35,0.35)'; g.lineWidth = 1.2;
    for (let x = x0 + 18; x < x1; x += 36) { g.beginPath(); g.moveTo(x, -16); g.lineTo(x, 0); g.stroke(); }
  }
  function gableRoof(g, x0, x1, yb, ph, o) {
    const cx = (x0 + x1) / 2, ov = 30, th = o.th || 28;
    g.fillStyle = o.ext;
    poly(g, [x0, yb, cx, yb - ph, x1, yb]); g.fill();
    g.save();
    poly(g, [x0, yb, cx, yb - ph, x1, yb]); g.clip();
    g.strokeStyle = U.rgba(U.shade(o.ext, -0.45), 0.35); g.lineWidth = 1.6;
    for (let y = yb - 12; y > yb - ph; y -= 13) { g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); }
    const sg = g.createLinearGradient(0, yb - ph, 0, yb - ph + 70);
    sg.addColorStop(0, 'rgba(20,10,10,0.25)'); sg.addColorStop(1, 'rgba(20,10,10,0)');
    g.fillStyle = sg; g.fillRect(x0, yb - ph, x1 - x0, 70);
    g.restore();
    const wy = yb - ph * 0.42;
    if (o.win === 'round') {
      circ(g, o.trim || '#f3ead9', cx, wy, 21); circ(g, '#5f7389', cx, wy, 15);
      rect(g, o.trim || '#f3ead9', cx - 1.5, wy - 15, 3, 30); rect(g, o.trim || '#f3ead9', cx - 15, wy - 1.5, 30, 3);
    } else if (o.win === 'heart') {
      g.fillStyle = U.shade(o.ext, -0.5);
      g.beginPath(); g.moveTo(cx, wy + 12); g.bezierCurveTo(cx - 22, wy - 4, cx - 10, wy - 18, cx, wy - 7); g.bezierCurveTo(cx + 10, wy - 18, cx + 22, wy - 4, cx, wy + 12); g.fill();
    } else if (o.win === 'twin') {
      for (const dx of [-17, 17]) { rect(g, o.trim || '#f3ead9', cx + dx - 12, wy - 18, 24, 34); rect(g, '#5f7389', cx + dx - 8, wy - 14, 16, 26); }
    }
    const sl = ph / (cx - x0);
    const Lx = x0 - ov, Ly = yb + ov * sl, Rx = x1 + ov, Ry = Ly, Ax = cx, Ay = yb - ph;
    const dy = th / Math.cos(Math.atan(sl));
    g.fillStyle = o.roof;
    poly(g, [Lx, Ly, Ax, Ay, Rx, Ry, Rx, Ry - dy, Ax, Ay - dy, Lx, Ly - dy]); g.fill();
    g.strokeStyle = U.shade(o.roof, -0.28); g.lineWidth = 2.2;
    for (const f of [0.34, 0.67]) { g.beginPath(); g.moveTo(Lx, Ly - dy * f); g.lineTo(Ax, Ay - dy * f); g.lineTo(Rx, Ry - dy * f); g.stroke(); }
    for (let side = -1; side <= 1; side += 2) {
      const ex = side < 0 ? Lx : Rx, ey = Ly, len = Math.hypot(Ax - ex, Ay - ey);
      for (let row = 0; row < 3; row++) {
        for (let d = 14 + row * 9; d < len - 10; d += 26) {
          const k = d / len, px = lerp(ex, Ax, k), py = lerp(ey, Ay, k) - dy * (row / 3);
          g.beginPath(); g.moveTo(px, py); g.lineTo(px, py - dy / 3 + 2); g.stroke();
        }
      }
    }
    g.strokeStyle = U.shade(o.roof, 0.22); g.lineWidth = 3;
    g.beginPath(); g.moveTo(Lx, Ly - dy); g.lineTo(Ax, Ay - dy); g.lineTo(Rx, Ry - dy); g.stroke();
    g.strokeStyle = o.trim || '#f3ead9'; g.lineWidth = 5;
    g.beginPath(); g.moveTo(Lx + 8, Ly - 2); g.lineTo(Ax, Ay + 1); g.lineTo(Rx - 8, Ry - 2); g.stroke();
    return { apex: { x: Ax, y: Ay - dy } };
  }
  function chimney(g, x, yRoof, h, w) {
    rect(g, '#8f4f3e', x, yRoof - h, w, h);
    g.strokeStyle = 'rgba(40,20,15,0.35)'; g.lineWidth = 1.2;
    for (let y = yRoof - h + 8; y < yRoof; y += 9) { g.beginPath(); g.moveTo(x, y); g.lineTo(x + w, y); g.stroke(); }
    rect(g, '#6e3a2e', x - 4, yRoof - h - 8, w + 8, 9);
  }
  function frame(g, x, y, w, h, inner) {
    rect(g, '#6b4a36', x - 4, y - 4, w + 8, h + 8);
    rect(g, '#f4ead6', x, y, w, h);
    if (inner) inner(g, x, y, w, h);
  }
  function miniSummit(g, x, y, w, h) {
    rect(g, '#9cc4e0', x, y, w, h);
    g.fillStyle = '#7f8fae'; poly(g, [x, y + h, x + w * 0.5, y + h * 0.18, x + w, y + h]); g.fill();
    g.fillStyle = '#f7f9fc'; poly(g, [x + w * 0.5, y + h * 0.18, x + w * 0.62, y + h * 0.42, x + w * 0.5, y + h * 0.36, x + w * 0.38, y + h * 0.42]); g.fill();
    rect(g, '#e8574a', x + w * 0.5, y + h * 0.08, w * 0.12, h * 0.07);
    rect(g, '#33312e', x + w * 0.5 - 0.5, y + h * 0.08, 1.5, h * 0.12);
  }

  /* ---- the café (x 0..560) ---- */
  const CAFE = { x: 0, w: 560 };
  function cafeBack(g) {
    const w = 560, wt = 20, yF = -16, yT = -266, ext = '#9a6444';
    foundation(g, -4, w + 4);
    roomBack(g, wt, w - wt, yT, yF, { wall: '#f3dcb9', paper: 'stripe', wain: '#a87250', wainH: 92, floor: '#c99c6b' });
    rect(g, '#7a5236', 296, -248, 150, 92); rect(g, '#2f3b37', 302, -242, 138, 80);
    g.save(); g.fillStyle = 'rgba(245,240,230,0.85)'; g.font = Art.font(22, 'hand', 700); g.textBaseline = 'middle';
    g.fillText('coffee', 314, -224); g.fillText('pie', 314, -198); g.fillText('3', 410, -224); g.fillText('4', 410, -198);
    g.strokeStyle = 'rgba(245,240,230,0.6)'; g.lineWidth = 1.5; g.beginPath(); g.arc(398, -178, 7, 0, Math.PI); g.stroke(); g.restore();
    rect(g, '#7a5236', 52, -204, 196, 7);
    for (let i = 0; i < 7; i++) {
      const mx = 66 + i * 27;
      if (i % 3 === 2) { rrect(g, '#e7dccb', mx - 7, -230, 16, 26, 3); rect(g, '#b07a4a', mx - 5, -220, 12, 14); }
      else { rrect(g, ['#e8574a', '#f3e7d8', '#4f7a5a'][i % 3], mx - 8, -220, 16, 16, 3); g.strokeStyle = '#7a5236'; g.lineWidth = 2; g.beginPath(); g.arc(mx + 10, -213, 4, -1.4, 1.4); g.stroke(); }
    }
    frame(g, 470, -240, 44, 54, (x, fx, fy) => { rrect(x, '#c66a43', fx + 12, fy + 20, 20, 18, 4); x.strokeStyle = '#a0a0a0'; x.lineWidth = 1.5; x.beginPath(); x.moveTo(fx + 18, fy + 16); x.quadraticCurveTo(fx + 22, fy + 10, fx + 18, fy + 6); x.stroke(); });
    potted(g, 274, -204, 'trail', 0.8, 7, '#e6d8c2');
    g.strokeStyle = '#2a2421'; g.lineWidth = 2;
    for (const px of [160, 400]) { g.beginPath(); g.moveTo(px, -266); g.lineTo(px, -236); g.stroke(); }
    // back counter with espresso machine
    rect(g, '#7c533a', 340, -138, 180, 8);
    rrect(g, '#c9ccd1', 432, -194, 74, 56, 6); rect(g, '#9da2a8', 438, -158, 62, 6); rrect(g, '#2a2421', 446, -158, 10, 12, 2); rrect(g, '#2a2421', 480, -158, 10, 12, 2);
    circ(g, '#e8574a', 492, -180, 4); rect(g, '#f3e7d8', 448, -142, 10, 4);
    // small table + stools (left)
    rect(g, '#6b4a36', 96, -88, 6, 64); rrect(g, '#8a5d3d', 64, -96, 72, 10, 4); rect(g, '#6b4a36', 82, -30, 40, 5);
    rrect(g, '#f3e7d8', 74, -108, 13, 12, 2);
    for (const sx of [40, 160]) { rect(g, '#6b4a36', sx - 3, -60, 6, 38); ell(g, '#c66a43', sx, -62, 16, 5); }
    wallCut(g, 0, wt, yT - 16, yF, ext);
    wallCut(g, w - wt, wt, yT - 16, yF, ext);
    slab(g, -6, w + 6, yT - 16, 16);
    gableRoof(g, -6, w + 6, yT - 16, 166, { ext, roof: '#5f3b30', win: 'twin', trim: '#efe2cc' });
    // hanging sign on the left wall
    g.strokeStyle = '#2a2421'; g.lineWidth = 3;
    g.beginPath(); g.moveTo(0, -212); g.lineTo(-58, -212); g.stroke();
    g.lineWidth = 1.5; g.beginPath(); g.moveTo(-50, -212); g.lineTo(-50, -200); g.moveTo(-14, -212); g.lineTo(-14, -200); g.stroke();
    rrect(g, '#efe2cc', -62, -200, 60, 44, 5); rrect(g, '#c66a43', -44, -186, 24, 20, 4);
    g.strokeStyle = '#c66a43'; g.lineWidth = 3; g.beginPath(); g.arc(-18, -177, 5, -1.3, 1.3); g.stroke();
  }
  function cafeFront(g) {
    rrect(g, '#e9d8bd', 316, -116, 234, 12, 3);
    rect(g, '#8a5a3c', 322, -104, 222, 80);
    for (let i = 0; i < 4; i++) rrect(g, '#9c6a48', 330 + i * 54, -95, 46, 62, 3);
    rect(g, 'rgba(0,0,0,0.2)', 322, -104, 222, 6);
    ell(g, '#f6efe6', 360, -116, 26, 4); rrect(g, '#f2c9a6', 344, -134, 32, 18, 4); rect(g, '#d97a8a', 344, -128, 32, 4);
    g.fillStyle = 'rgba(220,235,245,0.35)'; g.beginPath(); g.arc(360, -120, 24, Math.PI, 0); g.fill();
    rrect(g, 'rgba(220,235,245,0.6)', 516, -140, 20, 24, 3); circ(g, '#7fa86a', 523, -126, 3); circ(g, '#7fa86a', 529, -129, 3);
  }

  /* ---- granny's house (x 600..980) ---- */
  const GRAN = { x: 600, w: 380 };
  function grannyBack(g) {
    const w = 380, wt = 18, yF = -16, yT = -266, ext = '#a5c8d9';
    foundation(g, -4, w + 4);
    roomBack(g, wt, w - wt, yT, yF, { wall: '#f7e7c7', paper: 'rose', floor: '#a8754e' });
    rect(g, '#f3ead9', 238, -236, 104, 104);
    const wg = g.createLinearGradient(0, -230, 0, -138); wg.addColorStop(0, '#9ccbe8'); wg.addColorStop(1, '#d6ebf2');
    g.fillStyle = wg; g.fillRect(244, -230, 92, 92);
    g.fillStyle = 'rgba(255,255,255,0.85)';
    g.beginPath(); g.moveTo(244, -230); g.lineTo(272, -230); g.quadraticCurveTo(260, -184, 252, -138); g.lineTo(244, -138); g.fill();
    g.beginPath(); g.moveTo(336, -230); g.lineTo(308, -230); g.quadraticCurveTo(320, -184, 328, -138); g.lineTo(336, -138); g.fill();
    rect(g, '#f3ead9', 288, -230, 4, 92); rect(g, '#f3ead9', 240, -136, 100, 8);
    potted(g, 304, -136, 'bloom', 0.6, 21, '#c66a43');
    g.save(); g.translate(112, -208);
    ell(g, '#b08a4a', 0, 0, 30, 36); ell(g, '#f2e6cf', 0, 0, 24, 30);
    circ(g, '#8e8a90', 0, 6, 12); g.fillStyle = '#8e8a90'; poly(g, [-11, 0, -8, -14, -2, -4]); g.fill(); poly(g, [11, 0, 8, -14, 2, -4]); g.fill();
    circ(g, '#2a2421', -4, 4, 1.6); circ(g, '#2a2421', 4, 4, 1.6);
    g.restore();
    rrect(g, '#7a5236', 192, -240, 26, 34, 3); circ(g, '#f3e7d8', 205, -226, 8);
    g.strokeStyle = '#2a2421'; g.lineWidth = 1.4; g.beginPath(); g.moveTo(205, -226); g.lineTo(205, -232); g.moveTo(205, -226); g.lineTo(209, -224); g.stroke();
    g.fillStyle = '#5f3b30'; poly(g, [188, -240, 205, -252, 222, -240]); g.fill();
    rect(g, '#3a3330', 44, -196, 4, 176); ell(g, '#3a3330', 46, -22, 16, 4);
    g.fillStyle = '#f0c27a'; poly(g, [28, -196, 64, -196, 56, -226, 36, -226]); g.fill();
    g.strokeStyle = '#d08a3a'; g.lineWidth = 1.2; for (let x = 29; x <= 63; x += 4) { g.beginPath(); g.moveTo(x, -196); g.lineTo(x, -190); g.stroke(); }
    ell(g, '#a84848', 214, -28, 132, 11); ell(g, '#c76a5a', 214, -28, 116, 8); ell(g, '#a84848', 214, -28, 80, 5);
    rrect(g, '#b8895a', 78, -46, 34, 24, 4); circ(g, '#7fa8d6', 88, -48, 8); circ(g, '#e8a3a8', 102, -50, 7);
    g.strokeStyle = '#c9b090'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(92, -56); g.lineTo(110, -74); g.moveTo(98, -56); g.lineTo(104, -76); g.stroke();
    // wing chair back
    rrect(g, '#b86f7d', 128, -184, 86, 140, 16);
    rrect(g, '#c98290', 136, -176, 70, 122, 12);
    rrect(g, '#b86f7d', 120, -116, 102, 30, 10);
    rect(g, '#6b4a36', 248, -78, 4, 56); rect(g, '#6b4a36', 276, -78, 4, 56); rrect(g, '#8a5d3d', 240, -84, 48, 8, 3); ell(g, '#f6efe6', 264, -86, 20, 3);
    rrect(g, '#f3e7d8', 256, -98, 14, 11, 2); ell(g, '#f3e7d8', 263, -88, 10, 2.5);
    wallCut(g, 0, wt, yT - 16, yF, ext);
    wallCut(g, w - wt, wt, yT - 16, yF, ext);
    slab(g, -6, w + 6, yT - 16, 16);
    chimney(g, 262, -380, 74, 30);
    gableRoof(g, -6, w + 6, yT - 16, 176, { ext, roof: '#b0503f', win: 'heart', trim: '#ffffff' });
  }
  function grannyFront(g) {
    rrect(g, '#a8606d', 124, -98, 96, 26, 10);
    rrect(g, '#b86f7d', 128, -76, 92, 36, 6);
    rect(g, '#6b4a36', 134, -40, 6, 20); rect(g, '#6b4a36', 208, -40, 6, 20);
  }

  /* ---- the teen's house (x 1020..1440), two storeys ---- */
  const TEEN = { x: 1020, w: 420 };
  function teenBack(g) {
    const w = 420, wt = 20, ext = '#b6c88f';
    foundation(g, -4, w + 4);
    roomBack(g, wt, w - wt, -256, -16, { wall: '#fbf1d9', floor: '#d8c3a0' });
    g.save(); g.fillStyle = g.createPattern(patternTile('tile'), 'repeat'); g.translate(0, -160); g.fillRect(wt, 0, w - wt * 2, 44); g.restore();
    rrect(g, '#ece7dc', 34, -212, 76, 178, 8); rect(g, '#c9c3b6', 34, -150, 76, 3); rect(g, '#9da2a8', 98, -196, 4, 30); rect(g, '#9da2a8', 98, -140, 4, 40);
    rrect(g, '#e8574a', 46, -196, 12, 10, 2); rrect(g, '#4f7a5a', 64, -186, 10, 10, 2); rrect(g, '#f3c35a', 48, -130, 14, 12, 2); rect(g, '#ffffff', 70, -134, 16, 20);
    rect(g, '#f3ead9', 150, -236, 88, 76); rect(g, '#a6d2ea', 156, -230, 76, 64); rect(g, '#f3ead9', 192, -230, 4, 64);
    potted(g, 172, -160, 'leafy', 0.55, 31, '#e6d8c2'); potted(g, 214, -160, 'cactus', 0.55, 32, '#c66a43');
    circ(g, '#2a2421', 334, -212, 18); circ(g, '#fbf6ee', 334, -212, 15);
    g.strokeStyle = '#2a2421'; g.lineWidth = 2; g.beginPath(); g.moveTo(334, -212); g.lineTo(334, -222); g.moveTo(334, -212); g.lineTo(341, -209); g.stroke();
    // dad's chair (behind him)
    rrect(g, '#7a5236', 206, -160, 10, 130, 3); rect(g, '#7a5236', 206, -80, 54, 7); rect(g, '#6b4a36', 252, -74, 5, 50);
    // upper floor: bedroom
    roomBack(g, wt, w - wt, -492, -272, { wall: '#cdbde8', paper: 'stripe', floor: '#bf8f66' });
    frame(g, 44, -466, 58, 76, (x, fx, fy, fw, fh) => miniSummit(x, fx, fy, fw, fh));
    rrect(g, '#f2a59e', 116, -456, 44, 30, 3); TK.flowerIcon(g, 138, -441, 10, 0.2);
    rect(g, '#7a5236', 40, -366, 120, 6);
    for (let i = 0; i < 8; i++) rect(g, ['#e8574a', '#4f7a5a', '#f3c35a', '#6fb7ff', '#b49cff'][i % 5], 46 + i * 13, -396 + (i % 3) * 4, 10, 30 - (i % 3) * 4);
    rrect(g, '#8a5d3d', 194, -408, 18, 112, 5);
    rrect(g, '#8a5d3d', 384, -354, 14, 58, 4);
    rrect(g, '#f3eee6', 204, -344, 186, 24, 6);
    rrect(g, '#ffffff', 212, -370, 56, 28, 10);
    rect(g, '#6b4a36', 204, -320, 194, 32);
    g.strokeStyle = '#3a3330'; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(26, -476); for (let i = 0; i <= 12; i++) { const x = 26 + i * 31; g.quadraticCurveTo(x - 15, -462, x, -476); } g.stroke();
    wallCut(g, 0, wt, -508, -16, ext);
    wallCut(g, w - wt, wt, -508, -16, ext);
    slab(g, -6, w + 6, -272, 16);
    slab(g, -6, w + 6, -508, 16);
    gableRoof(g, -6, w + 6, -508, 150, { ext, roof: '#5c5a68', win: 'round', trim: '#f3ead9' });
  }
  function teenFront(g) {
    rrect(g, '#a87250', 270, -108, 124, 10, 3); rect(g, '#7c533a', 282, -98, 6, 76); rect(g, '#7c533a', 372, -98, 6, 76);
    rrect(g, '#f3e7d8', 338, -120, 16, 12, 2);
    g.fillStyle = '#3aa39b';
    g.beginPath(); g.moveTo(266, -344); g.quadraticCurveTo(306, -366, 388, -354); g.lineTo(390, -320); g.lineTo(256, -320); g.closePath(); g.fill();
    for (let i = 0; i < 4; i++) circ(g, '#5cc1b8', 290 + i * 28, -336 + (i % 2) * 6, 5);
  }

  /* ---- the square (x 1480..2120) and the town hall (x 2160..2500) ---- */
  function squareBack(g) {
    rect(g, '#cfc5b6', -40, -40, 700, 40);
    g.strokeStyle = 'rgba(90,70,60,0.25)'; g.lineWidth = 1.2;
    for (let x = -40; x < 660; x += 26) { g.beginPath(); g.moveTo(x, -40); g.lineTo(x - 8, 0); g.stroke(); }
    for (let y = -30; y < 0; y += 10) { g.beginPath(); g.moveTo(-40, y); g.lineTo(660, y); g.stroke(); }
    rrect(g, '#b8ad9e', -40, -82, 700, 42, 4); rect(g, '#d2c8b9', -40, -86, 700, 8);
    for (let i = 0; i < 9; i++) potted(g, 10 + i * 76, -86, ['bloom', 'round', 'bloom'][i % 3], 0.9, 600 + i, '#c66a43');
  }
  function hallBack(g) {
    // a timber-framed town hall with a little clock tower
    const w = 340, wall = '#f3e8d2', beam = '#5a3d30';
    rect(g, '#d9ccb5', 0, -34, w, 34);
    rect(g, wall, 0, -300, w, 266);
    g.fillStyle = beam;
    for (let x = 0; x <= w; x += 68) g.fillRect(x - 4, -300, 8, 266);
    g.fillRect(0, -304, w, 9); g.fillRect(0, -168, w, 9); g.fillRect(0, -40, w, 8);
    g.strokeStyle = beam; g.lineWidth = 7;
    for (let x = 0; x < w; x += 136) { g.beginPath(); g.moveTo(x + 4, -176); g.lineTo(x + 64, -296); g.moveTo(x + 132, -176); g.lineTo(x + 72, -296); g.stroke(); }
    for (let i = 0; i < 5; i++) {
      const wx = 34 + i * 68;
      if (i === 2) { rrect(g, '#6b4a36', wx - 30, -152, 60, 112, 26); rect(g, U.shade('#6b4a36', 0.15), wx - 2, -148, 4, 104); continue; }
      rrect(g, '#5f7389', wx - 18, -150, 36, 64, 16);
      rect(g, '#f3e8d2', wx - 1.5, -150, 3, 64);
    }
    for (let i = 0; i < 5; i++) { if (i === 2) continue; const wx = 34 + i * 68; rect(g, '#5f7389', wx - 16, -150 + 2, 0, 0); }
    g.fillStyle = '#5c5a68'; poly(g, [-26, -296, w / 2, -390, w + 26, -296]); g.fill();
    g.strokeStyle = '#f3e8d2'; g.lineWidth = 5; g.beginPath(); g.moveTo(-20, -298); g.lineTo(w / 2, -386); g.lineTo(w + 20, -298); g.stroke();
    // tower
    const tx = w / 2;
    rect(g, wall, tx - 44, -540, 88, 170);
    g.fillStyle = beam; g.fillRect(tx - 48, -544, 8, 174); g.fillRect(tx + 40, -544, 8, 174); g.fillRect(tx - 48, -548, 96, 8);
    circ(g, beam, tx, -470, 34); circ(g, '#fbf6ee', tx, -470, 28);
    g.strokeStyle = beam; g.lineWidth = 2;
    for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; g.beginPath(); g.moveTo(tx + Math.cos(a) * 22, -470 + Math.sin(a) * 22); g.lineTo(tx + Math.cos(a) * 26, -470 + Math.sin(a) * 26); g.stroke(); }
    g.lineWidth = 3; g.beginPath(); g.moveTo(tx, -470); g.lineTo(tx, -488); g.moveTo(tx, -470); g.lineTo(tx + 12, -464); g.stroke();
    rrect(g, '#5f7389', tx - 12, -418, 24, 38, 11);
    g.fillStyle = '#5c5a68'; poly(g, [tx - 60, -544, tx, -650, tx + 60, -544]); g.fill();
    g.strokeStyle = '#3b2a25'; g.lineWidth = 3; g.beginPath(); g.moveTo(tx, -650); g.lineTo(tx, -682); g.stroke();
    g.fillStyle = '#e8574a'; poly(g, [tx, -682, tx + 22, -676, tx, -668]); g.fill();
    // flower boxes
    for (let i = 0; i < 5; i++) { if (i === 2) continue; const wx = 34 + i * 68; rrect(g, '#7a5236', wx - 22, -86, 44, 10, 2); for (let j = 0; j < 4; j++) circ(g, j % 2 ? '#e5484d' : '#f48fb1', wx - 15 + j * 10, -90, 5); }
  }
  function bigTree(g) {
    g.fillStyle = '#6b4a36';
    g.beginPath(); g.moveTo(-15, 0); g.quadraticCurveTo(-8, -120, -16, -230); g.lineTo(8, -230); g.quadraticCurveTo(4, -120, 15, 0); g.closePath(); g.fill();
    g.strokeStyle = '#6b4a36'; g.lineCap = 'round'; g.lineWidth = 11;
    g.beginPath(); g.moveTo(-4, -170); g.quadraticCurveTo(-40, -215, -84, -246); g.stroke();
    g.beginPath(); g.moveTo(0, -200); g.quadraticCurveTo(40, -236, 76, -276); g.stroke();
    const blobs = [[-96, -282, 66], [-30, -340, 88], [54, -318, 80], [108, -258, 58], [-128, -226, 48], [0, -258, 82], [74, -214, 52], [-64, -206, 54], [20, -392, 52]];
    for (const [x, y, r] of blobs) circ(g, '#4b7845', x, y, r);
    for (const [x, y, r] of blobs) circ(g, '#5e9152', x - r * 0.14, y - r * 0.18, r * 0.8);
    for (const [x, y, r] of blobs.slice(0, 6)) circ(g, '#77a865', x - r * 0.3, y - r * 0.4, r * 0.4);
    g.fillStyle = 'rgba(30,40,20,0.18)';
    g.beginPath(); g.ellipse(0, -186, 120, 30, 0, 0, TAU); g.fill();
  }

  // draw a static layer (house-local coords) at x along the street. Drawn as vectors every
  // frame on purpose: large cached canvases make Chrome flush the canvas recording mid-frame.
  function layerImg(ctx, key, fn, x) { // key: label only
    ctx.save();
    ctx.translate(x, GY);
    fn(ctx);
    ctx.restore();
  }

  /* ---------------- characters ---------------- */
  const L = TK.LOOK;
  const SR = 0.68;                       // people indoors
  const SQ = 0.72;                       // people on the square (a little nearer)
  const cast = (t) => {
    const o = {};
    const fl = (a, b, k) => lerp(a, b, clamp(k));
    // h3 at the café, miming the narrator's lunatic grin
    const tellK = U.fade(t, T.tell[0], 4.0, 0.25, 0.6);
    o.h3 = {
      x: CAFE.x + 222, y: GY - 26, s: SR, look: 'h3', t, facing: 1,
      gesture: 'open', gw: 0.85 * U.fade(t, 1.25, 2.8, 0.3, 0.5), lean: 0.08 * U.fade(t, 1.25, 2.8, 0.3, 0.5),
      head: { tilt: Math.sin(t * 7) * 0.05 * tellK - 0.04, nod: t > 2.5 && t < 3.8 ? Math.max(0, Math.sin((t - 2.5) * 9)) * 0.1 : 0 },
      face: { smile: fl(0.35, 1, tellK), open: 0.45 * tellK, eyes: tellK > 0.5 ? 'sparkle' : 'open', browUp: 0.6 * tellK, talk: t > T.tell[0] && t < 2.4 ? 1 : 0 },
    };
    // the barista
    const hearK = U.ease(t, 2.4, 2.65, 'outBack');
    const phoneK = U.ease(t, 3.65, 4.05, 'inOutSine') * (1 - U.ease(t, 5.3, 5.8, 'inOutSine'));
    o.barista = {
      x: CAFE.x + 452, y: GY - 36, s: SR * 0.98, look: L.barista, t, facing: -1,
      lean: -0.06 * hearK + 0.04 * phoneK,
      head: { tilt: -0.07 * hearK * (1 - phoneK) + 0.12 * phoneK, turn: 0.15 },
      face: {
        smile: phoneK > 0.3 ? 0.45 : t < 2.4 ? 0.2 : -0.1, mouth: t > 2.4 && t < 3.2 ? 'o' : undefined, open: t > 2.4 && t < 3.2 ? 0.55 : 0,
        eyes: t > 2.38 && t < 3.7 ? 'wide' : 'open', browUp: t > 2.38 && t < 3.7 ? 1 : 0.2, lookX: phoneK > 0.3 ? 0.3 : 0, lookY: phoneK > 0.3 ? 0.9 : 0,
        talk: t > T.b1[0] && t < T.b1[0] + 0.5 ? 1 : 0,
      },
      phone: phoneK, phoneGlow: U.bump(t, 4.35, 0.25) + phoneK * 0.35,
    };
    // granny (+ the cat, drawn separately)
    const dingA = T.hopA[1];
    const gSurp = U.fade(t, dingA, dingA + 0.75, 0.05, 0.25);
    const gShow = U.ease(t, 5.1, 5.45, 'inOutBack') * (1 - U.ease(t, 6.95, 7.2, 'inOutSine'));
    o.granny = {
      x: GRAN.x + 176, y: GY - 26, s: SR, look: L.granny, t, facing: 1, pose: 'bench',
      head: { tilt: 0.1 * (1 - gShow) - 0.04 * gShow + (t > 5.2 && t < 7.2 ? Math.sin(t * 5) * 0.04 : 0), turn: 0.1 },
      face: {
        smile: gSurp > 0.2 ? 0.1 : gShow > 0.2 ? 0.85 : 0.35, open: gShow > 0.2 ? 0.25 : 0, mouth: gSurp > 0.4 ? 'o' : undefined,
        eyes: gSurp > 0.3 ? 'wide' : gShow > 0.3 ? 'happy' : 'open', browUp: gSurp, lookY: gShow > 0.2 ? 0 : 0.8, lookX: 0.3,
        talk: t > T.b2[0] && t < T.b2[0] + 0.8 ? 1 : 0,
      },
      show: gShow, phoneGlow: Math.max(U.bump(t, dingA + 0.05, 0.3), U.bump(t, T.hopB[0] - 0.05, 0.22), 0.25),
    };
    // the teen upstairs
    const dingB = T.hopB[1];
    const sitUp = U.ease(t, dingB + 0.05, dingB + 0.4, 'outBack');
    o.teen = {
      x: TEEN.x + 262, y: GY - 344, s: SR * 0.97, look: L.teen, t, facing: 1, pose: 'sit',
      lean: lerp(-0.42, 0.08, sitUp),
      head: { tilt: lerp(0.25, -0.05, sitUp) + (t > 8.1 && t < 9.8 ? Math.sin(t * 6) * 0.03 : 0), turn: 0.2 },
      face: {
        smile: sitUp > 0.5 ? 0.85 : 0.15, open: sitUp > 0.5 && t < 9.9 ? 0.3 : 0,
        eyes: sitUp > 0.5 ? 'sparkle' : 'open', browUp: sitUp * 0.7, lookY: sitUp > 0.5 ? 0.2 : 0.9,
        talk: t > T.b3[0] && t < T.b3[0] + 0.7 ? 1 : 0,
      },
      phoneGlow: Math.max(0.35, U.bump(t, dingB + 0.05, 0.3), U.bump(t, T.fan[0] - 0.02, 0.3)),
    };
    // dad downstairs, hidden behind his newspaper until his phone pings
    const peek = U.ease(t, 10.35, 10.65, 'outBack');
    o.dad = {
      x: TEEN.x + 236, y: GY - 26, s: SR, look: L.dad, t, facing: 1, pose: 'bench',
      head: { tilt: 0.02 },
      face: { eyes: peek > 0.3 ? 'wide' : 'open', browUp: peek, smile: 0.1, lookX: 0.4 },
      peek,
    };
    // three of the hikers on the square
    const dingC = T.hopC[1];
    const showC = U.ease(t, dingC + 0.1, dingC + 0.45, 'outBack');
    const lean2 = U.ease(t, dingC + 0.15, dingC + 0.6, 'outBack');
    o.h4 = {
      x: 1928, y: GY + 16, s: SQ, look: 'h4', t, facing: -1, pose: 'bench',
      head: { tilt: lerp(0.22, 0.02, showC), turn: lerp(0, 0.35, showC) },
      face: { eyes: t > dingC - 0.02 && t < dingC + 0.9 ? 'wide' : showC > 0.5 ? 'happy' : 'open', smile: showC > 0.5 ? 0.6 : 0.1, lookY: showC > 0.5 ? 0 : 0.9, browUp: showC * 0.6 },
      show: showC, phoneGlow: Math.max(0.4, U.bump(t, dingC, 0.35)),
    };
    o.h2 = {
      x: 1790, y: GY + 18, s: SQ, look: 'h2', t, facing: 1,
      lean: 0.3 * lean2, gesture: 'reach', gw: 0.5 * lean2,
      head: { tilt: 0.12 * lean2 + (t > 11.2 && t < 13.0 ? Math.sin(t * 7) * 0.035 : 0) },
      face: { eyes: lean2 > 0.4 ? 'sparkle' : 'open', smile: lean2 > 0.4 ? 0.85 : 0.25, open: lean2 > 0.4 ? 0.35 : 0, browUp: lean2 * 0.8, lookY: 0.5 * lean2, talk: t > T.b4[0] && t < T.b4[0] + 0.7 ? 1 : 0 },
    };
    const nodK = U.fade(t, 11.4, 13.4, 0.2, 0.3);
    o.h1 = {
      x: 1660, y: GY + 20, s: SQ, look: 'h1', t, facing: 1,
      lean: 0.12 * lean2, gesture: 'hips', gw: 1 - lean2 * 0.7,
      head: { nod: Math.max(0, Math.sin(t * 9)) * 0.14 * nodK, tilt: 0.06 * lean2 },
      face: { eyes: lean2 > 0.4 ? 'happy' : 'open', smile: lean2 > 0.4 ? 0.75 : 0.2, lookY: 0.3 * lean2 },
    };
    return o;
  };
  // body-local point (feet origin, +x forward) → world
  const local = (o, lx, ly) => {
    const look = typeof o.look === 'string' ? Art.CAST[o.look] : o.look;
    const S = o.s * (look.height || 1), f = o.facing === undefined ? 1 : o.facing;
    return { x: o.x + lx * S * f, y: o.y + ly * S };
  };

  /* ---------------- the cat ---------------- */
  function cat(g, x, y, s, t, o) {
    g.save();
    g.translate(x, y);
    g.scale(s, s);
    const body = '#8e8a90', dark = '#6c6870';
    const sw = Math.sin(t * 1.4) * 0.5 + (o.flick || 0);
    g.strokeStyle = dark; g.lineWidth = 7; g.lineCap = 'round';
    g.beginPath(); g.moveTo(28, -10); g.quadraticCurveTo(54, -12 + sw * 8, 48 + sw * 10, -36 - Math.abs(sw) * 6); g.stroke();
    ell(g, body, 8, -18, 33, 19);
    g.strokeStyle = dark; g.lineWidth = 3;
    for (const dx of [8, 18, 28]) { g.beginPath(); g.moveTo(dx, -36); g.quadraticCurveTo(dx + 4, -26, dx, -18); g.stroke(); }
    ell(g, '#a6a1a8', -12, -4, 12, 5); ell(g, '#a6a1a8', 8, -3, 11, 5);
    const ear = o.ears || 0;
    g.fillStyle = body;
    poly(g, [-36, -40, -33, -58 - ear * 6, -24, -45]); g.fill();
    poly(g, [-20, -45, -13, -60 - ear * 6, -10, -40]); g.fill();
    circ(g, body, -24, -32, 16);
    ell(g, '#c9c4ca', -28, -25, 7, 5);
    if (o.eyes === 'flat') {
      g.strokeStyle = '#2a2421'; g.lineWidth = 2.2;
      for (const ex of [-32, -18]) { ell(g, '#d9e27a', ex, -34, 3.6, 2); g.beginPath(); g.moveTo(ex - 4.5, -35); g.lineTo(ex + 4.5, -35); g.stroke(); }
    } else {
      const bl = U.blink(t, 77);
      for (const ex of [-32, -18]) { ell(g, '#d9e27a', ex, -35, 3.6, 3.8 * (1 - bl * 0.9) + 0.3); ell(g, '#2a2421', ex, -35, 1.3, 3.2 * (1 - bl * 0.9) + 0.2); }
    }
    g.fillStyle = '#d98a8a'; poly(g, [-27, -28, -23, -28, -25, -25.5]); g.fill();
    g.restore();
  }

  /* ---------------- gossip bubbles ---------------- */
  function gossip(ctx, t, t0, t1, text, icon, b) {
    if (t < t0 || t > t1) return;
    const typeDur = Math.min(2.4, 0.15 + text.length * 0.032);
    const pop = U.prog(t, t0, t0 + 0.4), alpha = U.fade(t, t0, t1, 0.12, 0.35), reveal = U.prog(t, t0 + 0.08, t0 + 0.08 + typeDur);
    const box = Art.bubble(ctx, text, { x: b.x, y: b.y, tx: b.tx, ty: b.ty, alpha, pop, reveal, size: 36 });
    if (!box) return;
    const ip = U.prog(t, t0 + 0.12, t0 + 0.5);
    if (ip <= 0) return;
    const sc = lerp(0.55, 1, U.E.outBack(pop));
    TK.iconBubble(ctx, b.x + (box.x - b.x) * sc + 6, b.y + (box.y - b.y) * sc + 4, 28, icon, { sc: U.E.outBack(ip), alpha, t, tail: 2.4, rot: -0.2 });
  }

  /* ---------------- sky (screen space, shared by both sets) ---------------- */
  function drawSky(ctx, t, P, tilt) {
    // the sky sits at "infinity": during the crane it slides at 0.45× so the warm lower
    // bands of the gradient stay in frame while we look up through the time-lapse
    const st = tilt * 0.45;
    TK.sky(ctx, P, 760 + st);
    const lapse = U.prog(t, T.lapse[0], T.lapse[1]);
    const night = U.bump(lapse, 0.5, 0.2);
    if (night > 0) Art.stars(ctx, { seed: 10, count: 240, t, alpha: night, y0: 0, y1: H });
    if (lapse > 0 && lapse < 1) {
      const s1 = U.prog(lapse, 0, 0.34), mo = U.prog(lapse, 0.34, 0.68), s2 = U.prog(lapse, 0.66, 1);
      if (s1 < 1) Art.sun(ctx, lerp(820, 2060, s1), lerp(300, 900, s1 * s1), 42, P.sun, 1 - s1 * 0.5);
      if (mo > 0 && mo < 1) Art.sun(ctx, lerp(-100, 2020, mo), 820 - Math.sin(mo * Math.PI) * 560, 30, '#eef2ff', Math.sin(mo * Math.PI));
      if (s2 > 0) Art.sun(ctx, lerp(-100, 640, s2), lerp(960, 300, U.E.outSine(s2)), 42, P.sun, s2);
    } else if (t < T.lapse[0]) {
      Art.sun(ctx, 250, 250 + st, 36, P.sun, 0.75);
      Art.rays(ctx, { x: 250, y: 250 + st, angle: 0.62, spread: 0.55, count: 6, len: 1700, color: P.light, alpha: 0.05, t, seed: 4 });
    }
    // a few birds crossing over the town
    for (let i = 0; i < 4; i++) {
      const sp = 38 + i * 7, bx = ((U.hash(i, 71) * 2200 + t * sp) % 2300) - 160;
      const by = 250 + U.hash(i, 72) * 150 + Math.sin(t * 0.8 + i * 2) * 10 + tilt;
      if (by < 120 || by > 980) continue;
      const fl = Math.sin(t * 8 + i * 1.7), sc = 0.8 + U.hash(i, 73) * 0.5;
      ctx.strokeStyle = U.rgba(U.mix('#3c4058', P.sky[0], 0.3), 0.6); ctx.lineWidth = 2.4; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(bx - 11 * sc, by - fl * 6 * sc); ctx.quadraticCurveTo(bx - 4 * sc, by - 3 * sc, bx, by); ctx.quadraticCurveTo(bx + 4 * sc, by - 3 * sc, bx + 11 * sc, by - fl * 6 * sc); ctx.stroke();
    }
    const nightK = U.bump(lapse, 0.5, 0.26);
    const cc = U.mix(U.mix('#ffffff', P.sky[2], 0.3), '#4a5378', nightK * 0.9);
    const off = t * 10 + U.ease(t, T.lapse[0] - 0.3, T.lapse[1] + 0.3, 'inOutSine') * 3600;
    Art.clouds(ctx, { seed: 6, count: 5, y0: 150 + st, y1: 230 + st, offset: off, color: cc, alpha: 0.72, scale: 0.62 });
    // high clouds, only seen while the camera looks up into the sky
    if (tilt > 300) {
      Art.clouds(ctx, { seed: 12, count: 6, y0: -470 + st, y1: -250 + st, offset: off * 1.25, color: cc, alpha: 0.8, scale: 1.0 });
      Art.clouds(ctx, { seed: 15, count: 5, y0: -170 + st, y1: 40 + st, offset: off * 0.9, color: U.mix(cc, P.sky[1], 0.3), alpha: 0.72, scale: 0.8 });
    }
  }

  /* ---------------- town set ---------------- */
  function drawTown(ctx, t, P, tilt) {
    const cam = townCam(t);
    const A = {};
    const scr = (p) => { const s = TK.toScreen(cam, p.x, p.y); return { x: s.x, y: s.y + tilt }; };

    ctx.save();
    ctx.translate(0, tilt);
    ctx.save();
    Art.cam(ctx, TK.layer(cam, REST, 0.05, 960, 540));
    TK.backdrop(ctx, P, { t, y: 500, sx: 1330, sh: 330, sw: 580, glow: 0.42 });
    ctx.restore();
    ctx.save();
    Art.cam(ctx, TK.layer(cam, REST, 0.17, 960, 540));
    Art.ridge(ctx, { seed: 33, y: 668, amp: 70, freq: 0.0022, color: U.mix(P.trees[0], P.fog, 0.4), x0: -800, x1: W + 800, step: 14 });
    Art.forest(ctx, { seed: 41, y: 650, spacing: 38, hMin: 40, hMax: 78, color: U.mix(P.trees[0], P.fog, 0.36), light: U.mix(P.trees[0], P.light, 0.2) });
    ctx.restore();
    const hl = TK.layer(cam, REST, 0.42, 960, 540);
    ctx.save();
    Art.cam(ctx, hl);
    TK.drawStrip(ctx, HILL, 'town10', Object.assign({ vx0: hl.x - W / 2 / hl.zoom, vx1: hl.x + W / 2 / hl.zoom }, HILL_HAZE));
    FAN.forEach((wn, i) => {
      const on = fanOn(t, i);
      if (on <= 0) return;
      Art.glow(ctx, wn.x, wn.y, 30, '#bfe0ff', 0.7 * on);
      rect(ctx, U.rgba('#e9f6ff', on), wn.x - wn.w / 2, wn.y - wn.h / 2, wn.w, wn.h);
    });
    ctx.restore();

    // main street layer
    ctx.save();
    Art.cam(ctx, { x: cam.x, y: cam.y, zoom: cam.z });
    rect(ctx, '#d5cbbd', cam.x - 1700, GY, 3400, 26);
    rect(ctx, 'rgba(255,255,255,0.35)', cam.x - 1700, GY, 3400, 3);
    ctx.strokeStyle = 'rgba(90,70,60,0.25)'; ctx.lineWidth = 1.5;
    for (let x = Math.floor((cam.x - 1500) / 60) * 60; x < cam.x + 1500; x += 60) { ctx.beginPath(); ctx.moveTo(x, GY + 3); ctx.lineTo(x - 4, GY + 26); ctx.stroke(); }
    rect(ctx, '#a99e90', cam.x - 1700, GY + 26, 3400, 8);
    rect(ctx, '#8f877d', cam.x - 1700, GY + 34, 3400, 400);
    ctx.fillStyle = 'rgba(255,255,255,0.07)';
    for (let i = Math.floor((cam.x - 1500) / 34); i < (cam.x + 1500) / 34; i++) for (let r = 0; r < 3; r++) {
      ctx.beginPath(); ctx.ellipse(i * 34 + (r % 2) * 17 + U.hash(i, r) * 6, GY + 50 + r * 26, 13, 7, 0, 0, TAU); ctx.fill();
    }
    const vis = (x0, x1) => { const a = TK.toScreen(cam, x0, 0).x, b = TK.toScreen(cam, x1, 0).x; return b > -150 && a < W + 150; };
    const O = cast(t);
    // ---- the café
    if (vis(CAFE.x - 80, CAFE.x + CAFE.w + 80)) {
      layerImg(ctx, 'cafeB', cafeBack, CAFE.x);
      for (const lx of [160, 400]) {
        ctx.fillStyle = '#2f5a45';
        poly(ctx, [CAFE.x + lx - 17, GY - 220, CAFE.x + lx + 17, GY - 220, CAFE.x + lx + 8, GY - 238, CAFE.x + lx - 8, GY - 238]); ctx.fill();
        circ(ctx, '#fff1c8', CAFE.x + lx, GY - 218, 5);
        Art.glow(ctx, CAFE.x + lx, GY - 210, 120, '#ffd38a', 0.3);
      }
      for (let i = 0; i < 3; i++) {
        const ph = U.fract(t * 0.45 + i / 3);
        ctx.strokeStyle = U.rgba('#ffffff', 0.5 * Math.sin(ph * Math.PI)); ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.moveTo(CAFE.x + 453, GY - 144 - ph * 30); ctx.quadraticCurveTo(CAFE.x + 458 + Math.sin(t * 3 + i) * 5, GY - 154 - ph * 30, CAFE.x + 453, GY - 164 - ph * 30); ctx.stroke();
      }
      const b = O.barista;
      const typing = t > 4.0 && t < 4.38 ? Math.sin(t * 22) * 2 : 0;
      const hb = local(b, 34, -176 + typing), hb2 = local(b, 26, -172);
      const r0 = local(b, 18, -124), r1 = local(b, -8, -120);
      A.barista = Art.person(ctx, Object.assign({}, b, {
        reachF: { x: lerp(r0.x, hb.x, b.phone), y: lerp(r0.y, hb.y, b.phone) },
        reachB: { x: lerp(r1.x, hb2.x, b.phone), y: lerp(r1.y, hb2.y, b.phone) },
        holdF: b.phone > 0.05 ? TK.phone(b.phoneGlow) : undefined,
      }));
      layerImg(ctx, 'cafeF', cafeFront, CAFE.x);
      A.h3 = Art.person(ctx, O.h3);
    }
    // ---- granny
    if (vis(GRAN.x - 80, GRAN.x + GRAN.w + 80)) {
      layerImg(ctx, 'granB', grannyBack, GRAN.x);
      Art.glow(ctx, GRAN.x + 46, GY - 206, 110, '#ffcf86', 0.35);
      for (let i = 0; i < 5; i++) { const ph = U.fract(t * 0.22 + i / 5); circ(ctx, U.rgba('#f4f1ec', 0.42 * (1 - ph)), GRAN.x + 277 + Math.sin(ph * 4 + t) * 10 + ph * 40, GY - 470 - ph * 140, 10 + ph * 22); }
      const gr = O.granny;
      const rest = local(gr, 32, -128), show = local(gr, 64, -150);
      A.granny = Art.person(ctx, Object.assign({}, gr, {
        reachF: { x: lerp(rest.x, show.x, gr.show), y: lerp(rest.y, show.y, gr.show) },
        reachB: local(gr, 22, -122),
        holdF: TK.phone(gr.phoneGlow, { rot: lerp(-0.3, -1.1, gr.show) }),
      }));
      layerImg(ctx, 'granF', grannyFront, GRAN.x);
      const ears = U.fade(t, T.hopA[1], T.hopA[1] + 1.2, 0.08, 0.5);
      cat(ctx, GRAN.x + 300, GY - 20, 0.86, t, { ears, eyes: t > 5.35 && t < 7.6 ? 'flat' : 'open', flick: (t > T.hopA[1] && t < T.hopA[1] + 0.4 ? Math.sin((t - T.hopA[1]) * 20) * 0.6 : 0) + (t > 5.8 && t < 7.1 ? Math.sin((t - 5.8) * 9) * 0.35 : 0) });
    }
    // ---- the teen's house
    if (vis(TEEN.x - 80, TEEN.x + TEEN.w + 80)) {
      layerImg(ctx, 'teenB', teenBack, TEEN.x);
      for (let i = 0; i <= 12; i++) {
        const lx = TEEN.x + 11 + i * 31, ly = GY - 469;
        circ(ctx, ['#ffd36b', '#ff8db0', '#8fe3a9', '#9ad0ff'][i % 4], lx, ly, 3.5);
        Art.glow(ctx, lx, ly, 16, '#ffe6a8', 0.35 * (0.6 + 0.4 * Math.sin(t * 2.2 + i * 1.7)));
      }
      const d = O.dad;
      const drop = 64 * d.peek;
      A.dad = Art.person(ctx, Object.assign({}, d, { reachF: local(d, 50, -150 + drop), reachB: local(d, 14, -150 + drop) }));
      // the newspaper, held up in front of his face (drops to let him peek over it)
      const np = local(d, 30, -200 + drop);
      const S = d.s * L.dad.height;
      ctx.save();
      ctx.translate(np.x, np.y);
      ctx.rotate(-0.05 + d.peek * 0.04);
      ctx.scale(S, S);
      rrect(ctx, '#f1ece2', -42, -54, 84, 104, 3);
      rect(ctx, '#ddd6c8', -2, -54, 4, 104);
      ctx.fillStyle = 'rgba(60,55,50,0.6)';
      ctx.fillRect(-34, -44, 30, 8); ctx.fillRect(6, -44, 28, 8);
      for (let i = 0; i < 7; i++) { ctx.fillRect(-34, -28 + i * 9, 18 + (i % 3) * 5, 3); ctx.fillRect(8, -28 + i * 9, 14 + ((i + 1) % 3) * 6, 3); }
      ctx.fillRect(-14, -28, 10, 18);
      ctx.restore();
      const te = O.teen;
      const tp = local(te, 46, -118);
      A.teen = Art.person(ctx, Object.assign({}, te, { reachF: tp, reachB: local(te, 36, -112), holdF: TK.phone(te.phoneGlow, { rot: -0.5 }) }));
      layerImg(ctx, 'teenF', teenFront, TEEN.x);
      const dp = { x: TEEN.x + 316, y: GY - 112 };
      rrect(ctx, '#1d2027', dp.x - 9, dp.y - 3, 18, 5, 2);
      const dg = U.bump(t, T.fan[0] + 0.5, 0.3);
      if (dg > 0.02) Art.glow(ctx, dp.x, dp.y - 2, 40, '#a9d8ff', dg * 0.7);
      A.dadPhone = scr(dp);
    }
    // ---- the square
    if (vis(1400, 2600)) {
      layerImg(ctx, 'sqB', squareBack, 1480);
      layerImg(ctx, 'hallB', hallBack, 2170);
      ctx.save();
      ctx.translate(1560, GY - 74);
      ctx.rotate(U.wind(t, 1560, 2) * 0.012);
      bigTree(ctx);
      ctx.restore();
      TK.lamp(ctx, 2100, GY + 8, 0.92, {});
      rect(ctx, '#2d3836', 1846, GY - 32, 6, 48); rect(ctx, '#2d3836', 2010, GY - 32, 6, 48);
      rrect(ctx, '#9c6a48', 1836, GY - 40, 190, 10, 3);
      rrect(ctx, '#9c6a48', 1836, GY - 94, 190, 9, 3); rrect(ctx, '#9c6a48', 1836, GY - 76, 190, 9, 3);
      rect(ctx, '#2d3836', 1848, GY - 96, 4, 58); rect(ctx, '#2d3836', 2012, GY - 96, 4, 58);
      const h4 = O.h4;
      const rest4 = local(h4, 32, -128), show4 = local(h4, 66, -166);
      A.h1 = Art.person(ctx, O.h1);
      A.h4 = Art.person(ctx, Object.assign({}, h4, {
        reachF: { x: lerp(rest4.x, show4.x, h4.show), y: lerp(rest4.y, show4.y, h4.show) },
        reachB: local(h4, 26, -124),
        holdF: TK.phone(h4.phoneGlow, { rot: lerp(-0.3, -1.3, h4.show) }),
      }));
      A.h2 = Art.person(ctx, O.h2);
    }
    ctx.restore(); // main layer
    ctx.restore(); // tilt

    // ---- gossip, in screen space ----
    for (const k of Object.keys(A)) if (A[k] && A[k].head) A[k] = { mouth: scr(A[k].mouth), top: scr(A[k].top), head: scr(A[k].head), handF: scr(A[k].handF) };
    const phoneOf = (k, dx = 0, dy = -12) => (A[k] ? { x: A[k].handF.x + dx, y: A[k].handF.y + dy } : null);
    if (A.h3) {
      const a = U.fade(t, T.tell[0] + 0.15, T.tell[1], 0.15, 0.3);
      const p = U.prog(t, T.tell[0] + 0.15, T.tell[0] + 0.55);
      TK.iconBubble(ctx, A.h3.top.x + 52, A.h3.top.y - 62, 42, 'grin', { sc: U.E.outBack(p), alpha: a, t, tail: 2.2 });
    }
    if (A.barista) gossip(ctx, t, T.b1[0], T.b1[1], '…a FLOWER?', 'flower', { x: A.barista.top.x + 70, y: A.barista.top.y - 80, tx: A.barista.mouth.x + 2, ty: A.barista.mouth.y - 20 });
    TK.hop(ctx, t, T.hopA[0], T.hopA[1], phoneOf('barista'), phoneOf('granny'), 'flower', { arc: 200, r: 28 });
    if (A.granny) gossip(ctx, t, T.b2[0], T.b2[1], 'smiling like a lunatic', 'grin', { x: A.granny.top.x + 60, y: A.granny.top.y - 96, tx: A.granny.mouth.x + 6, ty: A.granny.mouth.y - 18 });
    TK.hop(ctx, t, T.hopB[0], T.hopB[1], phoneOf('granny'), phoneOf('teen'), 'grin', { arc: 190, r: 28 });
    if (A.teen) gossip(ctx, t, T.b3[0], T.b3[1], 'must be some flower', 'flower', { x: A.teen.top.x + 90, y: A.teen.top.y - 86, tx: A.teen.mouth.x + 6, ty: A.teen.mouth.y - 18 });
    if (A.teen && t > T.fan[0] - 0.1 && t < T.fan[1] + 0.6) {
      FAN.forEach((wn, i) => {
        const s = TK.toScreenL(hl, wn.x, wn.y);
        const t0 = T.fan[0] + i * 0.12;
        TK.hop(ctx, t, t0, t0 + 0.42, phoneOf('teen'), { x: s.x, y: s.y + tilt }, i % 2 ? 'grin' : 'flower', { r: 20, arc: 120 + i * 20, pingAlpha: 0.8 });
      });
      if (A.dadPhone) TK.hop(ctx, t, T.fan[0] + 0.05, T.fan[0] + 0.5, phoneOf('teen'), A.dadPhone, 'flower', { r: 20, arc: -60 });
    }
    TK.hop(ctx, t, T.hopC[0], T.hopC[1], phoneOf('teen'), phoneOf('h4', 6, -16), 'grin', { arc: 240, r: 28 });
    if (A.h2) {
      const tops = [A.h2.top.y, A.h1 ? A.h1.top.y : 1e9, A.h4 ? A.h4.top.y : 1e9];
      gossip(ctx, t, T.b4[0], T.b4[1], 'where do we get one?', 'flower', { x: A.h2.top.x + 40, y: Math.min(...tops) - 76, tx: A.h2.mouth.x + 6, ty: A.h2.mouth.y - 16 });
    }
  }

  /* ---------------- shop street set ---------------- */
  const SHOPREST = { x: 40, y: GY - 365, z: 1 };
  function shopCam(t) {
    const k = U.ease(t, T.push[0], T.push[1] + 0.8, 'inOutSine');
    return { x: lerp(40, 20, k), y: lerp(GY - 365, GY - 226, k), z: lerp(1, 1.62, k) };
  }
  const STREET = TK.townStrip('street10', {
    seed: 2020, bottom: 980, ground: ['#a3b49a', '#93a88b'],
    tiers: [
      { x0: -900, x1: 2900, y: (x) => 600 - 16 * Math.sin(x * 0.002 + 0.5) - x * 0.02, wMin: 40, wMax: 66, hMin: 30, hMax: 50, gapMin: 16, gapMax: 80, treeK: 0.7 },
      { x0: -900, x1: 2900, y: (x) => 668 - 14 * Math.sin(x * 0.003 + 1.7) - x * 0.015, wMin: 56, wMax: 96, hMin: 40, hMax: 74, gapMin: 12, gapMax: 60, treeK: 0.9 },
    ],
  });
  const LOTROW = TK.townStrip('lotrow10', {
    seed: 3030, bottom: 980, ground: ['#9fb090'],
    walls: ['#efe0c4', '#e9c9a0', '#cfdde2', '#f0cfc0', '#e8dcc6', '#d6e2c4'],
    tiers: [{ x0: 1150, x1: 3300, y: () => 846, wMin: 120, wMax: 190, hMin: 110, hMax: 190, gapMin: 20, gapMax: 90, treeK: 1.8 }],
  });
  function neighbourA(g) {
    // pale blue house, local x 0..368 (attached to the shop's left wall)
    const w = 368;
    rect(g, '#bcd2de', 0, -600, w, 600);
    rect(g, '#f3ead9', -8, -612, w + 8, 16); rect(g, '#d9e6ee', 0, -596, w, 6);
    for (const wx of [80, 270]) {
      rect(g, '#f3ead9', wx - 48, -540, 96, 150); rect(g, '#5f7389', wx - 40, -532, 80, 134); rect(g, '#f3ead9', wx - 2, -532, 4, 134);
      rrect(g, '#7a5236', wx - 52, -388, 104, 18, 3);
      for (let i = 0; i < 6; i++) circ(g, i % 2 ? '#e5484d' : '#f48fb1', wx - 42 + i * 17, -392 - U.hash(i, wx) * 6, 6.5);
    }
    rect(g, '#f3ead9', 40, -300, 96, 150); rect(g, '#5f7389', 48, -292, 80, 134); rect(g, '#f3ead9', 86, -292, 4, 134);
    rect(g, '#f3ead9', 220, -276, 104, 276); rrect(g, '#a33d3a', 230, -266, 84, 266, 4); circ(g, '#cda24c', 302, -130, 5);
    rect(g, '#d9ccb5', 0, -26, 220, 26);
    // bicycle leaning on the wall
    g.strokeStyle = '#c4553b'; g.lineWidth = 5; g.lineCap = 'round';
    for (const wx of [60, 176]) { g.beginPath(); g.arc(wx, -38, 34, 0, TAU); g.stroke(); }
    g.beginPath(); g.moveTo(60, -38); g.lineTo(104, -92); g.lineTo(162, -92); g.lineTo(176, -38); g.moveTo(104, -92); g.lineTo(118, -38); g.lineTo(162, -92); g.moveTo(104, -92); g.lineTo(100, -108); g.stroke();
    g.strokeStyle = '#2a2421'; g.beginPath(); g.moveTo(162, -92); g.lineTo(166, -112); g.lineTo(182, -114); g.stroke();
    rrect(g, '#2a2421', 86, -114, 30, 8, 3);
  }
  function neighbourB(g) {
    // ochre gabled house, local x 0..340
    const w = 340;
    rect(g, '#e9c98e', 0, -560, w, 560);
    g.fillStyle = '#7d4b3e'; poly(g, [-24, -552, w / 2, -700, w + 24, -552]); g.fill();
    g.strokeStyle = '#f3ead9'; g.lineWidth = 5; g.beginPath(); g.moveTo(-18, -554); g.lineTo(w / 2, -694); g.lineTo(w + 18, -554); g.stroke();
    for (const [wx, wy] of [[90, -470], [250, -470], [90, -260], [250, -260]]) { rect(g, '#f3ead9', wx - 42, wy - 66, 84, 132); rect(g, '#5f7389', wx - 34, wy - 58, 68, 116); rect(g, '#f3ead9', wx - 2, wy - 58, 4, 116); rect(g, '#4f7a5a', wx - 66, wy - 62, 20, 124); rect(g, '#4f7a5a', wx + 46, wy - 62, 20, 124); }
    rect(g, '#d9ccb5', 0, -26, w, 26);
  }
  function lotEdge(g) {
    // local x 0..1100, the parking lot beside the shop
    rect(g, '#8e8a86', 0, -64, 1100, 64);
    g.strokeStyle = 'rgba(255,255,255,0.75)'; g.lineWidth = 4;
    for (let i = 0; i < 9; i++) { const x = 110 + i * 120; g.beginPath(); g.moveTo(x, -60); g.lineTo(x - 30, -2); g.stroke(); }
    rrect(g, '#b8ad9e', 380, -46, 720, 46, 4); rect(g, '#cfc5b6', 380, -50, 720, 8);
    rect(g, '#5e6a70', 112, -330, 7, 330);
    rrect(g, '#2f6fb3', 78, -404, 76, 76, 8);
    g.save(); g.font = Art.font(60, 'sans', 900); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#ffffff'; g.fillText('P', 116, -364); g.restore();
  }
  function compactCar(g, x, y, s, col) {
    g.save();
    g.translate(x, y);
    g.scale(s, s);
    ell(g, 'rgba(20,20,30,0.25)', 0, 0, 130, 10);
    rrect(g, col, -124, -74, 248, 58, 24); rrect(g, col, -72, -118, 144, 56, 26);
    rrect(g, '#a9cde0', -60, -110, 56, 40, 10); rrect(g, '#a9cde0', 6, -110, 56, 40, 10);
    rect(g, U.shade(col, -0.2), -2, -110, 6, 92);
    rrect(g, '#ffe7a8', 104, -64, 18, 12, 4); rrect(g, '#e8574a', -122, -64, 14, 12, 4);
    for (const wx of [-72, 72]) { circ(g, '#2a2421', wx, -14, 27); circ(g, '#c9ccd1', wx, -14, 11); }
    g.restore();
  }
  function drawShopStreet(ctx, t, P, tilt) {
    const cam = shopCam(t);
    ctx.save();
    ctx.translate(0, tilt);
    ctx.save();
    Art.cam(ctx, TK.layer(cam, SHOPREST, 0.05, 960, 540));
    TK.backdrop(ctx, P, { t, y: 500, sx: 1320, sh: 330, sw: 580, glow: 0.42 });
    ctx.restore();
    ctx.save();
    Art.cam(ctx, TK.layer(cam, SHOPREST, 0.17, 960, 540));
    Art.ridge(ctx, { seed: 34, y: 668, amp: 70, freq: 0.0022, color: U.mix(P.trees[0], P.fog, 0.4), x0: -800, x1: W + 800, step: 14 });
    Art.forest(ctx, { seed: 43, y: 650, spacing: 38, hMin: 40, hMax: 78, color: U.mix(P.trees[0], P.fog, 0.36), light: U.mix(P.trees[0], P.light, 0.2) });
    ctx.restore();
    const l42 = TK.layer(cam, SHOPREST, 0.42, 960, 540), l62 = TK.layer(cam, SHOPREST, 0.62, 960, 540);
    ctx.save();
    Art.cam(ctx, l42);
    TK.drawStrip(ctx, STREET, 'street10', Object.assign({ vx0: l42.x - W / 2 / l42.zoom, vx1: l42.x + W / 2 / l42.zoom }, HILL_HAZE));
    ctx.restore();
    ctx.save();
    Art.cam(ctx, l62);
    TK.drawStrip(ctx, LOTROW, 'lotrow10', { haze: [0.12], hazeC: P0.fog, vx0: l62.x - W / 2 / l62.zoom, vx1: l62.x + W / 2 / l62.zoom });
    ctx.restore();
    // main street layer
    ctx.save();
    Art.cam(ctx, { x: cam.x, y: cam.y, zoom: cam.z });
    rect(ctx, '#d5cbbd', -1400, GY, 4000, 30);
    rect(ctx, 'rgba(255,255,255,0.35)', -1400, GY, 4000, 3);
    ctx.strokeStyle = 'rgba(90,70,60,0.25)'; ctx.lineWidth = 1.5;
    for (let x = -1400; x < 2600; x += 60) { ctx.beginPath(); ctx.moveTo(x, GY + 3); ctx.lineTo(x - 4, GY + 30); ctx.stroke(); }
    rect(ctx, '#a99e90', -1400, GY + 30, 4000, 8);
    rect(ctx, '#8f877d', -1400, GY + 38, 4000, 400);
    layerImg(ctx, 'lotEdge', lotEdge, 192);
    compactCar(ctx, 900, GY - 30, 0.82, '#c0453a');
    layerImg(ctx, 'nbB', neighbourB, -900);
    layerImg(ctx, 'nbA', neighbourA, -560);
    TK.lamp(ctx, 640, GY + 10, 1.0, {});
    TK.shopfront(ctx, 0, GY, 0.64, t, { lit: 0.6, wind: 1 });
    for (let i = 0; i < 3; i++) {
      const bx = -150 + i * 64, by = GY + 8;
      for (let j = 0; j < 5; j++) {
        const fx = bx + (j - 2) * 7 + Math.sin(t * 1.3 + i + j) * 1.5, fh = 60 + U.hash(j, i) * 26;
        ctx.strokeStyle = '#4f8f4c'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(bx, by - 30); ctx.lineTo(fx, by - fh); ctx.stroke();
        circ(ctx, ['#f48fb1', '#ffd36b', '#ffffff', '#ff8a5c', '#d98be6'][(i * 2 + j) % 5], fx, by - fh, 7);
      }
      ctx.fillStyle = '#aeb7bd'; poly(ctx, [bx - 22, by - 40, bx + 22, by - 40, bx + 18, by, bx - 18, by]); ctx.fill();
      rect(ctx, '#c9d1d6', bx - 23, by - 42, 46, 5);
    }
    ctx.restore();
    ctx.restore();
  }

  /* ---------------- the scene ---------------- */
  Film.scene({
    id: 'word-spreads',
    order: 10,
    title: 'Word Gets Around',
    chapter: 'Part Two · The Shop',
    duration: D,
    mood: 'town',
    fadeIn: 1.0,
    fadeOut: 0.8,
    sfx: [
      [0.4, 'bird', { gain: 0.5 }], [T.tell[0] + 0.15, 'pop', { gain: 0.35 }], [T.b1[0] + 0.02, 'pop', { gain: 0.3 }],
      [T.hopA[1], 'ding'], [T.hopB[1], 'ding'],
      [T.fan[0] + 0.42, 'ding', { gain: 0.5 }], [T.fan[0] + 0.54, 'ding', { gain: 0.42 }], [T.fan[0] + 0.66, 'ding', { gain: 0.36 }], [T.fan[0] + 0.78, 'ding', { gain: 0.3 }], [T.fan[0] + 0.9, 'ding', { gain: 0.26 }],
      [T.hopC[1], 'ding'], [T.tiltUp[0] + 0.1, 'whoosh', { gain: 0.5 }], [T.lapse[0] + 0.05, 'clock', { gain: 0.6 }], [T.tiltDown[0] + 0.05, 'whoosh', { gain: 0.35 }], [T.tiltDown[1] + 0.15, 'bird', { gain: 0.4 }],
    ],
    post: { vignette: 0.3, grain: 0.04, letterbox: 1 },

    render(ctx, t) {
      const P = paletteAt(t);
      const tilt = tiltAt(t);
      drawSky(ctx, t, P, tilt);
      if (t < SWITCH) drawTown(ctx, t, P, tilt);
      else drawShopStreet(ctx, t, P, tilt);
      Art.captions(ctx, t, NARR);
    },
  });
})();
