// s13 · the_turn · backOfMind
// The biggest event in the film is a head turn. Dread peaks, Fear hides, and then the gesture
// Consciousness made comes back from the last place Fear expected it: a hand on its shoulder.
//
// Shots (data/staging.md §3 s13):
//   S.start → b01+2.0  LOCKED wide {500,889,0.72} (= s12's last frame, pixel-matched): THE TURN begins (a rim-light
//                  swell along the hood's edge makes it register); Fear stiffens, freezes.
//   b01+2.0 → +3.5 close on Fear {3.4}: frozen terror readable — eyes enormous, pupils to pinpoints, no breath;
//                  lips part as the hood arrives; a tiny dry swallow. (QA: in the wide Fear's face was ~45 px.)
//   b01+3.5 → b02  Fear's POV, low on the hood {668,480,1.45}, LOCKED: the turn arrives and the hood BOWS to look
//                  straight down at us/Fear — the Void's first movement, now large on screen.
//   b02 → b03      ECU on Fear's eyes (zoom 6.3 → 6.65, centred on the eyes): the hood reflected in them.
//   b03 → b04      high angle, the hood's POV {448,1495,1.6 → 1.74} inside a dark hood-oval: Fear hides.
//   b04 → b05      side close {525,1425,1.75}: Fear left third; the hand comes down the right, settles; flinch.
//   b05 → b06      close {460,1468,2.2 → 2.28}: the trembling stills; ONE eye peeks; hands lower; gaze climbs.
//   b06 → S.end    the same shot tilts on (no cut) → {640,590,1.1}: up the arm to the bowed hood; hold.

import { W, H, TAU, clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { makeExpr } from '../face.mjs';
import { drawFear, FEAR_ARMS, FEAR_FACE } from '../chars/fear.mjs';
import { drawVoid, drawVoidArm, drawVoidHand, toVoidLocal, voidRig, VOID_HANDS } from '../chars/void.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';
import { createCanvas } from '@napi-rs/canvas';

export const id = 's13';

// ---------------------------------------------------------------- staging constants (staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const LOOK_FEAR = { headTurn: -0.3, headDown: 0.8 };
const CAGE_B = [430, 1630, 0.952];
const THRESH = [440, 1648, 0.97];
const VOID_ARM_B = { bend: 1 };
const APPROACH_SHOULDER = [120, -40];
const SLEEVE_CLIP_Y = 1100;

// Fear's local geometry (src/chars/fear.mjs)
const NECK_Y = -148, HEAD_CY = -66;

export const sfx = [
  // THE TURN: a sub swell under the hood's slow yaw; a whisper of heavy cloth as it bows
  { at: 's13b01+0.2', name: 'rumble_low', gain: -14 },
  { at: 's13b01+3.7', name: 'cloth_rustle', gain: -19, rate: 0.8 },
  // "This is it." — the heart, slow and loud in the silence; carries on under the narration
  { at: 's13b02-0.12', name: 'heartbeat', gain: -12, loop: true, until: 's13b03+2.6', rate: 1.3, fade: 0.5 },
  // hiding: a trembling breath, the heart racing through the silence before the hand
  { at: 's13b03+2.3', name: 'breath_shaky', gain: -16 },
  { at: 's13b03+2.5', name: 'heartbeat', gain: -13, loop: true, until: 's13b04+3.0', rate: 1.65, fade: 0.4 },
  { at: 's13b03.end+0.2', name: 'breath_shaky', gain: -18 },
  // the hand: the sleeve lowering, then the touch (fingertips slide in at +2.1 → +2.7)
  { at: 's13b04+0.3', name: 'cloth_rustle', gain: -16 },
  { at: 's13b04+2.45', name: 'cloth_rustle', gain: -21, rate: 0.85 },
  // under the hand the heart slows: fast, then slower, then gone
  { at: 's13b04+2.9', name: 'heartbeat', gain: -15, loop: true, until: 's13b05+2.4', rate: 1.2, fade: 1.6 },
  // looking up: a small held inhale
  { at: 's13b06+0.15', name: 'breath_shaky', gain: -21, until: 's13b06+1.3', fade: 0.3 },
];

// ---------------------------------------------------------------- helpers
const sm = (a, b, x) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };

function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, W, H); }
  g.restore();
}

const sleeveFront = (g, pose) => {
  g.save(); g.beginPath(); g.rect(-1e4, SLEEVE_CLIP_Y, 2e4, 2e4); g.clip();
  drawVoidArm(g, ...VOID_B, pose, 'L', 'sleeve'); g.restore();
};

// blend two Fear arm specs (preset names or objects) by k; bend/hand/front switch at the midpoint
function arm(a, b, k, side) {
  const A = typeof a === 'string' ? FEAR_ARMS[a](side) : a;
  const B = typeof b === 'string' ? FEAR_ARMS[b](side) : b;
  if (k <= 0) return A;
  if (k >= 1) return B;
  const o = k < 0.5 ? { ...A } : { ...B };
  o.target = [lerp(A.target[0], B.target[0], k), lerp(A.target[1], B.target[1], k)];
  return o;
}


// ---------------------------------------------------------------- caches (perf)
// The cage never moves in this scene (door 0.9, unlocked, no shake; the stillness is the point), and Fear is
// always in front of it, so it is drawn once into a world-space sprite. Built from a fixed state/time, so every
// frame is identical whatever order frames are rendered in.
const CAGE_BOX = [222, 1138, 640, 1720], CAGE_RES = 2.4;
let cageSprite = null;
function drawCageCached(g, t0) {
  if (!cageSprite) {
    const [x0, y0, x1, y1] = CAGE_BOX;
    cageSprite = createCanvas(Math.ceil((x1 - x0) * CAGE_RES), Math.ceil((y1 - y0) * CAGE_RES));
    const c = cageSprite.getContext('2d');
    c.scale(CAGE_RES, CAGE_RES); c.translate(-x0, -y0);
    drawCage(c, ...CAGE_B, { t: t0, door: 0.9, locked: 0 });
  }
  const [x0, y0, x1, y1] = CAGE_BOX;
  g.drawImage(cageSprite, x0, y0, x1 - x0, y1 - y0);
}
// The ECU background (set + Void + cage, all motionless, mostly hidden behind Fear's head) is baked once
// at the ECU's reference framing and laid back in world space.
const ECU_W = 840, ECU_H = 1440, ECU_Z = 6.3;
let ecuBG = null;
function drawEcuBackground(g, ref, t0, vpose, st) {
  if (!ecuBG) {
    ecuBG = createCanvas(ECU_W, ECU_H);
    const c = ecuBG.getContext('2d');
    c.translate(ECU_W / 2, ECU_H / 2); c.scale(ECU_Z, ECU_Z); c.translate(-ref[0], -ref[1]);
    drawHQ(c, 'backOfMind', { ...st, t: t0 });
    drawVoid(c, ...VOID_B, { ...vpose, t: t0 });
    drawCage(c, ...CAGE_B, { t: t0, door: 0.9, locked: 0 });
  }
  g.drawImage(ecuBG, ref[0] - ECU_W / 2 / ECU_Z, ref[1] - ECU_H / 2 / ECU_Z, ECU_W / ECU_Z, ECU_H / ECU_Z);
}

// The close on Fear during the turn: everything behind Fear (set, robe, cage) is static there — the hood is far
// above the frame and the bow has not begun — so it is baked once at the shot's framing (crisp at its zoom).
const CU_Z0 = 3.9, CU_Z1 = 3.98, CU_M = 1.12;
let cuBG = null;
function drawCuBackground(g, S, st) {
  const c0 = CU_CAM(S), rw = (W / CU_Z0) * CU_M, rh = (H / CU_Z0) * CU_M, rx = c0.x - rw / 2, ry = c0.y - rh / 2;
  if (!cuBG) {
    const t0 = S.T(CU_IN);
    cuBG = createCanvas(Math.ceil(rw * CU_Z1), Math.ceil(rh * CU_Z1));
    const c = cuBG.getContext('2d');
    c.scale(cuBG.width / rw, cuBG.height / rh); c.translate(-rx, -ry);
    drawHQ(c, 'backOfMind', { ...st, t: t0, lightsDim: 0.4 });
    drawVoid(c, ...VOID_B, { t: t0, ...voidPose(t0, S).head, idle: 0, cosmos: 0, shadowSpread: 1, handL: { ...VOID_ARM_B, show: 0, defer: 'hand' } });
    drawCage(c, ...CAGE_B, { t: t0, door: 0.9, locked: 0 });
  }
  g.drawImage(cuBG, rx, ry, rw, rh);
}

// THE TURN's rim-light swell (QA: the turn, the Void's first movement, was easy to miss on a phone). The hood's own
// rim light is doubled — the same rim, drawn again from a silhouette pass, screen-blended and kept to the hood — so
// as the hood turns, the light visibly slides along its edge. It swells with the turn and holds through the bow.
let rimLayer = null, povBG = null;
function rimSwell(g, cam, vpose, k) {
  if (k <= 0.01) return;
  // half resolution (it is a glow: softer is better, and the silhouette hood sprites build at half the cost), and
  // all the raster work is clipped to the hood's on-screen box
  rimLayer ||= createCanvas(W / 2, H / 2);
  const c = rimLayer.getContext('2d');
  const f = voidRig(vpose).face, fx = VOID_B[0] + f[0] * VOID_B[2], fy = VOID_B[1] + f[1] * VOID_B[2];
  const z = cam.zoom, sx = (x) => W / 2 + (cam.shakeX || 0) + (x - cam.x) * z, sy = (y) => H / 2 + (cam.shakeY || 0) + (y - cam.y) * z;
  const X0 = clamp(Math.floor((sx(fx - 250) - 6) / 2), 0, W / 2), X1 = clamp(Math.ceil((sx(fx + 250) + 6) / 2), 0, W / 2);
  const Y0 = clamp(Math.floor((sy(fy - 260) - 6) / 2), 0, H / 2), Y1 = clamp(Math.ceil((sy(fy + 70) + 6) / 2), 0, H / 2);
  if (X1 <= X0 || Y1 <= Y0) return;
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1;
  c.clearRect(X0, Y0, X1 - X0, Y1 - Y0);
  c.save();
  c.beginPath(); c.rect(X0, Y0, X1 - X0, Y1 - Y0); c.clip();
  c.scale(0.5, 0.5);
  applyCamera(c, cam);
  drawVoid(c, ...VOID_B, { ...vpose, silhouette: true, handL: { ...VOID_ARM_B, show: 0, defer: 'hand' } });
  c.restore();
  // keep the hood's crown and sides only: in the silhouette pass the rims hidden under the mantle (the sleeve tops)
  // show through — fade out above them. (Done in device space with no clip:
  // in @napi-rs/canvas a destination-in fill under a clip or a scaled transform wiped the whole layer.)
  c.save();
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.globalCompositeOperation = 'destination-in';
  const gr = c.createLinearGradient(0, sy(272) / 2, 0, sy(316) / 2);       // world y: the sleeve tops sit at ≈325 (the mantle barely moves in the bow)
  gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  c.fillStyle = gr; c.fillRect(X0, Y0, X1 - X0, Y1 - Y0);
  c.restore();
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = 'screen'; g.globalAlpha = clamp(k);
  g.drawImage(rimLayer, X0, Y0, X1 - X0, Y1 - Y0, X0 * 2, Y0 * 2, (X1 - X0) * 2, (Y1 - Y0) * 2);
  g.restore();
}

// ---------------------------------------------------------------- timing helpers
function beats(S) {
  const T = (a) => S.T(a);
  return {
    b01: T('s13b01'), b02: T('s13b02'), b03: T('s13b03'), b04: T('s13b04'), b05: T('s13b05'), b06: T('s13b06'),
  };
}

// ---------------------------------------------------------------- the Void
function voidPose(t, S) {
  const head = S.k(t, [
    ['s13b01', STARE_B],
    ['s13b01+3.8', { headTurn: -0.3, headDown: 0.3 }, 'sine'],
    ['s13b01+5.0', LOOK_FEAR, 'sine'],
  ]);
  // the hand (§1.5 shoulder recipe with the side approach). The rest cuff hangs right above the cage, so
  // a straight reach would dangle the emerging hand over the TIME-OUT sign: the hand first slides out to
  // the RIGHT of the cage at cuff height, hanging (WP1, mostly above the frame), then descends outside the
  // right bars to the APPROACH point beside Fear, then the fingertips slide in over the shoulder.
  const reach = S.k(t, [['s13b04', 0], ['s13b04+0.85', 1, 'inOut']]);
  const show = S.k(t, [['s13b04+0.45', 0], ['s13b04+1.2', 1, 'sine']]);
  const descend = S.k(t, [['s13b04+0.85', 0], ['s13b04+2.1', 1, 'inOut']]);
  const settle = S.k(t, [['s13b04+2.1', 0], ['s13b04+2.7', 1, 'inOut']]);
  return { head, show, reach, descend, settle };
}

// ---------------------------------------------------------------- Fear

// Fear's breath is sin(t·2π·breathRate) on ABSOLUTE t, so animating the rate would spin the phase. Integrate
// the wanted rate instead and hand drawFear the equivalent constant: rate_eff = phase / (2π t).
// Starts in phase with s12's last frame (0.34 Hz); faster while hiding; slows under the hand.
function breathRateFor(t, S) {
  const t0 = S.T('scene.start');
  const r = (u) => S.k(u, [['scene.start', 0.34], ['s13b03+2.3', 0.34], ['s13b03+3.0', 0.75], ['s13b05+0.6', 0.75], ['s13b05+2.6', 0.36]]);
  if (t <= t0) return 0.34;
  const n = Math.max(4, Math.ceil((t - t0) * 12)), h = (t - t0) / n;
  let cyc = t0 * 0.34;
  for (let i = 0; i < n; i++) cyc += r(t0 + (i + 0.5) * h) * h;
  return cyc / t;
}
function fearPose(t, S) {
  const B = beats(S);
  // --- body
  const crouch = S.k(t, [
    ['s13b01+0.1', 1], ['s13b01+0.4', 0.8, 'out'],           // stiffens the instant the turn starts
    ['s13b03+2.25', 0.8], ['s13b03+2.85', 1, 'inOut'],       // pulls the knees up, hides
    ['s13b05+1.6', 1], ['s13b06+1.0', 0.3, 'inOut'],         // uncurls, looking up the arm
  ]);
  let tremble = S.k(t, [
    ['scene.start', 0.25], ['s13b01+0.1', 0.25], ['s13b01+0.35', 0, 'out'],   // the trembling stops: frozen
    ['s13b03+2.4', 0], ['s13b03+3.4', 0.9, 'inOut'],                           // trembles again, faster than ever
    ['s13b05', 0.9], ['s13b05+2.0', 0, 'out'],                                 // stills under the hand: fast, slower, gone
  ]);
  // breath amplitude; s12 ends on 1.1 * (1 + 0.35 sin(2.9 t)) at 0.34 Hz — continue exactly that across the cut
  const s12Breath = 1.1 * (1 + 0.35 * Math.sin(t * 2.9));
  const breathe = S.k(t, [
    ['scene.start', s12Breath], ['s13b01+0.1', s12Breath],
    ['s13b01+0.4', 0, 'out'],                                 // breath stops
    ['s13b03+2.3', 0], ['s13b03+3.1', 1.3],                   // panting while hidden
    ['s13b05+0.8', 1.3], ['s13b05+2.6', 0.7],                 // calmer
    ['s13b06+0.2', 0.7], ['s13b06+0.8', 0.15],                // a held breath, looking up
  ]);
  const breathRate = breathRateFor(t, S);
  // head: lifts toward the hood when it notices; ducks when hiding; flinch on the touch; tilts back at the end
  const headTilt = S.k(t, [
    ['scene.start', 0.12], ['s13b01+0.25', 0.1], ['s13b01+0.7', -0.1, 'out'],
    ['s13b03+2.2', -0.1], ['s13b03+2.8', 0.06, 'inOut'],
    ['s13b05+2.9', 0.04], ['s13b06+0.3', -0.13, 'inOut'], ['s13b06+1.2', -0.24, 'sine'],
  ]);
  const headTurn = S.k(t, [
    ['s13b01+0.2', 0.05], ['s13b01+0.65', 0.22, 'out'],
    ['s13b03+0.0', 0.22], ['s13b03+0.5', 0.08, 'inOut'],    // to the lens (the hood's POV)
    ['s13b05+0.3', 0.08], ['s13b05+0.8', 0.14, 'inOut'],    // peeking toward the hand
    ['s13b05+2.9', 0.16], ['s13b06+1.0', 0.22, 'sine'],
  ]);
  let headDY = S.k(t, [
    ['scene.start', 8], ['s13b01+0.2', 7], ['s13b01+0.6', -3, 'out'],   // (s12 ends at 8) lifts
    ['s13b01+3.22', -3], ['s13b01+3.32', 2, 'out'], ['s13b01+3.7', -2.5, 'sine'], // dry swallow (in the close)
    ['s13b03+2.2', -2.5], ['s13b03+2.8', 4, 'inOut'],        // ducks into its hands
    ['s13b03+4.8', 4], ['s13b03+4.95', 7, 'out'], ['s13b03+5.6', 5, 'sine'],         // "destroy": cringes
    ['s13b04+2.72', 5], ['s13b04+2.79', 10, 'out'], ['s13b04+3.35', 5, 'sine'],        // flinch at the touch
    ['s13b05+1.4', 5], ['s13b05+2.2', 0, 'inOut'],
    ['s13b05+2.9', 0], ['s13b06+1.1', -6, 'sine'],          // the head goes all the way back
  ]);
  // the head shies a little away from the huge hand while it peeks and stares, and comes back as it looks up
  const headDX = S.k(t, [['s13b05+0.3', 0], ['s13b05+0.9', -6, 'inOut'], ['s13b05+1.6', -6], ['s13b05+2.1', -8, 'sine'], ['s13b05+2.7', -8], ['s13b06+0.9', 0, 'inOut']]);
  // a touch-flinch jolt: the tremble spikes, the body jerks a hair away from the hand and settles back under it
  tremble = clamp(tremble + 0.6 * Math.max(0, 1 - Math.abs(t - S.T('s13b04+2.78')) / 0.18));
  const lean = S.k(t, [['s13b04+2.72', 0], ['s13b04+2.8', -0.03, 'out'], ['s13b04+3.4', 0, 'sine']]);

  // --- arms
  const hideK = S.k(t, [['s13b03+2.25', 0], ['s13b03+2.85', 1, 'inOut']]);
  const peekK = S.k(t, [['s13b05+0.4', 0], ['s13b05+0.85', 1, 'inOut']]);
  const lowerK = S.k(t, [['s13b05+1.5', 0], ['s13b05+2.3', 1, 'inOut']]);
  // Fear's arm targets are raw local points: they do NOT follow crouch / headDY, but the head does (crouch 1
  // drops it 20). The 'handsOnFace' preset (y −192) therefore left the palms on the FOREHEAD with the squeezed
  // lids showing underneath. Aim the wrists just under the eyes instead, so the palms cover them (brows stay
  // visible above the fingers, the trembling mouth below).
  const eyeLY = NECK_Y + 20 * crouch + headDY + HEAD_CY + 8 + FEAR_FACE.eyeY;   // local y of the eyes
  const onFace = (side) => ({ target: [side * 28, eyeLY + 12], bend: -side, front: true, hand: 'palm' });
  // the hands uncross outward first (under the chin), then rise to the face (one eased move through a waypoint)
  let armL = arm('hugSelf', { target: [-36, -134], bend: 1, front: true, hand: 'palm' }, clamp(hideK * 2), -1);
  let armR = arm('hugSelf', { target: [36, -134], bend: -1, front: true, hand: 'palm' }, clamp(hideK * 2), 1);
  armL = arm(armL, onFace(-1), clamp(hideK * 2 - 1), -1);
  armR = arm(armR, onFace(1), clamp(hideK * 2 - 1), 1);
  // the left palm (away from the Void's hand) slides down off its eye: one eye peeks across at the hand
  if (peekK > 0) armL = arm(armL, { target: [-44, eyeLY + 40], bend: 1, front: true, hand: 'palm' }, peekK, -1);
  if (lowerK > 0) {
    armL = arm(armL, 'chest', lowerK, -1);
    armR = arm(armR, { target: [14, -118], bend: 1, front: true, hand: 'open' }, lowerK, 1);
  }

  // --- face
  const sad = { browIn: 0.78, browUp: 0.1, lidTilt: 0.7, lidU: 0.42, lidL: 0.15, smile: -0.45, tremble: 0.3, tears: 0.7, stream: 0.75, pupil: 0.9, lookX: 0.05, lookY: 0.62 }; // = s12's SPENT
  const frozen = { browIn: 0.95, browUp: 0.85, lidU: -0.4, pupil: 0.45, smile: -0.35, wide: 0.2, lookX: 0.35, lookY: -1, tears: 0.7, stream: 0.6 };
  const ecu = { ...frozen, tears: 0.75, lidL: 0.1 };
  const atLens = { ...frozen, lookX: 0.1, lookY: -0.6, tears: 0.7 };
  const wince = { ...atLens, browIn: 1, browUp: 0.1, browSquish: 0.8, lidU: 0.05, lidL: 0.5, lidTilt: 0.35, pupil: 0.5, smile: -0.7, open: 0.16, wide: 0.4, tremble: 0.5, lookX: 0.05, lookY: -0.2 };
  const squeeze = { browIn: 1, browUp: -0.05, browSquish: 0.7, lidU: 1, lidL: 0.6, lidTilt: 0.2, smile: -0.7, open: 0.12, wide: 0.4, tremble: 0.7, tears: 0.6, stream: 0.45, pupil: 0.45 };
  const peek = { browIn: 0.9, browUp: 0.35, lidU: -0.05, lidL: 0.1, pupil: 0.7, smile: -0.4, wide: 0.1, lookX: 0.8, lookY: 0.5, tears: 0.65, stream: 0.45 };
  const stare = { browIn: 0.7, browUp: 0.6, lidU: -0.25, pupil: 1.0, smile: -0.12, open: 0.07, round: 0.3, lookX: 0.8, lookY: 0.45, tears: 0.7, stream: 0.45 };
  const up = { browIn: 0.5, browUp: 0.7, lidU: -0.32, pupil: 1.15, smile: -0.05, open: 0.22, round: 0.35, lookX: 0.3, lookY: -1, tears: 0.85, stream: 0.4 };
  let face = S.k(t, [
    ['scene.start', sad],
    ['s13b01+0.12', sad],
    ['s13b01+0.4', { ...sad, lookX: 0.35, lookY: -1, lidU: 0.1 }, 'out'],   // eyes first
    ['s13b01+0.75', frozen, 'out'],                                          // then everything opens
    ['s13b01+2.0', frozen],
    ['s13b01+2.6', { ...frozen, lookX: 0.3, pupil: 0.3, lidU: -0.45, browUp: 0.95 }, 'sine'], // eyes go enormous, pupils to pinpoints
    ['s13b01+2.75', { ...frozen, lookX: 0.3, pupil: 0.3, lidU: -0.45, browUp: 0.95 }],
    ['s13b01+3.0', { ...frozen, lookX: 0.3, pupil: 0.3, lidU: -0.45, browUp: 0.95, open: 0.22 }, 'sine'], // lips part as the hood arrives
    ['s13b01+3.22', { ...frozen, lookX: 0.3, pupil: 0.3, lidU: -0.45, browUp: 0.95, open: 0.22 }],
    ['s13b01+3.32', { ...frozen, lookX: 0.3, pupil: 0.3, lidU: -0.42, browUp: 0.95, open: 0, pressed: 0.7 }, 'out'], // tiny dry swallow
    ['s13b01+3.7', { ...frozen, lookX: 0.3, pupil: 0.32, open: 0.07 }, 'sine'],
    ['s13b01+5.0', { ...frozen, lookX: 0.3, pupil: 0.35, open: 0.07 }],
    ['s13b02', { ...ecu, lookX: 0.3, open: 0.07 }, 'sine'],
    ['s13b02+0.9', { ...ecu, lookX: 0.3, open: 0.07, tears: 0.95, browIn: 1 }, 'sine'],  // "...it."
    ['s13b03', { ...atLens, open: 0.07 }],
    ['s13b03+1.75', { ...atLens, open: 0.07 }],
    ['s13b03+2.15', wince, 'inOut'],                                         // brows collapse ("had had enough")
    ['s13b03+2.52', wince],
    ['s13b03+2.66', squeeze, 'out'],                                         // eyes squeeze shut behind the palms
    ['s13b05+0.4', squeeze],
    ['s13b05+0.75', peek, 'inOut'],                                          // one eye peeks at the hand
    ['s13b05+1.6', { ...peek, lidL: 0.05, browIn: 0.8, browUp: 0.45 }],
    ['s13b05+2.2', stare, 'inOut'],                                          // stares at the huge, gentle hand
    ['s13b05+2.75', stare],
    ['s13b06-0.1', { ...stare, lookX: 0.6, lookY: -0.35, browUp: 0.65 }, 'sine'], // gaze travels up the arm…
    ['s13b06+0.8', up, 'sine'],                                                     // …up, up, into the hood
  ]);
  face = makeExpr(face);
  face.noAutoBlink = true;
  face.t = t;
  // micro-life: the same tiny gaze drift as s12 (continuous across the cut), plus small darts while frozen
  const darts = sm(B.b01 + 0.8, B.b01 + 1.5, t) * (1 - sm(B.b03 + 2.0, B.b03 + 2.3, t));
  face.lookX = clamp(face.lookX + 0.03 * Math.sin(t * 1.7 + 0.4) + darts * fbm(t * 0.9, 31) * 0.05, -1, 1);
  face.lookY = clamp(face.lookY + 0.02 * Math.sin(t * 1.3 + 1.1) + darts * fbm(t * 0.7, 37) * 0.03, -1, 1);
  // lower lids quiver in the ECU (holding back)
  // (at 24 fps an 11 Hz wobble aliases into flicker and 0.04 lidL is invisible under the tear gloss: a slower,
  // irregular 3–5 Hz quiver around a raised lid — "holding it in" — reads in the ECU)
  const quiver = sm(B.b02 - 0.2, B.b02 + 0.3, t) * (1 - sm(B.b03 - 0.3, B.b03 + 0.2, t));
  face.lidL = clamp(face.lidL + quiver * (0.16 + 0.07 * Math.sin(t * TAU * 3.3) + 0.045 * Math.sin(t * TAU * 4.9 + 1.3)));
  // deliberate blink: after the peek ("A blink."). Otherwise frozen terror never blinks.
  // (s12's slow exhausted blink straddles the cut: finish it)
  face.blink = clamp(face.blink + Math.max(blinkAt(t, S.T('s12b11.end+0.4'), 0.4), blinkAt(t, S.T('s13b05+1.15'), 0.24)));

  // ONE eye peeks: the right eye (under the right palm, beside the Void's hand) stays clenched shut until the
  // hands lower; drawn as a second, eye-clipped pass in render()
  const rightClosed = S.k(t, [['s13b05+0.35', 0], ['s13b05+0.4', 1], ['s13b05+1.5', 1], ['s13b05+1.8', 0, 'inOut']]);
  return { crouch, tremble, breathe, breathRate, lean, headTilt, headTurn, headDX, headDY, armL, armR, face, rightClosed };
}

// ---------------------------------------------------------------- the eye reflection (ECU)
// Reproduce drawFear's head transform so the overlay sits exactly in the irises (valid when tremble = 0).
function eyeIrisPositions(fx, fy, fs, p, t) {
  const br = Math.sin(t * TAU * (p.breathRate || (0.28 + p.tremble * 0.5))) * p.breathe;
  const neckY = NECK_Y + p.crouch * 20 + br * 1.2 + (p.headDY || 0);
  const neckX = p.headDX || 0;
  const out = [];
  const e = p.face;
  const turn = clamp(p.headTurn || 0, -1, 1);
  for (const side of [-1, 1]) {
    const farSide = side * turn > 0;
    const squeeze = farSide ? 1 - Math.abs(turn) * 0.38 : 1 + Math.abs(turn) * 0.06;
    const ex = side * FEAR_FACE.eyeSpacing * (1 - Math.abs(turn) * 0.3) + turn * FEAR_FACE.eyeSpacing * 0.55;
    const ey = FEAR_FACE.eyeY;
    const rx = FEAR_FACE.eyeRx * squeeze, ry = FEAR_FACE.eyeRy;
    const irisR = rx * FEAR_FACE.irisR;
    const ix = ex + clamp(e.lookX, -1, 1) * rx * 0.42;
    const iy = ey + clamp(e.lookY, -1, 1) * ry * 0.36 + ry * 0.04;
    out.push({ ex, ey, rx, ry, ix, iy, irisR });
  }
  return { neckX, neckY, tilt: p.headTilt || 0, eyes: out };
}

function hoodReflection(g, fx, fy, fs, p, t, k) {
  if (k <= 0.01) return;
  const E = eyeIrisPositions(fx, fy, fs, p, t);
  g.save();
  g.translate(fx, fy); g.scale(fs, fs);
  g.translate(E.neckX, E.neckY); g.rotate(E.tilt); g.translate(0, HEAD_CY + 8);
  for (const e of E.eyes) {
    const r = e.irisR;
    g.save();
    g.beginPath(); g.ellipse(e.ex, e.ey, e.rx, e.ry, 0, 0, TAU); g.clip();
    g.beginPath(); g.arc(e.ix, e.iy, r * 0.98, 0, TAU); g.clip();
    g.globalAlpha = k;
    // a pale wash of reflected cavern light on the cornea, so the dark hood reads against it
    const cx = e.ix + r * 0.5, cy = e.iy - r * 0.3;
    const gw = g.createRadialGradient(cx, cy - r * 0.1, 0, cx, cy - r * 0.1, r * 0.75);
    gw.addColorStop(0, 'rgba(205,190,255,0.55)'); gw.addColorStop(1, 'rgba(205,190,255,0)');
    g.fillStyle = gw; g.fillRect(cx - r, cy - r, 2 * r, 2 * r);
    // the hood, bowed toward us: peak, rounded hood, broad shoulders running off the iris rim. Kept in the
    // upper-right of the iris (where the cornea catches the cavern light) so the pinpoint pupil stays clear,
    // and the shoulders run far past the rim so the clip — not a drawn straight edge — ends the silhouette.
    const s = r * 0.33;
    const hx = e.ix + r * 0.5, hy = e.iy - r * 0.22;
    const hood = () => {
      g.beginPath();
      g.moveTo(hx - s * 2.6, hy + s * 4.5);
      g.bezierCurveTo(hx - s * 1.6, hy + s * 1.1, hx - s * 0.8, hy + s * 0.25, hx - s * 0.55, hy - s * 0.05);
      g.bezierCurveTo(hx - s * 0.62, hy - s * 0.65, hx - s * 0.2, hy - s * 1.05, hx + s * 0.05, hy - s * 1.12);
      g.bezierCurveTo(hx + s * 0.35, hy - s * 1.0, hx + s * 0.62, hy - s * 0.6, hx + s * 0.55, hy - s * 0.05);
      g.bezierCurveTo(hx + s * 0.8, hy + s * 0.25, hx + s * 1.6, hy + s * 1.1, hx + s * 2.6, hy + s * 4.5);
    };
    hood(); g.closePath();
    g.fillStyle = 'rgba(10,8,24,0.86)'; g.fill();
    hood();                                       // rim light on the silhouette only (open path: no base line)
    g.strokeStyle = 'rgba(170,145,255,0.85)'; g.lineWidth = Math.max(0.9, r * 0.05); g.lineJoin = 'round';
    g.stroke();
    // the opening: pure darkness
    g.fillStyle = 'rgba(0,0,3,1)';
    g.beginPath(); g.ellipse(hx + s * 0.02, hy - s * 0.42, s * 0.25, s * 0.36, 0, 0, TAU); g.fill();
    // the pinpoint pupil reads on top (a reflection never hides it)
    g.fillStyle = FEAR_FACE.pupilColor;
    g.beginPath(); g.arc(e.ix, e.iy, r * 0.52 * (p.face.pupil ?? 1), 0, TAU); g.fill();
    g.restore();
    // keep the eye wet and alive: re-light the catch-lights over the reflection
    g.save();
    g.globalAlpha = k;
    g.fillStyle = 'rgba(255,255,255,0.95)';
    g.beginPath(); g.arc(e.ix - r * 0.4, e.iy - r * 0.42, r * 0.24, 0, TAU); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.6)';
    g.beginPath(); g.arc(e.ix - r * 0.1, e.iy + r * 0.42, r * 0.08, 0, TAU); g.fill();
    g.restore();
  }
  g.restore();
}

// draw Fear again, clipped to an ellipse around its (screen-)left eye
function leftEyePass(g, fx, fy, fs, pose, E, e) {
  g.save();
  const cur = g.getTransform();
  g.translate(fx, fy); g.scale(fs, fs);
  g.translate(E.neckX, E.neckY); g.rotate(E.tilt); g.translate(0, HEAD_CY + 8);
  const m = g.getTransform();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.beginPath();
  for (let i = 0; i < 40; i++) {
    const a = (i / 40) * TAU, lx = e.ex - 1 + Math.cos(a) * 31, ly = e.ey + Math.sin(a) * 36;
    const wx = m.a * lx + m.c * ly + m.e, wy = m.b * lx + m.d * ly + m.f;
    if (i === 0) g.moveTo(wx, wy); else g.lineTo(wx, wy);
  }
  g.closePath();
  g.clip();
  g.setTransform(cur);
  drawFear(g, fx, fy, fs, { ...pose, shadow: false });
  g.restore();
}

// world position of the midpoint between Fear's eyes (for the ECU framing)
function eyesMid(fx, fy, fs, p, t) {
  const E = eyeIrisPositions(fx, fy, fs, p, t);
  const ex = (E.eyes[0].ex + E.eyes[1].ex) / 2, ey = E.eyes[0].ey + HEAD_CY + 8;
  const c = Math.cos(E.tilt), sn = Math.sin(E.tilt);
  return [fx + fs * (E.neckX + ex * c - ey * sn), fy + fs * (E.neckY + ex * sn + ey * c)];
}

// ---------------------------------------------------------------- cameras
// 0..1 progress from t0 to t1 with a quadratic ramp-up over `a` s and ramp-down over `b` s (C1, no jolt at the
// joins); in between the speed is constant, so the peak speed is as low as the duration allows.
function tiltProgress(t, t0, t1, a, b) {
  const D = t1 - t0;
  if (t <= t0) return 0;
  if (t >= t1) return 1;
  const x = t - t0, v = 1 / (D - a / 2 - b / 2);
  if (x < a) return v * x * x / (2 * a);
  if (x <= D - b) return v * (a / 2 + (x - a));
  const y = D - x;
  return 1 - v * y * y / (2 * b);
}

// THE TURN is cut into three: the locked wide (the turn begins), a close on Fear's frozen terror, then Fear's POV
// low on the hood as it arrives and bows. (QA: the frozen face and the hood's movement were both lost in the wide.)
const CU_IN = 's13b01+2.0', POV_IN = 's13b01+3.5';
const POV_CAM = { x: 668, y: 480, zoom: 1.45 };
// face at screen (340, 585) at zoom 3.9 (the TIME-OUT sign stays just above the frame), from Fear's pose at the cut
const CU_CAM = (S) => {
  const t0 = S.T(CU_IN), P0 = fearPose(t0, S);
  const fx = THRESH[0] + ((P0.headDX || 0) + P0.headTurn * 16) * THRESH[2];
  const fy = THRESH[1] + (NECK_Y + 20 * P0.crouch + P0.headDY + HEAD_CY + 8) * THRESH[2];
  return { x: fx + (W / 2 - 340) / CU_Z0, y: fy + (H / 2 - 585) / CU_Z0 };
};

function camera(t, S, P) {
  const B = beats(S);
  let cam;
  if (t < S.T(CU_IN)) {
    return { x: 500, y: 889, zoom: 0.72 };                                   // LOCKED (= s12's last frame)
  } else if (t < S.T(POV_IN)) {
    // the close on Fear's frozen face, framed on its face at the cut (low-left, looking up-right at the hood)
    cam = { ...CU_CAM(S), zoom: S.k(t, [[CU_IN, CU_Z0], [POV_IN, CU_Z1, 'sine']]) };
  } else if (t < B.b02) {
    return { ...POV_CAM };                                                   // LOCKED: nothing moves but the hood
  } else if (t < B.b03) {
    // ECU on the eyes (both eyes fill the frame); a creeping push
    const m = eyesMid(...THRESH, P, t);
    cam = { x: m[0] - 1, y: m[1] + 4, zoom: S.k(t, [['s13b02', 6.3], ['s13b03', 6.65, 'sine']]) };
  } else if (t < B.b04) {
    // the hood's POV, "FEAR small on the threshold below": wider than the b04 close that follows, so the cut
    // reads as a new shot (1.6–1.74 → b04's 1.75 was a same-size jump cut with Fear sliding 135 px); +10 % push
    cam = { x: 446, y: 1480, zoom: S.k(t, [['s13b03', 1.45], ['s13b04', 1.6, 'sine']]) };
  } else {
    // b04 side close (Fear left third, the hand comes down the right) → slow push to the b05 close once the
    // hand has settled ("hold close on Fear under the hand"; a cut 1.75 → 2.2 on the same axis was a jump cut)
    const push = S.k(t, [['s13b04+3.25', 0], ['s13b05+0.55', 1, 'sine']]);
    const zc = lerp(1.85, 2.2, push) + S.k(t, [['s13b05+0.6', 0], ['s13b05+2.9', 0.08, 'sine']]);
    const xc = lerp(525, 460, push), yc = lerp(1430, 1468, push);
    // then ONE continuous tilt up the arm to the bowed hood. It starts creeping as Fear's gaze climbs the arm
    // (b05 end), so it can stay slow: exponential zoom + y/x spaced so the on-screen speed stays even, on a
    // gentle ramp-up / ramp-down profile (peak ≈ 20 px/frame instead of 31).
    const u = tiltProgress(t, S.T('s13b05+2.9'), S.T('scene.end-0.1'), 1.8, 1.3);
    if (u <= 0) cam = { x: xc, y: yc, zoom: zc };
    else {
      const z1 = 1.1, R = zc / z1;                         // zoom zc → z1 exponentially
      const F = (Math.pow(R, u) - 1) / (R - 1);            // world-path fraction with even screen speed
      cam = { x: lerp(xc, 640, F), y: lerp(yc, 590, F), zoom: zc * Math.pow(z1 / zc, u) };
    }
  }
  const d = drift(t, 2.5);
  cam.shakeX = d.dx; cam.shakeY = d.dy; cam.rot = d.dr;
  return cam;
}

// ---------------------------------------------------------------- render
export function render(g, t, S) {
  const B = beats(S);
  const V = voidPose(t, S);
  const P = fearPose(t, S);
  const cam = camera(t, S, P);

  // grade: start at s12's values and settle into s13's darkest close (staging §4.2)
  const kGrade = S.k(t, [['scene.start', 0], ['s13b01+2.0', 1, 'sine']]);
  const st = { t, lightsDim: lerp(0.35, 0.4, kGrade), mist: 0.6 };

  // the hand (only from s13b04)
  const [fx, fy, fs] = THRESH;
  const sh = [fx + 36 * fs, fy - (130 - 20 * P.crouch) * fs];
  const ap = [sh[0] + APPROACH_SHOULDER[0] * fs, sh[1] + APPROACH_SHOULDER[1] * fs];
  const WP1 = [ap[0] + 15, ap[1] - 235];                  // beside the cage's right bars, hand hanging
  const tA = [lerp(WP1[0], ap[0], V.descend), lerp(WP1[1], ap[1], V.descend)];
  const tgt = [lerp(tA[0], sh[0], V.settle), lerp(tA[1], sh[1], V.settle)];
  const angle = lerp(Math.PI / 2 + 0.3, Math.PI - 0.38, ease.sine(clamp(V.descend * 1.15)));
  const handOut = V.show > 0 || V.reach > 0;
  const handL = handOut
    ? { ...VOID_HANDS.shoulder(toVoidLocal(...VOID_B, ...tgt), -1), ...VOID_ARM_B, angle, elbow: 0.8 * V.reach, show: V.show, reach: V.reach, defer: 'hand' }
    : { ...VOID_ARM_B, show: 0, defer: 'hand' };
  const vpose = { t, ...V.head, idle: 0, cosmos: 0, shadowSpread: 1, handL };

  const ecu = t >= B.b02 && t < B.b03;

  g.save();
  applyCamera(g, cam);
  const cu = t >= S.T(CU_IN) && t < S.T(POV_IN), pov = t >= S.T(POV_IN) && t < B.b02;
  if (ecu) {
    // fixed reference framing = the ECU camera at its first frame (deterministic)
    const t0 = S.T('s13b02');
    const ref = eyesMid(...THRESH, fearPose(t0, S), t0);
    drawEcuBackground(g, [ref[0] - 1, ref[1] + 4], t0, vpose, { ...st, lightsDim: 0.4 });
  } else if (cu) {
    drawCuBackground(g, S, st);
  } else if (pov) {
    // LOCKED frame: the cavern behind the hood is baked once (the cage and Fear are far below this frame)
    if (!povBG) {
      povBG = createCanvas(W, H);
      const c = povBG.getContext('2d');
      applyCamera(c, POV_CAM);
      drawHQ(c, 'backOfMind', { ...st, t: S.T(POV_IN), lightsDim: 0.4 });
    }
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.drawImage(povBG, 0, 0); g.restore();
    drawVoid(g, ...VOID_B, vpose);
  } else {
    drawHQ(g, 'backOfMind', st);
    drawVoid(g, ...VOID_B, vpose);
    // the locked wide draws the cage live, exactly as s12 does (the matched cut); closer shots use the sprite
    if (t < B.b02) drawCage(g, ...CAGE_B, { t, door: 0.9, locked: 0 });
    else drawCageCached(g, S.T('scene.start'));
  }
  if (handOut) sleeveFront(g, vpose);
  const fearDraw = { t, facing: 1, ...P, shadow: true };
  if (P.rightClosed > 0.001) {
    // pass 1: both eyes with the right eye's state (clenched shut); pass 2: the same Fear clipped to the left eye
    // (the clip lies inside the opaque head, so nothing semi-transparent is doubled)
    const rc = P.rightClosed;
    const faceR = { ...P.face, lidU: lerp(P.face.lidU, 1, rc), lidL: lerp(P.face.lidL, 0.5, rc), blink: P.face.blink * (1 - rc) };
    drawFear(g, fx, fy, fs, { ...fearDraw, face: faceR });
    const E = eyeIrisPositions(fx, fy, fs, P, t), e = E.eyes[0];
    leftEyePass(g, fx, fy, fs, fearDraw, E, e);
  } else {
    drawFear(g, fx, fy, fs, fearDraw);
  }
  if (ecu) hoodReflection(g, fx, fy, fs, P, t, 1);
  if (handOut) drawVoidHand(g, ...VOID_B, vpose, 'L');
  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  // the rim swell: in the wide (rising with the turn) and in the POV on the hood (held through the bow); the ECU cuts away
  if (t < B.b02 && !cu) rimSwell(g, cam, vpose, S.k(t, [['s13b01+0.3', 0], ['s13b01+2.4', 1, 'sine']]));

  // hood POV: we look out of the darkness of the hood — a soft dark oval closes in from the edges
  if (t >= B.b03 && t < B.b04) {
    g.save();
    g.translate(W / 2, H * 0.5); g.scale(1, 1.5);
    const gr = g.createRadialGradient(0, 0, W * 0.3, 0, 0, W * 0.6);
    gr.addColorStop(0, 'rgba(2,1,8,0)'); gr.addColorStop(0.5, 'rgba(2,1,8,0.5)'); gr.addColorStop(1, 'rgba(2,1,8,0.95)');
    g.fillStyle = gr; g.fillRect(-W, -H, 2 * W, 2 * H);
    g.restore();
  }

  grade(g, lerp(0.6, 0.65, kGrade), 0);
  vignette(g, lerp(0.5, 0.55, kGrade));
}
