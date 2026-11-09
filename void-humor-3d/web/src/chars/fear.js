// FEAR — the creator's own Fear (0.85 m): a small soft pale-lavender bean (head and body ONE shape, wider at
// the bottom), oversized violet-grey eyes with heavy expressive upper lids, thin worried brows, a wobbly
// three-strand antenna tuft, thin arms with small four-digit hands, knobbly little legs with round feet and a
// chunky hand-knitted mustard scarf with hanging, fringed ends. Effervescent inner-being glow.
//
// Rig notes
//  * The bean is one mesh built from a smooth-union SDF of two ellipsoids. The "head" is the top of the bean:
//    a vertex shader bends everything above the scarf rigidly with the head rotation (pivot inside the scarf),
//    so head yaw/pitch/roll and "sinking into the scarf" (shrug / cower) keep one continuous surface.
//  * The Face rig (core/face.js) lives on the rigid head part; its surface is a ray-cast into the same SDF.
//  * Secondary motion (tuft strands, scarf ends) is a damped-spring response evaluated statelessly: the rig
//    samples the pose over the last ~0.9 s (pose function / pose.poseAt, or an extrapolation of the current
//    pose) and convolves the motion of the strand roots with the spring's impulse response. Pure function of t.
// Pose API, anchors, tips: docs/chars/fear.md.  Lab: src/labs/fear.js.
import * as THREE from 'three';
import { Character, gazePoint } from '../core/character.js';
import { Face, EXPR, FACE_DEFAULTS } from '../core/face.js';
import { SweepTube, Limb, Hand, solveIK2, orientYZ } from '../core/limbs.js';
import { being, cloth, glowSprite, contactShadow } from '../core/materials.js';
import { Particles, CELL } from '../core/particles.js';
import { CTX } from '../core/context.js';
import { clamp, lerp, smooth, smoothstep, noise1, fbm1, hash1 } from '../core/util.js';

const TAU = Math.PI * 2;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const toV = (a) => (a instanceof THREE.Vector3 ? a.clone() : V3(a[0], a[1], a[2]));
const fract = (x) => x - Math.floor(x);
const _q = new THREE.Quaternion(), _e = new THREE.Euler(), _m = new THREE.Matrix4(), _v = new THREE.Vector3();
const QI = new THREE.Quaternion();

// ---------------------------------------------------------------------------------------------------------
// Palette
const C_BODY = 0xbfaaee, C_RIM = 0xb49cff, C_GLOW = 0xc8b4ff, C_WRAP = 0xff9fd2, C_LIMB = 0xb7a2e6, C_TUFT = 0xcbb8f6;
const C_SCARF = 0xe4a419, C_IRIS = 0x6b6392, C_IRIS2 = 0xaea6cc, C_LIMBAL = 0x2c2346, C_BROW = 0x4e3a78, C_LASH = 0x2e2048;

// ---------------------------------------------------------------------------------------------------------
// Proportions. Root space: feet on y = 0, faces +Z, +X = character's left. Body space: origin at the pelvis.
export const PELVIS_Y = 0.212, SIT_Y = 0.088, KNEEL_Y = 0.125;
const HEAD_C = V3(0, 0.40, 0);            // head centre (body space) = Face origin
const PIVOT = V3(0, 0.25, 0);             // bend pivot (body space, inside the scarf)
const BEND_Y = [0.165, 0.29];             // bend blend zone (body-space y): 0 below .. 1 (rigid head) above
const SHOULDER = V3(0.168, 0.18, 0.045);
const HIP = V3(0.07, 0.0, 0.0);
const UPPER = 0.12, FORE = 0.114, HAND = 0.068;
const THIGH = 0.098, SHIN = 0.094, ANKLE_Y = 0.032;
const SCARF_Y = 0.247;
const EYE = { u: 0.45, v: 0.18, r: 0.078 };
const MOUTH_V = -0.35, HW0 = 0.038;
const LEG_R = [0.021, 0.0172, 0.0182, 0.0152, 0.0165];

// ---------------------------------------------------------------------------------------------------------
// Bean SDF (body space): smooth union of a wide lower ellipsoid and a rounder upper (head) ellipsoid.
const ELL = [
  { c: [0, 0.12, 0.0], r: [0.216, 0.196, 0.206] },
  { c: [0, 0.383, 0.006], r: [0.19, 0.236, 0.184] },
];
function sdEll(x, y, z, E) {
  const px = x - E.c[0], py = y - E.c[1], pz = z - E.c[2];
  const k0 = Math.hypot(px / E.r[0], py / E.r[1], pz / E.r[2]);
  const k1 = Math.hypot(px / (E.r[0] * E.r[0]), py / (E.r[1] * E.r[1]), pz / (E.r[2] * E.r[2]));
  return k1 < 1e-9 ? -0.18 : (k0 * (k0 - 1)) / k1;
}
function smin(a, b, k) { const h = clamp(0.5 + (0.5 * (b - a)) / k); return lerp(b, a, h) - k * h * (1 - h); }
export function bodySDF(x, y, z) {
  let d = smin(sdEll(x, y, z, ELL[0]), sdEll(x, y, z, ELL[1]), 0.11);
  // soft cheek fullness under the eyes (helps the mouth/cheeks read in 3/4)
  const ch = Math.exp(-(((Math.abs(x) - 0.1) / 0.06) ** 2) - (((y - 0.33) / 0.05) ** 2)) * smoothstep(0.05, 0.16, z);
  d -= 0.006 * ch;
  return d;
}
function sdfGrad(x, y, z, out = V3()) {
  const e = 6e-4;
  out.set(bodySDF(x + e, y, z) - bodySDF(x - e, y, z), bodySDF(x, y + e, z) - bodySDF(x, y - e, z), bodySDF(x, y, z + e) - bodySDF(x, y, z - e));
  return out.normalize();
}
// ray from an interior point o along unit d -> distance to the surface
function rayHit(o, d, rMax = 0.6) {
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

// ---------------------------------------------------------------------------------------------------------
// Expressions (Face params tuned for Fear: heavy lids, thin worried brows, small mouth). FX('scared', {...}).
export const FEAR_BASE = { lidU: 1.0, browIn: 0.4, browOut: -0.04, lidSad: 0.12, mSmile: -0.05, mTeethU: 0.55, mTeethL: 0.3, mTongue: 0.45 };
export const FEAR_EXPR = {
  neutral: {},
  worried: { browIn: 0.78, browOut: -0.18, browSq: 0.32, lidSad: 0.45, lidU: 0.98, mSmile: -0.32, mPress: 0.3, mWide: -0.2 },
  nervous: { browIn: 0.68, browOut: 0.1, browSq: 0.22, lidSad: 0.3, lidU: 1.08, mSmile: 0.14, mClench: 0.6, mWide: 0.45, mAsym: 0.15, saccade: 1.5 },
  scared: { lidU: 1.28, lidL: 0.04, browIn: 0.92, browOut: 0.28, browSq: 0.42, lidSad: 0.3, mSmile: -0.45, mOpen: 0.17, mWide: 0.35, mTeethL: 0.5, pupil: 0.68, mTremble: 0.35 },
  terror: { lidU: 1.42, browIn: 1, browOut: 0.55, browSq: 0.5, lidSad: 0.25, mOpen: 0.75, mWide: 0.45, mSmile: -0.6, mTeethL: 0.75, mTeethU: 0.5, pupil: 0.48, mTremble: 0.6 },
  flinch: { lidU: 0.0, blink: 1, lidL: 1, squint: 1, lidAngry: 0.35, browIn: -0.2, browSq: 1, browOut: -0.45, browMid: -0.2, mClench: 1, mWide: 0.75, mSmile: -0.35, autoBlink: 0, saccade: 0 },
  cry: { browIn: 0.95, browOut: -0.35, browSq: 0.45, lidSad: 0.7, lidU: 0.72, lidL: 0.38, mSmile: -0.72, mOpen: 0.24, mWide: 0.25, mPout: 0.3, mTremble: 0.6, tearL: 0.85, tearR: 0.8, wet: 0.9 },
  sob: { browIn: 1, browOut: -0.42, browSq: 0.6, lidSad: 0.6, lidU: 0.32, lidL: 0.62, mSmile: -0.78, mOpen: 0.52, mWide: 0.38, mTeethU: 0.4, mTremble: 0.7, tearL: 1, tearR: 1, wet: 1 },
  sniffle: { browIn: 0.82, browOut: -0.26, lidSad: 0.55, lidU: 0.8, lidL: 0.25, mSmile: -0.36, mPout: 0.45, mPress: 0.35, tearL: 0.5, tearR: 0.45, wet: 0.75 },
  startle: { lidU: 1.42, lidL: 0, browIn: 0.88, browOut: 0.92, mOpen: 0.4, mRound: 0.62, pupil: 0.58, autoBlink: 0, saccade: 0 },
  listen: { lidU: 1.24, browIn: 0.72, browOut: 0.38, browAsym: 0.32, browSq: 0.15, mOpen: 0.1, mRound: 0.5, mSmile: -0.15, pupil: 0.85, saccade: 0.35 },
  curious: { lidU: 1.1, browIn: 0.38, browOut: 0.28, browAsym: 0.3, mSmile: 0.06, mRound: 0.2, mPress: 0.15, pupil: 1.1 },
  peek: { lidUL: 1.05, lidUR: 0.22, lidLR: 0.55, browIn: 0.7, browSq: 0.45, browOutR: -0.2, mClench: 0.4, mWide: 0.25, mSmile: -0.12, lidSad: 0.25 },
  wonder: { lidU: 1.3, lidL: 0.04, browIn: 0.66, browOut: 0.46, browSq: 0, mOpen: 0.42, mRound: 0.5, mSmile: 0.08, pupil: 1.48, wet: 0.85, saccade: 0.25 },
  awe: { lidU: 1.16, lidL: 0.12, browIn: 0.82, browOut: 0.18, lidSad: 0.22, mOpen: 0.2, mRound: 0.3, mSmile: 0.28, pupil: 1.5, wet: 1, tearL: 0.55, tearR: 0.5 },
  shy: { lidU: 0.74, lidL: 0.26, browIn: 0.48, browOut: 0.04, lidSad: 0.26, mSmile: 0.14, mPress: 0.42, mWide: -0.25, blush: 0.6, gazePitch: -0.26, gazeYaw: 0.2 },
  shySmile: { lidU: 0.74, lidL: 0.44, browIn: 0.44, browOut: 0.1, lidSad: 0.2, mSmile: 0.52, mAsym: 0.14, mPress: 0.2, mWide: -0.1, blush: 0.75 },
  hopeful: { lidU: 1.12, browIn: 0.62, browOut: 0.2, mSmile: 0.26, mOpen: 0.04, wet: 0.45, pupil: 1.18 },
  relieved: { lidU: 0.72, lidL: 0.22, browIn: 0.62, browOut: -0.08, lidSad: 0.35, mSmile: 0.3, mOpen: 0.12, mRound: 0.42 },
  happy: { mSmile: 0.95, lidL: 0.5, lidU: 0.92, browIn: 0.34, browOut: 0.22, blush: 0.4, mOpen: 0.16, mTeethU: 0.5, mWide: 0.2 },
  giggle: { mSmile: 0.92, mOpen: 0.28, mTeethU: 0.7, lidL: 0.72, lidU: 0.55, browIn: 0.42, browOut: 0.15, blush: 0.45 },
  sad: { mSmile: -0.56, mPout: 0.36, browIn: 0.82, browOut: -0.36, browSq: 0.2, lidSad: 0.66, lidU: 0.68, wet: 0.35 },
  gulp: { lidU: 1.2, browIn: 0.82, browSq: 0.35, mPress: 0.9, mWide: -0.35, mSmile: -0.22, lidSad: 0.2 },
  trust: { lidU: 0.86, lidL: 0.32, browIn: 0.52, browOut: -0.05, lidSad: 0.3, mSmile: 0.32, wet: 0.5 },
  confused: { browAsym: 0.6, browIn: 0.32, browSq: 0.3, mAsym: -0.35, mSmile: -0.1, mPress: 0.3, lidU: 1.0 },
  whimper: { browIn: 0.96, browOut: -0.3, lidSad: 0.6, lidU: 0.86, mSmile: -0.56, mOpen: 0.13, mWide: 0.1, mTremble: 0.85, wet: 0.6 },
};
const SIDE_KEYS = { lidUL: 'lidU', lidUR: 'lidU', lidLL: 'lidL', lidLR: 'lidL', browInL: 'browIn', browInR: 'browIn', browOutL: 'browOut', browOutR: 'browOut' };
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
    const va = a[k2] ?? a[SIDE_KEYS[k2]] ?? FACE_DEFAULTS[k2], vb = b[k2] ?? b[SIDE_KEYS[k2]] ?? FACE_DEFAULTS[k2];
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
// p = wrist, fd = finger direction, pn = palm normal, pole = elbow hint, hand = Hand.pose params.
const ARM = {
  rest: { f: 'body', p: [0.212, 0.05, 0.115], fd: [-0.1, -1, 0.3], pn: [-1, 0, -0.35], pole: [0.6, -0.3, -0.9], hand: { curl: 0.32, spread: 0.12, thumb: 0.3, cup: 0.2 } },
  hug: { f: 'body', p: [-0.045, 0.145, 0.232], dyR: 0.045, fd: [-0.85, -0.05, -0.55], pn: [-0.45, 0.05, -1], pole: [0.5, -0.8, 0.3], sh: [-0.035, 0.012, 0.075], hand: { curl: 0.55, spread: 0.1, cup: 0.5, thumb: 0.25 } },
  clasp: { f: 'body', p: [0.024, 0.225, 0.265], fd: [-0.4, 0.85, 0.3], pn: [-1, 0, 0.15], pole: [1, -0.8, -0.1], sh: [-0.03, 0.02, 0.06], hand: { curl: 0.5, cup: 0.4, thumb: 0.55, spread: 0.05 } },
  chest: { f: 'body', p: [0.055, 0.165, 0.25], fd: [-0.35, 0.9, 0.15], pn: [0, 0, -1], pole: [1, -0.7, 0], sh: [-0.02, 0.01, 0.04], hand: { curl: 0.2, cup: 0.35, spread: 0.2, thumb: 0.35 } },
  tummy: { f: 'body', p: [0.11, 0.065, 0.235], fd: [-0.6, -0.5, 0.25], pn: [-0.3, 0, -1], pole: [1, -0.3, -0.4], hand: { curl: 0.2, cup: 0.3, spread: 0.2, thumb: 0.3 } },
  fidget: { f: 'body', p: [0.035, 0.11, 0.252], fd: [-0.85, 0.25, 0.4], pn: [0.15, -0.9, -0.4], pole: [1, -0.6, -0.3], sh: [-0.02, 0, 0.05], hand: { curl: 0.55, point: 0.75, thumb: 0.3, spread: 0.05 } },
  behind: { f: 'body', p: [0.09, 0.07, -0.215], fd: [-0.5, -0.6, -0.2], pn: [0, 0, 1], pole: [1, 0, 0.3], hand: { curl: 0.4, cup: 0.3 } },
  up: { f: 'body', p: [0.3, 0.42, 0.09], fd: [0.35, 1, 0.15], pn: [0, 0.1, 1], pole: [1, -0.8, -0.4], hand: { splay: 1, spread: 0.95, thumb: 0.9, curl: 0, cup: 0 } },
  shrug: { f: 'body', p: [0.27, 0.19, 0.14], fd: [0.7, 0.15, 0.6], pn: [0, 1, 0.1], pole: [1, -0.6, -0.4], hand: { curl: 0.12, spread: 0.45, thumb: 0.7, cup: 0.2 } },
  point: { f: 'body', p: [0.22, 0.28, 0.24], fd: [0.15, 0.05, 1], pn: [-0.6, -0.8, 0], pole: [1, -0.5, -0.4], hand: { point: 1, curl: 0.5, thumb: 0.2 } },
  wave: { f: 'body', p: [0.25, 0.4, 0.13], fd: [0.12, 1, 0.1], pn: [0, 0, 1], pole: [1, -0.7, -0.3], hand: { spread: 0.5, thumb: 0.6, curl: 0.06, cup: 0.05 } },
  reach: { f: 'body', p: [0.2, 0.36, 0.3], fd: [0.1, 0.6, 1], pn: [-0.2, -0.6, 0.1], pole: [1, -0.6, -0.4], hand: { spread: 0.45, curl: 0.1, thumb: 0.55, cup: 0.1 } },
  tiptoe: { f: 'body', p: [0.105, 0.245, 0.262], fd: [0.0, -0.75, 0.65], pn: [-0.15, -0.6, -0.8], pole: [1, -0.7, -0.3], sh: [-0.025, 0.025, 0.06], hand: { curl: 0.35, cup: 0.2, spread: 0.1, thumb: 0.2 } },
  flail: { f: 'body', p: [0.255, 0.33, 0.13], fd: [0.3, 0.9, 0.3], pn: [0, 0, 1], pole: [1, -0.6, -0.5], hand: { splay: 0.7, spread: 0.8, thumb: 0.8, curl: 0 } },
  grip: { f: 'body', p: [0.14, 0.27, 0.26], fd: [-0.8, 0, 0.3], pn: [0, 0, 1], pole: [1, -0.7, -0.3], hand: { grip: 1, curl: 0.6, thumb: 0.15 } },
  hold: { f: 'body', p: [0.14, 0.27, 0.26], fd: [-0.2, 0.3, 1], pn: [-0.3, -1, 0], pole: [1, -0.7, -0.3], hand: { grip: 0.7, curl: 0.45, thumb: 0.3 } },
  // head-frame presets (follow the head)
  wipe: { f: 'head', p: [0.122, -0.07, 0.158], fd: [-0.35, 0.82, 0.3], pn: [-0.3, -0.15, -1], pole: [1, -0.8, -0.2], sh: [-0.01, 0.025, 0.04], hand: { curl: 0.78, thumb: 0.15, cup: 0.3, spread: 0.05 } },
  cover_mouth: { f: 'head', p: [0.035, -0.14, 0.2], fd: [-0.3, 1, 0.15], pn: [0, 0, -1], pole: [1, -0.8, -0.1], sh: [-0.02, 0.025, 0.05], hand: { curl: 0.12, spread: 0.2, cup: 0.35, thumb: 0.35 } },
  cheeks: { f: 'head', p: [0.175, -0.12, 0.085], fd: [-0.25, 1, 0.3], pn: [-1, 0, -0.4], pole: [1, -0.8, -0.2], sh: [0, 0.03, 0.02], hand: { curl: 0.12, spread: 0.35, cup: 0.45, thumb: 0.45 } },
  shield: { f: 'head', p: [0.08, -0.03, 0.255], fd: [0.08, 1, 0.12], pn: [0, 0.05, 1], pole: [1, -0.9, -0.1], sh: [-0.02, 0.03, 0.05], hand: { splay: 0.5, spread: 0.6, thumb: 0.65, curl: 0.08 } },
  eyes: { f: 'head', p: [0.08, -0.04, 0.21], fd: [-0.3, 1, 0.1], pn: [0, -0.1, -1], pole: [1, -0.8, -0.1], sh: [-0.02, 0.03, 0.05], hand: { spread: 0.5, curl: 0.1, cup: 0.2, thumb: 0.3 } },
  chin: { f: 'head', p: [0.06, -0.15, 0.17], fd: [-0.35, 0.8, 0.4], pn: [0, -0.3, -1], pole: [1, -0.8, -0.2], hand: { curl: 0.65, point: 0.4, thumb: 0.3 } },
  bite: { f: 'head', p: [0.03, -0.15, 0.19], fd: [-0.2, 1, 0.25], pn: [0, 0, -1], pole: [1, -0.8, -0.1], hand: { curl: 0.62, thumb: 0.25, cup: 0.3 } },
};
ARM.crossed = ARM.hug; ARM.hips = ARM.tummy; ARM.pocket = ARM.behind; ARM.self = ARM.hug; ARM.heart = ARM.chest;
export const ARM_PRESETS = Object.keys(ARM);

// ---------------------------------------------------------------------------------------------------------
// Tuft strands (head-local, from the top of the head): base offset, rest dir, length, rest curvature, thickness
const TUFT = [
  { o: [0, 0, 0.006], d: [0.0, 1, 0.1], L: 0.09, curv: [0.04, 0, -0.42], r: 1.0 },
  { o: [0.017, -0.004, -0.002], d: [0.5, 1, 0.04], L: 0.064, curv: [0.48, 0, -0.12], r: 0.86 },
  { o: [-0.018, -0.004, -0.006], d: [-0.55, 1, -0.05], L: 0.058, curv: [-0.5, 0, 0.06], r: 0.8 },
];
const TUFT_PROFILE = [0.0088, 0.007, 0.0054, 0.0046, 0.0058, 0.0079];
const SPRING_N = 30, SPRING_DT = 0.03;
function springK(tau, f, zeta) {   // second derivative of the damped spring's impulse response
  const w = TAU * f, a = zeta * w, wd = w * Math.sqrt(1 - zeta * zeta);
  return Math.exp(-a * tau) * (-2 * a * Math.cos(wd * tau) + ((a * a - wd * wd) / wd) * Math.sin(wd * tau));
}
const KT = [], KS = [];
for (let i = 0; i < SPRING_N; i++) { const tau = (i + 0.5) * SPRING_DT; KT.push(springK(tau, 2.6, 0.26) * SPRING_DT); KS.push(springK(tau, 1.5, 0.32) * SPRING_DT); }
const softClamp = (v, m) => m * Math.tanh(v / m);

// ---------------------------------------------------------------------------------------------------------
// Materials
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

let _knitTex = null;
function knitTexture() {
  if (_knitTex) return _knitTex;
  const S = 128, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  g.fillStyle = 'rgb(196,190,184)'; g.fillRect(0, 0, S, S);
  const cell = 32;
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    const cx = i * cell + cell / 2, cy = j * cell + cell / 2;
    for (const leg of [-1, 1]) {
      g.save(); g.translate(cx, cy + leg * 7.2); g.rotate(-leg * 0.62);
      const gr = g.createRadialGradient(0, 0, 0, 0, 0, 13);
      gr.addColorStop(0, 'rgb(255,255,255)'); gr.addColorStop(0.6, 'rgb(242,240,238)'); gr.addColorStop(1, 'rgb(214,210,206)');
      g.fillStyle = gr; g.beginPath(); g.ellipse(0, 0, 13.5, 6.4, 0, 0, TAU); g.fill();
      g.restore();
    }
  }
  _knitTex = new THREE.CanvasTexture(c);
  _knitTex.colorSpace = THREE.SRGBColorSpace; _knitTex.wrapS = _knitTex.wrapT = THREE.RepeatWrapping; _knitTex.anisotropy = 4;
  return _knitTex;
}
function knitMaterial(repU, repV) {
  const m = cloth(C_SCARF, { roughness: 0.9, sheen: 0.6, sheenColor: 0xffc860, sheenRoughness: 0.55, rim: 0.25, rimColor: 0xffd27a, glow: 0.12 });
  const tex = knitTexture().clone(); tex.needsUpdate = true; tex.repeat.set(repU, repV);
  m.map = tex; m.bumpMap = tex; m.bumpScale = 1.6;
  return m;
}
// add a constant (u along, v around) uv attribute to a core SweepTube
function tubeUV(tube) {
  const rings = tube.rings, R = tube.R, nv = rings * R + 2;
  const uv = new Float32Array(nv * 2);
  for (let r = 0; r < rings; r++) for (let j = 0; j < R; j++) { const i = r * R + j; uv[i * 2] = r / (rings - 1); uv[i * 2 + 1] = j / R; }
  uv[(nv - 2) * 2] = 0; uv[(nv - 2) * 2 + 1] = 0.5; uv[(nv - 1) * 2] = 1; uv[(nv - 1) * 2 + 1] = 0.5;
  tube.geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

// ---------------------------------------------------------------------------------------------------------
export class Fear extends Character {
  constructor() {
    super({ name: 'FEAR', speaker: 'FEAR', height: 0.85, seed: 23 });
    // ---- materials
    this.U = { uBendQ: { value: new THREE.Vector4(0, 0, 0, 1) }, uBendPivot: { value: PIVOT.clone() }, uBendOff: { value: V3() }, uBendY: { value: new THREE.Vector2(...BEND_Y) } };
    const beingOpts = { roughness: 0.5, sheen: 0.35, sheenColor: 0xf4e8ff, rim: 0.7, rimColor: C_RIM, rimPower: 2.6, glow: 0.07, glowColor: C_GLOW,
      fizz: 0.05, fizzColor: 0xeee4ff, fizzScale: 10, fizzSpeed: 0.22, wrap: 0.3, wrapColor: C_WRAP };
    this.bodyMat = bendMaterial(being(C_BODY, beingOpts), this.U);
    this.lidMat = being(C_BODY, { ...beingOpts, rim: 0.45, rimPower: 3.2, fizz: 0.02 });
    this.limbMat = being(C_LIMB, { ...beingOpts, rim: 0.6, glow: 0.06, fizz: 0.03 });
    this.tuftMat = being(C_TUFT, { ...beingOpts, rim: 1.2, rimPower: 1.8, glow: 0.16, fizz: 0.1, fizzScale: 30 });
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

    // glow aura + fizz motes + contact shadow
    this.aura = glowSprite(0xb9a0ff, 1.05, 0.1); this.aura.position.set(0, 0.28, -0.06); this.aura.renderOrder = -1; this.bodyG.add(this.aura);
    this.fx = new Particles({ max: 60, intensity: 1.4 }); this.root.add(this.fx.mesh);
    this.shadow = contactShadow(0.62, 0.5, 0.42); this.root.add(this.shadow);

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
  _buildBody() {
    const NA = 56, NV = 46, C = V3(0, 0.27, 0);
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
      eyes: { u: EYE.u, v: EYE.v, radius: EYE.r, sink: 0.6, splay: 0.2, lidMaterial: this.lidMat,
        iris: C_IRIS, iris2: C_IRIS2, irisR: 0.6, pupilR: 0.26, sclera: 0xeae6f6, limbal: C_LIMBAL, pupilColor: 0x120c1e,
        lashColor: C_LASH, lash: 0.9, lowerLash: 0.3, catchlight: 1, lidGapU: 1.04, lidGapL: 1.035,
        upOpen: 0.55, upWide: 0.98, lowRelaxed: -0.64, lowRaised: -0.1, maxYaw: 0.62, maxPitch: 0.5 },
      brows: { color: C_BROW, thickness: 0.0054, lift: 0.003, inner: [0.12, 0.6], mid: [0.38, 0.625], outer: [0.66, 0.55], range: 0.12, flatten: 0.45,
        profile: [0.8, 1, 0.8, 0.4] },
      mouth: { v: MOUTH_V, halfW: HW0, line: '#4a2460', lineW: HW0 * 0.2, interior: '#2a1030', interior2: '#5a2148', tongue: '#d77a9e', teeth: '#f7f2ff',
        lipTintRGB: '200,120,190', blushColor: '255,130,190', blushX: 0.078, blushY: 0.03 },
      decal: { uMin: -0.85, uMax: 0.85, vMin: -0.6, vMax: 0.1, size: [512, 352] },
    });
    for (const eye of this.face.eyes) for (const c of eye.up.children) if (c.geometry && c.geometry.type === 'ConeGeometry') c.visible = false;
    // tear meniscus along each lower lid (wet, welling eyes)
    this.menisci = this.face.eyes.map((eye) => {
      const rl = EYE.r * 1.04;
      const tg = new THREE.TorusGeometry(rl, 0.0026, 6, 24, 1.9);
      tg.rotateZ(Math.PI / 2 - 0.95); tg.rotateX(Math.PI / 2);
      const m = new THREE.Mesh(tg, new THREE.MeshStandardMaterial({ color: 0xeaf6ff, roughness: 0.05, metalness: 0, transparent: true, opacity: 0, emissive: 0x9fc4ff, emissiveIntensity: 0.35, depthWrite: false }));
      m.position.y = 0.0015; m.renderOrder = 3;
      eye.lo.add(m);
      return m;
    });
  }

  _buildTuft() {
    const top = headSurface(0, Math.PI / 2 - 0.08);
    this.topP = top.p.clone();
    this.tuft = TUFT.map((s) => {
      const tube = new SweepTube({ material: this.tuftMat, segments: 14, radial: 8, capRings: 3 });
      this.headGroup.add(tube.mesh);
      const base = this.topP.clone().add(V3(...s.o)).addScaledVector(top.n, -0.006);
      return { ...s, tube, base, d0: V3(...s.d).normalize(), curv0: V3(...s.curv) };
    });
  }

  _buildScarf() {
    // wrap: a slightly spiralling loop around the bean at SCARF_Y, ends tucked under the knot (front-left)
    this.wrap = new SweepTube({ material: knitMaterial(30, 4), segments: 72, radial: 12, capRings: 2, castShadow: true });
    tubeUV(this.wrap); this.bodyG.add(this.wrap.mesh);
    this.wrap.mesh.material.map.repeat.set(30, 4);
    const KA = 0.5;                                  // knot angle (from +Z toward +X)
    this.knotA = KA;
    const pts = [], ups = [];
    const N = 25;
    for (let i = 0; i <= N; i++) {
      const th = KA + 0.18 + (TAU * 1.0 * i) / N;
      const y = SCARF_Y + 0.012 * (i / N - 0.5) - 0.006 * Math.max(0, Math.cos(th)) + 0.004 * Math.sin(th * 3 + 1);
      const d = V3(Math.sin(th), 0, Math.cos(th));
      const r = rayHit(V3(0, y, 0), d, 0.4);
      const lump = 1 + 0.05 * Math.sin(th * 5 + 0.7) + 0.03 * Math.sin(th * 11);
      pts.push(V3(0, y, 0).addScaledVector(d, r + 0.019 * lump));
      ups.push(d.clone().negate());            // seam toward the body
    }
    this.wrapPts = pts; this.wrapUps = ups;
    this.wrapR = (s) => 0.031 * (1 + 0.06 * Math.sin(s * 37.0) + 0.04 * Math.sin(s * 91.0 + 1.3)) * (s < 0.03 ? 0.8 + 6.6 * s : 1);
    // knot
    const kd = V3(Math.sin(KA), 0, Math.cos(KA));
    const kr = rayHit(V3(0, SCARF_Y - 0.01, 0), kd, 0.4);
    this.knotP = V3(0, SCARF_Y - 0.012, 0).addScaledVector(kd, kr + 0.028);
    this.knotN = kd;
    const kg = new THREE.SphereGeometry(1, 20, 14);
    this.knot = new THREE.Mesh(kg, knitMaterial(5, 3)); this.knot.castShadow = true;
    this.knot.scale.set(0.034, 0.036, 0.026);
    this.bodyG.add(this.knot);
    // hanging ends with fringe
    this.tails = [{ L: 0.2, off: -0.012, w: 1 }, { L: 0.158, off: 0.016, w: 0.92 }].map((T, i) => {
      const tube = new SweepTube({ material: knitMaterial(12, 2), segments: 14, radial: 10, capRings: 2, castShadow: true });
      tubeUV(tube); this.bodyG.add(tube.mesh);
      const fr = new THREE.Group(); this.bodyG.add(fr);
      const fm = new THREE.MeshStandardMaterial({ color: 0xc98f22, roughness: 0.9 });
      for (let k = 0; k < 5; k++) {
        const c = new THREE.Mesh(new THREE.CapsuleGeometry(0.0034, 0.026 + 0.006 * hash1(k * 7 + i), 2, 5), fm);
        c.position.set((k - 2) * 0.0085, -0.016, 0); c.rotation.z = (k - 2) * 0.06;
        fr.add(c);
      }
      return { ...T, tube, fr };
    });
  }

  _buildLimbs() {
    this.arms = {};
    for (const side of ['L', 'R']) {
      const hand = new Hand({ size: HAND, fingers: 3, side, material: this.limbMat, thick: 1.28, fingerLen: 1.05 });
      const limb = new Limb({ material: this.limbMat, upper: UPPER, lower: FORE, radius: [0.0145, 0.0118, 0.011], segments: 14, radial: 8, hand, soft: 0.4 });
      this.root.add(limb.group);
      const palmL = HAND * 0.46, palmT = HAND * 0.16 * 1.28;
      this.addAnchor('hand' + side, hand.root, [0, palmL * 0.55, -palmT * 0.9]);
      this.arms[side] = limb;
    }
    this.legs = {};
    for (const side of ['L', 'R']) {
      const tube = new SweepTube({ material: this.limbMat, segments: 12, radial: 8, capRings: 2, castShadow: true });
      this.root.add(tube.mesh);
      const knee = new THREE.Mesh(new THREE.SphereGeometry(0.0225, 14, 10), this.limbMat); knee.castShadow = true;
      this.root.add(knee);
      const foot = new THREE.Group(); this.root.add(foot);
      const fm = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), this.limbMat);
      fm.scale.set(0.04, 0.028, 0.056); fm.position.set(0, -0.006, 0.02); fm.castShadow = true;
      foot.add(fm);
      const ank = new THREE.Mesh(new THREE.SphereGeometry(0.0175, 12, 8), this.limbMat); foot.add(ank);
      this.legs[side] = { tube, knee, foot };
    }
  }

  _buildTears() {
    const mat = new THREE.MeshPhysicalMaterial({ color: 0xe6f4ff, roughness: 0.04, metalness: 0, transparent: true, opacity: 0.8, emissive: 0x8fb8ff,
      emissiveIntensity: 0.4, clearcoat: 1, clearcoatRoughness: 0.05, depthWrite: false });
    this.drops = [];
    for (let i = 0; i < 4; i++) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 10), mat.clone());
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
    let lean = (B.lean ?? 0) + wa * st.lean + 0.11 * crouch - 0.1 * ss + 0.05 * ks + 0.1 * hunch - recoil * 0.2 + 0.012 * idle * fbm1(t * 0.31, sd + 4) + sobP * 0.04;
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
    hp += 0.32 * hunch + 0.12 * slump - 0.06 * startle - 0.05 * recoil + 0.018 * idle * fbm1(t * 0.37, sd + 9) + sobP * 0.06 - wa * st.lean * 0.4;
    hy += 0.024 * idle * fbm1(t * 0.29, sd + 10);
    hr += -0.5 * wa * st.roll * s1 + 0.018 * idle * fbm1(t * 0.21, sd + 11);
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
    const headOff = V3(0, -0.034 * shrug - 0.012 * hunch + (Hd.up ?? 0), 0.014 * hunch + (Hd.forward ?? 0));
    return { pos, yaw, pel, bodyQ, bodyS, headQ, headOff, crouch, hunch, shrug, sit, kneel, cower, tremble, startle, sob, sobP, wa, ph, st, s1, c1, br, recoil };
  }
  // body space -> head-bent body space (CPU copy of the vertex-shader bend)
  _bend(K, p, out = V3()) {
    const w = smoothstep(BEND_Y[0], BEND_Y[1], p.y);
    _q.slerpQuaternions(QI, K.headQ, w);
    return out.copy(p).sub(PIVOT).applyQuaternion(_q).add(PIVOT).addScaledVector(K.headOff, w);
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
  /** spring responses (world-space relative displacement) of each tuft strand tip and of the scarf knot */
  _secondary(t, P, K0, poseAt) {
    const tips = this.tuft.map((S) => S.base.clone().addScaledVector(S.d0, S.L).add(V3(0, 0, 0.012)));
    const x0 = tips.map((p) => this._bodyToWorld(K0, this._headToBody(K0, p)));
    const k0 = this._bodyToWorld(K0, this._bend(K0, this.knotP));
    const yT = tips.map(() => V3()), yS = V3(), a = V3(), b = V3();
    for (let i = 0; i < SPRING_N; i++) {
      const tau = (i + 0.5) * SPRING_DT;
      let Pp;
      try { Pp = poseAt ? (poseAt(t - tau) || {}) : this._extrapolate(P, tau); } catch (e) { Pp = this._extrapolate(P, tau); }
      const K = this._solve(t - tau, Pp);
      for (let k = 0; k < tips.length; k++) {
        this._bodyToWorld(K, this._headToBody(K, tips[k], a), a).sub(x0[k]);
        yT[k].addScaledVector(a, -KT[i]);
      }
      this._bodyToWorld(K, this._bend(K, this.knotP, b), b).sub(k0);
      yS.addScaledVector(b, -KS[i]);
    }
    return { tuft: yT, tail: yS };
  }

  // ------------------------------------------------------------------------------------------------- update
  update(t, pose = {}) {
    let P, poseAt = null;
    if (typeof pose === 'function') { poseAt = pose; P = pose(t) || {}; } else { P = pose || {}; poseAt = P.poseAt || null; }
    const E = P.extra || {}, Hd = P.head || {};
    const K = this._solve(t, P);
    this.place(K.pos, K.yaw);
    this.bodyG.position.copy(K.pel); this.bodyG.quaternion.copy(K.bodyQ); this.bodyG.scale.copy(K.bodyS);
    this.headPivot.position.copy(PIVOT).add(K.headOff); this.headPivot.quaternion.copy(K.headQ);
    this.root.updateMatrixWorld(true);
    this.U.uBendQ.value.set(K.headQ.x, K.headQ.y, K.headQ.z, K.headQ.w);
    this.U.uBendOff.value.copy(K.headOff);
    this._K = K;
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
        const k = 'lidU' + side;
        fp[k] = lerp(fp[k] ?? fp.lidU, 0.12, w); fp['lidL' + side] = lerp(fp['lidL' + side] ?? fp.lidL, 0.7, w);
      }
    }
    const shut = smooth((0.22 - Math.max(fp.lidUL ?? fp.lidU, fp.lidUR ?? fp.lidU)) / 0.22);
    if (shut > 0) fp.blink = Math.max(fp.blink, shut);
    const gaze = gazePoint(P.gaze, CTX.camera);
    this.face.update(t, fp, { gaze, speech: this.speech(t, P), blinkAt: P.blinkAt });
    const men = clamp(cry * 1.3 + fp.wet * 0.25 + (fp.tearL + fp.tearR) * 0.2);
    this.menisci.forEach((m) => { m.material.opacity = 0.85 * men; m.visible = men > 0.02; });
    this._tears(t, cry, E);

    // ---- tuft & scarf
    this._tuft(t, K, E, sec.tuft);
    this._scarf(t, K, sec.tail);

    // ---- limbs
    this._legs(t, K, P);
    const MB = this.bodyG.matrix, MH = new THREE.Matrix4().multiplyMatrices(MB, this.headPivot.matrix).multiply(this.headGroup.matrix);
    const qH = K.bodyQ.clone().multiply(K.headQ);
    const ctx = { MB, MH, qB: K.bodyQ, qH };
    this._arm('L', P.armL || {}, K, t, ctx, P);
    this._arm('R', P.armR || {}, K, t, ctx, P);

    // ---- glow / fizz
    const gl = E.glow ?? 1, fz = E.fizz ?? 1;
    this.mats.forEach((m, i) => { const u = m.userData.uniforms; u.uRim.value = this.baseU[i].rim * gl; u.uGlow.value = this.baseU[i].glow * (0.6 + 0.4 * gl); u.uFizz.value = this.baseU[i].fizz * fz; });
    this.aura.material.opacity = 0.1 * gl * (E.aura ?? 1);

    // ---- anchors (root space)
    const an = (n, v) => this._anch[n].position.copy(v);
    const bp = (x, y, z) => V3(x, y, z).applyMatrix4(MB);
    an('chest', bp(0, 0.17, 0.225)); an('back', bp(0, 0.17, -0.225)); an('belly', bp(0, 0.06, 0.225)); an('hip', bp(0, 0, 0));
    an('scarf', this._bend(K, this.knotP).applyMatrix4(MB));
    an('shoulderL', bp(SHOULDER.x, SHOULDER.y + 0.02 * K.shrug, SHOULDER.z)); an('shoulderR', bp(-SHOULDER.x, SHOULDER.y + 0.02 * K.shrug, SHOULDER.z));
    an('tuft', this._tuftTip.clone().applyMatrix4(MH)); an('tuftBase', this.tuft[0].base.clone().applyMatrix4(MH));
    an('footL', this._feet.L); an('footR', this._feet.R);

    // ---- shadow & motes
    this.shadow.position.set(K.pel.x, 0.004, K.pel.z + 0.02);
    this.shadow.scale.set(1 + 0.25 * K.sit + 0.1 * K.crouch, 1, 1 + 0.3 * K.sit);
    this._motes(t, E, MB);
  }

  // ------------------------------------------------------------------------------------------------- parts
  _tuft(t, K, E, yWorld) {
    // world displacement -> head-local
    const qInv = new THREE.Quaternion().setFromAxisAngle(V3(0, 1, 0), K.yaw).multiply(K.bodyQ).multiply(K.headQ).invert();
    const perk = clamp((E.tuftPerk ?? 0) + K.startle * 0.9), droop = clamp(E.tuftDroop ?? 0), tr = K.tremble;
    const sd = this.seed, gain = 20 * (E.tuftWobble ?? 1);
    this.tuft.forEach((S, k) => {
      const yl = yWorld[k].clone().applyQuaternion(qInv);
      const dyn = V3(softClamp(yl.x * gain, 1.5), 0, softClamp(yl.z * gain, 1.5));
      const L = S.L * (1 + 0.12 * perk - 0.08 * droop) * (1 - 0.15 * softClamp(Math.max(0, yl.y * 8), 1));
      const d0 = S.d0.clone();
      d0.x *= 1 - 0.35 * perk; d0.normalize();
      const curv = S.curv0.clone().multiplyScalar(1 - 0.75 * perk);
      curv.add(V3(S.d0.x * 1.4 * droop, -0.4 * droop, -0.5 * droop));
      const wob = V3(0.07 * fbm1(t * 0.6, sd + 20 + k), 0, 0.06 * fbm1(t * 0.55, sd + 30 + k));
      if (tr > 0) wob.add(V3(tr * 0.22 * noise1(t * 23 + k * 3.1, sd + 40), 0, tr * 0.2 * noise1(t * 21 + k * 2.7, sd + 50)));
      const bend = curv.add(wob).add(dyn);
      const pts = [S.base.clone()];
      const n = 5;
      for (let i = 0; i < n; i++) {
        const s = (i + 0.5) / n;
        const dir = d0.clone().addScaledVector(bend, Math.pow(s, 1.25) * 1.3).normalize();
        pts.push(pts[i].clone().addScaledVector(dir, L / n));
      }
      S.tube.update(pts, TUFT_PROFILE.map((r) => r * S.r * (1 + 0.08 * perk)), {});
      if (k === 0) this._tuftTip = pts[n].clone();
    });
  }

  _scarf(t, K, yWorld) {
    // wrap follows the bend (CPU copy of the shader bend, so it hugs the bent bean)
    const pts = this.wrapPts.map((p) => this._bend(K, p));
    const ups = this.wrapUps.map((u, i) => { _q.slerpQuaternions(QI, K.headQ, smoothstep(BEND_Y[0], BEND_Y[1], this.wrapPts[i].y)); return u.clone().applyQuaternion(_q); });
    this.wrap.update(pts, this.wrapR, { up: (s) => ups[Math.min(ups.length - 1, Math.round(s * (ups.length - 1)))], flatten: 0.42 });
    // knot
    const kp = this._bend(K, this.knotP);
    const wk = smoothstep(BEND_Y[0], BEND_Y[1], this.knotP.y);
    _q.slerpQuaternions(QI, K.headQ, wk);
    this.knot.position.copy(kp);
    orientYZ(this.knot, V3(0, 1, 0).applyQuaternion(_q), this.knotN.clone().applyQuaternion(_q));
    // tails: hang from under the knot, drape over the belly, swing with the spring response
    const qInv = new THREE.Quaternion().setFromAxisAngle(V3(0, 1, 0), K.yaw).multiply(K.bodyQ).invert();
    const yl = yWorld.clone().applyQuaternion(qInv);
    const down = V3(0, -1, 0).applyQuaternion(K.bodyQ.clone().invert());   // gravity in body space
    const swing = V3(softClamp(yl.x * 1.1, 0.07), 0, softClamp(yl.z * 1.1, 0.07));
    const side = V3(Math.cos(this.knotA), 0, -Math.sin(this.knotA));
    const tw = K.tremble * 0.004;
    this.tails.forEach((T, i) => {
      const n = 6, pts2 = [], ups2 = [];
      const start = kp.clone().addScaledVector(side, T.off).add(V3(0, -0.012, 0));
      pts2.push(start);
      const g = V3();
      for (let k2 = 1; k2 <= n; k2++) {
        const s = k2 / n;
        const prev = pts2[k2 - 1];
        const p = prev.clone().addScaledVector(down, T.L / n).addScaledVector(this.knotN, 0.006 * (1 - s));
        p.addScaledVector(swing, Math.pow(s, 1.4) * T.w / n * 2.2);
        if (tw > 0) p.add(V3(tw * noise1(t * 19 + i, 70 + k2), 0, tw * noise1(t * 17 + i, 80 + k2)));
        p.x += 0.006 * fbm1(t * 0.5 + i, 90) * s;
        // keep outside the bean (+ tail half thickness)
        for (let it = 0; it < 2; it++) {
          const d = bodySDF(p.x, p.y, p.z) - 0.013;
          if (d < 0) { sdfGrad(p.x, p.y, p.z, g); p.addScaledVector(g, -d); }
        }
        // re-normalise segment length
        const seg = p.clone().sub(prev); p.copy(prev).addScaledVector(seg.normalize(), T.L / n);
        pts2.push(p);
      }
      for (const p of pts2) ups2.push(sdfGrad(p.x, p.y, p.z).negate());
      T.tube.update(pts2, (s) => 0.024 * (1 + 0.05 * Math.sin(s * 30 + i)) * (s > 0.92 ? 0.85 : 1), { up: (s) => ups2[Math.min(n, Math.round(s * n))], flatten: 0.78 });
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
        const uu = sx * (EYE.u + 0.07 + 0.1 * slide), vv = lerp(EYE.v - 0.37, -0.74, slide);
        const s = headSurface(uu, vv);
        const r = 0.0085 * (0.35 + 0.65 * swell) * (0.8 + 0.4 * cry);
        m.position.copy(s.p).addScaledVector(s.n, r * 0.45);
        const tdir = headSurface(uu + sx * 0.02, vv + 0.04).p.sub(s.p).normalize();   // up along the path
        orientYZ(m, tdir, s.n);
        m.scale.set(r * 0.85, r * (1.1 + 0.45 * slide), r * 0.62);
        m.material.opacity = 0.85 * (1 - smooth((u - 0.86) / 0.12));
        m.visible = true;
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
    const pp = mir(A.p); if (s < 0 && A.dyR) pp.y += A.dyR;
    return { sh: mir(A.sh || [0, 0, 0]), p: pp.applyMatrix4(M), fd: mir(A.fd).normalize().applyQuaternion(q), pn: mir(A.pn).normalize().applyQuaternion(q),
      pole: mir(A.pole).normalize().applyQuaternion(ctx.qB), hand: { ...A.hand }, f: A.f };
  }

  _arm(side, A, K, t, ctx, P) {
    const s = side === 'L' ? 1 : -1;
    const limb = this.arms[side];
    const wa = K.wa, st = K.st;
    const mixS = (a, b, u) => ({ sh: a.sh.clone().lerp(b.sh, u), p: a.p.clone().lerp(b.p, u), fd: a.fd.clone().lerp(b.fd, u).normalize(), pn: a.pn.clone().lerp(b.pn, u).normalize(),
      pole: a.pole.clone().lerp(b.pole, u).normalize(), hand: mixHand(a.hand, b.hand, u) });
    let name = A.preset || 'rest';
    let S = this._armSolve(name, side, ctx);
    // walk arm styles (only when the arm is otherwise at rest)
    if (wa > 0 && (!A.preset || A.preset === 'rest') && !A.target) {
      const ph = K.ph;
      if (st.arms === 'swing') {
        S.p.add(V3(0, 0.012 * Math.abs(Math.sin(ph * TAU)), -s * 0.0 - 0.07 * st.arm * Math.cos(ph * TAU) * s).applyQuaternion(ctx.qB).multiplyScalar(wa));
      } else {
        const W2 = this._armSolve(st.arms, side, ctx);
        if (st.arms === 'flail') W2.p.add(V3(0, 0.05 * Math.sin(ph * TAU * 2 + (s > 0 ? 0 : Math.PI)), 0.03 * Math.cos(ph * TAU * 2 + (s > 0 ? 0 : Math.PI))).applyQuaternion(ctx.qB));
        if (st.arms === 'tiptoe') W2.p.add(V3(0, 0.008 * Math.sin(ph * TAU + (s > 0 ? 0 : Math.PI)), 0).applyQuaternion(ctx.qB));
        S = mixS(S, W2, wa);
      }
    }
    if (A.from && A.from !== name) S = mixS(this._armSolve(A.from, side, ctx), S, clamp(A.mix ?? 1));
    // explicit target (world)
    if (A.target) {
      const tg = this.root.worldToLocal(toV(A.target));
      if (name === 'grip' || A.grip) {
        // grip a bar: palm faces the bar, fingers wrap around it horizontally (toward the midline)
        const axis = A.bar ? this._dirToRoot(toV(A.bar)).normalize() : V3(0, 1, 0);
        const sh0 = V3(s * SHOULDER.x, SHOULDER.y, SHOULDER.z).applyMatrix4(ctx.MB);
        const toBar = tg.clone().sub(sh0); toBar.addScaledVector(axis, -toBar.dot(axis)).normalize();
        let fd = new THREE.Vector3().crossVectors(axis, toBar).multiplyScalar(-s);
        if (A.fingers) fd = this._dirToRoot(toV(A.fingers)).normalize();
        const pn = toBar.clone();
        const br = A.barRadius ?? 0.008;
        const wrist = tg.clone().addScaledVector(pn, -(br + HAND * 0.13)).addScaledVector(fd, -HAND * 0.3);
        S.p.lerp(wrist, 1); S.fd = fd.normalize(); S.pn = pn; S.hand = { ...S.hand, grip: 1, curl: 0.6 };
      } else S.p.copy(tg);
    }
    if (A.palm) S.pn = this._dirToRoot(toV(A.palm)).normalize();
    if (A.fingers && !(A.target && (name === 'grip' || A.grip))) S.fd = this._dirToRoot(toV(A.fingers)).normalize();
    if (A.pole) S.pole = this._dirToRoot(toV(A.pole)).normalize();
    // procedural extras
    if (name === 'wipe') {
      const r = (A.rub ?? 1) * clamp(A.mix ?? 1);
      S.p.add(V3(0.008 * Math.sin(t * TAU * 2.3) * s, 0.007 * Math.cos(t * TAU * 2.3), 0).applyQuaternion(ctx.qH).multiplyScalar(r));
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
    // blend from rest by reach
    const reach = clamp(A.reach ?? 1);
    if (reach < 1) S = mixS(this._armSolve('rest', side, ctx), S, reach);
    // the arm root slides on the soft bean (forward for hugs / clasps, up for face presets)
    if (A.shoulder) S.sh.add(V3(A.shoulder[0] * s, A.shoulder[1], A.shoulder[2]));
    const sh = V3(s * SHOULDER.x, SHOULDER.y + 0.02 * K.shrug, SHOULDER.z).add(S.sh).applyMatrix4(ctx.MB);
    // tremble (hands on a target stay put; free hands shake)
    if (K.tremble > 0 && !A.target) S.p.add(V3(noise1(t * 22, 60 + s), noise1(t * 24, 61 + s), noise1(t * 20, 62 + s)).multiplyScalar(0.0035 * K.tremble));
    const hp = { ...S.hand, ...(A.hand || {}) };
    if (K.tremble > 0) hp.curl = (hp.curl ?? 0.15) + 0.06 * K.tremble * noise1(t * 18, 63 + s);
    limb.update(sh, S.p, S.pole, { palmNormal: S.pn, fingerDir: S.fd });
    limb.hand.pose(hp);
  }
  _dirToRoot(d) {   // world direction -> root space
    this.root.getWorldQuaternion(_q);
    return d.applyQuaternion(_q.invert());
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
    const p = headSurface(s * (EYE.u + 0.06), EYE.v - 0.36).p;
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
