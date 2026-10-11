// s07 · time_out · MIND_HQ, `alarm` view (cut from s06: same place, same moment)
// Consciousness puts the CEO back on. "Fear, we need to put you in a time-out." Fear hears exactly what it means.
// Shots (data/staging.md §3 s07): low wide (rise) → close Fear (its name) → close CEO (the line) → close Fear (reaction).
import { clamp, lerp, ease, blinkAt, applyCamera, drift, vignette, TAU } from '../engine.mjs';
import { EXPR, makeExpr, withSpeech } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, selfLocal } from '../chars/self.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, HQ_VIEWS, ALARM_REACH } from '../sets/hq.mjs';

export const id = 's07';

export const sfx = [
  { at: 's07b01-0.25', name: 'cloth_rustle', gain: -16, pan: -0.3 },            // Consciousness rises from the knee
  { at: 's07b01+0.2', name: 'breath_shaky', until: 's07b02', fade: 0.12, gain: -20, pan: -0.25 }, // the in-breath, held
  { at: 'scene.start+1.15', name: 'cloth_rustle', gain: -19, pan: -0.3 },       // tugs the blazer straight
  { at: 's07b02+0.25', name: 'alarm_pull', gain: -17, pan: 0.3 },               // hands off: the handle springs back up
  { at: 's07b02+0.38', name: 'cloth_rustle', gain: -22, pan: 0.25 },            // Fear turns around
];

const AA = HQ_VIEWS.alarm.anchors;
const [FX, FY, FS] = AA.fearAtAlarm;   // 498, 1406, 1.8
const [CX, CY, CS] = AA.ceoKneel;      // 135, 1520, 2.091
const KNEE = [100, -150];

const X = (...p) => makeExpr(...p);
const sine = (k) => ease.sine(clamp(k));

function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function cam(g, c, t, amp = 2.5) {
  const d = drift(t, amp, 6);
  applyCamera(g, { ...c, shakeX: d.dx, shakeY: d.dy, rot: d.dr * 0.5 });
}
function camK(S, t, keys) {
  const c = S.k(t, keys.map(([a, v, e]) => [a, { x: v.x, y: v.y, lz: Math.log(v.zoom) }, e]));
  return { x: c.x, y: c.y, zoom: Math.exp(c.lz) };
}

function look(t, S) {
  return {
    alarm: S.k(t, [['scene.start', 1], ['s07b02', 0, 'inOut']]),
    pulled: S.k(t, [['s07b02+0.15', 1], ['s07b02+0.4', 0, 'out']]),
    lightsDim: 0.35, cold: 0.5, vig: 0.45,
  };
}

// ------------------------------------------------------------------ CONSCIOUSNESS: rises, puts the CEO back on
function ceoPose(t, S) {
  const lip = S.lip('CONSCIOUSNESS', t);
  const kneel = 1 - sine((t - S.T('scene.start+0.22')) / 1.12);
  // tug the blazer straight (both hands on the lapels, a short pull down), then hands to the sides
  const tugIn = sine((t - S.T('scene.start+1.12')) / 0.24);
  const tugPull = sine((t - S.T('scene.start+1.38')) / 0.18);
  const tugOut = sine((t - S.T('scene.start+1.62')) / 0.3);
  const tug = tugIn * (1 - tugOut);
  const lap = (side) => [side * 26, -312 + 16 * tugPull];
  const restR = [58 + 14, -382 + 184], restL = [-72, -198];
  const pushOff = sine((t - S.T('scene.start+0.2')) / 0.9);  // the fist leaves the knee as they rise
  const baseR = [lerp(KNEE[0], restR[0], pushOff), lerp(KNEE[1], restR[1], pushOff)];
  const tugStarted = t >= S.T('scene.start+1.12');
  let armR, armL;
  if (!tugStarted) {
    // = s06's last pose (fist on the knee), then the arm comes down to the side as they rise
    armR = { preset: 'onShoulder', target: baseR, shake: 0.12 * (1 - pushOff), hand: pushOff < 0.55 ? 'fist' : 'rest',
      wrist: lerp(0.75, 0.1, pushOff), front: pushOff < 0.7 };
    armL = 'rest';
  } else if (tug > 0.001) {
    armR = { target: [lerp(restR[0], lap(1)[0], tug), lerp(restR[1], lap(1)[1], tug)], bend: 1, front: true, hand: tug > 0.5 ? 'grip' : 'rest' };
    armL = { target: [lerp(restL[0], lap(-1)[0], tug), lerp(restL[1], lap(-1)[1], tug)], bend: -1, front: true, hand: tug > 0.5 ? 'grip' : 'rest' };
  } else {
    armR = { preset: 'rest' }; armL = 'rest';
  }
  // after the line: the hands close at the sides
  const fists = S.k(t, [['s07b03+1.3', 0], ['s07b03+1.6', 1]]);
  if (fists > 0.5 && tug <= 0.001 && tugStarted) { armR = { preset: 'rest', hand: 'fist' }; armL = { preset: 'rest', hand: 'fist' }; }

  const atFearKneel = { lookX: 0.6, lookY: 0.42 };
  const atFear = { lookX: 0.55, lookY: 0.72 };   // standing: Fear is further down-right
  const sadDown = X(SELF_EXPR.sad, { browIn: 0.9, browSquish: 0.3, lidU: 0.28, lidTilt: 0.5, tears: 0.7, pressed: 0.25, smile: -0.35, lookX: 0.28, lookY: 0.62 });
  const ceoOn = X(SELF_EXPR.sternKind, { browIn: 0.05, browSquish: 0.45, lidU: 0.1, lidTilt: 0.12, tears: 0.6, pressed: 0.5, smile: -0.06, ...atFear });
  let face = S.k(t, [
    ['scene.start', sadDown],
    ['scene.start+0.35', X(sadDown, { open: 0.1, pressed: 0 })],          // a long exhale
    ['s07b01+0.15', X(sadDown, { open: 0.03, pressed: 0.1, lidU: 0.22 })],
    // rising: the face hardens only slightly; the eyes stay wet
    ['s07b01+0.75', X(SELF_EXPR.resolve, { browIn: 0.2, browSquish: 0.35, lidU: 0.18, lidTilt: 0.25, tears: 0.65, pressed: 0.45, ...atFear })],
    ['s07b01+1.2', ceoOn],
    ['s07b02-0.05', ceoOn],
    // "Fear," (the held breath released on the word)
    ['s07b02+0.8', X(ceoOn, { pressed: 0.3, browIn: 0.15 })],
    ['s07b03', X(ceoOn, { pressed: 0.3, browIn: 0.15 })],
    // "we need to put you in a time-out." — holds the gaze until 'time-out', then the eyes flick down and away
    ['s07b03+1.28', X(ceoOn, { pressed: 0.2, browIn: 0.25, browSquish: 0.5 })],
    ['s07b03+1.4', X(ceoOn, { pressed: 0.2, browIn: 0.35, browSquish: 0.5, lidU: 0.25, lookX: -0.12, lookY: 0.88 }), 'out'],
    ['s07b03+1.78', X(ceoOn, { pressed: 0.2, browIn: 0.35, browSquish: 0.5, lidU: 0.25, lookX: -0.12, lookY: 0.88 })],
    ['s07b03+1.95', X(ceoOn, { pressed: 0.2, browIn: 0.3, ...atFear })],
    // after the line: lids lower, lips press flat
    ['s07b03+2.12', X(ceoOn, { pressed: 0.3, browIn: 0.3, ...atFear })],
    ['s07b03+2.45', X(ceoOn, { pressed: 0.95, smile: -0.14, browIn: 0.5, lidU: 0.42, lidTilt: 0.32, tears: 0.72, tremble: 0.25, ...atFear })],
    ['scene.end', X(ceoOn, { pressed: 0.95, smile: -0.14, browIn: 0.55, lidU: 0.45, lidTilt: 0.34, tears: 0.75, tremble: 0.3, ...atFear })],
  ]);
  face = { ...face };
  // the eyes follow Fear as the head rises (kneeling eyeline → standing eyeline)
  face.noAutoBlink = t > S.T('s07b02-0.4') && t < S.T('s07b03+1.2');
  face.blink = blinkAt(t, S.T('s07b01+1.0'), 0.36);          // resolve: a slow blink as they straighten
  face = withSpeech(face, lip, 0.8);
  const chinUp = sine((t - S.T('s07b01+0.95')) / 0.35);
  const dip = (a, dur, amp) => { const k = clamp((t - S.T(a)) / dur); return Math.sin(k * Math.PI) * amp; };
  const headDY = S.k(t, [['scene.start', 10], ['scene.start+0.6', 6]]) * (1 - chinUp) - chinUp * 5 + dip('s07b03+1.3', 0.5, 4);
  // inhale through the nose and hold it; release it on the word
  const shrug = S.k(t, [['scene.start', 0], ['scene.start+0.5', 0], ['s07b01+0.85', 0], ['s07b02-0.05', 0.38], ['s07b02+0.35', 0.08], ['s07b03+2.2', 0.05], ['s07b03+2.6', 0.18]]);
  const breathe = S.k(t, [['s07b01+0.9', 1], ['s07b01+1.1', 0.15], ['s07b02', 0.15], ['s07b02+0.3', 1]]);
  const headTilt = S.k(t, [['scene.start', 0.06], ['s07b01+0.9', 0.04], ['s07b01+1.3', -0.02], ['s07b03', 0.03]]);
  const headTurn = S.k(t, [['s07b01+0.6', 0.2], ['s07b01+1.2', 0.14], ['s07b03+1.3', 0.14], ['s07b03+1.45', 0.02], ['s07b03+1.9', 0.12]]);
  return { t, outfit: 'ceo', kneel, facing: 1, face, headDY, headTilt, headTurn, shrug, breathe, armR, armL, lean: S.k(t, [['s07b01+1.0', 0], ['s07b01+1.3', -0.015]]) };
}

// ------------------------------------------------------------------ FEAR: clinging → frozen at its name → turns → betrayed
function fearPose(t, S, L) {
  const handleY = ALARM_REACH[1] + 26 * L.pulled;
  const turnK = clamp((t - S.T('s07b02+0.32')) / 0.3);       // facing 1 → -1
  const facing = turnK < 0.5 ? 1 : -1;
  const squash = turnK > 0 && turnK < 1 ? 1 - 0.22 * Math.sin(turnK * Math.PI) : 1;
  const crouch = S.k(t, [['scene.start', 0.38], ['s07b01+0.4', 0.3], ['s07b02+0.1', 0.26], ['s07b02+0.55', 0.02, 'out']]);
  const tremble = S.k(t, [['scene.start', 0.5], ['s07b01+0.75', 0.5], ['s07b01+0.95', 0], ['s07b03.end+0.2', 0], ['s07b03.end+0.5', 0.35]]);
  // arms
  const off = sine((t - S.T('s07b02+0.15')) / 0.28);           // hands come off the handle
  const palms = S.k(t, [['s07b03.end+0.3', 0], ['s07b03.end+0.55', 1, 'out'], ['s07b03.end+0.8', 1], ['s07b03.end+1.1', 0, 'inOut']]);
  let armL, armR;
  if (facing > 0) {
    // the hands let go and FALL: each target swings down on an arc around its own shoulder at near-full arm length,
    // so the elbows never fold up into an "M" (the old straight lerp passed right next to the shoulders)
    const sy = -134 + crouch * 18;
    const swing = (sx, tx, ty, aEnd) => {
      const a0 = Math.atan2(ty - sy, tx - sx), r0 = Math.min(88, Math.hypot(tx - sx, ty - sy));
      const a = lerp(a0, aEnd, off), r = lerp(r0, 70, off);
      return [sx + Math.cos(a) * r, sy + Math.sin(a) * r];
    };
    armR = { target: swing(27, ALARM_REACH[0], handleY, 1.2), bend: -1, front: true, hand: off > 0.35 ? 'open' : 'grip' };
    armL = { target: swing(-27, 80, handleY + 8, 1.95), bend: -1, front: true, hand: off > 0.35 ? 'open' : 'grip' };
  } else {
    // arms hanging where they fell (mirrored across the flip so the hands do not jump), stiffening at its sides;
    // then palms up and out ("why?"), then they drop
    const k = sine((t - S.T('s07b02+0.55')) / 0.4);
    const side = (sd) => {
      const tg = [lerp(sd * 44, sd * 36, k), lerp(-66, -84, k)];
      return { target: [lerp(tg[0], sd * 62, palms), lerp(tg[1], -150, palms)], bend: palms > 0.3 ? -sd : -sd, front: palms > 0.3, hand: palms > 0.3 ? 'palm' : 'open' };
    };
    armL = side(-1); armR = side(1);
  }
  // face
  const peek = { lookX: -0.62, lookY: -0.42 };                 // the kneeling CEO's face
  const upCeo = { lookX: -0.5, lookY: -0.86 };                 // the standing CEO's face
  const shut = X(EXPR.terrified, { lidU: 1, lidL: 0.6, browIn: 1, browUp: 0.3, open: 0.2, wide: 0.5, teeth: 0.6, smile: -0.6, tears: 0.85 });
  let face = S.k(t, [
    ['scene.start', shut],
    ['scene.start+0.12', X(EXPR.scared, { lidU: 0.2, browIn: 1, browUp: 0.5, smile: -0.5, open: 0.08, tears: 0.85, ...peek })],
    ['scene.start+0.4', X(EXPR.scared, { lidU: 0, browIn: 1, browUp: 0.5, smile: -0.5, open: 0.04, tears: 0.85, ...peek })],
    ['s07b01+0.1', X(EXPR.scared, { lidU: 0, browIn: 1, browUp: 0.5, smile: -0.5, open: 0.04, tears: 0.85, ...peek })],
    // reading the face as it rises: the eyes widen with dawning dread
    ['s07b01+0.9', X(EXPR.scared, { lidU: -0.32, browIn: 1, browUp: 0.8, smile: -0.45, open: 0.06, pupil: 0.66, tears: 0.8, ...upCeo })],
    ['s07b02', X(EXPR.scared, { lidU: -0.32, browIn: 1, browUp: 0.8, smile: -0.45, open: 0.04, pupil: 0.66, tears: 0.8, ...upCeo })],
    // its own name: frozen
    ['s07b02+0.2', X(EXPR.terrified, { lidU: -0.42, browIn: 1, browUp: 0.7, smile: -0.4, open: 0.02, wide: 0.1, teeth: 0, tremble: 0, pupil: 0.58, tears: 0.8, ...upCeo }), 'out'],
    ['s07b03.end', X(EXPR.terrified, { lidU: -0.38, browIn: 1, browUp: 0.68, smile: -0.4, open: 0.02, wide: 0.1, teeth: 0, tremble: 0, pupil: 0.6, tears: 0.8, ...upCeo })],
    // betrayed disbelief: mouth falls open, brows shoot up and apart, the lower lids rise
    ['s07b03.end+0.28', X({ browUp: 1, browIn: 0.25, lidU: -0.14, lidL: 0.55, open: 0.62, round: 0.3, smile: -0.35, pupil: 0.75, tears: 0.88, ...upCeo }), 'out'],
    ['scene.end', X({ browUp: 0.95, browIn: 0.4, lidU: -0.08, lidL: 0.5, open: 0.48, round: 0.22, smile: -0.4, pupil: 0.78, tears: 0.92, lookX: -0.48, lookY: -0.84 })],
  ]);
  face = { ...face };
  face.noAutoBlink = t > S.T('s07b01+0.3');
  face.blink = blinkAt(t, S.T('s07b01+0.18'), 0.18);          // one blink before the dread sets in
  const shake = (() => { const k = clamp((t - S.T('s07b03.end+0.3')) / 0.85); return Math.sin(k * TAU) * 0.17 * Math.sin(k * Math.PI); })();
  const headTurn = facing > 0 ? S.k(t, [['scene.start', -0.1], ['scene.start+0.4', -0.28]]) : shake;
  const headDY = S.k(t, [['s07b02', 0], ['s07b02+0.15', -5, 'out'], ['s07b02+0.8', -3], ['s07b03.end', -3], ['s07b03.end+0.25', 2, 'out']]);
  const breathe = S.k(t, [['s07b02', 1], ['s07b02+0.2', 0.2], ['s07b03.end+0.1', 0.2], ['s07b03.end+0.4', 1.2]]);
  return { t, face, facing, crouch, tremble, armL, armR, headTurn, headDY, headTilt: facing > 0 ? -0.05 : 0, squash, breathe, lean: facing > 0 ? S.k(t, [['scene.start', 0.08], ['s07b02+0.2', 0.03]]) : 0 };
}

function drawFearAt(g, F) {
  g.save();
  if (F.squash !== 1) { g.translate(FX, 0); g.scale(F.squash, 1); g.translate(-FX, 0); }
  drawFear(g, FX, FY, FS, F);
  g.restore();
}

function shot(g, t, S, L, c, amp) {
  const st = { t, lightsDim: L.lightsDim, consoleGlow: 0.8, mist: 0.4, alarm: L.alarm, alarmPulled: L.pulled, screenMode: 'room' };
  g.save(); cam(g, c, t, amp);
  drawHQ(g, 'alarm', st);
  drawFearAt(g, fearPose(t, S, L));
  drawSelf(g, CX, CY, CS, ceoPose(t, S));
  drawHQForeground(g, 'alarm', st);
  drawAlarmLight(g, 'alarm', st);
  g.restore();
}

export function render(g, t, S) {
  const L = look(t, S);
  const T = (a) => S.T(a);
  if (t < T('s07b02')) {
    // low angle, locked-ish: Consciousness rises; tiny Fear at the alarm looks up; the red pulse fades out
    shot(g, t, S, L, S.k(t, [['scene.start', { x: 420, y: 860, zoom: 0.8 }], ['s07b02', { x: 420, y: 852, zoom: 0.81 }]]), 1);
  } else if (t < T('s07b03')) {
    shot(g, t, S, L, camK(S, t, [['s07b02', { x: 536, y: 1000, zoom: 1.9 }], ['s07b03', { x: 532, y: 996, zoom: 1.96 }]]), 1.6);
  } else if (t < T('s07b03.end')) {
    shot(g, t, S, L, camK(S, t, [['s07b03', { x: 178, y: 552, zoom: 1.6 }], ['s07b03.end', { x: 174, y: 548, zoom: 1.7 }]]), 1.6);
  } else {
    shot(g, t, S, L, camK(S, t, [['s07b03.end', { x: 536, y: 1000, zoom: 1.9 }], ['scene.end', { x: 534, y: 998, zoom: 1.95 }]]), 1.6);
  }
  grade(g, L.cold, 0);
  vignette(g, L.vig);
}
