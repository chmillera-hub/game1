// Camera helpers. A "shot" = { pos:[x,y,z], look:[x,y,z], fov (vertical deg), roll (rad), drift (0..1) }.
//   applyShot(cam, shot, t)          set camera (+ subtle seeded drift if shot.drift)
//   shotAt(t, [[time, shot, ease], ...])   keyframed camera (positions/looks/fov/roll interpolated)
//   orbitPos(look, dist, yawDeg, pitchDeg) -> [x,y,z]  (yaw 0 = camera on +Z looking toward -Z)
//   frameFace(headWorldPos, {dist, yaw, pitch, fov, screenY}) -> shot that puts a point at a given screen height
import * as THREE from 'three';
import { T } from './timeline.js';
import { ease as EASE, clamp, fbm1, DEG } from './util.js';

const lerpArr = (a, b, u) => a.map((x, i) => x + (b[i] - x) * u);

export function shotAt(t, keys) {
  const ks = keys.map(([tt, s, e]) => [T(tt), s, e || 'inOut']);
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) {
    if (t < ks[i][0]) {
      const [t0, a] = ks[i - 1], [t1, b, e] = ks[i];
      const u = (EASE[e] || EASE.inOut)(clamp((t - t0) / Math.max(1e-6, t1 - t0)));
      return {
        pos: lerpArr(a.pos, b.pos, u), look: lerpArr(a.look, b.look, u),
        fov: (a.fov ?? 35) + ((b.fov ?? 35) - (a.fov ?? 35)) * u, roll: (a.roll || 0) + ((b.roll || 0) - (a.roll || 0)) * u,
        drift: (a.drift ?? 0.5) + ((b.drift ?? 0.5) - (a.drift ?? 0.5)) * u,
      };
    }
  }
  return ks[ks.length - 1][1];
}

export function applyShot(cam, s, t = 0, seed = 1) {
  const d = s.drift ?? 0.5;
  const dx = d * 0.012 * fbm1(t * 0.23, seed), dy = d * 0.008 * fbm1(t * 0.19, seed + 9), dz = d * 0.01 * fbm1(t * 0.17, seed + 21);
  cam.position.set(s.pos[0] + dx, s.pos[1] + dy, s.pos[2] + dz);
  cam.fov = s.fov ?? 35;
  cam.updateProjectionMatrix();
  cam.up.set(0, 1, 0);
  cam.lookAt(s.look[0] + dx * 0.4, s.look[1] + dy * 0.4, s.look[2]);
  if (s.roll) cam.rotateZ(s.roll);
  if (s.shake) { // { amp (rad), freq }
    cam.rotateX(s.shake.amp * fbm1(t * (s.shake.freq ?? 8), seed + 40));
    cam.rotateY(s.shake.amp * fbm1(t * (s.shake.freq ?? 8), seed + 41));
  }
  cam.updateMatrixWorld();
}

export function orbitPos(look, dist, yawDeg = 0, pitchDeg = 0) {
  const y = yawDeg * DEG, p = pitchDeg * DEG;
  return [look[0] + dist * Math.sin(y) * Math.cos(p), look[1] + dist * Math.sin(p), look[2] + dist * Math.cos(y) * Math.cos(p)];
}

/**
 * A shot that looks at `look` from (dist, yaw, pitch) but shifts the aim so `look` lands at screen height
 * `screenY` (0 = top, 1 = bottom of the 720x1280 frame). Handy to keep faces above the subtitle band.
 */
export function framed(look, { dist = 2, yaw = 0, pitch = 0, fov = 35, screenY = 0.38, drift = 0.5, roll = 0 } = {}) {
  const pos = orbitPos(look, dist, yaw, pitch);
  // shifting the aim point vertically by offset moves the subject in frame: subject at screenY means aim
  // is below it by (screenY-0.5)*frameHeight at that distance
  const fh = 2 * dist * Math.tan((fov * DEG) / 2);
  const off = (screenY - 0.5) * fh;
  const aim = [look[0], look[1] - off, look[2]];
  const pos2 = [pos[0], pos[1] - off, pos[2]];
  return { pos: pos2, look: aim, fov, drift, roll };
}

export function worldToScreen(cam, v) {
  const p = (v instanceof THREE.Vector3 ? v.clone() : new THREE.Vector3(...v)).project(cam);
  return [(p.x * 0.5 + 0.5) * 720, (1 - (p.y * 0.5 + 0.5)) * 1280, p.z];
}
