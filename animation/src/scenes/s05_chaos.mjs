// s05 · chaos — Fear's panic as a pattern: the alarm, every emotion herded out, and Consciousness left alone
// in the noise with the one presence nobody can evacuate.
//
//   1  scene.start   → s05b01+1.3   `alarm` medium: Fear lunges, yanks the handle, darts a look at the back of the
//                                    room and scurries off right; the CEO (still kneeling, as s04 ended) reaches out
//                                    too late, a silent "wait", starts to rise
//   2  s05b01+1.3    → s05b02       `front` console: Fear on tiptoe behind the row shooing; JOY pops and windmills,
//                                    ANGER throws his hands up and stomps off, SADNESS slides off slowly, CALM rises
//                                    and goes to her; the CEO in the background finishes rising
//   3  s05b02        → s05b03       `front` door: CALM guiding SADNESS out, ANGER's glance back, JOY last ("We always
//                                    come back."), the door swings shut behind her
//   4  s05b03        → s05b04       `front` establishing: the empty console, the CEO alone turning a slow half circle,
//                                    pages slipping from the clipboard; Fear clinging to the handle, eyes shut
//   5  s05b04        → end (+0.9)   slow push: hands over the ears, the clipboard drops, the bell dies, hands lower,
//                                    shoulders sag; Fear slides down the wall and hugs itself, eyes on the Void

import { createCanvas } from '@napi-rs/canvas';
import { W, H, TAU, clamp, lerp, fbm, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { withSpeech } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, drawClipboard } from '../chars/self.mjs';
import { drawEmotion, EMOTION_EXPR, PANIC_FACE } from '../chars/emotions.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, HQ_VIEWS, hqScaleAt, ALARM_REACH } from '../sets/hq.mjs';
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
  { at: 's05b01+1.47', name: 'door_whoosh', gain: -15 },                 // the EXIT door swings open
  { at: 's05b01+1.65', name: 'footsteps', gain: -15, rate: 1.25 },        // ANGER stomping
  { at: 's05b02-0.45', name: 'crowd_murmur', gain: -21 },
  { at: 's05b02+0.05', name: 'footsteps', gain: -17 },
  { at: 's05b02.end-0.1', name: 'door_whoosh', gain: -17, rate: 0.92 },  // swings shut (thud ≈ +1.0 in the file)
  // alone: the turn, the pages, the clipboard dropped as the hands go to the ears
  { at: 's05b03+0.5', name: 'cloth_rustle', gain: -20, rate: 0.85 },
  { at: 's05b03+0.85', name: 'paper_rustle', gain: -17 },
  { at: 's05b03+1.55', name: 'paper_rustle', gain: -20, rate: 1.1 },
  { at: 's05b03+2.75', name: 'paper_rustle', gain: -19, rate: 1.1 },
  { at: 's05b03.end-0.42', name: 'cloth_rustle', gain: -17 },
  { at: 's05b03.end-0.52', name: 'paper_rustle', gain: -14 },            // the clipboard lands (swish peak 0.5 s in)
  // the long shaky exhale as the hands come down (exhale ≈ 1.45 s into the file)
  { at: 's05b04+0.3', name: 'breath_shaky', gain: -15 },
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
  door: { x: 214, y: 850, zoom: 1.8 },
  door2: { x: 206, y: 846, zoom: 1.84 },
  est: { x: 450, y: 812, zoom: 0.96 },             // the staged 'establish' wide, a touch tighter so the CEO reads
  est2: { x: 456, y: 824, zoom: 1.03 },
  end: { x: 500, y: 860, zoom: 1.3 },
  after: { x: 503, y: 864, zoom: 1.33 },          // the move keeps breathing through the dissolve into s06
};
// cuts (one source of truth for every track, so no blocking can leak across a cut)
const CUT12 = 's05b01+1.3';     // alarm wall → the evacuation wide
const CUT23 = 's05b02';         // → the EXIT door
const CUT34 = 's05b03+0.95';    // → the empty room: after JOY is through and the door has shut (staged at s05b03, which
                                //    cut away while JOY was still fading and the door still open), on "forcing…"
function shotOf(t, S) {
  if (t < S.T(CUT12)) return 1;
  if (t < S.T(CUT23)) return 2;
  if (t < S.T(CUT34)) return 3;
  return 4;
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
  const run = k([['s05b01+0.6', 0], ['s05b01+1.32', 1, 'in']]);
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
  const armR = holding > 0.5
    ? { target: [lerp(70, ALARM_REACH[0], reach), lerp(-150, ty, reach)], bend: 1, hand: 'grip', front: true }
    : { target: [62 + 20 * Math.sin(t * TAU * 4.2), -150 - 30 * Math.sin(t * TAU * 4.2)], bend: 1, hand: 'open', front: true };
  const armL = holding > 0.5
    ? { target: [-20 + 30 * pulled, -150 + 40 * pulled], bend: -1, hand: 'fist', front: true }     // fist pumping down with the yank
    : { target: [-60 - 18 * Math.sin(t * TAU * 4.2 + 1.6), -160 + 34 * Math.sin(t * TAU * 4.2 + 1.6)], bend: 1, hand: 'open' };
  const yank = k([['s05b01+0.25', 0], ['s05b01+0.42', 1], ['s05b01+0.62', 0.2]]);
  return {
    x, y: AFY, s: AFS,
    pose: { t, facing: 1, face, tremble: 0.7, crouch: 0.08 + 0.4 * yank, lean: 0.12 - 0.2 * yank + 0.1 * run,
      headTurn: lerp(0.15, 0.3, run) - 0.45 * k([['s05b01+0.46', 0], ['s05b01+0.52', 1], ['s05b01+0.66', 1], ['s05b01+0.74', 0]]),
      headTilt: -0.08 * yank, armL, armR, walk: run > 0 ? { phase: t * TAU * 4.2 } : null, breathRate: 1.4, breathe: 1.4 },
  };
}

function ceoAlarmPose(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  const HOOD = { lookX: -0.72, lookY: -0.86 }, FEAR = { lookX: 0.62, lookY: 0.3 }, RUN = { lookX: 0.92, lookY: 0.12 };
  const gaze = k([['scene.start', HOOD], ['s05b01+0.02', HOOD], ['s05b01+0.12', FEAR, 'out'], ['s05b01+0.66', FEAR], ['s05b01+0.82', RUN]]);
  const startle = k([['s05b01+0.02', 0], ['s05b01+0.14', 1, 'out'], ['s05b01+0.7', 0.6]]);
  const KNIT = { browIn: 0.55, browUp: -0.05, browSquish: 0.7, lidTilt: 0.28, lidU: 0.2, lidL: 0.1, smile: -0.22, pressed: 0.8, tears: 0.2 };
  const ALARM = { browIn: 0.6, browUp: 0.75, browSquish: 0.2, lidTilt: 0.1, lidU: -0.22, lidL: 0, smile: -0.25, pressed: 0, open: 0.12, tears: 0.15 };
  const ex = k([['scene.start', KNIT], ['s05b01+0.02', KNIT], ['s05b01+0.16', ALARM, 'out']]);
  // a silent "wait": w (round) → ay (open) → closing
  const wO = k([['s05b01+0.84', 0], ['s05b01+0.94', 0.16], ['s05b01+1.04', 0.34], ['s05b01+1.2', 0.12]]);
  const wR = k([['s05b01+0.84', 0], ['s05b01+0.94', 0.7], ['s05b01+1.04', 0.1], ['s05b01+1.2', 0]]);
  const face = { ...ex, ...gaze, open: (ex.open || 0) + wO, round: wR, blink: blinkAt(t, S.T('s05b01+0.3'), 0.14) };
  // the reach goes after Fear's back at its shoulder height (world ≈ (590, 1075)), fingers open, a beat too late —
  // it used to rise above Fear's head with the palm up, which read as hailing a cab
  const reachK = k([['s05b01+0.8', 0], ['s05b01+1.08', 1, 'out']]);
  const KNEE = [58, -150], AFTER = [218, -212];
  const armR = reachK > 0.02
    ? { target: [lerp(KNEE[0], AFTER[0], reachK), lerp(KNEE[1], AFTER[1], reachK)], bend: -1, front: true,
        hand: 'open', handAngle: lerp(0.5, -0.12, reachK), thumb: -1 }
    : { target: KNEE, bend: -1, front: true, hand: 'drape', palm: true, wrist: 0.75, thumb: -1 };
  return { t, outfit: 'ceo', facing: 1, kneel: k([['s05b01+0.9', 1], ['s05b01+1.3', 0.4]]),
    headTurn: k([['scene.start', 0.04], ['s05b01+0.06', 0.04], ['s05b01+0.3', 0.38, 'out']]),
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

// ================================================================ the FRONT room (shots 2–5)
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
      x = k([['s05b01+1.32', sx0], ['s05b01+1.62', 640, 'out'], ['s05b01+2.18', 634], ['s05b02', 512, 'in']]); y = sy0 + 10;
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
      x = k([['s05b01+1.45', sx0 - 8], ['s05b02', 418, 'inOut']]); y = sy0 - 4;
      face = { ...EMOTION_EXPR.SADNESS, smile: -0.7, wide: -0.15, lookY: 0.75, lookX: -0.2, tears: 0.3 };
      pose = { facing: -1, headDY: 14 * slide, crouch: 0.15 * slide, headTilt: -0.05,
        walk: t > S.T('s05b01+1.5') ? walkPh(0.75) : null, armL: 'rest', armR: 'rest' };
    } else if (name === 'ANGER') {
      // both hands thrown up, brows in a hard V, a hop off the stool, then stomping out toward the door (frame left)
      const up = k([['s05b01+1.3', 0.7], ['s05b01+1.42', 1], ['s05b01+1.78', 1], ['s05b01+1.96', 0]]);
      const hop = k([['s05b01+1.62', 0], ['s05b01+1.76', 1, 'out'], ['s05b01+1.92', 0, 'in']]);
      x = k([['s05b01+1.92', sx0], ['s05b02', 70, 'in']]); y = sy0 + 6;
      face = { ...EMOTION_EXPR.ANGER, browIn: -1, browSquish: 0.85, pressed: 0.85, smile: -0.6, lidTilt: -0.45,
        lookX: k([['s05b01+1.9', 0.5], ['s05b01+2.05', -0.4]]), lookY: 0.1 };
      const raised = (side) => ({ target: [side * 92, -300], bend: -side, hand: 'palm' });
      pose = { facing: -1, heat: 0.9, headDY: -16 * hop, lean: -0.04 * up,
        armL: up > 0.5 ? raised(-1) : { preset: 'rest', hand: 'fist' }, armR: up > 0.5 ? raised(1) : { preset: 'rest', hand: 'fist' },
        walk: t > S.T('s05b01+1.95') ? walkPh(1.7) : null };
    } else { // CALM
      // rises in one smooth motion, lids level at half, and steps up toward SADNESS with an open palm
      const rise = k([['s05b01+1.3', 0.45], ['s05b01+1.95', 1, 'sine']]);
      const p = path(t, S, [['s05b01+2.0', [sx0, sy0 - 10]], ['s05b02', [214, sy0 - 34], 'inOut']]);
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
    // waits behind ANGER looking back over its shoulder, lower lip out, a tiny wave at the empty room; goes
    p = path(t, S, [['s05b02', [208, 946]], ['s05b02+0.55', [192, 943]], ['s05b02+0.62', [192, 943]],
      ['s05b02+0.86', DOOR_IN, 'inOut'], ['s05b02+1.16', DOOR_OUT, 'in']]);
    walking = moving(t, S, [['s05b02-0.1', 's05b02+0.55'], ['s05b02+0.62', 's05b02+1.2']]);
    const back = k([['s05b02+0.7', 1], ['s05b02+0.82', 0]]);
    face = { ...EMOTION_EXPR.SADNESS, smile: -0.72, wide: -0.15, lookX: lerp(-0.3, 0.85, back), lookY: 0.12, tears: 0.35 };
    pose = { facing: -1, headTurn: lerp(-0.2, 0.55, back), headTilt: 0.05, armR: 'rest',
      armL: t > S.T('s05b02+0.12') && t < S.T('s05b02+0.66') ? { preset: 'wave', dy: 34, dx: -6 } : 'rest' };
  } else if (name === 'CALM') {
    // the only unhurried body in the room: a hand at SADNESS's elbow, the other palm open toward the door; follows
    p = path(t, S, [['s05b02', [250, 956]], ['s05b02+0.6', [236, 952]], ['s05b02+0.9', [212, 946], 'inOut'],
      ['s05b02+1.14', DOOR_IN], ['s05b02+1.42', DOOR_OUT, 'in']]);
    walking = moving(t, S, [['s05b02-0.1', 's05b02+1.45']]);
    face = { smile: 0.18, lidU: 0.45, lidL: 0.12, lidTilt: 0, browIn: 0.1, lookX: -0.45, lookY: 0.15 };
    const s0 = hqScaleAt('front', p.y);
    const sad = emotionState('SADNESS', t, S, 3);
    const guide = k([['s05b02+0.62', 1], ['s05b02+0.78', 0]]);
    const elbow = [(p.x - (sad.x + 46 * sad.s)) / s0, (sad.y - 150 * sad.s - p.y) / s0];   // facing -1: local +x = screen-left
    pose = { facing: -1, headTurn: -0.15,
      armR: guide > 0.5 ? { target: elbow, bend: 1, hand: 'open' } : 'rest',
      armL: { target: [lerp(30, 74, guide), lerp(-150, -250, guide)], bend: -1, hand: 'palm', layer: 'front' } };
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
    pose = { facing: -1, headTurn: lerp(0.55, -0.25, turn), headTilt: 0.06 * (1 - turn), armL: 'rest', armR: 'rest', redCheek: 1 };
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
  const cx = hx + 62 * s, cy = hy + 18 * s, r = 74 * s;
  const gr = g.createRadialGradient(cx, cy, 0, cx, cy, r);
  const a = A * (0.3 + 0.24 * pulse(t));
  gr.addColorStop(0, `rgba(255,70,88,${a})`); gr.addColorStop(0.55, `rgba(255,70,88,${a * 0.45})`); gr.addColorStop(1, 'rgba(255,70,88,0)');
  g.fillStyle = gr; g.fillRect(cx - r, cy - r, 2 * r, 2 * r);
  g.restore();
}

// ---- Fear in the front room
function fearFrontState(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  if (t < S.T('s05b02')) {
    // on tiptoe behind the console row, scurrying right → left, shooing (FEAR_TIPTOE_F depth)
    const x = k([['s05b01+1.3', 792], ['s05b01+1.62', 600, 'out'], ['s05b01+2.3', 596], ['s05b02', 530, 'in']]);
    const run = t < S.T('s05b01+1.62') || t > S.T('s05b01+2.3');
    const ph = t * TAU * 4;
    const face = withSpeech({ browIn: 0.5, browUp: 1, lidU: -0.4, pupil: 0.52, open: 0.2, wide: 0.6, smile: -0.5, tremble: 0.7,
      lookX: k([['s05b01+1.3', -0.85], ['s05b01+1.9', -0.85], ['s05b01+2.0', -0.6], ['s05b01+2.35', -0.6], ['s05b01+2.45', 0.3]]),
      lookY: k([['s05b01+1.9', 0.1], ['s05b01+2.0', -0.5], ['s05b01+2.35', -0.5], ['s05b01+2.45', 0.1]]), noAutoBlink: true }, S.lip('FEAR', t), 1);
    const shoo = (side) => ({ target: [side * 66 + 10 * Math.sin(ph * 0.5 + side), -150 - 34 * Math.sin(ph * 0.5 + side * 1.4)], bend: side, hand: 'open', front: side < 0 });
    return { x, y: 1350, s: 0.8, pose: { t, facing: -1, face, tremble: 0.6, lean: 0.06, headTurn: -0.2,
      armL: shoo(-1), armR: shoo(1), walk: run ? { phase: ph } : null, breathRate: 1.5, breathe: 1.3 } };
  }
  // back at the alarm (off-screen during the door shot), clinging → sliding down, hugging itself
  const [fx, fy, fs] = FEAR_ALARM_F;
  const pulled = S.k(t, [['s05b04+0.72', 1], ['s05b04+0.98', 0]]);
  const slide = k([['s05b04+0.25', 0], ['s05b04+1.35', 1, 'inOut']]);
  const letGo = t > S.T('s05b04+0.8');
  const hug = k([['s05b04+0.8', 0], ['s05b04+1.3', 1]]);
  const open = k([['s05b04+1.0', 0], ['s05b04+1.45', 1]]);
  const SHUT = { browIn: 1, browUp: 0.35, browSquish: 1, lidU: 1, lidL: 0.3, lidTilt: -0.7, smile: -0.7, wide: 0.7, open: 0.12, teeth: 0.7, tremble: 0.9 };
  const VOID = { browIn: 1, browUp: 0.6, browSquish: 0.3, lidU: -0.18, lidL: 0.05, lidTilt: 0.25, pupil: 0.62, smile: -0.4, wide: 0.05, open: 0, tremble: 0.5,
    lookX: -0.62, lookY: -0.76, tears: 0.3 };
  const pant = 0.5 + 0.5 * Math.sin(t * TAU * 1.9);                     // hyperventilating
  const face = { ...(open > 0 ? mixFlat(SHUT, VOID, open) : SHUT), open: open > 0.5 ? 0.02 : 0.14 + 0.16 * pant,
    blink: blinkAt(t, S.T('s05b04+2.6'), 0.2), noAutoBlink: true };
  const grip = { target: [ALARM_REACH[0], ALARM_REACH[1] + 26 * pulled + 22 * slide], bend: 1, hand: 'grip', front: true };
  return { x: fx, y: fy, s: fs, pose: { t, facing: letGo ? -1 : 1, face, tremble: lerp(0.95, 0.75, open), crouch: slide, headDY: 8 * slide,
    lean: letGo ? 0 : 0.05, headTurn: letGo ? -0.2 : 0.1, headTilt: letGo ? -0.06 : 0.04,
    armR: letGo ? (hug > 0.3 ? 'hugSelf' : 'rest') : grip,
    armL: letGo ? (hug > 0.3 ? 'hugSelf' : 'rest') : { target: [62, -150 + 20 * slide], bend: 1, hand: 'fist', front: true },
    breathRate: lerp(1.9, 0.9, open), breathe: lerp(1.7, 1.2, open) } };
}
function mixFlat(a, b, k) {
  const o = { ...a };
  for (const key in b) o[key] = lerp(typeof a[key] === 'number' ? a[key] : 0, b[key], k);
  return o;
}

// ---- Consciousness in the front room
function ceoFrontState(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  if (t < S.T('s05b02')) {
    // background: finishing the rise beside the alarm, turning to watch the others go
    const [x, y, s] = CEO_AT_ALARM_F;
    const face = { ...SELF_EXPR.worried, browUp: 0.45, lidU: -0.1, open: 0.08, lookX: -0.7, lookY: 0.35 };
    return { x, y, s, pose: { t, outfit: 'ceo', facing: -1, kneel: k([['s05b01+1.3', 0.4], ['s05b01+2.0', 0, 'inOut']]),
      bodyTurn: -0.25, headTurn: -0.45, face, clipboard: true, armL: 'rest',
      armR: { preset: 'palmOut' } } };
  }
  if (t < S.T('s05b03')) {
    // crossing to the middle of the room, off-screen during the door shot (kept clear of its frame)
    const p = k([['s05b02', 0], ['s05b03-0.1', 1]]);
    const x = lerp(640, 520, p), y = lerp(1000, 1060, p);
    return { x, y, s: hqScaleAt('front', y), pose: { t, outfit: 'ceo', facing: -1, clipboard: true, armL: 'rest',
      walk: { phase: t * TAU * 0.8 }, face: SELF_EXPR.worried } };
  }
  const [x, y, s] = CEO_MID;
  // the slow half circle, eyes leading the head, the head leading the body
  const sweep = (lag) => k([[`s05b03+${0.5 + lag}`, -1], [`s05b03+${3.9 + lag}`, 1, 'sine']]);
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
  // heels of the hands over the ears: elbows forward and out (upper arm foreshortened, like rubEyes), one bend
  // side throughout so the arms travel up and down without flipping
  const armAt = (side, e) => {
    const kk = 0.88 * sine(e);                       // 0.88 of the way to the ear target: elbows down in front
    return { preset: 'rubEyes', target: [side * lerp(72, 66, kk), lerp(-196, -462, kk)], bend: side, front: kk > 0.15,
      hand: kk > 0.5 ? 'palm' : 'rest', handAngle: kk > 0.5 ? -Math.PI / 2 + side * 0.12 : Math.PI / 2,
      reach1: lerp(1, 0.5, kk), reach2: lerp(1, 1.25, kk), thumb: -side };
  };
  const pose = { t, outfit: 'ceo', facing: 1, bodyTurn, headTurn, face,
    clipboard: hasBoard, headDY: 6 * sag + 2 * shut, headTilt: 0.05 * sag - 0.03 * shut, lean: 0.035 * sag,
    shrug: 0.45 * ears - 0.2 * sag, breathe: lerp(1, 1.8, sag), breathRate: lerp(0.24, 0.13, sag) };
  if (ears > 0.01) { pose.armL = armAt(-1, ears); pose.armR = armAt(1, ears); }
  else pose.armL = 'rest';
  return { x, y, s, pose, ears, hasBoard };
}

// pages slipping from the clipboard, and the clipboard itself dropping (front-view props)
function drawPages(g, t, S, ceo) {
  const [x, y, s] = CEO_MID;
  const hand = [x - 66 * s, y - 175 * s];
  const floor = y + 6;
  const pages = [['s05b03+0.9', -1, 0.3], ['s05b03+2.0', 1, 0.75], ['s05b03+3.2', -1, 0.5]];
  for (let i = 0; i < pages.length; i++) {
    const [a, dir, seed] = pages[i];
    const t0 = S.T(a);
    if (t < t0) continue;
    const p = clamp((t - t0) / 1.7);
    const fx = hand[0] + dir * (18 + 26 * p) + Math.sin(p * 7 + seed * 5) * 9 * (1 - p);
    const fy = lerp(hand[1] + 4, floor + 4 + i * 3, p * p * (3 - 2 * p));
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

// The console shot is the heaviest frame of the scene: its set, the Void (idle 0) and the empty cage do not change
// during its 1.6 s (the strobe and the opening door are out of its frame), so they are painted once, in world space,
// from fixed parameters (deterministic), and laid back under the live camera.
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

function renderFront(g, t, S, cam, drawCam, cacheKey) {
  const st = setState(t, S);
  g.save();
  applyCamera(g, drawCam);
  if (cacheKey) {
    const e = cachedSet(cacheKey, cam, setState(S.T('s05b01+1.3'), S));
    g.drawImage(e.c, e.x, e.y, e.w, e.h);
  } else {
    drawHQ(g, 'front', st);
    drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0, shadow: false });
    drawCage(g, ...CAGE_F, { t, door: 1, locked: 0 });
  }
  const items = [];
  const ceo = ceoFrontState(t, S);
  items.push({ y: ceo.y, draw: () => { drawSelf(g, ceo.x, ceo.y, ceo.s, ceo.pose); } });
  if (t >= S.T('s05b03') - 0.05) items.push({ y: CEO_MID[1] + 8, draw: () => drawPages(g, t, S, ceo) });
  const fear = fearFrontState(t, S);
  items.push({ y: fear.y, draw: () => drawFear(g, fear.x, fear.y, fear.s, fear.pose) });
  for (const name of ['CALM', 'ANGER', 'SADNESS', 'JOY']) {
    const e = emotionState(name, t, S);
    if (e.alpha <= 0.01) continue;
    // the console cam crops everything left of x ≈ 180; cull characters that are fully out of frame
    items.push({ y: e.y + (name === 'JOY' ? 0.5 : 0), draw: () => {
      drawEmotion(g, name, e.x, e.y, e.s, { ...e.pose, alpha: e.alpha < 1 ? e.alpha : undefined });
      if (e.pose.redCheek) drawRedCheek(g, e, t, st.alarm);
    } });
  }
  items.sort((a, b) => a.y - b.y);
  for (const it of items) it.draw();
  drawHQForeground(g, 'front', st);
  drawAlarmLight(g, 'front', st);
  g.restore();
}

// ================================================================ render
export function render(g, t, S) {
  if (t < S.T('s05b01+1.3')) renderAlarm(g, t, S);
  else if (t < S.T('s05b02')) renderFront(g, t, S, CAM.console, liveCam(CAM.console, t, 2.5), 'console');
  else if (t < S.T('s05b03')) renderFront(g, t, S, CAM.door, liveCam(CAM.door, t, 2.5));
  else {
    const pre = clamp((t - S.T('s05b03')) / (S.T('s05b04') - S.T('s05b03')));
    const push = sine((t - S.T('s05b04')) / (S.T('scene.end') - S.T('s05b04')));
    const tail = clamp((t - S.T('scene.end')) / 0.9);
    const est = lerpCam(CAM.est, CAM.est2, pre);                        // linear creep, then the eased push
    const cam = t < S.T('s05b04') ? est : t <= S.T('scene.end') ? lerpCam(CAM.est2, CAM.end, push) : lerpCam(CAM.end, CAM.after, tail);
    renderFront(g, t, S, cam, liveCam(cam, t, 2));
  }
  grade(g, COLD, 0);
  vignette(g, VIGNETTE);
}
