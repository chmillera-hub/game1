// Group e vignettes: memory, questions, the button, simulations, the monument, erasure, silence,
// restart, the big bang, the crowd of lights and the kneeling witness.
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const U = require('../lib/util');
const FX = require('../lib/fx');

const { TAU, clamp, lerp, smooth, easeInOut, rgba, mix, shade } = U;
const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);

const GOLD = [255, 211, 138], AMBER = [255, 184, 92], CYAN = [127, 232, 255];
const CRIMSON = [214, 48, 74], BLOOD = [107, 20, 38], VIOLET = [120, 90, 190];
const ASH = [120, 120, 134];

// ---------------------------------------------------------------- shared helpers
function frame(w, h) {
  const unit = Math.min(w, h);
  return { unit, cx: w / 2, cy: h / 2, port: h > w * 1.3 };
}
function night(ctx, w, h, p, top = [6, 9, 21], bot = [20, 26, 51], starDiv = 9000, fade) {
  FX.bg(ctx, w, h, top, bot);
  if (starDiv) FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / starDiv), fade ? { fade } : {});
}
// cheap soft dot (two arcs, no gradient)
function dot(ctx, x, y, r, col, a) {
  if (a <= 0.01) return;
  ctx.fillStyle = rgba(col, a * 0.22); ctx.beginPath(); ctx.arc(x, y, r * 2.4, 0, TAU); ctx.fill();
  ctx.fillStyle = rgba(col, a); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
}
function rrect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}
function pose(o) {
  return Object.assign({ lean: 0, head: 0, armL: [0.12, 0.08], armR: [-0.12, -0.08], legL: [0.04, 0], legR: [-0.04, 0] }, o);
}
// A figure with a soft rim of light along the edges that face the light source (head, shoulders, limbs)
// plus a gentle fill, so it never reads as a near-black hole. Two offset copies in the rim colour sit
// behind the body; only a thin soft sliver shows on the lit side. No head crescent.
function litFigure(ctx, x, y, fh, P, o = {}) {
  const rim = o.rim || GOLD, a = o.alpha ?? 1;
  const lx = o.lx ?? x, ly = o.ly ?? y - fh * 4;
  let dx = lx - x, dy = ly - (y - fh * 0.6);
  const d = Math.hypot(dx, dy) || 1; dx /= d; dy /= d;
  const rw = fh * (o.rimW || 0.016), str = o.rimA ?? 1;
  const base = { child: o.child, facing: o.facing, phase: o.phase };
  // faint cool back-edge so the shadow side still separates from the dark
  if (o.back !== false) FX.figure(ctx, x - dx * rw * 0.6, y - dy * rw * 0.6, fh, P, Object.assign({}, base, { color: o.backCol || [70, 78, 110], alpha: a * 0.35 * str }));
  if (o.soft !== false) FX.figure(ctx, x + dx * rw * 2.1, y + dy * rw * 2.1, fh, P, Object.assign({}, base, { color: rim, alpha: a * 0.22 * str }));
  FX.figure(ctx, x + dx * rw, y + dy * rw, fh, P, Object.assign({}, base, { color: mix(rim, [255, 250, 235], 0.25), alpha: a * 0.65 * str }));
  return FX.figure(ctx, x, y, fh, P, Object.assign({}, base, { color: mix(o.color || [30, 28, 40], rim, o.fill ?? 0.14), alpha: a }));
}
function groundBand(ctx, w, h, gy, col, rim, rimA) {
  const g = ctx.createLinearGradient(0, gy, 0, h);
  g.addColorStop(0, rgba(col)); g.addColorStop(1, rgba(shade(col, -0.6)));
  ctx.fillStyle = g; ctx.fillRect(0, gy, w, h - gy);
  if (rim) {
    const l = ctx.createLinearGradient(0, 0, w, 0);
    l.addColorStop(0, rgba(rim, 0)); l.addColorStop(0.5, rgba(rim, rimA)); l.addColorStop(1, rgba(rim, 0));
    ctx.fillStyle = l; ctx.fillRect(0, gy - 1, w, 2);
  }
}

// ================================================================ memory_storm
// small "memory cards" with simple pictures: a face, a painting, laughter, a war, children, a victory
function memCard(ctx, kind, s, tint, a) {
  const cw = s, ch = s * 0.78;
  ctx.globalAlpha = a;
  const war = kind === 2;
  const base = war ? [70, 16, 30] : mix([60, 44, 34], tint, 0.25);
  const g = ctx.createLinearGradient(0, -ch / 2, 0, ch / 2);
  g.addColorStop(0, rgba(shade(base, 0.25))); g.addColorStop(1, rgba(shade(base, -0.3)));
  ctx.fillStyle = g; rrect(ctx, -cw / 2, -ch / 2, cw, ch, s * 0.06); ctx.fill();
  ctx.save(); ctx.clip();
  const ink = war ? [255, 120, 110] : mix([255, 222, 170], tint, 0.3);
  ctx.fillStyle = rgba(ink, 0.85); ctx.strokeStyle = rgba(ink, 0.85);
  ctx.lineCap = 'round';
  if (kind === 0) { // face in profile
    ctx.beginPath(); ctx.ellipse(-s * 0.02, -s * 0.06, s * 0.16, s * 0.19, 0, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.moveTo(s * 0.12, -s * 0.1); ctx.lineTo(s * 0.2, -s * 0.0); ctx.lineTo(s * 0.12, s * 0.02); ctx.fill();
    ctx.fillRect(-s * 0.09, s * 0.08, s * 0.13, s * 0.14);
    ctx.beginPath(); ctx.ellipse(-s * 0.03, s * 0.36, s * 0.3, s * 0.16, 0, 0, TAU); ctx.fill();
  } else if (kind === 1) { // painting: sun over hills in a frame
    ctx.lineWidth = s * 0.035; ctx.strokeRect(-cw * 0.36, -ch * 0.34, cw * 0.72, ch * 0.68);
    ctx.beginPath(); ctx.arc(s * 0.1, -s * 0.07, s * 0.07, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-cw * 0.34, ch * 0.3); ctx.quadraticCurveTo(-s * 0.1, -s * 0.08, s * 0.08, ch * 0.2);
    ctx.quadraticCurveTo(s * 0.2, s * 0.02, cw * 0.34, ch * 0.18); ctx.lineTo(cw * 0.34, ch * 0.32); ctx.lineTo(-cw * 0.34, ch * 0.32); ctx.fill();
  } else if (kind === 2) { // war: smoke plume over broken skyline
    for (let i = 0; i < 4; i++) {
      ctx.fillStyle = rgba([150, 60, 66], 0.55 - i * 0.08);
      ctx.beginPath(); ctx.arc(-s * 0.05 + i * s * 0.06, -s * 0.02 - i * s * 0.09, s * (0.09 + i * 0.025), 0, TAU); ctx.fill();
    }
    ctx.fillStyle = rgba([255, 140, 90], 0.8);
    ctx.beginPath(); ctx.ellipse(-s * 0.05, s * 0.1, s * 0.12, s * 0.06, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba([25, 6, 12], 0.95);
    ctx.beginPath(); ctx.moveTo(-cw / 2, ch / 2); ctx.lineTo(-cw / 2, s * 0.14); ctx.lineTo(-s * 0.3, s * 0.14); ctx.lineTo(-s * 0.3, s * 0.05);
    ctx.lineTo(-s * 0.2, s * 0.05); ctx.lineTo(-s * 0.16, s * 0.15); ctx.lineTo(s * 0.06, s * 0.15); ctx.lineTo(s * 0.1, s * 0.0);
    ctx.lineTo(s * 0.16, s * 0.08); ctx.lineTo(s * 0.22, s * 0.02); ctx.lineTo(s * 0.26, s * 0.12); ctx.lineTo(cw / 2, s * 0.12); ctx.lineTo(cw / 2, ch / 2); ctx.fill();
  } else if (kind === 3) { // laughter: round face, crescent eyes, open smile
    ctx.beginPath(); ctx.arc(0, 0, s * 0.25, 0, TAU); ctx.fill();
    ctx.strokeStyle = rgba(shade(base, -0.2), 0.95); ctx.lineWidth = s * 0.03;
    ctx.beginPath(); ctx.arc(-s * 0.09, -s * 0.03, s * 0.045, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
    ctx.beginPath(); ctx.arc(s * 0.09, -s * 0.03, s * 0.045, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
    ctx.fillStyle = rgba(shade(base, -0.2), 0.95);
    ctx.beginPath(); ctx.moveTo(-s * 0.13, s * 0.05); ctx.quadraticCurveTo(0, s * 0.24, s * 0.13, s * 0.05); ctx.closePath(); ctx.fill();
  } else if (kind === 4) { // children: adult and child holding hands
    const P1 = pose({ armL: [0.5, 0.1] }), P2 = pose({ armR: [-0.6, -0.1] });
    FX.figure(ctx, -s * 0.12, ch * 0.42, s * 0.62, P1, { color: ink });
    FX.figure(ctx, s * 0.15, ch * 0.42, s * 0.38, P2, { color: ink, child: true });
  } else { // victory: arms up under a sunburst
    ctx.fillStyle = rgba(ink, 0.35); ctx.beginPath(); ctx.arc(0, -s * 0.02, s * 0.22, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba(ink, 0.9);
    FX.figure(ctx, 0, ch * 0.5, s * 0.66, 'arms_up', { color: ink });
  }
  ctx.restore();
  ctx.lineWidth = Math.max(1, s * 0.02); ctx.strokeStyle = rgba(war ? CRIMSON : mix(GOLD, tint, 0.5), 0.6);
  rrect(ctx, -cw / 2, -ch / 2, cw, ch, s * 0.06); ctx.stroke();
  ctx.globalAlpha = 1;
}

const memory_storm = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    const prm = p.params || {};
    const tint = prm.cyan ? CYAN : GOLD;
    night(ctx, w, h, p, [7, 8, 20], [22, 18, 44], 14000);
    // in the portrait frame the storm sits high so no card passes behind the subtitle band (y 900-1040)
    const cyS = port ? h * 0.36 : cy;
    // the eye of the storm
    FX.glow(ctx, cx, cyS, unit * 0.55, prm.cyan ? CYAN : AMBER, 0.14 + 0.03 * Math.sin(p.t * 0.6));
    // soft spiral arms (wind)
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    const spin = p.t * 0.25 + p.u * 1.2;
    for (let k = 0; k < 3; k++) {
      ctx.strokeStyle = rgba(prm.cyan ? CYAN : [200, 170, 230], 0.07); ctx.lineWidth = unit * 0.05;
      ctx.beginPath();
      for (let i = 0; i <= 30; i++) {
        const f = i / 30, an = spin + k * TAU / 3 + f * 3.2, r = unit * (0.06 + f * 0.62);
        const x = cx + Math.cos(an) * r, y = cyS + Math.sin(an) * r * (port ? 0.95 : 0.8);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    ctx.restore();
    // cards orbit the eye; speed builds a little across u
    const N = port ? 16 : 13;
    const rnd = U.rng(p.seed * 7 + 11);
    const cards = [];
    for (let i = 0; i < N; i++) {
      const r0 = 0.18 + rnd() * 0.5, a0 = rnd() * TAU, sz = (0.13 + rnd() * 0.07) * (port ? 1.2 : 1), kind = i % 6, tilt = (rnd() - 0.5) * 0.8;
      const sp = 0.12 / (0.3 + r0);
      const an = a0 + p.t * sp + easeInOut(p.u) * 1.4 * sp * 4;
      const rr = unit * r0 * (1 + 0.05 * Math.sin(p.t * 0.3 + i));
      const x = cx + Math.cos(an) * rr * (port ? 0.62 : 1.25);
      const y = cyS + Math.sin(an) * rr * (port ? 0.68 : 0.72);
      const depth = 0.75 + 0.25 * Math.sin(an);
      cards.push({ x, y, s: unit * sz * depth, kind, rot: tilt + Math.sin(p.t * 0.4 + i) * 0.15, a: 0.55 + 0.45 * depth, depth });
    }
    cards.sort((a, b) => a.depth - b.depth);
    for (const c of cards) {
      ctx.save(); ctx.translate(c.x, c.y); ctx.rotate(c.rot);
      memCard(ctx, c.kind, c.s, tint, c.a);
      ctx.restore();
    }
    FX.vignette(ctx, w, h, 0.5);
  },
};

// ================================================================ questions_float
const glyphCache = new Map();
function glyphPoints(ch, size, n) {
  const key = ch + '|' + Math.round(size) + '|' + n;
  if (glyphCache.has(key)) return glyphCache.get(key);
  const S = Math.ceil(size * 1.4);
  const c = createCanvas(S, S), g = c.getContext('2d');
  g.fillStyle = '#fff'; g.font = `300 ${size}px Inter Display`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(ch, S / 2, S / 2);
  const d = g.getImageData(0, 0, S, S).data;
  const pts = [];
  const rnd = U.rng(91);
  let tries = 0;
  while (pts.length < n && tries < 40000) {
    tries++;
    const x = Math.floor(rnd() * S), y = Math.floor(rnd() * S);
    if (d[(y * S + x) * 4 + 3] > 128) pts.push([x - S / 2, y - S / 2, rnd(), rnd()]);
  }
  glyphCache.set(key, pts);
  return pts;
}
function wrapLines(ctx, text, maxW, size) {
  ctx.font = `300 ${size}px Inter Display`;
  const words = text.split(/\s+/).filter(Boolean), lines = [];
  let cur = '';
  for (const wd of words) {
    const t = cur ? cur + ' ' + wd : wd;
    if (ctx.measureText(t).width > maxW && cur) { lines.push(cur); cur = wd; } else cur = t;
  }
  if (cur) lines.push(cur);
  return lines;
}
const questions_float = {
  testParams: { text: 'Would you choose to be born?' },
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    const prm = p.params || {};
    night(ctx, w, h, p, [6, 8, 20], [18, 16, 40], 12000);
    FX.glow(ctx, cx, cy, unit * 0.6, [110, 110, 200], 0.1);
    FX.motes(ctx, w, h, p.t, p.seed + 5, port ? 18 : 12, [180, 190, 255], { alpha: 0.35 });
    if (prm.dissolve) {
      const size = unit * 0.5;
      const gx = cx, gy = cy + Math.sin(p.t * 0.5) * unit * 0.012;
      const sweep = smooth((p.u - 0.22) / 0.5); // 0..1 left->right erosion
      const left = gx - size * 0.32, right = gx + size * 0.32;
      const sx = lerp(left - size * 0.05, right + size * 0.05, sweep);
      FX.glow(ctx, gx, gy, size * 0.8, [170, 190, 255], 0.16 * (1 - sweep * 0.8));
      if (sweep < 1) {
        ctx.save(); if (sweep > 0) { ctx.beginPath(); ctx.rect(sx, 0, w - sx, h); ctx.clip(); }
        FX.text(ctx, '?', gx, gy, size, [225, 232, 255], { weight: 300, family: 'Inter Display', alpha: 0.95 });
        ctx.restore();
      }
      // dust released as the edge passes
      const pts = glyphPoints('?', size, 140);
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (const q of pts) {
        const px = gx + q[0], py = gy + q[1];
        if (px > sx) continue;
        const rel = clamp((sx - px) / (size * 0.7) + (p.u > 0.72 ? (p.u - 0.72) * 2.5 : 0));
        const age = rel * (0.8 + q[2] * 0.4);
        const x = px + age * unit * (0.2 + q[2] * 0.3) + Math.sin(p.t * 0.6 + q[3] * 6) * unit * 0.01 * age;
        const y = py - age * unit * (0.04 + q[3] * 0.18) + (q[2] - 0.5) * age * unit * 0.1;
        const a = (1 - smooth(age / 1.2)) * 0.8;
        dot(ctx, x, y, unit * (0.003 + q[3] * 0.003), [210, 220, 255], a);
      }
      ctx.restore();
      FX.vignette(ctx, w, h, 0.5);
      return;
    }
    // The spoken question is already on screen as a subtitle, so the vision shows no words: one large
    // question mark of light assembles from drifting motes and breathes, while a few smaller, fainter
    // question marks drift around it like echoes (count and placement vary with the line).
    const text = prm.text || '?';
    let th = 0; for (let i = 0; i < text.length; i++) th = (th * 31 + text.charCodeAt(i)) >>> 0;
    const size = unit * (port ? 0.62 : 0.56);
    const gx = cx, gy = (port ? h * 0.42 : cy) + Math.sin(p.t * 0.45) * unit * 0.012;
    const form = easeOut(p.u / 0.4);
    const breath = 0.9 + 0.1 * Math.sin(p.t * 0.8);
    FX.glow(ctx, gx, gy, size * 0.85, [150, 170, 255], 0.16 * form * breath);
    // the solid glyph fades in as the motes settle
    FX.text(ctx, '?', gx, gy, size, [225, 232, 255], { weight: 300, family: 'Inter Display', alpha: 0.85 * smooth((p.u - 0.15) / 0.35) * breath, glow: [140, 170, 255] });
    const pts = glyphPoints('?', size, 150);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (const q of pts) {
      const k = clamp(form * 1.15 - q[2] * 0.15);
      const sa = q[3] * TAU + (th % 7);
      const far = (1 - k) * unit * (0.35 + q[2] * 0.4);
      const x = gx + q[0] + Math.cos(sa + p.t * 0.15) * far + Math.sin(p.t * 0.7 + q[2] * 9) * unit * 0.004;
      const y = gy + q[1] + Math.sin(sa + p.t * 0.15) * far * (port ? 1.3 : 0.8);
      dot(ctx, x, y, unit * (0.0025 + q[3] * 0.0025), [210, 220, 255], 0.35 + 0.4 * (1 - k));
    }
    ctx.restore();
    // echoes: small question marks orbiting slowly and fading in and out
    const nE = 3 + (th % 3);
    for (let i = 0; i < nE; i++) {
      const hv = U.hash(th + i * 13), hs = U.hash(th + i * 29 + 5);
      const an = hv * TAU + p.t * (0.05 + hs * 0.04) * (i % 2 ? 1 : -1);
      const rx = unit * (port ? 0.36 : 0.52), ry = unit * (port ? 0.5 : 0.3);
      const ex = gx + Math.cos(an) * rx, ey = gy + Math.sin(an) * ry;
      const ea = (0.25 + 0.2 * Math.sin(p.t * 0.5 + i * 2)) * smooth((p.u - 0.1 - i * 0.05) / 0.3);
      FX.text(ctx, '?', ex, ey, unit * (0.07 + hs * 0.07), [200, 210, 255], { weight: 300, family: 'Inter Display', alpha: ea, glow: [140, 170, 255] });
    }
    FX.vignette(ctx, w, h, 0.5);
  },
};

// ================================================================ the_button
const the_button = {
  testParams: { pressed: true },
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    const pressed = !!(p.params && p.params.pressed);
    FX.bg(ctx, w, h, [5, 7, 17], [14, 14, 32]);
    const gy = port ? h * 0.66 : h * 0.8;
    const press = pressed ? easeInOut((p.u - 0.28) / 0.14) : 0;
    const burst = pressed ? smooth((p.u - 0.4) / 0.4) : 0;
    const breath = 0.5 + 0.5 * Math.sin(p.t * 1.1);
    // floor
    groundBand(ctx, w, h, gy, [12, 12, 26]);
    const pw = unit * 0.2, ph = unit * (port ? 0.36 : 0.32);
    const topY = gy - ph;
    const glowA = 0.35 + 0.12 * breath + burst * 0.35;
    // light pool on the floor
    ctx.save(); ctx.translate(cx, gy); ctx.scale(1, 0.18);
    FX.glow(ctx, 0, 0, unit * (0.45 + burst * 0.5), AMBER, 0.25 + burst * 0.2);
    ctx.restore();
    // halo behind
    FX.glow(ctx, cx, topY - unit * 0.03, unit * (0.32 + burst * 0.6), GOLD, glowA * 0.55);
    // pedestal column
    const cg = ctx.createLinearGradient(cx - pw / 2, 0, cx + pw / 2, 0);
    cg.addColorStop(0, '#11131f'); cg.addColorStop(0.45, rgba(mix([40, 38, 60], AMBER, 0.15 + burst * 0.2))); cg.addColorStop(1, '#0b0c16');
    ctx.fillStyle = cg;
    ctx.beginPath(); ctx.moveTo(cx - pw * 0.38, topY + unit * 0.03); ctx.lineTo(cx + pw * 0.38, topY + unit * 0.03);
    ctx.lineTo(cx + pw * 0.5, gy); ctx.lineTo(cx - pw * 0.5, gy); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.ellipse(cx, gy, pw * 0.5, pw * 0.08, 0, 0, Math.PI); ctx.fill();
    // top slab
    const sw = pw * 0.62, sh = unit * 0.035;
    ctx.fillStyle = '#1a1b2c'; ctx.fillRect(cx - sw, topY, sw * 2, sh);
    ctx.beginPath(); ctx.ellipse(cx, topY + sh, sw, sw * 0.16, 0, 0, Math.PI); ctx.fill();
    ctx.fillStyle = rgba(mix([44, 42, 66], GOLD, 0.25 + burst * 0.3));
    ctx.beginPath(); ctx.ellipse(cx, topY, sw, sw * 0.16, 0, 0, TAU); ctx.fill();
    // button housing ring
    const br = sw * 0.55;
    ctx.fillStyle = '#0c0d18'; ctx.beginPath(); ctx.ellipse(cx, topY, br * 1.12, br * 0.2, 0, 0, TAU); ctx.fill();
    // dome
    const domeH = br * 0.55 * (1 - press * 0.75);
    const dg = ctx.createRadialGradient(cx - br * 0.2, topY - domeH * 0.6, 0, cx, topY, br * 1.1);
    const hot = 0.15 + 0.2 * breath + burst * 0.6;
    dg.addColorStop(0, rgba(mix(GOLD, [255, 250, 235], hot))); dg.addColorStop(0.6, rgba(AMBER)); dg.addColorStop(1, rgba(shade(AMBER, -0.45)));
    ctx.fillStyle = dg;
    ctx.beginPath(); ctx.ellipse(cx, topY, br, br * 0.18, 0, 0, Math.PI);
    ctx.ellipse(cx, topY, br, domeH, 0, Math.PI, TAU); ctx.fill();
    FX.glow(ctx, cx, topY - domeH * 0.5, br * 2.6, GOLD, 0.35 + 0.15 * breath + burst * 0.5);
    if (pressed) {
      // light ripples outward after the press
      for (let k = 0; k < 3; k++) {
        const f = (p.u - 0.42 - k * 0.1) / 0.45;
        if (f <= 0 || f >= 1) continue;
        const e = easeOut(f);
        ctx.save(); ctx.translate(cx, topY); ctx.scale(1, 0.3);
        FX.ring(ctx, 0, 0, br + e * unit * 0.9, unit * 0.01 * (1 - f) + 1, GOLD, 0.3 * (1 - f) * (1 - f));
        ctx.restore();
      }
      // a column of light rises
      if (burst > 0) {
        const lg = ctx.createLinearGradient(0, topY, 0, 0);
        lg.addColorStop(0, rgba(GOLD, 0.35 * burst)); lg.addColorStop(1, rgba(GOLD, 0));
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = lg;
        ctx.beginPath(); ctx.moveTo(cx - br * 0.6, topY); ctx.lineTo(cx + br * 0.6, topY); ctx.lineTo(cx + br * 2.2, 0); ctx.lineTo(cx - br * 2.2, 0); ctx.closePath(); ctx.fill();
        ctx.restore();
      }
    }
    // a few motes rising from the button
    const rnd = U.rng(p.seed + 3);
    for (let i = 0; i < 10; i++) {
      const ph = rnd(), sp = 0.08 + rnd() * 0.06;
      const f = (ph + p.t * sp) % 1;
      dot(ctx, cx + (rnd() - 0.5) * br * 2 + Math.sin(p.t * 0.5 + i) * br * 0.2, topY - f * unit * 0.4, unit * 0.004, GOLD, (1 - f) * 0.6 * (0.6 + burst));
    }
    FX.vignette(ctx, w, h, 0.55);
  },
};

// ================================================================ simulations_branch
const branchCache = new Map();
function branchTree(seed) {
  if (branchCache.has(seed)) return branchCache.get(seed);
  const rnd = U.rng(seed * 13 + 5);
  const segs = []; // [x0,y0,x1,y1,depth,tip,outcome]
  const grow = (x, y, an, len, d) => {
    const x1 = x + Math.cos(an) * len, y1 = y + Math.sin(an) * len;
    const tip = d === 5;
    segs.push([x, y, x1, y1, d, tip, tip ? (rnd() < 0.18 ? 1 : rnd() < 0.12 ? 2 : 0) : 0]);
    if (tip) return;
    const spread = 0.35 + rnd() * 0.25;
    grow(x1, y1, an - spread + (rnd() - 0.5) * 0.15, len * (0.78 + rnd() * 0.1), d + 1);
    grow(x1, y1, an + spread + (rnd() - 0.5) * 0.15, len * (0.78 + rnd() * 0.1), d + 1);
  };
  const K = 7;
  for (let k = 0; k < K; k++) grow(0, 0, k * TAU / K + rnd() * 0.3, 0.13, 0);
  branchCache.set(seed, segs);
  return segs;
}
const simulations_branch = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    night(ctx, w, h, p, [5, 8, 20], [14, 18, 40], 14000);
    const segs = branchTree(p.seed);
    const g = 0.6 + easeOut(p.u / 0.8) * 5.4; // depth progress 0..6
    const sx = unit * (port ? 0.95 : 1.25), sy = unit * (port ? 1.55 : 0.9);
    const rot = p.t * 0.02;
    const cr = Math.cos(rot), sr = Math.sin(rot);
    const tr = (x, y) => [cx + (x * cr - y * sr) * sx, cy + (x * sr + y * cr) * sy];
    FX.glow(ctx, cx, cy, unit * 0.25, CYAN, 0.35);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    for (let d = 0; d <= 5; d++) {
      const f = clamp(g - d);
      if (f <= 0) break;
      ctx.strokeStyle = rgba(CYAN, 0.75 - d * 0.09);
      ctx.lineWidth = Math.max(1, unit * (0.007 - d * 0.0009));
      ctx.beginPath();
      for (const s of segs) {
        if (s[4] !== d) continue;
        const [x0, y0] = tr(s[0], s[1]), [x1, y1] = tr(lerp(s[0], s[2], f), lerp(s[1], s[3], f));
        ctx.moveTo(x0, y0); ctx.lineTo(x1, y1);
      }
      ctx.stroke();
    }
    ctx.restore();
    // nodes and outcomes at the tips
    for (const s of segs) {
      const f = clamp(g - s[4]);
      if (f < 1) continue;
      const [x1, y1] = tr(s[2], s[3]);
      if (s[5]) {
        const col = s[6] === 1 ? GOLD : s[6] === 2 ? CRIMSON : CYAN;
        const a = clamp((g - 6) * 3 + 0.6) * (0.7 + 0.3 * Math.sin(p.t * 0.7 + x1));
        dot(ctx, x1, y1, unit * (s[6] ? 0.006 : 0.004), col, a);
      } else if (s[4] < 3) dot(ctx, x1, y1, unit * 0.005, [200, 245, 255], 0.7);
    }
    FX.light(ctx, cx, cy, unit * 0.012, [200, 245, 255], 0.9);
    FX.vignette(ctx, w, h, 0.45);
  },
};

// ================================================================ monument
function monumentLayout(port) {
  const rows = port ? [6, 5, 4, 3, 2, 1] : [5, 4, 3, 2, 1];
  const figs = [];
  rows.forEach((n, r) => {
    for (let i = 0; i < n; i++) figs.push({ r, i, n, off: (i - (n - 1) / 2) });
  });
  return { rows, figs };
}
const monument = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    const crumble = !!(p.params && p.params.crumble);
    night(ctx, w, h, p, [8, 9, 22], [26, 22, 46], 12000);
    // base row stands above the subtitle band in the portrait frame; a lit stepped plinth fills the ground below
    const gy = port ? h * 0.665 : h * 0.86;
    const L = monumentLayout(port);
    const R = L.rows.length;
    const availH = (gy - (port ? h * 0.12 : h * 0.12)) * 0.95;
    const fh = availH / (1 + (R - 1) * 0.74 + 0.05);
    const step = fh * 0.74, spacing = fh * 0.34;
    const topY = gy - fh * 0.06 - (R - 1) * step - fh;
    // light above the summit
    const lightY = topY - fh * 0.35;
    const reveal = 0.35 + 0.65 * smooth(p.u / 0.8);
    FX.glow(ctx, cx, lightY, unit * (0.5 + 0.1 * reveal), GOLD, 0.3 * reveal + 0.05 * Math.sin(p.t * 0.6));
    // warm sky behind the monument so its figures read in silhouette
    FX.glow(ctx, cx, topY + (gy - topY) * 0.45, (gy - topY) * 0.75, AMBER, 0.16 + 0.1 * reveal, true);
    FX.light(ctx, cx, lightY, unit * 0.01, GOLD, 0.8 * reveal);
    // stepped plinth under the base row, its top edges caught by the summit light
    const pwid = L.rows[0] * spacing + fh * 0.4;
    const floorY = port ? h * 0.9 : h * 0.97;
    groundBand(ctx, w, h, floorY, [16, 14, 28], [140, 110, 90], 0.25);
    const steps = port ? 4 : 2;
    const stepH = (floorY - gy) / steps;
    for (let s2 = 0; s2 < steps; s2++) {
      const y0 = gy + s2 * stepH, ww = pwid + s2 * fh * 0.35;
      const sg = ctx.createLinearGradient(0, y0, 0, y0 + stepH);
      sg.addColorStop(0, rgba(mix([30, 26, 40], AMBER, 0.12 * reveal))); sg.addColorStop(1, rgba([14, 12, 22]));
      ctx.fillStyle = sg; ctx.fillRect(cx - ww / 2, y0, ww, stepH + 1);
      const eg = ctx.createLinearGradient(cx - ww / 2, 0, cx + ww / 2, 0);
      eg.addColorStop(0, rgba(GOLD, 0)); eg.addColorStop(0.5, rgba(GOLD, 0.35 * reveal)); eg.addColorStop(1, rgba(GOLD, 0));
      ctx.fillStyle = eg; ctx.fillRect(cx - ww / 2, y0, ww, Math.max(1.5, unit * 0.003));
    }
    // warm pool of light spilling down the steps
    ctx.save(); ctx.translate(cx, gy + (floorY - gy) * 0.4); ctx.scale(1, 0.45);
    FX.glow(ctx, 0, 0, pwid * 0.7, AMBER, 0.12 * reveal);
    ctx.restore();
    const stone = [16, 14, 24];
    const nF = L.figs.length;
    const dust = [];
    // crumble order: top first, roughly, with jitter
    const order = L.figs.map((f, k) => ({ k, key: -f.r + U.hash(k + p.seed * 31) * 1.6 }));
    order.sort((a, b) => a.key - b.key);
    const rank = new Array(nF); order.forEach((o, j) => { rank[o.k] = j; });
    L.figs.forEach((f, k) => {
      const y = gy - fh * 0.06 - f.r * step;
      const x = cx + f.off * spacing;
      const top = f.r === R - 1;
      // supporters hold the climbers above, the summit figure reaches for the light
      let P;
      const sway = Math.sin(p.t * 0.5 + k) * 0.05;
      if (top) P = pose({ armL: [2.85 + sway, 0.1], armR: [-2.75 + sway, -0.1], head: -0.4, lean: -0.03 });
      else if (f.r === R - 2) P = pose({ armL: [2.5 + sway, 0.35], armR: [-2.5 + sway, -0.35], head: -0.3 });
      else P = pose({ armL: [2.3 + sway * 0.5, 0.6], armR: [-2.3 + sway * 0.5, -0.6], head: -0.15, legL: [0.12, 0], legR: [-0.12, 0] });
      let alpha = 1, dy = 0;
      if (crumble) {
        const t0 = 0.12 + (rank[k] / nF) * 0.6;
        const c = smooth((p.u - t0) / 0.14);
        alpha = 1 - c; dy = c * fh * 0.04;
        if (c > 0 && c < 1 || (p.u - t0) > 0) {
          for (let j = 0; j < 7; j++) {
            const hs = U.hash(k * 17 + j * 5 + 1), hv = U.hash(k * 29 + j * 3 + 7);
            const age = (p.u - t0 - hv * 0.08) / 0.3;
            if (age <= 0 || age >= 1) continue;
            dust.push([x + (hs - 0.5) * fh * 0.2 + age * unit * (0.1 + hv * 0.15), y - fh * (0.2 + hs * 0.6) + age * fh * (0.15 - hv * 0.5), 1 - age]);
          }
        }
      }
      if (alpha <= 0.01) return;
      // rim light grows from the top as the light reveals
      const lit = clamp(reveal * 1.4 - (R - 1 - f.r) / R * 0.8);
      litFigure(ctx, x, y + dy, fh, P, { color: mix(stone, [110, 84, 66], 0.25 + lit * 0.35), alpha, rim: mix(GOLD, AMBER, 0.3), lx: cx, ly: lightY, rimW: 0.02, rimA: 0.55 + 0.45 * lit, fill: 0.12 });
    });
    if (dust.length) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (const d of dust) dot(ctx, d[0], d[1], unit * 0.004, [210, 180, 140], d[2] * 0.6);
      ctx.restore();
    }
    FX.motes(ctx, w, h, p.t, p.seed + 9, port ? 14 : 9, GOLD, { alpha: 0.35 });
    FX.vignette(ctx, w, h, 0.5);
  },
};

// ================================================================ flicker_erased
// A little huddle of people around one shared flame. Their lights go out one by one from the edge inward,
// each figure dissolving upward as ash; finally the flame gutters, dies and leaves only a smoke wisp -> nothing.
const FLICK_POSE = pose({ armL: [0.28, -1.95], armR: [-0.28, 1.95], head: 0.25 });
function smokeWisp(ctx, x, y, len, t, a, wd) {
  if (a <= 0.01) return;
  ctx.save(); ctx.lineCap = 'round';
  for (let k = 0; k < 3; k++) {
    ctx.strokeStyle = rgba([150, 150, 165], a * (0.22 - k * 0.05)); ctx.lineWidth = wd * (1 + k * 1.4);
    ctx.beginPath();
    for (let i = 0; i <= 18; i++) {
      const f = i / 18;
      const px = x + Math.sin(f * 5 + t * 0.7 + k) * len * 0.07 * f + Math.sin(f * 2.2 - t * 0.3) * len * 0.05 * f;
      const py = y - f * len;
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }
  ctx.restore();
}
const flicker_erased = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    FX.bg(ctx, w, h, [7, 8, 16], [16, 16, 26]);
    FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 16000), { fade: () => 0.5 * (1 - smooth((p.u - 0.5) / 0.4)) });
    const gy = port ? h * 0.6 : h * 0.72;
    const fx = cx, fy = gy - unit * 0.075;
    // the flame lives until ~0.72, guttering in its last moments
    const die = smooth((p.u - 0.6) / 0.14);
    const gutter = p.u > 0.5 ? 0.75 + 0.25 * Math.sin(p.t * 7.3) * Math.sin(p.t * 3.1) : 1;
    const life = (1 - die) * (0.92 + 0.08 * Math.sin(p.t * 2.1)) * (die > 0 ? gutter : 1);
    // warm light on the ground around the huddle
    ctx.save(); ctx.translate(fx, gy); ctx.scale(1, 0.22);
    FX.glow(ctx, 0, 0, unit * 0.5, AMBER, 0.3 * life);
    ctx.restore();
    FX.glow(ctx, fx, fy, unit * 0.42, AMBER, 0.2 * life);
    ctx.fillStyle = rgba([12, 11, 20], 0.8); ctx.fillRect(0, gy, w, h - gy);
    const fg = ctx.createLinearGradient(0, gy, 0, gy + unit * 0.12);
    fg.addColorStop(0, rgba(AMBER, 0.12 * life)); fg.addColorStop(1, rgba(AMBER, 0));
    ctx.fillStyle = fg; ctx.fillRect(0, gy, w, unit * 0.12);
    // the people: two shallow arcs, near ones lower and larger
    const N = 9;
    const figs = [];
    for (let i = 0; i < N; i++) {
      const side = i % 2 ? 1 : -1, k = Math.ceil(i / 2);
      const far = k % 2 === 0;
      const sc = port ? 1.3 : 1;
      const x = fx + side * (k * 0.075 + 0.015) * unit * sc;
      const y = gy + (far ? -unit * 0.015 : unit * 0.02) * sc;
      const fh = unit * (far ? 0.22 : 0.26) * sc;
      // outer people fade first
      const t0 = 0.12 + (1 - k / 4) * 0.4 + U.hash(i * 7 + 3) * 0.06;
      figs.push({ x, y, fh, side, t0, far, i });
    }
    figs.sort((a, b) => a.y - b.y);
    const ash = [];
    for (const f of figs) {
      if (f.i === 0) continue; // the centre spot is the flame
      const gone = smooth((p.u - f.t0) / 0.16);
      const P = pose(Object.assign({}, FLICK_POSE, { head: 0.3 + Math.sin(p.t * 0.4 + f.i) * 0.04 }));
      if (gone < 1) {
        const r = litFigure(ctx, f.x, f.y + gone * f.fh * 0.03, f.fh, P, { color: [26, 22, 32], rim: mix(GOLD, AMBER, 0.4), lx: fx, ly: fy, rimA: life * (1 - gone), fill: 0.18 * life, alpha: 1 - gone });
        // each person's own small light, cupped in both hands at the chest
        const lx = (r.handL[0] + r.handR[0]) / 2, ly = (r.handL[1] + r.handR[1]) / 2 - f.fh * 0.02;
        const la = (1 - smooth((p.u - f.t0 + 0.05) / 0.08)) * (0.85 + 0.15 * Math.sin(p.t * 1.3 + f.i));
        if (la > 0.02) { FX.glow(ctx, lx, ly, f.fh * 0.18, AMBER, 0.45 * la); dot(ctx, lx, ly, unit * 0.005, [255, 236, 200], la); }
        f.lx = lx; f.ly = ly;
      }
      // ash released as the figure goes
      if (gone > 0) {
        for (let j = 0; j < 8; j++) {
          const hv = U.hash(f.i * 31 + j), hs = U.hash(f.i * 17 + j * 5);
          const age = clamp((p.u - f.t0 - hv * 0.1) / 0.35);
          if (age <= 0 || age >= 1) continue;
          ash.push([f.x + (hs - 0.5) * f.fh * 0.25 + Math.sin(p.t * 0.6 + j) * unit * 0.01, f.y - f.fh * (0.3 + hs * 0.6) - age * unit * 0.2, 1 - age]);
        }
      }
      // a thin smoke curl where each little light went out
      const sm = smooth((p.u - f.t0) / 0.06) * (1 - smooth((p.u - f.t0 - 0.06) / 0.3));
      smokeWisp(ctx, f.x, f.y - f.fh * 0.6, unit * 0.1, p.t + f.i, sm * 0.5, Math.max(1, unit * 0.003));
    }
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (const d of ash) dot(ctx, d[0], d[1], unit * 0.003, [200, 180, 160], d[2] * 0.5);
    ctx.restore();
    // the shared flame
    if (life > 0.01) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const fhh = unit * 0.075 * (0.5 + 0.5 * life), fw = unit * 0.022 * (0.6 + 0.4 * life);
      const sw = Math.sin(p.t * 1.3) * fw * 0.35;
      const g = ctx.createRadialGradient(fx, fy, 0, fx, fy - fhh * 0.3, fhh);
      g.addColorStop(0, rgba([255, 245, 220], life)); g.addColorStop(0.4, rgba(GOLD, 0.85 * life)); g.addColorStop(1, rgba(AMBER, 0));
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(fx - fw, fy); ctx.quadraticCurveTo(fx - fw, fy - fhh * 0.5, fx + sw, fy - fhh);
      ctx.quadraticCurveTo(fx + fw, fy - fhh * 0.5, fx + fw, fy); ctx.arc(fx, fy, fw, 0, Math.PI); ctx.fill();
      ctx.restore();
      FX.glow(ctx, fx, fy - fhh * 0.3, unit * 0.1, GOLD, 0.4 * life);
    }
    // the last smoke from the flame, then nothing
    const smoke = smooth((p.u - 0.66) / 0.08) * (1 - smooth((p.u - 0.8) / 0.18));
    smokeWisp(ctx, fx, fy - unit * 0.01, unit * 0.32, p.t, smoke, Math.max(1.5, unit * 0.005));
    // an ember that lingers on the ground a moment
    dot(ctx, fx, fy + unit * 0.005, unit * 0.004, [255, 140, 80], smooth((p.u - 0.62) / 0.05) * (1 - smooth((p.u - 0.7) / 0.12)) * 0.8);
    FX.vignette(ctx, w, h, 0.5);
  },
};

// ================================================================ option_silence
// The universe's lights go out one by one, outer ones first, closing in on a last star whose ring
// collapses and fades into a calm, empty dark.
const silCache = new Map();
function silLayout(w, h, seed) {
  const k = w + 'x' + h + ':' + seed;
  if (silCache.has(k)) return silCache.get(k);
  const rnd = U.rng(seed * 3 + 101);
  const pts = [];
  for (let i = 0, n = Math.round(w * h / 9000); i < n; i++) pts.push({ x: rnd() * w, y: rnd() * h, r: 0.6 + rnd() * rnd() * 1.6, c: rnd(), ph: rnd() * TAU });
  silCache.set(k, pts);
  return pts;
}
const option_silence = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    const fadeAll = smooth((p.u - 0.15) / 0.7);
    const top = mix([8, 10, 26], [3, 4, 10], fadeAll), bot = mix([22, 20, 48], [6, 7, 14], fadeAll);
    FX.bg(ctx, w, h, top, bot);
    const sx = cx, sy = port ? h * 0.4 : cy;
    const maxD = Math.hypot(w, h) * 0.6;
    // faint nebulae that drain away first
    const neb = 1 - smooth(p.u / 0.45);
    FX.glow(ctx, w * 0.22, h * 0.25, unit * 0.45, VIOLET, 0.12 * neb);
    FX.glow(ctx, w * 0.8, h * (port ? 0.72 : 0.7), unit * 0.4, [80, 120, 200], 0.1 * neb);
    FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 7000), { fade: (i, x, y) => 0.7 * (1 - smooth((p.u - 0.08 - Math.pow(1 - clamp(Math.hypot(x - sx, y - sy) / maxD), 1.4) * 0.6 - U.hash(i + 3) * 0.1) / 0.1)) });
    // the larger lights, each going out with a small soft puff
    const L = silLayout(w, h, p.seed);
    L.forEach((s, i) => {
      const dd = Math.hypot(s.x - sx, s.y - sy) / maxD;
      if (dd < 0.08) return;
      const tOut = 0.1 + Math.pow(1 - clamp(dd), 1.4) * 0.62 + U.hash(i * 5 + 1) * 0.08;
      const a = 1 - smooth((p.u - tOut) / 0.06);
      const col = mix([200, 215, 255], [255, 225, 190], s.c);
      const tw = 0.85 + 0.15 * Math.sin(p.t * 0.6 + s.ph);
      if (a > 0.01) {
        FX.glow(ctx, s.x, s.y, unit * 0.035 * s.r, col, 0.3 * a * tw);
        dot(ctx, s.x, s.y, unit * 0.0028 * s.r, col, 0.95 * a * tw);
      }
      const puff = (p.u - tOut) / 0.08;
      if (puff > 0 && puff < 1) FX.glow(ctx, s.x, s.y, unit * (0.02 + 0.03 * puff) * s.r, col, 0.12 * (1 - puff));
    });
    // the last star: its ring contracts and fades, then the star itself dims away
    const last = 1 - smooth((p.u - 0.66) / 0.26);
    const ringK = smooth((p.u - 0.3) / 0.45);
    const br = 0.92 + 0.08 * Math.sin(p.t * 0.5);
    const rr = unit * lerp(0.26, 0.015, ringK);
    if (ringK < 1) FX.ring(ctx, sx, sy, rr, Math.max(1, unit * 0.004), [200, 215, 255], 0.35 * (1 - ringK * 0.7) * last);
    if (ringK < 1) FX.ring(ctx, sx, sy, rr * 1.15, Math.max(1, unit * 0.012), [150, 170, 240], 0.08 * (1 - ringK));
    FX.glow(ctx, sx, sy, unit * (0.12 + 0.12 * (1 - ringK)), [200, 210, 255], 0.3 * last * br);
    FX.light(ctx, sx, sy, unit * 0.01 * (0.4 + 0.6 * last), [225, 232, 255], (0.03 + 0.95 * last) * br);
    FX.vignette(ctx, w, h, 0.4 + 0.3 * fadeAll);
  },
};

// ================================================================ option_restart
const option_restart = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    FX.bg(ctx, w, h, [4, 5, 12], [10, 10, 22]);
    const ign = easeOut((p.u - 0.15) / 0.35);
    const flare = Math.exp(-Math.pow((p.u - 0.32) / 0.1, 2));
    const breath = 0.9 + 0.1 * Math.sin(p.t * 0.9);
    // faint warm pre-glow already visible at the cut
    FX.glow(ctx, cx, cy, unit * (0.12 + ign * 0.4), AMBER, (0.18 + ign * 0.3) * breath);
    FX.glow(ctx, cx, cy, unit * (0.06 + flare * 0.25), [255, 245, 225], 0.5 * flare);
    // rays: four soft spikes
    const rl = unit * (0.05 + ign * 0.22 + flare * 0.12);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let k = 0; k < 4; k++) {
      const an = k * Math.PI / 2 + Math.PI / 4 * 0 + p.t * 0.03;
      const len = rl * (k % 2 ? 0.75 : 1);
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(an);
      const g = ctx.createLinearGradient(0, 0, len, 0);
      g.addColorStop(0, rgba(GOLD, 0.6 * (0.3 + ign * 0.7))); g.addColorStop(1, rgba(GOLD, 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, -unit * 0.006); ctx.lineTo(len, 0); ctx.lineTo(0, unit * 0.006); ctx.fill();
      ctx.restore();
    }
    ctx.restore();
    // ignition ring
    const rf = (p.u - 0.3) / 0.45;
    if (rf > 0 && rf < 1) FX.ring(ctx, cx, cy, unit * (0.03 + easeOut(rf) * 0.4), unit * 0.004 * (1 - rf) + 1, GOLD, 0.18 * (1 - rf) * (1 - rf));
    FX.light(ctx, cx, cy, unit * (0.006 + ign * 0.008), [255, 230, 180], 0.55 + 0.45 * ign);
    // a few embers circling once it has caught
    for (let i = 0; i < 7; i++) {
      const an = i * TAU / 7 + p.t * 0.25 * (i % 2 ? 1 : -0.8), r = unit * (0.06 + 0.03 * Math.sin(i * 2.3 + p.t * 0.4)) * (0.5 + ign);
      dot(ctx, cx + Math.cos(an) * r, cy + Math.sin(an) * r * 0.85, unit * 0.0035, GOLD, 0.55 * ign);
    }
    FX.vignette(ctx, w, h, 0.5);
  },
};

// ================================================================ big_bang
const big_bang = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    const e = easeOut(p.u / 0.75);
    FX.bg(ctx, w, h, mix([3, 3, 8], [10, 8, 26], e), mix([3, 3, 8], [22, 14, 40], e));
    const span = Math.hypot(w, h) * 0.55;
    // nebula clouds drifting outward
    const cl = [[VIOLET, 0.3], [CYAN, 0.18], [AMBER, 0.22], [[200, 80, 140], 0.18], [VIOLET, 0.22], [GOLD, 0.15]];
    cl.forEach(([col, a], i) => {
      const an = i * TAU / cl.length + 0.4 + p.t * 0.01;
      const r = e * span * (0.35 + U.hash(i + 2) * 0.3);
      FX.glow(ctx, cx + Math.cos(an) * r, cy + Math.sin(an) * r * (port ? 1.4 : 0.8), unit * (0.15 + e * 0.35), col, a * e);
    });
    // the core: blinding at first, settling into a warm heart
    const core = 1 - 0.65 * e;
    FX.glow(ctx, cx, cy, unit * (0.18 + e * 0.5), [255, 240, 215], 0.85 * core);
    FX.glow(ctx, cx, cy, unit * (0.08 + e * 0.12), [255, 255, 245], core);
    // shock rings
    for (let k = 0; k < 3; k++) {
      const f = (p.u - 0.02 - k * 0.12) / 0.6;
      if (f <= 0 || f >= 1) continue;
      FX.ring(ctx, cx, cy, easeOut(f) * span, unit * 0.008 * (1 - f) + 1, k ? GOLD : [255, 245, 230], 0.22 * (1 - f) * (1 - f));
    }
    // matter flung outward along rays (streak + head)
    const rnd = U.rng(p.seed * 3 + 1);
    const N = 120;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    for (let i = 0; i < N; i++) {
      const an = rnd() * TAU, sp = 0.25 + rnd() * 0.75, delay = rnd() * 0.12, sz = rnd();
      const f = easeOut((p.u - delay) / 0.8);
      const drift = 1 + p.t * 0.004;
      const r = (unit * 0.02 + f * span * sp) * drift;
      const x = cx + Math.cos(an) * r, y = cy + Math.sin(an) * r;
      const col = mix([255, 245, 225], sz > 0.6 ? VIOLET : sz > 0.3 ? AMBER : CYAN, clamp(f * 1.2));
      const tail = unit * 0.06 * (1 - f) * sp;
      if (tail > 1) {
        ctx.strokeStyle = rgba(col, 0.35); ctx.lineWidth = 1 + sz * 1.5;
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - Math.cos(an) * tail, y - Math.sin(an) * tail); ctx.stroke();
      }
      dot(ctx, x, y, unit * (0.002 + sz * 0.003), col, 0.75);
    }
    ctx.restore();
    // a few young galaxies once things have spread
    for (let i = 0; i < 5; i++) {
      const an = U.hash(i * 7 + 3) * TAU, r = (0.3 + U.hash(i * 7 + 5) * 0.4) * span * e;
      const x = cx + Math.cos(an) * r, y = cy + Math.sin(an) * r;
      ctx.save(); ctx.translate(x, y); ctx.rotate(an + p.t * 0.05); ctx.scale(1, 0.4);
      FX.glow(ctx, 0, 0, unit * 0.05, i % 2 ? GOLD : [200, 190, 255], 0.5 * smooth((p.u - 0.45) / 0.3));
      ctx.restore();
    }
    FX.vignette(ctx, w, h, 0.4);
  },
};

// ================================================================ crowd_lights
const HOLD = pose({ armL: [0.28, -1.95], armR: [-0.28, 1.95], head: 0.15 });
function crowdLayout(w, h, port, seed) {
  const hz = port ? h * 0.36 : h * 0.42;
  const rows = [];
  const rnd = U.rng(seed * 5 + 77);
  const nR = port ? 7 : 6;
  for (let r = 0; r < nR; r++) {
    const depth = r / (nR - 1); // 0 = front, 1 = far
    let fh = lerp(port ? h * 0.2 : h * 0.33, h * 0.035, Math.pow(depth, 0.7));
    let gy = lerp(port ? h * 0.97 : h * 1.02, hz + fh * 0.6, Math.pow(depth, 0.6));
    if (port) {
      // portrait: the near row stands low with its lights below the subtitle band (y > 1060); the rest of
      // the crowd fills the field above it (feet at y < 880), leaving the band itself as open dark ground
      if (r === 0) { fh = h * 0.21; gy = h * 1.07; } else {
        const d2 = (r - 1) / (nR - 2);
        fh = lerp(h * 0.13, h * 0.03, Math.pow(d2, 0.7));
        gy = lerp(h * 0.685, hz + fh * 0.6, Math.pow(d2, 0.6));
      }
    }
    const sp = fh * (0.5 + depth * 0.2);
    const n = Math.ceil(w / sp) + 1;
    const off = rnd() * sp;
    const people = [];
    for (let i = 0; i < n; i++) people.push({ x: off + i * sp - sp * 0.5 + (rnd() - 0.5) * sp * 0.3, hs: 0.9 + rnd() * 0.2, ph: rnd() * TAU, ch: rnd() < 0.15 });
    rows.push({ depth, fh, gy, people });
  }
  return { hz, rows };
}
const crowd_lights = {
  testParams: { connect: true },
  draw(ctx, w, h, p) {
    const { unit, port } = frame(w, h);
    const connect = !!(p.params && p.params.connect);
    FX.bg(ctx, w, h, [6, 8, 22], [20, 18, 40]);
    FX.stars(ctx, w, h * 0.45, p.t, p.seed, Math.round(w * h / 16000));
    const L = crowdLayout(w, h, port, p.seed);
    // horizon of countless far lights
    const hg = ctx.createLinearGradient(0, L.hz - unit * 0.12, 0, L.hz + unit * 0.12);
    hg.addColorStop(0, rgba(AMBER, 0)); hg.addColorStop(0.5, rgba(AMBER, 0.16)); hg.addColorStop(1, rgba(AMBER, 0.04));
    ctx.fillStyle = hg; ctx.fillRect(0, L.hz - unit * 0.12, w, unit * 0.24);
    ctx.fillStyle = rgba([14, 12, 26]); ctx.fillRect(0, L.hz + unit * 0.02, w, h);
    const rnd = U.rng(p.seed + 404);
    for (let i = 0; i < 40; i++) {
      const x = rnd() * w, y = L.hz + unit * 0.005 + rnd() * unit * 0.04;
      dot(ctx, x, y, 1 + rnd(), GOLD, (0.3 + 0.3 * Math.sin(p.t * 0.6 + i)) * (0.4 + 0.6 * smooth(p.u / 0.5)));
    }
    // warm haze rising from the crowd so the silhouettes read against it
    const hz2 = ctx.createLinearGradient(0, L.hz, 0, h);
    const hzA = 0.1 + 0.12 * smooth(p.u / 0.6);
    hz2.addColorStop(0, rgba(AMBER, hzA * 0.7)); hz2.addColorStop(0.5, rgba(AMBER, hzA)); hz2.addColorStop(1, rgba(AMBER, hzA * 0.3));
    ctx.fillStyle = hz2; ctx.fillRect(0, L.hz, w, h - L.hz);
    const lights = [];
    // draw far to near
    for (let r = L.rows.length - 1; r >= 0; r--) {
      const row = L.rows[r];
      const on = smooth((p.u * 1.6 + 0.35) - row.depth * 0.9); // lights spread from front to back
      const col = mix([10, 10, 22], [24, 20, 38], row.depth);
      const rowLights = [];
      for (const pp of row.people) {
        const fh = row.fh * pp.hs * (pp.ch ? 0.7 : 1);
        if (pp.x < -fh || pp.x > w + fh) continue;
        let lx, ly;
        if (row.fh > unit * 0.07) {
          // rim light from the warm haze along the horizon + the light each one holds
          const res = row.fh > unit * 0.17
            ? litFigure(ctx, pp.x, row.gy, fh, HOLD, { color: col, child: pp.ch, rim: mix(AMBER, GOLD, 0.5), lx: pp.x + (pp.x - w / 2) * 0.3, ly: L.hz, rimA: 0.5 + 0.5 * on, fill: 0.1 + 0.08 * on, rimW: 0.014, back: false, soft: row.fh > unit * 0.3 })
            : FX.figure(ctx, pp.x, row.gy, fh, HOLD, { color: mix(col, AMBER, 0.12 * on), child: pp.ch });
          lx = (res.handL[0] + res.handR[0]) / 2; ly = (res.handL[1] + res.handR[1]) / 2 - fh * 0.04;
        } else {
          // distant: simple head-and-shoulders silhouette
          ctx.fillStyle = rgba(col);
          ctx.beginPath(); ctx.ellipse(pp.x, row.gy - fh * 0.5, fh * 0.13, fh * 0.5, 0, 0, TAU); ctx.fill();
          ctx.beginPath(); ctx.arc(pp.x, row.gy - fh * 0.98, fh * 0.08, 0, TAU); ctx.fill();
          lx = pp.x; ly = row.gy - fh * 0.62;
        }
        const fl = 0.85 + 0.15 * Math.sin(p.t * 0.7 + pp.ph);
        const a = clamp(on * 1.3 - U.hash(Math.round(pp.x) + r * 1000) * 0.3) * fl;
        rowLights.push([lx, ly, a, row.fh]);
      }
      // lights on top of this row
      for (const l of rowLights) {
        if (l[2] <= 0.02) continue;
        if (l[3] > unit * 0.1) {
          FX.glow(ctx, l[0], l[1], l[3] * 0.35, AMBER, 0.45 * l[2]);
          dot(ctx, l[0], l[1], Math.max(1.5, l[3] * 0.025), [255, 236, 200], l[2]);
        } else dot(ctx, l[0], l[1], Math.max(1, l[3] * 0.03), GOLD, l[2] * 0.9);
      }
      lights.push(rowLights);
    }
    if (connect) {
      // threads of light join neighbours within and between rows
      const k = smooth((p.u - 0.2) / 0.55);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      lights.forEach((rowL, ri) => {
        const next = lights[ri + 1];
        const thick = rowL.length ? Math.max(1, rowL[0][3] * 0.012) : 1;
        ctx.lineWidth = thick; ctx.strokeStyle = rgba(GOLD, 0.35 * k);
        ctx.beginPath();
        for (let i = 0; i < rowL.length; i++) {
          const a = rowL[i];
          const b = rowL[i + 1];
          if (b && a[2] > 0.1 && b[2] > 0.1) { ctx.moveTo(a[0], a[1]); ctx.lineTo(lerp(a[0], b[0], k), lerp(a[1], b[1], k)); }
          if (next && next.length && a[2] > 0.1 && !(port && ri === lights.length - 2)) {
            let best = null, bd = 1e9;
            for (const c of next) { const d = Math.abs(c[0] - a[0]); if (d < bd) { bd = d; best = c; } }
            if (best && best[2] > 0.1) { ctx.moveTo(a[0], a[1]); ctx.lineTo(lerp(a[0], best[0], k), lerp(a[1], best[1], k)); }
          }
        }
        ctx.stroke();
      });
      ctx.restore();
    }
    FX.vignette(ctx, w, h, 0.45);
  },
};

// ================================================================ kneel_spark
// A custom genuflecting figure: back knee and shin on the ground, front knee raised with its foot planted,
// torso bent forward, head bowed, near arm reaching down toward the spark, far arm resting on the raised knee.
// Drawn solid into an offscreen layer so it can be composited as one even translucent body of light.
const kneelLayers = new Map();
function kneelLayer(w, h) {
  const k = w + 'x' + h;
  if (!kneelLayers.has(k)) {
    const big = createCanvas(Math.ceil(w / 2), Math.ceil(h / 2));
    kneelLayers.set(k, { big });
  }
  return kneelLayers.get(k);
}
function kneelBody(g, x0, y0, H, sway) {
  const P = (x, y) => [x0 + x * H, y0 + y * H];
  const seg = (a, b, wd) => { g.lineWidth = wd * H; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); };
  g.lineCap = 'round'; g.lineJoin = 'round';
  const hip = P(0, -0.3), sh = P(0.15, -0.56 + sway * 0.005);
  // back leg: thigh down to the knee on the ground, shin lying back along it, foot behind
  const kneeB = P(0.03, -0.035);
  seg(hip, kneeB, 0.075); seg(kneeB, P(-0.2, -0.03), 0.055);
  g.beginPath(); g.ellipse(...P(-0.225, -0.022), 0.035 * H, 0.016 * H, 0.2, 0, TAU); g.fill();
  // far arm (behind the torso): resting its hand on the raised knee
  const kneeF = P(0.21, -0.29);
  const elF = P(0.19, -0.42);
  seg(P(0.12, -0.545), elF, 0.042); seg(elF, P(0.235, -0.315), 0.036);
  // front leg: thigh forward to a raised knee, shin down to a planted foot
  seg(hip, kneeF, 0.078); seg(kneeF, P(0.235, -0.025), 0.058);
  g.beginPath(); g.ellipse(...P(0.27, -0.016), 0.05 * H, 0.018 * H, 0, 0, TAU); g.fill();
  // torso: hips to bent-forward shoulders
  const nx = 0.86, ny = 0.5; // normal to torso direction
  g.beginPath();
  g.moveTo(hip[0] - 0.075 * H * nx, hip[1] - 0.075 * H * ny + 0.02 * H);
  g.quadraticCurveTo(...P(-0.03, -0.46), sh[0] - 0.085 * H * nx, sh[1] - 0.085 * H * ny);
  g.quadraticCurveTo(...P(0.17, -0.62), sh[0] + 0.08 * H * nx, sh[1] + 0.08 * H * ny);
  g.quadraticCurveTo(...P(0.1, -0.36), hip[0] + 0.07 * H * nx, hip[1] + 0.06 * H * ny);
  g.closePath(); g.fill();
  g.beginPath(); g.arc(hip[0], hip[1], 0.075 * H, 0, TAU); g.fill();
  // neck and bowed head, looking down and forward at the spark
  const head = P(0.235, -0.585 + sway * 0.004);
  seg(sh, P(0.205, -0.6), 0.045);
  g.beginPath(); g.ellipse(head[0], head[1], 0.058 * H, 0.068 * H, -0.9, 0, TAU); g.fill();
  // near arm: shoulder -> elbow -> open hand reaching down, palm toward the spark
  const elN = P(0.27, -0.43 + sway * 0.004), wr = P(0.36, -0.29 + sway * 0.006);
  seg(P(0.17, -0.55), elN, 0.045); seg(elN, wr, 0.038);
  g.save(); g.translate(wr[0], wr[1]); g.rotate(-0.55);
  g.beginPath(); g.ellipse(0, 0.03 * H, 0.022 * H, 0.032 * H, 0, 0, TAU); g.fill();
  g.lineWidth = 0.011 * H;
  for (let i = 0; i < 4; i++) { const fx = (-0.013 + i * 0.009) * H; g.beginPath(); g.moveTo(fx, 0.05 * H); g.lineTo(fx * 1.25, (0.085 - Math.abs(i - 1.5) * 0.007) * H); g.stroke(); }
  g.lineWidth = 0.012 * H; g.beginPath(); g.moveTo(0.016 * H, 0.025 * H); g.lineTo(0.036 * H, 0.052 * H); g.stroke();
  g.restore();
  return { head, hand: [wr[0] + 0.05 * H, wr[1] + 0.06 * H] };
}
const kneel_spark = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    FX.bg(ctx, w, h, [4, 6, 16], [12, 14, 30]);
    // dying stars: reddened, slowly going out one by one
    FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 7000), {
      color: (i) => (U.hash(i * 3 + 1) < 0.5 ? [255, 170, 150] : [190, 200, 240]),
      fade: (i) => 0.75 * (1 - 0.85 * smooth((p.u - U.hash(i + 9) * 1.4) / 0.3)),
    });
    for (let i = 0; i < 5; i++) {
      const x = U.hash(i * 11 + 2) * w, y = U.hash(i * 11 + 5) * h * (port ? 0.45 : 0.5);
      const a = 1 - smooth((p.u - 0.1 - i * 0.15) / 0.35);
      FX.glow(ctx, x, y, unit * 0.05, [230, 110, 90], 0.22 * a);
      dot(ctx, x, y, unit * 0.003, [255, 170, 140], 0.7 * a);
    }
    const gy = port ? h * 0.74 : h * 0.9;
    const H = Math.min((gy - h * (port ? 0.2 : 0.06)) / 0.66, w * 0.86 / 0.75);
    const x0 = cx - H * 0.125;
    // the vast fading figure of light
    const fade = 1 - 0.3 * smooth(p.u / 0.9);
    const breath = 0.94 + 0.06 * Math.sin(p.t * 0.5);
    const L = kneelLayer(w, h);
    const g = L.big.getContext('2d');
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, L.big.width, L.big.height);
    g.setTransform(0.5, 0, 0, 0.5, 0, 0); // half-resolution layer: the soft body of light needs no fine detail
    const grad = g.createLinearGradient(0, gy - H * 0.66, 0, gy);
    grad.addColorStop(0, rgba([205, 248, 255])); grad.addColorStop(0.45, rgba(CYAN)); grad.addColorStop(1, rgba([60, 150, 200]));
    g.fillStyle = grad; g.strokeStyle = grad;
    const sway = Math.sin(p.t * 0.35);
    g.shadowColor = rgba(CYAN, 0.9); g.shadowBlur = H * 0.015;
    const res = kneelBody(g, x0, gy, H, sway);
    g.shadowBlur = 0;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    // soft aura from a few broad glows along the body
    const aur = [[0.12, -0.5, 0.32], [0.2, -0.6, 0.18], [0.1, -0.22, 0.3], [0.32, -0.32, 0.18]];
    for (const [ax, ay, ar] of aur) FX.glow(ctx, x0 + ax * H, gy + ay * H, ar * H, CYAN, 0.16 * fade * breath, false);
    ctx.globalAlpha = 0.36 * fade * breath;
    ctx.drawImage(L.big, 0, 0, w, h);
    ctx.restore();
    FX.glow(ctx, res.head[0], res.head[1], H * 0.12, [210, 250, 255], 0.28 * fade * breath);
    // the floor of nothing in front
    const fg = ctx.createLinearGradient(0, gy, 0, h);
    fg.addColorStop(0, 'rgba(2,3,8,0.0)'); fg.addColorStop(0.15, 'rgba(2,3,8,0.6)'); fg.addColorStop(1, 'rgba(1,1,4,0.9)');
    ctx.fillStyle = fg; ctx.fillRect(0, gy, w, h - gy);
    // the spark, cupped in a hollow of deeper dark just below the reaching hand
    const sx = x0 + H * 0.45, sy = gy - H * 0.06;
    ctx.save(); ctx.translate(sx, sy + H * 0.015); ctx.scale(1, 0.6);
    const cup = ctx.createRadialGradient(0, 0, 0, 0, 0, H * 0.09);
    cup.addColorStop(0, 'rgba(0,0,3,0.85)'); cup.addColorStop(0.6, 'rgba(0,0,4,0.55)'); cup.addColorStop(1, 'rgba(0,0,4,0)');
    ctx.fillStyle = cup; ctx.beginPath(); ctx.arc(0, 0, H * 0.09, 0, TAU); ctx.fill();
    ctx.restore();
    const know = smooth(p.u / 0.85);
    const pulse = 0.88 + 0.12 * Math.sin(p.t * 1.1);
    FX.glow(ctx, sx, sy, unit * (0.05 + 0.04 * know), GOLD, (0.4 + 0.25 * know) * pulse);
    FX.light(ctx, sx, sy, unit * 0.005, [255, 238, 200], 0.95 * pulse);
    // the spark's warmth touching the face as recognition grows
    FX.glow(ctx, res.head[0] + H * 0.03, res.head[1] + H * 0.03, H * 0.06, GOLD, 0.18 * know * pulse);
    FX.vignette(ctx, w, h, 0.5);
  },
};

module.exports = {
  memory_storm, questions_float, the_button, simulations_branch, monument, flicker_erased,
  option_silence, option_restart, big_bang, crowd_lights, kneel_spark,
};
