// Shared props: volumetric light shafts, dust, flames, oil lamps, jars, staff, stones.
import * as THREE from 'three';
import { rng, noise3 } from './util.js';
import { modelParts, loadTexture } from './assets.js';
import { addFogUniforms } from './sky.js';

// ---------- volumetric light shaft (additive, soft-edged box along a direction) ----------
const beamVert = `
varying vec3 vLocal;
varying vec3 vWorld;
void main() {
  vLocal = position;
  vec4 w = modelMatrix * vec4(position, 1.0);
  vWorld = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}`;
const beamFrag = `
uniform vec3 color;
uniform float intensity, time, softness, noiseAmt, fadeStart, fadeEnd;
varying vec3 vLocal;
varying vec3 vWorld;
float hash(vec3 p){ p = fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vnoise(vec3 x){ vec3 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z); }
void main() {
  // local box: x,y in [-0.5,0.5] across the beam, z in [0,1] along it (0 = source)
  float ex = 1.0 - smoothstep(0.5 - softness, 0.5, abs(vLocal.x));
  float ey = 1.0 - smoothstep(0.5 - softness, 0.5, abs(vLocal.y));
  float along = smoothstep(0.0, fadeStart, vLocal.z) * (1.0 - smoothstep(fadeEnd, 1.0, vLocal.z));
  float n = mix(1.0, 0.55 + 0.9 * vnoise(vWorld * 0.6 + vec3(0.0, time * 0.05, time * 0.03)), noiseAmt);
  float a = ex * ey * along * n * intensity;
  gl_FragColor = vec4(color * a, 1.0);
}`;
export function lightBeam({ from, to, width = 2, height = 2, color = 0xffd8a0, intensity = 0.25, softness = 0.35, noise = 0.6, fadeStart = 0.15, fadeEnd = 0.75, up = new THREE.Vector3(0, 1, 0) }) {
  const geo = new THREE.BoxGeometry(1, 1, 1, 1, 1, 1).translate(0, 0, 0.5);
  const mat = new THREE.ShaderMaterial({
    uniforms: { color: { value: new THREE.Color(color) }, intensity: { value: intensity }, time: { value: 0 }, softness: { value: softness }, noiseAmt: { value: noise }, fadeStart: { value: fadeStart }, fadeEnd: { value: fadeEnd } },
    vertexShader: beamVert, fragmentShader: beamFrag, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false,
  });
  const m = new THREE.Mesh(geo, mat);
  const a = from.clone(), b = to.clone();
  const len = a.distanceTo(b);
  m.position.copy(a);
  m.up.copy(up);
  m.lookAt(b);
  m.scale.set(width, height, len);
  m.renderOrder = 5;
  m.userData.uniforms = mat.uniforms;
  return m;
}

// ---------- floating dust motes ----------
export function dustField({ count = 1500, box = [[-5, 0, -5], [5, 4, 5]], size = 0.025, color = 0xfff0d0, opacity = 0.7, seed = 4, inside = null }) {
  const r = rng(seed);
  const pos = new Float32Array(count * 3), ph = new Float32Array(count);
  let n = 0, guard = 0;
  while (n < count && guard++ < count * 50) {
    const x = r.range(box[0][0], box[1][0]), y = r.range(box[0][1], box[1][1]), z = r.range(box[0][2], box[1][2]);
    if (inside && !inside(x, y, z)) continue;
    pos.set([x, y, z], n * 3); ph[n] = r() * 100; n++;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos.slice(0, n * 3), 3));
  geo.setAttribute('phase', new THREE.BufferAttribute(ph.slice(0, n), 1));
  const mat = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 }, size: { value: size }, color: { value: new THREE.Color(color) }, opacity: { value: opacity } },
    vertexShader: `
      uniform float time, size; attribute float phase; varying float vA;
      void main(){
        vec3 p = position + vec3(sin(time*0.21+phase)*0.25, sin(time*0.13+phase*1.7)*0.18 + time*0.01, cos(time*0.17+phase*0.6)*0.25);
        vec4 mv = modelViewMatrix * vec4(p,1.0);
        gl_PointSize = clamp(size * 1280.0 / -mv.z, 1.0, 9.0);
        vA = 0.55 + 0.45 * sin(time*1.3 + phase*5.0);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      uniform vec3 color; uniform float opacity; varying float vA;
      void main(){ vec2 c = gl_PointCoord - 0.5; float d = length(c); float a = smoothstep(0.5, 0.0, d); gl_FragColor = vec4(color * a * opacity * vA, 1.0); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false,
  });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  pts.userData.uniforms = mat.uniforms;
  return pts;
}

// ---------- flame (billboard shader) + flickering point light ----------
const flameVert = `
varying vec2 vUv;
void main() {
  vUv = uv;
  vec4 mv = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0);
  vec2 scale = vec2(length(modelMatrix[0].xyz), length(modelMatrix[1].xyz));
  mv.xy += position.xy * scale;
  gl_Position = projectionMatrix * mv;
}`;
const flameFrag = `
uniform float time, seed, intensity;
varying vec2 vUv;
float hash(float n){ return fract(sin(n)*43758.5453); }
float noise(vec2 x){ vec2 i=floor(x), f=fract(x); f=f*f*(3.0-2.0*f); float n=i.x+i.y*57.0;
  return mix(mix(hash(n),hash(n+1.0),f.x),mix(hash(n+57.0),hash(n+58.0),f.x),f.y); }
void main() {
  vec2 p = vUv - vec2(0.5, 0.18);
  float t = time * 6.0 + seed * 10.0;
  float sway = (noise(vec2(t * 0.6, seed)) - 0.5) * 0.12 * (p.y + 0.2);
  p.x += sway;
  float h = clamp(p.y / 0.75, 0.0, 1.0);
  float w = max(mix(0.17, 0.0, pow(h, 0.85)) * (1.0 + 0.15 * (noise(vec2(t, p.y * 6.0)) - 0.5)), 0.004);
  float body = smoothstep(w, w * 0.25, abs(p.x)) * smoothstep(-0.15, 0.02, p.y) * (1.0 - smoothstep(0.55, 0.72, p.y));
  float core = smoothstep(w * 0.6, 0.0, abs(p.x)) * smoothstep(-0.08, 0.05, p.y) * (1.0 - smoothstep(0.15, 0.45, p.y));
  float blue = smoothstep(0.06, 0.0, abs(p.x)) * smoothstep(-0.12, -0.04, p.y) * (1.0 - smoothstep(-0.04, 0.03, p.y));
  vec3 col = vec3(1.0, 0.42, 0.08) * body * 2.2 + vec3(1.0, 0.85, 0.55) * core * 4.0 + vec3(0.2, 0.35, 1.0) * blue * 0.8;
  float glow = exp(-dot(p - vec2(0.0, 0.12), p - vec2(0.0, 0.12)) * 18.0) * 0.35;
  col += vec3(1.0, 0.55, 0.18) * glow;
  vec2 e = smoothstep(vec2(0.0), vec2(0.18), vUv) * smoothstep(vec2(0.0), vec2(0.18), 1.0 - vUv);
  gl_FragColor = vec4(col * intensity * e.x * e.y, 1.0);
}`;
export function flame({ size = 0.06, intensity = 1, seed = 1, light = true, lightIntensity = 1.2, lightDistance = 4, color = 0xff9a40, shadow = false }) {
  const g = new THREE.Group();
  const mat = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 }, seed: { value: seed }, intensity: { value: intensity } },
    vertexShader: flameVert, fragmentShader: flameFrag, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false,
  });
  const q = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
  q.scale.set(size, size * 2.0, 1);
  q.position.y = size * 0.75;
  q.renderOrder = 6;
  q.frustumCulled = false;
  g.add(q);
  let pl = null;
  if (light) {
    pl = new THREE.PointLight(color, lightIntensity, lightDistance, 2);
    pl.position.y = size * 0.9;
    if (shadow) { pl.castShadow = true; pl.shadow.mapSize.set(512, 512); pl.shadow.bias = -0.002; pl.shadow.radius = 4; }
    g.add(pl);
  }
  const base = lightIntensity;
  g.userData = {
    mat, light: pl,
    update(t) {
      mat.uniforms.time.value = t;
      if (pl) pl.intensity = base * (0.86 + 0.1 * Math.sin(t * 13.0 + seed * 3.0) + 0.06 * Math.sin(t * 23.7 + seed) + 0.05 * noise3(t * 3, seed, 0.5));
    },
  };
  return g;
}

// ---------- Herodian-style clay oil lamp ----------
let clayMat = null;
async function getClay() {
  if (clayMat) return clayMat;
  const diff = await loadTexture('/assets/models/planter_pot_clay/textures/planter_pot_clay_diff_1k.jpg', { srgb: true }).catch(() => null);
  clayMat = new THREE.MeshStandardMaterial({ color: diff ? 0xd8a080 : 0xa86a44, map: diff, roughness: 0.85 });
  return clayMat;
}
export async function oilLamp({ lit = true, seed = 1, flameSize = 0.05, lightIntensity = 0.9, lightDistance = 4, shadow = false } = {}) {
  const g = new THREE.Group();
  const mat = await getClay();
  const body = new THREE.LatheGeometry([
    new THREE.Vector2(0.0, 0.0), new THREE.Vector2(0.03, 0.0), new THREE.Vector2(0.045, 0.012), new THREE.Vector2(0.048, 0.022),
    new THREE.Vector2(0.04, 0.032), new THREE.Vector2(0.018, 0.036), new THREE.Vector2(0.012, 0.03), new THREE.Vector2(0.0, 0.03),
  ], 28);
  const bm = new THREE.Mesh(body, mat); bm.castShadow = true; bm.receiveShadow = true; g.add(bm);
  const nozzle = new THREE.CylinderGeometry(0.012, 0.016, 0.06, 14); nozzle.rotateZ(Math.PI / 2); nozzle.translate(0.055, 0.018, 0);
  const nm = new THREE.Mesh(nozzle, mat); nm.castShadow = true; g.add(nm);
  const handle = new THREE.TorusGeometry(0.013, 0.005, 6, 12, Math.PI); handle.rotateY(Math.PI / 2); handle.translate(-0.05, 0.026, 0);
  g.add(new THREE.Mesh(handle, mat));
  let fl = null;
  if (lit) {
    fl = flame({ size: flameSize, seed, lightIntensity, lightDistance, shadow });
    fl.position.set(0.085, 0.02, 0);
    g.add(fl);
  }
  g.userData = { flame: fl, update(t) { if (fl) fl.userData.update(t); } };
  return g;
}

// ---------- shepherd's staff ----------
export function staff({ height = 1.9, color = 0x5a3e28 } = {}) {
  const pts = [];
  for (let i = 0; i <= 20; i++) pts.push(new THREE.Vector3(0.01 * Math.sin(i * 0.7), (i / 20) * (height - 0.18), 0.006 * Math.cos(i * 0.9)));
  for (let i = 1; i <= 14; i++) { const a = (i / 14) * Math.PI * 1.15; pts.push(new THREE.Vector3(0.09 - 0.09 * Math.cos(a), height - 0.18 + 0.09 * Math.sin(a) + 0.02 * (i / 14), 0)); }
  const curve = new THREE.CatmullRomCurve3(pts);
  const geo = new THREE.TubeGeometry(curve, 80, 0.016, 8, false);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, roughness: 0.7 }));
  m.castShadow = true;
  return m;
}

// ---------- photoscanned stones (individual meshes from namaqualand_stones_01 / stone_01) ----------
export async function stoneSet() {
  const a = await modelParts('namaqualand_stones_01');
  return a;
}
export function placeStone(part, { size = 0.12, seed = 1 } = {}) {
  const r = rng(seed);
  const m = new THREE.Mesh(part.geometry, part.material);
  part.geometry.computeBoundingBox();
  const bb = part.geometry.boundingBox; const ext = Math.max(bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z);
  m.scale.setScalar(size / ext);
  m.rotation.set(r() * 6.28, r() * 6.28, r() * 6.28);
  m.castShadow = true; m.receiveShadow = true;
  const c = new THREE.Vector3(); bb.getCenter(c);
  m.position.copy(c).multiplyScalar(-size / ext);
  const g = new THREE.Group(); g.add(m);
  return g;
}

// ---------- stone water jar (Cana) ----------
export function stoneJar({ height = 0.75, seed = 1, mat }) {
  const r = rng(seed);
  const pts = [];
  const prof = [[0.0, 0.0], [0.17, 0.0], [0.2, 0.05], [0.215, 0.25], [0.205, 0.55], [0.18, 0.78], [0.15, 0.9], [0.16, 0.95], [0.16, 1.0], [0.13, 1.0], [0.13, 0.95]];
  for (const [x, y] of prof) pts.push(new THREE.Vector2(x * height * (1 + 0.04 * (r() - 0.5)), y * height));
  const geo = new THREE.LatheGeometry(pts, 40);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    const n = 1 + 0.03 * noise3(x * 6, y * 6, z * 6 + seed);
    pos.setXYZ(i, x * n, y, z * n);
  }
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true;
  return m;
}
