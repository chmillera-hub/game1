// TEMP probe for s20 kick geometry (delete when done)
import * as THREE from 'three';
import { ROOM } from '../scenes/marks.js';
import { marks } from '../scenes/kit_s20_22.js';
export async function setup(app) {
  const set = await app.set('BACKROOM');
  ROOM.fit(set);
  const vd = await app.char('VOID'), mag = await app.char('MAGICIAN');
  set.scene.add(vd.root, mag.root);
  const M = marks();
  const f = (v) => (v ? [v.x ?? v[0], v.y ?? v[1], v.z ?? v[2]].map((x) => +x.toFixed(3)) : null);
  const P = (q) => JSON.stringify(q);
  const tipOf = (kP, ky) => kP * (0.42 + 0.16 * Math.min(1, Math.max(0, (ky - 1.1) / 0.6)));
  const kickAt = (tg) => {
    vd.update(1, { pos: M.V, yaw: M.yV, head: { pitch: 0.25, yaw: 0.3 }, body: { lean: 0.02, pitch: -tipOf(1, tg[1]) }, extra: { kick: 1, kickSide: 'L', kickTarget: tg, kickLevel: 1 } });
    return vd.anchor('kickFoot').clone();
  };
  const axis = new THREE.Vector3(M.V[0], 0, M.V[2]);
  const rr = (p) => Math.hypot(p.x - axis.x, p.z - axis.z);
  for (const yaw of [-0.9, -0.6, -0.35, -0.1]) for (const [lean, crouch, peek, hunch] of [[1.15, 0.2, 0, 0.2], [1.3, 0.25, 0.4, 0.2]]) {
    const pose = (root) => ({ pos: root, yaw, body: { lean, crouch, peek, hunch }, head: { pitch: -0.35 }, armR: { preset: 'dagger_ready' }, armL: { preset: 'pouch' } });
    let root = [1.75, 0, -0.75], F = null, C = null;
    for (let i = 0; i < 6; i++) {
      mag.update(1, pose(root)); C = mag.anchor('chest').clone();
      F = kickAt([C.x, C.y, C.z]);
      root = [root[0] + (F.x - C.x), 0, root[2] + (F.z - C.z)];
    }
    mag.update(1, pose(root)); C = mag.anchor('chest').clone();
    const H = mag.anchor('head').clone(), E = mag.anchor('eyes').clone(), hat = mag.anchor('hat').clone();
    console.log('yaw', yaw, 'lean', lean, 'peek', peek, 'root', P(f(new THREE.Vector3(...root))), 'chest', P(f(C)), 'foot', P(f(F)), 'err', C.distanceTo(F).toFixed(3), 'head', P(f(H)), 'rHead', rr(H).toFixed(2), 'rChest', rr(C).toFixed(2), 'eyes', P(f(E)), 'rEyes', rr(E).toFixed(2), 'hat', P(f(hat)), 'rHat', rr(hat).toFixed(2));
  }
  return { scene: set.scene, look: {} };
}
export async function update(t, app, s) { app.camera.position.set(2, 1.2, 7); app.camera.lookAt(1, 1.2, 0); }
