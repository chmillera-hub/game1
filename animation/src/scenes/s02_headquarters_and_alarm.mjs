// s02 · headquarters_and_alarm · MIND_HQ (dissolve in from s01's amber eye-glow)
// The cozy control room, interrupted again and again. Fear pulls the alarm; the CEO walks in, kneels by Fear,
// asks "Fear? What are you looking at?" — Fear answers by pointing up-left past the CEO's shoulder.
//
// Shots (see data/staging.md §3 s02):
//  A  S.start → s02b01.end       back view: console ridge lights (zoom 2.0) pull out to the 'screen' wide (1.0),
//                                settled by s02b01+1.1 (all four emotions in frame)
//  B  → s02b02+1.0               back view: slow pan left toward the alarm wall (from s02b01+1.3)
//  C  → s02b02+2.8               alarm 'pull': Fear reaches blindly, pulls on 'alarm' (s02b02+2.40)
//  D  → s02b03+0.45              back view: the four (three in frame) don't even startle; red wash from the left
//  E  → s02b03+4.70 ('looking')  front 'door': the door opens, the CEO steps in, stops to tug the lapels, walks on
//  F  → s02b03.end−0.2           front: camera drifts right with the CEO's gaze to the alarm; CEO kneels by Fear
//  H  → s02b04+1.3               alarm view, CEO close (Fear's head at the right edge): the eyes come down from the
//                                bell and land on Fear, the brows soften, "Fear?" (QA: the intro had no readable face)
//  G  → S.end                    alarm two-shot: "What are you looking at?" → Fear points up-left; the CEO's eyes
//                                follow the finger, then the head turns over the left shoulder; cut on the turn

import { clamp, lerp, ease, mix, blinkAt, applyCamera, drift, vignette, noise1, fbm, ik, TAU } from '../engine.mjs';
import { makeExpr, withSpeech } from '../face.mjs';
import { blendHand } from '../hand.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, selfLocal, selfPoseAnchors } from '../chars/self.mjs';
import { drawEmotion, LOOKBACK_SMILE } from '../chars/emotions.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, HQ_VIEWS, HQ_STATIONS, hqScaleAt, ALARM_REACH } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';
import { loadTimeline, timeline, resolveAnchor } from '../timeline.mjs';
import { drawLit } from '../fx/rim.mjs';

export const id = 's02';

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const CAGE_F = [302, 846, 0.3];
const CEO_AT_ALARM_F = [640, 1000, 0.444];
const FEAR_ALARM_F = [734, 973, 0.42];
const OFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 }; // §5.11 per-character idle offsets
const FA = HQ_VIEWS.front.anchors, BA = HQ_VIEWS.back.anchors, AA = HQ_VIEWS.alarm.anchors;

const E = (...p) => makeExpr(...p); // full expression (every key present → clean blends)
const sstep = (a, b, x) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };
const pulseEnv = (t, a, up, hold, down) => (t < a ? 0 : t < a + up ? ease.sine((t - a) / up) : t < a + up + hold ? 1 : t < a + up + hold + down ? 1 - ease.sine((t - a - up - hold) / down) : 0);

function grade(g, cold, warm) {
  // (below ~0.12 a pass changes no channel by more than ~1.5 %: skip it, it costs ~1–3 ms of full-frame compositing)
  if (cold < 0.12) cold = 0;
  if (warm < 0.12) warm = 0;
  if (!cold && !warm) return;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function cam(g, c, t, amp = 2.5) {
  const d = drift(t, amp, 3);
  applyCamera(g, { x: c.x, y: c.y, zoom: c.zoom, shakeX: d.dx, shakeY: d.dy, rot: d.dr * 0.5 });
}

// ---------------------------------------------------------------- the CEO's walk (door → CEO_AT_ALARM_F)
// Path: a gentle curve from the doorway, toward the camera and right, ending exactly at CEO_AT_ALARM_F.
const P0 = [168, 934], P1 = [372, 1086], P2 = [CEO_AT_ALARM_F[0], CEO_AT_ALARM_F[1]];
const bez = (u) => [
  (1 - u) * (1 - u) * P0[0] + 2 * (1 - u) * u * P1[0] + u * u * P2[0],
  (1 - u) * (1 - u) * P0[1] + 2 * (1 - u) * u * P1[1] + u * u * P2[1],
];
const LUT = (() => { const a = [[0, 0]]; let L = 0, p = bez(0); for (let i = 1; i <= 200; i++) { const q = bez(i / 200); L += Math.hypot(q[0] - p[0], q[1] - p[1]); a.push([L, i / 200]); p = q; } return a; })();
const PATH_LEN = LUT[LUT.length - 1][0];
function pathAt(s) {
  s = clamp(s, 0, PATH_LEN);
  let i = 1; while (i < LUT.length - 1 && LUT[i][0] < s) i++;
  const [l0, u0] = LUT[i - 1], [l1, u1] = LUT[i];
  return bez(lerp(u0, u1, (s - l0) / (l1 - l0 || 1)));
}
// cadence (walk cycles / s) relative to τ = t − s02b03; the second cadence is solved so the CEO arrives exactly
// when the kneel starts. Stops are made at contact phases (feet planted apart) so there is no leg pop.
let WALK = null;
function walkModel(S) {
  if (WALK && WALK.key === S.start) return WALK;
  const b3 = S.T('s02b03'), kneelAt = S.T('s02b03.end-0.8') - b3;
  const C1 = 1.3; // brisk, performing confidence; the second leg (c2, solved) is slower and more tentative
  const segs = (c2) => [
    [0.18, 0], [0.38, C1], [2.36, C1], [2.62, 0], [3.38, 0], [3.68, c2], [kneelAt - 0.3, c2], [kneelAt, 0.0],
  ];
  const cad = (keys, τ) => {
    if (τ <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) if (τ <= keys[i][0]) {
      const [a, va] = keys[i - 1], [b, vb] = keys[i];
      return lerp(va, vb, ease.sine((τ - a) / (b - a || 1)));
    }
    return keys[keys.length - 1][1];
  };
  const DT = 1 / 96;
  const integrate = (c2) => {
    const keys = segs(c2), out = [];
    let s = 0, ph = 0, τ = 0;
    for (; τ <= kneelAt + 1e-6; τ += DT) {
      const p = pathAt(s), sc = hqScaleAt('front', p[1]);
      const c = cad(keys, τ);
      out.push([τ, s, ph]);
      s += c * 176 * sc * DT; ph += c * TAU * DT;
    }
    out.push([τ, s, ph]);
    return out;
  };
  let lo = 0.6, hi = 2.2, tab;
  for (let it = 0; it < 30; it++) { const mid = (lo + hi) / 2; tab = integrate(mid); if (tab[tab.length - 1][1] < PATH_LEN) lo = mid; else hi = mid; }
  const c2 = (lo + hi) / 2; tab = integrate(c2);
  // phase corrections: land the first stop on a contact pose (phase ≡ 0 mod π) and the kneel on phase ≡ π/2
  const phAt = (τ) => { const i = clamp(Math.floor(τ / DT), 0, tab.length - 1); return tab[i][2]; };
  const ph1 = phAt(2.62), want1 = Math.round(ph1 / Math.PI) * Math.PI;
  const phK = phAt(kneelAt) + (want1 - ph1);
  const want2 = Math.round((phK - Math.PI / 2) / TAU) * TAU + Math.PI / 2;
  WALK = { key: S.start, b3, kneelAt, c2, tab, DT, d1: want1 - ph1, d2: want2 - phK };
  return WALK;
}
function ceoWalk(S, t) {
  const M = walkModel(S);
  const τ = t - M.b3;
  const i = clamp(Math.floor(τ / M.DT), 0, M.tab.length - 2);
  const k = clamp((τ - M.tab[i][0]) / M.DT);
  const s = lerp(M.tab[i][1], M.tab[i + 1][1], k);
  let ph = lerp(M.tab[i][2], M.tab[i + 1][2], k);
  ph += M.d1 * sstep(1.9, 2.62, τ) + M.d2 * sstep(M.kneelAt - 1.2, M.kneelAt, τ);
  const p = pathAt(s);
  return { x: p[0], y: p[1], sc: hqScaleAt('front', p[1]), phase: ph, s, τ, moving: τ > 0.3 && τ < M.kneelAt && !(τ > 2.6 && τ < 3.4) };
}
// footstep times (absolute) for the sfx list: one per half cycle while walking
function stepTimes(S) {
  const M = walkModel(S), out = [];
  let prev = null;
  for (let τ = 0.4; τ < M.kneelAt; τ += 1 / 48) {
    const w = ceoWalk(S, M.b3 + τ);
    const n = Math.floor(w.phase / Math.PI);
    if (prev !== null && n !== prev && w.moving) out.push(+(τ).toFixed(3));
    prev = n;
  }
  return out;
}

// ---------------------------------------------------------------- shared state per frame
function lightState(S, t) {
  const a = 's02b04+2.2', b = 'scene.end';
  return {
    lightsDim: S.k(t, [[a, 0.05], [b, 0.35]]),
    consoleGlow: S.k(t, [['scene.start', 1.35], ['s02b01.end', 1.0], [a, 1.0], [b, 0.8]]),
    mist: S.k(t, [[a, 0.35], [b, 0.6]]),
    cold: S.k(t, [[a, 0.1], [b, 0.35]]),
    warm: S.k(t, [[a, 0.1], [b, 0]]),
    vig: S.k(t, [[a, 0.35], [b, 0.45]]),
  };
}
function alarmState(S, t) {
  return {
    alarm: S.k(t, [['s02b02+2.40', 0], ['s02b02+2.70', 1], ['s02b04+0.5', 1], ['s02b04+2.2', 0, 'out']]),
    alarmPulled: S.k(t, [['s02b02+2.40', 0], ['s02b02+2.65', 1, 'out'], ['s02b04+2.3', 1], ['s02b04+2.55', 0, 'out']]),
  };
}

// ---------------------------------------------------------------- emotions (back view: shots A, B, D)
function emotionsBack(g, S, t) {
  const tap = (t0, per, ph = 0) => { const q = (((t - t0) / per + ph) % 1 + 1) % 1; return q < 0.18 ? Math.sin(q / 0.18 * Math.PI) * 7 : 0; };
  const bell = S.T('s02b02+2.40');
  // JOY: bouncy humming button presses → wince at the bell → forced, too-wide smile over her shoulder
  {
    const [x, y, s] = BA.consoleBack1;
    const tt = t + OFF.JOY;
    const wince = pulseEnv(t, bell + 0.05, 0.08, 0.25, 0.35);
    const look = S.k(t, [['s02b02+2.62', 0], ['s02b02+3.0', 1, 'cubic'], ['s02b03+0.05', 1], ['s02b03+0.55', 0, 'cubic']]);
    const forced = S.k(t, [['s02b02+2.75', 0], ['s02b02+3.05', 1], ['s02b03+0.0', 1], ['s02b03+0.35', 0]]);
    const humming = 1 - clamp((t - bell) / 0.2);
    // the smile comes back forced and too bright: a stretched, toothy grin under high brows and staring eyes
    // (it has to read on a small 3/4 look-back face)
    const face = mix(E({ smile: 0.65, lidL: 0.35, lidU: 0.15, browUp: 0.1 }),
      E({ smile: 1, wide: 0.95, open: 0.2, teeth: 1, lidL: 0.12, lidU: -0.12, browUp: 0.6, browIn: 0.45, lookX: -0.2, lookY: 0.05 }), forced);
    face.blink = Math.max(0, wince * 1.0);
    const bounce = humming * Math.abs(Math.sin(tt * Math.PI * 2.1)) * 4;
    drawEmotion(g, 'JOY', x, y, s, {
      t: tt, view: 'back', lookBack: Math.max(look, humming * 0.32), lookSide: look > 0.05 ? -1 : 1, face,
      headDY: -bounce + wince * 7, crouch: wince * 0.25, headTilt: humming * Math.sin(tt * 2.1 * Math.PI) * 0.05,
      armL: { preset: 'pressButton', dy: tap(17.3, 1.1, 0.5) * humming },
      armR: { preset: 'pressButton', dy: tap(17.0, 0.55) * humming + wince * -6 },
    });
  }
  // SADNESS: chin propped on one hand, slowly turning a dial → sinks into its shoulders at the bell
  {
    const [x, y, s] = BA.consoleBack2;
    const tt = t + OFF.SADNESS;
    const sink = S.k(t, [['s02b02+2.5', 0], ['s02b02+3.9', 1, 'sine']]);
    drawEmotion(g, 'SADNESS', x, y, s, {
      t: tt, view: 'back', headTilt: -0.18 + sink * 0.05, headDY: 4 + sink * 6, crouch: sink * 0.32,
      breathe: 1.3, breathRate: 0.16,
      armL: { target: [-62, -232 + sink * 10], bend: 1, hand: 'fist', layer: 'back' },
      armR: { preset: 'pressButton', dx: Math.sin(tt * 0.9) * 3, dy: 2 },
    });
  }
  // ANGER: arms crossed, glaring at the screen → head drops back, a long steaming exhale
  {
    const [x, y, s] = BA.consoleBack3;
    const tt = t + OFF.ANGER;
    const back = S.k(t, [['s02b02+2.55', 0], ['s02b02+2.95', 1, 'out'], ['s02b03+0.0', 1], ['s02b03+0.6', 0.2]]);
    const exhale = S.k(t, [['s02b02+2.95', 0], ['s02b02+3.35', 1], ['s02b03+0.3', 0]]);
    // arms folded in front of the chest: from behind only the elbows show, poking out at the sides under the wide
    // head (the 'hugSelf' preset's elbows stay inside the body silhouette, so he read as armless from the back);
    // they rise a little with the long exhale and settle
    const fold = (side) => ({ target: [side * 35, -165 - 3 * exhale + 1.5 * Math.sin(tt * 0.7 + side)], bend: side, layer: 'front', hand: 'fist' });
    drawEmotion(g, 'ANGER', x, y, s, {
      t: tt, view: 'back', heat: 0.25 + 0.45 * exhale, headDY: back * 7 - exhale * 2, lean: -0.02 * back,
      breathe: 1 + exhale, headTilt: 0.04 * back,
      armL: fold(-1), armR: fold(1),
    });
  }
  // CALM: eases a lever forward with two fingers; at the bell, a practised hand settles on the evacuation lever
  {
    const [x, y, s] = BA.consoleBack4;
    const tt = t + OFF.CALM;
    const ease1 = S.k(t, [['scene.start', 0], ['s02b01+1.5', 6]]);
    const lever = S.k(t, [['s02b02+2.6', 0], ['s02b02+3.4', 1]]);
    drawEmotion(g, 'CALM', x, y, s, {
      t: tt, view: 'back',
      armL: { preset: 'pressButton', dy: ease1 },
      armR: { preset: 'pressButton', dx: 12 * lever, dy: 4 * lever },
    });
  }
}

// ---------------------------------------------------------------- emotions (front view: shots E, F)
function emotionsFront(g, S, t, vis = () => true) {
  const b3 = 's02b03';
  // CALM (slot 1): does not turn; lids level at half; one hand resting on the evacuation lever; a patient exhale
  if (vis(FA.consoleSlot1[0], 110)) {
    const [x, y, s] = FA.consoleSlot1;
    const tt = t + OFF.CALM;
    const ex = pulseEnv(t, S.T('s02b03+3.0'), 0.5, 0.2, 0.9);
    drawEmotion(g, 'CALM', x, y, s, {
      t: tt, face: E({ lidU: 0.22, smile: 0.05, lookX: 0.15, lookY: 0.35, browIn: 0.1 }), headDY: ex * 3, breathe: 1 + ex * 0.6,
      armL: 'pressButton', armR: { preset: 'pressButton', dy: 3 },
    });
  }
  // ANGER (slot 2): glares at the CEO walking in, then points his whole arm up-right at Fear: "obviously"
  if (vis(FA.consoleSlot2[0], 110)) {
    const [x, y, s] = FA.consoleSlot2;
    const tt = t + OFF.ANGER;
    const point = S.k(t, [[`${b3}+4.85`, 0], [`${b3}+5.35`, 1, 'outCubic'], [`${b3}+6.5`, 1], [`${b3}+7.2`, 0]]);
    const look = S.k(t, [[`${b3}+1.0`, E({ lookX: -0.7, lookY: -0.5, browIn: -0.4, lidU: 0.2, pressed: 0.4 })],
      [`${b3}+3.5`, E({ lookX: -0.1, lookY: -0.6, browIn: -0.4, lidU: 0.2, pressed: 0.4 })],
      [`${b3}+4.85`, E({ lookX: 0.0, lookY: -0.55, browIn: -0.35, lidU: 0.2, pressed: 0.4 })],
      [`${b3}+5.15`, E({ lookX: 0.75, lookY: -0.65, browUp: 0.55, browIn: 0.1, lidU: 0.05, pressed: 0.5, smile: -0.1 })],
      [`${b3}+6.6`, E({ lookX: 0.75, lookY: -0.65, browUp: 0.55, browIn: 0.1, lidU: 0.05, pressed: 0.5, smile: -0.1 })],
      [`${b3}+7.2`, E({ lookX: 0.1, lookY: 0.3, browIn: -0.3, lidU: 0.25, pressed: 0.3 })]]);
    // the whole arm shoots out along the line to Fear (up-right, ≈50°: Fear's head is 45° from his shoulder), the
    // finger on that line; he leans into it so the arm clears the console rim
    drawEmotion(g, 'ANGER', x, y, s, {
      t: tt, face: look, headTurn: lerp(-0.25, 0.35, point), heat: 0.3, lean: 0.06 * point, headDY: -3 * point,
      armL: 'pressButton',
      armR: point > 0.02 ? { target: [lerp(60, 112, point), lerp(-150, -276, point)], bend: -1, hand: 'point', layer: 'over', handAng: lerp(-0.4, -0.86, point) } : 'pressButton',
    });
  }
  // SADNESS (slot 3): looks up from its dial at the CEO, one slow heavy blink, then glances at Fear, inner brows lifting
  if (vis(FA.consoleSlot3[0], 110)) {
    const [x, y, s] = FA.consoleSlot3;
    const tt = t + OFF.SADNESS;
    const face = S.k(t, [[`${b3}+4.6`, E({ lookX: 0.1, lookY: 0.55, lidU: 0.25 })],
      [`${b3}+5.0`, E({ lookX: -0.45, lookY: -0.75, lidU: 0.1, browIn: 0.2 })],
      [`${b3}+6.2`, E({ lookX: -0.3, lookY: -0.75, lidU: 0.12, browIn: 0.25 })],
      [`${b3}+6.45`, E({ lookX: 0.65, lookY: -0.7, lidU: 0.0, browIn: 0.75, browUp: 0.15 })]]);
    face.blink = blinkAt(t, S.T(`${b3}+5.45`), 0.5);
    drawEmotion(g, 'SADNESS', x, y, s, {
      t: tt, face, headTurn: S.k(t, [[`${b3}+4.7`, 0], [`${b3}+5.1`, -0.3], [`${b3}+6.25`, -0.25], [`${b3}+6.55`, 0.3]]),
      headTilt: S.k(t, [[`${b3}+4.7`, 0.08], [`${b3}+5.1`, -0.05]]),
      armL: { preset: 'pressButton', dx: Math.sin(tt * 0.9) * 2 }, armR: 'pressButton',
    });
  }
  // JOY (slot 4): turns toward the CEO coming her way — brows up, lips to one side, a helpless palms-up shrug
  if (vis(FA.consoleSlot4[0], 110)) {
    const [x, y, s] = FA.consoleSlot4;
    const tt = t + OFF.JOY;
    const turn = S.k(t, [[`${b3}+5.3`, 0], [`${b3}+5.75`, 1, 'cubic'], [`${b3}+7.4`, 1], [`${b3}+7.9`, 0.3]]);
    const shrug = S.k(t, [[`${b3}+5.85`, 0], [`${b3}+6.25`, 1, 'outCubic'], [`${b3}+6.9`, 1], [`${b3}+7.4`, 0]]);
    const face = mix(E({ smile: 0.35, lidL: 0.25, lookY: 0.4 }),
      E({ browUp: 0.75, browIn: 0.25, smile: 0.15, wide: -0.35, lidU: -0.05, lookX: -0.75, lookY: -0.55, turn: -0.15 }), turn);
    // palms-up shrug: the hands swing off the console out to the sides (arm straight), then the forearms lift with
    // the elbows tucked down at her sides, so the open palms come up BESIDE the shoulders, outside the head
    // silhouette (rx 84), and never cross the face. The elbow side flips exactly where the arm is fully straight
    // (target ≥ reach 106 from the shoulder (34,−213)), so there is no elbow pop. Drawn 'front' (over the chest,
    // after the head), like the pressButton hands they come from: no layer pop either.
    const SW = 0.35, OUT = [115, -142], UP = [122, -200];
    const arm = (side) => {
      if (shrug <= 0.02) return { preset: 'pressButton' };
      const a = shrug < SW ? ease.sine(shrug / SW) : ease.sine((shrug - SW) / (1 - SW));
      const p = shrug < SW ? [lerp(46, OUT[0], a), lerp(-150, OUT[1], a)] : [lerp(OUT[0], UP[0], a), lerp(OUT[1], UP[1], a)];
      const angR = shrug < SW ? lerp(1.2, 0.75, a) : lerp(0.75, -0.52, a); // fingers: down-out → up-out (palm up)
      return { target: [side * p[0], p[1]], bend: shrug < SW ? side : -side, hand: 'palm', layer: 'front',
        handAng: side > 0 ? angR : Math.PI - angR };
    };
    drawEmotion(g, 'JOY', x, y, s, {
      t: tt, face, headTurn: -0.6 * turn, headTilt: 0.1 * shrug, headDY: -shrug * 4, armL: arm(-1), armR: arm(1),
    });
  }
}

// ---------------------------------------------------------------- Fear
// Both fists clutch the scarf END (it hangs down the body's right side, local x ≈ 10..30): the right fist at its top,
// the left one lower, its arm across the belly with the elbow DOWN at the left side (bend −1). The old left target
// (−8,−112) with bend +1 folded that elbow UP over the scarf wrap into an X with the other arm. The fists ride down
// with the crouch (the scarf drops 18·crouch).
const CLUTCH_L = [14, -106], CLUTCH_R = [16, -125];
const POINT_D = Math.hypot(-63, -50), POINT_A = Math.atan2(-50, -63) + 2 * Math.PI;   // the up-left point (−90,−184)
// the left arm from the scarf clutch (p = 0) to the up-left point (p = 1): the fist lets go and drops to arm's length
// at the side (bend −1, the elbow unfolding out-left), then the STRAIGHT arm swings out and up and only near the top
// bends a little under the pointing hand (bend +1). The elbow-side switch happens while the arm is straight (target
// beyond reach on a 95 px circle round the shoulder), so nothing pops.
function fearPointArm(p, crouch) {
  const sx = -27, sy = -134 + 18 * crouch, R = 95, A_HANG = 1.75, A_BEND = 3.55;
  if (p < 0.3) {
    const u = ease.sine(p / 0.3);
    const o = [sx + Math.cos(A_HANG) * R, sy + Math.sin(A_HANG) * R];
    return { target: [lerp(CLUTCH_L[0], o[0], u), lerp(CLUTCH_L[1] + 18 * crouch, o[1], u)], bend: -1 };
  }
  const a = lerp(A_HANG, POINT_A, ease.sine((p - 0.3) / 0.7));
  const r = a < A_BEND ? R : lerp(R, POINT_D, (a - A_BEND) / (POINT_A - A_BEND));
  return { target: [sx + Math.cos(a) * r, sy + Math.sin(a) * r], bend: 1 };
}
// at the alarm (alarm view: fearAtAlarm, scale 1.8 / front view: FEAR_ALARM_F, scale 0.42) — one pose model
function fearPose(S, t) {
  const st = alarmState(S, t);
  const b2 = 's02b02', b4 = 's02b04';
  const pull = S.T(`${b2}+2.40`);
  // right hand: clutching the scarf → groping blindly up for the handle → found it → pulled down → let go → scarf
  const grope = S.k(t, [[`${b2}+1.05`, 0], [`${b2}+2.05`, 1, 'inOut']]);
  const fumble = (1 - grope) * grope * 4;
  let armR;
  const handle = [ALARM_REACH[0], ALARM_REACH[1] + 26 * st.alarmPulled];
  const letGo = S.k(t, [[`${b4}+2.3`, 0], [`${b4}+2.7`, 1, 'inOut']]);
  // weight: on tiptoe reaching, then hanging on the pulled handle; stands up when it lets go
  const hang = st.alarmPulled * (1 - letGo);
  const yank = pulseEnv(t, pull, 0.08, 0.05, 0.4);
  const crouch = clamp(0.32 * hang + 0.25 * yank);
  const clR = [CLUTCH_R[0], CLUTCH_R[1] + 18 * crouch];
  if (t < S.T(`${b2}+1.05`) - 0.0) armR = { target: clR, bend: 1, front: true, hand: 'fist' };
  else {
    const gx = lerp(clR[0], handle[0], grope) + fumble * 10 * Math.sin((t - pull) * 9);
    const gy = lerp(clR[1], handle[1], grope) - fumble * 14 * Math.sin((t - pull) * 7 + 1);
    const on = [lerp(gx, clR[0], letGo), lerp(gy, clR[1], letGo)];
    armR = { target: on, bend: 1, front: true, hand: grope > 0.97 && letGo < 0.5 ? 'grip' : grope > 0.6 && letGo < 0.5 ? 'open' : 'fist' };
  }
  // left hand: scarf clutch → (b04) lets go, drops to the side and lifts to point up-left past the CEO's shoulder,
  // finger shaking (fearPointArm). The clutching fist rides down with the crouch: it stays on the scarf end, under
  // the mouth, so the pressed, trembling lips of the pull stay visible.
  const point = S.k(t, [[`${b4}+2.65`, 0], [`${b4}+3.5`, 1, 'linear']]);
  // the fist opens into a pointing index finger as the arm lifts; the wrist wavers slowly (fear, not a jitter)
  const fingerK = clamp((point - 0.35) / 0.45);
  const armL = { ...fearPointArm(point, crouch), front: true, hand: blendHand('fist', 'point', fingerK),
    wrist: fingerK * Math.sin(t * TAU * 0.85) * 0.05 };
  // eyes: fixed up-left on the dark the whole time, except: squeezed shut at the pull, and (front view, b03)
  // little fast glances over the shoulder that it cannot stop
  const squeeze = S.k(t, [[`${b2}+2.35`, 0], [`${b2}+2.45`, 1], [`${b2}+3.6`, 1], [`${b2}+4.2`, 0.35], [`s02b03+2.5`, 0.35], [`s02b03+3.0`, 0]]);
  const up = E({ browIn: 0.95, browUp: 0.6, lidU: -0.28, pupil: 0.62, smile: -0.35, wide: 0.15, lookX: -0.62, lookY: -0.78, tremble: 0.5 });
  // squeezed shut: lidL stays < 0.4 (above it the rig draws HAPPY closed arcs); a negative lid tilt pinches the
  // closed lids toward the nose under the knotted, inner-up brows (a wince); lips pressed in a trembling line
  const shut = E({ browIn: 1, browUp: 0.35, browSquish: 0.9, blink: 1, lidL: 0.3, lidTilt: -0.45, pressed: 0.9, smile: -0.5, wide: -0.15, tremble: 1, lookX: -0.3 });
  let face = mix(up, shut, squeeze);
  // b03 glances: between them the eyes drop to the handle — braced and tense, never sleepy
  const b3 = S.T('s02b03');
  if (t > b3 + 2.5 && t < S.T('s02b03.end-0.2')) {
    const gl = [3.3, 4.5, 5.4, 6.25, 7.0].reduce((m, a) => Math.max(m, pulseEnv(t, b3 + a, 0.09, 0.32, 0.14)), 0);
    const down = E({ browIn: 1, browUp: 0.45, browSquish: 0.6, lidU: 0.08, lidL: 0.25, pupil: 0.6, smile: -0.45, pressed: 0.55, lookX: 0.35, lookY: 0.4, tremble: 0.8 });
    const k = clamp((t - b3 - 2.5) / 0.6);
    // the last glance (b3+7.0) is held: by the cut to the two-shot the eyes are back up on the dark
    const hold = clamp((t - b3 - 7.2) / 0.25);
    face = mix(mix(face, down, k), up, Math.max(gl, hold));
    face.headTurnG = Math.max(gl, hold);
  }
  // b04 (from the CEO close on): no answer; the eyes do not leave the dark — a fixed stare well up and LEFT, the
  // same line as the finger that follows (at the old lookX −0.62 under a −0.25 head turn the irises sat nearly
  // centred and read as looking up at the bell, up-right). One slow blink on "What" (a cut lands on open eyes: no
  // automatic blinks in the close or the two-shot)
  const stare = t >= S.T('s02b03.end-0.2') ? 1 : 0;
  // (verifier: −0.98/−0.68 sat flat-left, on the kneeling CEO's chin; −0.9/−0.92 aims up past the CEO's head, along
  // the near-vertical finger, and matches s03's −0.62/−0.8 stare)
  if (stare) { face.lookX = -0.9; face.lookY = -0.92; }
  if (t >= S.T('s02b04')) face.blink = blinkAt(t, S.T(`${b4}+1.7`), 0.22);
  face.noAutoBlink = squeeze > 0.05 || t >= S.T('s02b03.end-0.25');
  const g0 = face.headTurnG || 0;
  const tremble = 0.6 + 0.35 * squeeze + 0.2 * point;
  return {
    face, tremble, facing: 1,
    crouch,
    lean: 0.05 * grope * (1 - hang) + 0.04 * hang - 0.03 * point,
    headTilt: -0.12 * (1 - squeeze) + 0.06 * squeeze - 0.06 * g0,
    headTurn: -0.25 + 0.1 * squeeze - 0.15 * g0 - 0.17 * stare,
    headDY: yank * 4,
    armL, armR, point,
  };
}

// ---------------------------------------------------------------- CEO
// As the CEO kneels, the FAR arm (armR, behind the torso in the 3/4 turn) settles onto the raised knee — the same
// pose s04 opens on — instead of hanging past the knee with the hand dangling by the front shoe (two-shot G). The
// bones foreshorten (reach1/reach2) so the elbow only bends like a relaxed arm, and it stays in the 'back' layer
// (the upper arm behind the torso, the CEO badge clear). The hanging 'rest' arm bends the other way: the elbow
// side switches at k = 0.15, while the shortened arm is still straight (target beyond reach), so nothing pops.
const KNEE_W = [92, -176], KNEE_R = [0.72, 0.5], KNEE_ANG = 1.25, KNEE_PALM = [-0.3, 0.4, -0.85];   // = s04's knee pose
function kneeArm(kneel, sh) {   // sh = the far (right) shoulder in local coords
  const k = sstep(0.15, 0.95, kneel);
  const rest = [sh[0] + 12, sh[1] + 184];
  // the 'rest' preset's hand angle (forearm + wrist −0.08), so the hand does not turn when this spec takes over
  const { a1, a2 } = ik(sh[0], sh[1], rest[0], rest[1], 100, 92, 1);
  const ang0 = a1 + a2 - 0.08;
  const u = clamp((k - 0.15) / 0.85), e = u * u * (3 - 2 * u);
  const r1 = k < 0.15 ? lerp(1, 0.94, k / 0.15) : lerp(0.94, KNEE_R[0], e);
  const r2 = k < 0.15 ? lerp(1, 0.94, k / 0.15) : lerp(0.94, KNEE_R[1], e);
  return { target: [lerp(rest[0], KNEE_W[0], e), lerp(rest[1], KNEE_W[1], e)], bend: k < 0.15 ? 1 : -1, layer: 'back',
    hand: blendHand('rest', 'drape', e), handAngle: lerp(ang0, KNEE_ANG, e), reach1: r1, reach2: r2,
    palmDir: [lerp(-0.9, KNEE_PALM[0], e), lerp(0, KNEE_PALM[1], e), lerp(-0.45, KNEE_PALM[2], e)] };
}
function ceoFace(S, t) {
  const b3 = 's02b03';
  // performed confidence → flicker → looking around → up at the bell, kneeling beside it. The landing on Fear (and
  // the performance dropping out) is played in the close that follows (shotTwo, H), where the face can be read.
  const chinUp = E({ browIn: -0.12, browUp: 0.05, lidU: 0.04, pressed: 0.35, smile: 0.12, lookX: 0.35, lookY: 0.0 });
  const flicker = E({ browIn: 0.35, browUp: 0.15, lidU: 0.08, pressed: 0.15, smile: 0.0, lookX: 0.3, lookY: 0.15 });
  const console_ = E({ browIn: 0.15, browUp: 0.15, lidU: 0.1, smile: 0.0, lookX: -0.1, lookY: 0.5 });
  const alarm_ = E({ browIn: 0.2, browUp: 0.28, lidU: 0.0, pressed: 0.25, smile: -0.03, lookX: 0.72, lookY: -0.42 });
  const f = S.k(t, [[`${b3}+0.4`, chinUp], [`${b3}+3.2`, chinUp], [`${b3}+3.5`, flicker], [`${b3}+4.70`, flicker],
    [`${b3}+4.95`, console_], [`${b3}+5.55`, console_], [`${b3}+5.85`, alarm_]]);
  f.blink = Math.max(blinkAt(t, S.T(`${b3}+3.25`), 0.13), blinkAt(t, S.T(`${b3}+3.47`), 0.13), blinkAt(t, S.T(`${b3}+6.5`), 0.2));
  return f;
}
function ceoHeadTurn(S, t) {
  const b3 = 's02b03';
  // eyes lead, the head follows ~0.25 s later: console (toward camera) → alarm (right) → Fear
  return S.k(t, [[`${b3}+4.95`, 0.12], [`${b3}+5.25`, -0.05], [`${b3}+5.85`, -0.05], [`${b3}+6.25`, 0.5], [`${b3}+6.9`, 0.42]]);
}

// =========================================================================== shots
function shotBack(g, S, t, which) {
  const L = lightState(S, t), A = alarmState(S, t);
  let c;
  if (which === 'A' || which === 'B') {
    // one continuous move: the pull-out from the ridge lights to the screen wide (exponential zoom) settles at
    // s02b01+1.1, so all four emotions read at their stations for a beat; then a slow pan left toward the alarm
    // wall (peak ≈ 98 px/s on screen)
    const kz = ease.sine(clamp((t - S.start) / (S.T('s02b01+1.1') - S.start)));
    const kp = ease.sine(clamp((t - S.T('s02b01+1.3')) / (S.T('s02b02+1.0') - S.T('s02b01+1.3'))));
    c = { x: lerp(450, 350, kp), y: lerp(790, 650, kz) + 50 * kp, zoom: 2.0 * Math.pow(0.5, kz) * (1 + 0.12 * kp) };
  } else {
    // JOY, SADNESS, ANGER; JOY's over-the-shoulder face (screen-left side of her head) kept inside x ≥ 72
    const k = ease.sine(clamp((t - S.T('s02b02+2.8')) / 1.5));
    c = { x: lerp(334, 331, k), y: lerp(742, 732, k), zoom: lerp(1.25, 1.3, k) };
  }
  const st = { t, ...A, lightsDim: L.lightsDim, consoleGlow: L.consoleGlow, mist: L.mist, screenMode: 'room', screenModeB: 'alarm', screenBlend: 0.6 * A.alarm,
    consolePress: { 1: 0, 13: 0 } };
  g.save();
  // drift amplitude ramps with the pan (a step at the A/B boundary would jolt the frame)
  cam(g, c, t, which === 'D' ? 2.5 : lerp(1.5, 2.5, clamp((t - S.T('s02b01+1.3')) / 1.7)));
  drawHQ(g, 'back', st);
  emotionsBack(g, S, t);
  drawHQForeground(g, 'back', st);
  drawAlarmLight(g, 'back', st);
  g.restore();
  // under the dissolve: a warm amber bloom on the ridge lights so the s01 eye-glow melts into them
  const warmIn = 1 - clamp((t - S.start) / 1.2);
  if (warmIn > 0) {
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'screen';
    const gr = g.createRadialGradient(360, 640, 40, 360, 640, 720);
    gr.addColorStop(0, `rgba(255,200,120,${0.22 * warmIn})`); gr.addColorStop(1, `rgba(229,154,74,${0.06 * warmIn})`);
    g.fillStyle = gr; g.fillRect(0, 0, 720, 1280); g.restore();
  }
  grade(g, L.cold, L.warm);
  vignette(g, L.vig);
}

function shotAlarmPull(g, S, t) {
  const L = lightState(S, t), A = alarmState(S, t);
  const k = ease.sine(clamp((t - S.T('s02b02+1.0')) / 1.8));
  const c = { x: lerp(556, 566, k), y: lerp(1000, 990, k), zoom: lerp(1.45, 1.5, k) };
  const st = { t, ...A, lightsDim: L.lightsDim, mist: L.mist };
  g.save();
  cam(g, c, t, 2.5);
  drawHQ(g, 'alarm', st);
  const [fx, fy, fs] = AA.fearAtAlarm;
  const fp = fearPose(S, t);
  drawFear(g, fx, fy, fs, { t, ...fp });
  drawHQForeground(g, 'alarm', st);
  drawAlarmLight(g, 'alarm', st);
  g.restore();
  grade(g, L.cold, L.warm);
  vignette(g, L.vig);
}

function shotFront(g, S, t, which) {
  const L = lightState(S, t), A = alarmState(S, t);
  const b3 = S.T('s02b03');
  let c;
  if (which === 'E') {
    const k = ease.sine(clamp((t - S.T('s02b03+0.45')) / (S.T('s02b03+4.70') - S.T('s02b03+0.45'))));
    // (y keeps CALM's foreground face above the bottom 15 %: on screen y ≈ 1075 → 1018)
    c = { x: lerp(215, 322, k), y: lerp(826, 846, k), zoom: lerp(1.7, 1.6, k) };
  } else {
    const k = ease.sine(clamp((t - S.T('s02b03+4.70')) / (S.T('s02b04') - S.T('s02b03+4.70'))));
    // (y keeps the console row's faces out of the bottom social-UI band: JOY's face (world y ≈ 1149) sits at
    // screen y ≈ 890 → 950, not 950 → 1075; the shot is cut at s02b03.end−0.2 (k ≈ 0.95) for the CEO close)
    c = { x: lerp(468, 645, k), y: lerp(950, 962, k), zoom: 1.25 * Math.pow(1.68 / 1.25, k) };
  }
  const door = S.k(t, [['s02b03+0.2', 0], ['s02b03+0.95', 1, 'out'], ['s02b03+2.1', 1], ['s02b03+2.9', 0, 'inOut']]);
  const st = { t, ...A, lightsDim: L.lightsDim, consoleGlow: L.consoleGlow, mist: L.mist, voidShadow: 0.15, doorOpen: door };
  g.save();
  cam(g, c, t, 2.5);
  drawHQ(g, 'front', st);
  drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 1, shadow: false });
  drawCage(g, ...CAGE_F, { t, door: 1, locked: 0 });
  // Fear at the alarm, hanging on the handle (front view scale)
  const fp = fearPose(S, t);
  // cull what is off-frame (the front set at this zoom is the heaviest frame of the scene)
  const vis = (wx, hw) => Math.abs((wx - c.x) * c.zoom) < 360 + hw * c.zoom + 20;
  const fearDraw = () => { if (vis(FEAR_ALARM_F[0], 60)) drawFear(g, FEAR_ALARM_F[0], FEAR_ALARM_F[1], FEAR_ALARM_F[2], { t, ...fp }); };
  // the CEO
  const w = ceoWalk(S, t);
  const kneel = S.k(t, [['s02b03.end-0.8', 0], ['s02b03.end', 1, 'inOut']]);
  const τ = t - b3;
  const ceoVis = door > 0.02 || τ > 1.5 ? 1 : 0;
  const leafEdge = lerp(107, 189, Math.cos(1.35 * door)); // world x of the door leaf's free edge (left wall)
  // clipboard hugged to the chest (E) → lowered to the waist as they go down on one knee
  const hug = 1 - S.k(t, [['s02b03+6.4', 0], ['s02b03.end', 1]]);
  const tug = pulseEnv(t, S.T('s02b03+2.58'), 0.22, 0.4, 0.3);
  const tugDown = S.k(t, [['s02b03+2.8', 0], ['s02b03+3.1', 1], ['s02b03+3.38', 0]]);
  const exhale = pulseEnv(t, S.T('s02b03+3.55'), 0.15, 0.1, 0.6);
  const ceoPose = {
    t: t + 0.7, outfit: 'ceo', facing: 1, clipboard: true,
    walk: kneel < 0.01 ? { phase: w.phase } : undefined, kneel,
    bodyTurn: lerp(0.4, 0.45, kneel), headTurn: lerp(0.18, 0, kneel) + ceoHeadTurn(S, t) * (τ > 4.6 ? 1 : 0),
    headTilt: lerp(-0.06, 0.08, sstep(5.9, 7.0, τ)) + kneel * 0.04, shrug: 0.2 * (1 - exhale) * (τ < 3.65 ? 1 : 0),
    headDY: exhale * 3,
    face: ceoFace(S, t),
  };
  const anc = selfPoseAnchors(w.x, w.y, w.sc, ceoPose);
  const loc = (p) => selfLocal(w.x, w.y, w.sc, 1, p[0], p[1]);
  const ch = loc(anc.chest), hp = loc(anc.hip);
  ceoPose.armL = { preset: 'holdClipboard', target: [ch[0] - 38 + 18 * (1 - hug), lerp(hp[1] + 40, ch[1] + 28, hug)] };
  // the CEO badge sits on the wearer's left lapel, 2/3 of the way from the neck to the near shoulder
  const ne = loc(anc.neck), sr = loc(anc.shoulderR);
  const badge = [ne[0] + 0.67 * (sr[0] - ne[0]), ne[1] + 0.67 * (sr[1] - ne[1]) + 22];
  if (tug > 0.01) {
    // elbow down at the side, forearm up (foreshortened) to the lapel edge just under the badge; tug it straight
    const rest = [sr[0] + 12, sr[1] + 184];
    const lap = [badge[0] + 4, badge[1] + 34 + 14 * tugDown];
    ceoPose.armR = { target: [lerp(rest[0], lap[0], tug), lerp(rest[1], lap[1], tug)], bend: 1, front: tug > 0.3, hand: tug > 0.5 ? 'grip' : 'rest',
      handAngle: tug > 0.5 ? -Math.PI / 2 - 0.3 : undefined, reach2: lerp(1, 0.55, tug) };
  } else if (kneel > 0) ceoPose.armR = kneeArm(kneel, sr);
  // the CEO comes through the doorway: everything left of the swinging leaf's free edge is still behind it
  // the open doorway is a bright warm source just behind-left of the CEO stepping out of it: a warm rim on the
  // door-side edge plus a little fill, fading as they walk away from it and as the door swings shut. (The leaf clip
  // is applied outside the lit layer, so the rim follows the CEO's silhouette, not the door's edge.)
  const doorLit = door * clamp(1 - (w.x - 190) / 230);
  const ceoBody = (c) => drawSelf(c, w.x, w.y, w.sc, ceoPose);
  const ceoDraw = () => {
    if (!ceoVis) return;
    g.save();
    if (τ < 1.6) { g.beginPath(); g.rect(leafEdge, 0, 2000, 2000); g.clip(); }
    if (doorLit > 0.02) drawLit(g, ceoBody, { dir: [-1, -0.3], color: '#ffd9a0', strength: 0.9 * doorLit, width: 3.4, fill: '#ffcf96', fillAlpha: 0.07 * doorLit });
    else ceoBody(g);
    g.restore();
  };
  // draw by depth: Fear (y 973) behind the CEO (y ≥ 934 → mostly in front)
  if (w.y < FEAR_ALARM_F[1]) { ceoDraw(); fearDraw(); }
  else { fearDraw(); ceoDraw(); }
  // framed in the doorway light: warm outside light wraps the figure as they step through
  if (door > 0.02) {
    g.save(); g.globalCompositeOperation = 'screen';
    const gx = 168, gy = 820, r = 150;
    const gr = g.createRadialGradient(gx, gy, 10, gx, gy, r);
    gr.addColorStop(0, `rgba(255,214,150,${0.22 * door})`); gr.addColorStop(1, 'rgba(255,214,150,0)');
    g.fillStyle = gr; g.fillRect(gx - r, gy - r, 2 * r, 2 * r); g.restore();
  }
  // the badge glints as the lapels are tugged straight
  const glint = pulseEnv(t, S.T('s02b03+3.0'), 0.12, 0.08, 0.35);
  if (glint > 0.01 && ceoVis) {
    const bx = w.x + badge[0] * w.sc, by = w.y + badge[1] * w.sc;
    sparkle(g, bx + 4 * w.sc, by - 3 * w.sc, 26 * w.sc * (0.6 + 0.4 * glint), glint);
  }
  emotionsFront(g, S, t, vis);
  drawHQForeground(g, 'front', st);
  drawAlarmLight(g, 'front', st);
  g.restore();
  grade(g, L.cold, L.warm);
  vignette(g, L.vig);
}
function sparkle(g, x, y, r, a) {
  g.save(); g.globalCompositeOperation = 'lighter';
  const gr = g.createRadialGradient(x, y, 0, x, y, r * 1.6);
  gr.addColorStop(0, `rgba(255,240,190,${0.7 * a})`); gr.addColorStop(1, 'rgba(255,220,140,0)');
  g.fillStyle = gr; g.fillRect(x - r * 1.6, y - r * 1.6, r * 3.2, r * 3.2);
  g.fillStyle = `rgba(255,250,225,${0.95 * a})`;
  g.beginPath();
  for (let i = 0; i < 8; i++) { const ang = i * Math.PI / 4, rr = i % 2 ? r * 0.16 : r; g.lineTo(x + Math.cos(ang) * rr, y + Math.sin(ang) * rr); }
  g.closePath(); g.fill(); g.restore();
}

// H (s02b03.end−0.2 → s02b04+1.3) and G (→ S.end) share one performance in the alarm view; only the camera cuts.
// H: a close on the CEO (Fear's head at the right edge), cut in on the last of the kneel: the eyes come down from the
// bell and land on Fear, the performed composure drains out of the brows and lids, a soft blink, "Fear?".
// G: punch out to the two-shot just before "What are you looking at?" (b04+1.46) — Fear doesn't answer.
const CU_FROM = 's02b03.end-0.2', CU_TO = 's02b04+1.3';
function shotTwo(g, S, t) {
  const L = lightState(S, t), A = alarmState(S, t);
  let c;
  if (t < S.T(CU_TO)) {
    // the CEO's eyes (world ≈ (201,756) kneeling) at screen ≈ (300,520): looking room toward Fear on the right
    // (x ≥ 360/1.5 = 240 keeps the frame on the stage's left edge); a barely-there push
    const k = ease.sine(clamp((t - S.T(CU_FROM)) / (S.T(CU_TO) - S.T(CU_FROM))));
    c = { x: lerp(242, 244, k), y: lerp(838, 832, k), zoom: lerp(1.5, 1.54, k) };
  } else {
    const k = ease.sine(clamp((t - S.T('s02b04+2.6')) / (S.end - S.T('s02b04+2.6'))));
    // (the alarm stage is 1600 tall: keep y ≤ 1600 − 640/zoom so the frame never runs off its bottom edge)
    c = { x: lerp(398, 384, k), y: lerp(956, 986, k), zoom: lerp(1.0, 1.1, k) };
  }
  const st = { t, ...A, lightsDim: L.lightsDim, mist: L.mist };
  g.save();
  cam(g, c, t, 2.2);
  drawHQ(g, 'alarm', st);
  const [fx, fy, fs] = AA.fearAtAlarm;
  const fp = fearPose(S, t);
  drawFear(g, fx, fy, fs, { t, ...fp });
  // CEO kneeling, lip-synced; head tilts to find Fear's eyes; after the line the eyes follow the finger, then the head
  const [cx, cy, cs] = AA.ceoKneel;
  const b4 = 's02b04', e3 = 's02b03.end';
  // H: eyes up-right on the bell (still holding the CEO face: lips pressed) → drop and land on Fear (a small lift of
  // the brows: how small it is) → the performance drains: inner brows up, lids soften → "Fear?"
  const bell = E({ browIn: 0.2, browUp: 0.3, lidU: -0.02, pressed: 0.3, smile: -0.02, lookX: 0.7, lookY: -0.6 });
  const land = E({ browIn: 0.35, browUp: 0.4, lidU: -0.04, pressed: 0.15, smile: -0.05, lookX: 0.6, lookY: 0.45 });
  const soft = E({ browIn: 0.8, browUp: 0.32, lidU: 0.14, lidTilt: 0.22, smile: -0.08, lookX: 0.6, lookY: 0.45 });
  const ask = E({ browIn: 0.6, browUp: 0.4, lidU: 0.02, smile: -0.05, lookX: 0.6, lookY: 0.45 });
  // after "at?" (b04+3.06) the eyes drop (through a blink) to the finger rising beside their shoulder, rest on it,
  // then run up-left along it, over the shoulder; the head follows ~0.25 s later and is most of the way round at
  // the cut (match on action into s03's back view)
  const finger = E({ browIn: 0.55, browUp: 0.5, lidU: 0.1, smile: -0.08, lookX: 0.5, lookY: 0.7 });
  const behind = E({ browIn: 0.7, browUp: 0.6, lidU: -0.14, smile: -0.12, open: 0.06, lookX: -0.8, lookY: -0.65 });
  const face = S.k(t, [[CU_FROM, bell], [`${e3}+0.05`, bell], [`${e3}+0.2`, land], [`${e3}+0.3`, land],
    [`${b4}-0.02`, soft], [`${b4}+0.5`, soft], [`${b4}+0.95`, ask], [`${b4}+3.1`, ask], [`${b4}+3.3`, finger],
    [`${b4}+3.85`, finger], [`${b4}+4.2`, behind]]);
  const said = withSpeech(face, S.lip('CONSCIOUSNESS', t));
  said.blink = Math.max(blinkAt(t, S.T(`${e3}+0.3`), 0.28), blinkAt(t, S.T(`${b4}+1.05`), 0.16), blinkAt(t, S.T(`${b4}+3.1`), 0.16));
  // deliberate blinks only (the close, the line, and the breath that stops after it). A random auto-blink used to
  // land at b04+2.86, 0.24 s before the deliberate one at b04+3.1: a double blink right on the turn to the finger
  said.noAutoBlink = true;
  const turn = S.k(t, [[CU_FROM, 0.42], [`${e3}+0.12`, 0.42], [`${e3}+0.55`, 0.16, 'inOut'], [`${b4}+2.6`, 0.2],
    [`${b4}+4.05`, 0.2], ['scene.end+0.3', -0.75, 'inOut']]);
  const tilt = S.k(t, [[CU_FROM, 0.0], [`${e3}+0.2`, 0.0], [`${b4}+0.1`, 0.1], [`${b4}+1.4`, 0.17], [`${b4}+4.0`, 0.17], ['scene.end', -0.02]]);
  const held = clamp((t - S.T(`${b4}.end+0.05`)) / 0.3);
  const kneel = S.k(t, [['s02b03.end-0.8', 0], ['s02b03.end', 1, 'inOut']]);
  // the out-breath as the composure goes (head and shoulders settle)
  const sigh = pulseEnv(t, S.T(`${e3}+0.35`), 0.3, 0.15, 0.6);
  const ceo = {
    t: t + 0.7, outfit: 'ceo', kneel, facing: 1, clipboard: true, armL: 'rest',
    face: said, headTurn: turn, headTilt: tilt, headDX: 6 * (1 - held), headDY: 4 * sigh,
    breathe: 1 - 0.85 * held + 0.6 * sigh, shrug: 0.12 * held,
  };
  // the far hand rests on the raised knee (it used to hang past the knee, the hand dangling by the front shoe)
  ceo.armR = kneeArm(kneel, selfLocal(cx, cy, cs, 1, ...selfPoseAnchors(cx, cy, cs, ceo).shoulderR));
  drawSelf(g, cx, cy, cs, ceo);
  drawHQForeground(g, 'alarm', st);
  drawAlarmLight(g, 'alarm', st);
  g.restore();
  grade(g, L.cold, L.warm);
  vignette(g, L.vig);
}

// =========================================================================== render
export function render(g, t, S) {
  if (t < S.T('s02b01.end')) return shotBack(g, S, t, 'A'); // A ends at rest, B starts from rest (sine)
  if (t < S.T('s02b02+1.0')) return shotBack(g, S, t, 'B');
  if (t < S.T('s02b02+2.8')) return shotAlarmPull(g, S, t);
  if (t < S.T('s02b03+0.45')) return shotBack(g, S, t, 'D');
  if (t < S.T('s02b03+4.70')) return shotFront(g, S, t, 'E');
  if (t < S.T(CU_FROM)) return shotFront(g, S, t, 'F');
  return shotTwo(g, S, t); // H (CEO close) → G (two-shot)
}

// =========================================================================== sound
if (!timeline()) loadTimeline();
function computeSfx() {
  const out = [
    { at: 's02b01+0.05', name: 'console_beeps', gain: -20, pan: -0.3 },
    { at: 's02b01+1.1', name: 'console_beeps', gain: -22, pan: 0.25, rate: 0.94 },
    // the pull station and bell are screen-right in the pull shot and in every front/alarm shot after it
    { at: 's02b02+2.345', name: 'alarm_pull', gain: -8, pan: 0.35 },
    { at: 's02b02+2.45', name: 'alarm_bell', until: 's02b04+2.2', fade: 1.6, gain: -20, loop: true, pan: 0.2 },
    { at: 's02b03-0.05', name: 'door_whoosh', gain: -14, pan: -0.5 },
    { at: 's02b03+1.9', name: 'door_whoosh', gain: -19, pan: -0.55, rate: 0.92 }, // swings shut behind them (thud)
    { at: 's02b03+2.55', name: 'cloth_rustle', gain: -17 },
    { at: 's02b03.end-0.8', name: 'cloth_rustle', gain: -16, pan: 0.2 },
    { at: 's02b04+2.3', name: 'alarm_pull', gain: -16, pan: 0.3, rate: 0.85 },
    { at: 's02b04+2.75', name: 'cloth_rustle', gain: -22, pan: 0.2 },
  ];
  // footsteps: one soft step per footfall of the CEO's walk (cut from the 4-step file)
  try {
    const sc = timeline().scenes.find((s) => s.id === 's02');
    const S = { start: sc.start, T: (a) => resolveAnchor(a, sc) };
    for (const τ of stepTimes(S)) out.push({ at: `s02b03+${(τ - 0.08).toFixed(3)}`, name: 'footsteps', until: `s02b03+${(τ + 0.4).toFixed(3)}`, fade: 0.12, gain: -15, pan: -0.4 + 0.1 * τ });
  } catch (e) { /* timeline unavailable: no footsteps */ }
  return out;
}
export const sfx = computeSfx();
