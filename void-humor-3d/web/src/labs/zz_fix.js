// SCRATCH lab (temporary, review-fix probing): Void head/chin and sleeve cuffs from problem angles. t = view index.
import * as THREE from 'three';
import { EYE_LIGHT } from '../core/context.js';
import { VX } from '../chars/void.js';

const VIEWS = [
  // [camPos, look, fov, pose]
  [[0, 2.2, 3.4], [0, 2.1, 0], 36, {}],
  [[0.4, 1.3, 2.3], [0, 2.05, 0.1], 40, {}],
  [[0.15, 1.75, 1.2], [0, 1.95, 0.1], 44, {}],
  [[1.5, 1.6, 1.6], [0, 2.0, 0.1], 40, {}],
  [[-1.4, 1.45, 1.8], [0, 2.0, 0.1], 40, {}],
  [[0.6, 2.5, 2.2], [0, 2.0, 0.1], 40, { head: { pitch: 0.25 } }],
  // cuffs: forearm toward the camera
  [[2.6, 2.3, 3.0], [0.9, 2.0, 0.6], 40, { armL: { preset: 'wave', from: 'rest', mix: 0.6, hand: { spread: 0.55, curl: 0.12, thumb: 0.6 } } }],
  [[0.6, 2.0, 3.2], [0.4, 1.9, 0.6], 40, { armL: { preset: 'whisper' } }],
  [[0.9, 1.7, 3.4], [0.6, 1.5, 0.9], 40, { armL: { preset: 'pat', target: [0.7, 1.55, 1.25] } }],
  [[0.9, 1.7, 3.4], [0.6, 1.5, 0.9], 40, { armL: { preset: 'around', target: [0.7, 1.4, 1.2] } }],
  [[1.2, 1.4, 3.4], [0.8, 1.7, 0.6], 40, { armL: { preset: 'shrug' } }],
  [[0.8, 1.4, 3.6], [0.5, 1.7, 0.6], 40, { armL: { preset: 'reach', target: [0.6, 1.6, 1.6] } }],
  // 12-15: bowed head, low cameras (s18/s19); over-the-shoulder look (s12); close low ECU
  [[0.3, 1.2, 2.6], [0, 1.95, 0.3], 40, { head: { pitch: 0.45 } }],
  [[0.9, 1.25, 1.9], [0, 1.9, 0.3], 40, { head: { pitch: 0.5, yaw: 0.3 } }],
  [[2.2, 1.7, -0.4], [0, 2.0, 0.0], 36, { head: { yaw: 1.0, pitch: 0.1 } }],
  [[0.25, 1.45, 1.35], [0.05, 1.85, 0.35], 44, { head: { pitch: 0.4, yaw: 0.15 } }],
  [[1.6, 2.3, -3.0], [0, 1.9, 0], 40, { head: { pitch: 0.45 } }],
  [[3.2, 2.0, 0.6], [0, 1.9, 0.2], 40, { head: { pitch: 0.45 } }],
  [[3.2, 2.0, 0.6], [0, 1.9, 0.2], 40, { head: { pitch: 0.0 } }],
];

export async function setup(app) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xc8a8b8);
  scene.add(new THREE.HemisphereLight(0xffe2cc, 0x4a3a66, 1.1));
  const key = new THREE.DirectionalLight(0xffd9b8, 2.4); key.position.set(4, 6, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(0xa8c0ff, 1.6); rim.position.set(-5, 4, -6); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const vd = await app.char('VOID'); scene.add(vd.root);
  { const pa = vd.hood.geometry.attributes.position, NS = 64, NC = NS + 1, NP = pa.count / NC;
    for (const j of [0, 4, 8, 12]) { const row = []; for (let i = 0; i < NP; i += 2) row.push(`${pa.getX(i * NC + j).toFixed(2)},${pa.getY(i * NC + j).toFixed(2)},${pa.getZ(i * NC + j).toFixed(2)}`); console.log('hood col', j, row.join(' ')); }
    const ff = vd.faceField.geometry.attributes.position; const r = []; for (let i = 0; i <= 36; i += 6) r.push(`${ff.getX(i).toFixed(2)},${ff.getY(i).toFixed(2)},${ff.getZ(i).toFixed(2)}`); console.log('face bottom', r.join(' '));
    console.log('headPivot', vd.headPivot.position.toArray().map((v) => v.toFixed(2)).join(','), 'headGroup', vd.headGroup.position.toArray().map((v) => v.toFixed(2)).join(','));
  }
  return { scene, vd, look: { bloom: 0.5, bloomThreshold: 0.85, exposure: 1.0 } };
}
export async function update(t, app, s) {
  const i = Math.max(0, Math.min(VIEWS.length - 1, Math.floor(t + 1e-6))), vr = Math.round((t - i) * 10);
  s.vd.fold && (s.vd.fold.mesh.visible = !(vr & 1)); s.vd.chinPlug.visible = !(vr & 2);
  if (!s.plug0) s.plug0 = [s.vd.chinPlug.scale.clone(), s.vd.chinPlug.position.clone()];
  if (vr & 4) { s.vd.chinPlug.scale.set(0.7, 0.3, 0.55); s.vd.chinPlug.position.set(0, -0.55, 0.18); } else { s.vd.chinPlug.scale.copy(s.plug0[0]); s.vd.chinPlug.position.copy(s.plug0[1]); }
  globalThis.__noChin = !!(vr & 8);
  const [p, l, fov, pose] = VIEWS[i];
  app.camera.position.set(...p); app.camera.up.set(0, 1, 0); app.camera.lookAt(...l); app.camera.fov = fov; app.camera.updateProjectionMatrix(); app.camera.updateMatrixWorld();
  s.vd.update(2.0, { face: VX('gentle'), ...pose });
}
