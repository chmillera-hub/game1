// THE VOID — CHARS.VOID (speaker 'VOID'; it only vocalizes). A ~3 m, plump, hooded cloak-being of deep indigo
// velvet with faint stars drifting INSIDE the fabric and a violet→teal rim glow. Its deep hood holds a field of
// cosmic darkness with two big starlight eyes (lids = the darkness), nebula-wisp brows and a crescent mouth that
// opens into deeper cosmos. Big gentle 3-finger hands from wide sleeves; short fat legs that peek out / kick.
// Pose API, anchors, tips: docs/chars/void.md.  Lab: src/labs/void.js.
import * as THREE from 'three';
import { Character, gazePoint } from '../core/character.js';
import { Face, FACE_DEFAULTS, ellipsoidSurface } from '../core/face.js';
import { SweepTube, Limb, orientYZ } from '../core/limbs.js';
import { contactShadow, GLOBAL } from '../core/materials.js';
import { Particles, CELL } from '../core/particles.js';
import { CTX, EYE_LIGHT } from '../core/context.js';
import { clamp, lerp, smooth, noise1, fbm1, hash1, ease } from '../core/util.js';
import { VoidHand, Cuff } from './void_parts.js';

const TAU = Math.PI * 2;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const toV = (a) => (a instanceof THREE.Vector3 ? a.clone() : new THREE.Vector3(a[0], a[1], a[2]));
const _e = new THREE.Euler(), _q = new THREE.Quaternion(), _m4 = new THREE.Matrix4();

// ---------------------------------------------------------------------------------------------------------
// Proportions (rest, metres, root space: feet on y=0, facing +Z, +X = the Void's left)
const NA = 56;                 // body columns (around)
const NR = 54;                 // body rows (profile samples: underside -> hem -> up to the neck)
const FSTEP = 0.1, FK = 28;    // spine frames every 10 cm (0 .. 2.7 m)
const SZ = 0.9;                // body depth / width
const NECK_Y = 1.66, HEAD_UP = 0.5, HEAD_FWD = 0.1;     // hood centre at rest ≈ (0, 2.16, 0.12)
const CHEST_Y = 1.05, SHOULDER_Y = 1.42, HIP_Y = 0.4;
const FR = [0.62, 0.58, 0.33], FC = [0, -0.05, 0.05];     // face-field ellipsoid (head-local)
const HOOD = { rx: 0.82, ry: 0.79, rz: 0.8, phi0: 1.0, roll: 0.09, tilt: 0.08, peak: 0.3 };
// shoulder capelet profile [radius, height]: from inside the hood, over the shoulders, scalloped hem, lip tucked in
const CAPE = [[0.3, 1.9], [0.58, 1.8], [0.75, 1.64], [0.9, 1.5], [0.985, 1.37], [1.035, 1.265], [1.06, 1.19], [1.04, 1.155], [0.995, 1.165], [0.955, 1.21]];
const NCR = 22, CAPE_LIP = [[-0.025, -0.035], [-0.07, -0.03], [-0.11, 0.015]];   // lip offsets [dr, dy] from the hem
const ARM_L1 = 0.64, ARM_L2 = 0.6, HAND = 0.44;
const ARM_R = [0.235, 0.215, 0.19, 0.165, 0.15];          // sleeve tube shoulder -> wrist (the cuff flares over the end)
const LEG_LEN = 0.42, FOOT = [0.215, 0.165, 0.25], LEG_R = [0.29, 0.275, 0.25];
const KICK_LEN = 0.66;                                     // hip -> ankle of the kicking leg at full extension
const MOUTH_V = -0.44;
const DECAL_UV = [-0.8, 0.8, -1.2, 0.05], DECAL_K = 1.7;  // face decal extent (u0, u1, v0, v1) and its colour gain
// profile [radius, height] from the underside centre, round the hem lip, up to the neck (inside the hood)
const PROFILE = [[0.0, 0.34], [0.42, 0.31], [0.76, 0.23], [0.93, 0.15], [1.0, 0.11], [1.05, 0.18], [1.09, 0.38],
  [1.1, 0.62], [1.06, 0.9], [0.96, 1.15], [0.8, 1.37], [0.61, 1.54], [0.41, 1.68], [0.2, 1.8], [0.0, 1.86]];

// walk styles: stride = one foot's travel per half cycle (body speed = 2*stride*cycles/s)
const WALK = {
  walk: { stride: 0.42, lift: 0.13, bob: 0.03, roll: 0.07, twist: 0.05, lean: 0.03, sway: 0.05, arm: 0.16 },
  waddle: { stride: 0.38, lift: 0.11, bob: 0.035, roll: 0.105, twist: 0.06, lean: 0.02, sway: 0.075, arm: 0.12 },
  run: { stride: 0.66, lift: 0.24, bob: 0.075, roll: 0.06, twist: 0.08, lean: 0.17, sway: 0.04, arm: 0.3 },
  stomp: { stride: 0.4, lift: 0.24, bob: 0.06, roll: 0.09, twist: 0.04, lean: 0.06, sway: 0.06, arm: 0.1 },
  sneak: { stride: 0.3, lift: 0.08, bob: 0.015, roll: 0.05, twist: 0.03, lean: 0.12, sway: 0.03, arm: 0.05 },
};

// Arm presets for the LEFT arm (mirrored for R). Body presets: p = wrist in the chest frame (rest y = CHEST_Y),
// dirs in the chest frame. head:true presets are in head-local space (follow the hood).
// `like` presets only define the hand shape/orientation and expect arm.target (fallback = `like` position).
export const ARM = {
  rest: { p: [1.2, -0.33, 0.25], fingers: [0.15, -1, 0.15], palm: [-1, 0, 0.12], pole: [0.7, 0, -1], hand: { curl: 0.32, spread: 0.12, thumb: 0.25, cup: 0.25 } },
  hips: { p: [1.16, -0.12, 0.1], fingers: [-0.3, -0.5, 1], palm: [-1, 0.2, 0], pole: [0.6, 0.3, -1], hand: { curl: 0.95, thumb: 0.1 } },
  belly: { p: [0.42, -0.23, 0.99], fingers: [-0.85, -0.4, 0.2], palm: [-0.15, 0.05, -1], pole: [1, -0.5, 0.1], hand: { curl: 0.25, spread: 0.35, cup: 0.45, thumb: 0.55 } },
  // folded arms: shoulders roll forward, lower (left) forearm on the belly, right forearm stacked over it in front;
  // each hand tucks past the centre toward the other elbow (pR / fingersR... = the right arm's own values)
  crossed: { p: [-0.32, -0.08, 0.95], pR: [-0.3, 0.1, 1.03], fingers: [-0.4, -0.2, -0.9], fingersR: [-0.45, -0.35, -0.8], palm: [0.7, -0.2, -0.65], palmR: [0.6, -0.5, -0.6],
    pole: [0.6, -0.85, 0.85], shFwd: 0.3, stretch: 1.4, hs: 0.8, hand: { curl: 0.88, spread: 0.02, thumb: 0.1, cup: 0.5 } },
  up: { p: [0.8, 1.5, 0.35], fingers: [0.15, 1, 0.1], palm: [0, 0, 1], pole: [1, 0, -0.4], hand: { curl: 0.08, spread: 0.45, thumb: 0.65 } },
  shrug: { p: [1.15, 0.0, 0.66], fingers: [0.55, 0.2, 0.8], palm: [0.15, 1, 0.1], pole: [0.8, -1, -0.4], hand: { curl: 0.12, spread: 0.45, thumb: 0.85, cup: 0.15 } },
  wave: { p: [1.08, 1.0, 0.45], fingers: [0.1, 1, 0.1], palm: [0, 0, 1], pole: [1, -0.6, -0.4], hand: { curl: 0.05, spread: 0.5, thumb: 0.7 } },
  open: { p: [1.05, -0.02, 0.86], fingers: [0.45, 0.25, 1], palm: [0.25, 1, -0.1], pole: [1, -0.8, -0.3], hand: { curl: 0.12, spread: 0.4, thumb: 0.7 } },
  point: { p: [0.75, 0.35, 1.15], fingers: [0.2, 0.1, 1], palm: [-1, 0, 0], pole: [1, -0.5, -0.3], hand: { point: 1, thumb: 0.2 } },
  fist: { p: [1.0, -0.2, 0.55], fingers: [0, 0.3, 1], palm: [-1, 0, 0], pole: [1, -0.6, -0.3], hand: { curl: 1, thumb: 0.1 } },
  hold: { p: [0.65, -0.05, 1.05], fingers: [-0.5, 0.2, 1], palm: [-0.4, 0.8, 0], pole: [1, -0.7, -0.2], hand: { curl: 0.35, cup: 0.6, spread: 0.2, thumb: 0.5 } },
  whisper: { head: true, p: [0.5, -0.42, 0.56], fingers: [-0.1, 1, 0.3], palm: [-1, 0, 0.2], pole: [1, -1, 0], hand: { curl: 0.35, cup: 0.9, spread: 0.06, thumb: 0.15 } },
  cover_mouth: { head: true, p: [0.24, -0.58, 0.68], fingers: [-0.75, 0.6, 0], palm: [0, 0, -1], pole: [1, -1, 0], hand: { curl: 0.15, cup: 0.4 } },
  chin: { head: true, p: [0.16, -0.86, 0.5], fingers: [-0.25, 1, 0.3], palm: [0, 0.2, -1], pole: [1, -1, 0.2], hand: { curl: 0.75, thumb: 0.3 } },
  // target-driven contact shapes: `target` (or `on` + `at`) is where the PALM CENTRE goes (tip: the index fingertip)
  pat: { like: 'rest', at: 'palm', palm: [0, -1, -0.1], fingers: [0.1, -0.45, 1], pole: [1, -0.4, -0.6], hand: { curl: 0.1, cup: 0.42, spread: 0.16, thumb: 0.35 } },
  around: { like: 'rest', at: 'palm', palm: [-0.1, -1, -0.15], fingers: [0.15, -0.55, 1], pole: [0.25, 0.85, -1], hand: { curl: 0.24, cup: 0.6, spread: 0.12, thumb: 0.4 } },
  tip: { like: 'rest', at: 'tip', palm: [0, -1, 0.2], hand: { point: 1, thumb: 0.25 } },
  reach: { like: 'rest', at: 'palm', palm: [0, -0.4, 1], fingers: [0, 0.3, 1], hand: { curl: 0.1, spread: 0.3, thumb: 0.5 } },
};

// ---------------------------------------------------------------------------------------------------------
// Void expression presets (Face params tuned for this face: no teeth, starlight lids, nebula brows).
// Void-only params that may ride inside face params: `puff` (0..1 huff cheeks), `mDroop` (0..1 corners droop while
// the centre still smiles: sad smile), `mWavy` (0..1 squiggly uneasy mouth line: awkward).
export const VOID_EXPR = {
  neutral: { lidU: 0.96, lidL: 0.12, browIn: 0.06 },
  calm: { lidU: 0.84, lidL: 0.25, mSmile: 0.14, browIn: 0.14, browOut: -0.05 },
  listen: { lidU: 1.08, lidL: 0.05, browIn: 0.4, browOut: 0.1, browAsym: 0.3, mPress: 0.25, mSmile: 0.05 },
  curious: { lidU: 1.12, browIn: 0.45, browOut: 0.35, browAsym: 0.45, mRound: 0.3, mOpen: 0.06 },
  gentle: { mSmile: 0.56, lidL: 0.24, lidU: 0.95, browIn: 0.6, browOut: -0.04, lidSad: 0.06, blush: 0.28, wet: 0.5 },
  happy: { mSmile: 0.9, mOpen: 0.14, mWide: 0.2, lidL: 0.68, lidU: 0.82, browIn: 0.28, browOut: 0.32, blush: 0.3 },
  laugh: { mSmile: 1, mOpen: 0.95, mWide: 0.85, lidL: 1, lidU: 0.42, browIn: 0.55, browOut: 0.8, blush: 0.35, saccade: 0 },
  giggle: { mSmile: 1, mOpen: 0.3, mWide: 0.25, lidL: 0.95, lidU: 0.5, browIn: 0.5, browOut: 0.22, blush: 0.35 },
  whisper: { mOpen: 0.2, mRound: 0.75, mWide: -0.35, lidU: 0.7, lidL: 0.32, browIn: 0.35, browOut: -0.1, browAsym: 0.25 },
  sideeye: { lidU: 0.56, lidL: 0.42, browIn: -0.4, browSq: 0.5, browAsym: -0.35, mPress: 0.55, mSmile: -0.25, mAsym: -0.35, gazeYaw: -0.62, saccade: 0.3 },
  scowl: { lidAngry: 1.35, lidU: 0.66, lidL: 0.42, browIn: -1, browSq: 1, browOut: 0.3, mSmile: -0.8, mPress: 0.55, mWide: 0.2, mOpen: 0.03 },
  annoyed: { lidU: 0.55, lidL: 0.18, browIn: -0.3, browSq: 0.45, mPress: 0.6, mSmile: -0.35, mAsym: 0.25 },
  huff: { lidAngry: 0.7, lidU: 0.5, lidL: 0.5, browIn: -0.75, browSq: 0.85, browOut: 0.25, mPress: 0.8, mPout: 0.9, mSmile: -0.3, puff: 1 },
  sadSmile: { mSmile: 0.34, mDroop: 0.5, browIn: 1.1, browOut: -0.35, browSq: 0.12, lidSad: 0.32, lidU: 0.93, lidL: 0.16, wet: 0.85 },
  sad: { mSmile: -0.75, mPout: 0.2, browIn: 1.05, browOut: -0.45, browSq: 0.2, lidSad: 0.75, lidU: 0.66 },
  innocent: { lidU: 1.16, lidL: 0.06, browIn: 0.65, browOut: 0.6, mSmile: 0.28, mPress: 0.35, mRound: 0.12, gazePitch: 0.2, gazeYaw: 0.28, saccade: 0.3 },
  surprised: { lidU: 1.42, browIn: 0.85, browOut: 0.95, mOpen: 0.5, mRound: 0.6, pupil: 0.8 },
  wonder: { lidU: 1.18, lidL: 0.1, browIn: 0.62, browOut: 0.38, mOpen: 0.16, mRound: 0.3, mSmile: 0.4, pupil: 1.25, wet: 0.6 },
  proud: { mSmile: 0.66, lidU: 0.8, lidL: 0.45, browIn: 0.2, browOut: 0.4, browAsym: 0.22, blush: 0.35 },
  peripheral: { lidU: 0.8, lidL: 0.34, browIn: -0.12, browSq: 0.28, mPress: 0.3, mSmile: 0.12, gazeYaw: -0.66, saccade: 0 },
  determined: { lidAngry: 0.8, lidU: 0.62, lidL: 0.48, browIn: -0.55, browSq: 0.7, mPress: 0.75, mSmile: -0.12 },
  smug: { lidU: 0.66, lidL: 0.4, lidAsym: -0.34, mSmile: 0.42, mAsym: 1.0, mShift: 0.3, browAsym: 0.6, browSq: 0.12 },
  tender: { mSmile: 0.45, lidU: 0.9, lidL: 0.3, lidSad: 0.1, browIn: 0.55, browOut: -0.05, blush: 0.3, wet: 0.4 },
  awkward: { mSmile: 0.04, mWide: 0.8, mWavy: 1, mPress: 0.3, mAsym: 0.12, browIn: 0.9, browOut: 0.3, browAsym: 0.15, lidU: 1.12, lidSad: 0.12, saccade: 1 },
  flinch: { lidU: 1.35, lidL: 0.1, browIn: 0.9, browOut: 0.5, browSq: 0.3, mOpen: 0.22, mRound: 0.35, mSmile: -0.3, pupil: 0.75 },
  hopeful: { lidU: 1.1, browIn: 0.55, browOut: 0.25, mSmile: 0.35, lidL: 0.15, wet: 0.3 },
};

/**
 * Whisper bend preset: side = +1 leans toward its LEFT (+X), -1 toward its right; depth scales the bend.
 * Mouth height (anchor 'mouth', yaw 0, measured with void_probe): depth 0 -> 1.86 m, 0.6 -> 1.77, 0.8 -> 1.74,
 * 1.0 -> 1.70, 1.1 -> 1.61, 1.2 -> 1.52, 1.3 -> 1.42 (above 1 the knees fold, the body tips further and the hood nods
 * down). Returns { body, head, armL|armR } to merge into a pose. v.solveWhisper() finds depth + position for an ear.
 * Pair with v.solvePos(t, pose, 'whisper', listenerEar) to put the Void's mouth right at someone's ear.
 */
export function whisperPose(side = 1, depth = 1, amount = 1) {
  const k = amount, d = depth, dd = Math.max(0, d - 1);
  const arm = { preset: 'whisper', from: 'rest', mix: clamp(amount * 1.4 - 0.2) };
  return {
    body: { lean: (0.5 * d + 0.25 * dd) * k, crouch: (0.16 * d + 0.8 * dd) * k, tilt: (0.2 + 0.1 * dd) * side * k, twist: 0.12 * side * k },
    head: { yaw: 0.32 * side * k, pitch: (-(0.1 + 0.42 * d) + 0.5 * dd) * k, roll: 0.16 * side * k },
    ...(side > 0 ? { armL: arm } : { armR: arm }),
  };
}

/** VX('scowl', { mOpen: 0.1 }) -> full flat face params for the Void (array form [[name, w], ...] blends). */
export function VX(name, over = {}) {
  const base = { ...FACE_DEFAULTS, puff: 0, mDroop: 0, mWavy: 0, mTeethU: 0, mTeethL: 0, mTongue: 0 };
  if (typeof name === 'string') Object.assign(base, VOID_EXPR[name] || {});
  else for (const [nm, w] of name) for (const [key, val] of Object.entries(VOID_EXPR[nm] || {})) base[key] += (val - (FACE_DEFAULTS[key] ?? 0)) * w;
  return Object.assign(base, over);
}

/**
 * Eye-roll helper: u = progress 0..1 of a ~0.9 s roll. Returns face param overrides (merge over an expression).
 * The gaze sweeps from one side, up and over the top, to the other side, lids lifting with it, then settling
 * annoyed. dir = +1 starts at its LEFT and ends at its RIGHT (screen: right -> left when it faces camera); -1 mirrors.
 */
export function eyeRoll(u, dir = 1) {
  const a = lerp(Math.PI + 0.45, -0.25, ease.inOut(clamp(u)));
  const top = Math.max(0, Math.sin(a));
  return { gazeYaw: -dir * 0.58 * Math.cos(a), gazePitch: 0.5 * Math.sin(a), lidU: lerp(0.62, 1.0, top), lidL: 0.15, browIn: 0.15 + 0.35 * top, browOut: 0.25 * top, saccade: 0, autoBlink: 0 };
}

// ---------------------------------------------------------------------------------------------------------
// Shaders
const VGLSL = /* glsl */`
float vd_h1(vec3 p){ p = fract(p * vec3(0.1031, 0.1030, 0.0973)); p += dot(p, p.yxz + 33.33); return fract((p.x + p.y) * p.z); }
vec3 vd_h3(vec3 p){ p = fract(p * vec3(0.1031, 0.1030, 0.0973)); p += dot(p, p.yxz + 33.33); return fract((p.xxy + p.yxx) * p.zyx); }
float vd_n(vec3 x){ vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(vd_h1(i), vd_h1(i + vec3(1,0,0)), f.x), mix(vd_h1(i + vec3(0,1,0)), vd_h1(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(vd_h1(i + vec3(0,0,1)), vd_h1(i + vec3(1,0,1)), f.x), mix(vd_h1(i + vec3(0,1,1)), vd_h1(i + vec3(1,1,1)), f.x), f.y), f.z); }
float vd_fbm(vec3 p){ return vd_n(p) * 0.57 + vd_n(p * 2.03 + 7.1) * 0.29 + vd_n(p * 4.1 + 3.3) * 0.14; }
float vd_stars(vec3 q, float thr, float rad, float t){
  vec3 c = floor(q), f = fract(q);
  vec3 h = vd_h3(c);
  float on = step(thr, vd_h1(c + 17.31));
  float d = length(f - (0.2 + 0.6 * h));
  float tw = 0.65 + 0.35 * sin(t * (0.6 + 1.2 * h.x) + h.y * 40.0);
  return on * smoothstep(rad, 0.0, d) * tw;
}
// fabric stars: varied size & brightness (mostly faint, a rare brighter "hero"); returns (brightness, tint 0..1)
vec2 vd_starsV(vec3 q, float thr, float rad, float t){
  vec3 c = floor(q), f = fract(q);
  vec3 h = vd_h3(c);
  float on = step(thr, vd_h1(c + 17.31));
  float d = length(f - (0.2 + 0.6 * h));
  float r = rad * (0.6 + 0.8 * h.y);
  float b = 0.28 + 0.72 * h.z * h.z * h.z + 1.6 * step(0.975, h.x);
  float tw = 0.7 + 0.3 * sin(t * (0.5 + 1.0 * h.x) + h.y * 40.0);
  return vec2(on * smoothstep(r, 0.0, d) * b * tw, h.y);
}`;

// Velvet: MeshStandard + fake key-lit violet sheen + stars inside the fabric (parallax in root space) +
// violet->teal fresnel rim (HDR, bloom-friendly) + faint nebula shimmer. `U` uniforms are shared by all parts.
function velvetMaterial(U) {
  // MeshLambert (per-pixel diffuse only: velvet has no real specular, and GGX is the expensive part on SwiftShader)
  // + a cheap key-light-aware velvet sheen, rim, nebula and fabric stars in the emissive block.
  const m = new THREE.MeshLambertMaterial({ color: 0x1b143c });
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U, { uKeyColor: EYE_LIGHT.uKeyColor, uTime: GLOBAL.uTime });
    sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
      varying vec3 vLp; varying vec3 vVd; varying float vShm; uniform mat4 uRootInv; uniform float uTime;
      ${VGLSL}`)
      .replace('#include <project_vertex>', `#include <project_vertex>
      vec3 vw_ = (modelMatrix * vec4(transformed, 1.0)).xyz;
      vLp = (uRootInv * vec4(vw_, 1.0)).xyz;
      vVd = mat3(uRootInv) * normalize(vw_ - cameraPosition);
      vShm = vd_n(vLp * 1.6 + vec3(0.0, uTime * 0.06, uTime * 0.035));`);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
      varying vec3 vLp; varying vec3 vVd; varying float vShm; uniform float uTime, uStars, uCosmos, uRimK, uNeb, uSheen;
      uniform vec3 uRimA, uRimB, uStarA, uStarB, uSheenC, uKeyView, uKeyColor;
      ${VGLSL}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      {
        vec3 nn = normalize(normal);
        float nv = clamp(dot(nn, normalize(vViewPosition)), 0.0, 1.0);
        float fr = 1.0 - nv;
        float frs = fr * sqrt(fr), fr2 = fr * fr;
        float shm = vShm;
        totalEmissiveRadiance += diffuseColor.rgb * 0.05 + vec3(0.29, 0.196, 0.75) * (0.16 * frs);   // glow + wrap
        // velvet sheen: grazing-angle violet, stronger on the key-lit side
        float lit = clamp(dot(nn, uKeyView) * 0.6 + 0.4, 0.0, 1.0);
        totalEmissiveRadiance += uSheenC * uKeyColor * (fr2 * sqrt(fr) * uSheen * (0.15 + 0.85 * lit));
        float rim = fr2 * frs * uRimK * (0.7 + 0.6 * shm);
        vec3 rc = mix(uRimA, uRimB, clamp(smoothstep(0.5, 0.97, fr) * 0.75 + 0.35 * smoothstep(0.42, 0.72, shm), 0.0, 1.0));
        totalEmissiveRadiance += rc * rim;
        float cz = 1.0 + 3.0 * uCosmos;
        // faint stars drifting INSIDE the fabric (parallax), tinted violet/teal, fading out toward the silhouette
        vec2 st = vd_starsV((vLp + vVd * 0.16) * 5.4 + vec3(0.0, uTime * 0.025, 0.0), 0.42, 0.12, uTime);
        totalEmissiveRadiance += mix(uStarA, uStarB, st.y) * (st.x * uStars * cz * smoothstep(0.08, 0.6, nv));
        float neb = smoothstep(0.55, 0.85, shm);
        totalEmissiveRadiance += mix(vec3(0.22, 0.08, 0.48), vec3(0.04, 0.32, 0.42), shm) * neb * uNeb * cz;
      }`);
  };
  m.customProgramCacheKey = () => 'voidVelvet5';
  return m;
}

// Face darkness (face field, hood lining, eyelids): unlit deep cosmos; pattern computed in head space from the
// direction around the face centre. Darkens toward the hood edge. The LID variant (eyelids + canthus caps) first
// projects each point along the view ray onto the face ellipsoid and samples the face decal (blush, puff glows)
// there, so lids show exactly what the field behind them would: blinks read as the darkness itself closing.
const FACE_VS = /* glsl */`uniform mat4 uHeadInv; uniform vec3 uC, uR; uniform float uTime;
varying vec3 vLp; varying vec2 vN;
${VGLSL}
void main(){ vec4 w = modelMatrix * vec4(position, 1.0);
  vec3 lp = (uHeadInv * w).xyz;
#ifdef LID
  vec3 cam = (uHeadInv * vec4(cameraPosition, 1.0)).xyz;
  vec3 rd = normalize(lp - cam);
  vec3 o = (cam - uC) / uR, dd = rd / uR;
  float A = dot(dd, dd), B = dot(o, dd), Cq = dot(o, o) - 1.0, disc = B * B - A * Cq;
  if (disc > 0.0) lp = cam + rd * ((-B - sqrt(disc)) / A);
#endif
  vLp = lp;
  vec3 d = normalize(lp - uC);
  vN = vec2(vd_n(d * 2.6 + vec3(0.0, uTime * 0.03, uTime * 0.02)), vd_n(d * 4.6 + vec3(5.2, -uTime * 0.025, 1.3)));
  gl_Position = projectionMatrix * viewMatrix * w; }`;
const FACE_FS = /* glsl */`
uniform mat4 uHeadInv; uniform vec3 uC, uR; uniform vec2 uOpen, uHalo; uniform vec4 uEyeP; uniform float uTime, uCosmos, uBright, uHoodGlow;
#ifdef LID
uniform sampler2D uDecal; uniform vec4 uDecalUV; uniform float uDecalK;
#endif
varying vec3 vLp; varying vec2 vN;
${VGLSL}
void main(){
  vec3 lp = vLp;
  vec3 d = normalize(lp - uC);
  float cz = 1.0 + 2.5 * uCosmos;
  float n1 = vN.x, n2 = vN.y;
  vec3 col = vec3(0.012, 0.010, 0.036);
  vec3 neb = mix(vec3(0.24, 0.07, 0.52), vec3(0.03, 0.34, 0.44), smoothstep(0.35, 0.7, n2));
  col += neb * smoothstep(0.42, 0.88, n1) * 0.075 * cz * uBright;
  float st = vd_stars(d * 19.0 + vec3(0.0, uTime * 0.04, 0.0), 0.55, 0.2, uTime);
  col += mix(vec3(0.8, 0.74, 1.0), vec3(0.6, 0.95, 1.0), n2) * st * 0.36 * cz * uBright;
  float e = length(lp.xy / uOpen);
  col *= mix(1.0, 0.05, smoothstep(0.32, 0.95, e));
  // soft starlight halos around the eyes + a faint violet glow in the hood (analytic: no big additive sprites)
  vec2 dl = lp.xy - uEyeP.xy, dr = lp.xy - uEyeP.zw, dc = lp.xy - vec2(0.0, -0.05);
  col += vec3(0.38, 0.75, 1.0) * (uHalo.x * exp(-dot(dl, dl) / 0.0225) + uHalo.y * exp(-dot(dr, dr) / 0.0225));
  col += vec3(0.16, 0.08, 1.0) * uHoodGlow * exp(-dot(dc, dc) / 0.07);
#ifdef LID
  vec3 q = (lp - uC) / uR;
  vec2 uv = vec2((atan(q.x, q.z) - uDecalUV.x) / (uDecalUV.y - uDecalUV.x), (asin(clamp(q.y, -1.0, 1.0)) - uDecalUV.z) / (uDecalUV.w - uDecalUV.z));
  if (uv.x > 0.0 && uv.x < 1.0 && uv.y > 0.0 && uv.y < 1.0) { vec4 dc = texture2D(uDecal, uv); col = mix(col, dc.rgb * uDecalK, dc.a); }
#endif
  gl_FragColor = vec4(col, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// Nebula wisp glow (brows, foot pads): additive, soft fresnel edge, violet (centre) -> teal (outer) along |x|.
const WISP_VS = /* glsl */`varying vec3 vN; varying vec3 vV; varying vec3 vP;
void main(){ vP = position; vN = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(position, 1.0); vV = -mv.xyz; gl_Position = projectionMatrix * mv; }`;
const WISP_FS = /* glsl */`uniform vec3 uA, uB; uniform float uI, uSoft, uTime, uX0, uX1, uShim;
varying vec3 vN; varying vec3 vV; varying vec3 vP;
void main(){
  float f = pow(clamp(abs(dot(normalize(vN), normalize(vV))), 0.0, 1.0), uSoft);
  vec3 c = mix(uA, uB, smoothstep(uX0, uX1, abs(vP.x)));
  float sh = 1.0 + uShim * (-0.18 + 0.18 * sin(vP.x * 60.0 - uTime * 1.6) * sin(vP.y * 45.0 + uTime * 1.1));
  gl_FragColor = vec4(c * uI * f * sh, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function wispMaterial(o) {
  return new THREE.ShaderMaterial({
    uniforms: { uA: { value: new THREE.Color(o.a ?? 0x9a6cff) }, uB: { value: new THREE.Color(o.b ?? 0x52e0f0) }, uI: { value: o.i ?? 2 },
      uSoft: { value: o.soft ?? 1.2 }, uTime: GLOBAL.uTime, uX0: { value: o.x0 ?? 0.08 }, uX1: { value: o.x1 ?? 0.3 }, uShim: { value: o.shim ?? 1 } },
    vertexShader: WISP_VS, fragmentShader: WISP_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  });
}

// ---------------------------------------------------------------------------------------------------------
// Geometry builders
function hoodGeometry(H) {
  // Lathe around +Z (the face axis). Each column psi gets its own profile, so the opening is a soft shield shape
  // (tall arch at the top, a slight off-centre V at the chin) rather than a porthole, and its edge is a deep cowl
  // in profile: brim forward over the brow, sides set back, chin edge drawn forward and down. The rolled brim is
  // thick at the top and thin at the sides. A teardrop peak droops at the top-back. Rows: outer shell (back pole ->
  // opening edge), rolled brim, then the lining going back into the dark (lining = material group 1).
  const NO = 28, NRL = 9, LIN = [[-0.004, -0.05], [-0.018, -0.15], [-0.036, -0.29], [-0.06, -0.45], [-0.09, -0.62], [-0.14, -0.8], [-0.21, -0.98]];
  const NS = 64, NP = NO + 1 + NRL + LIN.length;
  const parts = (psi) => {
    const up = Math.sin(psi), cs = Math.cos(psi);
    const vb = Math.max(0, -Math.sin(psi - 0.1));                          // V notch, a touch off-centre
    return { top: Math.max(0, up), bot: Math.max(0, -up), cs2: cs * cs, vb };
  };
  const profFor = (psi) => {
    const { top, bot, cs2, vb } = parts(psi);
    const phi0 = H.phi0 + 0.1 * top ** 2.5 + 0.035 * cs2 - 0.035 * bot ** 2 + 0.07 * vb ** 10;
    const prof = [];
    for (let i = 0; i <= NO; i++) { const phi = Math.PI - (Math.PI - phi0) * (i / NO); prof.push([Math.sin(phi), Math.cos(phi), i < NO ? 1 : 0]); }
    const e = prof[prof.length - 1], rr = H.roll * (0.82 + 0.6 * top ** 1.5 - 0.12 * cs2 + 0.12 * bot);
    for (let i = 1; i <= NRL; i++) { const a = Math.PI * i / NRL; prof.push([e[0] - rr + rr * Math.cos(a), e[1] + rr * 1.25 * Math.sin(a), 0]); }
    const l0 = prof[prof.length - 1];
    for (const [dr, dz] of LIN) prof.push([l0[0] + dr, l0[1] + dz, 0]);
    return prof;
  };
  const pos = new Float32Array(NP * (NS + 1) * 3);
  const peak = new THREE.Vector3(0, 0.66, -0.75).normalize();
  const c = Math.cos(H.tilt), s = Math.sin(H.tilt);
  const d = new THREE.Vector3();
  const rim = [];
  for (let j = 0; j <= NS; j++) {
    const psi = -Math.PI / 2 + TAU * j / NS;
    const prof = profFor(psi), { top, bot, cs2 } = parts(psi);
    for (let i = 0; i < NP; i++) {
      const [r, z, outer] = prof[i];
      let x = r * Math.cos(psi) * H.rx, y = r * Math.sin(psi) * H.ry, zz = z * H.rz;
      if (i >= NO - 9) {   // cowl edge: brim overhangs at the top, sides set back, chin edge forward and down
        const k = i >= NO ? 1 : smooth((i - (NO - 9)) / 9);
        zz += (0.19 * top * top - 0.07 * cs2 + 0.12 * bot * bot) * k;
        y -= (0.05 * top * top + 0.07 * bot * bot) * k;
      }
      if (outer) {
        // teardrop: a soft rounded peak at the top-back that droops backward (reads as a hood from behind / side)
        d.set(x / H.rx, y / H.ry, zz / H.rz).normalize();
        const w = Math.pow(Math.max(0, d.dot(peak)), 3);
        x *= 1 - 0.3 * w; y += w * H.peak; zz -= w * w * H.peak * 1.3;
        x *= 1 + 0.03 * Math.abs(d.x);
        // the bottom-back of the hood drapes down onto the shoulders (tucks under the collar roll)
        if (d.y < 0) { const b = Math.pow(-d.y, 2) * Math.max(0, -d.z + 0.3); y *= 1 + 0.06 * b; x *= 1 + 0.06 * b; zz *= 1 + 0.05 * b; }
      }
      const y2 = y * c - zz * s, z2 = y * s + zz * c;
      pos.set([x, y2, z2], (i * (NS + 1) + j) * 3);
      if (i === NO + Math.floor(NRL / 2)) rim[j] = new THREE.Vector3(x, y2, z2);
    }
  }
  const nLin = NO + 1 + Math.ceil(NRL * 0.55);   // inner half of the brim roll is already in the dark
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const idx = [];
  for (let i = 0; i < NP - 1; i++) for (let j = 0; j < NS; j++) {
    const a = i * (NS + 1) + j, b = a + 1, cc = a + NS + 1, dd = cc + 1;
    idx.push(a, b, cc, b, dd, cc);
  }
  g.setIndex(idx);
  g.addGroup(0, (nLin - 1) * NS * 6, 0);
  g.addGroup((nLin - 1) * NS * 6, (NP - nLin) * NS * 6, 1);
  g.computeVertexNormals();
  seamFix(g, NP, NS + 1);
  // rim(psi): head-local point on the crest of the rolled brim (for the overlap fold)
  g.userData.rim = (psi) => { let f = ((psi + Math.PI / 2) / TAU) * NS; f = ((f % NS) + NS) % NS; const j = Math.floor(f), u = f - j; return rim[j].clone().lerp(rim[j + 1], u); };
  return g;
}

// average normals of the first & last column of a (rows x cols) grid (closing a lathe seam)
function seamFix(g, rows, cols) {
  const n = g.attributes.normal.array;
  for (let r = 0; r < rows; r++) {
    const a = (r * cols) * 3, b = (r * cols + cols - 1) * 3;
    let x = n[a] + n[b], y = n[a + 1] + n[b + 1], z = n[a + 2] + n[b + 2];
    const l = Math.hypot(x, y, z) || 1; x /= l; y /= l; z /= l;
    n[a] = n[b] = x; n[a + 1] = n[b + 1] = y; n[a + 2] = n[b + 2] = z;
  }
  g.attributes.normal.needsUpdate = true;
}

function surfaceGeometry(surface, u0, u1, v0, v1, nu, nv) {
  const pos = [], idx = [];
  for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) {
    const { p } = surface(lerp(u0, u1, i / nu), lerp(v0, v1, j / nv));
    pos.push(p.x, p.y, p.z);
  }
  for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) {
    const a = j * (nu + 1) + i, b = a + 1, c = a + nu + 1, d = c + 1;
    idx.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

// ---------------------------------------------------------------------------------------------------------
export class Void extends Character {
  constructor() {
    super({ name: 'VOID', speaker: 'VOID', height: 3.0, seed: 23 });
    this.U = {
      uRootInv: { value: new THREE.Matrix4() }, uStars: { value: 1.0 }, uCosmos: { value: 0 }, uNeb: { value: 0.07 },
      uRimK: { value: 1.0 }, uRimP: { value: 2.7 }, uSheen: { value: 0.5 }, uKeyView: { value: new THREE.Vector3(0, 0, 1) }, uSheenC: { value: new THREE.Color(0.42, 0.2, 1.0) },
      uRimA: { value: new THREE.Color(0.55, 0.2, 1.25) }, uRimB: { value: new THREE.Color(0.12, 0.72, 0.95) },
      uStarA: { value: new THREE.Color(0.62, 0.46, 0.95) }, uStarB: { value: new THREE.Color(0.36, 0.7, 0.78) },
    };
    this.velvet = velvetMaterial(this.U);
    this.FU = { uHeadInv: { value: new THREE.Matrix4() }, uC: { value: new THREE.Vector3(...FC) }, uR: { value: new THREE.Vector3(...FR) }, uOpen: { value: new THREE.Vector2(0.6, 0.57) },
      uTime: GLOBAL.uTime, uCosmos: this.U.uCosmos, uBright: { value: 1 }, uHalo: { value: new THREE.Vector2() }, uEyeP: { value: new THREE.Vector4() }, uHoodGlow: { value: 0.1 } };
    this.faceMat = new THREE.ShaderMaterial({ uniforms: this.FU, vertexShader: FACE_VS, fragmentShader: FACE_FS });
    this.lidMat = new THREE.ShaderMaterial({ uniforms: { ...this.FU, uDecal: { value: null }, uDecalUV: { value: new THREE.Vector4(...DECAL_UV) }, uDecalK: { value: DECAL_K } },
      vertexShader: FACE_VS, fragmentShader: FACE_FS, defines: { LID: 1 } });
    this.browMat = wispMaterial({ a: 0xa070ff, b: 0x5ae6f2, i: 1.7, soft: 1.1 });
    this.browHaloMat = wispMaterial({ a: 0x7a4cff, b: 0x30c8e0, i: 0.75, soft: 2.2 });
    this.padMat = wispMaterial({ a: 0x9a70ff, b: 0x4ad8ee, i: 0.9, soft: 0.8, x0: 0.0, x1: 0.9, shim: 0 });
    this.F = { ax: new Float32Array(FK), ay: new Float32Array(FK), az: new Float32Array(FK), px: new Float32Array(FK), py: new Float32Array(FK), pz: new Float32Array(FK) };
    this.tipMat = new THREE.Matrix4();
    this._rootQInv = new THREE.Quaternion();
    this._buildBody();
    this._buildCape();
    this._buildHead();
    this._buildLimbs();
    this._buildFx();
    for (const n of ['chest', 'back', 'shoulderL', 'shoulderR', 'hip', 'footL', 'footR', 'kickFoot', 'sideL', 'sideR', 'backLow', 'hood']) this.addAnchor(n, this.root);
    // view-space key direction for the velvet sheen, from the camera that actually renders (set per draw)
    const kv = this.U.uKeyView.value;
    const obr = (r, sc, cam) => { kv.copy(EYE_LIGHT.uKeyDir.value).transformDirection(cam.matrixWorldInverse); };
    this.root.traverse((o) => { if (o.isMesh && (o.material === this.velvet || (Array.isArray(o.material) && o.material.includes(this.velvet)))) o.onBeforeRender = obr; });
    // perf (SwiftShader is fill-bound): only the body + hood cast shadows, and the parts that usually sit IN FRONT of
    // the big velvet body draw first so early-z rejects the body pixels they cover
    const opaque = (o) => o.isMesh && !(Array.isArray(o.material) ? o.material.some((m) => m.transparent) : o.material.transparent);
    this.root.traverse((o) => { if (o.isMesh) o.castShadow = false; });
    this.body.castShadow = true; this.hood.castShadow = true;
    this.headGroup.traverse((o) => { if (opaque(o)) o.renderOrder = -3; });
    this.hood.renderOrder = -2;
    for (const sd of ['L', 'R']) {
      this.arms[sd].group.traverse((o) => { if (opaque(o)) o.renderOrder = -2; });
      this.legs[sd].mesh.renderOrder = -1;
      this.feet[sd].group.traverse((o) => { if (opaque(o)) o.renderOrder = -1; });
    }
    this.cape.renderOrder = -1;
    this.update(0, {});
  }

  // ---------------------------------------------------------------- build
  _buildBody() {
    const curve = new THREE.CatmullRomCurve3(PROFILE.map(([r, y]) => new THREE.Vector3(r, y, 0)), false, 'centripetal');
    const pts = curve.getSpacedPoints(NR - 1);
    let iHem = 0; pts.forEach((p, i) => { if (p.y < pts[iHem].y) iHem = i; });
    this.rows = pts.map((p, i) => {
      const r = (i === 0 || i === NR - 1) ? 0 : Math.max(0, p.x), y = p.y, under = i < iHem;
      const g = (c, w) => Math.exp(-(((y - c) / w) ** 2));
      return {
        r, y, under,
        wHem: under ? smooth((r - 0.3) / 0.55) : smooth((0.62 - y) / 0.5),
        wLow: under ? smooth((r - 0.3) / 0.55) : smooth((1.05 - y) / 0.9),
        edge: under ? 0.6 * smooth((r - 0.7) / 0.25) : g(0.13, 0.08),
        wBelly: under ? 0 : g(0.75, 0.4), wChest: g(1.12, 0.4), wMid: g(0.88, 0.6), wSh: g(1.46, 0.2), wTop: under ? 0 : smooth((y - 1.32) / 0.35),
        // hem "curtain" lift profile: 1 at the hem, easing to 0 by ~1.25 m (monotonic: rows compress, never fold)
        fC: under ? smooth((r - 0.25) / 0.7) : 0.5 + 0.5 * Math.cos(Math.PI * clamp((y - 0.1) / 1.15)),
      };
    });
    const outer = this.rows.filter((rw) => !rw.under);
    const rAt0 = (y) => { // outer radius at rest height y
      for (let i = 1; i < outer.length; i++) if (outer[i].y >= y) { const u = (y - outer[i - 1].y) / (outer[i].y - outer[i - 1].y); return lerp(outer[i - 1].r, outer[i].r, u); }
      return 0;
    };
    const rTab = new Float32Array(301); for (let i = 0; i <= 300; i++) rTab[i] = rAt0(i / 100);
    this.rAt = (y) => { const f = clamp(y * 100, 0, 299.999), i = Math.floor(f); return lerp(rTab[i], rTab[i + 1], f - i); };
    this.cols = [];
    for (let a = 0; a <= NA; a++) {
      const th = Math.PI + TAU * a / NA;
      this.cols.push({ th, s: Math.sin(th), c: Math.cos(th), fold: Math.sin(7 * th + 0.6 * Math.sin(3 * th)) + 0.4 * Math.sin(13 * th + 1.1), scallop: Math.sin(9 * th + 1.3) });
    }
    this.hemLift = new Float32Array(NA + 1);
    const nv = NR * (NA + 1);
    this.bpos = new Float32Array(nv * 3);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.bpos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(nv * 3), 3).setUsage(THREE.DynamicDrawUsage));
    const idx = [];
    for (let r = 0; r < NR - 1; r++) for (let a = 0; a < NA; a++) {
      const A = r * (NA + 1) + a, B = A + 1, C = A + NA + 1, D = C + 1;
      idx.push(A, B, C, B, D, C);
    }
    g.setIndex(idx);
    this.bodyGeo = g;
    this.body = new THREE.Mesh(g, this.velvet);
    this.body.frustumCulled = false; this.body.castShadow = true;
    this.root.add(this.body);
    this._moteRows = [this.rows.findIndex((rw) => !rw.under && rw.y > 0.45), this.rows.findIndex((rw) => !rw.under && rw.y > 1.6)];
  }

  _buildCape() {
    // outer rows from the profile (down to the hem); the last CAPE_LIP rows are a rolled lip built per column
    // relative to the (possibly gathered-up) hem row, so the front opening edge keeps a soft thickness
    const curve = new THREE.CatmullRomCurve3(CAPE.slice(0, 7).map(([r, y]) => new THREE.Vector3(r, y, 0)), false, 'centripetal');
    const pts = curve.getSpacedPoints(NCR - 1 - CAPE_LIP.length);
    this.capeRows = pts.map((p) => ({ r: p.x, y: p.y, hem: smooth((1.36 - p.y) / 0.16), top: smooth((p.y - 1.4) / 0.32), sh: smooth((p.y - 1.15) / 0.5) }));
    this.capeR = (y) => { const o = CAPE.slice(0, 7); for (let i = 1; i < o.length; i++) if (o[i][1] <= y) { const u = (y - o[i][1]) / (o[i - 1][1] - o[i][1]); return lerp(o[i][0], o[i - 1][0], u); } return o[6][0]; };
    const nv = NCR * (NA + 1);
    this.cpos = new Float32Array(nv * 3);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(this.cpos, 3).setUsage(THREE.DynamicDrawUsage));
    g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(nv * 3), 3).setUsage(THREE.DynamicDrawUsage));
    const idx = [];
    // rows go DOWN the outside (opposite to the body), so flip the winding to face outward
    for (let r = 0; r < NCR - 1; r++) for (let a = 0; a < NA; a++) {
      const A = r * (NA + 1) + a, B = A + 1, C = A + NA + 1, D = C + 1;
      idx.push(A, C, B, B, C, D);
    }
    g.setIndex(idx);
    this.capeGeo = g;
    this.cape = new THREE.Mesh(g, this.velvet);
    this.cape.frustumCulled = false;
    this.root.add(this.cape);
  }

  _writeCape(D) {
    // open at the front like a cape: front columns gather the profile up toward the neck (under the hood)
    const pos = this.cpos, M = new THREE.Matrix4(), R = this.capeRows, NO = R.length;
    const radMul = 1 + D.breath * 0.01 + D.swell * 0.07 + D.shrug * 0.04 + D.crouch * 0.05;
    const P = (r, a, rho, ry, ly) => {   // write vertex (row r, column a)
      const col = this.cols[a], e = this._frameMat(ry, M).elements, k = (r * (NA + 1) + a) * 3;
      const lx = rho * col.s, lz = rho * col.c * SZ;
      pos[k] = e[0] * lx + e[4] * ly + e[8] * lz + e[12];
      pos[k + 1] = e[1] * lx + e[5] * ly + e[9] * lz + e[13];
      pos[k + 2] = e[2] * lx + e[6] * ly + e[10] * lz + e[14];
    };
    for (let a = 0; a <= NA; a++) {
      const col = this.cols[a];
      const fo = smooth((col.c - 0.62) / 0.33);
      let last = null;
      for (let r = 0; r < NO; r++) {
        const rf = r * (1 - 0.88 * fo), i0 = Math.min(NO - 2, Math.floor(rf)), u = rf - i0;
        const A0 = R[i0], A1 = R[i0 + 1];
        const ry = lerp(A0.y, A1.y, u), rr = lerp(A0.r, A1.r, u), hem = lerp(A0.hem, A1.hem, u), top = lerp(A0.top, A1.top, u), sh = lerp(A0.sh, A1.sh, u);
        let rho = rr * radMul * (1 + 0.014 * col.fold * hem + 0.012 * Math.sin(6 * col.th) * hem);
        if (col.c > 0) {
          rho *= 1 - 0.42 * top * Math.pow(col.c, 2);
          // toward the front opening the cape drapes flush onto the chest (no stand-off gap at its edges)
          const hug = this.rAt(ry) * (1 - 0.5 * smooth((ry - 1.32) / 0.35) * Math.pow(col.c, 1.5)) * radMul + 0.04;
          rho = lerp(rho, Math.min(rho, hug), smooth((col.c - 0.25) / 0.45));
        }
        const ly = hem * (0.035 * Math.sin(6 * col.th + 0.5) + 0.05 * col.c - 0.03) * (1 - fo) + D.shrug * 0.2 * sh + D.capeLift * hem;
        P(r, a, rho, ry, ly);
        last = { rho, ry, ly };
      }
      CAPE_LIP.forEach(([dr, dy], j) => P(NO + j, a, Math.max(0.05, last.rho + dr * (1 - 0.5 * fo)), last.ry, last.ly + dy));
    }
    const g = this.capeGeo;
    g.attributes.position.needsUpdate = true;
    g.computeVertexNormals();
    seamFix(g, NCR, NA + 1);
  }

  _buildHead() {
    this.headPivot = new THREE.Group(); this.root.add(this.headPivot);
    this.headGroup = new THREE.Group(); this.headGroup.position.set(0, HEAD_UP, 0); this.headPivot.add(this.headGroup);
    this.hood = new THREE.Mesh(hoodGeometry(HOOD), [this.velvet, this.faceMat]);
    this.hood.castShadow = true;
    this.headGroup.add(this.hood);
    // the cowl's one asymmetric overlap: the left side of the opening folds over the right at the chin
    { const rim = this.hood.geometry.userData.rim, P0 = -Math.PI / 2;
      const pts = [[1.3, 0.0, 0.0], [0.8, 0.06, -0.04], [0.3, 0.1, -0.09], [-0.2, 0.08, -0.1], [-0.6, 0.0, -0.06]]
        .map(([da, dz, dy]) => rim(P0 + da).add(V3(0, dy, dz)));
      this.fold = new SweepTube({ material: this.velvet, segments: 20, radial: 12, capRings: 3 });
      this.fold.update(pts, [0.035, 0.075, 0.09, 0.07, 0.03], { up: V3(0, -0.45, 1), flatten: 0.45 });
      this.headGroup.add(this.fold.mesh); }
    // soft fabric roll where the hood meets the capelet (back & sides only, tapering out before the face)
    this.collar = new SweepTube({ material: this.velvet, segments: 24, radial: 12, capRings: 3 });
    this.root.add(this.collar.mesh);
    const surface = ellipsoidSurface(FR, FC);
    this.surface = surface;
    this.faceField = new THREE.Mesh(surfaceGeometry(surface, -1.5, 1.5, -1.4, 1.35, 36, 32), this.faceMat);
    this.headGroup.add(this.faceField);
    // a dark "floor" under the face field so nothing below the head (neck, capelet, fold) peeks in under the chin
    this.chinPlug = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 10, 0, TAU, Math.PI * 0.35, Math.PI * 0.65), this.faceMat);
    this.chinPlug.scale.set(0.56, 0.16, 0.42); this.chinPlug.position.set(0, -0.6, 0.12);
    this.headGroup.add(this.chinPlug);
    const decalMat = new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, color: new THREE.Color(DECAL_K, DECAL_K, DECAL_K) });
    const self = this;
    this.face = new Face({
      head: this.headGroup, surface, seed: 23,
      eyes: { u: 0.37, v: 0.1, radius: 0.172, sink: 0.5, splay: 0.07, scale: [1, 1.1, 0.95], glow: 0.9,
        sclera: 0xdfe9ff, iris: 0x16288e, iris2: 0x1fa8c6, limbal: 0x050a30, pupilColor: 0x010208, irisR: 0.7, pupilR: 0.33,
        lidMaterial: this.lidMat, lash: 0, lowerLash: 0, catchlight: 0.8, lidGapU: 1.04, lidGapL: 1.04,
        upOpen: 0.74, upWide: 1.05, lowRelaxed: -0.8, lowRaised: 0.26, maxYaw: 0.72, maxPitch: 0.56 },
      brows: { material: this.browMat, thickness: 0.036, lift: 0.016, inner: [0.14, 0.43], mid: [0.36, 0.54], outer: [0.6, 0.45], range: 0.17, flatten: 0.25, profile: [0.5, 1.0, 0.85, 0.32] },
      mouth: {
        v: MOUTH_V, halfW: 0.15, line: 'rgba(0,0,0,0)', lineW: 0.013, lipTintRGB: '0,0,0', blushColor: '170,100,255',
        blushX: 0.32, blushY: 0.08, teeth: 'rgba(0,0,0,0)', animated: true,
        drawExtra: (g, p, t) => self._drawExtra(g, p, t),
      },
      decal: { uMin: DECAL_UV[0], uMax: DECAL_UV[1], vMin: DECAL_UV[2], vMax: DECAL_UV[3], size: [384, 320], lift: 0.004, material: decalMat },
    });
    // lids see the face decal (blush / puff glows). As the lids close / squint, the eye light fades into the darkness
    // toward the corners (socket space), so happy / closed eyes are tapered arcs of light with no white corner wedges.
    this.lidMat.uniforms.uDecal.value = this.face.decal.tex;
    for (const ey of this.face.eyes) {
      const u = ey.mat.uniforms;
      u.uSock = { value: new THREE.Matrix3() }; u.uCorner = { value: 0 };
      ey.mat.fragmentShader = ey.mat.fragmentShader
        .replace('uniform float uIrisR,', 'uniform mat3 uSock; uniform float uCorner; uniform float uIrisR,')
        .replace('gl_FragColor = vec4(lit, 1.0);', `vec3 sn = normalize(uSock * normalize(vWorldN));
  lit = mix(lit, vec3(0.012, 0.010, 0.036), clamp(uCorner * 1.4 * smoothstep(0.22, 0.56, abs(sn.x)), 0.0, 1.0));
  gl_FragColor = vec4(lit, 1.0);`);
      ey.mat.needsUpdate = true;
    }
    // eye halos + hood glow are analytic terms in the face shader (uHalo / uHoodGlow); eye centres in head space:
    this.FU.uEyeP.value.set(this.face.eyes[0].group.position.x, this.face.eyes[0].group.position.y, this.face.eyes[1].group.position.x, this.face.eyes[1].group.position.y);
    // brow halos (wider, fainter copies of the brow wisps)
    this.browHalo = this.face.brows.map(() => { const tb = new SweepTube({ material: this.browHaloMat, segments: 14, radial: 8, capRings: 3 }); this.headGroup.add(tb.mesh); return tb; });
    // head-space anchors
    const mp = surface(0, MOUTH_V);
    this.addAnchor('head', this.headGroup, [0, 0, 0]);
    const ep = surface(0, 0.1).p;
    this.addAnchor('eyes', this.headGroup, [0, ep.y, ep.z + 0.06]);
    this.addAnchor('mouth', this.headGroup, mp.p.clone().addScaledVector(mp.n, 0.03).toArray());
    this.addAnchor('mouthOut', this.headGroup, mp.p.clone().addScaledVector(mp.n, 0.6).toArray());
    this.addAnchor('earL', this.headGroup, [0.84, 0.0, -0.02]);
    this.addAnchor('earR', this.headGroup, [-0.84, 0.0, -0.02]);
    this.addAnchor('hoodTop', this.headGroup, [0, 0.92, -0.2]);
  }

  _buildLimbs() {
    this.arms = {}; this.legs = {}; this.feet = {};
    this.liningMat = new THREE.MeshBasicMaterial({ color: 0x07051a });
    for (const side of ['L', 'R']) {
      const s = side === 'L' ? 1 : -1;
      const hand = new VoidHand({ size: HAND, side, material: this.velvet });
      const limb = new Limb({ material: this.velvet, upper: ARM_L1, lower: ARM_L2, radius: ARM_R, segments: 16, radial: 14, hand, soft: 0.35 });
      this.root.add(limb.group);
      this.arms[side] = limb;
      limb.merged = { mesh: hand.mesh, update() {} };     // (compat: the hand already is one merged mesh)
      limb.cuff = new Cuff(this.velvet, this.liningMat);
      limb.group.add(limb.cuff.mesh);
      this.addAnchor('hand' + side, hand.root, hand.palmCentre.toArray());
      const leg = new SweepTube({ material: this.velvet, segments: 10, radial: 14, capRings: 4 });
      this.root.add(leg.mesh);
      this.legs[side] = leg;
      const foot = new THREE.Group(); this.root.add(foot);
      const fm = new THREE.Mesh(new THREE.SphereGeometry(1, 26, 16), this.velvet);
      fm.scale.set(FOOT[0], FOOT[1], FOOT[2]); fm.position.set(0, 0, 0.02);
      foot.add(fm);
      // soft glowing sole pad (+ three toe beans) — reads when the sole faces camera (kicks, sitting)
      // soft glowing sole pad + three toe beans, merged into ONE mesh (reads when the sole faces camera: kicks, sitting)
      const pg = new THREE.SphereGeometry(1, 20, 10, 0, TAU, Math.PI * 0.55, Math.PI * 0.45);
      pg.scale(FOOT[0] * 0.68, FOOT[1] * 1.05, FOOT[2] * 0.62); pg.translate(0, 0, -0.03);
      const parts = [pg];
      for (const tx of [-1, 0, 1]) {
        const x = tx * 0.095, z = 0.155 - 0.02 * Math.abs(tx);
        const y = -FOOT[1] * Math.sqrt(Math.max(0, 1 - (x / FOOT[0]) ** 2 - ((z - 0.02) / FOOT[2]) ** 2));
        const tg = new THREE.SphereGeometry(0.042, 10, 8); tg.translate(x, y + 0.012, z); parts.push(tg);
      }
      foot.add(new THREE.Mesh(mergeGeos(parts), this.padMat));
      this.feet[side] = { group: foot, s };
    }
  }

  _buildFx() {
    this.fx = new Particles({ max: 360, blending: 'add', intensity: 1.7 });
    this.root.add(this.fx.mesh);
    this.shadow = contactShadow(2.7, 2.4, 0.5);
    this.shadow.position.z = 0.1;
    this.root.add(this.shadow);
  }

  // ---------------------------------------------------------------- mouth painting (decal canvas, metres)
  // The Void's mouth is painted here (the core mouth is suppressed): a glowing crescent lip-line that opens into
  // deeper cosmos. Coordinates: metres around the mouth centre, +y up, +x = the Void's left (screen right).
  _cosmos(g, x0, x1, y0, y1, t, h, w) {
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, R = Math.max(x1 - x0, y1 - y0) * 0.6 + 0.01;
    const gr = g.createRadialGradient(cx, cy - h * 0.1, 0, cx, cy, R);
    gr.addColorStop(0, 'rgb(46,16,96)'); gr.addColorStop(0.55, 'rgb(17,6,44)'); gr.addColorStop(1, 'rgb(3,2,12)');
    g.fillStyle = gr; g.fillRect(x0 - 0.02, y0 - 0.02, x1 - x0 + 0.04, y1 - y0 + 0.04);
    for (let i = 0; i < 3; i++) {   // drifting nebula clouds
      const px = cx + Math.sin(t * 0.37 + i * 2.1) * w * 0.5, py = cy + Math.cos(t * 0.29 + i * 1.7) * h * 0.3;
      const rr = R * (0.45 + 0.15 * i);
      const g2 = g.createRadialGradient(px, py, 0, px, py, rr);
      const c = i === 1 ? '40,200,220' : i === 2 ? '220,90,200' : '150,70,255';
      g2.addColorStop(0, `rgba(${c},0.34)`); g2.addColorStop(1, `rgba(${c},0)`);
      g.fillStyle = g2; g.fillRect(px - rr, py - rr, rr * 2, rr * 2);
    }
    if (h > 0.06) {  // a tiny spiral galaxy turning deep inside a big open mouth
      const gx = cx + w * 0.3, gy = cy - h * 0.08, sz = Math.min(h, w) * 0.24;
      g.save(); g.translate(gx, gy); g.rotate(t * 0.6); g.scale(1, 0.6);
      g.strokeStyle = `rgba(215,205,255,${(clamp((h - 0.06) * 6) * 0.6).toFixed(3)})`; g.lineWidth = sz * 0.14; g.lineCap = 'round';
      for (let arm = 0; arm < 2; arm++) { g.beginPath(); for (let k = 0; k < 18; k++) { const a = arm * Math.PI + k * 0.28, r = sz * (0.1 + k * 0.05); const x = Math.cos(a) * r, y = Math.sin(a) * r; k ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
      g.fillStyle = 'rgba(255,250,235,0.9)'; g.beginPath(); g.arc(0, 0, sz * 0.12, 0, TAU); g.fill();
      g.restore();
    }
    for (let i = 0; i < 34; i++) {   // stars
      const u = (hash1(i * 7 + 1) + t * 0.015 * (0.5 + hash1(i * 3 + 2))) % 1, v = hash1(i * 13 + 5);
      const x = x0 + (x1 - x0) * u, y = y0 + (y1 - y0) * v;
      const sz = 0.003 + 0.006 * hash1(i * 11 + 3);
      const a = 0.55 + 0.45 * Math.sin(t * (1 + hash1(i) * 2) + i);
      g.fillStyle = `rgba(240,236,255,${a.toFixed(3)})`;
      g.beginPath(); g.arc(x, y, sz, 0, TAU); g.fill();
    }
  }

  _paintMouth(g, m, t) {
    const HW = 0.15;
    // cubic from (x0,y0) to (x1,y1) whose midpoint sits at yMid; c = control inset (small -> fuller/rounder curve)
    const bz = (x0, y0, x1, y1, yMid, c) => { const yc = (yMid - 0.125 * (y0 + y1)) / 0.75; g.bezierCurveTo(x0 + (x1 - x0) * c, yc, x1 - (x1 - x0) * c, yc, x1, y1); };
    const trem = m.tremble > 0 ? m.tremble * 0.012 * noise1(t * 11, 31) : 0;
    const open = clamp(m.open + trem * 2, 0, 1.3) * (1 - clamp(m.close));
    const round = clamp(m.round), wide = clamp(m.wide, -1, 1), press = clamp(m.press), pout = clamp(m.pout);
    const smile = clamp(m.smile + trem * 4, -1, 1), asym = clamp(m.asym, -1, 1), shift = (m.shift || 0) * HW * 0.4;
    const w = HW * (1 + 0.34 * wide) * (1 - 0.48 * round * clamp(open * 3 + 0.3)) * (1 - 0.18 * press) * (1 - 0.45 * pout);
    const droop = clamp(m.droop || 0), wavy = clamp(m.wavy || 0);
    const yR = (smile * 0.5 - asym * 0.42) * HW, yL = (smile * 0.5 + asym * 0.42) * HW;   // corner heights (R = -x)
    const xr = -w + shift, xl = w + shift, cm = (yR + yL) / 2;
    const h = HW * 1.75 * open + round * HW * 0.45 * Math.min(1, open * 4);
    const A = m.vis;
    const line = (al) => `rgba(224,212,255,${clamp(al).toFixed(3)})`;
    g.lineCap = 'round'; g.lineJoin = 'round';
    if (h < HW * 0.07) {
      // closed: a glowing crescent (lens), thicker in the middle; smile -> U, frown -> arch
      const sag = -smile * HW * (smile < 0 ? 0.55 : 0.36) * (1 - 0.6 * pout);
      const mid = cm + sag, th = HW * (0.055 + 0.05 * press + 0.06 * pout) + h * 0.5;
      const lens = () => { g.beginPath(); g.moveTo(xr, yR); bz(xr, yR, xl, yL, mid + th / 2, 0.3); bz(xl, yL, xr, yR, mid - th / 2, 0.3); g.closePath(); };
      if (pout > 0.25) {   // pursed / puffed: a small round pucker holding its breath
        const rx = w * 0.85, ry = HW * (0.06 + 0.07 * pout);
        g.fillStyle = 'rgba(14,6,34,0.95)'; g.beginPath(); g.ellipse(shift, mid, rx, ry, 0, 0, TAU); g.fill();
        g.strokeStyle = line(A * 0.35); g.lineWidth = HW * 0.13; g.stroke();
        g.strokeStyle = line(A); g.lineWidth = HW * 0.05; g.stroke();
        g.strokeStyle = line(A * 0.5); g.lineWidth = HW * 0.025;
        for (const k of [-1, 0, 1]) { g.beginPath(); g.moveTo(shift + k * rx * 0.45, mid + ry * 1.25); g.lineTo(shift + k * rx * 0.5, mid + ry * 1.7); g.stroke(); g.beginPath(); g.moveTo(shift + k * rx * 0.45, mid - ry * 1.25); g.lineTo(shift + k * rx * 0.5, mid - ry * 1.7); g.stroke(); }
      } else if (wavy > 0.05) {
        // uneasy squiggle (awkward): a wobbling wave line across a wide mouth
        const amp = HW * 0.075 * wavy, ph = t * 2.2;
        g.beginPath();
        for (let i = 0; i <= 28; i++) {
          const u = i / 28, x = lerp(xr, xl, u), env = Math.sin(Math.PI * u);
          const y = lerp(yR, yL, u) + sag * 0.4 * env + amp * Math.sin(u * Math.PI * 5 + ph) * (0.35 + 0.65 * env);
          i ? g.lineTo(x, y) : g.moveTo(x, y);
        }
        g.strokeStyle = line(A * 0.3); g.lineWidth = HW * 0.15; g.stroke();
        g.strokeStyle = line(A); g.lineWidth = HW * 0.055; g.stroke();
      } else {
        lens(); g.strokeStyle = line(A * 0.3); g.lineWidth = HW * 0.12; g.stroke();
        g.fillStyle = line(A); g.fill();
      }
      if (droop > 0.05 && pout <= 0.25) {   // sad smile: the corners turn down in little soft hooks
        for (const [x, y, sx] of [[xr, yR, -1], [xl, yL, 1]]) {
          g.beginPath(); g.moveTo(x - sx * HW * 0.02, y);
          g.quadraticCurveTo(x + sx * HW * 0.1, y + HW * 0.01, x + sx * HW * 0.15, y - HW * 0.17 * droop);
          g.strokeStyle = line(A * 0.3); g.lineWidth = HW * 0.11; g.stroke();
          g.strokeStyle = line(A * 0.95); g.lineWidth = HW * 0.045; g.stroke();
        }
      }
    } else {
      // open: upper edge nearly flat on a laugh (soft U on a smile), lower edge a full round bowl; 'round' -> O
      const up = h * (0.1 + 0.44 * round) - smile * HW * 0.42 * (1 - round) * Math.min(1, open * 2);
      const dn = h * (0.8 - 0.3 * round) + Math.max(0, smile) * h * 0.1;
      const cT = lerp(0.32, 0.1, round), cB = lerp(0.1, 0.07, round);
      const path = () => { g.beginPath(); g.moveTo(xr, yR); bz(xr, yR, xl, yL, cm + up, cT); bz(xl, yL, xr, yR, cm - dn, cB); g.closePath(); };
      g.save(); path(); g.clip();
      this._cosmos(g, xr, xl, cm - dn, cm + Math.max(up, 0) + 0.01, t, h, w);
      g.restore();
      path();
      g.strokeStyle = line(A * 0.3); g.lineWidth = HW * 0.14; g.stroke();
      g.strokeStyle = line(A); g.lineWidth = HW * (0.05 + 0.02 * press); g.stroke();
    }
    if (smile > 0.4 && A > 0.2) {   // little cheek creases at the corners of a big smile
      const k = (smile - 0.4) / 0.6;
      g.strokeStyle = line(A * 0.55 * k); g.lineWidth = HW * 0.035;
      for (const [x, y, sx] of [[xr, yR, -1], [xl, yL, 1]]) { g.beginPath(); g.moveTo(x + sx * HW * 0.05, y + HW * 0.16); g.quadraticCurveTo(x + sx * HW * 0.16, y + HW * 0.02, x + sx * HW * 0.07, y - HW * 0.13); g.stroke(); }
    }
  }

  _drawExtra(g, p, t) {
    const m = this._mouth;
    if (!m) return;
    if (m.blush > 0.01) {   // starry blush: soft violet glow under the eyes
      for (const sx of [-1, 1]) {
        const x = sx * 0.3, y = 0.1, r = 0.1;
        const gr = g.createRadialGradient(x, y, 0, x, y, r);
        gr.addColorStop(0, `rgba(200,110,255,${(0.28 * m.blush).toFixed(3)})`); gr.addColorStop(1, 'rgba(160,90,255,0)');
        g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
      }
    }
    const puff = m.puff;
    if (puff > 0.01) {   // puffed cheeks: two round soft glows that swell
      for (const sx of [-1, 1]) {
        const x = sx * 0.26 * (1 + 0.15 * puff), y = 0.03, r = 0.1 + 0.06 * puff;
        const gr = g.createRadialGradient(x, y, 0, x, y, r);
        gr.addColorStop(0, `rgba(160,120,255,${(0.4 * puff).toFixed(3)})`); gr.addColorStop(0.7, `rgba(110,90,230,${(0.16 * puff).toFixed(3)})`); gr.addColorStop(1, 'rgba(90,70,200,0)');
        g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill();
        g.strokeStyle = `rgba(210,190,255,${(0.4 * puff).toFixed(3)})`; g.lineWidth = 0.007; g.lineCap = 'round';
        g.beginPath(); g.arc(x, y, r * 0.72, sx > 0 ? -0.5 : Math.PI - 1.0, sx > 0 ? 1.0 : Math.PI + 0.5); g.stroke();
      }
    }
    this._paintMouth(g, m, m.tq);
  }

  // ---------------------------------------------------------------- spine frames
  _frames(D) {
    const F = this.F;
    let px = D.sway, py = D.base, pz = D.shiftZ;
    const up = new THREE.Vector3();
    for (let k = 0; k < FK; k++) {
      const y = k * FSTEP;
      const wl = smooth((y - 0.2) / 1.75), wh = smooth((y - 1.1) / 0.9), wt = smooth((y - 0.3) / 1.6);
      F.ax[k] = D.lean * wl + D.hunch * wh; F.az[k] = -D.tilt * wl; F.ay[k] = D.twist * wt;
      if (k > 0) {
        _e.set((F.ax[k] + F.ax[k - 1]) / 2, (F.ay[k] + F.ay[k - 1]) / 2, (F.az[k] + F.az[k - 1]) / 2, 'YXZ');
        up.set(0, 1, 0).applyEuler(_e);
        const st = FSTEP * D.sy;
        px += up.x * st; py += up.y * st; pz += up.z * st;
      }
      F.px[k] = px; F.py[k] = py; F.pz[k] = pz;
    }
    // whole-body tip about a pivot at the front-bottom (kicks, flinches)
    const piv = D.pivotZ;
    this.tipMat.makeTranslation(0, 0, piv).multiply(_m4.makeRotationX(D.tip)).multiply(new THREE.Matrix4().makeTranslation(0, 0, -piv));
  }
  _frameMat(y, out = new THREE.Matrix4()) {
    const F = this.F;
    const f = clamp(y / FSTEP, 0, FK - 1.0001), i = Math.floor(f), u = f - i;
    _e.set(lerp(F.ax[i], F.ax[i + 1], u), lerp(F.ay[i], F.ay[i + 1], u), lerp(F.az[i], F.az[i + 1], u), 'YXZ');
    out.makeRotationFromEuler(_e);
    out.setPosition(lerp(F.px[i], F.px[i + 1], u), lerp(F.py[i], F.py[i + 1], u), lerp(F.pz[i], F.pz[i + 1], u));
    return out.premultiply(this.tipMat);
  }
  /** body-frame point (rest height y, local offset) -> root space */
  _xf(y, x, yy, z) { return V3(x, yy, z).applyMatrix4(this._frameMat(y, _m4)); }
  /** body-frame direction -> root space (unit) */
  _xd(y, d) { return toV(d).transformDirection(this._frameMat(y, _m4)); }
  /** world direction -> root space (unit) */
  _wd(d) { return toV(d).applyQuaternion(this._rootQInv).normalize(); }
  _headDir(d) { this.headGroup.getWorldQuaternion(_q); return toV(d).applyQuaternion(_q).applyQuaternion(this._rootQInv).normalize(); }

  // ---------------------------------------------------------------- body skin
  _writeBody(D) {
    const pos = this.bpos, M = new THREE.Matrix4();
    let k = 0;
    for (let r = 0; r < NR; r++) {
      const row = this.rows[r];
      this._frameMat(row.y, M);
      const e = M.elements;
      const radMul = 1 + D.breath * 0.012 * row.wChest + D.swell * 0.09 * row.wMid + D.crouch * (0.07 * row.wHem + 0.08 * row.wMid)
        + (D.sit * 0.14 + D.kneel * 0.1) * row.wHem + D.laughB * 0.035 * row.wBelly;
      for (let a = 0; a <= NA; a++) {
        const col = this.cols[a];
        const lift = this.hemLift[a] * row.fC;
        let rho = row.r * (radMul + row.wHem * 0.016 * col.fold + row.wBelly * 0.05 * Math.max(0, col.c) * (1 + D.laughB)) * (1 + lift * 0.22);
        if (row.wTop > 0 && col.c > 0) rho *= 1 - 0.5 * row.wTop * Math.pow(col.c, 1.5);
        const ly = row.edge * 0.022 * col.scallop + lift + D.shrug * 0.11 * row.wSh + D.frontHem * row.wHem * Math.max(0, col.c);
        const lx = rho * col.s, lz = rho * col.c * SZ;
        let x = e[0] * lx + e[4] * ly + e[8] * lz + e[12];
        let y = e[1] * lx + e[5] * ly + e[9] * lz + e[13];
        let z = e[2] * lx + e[6] * ly + e[10] * lz + e[14];
        if (y < 0.012) { const d = 0.012 - y; y = 0.012 + d * 0.06; const f = 1 + Math.min(0.25, d * 0.35); x *= f; z *= f; }
        pos[k++] = x; pos[k++] = y; pos[k++] = z;
      }
    }
    const g = this.bodyGeo;
    g.attributes.position.needsUpdate = true;
    g.computeVertexNormals();
    seamFix(g, NR, NA + 1);
  }

  // ---------------------------------------------------------------- arms
  _presetSolve(name, s, D) {
    const pr = ARM[name] || ARM.rest;
    const base = pr.like ? ARM[pr.like] : pr;
    const mir = (v) => (v ? V3(v[0] * s, v[1], v[2]) : null);
    let tgt, fd, pn, pole;
    if (base.head) {
      tgt = this.headGroup.localToWorld(mir(base.p)); this.root.worldToLocal(tgt);
      fd = this._headDir(mir(base.fingers)); pn = this._headDir(mir(base.palm)); pole = this._headDir(mir(base.pole));
    } else {
      const p = mir(s < 0 && base.pR ? base.pR : base.p);
      p.z += -s * D.armSwing * D.c1;
      p.y += D.breath * 0.012;
      if (name === 'belly') { p.y += D.laughB * 0.06; p.z += D.laughB * 0.03; }
      if (name === 'rest' || pr.like === 'rest') {
        p.addScaledVector(V3(s * 0.35, 0.3, 0.05), D.kP);                  // arms out for balance during a kick
        p.y += 0.03 * fbm1(D.t * 0.3, 40 + s);
      }
      tgt = this._xf(CHEST_Y, p.x, p.y, p.z);
      fd = base.fingers ? this._xd(CHEST_Y, mir(s < 0 && base.fingersR ? base.fingersR : base.fingers)) : null;
      pn = base.palm ? this._xd(CHEST_Y, mir(s < 0 && base.palmR ? base.palmR : base.palm)) : null;
      pole = this._xd(CHEST_Y, mir((s < 0 && base.poleR) || base.pole || [1, 0, -0.5]));
    }
    // the target-driven shape (pat / around / tip / reach): its own dirs, used as the target end of `reach`
    const shape = pr !== base ? {
      fd: pr.fingers ? this._xd(CHEST_Y, mir(pr.fingers)) : null, pn: pr.palm ? this._xd(CHEST_Y, mir(pr.palm)) : pn,
      pole: pr.pole ? this._xd(CHEST_Y, mir(pr.pole)) : pole } : null;
    return { tgt, fd, pn, pole, shape, at: pr.at || 'wrist', shFwd: base.shFwd || 0, stretch: base.stretch || 1.2, hs: base.hs || 1, hand: { ...(base.hand || {}), ...(pr !== base ? pr.hand || {} : {}) } };
  }

  /**
   * Contact frame on a partner (any Character with shoulderL/R + head anchors) for `pat` / `around` (WORLD space):
   * { tgt: palm-centre point, pn: palm normal (into them), fd: finger direction, pole: elbow hint }.
   * pat: palm flat on top of the NEAR shoulder (or `spot`), fingers over its front, away from the head.
   * around: forearm draped behind the neck, palm down on the FAR shoulder, fingers over its front.
   */
  _contact(kind, on, spot, s) {
    const up = V3(0, 1, 0);
    const fwd = V3(0, 0, 1).applyQuaternion(on.root.getWorldQuaternion(new THREE.Quaternion())); fwd.y = 0; fwd.normalize();
    const SL = on.anchor('shoulderL'), SR = on.anchor('shoulderR');
    if (!SL || !SR) return null;
    const mySh = this.root.localToWorld(this._xf(SHOULDER_Y, s * 0.64, 0, 0.03));
    let which = spot;
    if (!which) {
      const near = SL.distanceTo(mySh) < SR.distanceTo(mySh) ? 'shoulderL' : 'shoulderR';
      which = kind === 'around' ? (near === 'shoulderL' ? 'shoulderR' : 'shoulderL') : near;
    }
    const P = on.anchor(which);
    if (!P) return null;
    const O = which === 'shoulderL' ? SR : which === 'shoulderR' ? SL : on.anchor('head') || P;
    const out = P.clone().sub(O); out.y = 0;
    if (out.lengthSq() < 1e-6) out.copy(mySh).sub(P).setY(0);
    out.normalize();
    const side = mySh.clone().sub(P).setY(0).normalize();     // from the contact toward me
    if (kind === 'around') {
      return { tgt: P.clone().addScaledVector(up, 0.025).addScaledVector(fwd, -0.02),
        pn: up.clone().multiplyScalar(-0.95).addScaledVector(out, -0.2).normalize(),
        fd: fwd.clone().multiplyScalar(0.62).addScaledVector(out, 0.4).addScaledVector(up, -0.6).normalize(),
        pole: fwd.clone().multiplyScalar(-1).addScaledVector(up, 0.85).addScaledVector(side, 0.25).normalize() };
    }
    return { tgt: P.clone().addScaledVector(up, 0.02),
      pn: up.clone().multiplyScalar(-0.95).addScaledVector(out, -0.22).normalize(),
      fd: fwd.clone().multiplyScalar(0.72).addScaledVector(out, 0.42).addScaledVector(up, -0.5).normalize(),
      pole: side.clone().multiplyScalar(0.6).addScaledVector(up, -0.65).addScaledVector(fwd, -0.4).normalize() };
  }

  _arm(side, A, D, t) {
    const s = side === 'L' ? 1 : -1;
    const limb = this.arms[side], hand = limb.hand;
    const name = A.preset || 'rest';
    let S = this._presetSolve(name, s, D);
    if (A.from && (A.mix ?? 1) < 1) {   // blend from another preset
      const F0 = this._presetSolve(A.from, s, D), w = clamp(A.mix ?? 1);
      const lv = (a, b) => (a && b ? a.clone().lerp(b, w).normalize() : (w < 0.5 ? a : b));
      S = { ...S, tgt: F0.tgt.clone().lerp(S.tgt, w), fd: lv(F0.fd, S.fd), pn: lv(F0.pn, S.pn), pole: lv(F0.pole, S.pole), hand: mixHand(F0.hand, S.hand, w),
        shFwd: lerp(F0.shFwd, S.shFwd, w), stretch: lerp(F0.stretch, S.stretch, w), hs: lerp(F0.hs, S.hs, w) };
    }
    // arm root (hidden under the capelet); some presets roll the shoulder forward around the round body
    const sh = this._xf(SHOULDER_Y, s * (0.64 - 0.06 * S.shFwd), -0.02 + D.shrug * 0.16 + D.breath * 0.006 - 0.05 * S.shFwd, 0.03 + S.shFwd);
    let { tgt, fd, pn, pole } = S;
    const hp = { ...S.hand, ...(A.hand || {}) };
    hp.curl = (hp.curl ?? 0.15) + 0.04 * fbm1(t * 0.5, 60 + s);
    hand.pose(hp);
    const k = A.handScale ?? (A.on ? 0.72 : S.hs);
    hand.root.scale.setScalar(k);
    const C = A.on ? this._contact(name, A.on, A.spot, s) : null;
    const tw = A.target ? toV(A.target) : C ? C.tgt : null;
    if (tw) {
      const r = clamp(A.reach ?? 1), sp = S.shape || S;
      const tl = this.root.worldToLocal(tw.clone());
      const pnT = A.palm ? this._wd(A.palm) : C ? this._wd(C.pn) : (sp.pn || V3(0, -1, 0));
      const fdT = A.fingers ? this._wd(A.fingers) : C ? this._wd(C.fd) : (sp.fd || tl.clone().sub(sh).normalize());
      const poleT = A.pole ? this._wd(A.pole) : C ? this._wd(C.pole) : sp.pole;
      if (A.pat) {   // pats: the palm lifts off along its normal and comes back down, `patRate` per second
        const ph = (((t - (A.patPhase ?? 0)) * (A.patRate ?? 2.2)) % 1 + 1) % 1;
        tl.addScaledVector(pnT, -0.075 * A.pat * Math.pow(Math.sin(Math.PI * ph), 2));
      }
      const at = A.at || (A.tip ? 'tip' : S.at);
      if (at === 'palm' || at === 'tip') {   // anchor the palm centre / index fingertip (not the wrist) on the target
        const L = at === 'tip' ? hand.indexTip : hand.palmCentre;
        const y = fdT.clone().normalize(), x = V3().crossVectors(y, pnT.clone().negate()).normalize(), z = V3().crossVectors(x, y);
        tl.addScaledVector(x, -L.x * k).addScaledVector(y, -L.y * k).addScaledVector(z, -L.z * k);
      }
      tgt = tgt.clone().lerp(tl, r);
      fd = fd ? fd.clone().lerp(fdT, r).normalize() : fdT;
      pn = pn ? pn.clone().lerp(pnT, r).normalize() : pnT;
      pole = pole.clone().lerp(poleT, r).normalize();
    } else {
      if (A.pole) pole = this._wd(A.pole);
      if (A.palm) pn = this._wd(A.palm);
      if (A.fingers) fd = this._wd(A.fingers);
    }
    if (A.offset) tgt.add(this._wd(A.offset).multiplyScalar(toV(A.offset).length()));
    const L = ARM_L1 + ARM_L2, f = clamp(tgt.distanceTo(sh) / (L * 0.97), 1, S.stretch);   // a little rubber stretch
    limb.l1 = ARM_L1 * f; limb.l2 = ARM_L2 * f;
    limb.update(sh, tgt, pole, { palmNormal: pn, fingerDir: fd, radius: ARM_R.map((r) => r / Math.sqrt(f)) });
    // flared sleeve cuff around the wrist, hanging a little toward the ground
    const fa = limb.end.clone().sub(limb.mid).normalize();
    limb.cuff.update(limb.end, fa, pn || V3(0, -1, 0), this._wd([0, -1, 0]), lerp(1, k, 0.6));
  }

  // ---------------------------------------------------------------- legs & feet
  _legs(D, E) {
    const out = {};
    for (const side of ['L', 'R']) {
      const s = side === 'L' ? 1 : -1, isK = s === D.kS && (D.kP > 0 || D.kM > 0);
      let fx = s * 0.4, fy = 0, fz = 0.56;
      const up = V3(0, 1, 0), fwd = V3(s * 0.14, 0, 1);
      if (D.wa > 0) {
        const u = ((D.ph + (side === 'L' ? 0 : 0.5)) % 1 + 1) % 1, st = D.st;
        let z, lift = 0;
        if (u < 0.5) z = st.stride / 2 - st.stride * (u / 0.5);
        else { const q = (u - 0.5) / 0.5; z = -st.stride / 2 + st.stride * smooth(q); lift = Math.sin(Math.PI * q) * st.lift; fwd.y += 0.6 * Math.sin(Math.PI * q * 1.1) * D.wa; }
        fz += z * D.wa; fy += lift * D.wa;
      }
      // sit: legs stick out in front (toes up); kneel: folded behind; crouch: knees out
      fx = lerp(fx, s * 0.5, D.sit); fy = lerp(fy, 0.0, D.sit); fz = lerp(fz, 1.16, D.sit);
      up.lerp(V3(0, 0.3, -0.95), D.sit * 0.85); fwd.lerp(V3(s * 0.2, 0.95, 0.3), D.sit * 0.85);
      fz = lerp(fz, -0.2, D.kneel); fy = lerp(fy, 0.02, D.kneel); up.lerp(V3(0, 0.15, -1), D.kneel); fwd.lerp(V3(0, 1, 0.1), D.kneel);
      fx += s * 0.06 * D.crouch;
      fx += s * 0.02 * D.hemOpen;
      if (!isK && D.kP > 0) { fz += 0.06 * D.kP; fx += s * 0.04 * D.kP; }
      up.normalize(); fwd.normalize();
      let centre = V3(fx, fy, fz).addScaledVector(up, FOOT[1] * 0.95);
      let ankle = centre.clone().addScaledVector(up, 0.08).addScaledVector(fwd, -0.08);
      let hip = this._xf(HIP_Y, s * 0.34, 0, 0.24);
      let fsc = 1;
      if (isK) {
        // wind-up: the knee comes up in front (chamber); kick: the hip slides back under the lifted back hem and the
        // short fat leg shoots straight back-and-up (height comes from the body tipping forward, not a long leg)
        const kM = D.kM, kP = clamp(D.kP, 0, 1.25), kE = smooth(clamp(kP));
        const chamber = V3(fx, lerp(fy, 0.3, kM), lerp(fz, 0.7, kM)).addScaledVector(up, FOOT[1] * 0.95);
        hip.lerp(this._xf(0.34, s * 0.38, 0, -0.55), kE);
        const dB = this._xd(0.34, [s * 0.38, 0.2, -1]);                 // back, out to its side, a touch up (body frame)
        let dir = dB.clone();
        if (D.kickT) {                                                    // aim at a target, inside a cone around dB
          const dt = D.kickT.clone().sub(hip).normalize();
          dir = dB.clone().lerp(dt, clamp(0.85 - 0.6 * Math.max(0, 0.5 - dt.dot(dB)))).normalize();
        }
        const len = KICK_LEN * (E.kickReach ?? 1) * (0.82 + 0.18 * kP) - FOOT[1];   // kickReach: opt-in rubber-hose stretch (default 1)
        const kCentre = hip.clone().addScaledVector(dir, len + FOOT[1] * 0.9);
        const kUp = dir.clone().negate();                                   // the sole (pad) faces the target
        const kFwd = V3(0, 1, 0).addScaledVector(kUp, -kUp.y).normalize(); // toes up
        centre = chamber.lerp(kCentre, kE);
        up.lerp(kUp, clamp(kE * 1.2)).normalize(); fwd.lerp(kFwd, clamp(kE * 1.2)).normalize();
        ankle = centre.clone().addScaledVector(up, lerp(0.08, FOOT[1] * 0.9, kE)).addScaledVector(fwd, -0.08 * (1 - kE));
        fx = centre.x; fy = centre.y - FOOT[1]; fz = centre.z;
        fsc = 1 + 0.18 * clamp((kP - 0.9) / 0.2) * (1 - clamp((kP - 1.1) / 0.15)) + 0.06 * kE;   // swells on impact
      }
      const d = ankle.clone().sub(hip), L = d.length(), mid = hip.clone().lerp(ankle, 0.5);
      let knee = mid;
      const LL = isK ? Math.max(LEG_LEN, L * 1.02) : LEG_LEN;
      if (L < LL) {
        const hk = Math.sqrt(Math.max(0, (LL / 2) ** 2 - (L / 2) ** 2));
        const pole = isK && D.kP > 0.2 ? V3(0, -1, 0.2) : V3(s * 0.45, 0, 1);
        pole.addScaledVector(d, -pole.dot(d) / (L * L)).normalize();
        knee = mid.clone().addScaledVector(pole, hk);
      }
      const rs = clamp(Math.sqrt(LEG_LEN / Math.max(L, LEG_LEN)), 0.88, 1);
      this.legs[side].update([hip, knee, ankle], isK ? [LEG_R[0] * 1.04, LEG_R[1], LEG_R[2]] : LEG_R.map((r) => r * rs), {});
      const fg = this.feet[side].group;
      fg.position.copy(centre);
      orientYZ(fg, up, fwd);
      fg.scale.setScalar(fsc);
      out[side] = { sole: V3(fx, fy, fz), centre, up, fwd, isK };
    }
    return out;
  }

  /** Per-column hem lift amplitudes (m): a smooth "curtain" opening over the feet / the kicking leg. */
  _hemLifts(D, feet) {
    const H = this.hemLift;
    const bumps = [];
    for (const side of ['L', 'R']) {
      const f = feet[side];
      if (f.isK) continue;
      const amt = clamp((f.centre.z - 0.62) * 0.7 + f.sole.y * 1.1, 0, 0.32);
      if (amt > 0.001) bumps.push([Math.atan2(f.centre.x, f.centre.z), amt, 0.55]);
    }
    if (D.kP > 0) bumps.push([Math.atan2(D.kS * 0.45, -0.6), 0.56 * smooth(clamp(D.kP)), 1.0]);
    if (D.kM > 0) bumps.push([Math.atan2(D.kS * 0.38, 0.9), D.kM * 0.24, 0.7]);
    if (D.sit > 0) bumps.push([0, D.sit * 0.2, 0.9]);
    for (let a = 0; a <= NA; a++) {
      const th = this.cols[a].th;
      let v = D.hemOpen * 0.3;
      for (const [c, amt, w] of bumps) { let dt = th - c; dt = Math.atan2(Math.sin(dt), Math.cos(dt)); v += amt * Math.exp(-((dt / w) ** 2)); }
      H[a] = Math.min(v, 0.6);
    }
  }

  // ---------------------------------------------------------------- main update
  update(t, pose = {}) {
    const P = pose || {}, B = P.body || {}, W = P.walk || {}, Hd = P.head || {}, E = P.extra || {}, fIn = P.face || {};
    this.place(P.pos || [0, 0, 0], P.yaw || 0);
    this.root.updateMatrixWorld(true);
    this.root.getWorldQuaternion(this._rootQInv).invert();
    const sd = this.seed;
    const br = Math.sin(t * (B.breathRate ?? 0.21) * TAU + sd) * (B.breathe ?? 1);
    const laugh = clamp(E.laugh ?? 0), puff = clamp(E.puff ?? fIn.puff ?? 0), cosmos = clamp(E.cosmos ?? 0);
    const kick = clamp(E.kick ?? 0, -0.5, 1.25), kP = Math.max(0, kick), kM = Math.max(0, -kick) / 0.5;
    const kS = (E.kickSide ?? 'R') === 'L' ? 1 : -1;
    const sit = clamp(B.sit ?? 0), kneel = clamp(B.kneel ?? 0), crouch = clamp(B.crouch ?? 0);
    const shrug = clamp(B.shrug ?? 0), slump = clamp(B.slump ?? 0), recoil = B.recoil ?? 0;
    const wa = clamp(W.amount ?? 0), ph = W.phase ?? 0, st = WALK[W.style] || WALK.waddle;
    const c1 = Math.cos(ph * TAU), s1 = Math.sin(ph * TAU), c2 = Math.cos(ph * 2 * TAU);
    const lr = laugh > 0 ? Math.pow(0.5 + 0.5 * Math.sin(t * TAU * 3.3), 1.5) : 0;      // "HA-HA-HA" belly rhythm
    const shake = laugh * 0.022 * noise1(t * 9, sd + 5);
    const kickT = E.kickTarget ? this.root.worldToLocal(toV(E.kickTarget)) : null;
    const D = {
      t, breath: br, crouch, sit, kneel, shrug, wa, ph, st, c1, kP, kM, kS, kickT,
      lean: (B.lean ?? 0) + slump * 0.16 - recoil * 0.22 + wa * st.lean - laugh * 0.1 + kP * 0.1 - kM * 0.05,
      hunch: (B.hunch ?? 0) + slump * 0.25 + kM * 0.1,
      tilt: (B.tilt ?? 0) + wa * st.roll * s1 + shake,
      twist: (B.twist ?? 0) + wa * st.twist * s1,
      sy: (1 - 0.2 * crouch - 0.05 * sit - 0.04 * kneel) * (1 + 0.005 * br) * (1 - 0.035 * laugh * lr) * (1 + (B.stretch ?? 0)) * (1 + 0.04 * puff),
      base: -(0.09 * crouch + 0.38 * sit + 0.3 * kneel) + (B.bounce ?? 0) - wa * st.bob * c2 + laugh * 0.03 * lr + (wa * (W.style === 'run' ? 1 : 0) * 0.03 * Math.abs(s1)),
      sway: wa * st.sway * s1, shiftZ: -recoil * 0.12, pivotZ: 0.55,
      tip: kP * (0.42 + 0.16 * (kickT ? clamp((kickT.y - 1.1) / 0.6) : 0)) - kM * 0.05 + (B.pitch ?? 0) + recoil * -0.06,
      swell: (B.swell ?? 0) + puff * 0.6,
      laughB: laugh * lr, armSwing: wa * st.arm,
      hemOpen: clamp(E.hem ?? 0), frontHem: 0.06 + 0.04 * sit, capeLift: 0.04 * laugh * lr + 0.05 * kP,
    };
    this._frames(D);
    const feet = this._legs(D, E);
    this._hemLifts(D, feet);
    this._writeBody(D);
    this._writeCape(D);

    // ---- head
    const neckM = this._frameMat(NECK_Y, new THREE.Matrix4());
    this.headPivot.position.copy(V3(0, -0.06 * shrug + 0.008 * br + D.laughB * 0.012, HEAD_FWD).applyMatrix4(neckM));
    const qn = new THREE.Quaternion().setFromRotationMatrix(neckM);
    let hyaw = clamp(Hd.yaw ?? 0, -2.0, 2.0), hpitch = Hd.pitch ?? 0, hroll = Hd.roll ?? 0;
    hpitch += -0.34 * laugh * (0.75 + 0.25 * lr) - D.tip * (E.kickLevel ?? 0.75) + 0.1 * slump + 0.012 * fbm1(t * 0.4, sd + 3) + kM * 0.05;
    hyaw += 0.015 * fbm1(t * 0.3, sd + 7);
    hroll += shake * 1.6 - 0.45 * wa * st.roll * s1 + 0.01 * fbm1(t * 0.27, sd + 9);
    const gaze = gazePoint(P.gaze, CTX.camera);
    if (Hd.track && gaze) {   // turn the hood partly toward the gaze target
      const g = this.root.worldToLocal(gaze.clone()).sub(this.headPivot.position).applyQuaternion(qn.clone().invert());
      hyaw += Hd.track * Math.atan2(g.x, g.z);
      hpitch += Hd.track * -Math.atan2(g.y - HEAD_UP, Math.hypot(g.x, g.z));
    }
    _e.set(hpitch, hyaw, hroll, 'YXZ');
    this.headPivot.quaternion.copy(qn).multiply(_q.setFromEuler(_e));
    const sq = (Hd.squash ?? 0) + 0.05 * laugh * lr - 0.04 * clamp((fIn.lidU ?? 1) - 1.2);
    this.headGroup.scale.set((1 + 0.1 * puff) * (1 + sq), (1 + 0.04 * puff) * (1 - sq), (1 + 0.07 * puff) * (1 + sq * 0.5));
    this.headGroup.updateMatrixWorld(true);
    { const pts = [], M = this._frameMat(NECK_Y, _m4);
      for (let i = 0; i <= 8; i++) {
        const th = lerp(1.05, TAU - 1.05, i / 8), R = 0.69 + 0.025 * Math.cos(3 * th);
        pts.push(V3(R * Math.sin(th), 0.06 + 0.02 * Math.sin(2.5 * th + 0.4) + shrug * 0.09 + 0.004 * br, R * Math.cos(th) * 0.92 - 0.02).applyMatrix4(M));
      }
      this.collar.update(pts, (u) => 0.02 + 0.09 * Math.pow(Math.sin(Math.PI * u), 0.6), { flatten: 0.25, up: this._xd(NECK_Y, [0, 1, 0]) }); }

    // ---- face
    const fp = { ...FACE_DEFAULTS, ...fIn };
    // mouth params (painted by _paintMouth); lip-sync blended here with the same rule as core Face
    const M = { open: fp.mOpen, smile: fp.mSmile, wide: fp.mWide, round: fp.mRound, press: fp.mPress, pout: fp.mPout, asym: fp.mAsym,
      shift: fp.mShift, close: 0, tremble: fp.mTremble, blush: fp.blush, puff, droop: clamp(fIn.mDroop ?? 0), wavy: clamp(fIn.mWavy ?? 0) };
    if (fp.mClench > 0) { M.press = Math.max(M.press, fp.mClench * 0.7); M.wide += fp.mClench * 0.4; M.open *= 1 - 0.7 * fp.mClench; }
    const sp = this.speech(t, P);
    if (sp && fp.talk > 0) {
      const k = fp.talk, so = sp.open * k;
      M.open = Math.max(M.open * (1 - 0.5 * k), so * 0.9 + M.open * 0.3 * k);
      M.round = lerp(M.round, sp.round, 0.75 * k);
      M.wide = lerp(M.wide, Math.max(M.wide, sp.wide * 0.8), 0.6 * k);
      M.close = (sp.close || 0) * k;
    }
    M.open *= 1 - 0.22 * laugh * (1 - lr);          // the laugh mouth pumps with each "HA"
    if (puff > 0) { M.open *= 1 - puff; M.press = Math.max(M.press, 0.7 * puff); M.pout = Math.max(M.pout, puff); M.wide = lerp(M.wide, -0.6, puff); }
    M.vis = clamp(0.1 + 1.5 * Math.abs(M.smile) + 4 * M.open + 0.8 * M.press + 0.8 * M.pout + 0.7 * Math.abs(M.asym) + 0.6 * M.wavy + 0.5 * M.droop + (E.mouthGlow ?? 0));
    M.vis = 0.14 + 0.86 * M.vis;
    this._mouth = M;
    // The core mouth stays invisible and CONSTANT (zeros), so the core decal never redraws on its own; the Void's
    // painted mouth (drawExtra) is redrawn exactly when this collision-free digest of its quantized inputs changes.
    // The cosmos interior (twinkling stars, turning galaxy) animates at 12 Hz: the quantized time is in the digest,
    // so the canvas uploads at most 12x per second and is still a pure function of t (no modulo, no hashing).
    const fcore = { ...fp, mOpen: 0, mSmile: 0, mWide: 0, mRound: 0, mPress: 0, mPout: 0, mAsym: 0, mClench: 0, mTremble: 0, mTeethU: 0, mTeethL: 0, mShift: 0, blush: 0, talk: 0 };
    this.face.cfg.mouth.line = 'rgba(0,0,0,0)';
    this.face.cfg.mouth.animated = false;
    const live = M.open * (1 - M.close) > 0.03 || M.tremble > 0 || M.wavy > 0.01;
    M.tq = live ? Math.floor(t * 12) / 12 : 0;
    const digest = [M.open, M.smile, M.wide, M.round, M.press, M.pout, M.asym, M.shift || 0, M.close, M.tremble, M.vis, M.puff, M.blush, M.droop, M.wavy]
      .map((v) => v.toFixed(3)).join(',') + '|' + M.tq.toFixed(4);
    if (digest !== this._mouthDigest) { this._mouthDigest = digest; this.face._lastKey = null; }   // force one core decal redraw
    this.face.update(t, fcore, { gaze, speech: null, blinkAt: P.blinkAt });
    const eyeGlow = (E.eyeGlow ?? 1) * (1 + 0.15 * cosmos);
    this.face.eyes.forEach((ey, i) => {
      ey.mat.uniforms.uGlow.value = 0.9 * eyeGlow;
      const up = -ey.up.rotation.x, low = -ey.lo.rotation.x, r = ey.r;
      const open = clamp((up - low) / 1.45);
      this.FU.uHalo.value.setComponent(i, (0.03 + 0.1 * open) * eyeGlow * 1.6);
      // eye-corner fade (see _buildHead): grows as the lids close / squint
      ey.mat.uniforms.uCorner.value = 1 - smooth((open - 0.06) / 0.4);
      if (open < 0.3) { ey.catch1.visible = false; ey.catch2.visible = false; }   // no catchlight dots on a squeezed eye
      ey.group.getWorldQuaternion(_q).invert();
      ey.mat.uniforms.uSock.value.setFromMatrix4(_m4.makeRotationFromQuaternion(_q));
    });
    this.FU.uHoodGlow.value = (0.08 + 0.12 * cosmos) * 1.2;
    this.face.brows.forEach((b, i) => {
      const pts = b.tube.curve.points.map((p) => p.clone());
      this.browHalo[i].update(pts, [0.04, 0.078, 0.07, 0.03], { flatten: 0.15 });
    });
    this.browMat.uniforms.uI.value = 1.7 * (1 + 0.4 * cosmos) * (E.browGlow ?? 1);

    // ---- arms
    this._arm('L', P.armL || {}, D, t);
    this._arm('R', P.armR || {}, D, t);

    // ---- uniforms
    this.U.uRootInv.value.copy(this.root.matrixWorld).invert();
    this.FU.uHeadInv.value.copy(this.headGroup.matrixWorld).invert();
    this.U.uCosmos.value = cosmos;
    this.U.uStars.value = E.stars ?? 1;
    this.U.uRimK.value = 1.0 * (E.rim ?? 1);
    this.FU.uBright.value = 1 + 0.6 * cosmos;

    // ---- anchors (root space)
    const an = (n, v) => this._anch[n].position.copy(v);
    const rc = this.rAt(1.2), rs = this.rAt(1.42), rl = this.rAt(0.95);
    an('chest', this._xf(1.2, 0, 0, rc * SZ + 0.03));
    an('back', this._xf(1.2, 0, 0, -rc * SZ - 0.03));
    an('backLow', this._xf(0.95, 0, 0, -rl * SZ - 0.03));
    const cs = this.capeR(1.47);
    an('shoulderL', this._xf(1.47, cs * 0.9, 0.1 + shrug * 0.14, 0.0));
    an('shoulderR', this._xf(1.47, -cs * 0.9, 0.1 + shrug * 0.14, 0.0));
    an('sideL', this._xf(0.95, rl + 0.03, 0, 0));
    an('sideR', this._xf(0.95, -rl - 0.03, 0, 0));
    an('hip', this._xf(0.55, 0, 0, 0));
    an('footL', feet.L.sole); an('footR', feet.R.sole);
    const kf = feet[kS > 0 ? 'L' : 'R'];
    an('kickFoot', kf.centre.clone().addScaledVector(kf.up, -FOOT[1]));
    this._anch.hood.position.copy(this.headPivot.position);

    // ---- contact shadow & particles
    this.shadow.scale.set(1 + 0.15 * sit + 0.1 * crouch, 1, 1 + 0.15 * sit);
    this.shadow.material.opacity = 0.5 * (1 - 0.3 * kP);
    this._fx(t, E, cosmos);
  }

  _moteOrigin(tb) {
    const n = Math.floor(tb * 1000);
    const [r0, r1] = this._moteRows;
    const r = Math.floor(lerp(r0, r1, hash1(n * 3 + 1))), a = Math.floor(hash1(n * 7 + 2) * NA);
    const i = (r * (NA + 1) + a) * 3, p = this.bpos, nn = this.bodyGeo.attributes.normal.array;
    return [p[i] + nn[i] * 0.04, p[i + 1] + nn[i + 1] * 0.04, p[i + 2] + nn[i + 2] * 0.04];
  }

  _fx(t, E, cosmos) {
    const fx = this.fx;
    fx.begin();
    const ma = E.motes ?? 1;
    const base = { t, t0: -30, t1: 1e6, life: 3.6, origin: (tb) => this._moteOrigin(tb), vel: [0, 0.15, 0], spread: [0.05, 0.04, 0.05],
      size: [0.03, 0.06], color: [0xc9b8ff, 0x9fe9ff, 0xffffff], fade: [0.25, 0.5], cell: CELL.star, twinkle: true, wobble: 0.05, grow: 0.5 };
    if (ma > 0) fx.stream({ ...base, seed: 91, rate: 1.4, alpha: 0.8 * ma });
    if (cosmos > 0.01) fx.stream({ ...base, seed: 92, rate: 10, alpha: 0.9 * cosmos, size: [0.035, 0.08], vel: [0, 0.22, 0], life: 3.0 });
    // coughed-up stars & spiral galaxies from the mouth. Default = a few BIG readable puffs on each "HA" (the laugh's
    // 3.3 Hz belly rhythm) flung out & up clear of the hood, plus a light sprinkle (E.cough: see docs/chars/void.md)
    const C = E.cough;
    if (C) {
      const m = this.root.worldToLocal(this.anchor('mouth')), dir = this._wd(this.mouthDir());
      const fwdB = C.forward ?? 1, sp = (C.speed ?? 2.4) * fwdB, upV = C.up ?? 1.1, spr = C.spread ?? 1;
      const sz = C.size ?? 1, gShare = C.galaxy ?? 0.4, life = C.life ?? 2.2, seed = C.seed ?? 77;
      m.addScaledVector(dir, 0.28);
      const cols = [0xffffff, 0xd8c8ff, 0x9feaff, 0xffd6f0];
      const common = { t, life, origin: m.toArray(), vel: [dir.x * sp, dir.y * sp + upV, dir.z * sp], gravity: [0, -0.5, 0], drag: 0.45,
        color: cols, fade: [0.06, 0.45], spin: 1.6, twinkle: true };
      // big puffs: one per "HA" peak inside [t0, t1]
      const per = C.puffs ?? 3, rate = C.haRate ?? 3.3;
      const n0 = Math.ceil((Math.max(C.t0, t - life * 1.3) * rate) - 0.25), n1 = Math.floor((Math.min(C.t1, t) * rate) - 0.25);
      for (let n = n0; n <= n1; n++) {
        const at = (n + 0.25) / rate;
        if (at < C.t0 || at > C.t1) continue;
        const gN = Math.round(per * gShare + (hash1(seed + n * 13) - 0.5) * 0.9 * Math.min(1, per * gShare));
        const sprd = [0.55 * spr, 0.35 * spr, 0.55 * spr];
        if (gN > 0) fx.burst({ ...common, seed: seed * 31 + n, at, count: gN, jitter: 0.05, spread: sprd, size: [0.15 * sz, 0.21 * sz], grow: 1.2, cell: CELL.galaxy, spin: 1.2 });
        if (per - gN > 0) fx.burst({ ...common, seed: seed * 37 + n, at, count: per - gN, jitter: 0.07, spread: sprd, size: [0.07 * sz, 0.12 * sz], grow: 1.3, cell: CELL.star });
      }
      // + a light sprinkle of small stars
      fx.stream({ ...common, seed, t0: C.t0, t1: C.t1, rate: C.rate ?? 4, spread: [0.45 * spr, 0.3 * spr, 0.45 * spr],
        size: [0.035 * sz, 0.07 * sz], grow: 1.3, life: life * 0.8, cell: (r) => (r() < 0.15 ? CELL.nebula : CELL.star) });
    }
    fx.end();
  }

  /**
   * Pure helper: returns pos [x, 0, z] so that, with this pose, anchor `name` lands on `target` (world) in the
   * ground plane (height is whatever the pose gives; check .err). Leaves the rig posed at that pos.
   */
  solvePos(t, pose, name, target) {
    this.update(t, { ...pose, pos: [0, 0, 0] });
    const a = this.anchor(name), tg = toV(target);
    const pos = [tg.x - a.x, 0, tg.z - a.z];
    this.update(t, { ...pose, pos });
    const err = tg.y - a.y;
    return Object.assign(pos, { err });
  }

  /**
   * Whisper helper: finds the whisperPose depth whose 'whisper' point is at `ear` height, then the ground position
   * that puts it on `ear`. pose = the rest of the pose (yaw, face...; its body/head are merged under the bend).
   * Returns { pos, depth, err, pose } (pose = the merged pose incl. pos). Leaves the rig posed there.
   */
  solveWhisper(t, pose, ear, side = 1, { amount = 1, lo = 0, hi = 1.5 } = {}) {
    const E = toV(ear);
    const mk = (d) => { const W = whisperPose(side, d, amount); return { ...pose, ...W, body: { ...(pose.body || {}), ...W.body }, head: { ...(pose.head || {}), ...W.head } }; };
    let a = lo, b = hi;
    for (let i = 0; i < 8; i++) {
      const m = (a + b) / 2;
      this.update(t, { ...mk(m), pos: [0, 0, 0] });
      if (this.anchor('whisper').y > E.y) a = m; else b = m;
    }
    const depth = (a + b) / 2, p = mk(depth);
    const pos = this.solvePos(t, p, 'whisper', E);
    return { pos: [pos[0], 0, pos[2]], depth, err: pos.err, pose: { ...p, pos: [pos[0], 0, pos[2]] } };
  }

  anchor(name) {
    if (name === 'mouthDir') return this.mouthDir();
    if (name === 'whisper') return super.anchor('mouth').addScaledVector(this.mouthDir(), 0.16);
    return super.anchor(name);
  }
  /** World unit vector pointing out of the mouth (for coughed-up stars / galaxies). */
  mouthDir() { return super.anchor('mouthOut').sub(super.anchor('mouth')).normalize(); }
}

function mergeGeos(list) {   // tiny non-indexed-safe merge (position/normal/index only)
  let nv = 0, ni = 0; for (const g of list) { nv += g.attributes.position.count; ni += g.index.count; }
  const pos = new Float32Array(nv * 3), nrm = new Float32Array(nv * 3), idx = []; let o = 0;
  for (const g of list) { pos.set(g.attributes.position.array, o * 3); nrm.set(g.attributes.normal.array, o * 3); for (const k of g.index.array) idx.push(k + o); o += g.attributes.position.count; }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nrm, 3)); out.setIndex(idx);
  return out;
}

function mixHand(a, b, w) {
  const o = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) o[k] = lerp(a[k] ?? (k === 'curl' ? 0.15 : 0), b[k] ?? (k === 'curl' ? 0.15 : 0), w);
  return o;
}

export async function create() { return new Void(); }
