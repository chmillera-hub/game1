// TEMP debug lab for the BACKROOM set (deleted after use)
import * as THREE from 'three';
import { applyShot } from '../core/camera.js';
export async function setup(app) {
  const set = await app.set('BACKROOM');
  set.scene.add(app.camera);
  return { scene: set.scene, set, look: set.look };
}
export async function update(t, app, S) {
  const set = S.set, mode = Math.round(t);
  set.update(t, { crash: 1, crashT: mode === 3 ? 0.75 : mode === 4 ? 0.9 : 4, bucketHat: mode >= 3 ? { pos: [3.5, 1.1, -3.4] } : undefined });
  const shots = [
    { pos: [3.4, 3.2, -3.2], look: [3.5, 0, -4.4], fov: 50 },
    { pos: [2.2, 0.6, -3.0], look: [3.6, 0.1, -4.4], fov: 45 },
    { pos: [3.7, 1.45, 1.15], look: [3.65, 0.36, -4.1], fov: 42 },
    { pos: [2.4, 0.7, -2.7], look: [3.5, 0.2, -4.4], fov: 40 },
    { pos: [2.4, 0.7, -2.7], look: [3.5, 0.2, -4.4], fov: 40 },
  ];
  applyShot(app.camera, { ...shots[mode], drift: 0 }, t);
  S.look = set.look;
}
