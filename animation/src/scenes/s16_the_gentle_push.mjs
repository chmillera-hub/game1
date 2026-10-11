// s16 · the_gentle_push · backOfMind. Fear wipes its tears; the Void's enormous hand gives the gentlest
// push; Fear stops, looks back at the stars in the dark hood, smiles for real, and skips off toward the HQ.
import { clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { star } from '../face.mjs';
import { createCanvas } from '@napi-rs/canvas';
import { drawHQ, drawHQForeground, hqScaleAt } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';
import { drawVoid, drawVoidArm, drawVoidHand, drawVoidGlow, voidRig, toVoidLocal, VOID_HANDS } from '../chars/void.mjs';
import { drawFear, FEAR_COLORS } from '../chars/fear.mjs';

export const id = 's16';

export const sfx = [
  // b01: the wipes, the big wet sniff, the shaky breath out that is almost a laugh
  { at: 'scene.start+0.05', name: 'cloth_rustle', gain: -20, pan: -0.1 },
  { at: 's16b01+0.56', name: 'cloth_rustle', gain: -21, pan: 0.1 },
  { at: 's16b01+0.5', name: 'breath_shaky', gain: -16 },           // 2nd catch = the sniff (+1.35), exhale = the half-laugh
  // b02: the sleeve stirs as the hand comes out, the fingertips meet Fear's back, two little steps
  { at: 's16b02-0.1', name: 'cloth_rustle', gain: -17, pan: 0.35 },
  { at: 's16b02+1.65', name: 'cloth_rustle', gain: -19, pan: 0.2 },
  { at: 's16b02+1.97', name: 'footsteps', gain: -15, rate: 1.35, until: 's16b02+2.75' },
  { at: 's16b02+2.67', name: 'footsteps', gain: -16, rate: 1.35, until: 's16b02+3.2' },
  // b03: walks on and stops; the hand slides back into the folds; the galaxies twinkle
  { at: 's16b02+3.47', name: 'footsteps', gain: -16, rate: 1.3, until: 's16b03+1.05' },
  { at: 's16b03+1.25', name: 'cloth_rustle', gain: -21, pan: 0.45 },
  { at: 's16b03+2.75', name: 'twinkle', gain: -14 },
  // b04: the skip back toward the HQ
  { at: 'scene.end-1.76', name: 'footsteps', gain: -15, rate: 1.4, until: 'scene.end-0.3' },   // one per hop landing
];

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const COSMOS_RESIDUE = 0.5;
const CAGE_B = [430, 1630, 0.952];
const THRESH = [440, 1648, 0.97];
const FEAR_STOP_B = [250, 1700, 1.065];
const VOID_ARM_B = { bend: 1 };
const PUSH_ANGLE = Math.PI - 0.55;
const APPROACH_PUSH = [110, -10];
const SLEEVE_CLIP_Y = 1100;
const STEP1 = [390, 1665, 1.01], STEP2 = [330, 1680, 1.035];
const HOOD = (() => { const f = voidRig(STARE_B).face; return [VOID_B[0] + f[0] * VOID_B[2], VOID_B[1] + f[1] * VOID_B[2]]; })();

// ---------------------------------------------------------------- local helpers
function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function starlight(g, x, y, r, k) {
  if (k <= 0) return;
  g.save(); g.globalCompositeOperation = 'screen';
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, `rgba(176,150,255,${0.30 * k})`); gr.addColorStop(0.55, `rgba(110,200,255,${0.12 * k})`);
  gr.addColorStop(1, 'rgba(110,200,255,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore();
}
const sleeveFront = (g, pose) => {
  g.save(); g.beginPath(); g.rect(-1e4, SLEEVE_CLIP_Y, 2e4, 2e4); g.clip();
  drawVoidArm(g, ...VOID_B, pose, 'L', 'sleeve'); g.restore();
};
const cam = (t, c, amp = 2.5) => { const d = drift(t, amp); return { ...c, shakeX: d.dx, shakeY: d.dy, rot: d.dr }; };
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp3 = (p, q, k) => [lerp(p[0], q[0], k), lerp(p[1], q[1], k), lerp(p[2], q[2], k)];

// the scarf end that Fear wipes its eyes with: a knitted strip from the scarf knot up into the fist (world
// coords), then the fist redrawn over it so the cloth is held, not stuck on the face
function scarfEnd(g, fx, fy, fs, facing, hand, k) {
  if (k <= 0.01) return;
  const [hx, hy] = hand;
  const side = hx > fx ? 1 : -1;                                     // the end on the wiping hand's side
  const nx = fx + side * 16 * fs, ny = fy - 140 * fs;                 // where the end leaves the wrap
  const mx = lerp(nx, hx, 0.45) + side * 10 * fs, my = lerp(ny, hy, 0.45) + 14 * fs;
  g.save();
  g.globalAlpha = k;
  g.lineCap = 'round'; g.lineJoin = 'round';
  g.strokeStyle = FEAR_COLORS.line; g.lineWidth = 13 * fs;
  g.beginPath(); g.moveTo(nx, ny); g.quadraticCurveTo(mx, my, hx, hy + 4 * fs); g.stroke();
  g.strokeStyle = FEAR_COLORS.scarf; g.lineWidth = 8.6 * fs;
  g.beginPath(); g.moveTo(nx, ny); g.quadraticCurveTo(mx, my, hx, hy + 4 * fs); g.stroke();
  g.strokeStyle = FEAR_COLORS.scarf2; g.lineWidth = 2.6 * fs;
  for (const q of [0.35, 0.7]) {
    const ax = (1 - q) * (1 - q) * nx + 2 * (1 - q) * q * mx + q * q * hx, ay = (1 - q) * (1 - q) * ny + 2 * (1 - q) * q * my + q * q * (hy + 4 * fs);
    g.beginPath(); g.moveTo(ax - 3.5 * fs, ay - 2 * fs); g.lineTo(ax + 3.5 * fs, ay + 2 * fs); g.stroke();
  }
  // the fist closed around it
  g.fillStyle = FEAR_COLORS.body; g.strokeStyle = FEAR_COLORS.line; g.lineWidth = 2.4 * fs;
  g.beginPath(); g.ellipse(hx, hy, 10.5 * fs, 9.5 * fs, 0, 0, Math.PI * 2); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(hx - facing * 3 * fs, hy - 5 * fs); g.lineTo(hx + facing * 1 * fs, hy + 4 * fs); g.stroke();
  g.restore();
}

// ---------------------------------------------------------------- shots
function shotOf(t, S) {
  if (t < S.T('s16b02')) return 'A';          // medium: the wipe
  if (t < S.T('s16b03')) return 'B';          // side: the push
  if (t < S.T('s16b03+2.6')) return 'C';      // front medium: walks on, stops, looks back
  if (t < S.T('s16b04')) return 'D';          // over Fear's shoulder: the starry hood
  return 'E';                                  // close: the smile, the nod, the skip
}

// ---------------------------------------------------------------- Fear's path & pose
function fearPlace(t, S) {
  const s1 = ease.inOut(seg(t, S.T('s16b02+1.94'), S.T('s16b02+2.42')));
  const s2 = ease.inOut(seg(t, S.T('s16b02+2.62'), S.T('s16b02+3.08')));
  const s3 = ease.sine(seg(t, S.T('s16b02+3.55'), S.T('s16b03+1.0')));
  let p = THRESH;
  if (s1 > 0) p = lerp3(THRESH, STEP1, s1);
  if (s2 > 0) p = lerp3(STEP1, STEP2, s2);
  if (s3 > 0) p = lerp3(STEP2, FEAR_STOP_B, s3);
  // the skip out of frame-left (b04 end): a hop on each step, along the floor toward the way back
  // (≈1.1 s on screen at zoom 2.8; it leaves the frame at ≈ scene.end-0.56 and the last 0.5 s stay empty)
  const sk = seg(t, S.T('scene.end-1.7'), S.T('scene.end-0.5'));
  let hop = 0;
  if (sk > 0) {
    const k = ease.in(sk) * 0.25 + sk * 0.75;                      // clears the frame edge (x ≈ 51) at ≈ scene.end-0.56
    const x = lerp(FEAR_STOP_B[0], 40, k), y = lerp(FEAR_STOP_B[1], 1686, k);
    p = [x, y, hqScaleAt('backOfMind', y)];
    hop = Math.abs(Math.sin(sk * Math.PI * 3)) * 16;
  }
  // distance walked → walk phase (Fear's foot swing is ±14 local: ~28 local units per step)
  const d = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const walked = d(THRESH, STEP1) * s1 + d(STEP1, STEP2) * s2 + d(STEP2, FEAR_STOP_B) * s3;
  const skipD = sk > 0 ? (FEAR_STOP_B[0] - p[0]) : 0;
  return { x: p[0], y: p[1] - hop * p[2], s: p[2], walking: (s1 > 0 && s1 < 1) || (s2 > 0 && s2 < 1) || (s3 > 0 && s3 < 1) || (sk > 0 && sk < 1),
    phase: (walked / 30) * Math.PI + (skipD / 34) * Math.PI, sk, hop };
}

function fearPose(t, S, shot) {
  const gx = fbm(t * 0.4, 51) * 0.06, gy = fbm(t * 0.35, 53) * 0.05;
  const P = fearPlace(t, S);
  const pose = { t, facing: -1, tremble: 0, scarfWind: 0 };
  if (P.walking) pose.walk = { phase: P.phase };
  let face;

  // ---- b01: the wipes (one eye, then the other), a big wet sniff, a shaky breath out that is almost a laugh
  // all of it inside b01's 2 s (+ the 0.45 s before it), so the half-laugh peaks in this medium, not on the cut
  const w1 = S.k(t, [['scene.start-0.3', 0.6], ['scene.start+0.1', 1], ['s16b01+0.36', 1], ['s16b01+0.57', 0]]);
  const w2 = S.k(t, [['s16b01+0.59', 0], ['s16b01+0.8', 1], ['s16b01+1.02', 1], ['s16b01+1.2', 0]]);
  const rub = (a) => Math.sin((t - S.T(a)) * 13) * 4;
  const sniff = S.k(t, [['s16b01+1.18', 0], ['s16b01+1.34', 1], ['s16b01+1.55', 0.2], ['s16b02+0.1', 0]]);
  // the shaky breath out that is almost a laugh: eyes crinkle, the gaze drops level, a wobbly open smile
  const laugh = S.k(t, [['s16b01+1.48', 0], ['s16b01+1.82', 1], ['s16b02+0.45', 0.6], ['s16b02+1.2', 0]]);
  const tearsA = S.k(t, [['scene.start', 0.7], ['s16b01+1.5', 0.32], ['s16b02+1.0', 0.25]]);
  // ---- b02: the touch, a surprised tip forward, arms out; then a second step on its own
  const surprise = S.k(t, [['s16b02+1.78', 0], ['s16b02+1.95', 1, 'outCubic'], ['s16b02+2.9', 0.7], ['s16b02+3.6', 0.25]]);
  const arms = S.k(t, [['s16b02+1.9', 0], ['s16b02+2.1', 1, 'outCubic'], ['s16b02+2.6', 0.85], ['s16b02+3.1', 0.15], ['s16b02+3.5', 0]]);
  const tip = S.k(t, [['s16b02+1.88', 0], ['s16b02+2.05', 1], ['s16b02+2.4', 0.3], ['s16b02+2.7', 0]]);
  const dart = S.k(t, [['s16b02+1.84', 0], ['s16b02+1.96', 1], ['s16b02+2.35', 1], ['s16b02+2.6', 0]]);
  // ---- b03: stops, looks back over its scarf (eyes first, then the head)
  const eyesBack = S.k(t, [['s16b03+1.05', 0], ['s16b03+1.25', 1]]);
  const headBack = S.k(t, [['s16b03+1.2', 0], ['s16b03+1.75', 1, 'inOut']]);
  // ---- b04: the smile arrives (eyes first), a last tear, a nod; turns to the light and skips
  const relax = S.k(t, [['s16b04-0.4', 0], ['s16b04+0.7', 1]]);
  const eyeSmile = S.k(t, [['s16b04+0.2', 0], ['s16b04+0.9', 1]]);
  const blush = S.k(t, [['s16b04+0.4', 0], ['s16b04+1.1', 1]]);
  const mouth = S.k(t, [['s16b04+0.75', 0], ['s16b04+1.5', 1, 'sine']]);
  const tearDrop = S.k(t, [['s16b04+0.9', 0], ['s16b04+2.1', 1, 'linear']]);
  const nod = S.k(t, [['s16b04+1.7', 0], ['s16b04+1.88', 1], ['s16b04+2.12', 0]]);
  const turnFwd = S.k(t, [['scene.end-1.9', 0], ['scene.end-1.62', 1, 'inOut']]);
  const eyesFwd = S.k(t, [['scene.end-2.02', 0], ['scene.end-1.88', 1]]);

  // head: looking back over the scarf, up at the hood (up-right on screen)
  const back = headBack * (1 - turnFwd);
  pose.headTurn = lerp(-0.12, 0.55, back) - 0.42 * turnFwd;
  pose.headTilt = 0.1 * back + 0.04 * Math.sin(Math.PI * nod) - 0.06 * turnFwd;
  pose.headDY = -5 * sniff + 5 * nod;
  pose.lean = -0.08 * tip + 0.05 * clamp(P.sk * 3) * (1 - P.sk);
  pose.crouch = 0.12 * S.k(t, [['scene.end-1.86', 0], ['scene.end-1.74', 1], ['scene.end-1.64', 0]]);
  pose.breathe = 1 + 1.4 * sniff;

  const lookBackX = lerp(lerp(-0.3, 0.6, dart), 0.7, eyesBack) * (1 - eyesFwd) - 0.75 * eyesFwd;
  const lookBackY = lerp(lerp(-0.55, -0.15, dart), -0.9, eyesBack) * (1 - eyesFwd) - 0.1 * eyesFwd;

  face = {
    lookX: lookBackX + gx, lookY: lookBackY + gy,
    browIn: lerp(0.55, 0.0, relax) + 0.25 * surprise, browUp: 0.15 * (1 - relax) + 0.6 * surprise,
    lidU: 0.05 - 0.3 * surprise - 0.05 * eyeSmile - 0.08 * laugh, lidL: 0.32 * eyeSmile + 0.38 * laugh, lidTilt: 0.12 * (1 - relax),
    smile: 0.1 + 0.48 * laugh - 0.15 * surprise + 0.55 * mouth, open: 0.17 * laugh + 0.16 * surprise, round: 0.5 * surprise,
    tremble: 0.35 * laugh + 0.15 * (1 - relax) * (shot === 'A' ? 1 : 0), pupil: 1.1 + 0.15 * eyesBack,
    tears: Math.max(tearsA, shot === 'D' || shot === 'E' ? lerp(0.6, 0.3, tearDrop) : 0),
    tearR: tearDrop > 0 && tearDrop < 1 ? tearDrop : 0,
    blush: 0.12 + 0.4 * blush, sparkle: 0.25 + 0.3 * eyesBack * (1 - eyesFwd),
  };
  // wipes: a crying squeeze while the fist rubs (eyes down), eyes shut tight for the sniff
  const wipe = Math.max(w1, w2);
  face.lidU += 0.3 * wipe; face.lidTilt += 0.3 * wipe; face.browIn += 0.3 * wipe; face.browUp += 0.12 * wipe;
  face.lookY = lerp(face.lookY, 0.25, wipe); face.lookX = lerp(face.lookX, -0.1, wipe);
  face.smile -= 0.18 * wipe; face.tremble += 0.3 * wipe;
  face.blink = Math.max(S.k(t, [['s16b01+1.19', 0], ['s16b01+1.27', 1], ['s16b01+1.46', 1], ['s16b01+1.58', 0]]), blinkAt(t, S.T('s16b04+0.55'), 0.45),
    blinkAt(t, S.T('scene.end-1.98'), 0.2));                      // a quick blink carries the turn toward the HQ
  face.noAutoBlink = t > S.T('s16b04+0.3') || (t > S.T('s16b01+1.0') && t < S.T('s16b02+0.3'));
  face.browIn += 0.35 * sniff + 0.2 * laugh; face.browUp += 0.25 * sniff;
  face.lookY = lerp(face.lookY, -0.1, 0.7 * laugh); face.lookX = lerp(face.lookX, -0.15, 0.6 * laugh);
  face.lidU -= 0.06 * laugh;
  pose.headDY += 3 * laugh * Math.max(0, Math.sin((t - S.T('s16b01+1.48')) * 15));     // the breath hitches out
  if (sniff > 0.3) face.pressed = 0.7 * sniff;
  // the turn toward the console light: bright, open, a little skip of joy
  face.lidU -= 0.18 * turnFwd; face.lidL -= 0.2 * turnFwd; face.browUp += 0.3 * turnFwd; face.browIn -= 0.1 * turnFwd;
  face.open += 0.12 * turnFwd; face.smile += 0.1 * turnFwd;
  // the slow blink as the smile reaches the eyes: inner brows soften up (tender, not sleepy)
  face.browIn += 0.25 * clamp(blinkAt(t, S.T('s16b04+0.55'), 0.45) * 2);
  pose.face = face;

  // arms
  pose.armL = { target: [-14, -118], bend: -1, front: true, hand: 'fist' };   // resting together at the belly
  pose.armR = { target: [12, -116], bend: 1, front: true, hand: 'fist' };
  if (w1 > 0.01) pose.armR = { target: [lerp(12, 30, w1) + 0.6 * rub('scene.start') * w1, lerp(-116, -198, w1) + 0.5 * rub('scene.start') * w1], bend: -1, front: true, hand: 'fist' };
  if (w2 > 0.01) pose.armL = { target: [lerp(-14, -30, w2) + 0.6 * rub('s16b01+0.55') * w2, lerp(-118, -198, w2) + 0.5 * rub('s16b01+0.55') * w2], bend: 1, front: true, hand: 'fist' };
  if (arms > 0.01) {
    pose.armL = { target: [lerp(-14, -78, arms), lerp(-118, -112, arms)], bend: 1, hand: 'open' };
    pose.armR = { target: [lerp(12, 80, arms), lerp(-116, -108, arms)], bend: -1, hand: 'open' };
  }
  if (P.walking && arms < 0.01) {
    const sw = Math.sin(P.phase) * 10;
    pose.armL = { target: [-36 + sw, -84], bend: 1, hand: 'open' };
    pose.armR = { target: [36 + sw, -84], bend: -1, hand: 'open' };
  }
  if (P.sk > 0) { // skipping: arms swing happily
    const sw = Math.sin(P.phase) * 14;
    pose.armL = { target: [-44 + sw, -96], bend: 1, hand: 'open' };
    pose.armR = { target: [44 + sw, -96], bend: -1, hand: 'open' };
  }
  pose.scarfWind = 0.4 * P.sk;
  return { pose, P, wipe: { w1, w2 } };
}

// ---------------------------------------------------------------- the Void's push hand
function voidPose(t, S, shot) {
  const show = S.k(t, [['s16b02+0.35', 0], ['s16b02+0.72', 1], ['s16b03+1.55', 1], ['s16b03+1.85', 0]]);
  const reach = S.k(t, [['s16b02', 0], ['s16b02+1.2', 1, 'inOut'], ['s16b03+1.3', 1], ['s16b03+2.0', 0, 'inOut']]);
  const settle = S.k(t, [['s16b02+1.2', 0], ['s16b02+1.8', 1, 'inOut'], ['s16b03+1.0', 1], ['s16b03+1.4', 0, 'inOut']]);
  const nudge = S.k(t, [['s16b02+1.94', 0], ['s16b02+2.4', 1, 'sine'], ['s16b02+2.94', 0, 'sine']]);
  const [fx, fy, fs] = THRESH;
  const back = [fx + 34 * fs, fy - 112 * fs];
  const ap = [back[0] + APPROACH_PUSH[0] * fs, back[1] + APPROACH_PUSH[1] * fs];
  const tgt = [lerp(ap[0], back[0], settle) - 8 * VOID_B[2] * nudge, lerp(ap[1], back[1], settle)];
  const handL = show > 0.001
    ? { ...VOID_HANDS.push(toVoidLocal(...VOID_B, ...tgt), -1), ...VOID_ARM_B, elbow: 0.8 * reach, angle: PUSH_ANGLE, show, reach, defer: 'hand' }
    : { ...VOID_ARM_B, show: 0, defer: 'hand' };
  // only shot D frames the hood; elsewhere the cosmos would be drawn off-frame (≈2 ms), so it is skipped
  return { t, ...STARE_B, idle: 0.5, cosmos: shot === 'D' ? COSMOS_RESIDUE : 0, cosmosOpts: { seed: 7, glyphs: 0 }, shadowSpread: 0.6, handL };
}

// ---------------------------------------------------------------- cameras
function camOf(t, S, shot) {
  if (shot === 'A') return cam(t, { x: 440, y: 1420, zoom: 1.8 + 0.06 * S.k(t, [['scene.start', 0], ['s16b02', 1, 'linear']]) }, 2);
  if (shot === 'B') return cam(t, { x: 420 - 12 * S.k(t, [['s16b02+1.9', 0], ['s16b03', 1]]), y: 1330, zoom: 1.25 }, 2);
  if (shot === 'C') return cam(t, { x: 300, y: 1300, zoom: 1.25 + 0.05 * S.k(t, [['s16b03', 0], ['s16b03+2.6', 1, 'linear']]) }, 2);
  if (shot === 'D') {
    const k = S.k(t, [['s16b03+2.6', 0], ['s16b04', 1, 'linear']]);
    return cam(t, { x: lerp(600, 612, k), y: lerp(720, 690, k), zoom: lerp(0.85, 0.9, k) }, 2);
  }
  return cam(t, { x: 255, y: 1470, zoom: 2.8 }, 1.8);
}

// ---------------------------------------------------------------- render
const BOM = (t) => ({ t, lightsDim: 0.25, mist: 0.45 });

export function render(g, t, S) {
  const shot = shotOf(t, S);
  const st = BOM(t);
  const vp = voidPose(t, S, shot);
  const { pose: fp, P, wipe } = fearPose(t, S, shot);
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#06050d'; g.fillRect(0, 0, 720, 1280);   // base under the stage seams
  g.restore(); g.save();
  applyCamera(g, camOf(t, S, shot));
  drawHQ(g, 'backOfMind', st);
  drawVoid(g, ...VOID_B, vp);
  const cst = { t, door: 0.9, locked: 0 };
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front' });
  if (vp.handL.show > 0) { sleeveFront(g, vp); drawVoidHand(g, ...VOID_B, vp, 'L'); }
  if (shot === 'D') {
    drawVoidGlow(g, ...VOID_B, { ...vp, glow: 0.6 });
    hoodTwinkles(g, t, S);
  } else {
    const exited = shot === 'E' && P.sk >= 0.97;                     // fully past the left frame edge: skip the draw
    if (!exited) {
      drawFear(g, P.x, P.y, P.s, fp);
      // the scarf end in the wiping fist
      const fs = P.s, f = fp.facing;
      const hand = (arm) => [P.x + f * arm.target[0] * fs, P.y + arm.target[1] * fs];
      if (wipe.w1 > 0.01) scarfEnd(g, P.x, P.y, fs, f, hand(fp.armR), clamp(wipe.w1 * 1.5));
      if (wipe.w2 > 0.01) scarfEnd(g, P.x, P.y, fs, f, hand(fp.armL), clamp(wipe.w2 * 1.5));
    }
    starlight(g, P.x + 25 * P.s, P.y - 250 * P.s, 190 * P.s, 0.45);
  }
  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  if (shot === 'D') foregroundFear(g, t, S, fp);
  grade(g, 0.15, 0.15);
  vignette(g, 0.4);
}

// tiny glints among the galaxies on "twinkling" (in addition to the cosmos' own slow twinkle)
function hoodTwinkles(g, t, S) {
  const glints = [[-14, -40, 's16b03+2.7'], [16, 22, 's16b03+2.9'], [-6, 58, 's16b03+3.12'], [10, -12, 's16b03+3.9'], [-12, 30, 's16b03+4.8']];
  g.save();
  g.globalCompositeOperation = 'lighter';
  for (const [dx, dy, at] of glints) {
    const k = Math.sin(Math.PI * seg(t, S.T(at), S.T(at) + 0.7));
    if (k <= 0) continue;
    g.fillStyle = `rgba(255,248,225,${0.9 * k})`;
    star(g, HOOD[0] + dx, HOOD[1] + dy, 7 * k + 2);
    g.fillStyle = `rgba(190,170,255,${0.25 * k})`;
    g.beginPath(); g.arc(HOOD[0] + dx, HOOD[1] + dy, 9 * k + 3, 0, Math.PI * 2); g.fill();
  }
  g.restore();
}

// Over-the-shoulder foreground: Fear's head soft and close in the lower-left (screen space). It is rendered
// at a third of the resolution and scaled up, which gives a cheap, even softness ("out of focus").
let FG = null;
function foregroundFear(g, t, S, fp) {
  const R = 3;
  if (!FG) FG = createCanvas(Math.ceil(720 / R), Math.ceil(1280 / R));
  const c = FG.getContext('2d');
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.clearRect(0, 0, FG.width, FG.height);
  c.setTransform(1 / R, 0, 0, 1 / R, 0, 0);
  const s = 2.6;
  const hx = 122 + fbm(t * 0.3, 61) * 3, hy = 1045 + fbm(t * 0.27, 63) * 2;            // head centre on screen
  const x = hx, y = hy + 214 * s;
  const glisten = S.k(t, [['s16b03+2.6', 0.45], ['s16b04', 0.85]]);
  drawFear(c, x, y, s, {
    t, facing: 1, headTurn: 0.5, headTilt: -0.08, breathe: 0.6, shadow: false,
    // alive while it looks: one slow blink after "galaxies twinkling", the water rising on the lower lids
    face: { ...fp.face, lookX: 0.55 + fbm(t * 0.35, 65) * 0.05, lookY: -0.85, tears: glisten, sparkle: 0.5 + 0.2 * glisten, lidU: 0.02,
      lidL: 0.08 + 0.1 * glisten, smile: 0.05, open: 0.04, browIn: 0.35 + 0.1 * glisten, browUp: 0.2,
      blink: blinkAt(t, S.T('s16b03+4.25'), 0.42), noAutoBlink: true },
    armL: { target: [-30, -80], bend: 1 }, armR: { target: [30, -80], bend: -1 },
  });
  // backlit: darken toward the camera side, starlight on the cheek turned to the hood
  c.globalCompositeOperation = 'source-atop';
  const gr = c.createLinearGradient(hx - 200, hy + 120, hx + 200, hy - 160);
  gr.addColorStop(0, 'rgba(10,8,26,0.62)'); gr.addColorStop(0.6, 'rgba(10,8,26,0.25)'); gr.addColorStop(1, 'rgba(120,150,255,0.12)');
  c.fillStyle = gr; c.fillRect(0, 0, 720, 1280);
  c.globalCompositeOperation = 'source-over';
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.imageSmoothingEnabled = true;
  g.drawImage(FG, 0, 0, FG.width, FG.height, 0, 0, FG.width * R, FG.height * R);
  g.restore();
  starlightScreen(g, hx + 70, hy - 60, 230, 0.35);
}
function starlightScreen(g, x, y, r, k) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); starlight(g, x, y, r, k); g.restore();
}
