// THE DEPRESSION MAGICIAN — CHARS.MAGICIAN (speaker 'MAGICIAN'). A creepy-funny stage magician made of desaturated
// grey-blue gloom: 2.1 m tall but stooped (hunched back, long neck jutting forward), dented tall top hat (flies off:
// bald dome + three sad comb-over strands that spring up), long tattered swallow-tail coat with a high collar, a little
// grey cravat, grey-white gloves with long thin fingers, spindly legs in striped trousers, pointy curled shoes.
// Gaunt pale-grey face: sunken heavy-lidded eyes (pale yellow-grey irises, small pupils), too-wide thin grin, pencil
// moustache, long nose. Props: a small wavy dagger (right hand) and a velvet pouch of numbing dust (left hand).
// Slapstick-durable: extra.kicked (spread-eagle flight), extra.crashed (upside-down headstand slump, legs up),
// extra.dizzy (spinning swirl irises + circling stars), extra.lick (long grey-violet tongue across the upper lip).
// Pose API, anchors, tips: docs/chars/magician.md.  Lab: src/labs/magician.js.  Pure function of (t, pose).
import * as THREE from 'three';
import { mergeVertices, mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { Character, gazePoint } from '../core/character.js';
import { Face, EXPR, FACE_DEFAULTS } from '../core/face.js';
import { SweepTube, solveIK2, orientYZ } from '../core/limbs.js';
import { enhance, contactShadow } from '../core/materials.js';
import { Particles, CELL } from '../core/particles.js';
import { CTX } from '../core/context.js';
import { clamp, lerp, smooth, smoothstep, noise1, fbm1, hash1 } from '../core/util.js';

const TAU = Math.PI * 2;
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const toV = (a) => (a instanceof THREE.Vector3 ? a.clone() : V(a[0], a[1], a[2]));
const fract = (x) => x - Math.floor(x);
const rounded = (x) => { const y = 1 - clamp(x); return Math.sqrt(Math.max(0, 1 - y * y)); };
const _q1 = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _e1 = new THREE.Euler(), _m1 = new THREE.Matrix4();
function pw(K, a, col = 1) { // piecewise-linear lookup in rows [[x, y1, y2, ...], ...]
  if (a <= K[0][0]) return K[0][col];
  for (let i = 1; i < K.length; i++) if (a <= K[i][0]) return lerp(K[i - 1][col], K[i][col], (a - K[i - 1][0]) / (K[i][0] - K[i - 1][0]));
  return K[K.length - 1][col];
}
const qE = (x, y, z, o = 'YXZ') => new THREE.Quaternion().setFromEuler(_e1.set(x, y, z, o));
// PURITY: three's Curve caches its arc-length table until `needsUpdate` is set, and core SweepTube.update() rewrites
// curve.points without invalidating it -> getPointAt() would use lengths from whichever frame was rendered first.
// Every tube update in this rig goes through sweep(), which invalidates the cache first.
function sweep(tube, pts, rad, opts) { tube.curve.needsUpdate = true; return tube.update(pts, rad, opts); }

// ---------------------------------------------------------------------------------------------------------
// Palette (desaturated grey-blue gloom)
const C = {
  face: 0xb3b9c6, socket: 0x666b80, coat: 0x4a5266, lapel: 0x30364a, shirt: 0xc3c7d0, cravat: 0x5f6476,
  glove: 0xcfd0d0, stripeA: 0x8b909e, hat: 0x353b4b, band: 0x1d2029, shoe: 0x262932, hair: 0x3c4050,
  velvet: 0x4d3d5c, blade: 0xc2cad8, tongue: 0x8c7f98, cold: 0x9fb9ea,
};
// Proportions (metres). Root at the feet, facing +Z, +X = the magician's LEFT.
const HIP_Y = 1.035, HIP_X = 0.078, THIGH = 0.475, SHIN = 0.465, ANKLE_Y = 0.062;
const WAIST = 0.12;                               // chest pivot above the pelvis
const STOOP = 0.42;                               // default forward hunch of the chest (rad)
const SH = [0.15, 0.365, -0.01];                  // left shoulder joint (chest-local)
const NECK_BASE = [0, 0.41, 0.0], NECK_LEN = 0.17, NECK_TILT = 0.95;
const HEAD_S = 1.2;                               // head scale (bigger head reads better at phone size)
const HR = [0.094, 0.138, 0.104];                 // skull radii (narrow, tall)
const EYE_U = 0.42, EYE_V = 0.1, EYE_R = 0.0275, MOUTH_V = -0.47, HW0 = 0.046;
const UPPER = 0.31, FORE = 0.29, HAND_SIZE = 0.2;
const JAW = { y: -0.075, drop: 0.009, back: 0.002, soft: 0.03 };

// ---------------------------------------------------------------------------------------------------------
// Head surface (head-local: origin = head centre, +Z out of the face). Shared by mesh, Face, hair, nose, tongue.
function headPoint(u, v, out = V()) {
  const cv = Math.cos(v), sv = Math.sin(v), cu = Math.cos(u), su = Math.sin(u);
  let x = HR[0] * su * cv, y = HR[1] * sv, z = HR[2] * cu * cv;
  const front = Math.max(0, cu), au = Math.abs(u);
  const low = smoothstep(0.05, -1.2, v);
  x *= 1 - 0.3 * low;                                                     // gaunt jaw -> pointed chin
  const chin = Math.exp(-(((v + 1.08) / 0.3) ** 2)) * front ** 3;
  y -= 0.016 * chin; z += 0.017 * chin;
  const back = Math.max(0, -cu) * smoothstep(-0.3, 0.8, v);
  z *= 1 + 0.07 * back; x *= 1 + 0.03 * back;                           // fuller cranium
  // gaunt sculpt (front half): sharp cheekbones over sunken cheeks, temple hollows, deep eye sockets under a brow
  // ridge, a lean jaw corner and a small muzzle so the thin grin sits proud of the hollows
  const g2 = (a, a0, sa, b, b0, sb) => Math.exp(-(((a - a0) / sa) ** 2) - (((b - b0) / sb) ** 2));
  const hollow = g2(au, 0.72, 0.28, v, -0.42, 0.17) * front;            // sunken cheeks (front)
  const suck = g2(au, 1.12, 0.36, v, -0.46, 0.2);                       // ... carried round to the silhouette
  const ck = g2(au, 0.82, 0.24, v, -0.1, 0.075) * front;                // sharp cheekbones
  const temple = g2(au, 1.08, 0.2, v, 0.3, 0.16);
  const es = g2(au, EYE_U, 0.18, v, EYE_V, 0.14);
  const br = g2(au, 0.4, 0.34, v, 0.33, 0.075) * front;
  const mb = g2(u, 0, 0.42, v, MOUTH_V + 0.02, 0.17) * front;
  const jaw = g2(au, 0.98, 0.2, v, -0.8, 0.13);
  const k = 1 - 0.115 * hollow - 0.07 * suck + 0.085 * ck - 0.055 * temple - 0.085 * es + 0.05 * br + 0.05 * mb + 0.04 * jaw;
  return out.set(x * k, y * k, z * k);
}
const _hu = V(), _hv = V(), _hw = V();
function headSurf(u, v) {
  const e = 1e-3, p = headPoint(u, v);
  headPoint(u + e, v, _hu).sub(headPoint(u - e, v, _hw));
  headPoint(u, v + e, _hv).sub(headPoint(u, v - e, _hw));
  const n = V().crossVectors(_hu, _hv);
  if (n.lengthSq() < 1e-14) n.copy(p);
  n.normalize(); if (n.dot(p) < 0) n.negate();
  return { p, n };
}
const SP = (u, v, h = 0) => { const { p, n } = headSurf(u, v); return p.addScaledVector(n, h); };

// Painted-mouth geometry (mirrors core/face.js _drawDecal) in decal metres around the mouth centre.
function mouthGeom(p) {
  const open = clamp(p.mOpen, 0, 1.3) * (1 - clamp(p.close ?? 0));
  const round = clamp(p.mRound), wide = clamp(p.mWide, -1, 1), clench = clamp(p.mClench), press = clamp(p.mPress);
  const w = HW0 * (1 + 0.3 * wide) * (1 - 0.45 * round) * (1 + 0.22 * clench) * (1 - 0.18 * press);
  const smile = clamp(p.mSmile, -1, 1), asym = clamp(p.mAsym, -1, 1);
  const shift = (p.mShift || 0) * HW0 * 0.4;
  const yR = (smile * 0.62 - asym * 0.3) * HW0, yL = (smile * 0.62 + asym * 0.3) * HW0;
  let h = HW0 * 1.75 * open + round * HW0 * 0.7 * Math.min(1, open * 4);
  if (clench > 0.01) h = Math.max(h, HW0 * 0.42 * clench);
  const cm = (yL + yR) / 2;
  let top, bot;
  if (h < HW0 * 0.04) { const cy = -smile * HW0 * 0.06; top = bot = 0.25 * cm + 0.75 * (cy - cm * 0.35 + (smile < 0 ? -smile * HW0 * 0.15 : 0)); }
  else {
    const yTop = cm * 0.35 + h * 0.3 + (smile < 0 ? -smile * HW0 * 0.1 : 0);
    const yBot = cm * 0.2 - h * 0.7 - (smile > 0 ? smile * h * 0.35 : 0);
    top = 0.25 * cm + 0.75 * yTop; bot = 0.25 * cm + 0.75 * yBot;
  }
  return { w, shift, yL, yR, cm, top, bot, h, open: h >= HW0 * 0.04, smile, press };
}

// ---------------------------------------------------------------------------------------------------------
// Expressions (layer on top of core EXPR). MX('gloat', {...}) -> full flat params.
export const MEXPR = {
  sly: { lidU: 0.64, lidL: 0.24, browIn: 0.0, browOut: 0.35, browAsym: 0.25, mSmile: 0.5, mWide: 0.45, mAsym: 0.3 },
  rest: { lidU: 0.7, lidL: 0.18, browIn: 0.05, browOut: 0.15, mSmile: 0.18, mWide: 0.3, mAsym: 0.12 },
  lurk: { lidU: 0.98, lidL: 0.32, browIn: -0.3, browOut: 0.6, browSq: 0.3, mSmile: 0.72, mWide: 0.75, mAsym: 0.2, pupil: 0.8 },
  scheme: { lidU: 0.52, lidL: 0.45, lidAngry: 0.35, browIn: -0.7, browOut: 0.6, browSq: 0.6, mSmile: 0.85, mWide: 0.85, mAsym: 0.12 },
  gloat: { lidU: 0.6, lidL: 0.5, lidAngry: 0.2, browIn: 0.05, browOut: 0.75, browAsym: 0.2, mSmile: 1, mWide: 1, mOpen: 0.16, mTeethU: 1, mTeethL: 0.9 },
  hungry: { lidU: 0.5, lidL: 0.42, browIn: 0.45, browOut: 0.25, mSmile: 0.75, mWide: 0.7, mOpen: 0.24, mTeethU: 0.9, mTeethL: 0.5, mTongue: 1, wet: 0.6, pupil: 1.3 },
  relish: { lidU: 0.1, lidL: 0.55, browIn: 0.6, browOut: 0.15, mSmile: 0.7, mWide: 0.6, autoBlink: 0, saccade: 0 },
  whisper: { lidU: 0.58, lidL: 0.4, browIn: -0.2, browOut: 0.6, browAsym: 0.5, mSmile: 0.5, mAsym: 0.4, mRound: 0.2, mWide: 0.35 },
  snicker: { lidU: 0.3, lidL: 0.75, browIn: 0.35, browOut: 0.45, mSmile: 1, mWide: 0.9, mOpen: 0.12, mTeethU: 1, mTeethL: 0.75 },
  innocent: { lidU: 1.12, lidL: 0.22, browIn: 0.7, browOut: 0.55, mSmile: 0.38, mPress: 0.45, mWide: 0.15, mRound: 0.1 },
  uhoh: { lidU: 1.32, lidL: 0.0, lidSad: 0.25, browIn: 1, browOut: 0.1, browSq: 0.4, mSmile: -0.45, mWide: 0.8, mClench: 1, pupil: 0.5, saccade: 0 },
  popped: { lidU: 1.42, lidL: 0, browIn: 1, browOut: 1, mOpen: 0.85, mRound: 0.25, mWide: 0.6, mSmile: -0.2, mTeethU: 1, mTeethL: 0.8, mTongue: 1, pupil: 0.42, autoBlink: 0, saccade: 0 },
  ow: { lidU: 0.1, lidL: 0.9, browIn: 1, browOut: -0.35, browSq: 0.9, lidSad: 0.15, mSmile: -0.6, mWide: 0.7, mClench: 0.95, mTremble: 0.8, autoBlink: 0 },
  dazed: { lidU: 0.86, lidL: 0.05, lidAsym: 0.16, browIn: 0.45, browOut: -0.15, browAsym: -0.45, mSmile: 0.2, mOpen: 0.38, mAsym: -0.45, mWide: 0.25, mTongue: 0.9, saccade: 0, autoBlink: 0 },
  sulk: { lidU: 0.55, lidL: 0.22, lidSad: 0.55, browIn: 0.6, browOut: -0.35, browSq: 0.4, mSmile: -0.55, mPout: 0.7, mPress: 0.45, mAsym: 0.25 },
  annoyed: { lidU: 0.46, lidL: 0.2, lidAngry: 0.3, browIn: -0.5, browSq: 0.55, browOut: 0.1, mSmile: -0.3, mPress: 0.55, mAsym: -0.3 },
  startled: { lidU: 1.36, lidL: 0, browIn: 0.9, browOut: 0.7, mOpen: 0.3, mRound: 0.5, pupil: 0.5, saccade: 0 },
  curious: { lidU: 1.06, lidL: 0.2, browIn: 0.2, browOut: 0.6, browAsym: 0.5, mSmile: 0.3, mWide: 0.3, mAsym: 0.3, pupil: 1.1 },
};
export function MX(name, over = {}) {
  const base = { ...FACE_DEFAULTS };
  let list = Array.isArray(name) ? name : [[name, 1]];
  if (typeof list[0] === 'string') list = [list.length > 1 && typeof list[1] === 'number' ? [list[0], list[1]] : [list[0], 1]];   // ['gloat', 0.6]
  for (const [nm, w] of list) {
    const e = MEXPR[nm] || EXPR[nm] || {};
    for (const [key, val] of Object.entries(e)) base[key] = (base[key] ?? 0) + (val - (FACE_DEFAULTS[key] ?? 0)) * w;
  }
  return Object.assign(base, over);
}
function resolveFace(f) {
  if (f == null) return MX('sly');
  if (typeof f === 'string' || Array.isArray(f)) return MX(f);
  if (f.expr) { const { expr, ...rest } = f; return MX(expr, rest); }
  return { ...MX('rest'), ...f };
}

// ---------------------------------------------------------------------------------------------------------
// Arm presets, written for the LEFT arm (+x = the magician's left); mirrored for the right.
//   sp: 'chest' (default; origin = waist pivot, rotates with the hunched torso) | 'body' (t relative to the shoulder,
//   axes of the upright body: gravity presets) | 'head' (head-local: follows the head).
//   t = wrist target, pole = elbow direction, palm = palm normal, fing = finger direction, hand = Hand.pose params,
//   anim = procedural extra (tap / wiggle / rub / wave / stroke).
export const ARM = {
  rest: { sp: 'body', t: [0.05, -0.575, 0.07], pole: [0.3, 0, -1], palm: [-1, 0, 0.15], fing: [0.02, -1, 0.15], hand: { curl: 0.38, spread: 0.12, thumb: 0.25, cup: 0.3 } },
  hang: { sp: 'body', t: [0.07, -0.6, 0.16], pole: [0.4, 0, -1], palm: [-0.6, 0, -0.5], fing: [0.05, -1, 0.3], hand: { curl: 0.5, spread: 0.2, thumb: 0.2, cup: 0.3 } },
  hips: { sp: 'chest', t: [0.215, 0.0, -0.01], pole: [1, 0.2, -0.4], palm: [-0.45, 0, -1], fing: [-0.4, -0.75, 0.5], hand: { curl: 0.9, thumb: 0.2 } },
  behind: { sp: 'chest', t: [0.06, 0.02, -0.2], pole: [1, -0.2, -0.2], palm: [0.3, 0.2, -1], fing: [-0.8, -0.4, 0.1], hand: { curl: 0.5, thumb: 0.3 } },
  crossed: { sp: 'chest', t: [-0.075, 0.25, 0.17], pole: [1, -0.6, 0.1], palm: [0, -0.4, -1], fing: [-1, 0.2, -0.1], hand: { curl: 0.55, spread: 0.05, thumb: 0.3 } },
  steeple: { sp: 'chest', t: [0.12, 0.24, 0.27], pole: [1, -0.6, -0.1], palm: [-1, 0.1, 0.15], fing: [-0.3, 0.88, 0.3], hand: { curl: 0.06, spread: 0.2, thumb: 0.45 }, anim: 'steeple' },
  rub: { sp: 'chest', t: [0.05, 0.2, 0.27], pole: [1, -0.6, 0], palm: [-1, 0, 0.1], fing: [-0.2, 0.75, 0.6], hand: { curl: 0.12, spread: 0.08, thumb: 0.3 }, anim: 'rub' },
  creep: { sp: 'chest', t: [0.2, 0.42, 0.3], pole: [1, -0.3, -0.4], palm: [0, -1, 0.1], fing: [0.1, -0.55, 1], hand: { curl: 0.42, spread: 0.45, thumb: 0.3 }, anim: 'wiggle' },
  claw: { sp: 'chest', t: [0.24, 0.42, 0.32], pole: [1, -0.2, -0.4], palm: [0, -0.2, 1], fing: [0.15, 1, 0.1], hand: { curl: 0.55, spread: 0.55, thumb: 0.4 }, anim: 'wiggle' },
  edge: { sp: 'chest', t: [0.22, 0.38, 0.36], pole: [1, -0.4, -0.3], palm: [0, 0, 1], fing: [0, 1, 0.1], hand: { curl: 0.2, spread: 0.25, thumb: 0.35 }, anim: 'tap' },
  dagger_ready: { sp: 'chest', t: [0.17, 0.6, 0.16], pole: [1, -0.6, -0.3], palm: [-1, 0, 0.3], fing: [0.1, 0.3, 1], hand: { grip: 1 } },
  dagger_low: { sp: 'chest', t: [0.16, 0.12, 0.3], pole: [1, 0, -0.5], palm: [-1, 0, 0.1], fing: [0, -0.55, 0.85], hand: { grip: 1 } },
  dagger_stab: { sp: 'chest', t: [0.07, 0.3, 0.6], pole: [1, -0.3, -0.5], palm: [-1, 0, 0], fing: [0, -0.75, 0.65], hand: { grip: 1 } },
  pouch: { sp: 'chest', t: [0.17, 0.27, 0.32], pole: [1, -0.4, -0.4], palm: [-0.3, -0.6, 0.6], fing: [0, 0.3, 1], hand: { curl: 0.72, thumb: 0.7, cup: 0.3 } },
  pour: { sp: 'chest', t: [0.12, 0.33, 0.52], pole: [1, -0.3, -0.5], palm: [-0.4, -0.7, 0.4], fing: [-0.1, 0.1, 1], hand: { curl: 0.72, thumb: 0.7, cup: 0.3 } },
  present: { sp: 'chest', t: [0.52, 0.32, 0.2], pole: [0.4, -1, -0.4], palm: [0, 1, 0.25], fing: [1, 0.35, 0.3], hand: { curl: 0.05, spread: 0.55, thumb: 0.8, splay: 0.3 } },
  shrug: { sp: 'chest', t: [0.31, 0.12, 0.22], pole: [0.3, -1, -0.5], palm: [0.15, 1, 0.1], fing: [0.55, 0.05, 1], hand: { curl: 0.12, spread: 0.45, thumb: 0.75, splay: 0.1 } },
  up: { sp: 'chest', t: [0.24, 0.98, 0.12], pole: [1, 0, -0.4], palm: [0, 0, 1], fing: [0, 1, 0.05], hand: { curl: 0.06, spread: 0.45, thumb: 0.6, splay: 0.3 } },
  wave: { sp: 'chest', t: [0.33, 0.62, 0.2], pole: [1, -0.8, -0.2], palm: [0, 0, 1], fing: [0.08, 1, 0], hand: { curl: 0.05, spread: 0.35, thumb: 0.6 }, anim: 'wave' },
  point: { sp: 'chest', t: [0.18, 0.4, 0.62], pole: [1, -0.6, -0.3], palm: [-1, -0.2, 0], fing: [0, 0.1, 1], hand: { point: 1, thumb: 0.2, curl: 0.9 } },
  clutch_chest: { sp: 'chest', t: [0.04, 0.24, 0.17], pole: [1, -0.5, 0], palm: [0.15, 0, -1], fing: [-0.55, 0.8, 0], hand: { curl: 0.3, spread: 0.3, thumb: 0.4 } },
  clutch_back: { sp: 'chest', t: [0.11, 0.06, -0.16], pole: [1, 0, -0.2], palm: [-0.3, 0, 1], fing: [-0.4, -0.2, 0.2], hand: { curl: 0.3, spread: 0.3, thumb: 0.4 } },
  cover_mouth: { sp: 'head', t: [0.065, -0.1, 0.13], pole: [1, -0.8, 0], palm: [0, 0, -1], fing: [-0.9, 0.35, 0.05], hand: { curl: 0.22, spread: 0.1, thumb: 0.35, cup: 0.4 } },
  shush: { sp: 'head', t: [0.02, -0.21, 0.13], pole: [1, -0.8, -0.2], palm: [-0.2, 0, -1], fing: [-0.05, 1, 0.1], hand: { point: 1, thumb: 0.25, curl: 0.85 } },
  whisper: { sp: 'head', t: [0.1, -0.15, 0.1], pole: [1, -0.8, -0.2], palm: [-1, 0, 0.35], fing: [0.05, 1, 0.25], hand: { curl: 0.2, spread: 0.05, thumb: 0.3, cup: 0.55 } },
  pocket: { sp: 'hip', t: [0.128, -0.015, 0.035], pole: [0.6, 0, -1], palm: [-1, 0, 0.1], fing: [-0.15, -1, 0.25], hand: { curl: 0.15, spread: 0.05, thumb: 0.15 } },
  chin: { sp: 'head', t: [0.03, -0.22, 0.05], pole: [1, -0.9, 0], palm: [-0.4, 0.2, -0.6], fing: [-0.3, 0.55, 0.75], hand: { curl: 0.55, thumb: 0.5, point: 0.3 }, anim: 'stroke' },
};
const HAND_KEYS = ['curl', 'point', 'spread', 'thumb', 'cup', 'splay', 'grip', 'pinch', 'tap'];
const HAND_DEF = { curl: 0.2, point: 0, spread: 0.15, thumb: 0.3, cup: 0.1, splay: 0, grip: 0, pinch: 0, tap: 0 };

// Gaits. stride = metres per full cycle (body speed = stride * rate m/s), stance = stance fraction of a cycle.
export const GAIT = {
  walk: { rate: 0.8, stride: 0.95, stance: 0.6, lift: 0.085, bob: 0.02, sway: 0.018, twist: 0.12, lean: 0.03, arm: 0.17, heel: 0, crouch: 0, run: 0 },
  sneak: { rate: 0.55, stride: 0.72, stance: 0.5, lift: 0.2, bob: 0.04, sway: 0.03, twist: 0.08, lean: 0.12, arm: 0, heel: 0.6, crouch: 0.28, run: 0, knee: 1 },
  tiptoe: { rate: 0.9, stride: 0.55, stance: 0.55, lift: 0.1, bob: 0.03, sway: 0.02, twist: 0.06, lean: 0.04, arm: 0.05, heel: 0.75, crouch: 0.05, run: 0 },
  run: { rate: 1.45, stride: 2.0, stance: 0.38, lift: 0.22, bob: 0.05, sway: 0.012, twist: 0.2, lean: 0.1, arm: 0.42, heel: 0, crouch: 0.05, run: 1 },
  stomp: { rate: 0.85, stride: 0.8, stance: 0.6, lift: 0.13, bob: 0.04, sway: 0.025, twist: 0.1, lean: 0.08, arm: 0.22, heel: 0, crouch: 0.06, run: 0 },
  waddle: { rate: 1.0, stride: 0.45, stance: 0.6, lift: 0.06, bob: 0.02, sway: 0.06, twist: 0.05, lean: 0.0, arm: 0.1, heel: 0, crouch: 0.03, run: 0 },
  limp: { rate: 0.62, stride: 0.5, stance: 0.62, lift: 0.07, bob: 0.018, sway: 0.03, twist: 0.08, lean: 0.06, arm: 0.06, heel: 0, crouch: 0.04, run: 0, limp: 1 },
};
function footCycle(u, S, bad) {
  const sf = S.stance, L = S.stride * sf;
  let z, lift = 0, pitch = 0;
  if (u < sf) {
    const a = u / sf;
    z = lerp(0.5, -0.5, a) * L;
    if (S.heel > 0) pitch = S.heel * (0.85 + 0.25 * Math.sin(Math.PI * a));
    else pitch = a < 0.15 ? lerp(-0.25, 0, smooth(a / 0.15)) : a > 0.62 ? lerp(0, 0.55 + 0.3 * S.run, smooth((a - 0.62) / 0.38)) : 0;
  } else {
    const b = (u - sf) / (1 - sf);
    z = lerp(-0.5, 0.5, smooth(b)) * L;
    lift = Math.pow(Math.sin(Math.PI * b), 1.25) * S.lift * (bad ? 0.35 : 1);
    if (S.heel > 0) pitch = S.heel + 0.45 * Math.sin(Math.PI * b);
    else pitch = lerp(0.55 + 0.3 * S.run, -0.25, smooth(b)) + 0.2 * Math.sin(Math.PI * b);
    if (bad) pitch *= 0.3;
  }
  return { z, lift, pitch };
}
// ankle for a foot planted at nominal ankle (x, z) with pitch (heel up > 0 pivots on the ball of the foot)
function plantAnkle(x, z, lift, pitch, out) {
  let y = ANKLE_Y, zz = z;
  if (pitch > 0) { const bz = z + 0.12; y = ANKLE_Y * Math.cos(pitch) + 0.12 * Math.sin(pitch); zz = bz + ANKLE_Y * Math.sin(pitch) - 0.12 * Math.cos(pitch); }
  else if (pitch < 0) { const hz = z - 0.05; y = ANKLE_Y * Math.cos(pitch) - 0.05 * Math.sin(pitch); zz = hz + ANKLE_Y * Math.sin(pitch) + 0.05 * Math.cos(pitch); }
  return out.set(x, y + lift, zz);
}

// ---------------------------------------------------------------------------------------------------------
// Materials
// Perf: MeshStandardMaterial by default (SwiftShader is fill-rate bound); physical (sheen / clearcoat) only when asked.
function gloom(color, o = {}) {
  const base = { color: new THREE.Color(color), roughness: o.roughness ?? 0.82, metalness: o.metalness ?? 0, side: o.side ?? THREE.FrontSide };
  const m = o.physical ? new THREE.MeshPhysicalMaterial({ ...base,
    sheen: o.sheen ?? 0.45, sheenColor: new THREE.Color(o.sheenColor ?? 0xa9b6d6), sheenRoughness: o.sheenRoughness ?? 0.5,
    clearcoat: o.clearcoat ?? 0, clearcoatRoughness: o.ccRough ?? 0.35 }) : new THREE.MeshStandardMaterial(base);
  enhance(m, { rim: o.rim ?? 0.55, rimColor: o.rimColor ?? C.cold, rimPower: o.rimPower ?? 2.6, glow: o.glow ?? 0.05,
    fizz: 0, wrap: o.wrap ?? 0.25, wrapColor: o.wrapColor ?? 0x7f92c8, jaw: o.jaw });
  return o.fizz ? fizzLite(m, o.fizz, o.fizzColor ?? 0xb5c3e6, o.fizzScale ?? 9) : m;
}
// Cheap effervescent shimmer (the BIBLE's 'made of gloom' fizz): ONE octave of core's value noise (vh_noise, already in
// the enhance() shader), slowly drifting -> soft low-contrast mottling + sparse soft glints, stronger toward the rim.
// A third of core's 3-octave fbm fizz (which A/B'd at ~15% of a close-up frame on SwiftShader). (A sine-product
// version was cheaper still but read as a regular polka-dot lattice on the coat.)
function fizzLite(mat, amt, color, scale) {
  const prev = mat.onBeforeCompile, key = mat.customProgramCacheKey();
  const u = { uFzA: { value: amt }, uFzC: { value: new THREE.Color(color) }, uFzS: { value: scale } };
  mat.userData.uniforms.uFizzLite = u.uFzA;
  mat.onBeforeCompile = (sh) => {
    prev(sh);
    Object.assign(sh.uniforms, u);
    const anchor = 'totalEmissiveRadiance += uWrapColor * uWrap * pow(fres, 1.5) * 0.35;';
    if (!sh.fragmentShader.includes(anchor)) return;           // core changed: just no fizz
    sh.fragmentShader = sh.fragmentShader.replace('uniform vec3 uRimColor', 'uniform float uFzA, uFzS; uniform vec3 uFzC;\n        uniform vec3 uRimColor')
      .replace(anchor, `${anchor}
          { float n = vh_noise(vObjPos * uFzS + vec3(0.0, uTime * 0.22, uTime * 0.13));
            totalEmissiveRadiance += uFzC * uFzA * (0.4 * n + 0.8 * smoothstep(0.62, 0.92, n)) * (0.5 + 0.5 * fres); }`);
  };
  mat.customProgramCacheKey = () => key + 'FZL';
  return mat;
}
// vertical pinstripes: per-vertex aRing = (cos, sin) of the around-angle (seam-free), anti-aliased with fwidth
function striped(mat, n = 8, dark = 0.52) {
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh) => {
    prev(sh);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec2 aRing; varying vec2 vRing;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvRing = aRing;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec2 vRing;')
      .replace('#include <color_fragment>', `#include <color_fragment>
        { float a = atan(vRing.y, vRing.x); float sv = sin(a * ${n.toFixed(1)}); float fw = fwidth(sv) + 0.04;
          float st = smoothstep(-fw, fw, sv); st = mix(st, 0.5, smoothstep(0.6, 1.2, fw));
          diffuseColor.rgb *= mix(${dark.toFixed(3)}, 1.0, st); }`);
  };
  const key = mat.customProgramCacheKey();
  mat.customProgramCacheKey = () => key + 'STRIPE' + n;
  return mat;
}
function ringAttr(tube) {
  const n = tube.rings * tube.R + 2, a = new Float32Array(n * 2);
  for (let r = 0; r < tube.rings; r++) for (let j = 0; j < tube.R; j++) { const ang = (j / tube.R) * TAU; a[(r * tube.R + j) * 2] = Math.cos(ang); a[(r * tube.R + j) * 2 + 1] = Math.sin(ang); }
  a[(n - 2) * 2] = 1; a[(n - 1) * 2] = 1;
  tube.geo.setAttribute('aRing', new THREE.BufferAttribute(a, 2));
}
// deformed sphere: fn(a = around (0 = +Z front, +pi/2 = +X), s = 0 bottom .. 1 top, out) -> position
function deformSphere(wS, hS, fn, ring = false) {
  const g = new THREE.SphereGeometry(1, wS, hS);
  g.deleteAttribute('uv'); g.deleteAttribute('normal');
  const P = g.attributes.position, v = V(), out = V();
  for (let i = 0; i < P.count; i++) {
    v.fromBufferAttribute(P, i);
    const s = 1 - Math.acos(clamp(v.y, -1, 1)) / Math.PI;
    const a = Math.atan2(v.x, v.z);
    fn(a, s, out); P.setXYZ(i, out.x, out.y, out.z);
  }
  const geo = mergeVertices(g); geo.computeVertexNormals();
  if (ring) {
    const Q = geo.attributes.position, r = new Float32Array(Q.count * 2);
    for (let i = 0; i < Q.count; i++) { const a = Math.atan2(Q.getX(i), Q.getZ(i)); r[i * 2] = Math.cos(a); r[i * 2 + 1] = Math.sin(a); }
    geo.setAttribute('aRing', new THREE.BufferAttribute(r, 2));
  }
  return geo;
}
const se = (c, n) => Math.sign(c) * Math.pow(Math.abs(c), 2 / n);   // superellipse

// ---------------------------------------------------------------------------------------------------------
// GloveHand — the magician's own glove (replaces core Hand for this rig): ONE skinned mesh per hand (palm, four
// long tapered fingers with fat roots + webbing, opposable thumb with a thenar pad, flared gauntlet cuff), so
// joints bend smoothly instead of reading as separate capsules, and a hand costs 1 draw call instead of 15.
// Same interface as core Hand: root (wrist at origin, fingers +Y, palm faces -Z), aim(fingerDir, palmNormal),
// pose({ curl, point, spread, thumb, cup, splay, grip, pinch, perFinger }).
// Correct chirality: the thumb sits on the INDEX side (right hand: thumb at -X local; left hand: +X).
const _gh = V(), _pv = V();
const GL = {
  FX: [0.0272, 0.0092, -0.0090, -0.0262], FY: [0.0835, 0.0868, 0.0848, 0.0785],     // knuckles (x * thumb side)
  LEN: [[0.046, 0.034, 0.028], [0.050, 0.037, 0.029], [0.048, 0.035, 0.028], [0.038, 0.027, 0.024]],
  RAD: [0.0104, 0.0108, 0.0103, 0.0094],                                                 // finger root radii
  LAT: [1.5, 0.5, -0.5, -1.5],
  FIST: [[1.36, 1.62, 1.05], [1.4, 1.66, 1.0], [1.44, 1.64, 0.98], [1.5, 1.6, 0.95]],  // grip: fingertips close on the palm
};
function thumbDir(th, a, b) { return V(th * Math.sin(a) * Math.cos(b), Math.cos(a) * Math.cos(b), -Math.sin(b)); }
function thumbQuat(th, a, b, out = new THREE.Quaternion()) {
  const d = thumbDir(th, a, b), m = V(-th, -0.1, -0.75);
  m.addScaledVector(d, -m.dot(d)).normalize();
  const x = V().crossVectors(d, m).normalize(), z = V().crossVectors(x, d).normalize();
  return out.setFromRotationMatrix(_m1.makeBasis(x, d, z));
}
class GloveHand {
  constructor({ side = 'R', material, cuffMaterial, castShadow = false } = {}) {
    this.side = side; this.size = HAND_SIZE;
    const th = this.th = side === 'R' ? -1 : 1;
    this.root = new THREE.Group();
    const bones = [];
    const bone = (parent, p) => { const b = new THREE.Bone(); b.position.copy(p); b.rotation.order = 'ZXY'; (parent || this.root).add(b); bones.push(b); return b; };
    const palmB = bone(null, V());
    const BI = (b) => bones.indexOf(b);
    const parts = [];
    // tube part builder: rings = [{ c, X, Z, rx, rz, w: [[bone, weight], ...] }], closed with caps (pole vertices)
    const tube = (rings, R, capStart = true, capEnd = true) => {
      const pos = [], si = [], sw = [], idx = [];
      const pushV = (p, w) => {
        pos.push(p.x, p.y, p.z);
        const ww = w.filter((e) => e[1] > 1e-4).slice(0, 4); let s = 0; for (const e of ww) s += e[1];
        for (let k = 0; k < 4; k++) { si.push(ww[k] ? BI(ww[k][0]) : 0); sw.push(ww[k] ? ww[k][1] / s : 0); }
      };
      for (const r of rings) for (let j = 0; j < R; j++) {
        const a = (j / R) * TAU;
        pushV(r.c.clone().addScaledVector(r.X, Math.cos(a) * r.rx).addScaledVector(r.Z, Math.sin(a) * r.rz), r.w);
      }
      for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < R; j++) {
        const a = i * R + j, b = i * R + (j + 1) % R, c = a + R, d = b + R; idx.push(a, c, b, b, c, d);
      }
      if (capStart) { const r = rings[0], n = V().crossVectors(r.Z, r.X).normalize(); const p0 = pos.length / 3; pushV(r.c.clone().addScaledVector(n, -0.0005), r.w); for (let j = 0; j < R; j++) idx.push(p0, j, (j + 1) % R); }
      if (capEnd) { const L = rings.length - 1, r = rings[L], p0 = pos.length / 3; pushV(r.c, r.w); for (let j = 0; j < R; j++) idx.push(p0, L * R + (j + 1) % R, L * R + j); }
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4));
      g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
      g.setIndex(idx); parts.push(g);
    };
    const bl = (y, j, h) => smooth((y - (j - h)) / (2 * h));
    const X0 = V(1, 0, 0), Z0 = V(0, 0, 1);
    // ---- fingers
    this.fingers = [];
    for (let i = 0; i < 4; i++) {
      const [l0, l1, l2] = GL.LEN[i], r0 = GL.RAD[i], base = V(th * GL.FX[i], GL.FY[i], 0.0015);
      const b0 = bone(palmB, base), b1 = bone(b0, V(0, l0, 0)), b2 = bone(b1, V(0, l1, 0));
      this.fingers.push({ b: [b0, b1, b2], lat: GL.LAT[i], len: [l0, l1, l2] });
      const L = l0 + l1 + l2, rings = [];
      const ys = [-0.02, -0.012, -0.005, 0.002, 0.01, l0 * 0.55, l0 - 0.005, l0, l0 + 0.005, l0 + l1 * 0.5, l0 + l1 - 0.004, l0 + l1, l0 + l1 + 0.004, l0 + l1 + l2 * 0.5, L - r0 * 0.75];
      const rad = (y) => {
        let r = lerp(r0 * 1.12, r0 * 0.68, smoothstep(0, L, y));                      // fat root, thin tip
        r *= 1 + 0.06 * Math.exp(-(((y - l0) / 0.006) ** 2)) + 0.05 * Math.exp(-(((y - l0 - l1) / 0.005) ** 2)); // soft knuckles
        return r;
      };
      for (const y of ys) {
        const a0 = bl(y, 0.003, 0.009), a1 = bl(y, l0, 0.0065), a2 = bl(y, l0 + l1, 0.0055);
        rings.push({ c: base.clone().add(V(0, y, 0)), X: X0, Z: Z0, rx: rad(y), rz: rad(y) * 0.86,
          w: [[palmB, 1 - a0], [b0, a0 * (1 - a1)], [b1, a0 * a1 * (1 - a2)], [b2, a0 * a1 * a2]] });
      }
      const rt = rad(L) * 0.9;     // rounded fingertip
      for (let k = 1; k <= 3; k++) { const an = (k / 4) * Math.PI / 2; rings.push({ c: base.clone().add(V(0, L - r0 * 0.75 + Math.sin(an) * rt, 0)), X: X0, Z: Z0, rx: Math.cos(an) * rt, rz: Math.cos(an) * rt * 0.86, w: [[b2, 1]] }); }
      tube(rings, 10, false, true);
      this.fingers[i].tip = V(0, l2 + rt * 0.2, -rt * 0.5);
    }
    // ---- thumb (metacarpal inside a thenar pad, proximal + distal phalanx)
    this.TB = V(th * 0.0205, 0.017, -0.0045); this.TA = [0.62, 0.38];
    const tq0 = thumbQuat(th, ...this.TA), d0 = thumbDir(th, ...this.TA);
    const tX = V(1, 0, 0).applyQuaternion(tq0), tZ = V(0, 0, 1).applyQuaternion(tq0);
    const tm = bone(palmB, this.TB); tm.quaternion.copy(tq0);
    const LM = 0.033, LP = 0.03, LD = 0.025;
    const tp = bone(tm, V(0, LM, 0)), td = bone(tp, V(0, LP, 0));
    this.thumb = { b: [tm, tp, td], tip: V(0, LD, -0.004) };
    {
      const rings = [], Lt = LM + LP + LD;
      const ys = [-0.006, 0.004, 0.014, 0.024, LM - 0.004, LM + 0.003, LM + LP * 0.5, LM + LP - 0.004, LM + LP + 0.003, LM + LP + LD * 0.5, Lt - 0.008];
      const rad = (y) => lerp(0.0142, 0.0092, smoothstep(0, LM + 0.006, y)) * (1 - 0.18 * smoothstep(LM + LP, Lt, y)) * (1 + 0.05 * Math.exp(-(((y - LM - LP) / 0.005) ** 2)));
      for (const y of ys) {
        const a0 = bl(y, 0.012, 0.012), a1 = bl(y, LM, 0.006), a2 = bl(y, LM + LP, 0.005);
        rings.push({ c: this.TB.clone().addScaledVector(d0, y), X: tX, Z: tZ, rx: rad(y) * 0.92, rz: rad(y),
          w: [[palmB, 1 - a0], [tm, a0 * (1 - a1)], [tp, a1 * (1 - a2)], [td, a2]] });
      }
      const rt = rad(Lt) * 0.95;
      for (let k = 1; k <= 3; k++) { const an = (k / 4) * Math.PI / 2; rings.push({ c: this.TB.clone().addScaledVector(d0, Lt - 0.008 + Math.sin(an) * rt), X: tX, Z: tZ, rx: Math.cos(an) * rt * 0.92, rz: Math.cos(an) * rt, w: [[td, 1]] }); }
      tube(rings, 10, true, true);
    }
    // ---- palm: rounded slab, domed back, knuckle edge weighted toward the finger roots (bends with a fist)
    {
      const NA = 22, NY = 12, rings = [];
      for (let k = 0; k <= NY; k++) {
        const s = k / NY, y = lerp(-0.006, 0.093, s);
        const top = smoothstep(0.072, 0.093, y);
        const hx = lerp(0.0245, 0.0355, smoothstep(-0.004, 0.06, y)) * (1 - 0.35 * top * top);
        const hz = 0.0128 * (1 - 0.55 * top * top);
        // per-ring we need per-vertex weights -> build vertex-wise via a custom ring list
        rings.push({ y, hx, hz });
      }
      const pos = [], si = [], sw = [], idx = [];
      for (const r of rings) for (let j = 0; j < NA; j++) {
        const a = (j / NA) * TAU, ca = Math.cos(a), sa = Math.sin(a);
        const x = r.hx * se(ca, 3.2), back = sa > 0;
        let z = (back ? r.hz * 1.08 : r.hz * 0.92) * se(sa, back ? 2.4 : 3.4);
        // thenar pad: palm side, thumb side, low
        const then = (!back ? 1 : 0.3) * smoothstep(0, 1, (th * x) / r.hx) * (1 - smoothstep(0.02, 0.06, r.y));
        z -= 0.006 * then * Math.abs(sa);
        pos.push(x, r.y, z);
        // weights: knuckle band follows the nearest finger's proximal bone
        let fi = 0, best = 1e9; for (let i = 0; i < 4; i++) { const dd = Math.abs(x - th * GL.FX[i]); if (dd < best) { best = dd; fi = i; } }
        const kw = 0.55 * smoothstep(0.068, 0.09, r.y), tw = 0.5 * then;
        const ww = [[0, 1 - kw - tw], [BI(this.fingers[fi].b[0]), kw], [BI(tm), tw]];
        for (let k = 0; k < 4; k++) { si.push(ww[k] ? ww[k][0] : 0); sw.push(ww[k] ? Math.max(0, ww[k][1]) : 0); }
      }
      for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < NA; j++) { const a = i * NA + j, b = i * NA + (j + 1) % NA, c = a + NA, d = b + NA; idx.push(a, c, b, b, c, d); }
      const p0 = pos.length / 3; pos.push(0, 0.094, 0); si.push(0, 0, 0, 0); sw.push(1, 0, 0, 0);
      const L = rings.length - 1; for (let j = 0; j < NA; j++) idx.push(p0, L * NA + (j + 1) % NA, L * NA + j);
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4));
      g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
      g.setIndex(idx); parts.push(g);
    }
    // ---- gauntlet cuff (flares into the sleeve, closed at the far end)
    {
      const rings = [];
      for (const [y, rx, rz] of [[0.006, 0.0262, 0.0158], [-0.004, 0.0272, 0.0178], [-0.016, 0.0292, 0.022], [-0.03, 0.0318, 0.027], [-0.044, 0.0336, 0.0305], [-0.05, 0.0338, 0.031]])
        rings.push({ c: V(0, y, 0.0005), X: X0, Z: Z0, rx, rz, w: [[palmB, 1]] });
      rings.reverse(); rings.push({ c: V(0, 0.0065, 0.0005), X: X0, Z: Z0, rx: 0.019, rz: 0.0105, w: [[palmB, 1]] });   // inward lip closes the top
      tube(rings, 18, true, false);
    }
    const geo = mergeGeometries(parts);
    geo.computeVertexNormals();
    this.mesh = new THREE.SkinnedMesh(geo, material);
    this.mesh.frustumCulled = false; this.mesh.castShadow = castShadow;
    this.root.add(this.mesh);
    this.root.updateMatrixWorld(true);
    this.mesh.bind(new THREE.Skeleton(bones), new THREE.Matrix4());
    // shirt cuff: a closed (lathe) ring, so no open-cylinder backfaces
    if (cuffMaterial) {
      const prof = [[0.0335, -0.012], [0.037, -0.011], [0.0385, -0.004], [0.0385, 0.004], [0.037, 0.011], [0.0335, 0.012], [0.0335, -0.012]].map(([r, y]) => new THREE.Vector2(r, y));
      const sc = new THREE.Mesh(new THREE.LatheGeometry(prof, 20), cuffMaterial);
      sc.position.y = -0.052; sc.scale.set(1, 1, 0.92); this.root.add(sc); this.shirtCuff = sc;
    }
    // grip frame: the dagger handle axis (local X) sits in the crease inside the curled fingers
    this.grip = new THREE.Object3D(); this.grip.position.set(th * 0.002, 0.066, -0.0275); this.root.add(this.grip);
    this.pose({});
  }
  aim(fingerDir, palmNormal) { return orientYZ(this.root, fingerDir, _gh.copy(palmNormal).multiplyScalar(-1)); }
  pose({ curl = 0.2, point = 0, spread = 0.15, thumb = 0.3, cup = 0.1, splay = 0, grip = 0, pinch = 0, perFinger = null } = {}) {
    const th = this.th;
    grip = clamp(grip); pinch = clamp(pinch) * (1 - grip);
    this.fingers.forEach((f, i) => {
      let c = perFinger ? perFinger[i] : curl;
      c = lerp(c, i === 0 ? 0 : 1, clamp(point));
      let b0 = c * 1.42 + cup * 0.22 - splay * 0.32, b1 = c * 1.6 + cup * 0.3 - splay * 0.1, b2 = c * 1.02 + cup * 0.2 - splay * 0.06;
      if (pinch > 0) { const P = [[1.0, 0.9, 0.4], [1.12, 1.0, 0.45], [1.3, 1.5, 0.9], [1.35, 1.5, 0.9]][i]; b0 = lerp(b0, P[0], pinch); b1 = lerp(b1, P[1], pinch); b2 = lerp(b2, P[2], pinch); }
      const G = GL.FIST[i];
      b0 = lerp(b0, G[0], grip); b1 = lerp(b1, G[1], grip); b2 = lerp(b2, G[2], grip);
      const sp = -th * f.lat * 0.15 * (spread + 0.7 * splay) * (1 - grip) * (1 - 0.6 * pinch);
      f.b[0].rotation.set(-b0, 0, sp); f.b[1].rotation.set(-b1, 0, 0); f.b[2].rotation.set(-Math.max(-0.25, b2), 0, 0);
    });
    // thumb: abduction a (0 = along the index .. 1.15 = out), opposition b (toward the palm), flexion of both phalanges
    const tOut = clamp(thumb);
    let a = lerp(0.3, 1.12, tOut) + 0.15 * splay, b = 0.22 + 0.3 * cup + 0.25 * curl * (1 - tOut);
    let f1 = 0.12 + 0.45 * curl * (1 - tOut) - 0.2 * splay, f2 = 0.1 + 0.5 * curl * (1 - tOut) - 0.25 * splay;
    a = lerp(a, -0.06, grip); b = lerp(b, 0.8, grip); f1 = lerp(f1, 0.3, grip); f2 = lerp(f2, 0.6, grip);
    a = lerp(a, 0.5, pinch); b = lerp(b, 0.68, pinch); f1 = lerp(f1, 0.3, pinch); f2 = lerp(f2, 0.3, pinch);
    const tk = clamp(point) * 0.85;                                       // pointing: thumb tucks over the curled fingers
    a = lerp(a, 0.2, tk); b = lerp(b, 0.85, tk); f1 = lerp(f1, 0.45, tk); f2 = lerp(f2, 0.5, tk);
    thumbQuat(th, a, b, this.thumb.b[0].quaternion);
    this.thumb.b[1].rotation.set(f1, 0, 0); this.thumb.b[2].rotation.set(f2, 0, 0);
    return this;
  }
  /** fingertip world positions (call after the hand's world matrix is current): i = 0..3 fingers, 'thumb' */
  tipWorld(i, out = V()) {
    const f = i === 'thumb' ? this.thumb : this.fingers[i];
    const b = f.b[2]; b.updateWorldMatrix(true, false);
    return out.copy(f.tip).applyMatrix4(b.matrixWorld);
  }
}


// chest coat profile (chest-local): [h, rx, rzFront, rzBack, zCentre]
const CHEST = [
  [-0.07, 0.098, 0.082, 0.086, 0.0], [0.02, 0.103, 0.086, 0.09, 0.0], [0.12, 0.122, 0.094, 0.1, -0.006],
  [0.22, 0.138, 0.098, 0.116, -0.012], [0.3, 0.156, 0.094, 0.126, -0.018], [0.36, 0.168, 0.086, 0.118, -0.022],
  [0.405, 0.152, 0.072, 0.098, -0.022], [0.44, 0.1, 0.055, 0.066, -0.016], [0.462, 0.03, 0.03, 0.03, -0.01],
];
// hips/trousers profile (pelvis-local): [h, rx, rzF, rzB]
// (wide enough at the seat to swallow the tops of the leg tubes, narrowing into the crotch between them)
const HIPS = [[-0.155, 0.03, 0.03, 0.034], [-0.125, 0.075, 0.06, 0.07], [-0.075, 0.122, 0.077, 0.088], [0.0, 0.127, 0.082, 0.092], [0.08, 0.113, 0.081, 0.086], [0.17, 0.097, 0.075, 0.079]];

// ---------------------------------------------------------------------------------------------------------
class Magician extends Character {
  constructor() {
    super({ name: 'MAGICIAN', speaker: 'MAGICIAN', height: 2.1, seed: 31 });
    this.rootInv = new THREE.Matrix4(); this.rootQInv = new THREE.Quaternion();
    this.Mb = new THREE.Matrix4(); this.Mp = new THREE.Matrix4(); this.Mc = new THREE.Matrix4(); this.Mh = new THREE.Matrix4();
    this._mats();
    this._skeleton();
    this._buildTorso();
    this._buildHead();
    this._buildHat();
    this._buildLimbs();
    this._buildTails();
    this._buildProps();
    this._buildFx();
    this._buildAnchors();
    this.update(0, {});
  }
  walkSpeed(style = 'walk') { return (GAIT[style] || GAIT.walk).stride; }
  walkRate(style = 'walk') { return (GAIT[style] || GAIT.walk).rate; }

  // ------------------------------------------------------------------ materials
  _mats() {
    // MeshStandard everywhere (physical only on the velvet pouch + wet tongue, where sheen / clearcoat actually show).
    // Gloom look: cold fresnel rim on every silhouette + a faint, slow, low-contrast fizz on the coat and skin.
    const FZ = { fizz: 0.04, fizzColor: 0xb9c6ea, fizzScale: 9 };
    this.faceMat = gloom(C.face, { roughness: 0.52, rim: 0.85, glow: 0.07, wrap: 0.38, jaw: JAW, ...FZ });
    this.skinMat = gloom(C.face, { roughness: 0.52, rim: 0.85, glow: 0.07, wrap: 0.38, ...FZ });
    this.lidMat = gloom(C.socket, { roughness: 0.6, rim: 0.35, glow: 0.04 });
    this.coatMat = gloom(C.coat, { rim: 0.78, wrap: 0.35, ...FZ, fizz: 0.045 });
    this.coat2Mat = gloom(C.coat, { rim: 0.65, wrap: 0.35, side: THREE.DoubleSide, ...FZ, fizz: 0.045 });
    this.lapelMat = gloom(C.lapel, { roughness: 0.3, metalness: 0.15, rim: 0.55 });            // satin-ish lapels / waistcoat
    this.shirtMat = gloom(C.shirt, { roughness: 0.75, rim: 0.45, glow: 0.06 });
    this.cravatMat = gloom(C.cravat, { roughness: 0.42, rim: 0.45 });
    this.gloveMat = gloom(C.glove, { roughness: 0.6, rim: 0.5, glow: 0.07 });
    this.trouserMat = striped(gloom(C.stripeA, { roughness: 0.85, rim: 0.55 }), 8, 0.5);
    this.hatMat = gloom(C.hat, { roughness: 0.62, rim: 0.7 });
    this.bandMat = gloom(C.band, { roughness: 0.32, metalness: 0.2, rim: 0.35 });
    this.shoeMat = gloom(C.shoe, { roughness: 0.18, metalness: 0.25, rim: 0.6 });                 // glossy patent shoes
    this.hairMat = gloom(C.hair, { roughness: 0.38, rim: 0.45 });
    this.mothMat = gloom(0x9c9688, { roughness: 0.9, rim: 0.5, glow: 0.05, side: THREE.DoubleSide });
    this.velvetMat = gloom(C.velvet, { physical: true, roughness: 0.9, sheen: 1, sheenColor: 0xa992cc, sheenRoughness: 0.35, rim: 0.55, rimColor: 0xb7a6e6 });
    this.bladeMat = gloom(C.blade, { roughness: 0.3, metalness: 0.2, rim: 1.1, rimColor: 0xd8e6ff, glow: 0.36, fizz: 0 }); this.bladeMat.vertexColors = true;
    this.darkMat = gloom(0x23252e, { roughness: 0.5, rim: 0.3, fizz: 0 });
    this.tongueMat = new THREE.MeshPhysicalMaterial({ color: C.tongue, roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.12 });
    enhance(this.tongueMat, { rim: 0.45, rimColor: 0xc9c0e0, glow: 0.06, wrap: 0.35, wrapColor: 0x9a86aa });
    this.droolMat = new THREE.MeshStandardMaterial({ color: 0xe4ebf4, roughness: 0.06, metalness: 0.1, transparent: true, opacity: 0.62, emissive: 0x3a4250 });
    this._rims = [this.faceMat, this.skinMat, this.coatMat, this.coat2Mat, this.lapelMat, this.shirtMat, this.cravatMat, this.gloveMat, this.trouserMat, this.hatMat, this.shoeMat, this.hairMat, this.velvetMat]
      .map((m) => [m, m.userData.uniforms.uRim.value]);
  }

  _skeleton() {
    this.bodyG = new THREE.Group(); this.root.add(this.bodyG);          // whole-body pivot (flight / crash)
    this.pelvisG = new THREE.Group(); this.bodyG.add(this.pelvisG);
    this.chestG = new THREE.Group(); this.pelvisG.add(this.chestG);
    this.chestG.position.y = WAIST;
    this.headG = new THREE.Group(); this.root.add(this.headG);           // placed explicitly (root-local)
    this.headGroup = this.headG;
    this.headG.scale.setScalar(HEAD_S);
    for (const g of [this.pelvisG, this.chestG]) g.rotation.order = 'YXZ';
  }

  // ------------------------------------------------------------------ torso: chest coat, hips, collar, shirt, cravat
  _buildTorso() {
    const chestGeo = deformSphere(44, 30, (a, s, out) => {
      const h = lerp(CHEST[0][0], CHEST[CHEST.length - 1][0], s);
      const rx = pw(CHEST, h, 1), rzF = pw(CHEST, h, 2), rzB = pw(CHEST, h, 3), zc = pw(CHEST, h, 4);
      const k = rounded(s / 0.05);
      const sx = se(Math.sin(a), 2.5), cz = se(Math.cos(a), 2.5);
      const droop = 0.045 * sx * sx * smoothstep(0.28, 0.44, h);         // sloped, sad shoulders
      out.set(rx * sx * k, h - droop, zc + (cz >= 0 ? rzF : rzB) * cz * k);
    });
    const chest = new THREE.Mesh(chestGeo, this.coatMat); chest.castShadow = true;
    this.chestG.add(chest);
    // hips (striped trousers)
    const hipGeo = deformSphere(36, 20, (a, s, out) => {
      const h = lerp(HIPS[0][0], HIPS[HIPS.length - 1][0], s);
      const rx = pw(HIPS, h, 1), rzF = pw(HIPS, h, 2), rzB = pw(HIPS, h, 3);
      const k = rounded((1 - s) / 0.06);
      const sx = se(Math.sin(a), 2.3), cz = se(Math.cos(a), 2.3);
      out.set(rx * sx * k, h, (cz >= 0 ? rzF : rzB) * cz * k);
    }, true);
    const hips = new THREE.Mesh(hipGeo, this.trouserMat); hips.castShadow = true;
    this.pelvisG.add(hips);
    // dark waistcoat band over the waist seam: hides where coat, hips and leg tubes meet; pointed at the front
    const vestGeo = deformSphere(36, 16, (a, s2, out) => {
      const y = lerp(-0.075, 0.15, s2), ca = Math.cos(a);
      const ybot = -0.004 - 0.042 * Math.pow(Math.max(0, ca), 6), ytop = 0.13;
      const inn = smoothstep(ybot - 0.006, ybot + 0.004, y) * (1 - smoothstep(ytop, ytop + 0.02, y));
      const rx = pw(HIPS, y, 1) + lerp(-0.014, 0.007, inn), rzF = pw(HIPS, y, 2) + lerp(-0.014, 0.009, inn), rzB = pw(HIPS, y, 3) + lerp(-0.014, 0.007, inn);
      const sx = se(Math.sin(a), 2.3), cz = se(ca, 2.3);
      out.set(rx * sx, y, (cz >= 0 ? rzF : rzB) * cz);
    });
    this.pelvisG.add(new THREE.Mesh(vestGeo, this.lapelMat));
    // shirt front, lapels, buttons, wilted bow tie — merged per material
    const gs = (p, sc, r = [0, 0, 0], seg = [20, 14]) => {
      const g = new THREE.SphereGeometry(1, seg[0], seg[1]); g.deleteAttribute('uv');
      return g.applyMatrix4(new THREE.Matrix4().compose(V(...p), new THREE.Quaternion().setFromEuler(new THREE.Euler(...r)), V(...sc)));
    };
    // a sad, WILTED bow tie: small knot, two floppy lobes drooping toward the floor
    const lobe = (k) => {
      const g = deformSphere(16, 12, (a, s2, out) => {
        const r = 0.021 * Math.pow(Math.sin(Math.PI * Math.pow(s2, 0.85)), 0.4) * (0.42 + 0.58 * s2);   // pinched at the knot, fat blunt end
        const along = s2 * 0.046, dr = 0.55 + 0.3 * s2;                    // droops more toward the tip
        const ca = Math.cos(a) * r;   // cross-section spans the shirt plane perpendicular to the lobe's axis
        out.set(k * along * Math.cos(dr) + Math.sin(dr) * ca, -along * Math.sin(dr) + k * Math.cos(dr) * ca, Math.sin(a) * r * 0.42);
      });
      g.deleteAttribute('normal'); g.translate(0, 0.392, 0.094); g.computeVertexNormals(); return g;
    };
    const addM = (geos, mat) => { const m = new THREE.Mesh(mergeGeometries(geos.map((g) => (g.index ? g : g))), mat); this.chestG.add(m); return m; };
    addM([gs([0, 0.3, 0.068], [0.056, 0.12, 0.026])], this.shirtMat);
    addM([1, -1].map((k) => gs([k * 0.064, 0.27, 0.074], [0.03, 0.15, 0.013], [0.12, k * 0.5, -k * 0.32])), this.lapelMat);
    addM([1, -1].map((k) => gs([k * 0.026, 0.035, 0.092], [0.009, 0.009, 0.006], [0, 0, 0], [10, 8])), this.darkMat);
    addM([gs([0, 0.391, 0.095], [0.011, 0.012, 0.009]), lobe(1), lobe(-1)], this.cravatMat);
    // high collar: a flared, open-fronted lathe, taller at the back
    const prof = [[0.064, 0], [0.07, 0.05], [0.088, 0.12], [0.112, 0.175], [0.118, 0.182]].map(([r, y]) => new THREE.Vector2(r, y));
    const cg = new THREE.LatheGeometry(prof, 36, 0.95, TAU - 1.9);
    const P = cg.attributes.position;
    for (let i = 0; i < P.count; i++) {
      const x = P.getX(i), y = P.getY(i), z = P.getZ(i), phi = Math.atan2(x, z);
      const back = (1 - Math.cos(phi)) / 2;                       // 0 at the front, 1 at the back
      P.setXYZ(i, x * 1.12, y * (0.45 + 0.55 * back), z - 0.01 * back);
    }
    cg.computeVertexNormals();
    this.collar = new THREE.Mesh(cg, this.coat2Mat);
    this.collar.position.set(0, 0.385, -0.008); this.collar.rotation.x = 0.42;
    this.chestG.add(this.collar);
    this.collarIn = new THREE.Mesh(cg, this.lapelMat); this.collarIn.scale.setScalar(0.97); this.collar.add(this.collarIn);
    // neck
    this.neck = new SweepTube({ material: this.skinMat, segments: 10, radial: 14, capRings: 2 });
    this.root.add(this.neck.mesh);
  }

  // ------------------------------------------------------------------ head, nose, ears, hair, face, tongue
  _buildHead() {
    const g = new THREE.SphereGeometry(1, 64, 48);
    g.deleteAttribute('uv'); g.deleteAttribute('normal');
    const P = g.attributes.position, tmp = V();
    for (let i = 0; i < P.count; i++) {
      tmp.fromBufferAttribute(P, i).normalize();
      const v = Math.asin(clamp(tmp.y, -1, 1)), u = Math.atan2(tmp.x, tmp.z);
      headPoint(u, v, tmp); P.setXYZ(i, tmp.x, tmp.y, tmp.z);
    }
    const geo = mergeVertices(g); geo.computeVertexNormals();
    this.headMesh = new THREE.Mesh(geo, this.faceMat); this.headMesh.castShadow = true;
    this.headG.add(this.headMesh);
    // long nose (slightly hooked, narrow, bulb tip)
    const nose = new SweepTube({ material: this.skinMat, segments: 16, radial: 12, capRings: 4 });
    sweep(nose, [SP(0, EYE_V + 0.01, -0.006), SP(0, -0.02, 0.008), SP(0, -0.09, 0.024), SP(0, -0.135, 0.046), SP(0, -0.16, 0.06), SP(0, -0.19, 0.058)],
      [0.0075, 0.0098, 0.0128, 0.0148, 0.0108, 0.0055], { up: V(1, 0, 0), flatten: 0.5 });
    this.headG.add(nose.mesh);
    // ears: long, flat, a bit pointy at the back (both ears + tips merged into one mesh)
    const earG = [];
    for (const k of [1, -1]) {
      const p = SP(k * 1.5, -0.02, -0.004);
      const em = new THREE.Matrix4().compose(p, new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.3, k * -0.45, k * -0.12)), V(0.007, 0.034, 0.019));
      const e = new THREE.SphereGeometry(1, 16, 12); e.deleteAttribute('uv'); e.applyMatrix4(em); earG.push(e);
      const tip = new THREE.ConeGeometry(0.008, 0.026, 8); tip.deleteAttribute('uv');
      tip.applyMatrix4(new THREE.Matrix4().compose(V(0, 0.95, -0.25), new THREE.Quaternion().setFromEuler(new THREE.Euler(-0.45, 0, 0)), V(1 / 0.007 * 0.004, 1 / 0.034, 1 / 0.019)).premultiply(em));
      earG.push(tip.toNonIndexed());
    }
    this.headG.add(new THREE.Mesh(mergeGeometries(earG.map((g) => (g.index ? g.toNonIndexed() : g))), this.skinMat));
    // slicked horseshoe of hair around the back/sides (the top is bald: see the comb-over strands)
    const NU = 40, NV = 9, hp = [], hi = [];
    for (let j = 0; j <= NV; j++) for (let i = 0; i <= NU; i++) {
      const u = lerp(1.05, TAU - 1.05, i / NU), side = Math.abs(Math.sin(u));
      const v0 = lerp(-0.42, -0.05, 1 - side * 0.6), v1 = lerp(0.36, 0.5, 1 - side);
      const v = lerp(v0, v1, j / NV);
      const e = rounded(Math.min(j / NV, 1 - j / NV) * 2.4) * rounded(Math.min(i / NU, 1 - i / NU) * 6);
      const { p, n } = headSurf(u, v); p.addScaledVector(n, -0.002 + 0.008 * e);
      hp.push(p.x, p.y, p.z);
    }
    for (let j = 0; j < NV; j++) for (let i = 0; i < NU; i++) { const a = j * (NU + 1) + i, b = a + 1, c = a + NU + 1, d = c + 1; hi.push(a, c, b, b, c, d); }
    const hg = new THREE.BufferGeometry(); hg.setAttribute('position', new THREE.Float32BufferAttribute(hp, 3)); hg.setIndex(hi); hg.computeVertexNormals();
    this.headG.add(new THREE.Mesh(hg, this.hairMat));
    // comb-over strands (hidden under the hat; spring up when it flies off)
    this.strands = [0, 1, 2].map(() => { const s = new SweepTube({ material: this.hairMat, segments: 12, radial: 5, capRings: 1 }); this.headG.add(s.mesh); return s; });
    // face rig
    this.face = new Face({
      head: this.headG, surface: headSurf, seed: 31,
      eyes: {
        u: EYE_U, v: EYE_V, radius: EYE_R, sink: 0.62, splay: 0.14, lidMaterial: this.lidMat,
        iris: 0xc4bb84, iris2: 0xece5b8, irisR: 0.56, pupilR: 0.17, limbal: 0x5f5b44, sclera: 0xe7e6dc, pupilColor: 0x0b0c10,
        lash: 0.55, lowerLash: 0.25, lashColor: 0x191b22, lowRaised: -0.02, upOpen: 0.5, upWide: 1.02, maxYaw: 0.62,
      },
      brows: { color: 0x262a38, thickness: 0.0046, lift: 0.002, inner: [0.13, 0.335], mid: [0.52, 0.425], outer: [0.79, 0.31], range: 0.17, flatten: 0.5, profile: [1.0, 1.15, 0.85, 0.28] },
      mouth: {
        v: MOUTH_V, halfW: HW0, line: '#231d2c', lineW: HW0 * 0.095, interior: '#24182f', interior2: '#76507f', teeth: '#d8d4c0',
        tongue: '#a283b8', lipTintRGB: '86,72,104', blushColor: '150,140,190', drawExtra: (gg, p) => this._drawExtra(gg, p),
      },
      decal: { uMin: -1.2, uMax: 1.2, vMin: MOUTH_V - 0.62, vMax: EYE_V + 0.33, size: [640, 512],
        // perf: a cheap Lambert decal (the paint is mostly dark shading / lines; core accepts cfg.decal.material)
        material: new THREE.MeshLambertMaterial({ transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }) },
      jaw: [this.faceMat.userData.uJaw],
    });
    // dizzy swirl caps (children of the eyeballs: follow gaze, sit under the lids)
    const sc = document.createElement('canvas'); sc.width = sc.height = 128;
    const g2 = sc.getContext('2d');
    g2.fillStyle = '#e6dfb0'; g2.beginPath(); g2.arc(64, 64, 62, 0, TAU); g2.fill();
    g2.strokeStyle = '#2a2a36'; g2.lineWidth = 9; g2.lineCap = 'round'; g2.beginPath();
    for (let k = 0; k <= 120; k++) { const a = k * 0.16, r = 3 + k * 0.48; const x = 64 + Math.cos(a) * r, y = 64 + Math.sin(a) * r; k ? g2.lineTo(x, y) : g2.moveTo(x, y); }
    g2.stroke();
    const stex = new THREE.CanvasTexture(sc); stex.colorSpace = THREE.SRGBColorSpace;
    const th = 0.66, capR = EYE_R * 1.008;
    const cap = new THREE.SphereGeometry(capR, 28, 8, 0, TAU, 0, th); cap.rotateX(Math.PI / 2);
    const CP = cap.attributes.position, CU = cap.attributes.uv, rr = capR * Math.sin(th);
    for (let i = 0; i < CP.count; i++) CU.setXY(i, 0.5 + CP.getX(i) / (2 * rr), 0.5 + CP.getY(i) / (2 * rr));
    this.swirls = this.face.eyes.map((eye) => {
      const m = new THREE.Mesh(cap, new THREE.MeshBasicMaterial({ map: stex, transparent: true, opacity: 0, depthWrite: false }));
      m.renderOrder = 3; m.visible = false; eye.ball.add(m); return m;
    });
    // tongue (3D, slides across the upper lip)
    this.tongue = new SweepTube({ material: this.tongueMat, segments: 26, radial: 12, capRings: 4 });
    this.headG.add(this.tongue.mesh);
    this.tongueCurve = new THREE.CatmullRomCurve3([V(), V(0, 1, 0), V(0, 2, 0)], false, 'centripetal');
    // drool: a clear whitish drop on a thin strand back to the lip corner / tongue tip
    this.drip = new THREE.Mesh(new THREE.SphereGeometry(0.0042, 12, 10), this.droolMat); this.headG.add(this.drip);
    this.strand = new SweepTube({ material: this.droolMat, segments: 8, radial: 5, capRings: 1 }); this.headG.add(this.strand.mesh);
  }

  // lips, moustache, sunken sockets, cheek hollows, grin creases painted into the face decal (metres around the mouth centre)
  _drawExtra(g, p) {
    const m = mouthGeom(p), d = this.face.decal;
    const U = (u) => u * d.rxEff, Vv = (v) => (v - MOUTH_V) * d.ryEff;
    const xr = -m.w + m.shift, xl = m.w + m.shift;
    const soft = (cx, cy, rx, ry, rot, rgb, a) => {
      g.save(); g.translate(cx, cy); g.rotate(rot); g.scale(1, ry / rx);
      const gr = g.createRadialGradient(0, 0, 0, 0, 0, rx);
      gr.addColorStop(0, `rgba(${rgb},${a})`); gr.addColorStop(0.55, `rgba(${rgb},${a * 0.55})`); gr.addColorStop(1, `rgba(${rgb},0)`);
      g.fillStyle = gr; g.beginPath(); g.arc(0, 0, rx, 0, TAU); g.fill(); g.restore();
    };
    g.save();
    for (const s of [-1, 1]) {
      // sunken sockets (the eyeball covers the centre -> a dark ring), slightly drooping outward
      soft(U(s * EYE_U), Vv(EYE_V - 0.03), U(0.26), Vv(EYE_V + 0.2) - Vv(EYE_V), s * 0.15, '34,36,62', 0.74);
      // cheek hollow under the cheekbone
      soft(U(s * 0.76), Vv(-0.38), U(0.2), Vv(-0.2) - Vv(-0.4), s * 0.3, '46,50,80', 0.38);
    }
    // tired eye-bags: a soft crease arcing under each lower lid (the 'depression' in the magician)
    g.lineCap = 'round';
    for (const k of [-1, 1]) {
      const cx = U(k * EYE_U), cy = Vv(EYE_V - 0.2), rx = U(0.17);
      g.strokeStyle = 'rgba(52,54,84,0.42)'; g.lineWidth = HW0 * 0.045;
      g.beginPath(); g.moveTo(cx - rx, cy + HW0 * 0.12); g.quadraticCurveTo(cx + k * rx * 0.15, cy - HW0 * 0.16, cx + rx * 0.95, cy + HW0 * 0.2); g.stroke();
    }
    // soft shadow under the lower lip + chin
    soft(m.shift, m.bot - HW0 * 0.38, m.w * 0.55, HW0 * 0.22, 0, '44,42,70', 0.3);
    // pencil moustache: a straight, near-horizontal pencil line just above the upper lip, split around the nose
    // (both halves stay visible in 3/4 and under the nose's shadow), following the grin only gently; tips flick a hair.
    const lipY = (x) => { const k = clamp(Math.abs(x - m.shift) / m.w); return lerp(m.top, x < m.shift ? m.yR : m.yL, k * k); };
    const y0 = Math.max(m.top, lipY(m.shift)) + HW0 * 0.24;
    g.fillStyle = '#1a1c26';
    for (const s of [-1, 1]) {
      const N = 16, top = [], bot = [];
      const x0 = m.shift + s * HW0 * 0.2, x1 = m.shift + s * Math.max(HW0 * 0.78, lerp(HW0 * 0.92, m.w * 0.9, 0.5));
      for (let i = 0; i <= N; i++) {
        const f = i / N, x = lerp(x0, x1, f);
        const th = HW0 * (0.052 * (1 - Math.pow(smoothstep(0.6, 1, f), 1.3) * 0.8) * (0.8 + 0.2 * smoothstep(0, 0.12, f)) + 0.006);
        let y = y0 + 0.25 * (lipY(x) - lipY(m.shift)) + HW0 * 0.08 * Math.pow(smoothstep(0.78, 1, f), 2) * (0.6 + 0.4 * clamp(p.mSmile + 0.5));
        y = Math.max(y, lipY(x) + HW0 * 0.11 + th);       // never sinks into a big grin's rising corners
        top.push([x, y + th * 1.05]); bot.push([x, y - th * 0.95]);
      }
      g.beginPath(); g.moveTo(top[0][0], top[0][1]);
      for (const [x, y] of top.slice(1)) g.lineTo(x, y);
      for (const [x, y] of bot.reverse()) g.lineTo(x, y);
      g.closePath(); g.fill();
    }
    g.restore();
  }

  // ------------------------------------------------------------------ hat (dented stovepipe, curled brim, band, card)
  _buildHat() {
    this.hatG = new THREE.Group(); this.root.add(this.hatG);
    const prof = [[0.087, 0.0], [0.083, 0.05], [0.081, 0.12], [0.087, 0.2], [0.092, 0.285], [0.09, 0.302], [0.07, 0.31], [0.0, 0.308]].map(([r, y]) => new THREE.Vector2(r, y));
    const cg = new THREE.LatheGeometry(prof, 44);
    cg.deleteAttribute('uv'); cg.deleteAttribute('normal');
    const P = cg.attributes.position;
    for (let i = 0; i < P.count; i++) {
      let x = P.getX(i), y = P.getY(i), z = P.getZ(i);
      const r = Math.hypot(x, z), ph = Math.atan2(x, z);
      const dent = 0.03 * Math.exp(-(((ph - 0.75) / 0.42) ** 2) - (((y - 0.2) / 0.065) ** 2)) + 0.016 * Math.exp(-(((ph + 2.3) / 0.35) ** 2) - (((y - 0.25) / 0.05) ** 2));
      const k = r > 1e-4 ? Math.max(0, r - dent * smoothstep(0, 0.02, r)) / r : 1;
      x *= k; z *= k;
      const lean = smoothstep(0.08, 0.31, y);
      x += 0.03 * lean * lean; z -= 0.012 * lean;
      y += 0.016 * (x / 0.09) * smoothstep(0.28, 0.31, y) - 0.008 * smoothstep(0.29, 0.31, y) * (r < 0.06 ? 1 - r / 0.06 : 0);
      P.setXYZ(i, x, y, z);
    }
    const crown = mergeVertices(cg); crown.computeVertexNormals();
    const hm = new THREE.Group(); this.hatG.add(hm); this.hatMesh = hm;
    // band
    const bg = new THREE.CylinderGeometry(0.0855, 0.0875, 0.036, 44, 1, true);
    const band = new THREE.Mesh(bg, this.bandMat); band.position.y = 0.03; band.scale.set(1.012, 1, 1.012); hm.add(band);
    // brim: closed thin lathe profile, oval, sides curled up
    const bp = [[0.08, -0.004], [0.148, -0.004], [0.157, 0.0], [0.152, 0.005], [0.08, 0.004], [0.08, -0.004]].map(([r, y]) => new THREE.Vector2(r, y));
    const brg = new THREE.LatheGeometry(bp, 56);
    brg.deleteAttribute('uv'); brg.deleteAttribute('normal');
    const BP = brg.attributes.position;
    for (let i = 0; i < BP.count; i++) {
      const x = BP.getX(i), y = BP.getY(i), z = BP.getZ(i) * 0.86;
      const ax = Math.abs(x) / 0.157;
      BP.setXYZ(i, x, y + 0.03 * Math.pow(ax, 3) - 0.008 * Math.pow(Math.abs(z) / 0.135, 2) * (1 - ax), z);
    }
    const brim = mergeVertices(brg); brim.computeVertexNormals();
    const cm = new THREE.Mesh(mergeGeometries([crown, brim]), this.hatMat); cm.castShadow = true; hm.add(cm);
    // a dead grey moth pinned to the band (original motif): furry body + drooping forewings/hindwings, one mesh
    const mothParts = [];
    const wing = (len, wid, droop) => {
      const sh = new THREE.Shape(); sh.moveTo(0, 0);
      sh.bezierCurveTo(len * 0.3, wid * 0.9, len * 0.85, wid * 0.7, len, wid * 0.15);
      sh.bezierCurveTo(len * 0.9, -wid * 0.35, len * 0.4, -wid * 0.4, 0, 0);
      const g = new THREE.ShapeGeometry(sh, 6); g.deleteAttribute('uv'); g.rotateZ(-droop); return g;
    };
    for (const k of [1, -1]) {
      const f = wing(0.034, 0.018, 0.35); f.rotateY(k > 0 ? 0 : Math.PI); f.rotateZ(k * 0.0); mothParts.push(f);
      const h = wing(0.022, 0.014, 0.95); h.rotateY(k > 0 ? 0 : Math.PI); h.translate(0, -0.004, -0.0005); mothParts.push(h);
    }
    const mb = new THREE.SphereGeometry(1, 8, 6); mb.deleteAttribute('uv'); mb.scale(0.0045, 0.013, 0.0045); mb.translate(0, -0.003, 0.002); mothParts.push(mb.toNonIndexed());
    for (const k of [1, -1]) { const an = new THREE.CylinderGeometry(0.0006, 0.0006, 0.014, 3); an.deleteAttribute('uv'); an.rotateZ(k * 0.5); an.translate(k * 0.004, 0.015, 0.002); mothParts.push(an.toNonIndexed()); }
    const moth = new THREE.Mesh(mergeGeometries(mothParts.map((g) => { if (!g.attributes.normal) g.computeVertexNormals(); return g.index ? g.toNonIndexed() : g; })), this.mothMat);
    moth.position.set(-0.062, 0.036, 0.064); moth.rotation.set(-0.1, -0.75, 0.25); hm.add(moth);
    this.hatRest = new THREE.Matrix4().compose(V(0.004, 0.096, -0.012), qE(-0.2, 0.0, 0.11, 'XYZ'), V(1, 1, 1));
  }

  // ------------------------------------------------------------------ arms (sleeves + gloves), legs (striped), shoes
  _buildLimbs() {
    this.arms = {};
    for (const side of ['L', 'R']) {
      const sleeve = new SweepTube({ material: this.coatMat, segments: 18, radial: 12, capRings: 3, castShadow: true });
      const hand = new GloveHand({ side, material: this.gloveMat, cuffMaterial: this.shirtMat });
      this.root.add(sleeve.mesh, hand.root);
      this.arms[side] = { sleeve, hand, elbow: V(), wrist: V(), shoulder: V() };
    }
    this.legs = {};
    for (const side of ['L', 'R']) {
      const tube = new SweepTube({ material: this.trouserMat, segments: 18, radial: 12, capRings: 2, castShadow: true });
      ringAttr(tube);
      const shoe = new THREE.Group();
      const sg = deformSphere(32, 20, (a, s, out) => {
        // a: around the long axis; s: 0 heel .. 1 toe (sphere y mapped to the shoe length)
        const L = s, z = lerp(-0.062, 0.235, L) - 0.012 * smoothstep(0.9, 1, L);
        const w = (0.036 + 0.01 * smoothstep(0.1, 0.42, L)) * Math.pow(1 - smoothstep(0.45, 1.0, L), 0.75) * rounded(L / 0.12) + 0.0018;
        const H = lerp(0.09, 0.03, smoothstep(0.2, 0.92, L)), hgt = H * rounded(L / 0.12) * rounded((1 - L) / 0.04);
        const y0 = -ANKLE_Y + 0.001;
        const yy = y0 + H * 0.5 * (1 - 0.35 * (1 - rounded(L / 0.12))) + hgt * 0.5 * se(Math.cos(a), 2.6) + 0.055 * Math.pow(smoothstep(0.62, 1.0, L), 2.2);
        out.set(w * se(Math.sin(a), 2.6), yy, z);
      });
      const sm = new THREE.Mesh(sg, this.shoeMat); shoe.add(sm);
      this.root.add(tube.mesh, shoe);
      this.legs[side] = { tube, shoe, hip: V(), knee: V(), ankle: V() };
    }
  }

  // ------------------------------------------------------------------ swallow tails (tattered, dynamic ribbons)
  _buildTails() {
    this.NU = 9; this.NV = 12;
    const n = (this.NU + 1) * (this.NV + 1);
    this.tails = [1, -1].map((s) => {
      const g = new THREE.BufferGeometry();
      const pos = new Float32Array(n * 3);
      g.setAttribute('position', new THREE.BufferAttribute(pos, 3).setUsage(THREE.DynamicDrawUsage));
      g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(n * 3), 3).setUsage(THREE.DynamicDrawUsage));
      const idx = [];
      for (let j = 0; j < this.NV; j++) for (let i = 0; i < this.NU; i++) { const a = j * (this.NU + 1) + i, b = a + 1, c = a + this.NU + 1, d = c + 1; idx.push(a, c, b, b, c, d); }
      g.setIndex(idx);
      const mesh = new THREE.Mesh(g, this.coat2Mat); mesh.frustumCulled = false;
      this.root.add(mesh);
      // tattered hem: per-column length factors (jagged)
      const jag = Array.from({ length: this.NU + 1 }, (_, i) => 1 + (i % 2 ? -0.12 : 0.03) * (0.6 + 0.8 * hash1(i * 7 + (s > 0 ? 3 : 11))));
      return { s, g, pos, mesh, jag };
    });
  }

  // ------------------------------------------------------------------ props: wavy dagger (R), velvet pouch (L)
  _buildProps() {
    // wavy (kris-like) dagger, built along +X: handle centred on the origin (sits in the fist's grip frame), guard,
    // then a wide wavy blade with a diamond cross-section; vertex colours paint a dark central fuller + bright edges
    // so the wave reads at phone size. One merged mesh (blade + guard + pommel) + the handle.
    const dg = new THREE.Group(), roll = new THREE.Group(); dg.add(roll);
    const L = 0.17, N = 40, X0 = 0.042, bp = [], bc = [], bi = [];
    const wave = (u) => 0.0085 * Math.sin(u * Math.PI * 3.0) * (1 - 0.45 * u);
    const half = (u) => 0.021 * Math.pow(1 - u, 0.55) * (1 - 0.25 * Math.exp(-(((u - 0.02) / 0.05) ** 2))) + 0.0008;
    const thick = (u) => 0.0032 * (1 - 0.7 * u) + 0.0006;
    for (let i = 0; i <= N; i++) {
      const u = i / N, x = X0 + u * L, yc = wave(u), w = half(u), tz = thick(u);
      // 4 cross-section verts: top edge, front ridge, bottom edge, back ridge
      for (const [y, z, c] of [[yc + w, 0, 1.3], [yc, tz, 0.34], [yc - w, 0, 1.3], [yc, -tz, 0.34]]) { bp.push(x, y, z); bc.push(c, c, c * 1.04); }
    }
    for (let i = 0; i < N; i++) for (let k = 0; k < 4; k++) {
      const a = i * 4 + k, b = i * 4 + (k + 1) % 4, c = a + 4, d = b + 4; bi.push(a, b, c, b, d, c);
    }
    const tipI = bp.length / 3; bp.push(X0 + L + 0.006, wave(1), 0); bc.push(1.2, 1.2, 1.25);
    for (let k = 0; k < 4; k++) bi.push(N * 4 + k, N * 4 + (k + 1) % 4, tipI);
    let bladeG = new THREE.BufferGeometry();
    bladeG.setAttribute('position', new THREE.Float32BufferAttribute(bp, 3)); bladeG.setAttribute('color', new THREE.Float32BufferAttribute(bc, 3));
    bladeG.setIndex(bi); bladeG = bladeG.toNonIndexed(); bladeG.computeVertexNormals();
    const colorize = (g, c) => { g.deleteAttribute('uv'); const n = g.attributes.position.count; g.setAttribute('color', new THREE.Float32BufferAttribute(new Array(n * 3).fill(c), 3)); return g.index ? g.toNonIndexed() : g; };
    const guardG = colorize(new THREE.CapsuleGeometry(0.0055, 0.05, 4, 10), 0.9); guardG.rotateZ(0.12); guardG.translate(X0 - 0.002, 0, 0);
    const pomG = colorize(new THREE.SphereGeometry(0.0125, 12, 10), 0.95); pomG.translate(-0.043, 0, 0);
    const metal = mergeGeometries([bladeG, guardG, pomG]);
    roll.add(new THREE.Mesh(metal, this.bladeMat));
    const hg = new THREE.CylinderGeometry(0.0118, 0.0128, 0.074, 14); hg.rotateZ(Math.PI / 2);
    roll.add(new THREE.Mesh(hg, this.darkMat));
    this.dagger = dg; this.daggerRoll = roll;
    this.daggerTip = new THREE.Object3D(); this.daggerTip.position.set(X0 + L + 0.006, 0, 0); roll.add(this.daggerTip);
    // right hand: thumb (blade) side is -X of the grip frame
    dg.rotation.set(0, Math.PI, 0);
    this.arms.R.hand.grip.add(dg);
    // pouch: hangs from the left hand's pinch (root child, oriented by gravity)
    const pg = new THREE.Group();
    const body = new THREE.Mesh(deformSphere(24, 16, (a, s, out) => {
      const y = lerp(-0.105, -0.012, s);
      const r = 0.052 * Math.sin(Math.PI * Math.pow(s, 0.8)) * (1 - 0.55 * smoothstep(0.75, 1, s)) + 0.012 * smoothstep(0.85, 1, s);
      const wob = 1 + 0.06 * Math.sin(a * 5) * smoothstep(0.55, 0.9, s);
      out.set(Math.sin(a) * r * wob, y, Math.cos(a) * r * wob);
    }), this.velvetMat);
    pg.add(body);
    const tieG = [];                          // neck tie ring + drawstring ends + knots: one merged mesh
    const nr = new THREE.TorusGeometry(0.015, 0.0035, 6, 18); nr.deleteAttribute('uv'); nr.rotateX(Math.PI / 2); nr.translate(0, -0.012, 0); tieG.push(nr);
    for (const k of [1, -1]) {
      const st = new SweepTube({ material: this.cravatMat, segments: 6, radial: 5, capRings: 1 });
      sweep(st, [V(k * 0.014, -0.012, 0.004), V(k * 0.026, -0.03, 0.012), V(k * 0.022, -0.055, 0.016)], 0.0022);
      tieG.push(st.geo.clone());
      const kn = new THREE.SphereGeometry(0.0045, 8, 6); kn.deleteAttribute('uv'); kn.translate(k * 0.022, -0.057, 0.016); tieG.push(kn);
    }
    pg.add(new THREE.Mesh(mergeGeometries(tieG.map((g) => (g.index ? g.toNonIndexed() : g))), this.cravatMat));
    this.frill = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.014, 0.03, 18, 1, true), this.velvetMat);
    this.frill.material = this.velvetMat; this.frill.position.y = 0.004; pg.add(this.frill);
    const fp = this.frill.geometry.attributes.position;
    for (let i = 0; i < fp.count; i++) if (fp.getY(i) > 0) { const a = Math.atan2(fp.getX(i), fp.getZ(i)); fp.setY(i, fp.getY(i) + 0.004 * Math.sin(a * 7)); }
    this.frill.geometry.computeVertexNormals();
    this.velvetMat.side = THREE.DoubleSide;
    this.pouchHole = new THREE.Mesh(new THREE.CircleGeometry(0.026, 18), new THREE.MeshBasicMaterial({ color: 0x0c0a12 }));
    this.pouchHole.rotation.x = -Math.PI / 2; this.pouchHole.position.y = 0.012; pg.add(this.pouchHole);
    this.pouchMouth = new THREE.Object3D(); this.pouchMouth.position.set(0, 0.02, 0); pg.add(this.pouchMouth);
    this.pouch = pg; this.root.add(pg);
  }

  _buildFx() {
    this.fx = new Particles({ max: 260, blending: 'add', intensity: 1.25 });
    this.root.add(this.fx.mesh);
    this.shadow = contactShadow(0.9, 0.7, 0.42);
    this.root.add(this.shadow);
  }

  _buildAnchors() {
    const H = this.headG, Cg = this.chestG;
    this.addAnchor('head', H, [0, 0, 0]);
    this.addAnchor('headTop', H, [0, HR[1] + 0.004, -0.008]);
    this.addAnchor('eyes', H, SP(0, EYE_V, 0.004).toArray());
    this.addAnchor('mouth', H, SP(0, MOUTH_V, 0.006).toArray());
    this.addAnchor('mouthOut', H, SP(0, MOUTH_V, 0.06).toArray());
    this.addAnchor('earL', H, SP(1.5, -0.02, 0.01).toArray());
    this.addAnchor('earR', H, SP(-1.5, -0.02, 0.01).toArray());
    this.addAnchor('noseTip', H, SP(0, -0.215, 0.06).toArray());
    this.addAnchor('chest', Cg, [0, 0.27, 0.115]);
    this.addAnchor('back', Cg, [0, 0.27, -0.14]);
    this.addAnchor('neck', Cg, [0, 0.41, 0.0]);
    this.addAnchor('shoulderL', Cg, [0.17, 0.39, 0]);
    this.addAnchor('shoulderR', Cg, [-0.17, 0.39, 0]);
    this.addAnchor('handL', this.arms.L.hand.root, [0, HAND_SIZE * 0.36, -0.012]);
    this.addAnchor('handR', this.arms.R.hand.root, [0, HAND_SIZE * 0.36, -0.012]);
    this.addAnchor('hip', this.pelvisG, [0, 0, 0]);
    this.addAnchor('belly', this.pelvisG, [0, 0.12, 0.1]);
    this._anch.dagger = this.daggerTip;
    this._anch.pouch = this.pouchMouth;
    this.addAnchor('hat', this.hatMesh, [0, 0.15, 0]);
    for (const nm of ['footL', 'footR', 'kneeL', 'kneeR', 'elbowL', 'elbowR']) this.addAnchor(nm, this.root, [0, 0, 0]);
  }

  // ======================================================================================== update
  update(t, pose = {}) {
    const P = pose || {}, B = P.body || {}, Wk = P.walk || {}, Hd = P.head || {}, E = P.extra || {};
    this.place(P.pos || [0, 0, 0], P.yaw || 0);
    this.root.updateMatrixWorld(true);
    this.rootInv.copy(this.root.matrixWorld).invert();
    this.root.getWorldQuaternion(this.rootQInv); this.rootQInv.invert();

    // ---- modes: standing (S) / kicked flight (K) / crashed upside-down (C)
    const wC = smooth(clamp(E.crashed ?? 0)), wK = smooth(clamp(E.kicked ?? 0)) * (1 - wC);
    const free = clamp(wK + wC), wS = 1 - free;
    const style = GAIT[Wk.style] ? Wk.style : 'walk', ST = GAIT[style];
    const amt = clamp(Wk.amount ?? 0) * wS, ph = Wk.phase ?? t * ST.rate;
    const kneel = clamp(B.kneel ?? 0) * wS, sit = clamp(B.sit ?? 0) * wS, tiptoe = clamp(B.tiptoe ?? 0) * wS;
    const crouch = clamp((B.crouch ?? 0) + amt * ST.crouch) * wS;
    const snick = clamp(B.giggle ?? B.snicker ?? 0);
    const gp = Math.sin(t * TAU * 5.5);
    const shrug = clamp((B.shrug ?? 0) + snick * (0.25 + 0.12 * gp));
    const hunch = (B.hunch ?? 0), slump = clamp(B.slump ?? 0), recoil = B.recoil ?? 0, peek = clamp(B.peek ?? 0, -1, 1);
    const br = (this.breath(t, B.breathRate ?? 0.2) - 0.5) * (B.breathe ?? 1);
    const idle = (B.sway ?? 1) * (1 - amt) * wS;
    const sp = this.speech(t, P);
    const talk = sp ? clamp(sp.open * 1.6) : 0;
    const dizzy = clamp(E.dizzy ?? 0), flail = (E.flail ?? 1) * wK;
    const limp = clamp((E.limp ?? 0) + (style === 'limp' ? 1 : 0));
    this._daggerVis = E.dagger === false ? 0 : (E.dagger ?? 1);
    this._pouchVis = E.pouch === false ? 0 : (E.pouch ?? 1);

    // ---- standing: pelvis & feet (root-local)
    const pel = V(0.008 * fbm1(t * 0.3, 5) * idle, HIP_Y + br * 0.004 - 0.005, -0.03);
    let pelYaw = 0.03 * fbm1(t * 0.21, 8) * idle, pelRoll = 0.015 * fbm1(t * 0.27, 9) * idle, pelPitch = 0;
    let lean = 0, chestYaw = 0, chestRoll = 0, swing = 0;
    const feet = [1, -1].map((s) => ({ s, a: V(s * 0.095, ANKLE_Y, s > 0 ? 0.03 : -0.015), pitch: 0, yaw: s * 0.2, pole: V(s * 0.2, 0, 1) }));
    if (amt > 0) {
      const zs = [];
      for (const f of feet) {
        const bad = limp > 0 && f.s > 0;
        let u = fract(ph + (f.s > 0 ? 0 : 0.5));
        const c = footCycle(u, bad ? { ...ST, stance: ST.stance * 0.85 } : ST, bad);
        const wa = plantAnkle(f.s * (0.1 - 0.03 * ST.run + 0.03 * (ST.knee || 0)), c.z, c.lift, c.pitch, V());
        f.a.lerp(wa, amt); f.pitch = lerp(f.pitch, c.pitch, amt); f.yaw = lerp(f.yaw, f.s * (0.1 + 0.15 * (ST.knee || 0)), amt);
        f.pole.lerp(V(f.s * (0.12 + 0.5 * (ST.knee || 0)), 0, 1), amt);
        zs.push(c.z);
      }
      swing = (zs[0] - zs[1]) / Math.max(0.1, ST.stride * ST.stance);
      pel.y -= amt * ST.bob * (0.5 + 0.5 * Math.cos(4 * Math.PI * ph)) - amt * ST.run * 0.02;
      if (limp > 0) { const dip = Math.max(0, Math.sin(TAU * (ph - 0.1))); pel.y -= amt * limp * 0.045 * dip; pelRoll += amt * limp * 0.09 * dip; chestRoll -= amt * limp * 0.12 * dip; }
      pel.x += amt * ST.sway * Math.sin(TAU * ph);
      pelYaw += -amt * ST.twist * swing;
      pelRoll += amt * 0.03 * Math.cos(TAU * ph);
      chestYaw += amt * ST.twist * 0.9 * swing;
      lean += amt * ST.lean;
    }
    if (tiptoe > 0) { for (const f of feet) { const pt = Math.max(f.pitch, 0.8 * tiptoe); plantAnkle(f.a.x, f.a.z, f.a.y - ANKLE_Y, pt, f.a); f.pitch = pt; } pel.y += 0.06 * tiptoe; }
    if (crouch > 0) {
      const c = smooth(crouch);
      pel.y -= 0.43 * c; pel.z -= 0.13 * c;
      for (const f of feet) { f.a.x += f.s * 0.1 * c; f.a.z += 0.04 * c; f.pole.lerp(V(f.s * 0.85, 0.1, 1), c); const pt = Math.max(f.pitch, 0.55 * c); plantAnkle(f.a.x, f.a.z, f.a.y - ANKLE_Y, pt, f.a); f.pitch = pt; f.yaw += f.s * 0.2 * c; }
      lean += 0.42 * c;
    }
    if (kneel > 0) {
      const k1 = smooth(kneel / 0.45), k2 = smooth((kneel - 0.15) / 0.85);
      for (const f of feet) {
        if (f.s < 0) { f.a.lerp(V(-0.11, 0.09, -0.42), k2); f.a.y += Math.sin(Math.PI * k2) * 0.04; f.pitch = lerp(f.pitch, 1.3, k2); f.pole.lerp(V(0, -0.7, 1), k2); }
        else { f.a.lerp(V(0.13, ANKLE_Y, 0.36), k1); f.a.y += Math.sin(Math.PI * k1) * 0.07; f.pitch *= 1 - k1; f.pole.lerp(V(0.2, 0.25, 1), k1); }
      }
      pel.lerp(V(0, 0.54, -0.06), k2); lean += 0.15 * Math.sin(Math.PI * k2) + 0.05 * k2;
    }
    if (sit > 0) {
      const c = smooth(sit);
      pel.lerp(V(0, 0.15, -0.14), c); pelPitch -= 0.32 * c;
      for (const f of feet) { f.a.lerp(V(f.s * 0.17, ANKLE_Y, 0.48), c); f.pole.lerp(V(f.s * 0.35, 1, 0.3), c); f.pitch = lerp(f.pitch, -0.3, c); f.yaw = lerp(f.yaw, f.s * 0.35, c); }
      lean += 0.2 * c;
    }
    pel.y += (B.bounce ?? 0) * wS;
    if (snick > 0) pel.y += 0.006 * snick * Math.abs(gp);
    if (peek) { pel.x += 0.12 * peek; pelRoll -= 0.06 * peek; }

    // ---- kicked flight (K) & crashed (C) configurations
    const fl = (k, f, a) => a * Math.sin(t * TAU * f + k);
    const flip = E.flip ?? 0;
    const qS = new THREE.Quaternion();
    const qK = qE(-0.55 + flip + 0.08 * fl(1, 1.3, flail), 0.12 * fl(2, 0.9, flail), 0.16 * fl(3, 1.1, flail), 'XYZ');
    const daze = dizzy * (0.6 + 0.4 * Math.sin(t * 2.1));
    const qC = new THREE.Quaternion().setFromAxisAngle(V(1, 0, 0), -0.3).multiply(new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), Math.PI + 0.12 + 0.03 * Math.sin(t * 1.7) * dizzy));
    const pivK = V(0, HIP_Y + 0.08, 0), pivC = V(0.02, 1.06, -0.16);
    const q = qS.clone().slerp(qK, wK / Math.max(1e-6, wS + wK)).slerp(qC, wC);
    this.bodyG.position.set(0, 0, 0).addScaledVector(pel, wS).addScaledVector(pivK, wK).addScaledVector(pivC, wC);
    this.bodyG.quaternion.copy(q);
    this.pelvisG.position.set(0, 0, 0);
    this.pelvisG.rotation.set(pelPitch * wS + 0.45 * wK + 0.1 * wC, pelYaw * wS, pelRoll * wS);
    // chest
    const stoop = STOOP + hunch * 0.35 + slump * 0.25 - amt * (ST.run || 0) * 0.24;   // running straightens the stoop a little
    const chestPitch = (stoop + lean + (B.lean ?? 0) - recoil * 0.3 + br * 0.014 + 0.01 * fbm1(t * 0.23, 12) * idle) * wS
      + (-0.4 + 0.06 * fl(4, 2.2, flail)) * wK + (0.3 + 0.05 * daze) * wC;
    const chestTilt = (-(B.tilt ?? 0) + chestRoll - 0.38 * peek + 0.015 * fbm1(t * 0.25, 14) * idle) * wS + 0.1 * fl(5, 1.7, flail) * wK + 0.12 * wC;
    this.chestG.position.set(0, WAIST - slump * 0.02 * wS, 0);
    this.chestG.rotation.set(chestPitch, (chestYaw + (B.twist ?? 0) + 0.025 * fbm1(t * 0.19, 13) * idle) * wS, chestTilt);
    this.bodyG.updateMatrixWorld(true);
    this.Mb.multiplyMatrices(this.rootInv, this.bodyG.matrixWorld);
    this.Mp.multiplyMatrices(this.rootInv, this.pelvisG.matrixWorld);
    this.Mc.multiplyMatrices(this.rootInv, this.chestG.matrixWorld);
    const qBody = new THREE.Quaternion().setFromRotationMatrix(this.Mb), qChest = new THREE.Quaternion().setFromRotationMatrix(this.Mc);

    // ---- neck & head (root-local)
    let hy = Hd.yaw ?? 0, hp = Hd.pitch ?? 0, hr = Hd.roll ?? 0;
    hy += (0.04 * fbm1(t * 0.17, 21) + 0.03 * fbm1(t * 0.11, 25)) * idle; hp += 0.025 * fbm1(t * 0.19, 22) * idle; hr += 0.02 * fbm1(t * 0.15, 23) * idle;
    hy -= chestYaw * 0.8 * wS;
    hp += amt * 0.015 * Math.cos(4 * Math.PI * ph);
    hr += 0.18 * peek;
    if (snick > 0) { hp += 0.04 * gp * snick; hr += 0.06 * snick; }
    if (sp && (Hd.talk ?? 1) > 0) { const k2 = Hd.talk ?? 1; hp += 0.05 * (sp.open - 0.3) * k2; hy += 0.04 * noise1(t * 0.9, 31) * k2; hr += 0.03 * noise1(t * 0.6, 32) * k2; }
    // in flight: head whips (lags the chest), crashed: lolls with the daze
    hp += (0.3 + 0.12 * fl(6, 2.6, flail)) * wK; hr += 0.2 * fl(7, 1.9, flail) * wK; hy += 0.15 * fl(8, 1.4, flail) * wK;
    hp += (-0.35) * wC; hr += (0.32 + 0.18 * Math.sin(t * 2.3) * dizzy) * wC; hy += 0.15 * Math.sin(t * 1.6) * dizzy * wC;
    const qBase = qBody.clone().slerp(qChest, 0.35);
    // compensate the inherited stoop so the face looks ahead (standing only)
    const inherit = new THREE.Euler().setFromQuaternion(qBase, 'YXZ');
    hp -= inherit.x * wS * (Hd.compensate ?? 1) * 0.95;
    const follow = clamp(Hd.follow ?? 0) * (1 - free);
    const neckBase = V(...NECK_BASE).applyMatrix4(this.Mc);
    if (follow > 0) {
      const lp = Hd.look ? toV(Hd.look) : gazePoint(P.gaze, CTX.camera);
      if (lp) {
        const loc = lp.clone().applyMatrix4(this.rootInv).sub(neckBase).sub(V(0, 0.15, 0.08)).applyQuaternion(qBase.clone().invert());
        const yT = clamp(Math.atan2(loc.x, loc.z), -1.3, 1.3), pT = clamp(-Math.atan2(loc.y, Math.hypot(loc.x, loc.z)), -0.8, 0.8);
        hy = lerp(hy, yT + (Hd.yaw ?? 0), follow); hp = lerp(hp, pT + (Hd.pitch ?? 0), follow);
      }
    }
    const qHead = qBase.clone().multiply(qE(hp, hy, -hr));
    const nd = V(0, Math.cos(NECK_TILT + 0.35 * clamp(hp, -0.5, 0.8)), Math.sin(NECK_TILT + 0.35 * clamp(hp, -0.5, 0.8))).applyQuaternion(qChest);
    const neckLen = NECK_LEN * (1 + 0.25 * wK + 0.3 * Math.abs(peek)) - shrug * 0.03;
    const neckTop = neckBase.clone().addScaledVector(nd, neckLen);
    if (peek) neckTop.addScaledVector(V(1, 0, 0).transformDirection(this.Mb), 0.11 * peek * wS);   // neck slides sideways round the edge
    const headPos = neckTop.clone().add(V(0, 0.098, 0.03).multiplyScalar(HEAD_S).applyQuaternion(qHead));
    this.headG.position.copy(headPos); this.headG.quaternion.copy(qHead);
    this.headG.updateMatrixWorld(true);
    this.Mh.copy(this.headG.matrix);
    const nB = neckBase.clone().addScaledVector(nd, -0.05), nM = neckBase.clone().addScaledVector(nd, neckLen * 0.5).add(V(0, 0, -0.008).applyQuaternion(qChest));
    const nT = V(0, -0.085, -0.03).applyMatrix4(this.Mh);
    sweep(this.neck, [nB, nM, neckTop, nT], [0.036, 0.029, 0.027, 0.032]);

    // ---- face
    const fp = resolveFace(P.face);
    const lick = clamp(E.lick ?? 0), lickOn = smooth(lick / 0.12) * smooth((1 - lick) / 0.1) * (lick > 0 && lick < 1 ? 1 : 0);
    const tOut = clamp(E.tongueOut ?? (wC * dizzy * 0.85));
    const tongueAmt = Math.max(lickOn, tOut);
    if (tongueAmt > 0) {
      fp.mOpen = Math.max(fp.mOpen, 0.26 * lickOn + 0.32 * tOut); fp.mClench = 0; fp.mPress = 0; fp.close = 0;
      fp.mTeethU = Math.max(fp.mTeethU, 0.9); fp.mRound = Math.max(fp.mRound ?? 0, 0.15);
    }
    if (wK > 0) { const pop = MX('popped'); for (const k of Object.keys(pop)) if (typeof pop[k] === 'number' && typeof fp[k] === 'number') fp[k] = lerp(fp[k], pop[k], wK); }
    const gaze = gazePoint(P.gaze, CTX.camera);
    if (dizzy > 0) { fp.saccade = 0; fp.autoBlink = (fp.autoBlink ?? 1) * (1 - dizzy); }
    for (const b of this.face.brows || []) b.tube.curve.needsUpdate = true;   // brow tubes: see sweep()
    // quantise the painted-mouth inputs (pure: same t -> same values) so near-static holds don't redraw the decal canvas
    const QK = 100;
    for (const kq of ['mOpen', 'mWide', 'mRound', 'mSmile', 'mAsym', 'mTeethU', 'mTeethL', 'mClench', 'mPress', 'mTongue', 'mPout', 'mShift', 'blush', 'tearL', 'tearR'])
      if (typeof fp[kq] === 'number') fp[kq] = Math.round(fp[kq] * QK) / QK;
    const spq = sp ? { open: Math.round(sp.open * QK) / QK, wide: Math.round((sp.wide || 0) * QK) / QK, round: Math.round((sp.round || 0) * QK) / QK, close: Math.round((sp.close || 0) * QK) / QK } : null;
    this.face.update(t, fp, { gaze: dizzy > 0.5 ? null : gaze, speech: tongueAmt > 0.3 ? null : spq, blinkAt: P.blinkAt });
    // popped eyes (scale up the whole eye) + dizzy swirls
    const popS = 1 + 0.32 * wK + 0.08 * clamp((fp.lidU - 1.25) / 0.17) * (1 - wK) + (E.eyePop ?? 0) * 0.35;
    this.face.eyes.forEach((eye, i) => {
      eye.group.scale.setScalar(popS);
      const sw = this.swirls[i];
      sw.visible = dizzy > 0.01; sw.material.opacity = smooth(dizzy * 1.4);
      sw.rotation.z = (i ? 1 : -1) * t * (5 + 2 * dizzy);
    });
    // tongue
    this._updateTongue(t, lick, lickOn, tOut);
    // comb-over strands
    const hatOff = clamp(E.hatOff ?? Math.max(wK, wC));
    this._updateStrands(t, hatOff);
    this._updateHat(t, E, hatOff, wK, wC);

    // ---- legs
    const hips = [1, -1].map((s) => V(s * HIP_X, -0.055, 0.0).applyMatrix4(this.Mp));
    const pFwd = V(0, 0, 1).transformDirection(this.Mp), pUp = V(0, 1, 0).transformDirection(this.Mp);
    for (let i = 0; i < 2; i++) {
      const f = feet[i], s = f.s, side = s > 0 ? 'L' : 'R', Lg = this.legs[side];
      let ank = f.a.clone(), pole = f.pole.clone().normalize();
      const qShoeS = qE(f.pitch, f.yaw + pelYaw * 0.3, 0);
      let qShoe = qShoeS;
      if (free > 0) {
        // flight: legs flung forward & wide, bicycling; crash: legs up in the air, splayed, knees out
        const kF = V(s * 0.34, -0.68, 0.38).add(V(0, 0.13 * fl(s * 1.7, 2.6, flail), 0.13 * Math.cos(t * TAU * 2.6 + s * 1.7) * flail));
        const kC = V(s * (0.36 + 0.03 * Math.sin(t * 1.3 + s)), -0.7, 0.18 + (s > 0 ? 0.08 : -0.05));
        const twitch = s < 0 ? 0.06 * Math.max(0, Math.sin(t * 5.1)) * Math.max(0, Math.sin(t * 0.9)) : 0;
        kC.y += twitch;
        const tF = kF.applyMatrix4(this.Mp), tC = kC.applyMatrix4(this.Mp);
        const freeT = tF.multiplyScalar(wK).addScaledVector(tC, wC).multiplyScalar(1 / free);
        ank.lerp(freeT, free);
        const pF = V(s * 0.6, 0.2, 1).transformDirection(this.Mp), pC = V(s * 0.9, 0, 0.5).transformDirection(this.Mp);
        pole.lerp(pF.multiplyScalar(wK).addScaledVector(pC, wC), free).normalize();
      }
      Lg.hip.copy(hips[i]);
      const { mid: knee, end: ankle } = solveIK2(Lg.hip, ank, THIGH, SHIN, pole);
      Lg.knee.copy(knee); Lg.ankle.copy(ankle);
      if (free > 0) {
        const shin = knee.clone().sub(ankle).normalize();
        const o = new THREE.Object3D(); orientYZ(o, shin, pFwd.clone().addScaledVector(pUp, -0.3));
        const qFree = o.quaternion.clone().multiply(qE(-1.0 + 0.2 * Math.sin(t * 7 + s) * flail, s * 0.25, 0));
        qShoe = qShoeS.clone().slerp(qFree, free);
      }
      Lg.shoe.position.copy(ankle); Lg.shoe.quaternion.copy(qShoe);
      const sd = knee.clone().sub(Lg.hip).normalize(), ad = ankle.clone().sub(knee).normalize();
      const end = ankle.clone().addScaledVector(ad, -0.03);
      sweep(Lg.tube, [Lg.hip.clone().addScaledVector(sd, -0.07), Lg.hip.clone().lerp(knee, 0.5), knee, knee.clone().lerp(ankle, 0.55), end],
        [0.06, 0.051, 0.043, 0.037, 0.046], { up: pFwd, capEnd: false });
      this._anch['knee' + side].position.copy(knee); this._anch['foot' + side].position.copy(ankle);
    }

    // ---- arms
    const X = { t, amt, ST, swing, shrug, br, talk, free, wK, wC, flail, dizzy, style, E };
    this._updateArm('L', P.armL, X);
    this._updateArm('R', P.armR, X);
    this._anch.elbowL.position.copy(this.arms.L.elbow); this._anch.elbowR.position.copy(this.arms.R.elbow);

    // ---- coat tails
    let wind = V(0, 0, 0);
    if (E.vel) wind.copy(toV(E.vel)).applyQuaternion(this.rootQInv).multiplyScalar(-0.35);
    else wind.add(V(0, 0.85, 0.55).multiplyScalar(wK));
    wind.add(V(0, 0.05, -0.45 * amt * (0.5 + ST.run)));
    this._updateTails(t, wind, amt, ph, free);

    // ---- props
    this._updateProps(t, E, X);
    // ---- fx & shadow
    this._fx(t, E, X, dizzy, wC);
    const ry = this.root.position.y;
    this.shadow.visible = P.shadow !== false;
    this.shadow.position.set(this.bodyG.position.x, -ry + 0.004, this.bodyG.position.z * 0.6);
    const air = clamp(ry / 1.5);
    this.shadow.scale.set((1 + 0.6 * sit + 0.5 * crouch + 0.8 * wC) * (1 + air), 1, (1 + 0.6 * sit + 0.3 * crouch + 0.8 * wC) * (1 + air));
    this.shadow.material.opacity = 0.42 * (1 - 0.7 * air);
    const glow = P.glow ?? E.glow ?? 1;
    for (const [m, base] of this._rims) m.userData.uniforms.uRim.value = base * glow;
    this.state = { t, kneel, crouch, sit, amt, shrug, wK, wC };
    return this;
  }

  // ------------------------------------------------------------------ arm solver
  _presetToRoot(d, s, sh) {
    const M = d.sp === 'head' ? this.Mh : d.sp === 'body' ? this.Mb : d.sp === 'hip' ? this.Mp : this.Mc;
    const mir = (a) => V(s * a[0], a[1], a[2]);
    const t = d.sp === 'body' ? sh.clone().add(mir(d.t).transformDirection(M).multiplyScalar(mir(d.t).length())) : mir(d.t).applyMatrix4(M);
    return { t, pole: mir(d.pole).transformDirection(M), palm: mir(d.palm).transformDirection(M), fing: mir(d.fing).transformDirection(M) };
  }

  _updateArm(side, A, X) {
    A = A || {};
    const s = side === 'L' ? 1 : -1, arm = this.arms[side], t = X.t;
    const sh = V(s * SH[0], SH[1] + X.shrug * 0.04 + X.br * 0.004, SH[2]).applyMatrix4(this.Mc);
    let list = A.preset ?? (X.amt > 0.5 && X.style === 'sneak' ? 'creep' : 'rest');
    if (typeof list === 'string') list = [[list, 1]];
    const acc = { t: V(), pole: V(), palm: V(), fing: V(), hand: {} };
    for (const k of HAND_KEYS) acc.hand[k] = 0;
    let wsum = 0, restW = 0, edgeW = 0; const anims = [];
    for (const [name, w0] of list) {
      const d = ARM[name] || ARM.rest, w = Math.max(0, w0);
      if (w <= 0) continue;
      const o = this._presetToRoot(d, s, sh);
      acc.t.addScaledVector(o.t, w); acc.pole.addScaledVector(o.pole, w); acc.palm.addScaledVector(o.palm, w); acc.fing.addScaledVector(o.fing, w);
      for (const k of HAND_KEYS) acc.hand[k] += (d.hand[k] ?? HAND_DEF[k]) * w;
      if (name === 'rest' || name === 'hang') restW += w;
      if (name === 'edge') edgeW += w;
      if (d.anim) anims.push([d.anim, w]);
      wsum += w;
    }
    if (wsum <= 0) { Object.assign(acc, this._presetToRoot(ARM.rest, s, sh)); acc.hand = { ...HAND_DEF, ...ARM.rest.hand }; restW = 1; }
    else { acc.t.multiplyScalar(1 / wsum); for (const k of HAND_KEYS) acc.hand[k] /= wsum; restW /= wsum; }
    if (A.target) acc.t.copy(toV(A.target)).applyMatrix4(this.rootInv);
    if (A.pole) acc.pole.copy(toV(A.pole)).applyQuaternion(this.rootQInv);
    if (A.palm) acc.palm.copy(toV(A.palm)).applyQuaternion(this.rootQInv);
    if (A.fingers) acc.fing.copy(toV(A.fingers)).applyQuaternion(this.rootQInv);
    if (A.offset) acc.t.add(toV(A.offset).applyQuaternion(this.rootQInv));
    // 'edge' with a surface target: back the wrist off along the palm normal so the (tapping) fingers rest ON it
    if (A.target && edgeW > 0) acc.t.addScaledVector(acc.palm.clone().normalize(), -(A.gap ?? 0.03) * edgeW / Math.max(1e-6, wsum));
    const reach = clamp(A.reach ?? 1);
    if (reach < 1) {
      const r = this._presetToRoot(ARM.rest, s, sh);
      acc.t.lerp(r.t, 1 - reach); acc.pole.normalize().lerp(r.pole, 1 - reach); acc.palm.normalize().lerp(r.palm, 1 - reach); acc.fing.normalize().lerp(r.fing, 1 - reach);
      for (const k of HAND_KEYS) acc.hand[k] = lerp(ARM.rest.hand[k] ?? HAND_DEF[k], acc.hand[k], reach);
      restW = lerp(1, restW, reach);
    }
    if (A.hand) for (const k of HAND_KEYS) if (A.hand[k] != null) acc.hand[k] = A.hand[k];
    // walk swing / run pump on the resting part
    if (X.amt > 0 && restW > 0) {
      const fwd = V(0, 0, 1).transformDirection(this.Mb);
      const k = X.amt * restW * (X.ST.arm || 0);
      acc.t.addScaledVector(fwd, -X.swing * s * k * 1.2).add(V(0, X.ST.run * 0.25 * X.amt * restW, 0));
      if (X.ST.run) { acc.t.addScaledVector(fwd, 0.12 * X.amt * restW); acc.hand.curl = lerp(acc.hand.curl, 0.8, X.amt * restW); }
    }
    // procedural anims
    let tap = acc.hand.tap || 0, wiggle = 0;
    for (const [an, w] of anims) {
      if (an === 'tap' || an === 'steeple') tap = Math.max(tap, w);
      if (an === 'wiggle') wiggle = Math.max(wiggle, w);
      if (an === 'rub') { const r = Math.sin(t * TAU * 2.2) * s; acc.t.add(V(0, 0.022 * r, 0.018 * r).transformDirection(this.Mc).multiplyScalar(w * 0.03)); }
      if (an === 'wave') acc.fing.add(V(Math.sin(t * TAU * 1.6) * 0.5 * s, 0, 0).transformDirection(this.Mc).multiplyScalar(w));
      if (an === 'stroke') acc.t.add(V(0, -0.015 * (0.5 + 0.5 * Math.sin(t * TAU * 0.9)), 0).transformDirection(this.Mh).multiplyScalar(0.02 * w));
    }
    if (X.E.tap != null) tap = Math.max(tap, X.E.tap);
    // free modes (flight flail / crash sprawl) override
    if (X.free > 0) {
      const fT = V(s * 0.62, 0.66, 0.12).add(V(0.12 * Math.sin(t * TAU * 2.1 + s), 0.12 * Math.cos(t * TAU * 2.1 + s), 0).multiplyScalar(X.flail)).applyMatrix4(this.Mc);
      const head = this.headG.position;
      const cT = V(head.x + s * 0.5, 0.05 + 0.03 * Math.sin(t * 0.8 + s), head.z + 0.18 + 0.06 * s);
      const tt = fT.multiplyScalar(X.wK).addScaledVector(cT, X.wC).multiplyScalar(1 / X.free);
      acc.t.lerp(tt, X.free);
      const pK = V(s * 0.3, -1, -0.5).transformDirection(this.Mc), pC = V(s, 0.6, 0).transformDirection(this.Mb);
      acc.pole.normalize().lerp(pK.multiplyScalar(X.wK).addScaledVector(pC, X.wC), X.free);
      const fK = V(s * 0.7, 0.7, 0.1).transformDirection(this.Mc), palmK = V(0, 0.1, 1).transformDirection(this.Mc);
      acc.fing.normalize().lerp(fK.multiplyScalar(X.wK).addScaledVector(V(s, 0.15, 0.4).normalize(), X.wC), X.free);
      acc.palm.normalize().lerp(palmK.multiplyScalar(X.wK).addScaledVector(V(0, 1, 0), X.wC), X.free);
      const hK = { curl: 0.05, spread: 1, thumb: 0.9, splay: 0.9, cup: 0, point: 0, grip: 0 }, hC = { curl: 0.35, spread: 0.3, thumb: 0.3, cup: 0.3, splay: 0, point: 0, grip: 0 };
      for (const k of Object.keys(hK)) acc.hand[k] = lerp(acc.hand[k], (hK[k] * X.wK + hC[k] * X.wC) / X.free, X.free);
    }
    // props force a hold
    const holdD = side === 'R' && this._daggerVis > 0.5, holdP = side === 'L' && this._pouchVis > 0.5;
    if (holdD) { acc.hand.grip = 1; acc.hand.point = 0; acc.hand.splay = 0; acc.hand.pinch = 0; }
    if (holdP) { acc.hand.pinch = 1; acc.hand.grip = 0; acc.hand.point = 0; acc.hand.splay = 0; }
    // solve
    const pole = acc.pole.lengthSq() > 1e-8 ? acc.pole.normalize() : V(s, 0, -1);
    const { mid, end } = solveIK2(sh, acc.t, UPPER, FORE, pole);
    arm.shoulder.copy(sh); arm.elbow.copy(mid); arm.wrist.copy(end);
    const chordMid = sh.clone().lerp(end, 0.5), m2 = mid.clone().lerp(chordMid, 0.06);
    const sIn = sh.clone().add(V(-s * 0.03, 0.01, 0).transformDirection(this.Mc).multiplyScalar(0.03));
    // sleeve stops short of the wrist so the shirt cuff + flared glove gauntlet show
    const fa0 = end.clone().sub(m2).normalize();
    sweep(arm.sleeve, [sIn, sh.clone().lerp(m2, 0.5), m2, m2.clone().lerp(end, 0.5), end.clone().addScaledVector(fa0, -0.05)],
      [0.05, 0.045, 0.04, 0.037, 0.041]);
    const H = arm.hand;
    H.root.position.copy(end);
    let fd = acc.fing.lengthSq() > 1e-8 ? acc.fing.clone().normalize() : end.clone().sub(mid).normalize();
    const fa = end.clone().sub(mid).normalize();
    if (fd.angleTo(fa) > 1.2) fd = fa.clone().lerp(fd, 1.2 / fd.angleTo(fa)).normalize();      // wrist limit
    H.aim(fd, acc.palm.lengthSq() > 1e-8 ? acc.palm.clone().normalize() : V(0, -1, 0));
    const hp = { ...acc.hand };
    if (tap > 0 || wiggle > 0) {
      const pf = [];
      for (let i = 0; i < 4; i++) {
        const ph = t * TAU * 3.2 - i * 0.9 * s;
        const tp = Math.pow(Math.max(0, Math.sin(ph)), 3) * 0.45 * tap;
        const wg = 0.3 * Math.sin(t * TAU * 1.7 + i * 1.3) * wiggle;
        pf.push(clamp(hp.curl + 0.15 * tap - tp + wg, -0.3, 1.2));
      }
      hp.perFinger = pf;
    }
    H.pose(hp);
  }

  // ------------------------------------------------------------------ tongue (lick across the upper lip / lolling out)
  // decal metres (x right = character's left, y up, around the mouth centre) + surface offset h -> head-local point
  _dm(x, y, h) { const d = this.face.decal; return SP(x / d.rxEff, MOUTH_V + y / d.ryEff, h); }
  _dn(x, y) { const d = this.face.decal; return headSurf(x / d.rxEff, MOUTH_V + y / d.ryEff).n; }

  _updateTongue(t, lick, lickOn, tOut) {
    const show = Math.max(lickOn, tOut);
    this.tongue.mesh.visible = show > 0.01;
    this.drip.visible = false; this.strand.mesh.visible = false;
    if (!this.tongue.mesh.visible) return;
    const m = mouthGeom(this.face.state), w = Math.max(m.w, HW0 * 0.8);
    const lipY = (x) => { const k = clamp(Math.abs(x - m.shift) / m.w); return lerp(m.top, x < m.shift ? m.yR : m.yL, k * k); };
    const D = (x, y, h) => this._dm(x, y, h);
    const midY = (m.top + m.bot) / 2;
    // ---- LICK: the tip sweeps along the UPPER lip (over the moustache) from the right corner to the left corner,
    // the body arching proud of the face (in front of the nose base); tip curls up at the far corner.
    const a = smooth((lick - 0.1) / 0.78), ext = smooth(lickOn);
    const xt = lerp(-1.02, 1.02, a) * w + 0.04 * HW0 * Math.sin(t * 14) * lickOn, sg = Math.sign(xt) || 1;
    const curl = smoothstep(0.78, 1, a) + smoothstep(0.22, 0, a) * 0.2;
    const yt = lipY(xt) + HW0 * (0.2 + 0.05 * Math.sin(t * 9)) + HW0 * 0.42 * curl;
    const tipIn = V(m.shift * 0.5, m.top - HW0 * 0.15, -0.004);
    const L = [D(m.shift, midY, -0.014), D(0.12 * xt, m.top - HW0 * 0.02, 0.016), D(0.55 * xt, lipY(0.55 * xt) + HW0 * 0.32, 0.036),
      D(xt, yt, 0.027), D(xt + sg * HW0 * 0.16 * (0.5 + curl), yt + HW0 * (0.12 + 0.3 * curl), 0.03)];
    const tin = D(tipIn.x, tipIn.y, tipIn.z);
    for (let i = 1; i < 5; i++) L[i].lerp(tin.clone().lerp(L[i], i / 4), 1 - ext);
    // ---- LOLL (tongueOut): out of the left corner, then hanging along GRAVITY (head-local), kept off the face
    const gl = V(0, -1, 0).applyQuaternion(this.headG.getWorldQuaternion(new THREE.Quaternion()).invert());
    const sw = 0.006 * Math.sin(t * 1.9);
    const p1 = D(0.5 * w, m.bot * 0.65 + m.top * 0.35, 0.012), n1 = this._dn(0.5 * w, m.bot);
    const side = V(1, 0, 0);
    const O = [D(m.shift, midY, -0.014), D(0.2 * w, midY, 0.006), p1];
    let q = p1.clone();
    for (const [dl, dn, ds] of [[0.024, 0.012, 0.006], [0.03, 0.004, 0.003], [0.026, 0.002, 0.002]]) {
      q = q.clone().addScaledVector(gl, dl).addScaledVector(n1, dn).addScaledVector(side, ds + sw); O.push(q);
    }
    for (let i = 3; i < O.length; i++) {           // push out of the skull (radial test against headPoint)
      const p = O[i], r = p.length(), u = Math.atan2(p.x, p.z), v = Math.asin(clamp(p.y / Math.max(r, 1e-6), -1, 1));
      const rs = headPoint(u, v, _hw).length() + 0.009;
      if (r < rs) p.multiplyScalar(rs / r);
    }
    O.splice(2, 0); // keep 6 points
    const Lp = [L[0], L[1], L[2], L[3], L[4], L[4].clone().addScaledVector(L[4].clone().sub(L[3]).normalize(), 0.004)];
    const wt = tOut / Math.max(1e-4, lickOn + tOut);
    const pts = Lp.map((p, i) => p.clone().lerp(O[i], wt));
    this.tongueCurve.points = pts; this.tongueCurve.needsUpdate = true;
    const S = [];
    for (let i = 0; i <= 10; i++) S.push(this.tongueCurve.getPoint(i / 10));
    const up = this._dn(0.4 * xt * (1 - wt) + 0.3 * w * wt, m.top);
    sweep(this.tongue, S, (s) => (0.0118 + 0.0016 * Math.sin(Math.PI * Math.min(1, s * 1.3))) * (s > 0.72 ? lerp(1, 0.58, (s - 0.72) / 0.28) : 1), { up, flatten: 0.6 });
    // drool near the end of the lick: hangs from the far lip corner on a thin strand, sags, then thins away
    const dr = (lick - 0.72) / 0.28;
    if (lickOn > 0.05 && dr > 0 && dr < 1 && wt < 0.5) {
      const anchor = D(m.w * 0.96, m.yL + HW0 * 0.06, 0.01);
      const drop = anchor.clone().addScaledVector(gl, 0.006 + 0.05 * dr * dr).add(V(0, 0, 0.004));
      const sc = 1 - smoothstep(0.82, 1, dr);
      this.drip.visible = sc > 0.05; this.strand.mesh.visible = sc > 0.05;
      this.drip.position.copy(drop); this.drip.scale.set(sc, sc * (1 + 0.5 * dr), sc);
      sweep(this.strand, [anchor, anchor.clone().lerp(drop, 0.5).add(V(0, 0, 0.002)), drop], [0.0016, 0.0011 * (0.4 + 0.6 * sc), 0.0014 * sc + 1e-4]);
    }
  }

  _updateStrands(t, off) {
    const pop = smooth(off / 0.6);
    const vis = off > 0.05;
    for (let i = 0; i < 3; i++) {
      const S = this.strands[i]; S.mesh.visible = vis;
      if (!vis) continue;
      const k = i - 1, wob = 0.22 * Math.sin(t * 9 + i * 2) * pop;
      const pts = [];
      for (let j = 0; j <= 4; j++) {
        const f = j / 4;
        const u = lerp(-1.15, 0.95, f) + k * 0.05, v = lerp(0.55 + 0.06 * k, 1.05 + 0.05 * k, Math.sin(Math.PI * f * 0.8));
        const lie = SP(u * (1 - pop * f * 0.6), v + pop * f * 0.15, 0.003 + pop * f * (0.05 + 0.02 * k) * (1 + wob));
        pts.push(lie);
      }
      sweep(S, pts, [0.0022, 0.002, 0.0018, 0.0015, 0.0012]);
    }
  }

  _updateHat(t, E, off, wK, wC) {
    const att = new THREE.Matrix4().multiplyMatrices(this.Mh, this.hatRest);
    const pA = V(), qA = new THREE.Quaternion(), sA = V();
    att.decompose(pA, qA, sA);
    if (off <= 0.001) { this.hatG.position.copy(pA); this.hatG.quaternion.copy(qA); this.hatG.visible = E.hat !== false; this.hatG.updateMatrix(); return; }
    let pF, qF;
    if (E.hatPos) pF = toV(E.hatPos).applyMatrix4(this.rootInv);
    else {
      const up = 0.55 * Math.sin(Math.PI * Math.min(1, off)) + 0.25 * off;
      pF = pA.clone().add(V(0.12 * off, up, -0.35 * off));
      if (wC > 0) pF.lerp(V(0.48, 0.0, 0.32), wC);
    }
    if (E.hatRot) qF = this.rootQInv.clone().multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(...E.hatRot)));
    else {
      qF = qA.clone().multiply(qE(-2.6 * off, 1.5 * off, 0.8 * off, 'XYZ'));
      if (wC > 0) qF.slerp(qE(0.0, 0.6, 1.45, 'XYZ'), wC);
    }
    this.hatG.position.copy(pA.lerp(pF, smooth(off)));
    this.hatG.quaternion.copy(qA.slerp(qF, smooth(off)));
    this.hatG.visible = E.hat !== false;
    this.hatG.updateMatrix();
  }

  // ------------------------------------------------------------------ coat tails (stateless hanging ribbons + leg push-out)
  _updateTails(t, wind, amt, ph, free) {
    const NU = this.NU, NV = this.NV, LEN = 0.6;
    const g = V(0, -1, 0).add(wind);
    const caps = [];
    for (const sd of ['L', 'R']) { const Lg = this.legs[sd]; caps.push([Lg.hip, Lg.knee, 0.075], [Lg.knee, Lg.ankle, 0.06]); }
    const pUp = V(0, 1, 0).transformDirection(this.Mp), pBack = V(0, 0, -1).transformDirection(this.Mp);
    const _c = V(), _d = V();
    for (const T of this.tails) {
      const s = T.s;
      for (let i = 0; i <= NU; i++) {
        const f = i / NU;
        // attachment on the waist seam: from the back centre around to the hip side
        const th = Math.PI - s * lerp(0.06, 2.25, f);
        const a = V(Math.sin(th) * 0.112, 0.085, Math.cos(th) * 0.098 - 0.004).applyMatrix4(this.Mp);
        const out = V(Math.sin(th), 0, Math.cos(th)).transformDirection(this.Mp);
        let p = a.clone();
        const Lc = LEN * T.jag[i] * (1 - 0.8 * smoothstep(0.35, 1, f)), ds = Lc / NV;
        for (let j = 0; j <= NV; j++) {
          const sj = j / NV;
          if (j > 0) {
            const d0 = pUp.clone().multiplyScalar(-1).addScaledVector(pBack, 0.22 + 0.1 * (1 - sj)).addScaledVector(out, 0.2 * (1 - f) + 0.05);
            const dir = d0.lerp(g, smooth(sj * 1.6) * 0.85);
            const fl = 0.18 * sj * (fbm1(t * 1.3 + s * 3 + i * 0.07, 41) + amt * Math.sin(TAU * ph + s * 1.5 + sj * 2)) + 0.5 * free * sj * Math.sin(t * 11 + s + sj * 4);
            dir.addScaledVector(out, fl * 0.5).add(V(fl * 0.3 * s, 0, 0));
            p.addScaledVector(dir.normalize(), ds);
            const narrow = 0.012 * (f - 0.5) * smooth(sj) * s;
            p.addScaledVector(out, -Math.abs(narrow));
            // push out of the legs
            for (const [A, Bp, r] of caps) {
              _d.copy(Bp).sub(A); const L2 = _d.lengthSq(); if (L2 < 1e-8) continue;
              const u = clamp(_c.copy(p).sub(A).dot(_d) / L2);
              _c.copy(A).addScaledVector(_d, u);
              const off = p.clone().sub(_c), dist = off.length();
              if (dist < r) { if (dist < 1e-5) off.copy(pBack); else off.multiplyScalar(1 / dist); p.copy(_c).addScaledVector(off, r); }
            }
          }
          const k = (j * (NU + 1) + i) * 3;
          T.pos[k] = p.x; T.pos[k + 1] = p.y; T.pos[k + 2] = p.z;
        }
      }
      T.g.attributes.position.needsUpdate = true;
      T.g.computeVertexNormals(); T.g.attributes.normal.needsUpdate = true;
    }
  }

  // ------------------------------------------------------------------ props per frame
  _updateProps(t, E, X) {
    this.dagger.visible = this._daggerVis > 0.5;
    // the handle lies in the fist's grip frame; roll the blade about its long axis so the wavy FACE turns to the
    // camera (a dagger seen edge-on reads as a needle). extra.daggerRoll (rad) overrides; daggerFace 0 disables.
    if (this.dagger.visible) {
      let ang = E.daggerRoll ?? 0;
      const cam = CTX.camera, kf = E.daggerRoll != null ? 0 : (E.daggerFace ?? 1);
      if (cam && kf > 0) {
        this.dagger.updateWorldMatrix(true, false);
        const c = cam.position.clone().applyMatrix4(_m1.copy(this.dagger.matrixWorld).invert());
        ang = lerp(ang, Math.atan2(-c.y, c.z), kf);
      }
      this.daggerRoll.rotation.set(ang, 0, 0);
    }
    // pouch hangs from the left hand's pinch point, swinging under gravity; dust tilts it to pour
    this.pouch.visible = this._pouchVis > 0.5;
    if (!this.pouch.visible) return;
    const H = this.arms.L.hand;
    H.root.updateMatrixWorld(true);
    const pinch = H.tipWorld('thumb').lerp(H.tipWorld(0, _pv), 0.5).applyMatrix4(this.rootInv);
    const dust = clamp(E.dust ?? 0);
    const fwd = V(0, 0, 1).transformDirection(this.Mb);
    const up = V(0, 1, 0).addScaledVector(fwd, 1.6 * dust).add(V(0.12 * Math.sin(t * 1.9), 0, 0.1 * Math.sin(t * 1.4 + 1)).multiplyScalar(1 - dust));
    if (X.free > 0) up.lerp(V(0.4 * Math.sin(t * 9), 1, 0.4 * Math.cos(t * 8)), X.free);
    const o = new THREE.Object3D(); orientYZ(o, up.normalize(), fwd);
    this.pouch.position.copy(pinch); this.pouch.quaternion.copy(o.quaternion);
    // pour: invert so the mouth (top) leans forward & down
    if (dust > 0) this.pouch.quaternion.multiply(qE(1.9 * smooth(dust), 0, 0, 'XYZ'));
    this.frill.scale.set(1 + 0.6 * dust, 1 + 0.2 * dust, 1 + 0.6 * dust);
    this.pouchHole.visible = dust > 0.05; this.pouchHole.scale.setScalar(0.6 + 0.6 * dust);
    this.pouch.updateMatrixWorld(true);
  }

  // ------------------------------------------------------------------ particles: gloom motes, numbing dust, dizzy stars
  _fx(t, E, X, dizzy, wC) {
    const fx = this.fx; fx.begin();
    const ma = E.motes ?? 1;
    if (ma > 0) {
      const pts = [this.Mc, this.Mc, this.Mh, this.hatG.matrix, this.Mp];
      const loc = [[0.15, 0.38, -0.02], [-0.15, 0.38, -0.02], [0, 0.05, -0.08], [0, 0.04, 0], [0, -0.3, -0.13]];
      fx.stream({ t, seed: 61, t0: -30, t1: 1e6, rate: 3.2, life: 2.8, alpha: 0.42 * ma,
        origin: (tb) => { const n = Math.floor(tb * 1000), k = Math.floor(hash1(n * 3 + 1) * 5) % 5; const l = loc[k];
          return V(l[0] + (hash1(n * 5 + 2) - 0.5) * 0.14, l[1] + (hash1(n * 7 + 3) - 0.5) * 0.06, l[2] + (hash1(n * 9 + 4) - 0.5) * 0.1).applyMatrix4(pts[k]).toArray(); },
        vel: [0, -0.1, 0], spread: [0.03, 0.03, 0.03], gravity: [0, -0.02, 0], size: [0.012, 0.024], color: [0xaab4cc, 0x8f98b4, 0xc4c8d8],
        fade: [0.2, 0.5], cell: CELL.dust, wobble: 0.03 });
    }
    const dust = clamp(E.dust ?? 0);
    if (dust > 0.01 && this.pouch.visible) {
      this.pouchMouth.updateMatrixWorld(true);
      const m = V().setFromMatrixPosition(this.pouchMouth.matrixWorld).applyMatrix4(this.rootInv);
      const dir = V(0, 1, 0).transformDirection(_m1.multiplyMatrices(this.rootInv, this.pouchMouth.matrixWorld));
      fx.stream({ t, seed: 62, t0: -30, t1: 1e6, rate: 34 * dust, life: 1.5, alpha: 0.95 * dust, origin: m.toArray(),
        vel: [dir.x * 0.3, dir.y * 0.3 - 0.05, dir.z * 0.3], spread: [0.08, 0.05, 0.08], gravity: [0, -0.55, 0], drag: 0.6,
        size: [0.012, 0.03], grow: 0.7, color: [0xe4e8f2, 0xb4bccc, 0xcfc6e4, 0x9aa2b8], fade: [0.05, 0.45],
        cell: (r) => (r() < 0.55 ? CELL.star : CELL.dust), twinkle: true, spin: 2, wobble: 0.02 });
      fx.stream({ t, seed: 63, t0: -30, t1: 1e6, rate: 4 * dust, life: 2.2, alpha: 0.18 * dust, origin: m.toArray(),
        vel: [dir.x * 0.1, -0.12, dir.z * 0.1], spread: [0.05, 0.02, 0.05], size: [0.06, 0.1], grow: 2.2, color: [0x9aa0b4], fade: [0.2, 0.6], cell: CELL.puff });
    }
    // dizzy: little stars circling above the head (world-up ring)
    const st = clamp(E.stars ?? dizzy);
    if (st > 0.01) {
      // above the head when upright; a ring round the head (in front of the face) when upside-down
      const c = this.headG.position.clone().add(V(0, 0.26 * (1 - wC) + 0.02 * wC, 0.04 * wC));
      const R = lerp(0.17, 0.27, wC);
      for (let i = 0; i < 5; i++) {
        const a = t * 3.2 + (i / 5) * TAU;
        const p = c.clone().add(V(Math.cos(a) * R, 0.03 * Math.sin(a * 2 + i) + wC * 0.1 * Math.sin(a), Math.sin(a) * R * 0.7));
        fx.add(p.toArray(), 0.05 + 0.012 * Math.sin(t * 7 + i), i % 2 ? 0xfff0b0 : 0xe8ecff, 0.95 * st, t * 2 + i, CELL.star);
      }
    }
    fx.end();
  }

  anchor(name) {
    if (name === 'headUp') { const a = super.anchor('headTop'), b = super.anchor('head'); return a.sub(b).normalize(); }
    if (name === 'mouthDir') return super.anchor('mouthOut').sub(super.anchor('mouth')).normalize();
    return super.anchor(name);
  }
}

export async function create() { return new Magician(); }
export { Magician };
