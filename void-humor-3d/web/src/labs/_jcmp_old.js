// TEMP perf comparison lab (deleted after benchmarking)
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { create } from '../chars/_jesus_orig_tmp.js';
export async function setup(app) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xd9cfc8);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshLambertMaterial({ color: 0xd9b6a0 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  scene.add(new THREE.HemisphereLight(0xffe6cc, 0x6d5a78, 1.05));
  const key = new THREE.DirectionalLight(0xffe0bc, 2.5); key.position.set(2.2, 4, 3.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 15 });
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0xa9bfff, 1.6); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const j = await create(); scene.add(j.root);
  return { scene, j, look: { bloom: 0.32, bloomThreshold: 0.85, vignette: 0.22, warm: 0.1 } };
}
export async function update(t, app, s) {
  const close = t >= 10;
  applyShot(app.camera, close ? framed([0, 1.47, 0], { dist: 1.0, yaw: 8, pitch: 2, fov: 30, screenY: 0.56, drift: 0 }) : framed([0, 0.92, 0], { dist: 3.3, yaw: 15, pitch: 3, fov: 32, screenY: 0.5, drift: 0 }), t);
  app.camera.updateMatrixWorld(true);
  s.j.update(t, { face: 'kind', gaze: 'camera', speech: false, armL: { preset: 'open' }, armR: { preset: 'explain' } });
}
