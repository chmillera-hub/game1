// SET 'COSMOS' (SETS.COSMOS) — the universe the Void shows Fear (bonus-scene climax). Full doc: docs/sets/cosmos.md.
//
//   const cos = await app.set('COSMOS');
//     // { scene, group, update(t, opts), attach(scene), dissolve(target, opts), hostFade(reveal), blendLook(), anchors, props, look }
//   standalone:       st.scene = cos.scene; cos.attach(cos.scene); cos.update(t, { reveal: 1 });
//   inside BACKROOM:  setup: cos.dissolve(br.props.room); cos.dissolve([br.props.bulb.parent, br.props.bulb2.parent], { opaque: true });
//                     cos.attach(br.scene)   (every frame BEFORE update — a group has ONE parent, like characters)
//                     br.update(t, { cosmos: cos.hostFade(reveal), shafts: 1 - smooth(reveal / .6), lights: { bulb, bulb2 } });
//                     cos.update(t, { reveal, center, source: voidRig.anchor('chest'), radius: 9 });   // AFTER br.update
//
// Contents (all a pure function of t + opts; deterministic seeded layout; no per-frame allocation of geometry):
//   - SKY SHELL: an inside-out ellipsoid around the characters. Its colour is looked up by CAMERA ray direction (the
//     sky sits at infinity: no parallax, no swimming) in a nebula cube map baked once on the GPU (half float, smooth
//     domain-warped fbm cloud complexes — violet/magenta, teal/blue, rose, a gold-cored warm cloud — separated by deep
//     dark space, dust lanes with gold rims, faint galactic band). It is depth-tested against the host scene, so anything farther
//     than the shell is covered: walls dissolve as the reveal opens the sky outward from the source (the Void),
//     first into deep starry space, then nebulae bloom open behind that front with a soft unfurling light.
//   - FLOOR VEIL: in a host room the floor beyond r0 fades into the same sky (the SAME reveal look as the shell, so the
//     floor/wall junction never shows a seam) + a procedural star field; a light pool + soft contact core under the pair.
//   - ISLAND: a disc of dark "glass over the universe" just below the floor plane (faint mirror of the sky): invisible
//     under a host floor, it is the ground whenever there is none (standalone, or a host that hides its floor).
//   - HOST DISSOLVE: cos.dissolve() patches host materials so walls / props / cords open with the same front as the sky.
//   - STARS: 3 parallax layers of point sprites — far (~2600, on the shell at infinity, denser along the band), mid
//     (520, world shell between characters and sky), near (72, metres around the source: 26 KINDLE one by one).
//     Gaussian cores >= 3.5 px (no sub-pixel shimmer), few bright stars with 4-point glints, gentle per-star twinkle.
//   - NEBULA PUFFS: 5 big soft world-space billboards (parallax depth), swelling open as the bloom front reaches them.
//   - 5 SPIRAL GALAXIES (4 baked, mipmapped variants): gold bulges, blue/violet/teal arms, rose knots, dust lanes;
//     inclined discs at infinity, each slowly spinning; they drift in during the last half of the reveal.
//   - BITS OF MEANING: 9 tiny glowing glyphs (heart, sun, music note, house, handprint, pencil) orbiting the source.
//   - LIGHTS: a violet/teal hemisphere + a warm starlight key from above the hero galaxy (intensity x reveal).
import * as THREE from 'three';
import { CTX, EYE_LIGHT } from '../core/context.js';
import { rng, clamp, lerp, smooth } from '../core/util.js';

const TAU = Math.PI * 2;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const nrm = (x, y, z) => V3(x, y, z).normalize();
const col = (hex) => new THREE.Color(hex);
// [x,y,z] | THREE.Vector3 (e.g. a rig anchor) -> [x,y,z]
const arr3 = (v, def) => (!v ? def : v.isVector3 ? [v.x, v.y, v.z] : v);

// ------------------------------------------------------------------------------------------------ layout (sky space)
// Convention: camera usually at +Z looking toward -Z at the characters, so "behind the characters" is -Z.
const SKY_AXIS = nrm(0.18, 1, 0.12);            // slow drift rotation axis of the whole sky
const SKY_RATE = 0.0045;                        // rad/s at drift 1 (about 8° per 30 s)
const SKY_SWING = 0.14;                         // max drift away from the designed layout (rad, ~8°)
const HERO_DIR = nrm(0.214, 0.469, -0.857);     // hero galaxy direction (az +14°, el 28°: fills the top half of the
                                                // gentle looking-up hero shot, upper-left of the pair)
const KEY_DIR = nrm(0.30, 0.62, -0.72);         // warm starlight key light (from just above the hero galaxy)
// galaxies: dir (sky space), angular half-size (tan), inclination (rad), position angle, spin rad/s, tint, bake variant
const GALAXIES = [
  { dir: HERO_DIR, size: 0.24, incl: 0.62, pa: 0.5, spin: 0.022, tint: 0xffffff, v: 0, delay: 0.0 },
  { dir: nrm(-0.113, 0.375, -0.92), size: 0.10, incl: 1.0, pa: -0.8, spin: -0.03, tint: 0xf4fbff, v: 1, delay: 0.12 },
  { dir: nrm(0.88, 0.16, 0.05), size: 0.13, incl: 1.28, pa: 2.2, spin: 0.028, tint: 0xfff0f4, v: 2, delay: 0.22 },
  { dir: nrm(-0.22, 0.96, 0.12), size: 0.19, incl: 0.30, pa: 1.1, spin: 0.018, tint: 0xffffff, v: 3, delay: 0.3 },
  { dir: nrm(-0.42, 0.28, 0.86), size: 0.16, incl: 0.85, pa: -2.0, spin: -0.024, tint: 0xfff8ec, v: 1, delay: 0.38 },
];
// world-space nebula puffs (mid layer, unit-dome space): dir, distance (0..1 of dome), size m, colour, alpha, channel
const PUFFS = [
  { dir: nrm(-0.15, 0.62, -0.95), d: 0.80, s: 4.2, c: 0x8a5cff, a: 0.12, ch: 0 },
  { dir: nrm(-0.95, 0.52, -0.40), d: 0.76, s: 3.6, c: 0x2fd2c8, a: 0.12, ch: 1 },
  { dir: nrm(0.35, 0.35, -0.95), d: 0.80, s: 3.2, c: 0xff7fb0, a: 0.10, ch: 2 },
  { dir: nrm(-0.30, 0.38, 1.0), d: 0.78, s: 3.8, c: 0x6a7dff, a: 0.11, ch: 3 },
  { dir: nrm(0.80, 0.40, 0.45), d: 0.76, s: 3.4, c: 0xff7fb0, a: 0.10, ch: 1 },
];
// EYE_LIGHT blending: fixed base (= the engine defaults in core/context.js) and the cosmos targets
const EYE_BASE = { dir: nrm(0.4, 0.6, 0.7), key: new THREE.Color(1.0, 0.95, 0.88), amb: new THREE.Color(0.55, 0.55, 0.62) };
const EYE_KEY = col(0xf2eaff), EYE_AMB = col(0x5a5a8a);
const GLYPHS = ['heart', 'sun', 'note', 'house', 'hand', 'pencil'];
const GLYPH_COLS = [0xff8fb8, 0xffd27a, 0x7fe8e0, 0xffc890, 0xffb0a0, 0xffe08a];

// ------------------------------------------------------------------------------------------------ GLSL
const NOISE = /* glsl */`
float h13(vec3 p){ p = fract(p * 0.1031); p += dot(p, p.zyx + 31.32); return fract((p.x + p.y) * p.z); }
float vnoise(vec3 x){ vec3 i = floor(x), f = fract(x); vec3 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
  float a = h13(i), b = h13(i + vec3(1,0,0)), c = h13(i + vec3(0,1,0)), d = h13(i + vec3(1,1,0));
  float e = h13(i + vec3(0,0,1)), g = h13(i + vec3(1,0,1)), h = h13(i + vec3(0,1,1)), k = h13(i + vec3(1,1,1));
  return mix(mix(mix(a, b, u.x), mix(c, d, u.x), u.y), mix(mix(e, g, u.x), mix(h, k, u.x), u.y), u.z); }
const mat3 NROT = mat3(0.00, 0.80, 0.60, -0.80, 0.36, -0.48, -0.60, -0.48, 0.64);
float fbm(vec3 p, int oct){ float s = 0.0, a = 0.5, n = 0.0;
  for (int i = 0; i < 6; i++){ if (i >= oct) break; s += a * vnoise(p); n += a; p = NROT * p * 2.03 + 1.7; a *= 0.5; }
  return s / n; }
`;

// shared runtime helpers: reveal mask (camera-relative angle from the source, in units of the frame half-diagonal)
// and the camera-ray / sky-ellipsoid exit distance
const COMMON = /* glsl */`
uniform vec3 uSrc, uDomeC, uDomeR;
uniform float uFront, uFrontN, uSoft;
float cosmosHalfDiag(mat4 P){ float tv = 1.0 / P[1][1]; float th = 1.0 / P[0][0]; return atan(sqrt(tv * tv + th * th)); }
float cosmosAcos(float x){ float ax = abs(x);
  float r = sqrt(max(0.0, 1.0 - ax)) * (1.5707288 + ax * (-0.2121144 + ax * (0.0742610 - 0.0187293 * ax)));
  return x < 0.0 ? 3.14159265 - r : r; }
// angle between a view ray and the ray to the source, in units of the frame half-diagonal
float cosmosAng(vec3 rd, float hd){ return cosmosAcos(clamp(dot(rd, normalize(uSrc - cameraPosition)), -1.0, 1.0)) / hd; }
float cosmosMaskA(float a, float jit, float front){ return front > 500.0 ? 1.0 : 1.0 - smoothstep(front - uSoft, front, a + jit); }
float cosmosMaskF(vec3 rd, float hd, float jit, float front){ return front > 500.0 ? 1.0 : cosmosMaskA(cosmosAng(rd, hd), jit, front); }
float cosmosMask(vec3 rd, float hd, float jit){ return cosmosMaskF(rd, hd, jit, uFront); }
float cosmosRay(vec3 O, vec3 D){
  vec3 o = (O - uDomeC) / uDomeR, d = D / uDomeR;
  float a = dot(d, d), b = dot(o, d), c = dot(o, o) - 1.0, disc = b * b - a * c;
  if (disc < 0.0) return -1.0;
  return (-b + sqrt(disc)) / a;
}
vec3 cosmosBase(vec3 d){
  vec3 top = vec3(0.0045, 0.0050, 0.026), hor = vec3(0.016, 0.010, 0.046), low = vec3(0.004, 0.016, 0.026);
  vec3 c = mix(hor, top, smoothstep(0.0, 0.85, d.y));
  return mix(c, low, smoothstep(0.0, -0.6, d.y));
}
vec4 cosmosSky(samplerCube tex, vec3 d){ return texture(tex, d); }
`;

// The reveal look shared by the sky shell AND the floor veil, so both surfaces agree exactly where they meet (a view
// ray that just misses the floor and one that just hits it get the same colour): deep space opening behind the front,
// nebulae blooming behind a second front (brighter at its leading edge), the soft unfurling light, the fringe glow.
const REVEAL = /* glsl */`
uniform float uRevA, uBloomA, uBloomR, uFringe;
uniform vec3 uBloomC1, uBloomC2, uBloomC3, uFringeA, uFringeB;
// returns premultiplied colour (rgb) + coverage (a) for camera ray rd (world), d (sky space), sky sample s
vec4 cosmosReveal(vec3 rd, float hd, vec3 d, vec4 s, float neb){
  if (uFront > 500.0) return vec4(cosmosBase(d) + s.rgb * neb, 1.0);    // fully revealed: no masking work
  float an = cosmosAng(rd, hd), jit = (s.a - 0.5) * uSoft * 1.8;
  float m = uRevA * cosmosMaskA(an, jit, uFront);                       // walls dissolve into deep space ...
  float mn = cosmosMaskA(an, jit * 1.4, uFrontN);                       // ... then the nebulae bloom open behind it
  float bl = mn * (1.0 - mn) * 4.0;
  vec3 c = cosmosBase(d) * m + s.rgb * neb * mn * (1.0 + 0.6 * bl * uFringe);
  float x = an / uBloomR;                                               // soft cloudy light unfurling from the source
  float g = uBloomA * exp(-x * x) * (0.3 + 1.1 * s.a * s.a) * m;
  c += mix(mix(uBloomC1, uBloomC2, smoothstep(0.35, 0.65, s.a)), uBloomC3, smoothstep(0.3, 1.0, x)) * g;
  float fr = m * (1.0 - m) * 4.0; fr *= fr;
  c += mix(uFringeA, uFringeB, s.a) * fr * uFringe;
  return vec4(c, m);
}
`;

// cos.dissolve(): patch for host materials (walls, props, cords) so they open with the SAME front as the sky behind
// them. alpha mode (transparent materials): alpha x (1 - mask) + a faint fringe glow; cut mode (opaque clones):
// discard where the front has passed. uCosDis is a live gate (0 whenever this cosmos is not drawing this frame).
const DIS_VS_HEAD = /* glsl */`
${COMMON}
uniform float uCosDis;
varying vec3 vCosRd; varying float vCosHD;
`;
const DIS_VS_BODY = /* glsl */`
vCosRd = mvPosition.xyz * mat3(viewMatrix);                 // world-space ray from the camera (view -> world rotation)
vCosHD = cosmosHalfDiag(projectionMatrix);
if (uCosDis > 0.0 && uFront > 500.0) gl_Position = vec4(0.0, 0.0, 2.0, 1.0);   // fully dissolved: no fragments at all
`;
const DIS_FS_HEAD = /* glsl */`
${COMMON}
uniform float uCosDis, uFringe; uniform vec3 uFringeA, uFringeB;
uniform samplerCube uSky; uniform mat3 uSkyRot;
varying vec3 vCosRd; varying float vCosHD;
`;
const DIS_FS_BODY = /* glsl */`
if (uCosDis > 0.0) {
  vec3 cRd = normalize(vCosRd);
  float cSa = texture(uSky, cRd * uSkyRot).a;
  float cK = uCosDis * cosmosMaskA(cosmosAng(cRd, vCosHD), (cSa - 0.5) * uSoft * 1.8, uFront);
#ifdef COSMOS_DIS_CUT
  if (cK > 0.5) discard;
#else
  float cFr = cK * (1.0 - cK) * 4.0;
  gl_FragColor.rgb += mix(uFringeA, uFringeB, cSa) * (cFr * cFr * 5.0 * uFringe);
  gl_FragColor.a *= 1.0 - cK;
  if (gl_FragColor.a < 0.002) discard;
#endif
}
`;

const QUAD_VS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

// Nebula sky map (equirect, rgb = nebula + band light (linear HDR), a = smooth edge noise for the reveal front).
// Designed as a few distinct cloud complexes separated by deep dark space (so shapes read and faces have calm
// darker sky behind them at eye level in the default front view toward -Z).
const SKY_BAKE_VS = `varying vec3 vDir; void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const SKY_BAKE_FS = /* glsl */`
precision highp float;
varying vec3 vDir;
${NOISE}
float env(vec3 d, vec3 c, float rad){ return exp(-(1.0 - dot(d, normalize(c))) / (rad * rad * 0.5)); }
vec3 cplx(vec3 d, vec3 dir, float rad, float n, float m, vec3 c1, vec3 c2, vec3 hot, float lo, float hi, float amp){
  float e = env(d, dir, rad);
  float dens = smoothstep(lo, hi, n);
  vec3 c = mix(c1, c2, smoothstep(0.3, 0.7, m));
  float core = env(d, dir, rad * 0.38) * dens * dens;
  return (c * (0.035 + dens) + hot * core * 0.9) * e * amp;
}
// warm complex: a saturated amber-gold heart (survives ACES as gold, not salmon) inside rose/peach edges
vec3 warm(vec3 d, vec3 dir, float rad, float n, float lo, float hi, vec3 core, vec3 edge, float amp){
  float e = env(d, dir, rad);
  float dens = smoothstep(lo, hi, n);
  vec3 c = mix(edge, core, env(d, dir, rad * 0.55));
  float hot = env(d, dir, rad * 0.34) * (0.35 + 0.65 * dens);
  return (c * (0.04 + dens) + core * hot * 0.55) * e * amp;
}
void main(){
  vec3 d = normalize(vDir);
  vec3 w = vec3(fbm(d * 1.25 + vec3(1.7, 9.2, 3.1), 4), fbm(d * 1.25 + vec3(8.3, 2.8, 5.4), 4), fbm(d * 1.25 + vec3(4.1, 6.6, 0.7), 4)) - 0.5;
  vec3 q = d + w * 0.7;
  float n1 = fbm(q * 2.1 + 3.0, 5);
  float n2 = fbm(q * 2.6 + 11.0, 5);
  float n3 = fbm(q * 1.7 + 23.0, 5);
  float m1 = fbm(q * 1.2 + 61.0, 3);
  float rid = 1.0 - abs(2.0 * fbm(q * 3.4 + 31.0, 4) - 1.0);
  vec3 dq = normalize(d + w * 0.5);
  vec3 VIO = vec3(0.30, 0.13, 0.85), MAG = vec3(0.62, 0.14, 0.70), TEAL = vec3(0.04, 0.48, 0.52), BLUE = vec3(0.10, 0.22, 0.85),
       ROSE = vec3(0.90, 0.22, 0.45), GOLD = vec3(1.0, 0.58, 0.22), PEACH = vec3(1.0, 0.62, 0.48), WHITE = vec3(1.0, 0.9, 0.95);
  vec3 c = vec3(0.0);
  // A: violet-magenta complex, high behind the characters (keeps the eye-level sky behind faces darker)
  c += cplx(dq, vec3(-0.25, 0.62, -0.95), 0.62, n1, m1, VIO, MAG, mix(WHITE, ROSE, 0.4), 0.42, 0.80, 0.75);
  // B: teal complex, left
  c += cplx(dq, vec3(-0.95, 0.45, -0.30), 0.55, n2, m1, TEAL, BLUE, vec3(0.6, 1.0, 0.95), 0.40, 0.80, 0.85);
  // C: warm gold glow beside the hero galaxy (slightly offset so the galaxy sits on darker sky), magenta-rose edges
  vec3 AMBER = vec3(1.0, 0.56, 0.12), CREAM = vec3(1.0, 0.78, 0.42);
  c += warm(dq, vec3(-0.05, 0.94, -0.30), 0.30, n3, 0.42, 0.80, mix(AMBER, CREAM, 0.15), mix(MAG, ROSE, 0.6), 0.5);
  // W: small warm luminous cloud (amber-gold heart, rose/peach edges) right of / above the Void in the front view,
  // under the hero galaxy in the looking-up view: the warm counterpoint to the cool sky
  c += warm(dq, vec3(0.0, 0.27, -0.96), 0.22, n3, 0.32, 0.74, AMBER, mix(ROSE, PEACH, 0.35), 0.62);
  // D: rose complex, right / low
  c += cplx(dq, vec3(0.98, 0.12, -0.05), 0.50, n1, n2, ROSE, MAG, vec3(1.0, 0.68, 0.40), 0.42, 0.80, 0.7);
  // E: blue-teal behind the camera
  c += cplx(dq, vec3(-0.35, 0.30, 1.0), 0.58, n2, n3, BLUE, TEAL, vec3(0.7, 0.9, 1.0), 0.42, 0.82, 0.7);
  // F: violet-rose behind the camera, right
  c += cplx(dq, vec3(0.70, 0.35, 0.65), 0.48, n3, m1, ROSE, VIO, vec3(1.0, 0.8, 0.9), 0.44, 0.82, 0.6);
  // G: faint teal-blue veil overhead
  c += cplx(dq, vec3(-0.15, 1.0, 0.25), 0.55, n1, n3, TEAL, BLUE, vec3(0.7, 1.0, 1.0), 0.46, 0.85, 0.45);
  // H: dim violet low behind the characters (eye-level glow, kept soft)
  c += cplx(dq, vec3(0.35, 0.02, -1.0), 0.42, n2, m1, BLUE, TEAL, vec3(0.6, 0.85, 1.0), 0.46, 0.88, 0.45);
  // filaments (fine light threads on cloud edges) and dark dust lanes
  c *= 1.0 + 0.6 * pow(rid, 6.0);
  float dl = fbm(q * 3.6 + 51.0, 4);
  float dust = smoothstep(0.52, 0.78, dl);
  c *= 1.0 - 0.62 * dust;
  // gold rim light along the dust-lane edges near the warm clouds
  float rim = smoothstep(0.40, 0.50, dl) * (1.0 - smoothstep(0.50, 0.62, dl));
  float wz = env(dq, vec3(0.0, 0.27, -0.96), 0.42) + 0.7 * env(dq, vec3(-0.05, 0.94, -0.30), 0.45);
  c += mix(AMBER, CREAM, 0.4) * rim * wz * (0.25 + 0.75 * smoothstep(0.35, 0.7, n3)) * 0.16;
  // faint galactic band (tilted great circle)
  vec3 nb = normalize(vec3(-0.55, 0.35, 0.75));
  float bd = dot(d, nb) + (n2 - 0.5) * 0.12;
  float band = exp(-bd * bd / 0.016) * (0.4 + 0.8 * n3);
  c += mix(vec3(0.34, 0.32, 0.62), vec3(0.70, 0.66, 0.85), exp(-bd * bd / 0.004)) * band * 0.06 * (1.0 - 0.7 * dust);
  // below the horizon: deeper, calmer
  c *= mix(1.0, 0.42, smoothstep(0.05, -0.45, d.y));
  gl_FragColor = vec4(c, fbm(d * 2.2 + 40.0, 3));
}`;

// Spiral galaxy (one per texture). p in [-1,1]^2, face-on.
const GAL_BAKE_FS = /* glsl */`
precision highp float;
varying vec2 vUv;
uniform float uArms, uPitch, uSeed, uBar, uTwist;
uniform vec3 uCore, uArm, uArm2, uKnot;
${NOISE}
float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  float r = length(p), th = atan(p.y, p.x);
  float n = fbm(vec3(p * 2.6, uSeed), 5);
  float n2 = fbm(vec3(p * 6.5, uSeed + 3.1), 4);
  float lr = log(max(r, 0.03));
  float ph = uArms * (th - lr / uPitch) + (n - 0.5) * 2.4 + uTwist;
  float arm = pow(0.5 + 0.5 * cos(ph), 1.9);
  float armMask = smoothstep(0.06 + 0.1 * uBar, 0.24, r) * (1.0 - smoothstep(0.55, 0.95, r));
  float armI = arm * armMask * (0.5 + 0.9 * n2);
  float disk = exp(-r * 3.6) * (1.0 - smoothstep(0.6, 1.0, r));
  // bar (stretched bulge) for barred variants
  vec2 pb = vec2(p.x, p.y * mix(1.0, 3.2, uBar));
  float rb = length(pb);
  float bulge = exp(-r * r / 0.007) * 1.35 + exp(-rb * rb / 0.05) * (0.5 + 0.45 * uBar);
  float dust = pow(0.5 + 0.5 * cos(ph - 0.85), 7.0) * smoothstep(0.08, 0.3, r) * (1.0 - smoothstep(0.5, 0.9, r)) * (0.6 + 0.6 * n);
  vec3 armCol = mix(uArm, uArm2, smoothstep(0.25, 0.8, r));
  vec3 c = uCore * bulge + armCol * (armI * 0.8 + disk * 0.3) + uCore * exp(-r * r / 0.09) * 0.25;
  float knots = smoothstep(0.62, 0.82, n2) * pow(arm, 1.5) * armMask * smoothstep(0.2, 0.4, r);
  c += uKnot * knots * 1.3;
  // a few resolved bright stars along the arms (sparse, soft)
  vec2 g = p * 30.0; vec2 gi = floor(g); vec2 gf = fract(g) - 0.5;
  vec2 off = vec2(h12(gi + uSeed * 7.0), h12(gi + uSeed * 7.0 + 19.1)) - 0.5;
  float sd = length(gf - off * 0.5);
  float st = step(0.9, h12(gi + uSeed * 3.0 + 5.0)) * exp(-sd * sd * 22.0) * arm * armMask;
  c += vec3(0.85, 0.92, 1.0) * st * 0.45;
  c *= 1.0 - 0.55 * dust;
  c *= 1.0 - smoothstep(0.72, 1.0, r);
  gl_FragColor = vec4(c, 1.0);
}`;

// 4 soft puff shapes packed in rgba
const PUFF_BAKE_FS = /* glsl */`
precision highp float;
varying vec2 vUv;
${NOISE}
float puff(vec2 p, float k){
  float r = length(p);
  float n = fbm(vec3(p * 1.7, k * 7.3), 5);
  float w = fbm(vec3(p * 3.2 + n * 1.5, k * 3.1 + 2.0), 4);
  float base = exp(-r * r * 2.4) * (1.0 - smoothstep(0.7, 1.0, r));
  return base * smoothstep(0.15, 0.85, n * 0.85 + w * 0.45 + base * 0.35 - 0.2);
}
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  gl_FragColor = vec4(puff(p, 1.0), puff(p, 2.0), puff(p, 3.0), puff(p, 4.0));
}`;

// --- sky shell
const DOME_VS = /* glsl */`
${COMMON}
varying vec3 vWorld; varying float vHD;
void main(){
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorld = wp.xyz;
  vHD = cosmosHalfDiag(projectionMatrix);
  gl_Position = projectionMatrix * viewMatrix * wp;
}`;
const DOME_FS = /* glsl */`
${COMMON}
${REVEAL}
uniform samplerCube uSky; uniform mat3 uSkyRot;
uniform float uIntensity, uNebula;
varying vec3 vWorld; varying float vHD;
void main(){
  vec3 rd = normalize(vWorld - cameraPosition);
  vec3 d = rd * uSkyRot;                 // world -> sky space (uSkyRot is sky -> world)
  vec4 r = cosmosReveal(rd, vHD, d, cosmosSky(uSky, d), uNebula);
#ifdef COSMOS_BLEND
  if (r.a < 0.004) discard;      // not yet revealed here: no colour AND no depth (host far glows stay until the front)
#endif
  gl_FragColor = vec4(r.rgb * uIntensity, r.a);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// --- island underlay: a disc of dark "glass over the universe" just BELOW the floor plane. Depth-tested, so it is
// invisible wherever a host floor exists and only shows when there is none (standalone, or a host that hides its
// floor): the characters always stand on something. Faint mirror of the sky above (fresnel) + a lilac sheen.
const ISLAND_FS = /* glsl */`
${COMMON}
uniform samplerCube uSky; uniform mat3 uSkyRot;
uniform float uIntensity, uNebula, uR0, uR1, uIslA, uIslRefl;
uniform vec3 uCenter, uIslC, uIslSheen;
varying vec3 vWorld; varying float vHD;
void main(){
  vec3 rd = normalize(vWorld - cameraPosition);
  float r = length(vWorld.xz - uCenter.xz);
  float m = 1.0;
  vec3 rr = vec3(rd.x, -rd.y, rd.z);                      // mirror ray (the sky above, reflected)
  vec3 d = rr * uSkyRot;
  vec4 s = cosmosSky(uSky, d);
  if (uFront < 500.0) m = cosmosMaskA(cosmosAng(rd, vHD), (s.a - 0.5) * uSoft * 1.8, uFront);
  float fres = 0.05 + 0.95 * pow(1.0 - clamp(-rd.y, 0.0, 1.0), 4.0);
  vec3 refl = (cosmosBase(d) * 2.0 + s.rgb * uNebula) * (0.12 + 0.55 * fres) * uIslRefl;
  float k = exp(-r * r / (uR0 * uR0 * 0.6));
  vec3 c = uIslC + refl + uIslSheen * k;
  float a = uIslA * m * (1.0 - smoothstep(uR0 * 0.8, uR1, r));
  gl_FragColor = vec4(c * a * uIntensity, a);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// --- floor veil (sky continuation over a host floor + light pool + contact core)
const FLOOR_FS = /* glsl */`
${COMMON}
${REVEAL}
uniform samplerCube uSky; uniform mat3 uSkyRot;
uniform float uIntensity, uNebula, uR0, uR1, uInner, uCover, uGlow, uStars, uContact, uRc;
// procedural star field by direction (continues the far star layer over the host floor, which hides the points)
float hs13(vec3 p){ p = fract(p * 0.1031); p += dot(p, p.zyx + 31.32); return fract((p.x + p.y) * p.z); }
vec3 cosmosStars(vec3 d, float pa){
  vec3 g = d * 38.0; vec3 gi = floor(g);
  float h = hs13(gi);
  if (h < 0.55) return vec3(0.0);
  vec3 sp = normalize(gi + 0.5 + (vec3(hs13(gi + 1.7), hs13(gi + 5.3), hs13(gi + 9.1)) - 0.5) * 0.6) * 38.0;
  float dpx = length(g - sp) / 38.0 / max(pa, 1e-5);
  float L = pow(hs13(gi + 3.3), 6.0);
  float b = (0.25 + 3.0 * L) * exp(-dpx * dpx * 0.9);
  return mix(vec3(1.0, 0.95, 0.9), vec3(0.75, 0.85, 1.0), hs13(gi + 7.7)) * b;
}
uniform vec3 uCenter, uGlowA, uGlowB;
varying vec3 vWorld; varying float vHD;
void main(){
  vec3 rd = normalize(vWorld - cameraPosition);
  vec3 d = rd * uSkyRot;
  vec4 sk = cosmosReveal(rd, vHD, d, cosmosSky(uSky, d), uNebula);   // identical to the shell along this ray
  float m = sk.a;
  float r = length(vWorld.xz - uCenter.xz);
  float rad = mix(uInner, 1.0, smoothstep(uR0, uR1, r)) * uCover;
  vec3 sky = (sk.rgb + cosmosStars(d, length(fwidth(rd))) * uStars * m) * uIntensity;
  // light pool: a bright soft core where the characters stand + a wide faint skirt
  float pool = exp(-r * r / (uR0 * uR0 * 0.16)) * 0.3 + exp(-r * r / (uR0 * uR0 * 0.6)) * 0.14 + exp(-r * r / (uR0 * uR0 * 2.0)) * 0.05;
  vec3 g = mix(uGlowA, uGlowB, smoothstep(0.0, 1.2, r / uR0)) * pool * uGlow * m;
  // contact core: a soft darkening of whatever is under it (premultiplied: coverage with no colour)
  float ct = uContact * exp(-r * r / (uRc * uRc)) * m;
  float a = m * rad;
  gl_FragColor = vec4(sky * rad + g, a + ct * (1.0 - a));
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// --- stars (points). mode 0 = sky (direction attribute, at infinity on the shell), 1 = world positions
const STAR_VS = /* glsl */`
${COMMON}
attribute vec4 aCol;    // rgb, brightness
attribute vec4 aMisc;   // size (px for sky / m for world), phase, twinkle amount, kindle threshold (<0 = mask)
uniform float uMode, uTime, uIntensity, uPxH, uKindle, uSpikeMul;
uniform mat3 uSkyRot;
varying vec3 vCol; varying float vSpike; varying float vSharp;
void main(){
  vec3 wp;
  if (uMode < 0.5) {
    vec3 D = normalize(uSkyRot * position);
    float t = cosmosRay(cameraPosition, D);
    wp = cameraPosition + D * (t > 0.0 ? t * 0.985 : 1000.0);
  } else wp = (modelMatrix * vec4(position, 1.0)).xyz;
  vec4 mv = viewMatrix * vec4(wp, 1.0);
  gl_Position = projectionMatrix * mv;
  float hd = cosmosHalfDiag(projectionMatrix);
  vec3 rd = normalize(wp - cameraPosition);
  float jit = (fract(aMisc.y * 7.13) - 0.5) * uSoft * 1.4;
  float vis;
  float flare = 0.0;
  if (aMisc.w >= 0.0) {             // kindled star: ignites when the reveal passes its threshold
    float k = uKindle - aMisc.w;
    vis = smoothstep(0.0, 0.035, k);
    flare = k > 0.0 ? exp(-k / 0.08) : 0.0;
  } else vis = cosmosMask(rd, hd, jit);
  float tw = 1.0 - aMisc.z * (0.5 + 0.5 * sin(uTime * (0.7 + 1.6 * fract(aMisc.y * 3.7)) + aMisc.y * 6.2831));
  float px = uMode < 0.5 ? aMisc.x : aMisc.x * projectionMatrix[1][1] * uPxH / max(-mv.z, 0.05);
  px *= 1.0 + 1.6 * flare;
  float b = aCol.a * tw * vis * uIntensity * (1.0 + 2.0 * flare);
  b *= smoothstep(0.35, 1.2, -mv.z);                  // fade if almost touching the lens
  // keep footprint >= 3.5 px (stable gaussian, no sub-pixel shimmer); conserve energy
  float minPx = 3.5;
  if (px < minPx) { b *= (px / minPx) * (px / minPx); px = minPx; }
  vSharp = clamp(px / 14.0, 0.0, 1.0);
  gl_PointSize = min(px, 72.0);
  vCol = aCol.rgb * b;
  vSpike = smoothstep(1.2, 3.0, aCol.a) * uSpikeMul + flare;
}`;
const STAR_FS = /* glsl */`
varying vec3 vCol; varying float vSpike; varying float vSharp;
void main(){
  vec2 q = gl_PointCoord * 2.0 - 1.0;
  float r2 = dot(q, q);
  if (r2 > 1.0) discard;
  float core = exp(-r2 * mix(5.0, 26.0, vSharp));
  float halo = exp(-r2 * 3.5) * 0.18 * vSharp;
  float sp = 0.0;
  if (vSpike > 0.01) sp = (exp(-abs(q.x) * 18.0) * exp(-q.y * q.y * 2.2) + exp(-abs(q.y) * 18.0) * exp(-q.x * q.x * 2.2)) * vSpike * 0.5;
  float a = (core + halo + sp) * (1.0 - smoothstep(0.7, 1.0, r2));
  gl_FragColor = vec4(vCol * a, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// --- galaxy discs (at infinity, inclined, spinning)
const GAL_VS = /* glsl */`
${COMMON}
uniform vec3 uGDir, uGU, uGV; uniform float uGSize; uniform mat3 uSkyRot;
varying vec2 vUv; varying float vM;
void main(){
  vec3 D = normalize(uSkyRot * uGDir);
  float t = cosmosRay(cameraPosition, D);
  float dist = (t > 0.0 ? t : 50.0) * 0.9;
  vec3 c = cameraPosition + D * dist;
  vec3 U = uSkyRot * uGU, V = uSkyRot * uGV;
  vec3 wp = c + (position.x * U + position.y * V) * 2.0 * uGSize * dist;
  vUv = position.xy * 2.0;
  vM = cosmosMask(D, cosmosHalfDiag(projectionMatrix), 0.0);
  gl_Position = projectionMatrix * viewMatrix * vec4(wp, 1.0);
}`;
const GAL_FS = /* glsl */`
uniform sampler2D uGal; uniform float uSpin, uAlpha, uIntensity; uniform vec3 uTint;
varying vec2 vUv; varying float vM;
void main(){
  float c = cos(uSpin), s = sin(uSpin);
  vec2 q = mat2(c, -s, s, c) * vUv;
  if (dot(q, q) > 1.0) discard;
  vec3 g = texture2D(uGal, q * 0.5 + 0.5).rgb;
  gl_FragColor = vec4(g * uTint * (uAlpha * vM * uIntensity), 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// --- instanced soft billboards (nebula puffs: channel textures; glyphs: canvas atlas)
const BB_VS = /* glsl */`
${COMMON}
attribute vec3 iPos; attribute vec4 iCol; attribute vec4 iMisc;   // size, rot, cell/channel, mask jitter (<-5 = no mask)
uniform float uCols, uRows, uFlip, uSwell;
varying vec2 vUv; varying vec4 vCol; varying vec4 vCh;
void main(){
  vec4 wc = modelMatrix * vec4(iPos, 1.0);
  vec4 mv = viewMatrix * wc;
  float m = iMisc.w < -5.0 ? 1.0 : cosmosMaskF(normalize(wc.xyz - cameraPosition), cosmosHalfDiag(projectionMatrix), iMisc.w, uFrontN);
  float c = cos(iMisc.y), s = sin(iMisc.y);
  vec2 q = vec2(c * position.x - s * position.y, s * position.x + c * position.y) * iMisc.x * mix(1.0 - uSwell, 1.0, m);
  mv.xy += q;
  gl_Position = projectionMatrix * mv;
  float cell = iMisc.z;
  if (uCols > 0.5) {
    float cx = mod(cell, uCols), cy = floor(cell / uCols);
    if (uFlip > 0.5) cy = uRows - 1.0 - cy;
    vUv = (uv + vec2(cx, cy)) / vec2(uCols, uRows);
    vCh = vec4(0.0, 0.0, 0.0, 1.0);
  } else {
    vUv = uv;
    vCh = vec4(cell < 0.5 ? 1.0 : 0.0, abs(cell - 1.0) < 0.5 ? 1.0 : 0.0, abs(cell - 2.0) < 0.5 ? 1.0 : 0.0, cell > 2.5 ? 1.0 : 0.0);
  }
  float nf = smoothstep(0.3, 1.0, -mv.z);
  vCol = vec4(iCol.rgb, iCol.a * m * nf);
}`;
const BB_FS = /* glsl */`
uniform sampler2D map; uniform float uIntensity;
varying vec2 vUv; varying vec4 vCol; varying vec4 vCh;
void main(){
  vec4 t = texture2D(map, vUv);
  float a = dot(t, vCh);
  if (a * vCol.a < 0.003) discard;
  gl_FragColor = vec4(vCol.rgb * (uIntensity * a * vCol.a), 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// ------------------------------------------------------------------------------------------------ bake helpers
function bake(renderer, fs, w, h, uniforms = {}, { mip = false, wrapS = THREE.ClampToEdgeWrapping } = {}) {
  const rt = new THREE.WebGLRenderTarget(w, h, {
    type: THREE.HalfFloatType, format: THREE.RGBAFormat, depthBuffer: false, stencilBuffer: false,
    generateMipmaps: mip, minFilter: mip ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter, magFilter: THREE.LinearFilter,
    wrapS, wrapT: THREE.ClampToEdgeWrapping,
  });
  const mat = new THREE.ShaderMaterial({ uniforms, vertexShader: QUAD_VS, fragmentShader: fs, depthTest: false, depthWrite: false });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat); quad.frustumCulled = false;
  const sc = new THREE.Scene(); sc.add(quad);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const prev = renderer.getRenderTarget();
  const prevClear = renderer.getClearColor(new THREE.Color()), prevA = renderer.getClearAlpha();
  renderer.setClearColor(0x000000, 0);
  renderer.setRenderTarget(rt); renderer.render(sc, cam); renderer.setRenderTarget(prev);
  renderer.setClearColor(prevClear, prevA);
  mat.dispose(); quad.geometry.dispose();
  return rt.texture;
}

// bake a direction -> colour shader into a cube map (CubeCamera at the origin inside a big inverted sphere)
function bakeCube(renderer, vs, fs, size) {
  const crt = new THREE.WebGLCubeRenderTarget(size, { type: THREE.HalfFloatType, generateMipmaps: false,
    minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
  const mat = new THREE.ShaderMaterial({ vertexShader: vs, fragmentShader: fs, side: THREE.BackSide, depthTest: false, depthWrite: false });
  const sph = new THREE.Mesh(new THREE.SphereGeometry(10, 96, 64), mat); sph.frustumCulled = false;
  const sc = new THREE.Scene(); sc.add(sph);
  const cc = new THREE.CubeCamera(0.1, 100, crt);
  const prev = renderer.getRenderTarget();
  cc.update(renderer, sc);
  renderer.setRenderTarget(prev);
  mat.dispose(); sph.geometry.dispose();
  return crt.texture;
}

function glyphAtlas() {
  const S = 128, c = document.createElement('canvas'); c.width = S * 3; c.height = S * 2;
  const g = c.getContext('2d');
  const cell = (i, fn) => { g.save(); g.translate((i % 3) * S + S / 2, Math.floor(i / 3) * S + S / 2); fn(); g.restore(); };
  const cap = (x0, y0, x1, y1, w) => { g.lineWidth = w; g.lineCap = 'round'; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); };
  g.fillStyle = '#fff'; g.strokeStyle = '#fff';
  const glow = () => { g.shadowColor = 'rgba(255,255,255,0.9)'; g.shadowBlur = 14; };
  cell(0, () => { glow(); g.beginPath(); g.moveTo(0, 30); g.bezierCurveTo(-52, -4, -26, -46, 0, -18); g.bezierCurveTo(26, -46, 52, -4, 0, 30); g.fill(); });
  cell(1, () => { glow(); g.beginPath(); g.arc(0, 0, 17, 0, TAU); g.fill();
    for (let k = 0; k < 8; k++) { const a = k * TAU / 8; cap(Math.cos(a) * 25, Math.sin(a) * 25, Math.cos(a) * 36, Math.sin(a) * 36, 6); } });
  cell(2, () => { glow(); g.save(); g.translate(-10, 22); g.rotate(-0.45); g.beginPath(); g.ellipse(0, 0, 12, 8.5, 0, 0, TAU); g.fill(); g.restore();
    cap(1, 19, 1, -32, 5); g.beginPath(); g.moveTo(1, -34); g.quadraticCurveTo(24, -22, 20, -2); g.quadraticCurveTo(16, -16, 1, -18); g.fill(); });
  cell(3, () => { glow(); g.beginPath(); g.moveTo(-30, -2); g.lineTo(0, -30); g.lineTo(30, -2); g.lineTo(24, -2); g.lineTo(24, 28); g.lineTo(-24, 28); g.lineTo(-24, -2); g.closePath(); g.fill();
    g.shadowBlur = 0; g.globalCompositeOperation = 'destination-out'; g.beginPath(); g.roundRect(-6, 8, 12, 20, 5); g.fill(); g.globalCompositeOperation = 'source-over'; });
  cell(4, () => { glow(); g.beginPath(); g.ellipse(0, 12, 19, 20, 0, 0, TAU); g.fill();
    cap(-13, -2, -17, -26, 9); cap(-4, -6, -5, -34, 9); cap(5, -6, 7, -33, 9); cap(13, -1, 17, -24, 8); cap(-17, 14, -32, 2, 9); });
  cell(5, () => { glow(); g.rotate(-0.7); g.beginPath(); g.roundRect(-7, -30, 14, 46, 3); g.fill();
    g.beginPath(); g.moveTo(-7, 16); g.lineTo(7, 16); g.lineTo(0, 34); g.closePath(); g.fill(); g.beginPath(); g.roundRect(-7, -40, 14, 8, 3); g.fill(); });
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  tex.generateMipmaps = true; tex.minFilter = THREE.LinearMipmapLinearFilter;
  return tex;
}

// ------------------------------------------------------------------------------------------------ billboards
class Billboards {
  constructor({ max, map, cols = 0, rows = 1, flip = 0, intensity = 1, renderOrder = 0, swell = 0 }) {
    this.max = max;
    const g = new THREE.InstancedBufferGeometry();
    const base = new THREE.PlaneGeometry(1, 1);
    g.index = base.index; g.setAttribute('position', base.attributes.position); g.setAttribute('uv', base.attributes.uv);
    const mk = (n) => new THREE.InstancedBufferAttribute(new Float32Array(max * n), n).setUsage(THREE.DynamicDrawUsage);
    this.aPos = mk(3); this.aCol = mk(4); this.aMisc = mk(4);
    g.setAttribute('iPos', this.aPos); g.setAttribute('iCol', this.aCol); g.setAttribute('iMisc', this.aMisc);
    g.instanceCount = 0;
    this.u = { map: { value: map }, uIntensity: { value: intensity }, uCols: { value: cols }, uRows: { value: rows },
      uFlip: { value: flip }, uSwell: { value: swell } };
    this.mat = new THREE.ShaderMaterial({ uniforms: this.u, vertexShader: BB_VS, fragmentShader: BB_FS, transparent: true,
      depthWrite: false, blending: THREE.AdditiveBlending });
    this.mesh = new THREE.Mesh(g, this.mat); this.mesh.frustumCulled = false; this.mesh.renderOrder = renderOrder;
    this.geo = g; this.n = 0;
  }
  begin() { this.n = 0; }
  add(p, size, c, alpha, rot, cell, jit = 0) {
    if (this.n >= this.max || alpha <= 0.002) return;
    const i = this.n++;
    this.aPos.array.set([p.x, p.y, p.z], i * 3);
    this.aCol.array.set([c.r, c.g, c.b, alpha], i * 4);
    this.aMisc.array.set([size, rot, cell, jit], i * 4);
  }
  end() { this.geo.instanceCount = this.n; this.aPos.needsUpdate = this.aCol.needsUpdate = this.aMisc.needsUpdate = true; }
}

// ------------------------------------------------------------------------------------------------ the set
class CosmosSet {
  constructor() {
    const renderer = CTX.renderer;
    if (!renderer) throw new Error('COSMOS: CTX.renderer is not set (create the set after main.js init)');
    this.skyTex = bakeCube(renderer, SKY_BAKE_VS, SKY_BAKE_FS, 640);
    this.puffTex = bake(renderer, PUFF_BAKE_FS, 256, 256, {}, { mip: false });   // always magnified: no mips
    const GV = [   // galaxy bake variants
      { uArms: 2, uPitch: 0.36, uSeed: 1.3, uBar: 0.0, uTwist: 0.0, uCore: 0xffd9a0, uArm: 0xb4c6ff, uArm2: 0x8a7cff, uKnot: 0xff7fb4 },
      { uArms: 2, uPitch: 0.30, uSeed: 4.7, uBar: 0.65, uTwist: 1.0, uCore: 0xffe2b0, uArm: 0x9ff0f0, uArm2: 0x5aa8ff, uKnot: 0xffa0c8 },
      { uArms: 3, uPitch: 0.42, uSeed: 7.9, uBar: 0.0, uTwist: 2.0, uCore: 0xffd0b0, uArm: 0xd6b4ff, uArm2: 0xff8fc0, uKnot: 0xffd27a },
      { uArms: 2, uPitch: 0.26, uSeed: 9.4, uBar: 0.2, uTwist: 0.5, uCore: 0xfff0c8, uArm: 0xc8d4ff, uArm2: 0xb48cff, uKnot: 0x7fe8e0 },
    ];
    this.galTex = GV.map((o) => {
      const u = {};
      for (const k in o) u[k] = { value: ['uCore', 'uArm', 'uArm2', 'uKnot'].includes(k) ? col(o[k]) : o[k] };
      return bake(renderer, GAL_BAKE_FS, 512, 512, u, { mip: true });
    });
    this.glyphTex = glyphAtlas();

    this.scene = new THREE.Scene();
    this.scene.background = col(0x05051a);
    this.group = new THREE.Group(); this.group.name = 'COSMOS';
    this.scene.add(this.group);

    // shared uniforms (same objects referenced by every cosmos material)
    this.U = {
      uSrc: { value: V3(0, 1.6, 0) }, uDomeC: { value: V3(0, 1.5, 0) }, uDomeR: { value: V3(7.5, 6.5, 7.5) },
      uFront: { value: 1e3 }, uFrontN: { value: 1e3 }, uSoft: { value: 0.3 },
      uSkyRot: { value: new THREE.Matrix3() }, uTime: { value: 0 },
    };
    const U = this.U;
    // reveal look (shell + floor veil + host dissolve share these objects)
    this.RU = { uRevA: { value: 1 }, uBloomA: { value: 0 }, uBloomR: { value: 1 }, uFringe: { value: 1 },
      uBloomC1: { value: col(0x9a6cff) }, uBloomC2: { value: col(0xff7fb8) }, uBloomC3: { value: col(0x3fd8d0) },
      uFringeA: { value: col(0x9a7cff).multiplyScalar(0.07) }, uFringeB: { value: col(0x6fe0e8).multiplyScalar(0.05) } };
    const RU = this.RU;
    const premul = { blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
      blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor };

    // sky shell. It writes depth (at the shell), so host TRANSPARENT things farther than the shell (BACKROOM's own far
    // backdrop stars / nebula sprites / screen glow) are hidden behind the cosmos instead of floating over it.
    this.domeU = { ...U, ...RU, uSky: { value: this.skyTex }, uIntensity: { value: 1 }, uNebula: { value: 1 } };
    // two programs: blended (while revealing; first among transparents) and solid (reveal 1: an opaque pass drawn
    // after the host's opaque objects, no blending, no discard — ~0.03 s cheaper on SwiftShader, identical pixels)
    this.domeMatB = new THREE.ShaderMaterial({ uniforms: this.domeU, vertexShader: DOME_VS, fragmentShader: DOME_FS, side: THREE.BackSide,
      transparent: true, depthWrite: true, defines: { COSMOS_BLEND: 1 }, ...premul });
    this.domeMatS = new THREE.ShaderMaterial({ uniforms: this.domeU, vertexShader: DOME_VS, fragmentShader: DOME_FS, side: THREE.BackSide,
      transparent: false, depthWrite: true, blending: THREE.NoBlending });
    this.dome = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 40), this.domeMatB);
    this.dome.frustumCulled = false; this.dome.renderOrder = -40;
    this.group.add(this.dome);

    // island underlay (below the floor plane; only visible where there is no host floor)
    const fg = new THREE.CircleGeometry(1, 96); fg.rotateX(-Math.PI / 2);
    this.islandU = { ...U, uSky: { value: this.skyTex }, uIntensity: { value: 1 }, uNebula: { value: 1 }, uR0: { value: 2.2 },
      uR1: { value: 5.5 }, uIslA: { value: 1 }, uIslRefl: { value: 1 }, uCenter: { value: V3() },
      uIslC: { value: col(0x2a2048) }, uIslSheen: { value: col(0xb49cff).multiplyScalar(0.05) } };
    this.island = new THREE.Mesh(fg, new THREE.ShaderMaterial({
      uniforms: this.islandU, vertexShader: DOME_VS, fragmentShader: ISLAND_FS, transparent: true, depthWrite: false, ...premul,
    }));
    this.island.frustumCulled = false; this.island.renderOrder = -37;
    this.group.add(this.island);

    // floor veil
    this.floorU = { ...U, ...RU, uSky: { value: this.skyTex }, uIntensity: { value: 1 }, uNebula: { value: 1 }, uR0: { value: 2.2 },
      uR1: { value: 5.5 }, uInner: { value: 0 }, uCover: { value: 1 }, uGlow: { value: 0.5 }, uCenter: this.islandU.uCenter,
      uGlowA: { value: col(0x8f7cff).multiplyScalar(0.55) }, uGlowB: { value: col(0x35c8d8).multiplyScalar(0.35) }, uStars: { value: 1 },
      uContact: { value: 0 }, uRc: { value: 1.2 } };
    this.floor = new THREE.Mesh(fg, new THREE.ShaderMaterial({
      uniforms: this.floorU, vertexShader: DOME_VS, fragmentShader: FLOOR_FS, transparent: true, depthWrite: false, ...premul,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
    }));
    this.floor.frustumCulled = false; this.floor.renderOrder = -35;
    this.group.add(this.floor);

    // host dissolve (cos.dissolve): shared uniforms + a LIVE gate. The gate is non-zero only while THIS cosmos is drawn
    // in the scene being rendered and was updated for this frame (see attach()), so patched host materials behave
    // exactly as before in every other scene / frame that renders the host without the cosmos.
    const self = this;
    this._live = false; this._renderScene = null; this._disW = 0;
    this.disU = { uSrc: U.uSrc, uDomeC: U.uDomeC, uDomeR: U.uDomeR, uFront: U.uFront, uFrontN: U.uFrontN, uSoft: U.uSoft,
      uSkyRot: U.uSkyRot, uSky: { value: this.skyTex }, uFringe: RU.uFringe, uFringeA: RU.uFringeA, uFringeB: RU.uFringeB,
      uCosDis: { get value() { return self._disGate(); }, set value(v) { /* read-only (driven by update) */ } } };
    this._disClones = new WeakMap();

    // stars
    const starMat = (mode, spike) => new THREE.ShaderMaterial({
      uniforms: { ...U, uMode: { value: mode }, uIntensity: { value: 1 }, uPxH: { value: CTX.H / 2 }, uKindle: { value: 1 }, uSpikeMul: { value: spike } },
      vertexShader: STAR_VS, fragmentShader: STAR_FS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    this.far = this._stars(this._farStars(2600), starMat(0, 0.8), -30);
    this.mid = this._stars(this._shellStars(520), starMat(1, 0.6), -20);
    this.near = this._stars(this._nearStars(72), starMat(1, 1.0), -10);
    this.midGroup = new THREE.Group(); this.group.add(this.midGroup);
    this.nearGroup = new THREE.Group(); this.group.add(this.nearGroup);
    this.group.add(this.far.pts); this.midGroup.add(this.mid.pts); this.nearGroup.add(this.near.pts);

    // nebula puffs (world, mid layer)
    this.puffs = new Billboards({ max: PUFFS.length, map: this.puffTex, cols: 0, intensity: 1, renderOrder: -28, swell: 0.35 });
    Object.assign(this.puffs.u, U);
    this.midGroup.add(this.puffs.mesh);

    // galaxies
    this.gals = GALAXIES.map((G, i) => {
      // plane basis: normal faces the viewer (−dir), tilted by incl about an in-plane axis, rotated by pa
      const n0 = G.dir.clone().negate();
      const a = Math.abs(n0.y) > 0.9 ? V3(1, 0, 0) : V3(0, 1, 0);
      const e1 = a.clone().cross(n0).normalize(), e2 = n0.clone().cross(e1).normalize();
      const q = new THREE.Quaternion().setFromAxisAngle(n0, G.pa);
      const e1r = e1.clone().applyQuaternion(q), e2r = e2.clone().applyQuaternion(q);
      const tilt = new THREE.Quaternion().setFromAxisAngle(e1r, G.incl);
      const u = { ...U, uGal: { value: this.galTex[G.v] }, uGDir: { value: G.dir.clone() }, uGU: { value: e1r.clone().applyQuaternion(tilt) },
        uGV: { value: e2r.clone().applyQuaternion(tilt) }, uGSize: { value: G.size }, uSpin: { value: 0 }, uAlpha: { value: 0 },
        uIntensity: { value: 1 }, uTint: { value: col(G.tint) } };
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShaderMaterial({ uniforms: u, vertexShader: GAL_VS, fragmentShader: GAL_FS,
        transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }));
      m.frustumCulled = false; m.renderOrder = -25 + i * 0.1;
      this.group.add(m);
      return { G, m, u, dir0: G.dir.clone() };
    });

    // bits of meaning
    this.glyphs = new Billboards({ max: 12, map: this.glyphTex, cols: 3, rows: 2, flip: 1, intensity: 1, renderOrder: -5 });
    Object.assign(this.glyphs.u, U);
    this.nearGroup.add(this.glyphs.mesh);
    const r = rng(777);
    this.glyphDefs = Array.from({ length: 9 }, (_, i) => ({
      cell: i % 6, col: col(GLYPH_COLS[i % 6]), a0: r() * TAU, rad: 1.9 + r() * 1.6, h: 0.2 + r() * 2.0, sp: (0.035 + r() * 0.03) * (r() < 0.5 ? -1 : 1),
      size: 0.11 + r() * 0.06, ph: r() * TAU, th: 0.62 + 0.3 * (i / 9),
    }));

    // lights (intensity follows reveal)
    this.hemi = new THREE.HemisphereLight(0x9a8cff, 0x1d5c6c, 0); this.group.add(this.hemi);
    this.key = new THREE.DirectionalLight(0xfff0dc, 0); this.group.add(this.key); this.group.add(this.key.target);
    // standalone-only: a soft lilac front fill so faces read (inner beings bring their own fresnel rims)
    this.fill = new THREE.DirectionalLight(0xc8b8ff, 0.6); this.fill.position.set(2, 2.5, 6); this.scene.add(this.fill);

    this.look = { bloom: 0.7, bloomRadius: 0.62, bloomThreshold: 0.72, vignette: 0.3, sat: 1.08, warm: 0.0,
      lift: [0.004, 0.003, 0.012], exposure: 1.05 };
    this.anchors = { center: V3(), source: V3(), domeCenter: V3(), hero: V3(), galaxies: GALAXIES.map(() => V3()), nebula: V3(), up: V3() };
    this.props = { dome: this.dome, floor: this.floor, island: this.island, far: this.far.pts, mid: this.mid.pts, near: this.near.pts,
      puffs: this.puffs.mesh, galaxies: this.gals.map((g) => g.m), glyphs: this.glyphs.mesh, hemi: this.hemi, key: this.key, skyTex: this.skyTex };
    this._q = new THREE.Quaternion(); this._m4 = new THREE.Matrix4();
    for (const k of ['update', 'attach', 'blendLook', 'dissolve', 'hostFade']) this[k] = this[k].bind(this);
    this.update(0, { eyeLight: 0 });
  }

  // dissolve gate (read by the patched host shaders at uniform-upload time, i.e. inside renderer.render)
  _disGate() {
    return this._disW > 0 && this._live && this.group.visible && this.group.parent !== null && this.group.parent === this._renderScene ? this._disW : 0;
  }

  /** Host fade value for a host that fades its own room by a 0..1 param (BACKROOM `cosmos`): its walls/props/lights
   *  follow the reveal, but it is CAPPED at .97 so the host never reaches its hard toggles (BACKROOM hides its bulbs at
   *  .98 and its whole room group, floor included, at .999) — the host floor stays and the floor veil makes the island. */
  hostFade(reveal) { return 0.97 * smooth(clamp(reveal / 0.8)); }

  /**
   * Make host objects open with the SAME front as the sky (walls, pipes, boxes, cords dissolve outward from the source as
   * seen by the current camera, instead of cross-fading uniformly). target: Object3D | Material | array of them.
   * Transparent materials are patched IN PLACE (alpha x (1 - mask), faint fringe glow at the edge). Opaque materials
   * are skipped unless opts.opaque: then each mesh gets a patched CLONE that is cut (discarded) behind the front (the
   * original, possibly shared material is untouched). A material's `userData.twin` (BACKROOM's transparent fade twins)
   * is patched too, so one call at setup is enough. Idempotent (call once or every frame). The patch is inert (gate 0)
   * whenever this cosmos is not drawn in the scene being rendered, and at reveal 1 patched geometry emits no fragments.
   */
  dissolve(target, opts = {}) {
    const list = Array.isArray(target) ? target : [target];
    const doMat = (m, ob, i) => {
      if (!m || m.isShaderMaterial || m.isSpriteMaterial || m.isPointsMaterial || m.isLineBasicMaterial) return m;
      if (m.userData.twin) this._patch(m.userData.twin, false);
      if (m.userData.cosmosDis) return m;
      if (m.transparent) { this._patch(m, false); return m; }
      if (!opts.opaque || !ob) return m;
      let c = this._disClones.get(m);
      if (!c) {
        c = m.clone();
        c.onBeforeCompile = m.onBeforeCompile; c.customProgramCacheKey = m.customProgramCacheKey;   // keep any existing patch
        this._patch(c, true);
        this._disClones.set(m, c);
      }
      return c;
    };
    for (const t of list) {
      if (!t) continue;
      if (t.isMaterial) { doMat(t, null); continue; }
      t.traverse((ob) => {
        if (!ob.isMesh || !ob.material) return;
        if (Array.isArray(ob.material)) ob.material = ob.material.map((m) => doMat(m, ob));
        else ob.material = doMat(ob.material, ob);
      });
    }
    return this;
  }

  _patch(m, cut) {
    if (m.userData.cosmosDis) return;
    m.userData.cosmosDis = cut ? 'cut' : 'alpha';
    const P = THREE.Material.prototype;
    const prev = m.onBeforeCompile !== P.onBeforeCompile ? m.onBeforeCompile : null;
    const prevKey = m.customProgramCacheKey !== P.customProgramCacheKey ? m.customProgramCacheKey : null;
    const key0 = prev ? prev.toString() : '';
    const DU = this.disU;
    m.onBeforeCompile = function (sh, r) {
      if (prev) prev.call(this, sh, r);
      Object.assign(sh.uniforms, DU);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\n' + DIS_VS_HEAD)
        .replace('#include <project_vertex>', '#include <project_vertex>\n' + DIS_VS_BODY);
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\n' + (cut ? '#define COSMOS_DIS_CUT\n' : '') + DIS_FS_HEAD)
        .replace('#include <dithering_fragment>', '#include <dithering_fragment>\n' + DIS_FS_BODY);
    };
    m.customProgramCacheKey = function () { return (prevKey ? prevKey.call(this) : key0) + '|cosmosDis:' + (cut ? 'cut' : 'alpha'); };
    m.needsUpdate = true;
  }

  // ---- star generation (deterministic)
  _stars(data, mat, order) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(data.pos, 3));
    g.setAttribute('aCol', new THREE.BufferAttribute(data.col, 4));
    g.setAttribute('aMisc', new THREE.BufferAttribute(data.misc, 4));
    const pts = new THREE.Points(g, mat); pts.frustumCulled = false; pts.renderOrder = order;
    return { pts, mat, data };
  }
  _starColor(r, out) {
    const k = r();
    if (k < 0.45) out.setRGB(1.0, 0.97, 0.92); else if (k < 0.7) out.setRGB(0.78, 0.86, 1.0);
    else if (k < 0.85) out.setRGB(1.0, 0.86, 0.66); else if (k < 0.94) out.setRGB(0.72, 1.0, 0.96); else out.setRGB(1.0, 0.75, 0.88);
    return out;
  }
  _farStars(n) {
    const r = rng(4242), pos = new Float32Array(n * 3), cl = new Float32Array(n * 4), misc = new Float32Array(n * 4);
    const nb = nrm(-0.55, 0.35, 0.75), c = new THREE.Color(), d = V3();
    let i = 0, guard = 0;
    while (i < n && guard++ < n * 20) {
      const z = r() * 2 - 1, a = r() * TAU, s = Math.sqrt(1 - z * z);
      d.set(s * Math.cos(a), z, s * Math.sin(a));
      const band = Math.exp(-(d.dot(nb) ** 2) / 0.03);
      if (r() > 0.35 + 0.65 * band) continue;        // denser in the galactic band
      pos.set([d.x, d.y, d.z], i * 3);
      const L = Math.pow(r(), 5.5);                    // power-law brightness: most faint, few bright
      const b = 0.22 + 3.4 * L;
      this._starColor(r, c);
      cl.set([c.r, c.g, c.b, b], i * 4);
      const tw = L > 0.15 ? 0.12 + 0.2 * r() : (r() < 0.12 ? 0.25 : 0);
      misc.set([3.6 + 3.2 * Math.sqrt(L) + r() * 0.8, r(), tw, -1], i * 4);
      i++;
    }
    return { pos: pos.subarray(0, i * 3), col: cl.subarray(0, i * 4), misc: misc.subarray(0, i * 4) };
  }
  _shellStars(n) {   // mid layer in unit-dome space (the mid group is scaled to the dome radii)
    const r = rng(9191), pos = new Float32Array(n * 3), cl = new Float32Array(n * 4), misc = new Float32Array(n * 4), c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      const z = r() * 1.6 - 0.6, a = r() * TAU, s = Math.sqrt(1 - z * z), d = 0.42 + 0.5 * r();
      pos.set([s * Math.cos(a) * d, z * d, s * Math.sin(a) * d], i * 3);
      const L = Math.pow(r(), 4);
      this._starColor(r, c);
      cl.set([c.r, c.g, c.b, 0.45 + 2.6 * L], i * 4);
      misc.set([0.018 + 0.03 * L + 0.006 * r(), r(), L > 0.2 ? 0.2 : 0.06, -1], i * 4);
    }
    return { pos, col: cl, misc };
  }
  _nearStars(n) {    // metres around the source; the first 26 kindle one by one during reveal 0.02..0.3
    const r = rng(5151), pos = new Float32Array(n * 3), cl = new Float32Array(n * 4), misc = new Float32Array(n * 4), c = new THREE.Color();
    const NK = 26;
    for (let i = 0; i < n; i++) {
      const kind = i < NK;
      const z = r() * 1.7 - 0.7, a = r() * TAU, s = Math.sqrt(1 - z * z);
      const d = kind ? 0.9 + 1.6 * Math.pow(i / NK, 0.7) + 0.3 * r() : 1.6 + 2.6 * r();
      pos.set([s * Math.cos(a) * d, z * d * 0.8 + 0.2, s * Math.sin(a) * d], i * 3);
      this._starColor(r, c); if (kind && r() < 0.5) c.setRGB(1.0, 0.95, 0.85);
      const L = kind ? 0.5 + 0.5 * r() : Math.pow(r(), 2);
      cl.set([c.r, c.g, c.b, 0.9 + 2.2 * L], i * 4);
      misc.set([0.022 + 0.026 * L, r(), 0.14 + 0.12 * r(), kind ? 0.05 + 0.85 * (i / NK) + 0.04 * r() : -1], i * 4);
    }
    return { pos, col: cl, misc };
  }

  /**
   * Attach the cosmos group to a host scene (call every frame BEFORE update(); idempotent). The first attach to a scene
   * chains its onBeforeRender/onAfterRender: the group is drawn only in a render that follows an update() (a frame of
   * another scene that renders the same host without updating the cosmos does not show stale cosmos state), and the
   * dissolve gate knows which scene is being rendered.
   */
  attach(scene) {
    if (this.group.parent !== scene) scene.add(this.group);
    if (!scene.userData.cosmosHooked) {
      scene.userData.cosmosHooked = true;
      const self = this, prevB = scene.onBeforeRender, prevA = scene.onAfterRender;
      scene.onBeforeRender = function (...a) {
        if (self.group.parent === scene) { self._renderScene = scene; if (!self._live) self.group.visible = false; }
        return prevB.apply(this, a);
      };
      scene.onAfterRender = function (...a) {
        if (self.group.parent === scene) { self._live = false; self._renderScene = null; }
        return prevA.apply(this, a);
      };
    }
    return this;
  }

  /** Post look blended from a host look (e.g. BACKROOM's) toward the cosmos look by w (0..1). */
  blendLook(base = {}, w = 1) {
    const out = { ...base };
    for (const k of Object.keys(this.look)) {
      const b = this.look[k], a = base[k] ?? b;
      out[k] = Array.isArray(b) ? b.map((x, i) => lerp(Array.isArray(a) ? a[i] : x, x, w)) : lerp(a, b, w);
    }
    return out;
  }

  /**
   * update(t, opts) — pure function of (t, opts). Full table: docs/sets/cosmos.md.
   *  reveal 0..1        0 = nothing; .015–.29 near stars kindle around `source`; .12–~.75 walls dissolve into deep space
   *                     outward from the source (camera-relative); .14–.72 a soft light unfurls behind the source;
   *                     .24–~.85 nebulae bloom open; .5–1 galaxies drift in; .62–1 glyphs. 1 = everything (cheapest).
   *  center [x,y,z]     floor point the cosmos surrounds (the characters' spot). Default [0,0,0]. (Vector3 ok)
   *  source [x,y,z]     where the reveal starts (the Void's chest anchor). Default center + [0,1.6,0]. (Vector3 ok)
   *  radius (m)         horizontal radius of the sky shell (default 7.5): geometry farther than the shell is covered.
   *  height (m)         vertical semi-axis of the shell (default 0.87·radius). Shell centre = center + [0, lift, 0].
   *  lift (m)           shell centre height above `center` (default 1.5).
   *  drift              speed multiplier for slow motion (bounded sky drift, galaxy spin, orbits). Default 1.
   *  clock              explicit motion clock (s) instead of t·drift (use when animating drift).
   *  intensity          global brightness multiplier (default 1).
   *  stars, nebula, galaxies, glyphs, puffs   per-element multipliers (default 1; 0 hides + skips the draw).
   *  bloom, fringe      mid-reveal unfurling light / dissolve-front glow (default 1).
   *  light              cosmic key (+ hemi standalone) multiplier (default 1). hemi: also add the hemi in a host.
   *  floor { cover, inner, r0, r1, glow, contact, rc, island, islandR, reflect }
   *                     cover: sky over the host floor beyond r0..r1 (default 1 host / 0 standalone; r0 1.8 / 2.2, r1 4.4 / 5.5);
   *                     inner: sky tint inside r0; glow: light pool (default .6 host / 1 standalone); contact: soft dark
   *                     core of radius rc (1.25 m) under `center` (default .28 / .3); island: alpha of the glass island
   *                     under the floor plane (1 host — only seen if the host floor is gone — / .6 standalone), radius
   *                     islandR (default r1 host / 3.6 standalone), reflect: its sky-mirror strength (1).
   *  dissolve 0..1      strength of the host dissolve (cos.dissolve-patched materials) (default 1).
   *  eyeLight 0..1      blend EYE_LIGHT toward the cosmos key (default 1 standalone, 0 in a host). Set from a fixed base
   *                     (standalone: engine defaults; host: what the host set this frame — call after the host's update).
   *  standalone         force standalone/host defaults (default: group.parent === this.scene).
   *  blendShell         keep the shell blended at reveal 1 (default false: opaque pass, same pixels, cheaper).
   */
  update(t, opts = {}) {
    const standalone = opts.standalone ?? (this.group.parent === this.scene);
    const reveal = clamp(opts.reveal ?? 1);
    const c = arr3(opts.center, [0, 0, 0]);
    const radius = opts.radius ?? 7.5, height = opts.height ?? radius * 0.87, lift = opts.lift ?? 1.5;
    const src = arr3(opts.source, [c[0], c[1] + 1.6, c[2]]);
    const clock = opts.clock ?? t * (opts.drift ?? 1);
    const I = opts.intensity ?? 1;
    const U = this.U, RU = this.RU;
    this._live = true; this.group.visible = true;      // drawn in the next render of the host (see attach())
    U.uTime.value = t;
    U.uSrc.value.set(src[0], src[1], src[2]);
    U.uDomeC.value.set(c[0], c[1] + lift, c[2]);
    U.uDomeR.value.set(radius, height, radius);
    this.dome.position.copy(U.uDomeC.value); this.dome.scale.copy(U.uDomeR.value);
    this.midGroup.position.copy(U.uDomeC.value); this.midGroup.scale.copy(U.uDomeR.value);
    this.nearGroup.position.set(src[0], src[1], src[2]);

    // sky rotation (sky -> world)
    // bounded drift: starts at SKY_RATE rad/s and never wanders more than ±SKY_SWING from the designed layout,
    // so compositions (which galaxy is where) do not depend on absolute film time
    const ang = SKY_SWING * Math.sin(clock * SKY_RATE / SKY_SWING);
    this._q.setFromAxisAngle(SKY_AXIS, ang);
    U.uSkyRot.value.setFromMatrix4(this._m4.makeRotationFromQuaternion(this._q));
    this.midGroup.quaternion.setFromAxisAngle(SKY_AXIS, ang * 0.7);

    // reveal stages
    const kindle = clamp(reveal / 0.3);
    // front radius in frame half-diagonals: ~linear across the frame (1.9 per unit), then races around the sphere
    const fr = (u) => (u >= 0.999 || reveal >= 0.999 ? 1e3 : 1.9 * u + 0.3 * Math.pow(u, 6) / (1 - u));
    const ub = clamp((reveal - 0.12) / 0.72), un = clamp((reveal - 0.24) / 0.72);
    const front = fr(ub);
    U.uFront.value = front; U.uFrontN.value = un <= 0 ? -1 : fr(un);
    U.uSoft.value = 0.22 + 0.22 * Math.min(front, 3);
    const galStage = clamp((reveal - 0.5) / 0.5);
    const glyphStage = clamp((reveal - 0.6) / 0.4);

    // shell + floor
    const D = this.domeU;
    D.uIntensity.value = I; D.uNebula.value = opts.nebula ?? 1; RU.uFringe.value = (opts.fringe ?? 1) * (front > 500 ? 0 : 1);
    RU.uRevA.value = smooth(ub * 6);
    this._disW = ub > 0 ? clamp(opts.dissolve ?? 1) : 0;   // host dissolve (cos.dissolve) follows the shell's front
    this.dome.visible = reveal > 0.11;
    // fully revealed: the shell is drawn as an OPAQUE pass after the host's opaque objects (depth-tested, no
    // blending: ~0.03 s cheaper on SwiftShader). While revealing it is a blended pass, first among transparents.
    const solid = front > 500 && !opts.blendShell;
    this.dome.material = solid ? this.domeMatS : this.domeMatB;
    this.dome.renderOrder = solid ? 1e6 : -40;
    const F = this.floorU, fo = opts.floor || {};
    F.uIntensity.value = I; F.uNebula.value = opts.nebula ?? 1; F.uStars.value = opts.stars ?? 1;
    F.uCenter.value.set(c[0], c[1], c[2]);
    const r0 = fo.r0 ?? (standalone ? 2.2 : 1.5);
    const h = lift;   // shell centre above the floor plane
    const rInt = radius * Math.sqrt(Math.max(0, 1 - (h / height) ** 2));
    F.uR0.value = Math.min(r0, rInt * 0.6); F.uR1.value = Math.min(fo.r1 ?? (standalone ? 5.5 : 3.8), rInt * 0.97);
    F.uInner.value = fo.inner ?? (standalone ? 0 : 0.22); F.uCover.value = fo.cover ?? (standalone ? 0 : 1);
    const fIn = smooth(reveal * 2);
    F.uGlow.value = (fo.glow ?? (standalone ? 1 : 0.6)) * I * fIn;
    F.uContact.value = clamp(fo.contact ?? (standalone ? 0.3 : 0.28)) * fIn;
    F.uRc.value = fo.rc ?? 1.25;
    this.floor.position.set(c[0], c[1] + 0.004, c[2]);
    this.floor.scale.setScalar(F.uCover.value > 0 || F.uInner.value > 0 ? rInt * 1.02 : Math.min(rInt, F.uR0.value * 1.9));
    // skip the veil draw entirely when it has nothing to do
    this.floor.visible = reveal > 0.11 && (F.uCover.value > 0 || F.uInner.value > 0 || F.uGlow.value > 0 || F.uContact.value > 0);
    // island underlay: just below the floor plane (hidden by any host floor; the ground when there is none)
    const IS = this.islandU;
    const islR = Math.min(fo.islandR ?? (standalone ? 3.6 : F.uR1.value), rInt * 0.97);
    IS.uIntensity.value = I; IS.uNebula.value = opts.nebula ?? 1;
    IS.uR0.value = Math.min(F.uR0.value, islR * 0.7); IS.uR1.value = islR;
    IS.uIslA.value = clamp(fo.island ?? (standalone ? 0.6 : 1)) * fIn;
    IS.uIslRefl.value = fo.reflect ?? 1;
    this.island.position.set(c[0], c[1] - 0.012, c[2]);
    this.island.scale.setScalar(islR * 1.02);
    this.island.visible = reveal > 0.11 && IS.uIslA.value > 0;

    // stars
    const S = opts.stars ?? 1;
    this.far.mat.uniforms.uIntensity.value = I * S;
    this.mid.mat.uniforms.uIntensity.value = I * S;
    this.near.mat.uniforms.uIntensity.value = I * S;
    this.near.mat.uniforms.uKindle.value = kindle;
    this.far.pts.visible = this.mid.pts.visible = reveal > 0.11 && S > 0;
    this.near.pts.visible = reveal > 0.005 && S > 0;
    // near stars orbit the source very slowly
    this.nearGroup.rotation.set(0, clock * 0.02, 0);

    // puffs
    this.puffs.u.uIntensity.value = I * (opts.puffs ?? 1) * (opts.nebula ?? 1);
    this.puffs.begin();
    const pc = new THREE.Color();
    PUFFS.forEach((p, i) => {
      const pp = p.dir.clone().multiplyScalar(p.d);
      pc.set(p.c);
      this.puffs.add(pp, p.s, pc, p.a, i * 1.7 + clock * 0.004 * (i % 2 ? 1 : -1), p.ch, 0.0);
    });
    this.puffs.end();
    this.puffs.mesh.visible = reveal > 0.2 && (opts.puffs ?? 1) * (opts.nebula ?? 1) > 0;

    // reveal bloom (stage .14 -> .72), drawn by the sky shell itself
    const bs = clamp((reveal - 0.14) / 0.58);
    RU.uBloomR.value = lerp(0.35, 2.4, 1 - Math.pow(1 - bs, 2));
    RU.uBloomA.value = bs > 0 && bs < 1 ? 0.24 * Math.pow(Math.sin(Math.PI * bs), 1.2) * (opts.bloom ?? 1) * (opts.nebula ?? 1) : 0;

    // galaxies: spin, drift in, fade in (staggered)
    const Gm = opts.galaxies ?? 1;
    const aAxis = V3();
    for (const g of this.gals) {
      const a = smooth((galStage - g.G.delay) / 0.45);
      g.u.uAlpha.value = a * Gm;
      g.u.uIntensity.value = I;
      g.u.uSpin.value = clock * g.G.spin + g.G.pa;
      // drift in: slide ~6° along a fixed tangent and grow from 80 %
      aAxis.copy(g.dir0).cross(SKY_AXIS).normalize();
      g.u.uGDir.value.copy(g.dir0).applyAxisAngle(aAxis, (1 - a) * 0.11).normalize();
      g.u.uGSize.value = g.G.size * (0.8 + 0.2 * a);
      g.m.visible = a > 0.001 && Gm > 0;
    }

    // glyphs
    this.glyphs.u.uIntensity.value = I * (opts.glyphs ?? 1);
    this.glyphs.begin();
    if (glyphStage > 0) {
      const p = V3();
      for (const gd of this.glyphDefs) {
        const a = smooth((glyphStage - (gd.th - 0.6)) / 0.35);
        if (a <= 0) continue;
        const ang = gd.a0 + clock * gd.sp;
        p.set(Math.cos(ang) * gd.rad, gd.h + 0.12 * Math.sin(clock * 0.35 + gd.ph), Math.sin(ang) * gd.rad);
        p.applyAxisAngle(V3(0, 1, 0), -clock * 0.02);       // undo the near-group spin (glyphs have their own orbit)
        const breathe = 0.75 + 0.25 * Math.sin(t * 0.6 + gd.ph);
        this.glyphs.add(p, gd.size, gd.col, 0.85 * a * breathe, 0.25 * Math.sin(clock * 0.3 + gd.ph), gd.cell, -10);
      }
    }
    this.glyphs.end();
    this.glyphs.mesh.visible = this.glyphs.n > 0 && (opts.glyphs ?? 1) > 0;

    // lights
    const L = (opts.light ?? 1) * smooth(reveal * 1.3);
    const kd = KEY_DIR.clone().applyMatrix3(U.uSkyRot.value);
    // host: only the warm key is added (hosts tint their own ambient, e.g. BACKROOM `cosmos`) unless opts.hemi
    this.hemi.visible = standalone || !!opts.hemi;
    this.hemi.intensity = standalone ? 0.3 + 0.35 * L : 0.4 * (opts.hemi === true ? 1 : opts.hemi || 0) * L;
    this.key.intensity = (standalone ? 1.25 : 0.65) * L;
    this.key.position.set(c[0] + kd.x * 10, c[1] + kd.y * 10, c[2] + kd.z * 10);
    this.key.target.position.set(c[0], c[1] + 1, c[2]);
    // EYE_LIGHT: SET from a fixed base (standalone: the engine defaults; in a host: the values the host set earlier in
    // this same frame — call cos.update after the host's update), never accumulated across frames.
    const ew = clamp(opts.eyeLight ?? (standalone ? 1 : 0));
    if (ew > 0) {
      if (standalone) {
        EYE_LIGHT.uKeyDir.value.copy(EYE_BASE.dir); EYE_LIGHT.uKeyColor.value.copy(EYE_BASE.key); EYE_LIGHT.uAmbient.value.copy(EYE_BASE.amb);
      }
      EYE_LIGHT.uKeyDir.value.lerp(kd.clone().add(V3(0, 0, 0.8)).normalize(), ew).normalize();
      EYE_LIGHT.uKeyColor.value.lerp(EYE_KEY, ew);
      EYE_LIGHT.uAmbient.value.lerp(EYE_AMB, ew);
    }

    // anchors (world; galaxies seen from the shell centre)
    const A = this.anchors;
    A.center.set(c[0], c[1], c[2]); A.source.copy(U.uSrc.value); A.domeCenter.copy(U.uDomeC.value);
    this.gals.forEach((g, i) => {
      const dw = g.u.uGDir.value.clone().applyMatrix3(U.uSkyRot.value);
      A.galaxies[i].copy(U.uDomeC.value).addScaledVector(dw, radius * 0.9);
    });
    A.hero.copy(A.galaxies[0]);
    A.nebula.copy(U.uDomeC.value).addScaledVector(PUFFS[0].dir.clone().applyMatrix3(U.uSkyRot.value), radius * 0.8);
    A.up.copy(U.uDomeC.value).add(V3(0, height * 0.9, 0));
    return this;
  }
}

export async function create() { return new CosmosSet(); }
