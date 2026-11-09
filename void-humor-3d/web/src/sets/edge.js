// SET 'EDGE' — "The Edge of the Mind" (Part One). An original luminous dreamscape at golden dusk.
//
//   const set = await app.set('EDGE');      // { scene, update(t, opts), anchors, props, look, groundAt, pathAt, shots }
//   set.update(t, { tod: 0..1, voidSky: 0..1, voidPos: [x,y,z], seeds: 1 });
//
// Layout (metres, Y up, camera usually at +Z looking toward -Z):
//   - a flat soft-grass clearing (y = 0 exactly for r < 7.5 m) where the characters act,
//   - a pale winding PATH that comes from behind the camera (+Z), runs through the clearing (x ≈ -0.35 at z = 0)
//     and winds away over rolling pastel hills, climbs a gentle crest (~46 m out: anchors.pathFar) and then
//     reappears on the far hills, converging into a gap in the far ridge right under the low sun,
//   - a sky dome (gold -> peach -> lilac -> indigo zenith, belt-of-Venus pink on the anti-sun side), a huge soft
//     sun glow ~8° left of -Z, backlit billboard clouds, a few early stars, and an optional Void "cosmic bleed",
//   - glowing puff-trees and round luminous bushes to the sides (the column behind faces is kept calm),
//   - tiny glowing flowers in the grass, drifting dandelion-like thought seeds, faint golden motes.
// Everything is a pure function of (t, opts). No Math.random / Date.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
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
// control points (x, z): from behind the camera, through the clearing, over the crest, into the sun gap
const PATH_CTRL = [[5.0, 36], [2.8, 19], [1.0, 8.5], [-0.2, 2.4], [-0.5, -3], [-1.5, -9], [-1.6, -15.5], [-0.4, -22],
  [1.2, -29], [0.6, -37], [-1.0, -46], [-3.0, -56], [-3.8, -68], [-5.6, -86], [-9.0, -110], [-13.5, -140],
  [-19.5, -175], [-27.0, -215], [-35.0, -255], [-42.0, -298], [-46.0, -322]];
const PATH = (() => {
  const curve = new THREE.CatmullRomCurve3(PATH_CTRL.map(([x, z]) => V3(x, 0, z)), false, 'centripetal');
  const N = 1100;
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
// Exactly 0 in the clearing (r < 7.5 m). Rolling pastel hills beyond, a crest the path climbs (~46 m), far ridges
// with a gap under the sun. Large wavelengths only (no high-frequency bumps).
function heightRaw(x, z, dp) {
  const r = Math.hypot(x, z);
  if (r < 7.5) return 0;
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
  return m * h;
}
export function groundAt(x, z) { const r = Math.hypot(x, z); if (r < 7.5) return 0; return heightRaw(x, z, pathDist(x, z)[0]); }

// path query: s = metres along the path measured from anchors.pathStart (negative = back toward the camera side)
let S0 = 0; // set below (index-space offset of pathStart)
function pathAtIndex(fi) {
  const { X, Z, N } = PATH;
  fi = clamp(fi, 0, N);
  const i = Math.min(N - 1, Math.floor(fi)), u = fi - i;
  const x = lerp(X[i], X[i + 1], u), z = lerp(Z[i], Z[i + 1], u);
  const dx = X[i + 1] - X[i], dz = Z[i + 1] - Z[i], l = Math.hypot(dx, dz) || 1;
  return { pos: [x, groundAt(x, z), z], dir: [dx / l, 0, dz / l], yaw: Math.atan2(dx, dz) };
}
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
  uEVoid: { value: 0 }, uEVoidCos: { value: Math.cos(36 * DEG) }, uEVoidUp: { value: 0.32 },
  uEVoidPos: { value: V3(0, 3.2, 0) },
};
const SKY_PARS = /* glsl */`
uniform vec3 uESunDir, uESunCol, uEHorS, uEHorA, uELowS, uELowA, uEMid, uEHigh, uEZen, uEBelt, uEShadow, uEVoidPos;
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
  c += uEBelt * wa * exp(-pow((hp - 0.17) / 0.08, 2.0));
  c = mix(c, uEShadow, wa * 0.6 * exp(-pow(hp / 0.06, 2.0)));
  float dAz = acos(clamp(ca, -1.0, 1.0));
  float dEl = h - uESunDir.y;
  float broad = exp(-(dAz * dAz / 0.5 + dEl * dEl / 0.018));
  float ang = acos(clamp(dot(d, uESunDir), -1.0, 1.0));
  float mid = exp(-ang * ang / 0.03);
  c += uESunCol * uEGlow * (0.26 * broad + 0.3 * mid);
  return c;
}
vec3 eHaze(vec3 d){ return eSkyGrad(normalize(vec3(d.x, 0.022, d.z))); }
// the Void's cosmic bleed: a soft region of sky around (and above) the Void, as seen from the camera
float eVoidMask(vec3 d){
  if (uEVoid <= 0.001) return 0.0;
  vec3 vd = normalize(normalize(uEVoidPos - cameraPosition) + vec3(0.0, uEVoidUp, 0.0));
  float n = eNoise(d * 3.5 + vec3(0.0, uETime * 0.03, uETime * 0.02));
  float e = dot(d, vd) + (n - 0.5) * 0.14;
  float m = smoothstep(uEVoidCos - 0.16, uEVoidCos + 0.22, e);
  return m * uEVoid * smoothstep(-0.04, 0.16, d.y);
}
`;

/**
 * edgify(material, opts): inject the set's atmospheric haze (+ optional grass forward-scatter / sheen, flower sway)
 * into a built-in material (Lambert / Standard / Physical / Basic), chaining an existing core `enhance()` hook.
 */
function edgify(mat, { grass = false, sway = false, scatter = 0, sheen = 0, haze = 1, self = 0 } = {}) {
  const prev = mat.onBeforeCompile;
  const enhanced = !!mat.userData.uniforms;
  const L = { uEScatter: { value: scatter }, uESheen: { value: sheen }, uEHazeMul: { value: haze }, uESelf: { value: self } };
  mat.userData.edge = L;
  mat.onBeforeCompile = (sh, r) => {
    if (enhanced) prev.call(mat, sh, r);
    Object.assign(sh.uniforms, U, L);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vEW;\nuniform float uETime;')
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
        }`);
    let fs = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vEW;\nuniform float uEScatter, uESheen, uEHazeMul, uESelf;\n' + SKY_PARS)
      .replace('#include <fog_fragment>', `{
          vec3 edv = vEW - cameraPosition; float edist = length(edv); vec3 ed = edv / max(edist, 1e-3);
          float eden = uEHazeDen * (0.55 + 0.45 * exp(-max(vEW.y, 0.0) * 0.04));
          float ehz = 1.0 - exp(-pow(edist * eden, 1.3));
          gl_FragColor.rgb = mix(gl_FragColor.rgb, eHaze(ed), clamp(ehz * uEHazeMax * uEHazeMul, 0.0, 1.0));
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
  mat.customProgramCacheKey = () => 'edge|' + (enhanced ? 'E' : '') + (grass ? 'G' : '') + (sway ? 'S' : '') + mat.type;
  return mat;
}

// ------------------------------------------------------------------------------------------- palettes (tod 0 / tod 1)
const PAL = [
  { horS: 0xffcf96, horA: 0xeab2b0, lowS: 0xf7b294, lowA: 0xe4a4bc, mid: 0xd29ac4, high: 0x968ac8, zen: 0x4a4896,
    belt: 0x3a1c24, shadow: 0xa89cd0, sun: 0xffae5c, glow: 0.95, disc: [4.2, 3.0, 1.55],
    key: 0xffd9a8, keyI: 2.6, fill: 0xffe2d2, fillI: 2.0, hemiS: 0xb8bcff, hemiG: 0xe8b4a8, hemiI: 1.0,
    cShade: 0xb092c4, cLit: 0xffc8b0, haze: 0.0042, exposure: 1.0, warm: 0.06 },
  { horS: 0xff9a58, horA: 0xd598ae, lowS: 0xf68a7c, lowA: 0xb889b8, mid: 0xa476b6, high: 0x5f4da0, zen: 0x1d1b50,
    belt: 0x40182c, shadow: 0x8576b0, sun: 0xff7e44, glow: 1.12, disc: [4.4, 2.0, 0.75],
    key: 0xffa070, keyI: 2.1, fill: 0xfac0c4, fillI: 1.65, hemiS: 0x8c86e0, hemiG: 0xc890a0, hemiI: 0.9,
    cShade: 0x76609c, cLit: 0xff9a80, haze: 0.0048, exposure: 0.97, warm: 0.12 },
].map((p) => {
  const o = {};
  for (const k in p) o[k] = (typeof p[k] === 'number' && k !== 'glow' && !/I$/.test(k) && k !== 'haze' && k !== 'exposure' && k !== 'warm') ? col(p[k]) : p[k];
  return o;
});

// ------------------------------------------------------------------------------------------- terrain
function buildTerrain() {
  const radii = [0];
  { let r = 0; while (r < TERRAIN_R) { r += Math.max(0.55, r * 0.042); radii.push(Math.min(r, TERRAIN_R)); } }
  const NA = 240;
  const nV = 1 + (radii.length - 1) * NA;
  const pos = new Float32Array(nV * 3), colA = new Float32Array(nV * 3);
  const C = { mint: col(0x84d8b0), peach: col(0xf6b896), lilac: col(0xb6a0ee), rose: col(0xf0a0c0), cream: col(0xf0d4b6),
    sage: col(0x96d6ae), far: col(0xc4a2d8) };
  const tmp = new THREE.Color();
  const setV = (i, x, z) => {
    const [dp] = pathDist(x, z);
    const y = heightRaw(x, z, dp);
    pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z;
    const r = Math.hypot(x, z);
    // pastel patchwork (very low frequency)
    const n1 = fbm2(x / 52 + 11, z / 52 - 3, 21), n2 = fbm2(x / 43 - 5, z / 43 + 8, 33), n3 = fbm2(x / 61 + 2, z / 61 + 19, 45);
    tmp.copy(C.peach).lerp(C.mint, smoothstep(-0.25, 0.2, n1));
    tmp.lerp(C.lilac, smoothstep(-0.1, 0.3, n2) * 0.9);
    tmp.lerp(C.rose, smoothstep(0.15, 0.5, n3) * 0.5);
    // the clearing: a calm soft sage-peach
    const calm = 1 - smoothstep(7, 18, r);
    const cn = vn2(x / 7, z / 7, 5), cn2 = vn2(x / 5.5 + 3, z / 5.5 - 1, 6);
    tmp.lerp(C.sage.clone().lerp(C.lilac, 0.22 * smoothstep(0.1, 0.7, cn)).lerp(C.peach, 0.18 * smoothstep(0.1, 0.7, cn2)), calm * 0.85);
    // far hills drift toward a lilac-rose
    tmp.lerp(C.far, smoothstep(90, 260, r) * 0.45);
    // worn, paler grass along the path edges
    tmp.lerp(C.cream, Math.exp(-Math.pow(dp / 1.4, 2)) * 0.25 * (1 - smoothstep(150, 300, r)));
    // gentle tonal variation (2-4 m), crests a touch lighter
    const k = 1 + 0.035 * fbm2(x / 3.2, z / 3.2, 77) + 0.012 * clamp(y, -3, 6);
    colA[i * 3] = tmp.r * k; colA[i * 3 + 1] = tmp.g * k; colA[i * 3 + 2] = tmp.b * k;
  };
  setV(0, 0, 0);
  for (let j = 1; j < radii.length; j++) {
    const r = radii[j];
    for (let a = 0; a < NA; a++) {
      const th = (a / NA) * TAU + (j % 2) * (Math.PI / NA);
      setV(1 + (j - 1) * NA + a, Math.sin(th) * r, -Math.cos(th) * r);
    }
  }
  const idx = [];
  for (let a = 0; a < NA; a++) idx.push(0, 1 + ((a + 1) % NA), 1 + a);
  for (let j = 1; j < radii.length - 1; j++) {
    const b0 = 1 + (j - 1) * NA, b1 = 1 + j * NA;
    for (let a = 0; a < NA; a++) {
      const a1 = (a + 1) % NA;
      idx.push(b0 + a, b0 + a1, b1 + a); idx.push(b0 + a1, b1 + a1, b1 + a);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(colA, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  // winding check: normals must point up
  if (g.attributes.normal.array[1] < 0) { const n = g.attributes.normal.array; for (let i = 0; i < n.length; i++) n[i] = -n[i]; g.index.array.reverse(); }
  const mat = edgify(new THREE.MeshLambertMaterial({ vertexColors: true }), { grass: true, scatter: 0.22, sheen: 0.06, self: 0.16 });
  const mesh = new THREE.Mesh(g, mat);
  mesh.receiveShadow = true;
  mesh.name = 'edge.terrain';
  return mesh;
}

// ------------------------------------------------------------------------------------------- path ribbon
function buildPath() {
  const { X, Z, N } = PATH;
  const ACROSS = [-1, -0.55, 0, 0.55, 1], AL = [0, 0.82, 1, 0.82, 0];
  const pos = [], colA = [], idx = [];
  const cC = col(0xf6e2c8), cE = col(0xeac8a6);
  const i0 = 0, step = 1;
  let rows = 0;
  for (let i = i0; i <= N; i += step) {
    const x = X[i], z = Z[i];
    const ip = Math.min(N, i + 1), im = Math.max(0, i - 1);
    let tx = X[ip] - X[im], tz = Z[ip] - Z[im]; const tl = Math.hypot(tx, tz) || 1; tx /= tl; tz /= tl;
    const nx = -tz, nz = tx;
    const r = Math.hypot(x, z);
    const w = (0.78 + 0.07 * noise1(i * 0.021, 3) + 0.06 * Math.sin(i * 0.013)) * lerp(1.0, 1.9, smoothstep(40, 220, r));
    const endFade = 1 - smoothstep(N - 70, N, i);
    const lift = 0.012 + r * 0.0007;
    for (let k = 0; k < ACROSS.length; k++) {
      const px = x + nx * w * ACROSS[k], pz = z + nz * w * ACROSS[k];
      pos.push(px, groundAt(px, pz) + lift, pz);
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
  const mat = edgify(new THREE.MeshLambertMaterial({ vertexColors: true, transparent: true, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 }), { grass: true, scatter: 0.32, sheen: 0.04, self: 0.08 });
  const mesh = new THREE.Mesh(g, mat);
  mesh.receiveShadow = true; mesh.renderOrder = -10; mesh.name = 'edge.path';
  return mesh;
}

// ------------------------------------------------------------------------------------------- sky
const SKY_FS = /* glsl */`
varying vec3 vW;
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
  vec3 c = eSkyGrad(d);
  float ang = acos(clamp(dot(d, uESunDir), -1.0, 1.0));
  c += uESunCol * uEGlow * 0.7 * exp(-ang * ang / 0.0032);
  // a warm glowing line hugging the horizon under the sun
  vec2 dh = normalize(d.xz + vec2(1e-6, 0.0));
  float dAz = acos(clamp(dot(dh, normalize(uESunDir.xz)), -1.0, 1.0));
  c += uESunCol * uEGlow * 0.3 * exp(-pow(max(d.y, 0.0) / 0.018, 2.0)) * exp(-dAz * dAz / 0.12);
  float disc = smoothstep(uESunR + 0.011, uESunR - 0.004, ang);
  c = mix(c, uEDisc, disc);
  float vm = eVoidMask(d);
  if (vm > 0.0) {
    float n2 = eNoise(d * 7.0 - vec3(uETime * 0.015));
    float n3 = eNoise(d * 2.2 + vec3(5.0, uETime * 0.01, 0.0));
    vec3 deep = mix(vec3(0.018, 0.016, 0.07), vec3(0.05, 0.026, 0.11), n2);
    deep += vec3(0.20, 0.08, 0.36) * 0.35 * smoothstep(0.45, 0.85, n3);
    deep += vec3(0.03, 0.18, 0.22) * 0.22 * smoothstep(0.55, 0.9, n2);
    c = mix(c, deep, vm * 0.93);
    c += vec3(0.40, 0.22, 0.85) * 0.10 * vm * (1.0 - vm) * 4.0;
  }
  float sh = smoothstep(0.26, 0.8, d.y);
  float dens = uEStars * 0.016 * sh + vm * 0.05;
  float st = eStar(d, dens) * (uEStars * 1.1 * sh + vm * 1.6);
  c += vec3(0.95, 0.93, 1.0) * st * 1.8;
  gl_FragColor = vec4(c, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function buildSky() {
  const L = { uEStars: { value: 0.4 }, uESunR: { value: 0.040 }, uEDisc: { value: V3(7, 5, 2.9) } };
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...U, ...L }, side: THREE.BackSide, depthWrite: false, fog: false,
    vertexShader: 'varying vec3 vW; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
    fragmentShader: SKY_FS,
  });
  const m = new THREE.Mesh(new THREE.SphereGeometry(SKY_R, 48, 24), mat);
  m.renderOrder = -1000; m.frustumCulled = false; m.name = 'edge.sky';
  m.userData.L = L;
  return m;
}

// ------------------------------------------------------------------------------------------- clouds
// A 2x2 atlas of soft procedural cloud shapes. R = coverage, G = thin edges (silver lining), B = underside light.
function cloudAtlas() {
  const W = 512, H = 256, CW = 256, CH = 128;
  const data = new Uint8Array(W * H * 4);
  const types = ['cumulus', 'cumulus', 'bank', 'streak'];
  const D = new Float32Array(CW * CH);
  for (let v = 0; v < 4; v++) {
    const ox = (v % 2) * CW, oy = Math.floor(v / 2) * CH;
    const R = rng(1000 + v * 37);
    const blobs = [];
    const type = types[v];
    if (type === 'cumulus') {
      const nb = 12;
      for (let i = 0; i < nb; i++) {
        const u = (i + 0.5) / nb, big = Math.pow(Math.sin(u * Math.PI), 0.8);
        const rr = 0.05 + 0.1 * big * (0.6 + 0.6 * R());
        blobs.push([0.08 + 0.84 * u + (R() - 0.5) * 0.05, 0.22 + rr * 0.9 + (R() - 0.3) * 0.12 * big, rr * 1.1, rr]);
      }
      for (let i = 0; i < 7; i++) { const u = 0.22 + 0.56 * R(); const rr = 0.05 + 0.05 * R(); blobs.push([u, 0.42 + 0.3 * R() * Math.sin(u * Math.PI), rr * 1.1, rr]); }
    } else if (type === 'bank') {
      for (let i = 0; i < 18; i++) { const u = (i + 0.5) / 18; const rr = 0.04 + 0.07 * Math.sin(u * Math.PI) * (0.5 + 0.7 * R()); blobs.push([0.04 + 0.92 * u, 0.28 + rr * 0.9, rr * 1.5, rr]); }
    } else {
      for (let i = 0; i < 14; i++) { const u = (i + 0.5) / 14; const rr = 0.03 + 0.035 * Math.sin(u * Math.PI) * (0.5 + 0.7 * R()); blobs.push([0.03 + 0.94 * u, 0.42 + 0.1 * Math.sin(u * 5 + 1) + (R() - 0.5) * 0.06, rr * 3.0, rr]); }
    }
    const bottom = type === 'streak' ? 0.0 : 0.2;
    for (let y = 0; y < CH; y++) for (let x = 0; x < CW; x++) {
      const px = x / (CW - 1), py = y / (CH - 1);
      let d = 0;
      for (const [cx, cy, rx, ry] of blobs) { const dx = (px - cx) / rx, dy = (py - cy) / (ry * 1.6); d += Math.exp(-(dx * dx + dy * dy) * 1.5); }
      d *= 0.75 + 0.5 * (0.5 + 0.5 * vn2(px * 14, py * 7, 70 + v)) * (0.8 + 0.4 * (0.5 + 0.5 * vn2(px * 30, py * 15, 90 + v)));
      if (type !== 'streak') d *= smoothstep(bottom - 0.05, bottom + 0.08, py);
      d *= smoothstep(0.0, 0.07, px) * smoothstep(1.0, 0.93, px) * smoothstep(0.0, 0.07, py) * smoothstep(1.0, 0.93, py);
      D[y * CW + x] = d;
    }
    for (let x = 0; x < CW; x++) {
      let acc = 0;                       // density accumulated below this pixel (light comes from the low sun, below)
      for (let y = 0; y < CH; y++) {
        const d = D[y * CW + x];
        let db = 0; for (let k = -5; k <= 5; k++) db += D[y * CW + clamp(x + k, 0, CW - 1)];
        db /= 11;
        const cov = smoothstep(0.3, 1.1, d);
        const thin = cov * (1 - smoothstep(0.35, 2.4, d));
        const lit = Math.exp(-acc * 0.03);
        acc += db;
        const i = ((oy + y) * W + ox + x) * 4;
        data[i] = Math.round(cov * 255); data[i + 1] = Math.round(thin * 255); data[i + 2] = Math.round(lit * 255); data[i + 3] = 255;
      }
    }
  }
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat, THREE.UnsignedByteType);
  tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearMipmapLinearFilter; tex.generateMipmaps = true;
  tex.needsUpdate = true;
  return tex;
}
const CLOUD_FS = /* glsl */`
varying vec2 vUv; varying vec3 vW; varying vec2 vCl;
uniform sampler2D uMap; uniform vec3 uCShade, uCLit; uniform float uCOpacity;
${SKY_PARS}
void main(){
  vec4 tx = texture2D(uMap, vUv);
  float a = tx.r * vCl.x * uCOpacity;
  if (a < 0.004) discard;
  vec3 d = normalize(vW - cameraPosition);
  float sp = max(dot(d, uESunDir), 0.0);
  float near = pow(sp, 14.0), side = pow(sp, 3.0);
  vec3 bg = eSkyGrad(d);
  // lit from below by the low sun (B = light reaching this point through the cloud); backlit near the sun
  vec3 body = mix(uCShade, uCLit, tx.b);
  body = mix(body, uCShade * 0.85, near * 0.55);
  vec3 c = mix(body, bg, 0.18);
  c += uESunCol * uEGlow * tx.g * (0.02 + 1.4 * near + 0.1 * side) * vCl.y;
  float vm = eVoidMask(d);
  c = mix(c, vec3(0.05, 0.035, 0.12), vm * 0.85);
  a *= 1.0 - vm * 0.6;
  gl_FragColor = vec4(c, a);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;
function buildClouds() {
  const R = rng(4242);
  const list = [];
  // [az (rad, relative to the sun), el (deg), width (m at dist), variant, opacity, rimBoost, dist]
  // low warm banks hugging the horizon on both sides of the sun gap
  list.push([-0.42, 2.6, 120, 2, 0.85, 1.0, 300], [0.36, 3.2, 105, 2, 0.8, 1.0, 305], [-0.95, 4.0, 90, 2, 0.75, 0.8, 300], [0.9, 3.0, 110, 2, 0.75, 0.8, 300]);
  // a thin streak crossing above the sun
  list.push([0.08, 11.5, 95, 3, 0.55, 1.2, 290]);
  // puffy cumulus around the sky (none directly over the sun)
  const cum = [[-0.62, 9, 70], [0.55, 13, 80], [-1.5, 15, 85], [1.4, 11, 80], [2.3, 8, 90], [-2.4, 12, 85], [3.0, 16, 90], [-0.25, 21, 60], [0.95, 26, 70]];
  for (const [a, e, w] of cum) list.push([a, e, w, R() < 0.5 ? 0 : 1, 0.82, 0.8, 285]);
  // high wisps
  const hi = [[-0.3, 36, 90], [0.6, 44, 100], [-1.1, 33, 80], [2.0, 40, 100], [-2.6, 38, 95], [1.3, 52, 110]];
  for (const [a, e, w] of hi) list.push([a, e, w, 3, 0.5, 0.6, 280]);
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
    const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
    for (const [sx, sy] of corners) {
      const p = c.clone().addScaledVector(right, sx * w / 2).addScaledVector(upv, sy * hgt / 2);
      pos.push(p.x, p.y, p.z);
      const ux = flip ? -sx : sx;
      uv.push(u0 + (ux * 0.5 + 0.5) * 0.5, v0 + (sy * 0.5 + 0.5) * 0.5);
      cl.push(op, rim);
    }
    const b = n * 4; idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('aCl', new THREE.Float32BufferAttribute(cl, 2));
  g.setIndex(idx);
  const L = { uMap: { value: cloudAtlas() }, uCShade: { value: new THREE.Color() }, uCLit: { value: new THREE.Color() }, uCOpacity: { value: 1 } };
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...U, ...L }, transparent: true, depthWrite: false, fog: false, side: THREE.DoubleSide,
    vertexShader: 'attribute vec2 aCl; varying vec2 vUv; varying vec3 vW; varying vec2 vCl; void main(){ vUv = uv; vCl = aCl; vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
    fragmentShader: CLOUD_FS,
  });
  const m = new THREE.Mesh(g, mat);
  m.renderOrder = -900; m.frustumCulled = false; m.name = 'edge.clouds';
  m.userData.L = L;
  return m;
}

// ------------------------------------------------------------------------------------------- trees + bushes
const HUES = {
  rose: [0xf7b6c8, 0xff8fb0], peach: [0xffcfa4, 0xffa070], mint: [0xb4f0d0, 0x60e0b0], lilac: [0xd2c0ff, 0xa688ff], gold: [0xffe2a0, 0xffc060],
};
function glowMat(hue, { glow = 0.3, rim = 1.0, wrap = 0.45 } = {}) {
  const [base, rimC] = HUES[hue];
  const m = new THREE.MeshStandardMaterial({ color: col(base), roughness: 0.75, metalness: 0, vertexColors: true });
  enhance(m, { rim, rimColor: rimC, rimPower: 2.4, glow, glowColor: base, wrap, wrapColor: rimC });
  return edgify(m);
}
function blobCluster(R, n, spread, rMin, rMax, flatY = 0.85) {
  const geos = [];
  for (let i = 0; i < n; i++) {
    const a = R() * TAU, d = Math.sqrt(R()) * spread;
    const rr = lerp(rMin, rMax, R());
    const g = new THREE.SphereGeometry(rr, 24, 16);
    g.scale(1, flatY, 1);
    g.translate(Math.cos(a) * d, rr * flatY * 0.75 + R() * spread * 0.35, Math.sin(a) * d);
    geos.push(g);
  }
  const g = mergeGeometries(geos);
  // vertex colour: darker toward the base, lighter on top (soft ambient occlusion)
  g.computeBoundingBox();
  const { min, max } = g.boundingBox;
  const p = g.attributes.position, c = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { const k = 0.62 + 0.38 * smoothstep(min.y, max.y, p.getY(i)); c[i * 3] = c[i * 3 + 1] = c[i * 3 + 2] = k; }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  return g;
}
function buildBush(x, z, s, hue, seed) {
  const R = rng(seed);
  const g = blobCluster(R, 4 + Math.floor(R() * 3), 0.55 * s, 0.32 * s, 0.62 * s);
  const m = new THREE.Mesh(g, glowMat(hue, { glow: 0.26, rim: 0.85 }));
  m.position.set(x, groundAt(x, z) - 0.06, z);
  m.rotation.y = R() * TAU;
  m.castShadow = true; m.receiveShadow = true;
  m.name = 'edge.bush';
  return m;
}
function buildTree(x, z, H, hue, seed) {
  const R = rng(seed);
  const k = H / 5;
  const grp = new THREE.Group();
  grp.position.set(x, groundAt(x, z) - 0.05, z);
  grp.rotation.y = R() * TAU;
  // trunk: a soft, slightly S-curved lathe with a flared foot
  const th = H * 0.56;
  const prof = [];
  for (let i = 0; i <= 14; i++) { const u = i / 14; prof.push(new THREE.Vector2((lerp(0.17, 0.085, Math.pow(u, 0.7)) + 0.16 * Math.exp(-u * 14)) * k, u * th)); }
  const tg = new THREE.LatheGeometry(prof, 16);
  const bend = (0.25 + 0.2 * R()) * k, ph = R() * 2;
  const tp = tg.attributes.position;
  for (let i = 0; i < tp.count; i++) { const u = tp.getY(i) / th; tp.setX(i, tp.getX(i) + bend * Math.sin(u * 2.4 + ph) * u); }
  tg.computeVertexNormals();
  const trunkMat = new THREE.MeshStandardMaterial({ color: col(0xf6e6ee), roughness: 0.7 });
  enhance(trunkMat, { rim: 0.55, rimColor: HUES[hue][1], rimPower: 2.4, glow: 0.14, wrap: 0.45, wrapColor: HUES[hue][1] });
  edgify(trunkMat);
  const trunk = new THREE.Mesh(tg, trunkMat); trunk.castShadow = true; grp.add(trunk);
  const top = V3(bend * Math.sin(2.4 + ph), th, 0);
  // canopy: a full, soft cluster of glowing puffs (wider than tall), with a faint light halo
  const cg = blobCluster(R, 8, 0.95 * k, 0.48 * k, 0.86 * k, 0.88);
  const canopy = new THREE.Mesh(cg, glowMat(hue, { glow: 0.34, rim: 1.1 }));
  canopy.position.copy(top).add(V3(0, -0.45 * k, 0)); canopy.castShadow = true;
  const sway = new THREE.Group(); sway.add(canopy); grp.add(sway);
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), color: col(HUES[hue][1]), transparent: true, opacity: 0.22,
    blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
  halo.scale.setScalar(4.6 * k); halo.position.copy(top).add(V3(0, 0.35 * k, 0)); sway.add(halo);
  // a few little lantern-fruits peeking under the canopy (HDR, they bloom)
  const fruitMat = edgify(new THREE.MeshBasicMaterial({ color: col(HUES[hue][1]).multiplyScalar(1.8) }));
  for (let i = 0; i < 5; i++) {
    const a = (i / 5 + R() * 0.1) * TAU, d = (0.55 + 0.35 * R()) * k;
    const f = new THREE.Mesh(new THREE.SphereGeometry(0.07 * k, 12, 8), fruitMat);
    f.position.copy(top).add(V3(Math.cos(a) * d, -0.35 * k - R() * 0.2 * k, Math.sin(a) * d));
    sway.add(f);
  }
  grp.userData = { sway, phase: R() * TAU, amp: 0.006 + 0.004 * R() };
  grp.name = 'edge.tree';
  return grp;
}

// ------------------------------------------------------------------------------------------- flowers
function buildFlowers() {
  const R = rng(777);
  const items = [];
  const avoid = (x, z) => { const r = Math.hypot(x, z); if (r < 2.6) return true; return pathDist(x, z)[0] < 1.15; };
  const hues = [0xffd66a, 0xff94c4, 0x84e4ff, 0xbc9cff, 0xffc890];
  for (let c = 0; c < 72; c++) {
    const a = R() * TAU, d = 3.0 + Math.pow(R(), 0.9) * 27;
    const cx = Math.sin(a) * d, cz = -Math.cos(a) * d;
    const n = 4 + Math.floor(R() * 8), hue = hues[Math.floor(R() * hues.length)];
    for (let i = 0; i < n; i++) {
      const x = cx + (R() - 0.5) * 2.4, z = cz + (R() - 0.5) * 2.4;
      if (avoid(x, z)) continue;
      items.push([x, z, 0.75 + 0.6 * R(), R() < 0.8 ? hue : hues[Math.floor(R() * hues.length)], R()]);
    }
  }
  const N = items.length;
  const stemG = new THREE.CylinderGeometry(0.0035, 0.005, 0.12, 4, 1); stemG.translate(0, 0.06, 0);
  const headG = new THREE.SphereGeometry(0.024, 10, 6); headG.scale(1, 0.6, 1); headG.translate(0, 0.125, 0);
  const stems = new THREE.InstancedMesh(stemG, edgify(new THREE.MeshLambertMaterial({ color: col(0x4c9a78) }), { sway: true }), N);
  const heads = new THREE.InstancedMesh(headG, edgify(new THREE.MeshBasicMaterial({ color: 0xffffff }), { sway: true }), N);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = V3(), p = V3(), c = new THREE.Color();
  items.forEach(([x, z, sc, hue, k], i) => {
    p.set(x, groundAt(x, z) - 0.01, z);
    q.setFromAxisAngle(V3(0, 1, 0), k * TAU);
    s.setScalar(sc);
    m4.compose(p, q, s);
    stems.setMatrixAt(i, m4); heads.setMatrixAt(i, m4);
    heads.setColorAt(i, c.set(hue).multiplyScalar(1.15 + 0.6 * k));
  });
  stems.instanceMatrix.needsUpdate = heads.instanceMatrix.needsUpdate = true;
  heads.instanceColor.needsUpdate = true;
  stems.receiveShadow = true;
  const grp = new THREE.Group(); grp.add(stems, heads); grp.name = 'edge.flowers';
  grp.userData = { heads, stems, count: N };
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
      this.P.push({ x: R(), y: R(), z: R(), sp: 0.7 + 0.6 * R(), ph: R() * TAU, f: 0.7 + 0.6 * R(), size: 0.09 + 0.07 * R(),
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
      this.aCol.array.set([p.tint.r * 1.5, p.tint.g * 1.5, p.tint.b * 1.5], k * 3);
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
      [15.5, -62, 6.4, 'rose'], [-24, -63, 7.2, 'peach'], [-31, -21, 6.2, 'lilac'], [27, -8, 5.8, 'mint'],
      [-10.5, 12.5, 4.8, 'lilac'], [12.5, 15.5, 5.2, 'gold'], [-22, 26, 6.0, 'rose'], [4, 30, 5.4, 'mint'],
    ].map(([x, z, H, hue], i) => buildTree(x, z, H, hue, 300 + i * 11));
    this.trees.forEach((t) => scene.add(t));
    this.bushes = [
      [-6.9, -5.5, 1.0, 'mint'], [7.4, -8.2, 1.2, 'lilac'], [-9.8, 4.2, 0.9, 'peach'], [8.8, 3.6, 1.0, 'rose'],
      [-5.6, -17, 0.8, 'lilac'], [6.2, -25, 0.9, 'mint'], [-12.5, -9.5, 1.1, 'rose'], [13.4, -11.5, 1.0, 'peach'],
      [3.6, 10.5, 0.8, 'mint'], [-4.6, 11.4, 0.9, 'lilac'], [-8.0, -14.8, 0.7, 'peach'], [11.6, -21.0, 0.8, 'rose'],
      [-16.5, -33.5, 1.2, 'peach'], [20, -35, 1.0, 'mint'],
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

    // path anchors: pathStart = closest path point to (0, 0, -1); pathFar = the crest (highest point 25..60 m out)
    { let best = 1e9, bi = 0; for (let i = 0; i <= PATH.N; i++) { const d = Math.hypot(PATH.X[i], PATH.Z[i] + 1); if (d < best) { best = d; bi = i; } } S0 = bi; }
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
      walkoff: { pos: [0.4, 1.9, 7.5], look: [-0.8, 1.4, -30], fov: 30, drift: 0.3 },
    };
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
   *   voidRadius      angular radius of the bleed in degrees (default 36). voidLift: m above voidPos (default 3.2)
   *   seeds           thought-seed density multiplier (default 1 = ~70 seeds in the volume; 0 = none). motes follow it.
   *   seedGlow        seed brightness mult (default 1)
   *   keyYaw          key azimuth offset from the sun (rad, default -0.62: back-left rim key). keyElev (deg) overrides.
   *   fillMul, keyMul, hemiMul   light intensity multipliers (default 1)
   *   eyeKey 0..1     EYE_LIGHT direction: 0 = the sun key (default 0.35 blend toward the front fill so eyes keep life)
   *   shadowAt [x,y,z] centre of the shadow frustum (default origin; move it with walking characters)
   *   haze            haze density multiplier (default 1). glow: multiplier for tree/bush/flower glow (default 1)
   */
  update(t, o = {}) {
    const tod = clamp(o.tod ?? 0), vs = clamp(o.voidSky ?? 0);
    const P0 = PAL[0], P1 = PAL[1];
    const L = (k) => lerp(P0[k], P1[k], tod);
    const C = (k, out) => lerpC(P0[k], P1[k], tod, out);
    // --- sun + sky
    const sunEl = lerp(6.2, 0.6, tod) * DEG;
    U.uESunDir.value.copy(dirAzEl(SUN_AZ, sunEl));
    C('sun', U.uESunCol.value);
    C('horS', U.uEHorS.value); C('horA', U.uEHorA.value); C('lowS', U.uELowS.value); C('lowA', U.uELowA.value);
    C('mid', U.uEMid.value); C('high', U.uEHigh.value); C('zen', U.uEZen.value); C('belt', U.uEBelt.value); C('shadow', U.uEShadow.value);
    U.uEGlow.value = L('glow');
    U.uEHazeDen.value = L('haze') * (o.haze ?? 1);
    const sl = this.sky.userData.L;
    sl.uEStars.value = lerp(0.35, 1.0, tod);
    sl.uESunR.value = lerp(0.031, 0.035, tod);
    sl.uEDisc.value.set(...P0.disc.map((v, i) => lerp(v, P1.disc[i], tod)));
    // --- void bleed
    const vp = o.voidPos || [0, 0, 0];
    U.uEVoid.value = vs;
    U.uEVoidPos.value.set(vp[0], (vp[1] ?? 0) + (o.voidLift ?? 3.2), vp[2]);
    U.uEVoidCos.value = Math.cos((o.voidRadius ?? 36) * DEG);
    // --- clouds (drift very slowly around the sky)
    this.clouds.rotation.y = -t * 0.0006;
    C('cShade', this.clouds.userData.L.uCShade.value); C('cLit', this.clouds.userData.L.uCLit.value);
    // --- lights
    const keyEl = (o.keyElev ?? lerp(28, 18, tod)) * DEG;
    const keyDir = dirAzEl(SUN_AZ + (o.keyYaw ?? -0.62), keyEl);
    const sc = o.shadowAt || [0, 0, 0];
    this.key.target.position.set(sc[0], sc[1], sc[2]);
    this.key.position.set(sc[0], sc[1], sc[2]).addScaledVector(keyDir, 40);
    C('key', this.key.color);
    this.key.intensity = L('keyI') * (1 - 0.12 * vs) * (o.keyMul ?? 1);
    const fillDir = V3(0.5, 0.42, 0.76).normalize();
    this.fill.position.copy(fillDir).multiplyScalar(30); this.fill.target.position.set(0, 0, 0);
    C('fill', this.fill.color);
    this.fill.color.lerp(this._c.a.setRGB(0.78, 0.7, 1.0), 0.25 * vs);
    this.fill.intensity = L('fillI') * (o.fillMul ?? 1);
    C('hemiS', this.hemi.color); C('hemiG', this.hemi.groundColor);
    this.hemi.color.lerp(this._c.a.setRGB(0.42, 0.4, 0.85), 0.3 * vs);
    this.hemi.intensity = L('hemiI') * (o.hemiMul ?? 1);
    this.scene.fog.color.copy(U.uEHorA.value).lerp(U.uEHorS.value, 0.5);
    // --- eyes: key light for all eyeball shaders
    const ek = clamp(o.eyeKey ?? 0.35);
    EYE_LIGHT.uKeyDir.value.copy(keyDir).lerp(fillDir, ek).normalize();
    EYE_LIGHT.uKeyColor.value.copy(this.key.color).lerp(this.fill.color, ek);
    EYE_LIGHT.uAmbient.value.copy(this.hemi.color).lerp(this.hemi.groundColor, 0.5).multiplyScalar(0.62);
    // --- ambient life
    const glow = o.glow ?? 1;
    for (const tr of this.trees) { const u = tr.userData; u.sway.rotation.z = u.amp * Math.sin(t * 0.45 + u.phase); u.sway.rotation.x = u.amp * 0.7 * Math.sin(t * 0.37 + u.phase * 1.3); }
    this._setGlow(glow);
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

  _setGlow(g) {
    if (this._glow === g) return;
    this._glow = g;
    const set = (m) => { const u = m.userData.uniforms; if (!u) return; if (m.userData.baseGlow === undefined) m.userData.baseGlow = u.uGlow.value; u.uGlow.value = m.userData.baseGlow * g; };
    for (const b of this.bushes) set(b.material);
    for (const tr of this.trees) tr.traverse((o) => { if (o.isMesh) set(o.material); });
  }
}

export async function create() { return new EdgeSet(); }
