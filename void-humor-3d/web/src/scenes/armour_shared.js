// Shared helpers for s08 / s09 / s10 ("the armour goes on": crossed arms, 'Hell no', the eye-roll and the sulk).
// Not a scene module (the registry only loads sNN.js). Pure helpers: no state that depends on render order.
//   wordT('s08b01', 'scowls')        -> absolute time of a spoken word (data/lines.json Whisper times, beat-relative,
//                                      so re-timed audio re-times the picture); falls back to a beat fraction.
//   fitShot(points, fov, pos0, look0) -> a camera that puts world points on target pixels (deterministic solver).
//   gazeSched(t, keys)                -> saccade-style switching between gaze targets (fast ease, holds).
//   pulse(t, a, up, hold, down)       -> 0..1 envelope.
import * as THREE from 'three';
import { T, TL } from '../core/timeline.js';
import { clamp, smooth, lerp, ease } from '../core/util.js';
import { EDGE } from './marks.js';

export const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
export const toV = (p) => (p && p.isVector3 ? p.clone() : Array.isArray(p) ? new THREE.Vector3(p[0], p[1], p[2]) : new THREE.Vector3());

// ------------------------------------------------------------------------------------------------ word times
let WORDS = null;
export async function loadWords() {
  if (WORDS) return WORDS;
  try { const r = await fetch('/data/lines.json'); WORDS = r.ok ? await r.json() : {}; } catch (e) { WORDS = {}; }
  return WORDS;
}
const norm = (w) => String(w).toLowerCase().replace(/[^a-z']/g, '');
/**
 * Absolute time of `word` (n-th occurrence) in line `beat` (start or end). Beat-relative, so it moves with the beat.
 * fallback: fraction of the beat (0..1) used when lines.json has no word list.
 */
export function wordT(beat, word, { which = 'start', n = 0, fallback = 0.5, off = 0 } = {}) {
  const b = TL.data.beats[beat];
  const L = WORDS && WORDS[beat];
  if (L && L.words) {
    let c = 0;
    for (const w of L.words) if (norm(w.w) === norm(word)) { if (c++ === n) return b.start + (which === 'end' ? w.end : w.start) + off; }
  }
  return b.start + (b.end - b.start) * fallback + off;
}

// ------------------------------------------------------------------------------------------------ envelopes
/** 0 -> 1 (over up s, eased) -> hold -> 0 (over down s). a = start time (s). */
export function pulse(t, a, up = 0.1, hold = 0, down = 0.2, eIn = 'inOut', eOut = 'inOut') {
  if (t <= a) return 0;
  if (t < a + up) return ease[eIn]((t - a) / up);
  if (t < a + up + hold) return 1;
  if (t < a + up + hold + down) return 1 - ease[eOut]((t - a - up - hold) / down);
  return 0;
}
/** eased 0 -> 1 between absolute times a and b. */
export const ramp = (t, a, b, e = 'inOut') => (b <= a ? (t >= b ? 1 : 0) : ease[e](clamp((t - a) / (b - a))));
/** damped wobble after time a: amplitude 1 at a, freq Hz, decay 1/s (0 before a). */
export const wobble = (t, a, freq = 2.2, decay = 4) => (t <= a ? 0 : Math.sin((t - a) * freq * Math.PI * 2) * Math.exp(-(t - a) * decay));

// ------------------------------------------------------------------------------------------------ gaze schedule
/**
 * keys: [[timeRef, target (Vector3 | [x,y,z] | () => Vector3), dur?], ...]. Switches like a saccade: each change eases
 * over `dur` (default 0.09 s ≈ 2 frames) from the previous target, then holds. Returns a Vector3.
 */
export function gazeSched(t, keys) {
  const res = (g) => toV(typeof g === 'function' ? g() : g);
  let i = -1;
  for (let j = 0; j < keys.length; j++) if (T(keys[j][0]) <= t) i = j;
  if (i <= 0) return res(keys[0][1]);
  const d = keys[i][2] ?? 0.09;
  const u = smooth((t - T(keys[i][0])) / d);
  if (u >= 1) return res(keys[i][1]);
  return res(keys[i - 1][1]).lerp(res(keys[i][1]), u);
}

/**
 * Head yaw/pitch (rig convention: yaw + = toward the character's left, pitch + = chin down) that turn a character at
 * feet `pos` / facing `yaw` part of the way toward a world point: `fy`/`fp` = share of the eye-line angle the head
 * takes (the eyes do the rest), pitch clamped to [-up, down] so a look up at the Void never snaps the neck back.
 */
export function headAim(pos, yaw, target, { fy = 0.4, fp = 0.35, up = 0.2, down = 0.25, eyeH = 1.55 } = {}) {
  const d = toV(target).sub(new THREE.Vector3(pos[0], eyeH, pos[2]));
  const lx = d.x * Math.cos(yaw) - d.z * Math.sin(yaw), lz = d.x * Math.sin(yaw) + d.z * Math.cos(yaw);
  const hy = Math.atan2(lx, lz), hp = -Math.atan2(d.y, Math.hypot(lx, lz));
  return { yaw: fy * hy, pitch: clamp(fp * hp, -up, down) };
}

// ------------------------------------------------------------------------------------------------ camera fitter
/**
 * Find a camera (pos, look) for vertical fov so world points land on target pixels.
 * pts: [[Vector3|[x,y,z], px, py, weight?]]. pos0/look0: world guesses; posReg pulls pos toward pos0.
 * Deterministic coordinate descent (no randomness). Returns { pos, look, fov, drift, err }.
 */
export function fitShot(pts, fov, pos0, look0, { posReg = 0.02, free = [1, 1, 1], yMin = -99, yMax = 99, drift = 0.3 } = {}) {
  const cam = new THREE.PerspectiveCamera(fov, 720 / 1280, 0.05, 400);
  const P = [...toV(pos0).toArray(), ...toV(look0).toArray()];
  const PT = pts.map(([w, x, y, wt]) => [toV(w), x, y, wt ?? 1]);
  const p0 = toV(pos0);
  const cost = (q) => {
    cam.position.set(q[0], q[1], q[2]); cam.up.set(0, 1, 0); cam.lookAt(q[3], q[4], q[5]); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
    let e = 0;
    for (const [w, x, y, wt] of PT) {
      const v = w.clone().project(cam);
      if (v.z > 1) { e += 1e7; continue; }
      const sx = (v.x * 0.5 + 0.5) * 720, sy = (1 - (v.y * 0.5 + 0.5)) * 1280;
      e += wt * ((sx - x) ** 2 + (sy - y) ** 2);
    }
    e += posReg * 1e4 * ((q[0] - p0.x) ** 2 + (q[1] - p0.y) ** 2 + (q[2] - p0.z) ** 2);
    if (q[1] < yMin) e += 1e7 * (yMin - q[1]) ** 2;
    if (q[1] > yMax) e += 1e7 * (q[1] - yMax) ** 2;
    return e;
  };
  let best = cost(P), step = 0.5;
  for (let it = 0; it < 500 && step > 0.001; it++) {
    let improved = false;
    for (let i = 0; i < 6; i++) {
      if (i < 3 && !free[i]) continue;
      for (const d of [step, -step]) { const q = P.slice(); q[i] += d; const c = cost(q); if (c < best) { best = c; P.splice(0, 6, ...q); improved = true; } }
    }
    if (!improved) step *= 0.6;
  }
  return { pos: P.slice(0, 3), look: P.slice(3, 6), fov, drift, err: Math.sqrt(best / Math.max(1, PT.length)) };
}

/** Linear blend of two shots (u 0..1, eased by caller) — for pushes that keep both ends exact. */
export function mixShot(a, b, u) {
  const L = (x, y) => x.map((v, i) => v + (y[i] - v) * u);
  return { pos: L(a.pos, b.pos), look: L(a.look, b.look), fov: lerp(a.fov, b.fov, u), drift: lerp(a.drift ?? 0.3, b.drift ?? 0.3, u), roll: lerp(a.roll || 0, b.roll || 0, u) };
}

// ------------------------------------------------------------------------------------------------ staging
const M = EDGE.M;
export const W = (m) => EDGE.W(m.p);            // a mark's world position
export const WY = (m) => EDGE.Y(m.yaw);         // a mark's world yaw
/** world yaw for a character at world p0 to face world p1 */
export const faceYaw = (p0, p1) => Math.atan2(toV(p1).x - toV(p0).x, toV(p1).z - toV(p0).z);
/** Jesus's world yaw facing the user from a local stage point */
export const MARKS = M;

/** Jesus's position in s08: a polite little dodge (0.14 of the way to JM) as the Void's elbow swings out, then
 *  in s08b03 one step on to JM. Pure. u = step progress (0..1), d = dodge progress. */
export function jesusStep(t) {
  const a = T('s08b03') + 0.05, b = a + 0.95;
  const u = smooth(clamp((t - a) / (b - a)));
  const dodge0 = T('s08b01') + 0.55;
  const d = smooth(clamp((t - dodge0) / 0.35));
  const p0 = W(M.JV), p1 = W(M.JM);
  const f = lerp(0.3 * d, 1, u);
  return { pos: [lerp(p0[0], p1[0], f), 0, lerp(p0[2], p1[2], f)], u, a, b, d, dodge0 };
}

// The frozen star mote (STAGING §1.6): the point is computed once per module (setup) from the Void's pose.
/** A little canvas sprite of a glowing star (used for the frozen mote, so it reads at phone size). */
export function starSprite(color = 0xfff4d8, size = 0.09) {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.15, 'rgba(255,255,255,0.85)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.18)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  g.fillStyle = 'rgba(255,255,255,0.9)';
  for (const r of [0, Math.PI / 2]) { g.save(); g.translate(32, 32); g.rotate(r); g.beginPath(); g.moveTo(-30, 0); g.quadraticCurveTo(0, 2.2, 30, 0); g.quadraticCurveTo(0, -2.2, -30, 0); g.fill(); g.restore(); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.SpriteMaterial({ map: tex, color, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
  const s = new THREE.Sprite(m); s.scale.setScalar(size); s.renderOrder = 6;
  return s;
}

/** A dandelion-like thought seed sprite (glowing core + fanned pappus), for s10's huff. */
export function seedSprite(size = 0.16) {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  g.translate(64, 70);
  const gl = g.createRadialGradient(0, 0, 0, 0, 0, 40); gl.addColorStop(0, 'rgba(255,248,225,0.55)'); gl.addColorStop(1, 'rgba(255,240,210,0)');
  g.fillStyle = gl; g.beginPath(); g.arc(0, 0, 40, 0, 7); g.fill();
  g.strokeStyle = 'rgba(255,250,235,0.85)'; g.lineWidth = 2; g.lineCap = 'round';
  for (let i = 0; i < 13; i++) {
    const a = -Math.PI / 2 + (i - 6) * 0.2, r = 34 + 4 * Math.cos(i * 1.7);
    g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(a) * r, Math.sin(a) * r); g.stroke();
    g.fillStyle = 'rgba(255,252,240,0.9)'; g.beginPath(); g.arc(Math.cos(a) * r, Math.sin(a) * r, 2.4, 0, 7); g.fill();
  }
  g.strokeStyle = 'rgba(255,240,215,0.9)'; g.lineWidth = 2.5; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 22); g.stroke();
  g.fillStyle = 'rgba(255,255,245,1)'; g.beginPath(); g.ellipse(0, 24, 3.5, 6, 0, 0, 7); g.fill();
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.SpriteMaterial({ map: tex, color: 0xfff1d6, transparent: true, depthWrite: false, toneMapped: true });
  const s = new THREE.Sprite(m); s.scale.setScalar(size); s.renderOrder = 6;
  return s;
}
