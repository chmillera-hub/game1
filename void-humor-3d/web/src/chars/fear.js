// FEAR — the creator's own Fear (0.85 m): a small soft pale-lavender bean/teardrop (head and body ONE shape: a
// narrower crown leaning back, a fuller bottom pushed forward — a gentle kidney curve in profile), oversized
// violet-grey eyes with heavy expressive upper lids, thin worried brows, a wobbly antenna-tuft of three thin
// drooping wisps with softly glowing tips, thin arms with small four-digit hands, knobbly little legs with round
// feet and a big lopsided hand-knitted mustard scarf (1¼ turns, sagging at the back, a knot at the front-left and
// two spread, fringed ends). Effervescent inner-being glow.
//
// Rig notes
//  * The bean is one mesh built from a smooth-union SDF of two ellipsoids (+ crown taper / lean). The "head" is
//    the top of the bean: a vertex shader bends everything above the scarf rigidly with the head rotation (pivot
//    inside the scarf), so head yaw/pitch/roll and "sinking into the scarf" keep one continuous surface. The head
//    can never sink so far that the mouth goes behind the scarf (MOUTH_CLEAR), and the scarf slips down a little
//    when the head sinks.
//  * The Face rig (core/face.js) lives on the rigid head part; its surface is a ray-cast into the same SDF. Fear
//    adds a real "squeeze" to closed eyes (flattened lids, matched lid roll = no corner gap, '><' creases, cheek
//    push lines) and keeps the sclera below the bloom threshold whatever the set's eye light is.
//  * Arms use their own 2-bone IK (core solveIK2) with rubber-hose stretch up to STRETCH_MAX for far targets
//    (cage bars), and every arm point is pushed outside the bean + scarf, so arms wrap around the body.
//  * Secondary motion (tuft wisps, scarf ends) is a damped-spring response evaluated statelessly: the rig samples
//    the pose on an ABSOLUTE time grid (SPRING_DT) over the last ~0.8 s and convolves the motion of the strand
//    roots with the spring kernel (weights are a smooth function of t). Pure function of t, no frame aliasing.
// Pose API, anchors, tips: docs/chars/fear.md.  Lab: src/labs/fear.js.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { Character, gazePoint } from '../core/character.js';
import { Face, EXPR, FACE_DEFAULTS } from '../core/face.js';
import { SweepTube, Hand, solveIK2, orientYZ } from '../core/limbs.js';
import { enhance, glowSprite, contactShadow } from '../core/materials.js';
import { Particles, CELL } from '../core/particles.js';
import { CTX, EYE_LIGHT } from '../core/context.js';
import { clamp, lerp, smooth, smoothstep, noise1, fbm1, hash1 } from '../core/util.js';

const TAU = Math.PI * 2;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const toV = (a) => (a instanceof THREE.Vector3 ? a.clone() : V3(a[0], a[1], a[2]));
const fract = (x) => x - Math.floor(x);
const _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _e = new THREE.Euler(), _v = new THREE.Vector3(), _g = new THREE.Vector3();
const QI = new THREE.Quaternion();

// ---------------------------------------------------------------------------------------------------------
// Palette
const C_BODY = 0xc1acef, C_RIM = 0xb49cff, C_GLOW = 0xc8b4ff, C_WRAP = 0xff9fd2, C_LIMB = 0xb7a2e6, C_TUFT = 0xcfbcf8;
const C_SCARF = 0xe2a21e, C_FRINGE = 0xc98a1c;
const C_IRIS = 0x4b4184, C_IRIS2 = 0x8e84c4, C_LIMBAL = 0x170d34, C_SCLERA = 0xd8d2e8, C_BROW = 0x4a3474, C_LASH = 0x2a1a46;

// ---------------------------------------------------------------------------------------------------------
// Proportions. Root space: feet on y = 0, faces +Z, +X = character's left. Body space: origin at the pelvis.
export const PELVIS_Y = 0.212, SIT_Y = 0.088, KNEEL_Y = 0.125;
const HEAD_C = V3(0, 0.40, 0);            // head centre (body space) = Face origin
const PIVOT = V3(0, 0.265, 0);            // bend pivot (body space, inside the scarf)
const BEND_Y = [0.195, 0.315];            // bend blend zone (body-space y): 0 below .. 1 (rigid head) above
const SHOULDER = V3(0.168, 0.18, 0.045);
const HIP = V3(0.07, 0.0, 0.0);
const UPPER = 0.12, FORE = 0.114, HAND = 0.075;
const ARM_R = [0.0148, 0.0128, 0.0118, 0.0108];
const STRETCH_MAX = 1.36;                 // rubber-hose arm stretch for far targets (reach 0.234 -> ~0.32 m)
const THIGH = 0.098, SHIN = 0.094, ANKLE_Y = 0.032;
const SCARF_Y = 0.234, SCARF_FOLLOW = 0.45, SCARF_R = 0.036;
const EYE = { u: 0.45, v: 0.18, r: 0.08, sink: 0.66 };
const MOUTH_V = -0.31, HW0 = 0.047;
const MOUTH_CLEAR = 0.032;                // mouth line stays >= this above the scarf top (body space)
const LEG_R = [0.021, 0.0172, 0.0182, 0.0152, 0.0165];

// ---------------------------------------------------------------------------------------------------------
// Bean SDF (body space): smooth union of a full lower ellipsoid and a rounder upper (head) ellipsoid whose crown
// tapers (teardrop) and leans back (kidney profile).
const ELL = [
  { c: [0, 0.112, 0.014], r: [0.232, 0.205, 0.222] },
  { c: [0, 0.385, -0.002], r: [0.188, 0.235, 0.182] },
];
function sdEll(x, y, z, E) {
  const px = x - E.c[0], py = y - E.c[1], pz = z - E.c[2];
  const k0 = Math.hypot(px / E.r[0], py / E.r[1], pz / E.r[2]);
  const k1 = Math.hypot(px / (E.r[0] * E.r[0]), py / (E.r[1] * E.r[1]), pz / (E.r[2] * E.r[2]));
  return k1 < 1e-9 ? -0.18 : (k0 * (k0 - 1)) / k1;
}
function smin(a, b, k) { const h = clamp(0.5 + (0.5 * (b - a)) / k); return lerp(b, a, h) - k * h * (1 - h); }
export function bodySDF(x, y, z) {
  const tp = smoothstep(0.46, 0.64, y), s = 1 - 0.2 * tp;
  const dH = sdEll(x / s, y, (z + 0.024 * tp) / s, ELL[1]) * s;
  let d = smin(sdEll(x, y, z, ELL[0]), dH, 0.11);
  // soft cheek fullness beside the mouth (helps the mouth/cheeks read in 3/4)
  const ch = Math.exp(-(((Math.abs(x) - 0.1) / 0.06) ** 2) - (((y - 0.33) / 0.05) ** 2)) * smoothstep(0.05, 0.16, z);
  return d - 0.006 * ch;
}
function sdfGrad(x, y, z, out = V3()) {
  const e = 6e-4;
  out.set(bodySDF(x + e, y, z) - bodySDF(x - e, y, z), bodySDF(x, y + e, z) - bodySDF(x, y - e, z), bodySDF(x, y, z + e) - bodySDF(x, y, z - e));
  return out.normalize();
}
function rayHit(o, d, rMax = 0.6) {   // ray from an interior point o along unit d -> distance to the surface
  let a = 0, b = rMax;
  for (let i = 0; i < 30; i++) {
    const m = 0.5 * (a + b);
    if (bodySDF(o.x + d.x * m, o.y + d.y * m, o.z + d.z * m) < 0) a = m; else b = m;
  }
  return 0.5 * (a + b);
}
// Face surface (head-local: origin = HEAD_C): u longitude (+ toward its left), v latitude
function headSurface(u, v) {
  const d = V3(Math.sin(u) * Math.cos(v), Math.sin(v), Math.cos(u) * Math.cos(v));
  const r = rayHit(HEAD_C, d);
  const pb = HEAD_C.clone().addScaledVector(d, r);
  const n = sdfGrad(pb.x, pb.y, pb.z);
  return { p: pb.sub(HEAD_C), n };
}
const MOUTH_P = headSurface(0, MOUTH_V).p;                       // head-local mouth centre
const SCARF_TOP = SCARF_Y + SCARF_R + 0.002;                     // top of the wrap at the front (body space)

// ---------------------------------------------------------------------------------------------------------
// Expressions (Face params tuned for Fear). FX('scared', {...}). Fear's baseline is anxious: lids a bit wide,
// inner brows up, pupils a touch small. Heavy lids are reserved for sad / tired / crying.
// Extra Fear-only face params: squeeze / squeezeL / squeezeR (0..1) = eyes squeezed shut ('><': flattened lids,
// creases, cheeks pushed up). Use with lidU ~0 (or blink 1) and lidL ~1.
export const FEAR_BASE = { lidU: 1.07, browIn: 0.56, browOut: 0.02, browSq: 0.12, lidSad: 0.14, pupil: 0.9, mSmile: -0.1, mTeethU: 0.55, mTeethL: 0.3, mTongue: 0.45, squeeze: 0 };
export const FEAR_EXPR = {
  neutral: {},
  worried: { browIn: 0.86, browOut: -0.14, browSq: 0.38, lidSad: 0.42, lidU: 1.04, mSmile: -0.36, mPress: 0.3, mWide: -0.12 },
  nervous: { browIn: 0.76, browOut: 0.14, browSq: 0.26, lidSad: 0.3, lidU: 1.13, mSmile: 0.14, mClench: 0.65, mWide: 0.3, mAsym: 0.12, saccade: 1.5, pupil: 0.82 },
  scared: { lidU: 1.3, lidL: 0.0, browIn: 0.96, browOut: 0.3, browSq: 0.46, lidSad: 0.3, mSmile: -0.52, mOpen: 0.32, mWide: 0.45, mTeethL: 0.55, mTeethU: 0.4, pupil: 0.64, mTremble: 0.35 },
  terror: { lidU: 1.42, browIn: 1, browOut: 0.62, browSq: 0.55, lidSad: 0.25, mOpen: 0.86, mWide: 0.7, mSmile: -0.66, mTeethL: 0.8, mTeethU: 0.6, pupil: 0.45, mTremble: 0.6 },
  flinch: { lidU: 0.0, blink: 1, lidL: 1, squeeze: 1, browIn: 1, browSq: 0.95, browOut: -0.32, lidSad: 0, mClench: 1, mWide: 1, mSmile: -0.35, mAsym: 0.1, autoBlink: 0, saccade: 0 },
  cry: { browIn: 1, browOut: -0.35, browSq: 0.5, lidSad: 0.7, lidU: 0.9, lidL: 0.28, mSmile: -0.75, mOpen: 0.36, mWide: 0.35, mPout: 0.3, mTremble: 0.6, tearL: 0.85, tearR: 0.8, wet: 0.9 },
  sob: { browIn: 1, browOut: -0.4, browSq: 0.7, lidSad: 0.4, lidU: 0.06, lidL: 0.85, squeeze: 0.75, mSmile: -0.8, mOpen: 0.72, mWide: 0.5, mTeethU: 0.45, mTremble: 0.7, tearL: 1, tearR: 1, wet: 1, autoBlink: 0 },
  sniffle: { browIn: 0.92, browOut: -0.26, browSq: 0.32, lidSad: 0.55, lidU: 0.88, lidL: 0.2, mSmile: -0.38, mPout: 0.45, mPress: 0.35, tearL: 0.5, tearR: 0.45, wet: 0.75 },
  startle: { lidU: 1.42, lidL: 0, browIn: 0.92, browOut: 0.95, mOpen: 0.56, mRound: 0.6, mWide: 0.1, pupil: 0.55, autoBlink: 0, saccade: 0 },
  listen: { lidU: 1.27, browIn: 0.82, browOut: 0.46, browAsym: 0.32, browSq: 0.15, mOpen: 0.16, mRound: 0.55, mSmile: -0.15, pupil: 0.82, saccade: 0.35 },
  curious: { lidU: 1.14, browIn: 0.52, browOut: 0.36, browAsym: 0.3, mSmile: 0.06, mRound: 0.25, mOpen: 0.04, mPress: 0.1, pupil: 1.1 },
  peek: { lidUL: 1.14, lidUR: 0.05, lidLR: 0.8, squeezeR: 0.65, browIn: 0.82, browSq: 0.5, browOutR: -0.25, mClench: 0.5, mWide: 0.3, mSmile: -0.12, lidSad: 0.2 },
  wonder: { lidU: 1.33, lidL: 0.0, browIn: 0.74, browOut: 0.52, browSq: 0, lidSad: 0.05, mOpen: 0.5, mRound: 0.5, mSmile: 0.08, pupil: 1.5, wet: 0.85, saccade: 0.25 },
  awe: { lidU: 1.2, lidL: 0.08, browIn: 0.86, browOut: 0.26, lidSad: 0.2, mOpen: 0.3, mRound: 0.3, mSmile: 0.3, pupil: 1.5, wet: 1, tearL: 0.55, tearR: 0.5 },
  // shy: eyes DOWN (lidU > 1 compensates the lid following the downward gaze), inner brows up, tiny pressed smile
  shy: { lidU: 1.14, lidL: 0.02, browIn: 0.82, browOut: 0.02, browSq: 0.26, lidSad: 0.45, mSmile: 0.12, mPress: 0.55, mWide: -0.38, blush: 1, gazePitch: -0.34, gazeYaw: 0.04, pupil: 1.08 },
  shySmile: { lidU: 1.13, lidL: 0.06, browIn: 0.78, browOut: 0.06, browSq: 0.16, lidSad: 0.42, mSmile: 0.44, mPress: 0.5, mWide: -0.32, mAsym: 0, blush: 1, gazePitch: -0.28, gazeYaw: 0.03, pupil: 1.12 },
  hopeful: { lidU: 1.16, browIn: 0.72, browOut: 0.22, mSmile: 0.26, mOpen: 0.05, wet: 0.45, pupil: 1.2 },
  relieved: { lidU: 0.94, lidL: 0.1, browIn: 0.74, browOut: 0.0, lidSad: 0.32, mSmile: 0.36, mOpen: 0.1, mRound: 0.3 },
  happy: { mSmile: 0.92, mOpen: 0.2, lidU: 1.12, lidL: 0.26, browIn: 0.56, browOut: 0.36, lidSad: 0.05, blush: 0.45, mTeethU: 0.55, mWide: 0.2, pupil: 1.15 },
  giggle: { mSmile: 0.95, mOpen: 0.32, mTeethU: 0.7, lidU: 0.8, lidL: 0.6, browIn: 0.64, browOut: 0.3, lidSad: 0.1, blush: 0.55 },
  sad: { mSmile: -0.6, mPout: 0.36, browIn: 0.9, browOut: -0.38, browSq: 0.22, lidSad: 0.66, lidU: 0.7, wet: 0.35 },
  gulp: { lidU: 1.22, browIn: 0.9, browSq: 0.38, mPress: 0.9, mWide: -0.35, mSmile: -0.22, lidSad: 0.2 },
  trust: { lidU: 0.98, lidL: 0.18, browIn: 0.64, browOut: 0.0, lidSad: 0.28, mSmile: 0.32, wet: 0.5, pupil: 1.1 },
  confused: { browAsym: 0.6, browIn: 0.42, browSq: 0.3, mAsym: -0.35, mSmile: -0.1, mPress: 0.3, lidU: 1.05 },
  whimper: { browIn: 1, browOut: -0.3, browSq: 0.3, lidSad: 0.6, lidU: 0.9, mSmile: -0.6, mOpen: 0.18, mWide: 0.15, mTremble: 0.85, wet: 0.6 },
};
FEAR_EXPR.squeeze = FEAR_EXPR.flinch;
const SIDE_KEYS = { lidUL: 'lidU', lidUR: 'lidU', lidLL: 'lidL', lidLR: 'lidL', browInL: 'browIn', browInR: 'browIn', browOutL: 'browOut', browOutR: 'browOut', squeezeL: 'squeeze', squeezeR: 'squeeze' };
/** Fear face params: FX('scared'), FX('scared', {mOpen: .3}), FX([['scared', .6], ['cry', .4]]). Unknown names fall back to core EXPR. */
export function FX(name, over = {}) {
  const base = { ...FACE_DEFAULTS, ...FEAR_BASE };
  const get = (nm) => FEAR_EXPR[nm] ?? EXPR[nm] ?? {};
  if (typeof name === 'string') Object.assign(base, get(name));
  else if (Array.isArray(name)) {
    const b0 = { ...base };
    for (const [nm, w] of name) for (const [k2, val] of Object.entries(get(nm))) {
      const ref = b0[k2] ?? b0[SIDE_KEYS[k2]] ?? 0;
      base[k2] = (base[k2] ?? b0[SIDE_KEYS[k2]] ?? 0) + (val - ref) * w;
    }
  }
  return Object.assign(base, over);
}
/** Blend two face param objects (per-side keys fall back to their generic key). */
export function mixFace(a, b, u) {
  const o = { ...a };
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k2 of keys) {
    const va = a[k2] ?? a[SIDE_KEYS[k2]] ?? FACE_DEFAULTS[k2] ?? 0, vb = b[k2] ?? b[SIDE_KEYS[k2]] ?? FACE_DEFAULTS[k2] ?? 0;
    o[k2] = (typeof va === 'number' && typeof vb === 'number') ? lerp(va, vb, u) : (u < 0.5 ? va : vb);
  }
  return o;
}

// ---------------------------------------------------------------------------------------------------------
// Walk styles. stride = one foot's travel (m) half-amplitude; cad = cycles/s. Body speed = 4*stride*cad.
export const WALK = {
  walk: { cad: 1.7, stride: 0.055, lift: 0.036, bob: 0.011, roll: 0.06, twist: 0.08, lean: 0.06, sway: 0.008, arm: 1, crouch: 0.05, tiptoe: 0, arms: 'swing', hold: 0 },
  sneak: { cad: 0.8, stride: 0.05, lift: 0.058, bob: 0.007, roll: 0.05, twist: 0.05, lean: 0.26, sway: 0.007, arm: 0.3, crouch: 0.45, tiptoe: 0.8, arms: 'tiptoe', hold: 0.4 },
  run: { cad: 2.9, stride: 0.085, lift: 0.05, bob: 0.016, roll: 0.05, twist: 0.1, lean: 0.24, sway: 0.006, arm: 1, crouch: 0.12, tiptoe: 0.3, arms: 'flail', hold: 0, flight: 0.012 },
  waddle: { cad: 1.5, stride: 0.045, lift: 0.026, bob: 0.01, roll: 0.13, twist: 0.04, lean: 0.0, sway: 0.016, arm: 0.6, crouch: 0.05, tiptoe: 0, arms: 'swing', hold: 0 },
  stomp: { cad: 1.6, stride: 0.055, lift: 0.045, bob: 0.02, roll: 0.08, twist: 0.06, lean: 0.04, sway: 0.01, arm: 1, crouch: 0.1, tiptoe: 0, arms: 'swing', hold: 0 },
};
WALK.scurry = WALK.run; WALK.tiptoe = WALK.sneak; WALK.stroll = WALK.walk;
/** Ground speed (m/s) for a walk style at `rate` cycles/s (default: the style's natural cadence). */
export const walkSpeed = (style = 'walk', rate) => { const s = WALK[style] || WALK.walk; return 4 * s.stride * (rate ?? s.cad); };

function footCycle(a, st) {   // a = 0..1 within this foot's cycle. stance [0,.5): front -> back on the ground
  if (a < 0.5) {
    const u = a / 0.5;
    return { z: 1 - 2 * u, lift: 0, pitch: u < 0.15 ? lerp(-0.25, 0, u / 0.15) : u > 0.7 ? lerp(0, 0.45, (u - 0.7) / 0.3) : 0 };
  }
  const u = (a - 0.5) / 0.5;
  const hold = st.hold || 0;
  const e = smooth(u / (1 - hold * 0.55));
  const lift = Math.pow(Math.sin(Math.PI * Math.min(1, u / (1 - hold * 0.25))), 0.8);
  return { z: lerp(-1, 1, e), lift, pitch: lerp(0.45, -0.25, smooth(u)) + 0.25 * Math.sin(Math.PI * u) * (hold > 0 ? 1.6 : 0.3) };
}

// ---------------------------------------------------------------------------------------------------------
// Arm presets (LEFT arm; mirrored for R). frame 'body' = body space (pelvis origin), 'head' = head-local.
// p = wrist, fd = finger direction, pn = palm normal, pole = elbow hint, sh = arm-root slide on the soft bean,
// hand = Hand.pose params, dyR/dzR = extra offset for the RIGHT wrist (so crossed hands don't collide).
const _eyeS = headSurface(EYE.u, EYE.v);
// wipe: a small fist, palm toward the face, its curled fingers pressed on the lower half of the eye (the camera sees
// the round back of the fist); WIPE_C = fist centre (head-local, LEFT eye)
const WIPE_C = _eyeS.p.clone().addScaledVector(_eyeS.n, 0.036).add(V3(-0.01, -0.028, 0.0));
const WIPE_FD = V3(-0.12, 1, -0.15).normalize(), WIPE_PN = V3(0.15, -0.2, -1).normalize();
const WIPE_P = WIPE_C.clone().addScaledVector(WIPE_FD, -0.03).addScaledVector(WIPE_PN, -0.008);
const ARM = {
  rest: { f: 'body', p: [0.215, 0.05, 0.12], fd: [-0.1, -1, 0.3], pn: [-1, 0, -0.35], pole: [0.6, -0.3, -0.9], hand: { curl: 0.32, spread: 0.12, thumb: 0.3, cup: 0.2 } },
  // hugs itself: elbows tucked at the sides, forearms wrap the bean and cross over the chest, fists clutch the scarf
  // (the arm roots slide forward-in on the bean so the elbows can bend and tuck low at the sides; forearms rise in a
  // crossed V; R fist sits a little higher and in front)
  hug: { f: 'body', p: [-0.03, 0.222, 0.272], dyR: 0.03, dzR: 0.018, fd: [-0.35, 0.9, 0.1], pn: [0.1, 0.0, -1], pole: [0.7, -1, 0.15], sh: [-0.05, 0.01, 0.1],
    hand: { curl: 0.95, spread: 0.04, cup: 0.45, thumb: 0.1 } },
  clasp: { f: 'body', p: [0.026, 0.215, 0.28], fd: [-0.4, 0.85, 0.3], pn: [-1, 0, 0.15], pole: [1, -0.8, -0.1], sh: [-0.03, 0.02, 0.06], hand: { curl: 0.5, cup: 0.4, thumb: 0.55, spread: 0.05 } },
  chest: { f: 'body', p: [0.06, 0.165, 0.262], fd: [-0.35, 0.9, 0.15], pn: [0, 0, -1], pole: [1, -0.7, 0], sh: [-0.02, 0.01, 0.04], hand: { curl: 0.2, cup: 0.35, spread: 0.2, thumb: 0.35 } },
  tummy: { f: 'body', p: [0.115, 0.065, 0.248], fd: [-0.6, -0.5, 0.25], pn: [-0.3, 0, -1], pole: [1, -0.3, -0.4], hand: { curl: 0.2, cup: 0.3, spread: 0.2, thumb: 0.3 } },
  fidget: { f: 'body', p: [0.035, 0.105, 0.265], fd: [-0.85, 0.25, 0.4], pn: [0.15, -0.9, -0.4], pole: [1, -0.6, -0.3], sh: [-0.02, 0, 0.05], hand: { curl: 0.55, point: 0.75, thumb: 0.3, spread: 0.05 } },
  behind: { f: 'body', p: [0.09, 0.07, -0.215], fd: [-0.5, -0.6, -0.2], pn: [0, 0, 1], pole: [1, 0, 0.3], hand: { curl: 0.4, cup: 0.3 } },
  up: { f: 'body', p: [0.3, 0.42, 0.09], fd: [0.35, 1, 0.15], pn: [0, 0.1, 1], pole: [1, -0.8, -0.4], hand: { splay: 1, spread: 0.95, thumb: 0.9, curl: 0, cup: 0 } },
  shrug: { f: 'body', p: [0.27, 0.19, 0.14], fd: [0.7, 0.15, 0.6], pn: [0, 1, 0.1], pole: [1, -0.6, -0.4], hand: { curl: 0.12, spread: 0.45, thumb: 0.7, cup: 0.2 } },
  point: { f: 'body', p: [0.22, 0.28, 0.24], fd: [0.15, 0.05, 1], pn: [-0.6, -0.8, 0], pole: [1, -0.5, -0.4], hand: { point: 1, curl: 0.5, thumb: 0.2 } },
  wave: { f: 'body', p: [0.25, 0.4, 0.13], fd: [0.12, 1, 0.1], pn: [0, 0, 1], pole: [1, -0.7, -0.3], hand: { spread: 0.5, thumb: 0.6, curl: 0.06, cup: 0.05 } },
  reach: { f: 'body', p: [0.2, 0.36, 0.3], fd: [0.1, 0.6, 1], pn: [-0.2, -0.6, 0.1], pole: [1, -0.6, -0.4], hand: { spread: 0.45, curl: 0.1, thumb: 0.55, cup: 0.1 } },
  tiptoe: { f: 'body', p: [0.105, 0.245, 0.275], fd: [0.0, -0.75, 0.65], pn: [-0.15, -0.6, -0.8], pole: [1, -0.7, -0.3], sh: [-0.025, 0.025, 0.06], hand: { curl: 0.35, cup: 0.2, spread: 0.1, thumb: 0.2 } },
  flail: { f: 'body', p: [0.255, 0.33, 0.13], fd: [0.3, 0.9, 0.3], pn: [0, 0, 1], pole: [1, -0.6, -0.5], hand: { splay: 0.7, spread: 0.8, thumb: 0.8, curl: 0 } },
  grip: { f: 'body', p: [0.14, 0.27, 0.27], fd: [-0.8, 0, 0.3], pn: [0, 0, 1], pole: [1, -0.7, -0.3], hand: { grip: 1, curl: 0.6, thumb: 0.15 } },
  hold: { f: 'body', p: [0.14, 0.27, 0.27], fd: [-0.2, 0.3, 1], pn: [-0.3, -1, 0], pole: [1, -0.7, -0.3], hand: { grip: 0.7, curl: 0.45, thumb: 0.3 } },
  // head-frame presets (follow the head)
  wipe: { f: 'head', p: WIPE_P.toArray(), fd: WIPE_FD.toArray(), pn: WIPE_PN.toArray(), pole: [1, -1, 0.1], sh: [-0.015, 0.05, 0.06], hand: { curl: 0.95, thumb: 0.1, cup: 0.45, spread: 0.02 } },
  cover_mouth: { f: 'head', p: [0.035, -0.135, 0.205], fd: [-0.3, 1, 0.15], pn: [0, 0, -1], pole: [1, -0.8, -0.1], sh: [-0.02, 0.03, 0.05], hand: { curl: 0.12, spread: 0.2, cup: 0.35, thumb: 0.35 } },
  cheeks: { f: 'head', p: [0.175, -0.12, 0.085], fd: [-0.25, 1, 0.3], pn: [-1, 0, -0.4], pole: [1, -0.8, -0.2], sh: [0, 0.03, 0.02], hand: { curl: 0.12, spread: 0.35, cup: 0.45, thumb: 0.45 } },
  // cowering: hands up in front of the eyes, palms out (the head tucks down behind them)
  shield: { f: 'head', p: [0.068, 0.0, 0.232], fd: [0.05, 1, 0.1], pn: [0.05, 0.05, 1], pole: [1, -0.9, -0.1], sh: [-0.02, 0.06, 0.06], hand: { splay: 0.45, spread: 0.6, thumb: 0.6, curl: 0.1 } },
  eyes: { f: 'head', p: [0.08, -0.035, 0.22], fd: [-0.3, 1, 0.1], pn: [0, -0.1, -1], pole: [1, -0.8, -0.1], sh: [-0.02, 0.04, 0.05], hand: { spread: 0.5, curl: 0.1, cup: 0.2, thumb: 0.3 } },
  chin: { f: 'head', p: [0.06, -0.145, 0.175], fd: [-0.35, 0.8, 0.4], pn: [0, -0.3, -1], pole: [1, -0.8, -0.2], hand: { curl: 0.65, point: 0.4, thumb: 0.3 } },
  bite: { f: 'head', p: [0.03, -0.145, 0.195], fd: [-0.2, 1, 0.25], pn: [0, 0, -1], pole: [1, -0.8, -0.1], hand: { curl: 0.62, thumb: 0.25, cup: 0.3 } },
};
ARM.crossed = ARM.hug; ARM.hips = ARM.tummy; ARM.pocket = ARM.behind; ARM.self = ARM.hug; ARM.heart = ARM.chest; ARM.scarf = ARM.hug;
export const ARM_PRESETS = Object.keys(ARM);

// ---------------------------------------------------------------------------------------------------------
// Tuft: three thin, soft, drooping wisps with glowing bulb tips (head-local, from the top of the head).
// o = base offset, d = rest direction, L = length, curv = rest bend (added along the strand), r = thickness mult.
const TUFT = [
  { o: [0.004, 0, 0.008], d: [0.2, 1, 0.1], L: 0.16, curv: [1.05, -0.85, 0.15], r: 1.0 },
  { o: [-0.013, -0.004, 0.0], d: [-0.4, 1, -0.02], L: 0.118, curv: [-0.95, -0.8, -0.15], r: 0.88 },
  { o: [0.006, -0.004, -0.014], d: [0.02, 1, -0.5], L: 0.088, curv: [0.15, -0.6, -0.85], r: 0.78 },
];
const tuftRad = (s) => Math.max(lerp(0.0064, 0.0032, Math.pow(s, 0.7)), 0.0057 * Math.sqrt(Math.max(0, 1 - ((1 - s) / 0.12) ** 2)));
const TUFT_SEG = 16;
// Secondary motion: spring kernels sampled on an ABSOLUTE time grid (see _secondary)
const SPRING_N = 50, SPRING_DT = 0.016;
function springK(tau, f, zeta) {   // second derivative of the damped spring's impulse response
  const w = TAU * f, a = zeta * w, wd = w * Math.sqrt(1 - zeta * zeta);
  return Math.exp(-a * tau) * (-2 * a * Math.cos(wd * tau) + ((a * a - wd * wd) / wd) * Math.sin(wd * tau));
}
const softClamp = (v, m) => m * Math.tanh(v / m);
const smax0 = (x, w) => (x >= w ? x : x <= -w ? 0 : ((x + w) * (x + w)) / (4 * w));   // C1-smooth max(0, x)

// ---------------------------------------------------------------------------------------------------------
// Materials: the inner-being parts are MeshPhong (soft broad highlight) + core enhance() (rim / glow / fizz / wrap):
// it reads like the physical 'being' material at Fear's scale and costs far less per pixel on SwiftShader.
function beingLite(color, o) {
  const m = new THREE.MeshPhongMaterial({ color: new THREE.Color(color), shininess: o.shininess ?? 22, specular: new THREE.Color(o.specular ?? 0x2e2a3c), vertexColors: !!o.vertexColors });
  return enhance(m, { rim: o.rim, rimColor: o.rimColor ?? color, rimPower: o.rimPower ?? 2.2, glow: o.glow, glowColor: o.glowColor ?? color,
    fizz: o.fizz ?? 0, fizzColor: o.fizzColor ?? 0xffffff, fizzScale: o.fizzScale ?? 7, fizzSpeed: o.fizzSpeed ?? 0.3, wrap: o.wrap ?? 0.3, wrapColor: o.wrapColor ?? color });
}

function bendMaterial(mat, U) {
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => {
    prev(sh, r);
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
        uniform vec4 uBendQ; uniform vec3 uBendPivot, uBendOff; uniform vec2 uBendY;
        vec3 fr_rot(vec3 v, vec4 q){ return v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v); }
        vec4 fr_q(float w){
          float s = length(uBendQ.xyz);
          if (s < 1e-6) return vec4(0.0, 0.0, 0.0, 1.0);
          float a = 2.0 * atan(s, uBendQ.w) * w * 0.5;
          return vec4(uBendQ.xyz / s * sin(a), cos(a));
        }`)
      .replace('#include <beginnormal_vertex>', `#include <beginnormal_vertex>
        float frW = smoothstep(uBendY.x, uBendY.y, position.y);
        vec4 frQ = fr_q(frW);
        objectNormal = fr_rot(objectNormal, frQ);`)
      .replace('vObjPos = transformed;', `vObjPos = transformed;
        transformed = uBendPivot + uBendOff * frW + fr_rot(transformed - uBendPivot, frQ);`);
  };
  const key = mat.customProgramCacheKey.bind(mat);
  mat.customProgramCacheKey = () => key() + 'fearBend';
  return mat;
}

// ONE material for wrap, knot, tails and fringe (uv repeats are baked into each geometry). The knit is PROCEDURAL:
// V-stitch chevrons + column grooves as colour and a derivative bump, faded out where a stitch gets smaller than ~2 px
// (no shimmer). SwiftShader pays far more for texture fetches (sRGB + trilinear) than for these few ALU ops.
function knitMaterial() {
  const m = new THREE.MeshStandardMaterial({ color: new THREE.Color(C_SCARF), roughness: 0.92, metalness: 0 });
  enhance(m, { rim: 0.28, rimColor: 0xffd27a, rimPower: 3.2, glow: 0.12, glowColor: C_SCARF, wrap: 0.35, wrapColor: 0xff9a40 });
  const prev = m.onBeforeCompile;
  m.onBeforeCompile = (sh, r) => {
    prev(sh, r);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec2 vKnit;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvKnit = uv;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
        varying vec2 vKnit;
        vec3 knitPerturb(vec3 sp, vec3 sn, vec2 dh, float fd) {
          vec3 sx = dFdx(sp), sy = dFdy(sp), r1 = cross(sy, sn), r2 = cross(sn, sx);
          float det = dot(sx, r1) * fd;
          return normalize(abs(det) * sn - sign(det) * (dh.x * r1 + dh.y * r2));
        }`)
      .replace('#include <map_fragment>', `#include <map_fragment>
        // uv unit ~ 4.4 cm along x / ~5.3 cm around y -> stitches ~1.1 cm long x ~0.75 cm wide (columns run along)
        vec2 kq = vec2(vKnit.x * 4.0, vKnit.y * 7.0);
        vec2 kc = fract(kq) - 0.5;
        float kRow = fract(kq.x + abs(kc.y) * 0.9);             // chevron rows: the 'V' legs of each stitch
        float kRidge = pow(sin(3.14159 * kRow), 0.7);
        float kCol = smoothstep(0.0, 0.2, abs(kc.y)) * (1.0 - 0.35 * smoothstep(0.38, 0.5, abs(kc.y)));
        float kH = kRidge * kCol;
        float kAA = clamp((0.6 - max(fwidth(kq.x), fwidth(kq.y))) / 0.3, 0.0, 1.0);   // fade below ~3 px per stitch
        diffuseColor.rgb *= mix(0.9, 0.79 + 0.25 * kH, kAA);`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        normal = knitPerturb(-vViewPosition, normal, vec2(dFdx(kH), dFdy(kH)) * 0.0025 * kAA, faceDirection);`);
  };
  const key = m.customProgramCacheKey.bind(m);
  m.customProgramCacheKey = () => key() + 'fearKnit';
  return m;
}
// add a constant (u along, v around) uv attribute to a core SweepTube, scaled by the repeat counts
function tubeUV(tube, repU, repV) {
  const rings = tube.rings, R = tube.R, nv = rings * R + 2;
  const uv = new Float32Array(nv * 2);
  for (let r = 0; r < rings; r++) for (let j = 0; j < R; j++) { const i = r * R + j; uv[i * 2] = (r / (rings - 1)) * repU; uv[i * 2 + 1] = (j / R) * repV; }
  uv[(nv - 2) * 2] = 0; uv[(nv - 2) * 2 + 1] = 0.5 * repV; uv[(nv - 1) * 2] = repU; uv[(nv - 1) * 2 + 1] = 0.5 * repV;
  tube.geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}
// per-vertex colour along a SweepTube (s = 0 root .. 1 tip): f(s) -> brightness (may exceed 1 for a glow)
function tubeColor(tube, f) {
  const { rings, R, C, S } = tube, nv = rings * R + 2;
  const col = new Float32Array(nv * 3);
  for (let r = 0; r < rings; r++) {
    const s = clamp((r - C) / S);
    const b = f(r >= rings - C ? 1 : s);
    for (let j = 0; j < R; j++) col.set([b, b, b], (r * R + j) * 3);
  }
  col.set([f(0), f(0), f(0)], (nv - 2) * 3); col.set([f(1), f(1), f(1)], (nv - 1) * 3);
  tube.geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
}

// ---------------------------------------------------------------------------------------------------------
// Combiner: copies many small rigidly-placed / swept parts that share ONE material into one dynamic mesh each frame
// (SwiftShader + MSAA HDR pays a lot per draw call; this turns ~55 draws into ~6). Sources keep their own
// geometry/pose logic (core SweepTube / Hand / meshes) and are simply not drawn themselves.
const _M = new THREE.Matrix4(), _N = new THREE.Matrix3();
function relMatrix(obj, anc, out) { out.identity(); for (let o = obj; o && o !== anc; o = o.parent) { o.updateMatrix(); out.premultiply(o.matrix); } return out; }
class Combiner {
  constructor(material, parent, { castShadow = false } = {}) { this.material = material; this.parent = parent; this.castShadow = castShadow; this.src = []; }
  /** obj: Mesh (its geometry is copied; pose = obj relative to the combiner's parent). rigid=false: positions already in parent space */
  add(obj, rigid = true) { obj.layers.disableAll(); this.src.push({ obj, geo: obj.geometry, rigid }); return this; }   // not drawn itself (children still are)
  build() {
    let nv = 0, ni = 0;
    for (const s of this.src) { s.v0 = nv; nv += s.geo.attributes.position.count; ni += s.geo.index.count; }
    const g = new THREE.BufferGeometry();
    this.pos = new Float32Array(nv * 3); this.nor = new Float32Array(nv * 3);
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('normal', new THREE.BufferAttribute(this.nor, 3).setUsage(THREE.DynamicDrawUsage));
    const uv = new Float32Array(nv * 2), col = new Float32Array(nv * 3).fill(1);
    const idx = nv > 65535 ? new Uint32Array(ni) : new Uint16Array(ni);
    let k = 0;
    for (const s of this.src) {
      const a = s.geo.attributes, ix = s.geo.index.array;
      for (let i = 0; i < ix.length; i++) idx[k++] = ix[i] + s.v0;
      if (a.uv) uv.set(a.uv.array.subarray(0, a.uv.count * 2), s.v0 * 2);
      if (a.color) col.set(a.color.array.subarray(0, a.color.count * 3), s.v0 * 3);
    }
    g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    if (this.material.vertexColors) g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setIndex(new THREE.BufferAttribute(idx, 1));
    this.geo = g;
    this.mesh = new THREE.Mesh(g, this.material);
    this.mesh.frustumCulled = false; this.mesh.castShadow = this.castShadow;
    this.parent.add(this.mesh);
    return this;
  }
  update() {
    const pos = this.pos, nor = this.nor;
    for (const s of this.src) {
      const P = s.geo.attributes.position.array, Nn = s.geo.attributes.normal.array, n = s.geo.attributes.position.count, o = s.v0 * 3;
      let vis = true; for (let q = s.obj; q && q !== this.parent; q = q.parent) if (q.userData.hide) { vis = false; break; }
      if (!vis) { pos.fill(0, o, o + n * 3); continue; }   // degenerate: draws nothing
      if (!s.rigid) { pos.set(P.subarray(0, n * 3), o); nor.set(Nn.subarray(0, n * 3), o); continue; }
      const e = relMatrix(s.obj, this.parent, _M).elements; _N.getNormalMatrix(_M); const m = _N.elements;
      for (let i = 0; i < n * 3; i += 3) {
        const x = P[i], y = P[i + 1], z = P[i + 2];
        pos[o + i] = e[0] * x + e[4] * y + e[8] * z + e[12]; pos[o + i + 1] = e[1] * x + e[5] * y + e[9] * z + e[13]; pos[o + i + 2] = e[2] * x + e[6] * y + e[10] * z + e[14];
        const a = Nn[i], b = Nn[i + 1], c = Nn[i + 2];
        let nx = m[0] * a + m[3] * b + m[6] * c, ny = m[1] * a + m[4] * b + m[7] * c, nz = m[2] * a + m[5] * b + m[8] * c;
        const l = 1 / (Math.hypot(nx, ny, nz) || 1); nor[o + i] = nx * l; nor[o + i + 1] = ny * l; nor[o + i + 2] = nz * l;
      }
    }
    this.geo.attributes.position.needsUpdate = true; this.geo.attributes.normal.needsUpdate = true;
  }
}

// ---------------------------------------------------------------------------------------------------------
export class Fear extends Character {
  constructor() {
    super({ name: 'FEAR', speaker: 'FEAR', height: 0.85, seed: 23 });
    // ---- materials
    this.U = { uBendQ: { value: new THREE.Vector4(0, 0, 0, 1) }, uBendPivot: { value: PIVOT.clone() }, uBendOff: { value: V3() }, uBendY: { value: new THREE.Vector2(...BEND_Y) } };
    const beingOpts = { roughness: 0.48, rim: 0.75, rimColor: C_RIM, rimPower: 2.6, glow: 0.09, glowColor: C_GLOW,
      fizz: 0.05, fizzColor: 0xeee4ff, fizzScale: 10, fizzSpeed: 0.22, wrap: 0.34, wrapColor: C_WRAP };
    this.bodyMat = bendMaterial(beingLite(C_BODY, beingOpts), this.U);
    this.lidMat = beingLite(C_BODY, { ...beingOpts, rim: 0.12, rimPower: 3.5, glow: 0.06, fizz: 0 });
    this.limbMat = beingLite(C_LIMB, { ...beingOpts, rim: 0.6, glow: 0.07, fizz: 0 });
    this.tuftMat = beingLite(C_TUFT, { ...beingOpts, rim: 1.0, rimPower: 1.8, glow: 0.2, fizz: 0, vertexColors: true });
    this.knitMat = knitMaterial();
    this.mats = [this.bodyMat, this.lidMat, this.limbMat, this.tuftMat];
    this.baseU = this.mats.map((m) => ({ rim: m.userData.uniforms.uRim.value, glow: m.userData.uniforms.uGlow.value, fizz: m.userData.uniforms.uFizz.value }));

    // ---- hierarchy
    this.bodyG = new THREE.Group(); this.root.add(this.bodyG);
    this.headPivot = new THREE.Group(); this.bodyG.add(this.headPivot);
    this.headGroup = new THREE.Group(); this.headPivot.add(this.headGroup);
    this.headGroup.position.copy(HEAD_C).sub(PIVOT);
    this._buildBody();
    this._buildFace();
    this._buildTuft();
    this._buildScarf();
    this._buildLimbs();
    this._buildTears();
    this._buildCombiners();

    // glow aura (wide shots only) + fizz motes + contact shadow
    this.aura = glowSprite(0xb9a0ff, 0.95, 0.1); this.aura.position.set(0, 0.28, -0.06); this.aura.renderOrder = -1; this.bodyG.add(this.aura);
    this.fx = new Particles({ max: 60, intensity: 1.4 }); this.root.add(this.fx.mesh);
    this.shadow = contactShadow(0.64, 0.52, 0.42); this.root.add(this.shadow);
    this._MBinv = new THREE.Matrix4();

    // ---- anchors
    const H = this.headGroup;
    this.addAnchor('head', H, [0, 0, 0]);
    const eL = headSurface(EYE.u, EYE.v).p, eR = headSurface(-EYE.u, EYE.v).p;
    this.addAnchor('eyes', H, [0, (eL.y + eR.y) / 2, (eL.z + eR.z) / 2 + 0.03]);
    this.addAnchor('eyeL', H, eL.toArray()); this.addAnchor('eyeR', H, eR.toArray());
    const mp = headSurface(0, MOUTH_V);
    this.addAnchor('mouth', H, mp.p.clone().addScaledVector(mp.n, 0.004).toArray());
    this.addAnchor('mouthOut', H, mp.p.clone().addScaledVector(mp.n, 0.3).toArray());
    const sL = headSurface(Math.PI / 2, -0.05).p, sR = headSurface(-Math.PI / 2, -0.05).p;
    this.addAnchor('earL', H, sL.toArray()); this.addAnchor('earR', H, sR.toArray());
    this.addAnchor('top', H, this.topP.toArray());
    for (const n of ['chest', 'back', 'belly', 'hip', 'scarf', 'tuft', 'tuftBase', 'shoulderL', 'shoulderR', 'footL', 'footR']) this.addAnchor(n, this.root);
    this.anchors = Object.keys(this._anch);
  }

  // ------------------------------------------------------------------------------------------------- build
  _buildCombiners() {
    const meshes = (o) => { const a = []; o.traverse((m) => { if (m.isMesh && m.visible) a.push(m); }); return a; };
    // limbs: arm tubes + hands + leg tubes + knees + feet -> one draw (root space)
    this.cLimbs = new Combiner(this.limbMat, this.root);
    for (const sd of ['L', 'R']) { const A = this.arms[sd]; this.cLimbs.add(A.tube.mesh, false); for (const m of meshes(A.hand.root)) this.cLimbs.add(m); }
    for (const sd of ['L', 'R']) { const G = this.legs[sd]; this.cLimbs.add(G.tube.mesh, false); this.cLimbs.add(G.knee); for (const m of meshes(G.foot)) this.cLimbs.add(m); }
    this.cLimbs.build();
    // scarf: wrap + knot + tails + fringes -> one draw (body space), the only shadow caster besides the body
    this.cScarf = new Combiner(this.knitMat, this.bodyG, { castShadow: true });
    this.cScarf.add(this.wrap.mesh, false).add(this.knot);
    for (const T of this.tails) { this.cScarf.add(T.tube.mesh, false); for (const m of meshes(T.fr)) this.cScarf.add(m); }
    this.cScarf.build();
    // tuft wisps (vertex-coloured glowing tips), brows, lids, lashes -> one draw each (head space)
    this.cTuft = new Combiner(this.tuftMat, this.headGroup); for (const S of this.tuft) this.cTuft.add(S.tube.mesh, false); this.cTuft.build();
    this.cBrows = new Combiner(this.face.brows[0].tube.mesh.material, this.headGroup); for (const b of this.face.brows) this.cBrows.add(b.tube.mesh, false); this.cBrows.build();
    this.cLids = new Combiner(this.lidMat, this.headGroup); for (const e of this.face.eyes) this.cLids.add(e.up).add(e.lo); this.cLids.build();
    this.lashMat = new THREE.MeshStandardMaterial({ color: C_LASH, roughness: 0.7 });
    this.cLash = new Combiner(this.lashMat, this.headGroup);
    for (const e of this.face.eyes) for (const lid of [e.up, e.lo]) for (const c of lid.children) if (c.isMesh && c.visible && c.geometry.type === 'TorusGeometry' && !c.userData.meniscus) this.cLash.add(c);
    this.cLash.build();
    this.combiners = [this.cLimbs, this.cScarf, this.cTuft, this.cBrows, this.cLids, this.cLash];
    // the face decal: no anisotropic filtering (it is seen nearly head-on)
    this.face.decal.tex.anisotropy = 1;
  }

  _buildBody() {
    const NA = 50, NV = 40, C = V3(0, 0.27, 0);
    const pos = [], nor = [], idx = [];
    this.surfPts = [];
    for (let j = 0; j <= NV; j++) {
      const ph = -Math.PI / 2 + (Math.PI * j) / NV;
      for (let i = 0; i <= NA; i++) {
        const th = (TAU * i) / NA;
        const d = V3(Math.sin(th) * Math.cos(ph), Math.sin(ph), Math.cos(th) * Math.cos(ph));
        const r = rayHit(C, d, 0.5);
        const p = C.clone().addScaledVector(d, r);
        const n = sdfGrad(p.x, p.y, p.z);
        pos.push(p.x, p.y, p.z); nor.push(n.x, n.y, n.z);
        if (i < NA && j > 2 && j < NV - 2 && (i + j) % 3 === 0) this.surfPts.push([p.x, p.y, p.z, n.x, n.y, n.z]);
      }
    }
    for (let j = 0; j < NV; j++) for (let i = 0; i < NA; i++) {
      const a = j * (NA + 1) + i, b = a + 1, c = a + NA + 1, d = c + 1;
      idx.push(a, b, c, b, d, c);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    g.setIndex(idx);
    g.computeBoundingSphere(); g.boundingSphere.radius += 0.2;
    this.body = new THREE.Mesh(g, this.bodyMat);
    this.body.castShadow = true; this.body.frustumCulled = false;
    this.bodyG.add(this.body);
  }

  _buildFace() {
    this.face = new Face({
      head: this.headGroup, surface: headSurface, seed: 29,
      eyes: { u: EYE.u, v: EYE.v, radius: EYE.r, sink: EYE.sink, splay: 0.2, lidMaterial: this.lidMat,
        iris: C_IRIS, iris2: C_IRIS2, irisR: 0.63, pupilR: 0.25, sclera: C_SCLERA, limbal: C_LIMBAL, pupilColor: 0x100820,
        lashColor: C_LASH, lash: 1.15, lowerLash: 0.3, catchlight: 1, lidGapU: 1.04, lidGapL: 1.035,
        upOpen: 0.55, upWide: 0.98, lowRelaxed: -0.64, lowRaised: -0.1, maxYaw: 0.62, maxPitch: 0.5 },
      brows: { color: C_BROW, thickness: 0.0062, lift: 0.003, inner: [0.12, 0.62], mid: [0.38, 0.65], outer: [0.66, 0.57], range: 0.12, flatten: 0.45,
        profile: [0.8, 1, 0.8, 0.4] },
      mouth: { v: MOUTH_V, halfW: HW0, line: '#4a2460', lineW: HW0 * 0.17, interior: '#2a1030', interior2: '#5a2148', tongue: '#d77a9e', teeth: '#f7f2ff',
        lipTintRGB: '200,120,190', blushColor: '255,130,190', blushX: 0.088, blushY: 0.04, drawExtra: (g, p) => this._drawCheeks(g, p) },
      decal: { uMin: -0.76, uMax: 0.76, vMin: -0.66, vMax: 0.0, size: [512, 352],
        material: new THREE.MeshLambertMaterial({ transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }) },
    });
    for (const eye of this.face.eyes) for (const c of eye.up.children) if (c.geometry && c.geometry.type === 'ConeGeometry') c.visible = false;
    // triangle budget (SwiftShader pays per triangle): the eyeball only needs its front cap (it rotates <= ~0.8 rad and
    // only ~0.85 rad around the front is outside the head); lids at a lower tessellation (the lash line hides the edge)
    for (const eye of this.face.eyes) {
      const r = EYE.r, cap = new THREE.SphereGeometry(r, 30, 13, 0, TAU, 0, 1.85); cap.rotateX(Math.PI / 2);
      eye.ball.geometry.dispose(); eye.ball.geometry = cap;
      const ru = r * 1.04, rl = r * 1.035;
      eye.up.geometry.dispose(); eye.up.geometry = new THREE.SphereGeometry(ru, 28, 10, 0, TAU, 0, Math.PI / 2);
      eye.lo.geometry.dispose(); eye.lo.geometry = new THREE.SphereGeometry(rl, 28, 9, 0, TAU, Math.PI / 2, Math.PI / 2);
    }
    // purity: core Face skips the decal redraw when its 3-decimal key is unchanged, so the canvas could keep a
    // previous frame's (slightly different) values. Draw from the rounded values = a pure function of the key.
    const DK = ['mOpen', 'mWide', 'mRound', 'mSmile', 'mAsym', 'mTeethU', 'mTeethL', 'mClench', 'mPress', 'mTongue', 'mPout', 'blush', 'tearL', 'tearR', 'close', 'mShift'];
    const draw = this.face._drawDecal.bind(this.face);
    this.face._drawDecal = (p, t) => { const q = { ...p }; for (const k2 of DK) q[k2] = +(q[k2] || 0).toFixed(3); for (const k2 of ['squeeze', 'squeezeL', 'squeezeR']) if (q[k2] != null) q[k2] = +(+q[k2]).toFixed(2); draw(q, t); };
    this.scleraLin = new THREE.Color(C_SCLERA);
    this._cheekKey = '';
    // tear meniscus along each lower lid (wet, welling eyes)
    this.menisci = this.face.eyes.map((eye) => {
      const rl = EYE.r * 1.04;
      const tg = new THREE.TorusGeometry(rl, 0.0026, 6, 24, 1.9);
      tg.rotateZ(Math.PI / 2 - 0.95); tg.rotateX(Math.PI / 2);
      const m = new THREE.Mesh(tg, new THREE.MeshStandardMaterial({ color: 0xeaf6ff, roughness: 0.05, metalness: 0, transparent: true, opacity: 0, emissive: 0x9fc4ff, emissiveIntensity: 0.35, depthWrite: false }));
      m.position.y = 0.0015; m.renderOrder = 3; m.userData.meniscus = true;
      eye.lo.add(m);
      return m;
    });
    // squeeze creases: the lower stroke of a '>' / '<' from the inner corner (rolls with the lower lid) and a short
    // lid-fold arc above the closed line. Static geometry, faded in with the squeeze amount.
    this.creases = this.face.eyes.map((eye) => {
      const sx = eye.sx;
      const dir = (az, el, rr) => V3(Math.sin(sx * az) * Math.cos(el), Math.sin(el), Math.cos(sx * az) * Math.cos(el)).multiplyScalar(EYE.r * rr);
      const mat = new THREE.MeshBasicMaterial({ color: C_LASH, transparent: true, opacity: 0, depthWrite: false });
      const mk = (pts, r0, r1) => {
        const tube = new SweepTube({ material: mat, segments: 12, radial: 6, capRings: 2 });
        tube.update(pts, (s) => lerp(r0, r1, s) * Math.sqrt(Math.sin(Math.PI * clamp(s * 0.9 + 0.05))), {});
        tube.mesh.renderOrder = 3;
        return tube.mesh;
      };
      const lower = mk([[-0.86, -0.02], [-0.45, -0.2], [-0.02, -0.4], [0.36, -0.56]].map(([a, e]) => dir(a, e, 1.06)), EYE.r * 0.06, EYE.r * 0.035);
      const upper = mk([[-0.1, 0.36], [0.2, 0.47], [0.5, 0.52]].map(([a, e]) => dir(a, e, 1.065)), EYE.r * 0.03, EYE.r * 0.04);
      const g = new THREE.Group(); g.add(lower, upper);
      eye.loRoll.add(g);
      g.visible = false;
      return { g, mat };
    });
  }

  _buildTuft() {
    const top = headSurface(0, Math.PI / 2 - 0.08);
    this.topP = top.p.clone();
    this.tuft = TUFT.map((s) => {
      const tube = new SweepTube({ material: this.tuftMat, segments: TUFT_SEG, radial: 6, capRings: 3 });
      tubeColor(tube, (u) => 1 + 1.3 * smoothstep(0.8, 0.97, u));   // glowing bulb tip
      this.headGroup.add(tube.mesh);
      const base = this.topP.clone().add(V3(...s.o)).addScaledVector(top.n, -0.006);
      const S = { ...s, tube, base, d0: V3(...s.d).normalize(), curv0: V3(...s.curv) };
      S.tip0 = this._strand(S, S.d0, S.curv0, S.L)[5];   // rest tip (head-local), for the spring look-back
      return S;
    });
  }
  _strand(S, d0, bend, L) {
    const pts = [S.base.clone()];
    for (let i = 0; i < 5; i++) {
      const s = (i + 0.5) / 5;
      const dir = d0.clone().addScaledVector(bend, Math.pow(s, 1.25) * 1.3).normalize();
      pts.push(pts[i].clone().addScaledVector(dir, L / 5));
    }
    return pts;
  }

  _buildScarf() {
    // wrap: 1.28 turns. Starts under the knot (front-left), goes round the back (sagging at the back-right), passes
    // the front, and the last quarter turn rides up over the first pass on Fear's left (an overlapping loop).
    this.wrap = new SweepTube({ material: this.knitMat, segments: 80, radial: 10, capRings: 2 });
    tubeUV(this.wrap, 40, 3.4); this.bodyG.add(this.wrap.mesh);   // ~1.75 m long, ~0.18 m round
    const KA = 0.62;                                  // knot angle (from +Z toward +X = its left)
    this.knotA = KA;
    const pts = [], ups = [];
    const N = 40, TURNS = 1.28, SAG = Math.PI + 0.65;
    for (let i = 0; i <= N; i++) {
      const s = i / N, th = KA + 0.12 + TAU * TURNS * s;
      const over = smoothstep(0.74, 0.96, s);
      const y = SCARF_Y - 0.007 + 0.024 * over - 0.016 * Math.max(0, Math.cos(th - SAG)) ** 2 + 0.006 * Math.cos(th - KA) + 0.003 * Math.sin(th * 3 + 1);
      const d = V3(Math.sin(th), 0, Math.cos(th));
      const r = rayHit(V3(0, y, 0), d, 0.4);
      const lump = 1 + 0.06 * Math.sin(th * 5 + 0.7) + 0.03 * Math.sin(th * 11);
      pts.push(V3(0, y, 0).addScaledVector(d, r + 0.02 * lump + 0.016 * over - 0.012 * smoothstep(0.96, 1, s)));
      ups.push(d.clone().negate());            // seam toward the body
    }
    this.wrapPts = pts; this.wrapUps = ups;
    this.wrapR = (s) => SCARF_R * (1 + 0.1 * Math.sin(s * TAU * 2.3 + 0.4) + 0.05 * Math.sin(s * 37.0) + 0.03 * Math.sin(s * 91.0 + 1.3))
      * (s < 0.04 ? 0.75 + 6.2 * s : 1) * (1 - 0.35 * smoothstep(0.93, 1, s));
    // knot (uv-scaled sphere, same knit material)
    const kd = V3(Math.sin(KA), 0, Math.cos(KA));
    const kr = rayHit(V3(0, SCARF_Y - 0.012, 0), kd, 0.4);
    this.knotP = V3(0, SCARF_Y - 0.014, 0).addScaledVector(kd, kr + 0.03);
    this.knotN = kd;
    const kg = new THREE.SphereGeometry(1, 14, 10);
    const kuv = kg.attributes.uv; for (let i = 0; i < kuv.count; i++) kuv.setXY(i, kuv.getX(i) * 6, kuv.getY(i) * 2.4);
    this.knot = new THREE.Mesh(kg, this.knitMat);
    this.knot.scale.set(0.042, 0.044, 0.031);
    this.bodyG.add(this.knot);
    // hanging ends with fringe: a long one down the tummy, a short one splayed out to its left side
    const fringeMat = new THREE.MeshStandardMaterial({ color: C_FRINGE, roughness: 0.9 });
    this.tails = [
      { L: 0.235, off: -0.016, w: 1.0, rad: 0.027, lat: V3(-0.25, 0, 0.05), spread: 0.35 },
      { L: 0.15, off: 0.02, w: 0.85, rad: 0.022, lat: V3(0.85, 0, -0.35), spread: 0.75 },
    ].map((T, i) => {
      const tube = new SweepTube({ material: this.knitMat, segments: 12, radial: 8, capRings: 2 });
      tubeUV(tube, T.L * 22.9, 2.3); this.bodyG.add(tube.mesh);
      const fr = new THREE.Group(); this.bodyG.add(fr);
      const parts = [];
      const nf = i ? 4 : 5;
      for (let k = 0; k < nf; k++) {
        const c = new THREE.CapsuleGeometry(0.0034, 0.026 + 0.008 * hash1(k * 7 + i), 1, 4);
        c.rotateZ((k - (nf - 1) / 2) * 0.07); c.translate((k - (nf - 1) / 2) * 0.0088 * (T.rad / 0.025), -0.016, 0);
        parts.push(c);
      }
      fr.add(new THREE.Mesh(mergeGeometries(parts), fringeMat));
      return { ...T, lat: T.lat.normalize(), tube, fr };
    });
  }

  _buildLimbs() {
    this.arms = {};
    for (const side of ['L', 'R']) {
      const hand = new Hand({ size: HAND, fingers: 3, side, material: this.limbMat, thick: 1.25, fingerLen: 1.05 });
      hand.root.traverse((m) => {   // the hand is a few cm on screen: re-tessellate its parts (core uses 10-20 segments)
        if (!m.isMesh) return;
        const g = m.geometry, pr = g.parameters;
        if (g.type === 'CapsuleGeometry') { m.geometry = new THREE.CapsuleGeometry(pr.radius, pr.length, 2, 6); g.dispose(); }
        else if (g.type === 'SphereGeometry') { m.geometry = new THREE.SphereGeometry(pr.radius, 12, 8); g.dispose(); }
      });
      const tube = new SweepTube({ material: this.limbMat, segments: 14, radial: 7, capRings: 3 });
      const group = new THREE.Group(); group.add(tube.mesh, hand.root);
      this.root.add(group);
      const palmL = HAND * 0.46, palmT = HAND * 0.16 * 1.25;
      this.addAnchor('hand' + side, hand.root, [0, palmL * 0.55, -palmT * 0.9]);
      this.arms[side] = { tube, hand, group, pts: null };
    }
    this.legs = {};
    for (const side of ['L', 'R']) {
      const tube = new SweepTube({ material: this.limbMat, segments: 10, radial: 7, capRings: 2 });
      this.root.add(tube.mesh);
      const knee = new THREE.Mesh(new THREE.SphereGeometry(0.0225, 10, 7), this.limbMat);
      this.root.add(knee);
      const foot = new THREE.Group(); this.root.add(foot);
      const fm = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 10), this.limbMat);
      fm.scale.set(0.04, 0.028, 0.056); fm.position.set(0, -0.006, 0.02);
      foot.add(fm);
      const ank = new THREE.Mesh(new THREE.SphereGeometry(0.0175, 8, 6), this.limbMat); foot.add(ank);
      this.legs[side] = { tube, knee, foot };
    }
  }

  _buildTears() {
    const mat = new THREE.MeshStandardMaterial({ color: 0xc4e2ff, roughness: 0.04, metalness: 0, transparent: true, opacity: 0.62, emissive: 0x7aa4ff,
      emissiveIntensity: 0.3, depthWrite: false });
    this.drops = [];
    for (let i = 0; i < 4; i++) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 10), mat);
      m.visible = false; m.renderOrder = 4;
      this.headGroup.add(m);
      this.drops.push(m);
    }
  }

  // ------------------------------------------------------------------------------------------------- solve
  /** Body-level kinematics for pose P at time t (pure: no scene-graph writes). */
  _solve(t, P) {
    const B = P.body || {}, W = P.walk || {}, Hd = P.head || {}, E = P.extra || {};
    const sd = this.seed;
    const tremble = clamp(E.tremble ?? 0), startle = clamp(E.startle ?? 0), sob = clamp(E.sob ?? 0);
    const sit = clamp(B.sit ?? 0), kneel = clamp(B.kneel ?? 0), cower = clamp(B.cower ?? 0);
    const shrug0 = clamp(B.shrug ?? 0), slump = clamp(B.slump ?? 0), recoil = B.recoil ?? 0;
    const wa = clamp(W.amount ?? 0), ph = W.phase ?? 0, st = WALK[W.style] || WALK.walk;
    const s1 = Math.sin(ph * TAU), c1 = Math.cos(ph * TAU), c2 = Math.cos(ph * 2 * TAU);
    const br = Math.sin(t * (B.breathRate ?? 0.32) * TAU + sd) * (B.breathe ?? 1) * (1 + 0.8 * tremble);
    const sobP = sob > 0 ? sob * Math.pow(Math.max(0, Math.sin(t * TAU * 1.3 + 0.7 * Math.sin(t * 1.9))), 5) : 0;
    const crouch = clamp((B.crouch ?? 0) + cower * 0.7 + wa * st.crouch);
    const hunch = clamp((B.hunch ?? 0) + cower * 0.55 + slump * 0.5);
    const shrug = clamp(shrug0 + cower * 0.6 + sobP * 0.7 + startle * 0.3);
    const ks = smooth(kneel), ss = smooth(sit);
    // wiping an eye: the head tilts into the hand
    let wipeRoll = 0, wipeW = 0;
    for (const [sx, A] of [[1, P.armL], [-1, P.armR]]) if (A && A.preset === 'wipe') { const w = clamp(A.mix ?? 1) * clamp(A.reach ?? 1); wipeRoll += -sx * 0.16 * w; wipeW = Math.max(wipeW, w); }
    // pelvis (root space)
    const pel = V3(0, PELVIS_Y - 0.082 * crouch, -0.012 * crouch);
    pel.lerp(V3(0, KNEEL_Y, -0.02), ks);
    pel.lerp(V3(0, SIT_Y, -0.03), ss);
    pel.y += wa * (-st.bob * c2 + (st.flight || 0) * Math.max(0, -c2)) + (B.bounce ?? 0) + startle * 0.03 + sobP * 0.008;
    pel.x += wa * st.sway * s1;
    pel.z += -recoil * 0.035;
    if (tremble > 0) { pel.x += tremble * 0.003 * noise1(t * 21, sd + 1); pel.y += tremble * 0.0018 * noise1(t * 23, sd + 2); pel.z += tremble * 0.0022 * noise1(t * 19, sd + 3); }
    // body rotation
    const idle = (B.idle ?? 1);
    let lean = (B.lean ?? 0) + wa * st.lean + 0.11 * crouch - 0.1 * ss + 0.05 * ks + 0.13 * hunch - recoil * 0.2 + 0.012 * idle * fbm1(t * 0.31, sd + 4) + sobP * 0.04;
    let tilt = (B.tilt ?? 0) + wa * st.roll * s1 + 0.014 * idle * fbm1(t * 0.27, sd + 5);
    let twist = (B.twist ?? 0) + wa * st.twist * c1 + 0.012 * idle * fbm1(t * 0.23, sd + 6);
    if (tremble > 0) { lean += tremble * 0.011 * noise1(t * 17, sd + 7); tilt += tremble * 0.013 * noise1(t * 18.5, sd + 8); }
    const bodyQ = new THREE.Quaternion().setFromEuler(_e.set(lean, twist, -tilt, 'YXZ'));
    // squash & stretch (+ squash, - stretch) about the pelvis
    const sq = (B.squash ?? 0) + 0.05 * crouch + 0.05 * cower + 0.03 * shrug - 0.08 * startle + 0.03 * sobP - (B.stretch ?? 0)
      + wa * 0.02 * Math.max(0, c2) * (st === WALK.run ? 1.5 : 0.6);
    const bodyS = V3(1 + 0.55 * sq + 0.004 * br, 1 - sq + 0.009 * br, 1 + 0.55 * sq + 0.004 * br);
    // head
    let hy = Hd.yaw ?? 0, hp = Hd.pitch ?? 0, hr = Hd.roll ?? 0;
    hp += 0.2 * hunch + 0.1 * slump - 0.06 * startle - 0.05 * recoil + 0.018 * idle * fbm1(t * 0.37, sd + 9) + sobP * 0.06 - wa * st.lean * 0.4 + 0.07 * wipeW;
    hy += 0.024 * idle * fbm1(t * 0.29, sd + 10);
    hr += -0.5 * wa * st.roll * s1 + 0.018 * idle * fbm1(t * 0.21, sd + 11) + wipeRoll;
    if (tremble > 0) { hp += tremble * 0.008 * noise1(t * 20, sd + 12); hy += tremble * 0.01 * noise1(t * 22, sd + 13); }
    const pos = P.pos || [0, 0, 0], yaw = P.yaw || 0;
    if (Hd.look) {   // turn the head toward a world point (weight head.track, default 1)
      const tg = gazePoint(Hd.look, CTX.camera);
      if (tg) {
        const w = Hd.track ?? 1;
        const lr = tg.sub(V3(pos[0], pos[1] ?? 0, pos[2] ?? 0)).applyAxisAngle(V3(0, 1, 0), -yaw).sub(pel);
        lr.applyQuaternion(bodyQ.clone().invert()).divide(bodyS).sub(HEAD_C);
        hy += w * Math.atan2(lr.x, Math.max(0.02, lr.z));
        hp += w * -Math.atan2(lr.y, Math.hypot(lr.x, lr.z));
      }
    }
    hy = clamp(hy, -1.35, 1.35); hp = clamp(hp, -0.8, 0.6); hr = clamp(hr, -0.55, 0.55);
    const headQ = new THREE.Quaternion().setFromEuler(_e.set(hp, hy, hr, 'YXZ'));
    if (headQ.w < 0) { headQ.x *= -1; headQ.y *= -1; headQ.z *= -1; headQ.w *= -1; }
    const scarfSlide = 0.011 * shrug + 0.004 * hunch;         // the sinking head pushes the scarf down a little
    const headOff = V3(0, -0.034 * shrug - 0.012 * hunch + (Hd.up ?? 0), 0.014 * hunch + (Hd.forward ?? 0));
    // never let the mouth sink behind the scarf: keep the mouth line >= MOUTH_CLEAR above the wrap's top
    const mY = _v.copy(MOUTH_P).add(HEAD_C).sub(PIVOT).applyQuaternion(headQ).y + PIVOT.y + headOff.y;
    const need = SCARF_TOP - scarfSlide + MOUTH_CLEAR - mY;
    headOff.y += smax0(need, 0.008);
    return { pos, yaw, pel, bodyQ, bodyS, headQ, headOff, crouch, hunch, shrug, scarfSlide, sit, kneel, cower, tremble, startle, sob, sobP, wa, ph, st, s1, c1, br, recoil };
  }
  // body space -> head-bent body space (CPU copy of the vertex-shader bend)
  _bend(K, p, out = V3(), k = 1) {
    const w = smoothstep(BEND_Y[0], BEND_Y[1], p.y) * k;
    _q.slerpQuaternions(QI, K.headQ, w);
    return out.copy(p).sub(PIVOT).applyQuaternion(_q).add(PIVOT).addScaledVector(K.headOff, w);
  }
  _unbend(K, p, out = V3()) {   // approximate inverse of _bend (weight taken at the bent point)
    const w = smoothstep(BEND_Y[0], BEND_Y[1], p.y);
    _q.slerpQuaternions(QI, K.headQ, w).invert();
    return out.copy(p).addScaledVector(K.headOff, -w).sub(PIVOT).applyQuaternion(_q).add(PIVOT);
  }
  _bodyToWorld(K, p, out = V3()) {
    out.copy(p).multiply(K.bodyS).applyQuaternion(K.bodyQ).add(K.pel).applyAxisAngle(_v.set(0, 1, 0), K.yaw);
    return out.add(_v.set(K.pos[0], K.pos[1] ?? 0, K.pos[2] ?? 0));
  }
  _headToBody(K, p, out = V3()) { return out.copy(p).add(HEAD_C).sub(PIVOT).applyQuaternion(K.headQ).add(PIVOT).add(K.headOff); }
  _extrapolate(P, tau) {   // fallback past pose: constant velocity + walk phase advancing at its cadence
    const Q = { ...P };
    if (P.vel && P.pos) Q.pos = [P.pos[0] - P.vel[0] * tau, (P.pos[1] ?? 0) - (P.vel[1] ?? 0) * tau, (P.pos[2] ?? 0) - (P.vel[2] ?? 0) * tau];
    if (P.walk && (P.walk.amount ?? 0) > 0) { const st = WALK[P.walk.style] || WALK.walk; Q.walk = { ...P.walk, phase: (P.walk.phase ?? 0) - tau * (P.walk.rate ?? st.cad) }; }
    return Q;
  }
  /**
   * Spring responses (world-space relative displacement) of each tuft wisp tip and of the scarf knot.
   * y(t) = -Σ K(t - g_i) (x(g_i) - x(t)) Δ over ABSOLUTE grid times g_i = floor(t/Δ)Δ - iΔ: the pose is sampled at
   * fixed instants (so a fast head snap is seen identically by every frame) and only the kernel weights slide.
   */
  _secondary(t, P, K0, poseAt) {
    const tips = this.tuft.map((S) => S.tip0);
    const x0 = tips.map((p) => this._bodyToWorld(K0, this._headToBody(K0, p)));
    const k0 = this._bodyToWorld(K0, this._bend(K0, this.knotP, V3(), SCARF_FOLLOW));
    const yT = tips.map(() => V3()), yS = V3(), a = V3(), b = V3();
    const g0 = Math.floor(t / SPRING_DT) * SPRING_DT;
    for (let i = 0; i < SPRING_N; i++) {
      const tg = g0 - i * SPRING_DT, tau = t - tg;
      if (tau < 1e-5) continue;            // x(g) - x(t) = 0
      let Pp;
      try { Pp = poseAt ? (poseAt(tg) || {}) : this._extrapolate(P, tau); } catch (e) { Pp = this._extrapolate(P, tau); }
      const K = this._solve(tg, Pp);
      const wT = springK(tau, 2.4, 0.24) * SPRING_DT, wS = springK(tau, 1.5, 0.32) * SPRING_DT;
      for (let k = 0; k < tips.length; k++) {
        this._bodyToWorld(K, this._headToBody(K, tips[k], a), a).sub(x0[k]);
        yT[k].addScaledVector(a, -wT);
      }
      this._bodyToWorld(K, this._bend(K, this.knotP, b, SCARF_FOLLOW), b).sub(k0);
      yS.addScaledVector(b, -wS);
    }
    return { tuft: yT, tail: yS };
  }

  // ------------------------------------------------------------------------------------------------- update
  update(t, pose = {}) {
    let P, poseAt = null;
    if (typeof pose === 'function') { poseAt = pose; P = pose(t) || {}; } else { P = pose || {}; poseAt = P.poseAt || null; }
    const E = P.extra || {};
    const K = this._solve(t, P);
    this.place(K.pos, K.yaw);
    this.bodyG.position.copy(K.pel); this.bodyG.quaternion.copy(K.bodyQ); this.bodyG.scale.copy(K.bodyS);
    this.headPivot.position.copy(PIVOT).add(K.headOff); this.headPivot.quaternion.copy(K.headQ);
    this.root.updateMatrixWorld(true);
    this.U.uBendQ.value.set(K.headQ.x, K.headQ.y, K.headQ.z, K.headQ.w);
    this.U.uBendOff.value.copy(K.headOff);
    this._K = K;
    this._MBinv.copy(this.bodyG.matrix).invert();
    const sec = this._secondary(t, P, K, poseAt);

    // ---- face
    let fp = typeof P.face === 'string' ? FX(P.face) : { ...FACE_DEFAULTS, ...FEAR_BASE, ...(P.face || {}) };
    fp = { ...fp };
    const cry = clamp(E.cry ?? 0);
    if (cry > 0) {
      fp.wet = Math.max(fp.wet, cry);
      fp.tearL = Math.max(fp.tearL, cry * (0.75 + 0.2 * Math.sin(t * 1.7)));
      fp.tearR = Math.max(fp.tearR, cry * (0.7 + 0.2 * Math.sin(t * 1.3 + 2)));
      fp.mTremble = Math.max(fp.mTremble, cry * 0.4);
    }
    if (K.tremble > 0) fp.mTremble = Math.max(fp.mTremble, K.tremble * 0.45);
    if (K.startle > 0) { fp.lidU = lerp(fp.lidU, Math.max(fp.lidU, 1.4), K.startle); fp.pupil = lerp(fp.pupil, Math.min(fp.pupil, 0.6), K.startle); }
    if (K.sobP > 0) { fp.mOpen = Math.max(fp.mOpen, fp.mOpen + K.sobP * 0.25); fp.lidU *= 1 - 0.25 * K.sobP; }
    // wiping an eye squeezes it shut
    for (const [side, A] of [['L', P.armL], ['R', P.armR]]) {
      if (A && A.preset === 'wipe') {
        const w = clamp(A.mix ?? 1) * clamp(A.reach ?? 1) * clamp(A.squeeze ?? 1);
        fp['lidU' + side] = lerp(fp['lidU' + side] ?? fp.lidU, 0.04, w); fp['lidL' + side] = lerp(fp['lidL' + side] ?? fp.lidL, 0.9, w);
        fp['squeeze' + side] = Math.max(fp['squeeze' + side] ?? fp.squeeze ?? 0, 0.85 * w);
      }
    }
    // fully shut lids (lidU < ~0.2) are closed like a blink, per side, in _eyes() (so they stay shut when the gaze pitches)
    this._shut = ['L', 'R'].map((sd) => smooth((0.22 - (fp['lidU' + sd] ?? fp.lidU)) / 0.22));
    const sqL = clamp(fp.squeezeL ?? fp.squeeze ?? 0), sqR = clamp(fp.squeezeR ?? fp.squeeze ?? 0);
    const ck = sqL.toFixed(2) + sqR.toFixed(2) + (fp.blush || 0).toFixed(3);
    if (ck !== this._cheekKey) { this._cheekKey = ck; this.face._lastKey = ''; }   // force a decal redraw (cheek lines)
    // squeeze flattens the eye BEFORE Face places the catchlights (they read the eye's world matrix): stays pure
    this.face.eyes.forEach((eye) => { const sq = smooth(eye.sx > 0 ? sqL : sqR); eye.inner.scale.set(1 - 0.05 * sq, 1 - 0.12 * sq, 1 - 0.19 * sq); });
    const gaze = gazePoint(P.gaze, CTX.camera);
    this.face.update(t, fp, { gaze, speech: this.speech(t, P), blinkAt: P.blinkAt });
    this._eyes(fp, sqL, sqR);
    const men = clamp(cry * 1.3 + fp.wet * 0.25 + (fp.tearL + fp.tearR) * 0.2);
    this.menisci.forEach((m) => { m.material.opacity = 0.85 * men; m.visible = men > 0.02; });
    this._tears(t, cry, E);

    // ---- tuft
    this._tuft(t, K, E, sec.tuft);

    // ---- limbs, then the scarf (its ends collide with the arms)
    this._legs(t, K, P);
    const MB = this.bodyG.matrix, MH = new THREE.Matrix4().multiplyMatrices(MB, this.headPivot.matrix).multiply(this.headGroup.matrix);
    const qH = K.bodyQ.clone().multiply(K.headQ);
    const ctx = { MB, MH, qB: K.bodyQ, qH };
    this._arm('L', P.armL || {}, K, t, ctx, P);
    this._arm('R', P.armR || {}, K, t, ctx, P);
    this._scarf(t, K, sec.tail);

    // ---- glow / fizz / aura (the aura only in wide shots: it is a big additive sprite)
    const gl = E.glow ?? 1, fz = E.fizz ?? 1;
    this.mats.forEach((m, i) => { const u = m.userData.uniforms; u.uRim.value = this.baseU[i].rim * gl; u.uGlow.value = this.baseU[i].glow * (0.6 + 0.4 * gl); u.uFizz.value = this.baseU[i].fizz * fz; });
    let auraK = 1;
    if (CTX.camera) { this.aura.getWorldPosition(_v); auraK = smoothstep(2.3, 3.2, CTX.camera.position.distanceTo(_v)); }
    this.aura.material.opacity = 0.1 * gl * (E.aura ?? 1) * auraK;
    this.aura.visible = this.aura.material.opacity > 0.004;

    // ---- anchors (root space)
    const an = (n, v) => this._anch[n].position.copy(v);
    const bp = (x, y, z) => V3(x, y, z).applyMatrix4(MB);
    an('chest', bp(0, 0.17, 0.235)); an('back', bp(0, 0.17, -0.225)); an('belly', bp(0, 0.06, 0.24)); an('hip', bp(0, 0, 0));
    an('scarf', this._bend(K, this.knotP, V3(), SCARF_FOLLOW).add(V3(0, -K.scarfSlide, 0)).applyMatrix4(MB));
    an('shoulderL', bp(SHOULDER.x, SHOULDER.y + 0.02 * K.shrug, SHOULDER.z)); an('shoulderR', bp(-SHOULDER.x, SHOULDER.y + 0.02 * K.shrug, SHOULDER.z));
    an('tuft', this._tuftTip.clone().applyMatrix4(MH)); an('tuftBase', this.tuft[0].base.clone().applyMatrix4(MH));
    an('footL', this._feet.L); an('footR', this._feet.R);

    // ---- copy the parts into their combined meshes
    this.root.updateMatrixWorld(true);
    for (const c of this.combiners) c.update();

    // ---- shadow & motes
    this.shadow.position.set(K.pel.x, 0.004, K.pel.z + 0.02);
    this.shadow.scale.set(1 + 0.25 * K.sit + 0.1 * K.crouch, 1, 1 + 0.3 * K.sit);
    this._motes(t, E, MB);
  }

  // ------------------------------------------------------------------------------------------------- parts
  /** Eye post-pass: squeeze (flatten + matched lid roll + creases), and keep the sclera below the bloom threshold. */
  _eyes(fp, sqL, sqR) {
    const a = EYE_LIGHT.uAmbient.value, k = EYE_LIGHT.uKeyColor.value;
    const Lmax = Math.max(a.r + k.r, a.g + k.g, a.b + k.b, 1e-3);
    const sMax = Math.max(this.scleraLin.r, this.scleraLin.g, this.scleraLin.b);
    const f = Math.min(1, 0.8 / (Lmax * sMax));
    this.face.eyes.forEach((eye, i) => {
      eye.mat.uniforms.uSclera.value.copy(this.scleraLin).multiplyScalar(f);
      const sq = smooth(eye.sx > 0 ? sqL : sqR), shut = this._shut[i];
      let up = -eye.up.rotation.x, low = -eye.lo.rotation.x;
      if (shut > 0) {   // same closing as Face's blink, for one side
        const lo2 = lerp(low, low + 0.06, shut);
        up = Math.max(lerp(up, low + 0.03, shut), lo2 + 0.02); low = lo2;
        eye.up.rotation.x = -up; eye.lo.rotation.x = -low;
        if (shut > 0.5) { eye.catch1.visible = false; eye.catch2.visible = false; }
      }
      const closed = smooth(1 - (up - low - 0.02) / 0.25);
      // closed lids share one roll (no sclera sliver at the corners); squeezing adds the '><' slant
      const roll = lerp(eye.upRoll.rotation.z, eye.upRoll.rotation.z * 0.5, closed) + eye.sx * 0.26 * sq * closed;
      eye.upRoll.rotation.z = roll;
      eye.loRoll.rotation.z = lerp(eye.loRoll.rotation.z, roll, closed);
      const C = this.creases[i];
      const o = smoothstep(0.15, 0.8, sq) * closed;
      C.g.visible = o > 0.02; C.mat.opacity = 0.92 * o;
    });
  }

  /** Decal extras: cheek push lines + highlight under squeezed eyes (drawn in the decal's metre space). */
  _drawCheeks(g, p) {
    const d = this.face.decal;
    if (p.blush > 0.05) {   // a second, rounder blush (the core one is faint at phone size)
      for (const sx of [1, -1]) {
        const cx = sx * 0.09, cy = 0.042, gr = g.createRadialGradient(cx, cy, 0, cx, cy, 0.034);
        gr.addColorStop(0, `rgba(255,112,176,${0.42 * clamp(p.blush)})`); gr.addColorStop(1, 'rgba(255,112,176,0)');
        g.fillStyle = gr; g.beginPath(); g.ellipse(cx, cy, 0.036, 0.024, 0, 0, TAU); g.fill();
      }
    }
    for (const [sx, side] of [[1, 'L'], [-1, 'R']]) {
      const s = clamp(p['squeeze' + side] ?? p.squeeze ?? 0);
      if (s < 0.03) continue;
      const ex = sx * d.eyeX * 1.02, ey = d.eyeY - EYE.r * 0.86;
      g.lineCap = 'round';
      const hl = g.createRadialGradient(ex, ey - 0.012, 0, ex, ey - 0.012, 0.04);
      hl.addColorStop(0, `rgba(255,236,255,${0.28 * s})`); hl.addColorStop(1, 'rgba(255,236,255,0)');
      g.fillStyle = hl; g.beginPath(); g.ellipse(ex, ey - 0.012, 0.045, 0.026, 0, 0, TAU); g.fill();
      g.strokeStyle = `rgba(86,52,140,${0.6 * s})`; g.lineWidth = 0.0042;
      g.beginPath(); g.moveTo(ex - sx * 0.032, ey + 0.002); g.quadraticCurveTo(ex + sx * 0.004, ey - 0.014, ex + sx * 0.04, ey + 0.01); g.stroke();
    }
  }

  _tuft(t, K, E, yWorld) {
    // world displacement -> head-local
    const qInv = new THREE.Quaternion().setFromAxisAngle(V3(0, 1, 0), K.yaw).multiply(K.bodyQ).multiply(K.headQ).invert();
    const perk = clamp((E.tuftPerk ?? 0) + K.startle * 0.9), droop = clamp(E.tuftDroop ?? 0), tr = K.tremble;
    const sd = this.seed, gain = 16 * (E.tuftWobble ?? 1);
    this.tuft.forEach((S, k) => {
      const yl = yWorld[k].clone().applyQuaternion(qInv);
      const dyn = V3(softClamp(yl.x * gain, 1.4), 0, softClamp(yl.z * gain, 1.4));
      const L = S.L * (1 + 0.1 * perk - 0.06 * droop) * (1 - 0.12 * softClamp(Math.max(0, yl.y * 8), 1));
      const d0 = S.d0.clone();
      d0.x *= 1 - 0.5 * perk; d0.z *= 1 - 0.5 * perk; d0.normalize();
      const curv = S.curv0.clone().multiplyScalar(1 - 0.8 * perk);
      curv.add(V3(Math.sign(S.d0.x || 0.01) * 0.9 * droop, -0.75 * droop, -0.35 * droop));
      // slow idle drift + (when scared) a soft ~10 Hz quiver; the body shake reaches the tips through the spring
      const wob = V3(0.07 * fbm1(t * 0.6, sd + 20 + k), 0, 0.06 * fbm1(t * 0.55, sd + 30 + k));
      if (tr > 0) wob.add(V3(tr * 0.08 * noise1(t * 10 + k * 3.1, sd + 40), 0, tr * 0.07 * noise1(t * 9 + k * 2.7, sd + 50)));
      const pts = this._strand(S, d0, curv.add(wob).add(dyn), L);
      S.tube.update(pts, (s) => tuftRad(s) * S.r * (1 + 0.08 * perk), {});
      if (k === 0) this._tuftTip = pts[5].clone();
    });
  }

  _scarf(t, K, yWorld) {
    // wrap follows part of the bend (CPU copy of the shader bend, so it hugs the bent bean) and slips down when the
    // head sinks into it
    const SK = SCARF_FOLLOW, slide = K.scarfSlide;
    const pts = this.wrapPts.map((p) => this._bend(K, p, V3(), SK).add(V3(0, -slide, 0)));
    const ups = this.wrapUps.map((u, i) => { _q.slerpQuaternions(QI, K.headQ, SK * smoothstep(BEND_Y[0], BEND_Y[1], this.wrapPts[i].y)); return u.clone().applyQuaternion(_q); });
    this.wrap.update(pts, this.wrapR, { up: (s) => ups[Math.min(ups.length - 1, Math.round(s * (ups.length - 1)))], flatten: 0.42 });
    // knot
    const kp = this._bend(K, this.knotP, V3(), SK).add(V3(0, -slide, 0));
    const wk = SK * smoothstep(BEND_Y[0], BEND_Y[1], this.knotP.y);
    _q.slerpQuaternions(QI, K.headQ, wk);
    this.knot.position.copy(kp);
    orientYZ(this.knot, V3(0, 1, 0).applyQuaternion(_q), this.knotN.clone().applyQuaternion(_q));
    // arm segments in body space (the tails are pushed off the forearms)
    const segs = [];
    for (const s of ['L', 'R']) {
      const ap = this.arms[s].pts; if (!ap) continue;
      const bpts = ap.map((p) => p.clone().applyMatrix4(this._MBinv));
      for (let i = 1; i < bpts.length - 1; i++) segs.push([bpts[i], bpts[i + 1]]);
      segs.push([bpts[bpts.length - 1], ap[ap.length - 1].clone().addScaledVector(this.arms[s].fd, HAND * 0.55).applyMatrix4(this._MBinv)]);
    }
    // tails: hang from under the knot, drape over the belly, swing with the spring response
    const qInv = new THREE.Quaternion().setFromAxisAngle(V3(0, 1, 0), K.yaw).multiply(K.bodyQ).invert();
    const yl = yWorld.clone().applyQuaternion(qInv);
    const down = V3(0, -1, 0).applyQuaternion(K.bodyQ.clone().invert());   // gravity in body space
    const swing = V3(softClamp(yl.x * 1.1, 0.07), 0, softClamp(yl.z * 1.1, 0.07));
    const side = V3(Math.cos(this.knotA), 0, -Math.sin(this.knotA));
    const tw = K.tremble * 0.004;
    const c = V3(), dd = V3();
    this.tails.forEach((T, i) => {
      const n = 6, pts2 = [], ups2 = [];
      const start = kp.clone().addScaledVector(side, T.off).add(V3(0, -0.014, 0));
      pts2.push(start);
      for (let k2 = 1; k2 <= n; k2++) {
        const s = k2 / n;
        const prev = pts2[k2 - 1];
        const p = prev.clone().addScaledVector(down, T.L / n).addScaledVector(this.knotN, 0.007 * (1 - s));
        p.addScaledVector(T.lat, (T.L / n) * T.spread * (1 - 0.6 * s));
        p.addScaledVector(swing, Math.pow(s, 1.4) * T.w / n * 2.2);
        if (tw > 0) p.add(V3(tw * noise1(t * 19 + i, 70 + k2), 0, tw * noise1(t * 17 + i, 80 + k2)));
        p.x += 0.006 * fbm1(t * 0.5 + i, 90) * s;
        // keep off the forearms, then outside the bean (+ tail half thickness)
        for (const [a, b] of segs) {
          dd.copy(b).sub(a); const L2 = dd.lengthSq();
          const u = L2 > 1e-9 ? clamp(_v.copy(p).sub(a).dot(dd) / L2) : 0;
          c.copy(a).addScaledVector(dd, u);
          const dist = p.distanceTo(c), minD = ARM_R[1] + T.rad * 0.5 + 0.006;
          if (dist < minD) { _v.copy(p).sub(c); if (_v.lengthSq() < 1e-10) _v.set(0, 0, 1); p.addScaledVector(_v.normalize(), minD - dist); }
        }
        for (let it = 0; it < 2; it++) {
          const d = bodySDF(p.x, p.y, p.z) - T.rad * 0.55;
          if (d < 0) { sdfGrad(p.x, p.y, p.z, _g); p.addScaledVector(_g, -d); }
        }
        const seg = p.clone().sub(prev); p.copy(prev).addScaledVector(seg.normalize(), T.L / n);
        pts2.push(p);
      }
      for (const p of pts2) ups2.push(sdfGrad(p.x, p.y, p.z).negate());
      T.tube.update(pts2, (s) => T.rad * (1 + 0.05 * Math.sin(s * 30 + i)) * (s > 0.92 ? 0.85 : 1), { up: (s) => ups2[Math.min(n, Math.round(s * n))], flatten: 0.78 });
      const end = pts2[n], tan = end.clone().sub(pts2[n - 1]).normalize();
      T.fr.position.copy(end);
      orientYZ(T.fr, tan.clone().negate(), ups2[n].clone().negate());
    });
  }

  _tears(t, cry, E) {
    const on = cry > 0.05;
    let di = 0;
    if (on) {
      const period = lerp(2.6, 1.25, cry);
      for (const sx of [1, -1]) for (let j = 0; j < 2; j++) {
        const m = this.drops[di++];
        const off = j * 0.5 + (sx > 0 ? 0 : 0.27);
        const cyc = t / period + off, n = Math.floor(cyc), u = cyc - n;
        const go = hash1(n * 13 + (sx > 0 ? 3 : 7) + j * 101) < 0.35 + 0.75 * cry;
        if (!go) { m.visible = false; continue; }
        const swell = smooth(u / 0.3), slide = smooth((u - 0.3) / 0.62);
        const uu = sx * (EYE.u + 0.07 + 0.1 * slide), vv = lerp(EYE.v - 0.34, -0.6, slide);
        const s = headSurface(uu, vv);
        const fade = 1 - smooth((u - 0.86) / 0.12);
        const r = 0.0076 * (0.35 + 0.65 * swell) * (0.8 + 0.4 * cry) * (0.3 + 0.7 * fade);
        m.position.copy(s.p).addScaledVector(s.n, r * 0.45);
        const tdir = headSurface(uu + sx * 0.02, vv + 0.04).p.sub(s.p).normalize();   // up along the path
        orientYZ(m, tdir, s.n);
        m.scale.set(r * 0.85, r * (1.1 + 0.45 * slide), r * 0.62);
        m.visible = fade > 0.02;
      }
    }
    for (; di < this.drops.length; di++) this.drops[di].visible = false;
  }

  _legs(t, K, P) {
    const W = P.walk || {}, B = P.body || {};
    const wa = K.wa, st = K.st, MB = this.bodyG.matrix;
    this._feet = {};
    const tiptoe = clamp((B.tiptoe ?? 0) + wa * st.tiptoe);
    for (const side of ['L', 'R']) {
      const s = side === 'L' ? 1 : -1;
      const hip = V3(s * HIP.x, HIP.y, HIP.z).applyMatrix4(MB);
      let ank = V3(s * 0.08, ANKLE_Y, 0.008), pitch = 0, yawF = s * 0.14;
      const pole = V3(s * 0.3, 0, 1);
      if (wa > 0) {
        const a = fract(K.ph + (s > 0 ? 0 : 0.5));
        const c = footCycle(a, st);
        const wk = V3(s * 0.074, ANKLE_Y + c.lift * st.lift, c.z * st.stride + 0.01);
        ank.lerp(wk, wa); pitch = lerp(pitch, c.pitch, wa); yawF = lerp(yawF, s * 0.06, wa);
      }
      // crouch: knees out, feet a little wider
      ank.x += s * 0.012 * K.crouch; pole.lerp(V3(s * 0.9, 0, 1), K.crouch * 0.6);
      if (tiptoe > 0 && ank.y < ANKLE_Y + 0.01) { const tp = 0.7 * tiptoe; pitch = Math.max(pitch, tp); }
      if (pitch > 0) { ank.y += 0.032 * Math.sin(pitch); ank.z -= 0.012 * (1 - Math.cos(pitch)); }
      // kneel: knees on the floor, feet tucked behind (soles up)
      const ks = smooth(K.kneel);
      if (ks > 0) { ank.lerp(V3(s * 0.07, 0.03, -0.115), ks); pitch = lerp(pitch, 1.45, ks); pole.lerp(V3(s * 0.15, -0.3, 1), ks); }
      // sit: legs stuck out in front, toes up
      const ss = smooth(K.sit);
      if (ss > 0) { ank.lerp(V3(s * 0.088, 0.034, 0.205), ss); pitch = lerp(pitch, -0.9, ss); pole.lerp(V3(s * 0.25, 1, 0.2), ss); yawF = lerp(yawF, s * 0.25, ss); }
      if (B.feet && B.feet[side]) ank.lerp(toV(B.feet[side]), B.feetMix ?? 1);
      const poleR = pole.normalize();
      const { mid, end } = solveIK2(hip, ank, THIGH, SHIN, poleR);
      const L = this.legs[side];
      L.tube.update([hip, hip.clone().lerp(mid, 0.5), mid, mid.clone().lerp(end, 0.5), end], LEG_R, {});
      L.knee.position.copy(mid);
      L.foot.position.copy(end);
      L.foot.rotation.set(pitch, yawF + (P.body?.twist ?? 0) * 0.3, 0, 'YXZ');
      this._feet[side] = end.clone().setY(0);
    }
  }

  _armSolve(name, side, ctx) {
    const s = side === 'L' ? 1 : -1;
    const A = ARM[name] || ARM.rest;
    const mir = (a) => V3(a[0] * s, a[1], a[2]);
    const M = A.f === 'head' ? ctx.MH : ctx.MB, q = A.f === 'head' ? ctx.qH : ctx.qB;
    const pp = mir(A.p); if (s < 0) { if (A.dyR) pp.y += A.dyR; if (A.dzR) pp.z += A.dzR; }
    return { sh: mir(A.sh || [0, 0, 0]), p: pp.applyMatrix4(M), fd: mir(A.fd).normalize().applyQuaternion(q), pn: mir(A.pn).normalize().applyQuaternion(q),
      pole: mir(A.pole).normalize().applyQuaternion(ctx.qB), hand: { ...A.hand }, f: A.f };
  }

  _arm(side, A, K, t, ctx, P) {
    const s = side === 'L' ? 1 : -1;
    const wa = K.wa, st = K.st;
    const mixS = (a, b, u) => ({ sh: a.sh.clone().lerp(b.sh, u), p: a.p.clone().lerp(b.p, u), fd: a.fd.clone().lerp(b.fd, u).normalize(), pn: a.pn.clone().lerp(b.pn, u).normalize(),
      pole: a.pole.clone().lerp(b.pole, u).normalize(), hand: mixHand(a.hand, b.hand, u) });
    const name = A.preset || 'rest';
    let S = this._armSolve(name, side, ctx);
    // walk arm styles (only when the arm is otherwise at rest)
    if (wa > 0 && (!A.preset || A.preset === 'rest') && !A.target) {
      const ph = K.ph;
      if (st.arms === 'swing') {
        S.p.add(V3(0, 0.012 * Math.abs(Math.sin(ph * TAU)), -0.07 * st.arm * Math.cos(ph * TAU) * s).applyQuaternion(ctx.qB).multiplyScalar(wa));
      } else {
        const W2 = this._armSolve(st.arms, side, ctx);
        if (st.arms === 'flail') W2.p.add(V3(0, 0.05 * Math.sin(ph * TAU * 2 + (s > 0 ? 0 : Math.PI)), 0.03 * Math.cos(ph * TAU * 2 + (s > 0 ? 0 : Math.PI))).applyQuaternion(ctx.qB));
        if (st.arms === 'tiptoe') W2.p.add(V3(0, 0.008 * Math.sin(ph * TAU + (s > 0 ? 0 : Math.PI)), 0).applyQuaternion(ctx.qB));
        S = mixS(S, W2, wa);
      }
    }
    if (A.from && A.from !== name) S = mixS(this._armSolve(A.from, side, ctx), S, clamp(A.mix ?? 1));
    const shRest = V3(s * SHOULDER.x, SHOULDER.y + 0.02 * K.shrug, SHOULDER.z);
    // explicit target (world)
    if (A.target) {
      const tg = this.root.worldToLocal(toV(A.target));
      if (name === 'grip' || A.grip) {
        // grip a bar: palm faces the bar, fingers wrap around it horizontally (toward the midline); the arm root
        // slides toward the bar on the soft bean so bars beside the face are within reach
        const axis = A.bar ? this._dirToRoot(toV(A.bar)).normalize() : V3(0, 1, 0);
        const sh0 = shRest.clone().applyMatrix4(ctx.MB);
        const toBar = tg.clone().sub(sh0); toBar.addScaledVector(axis, -toBar.dot(axis)).normalize();
        let fd = new THREE.Vector3().crossVectors(axis, toBar).multiplyScalar(-s);
        if (A.fingers) fd = this._dirToRoot(toV(A.fingers)).normalize();
        const pn = toBar.clone();
        const br = A.barRadius ?? 0.008;
        const wrist = tg.clone().addScaledVector(pn, -(br + HAND * 0.13)).addScaledVector(fd, -HAND * 0.3);
        S.p.copy(wrist); S.fd = fd.normalize(); S.pn = pn; S.hand = { ...S.hand, grip: 1, curl: 0.6 };
        const slide = toBar.clone().applyQuaternion(ctx.qB.clone().invert()); slide.y = 0;
        S.sh.add(slide.multiplyScalar(0.03)).add(V3(0, 0.015, 0));
      } else S.p.copy(tg);
    }
    if (A.palm) S.pn = this._dirToRoot(toV(A.palm)).normalize();
    if (A.fingers && !(A.target && (name === 'grip' || A.grip))) S.fd = this._dirToRoot(toV(A.fingers)).normalize();
    if (A.pole) S.pole = this._dirToRoot(toV(A.pole)).normalize();
    // procedural extras
    if (name === 'wipe') {   // a slow, big knuckle rub
      const r = (A.rub ?? 1) * clamp(A.mix ?? 1), ph = t * TAU * (A.rubRate ?? 1.25);
      S.p.add(V3(0.011 * Math.sin(ph) * s, 0.009 * Math.cos(ph), 0.003 * Math.sin(ph * 2)).applyQuaternion(ctx.qH).multiplyScalar(r));
      S.fd.add(V3(0.12 * Math.sin(ph + 0.6) * s, 0, 0).applyQuaternion(ctx.qH).multiplyScalar(r)).normalize();
    }
    if (name === 'wave') {
      const w = (A.wave ?? 1) * Math.sin(t * TAU * (A.waveRate ?? 2.0));
      const right = new THREE.Vector3().crossVectors(S.pn, S.fd).normalize();
      S.fd.addScaledVector(right, 0.5 * w * s).normalize();
      S.p.addScaledVector(right, 0.012 * w * s);
    }
    if (name === 'fidget') {
      const w = (A.fidget ?? 1);
      S.p.add(V3(-s * 0.006 * (0.5 + 0.5 * Math.sin(t * TAU * 1.6 + (s > 0 ? 0 : 1.3))), 0.004 * Math.sin(t * TAU * 0.8 + s), 0).applyQuaternion(ctx.qB).multiplyScalar(w));
    }
    if (name === 'hug') {   // clutching: knuckles knead the scarf a little
      const w = clamp(A.mix ?? 1);
      S.p.add(V3(0, 0.003 * Math.sin(t * TAU * 0.9 + (s > 0 ? 0 : 2)), 0.002 * Math.sin(t * TAU * 1.3 + s)).applyQuaternion(ctx.qB).multiplyScalar(w));
    }
    // blend from rest by reach
    const reach = clamp(A.reach ?? 1);
    if (reach < 1) S = mixS(this._armSolve('rest', side, ctx), S, reach);
    // the arm root slides on the soft bean (forward for hugs / clasps, up for face presets)
    if (A.shoulder) S.sh.add(V3(A.shoulder[0] * s, A.shoulder[1], A.shoulder[2]));
    const sh = shRest.clone().add(S.sh).applyMatrix4(ctx.MB);
    // tremble (hands on a target stay put; free hands shake)
    if (K.tremble > 0 && !A.target) S.p.add(V3(noise1(t * 22, 60 + s), noise1(t * 24, 61 + s), noise1(t * 20, 62 + s)).multiplyScalar(0.0035 * K.tremble));
    const hp = { ...S.hand, ...(A.hand || {}) };
    if (K.tremble > 0) hp.curl = (hp.curl ?? 0.15) + 0.06 * K.tremble * noise1(t * 18, 63 + s);
    this._limb(side, sh, S.p, S.pole, S.fd, S.pn, K, A.stretch ?? STRETCH_MAX);
    this.arms[side].hand.pose(hp);
  }

  /** 2-bone IK arm with rubber-hose stretch; every point but the (buried) root is kept outside the bean + scarf. */
  _limb(side, sh, wrist, pole, fd, pn, K, stretchMax) {
    const L = this.arms[side];
    const reach0 = (UPPER + FORE) * 0.97;
    const st = clamp(sh.distanceTo(wrist) / reach0, 1, Math.max(1, stretchMax));
    const { mid, end } = solveIK2(sh, wrist, UPPER * st, FORE * st, pole);
    const el = mid.clone().lerp(sh.clone().lerp(end, 0.5), 0.14);
    const pts = [sh.clone(), sh.clone().lerp(el, 0.5), el, el.clone().lerp(end, 1 / 3), el.clone().lerp(end, 2 / 3), end.clone()];
    for (let i = 1; i < pts.length; i++) this._pushOut(pts[i], K, ARM_R[Math.min(3, i >> 1)] + 0.004);
    L.tube.update(pts, (s) => (s < 0.5 ? lerp(ARM_R[0], ARM_R[1], s * 2) : lerp(ARM_R[1], ARM_R[3], (s - 0.5) * 2)), {});
    L.hand.root.position.copy(pts[5]);
    L.hand.aim(fd, pn);
    L.pts = pts; L.fd = fd.clone().normalize();
  }
  /** push a root-space point out of the (bent) bean, with extra margin across the scarf band */
  _pushOut(p, K, margin) {
    const q = _v.copy(p).applyMatrix4(this._MBinv);
    const u = this._unbend(K, q, V3());
    const sy = SCARF_Y - K.scarfSlide;
    const m = margin + 0.05 * Math.exp(-(((u.y - sy) / 0.036) ** 2));
    const d = bodySDF(u.x, u.y, u.z) - m;
    if (d >= 0) return p;
    sdfGrad(u.x, u.y, u.z, _g);
    u.addScaledVector(_g, -d);
    this._bend(K, u, q);
    return p.copy(q.applyMatrix4(this.bodyG.matrix));
  }
  _dirToRoot(d) {   // world direction -> root space
    this.root.getWorldQuaternion(_q2);
    return d.applyQuaternion(_q2.invert());
  }

  _motes(t, E, MB) {
    const fx = this.fx; fx.begin();
    const amt = E.motes ?? 1;
    if (amt > 0) {
      const pts = this.surfPts;
      fx.stream({ t, seed: 231, t0: -20, t1: 1e6, rate: 1.6 * amt, life: 2.6,
        origin: (tb) => { const q = pts[Math.floor(hash1(Math.floor(tb * 997)) * pts.length)]; return V3(q[0] + q[3] * 0.012, q[1] + q[4] * 0.012, q[2] + q[5] * 0.012).applyMatrix4(MB).toArray(); },
        vel: [0, 0.07, 0], spread: [0.02, 0.02, 0.02], size: [0.012, 0.024], color: [0xe6dcff, 0xffffff, 0xd0c0ff], alpha: 0.7, fade: [0.25, 0.5],
        cell: CELL.star, twinkle: true, wobble: 0.015, grow: 0.4 });
    }
    fx.end();
  }

  // ------------------------------------------------------------------------------------------------- helpers
  /** world position of an eye's lower lid outer corner (for wipe targets / tear FX) */
  tearPoint(side = 'L') {
    const s = side === 'L' ? 1 : -1;
    const p = headSurface(s * (EYE.u + 0.06), EYE.v - 0.33).p;
    this.headGroup.updateWorldMatrix(true, false);
    return p.applyMatrix4(this.headGroup.matrixWorld);
  }
}

function mixHand(a = {}, b = {}, u) {
  const o = {};
  for (const k2 of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const d = { curl: 0.15, point: 0, spread: 0.15, thumb: 0.3, cup: 0.1, splay: 0, grip: 0 }[k2] ?? 0;
    o[k2] = lerp(a[k2] ?? d, b[k2] ?? d, u);
  }
  return o;
}

export async function create() { return new Fear(); }
