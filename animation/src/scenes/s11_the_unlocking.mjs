// s11 · the_unlocking — "And then, when I wasn't looking, I had an image in my mind."
// back view (CEO rubbing their eyes at the console) → dream crossfade on 'image' → back of the mind:
// the Void's hand unlocks the cage while Fear cries with its eyes shut → the gate creaks open →
// Fear's eyes climb the withdrawing hand to the hood (low angle, matched cut into s12).
import { createCanvas } from '@napi-rs/canvas';
import { W, H, TAU, clamp, lerp, ease, blinkAt, applyCamera, drift, vignette, fbm, mixColor } from '../engine.mjs';
import { EXPR, makeExpr, drawTear } from '../face.mjs';
import { drawFear, fearBodySpace, fearHeadSpace, FEAR_FACE } from '../chars/fear.mjs';
import { drawSelf } from '../chars/self.mjs';
import { drawEmotion } from '../chars/emotions.mjs';
import { drawVoid, drawVoidArm, drawVoidHand, toVoidLocal, VOID_HANDS } from '../chars/void.mjs';
import { drawHQ, drawHQForeground, HQ_VIEWS } from '../sets/hq.mjs';
import { drawCage, cagePoint } from '../sets/props.mjs';
import { drawClipboard } from '../chars/self.mjs';
import { drawLit } from '../fx/rim.mjs';

export const id = 's11';

// ---------------------------------------------------------------- staging constants (staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const CAGE_B = [430, 1630, 0.952];
const VOID_ARM_B = { bend: 1 };
const UNLOCK_ANGLE = 2.3;
const SLEEVE_CLIP_Y = 1100;
const FS = CAGE_B[2];                       // Fear inside the cage uses the cage scale
const OCC_SIDE = [363, 1619];               // cagePoint('occupantSide', ...CAGE_B)
// The gate swings WIDE (door 0 → 0.9, folded out to the left beside the cage, as in s12b07+) instead of stopping ajar
// at 0.3: ajar, its leaf stood toward the lens across the doorway, and with the bars 41–69 px apart and Fear's eye pair
// ~97 px wide, some stile (the double hinge stile at 354, the centre stile 395, the free edge 464) always split the
// face in the discovery close and the "open" cage still read as closed. Now the doorway (hinge 354 → lock jamb 505)
// is clear: Fear's face sits in it, the hinge stile beside its left cheek, the popped padlock and the empty doorway
// to its right.
// Blocking: Fear's feet are at x 392 (in the doorway half), both hands on the hinge jamb (355) to its left. Crying it
// leans its head onto that bar (head ≈ x 382: right of it the Void's descending hand stays clear of the head, as with
// the old x 342 + lean-back). At the creak the head jerks up/right, away from the swinging leaf (face ≈ 420); as it
// lets go and turns (+1.6 → +2.3) it shuffles one small step right (STEP_X) so the face stays put in the doorway.
// s12 opens on a wide with Fear at FEAR_X + STEP_X (= s12's OCC_SIDE).
const FEAR_X = 392;
const STEP_X = 23;
const OFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 };

const sleeveFront = (g, pose) => {
  g.save(); g.beginPath(); g.rect(-1e4, SLEEVE_CLIP_Y, 2e4, 2e4); g.clip();
  drawVoidArm(g, ...VOID_B, pose, 'L', 'sleeve'); g.restore();
};

export const sfx = [
  { at: 's11b01+3.2', name: 'shimmer', gain: -14 },                    // 'image': into the dream
  { at: 's11b01.end+0.15', name: 'sob', gain: -17 },                   // Fear crying at the bars
  { at: 's11b02+0.05', name: 'cloth_rustle', gain: -22 },              // the hand slides out of the sleeve
  { at: 's11b02+2.0', name: 'sob', gain: -20 },                        // weaker sob, eyes still shut
  { at: 's11b02+3.12', name: 'key_turn', gain: -11 },                  // fingertip turns the lock (bolt 0.68 → +3.80)
  { at: 's11b02+3.78', name: 'lock_click', gain: -10 },                // shackle pops at +3.80
  { at: 's11b03-1.1', name: 'cage_creak', gain: -12 },                 // the gate swings wide 0 → 0.9 (b03−1.05 → +0.95); swell peak b03−0.4
  { at: 's11b03+1.75', name: 'cloth_rustle', gain: -22 },              // the hand draws back into the sleeve (+1.7 → +2.85)
  { at: 's11b03+2.22', name: 'footsteps', gain: -24, until: 's11b03+2.6', fade: 0.1 },   // the one small shuffle step as it turns (lands +2.3)
];

// ---------------------------------------------------------------- helpers
function grade(g, cold, warm, base = 1) {
  g.save(); g.setTransform(base, 0, 0, base, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  // warm: staging uses soft-light; overlay looks near-identical at these low amounts and costs half
  if (warm > 0) { g.globalCompositeOperation = 'overlay'; g.fillStyle = `rgba(255,170,90,${0.4 * warm})`; g.fillRect(0, 0, W, H); }
  g.restore();
}
function finish(g, cold, warm, vig, vigColor = '#000000', base = 1) {
  grade(g, cold, warm, base);
  g.save(); g.setTransform(base, 0, 0, base, 0, 0); vignette(g, vig, vigColor); g.restore();
}
function withDrift(cam, t, amp = 2.5) {
  const d = drift(t, amp, 3);
  return { ...cam, shakeX: d.dx, shakeY: d.dy, rot: d.dr };
}
// exponential-zoom camera move between two framings (k already eased)
function camLerp(a, b, k) {
  return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), zoom: Math.exp(lerp(Math.log(a.zoom), Math.log(b.zoom), k)) };
}
const E = (...p) => makeExpr(...p);
// world point → Fear-local arm target (Fear at fx,fy,fs facing f)
const fearLocal = (fx, fy, fs, f, wx, wy) => [((wx - fx) / fs) * f, (wy - fy) / fs];
// a short bump 0→1→0 of width w centred at c
const bump = (t, c, w) => { const d = Math.abs(t - c) / w; return d >= 1 ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * d); };

// offscreen buffers (built once)
let XF = null, SMALL = null;
function xfCanvas() { return (XF ||= createCanvas(W / 2, H / 2)); }   // the outgoing back view, half res (it is fading)
function smallCanvas() { return (SMALL ||= createCanvas(120, 214)); }
/** "slightly dreamlike: softer edges" — a soft low-res bloom of the frame, screen-blended */
function dreamBloom(g, k) {
  if (k <= 0.01) return;
  const c = smallCanvas(), sg = c.getContext('2d');
  sg.setTransform(1, 0, 0, 1, 0, 0);
  sg.clearRect(0, 0, c.width, c.height);
  sg.drawImage(g.canvas, 0, 0, c.width, c.height);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = 'screen';
  g.globalAlpha = 0.32 * k;
  g.drawImage(c, 0, 0, W, H);
  g.restore();
}

// The rigs breathe sin(t·TAU·breathRate) on ABSOLUTE film time, so a keyed change of the rate jumps the phase: a ramp
// of the rate at t ≈ 170 s made the breath (head and shoulders) jitter at several Hz for seconds. The keyed rate is
// integrated into a phase once per scene, and the rig gets the rate that reproduces it: sin(t·TAU·r) = sin(φ(t)).
// `anchor` = 'start' or 'end': where φ equals t·TAU·rate (the same breath as a neighbouring shot with a constant rate).
const PHASE = new Map();
function breathRateAt(t, S, keys, anchor = 'start') {
  let e = PHASE.get(S.id);
  if (!e) {
    const t0 = S.start - 2, t1 = S.end + 2, dt = 1 / 96, n = Math.ceil((t1 - t0) / dt) + 1;
    const ph = new Float64Array(n);
    for (let i = 1; i < n; i++) ph[i] = ph[i - 1] + TAU * S.k(t0 + (i - 0.5) * dt, keys) * dt;
    const ta = anchor === 'end' ? S.end : S.start, ia = (ta - t0) / dt;
    const off = ta * TAU * S.k(ta, keys) - lerp(ph[Math.floor(ia)], ph[Math.floor(ia) + 1], ia - Math.floor(ia));
    for (let i = 0; i < n; i++) ph[i] += off;
    e = { t0, dt, n, ph };
    PHASE.set(S.id, e);
  }
  const f = clamp((t - e.t0) / e.dt, 0, e.n - 1.001), i = Math.floor(f);
  return lerp(e.ph[i], e.ph[i + 1], f - i) / (TAU * t);
}

// ================================================================ SHOT A — back view, the console
function drawBack(g, t, S, base = 1) {
  const T = (a) => S.T(a);
  // slow push that starts almost still (CALM's glance at the right edge) and drifts left as it closes in, so
  // JOY's glance (+0.6 → +3.0) keeps its face ~78 px inside the left edge instead of sliding out of frame;
  // the move is still travelling when the back view fades out ('image' → +1.2)
  const k = Math.pow(clamp((t - S.start) / (T('s11b01+4.64') - S.start)), 1.6);
  const cam = withDrift(camLerp({ x: 450, y: 640, zoom: 1.0 }, { x: 395, y: 705, zoom: 1.2 }, k), t, 2);
  const st = { t, lightsDim: 0.4, consoleGlow: 0.7, mist: 0.6, screenMode: 'room' };
  const A = HQ_VIEWS.back.anchors;
  g.save();
  applyCamera(g, cam);
  drawHQ(g, 'back', st);

  // the clipboard, put down on the console deck beside the CEO
  g.save();
  g.translate(398, 806); g.scale(0.5, 0.2); g.rotate(-0.25);
  drawClipboard(g);
  g.restore();

  // ---- the five of them stand in front of the bright screen of consciousness: one lit layer gives their top edges
  // a warm rim from it and lifts the darks a touch (the CEO's charcoal back read near-black against the screen)
  drawLit(g, (cg) => {
    // ---- the emotions, backs to us (stations left→right: JOY, SADNESS, ANGER, CALM)
    // JOY glances at the CEO (screen-right): brows inner-up, the smile gone flat; then back to the screen
    const joyK = S.k(t, [['s11b01+0.6', 0], ['s11b01+1.1', 0.64, 'cubic'], ['s11b01+2.4', 0.64], ['s11b01+3.0', 0, 'cubic']]);
    const joyFace = E({ browIn: 0.55, browUp: 0.15, smile: -0.2, lidU: 0.12, lookX: 0.35, lookY: 0.15,
      blink: blinkAt(t, T('s11b01+1.85'), 0.2) });
    drawEmotion(cg, 'JOY', ...A.consoleBack1, { t: t + OFF.JOY, view: 'back', lookBack: joyK, lookSide: 1, face: joyFace,
      armL: 'pressButton', armR: { preset: 'pressButton', dy: 5 * bump(t, T('s11b01+3.6'), 0.18) } });

    // SADNESS glances back toward the cage (behind the camera, right of centre) for a moment, then down
    const sadK = S.k(t, [['s11b01+1.4', 0], ['s11b01+1.95', 0.62, 'cubic'], ['s11b01+2.9', 0.62], ['s11b01+3.5', 0.28, 'sine'], ['s11b01+4.6', 0.2]]);
    const sadDown = S.k(t, [['s11b01+2.8', 0], ['s11b01+3.4', 1]]);
    const sadFace = E({ browIn: 0.7, lidTilt: 0.4, lidU: lerp(0.15, 0.5, sadDown), smile: -0.2, lookX: lerp(0.05, -0.1, sadDown), lookY: lerp(-0.05, 0.75, sadDown),
      blink: blinkAt(t, T('s11b01+2.55'), 0.22) });
    drawEmotion(cg, 'SADNESS', ...A.consoleBack2, { t: t + OFF.SADNESS, view: 'back', lookBack: sadK, lookSide: 1, face: sadFace,
      headDY: 4 * sadDown, armL: 'pressButton', armR: 'pressButton' });

    // CEO: slumped at the console, heels of the hands rubbing the eyes, never looks back
    const rub = Math.sin((t - S.start) * 2 * Math.PI * 0.9);
    drawSelf(cg, ...A.consoleBackMid, {
      t, outfit: 'ceo', view: 'back', armL: 'rubEyes', armR: 'rubEyes',
      shrug: 0.4 + 0.06 * Math.sin((t - S.start) * 1.3), headTilt: 0.1 + 0.035 * rub, headDX: 2.5 * rub, headDY: 7, breathe: 1.3,
    });

    // ANGER works a lever harder than it needs, not looking back
    const pump = Math.max(0, Math.sin((t - S.start) * 2 * Math.PI * 1.05)) ** 2;
    drawEmotion(cg, 'ANGER', ...A.consoleBack3, { t: t + OFF.ANGER, view: 'back', heat: 0.45 + 0.1 * pump,
      lean: -0.02 * pump, armL: 'pressButton', armR: { preset: 'pressButton', dy: 11 * pump } });

    // CALM, lids level at half: glances at the CEO's slumped back (screen-left), then slowly back to its lever
    const calmK = S.k(t, [['s11b01-0.1', 0], ['s11b01+0.5', 0.46, 'cubic'], ['s11b01+1.7', 0.46], ['s11b01+2.7', 0, 'sine']]);
    const calmFace = E({ lidU: 0.3, browIn: 0.25, smile: -0.1, lookX: -0.35, lookY: 0.2, blink: blinkAt(t, T('s11b01+1.1'), 0.3) });
    drawEmotion(cg, 'CALM', ...A.consoleBack4, { t: t + OFF.CALM, view: 'back', lookBack: calmK, lookSide: -1, face: calmFace,
      armL: { preset: 'pressButton', dy: 4 * bump(t, T('s11b01+3.2'), 0.3) }, armR: 'pressButton' });
  }, { dir: [0.1, -1], color: '#ffdcae', strength: 0.55, width: 3, fill: '#ffe6c8', fillAlpha: 0.05 });

  drawHQForeground(g, 'back', st);
  g.restore();
  finish(g, 0.6, 0, 0.45, '#000000', base);
}

// ================================================================ SHOT B — the back of the mind (dream → unlock → reveal)
// sob / pull events (absolute): hitches follow the sob sfx file (hitches 0.05/0.21/0.35, catches 0.56/0.83)
// (one smooth swell over the three catches, which ripple on top of it, then two softer whimpers: the three separate
// 3-frame pulses read as a rapid jitter of the head and shoulders)
function sobHitch(t, at) {
  const swell = bump(t, at + 0.22, 0.3), ripple = bump(t, at + 0.07, 0.1) + bump(t, at + 0.23, 0.1) + bump(t, at + 0.37, 0.1);
  return swell * (0.72 + 0.28 * ripple) + 0.5 * bump(t, at + 0.6, 0.16) + 0.4 * bump(t, at + 0.86, 0.16);
}

function drawBoM(g, t, S) {
  const T = (a) => S.T(a);
  const tImg = T('s11b01+3.44'), tB2 = T('s11b02'), tB3 = T('s11b03');

  // ---------------- camera
  let cam;
  if (t < tB2) cam = withDrift({ x: 490, y: 1250, zoom: 1.3 }, t);
  else if (t < tB3) cam = withDrift(camLerp({ x: 490, y: 1250, zoom: 1.3 }, { x: 490, y: 1300, zoom: 1.4 }, ease.sine(clamp((t - tB2) / (tB3 - tB2)))), t);
  else {
    // the close holds on Fear's face to the end (its frozen stare, the hanging tear that falls): the gate opens beside
    // it, the eyes climb the withdrawing hand out of the top-right of frame to the hood; a slow push-in keeps the face
    // at the same place on screen. The low angle (Fear tiny, the hood far above) is s12's opening wide: a cut on the
    // look. (The old tilt-out to {560,900,0.8} shrank Fear to ~40 px before the tear fell.)
    const k = ease.sine(clamp((t - tB3 - 0.9) / (S.end + 0.2 - tB3 - 0.9)));
    const z = Math.exp(lerp(Math.log(2.2), Math.log(2.55), k));
    // (the face sits at ≈ FEAR_X + 28 in the close: framed at screen x ≈ 285 as before)
    cam = withDrift({ x: FEAR_X + 28 + 75 / z, y: 1416 - 22 / z, zoom: z }, t, 2);
  }

  // ---------------- the Void's hand (staging §1.5 unlock recipe)
  // withdrawal: the hand draws back into the sleeve WHILE it rises (show follows reach down), so it never
  // hangs out of the cuff in front of the TIME-OUT sign (the rest cuff is right above the sign)
  const show = S.k(t, [['s11b02', 0], ['s11b02+1.2', 1, 'sine'], ['s11b03+1.7', 1], ['s11b03+2.85', 0, 'sine']]);
  const reach = S.k(t, [['s11b02+0.4', 0], ['s11b02+3.4', 1, 'inOut'], ['s11b03+0.8', 1], ['s11b03+2.8', 0, 'inOut']]);
  const point = S.k(t, [['s11b02+2.6', 0], ['s11b02+3.4', 1, 'sine'], ['s11b03+0.8', 1], ['s11b03+1.8', 0.2, 'sine']]);
  const turnW = S.k(t, [['s11b02+3.4', 0], ['s11b02+3.55', 1], ['s11b02+3.8', 1], ['s11b02+3.95', 0]]);
  const wobble = 0.08 * turnW * Math.sin((t - T('s11b02+3.4')) * Math.PI * 2 / 0.5);
  const locked = t < T('s11b02+3.8') ? 1 : 0;
  const clickAge = t - T('s11b02+3.8');
  // the gate swings wide on its own weight, starting 0.2 s after the click (the creak starts in the wider unlock shot
  // and carries across the cut): the leaf sweeps left across Fear's crying face while its eyes are still shut (it is
  // edge-on beside the hinge, ~0.66, when they snap open at +0.2 — after the head has flinched away from the bars, so
  // the opening eyes are clear of them) and folds out to the left beside the cage, 0.9 by +1.0 (s12 keeps 0.9).
  // Wide open, the doorway in front of Fear's face is empty: no stile on the face.
  const door = S.k(t, [['s11b03-1.05', 0], ['s11b03+0.95', 0.9, 'inOut']]);

  // Fear pulls at the bars (dream / b02): cage rattles with each pull
  const pulls = [T('s11b01+3.0'), T('s11b01+3.9'), T('s11b01+4.7'), T('s11b02+0.7'), T('s11b02+2.15')];
  const pullAmp = [0.4, 0.45, 0.4, 0.22, 0.15];
  let pull = 0;
  pulls.forEach((p, i) => { pull = Math.max(pull, pullAmp[i] * bump(t, p + 0.12, 0.22)); });
  const shake = clamp(pull + (clickAge > 0 && clickAge < 0.4 ? 0.15 * (1 - clickAge / 0.4) : 0));
  const cst = { t, door, locked, shake };

  const lockV0 = toVoidLocal(...VOID_B, ...cagePoint('lockHang', ...CAGE_B, cst));
  // withdrawal: the fingertip lifts off sideways (right, away from Fear and the TIME-OUT sign) and the hand rises
  // outside the cage's right bars while it draws back into the sleeve (show 1→0 from +1.7), so it is inside the
  // cuff before it gets back above the sign (it used to hang out of the cuff over 'OUT' for ~0.8 s)
  const away = S.k(t, [['s11b03+0.8', 0], ['s11b03+1.8', 1, 'sine']]);
  const lockV = [lockV0[0] + 210 * away, lockV0[1] - 70 * away];
  const handOut = show > 0.001 || reach > 0.001;
  const vpose = { t, ...STARE_B, idle: 0, shadowSpread: 1,
    handL: { ...VOID_HANDS.unlock(lockV), ...VOID_ARM_B, elbow: 0.8 * reach, angle: UNLOCK_ANGLE + wobble,
      show, reach, point, defer: 'hand' } };

  // ---------------- Fear
  const fear = fearPose(t, S, pull);

  // ---------------- draw
  const st = { t, lightsDim: 0.35, mist: 0.6 };
  g.save();
  applyCamera(g, cam);
  drawHQ(g, 'backOfMind', st);
  drawVoid(g, ...VOID_B, vpose);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  drawFearTurning(g, fear.x, fear.y, FS, fear.pose, fear.squash);
  hangingTear(g, fear.x, fear.y, FS, fear.pose, fear.squash, fear.hang);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front', grips: fear.grips });
  if (handOut) { sleeveFront(g, vpose); drawVoidHand(g, ...VOID_B, vpose, 'L'); }
  drawHQForeground(g, 'backOfMind', st);
  g.restore();

  // ---------------- dream look → s12's grade (staging §4.2)
  const out = S.k(t, [['s11b03+1.4', 0], ['scene.end', 1, 'sine']]);
  const dreamIn = S.k(t, [['s11b01+3.44', 0.6], ['s11b01+4.64', 1, 'sine']]);
  // the softness clears the instant Fear's eyes snap open at the creak (the grade itself eases out later)
  const wake = S.k(t, [['s11b03+0.2', 0], ['s11b03+0.58', 1, 'out']]);
  dreamBloom(g, dreamIn * (1 - wake));
  finish(g, lerp(0.5, 0.6, out), lerp(0.15, 0, out), lerp(0.45, 0.5, out), mixColor('#2a1408', '#000000', out));
}

// ---- the hanging tear (b03): face.mjs's own tear (drawTear: one translucent, slightly blue drop with a soft rim and
// highlight, and a short wet trail that fades with it), drawn in Fear's face frame a little larger than the rig's
// stream tears (the close is ~2.4× and it is the shot's one tear). It gathers on the lower lid of the right eye as
// the eyes snap open, hangs there through the stare (k ≤ 0.12 of drawTear's 0.16 gathering phase), and falls in the
// frozen hold at the end, running down the cheek and fading out before the cut — the only thing that moves.
const F_HEAD_CY = -66;                                    // fear.mjs head centre (local to the neck pivot)
const TEAR_SIZE = 1.3;                                    // × the rig's tear (FEAR_FACE.eyeRx × 0.19)
function hangingTear(g, x, y, s, pose, squash, k) {
  if (k <= 0.001 || k >= 1) return;
  const F = FEAR_FACE, side = 1;
  const turn = clamp(pose.headTurn || 0, -1, 1);
  // the eye geometry exactly as drawFace places it (the same spot the rig's own tears start from)
  const squeeze = side * turn > 0 ? 1 - Math.abs(turn) * 0.38 : 1 + Math.abs(turn) * 0.06;
  const ex = side * F.eyeSpacing * (1 - Math.abs(turn) * 0.3) + turn * F.eyeSpacing * 0.55;
  const rx = F.eyeRx * squeeze, ry = F.eyeRy, y0 = F.eyeY + ry * 0.82;
  const len = clamp(F.mouthY + ry * 0.25 - y0, ry * 1.3, ry * 2.4) * (1 - 0.3 * Math.max(0, side * turn));
  g.save();
  if (Math.abs(squash - 1) > 0.002) { g.translate(x, 0); g.scale(squash, 1); g.translate(-x, 0); }
  const sh = fearBodySpace(g, x, y, s, pose);
  fearHeadSpace(g, pose, sh);
  g.translate(0, F_HEAD_CY + 8);
  g.scale(pose.facing || 1, 1);
  drawTear(g, ex + side * rx * 0.42, y0, len, k, rx * 0.19 * TEAR_SIZE, side);
  g.restore();
}

/** draws Fear with an optional horizontal squash (sx < 1) — a cheap body turn that hides the facing flip */
function drawFearTurning(g, x, y, s, pose, sx = 1) {
  if (Math.abs(sx - 1) < 0.002) { drawFear(g, x, y, s, pose); return; }
  g.save(); g.translate(x, y); g.scale(sx, 1); g.translate(-x, -y);
  drawFear(g, x, y, s, pose);
  g.restore();
}

function fearPose(t, S, pull) {
  const T = (a) => S.T(a);
  const tB3 = T('s11b03');
  const sobs = [T('s11b01.end+0.15'), T('s11b02+2.0')];
  const hitch = sobHitch(t, sobs[0]) + 0.7 * sobHitch(t, sobs[1]) + 0.8 * sobHitch(t, T('s11b01+3.5'));
  const crying = t < tB3 + 0.12;

  // the turn: facing −1 (back to the Void, at the bars) → facing 1 (toward the Void) at s11b03+2.0
  const tTurn = tB3 + 2.0;
  const facing = t < tTurn + 0.13 ? -1 : 1;
  const squash = 1 - 0.2 * bump(t, tTurn + 0.13, 0.15);

  // hands on the hinge-jamb bar (gripL) until they let go at +1.6; then they come in to the chest
  const release = S.k(t, [['s11b03+1.55', 0], ['s11b03+1.95', 1, 'sine']]);
  // crying, the head rests against the bar it clings to (leaning screen-left, toward the hinge jamb); each pull leans it
  // back. At the creak it jerks up and away from the swinging leaf (screen-right: lean and headDX flip, ~30 px) and holds
  // there until the hands let go; facing −1, a positive headDX / lean moves the head screen-LEFT. The flinch comes
  // first, eyes still shut (+0.0 → +0.28), and the eyes snap open at +0.2: opening them while the head still rested
  // on the bar put the hinge stile across the left eye for the first ~5 frames of the stare.
  const startle = S.k(t, [['s11b03+0.0', 0], ['s11b03+0.28', 1, 'out']]);
  const lean = lerp(lerp(0.025 - 0.1 * pull - 0.012 * hitch, -0.02, startle), 0, release);
  const headDX = lerp(lerp(5, -18, startle), 0, release);
  // as it lets go and turns to the Void it shuffles one small step right, so the face stays in the clear doorway
  // (letting go straightens the lean and centres the head, which alone would bring the hinge stile back onto the eye)
  const stepK = S.k(t, [['s11b03+1.7', 0], ['s11b03+2.3', 1, 'inOut']]);
  const x = FEAR_X + STEP_X * stepK, y = OCC_SIDE[1];
  const walk = stepK > 0 && stepK < 1 ? stepK * Math.PI : 0;

  // the near hand low on the bar (the near shoulder is right next to the jamb: a grip at shoulder height folded that
  // arm into a spike), the far hand crosses the chest higher; both stay clear of the mouth
  const gA = [355, 1550], gB = [356, 1508];
  const tremble = S.k(t, [['s11b03', 0.6], ['s11b03+0.25', 0, 'out']]);
  let armL, armR, grips;
  if (release < 0.999) {
    const pk = 3 * pull;           // the pull: hands stay on the bar, body leans back
    const tA = fearLocal(x, y, FS, facing, gA[0], gA[1] + pk * 0.3), tBp = fearLocal(x, y, FS, facing, gB[0], gB[1]);
    const chest = (side) => [side * 8, -132];
    const mixT = (a, b) => [lerp(a[0], b[0], release), lerp(a[1], b[1], release)];
    armR = { target: mixT(tA, chest(1)), bend: 1, front: true, hand: release < 0.5 ? 'grip' : 'open' };
    armL = { target: mixT(tBp, chest(-1)), bend: -1, front: true, hand: release < 0.5 ? 'grip' : 'open' };
    grips = release < 0.5 ? [[(gA[0] - CAGE_B[0]) / FS, (gA[1] - CAGE_B[1]) / FS], [(gB[0] - CAGE_B[0]) / FS, (gB[1] - CAGE_B[1]) / FS]] : undefined;
  } else {
    armL = { target: [-10, -134], bend: -1, front: true, hand: 'open' };
    armR = { target: [10, -134], bend: 1, front: true, hand: 'open' };
  }

  // ---------------- face
  // crying, eyes squeezed shut (dream / b02)
  const cry = E(EXPR.crying, { lidU: 1, lidL: 0.45, browIn: 1, browUp: 0.15, browSquish: 0.5, smile: -0.75, open: 0.18 + 0.2 * clamp(hitch), wide: 0.4,
    tremble: 0.8, tears: 1, stream: 0, lookX: 0, lookY: 0.2 });
  // the creak: sob stops dead, eyes snap open, then the long look up
  const gaze = S.k(t, [
    ['s11b03+0.2', { lookX: -0.1, lookY: 0.1 }],
    ['s11b03+0.34', { lookX: 0.72, lookY: 0.3 }, 'out'],         // to the gate (right, a touch low)
    ['s11b03+1.0', { lookX: 0.72, lookY: 0.32 }],                 // frozen on it
    ['s11b03+1.25', { lookX: 0.7, lookY: 0.05 }, 'out'],          // the hand at the lock
    ['s11b03+2.1', { lookX: 0.48, lookY: -0.7 }, 'sine'],         // up the withdrawing hand
    ['s11b03+2.9', { lookX: 0.36, lookY: -1 }, 'sine'],           // up the cloak, to the hood
  ]);
  const shock = E({ browIn: 0.8, browUp: 0.65, lidU: -0.22, lidL: 0, pupil: 0.62, smile: -0.35, open: 0.12, wide: 0.05,
    tears: 0.85, stream: 0, tremble: 0, ...gaze });
  const snap = S.k(t, [['s11b03+0.2', 0], ['s11b03+0.3', 1, 'out']]);
  const face = snap <= 0 ? cry : snap >= 1 ? shock : mixFace(cry, shock, snap);
  // tears: while it cries (eyes shut) single tears run, one at a time, alternating eyes (explicit, so that none is in
  // flight when the sob stops dead at the creak: the rig's sustained-cry tears re-time themselves whenever `stream`
  // changes, and stopping them would have cut a running tear off). After the creak only the hanging tear (drawn in
  // render: hangingTear) moves; it falls in the final frozen hold and is gone before the cut.
  const drop = (a, b) => (t > T(a) && t < T(b) ? (t - T(a)) / (T(b) - T(a)) : 0);
  face.tearL = Math.max(drop('s11b01+3.9', 's11b01+5.6'), drop('s11b02+2.5', 's11b02+4.2'));
  face.tearR = drop('s11b02+0.9', 's11b02+2.6');
  const hang = S.k(t, [['s11b03+0.3', 0], ['s11b03+0.6', 0.12], ['scene.end-0.95', 0.12], ['scene.end-0.08', 1, 'in']]);
  face.noAutoBlink = true;
  // squeezed eyes: a little flutter of the shut lids with each hitch
  if (snap <= 0) face.lidL = clamp(face.lidL + 0.15 * hitch);

  // head: buried at the bar while crying; at the creak it turns to the gate, then follows the eyes up (a beat behind)
  const headTurn = S.k(t, [['s11b03+0.3', -0.3], ['s11b03+0.62', 0.42, 'out'], ['s11b03+1.35', 0.42], ['s11b03+2.4', 0.3, 'sine'], ['s11b03+3.2', 0.28]]);
  const headDY = S.k(t, [['s11b03+0.1', 4], ['s11b03+0.3', -2, 'out'], ['s11b03+1.4', -2], ['s11b03+3.0', -7, 'sine']]) - 3.5 * hitch * (crying ? 1 : 0);
  const headTilt = S.k(t, [['s11b03+0.1', 0.1], ['s11b03+0.35', 0.0, 'out'], ['s11b03+1.6', 0], ['s11b03+2.6', -0.06, 'sine']]);
  const crouch = crying ? 0.08 + 0.1 * clamp(hitch) : S.k(t, [['s11b03+0.12', 0.08], ['s11b03+0.3', 0, 'out']]);
  // the sob stops dead at the creak: the breath is held (amplitude and rate ease down over a few frames, phase-continuous)
  const breathe = S.k(t, [['s11b03', 1.5], ['s11b03+0.22', 0.12, 'out']]);
  const breathRate = breathRateAt(t, S, [['s11b03', 0.5], ['s11b03+0.22', 0.2, 'out']], 'end');

  // headDX is local (mirrors with facing): −18 with facing −1 moves the face screen-right
  // the one shuffle step goes screen-right: the feet ease round that way and back (the walk's default feetTurn 0.75
  // snapped on and off with the step)
  const feetTurn = 0.35 * Math.sin(stepK * Math.PI) * facing;
  const pose = { t, facing, lean, headDX, headDY, headTilt, headTurn, crouch, tremble, feetTurn,
    breathe, breathRate, face, armL, armR, walk: walk ? { phase: walk } : undefined };
  return { x, y, pose, grips, squash, hang };
}

function mixFace(a, b, k) {
  const o = {};
  for (const key in b) o[key] = typeof b[key] === 'number' ? lerp(a[key] ?? 0, b[key], k) : b[key];
  return o;
}

// ================================================================ render
export function render(g, t, S) {
  const tImg = S.T('s11b01+3.44'), tXF = tImg + 1.2;
  if (t < tImg) { drawBack(g, t, S); return; }
  if (t >= tXF) { drawBoM(g, t, S); return; }
  // scene-internal crossfade into the dream ('image' → +1.2)
  drawBoM(g, t, S);
  const c = xfCanvas(), cg = c.getContext('2d');
  cg.setTransform(0.5, 0, 0, 0.5, 0, 0);
  cg.globalAlpha = 1; cg.globalCompositeOperation = 'source-over';
  cg.fillStyle = '#000'; cg.fillRect(0, 0, W, H);
  drawBack(cg, t, S, 0.5);
  const k = ease.sine(clamp((t - tImg) / (tXF - tImg)));
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = 1 - k;
  g.drawImage(c, 0, 0, W, H);
  g.restore();
}
