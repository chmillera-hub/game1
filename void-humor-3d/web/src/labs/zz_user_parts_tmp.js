// TEMP parts bench (USER review) — delete when done. Head close-up; t in [k,k+1) toggles one thing off.
import * as THREE from 'three';
import { applyShot, orbitPos } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
export const DURATION = 12;
export async function setup(app) {
  const scene = new THREE.Scene();
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 32, 16), new THREE.MeshBasicMaterial({ color: 0xe8d8cc, side: THREE.BackSide }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshLambertMaterial({ color: 0xd9b6a0 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  scene.add(new THREE.HemisphereLight(0xffe6cc, 0x6d5a78, 1.05));
  const key = new THREE.DirectionalLight(0xffe0bc, 2.5); key.position.set(2.2, 4, 3.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 15 });
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0xa9bfff, 1.6); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const U = await app.char('USER'); scene.add(U.root);
  const casters = []; U.root.traverse((o) => { if (o.isMesh && o.castShadow) casters.push(o); });
  return { scene, U, casters, look: { bloom: 0.32, bloomThreshold: 0.85, vignette: 0.22 } };
}
export async function update(t, app, s) {
  const U = s.U, k = Math.floor(t);
  const groups = {
    1: [U.hairShell], 2: [U.hairLocks, ...U.cowlick.map((c) => c.tb.mesh)],
    3: [U.headMesh], 4: [U.face.decal.mesh], 5: U.face.eyes.map((e) => e.group), 6: [U.glasses],
    7: [U.torso, U.hoodG], 8: [U.arms.L.sleeve.mesh, U.arms.R.sleeve.mesh, U.arms.L.hand.root, U.arms.R.hand.root],
    9: [...U.face.brows.map((b) => b.tube.mesh), ...U.headG.children.filter((c) => c.isMesh && c.material === U.bodySkin)],
    10: [U.neckTube && U.neckTube.mesh, ...U.strings.map((x) => x.tb.mesh)],
  };
  U.root.traverse((o) => { o.visible = true; });
  U.root.visible = k !== 11;
  const pos = orbitPos([0, 1.43, 0], 0.85, 15, 2);
  applyShot(app.camera, { pos, look: [0, 1.43 - 0.08, 0], fov: 30, drift: 0 }, t); app.camera.updateMatrixWorld(true);
  U.update(t, { face: 'terror', gaze: 'camera', extra: { tears: 0.6, phone: 0.85 } });
  for (const o of groups[k] || []) if (o) o.visible = false;
}
