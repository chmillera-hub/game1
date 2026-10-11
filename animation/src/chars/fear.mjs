// FEAR — small, pale-lavender, oversized eyes, wobbly tuft, knitted scarf, thin knobbly limbs.
// Reference implementation of the character API used by every character module:
//
//   drawFear(g, x, y, scale, pose)
//     x, y   : world position of the point between the feet on the ground
//     scale  : 1 = ~330px tall
//     pose   : see POSE below; all optional
//
// POSE fields
//   t          seconds (required for idle motion: breathing, tuft sway, tremble, blinking)
//   face       expression object (see face.mjs). blink is added automatically unless face.noAutoBlink.
//   facing     1 (default) or -1 to mirror the body (face stays readable)
//   headTilt   radians (+ tilts clockwise)
//   headTurn   -1..1 yaw (also passed to the face as turn)
//   headDX, headDY   head offset in px (nods, recoils)
//   lean       body lean radians;  crouch 0..1 (squash down / cower)
//   tremble    0..1 whole-body shiver;  breathe 0..2 breath amplitude (default 1); breathRate (Hz)
//   armL, armR { target:[x,y] (character-local, origin at feet, y up is negative), bend:+1/-1, front:bool, hand:'open'|'fist'|'grip' }
//              or a preset name from FEAR_ARMS
//   walk       { phase: radians } for a walk cycle (legs swing, body bobs)
//   scarfWind  -1..1 scarf ends sway
//   shadow     true to draw a ground shadow
//   alpha      overall opacity

import { clamp, lerp, TAU, fbm, noise1, autoBlink, ik, limb, ellipse, circle, groundShadow, shade, rgba } from '../engine.mjs';
import { drawFace, makeExpr } from '../face.mjs';

export const FEAR_COLORS = {
  body: '#b9a6ea', bodyShade: '#9883d6', bodyLight: '#d9cdf8', line: '#3d2c66',
  scarf: '#e5958a', scarf2: '#f6c9a6', iris: '#5546b8', iris2: '#9b8ff6', blush: '#ff8fb0',
};
const C = FEAR_COLORS;

export const FEAR_FACE = {
  eyeSpacing: 32, eyeY: -6, eyeRx: 24.5, eyeRy: 28.5, eyeShape: 'round',
  white: '#fdfbff', irisColor: C.iris, irisColor2: C.iris2, irisR: 0.66, pupilColor: '#1b1233',
  skin: C.body, line: C.line, lineW: 2.6, lash: 0.7, restLid: 0.1,
  browY: -42, browLen: 24, browThick: 5.5, browColor: C.line, browArch: 0.3,
  mouthY: 38, mouthW: 19, mouthColor: '#4b1d45', tongue: '#e8788f', blushColor: C.blush,
  blushX: 44, blushY: 22, blushR: 15,
};

// head geometry (local to neck)
const HEAD_CY = -66, HEAD_RX = 74, HEAD_RY = 68;
const NECK_Y = -148; // from feet
const SHOULDER_Y = -134, SHOULDER_X = 27;

/** arm presets: targets relative to feet origin */
export const FEAR_ARMS = {
  rest: (side) => ({ target: [side * 40, -78], bend: -side }),
  hugSelf: (side) => ({ target: [-side * 14, -118], bend: side, front: true }),
  wringHands: (side) => ({ target: [side * 4, -104], bend: side, front: true, hand: 'fist' }),
  handsOnFace: (side) => ({ target: [side * 30, -192], bend: -side, front: true, hand: 'palm' }),
  peek: (side) => ({ target: [side * 24, -170], bend: -side, front: true, hand: 'palm' }),
  coverMouth: (side) => ({ target: [side * 10, -164], bend: -side, front: true, hand: 'palm' }),
  reachUp: (side) => ({ target: [side * 92, -196], bend: side, hand: 'grip', front: true }),
  wipeEye: (side) => ({ target: [side * 34, -186], bend: -side, front: true, hand: 'fist' }),
  chest: (side) => ({ target: [side * 8, -128], bend: side, front: true }),
};

function resolveArm(a, side) {
  if (!a) return FEAR_ARMS.rest(side);
  if (typeof a === 'string') return (FEAR_ARMS[a] || FEAR_ARMS.rest)(side);
  return a;
}

export function drawFear(g, x, y, scale = 1, pose = {}) {
  const t = pose.t || 0;
  const facing = pose.facing || 1;
  const trem = clamp(pose.tremble || 0);
  const crouch = clamp(pose.crouch || 0);
  const breathe = pose.breathe ?? 1;
  const br = Math.sin(t * TAU * (pose.breathRate || (0.28 + trem * 0.5))) * breathe;
  const shiverX = trem * (noise1(t * 38, 1) * 2.2);
  const shiverY = trem * (noise1(t * 41, 2) * 1.4);

  g.save();
  if (pose.alpha != null) g.globalAlpha = clamp(pose.alpha);
  g.translate(x, y);
  g.scale(scale, scale);
  if (pose.shadow !== false) groundShadow(g, 0, 0, 62, 0.32);
  g.scale(facing, 1);

  // walk cycle
  const walk = pose.walk;
  const wph = walk ? walk.phase : 0;
  const bob = walk ? Math.abs(Math.sin(wph)) * -5 : 0;
  const hipY = -76 + crouch * 22 + bob;

  // legs
  const legSwing = walk ? Math.sin(wph) * 0.42 : 0;
  g.lineCap = 'round';
  for (const side of [-1, 1]) {
    const hx = side * 15;
    const sw = legSwing * side;
    const kneeX = hx + Math.sin(sw) * 22 + side * crouch * 10, kneeY = hipY + 38 - crouch * 8;
    const footX = hx + Math.sin(sw) * 34 + side * crouch * 14;
    const footY = walk ? -Math.max(0, Math.sin(wph * 1 + (side > 0 ? 0 : Math.PI))) * 9 : 0;
    g.strokeStyle = C.line; g.lineWidth = 13;
    g.beginPath(); g.moveTo(hx, hipY); g.quadraticCurveTo(kneeX, kneeY, footX, footY - 6); g.stroke();
    g.strokeStyle = C.bodyShade; g.lineWidth = 8;
    g.beginPath(); g.moveTo(hx, hipY); g.quadraticCurveTo(kneeX, kneeY, footX, footY - 6); g.stroke();
    // knee knob
    g.fillStyle = C.bodyShade; g.strokeStyle = C.line; g.lineWidth = 2.4;
    circle(g, lerp(hx, footX, 0.5) + (kneeX - hx) * 0.3, (hipY + footY) / 2 + 1, 6.2); g.fill(); g.stroke();
    // foot
    g.fillStyle = '#6c5a9e';
    ellipse(g, footX + side * 5, footY - 4, 13, 7.5); g.fill(); g.stroke();
  }

  g.translate(shiverX, shiverY);
  g.rotate((pose.lean || 0) + trem * noise1(t * 30, 3) * 0.015);

  const arms = [resolveArm(pose.armL, -1), resolveArm(pose.armR, 1)];
  // back arms (not 'front')
  for (const side of [-1, 1]) {
    const a = arms[side < 0 ? 0 : 1];
    if (!a.front) drawArm(g, side, a, t, trem, crouch, br);
  }

  // body (small pear) + scarf
  const bodyTop = NECK_Y + 6 + crouch * 18 + br * 0.8;
  g.fillStyle = C.body; g.strokeStyle = C.line; g.lineWidth = 3;
  g.beginPath();
  g.moveTo(-24, bodyTop + 6);
  g.bezierCurveTo(-40, bodyTop + 30, -44 - br * 0.6, hipY - 4, -26, hipY + 6);
  g.quadraticCurveTo(0, hipY + 16, 26, hipY + 6);
  g.bezierCurveTo(44 + br * 0.6, hipY - 4, 40, bodyTop + 30, 24, bodyTop + 6);
  g.quadraticCurveTo(0, bodyTop - 4, -24, bodyTop + 6);
  g.closePath(); g.fill(); g.stroke();
  // belly light
  g.fillStyle = rgba(C.bodyLight, 0.55);
  ellipse(g, -4, (bodyTop + hipY) / 2 + 6, 18, 20); g.fill();

  // scarf ends (behind head bottom, in front of body)
  const wind = (pose.scarfWind || 0) + fbm(t * 0.6, 4) * 0.15 + trem * noise1(t * 20, 5) * 0.1;
  g.fillStyle = C.scarf; g.strokeStyle = C.line; g.lineWidth = 2.5;
  g.beginPath();
  g.moveTo(10, bodyTop + 6);
  g.quadraticCurveTo(22 + wind * 14, bodyTop + 34, 16 + wind * 26, bodyTop + 58);
  g.lineTo(30 + wind * 26, bodyTop + 56);
  g.quadraticCurveTo(32 + wind * 12, bodyTop + 30, 24, bodyTop + 2);
  g.closePath(); g.fill(); g.stroke();
  g.strokeStyle = C.scarf2; g.lineWidth = 3;
  g.beginPath(); g.moveTo(17 + wind * 24, bodyTop + 48); g.lineTo(29 + wind * 24, bodyTop + 47); g.stroke();

  // head
  g.save();
  const neckX = 0, neckY = NECK_Y + crouch * 20 + br * 1.2;
  g.translate(neckX + (pose.headDX || 0), neckY + (pose.headDY || 0));
  g.rotate((pose.headTilt || 0) + trem * noise1(t * 26, 6) * 0.02);
  drawFearHead(g, pose, t, facing);
  g.restore();

  // scarf wrap (over neck)
  g.fillStyle = C.scarf; g.strokeStyle = C.line; g.lineWidth = 2.6;
  g.beginPath();
  g.ellipse(0, neckY + 4, 30, 11, 0, 0, TAU);
  g.fill(); g.stroke();
  g.strokeStyle = C.scarf2; g.lineWidth = 2.5;
  for (const k of [-14, 0, 14]) { g.beginPath(); g.moveTo(k - 3, neckY - 4); g.lineTo(k + 3, neckY + 12); g.stroke(); }

  // front arms
  for (const side of [-1, 1]) {
    const a = arms[side < 0 ? 0 : 1];
    if (a.front) drawArm(g, side, a, t, trem, crouch, br);
  }
  g.restore();
}

function drawFearHead(g, pose, t, facing) {
  const turn = clamp(pose.headTurn ?? 0, -1, 1) * facing;
  // head shape
  const gr = g.createRadialGradient(-20 + turn * 18, HEAD_CY - 26, 10, 0, HEAD_CY, HEAD_RX * 1.1);
  gr.addColorStop(0, C.bodyLight);
  gr.addColorStop(0.55, C.body);
  gr.addColorStop(1, C.bodyShade);
  g.fillStyle = gr; g.strokeStyle = C.line; g.lineWidth = 3.2;
  g.beginPath();
  g.ellipse(turn * 3, HEAD_CY, HEAD_RX, HEAD_RY, 0, 0, TAU);
  g.fill(); g.stroke();

  // tuft (secondary motion: lags behind head tilt and trembles)
  const sway = fbm(t * 0.7, 8) * 0.25 - (pose.headTilt || 0) * 0.8 + clamp(pose.tremble || 0) * noise1(t * 24, 9) * 0.25;
  g.save();
  g.translate(turn * 14, HEAD_CY - HEAD_RY + 4);
  g.rotate(sway);
  g.fillStyle = C.body; g.strokeStyle = C.line; g.lineWidth = 3;
  g.beginPath();
  g.moveTo(-9, 4);
  g.bezierCurveTo(-14, -26, 6, -44, 18, -40);
  g.bezierCurveTo(28, -36, 26, -22, 16, -22);
  g.bezierCurveTo(8, -22, 8, -30, 14, -31);
  g.bezierCurveTo(4, -30, 4, -12, 9, 4);
  g.closePath(); g.fill(); g.stroke();
  g.restore();

  // face — mirror back so it's drawn in true orientation when facing -1
  g.save();
  g.translate(0, HEAD_CY + 8);
  g.scale(facing, 1);
  const face = makeExpr(pose.face || {});
  face.t = t;
  face.turn = (pose.headTurn ?? 0) + (face.turn || 0) * 0;
  if (!face.noAutoBlink) face.blink = clamp((face.blink || 0) + autoBlink(t, 11, 0.3 + (pose.tremble || 0) * 0.25));
  drawFace(g, FEAR_FACE, face);
  g.restore();
}

function drawArm(g, side, a, t, trem, crouch, br) {
  const sx = side * SHOULDER_X, sy = SHOULDER_Y + crouch * 18 + br;
  const [tx0, ty0] = a.target;
  const tx = tx0 + trem * noise1(t * 33 + side, 12) * 3;
  const ty = ty0 + trem * noise1(t * 29 + side, 13) * 3;
  const L1 = 46, L2 = 44;
  const { a1, a2 } = ik(sx, sy, tx, ty, L1, L2, a.bend ?? -side);
  const p = limb(g, sx, sy, L1, L2, a1, a2, 8.5, 7, C.bodyShade, C.line);
  // hand
  const ang = a1 + a2;
  g.save();
  g.translate(p.hx, p.hy);
  g.rotate(ang);
  g.fillStyle = C.body; g.strokeStyle = C.line; g.lineWidth = 2.4;
  if (a.hand === 'palm') {
    // open palm facing viewer, fingers along the forearm direction (used to cover face)
    g.beginPath(); g.ellipse(9, 0, 15, 14, 0, 0, TAU); g.fill(); g.stroke();
    for (const f of [-9, 0, 9]) { g.beginPath(); g.ellipse(25, f * 1.05, 8, 5.2, f * 0.04, 0, TAU); g.fill(); g.stroke(); }
    g.beginPath(); g.ellipse(6, -15, 7, 5, -0.8, 0, TAU); g.fill(); g.stroke();
  } else if (a.hand === 'fist' || a.hand === 'grip') {
    ellipse(g, 4, 0, 10, 9); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(6, -5); g.lineTo(10, 5); g.stroke();
  } else {
    // little three-finger mitten
    g.beginPath();
    g.ellipse(5, 0, 11, 9, 0, 0, TAU);
    g.fill(); g.stroke();
    for (const f of [-5, 0, 5]) {
      g.beginPath(); g.ellipse(15, f, 5, 3.4, f * 0.05, 0, TAU); g.fill(); g.stroke();
    }
  }
  g.restore();
}
