// s03 · the_void · MIND_HQ (front view) · cut in on the CEO's head turn from s02
// The reveal: over the CEO's shoulder the camera tilts up from the spreading shadow, the hem, the still folds, to a
// hood of pure darkness. "The Void." — a locked wide where nothing moves. Then a slow push into the darkness.
//
// Shots (data/staging.md §3 s03):
//  A  S.start → s03b02     {560,760,1.5} → {470,520,1.5} tilt up; voidShadow 0.15 → 0.7; Fear lowers its arm and
//                          shrinks against the station; the CEO's head tips back; a mote drifts into the hood
//  B  s03b02 → s03b03      LOCKED {560,690,1.25}: nothing moves, nobody blinks (CEO leans back, hand to the floor)
//  C  s03b03 → S.end       {450,400,1.6} → {450,277,8.5} exponential push into the hood's darkness

import { clamp, lerp, ease, mix, blinkAt, applyCamera, drift, vignette, noise1, ik, TAU } from '../engine.mjs';
import { makeExpr } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, selfLocal, selfPoseAnchors } from '../chars/self.mjs';
import { drawVoid, voidRig } from '../chars/void.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';

export const id = 's03';

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const CAGE_F = [302, 846, 0.3];
const CEO_AT_ALARM_F = [640, 1000, 0.444];
const FEAR_ALARM_F = [734, 973, 0.42];

const E = (...p) => makeExpr(...p);
const sstep = (a, b, x) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };

function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}

// the hood's face centre in world coords (for the push-in and the mote)
const FACE = (() => { const r = voidRig({ ...STARE_F }); return [VOID_F[0] + r.face[0] * VOID_F[2], VOID_F[1] + r.face[1] * VOID_F[2]]; })();

function camera(S, t) {
  const tB = S.T('s03b02'), tC = S.T('s03b03');
  if (t < tB) {
    const k = ease.inOut(clamp((t - S.start) / (tB - S.start)));
    const d = drift(t, 2.2, 3);
    return { x: lerp(560, 470, k), y: lerp(760, 520, k), zoom: 1.5, shakeX: d.dx, shakeY: d.dy, rot: d.dr * 0.5, shot: 'A' };
  }
  if (t < tC) return { x: 560, y: 690, zoom: 1.25, shot: 'B' }; // LOCKED: no drift
  // exponential push: the hood's on-screen offset from the frame centre eases to 0 while the zoom grows
  // geometrically, so the darkness grows at a steady, inexorable rate
  const k = ease.sine(clamp((t - tC) / (S.end - tC)));
  const z = 1.6 * Math.pow(8.5 / 1.6, k);
  const ox = (FACE[0] - 450) * 1.6 * (1 - k), oy = (FACE[1] - 400) * 1.6 * (1 - k);
  const d = drift(t, 1.6 * (1 - k), 5);
  return { x: FACE[0] - ox / z, y: FACE[1] - oy / z, zoom: z, shakeX: d.dx, shakeY: d.dy, shot: 'C' };
}

// "Nothing moves in the frame at all" (s03b02): idle time (mist, breath, tuft, hair) slows to a near-stop during
// the locked wide; keyed actions still use real time. The cuts on both sides hide the change of pace.
function idleT(S, t) {
  const a = S.T('s03b02'), b = S.T('s03b03');
  return t >= a && t < b ? a + (t - a) * 0.12 : t;
}

// ---------------------------------------------------------------- Fear's pointing finger (local helper, as in s02)
function fearFinger(g, x, y, s, pose, side, alpha = 1) {
  const a = side < 0 ? pose.armL : pose.armR;
  if (!a || !a.target || alpha <= 0.01) return;
  const t = pose.t, trem = clamp(pose.tremble || 0), crouch = clamp(pose.crouch || 0), facing = pose.facing || 1;
  const br = Math.sin(t * TAU * (pose.breathRate || (0.28 + trem * 0.5))) * (pose.breathe ?? 1);
  g.save();
  g.translate(x, y); g.scale(s, s); g.scale(facing, 1);
  g.translate(trem * noise1(t * 38, 1) * 2.2, trem * noise1(t * 41, 2) * 1.4);
  g.rotate((pose.lean || 0) + trem * noise1(t * 30, 3) * 0.015);
  const sx = side * 27, sy = -134 + crouch * 18 + br;
  const tx = a.target[0] + trem * noise1(t * 33 + side, 12) * 3, ty = a.target[1] + trem * noise1(t * 29 + side, 13) * 3;
  const { a1, a2 } = ik(sx, sy, tx, ty, 46, 44, a.bend ?? -side);
  const ex = sx + Math.cos(a1) * 46, ey = sy + Math.sin(a1) * 46;
  const hx = ex + Math.cos(a1 + a2) * 44, hy = ey + Math.sin(a1 + a2) * 44;
  g.translate(hx, hy); g.rotate(a1 + a2 + (pose.fingerWobble || 0));
  g.globalAlpha *= alpha;
  g.lineCap = 'round';
  g.strokeStyle = '#3d2c66'; g.lineWidth = 8.6;
  g.beginPath(); g.moveTo(9, -3); g.lineTo(25, -4.5); g.stroke();
  g.strokeStyle = '#b9a6ea'; g.lineWidth = 4.4;
  g.beginPath(); g.moveTo(9, -3); g.lineTo(25, -4.5); g.stroke();
  g.restore();
}

// ---------------------------------------------------------------- Fear (front view, at the alarm)
function fearPose(S, t) {
  const s0 = S.start;
  // starts as s02 ended: facing 1, arm pointing up-left; lowers the arm, flinches round (facing −1) and shrinks
  // back against the station; in b02 it freezes, not even blinking
  const lower = S.k(t, [['scene.start+0.55', 0], ['scene.start+1.25', 1, 'inOut']]);
  const flipAt = S.T('scene.start+1.3');
  const facing = t < flipAt ? 1 : -1;
  const shrink = S.k(t, [['scene.start+1.2', 0], ['scene.start+1.55', 0.35, 'outCubic'], ['s03b02-0.5', 0.6, 'inOut']]);
  const frozen = S.k(t, [['s03b02-0.2', 0], ['s03b02+0.1', 1]]);
  const pointT = [-90, -184], scarf = [-6, -120];
  let armL, armR;
  if (facing > 0) {
    const p = [lerp(pointT[0], -58, ease.sine(clamp(lower * 1.6))), lerp(pointT[1], -124, ease.sine(clamp(lower * 1.6)))];
    const q = lower > 0.62 ? [lerp(-58, scarf[0], (lower - 0.62) / 0.38), lerp(-124, scarf[1], (lower - 0.62) / 0.38)] : p;
    armL = { target: q, bend: 1, front: true, hand: 'fist' };
    armR = { target: [10, -122], bend: 1, front: true, hand: 'fist' };
  } else {
    armL = 'hugSelf'; armR = 'hugSelf';
  }
  const scared = E({ browIn: 0.95, browUp: 0.75, lidU: -0.32, pupil: 0.55, smile: -0.45, wide: 0.3, open: 0.12, lookX: -0.62, lookY: -0.8, tremble: 0.6 });
  const peek = E({ browIn: 1, browUp: 0.85, lidU: -0.38, pupil: 0.5, smile: -0.5, wide: 0.2, open: 0.0, pressed: 0.5, lookX: -0.6, lookY: -0.82, tremble: 0 });
  const face = mix(scared, peek, frozen);
  face.noAutoBlink = frozen > 0.01 || t < s0 + 0.3;
  // the flinch-round (facing flips at S.start+1.3) happens inside a blink: the lids are shut on the frames on
  // both sides of the flip (a blinkAt pulse starting at the flip left the flip frame open-eyed)
  // (the rig only shuts the lids fully when lidU ≥ 0: the wide-eyed lidU is relaxed under the blink)
  const bk = S.k(t, [['scene.start+1.21', 0], ['scene.start+1.27', 1], ['scene.start+1.37', 1], ['scene.start+1.47', 0]]) * (1 - frozen);
  face.blink = bk;
  face.lidU = lerp(face.lidU, 0, bk);
  if (bk > 0) face.noAutoBlink = true;
  return {
    t: idleT(S, t), facing, face, crouch: shrink, tremble: 0.8 * (1 - frozen),
    lean: facing < 0 ? -0.07 * shrink / 0.6 : 0.0,
    headTilt: facing < 0 ? 0.1 : -0.1, headTurn: facing < 0 ? -0.15 : -0.25,
    headDY: shrink * 6, breathe: 1 - 0.85 * frozen,
    armL, armR, shadow: true, finger: facing > 0 ? clamp(1 - lower * 2.2) : 0, fingerWobble: Math.sin(t * 23) * 0.06,
  };
}

// ---------------------------------------------------------------- the CEO (back view, kneeling)
function ceoPose(S, t) {
  // completes the turn begun at the end of s02: the head is already over the left shoulder, tipping back as the
  // camera rises; a visible swallow; in b02 leans back half an inch, a hand finds the floor; then stone still
  const tip = S.k(t, [['scene.start', 0], ['s03b02-0.3', 1, 'inOut']]);
  const swallow = S.k(t, [['s03b01+1.9', 0], ['s03b01+2.05', 1], ['s03b01+2.35', 0]]);
  const back = S.k(t, [['s03b02+0.15', 0], ['s03b02+0.75', 1, 'inOut']]);
  const frozen = S.k(t, [['s03b02-0.1', 0], ['s03b02+0.2', 1]]);
  const [x, y, s] = CEO_AT_ALARM_F;
  const pose = {
    t: idleT(S, t) + 0.7, outfit: 'ceo', view: 'back', kneel: 1, facing: 1, clipboard: true, armL: 'rest',
    headTurn: lerp(-0.35, -0.25, tip), headTilt: -0.04 - 0.05 * tip, headDY: 3 * tip + 2.5 * swallow + 2 * back,
    lean: -0.05 * back, shrug: 0.15 * tip + 0.1 * swallow, breathe: 1 - 0.85 * frozen,
    face: E({ noAutoBlink: true }),
  };
  if (back > 0.01) {
    // the near (right) hand drops back and finds the floor beside the back knee; the clipboard stays at the hip
    const a = selfPoseAnchors(x, y, s, pose);
    const sh = selfLocal(x, y, s, 1, ...a.shoulderR);
    pose.armR = { target: [lerp(sh[0] + 6, sh[0] - 6, back), lerp(sh[1] + 175, -12, back)], bend: 1, hand: 'flat', handAngle: Math.PI / 2 - 0.25, layer: 'side' };
  }
  return pose;
}

// ---------------------------------------------------------------- one dust mote, dying out at the hood's rim
// It drifts down over the hood's crown fabric (up-right of the opening) toward the opening's upper-right rim and
// fades out BEFORE it reaches the dark: the light dies near the hood. (It used to come to rest at the centre of the
// opening, where it read as a single glowing pupil just before "its face was pure darkness" — the face has no eyes,
// and any light inside the hood belongs to s14's reveal.) Opening half-size ≈ 29.6 × 41.4 world px (80 × 112 × 0.37).
function mote(g, S, t) {
  const a = S.T('s03b01+1.5'), b = S.T('s03b01+3.0');
  if (t < a || t > b) return;
  const k = (t - a) / (b - a);
  const x = lerp(FACE[0] + 50, FACE[0] + 27, ease.sine(k)) + Math.sin(k * 5) * 1.5;
  const y = lerp(FACE[1] - 80, FACE[1] - 36, k) + Math.sin(k * 3.7) * 1.2;
  const alpha = Math.min(1, k * 5) * (1 - sstep(0.5, 0.88, k));
  g.save(); g.globalCompositeOperation = 'lighter';
  const r = 6.5;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, `rgba(235,228,255,${0.9 * alpha})`); gr.addColorStop(0.3, `rgba(180,160,255,${0.38 * alpha})`); gr.addColorStop(1, 'rgba(170,150,255,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r);
  g.restore();
}

// =========================================================================== render
export function render(g, t, S) {
  const c = camera(S, t);
  const shadow = S.k(t, [['scene.start', 0.15], ['s03b02-0.6', 0.7, 'out']]);
  const st = { t: idleT(S, t), lightsDim: 0.35, consoleGlow: 0.8, mist: 0.6, voidShadow: shadow, alarm: 0, alarmPulled: 0 };
  const close = c.shot === 'C';
  g.save();
  applyCamera(g, c);
  drawHQ(g, 'front', st);
  drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0, cosmos: 0, shadow: false });
  if (!close) {
    drawCage(g, ...CAGE_F, { t: idleT(S, t), door: 1, locked: 0 });
    const fp = fearPose(S, t);
    drawFear(g, ...FEAR_ALARM_F, fp);
    fearFinger(g, ...FEAR_ALARM_F, fp, -1, fp.finger);
    const cp = ceoPose(S, t);
    drawSelf(g, ...CEO_AT_ALARM_F, cp);
    drawHQForeground(g, 'front', st);
  }
  mote(g, S, t);
  g.restore();
  grade(g, 0.35, 0);
  vignette(g, 0.45);
}

// =========================================================================== sound
export const sfx = [
  { at: 'scene.start+0.9', name: 'breath_shaky', gain: -20, pan: 0.35 },
  { at: 's03b01-0.3', name: 'rumble_low', gain: -14 },
  { at: 's03b02+0.12', name: 'cloth_rustle', gain: -22, pan: 0.25 },
  { at: 's03b03-1.2', name: 'rumble_low', gain: -14 },
  { at: 's03b03+3.4', name: 'rumble_low', gain: -16 },
];
