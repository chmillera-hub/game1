// s06 · a_hand_on_the_shoulder · MIND_HQ (dissolve in = "one day")
// Consciousness tries tenderness first; Fear confesses it is only trying to keep them safe; then refuses.
// Views: `front` (opening wide), `alarm` (two-shots / closes), BACKDROP (front set + Void behind the alarm pair),
// an OTS cheat with Fear's crown in the foreground. See data/staging.md §3 s06.
import { createCanvas } from '@napi-rs/canvas';
import { W, H, clamp, lerp, ease, fbm, noise1, blinkAt, applyCamera, drift, vignette, TAU } from '../engine.mjs';
import { EXPR, makeExpr, withSpeech } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, selfLocal, drawClipboard } from '../chars/self.mjs';
import { drawEmotion } from '../chars/emotions.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, drawAlarmStation, HQ_VIEWS, hqScaleAt, ALARM_REACH } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';

export const id = 's06';

export const sfx = [
  { at: 'scene.start+0.48', name: 'footsteps', gain: -14, pan: 0.15 },          // the CEO crossing the room (steps = walk contacts)
  { at: 's06b01+1.45', name: 'cloth_rustle', gain: -16, pan: 0.2 },             // goes down on one knee
  { at: 's06b01+3.85', name: 'cloth_rustle', gain: -21, pan: 0.1 },             // the hand settles on the shoulder
  { at: 's06b02', name: 'breath_shaky', until: 's06b03+0.15', fade: 0.6, gain: -16 }, // Fear's fast shallow breathing (out before the line)
  { at: 's06b08+0.1', name: 'cloth_rustle', gain: -18, pan: 0.2 },              // Fear twists out from under the hand
  { at: 's06b08+0.545', name: 'alarm_pull', gain: -6, pan: 0.3 },               // clack lands on the yank (+0.6)
  { at: 's06b08+0.6', name: 'alarm_bell', until: 's07b02', loop: true, fade: 1.3, gain: -20, pan: 0.25 },
  { at: 's06b09+0.5', name: 'crowd_murmur', gain: -24, pan: -0.4 },            // off-screen: the others leave again
  { at: 's06b09+0.5', name: 'door_whoosh', gain: -22, pan: -0.5 },
];

// ---- staging constants (data/staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const CAGE_F = [302, 846, 0.3];
const CEO_AT_ALARM_F = [640, 1000, 0.444];
const FEAR_ALARM_F = [734, 973, 0.42];
const CEO_START_F = [606, 1160];      // (was 560: clear of s05's last CEO position (450,1060) in the dissolve)
const S05_END_CAM = { x: 540, y: 940, zoom: 1.2 };   // = s05 CAM.end (keep the two in sync)
const AA = HQ_VIEWS.alarm.anchors;
const FA = HQ_VIEWS.front.anchors;
const [FX, FY, FS] = AA.fearAtAlarm;   // 498, 1406, 1.8
const [CX, CY, CS] = AA.ceoKneel;      // 135, 1520, 2.091
const OFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 };
const KNEE = [100, -150];              // CEO-local wrist target resting on the raised front knee (kneel 1)

const X = (...p) => makeExpr(...p);
const sine = (k) => ease.sine(clamp(k));
// The narrator sheds no tear before the last scene: whatever the beat's tear welling, the CEO's lower lids only
// glisten (tears ≤ 0.35); the curve keeps the build-up (0.35 → .19, .85 → .32, 1 → .35)
const glisten = (x) => 0.35 * Math.pow(clamp(x || 0), 0.6);
// Fear's fist ON the alarm handle (alarm view, Fear-local at facing 1): the wrist sits `d` px back from the point the
// fist covers along the hand's screen angle (≈ −1.2: knuckles up, fingers hooked over the handle to pull it down),
// taken into Fear's body frame (drawFear rotates the arms with `lean`); `dx` = Fear's feet offset from FX (local px)
function onHandle(px, py, ang, lean, dx = 0, d = 8) {
  const x = px - d * Math.cos(ang) - dx, y = py - d * Math.sin(ang);
  const c = Math.cos(-lean), s = Math.sin(-lean);
  return { target: [x * c - y * s, x * s + y * c], handAng: ang - lean };
}
// for the yank Fear steps in toward the station (Fear-local px): from FX its far arm cannot reach the handle and the
// second fist hung below it, on the PULL DOWN label. s07 starts here and steps back as it turns round.
const YANK_DX = 15;

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
// keyframed camera with log-zoom interpolation (pushes feel even)
function camK(S, t, keys) {
  const c = S.k(t, keys.map(([a, v, e]) => [a, { x: v.x, y: v.y, lz: Math.log(v.zoom) }, e]));
  return { x: c.x, y: c.y, zoom: Math.exp(c.lz) };
}

// ------------------------------------------------------------------ global light / grade track
function look(t, S) {
  const alarm = S.k(t, [['s06b08+0.6', 0], ['s06b08+0.9', 1]]);
  const pulled = S.k(t, [['s06b08+0.6', 0], ['s06b08+0.85', 1]]);
  return {
    alarm, pulled,
    lightsDim: S.k(t, [['s06b08', 0.3], ['scene.end', 0.35]]),
    cold: S.k(t, [['s06b08', 0.45], ['scene.end', 0.5]]),
    vig: S.k(t, [['s06b08', 0.4], ['scene.end', 0.45]]),
  };
}
function setState(t, L, extra = {}) {
  return { t, lightsDim: L.lightsDim, consoleGlow: 0.8, mist: 0.4, voidShadow: 0.5, alarm: L.alarm, alarmPulled: L.pulled, screenMode: 'room', ...extra };
}

// ------------------------------------------------------------------ FEAR (alarm-view pose; the front view reuses it)
function fearPose(t, S, L) {
  const lip = S.lip('FEAR', t);
  // flinch at the touch ('shoulder')
  const touch = S.T('s06b01+3.96');
  const fl = t >= touch ? Math.exp(-(t - touch) * 7) * clamp((t - touch) / 0.05) : 0; // sharp spike, fast decay
  // twist out + yank (b08)
  const twist = clamp((t - S.T('s06b08+0.1')) / 0.42);
  const crouch = clamp(S.k(t, [
    ['s06b01', 1], ['s06b01+3.96', 1], ['s06b01+4.16', 0.84, 'out'], ['s06b01+4.9', 0.93],
    ['s06b04+0.8', 0.93], ['s06b04+1.4', 1], ['s06b05+1.2', 1], ['s06b05+1.4', 0.88, 'out'], ['s06b05+2.2', 0.94],
    ['s06b07', 0.96], ['s06b08+0.1', 0.96], ['s06b08+0.5', 0.12, 'out'], ['s06b08+0.75', 0.0], ['s06b08+0.95', 0.3, 'out'], ['s06b08+1.6', 0.38],
  ]));
  const headDY = S.k(t, [
    // slumped: the head sunk into the scarf until the touch jolts it up
    ['scene.start', 8], ['s06b01+3.96', 8], ['s06b01+4.1', 0, 'out'], ['s06b04+0.75', 0], ['s06b04+1.35', 10], ['s06b05-0.4', 6], ['s06b05+1.25', 3], ['s06b05+1.35', -4, 'out'],
    ['s06b05+2.2', 1], ['s06b07+0.15', 1], ['s06b07+0.35', 5, 'out'], ['s06b07+1.4', 4], ['s06b07+1.7', 0],
  ]) - fl * 12;
  const headTilt = S.k(t, [['s06b04+0.7', 0], ['s06b04+1.4', 0.09], ['s06b05-0.3', 0.04], ['s06b05+1.3', -0.03], ['s06b06', 0.02]])
    - fl * 0.16 + (twist > 0 && twist < 1 ? Math.sin(twist * Math.PI) * 0.12 : 0);
  // tiny fast "no, no, no" head shake that starts in b06 and fades out in b07 (large enough to read in the
  // backdrop two-shot: ±0.07 yaw was ~2 px on screen)
  const shakeAmt = S.k(t, [['s06b06+1.85', 0], ['s06b06+2.1', 1], ['s06b07', 0.75], ['s06b07+0.3', 0.45], ['s06b07+0.9', 0.15], ['s06b07+1.4', 0]]);
  const shakeW = Math.sin((t - S.T('s06b06')) * TAU * 3.1) * shakeAmt;
  const headTurn = shakeW * 0.17 + S.k(t, [['s06b05+1.15', 0], ['s06b05+1.45', -0.12, 'out'], ['s06b06+0.6', -0.1], ['s06b06+1.5', 0]]);
  const headDX = shakeW * 2.6;
  const tremble = clamp(S.k(t, [['s06b01', 0.7], ['s06b06', 0.65], ['s06b07+2.6', 0.65], ['s06b08+0.2', 0.95], ['scene.end', 0.85]]) + fl * 0.4);

  // breathing: fast and shallow in b02 (open-mouth panting), a single sniff in b06
  const pant = S.k(t, [['s06b01+4.0', 0], ['s06b01+4.4', 1], ['s06b03+0.6', 1], ['s06b03+1.4', 0.3]]);
  const sniffAt = S.T('s06b06+0.85');
  const sniff = t > sniffAt && t < sniffAt + 0.35 ? Math.sin((t - sniffAt) / 0.35 * Math.PI) : 0;

  // ---- face
  const toVoid = { lookX: -0.62, lookY: -0.74 };
  const toCeo = { lookX: -0.6, lookY: -0.3 };
  const toCeoUs = { lookX: -0.9, lookY: -0.3 };      // b05 close: unmistakably at the CEO (off-frame left)
  const scaredUp = X(EXPR.scared, { lidU: -0.12, open: 0.05, ...toVoid });
  const pinched = X(EXPR.worried, { browIn: 0.95, browSquish: 0.55, browUp: 0.25, lidTilt: 0.3, lidU: -0.05, smile: -0.35, ...toCeo });
  let face = S.k(t, [
    ['scene.start', scaredUp],
    ['s06b01+3.96', scaredUp],
    ['s06b01+4.04', X(EXPR.scared, { lidU: -0.38, browUp: 0.95, browIn: 0.9, open: 0.24, round: 0.3, pupil: 0.62, lookX: -0.42, lookY: 0.5 }), 'out'],
    ['s06b01+4.45', X(EXPR.scared, { lidU: -0.26, browUp: 0.75, open: 0.1, pupil: 0.7, lookX: -0.42, lookY: 0.5 })],
    ['s06b01+4.7', X(EXPR.scared, { lidU: -0.2, browUp: 0.6, open: 0.08, pupil: 0.75, ...toCeo }), 'out'],
    // b02: looks at the hand, then up into Consciousness's eyes, brows pinched, waiting to be scolded
    ['s06b02', X(pinched, { lookX: -0.45, lookY: 0.55 })],
    ['s06b02+0.75', X(pinched, { lookX: -0.45, lookY: 0.55 })],
    ['s06b02+1.0', pinched, 'out'],
    ['s06b04', X(pinched, { browIn: 0.85 })],
    // b04: lower lip pushes up and trembles; eyes drop in shame
    ['s06b04+0.45', X(EXPR.worried, { browIn: 1, browUp: 0.2, lidTilt: 0.45, lidU: 0.05, smile: -0.62, pressed: 0.45, tremble: 0.7, ...toCeo })],
    ['s06b04+0.75', X(EXPR.worried, { browIn: 1, browUp: 0.1, lidTilt: 0.55, lidU: 0.32, smile: -0.62, pressed: 0.5, tremble: 0.7, lookX: -0.12, lookY: 0.8 }), 'out'],
    // (the shame stings: the eyes start to fill while they are down)
    ['s06b04+1.55', X(EXPR.worried, { browIn: 1, browUp: 0.1, lidTilt: 0.55, lidU: 0.34, smile: -0.6, pressed: 0.5, tremble: 0.6, tears: 0.2, lookX: -0.1, lookY: 0.82 })],
    // ...then slowly the eyes drift up, past the CEO's shoulder, to the Void
    ['s06b04+2.4', X(EXPR.scared, { browIn: 1, browUp: 0.45, lidTilt: 0.25, lidU: -0.08, smile: -0.45, tremble: 0.4, pupil: 0.8, tears: 0.4, ...toVoid })],
    ['s06b05-0.2', X(EXPR.scared, { browIn: 1, browUp: 0.45, lidTilt: 0.25, lidU: -0.08, smile: -0.45, tremble: 0.4, pupil: 0.8, tears: 0.48, ...toVoid })],
    // b05: back to Consciousness; the tears already glisten on the lower lids (~0.5 from the line's start) and keep
    // rising; chin crumples. On 'us' (+1.30) the eyes go hard left INTO the CEO's ("I was protecting you too"): the
    // eyeline-table lookX −0.6 only moves the iris a quarter of the eye in this close and read as a look at the lens
    ['s06b05+0.15', X(EXPR.worried, { browIn: 1, browUp: 0.35, lidTilt: 0.4, smile: -0.5, tremble: 0.55, tears: 0.58, ...toCeo }), 'out'],
    ['s06b05+1.15', X(EXPR.worried, { browIn: 1, browUp: 0.35, lidTilt: 0.45, smile: -0.55, tremble: 0.6, tears: 0.68, ...toCeo })],
    ['s06b05+1.4', X(EXPR.worried, { browIn: 0.9, browUp: 0.7, lidTilt: 0.3, lidU: -0.16, smile: -0.5, tremble: 0.5, tears: 0.76, pupil: 1.1, ...toCeoUs }), 'out'],
    ['s06b05+1.75', X(EXPR.crying, { browIn: 1, browUp: 0.55, lidTilt: 0.5, lidU: -0.02, lidL: 0.2, smile: -0.7, open: 0.1, tremble: 0.8, tears: 0.88, stream: 0, ...toCeoUs })],
    ['s06b06', X(EXPR.crying, { browIn: 1, browUp: 0.5, lidTilt: 0.5, lidU: 0.0, lidL: 0.22, smile: -0.62, open: 0, tremble: 0.6, tears: 0.92, stream: 0, ...toCeo })],
    // b06: watches the nod; a tear sits on the lid; then the eyes slide to the Void and stay
    ['s06b06+1.35', X(EXPR.crying, { browIn: 1, browUp: 0.5, lidTilt: 0.5, lidU: 0.02, lidL: 0.22, smile: -0.6, open: 0, tremble: 0.5, tears: 0.95, stream: 0, ...toCeo })],
    ['s06b06+1.8', X(EXPR.scared, { browIn: 1, browUp: 0.6, lidTilt: 0.35, lidU: -0.12, lidL: 0.1, smile: -0.5, tremble: 0.5, tears: 0.9, pupil: 0.72, ...toVoid }), 'out'],
    ['s06b07+0.15', X(EXPR.scared, { browIn: 1, browUp: 0.6, lidTilt: 0.35, lidU: -0.1, smile: -0.5, tremble: 0.5, tears: 0.9, pupil: 0.72, ...toVoid })],
    // b07: eyes squeeze shut on "can't"
    ['s06b07+0.32', X(EXPR.crying, { browIn: 1, browUp: 0.2, lidU: 1, lidL: 0.55, lidTilt: 0.5, smile: -0.7, tremble: 0.8, tears: 0.9, stream: 0, lookX: -0.5, lookY: 0 }), 'out'],
    ['s06b07+1.4', X(EXPR.crying, { browIn: 1, browUp: 0.15, lidU: 1, lidL: 0.55, lidTilt: 0.5, smile: -0.7, tremble: 0.8, tears: 0.9, stream: 0, lookX: -0.5, lookY: 0 })],
    // ...open on "I'm sorry" and meet Consciousness's eyes for one heartbeat
    ['s06b07+1.65', X(EXPR.crying, { browIn: 1, browUp: 0.6, lidU: -0.02, lidL: 0.25, lidTilt: 0.55, smile: -0.55, tremble: 0.6, tears: 0.95, stream: 0, ...toCeo }), 'out'],
    ['s06b07+2.5', X(EXPR.crying, { browIn: 1, browUp: 0.6, lidU: 0.02, lidL: 0.25, lidTilt: 0.55, smile: -0.55, tremble: 0.6, tears: 0.95, stream: 0, ...toCeo })],
    ['s06b07+2.8', X(EXPR.scared, { browIn: 1, browUp: 0.7, lidU: -0.2, lidL: 0.1, smile: -0.55, tremble: 0.6, tears: 0.9, pupil: 0.65, ...toVoid })],
    // b08: twists away, eyes squeezed shut, yanks the alarm
    ['s06b08+0.05', X(EXPR.terrified, { lidU: -0.2, tears: 0.85, ...toVoid })],
    ['s06b08+0.22', X(EXPR.terrified, { lidU: 1, lidL: 0.6, browIn: 1, browUp: 0.3, open: 0.32, wide: 0.6, teeth: 0.8, smile: -0.6, tears: 0.85 }), 'out'],
    ['scene.end', X(EXPR.terrified, { lidU: 1, lidL: 0.6, browIn: 1, browUp: 0.3, open: 0.22, wide: 0.55, teeth: 0.7, smile: -0.6, tears: 0.85 })],
  ]);
  face = { ...face };
  // fast shallow mouth breathing (open enough to read as panting in the insert)
  if (pant > 0.01 && !lip) face.open = clamp(face.open + pant * (0.17 + 0.2 * Math.max(0, Math.sin(t * TAU * 2.3))));
  // b06: a single tear gathers on the lower lid and sits there; the squeeze on "can't" (b07) pushes it out
  {
    const tOn = S.T('s06b06+1.0'), tFall = S.T('s06b07+0.3');
    if (t >= tOn && t < tFall) face.tearR = 0.012 + 0.03 * sine((t - tOn) / 0.6);
    else if (t >= tFall) face.tearR = Math.min(1, 0.042 + (t - tFall) / 1.7);
  }
  if (sniff > 0) { face.open = 0; face.pressed = Math.max(face.pressed, 0.4); face.lidU += 0.15 * sniff; }
  // tiny eye flicks while it waits (searching the CEO's face): b03, b06 start
  const srch = S.k(t, [['s06b02+1.0', 0], ['s06b02+1.3', 1], ['s06b04', 1], ['s06b04+0.3', 0]]);
  face.lookX += srch * (Math.sin(t * TAU * 1.6) > 0 ? 0.05 : -0.05);
  // no blinks through "I'm only trying to keep us safe." (the brimming eyes hold the CEO's), until the deliberate
  // slow blink in b06 (the old b05+1.0 blink and a random auto-blink fell inside the line)
  face.noAutoBlink = t > S.T('s06b05-0.3') && t < S.T('s06b06+0.95') || t > S.T('s06b07+0.2') && t < S.T('s06b07+1.6') || t > S.T('s06b08+0.35');
  if (t < S.T('s06b07')) face.blink = blinkAt(t, S.T('s06b06+0.55'), 0.32);
  face = withSpeech(face, lip, 0.9);

  // ---- arms (facing -1: armL = screen-RIGHT (the handle side), armR = screen-LEFT (toward the CEO))
  const facing = twist < 0.5 ? -1 : 1;
  const handleY = ALARM_REACH[1] + 26 * L.pulled;
  // the raised hand slides off the handle at the touch and comes to the scarf
  const off = sine((t - S.T('s06b01+4.0')) / 0.55);
  const wr = S.k(t, [['s06b05', 0], ['s06b05+0.4', 1], ['s06b06+1.6', 1], ['s06b06+2.0', 0.6], ['s06b07+1.4', 0.6], ['s06b07+1.8', 0.3]]);
  const w1 = Math.sin(t * TAU * 1.3) * 4 * wr, w2 = Math.cos(t * TAU * 1.3) * 4 * wr;
  let armL, armR;
  if (facing < 0) {
    // local coords (mirrored): the scarf tail hangs at local x 12..30, y -110..-60
    const handle0 = [-ALARM_REACH[0], handleY];
    const atScarfL = [-6 - w1 * 0.5, -100 + w2 * 0.5];
    armL = { target: [lerp(handle0[0], atScarfL[0], off), lerp(handle0[1], atScarfL[1], off)], bend: off > 0.6 ? -1 : 1, front: true, hand: off > 0.3 ? 'fist' : 'grip' };
    const hug = [-14, -116];                     // hugging itself (as s05 ended), clear of the CEO's hand
    const atScarfR = [6 + w2 * 0.5, -104 - w1 * 0.5];
    // (the hugging hand lies over the far upper arm, palm on it: an open hand there stood up in front of the chin)
    armR = { target: [lerp(hug[0], atScarfR[0], off), lerp(hug[1], atScarfR[1], off)], bend: 1, front: true,
      hand: off > 0.4 ? 'fist' : 'drape', ...(off > 0.4 ? {} : { palmDir: [0, 0, -1], handAng: Math.PI + 0.35 }) };
    if (twist > 0) { // pulls its arms in as it turns (they reach for the handle after the turn)
      const k = clamp(twist * 2);
      armR = { target: [lerp(armR.target[0], 14, k), lerp(armR.target[1], -112, k)], bend: 1, front: true, hand: 'fist' };
      armL = { target: [lerp(armL.target[0], -14, k), lerp(armL.target[1], -116, k)], bend: -1, front: true, hand: 'fist' };
    }
  }
  const lean = facing > 0 ? S.k(t, [['s06b08+0.6', 0], ['s06b08+0.9', 0.12, 'out'], ['scene.end', 0.08]]) : 0;
  const dx = YANK_DX * sine((t - S.T('s06b08+0.14')) / 0.42);
  if (facing > 0) {
    // reaches up and locks both fists on the handle (knuckles up, elbows down), then hangs its weight off it
    const reach = sine((t - S.T('s06b08+0.31')) / 0.29);
    const hR = onHandle(ALARM_REACH[0] + 12, handleY, -1.15, lean, dx), hL = onHandle(ALARM_REACH[0] - 14, handleY + 1, -1.3, lean, dx);
    armR = { target: [lerp(14, hR.target[0], reach), lerp(-112, hR.target[1], reach)], bend: -1, front: true,
      hand: reach > 0.7 ? 'grip' : 'open', handAng: lerp(-1.6, hR.handAng, reach) };
    armL = { target: [lerp(-14, hL.target[0], reach), lerp(-116, hL.target[1], reach)], bend: -1, front: true,
      hand: reach > 0.7 ? 'grip' : 'open', handAng: lerp(-1.6, hL.handAng, reach) };
  }
  const squash = twist > 0 && twist < 1 ? 1 - 0.22 * Math.sin(twist * Math.PI) : 1;
  return { face, facing, crouch, headDY, headDX, headTilt, headTurn, tremble, armL, armR, lean, squash, dx,
    whiten: facing > 0 ? 0.55 * L.pulled : 0,
    breathRate: pant > 0.2 ? 1.5 : undefined, breathe: pant > 0.2 ? 1.2 : undefined, fl };
}
function shoulderPt(crouch) { return [FX - 36 * FS, FY - (131 - 20 * crouch) * FS]; }
function drawFearAt(g, x, y, s, t, P, extra = {}) {
  g.save();
  x += (P.dx || 0) * s;
  if (P.squash !== 1) { g.translate(x, 0); g.scale(P.squash, 1); g.translate(-x, 0); }
  drawFear(g, x, y, s, { t, face: P.face, facing: P.facing, crouch: P.crouch, headDY: P.headDY, headDX: P.headDX, headTilt: P.headTilt,
    headTurn: P.headTurn, tremble: P.tremble, armL: P.armL, armR: P.armR, lean: P.lean, breathRate: P.breathRate, breathe: P.breathe,
    whiten: P.whiten, ...extra });
  g.restore();
}

// ------------------------------------------------------------------ CONSCIOUSNESS (alarm view, kneeling at ceoKneel)
function ceoPose(t, S, F) {
  const lip = S.lip('CONSCIOUSNESS', t);
  const sh = shoulderPt(F.crouch);
  // the hand: lifts off the knee, hovers (fingers curling), settles on 'shoulder', stays; in b08 it is left in the air
  // hover: left of the shoulder at the level of the (sunk) head's lower edge; the fingertips stay ~60 px clear of
  // Fear's cheek and of its hugging arm (any higher and they brush the cheek: the shoulder sits under the big head)
  const hover = [sh[0] - 95, sh[1] - 18];
  const lift = sine((t - S.T('s06b01+2.0')) / 0.75);
  const settle = sine((t - S.T('s06b01+3.62')) / 0.34);
  // the hesitation: half-way there the hand draws back a little and the fingers curl in, then it decides
  const back = sine((t - S.T('s06b01+2.85')) / 0.3) * (1 - sine((t - S.T('s06b01+3.2')) / 0.38));
  const hv = Math.sin(t * TAU * 0.9) * 2.5 * (1 - settle);
  let hand = [lerp(lerp(CX + KNEE[0] * CS, hover[0], lift), sh[0], settle) - back * 16 + hv,
    lerp(lerp(CY + KNEE[1] * CS, hover[1], lift), sh[1], settle) - back * 5 + hv * 0.6];
  // thumb strokes (b03 once, b06 once), fingers tighten (b02, 'us')
  const stroke = (a) => { const k = clamp((t - S.T(a)) / 0.7); return Math.sin(k * Math.PI) * 7; };
  hand[0] += stroke('s06b03+1.75') + stroke('s06b06+1.05');
  const tight = S.k(t, [['s06b02+0.2', 0], ['s06b02+0.6', 1], ['s06b03', 0.5], ['s06b05+1.45', 0.5], ['s06b05+1.75', 1], ['s06b06', 0.6]]);
  hand[1] += tight * 3;
  // b07: the hand goes slack (slides a little down the scarf, the wrist gives)
  const slack = S.k(t, [['s06b07+2.2', 0], ['s06b07+2.7', 1]]);
  hand[1] += slack * 11; hand[0] -= slack * 6;
  // b08: Fear twists away: the hand is left where the shoulder was, closes to a loose fist, lowers to the knee
  const tw = S.T('s06b08+0.1');
  // fingers: extend as the hand lifts, curl in once while it draws back, extend again, drape on the shoulder
  // ('open' sticks the thumb up toward Fear's face like a thumbs-up; 'drape' keeps it along the fingers)
  const curl = back > 0.35;
  let handShape = settle > 0.6 ? 'drape' : lift > 0.3 ? (curl ? 'rest' : 'drape') : 'rest';
  let wrist = lerp(0.75, 0.35, lift * (1 - settle)) + back * 0.25 + slack * 0.35;
  let preset = 'onShoulder';
  // resting on the raised knee the arm is foreshortened (the elbow toward the camera, the forearm forward along the
  // thigh): at full length the far arm folded across the jacket front into a sharp "<" to reach the knee
  let onKnee = 1 - lift;
  if (t >= tw) {
    // the shoulder slides out from under the hand: a small reflexive give, then it just hangs there
    const sh0 = shoulderPt(0.96);
    const give = sine((t - tw) / 0.35);
    const frozen = [sh0[0] - 42 * give, sh0[1] - 4 * give];
    const down = sine((t - S.T('s06b08+1.0')) / 1.1);
    const knee = [CX + KNEE[0] * CS, CY + KNEE[1] * CS];
    hand = [lerp(frozen[0], knee[0], down), lerp(frozen[1], knee[1], down)];
    const fist = clamp((t - S.T('s06b08+0.75')) / 0.3);
    handShape = fist > 0.5 ? 'fist' : 'open';
    wrist = 0.75;
    onKnee = down;
  }
  const shakeAmt = t >= tw ? 0.12 : settle * 0.4 * (1 - slack * 0.6);
  const armR = { preset, target: selfLocal(CX, CY, CS, 1, hand[0], hand[1]), shake: shakeAmt, hand: handShape, wrist,
    reach1: lerp(1, 0.66, onKnee), reach2: lerp(1, 0.6, onKnee) };

  // ---- face
  const atFear = { lookX: 0.6, lookY: 0.42 };
  const tender = X(SELF_EXPR.worried, { browIn: 0.55, browSquish: 0.15, lidU: 0.14, smile: 0, lidTilt: 0.2, ...atFear });
  const firmSoft = X(SELF_EXPR.sternKind, { browIn: 0.35, browSquish: 0.35, lidU: 0.12, tears: 0.4, smile: 0, pressed: 0.25, ...atFear });
  let face = S.k(t, [
    ['scene.start', tender],
    ['s06b01+3.96', tender],
    ['s06b01+4.2', X(tender, { browIn: 0.7, browUp: 0.2, lidU: 0.05 })],
    // b02: feels the shaking: inner brows lift, eyes soften and glisten; a slow swallow
    ['s06b02+0.3', X(tender, { browIn: 0.7, browUp: 0.15 })],
    ['s06b02+0.9', X(SELF_EXPR.worried, { browIn: 1, browUp: 0.25, lidU: 0.2, lidTilt: 0.4, tears: 0.35, smile: -0.1, ...atFear })],
    ['s06b02+1.25', X(SELF_EXPR.worried, { browIn: 1, browUp: 0.25, lidU: 0.22, lidTilt: 0.4, tears: 0.42, pressed: 0.7, smile: -0.15, ...atFear })],
    ['s06b02+1.75', X(SELF_EXPR.worried, { browIn: 0.9, browUp: 0.2, lidU: 0.16, lidTilt: 0.35, tears: 0.45, pressed: 0.2, smile: -0.05, ...atFear })],
    // b03: "You need to stop pulling the fire alarm." level brows, inner corners lifted, steady eye contact
    ['s06b03', firmSoft],
    ['s06b04', X(firmSoft, { browIn: 0.5 })],
    // b04 (off-screen): softer, almost apologetic
    ['s06b04+0.8', X(SELF_EXPR.worried, { browIn: 0.7, browUp: 0.3, lidU: 0.18, tears: 0.45, ...atFear })],
    // b05 (soft fg): they had not expected that
    ['s06b05+1.3', X(SELF_EXPR.worried, { browIn: 0.7, browUp: 0.3, lidU: 0.18, tears: 0.45, ...atFear })],
    ['s06b05+1.6', X(SELF_EXPR.worried, { browIn: 0.85, browUp: 0.55, lidU: -0.02, tears: 0.5, open: 0.06, ...atFear }), 'out'],
    // b06: eyes fill, lips press, a slow nod ("I know you are")
    ['s06b06+0.2', X(SELF_EXPR.holdingBackTears, { lidU: 0.08, lidL: 0.16, tears: 0.85, tremble: 0.25, lookX: 0.6, lookY: 0.32 })],
    ['s06b06+2.0', X(SELF_EXPR.holdingBackTears, { lidU: 0.1, lidL: 0.18, tears: 1, tremble: 0.3, lookX: 0.55, lookY: 0.32 })],
    // b07: inner brows draw up and together, lips part on a breath that never becomes a word
    ['s06b07+1.6', X(SELF_EXPR.holdingBackTears, { lidU: 0.1, lidL: 0.18, tears: 0.85, tremble: 0.3, lookX: 0.6, lookY: 0.32 })],
    ['s06b07+2.3', X(SELF_EXPR.worried, { browIn: 1, browSquish: 0.5, browUp: 0.35, lidU: 0.1, lidTilt: 0.45, tears: 0.85, open: 0.12, smile: -0.2, pressed: 0, ...atFear })],
    // b08: the hand left in the air; a long, pained closing of the eyes
    ['s06b08+0.5', X(SELF_EXPR.worried, { browIn: 1, browSquish: 0.5, browUp: 0.4, lidU: 0.1, lidTilt: 0.45, tears: 0.85, open: 0.1, lookX: 0.75, lookY: 0.05 })],
    ['s06b08+0.85', X(SELF_EXPR.worried, { browIn: 1, browSquish: 0.55, browUp: 0.3, lidU: 0.3, lidTilt: 0.5, tears: 0.85, open: 0.04, lookX: 0.7, lookY: 0.1 })],
    ['s06b08+1.6', X(SELF_EXPR.sad, { browIn: 1, browSquish: 0.5, lidU: 1, lidTilt: 0.5, tears: 0.8, pressed: 0.6, smile: -0.35, lookX: 0.3, lookY: 0.5 })],
    // b09: opens the eyes; stares at the floor between them
    ['s06b09+0.25', X(SELF_EXPR.sad, { browIn: 1, browSquish: 0.45, lidU: 1, lidTilt: 0.5, tears: 0.8, pressed: 0.5, smile: -0.35, lookX: 0.3, lookY: 0.6 })],
    ['s06b09+0.65', X(SELF_EXPR.sad, { browIn: 0.95, browSquish: 0.35, lidU: 0.2, lidTilt: 0.5, tears: 0.75, pressed: 0.3, smile: -0.35, lookX: 0.3, lookY: 0.6 }), 'out'],
    ['scene.end', X(SELF_EXPR.sad, { browIn: 0.9, browSquish: 0.3, lidU: 0.28, lidTilt: 0.5, tears: 0.7, pressed: 0.25, smile: -0.35, lookX: 0.28, lookY: 0.62 })],
  ]);
  face = { ...face, tears: glisten(face.tears) };
  // a single exhale on the last line: lips part
  const exhale = S.k(t, [['s06b09+0.9', 0], ['s06b09+1.2', 1], ['s06b09+2.2', 0]]);
  face.open = Math.max(face.open, 0.08 * exhale); face.pressed *= 1 - exhale;
  face.noAutoBlink = t > S.T('s06b08+0.9') && t < S.T('s06b09+0.6');
  if (!face.noAutoBlink) face.blink = blinkAt(t, S.T('s06b01+4.3'), 0.2) + blinkAt(t, S.T('s06b02+1.5'), 0.34);
  face = withSpeech(face, lip, 0.85);
  // the slow swallow (b02), the nod on 'stop' (b03), the slow nod (b06), the sag (b09)
  const dip = (a, dur, amp) => { const k = clamp((t - S.T(a)) / dur); return Math.sin(k * Math.PI) * amp; };
  const headDY = dip('s06b02+1.1', 0.6, 4) + dip('s06b03+0.5', 0.45, 6) + dip('s06b06+0.4', 1.2, 11)
    + S.k(t, [['s06b08+0.6', 0], ['s06b08+1.6', 5], ['s06b09+0.9', 5], ['s06b09+2.0', 10]]);
  const shrug = S.k(t, [['s06b02+1.6', 0], ['s06b02+1.95', 0.25], ['s06b03+0.2', 0.12], ['s06b08', 0.12], ['s06b08+0.8', 0.35], ['s06b09+0.9', 0.35], ['s06b09+2.2', 0]]);
  const headTilt = S.k(t, [['s06b01', 0.1], ['s06b04', 0.1], ['s06b06', 0.13], ['s06b08+0.5', 0.13], ['s06b09', 0.06]]);
  return { t, outfit: 'ceo', kneel: 1, facing: 1, face, headDY, headTilt, shrug, armR, armL: 'rest', breathRate: shrug > 0.2 ? 0.16 : 0.2 };
}
function drawPair(g, t, S, L, opts = {}) {
  const F = fearPose(t, S, L);
  const C = ceoPose(t, S, F);
  drawSelf(g, CX, CY, CS, { ...C, layer: 'body' });
  if (opts.fear !== false) drawFearAt(g, FX, FY, FS, t, F);
  drawSelf(g, CX, CY, CS, { ...C, layer: 'front' });
  return F;
}

// extra red on the faces in the alarm view (§5.5), kept subtle
function redTint(g, t, L, x0, x1) {
  if (L.alarm <= 0.002) return;
  const pulse = 0.5 + 0.5 * Math.sin(t * 2 * Math.PI * 1.2 - Math.PI / 2);
  const a = L.alarm * (0.2 + 0.2 * pulse) * 0.75;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'multiply';
  const gr = g.createLinearGradient(x0, 0, x1, 0);
  gr.addColorStop(0, 'rgba(255,100,114,0)'); gr.addColorStop(1, `rgba(255,100,114,${a})`);
  g.fillStyle = gr; g.fillRect(0, 0, 720, 1280); g.restore();
}

// ------------------------------------------------------------------ shots
function shotAlarm(g, t, S, L, c, opts = {}) {
  const st = setState(t, L);
  g.save(); cam(g, c, t, opts.amp ?? 2.5);
  drawHQ(g, 'alarm', st);
  drawPair(g, t, S, L, opts);
  drawHQForeground(g, 'alarm', st);
  drawAlarmLight(g, 'alarm', st);
  g.restore();
  if (opts.tint) redTint(g, t, L, opts.tint[0], opts.tint[1]);
}

// While the camera holds on S05_END_CAM (the dissolve from s05), the static set + Void + empty cage are painted
// once (baked at the hand-over time, so nothing jumps when live drawing takes over) and reused: the dissolve frames
// draw both scenes and the live front set is the most expensive part of each.
const SET_M = 40;
let heldSet = null;
function drawHeldSet(g, t0, st) {
  if (!heldSet) {
    const c = createCanvas(W + 2 * SET_M, H + 2 * SET_M), b = c.getContext('2d'), cm = S05_END_CAM;
    b.translate(SET_M, SET_M); applyCamera(b, cm);
    drawHQ(b, 'front', { ...st, t: t0 });
    drawVoid(b, ...VOID_F, { t: t0, ...STARE_F, idle: 0, shadow: false });
    drawCage(b, ...CAGE_F, { t: t0, door: 1, locked: 0 });
    heldSet = { c, x: cm.x - (W / 2 + SET_M) / cm.zoom, y: cm.y - (H / 2 + SET_M) / cm.zoom, w: (W + 2 * SET_M) / cm.zoom, h: (H + 2 * SET_M) / cm.zoom };
  }
  g.drawImage(heldSet.c, heldSet.x, heldSet.y, heldSet.w, heldSet.h);
}

// opening wide in the front view: the emotions back at the console, the CEO crossing to Fear and kneeling
function shotFrontWide(g, t, S, L) {
  // starts on s05's LAST camera (s05 CAM.end, held there with this same drift), so the "one day" dissolve keeps
  // the set, the Void, the cage and Fear's spot in register (no doubled room); moves on once the dissolve is done
  const c = camK(S, t, [['scene.start+0.9', S05_END_CAM], ['s06b01+2.28', { x: 586, y: 962, zoom: 1.18 }]]);
  const st = setState(t, L);
  g.save(); cam(g, c, t, 2);
  const tHold = S.T('scene.start+0.9');
  if (t < tHold) drawHeldSet(g, tHold, setState(tHold, L));
  else {
    drawHQ(g, 'front', st);
    drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0, shadow: false });
    drawCage(g, ...CAGE_F, { t, door: 1, locked: 0 });
  }
  // CEO: crossing up-right, then kneeling beside Fear (back view, eyes on Fear)
  const t0 = S.T('scene.start'), tk = S.T('s06b01+1.48');
  const u = clamp((t - t0) / (tk - t0));
  const ue = u < 0.75 ? u / 0.75 * 0.8 : 0.8 + 0.2 * ease.out((u - 0.75) / 0.25); // steady walk, gentle arrival
  const cx = lerp(CEO_START_F[0], CEO_AT_ALARM_F[0], ue), cy = lerp(CEO_START_F[1], CEO_AT_ALARM_F[1], ue);
  const cs = hqScaleAt('front', cy);
  const kneel = sine((t - tk) / 0.8);
  const F = fearPose(t, S, L);
  const fearFront = () => drawFearAt(g, FEAR_ALARM_F[0], FEAR_ALARM_F[1], FEAR_ALARM_F[2], t, F);
  const ceo = () => drawSelf(g, cx, cy, cs, { t, outfit: 'ceo', view: 'back', facing: 1,
    walk: kneel > 0.001 ? null : { phase: ue * 4 * Math.PI }, bodyTurn: kneel > 0.001 ? undefined : 0.18,
    kneel, headTurn: lerp(0.25, 0.4, kneel), armR: kneel > 0.5 ? { preset: 'rest' } : undefined });
  // y-sorted: Fear (973) is behind the arriving CEO (1000+)
  fearFront(); ceo();
  // the emotions behind the console, working quietly; JOY glances back at Fear
  const tap = (tt, rate, ph) => Math.pow(Math.max(0, Math.sin(tt * TAU * rate + ph)), 6) * 7;
  const jk = sine((t - S.T('s06b01+0.6')) / 0.55);
  // (JOY's base expression adds smile .22 / browUp .1 / lidL .1: the smile fades to a small worried frown,
  //  inner brows up, lids level — worried, not startled)
  const jf = S.k(t, [['s06b01+0.75', X({ smile: 0.4, lidL: 0.15 })], ['s06b01+1.6', X({ smile: -0.36, browIn: 0.95, browUp: 0.12, lidTilt: 0.3, lidU: 0.06, lidL: -0.1 })]]);
  const order = [['CALM', FA.consoleSlot1], ['ANGER', FA.consoleSlot2], ['SADNESS', FA.consoleSlot3], ['JOY', FA.consoleSlot4]];
  for (const [n, [ex, ey, es]] of order) {
    const tt = t + OFF[n];
    if (n === 'JOY') {
      drawEmotion(g, n, ex, ey, es, { t: tt, headTurn: 0.5 * jk, face: { ...jf, lookX: 0.6 * jk, lookY: -0.5 * jk },
        armL: { preset: 'pressButton', dy: tap(tt, 0.7, 0) * (1 - jk) }, armR: { preset: 'pressButton', atY: -258, hand: 'point', handAng: 1.35, dy: tap(tt, 0.55, 1.3) * (1 - jk) - 9 * jk } });
    } else {
      drawEmotion(g, n, ex, ey, es, { t: tt, face: n === 'SADNESS' ? { lookX: 0.2, lookY: 0.3 } : {},
        armL: { preset: 'pressButton', dy: tap(tt, 0.45, 1) }, armR: { preset: 'pressButton', dy: tap(tt, 0.38, 2.5) } });
    }
  }
  drawHQForeground(g, 'front', st);
  // the clipboard, put down on the console rim
  g.save(); g.translate(612, 1236); g.rotate(-0.12); g.scale(0.62, 0.62 * 0.42); drawClipboard(g); g.restore();
  drawAlarmLight(g, 'front', st);
  g.restore();
}

// the BACKDROP close two-shot (§1.6): front set + Void far behind, the pair in alarm coordinates in front
function shotBackdrop(g, t, S, L) {
  const BG = { x: 530, y: 520, zoom: 1.75 }, HAZE = 0.18;
  const FG = S.k(t, [['s06b06', { x: 360, y: 940, zoom: 0.95 }], ['s06b07', { x: 362, y: 936, zoom: 0.975 }]]);
  const st = setState(t, L);
  g.save(); cam(g, BG, t, 1.2);
  drawHQ(g, 'front', st);
  drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0, shadow: false });
  drawCage(g, ...CAGE_F, { t, door: 1, locked: 0 });
  drawHQForeground(g, 'front', st);
  g.restore();
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = `rgba(13,11,28,${HAZE})`; g.fillRect(0, 0, 720, 1280); g.restore();
  g.save(); cam(g, FG, t, 1.2);
  drawAlarmStation(g, 692, 1089, 1.8, { t, alarm: L.alarm, alarmPulled: L.pulled });
  drawPair(g, t, S, L);
  drawHQForeground(g, 'alarm', { ...st, lightsDim: 0 });
  g.restore();
}

// over Fear's shoulder onto Consciousness: Fear's crown + tuft in the soft foreground (screen-space cheat)
let crownCv = null;
function shotOTS(g, t, S, L) {
  const c = camK(S, t, [['s06b02+0.95', { x: 268, y: 812, zoom: 1.52 }], ['s06b04', { x: 250, y: 782, zoom: 1.75 }]]);
  shotAlarm(g, t, S, L, c, { fear: false, amp: 1.8 });
  // Fear's crown, rendered at quarter resolution and upscaled = out of focus
  const F = fearPose(t, S, L);
  const droop = S.k(t, [['s06b03+0.5', 0], ['s06b03+1.1', 1, 'out']]);
  crownCv ||= createCanvas(120, 90);
  const cg = crownCv.getContext('2d');
  cg.setTransform(1, 0, 0, 1, 0, 0); cg.clearRect(0, 0, 120, 90);
  cg.setTransform(0.25, 0, 0, 0.25, -340 * 0.25, -920 * 0.25);
  drawFear(cg, 600, 1985 + droop * 24, 3.0, { t, facing: -1, crouch: F.crouch, tremble: F.tremble, headTilt: -0.05 + droop * 0.06,
    face: F.face, armL: 'hugSelf', armR: 'hugSelf', shadow: false });
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.imageSmoothingEnabled = true;
  g.drawImage(crownCv, 340, 920, 480, 360);
  g.restore();
}

// ------------------------------------------------------------------ render
export function render(g, t, S) {
  const L = look(t, S);
  const T = (a) => S.T(a);
  if (t < T('s06b01+2.28')) {
    shotFrontWide(g, t, S, L);
  } else if (t < T('s06b02')) {
    // close two-shot at Fear's height as the hand arrives
    const c = S.k(t, [['s06b01+2.28', { x: 418, y: 1062, zoom: 1.2 }], ['s06b02', { x: 418, y: 1060, zoom: 1.24 }]]);
    shotAlarm(g, t, S, L, c);
  } else if (t < T('s06b02+0.95')) {
    // insert on the hand on the small shoulder (trembling with Fear), Fear's whole face upper right, slow push.
    // Fear looks at the hand, then up into Consciousness's eyes: we cut on that look to the reverse (OTS).
    // (Was a hand→face tilt of ~400 world px in 1.4 s: up to 37 px/frame with a zoom pump — far too fast.)
    const c = camK(S, t, [['s06b02', { x: 462, y: 1180, zoom: 1.95 }], ['s06b02+0.95', { x: 459, y: 1174, zoom: 2.02 }]]);
    shotAlarm(g, t, S, L, c, { amp: 1.2 });
  } else if (t < T('s06b04')) {
    // the close on Consciousness's face with Fear soft in the foreground: b02's swallow and held breath, then the line
    shotOTS(g, t, S, L);
  } else if (t < T('s06b06')) {
    // reverse: close on Fear over Consciousness's shoulder (the CEO's arm and hand at the left)
    const c = camK(S, t, [['s06b04', { x: 520, y: 1000, zoom: 2.0 }], ['s06b06', { x: 516, y: 996, zoom: 2.12 }]]);
    shotAlarm(g, t, S, L, c, { amp: 1.8 });
  } else if (t < T('s06b07')) {
    shotBackdrop(g, t, S, L);
  } else if (t < T('s06b08')) {
    const c = camK(S, t, [['s06b07', { x: 518, y: 998, zoom: 2.05 }], ['s06b08', { x: 516, y: 994, zoom: 2.12 }]]);
    shotAlarm(g, t, S, L, c, { amp: 1.8 });
  } else if (t < T('s06b09')) {
    // a little wider than the b01 two-shot so the yank (the handle and box) is in frame, not cut by the right edge,
    // and the CEO's face is not cut by the left edge
    shotAlarm(g, t, S, L, S.k(t, [['s06b08', { x: 432, y: 1036, zoom: 1.04 }], ['s06b09', { x: 430, y: 1034, zoom: 1.06 }]]));
  } else {
    const c = camK(S, t, [['s06b09', { x: 230, y: 770, zoom: 1.9 }], ['scene.end', { x: 226, y: 772, zoom: 1.98 }]]);
    shotAlarm(g, t, S, L, c, { amp: 1.6 });
  }
  grade(g, L.cold, 0);
  vignette(g, L.vig);
}
