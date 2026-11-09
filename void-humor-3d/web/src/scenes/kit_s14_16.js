// Shared helpers for scenes s14 / s15 / s16 (EDGE, Part One: the block, the shrug, the walk into the sunset).
// Not a scene module (the registry only loads sNN.js). Pure helpers + small prop builders; every pose is f(t).
//   - re-exports the s11-s13 kit (word times W(), marks POS/YAW, two-pass solve(), pulse(), own()/stamp() leak guard)
//   - makeJesusPhone(): the small plain phone Jesus keeps in his sash (generic notification card, no logos)
//   - pathPose(set, s, side): a walker on the EDGE path s metres from pathStart (+ toward the sun), offset sideways
//   - lookRot(): a camera roll that keeps a prop upright in an insert
import * as THREE from 'three';
import { clamp, lerp, smooth } from '../core/util.js';
export { loadLines, W, POS, YAW, SW, SV, add, arr, own, stamp, drawSkyGalaxy, makeLittleGalaxy, solve, pulse, walkPath, dirPoint } from './kit_s11_13.js';

export const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
export const toV = (p) => (p && p.isVector3 ? p.clone() : Array.isArray(p) ? new THREE.Vector3(p[0], p[1], p[2]) : new THREE.Vector3());
/** 0 before a, eased 0 -> 1 over [a, b], 1 after */
export const ramp = (t, a, b, e = smooth) => (b <= a ? (t >= b ? 1 : 0) : e(clamp((t - a) / (b - a))));
/** sharp tap: 0 -> 1 -> 0 over d seconds starting at a (sin hump) */
export const bump = (t, a, d) => { const u = (t - a) / d; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; };
/** damped wobble after a (0 before) */
export const wob = (t, a, freq = 2.2, decay = 4) => (t <= a ? 0 : Math.sin((t - a) * freq * Math.PI * 2) * Math.exp(-(t - a) * decay));
/** blend flat face-param objects: [[face, w], ...] (weights need not sum to 1) */
export function fblend(list) {
  let ws = 0; const o = {};
  for (const [f, w] of list) { if (w <= 0) continue; ws += w; for (const k in f) if (typeof f[k] === 'number') o[k] = (o[k] ?? 0) + f[k] * w; }
  for (const k in o) o[k] /= Math.max(1e-6, ws);
  const first = list.find(([, w]) => w > 0) || list[0];
  for (const k in first[0]) if (typeof first[0][k] !== 'number') o[k] = first[0][k];
  return o;
}

// ------------------------------------------------------------------------------------------- the path
/** a walker on the EDGE path: s metres from pathStart (+ toward the sun), `side` metres to the walker's LEFT
 *  (negative = right). Returns { pos (world, feet on the ground), yaw (facing along the path toward the sun), dir }. */
export function pathPose(set, s, side = 0) {
  const a = set.pathAt(s - 0.6), b = set.pathAt(s + 0.6), c = set.pathAt(s);
  const dx = b.pos[0] - a.pos[0], dz = b.pos[2] - a.pos[2], l = Math.hypot(dx, dz) || 1;
  const d = [dx / l, 0, dz / l];
  const yaw = Math.atan2(d[0], d[2]);
  const left = [Math.cos(yaw), 0, -Math.sin(yaw)];
  const x = c.pos[0] + left[0] * side, z = c.pos[2] + left[2] * side;
  return { pos: [x, set.groundAt(x, z), z], yaw, dir: d, left };
}
/** path s (metres from pathStart) of the path point closest to a world point (coarse search; call in setup) */
export function pathS(set, p, lo = -20, hi = 60) {
  let best = 1e9, bs = 0;
  for (let s = lo; s <= hi; s += 0.05) { const q = set.pathAt(s).pos; const d = (q[0] - p[0]) ** 2 + (q[2] - p[2]) ** 2; if (d < best) { best = d; bs = s; } }
  return bs;
}
/** walking distance along a path with a smooth start/stop: trapezoid speed v (m/s), accel ta, decel td */
export function travel(t, t0, t1, v, ta = 0.5, td = 0.6) {
  if (t <= t0) return 0;
  const T = t1 - t0, tt = Math.min(t - t0, T), D = v * (T - (ta + td) / 2);
  if (tt < ta) return 0.5 * v * tt * tt / ta;
  if (tt <= T - td) return 0.5 * v * ta + v * (tt - ta);
  const e = T - tt;
  return D - 0.5 * v * e * e / td;
}

// ------------------------------------------------------------------------------------------- camera roll for inserts
/** roll (rad) for applyShot so that world direction `up` reads as screen-up from a camera at `pos` looking at `look` */
export function rollFor(pos, look, up) {
  const m = new THREE.Matrix4().lookAt(toV(pos), toV(look), V3(0, 1, 0));
  const inv = m.clone().invert();
  const u = toV(up).transformDirection(inv);
  return -Math.atan2(u.x, u.y);
}

// ------------------------------------------------------------------------------------------- Jesus's phone
function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function bubble(g, cx, cy, s, col) {   // the generic app icon: a plain white speech bubble
  g.fillStyle = col; g.beginPath(); g.ellipse(cx, cy, s, s * 0.78, 0, 0, 7); g.fill();
  g.beginPath(); g.moveTo(cx - s * 0.45, cy + s * 0.5); g.lineTo(cx - s * 0.62, cy + s * 1.02); g.lineTo(cx - s * 0.05, cy + s * 0.7); g.closePath(); g.fill();
}
function notifCanvas() {
  const W = 300, H = 640, c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  // a calm lock-screen gradient (dusky rose -> violet), clock
  const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#f2c6ae'); gr.addColorStop(0.5, '#c9a6d8'); gr.addColorStop(1, '#7d6fb3');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  g.fillStyle = 'rgba(255,255,255,0.92)'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = '300 64px sans-serif'; g.fillText('7:42', W / 2, 118);
  g.font = '18px sans-serif'; g.fillStyle = 'rgba(255,255,255,0.8)'; g.fillText('a lovely evening', W / 2, 166);
  // the notification card
  g.fillStyle = 'rgba(255,255,255,0.97)'; rr(g, 10, 236, W - 20, 178, 24); g.fill();
  g.fillStyle = '#5b8def'; rr(g, 26, 254, 50, 50, 13); g.fill();
  bubble(g, 51, 276, 16, '#ffffff');
  g.textAlign = 'left'; g.fillStyle = '#8a909c'; g.font = 'bold 16px sans-serif'; g.fillText('MESSAGES', 90, 272);
  g.textAlign = 'right'; g.font = '16px sans-serif'; g.fillText('now', W - 28, 272);
  g.textAlign = 'left'; g.fillStyle = '#141824'; g.font = 'bold 25px sans-serif'; g.fillText('@definitely_fine_lol', 26, 338);
  g.fillStyle = '#2a3040'; g.font = '25px sans-serif'; g.fillText('blocked you.', 26, 376);
  // a second, older card below (soft) so it reads as a real lock screen
  g.fillStyle = 'rgba(255,255,255,0.5)'; rr(g, 10, 426, W - 20, 70, 18); g.fill();
  g.fillStyle = 'rgba(40,46,60,0.3)'; rr(g, 28, 446, 150, 11, 5); g.fill(); rr(g, 28, 466, 210, 9, 4); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}
/**
 * The small plain phone Jesus keeps tucked in his sash. Returns { group, update(jesus, o) }:
 *   o.show 0..1 (visible), o.glow 0..1 (screen light), o.hand 'R'|'L', o.slide (m along the fingers), o.tilt (rad),
 *   o.up (world dir: the phone's top points that way — a real grip, the fingers across its back round the far edge)
 * The phone sits on the palm side of the hand (screen = palm normal, long axis = fingers), so a scene poses the arm
 * (palm toward his eyes, fingers up) and the phone follows exactly.
 */
export function makeJesusPhone() {
  const group = new THREE.Group(); group.name = 'jesusPhone';
  const PW = 0.064, PH = 0.132, PT = 0.009;
  const body = new THREE.Mesh(new THREE.BoxGeometry(PW, PH, PT, 2, 2, 1), new THREE.MeshStandardMaterial({ color: 0x3e4452, roughness: 0.5, metalness: 0.1 }));
  // round the box a little (pull the corner vertices in)
  { const p = body.geometry.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i); if (Math.abs(x) > PW * 0.49 && Math.abs(y) > PH * 0.49) { p.setX(i, x * 0.93); p.setY(i, y * 0.985); } } }
  const tex = notifCanvas();
  const scrMat = new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(1, 1, 1), toneMapped: true });
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(PW * 0.9, PH * 0.92), scrMat);
  screen.position.z = PT * 0.5 + 0.0006;
  group.add(body, screen);
  group.matrixAutoUpdate = false;
  const m = new THREE.Matrix4(), x = V3(), y = V3(), z = V3();
  return {
    group, screen, body, PW, PH,
    update(jesus, o = {}) {
      const show = o.show ?? 1;
      group.visible = show > 0.5;
      if (!group.visible) return null;
      const side = o.hand || 'R';
      const hr = jesus.arms[side].hand.root;
      hr.updateWorldMatrix(true, false);
      const e = hr.matrixWorld.elements;
      const fd = V3(e[4], e[5], e[6]).normalize();          // hand +Y = fingers
      const back = V3(e[8], e[9], e[10]).normalize();       // hand +Z = back of the hand (palm faces -Z)
      const pc = jesus.anchor(side === 'R' ? 'handR' : 'handL');
      // screen faces the palm-normal side; long axis along the fingers (tilted by o.tilt about the palm normal)
      z.copy(back).negate();
      y.copy(fd).addScaledVector(z, -fd.dot(z)).normalize();
      if (o.up) { const u = toV(o.up); y.copy(u).addScaledVector(z, -u.dot(z)).normalize(); }   // stand it upright (fingers across its back)
      if (o.tilt) y.applyAxisAngle(z, o.tilt);
      x.crossVectors(y, z).normalize();
      const c = pc.clone().addScaledVector(z, 0.013 + PT * 0.5).addScaledVector(y, o.slide ?? 0.026);
      m.makeBasis(x, y, z).setPosition(c);
      group.matrix.copy(m); group.matrixWorldNeedsUpdate = true;
      scrMat.color.setScalar(lerp(0.08, 0.8, clamp(o.glow ?? 1)));
      return { center: c, normal: z.clone(), up: y.clone() };
    },
  };
}

// ------------------------------------------------------------------------------------------- small glow sprite
let _gt = null;
export function glowTex() {
  if (_gt) return _gt;
  const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.35, 'rgba(255,255,255,0.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  _gt = new THREE.CanvasTexture(c); return _gt;
}
export function glowSprite(color = 0xffffff, size = 0.2) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex(), color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
  s.scale.setScalar(size); s.renderOrder = 7; return s;
}

// ------------------------------------------------------------------------------------------- aiming
/** a shot from `pos` that puts world point `target` at screen row `py` (px of 1280) on the vertical centre line */
export function aim(pos, target, py, fov, extra = {}) {
  const P = toV(pos), Tg = toV(target);
  const d = Tg.clone().sub(P), dist = d.length();
  const ang = ((py / 1280) - 0.5) * fov * Math.PI / 180;        // + = target below centre
  // rotate the view direction about the camera's horizontal axis so the target sits `ang` off-centre
  const right = V3().crossVectors(d, V3(0, 1, 0)).normalize();
  const dir = d.clone().normalize().applyAxisAngle(right, ang);
  return { pos: P.toArray(), look: P.clone().addScaledVector(dir, dist).toArray(), fov, drift: 0.15, ...extra };
}

/** like aim(), but also places the target at screen column `px` (px of 720) */
export function aimXY(pos, target, px, py, fov, extra = {}) {
  const P = toV(pos), Tg = toV(target);
  const d = Tg.clone().sub(P), dist = d.length();
  const hf = 2 * Math.atan(Math.tan((fov * Math.PI / 180) / 2) * 720 / 1280);
  const ax = ((px / 720) - 0.5) * hf, ay = ((py / 1280) - 0.5) * fov * Math.PI / 180;
  const dir = d.clone().normalize().applyAxisAngle(V3(0, 1, 0), ax);
  const right = V3().crossVectors(dir, V3(0, 1, 0)).normalize();
  dir.applyAxisAngle(right, ay);
  return { pos: P.toArray(), look: P.clone().addScaledVector(dir, dist).toArray(), fov, drift: 0.1, ...extra };
}

// ------------------------------------------------------------------------------------------- cheat a prop out of an insert
import { CTX } from '../core/context.js';
/**
 * Hide `obj` while the frame time CTX.t is inside any registered window [a, b) (absolute seconds). Pure (a getter on
 * `visible`, no per-frame state), so it never leaks into other scenes' frames. Windows from several scenes accumulate.
 * Used to cheat the USER's hoodie drawstrings out of the lens in the phone inserts (the camera sits at the chest).
 */
export function hideDuring(obj, wins) {
  const ud = obj.userData;
  if (!ud.hideWins) {
    ud.hideWins = [];
    let own = obj.visible;
    Object.defineProperty(obj, 'visible', {
      configurable: true,
      get() { const t = CTX.t; return own && !ud.hideWins.some(([a, b]) => t >= a && t < b); },
      set(v) { own = !!v; },
    });
  }
  for (const w of wins) if (!ud.hideWins.some(([a, b]) => a === w[0] && b === w[1])) ud.hideWins.push(w);
  return obj;
}
