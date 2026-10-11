// s14 · the_universe_inside · VOID_FACE / backOfMind
// The revelation: Fear's POV pushes into the dark hood, the cosmos kindles, a long drift through the stars,
// then the change happens on Fear's face (close), the pull-back two-shot, "Why are you showing me this?",
// the hand lifts away, the hood turns back to the distance, and Fear turns to look where the Void looks.

import { createCanvas } from '@napi-rs/canvas';
import { W, H, clamp, lerp, ease, smoothstep, blinkAt, applyCamera, drift, vignette, fbm } from '../engine.mjs';
import { withSpeech } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawVoid, drawVoidGlow, drawVoidArm, drawVoidHand, toVoidLocal, voidRig, VOID_HANDS } from '../chars/void.mjs';
import { drawCosmos, vfbm } from '../fx/cosmos.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';

export const id = 's14';

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const LOOK_FEAR = { headTurn: -0.3, headDown: 0.8 };
const COSMOS_OPTS = { seed: 7, glyphs: 1 };
const CAGE_B = [430, 1630, 0.952];
const THRESH = [440, 1648, 0.97];
const VOID_ARM_B = { bend: 1 };
const APPROACH_SHOULDER = [120, -40];
const SLEEVE_CLIP_Y = 1100;

// ---------------------------------------------------------------- sound
export const sfx = [
  { at: 's14b01+0.35', name: 'shimmer', gain: -17 },            // the hush before the first light
  { at: 's14b01+0.78', name: 'twinkle', gain: -18 },            // the single first star (note at 0.02)
  { at: 's14b01+2.2', name: 'twinkle', gain: -21 },             // "then hundreds"
  { at: 's14b02+4.08', name: 'twinkle', gain: -19 },            // '...of lights'
  { at: 's14b03+2.58', name: 'twinkle', gain: -21 },            // '...and stars'
  { at: 's14b04+1.75', name: 'shimmer', gain: -15 },            // glyphs bloom, swell peaks near 'meaning'
  { at: 's14b06+5.06', name: 'twinkle', gain: -21 },            // 'wonder' (the little smile)
  { at: 's14b09+0.02', name: 'cloth_rustle', gain: -17 },       // the hand lifts off the shoulder
  { at: 's14b09+1.45', name: 'cloth_rustle', gain: -21, rate: 0.85 }, // the hood turns back to the distance
  { at: 's14b10+1.42', name: 'footsteps', gain: -19, until: 's14b10+1.9', fade: 0.15 }, // Fear's small turning step
];

// ---------------------------------------------------------------- helpers
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
const sleeveFront = (g, pose) => {
  g.save(); g.beginPath(); g.rect(-1e4, SLEEVE_CLIP_Y, 2e4, 2e4); g.clip();
  drawVoidArm(g, ...VOID_B, pose, 'L', 'sleeve'); g.restore();
};
const rotAbout = (p, o, a) => {
  const c = Math.cos(a), s = Math.sin(a), dx = p[0] - o[0], dy = p[1] - o[1];
  return [o[0] + dx * c - dy * s, o[1] + dx * s + dy * c];
};
// living camera: drift in SCREEN px whatever the zoom
function cam(x, y, zoom, t, amp = 2.5) {
  if (!amp) return { x, y, zoom };
  const d = drift(t, amp, 14);
  return { x: x + d.dx / zoom, y: y + d.dy / zoom, zoom, rot: d.dr * 0.5 };
}
const zoomExp = (z0, z1, k) => z0 * Math.pow(z1 / z0, k);

let off = null;   // offscreen for the hood → full-screen cosmos crossfade
function offscreen() {
  if (!off) off = createCanvas(W, H);
  const o = off.getContext('2d');
  o.setTransform(1, 0, 0, 1, 0, 0); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over';
  o.clearRect(0, 0, W, H);
  return o;
}

// ---------------------------------------------------------------- tracks
function cosmosAt(t, S) {
  return S.k(t, [
    // the single first star kindles WITH its twinkle (sfx b01+0.78, first note +0.02): reveal crosses the
    // module's first-star threshold (0.015) at ≈ +0.66 and is half-lit by +0.8 (was already visible at +0.45)
    ['scene.start', 0], ['s14b01+0.6', 0], ['s14b01+0.95', 0.055, 'out'],
    ['s14b01+1.5', 0.07], ['s14b01.end', 0.3, 'in'],                      // another… then hundreds
    ['s14b02.end', 0.62], ['s14b03.end', 0.85], ['s14b04+1.5', 1.0],
    ['s14b09', 1.0], ['s14b10+2.0', 0.6],
  ]);
}

/** The Void's pose for this instant (hand on Fear's shoulder until b09, then lifted away). */
function voidPose(t, S, cosmos, fear) {
  const head = S.k(t, [['s14b09+1.4', LOOK_FEAR], ['s14b09+3.4', STARE_B]]);
  // withdrawal = s13's approach in reverse: the fingertips slide off the shoulder (settle), the hand rises
  // beside the cage's right bars to s13's waypoint (ascend) while it slips back into the sleeve (show), and
  // only then the empty sleeve swings back to rest (reach) — the hand never passes over the TIME-OUT sign.
  const settle = S.k(t, [['s14b09', 1], ['s14b09+0.6', 0, 'inOut']]);
  const ascend = S.k(t, [['s14b09+0.5', 0], ['s14b09+1.6', 1, 'inOut']]);
  const show = S.k(t, [['s14b09+1.25', 1], ['s14b09+2.0', 0, 'inOut']]);
  const reach = S.k(t, [['s14b09+1.9', 1], ['s14b09+2.9', 0, 'inOut']]);
  const [fx, fy, fs] = THRESH;
  // Fear's near (right) shoulder, following crouch and lean (staging §1.5)
  let sh = [fx + 36 * fs, fy - (130 - 20 * fear.crouch) * fs];
  sh = rotAbout(sh, [fx, fy], fear.leanScreen);
  const ap = [sh[0] + APPROACH_SHOULDER[0] * fs, sh[1] + APPROACH_SHOULDER[1] * fs];
  const WP1 = [ap[0] + 15, ap[1] - 235];                 // = s13's waypoint beside the cage's right bars
  const tA = [lerp(ap[0], WP1[0], ascend), lerp(ap[1], WP1[1], ascend)];
  const tgt = [lerp(tA[0], sh[0], settle), lerp(tA[1], sh[1], settle)];
  const angle = lerp(Math.PI - 0.38, Math.PI / 2 + 0.3, ease.sine(clamp(ascend * 1.15)));
  return {
    t, ...head, idle: 0.5, cosmos, cosmosOpts: COSMOS_OPTS, glow: 1.2,
    shadowSpread: S.k(t, [['s14b04', 1], ['s14b06', 0.8]]),
    handL: { ...VOID_HANDS.shoulder(toVoidLocal(...VOID_B, ...tgt), -1), ...VOID_ARM_B, angle, elbow: 0.8 * reach, show, reach, defer: 'hand' },
  };
}

/** Fear on the threshold: body + face for this instant. */
function fearState(t, S) {
  const K = (keys, e) => S.k(t, keys, e);

  // ---------- body
  const crouch = K([
    ['s14b05', 0.3],
    ['s14b10+0.3', 0.3], ['s14b10+1.25', 0, 'inOut'],                      // stands up
  ]);
  const leanScreen = K([['s14b09+0.3', 0], ['s14b09+1.0', 0.09, 'outCubic'], ['s14b09+2.3', 0, 'inOut']]); // leans after the hand
  const facing = t < S.T('s14b10+1.52') ? 1 : -1;
  const headTurn = K([
    ['s14b05', 0.25],
    ['s14b09+0.25', 0.25], ['s14b09+0.7', 0.42],                            // glance at its own shoulder
    ['s14b09+1.5', 0.25],
    ['s14b10+1.1', 0.25], ['s14b10+1.95', -0.22, 'inOut'],                 // turns to the glow
  ]);
  const tiltScreen = K([
    ['s14b05', -0.15],
    ['s14b06+2.6', -0.15], ['s14b06+3.3', -0.12],
    ['s14b08', -0.14], ['s14b08.end', -0.23],                               // tilts a few degrees as it asks
    ['s14b09+0.25', -0.2], ['s14b09+0.8', 0.07],                            // dips toward the shoulder
    ['s14b09+1.6', -0.13],
    ['s14b10+1.1', -0.14], ['s14b10+2.0', -0.06, 'inOut'],
  ]) + fbm(t * 0.35, 21) * 0.015;
  const headDY = K([
    ['s14b06+2.75', 0], ['s14b06+2.95', -3], ['s14b06+3.2', -0.5], ['s14b06+3.4', -2.5], ['s14b06+3.7', 0], // breath of a laugh
    ['s14b07+0.85', 0], ['s14b07+1.0', 3.2], ['s14b07+1.2', 0],             // swallow
    ['s14b07+1.2', 0], ['s14b07+1.5', -1.8], ['s14b07+1.9', 0],             // small breath
    ['s14b10+1.45', 0], ['s14b10+1.55', 2.5], ['s14b10+1.75', 0],          // weight shift on the turn
  ]);

  // arms: (first seen at b05, 17 s after s13's last view of Fear) the left arm hugs the belly, the right hand
  // holds the scarf; they relax; on 'wonder' the left hand lifts a little, outward and open, without meaning
  // to, then drifts down; at the end the hands clasp at the scarf (= s15). The left arm keeps bend +1 (elbow
  // down) until the body turns round (facing flips at b10+1.52, which masks the switch to s15's bend −1).
  const L2 = (p, q, k) => [lerp(p[0], q[0], k), lerp(p[1], q[1], k)];
  const relax = K([['s14b05', 0], ['s14b05+3.8', 1]]);
  const lift = K([['s14b06+5.3', 0], ['s14b06+6.2', 1, 'inOut'], ['s14b06+6.9', 1], ['s14b06.end+0.4', 0, 'inOut']]);
  const clasp = K([['s14b10+3.2', 0], ['s14b10+4.0', 1, 'inOut']]);
  let armL, armR;
  if (facing > 0) {
    let tL = L2([-20, -106], [-24, -100], relax);
    // the lift opens OUT and a little up (fingers angled up and away), not up beside the head: with the hand
    // raised to shoulder height and the fingers vertical (the old [-58,-126]) it read as a wave hello
    const drift = K([['s14b06+6.2', 0], ['s14b06+6.9', 1]]);
    if (lift > 0) tL = L2(tL, [-78, -111 - 6 * drift], lift);
    armL = { target: tL, bend: 1, front: true, hand: lift > 0.3 ? 'open' : undefined };
    armR = { target: L2([14, -118], [19, -103], relax), bend: 1, front: true, hand: 'open' };
  } else {
    armL = { target: L2([-15, -108], [-7, -127], clasp), bend: -1, front: true, hand: clasp > 0.5 ? 'fist' : undefined };
    armR = { target: L2([19, -103], [7, -124], clasp), bend: 1, front: true, hand: clasp > 0.5 ? 'fist' : 'open' };
  }

  // ---------- face channels
  const brows = K([
    ['s14b05', { browUp: 0.12, browIn: 0.85, browSquish: 0.45, browUpL: 0, browUpR: 0 }],
    ['s14b05+0.4', { browUp: 0.12, browIn: 0.85, browSquish: 0.45, browUpL: 0, browUpR: 0 }],
    ['s14b05+1.9', { browUp: 0.48, browIn: 0.38, browSquish: 0.0, browUpL: 0, browUpR: 0 }],   // un-knot, open
    ['s14b06+2.6', { browUp: 0.52, browIn: 0.32, browSquish: 0, browUpL: 0, browUpR: 0 }],
    ['s14b06+3.1', { browUp: 0.6, browIn: 0.2, browSquish: 0, browUpL: 0, browUpR: 0 }],        // lift and soften
    ['s14b07+0.1', { browUp: 0.6, browIn: 0.22, browSquish: 0, browUpL: 0, browUpR: 0 }],
    ['s14b07+0.5', { browUp: 0.66, browIn: 0.42, browSquish: 0, browUpL: 0, browUpR: 0 }],      // trying to speak
    ['s14b08+0.1', { browUp: 0.55, browIn: 0.48, browSquish: 0, browUpL: 0, browUpR: 0 }],      // gently raised, asking
    ['s14b08.end', { browUp: 0.6, browIn: 0.5, browSquish: 0, browUpL: 0, browUpR: 0 }],
    ['s14b09+0.25', { browUp: 0.6, browIn: 0.5, browSquish: 0, browUpL: 0, browUpR: 0 }],
    ['s14b09+0.7', { browUp: 0.22, browIn: 0.72, browSquish: 0.15, browUpL: 0, browUpR: 0 }],   // dip: missing the hand
    ['s14b09+1.6', { browUp: 0.3, browIn: 0.6, browSquish: 0.1, browUpL: 0.18, browUpR: -0.05 }], // puzzled, watching the hood turn
    ['s14b10+1.8', { browUp: 0.32, browIn: 0.55, browSquish: 0.1, browUpL: 0.15, browUpR: 0 }],
    ['s14b10+2.35', { browUp: -0.22, browIn: 0.05, browSquish: 0.55, browUpL: 0, browUpR: 0 }], // narrow to see (peering)
    ['s14b10+3.0', { browUp: -0.22, browIn: 0.05, browSquish: 0.55, browUpL: 0, browUpR: 0 }],
    ['s14b10+3.45', { browUp: 0.7, browIn: 0.45, browSquish: 0, browUpL: 0, browUpR: 0 }],      // widen
  ]);
  const lids = K([
    ['s14b05', { lidU: 0.1, lidL: 0.14, lidTilt: 0.34 }],
    ['s14b05+1.2', { lidU: 0.12, lidL: 0.14, lidTilt: 0.3 }],
    ['s14b05+2.7', { lidU: -0.12, lidL: 0.05, lidTilt: 0.08 }],      // heavy lids rise, softly
    ['s14b06+2.8', { lidU: -0.12, lidL: 0.05, lidTilt: 0.08 }],
    ['s14b06+3.2', { lidU: -0.05, lidL: 0.18, lidTilt: 0.05 }],      // the breath of a laugh lifts the cheeks
    ['s14b06+5.15', { lidU: -0.05, lidL: 0.2, lidTilt: 0.05 }],
    ['s14b06+5.75', { lidU: 0.0, lidL: 0.32, lidTilt: 0.06 }],        // smiling eyes on 'wonder'
    ['s14b06.end', { lidU: -0.04, lidL: 0.22, lidTilt: 0.06 }],
    ['s14b08', { lidU: -0.08, lidL: 0.12, lidTilt: 0.12 }],
    ['s14b09+0.3', { lidU: -0.08, lidL: 0.12, lidTilt: 0.12 }],
    ['s14b09+0.7', { lidU: 0.22, lidL: 0.1, lidTilt: 0.25 }],         // eyes drop to the shoulder
    ['s14b09+1.5', { lidU: -0.02, lidL: 0.05, lidTilt: 0.15 }],
    ['s14b10+1.85', { lidU: -0.02, lidL: 0.05, lidTilt: 0.12 }],
    ['s14b10+2.35', { lidU: 0.15, lidL: 0.5, lidTilt: -0.12 }],      // narrow: lower lids rise, peering
    ['s14b10+3.0', { lidU: 0.15, lidL: 0.5, lidTilt: -0.12 }],
    ['s14b10+3.45', { lidU: -0.2, lidL: 0.0, lidTilt: 0.1 }],         // widen
  ]);
  const mouth = K([
    ['s14b05', { open: 0.07, smile: -0.32, round: 0, wide: 0.05, pressed: 0, tremble: 0 }],
    ['s14b05+1.5', { open: 0.07, smile: -0.3, round: 0, wide: 0.05, pressed: 0, tremble: 0 }],
    ['s14b05+2.8', { open: 0.27, smile: -0.06, round: 0.34, wide: -0.05, pressed: 0, tremble: 0.1 }],  // falls open
    // lower lip quivers: the rig's lip tremble is ~0.07·mouthW·tremble, i.e. 1.4 screen px at 0.32 in this
    // close (invisible on a phone); 0.62 gives a readable ~2.7 px quiver while the mouth stays soft and open
    ['s14b05+3.6', { open: 0.25, smile: -0.08, round: 0.32, wide: -0.05, pressed: 0, tremble: 0.62 }],
    ['s14b06+1.6', { open: 0.22, smile: -0.06, round: 0.3, wide: -0.05, pressed: 0, tremble: 0.55 }],
    ['s14b06+2.75', { open: 0.2, smile: -0.04, round: 0.28, wide: -0.05, pressed: 0, tremble: 0.3 }],
    ['s14b06+2.95', { open: 0.32, smile: 0.12, round: 0.12, wide: 0.1, pressed: 0, tremble: 0.1 }],    // a breath of a laugh
    ['s14b06+3.25', { open: 0.16, smile: 0.04, round: 0.2, wide: 0, pressed: 0, tremble: 0.15 }],
    ['s14b06+3.45', { open: 0.25, smile: 0.1, round: 0.1, wide: 0.08, pressed: 0, tremble: 0.1 }],
    ['s14b06+3.9', { open: 0.17, smile: 0.0, round: 0.22, wide: 0, pressed: 0, tremble: 0.15 }],
    ['s14b06+5.15', { open: 0.17, smile: 0.0, round: 0.22, wide: 0, pressed: 0, tremble: 0.12 }],
    ['s14b06+5.7', { open: 0.13, smile: 0.56, round: 0.0, wide: 0.14, pressed: 0, tremble: 0.06 }],    // small disbelieving smile on 'wonder' (+5.08)
    ['s14b06+6.6', { open: 0.1, smile: 0.42, round: 0.0, wide: 0.1, pressed: 0, tremble: 0.05 }],      // 'amazement': smaller
    ['s14b06.end', { open: 0.12, smile: 0.25, round: 0.05, wide: 0.05, pressed: 0, tremble: 0.05 }],
    // b07: lips move, nothing comes out; it swallows; one small breath
    ['s14b07+0.1', { open: 0.12, smile: 0.2, round: 0.05, wide: 0.05, pressed: 0, tremble: 0.05 }],
    ['s14b07+0.3', { open: 0.24, smile: 0.06, round: 0.3, wide: 0, pressed: 0, tremble: 0.1 }],
    ['s14b07+0.48', { open: 0.05, smile: 0.04, round: 0.1, wide: 0, pressed: 0, tremble: 0.05 }],
    ['s14b07+0.62', { open: 0.18, smile: 0.02, round: 0.35, wide: 0, pressed: 0, tremble: 0.1 }],
    ['s14b07+0.85', { open: 0.0, smile: 0.0, round: 0.0, wide: 0, pressed: 0.25, tremble: 0 }],
    ['s14b07+1.05', { open: 0.0, smile: -0.02, round: 0.0, wide: -0.1, pressed: 0.65, tremble: 0 }],   // swallow
    ['s14b07+1.25', { open: 0.04, smile: 0.0, round: 0.1, wide: 0, pressed: 0.1, tremble: 0 }],
    ['s14b07+1.5', { open: 0.12, smile: 0.0, round: 0.25, wide: 0, pressed: 0, tremble: 0 }],          // small breath in
    ['s14b08', { open: 0.06, smile: 0.06, round: 0.1, wide: 0, pressed: 0, tremble: 0.12 }],
    ['s14b08.end', { open: 0.06, smile: 0.04, round: 0.1, wide: 0, pressed: 0, tremble: 0.12 }],
    ['s14b08.end+0.4', { open: 0.1, smile: 0.0, round: 0.15, wide: 0, pressed: 0, tremble: 0.1 }],     // lips parted, waiting
    ['s14b09+0.3', { open: 0.1, smile: 0.0, round: 0.15, wide: 0, pressed: 0, tremble: 0.1 }],
    ['s14b09+0.8', { open: 0.03, smile: -0.18, round: 0.0, wide: -0.08, pressed: 0.2, tremble: 0.05 }], // missing it
    ['s14b09+1.8', { open: 0.07, smile: -0.12, round: 0.1, wide: 0, pressed: 0, tremble: 0 }],
    ['s14b10+1.9', { open: 0.06, smile: -0.08, round: 0.1, wide: 0, pressed: 0, tremble: 0 }],
    ['s14b10+2.35', { open: 0.0, smile: -0.05, round: 0.0, wide: -0.05, pressed: 0.3, tremble: 0 }],   // squinting
    ['s14b10+3.0', { open: 0.0, smile: -0.05, round: 0.0, wide: -0.05, pressed: 0.3, tremble: 0 }],
    ['s14b10+3.45', { open: 0.2, smile: 0.0, round: 0.4, wide: -0.05, pressed: 0, tremble: 0.1 }],     // widen: a soft "oh"
  ]);
  const eyes = K([
    ['s14b05', { pupil: 0.82, sparkle: 0.85 }],
    ['s14b05+0.5', { pupil: 0.82, sparkle: 0.9 }],
    ['s14b05+2.6', { pupil: 1.32, sparkle: 1 }],
    ['s14b09+1.0', { pupil: 1.28, sparkle: 1 }],
    ['s14b10+1.5', { pupil: 1.15, sparkle: 0.85 }],
    ['s14b10+2.35', { pupil: 0.95, sparkle: 0.45 }],
    ['s14b10+3.45', { pupil: 1.3, sparkle: 0.6 }],
  ]);
  // gaze (with micro-saccades that "search the stars")
  const gaze = K([
    ['s14b05', { lookX: 0.35, lookY: -1 }],
    ['s14b08+0.5', { lookX: 0.35, lookY: -1 }], ['s14b08+0.58', { lookX: 0.5, lookY: -0.92 }],
    ['s14b08+1.32', { lookX: 0.5, lookY: -0.92 }], ['s14b08+1.4', { lookX: 0.26, lookY: -1 }],
    ['s14b08.end+0.6', { lookX: 0.26, lookY: -1 }], ['s14b08.end+0.68', { lookX: 0.38, lookY: -0.98 }],
    ['s14b09+0.2', { lookX: 0.38, lookY: -0.98 }], ['s14b09+0.45', { lookX: 0.8, lookY: 0.4 }],      // glance at its own shoulder
    ['s14b09+1.0', { lookX: 0.8, lookY: 0.4 }], ['s14b09+1.3', { lookX: 0.62, lookY: -0.7 }],         // up the withdrawing arm
    ['s14b09+1.7', { lookX: 0.5, lookY: -0.9 }], ['s14b09+3.0', { lookX: 0.32, lookY: -1 }],          // to the hood as it turns
    ['s14b10+0.9', { lookX: 0.34, lookY: -1 }], ['s14b10+1.4', { lookX: -0.22, lookY: -0.82 }],       // eyes lead to the glow
    ['s14b10+1.9', { lookX: -0.2, lookY: -0.8 }],
  ]);
  const searching = S.talking('FEAR', t) * 0.05;
  const micro = (s) => fbm(t * 0.45, s) * (0.05 + searching);
  // tears of wonder
  const tears = K([['s14b05', 0.38], ['s14b05+0.6', 0.4], ['s14b05+2.4', 0.92], ['s14b09', 0.9], ['s14b10+3.0', 0.82], ['s14b10+3.6', 0.95]]);
  // both drops run down the screen-LEFT cheek: the right cheek is under the Void's fingers in the close (a
  // right-hand drop was hidden for ~80 % of its run). One spills (b05+2.45), then a second (b05+4.25); the
  // track restarts only after the first drop has faded out (alpha 0 from progress 1), so nothing pops.
  const drop = (a, b) => clamp((t - S.T(a)) / (S.T(b) - S.T(a)), 0, 1);
  const d1 = drop('s14b05+2.45', 's14b05+4.15'), d2 = drop('s14b05+4.25', 's14b05+5.95');
  const tearL = t < S.T('s14b05+4.2') ? d1 : d2;
  const tearR = 0;
  const stream = K([['s14b05+2.7', 0], ['s14b05+4.6', 0.32], ['s14b09', 0.3], ['s14b10.end', 0.24]]);
  const blush = K([['s14b06+4.9', 0], ['s14b06+6.3', 0.6], ['s14b08.end', 0.45], ['s14b10', 0.3]]);
  const blink = Math.max(
    blinkAt(t, S.T('s14b05+1.0'), 0.5),       // the realisation: a slow blink, then the lids rise
    blinkAt(t, S.T('s14b06+1.15'), 0.36),
    blinkAt(t, S.T('s14b06+3.55'), 0.18),
    blinkAt(t, S.T('s14b06+7.3'), 0.42),      // after 'amazement' (the word ends at +7.22)
    blinkAt(t, S.T('s14b07+0.92'), 0.2),      // with the swallow
    blinkAt(t, S.T('s14b08.end+0.2'), 0.42),  // waiting for an answer
    blinkAt(t, S.T('s14b09+1.08'), 0.18),     // gaze shift up the arm
    blinkAt(t, S.T('s14b10+1.42'), 0.22),     // the eyes have led to the glow; blink as the head and body come
                                              // round: lids shut across the facing flip at b10+1.52 (masks it)
    blinkAt(t, S.T('s14b10+3.02'), 0.17),     // "did I see that right?"
  );

  let face = {
    ...brows, ...lids, ...mouth, ...eyes,
    lookX: gaze.lookX + micro(31), lookY: gaze.lookY + micro(37) * 0.6,
    tears, tearL, tearR, stream, blush, blink, noAutoBlink: true,
  };
  face = withSpeech(face, S.lip('FEAR', t), 0.72);   // a whisper, barely above a breath

  return {
    crouch, leanScreen, facing,
    pose: {
      t, facing, crouch, tremble: 0, lean: leanScreen * facing, headTilt: tiltScreen * facing, headTurn, headDY,
      breathe: 0.9, armL, armR, face,
    },
  };
}

// ---------------------------------------------------------------- the back-of-the-mind stage
// PERFORMANCE: in the static closes and the pull-back everything behind Fear (set, Void, cage, the sleeve in
// front of the cage) is still, so it is rendered once into a world-space "plate" (cached, keyed by shot/zoom
// bucket, built at a FIXED time so any frame renders identically in any order) and blitted under the live
// camera; Fear, the glow, the starlight, the hand and the low mist stay live. The glow is rendered at 1/4 res.
const plates = new Map();
function getPlate(key, rect, res, build) {
  let p = plates.get(key);
  if (p) return p;
  if (plates.size >= 5) plates.delete(plates.keys().next().value);
  const ww = rect[2] - rect[0], wh = rect[3] - rect[1];
  const c = createCanvas(Math.ceil(ww * res), Math.ceil(wh * res));
  const pg = c.getContext('2d');
  pg.scale(c.width / ww, c.height / wh);
  pg.translate(-rect[0], -rect[1]);
  build(pg);
  p = { c, rect };
  plates.set(key, p);
  return p;
}
/** world rect seen by a camera at (x, y, zoom), grown by `m` screen px for drift */
const frameRect = (x, y, z, m = 8) => [x - (360 + m) / z, y - (640 + m) / z, x + (360 + m) / z, y + (640 + m) / z];
const unionRect = (a, b) => [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])];

let glowC = null;
function glowLowRes(g, camera, vp) {
  if (!(vp.cosmos > 0.005)) return;
  if (!glowC) glowC = createCanvas(W / 4, H / 4);
  const o = glowC.getContext('2d');
  o.setTransform(1, 0, 0, 1, 0, 0);
  o.globalCompositeOperation = 'source-over'; o.globalAlpha = 1;
  o.clearRect(0, 0, W / 4, H / 4);
  o.scale(0.25, 0.25);
  applyCamera(o, camera);
  drawVoidGlow(o, ...VOID_B, vp);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'screen';
  g.drawImage(glowC, 0, 0, W, H); g.restore();
}

/**
 * opts: cosmos, starK, fear (false = no Fear/cage, hood POV),
 *       plate: { key, rect, res, tb }  (static background), tb: frozen time for the set + cage (pull-back)
 */
function drawStage(g, t, S, camera, opts = {}) {
  const cosmos = opts.cosmos;
  const fear = fearState(t, S);
  const vp = voidPose(t, S, cosmos, fear);
  const tb = opts.plate ? opts.plate.tb : opts.tb ?? t;
  const st = { t, lightsDim: 0.35, mist: 0.5, alarm: 0 };
  const handOut = vp.handL.show > 0.001 || vp.handL.reach > 0.001;
  const back = (c, tt, v) => {
    drawHQ(c, 'backOfMind', { ...st, t: tt });
    drawVoid(c, ...VOID_B, v);
    if (opts.fear === false) return;
    const cst = { t: tt, door: 0.9, locked: 0, rust: 0, dim: 0 };
    drawCage(c, ...CAGE_B, { ...cst, layer: 'back' });
    drawCage(c, ...CAGE_B, { ...cst, layer: 'front' });
    if (handOut) sleeveFront(c, v);
  };
  g.save();
  applyCamera(g, camera);
  if (opts.plate) {
    const P = opts.plate;
    // the plate's Void pose is evaluated AT the frozen instant (not "this frame's pose at tb"): shadowSpread
    // eases through b05, so a plate first built mid-shot used to differ from one built at the shot's start,
    // i.e. the picture depended on which frame a render process happened to reach first (chunked renders)
    const pl = getPlate(P.key, P.rect, P.res, (pg) => back(pg, P.tb, voidPose(P.tb, S, cosmosAt(P.tb, S), fearState(P.tb, S))));
    g.drawImage(pl.c, pl.rect[0], pl.rect[1], pl.rect[2] - pl.rect[0], pl.rect[3] - pl.rect[1]);
  } else {
    back(g, tb, vp);
  }
  if (opts.fear !== false) {
    const [fx, fy, fs] = THRESH;
    drawFear(g, fx, fy, fs, fear.pose);
  }
  g.restore();
  if (opts.fear !== false) {
    glowLowRes(g, camera, vp);
    const [fx, fy, fs] = THRESH;
    g.save();
    applyCamera(g, camera);
    starlight(g, fx + 25 * fs, fy - 250 * fs, 190 * fs, opts.starK ?? cosmos);
    if (vp.handL.show > 0.001) drawVoidHand(g, ...VOID_B, vp, 'L');
    drawHQForeground(g, 'backOfMind', st);
    g.restore();
  } else {
    g.save(); applyCamera(g, camera); drawHQForeground(g, 'backOfMind', st); g.restore();
  }
}

// ---------------------------------------------------------------- shots
// close on Fear (b05, b07–b08). Staging gives {450,1430,3.0}; pushed to 3.3 and down to y 1500 so the face
// sits on the upper third and the TIME-OUT sign leaves the top of the frame (it fought the face for attention)
const CLOSE = [445, 1500, 3.3];
// the two-shot from the side (end of b06, b09). Staging gives {560,1000,0.85}, which crops the hood opening
// at the frame top; 0.8 a little higher keeps the whole starry hood bowed above Fear
const TWO = [560, 965, 0.8];
// over the Void's shoulder {360,1200,1.3} (b10)
// Staging gives {360,1200,1.3}; nudged left/wider so the floor's glowing paths run into the far glow across the
// open left of the frame and Fear (right of centre) looks into that space; the Void's sleeve/robe at the right
const OTS = [330, 1160, 1.2];

function hoodPOV(g, t, S, cosmos) {
  // Fear's POV pushing slowly into the bowed hood: {679,336,4.5} → {679,336,7.0}
  const k = S.k(t, [['scene.start', 0], ['s14b02+0.5', 1]]);
  const z = zoomExp(4.5, 7.0, k);
  drawStage(g, t, S, cam(679, 336, z, t, 1.5), { cosmos, fear: false });
}

function cosmosFull(g, t, S, cosmos) {
  // full-screen universe: a slow drift (≈0.3 px/frame) and a 1.00 → 1.06 scale over b02–b04
  const u = S.k(t, [['s14b02-0.5', 0], ['s14b05', 1]], 'linear');
  const sc = S.k(t, [['s14b02-0.5', 1], ['s14b04.end', 1.06]]);
  const cx = lerp(395, 325, u), cy = lerp(685, 595, u);
  g.fillStyle = '#020108';
  g.fillRect(0, 0, W, H);
  // the glyphs are b04's discovery ("bits and pieces of meaning"): they arrive with the line, full by 'meaning'
  const glyphs = S.k(t, [['s14b04-0.4', 0], ['s14b04+2.72', 1, 'inOut']]);
  const rx = 410 * sc, ry = 700 * sc;
  drawCosmos(g, cx, cy, rx, ry, t, { reveal: cosmos, seed: 7, glyphs });
  // on 'meaning' the heart (the cosmos module's glyph 0, near the centre) glows briefly brighter
  const pulse = S.k(t, [['s14b04+2.62', 0], ['s14b04+3.0', 1, 'out'], ['s14b04+4.6', 0, 'sine']]);
  if (pulse > 0.002) {
    const hx = cx + (-0.06 + vfbm(t * 0.045, 91) * 0.07 + Math.sin(t * 0.07) * 0.025) * rx;
    const hy = cy + (0.2 + vfbm(t * 0.04, 92) * 0.06 + Math.cos(t * 0.06) * 0.02) * ry;
    const r = 120;
    g.save(); g.globalCompositeOperation = 'screen';
    const gr = g.createRadialGradient(hx, hy, 0, hx, hy, r);
    gr.addColorStop(0, `rgba(255,170,215,${0.42 * pulse})`); gr.addColorStop(0.35, `rgba(255,140,200,${0.16 * pulse})`);
    gr.addColorStop(1, 'rgba(255,140,200,0)');
    g.fillStyle = gr; g.fillRect(hx - r, hy - r, 2 * r, 2 * r); g.restore();
  }
}

// b06 is one slow pull-back told in two pieces. A single continuous move CLOSE (3.47) → TWO (0.8) inside b06
// cannot be slow AND keep the smile on 'wonder' readable: the smile needs zoom ≳ 2.3 at b06+5.7, which leaves
// < 3 s for the remaining 2.9× (the first version peaked at 1.85×/s and landed on the two-shot on the very
// frame of the cut, so the composition never held). Now: (a) the close breathes out slowly to a medium,
// anchored on Fear's face (ease-in, ≤ 1.26×/s, zoom ≈ 2.6 at the smile), and (b) on 'amazement' it cuts on the
// motion to the two-shot from the side, which keeps pulling back very gently (0.86 → 0.80, easing out) for
// 1.7 s: tiny Fear under the starry hood bowed above it, held before b07's close.
const FACE_P = [440, 1454];
const CLOSE_PUSH = 1.05, Z_A = CLOSE[2] * CLOSE_PUSH;     // the close's zoom when the pull-back starts
const Z_M = 2.3;                                           // the medium the close breathes out to
const S0 = [360 + (FACE_P[0] - CLOSE[0]) * Z_A, 640 + (FACE_P[1] - CLOSE[1]) * Z_A];
const S_M = [352, 522];                                    // Fear's face on screen at the medium
function pullCam(k) {
  const zoom = zoomExp(Z_A, Z_M, k);
  const sx = lerp(S0[0], S_M[0], k), sy = lerp(S0[1], S_M[1], k);
  return { x: FACE_P[0] - (sx - 360) / zoom, y: FACE_P[1] - (sy - 640) / zoom, zoom };
}
const pullCamAtZoom = (z) => pullCam(clamp(Math.log(z / Z_A) / Math.log(Z_M / Z_A)));
const TWO_B06 = [552, 985, 0.86];                          // the two-shot as b06 cuts to it (→ TWO by b07)

// "a soft shimmer passes through them" (b06, VOID): a faint band of light crossing the stars in the hood
// opening, clipped inside the opening so the hood shell itself stays unlit (staging §5.4)
const HOOD_LF = (() => { const r = voidRig({ ...LOOK_FEAR }); return { x: VOID_B[0] + r.face[0] * VOID_B[2],
  y: VOID_B[1] + r.face[1] * VOID_B[2], rx: r.faceRx * VOID_B[2], ry: r.faceRy * VOID_B[2] }; })();
function hoodShimmer(g, camera, k) {
  if (k <= 0 || k >= 1) return;
  const { x, y, rx, ry } = HOOD_LF;
  const a = Math.sin(Math.PI * k);                         // fades in and out as it passes
  const p = lerp(-1.4, 1.4, k);                            // band centre along the diagonal (opening radii)
  g.save(); applyCamera(g, camera);
  g.beginPath(); g.ellipse(x, y + ry * 0.08, rx * 0.8, ry * 0.82, 0, 0, Math.PI * 2); g.clip();
  g.globalCompositeOperation = 'screen';
  const ux = 0.6, uy = 0.8, cx = x + ux * p * rx, cy = y + uy * p * ry, w = rx * 0.9;
  const gr = g.createLinearGradient(cx - ux * w, cy - uy * w, cx + ux * w, cy + uy * w);
  gr.addColorStop(0, 'rgba(190,170,255,0)'); gr.addColorStop(0.5, `rgba(210,195,255,${0.42 * a})`);
  gr.addColorStop(1, 'rgba(150,220,255,0)');
  g.fillStyle = gr; g.fillRect(x - rx * 2, y - ry * 2, rx * 4, ry * 4);
  g.restore();
}

export function render(g, t, S) {
  const cosmos = cosmosAt(t, S);
  const T = (a) => S.T(a);
  const cold = S.k(t, [['s14b01', 0.65], ['s14b02.end', 0.3]]);
  const vig = S.k(t, [['s14b01', 0.55], ['s14b02.end', 0.4]]);

  if (t < T('s14b02+0.5')) {
    // 1. the hood POV; crossfade (1.0 s) into the full-screen cosmos
    hoodPOV(g, t, S, cosmos);
    const x = smoothstep(T('s14b02-0.5'), T('s14b02+0.5'), t);
    if (x > 0) {
      const o = offscreen();
      cosmosFull(o, t, S, cosmos);
      g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = x; g.drawImage(off, 0, 0); g.restore();
    }
  } else if (t < T('s14b05')) {
    // 2. drifting through the stars (b02–b04)
    cosmosFull(g, t, S, cosmos);
  } else if (t < T('s14b06+2.8')) {
    // 3. reverse: close on Fear, lit by starlight; the change happens on its face (b05), the breath of a laugh
    // after 'afraid' (b06) — one continuous shot with the faintest push-in
    const z = CLOSE[2] * S.k(t, [['s14b05', 1], ['s14b06+2.8', CLOSE_PUSH, 'sine']]);
    const plate = { key: 'b05', rect: frameRect(CLOSE[0], CLOSE[1], CLOSE[2]), res: CLOSE[2] * CLOSE_PUSH, tb: T('s14b05') };
    drawStage(g, t, S, cam(CLOSE[0], CLOSE[1], z, t, 2), { cosmos, plate });
  } else if (t < T('s14b06+6.35')) {
    // 4a. the same shot breathes out to a medium, anchored on the face: slow at first (the laugh), ≈2.6 at the
    // smile on 'wonder', still gently moving when it cuts (b) — the pull-back continues across the cut
    const k = S.k(t, [['s14b06+2.8', 0], ['s14b06+6.35', 1, 'in']]);
    const pb = pullCam(k);
    const tb = T('s14b05');   // same frozen instant as shot 3's plate: the shot runs on without a pop
    // background plates per zoom bucket (each rendered at its bucket's highest zoom, then shrunk)
    const R = 0.84, kb = Math.floor(Math.log(Z_A / pb.zoom) / Math.log(1 / R) + 1e-9);
    const zHi = Z_A * Math.pow(R, kb), zLo = zHi * R;
    const a = pullCamAtZoom(zHi), b2 = pullCamAtZoom(Math.max(zLo, Z_M * 0.98));
    const plate = { key: 'pb' + kb, rect: unionRect(frameRect(a.x, a.y, a.zoom), frameRect(b2.x, b2.y, b2.zoom)), res: zHi, tb };
    drawStage(g, t, S, cam(pb.x, pb.y, pb.zoom, t, 2), { cosmos, plate, tb });
  } else if (t < T('s14b07')) {
    // 4b. cut on 'amazement' to the two-shot from the side; the pull-back carries on, very slowly, and settles
    const k = S.k(t, [['s14b06+6.35', 0], ['s14b07', 1, 'out']]);
    const c = cam(lerp(TWO_B06[0], TWO[0], k), lerp(TWO_B06[1], TWO[1], k), zoomExp(TWO_B06[2], TWO[2], k), t, 2);
    drawStage(g, t, S, c, { cosmos });
    hoodShimmer(g, c, S.k(t, [['s14b06+6.5', 0], ['s14b06+7.9', 1, 'linear']]));
  } else if (t < T('s14b09')) {
    // 5. close on Fear: the swallow, the breath, "Why are you showing me this?" (b07–b08)
    const z = CLOSE[2] * S.k(t, [['s14b07', 1], ['s14b09', 1.05]]);
    const plate = { key: 'b07', rect: frameRect(CLOSE[0], CLOSE[1] - 4, CLOSE[2]), res: CLOSE[2] * 1.05, tb: T('s14b07') };
    drawStage(g, t, S, cam(CLOSE[0], CLOSE[1] - 4, z, t, 2), { cosmos, plate });
  } else if (t < T('s14b10')) {
    // 6. two-shot: the hand lifts away, the hood turns back to the distance (b09)
    drawStage(g, t, S, cam(TWO[0], TWO[1], TWO[2], t, 2), { cosmos });
  } else {
    // 7. over the Void's shoulder: the far glow; Fear stands and turns to look (b10 → end)
    const z = OTS[2] * S.k(t, [['s14b10', 1], ['scene.end+0.9', 1.03]]);
    const starK = S.k(t, [['s14b10', 1], ['s14b10+2.0', 0.5]]);
    drawStage(g, t, S, cam(OTS[0], OTS[1], z, t, 2), { cosmos, starK });
  }

  grade(g, cold, 0);
  vignette(g, vig);
}
