'use strict';
// Effects drawn over the fantasy stills. Every effect is a pure function of
// time (particles come from seeded random numbers), so any frame can be
// rendered on its own.

const path = require('path');
const lib = (p) => require(path.join(__dirname, '..', 'render', 'lib', p));
const S = lib('stage');
const { clamp, lerp, smooth, rng, fbm } = lib('util');

const W = S.W, H = S.H;
const easeIn = (u) => u * u;

function withAdd(ctx, fn) {
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'lighter'; fn(); ctx.restore();
}

// ---------------------------------------------------------------- particles
// Falling snow (or ash). depth gives near flakes that are bigger, faster, softer.
function snow(ctx, t, { n = 140, seed = 1, speed = 90, wind = 30, alpha = 0.8, size = 3.2 } = {}) {
  const r = rng(seed);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  for (let i = 0; i < n; i++) {
    const x0 = r() * W, y0 = r() * H, d = 0.35 + r() * 0.65, ph = r() * 6.28;
    const y = (y0 + t * speed * d) % (H + 40) - 20;
    const x = (x0 + t * wind * d + Math.sin(t * 0.9 * d + ph) * 18 * d + W) % W;
    const s = size * d;
    ctx.fillStyle = `rgba(255,255,255,${alpha * (0.35 + 0.65 * d)})`;
    ctx.beginPath(); ctx.arc(x, y, s, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

// Floating dust or light motes, drifting and twinkling.
function motes(ctx, t, { n = 60, seed = 2, rgb = [255, 220, 160], alpha = 0.7, area = { x0: 0, x1: W, y0: 0, y1: H }, rise = 12, size = 2.6 } = {}) {
  const r = rng(seed);
  withAdd(ctx, () => {
    for (let i = 0; i < n; i++) {
      const x0 = area.x0 + r() * (area.x1 - area.x0), y0 = area.y0 + r() * (area.y1 - area.y0), ph = r() * 6.28, d = 0.4 + r() * 0.6;
      const y = area.y0 + ((y0 - area.y0 - t * rise * d) % (area.y1 - area.y0) + (area.y1 - area.y0)) % (area.y1 - area.y0);
      const x = x0 + Math.sin(t * 0.5 + ph) * 20 * d;
      const tw = 0.45 + 0.55 * Math.sin(t * (1.2 + d) + ph * 3);
      const s = size * d * 2.4;
      const g = ctx.createRadialGradient(x, y, 0, x, y, s);
      g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${alpha * tw})`); g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      ctx.fillStyle = g; ctx.fillRect(x - s, y - s, s * 2, s * 2);
    }
  });
}

// Star twinkles inside an ellipse (stars caught in her hair).
function twinkles(ctx, t, { cx, cy, rx, ry, n = 40, seed = 7, rgb = [255, 226, 150], alpha = 1, k = 1 } = {}) {
  const r = rng(seed);
  withAdd(ctx, () => {
    for (let i = 0; i < n; i++) {
      const a = r() * Math.PI * 2, rr = Math.sqrt(r());
      const x = cx + Math.cos(a) * rx * rr, y = cy + Math.sin(a) * ry * rr;
      const born = r() * 1.2;
      const on = clamp((k * 1.4 - born) / 0.3);
      if (on <= 0) continue;
      const tw = 0.5 + 0.5 * Math.sin(t * (2 + r() * 3) + r() * 6.28);
      const s = (3 + r() * 6) * (0.6 + 0.4 * tw) * on;
      const A = alpha * on * (0.5 + 0.5 * tw);
      const g = ctx.createRadialGradient(x, y, 0, x, y, s * 3);
      g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${A})`); g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      ctx.fillStyle = g; ctx.fillRect(x - s * 3, y - s * 3, s * 6, s * 6);
      ctx.strokeStyle = `rgba(255,250,235,${A * 0.8})`; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(x - s * 2.2, y); ctx.lineTo(x + s * 2.2, y); ctx.moveTo(x, y - s * 2.2); ctx.lineTo(x, y + s * 2.2); ctx.stroke();
    }
  });
}

// ---------------------------------------------------------------- light
// God rays: soft wedges from a point, breathing slowly.
function rays(ctx, t, { x = W / 2, y = 0, angle = Math.PI / 2, spread = 0.9, n = 7, len = 2200, rgb = [255, 228, 170], alpha = 0.22, seed = 3 } = {}) {
  const r = rng(seed);
  withAdd(ctx, () => {
    for (let i = 0; i < n; i++) {
      const a = angle + (r() - 0.5) * spread + Math.sin(t * 0.21 + i) * 0.03;
      const w = 0.03 + r() * 0.07;
      const A = alpha * (0.5 + 0.5 * Math.sin(t * (0.4 + r() * 0.5) + i * 1.7));
      const g = ctx.createLinearGradient(x, y, x + Math.cos(a) * len, y + Math.sin(a) * len);
      g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${A})`); g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(x, y);
      ctx.lineTo(x + Math.cos(a - w) * len, y + Math.sin(a - w) * len);
      ctx.lineTo(x + Math.cos(a + w) * len, y + Math.sin(a + w) * len);
      ctx.closePath(); ctx.fill();
    }
  });
}

// The Light: a small orb that breathes, and brightens while it speaks.
function orb(ctx, t, { x, y, r = 34, level = 0, alpha = 1, rgb = [200, 228, 255] } = {}) {
  if (alpha <= 0) return;
  const bob = Math.sin(t * 1.3) * 10, sway = Math.sin(t * 0.7) * 8;
  const X = x + sway, Y = y + bob;
  const pulse = 1 + 0.08 * Math.sin(t * 2.1) + level * 0.5;
  withAdd(ctx, () => {
    // a wide cool spill on the scene, then halo, glow and core
    const sp = ctx.createRadialGradient(X, Y, 0, X, Y, r * 22);
    sp.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${0.10 * alpha})`); sp.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
    ctx.fillStyle = sp; ctx.fillRect(X - r * 22, Y - r * 22, r * 44, r * 44);
    for (const [rr, a] of [[r * 10 * pulse, 0.16], [r * 4.5 * pulse, 0.3], [r * 1.8 * pulse, 0.6], [r * pulse, 1.0]]) {
      const g = ctx.createRadialGradient(X, Y, 0, X, Y, rr);
      g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a * alpha})`); g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      ctx.fillStyle = g; ctx.fillRect(X - rr, Y - rr, rr * 2, rr * 2);
    }
    ctx.fillStyle = `rgba(255,255,255,${0.95 * alpha})`;
    ctx.beginPath(); ctx.arc(X, Y, r * 0.42 * pulse, 0, Math.PI * 2); ctx.fill();
  });
  // a few sparks orbit it
  motes(ctx, t, { n: 10, seed: 41, rgb, alpha: 0.6 * alpha, area: { x0: X - r * 4, x1: X + r * 4, y0: Y - r * 4, y1: Y + r * 4 }, rise: 18, size: 2 });
}

// A held light (the truth in her hands): flickering glow.
function ember(ctx, t, { x, y, r = 60, k = 1, rgb = [255, 190, 110] } = {}) {
  const f = 0.85 + 0.15 * fbm(t * 6, 5);
  withAdd(ctx, () => {
    for (const [rr, a] of [[r * 6, 0.12], [r * 2.6, 0.3], [r, 0.7]]) {
      const R = rr * f * (0.7 + 0.3 * k);
      const g = ctx.createRadialGradient(x, y, 0, x, y, R);
      g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a * k})`); g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      ctx.fillStyle = g; ctx.fillRect(x - R, y - R, R * 2, R * 2);
    }
  });
  S.embers(ctx, t, Math.round(14 * k), 9, { x0: x - r * 2, x1: x + r * 2, y0: y - r * 6, y1: y }, rgb, 0.8 * k);
}

// Aurora curtains over the top of the frame.
function aurora(ctx, t, { alpha = 0.35, y0 = 0, y1 = H * 0.45 } = {}) {
  withAdd(ctx, () => {
    for (let b = 0; b < 3; b++) {
      const rgb = b === 1 ? [90, 220, 190] : [70, 200, 140];
      ctx.beginPath();
      const pts = [];
      for (let x = -40; x <= W + 40; x += 40) {
        const y = y0 + (y1 - y0) * (0.35 + 0.2 * b) + Math.sin(x * 0.006 + t * 0.25 + b * 2) * 70 + fbm(x * 0.004 + t * 0.12, b + 3) * 90;
        pts.push([x, y]);
      }
      const top = Math.min(...pts.map((p) => p[1])) - 260;
      const g = ctx.createLinearGradient(0, top, 0, top + 360);
      const A = alpha * (0.6 + 0.4 * Math.sin(t * 0.33 + b));
      g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      g.addColorStop(0.75, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${A * 0.6})`);
      g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (const p of pts) ctx.lineTo(p[0], p[1]);
      for (let i = pts.length - 1; i >= 0; i--) ctx.lineTo(pts[i][0], pts[i][1] - 300);
      ctx.closePath();
      ctx.fillStyle = g; ctx.fill();
    }
  });
}

// Candle or lantern flicker on the whole image (warm light breathing).
function flicker(ctx, t, { amount = 0.08, rgb = [255, 170, 90], seed = 1, rate = 7 } = {}) {
  const f = fbm(t * rate, seed) * 0.5 + 0.5;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${amount * (0.4 + f)})`; ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = `rgba(0,0,0,${amount * 0.6 * (1 - f)})`; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

function flash(ctx, k, rgb = [255, 245, 225]) {
  if (k <= 0) return;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${clamp(k)})`; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// Lightning: brief double flashes at the given times, with a jagged bolt.
function lightning(ctx, t, times, { x = W * 0.7, seed = 5 } = {}) {
  for (const t0 of times) {
    const u = t - t0;
    if (u < 0 || u > 0.5) continue;
    const k = (u < 0.08 ? 1 : u < 0.16 ? 0.3 : u < 0.22 ? 0.8 : 1 - (u - 0.22) / 0.28) * 0.55;
    flash(ctx, k * 0.5, [210, 220, 255]);
    const r = rng(seed + Math.round(t0 * 10));
    withAdd(ctx, () => {
      ctx.strokeStyle = `rgba(230,235,255,${k})`; ctx.lineWidth = 4; ctx.shadowColor = 'rgba(180,200,255,1)'; ctx.shadowBlur = 30;
      ctx.beginPath(); let X = x + (r() - 0.5) * 300, Y = 0; ctx.moveTo(X, Y);
      while (Y < H * 0.45) { X += (r() - 0.5) * 120; Y += 40 + r() * 60; ctx.lineTo(X, Y); }
      ctx.stroke();
    });
  }
}

// ---------------------------------------------------------------- breaking
// Cracks that grow from a point over [t0, t0 + dur], glowing from inside.
function cracks(ctx, t, { x, y, t0, dur = 1.6, n = 9, len = 900, seed = 11, glow = [255, 236, 200], width = 3 } = {}) {
  const k = smooth((t - t0) / dur);
  if (k <= 0) return;
  const r = rng(seed);
  withAdd(ctx, () => {
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (let i = 0; i < n; i++) {
      const a0 = (i / n) * Math.PI * 2 + (r() - 0.5) * 0.5;
      const L = len * (0.5 + r() * 0.6) * clamp(k * (1.3 - r() * 0.4));
      const segs = 9;
      const pts = [[x, y]];
      let a = a0, X = x, Y = y;
      for (let s = 1; s <= segs; s++) {
        a += (r() - 0.5) * 0.6;
        X += Math.cos(a) * (L / segs); Y += Math.sin(a) * (L / segs) * 0.6;   // flattened: a floor seen at an angle
        pts.push([X, Y]);
      }
      for (const [lw, A] of [[width * 6, 0.12], [width * 2.2, 0.35], [width * 0.8, 0.95]]) {
        ctx.strokeStyle = `rgba(${glow[0]},${glow[1]},${glow[2]},${A})`; ctx.lineWidth = lw;
        ctx.beginPath(); pts.forEach((p, j) => (j ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke();
      }
    }
  });
}

// An expanding ring of light along the ground.
function shockwave(ctx, t, { x, y, t0, dur = 1.4, rgb = [255, 240, 210], flat = 0.28 } = {}) {
  const u = (t - t0) / dur;
  if (u < 0 || u > 1) return;
  const R = 60 + easeIn(Math.sqrt(u)) * 1400;
  withAdd(ctx, () => {
    ctx.save(); ctx.translate(x, y); ctx.scale(1, flat);
    for (const [w, a] of [[90, 0.15], [30, 0.4], [8, 0.9]]) {
      ctx.strokeStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a * (1 - u)})`; ctx.lineWidth = w;
      ctx.beginPath(); ctx.arc(0, 0, R, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.restore();
  });
}

// Shards flying outward from a point (the mask breaking).
function shards(ctx, t, { x, y, t0, n = 26, seed = 13, rgb = [245, 245, 250], speed = 900 } = {}) {
  const u = t - t0;
  if (u < 0 || u > 3) return;
  const r = rng(seed);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  for (let i = 0; i < n; i++) {
    const a = r() * Math.PI * 2, v = speed * (0.3 + r() * 0.7), spin = (r() - 0.5) * 8, sz = 14 + r() * 36;
    const X = x + Math.cos(a) * v * u, Y = y + Math.sin(a) * v * u + 600 * u * u;
    const A = clamp(1 - u / 2.6);
    ctx.save(); ctx.translate(X, Y); ctx.rotate(spin * u + a);
    ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${0.85 * A})`;
    ctx.beginPath(); ctx.moveTo(-sz, -sz * 0.3); ctx.lineTo(sz * 0.7, -sz * 0.5); ctx.lineTo(sz * 0.4, sz * 0.6); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = `rgba(255,255,255,${A})`; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.restore();
  }
  ctx.restore();
}

// Light shards spinning around (sensory overload).
function glare(ctx, t, { k = 1, seed = 17, x = W / 2, y = H * 0.42 } = {}) {
  if (k <= 0) return;
  const r = rng(seed);
  withAdd(ctx, () => {
    const g = ctx.createRadialGradient(x, y, 0, x, y, 1100);
    g.addColorStop(0, `rgba(255,250,235,${0.35 * k})`); g.addColorStop(1, 'rgba(255,250,235,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 22; i++) {
      const a = r() * Math.PI * 2 + t * (0.4 + r()) * (r() > 0.5 ? 1 : -1);
      const d = 220 + r() * 700 + Math.sin(t * 3 + i) * 40;
      const X = x + Math.cos(a) * d, Y = y + Math.sin(a) * d * 1.2;
      const len = 60 + r() * 160;
      ctx.strokeStyle = `rgba(255,248,230,${(0.25 + 0.4 * r()) * k})`; ctx.lineWidth = 2 + r() * 5;
      ctx.beginPath(); ctx.moveTo(X, Y); ctx.lineTo(X + Math.cos(a + 1.3) * len, Y + Math.sin(a + 1.3) * len); ctx.stroke();
    }
  });
}

// ---------------------------------------------------------------- birds
// Distant birds as silhouettes with beating wings, flying along paths.
function flock(ctx, t, { n = 40, seed = 23, t0 = 0, from = [W / 2, H * 0.8], spread = 500, rise = 520, rgb = [30, 22, 18], size = 14 } = {}) {
  const r = rng(seed);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.strokeStyle = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`; ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const delay = r() * 1.6, dir = (r() - 0.5) * 2, sp = 0.7 + r() * 0.6, ph = r() * 6.28, sz = size * (0.5 + r() * 0.9);
    const u = t - t0 - delay;
    if (u < 0) continue;
    const X = from[0] + (r() - 0.5) * spread * 0.4 + dir * spread * u * 0.35 * sp + Math.sin(u * 1.3 + ph) * 30;
    const Y = from[1] - rise * u * sp + Math.sin(u * 2 + ph) * 20;
    if (Y < -50 || X < -60 || X > W + 60) continue;
    const s = sz * (1 + u * 0.12);
    const flap = Math.sin(u * 14 * sp + ph);
    ctx.lineWidth = Math.max(1.5, s * 0.22);
    ctx.beginPath();
    ctx.moveTo(X - s, Y - flap * s * 0.6); ctx.quadraticCurveTo(X - s * 0.4, Y - s * 0.1, X, Y);
    ctx.quadraticCurveTo(X + s * 0.4, Y - s * 0.1, X + s, Y - flap * s * 0.6);
    ctx.stroke();
  }
  ctx.restore();
}

// ---------------------------------------------------------------- water
// Draw an image (already placed by drawFn into a layer) through rippling water:
// horizontal strips shifted by a travelling wave, with a cool tint.
function rippleDraw(ctx, src, t, { amp = 7, k = 0.025, speed = 2.2, strip = 12, tint = [80, 140, 210], tintA = 0.18 } = {}) {
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  for (let y = 0; y < H; y += strip) {
    const dx = Math.sin(y * k - t * speed) * amp + Math.sin(y * k * 2.3 + t * speed * 0.7) * amp * 0.4;
    ctx.drawImage(src, 0, y, W, strip, dx, y, W, strip);
  }
  ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = `rgba(${tint[0]},${tint[1]},${tint[2]},${tintA})`; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// Concentric ripples spreading on a water surface (seen at an angle).
function rings(ctx, t, { x, y, t0 = 0, period = 1.6, n = 3, rmax = 420, flat = 0.32, alpha = 0.35 } = {}) {
  withAdd(ctx, () => {
    ctx.save(); ctx.translate(x, y); ctx.scale(1, flat);
    for (let i = 0; i < n; i++) {
      const u = ((t - t0) / period + i / n) % 1;
      if (t - t0 < 0) continue;
      ctx.strokeStyle = `rgba(200,225,255,${alpha * (1 - u)})`; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(0, 0, 20 + u * rmax, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.restore();
  });
}

// ---------------------------------------------------------------- grading
function grade(ctx, rgb, a, op = 'soft-light') {
  if (a <= 0) return;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalCompositeOperation = op;
  ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// Mirror glass: cooler, a soft sheen, the frame's gilded edge.
function mirrorGlass(ctx) {
  grade(ctx, [150, 190, 225], 0.18);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createLinearGradient(0, 0, W, H * 0.7);
  g.addColorStop(0, 'rgba(255,255,255,0.12)'); g.addColorStop(0.3, 'rgba(255,255,255,0)');
  g.addColorStop(0.52, 'rgba(255,255,255,0.06)'); g.addColorStop(0.6, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

module.exports = {
  snow, motes, twinkles, rays, orb, ember, aurora, flicker, flash, lightning, cracks, shockwave, shards, glare,
  flock, rippleDraw, rings, grade, mirrorGlass, withAdd,
};
