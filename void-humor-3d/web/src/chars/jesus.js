// JESUS — warm, kind, playful, unhurried stylized human (1.75 m). Fully procedural rig:
//   sculpted head (custom surface shared with the Face rig) + nose/ears, big warm brown eyes with lash lines,
//   thick swept brows, painted mouth with lips + laugh lines inside a SCULPTED BEARD SHELL whose mouth opening
//   is recomputed every frame from the mouth shape (lips always readable, never covered by the mustache),
//   middle-parted hair cap + chunky shoulder-length locks (gravity + shoulder collision), lathe robe whose
//   skirt is re-draped every frame by a stateless column solver (legs / hips / floor collisions -> walk sway,
//   kneel folds and floor puddles), wide bell sleeves that slide down raised forearms, terracotta mantle over
//   the left shoulder, twisted rope belt with hanging ends, sandals with visible toes, subtle golden rim glow.
// Pose API + tips: docs/chars/jesus.md. Every frame is a pure function of (t, pose).
import * as THREE from 'three';
import { mergeVertices, mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { Character, gazePoint } from '../core/character.js';
import { Face, EXPR, FACE_DEFAULTS } from '../core/face.js';
import { SweepTube, solveIK2, orientYZ } from '../core/limbs.js';
import { enhance, contactShadow } from '../core/materials.js';
import { CTX } from '../core/context.js';
import { clamp, lerp, smooth, smoothstep, noise1, fbm1, hash1, schedule } from '../core/util.js';

// ---------------------------------------------------------------------------------------------------------
// Palette
const SKIN = 0xb08c6e, HAIR_C = 0x46291a, BROW_C = 0x3a2215, ROBE_C = 0xe9ddc4, MANTLE_C = 0xb34d33,
  ROPE_C = 0xb49467, LEATHER_C = 0x6d4429, GOLD = 0xffc46e;

// Proportions (metres). Root at the feet, facing +Z, +X = character's left.
const HIP_Y = 0.92, WAIST_H = 0.12, CHEST_Y0 = HIP_Y + WAIST_H;      // waist pivot at 1.04
const NECK_BASE = 0.30, NECK_LEN = 0.072, HEAD_UP = 0.122, HEAD_SCALE = 1.08;   // head centre ~1.53
const SH = [0.178, 0.272, -0.012];                                   // left shoulder joint (chest-local)
const UPPER = 0.27, FORE = 0.25, HAND_SIZE = 0.17;
const HIP_X = 0.09, THIGH = 0.42, SHIN = 0.41, ANKLE_Y = 0.075, FLOOR = 0.012;
const HR = [0.136, 0.165, 0.152];                                    // skull radii
const EYE_U = 0.36, EYE_V = 0.08, EYE_R = 0.04, MOUTH_V = -0.50, HW0 = 0.041;
const JAW = { y: -0.09, drop: 0.019, back: 0.006, soft: 0.032 };
const MAXWRIST = 1.25;                                               // max finger/forearm angle (rad)

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const fract = (x) => x - Math.floor(x);
const rounded = (x) => { const y = 1 - clamp(x); return Math.sqrt(Math.max(0, 1 - y * y)); };
function pw(K, a) { // piecewise-linear lookup in [[x, y], ...]
  if (a <= K[0][0]) return K[0][1];
  for (let i = 1; i < K.length; i++) if (a <= K[i][0]) return lerp(K[i - 1][1], K[i][1], (a - K[i - 1][0]) / (K[i][0] - K[i - 1][0]));
  return K[K.length - 1][1];
}
const toV = (a) => (a instanceof THREE.Vector3 ? a.clone() : V(a[0], a[1], a[2]));
// core SweepTube closes even an un-capped end with a flat fan; drop those triangles for truly open tubes
function openTube(tube, start = false, end = true) {
  const tipA = tube.rings * tube.R, tipB = tipA + 1, src = tube.geo.index.array, keep = [];
  for (let i = 0; i < src.length; i += 3) {
    const a = src[i], b = src[i + 1], c = src[i + 2];
    if ((start && (a === tipA || b === tipA || c === tipA)) || (end && (a === tipB || b === tipB || c === tipB))) continue;
    keep.push(a, b, c);
  }
  tube.geo.setIndex(keep);
  return tube;
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

// MeshStandard + core enhance() (cheap rim / wrap / glow): the perf-friendly replacement for MeshPhysical sheen
function stdMat(color, o = {}) {
  const m = new THREE.MeshStandardMaterial({ color: new THREE.Color(color), roughness: o.roughness ?? 0.85, metalness: 0,
    side: o.side ?? THREE.FrontSide, vertexColors: !!o.vertexColors });
  return enhance(m, { rim: o.rim ?? 0.2, rimColor: o.rimColor ?? 0xffffff, rimPower: o.rimPower ?? 3.2, glow: o.glow ?? 0.03,
    wrap: o.wrap ?? 0, wrapColor: o.wrapColor ?? 0xff8866, jaw: o.jaw });
}

// ---------------------------------------------------------------------------------------------------------
// Head surface (head-local: origin = head centre, +Z out of the face). Shared by mesh, Face, hair, beard.
function headPoint(u, v, out = new THREE.Vector3()) {
  const cv = Math.cos(v), sv = Math.sin(v), cu = Math.cos(u), su = Math.sin(u);
  let x = HR[0] * su * cv, y = HR[1] * sv, z = HR[2] * cu * cv;
  const front = Math.max(0, cu), au = Math.abs(u);
  const low = smoothstep(-0.05, -1.25, v);
  x *= 1 - 0.13 * low;                                         // jaw tapers toward the chin
  const back = Math.max(0, -cu) * smoothstep(-0.5, 0.6, v);
  x *= 1 + 0.025 * back; z *= 1 + 0.07 * back;                // fuller cranium
  const chin = Math.exp(-(((v + 0.95) / 0.3) ** 2)) * front ** 4;
  z += 0.012 * chin;
  const ck = Math.exp(-(((au - 0.62) / 0.26) ** 2) - (((v + 0.14) / 0.2) ** 2)) * front;   // cheekbones
  const es = Math.exp(-(((au - EYE_U) / 0.16) ** 2) - (((v - EYE_V) / 0.13) ** 2));        // eye sockets
  const br = Math.exp(-(((au - 0.34) / 0.32) ** 2) - (((v - 0.36) / 0.09) ** 2)) * front;  // brow ridge
  const k = 1 + 0.03 * ck - 0.016 * es + 0.02 * br;
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

// Hairline latitude per longitude (middle part; hair sweeps down over the temples, covers the ears).
const HAIRLINE = [[0, 0.80], [0.3, 0.74], [0.55, 0.57], [0.8, 0.37], [1.05, 0.16], [1.3, -0.08], [1.6, -0.32], [2.2, -0.66], [Math.PI, -0.82]];
// soft side-swept masses over the temples lower the hairline a little (rounded lobe, breaks the forehead ledge)
const templeMass = (au) => Math.exp(-(((au - 0.74) / 0.2) ** 2));
const hairline = (u) => pw(HAIRLINE, Math.abs(u)) - 0.045 * templeMass(Math.abs(u));
// Hanging locks: 3 per side + one shared at the back centre (lock centres at |u| = 0.9 + (i + 0.5) * LOCK_P)
const LOCK_U0 = 0.9, LOCK_P = (Math.PI - LOCK_U0) / 3.5;
function lockOf(u) {
  const s = Math.max(0, (Math.abs(u) - LOCK_U0) / LOCK_P), id = Math.floor(s), f = s - id;
  const c = Math.cos(Math.PI * (f - 0.5)) ** 2;                               // 1 at a lock centre, 0 in the groove
  return { id, f, c, ph: 1.7 * id + (u < 0 && id < 3 ? 0.9 : 0) };             // slight L/R asymmetry
}
function hairThick(u, v, vh, p, cw = 0) {
  const dv = v - vh, au = Math.abs(u);
  const cu = Math.cos(u), side = Math.abs(Math.sin(u));
  const front = smoothstep(0.6, 0.2, au) * Math.max(0, cu);
  // edge profile: rounded lip at the sides/back, a thinner softer edge at the forehead (no dark ledge)
  const eLen = lerp(0.15, 0.26, front);
  const edge = lerp(lerp(rounded(dv / eLen), smooth(dv / eLen) * 0.75 + 0.25 * rounded(dv / eLen), front), 1, cw);
  let T = 0.019 + 0.017 * side * smoothstep(-0.6, 0.6, v) + 0.008 * smoothstep(0.6, 1.3, v);
  const part = Math.exp(-((u / 0.075) ** 2)) * Math.max(0, cu) * smoothstep(0.55, 0.85, v) * (1 - smoothstep(1.2, 1.45, v));
  T *= 1 - 0.6 * part;
  // temple masses: swept volume rolling from the part over the temples
  const tm = templeMass(au) * Math.exp(-(((v - (0.47 + 0.25 * (0.74 - au))) / 0.2) ** 2));
  T += 0.011 * tm;
  // flow grooves: from the part toward the ears at the front, continuing into the hanging locks at the back
  const phiX = Math.atan2(p.z, p.y);
  const back = smoothstep(0.2, -0.6, cu);
  const L = lockOf(u);
  const ridge = lerp(Math.sin(phiX * 7 + 0.9), 2 * L.c - 1, back);
  T *= 1 + 0.22 * ridge * smoothstep(0.02, 0.2, dv) * (1 - smoothstep(1.25, 1.5, v));
  T = lerp(T, 0.03, smoothstep(1.25, 1.5, v));
  return lerp(-0.003, T, edge);
}

// Beard region: top edge (mustache under the nose -> cheek line -> sideburn), bottom under the chin.
const BEARD_TOP = [[0, -0.285], [0.22, -0.30], [0.42, -0.355], [0.62, -0.31], [0.85, -0.2], [1.05, -0.07], [1.25, 0.06], [1.62, 0.14]];
const BEARD_BOT = [[0, -1.36], [0.9, -1.33], [1.3, -1.2], [1.62, -1.0]];
// smooth (Hermite) lookup through [[x, y], ...] — no kinks in the beard contour
function hermite(K, a) {
  if (a <= K[0][0]) return K[0][1];
  const n = K.length;
  for (let i = 1; i < n; i++) if (a <= K[i][0]) {
    const [x0, y0] = K[i - 1], [x1, y1] = K[i], h = x1 - x0, t = (a - x0) / h;
    const m = (j) => (j <= 0 ? (K[1][1] - K[0][1]) / (K[1][0] - K[0][0]) * 0 : j >= n - 1 ? (K[n - 1][1] - K[n - 2][1]) / (K[n - 1][0] - K[n - 2][0]) : (K[j + 1][1] - K[j - 1][1]) / (K[j + 1][0] - K[j - 1][0]));
    const t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * y0 + (t3 - 2 * t2 + t) * h * m(i - 1) + (-2 * t3 + 3 * t2) * y1 + (t3 - t2) * h * m(i);
  }
  return K[n - 1][1];
}
// cheek line with soft tuft scallops (the mustache stays clean)
const beardTop = (a) => hermite(BEARD_TOP, a) + 0.016 * Math.pow(Math.max(0, Math.sin(a * 15 + 0.3)), 2) * smoothstep(0.5, 0.75, a) * smoothstep(1.4, 1.1, a);
const beardBot = (a) => hermite(BEARD_BOT, a);
const beardEdge = (u, v) => { const a = Math.abs(u); return Math.min((beardTop(a) - v) / 0.1, (v - beardBot(a)) / 0.14, (1.6 - a) / 0.16); };
function beardStatic(u, v) {
  const a = Math.abs(u);
  const e = beardEdge(u, v);
  let T = 0.0085 + 0.0035 * smoothstep(0.3, 1.0, a);
  T += 0.009 * Math.exp(-((u / 0.55) ** 2)) * smoothstep(-0.62, -1.0, v);          // chin mass
  T *= lerp(0.72, 1, smoothstep(-0.36, -0.5, v) + smoothstep(0.42, 0.6, a));           // finer mustache
  const lower = smoothstep(-0.5, -0.85, v);
  // tuft lobes along the jaw / chin silhouette + soft flow variation on the cheeks
  T *= 1 + 0.32 * Math.pow(Math.max(0, Math.sin(u * 8.5 + 0.6 + Math.sin(v * 3) * 0.8)), 2) * lower - 0.08 * lower + 0.05 * Math.sin(u * 9 - v * 4) * (1 - lower);
  return lerp(-0.0045, T, rounded(e));
}

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
  if (h < HW0 * 0.04) {
    const cy = -smile * HW0 * 0.06;
    const c1 = cy - cm * 0.35 + (smile < 0 ? -smile * HW0 * 0.15 : 0);
    top = bot = 0.25 * cm + 0.75 * c1;
  } else {
    const yTop = cm * 0.35 + h * 0.3 + (smile < 0 ? -smile * HW0 * 0.1 : 0);
    const yBot = cm * 0.2 - h * 0.7 - (smile > 0 ? smile * h * 0.35 : 0);
    top = 0.25 * cm + 0.75 * yTop; bot = 0.25 * cm + 0.75 * yBot;
  }
  return { w, shift, yL, yR, cm, top, bot, h, open: h >= HW0 * 0.04, smile, press, round };
}
// signed distance-ish from the lip outline (negative inside the opening the beard must leave clear)
function lipHoleDist(X, Y, g) {
  const tx = (X - g.shift) / g.w, at = Math.abs(tx);
  const s = at < 1 ? 1 - at * at : 0;
  const yc = lerp(g.yR, g.yL, clamp((tx + 1) / 2));
  const m = Math.sqrt(Math.max(0, 1 - (at / 1.22) ** 2));
  const top = yc + (g.top - g.cm) * s + (0.0085 + 0.002 * g.round) * m;
  const bot = yc + (g.bot - g.cm) * s - (0.0135 + 0.002 * g.round) * m;
  return Math.max((at - 1.22) * g.w, Y - top, bot - Y);
}

// ---------------------------------------------------------------------------------------------------------
// Expression presets (layer on top of core EXPR; JX('teehee', {...}) -> full flat params)
export const JEXPR = {
  kind: { mSmile: 0.3, lidU: 0.96, lidL: 0.06, browIn: 0.16, browOut: 0.06 },
  warm: { mSmile: 0.64, lidU: 0.88, lidL: 0.26, browIn: 0.26, browOut: 0.14, blush: 0.08 },
  beam: { mSmile: 0.94, mOpen: 0.22, mTeethU: 1, mTeethL: 0.1, lidU: 0.74, lidL: 0.62, browIn: 0.4, browOut: 0.32, blush: 0.16 },
  laugh: { mSmile: 1, mOpen: 0.74, mTeethU: 1, mTeethL: 0.3, mTongue: 0.6, lidL: 1, lidU: 0.04, browIn: 0.62, browOut: 0.3, blush: 0.3, wet: 0.4, autoBlink: 0, saccade: 0 },
  teehee: { mSmile: 1, mOpen: 0.15, mTeethU: 1, mTeethL: 0, lidU: 0.0, lidL: 1, browIn: 0.68, browOut: 0.26, blush: 0.36, autoBlink: 0, saccade: 0 },
  content: { mSmile: 0.42, lidU: 0.5, lidL: 0.3, browIn: 0.08, browOut: 0.14, saccade: 0.3 },
  listening: { mSmile: 0.16, lidU: 0.98, lidL: 0.1, browIn: 0.42, browOut: 0.06, browMid: 0.06 },
  whisper: { mSmile: 0.32, mAsym: 0.32, mRound: 0.3, mOpen: 0.07, lidU: 0.78, lidL: 0.34, browIn: 0.3, browAsym: 0.4 },
  amused: { mSmile: 0.58, mAsym: 0.42, lidU: 0.82, lidL: 0.36, browAsym: 0.42, browIn: 0.14, browOut: 0.1 },
  // the hero "oh boy, this is awkward": wide clenched teeth, corners strained out & a touch down, worried brows up
  awkward: { mClench: 1, mOpen: 0.34, mWide: 1, mSmile: -0.04, mAsym: 0.16, browIn: 1.0, browOut: 0.18, browSq: 0.12, browAsym: 0.16, lidU: 1.22, lidSad: 0.42, saccade: 0 },
  compassion: { browIn: 0.95, browOut: -0.22, browSq: 0.3, lidSad: 0.5, lidU: 0.94, mSmile: 0.02, mPress: 0.22, wet: 0.35 },
  concerned: { browIn: 0.78, browOut: -0.16, browSq: 0.36, lidSad: 0.38, lidU: 1.0, mSmile: -0.08, mPress: 0.3 },
  tender: { mSmile: 0.38, lidU: 0.82, lidL: 0.24, lidSad: 0.36, browIn: 0.72, browOut: -0.14, wet: 0.55 },
  hopeful: { mSmile: 0.56, mOpen: 0.1, mTeethU: 0.8, browIn: 0.68, browOut: 0.5, lidU: 1.1, lidL: 0.16, wet: 0.3 },
  eager: { mSmile: 1, mOpen: 0.32, mTeethU: 1, mTeethL: 0.5, browIn: 0.85, browOut: 0.8, lidU: 1.3, lidL: 0.2, pupil: 1.2, wet: 0.6 },
  // "eh — oh well": brows way up, a small closed amiable smile pulled to one side
  shrug: { browIn: 0.78, browOut: 0.95, mSmile: 0.16, mPress: 0.42, mWide: 0.28, mAsym: 0.34, lidU: 1.02, lidL: 0.12 },
  rueful: { browIn: 0.56, browOut: 0.5, browAsym: 0.32, mSmile: 0.26, mPress: 0.62, mAsym: 0.48, lidU: 0.8, lidL: 0.26 },
  oh: { lidU: 1.14, browIn: 0.55, browOut: 0.5, mOpen: 0.2, mRound: 0.65, mSmile: 0.05 },
  ooh: { lidU: 1.2, browIn: 0.6, browOut: 0.7, mOpen: 0.32, mRound: 0.85, mSmile: 0.25, pupil: 1.2 },
  surprised: { lidU: 1.32, browIn: 0.78, browOut: 0.85, mOpen: 0.34, mRound: 0.42 },
  curious: { lidU: 1.08, browIn: 0.3, browOut: 0.42, browAsym: 0.45, mSmile: 0.12, mRound: 0.2, mPress: 0.1 },
  reading: { lidU: 0.72, lidL: 0.42, browIn: -0.25, browSq: 0.6, mPress: 0.32, mSmile: -0.05 },
  sadSmile: { mSmile: 0.28, browIn: 0.92, browOut: -0.26, lidSad: 0.62, lidU: 0.78, lidL: 0.2, wet: 0.4 },
  wince: { lidU: 0.5, lidL: 0.5, browIn: 0.7, browSq: 0.45, mClench: 0.6, mWide: 0.6, mSmile: -0.12 },
  serene: { mSmile: 0.24, lidU: 0.58, lidL: 0.28, browIn: 0.14, saccade: 0.2 },
  pressed: { mPress: 0.85, mSmile: 0.44, mAsym: 0.12, browIn: 0.4, browOut: 0.38, lidL: 0.46, lidU: 0.8, blush: 0.14 },      // holding in a laugh
};
export function JX(name, over = {}) {
  const base = { ...FACE_DEFAULTS };
  const list = !Array.isArray(name) ? [[name, 1]] : typeof name[0] === 'string' ? [name] : name;   // 'x' | ['x', w] | [['x', w], ...]
  for (const [nm, w = 1] of list) {
    const e = JEXPR[nm] || EXPR[nm] || {};
    for (const [key, val] of Object.entries(e)) base[key] = (base[key] ?? 0) + (val - (FACE_DEFAULTS[key] ?? 0)) * w;
  }
  return Object.assign(base, over);
}
function resolveFace(f) {
  if (f == null) return JX('kind');
  if (typeof f === 'string' || Array.isArray(f)) return JX(f);
  if (f.expr) { const { expr, ...rest } = f; return JX(expr, rest); }
  return { ...FACE_DEFAULTS, ...f };
}

// ---------------------------------------------------------------------------------------------------------
// Arm presets, written for the LEFT arm (x+ = character's left); mirrored for the right.
// t = wrist target, pole = elbow direction, palm = palm normal, fing = finger direction, hand = Hand.pose params.
// space: 'chest' (default; origin = waist pivot, 1.04 m above the feet, rotates with the torso) | 'head'.
export const ARM = {
  rest: { t: [0.235, -0.245, 0.045], pole: [0.35, -0.1, -1], palm: [-1, 0, 0.2], fing: [0.04, -1, 0.15], hand: { curl: 0.13, spread: 0.08, thumb: 0.2, cup: 0.15 } },
  hips: { t: [0.25, -0.06, 0.02], pole: [1, 0.15, -0.5], palm: [-0.4, -0.2, -1], fing: [-0.35, -0.6, 0.6], hand: { curl: 0.85, thumb: 0.2 } },
  side: { t: [0.235, -0.04, 0.07], pole: [1, -0.2, -0.6], palm: [-1, 0, -0.1], fing: [-0.2, -0.8, 0.5], hand: { curl: 0.25, spread: 0.12, cup: 0.4 } },
  crossed: { t: [-0.075, 0.125, 0.18], pole: [1, -0.55, 0.15], palm: [0, -0.4, -1], fing: [-1, 0.2, -0.15], hand: { curl: 0.6, spread: 0.05, thumb: 0.3 } },
  up: { t: [0.22, 0.80, 0.06], pole: [1, 0, -0.4], palm: [0, 0, 1], fing: [0, 1, 0.05], hand: { curl: 0.08, spread: 0.3, thumb: 0.5 } },
  wave: { t: [0.32, 0.50, 0.14], pole: [1, -0.8, -0.2], palm: [0, 0, 1], fing: [0.08, 1, 0], hand: { curl: 0.05, spread: 0.35, thumb: 0.6 }, anim: 'wave' },
  shrug: { t: [0.30, 0.03, 0.20], pole: [0.3, -1, -0.5], palm: [0.15, 1, 0.1], fing: [0.55, 0.05, 1], hand: { curl: 0.12, spread: 0.42, thumb: 0.75, splay: 0.12, cup: 0.15 } },
  open: { t: [0.27, 0.0, 0.25], pole: [0.4, -1, -0.4], palm: [-0.25, 0.9, 0.35], fing: [0.25, -0.05, 1], hand: { curl: 0.1, spread: 0.35, thumb: 0.6, cup: 0.3, splay: 0.06 } },
  explain: { t: [0.16, 0.08, 0.30], pole: [0.6, -1, -0.3], palm: [-0.5, 0.8, 0.25], fing: [-0.15, 0.05, 1], hand: { curl: 0.22, spread: 0.25, thumb: 0.5, cup: 0.4 }, anim: 'beat' },
  offer: { t: [0.12, 0.06, 0.43], pole: [0.5, -1, -0.2], palm: [-0.2, 1, 0.1], fing: [-0.05, 0.1, 1], hand: { curl: 0.1, spread: 0.3, thumb: 0.6, cup: 0.35 } },
  stop: { t: [0.20, -0.05, 0.30], pole: [0.6, -1, -0.5], palm: [0, -1, 0.15], fing: [-0.1, 0.05, 1], hand: { curl: 0.05, spread: 0.2, thumb: 0.4 } },   // gentle 'hold on, one sec'
  heart: { t: [0.0, 0.125, 0.165], pole: [1, -0.6, 0], palm: [0, 0, -1], fing: [-0.45, 0.85, 0.1], hand: { curl: 0.12, spread: 0.12, thumb: 0.35 } },
  clasp: { t: [0.04, -0.06, 0.185], pole: [1, -0.4, -0.6], palm: [-1, 0.25, 0.1], fing: [-0.5, -0.55, 0.6], hand: { curl: 0.55, spread: 0.05, thumb: 0.4 } },
  clasp_chest: { t: [0.045, 0.14, 0.2], pole: [1, -1, -0.4], palm: [-1, 0, 0.1], fing: [-0.3, 0.75, 0.6], hand: { curl: 0.5, spread: 0.05, thumb: 0.45 } },
  behind: { t: [0.07, -0.12, -0.19], pole: [1, 0, 0.3], palm: [-0.3, 0.1, -1], fing: [-1, -0.35, 0], hand: { curl: 0.45, spread: 0.05, thumb: 0.3 } },
  point: { t: [0.2, 0.22, 0.48], pole: [1, -0.6, -0.2], palm: [-1, 0, 0], fing: [0, 0.1, 1], hand: { point: 1, curl: 0.8, thumb: 0.2 } },
  reach: { t: [0.15, 0.2, 0.5], pole: [1, -0.5, -0.2], palm: [0, -1, 0.1], fing: [0, -0.1, 1], hand: { curl: 0.15, spread: 0.15, cup: 0.3 } },
  shoulder: { t: [0.25, 0.28, 0.36], pole: [1, -1, -0.3], palm: [0, -0.86, -0.5], fing: [0.05, -0.5, 0.86], hand: { curl: 0.2, spread: 0.1, cup: 0.38, thumb: 0.3 }, at: 'palm' },
  pat: { t: [0.25, 0.3, 0.36], pole: [1, -1, -0.3], palm: [0, -0.2, 1], fing: [0.1, 1, 0.1], hand: { curl: 0.08, spread: 0.15, cup: 0.3, thumb: 0.35 }, at: 'palm', anim: 'pat' },
  around: { t: [0.5, 0.36, -0.22], pole: [0.5, 0.8, -0.6], palm: [0.45, -0.2, 0.85], fing: [0.85, -0.12, -0.4], hand: { curl: 0.3, spread: 0.2, cup: 0.6, thumb: 0.42 }, at: 'palm' },
  knee_rest: { t: [0.2, -0.32, 0.36], pole: [1, -0.2, -0.3], palm: [-0.2, 0.9, 0.3], fing: [-0.2, 0, 1], hand: { curl: 0.12, spread: 0.3, thumb: 0.55, cup: 0.4, splay: 0.05 }, anim: 'knee' },
  // head-space (face) presets — target relative to the head centre
  whisper: { space: 'head', t: [0.095, -0.15, 0.115], pole: [0.8, -1, 0.0], palm: [-0.62, 0.0, 0.78], fing: [-0.1, 1, 0.08], hand: { curl: 0.14, spread: 0.1, thumb: 0.35, cup: 0.7 } },
  teehee: { space: 'head', t: [0.05, -0.178, 0.148], pole: [0.8, -1, 0.1], palm: [-0.5, -0.15, -0.85], fing: [-0.45, 0.88, 0.15], hand: { curl: 0.5, spread: 0.06, thumb: 0.25, cup: 0.4 } },
  cover_mouth: { space: 'head', t: [0.04, -0.19, 0.15], pole: [0.8, -1, 0.1], palm: [-0.1, 0, -1], fing: [-0.4, 0.92, 0.0], hand: { curl: 0.18, spread: 0.08, thumb: 0.3, cup: 0.45 } },
  chin: { space: 'head', t: [0.03, -0.30, 0.09], pole: [0.8, -1, 0.2], palm: [0.1, -0.3, -1], fing: [-0.2, 0.7, 0.6], hand: { curl: 0.75, spread: 0.05, thumb: 0.5 } },
  wipe_eye: { space: 'head', t: [0.09, -0.10, 0.115], pole: [0.8, -1, 0.2], palm: [-0.4, -0.2, -1], fing: [-0.35, 0.8, 0.2], hand: { curl: 0.85, point: 0, thumb: 0.2 } },
};
const HAND_KEYS = ['curl', 'point', 'spread', 'thumb', 'cup', 'splay', 'grip'];
const HAND_DEF = { curl: 0.15, point: 0, spread: 0.15, thumb: 0.3, cup: 0.1, splay: 0, grip: 0 };

// Walk styles. The scene moves `pos` at stride * cycles/s (see Jesus.walkSpeed()).
export const WALK = {
  walk: { rate: 0.85, stride: 1.05, stance: 0.62, lift: 0.07, bob: 0.016, bobPh: 0, sway: 0.014, twist: 0.10, lean: 0.03, drag: 0.04, arm: 0.13, run: 0 },
  stroll: { rate: 0.72, stride: 0.9, stance: 0.64, lift: 0.055, bob: 0.012, bobPh: 0, sway: 0.016, twist: 0.08, lean: 0.0, drag: 0.03, arm: 0.08, run: 0 },
  run: { rate: 1.35, stride: 2.1, stance: 0.36, lift: 0.17, bob: 0.04, bobPh: 0.18, sway: 0.01, twist: 0.16, lean: 0.17, drag: 0.09, arm: 0.2, run: 1 },
  sneak: { rate: 0.6, stride: 0.6, stance: 0.66, lift: 0.06, bob: 0.01, bobPh: 0, sway: 0.01, twist: 0.06, lean: 0.12, drag: 0.02, arm: 0.04, run: 0 },
};
function footCycle(u, S) {
  const L = S.stride * S.stance, sf = S.stance;
  let z, lift = 0, pitch = 0;
  if (u < sf) {
    const a = u / sf;
    z = lerp(0.5, -0.5, a);
    pitch = a < 0.14 ? lerp(-0.22, 0, smooth(a / 0.14)) : a > 0.62 ? lerp(0, 0.55 + 0.3 * S.run, smooth((a - 0.62) / 0.38)) : 0;
  } else {
    const b = (u - sf) / (1 - sf);
    z = lerp(-0.5, 0.5, smooth(b));
    lift = Math.pow(Math.sin(Math.PI * b), 1.3);
    pitch = lerp(0.55 + 0.3 * S.run, -0.22, smooth(b)) + 0.2 * Math.sin(Math.PI * b);
  }
  return { z: z * L, lift: lift * S.lift, pitch };
}
// ankle position for a foot planted at nominal ankle (x, z) with pitch (heel up > 0 pivots on the ball)
function plantAnkle(x, z, lift, pitch, out) {
  let y = ANKLE_Y, zz = z;
  if (pitch > 0) { const bz = z + 0.10; y = ANKLE_Y * Math.cos(pitch) + 0.10 * Math.sin(pitch); zz = bz + ANKLE_Y * Math.sin(pitch) - 0.10 * Math.cos(pitch); }
  else if (pitch < 0) { const hz = z - 0.05; y = ANKLE_Y * Math.cos(pitch) - 0.05 * Math.sin(pitch); zz = hz + ANKLE_Y * Math.sin(pitch) + 0.05 * Math.cos(pitch); }
  return out.set(x, y + lift, zz);
}

// Robe profile (rest, root-local): [y, rx, rz, superellipse exponent, z-offset]
const ROBE_TOP = [
  [1.402, 0.050, 0.046, 2.0, 0.004],    // inner collar fold
  [1.414, 0.066, 0.060, 2.0, 0.004],    // collar rim
  [1.398, 0.092, 0.077, 2.15, 0.004],
  [1.380, 0.118, 0.089, 2.25, 0.004],
  [1.360, 0.143, 0.101, 2.35, 0.004],
  [1.340, 0.161, 0.111, 2.42, 0.005],   // rounded shoulder (more rows, softer superellipse: no square corners)
  [1.318, 0.1745, 0.119, 2.48, 0.006],
  [1.292, 0.1815, 0.125, 2.5, 0.008],
  [1.260, 0.183, 0.130, 2.5, 0.010],
  [1.220, 0.179, 0.135, 2.45, 0.014],
  [1.180, 0.172, 0.138, 2.4, 0.017],
  [1.110, 0.162, 0.133, 2.3, 0.012],
  [1.050, 0.166, 0.130, 2.2, 0.008],
];
const SKIRT_TOP = 0.995, HEM_Y = 0.085;
const skirtR = (s) => [0.17 + 0.03 * smooth(s / 0.18) + 0.046 * s, 0.132 + 0.03 * smooth(s / 0.18) + 0.082 * s, lerp(2.2, 2.0, s), 0.008 * (1 - s)];
function sePoint(th, rx, rz, n, zo) {
  const s = Math.sin(th), c = Math.cos(th);
  const f = Math.pow(Math.pow(Math.abs(s), n) + Math.pow(Math.abs(c), n), -1 / n);
  return [rx * s * f, rz * c * f + zo];
}
// combined rest profile for anything that hugs the torso (mantle, hair collision)
const PROFILE = [...ROBE_TOP.slice(1), ...[0, 0.1, 0.2, 0.35].map((s) => { const [rx, rz, n, zo] = skirtR(s); return [lerp(SKIRT_TOP, HEM_Y, s), rx, rz, n, zo]; })];
function profileAt(y) {
  if (y >= PROFILE[0][0]) return PROFILE[0];
  for (let i = 1; i < PROFILE.length; i++) {
    if (y >= PROFILE[i][0]) { const a = PROFILE[i - 1], b = PROFILE[i], f = (y - b[0]) / (a[0] - b[0]); return b.map((x, k) => lerp(x, a[k], f)); }
  }
  return PROFILE[PROFILE.length - 1];
}
function robeRest(y, th) { const [, rx, rz, n, zo] = profileAt(y); const [x, z] = sePoint(th, rx, rz, n, zo); return V(x, y, z); }
function robeRestN(y, th) {
  const e = 0.004;
  const a = robeRest(y, th + e).sub(robeRest(y, th - e)), b = robeRest(y + e, th).sub(robeRest(y - e, th));
  const n = new THREE.Vector3().crossVectors(b, a).normalize();
  const p = robeRest(y, th); if (n.x * p.x + n.z * (p.z - 0.01) < 0) n.negate();
  return n;
}
// top-of-torso height (rest, root-local) at horizontal (x, z) or null when outside the torso silhouette
function torsoTopY(x, z) {
  let prevQ = null, prevY = 0;
  for (const [y, rx, rz, , zo] of ROBE_TOP.slice(1)) {
    const q = Math.hypot(x / rx, (z - zo) / rz);
    if (q <= 1) return prevQ == null ? y : lerp(prevY, y, (prevQ - 1) / Math.max(1e-4, prevQ - q));
    prevQ = q; prevY = y;
  }
  return null;
}
// shoulder/scapula protraction influence (root-rest coords) around each shoulder joint
const protW = (x, y, z, s) => Math.exp(-(((x - s * SH[0]) ** 2 + (y - CHEST_Y0 - SH[1]) ** 2 + (z - SH[2]) ** 2) / 0.0095));
const shoulderBand = (x, y) => smoothstep(0.05, 0.16, Math.abs(x)) * smoothstep(1.22, 1.33, y);

// Mantle / sash (root-space rest: [y, angle from +Z toward +X, half-width]): from the knot at the RIGHT front hip,
// up the front to the LEFT shoulder, down the back, then wrapped round the right side at the waist (just under the
// rope belt) back into the knot — one continuous drape from every side. A short knotted tail hangs from the knot.
const KNOT_TH = -0.98, KNOT_Y = 0.958;
const MANTLE = [[KNOT_Y + 0.006, KNOT_TH + 0.02, 0.04], [1.03, -0.74, 0.056], [1.12, -0.42, 0.064], [1.21, -0.06, 0.066], [1.29, 0.36, 0.07], [1.352, 0.86, 0.074],
  [1.376, 1.5, 0.078], [1.352, 2.12, 0.074], [1.29, 2.62, 0.07], [1.205, 3.02, 0.066], [1.11, 3.42, 0.06], [1.03, 3.8, 0.05],
  [0.975, 4.22, 0.038], [0.958, 4.68, 0.035], [0.955, 5.04, 0.035], [KNOT_Y - 0.002, 2 * Math.PI + KNOT_TH - 0.04, 0.034]];

// ---------------------------------------------------------------------------------------------------------
/**
 * SoftHand — same API as core Hand (root, aim(fingerDir, palmNormal), pose({curl, point, spread, thumb, cup,
 * splay, grip, perFinger})) but every finger is ONE smooth swept tube through its joints (no capsule gaps), so
 * curls, cups and fists stay clean in close-ups. Local frame: wrist at origin, fingers +Y, palm faces -Z,
 * thumb on the anatomically correct side (RIGHT hand: -X, LEFT hand: +X).
 */
class SoftHand {
  constructor({ size = 0.17, side = 'R', material }) {
    this.size = size; this.side = side;
    const ts = this.ts = side === 'L' ? 1 : -1;
    this.root = new THREE.Group();
    const pl = this.pl = size * 0.47, pw = this.pw = size * 0.45, pt = this.pt = size * 0.19;
    const palm = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), material);
    palm.scale.set(pw * 0.53, pl * 0.58, pt * 0.52); palm.position.set(0, pl * 0.52, -pt * 0.05);
    const heel = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), material);
    heel.scale.set(pw * 0.4, pl * 0.32, pt * 0.5); heel.position.set(ts * pw * 0.06, pl * 0.18, -pt * 0.04);
    this.root.add(palm, heel);
    bake(this.root, [palm, heel]);
    const lens = [0.93, 1.0, 0.95, 0.77];
    this.fingers = [0, 1, 2, 3].map((i) => {
      const u = (i - 1.5) / 1.5;                                    // index = -1 (thumb side)
      const tube = new SweepTube({ material, segments: 10, radial: 8, capRings: 2 });
      this.root.add(tube.mesh);
      const L = size * 0.53 * lens[i];
      return { i, u, base: V(-ts * u * pw * 0.37, pl * 0.9, -pt * 0.02), segs: [0.44, 0.31, 0.25].map((f) => f * L), r: size * 0.07 * (i === 3 ? 0.86 : i === 0 ? 1.0 : 0.97), tube, pts: [V(), V(), V(), V(), V()] };
    });
    this.thumb = { base: V(ts * pw * 0.34, pl * 0.2, -pt * 0.2), segs: [0.2, 0.19, 0.15].map((f) => f * size), r: size * 0.08, tube: new SweepTube({ material, segments: 8, radial: 8, capRings: 2 }), pts: [V(), V(), V(), V()] };
    this.root.add(this.thumb.tube.mesh);
    this.pose({});
  }
  aim(fingerDir, palmNormal) { return orientYZ(this.root, fingerDir, palmNormal.clone().multiplyScalar(-1)); }
  pose({ curl = 0.15, point = 0, spread = 0.15, thumb = 0.3, cup = 0.1, splay = 0, grip = 0, perFinger = null } = {}) {
    const ts = this.ts, pn = V(0, 0, -1);
    for (const f of this.fingers) {
      let c = perFinger ? perFinger[f.i] : curl;
      c = lerp(c, f.i === 0 ? 0 : 1, point);
      c = lerp(c, 0.55, grip);
      const extra = f.i * 0.04 * c;                                 // pinky side curls a bit more
      const mcp = c * 1.3 + cup * 0.32 - splay * 0.38 + extra;
      const pip = c * 1.6 + cup * 0.12 - splay * 0.12;
      const dip = c * 1.0 + cup * 0.08;
      const fan = ts * f.u * (spread * 0.3 + 0.035);              // rotate +Y toward the pinky side as u grows
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
    // thumb: 0 = alongside the index .. 1 = out; curl/grip/cup swing it across the palm
    const T = this.thumb, P = T.pts;
    const across = clamp(curl * 0.8 + grip * 0.6 + cup * 0.35);
    let d0 = V(ts * lerp(0.35, 0.9, thumb), lerp(0.88, 0.42, thumb), -0.28).normalize();
    d0.lerp(V(-ts * 0.15, 0.55, -0.82), across * 0.6).normalize();
    const bendAx = V(-ts * 0.45, 0, -0.9).normalize();
    const d1 = d0.clone().addScaledVector(bendAx, 0.25 + across * 0.7).normalize();
    const d2 = d1.clone().addScaledVector(bendAx, 0.2 + across * 0.9).normalize();
    P[0].copy(T.base);
    P[1].copy(P[0]).addScaledVector(d0, T.segs[0]);
    P[2].copy(P[1]).addScaledVector(d1, T.segs[1]);
    P[3].copy(P[2]).addScaledVector(d2, T.segs[2]);
    T.tube.update(P, [T.r * 1.25, T.r * 1.02, T.r * 0.95, T.r * 0.85]);
    return this;
  }
}

// ---------------------------------------------------------------------------------------------------------
/**
 * Sleeve — a wide cloth sleeve with REAL thickness: outer surface (shoulder -> cuff), a rolled hem at the cuff that
 * folds inward, and an inner lining surface running back up toward the elbow (lit, darkening with depth via vertex
 * colours). One indexed mesh, two material groups, no back-face tricks, so the cuff reads from every angle.
 *   update(points, radiusFn(s), { hem }) — points: root-space centreline (shoulder .. cuff)
 */
class Sleeve {
  constructor(outerMat, innerMat, { segs = 16, radial = 16, inner = 6, depth = 0.42 } = {}) {
    this.S = segs; this.R = radial; this.NI = inner; this.depth = depth;
    this.rings = segs + 1 + 1 + inner;                         // outer 0..S, lip, inner 1..NI
    const nv = this.rings * radial + 1;
    this.pos = new Float32Array(nv * 3);
    const col = new Float32Array(nv * 3).fill(1);
    for (let k = 0; k <= inner; k++) {
      const c = k === 0 ? 0.95 : lerp(0.82, 0.5, (k - 1) / Math.max(1, inner - 1));
      const r0 = (segs + 1 + k) * radial;
      for (let j = 0; j < radial; j++) col.fill(c, (r0 + j) * 3, (r0 + j) * 3 + 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const outer = [], innerIdx = [];
    for (let r = 0; r < this.rings - 1; r++) for (let j = 0; j < radial; j++) {
      const a = r * radial + j, b = r * radial + ((j + 1) % radial), c = (r + 1) * radial + j, d = (r + 1) * radial + ((j + 1) % radial);
      (r < segs + 1 ? outer : innerIdx).push(a, b, c, b, d, c);
    }
    const tip = this.rings * radial;
    for (let j = 0; j < radial; j++) outer.push(tip, (j + 1) % radial, j);
    g.setIndex([...outer, ...innerIdx]);
    g.addGroup(0, outer.length, 0); g.addGroup(outer.length, innerIdx.length, 1);
    this.geo = g;
    this.mesh = new THREE.Mesh(g, [outerMat, innerMat]);
    this.mesh.frustumCulled = false;
    this.curve = new THREE.CatmullRomCurve3([V(), V(0, 1, 0)], false, 'centripetal');
    this.P = []; this.T = []; this.N = []; this.B = [];
    for (let i = 0; i <= segs; i++) { this.P.push(V()); this.T.push(V()); this.N.push(V()); this.B.push(V()); }
  }
  update(points, rad, { hem = 0.0065 } = {}) {
    const { S, R, NI, P, T, N, B } = this;
    this.curve.points = points;
    for (let i = 0; i <= S; i++) { this.curve.getPointAt(i / S, P[i]); this.curve.getTangentAt(i / S, T[i]).normalize(); }
    const up = Math.abs(T[0].y) < 0.9 ? V(0, 1, 0) : V(1, 0, 0);
    N[0].copy(up).sub(_hu.copy(T[0]).multiplyScalar(up.dot(T[0]))).normalize(); B[0].crossVectors(T[0], N[0]);
    for (let i = 1; i <= S; i++) { N[i].copy(N[i - 1]).sub(_hu.copy(T[i]).multiplyScalar(N[i - 1].dot(T[i]))).normalize(); B[i].crossVectors(T[i], N[i]); }
    const pos = this.pos; let k = 0;
    const ring = (c, n, b, r) => { for (let j = 0; j < R; j++) { const a = (j / R) * Math.PI * 2, x = Math.cos(a) * r, y = Math.sin(a) * r; pos[k++] = c.x + n.x * x + b.x * y; pos[k++] = c.y + n.y * x + b.y * y; pos[k++] = c.z + n.z * x + b.z * y; } };
    for (let i = 0; i <= S; i++) ring(P[i], N[i], B[i], rad(i / S));
    const rE = rad(1);
    ring(_hv.copy(P[S]).addScaledVector(T[S], hem * 0.55), N[S], B[S], rE - hem * 0.5);              // rolled lip
    for (let q = 1; q <= NI; q++) {                                                                      // lining, back up the sleeve
      const sq = 1 - this.depth * Math.pow(q / NI, 1.3) - 0.012, f = sq * S, i0 = Math.min(S - 1, Math.floor(f)), u = f - i0;
      _hv.copy(P[i0]).lerp(P[i0 + 1], u);
      ring(_hv, N[u < 0.5 ? i0 : i0 + 1], B[u < 0.5 ? i0 : i0 + 1], Math.max(0.01, rad(sq) - hem));
    }
    _hv.copy(P[0]).addScaledVector(T[0], -rad(0) * 0.6);
    pos[k++] = _hv.x; pos[k++] = _hv.y; pos[k++] = _hv.z;
    this.geo.attributes.position.needsUpdate = true;
    this.geo.computeVertexNormals();
    return this;
  }
}

// ---------------------------------------------------------------------------------------------------------
class Jesus extends Character {
  constructor() {
    super({ name: 'JESUS', speaker: 'JESUS', height: 1.75, seed: 11 });
    this.Mp = new THREE.Matrix4(); this.Mc = new THREE.Matrix4(); this.Mh = new THREE.Matrix4();
    this.rootInv = new THREE.Matrix4(); this.rootQInv = new THREE.Quaternion();
    this._mats();
    this._skeleton();
    this._buildHead();
    this._buildHair();
    this._buildBeard();
    this._buildRobe();
    this._buildMantle();
    this._buildBelt();
    this._buildArms();
    this._buildLegs();
    this._buildAnchors();
    // draw outer layers first so early-z rejects the skin / robe underneath (opaque sort is by renderOrder, then material)
    const layer = (mats, ro) => this.root.traverse((o) => { if (o.isMesh && (Array.isArray(o.material) ? o.material.some((m) => mats.includes(m)) : mats.includes(o.material))) o.renderOrder = ro; });
    layer([this.hairMat, this.hairShellMat, this.beardMat], -3);
    layer([this.mantleMat, this.sleeveMat, this.ropeMat], -2);
    layer([this.robeMat, this.liningMat], -1);
    this.dartEv = schedule(this.seed * 19 + 7, -4, 3000, 0.3, 0.72);
    this.beatEv = schedule(this.seed * 23 + 5, -4, 3000, 0.32, 0.85);
    this.update(0, {});
  }

  /** metres per walk cycle; move pos at walkSpeed(style) * cycles-per-second */
  walkSpeed(style = 'walk') { return (WALK[style] || WALK.walk).stride; }
  walkRate(style = 'walk') { return (WALK[style] || WALK.walk).rate; }

  // ------------------------------------------------------------------ materials
  _mats() {
    // Perf: everything is MeshStandard + core enhance() (rim / wrap / glow) — no MeshPhysical sheen passes.
    const sk = { rim: 0.42, rimColor: GOLD, wrap: 0.34, wrapColor: 0xff7a58, roughness: 0.5, glow: 0.05 };
    this.headSkin = stdMat(SKIN, { ...sk, jaw: JAW });
    this.bodySkin = stdMat(SKIN, sk);
    const hs = { roughness: 0.7, rim: 0.5, rimColor: 0xffbf70, rimPower: 2.6, glow: 0.07, wrap: 0.2, wrapColor: 0x8a4a28, vertexColors: true };
    this.hairMat = stdMat(0xffffff, hs);
    this.hairShellMat = stdMat(0xffffff, { ...hs, side: THREE.DoubleSide }); this.hairShellMat.shadowSide = THREE.BackSide;
    this.beardMat = stdMat(0x45291a, { roughness: 0.7, rim: 0.42, rimColor: 0xffbf70, rimPower: 2.6, glow: 0.02 });
    const cl = { roughness: 0.92, rim: 0.36, rimColor: 0xffd28c, rimPower: 3.2, glow: 0.035, wrap: 0.25, wrapColor: 0xffe8c8 };
    this.robeMat = stdMat(ROBE_C, cl);
    this.sleeveMat = stdMat(ROBE_C, cl);
    this.liningMat = stdMat(0xb09878, { roughness: 0.95, rim: 0, glow: 0.04, vertexColors: true });   // lit sleeve interior (darkens inward)
    this.mantleMat = stdMat(MANTLE_C, { roughness: 0.85, rim: 0.34, rimColor: 0xffb070, rimPower: 3, glow: 0.04, wrap: 0.3, wrapColor: 0xff8a5c });
    this.ropeMat = stdMat(ROPE_C, { roughness: 0.92, rim: 0.2, rimColor: 0xffd090, glow: 0.03 });
    this.leatherMat = stdMat(LEATHER_C, { roughness: 0.62, rim: 0.2, rimColor: 0xffc080, glow: 0.02 });
    this.creaseMat = new THREE.MeshBasicMaterial({ color: 0x24130b });
    this._rims = [[this.headSkin, 0.42], [this.bodySkin, 0.42], [this.hairMat, 0.5], [this.hairShellMat, 0.5], [this.beardMat, 0.42], [this.robeMat, 0.36], [this.sleeveMat, 0.36], [this.mantleMat, 0.34], [this.ropeMat, 0.2], [this.leatherMat, 0.2]];
  }

  _skeleton() {
    this.pelvisG = new THREE.Group(); this.root.add(this.pelvisG);
    this.chestG = new THREE.Group(); this.pelvisG.add(this.chestG);
    this.neckG = new THREE.Group(); this.chestG.add(this.neckG);
    this.headPivot = new THREE.Group(); this.neckG.add(this.headPivot);
    this.headG = new THREE.Group(); this.headPivot.add(this.headG);
    this.headGroup = this.headG;
    this.chestG.position.y = WAIST_H;
    this.neckG.position.set(0, NECK_BASE, -0.01);
    this.headPivot.position.set(0, NECK_LEN, 0.004);
    this.headG.position.set(0, HEAD_UP, 0); this.headG.scale.setScalar(HEAD_SCALE);
    this.neckG.rotation.order = this.headPivot.rotation.order = 'YXZ';
    this.pelvisG.rotation.order = 'YXZ'; this.chestG.rotation.order = 'YXZ';
  }

  // ------------------------------------------------------------------ head, nose, ears, face
  _buildHead() {
    const g = new THREE.SphereGeometry(1, 60, 44);
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
    // nose: one smooth lofted mesh (bridge -> rounded tip, wings flaring back into the cheeks)
    const nTop = headSurf(0, EYE_V - 0.05).p, nBot = headSurf(0, -0.27).p;
    const ng = new THREE.SphereGeometry(1, 20, 18);
    const NP = ng.attributes.position;
    for (let i = 0; i < NP.count; i++) {
      const xs = NP.getX(i), ys = NP.getY(i), zs = NP.getZ(i);
      const t = (1 - ys) / 2;
      const cy = lerp(nTop.y + 0.006, nBot.y - 0.004, t), cz = lerp(nTop.z - 0.008, nBot.z + 0.007, Math.pow(t, 1.4));
      let W = lerp(0.0078, 0.0128, t) + 0.0068 * smoothstep(0.62, 0.95, t);
      W *= 1 + 0.42 * smoothstep(0.62, 0.95, t) * Math.max(0, -zs);
      const D = lerp(0.006, 0.0185, Math.pow(t, 1.1));
      NP.setXYZ(i, xs * W, cy - 0.0035 * Math.max(0, zs) * smoothstep(0.7, 1, t), cz + zs * D);
    }
    ng.deleteAttribute('normal'); ng.deleteAttribute('uv');
    const ngm = mergeVertices(ng); ngm.computeVertexNormals();
    this.nose = new THREE.Mesh(ngm, this.bodySkin); this.headG.add(this.nose);
    const sph = (r, p, sx = 1, sy = 1, sz = 1) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), this.bodySkin); m.position.copy(p); m.scale.set(sx, sy, sz); this.headG.add(m); return m; };
    // ears (mostly under the hair)
    const ears = [1, -1].map((s) => { const e = sph(0.03, V(s * 0.138, -0.012, -0.012), 0.42, 1.05, 0.72); e.rotation.set(0, s * -0.35, s * 0.08); return e; });
    bake(this.headG, [this.nose, ...ears]);
    this.face = new Face({
      head: this.headG, surface: headSurf, seed: 11,
      eyes: {
        u: EYE_U, v: EYE_V, radius: EYE_R, sink: 0.68, splay: 0.1, lidMaterial: this.bodySkin,
        iris: 0x55301a, iris2: 0xb67a3e, irisR: 0.64, pupilR: 0.25, limbal: 0x1f1209, sclera: 0xf8f1e7,
        lash: 1.55, lowerLash: 0.3, lashColor: 0x1b0f09, lowRelaxed: -0.52, lowRaised: 0.3, upOpen: 0.47, upWide: 0.95, maxYaw: 0.62,
      },
      brows: { color: BROW_C, thickness: 0.0112, lift: 0.002, inner: [0.115, 0.37], mid: [0.32, 0.425], outer: [0.57, 0.375], range: 0.2, flatten: 0.55, profile: [0.95, 1.08, 0.9, 0.42] },
      mouth: {
        v: MOUTH_V, halfW: HW0, line: '#43160f', lineW: HW0 * 0.15, interior: '#2a0a0c', interior2: '#5a1a20', teeth: '#f7f0e4',
        tongue: '#c55a60', lipTintRGB: '168,82,72', blushColor: '235,115,90', blushX: HW0 * 2.3, blushY: HW0 * 1.6,
        drawExtra: (g, p) => this._drawExtra(g, p),
      },
      decal: { uMin: -0.82, uMax: 0.82, vMin: MOUTH_V - 0.3, vMax: EYE_V + 0.1, size: [640, 400] },
      jaw: [this.headSkin.userData.uJaw],
    });
    this._buildCreases();
  }

  // ^^ happy-squeeze creases: an arched dark lid line over each closed eye (rides the upper-lid roll), hidden otherwise
  _buildCreases() {
    this.creases = this.face.eyes.map((eye) => {
      const tube = new SweepTube({ material: this.creaseMat, segments: 16, radial: 6, capRings: 2 });
      tube.mesh.visible = false;
      eye.upRoll.add(tube.mesh);
      const lashes = [...eye.up.children, ...eye.lo.children];
      return { eye, tube, lashes, pts: Array.from({ length: 7 }, () => V()) };
    });
  }
  /** per-frame face tweaks the core rig has no knob for (happy squeeze: lower lid up harder, flatter closed lids) */
  _faceExtras(fp) {
    const hap = smoothstep(0.34, 0.08, fp.lidU ?? 1) * smoothstep(0.45, 0.85, fp.mSmile ?? 0);
    this._hap = hap;
    this.face.cfg.eyes.lowRaised = 0.3 + 0.12 * hap;
    for (const e of this.face.eyes) e.inner.scale.set(1 + 0.05 * hap, 1 - 0.04 * hap, 1 - 0.16 * hap);
    // the core decal only redraws on mouth changes; the cheek bunching / crow's feet depend on the lids too
    const key = hap.toFixed(3) + ',' + clamp(fp.lidL ?? 0).toFixed(3) + ',' + clamp(fp.lidSad ?? 0).toFixed(2);
    if (key !== this._xKey) { this._xKey = key; this.face._lastKey = ''; }
  }
  _updateCreases(fp) {
    const hap = this._hap || 0;
    for (const C of this.creases) {
      const vis = hap > 0.02;
      C.tube.mesh.visible = vis;
      for (const l of C.lashes) l.visible = hap < 0.55;
      if (!vis) continue;
      const up = -C.eye.up.rotation.x, low = -C.eye.lo.rotation.x, ec = Math.max(up, low + 0.02) + 0.02;
      const R = EYE_R * 1.085;
      for (let k = 0; k < 7; k++) {
        const a = lerp(-0.86, 0.86, k / 6), e = ec + 0.05 - 0.78 * (a / 0.86) ** 2;
        C.pts[k].set(R * Math.sin(a) * Math.cos(e), R * Math.sin(e), R * Math.cos(a) * Math.cos(e));
      }
      C.tube.update(C.pts, (s) => EYE_R * 0.09 * hap * (0.4 + 0.6 * Math.sin(Math.PI * s)));
    }
  }

  // lips, laugh lines, smile crinkles, cheek bunching under squeezed eyes — painted into the face decal
  _drawExtra(g, p) {
    const m = mouthGeom(p);
    const xr = -m.w + m.shift, xl = m.w + m.shift;
    g.save();
    // lower lip (fuller), just under the mouth line / opening
    const lw = m.w * 0.64, ly = m.bot - HW0 * (m.open ? 0.21 : 0.25);
    let gr = g.createRadialGradient(m.shift, ly, 0, m.shift, ly, lw);
    gr.addColorStop(0, `rgba(184,84,76,${0.74 - 0.22 * m.press})`); gr.addColorStop(0.65, `rgba(184,84,76,${0.4 - 0.12 * m.press})`); gr.addColorStop(1, 'rgba(184,84,76,0)');
    g.fillStyle = gr; g.beginPath(); g.ellipse(m.shift, ly, lw, HW0 * 0.21, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(255,220,204,0.24)'; g.beginPath(); g.ellipse(m.shift - HW0 * 0.1, ly + HW0 * 0.035, lw * 0.42, HW0 * 0.06, 0, 0, Math.PI * 2); g.fill();
    // upper lip: a visible rosy band with a soft cupid's bow
    const uy = m.top + HW0 * 0.14;
    g.fillStyle = `rgba(170,74,68,${0.56 - 0.18 * m.press})`;
    for (const sx of [-1, 1]) { g.beginPath(); g.ellipse(m.shift + sx * m.w * 0.31, uy + (sx > 0 ? m.yL - m.cm : m.yR - m.cm) * 0.25, m.w * 0.44, HW0 * 0.1, sx * -0.12, 0, Math.PI * 2); g.fill(); }
    const d = this.face.decal;
    const hap = this._hap || 0, lidL = clamp(p.lidL ?? 0);
    // nasolabial laugh lines (upper part peeks above the beard) and eye crinkles when smiling
    const sm = Math.max(smoothstep(0.3, 0.95, p.mSmile), hap);
    g.lineCap = 'round';
    if (sm > 0.01) {
      g.strokeStyle = `rgba(118,58,38,${0.13 * sm})`; g.lineWidth = 0.002;
      for (const s of [-1, 1]) {
        const x0 = s * 0.16 * d.rxEff, y0 = (-0.25 - MOUTH_V) * d.ryEff, x1 = s * 0.27 * d.rxEff, y1 = (-0.33 - MOUTH_V) * d.ryEff;
        g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(x1 + s * 0.006, (y0 + y1) / 2 + 0.004, x1, y1); g.stroke();
      }
      // crow's feet: three lines fanning from the outer corner (stronger in a squeeze)
      const cf = Math.max(0.3 * sm, hap);
      g.strokeStyle = `rgba(104,50,32,${0.42 * cf})`; g.lineWidth = 0.0018 + 0.0007 * hap;
      const ey = (EYE_V - MOUTH_V) * d.ryEff;
      for (const s of [-1, 1]) {
        const xc = s * (EYE_U + 0.27) * d.rxEff;
        for (const [dy, len, bend] of [[0.004, 0.009, 0.002], [-0.002, 0.011, 0], [-0.008, 0.009, -0.0022]]) {
          g.beginPath(); g.moveTo(xc, ey + dy * 0.4); g.quadraticCurveTo(xc + s * len * 0.6, ey + dy + bend, xc + s * len, ey + dy * 1.7); g.stroke();
        }
      }
    }
    // cheek bunching: the lower lid / cheek pushed up — a soft crease arc under each eye + a warm lit cheek apple
    const cb = Math.max(hap, 0.55 * smoothstep(0.35, 1, lidL) * smoothstep(0.3, 0.9, p.mSmile));
    if (cb > 0.01) {
      const ey = (EYE_V - MOUTH_V) * d.ryEff - EYE_R * 0.98;
      for (const s of [-1, 1]) {
        const xc = s * EYE_U * d.rxEff * 1.02;
        g.strokeStyle = `rgba(112,52,34,${0.34 * cb})`; g.lineWidth = 0.0022;
        g.beginPath(); g.moveTo(xc - s * EYE_R * 0.75, ey + 0.004); g.quadraticCurveTo(xc + s * 0.004, ey - 0.0085, xc + s * EYE_R * 0.95, ey + 0.002); g.stroke();
        const ag = g.createRadialGradient(xc + s * 0.004, ey - 0.016, 0, xc + s * 0.004, ey - 0.016, 0.022);
        ag.addColorStop(0, `rgba(255,190,160,${0.22 * cb})`); ag.addColorStop(1, 'rgba(255,190,160,0)');
        g.fillStyle = ag; g.beginPath(); g.ellipse(xc + s * 0.004, ey - 0.016, 0.024, 0.016, 0, 0, Math.PI * 2); g.fill();
      }
    }
    g.restore();
  }

  // ------------------------------------------------------------------ hair: sculpted shell + fat seated locks
  _buildHair() {
    // One continuous sculpted shell: static rows hug the skull (middle part, flow grooves, swept temple masses),
    // dynamic rows hang from the temples / sides / back to the shoulders as 7 distinct locks (S-wave lobes, groove
    // between locks, pointed tapered tips rolled inward). Collides with the shoulders, the mantle and the raised
    // upper arms. Vertex colours give darker roots, a soft sheen band and lighter tips (no plastic gloss).
    const J = this.hJ = 72, H = this.hH = 9, K = this.hK = 17, R = this.hR = H + 1 + K + 1;
    this.hPos = new Float32Array(J * R * 3);
    const col = new Float32Array(J * R * 3), base = new THREE.Color(HAIR_C);
    this.hCols = [];
    const at = (j, r) => (j * R + r) * 3;
    const setCol = (j, r, k) => { const o = at(j, r); col[o] = base.r * k; col[o + 1] = base.g * k * 0.97; col[o + 2] = base.b * k * 0.93; };
    for (let j = 0; j < J; j++) {
      const u = -Math.PI + (j / J) * 2 * Math.PI, vh = hairline(u), au = Math.abs(u);
      const cw = smoothstep(0.84, 1.22, au);
      const vHang = cw > 0 ? Math.max(vh, -0.5) : vh - 0.03;
      const L = lockOf(u);
      for (let k = 0; k <= K; k++) {
        const v = lerp(vHang, Math.PI / 2 - 1e-3, Math.pow(k / K, 0.9));
        const { p, n } = headSurf(u, v);
        p.addScaledVector(n, hairThick(u, v, vh, p, cw));
        this.hPos.set([p.x, p.y, p.z], at(j, H + 1 + k));
        // roots darker toward the part, a soft sheen band around the crown, grooves darker / lock crowns lighter
        const band = Math.exp(-(((v - 1.02) / 0.16) ** 2)) * (0.6 + 0.4 * Math.max(0, Math.cos(u)));
        const groove = lerp(1, 0.86 + 0.2 * L.c, smoothstep(-0.2, -0.7, Math.cos(u)) * smoothstep(0.6, 0.1, v));
        const fr = Math.sin(Math.atan2(p.z, p.y) * 7 + 0.9) * smoothstep(-0.2, 0.4, Math.cos(u)) * smoothstep(0.1, 0.5, v - vh);
        setCol(j, H + 1 + k, (0.88 + 0.42 * band - 0.12 * smoothstep(1.25, 1.5, v)) * groove * (1 + 0.1 * fr));
      }
      const A = V(...this.hPos.slice(at(j, H + 1), at(j, H + 1) + 3)), above = V(...this.hPos.slice(at(j, H + 2), at(j, H + 2) + 3));
      const down = A.clone().sub(above).normalize();
      const d = V(Math.sin(u), 0, Math.cos(u)), back = Math.max(0, -Math.cos(u));
      // pointed lock tips (notches between locks), per-lock length variation
      const tipDrop = 0.03 * (1 - Math.pow(Math.abs(2 * L.f - 1), 1.7)) + 0.012 * (hash1(L.id * 7 + (u < 0 ? 3 : 0)) - 0.5);
      const yTip = -0.205 - 0.018 * back - tipDrop * smoothstep(0.95, 1.3, au);
      const RA = Math.hypot(A.x, A.z);
      const tipFull = d.clone().multiplyScalar(RA + lerp(-0.008, 0.022, smoothstep(1.0, 1.7, au)) + 0.008 * L.c).setY(yTip);
      const tip = A.clone().lerp(tipFull, cw);
      const c1 = A.clone().addScaledVector(down, 0.065 * cw), c2 = tip.clone().add(V(0, 0.09 * cw, 0)).addScaledVector(d, -0.004 * cw);
      const rest = [];
      for (let i = 1; i <= H; i++) {
        const sb = (i - 1) / H, m = 1 - sb;              // Bezier from the tip (sb=0) toward A
        const pnt = tip.clone().multiplyScalar(m * m * m).addScaledVector(c2, 3 * m * m * sb).addScaledVector(c1, 3 * m * sb * sb).addScaledVector(A, sb * sb * sb);
        // S-wave lobes (each lock its own phase) + lock bulge (grooves between locks)
        const env = smoothstep(1.0, 0.55, sb) * cw;
        pnt.addScaledVector(d, (0.011 * Math.sin(sb * Math.PI * 2.3 + L.ph) + 0.014 * L.c - 0.004) * env);
        rest.push(pnt);
        const band = Math.exp(-(((sb - 0.62) / 0.14) ** 2));
        setCol(j, i, (0.9 + 0.14 * L.c + 0.2 * band * L.c + 0.16 * smoothstep(0.25, 0, sb)) * lerp(1, 0.85, 1 - L.c));
      }
      setCol(j, 0, 0.62);
      this.hCols.push({ u, cw, A, d, rest, L });
    }
    const hang = [], cap = [];
    for (let j = 0; j < J; j++) for (let r = 0; r < R - 1; r++) {
      const a = j * R + r, b = ((j + 1) % J) * R + r, c = a + 1, e = b + 1;
      (r < H + 1 ? hang : cap).push(a, b, c, b, e, c);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.hPos, 3).setUsage(THREE.DynamicDrawUsage)); g.setIndex([...hang, ...cap]);
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.addGroup(0, hang.length, 0); g.addGroup(hang.length, cap.length, 1);
    this.hairShell = new THREE.Mesh(g, [this.hairShellMat, this.hairMat]); this.hairShell.castShadow = true; this.hairShell.frustumCulled = false;
    this.headG.add(this.hairShell);
  }

  _updateHair(t, shrug) {
    this.headG.updateWorldMatrix(true, false);
    const q = new THREE.Quaternion(); this.headG.matrixWorld.decompose(_hw, q, _hu);
    const gd = V(0, -1, 0).applyQuaternion(q.invert());
    const qg = new THREE.Quaternion().setFromUnitVectors(V(0, -1, 0), gd), id = new THREE.Quaternion(), qk = new THREE.Quaternion();
    const chestInv = new THREE.Matrix4().copy(this.chestG.matrixWorld).invert();
    const Mhc = chestInv.clone().multiply(this.headG.matrixWorld);
    const Mch = Mhc.clone().invert();
    // raised upper arms (shoulder -> elbow capsules incl. the sleeve) in chest space
    const caps = ['L', 'R'].map((sd) => {
      const A = this.arms[sd];
      return { a: A.shoulderIn.clone().applyMatrix4(chestInv), b: A.elbow.clone().applyMatrix4(chestInv), r: 0.082 };
    });
    const J = this.hJ, H = this.hH, R = this.hR, P = this.hPos, tmp = V(), p = V(), cp = V(), ab = V();
    const sway = 0.0025 * noise1(t * 0.55, 3);
    for (let j = 0; j < J; j++) {
      const C = this.hCols[j];
      for (let i = 1; i <= H; i++) {
        const sb = (i - 1) / H;
        p.copy(C.rest[i - 1]);
        if (C.cw > 0.01) {
          qk.copy(id).slerp(qg, 0.85 * (1 - sb));
          p.sub(C.A).applyQuaternion(qk).add(C.A);
          p.x += sway * (1 - sb) * C.cw;
          tmp.copy(p).applyMatrix4(Mhc);
          let moved = false;
          // rest on the shoulders / back (+ the mantle band over the left shoulder); smooth radial-vs-up blend
          const yr = tmp.y + CHEST_Y0, top = torsoTopY(tmp.x, tmp.z);
          if (top != null) {
            const lift = shrug * 0.055 * shoulderBand(tmp.x, top) + 0.016 + 0.024 * smoothstep(0.05, 0.11, tmp.x) * smoothstep(1.2, 1.3, top);
            if (yr < top + lift) {
              const dy = top + lift - yr;
              const [, rx, rz, , zo] = profileAt(yr);
              const qn = Math.hypot(tmp.x / rx, (tmp.z - zo) / rz);
              const dr = (1.07 - qn) * Math.min(rx, rz);
              const w = qn > 0.5 ? smoothstep(0.012, -0.012, dr - dy) : 0;     // 1 = radial push is cheaper
              const f = 1.07 / Math.max(qn, 1e-3);
              const rx2 = tmp.x * f, rz2 = zo + (tmp.z - zo) * f;
              tmp.set(lerp(tmp.x, rx2, w), tmp.y + dy * (1 - w), lerp(tmp.z, rz2, w));
              moved = true;
            }
          }
          // upper arms / sleeve roots: push the curtain outward over them
          for (const c of caps) {
            ab.copy(c.b).sub(c.a);
            const f = clamp(cp.copy(tmp).sub(c.a).dot(ab) / Math.max(1e-6, ab.lengthSq()));
            cp.copy(c.a).addScaledVector(ab, f);
            const dd = tmp.distanceTo(cp);
            if (dd < c.r) { tmp.sub(cp).multiplyScalar(c.r / Math.max(dd, 1e-4)).add(cp); moved = true; }
          }
          if (moved) p.copy(tmp.applyMatrix4(Mch));
        }
        const o = (j * R + i) * 3; P[o] = p.x; P[o + 1] = p.y; P[o + 2] = p.z;
        if (i === 1) { // rolled tip
          const o0 = j * R * 3;
          P[o0] = p.x - C.d.x * 0.016 * C.cw; P[o0 + 1] = p.y + 0.012 * C.cw; P[o0 + 2] = p.z - C.d.z * 0.016 * C.cw;
        }
      }
    }
    const geo = this.hairShell.geometry;
    geo.attributes.position.needsUpdate = true; geo.computeVertexNormals();
  }

  // ------------------------------------------------------------------ beard shell with live mouth opening
  _buildBeard() {
    // grid denser around the mouth (u near 0, v near the mouth); vertices next to the static contour are snapped
    // ONTO it at build time and vertices next to the live lip-hole contour are snapped onto it every frame, so the
    // beard edge is a clean curve instead of grid stair-steps.
    const NU = this.bNU = 84, NV = this.bNV = 50, U1 = 1.62, V0 = -1.42, V1 = 0.16;
    const n = (NU + 1) * (NV + 1);
    const ym = (() => { const target = (MOUTH_V - V0) / (V1 - V0); let y = target; for (let i = 0; i < 40; i++) y = target + 0.55 * Math.sin(2 * Math.PI * y) / (2 * Math.PI); return y; })();
    const gv = (y) => y - 0.55 * (Math.sin(2 * Math.PI * (y - ym)) + Math.sin(2 * Math.PI * ym)) / (2 * Math.PI);
    const gu = (x) => U1 * (x * 0.42 + 0.58 * x * x * x);
    this.bBase = new Float32Array(n * 3); this.bN = new Float32Array(n * 3);
    this.bT0 = new Float32Array(n); this.bX = new Float32Array(n); this.bY = new Float32Array(n); this.bU = new Float32Array(n); this.bV = new Float32Array(n); this.bTv = new Float32Array(n * 3);
    const d = this.face.decal, idx = [];
    this.rxEff = d.rxEff; this.ryEff = d.ryEff;
    const eps = 1e-3;
    for (let j = 0; j <= NV; j++) for (let i = 0; i <= NU; i++) {
      const k = j * (NU + 1) + i;
      let u = gu(i / NU * 2 - 1), v = V0 + (V1 - V0) * gv(j / NV);
      let T0 = beardStatic(u, v);
      // snap the first ring OUTSIDE the static contour onto it (Newton on beardEdge = 0)
      const e = beardEdge(u, v);
      if (e < 0 && e > -0.55) {
        for (let it = 0; it < 3; it++) {
          const ee = beardEdge(u, v), gx = (beardEdge(u + eps, v) - beardEdge(u - eps, v)) / (2 * eps), gy = (beardEdge(u, v + eps) - beardEdge(u, v - eps)) / (2 * eps);
          const g2 = gx * gx + gy * gy; if (g2 < 1e-9) break;
          u -= ee * gx / g2; v -= ee * gy / g2;
        }
        u = clamp(u, -U1, U1);
        T0 = 0.0004;
      }
      const { p, n: nn } = headSurf(u, v);
      const pv = headPoint(u, v + 0.01).sub(headPoint(u, v - 0.01)).multiplyScalar(1 / (0.02 * d.ryEff));   // d(pos)/d(decal Y)
      this.bTv.set([pv.x, pv.y, pv.z], k * 3);
      this.bBase.set([p.x, p.y, p.z], k * 3); this.bN.set([nn.x, nn.y, nn.z], k * 3);
      this.bT0[k] = T0; this.bX[k] = u * d.rxEff; this.bY[k] = (v - MOUTH_V) * d.ryEff; this.bU[k] = u; this.bV[k] = v;
    }
    for (let j = 0; j < NV; j++) for (let i = 0; i < NU; i++) {
      const a = j * (NU + 1) + i, b = a + 1, c = a + NU + 1, e = c + 1;
      if (this.bT0[a] < -0.0044 && this.bT0[b] < -0.0044 && this.bT0[c] < -0.0044 && this.bT0[e] < -0.0044) continue;   // fully outside: skip
      idx.push(a, b, c, b, e, c);
    }
    const g = new THREE.BufferGeometry();
    this.bPos = new Float32Array(n * 3);
    g.setAttribute('position', new THREE.BufferAttribute(this.bPos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setIndex(idx);
    this.beard = new THREE.Mesh(g, this.beardMat);
    this.headG.add(this.beard);
    this._beardKey = '';
  }

  _updateBeard(fp) {
    const g = mouthGeom(fp), jaw = this.headSkin.userData.uJaw.value;
    const key = [g.w, g.shift, g.yL, g.yR, g.top, g.bot, g.round, jaw].map((x) => x.toFixed(4)).join(',');
    if (key === this._beardKey) return;
    this._beardKey = key;
    const B = this.bBase, N = this.bN, P = this.bPos, rxE = this.rxEff, ryE = this.ryEff;
    const eps = 0.0004, band = 0.0042, hs = { p: null, n: null };
    const TV = this.bTv;
    // the mustache rides the upper lip: corners up in a smile -> the mustache curves up with them (no "toothbrush" patch)
    const lipLift = (X) => {
      const tx = (X - g.shift) / g.w, at = Math.abs(tx), sx = at < 1 ? 1 - at * at : 0;
      const yc = lerp(g.yR, g.yL, clamp((tx + 1) / 2));
      return (yc + (g.top - g.cm) * sx) * Math.exp(-(Math.max(0, at - 1) ** 2) / 0.3);
    };
    for (let k = 0; k < this.bT0.length; k++) {
      let x = B[k * 3], y0 = B[k * 3 + 1], z = B[k * 3 + 2], nx = N[k * 3], ny = N[k * 3 + 1], nz = N[k * 3 + 2];
      const jw = jaw * (1 - smoothstep(JAW.y - JAW.soft, JAW.y + JAW.soft, y0));
      let T = this.bT0[k];
      if (T > -0.0044) {
        const X = this.bX[k];
        let Y = this.bY[k] - jw * JAW.drop;
        const up = smoothstep(-0.006, 0.006, this.bY[k]) * (1 - 0.6 * smoothstep(0.004, 0.04, this.bY[k]));
        if (up > 0.001) {
          const dY = lipLift(X) * up;
          if (Math.abs(dY) > 2e-4) { Y += dY; x += TV[k * 3] * dY; y0 += TV[k * 3 + 1] * dY; z += TV[k * 3 + 2] * dY; }
        }
        const dd = lipHoleDist(X, Y, g);
        if (dd < 0 && dd > -band) {
          // first ring inside the opening: snap onto the lip-hole contour -> a smooth edge
          let x2 = X, y2 = Y;
          for (let it = 0; it < 2; it++) {
            const e0 = lipHoleDist(x2, y2, g), gx = (lipHoleDist(x2 + eps, y2, g) - lipHoleDist(x2 - eps, y2, g)) / (2 * eps), gy = (lipHoleDist(x2, y2 + eps, g) - lipHoleDist(x2, y2 - eps, g)) / (2 * eps);
            const g2 = gx * gx + gy * gy; if (g2 < 1e-8) break;
            x2 -= e0 * gx / g2; y2 -= e0 * gy / g2;
          }
          const sp = headSurf(x2 / rxE, (y2 + jw * JAW.drop) / ryE + MOUTH_V);
          x = sp.p.x; y0 = sp.p.y; z = sp.p.z; nx = sp.n.x; ny = sp.n.y; nz = sp.n.z;
          T = 0.0006;
        } else T = lerp(-0.0045, T, rounded(dd / 0.0058));
      }
      P[k * 3] = x + nx * T;
      P[k * 3 + 1] = y0 + ny * T - jw * JAW.drop;
      P[k * 3 + 2] = z + nz * T - jw * JAW.back;
    }
    const geo = this.beard.geometry;
    geo.attributes.position.needsUpdate = true;
    geo.computeVertexNormals(); geo.computeBoundingSphere();
  }

  // ------------------------------------------------------------------ robe (lathe + drape solver)
  _buildRobe() {
    const J = this.RJ = 40, SI = this.SI = 18, NT = ROBE_TOP.length;
    this.NT = NT; this.RR = NT + SI + 1 + 2;
    const R = this.RR;
    this.robePos = new Float32Array(R * J * 3);
    // upper rows rest (root-local) + chest weight
    this.topRest = [];
    for (let r = 0; r < NT; r++) {
      const [y, rx, rz, n, zo] = ROBE_TOP[r];
      for (let j = 0; j < J; j++) {
        const th = (j / J) * Math.PI * 2;
        const [x, z] = sePoint(th, rx, rz, n, zo);
        const fold = 1 + 0.012 * Math.sin(th * 5 + 0.7) * smoothstep(1.3, 1.1, y);
        this.topRest.push(V(x * fold, y, z * fold));
      }
    }
    this.topW = ROBE_TOP.map(([y]) => smoothstep(1.03, 1.14, y));
    // skirt rest (pelvis-local, relative to (0, HIP_Y, 0)) with pleats deepening toward the hem
    this.skRest = []; this.skStep = []; this.skLen = [];
    for (let i = 0; i <= SI; i++) {
      const s = i / SI, y = lerp(SKIRT_TOP, HEM_Y, s) - HIP_Y;
      const [rx, rz, n, zo] = skirtR(s);
      const row = [];
      for (let j = 0; j < J; j++) {
        const th = (j / J) * Math.PI * 2;
        const pl = 1 + s * (0.034 * Math.sin(th * 7 + 0.5) + 0.02 * Math.sin(th * 11 + 1.3));
        const [x, z] = sePoint(th, rx * pl, rz * pl, n, zo);
        row.push(V(x, y, z));
      }
      this.skRest.push(row);
      if (i > 0) { this.skStep.push(row.map((p, j) => p.clone().sub(this.skRest[i - 1][j]))); this.skLen.push(row.map((p, j) => p.distanceTo(this.skRest[i - 1][j]))); }
      else { this.skStep.push(null); this.skLen.push(null); }
    }
    this.swingW = []; for (let i = 0; i <= SI; i++) this.swingW.push(i === 0 ? 0 : (i / SI) ** 1.6 - ((i - 1) / SI) ** 1.6);
    const idx = [];
    for (let r = 0; r < R - 1; r++) for (let j = 0; j < J; j++) {
      const a = r * J + j, b = r * J + ((j + 1) % J), c = (r + 1) * J + j, d = (r + 1) * J + ((j + 1) % J);
      idx.push(a, c, b, b, c, d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.robePos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setIndex(idx);
    this.robe = new THREE.Mesh(g, this.robeMat); this.robe.castShadow = true; this.robe.receiveShadow = true;
    this.robe.frustumCulled = false;
    this.root.add(this.robe);
    this._q = V(); this._p = V(); this._t = V(); this._c = V();
  }

  _collide(q, i, caps, pc, yaw, rdx = 0, rdz = 0) {
    for (let c = 0; c < caps.length; c++) {
      const C = caps[c];
      const abx = C.b.x - C.a.x, aby = C.b.y - C.a.y, abz = C.b.z - C.a.z;
      const L2 = abx * abx + aby * aby + abz * abz;
      let f = L2 > 1e-9 ? ((q.x - C.a.x) * abx + (q.y - C.a.y) * aby + (q.z - C.a.z) * abz) / L2 : 0;
      const capEnd = f < 0 || f > 1;
      f = clamp(f);
      const cx = C.a.x + abx * f, cy = C.a.y + aby * f, cz = C.a.z + abz * f;
      let dx = q.x - cx, dy = q.y - cy, dz = q.z - cz;
      const r = lerp(C.ra, C.rb, f) + 0.013;
      const d2 = dx * dx + dy * dy + dz * dz;
      if (d2 < r * r) {
        // exit along the column's outward direction so the cloth always wraps the leg from the OUTSIDE
        // (or upward when the bone points along that direction, e.g. a forward thigh when kneeling)
        let done = false;
        const L = Math.sqrt(L2), ax = L > 1e-5 ? abx / L : 0, ay = L > 1e-5 ? aby / L : 1, az = L > 1e-5 ? abz / L : 0;
        for (let pass = 0; pass < 2 && !done && (rdx || rdz); pass++) {
          const ex = pass ? 0 : rdx, ey = pass ? 1 : 0, ez = pass ? 0 : rdz;
          let px = ex, py = ey, pz = ez;
          if (!capEnd) { const k = px * ax + py * ay + pz * az; px -= k * ax; py -= k * ay; pz -= k * az; }
          const A = px * px + py * py + pz * pz;
          if (A > 0.08) {
            const B = 2 * (dx * px + dy * py + dz * pz), Cc = d2 - r * r;
            const lam = (-B + Math.sqrt(Math.max(0, B * B - 4 * A * Cc))) / (2 * A);
            if (lam < 0.35) { q.x += ex * lam; q.y += ey * lam; q.z += ez * lam; done = true; }
          }
        }
        if (!done) {
          let d = Math.sqrt(d2);
          if (d < 1e-5) { dx = q.x - pc.x; dy = 0; dz = q.z - pc.z; d = Math.hypot(dx, dz) || 1; }
          const k = r / d; q.set(cx + dx * k, cy + dy * k, cz + dz * k);
        }
      }
    }
    if (i <= 9) { // hips (pelvis-centred ellipsoid, yaw-aligned)
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const lx0 = q.x - pc.x, ly = q.y - pc.y, lz0 = q.z - pc.z;
      const lx = lx0 * cy - lz0 * sy, lz = lx0 * sy + lz0 * cy;
      const e = (lx / 0.192) ** 2 + (ly / 0.2) ** 2 + (lz / 0.158) ** 2;
      if (e < 1) { const k = 1 / Math.sqrt(e); q.set(pc.x + lx0 * k, pc.y + ly * k, pc.z + lz0 * k); }
    }
    if (q.y < FLOOR) {
      const ex = FLOOR - q.y; q.y = FLOOR;
      const hx = q.x - pc.x, hz = q.z - pc.z, h = Math.hypot(hx, hz) || 1;
      q.x += (hx / h) * ex * 1.25; q.z += (hz / h) * ex * 1.25;
    }
  }

  _updateRobe(ctx) {
    const { br, shrug, hunch, caps, pc, yaw, swing, knees } = ctx;
    const drop = clamp((HIP_Y - pc.y) / 0.8), ky0 = lerp(1, 0.35, Math.pow(drop, 0.85));   // fabric bunches when the hips drop
    // ...except over a raised knee (the cloth must travel over the thigh and down the shin)
    const J = this.RJ, NT = this.NT, SI = this.SI, P = this.robePos;
    const Mc = this.Mc, Mp = this.Mp, a = V(), b = V();
    // upper body: chest/pelvis blended rigid skin + breathing + shrug
    for (let r = 0; r < NT; r++) {
      const w = this.topW[r];
      for (let j = 0; j < J; j++) {
        const rp = this.topRest[r * J + j];
        const band = smoothstep(1.06, 1.18, rp.y) * smoothstep(1.36, 1.24, rp.y);
        const kx = 1 + 0.02 * br * band, kz = 1 + 0.03 * br * band;
        a.set(rp.x * kx, rp.y - CHEST_Y0 + shrug * 0.055 * shoulderBand(rp.x, rp.y) + 0.004 * br * smoothstep(1.2, 1.32, rp.y),
          rp.z * kz + hunch * 0.03 * shoulderBand(rp.x, rp.y));
        this._protAdd(a, rp.x, rp.y, rp.z).applyMatrix4(Mc);
        if (w < 1) { b.set(rp.x, rp.y - HIP_Y, rp.z).applyMatrix4(Mp); a.lerp(b, 1 - w); }
        const o = (r * J + j) * 3; P[o] = a.x; P[o + 1] = a.y; P[o + 2] = a.z;
      }
    }
    // skirt: march each column down from the waist, colliding with legs / hips / floor
    const cyw = Math.cos(yaw), syw = Math.sin(yaw);
    const p = this._p, q = this._q, hp = this._t;
    const rowOf = (i) => (NT + i) * J;
    const FH = this._free || (this._free = new Float32Array((SI + 1) * J * 3));   // free-hanging solution
    for (let j = 0; j < J; j++) {
      p.copy(this.skRest[0][j]).applyMatrix4(Mp);
      const th = (j / J) * Math.PI * 2, rdx = Math.sin(th) * cyw + Math.cos(th) * syw, rdz = -Math.sin(th) * syw + Math.cos(th) * cyw;
      let fr = 0;
      for (const kn of knees) { const hx = kn.x - pc.x, hz = kn.z - pc.z, h = Math.hypot(hx, hz); if (h > 0.12 && kn.y > 0.25) fr = Math.max(fr, Math.pow(Math.max(0, (rdx * hx + rdz * hz) / h), 3) * smoothstep(0.12, 0.3, h)); }
      const ky = lerp(ky0, 1.04, fr);
      let o = (rowOf(0) + j) * 3; P[o] = p.x; P[o + 1] = p.y; P[o + 2] = p.z;
      hp.copy(p);
      for (let i = 1; i <= SI; i++) {
        const st = this.skStep[i][j], sw = this.swingW[i];
        const sy = st.y * ky, len = Math.sqrt(st.x * st.x + st.z * st.z + sy * sy);
        q.set(st.x * cyw + st.z * syw + swing.x * sw, sy, -st.x * syw + st.z * cyw + swing.z * sw);
        hp.add(q); if (hp.y < FLOOR) hp.y = FLOOR;
        FH[(i * J + j) * 3] = hp.x; FH[(i * J + j) * 3 + 1] = hp.y; FH[(i * J + j) * 3 + 2] = hp.z;
        q.add(p);
        this._collide(q, i, caps, pc, yaw, rdx, rdz);
        q.sub(p).setLength(len).add(p);
        this._collide(q, i, caps, pc, yaw, rdx, rdz);
        p.copy(q);
        o = (rowOf(i) + j) * 3; P[o] = p.x; P[o + 1] = p.y; P[o + 2] = p.z;
      }
    }
    // tenting: diffuse the collision displacement (vs. the free hang) across columns, then re-collide
    const tmp = this._tmpRow || (this._tmpRow = new Float32Array(J * 3)), Dd = this._dRow || (this._dRow = new Float32Array(J * 3));
    for (let i = 2; i <= SI; i++) {
      const base = rowOf(i) * 3;
      for (let j = 0; j < J; j++) for (let c = 0; c < 3; c++) Dd[j * 3 + c] = P[base + j * 3 + c] - FH[(i * J + j) * 3 + c];
      for (let pass = 0; pass < 7; pass++) {
        for (let j = 0; j < J; j++) {
          const jm = ((j + J - 1) % J) * 3, jp = ((j + 1) % J) * 3;
          for (let c = 0; c < 3; c++) tmp[j * 3 + c] = 0.5 * Dd[j * 3 + c] + 0.25 * (Dd[jm + c] + Dd[jp + c]);
        }
        for (let j = 0; j < J; j++) for (let c = 0; c < 3; c++) { const a = Dd[j * 3 + c], b = tmp[j * 3 + c]; Dd[j * 3 + c] = Math.abs(b) > Math.abs(a) ? b : a; }
      }
      for (let j = 0; j < J; j++) for (let c = 0; c < 3; c++) tmp[j * 3 + c] = FH[(i * J + j) * 3 + c] + Dd[j * 3 + c];
      {
        for (let j = 0; j < J; j++) {
          q.set(tmp[j * 3], tmp[j * 3 + 1], tmp[j * 3 + 2]);
          const th = (j / J) * Math.PI * 2;
          this._collide(q, i, caps, pc, yaw, Math.sin(th) * cyw + Math.cos(th) * syw, -Math.sin(th) * syw + Math.cos(th) * cyw);
          const o0 = base + j * 3; P[o0] = q.x; P[o0 + 1] = q.y; P[o0 + 2] = q.z;
        }
      }
    }
    // hem roll (two rows folding inward/up so the hem has thickness)
    for (let j = 0; j < J; j++) {
      const oh = (rowOf(SI) + j) * 3;
      const hx = P[oh], hy = P[oh + 1], hz = P[oh + 2];
      let ix = pc.x - hx, iz = pc.z - hz; const il = Math.hypot(ix, iz) || 1; ix /= il; iz /= il;
      let o = (rowOf(SI + 1) + j) * 3; P[o] = hx + ix * 0.011; P[o + 1] = hy + 0.007; P[o + 2] = hz + iz * 0.011;
      o = (rowOf(SI + 2) + j) * 3; P[o] = hx + ix * 0.018; P[o + 1] = hy + 0.04; P[o + 2] = hz + iz * 0.018;
    }
    const geo = this.robe.geometry;
    geo.attributes.position.needsUpdate = true;
    geo.computeVertexNormals();
  }
  /** skirt vertex (root-local) at row i (0 = waist .. SI = hem), column angle th (rad from +Z toward +X) */
  skirtPoint(i, th, out = V()) {
    const J = this.RJ, j = ((Math.round((th / (Math.PI * 2)) * J) % J) + J) % J;
    const o = ((this.NT + i) * J + j) * 3;
    return out.set(this.robePos[o], this.robePos[o + 1], this.robePos[o + 2]);
  }

  /** add both shoulders' protraction displacement (chest space) to chest-space point a, given root-rest coords */
  _protAdd(a, x, y, z) {
    const L = this.arms.L.protC, R = this.arms.R.protC;
    if (L.lengthSq() + R.lengthSq() < 1e-10) return a;
    const wl = protW(x, y, z, 1), wr = protW(x, y, z, -1);
    return a.addScaledVector(L, wl).addScaledVector(R, wr);
  }
  /** horizontal radius (from the pelvis axis pc) of the draped skirt at height y in the column nearest angle th */
  _skirtRadAt(th, y, pc) {
    const J = this.RJ, j = ((Math.round((th / (Math.PI * 2)) * J) % J) + J) % J, P = this.robePos;
    let prev = null;
    for (let i = 0; i <= this.SI; i++) {
      const o = ((this.NT + i) * J + j) * 3, py = P[o + 1], r = Math.hypot(P[o] - pc.x, P[o + 2] - pc.z);
      if (py <= y) { if (!prev) return r; const f = (prev[0] - y) / Math.max(1e-5, prev[0] - py); return lerp(prev[1], r, f); }
      prev = [py, r];
    }
    return prev ? prev[1] : 0;
  }
  /** hang a chain of points from p0 under gravity (+ swing), each pushed out of the skirt; segment lengths kept */
  _hang(p0, n, seg, pc, swing, margin, out) {
    out[0].copy(p0);
    const q = V();
    for (let i = 1; i <= n; i++) {
      q.copy(out[i - 1]).add(V(swing.x * 0.35 * i / n, -seg, swing.z * 0.35 * i / n));
      for (let pass = 0; pass < 2; pass++) {
        const th = Math.atan2(q.x - pc.x, q.z - pc.z), r = Math.hypot(q.x - pc.x, q.z - pc.z);
        const need = this._skirtRadAt(this._skAng(th), q.y, pc) + margin;
        if (r < need) { const k = need / Math.max(r, 1e-4); q.x = pc.x + (q.x - pc.x) * k; q.z = pc.z + (q.z - pc.z) * k; }
        if (q.y < FLOOR + 0.008) q.y = FLOOR + 0.008;
        q.sub(out[i - 1]).setLength(seg).add(out[i - 1]);
      }
      out[i].copy(q);
    }
    return out;
  }
  _skAng(thR) { return thR - (this._pelYaw || 0); }   // root-space angle -> skirt column angle

  // ------------------------------------------------------------------ mantle / sash (terracotta, over the left shoulder, knotted at the right hip)
  _buildMantle() {
    this.mRest = MANTLE.map(([y, th]) => robeRest(y, th).addScaledVector(robeRestN(y, th), y < 1.04 ? 0.012 : 0.0175));
    this.mUpsRest = MANTLE.map(([y, th]) => robeRestN(y, th));
    this.mRad = MANTLE.map((m) => m[2]);
    this.mW = MANTLE.map(([y]) => smoothstep(1.03, 1.14, y));
    this.mantle = new SweepTube({ material: this.mantleMat, segments: 48, radial: 10, capRings: 2 });
    this.root.add(this.mantle.mesh);
    this.mPts = this.mRest.map(() => V()); this.mUps = this.mRest.map(() => V());
    // knot + hanging tails
    this.knotRest = robeRest(KNOT_Y, KNOT_TH).addScaledVector(robeRestN(KNOT_Y, KNOT_TH), 0.016);
    this.knotN = robeRestN(KNOT_Y, KNOT_TH);
    this.knot = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), this.mantleMat);
    this.root.add(this.knot);
    this.tails = [[6, 0.04, 0.046, -0.008], [4, 0.04, 0.038, 0.018]].map(([n, seg, w, dx]) => ({ n, seg, w, dx, tube: new SweepTube({ material: this.mantleMat, segments: 14, radial: 8, capRings: 2 }), pts: Array.from({ length: n + 1 }, () => V()) }));
    for (const T of this.tails) this.root.add(T.tube.mesh);
  }
  _xfRest(p, w, shrug, hunch, br, out) {      // root-rest point -> current root space (chest/pelvis blend)
    const yr = p.y;
    out.set(p.x * (1 + 0.02 * br * w), yr - CHEST_Y0 + shrug * 0.055 * shoulderBand(p.x, yr) + 0.004 * br * smoothstep(1.2, 1.32, yr), p.z + hunch * 0.03 * shoulderBand(p.x, yr));
    this._protAdd(out, p.x, yr, p.z).applyMatrix4(this.Mc);
    if (w < 1) { const b = V(p.x, yr - HIP_Y, p.z).applyMatrix4(this.Mp); out.lerp(b, 1 - w); }
    return out;
  }
  _updateMantle(shrug, hunch, br, pc, swing) {
    const n = this.mRest.length;
    const qc = new THREE.Quaternion().setFromRotationMatrix(this.Mc), qp = new THREE.Quaternion().setFromRotationMatrix(this.Mp);
    for (let i = 0; i < n; i++) {
      this._xfRest(this.mRest[i], this.mW[i], shrug, hunch, br, this.mPts[i]);
      this.mUps[i].copy(this.mUpsRest[i]).applyQuaternion(this.mW[i] > 0.5 ? qc : qp);
    }
    const ups = this.mUps;
    this.mantle.update(this.mPts, this.mRad, { up: (s) => { const f = s * (n - 1), i = Math.min(n - 2, Math.floor(f)); return _hv.copy(ups[i]).lerp(ups[i + 1], f - i); }, flatten: 1.19 });
    // knot (pelvis-rigid) + two tails hanging under gravity over the skirt
    const K = this.knotRest.clone().sub(V(0, HIP_Y, 0)).applyMatrix4(this.Mp), kn = this.knotN.clone().applyQuaternion(qp);
    this.knot.position.copy(K);
    this.knot.scale.set(0.034, 0.024, 0.011);
    orientYZ(this.knot, V(0, 1, 0), kn);
    const side = V(-kn.z, 0, kn.x);
    for (const T of this.tails) {
      const p0 = K.clone().addScaledVector(side, T.dx).add(V(0, -0.012, 0)).addScaledVector(kn, -0.004);
      this._hang(p0, T.n, T.seg, pc, swing, 0.012, T.pts);
      const r = (s) => T.w * (0.75 + 0.35 * s) * (s > 0.92 ? 0.7 : 1);
      T.tube.update(T.pts, r, { up: kn, flatten: 1.15 });
    }
  }

  // ------------------------------------------------------------------ rope belt (two twisted strands) + knot + ends
  _buildBelt() {
    const yb = 1.0 - HIP_Y, rx = 0.176, rz = 0.139, zo = 0.007, beltParts = [];
    for (let k = 0; k < 2; k++) {
      const pts = [];
      for (let i = 0; i <= 96; i++) {
        const th = 0.5 + (i / 96) * Math.PI * 2;
        const tw = th * 9 + k * Math.PI;
        const r = 1 + 0.032 * Math.cos(tw);
        pts.push(V(Math.sin(th) * rx * r, yb + 0.0058 * Math.sin(tw), Math.cos(th) * rz * r + zo));
      }
      const tube = new SweepTube({ material: this.ropeMat, segments: 110, radial: 5, capRings: 1 });
      tube.update(pts, 0.0068);
      this.pelvisG.add(tube.mesh); beltParts.push(tube.mesh);
    }
    const kp = V(Math.sin(0.5) * rx * 1.03, yb - 0.004, Math.cos(0.5) * rz * 1.03 + zo);
    this.knotLocal = kp;
    for (const [dx, dy, r] of [[0, 0, 0.017], [0.012, -0.012, 0.012], [-0.01, -0.01, 0.011]]) {
      const m = new THREE.Mesh(new THREE.SphereGeometry(r, 14, 10), this.ropeMat);
      m.position.copy(kp).add(V(dx, dy, 0.006)); this.pelvisG.add(m); beltParts.push(m);
    }
    bake(this.pelvisG, beltParts);
    this.ropeEnds = [[7, -0.006], [6, 0.008]].map(([n, dx]) => {
      const tube = new SweepTube({ material: this.ropeMat, segments: 14, radial: 7, capRings: 2 });
      const tas = new THREE.Mesh(new THREE.SphereGeometry(0.011, 12, 8), this.ropeMat); tas.scale.set(1, 1.5, 1);
      this.root.add(tube.mesh, tas);
      return { n, dx, tube, tas, pts: Array.from({ length: n + 1 }, () => V()) };
    });
  }
  _updateRopeEnds(pc, swing) {
    const kp = this.knotLocal.clone().applyMatrix4(this.Mp);
    const side = V(1, 0, 0).transformDirection(this.Mp);
    for (const E of this.ropeEnds) {
      const p0 = kp.clone().addScaledVector(side, E.dx).add(V(0, -0.012, 0));
      this._hang(p0, E.n, 0.052, pc, swing, 0.011, E.pts);
      E.tube.update(E.pts, 0.0072);
      E.tas.position.copy(E.pts[E.n]).add(V(0, -0.008, 0));
    }
  }

  // ------------------------------------------------------------------ arms: wide bell sleeves, forearms, hands
  _buildArms() {
    this.arms = {};
    for (const side of ['L', 'R']) {
      const sleeve = new Sleeve(this.sleeveMat, this.liningMat);
      const fore = new SweepTube({ material: this.bodySkin, segments: 6, radial: 10, capRings: 2 });
      const hand = new SoftHand({ size: HAND_SIZE, side, material: this.bodySkin });
      this.root.add(sleeve.mesh, fore.mesh, hand.root);
      this.arms[side] = { sleeve, fore, hand, elbow: V(), wrist: V(), shoulder: V(), shoulderIn: V(), prot: V(), protC: V(), contact: null };
    }
  }

  _presetToRoot(d, s, out) {
    const M = d.space === 'head' ? this.Mh : this.Mc;
    out.t.set(s * d.t[0], d.t[1], d.t[2]).applyMatrix4(M);
    out.pole.set(s * d.pole[0], d.pole[1], d.pole[2]).transformDirection(M);
    out.palm.set(s * d.palm[0], d.palm[1], d.palm[2]).transformDirection(M);
    out.fing.set(s * d.fing[0], d.fing[1], d.fing[2]).transformDirection(M);
    return out;
  }
  /** weight (0..1) of a named preset in an arm spec (for the automatic body response), times reach */
  static presetW(A, name) {
    if (!A || !A.preset) return 0;
    const list = typeof A.preset === 'string' ? [[A.preset, 1]] : A.preset;
    let w = 0, sum = 0; for (const [n, x] of list) { const ww = Math.max(0, x ?? 1); sum += ww; if (n === name) w += ww; }
    return sum > 0 ? (w / sum) * clamp(A.reach ?? 1) : 0;
  }

  // ---- contact with another body (world space) ------------------------------------------------------------
  _surfList(obj) {
    if (this._sl && this._sl.obj === obj && this._sl.stamp === this._stamp) return this._sl.list;
    obj.updateMatrixWorld(true);
    const list = [];
    obj.traverseVisible((o) => {
      if (!o.isMesh || o.isInstancedMesh) return;
      const m = Array.isArray(o.material) ? o.material[0] : o.material;
      if (!m || m.transparent || m.blending === THREE.AdditiveBlending || m.depthWrite === false) return;
      const pa = o.geometry && o.geometry.attributes.position;
      if (!pa || pa.count < 60) return;
      o.geometry.computeBoundingSphere();         // dynamic geometry: keep the raycast bounds honest
      list.push(o);
    });
    this._sl = { obj, stamp: this._stamp, list };
    return list;
  }
  _ray(list, o, d, far = 4) {
    const rc = this._rc || (this._rc = new THREE.Raycaster());
    rc.set(o, d); rc.near = 0; rc.far = far;
    const hits = rc.intersectObjects(list, false);
    if (!hits.length) return null;
    const h = hits[0];
    const n = h.face ? h.face.normal.clone().applyMatrix3(new THREE.Matrix3().getNormalMatrix(h.object.matrixWorld)).normalize() : d.clone().negate();
    if (n.dot(d) > 0) n.negate();
    return { p: h.point.clone(), n };
  }
  /** surface spec -> { list, C } (meshes to raycast + the partner's vertical axis point) or a plain centre */
  _surf(spec) {
    if (!spec) return null;
    if (spec.isObject3D || spec.root) {
      const obj = spec.isObject3D ? spec : spec.root;
      return { list: this._surfList(obj), C: obj.getWorldPosition(V()) };
    }
    if (spec.center) return { C: toV(spec.center) };
    return { C: toV(spec) };
  }
  /** 'around': walk the hand round the partner's flank toward its back as far as the arm comfortably reaches */
  _aroundContact(A, s, shW, chestFwd) {
    const S = this._surf(A.surface), tg = A.target ? toV(A.target) : null;
    const h = tg ? tg.y : (A.height ?? shW.y + 0.1);
    const C = S.C, e0 = V(shW.x - C.x, 0, shW.z - C.z).normalize();
    const back = V(-chestFwd.x, 0, -chestFwd.z).normalize();
    const sg = Math.sign(e0.z * back.x - e0.x * back.z) || 1;
    const dirAt = (phi) => { const a = sg * phi, c = Math.cos(a), sn = Math.sin(a); return V(e0.x * c + e0.z * sn, 0, -e0.x * sn + e0.z * c); };
    const hitAt = (phi) => {
      const d = dirAt(phi);
      if (!S.list) { const r = tg ? Math.hypot(tg.x - C.x, tg.z - C.z) : 0.8; return { p: V(C.x, h, C.z).addScaledVector(d, r), n: d.clone(), phi }; }
      const r = this._ray(S.list, V(C.x, h, C.z).addScaledVector(d, 3.5), d.clone().negate(), 3.6);
      if (r) r.phi = phi;
      return r;
    };
    const budget = A.span ?? 0.5;
    let phiMax = 1.7;
    if (tg) { const dt = V(tg.x - C.x, 0, tg.z - C.z).normalize(); phiMax = Math.min(phiMax, Math.max(0, Math.acos(clamp(dt.dot(e0), -1, 1)))); }
    let prev = hitAt(0);
    if (!prev) return null;
    if (prev.p.distanceTo(shW) <= budget) {
      let done = false;
      for (let phi = 0.2; phi <= phiMax + 1e-6 && !done; phi = Math.min(phi + 0.2, phiMax + (phi >= phiMax ? 1 : 0))) {
        const cur = hitAt(Math.min(phi, phiMax));
        if (!cur) break;
        if (cur.p.distanceTo(shW) > budget) {
          let lo = prev, hi = cur;
          for (let it = 0; it < 3; it++) { const m = hitAt((lo.phi + hi.phi) / 2); if (!m) break; if (m.p.distanceTo(shW) > budget) hi = m; else lo = m; }
          const dl = lo.p.distanceTo(shW), dh = hi.p.distanceTo(shW), f = clamp((budget - dl) / Math.max(1e-5, dh - dl));
          prev = { p: lo.p.clone().lerp(hi.p, f), n: lo.n.clone().lerp(hi.n, f).normalize(), phi: lerp(lo.phi, hi.phi, f) };
          done = true;
        } else prev = cur;
        if (phi >= phiMax) break;
      }
    }
    const d = dirAt(prev.phi), tw = V(sg * d.z, 0, -sg * d.x);
    return { p: prev.p, n: prev.n, tw, C };
  }
  /** a hand resting ON a surface (shoulder / pat / any palm contact): snap the target onto it from above / along the reach */
  _restContact(A, shW, tgW) {
    const S = this._surf(A.surface);
    if (S && S.list) {
      let r = this._ray(S.list, tgW.clone().add(V(0, 0.12, 0)), V(0, -1, 0), 0.3);
      if (!r || r.p.distanceTo(tgW) > 0.16 || r.n.y < 0.35) r = this._ray(S.list, shW, tgW.clone().sub(shW).normalize(), shW.distanceTo(tgW) + 0.25);
      if (r && r.p.distanceTo(tgW) < 0.25) return r;
      return null;
    }
    if (S) return { p: tgW.clone(), n: V(tgW.x - S.C.x, 0, tgW.z - S.C.z).normalize() };
    return null;
  }

  _updateArm(side, A, ctx) {
    const s = side === 'L' ? 1 : -1, arm = this.arms[side], t = ctx.t;
    A = A || {};
    let list = A.preset ?? 'rest';
    if (typeof list === 'string') list = [[list, 1]];
    const acc = { t: V(), pole: V(), palm: V(), fing: V(), hand: {} }, one = { t: V(), pole: V(), palm: V(), fing: V() };
    for (const k of HAND_KEYS) acc.hand[k] = 0;
    let wsum = 0, restW = 0, palmW = 0, aroundW = 0, anims = [];
    for (const [name, w0] of list) {
      const d = ARM[name] || ARM.rest; const w = Math.max(0, w0 ?? 1);
      if (w <= 0) continue;
      this._presetToRoot(d, s, one);
      if (d.anim === 'knee' && ctx.kneeFront) {      // forearm resting on the raised knee
        const kn = ctx.kneeFront;
        one.t.copy(kn).add(V(s * 0.03, 0.06, 0.1).applyQuaternion(ctx.rootYawQ || new THREE.Quaternion()));
      }
      acc.t.addScaledVector(one.t, w); acc.pole.addScaledVector(one.pole, w); acc.palm.addScaledVector(one.palm, w); acc.fing.addScaledVector(one.fing, w);
      for (const k of HAND_KEYS) acc.hand[k] += (d.hand[k] ?? HAND_DEF[k]) * w;
      if (name === 'rest') restW += w;
      if (name === 'around') aroundW += w;
      if (d.anim) anims.push([d.anim, w]);
      if (d.at === 'palm') palmW += w;
      wsum += w;
    }
    if (wsum <= 0) { this._presetToRoot(ARM.rest, s, acc); for (const k of HAND_KEYS) acc.hand[k] = ARM.rest.hand[k] ?? HAND_DEF[k]; restW = 1; wsum = 1; }
    else { acc.t.multiplyScalar(1 / wsum); for (const k of HAND_KEYS) acc.hand[k] /= wsum; restW /= wsum; aroundW /= wsum; }
    const reach = clamp(A.reach ?? 1);
    const atPalm = A.at ? A.at === 'palm' : palmW / Math.max(wsum, 1e-6) > 0.5;
    // shoulder joint (root space) before protraction
    const sh0 = V(s * SH[0], SH[1] + ctx.shrug * 0.05 + 0.004 * ctx.br, SH[2] + ctx.hunch * 0.03).applyMatrix4(this.Mc);
    const M = this.root.matrixWorld, shW = sh0.clone().applyMatrix4(M);
    // ---- contact with a partner's body (world): around (wrap round the flank) / rest-on (shoulder, pat...)
    arm.contact = null;
    let contactPole = null;
    const wantContact = (A.surface || A.normal) && atPalm;
    if (wantContact || (aroundW > 0.5 && A.target)) {
      const chestFwd = V(0, 0, 1).transformDirection(this.Mc).transformDirection(M);
      let c = null;
      if (aroundW > 0.5) {
        if (A.surface) c = this._aroundContact(A, s, shW, chestFwd);
        if (!c && A.target) {           // target only: assume the body's inward normal points away from his chest
          const tg = toV(A.target), cw = V(0, 0, 0).applyMatrix4(this.Mc).applyMatrix4(M);
          const nIn = V(tg.x - cw.x, 0, tg.z - cw.z).normalize();
          const n = A.normal ? toV(A.normal).normalize() : nIn.clone().negate();
          const tw = V(-n.z, 0, n.x); if (tw.dot(chestFwd) > 0) tw.negate();
          c = { p: tg, n, tw };
        }
        if (c) {
          const n = c.n.clone(), tw = c.tw.clone().sub(n.clone().multiplyScalar(n.dot(c.tw))).normalize();
          acc.t.copy(c.p).addScaledVector(n, 0.004).applyMatrix4(this.rootInv);
          if (!A.palm) acc.palm.copy(n).negate().applyQuaternion(this.rootQInv);
          if (!A.fingers) acc.fing.copy(tw).multiplyScalar(0.94).add(V(0, -0.2, 0)).addScaledVector(n, -0.12).normalize().applyQuaternion(this.rootQInv);
          const back = V(-chestFwd.x, 0, -chestFwd.z).normalize();
          contactPole = n.clone().multiplyScalar(0.55).add(V(0, 0.8, 0)).addScaledVector(back, 0.3).normalize().applyQuaternion(this.rootQInv);
          arm.contact = { p: c.p.clone(), n };
        }
      } else if (A.target) {
        const tg = toV(A.target);
        c = A.normal ? { p: tg, n: toV(A.normal).normalize() } : this._restContact(A, shW, tg);
        if (c) {
          acc.t.copy(c.p).addScaledVector(c.n, 0.004).applyMatrix4(this.rootInv);
          if (!A.palm) acc.palm.copy(c.n).negate().applyQuaternion(this.rootQInv);
          arm.contact = { p: c.p.clone(), n: c.n.clone() };
        }
      }
    }
    // world overrides
    if (A.target && !arm.contact) acc.t.copy(toV(A.target)).applyMatrix4(this.rootInv);
    if (A.pole) acc.pole.copy(toV(A.pole)).applyQuaternion(this.rootQInv); else if (contactPole) acc.pole.copy(contactPole);
    if (A.palm) acc.palm.copy(toV(A.palm)).applyQuaternion(this.rootQInv);
    if (A.fingers) acc.fing.copy(toV(A.fingers)).applyQuaternion(this.rootQInv);
    else if ((A.palm || (arm.contact && aroundW <= 0.5)) && atPalm) {
      // palm given but no fingers: lay the fingers forward / over (along the reach, in the palm plane, drooping)
      const pn = acc.palm.clone().normalize();
      const d = acc.t.clone().sub(V(0, sh0.y, 0).setX(0)); d.y = 0; d.normalize();
      let f = d.clone().addScaledVector(pn, -pn.dot(d));
      if (f.lengthSq() < 0.09) { f = V(0, -1, 0).addScaledVector(pn, pn.y); }
      acc.fing.copy(f.normalize()).addScaledVector(V(0, -1, 0), 0.25).addScaledVector(pn, 0.18).normalize();
    }
    if (A.offset) acc.t.add(toV(A.offset).applyQuaternion(this.rootQInv));
    // reach: blend from rest
    if (reach < 1) {
      const r = this._presetToRoot(ARM.rest, s, { t: V(), pole: V(), palm: V(), fing: V() });
      acc.t.lerp(r.t, 1 - reach); acc.pole.normalize().lerp(r.pole, 1 - reach); acc.palm.normalize().lerp(r.palm, 1 - reach); acc.fing.normalize().lerp(r.fing, 1 - reach);
      for (const k of HAND_KEYS) acc.hand[k] = lerp(ARM.rest.hand[k] ?? HAND_DEF[k], acc.hand[k], reach);
      restW = lerp(1, restW, reach);
    }
    if (A.hand) for (const k of HAND_KEYS) if (A.hand[k] != null) acc.hand[k] = A.hand[k];
    // palm-anchored contact: the target is where the PALM centre goes (wrist backs off along the fingers / palm normal)
    if (atPalm && acc.fing.lengthSq() > 1e-8 && acc.palm.lengthSq() > 1e-8) {
      const fdn = acc.fing.clone().normalize(), pn = acc.palm.clone().normalize();
      acc.t.addScaledVector(fdn, -HAND_SIZE * 0.42 * reach).addScaledVector(pn, -0.022 * reach);
    }
    // walk / run arm swing (on the resting part of the pose)
    if (ctx.amt > 0 && restW > 0) {
      const S = ctx.ST, sw = ctx.swing * s * -1;     // opposite to the same-side leg
      const w = ctx.amt * restW;
      const fwd = V(0, 0, 1).transformDirection(this.Mp);
      acc.t.addScaledVector(fwd, sw * S.arm * w);
      acc.t.y += (0.02 * Math.abs(sw) + 0.17 * S.run) * w;
      if (S.run) { acc.t.addScaledVector(fwd, 0.1 * w); acc.t.x -= s * 0.04 * w; acc.pole.lerp(V(s * 0.3, -0.4, -1), w); acc.hand.curl = lerp(acc.hand.curl, 0.75, w); }
    }
    // gesture beats / waves
    const gest = A.gesture ?? 1;
    for (const [an, w] of anims) {
      if (an === 'beat' && gest > 0) {
        let b = 0;
        const ev = this.beatEv;
        for (let i = this._bsearch(ev, t); i >= 0 && i > this._bsearch(ev, t) - 3; i--) { const dt = t - ev[i]; if (dt >= 0) b = Math.max(b, Math.exp(-dt * 5) * (1 - Math.exp(-dt * 40)) * (0.6 + 0.4 * hash1(i * 5 + (s > 0 ? 1 : 2)))); }
        const amp = gest * w * (ctx.talk ? 0.5 + ctx.talk : 1);
        acc.t.y -= 0.045 * b * amp;
        acc.t.x += s * 0.02 * noise1(t * 0.7, 51 + s) * amp; acc.t.z += 0.025 * noise1(t * 0.55, 61 + s) * amp;
        acc.fing.y -= 0.25 * b * amp;
      }
      if (an === 'pat') { const ph2 = (t * (A.patRate ?? 2.2)) % 1; acc.t.addScaledVector(acc.palm.clone().normalize(), -0.035 * w * (A.pat ?? 1) * Math.pow(Math.sin(Math.PI * ph2), 2)); }
      if (an === 'wave') { const a = 0.38 * Math.sin(t * Math.PI * 2 * 1.6) * w; acc.fing.addScaledVector(V(s, 0, 0).transformDirection(this.Mc), a); }
    }
    if (A.wiggle) acc.t.add(V(noise1(t * 2.1, 71 + s), noise1(t * 2.3, 73 + s), noise1(t * 1.9, 75 + s)).multiplyScalar(0.012 * A.wiggle));
    // shoulder / scapula protraction toward far targets (and always a little for a contact around someone)
    const dT = acc.t.clone().sub(sh0), dist = dT.length();
    const pk = clamp((dist - 0.4) * 0.9, 0, 0.075) + 0.05 * aroundW * reach + 0.02 * (arm.contact ? 1 : 0) * reach;
    arm.prot.copy(dT.normalize()).multiplyScalar(Math.min(0.11, pk));
    arm.prot.y = Math.max(arm.prot.y, 0) * 0.8 + 0.025 * aroundW * reach;
    arm.protC.copy(arm.prot).applyQuaternion(new THREE.Quaternion().setFromRotationMatrix(this.Mc).invert());   // chest-space (robe/mantle field)
    // IK
    const sh = arm.shoulder.copy(sh0).add(arm.prot);
    const pole = acc.pole.lengthSq() > 1e-8 ? acc.pole.normalize() : V(s, 0, -1);
    const { mid: elbow, end: wrist } = solveIK2(sh, acc.t, UPPER, FORE, pole);
    arm.elbow.copy(elbow); arm.wrist.copy(wrist);
    // hand orientation with a wrist limit
    const fore = wrist.clone().sub(elbow).normalize();
    let fd = acc.fing.lengthSq() > 1e-8 ? acc.fing.clone().normalize() : fore.clone();
    const ang = fore.angleTo(fd);
    if (ang > MAXWRIST) { const qq = new THREE.Quaternion().setFromUnitVectors(fore, fd); fd = fore.clone().applyQuaternion(new THREE.Quaternion().slerp(qq, MAXWRIST / ang)); }
    let palm = acc.palm.lengthSq() > 1e-8 ? acc.palm.clone().normalize() : V(0, -1, 0);
    if (Math.abs(palm.dot(fd)) > 0.97) palm = V(-s, 0, 0);
    arm.hand.root.position.copy(wrist);
    arm.hand.aim(fd, palm);
    arm.hand.pose(acc.hand);
    // sleeve: slides toward the elbow when the forearm points up, droops when horizontal; rolled hem + lit lining
    const up = fore.y;
    const kEnd = lerp(0.84, 0.6, smoothstep(-0.25, 0.85, up));
    const sEnd = elbow.clone().lerp(wrist, kEnd);
    const droop = 0.02 * (1 - Math.abs(up));
    sEnd.y -= droop;
    const shIn = arm.shoulderIn.set(s * (SH[0] - 0.035), SH[1] + ctx.shrug * 0.05 - 0.006, SH[2]).applyMatrix4(this.Mc).addScaledVector(arm.prot, 0.85);
    const m1 = sh.clone().lerp(elbow, 0.5), m2 = elbow.clone().lerp(sEnd, 0.55); m2.y -= droop * 0.5;
    const SR = [0.058, 0.062, 0.058, 0.056, 0.063, 0.072];
    arm.sleeve.update([shIn, sh.clone().lerp(m1, 0.3), m1, elbow, m2, sEnd], (u) => { const f = u * 5, i = Math.min(4, Math.floor(f)); return lerp(SR[i], SR[i + 1], smooth(f - i)); });
    arm.fore.update([elbow.clone().lerp(wrist, 0.3), wrist.clone().addScaledVector(fore, 0.012)], [0.035, 0.029]);
  }
  _bsearch(arr, t) { let lo = 0, hi = arr.length - 1, r = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (arr[m] <= t) { r = m; lo = m + 1; } else hi = m - 1; } return r; }

  // ------------------------------------------------------------------ legs (invisible IK -> drape colliders), feet + sandals
  _buildLegs() {
    this.feet = {};
    for (const side of ['L', 'R']) {
      const s = side === 'L' ? 1 : -1;
      const g = new THREE.Group(); g.rotation.order = 'YXZ';
      // sandal sole (extruded outline, big toe on the inside)
      const sh = new THREE.Shape();
      const X = (x) => x * s;
      sh.moveTo(0, -0.07);
      sh.quadraticCurveTo(X(0.038), -0.07, X(0.038), -0.035);
      sh.lineTo(X(0.043), 0.06);
      sh.quadraticCurveTo(X(0.05), 0.13, X(0.03), 0.166);
      sh.quadraticCurveTo(X(0.0), 0.19, X(-0.03), 0.174);
      sh.quadraticCurveTo(X(-0.047), 0.15, X(-0.042), 0.09);
      sh.quadraticCurveTo(X(-0.03), 0.03, X(-0.034), -0.03);
      sh.quadraticCurveTo(X(-0.036), -0.07, 0, -0.07);
      const sg = new THREE.ExtrudeGeometry(sh, { depth: 0.011, bevelEnabled: true, bevelThickness: 0.004, bevelSize: 0.004, bevelSegments: 1, curveSegments: 5 });
      sg.rotateX(Math.PI / 2); sg.translate(0, -ANKLE_Y + 0.015, 0);
      // (ExtrudeGeometry normalises the winding of the mirrored outline itself)
      const sole = new THREE.Mesh(sg, this.leatherMat); g.add(sole);
      const sk = (r, p, sc = [1, 1, 1], ws = 18, hs = 12) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, ws, hs), this.bodySkin); m.position.set(...p); m.scale.set(...sc); g.add(m); return m; };
      sk(1, [0, -ANKLE_Y + 0.044, 0.042], [0.039, 0.029, 0.098]);           // foot body
      sk(0.032, [0, -ANKLE_Y + 0.036, -0.035]);                              // heel
      sk(0.034, [0, -0.006, -0.008], [1, 1.1, 1]);                           // ankle
      const toes = [[-0.022, 0.134, 0.0148], [-0.004, 0.137, 0.0108], [0.011, 0.131, 0.0099], [0.024, 0.121, 0.0091], [0.035, 0.107, 0.0086]];
      for (const [x, z, r] of toes) sk(r, [X(x), -ANKLE_Y + 0.016 + r * 0.95, z], [1, 0.9, 1.15], 12, 8);
      const st = (geo, p, rot, sc = [1, 1, 1]) => { const m = new THREE.Mesh(geo, this.leatherMat); m.position.set(...p); m.rotation.set(...rot); m.scale.set(...sc); g.add(m); return m; };
      st(new THREE.TorusGeometry(0.041, 0.0062, 6, 18, Math.PI), [0, -ANKLE_Y + 0.017, 0.052], [0, 0, 0], [1.02, 0.95, 2.2]);   // instep strap
      st(new THREE.TorusGeometry(0.038, 0.0052, 6, 16, Math.PI), [X(-0.004), -ANKLE_Y + 0.016, 0.098], [0, 0, 0], [1, 0.75, 1.4]);   // toe strap
      st(new THREE.TorusGeometry(0.037, 0.0055, 6, 20), [0, -0.03, -0.012], [Math.PI / 2, 0, 0], [1, 1.05, 1]);   // ankle strap
      st(new THREE.CylinderGeometry(0.006, 0.006, 0.035, 6), [0, -0.05, -0.052], [0.35, 0, 0]);                      // heel strap
      bake(g, [...g.children]);
      this.root.add(g);
      const shin = new SweepTube({ material: this.bodySkin, segments: 4, radial: 10, capRings: 2 });
      this.root.add(shin.mesh);
      this.feet[side] = { g, shin, knee: V(), ankle: V(), hip: V() };
    }
    this.shadow = contactShadow(0.95, 0.62, 0.38); this.root.add(this.shadow);
  }

  // ------------------------------------------------------------------ anchors
  _buildAnchors() {
    const H = this.headG, C = this.chestG;
    this.addAnchor('head', H, [0, 0, 0]);
    this.addAnchor('top', H, [0, 0.2, -0.01]);
    this.addAnchor('eyes', H, [0, EYE_V * HR[1], 0.145]);
    this.addAnchor('mouth', H, [0, -0.078, 0.14]);
    this.addAnchor('earL', H, [0.15, -0.012, -0.012]);
    this.addAnchor('earR', H, [-0.15, -0.012, -0.012]);
    this.addAnchor('chest', C, [0, 0.16, 0.15]);
    this.addAnchor('back', C, [0, 0.17, -0.15]);
    this.addAnchor('shoulderL', C, [0.165, 0.315, -0.01]);
    this.addAnchor('shoulderR', C, [-0.165, 0.315, -0.01]);
    this.addAnchor('handL', this.arms.L.hand.root, [0, HAND_SIZE * 0.42, -0.012]);
    this.addAnchor('handR', this.arms.R.hand.root, [0, HAND_SIZE * 0.42, -0.012]);
    this.addAnchor('hip', this.pelvisG, [0, 0, 0]);
    for (const n of ['footL', 'footR', 'kneeL', 'kneeR', 'elbowL', 'elbowR']) this.addAnchor(n, this.root, [0, 0, 0]);
  }

  // ===================================================================================== update
  update(t, pose = {}) {
    const P = pose || {}, B = P.body || {}, Wk = P.walk || {}, Hd = P.head || {};
    this.place(P.pos || [0, 0, 0], P.yaw || 0);
    this.root.updateWorldMatrix(true, false);
    this.rootInv.copy(this.root.matrixWorld).invert();
    this.root.getWorldQuaternion(this.rootQInv); this.rootQInv.invert();
    const style = WALK[Wk.style] ? Wk.style : 'walk', ST = WALK[style];
    const amt = clamp(Wk.amount ?? 0), ph = Wk.phase ?? t * ST.rate;
    const kneel = clamp(B.kneel ?? 0), crouch = clamp(B.crouch ?? 0), sit = clamp(B.sit ?? 0), tiptoe = clamp(B.tiptoe ?? 0);
    const giggle = clamp(B.giggle ?? 0);
    const gp = Math.sin(t * Math.PI * 2 * 5.2);
    const shrug = clamp((B.shrug ?? 0) + giggle * (0.28 + 0.1 * gp));
    const hunch = clamp(B.hunch ?? 0), slump = clamp(B.slump ?? 0), recoil = B.recoil ?? 0;
    const br = (this.breath(t, B.breathRate ?? 0.22) - 0.5) * (B.breathe ?? 1);
    const idle = (B.sway ?? 1) * (1 - amt);
    this._stamp = {};
    // automatic body response to an arm around someone (lean into them, chest turns toward them)
    const arL = Jesus.presetW(P.armL, 'around'), arR = Jesus.presetW(P.armR, 'around');
    const autoL = P.armL && P.armL.auto === false ? 0 : arL, autoR = P.armR && P.armR.auto === false ? 0 : arR;
    const autoTilt = 0.07 * (autoL - autoR), autoTwist = 0.13 * (autoL - autoR), autoLean = 0.03 * Math.max(autoL, autoR);
    const sp = this.speech(t, P);
    const talk = sp ? clamp(sp.open * 1.6) : 0;

    // ---- feet & pelvis (root-local)
    const pel = V(0.007 * fbm1(t * 0.3, 5) * idle, HIP_Y + br * 0.004 - 0.004, 0);
    let pelYaw = 0.02 * fbm1(t * 0.21, 8) * idle, pelRoll = 0.012 * fbm1(t * 0.27, 9) * idle, pelPitch = 0, lean = 0, chestYaw = 0, swingDz = 0;
    const feet = [1, -1].map((s) => ({ s, a: V(s * 0.1, ANKLE_Y, s > 0 ? 0.02 : -0.01), pitch: 0, yaw: s * 0.12, pole: V(s * 0.12, 0, 1) }));
    if (amt > 0) {
      const zs = [];
      for (const f of feet) {
        const c = footCycle(fract(ph + (f.s > 0 ? 0 : 0.5)), ST);
        const wa = plantAnkle(f.s * (0.1 - 0.02 * ST.run), c.z, c.lift, c.pitch, V());
        f.a.lerp(wa, amt); f.pitch = lerp(f.pitch, c.pitch, amt); f.yaw = lerp(f.yaw, f.s * 0.06, amt);
        f.pole.lerp(V(f.s * 0.08, 0, 1), amt);
        zs.push(c.z);
      }
      swingDz = (zs[0] - zs[1]) / (ST.stride * ST.stance);
      pel.y -= amt * ST.bob * (0.5 + 0.5 * Math.cos(4 * Math.PI * (ph - ST.bobPh))) - amt * ST.run * 0.02;
      pel.x += amt * ST.sway * Math.sin(2 * Math.PI * ph);
      pelYaw += -amt * ST.twist * swingDz;
      pelRoll += amt * 0.025 * Math.cos(2 * Math.PI * ph);
      chestYaw += amt * ST.twist * 0.85 * swingDz;
      lean += amt * ST.lean;
    }
    if (tiptoe > 0) { for (const f of feet) { plantAnkle(f.a.x, f.a.z, f.a.y - ANKLE_Y, Math.max(f.pitch, 0.75 * tiptoe), f.a); f.pitch = Math.max(f.pitch, 0.75 * tiptoe); } pel.y += 0.058 * tiptoe; }
    let kneeFront = null;
    if (kneel > 0) {
      const ks = B.kneelSide === 'L' ? 1 : -1;
      const k1 = smooth(kneel / 0.45), k2 = smooth((kneel - 0.15) / 0.85);
      for (const f of feet) {
        if (f.s === ks) {
          f.a.lerp(V(ks * 0.1, 0.088, -0.40), k2); f.a.y += Math.sin(Math.PI * k2) * 0.04;
          f.pitch = lerp(f.pitch, 1.3, k2); f.yaw = lerp(f.yaw, ks * 0.04, k2); f.pole.lerp(V(0, -0.7, 1), k2);
        } else {
          f.a.lerp(V(-ks * 0.12, ANKLE_Y, 0.34), k1); f.a.y += Math.sin(Math.PI * k1) * 0.07;
          f.pitch *= 1 - k1; f.pole.lerp(V(-ks * 0.15, 0.25, 1), k1);
        }
      }
      pel.lerp(V(0, 0.515, -0.05), k2);
      lean += 0.16 * Math.sin(Math.PI * k2) + 0.03 * k2;
      pelPitch -= 0.06 * k2;
    }
    if (crouch > 0) {
      const c = smooth(crouch);
      pel.y -= 0.37 * c; pel.z -= 0.08 * c;
      for (const f of feet) { f.a.x += f.s * 0.035 * c; f.pole.lerp(V(f.s * 0.4, 0, 1), c); }
      lean += 0.4 * c;
    }
    if (sit > 0) {
      const c = smooth(sit);
      pel.lerp(V(0, 0.14, -0.12), c); pelPitch -= 0.3 * c;
      for (const f of feet) { f.a.lerp(V(f.s * 0.13, ANKLE_Y, 0.36), c); f.pole.lerp(V(f.s * 0.25, 1, 0.4), c); f.pitch = lerp(f.pitch, -0.25, c); }
      lean += 0.25 * c;
    }
    pel.y += B.bounce ?? 0;
    if (giggle > 0) pel.y += 0.006 * giggle * Math.abs(gp);
    this.pelvisG.position.copy(pel);
    this.pelvisG.rotation.set(pelPitch, pelYaw, pelRoll);
    this._pelYaw = pelYaw;
    // ---- chest
    const chestLean = lean + autoLean + (B.lean ?? 0) + slump * 0.2 + hunch * 0.16 - recoil * 0.22 + br * 0.012 + 0.008 * fbm1(t * 0.23, 12) * idle;
    this.chestG.position.set(0, WAIST_H - slump * 0.02, 0);
    this.chestG.rotation.set(chestLean, chestYaw + autoTwist + (B.twist ?? 0) + 0.02 * fbm1(t * 0.19, 13) * idle, -(B.tilt ?? 0) - autoTilt + 0.014 * fbm1(t * 0.25, 14) * idle);
    this.pelvisG.updateMatrix(); this.chestG.updateMatrix();
    this.Mp.copy(this.pelvisG.matrix); this.Mc.multiplyMatrices(this.Mp, this.chestG.matrix);
    // ---- neck & head
    this.neckG.position.set(0, NECK_BASE - shrug * 0.022 - slump * 0.01, -0.01 + hunch * 0.03);
    let hy = Hd.yaw ?? 0, hp = Hd.pitch ?? 0, hr = Hd.roll ?? 0;
    hy += 0.035 * fbm1(t * 0.17, 21) * idle; hp += 0.02 * fbm1(t * 0.19, 22) * idle; hr += 0.018 * fbm1(t * 0.15, 23) * idle;
    hy -= chestYaw * 0.85; hp += amt * 0.012 * Math.cos(4 * Math.PI * ph) - lean * 0.6 * (Hd.compensate ?? 1);
    hp += slump * 0.18 - recoil * 0.15 - hunch * 0.1;
    if (giggle > 0) { hp += 0.03 * gp * giggle; hr += 0.07 * giggle; }
    if (sp && (Hd.talk ?? 1) > 0) { const k2 = Hd.talk ?? 1; hp += 0.05 * (sp.open - 0.3) * k2; hy += 0.03 * noise1(t * 0.8, 31) * k2; hr += 0.02 * noise1(t * 0.6, 32) * k2; }
    const follow = clamp(Hd.follow ?? 0);
    if (follow > 0) {
      const lp = Hd.look ? toV(Hd.look) : gazePoint(P.gaze, CTX.camera);
      if (lp) {
        this.root.updateMatrixWorld(true);
        const loc = this.chestG.worldToLocal(lp.clone()).sub(V(0, NECK_BASE + NECK_LEN + 0.06, 0));
        const yT = clamp(Math.atan2(loc.x, loc.z), -1.3, 1.3), pT = clamp(-Math.atan2(loc.y, Math.hypot(loc.x, loc.z)), -0.75, 0.7);
        hy = lerp(hy, yT + (Hd.yaw ?? 0), follow); hp = lerp(hp, pT + (Hd.pitch ?? 0), follow);
      }
    }
    this.neckG.rotation.set(0.3 * hp + hunch * 0.3, 0.3 * hy, -0.3 * hr);
    this.headPivot.rotation.set(0.7 * hp - hunch * 0.22, 0.7 * hy, -0.7 * hr);
    this.root.updateMatrixWorld(true);
    this.Mh.multiplyMatrices(this.rootInv, this.headG.matrixWorld);

    // ---- face (eyes, brows, mouth) + beard + hair
    const fp = resolveFace(P.face);
    const dart = clamp(P.dart ?? 0);
    if (dart > 0) {
      const ev = this.dartEv, i = this._bsearch(ev, t);
      const side = (k) => (k < 0 ? 0 : ((k % 2) ? 1 : -1) * (0.7 + 0.3 * hash1(k * 7 + 3)));
      const u = smooth((t - ev[Math.max(0, i)]) / 0.06);
      fp.gazeYaw = (fp.gazeYaw ?? 0) + lerp(side(i - 1), side(i), u) * 0.34 * dart;
      fp.gazePitch = (fp.gazePitch ?? 0) + (hash1(i * 13 + 1) - 0.5) * 0.1 * dart;
      fp.saccade = 0;
    }
    const gaze = gazePoint(P.gaze, CTX.camera);
    this._faceExtras(fp);
    this.face.update(t, fp, { gaze, speech: sp, blinkAt: P.blinkAt });
    this._updateBeard(this.face.state);
    this._updateCreases(this.face.state);

    // ---- neck tube
    if (!this.neckTube) { this.neckTube = new SweepTube({ material: this.bodySkin, segments: 6, radial: 14, capRings: 2 }); this.root.add(this.neckTube.mesh); }
    const n0 = V(0, NECK_BASE - 0.05, -0.012).applyMatrix4(this.Mc);
    const n1 = V(0, 0, 0).applyMatrix4(this.Mh.clone().multiply(new THREE.Matrix4().makeTranslation(0, -HEAD_UP, 0)));
    const n2 = V(0, -0.085, -0.025).applyMatrix4(this.Mh);
    this.neckTube.update([n0, n1, n2], [0.05, 0.05, 0.048]);

    // ---- legs (IK) -> feet visuals + drape colliders
    const caps = [];
    for (const f of feet) {
      const side = f.s > 0 ? 'L' : 'R', F = this.feet[side];
      F.hip.set(f.s * HIP_X, -0.06, 0).applyMatrix4(this.Mp);
      const { mid: knee, end: ankle } = solveIK2(F.hip, f.a, THIGH, SHIN, f.pole.normalize());
      F.knee.copy(knee); F.ankle.copy(ankle);
      F.g.position.copy(ankle); F.g.rotation.set(f.pitch, f.yaw + pelYaw * 0.4, 0);
      const sd = knee.clone().sub(ankle).normalize();
      F.shin.update([ankle.clone().addScaledVector(sd, 0.01), ankle.clone().addScaledVector(sd, 0.16)], [0.036, 0.04]);
      const fwd = V(0, 0, 1).applyEuler(F.g.rotation);
      const toe = ankle.clone().addScaledVector(fwd, 0.15).add(V(0, -0.04, 0).applyEuler(F.g.rotation));
      caps.push({ a: F.hip, b: knee, ra: 0.088, rb: 0.066 }, { a: knee, b: ankle, ra: 0.063, rb: 0.046 }, { a: ankle, b: toe, ra: 0.045, rb: 0.035 });
      this._anch['knee' + side].position.copy(knee); this._anch['foot' + side].position.copy(ankle);
      if (kneel > 0 && f.s !== (B.kneelSide === 'L' ? 1 : -1)) kneeFront = knee.clone();
    }
    // ---- arms
    const actx = { t, amt, ST, swing: swingDz, shrug, hunch, br, talk, kneeFront };
    this._updateArm('L', P.armL, actx);
    this._updateArm('R', P.armR, actx);
    this._anch.elbowL.position.copy(this.arms.L.elbow); this._anch.elbowR.position.copy(this.arms.R.elbow);
    this._updateHair(t, shrug);
    // ---- robe + drape
    const swing = V(amt * 0.03 * Math.sin(2 * Math.PI * ph - 1.1) + 0.006 * fbm1(t * 0.4, 41) * idle, 0, -amt * ST.drag + 0.005 * fbm1(t * 0.35, 42) * idle);
    this._updateRobe({ br, shrug, hunch, caps, pc: pel, yaw: pelYaw, swing, knees: [this.feet.L.knee, this.feet.R.knee] });
    this._updateRopeEnds(pel, swing);
    this._updateMantle(shrug, hunch, br, pel, swing);
    // ---- contact shadow / glow
    this.shadow.visible = P.shadow !== false;
    this.shadow.scale.set(1 + 0.4 * kneel + 0.5 * sit, 1, 1 + 0.7 * kneel + 0.6 * sit);
    this.shadow.position.set(pel.x, 0.004, pel.z * 0.6);
    const glow = P.glow ?? 1;
    for (const [m, base] of this._rims) m.userData.uniforms.uRim.value = base * glow;
    this.state = { t, kneel, crouch, sit, amt, shrug };
    return this;
  }
}

export async function create() { return new Jesus(); }
export { Jesus };
