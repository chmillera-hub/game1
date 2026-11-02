/* ==========================================================================
   art.js — the shared visual vocabulary of the film.
   Global: Art
   All coordinates are in film space: 1920 × 1080 (U.W × U.H).
   Everything draws procedurally and deterministically from its arguments.
   ========================================================================== */
(function (g) {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const Art = {};
  Art.W = W;
  Art.H = H;
  /** visible picture area when the cinemascope letterbox is fully on */
  Art.PIC = { top: 138, bottom: 942, h: 804, mid: 540 };

  /* ======================================================================
     FONTS
     ====================================================================== */
  Art.F = {
    serif: '"Cormorant Garamond", "Iowan Old Style", "Palatino Linotype", Georgia, serif',
    sans: '"Nunito", "Trebuchet MS", "Segoe UI", system-ui, sans-serif',
    hand: '"Caveat", "Segoe Print", "Bradley Hand", "Comic Sans MS", cursive',
  };
  /** Art.font(48, 'serif', 500, 'italic') → CSS font string */
  Art.font = (size, fam = 'sans', weight = 700, style = 'normal') =>
    `${style} ${weight} ${Math.round(size * 10) / 10}px ${Art.F[fam] || fam}`;

  /* ======================================================================
     OFFSCREEN HELPERS
     ====================================================================== */
  const canvases = new Map();
  /** cached offscreen canvas by key */
  Art.canvas = (key, w, h) => {
    let c = canvases.get(key);
    if (!c) {
      c = document.createElement('canvas');
      canvases.set(key, c);
    }
    w = Math.max(1, Math.ceil(w)); h = Math.max(1, Math.ceil(h));
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; c._gen = (c._gen || 0) + 1; }
    return c;
  };
  /** base transform (film space → backing pixels); set by the engine each frame */
  Art._base = null;
  /**
   * Draw something blurred (depth of field). amount ≈ blur radius in film px.
   * drawFn(ctx2) draws in the SAME coordinate space you are in when calling.
   * Works under any camera transform. Cheap: renders at reduced resolution.
   */
  Art.blurred = (ctx, amount, drawFn, key = 'blur') => {
    if (amount < 0.6) { drawFn(ctx); return; }
    const f = clamp(amount * 0.55, 1.5, 14);
    const base = Art._base || new DOMMatrix();
    const cur = ctx.getTransform();
    const rel = base.inverse().multiply(cur);
    const c = Art.canvas(key + ':' + Math.round(f * 4), W / f, H / f);
    const c2 = c.getContext('2d');
    c2.setTransform(1, 0, 0, 1, 0, 0);
    c2.clearRect(0, 0, c.width, c.height);
    c2.setTransform(new DOMMatrix().scale(1 / f, 1 / f).multiply(rel));
    c2.globalAlpha = 1;
    c2.globalCompositeOperation = 'source-over';
    drawFn(c2);
    ctx.save();
    ctx.setTransform(base);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(c, 0, 0, W, H);
    ctx.restore();
  };
  /** run fn with alpha multiplied */
  Art.withAlpha = (ctx, a, fn) => {
    if (a <= 0.001) return;
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    fn(ctx);
    ctx.restore();
  };
  /** camera: call inside save/restore. focus point (x,y) lands at screen center. */
  Art.cam = (ctx, { x = W / 2, y = H / 2, zoom = 1, rot = 0, sx = W / 2, sy = H / 2 } = {}) => {
    ctx.translate(sx, sy);
    ctx.scale(zoom, zoom);
    if (rot) ctx.rotate(rot);
    ctx.translate(-x, -y);
  };
  /** handheld camera drift / shake offset {x,y} */
  Art.shake = (t, amt = 1, seed = 0) => Art.reducedMotion ? { x: 0, y: 0 } : ({
    x: (U.noise1(t * 0.6, seed) * 6 + U.noise1(t * 7, seed + 3) * 1.2 * amt) * amt,
    y: (U.noise1(t * 0.5, seed + 9) * 4 + U.noise1(t * 7.5, seed + 5) * 1.2 * amt) * amt,
  });

  /* ======================================================================
     PALETTES — time of day. Every environment color comes from one of these
     so scenes stay consistent. Use U.mixDeep(Art.TOD.a, Art.TOD.b, k) to blend.
     ====================================================================== */
  Art.TOD = {
    dawn: {
      sky: ['#151b36', '#4b4878', '#e39b86'], sun: '#ffd7ab', haze: '#c9a3b2',
      far: '#6b6690', mid: '#4d5376', summit: '#8f8fb3', snow: '#e9e4f2',
      trees: ['#4f5c78', '#36435a', '#232e3e'], ground: '#28352e', ground2: '#18211c',
      trail: '#5a5250', grass: '#3d5446', light: '#ffc79c', fog: '#b9a2bd',
    },
    morning: {
      sky: ['#6aa3d4', '#a8d1e6', '#f1e8cf'], sun: '#fff3d4', haze: '#e3ede4',
      far: '#9cb4c4', mid: '#7f9cab', summit: '#aebfcf', snow: '#f7f9fc',
      trees: ['#7c9e98', '#517c69', '#2d5545'], ground: '#43693c', ground2: '#2c4a2b',
      trail: '#a78962', grass: '#679a4c', light: '#fff0c4', fog: '#e8f0e8',
    },
    golden: {
      sky: ['#557eb3', '#e3b78c', '#ffd497'], sun: '#ffe1a3', haze: '#f3d2a8',
      far: '#a490a8', mid: '#827c98', summit: '#c7a9b3', snow: '#fff0e0',
      trees: ['#7f8b7a', '#566a4f', '#33473a'], ground: '#4d6a39', ground2: '#334826',
      trail: '#b68c5d', grass: '#8c9d4b', light: '#ffcf86', fog: '#f5ddb7',
    },
    dusk: {
      sky: ['#221c46', '#8b4a77', '#ef8f62'], sun: '#ffb378', haze: '#c97a85',
      far: '#5e4a70', mid: '#46395b', summit: '#d98c96', snow: '#ffd6cf',
      trees: ['#4a3f5d', '#342e48', '#211e33'], ground: '#2a2a3b', ground2: '#1b1b29',
      trail: '#6b5662', grass: '#3d4a47', light: '#ff9f70', fog: '#9c6b85',
    },
    night: {
      sky: ['#050814', '#0e1632', '#21305a'], sun: '#dfe8ff', haze: '#26355e',
      far: '#1b2443', mid: '#141b34', summit: '#2b3963', snow: '#93a6d6',
      trees: ['#152039', '#0f162a', '#080d1a'], ground: '#0c1222', ground2: '#070b16',
      trail: '#262b40', grass: '#16233a', light: '#9db6ff', fog: '#1c2a4f',
    },
  };
  /** desaturate every color in a palette by amt (0..1) */
  Art.desatPalette = (P, amt) => {
    const f = (v) => (typeof v === 'string' ? U.desat(v, amt) : Array.isArray(v) ? v.map(f) : v);
    const o = {};
    for (const k of Object.keys(P)) o[k] = f(P[k]);
    return o;
  };

  /* ======================================================================
     SKY, SUN, STARS, CLOUDS
     ====================================================================== */
  /** full-frame vertical gradient sky. P = palette. opts.horizon = y of the lightest band */
  Art.sky = (ctx, P, { horizon = 760 } = {}) => {
    const gr = ctx.createLinearGradient(0, 0, 0, horizon);
    gr.addColorStop(0, P.sky[0]);
    gr.addColorStop(0.55, P.sky[1]);
    gr.addColorStop(1, P.sky[2]);
    ctx.fillStyle = gr;
    ctx.fillRect(-W, -H, W * 3, horizon + H);
    ctx.fillStyle = P.sky[2];
    ctx.fillRect(-W, horizon - 1, W * 3, H * 2);
  };
  /** sun / moon disc with soft halo */
  Art.sun = (ctx, x, y, r, color, a = 1) => {
    Art.glow(ctx, x, y, r * 9, color, 0.45 * a, 'screen');
    Art.glow(ctx, x, y, r * 3, color, 0.75 * a, 'screen');
    const core = U.mix(color, '#ffffff', 0.8);
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.fillStyle = core;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.restore();
    Art.glow(ctx, x, y, r * 1.7, core, 0.55 * a, 'screen');
  };
  /** twinkling star field */
  Art.stars = (ctx, { seed = 1, count = 220, t = 0, alpha = 1, y0 = 0, y1 = 700, x0 = 0, x1 = W, color = '#ffffff' } = {}) => {
    if (alpha <= 0) return;
    ctx.save();
    ctx.fillStyle = color;
    for (let i = 0; i < count; i++) {
      const x = x0 + U.hash(i, seed) * (x1 - x0);
      const y = y0 + Math.pow(U.hash(i, seed + 1), 1.4) * (y1 - y0);
      const m = U.hash(i, seed + 2);
      const tw = 0.55 + 0.45 * Math.sin(t * (0.8 + m * 2.5) + i);
      const r = 0.6 + m * m * 2.0;
      ctx.globalAlpha = alpha * tw * (0.35 + 0.65 * m);
      ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
      if (m > 0.93) {
        ctx.globalAlpha = alpha * tw * 0.5;
        ctx.fillRect(x - r * 4, y - 0.5, r * 8, 1);
        ctx.fillRect(x - 0.5, y - r * 4, 1, r * 8);
      }
    }
    ctx.restore();
  };
  /** soft drifting clouds. offset scrolls them (use small parallax). */
  Art.clouds = (ctx, { seed = 1, count = 6, y0 = 120, y1 = 360, offset = 0, color = '#ffffff', alpha = 0.6, scale = 1, shade = null, bg = null } = {}) => {
    const span = W + 900;
    for (let i = 0; i < count; i++) {
      const bx = U.hash(i, seed) * span;
      const x = ((((bx - offset) % span) + span) % span) - 450;
      const y = lerp(y0, y1, U.hash(i, seed + 1));
      const s = scale * (0.6 + U.hash(i, seed + 2) * 0.8);
      Art.cloud(ctx, x, y, s, color, alpha * (0.6 + 0.4 * U.hash(i, seed + 3)), i + seed * 13, shade, bg);
    }
  };
  Art.cloud = (ctx, x, y, s, color, a, seed = 0, shade = null, bg = null) => {
    ctx.save();
    let under = shade || U.shade(color, -0.12);
    if (bg) { color = U.mix(bg, color, a); under = U.mix(bg, under, a); } else ctx.globalAlpha *= a;
    const n = 6;
    // base (shadowed) lobes then lit lobes
    for (let pass = 0; pass < 2; pass++) {
      ctx.fillStyle = pass === 0 ? under : color;
      ctx.beginPath();
      for (let i = 0; i < n; i++) {
        const k = i / (n - 1);
        const px = x + (k - 0.5) * 300 * s;
        const r = (34 + 40 * Math.sin(k * Math.PI) + U.hash(i, seed) * 18) * s;
        const py = y - Math.sin(k * Math.PI) * 26 * s - (pass ? 6 * s : 0);
        ctx.moveTo(px + r, py);
        ctx.arc(px, py, r * (pass ? 0.92 : 1), 0, TAU);
      }
      ctx.fill();
    }
    ctx.restore();
  };

  /* ======================================================================
     TERRAIN: ridges, the summit, ground, trail
     ====================================================================== */
  /** a mountain ridge silhouette across the screen. offset scrolls (parallax). */
  Art.ridge = (ctx, { seed = 1, y = 620, amp = 160, freq = 0.0034, color = '#888', offset = 0, oct = 5, step = 8, x0 = -40, x1 = W + 40, sharp = 0.55, bottom = H + 200 } = {}) => {
    ctx.beginPath();
    ctx.moveTo(x0, bottom);
    for (let x = x0; x <= x1 + step; x += step) {
      const n = U.fbm1((x + offset) * freq, oct, seed);
      const ridged = 1 - Math.abs(n);
      const v = lerp(n * 0.5 + 0.5, ridged, sharp);
      ctx.lineTo(x, y - v * amp);
    }
    ctx.lineTo(x1 + step, bottom);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  };
  /** height of a ridge at x (same params as Art.ridge) — for placing things on it */
  Art.ridgeY = (x, { seed = 1, y = 620, amp = 160, freq = 0.0034, offset = 0, oct = 5, sharp = 0.55 } = {}) => {
    const n = U.fbm1((x + offset) * freq, oct, seed);
    return y - lerp(n * 0.5 + 0.5, 1 - Math.abs(n), sharp) * amp;
  };
  /**
   * THE SUMMIT — the distant peak everyone is hiking toward. A recognisable
   * motif: tall, snow-capped, with a faint promise-glow at its tip.
   * (x, y) = base center; h = height; P = palette.
   */
  Art.summit = (ctx, { x = 1450, y = 640, h = 420, w = 760, P = Art.TOD.morning, glow = 0.5, t = 0, seed = 5, flag = true, snow = 0.34, glowMode = 'lighter', flagColor = '#e8574a' } = {}) => {
    const tip = { x: x + w * 0.03, y: y - h };
    const L = { x: x - w / 2, y }, Rb = { x: x + w / 2, y };
    const N = 14;
    // jagged ridge lines from the tip down each side (u: 0 at tip → 1 at base)
    const side = (base, dir, u) => {
      const px = lerp(tip.x, base.x, u), py = lerp(tip.y, base.y, Math.pow(u, 0.85));
      const j = u > 0 && u < 1 ? (U.hash(Math.round(u * N), seed + dir) - 0.5) * 30 * Math.sin(u * Math.PI) : 0;
      return { x: px + j * 0.4 * dir, y: py + j };
    };
    const left = [], right = [];
    for (let i = 0; i <= N; i++) { left.push(side(L, -1, i / N)); right.push(side(Rb, 1, i / N)); }
    ctx.beginPath();
    ctx.moveTo(L.x, y + 300);
    for (let i = N; i >= 0; i--) ctx.lineTo(left[i].x, left[i].y);
    for (let i = 1; i <= N; i++) ctx.lineTo(right[i].x, right[i].y);
    ctx.lineTo(Rb.x, y + 300);
    ctx.closePath();
    ctx.fillStyle = P.summit;
    ctx.fill();
    // lit face (right of a crease running down from the tip)
    ctx.beginPath();
    ctx.moveTo(tip.x, tip.y);
    for (let i = 1; i <= N; i++) ctx.lineTo(right[i].x, right[i].y);
    ctx.lineTo(Rb.x, y + 300);
    ctx.lineTo(tip.x + w * 0.08, y + 300);
    for (let i = 6; i >= 1; i--) { const k = i / 6; ctx.lineTo(tip.x + w * 0.08 * k + Math.sin(k * 7 + seed) * 10 * k, lerp(tip.y, y, k)); }
    ctx.closePath();
    ctx.fillStyle = U.shade(P.summit, 0.14);
    ctx.fill();
    // snow cap: down both ridges to the snow line, zig-zag edge between
    const sN = Math.max(2, Math.round(N * snow));
    ctx.beginPath();
    ctx.moveTo(tip.x, tip.y);
    for (let i = 1; i <= sN; i++) ctx.lineTo(right[i].x, right[i].y);
    const a = right[sN], b = left[sN];
    const Z = 9;
    for (let j = 1; j < Z; j++) {
      const k = j / Z;
      const zx = lerp(a.x, b.x, k), zy = lerp(a.y, b.y, k);
      ctx.lineTo(zx, zy + (j % 2 ? 26 + U.hash(j, seed + 7) * 34 : -6 + U.hash(j, seed + 9) * 10));
    }
    for (let i = sN; i >= 1; i--) ctx.lineTo(left[i].x, left[i].y);
    ctx.closePath();
    ctx.fillStyle = P.snow;
    ctx.fill();
    // snow shadow on the dark face
    ctx.save();
    ctx.clip();
    ctx.fillStyle = U.rgba(P.summit, 0.28);
    ctx.beginPath();
    ctx.moveTo(tip.x, tip.y);
    ctx.lineTo(tip.x + w * 0.05, y);
    ctx.lineTo(L.x, y);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
    // promise-glow at the tip
    if (glow > 0) Art.glow(ctx, tip.x, tip.y + 6, 120, P.light, glow * (0.55 + 0.15 * Math.sin(t * 1.4)), glowMode);
    if (flag) {
      ctx.strokeStyle = U.shade(P.summit, -0.45);
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(tip.x, tip.y + 2); ctx.lineTo(tip.x, tip.y - 26); ctx.stroke();
      const fl = Math.sin(t * 3) * 3;
      ctx.fillStyle = flagColor;
      ctx.beginPath(); ctx.moveTo(tip.x, tip.y - 26); ctx.lineTo(tip.x + 16, tip.y - 21 + fl); ctx.lineTo(tip.x, tip.y - 16); ctx.closePath(); ctx.fill();
    }
    return { x: tip.x, y: tip.y };
  };
  /** y of a gently rolling ground line at screen x */
  Art.groundY = (x, { y = 860, amp = 22, freq = 0.0016, offset = 0, seed = 3 } = {}) =>
    y + U.fbm1((x + offset) * freq, 3, seed) * amp;
  /** fill ground from the rolling line down. */
  Art.ground = (ctx, { y = 860, amp = 22, freq = 0.0016, offset = 0, seed = 3, color = '#43693c', color2 = '#2c4a2b', step = 12 } = {}) => {
    const o = { y, amp, freq, offset, seed };
    ctx.beginPath();
    ctx.moveTo(-40, H + 400);
    for (let x = -40; x <= W + 40; x += step) ctx.lineTo(x, Art.groundY(x, o));
    ctx.lineTo(W + 40, H + 400);
    ctx.closePath();
    const gr = ctx.createLinearGradient(0, y - amp, 0, H);
    gr.addColorStop(0, color);
    gr.addColorStop(1, color2);
    ctx.fillStyle = gr;
    ctx.fill();
  };
  /** a packed-dirt trail band riding just below the ground line (side view) */
  Art.trail = (ctx, { y = 860, amp = 22, freq = 0.0016, offset = 0, seed = 3, color = '#a78962', depth = 46, stones = true } = {}) => {
    const o = { y, amp, freq, offset, seed };
    ctx.beginPath();
    for (let x = -40; x <= W + 40; x += 12) ctx.lineTo(x, Art.groundY(x, o) + 4);
    for (let x = W + 40; x >= -40; x -= 12) ctx.lineTo(x, Art.groundY(x, o) + depth + Math.sin((x + offset) * 0.01) * 6);
    ctx.closePath();
    const gr = ctx.createLinearGradient(0, y - amp, 0, y + depth + amp);
    gr.addColorStop(0, U.shade(color, 0.1));
    gr.addColorStop(1, U.shade(color, -0.18));
    ctx.fillStyle = gr;
    ctx.fill();
    if (stones) {
      const sp = 60, i0 = Math.floor((offset - 60) / sp), i1 = Math.ceil((offset + W + 60) / sp);
      for (let i = i0; i <= i1; i++) {
        if (U.hash(i, seed + 40) < 0.45) continue;
        const sx = i * sp + U.hash(i, seed + 41) * sp - offset;
        const gy = Art.groundY(sx, o);
        const sy = gy + 10 + U.hash(i, seed + 42) * (depth - 18);
        const r = 2 + U.hash(i, seed + 43) * 5;
        ctx.fillStyle = U.shade(color, -0.28 + U.hash(i, seed + 44) * 0.2);
        ctx.beginPath(); ctx.ellipse(sx, sy, r * 1.6, r, 0, 0, TAU); ctx.fill();
      }
    }
  };

  /* ======================================================================
     VEGETATION
     ====================================================================== */
  /** stylised pine. (x,y) = base of trunk. light = lit-side color (optional) */
  Art.pine = (ctx, x, y, h, col, { sway = 0, light = null, tiers = 4, w = 0.4 } = {}) => {
    const tw0 = h * w;
    ctx.fillStyle = U.shade(col, -0.3);
    ctx.fillRect(x - h * 0.022, y - h * 0.2, h * 0.044, h * 0.2 + 2);
    for (let i = 0; i < tiers; i++) {
      const k = tiers > 1 ? i / (tiers - 1) : 0;
      const by = y - h * 0.13 - k * h * 0.56;
      const tw = tw0 * (1 - k * 0.62);
      const th = h * 0.36 * (1 - k * 0.22);
      const sx = sway * (0.2 + k * 0.8);
      const ax = x + sx * 1.25, ay = by - th;
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.quadraticCurveTo(x + sx + tw * 0.16, by - th * 0.45, x + sx + tw * 0.5, by);
      ctx.quadraticCurveTo(x + sx, by - th * 0.14, x + sx - tw * 0.5, by);
      ctx.quadraticCurveTo(x + sx - tw * 0.16, by - th * 0.45, ax, ay);
      ctx.fillStyle = col;
      ctx.fill();
      if (light) {
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.quadraticCurveTo(x + sx + tw * 0.16, by - th * 0.45, x + sx + tw * 0.5, by);
        ctx.quadraticCurveTo(x + sx + tw * 0.22, by - th * 0.1, x + sx + tw * 0.04, by - th * 0.08);
        ctx.closePath();
        ctx.fillStyle = light;
        ctx.fill();
      }
    }
  };
  /** stylised round-canopy (deciduous) tree */
  Art.roundTree = (ctx, x, y, h, col, { sway = 0, light = null, seed = 0 } = {}) => {
    ctx.strokeStyle = U.shade(col, -0.35);
    ctx.lineCap = 'round';
    ctx.lineWidth = h * 0.05;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + sway * 0.2, y - h * 0.3, x + sway * 0.5, y - h * 0.55); ctx.stroke();
    const cx = x + sway * 0.7, cy = y - h * 0.68, R = h * 0.3;
    const lobes = 5;
    ctx.fillStyle = col;
    ctx.beginPath();
    for (let i = 0; i < lobes; i++) {
      const a = (i / lobes) * TAU + U.hash(i, seed) * 0.5;
      const r = R * (0.55 + U.hash(i, seed + 1) * 0.25);
      const px = cx + Math.cos(a) * R * 0.5, py = cy + Math.sin(a) * R * 0.42;
      ctx.moveTo(px + r, py); ctx.arc(px, py, r, 0, TAU);
    }
    ctx.fill();
    if (light) {
      ctx.fillStyle = light;
      ctx.beginPath();
      ctx.arc(cx + R * 0.3, cy - R * 0.25, R * 0.42, 0, TAU);
      ctx.fill();
    }
  };
  /**
   * A band of trees spanning the screen. offset scrolls the band (parallax:
   * pass worldX * depthFactor). Deterministic per tree index.
   */
  Art.forest = (ctx, { seed = 1, y = 760, offset = 0, spacing = 110, hMin = 220, hMax = 380, color = '#2d5545', light = null, kind = 'pine', sway = 0, t = 0, jitterY = 24, varC = 0.06, w = 0.4 } = {}) => {
    const i0 = Math.floor((offset - 400) / spacing), i1 = Math.ceil((offset + W + 400) / spacing);
    for (let i = i0; i <= i1; i++) {
      const r1 = U.hash(i, seed), r2 = U.hash(i, seed + 1), r3 = U.hash(i, seed + 2);
      const x = i * spacing + (r2 - 0.5) * spacing * 0.9 - offset;
      if (x < -300 || x > W + 300) continue;
      const h = lerp(hMin, hMax, r1);
      const c = varC ? U.shade(color, (r3 - 0.5) * varC * 2) : color;
      const sw = sway ? sway * U.wind(t, x + offset, i) : 0;
      const yy = y + (r3 - 0.5) * jitterY;
      if (kind === 'round' || (kind === 'mix' && r3 < 0.32)) Art.roundTree(ctx, x, yy, h * 0.85, c, { sway: sw, light, seed: i });
      else Art.pine(ctx, x, yy, h, c, { sway: sw, light, w: w * (0.85 + r2 * 0.3) });
    }
  };
  /** grass blades along a baseline. y may be a number or fn(x) → y */
  Art.grass = (ctx, { seed = 1, y = 860, offset = 0, spacing = 7, h = 26, hVar = 0.6, color = '#679a4c', color2 = null, t = 0, wind = 1, x0 = -20, x1 = W + 20, width = 2.6 } = {}) => {
    const yf = typeof y === 'function' ? y : () => y;
    const i0 = Math.floor((offset + x0) / spacing), i1 = Math.ceil((offset + x1) / spacing);
    const c2 = color2 || U.shade(color, 0.18);
    for (let pass = 0; pass < 2; pass++) {
      ctx.fillStyle = pass ? c2 : color;
      ctx.beginPath();
      for (let i = i0; i <= i1; i++) {
        if ((U.hash(i, seed + 7) < 0.5) !== !!pass) continue;
        const x = i * spacing + (U.hash(i, seed) - 0.5) * spacing * 1.6 - offset;
        const by = yf(x) + 2;
        const hh = h * (1 - hVar / 2 + U.hash(i, seed + 1) * hVar);
        const sw = (U.wind(t, x + offset, seed) * 0.6 + (U.hash(i, seed + 2) - 0.5) * 0.8) * hh * 0.45 * wind;
        const wd = width * (0.7 + U.hash(i, seed + 3) * 0.6);
        ctx.moveTo(x - wd, by);
        ctx.quadraticCurveTo(x + sw * 0.25, by - hh * 0.6, x + sw, by - hh);
        ctx.quadraticCurveTo(x + sw * 0.25 + wd * 0.4, by - hh * 0.6, x + wd, by);
      }
      ctx.fill();
    }
  };
  /** a fern (x,y = root) */
  Art.fern = (ctx, x, y, s, color, sway = 0) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = color;
    const fronds = [-1.1, -0.55, 0, 0.55, 1.1];
    for (let f = 0; f < fronds.length; f++) {
      const a = fronds[f] + sway * 0.12;
      ctx.save();
      ctx.rotate(a);
      const L = 70 - Math.abs(fronds[f]) * 18;
      ctx.beginPath();
      for (let i = 1; i < 9; i++) {
        const k = i / 9;
        const py = -L * k;
        const bend = Math.sin(k * 1.4) * 10 * Math.sign(fronds[f] || 1);
        const lw = 11 * (1 - k * 0.8);
        ctx.moveTo(bend, py);
        ctx.ellipse(bend - lw * 0.6, py + 2, lw * 0.7, 2.6, 0.5, 0, TAU);
        ctx.moveTo(bend, py);
        ctx.ellipse(bend + lw * 0.6, py + 2, lw * 0.7, 2.6, -0.5, 0, TAU);
      }
      ctx.fill();
      ctx.strokeStyle = color; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(Math.sign(fronds[f] || 1) * 6, -L * 0.5, Math.sin(1.4) * 10 * Math.sign(fronds[f] || 1), -L); ctx.stroke();
      ctx.restore();
    }
    ctx.restore();
  };
  /** a rounded bush */
  Art.bush = (ctx, x, y, r, color, light = null, seed = 0) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const k = i / 4;
      const px = x + (k - 0.5) * r * 1.6, py = y - Math.sin(k * Math.PI) * r * 0.5 - r * 0.3;
      const rr = r * (0.45 + U.hash(i, seed) * 0.25);
      ctx.moveTo(px + rr, py); ctx.arc(px, py, rr, 0, TAU);
    }
    ctx.fill();
    if (light) { ctx.fillStyle = light; ctx.beginPath(); ctx.arc(x + r * 0.25, y - r * 0.85, r * 0.3, 0, TAU); ctx.fill(); }
  };
  /** a rock */
  Art.rock = (ctx, x, y, w, h, color, seed = 0) => {
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(seed, 1) * 8, y - h);
    ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    ctx.lineTo(x + w / 2, y);
    ctx.closePath();
    ctx.fillStyle = color; ctx.fill();
    ctx.beginPath();
    ctx.moveTo(x - w * 0.12, y - h * 0.95);
    ctx.quadraticCurveTo(x + w * 0.3, y - h * 0.98, x + w * 0.45, y - h * 0.25);
    ctx.lineTo(x + w * 0.1, y - h * 0.4);
    ctx.closePath();
    ctx.fillStyle = U.shade(color, 0.15); ctx.fill();
  };

  /* ======================================================================
     LIGHT & ATMOSPHERE
     ====================================================================== */
  /** additive radial glow */
  Art.glow = (ctx, x, y, r, color, a = 1, mode = 'lighter') => {
    if (a <= 0.002 || r <= 0) return;
    ctx.save();
    ctx.globalCompositeOperation = mode;
    ctx.globalAlpha *= clamp(a);
    const gr = ctx.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, U.rgba(color, 1));
    gr.addColorStop(0.35, U.rgba(color, 0.45));
    gr.addColorStop(1, U.rgba(color, 0));
    ctx.fillStyle = gr;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.restore();
  };
  /** god rays fanning from (x,y) toward angle (radians; PI/2 = straight down) */
  Art.rays = (ctx, { x = 1500, y = -100, angle = 2.1, spread = 0.7, count = 7, len = 1500, color = '#fff3cf', alpha = 0.18, t = 0, seed = 1, width = 0.05, mode = 'lighter' } = {}) => {
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalCompositeOperation = mode;
    for (let i = 0; i < count; i++) {
      const a = angle + (U.hash(i, seed) - 0.5) * spread;
      const wdt = width * (0.5 + U.hash(i, seed + 1));
      const flick = 0.55 + 0.45 * Math.sin(t * (0.3 + U.hash(i, seed + 2) * 0.5) + i * 2.1);
      const ex = x + Math.cos(a) * len, ey = y + Math.sin(a) * len;
      const gr = ctx.createLinearGradient(x, y, ex, ey);
      gr.addColorStop(0, U.rgba(color, alpha * flick));
      gr.addColorStop(0.6, U.rgba(color, alpha * flick * 0.35));
      gr.addColorStop(1, U.rgba(color, 0));
      ctx.fillStyle = gr;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + Math.cos(a - wdt) * len, y + Math.sin(a - wdt) * len);
      ctx.lineTo(x + Math.cos(a + wdt) * len, y + Math.sin(a + wdt) * len);
      ctx.closePath();
      ctx.fill();
    }
    ctx.restore();
  };
  /**
   * floating particles: dust motes, pollen, fireflies. Deterministic in t.
   * Box [x0,y0]-[x1,y1]; drift = px/s upward-ish; glow adds halos.
   */
  Art.motes = (ctx, { seed = 1, count = 40, x0 = 0, y0 = 0, x1 = W, y1 = H, t = 0, color = '#fff6d8', size = 2.2, drift = 12, alpha = 0.7, twinkle = 0.5, glow = 0, wander = 30, blink = 0 } = {}) => {
    if (alpha <= 0) return;
    const bw = x1 - x0, bh = y1 - y0;
    ctx.save();
    for (let i = 0; i < count; i++) {
      const sp = 0.4 + U.hash(i, seed + 3) * 0.9;
      let px = x0 + U.hash(i, seed) * bw + U.noise1(t * 0.23 * sp + i, seed) * wander + t * drift * 0.3 * (U.hash(i, seed + 5) - 0.5);
      let py = y0 + U.hash(i, seed + 1) * bh - t * drift * sp + U.noise1(t * 0.31 * sp + i * 1.7, seed + 2) * wander * 0.6;
      px = x0 + ((((px - x0) % bw) + bw) % bw);
      py = y0 + ((((py - y0) % bh) + bh) % bh);
      let a = alpha * (1 - twinkle + twinkle * (0.5 + 0.5 * Math.sin(t * (1 + sp * 2) + i * 3.1)));
      if (blink) a *= clamp(Math.sin(t * (0.7 + sp * 0.6) + i * 2.3) * 1.6 + 0.2 - blink * 0.2, 0, 1);
      const r = size * (0.5 + U.hash(i, seed + 4));
      if (glow) Art.glow(ctx, px, py, r * 7 * glow, color, a * 0.5);
      ctx.globalAlpha = a;
      ctx.fillStyle = color;
      ctx.beginPath(); ctx.arc(px, py, r, 0, TAU); ctx.fill();
    }
    ctx.restore();
  };
  /** horizontal fog band */
  Art.fog = (ctx, { y = 700, h = 200, color = '#e8f0e8', alpha = 0.5 } = {}) => {
    if (alpha <= 0) return;
    const gr = ctx.createLinearGradient(0, y - h / 2, 0, y + h / 2);
    gr.addColorStop(0, U.rgba(color, 0));
    gr.addColorStop(0.5, U.rgba(color, alpha));
    gr.addColorStop(1, U.rgba(color, 0));
    ctx.fillStyle = gr;
    ctx.fillRect(-W, y - h / 2, W * 3, h);
  };
  /** full-frame desaturation (uses the 'saturation' blend mode) */
  Art.desaturate = (ctx, amt, rect = null) => {
    if (amt <= 0.003) return;
    ctx.save();
    ctx.globalCompositeOperation = 'saturation';
    ctx.globalAlpha = clamp(amt);
    ctx.fillStyle = '#808080';
    if (rect) ctx.fillRect(rect[0], rect[1], rect[2], rect[3]); else ctx.fillRect(-W, -H, W * 3, H * 3);
    ctx.restore();
  };
  /** full-frame color grade: 'color' blend toward a hue (sepia storybook, cold, etc.) */
  Art.colorize = (ctx, color, amt, mode = 'color', rect = null) => {
    if (amt <= 0.003) return;
    ctx.save();
    ctx.globalCompositeOperation = mode;
    ctx.globalAlpha = clamp(amt);
    ctx.fillStyle = color;
    if (rect) ctx.fillRect(rect[0], rect[1], rect[2], rect[3]); else ctx.fillRect(-W, -H, W * 3, H * 3);
    ctx.restore();
  };
  /** radial vignette */
  Art.vignette = (ctx, amt = 0.4, color = '#000000') => {
    if (amt <= 0) return;
    const c = Art.canvas('vignette:' + color, 640, 360);
    if (c._vg !== c._gen) {
      const x = c.getContext('2d');
      x.setTransform(640 / W, 0, 0, 360 / H, 0, 0);
      x.clearRect(0, 0, W, H);
      const gr = x.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
      gr.addColorStop(0, U.rgba(color, 0));
      gr.addColorStop(1, U.rgba(color, 1));
      x.fillStyle = gr;
      x.fillRect(0, 0, W, H);
      c._vg = c._gen;
    }
    ctx.save();
    ctx.globalAlpha *= clamp(amt);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(c, 0, 0, W, H);
    ctx.restore();
  };
  /** cinemascope bars; amt 0..1 */
  Art.letterbox = (ctx, amt = 1) => {
    if (amt <= 0) return;
    const bar = (H - W / 2.39) / 2 * clamp(amt);
    ctx.fillStyle = '#000';
    ctx.fillRect(0, -2, W, bar + 2);
    ctx.fillRect(0, H - bar, W, bar + 2);
  };
  let grainTiles = null;
  /** animated film grain */
  Art.grain = (ctx, amt = 0.05, T = 0) => {
    if (amt <= 0) return;
    if (!grainTiles) {
      grainTiles = [];
      const r = U.rng(99);
      for (let k = 0; k < 4; k++) {
        const c = document.createElement('canvas');
        c.width = c.height = 256;
        const x = c.getContext('2d');
        const img = x.createImageData(256, 256);
        for (let i = 0; i < img.data.length; i += 4) {
          const v = 128 + (r() - 0.5) * 255;
          img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
          img.data[i + 3] = 255;
        }
        x.putImageData(img, 0, 0);
        grainTiles.push(c);
      }
    }
    const f = Math.floor(T * 24);
    const tile = grainTiles[f % 4];
    ctx.save();
    ctx.globalCompositeOperation = 'overlay';
    ctx.globalAlpha = amt;
    const ox = -Math.floor(U.hash(f, 1) * 256), oy = -Math.floor(U.hash(f, 2) * 256);
    const pat = ctx.createPattern(tile, 'repeat');
    ctx.translate(ox, oy);
    ctx.fillStyle = pat;
    ctx.fillRect(0, 0, W + 256, H + 256);
    ctx.restore();
  };

  /* ======================================================================
     CHARACTERS
     ====================================================================== */
  /**
   * The cast. Pass a key ('me', 'h1'...) or an object as `look`.
   *  me  — the narrator ("I"): warm, earthy, rust beanie, mustard jacket.
   *  h1  — trail leader: tall, cap, electric-blue tech jacket, trekking poles.
   *  h2  — ponytail, teal shell, huge orange pack.
   *  h3  — curly hair, bucket hat, slate-violet fleece.
   *  h4  — buzz cut, grey hoodie, always holding a phone.
   *  emb — EMBARRASSMENT, the flower-shop owner: a personified emotion.
   *        Lanky, rose-pink skin, perma-blush, round glasses, green apron.
   */
  Art.CAST = {
    me: { name: 'me', skin: '#e8b48c', hair: '#3a2a21', hairStyle: 'messy', hat: 'beanie', hatColor: '#c4553b', shirt: '#d99d3c', shirt2: '#8d5a26', pants: '#2f4a4f', shoes: '#5b3b2a', pack: '#6b7a3f', packSize: 0.85, beard: '#3a2a21', height: 1 },
    h1: { name: 'h1', skin: '#f0c3a0', hair: '#2a2a2a', hairStyle: 'short', hat: 'cap', hatColor: '#1d3557', shirt: '#2f7fd8', shirt2: '#a8f0ff', pants: '#2b2f3a', shoes: '#e9edf0', pack: '#3a3f4b', packSize: 0.9, poles: true, height: 1.08 },
    h2: { name: 'h2', skin: '#b5805e', hair: '#1f1712', hairStyle: 'ponytail', shirt: '#3aa39b', shirt2: '#dbf6f1', pants: '#384151', shoes: '#2b2b33', pack: '#e0623f', packSize: 1.25, height: 0.96 },
    h3: { name: 'h3', skin: '#f1cfb3', hair: '#7a4b2a', hairStyle: 'curly', hat: 'bucket', hatColor: '#8d89a8', shirt: '#6857c8', shirt2: '#cfc8ff', pants: '#3a3550', shoes: '#22222a', pack: '#4b4f63', packSize: 0.9, height: 0.92 },
    h4: { name: 'h4', skin: '#8c5a3f', hair: '#151515', hairStyle: 'buzz', shirt: '#8a93a3', shirt2: '#c9cfd9', pants: '#2e3440', shoes: '#f1f1f1', pack: '#2a2f3a', packSize: 0.95, hood: true, height: 1.02 },
    emb: { name: 'emb', skin: '#f2a59e', hair: '#8c2f45', hairStyle: 'tuft', shirt: '#f3e7d8', shirt2: '#d9c6b0', pants: '#5b4b45', shoes: '#3b2a25', apron: '#4f7a5a', glasses: true, blush: 0.8, height: 1.1, lanky: true },
  };
  Art.HIKERS = ['h1', 'h2', 'h3', 'h4'];
  /** the emotions (small luminous beings that live in the narrator's mind) */
  Art.EMO = { wonder: '#ffc94a', calm: '#6fb7ff', heart: '#ff7aa8', spark: '#8fe3a9', dream: '#b49cff', shy: '#f59a8e' };

  const SKEL = { thigh: 58, shin: 56, torso: 88, neck: 12, headR: 36, upper: 50, fore: 47, hipW: 22, shW: 27 };

  /** two-bone IK. angles measured from straight down, positive = forward (+x). */
  function ik2(ox, oy, tx, ty, l1, l2, bend) {
    const dx = tx - ox, dy = ty - oy;
    let d = Math.hypot(dx, dy);
    d = clamp(d, Math.abs(l1 - l2) + 0.01, l1 + l2 - 0.01);
    const base = Math.atan2(dx, dy);
    const A = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
    const B = Math.acos(clamp((l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2), -1, 1));
    return [base + bend * A, -bend * (Math.PI - B)];
  }
  Art.ik2 = ik2;
  function limb(ox, oy, a1, l1, rel, l2) {
    const x1 = ox + Math.sin(a1) * l1, y1 = oy + Math.cos(a1) * l1;
    const a2 = a1 + rel;
    return { x0: ox, y0: oy, x1, y1, x2: x1 + Math.sin(a2) * l2, y2: y1 + Math.cos(a2) * l2, a1, a2 };
  }
  function strokeLimb(ctx, L, w1, w2, col) {
    ctx.strokeStyle = col;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = w1;
    ctx.beginPath(); ctx.moveTo(L.x0, L.y0); ctx.lineTo(L.x1, L.y1); ctx.stroke();
    ctx.lineWidth = w2;
    ctx.beginPath(); ctx.moveTo(L.x1, L.y1); ctx.lineTo(L.x2, L.y2); ctx.stroke();
  }
  const lookOf = (l) => (typeof l === 'string' ? Art.CAST[l] : l) || Art.CAST.me;

  /* ------------------------- face & head ------------------------- */
  function drawEye(ctx, ex, ey, sc, style, f, ink) {
    const bl = clamp(f.blink || 0);
    const lx = (f.lookX || 0) * 2.2, ly = (f.lookY || 0) * 2.2;
    ctx.save();
    ctx.translate(ex, ey);
    ctx.scale(sc, sc);
    ctx.fillStyle = ink;
    ctx.strokeStyle = ink;
    ctx.lineCap = 'round';
    ctx.lineWidth = 3;
    const open = (rx, ry) => {
      const r = ry * (1 - bl * 0.95);
      if (r < 0.9) { ctx.beginPath(); ctx.moveTo(-rx, 0); ctx.lineTo(rx, 0); ctx.stroke(); return false; }
      ctx.beginPath(); ctx.ellipse(lx * 0.6, ly * 0.6, rx, r, 0, 0, TAU); ctx.fill();
      return true;
    };
    switch (style) {
      case 'happy':
        ctx.beginPath(); ctx.arc(0, 3, 5.4, Math.PI + 0.35, TAU - 0.35); ctx.stroke(); break;
      case 'closed':
        ctx.beginPath(); ctx.arc(0, -2.5, 5.2, 0.35, Math.PI - 0.35); ctx.stroke(); break;
      case 'squeeze': // >_< laughing hard
        ctx.beginPath(); ctx.moveTo(-5, -4); ctx.lineTo(3, 0); ctx.lineTo(-5, 4); ctx.stroke(); break;
      case 'wide': {
        const r = 8 * (1 - bl * 0.95);
        ctx.fillStyle = '#fbf8f2';
        ctx.beginPath(); ctx.ellipse(0, 0, 7.2, Math.max(0.8, r), 0, 0, TAU); ctx.fill();
        ctx.lineWidth = 1.4; ctx.stroke();
        if (r > 2) { ctx.fillStyle = ink; ctx.beginPath(); ctx.arc(lx * 1.2, ly * 1.2, 3.4, 0, TAU); ctx.fill(); }
        break;
      }
      case 'roll': { // eye-roll: pupils up
        ctx.fillStyle = '#fbf8f2';
        ctx.beginPath(); ctx.ellipse(0, 0, 6.6, 7.4, 0, 0, TAU); ctx.fill();
        ctx.lineWidth = 1.3; ctx.stroke();
        ctx.fillStyle = ink;
        ctx.beginPath(); ctx.arc(lx * 1.1, -4.2 + ly, 3.2, 0, TAU); ctx.fill();
        break;
      }
      case 'distant': { // tired, half-lidded, unfocused
        if (open(4.4, 5.4)) {
          ctx.fillStyle = f.skinLid || '#e8b48c';
          ctx.fillRect(-7, -9, 14, 8.2);
          ctx.beginPath(); ctx.moveTo(-6, -0.8); ctx.lineTo(6, -0.8); ctx.stroke();
        }
        ctx.globalAlpha *= 0.35; ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.arc(0, 4, 5.5, 0.4, Math.PI - 0.4); ctx.stroke();
        break;
      }
      case 'flat': { // deadpan, lids half down
        if (open(4.4, 5.6)) {
          ctx.fillStyle = f.skinLid || '#e8b48c';
          ctx.fillRect(-7, -9, 14, 8.4);
          ctx.beginPath(); ctx.moveTo(-6, -0.6); ctx.lineTo(6, -0.6); ctx.stroke();
        }
        break;
      }
      case 'sparkle': { // beaming, glinting
        if (open(5, 6.4)) {
          ctx.fillStyle = '#ffffff';
          ctx.beginPath(); ctx.arc(1.6 + lx * 0.6, -2.2 + ly * 0.6, 2.1, 0, TAU); ctx.fill();
          ctx.beginPath(); ctx.arc(-1.6 + lx * 0.6, 2 + ly * 0.6, 1, 0, TAU); ctx.fill();
        }
        break;
      }
      default: // 'open'
        if (open(4.4, 5.6)) {
          ctx.fillStyle = 'rgba(255,255,255,0.9)';
          ctx.beginPath(); ctx.arc(1.4 + lx * 0.6, -2 + ly * 0.6, 1.5, 0, TAU); ctx.fill();
        }
    }
    ctx.restore();
  }

  /**
   * Draw a face in head-local space (center 0,0, radius 36, facing +x).
   * f = { smile -1..1, open 0..1, talk 0..1, eyes, brow -1(angry)..1(worried),
   *       browUp 0..1, blush, sweat, lookX, lookY, blink, smirk 0..1, mouth:'o' }
   */
  function drawFace(ctx, look, f, turn, t, seed) {
    const R = SKEL.headR;
    const fx = 8 * (1 - turn);
    const ink = '#2a201c';
    const skinD = U.shade(look.skin, -0.22);
    f = Object.assign({ smile: 0.15, eyes: 'open', brow: 0, browUp: 0 }, f);
    if (f.blink === undefined) f.blink = U.blink(t, seed);
    f.skinLid = look.skin;
    // ear
    if (turn < 0.75) {
      ctx.fillStyle = skinD;
      ctx.beginPath(); ctx.ellipse(fx - 17 - 4 * (1 - turn), 3, 5.5, 8, 0, 0, TAU); ctx.fill();
    }
    // cheeks
    const blush = Math.max(f.blush || 0, look.blush || 0);
    if (blush > 0) {
      ctx.save();
      ctx.globalAlpha *= blush * 0.55;
      ctx.fillStyle = '#ff5e78';
      ctx.beginPath(); ctx.ellipse(fx + 17, 10, 7.5, 4.6, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.ellipse(fx - 11 + turn * -4, 10, 6.5 + turn, 4.2, 0, 0, TAU); ctx.fill();
      ctx.restore();
    }
    // stubble
    if (look.beard) {
      ctx.save();
      ctx.beginPath(); ctx.arc(0, 0, R - 0.5, 0, TAU); ctx.clip();
      ctx.globalAlpha *= 0.16;
      ctx.fillStyle = look.beard;
      ctx.beginPath(); ctx.ellipse(fx * 0.7 + 3, 22, R * 0.62, R * 0.42, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.ellipse(fx * 0.7 + 4, 12, 10, 3.2, 0, 0, TAU); ctx.fill();
      ctx.restore();
    }
    // eyes
    const eyeY = -3 + (f.lookY || 0) * 0.6;
    const nearX = fx + 12.5 * (1 - turn) + 12 * turn, farX = fx - 9.5 * (1 - turn) - 12 * turn;
    drawEye(ctx, nearX, eyeY, 1, f.eyes, f, ink);
    drawEye(ctx, farX, eyeY, 0.86 + 0.14 * turn, f.eyes, f, ink);
    // glasses
    if (look.glasses) {
      ctx.strokeStyle = '#3b2a25';
      ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.arc(nearX, eyeY, 9.5, 0, TAU); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(farX, eyeY, 8.2 + turn, 9.2, 0, 0, TAU); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(farX + 8.5, eyeY - 1); ctx.quadraticCurveTo((nearX + farX) / 2, eyeY - 4, nearX - 9.5, eyeY - 1); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(farX - 8.5, eyeY - 2); ctx.lineTo(fx - 20, eyeY - 1); ctx.stroke();
      ctx.save(); ctx.globalAlpha *= 0.25; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(nearX, eyeY, 6.5, -2.4, -1.5); ctx.stroke(); ctx.restore();
    }
    // brows
    const by = -16 - (f.browUp || 0) * 5;
    const b = f.brow || 0;
    ctx.strokeStyle = U.shade(look.hair, -0.1);
    ctx.lineWidth = 3.2;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(nearX - 6, by - 3 * b); ctx.lineTo(nearX + 6, by + 3 * b - 1); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(farX - 5, by + 3 * b - 1); ctx.lineTo(farX + 5, by - 3 * b); ctx.stroke();
    // nose
    const nx = lerp(fx + 19, 2, turn);
    ctx.strokeStyle = skinD;
    ctx.lineWidth = 2.6;
    ctx.beginPath(); ctx.moveTo(nx - 1, 1); ctx.quadraticCurveTo(nx + 5 * (1 - turn) + 2, 7, nx - 1.5, 9); ctx.stroke();
    // mouth
    let open = f.open || 0;
    if (f.talk) open = Math.max(open, f.talk * (0.2 + 0.65 * Math.abs(U.noise1(t * 9.5, seed + 4))));
    const s = clamp(f.smile, -1, 1);
    const mx = lerp(fx + 5, 0, turn), my = 17;
    const mw = 8.5 + 3.5 * Math.abs(s) + open * 2;
    const sm = f.smirk || 0;
    const ly = my - s * 2.4 + sm * 1.5, ry = my - s * 2.4 - sm * 5.5;
    if (f.mouth === 'o') {
      ctx.fillStyle = '#5a2430';
      ctx.beginPath(); ctx.ellipse(mx, my + 2, 4 + open * 2, 5 + open * 4, 0, 0, TAU); ctx.fill();
    } else if (open < 0.08) {
      ctx.strokeStyle = '#5c2b2b';
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(mx - mw, ly); ctx.quadraticCurveTo(mx + sm * 3, my + s * 9 - sm * 2, mx + mw, ry); ctx.stroke();
    } else {
      const drop = 5 + open * 13;
      ctx.fillStyle = '#5a2430';
      ctx.beginPath();
      ctx.moveTo(mx - mw, ly);
      ctx.quadraticCurveTo(mx, my + s * 5 - 2, mx + mw, ry);
      ctx.quadraticCurveTo(mx, my + drop + s * 5, mx - mw, ly);
      ctx.fill();
      ctx.save();
      ctx.clip();
      if (s > 0.25) { ctx.fillStyle = '#fbf6ef'; ctx.fillRect(mx - mw, my - 6, mw * 2, 6 + s * 2); }
      ctx.fillStyle = '#d9606f';
      ctx.beginPath(); ctx.ellipse(mx, my + drop + s * 3, mw * 0.6, 5, 0, 0, TAU); ctx.fill();
      ctx.restore();
    }
    // sweat
    if (f.sweat > 0) {
      ctx.save();
      ctx.globalAlpha *= clamp(f.sweat);
      for (let i = 0; i < 3; i++) {
        const ph = U.fract(t * 0.45 + i * 0.37);
        const dx = [fx - 22, fx + 26, fx - 8][i], dy = [-20, -14, -28][i] + ph * 16;
        ctx.globalAlpha = clamp(f.sweat) * Math.sin(ph * Math.PI);
        ctx.fillStyle = '#bfe8ff';
        ctx.beginPath();
        ctx.moveTo(dx, dy - 6);
        ctx.quadraticCurveTo(dx + 4.5, dy + 1, dx, dy + 3.5);
        ctx.quadraticCurveTo(dx - 4.5, dy + 1, dx, dy - 6);
        ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.beginPath(); ctx.arc(dx - 1, dy, 1, 0, TAU); ctx.fill();
      }
      ctx.restore();
    }
  }

  /** hairline: hair is drawn where y < hl(x) inside the head circle */
  function hairPath(ctx, look, turn) {
    const R = SKEL.headR;
    const fx = 8 * (1 - turn);
    const st = look.hairStyle;
    const frontY = st === 'buzz' ? -22 : st === 'tuft' ? -17 : -15;
    const backY = st === 'buzz' ? -2 : st === 'long' || st === 'ponytail' ? 12 : 8;
    ctx.beginPath();
    ctx.moveTo(-R - 8, -R - 30);
    ctx.lineTo(R + 8, -R - 30);
    for (let i = 0; i <= 24; i++) {
      const x = lerp(R + 8, -R - 8, i / 24);
      const k = U.smooth(U.invLerp(fx + 6, -R + 4, x));
      let y = lerp(frontY, backY, k);
      if (st !== 'buzz') y += Math.sin(x * 0.42) * 2.5 * (1 - k);
      if (turn > 0.5 && Math.abs(x) < 14) y -= 2;
      ctx.lineTo(x, y);
    }
    ctx.closePath();
  }
  /**
   * draw a head in head-local space. Exposed as Art.drawHeadLocal.
   */
  function drawHeadLocal(ctx, look, f, turn, t, seed) {
    const R = SKEL.headR;
    const st = look.hairStyle;
    const hair = look.hair;
    // back hair layers
    if (st === 'ponytail') {
      const sw = Math.sin(t * 3.2 + seed) * 4;
      ctx.strokeStyle = hair; ctx.lineCap = 'round'; ctx.lineWidth = 14;
      ctx.beginPath(); ctx.moveTo(-R + 6, -14); ctx.quadraticCurveTo(-R - 18 + sw, 0, -R - 10 + sw * 1.6, 34); ctx.stroke();
      ctx.fillStyle = U.shade(hair, 0.2); ctx.beginPath(); ctx.arc(-R + 4, -14, 6, 0, TAU); ctx.fill();
    }
    if (st === 'long') {
      ctx.fillStyle = hair;
      ctx.beginPath(); ctx.ellipse(-8, 10, R * 0.95, R * 1.25, 0, 0, TAU); ctx.fill();
    }
    if (st === 'bun') { ctx.fillStyle = hair; ctx.beginPath(); ctx.arc(-R * 0.6, -R * 0.75, 13, 0, TAU); ctx.fill(); }
    // head
    const hg = ctx.createRadialGradient(R * 0.3, -R * 0.35, R * 0.1, 0, 0, R * 1.04);
    hg.addColorStop(0, U.shade(look.skin, 0.1));
    hg.addColorStop(0.62, look.skin);
    hg.addColorStop(1, U.shade(look.skin, -0.14));
    ctx.fillStyle = hg;
    ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.fill();
    drawFace(ctx, look, f, turn, t, seed);
    // hair cap (clipped to slightly enlarged head)
    if (!(look.hat && (look.hat === 'beanie'))) {
      ctx.save();
      ctx.beginPath(); ctx.arc(0, -1, R + 2.5, 0, TAU); ctx.clip();
      hairPath(ctx, look, turn);
      ctx.fillStyle = hair;
      ctx.globalAlpha *= st === 'buzz' ? 0.85 : 1;
      ctx.fill();
      ctx.restore();
    }
    // style extras
    ctx.fillStyle = hair;
    if (st === 'messy' && !look.hat) {
      for (let i = 0; i < 5; i++) {
        const a = -2.6 + i * 0.42;
        const px = Math.cos(a) * R, py = Math.sin(a) * R;
        ctx.beginPath(); ctx.moveTo(px - 6, py + 3); ctx.lineTo(px + Math.cos(a) * 10 + 3, py + Math.sin(a) * 10); ctx.lineTo(px + 6, py + 3); ctx.fill();
      }
    }
    if (st === 'curly') {
      for (let i = 0; i < 9; i++) {
        const a = Math.PI + 0.1 + i * 0.36;
        ctx.beginPath(); ctx.arc(Math.cos(a) * (R - 1), Math.sin(a) * (R - 1) - 2, 9.5, 0, TAU); ctx.fill();
      }
    }
    if (st === 'tuft') {
      const sw = Math.sin(t * 2.4 + seed) * 2;
      ctx.beginPath();
      ctx.moveTo(-14, -R + 6);
      ctx.bezierCurveTo(-10, -R - 22, 18 + sw, -R - 30, 26 + sw, -R - 10);
      ctx.bezierCurveTo(16, -R - 16, 6, -R - 8, 6, -R + 6);
      ctx.fill();
      ctx.beginPath(); ctx.arc(-R + 6, -14, 8, 0, TAU); ctx.fill();
    }
    // hats
    if (look.hat) {
      const hc = look.hatColor || '#c4553b';
      if (look.hat === 'beanie') {
        ctx.fillStyle = hc;
        ctx.beginPath();
        ctx.moveTo(-R - 3, -6);
        ctx.bezierCurveTo(-R - 4, -R - 16, R + 2, -R - 18, R + 3, -10);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = U.shade(hc, -0.15);
        ctx.beginPath();
        ctx.moveTo(-R - 4, -3); ctx.lineTo(R + 4, -8); ctx.lineTo(R + 4, -18); ctx.lineTo(-R - 4, -15); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = U.shade(hc, -0.28); ctx.lineWidth = 1.5;
        for (let i = -3; i <= 3; i++) { ctx.beginPath(); ctx.moveTo(i * 10, -5 - i * 0.7); ctx.lineTo(i * 10 + 1, -16 - i * 0.7); ctx.stroke(); }
        ctx.fillStyle = U.shade(hc, 0.12);
        ctx.beginPath(); ctx.arc(-6, -R - 14, 7.5, 0, TAU); ctx.fill();
        // hair poking out at the back
        ctx.fillStyle = hair;
        ctx.beginPath(); ctx.moveTo(-R + 1, -4); ctx.quadraticCurveTo(-R - 4, 8, -R + 6, 10); ctx.lineTo(-R + 9, -2); ctx.fill();
      } else if (look.hat === 'cap') {
        ctx.fillStyle = hc;
        ctx.beginPath(); ctx.arc(0, -6, R + 1, Math.PI + 0.05, TAU - 0.05); ctx.closePath(); ctx.fill();
        ctx.fillStyle = U.shade(hc, -0.2);
        ctx.beginPath(); ctx.moveTo(R * 0.3, -10); ctx.quadraticCurveTo(R + 14, -14, R + 22, -6); ctx.quadraticCurveTo(R + 6, -4, R * 0.3, -6); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.globalAlpha *= 0.85;
        ctx.beginPath(); ctx.arc(R * 0.35, -R * 0.62, 4, 0, TAU); ctx.fill();
        ctx.globalAlpha /= 0.85;
      } else if (look.hat === 'bucket') {
        ctx.fillStyle = hc;
        ctx.beginPath(); ctx.arc(0, -8, R - 2, Math.PI, TAU); ctx.closePath(); ctx.fill();
        ctx.fillStyle = U.shade(hc, -0.15);
        ctx.beginPath(); ctx.moveTo(-R - 12, 0); ctx.quadraticCurveTo(0, -16, R + 12, 0); ctx.lineTo(R + 4, -10); ctx.quadraticCurveTo(0, -20, -R - 4, -10); ctx.closePath(); ctx.fill();
      }
    }
  }
  Art.drawHeadLocal = drawHeadLocal;
  Art.drawFaceLocal = drawFace;

  /**
   * Standalone head at world (x,y) with radius r (default 36). Useful for gags,
   * thought bubbles, portraits.
   */
  Art.head = (ctx, x, y, r, look, face = {}, { facing = 1, turn = 0, t = 0, seed = 0, tilt = 0 } = {}) => {
    look = lookOf(look);
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(tilt * facing);
    const k = r / SKEL.headR;
    ctx.scale(k * facing, k);
    drawHeadLocal(ctx, look, face, turn, t, seed);
    ctx.restore();
  };

  /* ------------------------- body rig ------------------------- */
  const GESTURES = {
    // [shoulder, elbow] for front arm / back arm. Angles from straight down, + = forward.
    stand: { F: [0.1, 0.18], B: [-0.08, 0.14] },
    wave: { F: [2.25, 0.62], B: [-0.05, 0.15], waveF: true },
    shrug: { F: [0.3, 1.5], B: [0.08, 1.55], shrug: 1 },
    point: { F: [1.5, 0.05], B: [-0.05, 0.15] },
    give: { F: [1.25, 0.25], B: [-0.05, 0.15] },
    cheer: { F: [2.45, 0.38], B: [2.62, 0.3] },
    reach: { F: [1.0, 0.25], B: [-0.1, 0.2] },
    open: { F: [0.8, 0.5], B: [-0.7, 0.4] },
    // IK targets in body-local coords (relative to feet), resolved at draw time
    hips: { tF: [13, -128], tB: [-19, -128] },
    hold: { tF: [36, -166], tB: [30, -160] },
    holdHigh: { tF: [40, -222], tB: [34, -216] },
    pocket: { tF: [11, -112], tB: [-15, -112] },
    chin: { tF: ['face', 14, 22], B: [-0.05, 0.15] },
    facepalm: { tF: ['face', 14, -2], B: [0.05, 0.3] },
    heart: { tF: [16, -184], B: [-0.05, 0.15] },
    phone: { F: [2.15, 0.75], B: [-0.05, 0.15] },
    phoneLook: { tF: [34, -176], tB: [28, -172] },
    behind: { tF: [-22, -128], tB: [-26, -126] },
  };
  Art.GESTURES = GESTURES;

  /**
   * Art.person(ctx, opts) → anchors {head, top, handF, handB, chest, feet} in world coords.
   * opts:
   *  x, y        feet position (ground contact)
   *  s           scale (1 → ~300px tall for height 1.0)
   *  facing      1 = right, -1 = left
   *  look        cast key or look object
   *  pose        'stand' | 'walk' | 'sit' (on ground) | 'bench' | 'crouch' | 'kneel'
   *  walk        walk-cycle phase in radians (advance ≈ speed * t)
   *  stride      0..1 walk amplitude
   *  lean        torso lean (rad, + forward)
   *  gesture     key of Art.GESTURES; gw = weight 0..1 (blend from neutral)
   *  armF/armB   explicit [shoulder, elbow] overrides
   *  reachF/reachB  {x,y} WORLD target for that hand (two-bone IK)
   *  shrug       0..1 raise shoulders
   *  head        { tilt, turn (0 = 3/4 view .. 1 = facing camera), nod }
   *  face        see drawFace
   *  tired       0..1 slump; bounce 0..1 happy spring in the step
   *  t, seed     time and per-character seed (blinks, breathing)
   *  holdF       fn(ctx) drawn at the front hand (local units, +x forward)
   *  holdB       fn(ctx) at the back hand
   *  glow        0..1 warm inner light (for moments of meaning)
   *  shadow      draw ground shadow (default true); alpha
   */
  Art.person = (ctx, o = {}) => {
    const look = lookOf(o.look);
    const t = o.t || 0, seed = o.seed !== undefined ? o.seed : (look.name || 'x').charCodeAt(0) * 7 + (parseInt(String(look.name || '').replace(/\D/g, ''), 10) || 0) * 101;
    const facing = o.facing === undefined ? 1 : o.facing;
    const S = (o.s || 1) * (look.height || 1);
    const x = o.x || 0, y = o.y || 0;
    const lank = look.lanky ? 1.1 : 1;
    const thigh = SKEL.thigh * lank, shin = SKEL.shin * lank, upper = SKEL.upper * lank, fore = SKEL.fore * lank;
    const torsoH = SKEL.torso * (look.lanky ? 1.06 : 1);
    const pose = o.pose || (o.walk !== undefined ? 'walk' : 'stand');
    const tired = o.tired || 0;
    const stride = o.stride === undefined ? 1 : o.stride;
    const head = Object.assign({ tilt: 0, turn: 0, nod: 0 }, o.head || {});
    let lean = (o.lean || 0) + tired * 0.22;
    const breathe = Math.sin(t * 1.7 + seed) * 1.3;

    // ---- legs & hip ----
    let hipX = 0, hipY = -(thigh + shin + 4);
    let legF, legB;
    if (pose === 'walk') {
      const ph = o.walk || 0;
      const sw = 0.42 * stride;
      const aF = Math.sin(ph) * sw, aB = -aF;
      const kF = -(0.12 + Math.max(0, Math.cos(ph)) * 0.75 * stride);
      const kB = -(0.12 + Math.max(0, -Math.cos(ph)) * 0.75 * stride);
      hipY += (1 - Math.abs(Math.cos(ph))) * 0 + Math.abs(Math.sin(ph)) * 5 * stride - 3 * stride;
      hipY -= (o.bounce || 0) * Math.abs(Math.cos(ph)) * 9;
      legF = limb(hipX + 3, hipY, aF, thigh, kF, shin);
      legB = limb(hipX - 3, hipY, aB, thigh, kB, shin);
      lean += 0.06 * stride;
    } else if (pose === 'sit') {
      hipY = -22;
      legF = limb(hipX + 4, hipY, 2.05, thigh, -1.7, shin);
      legB = limb(hipX - 2, hipY, 2.0, thigh, -1.5, shin);
    } else if (pose === 'bench') {
      hipY = -(shin + 10) * 1;
      legF = limb(hipX + 4, hipY, 1.52, thigh, -1.42, shin);
      legB = limb(hipX - 2, hipY, 1.45, thigh, -1.25, shin);
    } else if (pose === 'crouch') {
      hipY = -64;
      legF = limb(hipX + 4, hipY, 1.38, thigh, -1.62, shin);
      legB = limb(hipX - 4, hipY, 0.95, thigh, -1.92, shin);
      lean += 0.38;
    } else if (pose === 'kneel') {
      hipY = -76;
      legF = limb(hipX + 4, hipY, 1.3, thigh, -1.25, shin);
      legB = limb(hipX - 4, hipY, 0.2, thigh, -1.6, shin);
      lean += 0.12;
    } else {
      hipY += 1;
      legF = limb(hipX + 4, hipY, 0.05, thigh, -0.02, shin);
      legB = limb(hipX - 4, hipY, -0.04, thigh, -0.02, shin);
    }
    hipY += (o.bob || 0);

    // ---- torso / shoulders / head ----
    const shrug = Math.max(o.shrug || 0, (GESTURES[o.gesture] && GESTURES[o.gesture].shrug ? (o.gw === undefined ? 1 : o.gw) : 0));
    const sinL = Math.sin(lean), cosL = Math.cos(lean);
    const topLen = torsoH + breathe * 0.3;
    const shX = hipX + sinL * topLen, shY = hipY - cosL * topLen;
    const shoulderY = shY + 7 - shrug * 8;
    const nod = head.nod || 0;
    const hTilt = (head.tilt || 0) + tired * 0.35 + nod;
    const neckLen = SKEL.neck + SKEL.headR - shrug * 6;
    const hdx = shX + Math.sin(lean + hTilt * 0.6) * neckLen + 4, hdy = shY - Math.cos(lean + hTilt * 0.6) * neckLen;
    const R = SKEL.headR;

    // ---- arms ----
    const gw = o.gw === undefined ? 1 : clamp(o.gw);
    const gest = GESTURES[o.gesture] || null;
    const shF = { x: shX + 3, y: shoulderY }, shB = { x: shX - 6, y: shoulderY + 1 };
    const toLocal = (p) => ({ x: (p.x - x) / (S * facing), y: (p.y - y) / S });
    let aF, aB;
    if (pose === 'walk') {
      const ph = o.walk || 0;
      const sw = Math.sin(ph) * 0.5 * stride * (1 - tired * 0.5);
      aF = [-sw * 0.9 + 0.04, 0.25 + Math.max(0, -sw) * 0.6];
      aB = [sw * 0.9 - 0.04, 0.25 + Math.max(0, sw) * 0.6];
    } else if (pose === 'sit' || pose === 'bench') {
      aF = ik2(shF.x, shF.y, legF.x1 + 4, legF.y1 - 8, upper, fore, -1);
      aB = ik2(shB.x, shB.y, legB.x1 - 4, legB.y1 - 6, upper, fore, -1);
    } else if (pose === 'crouch' || pose === 'kneel') {
      aF = ik2(shF.x, shF.y, legF.x1 + 10, legF.y1 - 4, upper, fore, -1);
      aB = ik2(shB.x, shB.y, legB.x1 + 6, legB.y1 - 2, upper, fore, -1);
    } else {
      aF = GESTURES.stand.F.slice();
      aB = GESTURES.stand.B.slice();
      aF[0] += Math.sin(t * 1.7 + seed) * 0.015;
    }
    const resolve = (g, which, sh) => {
      if (!g) return null;
      const tk = which === 'F' ? g.tF : g.tB;
      if (tk) {
        let tx, ty;
        if (tk[0] === 'face') { tx = hdx + tk[1]; ty = hdy + tk[2]; } else { tx = tk[0] + (shX - hipX); ty = tk[1]; }
        return ik2(sh.x, sh.y, tx, ty, upper, fore, -1);
      }
      const a = which === 'F' ? g.F : g.B;
      return a ? a.slice() : null;
    };
    if (gest) {
      const gF = resolve(gest, 'F', shF), gB = resolve(gest, 'B', shB);
      if (gF) { if (gest.waveF) gF[1] += Math.sin(t * 10) * 0.38; aF = [lerp(aF[0], gF[0], gw), lerp(aF[1], gF[1], gw)]; }
      if (gB) aB = [lerp(aB[0], gB[0], gw), lerp(aB[1], gB[1], gw)];
    }
    if (o.armF) aF = o.armF;
    if (o.armB) aB = o.armB;
    if (o.reachF) { const p = toLocal(o.reachF); aF = ik2(shF.x, shF.y, p.x, p.y, upper, fore, -1); }
    if (o.reachB) { const p = toLocal(o.reachB); aB = ik2(shB.x, shB.y, p.x, p.y, upper, fore, -1); }
    const armF = limb(shF.x, shF.y, aF[0], upper, aF[1], fore);
    const armB = limb(shB.x, shB.y, aB[0], upper, aB[1], fore);

    // ---- draw ----
    ctx.save();
    if (o.alpha !== undefined) ctx.globalAlpha *= clamp(o.alpha);
    ctx.translate(x, y);
    if (o.shadow !== false) {
      ctx.fillStyle = 'rgba(10,12,20,0.22)';
      ctx.beginPath(); ctx.ellipse(0, 2, 46 * S * (pose === 'sit' ? 1.5 : 1), 8 * S, 0, 0, TAU); ctx.fill();
    }
    ctx.scale(S * facing, S);
    if (o.glow) Art.glow(ctx, shX, shY + 20, 260, '#ffd38a', o.glow * 0.6);
    const sleeveB = U.shade(look.shirt, -0.2), pantsB = U.shade(look.pants, -0.22);
    const walkPoles = look.poles && pose === 'walk' && o.poles !== false;
    const pole = (arm, dark) => {
      const hx = arm.x2, hy = arm.y2 - 4, tx2 = arm.x2 + 26, ty2 = -1;
      const dx = tx2 - hx, dy = ty2 - hy, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
      ctx.lineCap = 'round';
      ctx.strokeStyle = U.shade(look.pole || '#6f7680', dark); ctx.lineWidth = 4.4;
      ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(tx2, ty2); ctx.stroke();
      ctx.strokeStyle = U.shade(look.poleHi || '#d3d7dd', dark); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(hx + ux * 12 - uy * 0.8, hy + uy * 12 + ux * 0.8); ctx.lineTo(tx2 - ux * 6, ty2 - uy * 6); ctx.stroke();
      ctx.strokeStyle = '#272b35'; ctx.lineWidth = 5.4;
      ctx.beginPath(); ctx.moveTo(hx - ux * 7, hy - uy * 7); ctx.lineTo(hx + ux * 9, hy + uy * 9); ctx.stroke();
      ctx.strokeStyle = '#3a3f4b'; ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.moveTo(tx2 - ux * 9 - uy * 5, ty2 - uy * 9 + ux * 5); ctx.lineTo(tx2 - ux * 9 + uy * 5, ty2 - uy * 9 - ux * 5); ctx.stroke();
    };
    if (walkPoles) pole(armB, -0.18);
    // back arm
    strokeLimb(ctx, armB, 13, 12, sleeveB);
    ctx.fillStyle = U.shade(look.skin, -0.15);
    ctx.beginPath(); ctx.arc(armB.x2, armB.y2, 7, 0, TAU); ctx.fill();
    if (o.holdB) { ctx.save(); ctx.translate(armB.x2, armB.y2); o.holdB(ctx); ctx.restore(); }
    // back leg
    strokeLimb(ctx, legB, 19, 17, pantsB);
    drawShoe(ctx, legB, U.shade(look.shoes, -0.15));
    // backpack
    if (look.pack && o.pack !== false) {
      const ps = look.packSize || 1;
      ctx.save();
      ctx.translate(hipX, hipY);
      ctx.rotate(lean);
      ctx.fillStyle = look.pack;
      const pw = 30 * ps, ph = 70 * ps;
      roundRect(ctx, -SKEL.shW - pw + 10, -torsoH + 6 - (ps - 1) * 30, pw, ph, 10);
      ctx.fill();
      ctx.fillStyle = U.shade(look.pack, -0.18);
      roundRect(ctx, -SKEL.shW - pw + 8, -torsoH + 38 - (ps - 1) * 10, pw * 0.7, ph * 0.38, 7);
      ctx.fill();
      if (ps > 1.1) { // bedroll
        ctx.fillStyle = '#c9b48a';
        roundRect(ctx, -SKEL.shW - pw + 6, -torsoH - 10 - (ps - 1) * 30, pw + 6, 16, 8);
        ctx.fill();
      }
      ctx.restore();
    }
    // front leg
    strokeLimb(ctx, legF, 19, 17, look.pants);
    drawShoe(ctx, legF, look.shoes);
    // torso
    ctx.save();
    ctx.translate(hipX, hipY);
    ctx.rotate(lean);
    const hw = SKEL.hipW, sw = SKEL.shW, th = topLen;
    ctx.beginPath();
    ctx.moveTo(-hw, 6);
    ctx.lineTo(hw + 1, 6);
    ctx.quadraticCurveTo(sw + 3, -th * 0.45, sw, -th + 9);
    ctx.quadraticCurveTo(sw - 1, -th - 2 + shrug * -6, sw - 13, -th - 2 + shrug * -6);
    ctx.lineTo(-sw + 11, -th - 2 + shrug * -6);
    ctx.quadraticCurveTo(-sw - 1, -th - 1 + shrug * -6, -sw, -th + 10);
    ctx.quadraticCurveTo(-sw - 3, -th * 0.45, -hw, 6);
    ctx.closePath();
    ctx.fillStyle = look.shirt;
    ctx.fill();
    ctx.save();
    ctx.clip();
    ctx.fillStyle = U.rgba('#000000', 0.12);
    ctx.fillRect(-sw - 6, -th - 10, sw * 0.75, th + 20);
    if (look.apron) {
      ctx.fillStyle = look.apron;
      ctx.beginPath();
      ctx.moveTo(-4, -th + 22); ctx.lineTo(sw + 6, -th + 22); ctx.lineTo(sw + 8, 10); ctx.lineTo(-8, 10); ctx.closePath(); ctx.fill();
      ctx.fillStyle = U.shade(look.apron, 0.12);
      ctx.fillRect(4, -th * 0.45, sw - 2, 14);
      ctx.strokeStyle = look.apron; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(-2, -th + 22); ctx.lineTo(-6, -th - 2); ctx.stroke();
    } else {
      // zipper + chest accent
      ctx.strokeStyle = U.rgba(look.shirt2 || '#ffffff', 0.55);
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(sw * 0.5, -th + 2); ctx.lineTo(sw * 0.42, 4); ctx.stroke();
      ctx.fillStyle = U.rgba(look.shirt2 || '#ffffff', 0.85);
      ctx.fillRect(-sw, -th * 0.62, sw * 2.2, 5);
    }
    ctx.restore();
    // hood / collar
    if (look.hood) {
      ctx.fillStyle = U.shade(look.shirt, -0.12);
      ctx.beginPath(); ctx.ellipse(-12, -th + 2, 18, 10, -0.3, 0, TAU); ctx.fill();
    } else if (!look.apron) {
      ctx.fillStyle = U.shade(look.shirt, -0.1);
      ctx.beginPath(); ctx.moveTo(-10, -th - 2); ctx.lineTo(10, -th - 2); ctx.lineTo(4, -th + 10); ctx.closePath(); ctx.fill();
    }
    // backpack strap
    if (look.pack && o.pack !== false) {
      ctx.strokeStyle = U.shade(look.pack, -0.25); ctx.lineWidth = 6; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(-6, -th + 2); ctx.quadraticCurveTo(10, -th * 0.6, 4, -th * 0.18); ctx.stroke();
    }
    ctx.restore();
    // neck
    ctx.strokeStyle = U.shade(look.skin, -0.12);
    ctx.lineWidth = 15;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(shX + 1, shY + 2); ctx.lineTo(lerp(shX, hdx, 0.55), lerp(shY, hdy, 0.55)); ctx.stroke();
    // head
    ctx.save();
    ctx.translate(hdx, hdy);
    ctx.rotate(hTilt + lean * 0.3);
    drawHeadLocal(ctx, look, o.face || {}, head.turn || 0, t, seed);
    ctx.restore();
    // trekking poles (front)
    if (walkPoles) pole(armF, 0);
    // front arm
    strokeLimb(ctx, armF, 13.5, 12.5, look.shirt);
    ctx.fillStyle = look.skin;
    ctx.beginPath(); ctx.arc(armF.x2, armF.y2, 7.5, 0, TAU); ctx.fill();
    if (o.gesture === 'point' || o.finger) {
      const fa = armF.a2;
      ctx.strokeStyle = look.skin; ctx.lineWidth = 4.6; ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(armF.x2 + Math.sin(fa) * 3, armF.y2 + Math.cos(fa) * 3);
      ctx.lineTo(armF.x2 + Math.sin(fa) * 15, armF.y2 + Math.cos(fa) * 15);
      ctx.stroke();
    }
    if (o.holdF) { ctx.save(); ctx.translate(armF.x2, armF.y2); o.holdF(ctx); ctx.restore(); }
    ctx.restore();

    const W_ = (lx, ly) => ({ x: x + lx * S * facing, y: y + ly * S });
    return {
      head: Object.assign(W_(hdx, hdy), { r: R * S }),
      top: W_(hdx, hdy - R - 14),
      mouth: W_(hdx + 10, hdy + 16),
      handF: W_(armF.x2, armF.y2),
      handB: W_(armB.x2, armB.y2),
      shoulder: W_(shF.x, shF.y),
      chest: W_(shX + 4, shY + 30),
      hip: W_(hipX, hipY),
      feet: { x, y },
      scale: S,
      facing,
      seed,
      headTilt: hTilt + lean * 0.3,
    };
  };
  function drawShoe(ctx, L, col) {
    ctx.save();
    ctx.translate(L.x2, L.y2);
    ctx.rotate(clamp((L.a2) * -0.25, -0.5, 0.5));
    ctx.fillStyle = col;
    ctx.beginPath(); ctx.ellipse(7, -2, 15, 7.5, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = U.shade(col, -0.3);
    ctx.fillRect(-7, 2.5, 28, 3);
    ctx.restore();
  }
  function roundRect(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  Art.roundRect = roundRect;

  /**
   * An emotion — a small luminous bean-shaped being from the narrator's mind.
   * o = { x, y (feet), s, color, face, arms:'idle'|'facepalm'|'wave'|'tap'|'cheer'|'point'|'hug'|'shrug',
   *       t, glow, facing, squash (-1..1), seed, alpha }
   */
  Art.emotion = (ctx, o = {}) => {
    const s = o.s || 1, t = o.t || 0, col = o.color || Art.EMO.wonder, seed = o.seed || 0;
    const facing = o.facing || 1;
    const sq = o.squash || 0;
    const bob = Math.sin(t * 2.2 + seed) * 2.5;
    ctx.save();
    if (o.alpha !== undefined) ctx.globalAlpha *= clamp(o.alpha);
    ctx.translate(o.x || 0, (o.y || 0));
    ctx.scale(s * facing, s);
    if (o.glow !== 0) Art.glow(ctx, 0, -46, 95, col, (o.glow === undefined ? 0.6 : o.glow) * 0.65);
    ctx.translate(0, bob);
    const bw = 30 * (1 + sq * 0.15), bh = 44 * (1 - sq * 0.15);
    // feet
    ctx.fillStyle = U.shade(col, -0.3);
    ctx.beginPath(); ctx.ellipse(-10, -2 - bob, 8, 4.5, 0, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.ellipse(11, -2 - bob, 8, 4.5, 0, 0, TAU); ctx.fill();
    // body: rounded bean
    const gr = ctx.createRadialGradient(-8, -bh * 1.5, 4, 0, -bh, bh * 1.4);
    gr.addColorStop(0, U.shade(col, 0.55));
    gr.addColorStop(0.5, col);
    gr.addColorStop(1, U.shade(col, -0.18));
    ctx.fillStyle = gr;
    ctx.beginPath();
    ctx.moveTo(0, -bh * 2.05);
    ctx.bezierCurveTo(bw * 1.15, -bh * 2.05, bw * 1.1, -2, 0, -2);
    ctx.bezierCurveTo(-bw * 1.1, -2, -bw * 1.15, -bh * 2.05, 0, -bh * 2.05);
    ctx.fill();
    // arms
    const arm = o.arms || 'idle';
    ctx.strokeStyle = U.shade(col, -0.12);
    ctx.lineWidth = 7;
    ctx.lineCap = 'round';
    const A = (x0, y0, x1, y1, cx, cy) => { ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(cx, cy, x1, y1); ctx.stroke(); };
    const sY = -bh * 0.95;
    let coverEyes = false;
    if (arm === 'facepalm') { A(bw * 0.8, sY, 6, -bh * 1.32, bw * 1.3, -bh * 1.3); A(-bw * 0.85, sY, -bw * 1.2, -8, -bw * 1.3, sY * 0.5); coverEyes = true; }
    else if (arm === 'wave') { const w = Math.sin(t * 9) * 6; A(bw * 0.8, sY, bw * 1.3 + w, -bh * 2.0, bw * 1.6, -bh * 1.2); A(-bw * 0.85, sY, -bw * 1.2, -8, -bw * 1.3, sY * 0.5); }
    else if (arm === 'tap') { const k = Math.max(0, Math.sin(t * 7)); A(bw * 0.8, sY, bw * 1.9 + k * 6, -bh * 1.35 - k * 4, bw * 1.5, -bh * 1.0); A(-bw * 0.85, sY, -bw * 1.2, -8, -bw * 1.3, sY * 0.5); }
    else if (arm === 'cheer') { A(bw * 0.8, sY, bw * 1.2, -bh * 2.3, bw * 1.6, -bh * 1.5); A(-bw * 0.8, sY, -bw * 1.2, -bh * 2.3, -bw * 1.6, -bh * 1.5); }
    else if (arm === 'point') { A(bw * 0.8, sY, bw * 2.0, -bh * 1.15, bw * 1.4, -bh * 1.0); A(-bw * 0.85, sY, -bw * 1.2, -8, -bw * 1.3, sY * 0.5); }
    else if (arm === 'hug') { A(bw * 0.8, sY, bw * 0.1, -bh * 0.75, bw * 1.3, -bh * 0.5); A(-bw * 0.8, sY, -bw * 0.1, -bh * 0.7, -bw * 1.3, -bh * 0.5); }
    else if (arm === 'shrug') { A(bw * 0.8, sY, bw * 1.5, -bh * 1.35, bw * 1.5, -bh * 0.7); A(-bw * 0.8, sY, -bw * 1.5, -bh * 1.35, -bw * 1.5, -bh * 0.7); }
    else { A(bw * 0.85, sY, bw * 1.2, -8, bw * 1.3, sY * 0.5); A(-bw * 0.85, sY, -bw * 1.2, -8, -bw * 1.3, sY * 0.5); }
    // face
    const f = Object.assign({ smile: 0.4, eyes: 'open' }, o.face || {});
    const fy = -bh * 1.35;
    const ink = U.shade(col, -0.75);
    const bl = f.blink !== undefined ? f.blink : U.blink(t, seed + 3);
    if (!coverEyes) {
      drawEye(ctx, -9, fy, 1.15, f.eyes, Object.assign({}, f, { blink: bl, skinLid: col }), ink);
      drawEye(ctx, 9, fy, 1.15, f.eyes, Object.assign({}, f, { blink: bl, skinLid: col }), ink);
      ctx.strokeStyle = ink; ctx.lineWidth = 2.6;
      const b = f.brow || 0, by = fy - 12 - (f.browUp || 0) * 4;
      ctx.beginPath(); ctx.moveTo(-14, by - 2 * b); ctx.lineTo(-5, by + 2 * b); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(5, by + 2 * b); ctx.lineTo(14, by - 2 * b); ctx.stroke();
    }
    const ms = clamp(f.smile, -1, 1);
    let mo = f.open || 0;
    if (f.talk) mo = Math.max(mo, f.talk * (0.2 + 0.6 * Math.abs(U.noise1(t * 9, seed))));
    ctx.strokeStyle = ink; ctx.fillStyle = U.shade(col, -0.6); ctx.lineWidth = 2.6;
    const my = fy + 13;
    if (mo > 0.08) { ctx.beginPath(); ctx.ellipse(0, my + 2, 6, 3 + mo * 6, 0, 0, TAU); ctx.fill(); }
    else { ctx.beginPath(); ctx.moveTo(-7, my - ms * 2); ctx.quadraticCurveTo(0, my + ms * 8, 7, my - ms * 2); ctx.stroke(); }
    if (f.blush) { ctx.save(); ctx.globalAlpha *= f.blush * 0.5; ctx.fillStyle = '#ff5e78'; ctx.beginPath(); ctx.ellipse(-16, fy + 9, 5, 3, 0, 0, TAU); ctx.ellipse(16, fy + 9, 5, 3, 0, 0, TAU); ctx.fill(); ctx.restore(); }
    // highlight
    ctx.fillStyle = 'rgba(255,255,255,0.45)';
    ctx.beginPath(); ctx.ellipse(-bw * 0.45, -bh * 1.75, 6, 3.5, -0.6, 0, TAU); ctx.fill();
    ctx.restore();
    return { head: { x: (o.x || 0), y: (o.y || 0) + (fy + bob) * s }, top: { x: o.x || 0, y: (o.y || 0) + (-bh * 2.1 + bob) * s } };
  };

  /* ======================================================================
     FLOWERS
     ====================================================================== */
  /** THE flower: luminous magenta-rose petals, golden phyllotaxis heart */
  Art.FLOWER = { petal: '#d4185e', tip: '#ff8db0', inner: '#7c0d3b', center: '#ffc23d', seed: '#b8620f', stem: '#3c7a37', leaf: '#4d9844' };
  const GOLDEN = Math.PI * (3 - Math.sqrt(5)); // 137.507764°
  Art.GOLDEN_ANGLE = GOLDEN;
  /** phyllotaxis seed head: n seeds spaced c*sqrt(i) at the golden angle */
  Art.phyllotaxis = (ctx, { x = 0, y = 0, n = 89, c = 2.2, size = 1.4, rot = 0, color = '#b8620f', color2 = null, grow = 1, alpha = 1 } = {}) => {
    ctx.save();
    ctx.globalAlpha *= alpha;
    const m = Math.floor(n * clamp(grow));
    for (let i = 1; i <= m; i++) {
      const a = i * GOLDEN + rot, r = c * Math.sqrt(i);
      const k = i / n;
      ctx.fillStyle = color2 ? U.mix(color, color2, k) : color;
      ctx.beginPath();
      ctx.arc(x + Math.cos(a) * r, y + Math.sin(a) * r, size * (0.6 + 0.6 * k), 0, TAU);
      ctx.fill();
    }
    ctx.restore();
  };
  function petalPath(ctx, L, w) {
    ctx.moveTo(0, 0);
    ctx.bezierCurveTo(w, -L * 0.25, w * 1.05, -L * 0.82, 0, -L);
    ctx.bezierCurveTo(-w * 1.05, -L * 0.82, -w, -L * 0.25, 0, 0);
  }
  /**
   * Art.flower(ctx, opts) → { head:{x,y}, r }
   *  x, y      base of stem (ground)
   *  s         scale (1 → ~190px tall)
   *  kind      'hero' | 'daisy' | 'tulip' | 'bell' | 'rose' | 'wild'
   *  bloom     0 (bud) .. 1 (open)
   *  sat       saturation 0..1 (0 = grey, "invisible")
   *  glow      0..1 halo
   *  sway      wind amount; t time
   *  droop     0..1 wilting
   *  face      0 (side, squashed head) .. 1 (facing camera)
   *  stemH     stem height (unscaled px, default 150)
   *  colors    override palette {petal, tip, inner, center, seed, stem, leaf}
   *  dust      0..1 neglected / dusty look
   */
  Art.flower = (ctx, o = {}) => {
    const s = o.s || 1, t = o.t || 0, seed = o.seed || 1;
    const bloom = o.bloom === undefined ? 1 : clamp(o.bloom);
    const sat = o.sat === undefined ? 1 : clamp(o.sat);
    const droop = clamp(o.droop || 0);
    const kind = o.kind || 'hero';
    const face = o.face === undefined ? 0.75 : clamp(o.face);
    const C0 = Object.assign({}, Art.FLOWER, o.colors || {});
    const C = {};
    for (const k in C0) C[k] = sat < 1 ? U.desat(C0[k], 1 - sat) : C0[k];
    if (o.dust) for (const k in C) C[k] = U.mix(C[k], '#b9ad98', o.dust * 0.55);
    const x = o.x || 0, y = o.y || 0;
    const stemH = (o.stemH || 150) * s;
    const sw = (o.sway === undefined ? 1 : o.sway) * U.wind(t, x, seed) * 9 * s;
    const hx = x + sw + droop * 34 * s, hy = y - stemH * (1 - droop * 0.28);
    ctx.save();
    if (o.alpha !== undefined) ctx.globalAlpha *= clamp(o.alpha);
    // stem
    ctx.strokeStyle = C.stem;
    ctx.lineCap = 'round';
    ctx.lineWidth = 5 * s;
    ctx.beginPath();
    ctx.moveTo(x, y);
    const cx = x + sw * 0.25 - droop * 6 * s, cy = y - stemH * 0.55;
    ctx.quadraticCurveTo(cx, cy, hx, hy);
    ctx.stroke();
    // leaves
    const leaf = (k, dir, len) => {
      const lx = lerp(x, hx, k * k) + (cx - x) * k * (1 - k) * 2, ly = lerp(y, hy, k);
      ctx.save();
      ctx.translate(lx, ly);
      ctx.rotate(dir * (0.9 + droop * 0.6) + sw * 0.004);
      ctx.fillStyle = C.leaf;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.quadraticCurveTo(len * 0.5 * dir, -len * 0.45, len * dir, 0);
      ctx.quadraticCurveTo(len * 0.5 * dir, len * 0.18, 0, 0);
      ctx.fill();
      ctx.strokeStyle = U.shade(C.leaf, -0.2); ctx.lineWidth = 1.4 * s;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(len * 0.5 * dir, -len * 0.18, len * 0.9 * dir, -len * 0.02); ctx.stroke();
      ctx.restore();
    };
    leaf(0.3, 1, 44 * s);
    leaf(0.48, -1, 38 * s);
    // glow
    const headR = 52 * s;
    if (o.glow) {
      Art.glow(ctx, hx, hy, headR * 4.2, C.tip, o.glow * 0.45);
      Art.glow(ctx, hx, hy, headR * 1.8, '#fff2d6', o.glow * 0.35);
    }
    // head
    ctx.save();
    ctx.translate(hx, hy);
    ctx.rotate(sw * 0.006 + droop * 1.25);
    const sq = lerp(0.5, 1, face);
    if (kind === 'tulip') {
      const L = 46 * s * (0.4 + 0.6 * bloom);
      const gr = ctx.createLinearGradient(0, 0, 0, -L);
      gr.addColorStop(0, C.inner); gr.addColorStop(0.4, C.petal); gr.addColorStop(1, C.tip);
      ctx.fillStyle = gr;
      for (const a of [-0.38 * bloom, 0.38 * bloom, 0]) {
        ctx.save(); ctx.rotate(a); ctx.beginPath(); petalPath(ctx, L, L * 0.42); ctx.fill(); ctx.restore();
      }
    } else if (kind === 'bell') {
      for (let i = 0; i < 3; i++) {
        ctx.save();
        ctx.translate((i - 1) * 22 * s, 10 * s + Math.abs(i - 1) * 8 * s);
        ctx.fillStyle = i === 1 ? C.petal : U.shade(C.petal, -0.1);
        ctx.beginPath();
        ctx.moveTo(-10 * s, 0); ctx.quadraticCurveTo(-12 * s, 22 * s, -15 * s, 28 * s);
        ctx.lineTo(15 * s, 28 * s); ctx.quadraticCurveTo(12 * s, 22 * s, 10 * s, 0);
        ctx.quadraticCurveTo(0, -6 * s, -10 * s, 0); ctx.fill();
        ctx.restore();
      }
    } else if (kind === 'rose') {
      const R = 30 * s * (0.5 + 0.5 * bloom);
      for (let i = 6; i >= 0; i--) {
        const k = i / 6;
        ctx.fillStyle = U.mix(C.inner, C.petal, k);
        ctx.beginPath();
        ctx.ellipse(Math.cos(i * 2.1) * R * 0.12, Math.sin(i * 2.1) * R * 0.1, R * (0.3 + 0.7 * k), R * (0.3 + 0.7 * k) * sq, i * 0.7, 0, TAU);
        ctx.fill();
        ctx.strokeStyle = U.shade(C.inner, -0.2); ctx.lineWidth = 1.2 * s;
        ctx.stroke();
      }
    } else {
      // radial flowers: hero, daisy, wild
      const n = o.petals || (kind === 'daisy' ? 14 : kind === 'wild' ? 6 : 8);
      const be = U.E.outCubic(bloom);
      const L = (kind === 'daisy' ? 40 : 50) * s * (0.25 + 0.75 * be);
      const pw = (kind === 'daisy' ? 7 : 19) * s * (0.5 + 0.5 * be);
      const rot = (o.rot || 0) + seed;
      ctx.scale(1, sq);
      const gr = ctx.createRadialGradient(0, 0, 0, 0, 0, L);
      gr.addColorStop(0, C.inner);
      gr.addColorStop(0.3, C.petal);
      gr.addColorStop(1, C.tip);
      // back ring
      if (kind === 'hero') {
        ctx.fillStyle = U.shade(C.petal, -0.25);
        for (let i = 0; i < n; i++) {
          ctx.save(); ctx.rotate(rot + (i + 0.5) / n * TAU); ctx.beginPath(); petalPath(ctx, L * 0.92, pw * 0.9); ctx.fill(); ctx.restore();
        }
      }
      ctx.fillStyle = gr;
      for (let i = 0; i < n; i++) {
        const wob = Math.sin(t * 1.6 + i * 1.3 + seed) * 0.03;
        ctx.save(); ctx.rotate(rot + i / n * TAU + wob); ctx.beginPath(); petalPath(ctx, L, pw); ctx.fill(); ctx.restore();
      }
      // petal veins
      if (kind === 'hero' && s > 0.6) {
        ctx.strokeStyle = U.rgba(C.inner, 0.35); ctx.lineWidth = 1.1 * s;
        for (let i = 0; i < n; i++) {
          ctx.save(); ctx.rotate(rot + i / n * TAU); ctx.beginPath(); ctx.moveTo(0, -L * 0.2); ctx.lineTo(0, -L * 0.75); ctx.stroke(); ctx.restore();
        }
      }
      // center
      const rc = (kind === 'daisy' ? 0.32 : 0.3) * L + 3 * s;
      ctx.fillStyle = C.center;
      ctx.beginPath(); ctx.arc(0, 0, rc, 0, TAU); ctx.fill();
      if (s * bloom > 0.35) Art.phyllotaxis(ctx, { n: kind === 'hero' ? 55 : 34, c: rc / Math.sqrt(kind === 'hero' ? 62 : 40), size: 0.9 * s, rot: t * 0.05, color: C.seed, color2: U.shade(C.center, -0.1) });
      // bud sepals when barely open
      if (bloom < 0.45) {
        ctx.fillStyle = C.leaf;
        const k = 1 - bloom / 0.45;
        for (let i = 0; i < 5; i++) { ctx.save(); ctx.rotate(i / 5 * TAU + 0.3); ctx.globalAlpha *= k; ctx.beginPath(); petalPath(ctx, L * 1.15, pw * 0.8); ctx.fill(); ctx.restore(); }
      }
    }
    ctx.restore();
    // dust & cobweb for neglected flowers
    if (o.dust > 0.2) {
      ctx.save();
      ctx.globalAlpha *= o.dust * 0.7;
      ctx.strokeStyle = '#e8e2d6'; ctx.lineWidth = 0.9;
      const wx = hx + 6 * s, wy = hy + 30 * s;
      for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(wx, wy); ctx.lineTo(wx + Math.cos(i * 0.5 - 1.2) * 46 * s, wy + Math.sin(i * 0.5 - 1.2) * 46 * s); ctx.stroke(); }
      for (let r = 12; r < 46; r += 11) { ctx.beginPath(); ctx.arc(wx, wy, r * s, -1.2, 0.8); ctx.stroke(); }
      ctx.restore();
    }
    ctx.restore();
    return { head: { x: hx, y: hy }, r: headR };
  };
  /** terracotta pot. (x,y) = bottom center */
  Art.pot = (ctx, x, y, w = 70, h = 60, color = '#c66a43') => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x - w * 0.36, y); ctx.lineTo(x + w * 0.36, y); ctx.lineTo(x + w * 0.48, y - h * 0.8); ctx.lineTo(x - w * 0.48, y - h * 0.8); ctx.closePath(); ctx.fill();
    ctx.fillStyle = U.shade(color, 0.1);
    roundRect(ctx, x - w * 0.55, y - h, w * 1.1, h * 0.24, 4); ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,0.15)';
    ctx.beginPath(); ctx.moveTo(x - w * 0.36, y); ctx.lineTo(x - w * 0.1, y); ctx.lineTo(x - w * 0.16, y - h * 0.76); ctx.lineTo(x - w * 0.46, y - h * 0.76); ctx.closePath(); ctx.fill();
    return { top: { x, y: y - h } };
  };

  /* ======================================================================
     TEXT — captions (narration), speech bubbles, titles, handwriting.
     Captions are deferred to an overlay pass so they sit above post-FX.
     ====================================================================== */
  Art._overlay = [];
  Art._alpha = 1;
  /** defer a draw call to the overlay pass (after vignette/grain/letterbox) */
  Art.later = (fn) => { Art._overlay.push({ fn, a: Art._alpha }); };
  const wrapCache = new Map();
  Art.wrap = (ctx, text, maxW) => {
    const key = ctx.font + '|' + maxW + '|' + text;
    let lines = wrapCache.get(key);
    if (lines) return lines;
    lines = [];
    for (const para of String(text).split('\n')) {
      const words = para.split(' ');
      let line = '';
      for (const w of words) {
        const test = line ? line + ' ' + w : w;
        if (ctx.measureText(test).width > maxW && line) { lines.push(line); line = w; } else line = test;
      }
      lines.push(line);
    }
    // balance two-line captions: avoid a lonely last word
    if (lines.length === 2 && String(text).indexOf('\n') < 0) {
      const all = lines.join(' ').split(' ');
      let best = lines, bestD = Infinity;
      for (let i = 1; i < all.length; i++) {
        const a = all.slice(0, i).join(' '), b = all.slice(i).join(' ');
        const wa = ctx.measureText(a).width, wb = ctx.measureText(b).width;
        if (wa > maxW || wb > maxW) continue;
        const d = Math.abs(wa - wb);
        if (d < bestD) { bestD = d; best = [a, b]; }
      }
      lines = best;
    }
    if (wrapCache.size > 4000) wrapCache.clear();
    wrapCache.set(key, lines);
    return lines;
  };
  Art.clearTextCache = () => wrapCache.clear();

  /**
   * Narration caption (deferred to overlay). By default sits centered in the
   * bottom letterbox bar. o = { alpha, reveal (0..1 word-by-word), y, size,
   * maxW, color, style:'italic', weight, family, now (draw immediately) }
   */
  Art.caption = (ctx, text, o = {}) => {
    const alpha = o.alpha === undefined ? 1 : o.alpha;
    if (alpha <= 0.003 || !text) return;
    const draw = (c) => {
      const size = o.size || 46;
      c.save();
      const base = c.globalAlpha;
      c.font = Art.font(size, o.family || 'serif', o.weight || 500, o.style || 'italic');
      c.textBaseline = 'middle';
      c.textAlign = 'left';
      const maxW = o.maxW || 1560;
      const lines = Art.wrap(c, text, maxW);
      const lh = size * 1.18;
      const cy = o.y === undefined ? 1011 - (Art.captionLift || 0) : o.y;
      const y0 = cy - ((lines.length - 1) * lh) / 2;
      const reveal = o.reveal === undefined ? 1 : o.reveal;
      const lifted = o.y === undefined ? clamp((Art.captionLift || 0) / 40) : 0;
      if (lifted > 0.01) {
        // a soft backing keeps a caption legible while it is lifted over the picture
        let mw = 0;
        for (const l of lines) mw = Math.max(mw, c.measureText(l).width);
        c.save();
        c.globalAlpha = base * alpha * 0.5 * lifted;
        c.fillStyle = '#000';
        roundRect(c, (o.x === undefined ? W / 2 : o.x) - (o.align === 'left' ? 24 : mw / 2 + 28), y0 - lh * 0.62, mw + 56, lh * (lines.length + 0.24), 18);
        c.fill();
        c.restore();
      }
      const totalWords = lines.reduce((n, l) => n + l.split(' ').length, 0);
      let wi = 0;
      c.shadowColor = 'rgba(0,0,0,0.55)';
      c.shadowBlur = o.shadow === false ? 0 : 14;
      c.fillStyle = o.color || '#f7efe2';
      const space = c.measureText(' ').width;
      lines.forEach((line, li) => {
        const words = line.split(' ');
        const lw = c.measureText(line).width;
        let x = (o.x === undefined ? W / 2 : o.x) - (o.align === 'left' ? 0 : lw / 2);
        const y = y0 + li * lh;
        for (const w of words) {
          const k = clamp(reveal * (totalWords + 2.5) - wi);
          if (k > 0) {
            c.globalAlpha = base * alpha * U.smooth(k);
            c.fillText(w, x, y + (1 - U.smooth(k)) * 6);
          }
          x += c.measureText(w).width + space;
          wi++;
        }
      });
      c.restore();
    };
    if (o.now) draw(ctx); else Art.later(draw);
  };
  /** schedule captions: cues = [[t0, t1, text, opts?], ...] */
  Art.captions = (ctx, t, cues, o = {}) => {
    for (const cue of cues) {
      const [t0, t1, text, co] = cue;
      if (t < t0 - 0.01 || t > t1 + 0.01) continue;
      const a = U.fade(t, t0, t1, 0.45, 0.6);
      const words = text.split(' ').length;
      const reveal = U.prog(t, t0, t0 + Math.min(2.2, 0.25 + words * 0.11));
      Art.caption(ctx, text, Object.assign({}, o, co || {}, { alpha: a * (o.alpha === undefined ? 1 : o.alpha), reveal }));
    }
  };

  /**
   * Speech bubble. (x,y) = bubble center. (tx,ty) = tail tip (speaker's mouth).
   * o = { alpha, pop 0..1 (scale-in), reveal 0..1 (typewriter), size, maxW,
   *       style: 'speech'|'thought'|'shout'|'whisper', bg, fg, family, weight, align }
   * returns box {x,y,w,h}
   */
  Art.bubble = (ctx, text, o = {}) => {
    const alpha = o.alpha === undefined ? 1 : o.alpha;
    if (alpha <= 0.003) return null;
    const size = o.size || 34;
    const style = o.style || 'speech';
    const fam = o.family || (style === 'thought' ? 'hand' : 'sans');
    ctx.save();
    ctx.font = Art.font(fam === 'hand' ? size * 1.25 : size, fam, o.weight || (fam === 'hand' ? 700 : 800));
    const lines = Art.wrap(ctx, text, o.maxW || 540);
    const lh = (fam === 'hand' ? size * 1.25 : size) * 1.22;
    let tw = 0;
    for (const l of lines) tw = Math.max(tw, ctx.measureText(l).width);
    const padX = style === 'thought' ? 40 : 28, padY = style === 'thought' ? 30 : 20;
    const bw = tw + padX * 2, bh = lines.length * lh + padY * 2;
    const x = o.x, y = o.y;
    const tx = o.tx === undefined ? x : o.tx, ty = o.ty === undefined ? y + bh : o.ty;
    const pop = o.pop === undefined ? 1 : clamp(o.pop);
    const sc = lerp(0.55, 1, U.E.outBack(pop));
    const bg = o.bg || '#fffaf1', fg = o.fg || '#2b2530';
    const L = x - bw / 2, T = y - bh / 2;
    const reveal = o.reveal === undefined ? 1 : o.reveal;
    // speech balloons hug the text as it types (growing from the final top-left so words never move)
    let fw = bw, fh = bh;
    if ((style === 'speech' || style === 'whisper') && o.fit !== false && reveal < 1) {
      let rem = reveal * lines.reduce((n, l) => n + l.length, 0), cw = 0, rows = 0;
      for (let i = 0; i < lines.length && rem > 0; i++) {
        const ln = lines[i], k = Math.min(ln.length, rem), kk = Math.floor(k);
        const lw = ctx.measureText(ln).width;
        const part = ctx.measureText(ln.slice(0, kk)).width + (kk < ln.length ? (k - kk) * ctx.measureText(ln[kk]).width : 0);
        cw = Math.max(cw, (tw - lw) / 2 + part);
        rows = i + U.smooth(Math.min(1, k / 3));
        rem -= ln.length;
      }
      fw = tx <= L + bw * 0.55 ? Math.min(bw, Math.max(cw + padX * 2, padX * 2 + 110)) : bw;
      fh = Math.min(bh, Math.max(1, rows) * lh + padY * 2);
    }
    // pop springs out of the tail tip
    ctx.globalAlpha *= alpha * clamp(pop * 4);
    ctx.translate(tx, ty);
    ctx.scale(sc, sc);
    ctx.translate(-tx, -ty);
    ctx.shadowColor = 'rgba(0,0,0,0.28)';
    ctx.shadowBlur = 18;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = bg;
    if (style === 'thought') {
      ctx.beginPath();
      const n = Math.max(8, Math.round((bw + bh) / 46));
      for (let i = 0; i < n; i++) {
        const a = (i / n) * TAU;
        const px = x + Math.cos(a) * bw * 0.5, py = y + Math.sin(a) * bh * 0.5;
        const r = 26 + U.hash(i, 3) * 12;
        ctx.moveTo(px + r, py); ctx.arc(px, py, r, 0, TAU);
      }
      ctx.ellipse(x, y, bw * 0.5, bh * 0.5, 0, 0, TAU);
      ctx.fill();
      // trailing dots to the thinker
      for (let i = 0; i < 3; i++) {
        const k = 0.35 + i * 0.25;
        const px = lerp(x, tx, k), py = lerp(y + bh * 0.45, ty, k);
        ctx.beginPath(); ctx.arc(px, py, 12 - i * 3.5, 0, TAU); ctx.fill();
      }
    } else if (style === 'shout') {
      ctx.beginPath();
      const n = 22;
      for (let i = 0; i <= n; i++) {
        const a = (i / n) * TAU;
        const rr = i % 2 ? 0.5 : 0.62;
        const px = x + Math.cos(a) * bw * rr, py = y + Math.sin(a) * bh * (rr + 0.08);
        i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
      }
      ctx.closePath();
      ctx.fill();
    } else {
      roundRect(ctx, L, T, fw, fh, Math.min(30, fh / 2));
      ctx.fill();
      // tail
      const inset = Math.min(40, fw / 2);
      const ax = clamp(tx, L + inset, L + fw - inset);
      const below = ty > T + fh / 2;
      const by = below ? T + fh - 2 : T + 2;
      ctx.beginPath();
      ctx.moveTo(ax - 18, by);
      ctx.quadraticCurveTo(lerp(ax, tx, 0.5) - 4, lerp(by, ty, 0.55), tx, ty);
      ctx.quadraticCurveTo(lerp(ax, tx, 0.5) + 8, lerp(by, ty, 0.4), ax + 16, by);
      ctx.closePath();
      ctx.fill();
      if (style === 'whisper') {
        ctx.shadowColor = 'transparent';
        ctx.setLineDash([8, 7]);
        ctx.strokeStyle = U.rgba(fg, 0.5);
        ctx.lineWidth = 2;
        roundRect(ctx, L + 6, T + 6, fw - 12, fh - 12, Math.min(24, fh / 2));
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
    ctx.shadowColor = 'transparent';
    // text with typewriter reveal
    const total = lines.reduce((n, l) => n + l.length, 0);
    let shown = Math.floor(reveal * total + 0.0001);
    ctx.fillStyle = fg;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    lines.forEach((line, i) => {
      if (shown <= 0) return;
      const part = line.slice(0, shown);
      shown -= line.length;
      const lw = ctx.measureText(line).width;
      ctx.fillText(part, x - lw / 2, T + padY + lh * (i + 0.5) + (fam === 'hand' ? 2 : 1));
    });
    ctx.restore();
    return { x: L, y: T, w: bw, h: bh, cur: { w: fw, h: fh } };
  };
  /**
   * schedule bubbles: cues = [[t0, t1, text, {x,y,tx,ty,who,...}], ...]
   * returns { talking: {who: 0..1} } so mouths can sync to the typewriter.
   */
  Art.bubbles = (ctx, t, cues) => {
    const talking = {};
    for (const cue of cues) {
      const [t0, t1, text, bo] = cue;
      if (t < t0 || t > t1) continue;
      const len = text.length;
      const typeDur = Math.min(2.4, 0.15 + len * 0.032);
      const pop = U.prog(t, t0, t0 + 0.4);
      const alpha = U.fade(t, t0, t1, 0.12, 0.35);
      const reveal = U.prog(t, t0 + 0.08, t0 + 0.08 + typeDur);
      if (bo && bo.who) talking[bo.who] = Math.max(talking[bo.who] || 0, reveal < 1 ? 1 : 0);
      Art.bubble(ctx, text, Object.assign({}, bo, { alpha: alpha * (bo && bo.alpha !== undefined ? bo.alpha : 1), pop, reveal }));
    }
    return { talking };
  };
  /** is someone talking at time t according to a cue list? → 0..1 */
  Art.talkingAt = (t, cues, who) => {
    for (const [t0, t1, text, bo] of cues) {
      if (!bo || bo.who !== who) continue;
      const typeDur = Math.min(2.4, 0.15 + text.length * 0.032);
      if (t >= t0 + 0.05 && t <= t0 + 0.1 + typeDur) return 1;
    }
    return 0;
  };

  /**
   * Display title with per-letter reveal. o = { x, y, size, family, style,
   * weight, color, alpha, reveal 0..1, glow (color), align, spacing }
   */
  Art.title = (ctx, text, o = {}) => {
    const alpha = o.alpha === undefined ? 1 : o.alpha;
    if (alpha <= 0.003) return;
    const draw = (c) => {
      const size = o.size || 96;
      c.save();
      const base = c.globalAlpha;
      c.font = Art.font(size, o.family || 'serif', o.weight || 500, o.style || 'italic');
      c.textBaseline = 'middle';
      c.textAlign = 'left';
      const spacing = o.spacing || 0;
      const chars = [...text];
      const widths = chars.map((ch) => c.measureText(ch).width + spacing);
      const total = c.measureText(text).width + spacing * (chars.length - 1);
      let x = (o.x === undefined ? W / 2 : o.x) - (o.align === 'left' ? 0 : o.align === 'right' ? total : total / 2);
      const y = o.y === undefined ? H / 2 : o.y;
      const reveal = o.reveal === undefined ? 1 : o.reveal;
      const n = chars.length;
      let prefix = '';
      if (o.glow) { c.shadowColor = o.glow; c.shadowBlur = size * 0.45; }
      c.fillStyle = o.color || '#f7efe2';
      for (let i = 0; i < n; i++) {
        const k = clamp(reveal * (n + 6) - i * 1.0, 0, 6) / 6;
        const px = (o.align === 'left' ? 0 : 0) + x + (spacing ? 0 : 0);
        if (k > 0) {
          c.globalAlpha = base * alpha * U.smooth(k);
          const cx = spacing ? px : (o.x === undefined ? W / 2 : o.x) - (o.align === 'left' ? 0 : o.align === 'right' ? total : total / 2) + c.measureText(prefix).width;
          c.fillText(chars[i], cx, y + (1 - U.smooth(k)) * size * 0.12);
        }
        prefix += chars[i];
        x += widths[i];
      }
      c.restore();
    };
    if (o.now === false) Art.later(draw); else draw(ctx);
  };
  /** handwritten line (Caveat), written on letter by letter with slight wobble */
  Art.hand = (ctx, text, o = {}) => {
    const alpha = o.alpha === undefined ? 1 : o.alpha;
    if (alpha <= 0.003) return;
    if (o.now === false) { const o2 = Object.assign({}, o, { now: true }); Art.later((c) => Art.hand(c, text, o2)); return; }
    const size = o.size || 56;
    ctx.save();
    ctx.font = Art.font(size, 'hand', o.weight || 700);
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    const lines = Art.wrap(ctx, text, o.maxW || 1200);
    const lh = size * 1.1;
    const reveal = o.reveal === undefined ? 1 : o.reveal;
    const total = lines.reduce((n, l) => n + l.length, 0);
    let shown = reveal * total;
    ctx.fillStyle = o.color || '#fff4dd';
    if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = size * 0.5; }
    const y0 = (o.y === undefined ? H / 2 : o.y) - ((lines.length - 1) * lh) / 2;
    lines.forEach((line, li) => {
      const lw = ctx.measureText(line).width;
      const x0 = (o.x === undefined ? W / 2 : o.x) - (o.align === 'left' ? 0 : lw / 2);
      for (let i = 0; i < line.length; i++) {
        const k = clamp(shown - i);
        if (k <= 0) break;
        const px = x0 + ctx.measureText(line.slice(0, i)).width;
        ctx.save();
        ctx.globalAlpha *= alpha * k;
        ctx.translate(px, y0 + li * lh + Math.sin(i * 1.7 + li) * 2);
        ctx.rotate(Math.sin(i * 2.3 + li) * 0.04);
        ctx.fillText(line[i], 0, 0);
        ctx.restore();
      }
      shown -= line.length;
    });
    ctx.restore();
  };

  g.Art = Art;
})(window);
