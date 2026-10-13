// s04 · not_safe — Fear names what it believes ("It's going to hurt me", "It's not safe here") and Consciousness
// reaches for a reassurance it cannot honestly give. Nobody touches anybody yet.
//
// View: the `alarm` wall for Fear's closes, and the BACKDROP composite (staging §1.6) for the two-shots and the
// CEO closes: the `front` set (+ the Void, + the empty open cage) blurred and hazed behind characters drawn in
// `alarm`-view coordinates, so the hood looms upper-left above/behind the kneeling CEO.
//
// Shots (beat anchors; the two short reaction cuts were moved a few tenths off the staging table so the
// two-shot gets 1.6 s of breathing room for the CEO's aborted reach):
//   A  scene.start   → s04b01+1.31  alarm close on Fear (unblinking, whisper)
//   B  s04b01+1.31   → s04b02+0.62  BACKDROP two-shot: CEO looks up at the hood and back, the hand starts toward
//                                   Fear and returns to the knee, "It hasn't…"
//   C  s04b02+0.62   → s04b03       BACKDROP CEO close: "…moved." + quick glance up-left, half-smile; Fear's tuft
//   D  s04b03        → s04b04       alarm close on Fear, the CEO soft at the left frame edge; scarf over the mouth
//   E  s04b04        → s04b05       BACKDROP two-shot, tighter: the eye-flick on "Nothing"; Fear sees the doubt
//   F  s04b05        → s04b06       alarm close on Fear: "You don't know that." slow blink, defeated shrug
//   G  s04b06        → end          BACKDROP CEO close, slow push: lips part, close; eyes drift up to the hood, stay

import { createCanvas } from '@napi-rs/canvas';
import { W, H, TAU, clamp, lerp, noise1, fbm, blinkAt, applyCamera, drift, vignette, ik, limb } from '../engine.mjs';
import { withSpeech } from '../face.mjs';
import { drawFear, FEAR_COLORS, fearBodySpace, fearHeadSpace, drawFearFrontArms } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, selfLocal, drawClipboard } from '../chars/self.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground, drawAlarmStation, HQ_VIEWS } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';

export const id = 's04';

export const sfx = [
  // Fear's racing heart under the whispers (screenplay b01), fading out as Consciousness tries to reassure
  { at: 'scene.start+0.05', name: 'heartbeat', until: 's04b04+0.6', loop: true, gain: -14, rate: 1.45, fade: 1.6 },
  // the CEO's hand lifting off the knee toward Fear, and settling back
  { at: 's04b01+1.42', name: 'cloth_rustle', gain: -19 },
  // Fear's shaky whispered breathing under "It hasn't moved." (b02)
  { at: 's04b02+0.2', name: 'breath_shaky', gain: -19, rate: 1.3, until: 's04b03', fade: 0.35 },
  // the scarf pulled up over the mouth on "…not safe here."
  { at: 's04b03+3.66', name: 'cloth_rustle', gain: -20, rate: 1.2 },
  // the silent beat: the CEO's in-breath for words that never come (shoulders rise at b06+0.2), held, let out
  { at: 's04b06+0.12', name: 'breath_shaky', gain: -21, rate: 0.95, until: 'scene.end', fade: 0.5 },
];

// ---------------------------------------------------------------- staging constants (staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const CAGE_F = [302, 846, 0.3];
const [FX, FY, FS] = HQ_VIEWS.alarm.anchors.fearAtAlarm;   // 498, 1406, 1.8
const [CX, CY, CS] = HQ_VIEWS.alarm.anchors.ceoKneel;      // 135, 1520, 2.091
const [HX, HY] = HQ_VIEWS.alarm.anchors.handle;            // 692, 1089

// set / grade values for s04 (staging §4.2)
const SET = { alarm: 0, alarmPulled: 0, lightsDim: 0.35, consoleGlow: 0.8, mist: 0.6, voidShadow: 0.7, screenMode: 'room' };
const COLD = 0.4, VIGNETTE = 0.45;

// cameras
const CAM = {
  A0: { x: 486, y: 1014, zoom: 2.0 }, A1: { x: 486, y: 1012, zoom: 2.1 },
  D0: { x: 392, y: 1010, zoom: 1.5 }, D1: { x: 397, y: 1012, zoom: 1.58 },
  F0: { x: 404, y: 1016, zoom: 1.6 }, F1: { x: 408, y: 1018, zoom: 1.68 },
};
const BD = {
  two: { bg: { x: 519, y: 552, zoom: 1.6 }, haze: 0.16, fg: { x: 400, y: 950, zoom: 0.75 } },
  twoT: { bg: { x: 495, y: 565, zoom: 1.75 }, haze: 0.18, fg: { x: 360, y: 940, zoom: 0.95 } },   // hood clear above the CEO's hair
  // CEO closes: Fear's near eye must sit clear of the phone UI (caption band + right-hand buttons), at <= 80 % of
  // the frame height and well inside the right edge. The fg camera rides 60 world px lower (the CEO 90 px higher on
  // screen; the backdrop follows by 15 so the hood keeps its air above the hair) and Fear is cheated 31 left / 77 up
  // in these two closes only (an invisible close-up cheat: it never shares a frame with its true spot)
  ceoC: { bg: { x: 550, y: 492, zoom: 1.9 }, haze: 0.2, fg: { x: 250, y: 712, zoom: 1.5 }, fearOff: [-31, -77] },
  ceoG0: { bg: { x: 550, y: 492, zoom: 1.9 }, haze: 0.2, fg: { x: 256, y: 720, zoom: 1.5 }, fearOff: [-31, -77] },
  ceoG1: { fg: { x: 263, y: 728, zoom: 1.6 } },
};

// ---------------------------------------------------------------- helpers
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

// The backdrop: the `front` room with the Void and the empty open cage, rendered ONCE per camera into a blurred,
// hazed bitmap ("out of focus"). Built from fixed parameters only, so every frame is deterministic.
const MARGIN = 28;
const bgCache = new Map();
function backdrop(bg, haze) {
  const key = `${bg.x}|${bg.y}|${bg.zoom}|${haze}`;
  let c = bgCache.get(key);
  if (c) return c;
  const w = W + 2 * MARGIN, h = H + 2 * MARGIN;
  const raw = createCanvas(w, h);
  const r = raw.getContext('2d');
  const st = { ...SET, t: 52 };
  r.save();
  r.translate(MARGIN, MARGIN);
  applyCamera(r, bg);
  drawHQ(r, 'front', st);
  drawVoid(r, ...VOID_F, { t: 52, ...STARE_F, idle: 0, shadow: false });
  drawCage(r, ...CAGE_F, { t: 52, door: 1, locked: 0 });
  drawHQForeground(r, 'front', st);
  r.restore();
  c = createCanvas(w, h);
  const b = c.getContext('2d');
  b.filter = 'blur(2.2px)';
  b.drawImage(raw, 0, 0);
  b.filter = 'none';
  b.fillStyle = `rgba(13,11,28,${haze})`;
  b.fillRect(0, 0, w, h);
  bgCache.set(key, c);
  return c;
}
function drawBackdrop(g, bg, haze, t) {
  const img = backdrop(bg, haze);
  const d = drift(t, 1.2, 7);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(img, -MARGIN + d.dx, -MARGIN + d.dy);
  g.restore();
}

// --------------------------------------------------------------- FEAR (alarm coords, facing -1, toward the CEO)
// eyelines (staging §1.2): Fear → Void up-left; Fear → CEO left, flatter.
const F_HOOD = { lookX: -0.6, lookY: -0.74 };
const F_CEO = { lookX: -0.66, lookY: -0.22 };
const F_FLICK = { lookX: -0.62, lookY: -0.36 };     // its eyes ride the CEO's flick up a hair
const E_FROZEN = { browIn: 1, browUp: 0.62, browSquish: 0.35, lidU: -0.34, lidL: 0, lidTilt: 0, pupil: 0.56, smile: -0.32, wide: 0.08, tears: 0.12, tremble: 0.35 };
const E_PLEAD = { browIn: 1, browUp: 0.8, browSquish: 0.18, lidU: -0.1, lidL: 0.05, lidTilt: 0.28, pupil: 1.18, smile: -0.52, wide: 0.05, tears: 0.42, tremble: 0.5 };
const E_NOTSAFE = { browIn: 1, browUp: 0.72, browSquish: 0.42, lidU: -0.3, lidL: 0, lidTilt: 0.12, pupil: 0.62, smile: -0.5, wide: 0.1, tears: 0.5, tremble: 0.7 };
const E_DOUBT = { browIn: 0.55, browUp: 0.12, browSquish: 0.5, lidU: 0.24, lidL: 0.4, lidTilt: 0.12, pupil: 0.95, smile: -0.32, wide: -0.05, tears: 0.45, tremble: 0.35 };
const E_TRUE = { browIn: 0.88, browUp: 0.32, browSquish: 0.25, lidU: 0.14, lidL: 0.24, lidTilt: 0.38, pupil: 1.06, smile: -0.42, wide: -0.05, tears: 0.55, tremble: 0.85 };
const E_WATCH = { browIn: 0.95, browUp: 0.45, browSquish: 0.2, lidU: 0.04, lidL: 0.14, lidTilt: 0.42, pupil: 0.92, smile: -0.36, wide: 0, tears: 0.55, tremble: 0.5 };
const E_BACK = { browIn: 1, browUp: 0.55, browSquish: 0.35, lidU: -0.16, lidL: 0.05, lidTilt: 0.25, pupil: 0.7, smile: -0.4, wide: 0.05, tears: 0.55, tremble: 0.45 };

function fearPose(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  const gaze = k([
    ['scene.start', F_HOOD],
    ['s04b03-0.16', F_HOOD], ['s04b03+0.12', F_CEO, 'cubic'],                 // first look at the CEO
    ['s04b03+2.55', F_CEO], ['s04b03+2.88', F_HOOD, 'cubic'],                 // "…not safe" → back to the hood
    ['s04b04-0.42', F_HOOD], ['s04b04-0.14', F_CEO, 'cubic'],                 // the CEO draws breath: look back
    ['s04b04+0.2', F_CEO], ['s04b04+0.3', F_FLICK], ['s04b04+0.5', F_FLICK], ['s04b04+0.62', F_CEO],
    ['s04b06+1.4', F_CEO], ['s04b06+1.88', F_HOOD, 'cubic'],                  // after the CEO's eyes go up
  ]);
  const ex = k([
    ['scene.start', E_FROZEN],
    ['s04b03-0.18', E_FROZEN], ['s04b03+0.32', E_PLEAD],
    ['s04b03+2.52', E_PLEAD], ['s04b03+2.95', E_NOTSAFE],
    ['s04b04+0.5', E_NOTSAFE], ['s04b04+1.05', E_DOUBT],                       // it has seen the doubt
    ['s04b05-0.3', E_DOUBT], ['s04b05+0.12', E_TRUE],
    ['s04b06+0.1', E_TRUE], ['s04b06+0.7', E_WATCH],
    ['s04b06+1.4', E_WATCH], ['s04b06+1.95', E_BACK],
  ]);
  // a dry swallow before speaking; the defeated shrug after "You don't know that."
  const swallow = k([['scene.start+0.1', 0], ['scene.start+0.24', 1], ['scene.start+0.5', 0]]);
  const shrugUp = k([['s04b05+1.0', 0], ['s04b05+1.2', 1], ['s04b05+1.42', 0]]);
  const crouch = k([['scene.start', 0.3], ['s04b03+2.75', 0.3], ['s04b03+3.1', 0.42], ['s04b04+0.8', 0.42], ['s04b04+1.6', 0.34],
    ['s04b05+1.25', 0.3], ['s04b05+1.75', 0.44]]);
  const tremble = k([['scene.start', 0.75], ['s04b03+2.65', 0.72], ['s04b03+2.95', 0.95], ['s04b03+4.2', 0.92],
    ['s04b04+0.6', 0.82], ['s04b05', 0.66], ['s04b06+0.5', 0.6]]);
  const lip = S.lip('FEAR', t);
  const amt = k([['s04b01', 0.55], ['s04b03-0.2', 0.55], ['s04b03', 0.8], ['s04b05-0.2', 0.8], ['s04b05', 0.5]]);
  const blink = Math.max(
    blinkAt(t, S.T('s04b02+1.15'), 0.18), blinkAt(t, S.T('s04b03-0.06'), 0.16), blinkAt(t, S.T('s04b03+1.6'), 0.2),
    blinkAt(t, S.T('s04b03+4.15'), 0.18), blinkAt(t, S.T('s04b04+1.7'), 0.18), blinkAt(t, S.T('s04b05-0.45'), 0.16),
    blinkAt(t, S.T('s04b05+0.92'), 0.52), blinkAt(t, S.T('s04b06+1.12'), 0.2), blinkAt(t, S.T('s04b06+2.4'), 0.18));
  const micro = { x: fbm(t * 1.1, 21) * 0.045, y: fbm(t * 0.9, 22) * 0.035 };
  const face = withSpeech({ ...ex, lookX: gaze.lookX + micro.x, lookY: gaze.lookY + micro.y,
    pressed: 0.55 * swallow, blink, noAutoBlink: true }, lip, amt);
  // hands: fists on the scarf → scarf pulled up over the mouth (after "here.") → down to answer → slip to the belly
  const up = k([['s04b03+3.68', 0], ['s04b03+4.05', 1, 'cubic'], ['s04b04+1.78', 1], ['s04b04+2.22', 0, 'cubic']]);
  const slump = k([['s04b05+1.1', 0], ['s04b05+1.7', 1]]);
  const cy = crouch * 20;
  const arm = (side) => {
    // mouth: fists on the pulled-up band's lower edge, a hair below the shoulder line, so the elbows hang down
    // outside the body (a target above the shoulder folds both forearms across the chest into an X)
    const scarf = [side * 13, -134 + cy], mouth = [side * 13, -131 + cy], belly = [side * 12, -106 + cy * 0.4];
    const p = [lerp(lerp(scarf[0], mouth[0], up), belly[0], slump), lerp(lerp(scarf[1], mouth[1], up), belly[1], slump)];
    return { target: p, bend: side, front: true, hand: 'fist' };
  };
  const turn = lerp(-0.16, -0.26, clamp((gaze.lookY + 0.74) / 0.52));
  return {
    t, facing: -1, crouch, tremble, face,
    headTurn: turn, headTilt: -0.04 + 0.03 * Math.sin(t * 0.7),
    headDY: 4 * swallow - 3 * shrugUp + 5 * up, breathRate: 0.62, breathe: 1.15,
    armL: arm(-1), armR: arm(1), scarfUp: up, whiten: k([['s04b01+0.5', 0], ['s04b01+0.9', 1], ['s04b02+0.4', 1], ['s04b02+1.4', 0.25]]),
  };
}

// the pulled-up scarf is drawn in Fear's own body/head frames (fear.mjs), so it sits exactly on the drawn Fear
function drawScarfUp(g, x, y, s, p) {
  const k = clamp(p.scarfUp || 0);
  if (k <= 0.01) return;
  const C = FEAR_COLORS;
  g.save();
  const sh = fearBodySpace(g, x, y, s, p);
  g.save();
  fearHeadSpace(g, p, sh);
  // the knitted wrap is stretched up from the neck over the mouth and chin (just under the eyes)
  const top = lerp(2, -31, k), bot = 12, hw = lerp(30, 40, k);
  g.fillStyle = C.scarf; g.strokeStyle = C.line; g.lineWidth = 2.6; g.lineJoin = 'round';
  g.beginPath();
  g.moveTo(-hw, top + 5);
  g.quadraticCurveTo(0, top - 4, hw, top + 5);
  g.quadraticCurveTo(hw + 5, (top + bot) / 2, hw - 3, bot);
  g.quadraticCurveTo(0, bot + 7, -hw + 3, bot);
  g.quadraticCurveTo(-hw - 5, (top + bot) / 2, -hw, top + 5);
  g.closePath(); g.fill(); g.stroke();
  g.save(); g.clip();
  g.strokeStyle = C.scarf2; g.lineWidth = 2.5;           // the same slanted knit stripes as the neck wrap
  for (let q = -hw - 10; q < hw + 10; q += 13) { g.beginPath(); g.moveTo(q - 3, top - 2); g.lineTo(q + 5, bot + 6); g.stroke(); }
  g.restore();
  g.restore();
  g.restore();
  // the arms again, over the band (same geometry as drawFear's own front arms underneath)
  drawFearFrontArms(g, x, y, s, p);
}

function drawFearNow(g, t, S, [ox, oy] = [0, 0]) {
  const p = fearPose(t, S);
  // "knuckles whiten on the scarf": the fists' own knuckles pale (p.whiten) while the scarf is down
  drawFear(g, FX + ox, FY + oy, FS, { ...p, whiten: (p.scarfUp || 0) > 0.01 ? 0 : p.whiten, shadow: true });
  drawScarfUp(g, FX + ox, FY + oy, FS, p);
}

// --------------------------------------------------------------- CONSCIOUSNESS (alarm coords, kneeling, facing 1)
const C_FEAR = { lookX: 0.6, lookY: 0.42 };
const C_HOOD = { lookX: -0.85, lookY: -0.82 };
const C_HOODSTAY = { lookX: -0.72, lookY: -0.86 };
const CE_WORRY = { ...SELF_EXPR.worried, browIn: 0.7, smile: -0.12, pressed: 0 };
const CE_DREAD = { browIn: 0.85, browUp: 0.38, browSquish: 0.3, lidTilt: 0.15, lidU: -0.12, lidL: 0, smile: -0.2, pressed: 0, pupil: 0.85 };
const CE_HALF = { browIn: 0.9, browUp: 0.16, browSquish: 0.1, lidTilt: 0.3, lidU: 0.06, lidL: 0, smile: 0.24, pressed: 0 };
const CE_FALL = { browIn: 0.85, browUp: 0.1, browSquish: 0.3, lidTilt: 0.32, lidU: 0.12, lidL: 0.02, smile: -0.14, pressed: 0 };
const CE_FIRM = { browIn: -0.12, browUp: 0.02, browSquish: 0.32, lidTilt: 0.04, lidU: 0.04, lidL: 0.06, smile: 0.08, pressed: 0.1 };
const CE_CRACK = { browIn: 0.9, browUp: 0.15, browSquish: 0.32, lidTilt: 0.35, lidU: 0.16, lidL: 0.05, smile: -0.18, pressed: 0.15 };
const CE_KNIT = { browIn: 0.55, browUp: -0.05, browSquish: 0.7, lidTilt: 0.28, lidU: 0.2, lidL: 0.1, smile: -0.22, pressed: 0.8, tears: 0.2 };

const KNEE = [58, -150];                                          // palm resting on the front thigh, above the knee (local)
const HOVER = selfLocal(CX, CY, CS, 1, 336, 1182);                // in the air, short of Fear's shoulder (433,1170)

function ceoPose(t, S) {
  const k = (keys, e) => S.k(t, keys, e);
  const gaze = k([
    ['scene.start', C_FEAR],
    ['s04b01+1.38', C_FEAR], ['s04b01+1.58', C_HOOD, 'cubic'],            // from Fear's face up to the hood…
    ['s04b01+1.9', C_HOOD], ['s04b01+2.1', C_FEAR, 'cubic'],               // …and back
    ['s04b02+0.66', C_FEAR], ['s04b02+0.75', C_HOOD], ['s04b02+0.92', C_HOOD], ['s04b02+1.06', C_FEAR],  // mid-line glance
    ['s04b04+0.12', C_FEAR], ['s04b04+0.2', C_HOOD], ['s04b04+0.38', C_HOOD], ['s04b04+0.46', C_FEAR],    // the flick on "Nothing"
    ['s04b06+1.05', C_FEAR], ['s04b06+1.75', C_HOODSTAY, 'sine'],          // eyes drift up and stay
  ]);
  const headTurn = k([
    ['scene.start', 0.32], ['s04b01+1.45', 0.32], ['s04b01+1.8', -0.12, 'cubic'], ['s04b01+2.0', -0.12], ['s04b01+2.3', 0.3, 'cubic'],
    ['s04b02+0.7', 0.3], ['s04b02+0.85', 0.2], ['s04b02+1.05', 0.3],
    ['s04b06+1.15', 0.3], ['s04b06+2.1', -0.06, 'sine'],
  ]);
  const headTilt = k([
    ['scene.start', 0.05], ['s04b01+1.45', 0.05], ['s04b01+1.8', -0.06], ['s04b01+2.05', -0.06], ['s04b01+2.35', 0.05],
    ['s04b04-0.3', 0.05], ['s04b04', -0.02], ['s04b04+1.9', -0.02], ['s04b04+2.6', 0.04],
    ['s04b06+1.15', 0.04], ['s04b06+2.1', -0.05],
  ]);
  const ex = k([
    ['scene.start', CE_WORRY],
    ['s04b01+1.45', CE_WORRY], ['s04b01+1.75', CE_DREAD], ['s04b01+2.1', CE_DREAD], ['s04b02-0.2', CE_WORRY],
    ['s04b02-0.05', CE_WORRY], ['s04b02+0.3', CE_HALF],                     // the half-smile that doesn't reach the eyes
    ['s04b03+0.62', CE_HALF], ['s04b03+1.12', CE_FALL],                     // it falls away under "scares me"
    ['s04b04-0.4', CE_FALL], ['s04b04-0.05', CE_FIRM],                      // reaching for certainty
    ['s04b04+1.9', CE_FIRM], ['s04b05+0.35', CE_FIRM], ['s04b05+0.85', CE_CRACK],
    ['s04b06+1.3', CE_CRACK], ['s04b06+2.3', CE_KNIT],                      // brows knit, lips press: cannot promise
  ]);
  // the mid-line glance at the hood: the brave half-smile falters while the eyes are up there
  const falter = k([['s04b02+0.64', 0], ['s04b02+0.74', 1], ['s04b02+0.96', 1], ['s04b02+1.2', 0]]);
  ex.smile = lerp(ex.smile, 0.02, falter); ex.browUp = (ex.browUp || 0) + 0.25 * falter; ex.lidU = (ex.lidU || 0) - 0.1 * falter;
  // little mouth events: the aborted answer in b03, the lips parting in b06
  const opens = Math.max(k([['s04b03+1.5', 0], ['s04b03+1.68', 0.2], ['s04b03+1.95', 0.2], ['s04b03+2.15', 0]]),
    k([['s04b06+0.28', 0], ['s04b06+0.5', 0.3], ['s04b06+0.92', 0.3], ['s04b06+1.12', 0]]));
  const swallow = k([['s04b01+2.12', 0], ['s04b01+2.25', 1], ['s04b01+2.5', 0]]);
  const chin = k([['s04b04-0.35', 0], ['s04b04-0.05', 1], ['s04b04+1.9', 1], ['s04b05+0.4', 0]]);
  const nod = k([['s04b04+1.12', 0], ['s04b04+1.3', 1], ['s04b04+1.62', 0]]);
  const lean = k([['scene.start', 0.01], ['s04b01+2.15', 0.01], ['s04b02+0.2', 0.06], ['s04b03+3', 0.06], ['s04b04', 0.02], ['s04b06', 0.04]]);
  // b06: as the eyes drift up to the hood the upper lids lift with them (under CE_KNIT's heavy lids the irises
  // only slid sideways and read as "looking left"), the chin comes up a touch and the head eases toward the hood
  const upK = k([['s04b06+1.05', 0], ['s04b06+1.8', 1, 'sine']]);
  ex.lidU = lerp(ex.lidU || 0, -0.1, upK); ex.lidTilt = (ex.lidTilt || 0) * (1 - 0.45 * upK); ex.lidL = (ex.lidL || 0) * (1 - 0.6 * upK);
  const lip = S.lip('CONSCIOUSNESS', t);
  const blink = Math.max(blinkAt(t, S.T('s04b01+2.0'), 0.2), blinkAt(t, S.T('s04b03+2.35'), 0.46),
    blinkAt(t, S.T('s04b05+1.0'), 0.2), blinkAt(t, S.T('s04b06+1.0'), 0.22));
  const quiet = t > S.T('s04b04-0.1') && t < S.T('s04b04+0.8');
  const micro = { x: fbm(t * 0.5, 31) * 0.05, y: fbm(t * 0.42, 32) * 0.04 };
  const face = withSpeech({ ...ex, ...gaze, lookX: gaze.lookX + micro.x, lookY: gaze.lookY + micro.y,
    open: (ex.open || 0) + opens, pressed: Math.max(ex.pressed || 0, 0.6 * swallow), blink, noAutoBlink: quiet }, lip, 0.9);
  // the hand: off the knee toward Fear, stops in the air, returns ("not yet")
  const reach = k([['s04b01+1.4', 0], ['s04b01+1.84', 0.62, 'cubic'], ['s04b01+2.16', 0.6], ['s04b02+0.3', 0, 'cubic']]);
  // palm stops in the air beside Fear's shoulder, fingers up (never touching), then sinks back to the knee
  const rp = clamp(reach / 0.62);
  const curl = k([['s04b01+1.86', 0], ['s04b01+2.1', 1]]);
  const armR = { target: [lerp(KNEE[0], HOVER[0], rp), lerp(KNEE[1], HOVER[1], rp)], bend: -1, front: true, palm: true,
    hand: rp > 0.08 ? (curl > 0.5 && rp > 0.5 ? 'rest' : 'open') : 'drape',
    ...(rp > 0.08 ? { handAngle: lerp(-0.2, -0.62, rp) } : { wrist: 0.75 }), thumb: -1 };
  const inhale = k([['s04b06+0.2', 0], ['s04b06+0.55', 1], ['s04b06+0.95', 1], ['s04b06+1.5', 0]]);  // breath for words that never come
  return { t, outfit: 'ceo', kneel: 1, facing: 1, face, headTurn, headTilt, lean, shrug: 0.22 * inhale,
    headDY: 5 * swallow - 4 * chin + 6 * nod - 2 * inhale - 4 * upK, armR };
}

function drawClipboardOnFloor(g) {
  // continuity (staging §5.11): the clipboard lies on the floor by the CEO's back knee in s04
  g.save();
  g.translate(CX - 58 * CS, CY + 22 * CS);
  g.scale(CS * 1.05, CS * 0.42);
  g.rotate(-0.32);
  g.fillStyle = 'rgba(0,0,0,0.28)';
  g.beginPath(); g.ellipse(4, 6, 40, 48, 0, 0, TAU); g.fill();
  drawClipboard(g);
  g.restore();
}

// characters in alarm-view coordinates (camera already applied)
function drawPeople(g, t, S, { ceoAlpha = 1, fearOff } = {}) {
  drawFearNow(g, t, S, fearOff);
  drawClipboardOnFloor(g);
  drawSelf(g, CX, CY, CS, { ...ceoPose(t, S), alpha: ceoAlpha < 1 ? ceoAlpha : undefined });
}

// --------------------------------------------------------------- shots
function shotAt(t, S) {
  if (t < S.T('s04b01+1.31')) return 'A';
  if (t < S.T('s04b02+0.62')) return 'B';
  if (t < S.T('s04b03')) return 'C';
  if (t < S.T('s04b04')) return 'D';
  if (t < S.T('s04b05')) return 'E';
  if (t < S.T('s04b06')) return 'F';
  return 'G';
}

function renderAlarmShot(g, t, S, cam, { ceoHaze = 0 } = {}) {
  const st = { ...SET, t };
  g.save();
  applyCamera(g, liveCam(cam, t));
  drawHQ(g, 'alarm', st);
  drawFearNow(g, t, S);
  if (ceoHaze > 0) {
    // the CEO at the frame edge is nearer the lens and out of the focal plane: draw it through a soft layer
    softLayer(g, (c) => { drawClipboardOnFloor(c); drawSelf(c, CX, CY, CS, ceoPose(t, S)); });
  } else {
    drawClipboardOnFloor(g);
    drawSelf(g, CX, CY, CS, ceoPose(t, S));
  }
  drawHQForeground(g, 'alarm', st);
  g.restore();
}

// draw a foreground figure through a small offscreen copy, upscaled (a cheap rack-focus softness). Only the
// left part of the frame is blitted: the near figure lives there in every shot that uses this.
const SOFT_Q = 0.42, SOFT_W = 470;
let soft = null, softCtx = null;
function softLayer(g, drawFn) {
  const q = SOFT_Q;
  if (!soft) { soft = createCanvas(Math.ceil(SOFT_W * q), Math.ceil(H * q)); softCtx = soft.getContext('2d'); }
  const c = softCtx;
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.clearRect(0, 0, soft.width, soft.height);
  const m = g.getTransform();
  c.setTransform(m.a * q, m.b * q, m.c * q, m.d * q, m.e * q, m.f * q);
  drawFn(c);
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.imageSmoothingEnabled = true;
  g.imageSmoothingQuality = 'high';
  g.drawImage(soft, 0, 0, soft.width, soft.height, 0, 0, soft.width / q, soft.height / q);
  g.restore();
}

function renderBackdropShot(g, t, S, bd, fg) {
  drawBackdrop(g, bd.bg, bd.haze, t);
  g.save();
  applyCamera(g, liveCam(fg, t, 2.2));
  drawAlarmStation(g, HX, HY, 1.8, { t, alarm: 0, alarmPulled: 0 });
  drawPeople(g, t, S, { fearOff: bd.fearOff });
  drawHQForeground(g, 'alarm', { ...SET, t, lightsDim: 0 });
  g.restore();
}

export function render(g, t, S) {
  const shot = shotAt(t, S);
  const span = (a, b) => clamp((t - S.T(a)) / (S.T(b) - S.T(a)));
  const sine = (k) => -(Math.cos(Math.PI * k) - 1) / 2;
  if (shot === 'A') renderAlarmShot(g, t, S, lerpCam(CAM.A0, CAM.A1, sine(span('scene.start', 's04b01+1.31'))), { ceoHaze: 1.3 });
  else if (shot === 'B') renderBackdropShot(g, t, S, BD.two, BD.two.fg);
  else if (shot === 'C') renderBackdropShot(g, t, S, BD.ceoC, BD.ceoC.fg);
  else if (shot === 'D') renderAlarmShot(g, t, S, lerpCam(CAM.D0, CAM.D1, sine(span('s04b03', 's04b04'))), { ceoHaze: 1 });
  else if (shot === 'E') renderBackdropShot(g, t, S, BD.twoT, BD.twoT.fg);
  else if (shot === 'F') renderAlarmShot(g, t, S, lerpCam(CAM.F0, CAM.F1, sine(span('s04b05', 's04b06'))), { ceoHaze: 1 });
  else renderBackdropShot(g, t, S, BD.ceoG0, lerpCam(BD.ceoG0.fg, BD.ceoG1.fg, sine(span('s04b06', 'scene.end'))));
  grade(g, COLD, 0);
  vignette(g, VIGNETTE);
}
