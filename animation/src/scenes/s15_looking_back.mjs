// s15 · looking_back · MIND_HQ (back view) intercut with Fear at the cage threshold (backOfMind).
// "My other emotions were looking back." — Fear's POV down the room: the four emotions turned on their
// stools, looking straight at Fear; one smile each; then back to work.
import { clamp, lerp, mix, fbm, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { drawHQ, drawHQForeground, HQ_VIEWS } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf } from '../chars/self.mjs';
import { drawEmotion, LOOKBACK_SMILE } from '../chars/emotions.mjs';

export const id = 's15';

export const sfx = [
  // the four turn back to work (soft cloth as they swivel), JOY's button, CALM's lever
  { at: 's15b03+3.16', name: 'cloth_rustle', gain: -19 },
  { at: 's15b03+3.8', name: 'cloth_rustle', gain: -20, pan: -0.4 },
  { at: 's15b03+4.48', name: 'console_beeps', gain: -18, pan: -0.5 },
  { at: 's15b03+4.85', name: 'console_beeps', gain: -22, pan: 0.5, rate: 0.9 },
];

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const CAGE_B = [430, 1630, 0.952];
const THRESH = [440, 1648, 0.97];
const BK = HQ_VIEWS.back.anchors;
const OFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 };   // idle-life offsets (§5.11)
const SIDE = { JOY: 1, SADNESS: 1, ANGER: -1, CALM: -1 };          // lookSide: faces turn to the centre (§1.2)

// ---------------------------------------------------------------- local helpers
function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function starlight(g, x, y, r, k) {
  if (k <= 0) return;
  g.save(); g.globalCompositeOperation = 'screen';
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, `rgba(176,150,255,${0.30 * k})`); gr.addColorStop(0.55, `rgba(110,200,255,${0.12 * k})`);
  gr.addColorStop(1, 'rgba(110,200,255,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore();
}
const cam = (t, c, amp = 2.5) => { const d = drift(t, amp); return { ...c, shakeX: d.dx, shakeY: d.dy, rot: d.dr }; };

// ---------------------------------------------------------------- shots
// pov (wide) → Fear → two close two-shots of the smiles (JOY+SADNESS, then ANGER+CALM, held through "They smiled")
// → Fear's answering smile on "just for a moment" → the wide on "then went back to helping me"
function shotOf(t, S) {
  if (t < S.T('s15b01+1.9')) return 'pov';
  if (t < S.T('s15b02')) return 'fearA';
  if (t < S.T('s15b02+2.1')) return 'closeA';
  if (t < S.T('s15b03+0.64')) return 'closeB';
  if (t < S.T('s15b03+2.76')) return 'fearB';
  return 'screen';
}

export function render(g, t, S) {
  const shot = shotOf(t, S);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#06050d'; g.fillRect(0, 0, 720, 1280); g.restore();
  if (shot === 'fearA' || shot === 'fearB') renderFear(g, t, S, shot);
  else renderBack(g, t, S, shot);
}

// ================================================================= BACK VIEW (the console, Fear's POV)
function backCam(t, S, shot) {
  if (shot === 'pov') {
    const k = S.k(t, [['scene.start', 0], ['s15b01+1.9', 1, 'sine']]);
    return cam(t, { x: 450, y: lerp(800, 705, k), zoom: lerp(0.8, 0.97, k) }, 2);
  }
  if (shot === 'closeA' || shot === 'closeB') {
    // close two-shots at zoom ≈2.2: the two 3/4 faces (they sit on the side of each head that turns to the centre)
    // land at screen x ≈ 130 and ≈ 590, y ≈ 500–620, the screen of consciousness above them; a slow drift right
    // (≈20 px/s) carries the eye on toward the next pair
    const A = shot === 'closeA';
    const a = S.T(A ? 's15b02' : 's15b02+2.1'), b = S.T(A ? 's15b02+2.1' : 's15b03+0.64');
    const k = clamp((t - a) / (b - a));
    return cam(t, A ? { x: lerp(262, 280, k), y: 800, zoom: 2.15 + 0.04 * k }
                    : { x: lerp(624, 642, k), y: 785, zoom: 2.15 + 0.04 * k }, 1.6);
  }
  // 'screen': settle back on the whole console row (JOY and CALM inside the face-safe band); a whisper of a push
  const k = S.k(t, [['s15b03+2.76', 0], ['scene.end+1', 1, 'linear']]);
  return cam(t, { x: 450, y: lerp(655, 660, k), zoom: lerp(0.93, 0.955, k) }, 2.5);
}

// per-emotion timing of the smile (closeA: JOY then SADNESS; closeB: ANGER then CALM — every smile is full and held
// ≥ 0.9 s on screen, and all four are still smiling, still looking back, through "They smiled") and of the turn back
// (in the wide, a beat after the cut, on "went back to helping me": ANGER first, JOY last)
const SMILE_AT = { JOY: 's15b02+0.15', SADNESS: 's15b02+0.6', ANGER: 's15b02+2.4', CALM: 's15b02+2.95' };
const BACK_AT = { ANGER: 's15b03+3.16', CALM: 's15b03+3.4', SADNESS: 's15b03+3.6', JOY: 's15b03+3.9' };
const add = (a, s) => a.replace(/([+-][0-9.]+)?$/, (m) => `+${(+(m || 0) + s).toFixed(3)}`);

function emotionPose(name, t, S) {
  const te = t + OFF[name];
  const side = SIDE[name];
  const sm = S.k(t, [[SMILE_AT[name], 0], [add(SMILE_AT[name], 0.55), 1, 'sine']]);
  const lb = S.k(t, [[BACK_AT[name], 1], [add(BACK_AT[name], name === 'JOY' ? 0.45 : 0.6), 0, 'cubic']]);
  const work = 1 - lb;                                      // back at work
  const gaze = { lookX: fbm(te * 0.4, 21) * 0.07, lookY: fbm(te * 0.37, 23) * 0.06 };
  const pose = { t: te, view: 'back', lookBack: lb, lookSide: side, armL: 'pressButton', armR: 'pressButton' };
  let face;
  if (name === 'JOY') {
    // b01: very still, eyes wide, brows lifted, lips parted · b02: the warm wide smile + a tiny finger wave
    const f0 = { browUp: 0.55, lidU: -0.22, open: 0.3, round: 0.35, smile: -0.22, pupil: 1.15 };
    const f1 = { ...LOOKBACK_SMILE, browUp: 0.32 };
    face = mix(f0, f1, sm);
    face = mix(face, { smile: 0.25, lidL: 0.15 }, work);
    // the tuft perks: a little upward pop of the head when the smile lands
    pose.headDY = -4 * Math.sin(Math.PI * clamp((t - S.T(add(SMILE_AT.JOY, 0.25))) / 0.45));
    const wave = S.k(t, [['s15b02+0.3', 0], ['s15b02+0.55', 1], ['s15b02+1.3', 1], ['s15b02+1.6', 0]]);
    if (wave > 0.01) {
      const w = Math.sin((t - S.T('s15b02+0.3')) * Math.PI * 2 * 2.2) * 0.3 * wave;
      pose.armR = { target: [lerp(55, 92, wave), lerp(-201, -262, wave)], bend: -1, hand: 'palm', layer: 'over', handAng: -Math.PI / 2 + 0.25 + w };
    }
    // back at work: the press, with a bounce of the tuft
    const tap = S.k(t, [['s15b03+4.35', 0], ['s15b03+4.5', 8], ['s15b03+4.72', 0]]);
    if (work > 0.5) pose.armR = { preset: 'pressButton', dy: tap };
    pose.headDY = (pose.headDY || 0) + 3 * Math.sin((t - S.T('s15b03+4.5')) * 9) * clamp(1 - (t - S.T('s15b03+4.5')) / 1.2) * (t > S.T('s15b03+4.5') ? 1 : 0);
  } else if (name === 'SADNESS') {
    // b01: inner brows up, wet shining eyes, lower lip tucked · b02: small wet tilted smile, slow blink
    const f0 = { browIn: 0.75, browUp: 0.2, tears: 1, sparkle: 0.6, pressed: 0.5, smile: -0.12, lidU: 0.05 };
    const f1 = { browIn: 0.6, tears: 0.9, sparkle: 0.5, smile: 0.88, open: 0.06, lidL: 0.32, blush: 0.35, lidU: 0.12 };
    face = mix(f0, f1, sm);
    // b03: one more wet smile, cheeks faintly blushed, then back to its dial
    face.blush = (face.blush || 0) + 0.25 * S.k(t, [['s15b03+3.0', 0], ['s15b03+3.5', 1]]);
    face = mix(face, { browIn: 0.2, tears: 0.4, smile: 0.15, blush: 0.4 }, work);
    face.blink = blinkAt(t, S.T(add(SMILE_AT.SADNESS, 0.75)), 0.42) + blinkAt(t, S.T('s15b03+3.3'), 0.36);
    pose.headTilt = 0.1 * sm * (1 - work);
    pose.lean = -0.025 * (1 - work);                                    // "peeking around Joy"
    if (work > 0.5) {                                                   // turning its dial
      const ph = (t - S.T('s15b03+4.2')) * 2.2;
      pose.armL = { preset: 'pressButton', dx: 3 * Math.sin(ph), dy: 3 * Math.cos(ph) * clamp(ph) };
    }
  } else if (name === 'ANGER') {
    // b01: arms folded but looking; brows not quite as low · b02: a corner twitches up, one gruff nod
    const f0 = { browIn: -0.15, browSquish: 0.25, lidU: 0.12, pressed: 0.35, smile: -0.1 };
    const twitch = S.k(t, [[SMILE_AT.ANGER, 0], [add(SMILE_AT.ANGER, 0.2), 0.78, 'outCubic'], [add(SMILE_AT.ANGER, 0.45), 0.42], [add(SMILE_AT.ANGER, 0.6), 0.5]]);
    face = { ...f0, smile: -0.1 + twitch, pressed: 0.35 * (1 - twitch * 1.5) };
    face = mix(face, { browIn: -0.2, smile: 0.05 }, work);
    pose.noBase = true;
    face.browIn -= 0.3;                                                // keep the grump, gentler than the base
    const nodK = S.k(t, [[add(SMILE_AT.ANGER, 0.55), 0], [add(SMILE_AT.ANGER, 0.8), 1], [add(SMILE_AT.ANGER, 1.15), 0]]);
    pose.headDY = 7 * nodK;
    face.lookY = (face.lookY || 0) + 0.25 * nodK;
    const fold = S.k(t, [['s15b03+3.1', 1], ['s15b03+3.5', 0]]);
    if (fold > 0.5) { pose.armL = 'hugSelf'; pose.armR = 'hugSelf'; }
    // b03: nudges the CEO (left hand to the CEO's arm), then the same hand lifts and points up at the screen
    const nudge = S.k(t, [['s15b03+3.45', 0], ['s15b03+3.75', 1], ['s15b03+3.9', 0.75], ['s15b03+4.05', 1], ['s15b03+4.3', 0.6]]);
    const pt = S.k(t, [['s15b03+4.2', 0], ['s15b03+4.65', 1]]);
    if (fold <= 0.5 && (nudge > 0.01 || pt > 0.01)) {
      const nx = lerp(-62, -128, nudge), ny = lerp(-186, -205, nudge);
      pose.armL = { target: [lerp(nx, -104, pt), lerp(ny, -300, pt)], bend: lerp(1, -1, pt) > 0 ? 1 : -1, hand: pt > 0.5 ? 'point' : 'fist', layer: 'back', boneK: [1, lerp(1, 1.2, pt)],
        handAng: pt > 0.5 ? -Math.PI / 2 - 0.55 : undefined };
    }
    face.lookX = (face.lookX || 0) - 0.25 * pt;
  } else {
    // CALM: lids level at half, faint closed smile already there · b02 slow deliberate blink, soft closed smile
    const f0 = { lidU: 0.12, smile: 0.12 };
    const f1 = { lidU: 0.12, smile: 0.42, lidL: 0.2 };
    face = mix(f0, f1, sm);
    face.blink = blinkAt(t, S.T(add(SMILE_AT.CALM, 0.62)), 0.55);
    face.noAutoBlink = Math.abs(t - S.T(add(SMILE_AT.CALM, 0.9))) < 0.9;
    face = mix(face, { lidU: 0.15, smile: 0.25 }, work);
    // eases a lever forward
    const lever = S.k(t, [['s15b03+4.05', 0], ['s15b03+4.9', 1]]);
    if (work > 0.5) pose.armR = { preset: 'pressButton', dy: 9 * lever, dx: -3 * lever };
  }
  pose.face = { ...face, lookX: (face.lookX || 0) + gaze.lookX * (1 - work * 0.5), lookY: (face.lookY || 0) + gaze.lookY };
  return pose;
}

function ceoPose(t, S) {
  // back to us at the console; the pen paused mid-stroke; head turns a few degrees ("heard something")
  const turn = S.k(t, [['scene.start', 0], ['s15b01+1.0', 0], ['s15b01+1.9', 0.2], ['s15b03+3.5', 0.2], ['s15b03+3.9', 0.04]]);
  const nod = Math.max(0, Math.sin(Math.PI * clamp((t - S.T('s15b03+3.95')) / 0.35))) * 6 +
              Math.max(0, Math.sin(Math.PI * clamp((t - S.T('s15b03+4.35')) / 0.3))) * 4;
  // writing: the right forearm scribbles (only the elbow reads from behind)
  const write = S.k(t, [['s15b03+4.4', 0], ['s15b03+4.7', 1]]);
  const wph = (t - S.T('s15b03+4.4')) * 7;
  // back to writing: the head bows a touch to the clipboard and the writing elbow (poking out at the right side
  // of the back) ticks with the strokes
  return {
    t, outfit: 'ceo', view: 'back', clipboard: true, headTurn: turn, headDY: nod + 4 * write, headTilt: 0.03 + 0.03 * write,
    armR: { target: [34 + 7 * Math.sin(wph) * write, -292 + 4 * Math.sin(wph * 1.7) * write], bend: 1, hand: 'grip', front: true },
  };
}

function renderBack(g, t, S, shot) {
  const glowPress = S.k(t, [['s15b03+4.45', 0], ['s15b03+4.6', 1, 'outCubic'], ['scene.end', 0.7]]);
  const st = { t, lightsDim: 0.15, consoleGlow: 1.0, mist: 0.3, screenMode: 'room', consolePress: { 0: glowPress, 13: 0.5 * S.k(t, [['s15b03+4.2', 0], ['s15b03+4.9', 1]]) } };
  const camera = backCam(t, S, shot);
  // in the close two-shots only the pair in frame (+ the CEO's shoulder at the edge) is drawn: saves ≈ 8 ms
  const half = 360 / camera.zoom + 60;
  const seen = (x) => Math.abs(x - camera.x) < half;
  g.save();
  applyCamera(g, camera);
  drawHQ(g, 'back', st);
  // JOY's pressed button sits right behind her head (button1 126,802): its flare shows as a warm halo round her
  if (glowPress > 0.01) {
    const [bx, by] = BK.button1;
    g.save(); g.globalCompositeOperation = 'lighter';
    const gr = g.createRadialGradient(bx + 8, by - 18, 4, bx + 8, by - 18, 82);
    gr.addColorStop(0, `rgba(255,214,130,${0.55 * glowPress})`); gr.addColorStop(0.45, `rgba(255,170,70,${0.22 * glowPress})`);
    gr.addColorStop(1, 'rgba(255,170,70,0)');
    g.fillStyle = gr; g.fillRect(bx - 80, by - 106, 176, 176); g.restore();
  }
  // emotions + CEO by y (all on the same row: left → right)
  const SLOT = { JOY: 'consoleBack1', SADNESS: 'consoleBack2', ANGER: 'consoleBack3', CALM: 'consoleBack4' };
  for (const name of ['JOY', 'SADNESS']) if (seen(BK[SLOT[name]][0])) drawEmotion(g, name, ...BK[SLOT[name]], emotionPose(name, t, S));
  if (seen(BK.consoleBackMid[0])) drawSelf(g, ...BK.consoleBackMid, ceoPose(t, S));
  for (const name of ['CALM', 'ANGER']) if (seen(BK[SLOT[name]][0])) drawEmotion(g, name, ...BK[SLOT[name]], emotionPose(name, t, S));
  drawHQForeground(g, 'back', st);
  g.restore();
  grade(g, 0, 0.2);
  vignette(g, 0.35);
}

// ================================================================= FEAR at the threshold (reverse shots)
function fearFace(t, S, shot) {
  const gx = fbm(t * 0.4, 41) * 0.06, gy = fbm(t * 0.35, 43) * 0.05;
  if (shot === 'fearA') {
    // eyes widen; lower lip quivers; brows lift into a hopeful, worried shape; very still
    const w = S.k(t, [['s15b01+1.95', 0], ['s15b01+2.35', 1, 'outCubic']]);
    return {
      lookX: -0.42 + gx, lookY: -0.06 + gy,
      lidU: lerp(0.05, -0.25, w), pupil: lerp(1.1, 1.3, w), browIn: lerp(0.45, 0.75, w), browUp: lerp(0.15, 0.5, w),
      lidTilt: 0.15, smile: -0.12, open: 0.04, tremble: 0.55 * w, tears: 0.55, sparkle: 0.35, blush: 0.1,
    };
  }
  // fearB: a wobbly smile answers theirs before it can stop it; then its eyes fill again
  const sm = S.k(t, [['s15b03+0.7', 0], ['s15b03+1.4', 1, 'sine']]);
  const fill = S.k(t, [['s15b03+1.5', 0], ['s15b03+2.6', 1, 'sine']]);
  // the eyes stay open while they fill (heavy lids read as sleepy at phone size): the water rises on the lower lid,
  // the inner brows lift, the smile wobbles but stays; a slow blink pushes a bead of water onto the lid
  return {
    lookX: -0.4 + gx, lookY: -0.04 + gy,
    lidU: lerp(-0.22, -0.1, sm) - 0.04 * fill, lidL: 0.3 * sm + 0.06 * fill, pupil: 1.25 + 0.1 * fill,
    browIn: lerp(0.7, 0.5, sm) + 0.32 * fill, browUp: lerp(0.45, 0.25, sm) + 0.18 * fill,
    lidTilt: 0.12 + 0.12 * fill, smile: lerp(-0.1, 0.5, sm) - 0.08 * fill, open: 0.03 + 0.04 * sm,
    tremble: 0.3 + 0.45 * fill, tears: lerp(0.55, 1, fill), sparkle: 0.4 + 0.25 * fill, blush: lerp(0.12, 0.38, sm),
    tearL: 0.22 * S.k(t, [['s15b03+2.2', 0], ['s15b03+2.7', 1]]),
    blink: blinkAt(t, S.T('s15b03+1.95'), 0.36),
  };
}

function renderFear(g, t, S, shot) {
  const st = { t, lightsDim: 0.3, mist: 0.48 };
  // a breath of push-in on each reverse
  const t0 = S.T(shot === 'fearA' ? 's15b01+1.9' : 's15b03+0.64');
  const z = 3.0 + 0.06 * clamp((t - t0) / 2.5);
  g.save();
  applyCamera(g, cam(t, { x: 440, y: 1430, zoom: z }, 2));
  drawHQ(g, 'backOfMind', st);
  // the hood (face y≈243) is far above this frame, so its cosmos (0.5 from s14b10) is not drawn: saves ≈2 ms
  const vpose = { t, ...STARE_B, idle: 0.5, cosmos: 0, shadowSpread: 0.7, handL: { bend: 1, show: 0, defer: 'hand' } };
  drawVoid(g, ...VOID_B, vpose);
  const cst = { t, door: 0.9, locked: 0 };
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front' });
  const [fx, fy, fs] = THRESH;
  // hands clasped against its scarf, held very still (breath held)
  const hold = shot === 'fearA' ? 0.45 : 0.75;
  drawFear(g, fx, fy, fs, {
    t, facing: -1, headTilt: 0.12, headTurn: -0.06, breathe: hold, tremble: 0,
    face: fearFace(t, S, shot),
    armL: { target: [-7, -127], bend: -1, front: true, hand: 'fist' },
    armR: { target: [7, -124], bend: 1, front: true, hand: 'fist' },
  });
  starlight(g, fx + 25 * fs, fy - 250 * fs, 190 * fs, 0.5);
  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  grade(g, 0.2, 0.1);
  vignette(g, 0.4);
}
