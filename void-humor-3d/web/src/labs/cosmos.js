// Lab: SET 'COSMOS' — the reveal from inside a placeholder back room, the "looking up" hero angle past two
// placeholder capsules (Fear 0.85 m beside a 3 m Void), the standalone background scene, and an integration check
// inside the real BACKROOM set.
//   node tools/render.js sheet --lab cosmos --from 0.5 --to 11 --n 12 --cols 6 --out out/sheets/cosmos_revealA.jpg
//   node tools/render.js sheet --lab cosmos --from 12 --to 27 --n 8 --cols 4 --out out/sheets/cosmos_lookup.jpg
//   node tools/render.js sheet --lab cosmos --from 28 --to 39.5 --n 8 --cols 4 --out out/sheets/cosmos_standalone.jpg
//   node tools/render.js sheet --lab cosmos --from 40 --to 56 --n 8 --cols 4 --out out/sheets/cosmos_backroom.jpg
//   node tools/render.js sheet --lab cosmos --from 100 --to 109 --n 10 --cols 5 --out out/sheets/cosmos_survey.jpg
//   node tools/render.js bench --lab cosmos --t 24
// Segments (exported `segments`): [start, end, name]. Debug time ranges:
//   100–109 sky survey (8 horizontal directions, zenith, nadir; designed sky orientation, standalone),
//   200–209 same, shell only; 300–309 survey inside the placeholder room (floor veil); 400–404 aimed views;
//   9000+ empty-scene perf baseline (same camera); k*1000 + t = lab time t with debug variant k
//   (1 no puffs, 2 no fringe, 3 shell+floor only, 4 no capsules, 5 room without cosmos, 6 no floor veil,
//    7 no shell, 8 neither, 10 no stars, 11 no galaxies/glyphs, 12 no cosmos lights).
import * as THREE from 'three';
import { applyShot } from '../core/camera.js';
import { being, contactShadow } from '../core/materials.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { create as createCosmos } from '../sets/cosmos.js';

export const segments = [
  [0, 12, 'A: reveal from inside the room (front)'],
  [12, 22, 'B: reveal, looking up past Fear + Void'],
  [22, 28, 'C: hold, looking up (calm)'],
  [28, 36, 'D: standalone, slow orbit'],
  [36, 40, 'E: standalone, zenith / wide'],
  [40, 52, 'F: inside the real BACKROOM set (its cosmos fade + this group), reveal 0->1'],
  [52, 58, 'G: BACKROOM, looking up, full reveal'],
  [58, 64, 'H: real VOID + FEAR rigs in the standalone cosmos (front 3/4)'],
  [64, 70, 'I: real rigs, low camera looking up past them'],
];
const VOID_POS = [0.95, 0, -0.25], FEAR_POS = [-0.7, 0, 0.35];
const SRC = [0.95, 2.05, 0.55];   // the Void's chest (front)

function room() {
  // a plain stand-in for MIND_BACKROOM: 20 x 9 x 20 m box with shelves, a door, a lamp, a bucket
  const g = new THREE.Group();
  const wall = new THREE.MeshStandardMaterial({ color: 0x6a5e70, roughness: 0.92 });
  const floorM = new THREE.MeshStandardMaterial({ color: 0x4a3c3a, roughness: 0.8 });
  const wood = new THREE.MeshStandardMaterial({ color: 0x7a5a42, roughness: 0.8 });
  const W = 10, Hh = 9;
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(2 * W, 2 * W), floorM); fl.rotation.x = -Math.PI / 2; g.add(fl);
  const ce = new THREE.Mesh(new THREE.PlaneGeometry(2 * W, 2 * W), wall); ce.rotation.x = Math.PI / 2; ce.position.y = Hh; g.add(ce);
  for (const [x, z, ry] of [[0, -W, 0], [0, W, Math.PI], [-W, 0, Math.PI / 2], [W, 0, -Math.PI / 2]]) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(2 * W, Hh), wall); m.position.set(x, Hh / 2, z); m.rotation.y = ry; g.add(m);
  }
  for (let i = 0; i < 4; i++) {   // shelves on the back wall
    const s = new THREE.Mesh(new THREE.BoxGeometry(5, 0.12, 0.6), wood); s.position.set(-2.5 + (i % 2) * 6, 1.4 + i * 0.9, -W + 0.32); g.add(s);
    for (let k = 0; k < 4; k++) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.5, 0.4), new THREE.MeshStandardMaterial({ color: [0x8a6a9a, 0x5a7a8a, 0x9a7a5a, 0x7a8a6a][k], roughness: 0.9 }));
      b.position.set(s.position.x - 1.8 + k * 1.2, s.position.y + 0.31, -W + 0.4); g.add(b); }
  }
  const door = new THREE.Mesh(new THREE.BoxGeometry(1.6, 3.2, 0.1), wood); door.position.set(-6, 1.6, -W + 0.06); g.add(door);
  const bucket = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.24, 0.5, 20), new THREE.MeshStandardMaterial({ color: 0x8a96a8, metalness: 0.6, roughness: 0.4 }));
  bucket.position.set(4.5, 0.25, -3); g.add(bucket);
  const lampC = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 12), new THREE.MeshBasicMaterial({ color: 0xffd8a0 })); lampC.position.set(-1.5, 5.2, -2); g.add(lampC);
  const lamp = new THREE.PointLight(0xffc890, 14, 16, 1.6); lamp.position.copy(lampC.position); g.add(lamp);
  g.add(new THREE.HemisphereLight(0x8890b0, 0x2a2228, 0.55));
  const cool = new THREE.DirectionalLight(0xa8c0ff, 0.6); cool.position.set(3, 6, 8); g.add(cool);
  return { g, lamp, lampC };
}

function capsules() {
  const g = new THREE.Group();
  // VOID stand-in: 3.0 m, wide, deep indigo with violet rim
  const vm = being(0x1a1438, { rim: 1.6, rimColor: 0x8a6cff, glow: 0.15, fizz: 0.0, wrap: 0.2 });
  const v = new THREE.Mesh(new THREE.CapsuleGeometry(0.95, 1.1, 10, 32), vm); v.scale.set(1.08, 1, 1); v.position.set(VOID_POS[0], 1.5, VOID_POS[2]); g.add(v);
  for (const sx of [-1, 1]) {   // its two starlight eyes, looking up-ish
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 12), new THREE.MeshBasicMaterial({ color: 0xe8f6ff }));
    e.position.set(VOID_POS[0] + sx * 0.28, 2.3, VOID_POS[2] + 0.88); g.add(e);
  }
  // FEAR stand-in: 0.85 m lavender bean + mustard scarf ring
  const fm = being(0xcbb8f0, { rim: 1.0, rimColor: 0xe8dcff, glow: 0.25, fizz: 0.0 });
  const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 0.41, 8, 24), fm); f.position.set(FEAR_POS[0], 0.425, FEAR_POS[2]); g.add(f);
  const sc = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.05, 10, 24), new THREE.MeshStandardMaterial({ color: 0xd8a23a, roughness: 0.9 }));
  sc.rotation.x = Math.PI / 2; sc.position.set(FEAR_POS[0], 0.5, FEAR_POS[2]); g.add(sc);
  for (const sx of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.055, 14, 10), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    e.position.set(FEAR_POS[0] + sx * 0.08, 0.7, FEAR_POS[2] + 0.17); g.add(e);
    const p = new THREE.Mesh(new THREE.SphereGeometry(0.03, 10, 8), new THREE.MeshBasicMaterial({ color: 0x221a30 }));
    p.position.set(FEAR_POS[0] + sx * 0.08, 0.735, FEAR_POS[2] + 0.215); g.add(p);
    (g.userData.pupils ||= []).push({ p, x: FEAR_POS[0] + sx * 0.08 });
  }
  g.userData.lookUp = (u) => { for (const q of g.userData.pupils) q.p.position.set(q.x + 0.012 * u, 0.735 + 0.03 * u, FEAR_POS[2] + 0.215 - 0.012 * u); };
  const s1 = contactShadow(2.6, 2.2, 0.5); s1.position.set(VOID_POS[0], 0.006, VOID_POS[2]); g.add(s1);
  const s2 = contactShadow(0.7, 0.6, 0.5); s2.position.set(FEAR_POS[0], 0.006, FEAR_POS[2]); g.add(s2);
  return g;
}

export async function setup(app) {
  const cos = await createCosmos();
  const roomScene = new THREE.Scene(); roomScene.background = new THREE.Color(0x141018);
  const rm = room(); roomScene.add(rm.g);
  const caps = capsules();
  let br = null, rigs = null;
  try { br = await app.set('BACKROOM'); } catch (e) { console.log('cosmos lab: BACKROOM unavailable: ' + e.message); }
  try {
    const [vd, fr, vm, fm] = await Promise.all([app.char('VOID'), app.char('FEAR'), import('../chars/void.js'), import('../chars/fear.js')]);
    rigs = { vd, fr, VX: vm.VX, FX: fm.FX, mixFace: fm.mixFace };
  } catch (e) { console.log('cosmos lab: rigs unavailable: ' + e.message); }
  return { br, rigs, scene: roomScene, roomScene, rm, cos, caps, look: { ...cos.look } };
}

const sm = (a, b, x) => smooth((x - a) / (b - a));

// debug survey (t >= 100): 8 views around + up + down, standalone, no capsules. t in [100,110): full set;
// [200,210): shell only (no puffs, galaxies, glyphs); [300,310): reveal fronts 0.2..0.95 in the room.
function survey(t, app, s) {
  const { cos } = s;
  const base = Math.floor(t / 100) * 100, i = Math.floor(t - base);
  const dirs = base === 400 ? [[-15, 25], [-22, 38], [0, 10], [-10, 15], [10, 20], [-15, 25], [-15, 25], [-15, 25], [-15, 25], [-15, 25]] : base === 300 ? [[0, -20], [60, -25], [120, -20], [180, -30], [240, -20], [300, -25], [0, -45], [90, 10], [0, 40], [200, 30]]
    : [[0, 0], [45, 0], [90, 0], [135, 0], [180, 0], [225, 0], [270, 0], [315, 0], [0, 70], [0, -60]];
  const [yaw, pitch] = dirs[i % 10];
  const y = yaw * Math.PI / 180, p = pitch * Math.PI / 180;
  const pos = base === 300 ? [0.2, 1.4, 4.2] : [0.1, 1.5, 0.05];
  applyShot(app.camera, { pos, look: [pos[0] - Math.sin(y) * Math.cos(p), pos[1] + Math.sin(p), pos[2] - Math.cos(y) * Math.cos(p)], fov: 60, drift: 0 }, t);
  s.caps.position.set(0, 0, 0); s.caps.userData.lookUp(0.5);
  if (base === 300) { cos.attach(s.roomScene); s.scene = s.roomScene; s.roomScene.add(s.caps); s.rm.lampC.visible = false; }
  else { cos.attach(cos.scene); s.scene = cos.scene; s.scene.remove(s.caps); }
  const only = base === 200;
  cos.update(t, { reveal: 1, clock: 0, center: [0.1, 0, 0.05], source: SRC, radius: 7.5, puffs: only ? 0 : 1, galaxies: only ? 0 : 1, glyphs: only ? 0 : 1, stars: only ? 0 : 1 });
  s.look = { ...cos.look };
}

// F/G: integration check with the real BACKROOM set (capsules at its layout spots)
function inBackroom(t, app, s) {
  const { cos, caps, br } = s;
  const L = br.layout, vs = L.voidSpot, fo = L.fearOutside;
  const reveal = t < 52 ? sm(41, 50, t) : 1;
  const shot = t < 52 ? { pos: [-0.3, 1.4, 6.6], look: [-0.15, 1.85, -0.3], fov: 48, drift: 0.3 }
    : { pos: [fo.x - 1.2, 0.4, fo.z + 2.4], look: [vs.x + 1.2, 4.4, vs.z - 4.5], fov: 56, drift: 0.3 };
  applyShot(app.camera, shot, t);
  caps.position.set(vs.x - VOID_POS[0], 0, vs.z - VOID_POS[2]);   // Void capsule on the void spot (Fear near fearOutside)
  caps.userData.lookUp(t < 52 ? 0.4 * reveal : 1);
  br.scene.add(caps); cos.attach(br.scene); s.scene = br.scene;
  br.update(t, { cosmos: smooth(clamp(reveal / 0.8)) });
  const src = [vs.x, 2.05, vs.z + 0.8];
  cos.update(t, { reveal, center: [(vs.x + fo.x) / 2, 0, (vs.z + fo.z) / 2], source: src, radius: 9 });
  s.look = cos.blendLook(br.look, smooth(reveal));
}

// H/I: the real characters in the standalone cosmos (readability of faces against the sky)
function withRigs(t, app, s) {
  const { cos, rigs } = s;
  const { vd, fr, VX, FX, mixFace } = rigs;
  const shot = t < 64 ? { pos: [0.9, 1.45, 6.9], look: [0.1, 1.55, 0], fov: 40, drift: 0.3 }
    : { pos: [-1.6, 0.3, 2.9], look: [0.5, 4.2, -4.0], fov: 56, drift: 0.3 };
  applyShot(app.camera, shot, t);           // camera first (rigs read CTX.camera during update)
  cos.attach(cos.scene); s.scene = cos.scene; s.caps.removeFromParent();
  cos.scene.add(vd.root); cos.scene.add(fr.root);
  cos.update(t, { reveal: 1, center: [0.1, 0, 0.05], source: [0.7, 2.0, 0.3], radius: 7.5 });
  const up = t < 64 ? 0.55 : 1;
  const fface = mixFace(FX('wonder'), FX('awe'), 0.6); fface.gazePitch = 0.2 * up;
  fr.update(t, { pos: [-0.55, 0, 0.45], yaw: 0.35, face: fface, gaze: null, head: { pitch: -0.6 * up, roll: 0.04 }, body: { lean: -0.05 },
    extra: { cry: 0.3, glow: 1.3, tuftPerk: 0.3 }, armL: { preset: 'clasp' }, armR: { preset: 'clasp' } });
  vd.update(t, { pos: [0.75, 0, -0.45], yaw: -0.35, face: VX('tender'), gaze: fr, head: { pitch: 0.12 }, extra: { cosmos: 1 } });
  s.look = { ...cos.look };
}

export async function update(t, app, s) {
  if (t >= 9000 && t < 10000) {   // perf baseline: same camera, empty scene (post + readback only)
    if (!s.empty) { s.empty = new THREE.Scene(); s.empty.background = new THREE.Color(0x101018); }
    applyShot(app.camera, { pos: [0.35, 1.35, 6.6], look: [0.3, 1.95, 0], fov: 50, drift: 0 }, t);
    s.scene = s.empty; s.look = { ...s.cos.look }; return;
  }
  if (t >= 1000) { s.dbg = Math.floor(t / 1000); t = t % 1000; } else s.dbg = 0;
  if (t >= 100) return survey(t, app, s);
  if (s.rigs) { s.rigs.vd.root.removeFromParent(); s.rigs.fr.root.removeFromParent(); }
  if (t >= 58 && s.rigs) return withRigs(t, app, s);
  if (t >= 40 && s.br) return inBackroom(t, app, s);
  const { cos, caps } = s;
  const roomLook = { bloom: 0.45, bloomRadius: 0.55, bloomThreshold: 0.85, vignette: 0.3, sat: 1.04, exposure: 1.0 };
  let reveal = 1, shot, host = 'room';
  if (t < 12) {
    reveal = sm(0.5, 11, t);
    shot = { pos: [0.35, 1.35, 6.6], look: [0.3, 1.95, 0], fov: 50, drift: 0.3 };
  } else if (t < 22) {
    reveal = sm(12.5, 20.5, t);
    shot = { pos: [-2.0, 0.42, 3.3], look: [0.5, 4.4, -4.2], fov: 56, drift: 0.3 };
  } else if (t < 28) {
    const u = (t - 22) / 6;
    shot = { pos: [lerp(-2.0, -1.8, u), lerp(0.42, 0.5, u), lerp(3.3, 2.9, u)], look: [0.5, 4.4, -4.2], fov: 56, drift: 0.3 };
  } else if (t < 36) {
    host = 'alone';
    const a = lerp(-0.5, 0.9, (t - 28) / 8);
    shot = { pos: [Math.sin(a) * 6.2, 1.5, Math.cos(a) * 6.2], look: [0.1, 1.6, 0], fov: 40, drift: 0.3 };
  } else {
    host = 'alone';
    shot = t < 38 ? { pos: [0.3, 1.2, 1.6], look: [0.2, 9, -0.6], fov: 60, drift: 0.2 } : { pos: [0.5, 2.2, 6.8], look: [0.1, 2.6, -3], fov: 54, drift: 0.2 };
  }
  applyShot(app.camera, shot, t);
  caps.position.set(0, 0, 0);
  caps.userData.lookUp(t >= 12 && t < 28 ? 1 : 0.3 * smooth(reveal));   // Fear's placeholder eyes look up at the sky
  if (s.dbg === 4) { caps.removeFromParent(); }
  if (s.dbg === 5) { cos.group.removeFromParent(); s.roomScene.add(caps); s.scene = s.roomScene; }
  else if (host === 'room') { cos.attach(s.roomScene); if (s.dbg !== 4) s.roomScene.add(caps); s.scene = s.roomScene; }
  else { cos.attach(cos.scene); if (s.dbg !== 4) cos.scene.add(caps); s.scene = cos.scene; }
  const dbg = s.dbg === 1 ? { puffs: 0 } : s.dbg === 10 ? { stars: 0 } : s.dbg === 11 ? { galaxies: 0, glyphs: 0 } : s.dbg === 2 ? { fringe: 0 } : s.dbg === 3 ? { puffs: 0, fringe: 0, stars: 0, galaxies: 0, glyphs: 0 } : {};
  cos.update(t, { reveal, center: [0.1, 0, 0.05], source: SRC, radius: 7.5, ...dbg });
  if (s.dbg === 6) cos.props.floor.visible = false;
  if (s.dbg === 7) cos.props.dome.visible = false;
  if (s.dbg === 8) { cos.props.dome.visible = false; cos.props.floor.visible = false; }
  cos.props.key.visible = s.dbg !== 12;   // (reset every frame: frames stay pure)
  if (s.dbg === 12) cos.props.hemi.visible = false;
  // what the BACKROOM would do itself: its lamp (inside the sky shell) dims out as the cosmos arrives
  s.rm.lamp.intensity = 14 * (1 - 0.85 * smooth(reveal * 1.4)); s.rm.lampC.visible = reveal < 0.6;
  // post look: room look -> cosmos look as the reveal completes
  s.look = cos.blendLook(roomLook, host === 'room' ? smooth(reveal) : 1);
}
