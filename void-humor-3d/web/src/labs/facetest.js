// Lab: face rig test — a plain head cycling through expression presets (1 s each).
import * as THREE from 'three';
import { Face, X, EXPR } from '../core/face.js';
import { skin, hair } from '../core/materials.js';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';

const NAMES = Object.keys(EXPR);
export async function setup(app) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x3a3550);
  scene.add(new THREE.HemisphereLight(0xfff0e0, 0x403050, 1.2));
  const key = new THREE.DirectionalLight(0xfff2e0, 2.2); key.position.set(1.5, 2.5, 3); scene.add(key);
  const rim = new THREE.DirectionalLight(0x9fb8ff, 1.4); rim.position.set(-2, 1.5, -2); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const head = new THREE.Group(); head.position.set(0, 1.5, 0); scene.add(head);
  const skinMat = skin(0xd9a07a, { jaw: { y: -0.045, drop: 0.022, back: 0.004, soft: 0.03 } });
  const geo = new THREE.SphereGeometry(1, 64, 48); geo.scale(0.12, 0.135, 0.118);
  const headMesh = new THREE.Mesh(geo, skinMat); head.add(headMesh);
  const hairMesh = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32, 0, Math.PI * 2, 0, Math.PI * 0.42), hair(0x3b2416));
  hairMesh.scale.set(0.128, 0.145, 0.128); hairMesh.rotation.x = -0.25; hairMesh.position.y = 0.01; head.add(hairMesh);
  const face = new Face({
    head, radii: [0.12, 0.135, 0.118], seed: 3,
    eyes: { u: 0.36, v: 0.1, radius: 0.034, sink: 0.5, lidMaterial: skinMat, iris: 0x5a3a20, iris2: 0xb08850, irisR: 0.66, pupilR: 0.27 },
    brows: { color: 0x3b2416, thickness: 0.0085, lift: 0.002, inner: [0.16, 0.36], mid: [0.36, 0.42], outer: [0.56, 0.36], range: 0.11 },
    mouth: { v: -0.42, halfW: 0.036 },
    jaw: [skinMat.userData.uJaw],
  });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.16, 0.4, 8, 24), skin(0x4a6fa5));
  body.position.set(0, 1.08, 0); scene.add(body);
  return { scene, head, face, look: { bloom: 0.3 } };
}
export async function update(t, app, s) {
  const i = Math.floor(t) % NAMES.length;
  const p = X(NAMES[i], { autoBlink: 0, saccade: 0 });
  s.head.rotation.set(0, 0.25 * Math.sin(t * 0.5) * (app.yaw ?? 0), 0);
  applyShot(app.camera, framed([0, 1.5, 0], { dist: 0.9, yaw: 12, pitch: 2, fov: 30, screenY: 0.4, drift: 0 }), t);
  s.face.update(t, p, { gaze: app.camera.position.clone() });
}
export const names = NAMES;
