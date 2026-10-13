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
//   armL, armR { target:[x,y] (character-local, origin at feet, y up is negative), bend:+1/-1, front:bool,
//                hand: 'open'|'rest'|'palm'|'flat'|'drape'|'cup'|'fist'|'grip'|'point'|'pinch' or a pose object (hand.mjs),
//                palmDir [x,y,z] where the palm faces (z toward camera) or roll, wrist (radians), spread, curl, holding }
//              or a preset name from FEAR_ARMS
//   walk       { phase: radians } for a walk cycle (legs swing, body bobs)
//   feetTurn   -1..1 feet from front-on (0, default standing) to pointing along local +x (default 0.75 walking)
//   scarfWind  -1..1 scarf ends sway
//   shadow     true to draw a ground shadow
//   alpha      overall opacity

import { clamp, lerp, TAU, fbm, noise1, autoBlink, ik, limb, ellipse, circle, groundShadow, shade, rgba, smoothShake } from '../engine.mjs';
import { drawFace, makeExpr } from '../face.mjs';
import { drawHand, makeHandStyle, TOON3 } from '../hand.mjs';

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

/** Fear's emotional shaking (engine.smoothShake): scenes that overlay things on Fear use the same numbers */
export const fearShake = (t, trem) => smoothShake(t, trem, 0);

// head geometry (local to neck)
const HEAD_CY = -66, HEAD_RX = 74, HEAD_RY = 68;
const NECK_Y = -148; // from feet
const SHOULDER_Y = -134, SHOULDER_X = 27;

/** arm presets: targets relative to feet origin */
export const FEAR_ARMS = {
  // hanging relaxed along the body: fingers down, palm toward the side of the body, thumb forward
  rest: (side) => ({ target: [side * 39, -80], bend: -side, hand: 'rest', handAng: Math.PI / 2 - side * 0.22 }),
  hugSelf: (side) => ({ target: [-side * 14, -118], bend: side, front: true, hand: 'drape', palmDir: [0, 0, -1] }),
  wringHands: (side) => ({ target: [side * 4, -104], bend: side, front: true, hand: 'fist', palmDir: [-side, 0, -0.35] }),
  handsOnFace: (side) => ({ target: [side * 30, -192], bend: -side, front: true, hand: 'open', palmDir: [0, 0, -1] }),
  peek: (side) => ({ target: [side * 24, -170], bend: -side, front: true, hand: 'open', spread: 0.34, palmDir: [0, 0, -1] }),
  coverMouth: (side) => ({ target: [side * 10, -164], bend: -side, front: true, hand: 'flat', palmDir: [0, 0, -1] }),
  reachUp: (side) => ({ target: [side * 92, -196], bend: side, hand: 'grip', front: true, palmDir: [0, 0, -1] }),
  wipeEye: (side) => ({ target: [side * 34, -186], bend: -side, front: true, hand: 'fist', palmDir: [-side * 0.3, 0, -1] }),
  chest: (side) => ({ target: [side * 8, -128], bend: side, front: true, hand: 'flat', palmDir: [0, 0, -1] }),
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
  const sh = fearShake(t, trem);

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

  // legs; the feet point where the body faces: toward the camera, or (feetTurn ±1, default while walking) along the
  // direction of travel (local +x = the facing direction)
  const ft = clamp(pose.feetTurn ?? (walk ? 0.75 : 0), -1, 1);
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
    drawFoot(g, footX, footY, side, ft);
  }

  g.translate(sh.x, sh.y);
  g.rotate((pose.lean || 0) + sh.rot);

  const arms = [resolveArm(pose.armL, -1), resolveArm(pose.armR, 1)];
  // back arms (not 'front')
  for (const side of [-1, 1]) {
    const a = arms[side < 0 ? 0 : 1];
    if (!a.front) drawArm(g, side, a, t, sh, crouch, br, pose.whiten);
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
  const wind = (pose.scarfWind || 0) + fbm(t * 0.6, 4) * 0.15 + sh.scarf;
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
  g.rotate((pose.headTilt || 0) + sh.head);
  drawFearHead(g, pose, t, facing, sh);
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
    if (a.front) drawArm(g, side, a, t, sh, crouch, br, pose.whiten);
  }
  g.restore();
}

/** a little rounded foot: front-on it is a toe cap under the leg; turned, it lengthens toward the facing side */
function drawFoot(g, x, y, side, ft) {
  const a = Math.abs(ft);
  const rx = lerp(10, 13.5, a), ry = lerp(8.2, 7, a);
  const cx = x + ft * 6, cy = y - ry * 0.62;
  g.fillStyle = '#6c5a9e'; g.strokeStyle = C.line; g.lineWidth = 2.4;
  ellipse(g, cx, cy, rx, ry); g.fill(); g.stroke();
  // sole edge + toe light (reads as the front of the foot, not a flat disc)
  g.save();
  ellipse(g, cx, cy, rx, ry); g.clip();
  g.fillStyle = 'rgba(40,28,80,0.35)';
  g.fillRect(cx - rx, cy + ry * 0.45, rx * 2, ry);
  const gr = g.createRadialGradient(cx - rx * 0.25 + ft * rx * 0.35, cy - ry * 0.35, 0, cx - rx * 0.25 + ft * rx * 0.35, cy - ry * 0.35, rx * 0.8);
  gr.addColorStop(0, 'rgba(255,255,255,0.28)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(cx - rx, cy - ry, rx * 2, ry * 2);
  g.restore();
}

function drawFearHead(g, pose, t, facing, sh) {
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
  const sway = fbm(t * 0.7, 8) * 0.25 - (pose.headTilt || 0) * 0.8 + sh.tuft;
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

/** Fear's transform from the world to its body frame (feet origin, facing, shake, lean) — for things drawn ON Fear
 *  by a scene (returns the shake, so a head frame can follow: fearHeadSpace) */
export function fearBodySpace(g, x, y, scale, pose) {
  const t = pose.t || 0;
  const sh = fearShake(t, clamp(pose.tremble || 0));
  g.translate(x, y); g.scale(scale, scale); g.scale(pose.facing || 1, 1);
  g.translate(sh.x, sh.y);
  g.rotate((pose.lean || 0) + sh.rot);
  return sh;
}
const fearBreath = (pose) => Math.sin((pose.t || 0) * TAU * (pose.breathRate || (0.28 + clamp(pose.tremble || 0) * 0.5))) * (pose.breathe ?? 1);
/** from the body frame to the head's neck pivot (same as drawFear) */
export function fearHeadSpace(g, pose, sh) {
  const crouch = clamp(pose.crouch || 0);
  g.translate(pose.headDX || 0, NECK_Y + crouch * 20 + fearBreath(pose) * 1.2 + (pose.headDY || 0));
  g.rotate((pose.headTilt || 0) + sh.head);
}
/** Fear's front arms again, exactly as drawFear draws them (to lay them over something drawn on Fear's body) */
export function drawFearFrontArms(g, x, y, scale, pose) {
  g.save();
  const sh = fearBodySpace(g, x, y, scale, pose);
  const crouch = clamp(pose.crouch || 0), br = fearBreath(pose);
  for (const side of [-1, 1]) {
    const a = resolveArm(side < 0 ? pose.armL : pose.armR, side);
    if (a.front) drawArm(g, side, a, pose.t || 0, sh, crouch, br, pose.whiten);
  }
  g.restore();
}

export const FEAR_HAND = makeHandStyle(TOON3, 30, { skin: C.body, light: C.bodyLight, shade: C.bodyShade, line: C.line }, 2.4);
// hand shape per arm spec: hand 'open'|'rest'|'palm'|'fist'|'grip'|'point'|... or a pose object; palmDir/roll
// orient it (see hand.mjs). Presets name their own; otherwise a relaxed open hand.
const HAND_ALIAS = { open: 'open', palm: 'palm', fist: 'fist', grip: 'grip' };

function drawArm(g, side, a, t, sh, crouch, br, whiten = 0) {
  const sx = side * SHOULDER_X, sy = SHOULDER_Y + crouch * 18 + br;
  const [tx0, ty0] = a.target;
  const [ox, oy] = sh.arm(side);
  const tx = tx0 + ox, ty = ty0 + oy;
  const L1 = 46, L2 = 44;
  const { a1, a2 } = ik(sx, sy, tx, ty, L1, L2, a.bend ?? -side);
  const p = limb(g, sx, sy, L1, L2, a1, a2, 8.5, 7, C.bodyShade, C.line);
  // hand (the wrist bends a little toward the gesture; presets give palmDir so the thumb sits where anatomy puts it)
  const ang = a.handAng != null ? a.handAng : a1 + a2 + (a.wrist || 0);
  const shape = typeof a.hand === 'object' && a.hand ? a.hand : HAND_ALIAS[a.hand] || a.hand || 'open';
  g.save();
  g.translate(p.hx, p.hy);
  drawHand(g, FEAR_HAND, { ang, shape, roll: a.roll, palmDir: a.palmDir || (a.roll == null ? defaultPalm(shape, side, ang) : null), chir: side, curl: a.curl, spread: a.spread, holding: a.holding, whiten });
  g.restore();
}

/** where the palm faces when a spec doesn't say: by the hips the palms face the body; raised hands show their
 *  backs when near the face; fists turn their thumbs up */
function defaultPalm(shape, side, ang) {
  const up = -Math.sin(ang); // >0: fingers point upward
  if (shape === 'palm' || shape === 'wave') return [0, 0, 1];
  if (shape === 'rest' || shape === 'open') return up > 0.5 ? [0, 0, -1] : [-side * 0.9, 0, -0.45];
  if (shape === 'fist' || shape === 'grip') return [-side * 0.6, 0.2, -0.8];
  return [-side * 0.6, 0, -0.8];
}
