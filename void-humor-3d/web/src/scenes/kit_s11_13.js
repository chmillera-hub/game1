// Shared helpers for scenes s11 / s12 / s13 (EDGE, Part One, late dusk). Not a scene module (the registry only
// loads sNN.js). Pure helpers + small prop builders; every pose is a function of t.
import * as THREE from 'three';
import { T } from '../core/timeline.js';
import { CTX } from '../core/context.js';
import { CELL } from '../core/particles.js';
import { EDGE, galaxyAt, galaxySpin } from './marks.js';
import { makeLittleGalaxy as mkLittleGalaxy } from './edgeprops.js';

// ------------------------------------------------------------------------------------------- word timings
// W('s13b08', 'you') -> absolute time of that word (from data/lines.json, relative to the beat start), so a
// re-recorded line re-times the reaction. Falls back to a fraction of the beat if the word is missing.
let LINES = null;
export async function loadLines() {
  if (!LINES) { try { LINES = await (await fetch('/data/lines.json')).json(); } catch (e) { LINES = {}; } }
  return LINES;
}
const norm = (s) => String(s).toLowerCase().replace(/[^a-z']/g, '');
export function W(beat, word, { end = false, occ = 0, frac = 0.5, alt = [] } = {}) {
  const L = LINES && LINES[beat];
  const t0 = T(beat);
  if (L && L.words) {
    const names = [norm(word), ...alt.map(norm)];
    let n = 0;
    for (const w of L.words) if (names.includes(norm(w.w))) { if (n++ === occ) return t0 + (end ? w.end : w.start); }
  }
  return t0 + frac * (T(beat + '.end') - t0);
}

// ------------------------------------------------------------------------------------------- marks (world)
const M = EDGE.M;
export const POS = Object.fromEntries(Object.entries(M).map(([k, m]) => [k, EDGE.W(m.p)]));
export const YAW = Object.fromEntries(Object.entries(M).map(([k, m]) => [k, EDGE.Y(m.yaw)]));
// the user's seat: U minus the 5 cm scoot back on "thing" (s09b03), kept through s10+ (armour_common.userPos)
POS.USEAT = [POS.U[0] - Math.sin(YAW.U) * 0.05, 0, POS.U[2] - Math.cos(YAW.U) * 0.05];
/** stage-local point -> world array */
export const SW = (x, y, z) => EDGE.W(x, y, z);
/** a world point `dist` m from a stage-local origin along a LOCAL facing yaw + offsets (for gaze directions) */
export function dirPoint(originW, localYaw, yawOff, pitch, dist = 3) {
  const y = localYaw + yawOff;
  const L = EDGE.L(originW);
  return EDGE.W(L[0] + dist * Math.sin(y) * Math.cos(pitch), L[1] + dist * Math.sin(pitch), L[2] + dist * Math.cos(y) * Math.cos(pitch));
}
export const v3 = (a) => (a.isVector3 ? a.clone() : new THREE.Vector3(a[0], a[1], a[2]));
export const arr = (v) => (v.isVector3 ? [v.x, v.y, v.z] : v);
export const add = (a, b) => { const A = arr(a), B = arr(b); return [A[0] + B[0], A[1] + B[1], A[2] + B[2]]; };
/** stage-local offset vector (direction) -> world vector */
export function SV(x, y, z) { const o = EDGE.W(0, 0, 0), p = EDGE.W(x, y, z); return [p[0] - o[0], p[1] - o[1], p[2] - o[2]]; }

// ------------------------------------------------------------------------------------------- leak guard
// Props live in the shared EDGE scene. So they never draw in another scene's frame, each update() stamps
// the frame time and the meshes collapse themselves in onBeforeRender when the stamp is stale.
const STAMPS = {};
export function stamp(t, id = 'default') { STAMPS[id] = t; }
const ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
/** guard every mesh under obj: it draws only in frames whose update() called stamp(t, id) for this very t */
export function own(obj, id = 'default') {
  obj.traverse((o) => {
    if (!o.isMesh && !o.isPoints && !o.isSprite) return;
    const prev = o.onBeforeRender;
    o.onBeforeRender = function (...a) { if (CTX.t !== STAMPS[id]) this.matrixWorld.copy(ZERO); if (prev) prev.apply(this, a); };
  });
  return obj;
}

// ------------------------------------------------------------------------------------------- galaxies
// The big sky galaxy (shared helper positions) + the little galaxy lying flat by the user's sneaker.
export function drawSkyGalaxy(ps, t) {
  const g = galaxyAt(t);
  if (g) ps.add(g, EDGE.GALAXY.size, 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
}
/** the little galaxy lying flat by the user's sneaker: the SHARED prop of edgeprops.js (same rest spot / look as
 *  s04-s10; it scopes itself to [s04, s14.end)). Returns its group with userData.update(t). */
let _lg = null;
export function makeLittleGalaxy() {
  if (_lg) return _lg;                                 // ONE instance shared by s11-s13 (no stacked stale copies)
  const lg = mkLittleGalaxy();
  lg.group.userData.update = (t) => lg.update(t);
  return (_lg = lg.group);
}

// ------------------------------------------------------------------------------------------- two-pass solve
// Characters gaze at / touch each other: pass 0 runs every rig with gaze + head-follow stripped (so nothing
// depends on stale anchors from another frame), pass 1 runs the real poses against the fresh anchors.
// `mid()` runs between the passes (frame the camera there from fresh pass-0 anchors, then applyShot, so the
// final pass sees the right camera for catchlights).
export function solve(t, list, mid = null) {
  for (const [ch, fn] of list) {
    const p = fn(0);
    const q = { ...p, gaze: null };
    if (q.head) q.head = { ...q.head, follow: 0, look: undefined, track: 0 };
    ch.update(t, q);
  }
  if (mid) mid();
  for (const [ch, fn] of list) ch.update(t, fn(1));
}

// eased pulse 0 -> 1 -> 0: up over [a, a+up], down over [b-down, b]
export function pulse(t, a, b, up = 0.15, down = 0.25) {
  if (t <= a || t >= b) return 0;
  const u = Math.min(1, (t - a) / up), d = Math.min(1, (b - t) / down);
  const s = (x) => x * x * (3 - 2 * x);
  return s(Math.min(u, d));
}

// ------------------------------------------------------------------------------------------- walking a path
// A stage-local polyline walked from t0 to t1 with a trapezoid speed profile (accelerate over ta, settle over td).
// Returns { pos (world), yaw (world), amount, phase, speed, u } — feed walk:{amount, phase} and pos/yaw to the rig.
// Feet stay honest: the cycle phase is distance / stride. Yaw follows the tangent, blended from yaw0 at the
// start and into yaw1 over the last `turn` seconds (local yaws, unwrapped by the caller).
const _curves = new Map();
export function walkPath(t, ptsLocal, t0, t1, { ta = 0.4, td = 0.5, stride = 1.05, phase0 = 0, yaw0 = null, yaw1 = null, turnIn = 0.35, turn = 0.5 } = {}) {
  const key = JSON.stringify(ptsLocal);
  let c = _curves.get(key);
  if (!c) { c = new THREE.CatmullRomCurve3(ptsLocal.map((p) => new THREE.Vector3(p[0], 0, p[2])), false, 'centripetal'); c.L = c.getLength(); _curves.set(key, c); }
  const D = Math.max(1e-3, t1 - t0), L = c.L;
  const v = L / (D - (ta + td) / 2);
  const tt = Math.min(Math.max(t - t0, 0), D);
  let s;
  if (tt < ta) s = 0.5 * v * tt * tt / ta;
  else if (tt <= D - td) s = 0.5 * v * ta + v * (tt - ta);
  else s = L - 0.5 * v * (D - tt) * (D - tt) / td;
  const speed = tt <= 0 || tt >= D ? 0 : tt < ta ? v * tt / ta : tt > D - td ? v * (D - tt) / td : v;
  const u = Math.min(1, Math.max(0, s / L));
  const p = c.getPointAt(u), tg = c.getTangentAt(Math.min(0.999, Math.max(0.001, u)));
  let yaw = Math.atan2(tg.x, tg.z);
  const smooth = (x) => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
  const unwrap = (a, ref) => { while (a - ref > Math.PI) a -= 2 * Math.PI; while (a - ref < -Math.PI) a += 2 * Math.PI; return a; };
  if (yaw0 != null) { yaw = unwrap(yaw, yaw0); yaw = yaw0 + (yaw - yaw0) * smooth((t - t0) / turnIn); }
  if (yaw1 != null) { const y1 = unwrap(yaw1, yaw); yaw = yaw + (y1 - yaw) * smooth((t - (t1 - turn)) / turn); }
  const amount = smooth(Math.min((t - t0) / (ta * 0.7), (t1 + 0.12 - t) / (td * 0.9)));
  return { pos: EDGE.W(p.x, 0, p.z), local: [p.x, 0, p.z], yawLocal: yaw, yaw: EDGE.Y(yaw), amount: t < t0 || t > t1 + 0.12 ? 0 : amount, phase: phase0 + s / stride, speed, u };
}
