// TEMP bench lab (edge set agent): set only, 4 camera setups, optional &hide=a,b (component breakdown). Delete after.
import { applyShot } from '../core/camera.js';
import { create } from '../sets/edge.js';
const SH = [
  [{ pos: [0.6, 1.7, 10.5], look: [-0.4, 1.6, -12], fov: 40 }, { tod: 0 }],
  [{ pos: [0.6, 1.55, 5.2], look: [0.3, 1.45, 0], fov: 32 }, { tod: 0.2, voidSky: 0.6, voidPos: [1.25, 0, -0.5] }],
  [{ pos: [-0.2, 1.6, -5.4], look: [-0.6, 1.25, 1.8], fov: 34 }, { tod: 0.5 }],
  [{ pos: [6, 9, 16], look: [-2, 0, -14], fov: 42 }, { tod: 0.3 }],
];
const HIDE = new Set((new URLSearchParams(location.search).get('hide') || '').split(',').filter(Boolean));
export async function setup(app) { const set = await create(); return { scene: set.scene, set, look: set.look }; }
export async function update(t, app, s) {
  const [shot, o] = SH[Math.floor(t / 2) % 4]; s.set.update(t, o); applyShot(app.camera, shot, t); s.look = { ...s.set.look };
  const P = s.set.props;
  const vis = { sky: P.sky, clouds: P.clouds, terrain: P.terrain, path: P.path, flowers: P.flowers, seeds: P.seeds.mesh, motes: P.motes.mesh };
  for (const k in vis) vis[k].visible = !HIDE.has(k) && !HIDE.has('all');
  for (const tr of P.trees) tr.visible = !HIDE.has('trees') && !HIDE.has('all');
  for (const b of P.bushes) b.visible = !HIDE.has('bushes') && !HIDE.has('all');
  P.key.castShadow = !HIDE.has('shadow') && !HIDE.has('all');
  if (HIDE.has('lights') || HIDE.has('all')) { P.key.visible = P.fill.visible = P.hemi.visible = false; }
}
