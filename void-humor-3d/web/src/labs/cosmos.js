// Lab: SET 'COSMOS' — the reveal from inside a placeholder back room, the "looking up" hero angle past two
// placeholder capsules (Fear 0.85 m beside a 3 m Void), the standalone background scene, and an integration check
// inside the real BACKROOM set (the documented recipe: hostFade + dissolve) with the real VOID + FEAR rigs.
//   node tools/render.js sheet --lab cosmos --from 0.5 --to 11 --n 12 --cols 6 --out out/sheets/cosmos_revealA.jpg
//   node tools/render.js sheet --lab cosmos --from 12 --to 27 --n 8 --cols 4 --out out/sheets/cosmos_lookup.jpg
//   node tools/render.js sheet --lab cosmos --from 28 --to 39.5 --n 8 --cols 4 --out out/sheets/cosmos_standalone.jpg
//   node tools/render.js sheet --lab cosmos --from 40 --to 58 --n 8 --cols 4 --out out/sheets/cosmos_backroom.jpg
//   node tools/render.js sheet --lab cosmos --from 58 --to 69 --n 4 --cols 4 --out out/sheets/cosmos_rigs.jpg
//   node tools/render.js sheet --lab cosmos --from 100 --to 109 --n 10 --cols 5 --out out/sheets/cosmos_survey.jpg
//   node tools/render.js bench --lab cosmos --t 24
// Segments (exported `segments`): [start, end, name]. Frames of A–C and F–I print the screen position of both faces
// ("COSMOSPIX ..." console lines: [x, y] px of Fear's / the Void's eyes) so the camera recipes can be checked.
// Debug time ranges:
//   100–109 sky survey (8 horizontal directions, zenith, nadir; designed sky orientation, standalone),
//   200–209 same, shell only; 300–309 survey inside the placeholder room (floor veil); 400–404 aimed views;
//   9000+ empty-scene perf baseline (same camera); k*1000 + t = lab time t with debug variant k
//   (1 no puffs, 2 no fringe, 3 shell+floor only, 4 no capsules, 5 room without cosmos, 6 no floor veil,
//    7 no shell, 8 neither, 10 no stars, 11 no galaxies/glyphs, 12 no cosmos lights,
//    13 BACKROOM segments with BACKROOM alone (its own cosmos fade = hostFade(reveal), no COSMOS group) — perf A/B,
//    14 BACKROOM segments with the OLD recipe (cosmos: smooth(reveal/.8), no dissolve) — regression check).
import * as THREE from 'three';
import { applyShot, worldToScreen } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { being, contactShadow } from '../core/materials.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { create as createCosmos } from '../sets/cosmos.js';

export const segments = [
  [0, 12, 'A: reveal from inside the room (front two-shot)'],
  [12, 22, 'B: reveal, looking up past Fear + Void'],
  [22, 28, 'C: hold, looking up (calm)'],
  [28, 36, 'D: standalone, slow orbit'],
  [36, 40, 'E: standalone, zenith / wide'],
  [40, 52, 'F: inside the real BACKROOM (recipe: hostFade + dissolve), real rigs, reveal 0->1'],
  [52, 58, 'G: BACKROOM, looking up past the real rigs, full reveal'],
  [58, 64, 'H: real VOID + FEAR rigs in the standalone cosmos (front two-shot)'],
  [64, 70, 'I: real rigs, low camera looking up past them (hero shot)'],
];
const VOID_POS = [0.95, 0, -0.25], FEAR_POS = [-0.7, 0, 0.35];
const SRC = [0.95, 2.05, 0.55];   // the Void's chest (front)

// ---- camera recipes (documented in docs/sets/cosmos.md; checked with COSMOSPIX screen positions)
// front two-shot from inside (capsules / rigs at the positions above): Fear's eyes ~y 760, the Void's eyes ~y 400
export const TWO_SHOT = { pos: [0.3, 0.95, 7.0], look: [0.25, 1.38, 0], fov: 46 };
// hero "looking up past Fear + the Void": Fear's upturned face ~y 720–780, both Void eyes in frame, hero galaxy top half
export const HERO_SHOT = { pos: [-1.3, 0.3, 4.0], look: [-0.03, 1.34, -0.72], fov: 60 };

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
  // a host sets EYE_LIGHT every frame (frames are rendered out of order)
  const eye = () => { EYE_LIGHT.uKeyDir.value.set(3, 6, 8).normalize(); EYE_LIGHT.uKeyColor.value.setRGB(0.9, 0.92, 1.0); EYE_LIGHT.uAmbient.value.setRGB(0.5, 0.5, 0.58); };
  return { g, lamp, lampC, eye };
}

function capsules() {
  const g = new THREE.Group();
  // VOID stand-in: 3.0 m, wide, deep indigo with violet rim
  const vm = being(0x1a1438, { rim: 1.6, rimColor: 0x8a6cff, glow: 0.15, fizz: 0.0, wrap: 0.2 });
  const v = new THREE.Mesh(new THREE.CapsuleGeometry(0.95, 1.1, 10, 32), vm); v.scale.set(1.08, 1, 1); v.position.set(VOID_POS[0], 1.5, VOID_POS[2]); g.add(v);
  g.userData.vEyes = [];
  for (const sx of [-1, 1]) {   // its two starlight eyes; the face turned toward Fear (yaw -0.5, like the rig)
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 12), new THREE.MeshBasicMaterial({ color: 0xe8f6ff }));
    const c = Math.cos(-0.5), sn = Math.sin(-0.5), x = sx * 0.28, z = 0.9;
    e.position.set(VOID_POS[0] + x * c + z * sn, 2.3, VOID_POS[2] - x * sn + z * c); g.add(e); g.userData.vEyes.push(e);
  }
  // FEAR stand-in: 0.85 m lavender bean + mustard scarf ring
  const fm = being(0xcbb8f0, { rim: 1.0, rimColor: 0xe8dcff, glow: 0.25, fizz: 0.0 });
  const f = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 0.41, 8, 24), fm); f.position.set(FEAR_POS[0], 0.425, FEAR_POS[2]); g.add(f);
  const sc = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.05, 10, 24), new THREE.MeshStandardMaterial({ color: 0xd8a23a, roughness: 0.9 }));
  sc.rotation.x = Math.PI / 2; sc.position.set(FEAR_POS[0], 0.5, FEAR_POS[2]); g.add(sc);
  g.userData.fEyes = [];
  for (const sx of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.055, 14, 10), new THREE.MeshBasicMaterial({ color: 0xffffff }));
    e.position.set(FEAR_POS[0] + sx * 0.08, 0.7, FEAR_POS[2] + 0.17); g.add(e); g.userData.fEyes.push(e);
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
const px = (cam, v) => worldToScreen(cam, v).slice(0, 2).map(Math.round);
const W3 = (o) => o.getWorldPosition(new THREE.Vector3());
// screen positions of both faces (each eye) — "COSMOSPIX t seg fear:[[x,y],[x,y]] void:[[x,y],[x,y]]"
function logPix(t, seg, cam, fearEyes, voidEyes) {
  console.log(`COSMOSPIX ${t.toFixed(2)} ${seg} fear:${JSON.stringify(fearEyes.map((v) => px(cam, v)))} void:${JSON.stringify(voidEyes.map((v) => px(cam, v)))}`);
}
const rigEyes = (s) => ({ f: [s.rigs.fr.anchor('eyeL'), s.rigs.fr.anchor('eyeR')], v: s.rigs.vd.face.eyes.map((e) => W3(e.group)) });

// debug survey (t >= 100): 8 views around + up + down, standalone, no capsules. t in [100,110): full set;
// [200,210): shell only (no puffs, galaxies, glyphs); [300,310): inside the room (floor veil); [400,410): aimed views.
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
  if (base === 300) { cos.attach(s.roomScene); s.scene = s.roomScene; s.roomScene.add(s.caps); s.rm.lampC.visible = false; s.rm.eye(); }
  else { cos.attach(cos.scene); s.scene = cos.scene; s.scene.remove(s.caps); }
  const only = base === 200;
  cos.update(t, { reveal: 1, clock: 0, center: [0.1, 0, 0.05], source: SRC, radius: 7.5, puffs: only ? 0 : 1, galaxies: only ? 0 : 1, glyphs: only ? 0 : 1, stars: only ? 0 : 1 });
  s.look = { ...cos.look };
}

// F/G: integration with the real BACKROOM set and the real rigs — THE DOCUMENTED RECIPE
function inBackroom(t, app, s) {
  const { cos, br, rigs } = s;
  const L = br.layout, vs = L.voidSpot, fo = L.fearOutside;
  const reveal = t < 52 ? sm(41, 50, t) : 1;
  const mid = [(vs.x + fo.x) / 2, 0, (vs.z + fo.z) / 2];
  // F: front two-shot of the pair (Fear's eyes ~y 760, the Void's ~y 420); G: looking up past them
  const shot = t < 52 ? { pos: [mid[0] - 0.05, 0.95, mid[2] + 6.6], look: [mid[0] - 0.05, 1.4, mid[2] - 0.2], fov: 46, drift: 0.3 }
    : { pos: [fo.x - 0.67, 0.3, fo.z + 2.77], look: [fo.x + 0.51, 1.34, fo.z - 1.98], fov: 56, drift: 0.3 };
  applyShot(app.camera, shot, t);
  s.scene = br.scene; s.caps.removeFromParent();
  const old = s.dbg === 14, alone = s.dbg === 13;
  // the room: its own fade CAPPED by hostFade (keeps its floor, never hard-toggles the bulbs), bulbs dim as the
  // front approaches them, shafts/dust out; walls + bulb cords open with the cosmos front (dissolve)
  br.update(t, old ? { cosmos: smooth(clamp(reveal / 0.8)) } : {
    cosmos: cos.hostFade(reveal), shafts: 1 - sm(0, 0.6, reveal), dust: 1 - sm(0, 0.6, reveal),
    lights: { bulb: 1 - sm(0.12, 0.4, reveal), bulb2: 1 - sm(0.12, 0.4, reveal) },
  });
  if (!old && !alone && !s.dissolved) {   // one-time patch (idempotent): room fade twins + the two bulb pendants
    cos.dissolve(br.props.room);
    cos.dissolve([br.props.bulb.parent, br.props.bulb2.parent], { opaque: true });
    s.dissolved = true;
  }
  if (rigs) {
    const { vd, fr, VX, FX, mixFace } = rigs;
    br.scene.add(vd.root); br.scene.add(fr.root);
    const up = t < 52 ? sm(42, 48, t) : 1;
    const fface = mixFace(FX('wonder'), FX('awe'), 0.3 + 0.4 * up); fface.gazePitch = 0.22 * up;
    fr.update(t, { pos: [fo.x + 0.05, 0, fo.z], yaw: lerp(2.0, 0.55, up), face: fface, gaze: null,
      head: { pitch: -0.55 * up, roll: 0.04 }, extra: { cry: 0.35 * up, glow: 1.2, tuftPerk: 0.3 }, armL: { preset: 'clasp' }, armR: { preset: 'clasp' } });
    vd.update(t, { pos: [vs.x, 0, vs.z], yaw: lerp(-0.8, -0.45, up), face: VX('tender'), gaze: fr, head: { pitch: 0.1 }, extra: { cosmos: reveal } });
    const e = rigEyes(s); logPix(t, t < 52 ? 'F' : 'G', app.camera, e.f, e.v);
  }
  if (!alone) {
    cos.attach(br.scene);
    cos.update(t, { reveal, center: mid, source: (rigs && rigs.vd.anchor('chest')) || [vs.x, 2.05, vs.z + 0.8], radius: 9 });
  } else cos.group.removeFromParent();
  s.look = alone ? { ...br.look } : cos.blendLook(br.look, smooth(reveal));
}

// H/I: the real characters in the standalone cosmos (readability of faces against the sky)
function withRigs(t, app, s) {
  const { cos, rigs } = s;
  const { vd, fr, VX, FX, mixFace } = rigs;
  const shot = t < 64 ? { ...TWO_SHOT, drift: 0.3 } : { ...HERO_SHOT, drift: 0.3 };
  applyShot(app.camera, shot, t);           // camera first (rigs read CTX.camera during update)
  cos.attach(cos.scene); s.scene = cos.scene; s.caps.removeFromParent();
  cos.scene.add(vd.root); cos.scene.add(fr.root);
  cos.update(t, { reveal: 1, center: [0.1, 0, 0.05], source: [0.95, 2.0, 0.3], radius: 7.5 });
  const up = t < 64 ? 0.55 : 1;
  const fface = mixFace(FX('wonder'), FX('awe'), 0.6); fface.gazePitch = 0.2 * up;
  // H: Fear looks up toward the sky above the camera; I: up at the hero galaxy (eyes roll up-left, the head follows)
  fr.update(t, { pos: [FEAR_POS[0], 0, FEAR_POS[2]], yaw: t < 64 ? 0.3 : 0.15, face: fface, gaze: t < 64 ? null : cos.anchors.hero,
    head: { pitch: -0.6 * up, yaw: t < 64 ? 0 : -0.25, roll: 0.04 }, body: { lean: -0.05 },
    extra: { cry: 0.3, glow: 1.3, tuftPerk: 0.3 }, armL: { preset: 'clasp' }, armR: { preset: 'clasp' } });
  vd.update(t, { pos: [VOID_POS[0], 0, VOID_POS[2]], yaw: t < 64 ? -0.35 : -0.5, face: VX('tender'), gaze: fr, head: { pitch: 0.12 }, extra: { cosmos: 1 } });
  const e = rigEyes(s); logPix(t, t < 64 ? 'H' : 'I', app.camera, e.f, e.v);
  s.look = { ...cos.look };
}

export async function update(t, app, s) {
  if (t >= 9000 && t < 10000) {   // perf baseline: same camera, empty scene (post + readback only)
    if (!s.empty) { s.empty = new THREE.Scene(); s.empty.background = new THREE.Color(0x101018); }
    applyShot(app.camera, { ...TWO_SHOT, drift: 0 }, t);
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
    shot = { ...TWO_SHOT, drift: 0.3 };
  } else if (t < 22) {
    reveal = sm(12.5, 20.5, t);
    shot = { ...HERO_SHOT, drift: 0.3 };
  } else if (t < 28) {
    const u = (t - 22) / 6;   // slow push-in, the framing stays put
    shot = { pos: HERO_SHOT.pos.map((x, i) => lerp(x, HERO_SHOT.look[i], 0.06 * u)), look: HERO_SHOT.look, fov: HERO_SHOT.fov, drift: 0.3 };
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
  if (t < 28) logPix(t, t < 12 ? 'A' : t < 22 ? 'B' : 'C', app.camera, caps.userData.fEyes.map(W3), caps.userData.vEyes.map(W3));
  if (s.dbg === 4) { caps.removeFromParent(); }
  if (host === 'room') s.rm.eye();
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
