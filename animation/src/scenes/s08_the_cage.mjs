// s08 · the_cage · backOfMind (wide → padlock insert → close) → front (two planes)
// "So I put my fear into a cage." / FEAR: "Please don't leave me with it." / silent walk-away.
import { clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette, TAU } from '../engine.mjs';
import { EXPR, withSpeech } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, selfLocal, WALK_ADVANCE } from '../chars/self.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground, hqScaleAt } from '../sets/hq.mjs';
import { drawCage, cagePoint } from '../sets/props.mjs';

export const id = 's08';

// ---- staging constants (data/staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const VOID_B = [700, 1600, 0.9];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const CAGE_F = [302, 846, 0.3];
const CAGE_B = [430, 1630, 0.952];
const CEO_B_DOOR = [300, 1730, 1.12];                // staging value (kept for reference)
const CEO_KNEEL = [255, 1730, 1.12];                 // s08 only: 45 px left of CEO_B_DOOR so the kneeling CEO's head
                                                     //   clears Fear's face in the wide; the hand still reaches the lock
const CEO_B_BARS = [96, 1735, 1.12];                 // staging 140 assumed the close at x 430; this close sits at x 414,
                                                     //   where the kneeling CEO's hair and raised knee peeked in at frame-left

// ---- light (§4.2)
const SET_B = { lightsDim: 0.3, mist: 0.6 };
const SET_F = { lightsDim: 0.4, mist: 0.45, voidShadow: 0.6, consoleGlow: 0.7 };
const COLD = 0.55, VIG = 0.5;

export const sfx = [
  // the CEO's steps guiding Fear in (contacts every ~0.48 s), Fear's tiny patter under them
  { at: 'scene.start-0.02', name: 'footsteps', gain: -14, rate: 1.17, until: 's08b01+1.3', fade: 0.15 },
  { at: 'scene.start+0.1', name: 'footsteps', gain: -22, rate: 1.9, until: 's08b01+1.6', fade: 0.15, pan: 0.15 },
  { at: 's08b01+1.15', name: 'cloth_rustle', gain: -16 },                 // goes down on one knee
  { at: 's08b01+1.65', name: 'cage_creak', gain: -21, until: 's08b01+2.4', fade: 0.05 },   // the gate swinging round
  { at: 's08b01+2.37', name: 'cage_close', gain: -8 },                    // clang at +2.4 (sync 0.03)
  { at: 's08b02-0.88', name: 'key_turn', gain: -10 },                     // bolt (0.68) lands on the lock at b02-0.2
  { at: 's08b02-0.22', name: 'lock_click', gain: -10 },
  { at: 's08b02+0.15', name: 'cloth_rustle', gain: -20, pan: -0.5 },      // the CEO rising beside the bars
  { at: 's08b03+0.0', name: 'sob', gain: -16, pan: 0.15 },
  { at: 's08b03+0.12', name: 'cloth_rustle', gain: -18, pan: -0.3 },      // turns away from the cage
  { at: 's08b03+0.52', name: 'footsteps', gain: -16, rate: 1.2, until: 's08b03+1.3', fade: 0.12, pan: -0.3 },   // two steps (+0.58, +1.06)
  // weak rattles at +0.55 / +1.5 / +2.25 / +3.0: the creak's swell (peak 0.7 s into the file) lands inside each shake
  { at: 's08b03+0.3', name: 'cage_creak', gain: -17, pan: 0.15, until: 's08b03+1.3' },
  { at: 's08b03+1.3', name: 'breath_shaky', gain: -18, pan: -0.3 },        // the CEO's in-breath
  { at: 's08b03+1.25', name: 'cage_creak', gain: -18, pan: 0.15, until: 's08b03+2.15' },
  { at: 's08b03+1.85', name: 'sob', gain: -17, pan: 0.15 },
  { at: 's08b03+2.0', name: 'cage_creak', gain: -19, pan: 0.15, until: 's08b03+2.9' },
  { at: 's08b03+2.75', name: 'cage_creak', gain: -21, pan: 0.15, until: 's08b03+3.55' },
  { at: 's08b03+2.65', name: 'footsteps', gain: -15, rate: 1.15, pan: -0.35 },
  { at: 'scene.end-1.5', name: 'door_whoosh', gain: -22, pan: -0.7, until: 'scene.end+0.05', fade: 0.1 },   // the door begins to open
];

// ---------------------------------------------------------------- local helpers
function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function cam(g, c, t, amp = 2.5) {
  const d = amp ? drift(t, amp, 8) : { dx: 0, dy: 0, dr: 0 };
  applyCamera(g, { x: c.x + d.dx / c.zoom, y: c.y + d.dy / c.zoom, zoom: c.zoom, rot: d.dr * 0.5 });
}
const sstep = (a, b, x) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };
/** Sobbing: returns 0..1 hitch pulses (3 quick catches per sob), sob every `period` s. */
function sobHitch(t, period = 1.7, phase = 0) {
  const u = ((t + phase) % period + period) % period;
  let v = 0;
  for (const c of [0.0, 0.17, 0.32]) { const d = u - c; if (d >= 0 && d < 0.16) v = Math.max(v, Math.sin((d / 0.16) * Math.PI)); }
  return v;
}
/** a small gold key sticking out of a keyhole toward the camera (cartoon 3/4): collar at (x,y), shank along
 *  `ang`, bow at the end; `spin` 0..1 = the quarter turn (the bow narrows as it rotates about the shank). */
function drawKey(g, x, y, ang, s = 1, alpha = 1, spin = 0) {
  if (alpha <= 0) return;
  g.save();
  g.globalAlpha *= alpha;
  g.translate(x, y);
  g.rotate(ang);
  g.scale(s, s);
  g.lineJoin = 'round';
  const w = Math.max(0.18, Math.abs(Math.cos(spin * Math.PI / 2)));
  g.strokeStyle = '#4a300c'; g.lineWidth = 0.9;
  // shank
  g.fillStyle = '#d2a640';
  g.beginPath(); g.roundRect(-0.5, -1.5, 6.5, 3.0, 1.2); g.fill(); g.stroke();
  // bow (flat loop, rotating about the shank axis)
  const gr = g.createLinearGradient(5, -4, 13, 4);
  gr.addColorStop(0, '#fff0b0'); gr.addColorStop(0.45, '#e8c25a'); gr.addColorStop(1, '#a87b22');
  g.fillStyle = gr;
  g.beginPath(); g.ellipse(10, 0, 4.4, 4.2 * w, 0, 0, TAU); g.fill(); g.stroke();
  if (w > 0.35) { g.fillStyle = '#2a1d10'; g.beginPath(); g.ellipse(10.6, 0, 1.5, 1.4 * w, 0, 0, TAU); g.fill(); }
  // collar where it enters the lock
  g.fillStyle = '#b8892c';
  g.beginPath(); g.ellipse(0, 0, 1.4, 2.4, 0, 0, TAU); g.fill(); g.stroke();
  // glint
  g.fillStyle = `rgba(255,250,225,${0.9 * w})`;
  g.beginPath(); g.ellipse(8.6, -2.0 * w, 1.4, 0.6, 0, 0, TAU); g.fill();
  g.restore();
}
/** world keyhole of the padlock on CAGE_B (follows the hanging/closed padlock exactly as props.mjs draws it) */
function keyholeB(cst) {
  const [hx, hy] = cagePoint('lockHang', ...CAGE_B, cst);
  const open = 1 - clamp(cst.locked);
  const c1 = 1.70158, c3 = c1 + 1, ob = open <= 0 ? 0 : 1 + c3 * Math.pow(open - 1, 3) + c1 * Math.pow(open - 1, 2);
  const ang = -0.5 * ob + Math.sin(cst.t * 1.3) * 0.015;
  const d = 31 + 9 * open, s = CAGE_B[2];
  return [hx + s * (-Math.sin(ang) * d), hy + s * (-4 + Math.cos(ang) * d)];
}

// ---------------------------------------------------------------- timing helpers
function times(S) {
  return {
    start: S.start,
    let: S.T('s08b01+1.2'), door: S.T('s08b01+1.4'), inside: S.T('s08b01+1.7'), grip: S.T('s08b01+2.0'),
    cutInsert: S.T('s08b01+2.2'), shut: S.T('s08b01+2.4'),
    b02: S.T('s08b02'), b02e: S.T('s08b02.end'), b03: S.T('s08b03'), end: S.end,
  };
}

// The cage state (shared by all shots)
function cageState(t, S) {
  // it swings out from behind the kneeling CEO (1 → 0.62, out of sight), the CEO's hand pulls it shut (→ 0)
  const door = S.k(t, [['s08b01+1.8', 1], ['s08b01+2.06', 0.62, 'in'], ['s08b01+2.4', 0, 'inOut']]);
  const locked = S.k(t, [['s08b02-0.2', 0], ['s08b02-0.14', 1, 'linear']]);
  return { t, door, locked };
}

// CEO walk-in position (backOfMind)
function ceoWalk(t, S) {
  const t0 = S.start, t1 = S.T('s08b01+1.2');
  const u = clamp((t - t0) / (t1 - t0));
  const g = 1.3 * u - 0.3 * u * u;               // a steady walk, slowing as they arrive
  const x = lerp(-10, CEO_KNEEL[0], g), y = lerp(1735, CEO_KNEEL[1], g);
  return { x, y, u };
}
// Fear position (backOfMind): pushed along ahead of the CEO, then steps in alone
function fearWalk(t, S) {
  const tl = S.T('s08b01+1.2'), td = S.T('s08b01+1.4'), ti = S.T('s08b01+1.7');
  if (t <= tl) {
    const c = ceoWalk(t, S);
    const k = clamp((t - S.start) / (tl - S.start));
    return { x: c.x + 140, y: lerp(1712, 1655, ease.sine(k)), moving: 1 };
  }
  if (t <= td) {
    const k = (t - tl) / (td - tl);
    return { x: lerp(CEO_KNEEL[0] + 140, 430, ease.out(k)), y: lerp(1655, 1642, k), moving: 1 - k * 0.3 };
  }
  const k = ease.sine(clamp((t - td) / (ti - td)));
  return { x: 430, y: lerp(1642, 1630, k), moving: t < ti ? 0.6 * (1 - k) : 0 };
}
const fearScaleB = (y) => (y >= 1642 ? hqScaleAt('backOfMind', y) : lerp(0.952, hqScaleAt('backOfMind', 1642), clamp((y - 1630) / 12)));

// ---------------------------------------------------------------- render
export function render(g, t, S) {
  const T = times(S);
  if (t < T.cutInsert) shotWide(g, t, S, T);
  else if (t < T.b02) shotInsert(g, t, S, T);
  else if (t < T.b03) shotClose(g, t, S, T);
  else shotFront(g, t, S, T);
}

// ---- Fear in the back-of-mind shots (wide / insert / close)
function fearPoseB(t, S, T, cst, fx, fy, fs) {
  const loc = (p) => [(p[0] - fx) / fs, (p[1] - fy) / fs];
  const gl = loc(cagePoint('gripL', ...CAGE_B, cst)), gr = loc(cagePoint('gripR', ...CAGE_B, cst));
  // face: dread while walking under the Void (eyes up-right on the hood, no blinking) → turns to the CEO,
  // crying → (insert) eyes drop to the key in the CEO's fingers → flinch at the click → back up to the CEO
  const dread = { ...EXPR.scared, lookX: 0.42, lookY: -1, open: 0.16, lidU: -0.3, pupil: 0.62, tears: 0.45 };
  const atCEO = { ...EXPR.crying, open: 0.12, stream: 0.0, tears: 0.75, lookX: -0.55, lookY: -0.45, lidU: 0.12 };
  const watchLock = { ...atCEO, lookX: 0.55, lookY: 0.75, browUp: 0.55, smile: -0.7, open: 0.2, lidU: 0.05 };
  const afterClick = { ...atCEO, lookX: -0.4, lookY: -0.2, browUp: 0.5, lidU: 0.2, smile: -0.85 };
  let face = S.k(t, [
    ['scene.start', dread], ['s08b01+1.75', dread], ['s08b01+2.05', atCEO], ['s08b01+2.35', atCEO],
    ['s08b01+2.7', watchLock], ['s08b02-0.18', watchLock], ['s08b02', afterClick],
  ]);
  // tremble: frozen while staring up (fear 0.25), shaking at the bars (0.6)
  let tremble = S.k(t, [['s08b01+1.7', 0.25], ['s08b01+2.1', 0.6]]);
  const flinch = blinkAt(t, S.T('s08b02-0.17'), 0.3);
  face = { ...face, blink: Math.max(flinch, blinkAt(t, S.T('s08b01+2.1'), 0.22)) };
  if (t < T.inside + 0.2) face.noAutoBlink = true;   // the frozen stare up at the Void
  const fw = fearWalk(t, S);
  const walking = fw.moving > 0.01;
  // head craned back toward the hood, settling level as it turns to the bars
  const crane = S.k(t, [['s08b01+1.6', 1], ['s08b01+2.0', 0]]);
  const gripK = sstep(T.inside, T.grip, t);
  const armL = gripK > 0 ? { target: [lerp(-34, gl[0], gripK), lerp(-82, gl[1], gripK)], bend: 1, front: gripK > 0.5, hand: gripK > 0.6 ? 'grip' : 'fist' } : { target: [-34, -82], bend: 1, hand: 'fist' };
  const armR = gripK > 0 ? { target: [lerp(34, gr[0], gripK), lerp(-82, gr[1], gripK)], bend: -1, front: gripK > 0.5, hand: gripK > 0.6 ? 'grip' : 'fist' } : { target: [34, -82], bend: -1, hand: 'fist' };
  return {
    t, facing: 1, tremble, crouch: 0,
    headTurn: 0.3 * crane, headDY: -9 * crane, headTilt: 0.11 * crane,
    walk: walking ? { phase: ((fw.x - 430) / (58 * fs)) * TAU + Math.PI / 2 + clamp((1642 - fw.y) / 12) * Math.PI } : null,
    breathe: 1.3, breathRate: 0.9,
    face, armL, armR, grips: gripK > 0.6,
  };
}

// ---------------------------------------------------------------- shot 1: wide, back of the mind
function shotWide(g, t, S, T) {
  g.save();
  cam(g, { x: 440, y: 1020, zoom: 0.85 }, t, 2.5);
  const st = { t, ...SET_B };
  drawHQ(g, 'backOfMind', st);
  drawVoid(g, ...VOID_B, { t, ...STARE_B, idle: 0, shadowSpread: 0.7 });
  const cst = cageState(t, S);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });

  const fw = fearWalk(t, S);
  const fs = fearScaleB(fw.y);
  const fp = fearPoseB(t, S, T, cst, fw.x, fw.y, fs);
  const inside = fw.y < 1642;
  if (inside) drawFear(g, fw.x, fw.y, fs, fp);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front', grips: fp.grips ? ['gripL', 'gripR'] : undefined });
  if (!inside) drawFear(g, fw.x, fw.y, fs, fp);

  // ---- the CEO: hand on Fear's shoulder while walking, lets go, kneels, swings the gate shut
  // The CEO is in 3/4 toward the cage, so the right arm is the FAR arm: it is drawn behind the torso (not `front`) and
  // its hand comes out past the body's right edge — onto Fear's shoulder, then resting on the forward knee, then onto
  // the gate's hasp. (Drawn `front`, the far arm read as folded across the chest.) The open gate lies behind the
  // kneeling body, so its first swing (door 1 → 0.62) happens out of sight; the hand meets the hasp as it comes past
  // the body and pulls it shut (0.62 → 0, into the insert).
  const c = ceoWalk(t, S);
  const cs = CEO_KNEEL[2];
  const kneel = S.k(t, [['s08b01+1.2', 0], ['s08b01+1.8', 1, 'inOut']]);
  const walking = kneel < 0.01;
  const phase = ((c.x - CEO_KNEEL[0]) / (WALK_ADVANCE * cs)) * TAU + Math.PI / 2;   // ends on a passing pose
  const L = (wx, wy) => selfLocal(c.x, c.y, cs, 1, wx, wy);
  const crouchW = 0.6 * (1 - sstep(0, 0.6, kneel)), leanW = 0.22 * (1 - sstep(0, 0.7, kneel));
  const bodyPose = { t, outfit: 'ceo', facing: 1, kneel, walk: walking ? { phase } : null, crouch: crouchW, lean: leanW };
  // Fear's near shoulder (screen-left): one hand on it, the CEO stooping to reach (gentle, not letting go)
  const shN = [fw.x - 34 * fs, fw.y - 134 * fs];
  const hold = 1 - sstep(T.let - 0.05, T.let + 0.3, t);          // lets go as Fear steps in
  const hasp = cagePoint('doorHandle', ...CAGE_B, cst);
  const kE = sstep(0, 1, kneel);
  const kneeR = [lerp(75, 66, kE), lerp(-205, -168, kE)];          // the hand comes to rest on the forward knee
  const catchK = sstep(S.T('s08b01+1.84'), S.T('s08b01+2.06'), t);  // ...and rises to meet the swinging hasp
  let armR;
  if (catchK > 0) {
    const tg = L(hasp[0] - 16, hasp[1] + 6);
    armR = { target: [lerp(kneeR[0], tg[0], catchK), lerp(kneeR[1], tg[1], catchK)], bend: -1, hand: catchK > 0.85 ? 'grip' : 'open', thumb: -1 };
  } else if (hold > 0.999) {
    armR = { preset: 'onShoulder', target: L(...shN), hand: 'drape', front: false };
  } else {
    const tR = L(shN[0] - 6, shN[1] - 18 * (1 - hold));
    armR = { target: [lerp(kneeR[0], tR[0], hold), lerp(kneeR[1], tR[1], hold)], bend: -1, hand: 'open' };
  }
  const armL = 'rest';
  // face set, eyes on Fear's back / the gate — never up at the Void, never quite meeting Fear's eyes.
  // For the gate: a glance down-left to find the hasp, then the eyes follow the gate across to the lock.
  const ceoFace = S.k(t, [
    ['scene.start', { ...SELF_EXPR.resolve, lookX: 0.35, lookY: 0.55, lidU: 0.22 }],
    ['s08b01+1.3', { ...SELF_EXPR.resolve, lookX: 0.35, lookY: 0.55, lidU: 0.22 }],
    ['s08b01+1.55', { ...SELF_EXPR.resolve, lookX: -0.45, lookY: 0.65, lidU: 0.3, pressed: 0.7, browIn: 0.15 }],
    ['s08b01+1.8', { ...SELF_EXPR.resolve, lookX: -0.45, lookY: 0.65, lidU: 0.3, pressed: 0.8, browIn: 0.15 }],
    ['s08b01+2.15', { ...SELF_EXPR.resolve, lookX: 0.75, lookY: 0.45, lidU: 0.28, pressed: 0.8, browIn: 0.15 }],
  ]);
  ceoFace.blink = blinkAt(t, S.T('s08b01+1.5'), 0.2);             // the glance down carries a blink
  drawSelf(g, c.x, c.y, cs, {
    ...bodyPose, headTurn: 0.22 * kE - 0.12 * Math.max(0, -ceoFace.lookX), headTilt: 0.08, headDX: -12 * kE, face: ceoFace, armR, armL,
  });

  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  grade(g, COLD, 0);
  vignette(g, VIG);
}

// ---------------------------------------------------------------- shot 2: insert on the padlock
function shotInsert(g, t, S, T) {
  g.save();
  cam(g, { x: 505, y: 1540, zoom: 3.2 }, t, 1.2);
  const st = { t, ...SET_B };
  drawHQ(g, 'backOfMind', st);
  drawVoid(g, ...VOID_B, { t, ...STARE_B, idle: 0, shadowSpread: 0.7 });
  const cst = cageState(t, S);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  const [fx, fy] = cagePoint('occupantFront', ...CAGE_B, cst);
  const fs = CAGE_B[2];
  const fp = fearPoseB(t, S, T, cst, fx, fy, fs);
  fp.walk = null;
  drawFear(g, fx, fy, fs, fp);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front', grips: ['gripL', 'gripR'] });

  // the CEO's hand: hasp (door closing) → down to the padlock with the key → hesitate → turn → leave
  const [cx, cy, cs] = CEO_KNEEL;
  const L = (wx, wy) => selfLocal(cx, cy, cs, 1, wx, wy);
  const kh = keyholeB(cst);
  const KS = 1.6, KANG = Math.PI + 0.62;                                // shank sticks out up-left, toward the hand
  // hesitation: the fingers tremble on the key, a false start of the turn, a stop… then they commit
  const spin = S.k(t, [['s08b02-1.05', 0], ['s08b02-0.92', 0.14], ['s08b02-0.72', 0.03], ['s08b02-0.6', 0.03], ['s08b02-0.22', 1, 'inOut']]);
  const hes = sstep(S.T('s08b01+2.65'), S.T('s08b01+2.85'), t) * (1 - sstep(S.T('s08b02-0.7'), S.T('s08b02-0.55'), t));
  const toLock = sstep(T.shut + 0.02, S.T('s08b01+2.62'), t);
  const leave = sstep(S.T('s08b02-0.15'), S.T('s08b02'), t);
  const out = 0;
  const bow = [kh[0] + Math.cos(KANG) * (10 + out) * KS, kh[1] + Math.sin(KANG) * (10 + out) * KS];
  const handAng = 0.42 + 0.25 * spin;                                    // the wrist rolls with the turn
  const pinchOff = 33;                                                   // wrist → thumb/index pinch (world px)
  const pinch = [bow[0] - Math.cos(handAng) * pinchOff, bow[1] - Math.sin(handAng) * pinchOff + 6];
  const hasp = cagePoint('doorHandle', ...CAGE_B, cst);
  const onHasp = [hasp[0] - Math.cos(0.42) * 30, hasp[1] - Math.sin(0.42) * 30 + 2];
  let wr = [lerp(onHasp[0], pinch[0], toLock), lerp(onHasp[1], pinch[1], toLock)];
  const slide = [-150 * leave, 26 * leave];                              // slides left along the middle rail
  wr = [wr[0] + slide[0], wr[1] + slide[1]];
  const armR = { target: L(...wr), bend: -1, front: true, hand: 'grip', handAngle: handAng, thumb: -1, shake: 0.4 * hes };
  drawSelf(g, cx, cy, cs, { t, outfit: 'ceo', facing: 1, kneel: 1, face: { ...SELF_EXPR.resolve, lookX: 0.8, lookY: 0.5 }, armR, armL: 'rest' });
  // the key: produced in the fingers as the hand drops, turned, then drawn out with the hand
  const keyIn = sstep(T.shut + 0.08, S.T('s08b01+2.55'), t);
  drawKey(g, kh[0] + Math.cos(KANG) * out * KS + slide[0], kh[1] + Math.sin(KANG) * out * KS + slide[1], KANG, KS, keyIn * (1 - sstep(0.3, 0.7, leave)), spin);

  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  grade(g, COLD, 0);
  vignette(g, VIG);
}

// ---------------------------------------------------------------- shot 3: close on Fear behind the bars
function shotClose(g, t, S, T) {
  g.save();
  // close (staging {430,1430,2.2}), pushed in so Fear's face fills ~half the frame width (at 2.2 the whole cage and
  // plinth were in frame: a medium) and nudged left so the leftmost bar + the CEO's hand sit at the frame edge;
  // the TIME-OUT sign stays in at the top. A slow push through the line.
  cam(g, S.k(t, [['s08b02', { x: 404, y: 1440, zoom: 2.35 }], ['s08b03', { x: 405, y: 1436, zoom: 2.52 }, 'linear']]), t, 2);
  const st = { t, ...SET_B };
  drawHQ(g, 'backOfMind', st);
  drawVoid(g, ...VOID_B, { t, ...STARE_B, idle: 0, shadowSpread: 0.7 });
  const cst = cageState(t, S);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  const [fx, fy] = cagePoint('occupantFront', ...CAGE_B, cst);
  const fs = CAGE_B[2];
  const loc = (p) => [(p[0] - fx) / fs, (p[1] - fy) / fs];
  const gl = loc(cagePoint('gripL', ...CAGE_B, cst)), gr = loc(cagePoint('gripR', ...CAGE_B, cst));
  // eyes: on the CEO (left, rising with them) → up-right to the Void on 'with it' → back, begging
  const toCEO = S.k(t, [['s08b02', -0.25], ['s08b02+0.9', -0.6]]);
  const lookX = S.k(t, [['s08b02+1.42', -0.62], ['s08b02+1.62', 0.42], ['s08b02+1.98', 0.42], ['s08b02+2.25', -0.62]]);
  const lookY = S.k(t, [['s08b02+1.42', toCEO], ['s08b02+1.62', -1], ['s08b02+1.98', -1], ['s08b02+2.25', -0.6]]);
  const beg = S.k(t, [['s08b02+1.9', 0], ['s08b02+2.3', 1]]);
  const tearL = S.k(t, [['s08b02+0.15', 0], ['s08b02+1.8', 1, 'linear']]);
  const tearR = S.k(t, [['s08b02+0.95', 0], ['s08b02+2.6', 1, 'linear']]);
  const base = { ...EXPR.crying, open: 0.06, wide: 0.15, stream: S.k(t, [['s08b02', 0.05], ['s08b02.end', 0.45]]), tears: 1,
    lookX, lookY: t < S.T('s08b02+1.42') ? toCEO : lookY, browUp: 0.3 + 0.35 * beg, lidU: 0.2 - 0.15 * beg, tearL, tearR: t > S.T('s08b02+0.95') ? tearR : 0 };
  const face = withSpeech(base, S.lip('FEAR', t), 0.85);
  // pressed to the bars: a small lean in, pulls on 'leave'
  const pull = S.k(t, [['s08b02+1.0', 0], ['s08b02+1.2', 1], ['s08b02+1.6', 0.3]]);
  const hitch = sobHitch(t, 1.9, 0.4) * (t > S.T('s08b02.end') ? 1 : 0.35);
  // on 'with it' the head follows the eyes a touch up toward the hood (so the look reads at phone size), then back
  const roll = S.k(t, [['s08b02+1.45', 0], ['s08b02+1.7', 1], ['s08b02+1.98', 1], ['s08b02+2.3', 0]]);
  drawFear(g, fx, fy, fs, {
    t, facing: 1, tremble: 0.6, lean: -0.02 * pull, headDY: -2 * hitch + 1.5 - 4 * roll, headTurn: 0.12 * roll, headTilt: 0.08 * roll,
    breathe: 1.4, breathRate: 0.85,
    face,
    armL: { target: [gl[0], gl[1] + 3 * pull], bend: 1, front: true, hand: 'grip' },
    armR: { target: [gr[0], gr[1] + 3 * pull], bend: -1, front: true, hand: 'grip' },
  });
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front', grips: ['gripL', 'gripR'], shake: 0.25 * pull });

  // the CEO's hand on the leftmost bar (body off-frame left): slides up as they stand, tightens on 'leave', lets go
  const [cx, cy, cs] = CEO_B_BARS;
  const kneel = S.k(t, [['s08b02+0.1', 1], ['s08b02+0.9', 0, 'inOut']]);
  const barY = lerp(1440, 1490, kneel);
  const tight = S.k(t, [['s08b02+1.05', 0], ['s08b02+1.2', 1], ['s08b02.end-0.1', 1], ['s08b02.end+0.05', 0]]);
  const off = sstep(S.T('s08b02.end'), S.T('s08b02.end+0.35'), t);
  const target = selfLocal(cx, cy, cs, 1, 262 - 4 * tight - 120 * off, barY + 30 * off);
  drawSelf(g, cx, cy, cs, {
    t, outfit: 'ceo', facing: 1, kneel, face: { ...SELF_EXPR.holdingBackTears, lookX: 0.7, lookY: 0.6 },
    armR: { target, bend: -1, front: true, hand: off > 0.2 ? 'open' : tight > 0.5 ? 'fist' : 'grip', handAngle: -0.05 - 0.12 * tight, thumb: -1, shake: 0.3 * tight },
    armL: 'rest',
  });
  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  grade(g, COLD, 0);
  vignette(g, VIG);
}

// ---------------------------------------------------------------- shot 4: front view, two planes
function shotFront(g, t, S, T) {
  g.save();
  // two planes: start on the CEO at the cage (staging {330,740,1.6} reframed tighter and lower so the CEO
  // comes INTO the foreground at the stop, face lower-left third, Fear's face behind at upper right)
  cam(g, S.k(t, [['s08b03', { x: 266, y: 796, zoom: 1.9 }], ['s08b03+1.2', { x: 268, y: 800, zoom: 1.9 }, 'sine'],
    ['s08b03+2.6', { x: 268, y: 806, zoom: 1.98 }, 'sine'], ['scene.end', { x: 268, y: 814, zoom: 1.96 }, 'sine']]), t, 2.5);
  // the EXIT door starts to open behind the CEO as the shot ends: the emotions are coming back (s09 opens on it at 0.6)
  const st = { t, ...SET_F, doorOpen: S.k(t, [['scene.end-1.1', 0], ['scene.end', 0.6, 'inOut']]) };
  drawHQ(g, 'front', st);
  drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0, shadow: false });
  // rattles: Fear pulls the bars weakly
  const rattles = [0.55, 1.5, 2.25, 3.0].map((d) => S.T('s08b03') + d);
  let shake = 0, pullK = 0;
  for (const r of rattles) {
    const d = t - r;
    if (d > -0.15 && d < 0.6) { shake = Math.max(shake, 0.6 * (d < 0 ? 1 + d / 0.15 : 1 - d / 0.6)); }
    if (d > -0.2 && d < 0.45) pullK = Math.max(pullK, Math.sin(clamp((d + 0.2) / 0.65) * Math.PI));
  }
  const cst = { t, door: 0, locked: 1, shake };
  drawCage(g, ...CAGE_F, { ...cst, layer: 'back' });
  const [fx, fy] = cagePoint('occupantFront', ...CAGE_F, cst);
  const fs = CAGE_F[2];
  const loc = (p) => [(p[0] - fx) / fs, (p[1] - fy) / fs];
  const gl = loc(cagePoint('gripL', ...CAGE_F, cst)), gr = loc(cagePoint('gripR', ...CAGE_F, cst));
  const hitch = sobHitch(t, 1.6, 0.2);
  drawFear(g, fx, fy, fs, {
    t, facing: 1, tremble: 0.7, lean: -0.05 * pullK, headDY: -3 * hitch, breathe: 1.9, breathRate: 0.8,
    face: { ...EXPR.crying, open: 0.3 + 0.2 * hitch, lidU: 0.45, stream: 0.75, tearL: ((t - S.T('s08b03')) / 1.6) % 1, lookY: -0.2, lookX: -0.3 },
    armL: { target: [gl[0] + 3 * pullK, gl[1] + 4 * pullK], bend: 1, front: true, hand: 'grip' },
    armR: { target: [gr[0] - 3 * pullK, gr[1] + 4 * pullK], bend: -1, front: true, hand: 'grip' },
  });
  drawCage(g, ...CAGE_F, { ...cst, layer: 'front', grips: ['gripL', 'gripR'] });

  // ---- the CEO: hand off the bars, turns, two steps, stops (holding it in), walks on toward camera
  const b = S.T('s08b03');
  // (215,912) at the bars → two steps toward camera → stop (198,1090) → walks on, leaving at (190,1170) = s09's start
  const pos = S.k(t, [
    ['s08b03', { x: 215, y: 912 }], ['s08b03+0.58', { x: 215, y: 912 }],
    ['s08b03+1.35', { x: 198, y: 1090 }, 'sine'], ['s08b03+2.6', { x: 198, y: 1090 }],
    ['scene.end', { x: 190, y: 1170 }, 'in'],
  ]);
  const cs = hqScaleAt('front', pos.y);
  const moving = (t > b + 0.58 && t < b + 1.35) || t > b + 2.6;
  const phase = (t < b + 2 ? (t - b - 0.58) : (t - b - 2.6) + 0.8) * TAU * 1.05;
  // the turn, AWAY from the cage (over the left shoulder): the hand leaves the bars (+0 → +0.3); the head goes first
  // (back view: lost profile, then through the over-the-shoulder crossfade in 3 frames to a 3/4 face, +0.12 → +0.54);
  // the body follows on the swap (+0.58: front view, 3/4 to screen-left) and squares up by +1.05 while walking.
  const headK = sstep(b + 0.12, b + 0.42, t);
  const overK = clamp((t - (b + 0.42)) / 0.12);
  const swap = b + 0.58;
  const back = t < swap;
  const bodyK = sstep(swap, b + 1.05, t);
  const handOff = sstep(b + 0.0, b + 0.3, t);
  const L = (wx, wy) => selfLocal(pos.x, pos.y, cs, 1, wx, wy);
  // in-breath, swallow, clench/unclench, flinches at each rattle
  const breathIn = S.k(t, [['s08b03+1.3', 0], ['s08b03+1.85', 1], ['s08b03+2.25', 1], ['s08b03+2.6', 0.2]]);
  const swallow = Math.sin(clamp((t - (b + 2.05)) / 0.45) * Math.PI);
  let flinch = 0;
  for (const r of rattles) { const d = t - r; if (d > 0.04 && d < 0.4) flinch = Math.max(flinch, Math.sin(((d - 0.04) / 0.36) * Math.PI)); }
  const clench = (t > b + 1.4 && t < b + 1.75) || (t > b + 2.05 && t < b + 2.45) || t > b + 2.75;
  const face = {
    ...SELF_EXPR.holdingBackTears, tears: 0.85, lookY: 0.15 + 0.15 * swallow, lookX: back ? -0.3 : lerp(-0.35, -0.08, bodyK),
    lidL: 0.32 + 0.35 * flinch, lidU: 0.24 + 0.2 * flinch, pressed: 0.95, tremble: 0.55,
    blink: Math.max(blinkAt(t, b + 1.36, 0.32), blinkAt(t, b + 0.5, 0.16)),
  };
  let armL, armR;
  if (back) {
    // the hand lets go of the cage's left bars and drops to the side (elbow out, never across the back)
    const tg = L(252, 800);
    armR = handOff < 1 ? { target: [lerp(tg[0], 70, handOff), lerp(tg[1], -198, handOff)], bend: 1, hand: handOff < 0.3 ? 'grip' : 'rest' } : 'rest';
    armL = 'rest';
  } else {
    armL = { preset: 'rest', hand: clench ? 'fist' : 'rest' };
    armR = { preset: 'rest', hand: clench ? 'fist' : 'rest' };
  }
  drawSelf(g, pos.x, pos.y, cs, {
    t, outfit: 'ceo', facing: 1,
    view: back ? 'back' : 'front',
    headTurn: back ? -0.5 * headK - 0.3 * overK : lerp(-0.62, 0, bodyK) + 0.03 * flinch,
    bodyTurn: back ? 0 : lerp(-0.55, 0, bodyK),
    walk: moving ? { phase } : null,
    shrug: 0.55 * breathIn + 0.12 * flinch, headDY: 3 * swallow - 2 * breathIn,
    lean: -0.02 * breathIn,
    face, armL, armR,
  });
  drawHQForeground(g, 'front', st);
  g.restore();
  grade(g, COLD, 0);
  vignette(g, VIG);
}
