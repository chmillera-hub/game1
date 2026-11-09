// TEMP lab (s08-s10 animator): folded-arm variants for the Void, seen from the film's camera angles.
// t = variant*4 + view (views: 0 low front (LOWUP), 1 close front (VOID_CU), 2 high 13 deg left (MASTER), 3 3/4 right)
import * as THREE from 'three';
import { applyShot } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { VX } from '../chars/void.js';
import { frame, EDGE } from '../scenes/marks.js';
import { foldedArms } from '../scenes/armour_common.js';

const VARIANTS = [
  {},
  { pl: [0.7, -0.35, 0.65], pr: [-0.7, -0.3, 0.7] },
  { pl: [0.5, -0.3, 0.85], pr: [-0.5, -0.25, 0.85], lz: 0.12, rz: 0.22 },
  { pl: [0.7, -0.35, 0.65], pr: [-0.7, -0.3, 0.7], hs: 0.68 },
  { pl: [0.5, -0.3, 0.85], pr: [-0.5, -0.25, 0.85], lz: 0.12, rz: 0.22, lx: -0.38, rx: 0.38, hs: 0.68 },
];
export async function setup(app) {
  const set = await app.set('EDGE');
  const vd = await app.char('VOID');
  set.scene.add(vd.root);
  return { scene: set.scene, set, vd, look: set.look };
}
export async function update(t, app, st) {
  const vi = Math.floor(t / 4), view = Math.floor(t % 4);
  const v = VARIANTS[Math.min(vi, VARIANTS.length - 1)];
  const sit = vi >= VARIANTS.length ? 1 : 0;
  const P0 = EDGE.W(EDGE.M.V.p), y0 = EDGE.Y(EDGE.M.V.yaw), yd = y0 * 180 / Math.PI;
  const at = (dx, dy, dz) => [P0[0] + dx, dy, P0[2] + dz];
  const fw = [Math.sin(y0), Math.cos(y0)];
  const eye = at(fw[0] * 0.3, 2.16 - 0.9 * sit, fw[1] * 0.3);
  const shots = [
    { pos: at(Math.sin(y0 - 0.1) * 4.4, 0.97, Math.cos(y0 - 0.1) * 4.4), look: at(0, 1.75, 0), fov: 47, drift: 0 },
    frame(eye, { dist: 3.4, yaw: yd + 5, pitch: -4, fov: 33, screenY: 0.29, drift: 0 }),
    frame(at(0, 1.2, 0), { dist: 8, yaw: yd + 13, pitch: 14, fov: 33, screenY: 0.45, drift: 0 }),
    frame(at(0, 1.4 - 0.5 * sit, 0), { dist: 8.5, yaw: yd - 40, pitch: 4, fov: 33, screenY: 0.45, drift: 0 }),
  ];
  applyShot(app.camera, shots[view], t);
  st.set.update(100, { tod: 0.33, voidSky: 0.6 });
  const pose = { pos: P0, yaw: y0, face: VX('scowl'), body: { lean: -0.05, sit }, gaze: 'camera', armL: { preset: 'crossed' }, armR: { preset: 'crossed' } };
  st.vd.update(t, pose);
  const f = foldedArms(st.vd, { o: v });
  st.vd.update(t, { ...pose, ...f });
}
