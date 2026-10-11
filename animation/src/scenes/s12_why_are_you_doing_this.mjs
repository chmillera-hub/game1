// s12 · why_are_you_doing_this — Fear's accusations meet absolute silence and collapse into pleas.
// backOfMind throughout. The Void never moves (STARE_B, idle 0, hand hidden with bend 1). The camera keeps
// changing sizes around a stillness that gives nothing back; Fear does all the moving.
import { W, H, clamp, lerp, ease, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { makeExpr, withSpeech } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawCage, cagePoint } from '../sets/props.mjs';

export const id = 's12';

// ---------------------------------------------------------------- staging constants (staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const CAGE_B = [430, 1630, 0.952];
const VOID_ARM_B = { bend: 1 };
const THRESH = [440, 1648, 0.97];
const FS = CAGE_B[2];
// occupantBack / occupantFront nudged +22 px right: with the gate ajar (0.3) its stiles stand at x 395 / 464 and the lock
// jamb at 505; from x 452 the near eye sits in the 395–464 gap and the far eye between 464 and 505, so no bar
// crosses an iris in the full-cage shots (b03, b06). Centred at 430 a stile ran through each eye.
const OCC_SIDE = [363, 1619], OCC_BACK = [452, 1598], OCC_FRONT = [452, 1630];
const DOORWAY_Y = 1642;

export const sfx = [
  { at: 'scene.start+0.564', name: 'footsteps', gain: -19, rate: 1.31, until: 'scene.start+1.25', fade: 0.12 }, // two tiny shuffles back: steps land on the contacts (+0.63, +1.05)
  { at: 's12b05+0.35', name: 'breath_shaky', gain: -14 },                                          // breath held … the exhale (file 1.45) leaks out at +1.8 with the body
  { at: 's12b06+0.32', name: 'footsteps', gain: -18, until: 's12b06+1.15', fade: 0.12 },           // the step to the gate
  { at: 's12b07-0.05', name: 'cage_creak', gain: -15, rate: 1.5 },                                 // the gate pushed wide
  { at: 's12b07+0.5', name: 'footsteps', gain: -18, until: 's12b07+0.75', fade: 0.08 },            // stepping out: foot lands at +0.58
  { at: 's12b07+0.88', name: 'footsteps', gain: -11, until: 's12b07+1.25', fade: 0.1 },            // the tiny furious stamp on 'hurt'
  { at: 's12b09+1.9', name: 'sob', gain: -14 },                                                    // 'forever' breaks into a sob
  { at: 's12b10+0.15', name: 'cloth_rustle', gain: -21 },                                          // nose wiped on the scarf
  { at: 's12b10+1.1', name: 'sob', gain: -21, until: 's12b10+1.55', fade: 0.12 },                  // a hiccup
  { at: 's12b11+1.95', name: 'breath_shaky', gain: -23, until: 's12b11+3.6', fade: 0.4 },          // small uneven breaths in the narrator's pause
];

// ---------------------------------------------------------------- helpers
function finish(g, cold, warm, vig) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  if (warm > 0) { g.globalCompositeOperation = 'overlay'; g.fillStyle = `rgba(255,170,90,${0.4 * warm})`; g.fillRect(0, 0, W, H); }
  g.globalCompositeOperation = 'source-over';
  vignette(g, vig);
  g.restore();
}
const withDrift = (cam, t, amp = 2.5) => { const d = drift(t, amp, 3); return { ...cam, shakeX: d.dx, shakeY: d.dy, rot: d.dr }; };
const camLerp = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), zoom: Math.exp(lerp(Math.log(a.zoom), Math.log(b.zoom), k)) });
const E = (...p) => makeExpr(...p);
const bump = (t, c, w) => { const d = Math.abs(t - c) / w; return d >= 1 ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * d); };
const lerp2 = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
// body hitches that follow the sob sfx file (hitches at 0.05 / 0.21 / 0.35, whimper catches 0.56 / 0.83)
const sobHitch = (t, at, catches = 1) => bump(t, at + 0.07, 0.07) + bump(t, at + 0.23, 0.07) + bump(t, at + 0.37, 0.07)
  + catches * (0.6 * bump(t, at + 0.58, 0.09) + 0.5 * bump(t, at + 0.85, 0.09));

// ---------------------------------------------------------------- shots
// [start anchor, camera fn, cage mode]   cage: 'full' | 'cheat' (inside-cage close: back layer only, §1.7-10)
function shot(t, S) {
  const T = (a) => S.T(a);
  if (t < T('s12b02-0.3')) {
    const k = ease.sine(clamp((t - S.start) / (T('s12b02') - S.start)));
    return { cam: withDrift(camLerp({ x: 560, y: 900, zoom: 0.8 }, { x: 560, y: 940, zoom: 0.8 }, k), t), cage: 'full' };
  }
  if (t < T('s12b03-0.25')) return { cam: withDrift({ x: 440, y: 1400, zoom: 2.2 }, t, 2), cage: 'cheat' };
  if (t < T('s12b04-0.2')) {
    const k = ease.sine(clamp((t - T('s12b03-0.25')) / 1.6));
    return { cam: withDrift(camLerp({ x: 470, y: 1300, zoom: 1.3 }, { x: 468, y: 1296, zoom: 1.34 }, k), t), cage: 'full' };
  }
  if (t < T('s12b05')) return { cam: withDrift({ x: 440, y: 1400, zoom: 2.2 }, t, 2), cage: 'cheat' };
  if (t < T('s12b06-0.1')) return { cam: { x: 500, y: 889, zoom: 0.72 }, cage: 'full' };                     // LOCKED
  if (t < T('s12b07-0.3')) {
    const k = ease.sine(clamp((t - T('s12b06-0.1')) / 2.6));
    return { cam: withDrift(camLerp({ x: 450, y: 1380, zoom: 1.6 }, { x: 452, y: 1384, zoom: 1.66 }, k), t), cage: 'full' };
  }
  if (t < T('s12b08-0.3')) return { cam: withDrift({ x: 560, y: 980, zoom: 0.8 }, t), cage: 'full' };
  if (t < T('s12b09')) return { cam: withDrift({ x: 450, y: 1430, zoom: 2.0 }, t, 2), cage: 'full' };
  if (t < T('s12b10')) {
    const k = ease.sine(clamp((t - T('s12b09')) / (T('s12b10') - T('s12b09'))));
    return { cam: withDrift(camLerp({ x: 450, y: 1430, zoom: 2.0 }, { x: 450, y: 1440, zoom: 2.15 }, k), t, 2), cage: 'full' };
  }
  return { cam: { x: 500, y: 889, zoom: 0.72 }, cage: 'full' };                                               // LOCKED
}

// ---------------------------------------------------------------- Fear
const FROZEN = E({ browIn: 0.8, browUp: 0.65, lidU: -0.22, pupil: 0.62, smile: -0.35, open: 0.12, wide: 0.05, tears: 0.85, stream: 0.6, lookX: 0.36, lookY: -1 });
const ACCUSE = E({ browIn: 0.95, browUp: 0.55, lidU: -0.12, pupil: 0.7, smile: -0.45, tremble: 0.55, tears: 0.85, stream: 0.55, lookX: 0.38, lookY: -1 });
const CRACK = E(ACCUSE, { browUp: 0.9, browIn: 1, lidU: -0.28, pupil: 0.66 });
const CERTAIN = E({ browIn: 0.9, browUp: 0.35, lidTilt: 0.35, lidU: 0.04, smile: -0.55, tremble: 0.95, tears: 0.95, stream: 0.55, pupil: 0.75, lookX: 0.38, lookY: -1 });
// suspicious squint from BELOW (lower lids high, inner corners low); a heavy upper lid over an up-looking iris read as an eye-roll
const SUSPECT = E({ lidU: 0.12, lidL: 0.85, lidTilt: -0.2, browIn: -0.22, browUpL: -0.32, browUpR: 0.2, browSquish: 0.6, smile: -0.3, wide: -0.15, tremble: 0.4, tears: 0.7, stream: 0.5, pupil: 0.8, lookX: 0.38, lookY: -0.8 });
const CONFUSED = E({ browUpL: 0.7, browUpR: -0.3, browIn: 0.35, lidU: 0.05, lidL: 0.08, smile: -0.32, wide: -0.12, tremble: 0.35, tears: 0.78, stream: 0.5, pupil: 0.85, lookX: 0.38, lookY: -1 });
const WAITING = E({ browIn: 0.72, browUp: 0.48, lidU: -0.16, pupil: 0.68, smile: -0.22, pressed: 0.55, tears: 0.82, stream: 0.5, lookX: 0.38, lookY: -1 });
const CRUMBLE = E({ browIn: 1, browUp: 0.4, lidTilt: 0.6, lidU: 0.18, lidL: 0.22, smile: -0.62, tremble: 0.85, pressed: 0.25, tears: 1, stream: 0.6, pupil: 0.8, lookX: 0.38, lookY: -0.95 });
const CRY = E({ browIn: 1, browUp: 0.35, lidTilt: 0.75, lidU: 0.16, lidL: 0.32, smile: -0.75, wide: 0.3, tremble: 0.95, tears: 1, stream: 0.72, pupil: 0.85, lookX: 0.36, lookY: -0.9 });
const FURY = E({ browIn: -0.32, browSquish: 0.75, lidU: 0.14, lidL: 0.3, lidTilt: -0.05, smile: -0.6, wide: 0.35, teeth: 0.45, tremble: 0.55, tears: 1, stream: 0.75, pupil: 0.8, lookX: 0.42, lookY: -1 });
// squeezed half shut from BELOW (cheeks up), the upper lids only a little: heavy upper lids + eyes up read as an eye-roll
const SHOUT = E({ lidU: 0.24, lidL: 0.72, lidTilt: 0.3, browIn: 1, browUp: 0.3, browSquish: 1, open: 0.2, wide: 0.6, teeth: 0.7, smile: -0.5, tremble: 0.5, tears: 1, stream: 0.8, pupil: 0.8, lookX: 0.36, lookY: -0.55 });
const PLEA = E({ browIn: 1, browUp: 0.45, lidTilt: 0.85, lidU: 0.12, lidL: 0.34, smile: -0.85, wide: 0.42, tremble: 1, tears: 1, stream: 0.9, pupil: 0.85, lookX: 0.36, lookY: -0.8 });
const SOBBING = E(PLEA, { lidU: 0.92, lidL: 0.5, open: 0.22, lookY: 0.3 });
const SPENT = E({ browIn: 0.78, browUp: 0.1, lidTilt: 0.7, lidU: 0.42, lidL: 0.15, smile: -0.45, tremble: 0.3, tears: 0.7, stream: 0.75, pupil: 0.9, lookX: 0.05, lookY: 0.62 });

function fearState(t, S) {
  const T = (a) => S.T(a);

  // ---------------- position / walking
  // shuffle back: occupantSide → occupantBack (two small steps), eyes never leave the hood
  const sh = clamp((t - T('scene.start+0.2')) / (T('s12b01+0.6') - T('scene.start+0.2')));
  let pos = lerp2(OCC_SIDE, OCC_BACK, ease.sine(sh));
  let walk = sh > 0 && sh < 1 ? sh * 2 * Math.PI : 0;
  let scale = FS;
  // b06: one step forward to the gate (occupantFront)
  const st6 = clamp((t - T('s12b06+0.4')) / 0.6);
  if (st6 > 0) { pos = lerp2(OCC_BACK, OCC_FRONT, ease.sine(st6)); walk = st6 < 1 ? st6 * Math.PI : 0; }
  // b07: through the gate onto the threshold (two quick steps), then the stamp on 'hurt'
  const st7 = clamp((t - T('s12b07+0.32')) / 0.52);
  if (st7 > 0) {
    pos = lerp2(OCC_FRONT, THRESH, ease.sine(st7));
    scale = lerp(FS, THRESH[2], ease.sine(st7));
    walk = st7 < 1 ? st7 * 2 * Math.PI : 0;
  }
  const stampT = T('s12b07+0.96');
  const stampLift = t > stampT - 0.16 && t < stampT ? Math.sin(((t - (stampT - 0.16)) / 0.16) * Math.PI / 2) : 0;
  if (stampLift > 0) walk = 2 * Math.PI + stampLift * Math.PI / 2;
  const stampHit = bump(t, stampT + 0.05, 0.1);

  // ---------------- face (keyed through the beats)
  const faceK = S.k(t, [
    ['scene.start-1', FROZEN], ['s12b01-0.1', FROZEN], ['s12b01+0.25', ACCUSE], ['s12b01+0.82', ACCUSE], ['s12b01+1.0', CRACK, 'out'],
    ['s12b01.end+0.15', CRACK], ['s12b01.end+0.6', ACCUSE],
    ['s12b02-0.2', CERTAIN], ['s12b02.end+0.2', CERTAIN],
    ['s12b03-0.15', SUSPECT, 'out'], ['s12b03.end+0.1', SUSPECT],
    ['s12b04+0.05', CONFUSED], ['s12b04.end+0.2', E(CONFUSED, { browUpL: 0.55, browIn: 0.55 })],
    ['s12b05+0.25', WAITING], ['s12b05+2.1', WAITING], ['s12b05+2.95', CRUMBLE],
    ['s12b06+0.3', CRY], ['s12b06.end+0.5', CRY],
    ['s12b07-0.05', FURY, 'out'], ['s12b07.end+0.2', FURY],
    ['s12b08-0.15', SHOUT, 'out'], ['s12b08.end+0.2', SHOUT],
    ['s12b09+0.35', PLEA], ['s12b09+1.75', PLEA], ['s12b09+2.05', SOBBING, 'out'], ['s12b09+2.9', SOBBING],
    ['s12b10+0.5', SPENT],
  ]);
  const face = { ...faceK };

  // gaze: eyelines are absolute (the hood up-right, the gate down in front, the glow up-left)
  const HOOD = { lookX: 0.38, lookY: -1 }, GATE = { lookX: 0.16, lookY: 0.95 };
  let gz = null;
  const gaze = (keys) => S.k(t, keys);
  if (t >= T('s12b02-0.3') && t < T('s12b03-0.25')) {
    // "eyes flick to the open gate and back up, as if the gate were bait"
    gz = gaze([['s12b02+0.18', HOOD], ['s12b02+0.3', GATE, 'out'], ['s12b02+0.66', GATE], ['s12b02+0.8', HOOD, 'out']]);
  } else if (t >= T('s12b03-0.25') && t < T('s12b04-0.2')) {
    // suspicious: the eyes dart to the fold where the hand went, then back to the hood
    const HOOD_SQ = { lookX: 0.38, lookY: -0.8 }, FOLD_SQ = { lookX: 0.06, lookY: -0.86 };
    gz = gaze([['s12b03-0.25', HOOD], ['s12b03+0.12', HOOD_SQ], ['s12b03+0.22', FOLD_SQ, 'out'], ['s12b03+0.5', FOLD_SQ], ['s12b03+0.6', HOOD_SQ, 'out'], ['s12b03+0.95', HOOD_SQ], ['s12b03+1.03', { lookX: 0.1, lookY: -0.84 }, 'out'], ['s12b03+1.2', HOOD_SQ, 'out'], ['s12b04-0.2', HOOD, 'sine']]);
  } else if (t >= T('s12b04-0.2') && t < T('s12b05+0.25')) {
    // the glance at the gate again, longer this time
    gz = gaze([['s12b04+0.2', HOOD], ['s12b04+0.34', GATE, 'out'], ['s12b05-0.05', GATE], ['s12b05+0.2', HOOD, 'out']]);
  } else if (t >= T('s12b05+0.25') && t < T('s12b06')) {
    // searching the hood for any sign; following its stare into the distance; back up
    gz = gaze([['s12b05+0.3', HOOD], ['s12b05+0.4', { lookX: 0.27, lookY: -0.9 }, 'out'], ['s12b05+0.7', { lookX: 0.27, lookY: -0.9 }],
      ['s12b05+0.8', { lookX: 0.5, lookY: -1 }, 'out'], ['s12b05+1.1', { lookX: 0.5, lookY: -1 }], ['s12b05+1.2', { lookX: 0.33, lookY: -0.82 }, 'out'],
      ['s12b05+1.5', { lookX: 0.33, lookY: -0.82 }], ['s12b05+2.05', { lookX: -0.2, lookY: -0.88 }, 'sine'],   // along its stare to the far glow
      ['s12b05+2.35', { lookX: -0.2, lookY: -0.88 }], ['s12b05+2.6', HOOD, 'sine']]);
  } else if (t >= T('s12b06') && t < T('s12b07')) {
    // looking at the gate as it steps to it, then back up at the hood for the line's end
    gz = gaze([['s12b06+0.2', { lookX: 0.3, lookY: -0.95 }], ['s12b06+0.45', { lookX: 0.2, lookY: 0.55 }, 'out'], ['s12b06+1.3', { lookX: 0.2, lookY: 0.55 }], ['s12b06+1.55', HOOD, 'out']]);
  } else if (t >= T('s12b10') && t < T('s12b11')) {
    gz = gaze([['s12b10+1.45', { lookX: 0.05, lookY: 0.62 }], ['s12b10+1.6', { lookX: 0.4, lookY: -1 }, 'out'], ['s12b10+2.15', { lookX: 0.4, lookY: -1 }], ['s12b10+2.4', { lookX: 0.0, lookY: 0.6 }, 'sine']]);
  }
  if (gz) { face.lookX = gz.lookX; face.lookY = gz.lookY; }
  // the glances DOWN at the gate (b02 flick, b04 longer look): the upper lids follow the eyes down and the head
  // dips after them (~0.12 s later), so it reads as looking at the gate in front, not into the lens
  const gateK = (u) => Math.max(
    S.k(u, [['s12b02+0.18', 0], ['s12b02+0.3', 1, 'out'], ['s12b02+0.66', 1], ['s12b02+0.8', 0, 'out']]),
    S.k(u, [['s12b04+0.2', 0], ['s12b04+0.34', 1, 'out'], ['s12b05-0.05', 1], ['s12b05+0.2', 0, 'out']]));
  const gk = gateK(t), gkHead = gateK(t - 0.12);
  face.lidU += 0.2 * gk; face.browUp -= 0.12 * gk;
  // looking up once in b10: the heavy lids lift with the eyes (hope), then sink again
  const upOnce = S.k(t, [['s12b10+1.45', 0], ['s12b10+1.6', 1, 'out'], ['s12b10+2.15', 1], ['s12b10+2.4', 0, 'sine']]);
  if (upOnce > 0) { face.lidU = lerp(face.lidU, 0.02, upOnce); face.browUp = lerp(face.browUp, 0.45, upOnce); face.lidTilt = lerp(face.lidTilt, 0.4, upOnce); }
  // micro-life: tiny gaze drift (not while frozen at the very start)
  const live = S.k(t, [['scene.start+0.1', 0], ['scene.start+0.5', 1]]);
  face.lookX += 0.03 * live * Math.sin(t * 1.7 + 0.4) ;
  face.lookY += 0.02 * live * Math.sin(t * 1.3 + 1.1);

  // wavering squint in b03
  if (t > T('s12b03-0.2') && t < T('s12b04+0.1')) {
    const w = S.k(t, [['s12b03-0.1', 0], ['s12b03+0.1', 1], ['s12b04-0.15', 1], ['s12b04+0.1', 0]]);
    face.lidL += 0.12 * w * Math.sin(t * 2 * Math.PI * 2.1);
    face.lidU += 0.06 * w * Math.sin(t * 2 * Math.PI * 1.6 + 1);
  }

  // tears: the hanging tear from s11 falls; spills on 'sense'; a new pair on 'forever'
  face.tearR = Math.max(S.k(t, [['scene.start-0.5', 0.07], ['scene.start+0.4', 1, 'in'], ['scene.start+0.41', 0]]),
    S.k(t, [['s12b06+1.0', 0], ['s12b06+2.7', 1], ['s12b06+2.71', 0]]),
    S.k(t, [['s12b09+1.7', 0], ['s12b09+3.4', 1], ['s12b09+3.41', 0]]));
  face.tearL = Math.max(S.k(t, [['s12b06+0.45', 0], ['s12b06+2.1', 1], ['s12b06+2.11', 0]]),
    S.k(t, [['s12b09+1.2', 0], ['s12b09+2.7', 1], ['s12b09+2.71', 0]]));
  if (t > T('s12b06+0.2') && t < T('s12b07')) face.tears = 1;

  // blinks: frozen (no blinks) at the start; then deliberate ones on the shifts
  face.noAutoBlink = true;
  const blinks = [
    ['scene.start+0.32', 0.22], ['s12b01.end+0.3', 0.2], ['s12b02.end+0.25', 0.2], ['s12b03+0.7', 0.12],
    ['s12b04+0.7', 0.25], ['s12b05+2.25', 0.3], ['s12b06+1.75', 0.24], ['s12b07.end+0.25', 0.18],
    ['s12b08+0.55', 0.14], ['s12b08.end+0.35', 0.2], ['s12b09+0.9', 0.22],
    ['s12b10+0.95', 0.25], ['s12b10+2.55', 0.32], ['s12b11+1.1', 0.35], ['s12b11+3.75', 0.75], ['s12b11.end+0.4', 0.4],
  ];
  let bl = 0;
  for (const [a, d] of blinks) bl = Math.max(bl, blinkAt(t, T(a), d));
  // a slow exhausted blink on 'It stood there': hold the lids low a moment
  face.blink = clamp(bl);

  // the quick swallow before the first line: lips pressed, a small dip
  const swallow = bump(t, T('scene.start+0.25'), 0.18);
  face.pressed = clamp((face.pressed || 0) + 0.8 * swallow);

  // ---------------- lip-sync (Fear speaks every line on screen)
  const lip = S.lip('FEAR', t);
  let amount = 1;
  if (t > T('s12b04-0.1') && t < T('s12b04.end+0.1')) amount = 0.8;             // the voice drops
  if (t > T('s12b08-0.1') && t < T('s12b08.end+0.1')) amount = 1.3;             // the most volume Fear has
  let spoken = withSpeech(face, lip, amount);
  if (lip && t > T('s12b08+0.85') && t < T('s12b08+1.35')) spoken = { ...spoken, open: clamp(spoken.open + 0.35 * bump(t, T('s12b08+1.1'), 0.3)), wide: spoken.wide + 0.2 }; // mouth wide on 'standing'

  // ---------------- head
  const hitch = clamp(sobHitch(t, T('s12b09+1.9')) + sobHitch(t, T('s12b10+1.1'), 0));   // the sob after 'forever'; the hiccup
  const headDY = S.k(t, [['scene.start-1', -7], ['s12b01+0.75', -7], ['s12b01+0.95', -12, 'out'], ['s12b01.end+0.3', -11], ['s12b02', -6],
    ['s12b03', -5], ['s12b04+0.3', -2], ['s12b04.end', 2], ['s12b05+0.2', -6, 'out'], ['s12b05+2.4', -6], ['s12b05+2.95', -1],
    ['s12b06+0.5', 2], ['s12b06+1.6', -3], ['s12b07', -5], ['s12b08', -10], ['s12b08.end', -11], ['s12b09+1.0', -6], ['s12b09+2.2', 4],
    ['s12b10+1.45', 5], ['s12b10+1.7', -3, 'out'], ['s12b10+2.2', -3], ['s12b10+2.6', 6, 'sine'], ['s12b11+3.7', 7], ['s12b11+4.4', 8]])
    + 3 * swallow + 3 * stampHit - 3.5 * hitch + 6 * gkHead;
  const headTilt = S.k(t, [['scene.start-1', -0.06], ['s12b01+0.6', -0.06], ['s12b01+1.0', -0.1, 'out'], ['s12b02', -0.05],
    ['s12b03', 0.03], ['s12b04', 0.0], ['s12b04+0.4', 0.11], ['s12b05+0.2', 0.03], ['s12b05+1.6', 0.03], ['s12b05+2.2', -0.06], ['s12b05+2.8', 0],
    ['s12b06+0.6', 0.05], ['s12b07', -0.04], ['s12b08', -0.08], ['s12b09+0.5', -0.02], ['s12b09+2.3', 0.1], ['s12b10+1.5', 0.12], ['s12b10+1.7', 0.02], ['s12b10+2.6', 0.12]])
    + 0.035 * Math.sin(t * 2 * Math.PI * 1.6) * S.k(t, [['s12b06', 0], ['s12b06+0.2', 1], ['s12b06.end', 1], ['s12b06.end+0.2', 0]]);   // a wobbling "no" shake
  const headTurn = S.k(t, [['scene.start-1', 0.28], ['s12b01', 0.28], ['s12b02', 0.25], ['s12b04+0.3', 0.25], ['s12b04+0.5', 0.12], ['s12b05+0.2', 0.25],
    ['s12b05+1.7', 0.25], ['s12b05+2.2', -0.12], ['s12b05+2.4', -0.12], ['s12b05+2.75', 0.25], ['s12b06+0.4', 0.15], ['s12b06+1.5', 0.25],
    ['s12b07+0.4', 0.35], ['s12b08', 0.3], ['s12b09+1.6', 0.2], ['s12b10', 0.05]]);
  const lean = S.k(t, [['s12b05+0.6', 0], ['s12b05+0.95', 0.06, 'out'], ['s12b05+1.25', 0.06], ['s12b05+1.6', -0.02, 'sine'], ['s12b05+2.0', 0],
    ['s12b07+0.9', 0], ['s12b07+1.0', 0.04], ['s12b07+1.3', 0.02], ['s12b08', 0.05], ['s12b08.end', 0.05], ['s12b09+0.8', 0]]);
  const crouch = clamp(S.k(t, [['s12b09+1.35', 0], ['s12b09+2.45', 1, 'inOut']]) + 0.22 * stampHit - 0.08 * hitch);
  const tremble = S.k(t, [['scene.start', 0], ['scene.start+0.6', 0.45], ['s12b05', 0.45], ['s12b05+0.3', 0.2], ['s12b05+2.3', 0.25], ['s12b05+2.9', 0.55],
    ['s12b06+0.3', 0.6], ['s12b07', 0.4], ['s12b08', 0.5], ['s12b09+0.5', 0.7], ['s12b09+2.6', 0.6], ['s12b10+0.5', 0.35], ['s12b11', 0.25]]);
  // breath: held in b05 (barely moving), then the shaky leak; small uneven breaths at the end
  const breathe = S.k(t, [['scene.start', 0.12], ['scene.start+0.6', 1], ['s12b05+0.2', 1], ['s12b05+0.45', 0.08], ['s12b05+1.8', 0.08], ['s12b05+2.1', 1.7], ['s12b06+0.3', 1.3],
    ['s12b10', 1.4], ['s12b11', 1.1]]) * (1 + 0.35 * live * Math.sin(t * 2.9));
  const breathRate = S.k(t, [['scene.start', 0.2], ['scene.start+0.6', 0.42], ['s12b05+1.9', 0.42], ['s12b05+2.1', 0.75], ['s12b06+0.5', 0.5], ['s12b10', 0.42], ['s12b11', 0.34]]);

  // ---------------- arms
  const P = (a, b, k) => lerp2(a, b, clamp(k));
  const chest = (s) => [s * 10, -134], wring = (s) => [s * 5, -106], fists = (s) => [s * 41, -54],
    shoutFists = (s) => [s * 44, -58], fold = (s) => [s * 17, -110], hug = (s) => [-s * 14, -118];
  // knot through the beats
  const armK = (s) => {
    const keys = [
      ['scene.start-1', chest(s)], ['s12b05+0.3', chest(s)], ['s12b05+0.8', wring(s)], ['s12b06+0.3', wring(s)], ['s12b06+0.7', chest(s)],
      ['s12b07+0.35', s > 0 ? [24, -112] : chest(s)], ['s12b07+0.65', fists(s)], ['s12b08-0.1', fists(s)], ['s12b08+0.2', shoutFists(s)],
      ['s12b09+0.3', shoutFists(s)], ['s12b09+1.1', fold(s)], ['s12b09+1.5', fold(s)], ['s12b09+2.4', hug(s)],
    ];
    return S.k(t, keys.map(([a, v]) => [a, { x: v[0], y: v[1] }]));
  };
  let L = armK(-1), R = armK(1);
  let armL = { target: [L.x, L.y], bend: -1, front: true, hand: 'open' };   // = s11's last frame (chest, elbows out)
  let armR = { target: [R.x, R.y], bend: 1, front: true, hand: 'open' };
  const fistOn = (t > T('s12b01+0.55') && t < T('s12b05+0.3')) || (t > T('s12b07+0.4') && t < T('s12b09+0.6'));
  if (fistOn) { armL.hand = 'fist'; armR.hand = 'fist'; }
  if (t > T('s12b05+0.5') && t < T('s12b06+0.5')) { armL.hand = 'fist'; armR.hand = 'fist'; }
  // fists hanging at the sides: the elbows bend in like the rest pose (the arms are nearly straight when it flips)
  if (t > T('s12b07+0.5') && t < T('s12b09+0.3')) { armL.bend = 1; armR.bend = -1; }
  // the stamp: the fists jab down with the foot
  if (stampHit > 0) { armL.target = [armL.target[0], armL.target[1] + 7 * stampHit]; armR.target = [armR.target[0], armR.target[1] + 7 * stampHit]; }

  // b06/b07: the right hand finds the gate's free edge, holds it, pushes it wide, lets go
  let grips;
  const door = S.k(t, [['s12b07+0.02', 0.3], ['s12b07+0.62', 0.9, 'outCubic']]);
  const reachK = S.k(t, [['s12b06+0.85', 0], ['s12b06+1.4', 1, 'inOut'], ['s12b07+0.22', 1], ['s12b07+0.45', 0, 'sine']]);
  if (reachK > 0) {
    const h = cagePoint('doorHandle', ...CAGE_B, { door, locked: 0 });
    const loc = [(h[0] - pos[0]) / scale, (h[1] - pos[1]) / scale];
    armR = { target: P(armR.target, loc, reachK), bend: -1, front: true, hand: reachK > 0.85 ? 'grip' : 'open' };
    if (reachK > 0.85 && t < T('s12b07+0.3')) grips = [[(h[0] - CAGE_B[0]) / FS, (h[1] - CAGE_B[1]) / FS]];
  }
  // b10: wipes its nose on the scarf (right hand), then folds back into the hug
  const wipe = S.k(t, [['s12b10+0.05', 0], ['s12b10+0.35', 1, 'out'], ['s12b10+0.95', 1], ['s12b10+1.3', 0, 'sine']]);
  if (wipe > 0) {
    const sweep = Math.sin((t - T('s12b10+0.35')) * 2 * Math.PI * 1.7) * clamp((t - T('s12b10+0.35')) / 0.1);
    armR = { target: P(armR.target, [6 + 12 * sweep, -158], wipe), bend: -1, front: true, hand: 'fist' };
  }

  return { pos, scale, walk, face: spoken, headDY, headTilt, headTurn, lean, crouch, tremble, breathe, breathRate, armL, armR, grips, door };
}

// ---------------------------------------------------------------- render
export function render(g, t, S) {
  const { cam, cage } = shot(t, S);
  const F = fearState(t, S);
  const cst = { t, door: F.door, locked: 0, shake: 0.12 * bump(t, S.T('s12b07+0.62'), 0.2) };
  const vpose = { t, ...STARE_B, idle: 0, shadowSpread: 1, handL: { ...VOID_ARM_B, show: 0, defer: 'hand' } };
  const st = { t, lightsDim: 0.35, mist: 0.6 };
  const inside = F.pos[1] <= DOORWAY_Y;
  const fearPose = { t, facing: 1, headTurn: F.headTurn, headTilt: F.headTilt, headDY: F.headDY, lean: F.lean, crouch: F.crouch,
    tremble: F.tremble, breathe: F.breathe, breathRate: F.breathRate, face: F.face, armL: F.armL, armR: F.armR,
    walk: F.walk ? { phase: F.walk } : undefined };

  g.save();
  applyCamera(g, cam);
  drawHQ(g, 'backOfMind', st);
  drawVoid(g, ...VOID_B, vpose);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  if (inside) drawFear(g, F.pos[0], F.pos[1], F.scale, fearPose);
  if (cage === 'full') drawCage(g, ...CAGE_B, { ...cst, layer: 'front', grips: F.grips });
  if (!inside) drawFear(g, F.pos[0], F.pos[1], F.scale, fearPose);
  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  finish(g, 0.6, 0, 0.5);
}
