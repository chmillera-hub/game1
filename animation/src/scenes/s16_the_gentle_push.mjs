// s16 · the_gentle_push · backOfMind. Fear wipes its tears; the Void's enormous hand gives the gentlest
// push; Fear stops, looks back at the stars in the dark hood, smiles for real, and skips off toward the HQ.
import fs from 'fs';
import { clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { star } from '../face.mjs';
import { drawHQ, drawHQForeground, hqScaleAt } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';
import { drawVoid, drawVoidArm, drawVoidHand, drawVoidGlow, voidRig, toVoidLocal, VOID_HANDS } from '../chars/void.mjs';
import { drawFear, FEAR_COLORS } from '../chars/fear.mjs';

export const id = 's16';

// word starts in s16b03 (data/lines.json) — "The Void stood there, with | galaxies twinkling in its dark | facade."
// — so the cut to the hood lands on "galaxies" and the cut back to Fear on "facade" if the voice is re-rendered
const WORDS = (() => {
  const w = { galaxies: 2.26, facade: 4.8 };
  try {
    const L = JSON.parse(fs.readFileSync(new URL('../../data/lines.json', import.meta.url), 'utf8')).s16b03;
    for (const k of Object.keys(w)) { const x = L.words.find((q) => q.w.toLowerCase().replace(/[^a-z]/g, '') === k); if (x) w[k] = x.start; }
  } catch (e) { /* keep the defaults */ }
  return w;
})();
const W = (word, d = 0) => `s16b03+${(WORDS[word] + d).toFixed(3)}`;

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
  { at: W('galaxies', 0.5), name: 'twinkle', gain: -14 },
  // b04: the skip back toward the HQ
  { at: 'scene.end-1.76', name: 'footsteps', gain: -15, rate: 1.4, until: 'scene.end-0.3' },   // one per hop landing
];

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const COSMOS_RESIDUE = 0.5;
const COSMOS_HOOD = 0.75;   // the hood insert (shot D) only: galaxies bright enough to read on a phone (QA); the hood is
                            // in frame nowhere else in s16, and s17/s19 show it small at COSMOS_RESIDUE
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
// the hand slides out of the cuff while the arm is already swinging, so it is angled off the sleeve's axis: while it
// is still mostly inside (show < ~0.25) a fingertip would poke through the SIDE of the sleeve. Keep it to the far
// side of the cuff opening; the cut-off plane recedes up the sleeve as the hand comes out (gone by show 0.7).
function emergingHand(g, vp) {
  const show = vp.handL.show;
  if (show >= 0.999) { drawVoidHand(g, ...VOID_B, vp, 'L'); return; }
  const A = voidRig(vp).armL, u = [Math.cos(A.fa), Math.sin(A.fa)], n = [-u[1], u[0]];
  const back = 14 + 400 * ease.inOut(clamp((show - 0.3) / 0.4));
  const [vx, vy, vs] = VOID_B;
  const o = [vx + (A.W[0] - u[0] * back) * vs, vy + (A.W[1] - u[1] * back) * vs], R = 1e4;
  g.save();
  g.beginPath();
  g.moveTo(o[0] + n[0] * R, o[1] + n[1] * R); g.lineTo(o[0] - n[0] * R, o[1] - n[1] * R);
  g.lineTo(o[0] - n[0] * R + u[0] * R, o[1] - n[1] * R + u[1] * R); g.lineTo(o[0] + n[0] * R + u[0] * R, o[1] + n[1] * R + u[1] * R);
  g.closePath(); g.clip();
  drawVoidHand(g, ...VOID_B, vp, 'L');
  g.restore();
}
const cam = (t, c, amp = 2.5) => { const d = drift(t, amp); return { ...c, shakeX: d.dx, shakeY: d.dy, rot: d.dr }; };
const seg = (t, a, b) => clamp((t - a) / (b - a));
const lerp3 = (p, q, k) => [lerp(p[0], q[0], k), lerp(p[1], q[1], k), lerp(p[2], q[2], k)];
// blend two of Fear's arm poses (local coords; side −1 = armL, +1 = armR). When the elbow bend or the front/back draw
// order differ, the arm passes through a straight pose hanging out at the side, where the bend flip is invisible and
// the arm barely overlaps the body, so neither switch pops
function armMix(a, b, k, side) {
  if (k <= 0.001) return a;
  if (k >= 0.999) return b;
  const lin = [lerp(a.target[0], b.target[0], k), lerp(a.target[1], b.target[1], k)];
  if (a.bend === b.bend && !!a.front === !!b.front) return { ...(k < 0.5 ? a : b), target: lin };
  const s = Math.sin(Math.PI * k), straight = [side * 72, -56];   // shoulder (±27, −134) + 90 at 30° out from vertical
  return { ...(k < 0.5 ? a : b), target: [lerp(lin[0], straight[0], s), lerp(lin[1], straight[1], s)] };
}

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
  if (t < S.T(W('galaxies', -0.15))) return 'C';   // front medium: walks on, stops, looks back over its shoulder
  if (t < S.T(W('facade', -0.05))) return 'D';     // Fear's eyeline: push in on the hood, galaxies twinkling
  return 'E';                                  // medium close (body to the HQ, head turned back up at the hood):
                                               // brows ease, eyes glisten → the smile, the nod, the skip
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
  // back on Fear after the hood the eyes fill and shine (wonder) at once; the worried inner-up brows hold while it
  // takes in the stars, then from ≈ b04−0.4 they visibly let go (QA: before, the change went unseen until ≈ b04+0.6),
  // ahead of the smile, which is the end of it
  const relax = S.k(t, [[W('facade', -0.05), 0], ['s16b04-0.4', 0.1], ['s16b04+0.45', 0.85, 'inOut'], ['s16b04+0.8', 1]]);
  const glisten = S.k(t, [[W('facade', -0.3), 0], [W('facade', 0.6), 1, 'sine'], ['s16b04+0.9', 1], ['scene.end-1.9', 0.5]]);
  const eyeSmile = S.k(t, [['s16b04+0.2', 0], ['s16b04+0.9', 1]]);
  const blush = S.k(t, [['s16b04+0.4', 0], ['s16b04+1.1', 1]]);
  const mouth = S.k(t, [['s16b04+0.75', 0], ['s16b04+1.5', 1, 'sine']]);
  const tearDrop = S.k(t, [['s16b04+0.9', 0], ['s16b04+2.1', 1, 'linear']]);
  const nod = S.k(t, [['s16b04+1.7', 0], ['s16b04+1.88', 1], ['s16b04+2.12', 0]]);
  const turnFwd = S.k(t, [['scene.end-1.9', 0], ['scene.end-1.62', 1, 'inOut']]);
  const eyesFwd = S.k(t, [['scene.end-2.02', 0], ['scene.end-1.88', 1]]);

  // head: looking back over the scarf, up at the hood (up-right on screen)
  // the look back OVER THE SHOULDER (QA: it read square to camera, as a look up): the body stays pointed the way it
  // was walking (screen-left: see the arms below; it leans a touch into it) while the head turns back toward the
  // hood and shifts over the right shoulder
  const back = headBack * (1 - turnFwd);
  pose.headTurn = lerp(-0.12, 0.74, back) - 0.42 * turnFwd;
  pose.headDX = -5 * back;
  pose.headTilt = 0.1 * back + 0.04 * Math.sin(Math.PI * nod) - 0.06 * turnFwd;
  pose.headDY = -5 * sniff + 5 * nod;
  pose.lean = -0.08 * tip + 0.05 * clamp(P.sk * 3) * (1 - P.sk) + 0.05 * back;
  pose.crouch = 0.12 * S.k(t, [['scene.end-1.86', 0], ['scene.end-1.74', 1], ['scene.end-1.64', 0]]);
  pose.breathe = 1 + 1.4 * sniff;

  const lookBackX = lerp(lerp(-0.3, 0.6, dart), 0.7, eyesBack) * (1 - eyesFwd) - 0.75 * eyesFwd;
  const lookBackY = lerp(lerp(-0.55, -0.15, dart), -0.9, eyesBack) * (1 - eyesFwd) - 0.1 * eyesFwd;

  face = {
    lookX: lookBackX + gx, lookY: lookBackY + gy,
    browIn: lerp(0.55, 0.0, relax) + 0.25 * surprise, browUp: 0.15 * (1 - relax) + 0.6 * surprise,
    lidU: 0.05 - 0.3 * surprise - 0.05 * eyeSmile - 0.08 * laugh, lidL: 0.32 * eyeSmile + 0.38 * laugh, lidTilt: 0.12 * (1 - relax),
    smile: 0.1 + 0.48 * laugh - 0.15 * surprise + 0.55 * mouth, open: 0.17 * laugh + 0.16 * surprise, round: 0.5 * surprise,
    tremble: 0.35 * laugh + 0.15 * (1 - relax) * (shot === 'A' ? 1 : 0), pupil: 1.1 + 0.15 * eyesBack + 0.1 * glisten,
    tears: Math.max(tearsA, shot === 'E' ? lerp(0.35, 0.65, glisten) * lerp(1, 0.5, tearDrop) : 0),
    tearR: tearDrop > 0 && tearDrop < 1 ? tearDrop : 0,
    blush: 0.12 + 0.4 * blush, sparkle: 0.25 + 0.3 * eyesBack * (1 - eyesFwd) + 0.35 * glisten,
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

  // arms (character-local; facing −1, so local +x is screen-left, the way Fear leaves). armL is the screen-RIGHT arm.
  const CLASP_L = { target: [-14, -118], bend: -1, front: true, hand: 'fist' };   // resting together at the belly
  const CLASP_R = { target: [12, -116], bend: 1, front: true, hand: 'fist' };
  const sw = Math.sin(P.phase) * 10, ssw = Math.sin(P.phase) * 14;
  const WALK_L = { target: [-36 + sw, -84], bend: 1, hand: 'open' }, WALK_R = { target: [36 + sw, -84], bend: -1, hand: 'open' };
  const SKIP_L = { target: [-44 + ssw, -96], bend: 1, hand: 'open' }, SKIP_R = { target: [44 + ssw, -96], bend: -1, hand: 'open' };
  // the look back OVER THE SHOULDER (QA: the frontal clasp read square to camera): the body is turned toward the exit,
  // so the near (screen-right) arm crosses the belly to its far side and the far arm hangs hidden behind the body
  const LOOK_L = { target: [8, -114], bend: -1, front: true, hand: 'fist' }, LOOK_R = { target: [26, -92], bend: -1, hand: 'fist' };
  const walkW = S.k(t, [['s16b02+2.75', 0], ['s16b02+3.3', 1]]);                  // the startled arms settle into the walk
  const lookW = S.k(t, [['s16b03+0.95', 0], ['s16b03+1.55', 1, 'inOut']]);         // the stop: arms settle as the head turns back
  const skipW = S.k(t, [['scene.end-1.9', 0], ['scene.end-1.66', 1, 'inOut']]);    // swing out into the skip
  pose.armL = CLASP_L; pose.armR = CLASP_R;
  if (w1 > 0.01) pose.armR = { target: [lerp(12, 30, w1) + 0.6 * rub('scene.start') * w1, lerp(-116, -198, w1) + 0.5 * rub('scene.start') * w1], bend: -1, front: true, hand: 'fist' };
  if (w2 > 0.01) pose.armL = { target: [lerp(-14, -30, w2) + 0.6 * rub('s16b01+0.55') * w2, lerp(-118, -198, w2) + 0.5 * rub('s16b01+0.55') * w2], bend: 1, front: true, hand: 'fist' };
  if (arms > 0.01) {
    // the arms fly out from the clasp and, as they come down, settle toward the walk pose (not back to the clasp, which
    // flashed for two frames between them)
    const bL = lerp3([...CLASP_L.target, 0], [...WALK_L.target, 0], walkW), bR = lerp3([...CLASP_R.target, 0], [...WALK_R.target, 0], walkW);
    pose.armL = { target: [lerp(bL[0], -78, arms), lerp(bL[1], -112, arms)], bend: 1, hand: 'open' };
    pose.armR = { target: [lerp(bR[0], 80, arms), lerp(bR[1], -108, arms)], bend: -1, hand: 'open' };
  } else if (walkW > 0) {
    // walk → (the stop) the look back → the skip, each a blend (the stop used to snap the walk arms into the clasp)
    pose.armL = armMix(armMix(WALK_L, LOOK_L, lookW, -1), SKIP_L, skipW, -1);
    pose.armR = armMix(armMix(WALK_R, LOOK_R, lookW, 1), SKIP_R, skipW, 1);
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
  // ONE arm config for the whole scene (show only hides the hand): at reach 0 it is exactly the rest sleeve
  // (wrist at rest, elbow 0, bend 1), so the sleeve starts moving at s16b02 and never jumps when the hand shows
  const handL = { ...VOID_HANDS.push(toVoidLocal(...VOID_B, ...tgt), -1), ...VOID_ARM_B, elbow: 0.8 * reach, angle: PUSH_ANGLE, show, reach, defer: 'hand' };
  // only shot D frames the hood; elsewhere the cosmos would be drawn off-frame (≈2 ms), so it is skipped
  return { t, ...STARE_B, idle: 0.5, cosmos: shot === 'D' ? COSMOS_HOOD : 0, cosmosOpts: { seed: 7, glyphs: 0 }, shadowSpread: 0.6, handL };
}

// ---------------------------------------------------------------- cameras
function camOf(t, S, shot) {
  if (shot === 'A') return cam(t, { x: 440, y: 1420, zoom: 1.8 + 0.06 * S.k(t, [['scene.start', 0], ['s16b02', 1, 'linear']]) }, 2);
  if (shot === 'B') return cam(t, { x: 420 - 12 * S.k(t, [['s16b02+1.9', 0], ['s16b03', 1]]), y: 1330, zoom: 1.25 }, 2);
  if (shot === 'C') {
    // a gentle push toward Fear once it has stopped and turns to look back over its shoulder
    const k = S.k(t, [['s16b03+0.9', 0], [W('galaxies', -0.15), 1, 'inOut']]);
    return cam(t, { x: lerp(300, 290, k), y: lerp(1300, 1335, k), zoom: lerp(1.25, 1.42, k) }, 2);
  }
  if (shot === 'D') {
    // Fear's eyeline: the hood opening fills the upper middle of the frame (≈ 210×390 px), a slow push in
    const k = S.k(t, [[W('galaxies', -0.15), 0], [W('facade', -0.05), 1, 'linear']]);
    return cam(t, { x: HOOD[0] + 6, y: lerp(350, 336, k), zoom: lerp(1.85, 2.05, k) }, 1.4);
  }
  // E: medium close. Fear on the left third with room to look up-right at the (off-frame) hood; the open cage and the
  // WHOLE TIME-OUT sign behind it on the right (at zoom 2.8 the sign was cropped to a stray "T" in the corner)
  const k = S.k(t, [[W('facade', -0.05), 0], ['scene.end', 1, 'linear']]);
  return cam(t, { x: lerp(332, 338, k), y: lerp(1478, 1474, k), zoom: lerp(1.84, 1.95, k) }, 1.8);
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
  if (vp.handL.reach > 0.001 || vp.handL.show > 0) sleeveFront(g, vp);    // the moving sleeve passes in front of the cage
  if (vp.handL.show > 0) emergingHand(g, vp);
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
  grade(g, 0.15, 0.15);
  vignette(g, 0.4);
}

// tiny glints among the galaxies on "twinkling" (in addition to the cosmos' own slow twinkle)
function hoodTwinkles(g, t, S) {
  const glints = [[-14, -40, W('galaxies', 0.45)], [16, 22, W('galaxies', 0.65)], [-6, 58, W('galaxies', 0.9)], [20, -62, W('galaxies', 1.25)],
    [10, -12, W('galaxies', 1.65)], [-22, 8, W('galaxies', 1.95)], [-12, 34, W('galaxies', 2.3)]];
  g.save();
  g.globalCompositeOperation = 'lighter';
  for (const [dx, dy, at] of glints) {
    const k = Math.sin(Math.PI * seg(t, S.T(at), S.T(at) + 0.7));
    if (k <= 0) continue;
    // a soft halo (a flat disc read as a grey "button" behind the star at this zoom), then the four-point glint
    const x = HOOD[0] + dx, y = HOOD[1] + dy, r = 11 * k + 3;
    const halo = g.createRadialGradient(x, y, 0, x, y, r);
    halo.addColorStop(0, `rgba(205,190,255,${0.32 * k})`); halo.addColorStop(1, 'rgba(190,170,255,0)');
    g.fillStyle = halo; g.fillRect(x - r, y - r, 2 * r, 2 * r);
    g.fillStyle = `rgba(255,248,225,${0.9 * k})`;
    star(g, x, y, 7 * k + 2);
  }
  g.restore();
}
