// Lab: SET 'EDGE' — "The Edge of the Mind". Placeholder capsule figures at the origin for scale.
//   node tools/render.js sheet --lab edge --from 0 --to 31 --n 32 --cols 8 --out out/sheets/edge_all.jpg
//   (each segment is 2 s; the sheet samples every segment. `segments` lists [start, end, name].)
import * as THREE from 'three';
import { applyShot, framed, orbitPos } from '../core/camera.js';
import { skin, cloth, hair, contactShadow } from '../core/materials.js';
import { clamp, lerp, smooth } from '../core/util.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const SEG = 2;

// ------------------------------------------------------------------ placeholder figures
function eyes(g, y, z, sep, r, color = 0x1a1210) {
  for (const sx of [-1, 1]) {
    const w = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), new THREE.MeshStandardMaterial({ color: 0xf6f0ea, roughness: 0.3 }));
    w.position.set(sx * sep, y, z); g.add(w);
    const p = new THREE.Mesh(new THREE.SphereGeometry(r * 0.55, 12, 8), new THREE.MeshBasicMaterial({ color }));
    p.position.set(sx * sep, y, z + r * 0.62); g.add(p);
  }
}
function human(h, body, skinC, hairC) {
  const g = new THREE.Group();
  const k = h / 1.75;
  const robe = new THREE.Mesh(new THREE.CapsuleGeometry(0.21 * k, 0.86 * k, 8, 20), cloth(body));
  robe.position.y = 0.66 * k; g.add(robe);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.135 * k, 32, 24), skin(skinC));
  head.position.y = 1.54 * k; g.add(head);
  const hr = new THREE.Mesh(new THREE.SphereGeometry(0.145 * k, 28, 18, 0, Math.PI * 2, 0, 1.5), hair(hairC));
  hr.position.y = 1.56 * k; hr.rotation.x = -0.45; g.add(hr);
  eyes(g, 1.56 * k, 0.115 * k, 0.047 * k, 0.026 * k);
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  const cs = contactShadow(0.7, 0.5, 0.35); g.add(cs);
  return g;
}
function seated(body, skinC, hairC) {
  const g = new THREE.Group();
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.19, 0.32, 8, 18), cloth(body));
  torso.position.set(0, 0.42, -0.08); torso.rotation.x = -0.3; g.add(torso);
  for (const sx of [-1, 1]) {
    const leg = new THREE.Mesh(new THREE.CapsuleGeometry(0.075, 0.5, 6, 12), cloth(0x2e3346));
    leg.rotation.x = Math.PI / 2 - 0.25; leg.position.set(sx * 0.1, 0.14, 0.24); g.add(leg);
  }
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.13, 32, 24), skin(skinC)); head.position.set(0, 0.84, -0.14); g.add(head);
  const hr = new THREE.Mesh(new THREE.SphereGeometry(0.14, 28, 18, 0, Math.PI * 2, 0, 1.5), hair(hairC)); hr.position.set(0, 0.86, -0.15); hr.rotation.x = -0.6; g.add(hr);
  const e = new THREE.Group(); eyes(e, 0, 0, 0.045, 0.027); e.position.set(0, 0.87, -0.04); e.rotation.x = -0.25; g.add(e);
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  g.add(contactShadow(0.8, 0.9, 0.35));
  return g;
}
function voidish() {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: 0x1e1a46, roughness: 0.6 });
  const body = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 28), cloth(0x1c1844, { rim: 1.4, rimColor: 0x8a6cff }));
  body.scale.set(1.05, 1.25, 0.95); body.position.y = 1.2; g.add(body);
  const hood = new THREE.Mesh(new THREE.SphereGeometry(0.62, 32, 24), cloth(0x1c1844, { rim: 1.6, rimColor: 0x6ad8ff }));
  hood.position.set(0, 2.45, 0.12); hood.scale.set(1, 1.05, 0.95); g.add(hood);
  const face = new THREE.Mesh(new THREE.SphereGeometry(0.46, 28, 20), new THREE.MeshBasicMaterial({ color: 0x05040e }));
  face.position.set(0, 2.38, 0.36); face.scale.set(1, 0.95, 0.6); g.add(face);
  for (const sx of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.085, 20, 14), new THREE.MeshBasicMaterial({ color: new THREE.Color(0xe8fbff).multiplyScalar(1.6) }));
    e.position.set(sx * 0.17, 2.44, 0.62); e.scale.set(1, 1.15, 0.5); g.add(e);
  }
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  g.add(contactShadow(2.4, 1.8, 0.4));
  void m;
  return g;
}

// ------------------------------------------------------------------ segments: [name, shot(u, S), opts(u), cast]
// cast: which placeholders are visible and where. JES = 1.75 human, USR = 1.65 human (standing or seated), VOID = 3 m
const SEGMENTS = [
  ['01 establishing wide  tod 0', () => ({ pos: [0.6, 1.7, 10.5], look: [-0.4, 1.6, -12], fov: 40 }), () => ({ tod: 0 }), 'all'],
  ['02 two-shot eye level  tod 0', (u) => framed([0.35, 1.55, 0], { dist: 4.6 - 0.3 * u, yaw: 4, pitch: 2, fov: 32, screenY: 0.36 }), () => ({ tod: 0 }), 'jv'],
  ['03 MCU face  tod 0', (u) => framed([-0.55, 1.56, 0.2], { dist: 1.7, yaw: 8 - 6 * u, pitch: 1, fov: 30, screenY: 0.33 }), () => ({ tod: 0 }), 'jv'],
  ['04 low angle up at Void  voidSky 1', (u) => ({ pos: [0.2 + 0.2 * u, 0.5, 3.6], look: [0.9, 2.5, 0], fov: 40 }), () => ({ tod: 0, voidSky: 1, voidPos: [1.25, 0, -0.5] }), 'jv'],
  ['05 high angle down on seated  tod 0', (u) => ({ pos: [0.3 + 0.15 * u, 3.3, 3.3], look: [-1.4, 0.4, 1.2], fov: 36 }), () => ({ tod: 0 }), 'all'],
  ['06 reverse (look +Z)  tod .5', (u) => ({ pos: [-0.2, 1.6, -5.4 + 0.2 * u], look: [-0.6, 1.25, 1.8], fov: 34 }), () => ({ tod: 0.5 }), 'all'],
  ['07 side (look -X)  tod .5', (u) => ({ pos: [7.5, 1.6, 1.2], look: [-2, 1.4, -0.6 - u * 0.5], fov: 34 }), () => ({ tod: 0.5 }), 'all'],
  ['08 walk-off  tod 1', (u) => ({ pos: [0.4, 1.85, 7.0], look: [-0.8, 1.5, -30], fov: 30 }), () => ({ tod: 1 }), 'walk'],
  ['09 walk-off tele  tod 1', (u) => ({ pos: [0.6, 1.7, 9], look: [-1.0, 2.5, -45], fov: 16 }), () => ({ tod: 1 }), 'walk'],
  ['10 tod sweep 0->1 wide', () => ({ pos: [0.6, 1.7, 10.5], look: [-0.4, 1.8, -12], fov: 40 }), (u) => ({ tod: u }), 'all'],
  ['11 voidSky sweep 0->1', (u) => framed([0.6, 1.9, 0], { dist: 6.5, yaw: -6, pitch: 4, fov: 34, screenY: 0.4 }), (u) => ({ tod: 0.25, voidSky: smooth(u), voidPos: [1.25, 0, -0.5] }), 'jv'],
  ['12 high establishing', () => ({ pos: [6, 9, 16], look: [-2, 0, -14], fov: 42 }), () => ({ tod: 0.3 }), 'all'],
  ['13 reverse low  tod 0 voidSky .6', () => ({ pos: [0.8, 0.6, -3.6], look: [0.2, 1.9, 2], fov: 38 }), () => ({ tod: 0, voidSky: 0.6, voidPos: [1.25, 0, -0.5] }), 'all'],
  ['14 sky up (stars)  tod 1', () => ({ pos: [0, 1.5, 4], look: [-1, 9, -6], fov: 45 }), () => ({ tod: 1 }), 'jv'],
  ['15 seeds x2  tod .2', (u) => framed([0.0, 1.5, 0], { dist: 5.5, yaw: 12, pitch: 2, fov: 34, screenY: 0.38 }), () => ({ tod: 0.2, seeds: 2 }), 'jv'],
  ['16 OTS user->jesus  tod .3', () => ({ pos: [-1.9, 1.15, 2.6], look: [-0.3, 1.4, 0], fov: 30 }), () => ({ tod: 0.3 }), 'all'],
];
export const segments = SEGMENTS.map((s, i) => [i * SEG, (i + 1) * SEG, s[0]]);
export const DURATION = SEGMENTS.length * SEG;

export async function setup(app) {
  const set = await app.set('EDGE');
  const scene = set.scene;
  const jes = human(1.75, 0xe8dcc4, 0xc8946c, 0x3a2416);
  const usr = human(1.65, 0x5a6f96, 0xf0c4a0, 0x3a2618);
  const usrSit = seated(0x5a6f96, 0xf0c4a0, 0x3a2618);
  const vd = voidish();
  const figs = new THREE.Group(); figs.add(jes, usr, usrSit, vd); scene.add(figs);
  // HUD label
  scene.add(app.camera);
  const lc = document.createElement('canvas'); lc.width = 1024; lc.height = 64;
  const ltex = new THREE.CanvasTexture(lc); ltex.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1, 1 / 16), new THREE.MeshBasicMaterial({ map: ltex, transparent: true, depthTest: false, toneMapped: false }));
  label.renderOrder = 999; label.position.set(0, -0.36, -1); label.scale.setScalar(0.36); app.camera.add(label);
  return { scene, set, jes, usr, usrSit, vd, figs, label, lc, ltex, lastLabel: '', look: set.look };
}

export async function update(t, app, s) {
  const i = clamp(Math.floor(t / SEG), 0, SEGMENTS.length - 1);
  const u = clamp((t - i * SEG) / SEG);
  const [name, shotFn, optsFn, cast] = SEGMENTS[i];
  const opts = optsFn(u);
  s.set.update(t, opts);
  // cast placement
  const { jes, usr, usrSit, vd } = s;
  jes.visible = usr.visible = usrSit.visible = vd.visible = false;
  if (cast === 'all' || cast === 'jv') {
    jes.visible = true; jes.position.set(-0.55, 0, 0.35); jes.rotation.y = 0.25;
    vd.visible = true; vd.position.set(1.25, 0, -0.5); vd.rotation.y = -0.3;
  }
  if (cast === 'all') { usrSit.visible = true; usrSit.position.set(-1.6, 0, 1.4); usrSit.rotation.y = 2.4; }
  if (cast === 'walk') {
    // two figures walking away along the path toward the glow
    const S = s.set;
    const a = S.pathAt(lerp(6, 14, u)), b = S.pathAt(lerp(6, 14, u) + 0.2);
    const side = [a.dir[2], 0, -a.dir[0]];
    jes.visible = true; jes.position.set(a.pos[0] - side[0] * 0.45, a.pos[1], a.pos[2] - side[2] * 0.45); jes.rotation.y = a.yaw;
    vd.visible = true; vd.position.set(b.pos[0] + side[0] * 0.9, b.pos[1], b.pos[2] + side[2] * 0.9); vd.rotation.y = b.yaw; vd.scale.setScalar(1);
  }
  applyShot(app.camera, shotFn(u), t);
  { const th = Math.tan(app.camera.fov * Math.PI / 360); s.label.position.set(0, -th * 0.9, -1); s.label.scale.setScalar(2 * th * app.camera.aspect); }
  s.look = { ...s.set.look };
  const txt = `${name}   t=${t.toFixed(2)}`;
  if (txt !== s.lastLabel) {
    s.lastLabel = txt;
    const g = s.lc.getContext('2d'); g.clearRect(0, 0, 1024, 64); g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(0, 0, 1024, 64);
    g.fillStyle = '#fff'; g.font = 'bold 34px sans-serif'; g.fillText(txt, 14, 44); s.ltex.needsUpdate = true;
  }
}
