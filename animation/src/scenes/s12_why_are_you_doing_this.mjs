// s12 · why_are_you_doing_this — Fear's accusations meet absolute silence and collapse into pleas.
// backOfMind throughout. The Void never moves (STARE_B, idle 0, hand hidden with bend 1). The camera keeps
// changing sizes around a stillness that gives nothing back; Fear does all the moving.
import { W, H, TAU, clamp, lerp, ease, noise1, blinkAt, applyCamera, drift, vignette, smoothstep } from '../engine.mjs';
import { makeExpr, withSpeech } from '../face.mjs';
import { drawFear, fearShake } from '../chars/fear.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';
import { createCanvas } from '@napi-rs/canvas';

export const id = 's12';

// ---------------------------------------------------------------- staging constants (staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const CAGE_B = [430, 1630, 0.952];
const VOID_ARM_B = { bend: 1 };
const THRESH = [440, 1648, 0.97];
const FS = CAGE_B[2];
// The gate stands WIDE OPEN (door 0.9, folded out to the left beside the cage) for the whole scene: s11 now swings it
// wide (the ajar 0.3 leaf stood across the doorway and put a stile through Fear's face in s11's close and in b06).
// The doorway runs from the hinge stile (x 354) to the lock jamb (505) with nothing in front of it.
// OCC_SIDE = where s11 leaves Fear (its FEAR_X 392 + the step 23). occupantBack keeps its old +22 nudge (452: the
// closes are framed on it, the lock jamb beside the far eye in b02/b04). In b06 Fear steps into the middle of the open
// doorway (432): from 452 the lock jamb grazed its far eye in the medium; at 432 both eyes are clear of the hinge
// stile and the jamb.
const OCC_SIDE = [415, 1619], OCC_BACK = [452, 1598], OCC_FRONT = [432, 1630];
const DOOR_OPEN = 0.9;
const DOORWAY_Y = 1642;
// Fear's rig (src/chars/fear.mjs): neck pivot and head centre (local), face origin = head centre + 8
const NECK_Y = -148, HEAD_CY = -66, HEAD_RX = 74, HEAD_RY = 68;
// the inside-cage closes keep ONE piece of the front layer: the right (lock) jamb with the popped padlock, so the
// glances at "the open gate" have something to land on. Bars left of this x (the hinge stile at 354, the back bars)
// would cross the face; the jamb bar (x≈505) runs just right of the far eye and is masked out behind the head.
const LOCK_STRIP_X = 497;
// b06: the right hand on the lock jamb (cage x +79 local) at shoulder height, above the padlock's staple (510,1516)
const JAMB_GRIP = [505, 1478];
// the reach path (Fear-local): chin → hip (arm almost straight, 87 of 90 long) → up onto the jamb
const REACH_C0 = [20, -70], REACH_OUT = [66, -56], REACH_C1 = [98, -98];
const quad = (a, c, b, u) => [(1 - u) * (1 - u) * a[0] + 2 * (1 - u) * u * c[0] + u * u * b[0], (1 - u) * (1 - u) * a[1] + 2 * (1 - u) * u * c[1] + u * u * b[1]];

export const sfx = [
  { at: 'scene.start+0.564', name: 'footsteps', gain: -19, rate: 1.31, until: 'scene.start+1.25', fade: 0.12 }, // two tiny shuffles back: steps land on the contacts (+0.63, +1.05)
  { at: 's12b05+0.35', name: 'breath_shaky', gain: -14 },                                          // breath held … the exhale (file 1.45) leaks out at +1.8 with the body
  { at: 's12b06+0.32', name: 'footsteps', gain: -18, until: 's12b06+1.15', fade: 0.12 },           // the step to the gate
  { at: 's12b07+0.5', name: 'footsteps', gain: -18, until: 's12b07+0.75', fade: 0.08 },            // stepping out: foot lands at +0.58
  { at: 's12b07+0.88', name: 'footsteps', gain: -11, until: 's12b07+1.25', fade: 0.1 },            // the tiny furious stamp on 'hurt'
  { at: 's12b09+1.9', name: 'sob', gain: -14 },                                                    // 'forever' breaks into a sob
  { at: 's12b10+0.15', name: 'cloth_rustle', gain: -21 },                                          // nose wiped on the scarf
  { at: 's12b10+1.1', name: 'sob', gain: -21, until: 's12b10+1.55', fade: 0.12 },                  // a hiccup
  { at: 's12b11+1.95', name: 'breath_shaky', gain: -23, until: 's12b11+3.6', fade: 0.4 },          // small uneven breaths in the narrator's pause
];

// ---------------------------------------------------------------- helpers
function finish(g, cold, warm, vig) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  if (warm > 0) { g.globalCompositeOperation = 'overlay'; g.fillStyle = `rgba(255,170,90,${0.4 * warm})`; g.fillRect(0, 0, W, H); }
  g.globalCompositeOperation = 'source-over';
  vignette(g, vig);
  g.restore();
}
const withDrift = (cam, t, amp = 2.5) => { const d = drift(t, amp, 3); return { ...cam, shakeX: d.dx, shakeY: d.dy, rot: d.dr }; };
const camLerp = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), zoom: Math.exp(lerp(Math.log(a.zoom), Math.log(b.zoom), k)) });
const E = (...p) => makeExpr(...p);
const bump = (t, c, w) => { const d = Math.abs(t - c) / w; return d >= 1 ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * d); };
const lerp2 = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
// body hitches that follow the sob sfx file (hitches at 0.05 / 0.21 / 0.35, whimper catches 0.56 / 0.83)
const sobHitch = (t, at, catches = 1) => bump(t, at + 0.07, 0.07) + bump(t, at + 0.23, 0.07) + bump(t, at + 0.37, 0.07)
  + catches * (0.6 * bump(t, at + 0.58, 0.09) + 0.5 * bump(t, at + 0.85, 0.09));

// Fear's face transform: replicates drawFear → drawFearHead up to drawFace's origin (facing 1), so overlays
// (the chin crumple, the head mask of the lock strip) sit exactly on the drawn face, tremble included.
function faceXform(g, F, t) {
  const trem = clamp(F.tremble || 0), crouch = clamp(F.crouch || 0);
  const br = Math.sin(t * TAU * (F.breathRate || (0.28 + trem * 0.5))) * (F.breathe ?? 1);
  g.translate(F.pos[0], F.pos[1]); g.scale(F.scale, F.scale);
  const sh = fearShake(t, trem);
  g.translate(sh.x, sh.y);
  g.rotate((F.lean || 0) + sh.rot);
  g.translate(F.headDX || 0, NECK_Y + crouch * 20 + br * 1.2 + (F.headDY || 0));
  g.rotate((F.headTilt || 0) + sh.head);
  g.translate(0, HEAD_CY + 8);
}
// world point of the face origin, smooth (no breath / shiver): used to frame the closes
function faceAt(F) {
  return [F.pos[0] + ((F.headDX || 0) + clamp(F.headTurn, -1, 1) * 32 * 0.5) * F.scale,
    F.pos[1] + (NECK_Y + 20 * clamp(F.crouch || 0) + (F.headDY || 0) + HEAD_CY + 8) * F.scale];
}

// the chin crumples (mentalis): the lower lip pushes up into a dimpled little ball under a frowning mouth.
// face.mjs has no chin parameter, so it is drawn here, in face coordinates, just above the scarf (y < 57).
function chinCrumple(g, F, k, t) {
  if (k <= 0.01) return;
  const e = F.face, W0 = 19;
  const mx = clamp(F.headTurn, -1, 1) * 32 * 0.45, my = 38;
  const pressed = clamp(e.pressed || 0), open = clamp(e.open || 0) * (1 - pressed * 0.9), round = clamp(e.round || 0);
  const h = W0 * 1.3 * open * (1 + 0.35 * round);
  const smile = clamp(e.smile || 0, -1, 1);
  const under = h < 1.6 ? Math.max(1.5, -smile * W0 * 0.12) : h * 0.72 + smile * W0 * 0.1;
  const q = 0.8 * Math.sin(t * TAU * 4.3) + 0.5 * Math.sin(t * TAU * 6.1 + 1.7);       // the chin quivers
  const y0 = Math.min(my + under + 4.5 + q * 0.5 * k, 52);
  const hw = 9 + 2 * k;
  g.save();
  faceXform(g, F, t);
  g.lineCap = 'round';
  // the ball of the chin: a soft shaded cup under the lip
  const gr = g.createRadialGradient(mx, y0 + 1, 0, mx, y0 + 1, hw);
  gr.addColorStop(0, `rgba(61,44,102,${0.16 * k})`); gr.addColorStop(1, 'rgba(61,44,102,0)');
  g.fillStyle = gr; g.beginPath(); g.ellipse(mx, y0 + 1, hw, hw * 0.55, 0, 0, TAU); g.fill();
  // its lower contour, bumpy: the dimpled "pebbled" skin
  g.strokeStyle = `rgba(61,44,102,${0.62 * k})`; g.lineWidth = 1.7;
  g.beginPath();
  for (let i = 0; i <= 12; i++) {
    const u = i / 12, x = mx + (u * 2 - 1) * hw;
    const y = y0 + 4.2 * Math.sin(u * Math.PI) + 0.9 * k * Math.sin(u * Math.PI * 4 + t * 9) * Math.sin(u * Math.PI);
    if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
  }
  g.stroke();
  // three tiny dimples
  g.fillStyle = `rgba(61,44,102,${0.4 * k})`;
  for (const [dx, dy] of [[-4.2, 1.6], [0.6, 2.6], [4.8, 1.4]]) { g.beginPath(); g.arc(mx + dx, y0 + dy + 0.3 * q, 0.95, 0, TAU); g.fill(); }
  g.restore();
}

// the inside-cage closes: only the right (lock) jamb and the popped padlock of the front layer, masked out
// behind Fear's head (so the jamb never crosses the face; it reads as passing behind the head)
function lockStrip(g, cst, F, t) {
  g.save();
  // from the eye line down: above it the strip would catch the end of the TIME-OUT sign and the jamb's top
  const yTop = faceAt(F)[1] - 14 * F.scale;
  g.beginPath(); g.rect(LOCK_STRIP_X, yTop, 2e4, 2e4); g.clip();
  g.beginPath(); g.rect(-1e4, -1e4, 2e4, 2e4);
  g.save(); faceXform(g, F, t);
  g.ellipse(clamp(F.headTurn, -1, 1) * 3, -8, HEAD_RX + 2.5, HEAD_RY + 2.5, 0, 0, TAU);
  g.restore();
  g.clip('evenodd');
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front' });
  g.restore();
}

// ---------------------------------------------------------------- shots
// cage: 'full' | 'cheat' (inside-cage close: back layer only, §1.7-10) | 'cheatLock' (cheat + the lock jamb)
// The closes frame Fear's FACE (QA: the old 2.0–2.2 "closes" were full-length figures): b01 a big close-up with the
// darkness above it, b02/b04 true face close-ups inside the cage, b03 a medium-close (inside-cage cheat) with the
// fold of the sleeve above, b08/b09 a face close-up on the threshold. The wides (b05, b10) are unchanged.
function shot(t, S, F) {
  const T = (a) => S.T(a);
  // frame the face at screen (sx, sy) for zoom z, using the face position at a reference time (no head tracking)
  const frame = (ref, z, sx, sy) => { const f = faceAt(fearState(T(ref), S)); return { x: f[0] + (W / 2 - sx) / z, y: f[1] + (H / 2 - sy) / z, zoom: z }; };
  const push = (a, b, z0, z1) => Math.exp(lerp(Math.log(z0), Math.log(z1), ease.sine(clamp((t - T(a)) / (T(b) - T(a))))));
  // (s11 now ends on a close of Fear looking up, and cuts on the look to this wide: the reveal of the hood gets
  // ~1.25 s — the two shuffle steps and a beat — before the close takes 'this?' and the crack)
  if (t < T('s12b01+0.8')) {
    const k = ease.sine(clamp((t - S.start) / (T('s12b02') - S.start)));
    return { cam: withDrift(camLerp({ x: 560, y: 900, zoom: 0.8 }, { x: 560, y: 940, zoom: 0.8 }, k), t), cage: 'full' };
  }
  if (t < T('s12b02-0.3')) {
    // b01 close-up: the face low-left, looking up and back into the dark of the robe; the chin tips up on 'this'
    const z = push('s12b01+0.8', 's12b02-0.3', 2.6, 2.7);
    const c = frame('s12b01+1.0', 2.6, 318, 770);
    return { cam: withDrift(frame('s12b01+1.0', z, 318, 770), t, 2), cage: 'cheat', bake: { key: 'b01', x: c.x, y: c.y, zMin: 2.6, zMax: 2.7, m: 1.12, at: 's12b01+1.0' } };
  }
  if (t < T('s12b03-0.25')) {
    const z = push('s12b02-0.3', 's12b03-0.25', 3.95, 4.1);
    const c = frame('s12b02+0.5', 3.95, 352, 610);
    return { cam: withDrift(frame('s12b02+0.5', z, 352, 610), t, 1.5), cage: 'cheatLock', bake: { key: 'b02', x: c.x, y: c.y, zMin: 3.95, zMax: 4.1, m: 1.12, at: 's12b02+0.5' } };
  }
  if (t < T('s12b04-0.2')) {
    // b03 medium-close, inside the cage: the face low in the frame, the dark fold of the sleeve where the hand
    // went (cuff ≈ (464,1096)) hanging at the top. (Through the ajar gate the door's top rail and centre stile
    // crossed the squint at any size.)
    const z = push('s12b03-0.25', 's12b04-0.2', 2.45, 2.52);
    const c = frame('s12b03+0.4', 2.45, 372, 905);
    return { cam: withDrift(frame('s12b03+0.4', z, 372, 905), t, 2), cage: 'cheat', bake: { key: 'b03', x: c.x, y: c.y, zMin: 2.45, zMax: 2.52, m: 1.12, at: 's12b03+0.4' } };
  }
  if (t < T('s12b05')) {
    const z = push('s12b04-0.2', 's12b05', 3.95, 4.1);
    const c = frame('s12b04+0.3', 3.95, 352, 610);
    return { cam: withDrift(frame('s12b04+0.3', z, 352, 610), t, 1.5), cage: 'cheatLock', bake: { key: 'b04', x: c.x, y: c.y, zMin: 3.95, zMax: 4.1, m: 1.12, at: 's12b04+0.3' } };
  }
  if (t < T('s12b06-0.1')) return { cam: { x: 500, y: 889, zoom: 0.72 }, cage: 'full' };                     // LOCKED
  if (t < T('s12b07-0.3')) {
    const k = ease.sine(clamp((t - T('s12b06-0.1')) / 2.6));
    return { cam: withDrift(camLerp({ x: 450, y: 1380, zoom: 1.6 }, { x: 452, y: 1384, zoom: 1.66 }, k), t), cage: 'full' };
  }
  if (t < T('s12b08-0.3')) return { cam: withDrift({ x: 560, y: 980, zoom: 0.8 }, t), cage: 'full' };
  if (t < T('s12b10')) {
    // b08 → b09: one face close-up on the threshold, from above; a slight push through the plea, the camera
    // easing down after the face as Fear sinks onto the threshold
    const c0 = frame('s12b08+0.6', 3.7, 360, 575);
    const f = faceAt(F), follow = ease.sine(clamp((t - T('s12b09+1.2')) / 1.6));
    const z = push('s12b09', 's12b10', 3.7, 4.05);
    const y = lerp(c0.y, f[1] + (H / 2 - 640) / z, 0.75 * follow);
    return { cam: withDrift({ x: c0.x, y, zoom: z }, t, 1.5), cage: 'full', bake: { key: 'b08', x: c0.x, y: c0.y + 22, zMin: 3.7, zMax: 4.05, m: 1.3, at: 's12b08+0.6', front: true } };
  }
  return { cam: { x: 500, y: 889, zoom: 0.72 }, cage: 'full' };                                               // LOCKED
}

// ---------------------------------------------------------------- Fear
const FROZEN = E({ browIn: 0.8, browUp: 0.65, lidU: -0.22, pupil: 0.62, smile: -0.35, open: 0.12, wide: 0.05, tears: 0.85, stream: 0.6, lookX: 0.36, lookY: -1 });
// The five faces of the accusation are pushed apart so they read as five different thoughts at phone size
// (QA: they all read as one wide-eyed worried look-up). ACCUSE/CRACK: wide, brows up. CERTAIN: lids lowered, brows
// knit, chin trembling. SUSPECT: squeezed from below, brows DOWN, eyes sliding sideways. CONFUSED: one brow up,
// one down. SHOUT: hard V, mouth wide. PLEA: brows tipped up, chin crumpled, streaming.
const ACCUSE = E({ browIn: 1, browUp: 0.6, lidU: -0.18, pupil: 0.66, smile: -0.5, tremble: 0.6, tears: 0.85, stream: 0.55, lookX: 0.4, lookY: -1 });
const CRACK = E(ACCUSE, { browUp: 1, browIn: 1, lidU: -0.32, pupil: 0.6, wide: 0.25 });
const CERTAIN = E({ browIn: 0.6, browUp: -0.12, browSquish: 0.75, lidTilt: 0.3, lidU: 0.02, lidL: 0.42, smile: -0.72, wide: 0.15, tremble: 1, tears: 1, stream: 0.65, pupil: 0.72, lookX: 0.4, lookY: -0.9 });
// suspicious squint from BELOW (lower lids right up, inner corners low), brows pulled DOWN and in, eyes slid to the
// side; the upper lid stays light (a heavy upper lid over an up-looking iris reads as an eye-roll)
const SUSPECT = E({ lidU: 0.16, lidL: 1, lidTilt: -0.4, browIn: -0.75, browUp: -0.3, browUpL: -0.12, browUpR: 0.22, browSquish: 1, smile: -0.32, wide: -0.32, tremble: 0.35, tears: 0.75, stream: 0.5, pupil: 0.8, lookX: 0.85, lookY: -0.5 });
const CONFUSED = E({ browUpL: 1, browUpR: -0.6, browIn: 0.35, browSquish: 0.25, lidU: 0.0, lidL: 0.12, smile: -0.28, wide: -0.2, open: 0.06, tremble: 0.3, tears: 0.78, stream: 0.5, pupil: 0.88, lookX: 0.3, lookY: -0.8 });
const WAITING = E({ browIn: 0.72, browUp: 0.48, lidU: -0.16, pupil: 0.68, smile: -0.22, pressed: 0.55, tears: 0.82, stream: 0.5, lookX: 0.38, lookY: -1 });
const CRUMBLE = E({ browIn: 1, browUp: 0.4, lidTilt: 0.6, lidU: 0.18, lidL: 0.22, smile: -0.62, tremble: 0.85, pressed: 0.25, tears: 1, stream: 0.6, pupil: 0.8, lookX: 0.38, lookY: -0.95 });
const CRY = E({ browIn: 1, browUp: 0.35, lidTilt: 0.75, lidU: 0.16, lidL: 0.32, smile: -0.75, wide: 0.3, tremble: 0.95, tears: 1, stream: 0.72, pupil: 0.85, lookX: 0.36, lookY: -0.9 });
const FURY = E({ browIn: -0.55, browSquish: 0.85, browUp: -0.15, lidU: 0.14, lidL: 0.35, lidTilt: -0.25, smile: -0.6, wide: 0.35, teeth: 0.45, tremble: 0.55, tears: 1, stream: 0.75, pupil: 0.8, lookX: 0.42, lookY: -1 });
// SHOUT: brows in a hard V, eyes squeezed half shut from below (cheeks up) — heavy upper lids + eyes up read as an
// eye-roll — and the mouth held wide open under the words
const SHOUT = E({ lidU: 0.2, lidL: 0.62, lidTilt: -0.5, browIn: -1, browUp: -0.35, browSquish: 1, open: 0.6, wide: 0.65, teeth: 0.85, smile: -0.55, tremble: 0.5, tears: 1, stream: 0.85, pupil: 0.75, lookX: 0.32, lookY: -0.6 });
// PLEA: the anger collapses — brows tip right up in the middle, lids droop, the chin crumples (drawn: chinCrumple)
const PLEA = E({ browIn: 1, browUp: 0.55, browSquish: 0.35, lidTilt: 0.95, lidU: 0.14, lidL: 0.38, smile: -0.9, wide: 0.45, tremble: 1, tears: 1, stream: 1, pupil: 0.9, lookX: 0.32, lookY: -0.8 });
const SOBBING = E(PLEA, { lidU: 0.92, lidL: 0.5, open: 0.22, lookY: 0.3 });
const SPENT = E({ browIn: 0.78, browUp: 0.1, lidTilt: 0.7, lidU: 0.42, lidL: 0.15, smile: -0.45, tremble: 0.3, tears: 0.7, stream: 0.75, pupil: 0.9, lookX: 0.05, lookY: 0.62 });

function fearState(t, S) {
  const T = (a) => S.T(a);

  // ---------------- position / walking
  // shuffle back: occupantSide → occupantBack (two small steps), eyes never leave the hood
  const sh = clamp((t - T('scene.start+0.2')) / (T('s12b01+0.6') - T('scene.start+0.2')));
  let pos = lerp2(OCC_SIDE, OCC_BACK, ease.sine(sh));
  let walk = sh > 0 && sh < 1 ? sh * 2 * Math.PI : 0;
  let scale = FS;
  // b06: one step forward to the gate (occupantFront)
  const st6 = clamp((t - T('s12b06+0.4')) / 0.6);
  if (st6 > 0) { pos = lerp2(OCC_BACK, OCC_FRONT, ease.sine(st6)); walk = st6 < 1 ? st6 * Math.PI : 0; }
  // b07: through the gate onto the threshold (two quick steps), then the stamp on 'hurt'
  const st7 = clamp((t - T('s12b07+0.32')) / 0.52);
  if (st7 > 0) {
    pos = lerp2(OCC_FRONT, THRESH, ease.sine(st7));
    scale = lerp(FS, THRESH[2], ease.sine(st7));
    walk = st7 < 1 ? st7 * 2 * Math.PI : 0;
  }
  const stampT = T('s12b07+0.96');
  const stampLift = t > stampT - 0.16 && t < stampT ? Math.sin(((t - (stampT - 0.16)) / 0.16) * Math.PI / 2) : 0;
  if (stampLift > 0) walk = 2 * Math.PI + stampLift * Math.PI / 2;
  const stampHit = bump(t, stampT + 0.05, 0.1);

  // ---------------- face (keyed through the beats)
  const faceK = S.k(t, [
    ['scene.start-1', FROZEN], ['s12b01-0.1', FROZEN], ['s12b01+0.25', ACCUSE], ['s12b01+0.82', ACCUSE], ['s12b01+1.0', CRACK, 'out'],
    ['s12b01.end+0.15', CRACK], ['s12b01.end+0.6', ACCUSE],
    ['s12b02-0.2', CERTAIN], ['s12b02.end+0.2', CERTAIN],
    ['s12b03-0.15', SUSPECT, 'out'], ['s12b03.end+0.1', SUSPECT],
    ['s12b04+0.05', CONFUSED], ['s12b04.end+0.2', E(CONFUSED, { browUpL: 0.75, browUpR: -0.35, browIn: 0.55 })],
    ['s12b05+0.25', WAITING], ['s12b05+2.1', WAITING], ['s12b05+2.95', CRUMBLE],
    ['s12b06+0.3', CRY], ['s12b06.end+0.5', CRY],
    ['s12b07-0.05', FURY, 'out'], ['s12b07.end+0.2', FURY],
    ['s12b08-0.15', SHOUT, 'out'], ['s12b08.end+0.2', SHOUT],
    ['s12b09+0.35', PLEA], ['s12b09+1.75', PLEA], ['s12b09+2.05', SOBBING, 'out'], ['s12b09+2.9', SOBBING],
    ['s12b10+0.5', SPENT],
  ]);
  const face = { ...faceK };

  // gaze: eyelines are absolute (the hood up-right, the gate down in front, the glow up-left)
  // (the closes show the popped padlock low on the right: the glances "at the gate" go down-right onto it)
  const HOOD = { lookX: 0.38, lookY: -1 }, GATE = { lookX: 0.45, lookY: 0.95 };
  let gz = null;
  const gaze = (keys) => S.k(t, keys);
  if (t >= T('s12b02-0.3') && t < T('s12b03-0.25')) {
    // "eyes flick to the open gate and back up, as if the gate were bait"
    gz = gaze([['s12b02+0.18', HOOD], ['s12b02+0.3', GATE, 'out'], ['s12b02+0.66', GATE], ['s12b02+0.8', HOOD, 'out']]);
  } else if (t >= T('s12b03-0.25') && t < T('s12b04-0.2')) {
    // suspicious: the eyes dart to the fold where the hand went, then back to the hood
    const HOOD_SQ = { lookX: 0.85, lookY: -0.5 }, FOLD_SQ = { lookX: 0.06, lookY: -0.86 };   // side-eye at the hood; the fold is straight above
    gz = gaze([['s12b03-0.25', HOOD], ['s12b03+0.12', HOOD_SQ], ['s12b03+0.22', FOLD_SQ, 'out'], ['s12b03+0.5', FOLD_SQ], ['s12b03+0.6', HOOD_SQ, 'out'], ['s12b03+0.95', HOOD_SQ], ['s12b03+1.03', { lookX: 0.12, lookY: -0.84 }, 'out'], ['s12b03+1.2', HOOD_SQ, 'out'], ['s12b04-0.2', HOOD, 'sine']]);
  } else if (t >= T('s12b04-0.2') && t < T('s12b05+0.25')) {
    // the glance at the gate again, longer this time
    gz = gaze([['s12b04+0.5', HOOD], ['s12b04+0.66', GATE, 'out'], ['s12b05-0.05', GATE], ['s12b05+0.2', HOOD, 'out']]);
  } else if (t >= T('s12b05+0.25') && t < T('s12b06')) {
    // searching the hood for any sign; following its stare into the distance; back up
    gz = gaze([['s12b05+0.3', HOOD], ['s12b05+0.4', { lookX: 0.27, lookY: -0.9 }, 'out'], ['s12b05+0.7', { lookX: 0.27, lookY: -0.9 }],
      ['s12b05+0.8', { lookX: 0.5, lookY: -1 }, 'out'], ['s12b05+1.1', { lookX: 0.5, lookY: -1 }], ['s12b05+1.2', { lookX: 0.33, lookY: -0.82 }, 'out'],
      ['s12b05+1.5', { lookX: 0.33, lookY: -0.82 }], ['s12b05+2.05', { lookX: -0.2, lookY: -0.88 }, 'sine'],   // along its stare to the far glow
      ['s12b05+2.35', { lookX: -0.2, lookY: -0.88 }], ['s12b05+2.6', HOOD, 'sine']]);
  } else if (t >= T('s12b06') && t < T('s12b07')) {
    // looking at the gate as it steps to it, then back up at the hood for the line's end
    gz = gaze([['s12b06+0.2', { lookX: 0.3, lookY: -0.95 }], ['s12b06+0.45', { lookX: 0.2, lookY: 0.55 }, 'out'], ['s12b06+1.3', { lookX: 0.2, lookY: 0.55 }], ['s12b06+1.55', HOOD, 'out']]);
  } else if (t >= T('s12b10') && t < T('s12b11')) {
    gz = gaze([['s12b10+1.45', { lookX: 0.05, lookY: 0.62 }], ['s12b10+1.6', { lookX: 0.4, lookY: -1 }, 'out'], ['s12b10+2.15', { lookX: 0.4, lookY: -1 }], ['s12b10+2.4', { lookX: 0.0, lookY: 0.6 }, 'sine']]);
  }
  if (gz) { face.lookX = gz.lookX; face.lookY = gz.lookY; }
  // the glances DOWN at the gate (b02 flick, b04 longer look): the upper lids follow the eyes down and the head
  // dips after them (~0.12 s later), so it reads as looking at the gate in front, not into the lens
  const gateK = (u) => Math.max(
    S.k(u, [['s12b02+0.18', 0], ['s12b02+0.3', 1, 'out'], ['s12b02+0.66', 1], ['s12b02+0.8', 0, 'out']]),
    S.k(u, [['s12b04+0.5', 0], ['s12b04+0.66', 1, 'out'], ['s12b05-0.05', 1], ['s12b05+0.2', 0, 'out']]));
  const gk = gateK(t), gkHead = gateK(t - 0.12);
  face.lidU += 0.2 * gk; face.browUp -= 0.12 * gk;
  // looking up once in b10: the heavy lids lift with the eyes (hope), then sink again
  const upOnce = S.k(t, [['s12b10+1.45', 0], ['s12b10+1.6', 1, 'out'], ['s12b10+2.15', 1], ['s12b10+2.4', 0, 'sine']]);
  if (upOnce > 0) { face.lidU = lerp(face.lidU, 0.02, upOnce); face.browUp = lerp(face.browUp, 0.45, upOnce); face.lidTilt = lerp(face.lidTilt, 0.4, upOnce); }
  // micro-life: tiny gaze drift (not while frozen at the very start)
  const live = S.k(t, [['scene.start+0.1', 0], ['scene.start+0.5', 1]]);
  face.lookX += 0.03 * live * Math.sin(t * 1.7 + 0.4) ;
  face.lookY += 0.02 * live * Math.sin(t * 1.3 + 1.1);

  // wavering squint in b03
  if (t > T('s12b03-0.2') && t < T('s12b04+0.1')) {
    const w = S.k(t, [['s12b03-0.1', 0], ['s12b03+0.1', 1], ['s12b04-0.15', 1], ['s12b04+0.1', 0]]);
    face.lidL += 0.12 * w * Math.sin(t * 2 * Math.PI * 2.1);
    face.lidU += 0.06 * w * Math.sin(t * 2 * Math.PI * 1.6 + 1);
  }

  // tears: the hanging tear from s11 falls; spills on 'sense'; a new pair on 'forever'
  face.tearR = Math.max(S.k(t, [['scene.start-0.5', 0.07], ['scene.start+0.4', 1, 'in'], ['scene.start+0.41', 0]]),
    S.k(t, [['s12b06+1.0', 0], ['s12b06+2.7', 1], ['s12b06+2.71', 0]]),
    S.k(t, [['s12b09+1.7', 0], ['s12b09+3.4', 1], ['s12b09+3.41', 0]]));
  face.tearL = Math.max(S.k(t, [['s12b06+0.45', 0], ['s12b06+2.1', 1], ['s12b06+2.11', 0]]),
    S.k(t, [['s12b09+1.2', 0], ['s12b09+2.7', 1], ['s12b09+2.71', 0]]));
  if (t > T('s12b06+0.2') && t < T('s12b07')) face.tears = 1;

  // blinks: frozen (no blinks) at the start; then deliberate ones on the shifts
  face.noAutoBlink = true;
  const blinks = [
    ['scene.start+0.32', 0.22], ['s12b01.end+0.3', 0.2], ['s12b02.end+0.25', 0.2], ['s12b03+0.7', 0.12],
    ['s12b04+0.7', 0.25], ['s12b05+2.25', 0.3], ['s12b06+1.75', 0.24], ['s12b07.end+0.25', 0.18],
    ['s12b08+0.55', 0.14], ['s12b08.end+0.35', 0.2], ['s12b09+0.9', 0.22],
    ['s12b10+0.95', 0.25], ['s12b10+2.55', 0.32], ['s12b11+1.1', 0.35], ['s12b11+3.75', 0.75], ['s12b11.end+0.4', 0.4],
  ];
  let bl = 0;
  for (const [a, d] of blinks) bl = Math.max(bl, blinkAt(t, T(a), d));
  // a slow exhausted blink on 'It stood there': hold the lids low a moment
  face.blink = clamp(bl);

  // the quick swallow before the first line: lips pressed, a small dip
  const swallow = bump(t, T('scene.start+0.25'), 0.18);
  face.pressed = clamp((face.pressed || 0) + 0.8 * swallow);

  // ---------------- lip-sync (Fear speaks every line on screen)
  const lip = S.lip('FEAR', t);
  let amount = 1;
  if (t > T('s12b04-0.1') && t < T('s12b04.end+0.1')) amount = 0.8;             // the voice drops
  if (t > T('s12b08-0.1') && t < T('s12b08.end+0.1')) amount = 1.3;             // the most volume Fear has
  let spoken = withSpeech(face, lip, amount);
  // the shout: the jaw never closes between the words (the most volume Fear has)
  if (lip && t > T('s12b08-0.1') && t < T('s12b08.end+0.1')) spoken = { ...spoken, open: Math.max(spoken.open, 0.4 + 0.45 * (lip.open || 0)) };
  if (lip && t > T('s12b08+0.85') && t < T('s12b08+1.35')) spoken = { ...spoken, open: clamp(spoken.open + 0.35 * bump(t, T('s12b08+1.1'), 0.3)), wide: spoken.wide + 0.2 }; // mouth wide on 'standing'

  // ---------------- head
  const hitch = clamp(sobHitch(t, T('s12b09+1.9')) + sobHitch(t, T('s12b10+1.1'), 0));   // the sob after 'forever'; the hiccup
  const headDY = S.k(t, [['scene.start-1', -7], ['s12b01+0.75', -7], ['s12b01+0.95', -12, 'out'], ['s12b01.end+0.3', -11], ['s12b02', -6],
    ['s12b03', -5], ['s12b04+0.3', -2], ['s12b04.end', 2], ['s12b05+0.2', -6, 'out'], ['s12b05+2.4', -6], ['s12b05+2.95', -1],
    ['s12b06+0.5', 2], ['s12b06+1.6', -3], ['s12b07', -5], ['s12b08', -10], ['s12b08.end', -11], ['s12b09+1.0', -6], ['s12b09+2.2', 4],
    ['s12b10+1.45', 5], ['s12b10+1.7', -3, 'out'], ['s12b10+2.2', -3], ['s12b10+2.6', 6, 'sine'], ['s12b11+3.7', 7], ['s12b11+4.4', 8]])
    + 3 * swallow + 3 * stampHit - 3.5 * hitch + 6 * gkHead;
  const headTilt = S.k(t, [['scene.start-1', -0.06], ['s12b01+0.6', -0.06], ['s12b01+1.0', -0.1, 'out'], ['s12b02', -0.05],
    ['s12b03', 0.03], ['s12b04', 0.0], ['s12b04+0.4', 0.11], ['s12b05+0.2', 0.03], ['s12b05+1.6', 0.03], ['s12b05+2.2', -0.06], ['s12b05+2.8', 0],
    ['s12b06+0.6', 0.05], ['s12b07', -0.04], ['s12b08', -0.08], ['s12b09+0.5', -0.02], ['s12b09+2.3', 0.1], ['s12b10+1.5', 0.12], ['s12b10+1.7', 0.02], ['s12b10+2.6', 0.12]])
    + 0.035 * Math.sin(t * 2 * Math.PI * 1.6) * S.k(t, [['s12b06', 0], ['s12b06+0.2', 1], ['s12b06.end', 1], ['s12b06.end+0.2', 0]]);   // a wobbling "no" shake
  const headTurn = S.k(t, [['scene.start-1', 0.28], ['s12b01', 0.28], ['s12b02', 0.25], ['s12b03-0.15', 0.25], ['s12b03+0.2', 0.08, 'out'], ['s12b03.end', 0.1], // side-eye: the head turns a little away, the eyes stay on the hood
    ['s12b04+0.1', 0.25], ['s12b04+0.55', 0.25], ['s12b04+0.8', 0.12], ['s12b05+0.2', 0.25],
    ['s12b05+1.7', 0.25], ['s12b05+2.2', -0.12], ['s12b05+2.4', -0.12], ['s12b05+2.75', 0.25], ['s12b06+0.4', 0.15], ['s12b06+1.5', 0.25],
    ['s12b07+0.4', 0.35], ['s12b08', 0.3], ['s12b09+1.6', 0.2], ['s12b10', 0.05]]);
  const lean = S.k(t, [['s12b05+0.6', 0], ['s12b05+0.95', 0.06, 'out'], ['s12b05+1.25', 0.06], ['s12b05+1.6', -0.02, 'sine'], ['s12b05+2.0', 0],
    ['s12b07+0.9', 0], ['s12b07+1.0', 0.04], ['s12b07+1.3', 0.02], ['s12b08', 0.05], ['s12b08.end', 0.05], ['s12b09+0.8', 0]]);
  const crouch = clamp(S.k(t, [['s12b09+1.35', 0], ['s12b09+2.45', 1, 'inOut']]) + 0.22 * stampHit - 0.08 * hitch);
  const tremble = S.k(t, [['scene.start', 0], ['scene.start+0.6', 0.45], ['s12b05', 0.45], ['s12b05+0.3', 0.2], ['s12b05+2.3', 0.25], ['s12b05+2.9', 0.55],
    ['s12b06+0.3', 0.6], ['s12b07', 0.4], ['s12b08', 0.5], ['s12b09+0.5', 0.7], ['s12b09+2.6', 0.6], ['s12b10+0.5', 0.35], ['s12b11', 0.25]]);
  // breath: held in b05 (barely moving), then the shaky leak; small uneven breaths at the end
  const breathe = S.k(t, [['scene.start', 0.12], ['scene.start+0.6', 1], ['s12b05+0.2', 1], ['s12b05+0.45', 0.08], ['s12b05+1.8', 0.08], ['s12b05+2.1', 1.7], ['s12b06+0.3', 1.3],
    ['s12b10', 1.4], ['s12b11', 1.1]]) * (1 + 0.35 * live * Math.sin(t * 2.9));
  const breathRate = S.k(t, [['scene.start', 0.2], ['scene.start+0.6', 0.42], ['s12b05+1.9', 0.42], ['s12b05+2.1', 0.75], ['s12b06+0.5', 0.5], ['s12b10', 0.42], ['s12b11', 0.34]]);

  // ---------------- arms
  const P = (a, b, k) => lerp2(a, b, clamp(k));
  const chest = (s) => [s * 10, -134], wring = (s) => [s * 5, -106], fists = (s) => [s * 41, -54],
    shoutFists = (s) => [s * 44, -58], fold = (s) => [s * 17, -110], hug = (s) => [-s * 14, -118];
  // knot through the beats
  const armK = (s) => {
    const keys = [
      ['scene.start-1', chest(s)], ['s12b05+0.3', chest(s)], ['s12b05+0.8', wring(s)], ['s12b06+0.3', wring(s)], ['s12b06+0.7', chest(s)],
      ['s12b07+0.35', s > 0 ? [24, -112] : chest(s)], ['s12b07+0.65', fists(s)], ['s12b08-0.1', fists(s)], ['s12b08+0.2', shoutFists(s)],
      ['s12b09+0.3', shoutFists(s)], ['s12b09+1.1', fold(s)], ['s12b09+1.5', fold(s)], ['s12b09+2.4', hug(s)],
    ];
    return S.k(t, keys.map(([a, v]) => [a, { x: v[0], y: v[1] }]));
  };
  let L = armK(-1), R = armK(1);
  let armL = { target: [L.x, L.y], bend: -1, front: true, hand: 'open' };   // = s11's last frame (chest, elbows out)
  let armR = { target: [R.x, R.y], bend: 1, front: true, hand: 'open' };
  const fistOn = (t > T('s12b01+0.55') && t < T('s12b05+0.3')) || (t > T('s12b07+0.4') && t < T('s12b09+0.6'));
  if (fistOn) { armL.hand = 'fist'; armR.hand = 'fist'; }
  if (t > T('s12b05+0.5') && t < T('s12b06+0.5')) { armL.hand = 'fist'; armR.hand = 'fist'; }
  // fists hanging at the sides: the elbows bend in like the rest pose (the arms are nearly straight when it flips)
  if (t > T('s12b07+0.5') && t < T('s12b09+0.3')) { armL.bend = 1; armR.bend = -1; }
  // the stamp: the fists jab down with the foot
  if (stampHit > 0) { armL.target = [armL.target[0], armL.target[1] + 7 * stampHit]; armR.target = [armR.target[0], armR.target[1] + 7 * stampHit]; }

  // b06/b07: "one step to the open gate; a small hand grips its edge": the right hand finds the edge of the open doorway
  // (the lock jamb, just above the dangling padlock), holds it through the line, lets go as Fear steps out (b07)
  let grips;
  const door = DOOR_OPEN;
  const reachK = S.k(t, [['s12b06+0.75', 0], ['s12b06+1.45', 1, 'inOut'], ['s12b07+0.22', 1], ['s12b07+0.5', 0, 'sine']]);
  if (reachK > 0) {
    const h = JAMB_GRIP;
    const loc = [(h[0] - pos[0]) / scale, (h[1] - pos[1]) / scale];
    let tgt, bend;
    if (t < T('s12b07')) {
      // the reach: the hand drops from the chin to the hip, where the arm is nearly straight and the elbow can change
      // sides without a pop, then swings up onto the jamb, elbow down. (The straight chin → jamb path ran past the
      // shoulder with the elbow flipped: the upper arm stood straight up across the mouth for ~5 frames mid-line.)
      tgt = reachK < 0.5 ? quad(armR.target, REACH_C0, REACH_OUT, reachK / 0.5) : quad(REACH_OUT, REACH_C1, loc, (reachK - 0.5) / 0.5);
      bend = lerp(armR.bend, -1, smoothstep(0.4, 0.6, reachK));
    } else {
      // letting go (b07, the wide): straight down to the arms' pose, elbow down (as the b07 fists pose that follows)
      tgt = P(armR.target, loc, reachK); bend = -1;
    }
    armR = { target: tgt, bend, front: true, hand: reachK > 0.85 ? 'grip' : 'open' };
    if (reachK > 0.85 && t < T('s12b07+0.3')) grips = [[(h[0] - CAGE_B[0]) / FS, (h[1] - CAGE_B[1]) / FS]];
  }
  // b10: wipes its nose on the scarf (right hand), then folds back into the hug
  const wipe = S.k(t, [['s12b10+0.05', 0], ['s12b10+0.35', 1, 'out'], ['s12b10+0.95', 1], ['s12b10+1.3', 0, 'sine']]);
  if (wipe > 0) {
    const sweep = Math.sin((t - T('s12b10+0.35')) * 2 * Math.PI * 1.7) * clamp((t - T('s12b10+0.35')) / 0.1);
    armR = { target: P(armR.target, [6 + 12 * sweep, -158], wipe), bend: -1, front: true, hand: 'fist' };
  }

  // the chin: trembles under 'certain', starts to go in the silence, crumples in the plea
  const chin = S.k(t, [['s12b02-0.3', 0], ['s12b02', 0.5], ['s12b02.end+0.2', 0.5], ['s12b03-0.1', 0],
    ['s12b05+2.4', 0], ['s12b05+2.95', 0.45], ['s12b06+0.3', 0.6], ['s12b07-0.1', 0.6], ['s12b07+0.2', 0.15], ['s12b08-0.2', 0],
    ['s12b09+0.1', 0], ['s12b09+0.5', 1, 'out'], ['s12b10+0.5', 0.8], ['s12b11', 0.4]]);
  return { pos, scale, walk, chin, face: spoken, headDY, headTilt, headTurn, lean, crouch, tremble, breathe, breathRate, armL, armR, grips, door };
}

// ---------------------------------------------------------------- baked backgrounds (perf)
// In the closes everything behind Fear is static (the set, the frozen Void, the cage with the gate standing still),
// but drawn at 3–4× zoom it cost ~25 ms a frame. Each close bakes it once into a world-space sprite at the shot's
// widest framing, sampled at its tightest zoom (crisp through the push). Built from a fixed reference time, so a
// frame renders identically whatever was rendered before it.
const BG_CACHE = new Map();
function drawBaked(g, spec, build) {
  let e = BG_CACHE.get(spec.key);
  if (!e) {
    const rw = (W / spec.zMin) * spec.m, rh = (H / spec.zMin) * spec.m;
    const rx = spec.x - rw / 2, ry = spec.y - rh / 2;
    const c = createCanvas(Math.ceil(rw * spec.zMax), Math.ceil(rh * spec.zMax));
    const cg = c.getContext('2d');
    cg.scale(c.width / rw, c.height / rh); cg.translate(-rx, -ry);
    build(cg);
    e = { c, rx, ry, rw, rh };
    BG_CACHE.set(spec.key, e);
  }
  g.drawImage(e.c, e.rx, e.ry, e.rw, e.rh);
}

// ---------------------------------------------------------------- render
export function render(g, t, S) {
  const F = fearState(t, S);
  const { cam, cage, bake } = shot(t, S, F);
  const cst = { t, door: F.door, locked: 0, shake: 0 };
  const vpose = { t, ...STARE_B, idle: 0, shadowSpread: 1, handL: { ...VOID_ARM_B, show: 0, defer: 'hand' } };
  const st = { t, lightsDim: 0.35, mist: 0.6 };
  const inside = F.pos[1] <= DOORWAY_Y;
  const fearPose = { t, facing: 1, headTurn: F.headTurn, headTilt: F.headTilt, headDY: F.headDY, lean: F.lean, crouch: F.crouch,
    tremble: F.tremble, breathe: F.breathe, breathRate: F.breathRate, face: F.face, armL: F.armL, armR: F.armR,
    walk: F.walk ? { phase: F.walk } : undefined };

  g.save();
  applyCamera(g, cam);
  if (bake) {
    drawBaked(g, bake, (cg) => {
      const tb = S.T(bake.at), cb = { t: tb, door: fearState(tb, S).door, locked: 0, shake: 0 };
      drawHQ(cg, 'backOfMind', { ...st, t: tb });
      drawVoid(cg, ...VOID_B, { ...vpose, t: tb });
      drawCage(cg, ...CAGE_B, { ...cb, layer: 'back' });
      if (bake.front) drawCage(cg, ...CAGE_B, { ...cb, layer: 'front' });
    });
  } else {
    drawHQ(g, 'backOfMind', st);
    drawVoid(g, ...VOID_B, vpose);
    drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  }
  if (inside) drawFear(g, F.pos[0], F.pos[1], F.scale, fearPose);
  if (inside) chinCrumple(g, F, F.chin, t);
  if (cage === 'full' && !(bake && bake.front)) drawCage(g, ...CAGE_B, { ...cst, layer: 'front', grips: F.grips });
  else if (cage === 'cheatLock') lockStrip(g, cst, F, t);
  if (!inside) { drawFear(g, F.pos[0], F.pos[1], F.scale, fearPose); chinCrumple(g, F, F.chin, t); }
  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  // b08–b09 close from above: the darkness of the hood edges the top of the frame (and swallows the sign's end)
  if (t >= S.T('s12b08-0.3') && t < S.T('s12b10')) {
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
    const gr = g.createLinearGradient(0, 0, 0, 330);
    gr.addColorStop(0, 'rgba(5,3,14,0.97)'); gr.addColorStop(0.3, 'rgba(5,3,14,0.82)'); gr.addColorStop(1, 'rgba(5,3,14,0)');
    g.fillStyle = gr; g.fillRect(0, 0, W, 330);
    g.restore();
  }
  finish(g, 0.6, 0, 0.5);
}
