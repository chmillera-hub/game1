// WIP probe lab for the JESUS rig (scratch; shot = floor(t)). Not part of the film.
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { JX } from '../chars/jesus.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const head = (yaw, pose = {}, dist = 1.0, pitch = 3) => ({ pose, shot: framed([0, 1.5, 0], { dist, yaw, pitch, fov: 30, screenY: 0.42, drift: 0 }) });
const SHOTS = [
  head(0), head(35),
  { pose: { face: 'kind' }, shot: framed([0, 1.35, 0], { dist: 2.0, yaw: 150, pitch: 8, fov: 30, screenY: 0.4, drift: 0 }) },
  { pose: { face: 'kind' }, shot: framed([0, 1.3, 0], { dist: 2.6, yaw: 185, pitch: 4, fov: 30, screenY: 0.4, drift: 0 }) },
  head(10, { face: 'teehee', body: { giggle: 1, shrug: 0.45 }, armR: { preset: 'teehee' }, gaze: 'camera' }, 1.1),
  head(10, { face: 'laugh', body: { giggle: 0.6 }, gaze: 'camera' }, 1.1),
  head(5, { face: 'awkward', body: { shrug: 0.7, hunch: 0.2 }, gaze: null }, 1.1),
  head(15, { face: 'whisper', armR: { preset: 'whisper' }, head: { yaw: 0.45, roll: -0.08 }, gaze: V(0.6, 1.55, 0.6) }, 1.1),
  head(10, { face: 'kind', gaze: 'camera' }, 1.1),
  head(90, { face: 'kind' }, 1.2),
  head(10, { face: 'shrug', body: { shrug: 0.8 }, armL: { preset: 'shrug' }, armR: { preset: 'shrug' }, head: { roll: 0.1 }, gaze: 'camera' }, 2.2),
  { pose: { face: 'kind', armL: { preset: 'open' }, armR: { preset: 'open' }, gaze: 'camera' }, shot: framed([0, 1.1, 0], { dist: 2.4, yaw: 0, pitch: 6, fov: 30, screenY: 0.5, drift: 0 }) },
  { pose: { face: 'kind', yaw: 1.2 }, shot: framed([0, 0.95, 0], { dist: 3.6, yaw: 0, pitch: 3, fov: 32, screenY: 0.45, drift: 0 }) },
  { pose: { face: 'kind', yaw: -1.4 }, shot: framed([0, 0.95, 0], { dist: 3.6, yaw: 0, pitch: 3, fov: 32, screenY: 0.45, drift: 0 }) },
  { pose: { face: 'kind' }, shot: framed([-0.08, 1.12, -0.1], { dist: 0.9, yaw: 200, pitch: 4, fov: 30, screenY: 0.5, drift: 0 }) },
  { pose: { face: 'kind' }, shot: framed([-0.12, 1.0, 0.05], { dist: 0.9, yaw: -70, pitch: 4, fov: 30, screenY: 0.5, drift: 0 }) },
];
export const DURATION = SHOTS.length;
export async function setup(app) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xd9cfc8);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshLambertMaterial({ color: 0xd9b6a0 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  scene.add(new THREE.HemisphereLight(0xffe6cc, 0x6d5a78, 1.05));
  const key = new THREE.DirectionalLight(0xffe0bc, 2.5); key.position.set(2.2, 4, 3.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 15 }); key.shadow.bias = -0.0005;
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0xa9bfff, 1.6); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  EYE_LIGHT.uKeyColor.value.set(1.0, 0.93, 0.84);
  const jesus = await app.char('JESUS');
  scene.add(jesus.root);
  return { scene, jesus, look: { bloom: 0.32, bloomThreshold: 0.85, vignette: 0.22, warm: 0.1 } };
}
export async function update(t, app, s) {
  const S = SHOTS[Math.min(SHOTS.length - 1, Math.max(0, Math.floor(t)))];
  applyShot(app.camera, S.shot, t); app.camera.updateMatrixWorld(true);
  s.jesus.update(t, { speech: false, ...S.pose });
}
