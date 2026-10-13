// s07 · time_out · MIND_HQ, `alarm` view (cut from s06: same place, same moment)
// Consciousness puts the CEO back on. "Fear, we need to put you in a time-out." Fear hears exactly what it means.
// Shots (data/staging.md §3 s07): low wide (rise) → close Fear (its name) → close CEO (the line) → close Fear (betrayed:
// brows up and apart, one slow head shake, the hands drop) → close CEO (seeing it; the eyes drop). The last two use the
// 1.7 s of silence added after s07b03.
import { clamp, lerp, ease, blinkAt, applyCamera, drift, vignette, TAU } from '../engine.mjs';
import { EXPR, makeExpr, withSpeech } from '../face.mjs';
import { blendHand } from '../hand.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, selfLocal, selfPoseAnchors } from '../chars/self.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, HQ_VIEWS, ALARM_REACH } from '../sets/hq.mjs';

export const id = 's07';

export const sfx = [
  { at: 's07b01-0.25', name: 'cloth_rustle', gain: -16, pan: -0.3 },            // Consciousness rises from the knee
  { at: 's07b01+0.2', name: 'breath_shaky', until: 's07b02', fade: 0.12, gain: -20, pan: -0.25 }, // the in-breath, held
  { at: 'scene.start+1.15', name: 'cloth_rustle', gain: -19, pan: -0.3 },       // tugs the blazer straight
  { at: 's07b02+0.25', name: 'alarm_pull', gain: -17, pan: 0.3 },               // hands off: the handle springs back up
  { at: 's07b02+0.38', name: 'cloth_rustle', gain: -22, pan: 0.25 },            // Fear turns around
  { at: 's07b03.end+0.12', name: 'breath_shaky', until: 's07b03.end+1.05', fade: 0.35, gain: -23, pan: 0.2 }, // Fear's caught breath as the betrayed face forms
];

const AA = HQ_VIEWS.alarm.anchors;
const [FX, FY, FS] = AA.fearAtAlarm;   // 498, 1406, 1.8
const [CX, CY, CS] = AA.ceoKneel;      // 135, 1520, 2.091
const KNEE = [100, -150];
const CUT_CEO = 's07b03.end+1.88';   // Fear's reaction → Consciousness's reaction (right out of Fear's slow blink)

const X = (...p) => makeExpr(...p);
const sine = (k) => ease.sine(clamp(k));
// the narrator sheds no tear before the last scene: the CEO's lower lids only glisten (tears ≤ 0.35), keeping the
// build-up of the beat's welling (.6 → .26, .85 → .32, 1 → .35)
const glisten = (x) => 0.35 * Math.pow(clamp(x || 0), 0.6);
// Fear's fist ON the alarm handle (as in s06's yank): wrist `d` px back from the covered point along the hand angle,
// in Fear's body frame (drawFear rotates arms with `lean`); `dx` = feet offset from FX (local px)
function onHandle(px, py, ang, lean, dx = 0, d = 8) {
  const x = px - d * Math.cos(ang) - dx, y = py - d * Math.sin(ang);
  const c = Math.cos(-lean), s = Math.sin(-lean);
  return { target: [x * c - y * s, x * s + y * c], handAng: ang - lean };
}
const YANK_DX = 15;   // = s06: Fear stepped in to the station for the yank; it steps back as it turns round

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
  // each fist closes on its own lapel (knuckles to camera, fingers round the lapel edge toward the sweater): the
  // wrists sit outside the lapels so the fists land on them (at ±26 the two fists met in the middle of the chest
  // and read as clasped hands)
  const lap = (side) => [side * 60, -300 + 16 * tugPull];
  const lapAng = (side) => (side > 0 ? Math.PI + 0.55 : -0.55);   // the fist points in and up along the lapel edge
  const restR = [58 + 14, -382 + 184], restL = [-72, -198];
  const pushOff = sine((t - S.T('scene.start+0.2')) / 0.9);  // the fist leaves the knee as they rise
  const baseR = [lerp(KNEE[0], restR[0], pushOff), lerp(KNEE[1], restR[1], pushOff)];
  const tugStarted = t >= S.T('scene.start+1.12');
  let armR, armL;
  if (!tugStarted) {
    // = s06's last pose (fist on the knee), then the arm comes down to the side as they rise
    // (foreshortened on the knee as at the end of s06, the arm lengthening as it comes off: no "<" fold across the
    // jacket front on the way up)
    armR = { preset: 'onShoulder', target: baseR, shake: 0.12 * (1 - pushOff), hand: pushOff < 0.55 ? 'fist' : 'rest',
      wrist: lerp(0.75, 0.1, pushOff), front: pushOff < 0.7 };   // bend / reach: set below (elbowThrough)
    armL = 'rest';
  } else if (tug > 0.001) {
    // the hand turns from hanging (fingers down, palm to the thigh) to the lapel grip through the whole move, so it
    // never flips in one frame
    const hold = (side) => ({ hand: blendHand('rest', 'grip', tug), handAngle: lerp(Math.PI / 2 - side * 0.1, lapAng(side), tug),
      palmDir: [lerp(-side * 0.9, 0, tug), 0, lerp(-0.45, -1, tug)] });
    armR = { target: [lerp(restR[0], lap(1)[0], tug), lerp(restR[1], lap(1)[1], tug)], bend: 1, front: true, ...hold(1) };
    armL = { target: [lerp(restL[0], lap(-1)[0], tug), lerp(restL[1], lap(-1)[1], tug)], bend: -1, front: true, ...hold(-1) };
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
    // (off-screen while Fear's face changes: holding the hard face)
    ['s07b03.end+1.8', X(ceoOn, { pressed: 0.95, smile: -0.14, browIn: 0.55, lidU: 0.42, lidTilt: 0.34, tears: 0.75, tremble: 0.3, ...atFear })],
    // REACTION to Fear's betrayed face (the cut lands on it): the sternness breaks: inner brows go up, the lids lift
    // (they really see it), the pressed mouth loosens for a breath...
    ['s07b03.end+2.12', X(SELF_EXPR.worried, { browIn: 0.95, browUp: 0.3, browSquish: 0.35, lidU: 0.08, lidL: 0.05, lidTilt: 0.42, tears: 0.85,
      pressed: 0.35, open: 0.05, smile: -0.22, tremble: 0.35, ...atFear }), 'out'],
    // ...then the lips press hard against it, the chin trembles, a swallow...
    ['s07b03.end+2.45', X(SELF_EXPR.holdingBackTears, { browIn: 0.95, browSquish: 0.55, lidU: 0.16, lidL: 0.12, lidTilt: 0.45, tears: 0.95,
      pressed: 1, smile: -0.3, tremble: 0.6, ...atFear })],
    // ...and after a slow blink the eyes cannot hold Fear's: they drop, down and a little away
    ['s07b03.end+2.68', X(SELF_EXPR.holdingBackTears, { browIn: 0.9, browSquish: 0.55, lidU: 0.34, lidL: 0.12, lidTilt: 0.48, tears: 0.95,
      pressed: 0.95, smile: -0.3, tremble: 0.5, lookX: 0.12, lookY: 0.95 })],
    ['scene.end+0.4', X(SELF_EXPR.holdingBackTears, { browIn: 0.9, browSquish: 0.5, lidU: 0.36, lidL: 0.12, lidTilt: 0.48, tears: 0.95,
      pressed: 0.95, smile: -0.3, tremble: 0.45, lookX: 0.1, lookY: 0.95 })],
  ]);
  face = { ...face, tears: glisten(face.tears) };
  // the eyes follow Fear as the head rises (kneeling eyeline → standing eyeline)
  face.noAutoBlink = t > S.T('s07b02-0.4') && t < S.T('s07b03+1.2') || t > S.T('s07b03.end+1.4');
  face.blink = blinkAt(t, S.T('s07b01+1.0'), 0.36)           // resolve: a slow blink as they straighten
    + blinkAt(t, S.T('s07b03.end+2.5'), 0.4);                  // the reaction: a slow blink, the eyes come out of it lowered
  face = withSpeech(face, lip, 0.8);
  const chinUp = sine((t - S.T('s07b01+0.95')) / 0.35);
  const dip = (a, dur, amp) => { const k = clamp((t - S.T(a)) / dur); return Math.sin(k * Math.PI) * amp; };
  // the reaction: a tiny recoil (head back/up), the swallow, then the head lowers a little with the eyes
  const headDY = S.k(t, [['scene.start', 10], ['scene.start+0.6', 6]]) * (1 - chinUp) - chinUp * 5 + dip('s07b03+1.3', 0.5, 4)
    + S.k(t, [['s07b03.end+1.95', 0], ['s07b03.end+2.12', -3, 'out'], ['s07b03.end+2.35', -2], ['s07b03.end+2.9', 3]]) + dip('s07b03.end+2.3', 0.4, 4);
  // inhale through the nose and hold it; release it on the word; a caught breath at the reaction
  const shrug = S.k(t, [['scene.start', 0], ['scene.start+0.5', 0], ['s07b01+0.85', 0], ['s07b02-0.05', 0.38], ['s07b02+0.35', 0.08], ['s07b03+2.2', 0.05], ['s07b03+2.6', 0.18],
    ['s07b03.end+1.95', 0.18], ['s07b03.end+2.15', 0.3, 'out'], ['s07b03.end+2.8', 0.12]]);
  const breathe = S.k(t, [['s07b01+0.9', 1], ['s07b01+1.1', 0.15], ['s07b02', 0.15], ['s07b02+0.3', 1]]);
  const headTilt = S.k(t, [['scene.start', 0.06], ['s07b01+0.9', 0.04], ['s07b01+1.3', -0.02], ['s07b03', 0.03], ['s07b03.end+1.95', 0.03], ['s07b03.end+2.2', 0.0], ['s07b03.end+2.9', 0.05]]);
  const headTurn = S.k(t, [['s07b01+0.6', 0.2], ['s07b01+1.2', 0.14], ['s07b03+1.3', 0.14], ['s07b03+1.45', 0.02], ['s07b03+1.9', 0.12],
    ['s07b03.end+2.5', 0.12], ['s07b03.end+2.95', 0.04]]);                                   // turns a little away
  const pose = { t, outfit: 'ceo', kneel, facing: 1, face, headDY, headTilt, headTurn, shrug, breathe, armR, armL, lean: S.k(t, [['s07b01+1.0', 0], ['s07b01+1.3', -0.015]]) };
  if (!tugStarted) Object.assign(armR, elbowThrough(pose, armR.target, pushOff));
  return pose;
}
// The rising arm's elbow changes sides: on the knee (= s06's last frame) it points in and toward the camera
// (foreshortened, bend −1); hanging at the side, and for the lapel tug, it points out (bend +1). Flipping `bend` on
// a bent arm pops the elbow across the body (it did, at the tug), so the arm first straightens (its bones shortened
// to just under the shoulder→wrist distance: a straight, foreshortened arm, where both bends coincide), flips there,
// and lengthens again with the elbow out.
function elbowThrough(pose, target, p) {
  const A = selfPoseAnchors(CX, CY, CS, pose);
  const [sx, sy] = selfLocal(CX, CY, CS, 1, ...A.shoulderR);
  const dt = Math.hypot(target[0] - sx, target[1] - sy);
  const dw = Math.max(40, dt - 17 * 1.42);                     // onShoulder lands the palm: the wrist sits back
  const rS = Math.min(1, (0.985 * dw) / 192);                  // straight (L1 + L2 = 192 at reach 1)
  // (after the flip the arm stays straight as the body rises (rS grows with the distance) and only takes its full
  // length, the elbow just off the side, at the very end: lengthened early it stuck out akimbo)
  const a = clamp(p / 0.45), b = clamp((p - 0.8) / 0.2);
  if (p < 0.45) return { bend: -1, reach1: lerp(0.66, rS, sine(a)), reach2: lerp(0.6, rS, sine(a)) };
  return { bend: 1, reach1: lerp(rS, 1, sine(b)), reach2: lerp(rS, 1, sine(b)) };
}

// ------------------------------------------------------------------ FEAR: clinging → frozen at its name → turns → betrayed
function fearPose(t, S, L) {
  const handleY = ALARM_REACH[1] + 26 * L.pulled;
  const turnK = clamp((t - S.T('s07b02+0.32')) / 0.3);       // facing 1 → -1
  const facing = turnK < 0.5 ? 1 : -1;
  const squash = turnK > 0 && turnK < 1 ? 1 - 0.22 * Math.sin(turnK * Math.PI) : 1;
  const crouch = S.k(t, [['scene.start', 0.38], ['s07b01+0.4', 0.3], ['s07b02+0.1', 0.26], ['s07b02+0.55', 0.02, 'out'],
    ['s07b03.end+1.45', 0.02], ['s07b03.end+1.95', 0.1]]);                // the body gives a little as the hands drop
  // betrayed disbelief is STILL (shock), the shiver only creeps back as the hands drop
  const tremble = S.k(t, [['scene.start', 0.5], ['s07b01+0.75', 0.5], ['s07b01+0.95', 0], ['s07b03.end+1.4', 0], ['s07b03.end+1.9', 0.3]]);
  // arms
  const off = sine((t - S.T('s07b02+0.15')) / 0.28);           // hands come off the handle
  // "why?": the open hands lift slowly to waist height (not a flick), hold through the head shake, then fall
  const palms = S.k(t, [['s07b03.end+0.35', 0], ['s07b03.end+0.9', 1, 'inOut'], ['s07b03.end+1.42', 1], ['s07b03.end+1.85', 0, 'inOut']]);
  let armL, armR;
  const lean = facing > 0 ? S.k(t, [['scene.start', 0.08], ['s07b02+0.2', 0.03]]) : 0;
  const dx = YANK_DX * (1 - sine((t - S.T('s07b02+0.2')) / 0.45));
  if (facing > 0) {
    // both fists on the pulled handle (= s06's last frame); the hands let go and FALL: each target swings down on an
    // arc around its own shoulder at near-full arm length, so the elbows never fold up into an "M" (the old straight
    // lerp passed right next to the shoulders)
    const sy = -134 + crouch * 18;
    const swing = (sx, tx, ty, aEnd) => {
      const a0 = Math.atan2(ty - sy, tx - sx), r0 = Math.min(88, Math.hypot(tx - sx, ty - sy));
      const a = lerp(a0, aEnd, off), r = lerp(r0, 70, off);
      return [sx + Math.cos(a) * r, sy + Math.sin(a) * r];
    };
    const hR = onHandle(ALARM_REACH[0] + 12, handleY, -1.15, lean, dx), hL = onHandle(ALARM_REACH[0] - 14, handleY + 1, -1.3, lean, dx);
    armR = { target: swing(27, ...hR.target, 1.2), bend: -1, front: true, hand: off > 0.35 ? 'open' : 'grip', handAng: lerp(hR.handAng, Math.PI / 2 - 0.35, off) };
    armL = { target: swing(-27, ...hL.target, 1.95), bend: -1, front: true, hand: off > 0.35 ? 'open' : 'grip', handAng: lerp(hL.handAng, Math.PI / 2 + 0.35, off) };
  } else {
    // arms hanging where they fell (mirrored across the flip so the hands do not jump), stiffening at its sides;
    // then palms up and out ("why?"), then they drop
    const k = sine((t - S.T('s07b02+0.55')) / 0.4);
    const side = (sd) => {
      const tg = [lerp(sd * 44, sd * 36, k), lerp(-66, -84, k)];
      // the arms stay BEHIND the body through the lift and the drop: the forearms come out at the hips, palms open.
      // (Drawn in front, the elbows crossed over the belly in an "X" on the way up and down: the IK elbow sits on the
      // body's centre line until the hands are nearly out.)
      return { target: [lerp(tg[0], sd * 70, palms), lerp(tg[1], -98, palms)], bend: -sd, front: false, hand: palms > 0.3 ? 'palm' : 'open' };
    };
    armL = side(-1); armR = side(1);
  }
  // face
  const peek = { lookX: -0.62, lookY: -0.42 };                 // the kneeling CEO's face
  const upCeo = { lookX: -0.5, lookY: -0.86 };                 // the standing CEO's face
  const shut = X(EXPR.terrified, { lidU: 1, lidL: 0.6, browIn: 1, browUp: 0.3, open: 0.2, wide: 0.5, teeth: 0.6, smile: -0.6, tears: 0.85 });
  // BETRAYED: brows up and apart, lower lids up, jaw dropped, eyes level on Consciousness (not rolled up)
  const BETRAYED_LOOK = { lookX: -0.78, lookY: -0.5 };
  const BETRAYED = X({ browUp: 1, browIn: 0, browSquish: 0, lidU: 0, lidL: 0.4, lidTilt: 0.1, open: 0.4, round: 0.2, wide: -0.05,
    smile: -0.35, pupil: 0.78, tears: 0.9, ...BETRAYED_LOOK });
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
    // 'time-out' lands; a beat of nothing, then BETRAYED disbelief forms, brows first: they go up and come APART
    // (browIn 0 = flat, not the worried tent), the lower lids rise, the jaw drops; the eyes come down from the
    // standing CEO's eyes-rolled-up angle to a level look straight at them (the CEO is just off-frame left)
    ['s07b03.end+0.18', X(EXPR.terrified, { lidU: -0.3, browIn: 0.85, browUp: 0.75, smile: -0.35, open: 0.0, wide: 0.05, teeth: 0, tremble: 0, pupil: 0.62, tears: 0.82, ...upCeo })],
    ['s07b03.end+0.45', X({ browUp: 1, browIn: 0.05, lidU: -0.04, lidL: 0.22, open: 0.12, smile: -0.3, pupil: 0.72, tears: 0.86, ...BETRAYED_LOOK }), 'out'],
    ['s07b03.end+0.75', BETRAYED, 'out'],
    ['s07b03.end+1.45', X(BETRAYED, { open: 0.34, lidL: 0.44, tears: 0.92 })],
    // the hands fall: the mouth stays open, the inner brows begin to tent again (it is turning into hurt)
    ['s07b03.end+1.9', X(BETRAYED, { open: 0.26, browIn: 0.3, browUp: 0.9, lidL: 0.46, lidU: 0.04, smile: -0.42, tremble: 0.25, tears: 0.95 })],
    ['scene.end+0.4', X(BETRAYED, { open: 0.24, browIn: 0.35, browUp: 0.88, lidL: 0.46, lidU: 0.05, smile: -0.45, tremble: 0.3, tears: 0.95 })],
  ]);
  face = { ...face };
  face.noAutoBlink = t > S.T('s07b01+0.3');
  // one blink before the dread sets in; then none until the hands have dropped: a slow one, letting it sink in
  // (the cut to Consciousness comes right out of it)
  face.blink = blinkAt(t, S.T('s07b01+0.18'), 0.18) + blinkAt(t, S.T('s07b03.end+1.5'), 0.38);
  // one tear, from one eye: it gathers on the lid halfway through the reaction shot (through the head shake) and
  // leaves it as the hands drop, so it is seen running before the cut (it started 0.4 s before the cut and was only
  // ever a bead on the lid)
  face.tearR = t > S.T('s07b03.end+0.95') ? Math.min(1, (t - S.T('s07b03.end+0.95')) / 1.7) : 0;
  // ONE slow head shake (left, right, back to centre) over 0.8 s; the eyes stay locked on the CEO through it
  const shk = clamp((t - S.T('s07b03.end+0.72')) / 0.8);
  const shakeW = Math.sin(shk * TAU) * Math.sin(shk * Math.PI);
  const shake = shakeW * 0.24;
  const headTurn = facing > 0 ? S.k(t, [['scene.start', -0.1], ['scene.start+0.4', -0.28]]) : shake + S.k(t, [['s07b03.end+0.3', 0], ['s07b03.end+0.6', -0.06]]);
  // a small intake before the face changes (the head lifts), the jaw drop lets it settle, a swallow as the hands fall
  const dip = (a, dur, amp) => { const kk = clamp((t - S.T(a)) / dur); return Math.sin(kk * Math.PI) * amp; };
  const headDY = S.k(t, [['s07b02', 0], ['s07b02+0.15', -5, 'out'], ['s07b02+0.8', -3], ['s07b03.end+0.1', -3], ['s07b03.end+0.3', -5, 'out'],
    ['s07b03.end+0.65', 0]]) + dip('s07b03.end+1.55', 0.45, 4);
  const headDX = shakeW * 3;
  // breath held through the line; a catch of breath as the face forms, then shallow
  const breathe = S.k(t, [['s07b02', 1], ['s07b02+0.2', 0.2], ['s07b03.end+0.15', 0.2], ['s07b03.end+0.35', 1.4], ['s07b03.end+0.7', 0.4], ['s07b03.end+1.6', 0.5], ['s07b03.end+2.0', 1.1]]);
  return { t, face, facing, crouch, tremble, armL, armR, headTurn, headDY, headDX: facing > 0 ? 0 : headDX, headTilt: facing > 0 ? -0.05 : 0, squash, breathe, lean, dx,
    whiten: facing > 0 ? 0.55 * L.pulled : 0 };
}

function drawFearAt(g, F) {
  g.save();
  const x = FX + (F.dx || 0) * FS;
  if (F.squash !== 1) { g.translate(x, 0); g.scale(F.squash, 1); g.translate(-x, 0); }
  drawFear(g, x, FY, FS, F);
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
  } else if (t < T(CUT_CEO)) {
    // Fear's betrayed face: the long beat (s07 got 1.7 s more silence for it), a slow push
    shot(g, t, S, L, camK(S, t, [['s07b03.end', { x: 536, y: 1000, zoom: 1.9 }], [CUT_CEO, { x: 530, y: 994, zoom: 2.04 }]]), 1.4);
  } else {
    // ...and Consciousness seeing it (same set-up as their line, a touch closer)
    shot(g, t, S, L, camK(S, t, [[CUT_CEO, { x: 176, y: 548, zoom: 1.72 }], ['scene.end', { x: 174, y: 548, zoom: 1.8 }]]), 1.4);
  }
  grade(g, L.cold, 0);
  vignette(g, L.vig);
}
