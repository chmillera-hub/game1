// Lab: SET 'EDGE' lighting check with the real JESUS + VOID rigs (faces must read). 2 s per shot.
//   node tools/render.js sheet --lab edge_cast --from 1 --to 15 --n 8 --cols 8 --out out/sheets/edge_cast.jpg
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { clamp } from '../core/util.js';
import { JX } from '../chars/jesus.js';
import { VX } from '../chars/void.js';

const SEG = 2;
const JP = [-0.45, 0, 0.35], VP = [1.25, 0, -0.45];
const SHOTS = [
  ['two-shot tod0', () => framed([0.35, 1.75, 0], { dist: 5.2, yaw: 3, pitch: 2, fov: 32, screenY: 0.4 }), { tod: 0 }],
  ['jesus MCU tod0', () => framed([JP[0], 1.55, JP[2]], { dist: 1.5, yaw: 10, pitch: 1, fov: 30, screenY: 0.34 }), { tod: 0 }],
  ['void low MCU voidSky .7', () => ({ pos: [0.6, 0.9, 3.4], look: [1.1, 2.15, -0.4], fov: 34 }), { tod: 0, voidSky: 0.7 }],
  ['jesus MCU tod1', () => framed([JP[0], 1.55, JP[2]], { dist: 1.5, yaw: -12, pitch: 1, fov: 30, screenY: 0.34 }), { tod: 1 }],
  ['reverse OTS tod.5', () => ({ pos: [1.6, 2.1, -3.6], look: [-0.5, 1.4, 0.9], fov: 32 }), { tod: 0.5 }],
  ['wide tod.3', () => ({ pos: [0.5, 1.6, 9.5], look: [0.0, 1.5, -10], fov: 38 }), { tod: 0.3 }],
  ['high on jesus kneel', () => ({ pos: [0.2, 3.2, 2.8], look: [-0.5, 0.6, 0.3], fov: 34 }), { tod: 0.2 }],
  ['walk-off tod1', () => ({ pos: [0.4, 1.85, 7.0], look: [-0.8, 1.5, -30], fov: 30 }), { tod: 1, walk: true }],
];
export async function setup(app) {
  const set = await app.set('EDGE');
  const jesus = await app.char('JESUS');
  const vd = await app.char('VOID');
  set.scene.add(jesus.root, vd.root);
  return { scene: set.scene, set, jesus, vd, look: set.look };
}
export async function update(t, app, s) {
  const i = clamp(Math.floor(t / SEG), 0, SHOTS.length - 1);
  const [, shot, o] = SHOTS[i];
  applyShot(app.camera, shot(), t);
  if (o.walk) {
    const a = s.set.pathAt(10 + t * 0.2), b = s.set.pathAt(10.3 + t * 0.2);
    const side = [a.dir[2], 0, -a.dir[0]];
    s.set.update(t, { ...o, shadowAt: a.pos });
    s.jesus.update(t, { pos: [a.pos[0] - side[0] * 0.5, a.pos[1], a.pos[2] - side[2] * 0.5], yaw: a.yaw, walk: { amount: 1, phase: t * 0.85 } });
    s.vd.update(t, { pos: [b.pos[0] + side[0] * 0.9, b.pos[1], b.pos[2] + side[2] * 0.9], yaw: b.yaw, walk: { amount: 1, phase: t * 1.0 } });
  } else {
    s.set.update(t, { ...o, voidPos: VP });
    const kneel = i === 6 ? 1 : 0;
    s.jesus.update(t, { pos: JP, yaw: 0.25, face: JX(i === 3 ? 'tender' : 'warm'), gaze: 'camera', body: { kneel } });
    s.vd.update(t, { pos: VP, yaw: -0.35, face: VX(i === 2 ? 'gentle' : 'calm'), gaze: i === 2 ? 'camera' : s.jesus });
  }
  s.look = { ...s.set.look };
}
