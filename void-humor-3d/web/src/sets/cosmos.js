// SET 'COSMOS' (SETS.COSMOS) — the universe the Void shows Fear (bonus-scene climax). See docs/sets/cosmos.md.
//
//   const cos = await app.set('COSMOS');   // { scene, group, update(t, opts), anchors, props, look, attach(scene) }
//   standalone:   st.scene = cos.scene;                       cos.update(t, { reveal: 1 });
//   inside BACKROOM: backroom.scene.add(cos.group) (every frame, like characters: a group has ONE parent)
//                 cos.update(t, { reveal, center: [x,0,z], source: voidChest, radius: 7 });
//
// Contents (all a pure function of t + opts; deterministic seeded layout):
//   - SKY SHELL: an inside-out ellipsoid around the characters. Its colour is looked up by CAMERA ray direction (so
//     the sky sits at infinity: no parallax, no swimming) in a nebula map baked once on the GPU (equirect, half
//     float, smooth domain-warped fbm: violet / teal / rose / gold clouds + a soft galactic band). It is depth-tested
//     against the host scene, so whatever is farther than the shell (BACKROOM walls) is covered: walls "dissolve"
//     as reveal opens the sky outward from the source (the Void) with a soft glowing fringe.
//   - FLOOR VEIL: in a host room, the floor beyond r0 fades into the same sky (seamless with the shell); in
//     standalone mode a soft light pool marks where the characters stand on "glass over the universe".
//   - STARS: 3 parallax layers of point sprites — far (2600, on the shell at infinity), mid (520, world shell between
//     the characters and the sky: parallax), near (70, metres around the source: the first ones KINDLE one by one).
//     Soft gaussian cores (no sub-pixel shimmer), few bright stars with small 4-point glints, gentle per-star twinkle.
//   - NEBULA PUFFS: a few huge soft world-space billboards (parallax depth), swelling open as the reveal reaches them.
//   - 5 SPIRAL GALAXIES: procedural (baked, mipmapped) with gold bulges, blue-violet arms, rose knots, dust lanes;
//     inclined discs at infinity, each slowly spinning; they drift in during the last third of the reveal.
//   - BITS OF MEANING: tiny glowing glyphs (heart, sun, music note, house, handprint, pencil) drifting near the source.
//   - LIGHTS: a cool-violet hemisphere + a warm starlight key from the hero galaxy (intensity × reveal).
import * as THREE from 'three';
import { CTX, EYE_LIGHT } from '../core/context.js';
import { rng, clamp, lerp, smooth, noise1 } from '../core/util.js';

const TAU = Math.PI * 2;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const nrm = (x, y, z) => V3(x, y, z).normalize();
const col = (hex) => new THREE.Color(hex);

// ------------------------------------------------------------------------------------------------ layout (sky space)
// Convention: camera usually at +Z looking toward -Z at the characters, so "behind the characters" is -Z.
const SKY_AXIS = nrm(0.18, 1, 0.12);            // slow drift rotation axis of the whole sky
const SKY_RATE = 0.0045;                        // rad/s at drift 1 (about 8° per 30 s)
const KEY_DIR = nrm(0.30, 0.62, -0.72);         // hero galaxy direction = starlight key light
// galaxies: dir (sky space), angular half-size (tan), inclination (rad), position angle, spin rad/s, tint, bake variant
const GALAXIES = [
  { dir: KEY_DIR, size: 0.24, incl: 0.62, pa: 0.5, spin: 0.022, tint: 0xffffff, v: 0, delay: 0.0 },
  { dir: nrm(-0.78, 0.40, -0.50), size: 0.15, incl: 1.08, pa: -0.8, spin: -0.03, tint: 0xf4fbff, v: 1, delay: 0.12 },
  { dir: nrm(0.88, 0.16, 0.05), size: 0.13, incl: 1.28, pa: 2.2, spin: 0.028, tint: 0xfff0f4, v: 2, delay: 0.22 },
  { dir: nrm(-0.22, 0.96, 0.12), size: 0.19, incl: 0.30, pa: 1.1, spin: 0.018, tint: 0xffffff, v: 3, delay: 0.3 },
  { dir: nrm(-0.42, 0.28, 0.86), size: 0.16, incl: 0.85, pa: -2.0, spin: -0.024, tint: 0xfff8ec, v: 1, delay: 0.38 },
];
// world-space nebula puffs (mid layer, unit-dome space): dir, distance (0..1 of dome), size m, colour, alpha, channel
const PUFFS = [
  { dir: nrm(0.05, 0.42, -1), d: 0.78, s: 5.5, c: 0x8a5cff, a: 0.20, ch: 0 },
  { dir: nrm(-0.8, 0.7, -0.6), d: 0.72, s: 4.6, c: 0x2fd2c8, a: 0.17, ch: 1 },
  { dir: nrm(0.95, 0.35, -0.3), d: 0.74, s: 4.2, c: 0xff6fa8, a: 0.16, ch: 2 },
  { dir: nrm(0.3, 0.95, -0.35), d: 0.66, s: 4.8, c: 0xffc46b, a: 0.12, ch: 3 },
  { dir: nrm(-0.45, 0.9, 0.45), d: 0.7, s: 5.0, c: 0x6a7dff, a: 0.15, ch: 0 },
  { dir: nrm(-0.15, 0.45, 1), d: 0.74, s: 5.0, c: 0xff7fb0, a: 0.14, ch: 2 },
  { dir: nrm(-0.95, 0.3, 0.35), d: 0.75, s: 4.4, c: 0x34c6d0, a: 0.15, ch: 3 },
  { dir: nrm(0.75, 0.5, 0.6), d: 0.72, s: 4.4, c: 0x9a6cff, a: 0.15, ch: 1 },
];
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
uniform float uFront, uSoft;
float cosmosHalfDiag(mat4 P){ float tv = 1.0 / P[1][1]; float th = 1.0 / P[0][0]; return atan(sqrt(tv * tv + th * th)); }
float cosmosMask(vec3 rd, float hd, float jit){
  if (uFront > 500.0) return 1.0;
  vec3 sd = normalize(uSrc - cameraPosition);
  float a = acos(clamp(dot(rd, sd), -1.0, 1.0)) / hd;
  return 1.0 - smoothstep(uFront - uSoft, uFront, a + jit);
}
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
vec4 cosmosSky(sampler2D tex, vec3 d){
  vec2 uv = vec2(atan(d.z, d.x) * 0.15915494 + 0.5, asin(clamp(d.y, -1.0, 1.0)) * 0.31830989 + 0.5);
  return texture2D(tex, uv);
}
`;

const QUAD_VS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

// Nebula sky map (equirect, rgb = nebula + band light (linear HDR), a = smooth edge noise for the reveal front)
const SKY_BAKE_FS = /* glsl */`
precision highp float;
varying vec2 vUv;
${NOISE}
float env(vec3 d, vec3 c, float rad){ return exp(-(1.0 - dot(d, normalize(c))) / (rad * rad * 0.5)); }
void main(){
  float th = (vUv.x - 0.5) * 6.2831853, ph = (vUv.y - 0.5) * 3.1415927;
  vec3 d = vec3(cos(ph) * cos(th), sin(ph), cos(ph) * sin(th));
  vec3 w = vec3(fbm(d * 1.3 + vec3(1.7, 9.2, 3.1), 4), fbm(d * 1.3 + vec3(8.3, 2.8, 5.4), 4), fbm(d * 1.3 + vec3(4.1, 6.6, 0.7), 4)) - 0.5;
  vec3 q = d + w * 0.6;
  float n1 = fbm(q * 2.0 + 3.0, 5);
  float n2 = fbm(q * 2.5 + 11.0, 5);
  float n3 = fbm(q * 1.5 + 23.0, 4);
  float rid = 1.0 - abs(2.0 * fbm(q * 3.0 + 31.0, 4) - 1.0);
  vec3 dq = normalize(d + w * 0.45);
  float c1 = smoothstep(0.38, 0.78, n1), c2 = smoothstep(0.40, 0.80, n2), c3 = smoothstep(0.42, 0.75, n3);
  float fil = pow(rid, 4.0);
  vec3 VIO = vec3(0.36, 0.17, 0.95), TEAL = vec3(0.06, 0.55, 0.60), ROSE = vec3(0.95, 0.25, 0.50), GOLD = vec3(1.0, 0.62, 0.25), BLUE = vec3(0.16, 0.30, 0.95);
  vec3 c = vec3(0.0);
  // big cloud complexes (envelope x warped density + faint haze + filaments)
  float e;
  e = env(dq, vec3(0.10, 0.28, -1.0), 0.75);  c += VIO  * e * (0.10 + 0.55 * c1 + 0.25 * fil * c1);
  e = env(dq, vec3(-0.9, 0.55, -0.6), 0.62);  c += TEAL * e * (0.08 + 0.55 * c2 + 0.25 * fil);
  e = env(dq, vec3(0.95, 0.15, -0.35), 0.55); c += ROSE * e * (0.07 + 0.50 * c1 * c2 + 0.30 * c2);
  e = env(dq, vec3(0.3, 0.9, -0.45), 0.42);   c += GOLD * e * (0.06 + 0.40 * c3);
  e = env(dq, vec3(-0.3, 0.85, 0.5), 0.70);   c += BLUE * e * (0.06 + 0.40 * c2 + 0.2 * fil);
  e = env(dq, vec3(-0.2, 0.25, 1.0), 0.70);   c += ROSE * e * (0.05 + 0.40 * c3) + GOLD * e * 0.12 * c1;
  e = env(dq, vec3(-0.85, -0.1, 0.55), 0.60); c += TEAL * e * (0.05 + 0.40 * c1);
  e = env(dq, vec3(0.7, -0.05, 0.75), 0.55);  c += VIO  * e * (0.06 + 0.45 * c3);
  e = env(dq, vec3(0.2, -0.75, -0.3), 0.8);   c += VIO * e * (0.03 + 0.25 * c2) + TEAL * e * 0.12 * c1;
  // soft galactic band (tilted great circle), warm core, dust lane
  vec3 nb = normalize(vec3(0.62, 0.42, 0.66));
  float bd = dot(d, nb) + (n2 - 0.5) * 0.14 + (n1 - 0.5) * 0.06;
  float band = exp(-bd * bd / 0.020), core = exp(-bd * bd / 0.0045);
  float patchy = 0.45 + 0.9 * n3;
  vec3 bandCol = mix(vec3(0.42, 0.30, 0.70), vec3(1.0, 0.80, 0.62), core);
  float dust = smoothstep(0.45, 0.75, fbm(q * 4.0 + 51.0, 4)) * core;
  c += bandCol * band * patchy * 0.22 * (1.0 - 0.75 * dust);
  // overall gentle low-frequency breathing of brightness
  c *= 0.75 + 0.5 * fbm(d * 0.9 + 70.0, 3);
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
  float arm = pow(0.5 + 0.5 * cos(ph), 2.6);
  float armMask = smoothstep(0.06 + 0.1 * uBar, 0.24, r) * (1.0 - smoothstep(0.55, 0.95, r));
  float armI = arm * armMask * (0.5 + 0.9 * n2);
  float disk = exp(-r * 3.6) * (1.0 - smoothstep(0.6, 1.0, r));
  // bar (stretched bulge) for barred variants
  vec2 pb = vec2(p.x, p.y * mix(1.0, 3.2, uBar));
  float rb = length(pb);
  float bulge = exp(-r * r / 0.010) * 2.6 + exp(-rb * rb / 0.05) * (0.55 + 0.5 * uBar);
  float dust = pow(0.5 + 0.5 * cos(ph - 0.85), 7.0) * smoothstep(0.08, 0.3, r) * (1.0 - smoothstep(0.5, 0.9, r)) * (0.6 + 0.6 * n);
  vec3 armCol = mix(uArm, uArm2, smoothstep(0.25, 0.8, r));
  vec3 c = uCore * bulge + armCol * (armI * 0.95 + disk * 0.35);
  float knots = smoothstep(0.66, 0.84, n2) * arm * armMask;
  c += uKnot * knots * 1.1;
  // resolved stars sprinkled over arms and disk
  vec2 g = p * 46.0; vec2 gi = floor(g); vec2 gf = fract(g) - 0.5;
  vec2 off = vec2(h12(gi + uSeed * 7.0), h12(gi + uSeed * 7.0 + 19.1)) - 0.5;
  float sd = length(gf - off * 0.6);
  float st = step(0.8, h12(gi + uSeed * 3.0 + 5.0)) * exp(-sd * sd * 40.0) * (arm * armMask + disk * 0.7);
  c += vec3(0.85, 0.92, 1.0) * st * 0.9;
  c *= 1.0 - 0.6 * dust;
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
uniform sampler2D uSky; uniform mat3 uSkyRot;
uniform float uIntensity, uNebula, uFringe, uAlpha;
uniform vec3 uFringeA, uFringeB;
varying vec3 vWorld; varying float vHD;
void main(){
  vec3 rd = normalize(vWorld - cameraPosition);
  vec3 d = rd * uSkyRot;                 // world -> sky space (uSkyRot is sky -> world)
  vec4 s = cosmosSky(uSky, d);
  float m = cosmosMask(rd, vHD, (s.a - 0.5) * uSoft * 1.8) * uAlpha;
  vec3 c = (cosmosBase(d) + s.rgb * uNebula) * uIntensity;
  float fr = m * (1.0 - m) * 4.0;
  vec3 fc = mix(uFringeA, uFringeB, s.a) * fr * uFringe;
  gl_FragColor = vec4(c * m + fc, m);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// --- floor veil (sky continuation over a host floor + light pool)
const FLOOR_FS = /* glsl */`
${COMMON}
uniform sampler2D uSky; uniform mat3 uSkyRot;
uniform float uIntensity, uNebula, uR0, uR1, uInner, uCover, uGlow;
uniform vec3 uCenter, uGlowA, uGlowB;
varying vec3 vWorld; varying float vHD;
void main(){
  vec3 rd = normalize(vWorld - cameraPosition);
  vec3 d = rd * uSkyRot;
  vec4 s = cosmosSky(uSky, d);
  float m = cosmosMask(rd, vHD, (s.a - 0.5) * uSoft * 1.8);
  vec3 sky = (cosmosBase(d) + s.rgb * uNebula) * uIntensity;
  vec2 dx = vWorld.xz - uCenter.xz; float r = length(dx);
  float cov = mix(uInner, 1.0, smoothstep(uR0, uR1, r)) * uCover * m;
  float pool = exp(-r * r / (uR0 * uR0 * 0.35)) * 0.8 + exp(-r * r / (uR0 * uR0 * 1.6)) * 0.35;
  float ring = exp(-pow((r - uR0 * 0.95) / (uR0 * 0.18), 2.0)) * 0.25;
  vec3 g = mix(uGlowA, uGlowB, clamp(r / uR0, 0.0, 1.0)) * (pool + ring) * uGlow * m;
  gl_FragColor = vec4(sky * cov + g, cov);
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
    flare = k > 0.0 ? exp(-k / 0.05) : 0.0;
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
  float m = iMisc.w < -5.0 ? 1.0 : cosmosMask(normalize(wc.xyz - cameraPosition), cosmosHalfDiag(projectionMatrix), iMisc.w);
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
    this.skyTex = bake(renderer, SKY_BAKE_FS, 2048, 1024, {}, { wrapS: THREE.RepeatWrapping });
    this.puffTex = bake(renderer, PUFF_BAKE_FS, 256, 256, {}, { mip: true });
    const GV = [   // galaxy bake variants
      { uArms: 2, uPitch: 0.36, uSeed: 1.3, uBar: 0.0, uTwist: 0.0, uCore: 0xffd9a0, uArm: 0xb4c6ff, uArm2: 0x8a7cff, uKnot: 0xff7fb4 },
      { uArms: 2, uPitch: 0.30, uSeed: 4.7, uBar: 0.65, uTwist: 1.0, uCore: 0xffe2b0, uArm: 0x9ff0f0, uArm2: 0x5aa8ff, uKnot: 0xffa0c8 },
      { uArms: 3, uPitch: 0.42, uSeed: 7.9, uBar: 0.0, uTwist: 2.0, uCore: 0xffd0b0, uArm: 0xd6b4ff, uArm2: 0xff8fc0, uKnot: 0xffd27a },
      { uArms: 2, uPitch: 0.26, uSeed: 9.4, uBar: 0.2, uTwist: 0.5, uCore: 0xfff0c8, uArm: 0xc8d4ff, uArm2: 0xb48cff, uKnot: 0x7fe8e0 },
    ];
    this.galTex = GV.map((o) => {
      const u = {};
      for (const k in o) u[k] = { value: typeof o[k] === 'number' && k.startsWith('uC') || k === 'uArm' || k === 'uArm2' || k === 'uKnot' ? col(o[k]) : o[k] };
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
      uFront: { value: 1e3 }, uSoft: { value: 0.3 },
      uSkyRot: { value: new THREE.Matrix3() }, uTime: { value: 0 },
    };
    const U = this.U;

    // sky shell
    this.domeU = { ...U, uSky: { value: this.skyTex }, uIntensity: { value: 1 }, uNebula: { value: 1 }, uFringe: { value: 1 },
      uAlpha: { value: 1 }, uFringeA: { value: col(0x7a5cff).multiplyScalar(0.6) }, uFringeB: { value: col(0x3fe0d0).multiplyScalar(0.5) } };
    this.dome = new THREE.Mesh(new THREE.SphereGeometry(1, 64, 40), new THREE.ShaderMaterial({
      uniforms: this.domeU, vertexShader: DOME_VS, fragmentShader: DOME_FS, side: THREE.BackSide, transparent: true,
      depthWrite: false, blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
      blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor,
    }));
    this.dome.frustumCulled = false; this.dome.renderOrder = -40;
    this.group.add(this.dome);

    // floor veil
    this.floorU = { ...U, uSky: { value: this.skyTex }, uIntensity: { value: 1 }, uNebula: { value: 1 }, uR0: { value: 2.2 },
      uR1: { value: 5.5 }, uInner: { value: 0 }, uCover: { value: 1 }, uGlow: { value: 0.5 }, uCenter: { value: V3() },
      uGlowA: { value: col(0x8f7cff).multiplyScalar(0.55) }, uGlowB: { value: col(0x35c8d8).multiplyScalar(0.35) } };
    const fg = new THREE.CircleGeometry(1, 96); fg.rotateX(-Math.PI / 2);
    this.floor = new THREE.Mesh(fg, new THREE.ShaderMaterial({
      uniforms: this.floorU, vertexShader: DOME_VS, fragmentShader: FLOOR_FS, transparent: true, depthWrite: false,
      blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
      blendSrcAlpha: THREE.OneFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
    }));
    this.floor.frustumCulled = false; this.floor.renderOrder = -35;
    this.group.add(this.floor);

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
      cell: i % 6, col: col(GLYPH_COLS[i % 6]), a0: r() * TAU, rad: 1.3 + r() * 1.5, h: -0.6 + r() * 2.2, sp: (0.035 + r() * 0.03) * (r() < 0.5 ? -1 : 1),
      size: 0.11 + r() * 0.06, ph: r() * TAU, th: 0.62 + 0.3 * (i / 9),
    }));

    // lights (intensity follows reveal)
    this.hemi = new THREE.HemisphereLight(0x9a8cff, 0x1d5c6c, 0); this.group.add(this.hemi);
    this.key = new THREE.DirectionalLight(0xfff0dc, 0); this.group.add(this.key); this.group.add(this.key.target);
    // standalone-only lights (cool rim from behind + soft front fill so faces read)
    this.rim = new THREE.DirectionalLight(0x6fe0ff, 1.2); this.rim.position.set(-3, 4, -6); this.scene.add(this.rim);
    this.fill = new THREE.DirectionalLight(0xc8b8ff, 0.55); this.fill.position.set(2, 2.5, 6); this.scene.add(this.fill);
    this.sceneHemi = new THREE.HemisphereLight(0x7a70d0, 0x203048, 0.35); this.scene.add(this.sceneHemi);

    this.look = { bloom: 0.7, bloomRadius: 0.62, bloomThreshold: 0.72, vignette: 0.3, sat: 1.08, warm: 0.0,
      lift: [0.004, 0.003, 0.012], exposure: 1.05 };
    this.anchors = { center: V3(), source: V3(), domeCenter: V3(), hero: V3(), galaxies: GALAXIES.map(() => V3()), nebula: V3(), up: V3() };
    this.props = { dome: this.dome, floor: this.floor, far: this.far.pts, mid: this.mid.pts, near: this.near.pts, puffs: this.puffs.mesh,
      galaxies: this.gals.map((g) => g.m), glyphs: this.glyphs.mesh, hemi: this.hemi, key: this.key, skyTex: this.skyTex };
    this._q = new THREE.Quaternion(); this._m4 = new THREE.Matrix4();
    this.update(0, {});
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
    const nb = nrm(0.62, 0.42, 0.66), c = new THREE.Color(), d = V3();
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
      misc.set([0.022 + 0.026 * L, r(), 0.14 + 0.12 * r(), kind ? 0.02 + 0.27 * (i / NK) + 0.02 * r() : -1], i * 4);
    }
    return { pos, col: cl, misc };
  }

  /** Attach the cosmos group to a host scene (call every frame in a scene's update; idempotent). */
  attach(scene) { if (this.group.parent !== scene) scene.add(this.group); return this; }

  /**
   * update(t, opts) — pure function of (t, opts).
   *  reveal 0..1        0 = nothing; .02–.3 near stars kindle around `source`; .12–.9 sky blooms outward from the source
   *                     (walls dissolve behind a soft glowing fringe), nebula puffs swell open; .5–1 galaxies drift in;
   *                     .62–1 glyphs. 1 = everything (cheap: no masking).
   *  center [x,y,z]     floor point the cosmos surrounds (the characters' spot). Default [0,0,0].
   *  source [x,y,z]     where the reveal starts (the Void's chest). Default center + [0,1.6,0].
   *  radius (m)         horizontal radius of the sky shell (default 7.5). Must be < distance to the host walls.
   *  height (m)         vertical semi-axis of the shell (default 0.87·radius). Shell centre = center + [0, lift, 0].
   *  lift (m)           shell centre height above `center` (default 1.5).
   *  drift              speed multiplier for all slow motion (sky rotation, galaxy spin, glyph orbits). Default 1.
   *  clock              explicit motion clock (s) instead of t·drift (use when animating drift).
   *  intensity          global brightness multiplier (default 1).
   *  stars, nebula, galaxies, glyphs, puffs   per-element brightness multipliers (default 1).
   *  fringe             reveal-front glow (default 1).
   *  light              multiplier for the cosmic hemi + key lights (default 1; 0 = no light added to the host).
   *  floor { cover, inner, r0, r1, glow }    cover: sky over the host floor beyond r0..r1 (default 1 in a host, 0 standalone);
   *                     inner: sky tint inside r0; glow: light pool under the characters (default .35 host / 1 standalone).
   *  eyeLight 0..1      blend EYE_LIGHT toward the cosmos key (default 1 standalone, 0 in a host).
   */
  update(t, opts = {}) {
    const standalone = this.group.parent === this.scene;
    const reveal = clamp(opts.reveal ?? 1);
    const c = opts.center || [0, 0, 0];
    const radius = opts.radius ?? 7.5, height = opts.height ?? radius * 0.87, lift = opts.lift ?? 1.5;
    const src = opts.source || [c[0], c[1] + 1.6, c[2]];
    const clock = opts.clock ?? t * (opts.drift ?? 1);
    const I = opts.intensity ?? 1;
    const U = this.U;
    U.uTime.value = t;
    U.uSrc.value.set(src[0], src[1], src[2]);
    U.uDomeC.value.set(c[0], c[1] + lift, c[2]);
    U.uDomeR.value.set(radius, height, radius);
    this.dome.position.copy(U.uDomeC.value); this.dome.scale.copy(U.uDomeR.value);
    this.midGroup.position.copy(U.uDomeC.value); this.midGroup.scale.copy(U.uDomeR.value);
    this.nearGroup.position.set(src[0], src[1], src[2]);

    // sky rotation (sky -> world)
    this._q.setFromAxisAngle(SKY_AXIS, clock * SKY_RATE);
    U.uSkyRot.value.setFromMatrix4(this._m4.makeRotationFromQuaternion(this._q));
    this.midGroup.quaternion.setFromAxisAngle(SKY_AXIS, clock * SKY_RATE * 0.7);

    // reveal stages
    const kindle = clamp(reveal / 0.3);
    const ub = clamp((reveal - 0.12) / 0.78);
    const front = ub >= 0.999 || reveal >= 0.999 ? 1e3 : 0.55 * ub / (1 - ub);
    U.uFront.value = front;
    U.uSoft.value = 0.22 + 0.22 * Math.min(front, 3);
    const galStage = clamp((reveal - 0.5) / 0.5);
    const glyphStage = clamp((reveal - 0.6) / 0.4);

    // shell + floor
    const D = this.domeU;
    D.uIntensity.value = I; D.uNebula.value = opts.nebula ?? 1; D.uFringe.value = (opts.fringe ?? 1) * (front > 500 ? 0 : 1);
    D.uAlpha.value = smooth(ub * 6);
    this.dome.visible = reveal > 0.11;
    const F = this.floorU, fo = opts.floor || {};
    F.uIntensity.value = I; F.uNebula.value = opts.nebula ?? 1;
    F.uCenter.value.set(c[0], c[1], c[2]);
    const r0 = fo.r0 ?? 2.2;
    const h = lift;   // shell centre above the floor plane
    const rInt = radius * Math.sqrt(Math.max(0, 1 - (h / height) ** 2));
    F.uR0.value = Math.min(r0, rInt * 0.6); F.uR1.value = Math.min(fo.r1 ?? 5.5, rInt * 0.97);
    F.uInner.value = fo.inner ?? 0; F.uCover.value = fo.cover ?? (standalone ? 0 : 1);
    F.uGlow.value = (fo.glow ?? (standalone ? 1 : 0.35)) * I * smooth(reveal * 2);
    this.floor.position.set(c[0], c[1] + 0.004, c[2]); this.floor.scale.setScalar(rInt * 1.02);
    this.floor.visible = reveal > 0.11;

    // stars
    const S = opts.stars ?? 1;
    this.far.mat.uniforms.uIntensity.value = I * S;
    this.mid.mat.uniforms.uIntensity.value = I * S;
    this.near.mat.uniforms.uIntensity.value = I * S;
    this.near.mat.uniforms.uKindle.value = kindle;
    this.far.pts.visible = reveal > 0.11; this.mid.pts.visible = reveal > 0.11;
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
    this.puffs.mesh.visible = reveal > 0.11;

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
      g.m.visible = a > 0.001;
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

    // lights
    const L = (opts.light ?? 1) * smooth(reveal * 1.3);
    const kd = KEY_DIR.clone().applyMatrix3(U.uSkyRot.value);
    this.hemi.intensity = 0.55 * L;
    this.key.intensity = 1.25 * L;
    this.key.position.set(c[0] + kd.x * 10, c[1] + kd.y * 10, c[2] + kd.z * 10);
    this.key.target.position.set(c[0], c[1] + 1, c[2]);
    this.rim.visible = this.fill.visible = this.sceneHemi.visible = true;
    const ew = opts.eyeLight ?? (standalone ? 1 : 0);
    if (ew > 0) {
      EYE_LIGHT.uKeyDir.value.lerp(kd.clone().add(V3(0, 0, 0.8)).normalize(), ew).normalize();
      EYE_LIGHT.uKeyColor.value.lerp(col(0xf2eaff), ew);
      EYE_LIGHT.uAmbient.value.lerp(col(0x5a5a8a), ew);
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
