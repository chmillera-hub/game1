// Small helpers shared by s01.js / s02.js (not a scene module: the registry only loads sNN.js).
// Pure functions of t; no state carried between frames.
import * as THREE from 'three';
import { CTX } from '../core/context.js';
import { clamp, smooth } from '../core/util.js';
import { T } from '../core/timeline.js';
import { EDGE } from './marks.js';

/**
 * A Group for a scene's own props inside a SHARED set scene. Other scenes never remove it, so it hides itself
 * whenever the frame being rendered is not this scene's (st.__t is set at the top of the scene's update()).
 */
export function ownedGroup(st, name = 'owned') {
  const g = new THREE.Group();
  g.name = name;
  const base = THREE.Object3D.prototype.updateMatrixWorld;
  g.updateMatrixWorld = function (force) { this.visible = st.__t === CTX.t; return base.call(this, force); };
  return g;
}

/** (Re)attach exactly the characters `names` to the scene; detach any other loaded character parented to it. */
export function cast(app, scene, names) {
  for (const [nm, c] of Object.entries(app.chars)) {
    if (!c || !c.root) continue;
    if (names.includes(nm)) { if (c.root.parent !== scene) scene.add(c.root); c.root.visible = true; }
    else if (c.root.parent === scene) scene.remove(c.root);
  }
}

/** local stage mark (x, z) -> world [x, groundY, z] on the EDGE terrain */
export function G(set, lx, lz, dy = 0) {
  const w = EDGE.W(lx, 0, lz);
  w[1] = set.groundAt(w[0], w[2]) + dy;
  return w;
}

/** 0 -> 1 -> 0 bump over [a, b] (seconds), smooth both sides; peak at a + (b - a) * pk */
export function bump(t, a, b, pk = 0.5) {
  if (t <= a || t >= b) return 0;
  const m = a + (b - a) * pk;
  return t < m ? smooth((t - a) / (m - a)) : smooth((b - t) / (b - m));
}

/** step 0 -> 1 eased between two times (refs or seconds) */
export const ramp = (t, a, b, e = smooth) => e(clamp((t - T(a)) / Math.max(1e-6, T(b) - T(a))));

/** damped "water balloon" jiggle after footfalls at phase steps: phase in cycles, 2 steps per cycle */
export function jiggle(phase, cps, amp = 0.012, decay = 7, freq = 5.2) {
  const tau = (((phase * 2) % 1) + 1) % 1 / (2 * cps);   // seconds since the last footfall
  return amp * Math.exp(-decay * tau) * Math.cos(2 * Math.PI * freq * tau);
}

/** times (s) in [t0, t1) when a foot plants for a walk phase function phase = (t - tA) * cps + ph0 (2 per cycle) */
export function footfalls(t0, t1, tA, cps, ph0 = 0, offset = 0) {
  const out = [];
  const p0 = (t0 - tA) * cps + ph0, p1 = (t1 - tA) * cps + ph0;
  for (let n = Math.ceil((p0 - offset) * 2); n / 2 + offset < p1; n++) out.push(tA + (n / 2 + offset - ph0) / cps);
  return out;
}

export const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
export const toArr = (v) => (v.isVector3 ? [v.x, v.y, v.z] : v);
/** world direction of a LOCAL stage direction (x, z) */
export const WD = (x, z) => { const a = EDGE.W(x, 0, z), o = EDGE.W(0, 0, 0); return V3(a[0] - o[0], 0, a[2] - o[2]); };

/**
 * Fit a camera (no rendering): find pos/look so world points land on target pixels.
 * pts: [[Vector3, px, py, weight]]; pos regularised toward pos0; yMin/yMax clamp the camera height. Deterministic.
 */
export function fitCam(pts, fov, pos0, look0, { reg = 0.02, yMin = -99, yMax = 99, iters = 500 } = {}) {
  const cam = new THREE.PerspectiveCamera(fov, 720 / 1280, 0.05, 400);
  const P = [...pos0, ...look0];
  const cost = (q) => {
    cam.position.set(q[0], q[1], q[2]); cam.up.set(0, 1, 0); cam.lookAt(q[3], q[4], q[5]); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
    let e = 0;
    for (const [w, x, y, wt = 1] of pts) {
      const v = w.clone().project(cam);
      if (v.z > 1) { e += 1e7; continue; }
      const sx = (v.x * 0.5 + 0.5) * 720, sy = (1 - (v.y * 0.5 + 0.5)) * 1280;
      e += wt * ((sx - x) ** 2 + (sy - y) ** 2);
    }
    for (let i = 0; i < 3; i++) e += reg * 1e4 * (q[i] - pos0[i]) ** 2;
    if (q[1] < yMin) e += 1e7 * (yMin - q[1]) ** 2; if (q[1] > yMax) e += 1e7 * (q[1] - yMax) ** 2;
    return e;
  };
  let best = cost(P), step = 0.5;
  for (let it = 0; it < iters && step > 0.001; it++) {
    let improved = false;
    for (let i = 0; i < 6; i++) for (const d of [step, -step]) { const q = P.slice(); q[i] += d; const c = cost(q); if (c < best) { best = c; P.splice(0, 6, ...q); improved = true; } }
    if (!improved) step *= 0.6;
  }
  return { pos: P.slice(0, 3), look: P.slice(3, 6), err: Math.sqrt(best / Math.max(1, pts.length)) };
}
