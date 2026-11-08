// Deterministic billboard particles (stateless: every particle's state is a pure function of time).
//   const ps = new Particles({ max: 600, blending: 'add' | 'normal' }); scene.add(ps.mesh);
//   each frame: ps.begin(); ps.burst({...}) / ps.stream({...}) / ps.add(...); ps.end();
// Sprite cells (CELL.*): star (4-point sparkle), dot (soft round), galaxy (spiral), puff (soft cloud),
//   dust (tiny speck), ring, nebula (wispy blob), heart.
import * as THREE from 'three';
import { rng, clamp, lerp, smooth } from './util.js';

export const CELL = { star: 0, dot: 1, galaxy: 2, puff: 3, dust: 4, ring: 5, nebula: 6, heart: 7 };

let _atlas = null;
function atlas() {
  if (_atlas) return _atlas;
  const S = 128, c = document.createElement('canvas'); c.width = S * 4; c.height = S * 2;
  const g = c.getContext('2d');
  const cell = (i, fn) => { g.save(); g.translate((i % 4) * S + S / 2, Math.floor(i / 4) * S + S / 2); fn(); g.restore(); };
  const rad = (r0, stops) => { const gr = g.createRadialGradient(0, 0, 0, 0, 0, r0); stops.forEach(([o, a]) => gr.addColorStop(o, `rgba(255,255,255,${a})`)); return gr; };
  cell(0, () => { // star sparkle
    g.fillStyle = rad(60, [[0, 1], [0.12, 0.9], [0.3, 0.25], [1, 0]]); g.beginPath(); g.arc(0, 0, 60, 0, 7); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.95)';
    for (const r of [0, Math.PI / 2]) { g.save(); g.rotate(r); g.beginPath(); g.moveTo(-60, 0); g.quadraticCurveTo(0, 5, 60, 0); g.quadraticCurveTo(0, -5, -60, 0); g.fill(); g.restore(); }
  });
  cell(1, () => { g.fillStyle = rad(60, [[0, 1], [0.35, 0.7], [1, 0]]); g.beginPath(); g.arc(0, 0, 60, 0, 7); g.fill(); });
  cell(2, () => { // spiral galaxy
    g.fillStyle = rad(58, [[0, 0.9], [0.15, 0.6], [0.5, 0.12], [1, 0]]); g.beginPath(); g.arc(0, 0, 60, 0, 7); g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.75)'; g.lineCap = 'round';
    for (let arm = 0; arm < 2; arm++) {
      g.beginPath();
      for (let k = 0; k < 60; k++) { const a = arm * Math.PI + k * 0.11, r = 4 + k * 0.85; const x = Math.cos(a) * r, y = Math.sin(a) * r * 0.62; k ? g.lineTo(x, y) : g.moveTo(x, y); }
      g.lineWidth = 7; g.stroke();
    }
    g.fillStyle = 'rgba(255,255,255,1)'; g.beginPath(); g.ellipse(0, 0, 9, 6, 0, 0, 7); g.fill();
  });
  cell(3, () => { // puff
    const r = rng(5);
    for (let k = 0; k < 7; k++) { const x = (r() - 0.5) * 50, y = (r() - 0.5) * 30, rr = 25 + r() * 20; g.fillStyle = (() => { const gr = g.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); return gr; })(); g.beginPath(); g.arc(x, y, rr, 0, 7); g.fill(); }
  });
  cell(4, () => { g.fillStyle = rad(22, [[0, 1], [0.5, 0.5], [1, 0]]); g.beginPath(); g.arc(0, 0, 22, 0, 7); g.fill(); });
  cell(5, () => { g.strokeStyle = 'rgba(255,255,255,0.9)'; g.lineWidth = 8; g.beginPath(); g.arc(0, 0, 44, 0, 7); g.stroke(); });
  cell(6, () => { // nebula wisp
    const r = rng(11);
    for (let k = 0; k < 14; k++) { const a = r() * 6.28, d = r() * 34, x = Math.cos(a) * d, y = Math.sin(a) * d * 0.6, rr = 18 + r() * 26; const gr = g.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, 'rgba(255,255,255,0.32)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.beginPath(); g.arc(x, y, rr, 0, 7); g.fill(); }
  });
  cell(7, () => { g.fillStyle = 'rgba(255,255,255,0.95)'; g.beginPath(); g.moveTo(0, 30); g.bezierCurveTo(-60, -10, -25, -55, 0, -22); g.bezierCurveTo(25, -55, 60, -10, 0, 30); g.fill(); });
  _atlas = new THREE.CanvasTexture(c);
  _atlas.colorSpace = THREE.SRGBColorSpace;
  return _atlas;
}

const VS = /* glsl */`
attribute vec3 iPos; attribute vec4 iCol; attribute vec3 iMisc; // size, rot, cell
varying vec2 vUv; varying vec4 vCol;
void main(){
  vec4 mv = modelViewMatrix * vec4(iPos, 1.0);
  float c = cos(iMisc.y), s = sin(iMisc.y);
  vec2 q = vec2(c * position.x - s * position.y, s * position.x + c * position.y) * iMisc.x;
  mv.xy += q;
  gl_Position = projectionMatrix * mv;
  float cell = iMisc.z;
  vec2 o = vec2(mod(cell, 4.0), floor(cell / 4.0));
  vUv = (vec2(uv.x, 1.0 - uv.y) + o) / vec2(4.0, 2.0);
  vUv.y = 1.0 - vUv.y;
  vCol = iCol;
}`;
const FS = /* glsl */`
uniform sampler2D map; uniform float uIntensity;
varying vec2 vUv; varying vec4 vCol;
void main(){
  vec4 t = texture2D(map, vUv);
  gl_FragColor = vec4(vCol.rgb * uIntensity, t.a * vCol.a);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

export class Particles {
  constructor({ max = 500, blending = 'add', intensity = 1.6, depthTest = true, renderOrder = 5 } = {}) {
    this.max = max;
    const g = new THREE.InstancedBufferGeometry();
    const base = new THREE.PlaneGeometry(1, 1);
    g.index = base.index; g.attributes.position = base.attributes.position; g.attributes.uv = base.attributes.uv;
    this.aPos = new THREE.InstancedBufferAttribute(new Float32Array(max * 3), 3).setUsage(THREE.DynamicDrawUsage);
    this.aCol = new THREE.InstancedBufferAttribute(new Float32Array(max * 4), 4).setUsage(THREE.DynamicDrawUsage);
    this.aMisc = new THREE.InstancedBufferAttribute(new Float32Array(max * 3), 3).setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('iPos', this.aPos); g.setAttribute('iCol', this.aCol); g.setAttribute('iMisc', this.aMisc);
    g.instanceCount = 0;
    this.mat = new THREE.ShaderMaterial({
      uniforms: { map: { value: atlas() }, uIntensity: { value: intensity } }, vertexShader: VS, fragmentShader: FS,
      transparent: true, depthWrite: false, depthTest,
      blending: blending === 'add' ? THREE.AdditiveBlending : THREE.NormalBlending,
    });
    this.mesh = new THREE.Mesh(g, this.mat);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = renderOrder;
    this.geo = g; this.n = 0;
  }
  begin() { this.n = 0; }
  add(pos, size, color, alpha = 1, rot = 0, cell = 0) {
    if (this.n >= this.max || alpha <= 0.002 || size <= 0) return;
    const i = this.n++;
    this.aPos.array.set([pos[0], pos[1], pos[2]], i * 3);
    const c = color instanceof THREE.Color ? color : new THREE.Color(color);
    this.aCol.array.set([c.r, c.g, c.b, clamp(alpha)], i * 4);
    this.aMisc.array.set([size, rot, cell], i * 3);
  }
  end() {
    this.geo.instanceCount = this.n;
    this.aPos.needsUpdate = this.aCol.needsUpdate = this.aMisc.needsUpdate = true;
  }

  /**
   * stream: particles born continuously between t0 and t1 at `rate` per second.
   * opts: t, seed, t0, t1, rate, life, origin [x,y,z] | fn(birthTime)->[x,y,z], vel [x,y,z], spread [x,y,z] (random
   * velocity range), gravity [x,y,z], drag (0..), size [min,max], grow (size multiplier at end of life), color(s)
   * (array -> random pick), alpha, fade [in,out] (fraction of life), cell, spin (rad/s range), wobble (amp)
   */
  stream(o) {
    const { t } = o;
    if (t < o.t0) return;
    const rate = o.rate ?? 10, life = o.life ?? 2;
    const first = Math.max(0, Math.floor((t - life - o.t0) * rate)), last = Math.floor((Math.min(t, o.t1) - o.t0) * rate);
    for (let i = first; i <= last; i++) {
      const r = rng((o.seed ?? 1) * 100003 + i * 7919);
      const tb = o.t0 + (i + r() * 0.9) / rate;
      if (tb > o.t1 || tb > t) continue;
      this._one(o, r, tb, t - tb, life * (0.75 + 0.5 * r()));
    }
  }

  /** burst: `count` particles all born around time `at` (jitter `jitter` s). */
  burst(o) {
    const { t } = o;
    const life = o.life ?? 2;
    for (let i = 0; i < (o.count ?? 20); i++) {
      const r = rng((o.seed ?? 1) * 50021 + i * 104729);
      const tb = o.at + r() * (o.jitter ?? 0);
      const L = life * (0.7 + 0.6 * r());
      if (t < tb || t > tb + L) continue;
      this._one(o, r, tb, t - tb, L);
    }
  }

  _one(o, r, tb, age, L) {
    const u = age / L;
    if (u < 0 || u > 1) { r(); return; }
    const org = typeof o.origin === 'function' ? o.origin(tb) : (o.origin || [0, 0, 0]);
    const sp = o.spread || [0, 0, 0], v0 = o.vel || [0, 0, 0], gr = o.gravity || [0, 0, 0];
    const vx = v0[0] + (r() - 0.5) * 2 * sp[0], vy = v0[1] + (r() - 0.5) * 2 * sp[1], vz = v0[2] + (r() - 0.5) * 2 * sp[2];
    const drag = o.drag ?? 0;
    const dt = drag > 0 ? (1 - Math.exp(-drag * age)) / drag : age;
    const wob = o.wobble ?? 0, ph = r() * 6.28;
    const x = org[0] + vx * dt + 0.5 * gr[0] * age * age + wob * Math.sin(age * 2.1 + ph);
    const y = org[1] + vy * dt + 0.5 * gr[1] * age * age;
    const z = org[2] + vz * dt + 0.5 * gr[2] * age * age + wob * Math.cos(age * 1.7 + ph);
    const [s0, s1] = o.size || [0.05, 0.1];
    const size = lerp(s0, s1, r()) * lerp(1, o.grow ?? 1, u);
    const cols = Array.isArray(o.color) ? o.color : [o.color ?? 0xffffff];
    const col = cols[Math.floor(r() * cols.length) % cols.length];
    const [fi, fo] = o.fade || [0.15, 0.35];
    const a = (o.alpha ?? 1) * smooth(u / Math.max(1e-3, fi)) * smooth((1 - u) / Math.max(1e-3, fo));
    const spin = (r() - 0.5) * 2 * (o.spin ?? 0);
    const tw = o.twinkle ? (0.65 + 0.35 * Math.sin(age * (5 + r() * 6) + ph)) : 1;
    this.add([x, y, z], size, col, a * tw, ph + spin * age, typeof o.cell === 'function' ? o.cell(r) : (o.cell ?? 0));
  }
}
