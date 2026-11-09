// TEMP debug lab (magician detail views) — removed before hand-off.
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const VIEWS = [
  { look: 'footR', dist: 0.9, yaw: 70, pitch: 10, pose: {} },
  { look: 'footR', dist: 0.9, yaw: 20, pitch: 25, pose: {} },
  { look: 'handR', dist: 0.7, yaw: 40, pitch: 5, pose: { armR: { preset: 'dagger_ready' }, armL: { preset: 'pouch' } } },
  { look: 'handL', dist: 0.7, yaw: 10, pitch: 5, pose: { armR: { preset: 'dagger_ready' }, armL: { preset: 'pouch' } } },
  { look: 'chest', dist: 1.1, yaw: 15, pitch: 5, pose: {} },
  { look: 'hip', dist: 1.6, yaw: 60, pitch: 5, pose: {} },
];
export async function setup(app) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x3a3550);
  scene.add(new THREE.HemisphereLight(0xc8d0ff, 0x3a3448, 1.15));
  const key = new THREE.DirectionalLight(0xffe2c4, 2.4); key.position.set(2.2, 4, 3.4); scene.add(key);
  const rim = new THREE.DirectionalLight(0x9fb8ff, 2.0); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const g = new THREE.Mesh(new THREE.CircleGeometry(10, 32), new THREE.MeshStandardMaterial({ color: 0x4a4658 })); g.rotation.x = -Math.PI / 2; scene.add(g);
  const mag = await app.char('MAGICIAN'); scene.add(mag.root);
  return { scene, mag, look: { bloom: 0.3 } };
}
export async function update(t, app, s) {
  if (app.dbgCheck) {
    s.mag.update(t, app.dbgCheck);
    const bad = [];
    s.mag.root.traverse((o) => { const p = o.geometry?.attributes?.position; if (p) { for (let i = 0; i < p.array.length; i++) if (!Number.isFinite(p.array[i])) { bad.push(o.name || o.type + ':' + (o.material?.color?.getHexString?.() || '')); break; } } if (!Number.isFinite(o.position.x) || !Number.isFinite(o.quaternion.x)) bad.push('xf:' + o.type + (o.name||'')); });
    console.log('NaN check', JSON.stringify(bad.slice(0, 20)));
  }
  const v = VIEWS[Math.floor(t) % VIEWS.length];
  s.mag.update(t, { face: 'sly', ...v.pose, ...(app.dbgPose || {}) });
  const a = s.mag.anchor(v.look);
  applyShot(app.camera, framed(a.toArray(), { dist: v.dist, yaw: v.yaw, pitch: v.pitch, fov: 30, screenY: 0.5, drift: 0 }), t);
  app.camera.updateMatrixWorld(true);
  s.mag.update(t, { face: 'sly', ...v.pose });
}
