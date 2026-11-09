// USER — "the Twitter user" (1.65 m). Young adult, gender-ambiguous-to-feminine, scared-sarcastic, ALWAYS on
// the phone. Fully procedural rig (no external models):
//   sculpted round head (custom surface shared with the core Face rig): big hazel eyes with lash lines,
//   a wet "tear line" on each lower lid, swept brows, small upturned nose, painted mouth + lips + freckles +
//   rosy cheeks; slightly-too-big round glasses (thin frames, never covering the eyes; slip / tilt / jump);
//   messy dark-brown bob made of sculpted chunky locks over a cap shell (side part, swept fringe kept above the
//   brows, a bouncing cowlick, GPU swing of the hanging ends); oversized slate-blue hoodie (skinned lathe body
//   that bends between pelvis and chest, collides with the thighs, kangaroo pocket, ribbed hem, hood down as a
//   rolled collar + hood on the back, two bouncing drawstrings), oversized bunched sleeves, soft hands with a
//   phone grip + thumb-tap, charcoal joggers with cuffed ankles, chunky white sneakers;
//   a generic slab phone (no logos) whose screen shows a scrolling feed of grey cards / a confirm-Block dialog /
//   a 'You blocked …' page, and whose cool glow lights the face (custom shader term, no extra lights) and
//   reflects in the eyes and glasses; 3D tear drops.
// Pose API + tips: docs/chars/user.md. Every frame is a pure function of (t, pose).
import * as THREE from 'three';
import { mergeVertices, mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { Character, gazePoint } from '../core/character.js';
import { Face, EXPR, FACE_DEFAULTS } from '../core/face.js';
import { SweepTube, solveIK2, orientYZ } from '../core/limbs.js';
import { skin, cloth, hair, contactShadow } from '../core/materials.js';
import { CTX } from '../core/context.js';
import { clamp, lerp, smooth, smoothstep, noise1, fbm1, hash1, schedule, rng } from '../core/util.js';

// ---------------------------------------------------------------------------------------------------------
// Palette
const SKIN = 0xe2ad8b, HAIR_C = 0x4a2b1b, BROW_C = 0x2e1a10, HOODIE = 0x5f7499, JOG = 0x35373f,
  SNEAK = 0xf4f1ea, SOLE = 0xe7e1d6, OUTSOLE = 0xb9b2a8, LACE = 0xd9d6cf, CASE = 0xef8e78, FRAME = 0x2a2230;

// Proportions (metres). Root at the feet, facing +Z, +X = character's left.
const HIP_Y = 0.835, WAIST_H = 0.13, CHEST_Y0 = HIP_Y + WAIST_H;     // chest pivot 0.965 at rest
const SH = [0.172, 0.25, -0.014];                                    // left shoulder joint (chest-local) -> y 1.215
const NECK_BASE = 0.262, NECK_LEN = 0.062, HEAD_UP = 0.14, HEAD_SCALE = 1.12;   // head centre ~1.43
const UPPER = 0.25, FORE = 0.235, HAND_SIZE = 0.15;
const HIP_X = 0.083, HIP_DY = -0.045, THIGH = 0.358, SHIN = 0.346, ANKLE_Y = 0.095;
const BALL_Z = 0.125, HEEL_Z = -0.062;
const HR = [0.138, 0.153, 0.143];                                    // skull radii
const EYE_U = 0.40, EYE_V = 0.02, EYE_R = 0.043, MOUTH_V = -0.47, HW0 = 0.035;
const JAW = { y: -0.085, drop: 0.017, back: 0.005, soft: 0.03 };
const MAXWRIST = 1.3;
const PH_W = 0.071, PH_H = 0.148, PH_D = 0.0085;                     // phone slab

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const toV = (a) => (a instanceof THREE.Vector3 ? a.clone() : V(a[0], a[1], a[2]));
const fract = (x) => x - Math.floor(x);
const bump = (x, a, b) => (x <= a || x >= b ? 0 : Math.sin(Math.PI * (x - a) / (b - a)));
function pw(K, a) { // piecewise-linear lookup in [[x, y], ...]
  if (a <= K[0][0]) return K[0][1];
  for (let i = 1; i < K.length; i++) if (a <= K[i][0]) return lerp(K[i - 1][1], K[i][1], (a - K[i - 1][0]) / (K[i][0] - K[i - 1][0]));
  return K[K.length - 1][1];
}
// Catmull-Rom through keyed arrays [[s, [..values]], ...] (smooth velocity through the keys)
function crKeys(K, s) {
  if (s <= K[0][0]) return K[0][1].slice();
  const n = K.length;
  if (s >= K[n - 1][0]) return K[n - 1][1].slice();
  let i = 0; while (i < n - 2 && s > K[i + 1][0]) i++;
  const u = (s - K[i][0]) / (K[i + 1][0] - K[i][0]);
  const p0 = K[Math.max(0, i - 1)][1], p1 = K[i][1], p2 = K[i + 1][1], p3 = K[Math.min(n - 1, i + 2)][1];
  const u2 = u * u, u3 = u2 * u;
  return p1.map((_, k) => 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3));
}
// merge static child meshes of `parent` into one mesh per material (fewer draw calls)
function bake(parent, meshes) {
  const byMat = new Map();
  for (const m of meshes) {
    m.updateMatrix();
    let g = m.geometry.clone().applyMatrix4(m.matrix);
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
    if (g.index) g = g.toNonIndexed();
    if (!byMat.has(m.material)) byMat.set(m.material, []);
    byMat.get(m.material).push(g);
    parent.remove(m);
  }
  const out = [];
  for (const [mat, gs] of byMat) { const mm = new THREE.Mesh(mergeGeometries(gs), mat); parent.add(mm); out.push(mm); }
  return out;
}

// ---------------------------------------------------------------------------------------------------------
// Phone glow: a custom shading term (no extra scene light -> no shader recompiles in any scene). The screen
// lights what it faces with a soft falloff. Uniforms are per character; positions go to view space in
// onBeforeRender so they always use the camera that actually draws.
function phoneLit(mat, U) {
  const prev = mat.onBeforeCompile;
  const prevKey = mat.customProgramCacheKey;
  mat.onBeforeCompile = (sh, r) => {
    if (prev) prev.call(mat, sh, r);
    sh.uniforms.uPhPos = U.pos; sh.uniforms.uPhDir = U.dir; sh.uniforms.uPhCol = U.col;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uPhPos, uPhDir, uPhCol;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      {
        vec3 pv = -vViewPosition; vec3 Lv = uPhPos - pv; float d2 = dot(Lv, Lv);
        vec3 Lp = Lv * inversesqrt(max(d2, 1e-6));
        float lam = max(dot(normalize(normal), Lp), 0.0);
        float facing = clamp(dot(-Lp, uPhDir) * 1.4 + 0.1, 0.0, 1.0);
        float fall = 0.035 / (d2 + 0.035) * smoothstep(0.0, 0.0081, d2);
        totalEmissiveRadiance += diffuseColor.rgb * uPhCol * (0.25 + 0.75 * lam) * facing * fall;
      }`);
  };
  mat.customProgramCacheKey = () => (prevKey ? prevKey.call(mat) : mat.type) + '|uph';
  return mat;
}
// Hair swing: hanging ends (head-local y below the cheekbones) are displaced on the GPU (stateless follow-through)
function hairSwing(mat, U) {
  const prev = mat.onBeforeCompile;
  const prevKey = mat.customProgramCacheKey;
  mat.onBeforeCompile = (sh, r) => {
    if (prev) prev.call(mat, sh, r);
    sh.uniforms.uSwing = U.swing; sh.uniforms.uBounce = U.bounce;
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uSwing; uniform float uBounce;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
      { float hw = smoothstep(0.03, -0.1, transformed.y); hw *= hw;
        transformed += uSwing * hw; transformed.y += uBounce * hw; }`);
  };
  mat.customProgramCacheKey = () => (prevKey ? prevKey.call(mat) : mat.type) + '|hsw';
  return mat;
}

// ---------------------------------------------------------------------------------------------------------
// Head surface (head-local: origin = head centre, +Z out of the face). Shared by mesh, Face, hair, glasses.
function headPoint(u, v, out = new THREE.Vector3()) {
  const cv = Math.cos(v), sv = Math.sin(v), cu = Math.cos(u), su = Math.sin(u);
  let x = HR[0] * su * cv, y = HR[1] * sv, z = HR[2] * cu * cv;
  const front = Math.max(0, cu), au = Math.abs(u);
  const low = smoothstep(-0.05, -1.3, v);
  x *= 1 - 0.17 * low;                                          // soft rounded jaw
  z *= 1 - 0.07 * low * (1 - front);
  const back = Math.max(0, -cu) * smoothstep(-0.3, 0.7, v);
  x *= 1 + 0.03 * back; z *= 1 + 0.06 * back;                  // round cranium
  const chin = Math.exp(-(((v + 1.0) / 0.26) ** 2)) * front ** 4;
  z += 0.006 * chin; y -= 0.003 * chin;
  const ck = Math.exp(-(((au - 0.56) / 0.3) ** 2) - (((v + 0.3) / 0.24) ** 2)) * front;     // full cheeks
  const es = Math.exp(-(((au - EYE_U) / 0.17) ** 2) - (((v - EYE_V) / 0.14) ** 2));        // eye sockets
  const br = Math.exp(-(((au - 0.36) / 0.3) ** 2) - (((v - 0.36) / 0.1) ** 2)) * front;    // soft brow ridge
  const k = 1 + 0.045 * ck - 0.014 * es + 0.012 * br;
  return out.set(x * k, y * k, z * k);
}
const _hu = new THREE.Vector3(), _hv = new THREE.Vector3(), _hw = new THREE.Vector3();
function headSurf(u, v) {
  const e = 1e-3;
  const p = headPoint(u, v);
  headPoint(u + e, v, _hu).sub(headPoint(u - e, v, _hw));
  headPoint(u, v + e, _hv).sub(headPoint(u, v - e, _hw));
  const n = new THREE.Vector3().crossVectors(_hu, _hv);
  if (n.lengthSq() < 1e-14) n.copy(p);
  n.normalize();
  if (n.dot(p) < 0) n.negate();
  return { p, n };
}

// Hair cap shell: hairline latitude per |longitude|; the fringe locks fall over the front edge.
const HAIRLINE = [[0, 0.64], [0.5, 0.56], [0.9, 0.34], [1.3, 0.02], [1.7, -0.22], [2.4, -0.42], [Math.PI, -0.48]];
const hairline = (u) => pw(HAIRLINE, Math.abs(u));

// ---------------------------------------------------------------------------------------------------------
// Expressions. UX(name, overrides) like core X(); USER presets + all core EXPR names.
export const UEXPR = {
  idle: { lidU: 1.0, lidL: 0.06, browIn: 0.18, browSq: 0.05, mSmile: -0.06, mPress: 0.15 },
  scroll: { lidU: 0.74, lidL: 0.16, browIn: 0.08, browSq: 0.12, mPress: 0.3, mSmile: -0.12, mAsym: 0.12, saccade: 0.4 },
  sob: { lidU: 0.2, lidL: 1, lidSad: 1, browIn: 1.0, browOut: -0.55, browSq: 0.6, mOpen: 0.78, mWide: 0.95, mSmile: -0.95, mTeethU: 0.5, mTeethL: 0.85, mTremble: 0.7, wet: 1, tearL: 0.9, tearR: 0.9, blush: 0.5, autoBlink: 0 },
  terror: { lidU: 1.48, lidL: 0.32, browIn: 1.0, browOut: 0.55, browSq: 0.55, lidSad: 0.2, mOpen: 0.5, mWide: 0.75, mSmile: -0.65, mTeethL: 0.85, mTeethU: 0.5, pupil: 0.42, mTremble: 0.6, wet: 1, saccade: 0.25 },
  scream: { lidU: 1.46, lidL: 0.1, browIn: 1, browOut: 0.8, browSq: 0.45, mOpen: 0.85, mWide: 1, mSmile: -0.4, mTeethU: 1, mTeethL: 1, mTongue: 0.2, pupil: 0.34, mTremble: 0.3, autoBlink: 0 },
  gasp: { lidU: 1.44, browIn: 0.85, browOut: 0.95, mOpen: 0.7, mRound: 0.85, mTeethU: 0.3, mTeethL: 0.2, pupil: 0.48 },
  wtf: { lidU: 1.32, browIn: 0.6, browOut: 1.0, browAsym: 0.55, mOpen: 0.52, mWide: 0.35, mSmile: -0.45, mAsym: -0.3, mTeethL: 0.5, mTeethU: 0.6 },
  scrunch: { lidU: 0.02, lidL: 1, squint: 1, browIn: -1, browSq: 1, browOut: 0.25, mOpen: 0.42, mWide: 1, mSmile: -0.55, mTeethU: 1, mTeethL: 1, mClench: 0.0, autoBlink: 0, blush: 0.3 },
  deadpan: { lidU: 0.48, lidL: 0.12, browIn: 0.0, browOut: -0.08, mPress: 0.35, mSmile: -0.1, saccade: 0.2 },
  hellno: { lidU: 0.62, lidL: 0.42, lidAngry: 0.6, browIn: -0.95, browSq: 1, browOut: 0.25, mPress: 0.85, mSmile: -0.55, mPout: 0.2 },
  pout: { lidU: 0.7, lidL: 0.38, lidAngry: 0.35, browIn: -0.45, browSq: 0.6, mPout: 1, mSmile: -0.5, mPress: 0.45, mShift: 0.15 },
  smirk: { lidU: 0.64, lidL: 0.32, browAsym: 0.5, browSq: 0.2, mSmile: 0.32, mAsym: 0.75, mPress: 0.35 },
  suspicious: { lidU: 0.6, lidL: 0.48, browIn: -0.35, browSq: 0.6, browAsym: -0.4, mPress: 0.55, mAsym: -0.35, mSmile: -0.18 },
  glare: { lidU: 0.56, lidL: 0.38, lidAngry: 0.75, browIn: -1, browSq: 1, mPress: 0.65, mSmile: -0.45 },
  gulp: { lidU: 1.25, browIn: 0.85, browOut: 0.2, browSq: 0.35, mPress: 0.95, mSmile: -0.35, mWide: -0.35, pupil: 0.65 },
  guilt: { lidU: 0.88, browIn: 0.75, browOut: -0.2, lidSad: 0.5, mSmile: -0.22, mPress: 0.25, mOpen: 0.03 },
  soften: { lidU: 1.14, browIn: 0.8, browOut: 0.05, lidSad: 0.32, mOpen: 0.1, mSmile: 0.04, mTremble: 0.35, wet: 1, pupil: 1.32 },
  tremble: { lidU: 0.96, lidL: 0.32, browIn: 0.95, browOut: -0.15, browSq: 0.35, lidSad: 0.55, mPress: 0.75, mPout: 0.6, mSmile: -0.38, mTremble: 1, wet: 1 },
  dawning: { lidU: 1.18, browIn: 0.6, browOut: 0.4, mOpen: 0.13, mRound: 0.3, wet: 0.5, pupil: 1.15 },
  notquite: { lidU: 0.9, lidL: 0.32, browIn: 0.6, lidSad: 0.3, mSmile: 0.24, mPress: 0.35, mTremble: 0.25, wet: 0.6 },
  nervous: { mClench: 0.85, mWide: 0.7, mSmile: 0.18, mAsym: 0.2, browIn: 0.85, browOut: 0.4, lidU: 1.12 },
  storm: { lidU: 0.6, lidL: 0.34, lidAngry: 0.85, browIn: -1, browSq: 1, browOut: 0.15, mPout: 0.7, mSmile: -0.62, mPress: 0.55, mAsym: -0.22 },
  disbelief: { lidU: 0.55, lidL: 0.05, browIn: 0.35, browOut: 0.15, browAsym: 0.4, mOpen: 0.2, mWide: 0.1, mSmile: -0.15, saccade: 0.2 },
};
export function UX(name, over = {}) {
  const base = { ...FACE_DEFAULTS };
  const list = !Array.isArray(name) ? [[name, 1]] : typeof name[0] === 'string' ? [name] : name;   // 'x' | ['x', w] | [['a', wa], ...]
  for (const [nm, w = 1] of list) {
    const e = UEXPR[nm] || EXPR[nm] || {};
    for (const [key, val] of Object.entries(e)) base[key] = (base[key] ?? 0) + (val - (FACE_DEFAULTS[key] ?? 0)) * w;
  }
  return Object.assign(base, over);
}
function resolveFace(f) {
  if (f == null) return UX('idle');
  if (typeof f === 'string' || Array.isArray(f)) return UX(f);
  if (f.expr) { const { expr, ...rest } = f; return UX(expr, rest); }
  return { ...FACE_DEFAULTS, ...f };
}

// ---------------------------------------------------------------------------------------------------------
// Arm presets, written for the LEFT arm (x+ = character's left); mirrored for the right.
// t = wrist target, pole = elbow direction, palm = palm normal (= the phone screen's facing when the phone is in
// that hand), fing = finger direction, hand = pose params, grip = phone grip ('flat' | 'fist' | 'tuck').
// space: 'chest' (default; origin = waist pivot) | 'head' (head centre) | 'pelvis' | 'ground' (pelvis XZ, y on the floor)
export const ARM = {
  rest: { t: [0.255, -0.2, 0.035], pole: [0.35, -0.1, -1], palm: [-1, 0, 0.15], fing: [0.05, -1, 0.1], hand: { curl: 0.22, spread: 0.08, thumb: 0.2, cup: 0.2 } },
  hold: { t: [0.1, -0.05, 0.215], pole: [0.6, -0.5, -0.6], palm: [-0.2, 0.72, -0.66], fing: [-0.3, 0.62, 0.72], hand: { curl: 0.12, spread: 0.05, thumb: 0.4, cup: 0.3 }, grip: 'flat' },
  look: { t: [0.07, 0.15, 0.29], pole: [0.7, -1, -0.15], palm: [-0.18, 0.62, -0.76], fing: [-0.12, 0.8, 0.58], hand: { curl: 0.12, spread: 0.05, thumb: 0.4, cup: 0.3 }, grip: 'flat' },
  clutch: { t: [0.065, 0.055, 0.165], pole: [1, -0.7, 0.1], palm: [0.05, -0.05, -1], fing: [-0.45, 0.88, 0.05], hand: { curl: 0.3, spread: 0.06, thumb: 0.35, cup: 0.35 }, grip: 'flat' },
  hug: { t: [-0.055, 0.03, 0.2], pole: [1, -0.8, 0.2], palm: [0.15, 0.0, -1], fing: [-0.7, 0.68, 0.1], hand: { curl: 0.35, spread: 0.1, thumb: 0.3, cup: 0.45 } },
  defend: { t: [0.215, 0.375, 0.3], pole: [0.9, -0.75, -0.25], palm: [0.12, 0.05, 1], fing: [0.14, 1, 0.06], hand: { curl: 0.0, spread: 1, splay: 1, thumb: 1, cup: 0 } },
  stop: { t: [0.15, 0.14, 0.36], pole: [0.8, -1, -0.3], palm: [0.0, 0.05, 1], fing: [-0.05, 1, 0.12], hand: { curl: 0.05, spread: 0.55, splay: 0.35, thumb: 0.7, cup: 0.05 } },
  prop: { space: 'ground', t: [0.215, 0.04, -0.27], pole: [0.4, 0.5, -1], palm: [0, -1, 0.05], fing: [0.3, 0, -1], hand: { curl: 0.06, spread: 0.45, splay: 0.15, thumb: 0.5, cup: 0.05 }, grip: 'fist' },
  knee: { t: [0.15, -0.2, 0.3], pole: [1, -0.3, -0.4], palm: [-0.2, -0.9, 0.2], fing: [-0.1, -0.3, 1], hand: { curl: 0.35, spread: 0.12, thumb: 0.4, cup: 0.4 }, anim: 'knee' },
  lap: { space: 'pelvis', t: [0.07, 0.11, 0.2], pole: [1, -0.4, -0.3], palm: [-0.15, 0.95, -0.25], fing: [-0.3, 0.15, 0.95], hand: { curl: 0.12, spread: 0.05, thumb: 0.4, cup: 0.3 }, grip: 'flat' },
  crossed: { t: [-0.085, 0.085, 0.17], pole: [1, -0.6, 0.15], palm: [0, -0.4, -1], fing: [-1, 0.25, -0.2], hand: { curl: 0.6, spread: 0.05, thumb: 0.3 }, grip: 'tuck' },
  heart: { t: [0.035, 0.1, 0.155], pole: [1, -0.6, 0], palm: [0, 0, -1], fing: [-0.45, 0.85, 0.1], hand: { curl: 0.12, spread: 0.12, thumb: 0.35, cup: 0.2 } },
  pocket: { t: [0.06, -0.135, 0.13], pole: [1, -0.2, -0.4], palm: [-0.4, 0.1, -1], fing: [-0.75, -0.35, 0.3], hand: { curl: 0.4, spread: 0.05, thumb: 0.2 } },
  hips: { t: [0.26, -0.07, 0.02], pole: [1, 0.15, -0.5], palm: [-0.4, -0.2, -1], fing: [-0.35, -0.6, 0.6], hand: { curl: 0.85, thumb: 0.2 } },
  shield: { t: [0.06, 0.29, 0.24], pole: [0.8, -1, 0], palm: [0.05, 0.05, 1], fing: [-0.25, 0.95, 0.05], hand: { curl: 0.12, spread: 0.05, thumb: 0.4, cup: 0.3 }, grip: 'flat' },
  jab: { t: [0.11, 0.24, 0.47], pole: [1, -0.5, -0.2], palm: [0.0, 0.08, 1], fing: [-0.15, 1, 0.12], hand: { curl: 0.12, spread: 0.05, thumb: 0.4, cup: 0.3 }, grip: 'flat' },
  show: { t: [0.33, 0.6, 0.02], pole: [1, -0.3, 0.3], palm: [0.2, 0.05, -1], fing: [0.05, 1, 0.1], hand: { curl: 0.12, spread: 0.05, thumb: 0.4, cup: 0.3 }, grip: 'flat' },
  point: { t: [0.2, 0.2, 0.45], pole: [1, -0.6, -0.2], palm: [-1, 0, 0], fing: [0, 0.1, 1], hand: { point: 1, curl: 0.85, thumb: 0.2 } },
  shrug: { t: [0.3, 0.02, 0.19], pole: [0.3, -1, -0.5], palm: [0.15, 1, 0.1], fing: [0.55, 0.05, 1], hand: { curl: 0.12, spread: 0.42, thumb: 0.75, splay: 0.12, cup: 0.15 } },
  strings: { t: [0.035, 0.03, 0.2], pole: [1, -0.8, -0.1], palm: [-1, 0, 0.1], fing: [-0.1, -0.2, 1], hand: { curl: 0.75, thumb: 0.6, spread: 0.05 } },
  // face-space presets (relative to the head centre)
  wipe: { space: 'head', t: [0.085, -0.16, 0.1], pole: [0.8, -1, 0.2], palm: [-0.45, -0.25, -1], fing: [-0.45, 0.85, 0.15], hand: { curl: 0.85, thumb: 0.2 } },
  glasses: { space: 'head', t: [0.02, -0.17, 0.2], pole: [0.8, -1, 0.3], palm: [0.05, 0.1, -1], fing: [-0.12, 1, -0.1], hand: { point: 1, curl: 0.9, thumb: 0.15 } },
  cover_mouth: { space: 'head', t: [0.035, -0.235, 0.15], pole: [0.8, -1, 0.1], palm: [0, 0, -1], fing: [-0.35, 0.94, 0.0], hand: { curl: 0.1, spread: 0.1, thumb: 0.3, cup: 0.4 } },
  // running pumps / flails are procedural (see _armTarget)
};
const HAND_KEYS = ['curl', 'point', 'spread', 'thumb', 'cup', 'splay', 'grip'];
const HAND_DEF = { curl: 0.15, point: 0, spread: 0.15, thumb: 0.3, cup: 0.1, splay: 0, grip: 0 };

// Walk styles. The scene moves `pos` at stride * cycles/s (see User.walkSpeed()).
export const WALK = {
  walk: { rate: 0.95, stride: 0.92, stance: 0.62, lift: 0.075, bob: 0.017, bobPh: 0, sway: 0.016, twist: 0.12, lean: 0.04, arm: 0.14, run: 0, stomp: 0 },
  run: { rate: 1.45, stride: 1.7, stance: 0.38, lift: 0.19, bob: 0.042, bobPh: 0.16, sway: 0.014, twist: 0.2, lean: 0.2, arm: 0, run: 1, stomp: 0 },
  stomp: { rate: 1.0, stride: 0.8, stance: 0.6, lift: 0.14, bob: 0.012, bobPh: 0, sway: 0.024, twist: 0.1, lean: 0.17, arm: 0.17, run: 0, stomp: 1 },
  sneak: { rate: 0.6, stride: 0.55, stance: 0.66, lift: 0.06, bob: 0.01, bobPh: 0, sway: 0.01, twist: 0.06, lean: 0.14, arm: 0.04, run: 0, stomp: 0 },
};
function footCycle(u, S) {
  const L = S.stride * S.stance, sf = S.stance;
  let z, lift = 0, pitch = 0;
  if (u < sf) {
    const a = u / sf;
    z = lerp(0.5, -0.5, a);
    if (S.stomp) pitch = a > 0.62 ? lerp(0, 0.4, smooth((a - 0.62) / 0.38)) : 0;            // flat slam, no heel roll
    else pitch = a < 0.14 ? lerp(-0.25, 0, smooth(a / 0.14)) : a > 0.62 ? lerp(0, 0.55 + 0.35 * S.run, smooth((a - 0.62) / 0.38)) : 0;
  } else {
    const b = (u - sf) / (1 - sf);
    if (S.stomp) {                                               // knee up early, then a hard drop
      z = lerp(-0.5, 0.5, smooth(Math.min(1, b * 1.15)));
      lift = Math.pow(Math.sin(Math.PI * Math.min(1, b * 1.08) ** 0.75), 0.8);
      pitch = lerp(0.4, -0.05, smooth(b)) + 0.25 * Math.sin(Math.PI * b);
    } else {
      z = lerp(-0.5, 0.5, smooth(b));
      lift = Math.pow(Math.sin(Math.PI * b), 1.2);
      pitch = lerp(0.55 + 0.35 * S.run, -0.25, smooth(b)) + 0.25 * Math.sin(Math.PI * b) + S.run * 0.5 * bump(b, 0, 0.6);
    }
  }
  return { z: z * L, lift: lift * S.lift, pitch };
}
// ankle position for a foot planted at nominal ankle (x, z): heel up (pitch > 0) pivots on the ball,
// toes up (pitch < 0) pivots on the heel
function plantAnkle(x, z, lift, pitch, out) {
  let y = ANKLE_Y, zz = z;
  if (pitch > 0) { const bz = z + BALL_Z; y = ANKLE_Y * Math.cos(pitch) + BALL_Z * Math.sin(pitch); zz = bz + ANKLE_Y * Math.sin(pitch) - BALL_Z * Math.cos(pitch); }
  else if (pitch < 0) { const hz = z + HEEL_Z; y = ANKLE_Y * Math.cos(pitch) + HEEL_Z * Math.sin(pitch); zz = hz + ANKLE_Y * Math.sin(pitch) - HEEL_Z * Math.cos(pitch); }
  return out.set(x, y + lift, zz);
}

// Sit paths: s -> [pelY, pelZ, pelPitch, chestLean, fLz, fLy, fRz, fRy, footPitch, kneeOut]
const SIT_SEATED = [0.152, -0.2, -0.36, -0.03, 0.6, 0, 0.55, 0, -0.85, 0.14];
const SIT_STAND = [HIP_Y, 0, 0, 0, 0.02, 0, -0.01, 0, 0, 0];
const SIT_FALL = [
  [0.0, SIT_STAND],
  [0.2, [0.75, -0.04, -0.12, -0.04, 0.26, 0.0, 0.0, 0.0, -0.35, 0.0]],
  [0.42, [0.48, -0.13, -0.36, -0.16, 0.48, 0.16, 0.3, 0.1, -0.65, 0.04]],
  [0.62, [0.24, -0.19, -0.58, -0.26, 0.56, 0.33, 0.48, 0.27, -0.95, 0.1]],
  [0.78, [0.145, -0.21, -0.5, -0.22, 0.59, 0.2, 0.54, 0.16, -0.95, 0.12]],
  [0.9, [0.155, -0.2, -0.38, 0.06, 0.6, 0.06, 0.55, 0.05, -0.88, 0.13]],
  [1.0, SIT_SEATED],
];
const SIT_RISE = [
  [0.0, SIT_STAND],
  [0.22, [0.7, 0.01, 0.04, 0.2, 0.04, 0, 0.0, 0, 0, 0.01]],
  [0.42, [0.47, 0.03, 0.1, 0.48, 0.1, 0, 0.05, 0, 0.0, 0.05]],
  [0.62, [0.26, -0.02, 0.06, 0.55, 0.16, 0, 0.11, 0, 0.0, 0.09]],
  [0.82, [0.165, -0.16, -0.16, 0.24, 0.32, 0, 0.28, 0, -0.15, 0.12]],
  [1.0, SIT_SEATED],
];
const SIT_PLAIN = [[0, SIT_STAND], [1, SIT_SEATED]];

// Hoodie body profile (rest, root-local): [y, rx, rz, superellipse n, zOffset]
const TORSO = [
  [0.700, 0.168, 0.128, 2.4, 0.006], [0.716, 0.177, 0.137, 2.4, 0.006], [0.745, 0.187, 0.147, 2.4, 0.007],
  [0.80, 0.193, 0.151, 2.5, 0.009], [0.87, 0.191, 0.150, 2.5, 0.011], [0.94, 0.186, 0.143, 2.5, 0.009],
  [1.01, 0.186, 0.137, 2.5, 0.007], [1.08, 0.193, 0.135, 2.6, 0.009], [1.14, 0.201, 0.129, 2.7, 0.006],
  [1.185, 0.205, 0.121, 2.8, 0.002], [1.215, 0.197, 0.111, 2.6, -0.002], [1.240, 0.170, 0.099, 2.3, -0.006],
  [1.258, 0.130, 0.089, 2.1, -0.009], [1.270, 0.092, 0.079, 2.0, -0.011], [1.278, 0.07, 0.07, 2.0, -0.012],
];
function torsoProf(y) {
  const K = TORSO;
  if (y <= K[0][0]) return K[0].slice(1);
  if (y >= K[K.length - 1][0]) return K[K.length - 1].slice(1);
  let i = 0; while (y > K[i + 1][0]) i++;
  const u = (y - K[i][0]) / (K[i + 1][0] - K[i][0]);
  const a = K[Math.max(0, i - 1)], b = K[i], c = K[i + 1], d = K[Math.min(K.length - 1, i + 2)];
  const out = [];
  for (let k = 1; k < 5; k++) {
    const m1 = (c[k] - a[k]) / Math.max(1e-6, (c[0] - a[0])) * (c[0] - b[0]), m2 = (d[k] - b[k]) / Math.max(1e-6, (d[0] - b[0])) * (c[0] - b[0]);
    const u2 = u * u, u3 = u2 * u;
    out.push((2 * u3 - 3 * u2 + 1) * b[k] + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * c[k] + (u3 - u2) * m2);
  }
  return out;
}
const se = (s, n) => Math.sign(s) * Math.pow(Math.abs(s), 2 / n);
// kangaroo pocket mask (theta from the front, rest y)
function pocketMask(th, y) {
  const yy = smoothstep(0.755, 0.77, y) * (1 - smoothstep(0.915, 0.93, y));
  const half = lerp(0.66, 0.48, clamp((y - 0.77) / 0.15));
  return yy * (1 - smoothstep(half - 0.03, half + 0.01, Math.abs(th)));
}

// ---------------------------------------------------------------------------------------------------------
// Phone screens (generic social app: plain speech-bubble icon, grey cards; NO logos). Canvases are cached.
const SCR = { W: 320, H: 690 };
const _scr = {};
function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function bubbleIcon(g, cx, cy, s, col) {
  g.fillStyle = col; rr(g, cx - s, cy - s * 0.72, s * 2, s * 1.35, s * 0.55); g.fill();
  g.beginPath(); g.moveTo(cx - s * 0.45, cy + s * 0.5); g.lineTo(cx - s * 0.7, cy + s * 1.05); g.lineTo(cx - s * 0.02, cy + s * 0.55); g.fill();
}
function header(g, W) {
  g.fillStyle = '#f7f8fb'; g.fillRect(0, 0, W, 70);
  bubbleIcon(g, W / 2, 34, 15, '#6f8fd8');
  g.fillStyle = '#c6ccd6'; g.beginPath(); g.arc(30, 35, 13, 0, 7); g.fill();
  g.fillStyle = '#d8dde5'; g.fillRect(0, 68, W, 2);
}
function feedCanvas() {
  if (_scr.feed) return _scr.feed;
  const W = SCR.W, H = SCR.H * 2, c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.fillStyle = '#e9edf3'; g.fillRect(0, 0, W, H);
  const r = rng(404);
  const av = ['#f2b8a2', '#a9c8f0', '#b9e0c4', '#e3c3f0', '#f5d98f', '#9fd8d8'];
  let y = 8, k = 0;
  while (y < H - 10) {
    const img = k % 3 === 1, h = img ? 250 : 150;
    const hh = Math.min(h, H - 8 - y);
    g.fillStyle = '#ffffff'; rr(g, 10, y, W - 20, hh, 14); g.fill();
    g.fillStyle = av[k % av.length]; g.beginPath(); g.arc(40, y + 32, 18, 0, 7); g.fill();
    g.fillStyle = '#4a5160'; rr(g, 68, y + 20, 80 + r() * 50, 11, 5); g.fill();
    g.fillStyle = '#b9bfca'; rr(g, 68, y + 37, 50 + r() * 30, 8, 4); g.fill();
    g.fillStyle = '#c9ced8';
    let ty = y + 64;
    for (let i = 0; i < 2 + (k % 2); i++) { rr(g, 24, ty, (W - 60) * (i === 1 + (k % 2) ? 0.55 : 0.95 - r() * 0.15), 9, 4.5); g.fill(); ty += 18; }
    if (img) { g.fillStyle = ['#cfe1f7', '#f6dccf', '#dcd3f2'][k % 3]; rr(g, 24, ty + 4, W - 48, 100, 10); g.fill(); ty += 110; }
    g.fillStyle = '#d3d8e0';
    for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(36 + i * 68, y + hh - 18, 6, 0, 7); g.fill(); }
    y += h + 10; k++;
  }
  return (_scr.feed = c);
}
function avatar(g, cx, cy, R) {   // a generic friendly bearded face (the profile picture)
  g.save(); g.beginPath(); g.arc(cx, cy, R, 0, 7); g.clip();
  g.fillStyle = '#f3dfb8'; g.fillRect(cx - R, cy - R, 2 * R, 2 * R);
  g.fillStyle = '#4a2c1b'; g.beginPath(); g.ellipse(cx, cy - R * 0.05, R * 0.62, R * 0.78, 0, 0, 7); g.fill();
  g.fillStyle = '#c99872'; g.beginPath(); g.ellipse(cx, cy + R * 0.02, R * 0.42, R * 0.5, 0, 0, 7); g.fill();
  g.fillStyle = '#4a2c1b'; g.beginPath(); g.ellipse(cx, cy + R * 0.3, R * 0.44, R * 0.3, 0, 0, Math.PI); g.fill();
  g.fillStyle = '#4a2c1b'; g.fillRect(cx - R * 0.44, cy + R * 0.12, R * 0.88, R * 0.2);
  g.fillStyle = '#2a1810'; for (const s of [-1, 1]) { g.beginPath(); g.arc(cx + s * R * 0.16, cy - R * 0.06, R * 0.05, 0, 7); g.fill(); }
  g.strokeStyle = '#fff4e8'; g.lineWidth = R * 0.07; g.lineCap = 'round'; g.beginPath(); g.arc(cx, cy + R * 0.12, R * 0.15, 0.25, Math.PI - 0.25); g.stroke();
  g.fillStyle = '#e8ecf2'; g.fillRect(cx - R, cy + R * 0.72, 2 * R, R);
  g.restore();
}
function screenCanvas(mode, name) {
  const key = mode + '|' + name;
  if (_scr[key]) return _scr[key];
  const W = SCR.W, H = SCR.H, c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.textAlign = 'center'; g.textBaseline = 'middle';
  if (mode === 'block') {
    g.drawImage(feedCanvas(), 0, 0, W, H, 0, 70, W, H);
    header(g, W);
    g.fillStyle = 'rgba(16,20,30,0.55)'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#ffffff'; rr(g, 22, 190, W - 44, 300, 22); g.fill();
    g.fillStyle = '#1e2430'; g.font = 'bold 30px sans-serif'; g.fillText(`Block ${name}?`, W / 2, 238);
    g.fillStyle = '#7a8291'; g.font = '17px sans-serif';
    g.fillText('They won’t be able to message', W / 2, 284); g.fillText('you or see your posts.', W / 2, 306);
    g.fillStyle = '#e5484d'; rr(g, 42, 344, W - 84, 54, 27); g.fill();
    g.fillStyle = '#ffffff'; g.font = 'bold 25px sans-serif'; g.fillText('Block', W / 2, 372);
    g.strokeStyle = '#c3c8d1'; g.lineWidth = 3; rr(g, 42, 414, W - 84, 50, 25); g.stroke();
    g.fillStyle = '#5d6573'; g.font = 'bold 21px sans-serif'; g.fillText('Cancel', W / 2, 440);
  } else {   // 'blocked' | 'profile'
    g.fillStyle = '#eef1f5'; g.fillRect(0, 0, W, H);
    header(g, W);
    const gr = g.createLinearGradient(0, 70, W, 200); gr.addColorStop(0, '#f6d7c3'); gr.addColorStop(1, '#cfd9f5');
    g.fillStyle = gr; g.fillRect(0, 70, W, 120);
    g.fillStyle = '#ffffff'; g.beginPath(); g.arc(78, 196, 52, 0, 7); g.fill();
    avatar(g, 78, 196, 46);
    g.textAlign = 'left';
    g.fillStyle = '#1e2430'; g.font = 'bold 30px sans-serif'; g.fillText(name, 26, 278);
    g.fillStyle = '#9aa1ad'; rr(g, 26, 300, 110, 10, 5); g.fill();
    g.textAlign = 'center';
    if (mode === 'profile') {
      g.fillStyle = '#4a5160'; g.font = '18px sans-serif';
      g.fillText('Would love to hear', W / 2, 352); g.fillText('about your feelings.', W / 2, 376);
      g.fillStyle = '#e5484d'; rr(g, 42, 420, W - 84, 54, 27); g.fill();
      g.fillStyle = '#ffffff'; g.font = 'bold 25px sans-serif'; g.fillText('Block', W / 2, 448);
    } else {
      g.fillStyle = '#ffffff'; rr(g, 18, 336, W - 36, 120, 18); g.fill();
      g.strokeStyle = '#e5484d'; g.lineWidth = 5; g.beginPath(); g.arc(W / 2, 372, 17, 0, 7); g.stroke();
      g.beginPath(); g.moveTo(W / 2 - 12, 384); g.lineTo(W / 2 + 12, 360); g.stroke();
      g.fillStyle = '#1e2430'; g.font = 'bold 22px sans-serif'; g.fillText(`You blocked ${name}.`, W / 2, 422);
      g.strokeStyle = '#c3c8d1'; g.lineWidth = 3; rr(g, 60, 486, W - 120, 48, 24); g.stroke();
      g.fillStyle = '#5d6573'; g.font = 'bold 20px sans-serif'; g.fillText('Unblock', W / 2, 511);
    }
    g.fillStyle = '#dfe3ea';
    for (let i = 0; i < 2; i++) { rr(g, 18, 560 + i * 60, W - 36, 46, 12); g.fill(); }
  }
  return (_scr[key] = c);
}
const SCREEN_LUM = { feed: 0.95, block: 0.5, blocked: 0.85, profile: 0.85, off: 0 };
// default thumb hover/tap point per screen (u right, v down): the red Block button on 'block'
const THUMB_AT = { feed: [0.58, 0.62], block: [0.5, 0.538], blocked: [0.6, 0.84], profile: [0.5, 0.65], off: [0.5, 0.7] };

// ---------------------------------------------------------------------------------------------------------
/**
 * UHand — one-piece-finger soft hand (palm + swept fingers). Local frame: wrist at origin, fingers +Y, palm faces
 * -Z, thumb on the anatomically correct side (RIGHT hand: -X, LEFT hand: +X). Extra phone controls:
 * pose({ ..., thumbTo: Vector3|null (thumb tip target, hand-local), thumbW: 0..1 })
 */
class UHand {
  constructor({ size = 0.15, side = 'R', material }) {
    this.size = size; this.side = side;
    const ts = this.ts = side === 'L' ? 1 : -1;
    this.root = new THREE.Group();
    const pl = this.pl = size * 0.46, pw2 = this.pw = size * 0.47, pt = this.pt = size * 0.2;
    const palm = new THREE.Mesh(new THREE.SphereGeometry(1, 22, 14), material);
    palm.scale.set(pw2 * 0.53, pl * 0.58, pt * 0.52); palm.position.set(0, pl * 0.52, -pt * 0.05);
    const heel = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 10), material);
    heel.scale.set(pw2 * 0.4, pl * 0.32, pt * 0.5); heel.position.set(ts * pw2 * 0.06, pl * 0.18, -pt * 0.04);
    this.root.add(palm, heel);
    bake(this.root, [palm, heel]);
    const lens = [0.93, 1.0, 0.95, 0.78];
    this.fingers = [0, 1, 2, 3].map((i) => {
      const u = (i - 1.5) / 1.5;                                    // index = -1 (thumb side)
      const tube = new SweepTube({ material, segments: 9, radial: 8, capRings: 2 });
      this.root.add(tube.mesh);
      const L = size * 0.5 * lens[i];
      return { i, u, base: V(-ts * u * pw2 * 0.37, pl * 0.9, -pt * 0.02), segs: [0.44, 0.31, 0.25].map((f) => f * L), r: size * 0.074 * (i === 3 ? 0.86 : i === 0 ? 1.0 : 0.97), tube, pts: [V(), V(), V(), V(), V()] };
    });
    this.thumb = { base: V(ts * pw2 * 0.34, pl * 0.2, -pt * 0.2), segs: [0.2, 0.19, 0.15].map((f) => f * size), r: size * 0.084, tube: new SweepTube({ material, segments: 8, radial: 8, capRings: 2 }), pts: [V(), V(), V(), V()] };
    this.root.add(this.thumb.tube.mesh);
    this.pose({});
  }
  aim(fingerDir, palmNormal) { return orientYZ(this.root, fingerDir, palmNormal.clone().multiplyScalar(-1)); }
  pose({ curl = 0.15, point = 0, spread = 0.15, thumb = 0.3, cup = 0.1, splay = 0, grip = 0, perFinger = null, thumbTo = null, thumbW = 0 } = {}) {
    const ts = this.ts, pn = V(0, 0, -1);
    for (const f of this.fingers) {
      let c = perFinger ? perFinger[f.i] : curl;
      c = lerp(c, f.i === 0 ? 0 : 1, point);
      c = lerp(c, 0.55, grip);
      const extra = f.i * 0.05 * c;
      const mcp = c * 1.3 + cup * 0.32 - splay * 0.42 + extra;
      const pip = c * 1.6 + cup * 0.12 - splay * 0.14;
      const dip = c * 1.0 + cup * 0.08;
      const fan = ts * f.u * (spread * 0.34 + 0.035);
      const fd = V(-Math.sin(fan), Math.cos(fan), 0);
      const dirAt = (a) => fd.clone().multiplyScalar(Math.cos(a)).addScaledVector(pn, Math.sin(a));
      const P = f.pts;
      P[0].copy(f.base).addScaledVector(fd, -f.r * 1.2);
      P[1].copy(f.base);
      P[2].copy(P[1]).addScaledVector(dirAt(mcp), f.segs[0]);
      P[3].copy(P[2]).addScaledVector(dirAt(mcp + pip), f.segs[1]);
      P[4].copy(P[3]).addScaledVector(dirAt(mcp + pip + dip), f.segs[2]);
      f.tube.update(P, [f.r * 1.05, f.r, f.r * 0.95, f.r * 0.88, f.r * 0.8]);
    }
    const T = this.thumb, P = T.pts;
    const across = clamp(curl * 0.8 + grip * 0.6 + cup * 0.35);
    let d0 = V(ts * lerp(0.35, 0.95, thumb), lerp(0.88, 0.4, thumb), -0.28).normalize();
    d0.lerp(V(-ts * 0.15, 0.55, -0.82), across * 0.6).normalize();
    const bendAx = V(-ts * 0.45, 0, -0.9).normalize();
    const d1 = d0.clone().addScaledVector(bendAx, 0.25 + across * 0.7).normalize();
    const d2 = d1.clone().addScaledVector(bendAx, 0.2 + across * 0.9).normalize();
    P[0].copy(T.base);
    P[1].copy(P[0]).addScaledVector(d0, T.segs[0]);
    P[2].copy(P[1]).addScaledVector(d1, T.segs[1]);
    P[3].copy(P[2]).addScaledVector(d2, T.segs[2]);
    if (thumbTo && thumbW > 0) {                     // reach the tip toward a point (e.g. on the phone screen)
      const tip = P[3].clone().lerp(thumbTo, thumbW);
      const mid = P[0].clone().lerp(tip, 0.5);
      const out = V(ts * 0.6, 0, -0.8).normalize();  // knuckle bulges out, away from the palm centre
      const L0 = T.segs[0] + T.segs[1] + T.segs[2], dd = P[0].distanceTo(tip);
      const bulge = Math.sqrt(Math.max(0, L0 * L0 - dd * dd)) * 0.32;
      P[1].lerp(P[0].clone().lerp(mid, 0.75).addScaledVector(out, bulge * 0.8), thumbW);
      P[2].lerp(mid.clone().lerp(tip, 0.55).addScaledVector(out, bulge), thumbW);
      P[3].copy(tip);
    }
    T.tube.update(P, [T.r * 1.25, T.r * 1.02, T.r * 0.95, T.r * 0.85]);
    return this;
  }
}

// ---------------------------------------------------------------------------------------------------------
class User extends Character {
  constructor() {
    super({ name: 'USER', speaker: 'USER', height: 1.65, seed: 23 });
    this.Mp = new THREE.Matrix4(); this.Mc = new THREE.Matrix4(); this.Mh = new THREE.Matrix4();
    this.rootInv = new THREE.Matrix4(); this.rootQInv = new THREE.Quaternion(); this.rootQ = new THREE.Quaternion();
    this.PU = { pos: { value: V() }, dir: { value: V(0, 0, 1) }, col: { value: new THREE.Color(0, 0, 0) } };
    this.phW = V(); this.phN = V(0, 0, 1);
    this.HS = { swing: { value: V() }, bounce: { value: 0 } };
    this._mats();
    this._skeleton();
    this._buildHead();
    this._buildHair();
    this._buildGlasses();
    this._buildTorso();
    this._buildHood();
    this._buildArms();
    this._buildPhone();
    this._buildLegs();
    this._buildTears();
    this._buildAnchors();
    // phone-glow uniforms go to view space right before each draw (always the camera that renders)
    const tmp = V();
    const obr = (r, s, cam) => {
      const m = cam.matrixWorldInverse;
      this.PU.pos.value.copy(this.phW).applyMatrix4(m);
      this.PU.dir.value.copy(this.phN).transformDirection(m);
      tmp.set(0, 0, 0);
    };
    this.root.traverse((o) => { if (o.isMesh) o.onBeforeRender = obr; });
    // outer layers first (early-z rejects what's underneath)
    const layer = (mats, ro) => this.root.traverse((o) => { if (o.isMesh && mats.includes(o.material)) o.renderOrder = ro; });
    layer([this.hairMat], -3);
    layer([this.hoodieMat, this.sleeveMat], -2);
    this.tapEv = schedule(this.seed * 31 + 3, -4, 3000, 0.28, 0.6);
    this.update(0, {});
  }

  /** metres per walk cycle; move pos at walkSpeed(style) * walkRate(style) m/s */
  walkSpeed(style = 'walk') { return (WALK[style] || WALK.walk).stride; }
  walkRate(style = 'walk') { return (WALK[style] || WALK.walk).rate; }
  /** metres the seated body travels backward per scoot cycle (move pos backward at scootSpeed * scoot rate) */
  scootSpeed(amount = 1) { return 0.09 * amount; }

  // ------------------------------------------------------------------ materials
  _mats() {
    const U = this.PU;
    const sk = { rim: 0.38, rimColor: 0xffc49a, wrap: 0.45, wrapColor: 0xff7058, sheen: 0.3, sheenColor: 0xffd8c0, roughness: 0.5, glow: 0.05 };
    this.headSkin = phoneLit(skin(SKIN, { ...sk, jaw: JAW }), U);
    this.bodySkin = phoneLit(skin(SKIN, sk), U);
    this.hairMat = hairSwing(phoneLit(hair(HAIR_C, { rim: 0.45, rimColor: 0xffc890, sheenColor: 0x9a6c4c, roughness: 0.5 }), U), this.HS);
    this.hoodieMat = phoneLit(cloth(0xffffff, { sheen: 0.55, sheenColor: 0x9fb4e0, rim: 0.3, rimColor: 0xc8d8ff, roughness: 0.88 }), U);
    this.hoodieMat.color.set(HOODIE);
    this.sleeveMat = phoneLit(cloth(HOODIE, { sheen: 0.55, sheenColor: 0x9fb4e0, rim: 0.3, rimColor: 0xc8d8ff, roughness: 0.88 }), U);
    this.jogMat = cloth(JOG, { sheen: 0.45, sheenColor: 0x7c8090, rim: 0.22, rimColor: 0xc0c8e0, roughness: 0.9 });
    this.shoeMat = cloth(SNEAK, { sheen: 0.2, sheenColor: 0xffffff, rim: 0.15, rimColor: 0xffffff, roughness: 0.62 });
    this.soleMat = cloth(SOLE, { sheen: 0.1, rim: 0.1, roughness: 0.7 });
    this.outsoleMat = cloth(OUTSOLE, { sheen: 0.1, rim: 0.05, roughness: 0.8 });
    this.laceMat = cloth(LACE, { sheen: 0.2, rim: 0.1, roughness: 0.8 });
    this.tabMat = cloth(HOODIE, { sheen: 0.3, rim: 0.1, roughness: 0.75 });
    this.stringMat = cloth(0xeeeae2, { sheen: 0.3, rim: 0.15, roughness: 0.8 });
    this.agletMat = new THREE.MeshStandardMaterial({ color: 0xd8dde4, roughness: 0.3, metalness: 0.7 });
    this.frameMat = new THREE.MeshStandardMaterial({ color: FRAME, roughness: 0.32, metalness: 0.1 });
    this.caseMat = phoneLit(cloth(CASE, { sheen: 0.3, sheenColor: 0xffc0b0, rim: 0.2, rimColor: 0xffd0c0, roughness: 0.45 }), U);
    this.bumpMat = new THREE.MeshStandardMaterial({ color: 0x23262e, roughness: 0.35 });
    this.decalMat = phoneLit(new THREE.MeshStandardMaterial({ transparent: true, roughness: 0.55, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }), U);
    this.tearMat = new THREE.MeshStandardMaterial({ color: 0xdff0ff, roughness: 0.06, metalness: 0.0, emissive: 0x6d8fb8, emissiveIntensity: 0.55, transparent: true, opacity: 0.9 });
    this.wetMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.25, 1.35, 1.5), transparent: true, opacity: 0, depthWrite: false });
    for (const m of [this.jogMat, this.shoeMat, this.soleMat, this.outsoleMat, this.laceMat, this.tabMat, this.stringMat, this.caseMat]) m.sheen = 0;
    this._rims = [[this.headSkin, 0.38], [this.bodySkin, 0.38], [this.hairMat, 0.5], [this.hoodieMat, 0.3], [this.sleeveMat, 0.3]];
  }

  _skeleton() {
    this.pelvisG = new THREE.Group(); this.root.add(this.pelvisG);
    this.chestG = new THREE.Group(); this.pelvisG.add(this.chestG);
    this.neckG = new THREE.Group(); this.chestG.add(this.neckG);
    this.headPivot = new THREE.Group(); this.neckG.add(this.headPivot);
    this.headG = new THREE.Group(); this.headPivot.add(this.headG);
    this.headGroup = this.headG;
    this.chestG.position.y = WAIST_H;
    this.neckG.position.set(0, NECK_BASE, -0.012);
    this.headPivot.position.set(0, NECK_LEN, 0.006);
    this.headG.position.set(0, HEAD_UP, 0); this.headG.scale.setScalar(HEAD_SCALE);
    for (const g of [this.pelvisG, this.chestG, this.neckG, this.headPivot]) g.rotation.order = 'YXZ';
  }

  // ------------------------------------------------------------------ head, nose, face
  _buildHead() {
    const g = new THREE.SphereGeometry(1, 50, 38);
    g.deleteAttribute('uv'); g.deleteAttribute('normal');
    const P = g.attributes.position, tmp = V();
    for (let i = 0; i < P.count; i++) {
      tmp.fromBufferAttribute(P, i).normalize();
      const v = Math.asin(clamp(tmp.y, -1, 1)), u = Math.atan2(tmp.x, tmp.z);
      headPoint(u, v, tmp); P.setXYZ(i, tmp.x, tmp.y, tmp.z);
    }
    const geo = mergeVertices(g); geo.computeVertexNormals();
    this.headMesh = new THREE.Mesh(geo, this.headSkin); this.headMesh.castShadow = true;
    this.headG.add(this.headMesh);
    // small upturned button nose (lofted)
    const nTop = headSurf(0, EYE_V - 0.09).p, nBot = headSurf(0, -0.25).p;
    const ng = new THREE.SphereGeometry(1, 20, 18);
    const NP = ng.attributes.position;
    for (let i = 0; i < NP.count; i++) {
      const xs = NP.getX(i), ys = NP.getY(i), zs = NP.getZ(i);
      const t = (1 - ys) / 2;
      const cy = lerp(nTop.y + 0.004, nBot.y + 0.002, t), cz = lerp(nTop.z - 0.006, nBot.z + 0.004, Math.pow(t, 1.2));
      let W = lerp(0.005, 0.0105, t) + 0.0072 * smoothstep(0.6, 0.95, t);
      W *= 1 + 0.35 * smoothstep(0.62, 0.95, t) * Math.max(0, -zs);
      const D = lerp(0.003, 0.0145, Math.pow(t, 1.25));
      NP.setXYZ(i, xs * W, cy + 0.0035 * Math.max(0, zs) * smoothstep(0.55, 1, t) - 0.002 * smoothstep(0.85, 1, t), cz + zs * D);
    }
    ng.deleteAttribute('normal'); ng.deleteAttribute('uv');
    const ngm = mergeVertices(ng); ngm.computeVertexNormals();
    this.nose = new THREE.Mesh(ngm, this.bodySkin); this.headG.add(this.nose);
    // small ears (mostly under the bob)
    const ears = [1, -1].map((s) => { const e = new THREE.Mesh(new THREE.SphereGeometry(0.027, 16, 12), this.bodySkin); e.position.set(s * 0.132, -0.02, -0.01); e.scale.set(0.45, 1.05, 0.75); e.rotation.set(0, s * -0.35, s * 0.08); this.headG.add(e); return e; });
    bake(this.headG, [this.nose, ...ears]);
    // freckles (fixed, deterministic)
    const r = rng(9001);
    this.freckles = [];
    for (let i = 0; i < 34; i++) {
      const side = i % 2 ? 1 : -1, onNose = i < 8;
      const u = onNose ? (r() - 0.5) * 0.22 : side * lerp(0.24, 0.66, r());
      const v = onNose ? lerp(-0.1, -0.18, r()) : lerp(-0.15, -0.3, r()) - 0.03 * Math.abs(u);
      this.freckles.push([u, v, lerp(0.0011, 0.002, r()), lerp(0.25, 0.45, r())]);
    }
    this.face = new Face({
      head: this.headG, surface: headSurf, seed: 23,
      eyes: {
        u: EYE_U, v: EYE_V, radius: EYE_R, sink: 0.66, splay: 0.09, lidMaterial: this.bodySkin, scale: [1, 1.05, 1],
        iris: 0x4b6a33, iris2: 0xc39a52, irisR: 0.66, pupilR: 0.27, limbal: 0x18220f, sclera: 0xf8f4ef,
        lash: 1.4, lowerLash: 0.55, lashColor: 0x1b100b, lowRelaxed: -0.56, lowRaised: 0.22, upOpen: 0.5, upWide: 1.03, maxYaw: 0.66, maxPitch: 0.5,
      },
      brows: { color: BROW_C, thickness: 0.0086, lift: 0.002, inner: [0.13, 0.335], mid: [0.37, 0.405], outer: [0.62, 0.35], range: 0.15, flatten: 0.5, profile: [0.92, 1.06, 0.9, 0.45] },
      mouth: {
        v: MOUTH_V, halfW: HW0, line: '#5c2320', lineW: HW0 * 0.16, interior: '#3a0d14', interior2: '#6c2029', teeth: '#fbf6ee',
        tongue: '#d4646c', lipTintRGB: '214,104,104', blushColor: '246,118,104', blushX: HW0 * 2.55, blushY: HW0 * 1.8,
        drawExtra: (gg, p) => this._drawExtra(gg, p),
      },
      decal: { uMin: -0.92, uMax: 0.92, vMin: MOUTH_V - 0.32, vMax: EYE_V - 0.02, size: [512, 352], material: this.decalMat },
      jaw: [this.headSkin.userData.uJaw],
    });
    // wet tear line on each lower lid + phone reflection on each cornea
    this.wetLines = []; this.eyeRefl = [];
    for (const eye of this.face.eyes) {
      const rl = eye.r * 1.035;
      const tg = new THREE.TorusGeometry(rl * 1.01, eye.r * 0.055, 5, 26, Math.PI * 0.72);
      tg.rotateZ(Math.PI * 0.14);
      const m = new THREE.Mesh(tg, this.wetMat); m.rotation.x = Math.PI / 2; m.renderOrder = 3;
      eye.lo.add(m); this.wetLines.push(m);
      const rm = new THREE.Mesh(new THREE.PlaneGeometry(eye.r * 0.15, eye.r * 0.24), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.85, 0.93, 1.1), transparent: true, opacity: 0, depthWrite: false, toneMapped: false }));
      eye.inner.add(rm); this.eyeRefl.push(rm);
    }
  }

  // freckles, rosy cheeks, lips — painted into the face decal (metres around the mouth centre, +y up)
  _drawExtra(g, p) {
    const d = this.face.decal;
    g.save();
    // permanent soft rosy cheeks + nose tip
    for (const sx of [-1, 1]) {
      const cx = sx * 0.5 * d.rxEff, cy = (-0.24 - MOUTH_V) * d.ryEff;
      const gr = g.createRadialGradient(cx, cy, 0, cx, cy, 0.03);
      gr.addColorStop(0, `rgba(240,120,110,${0.16 + 0.25 * (p.blush || 0)})`); gr.addColorStop(1, 'rgba(240,120,110,0)');
      g.fillStyle = gr; g.beginPath(); g.ellipse(cx, cy, 0.032, 0.022, 0, 0, Math.PI * 2); g.fill();
    }
    // freckles
    for (const [u, v, rad, a] of this.freckles) {
      g.fillStyle = `rgba(150,78,48,${a})`;
      g.beginPath(); g.ellipse(u * d.rxEff, (v - MOUTH_V) * d.ryEff, rad, rad * 0.85, 0, 0, Math.PI * 2); g.fill();
    }
    // lower lip tint (soft) under the mouth line
    const open = clamp(p.mOpen, 0, 1.3) * (1 - clamp(p.close ?? 0));
    const press = clamp(p.mPress), wide = clamp(p.mWide, -1, 1), round = clamp(p.mRound);
    const w = HW0 * (1 + 0.3 * wide) * (1 - 0.45 * round) * (1 + 0.22 * clamp(p.mClench)) * (1 - 0.18 * press);
    const h = HW0 * 1.75 * open + round * HW0 * 0.7 * Math.min(1, open * 4);
    const sm = clamp(p.mSmile, -1, 1);
    const shift = (p.mShift || 0) * HW0 * 0.4;
    const ly = -h * 0.72 - HW0 * (0.2 + 0.1 * (p.mPout || 0)) + Math.min(0, sm) * HW0 * 0.12;
    const gr = g.createRadialGradient(shift, ly, 0, shift, ly, w * 0.7);
    gr.addColorStop(0, `rgba(205,96,96,${0.42 - 0.15 * press + 0.15 * (p.mPout || 0)})`); gr.addColorStop(1, 'rgba(205,96,96,0)');
    g.fillStyle = gr; g.beginPath(); g.ellipse(shift, ly, w * 0.68, HW0 * (0.2 + 0.08 * (p.mPout || 0)), 0, 0, Math.PI * 2); g.fill();
    // chin dimple / crumple when the lips press and pout (about to cry)
    const cr = clamp(press * 0.6 + (p.mPout || 0) * 0.6 + (p.mTremble || 0) * 0.3 - 0.3);
    if (cr > 0.01) {
      g.strokeStyle = `rgba(150,70,55,${0.22 * cr})`; g.lineWidth = 0.0016; g.lineCap = 'round';
      g.beginPath(); g.arc(shift, ly - HW0 * 0.75, HW0 * 0.35, Math.PI * 0.15, Math.PI * 0.85); g.stroke();
    }
    g.restore();
  }

  // ------------------------------------------------------------------ hair: cap shell + chunky sculpted locks + cowlick
  _lockPts(keys, hang = true) {
    // keys: [[u, v, off], ...] on the head; below the cheekbones the hair falls straight (radius >= the widest point)
    return keys.map(([u, v, off, dr = 0, dy = 0]) => {
      const { p, n } = headSurf(u, v);
      p.addScaledVector(n, off);
      if (hang && v < 0.08) {
        const top = headSurf(u, 0.08); top.p.addScaledVector(top.n, off);
        const rTop = Math.hypot(top.p.x, top.p.z), rP = Math.hypot(p.x, p.z);
        const rr2 = Math.max(rP, rTop) + dr;
        const a = Math.atan2(p.x, p.z);
        p.x = Math.sin(a) * rr2; p.z = Math.cos(a) * rr2;
      } else if (dr) { const a = Math.atan2(p.x, p.z), rP = Math.hypot(p.x, p.z) + dr; p.x = Math.sin(a) * rP; p.z = Math.cos(a) * rP; }
      p.y += dy;
      return p;
    });
  }
  _buildHair() {
    // ONE sculpted shell: crown rows hug the skull (side part, broad flow grooves); on the sides and back the
    // hair falls straight from the widest point to the jaw (slight A-line flare) and rolls under at the ends
    // (thick rounded bob edge). The face side of the curtain is a diagonal from the temple to the jaw.
    const J = 68, K = 14, H = 8, R = H + 2 + K + 1;
    const pos = new Float32Array(J * R * 3);
    const at = (j, r) => (j * R + r) * 3;
    for (let j = 0; j < J; j++) {
      const u = -Math.PI + (j / J) * 2 * Math.PI, au = Math.abs(u), vh = hairline(u);
      const cw = smoothstep(0.88, 1.2, au);                         // 0 = face (fringe covers), 1 = hanging curtain
      const back = Math.max(0, -Math.cos(u));
      const vEnd = lerp(vh, 0.1, cw);
      const thick = (v) => {
        let T = 0.014 + 0.012 * smoothstep(0.2, 1.2, v);
        const part = Math.exp(-(((u - 0.3) / 0.07) ** 2)) * smoothstep(0.75, 1.0, v) * (1 - smoothstep(1.25, 1.45, v));
        T *= 1 - 0.55 * part;
        T *= 1 + 0.1 * Math.sin(u * 9 + 0.5) * smoothstep(0.2, 0.9, v) * (1 - smoothstep(1.2, 1.45, v));   // chunky flow grooves
        return T;
      };
      for (let k = 0; k <= K; k++) {
        const v = lerp(Math.PI / 2 - 1e-3, vEnd, Math.pow(k / K, 1.1));
        const { p, n } = headSurf(u, v);
        const e = clamp((v - vh) / 0.1);
        p.addScaledVector(n, lerp(-0.002, thick(v), cw > 0.5 ? 1 : Math.sqrt(e)));
        pos.set([p.x, p.y, p.z], at(j, H + 2 + (K - k)));
      }
      // hanging curtain (rows H+1 .. 0), Bezier from A (bottom skull row) to the tip, then the roll-under
      const A = V(...pos.slice(at(j, H + 2), at(j, H + 2) + 3));
      const d = V(Math.sin(u), 0, Math.cos(u));
      const RA = Math.hypot(A.x, A.z);
      const yTip = -0.122 + 0.012 * back - 0.008 * Math.max(0, Math.cos(u)) + 0.006 * Math.sin(u * 4.3 + 0.7);
      const tipFull = d.clone().multiplyScalar(RA + 0.006 + 0.004 * Math.sin(u * 3.1)).setY(yTip);
      const tip = A.clone().lerp(tipFull, cw);
      const c1 = A.clone().add(V(0, -0.06 * cw, 0)).addScaledVector(d, 0.004 * cw), c2 = tip.clone().add(V(0, 0.07 * cw, 0)).addScaledVector(d, -0.004 * cw);
      for (let i = 0; i <= H; i++) {
        const sb = i / H, m = 1 - sb;                                  // sb = 0 at the tip -> 1 at A
        const q = tip.clone().multiplyScalar(m * m * m).addScaledVector(c2, 3 * m * m * sb).addScaledVector(c1, 3 * m * sb * sb).addScaledVector(A, sb * sb * sb);
        q.addScaledVector(d, 0.006 * Math.sin(sb * Math.PI) * cw);
        pos.set([q.x, q.y, q.z], at(j, i + 1));
      }
      // rolled-under end: tucks toward the neck and slightly up (thick, rounded bob edge)
      const T0 = V(...pos.slice(at(j, 1), at(j, 1) + 3));
      T0.addScaledVector(d, -0.02 * cw).add(V(0, 0.016 * cw, 0));
      pos.set([T0.x, T0.y, T0.z], at(j, 0));
    }
    const idx = [];
    for (let j = 0; j < J; j++) for (let r = 0; r < R - 1; r++) {
      const a2 = j * R + r, b2 = ((j + 1) % J) * R + r;
      idx.push(a2, b2, a2 + 1, b2, b2 + 1, a2 + 1);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(idx);
    g.computeVertexNormals();
    const shell = new THREE.Mesh(g, this.hairMat); shell.castShadow = true;
    this.hairShell = shell;
    this.headG.add(shell);
    // chunky accent locks: swept fringe (kept above the brows), face-framing clumps, curtain clumps
    const r = rng(77);
    const locks = [];
    const fr = [
      { keys: [[0.34, 1.12, 0.018], [0.14, 0.92, 0.026], [-0.18, 0.76, 0.026], [-0.42, 0.66, 0.022]], w: 0.085 },
      { keys: [[0.3, 1.05, 0.018], [0.02, 0.86, 0.026], [-0.45, 0.72, 0.026], [-0.82, 0.52, 0.024]], w: 0.08 },
      { keys: [[0.42, 1.05, 0.018], [0.3, 0.86, 0.025], [0.16, 0.7, 0.02]], w: 0.07 },
      { keys: [[0.44, 1.04, 0.018], [0.6, 0.86, 0.025], [0.76, 0.66, 0.023]], w: 0.07 },
      { keys: [[-0.1, 1.15, 0.02], [-0.6, 0.92, 0.028], [-0.98, 0.6, 0.028], [-1.06, 0.3, 0.026]], w: 0.08 },
    ];
    for (const f of fr) locks.push({ ...f, hang: false, flat: 0.72, tip: 0.55 });
    // curtain clumps (on top of the shell): follow the column straight down, a few flick out / tuck under
    const cl = [1.02, 1.42, 1.9, 2.55, -3.0, -2.3, -1.75, -1.3, -1.06];
    cl.forEach((u, i) => {
      const fl = i % 3 === 0 ? 0.012 : i % 3 === 1 ? -0.006 : 0.003;
      const vEnd = -0.5 - 0.08 * r();
      locks.push({ keys: [[u * 0.8, 0.95, 0.018], [u, 0.55, 0.027], [u, 0.12, 0.029], [u, -0.2, 0.027, 0.003], [u - Math.sign(u) * 0.05, vEnd, 0.022, fl, fl > 0 ? 0.005 : 0.0]], w: 0.07 + 0.02 * r(), flat: 0.86, tip: 0.45 });
    });
    const geos = [];
    const tube = new SweepTube({ material: this.hairMat, segments: 13, radial: 8, capRings: 2 });
    for (const L of locks) {
      const pts = this._lockPts(L.keys, L.hang !== false);
      const ups = pts.map((p) => p.clone().normalize());
      const w = L.w, tp = L.tip;
      tube.update(pts, (s) => w * 0.5 * (0.45 + 0.55 * smoothstep(0, 0.2, s)) * (1 - (1 - tp) * smoothstep(0.65, 1, s)),
        { up: (s) => ups[Math.min(ups.length - 1, Math.round(s * (ups.length - 1)))], flatten: L.flat });
      geos.push(tube.geo.clone());
    }
    const locksMesh = new THREE.Mesh(mergeGeometries(geos), this.hairMat);
    this.headG.add(locksMesh);
    // cowlick (dynamic: bounces)
    this.cowlick = [0, 1, 2].map((i) => {
      const tb = new SweepTube({ material: this.hairMat, segments: 10, radial: 8, capRings: 2 });
      this.headG.add(tb.mesh);
      return { tb, u: Math.PI - 0.3 + i * 0.26, v: 1.12 - i * 0.05, len: [1, 0.8, 0.62][i], tw: [-0.3, 0.12, 0.45][i] };
    });
  }
  _updateCowlick(bounce, t) {
    for (const C of this.cowlick) {
      const { p, n } = headSurf(C.u, C.v);
      const fwd = V(0, 0, 1), up = n.clone().lerp(V(0, 1, 0), 0.5).normalize();
      const side = V(Math.sin(C.tw), 0, 0);
      const b = bounce * C.len;
      const pts = [p.clone().addScaledVector(n, 0.01)];
      let q = p.clone().addScaledVector(n, 0.03);
      pts.push(q.clone());
      const dirs = [up.clone().addScaledVector(fwd, 0.15 + b * 0.5), up.clone().addScaledVector(fwd, 0.75 + b), up.clone().multiplyScalar(0.2).addScaledVector(fwd, 1).addScaledVector(V(0, -1, 0), 0.35 - b * 0.4)];
      const lens = [0.03, 0.024, 0.018].map((x) => x * C.len);
      for (let k = 0; k < 3; k++) { q = q.clone().addScaledVector(dirs[k].normalize().add(side).normalize(), lens[k]); pts.push(q.clone()); }
      C.tb.update(pts, (s) => 0.013 * C.len * (1 - 0.8 * smoothstep(0.4, 1, s)) + 0.002, { up: V(1, 0, 0), flatten: 0.45 });
    }
  }

  // ------------------------------------------------------------------ glasses (thin round frames, a touch too big)
  _buildGlasses() {
    this.glasses = new THREE.Group(); this.headG.add(this.glasses);
    this.glassesPivot = V();
    const lensTex = (() => {
      const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
      g.translate(64, 64); g.rotate(-0.7);
      const gr = g.createLinearGradient(-64, 0, 64, 0);
      gr.addColorStop(0.62, 'rgba(255,255,255,0)'); gr.addColorStop(0.7, 'rgba(255,255,255,0.6)'); gr.addColorStop(0.76, 'rgba(255,255,255,0)');
      gr.addColorStop(0.8, 'rgba(255,255,255,0)'); gr.addColorStop(0.83, 'rgba(255,255,255,0.35)'); gr.addColorStop(0.86, 'rgba(255,255,255,0)');
      g.fillStyle = gr; g.fillRect(-64, -64, 128, 128);
      const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
    })();
    this.lensMat = new THREE.MeshBasicMaterial({ map: lensTex, color: 0xffffff, transparent: true, opacity: 0.14, blending: THREE.AdditiveBlending, depthWrite: false });
    const RING = 0.047, TH = 0.0027;
    const parts = [];
    let cz = 0;
    this.lenses = [];
    for (const eye of this.face.eyes) {
      const ep = eye.group.position, s = eye.sx;
      const c = V(ep.x + s * 0.002, ep.y - 0.006, ep.z + EYE_R + 0.011);
      cz = c.z;
      const ring = new THREE.Mesh(new THREE.TorusGeometry(RING, TH, 8, 44), this.frameMat);
      ring.position.copy(c); ring.rotation.y = s * 0.16; parts.push(ring);
      const lens = new THREE.Mesh(new THREE.CircleGeometry(RING * 0.97, 32), this.lensMat);
      lens.position.copy(c); lens.rotation.y = s * 0.16; lens.renderOrder = 4; this.glasses.add(lens); this.lenses.push(lens);
      // temple arm: from the outer rim along the side of the face (just off the skin), then under the hair
      const o = c.clone().add(V(s * RING * Math.cos(0.16), 0.008, -RING * Math.sin(0.16)));
      const ap = [0.86, 1.1, 1.4].map((uu) => { const q = headSurf(s * uu, EYE_V + 0.06); return q.p.addScaledVector(q.n, 0.0045); });
      const arm = new SweepTube({ material: this.frameMat, segments: 10, radial: 6, capRings: 1 });
      arm.update([o, ...ap], TH * 0.9);
      parts.push(new THREE.Mesh(arm.geo.clone(), this.frameMat));
    }
    const eL = this.face.eyes[0].group.position;
    const br = new THREE.Mesh(new THREE.TorusGeometry(Math.max(0.006, eL.x - RING * 0.95), TH * 0.9, 6, 14, Math.PI), this.frameMat);
    br.position.set(0, eL.y - 0.002, cz + 0.002); parts.push(br);
    for (const p of parts) this.glasses.add(p);
    bake(this.glasses, parts);
    this.glassesPivot.set(0, eL.y - 0.01, cz);
  }

  // ------------------------------------------------------------------ hoodie body (skinned lathe grid)
  _buildTorso() {
    const ys = [0.734, 0.71, 0.7, 0.708, 0.722, 0.745, 0.775, 0.81, 0.85, 0.89, 0.93, 0.97, 1.01, 1.05, 1.09, 1.125, 1.155, 1.18, 1.2, 1.215, 1.229, 1.242, 1.254, 1.264, 1.272, 1.278];
    const inner = [0.86, 0.9];                                       // the first two rings fold back inside the hem
    const R = this.tR = 40, NR = this.tN = ys.length, C = R + 1;
    const n = NR * C;
    this.tRest = new Float32Array(n * 3); this.tW = new Float32Array(n); this.tPos = new Float32Array(n * 3);
    const uvs = new Float32Array(n * 2), nor = new Float32Array(n * 3);
    for (let i = 0; i < NR; i++) {
      const y = ys[i];
      let [rx, rz, ne, zo] = torsoProf(Math.max(0.7, y));
      if (i < 2) { rx *= inner[i]; rz *= inner[i]; }
      for (let j = 0; j < C; j++) {
        const th = -Math.PI + (j / R) * 2 * Math.PI;
        const x = rx * se(Math.sin(th), ne);
        let z = rz * se(Math.cos(th), ne) + zo * Math.max(0, Math.cos(th));
        if (i >= 2) z += 0.007 * pocketMask(th, y) * Math.max(0, Math.cos(th));
        const k = i * C + j;
        this.tRest.set([x, y, z], k * 3);
        this.tW[k] = smoothstep(0.86, 1.04, y);
        uvs[k * 2] = j / R; uvs[k * 2 + 1] = i < 2 ? 0.02 : clamp((y - 0.68) / 0.62);
      }
    }
    const idx = [];
    for (let i = 0; i < NR - 1; i++) for (let j = 0; j < R; j++) {
      const a = i * C + j, b = a + 1, c = a + C, d = c + 1;
      idx.push(a, b, c, b, d, c);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.tPos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('normal', new THREE.BufferAttribute(nor, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
    g.setIndex(idx);
    this.hoodieMat.map = this._hoodieTex();
    this.torso = new THREE.Mesh(g, this.hoodieMat); this.torso.castShadow = true; this.torso.frustumCulled = false;
    this.root.add(this.torso);
  }
  _hoodieTex() {
    const S = 512, c = document.createElement('canvas'); c.width = S; c.height = S;
    const g = c.getContext('2d');
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, S, S);
    const X = (th) => (th + Math.PI) / (2 * Math.PI) * S, Y = (y) => (1 - clamp((y - 0.68) / 0.62)) * S;
    // ribbed hem band
    g.fillStyle = '#e2e2e2'; g.fillRect(0, Y(0.745), S, Y(0.69) - Y(0.745));
    g.fillStyle = 'rgba(0,0,0,0.12)'; g.fillRect(0, Y(0.748), S, 3);
    // pocket face + outline + slanted openings
    const pts = [];
    for (let k = 0; k <= 20; k++) { const y = lerp(0.77, 0.915, k / 20); pts.push([lerp(0.66, 0.48, (y - 0.77) / 0.15), y]); }
    g.beginPath(); g.moveTo(X(-pts[0][0]), Y(0.77));
    for (const [h, y] of pts) g.lineTo(X(-h), Y(y));
    for (const [h, y] of pts.slice().reverse()) g.lineTo(X(h), Y(y));
    g.closePath();
    g.fillStyle = '#f1f1f1'; g.fill();
    g.strokeStyle = 'rgba(40,40,60,0.28)'; g.lineWidth = 3; g.stroke();
    g.strokeStyle = 'rgba(20,20,40,0.55)'; g.lineWidth = 5; g.lineCap = 'round';
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(X(s * 0.49), Y(0.905)); g.quadraticCurveTo(X(s * 0.6), Y(0.86), X(s * 0.645), Y(0.79)); g.stroke(); }
    // side seams + a soft centre-front shade
    g.strokeStyle = 'rgba(0,0,0,0.1)'; g.lineWidth = 3;
    for (const th of [-Math.PI / 2, Math.PI / 2]) { g.beginPath(); g.moveTo(X(th), 0); g.lineTo(X(th), Y(0.745)); g.stroke(); }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
    return t;
  }
  _updateTorso(ctx) {
    const { shrug, br, caps } = ctx;
    const R = this.tR, NR = this.tN, C = R + 1;
    const Mp = this.Mp, Mc = this.Mc, rest = this.tRest, P = this.tPos;
    const a = V(), b = V(), q = V(), ab = V(), aq = V();
    for (let k = 0; k < NR * C; k++) {
      let x = rest[k * 3], y = rest[k * 3 + 1], z = rest[k * 3 + 2];
      const w = this.tW[k];
      // shrug lifts the shoulder line; breath swells the chest
      const sh = smoothstep(1.12, 1.22, y) * (0.35 + 0.65 * smoothstep(0.04, 0.15, Math.abs(x)));
      const chest = bump(y, 0.98, 1.24);
      const yy = y + shrug * 0.042 * sh + br * 0.004 * chest;
      const zz = z * (1 + br * 0.03 * chest);
      a.set(x, yy - HIP_Y, zz).applyMatrix4(Mp);
      b.set(x * (1 + 0.012 * br * chest), yy - CHEST_Y0, zz).applyMatrix4(Mc);
      q.copy(a).lerp(b, w);
      // the hem drapes over the thighs (capsule push-out) and never sinks into the floor
      if (y < 0.93 && caps) {
        for (const cp of caps) {
          ab.copy(cp.b).sub(cp.a); aq.copy(q).sub(cp.a);
          const tt = clamp(aq.dot(ab) / ab.lengthSq());
          const c0 = cp.a.clone().addScaledVector(ab, tt);
          const d = q.distanceTo(c0), rad = lerp(cp.ra, cp.rb, tt);
          if (d < rad) {
            const dir = q.clone().sub(c0); if (dir.lengthSq() < 1e-10) dir.set(0, 1, 0);
            dir.normalize(); dir.y = Math.max(dir.y, 0.25); dir.normalize();
            q.copy(c0).addScaledVector(dir, rad);
          }
        }
      }
      if (q.y < 0.012) q.y = 0.012;
      P[k * 3] = q.x; P[k * 3 + 1] = q.y; P[k * 3 + 2] = q.z;
    }
    // seam-safe grid normals
    const N = this.torso.geometry.attributes.normal.array;
    const at = (i, j) => (i * C + ((j + R) % R)) * 3;
    const du = V(), dv = V(), nn = V();
    for (let i = 0; i < NR; i++) for (let j = 0; j < C; j++) {
      const j0 = j % R;
      const p1 = at(i, j0 + 1), p0 = at(i, j0 - 1);
      du.set(P[p1] - P[p0], P[p1 + 1] - P[p0 + 1], P[p1 + 2] - P[p0 + 2]);
      const i1 = Math.min(NR - 1, i + 1), i0 = Math.max(0, i - 1);
      const q1 = at(i1, j0), q0 = at(i0, j0);
      dv.set(P[q1] - P[q0], P[q1 + 1] - P[q0 + 1], P[q1 + 2] - P[q0 + 2]);
      nn.crossVectors(du, dv);
      if (i < 2) nn.negate();
      nn.normalize();
      const o = (i * C + j) * 3; N[o] = nn.x; N[o + 1] = nn.y; N[o + 2] = nn.z;
    }
    const geo = this.torso.geometry;
    geo.attributes.position.needsUpdate = true; geo.attributes.normal.needsUpdate = true;
  }

  // ------------------------------------------------------------------ hood (down) + drawstrings
  _buildHood() {
    this.hoodG = new THREE.Group(); this.chestG.add(this.hoodG);
    const roll = new SweepTube({ material: this.sleeveMat, segments: 30, radial: 12, capRings: 3 });
    const yb = 1.272 - CHEST_Y0;   // neck-hole height (chest-local)
    const pts = [[0.034, yb - 0.012, 0.088], [0.085, yb + 0.004, 0.05], [0.112, yb + 0.018, -0.02], [0.088, yb + 0.034, -0.088], [0, yb + 0.04, -0.118],
      [-0.088, yb + 0.034, -0.088], [-0.112, yb + 0.018, -0.02], [-0.085, yb + 0.004, 0.05], [-0.034, yb - 0.012, 0.088]].map((p) => V(...p));
    roll.update(pts, (s) => lerp(0.016, 0.034, Math.sin(Math.PI * s) ** 1.3), { flatten: 0.25, up: V(0, 1, 0) });
    const rm = new THREE.Mesh(roll.geo.clone(), this.sleeveMat); rm.castShadow = true;
    // hood bag lying on the upper back (cupped, thicker at the rim)
    const bg = new THREE.SphereGeometry(1, 28, 18);
    const BP = bg.attributes.position;
    for (let i = 0; i < BP.count; i++) {
      let x = BP.getX(i), y = BP.getY(i), z = BP.getZ(i);
      const pinch = 1 - 0.35 * smoothstep(0.1, -1, y);              // tapers to a soft point at the bottom
      x *= 0.118 * pinch; z *= 0.042; y = y * 0.115 + (z > 0 ? 0 : 0);
      BP.setXYZ(i, x, y, z);
    }
    bg.computeVertexNormals();
    const bag = new THREE.Mesh(bg, this.sleeveMat);
    bag.position.set(0, yb - 0.075, -0.142); bag.rotation.x = 0.22; bag.castShadow = true;
    this.hoodG.add(rm, bag);
    bake(this.hoodG, [rm, bag]);
    // drawstrings (dynamic) + metal aglets
    this.strings = [1, -1].map((s) => {
      const tb = new SweepTube({ material: this.stringMat, segments: 8, radial: 6, capRings: 1 });
      this.root.add(tb.mesh);
      const ag = new THREE.Mesh(new THREE.CylinderGeometry(0.0052, 0.0048, 0.018, 8), this.agletMat);
      this.root.add(ag);
      return { s, tb, ag };
    });
  }
  _updateStrings(t, ctx) {
    const { amt, ph, ST, br, shrug } = ctx;
    const Mc = this.Mc;
    const inv = new THREE.Matrix4().copy(Mc).invert();
    const down = V(0, -1, 0).transformDirection(inv);   // gravity in chest space
    const yb = 1.272 - CHEST_Y0;
    for (const S of this.strings) {
      const s = S.s;
      const sw = amt * (0.35 + ST.run * 0.6) * Math.sin(2 * Math.PI * (ph + (s > 0 ? 0 : 0.5)) + 0.6) + 0.15 * fbm1(t * 0.8, 40 + s);
      const pts = [];
      let p = V(s * 0.032, yb - 0.006 + shrug * 0.03, 0.098);
      pts.push(p.clone());
      const L = [0.05, 0.055, 0.055, 0.05];
      for (let k = 0; k < L.length; k++) {
        const d = down.clone().add(V(s * 0.06 + sw * 0.25 * (k + 1) / 4, 0, 0.12 + Math.abs(sw) * 0.15)).normalize();
        p = p.clone().addScaledVector(d, L[k]);
        // lie on the hoodie front
        const [, rz, , zo] = torsoProf(p.y + CHEST_Y0);
        const zmin = rz + zo + 0.007 + 0.006 * br;
        if (p.z < zmin) p.z = zmin;
        pts.push(p.clone());
      }
      const wpts = pts.map((x) => x.applyMatrix4(Mc));
      S.tb.update(wpts, 0.0038);
      const e = wpts[wpts.length - 1], d = e.clone().sub(wpts[wpts.length - 2]).normalize();
      S.ag.position.copy(e).addScaledVector(d, 0.006);
      orientYZ(S.ag, d.clone().negate(), V(0, 0, 1));
    }
  }

  // ------------------------------------------------------------------ arms: oversized bunched sleeves + hands
  _buildArms() {
    this.arms = {};
    for (const side of ['L', 'R']) {
      const sleeve = new SweepTube({ material: this.sleeveMat, segments: 26, radial: 14, capRings: 2, castShadow: true });
      const hand = new UHand({ size: HAND_SIZE, side, material: this.bodySkin });
      this.root.add(sleeve.mesh, hand.root);
      this.arms[side] = { sleeve, hand, elbow: V(), wrist: V(), shoulder: V() };
    }
  }
  _presetToRoot(d, s, out) {
    const sp = d.space || 'chest';
    const M = sp === 'head' ? this.Mh : sp === 'pelvis' || sp === 'ground' ? this.Mp : this.Mc;
    if (sp === 'ground') { out.t.set(s * d.t[0], 0, d.t[2]).applyMatrix4(this.MpYaw).add(this.pelvisG.position); out.t.y = d.t[1]; }
    else out.t.set(s * d.t[0], d.t[1], d.t[2]).applyMatrix4(M);
    const rot = sp === 'ground' ? this.MpYaw : M;
    out.pole.set(s * d.pole[0], d.pole[1], d.pole[2]).transformDirection(rot);
    out.palm.set(s * d.palm[0], d.palm[1], d.palm[2]).transformDirection(rot);
    out.fing.set(s * d.fing[0], d.fing[1], d.fing[2]).transformDirection(rot);
    return out;
  }
  _armTarget(side, A, ctx) {
    const s = side === 'L' ? 1 : -1, t = ctx.t;
    const isPhone = this.phoneSide === side;
    let list = A.preset ?? (isPhone ? 'hold' : 'rest');
    if (typeof list === 'string') list = [[list, 1]];
    const acc = { t: V(), pole: V(), palm: V(), fing: V(), hand: {}, grip: null }, one = { t: V(), pole: V(), palm: V(), fing: V() };
    for (const k of HAND_KEYS) acc.hand[k] = 0;
    let wsum = 0, restW = 0, gripW = {}, anims = [];
    const add = (d, w, name) => {
      this._presetToRoot(d, s, one);
      if (d.anim === 'knee' && ctx.knee[side]) one.t.copy(ctx.knee[side]).add(V(s * 0.02, 0.07, 0.03).applyQuaternion(this.rootQ));
      acc.t.addScaledVector(one.t, w); acc.pole.addScaledVector(one.pole, w); acc.palm.addScaledVector(one.palm, w); acc.fing.addScaledVector(one.fing, w);
      for (const k of HAND_KEYS) acc.hand[k] += (d.hand[k] ?? HAND_DEF[k]) * w;
      if (name === 'rest' || name === 'hold') restW += w;
      if (d.grip) gripW[d.grip] = (gripW[d.grip] || 0) + w;
      if (d.anim) anims.push([d.anim, w]);
      wsum += w;
    };
    for (const [name, w0] of list) { const w = Math.max(0, w0); if (w > 0) add(ARM[name] || ARM.rest, w, name); }
    if (wsum <= 0) { add(ARM.rest, 1, 'rest'); }
    acc.t.multiplyScalar(1 / wsum); for (const k of HAND_KEYS) acc.hand[k] /= wsum; restW /= wsum;
    // phone up to look at it (phone hand only)
    const up = isPhone ? clamp(ctx.phoneUp) : 0;
    if (up > 0) {
      const L = this._presetToRoot(ARM.look, s, { t: V(), pole: V(), palm: V(), fing: V() });
      acc.t.lerp(L.t, up); acc.pole.normalize().lerp(L.pole, up); acc.palm.normalize().lerp(L.palm, up); acc.fing.normalize().lerp(L.fing, up);
      for (const k of HAND_KEYS) acc.hand[k] = lerp(acc.hand[k], ARM.look.hand[k] ?? HAND_DEF[k], up);
      gripW.flat = (gripW.flat || 0) + up * 2; restW *= 1 - up;
    }
    // world overrides
    if (A.target) acc.t.copy(toV(A.target)).applyMatrix4(this.rootInv);
    if (A.pole) acc.pole.copy(toV(A.pole)).applyQuaternion(this.rootQInv);
    if (A.palm) acc.palm.copy(toV(A.palm)).applyQuaternion(this.rootQInv);
    if (A.fingers) acc.fing.copy(toV(A.fingers)).applyQuaternion(this.rootQInv);
    if (A.offset) acc.t.add(toV(A.offset).applyQuaternion(this.rootQInv));
    const reach = clamp(A.reach ?? 1);
    if (reach < 1) {
      const rp = isPhone ? ARM.hold : ARM.rest;
      const r = this._presetToRoot(rp, s, { t: V(), pole: V(), palm: V(), fing: V() });
      acc.t.lerp(r.t, 1 - reach); acc.pole.normalize().lerp(r.pole, 1 - reach); acc.palm.normalize().lerp(r.palm, 1 - reach); acc.fing.normalize().lerp(r.fing, 1 - reach);
      for (const k of HAND_KEYS) acc.hand[k] = lerp(rp.hand[k] ?? HAND_DEF[k], acc.hand[k], reach);
      restW = lerp(1, restW, reach);
    }
    // ---- locomotion: walk swing / run pump (+ panicked flail) / stomp fists
    const amt = ctx.amt;
    if (amt > 0 && restW > 0) {
      const S = ctx.ST, w = amt * restW, ph = ctx.ph + (s > 0 ? 0.5 : 0);      // opposite to the same-side leg
      const fwd = V(0, 0, 1).transformDirection(this.Mp);
      if (S.run) {
        const a = Math.sin(2 * Math.PI * ph);
        const R3 = new THREE.Matrix4().extractRotation(this.Mc);
        const sh = V(s * SH[0], SH[1], SH[2]).applyMatrix4(this.Mc);
        const fl = clamp(A.flail ?? ctx.flail);
        const f1 = noise1(t * 2.2, 81 + s), f2 = noise1(t * 2.6, 83 + s);
        const c = Math.cos(2 * Math.PI * ph + s), d = Math.sin(2 * Math.PI * ph + 0.7 * s);
        const off = V(s * (0.035 + 0.04 * fl * (0.5 + 0.5 * f1) + 0.035 * fl * c), -0.21 + 0.17 * a + 0.07 * fl * f2 + 0.05 * fl * d, 0.07 + 0.2 * a);
        const P = sh.clone().add(off.applyMatrix4(R3));
        acc.t.lerp(P, w);
        acc.pole.lerp(V(s * 0.5, -0.6, -1).transformDirection(this.Mc), w);
        acc.fing.lerp(V(-s * 0.4, 0.5 + 0.4 * a, 0.7).transformDirection(this.Mc), w);
        acc.palm.lerp(V(-s * 0.9, 0.1, 0.2).transformDirection(this.Mc), w);
        acc.hand.curl = lerp(acc.hand.curl, 0.95 - 0.5 * fl * Math.max(0, f1), w); acc.hand.spread = lerp(acc.hand.spread, 0.2 * fl, w); acc.hand.thumb = lerp(acc.hand.thumb, 0.15, w);
        gripW.fist = (gripW.fist || 0) + 3 * w;
      } else {
        const sw = Math.sin(2 * Math.PI * ph);
        if (isPhone && S.stomp) {
          const r = this._presetToRoot(ARM.rest, s, { t: V(), pole: V(), palm: V(), fing: V() });
          acc.t.lerp(r.t, w); acc.pole.lerp(r.pole, w); acc.palm.lerp(r.palm, w); acc.fing.lerp(r.fing, w);
        }
        acc.t.addScaledVector(fwd, sw * S.arm * w);
        acc.t.y += 0.018 * Math.abs(sw) * w;
        if (S.stomp) {             // stiff fists, elbows locked-ish, a bit out from the body
          acc.t.x += s * 0.035 * w; acc.t.y += 0.03 * w; acc.t.addScaledVector(fwd, 0.03 * w);
          acc.hand.curl = lerp(acc.hand.curl, 1, w); acc.hand.thumb = lerp(acc.hand.thumb, 0.1, w); acc.hand.cup = lerp(acc.hand.cup, 0, w);
          gripW.fist = (gripW.fist || 0) + 3 * w;
        }
      }
    }
    // ---- falling: arms fling up (the phone hand saves the phone, priorities)
    if (ctx.fall > 0) {
      const f = ctx.fall;
      const sh = V(s * SH[0], SH[1], SH[2]).applyMatrix4(this.Mc);
      const ang = 2 * Math.PI * (t * 1.3) * (isPhone ? 0 : 1) + s;
      const P = sh.clone().add(V(s * (0.22 + 0.06 * Math.cos(ang)), 0.32 + 0.08 * Math.sin(ang) + (isPhone ? 0.1 : 0), 0.12).applyMatrix4(new THREE.Matrix4().extractRotation(this.Mc)));
      acc.t.lerp(P, f);
      acc.pole.lerp(V(s, -0.3, -0.6).transformDirection(this.Mc), f);
      acc.fing.lerp(V(s * 0.3, 1, 0.1).transformDirection(this.Mc), f);
      acc.palm.lerp(V(0, 0.1, 1).transformDirection(this.Mc), f);
      if (!isPhone) { acc.hand.spread = lerp(acc.hand.spread, 0.9, f); acc.hand.splay = lerp(acc.hand.splay, 0.8, f); acc.hand.curl = lerp(acc.hand.curl, 0, f); }
    }
    if (A.hand) for (const k of HAND_KEYS) if (A.hand[k] != null) acc.hand[k] = A.hand[k];
    // gestures: flap (a feeble outward wave of the raised hand), tremble
    if (A.flap) acc.fing.add(V(s * 0.9 * A.flap, -0.3 * A.flap, 0).transformDirection(this.Mc));
    const tr = (A.tremble ?? 0) + ctx.tremble * 0.5;
    if (tr > 0) {
      acc.t.add(V(noise1(t * 11, 71 + s), noise1(t * 12.3, 73 + s), noise1(t * 10.1, 75 + s)).multiplyScalar(0.007 * tr));
      acc.fing.add(V(noise1(t * 13, 77 + s), 0, noise1(t * 12, 79 + s)).multiplyScalar(0.12 * tr));
    }
    if (A.wiggle) acc.t.add(V(noise1(t * 2.1, 61 + s), noise1(t * 2.3, 63 + s), noise1(t * 1.9, 65 + s)).multiplyScalar(0.012 * A.wiggle));
    let grip = A.grip || null;
    if (!grip) { let best = 0; for (const [g, w] of Object.entries(gripW)) if (w > best) { best = w; grip = g; } }
    acc.grip = grip || (acc.hand.curl > 0.6 ? 'fist' : 'flat');
    return acc;
  }
  _updateArm(side, A, ctx) {
    const s = side === 'L' ? 1 : -1, arm = this.arms[side];
    const acc = this._armTarget(side, A || {}, ctx);
    const sh = arm.shoulder.set(s * SH[0], SH[1] + ctx.shrug * 0.045 + 0.004 * ctx.br, SH[2] + ctx.hunch * 0.03).applyMatrix4(this.Mc);
    const pole = acc.pole.lengthSq() > 1e-8 ? acc.pole.normalize() : V(s, 0, -1);
    const { mid: elbow, end: wrist } = solveIK2(sh, acc.t, UPPER, FORE, pole);
    arm.elbow.copy(elbow); arm.wrist.copy(wrist);
    const fore = wrist.clone().sub(elbow).normalize();
    let fd = acc.fing.lengthSq() > 1e-8 ? acc.fing.clone().normalize() : fore.clone();
    const ang = fore.angleTo(fd);
    if (ang > MAXWRIST) { const qq = new THREE.Quaternion().setFromUnitVectors(fore, fd); fd = fore.clone().applyQuaternion(new THREE.Quaternion().slerp(qq, MAXWRIST / ang)); }
    let palm = acc.palm.lengthSq() > 1e-8 ? acc.palm.clone().normalize() : V(0, -1, 0);
    if (Math.abs(palm.dot(fd)) > 0.97) palm = V(-s, 0, 0);
    arm.hand.root.position.copy(wrist);
    arm.hand.aim(fd, palm);
    // phone grip / thumb tap
    const hp = { ...acc.hand };
    const isPhone = this.phoneSide === side && this.phoneVis;
    if (isPhone) {
      const gm = acc.grip;
      if (gm === 'flat') {
        // phone lies on the palm + fingers (fingers stay behind the slab), pinky tucks under the bottom edge
        hp.curl = Math.min(hp.curl, 0.06); hp.cup = Math.min(hp.cup, 0.04); hp.spread = Math.min(hp.spread, 0.06); hp.point = 0; hp.splay = 0.06;
        hp.perFinger = [0.02, 0.03, 0.05, 0.12];
        const tap = clamp(ctx.tap), tw = clamp(ctx.thumbOn + tap);
        if (tw > 0) {
          const scr = this._phoneLocal('flat');
          const ta = ctx.thumbAt || THUMB_AT[ctx.screen] || THUMB_AT.feed;
          const tu = ta[0] + 0.012 * noise1(ctx.t * 0.9, 7 + s), tv = ta[1] + 0.02 * noise1(ctx.t * 1.3, 5 + s);
          // screen (u, v) -> phone local (x right, y up) -> hand local (phone is turned 180 deg about Y)
          const px = (tu - 0.5) * (PH_W - 0.007), py = (0.5 - tv) * (PH_H - 0.008);
          hp.thumbTo = V(-px + arm.hand.ts * 0.006, scr.pos.y + py, scr.z - 0.0095 - 0.014 * (1 - tap));
          hp.thumbW = tw;
        }
      } else if (gm === 'fist') { hp.curl = Math.max(hp.curl, 0.88); hp.grip = 0.2; hp.thumb = Math.min(hp.thumb, 0.25); }
      else if (gm === 'tuck') { hp.curl = Math.max(hp.curl, 0.6); }
      this.phoneGrip = gm;
    }
    arm.hand.pose(hp);
    // oversized sleeve: drop shoulder, bunched forearm folds, ribbed cuff over the wrist
    const shIn = V(s * (SH[0] - 0.05), SH[1] + ctx.shrug * 0.045 - 0.01, SH[2]).applyMatrix4(this.Mc);
    const m1 = sh.clone().lerp(elbow, 0.5);
    const cuffEnd = wrist.clone().addScaledVector(fore, 0.012);
    const m2 = elbow.clone().lerp(wrist, 0.5);
    const sag = 0.012 * (1 - Math.abs(fore.y));
    m2.y -= sag; m1.y -= 0.006;
    const bunch = 1;
    arm.sleeve.update([shIn, sh, m1, elbow, m2, wrist.clone().addScaledVector(fore, -0.03), cuffEnd], (u) => {
      let r = u < 0.18 ? lerp(0.07, 0.066, u / 0.18) : u < 0.5 ? lerp(0.066, 0.06, (u - 0.18) / 0.32) : lerp(0.06, 0.057, (u - 0.5) / 0.4);
      if (u > 0.52 && u < 0.9) r += 0.0075 * bunch * Math.abs(Math.sin((u - 0.52) / 0.38 * Math.PI * 3.5)) - 0.003;
      if (u >= 0.9) r = lerp(0.054, 0.043, smoothstep(0.9, 0.95, u));
      return r;
    });
  }

  // ------------------------------------------------------------------ phone
  _buildPhone() {
    this.phone = new THREE.Group();
    const body = new THREE.Mesh(new RoundedBoxGeometry(PH_W, PH_H, PH_D, 3, 0.0075), this.caseMat);
    const cam = new THREE.Mesh(new RoundedBoxGeometry(0.024, 0.024, 0.003, 2, 0.006), this.bumpMat);
    cam.position.set(-0.016, 0.05, -PH_D / 2 - 0.001);
    this.phone.add(body, cam);
    bake(this.phone, [body, cam]);
    this.screenMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.screen = new THREE.Mesh(new THREE.PlaneGeometry(PH_W - 0.007, PH_H - 0.008), this.screenMat);
    this.screen.position.z = PH_D / 2 + 0.0003;
    this.phone.add(this.screen);
    this.hdrMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const hc = document.createElement('canvas'); hc.width = SCR.W; hc.height = 70; header(hc.getContext('2d'), SCR.W);
    const ht = new THREE.CanvasTexture(hc); ht.colorSpace = THREE.SRGBColorSpace; this.hdrMat.map = ht;
    const hh = (PH_H - 0.008) * 70 / SCR.H;
    this.hdr = new THREE.Mesh(new THREE.PlaneGeometry(PH_W - 0.007, hh), this.hdrMat);
    this.hdr.position.set(0, (PH_H - 0.008) / 2 - hh / 2, PH_D / 2 + 0.0006);
    this.phone.add(this.hdr);
    this.texCache = {};
    const ft = new THREE.CanvasTexture(feedCanvas()); ft.colorSpace = THREE.SRGBColorSpace; ft.wrapT = THREE.RepeatWrapping; ft.anisotropy = 4;
    ft.repeat.set(1, 0.5); this.feedTex = ft;
    this.screenKey = '';
    this.anchorPhone = new THREE.Object3D(); this.phone.add(this.anchorPhone);
    this.anchorScreen = new THREE.Object3D(); this.anchorScreen.position.z = PH_D / 2 + 0.001; this.phone.add(this.anchorScreen);
  }
  /** phone centre/orientation in hand-local space for a grip mode (screen faces the palm-normal side, -Z) */
  _phoneLocal(mode) {
    if (mode === 'fist') return { pos: V(0, 0.048, -0.021), rot: new THREE.Euler(0, Math.PI, Math.PI / 2, 'XYZ'), z: -0.026 };
    if (mode === 'tuck') return { pos: V(0, 0.048, -0.021), rot: new THREE.Euler(0, Math.PI, Math.PI / 2 + 0.3, 'XYZ'), z: -0.026 };
    const z = -(this.arms ? this.arms.L.hand.pt * 0.5 : 0.015) - PH_D / 2 - 0.0035;
    return { pos: V(0, 0.07, z), rot: new THREE.Euler(0, Math.PI, 0), z: z - PH_D / 2 };
  }
  _updatePhone(t, E) {
    const side = this.phoneSide, hand = this.arms[side].hand;
    if (this.phone.parent !== hand.root) hand.root.add(this.phone);
    this.phone.visible = this.phoneVis;
    const L = this._phoneLocal(this.phoneGrip || 'flat');
    this.phone.position.copy(L.pos);
    this.phone.rotation.copy(L.rot);
    if (this.phoneGrip === 'flat') this.phone.position.x += hand.ts * 0.006;
    // screen content
    const mode = E.screen || 'feed', name = E.screenName || 'Jesus';
    const lum = this.phoneVis ? clamp(E.phone ?? 0.85) : 0;
    const key = mode + '|' + name;
    if (key !== this.screenKey) {
      this.screenKey = key;
      if (mode === 'feed') { this.screenMat.map = this.feedTex; this.hdr.visible = true; }
      else {
        if (!this.texCache[key]) { const tx = new THREE.CanvasTexture(screenCanvas(mode, name)); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 4; this.texCache[key] = tx; }
        this.screenMat.map = this.texCache[key]; this.hdr.visible = false;
      }
      this.screenMat.needsUpdate = true;
    }
    if (mode === 'feed') this.feedTex.offset.y = -(E.scroll ?? 0) * 0.5 % 1;
    const k = mode === 'off' ? 0 : lum;
    const bright = lerp(0.025, 1.08, k);
    this.screenMat.color.setRGB(bright * 0.95, bright * 0.98, bright);
    this.hdrMat.color.copy(this.screenMat.color);
    if (mode === 'off') this.screenMat.color.setRGB(0.02, 0.022, 0.03);
    // glow uniforms (world; converted to view space at draw time)
    this.phone.updateWorldMatrix(true, false);
    this.phW.set(0, 0, PH_D / 2 + 0.01).applyMatrix4(this.phone.matrixWorld);
    this.phN.set(0, 0, 1).transformDirection(this.phone.matrixWorld);
    const g = k * (SCREEN_LUM[mode] ?? 0.8) * (E.glow ?? 1);
    this.PU.col.value.setRGB(0.75 * g, 1.08 * g, 1.6 * g);
    // reflections: eyes (cornea glint where the phone is) and glasses
    const cam = CTX.camera;
    for (let i = 0; i < 2; i++) {
      const eye = this.face.eyes[i], rm = this.eyeRefl[i];
      rm.visible = false;
      if (!cam || g < 0.02) continue;
      eye.inner.updateWorldMatrix(true, false);
      const inv = new THREE.Matrix4().copy(eye.inner.matrixWorld).invert();
      const Lp = this.phW.clone().applyMatrix4(inv).normalize(), Vc = cam.position.clone().applyMatrix4(inv).normalize();
      const n = Lp.clone().add(Vc).normalize();
      const elev = Math.asin(clamp(n.y, -1, 1));
      const upE = -eye.up.rotation.x, loE = -eye.lo.rotation.x;
      if (n.z < 0.35 || elev > upE - 0.14 || elev < loE + 0.14) continue;
      rm.visible = true;
      rm.position.copy(n).multiplyScalar(eye.r * 1.015);
      rm.lookAt(cam.position);
      rm.material.opacity = clamp(g * 0.9) * 0.85;
    }
    this.lensMat.opacity = 0.06 + 0.14 * g;
  }

  // ------------------------------------------------------------------ legs: joggers + chunky sneakers
  _buildLegs() {
    this.feet = {};
    for (const side of ['L', 'R']) {
      const s = side === 'L' ? 1 : -1;
      const g = new THREE.Group(); g.rotation.order = 'YXZ';
      const A = -ANKLE_Y;                                           // ground level in foot space
      const X = (x) => x * s;
      const outline = (o) => {
        const sh = new THREE.Shape();
        sh.moveTo(0, -0.088 - o);
        sh.quadraticCurveTo(X(0.047 + o), -0.088 - o, X(0.048 + o), -0.03);
        sh.quadraticCurveTo(X(0.05 + o), 0.08, X(0.052 + o), 0.13);
        sh.quadraticCurveTo(X(0.05 + o), 0.205 + o, X(0.0), 0.212 + o);
        sh.quadraticCurveTo(X(-0.05 - o), 0.205 + o, X(-0.05 - o), 0.12);
        sh.quadraticCurveTo(X(-0.043 - o), 0.04, X(-0.045 - o), -0.03);
        sh.quadraticCurveTo(X(-0.046 - o), -0.088 - o, 0, -0.088 - o);
        return sh;
      };
      const ext = (o, depth, y, mat) => {
        const eg = new THREE.ExtrudeGeometry(outline(o), { depth, bevelEnabled: true, bevelThickness: 0.006, bevelSize: 0.006, bevelSegments: 2, curveSegments: 8 });
        eg.rotateX(Math.PI / 2); eg.translate(0, y + depth, 0);
        return new THREE.Mesh(eg, mat);
      };
      const outsole = ext(0.001, 0.006, A + 0.006, this.outsoleMat);
      const mid = ext(0.0, 0.02, A + 0.016, this.soleMat);
      // upper: a deformed ellipsoid (toe box lower than the heel)
      const ug = new THREE.SphereGeometry(1, 28, 18);
      const UP = ug.attributes.position;
      for (let i = 0; i < UP.count; i++) {
        let x = UP.getX(i), y = UP.getY(i), z = UP.getZ(i);
        const zz = 0.062 + z * 0.142;
        const h = lerp(1.0, 0.46, smoothstep(-0.04, 0.19, zz));
        let yy = y > 0 ? y * 0.07 * h : y * 0.03;
        yy += A + 0.052;
        const wdt = lerp(0.044, 0.05, smoothstep(-0.05, 0.12, zz)) * (1 - 0.12 * smoothstep(0.16, 0.21, zz));
        UP.setXYZ(i, x * wdt + X(0.002) * smoothstep(0.1, 0.2, zz), yy, zz);
      }
      ug.computeVertexNormals();
      const upper = new THREE.Mesh(ug, this.shoeMat);
      const collar = new THREE.Mesh(new THREE.TorusGeometry(0.039, 0.0135, 8, 22), this.shoeMat);
      collar.position.set(0, -0.004, -0.032); collar.rotation.set(Math.PI / 2 - 0.3, 0, 0); collar.scale.set(1.05, 1.15, 1);
      const tongue = new THREE.Mesh(new RoundedBoxGeometry(0.046, 0.052, 0.014, 2, 0.006), this.shoeMat);
      tongue.position.set(0, -0.004, 0.022); tongue.rotation.x = -0.55;
      const laces = [0.035, 0.058, 0.08].map((z, i) => {
        const m = new THREE.Mesh(new THREE.CapsuleGeometry(0.0042, 0.04, 3, 6), this.laceMat);
        m.position.set(0, A + 0.052 + 0.07 * lerp(1.0, 0.46, smoothstep(-0.04, 0.19, z)) - 0.001 - i * 0.002, z); m.rotation.set(0.35, 0, Math.PI / 2);
        return m;
      });
      const tab = new THREE.Mesh(new RoundedBoxGeometry(0.03, 0.04, 0.012, 2, 0.005), this.tabMat);
      tab.position.set(0, -0.008, -0.086); tab.rotation.x = 0.25;
      g.add(outsole, mid, upper, collar, tongue, ...laces, tab);
      bake(g, [...g.children]);
      this.root.add(g);
      const leg = new SweepTube({ material: this.jogMat, segments: 22, radial: 12, capRings: 2, castShadow: true });
      this.root.add(leg.mesh);
      this.feet[side] = { g, leg, knee: V(), ankle: V(), hip: V() };
    }
    // seat (jogger hips under the hoodie)
    const seat = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 18), this.jogMat);
    seat.scale.set(0.158, 0.12, 0.125); seat.position.set(0, -0.035, -0.008); seat.castShadow = true;
    this.pelvisG.add(seat);
    this.shadow = contactShadow(0.85, 0.55, 0.36); this.root.add(this.shadow);
  }

  // ------------------------------------------------------------------ tears (3D drops sliding down the cheeks)
  _buildTears() {
    this.drops = [];
    const geo = new THREE.SphereGeometry(1, 12, 10);
    for (let i = 0; i < 4; i++) {
      const m = new THREE.Mesh(geo, this.tearMat); m.visible = false; m.renderOrder = 3;
      this.headG.add(m); this.drops.push(m);
    }
    this.dropEv = [schedule(this.seed * 41 + 1, -4, 3000, 0.7, 1.6), schedule(this.seed * 43 + 2, -4, 3000, 0.7, 1.6)];
  }
  _updateTears(t, tears, run) {
    for (const m of this.drops) m.visible = false;
    if (tears <= 0.02) return;
    let used = 0;
    for (let e = 0; e < 2; e++) {
      const s = e === 0 ? 1 : -1, ev = this.dropEv[e];
      const life = run > 0.3 ? 0.55 : 1.5;
      let i = this._bsearch(ev, t);
      for (let k = 0; k < 3 && i >= 0 && used < 4; k++, i--) {
        const age = t - ev[i];
        if (age < 0 || age > life || hash1(i * 7 + e) > tears) continue;
        const u = age / life;
        const m = this.drops[used++];
        let uu = s * (EYE_U + 0.06 + 0.05 * u), vv = EYE_V - 0.2 - 0.38 * u * u;
        const { p, n } = headSurf(uu, vv);
        p.addScaledVector(n, 0.003);
        if (run > 0.3) { p.addScaledVector(V(s * 0.6, 0.2, -1).normalize(), 0.09 * u * u * run); }   // flung back while running
        m.position.copy(p);
        const sc = 0.0042 * (u < 0.15 ? smooth(u / 0.15) : 1 - 0.5 * u);
        m.scale.set(sc, sc * 1.35, sc * 0.8);
        m.visible = true;
      }
    }
  }

  // ------------------------------------------------------------------ anchors
  _buildAnchors() {
    const H = this.headG, C = this.chestG;
    this.addAnchor('head', H, [0, 0, 0]);
    this.addAnchor('top', H, [0, 0.175, -0.01]);
    this.addAnchor('eyes', H, [0, EYE_V * HR[1], 0.142]);
    this.addAnchor('mouth', H, [0, -0.068, 0.135]);
    this.addAnchor('earL', H, [0.15, -0.02, -0.01]);
    this.addAnchor('earR', H, [-0.15, -0.02, -0.01]);
    this.addAnchor('chest', C, [0, 0.13, 0.15]);
    this.addAnchor('back', C, [0, 0.15, -0.15]);
    this.addAnchor('shoulderL', C, [0.165, 0.29, -0.015]);
    this.addAnchor('shoulderR', C, [-0.165, 0.29, -0.015]);
    this.addAnchor('handL', this.arms.L.hand.root, [0, HAND_SIZE * 0.42, -0.012]);
    this.addAnchor('handR', this.arms.R.hand.root, [0, HAND_SIZE * 0.42, -0.012]);
    this.addAnchor('hip', this.pelvisG, [0, 0, 0]);
    this._anch.phone = this.anchorPhone;
    this._anch.phoneScreen = this.anchorScreen;
    for (const n of ['footL', 'footR', 'kneeL', 'kneeR', 'elbowL', 'elbowR']) this.addAnchor(n, this.root, [0, 0, 0]);
  }
  _bsearch(arr, t) { let lo = 0, hi = arr.length - 1, r = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (arr[m] <= t) { r = m; lo = m + 1; } else hi = m - 1; } return r; }

  // ===================================================================================== update
  update(t, pose = {}) {
    const P = pose || {}, B = P.body || {}, Wk = P.walk || {}, Hd = P.head || {}, E = P.extra || {};
    this.place(P.pos || [0, 0, 0], P.yaw || 0);
    this.root.updateWorldMatrix(true, false);
    this.rootInv.copy(this.root.matrixWorld).invert();
    this.root.getWorldQuaternion(this.rootQ); this.rootQInv.copy(this.rootQ).invert();
    this.phoneSide = E.phoneHand === 'R' ? 'R' : 'L';
    this.phoneVis = E.phoneVisible !== false;
    const style = WALK[Wk.style] ? Wk.style : 'walk', ST = WALK[style];
    const amt = clamp(Wk.amount ?? 0), ph = Wk.phase ?? t * ST.rate;
    const sit = clamp(B.sit ?? 0), crouch = clamp(B.crouch ?? 0), kneel = clamp(B.kneel ?? 0);
    const sitPath = B.sitPath || 'fall';
    const scoot = clamp(B.scoot ?? 0) * smoothstep(0.85, 1, sit);
    const flinch = clamp(B.flinch ?? 0), tremble = clamp(B.tremble ?? 0), jut = clamp(B.jut ?? 0, -0.5, 1);
    const shrug = clamp((B.shrug ?? 0) + flinch * 0.7 + ST.stomp * amt * 0.35);
    const hunch = clamp((B.hunch ?? 0.18) + ST.stomp * amt * 0.45 + flinch * 0.3), slump = clamp(B.slump ?? 0), recoil = (B.recoil ?? 0) + flinch * 0.25;
    const pant = clamp(B.pant ?? 0);
    const br = (this.breath(t, lerp(B.breathRate ?? 0.25, 1.6, pant)) - 0.5) * (B.breathe ?? 1) * (1 + pant * 0.6);
    const idle = (B.sway ?? 1) * (1 - amt) * (1 - 0.7 * sit);
    const sp = this.speech(t, P);
    const talk = sp ? clamp(sp.open * 1.6) : 0;
    const lookBack = clamp(B.lookBack ?? 0, -1, 1);

    // ---- feet & pelvis (root-local)
    const pel = V(0.007 * fbm1(t * 0.3, 5) * idle, HIP_Y + br * 0.004 - 0.004, 0);
    let pelYaw = 0.02 * fbm1(t * 0.21, 8) * idle, pelRoll = 0.012 * fbm1(t * 0.27, 9) * idle, pelPitch = 0, lean = 0, chestYaw = 0, swingDz = 0, impact = 0;
    const feet = [1, -1].map((s) => ({ s, a: V(s * 0.1, ANKLE_Y, s > 0 ? 0.02 : -0.01), pitch: 0, yaw: s * 0.1, pole: V(s * 0.1, 0, 1) }));
    if (amt > 0) {
      const zs = [];
      for (const f of feet) {
        const c = footCycle(fract(ph + (f.s > 0 ? 0 : 0.5)), ST);
        const wa = plantAnkle(f.s * (0.1 - 0.015 * ST.run + 0.015 * ST.stomp), c.z, c.lift, c.pitch, V());
        f.a.lerp(wa, amt); f.pitch = lerp(f.pitch, c.pitch, amt); f.yaw = lerp(f.yaw, f.s * (0.05 + 0.08 * ST.stomp), amt);
        f.pole.lerp(V(f.s * 0.08, 0, 1), amt);
        zs.push(c.z);
      }
      swingDz = (zs[0] - zs[1]) / (ST.stride * ST.stance);
      pel.y -= amt * ST.bob * (0.5 + 0.5 * Math.cos(4 * Math.PI * (ph - ST.bobPh))) - amt * ST.run * 0.02;
      if (ST.stomp) {   // heavy landing: a sharp drop right after each heel slam
        const lp = fract(ph * 2 + 0.02);
        impact = Math.exp(-lp * 9) * (1 - Math.exp(-lp * 60));
        pel.y -= amt * 0.028 * impact;
      }
      pel.x += amt * ST.sway * Math.sin(2 * Math.PI * ph);
      pelYaw += -amt * ST.twist * swingDz;
      pelRoll += amt * (0.025 + 0.02 * ST.stomp) * Math.cos(2 * Math.PI * ph);
      chestYaw += amt * ST.twist * 0.8 * swingDz;
      lean += amt * ST.lean;
    }
    if (kneel > 0) {
      const ks = B.kneelSide === 'L' ? 1 : -1;
      const k1 = smooth(kneel / 0.45), k2 = smooth((kneel - 0.15) / 0.85);
      for (const f of feet) {
        if (f.s === ks) { f.a.lerp(V(ks * 0.1, 0.1, -0.38), k2); f.a.y += Math.sin(Math.PI * k2) * 0.04; f.pitch = lerp(f.pitch, 1.25, k2); f.pole.lerp(V(0, -0.7, 1), k2); }
        else { f.a.lerp(V(-ks * 0.12, ANKLE_Y, 0.32), k1); f.a.y += Math.sin(Math.PI * k1) * 0.07; f.pitch *= 1 - k1; f.pole.lerp(V(-ks * 0.15, 0.25, 1), k1); }
      }
      pel.lerp(V(0, 0.49, -0.05), k2);
      lean += 0.14 * Math.sin(Math.PI * k2) + 0.04 * k2;
    }
    if (crouch > 0) {
      const c = smooth(crouch);
      pel.y -= 0.34 * c; pel.z -= 0.08 * c;
      for (const f of feet) { f.a.x += f.s * 0.035 * c; f.pole.lerp(V(f.s * 0.4, 0, 1), c); }
      lean += 0.42 * c;
    }
    let fall = 0;
    if (sit > 0) {
      const tab = sitPath === 'rise' ? SIT_RISE : sitPath === 'plain' ? SIT_PLAIN : SIT_FALL;
      const k = sitPath === 'plain' ? SIT_PLAIN[1][1].map((x, i) => lerp(SIT_STAND[i], x, smooth(sit))) : crKeys(tab, sit);
      const [pY, pZ, pP, cL, lz, ly, rz, ry, fp, ko] = k;
      const wS = smoothstep(0, 0.12, sit);                       // blend away from whatever the feet were doing
      pel.y = lerp(pel.y, pY + (pel.y - HIP_Y) * (1 - sit), wS); pel.z = lerp(pel.z, pZ, wS);
      pelPitch += pP * wS; lean = lerp(lean, cL, wS) + (sitPath === 'fall' ? 0 : 0);
      for (const f of feet) {
        const L = f.s > 0;
        const zf = L ? lz : rz, yf = L ? ly : ry;
        const target = plantAnkle(f.s * (0.11 + ko * 0.4), zf, yf, fp, V());
        f.a.lerp(target, wS); f.pitch = lerp(f.pitch, fp, wS);
        f.yaw = lerp(f.yaw, f.s * (0.12 + ko), wS);
        f.pole.lerp(V(f.s * (0.2 + ko), 1, 0.45), smoothstep(0.15, 0.6, sit));
      }
      if (sitPath === 'fall') { fall = bump(sit, 0.1, 0.86) ** 0.8; impact = Math.max(impact, bump(sit, 0.74, 0.92)); }
      // scoot backward while seated: hitch the hips back, re-plant the feet (scene moves pos backward)
      if (scoot > 0) {
        const sp2 = fract(B.scootPhase ?? t * 1.6), D = this.scootSpeed(1);
        const push = smooth(sp2 / 0.45);
        const zp = (sp2 < 0.45 ? -D * push + D * sp2 : -D + D * sp2) * scoot;
        const fw = (sp2 < 0.45 ? D * sp2 : sp2 < 0.85 ? D * sp2 - D * smooth((sp2 - 0.45) / 0.4) : D * sp2 - D) * scoot;
        pel.z += zp; pel.y += 0.022 * scoot * bump(sp2, 0.02, 0.5);
        lean += scoot * (0.12 * bump(sp2, 0, 0.5) - 0.04);
        for (const f of feet) {
          f.a.z += fw - 0.17 * scoot; f.a.y += 0.035 * scoot * bump(sp2, 0.5, 0.85);
          f.pitch = lerp(f.pitch, -0.35, scoot); f.pole.lerp(V(f.s * 0.3, 1, 0.6), scoot);
        }
      }
    }
    pel.y += B.bounce ?? 0;
    if (tremble > 0) { pel.x += 0.002 * tremble * noise1(t * 14, 3); }
    this.pelvisG.position.copy(pel);
    this.pelvisG.rotation.set(pelPitch, pelYaw + lookBack * 0.12, pelRoll);
    // ---- chest
    const chestLean = lean + (B.lean ?? 0) + slump * 0.2 + hunch * 0.15 - recoil * 0.22 + br * 0.012 + 0.008 * fbm1(t * 0.23, 12) * idle
      + jut * 0.08 + impact * 0.08 + 0.012 * tremble * noise1(t * 12, 21);
    this.chestG.position.set(0, WAIST_H - slump * 0.02 - impact * 0.012, 0);
    this.chestG.rotation.set(chestLean, chestYaw + (B.twist ?? 0) + lookBack * 0.42 + 0.02 * fbm1(t * 0.19, 13) * idle, -(B.tilt ?? 0) + 0.014 * fbm1(t * 0.25, 14) * idle);
    this.pelvisG.updateMatrix(); this.chestG.updateMatrix();
    this.Mp.copy(this.pelvisG.matrix); this.Mc.multiplyMatrices(this.Mp, this.chestG.matrix);
    this.MpYaw = new THREE.Matrix4().makeRotationY(pelYaw);
    // ---- neck & head
    this.neckG.position.set(0, NECK_BASE - shrug * 0.024 - slump * 0.01, -0.012 + hunch * 0.028 + jut * 0.045);
    let hy = Hd.yaw ?? 0, hp = Hd.pitch ?? 0, hr = Hd.roll ?? 0;
    hy += 0.035 * fbm1(t * 0.17, 21) * idle; hp += 0.02 * fbm1(t * 0.19, 22) * idle; hr += 0.018 * fbm1(t * 0.15, 23) * idle;
    hy -= chestYaw * 0.85; hy += lookBack * 1.05;
    const comp = Hd.compensate ?? 1;
    hp += amt * (0.012 + 0.03 * ST.run) * Math.cos(4 * Math.PI * ph) - (lean + pelPitch * 0.85) * 0.75 * comp;
    hp += slump * 0.18 - recoil * 0.15 - hunch * 0.12 - jut * 0.22 + impact * 0.12 + flinch * 0.12;
    if (ST.stomp && amt > 0) hp += 0.1 * amt;
    if (tremble > 0) { hy += 0.012 * tremble * noise1(t * 13, 41); hp += 0.01 * tremble * noise1(t * 11, 42); }
    if (sp && (Hd.talk ?? 1) > 0) { const k2 = Hd.talk ?? 1; hp += 0.05 * (sp.open - 0.3) * k2; hy += 0.03 * noise1(t * 0.8, 31) * k2; hr += 0.02 * noise1(t * 0.6, 32) * k2; }
    const follow = clamp(Hd.follow ?? 0);
    if (follow > 0) {
      const lp = Hd.look ? toV(Hd.look) : gazePoint(P.gaze, CTX.camera);
      if (lp) {
        this.root.updateMatrixWorld(true);
        const loc = this.chestG.worldToLocal(lp.clone()).sub(V(0, NECK_BASE + NECK_LEN + 0.06, 0));
        const yT = clamp(Math.atan2(loc.x, loc.z), -1.4, 1.4), pT = clamp(-Math.atan2(loc.y, Math.hypot(loc.x, loc.z)), -0.75, 0.7);
        hy = lerp(hy, yT + (Hd.yaw ?? 0), follow); hp = lerp(hp, pT + (Hd.pitch ?? 0), follow);
      }
    }
    this.neckG.rotation.set(0.3 * hp + hunch * 0.3 + jut * 0.35, 0.3 * hy, -0.3 * hr);
    this.headPivot.rotation.set(0.7 * hp - hunch * 0.22, 0.7 * hy, -0.7 * hr);
    this.root.updateMatrixWorld(true);
    this.Mh.multiplyMatrices(this.rootInv, this.headG.matrixWorld);

    // ---- face
    const fp = resolveFace(P.face);
    const tears = clamp(E.tears ?? 0);
    if (tears > 0) { fp.tearL = Math.max(fp.tearL, tears * 0.9); fp.tearR = Math.max(fp.tearR, tears * 0.9); fp.wet = Math.max(fp.wet, tears); }
    if (impact > 0.3 && sitPath === 'fall') { fp.lidU = lerp(fp.lidU, 0.35, (impact - 0.3) * 1.2); fp.browSq = Math.max(fp.browSq, impact * 0.6); }
    const gaze = gazePoint(P.gaze, CTX.camera);
    this.face.update(t, fp, { gaze, speech: sp, blinkAt: P.blinkAt });
    const glisten = clamp(Math.max(E.glisten ?? 0, (this.face.state.wet ?? 0) * 0.8, tears));
    this.wetMat.opacity = 0.75 * glisten;
    for (const w of this.wetLines) w.visible = glisten > 0.02;
    // hair: cowlick bounce + swing of the hanging ends
    const run = amt * ST.run;
    const hb = amt * (0.25 + 0.6 * ST.run + 0.5 * ST.stomp) * Math.sin(4 * Math.PI * ph - 0.6) + 0.06 * fbm1(t * 0.9, 51) + impact * 0.8 + tremble * 0.15 * noise1(t * 9, 52);
    this._updateCowlick(hb, t);
    const sw = E.hairSwing ? toV(E.hairSwing) : V();
    sw.y += 0;
    sw.z -= run * 0.01 + amt * 0.004;
    sw.x += amt * 0.006 * Math.sin(2 * Math.PI * ph - 0.8);
    this.HS.swing.value.copy(sw);
    this.HS.bounce.value = -0.006 * hb;
    // glasses
    this.glasses.visible = (E.glasses ?? 1) > 0.5;
    if (this.glasses.visible) {
      const slip = clamp(E.glassesSlip ?? 0), jump = (E.glassesJump ?? 0) + impact * 0.6 * (sitPath === 'fall' ? 1 : 0);
      this.glasses.position.set(0, -0.011 * slip + 0.008 * jump, -0.004 * slip);
      this.glasses.rotation.set(0.05 * slip, 0, E.glassesTilt ?? 0);
    }

    // ---- neck tube
    if (!this.neckTube) { this.neckTube = new SweepTube({ material: this.bodySkin, segments: 6, radial: 14, capRings: 2 }); this.root.add(this.neckTube.mesh); }
    const n0 = V(0, NECK_BASE - 0.05, -0.014).applyMatrix4(this.Mc);
    const n1 = V(0, -HEAD_UP + 0.02, -0.005).applyMatrix4(this.Mh);
    const n2 = V(0, -0.08, -0.025).applyMatrix4(this.Mh);
    this.neckTube.update([n0, n1, n2], [0.043, 0.042, 0.042]);

    // ---- legs (IK) -> jogger tubes + sneakers, thigh capsules for the hoodie hem
    const caps = [], knee = {};
    for (const f of feet) {
      const side = f.s > 0 ? 'L' : 'R', F = this.feet[side];
      F.hip.set(f.s * HIP_X, HIP_DY, 0).applyMatrix4(this.Mp);
      const { mid: kn, end: ankle } = solveIK2(F.hip, f.a, THIGH, SHIN, f.pole.normalize());
      F.knee.copy(kn); F.ankle.copy(ankle); knee[side] = kn.clone();
      F.g.position.copy(ankle); F.g.rotation.set(f.pitch, f.yaw + pelYaw * 0.4, 0);
      const sd = kn.clone().sub(ankle).normalize();
      const hipIn = F.hip.clone().add(V(-f.s * 0.02, 0.05, 0).applyMatrix4(new THREE.Matrix4().extractRotation(this.Mp)));
      const thighMid = F.hip.clone().lerp(kn, 0.5), shinMid = kn.clone().lerp(ankle, 0.5);
      const cuffTop = ankle.clone().addScaledVector(sd, 0.05), cuff = ankle.clone().addScaledVector(sd, 0.004);
      F.leg.update([hipIn, F.hip, thighMid, kn, shinMid, cuffTop, cuff], (u) => {
        let r = u < 0.42 ? lerp(0.088, 0.072, smoothstep(0.1, 0.42, u)) : u < 0.7 ? lerp(0.07, 0.06, (u - 0.42) / 0.28) : lerp(0.06, 0.055, (u - 0.7) / 0.2);
        if (u > 0.8 && u < 0.94) r += 0.006 * Math.abs(Math.sin((u - 0.8) / 0.14 * Math.PI * 2));   // bunching above the cuff
        if (u >= 0.94) r = lerp(0.05, 0.042, smoothstep(0.94, 0.97, u));
        return r;
      });
      caps.push({ a: F.hip, b: kn, ra: 0.1, rb: 0.085 });
      this._anch['knee' + side].position.copy(kn); this._anch['foot' + side].position.copy(ankle);
    }
    // ---- arms (+ phone)
    const actx = { t, amt, ST, ph, swing: swingDz, shrug, hunch, br, talk, knee, fall, tremble, flail: Wk.flail ?? (ST.run ? 0.55 : 0),
      phoneUp: E.phoneUp ?? 0, tap: E.tap ?? 0, thumbOn: E.thumb ?? (E.tap != null ? 1 : 0), screen: E.screen || 'feed', thumbAt: E.thumbAt || null };
    this.phoneGrip = 'flat';
    this._updateArm('L', P.armL, actx);
    this._updateArm('R', P.armR, actx);
    this._anch.elbowL.position.copy(this.arms.L.elbow); this._anch.elbowR.position.copy(this.arms.R.elbow);
    this._updatePhone(t, E);
    // ---- hoodie body, hood strings
    this._updateTorso({ shrug, br, caps });
    this.hoodG.position.y = shrug * 0.03;
    this._updateStrings(t, { amt, ph, ST, br, shrug });
    this._updateTears(t, tears, run);
    // ---- contact shadow / rim
    this.shadow.visible = P.shadow !== false;
    this.shadow.scale.set(1 + 0.5 * sit, 1, 1 + 1.0 * sit);
    this.shadow.position.set(pel.x, 0.004, pel.z * 0.5 + 0.18 * sit);
    const rimK = P.rim ?? 1;
    for (const [m, base] of this._rims) m.userData.uniforms.uRim.value = base * rimK;
    this.state = { t, sit, crouch, kneel, amt, shrug, impact };
    return this;
  }
}

/**
 * headShake(t, t0, opts) -> { yaw, hairSwing } — a 'hell no' head shake starting at t0 (pure function of t).
 * Pass yaw into head.yaw and hairSwing into extra.hairSwing (the bob lags behind the head).
 * opts: { count (shakes, default 2.5), dur (s, 0.85), amp (rad, 0.36) }
 */
export function headShake(t, t0, { count = 2.5, dur = 0.85, amp = 0.36 } = {}) {
  const u = (t - t0) / dur;
  if (u <= 0 || u >= 1.25) return { yaw: 0, hairSwing: [0, 0, 0] };
  const env = u < 1 ? Math.pow(Math.sin(Math.PI * Math.min(1, u)), 0.6) : 0;
  const w = 2 * Math.PI * count;
  const yaw = amp * env * Math.sin(w * u);
  const lagEnv = u < 1.25 ? Math.pow(Math.sin(Math.PI * Math.min(1, u / 1.25)), 0.6) : 0;
  return { yaw, hairSwing: [-0.022 * lagEnv * Math.sin(w * u - 1.2), 0, 0] };
}

export async function create() { return new User(); }
export { User };
