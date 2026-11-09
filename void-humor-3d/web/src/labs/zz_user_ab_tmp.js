// TEMP A/B perf bench (USER review) — delete when done. t in [0,1): OLD rig, [1,2): NEW rig, [2,3): set only.
// Each second has 4 framings (0.25 s each): head close-up, full body, phone insert, dark phone glow.
import * as THREE from 'three';
import { applyShot, orbitPos } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { create as createOld } from '../chars/zz_user_orig_tmp.js';
export const DURATION = 3;
function framed(look, { dist = 2, yaw = 0, pitch = 0, fov = 35, screenY = 0.4 } = {}) {
  const pos = orbitPos(look, dist, yaw, pitch);
  const off = (screenY - 0.5) * 2 * dist * Math.tan((fov * Math.PI / 180) / 2);
  return { pos: [pos[0], pos[1] + off, pos[2]], look: [look[0], look[1] + off, look[2]], fov, drift: 0 };
}
export async function setup(app) {
  const scene = new THREE.Scene();
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 32, 16), new THREE.MeshBasicMaterial({ color: 0xe8d8cc, side: THREE.BackSide }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshLambertMaterial({ color: 0xd9b6a0 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const hemi = new THREE.HemisphereLight(0xffe6cc, 0x6d5a78, 1.05); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffe0bc, 2.5); key.position.set(2.2, 4, 3.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 15 });
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0xa9bfff, 1.6); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const nu = await app.char('USER'), old = await createOld();
  scene.add(nu.root, old.root);
  return { scene, nu, old, lights: [[key, 2.5], [rim, 1.6], [hemi, 1.05]], sky, look: { bloom: 0.32, bloomThreshold: 0.85, vignette: 0.22 } };
}
export async function update(t, app, s) {
  const which = Math.floor(t), shot = Math.floor((t % 1) * 4);
  s.old.root.visible = which === 0; s.nu.root.visible = which === 1;
  const U = which === 0 ? s.old : s.nu;
  const dark = shot === 3;
  for (const [l, b] of s.lights) l.intensity = b * (dark ? 0.18 : 1);
  s.sky.visible = !dark; s.scene.background = dark ? new THREE.Color(0x141a2c) : null;
  const pose = shot === 0 ? { face: 'terror', gaze: 'camera', extra: { tears: 0.6, phone: 0.85 } }
    : shot === 1 ? { face: 'idle', extra: { phone: 0.85 } }
    : { face: 'scroll', head: { pitch: 0.2 }, extra: { phoneUp: 1, phone: 1, screen: shot === 2 ? 'block' : 'feed', tap: 0.5, thumb: 1 } };
  const doUpd = (u) => { u.update(t, pose); if (shot >= 2) { pose.gaze = u.anchor('phoneScreen'); u.update(t, pose); } };
  doUpd(U);
  let sh;
  if (shot === 0) sh = framed([0, 1.43, 0], { dist: 0.85, yaw: 15, pitch: 2, fov: 30 });
  else if (shot === 1) sh = framed([0, 0.86, 0], { dist: 4.1, yaw: 20, pitch: 3, fov: 32, screenY: 0.45 });
  else if (shot === 2) { const ph = U.anchor('phoneScreen'), n = new THREE.Vector3(0, 0, 1).transformDirection(U.phone.matrixWorld); const cp = ph.clone().addScaledVector(n, 0.24); sh = { pos: cp.toArray(), look: ph.toArray(), fov: 30, drift: 0 }; }
  else sh = framed([0, 1.32, 0], { dist: 1.3, yaw: 25, pitch: -2, fov: 30 });
  applyShot(app.camera, sh, t); app.camera.updateMatrixWorld(true);
  doUpd(U);
}
