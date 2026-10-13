// s05 · chaos — Fear's panic as a pattern: the alarm, every emotion herded out, and Consciousness left alone
// in the noise with the one presence nobody can evacuate.
//
//   1  scene.start   → s05b01+1.3   `alarm` medium: Fear lunges, yanks the handle, darts a look at the back of the
//                                    room and scurries off right; the CEO (still kneeling, as s04 ended) reaches out
//                                    too late, a silent "wait", starts to rise
//   2  s05b01+1.3    → s05b02       `front` console: Fear picked up mid-dash in front of its post (the CEO's eyes
//                                    follow it), up on tiptoe behind the row shooing; JOY pops and windmills,
//                                    ANGER throws his hands up and stomps off, SADNESS slides off slowly, CALM rises
//                                    and goes to her; the CEO in the background finishes rising
//   3  s05b02        → s05b03       `front` door: CALM guiding SADNESS out, ANGER's glance back, JOY last ("We always
//                                    come back."), the door swings shut behind her
//   4  s05b02+1.9    → s05b03+2.7   `alarm` close: the PANIC ATTACK under "Panic attacks, forcing every…": Fear
//                                    clinging to the handle, eyes squeezed shut, hyperventilating (fast shoulder rise
//                                    and fall), tuft vibrating, the red pulse on its cheek; the door slams off-screen
//                                    behind the evacuated emotions and it flinches
//   5  s05b03+2.7    → end (+0.9)   `front` wide on "…emotion out of my mind" → "Causing chaos.": the empty console,
//                                    the CEO alone finishing a slow half circle (begun off-screen), pages slipping;
//                                    hands over the ears, the clipboard drops and spills its pages, the bell dies,
//                                    hands lower, shoulders sag; Fear slides down the wall and hugs itself. One slow
//                                    push ends EXACTLY on s06's first camera (CAM.end), held through the dissolve, so
//                                    the "one day" dissolve keeps the set still and only the people change

import { createCanvas } from '@napi-rs/canvas';
import { W, H, TAU, clamp, lerp, fbm, blinkAt, applyCamera, drift, vignette, shade, circle, roundRect, continuousRate } from '../engine.mjs';
import { withSpeech } from '../face.mjs';
import { drawFear, FEAR_ARMS } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, SELF_ARMS, drawClipboard, selfPoseAnchors, selfLocal } from '../chars/self.mjs';
import { drawEmotion, EMOTION_EXPR, PANIC_FACE } from '../chars/emotions.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, drawAlarmStation, HQ_VIEWS, HQ_COLORS, hqScaleAt, ALARM_REACH } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';

export const id = 's05';

export const sfx = [
  // the pull (clack at 0.055 s in the file) and the bell, which dies under "Causing chaos."
  { at: 's05b01+0.195', name: 'alarm_pull', gain: -6 },                 // clack (0.055 s in) on the pull at +0.25
  { at: 's05b01+0.3', name: 'alarm_bell', until: 's05b04.end', loop: true, gain: -20, fade: 1.55 },
  // Fear's little feet scurrying off, and the evacuation
  { at: 's05b01+0.58', name: 'footsteps', gain: -17, rate: 1.9 },
  { at: 's05b01+0.75', name: 'crowd_murmur', gain: -18 },
  { at: 's05b01+0.9', name: 'cloth_rustle', gain: -16 },                 // the CEO rising from the knee
  { at: 's05b01+1.47', name: 'door_whoosh', gain: -15 },                 // the EXIT door swings open (left edge of the wide)
  { at: 's05b01+1.88', name: 'footsteps', gain: -15, rate: 1.8 },         // ANGER lands from his hop and stomps (≈0.31 s steps)
  { at: 's05b02-0.45', name: 'crowd_murmur', gain: -21 },
  { at: 's05b02+0.48', name: 'footsteps', gain: -17, rate: 1.2 },         // through the door: ANGER, SADNESS, CALM, JOY
  { at: 's05b02+1.55', name: 'door_whoosh', gain: -17, rate: 1.15 },     // swings shut behind JOY (b02+1.92 → +2.42; thud on +2.42)
  // alone: the turn, the pages, the clipboard dropped as the hands go to the ears
  { at: 's05b03+1.05', name: 'cloth_rustle', gain: -20, rate: 0.85 },    // the half circle starts as the empty room cuts in
  { at: 's05b03+1.2', name: 'paper_rustle', gain: -17 },                 // pages slip at b03+1.3 / +2.3 / +3.4
  { at: 's05b03+2.2', name: 'paper_rustle', gain: -20, rate: 1.1 },
  { at: 's05b03+3.3', name: 'paper_rustle', gain: -19, rate: 1.1 },
  { at: 's05b03.end-0.42', name: 'cloth_rustle', gain: -17 },
  { at: 's05b03.end-0.52', name: 'paper_rustle', gain: -14 },            // the clipboard lands (swish peak 0.5 s in)
  // the long shaky exhale as the hands come down (exhale ≈ 1.45 s into the file)
  { at: 's05b04+0.3', name: 'breath_shaky', gain: -15 },
  // Fear lets go: the handle springs back up (alarmPulled 1→0 over s05b04+0.72 → +0.98), as in s02 / s07
  { at: 's05b04+0.67', name: 'alarm_pull', gain: -20, rate: 0.85, pan: 0.4 },
  // the panic-attack close: racing heart + fast shaky breathing under "Panic attacks, forcing every…"
  { at: 's05b02+1.9', name: 'heartbeat', until: 's05b03+2.95', loop: true, gain: -15, rate: 2.0, fade: 0.5 },
  { at: 's05b02+1.92', name: 'breath_shaky', until: 's05b03+2.85', gain: -19, rate: 1.35, fade: 0.3, pan: 0.15 },
];

// ---------------------------------------------------------------- staging constants (staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const CAGE_F = [302, 846, 0.3];
const CEO_AT_ALARM_F = [640, 1000, 0.444];
const FEAR_ALARM_F = [734, 973, 0.42];
const CEO_MID = [450, 1060, 0.5];                 // alone in the middle of the room (staging §3 s05)
const [AFX, AFY, AFS] = HQ_VIEWS.alarm.anchors.fearAtAlarm;
const [ACX, ACY, ACS] = HQ_VIEWS.alarm.anchors.ceoKneel;
const SLOT = HQ_VIEWS.front.anchors;              // consoleSlot1..4 = CALM, ANGER, SADNESS, JOY
const T_OFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 };   // per-character idle offsets (staging §5.11)

const COLD = 0.4, VIGNETTE = 0.45;
const CAM = {
  medium: { x: 445, y: 960, zoom: 1.0 },
  // the evacuation wide: the staged 'console' cam (zoom 1.35) cut CALM and JOY in half at the frame edges, so their
  // reactions did not read; this frame holds all four, Fear, the CEO behind them and the Void over everything, and
  // rhymes with the empty wide of shot 4 (same room, a minute later, nobody left)
  console: { x: 466, y: 846, zoom: 1.0 },
  console2: { x: 462, y: 852, zoom: 1.03 },
  door: { x: 234, y: 846, zoom: 2.08 },          // tighter than the staged {215,820,1.7}: the group fills the frame
  door2: { x: 228, y: 842, zoom: 2.14 },
  est: { x: 452, y: 816, zoom: 0.98 },             // the staged 'establish' wide, a touch tighter so the CEO reads
  // = s06's FIRST camera (s06 holds it through the dissolve, then moves on): with both scenes on the same camera
  // the set, the Void, the cage and Fear's spot do not double in the "one day" dissolve; only the people change
  end: { x: 540, y: 940, zoom: 1.2 },
  // the panic medium, alarm view: Fear to the knees, face on the left third, the red station on the right
  panic: { x: 572, y: 1092, zoom: 1.46 },        // (zoom stays inside one hq.mjs cache resolution bucket, ≤ 1.56)
  panic2: { x: 566, y: 1080, zoom: 1.55 },
};
// cuts (one source of truth for every track, so no blocking can leak across a cut)
const CUT12 = 's05b01+1.3';     // alarm wall → the evacuation wide
const CUT23 = 's05b02';         // → the EXIT door
const CUT3P = 's05b02+1.9';     // → the panic close: JOY is through the door (gone at +1.9), the door starts to swing
                                //    shut; the cut lands on "attacks" (b03+0.28); the slam is heard off-screen
const CUTPW = 's05b03+2.7';     // → the empty room, on "emotion out of my mind" (b03+2.74); the close runs 2.4 s
const SWEEP0 = 's05b03+1.0';    // the CEO's slow look around starts off-screen, during the panic close
function shotOf(t, S) {
  if (t < S.T(CUT12)) return 1;
  if (t < S.T(CUT23)) return 2;
  if (t < S.T(CUT3P)) return 3;
  if (t < S.T(CUTPW)) return 4;
  return 5;
}
const DOOR_SHUT0 = 's05b02+1.92', DOOR_SHUT1 = 's05b02+2.42';   // JOY is through at +1.9

// The EXIT doorway, front view (hq.mjs: wallXform(side -1, lam 1.3, cheat 0.12) → world = (148.4 + 0.5394·X,
// 936 − 0.529·X + 1.3·Y) for door-local (X, Y)): vertical jambs at x 115 / 182, the arch from the spring line
// (Y −150) to the crown (Y −212). Someone walking out is visible only inside the opening once past the wall plane:
// this clip keeps the whole room side (x ≥ 182) plus the opening, so the near jamb hides them as they go.
const DOOR_CLIP = (() => {
  const P = (X, Y) => [148.4 + 0.5394 * X, 936 - 0.529 * X + 1.3 * Y];
  const pts = [[115, 4000], P(-62, -150)];
  for (let i = 1; i < 12; i++) { const a = Math.PI + (Math.PI * i) / 12; pts.push(P(62 * Math.cos(a), -150 + 62 * Math.sin(a))); }
  pts.push(P(62, -150), [182, -4000], [4000, -4000], [4000, 4000]);
  return pts;
})();
function clipDoor(g) {
  g.beginPath();
  DOOR_CLIP.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y)));
  g.closePath();
  g.clip();
}
const DOOR_IN = [150, 937], DOOR_OUT = [66, 936];   // threshold centre / far enough out to be hidden by the jamb

function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, W, H); }
  g.restore();
}
const lerpCam = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), zoom: lerp(a.zoom, b.zoom, k) });
function liveCam(cam, t, amp = 2.5) {
  const d = drift(t, amp);
  return { x: cam.x + d.dx / cam.zoom, y: cam.y + d.dy / cam.zoom, zoom: cam.zoom, rot: d.dr * 0.5 };
}
const sine = (k) => -(Math.cos(Math.PI * clamp(k)) - 1) / 2;
const pulse = (t) => 0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 1.2 - Math.PI / 2);   // the set's alarm pulse

// Fear's hand ON the alarm handle (alarm view; handle centre = ALARM_REACH + 26·pulled, Fear-local). The wrist goes
// `d` px back from the point the fist should cover, along the hand's screen angle `ang` (≈ −1.2: knuckles up, the
// fingers hooked over the top of the handle to pull it down), and the point is taken into Fear's BODY frame: drawFear
// rotates the arms with `lean` about the feet (an unrotated target drifted the fist off the handle — below it and
// onto the PULL DOWN label); `dx` = Fear's feet offset from the alarm anchor (local px).
function onHandle(px, py, ang, lean, dx = 0, d = 8) {
  const x = px - d * Math.cos(ang) - dx, y = py - d * Math.sin(ang);
  const c = Math.cos(-lean), s = Math.sin(-lean);
  return { target: [x * c - y * s, x * s + y * c], handAng: ang - lean };
}

// ---------------------------------------------------------------- shared state
function setState(t, S) {
  return {
    t,
    alarm: S.k(t, [['s05b01+0.25', 0], ['s05b01+0.55', 1], ['s05b04', 1], ['s05b04.end', 0, 'sine']]),
    alarmPulled: S.k(t, [['s05b01+0.25', 0], ['s05b01+0.5', 1], ['s05b04+0.72', 1], ['s05b04+0.98', 0]]),
    lightsDim: 0.35,
    consoleGlow: S.k(t, [['s05b01+0.3', 0.8], ['s05b01+1.4', 0.6]]),
    mist: 0.6, voidShadow: 0.7, screenMode: 'room',
    // opens as the evacuation starts (seen at the left edge of the wide), shuts behind JOY inside the door shot
    doorOpen: S.k(t, [['s05b01+1.5', 0], ['s05b01+2.3', 1, 'inOut'], [DOOR_SHUT0, 1], [DOOR_SHUT1, 0, 'inOut']]),
  };
}

// ================================================================ SHOT 1 — the alarm wall
function fearAlarmPose(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  const pulled = k([['s05b01+0.25', 0], ['s05b01+0.5', 1]]);
  const reach = k([['scene.start', 0.55], ['s05b01-0.12', 1, 'out']]);          // already lunging on frame 1
  const holding = k([['s05b01+0.56', 1], ['s05b01+0.66', 0]]);
  // the scurry gets going at once (sine, was a slow quadratic start): Fear is a body-width clear of the CEO's
  // late reach (+0.8 → +1.08), which used to land on its chin and scarf
  const run = k([['s05b01+0.6', 0], ['s05b01+1.32', 1, 'sine']]);
  const x = lerp(AFX, 1010, run);
  // gaze: on the handle → "Out!" at the others (right) → a darting look back at the hood → off to the console
  const gaze = k([
    ['scene.start', { lookX: 0.45, lookY: -0.55 }], ['s05b01-0.05', { lookX: 0.45, lookY: -0.55 }],
    ['s05b01+0.06', { lookX: 0.85, lookY: 0.05 }], ['s05b01+0.42', { lookX: 0.85, lookY: 0.05 }],
    ['s05b01+0.5', { lookX: -0.7, lookY: -0.72 }], ['s05b01+0.66', { lookX: -0.7, lookY: -0.72 }],
    ['s05b01+0.74', { lookX: 0.9, lookY: 0.1 }],
  ]);
  const face = withSpeech({ ...PANIC_FACE, browIn: 0.55, browUp: 1, lidU: -0.4, pupil: 0.52, open: 0.25, wide: 0.6, smile: -0.5,
    tremble: 0.7, teeth: 0.4, ...gaze, blink: blinkAt(t, S.T('s05b01+0.27'), 0.12), noAutoBlink: true }, S.lip('FEAR', t), 1);
  const ty = ALARM_REACH[1] + 26 * pulled;
  const yank = k([['s05b01+0.25', 0], ['s05b01+0.42', 1], ['s05b01+0.62', 0.2]]);
  const lean = 0.12 - 0.2 * yank + 0.1 * run;
  // the fist lands ON the handle (knuckles up, fingers over the top) and rides it down; the elbow drops for the pull
  const h = onHandle(ALARM_REACH[0] + 4, ty, -1.15, lean);
  // (letting go blends the hand off the handle into the first flap over 0.1 s instead of jumping there)
  const flapR = [62 + 20 * Math.sin(t * TAU * 4.2), -150 - 30 * Math.sin(t * TAU * 4.2)];
  const flapAng = -0.95 + 0.35 * Math.sin(t * TAU * 4.2 + 0.5) - lean;          // the shooing hand, fingers up
  const armR = holding > 0.001
    ? { target: [lerp(flapR[0], lerp(70, h.target[0], reach), holding), lerp(flapR[1], lerp(-150, h.target[1], reach), holding)],
        bend: -1, hand: holding > 0.5 ? 'grip' : 'open', front: true, handAng: lerp(flapAng, lerp(-0.55 - lean, h.handAng, reach), holding),
        ...(holding > 0.5 ? {} : { palmDir: [0.7, 0, 0.7] }) }
    : { target: flapR, bend: -1, hand: 'open', front: true, handAng: flapAng, palmDir: [0.7, 0, 0.7] };   // palm out: shooing
  const armL = holding > 0.5
    ? { target: [-20 + 30 * pulled, -150 + 40 * pulled], bend: -1, hand: 'fist', front: true }     // fist pumping down with the yank
    : { target: [-60 - 18 * Math.sin(t * TAU * 4.2 + 1.6), -160 + 34 * Math.sin(t * TAU * 4.2 + 1.6)], bend: 1, hand: 'open' };
  return {
    x, y: AFY, s: AFS,
    pose: { t, facing: 1, face, tremble: 0.7, crouch: 0.08 + 0.4 * yank, lean,
      headTurn: lerp(0.15, 0.3, run) - 0.45 * k([['s05b01+0.46', 0], ['s05b01+0.52', 1], ['s05b01+0.66', 1], ['s05b01+0.74', 0]]),
      headTilt: -0.08 * yank, armL, armR, walk: run > 0 ? { phase: t * TAU * 4.2 } : null, breathRate: 1.4, breathe: 1.4 },
  };
}

function ceoAlarmPose(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  const HOOD = { lookX: -0.72, lookY: -0.86 }, FEAR = { lookX: 0.62, lookY: 0.3 }, RUN = { lookX: 0.92, lookY: 0.12 };
  const gaze = k([['scene.start', HOOD], ['s05b01+0.02', HOOD], ['s05b01+0.12', FEAR, 'out'], ['s05b01+0.66', FEAR], ['s05b01+0.82', RUN]]);
  const startle = k([['s05b01+0.02', 0], ['s05b01+0.14', 1, 'out'], ['s05b01+0.7', 0.6]]);
  // = s04's last frame (eyes up at the hood, lids lifted with the gaze, brows knit, lips pressed): a cut, no time skip
  const KNIT = { browIn: 0.55, browUp: -0.05, browSquish: 0.7, lidTilt: 0.15, lidU: -0.1, lidL: 0.04, smile: -0.22, pressed: 0.8, tears: 0.2 };
  const ALARM = { browIn: 0.6, browUp: 0.75, browSquish: 0.2, lidTilt: 0.1, lidU: -0.22, lidL: 0, smile: -0.25, pressed: 0, open: 0.12, tears: 0.15 };
  const ex = k([['scene.start', KNIT], ['s05b01+0.02', KNIT], ['s05b01+0.16', ALARM, 'out']]);
  // a silent "wait": w (round) → ay (open) → closing
  const wO = k([['s05b01+0.84', 0], ['s05b01+0.94', 0.16], ['s05b01+1.04', 0.34], ['s05b01+1.2', 0.12]]);
  const wR = k([['s05b01+0.84', 0], ['s05b01+0.94', 0.7], ['s05b01+1.04', 0.1], ['s05b01+1.2', 0]]);
  const face = { ...ex, ...gaze, open: (ex.open || 0) + wO, round: wR, blink: blinkAt(t, S.T('s05b01+0.3'), 0.14) };
  // the reach goes after Fear's back at its shoulder height (world ≈ (590, 1075)), fingers open, a beat too late —
  // it used to rise above Fear's head with the palm up, which read as hailing a cab
  const reachK = k([['s05b01+0.8', 0], ['s05b01+1.08', 1, 'out']]);
  const KNEE = [58, -150], AFTER = [198, -214];
  const armR = reachK > 0.02
    ? { target: [lerp(KNEE[0], AFTER[0], reachK), lerp(KNEE[1], AFTER[1], reachK)], bend: -1, front: true,
        hand: 'open', handAngle: lerp(0.5, -0.12, reachK), thumb: -1 }
    : { target: KNEE, bend: -1, front: true, hand: 'drape', palm: true, wrist: 0.75, thumb: -1 };
  return { t, outfit: 'ceo', facing: 1, kneel: k([['s05b01+0.9', 1], ['s05b01+1.3', 0.4]]),
    headTurn: k([['scene.start', -0.06], ['s05b01+0.06', -0.06], ['s05b01+0.3', 0.38, 'out']]),
    headTilt: k([['scene.start', -0.05], ['s05b01+0.3', 0.02]]), headDY: -4 * startle, lean: -0.03 * startle, face, armR };
}

function renderAlarm(g, t, S) {
  const st = setState(t, S);
  g.save();
  applyCamera(g, liveCam(CAM.medium, t, 2));
  drawHQ(g, 'alarm', st);
  const f = fearAlarmPose(t, S);
  drawFear(g, f.x, f.y, f.s, f.pose);
  drawSelf(g, ACX, ACY, ACS, ceoAlarmPose(t, S));
  drawHQForeground(g, 'alarm', st);
  drawAlarmLight(g, 'alarm', st);
  g.restore();
}

// ================================================================ SHOT 4 — the panic attack (alarm view close)
// Back at its post (the front room's shot 5 picks it up in the same state): both hands locked on the pulled handle,
// eyes squeezed shut, hyperventilating — the shoulders heave at ~1.9 Hz and the mouth gasps on each in-breath — the
// whole body shivering so the tuft buzzes; the red beacon pulses on its cheek. The door thuds shut off-screen behind
// the others (door_whoosh thud at s05b02+2.42): a flinch that hunches it tighter.
const PANIC_BR = 1.9;   // breaths per second (= drawFear's own breathRate, so the extra heave below is in phase)
// Fear stands this far nearer the station in the close (Fear-local px): from the anchor spot the far (left) arm cannot
// reach across the body to the handle, and both fists hung below it; one small step in, both hands lock on
const PANIC_DX = 15;
function fearPanicPose(t, S) {
  const ph = Math.sin(t * TAU * PANIC_BR);                        // +1 = top of the in-breath
  const ts = S.T('s05b02+2.45');
  const fl = t >= ts ? Math.exp(-(t - ts) * 5) * clamp((t - ts) / 0.05) : 0;   // the slam: sharp, fast decay
  const crouch = clamp(0.26 - 0.1 * ph + 0.2 * fl);
  const handleY = ALARM_REACH[1] + 26;                            // the handle is pulled down (alarmPulled 1)
  const lean = 0.1 + 0.03 * fl;
  // squeezed shut (lidL < 0.4: above it the rig draws happy closed arcs), lids pinched toward the nose under knotted,
  // inner-up brows; a gasping grimace that opens on every in-breath; a sweat drop
  const face = {
    browIn: 1, browUp: 0.5 - 0.2 * fl, browSquish: 1, lidU: 1, lidL: 0.36, lidTilt: -0.8,
    smile: -0.6, wide: 0.75, teeth: 0.85, tremble: 1, sweat: 0.9,
    open: 0.16 + 0.26 * Math.max(0, ph) - 0.08 * fl,             // gasping in; teeth clench at the slam
    lookX: 0.3, lookY: 0, noAutoBlink: true,
  };
  // both fists locked side by side on the pulled handle, knuckles up, elbows hanging down: the weight hangs off it
  const hR = onHandle(ALARM_REACH[0] + 12, handleY, -1.15, lean, PANIC_DX);
  const hL = onHandle(ALARM_REACH[0] - 14, handleY + 1, -1.3, lean, PANIC_DX);
  return {
    t, facing: 1, face, crouch, tremble: 0.85, breathRate: PANIC_BR, breathe: 2,
    headDY: -4.5 * ph + 8 * fl, headTilt: -0.05 + 0.04 * fl, headTurn: 0.14, lean,
    armR: { ...hR, bend: -1, hand: 'grip', front: true },
    armL: { ...hL, bend: -1, hand: 'grip', front: true },
    whiten: 0.6,                                                   // knuckles paling on the grip
    scarfWind: 0.15 * ph,
  };
}
// world-space centre of Fear's head (drawFear geometry: neck −148 + crouch·20 + breath·1.2 + headDY, head centre −66)
function fearHeadAt(x, y, s, P) {
  const br = Math.sin(P.t * TAU * P.breathRate) * P.breathe;
  const h = -148 + P.crouch * 20 + br * 1.2 + (P.headDY || 0) - 66;
  return [x - h * Math.sin(P.lean || 0) * s, y + h * Math.cos(P.lean || 0) * s];
}
// the beacon's red on the station-side cheek, kept inside the head outline (pulse = the set's alarm pulse)
function drawFearRedCheek(g, x, y, s, P, t, A) {
  const [hx, hy] = fearHeadAt(x, y, s, P);
  g.save();
  g.beginPath(); g.ellipse(hx, hy, 74 * s, 68 * s, 0, 0, TAU); g.clip();
  const cx = hx + 58 * s, cy = hy + 18 * s, r = 82 * s;
  const a = A * (0.16 + 0.22 * pulse(t));
  const gr = g.createRadialGradient(cx, cy, 0, cx, cy, r);
  gr.addColorStop(0, `rgba(255,64,84,${a})`); gr.addColorStop(0.6, `rgba(255,64,84,${a * 0.4})`); gr.addColorStop(1, 'rgba(255,64,84,0)');
  g.fillStyle = gr; g.fillRect(cx - r, cy - r, 2 * r, 2 * r);
  g.restore();
}
function renderPanic(g, t, S) {
  const st = setState(t, S);
  const u = sine((t - S.T(CUT3P)) / (S.T(CUTPW) - S.T(CUT3P)));
  const cam = { x: lerp(CAM.panic.x, CAM.panic2.x, u), y: lerp(CAM.panic.y, CAM.panic2.y, u),
    zoom: Math.exp(lerp(Math.log(CAM.panic.zoom), Math.log(CAM.panic2.zoom), u)) };
  g.save();
  applyCamera(g, liveCam(cam, t, 1.6));
  drawHQ(g, 'alarm', st);
  const P = fearPanicPose(t, S);
  const fx = AFX + PANIC_DX * AFS;
  drawFear(g, fx, AFY, AFS, P);
  drawFearRedCheek(g, fx, AFY, AFS, P, t, st.alarm);
  drawHQForeground(g, 'alarm', st);
  drawAlarmLight(g, 'alarm', st);
  g.restore();
}

// ================================================================ the FRONT room (shots 2, 3, 5)
// ---- the emotions: shot 2 (the evacuation wide: they leave the console row) and shot 3 (the EXIT door: they
//      file out through the opening, JOY last). Nobody fades in the middle of the room any more.
const SLOT_OF = { CALM: 'consoleSlot1', ANGER: 'consoleSlot2', SADNESS: 'consoleSlot3', JOY: 'consoleSlot4' };
// a key track [anchor, [x, y], ease?] → {x, y}
function path(t, S, keys) {
  const xs = S.k(t, keys.map(([a, p, e]) => [a, p[0], e])), ys = S.k(t, keys.map(([a, p, e]) => [a, p[1], e]));
  return { x: xs, y: ys };
}
const moving = (t, S, spans) => spans.some(([a, b]) => t > S.T(a) && t < S.T(b));
function emotionState(name, t, S, shot) {
  const k = (keys, e) => S.k(t, keys, e);
  const [sx0, sy0, ss0] = SLOT[SLOT_OF[name]];
  const tt = t + T_OFF[name];
  const walkPh = (rate) => ({ phase: t * TAU * rate + T_OFF[name] });
  let x, y, face, pose = {}, s = ss0;
  if (shot <= 2) {
    // ------------------------------------------------ shot 2: the evacuation wide (all four in frame)
    if (name === 'JOY') {
      // shooed off her stool by Fear popping up behind her: eyes pop, round "oh", windmilling; hops left, then hurries
      x = k([['s05b01+1.32', sx0], ['s05b01+1.62', 630, 'out'], ['s05b01+2.18', 624], ['s05b02', 516, 'in']]); y = sy0 + 10;
      const pop = k([['s05b01+1.3', 0.6], ['s05b01+1.4', 1], ['s05b01+1.78', 0]]);
      const flail = k([['s05b01+1.3', 1], ['s05b01+2.08', 1], ['s05b01+2.22', 0]]);
      face = { browUp: 0.95, browIn: 0.35, lidU: -0.35, pupil: 0.7, open: 0.45, round: 0.85, smile: 0,
        lookX: k([['s05b01+2.12', 0.75], ['s05b01+2.26', -0.35]]), lookY: 0.1,
        blink: blinkAt(t, S.T('s05b01+2.2'), 0.14), noAutoBlink: true };
      pose = { facing: -1, headDY: -14 * pop, headTurn: lerp(-0.25, 0.45, flail), lean: 0.07 * flail * Math.sin(t * 7.5),
        armL: flail > 0.5 ? 'flail' : 'rest', armR: flail > 0.5 ? 'flail' : 'rest',
        walk: moving(t, S, [['s05b01+1.34', 's05b01+1.62'], ['s05b01+2.2', 's05b02+0.1']]) ? walkPh(2.0) : null };
    } else if (name === 'SADNESS') {
      // slides off its stool slowly, lower lip out, eyes on the floor; shuffles left
      const slide = k([['s05b01+1.3', 0.3], ['s05b01+2.0', 1, 'sine']]);
      x = k([['s05b01+1.4', sx0 - 8], ['s05b02', 424, 'inOut']]); y = sy0 - 4;
      face = { ...EMOTION_EXPR.SADNESS, smile: -0.7, wide: -0.15, lookY: 0.75, lookX: -0.2, tears: 0.3 };
      pose = { facing: -1, headDY: 14 * slide, crouch: 0.15 * slide, headTilt: -0.05,
        walk: t > S.T('s05b01+1.5') ? walkPh(0.75) : null, armL: 'rest', armR: 'rest' };
    } else if (name === 'ANGER') {
      // both hands thrown up, brows in a hard V, a hop off the stool, then stomping out toward the door (frame left)
      const up = k([['s05b01+1.3', 0.7], ['s05b01+1.42', 1], ['s05b01+1.78', 1], ['s05b01+1.96', 0]]);
      const hop = k([['s05b01+1.62', 0], ['s05b01+1.76', 1, 'out'], ['s05b01+1.92', 0, 'in']]);
      x = k([['s05b01+1.92', sx0], ['s05b02', 296, 'in']]); y = sy0 + 6;   // stomping off; never crosses CALM in this shot
      face = { ...EMOTION_EXPR.ANGER, browIn: -1, browSquish: 0.85, pressed: 0.85, smile: -0.6, lidTilt: -0.45,
        lookX: k([['s05b01+1.9', 0.5], ['s05b01+2.05', -0.4]]), lookY: 0.1 };
      const raised = (side) => ({ target: [side * 92, -300], bend: -side, hand: 'palm' });
      pose = { facing: -1, heat: 0.9, headDY: -16 * hop, lean: -0.04 * up,
        armL: up > 0.5 ? raised(-1) : { preset: 'rest', hand: 'fist' }, armR: up > 0.5 ? raised(1) : { preset: 'rest', hand: 'fist' },
        walk: t > S.T('s05b01+1.95') ? walkPh(1.7) : null };
    } else { // CALM
      // rises in one smooth motion, lids level at half, and steps up toward SADNESS with an open palm
      const rise = k([['s05b01+1.3', 0.45], ['s05b01+1.95', 1, 'sine']]);
      const p = path(t, S, [['s05b01+2.0', [sx0, sy0 - 10]], ['s05b02', [182, sy0 - 22], 'inOut']]);
      x = p.x; y = p.y; s = hqScaleAt('front', y);
      face = { smile: 0.05, lidU: 0.45, lidL: 0.1, lidTilt: 0, browIn: 0.15, lookX: 0.6, lookY: 0.2 };
      pose = { facing: 1, headDY: 12 * (1 - rise), headTurn: 0.45 * rise,
        armR: rise > 0.8 ? { target: [112, -250], bend: 1, hand: 'palm' } : 'rest', armL: 'rest',
        walk: t > S.T('s05b01+2.02') ? walkPh(0.8) : null };
    }
    return { name, x, y, s, alpha: 1, pose: { t: tt, view: 'front', face, ...pose } };
  }
  if (shot > 3) return { name, alpha: 0 };
  // ------------------------------------------------ shot 3: the EXIT door (everyone walks out through the opening)
  let p, walking = false;
  if (name === 'ANGER') {
    // in the doorway, a glance back at Fear: the hard V softens into worry for a moment, hardens, and he goes
    p = path(t, S, [['s05b02', DOOR_IN], ['s05b02+0.52', DOOR_IN], ['s05b02+0.82', DOOR_OUT, 'in']]);
    walking = moving(t, S, [['s05b02+0.5', 's05b02+0.9']]);
    const soft = k([['s05b02+0.16', 0], ['s05b02+0.28', 1], ['s05b02+0.4', 1], ['s05b02+0.5', 0]]);
    face = { browIn: lerp(-0.95, 0.75, soft), browSquish: lerp(0.8, 0.3, soft), browUp: 0.2 * soft, pressed: lerp(0.8, 0.25, soft),
      smile: lerp(-0.55, -0.3, soft), lidTilt: lerp(-0.4, 0.25, soft), lidU: lerp(0.15, 0.02, soft),
      lookX: k([['s05b02+0.04', -0.4], ['s05b02+0.13', 0.85], ['s05b02+0.48', 0.85], ['s05b02+0.56', -0.5]]), lookY: 0.05,
      blink: blinkAt(t, S.T('s05b02+0.5'), 0.12), noAutoBlink: true };
    pose = { facing: -1, heat: lerp(0.75, 0.2, soft),
      headTurn: k([['s05b02', -0.3], ['s05b02+0.12', 0.6], ['s05b02+0.48', 0.6], ['s05b02+0.58', -0.35]]),
      armL: { preset: 'rest', hand: 'fist' }, armR: { preset: 'rest', hand: 'fist' } };
  } else if (name === 'SADNESS') {
    // waits behind CALM looking back over its shoulder, lower lip out, a tiny wave at the empty room; then follows
    // CALM out. (CALM, on its door side, holds its near elbow.)
    p = path(t, S, [['s05b02', [250, 951]], ['s05b02+0.55', [238, 949]], ['s05b02+0.95', [236, 949]],
      ['s05b02+1.25', DOOR_IN, 'inOut'], ['s05b02+1.52', DOOR_OUT, 'in']]);
    walking = moving(t, S, [['s05b02-0.1', 's05b02+0.55'], ['s05b02+0.95', 's05b02+1.55']]);
    const back = k([['s05b02+0.7', 1], ['s05b02+0.82', 0]]);
    face = { ...EMOTION_EXPR.SADNESS, smile: -0.72, wide: -0.15, lookX: lerp(-0.3, 0.85, back), lookY: 0.12, tears: 0.35 };
    // the tiny wave is low and out to the side (shoulder height): at the old height the hand flapped behind the head
    // and read as scratching it
    pose = { facing: -1, headTurn: lerp(-0.2, 0.55, back), headTilt: 0.05, armR: 'rest',
      armL: t > S.T('s05b02+0.12') && t < S.T('s05b02+0.66') ? { preset: 'wave', dy: 64, dx: 16 } : 'rest' };
  } else if (name === 'CALM') {
    // the only unhurried body in the room. CALM stands on SADNESS's door side, a step nearer the camera (drawn over
    // SADNESS: from behind SADNESS the guiding hand was hidden by SADNESS's body), its near hand cupped at SADNESS's
    // elbow while SADNESS waves at the room; once ANGER has cleared the doorway, its other palm opens toward the door;
    // then it leads SADNESS out, the hand sliding off the elbow as it steps through.
    p = path(t, S, [['s05b02', [194, 956]], ['s05b02+0.5', [186, 955]], ['s05b02+0.92', [186, 955]],
      ['s05b02+1.15', DOOR_IN, 'inOut'], ['s05b02+1.4', DOOR_OUT, 'in']]);
    walking = moving(t, S, [['s05b02-0.1', 's05b02+0.5'], ['s05b02+0.92', 's05b02+1.43']]);
    // eyes on SADNESS (screen-right) through the wave, then to the door
    const toDoor = k([['s05b02+0.52', 0], ['s05b02+0.68', 1]]);
    face = { smile: 0.18, lidU: 0.45, lidL: 0.12, lidTilt: 0, browIn: 0.1, lookX: lerp(0.5, -0.45, toDoor), lookY: lerp(0.3, 0.15, toDoor) };
    const s0 = hqScaleAt('front', p.y);
    const sad = emotionState('SADNESS', t, S, 3);
    // SADNESS's screen-left elbow, in CALM-local coords (facing -1: local +x = screen-left)
    const elbow = [(p.x - (sad.x - 66 * sad.s)) / s0, (sad.y - 182 * sad.s - p.y) / s0];
    const rel = k([['s05b02+0.92', 0], ['s05b02+1.06', 1]]);        // the hand slides off as CALM steps ahead
    const low = [-40, -200];
    const guideArm = rel < 0.5
      ? { target: [lerp(elbow[0], low[0], rel), lerp(elbow[1], low[1], rel)], bend: 1, hand: 'cup', palmDir: [-0.85, 0.2, -0.45] }
      : { target: [lerp(elbow[0], low[0], rel), lerp(elbow[1], low[1], rel)], bend: -1, hand: 'rest', handAng: Math.PI / 2 + 0.2 };
    // palm up toward the (now empty) doorway: "this way"
    const ush = k([['s05b02+0.7', 0], ['s05b02+0.86', 1], ['s05b02+0.98', 1], ['s05b02+1.14', 0]]);
    const ushArm = ush > 0.3
      ? { target: [lerp(40, 112, ush), lerp(-200, -240, ush)], bend: -1, hand: 'palm', palmDir: [0.25, -0.85, 0.45], handAng: lerp(0.8, -0.3, ush) }
      : 'rest';
    pose = { facing: -1, headTurn: lerp(0.3, -0.15, toDoor), armR: ushArm, armL: guideArm };
  } else { // JOY
    // last: in the foreground, "We always come back." — the big smile thins, her eyes flick back toward Fear (screen
    // right, the alarm), brows tilt up; the alarm's red pulse on her right cheek. Then she hurries out.
    p = path(t, S, [['s05b02', [336, 1014]], ['s05b02+1.2', [330, 1012]], ['s05b02+1.62', [196, 943], 'inOut'],
      ['s05b02+1.7', DOOR_IN], ['s05b02+1.9', DOOR_OUT, 'in']]);
    walking = moving(t, S, [['s05b02+1.24', 's05b02+1.92']]);
    const thin = k([['s05b02+0.2', 0], ['s05b02.end', 1]]);
    const turn = k([['s05b02+1.12', 0], ['s05b02+1.3', 1]]);
    face = withSpeech({ smile: lerp(0.95, 0.32, thin), lidL: lerp(0.4, 0.12, thin), browUp: lerp(0.35, 0.18, thin),
      browIn: lerp(0.05, 0.8, thin), blush: 0.25,
      lookX: k([['s05b02', -0.5], ['s05b02+0.12', -0.5], ['s05b02+0.26', 0.85], ['s05b02+1.12', 0.85], ['s05b02+1.24', -0.6]]),
      lookY: -0.08, blink: Math.max(blinkAt(t, S.T('s05b02.end+0.02'), 0.18)), noAutoBlink: true }, S.lip('JOY', t), 1);
    // the speaker's one small gesture: the near hand lifts a little, palm open toward Fear (screen right), on "We
    // always come back.", and drops as she turns to go (she stood with both arms hanging through the line)
    const lift = k([['s05b02+0.18', 0], ['s05b02+0.5', 1], ['s05b02+1.0', 1], ['s05b02+1.24', 0]]);
    const bob = Math.sin((t - S.T('s05b02')) * TAU * 1.1) * 3 * lift;
    pose = { facing: -1, headTurn: lerp(0.55, -0.25, turn), headTilt: 0.06 * (1 - turn), armR: 'rest', redCheek: 1,
      armL: lift > 0.02
        ? { target: [lerp(-64, -84, lift), lerp(-119, -186, lift) + bob], bend: -1, hand: lift > 0.4 ? 'palm' : 'rest',
            palmDir: lift > 0.4 ? [-0.55, -0.55, 0.6] : undefined, handAng: lerp(Math.PI / 2 + 0.2, Math.PI + 0.35, lift) }
        : 'rest' };
  }
  x = p.x; y = p.y; s = hqScaleAt('front', y);
  if (walking) pose.walk = walkPh(name === 'SADNESS' ? 0.85 : name === 'ANGER' ? 1.6 : name === 'JOY' ? 1.5 : 0.8);
  return { name, x, y, s, alpha: 1, door: true, pose: { t: tt, view: 'front', face, ...pose } };
}

// the alarm's soft red pulse on JOY's right cheek (the alarm wall is off-frame right): a red light kept inside the
// head's outline so it sits ON the cheek and reads at phone size (the old screen-blended halo was invisible)
function drawRedCheek(g, e, t, A) {
  if (A <= 0.01) return;
  const s = e.s, hx = e.x + (e.pose.headDX || 0) * s, hy = e.y - 304 * s + (e.pose.headDY || 0) * s;
  g.save();
  g.beginPath(); g.ellipse(hx, hy, 84 * s, 80 * s, 0, 0, TAU); g.clip();
  const cx = hx + 64 * s, cy = hy + 42 * s, r = 56 * s;            // under the right eye, toward the off-frame alarm
  const gr = g.createRadialGradient(cx, cy, 0, cx, cy, r);
  const a = A * (0.26 + 0.22 * pulse(t));
  gr.addColorStop(0, `rgba(255,70,88,${a})`); gr.addColorStop(0.55, `rgba(255,70,88,${a * 0.45})`); gr.addColorStop(1, 'rgba(255,70,88,0)');
  g.fillStyle = gr; g.fillRect(cx - r, cy - r, 2 * r, 2 * r);
  g.restore();
}

// ---- Fear in the front room
function fearFrontState(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  if (t < S.T(CUT23)) {
    // the wide picks Fear up mid-dash (it left the alarm wall frame-right a moment ago, toward the console): on the
    // floor just in front of its post, beside the rising CEO, scurrying down-screen toward the console row; it ducks
    // in behind JOY as she hops away and comes up on tiptoe (FEAR_TIPTOE_F depth) in the clear spot she has just
    // vacated for "…out!", flapping its arms at the others, a darting glance up at the Void (up-left of it in this
    // view), then scurries left after them
    const ARRIVE = 's05b01+1.72';
    const y = k([['s05b01+1.3', 1040], ['s05b01+1.58', 1292], [ARRIVE, 1350, 'out']]);
    const x = k([['s05b01+1.3', 776], ['s05b01+1.58', 772], [ARRIVE, 754, 'out'], ['s05b01+2.3', 748], ['s05b02', 664, 'in']]);
    const s = hqScaleAt('front', y) * (0.8 / hqScaleAt('front', 1350));
    const run = t < S.T(ARRIVE) || t > S.T('s05b01+2.32');
    const ph = t * TAU * 4;
    const face = withSpeech({ browIn: 0.5, browUp: 1, lidU: -0.4, pupil: 0.52, open: 0.2, wide: 0.6, smile: -0.5, tremble: 0.7,
      lookX: k([['s05b01+1.3', -0.85], ['s05b01+1.96', -0.85], ['s05b01+2.03', -0.5], ['s05b01+2.17', -0.5], ['s05b01+2.24', -0.85]]),
      lookY: k([['s05b01+1.96', 0.1], ['s05b01+2.03', -0.8], ['s05b01+2.17', -0.8], ['s05b01+2.24', 0.1]]), noAutoBlink: true },
    S.lip('FEAR', t), 1);
    // arms flap high, above the console rim, shooing the others left
    // (palms out toward the others: shooing, not waving the backs of the hands)
    const shoo = (side) => ({ target: [side * 70 + 10 * Math.sin(ph * 0.5 + side), -188 - 30 * Math.sin(ph * 0.5 + side * 1.4)],
      bend: -side, hand: 'open', front: side < 0, palmDir: [0.6, 0, 0.8] });
    // feet: toward the camera on the dash down-screen, along the direction of travel on the scurry left
    const feetTurn = t < S.T(ARRIVE) ? 0.2 : 0.75;
    return { x, y, s, pose: { t, facing: -1, face, tremble: 0.6, lean: 0.06, headTurn: -0.2,
      armL: shoo(-1), armR: shoo(1), walk: run ? { phase: ph } : null, feetTurn, breathRate: 1.5, breathe: 1.3 } };
  }
  // back at the alarm (off-screen during the door shot), clinging → sliding down, hugging itself
  const [fx, fy, fs] = FEAR_ALARM_F;
  const pulled = S.k(t, [['s05b04+0.72', 1], ['s05b04+0.98', 0]]);
  const slide = k([['s05b04+0.25', 0], ['s05b04+1.35', 1, 'inOut']]);
  const open = k([['s05b04+1.0', 0], ['s05b04+1.45', 1]]);
  const SHUT = { browIn: 1, browUp: 0.35, browSquish: 1, lidU: 1, lidL: 0.3, lidTilt: -0.7, smile: -0.7, wide: 0.7, open: 0.12, teeth: 0.7, tremble: 0.9 };
  const VOID = { browIn: 1, browUp: 0.6, browSquish: 0.3, lidU: -0.18, lidL: 0.05, lidTilt: 0.25, pupil: 0.62, smile: -0.4, wide: 0.05, open: 0, tremble: 0.5,
    lookX: -0.62, lookY: -0.76, tears: 0.3 };
  const pant = 0.5 + 0.5 * Math.sin(t * TAU * 1.9);                     // hyperventilating
  const face = { ...(open > 0 ? mixFlat(SHUT, VOID, open) : SHUT), open: open > 0.5 ? 0.02 : 0.14 + 0.16 * pant,
    blink: blinkAt(t, S.T('s05b04+2.6'), 0.2), noAutoBlink: true };
  // As in the panic close: both fists locked on the pulled handle (Fear a small step nearer the station, PANIC_DX).
  // When the bell dies the handle springs up out of its hands (+0.72): the hands come in to the chest, Fear turns
  // from the wall to the room (the facing flip happens inside a quick squash, as in s06/s07, never as a pop), steps
  // back onto its spot (= s06's first frame) and folds its arms around itself while sliding down.
  const rel = k([['s05b04+0.7', 0], ['s05b04+0.86', 1]]);
  const turnK = clamp((t - S.T('s05b04+0.8')) / 0.24);
  const facing = turnK < 0.5 ? 1 : -1;
  const squash = turnK > 0 && turnK < 1 ? 1 - 0.22 * Math.sin(turnK * Math.PI) : 1;
  const hug = k([['s05b04+0.92', 0], ['s05b04+1.32', 1]]);
  const dx = PANIC_DX * (1 - k([['s05b04+0.76', 0], ['s05b04+1.12', 1]]));
  const lean = 0.06 * (1 - rel);
  const hy = ALARM_REACH[1] + 26 * pulled;
  const hR = onHandle(ALARM_REACH[0] + 12, hy, -1.15, lean, dx), hL = onHandle(ALARM_REACH[0] - 14, hy + 1, -1.3, lean, dx);
  const CH = [6, -122];                                              // hands meet at the chest for the turn
  let armR, armL;
  if (facing > 0) {
    armR = { target: [lerp(hR.target[0], CH[0], rel), lerp(hR.target[1], CH[1], rel)], bend: -1, front: true,
      hand: rel > 0.3 ? 'open' : 'grip', handAng: lerp(hR.handAng, -1.9, rel), palmDir: rel > 0.3 ? [0, 0, -1] : undefined };
    armL = { target: [lerp(hL.target[0], -CH[0], rel), lerp(hL.target[1], CH[1], rel)], bend: -1, front: true,
      hand: rel > 0.3 ? 'open' : 'grip', handAng: lerp(hL.handAng, -1.4, rel), palmDir: rel > 0.3 ? [0, 0, -1] : undefined };
  } else {
    // (mirrored: the same screen spots as before the flip) → hugSelf
    const toHug = (side) => {
      const h = FEAR_ARMS.hugSelf(side);
      const c0 = [side * CH[0], CH[1]];
      return { ...h, target: [lerp(c0[0], h.target[0], hug), lerp(c0[1], h.target[1], hug) + 10 * slide * hug] };
    };
    armR = toHug(1); armL = toHug(-1);
  }
  return { x: fx + dx * fs, y: fy, s: fs, squash, pose: { t, facing, face, tremble: lerp(0.95, 0.75, open), crouch: slide, headDY: 8 * slide,
    lean, headTurn: facing < 0 ? -0.2 : 0.1, headTilt: facing < 0 ? -0.06 : 0.04, armR, armL,
    whiten: 0.6 * (1 - rel), breathe: lerp(1.7, 1.2, open),
    // panting slows as the eyes open: the rate is integrated so the breath never re-phases (no flutter)
    breathRate: continuousRate(t, 's05:fearAlarm', (tt) => lerp(1.9, 0.9, S.k(tt, [['s05b04+1.0', 0], ['s05b04+1.45', 1]])),
      [S.T('s05b04'), S.end + 1], S.T('s05b04')) } };
}
function mixFlat(a, b, k) {
  const o = { ...a };
  for (const key in b) o[key] = lerp(typeof a[key] === 'number' ? a[key] : 0, b[key], k);
  return o;
}

// ---- Consciousness in the front room
function ceoFrontState(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  if (t < S.T(CUT23)) {
    // background: finishing the rise beside the alarm; the eyes (then the head) follow Fear's dash down past its
    // right side toward the console (as they followed it off the alarm wall in shot 1), then turn to watch the
    // others go
    const [x, y, s] = CEO_AT_ALARM_F;
    const face = { ...SELF_EXPR.worried, browUp: 0.45, lidU: -0.1, open: 0.08,
      lookX: k([['s05b01+1.3', 0.4], ['s05b01+1.5', 0.3], ['s05b01+1.74', -0.7, 'inOut']]),
      lookY: k([['s05b01+1.3', 0.5], ['s05b01+1.5', 0.72], ['s05b01+1.74', 0.35, 'inOut']]) };
    // the useless "wait" hand sinks once they are all going (it was held up, frozen, to the end of the shot)
    const low = k([['s05b01+2.05', 0], ['s05b01+2.8', 1, 'inOut']]);
    const po = SELF_ARMS.palmOut(1), re = SELF_ARMS.rest(1);
    const armR = low < 0.001 ? { preset: 'palmOut' } : low > 0.999 ? 'rest'
      : { target: [lerp(po.target[0], re.target[0], low), lerp(po.target[1], re.target[1], low)], bend: -1, front: low < 0.6,
          hand: low > 0.55 ? 'rest' : 'palm', handAngle: lerp(po.handAngle, Math.PI / 2 - 0.08, sine(low)),
          ...(low > 0.55 ? {} : { palmDir: po.palmDir }) };
    return { x, y, s, pose: { t, outfit: 'ceo', facing: -1, kneel: k([['s05b01+1.3', 0.4], ['s05b01+2.0', 0, 'inOut']]),
      bodyTurn: -0.25, headTurn: k([['s05b01+1.3', -0.12], ['s05b01+1.56', -0.12], ['s05b01+1.86', -0.45, 'inOut']]),
      face, clipboard: true, armL: 'rest', armR } };
  }
  if (t < S.T(CUT3P)) {
    // crossing to the middle of the room, off-screen during the door shot (its frame ends at x ≈ 414)
    const p = k([[CUT23, 0], [CUT3P, 1]]);
    const x = lerp(640, 540, p), y = lerp(1000, 1060, p);
    return { x, y, s: hqScaleAt('front', y), pose: { t, outfit: 'ceo', facing: -1, clipboard: true, armL: 'rest',
      walk: { phase: t * TAU * 0.8 }, face: SELF_EXPR.worried } };
  }
  const [x, y, s] = CEO_MID;
  // the slow half circle, eyes leading the head, the head leading the body
  // (from the door, screen-left, across the empty console to the alarm side; it starts off-screen during the panic
  // close, so the wide cuts back in on the middle of it)
  const c34 = S.T(SWEEP0);
  const sweep = (lag) => k([[c34 + 0.1 + lag, -1], [c34 + 2.9 + lag, 1, 'sine']]);
  const eyesK = sweep(0), headK = sweep(0.3), bodyK = sweep(0.6);
  const ears = k([['s05b03.end-0.3', 0], ['s05b03.end+0.05', 1, 'out'], ['s05b04+0.98', 1], ['s05b04+1.6', 0, 'inOut']]);
  const shut = k([['s05b03.end-0.3', 0], ['s05b03.end-0.1', 1], ['s05b04+1.2', 1], ['s05b04+1.75', 0]]);
  const sag = k([['s05b04+1.4', 0], ['s05b04+2.2', 1, 'sine']]);
  const stare = k([['s05b04+1.75', 0], ['s05b04+2.3', 1]]);
  const LOST = { ...SELF_EXPR.tired, browIn: 0.65, browUp: 0.15, lidU: 0.22, smile: -0.18 };
  const SQUEEZE = { browIn: 0.85, browUp: -0.1, browSquish: 0.8, lidU: 1, lidL: 0.35, lidTilt: 0.3, smile: -0.35, pressed: 0.65, wide: 0.15 };
  const EMPTY = { browIn: 0.8, browUp: 0.1, browSquish: 0.2, lidU: 0.36, lidL: 0.05, lidTilt: 0.4, smile: -0.28, tears: 0.25 };
  let ex = mixFlat(LOST, EMPTY, stare);
  ex = mixFlat(ex, SQUEEZE, shut);
  const look = { lookX: lerp(lerp(-0.85, 0.8, sine((eyesK + 1) / 2)), -0.08, stare) + fbm(t * 0.5, 41) * 0.04,
    lookY: lerp(0.42, 0.55, stare) + fbm(t * 0.4, 42) * 0.03 };
  const face = { ...ex, ...look };
  const headTurn = lerp(lerp(-0.6, 0.55, (headK + 1) / 2), 0.02, Math.max(ears, stare));
  const bodyTurn = lerp(-0.42, 0.42, (bodyK + 1) / 2) * (1 - 0.7 * Math.max(ears, stare));
  // hands: clipboard hanging → heels of the hands over the ears (the clipboard slips) → lowered, limp
  const hasBoard = t < S.T('s05b03.end-0.34');
  const pose = { t, outfit: 'ceo', facing: 1, bodyTurn, headTurn, face,
    clipboard: hasBoard, headDY: 6 * sag + 2 * shut, headTilt: 0.05 * sag - 0.03 * shut, lean: 0.035 * sag,
    shrug: 0.45 * ears - 0.2 * sag, breathe: lerp(1, 1.8, sag),
    breathRate: continuousRate(t, 's05:ceo', (tt) => lerp(0.24, 0.13, S.k(tt, [['s05b04+1.4', 0], ['s05b04+2.2', 1, 'sine']])),
      [S.start, S.end + 1], S.start) };
  if (ears > 0.01) { pose.armL = earsArm(x, y, s, pose, -1, ears); pose.armR = earsArm(x, y, s, pose, 1, ears); }
  else pose.armL = 'rest';
  return { x, y, s, pose, ears, hasBoard };
}

// Palms over the ears with the elbows down in front of the chest. The elbow AND the wrist follow explicit paths
// (rest → hands up in front of the chest → at the ears), and the bone lengths/bend are derived from them, so the IK
// lands exactly on that elbow every frame: no elbows splaying out (hands-on-hips) and no folded "slab" sleeves on
// the way up or down. Upper arm foreshortened toward the camera (short), forearm upright.
function earsArm(x, y, s, pose, side, e) {
  const A = selfPoseAnchors(x, y, s, pose);
  const sh = selfLocal(x, y, s, 1, ...(side < 0 ? A.shoulderL : A.shoulderR));
  const hc = selfLocal(x, y, s, 1, ...A.headCenter);
  const K = [
    { k: 0, E: [sh[0] + side * 5, sh[1] + 99], W: [sh[0] + side * 12, sh[1] + 184] },
    { k: 0.45, E: [sh[0] + side * 9, sh[1] + 62], W: [sh[0] - side * 4, sh[1] - 8] },
    { k: 1, E: [sh[0] + side * 6, sh[1] + 34], W: [hc[0] + side * 61, hc[1] + 32] },
  ];
  const kk = clamp(e);
  const i = kk < K[1].k ? 0 : 1;
  const u = sine((kk - K[i].k) / (K[i + 1].k - K[i].k));
  const P = (a, b) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u)];
  const E = P(K[i].E, K[i + 1].E), Wr = P(K[i].W, K[i + 1].W);
  const L1 = Math.hypot(E[0] - sh[0], E[1] - sh[1]), L2 = Math.hypot(Wr[0] - E[0], Wr[1] - E[1]);
  const cross = (Wr[0] - sh[0]) * (E[1] - sh[1]) - (Wr[1] - sh[1]) * (E[0] - sh[0]);
  return { target: Wr, bend: cross < 0 ? 1 : -1, reach1: L1 / 100, reach2: L2 / 92, front: kk > 0.12,
    hand: kk > 0.55 ? 'flat' : 'rest', ...(kk > 0.55 ? { handAngle: -Math.PI / 2 - side * 0.1, palmDir: [-side, 0, -0.3] } : { thumb: -side }) };
}

// pages slipping from the clipboard, and the clipboard itself dropping (front-view props)
function drawPages(g, t, S, ceo) {
  const [x, y, s] = CEO_MID;
  const hand = [x - 66 * s, y - 175 * s];
  const floor = y + 6;
  const c34 = S.T(SWEEP0);                         // three pages slip loose during the half circle
  const td = S.T('s05b03.end-0.3');               // ...and as the hands fly to the ears the clipboard spills the rest:
  // [start, dir, seed, sideways spread, fall time, floor offset]  a slow paper flurry under "Causing chaos."
  const pages = [[c34 + 0.35, -1, 0.3, 26, 1.7, 4], [c34 + 1.35, 1, 0.75, 26, 1.7, 7], [c34 + 2.45, -1, 0.5, 26, 1.7, 10],
    [td, 1, 0.15, 64, 1.5, 2], [td + 0.04, -1, 0.62, 52, 1.9, 9], [td + 0.07, 1, 0.41, 96, 2.2, 13],
    [td + 0.1, -1, 0.88, 84, 1.7, 5], [td + 0.14, 1, 0.27, 30, 2.4, 11]];
  for (let i = 0; i < pages.length; i++) {
    const [t0, dir, seed, spread, dur, fo] = pages[i];
    if (t < t0) continue;
    const p = clamp((t - t0) / dur);
    const fx = hand[0] + dir * (18 + spread * p) + Math.sin(p * 7 + seed * 5) * 9 * (1 - p);
    const fy = lerp(hand[1] + 4, floor + fo, p * p * (3 - 2 * p));
    const flat = p < 1 ? 0.55 + 0.45 * Math.abs(Math.cos(p * 6 + seed)) : 0.32;
    g.save();
    g.translate(fx, fy);
    g.rotate((dir * 0.5 + Math.sin(p * 5 + seed * 3) * 0.6) * (1 - p) + dir * 0.25 * p);
    g.scale(1, flat);
    g.fillStyle = '#efe6d2'; g.strokeStyle = 'rgba(60,40,40,0.7)'; g.lineWidth = 0.9;
    g.fillRect(-7, -9, 14, 18); g.strokeRect(-7, -9, 14, 18);
    g.strokeStyle = 'rgba(80,80,110,0.55)';
    for (let l = -5; l <= 5; l += 3.3) { g.beginPath(); g.moveTo(-4.5, l); g.lineTo(4.5, l); g.stroke(); }
    g.restore();
  }
  // the clipboard slips from the left hand as both hands go to the ears
  const t0 = S.T('s05b03.end-0.34');
  if (t >= t0 && ceo) {
    const p = clamp((t - t0) / 0.32);
    const bx = lerp(hand[0] - 4, x - 40 * s, p), by = lerp(hand[1] + 12, floor + 2, p * p);
    g.save();
    g.translate(bx, by);
    g.rotate(lerp(0.1, -0.5, p));
    g.scale(s * 0.92, s * 0.92 * lerp(1, 0.36, p));
    drawClipboard(g);
    g.restore();
  }
}

// ---- live pieces over a cached front set -------------------------------------------------------------------------
// The front set is ~11–19 ms per frame (more at the door's zoom); everything in it is static in these shots except
// the EXIT door (it swings) and the alarm station (bell + beacon animate). The set is painted once per shot with the
// door shut and the station idle, and those two are painted live on top, exactly as drawHQ composes them:
// part → room dim (rgba(6,5,14,.62·lightsDim)) → for an open door: floor glow + the undimmed door again.
// Wall transforms replicate hq.mjs wallXform(G.front, side, lam, yup, cheat) (GEO.front: vx 450, vy 520, eye 320,
// hw 232, f 900); the door painter is a copy of hq.mjs drawExitDoor (not exported).
function frontWallXf(side, lam, yup, cheat) {
  const ox = 450 + lam * side * 232, oy = 520 + lam * (320 - yup), k = (lam * lam) / 900;
  return [lerp(232 * k, lam, cheat), lerp(side * (320 - yup) * k, 0, cheat), 0, lam, ox, oy];
}
const DOOR_XF = frontWallXf(-1, 1.3, 0, 0.12);
const ALARM_XF = frontWallXf(1, 1.42, 180 * 0.296, 0.5);
const HQ_LINE = HQ_COLORS.line;
function doorPath(g, pad = 0) {
  const W2 = 62, Hs = 150;
  g.beginPath();
  g.moveTo(-W2 - pad, 0); g.lineTo(-W2 - pad, -Hs); g.arc(0, -Hs, W2 + pad, Math.PI, 0); g.lineTo(W2 + pad, 0);
  g.closePath();
}
function paintExitDoor(g, open) {
  const W2 = 62, Hs = 150, R = 62;
  const lin = (x0, y0, x1, y1, stops) => { const gr = g.createLinearGradient(x0, y0, x1, y1); for (const [k, c] of stops) gr.addColorStop(k, c); return gr; };
  doorPath(g, 14); g.fillStyle = '#41377a'; g.fill(); g.strokeStyle = HQ_LINE; g.lineWidth = 3; g.stroke();
  doorPath(g, 14); g.save(); g.clip();
  g.strokeStyle = 'rgba(170,150,240,0.3)'; g.lineWidth = 3; doorPath(g, 10); g.stroke();
  g.restore();
  doorPath(g, 0); g.save(); g.clip();
  g.fillStyle = lin(0, -Hs - R, 0, 0, [[0, '#fff3d6'], [1, '#ffd9a0']]);
  g.fillRect(-W2 - 2, -Hs - R - 2, W2 * 2 + 4, Hs + R + 4);
  const ang = open * 1.35, lw = W2 * 2 * Math.cos(ang);
  if (lw > 1) {
    g.save();
    g.translate(-W2, 0); g.scale(lw / (W2 * 2), 1); g.translate(W2, 0);
    doorPath(g, 0);
    const sh = open * 0.5;
    g.fillStyle = lin(-W2, 0, W2, 0, [[0, shade('#5a4290', -sh)], [1, shade('#463370', -sh)]]);
    g.fill(); g.strokeStyle = HQ_LINE; g.lineWidth = 2.5; g.stroke();
    g.strokeStyle = 'rgba(15,10,30,0.5)'; g.lineWidth = 2.5;
    g.beginPath(); g.moveTo(0, -Hs - R + 4); g.lineTo(0, 0); g.stroke();
    for (const sx of [-1, 1]) { roundRect(g, sx * 31 - 20, -Hs + 6, 40, 70, 10); g.stroke(); roundRect(g, sx * 31 - 20, -64, 40, 50, 10); g.stroke(); }
    g.fillStyle = '#ffe6b0'; circle(g, 0, -Hs - 12, 18); g.fill();
    g.strokeStyle = '#2b2255'; g.lineWidth = 4; g.stroke();
    g.fillStyle = '#e8c25a'; circle(g, W2 - 14, -80, 6); g.fill();
    g.strokeStyle = HQ_LINE; g.lineWidth = 1.5; g.stroke();
    g.restore();
  }
  g.restore();
}
function drawDoorLive(g, st) {
  const open = clamp(st.doorOpen || 0), dim = 0.62 * (st.lightsDim || 0);
  g.save(); g.transform(...DOOR_XF);
  paintExitDoor(g, open);
  if (dim > 0) { doorPath(g, 16); g.clip(); g.fillStyle = `rgba(6,5,14,${dim})`; g.fillRect(-90, -300, 180, 320); }
  g.restore();
  if (open > 0) {
    g.save(); g.globalCompositeOperation = 'lighter';
    g.translate(DOOR_XF[4] + 70, DOOR_XF[5] + 10); g.scale(1, 40 / 160);
    const a = 0.25 * open, gr = g.createRadialGradient(0, 0, 0, 0, 0, 160);
    gr.addColorStop(0, `rgba(255,226,168,${a})`); gr.addColorStop(0.5, `rgba(255,226,168,${a * 0.5})`); gr.addColorStop(1, 'rgba(255,226,168,0)');
    g.fillStyle = gr; g.fillRect(-160, -160, 320, 320);
    g.restore();
    if (dim > 0.006) { g.save(); g.globalAlpha = clamp(open * 1.5); g.transform(...DOOR_XF); paintExitDoor(g, open); g.restore(); }
  }
}
// the station is dimmed like the room around it: painted in a small offscreen, darkened with source-atop, blitted
let stCan = null, stCtx = null;
function drawStationLive(g, st) {
  const m = g.getTransform();
  const corners = [[742, 722], [818, 722], [742, 952], [818, 952]].map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]);
  const x0 = Math.floor(Math.min(...corners.map((c) => c[0]))) - 2, y0 = Math.floor(Math.min(...corners.map((c) => c[1]))) - 2;
  const x1 = Math.ceil(Math.max(...corners.map((c) => c[0]))) + 2, y1 = Math.ceil(Math.max(...corners.map((c) => c[1]))) + 2;
  if (x1 <= 0 || y1 <= 0 || x0 >= W || y0 >= H) return;
  const bw = x1 - x0, bh = y1 - y0;
  if (!stCan || stCan.width < bw || stCan.height < bh) { stCan = createCanvas(Math.max(bw, 160), Math.max(bh, 400)); stCtx = stCan.getContext('2d'); }
  const c = stCtx;
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'source-over'; c.clearRect(0, 0, stCan.width, stCan.height);
  c.setTransform(m.a, m.b, m.c, m.d, m.e - x0, m.f - y0);
  c.transform(...ALARM_XF);
  drawAlarmStation(c, 0, 0, 0.296, st);
  c.setTransform(1, 0, 0, 1, 0, 0);
  const dim = 0.62 * (st.lightsDim || 0);
  if (dim > 0) { c.globalCompositeOperation = 'source-atop'; c.fillStyle = `rgba(6,5,14,${dim})`; c.fillRect(0, 0, bw, bh); c.globalCompositeOperation = 'source-over'; }
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(stCan, 0, 0, bw, bh, x0, y0, bw, bh);
  g.restore();
}

// Shots 2 and 3: the set (door shut, station idle), the Void (idle 0) and the empty cage are painted once per shot, in
// world space, from fixed parameters (deterministic), and laid back under the live camera (drift + a small push in,
// both inside the cached margin); the door and the station are then drawn live on top (above).
const SET_M = 40;
const setCache = new Map();
function cachedSet(key, cam, st) {
  let e = setCache.get(key);
  if (!e) {
    const c = createCanvas(W + 2 * SET_M, H + 2 * SET_M);
    const b = c.getContext('2d');
    b.translate(SET_M, SET_M);
    applyCamera(b, cam);
    drawHQ(b, 'front', st);
    drawVoid(b, ...VOID_F, { t: st.t, ...STARE_F, idle: 0, shadow: false });
    drawCage(b, ...CAGE_F, { t: st.t, door: 1, locked: 0 });
    e = { c, x: cam.x - (W / 2 + SET_M) / cam.zoom, y: cam.y - (H / 2 + SET_M) / cam.zoom,
      w: (W + 2 * SET_M) / cam.zoom, h: (H + 2 * SET_M) / cam.zoom };
    setCache.set(key, e);
  }
  return e;
}

// fx/rim.mjs drawLit, done on a canvas the size of the character's box instead of the whole frame (drawLit's four
// full-frame layers cost ~22 ms per character; the door shot lights up to four of them). Same light model: a soft
// fill where the character is, and a rim of the source's colour on the silhouette edge that faces it.
//   box = world rect [x0, y0, x1, y1] that holds the character (in g's current transform)
let litC = null;
function drawLitBox(g, drawFn, box, o) {
  const m = g.getTransform();
  const cs = [[box[0], box[1]], [box[2], box[1]], [box[0], box[3]], [box[2], box[3]]].map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]);
  const x0 = Math.max(0, Math.floor(Math.min(...cs.map((c) => c[0]))) - 8), y0 = Math.max(0, Math.floor(Math.min(...cs.map((c) => c[1]))) - 8);
  const x1 = Math.min(W, Math.ceil(Math.max(...cs.map((c) => c[0]))) + 8), y1 = Math.min(H, Math.ceil(Math.max(...cs.map((c) => c[1]))) + 8);
  const bw = x1 - x0, bh = y1 - y0;
  if (bw <= 0 || bh <= 0) return;
  if (!litC || litC[0].width < bw || litC[0].height < bh) {
    const cw = Math.max(bw, litC ? litC[0].width : 0), ch = Math.max(bh, litC ? litC[0].height : 0);
    litC = [createCanvas(cw, ch), createCanvas(cw, ch), createCanvas(cw, ch)];
    if (globalThis.__FACE_CANVASES) globalThis.__FACE_CANVASES.add(litC[0]);   // faces on it count for caption placement
  }
  const [L, T, U] = litC, gl = L.getContext('2d'), gt = T.getContext('2d'), gu = U.getContext('2d');
  for (const c of [gl, gt, gu]) { c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.clearRect(0, 0, bw + 2, bh + 2); }
  gl.setTransform(m.a, m.b, m.c, m.d, m.e - x0, m.f - y0);
  // (faces drawn here are logged for caption placement in box coordinates: move them back to the frame)
  const log = globalThis.__FACE_LOG, n0 = log ? log.length : 0;
  gl.save(); drawFn(gl); gl.restore();
  if (log) for (let i = n0; i < log.length; i++) { const f = log[i]; f.x0 += x0; f.x1 += x0; f.y0 += y0; f.y1 += y0; }
  gl.setTransform(1, 0, 0, 1, 0, 0);
  if (o.fillAlpha > 0) {
    gl.globalCompositeOperation = 'source-atop'; gl.fillStyle = rgbaHex(o.fill, o.fillAlpha); gl.fillRect(0, 0, bw, bh);
    gl.globalCompositeOperation = 'source-over';
  }
  const dl = Math.hypot(o.dir[0], o.dir[1]) || 1, ux = o.dir[0] / dl, uy = o.dir[1] / dl, w = o.width ?? 3.5;
  gt.drawImage(L, 0, 0); gt.globalCompositeOperation = 'destination-out'; gt.drawImage(L, -ux * w, -uy * w);
  gu.drawImage(L, 0, 0); gu.globalCompositeOperation = 'destination-out'; gu.drawImage(L, -ux * w * 2.6, -uy * w * 2.6);
  gu.globalCompositeOperation = 'source-in'; gu.fillStyle = rgbaHex(o.color, 0.3); gu.fillRect(0, 0, bw, bh);
  gt.globalCompositeOperation = 'source-in'; gt.fillStyle = rgbaHex(o.color, 1); gt.fillRect(0, 0, bw, bh);
  gt.globalCompositeOperation = 'source-over'; gt.drawImage(U, 0, 0);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(L, 0, 0, bw, bh, x0, y0, bw, bh);
  g.globalCompositeOperation = 'screen'; g.globalAlpha *= o.strength;
  g.drawImage(T, 0, 0, bw, bh, x0, y0, bw, bh);
  g.restore();
}
const rgbaHex = (hex, a) => `rgba(${parseInt(hex.slice(1, 3), 16)},${parseInt(hex.slice(3, 5), 16)},${parseInt(hex.slice(5, 7), 16)},${a})`;

function renderFront(g, t, S, cam, drawCam, cacheKey) {
  const shot = shotOf(t, S);
  const st = setState(t, S);
  g.save();
  applyCamera(g, drawCam);
  if (cacheKey) {
    // the door is baked in while it is fully shut or fully open; only the swing itself is painted live
    const swing = st.doorOpen > 0.001 && st.doorOpen < 0.999;
    const held = swing ? 0 : Math.round(st.doorOpen);
    // 'end' = the held last camera (dissolve into s06): baked at scene.end itself, so the Void's shimmer does not
    // jump when the live drawing hands over to the cache
    const at = S.T(cacheKey === 'door' ? CUT23 : cacheKey === 'end' ? 'scene.end' : CUT12);
    const e = cachedSet(`${cacheKey}:${held}`, cam, { ...setState(at, S), t: cacheKey === 'end' ? at : 69, doorOpen: held, alarm: 0 });
    g.drawImage(e.c, e.x, e.y, e.w, e.h);
    if (swing) drawDoorLive(g, st);
    if (cacheKey !== 'door') drawStationLive(g, st);   // off-frame in the door shot
  } else {
    drawHQ(g, 'front', st);
    drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0, shadow: false });
    drawCage(g, ...CAGE_F, { t, door: 1, locked: 0 });
  }
  const items = [];
  // the door shot (x ≈ 60…400) never sees the CEO (crossing at x ≥ 540) nor Fear (at the alarm, x 734): skip them
  const ceo = shot === 3 ? null : ceoFrontState(t, S);
  if (ceo) items.push({ y: ceo.y, draw: () => { drawSelf(g, ceo.x, ceo.y, ceo.s, ceo.pose); } });
  if (shot === 5) items.push({ y: CEO_MID[1] + 8, draw: () => drawPages(g, t, S, ceo) });
  const fear = shot === 3 ? null : fearFrontState(t, S);
  if (fear) items.push({ y: fear.y, draw: () => {
    g.save();
    if (fear.squash && fear.squash !== 1) { g.translate(fear.x, 0); g.scale(fear.squash, 1); g.translate(-fear.x, 0); }
    drawFear(g, fear.x, fear.y, fear.s, fear.pose);
    g.restore();
  } });
  for (const name of ['CALM', 'ANGER', 'SADNESS', 'JOY']) {
    const e = emotionState(name, t, S, shot);
    if (e.alpha <= 0.01) continue;
    if (e.door && e.x < 76) continue;              // fully behind the near jamb (x 115) now: nothing to draw
    // walking out: hidden by the near jamb once past the wall plane (clip only when near the doorway, x < 230)
    const clip = e.door && e.x < 230;
    // the open EXIT door is the brightest thing in the room: whoever stands in front of / beside the doorway gets a
    // warm rim on the edges toward it and a touch of warm fill (strength by distance from the opening)
    const lit = shot === 3 ? clamp((268 - e.x) / 110) * clamp(st.doorOpen * 1.5) : 0;
    items.push({ y: e.y + (name === 'JOY' ? 0.5 : 0), draw: () => {
      if (clip) { g.save(); clipDoor(g); }
      if (lit > 0.02) {
        drawLitBox(g, (g2) => drawEmotion(g2, name, e.x, e.y, e.s, e.pose), [e.x - 150 * e.s, e.y - 560 * e.s, e.x + 150 * e.s, e.y + 30 * e.s],
          { dir: [-1, -0.25], color: '#ffe2a8', strength: 0.75 * lit, width: 3.2, fill: '#ffd9a0', fillAlpha: 0.07 * lit });
      } else drawEmotion(g, name, e.x, e.y, e.s, e.pose);
      if (e.pose.redCheek) drawRedCheek(g, e, t, st.alarm);
      if (clip) g.restore();
    } });
  }
  items.sort((a, b) => a.y - b.y);
  for (const it of items) it.draw();
  if (shot !== 3) drawHQForeground(g, 'front', st);   // the console is below the door shot's frame (measured: 0 px)
  drawAlarmLight(g, 'front', st);
  g.restore();
}

// ================================================================ render
export function render(g, t, S) {
  const shot = shotOf(t, S);
  if (shot === 1) renderAlarm(g, t, S);
  else if (shot === 2) {
    const cam = lerpCam(CAM.console, CAM.console2, sine((t - S.T(CUT12)) / (S.T(CUT23) - S.T(CUT12))));
    renderFront(g, t, S, CAM.console, liveCam(cam, t, 2.5), 'wide');
  } else if (shot === 3) {
    const cam = lerpCam(CAM.door, CAM.door2, sine((t - S.T(CUT23)) / (S.T(CUT3P) - S.T(CUT23))));
    renderFront(g, t, S, CAM.door, liveCam(cam, t, 2.5), 'door');
  } else if (shot === 4) {
    renderPanic(g, t, S);
  } else {
    // one slow push from the establishing wide to s06's first camera (log zoom, ≤ ~55 px/s on screen), then held
    // through the dissolve; the drift is s06's own (drift(t, 2, seed 6) as a screen shake) so the two layers of the
    // dissolve stay in register
    const u = sine((t - S.T(CUTPW)) / (S.T('scene.end') - S.T(CUTPW)));
    const cam = { x: lerp(CAM.est.x, CAM.end.x, u), y: lerp(CAM.est.y, CAM.end.y, u),
      zoom: Math.exp(lerp(Math.log(CAM.est.zoom), Math.log(CAM.end.zoom), u)) };
    const d = drift(t, 2, 6);
    // once the camera holds (the dissolve), the static set is painted once and reused: the dissolve frames draw
    // both scenes, and the live front set is the most expensive part of each (~17 ms)
    const held = t >= S.T('scene.end');
    renderFront(g, t, S, held ? CAM.end : cam, { ...cam, shakeX: d.dx, shakeY: d.dy, rot: d.dr * 0.5 }, held ? 'end' : undefined);
  }
  grade(g, COLD, 0);
  vignette(g, VIGNETTE);
}
