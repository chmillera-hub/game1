// TEMP debug lab (USER review fixes) — hides one part per second to identify artefacts. Delete when done.
import * as THREE from 'three';
import { applyShot, orbitPos } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
export const DURATION = 8;
export async function setup(app) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0xe8e0d8);
  scene.add(new THREE.HemisphereLight(0xffe6cc, 0x6d5a78, 1.05));
  const key = new THREE.DirectionalLight(0xffe0bc, 2.5); key.position.set(2.2, 4, 3.4); scene.add(key);
  const rim = new THREE.DirectionalLight(0xa9bfff, 1.6); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const user = await app.char('USER'); scene.add(user.root);
  const P = user.hairShell.geometry.attributes.position, R = 24, J = P.count / R;
  const out = [];
  for (let i = 0; i < P.count; i++) {
    const x = P.getX(i), y = P.getY(i), z = P.getZ(i);
    const j = Math.floor(i / R), r = i % R, u = -Math.PI + (j / J) * 2 * Math.PI;
    if (y < -0.04 && Math.hypot(x, z) < 0.13) out.push(`j${j} u${u.toFixed(2)} r${r}: ${x.toFixed(3)},${y.toFixed(3)},${z.toFixed(3)} rad${Math.hypot(x, z).toFixed(3)}`);
  }
  console.log(out.length + ' suspicious\n' + out.slice(0, 40).join('\n'));
  return { scene, user, look: { bloom: 0.3 } };
}
export async function update(t, app, s) {
  const U = s.user, i = Math.floor(t);
  const parts = [null, U.hairLocks, U.hairShell, U.glasses, U.hoodG, U.neckTube && U.neckTube.mesh, U.face.decal.mesh, U.headMesh];
  for (const p of parts) if (p) p.visible = true;
  if (parts[i]) parts[i].visible = false;
  const pos = orbitPos([0, 1.42, 0], 1.5, 10, 2);
  applyShot(app.camera, { pos, look: [0, 1.42 - 0.1 * 0.8, 0], fov: 30, drift: 0 }, t);
  app.camera.updateMatrixWorld(true);
  U.update(t, { face: 'idle', gaze: 'camera', extra: { phone: 0.6 } });
  if (parts[i]) parts[i].visible = false;
}
