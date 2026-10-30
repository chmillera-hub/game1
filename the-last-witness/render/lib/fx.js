// Shared drawing helpers for scenes and vignettes: glows, starfields, motes, simple anatomical
// figures (silhouettes with real limbs and hands), text, and a few props.
'use strict';
const path = require('path');
const { GlobalFonts } = require('@napi-rs/canvas');
const U = require('./util');
const { clamp, lerp, smooth, rgba, mix, shade, TAU } = U;
const R = require('./rig');

const FONT_DIR = '/usr/share/fonts/opentype/inter';
let fontsReady = false;
function fonts() {
  if (fontsReady) return;
  for (const f of ['Inter-SemiBold', 'Inter-SemiBoldItalic', 'Inter-Medium', 'Inter-MediumItalic', 'InterDisplay-Light', 'InterDisplay-ExtraLight', 'InterDisplay-Medium', 'Inter-Regular', 'Inter-Italic']) {
    GlobalFonts.registerFromPath(path.join(FONT_DIR, f + '.otf'), f.startsWith('InterDisplay') ? 'Inter Display' : 'Inter');
  }
  fontsReady = true;
}
fonts();

// soft radial glow (additive)
function glow(ctx, x, y, r, color, a = 1, additive = true) {
  if (a <= 0 || r <= 0) return;
  ctx.save();
  if (additive) ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(color, a)); g.addColorStop(0.25, rgba(color, a * 0.5)); g.addColorStop(1, rgba(color, 0));
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
  ctx.restore();
}
// hard core + glow: a point of light
function light(ctx, x, y, r, color, a = 1) {
  glow(ctx, x, y, r * 6, color, a * 0.35);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = rgba(shade(color, 0.6), a); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  ctx.restore();
}

function bg(ctx, w, h, top, bottom) {
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, rgba(top)); g.addColorStop(1, rgba(bottom));
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
}
function vignette(ctx, w, h, a = 0.6) {
  const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.3, w / 2, h / 2, Math.hypot(w, h) * 0.6);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
}

// deterministic starfield; twinkle is slow (low bitrate); fade(i) lets callers dim stars individually
function stars(ctx, w, h, t, seed = 1, n = 120, opts = {}) {
  const rnd = U.rng(seed);
  ctx.save();
  for (let i = 0; i < n; i++) {
    const x = rnd() * w, y = rnd() * h, s = 0.5 + rnd() * rnd() * 2.2;
    const ph = rnd() * TAU;
    let a = (0.45 + 0.55 * rnd()) * (0.9 + 0.1 * Math.sin(t * 0.25 + ph));
    if (opts.fade) a *= opts.fade(i, x, y);
    if (a <= 0.01) continue;
    const c = opts.color ? opts.color(i) : mix([200, 215, 255], [255, 230, 200], rnd());
    ctx.fillStyle = rgba(c, a);
    ctx.beginPath(); ctx.arc(x, y, s, 0, TAU); ctx.fill();
    if (s > 1.6) glow(ctx, x, y, s * 5, c, a * 0.25);
  }
  ctx.restore();
}

// slow drifting motes of light
function motes(ctx, w, h, t, seed = 3, n = 30, color = [180, 230, 255], opts = {}) {
  const rnd = U.rng(seed);
  for (let i = 0; i < n; i++) {
    const x0 = rnd() * w, y0 = rnd() * h, sp = 6 + rnd() * 14, r = 1 + rnd() * 2.5;
    const y = ((y0 - t * sp * (opts.up ?? 1)) % h + h) % h;
    const x = x0 + Math.sin(t * 0.3 + i) * 10;
    const a = (0.3 + 0.5 * rnd()) * (opts.alpha ?? 1);
    glow(ctx, x, y, r * 4, color, a * 0.6);
  }
}

function text(ctx, str, x, y, size, color, opts = {}) {
  ctx.save();
  ctx.font = `${opts.italic ? 'italic ' : ''}${opts.weight || 500} ${size}px ${opts.family || 'Inter'}`;
  ctx.textAlign = opts.align || 'center';
  ctx.textBaseline = opts.baseline || 'middle';
  if (opts.spacing) ctx.letterSpacing = `${opts.spacing}px`;
  if (opts.glow) { ctx.shadowColor = rgba(opts.glow, 0.8); ctx.shadowBlur = size * 0.6; }
  ctx.fillStyle = rgba(color, opts.alpha ?? 1);
  ctx.fillText(str, x, y);
  ctx.restore();
}

// ---------------------------------------------------------------- figures
// A simple, anatomically sound figure (head, neck, torso, two-segment arms with hands, legs with feet).
// x,y = feet ground point; h = total height px. pose keys below; all angles in radians.
// opts: {color, rim, rimSide (-1/1), alpha, glow, facing (-1/1), child (true = shorter neck/torso), hands: true}
const FIG_POSES = {
  stand:   { lean: 0, armL: [0.12, 0.08], armR: [-0.12, -0.08], legL: [0.04, 0], legR: [-0.04, 0], head: 0 },
  walk:    null, // computed from phase
  reach:   { lean: 0.08, armL: [0.1, 0.1], armR: [-1.35, -0.25], legL: [0.12, 0], legR: [-0.1, 0], head: -0.1 },
  arms_up: { lean: -0.05, armL: [2.6, 0.2], armR: [-2.6, -0.2], legL: [0.08, 0], legR: [-0.08, 0], head: -0.25 },
  hold:    { lean: 0.02, armL: [0.45, 1.3], armR: [-0.45, -1.3], legL: [0.05, 0], legR: [-0.05, 0], head: 0.25 },
  kneel:   { lean: 0.15, armL: [0.2, 0.3], armR: [-0.2, -0.3], kneel: true, head: 0.3 },
  sit:     { lean: 0, armL: [0.3, 0.9], armR: [-0.3, -0.9], sit: true, head: 0.1 },
  bow:     { lean: 0.35, armL: [0.1, 0.05], armR: [-0.1, -0.05], legL: [0.04, 0], legR: [-0.04, 0], head: 0.5 },
  push:    { lean: 0.35, armL: [-0.9, -0.6], armR: [-1.1, -0.4], legL: [0.45, 0.3], legR: [-0.35, 0.1], head: -0.1 },
};
function figPose(name, phase = 0) {
  if (name === 'walk') {
    const s = Math.sin(phase * TAU), c = Math.cos(phase * TAU);
    return { lean: 0.04, armL: [s * 0.5, 0.25 + Math.max(0, s) * 0.3], armR: [-s * 0.5, -(0.25 + Math.max(0, -s) * 0.3)], legL: [-s * 0.45, Math.max(0, c) * 0.5], legR: [s * 0.45, Math.max(0, -c) * 0.5], head: 0, bob: Math.abs(c) * 0.012 };
  }
  return FIG_POSES[name] || FIG_POSES.stand;
}
function limb(ctx, x0, y0, a1, a2, l1, l2, w0, w1) {
  // two-segment limb from (x0,y0): angle measured from straight down, positive = toward +x
  const x1 = x0 + Math.sin(a1) * l1, y1 = y0 + Math.cos(a1) * l1;
  const x2 = x1 + Math.sin(a1 + a2) * l2, y2 = y1 + Math.cos(a1 + a2) * l2;
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.lineWidth = w0; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
  ctx.lineWidth = w1; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  return [x2, y2, a1 + a2];
}
function figure(ctx, x, y, h, pose = 'stand', opts = {}) {
  const P = typeof pose === 'object' ? pose : figPose(pose, opts.phase || 0);
  const col = opts.color || [20, 22, 30];
  const child = !!opts.child;
  const f = opts.facing || 1;
  ctx.save();
  ctx.translate(x, y - (P.bob || 0) * h);
  ctx.scale(f, 1);
  if (opts.alpha != null) ctx.globalAlpha *= opts.alpha;
  const u = h; // unit
  const headR = (child ? 0.085 : 0.065) * u;
  const legLen = (child ? 0.42 : 0.47) * u;
  const torso = (child ? 0.26 : 0.3) * u;
  const neck = (child ? 0.025 : 0.04) * u;
  let hipY = -legLen;
  if (P.kneel) hipY = -legLen * 0.55;
  if (P.sit) hipY = -legLen * 0.5;
  const lean = P.lean || 0;
  const shY = hipY - torso * Math.cos(lean), shX = torso * Math.sin(lean);
  const headX = shX + Math.sin(lean + (P.head || 0) * 0.4) * (neck + headR), headY = shY - Math.cos(lean) * (neck + headR * 0.95) + (P.head || 0) * headR * 0.3;
  ctx.fillStyle = rgba(col); ctx.strokeStyle = rgba(col);
  // legs
  const lw = 0.055 * u;
  const drawLeg = (L, sgn) => {
    if (P.kneel) {
      // thigh forward-down to knee on the ground, shin back along the ground; feet hidden behind
      ctx.lineWidth = lw; ctx.lineCap = 'round';
      const kx = sgn * 0.02 * u + 0.12 * u, ky = 0;
      ctx.beginPath(); ctx.moveTo(sgn * 0.03 * u, hipY); ctx.lineTo(kx, ky - lw * 0.4); ctx.lineTo(kx - 0.2 * u, ky - lw * 0.4); ctx.stroke();
      return;
    }
    if (P.sit) {
      ctx.lineWidth = lw; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(sgn * 0.03 * u, hipY); ctx.lineTo(0.2 * u, hipY); ctx.lineTo(0.2 * u + sgn * 0.01 * u, 0); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(0.24 * u, -0.01 * u, 0.045 * u, 0.018 * u, 0, 0, TAU); ctx.fill();
      return;
    }
    const [fx, fy] = limb(ctx, sgn * 0.03 * u, hipY, L[0], L[1], legLen * 0.52, legLen * 0.5, lw, lw * 0.85);
    ctx.beginPath(); ctx.ellipse(fx + 0.03 * u, fy - 0.005 * u, 0.045 * u, 0.018 * u, 0, 0, TAU); ctx.fill();
  };
  drawLeg(P.legR || [0, 0], -1);
  // torso
  ctx.beginPath();
  const tw = (child ? 0.085 : 0.1) * u;
  ctx.moveTo(-tw * 0.75, hipY); ctx.lineTo(tw * 0.75, hipY);
  ctx.quadraticCurveTo(tw * 1.05 + shX, (hipY + shY) / 2, tw + shX, shY + 0.02 * u);
  ctx.quadraticCurveTo(shX, shY - 0.025 * u, -tw + shX, shY + 0.02 * u);
  ctx.quadraticCurveTo(-tw * 1.05 + shX, (hipY + shY) / 2, -tw * 0.75, hipY);
  ctx.fill();
  drawLeg(P.legL || [0, 0], 1);
  // neck + head
  ctx.lineWidth = 0.04 * u; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(shX, shY); ctx.lineTo(headX * 0.9 + shX * 0.1, headY + headR * 0.7); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(headX, headY, headR * 0.88, headR, lean * 0.5, 0, TAU); ctx.fill();
  // arms with small hands (palm + thumb)
  const aw = 0.042 * u;
  const drawArm = (A, sgn) => {
    const [hx, hy, ang] = limb(ctx, shX + sgn * tw * 0.9, shY + 0.02 * u, A[0], A[1], 0.17 * u, 0.15 * u, aw, aw * 0.85);
    ctx.save(); ctx.translate(hx, hy); ctx.rotate(-ang);
    ctx.beginPath(); ctx.ellipse(0, 0.035 * u, 0.026 * u, 0.04 * u, 0, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.ellipse(sgn * -0.02 * u, 0.02 * u, 0.01 * u, 0.022 * u, sgn * 0.6, 0, TAU); ctx.fill();
    ctx.restore();
    return [hx, hy];
  };
  const hR = drawArm(P.armR || [0, 0], -1);
  const hL = drawArm(P.armL || [0, 0], 1);
  // rim light on one side
  if (opts.rim) {
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = rgba(opts.rim, 0.5); ctx.lineWidth = 0.012 * u;
    ctx.beginPath(); ctx.arc(headX, headY, headR * 0.95, -1.2 * (opts.rimSide || 1), 0.8 * (opts.rimSide || 1), (opts.rimSide || 1) < 0); ctx.stroke();
  }
  ctx.restore();
  if (opts.glow) glow(ctx, x + headX * f, y + headY, h * 0.5, opts.glow, opts.glowA ?? 0.25);
  return { head: [x + headX * f, y + headY - (P.bob || 0) * h], handL: [x + hL[0] * f, y + hL[1]], handR: [x + hR[0] * f, y + hR[1]] };
}

// realistic hand for close vignettes (wraps rig.drawHand); size = hand length px
function hand(ctx, x, y, angle, size, pose = 'open', opts = {}) {
  R.drawHand(ctx, x, y, angle, size / 1.8, pose, {
    skin: opts.skin || [205, 150, 116], shadow: opts.shadow || [128, 78, 62], outline: opts.outline,
    mirror: !!opts.mirror, back: !!opts.back,
  });
}

// a glowing seed (almond shape with inner light)
function seed(ctx, x, y, r, a = 1, color = [255, 214, 140]) {
  glow(ctx, x, y, r * 7, color, 0.35 * a);
  ctx.save(); ctx.translate(x, y);
  const g = ctx.createRadialGradient(-r * 0.2, -r * 0.3, 0, 0, 0, r * 1.3);
  g.addColorStop(0, rgba([255, 250, 230], a)); g.addColorStop(0.6, rgba(color, a)); g.addColorStop(1, rgba(shade(color, -0.3), a));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(0, -r * 1.3); ctx.quadraticCurveTo(r, -r * 0.2, 0, r * 1.1); ctx.quadraticCurveTo(-r, -r * 0.2, 0, -r * 1.3); ctx.fill();
  ctx.restore();
}

// expanding ring
function ring(ctx, x, y, r, w, color, a) {
  if (a <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.strokeStyle = rgba(color, a); ctx.lineWidth = w; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.stroke();
  ctx.restore();
}

module.exports = { fonts, glow, light, bg, vignette, stars, motes, text, figure, figPose, FIG_POSES, hand, seed, ring, limb };
