// Lab: SET BACKROOM — 10 camera angles, cage latch + door, janitor-corner crash, bucket hat + mop wig, rolling bucket,
// cosmos fade. Placeholder capsules for scale: VOID 3.0 m (indigo bell), FEAR 0.85 m (lavender bean), MAGICIAN 2.1 m.
// Segments (s): angles 0-12 (1.2 s each: wide reverse corner cage fearPOV lurk sideKick farCorner high latch),
// door 12-16, crash 16-26 (impact at 16.8, crashT = t - 16.8), hat 26-30.5, roll 30.5-33.5, cosmos 33.5-36.5.
//   node tools/render.js sheet --lab backroom --from 0.6 --to 11.4 --n 10 --cols 5 --out out/sheets/backroom_angles.jpg
//   node tools/render.js sheet --lab backroom --from 12 --to 16 --n 6 --cols 6 --out out/sheets/backroom_door.jpg
//   node tools/render.js sheet --lab backroom --from 16.2 --to 26 --n 16 --cols 8 --out out/sheets/backroom_crash.jpg
//   node tools/render.js sheet --lab backroom --from 26 --to 36.4 --n 12 --cols 6 --out out/sheets/backroom_end.jpg
//   exported `segments` = [[start, end, name], ...]
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { clamp, lerp, smooth, ease } from '../core/util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const sm = (a, b, x) => smooth((x - a) / (b - a));

const ANGLES = ['wide', 'reverse', 'corner', 'cage', 'fearPOV', 'lurk', 'sideKick', 'farCorner', 'high', 'latch'];
const SEGS = [...ANGLES.map((n) => [n, 1.2]), ['door', 4], ['crash', 10], ['hat', 4.5], ['roll', 3], ['cosmos', 3]];
export const segments = [];
{ let t0 = 0; for (const [n, d] of SEGS) { segments.push([t0, t0 + d, n]); t0 += d; } }
const segAt = (t) => { for (const s of segments) if (t >= s[0] && t < s[1]) return { name: s[2], u: t - s[0], d: s[1] - s[0] }; const s = segments[segments.length - 1]; return { name: s[2], u: t - s[0], d: s[1] - s[0] }; };

function label() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 64;
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.01), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, toneMapped: false }));
  m.renderOrder = 100; m.position.set(-0.03, -0.072, -0.3);
  let last = '';
  return { m, set(s) { if (s === last) return; last = s; const g = c.getContext('2d'); g.clearRect(0, 0, 512, 64); g.fillStyle = 'rgba(0,0,0,0.5)'; g.fillRect(0, 0, 512, 64); g.fillStyle = '#fff'; g.font = 'bold 34px sans-serif'; g.fillText(s, 14, 44); tex.needsUpdate = true; } };
}

function placeholders() {
  const std = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7, ...o });
  // VOID: plump bell 3.0 m, base radius 1.1, two eye dots on the front
  const vg = new THREE.Group();
  const prof = [[0.001, 3.0], [0.35, 2.92], [0.6, 2.6], [0.72, 2.1], [0.82, 1.6], [0.98, 1.0], [1.08, 0.45], [1.1, 0.08], [1.02, 0.0]].map(([x, y]) => new THREE.Vector2(x, y));
  const vb = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), std(0x1e1a44, { emissive: 0x120c30 })); vb.castShadow = true; vg.add(vb);
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 10), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.9, 1.0, 1.1) })); e.position.set(s * 0.2, 2.16, 0.66); e.scale.set(0.8, 1.1, 0.5); vg.add(e); }
  // FEAR: 0.85 lavender bean
  const fg = new THREE.Group();
  const fb = new THREE.Mesh(new THREE.CapsuleGeometry(0.21, 0.42, 6, 16), std(0xcab8ee, { emissive: 0x3a2a60 })); fb.position.y = 0.42; fb.castShadow = true; fg.add(fb);
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffffff })); e.position.set(s * 0.08, 0.64, 0.17); fg.add(e); }
  // MAGICIAN: 2.1 m stooped grey capsule + top hat; head group for the bucket
  const mg = new THREE.Group();
  const body = new THREE.Group(); mg.add(body);
  const mb = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 1.05, 6, 14), std(0x5e6678)); mb.position.y = 0.85; mb.castShadow = true; body.add(mb);
  const head = new THREE.Group(); head.position.set(0, 1.68, 0.2); body.add(head);
  const hm = new THREE.Mesh(new THREE.SphereGeometry(1, 18, 12), std(0xaeb3bf)); hm.scale.set(0.113, 0.166, 0.125); head.add(hm);   // magician skull size
  const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.12, 0.32, 16), std(0x262a36)); hat.position.y = 0.32; head.add(hat);
  const headTop = new THREE.Object3D(); headTop.position.y = 0.17; head.add(headTop);
  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.018, 0.09, 8), std(0xaeb3bf)); nose.rotation.x = Math.PI / 2; nose.position.set(0, 0.0, 0.16); head.add(nose);
  const legs = new THREE.Group(); mg.add(legs);
  for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.CapsuleGeometry(0.07, 0.7, 4, 10), std(0x4a5060)); l.rotation.set(Math.PI / 2 - 0.15, 0, s * 0.35); l.position.set(s * 0.17, 0.12, 0.3); legs.add(l); }
  return { vg, fg, mg, body, head, hat, headTop, legs };
}

export async function setup(app) {
  const set = await app.set('BACKROOM');
  const scene = set.scene;
  const P = placeholders();
  scene.add(P.vg, P.fg, P.mg);
  scene.add(app.camera);
  const lab = label(); app.camera.add(lab.m);
  return { scene, set, P, lab, look: set.look };
}

function sitMag(P, A, Y) {   // placeholder magician slumped sitting against the pile, legs splayed toward the room
  P.mg.position.copy(A.crashSpot); P.mg.rotation.y = Y.magicianCrash;
  P.body.rotation.set(-0.42, 0, 0.12); P.body.position.set(0, -0.62, -0.32); P.legs.visible = true; P.hat.visible = false;
}
const CORNER_SHOT = { pos: [3.7, 1.45, 1.15], look: [3.65, 0.36, -4.1], fov: 42, drift: 0 };
export async function update(t, app, S) {
  const seg = segAt(t), u = seg.u, set = S.set, P = S.P, A = set.anchors, Y = set.yaws;
  let shot = null, o = {};
  // default placements: Void at its spot, Fear outside the cage, magician lurking
  P.vg.position.copy(A.voidSpot); P.vg.rotation.set(0, Y.void, 0); P.vg.visible = true;
  P.fg.position.copy(A.fearOutside); P.fg.rotation.set(0, Y.fear, 0); P.fg.visible = true;
  P.mg.position.copy(A.lurkSpot); P.mg.rotation.set(0, Y.magicianLurk, 0); P.mg.visible = true;
  P.body.rotation.set(0.25, 0, 0); P.body.position.set(0, 0, 0); P.hat.visible = true; P.legs.visible = false;
  const c = A.cageCenter;
  const F = A.fearOutside, Vs = A.voidSpot;
  if (seg.name === 'wide') shot = framed([-0.5, 1.25, -0.9], { dist: 11, yaw: 6, pitch: 4, fov: 35, screenY: 0.47, drift: 0 });
  else if (seg.name === 'reverse') shot = { pos: [-0.9, 1.5, -4.4], look: [-1.6, 1.9, 10], fov: 46, drift: 0 };
  else if (seg.name === 'corner') { shot = CORNER_SHOT; P.mg.visible = false; }
  else if (seg.name === 'cage') { shot = framed([c.x, 0.6, c.z], { dist: 2.4, yaw: 14, pitch: 6, fov: 32, screenY: 0.5, drift: 0 }); P.fg.position.copy(A.cageInside); P.fg.rotation.y = Y.fearInCage - 0.7; }
  else if (seg.name === 'fearPOV') { shot = { pos: [F.x - 0.75, 0.55, F.z + 0.55], look: [Vs.x - 0.45, 2.05, Vs.z + 0.45], fov: 50, drift: 0 }; }
  else if (seg.name === 'lurk') shot = { pos: [2.95, 1.55, -2.4], look: [-1.2, 0.8, 0.3], fov: 38, drift: 0 };
  else if (seg.name === 'sideKick') shot = { pos: [6.6, 1.0, 5.8], look: [0.3, 1.45, -0.5], fov: 35, drift: 0 };
  else if (seg.name === 'farCorner') { shot = { pos: [-5.6, 3.1, -2.6], look: [3.7, 0.55, -4.25], fov: 34, drift: 0 }; }   // from the left wall, high: clears the Void
  else if (seg.name === 'high') shot = { pos: [-3.5, 7.5, 6.5], look: [1.0, 0.0, -2.0], fov: 45, drift: 0 };
  else if (seg.name === 'latch') { o.latch = sm(0.2, 1.0, u); const L = A.cageLatch; shot = framed([L.x, L.y + 0.05, L.z], { dist: 0.85, yaw: 38, pitch: 8, fov: 30, screenY: 0.5, drift: 0 }); P.vg.visible = false; P.fg.position.copy(A.cageInside); P.fg.rotation.y = Y.fearInCage; }
  else if (seg.name === 'door') {
    o.latch = sm(0.3, 1.2, u); o.cageDoor = sm(1.5, 3.6, u);
    P.fg.position.copy(A.cageInside); P.fg.rotation.y = Y.fearInCage;
    shot = framed([c.x + 0.15, 0.5, c.z + 0.15], { dist: 2.7, yaw: 62, pitch: 9, fov: 34, screenY: 0.5, drift: 0 });
  } else if (seg.name === 'crash') {
    // magician placeholder flies from lurkSpot (u 0..0.8), impact at u = 0.8, then crashT = u - 0.8
    const fl = clamp(u / 0.8);
    const tc = u - 0.8;
    if (tc < 0) {
      P.mg.position.copy(set.flightPos(fl)); P.body.rotation.set(-0.5 - 1.0 * fl, 0, 0); P.body.position.set(0, 0.2, 0);
      shot = { pos: [0.4, 3.3, 4.2], look: [2.7, 0.8, -2.9], fov: 42, drift: 0 };
    } else {
      sitMag(P, A, Y);
      o.crash = 1; o.crashT = tc; o.signOn = 0.3;
      // first the documented corner medium, then a low side view along the back wall (wringer clearance, puddle, sign)
      shot = tc < 5.0 ? CORNER_SHOT : { pos: [1.2, 0.75, -2.6], look: [3.95, 0.3, -4.35], fov: 40, drift: 0 };
    }
    P.hat.visible = tc < 0.3;
  } else if (seg.name === 'hat') {
    sitMag(P, A, Y);
    P.mg.updateMatrixWorld(true);
    const top = P.headTop.getWorldPosition(V(0, 0, 0)), q = P.head.getWorldQuaternion(new THREE.Quaternion()), up = V(0, 1, 0).applyQuaternion(q);
    o.crash = 1; o.crashT = 0.2 + u; o.signOn = 0.35;
    // default seat (lift 0.075: the nose clears under the rim) + the "bucket lifts an inch" peek on top
    o.bucketHat = { pos: top, up, yaw: 0, at: 1.0, lift: 0.075 + 0.035 * sm(3.0, 3.4, u) * (1 - sm(3.9, 4.3, u)) };
    o.mopWig = sm(1.4, 2.2, u);
    o.signFall = 0;
    // orbit stays INSIDE the room (camera x < 4.6, z > -4.8): -75 .. +18 deg around the head, from the room side
    const oy = (-75 + 93 * sm(2.4, 4.5, u)) * Math.PI / 180, od = 1.7;
    shot = { pos: [top.x + od * Math.sin(oy), top.y + 0.32, top.z + od * Math.cos(oy)], look: [top.x, top.y - 0.06, top.z], fov: 34, drift: 0 };
  } else if (seg.name === 'roll') {
    o.crash = 1; o.crashT = 12; o.rollBucket = sm(0.2, 2.8, u); o.signOn = 0.3;
    sitMag(P, A, Y);
    P.vg.visible = false; P.fg.visible = false;
    shot = { pos: [0.7, 2.6, 4.8], look: [0.7, 0.15, -3.9], fov: 54, drift: 0 };   // the whole path, corner -> rollEnd, in frame
  } else if (seg.name === 'cosmos') {
    o.cosmos = sm(0.2, 2.6, u); o.cageDoor = 1; o.latch = 1; o.crash = 1; o.crashT = 12;
    shot = framed([-0.2, 1.4, -0.6], { dist: 9.5, yaw: 10, pitch: 6, fov: 38, screenY: 0.47, drift: 0 });
  }
  set.update(t, o);
  applyShot(app.camera, shot, t);
  S.lab.set(`${seg.name}  ${u.toFixed(2)}s`);
  S.look = set.look;
}
