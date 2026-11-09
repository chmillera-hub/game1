// SET 'EDGE' — "The Edge of the Mind" (Part One). An original luminous dreamscape at golden dusk.
//
//   const set = await app.set('EDGE');      // { scene, update(t, opts), anchors, props, look, groundAt, pathAt, shots }
//   set.update(t, { tod: 0..1, voidSky: 0..1, voidPos: [x,y,z], seeds: 1 });
//
// Layout (metres, Y up; the low sun is ~8° left of world -Z). Compatible with scenes/marks.js (EDGE.*_WORLD):
//   - a flat soft-grass stage (y = 0 exactly for r < 5.2 m) where the characters act,
//   - a pale winding PATH that comes from the far north-east hills (where the Void came from), runs over the peach
//     crest (≈ (7.4, 1.26, 10.3)), THROUGH the stage (anchors.pathStart ≈ origin), over the gentle rise
//     (≈ (-0.8, 0.49, -11)) beside the lilac hillock (top ≈ (-3.6, 2.6, -10)), climbs the long crest (~41 m:
//     anchors.pathFar) and converges into the gap in the far ridge right under the sun,
//   - a sky dome (gold -> peach -> lilac -> indigo zenith, belt-of-Venus pink on the anti-sun side), a huge soft
//     sun glow, backlit billboard clouds, a few early stars, and an optional Void "cosmic bleed",
//   - glowing puff-trees, a few glassy "soft crystal" trees (the rose-gold one beside the bend at (2, 0, -5.2)),
//     round luminous bushes, tiny glowing flowers, drifting dandelion-like thought seeds, faint golden motes.
// Everything is a pure function of (t, opts). No Math.random / Date.
import * as THREE from 'three';
import { mergeGeometries, mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { EYE_LIGHT } from '../core/context.js';
import { GLOBAL, enhance, glowTexture } from '../core/materials.js';
import { Particles, CELL } from '../core/particles.js';
import { rng, hash1, hash2, noise1, clamp, lerp, smooth, smoothstep, DEG } from '../core/util.js';

const TAU = Math.PI * 2;
export const SUN_AZ = -0.14;              // sun azimuth (rad). 0 = toward -Z, + = toward +X
const SKY_R = 372, TERRAIN_R = 332;
const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const col = (hex) => new THREE.Color(hex);                        // sRGB hex -> linear working colour
const lerpC = (a, b, u, out = new THREE.Color()) => out.copy(a).lerp(b, u);
const dirAzEl = (az, el) => V3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));

// ------------------------------------------------------------------------------------------- 2D value noise
function vn2(x, y, seed) {
  const ix = Math.floor(x), iy = Math.floor(y);
  let fx = x - ix, fy = y - iy;
  fx = fx * fx * fx * (fx * (fx * 6 - 15) + 10); fy = fy * fy * fy * (fy * (fy * 6 - 15) + 10);
  const s = seed * 1013;
  const a = hash2(ix + s, iy), b = hash2(ix + 1 + s, iy), c = hash2(ix + s, iy + 1), d = hash2(ix + 1 + s, iy + 1);
  return lerp(lerp(a, b, fx), lerp(c, d, fx), fy) * 2 - 1;
}
function fbm2(x, y, seed, oct = 3) {
  let s = 0, a = 0.5, n = 0, f = 1;
  for (let o = 0; o < oct; o++) { s += a * vn2(x * f + o * 17.3, y * f - o * 9.1, seed + o * 31); n += a; a *= 0.5; f *= 2.03; }
  return s / n;
}
const angDiff = (a, b) => { let d = a - b; while (d > Math.PI) d -= TAU; while (d < -Math.PI) d += TAU; return d; };

// ------------------------------------------------------------------------------------------- the path
// control points (x, z), upstream -> downstream. Upstream it comes from the far north-east hills (where the Void came
// from) over the peach crest, runs THROUGH the stage (matches scenes/marks.js EDGE.PATH_WORLD from (14,18) to (0,-50)),
// crests the gentle rise, climbs the long crest (~46 m: anchors.pathFar) and converges into the gap under the sun.
const PATH_CTRL = [[168, 248], [118, 176], [80, 118], [52, 76], [36, 51], [25.5, 34.5], [19.2, 25.5],
  [14, 18], [8.8, 11.6], [4.2, 6.1], [1.6, 2.8], [0.3, 1.5], [-0.3, -1.9], [-0.6, -3.3], [-0.5, -6.6], [-0.6, -11.7],
  [-1.5, -18], [-2.5, -26], [-1.0, -36], [0.0, -50], [-1.4, -64], [-3.6, -82], [-7.5, -106], [-12.5, -136],
  [-19.0, -172], [-27.0, -215], [-35.0, -255], [-42.0, -298], [-46.0, -322]];
const PATH = (() => {
  const curve = new THREE.CatmullRomCurve3(PATH_CTRL.map(([x, z]) => V3(x, 0, z)), false, 'centripetal');
  const N = 1700;
  const pts = curve.getSpacedPoints(N);
  const len = curve.getLength();
  const X = new Float32Array(N + 1), Z = new Float32Array(N + 1);
  pts.forEach((p, i) => { X[i] = p.x; Z[i] = p.z; });
  return { X, Z, N, len, step: len / N };
})();
// distance (XZ) from a point to the path polyline + index of the closest sample
function pathDist(x, z) {
  const { X, Z, N } = PATH;
  let best = 1e18, bi = 0;
  for (let i = 0; i <= N; i += 12) { const dx = X[i] - x, dz = Z[i] - z, d = dx * dx + dz * dz; if (d < best) { best = d; bi = i; } }
  const i0 = Math.max(0, bi - 16), i1 = Math.min(N, bi + 16);
  for (let i = i0; i <= i1; i++) { const dx = X[i] - x, dz = Z[i] - z, d = dx * dx + dz * dz; if (d < best) { best = d; bi = i; } }
  return [Math.sqrt(best), bi];
}

// ------------------------------------------------------------------------------------------- terrain height
// Exactly 0 on the stage (r < 5.2 m). Hand-placed staging hills (FEATURES), rolling pastel hills beyond, a long
// crest the path climbs (~46 m), far ridges with a gap under the sun. Large wavelengths only (no high-frequency bumps).
// FEATURES: [x, z, radius, height, hue] — smooth domes; these match scenes/marks.js (EDGE.*_WORLD).
export const FEATURES = [
  [10.5, 14.5, 11.5, 1.75, 'peach'],   // peach crest the path runs over (s01: the Void plods over it) ≈ CREST_WORLD
  [-4.8, -10.6, 4.4, 2.75, 'lilac'],   // lilac hillock right beside the path (s16b07: the user sits on top) ≈ HILL_WORLD
  [-0.8, -13.0, 6.5, 0.6, 'mint'],     // gentle rise the path crests (s14: the user vanishes over it) ≈ RISE_WORLD
];
// polynomial smooth max: no crease where two domes meet (a hard max() leaves a V-valley the mesh cannot follow)
// (k shrinks to 0 as either dome fades out at its rim, so the blend stays continuous at every dome's edge)
const smax = (a, b, k) => { k = Math.min(k, 1.5 * Math.min(a, b)); if (k < 1e-5) return Math.max(a, b); const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.max(a, b) + h * h * k * 0.25; };
function featureH(x, z) {
  let h = 0;
  for (const [cx, cz, R, H] of FEATURES) {
    const d2 = ((x - cx) * (x - cx) + (z - cz) * (z - cz)) / (R * R);
    if (d2 < 1) h = h > 0 ? smax(h, H * smooth(1 - d2), 0.5) : H * smooth(1 - d2);
  }
  return h;
}
function heightRaw(x, z, dp) {
  const r = Math.hypot(x, z);
  if (r < 5.2) return 0;
  const fh = featureH(x, z) * smoothstep(5.2, 6.6, r);
  if (r < 7.5) return fh;
  const m = smoothstep(7.5, 26, r);
  const az = Math.atan2(x, -z);
  const sunSec = Math.exp(-Math.pow(angDiff(az, SUN_AZ) / 0.55, 2));        // the sector the path runs through
  let h = 3.0 * fbm2(x / 36, z / 36, 3) + 1.1 * fbm2(x / 16 + 7.3, z / 16 - 2.1, 7) * smoothstep(14, 40, r);
  h *= lerp(0.9, 2.6, smoothstep(25, 150, r));
  h += 1.6 * smoothstep(9, 42, r);                                           // a soft bowl around the clearing
  h += sunSec * (2.4 * Math.exp(-Math.pow((r - 47) / 13, 2)) - 2.2 * Math.exp(-Math.pow((r - 84) / 20, 2)));
  // far ridges framing a low gap under the sun
  const far = smoothstep(100, 235, r);
  const ridge = 13 + 8 * noise1(az * 2.1 + 3.1, 5) + 5 * noise1(az * 4.7 + 1.0, 9);
  const gap = Math.exp(-Math.pow(angDiff(az, SUN_AZ) / 0.24, 2));
  h += far * ridge * (1 - 0.85 * gap);
  // a gentle valley along the path (keeps it walkable and visible)
  const vw = 3.2 + r * 0.07;
  h *= 1 - 0.55 * Math.exp(-(dp * dp) / (vw * vw)) * smoothstep(8, 30, r);
  return m * h + fh;
}
export function groundAt(x, z) { const r = Math.hypot(x, z); if (r < 5.2) return 0; return heightRaw(x, z, r < 7.5 ? 99 : pathDist(x, z)[0]); }

// ------------------------------------------------------------------------------------------- terrain tessellation
// Polar mesh: ring radii RADII (0.5 m steps over the staging hills, coarser outward), TNA vertices per ring, odd rings
// rotated half a step. meshHeightAt(x, z) = the exact height of the rendered (linearly interpolated) terrain mesh.
const TERRAIN_NA = 144;
const RADII = (() => { const a = [0]; let r = 0; while (r < TERRAIN_R) { r += (r > 4.5 && r < 22) ? 0.5 : Math.max(0.6, r * 0.048); a.push(Math.min(r, TERRAIN_R)); } return a; })();
const ringAng = (j, a) => (a / TERRAIN_NA) * TAU + (j % 2) * (Math.PI / TERRAIN_NA);
// the two triangles of quad (j, a) between ring j and j+1, as [[j, a], ...] vertex refs (ring 0 = the centre point)
function quadTris(j, a) {
  const a1 = a + 1;
  if (j === 0) return [[[0, 0], [1, a1], [1, a]]];
  return j % 2 === 0
    ? [[[j, a], [j, a1], [j + 1, a]], [[j, a1], [j + 1, a1], [j + 1, a]]]
    : [[[j, a], [j, a1], [j + 1, a1]], [[j, a], [j + 1, a1], [j + 1, a]]];
}
const ringXZ = (j, a) => { if (j === 0) return [0, 0]; const th = ringAng(j, a), r = RADII[j]; return [Math.sin(th) * r, -Math.cos(th) * r]; };
const vertH = (j, a) => { const [x, z] = ringXZ(j, a); return heightRaw(x, z, Math.hypot(x, z) < 7.5 ? 99 : pathDist(x, z)[0]); };
export function meshHeightAt(x, z) {
  const r = Math.hypot(x, z);
  if (r < 5.2) return 0;
  let j = 0; { let lo = 0, hi = RADII.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (RADII[m] <= r) lo = m; else hi = m; } j = lo; }
  if (j >= RADII.length - 1) return groundAt(x, z);
  const th = ((Math.atan2(x, -z) % TAU) + TAU) % TAU;
  const ai = Math.floor(th / TAU * TERRAIN_NA);
  for (let da = -1; da <= 1; da++) for (const tri of quadTris(j, ai + da)) {
    const P = tri.map(([jj, aa]) => ringXZ(jj, aa));
    const [[x0, z0], [x1, z1], [x2, z2]] = P;
    const det = (z1 - z2) * (x0 - x2) + (x2 - x1) * (z0 - z2);
    if (Math.abs(det) < 1e-12) continue;
    const l0 = ((z1 - z2) * (x - x2) + (x2 - x1) * (z - z2)) / det, l1 = ((z2 - z0) * (x - x2) + (x0 - x2) * (z - z2)) / det, l2 = 1 - l0 - l1;
    if (l0 >= -1e-6 && l1 >= -1e-6 && l2 >= -1e-6) return l0 * vertH(...tri[0]) + l1 * vertH(...tri[1]) + l2 * vertH(...tri[2]);
  }
  return groundAt(x, z);
}
// height of the path ribbon's surface above a point near the path (it rides a little above the rendered terrain mesh)
const pathLift = (r) => 0.012 + 0.008 * smoothstep(5.3, 7.5, r) + r * 0.00025;
export function pathSurfaceAt(x, z) { const r = Math.hypot(x, z); return Math.max(groundAt(x, z), meshHeightAt(x, z)) + pathLift(r); }

// path query: s = metres along the path measured from anchors.pathStart (negative = back toward the camera side)
// S0 (index-space offset of pathStart = the path sample closest to the origin) is computed at module load, so the
// named export pathAt() works before create().
const S0 = (() => { let best = 1e9, bi = 0; for (let i = 0; i <= PATH.N; i++) { const d = Math.hypot(PATH.X[i], PATH.Z[i]); if (d < best) { best = d; bi = i; } } return bi; })();
function pathAtIndex(fi) {
  const { X, Z, N } = PATH;
  fi = clamp(fi, 0, N);
  const i = Math.min(N - 1, Math.floor(fi)), u = fi - i;
  const x = lerp(X[i], X[i + 1], u), z = lerp(Z[i], Z[i + 1], u);
  const dx = X[i + 1] - X[i], dz = Z[i + 1] - Z[i], l = Math.hypot(dx, dz) || 1;
  return { pos: [x, groundAt(x, z), z], dir: [dx / l, 0, dz / l], yaw: Math.atan2(dx, dz), surface: pathSurfaceAt(x, z) };
}
/** s metres along the path from pathStart -> { pos: [x, groundAt, z], dir, yaw, surface: y of the path ribbon there }. */
export function pathAt(s) { return pathAtIndex(S0 + s / PATH.step); }

// ------------------------------------------------------------------------------------------- shared uniforms + GLSL
const U = {
  uETime: GLOBAL.uTime,
  uESunDir: { value: dirAzEl(SUN_AZ, 6 * DEG) },
  uESunCol: { value: col(0xffc27a) },
  uEHorS: { value: new THREE.Color() }, uEHorA: { value: new THREE.Color() },
  uELowS: { value: new THREE.Color() }, uELowA: { value: new THREE.Color() },
  uEMid: { value: new THREE.Color() }, uEHigh: { value: new THREE.Color() }, uEZen: { value: new THREE.Color() },
  uEBelt: { value: new THREE.Color() }, uEShadow: { value: new THREE.Color() },
  uEGlow: { value: 1 },
  uEHazeDen: { value: 0.0042 }, uEHazeMax: { value: 0.96 },
  uEVoid: { value: 0 }, uEVoidCos: { value: Math.cos(34 * DEG) }, uEVoidUp: { value: 0.1 },
  uEVoidPos: { value: V3(0, 2.0, 0) },
  uEKeyDir: { value: V3(0, 1, 0) },
  uEGTint: { value: V3(1, 1, 1) }, uEGSat: { value: 1.12 },          // ground grade (keeps the grass clear pastel at every tod)
  uEGDusk: { value: 0 },                                             // backlit ground -> dusky rose-lilac (never olive)
};
const SKY_PARS = /* glsl */`
uniform vec3 uEKeyDir, uESunDir, uESunCol, uEHorS, uEHorA, uELowS, uELowA, uEMid, uEHigh, uEZen, uEBelt, uEShadow, uEVoidPos;
uniform float uEGlow, uEHazeDen, uEHazeMax, uEVoid, uEVoidCos, uEVoidUp, uETime;
float eHash(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float eNoise(vec3 x){ vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(eHash(i), eHash(i + vec3(1,0,0)), f.x), mix(eHash(i + vec3(0,1,0)), eHash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(eHash(i + vec3(0,0,1)), eHash(i + vec3(1,0,1)), f.x), mix(eHash(i + vec3(0,1,1)), eHash(i + vec3(1,1,1)), f.x), f.y), f.z); }
// sky gradient + broad sun glows (no disc / stars / void): shared by the sky, the clouds and the haze
vec3 eSkyGrad(vec3 d){
  float h = d.y, hp = max(h, 0.0);
  vec2 dh = normalize(d.xz + vec2(1e-6, 0.0));
  vec2 sh = normalize(uESunDir.xz);
  float ca = dot(dh, sh);
  float ws = pow(0.5 + 0.5 * ca, 1.6);
  vec3 c = mix(mix(uEHorA, uEHorS, ws), mix(uELowA, uELowS, ws), smoothstep(0.0, 0.10, hp));
  c = mix(c, uEMid, smoothstep(0.07, 0.32, hp));
  c = mix(c, uEHigh, smoothstep(0.26, 0.62, hp));
  c = mix(c, uEZen, smoothstep(0.55, 1.0, hp));
  float wa = pow(0.5 - 0.5 * ca, 2.0);
  c += uEBelt * wa * exp(-pow((hp - 0.11) / 0.075, 2.0));                // belt of Venus: low pink band, anti-sun side
  c = mix(c, uEShadow, wa * 0.6 * exp(-pow(hp / 0.06, 2.0)));
  float dAz2 = 2.0 * (1.0 - ca);                         // ≈ azimuth difference² (no acos: cheaper on SwiftShader)
  float dEl = h - uESunDir.y;
  float broad = exp(-(dAz2 / 0.5 + dEl * dEl / 0.018));
  float mid = exp(-2.0 * (1.0 - dot(d, uESunDir)) / 0.03);
  c += uESunCol * uEGlow * (0.26 * broad + 0.3 * mid);
  return c;
}
vec3 eHaze(vec3 d){ return eSkyGrad(normalize(vec3(d.x, 0.022, d.z))); }
// the Void's cosmic bleed: a soft region of sky around (and above) the Void, as seen from the camera
float eVoidMask(vec3 d){
  if (uEVoid <= 0.001) return 0.0;
  vec3 vd = normalize(normalize(uEVoidPos - cameraPosition) + vec3(0.0, uEVoidUp, 0.0));
  // keep the patch centre inside the frame: when the Void is in front of the camera, its centre may sit at most ~9°
  // above the view axis (eye-level mediums otherwise only show the patch's lower rim)
  vec3 cf = -vec3(viewMatrix[0][2], viewMatrix[1][2], viewMatrix[2][2]);
  float front = smoothstep(0.2, 0.6, dot(normalize(vd.xz + 1e-5), normalize(cf.xz + 1e-5)));
  float yMax = sin(clamp(asin(clamp(cf.y, -1.0, 1.0)) + 0.16, -0.2, 1.2));
  if (vd.y > yMax && front > 0.0) { vec3 vc = vd; vc.y = mix(vd.y, yMax, front); vc.xz = normalize(vd.xz + 1e-5) * sqrt(max(1.0 - vc.y * vc.y, 0.0)); vd = vc; }
  float n = eNoise(d * 3.5 + vec3(0.0, uETime * 0.03, uETime * 0.02));
  float e = dot(d, vd) + (n - 0.5) * 0.14;
  float m = smoothstep(uEVoidCos - 0.13, min(uEVoidCos + 0.12, 0.995), e);
  return m * uEVoid * smoothstep(-0.03, 0.12, d.y);
}
`;

/**
 * edgify(material, opts): inject the set's atmospheric haze (+ optional grass forward-scatter / sheen, flower sway)
 * into a built-in material (Lambert / Standard / Physical / Basic), chaining an existing core `enhance()` hook.
 */
function edgify(mat, { grass = false, sway = false, scatter = 0, sheen = 0, haze = 1, self = 0, form = 0, grade = false } = {}) {
  const prev = mat.onBeforeCompile;
  const enhanced = !!mat.userData.uniforms;
  const L = { uEScatter: { value: scatter }, uESheen: { value: sheen }, uEHazeMul: { value: haze }, uESelf: { value: self }, uEForm: { value: form } };
  mat.userData.edge = L;
  mat.onBeforeCompile = (sh, r) => {
    if (enhanced) prev.call(mat, sh, r);
    Object.assign(sh.uniforms, U, L);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vEW;\nvarying vec4 vEHz;\nuniform float uEHazeMul;\n' + SKY_PARS)
      .replace('#include <begin_vertex>', sway ? `#include <begin_vertex>
        {
          float eph = 0.0;
        #ifdef USE_INSTANCING
          eph = instanceMatrix[3].x * 1.7 + instanceMatrix[3].z * 1.3;
        #endif
          float ek = max(position.y, 0.0) / 0.16;
          transformed.x += sin(uETime * 1.1 + eph) * 0.012 * ek;
          transformed.z += sin(uETime * 0.83 + eph * 1.3) * 0.008 * ek;
        }` : '#include <begin_vertex>')
      .replace('#include <project_vertex>', `#include <project_vertex>
        {
          vec4 ewp = vec4(transformed, 1.0);
        #ifdef USE_INSTANCING
          ewp = instanceMatrix * ewp;
        #endif
          vEW = (modelMatrix * ewp).xyz;
          // atmospheric haze, evaluated per vertex (smooth at every scale; saves a sky evaluation per pixel)
          vec3 edv = vEW - cameraPosition; float edist = length(edv); vec3 ed = edv / max(edist, 1e-3);
          float eden = uEHazeDen * (0.55 + 0.45 * exp(-max(vEW.y, 0.0) * 0.04));
          float ehz = 1.0 - exp(-pow(edist * eden, 1.3));
          vEHz = vec4(eHaze(ed), clamp(ehz * uEHazeMax * uEHazeMul, 0.0, 1.0));
        }`);
    let fs = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vEW;\nvarying vec4 vEHz;\nuniform float uEScatter, uESheen, uESelf, uEForm, uEGSat, uEGDusk;\nuniform vec3 uEKeyDir, uESunDir, uESunCol, uEGTint;\n')
      .replace('#include <fog_fragment>', `{
          ${grass ? `{ // hill form: slopes turned toward the (back) sun key brighten, slopes facing away darken (beyond the clearing)
            vec3 enW = normalize((vec4(normal, 0.0) * viewMatrix).xyz);
            float ef = clamp(1.0 + 0.75 * (dot(enW, uEKeyDir) - uEKeyDir.y), 0.86, 1.15);   // backlit slopes never go muddy
            gl_FragColor.rgb *= mix(1.0, ef, uEForm);       // neutral (1.0) on flat ground, so it can apply everywhere
          }` : ''}
          ${grade ? `{ // ground grade: tod tint (no olive under the red sunset key) + saturation back toward clear pastel
            vec3 eg = gl_FragColor.rgb * uEGTint; float egl = dot(eg, vec3(0.2126, 0.7152, 0.0722));
            eg = mix(eg, egl * vec3(1.42, 0.68, 1.6), uEGDusk);     // dusky rose-lilac, not grey
            gl_FragColor.rgb = max(mix(vec3(egl), eg, uEGSat), 0.0);
          }` : ''}
          gl_FragColor.rgb = mix(gl_FragColor.rgb, vEHz.rgb, vEHz.a);
        }`);
    if (grass) fs = fs.replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        {
          vec3 ev = normalize(vEW - cameraPosition);
          float efs = pow(max(dot(ev, uESunDir), 0.0), 5.0);
          float efr = 1.0 - clamp(abs(dot(normalize(normal), normalize(vViewPosition))), 0.0, 1.0);
          totalEmissiveRadiance += uESunCol * diffuseColor.rgb * (uEScatter * efs * (0.35 + 0.65 * efr));
          totalEmissiveRadiance += diffuseColor.rgb * mix(vec3(1.0), uESunCol, 0.5) * uESheen * pow(efr, 3.0);
          totalEmissiveRadiance += diffuseColor.rgb * uESelf;
        }`);
    sh.fragmentShader = fs;
  };
  mat.customProgramCacheKey = () => 'edge|' + (enhanced ? 'E' : '') + (grass ? 'G' : '') + (sway ? 'S' : '') + (grade ? 'R' : '') + mat.type;
  return mat;
}

// ------------------------------------------------------------------------------------------- palettes (tod 0 / tod 1)
const PAL = [
  { horS: 0xfcc088, horA: 0xeab2b0, lowS: 0xf4a88e, lowA: 0xe4a4bc, mid: 0xd29ac4, high: 0x968ac8, zen: 0x4a4896,
    belt: 0x6a2c4a, shadow: 0xa89cd0, sun: 0xffae5c, glow: 0.95, disc: [2.25, 1.5, 0.66], gTint: [1, 1, 1], gSat: 1.04,
    key: 0xffd9a8, keyI: 2.3, fill: 0xffe2d2, fillI: 1.8, hemiS: 0xb8bcff, hemiG: 0xe8b4a8, hemiI: 1.0,
    cShade: 0xb092c4, cLit: 0xffc8b0, haze: 0.0042, exposure: 1.0, warm: 0.06 },
  { horS: 0xff9a58, horA: 0xd598ae, lowS: 0xf68a7c, lowA: 0xb889b8, mid: 0xa476b6, high: 0x5f4da0, zen: 0x1d1b50,
    belt: 0x6a2440, shadow: 0x8576b0, sun: 0xff7e44, glow: 1.12, disc: [2.45, 1.08, 0.36], gTint: [0.9, 0.98, 1.18], gSat: 1.12,
    key: 0xffa070, keyI: 2.1, fill: 0xfac0c4, fillI: 1.65, hemiS: 0x8c86e0, hemiG: 0xc890a0, hemiI: 0.9,
    cShade: 0x76609c, cLit: 0xff9a80, haze: 0.0048, exposure: 0.97, warm: 0.12 },
].map((p) => {
  const o = {};
  for (const k in p) o[k] = (typeof p[k] === 'number' && k !== 'glow' && !/I$/.test(k) && k !== 'haze' && k !== 'exposure' && k !== 'warm' && k !== 'gSat') ? col(p[k]) : p[k];
  return o;
});

// ------------------------------------------------------------------------------------------- terrain
// soft-chroma colour blend (linear RGB): a plain lerp, then give back PART of the chroma the lerp lost (q), so blends of
// complementary pastels stay soft pastel instead of going grey/mud — without swinging through the hue wheel (neon)
const lumOf = (c) => 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
function chromaOf(c) { const l = lumOf(c); return Math.hypot(c.r - l, c.g - l, c.b - l); }
function setChroma(c, k) { const l = lumOf(c), ch = Math.hypot(c.r - l, c.g - l, c.b - l); if (ch < 1e-5) return c; const s = k / ch; c.r = l + (c.r - l) * s; c.g = l + (c.g - l) * s; c.b = l + (c.b - l) * s; return c; }
function mixC(a, b, u, q = 0.35) { if (u <= 0) return a; const ca = chromaOf(a), cb = chromaOf(b); a.lerp(b, u); const c = chromaOf(a); return setChroma(a, lerp(c, lerp(ca, cb, u), q)); }

function buildTerrain() {
  const NA = TERRAIN_NA, radii = RADII;
  const nV = 1 + (radii.length - 1) * NA;
  const pos = new Float32Array(nV * 3), colA = new Float32Array(nV * 3);
  const C = { mint: col(0x84d8b0), peach: col(0xf6b896), lilac: col(0xac90ec), rose: col(0xf0a0c0), cream: col(0xf0d4b6), far: col(0xc4a2d8),
    // the stage: ONE clear mint (analogous variation only); the staging hills: one hue each with value variation
    stage: col(0x7edcb0), stageL: col(0x9eeac2), stageT: col(0x74d8bc),
    hLilacD: col(0x9a80e6), hLilac: col(0xae92f0), hLilacL: col(0xccb6fa), hMint: col(0x88dcb4), hMintL: col(0xa4e8c4) };
  const tmp = new THREE.Color(), t2 = new THREE.Color();
  const FEAT = FEATURES.slice().sort((p, q) => p[3] - q[3]);          // low -> high: the taller hill's colour wins
  const setV = (i, x, z) => {
    const [dp] = pathDist(x, z);
    const y = heightRaw(x, z, dp);
    pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z;
    const r = Math.hypot(x, z);
    // pastel patchwork (very low frequency)
    const n1 = fbm2(x / 52 + 11, z / 52 - 3, 21), n2 = fbm2(x / 43 - 5, z / 43 + 8, 33), n3 = fbm2(x / 61 + 2, z / 61 + 19, 45);
    tmp.copy(C.peach); mixC(tmp, C.mint, smoothstep(-0.25, 0.2, n1));
    mixC(tmp, C.lilac, smoothstep(-0.1, 0.3, n2) * 0.9);
    mixC(tmp, C.rose, smoothstep(0.15, 0.5, n3) * 0.5);
    // the clearing: one calm clear mint (no complementary mixes -> no grey-sage)
    const calm = 1 - smoothstep(8, 19, r);
    if (calm > 0) {
      const cn = vn2(x / 7, z / 7, 5), cn2 = vn2(x / 5.5 + 3, z / 5.5 - 1, 6);
      t2.copy(C.stage).lerp(C.stageL, 0.3 * smoothstep(-0.2, 0.7, cn)).lerp(C.stageT, 0.3 * smoothstep(0.1, 0.8, cn2));
      mixC(tmp, t2, calm * 0.92, 0.6);
    }
    // the staging hills (taller wins): a single hue each, full strength down to the toe, lighter toward the top
    for (const [cx, cz, R, , hue] of FEAT) {
      const d2 = ((x - cx) * (x - cx) + (z - cz) * (z - cz)) / (R * R);
      if (d2 >= 1) continue;
      const top = smooth(1 - d2);
      if (hue === 'lilac') {
        t2.copy(C.hLilacD).lerp(C.hLilac, smoothstep(0, 0.4, top)).lerp(C.hLilacL, 0.5 * smoothstep(0.35, 1, top));
        mixC(tmp, t2, smoothstep(1.0, 0.66, d2), 0.45);          // wide toe blend (wider than the mesh spacing: no teeth)
      } else if (hue === 'mint') {
        mixC(tmp, t2.copy(C.hMint).lerp(C.hMintL, 0.35 * top), smoothstep(1, 0.6, d2) * 0.85, 0.6);
      } else {
        mixC(tmp, t2.copy(C[hue]).multiplyScalar(1 + 0.06 * top), smoothstep(1, 0.6, d2) * 0.85, 0.6);
      }
    }
    // far hills drift toward a lilac-rose
    tmp.lerp(C.far, smoothstep(90, 260, r) * 0.45);
    // worn, paler grass along the path edges
    tmp.lerp(C.cream, Math.exp(-Math.pow(dp / 1.2, 2)) * 0.18 * (1 - smoothstep(150, 300, r)));
    // gentle tonal variation (2-4 m), crests a touch lighter
    const k = 1 + 0.035 * fbm2(x / 3.2, z / 3.2, 77) + 0.012 * clamp(y, -3, 6);
    // a mild overall saturation lift (pastel, not neon)
    const lum = lumOf(tmp), sat = 1.12;
    colA[i * 3] = (lum + (tmp.r - lum) * sat) * k; colA[i * 3 + 1] = (lum + (tmp.g - lum) * sat) * k; colA[i * 3 + 2] = (lum + (tmp.b - lum) * sat) * k;
  };
  setV(0, 0, 0);
  for (let j = 1; j < radii.length; j++) for (let a = 0; a < NA; a++) { const [x, z] = ringXZ(j, a); setV(1 + (j - 1) * NA + a, x, z); }
  const vi = (j, a) => (j === 0 ? 0 : 1 + (j - 1) * NA + (((a % NA) + NA) % NA));
  const idx = [];
  for (let j = 0; j < radii.length - 1; j++) for (let a = 0; a < NA; a++) for (const tri of quadTris(j, a)) idx.push(...tri.map(([jj, aa]) => vi(jj, aa)));
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(colA, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  // winding check: normals must point up
  if (g.attributes.normal.array[1] < 0) { g.index.array.reverse(); g.computeVertexNormals(); }
  const mat = edgify(new THREE.MeshLambertMaterial({ vertexColors: true }), { grass: true, scatter: 0.22, sheen: 0.06, self: 0.17, form: 1, grade: true });
  const grp = splitByRadius(g, mat, 'edge.terrain');
  grp.userData.inner.renderOrder = grp.userData.outer.renderOrder = -20;   // first: the path ribbon draws right after it
  return grp;
}
// Split a ground mesh into an inner part (r < SHADOW_R: always receives the key's shadows) and an outer part (receives
// them only when update(opts.shadowAt) moves the frustum away from the origin). PCF-soft costs 16 taps per pixel, so
// this keeps the far ground cheap in the usual shots.
const SHADOW_R = 18;
function splitByRadius(g, mat, name) {
  const p = g.attributes.position.array, ix = g.index.array, inn = [], out = [];
  const rr = (v) => Math.hypot(p[v * 3], p[v * 3 + 2]);
  for (let i = 0; i < ix.length; i += 3) {
    const a = ix[i], b = ix[i + 1], c = ix[i + 2];
    (Math.max(rr(a), rr(b), rr(c)) <= SHADOW_R ? inn : out).push(a, b, c);
  }
  const grp = new THREE.Group(); grp.name = name;
  for (const [list, key] of [[inn, 'inner'], [out, 'outer']]) {
    const sub = new THREE.BufferGeometry();
    for (const k in g.attributes) sub.setAttribute(k, g.attributes[k]);
    sub.setIndex(list);
    const m = new THREE.Mesh(sub, mat);
    m.receiveShadow = key === 'inner'; m.renderOrder = mat.transparent ? -10 : 0; m.name = name + '.' + key;
    grp.add(m); grp.userData[key] = m;
  }
  grp.userData.material = mat;
  return grp;
}

// ------------------------------------------------------------------------------------------- path ribbon
function buildPath() {
  const { X, Z, N } = PATH;
  const ACROSS = [-1, -0.55, 0, 0.55, 1], AL = [0, 0.82, 1, 0.82, 0];
  const pos = [], colA = [], idx = [];
  const cC = col(0xf4e4cc), cE = col(0xe8ceb0);
  const i0 = 0, step = 1;
  let rows = 0;
  for (let i = i0; i <= N; i += step) {
    const x = X[i], z = Z[i];
    const ip = Math.min(N, i + 1), im = Math.max(0, i - 1);
    let tx = X[ip] - X[im], tz = Z[ip] - Z[im]; const tl = Math.hypot(tx, tz) || 1; tx /= tl; tz /= tl;
    const nx = -tz, nz = tx;
    const r = Math.hypot(x, z);
    const w = (0.7 + 0.06 * noise1(i * 0.021, 3) + 0.05 * Math.sin(i * 0.013)) * lerp(1.0, 2.0, smoothstep(40, 220, r));
    const endFade = 1 - smoothstep(N - 70, N, i);
    for (let k = 0; k < ACROSS.length; k++) {
      const px = x + nx * w * ACROSS[k], pz = z + nz * w * ACROSS[k];
      // on the RENDERED terrain mesh (never below it), 1.2 cm up on the stage, ~2-3 cm on the hills
      pos.push(px, pathSurfaceAt(px, pz), pz);
      const c = cE.clone().lerp(cC, AL[k]);
      colA.push(c.r, c.g, c.b, AL[k] * endFade);
    }
    rows++;
  }
  for (let j = 0; j < rows - 1; j++) for (let k = 0; k < ACROSS.length - 1; k++) {
    const a = j * ACROSS.length + k, b = a + 1, c = a + ACROSS.length, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(colA, 4));
  g.setIndex(idx);
  g.computeVertexNormals();
  if (g.attributes.normal.array[1] < 0) { g.index.array.reverse(); g.computeVertexNormals(); }
  // Blended, but drawn in the OPAQUE pass right after the terrain (renderOrder -10, no depth write): everything drawn
  // later — characters' feet included — lands ON TOP of the ribbon instead of sinking into a late transparent decal.
  const mat = edgify(new THREE.MeshLambertMaterial({ vertexColors: true, transparent: false, depthWrite: false,
    blending: THREE.CustomBlending, blendSrc: THREE.SrcAlphaFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
    blendSrcAlpha: THREE.ZeroFactor, blendDstAlpha: THREE.OneFactor,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 }), { grass: true, scatter: 0.26, sheen: 0.04, self: 0.07 });
  const grp = splitByRadius(g, mat, 'edge.path');
  grp.userData.inner.renderOrder = grp.userData.outer.renderOrder = -10;
  return grp;
}

// ------------------------------------------------------------------------------------------- sky
const SKY_FS = /* glsl */`
varying vec3 vW; varying vec3 vGrad;
uniform float uEStars, uESunR;
uniform vec3 uEDisc;
${SKY_PARS}
float eStar(vec3 d, float dens){
  vec3 p = d * 150.0; vec3 c = floor(p); vec3 f = fract(p);
  float h = eHash(c + 0.37);
  if (h > dens) return 0.0;
  vec3 sp = 0.25 + 0.5 * vec3(eHash(c + 13.1), eHash(c + 27.7), eHash(c + 41.3));
  float r = length(f - sp);
  float tw = 0.78 + 0.22 * sin(uETime * (0.5 + 1.2 * eHash(c + 5.1)) + 37.0 * h);
  return smoothstep(0.24, 0.02, r) * tw * (0.35 + 0.9 * eHash(c + 71.3));
}
void main(){
  vec3 d = normalize(vW - cameraPosition);
  vec3 c = vGrad;                                         // smooth gradient: evaluated per vertex (dense near the horizon)
  float ang2 = 2.0 * (1.0 - dot(d, uESunDir));            // ≈ angle² to the sun (small-angle exact)
  c += uESunCol * uEGlow * 0.55 * exp(-ang2 / 0.0032);
  // a warm glowing line hugging the horizon under the sun
  vec2 dh = normalize(d.xz + vec2(1e-6, 0.0));
  float dAz2 = 2.0 * (1.0 - dot(dh, normalize(uESunDir.xz)));
  float hy = max(d.y, 0.0) / 0.018;
  c += uESunCol * uEGlow * 0.3 * exp(-hy * hy - dAz2 / 0.12);
  float ang = sqrt(max(ang2, 0.0));
  float disc = smoothstep(uESunR + 0.011, uESunR - 0.004, ang);
  c = mix(c, uEDisc, disc);
  float vm = eVoidMask(d);
  if (vm > 0.0) {
    // perceptual curve (reads already at 0.4-0.6), toward a deep but clearly INDIGO night (not near-black / mauve)
    float vp = pow(vm, 0.6);
    float n2 = eNoise(d * 7.0 - vec3(uETime * 0.015));
    float n3 = eNoise(d * 2.2 + vec3(5.0, uETime * 0.01, 0.0));
    vec3 deep = mix(vec3(0.045, 0.04, 0.17), vec3(0.075, 0.05, 0.22), n2);
    deep += vec3(0.20, 0.08, 0.36) * 0.3 * smoothstep(0.45, 0.85, n3);
    deep += vec3(0.03, 0.16, 0.22) * 0.2 * smoothstep(0.55, 0.9, n2);
    c = mix(c, deep, vp * 0.94);
    c += vec3(0.40, 0.22, 0.85) * 0.12 * vp * (1.0 - vp) * 4.0;          // soft violet fringe
  }
  float sh = smoothstep(0.26, 0.8, d.y);
  float dens = uEStars * 0.016 * sh + vm * 0.11;
  if (dens > 0.0015) {
    float st = eStar(d, dens) * (uEStars * 1.1 * sh + vm * 1.9);
    c += vec3(0.95, 0.93, 1.0) * st * 1.8;
  }
  gl_FragColor = vec4(c, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function buildSky() {
  const L = { uEStars: { value: 0.4 }, uESunR: { value: 0.040 }, uEDisc: { value: V3(7, 5, 2.9) } };
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...U, ...L }, side: THREE.DoubleSide, depthWrite: false, fog: false,
    vertexShader: `varying vec3 vW; varying vec3 vGrad;\n${SKY_PARS}\nvoid main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz;
      vGrad = eSkyGrad(normalize(w.xyz - cameraPosition)); gl_Position = projectionMatrix * viewMatrix * w; }`,
    fragmentShader: SKY_FS,
  });
  // lat-long dome with rings every ~1° near the horizon (where the gradient changes fastest), coarser above
  const els = [-90, -45, -20, -10, -6, -4, -3, -2, -1.2, -0.5, 0, 0.6, 1.3, 2];
  for (let e = 3; e <= 20; e += 1) els.push(e);
  for (let e = 22.5; e <= 45; e += 2.5) els.push(e);
  for (let e = 50; e <= 90; e += 5) els.push(e);
  const NA = 160, sp = [], si = [];
  els.forEach((e) => { for (let i = 0; i <= NA; i++) { const d = dirAzEl((i / NA) * TAU, e * DEG); sp.push(d.x * SKY_R, d.y * SKY_R, d.z * SKY_R); } });
  for (let j = 0; j < els.length - 1; j++) for (let i = 0; i < NA; i++) {
    const a0 = j * (NA + 1) + i, b0 = a0 + NA + 1;
    si.push(a0, a0 + 1, b0, a0 + 1, b0 + 1, b0);
  }
  const sg = new THREE.BufferGeometry();
  sg.setAttribute('position', new THREE.Float32BufferAttribute(sp, 3)); sg.setIndex(si);
  const m = new THREE.Mesh(sg, mat);
  // drawn LAST among opaques (depth-tested, no depth write): early-z skips every sky pixel hidden by terrain/props/characters
  m.renderOrder = 1000; m.frustumCulled = false; m.name = 'edge.sky';
  m.userData.L = L;
  return m;
}

// ------------------------------------------------------------------------------------------- clouds
// A 2x2 atlas of soft procedural clouds (cells 256x128: two sculpted cumulus, a low bank, a feathered streak).
// Each cloud is a smooth height field (soft union of dome caps + a flat base): R = coverage, G = thinness (backlit
// edges transmit light), B/A = the form normal (x, y) in the billboard plane -> lit per cloud by the actual low sun.
function cloudAtlas() {
  const W = 512, H = 256, CW = 256, CH = 128;
  const data = new Uint8Array(W * H * 4);
  const types = ['cumulus', 'cumulus', 'bank', 'streak'];
  const HF = new Float32Array(CW * CH);
  for (let v = 0; v < 4; v++) {
    const ox = (v % 2) * CW, oy = Math.floor(v / 2) * CH;
    const R = rng(1000 + v * 37);
    const type = types[v];
    const blobs = [];                      // [cx, cy, rx, ry] in px (y up from the cell bottom)
    let base = 20, k = 5, gScale = 1;
    if (type === 'cumulus') {
      base = 24;
      const n = 5;
      for (let i = 0; i < n; i++) {
        const u = (i + 0.5) / n, big = Math.pow(Math.sin(u * Math.PI), 0.9);
        const r = (20 + 26 * big) * (0.85 + 0.3 * R());
        blobs.push([30 + 196 * u + (R() - 0.5) * 14, base + r * (0.25 + 0.15 * R()), r * 1.05, r]);
      }
      for (let i = 0; i < 9; i++) {         // cauliflower puffs on the upper surface
        const u = 0.18 + 0.64 * R(), env = Math.sin(u * Math.PI);
        const r = 10 + 13 * R() * env + 4;
        blobs.push([22 + 212 * u, base + 22 + 46 * env * (0.6 + 0.4 * R()), r * 1.05, r]);
      }
    } else if (type === 'bank') {
      base = 26; k = 6; gScale = 0.6;
      for (let i = 0; i < 16; i++) { const u = (i + 0.5) / 16; const r = (7 + 16 * Math.sin(u * Math.PI)) * (0.6 + 0.6 * R()); blobs.push([10 + 236 * u, base + r * 0.3, r * 1.9, r]); }
    } else {
      base = -100; k = 4; gScale = 0.35;
      for (let i = 0; i < 24; i++) { const u = R(); const env = Math.pow(Math.sin(u * Math.PI), 0.7); const r = (3 + 9 * env * R()) * (R() < 0.25 ? 0.5 : 1);
        blobs.push([14 + 228 * u, 58 + 14 * Math.sin(u * 4.2 + 1) + (R() - 0.5) * 10 * env, r * (3 + 3 * R()), r]); }
    }
    // soft union (log-sum-exp) of dome caps
    for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
      let s = 0;
      for (const [cx, cy, rx, ry] of blobs) {
        const dx = (x - cx) / rx, dy = (y - cy) / ry, q = 1 - dx * dx - dy * dy;
        if (q > -0.4) s += Math.exp((ry * Math.sqrt(Math.max(q, 0)) - (q < 0 ? -q * ry * 0.6 : 0)) / k);
      }
      let h = s > 0 ? k * Math.log(s) : -40;
      h += 1.8 * vn2(x / 15, y / 15, 70 + v) + 0.7 * vn2(x / 8, y / 8, 90 + v);    // organic edge, gentle (no fur)
      if (base > 0) h -= Math.max(0, base - y) * 2.2;                                // a flat-ish base
      h *= smoothstep(0, 10, x) * smoothstep(CW - 1, CW - 11, x) * smoothstep(0, 6, y) * smoothstep(CH - 1, CH - 7, y);
      HF[y * CW + x] = h;
    }
    // soften the field (2 box passes) so the form normals are smooth puffs, not grain
    for (let pass = 0; pass < 2; pass++) {
      const T = Float32Array.from(HF);
      for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
        let a = 0; for (let d = -2; d <= 2; d++) a += T[y * CW + clamp(x + d, 0, CW - 1)];
        HF[y * CW + x] = a / 5;
      }
      T.set(HF);
      for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
        let a = 0; for (let d = -2; d <= 2; d++) a += T[clamp(y + d, 0, CH - 1) * CW + x];
        HF[y * CW + x] = a / 5;
      }
    }
    for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
      const h = HF[y * CW + x];
      const hx = HF[y * CW + clamp(x + 1, 0, CW - 1)] - HF[y * CW + clamp(x - 1, 0, CW - 1)];
      const hy = HF[clamp(y + 1, 0, CH - 1) * CW + x] - HF[clamp(y - 1, 0, CH - 1) * CW + x];
      let nx = -hx * 0.5 * gScale, ny = -hy * 0.5 * gScale, nz = 1;
      // the underside (near the flat base) faces down a little more: the low sun lights it from below
      if (base > 0) ny -= 0.9 * (1 - smoothstep(base, base + 26, y));
      const nl = Math.hypot(nx, ny, nz); nx /= nl; ny /= nl;
      const cov = type === 'streak' ? smoothstep(0.0, 5, h) * 0.85 : smoothstep(0.5, 7, h);
      const thin = cov * (1 - smoothstep(2, type === 'cumulus' ? 26 : 12, h));
      const i = ((oy + y) * W + ox + x) * 4;
      data[i] = Math.round(cov * 255); data[i + 1] = Math.round(thin * 255);
      data[i + 2] = Math.round((nx * 0.5 + 0.5) * 255); data[i + 3] = Math.round((ny * 0.5 + 0.5) * 255);
    }
  }
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat, THREE.UnsignedByteType);
  tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearMipmapLinearFilter; tex.generateMipmaps = true;
  tex.premultiplyAlpha = false;
  tex.needsUpdate = true;
  return tex;
}
const CLOUD_VS = /* glsl */`
attribute vec3 aCl; varying vec2 vUv; varying vec3 vCl; varying vec3 vBg; varying vec3 vSun; varying vec3 vL;
${SKY_PARS}
void main(){
  vUv = uv; vCl = aCl;
  vec4 w = modelMatrix * vec4(position, 1.0);
  vec3 d = normalize(w.xyz - cameraPosition);
  float sp = max(dot(d, uESunDir), 0.0);
  vSun = vec3(pow(sp, 14.0), pow(sp, 3.0), eVoidMask(d));      // near-sun, sun-side, void bleed
  vBg = eSkyGrad(d);
  // the sun direction in the billboard's frame (x right, y up, z toward the viewer near the origin)
  vec3 f = normalize(w.xyz), rt = normalize(cross(f, vec3(0.0, 1.0, 0.0))), up = cross(rt, f);
  vL = vec3(dot(uESunDir, rt) * aCl.z, dot(uESunDir, up), -dot(uESunDir, f));
  gl_Position = projectionMatrix * viewMatrix * w;
}`;
const CLOUD_FS = /* glsl */`
varying vec2 vUv; varying vec3 vCl; varying vec3 vBg; varying vec3 vSun; varying vec3 vL;
uniform sampler2D uMap; uniform vec3 uCShade, uCLit, uESunCol, uEHigh; uniform float uCOpacity, uEGlow;
void main(){
  vec4 tx = texture2D(uMap, vUv);
  float a = tx.r * vCl.x * uCOpacity;
  if (a < 0.004) discard;
  float near = vSun.x, side = vSun.y, vm = vSun.z;
  vec3 n = vec3(tx.b * 2.0 - 1.0, tx.a * 2.0 - 1.0, 0.0); n.z = sqrt(max(1.0 - dot(n.xy, n.xy), 0.0));
  vec3 L = normalize(vL);
  // sculpted form: wrap-lit by the low sun (from below / behind / in front, per cloud), cool sky on the tops
  float lit = smoothstep(-0.5, 0.8, dot(n, L));
  vec3 body = mix(uCShade, uCLit, lit);
  body += uEHigh * 0.22 * max(n.y, 0.0);
  // the low sun warms the undersides (and the flat base) of every cloud on the sun's side of the sky
  body += uCLit * uESunCol * 0.45 * max(-n.y, 0.0) * (0.3 + 0.7 * side);
  vec3 c = mix(body, vBg, 0.1);
  // backlit: thin parts + silhouette edges glow (silver/gold lining) — on the edges that face the sun, near the sun
  float edge = pow(1.0 - n.z, 1.5);
  float toward = 0.25 + 0.75 * smoothstep(-0.2, 0.7, dot(normalize(n.xy + 1e-4), normalize(L.xy + 1e-4)));
  c += uESunCol * uEGlow * (0.55 * edge + 0.8 * tx.g) * toward * (1.6 * near + 0.3 * side) * vCl.y;
  c = mix(c, vec3(0.06, 0.05, 0.19), vm * 0.85);
  a *= 1.0 - vm * 0.5;
  gl_FragColor = vec4(c, a);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function buildClouds() {
  const R = rng(4242);
  const list = [];
  // [az (rad, relative to the sun), el (deg), width (m at dist), variant, opacity, rimBoost, dist]
  // low warm banks hugging the horizon on both sides of the sun gap
  list.push([-0.42, 2.6, 120, 2, 0.8, 1.0, 300], [0.36, 3.2, 105, 2, 0.75, 1.0, 305], [-0.95, 4.0, 90, 2, 0.7, 0.8, 300], [0.9, 3.0, 110, 2, 0.7, 0.8, 300]);
  // a thin streak crossing above the sun
  list.push([0.08, 17.5, 95, 3, 0.5, 1.2, 290]);
  // HERO cumulus on the two main camera axes: sunward (world -Z; the sun is 8° left of it) and the north-east staging
  // master (world azimuth ~2.38 rad), low enough to sit in portrait frames, above head height in eye-level mediums
  list.push([0.30, 10.5, 58, 0, 0.97, 1.0, 285], [-0.33, 13.5, 50, 1, 0.95, 1.0, 286]);           // sunward pair (±10° of -Z)
  list.push([2.44, 4.6, 56, 0, 0.97, 0.8, 284], [2.84, 6.2, 44, 1, 0.95, 0.8, 287]);              // NE master pair
  // more puffy cumulus around the sky (none directly over the sun)
  const cum = [[-0.95, 9, 70], [0.75, 15, 75], [-1.5, 15, 85], [1.4, 11, 80], [-2.4, 12, 85], [3.3, 15, 80], [-0.1, 24, 60], [1.05, 26, 70]];
  for (const [a, e, w] of cum) list.push([a, e, w, R() < 0.5 ? 0 : 1, 0.88, 0.8, 285]);
  // high wisps
  const hi = [[-0.3, 36, 90], [0.6, 44, 100], [-1.1, 33, 80], [2.0, 40, 100], [-2.6, 38, 95], [1.3, 52, 110]];
  for (const [a, e, w] of hi) list.push([a, e, w, 3, 0.45, 0.6, 280]);
  const pos = [], uv = [], cl = [], idx = [];
  const up = V3(0, 1, 0);
  list.forEach(([a, e, w, v, op, rim, dist], n) => {
    const f = dirAzEl(SUN_AZ + a, e * DEG);
    const c = f.clone().multiplyScalar(dist);
    const right = V3().crossVectors(f, up).normalize();
    const upv = V3().crossVectors(right, f).normalize();
    const hgt = w * (v === 3 ? 0.32 : v === 2 ? 0.34 : 0.5) * (0.9 + 0.2 * R());
    const flip = R() < 0.5;
    const u0 = (v % 2) * 0.5, v0 = Math.floor(v / 2) * 0.5;
    // subdivided quad (the sky colour behind / sun proximity are evaluated per vertex)
    const NX = 8, NY = 4, b0 = pos.length / 3;
    for (let j = 0; j <= NY; j++) for (let i = 0; i <= NX; i++) {
      const sx = (i / NX) * 2 - 1, sy = (j / NY) * 2 - 1;
      const p = c.clone().addScaledVector(right, sx * w / 2).addScaledVector(upv, sy * hgt / 2);
      pos.push(p.x, p.y, p.z);
      const ux = flip ? -sx : sx;
      uv.push(u0 + (ux * 0.5 + 0.5) * 0.5, v0 + (sy * 0.5 + 0.5) * 0.5);
      cl.push(op, rim, flip ? -1 : 1);
    }
    for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
      const q = b0 + j * (NX + 1) + i;
      idx.push(q, q + 1, q + NX + 2, q, q + NX + 2, q + NX + 1);
    }
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('aCl', new THREE.Float32BufferAttribute(cl, 3));
  g.setIndex(idx);
  const L = { uMap: { value: cloudAtlas() }, uCShade: { value: new THREE.Color() }, uCLit: { value: new THREE.Color() }, uCOpacity: { value: 1 } };
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...U, ...L }, transparent: true, depthWrite: false, fog: false, side: THREE.DoubleSide,
    vertexShader: CLOUD_VS,
    fragmentShader: CLOUD_FS,
  });
  const m = new THREE.Mesh(g, mat);
  m.renderOrder = -900; m.frustumCulled = false; m.name = 'edge.clouds';
  m.userData.L = L;
  return m;
}

// ------------------------------------------------------------------------------------------- trees + bushes
const HUES = {
  roseGold: [0xffd2c4, 0xf4a0a8], rose: [0xf7b6c8, 0xff8fb0], peach: [0xffcfa4, 0xffa070], mint: [0xb4f0d0, 0x60e0b0], lilac: [0xd2c0ff, 0xa688ff], gold: [0xffe2a0, 0xffc060],
};
function glowMat(hue, { glow = 0.3, rim = 1.0, wrap = 0.45, rough = 0.75, rimColor = null, rimPower = 2.4 } = {}) {
  const [base, rimC] = HUES[hue];
  const m = new THREE.MeshStandardMaterial({ color: col(base), roughness: rough, metalness: 0, vertexColors: true });
  enhance(m, { rim, rimColor: rimColor ?? rimC, rimPower, glow, glowColor: base, wrap, wrapColor: rimC });
  return edgify(m);
}
/**
 * Smooth-union blob surface: an icosphere shrink-wrapped onto a soft union of ellipsoids [cx, cy, cz, r, flatY]
 * (k = blend radius, m). One closed mesh with SDF-gradient normals: no intersection seams, no faceted outlines.
 * Vertex colour: soft AO (darker toward the base and in the creases between puffs).
 */
function blobSurface(blobs, k, detail, aoFloor = 0.64, crease = 0.22) {
  const sd = (x, y, z) => {
    let d = 1e9;
    for (const [cx, cy, cz, r, fy] of blobs) {
      const dx = (x - cx) / r, dy = (y - cy) / (r * fy), dz = (z - cz) / r;
      const di = (Math.sqrt(dx * dx + dy * dy + dz * dz) - 1) * r * Math.min(1, fy);
      const h = Math.max(k - Math.abs(d - di), 0) / k;
      d = Math.min(d, di) - h * h * k * 0.25;
    }
    return d;
  };
  const hard = (x, y, z) => { let d = 1e9; for (const [cx, cy, cz, r, fy] of blobs) { const dx = (x - cx) / r, dy = (y - cy) / (r * fy), dz = (z - cz) / r; d = Math.min(d, (Math.sqrt(dx * dx + dy * dy + dz * dz) - 1) * r * Math.min(1, fy)); } return d; };
  let wsum = 0; const c = V3();
  for (const [cx, cy, cz, r] of blobs) { const w = r * r * r; c.x += cx * w; c.y += cy * w; c.z += cz * w; wsum += w; }
  c.multiplyScalar(1 / wsum);
  let tmax = 0; for (const [cx, cy, cz, r] of blobs) tmax = Math.max(tmax, Math.hypot(cx - c.x, cy - c.y, cz - c.z) + r * 1.2);
  const g0 = new THREE.IcosahedronGeometry(1, detail); g0.deleteAttribute('normal'); g0.deleteAttribute('uv');
  const g = mergeVertices(g0);
  const p = g.attributes.position, n = p.count;
  const nor = new Float32Array(n * 3), colA = new Float32Array(n * 3);
  const step = tmax / 40, e = 0.004 * tmax;
  let y0 = 1e9, y1 = -1e9;
  for (let i = 0; i < n; i++) {
    const dx = p.getX(i), dy = p.getY(i), dz = p.getZ(i);
    let t = tmax;
    while (t > 0 && sd(c.x + dx * t, c.y + dy * t, c.z + dz * t) > 0) t -= step;
    let lo = Math.max(t, 0), hi = t + step;
    for (let it = 0; it < 16; it++) { const m = (lo + hi) / 2; if (sd(c.x + dx * m, c.y + dy * m, c.z + dz * m) > 0) hi = m; else lo = m; }
    const tt = (lo + hi) / 2, x = c.x + dx * tt, y = c.y + dy * tt, z = c.z + dz * tt;
    p.setXYZ(i, x, y, z);
    const gx = sd(x + e, y, z) - sd(x - e, y, z), gy = sd(x, y + e, z) - sd(x, y - e, z), gz = sd(x, y, z + e) - sd(x, y, z - e);
    const gl = Math.hypot(gx, gy, gz) || 1;
    nor[i * 3] = gx / gl; nor[i * 3 + 1] = gy / gl; nor[i * 3 + 2] = gz / gl;
    colA[i * 3] = clamp(hard(x, y, z) / (k * 0.3));            // crease depth (temporarily)
    y0 = Math.min(y0, y); y1 = Math.max(y1, y);
  }
  for (let i = 0; i < n; i++) {
    const ao = (aoFloor + (1 - aoFloor) * smoothstep(y0, y1, p.getY(i))) * (1 - crease * colA[i * 3]);
    colA[i * 3] = colA[i * 3 + 1] = colA[i * 3 + 2] = ao;
  }
  g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  g.setAttribute('color', new THREE.BufferAttribute(colA, 3));
  g.computeBoundingSphere();
  return g;
}
function clusterBlobs(R, n, spread, rMin, rMax, flatY = 0.85) {
  const blobs = [];
  for (let i = 0; i < n; i++) {
    const a = R() * TAU, d = Math.sqrt(R()) * spread, rr = lerp(rMin, rMax, R());
    blobs.push([Math.cos(a) * d, rr * flatY * 0.75 + R() * spread * 0.35, Math.sin(a) * d, rr, flatY]);
  }
  return blobs;
}
const lodFor = (x, z, near, mid, far) => { const d = Math.hypot(x, z); return d < 10 ? near : d < 24 ? mid : far; };
function buildBush(x, z, s, hue, seed) {
  const R = rng(seed);
  const blobs = clusterBlobs(R, 4 + Math.floor(R() * 3), 0.55 * s, 0.32 * s, 0.62 * s);
  const m = new THREE.Mesh(blobSurface(blobs, 0.1 * s, lodFor(x, z, 12, 9, 6)), glowMat(hue, { glow: 0.26, rim: 0.8 }));
  m.position.set(x, groundAt(x, z) - 0.06, z);
  m.rotation.y = R() * TAU;
  m.castShadow = true;
  m.name = 'edge.bush';
  m.userData.casters = [m];
  return m;
}
function trunkGeo(R, th, k, r0 = 0.24, r1 = 0.13) {
  const prof = [];
  for (let i = 0; i <= 14; i++) { const u = i / 14; prof.push(new THREE.Vector2((lerp(r0, r1, Math.pow(u, 0.7)) + 0.2 * Math.exp(-u * 12)) * k, u * th)); }
  const tg = new THREE.LatheGeometry(prof, 16);
  const bend = (0.25 + 0.2 * R()) * k, ph = R() * 2;
  const tp = tg.attributes.position;
  for (let i = 0; i < tp.count; i++) { const u = tp.getY(i) / th; tp.setX(i, tp.getX(i) + bend * Math.sin(u * 2.4 + ph) * u); }
  tg.computeVertexNormals();
  return { tg, top: V3(bend * Math.sin(2.4 + ph), th, 0) };
}
function fruitGeo(R, top, k, n, rad, drop) {
  const geos = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n + R() * 0.1) * TAU, d = (0.55 + 0.35 * R()) * rad;
    const f = new THREE.SphereGeometry(0.07 * k, 12, 8);
    f.translate(top.x + Math.cos(a) * d, top.y - drop - R() * 0.2 * k, top.z + Math.sin(a) * d);
    geos.push(f);
  }
  return mergeGeometries(geos);
}
function buildTree(x, z, H, hue, seed, crystal = false) {
  const R = rng(seed);
  const k = H / 5;
  const grp = new THREE.Group();
  grp.position.set(x, groundAt(x, z) - 0.05, z);
  grp.rotation.y = R() * TAU;
  // trunk: a soft, slightly S-curved lathe with a flared foot
  const { tg, top } = trunkGeo(R, H * 0.5, k);
  const trunkMat = new THREE.MeshStandardMaterial({ color: col(0xf6e6ee), roughness: 0.7 });
  enhance(trunkMat, { rim: 0.55, rimColor: HUES[hue][1], rimPower: 2.4, glow: 0.14, wrap: 0.45, wrapColor: HUES[hue][1] });
  edgify(trunkMat);
  const trunk = new THREE.Mesh(tg, trunkMat); trunk.castShadow = true; grp.add(trunk);
  // canopy: ONE smooth soft-union mass of glowing puffs (wider than tall), with a faint light halo
  const blobs = clusterBlobs(R, crystal ? 8 : 9, 0.78 * k, 0.6 * k, 0.98 * k, crystal ? 0.95 : 0.86);
  const canopy = new THREE.Mesh(blobSurface(blobs, 0.16 * k, lodFor(x, z, 20, 14, 9)),
    glowMat(hue, crystal ? { glow: 0.36, rim: 0.7, wrap: 0.55, rough: 0.45, rimColor: 0xc8a8ff, rimPower: 2.2 } : { glow: 0.34, rim: 1.0, wrap: 0.45 }));
  canopy.position.copy(top).add(V3(0, -0.6 * k, 0)); canopy.castShadow = true;
  const sway = new THREE.Group(); sway.add(canopy); grp.add(sway);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color: col(HUES[hue][1]), transparent: true, opacity: 0.16,
    blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  halo.scale.setScalar(4.6 * k); halo.position.copy(top).add(V3(0, 0.35 * k, 0)); sway.add(halo);
  // a few little lantern-fruits peeking under the canopy (HDR, they bloom) — one merged mesh
  const fruitMat = edgify(new THREE.MeshBasicMaterial({ color: col(HUES[hue][1]).multiplyScalar(1.8) }));
  sway.add(new THREE.Mesh(fruitGeo(R, top, k, 5, k, 0.35 * k), fruitMat));
  grp.userData = { sway, phase: R() * TAU, amp: 0.006 + 0.004 * R(), casters: [trunk, canopy], reach: 0.5 * H };
  grp.name = 'edge.tree';
  return grp;
}
/**
 * The rose-gold "soft crystal" tree beside the bend (scenes/marks.js EDGE.TREE_WORLD = (2, 0, -5.2)): a slender tall
 * trunk and a compact, smooth satin-candy crown held HIGH (crown bottom ~2.75 m, so it clears heads in eye-level and
 * OTS framings), calm finish (roughness 0.45, no metal, no hot spots), soft iridescent lilac rim, no halo sprite.
 * update(opts.heroTreeGlow 0..1) calms it for close-ups; opts.hideHeroTree removes it for a shot.
 */
function buildHeroTree(x, z) {
  const R = rng(9090);
  const grp = new THREE.Group();
  grp.position.set(x, groundAt(x, z) - 0.04, z);
  grp.rotation.y = 0.6;
  const k = 0.82;
  const { tg, top } = trunkGeo(R, 3.05, k, 0.2, 0.1);
  const trunkMat = new THREE.MeshStandardMaterial({ color: col(0xf8e8ee), roughness: 0.62 });
  enhance(trunkMat, { rim: 0.4, rimColor: 0xff9a78, rimPower: 2.6, glow: 0.12, wrap: 0.45, wrapColor: 0xff9a78 });
  edgify(trunkMat);
  const trunk = new THREE.Mesh(tg, trunkMat); trunk.castShadow = true; grp.add(trunk);
  // crown: a lobed soft cloud of puffs (core + a drooping lower ring + an upper ring + a top), ~2.3 m wide, ~1.6 m tall,
  // smooth fillets between lobes (k = 0.14 m) so it reads as soft puffs, not one blob and not a pile of balls
  const blobs = [[0, 0.62, 0, 0.62, 0.88]];
  for (let i = 0; i < 6; i++) { const a = i / 6 * TAU + 0.3, rr = 0.4 + 0.07 * Math.sin(i * 2.3); blobs.push([Math.cos(a) * 0.68, 0.34 + 0.08 * Math.sin(i * 1.7), Math.sin(a) * 0.68, rr, 0.86]); }
  for (let i = 0; i < 4; i++) { const a = i / 4 * TAU + 0.9, rr = 0.38 + 0.04 * Math.cos(i * 1.9); blobs.push([Math.cos(a) * 0.36, 0.9, Math.sin(a) * 0.36, rr, 0.9]); }
  blobs.push([0.05, 1.16, -0.02, 0.32, 0.95]);
  const canopyMat = glowMat('roseGold', { glow: 0.24, rim: 0.42, rimColor: 0xd0b0ff, rimPower: 2.4, wrap: 0.5, rough: 0.48 });
  const canopy = new THREE.Mesh(blobSurface(blobs, 0.14, 24, 0.76, 0.14), canopyMat);
  canopy.position.copy(top).add(V3(0, -0.3, 0)); canopy.castShadow = true;
  // three slender branches fork from the trunk up into the crown's underside
  {
    const geos = [], from = V3(top.x * 0.7, 2.25, 0);
    for (let i = 0; i < 3; i++) {
      const a = i / 3 * TAU + 0.5, to = V3(top.x + Math.cos(a) * 0.55, top.y - 0.05, Math.sin(a) * 0.55), L = from.distanceTo(to);
      const bg = new THREE.CylinderGeometry(0.035, 0.06, L, 10, 1, true); bg.translate(0, L / 2, 0);
      bg.applyMatrix4(new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion().setFromUnitVectors(V3(0, 1, 0), to.clone().sub(from).normalize())));
      bg.translate(from.x, from.y, from.z); geos.push(bg);
    }
    const br = new THREE.Mesh(mergeGeometries(geos), trunkMat); br.castShadow = true; grp.add(br);
  }
  const sway = new THREE.Group(); sway.add(canopy); grp.add(sway);
  const fruitMat = edgify(new THREE.MeshBasicMaterial({ color: col(0xffb0a0).multiplyScalar(1.15) }));
  const fruits = new THREE.Mesh(fruitGeo(R, top, 0.7, 4, 0.66, 0.2), fruitMat);   // glowing buds tucked under the crown
  sway.add(fruits);
  grp.userData = { sway, phase: 1.3, amp: 0.004, casters: [trunk, canopy], reach: 3, hero: true, canopyMat, fruitMat, fruits,
    base: { glow: 0.24, rim: 0.42, fruit: fruitMat.color.clone() } };
  grp.name = 'edge.heroTree';
  return grp;
}

// ------------------------------------------------------------------------------------------- flowers
// Tiny glowing flowers: instanced stem + soft low-poly bloom head, plus a faint additive glow point per head
// (so they read as little lights, not pins). ~13k triangles in all.
const FLOWER_GLOW_VS = /* glsl */`
uniform float uETime; attribute float aA; attribute vec3 aC; varying vec3 vC; varying float vA;
void main(){
  vec3 p = position;
  float eph = p.x * 1.7 + p.z * 1.3;
  p.x += sin(uETime * 1.1 + eph) * 0.007; p.z += sin(uETime * 0.83 + eph * 1.3) * 0.005;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  float dist = -mv.z;
  gl_PointSize = clamp(0.085 * projectionMatrix[1][1] * 640.0 / max(dist, 0.1), 1.5, 40.0);
  gl_Position = projectionMatrix * mv;
  vC = aC; vA = aA * smoothstep(0.6, 2.0, dist) * exp(-dist / 40.0);
}`;
const FLOWER_GLOW_FS = /* glsl */`
varying vec3 vC; varying float vA;
void main(){ vec2 q = gl_PointCoord * 2.0 - 1.0; float r2 = dot(q, q); if (r2 > 1.0) discard;
  float g = exp(-r2 * 4.0) * vA;
  gl_FragColor = vec4(vC * g, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function buildFlowers() {
  const R = rng(777);
  const items = [];
  const avoid = (x, z) => { const r = Math.hypot(x, z); if (r < 2.6) return true; return pathDist(x, z)[0] < 1.15; };
  const hues = [0xffd66a, 0xff94c4, 0x84e4ff, 0xbc9cff, 0xffc890];
  for (let c = 0; c < 64; c++) {
    const a = R() * TAU, d = 3.0 + Math.pow(R(), 0.9) * 27;
    const cx = Math.sin(a) * d, cz = -Math.cos(a) * d;
    const n = 3 + Math.floor(R() * 7), hue = hues[Math.floor(R() * hues.length)];
    for (let i = 0; i < n; i++) {
      const x = cx + (R() - 0.5) * 2.4, z = cz + (R() - 0.5) * 2.4;
      if (avoid(x, z)) continue;
      items.push([x, z, 0.75 + 0.6 * R(), R() < 0.8 ? hue : hues[Math.floor(R() * hues.length)], R()]);
    }
  }
  const N = items.length;
  const stemG = new THREE.CylinderGeometry(0.0028, 0.004, 0.085, 4, 1, true); stemG.translate(0, 0.0425, 0);
  const headG = new THREE.IcosahedronGeometry(0.034, 0); headG.scale(1, 0.62, 1); headG.translate(0, 0.095, 0);
  const stems = new THREE.InstancedMesh(stemG, edgify(new THREE.MeshLambertMaterial({ color: col(0x4c9a78) }), { sway: true }), N);
  const heads = new THREE.InstancedMesh(headG, edgify(new THREE.MeshBasicMaterial({ color: 0xffffff }), { sway: true }), N);
  const gp = new Float32Array(N * 3), gc = new Float32Array(N * 3), ga = new Float32Array(N);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = V3(), p = V3(), c = new THREE.Color();
  items.forEach(([x, z, sc, hue, k], i) => {
    p.set(x, groundAt(x, z) - 0.01, z);
    q.setFromAxisAngle(V3(0, 1, 0), k * TAU);
    s.setScalar(sc);
    m4.compose(p, q, s);
    stems.setMatrixAt(i, m4); heads.setMatrixAt(i, m4);
    heads.setColorAt(i, c.set(hue).multiplyScalar(0.85 + 0.35 * k));
    gp.set([x, p.y + 0.095 * sc, z], i * 3);
    c.set(hue); gc.set([c.r * 0.5, c.g * 0.5, c.b * 0.5], i * 3); ga[i] = 0.6 + 0.4 * k;
  });
  stems.instanceMatrix.needsUpdate = heads.instanceMatrix.needsUpdate = true;
  heads.instanceColor.needsUpdate = true;
  const gg = new THREE.BufferGeometry();
  gg.setAttribute('position', new THREE.BufferAttribute(gp, 3)); gg.setAttribute('aC', new THREE.BufferAttribute(gc, 3));
  const aA = new THREE.BufferAttribute(ga, 1); gg.setAttribute('aA', aA);
  const glow = new THREE.Points(gg, new THREE.ShaderMaterial({ uniforms: { uETime: GLOBAL.uTime }, vertexShader: FLOWER_GLOW_VS, fragmentShader: FLOWER_GLOW_FS,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  glow.frustumCulled = false; glow.renderOrder = 5; glow.name = 'edge.flowerGlow';
  const grp = new THREE.Group(); grp.add(stems, heads, glow); grp.name = 'edge.flowers';
  grp.userData = { heads, stems, glow, count: N, items, base: Float32Array.from(heads.instanceMatrix.array), baseA: Float32Array.from(ga), aA, clearKey: '' };
  return grp;
}

// ------------------------------------------------------------------------------------------- thought seeds
// Dandelion-like glowing seeds (own billboard shader + atlas-free sprite), drifting slowly on a soft wind.
function seedTexture() {
  const S = 128, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  const cx = 64, cy = 72;
  let gr = g.createRadialGradient(cx, cy - 14, 0, cx, cy - 14, 56);
  gr.addColorStop(0, 'rgba(255,255,255,0.32)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.08)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, S, S);
  // pappus: soft filaments fanning up and out, each ending in a tiny glowing tuft
  const N = 19;
  for (let i = 0; i < N; i++) {
    const a = -Math.PI / 2 + (i / (N - 1) - 0.5) * Math.PI * 1.25;
    const L = 40 + 4 * Math.sin(i * 1.7);
    const ex = cx + Math.cos(a) * L, ey = cy + Math.sin(a) * L * 0.92;
    g.strokeStyle = 'rgba(255,255,255,0.42)'; g.lineWidth = 1.6; g.lineCap = 'round';
    g.beginPath(); g.moveTo(cx, cy); g.quadraticCurveTo(cx + Math.cos(a) * L * 0.5, cy + Math.sin(a) * L * 0.6 - 4, ex, ey); g.stroke();
    gr = g.createRadialGradient(ex, ey, 0, ex, ey, 5);
    gr.addColorStop(0, 'rgba(255,255,255,0.8)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(ex, ey, 5, 0, TAU); g.fill();
  }
  // stem + seed
  g.strokeStyle = 'rgba(255,255,255,0.55)'; g.lineWidth = 1.8; g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + 1, cy + 20); g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.9)'; g.beginPath(); g.ellipse(cx + 1, cy + 23, 2.4, 4.2, 0, 0, TAU); g.fill();
  gr = g.createRadialGradient(cx, cy, 0, cx, cy, 9);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, 9, 0, TAU); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
class Seeds {
  constructor(max = 200) {
    this.max = max;
    const g = new THREE.InstancedBufferGeometry();
    const base = new THREE.PlaneGeometry(1, 1);
    g.index = base.index; g.attributes.position = base.attributes.position; g.attributes.uv = base.attributes.uv;
    this.aPos = new THREE.InstancedBufferAttribute(new Float32Array(max * 3), 3).setUsage(THREE.DynamicDrawUsage);
    this.aCol = new THREE.InstancedBufferAttribute(new Float32Array(max * 3), 3).setUsage(THREE.DynamicDrawUsage);
    this.aMisc = new THREE.InstancedBufferAttribute(new Float32Array(max * 3), 3).setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('iPos', this.aPos); g.setAttribute('iCol', this.aCol); g.setAttribute('iMisc', this.aMisc);
    g.instanceCount = 0;
    this.mat = new THREE.ShaderMaterial({
      uniforms: { uMap: { value: seedTexture() }, uI: { value: 1 } },
      vertexShader: /* glsl */`
        attribute vec3 iPos, iCol, iMisc; varying vec2 vUv; varying vec3 vCol; varying float vA;
        void main(){
          vec4 mv = modelViewMatrix * vec4(iPos, 1.0);
          float c = cos(iMisc.y), s = sin(iMisc.y);
          mv.xy += vec2(c * position.x - s * position.y, s * position.x + c * position.y) * iMisc.x;
          gl_Position = projectionMatrix * mv;
          vUv = uv; vCol = iCol;
          float dist = length(mv.xyz);
          vA = iMisc.z * smoothstep(0.8, 2.4, dist) * exp(-dist / 48.0);
        }`,
      fragmentShader: /* glsl */`
        uniform sampler2D uMap; uniform float uI; varying vec2 vUv; varying vec3 vCol; varying float vA;
        void main(){ vec4 t = texture2D(uMap, vUv); gl_FragColor = vec4(vCol * uI, t.a * vA);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    this.mesh = new THREE.Mesh(g, this.mat);
    this.mesh.frustumCulled = false; this.mesh.renderOrder = 6; this.mesh.name = 'edge.seeds';
    this.geo = g;
    // fixed per-seed parameters
    const R = rng(9001);
    const tints = [col(0xfff0d0), col(0xfff0d0), col(0xffe0b8), col(0xd8fff0), col(0xe8deff), col(0xffd8e4)];
    this.P = [];
    for (let i = 0; i < max; i++) {
      this.P.push({ x: R(), y: R(), z: R(), sp: 0.7 + 0.6 * R(), ph: R() * TAU, f: 0.7 + 0.6 * R(), size: 0.15 + 0.1 * R(),
        tint: tints[Math.floor(R() * tints.length)], b: 0.8 + 0.5 * R() });
    }
  }
  update(t, density = 1, intensity = 1, wind = [0.11, 0.02, -0.05]) {
    const B = { x0: -15, x1: 15, y0: 0.35, y1: 5.6, z0: -30, z1: 9 };
    const W = B.x1 - B.x0, Hh = B.y1 - B.y0, D = B.z1 - B.z0;
    const n = Math.min(this.max, Math.ceil(70 * Math.max(0, density)));
    const fracA = clamp(70 * density - (n - 1));
    const wrap = (v, a, L) => a + (((v - a) % L) + L) % L;
    let k = 0;
    for (let i = 0; i < n; i++) {
      const p = this.P[i];
      const wx = 0.35 * Math.sin(t * 0.31 * p.f + p.ph), wy = 0.22 * Math.sin(t * 0.43 * p.f + p.ph * 1.7), wz = 0.3 * Math.sin(t * 0.27 * p.f + p.ph * 2.3);
      const x = wrap(B.x0 + p.x * W + wind[0] * p.sp * t + wx, B.x0, W);
      const y = wrap(B.y0 + p.y * Hh + wind[1] * p.sp * t + wy, B.y0, Hh);
      const z = wrap(B.z0 + p.z * D + wind[2] * p.sp * t + wz, B.z0, D);
      const edge = smoothstep(0, 2.5, x - B.x0) * smoothstep(0, 2.5, B.x1 - x) * smoothstep(0, 0.6, y - B.y0) * smoothstep(0, 0.6, B.y1 - y)
        * smoothstep(0, 2.5, z - B.z0) * smoothstep(0, 2.5, B.z1 - z);
      let a = edge * p.b * 0.75 * (i === n - 1 ? fracA : 1);
      if (a < 0.003) continue;
      const gy = groundAt(x, z);
      this.aPos.array.set([x, gy + y, z], k * 3);
      this.aCol.array.set([p.tint.r * 1.8, p.tint.g * 1.8, p.tint.b * 1.8], k * 3);
      this.aMisc.array.set([p.size, 0.28 * Math.sin(t * 0.5 * p.f + p.ph), a], k * 3);
      k++;
    }
    this.geo.instanceCount = k;
    this.aPos.needsUpdate = this.aCol.needsUpdate = this.aMisc.needsUpdate = true;
    this.mat.uniforms.uI.value = intensity;
  }
}

// ------------------------------------------------------------------------------------------- the set
class EdgeSet {
  constructor() {
    const scene = this.scene = new THREE.Scene();
    scene.name = 'SET.EDGE';
    // the terrain is built first so groundAt-based placement and anchors agree with the mesh
    this.sky = buildSky(); scene.add(this.sky);
    this.clouds = buildClouds(); scene.add(this.clouds);
    this.terrain = buildTerrain(); scene.add(this.terrain);
    this.path = buildPath(); scene.add(this.path);
    // luminous puff trees (to the sides; the column behind the faces stays calm) + round glowing bushes
    this.trees = [
      [-8.8, -13.5, 4.6, 'rose'], [10.8, -19.5, 5.4, 'peach'], [-15.5, -31, 6.0, 'mint'], [18.5, -37, 5.2, 'lilac'],
      [15.5, -62, 6.4, 'rose'], [-24, -63, 7.2, 'peach'], [12.5, -31, 5.4, 'mint'], [-17, -41, 6.2, 'rose'], [-31, -21, 6.2, 'lilac'], [27, -8, 5.8, 'mint'],
      [-10.5, 12.5, 4.8, 'lilac', 1], [18.5, 9.5, 5.2, 'gold', 1], [-22, 26, 6.0, 'rose'], [4, 30, 5.4, 'mint'],
      // north-east dressing (the anti-sun backdrop of the staging master): two glowing trees on the far crest
      [21, 41, 6.6, 'rose'], [41, 27, 6.2, 'gold'],
    ].map(([x, z, H, hue, cr], i) => buildTree(x, z, H, hue, 300 + i * 11, !!cr));
    // the rose-gold crystal tree beside the bend (scenes/marks.js EDGE.TREE_WORLD) — the hero prop, built on its own
    this.heroTree = buildHeroTree(2.0, -5.2);
    this.trees.push(this.heroTree);
    this.trees.forEach((t) => scene.add(t));
    this.bushes = [
      [-6.9, -5.5, 1.0, 'mint'], [7.4, -8.2, 1.2, 'lilac'], [-9.8, 4.2, 0.9, 'peach'], [8.8, 3.6, 1.0, 'rose'],
      [-5.6, -17, 0.8, 'lilac'], [10.5, -24, 0.9, 'mint'], [-12.5, -9.5, 1.1, 'rose'], [13.4, -11.5, 1.0, 'peach'],
      [3.6, 10.5, 0.8, 'mint'], [-4.6, 11.4, 0.9, 'lilac'], [-8.0, -14.8, 0.7, 'peach'], [11.6, -21.0, 0.8, 'rose'],
      [-16.5, -33.5, 1.2, 'peach'], [20, -35, 1.0, 'mint'], [0.4, -16.8, 0.7, 'mint'], [-3.9, -15.5, 0.75, 'lilac'],
      [11.4, -33.5, 0.9, 'peach'], [-4.8, -23.5, 0.6, 'rose'],
    ].map(([x, z, s, hue], i) => buildBush(x, z, s, hue, 500 + i * 7));
    this.bushes.forEach((b) => scene.add(b));
    this.flowers = buildFlowers(); scene.add(this.flowers);
    this.seeds = new Seeds(220); scene.add(this.seeds.mesh);
    this.motes = new Particles({ max: 160, blending: 'add', intensity: 1.3, renderOrder: 6 }); scene.add(this.motes.mesh);

    // lights: warm sun key (the one shadow caster, tight frustum), warm front bounce, cool sky hemisphere
    this.hemi = new THREE.HemisphereLight(0xbcc0ff, 0xf0b8a0, 1.0); scene.add(this.hemi);
    this.key = new THREE.DirectionalLight(0xffcf98, 2.7);
    this.key.castShadow = true;
    this.key.shadow.mapSize.set(1024, 1024);
    Object.assign(this.key.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: 5, far: 80 });
    this.key.shadow.bias = -0.0004; this.key.shadow.normalBias = 0.03; this.key.shadow.radius = 3;
    scene.add(this.key, this.key.target);
    this.fill = new THREE.DirectionalLight(0xffd2bc, 1.05); scene.add(this.fill, this.fill.target);
    // gentle depth haze for characters / props that are not "edgified" (very low density)
    scene.fog = new THREE.FogExp2(0xf0c8b8, 0.0055);

    // path anchors: pathStart = closest path point to the origin (S0, a module-level const); pathFar = the crest
    // (highest point 25..60 m out)
    let crestS = 45, crestY = -1e9;
    for (let s = 25; s <= 62; s += 0.5) { const y = pathAt(s).pos[1]; if (y > crestY) { crestY = y; crestS = s; } }
    this.crestS = crestS;
    const sunHz = dirAzEl(SUN_AZ, 0).multiplyScalar(300);
    this.anchors = {
      origin: [0, 0, 0],
      pathStart: pathAt(0).pos, pathStartYaw: pathAt(0).yaw,
      pathFar: pathAt(crestS).pos, pathFarYaw: pathAt(crestS).yaw, pathFarS: crestS,
      pathBeyond: pathAt(crestS + 14).pos,                  // a little past the crest (figures half hidden)
      sunHorizon: [sunHz.x, 0, sunHz.z],                   // ground point on the horizon under the sun
      clearingRadius: 7.5,
    };
    this.props = { sky: this.sky, clouds: this.clouds, terrain: this.terrain, path: this.path, trees: this.trees, bushes: this.bushes,
      flowers: this.flowers, seeds: this.seeds, motes: this.motes, key: this.key, fill: this.fill, hemi: this.hemi };
    // default post look (update() keeps it in sync with tod; scenes may spread/override it)
    this.look = { bloom: 0.45, bloomRadius: 0.6, bloomThreshold: 0.92, vignette: 0.22, sat: 1.06, warm: 0.06, exposure: 1.0 };
    // handy camera presets (shots for core/camera.js applyShot); scenes will usually frame their own
    this.shots = {
      wide: { pos: [0.6, 1.7, 10.5], look: [-0.4, 1.6, -12], fov: 40, drift: 0.4 },
      two: { pos: [0.1, 1.55, 5.2], look: [0.1, 1.42, 0], fov: 32, drift: 0.4 },
      lowUp: { pos: [0.2, 0.55, 3.4], look: [0.6, 2.2, 0], fov: 38, drift: 0.3 },
      highDown: { pos: [0.5, 3.4, 2.8], look: [-0.4, 0.4, 0.4], fov: 36, drift: 0.3 },
      reverse: { pos: [-0.4, 1.6, -5.2], look: [0.2, 1.3, 1.5], fov: 34, drift: 0.4 },
      // sunward: the key is a deliberate cheat (35° left of / higher than the visible sun, so faces turned to camera get
      // modelling); for shots looking INTO the sun fold it back toward the sun -> shadows run toward camera, longer
      walkoff: { pos: [0.4, 1.9, 7.5], look: [-0.8, 1.4, -30], fov: 30, drift: 0.3, opts: { keyYaw: -0.22, keyElev: 12 } },
    };
    /**
     * FINALE recipe (Part One's last image): a long lens from behind, aligned so walkers just below the crest stand IN
     * FRONT of the low sun's disc (aligned for tod 0.9; good for 0.8-1). Use all three parts:
     *   applyShot(cam, shots.finale, t);  set.update(t, { ...myOpts, ...shots.finale.opts });
     *   st.look = { ...lookFor(...), ...shots.finale.post };          // ('look' is the camera target, hence 'post')
     * Walk the pair along pathAt(s) for s in shots.finale.walk ([crest-8, crest+6]): they top the crest dark against
     * the disc, then sink behind it. (Feet: groundAt; Jesus ~0.45 m left of the path, the Void ~0.9 m right.)
     */
    {
      // (sunShift -0.05: the sun a touch left, so the long lens clears the rose-gold tree and the bend's bushes)
      const SHIFT = -0.05, sF = crestS - 2.5, pm = pathAt(sF).pos, sunD = dirAzEl(SUN_AZ + SHIFT, lerp(6.2, 0.6, 0.9) * DEG);
      const body = V3(pm[0], pm[1] + 1.3, pm[2]);
      const D = 48, fov = 18, sy = 0.4;
      const cam = body.clone().addScaledVector(sunD, -D);
      const fh = 2 * D * Math.tan(fov * DEG / 2);
      const aim = body.clone().add(V3(0, (sy - 0.5) * fh, 0));       // pair + sun centred at screenY ≈ 0.4
      this.shots.finale = { pos: cam.toArray(), look: aim.toArray(), fov, drift: 0.15,
        opts: { tod: 0.9, silhouette: 1, sunShift: SHIFT, keyYaw: 0, keyElev: 5, seeds: 0.5, shadowAt: pm },
        post: { bloom: 0.18, bloomRadius: 0.3, bloomThreshold: 0.95 },
        walk: [crestS - 8, crestS + 6] };
    }
    this.groundAt = groundAt;
    this.pathAt = pathAt;
    this.SUN_AZ = SUN_AZ;
    this._c = { a: new THREE.Color(), b: new THREE.Color() };
    this.update(0, {});
  }

  /**
   * update(t, opts)
   *   tod 0..1        0 golden dusk -> 1 deep sunset (sun lower/redder, sky deeper, more stars). Animate it with k().
   *   voidSky 0..1    the Void's presence: the sky region around/above voidPos (as seen from the camera) darkens to
   *                   indigo with stars and a faint violet fringe; lights cool very slightly.
   *   voidPos [x,y,z] where the Void stands (feet). Default [0,0,0].
   *   voidRadius      angular radius of the bleed in degrees (default 34). voidLift: m above voidPos (default 2.0)
   *   seeds           thought-seed density multiplier (default 1 = ~70 seeds in the volume; 0 = none). motes follow it.
   *   seedGlow        seed brightness mult (default 1)
   *   keyYaw          key azimuth offset from the sun (rad, default -0.62: back-left rim key). keyElev (deg) overrides.
   *   fillMul, keyMul, hemiMul   light intensity multipliers (default 1)
   *   eyeKey 0..1     EYE_LIGHT direction: 0 = the sun key (default 0.35 blend toward the front fill so eyes keep life)
   *   shadowAt [x,y,z] centre of the shadow frustum (default origin; move it with walking characters)
   *   haze            haze density multiplier (default 1). glow: multiplier for tree/bush glow (default 1)
   *   sunShift        per-shot cheat: nudge the sun azimuth (rad, ±0.15 max, stays in the ridge gap) — e.g. so the
   *                   disc never sits right behind Jesus's head (it would read as a halo)
   *   sunGlow         sun disc/glow multiplier (default 1; ~0.5 calms close-ups with the sun behind a face)
   *   clear           [[x, z, r], ...] hide the little flowers inside these circles (under a seated / fallen character)
   *   silhouette 0..1 shots INTO the sun with dark figures (finale): key x0.5, fill x0.1, hemi x0.4, fog off; pair it
   *                   with shots.finale.post (low, tight bloom) — see shots.finale
   *   heroTreeGlow    0..1 glow / rim / lantern multiplier of the rose-gold tree (default 1; ~0.3 for close-ups)
   *   hideHeroTree    true: remove the rose-gold tree for this shot
   */
  update(t, o = {}) {
    const tod = clamp(o.tod ?? 0), vs = clamp(o.voidSky ?? 0);
    const P0 = PAL[0], P1 = PAL[1];
    const L = (k) => lerp(P0[k], P1[k], tod);
    const C = (k, out) => lerpC(P0[k], P1[k], tod, out);
    // --- sun + sky
    const sunEl = lerp(6.2, 0.6, tod) * DEG;
    const sunAz = SUN_AZ + clamp(o.sunShift ?? 0, -0.15, 0.15);
    const sg = o.sunGlow ?? 1;
    U.uESunDir.value.copy(dirAzEl(sunAz, sunEl));
    C('sun', U.uESunCol.value);
    C('horS', U.uEHorS.value); C('horA', U.uEHorA.value); C('lowS', U.uELowS.value); C('lowA', U.uELowA.value);
    C('mid', U.uEMid.value); C('high', U.uEHigh.value); C('zen', U.uEZen.value); C('belt', U.uEBelt.value); C('shadow', U.uEShadow.value);
    U.uEGTint.value.set(...P0.gTint.map((v, i) => lerp(v, P1.gTint[i], tod))); U.uEGSat.value = L('gSat');
    U.uEGDusk.value = Math.max(0.6 * clamp(o.silhouette ?? 0), 0.18 * smoothstep(0.5, 1, tod));
    U.uEGlow.value = L('glow') * lerp(1, sg, 0.6);
    U.uEHazeDen.value = L('haze') * (o.haze ?? 1);
    const sl = this.sky.userData.L;
    sl.uEStars.value = lerp(0.35, 1.0, tod);
    sl.uESunR.value = lerp(0.031, 0.035, tod);
    sl.uEDisc.value.set(...P0.disc.map((v, i) => lerp(v, P1.disc[i], tod) * sg));
    // --- void bleed
    const vp = o.voidPos || [0, 0, 0];
    U.uEVoid.value = vs;
    U.uEVoidPos.value.set(vp[0], (vp[1] ?? 0) + (o.voidLift ?? 2.0), vp[2]);
    U.uEVoidCos.value = Math.cos((o.voidRadius ?? 34) * DEG);
    // --- clouds (drift very slowly around the sky)
    this.clouds.rotation.y = -t * 0.0006;
    C('cShade', this.clouds.userData.L.uCShade.value); C('cLit', this.clouds.userData.L.uCLit.value);
    // --- lights
    const keyEl = (o.keyElev ?? lerp(28, 18, tod)) * DEG;
    const keyDir = dirAzEl(sunAz + (o.keyYaw ?? -0.62), keyEl);
    U.uEKeyDir.value.copy(keyDir);
    const sc = o.shadowAt || [0, 0, 0];
    this.key.target.position.set(sc[0], sc[1], sc[2]);
    { const far = Math.hypot(sc[0], sc[2]) > 6; this.terrain.userData.outer.receiveShadow = far; this.path.userData.outer.receiveShadow = far; }
    this.key.position.set(sc[0], sc[1], sc[2]).addScaledVector(keyDir, 40);
    C('key', this.key.color);
    const sil = clamp(o.silhouette ?? 0);
    this.key.intensity = L('keyI') * (1 - 0.12 * vs) * (o.keyMul ?? 1) * lerp(1, 0.5, sil);
    const fillDir = V3(0.5, 0.42, 0.76).normalize();
    this.fill.position.copy(fillDir).multiplyScalar(30); this.fill.target.position.set(0, 0, 0);
    C('fill', this.fill.color);
    this.fill.color.lerp(this._c.a.setRGB(0.78, 0.7, 1.0), 0.25 * vs);
    this.fill.intensity = L('fillI') * (o.fillMul ?? 1) * lerp(1, 0.1, sil);
    C('hemiS', this.hemi.color); C('hemiG', this.hemi.groundColor);
    this.hemi.color.lerp(this._c.a.setRGB(0.42, 0.4, 0.85), 0.3 * vs);
    this.hemi.intensity = L('hemiI') * (o.hemiMul ?? 1) * lerp(1, 0.4, sil);
    this.scene.fog.color.copy(U.uEHorA.value).lerp(U.uEHorS.value, 0.5);
    this.scene.fog.density = 0.0055 * (1 - sil);          // (fog would lift the silhouettes toward the bright horizon)
    // --- eyes: key light for all eyeball shaders
    const ek = clamp(o.eyeKey ?? 0.35);
    EYE_LIGHT.uKeyDir.value.copy(keyDir).lerp(fillDir, ek).normalize();
    EYE_LIGHT.uKeyColor.value.copy(this.key.color).lerp(this.fill.color, ek);
    EYE_LIGHT.uAmbient.value.copy(this.hemi.color).lerp(this.hemi.groundColor, 0.5).multiplyScalar(0.62);
    // --- ambient life
    const glow = o.glow ?? 1;
    for (const tr of this.trees) { const u = tr.userData; u.sway.rotation.z = u.amp * Math.sin(t * 0.45 + u.phase); u.sway.rotation.x = u.amp * 0.7 * Math.sin(t * 0.37 + u.phase * 1.3); }
    this.heroTree.visible = !o.hideHeroTree;
    this._setGlow(glow, clamp(o.heroTreeGlow ?? 1));
    // only props near the ±7 m shadow frustum cast (far trees / bushes stay out of the shadow pass)
    for (const tr of this.trees) { const on = Math.hypot(tr.position.x - sc[0], tr.position.z - sc[2]) < 9 + tr.userData.reach; for (const m of tr.userData.casters) m.castShadow = on; }
    for (const b of this.bushes) b.castShadow = Math.hypot(b.position.x - sc[0], b.position.z - sc[2]) < 9;
    this._clearFlowers(o.clear);
    const seeds = o.seeds ?? 1;
    this.seeds.update(t, seeds, (o.seedGlow ?? 1) * lerp(1.0, 1.15, tod));
    this.motes.begin();
    if (seeds > 0) {
      this.motes.stream({ t, seed: 31, t0: -40, t1: 1e6, rate: 3.2 * seeds, life: 11,
        origin: (tb) => { const r = rng(Math.floor(tb * 1000) + 17); return [lerp(-7, 7, r()), lerp(0.3, 3.2, r()), lerp(-9, 4, r())]; },
        vel: [0.05, 0.035, -0.02], spread: [0.04, 0.025, 0.04], size: [0.018, 0.04], color: [0xffe2a8, 0xffd0b0, 0xfff4d8],
        alpha: 0.55, fade: [0.25, 0.35], cell: CELL.dot, wobble: 0.12 });
    }
    this.motes.end();
    // --- post look
    this.look.exposure = L('exposure'); this.look.warm = L('warm');
    return this;
  }

  // opts.clear: [[x, z, radius], ...] -> hide the flowers inside those circles (where characters stand / sit / fall)
  _clearFlowers(clear) {
    const F = this.flowers.userData;
    const key = clear && clear.length ? JSON.stringify(clear) : '';
    if (key === F.clearKey) return;
    F.clearKey = key;
    const hm = F.heads.instanceMatrix.array, sm = F.stems.instanceMatrix.array, ga = F.aA.array;
    hm.set(F.base); sm.set(F.base); ga.set(F.baseA);
    if (key) F.items.forEach(([x, z], i) => {
      if (clear.some(([cx, cz, r]) => (x - cx) * (x - cx) + (z - cz) * (z - cz) < r * r)) {
        for (let k = 0; k < 16; k++) { if (k < 15 && k !== 12 && k !== 13 && k !== 14) hm[i * 16 + k] = sm[i * 16 + k] = 0; }
        ga[i] = 0;
      }
    });
    F.heads.instanceMatrix.needsUpdate = F.stems.instanceMatrix.needsUpdate = F.aA.needsUpdate = true;
  }

  _setGlow(g, hg = 1) {
    const key = g + '|' + hg;
    if (this._glow === key) return;
    this._glow = key;
    const set = (m) => { const u = m.userData.uniforms; if (!u) return; if (m.userData.baseGlow === undefined) m.userData.baseGlow = u.uGlow.value; u.uGlow.value = m.userData.baseGlow * g; };
    for (const b of this.bushes) set(b.material);
    for (const tr of this.trees) if (tr !== this.heroTree) tr.traverse((o) => { if (o.isMesh) set(o.material); });
    // the rose-gold hero tree: glow, rim and lanterns follow opts.heroTreeGlow (calm it in close-ups)
    const H = this.heroTree.userData, u = H.canopyMat.userData.uniforms;
    u.uGlow.value = H.base.glow * g * lerp(0.35, 1, hg); u.uRim.value = H.base.rim * lerp(0.3, 1, hg);
    H.fruitMat.color.copy(H.base.fruit).multiplyScalar(lerp(0.55, 1, hg) * g); H.fruits.visible = hg > 0.05;
  }
}

export async function create() { return new EdgeSet(); }
export const U_DBG = U;   // TEMP debug (edge lab)
