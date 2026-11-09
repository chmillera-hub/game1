// Lab: JESUS — turntable (0–4 s), expression sheet (1 s each), then key poses / actions with placeholder
// partners (a big plump "Void" stand-in, a seated person, a floating notification).
//   node tools/render.js sheet --lab jesus --from 0 --to 4 --n 8 --cols 4 --out out/sheets/jesus_turn.jpg
//   node tools/render.js stills --lab jesus --t 4.5,5.5 ...      (see SEGMENTS printed in the label)
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { glowSprite } from '../core/materials.js';
import { JX } from '../chars/jesus.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const seg = [];
let T0 = 0;
function S(name, dur, fn) { seg.push({ name, t0: T0, t1: T0 + dur, fn }); T0 += dur; }

// synthetic lip-sync for talking demos
const talkSample = (t, k = 1) => {
  const o = Math.max(0, Math.sin(t * 11.3) * 0.55 + Math.sin(t * 4.1 + 1) * 0.3 + 0.1) * (0.55 + 0.45 * noise1(t * 2.5, 7));
  return { open: clamp(o * k, 0, 0.75), wide: 0.3 + 0.3 * noise1(t * 3, 9), round: clamp(0.4 * noise1(t * 2.2, 11)), close: o < 0.08 ? 0.6 : 0 };
};
const ramp = (lt, a, b) => smooth((lt - a) / (b - a));

// ---------------------------------------------------------------------------------- expression sheet
const EX = [
  ['kind (default)', { face: 'kind' }],
  ['warm smile', { face: 'warm' }],
  ['beaming', { face: 'beam' }],
  ['laugh', { face: 'laugh', body: { giggle: 0.6 } }],
  ['teehee', { face: 'teehee', body: { giggle: 1, shrug: 0.45 }, armR: { preset: 'teehee' } }],
  ['listening (nods)', { face: 'listening', nod: 1, head: { roll: 0.1 } }],
  ['whisper', { face: 'whisper', armR: { preset: 'whisper' }, head: { yaw: 0.45, roll: -0.08 }, body: { lean: 0.08, tilt: 0.06 } }],
  ['amused', { face: 'amused', head: { roll: -0.06 } }],
  ['awkward (darting)', { face: 'awkward', dart: 1, body: { shrug: 0.75 } }],
  ['compassion', { face: 'compassion', head: { roll: 0.08 } }],
  ['tender', { face: 'tender', head: { roll: 0.1 } }],
  ['hopeful', { face: 'hopeful', armL: { preset: 'clasp_chest' }, armR: { preset: 'clasp_chest' }, head: { roll: -0.1 } }],
  ['eager', { face: 'eager', body: { lean: 0.06 } }],
  ['surprised', { face: 'surprised', body: { recoil: 0.3 } }],
  ['ooh', { face: 'ooh', head: { pitch: -0.15 } }],
  ['curious', { face: 'curious', head: { roll: 0.14 } }],
  ['reading (squint)', { face: 'reading', head: { pitch: 0.12 }, body: { lean: 0.08 } }],
  ['shrug "eh"', { face: 'shrug', body: { shrug: 0.85 }, armL: { preset: 'shrug' }, armR: { preset: 'shrug' } }],
  ['rueful', { face: 'rueful', head: { roll: 0.06 } }],
  ['sad smile', { face: 'sadSmile' }],
  ['wince', { face: 'wince', body: { shrug: 0.3 } }],
  ['content (eyes half)', { face: 'content', head: { pitch: -0.1 } }],
  ['holding in a laugh', { face: 'pressed', body: { giggle: 0.35 } }],
  ['heart / sincere', { face: 'tender', armR: { preset: 'heart' } }],
  ['talking (lip-sync)', { face: 'kind', talk: 1, armR: { preset: 'explain' } }],
];

S('turntable', 4, (lt, s, app) => {
  s.jesus.update(s.t, { yaw: (lt / 4) * Math.PI * 2, face: 'kind', gaze: null });
  return { shot: framed([0, 0.92, 0], { dist: 4.3, yaw: 0, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }) };
});
for (const [name, e] of EX) {
  S('expr: ' + name, 1, (lt, s, app) => {
    const t = s.t;
    const head = { ...(e.head || {}) };
    if (e.nod) head.pitch = (head.pitch || 0) + 0.12 * Math.max(0, Math.sin(lt * Math.PI * 2 * 1.6));
    const pose = { face: e.face, dart: e.dart, body: e.body, armL: e.armL, armR: e.armR, head, gaze: 'camera' };
    if (e.talk) pose.speech = talkSample(t); else pose.speech = false;
    if (name.startsWith('whisper')) pose.gaze = V(0.6, 1.55, 0.6);
    if (name.startsWith('awkward')) pose.gaze = null;
    if (name.startsWith('reading')) pose.gaze = V(0.0, 1.25, 0.5);
    if (name.startsWith('ooh')) pose.gaze = V(-0.2, 2.4, 1.2);
    s.jesus.update(t, pose);
    return { shot: framed([0, 1.47, 0], { dist: 1.25, yaw: 8, pitch: 2, fov: 30, screenY: 0.36, drift: 0 }) };
  });
}

// ---------------------------------------------------------------------------------- actions
S('idle', 2.5, (lt, s) => {
  s.jesus.update(s.t, { face: 'kind', gaze: 'camera', armL: { preset: 'clasp' }, armR: { preset: 'clasp' } });
  return { shot: framed([0, 0.95, 0], { dist: 4.0, yaw: 20, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }) };
});
S('calm walk (3/4)', 3, (lt, s) => {
  const J = s.jesus, rate = J.walkRate('walk'), sp = J.walkSpeed('walk') * rate;
  const z = -1.2 + sp * lt;
  J.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'walk' }, face: 'content', gaze: V(0, 1.5, z + 3) });
  return { shot: framed([0, 0.95, z], { dist: 4.2, yaw: 35, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }) };
});
S('calm walk (side), hands behind', 3, (lt, s) => {
  const J = s.jesus, rate = J.walkRate('stroll'), sp = J.walkSpeed('stroll') * rate;
  const z = -1.2 + sp * lt;
  J.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'stroll' }, face: 'content', head: { pitch: -0.12 }, armL: { preset: 'behind' }, armR: { preset: 'behind' } });
  return { shot: framed([0, 0.95, z], { dist: 4.2, yaw: 88, pitch: 2, fov: 32, screenY: 0.44, drift: 0 }) };
});
S('run (side)', 2, (lt, s) => {
  const J = s.jesus, rate = J.walkRate('run'), sp = J.walkSpeed('run') * rate;
  const z = -2 + sp * lt;
  J.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'run' }, face: ['eager', 0.5] });
  return { shot: framed([0, 0.95, z], { dist: 4.4, yaw: 80, pitch: 2, fov: 32, screenY: 0.44, drift: 0 }) };
});
S('kneel to a seated person, open palms', 6, (lt, s) => {
  const kn = ramp(lt, 0.3, 1.6) - ramp(lt, 5.0, 5.9);
  const open = ramp(lt, 1.2, 1.9) * (1 - ramp(lt, 4.9, 5.5));
  const talking = lt > 2.2 && lt < 4.6;
  s.jesus.update(s.t, {
    yaw: 0, body: { kneel: kn }, face: talking ? 'tender' : 'kind', gaze: s.seated.userData.eyes,
    head: { follow: 0.6 }, speech: talking ? talkSample(s.t, 0.8) : false,
    armL: { preset: [['knee_rest', 0.6], ['open', 0.4]], reach: open, hand: { splay: 0.08, cup: 0.45 } },
    armR: { preset: talking ? 'explain' : 'open', reach: open, hand: { splay: 0.08, cup: 0.45 } },
  });
  s.seated.visible = true;
  return { shot: framed([0.1, 0.8, 0.3], { dist: 3.4, yaw: 62, pitch: 4, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('arm around big partner + whisper', 5, (lt, s) => {
  s.big.visible = true;
  const B = s.big.userData;
  const around = ramp(lt, 0.2, 1.0);
  const wh = ramp(lt, 1.6, 2.2) * (1 - ramp(lt, 4.3, 4.8));
  s.jesus.update(s.t, {
    face: wh > 0.5 ? 'whisper' : 'warm', gaze: wh > 0.3 ? B.ear : B.eye,
    head: { follow: 0.75, roll: -0.1 * wh }, body: { tilt: 0.1 * wh, lean: 0.05 * wh, tiptoe: 0.8 * wh },
    speech: wh > 0.6 ? { open: 0.12 + 0.1 * Math.max(0, Math.sin(s.t * 13)), wide: 0.2, round: 0.5, close: 0 } : false,
    armL: { preset: 'around', target: B.back, reach: around },
    armR: { preset: 'whisper', reach: wh },
  });
  return { shot: lt < 2.0 ? framed([0.3, 1.3, -0.1], { dist: 3.3, yaw: 205, pitch: 6, fov: 32, screenY: 0.4, drift: 0 })
    : framed([0.1, 1.5, 0.05], { dist: 1.8, yaw: 18, pitch: 3, fov: 30, screenY: 0.38, drift: 0 }) };
});
S('listening nods (head.pitch)', 3, (lt, s) => {
  s.big.visible = true;
  const B = s.big.userData;
  s.jesus.update(s.t, {
    face: 'listening', gaze: B.eye, head: { follow: 0.85, roll: 0.12, pitch: 0.13 * Math.max(0, Math.sin(lt * Math.PI * 2 * 1.3)) },
    armL: { preset: 'around', target: B.back }, armR: { preset: 'rest' },
  });
  return { shot: framed([0.15, 1.45, 0], { dist: 2.0, yaw: -30, pitch: 2, fov: 30, screenY: 0.38, drift: 0 }) };
});
S('hand on shoulder', 3, (lt, s) => {
  s.big.visible = true;
  s.big.position.set(0.35, 0, 0.92); s.big.rotation.y = 0;                 // in front, back turned to Jesus
  s.big.updateMatrixWorld(true);
  const sh = V(-0.5, 1.5, -0.56).applyMatrix4(s.big.matrixWorld), eye = V(-0.45, 1.8, -0.2).applyMatrix4(s.big.matrixWorld);
  const r = ramp(lt, 0.2, 1.0);
  s.jesus.update(s.t, { face: lt > 1.4 ? 'tender' : 'kind', gaze: eye, head: { follow: 0.5, pitch: lt > 1.8 && lt < 2.5 ? 0.12 : 0 },
    armR: { preset: 'shoulder', target: sh, reach: r }, body: { tiptoe: 0.3 * r, lean: 0.06 * r } });
  return { shot: framed([0.0, 1.35, 0.35], { dist: 3.2, yaw: -75, pitch: 3, fov: 32, screenY: 0.4, drift: 0 }) };
});
S('shrug, palms up', 2.5, (lt, s) => {
  const a = ramp(lt, 0.2, 0.7) * (1 - ramp(lt, 2.0, 2.4));
  s.jesus.update(s.t, { face: a > 0.4 ? 'shrug' : 'kind', gaze: 'camera', body: { shrug: 0.85 * a }, armL: { preset: 'shrug', reach: a }, armR: { preset: 'shrug', reach: a }, head: { roll: 0.1 * a } });
  return { shot: framed([0, 1.15, 0], { dist: 2.6, yaw: 10, pitch: 2, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('look at a floating notification', 3, (lt, s) => {
  s.note.visible = true;
  const np = s.note.position;
  const read = ramp(lt, 0.4, 0.9);
  s.jesus.update(s.t, { face: lt < 1.6 ? ['reading', read] : 'surprised', gaze: np, head: { look: np, follow: 0.7 * read }, body: { lean: 0.05 * read } });
  return { shot: framed([-0.12, 1.62, 0.2], { dist: 2.7, yaw: 28, pitch: -2, fov: 32, screenY: 0.4, drift: 0 }) };
});
S('teehee', 2.5, (lt, s) => {
  const a = ramp(lt, 0.15, 0.5) * (1 - ramp(lt, 2.1, 2.45));
  s.jesus.update(s.t, { face: a > 0.3 ? 'teehee' : 'warm', body: { giggle: a, shrug: 0.4 * a }, armR: { preset: 'teehee', reach: a }, gaze: 'camera', head: { roll: 0.12 * a } });
  return { shot: framed([0, 1.35, 0], { dist: 1.9, yaw: 12, pitch: 2, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('awkward grimace, eyes darting', 3, (lt, s) => {
  const a = ramp(lt, 0.2, 0.7);
  s.jesus.update(s.t, { face: ['awkward', a], dart: a, body: { shrug: 0.7 * a }, armL: { preset: 'clasp', reach: a }, armR: { preset: 'clasp', reach: a } });
  return { shot: framed([0, 1.35, 0], { dist: 1.9, yaw: 5, pitch: 2, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('talking gestures', 5, (lt, s) => {
  const ph = Math.floor(lt / 1.25);
  const presets = [['explain', 'rest'], ['open', 'open'], ['heart', 'rest'], ['offer', 'explain']][ph % 4];
  s.jesus.update(s.t, { face: ['kind', 'hopeful', 'tender', 'warm'][ph % 4], gaze: 'camera', speech: talkSample(s.t), armR: { preset: presets[0] }, armL: { preset: presets[1] } });
  return { shot: framed([0, 1.15, 0], { dist: 2.6, yaw: 15, pitch: 2, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('walk off with an arm around, talking', 5, (lt, s) => {
  s.big.visible = true;
  const J = s.jesus, rate = J.walkRate('walk') * 0.9, sp = J.walkSpeed('walk') * rate;
  const d = sp * lt;
  const dir = V(0.35, 0, -1).normalize();
  const yaw = Math.atan2(dir.x, dir.z);
  const pos = dir.clone().multiplyScalar(d);
  s.big.position.copy(pos).add(V(0.92, 0, -0.06).applyAxisAngle(V(0, 1, 0), yaw));
  s.big.rotation.y = yaw;
  s.big.updateMatrixWorld(true);
  const B = s.bigAnchors();
  J.update(s.t, { pos: [pos.x, 0, pos.z], yaw, walk: { amount: 1, phase: lt * rate }, face: 'warm', gaze: B.eye, head: { follow: 0.6 },
    speech: talkSample(s.t, 0.8), armL: { preset: 'around', target: B.back }, armR: { preset: 'explain' } });
  return { shot: framed([pos.x + 0.4, 1.2, pos.z], { dist: 4.4, yaw: 25, pitch: 6, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('crouch + sit (generic)', 3, (lt, s) => {
  const c = ramp(lt, 0.1, 0.8) * (1 - ramp(lt, 1.3, 1.6));
  const si = ramp(lt, 1.6, 2.4);
  s.jesus.update(s.t, { face: 'kind', gaze: 'camera', body: { crouch: c, sit: si }, armL: { preset: si > 0.5 ? 'knee_rest' : 'rest' }, armR: { preset: 'rest' } });
  return { shot: framed([0, 0.7, 0], { dist: 3.6, yaw: 50, pitch: 4, fov: 32, screenY: 0.44, drift: 0 }) };
});
export const DURATION = T0;
export const SEGMENTS = seg.map((x) => ({ name: x.name, t0: x.t0, t1: x.t1 }));

// ---------------------------------------------------------------------------------- set
export async function setup(app) {
  const scene = new THREE.Scene();
  // soft dusk gradient sky
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 a = vec3(1.0,0.78,0.62), b = vec3(0.55,0.52,0.78); gl_FragColor = vec4(mix(a, b, smoothstep(-0.05, 0.6, h)), 1.0);\n#include <colorspace_fragment>\n}',
  }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshLambertMaterial({ color: 0xd9b6a0 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  // footprints grid (to read walking motion)
  const dots = new THREE.InstancedMesh(new THREE.CircleGeometry(0.035, 12), new THREE.MeshBasicMaterial({ color: 0xbf9580 }), 400);
  let n = 0; const m = new THREE.Matrix4();
  for (let i = -10; i < 10; i++) for (let j = -10; j < 10; j++) { m.makeRotationX(-Math.PI / 2).setPosition(i * 0.5, 0.002, j * 0.5); dots.setMatrixAt(n++, m); }
  scene.add(dots);
  scene.add(new THREE.HemisphereLight(0xffe6cc, 0x6d5a78, 1.05));
  const key = new THREE.DirectionalLight(0xffe0bc, 2.5); key.position.set(2.2, 4, 3.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 15 }); key.shadow.bias = -0.0005;
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0xa9bfff, 1.6); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  EYE_LIGHT.uKeyColor.value.set(1.0, 0.93, 0.84);
  const jesus = await app.char('JESUS');
  scene.add(jesus.root);
  // big plump partner stand-in (Void-ish, ~2.8 m, leaning its head down toward Jesus)
  const big = new THREE.Group();
  const vm = new THREE.MeshStandardMaterial({ color: 0x2a2450, roughness: 0.6, emissive: 0x120c30 });
  const body = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 28), vm); body.scale.set(0.75, 1.15, 0.7); body.position.y = 1.15; big.add(body);
  const hd = new THREE.Mesh(new THREE.SphereGeometry(0.42, 32, 20), vm); hd.position.set(-0.45, 1.74, 0.1); big.add(hd);
  const eyeM = new THREE.MeshBasicMaterial({ color: 0xe8fbff });
  for (const x of [-0.62, -0.38]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.06, 16, 12), eyeM); e.position.set(x, 1.8, 0.47); big.add(e); }
  big.position.set(0.92, 0, -0.06); big.visible = false; scene.add(big);
  const bigAnchors = () => {
    big.updateMatrixWorld(true);
    const w = (x, y, z) => V(x, y, z).applyMatrix4(big.matrixWorld);
    return { back: w(-0.68, 1.42, -0.2), ear: w(-0.82, 1.66, 0.16), eye: w(-0.5, 1.8, 0.5), shoulder: w(-0.8, 1.47, 0.15), side: w(-0.74, 1.3, 0.05) };
  };
  // seated person stand-in
  const seated = new THREE.Group();
  const sm = new THREE.MeshStandardMaterial({ color: 0x5a76a8, roughness: 0.7 });
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.3, 8, 16), sm); torso.position.y = 0.42; torso.rotation.x = 0.25; seated.add(torso);
  const sh = new THREE.Mesh(new THREE.SphereGeometry(0.15, 24, 16), new THREE.MeshStandardMaterial({ color: 0xe0b090, roughness: 0.6 })); sh.position.set(0, 0.84, -0.03); seated.add(sh);
  seated.position.set(0.05, 0, 0.95); seated.rotation.y = Math.PI; seated.visible = false; scene.add(seated);
  seated.userData.eyes = V(0.05, 0.86, 0.85);
  // floating notification card
  const note = new THREE.Group();
  const card = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.12), new THREE.MeshBasicMaterial({ color: 0xeef6ff, toneMapped: false }));
  note.add(card);
  const ic = new THREE.Mesh(new THREE.CircleGeometry(0.035, 20), new THREE.MeshBasicMaterial({ color: 0x5aa0ff, toneMapped: false })); ic.position.set(-0.12, 0, 0.001); note.add(ic);
  const gl = glowSprite(0x9fd0ff, 0.42, 0.28); gl.position.z = -0.02; note.add(gl);
  const frame = new THREE.Mesh(new THREE.PlaneGeometry(0.37, 0.15), new THREE.MeshBasicMaterial({ color: 0x5a78a8 })); frame.position.z = -0.002; note.add(frame);
  note.position.set(-0.32, 1.95, 0.55); note.rotation.y = 0.5; note.visible = false; scene.add(note);
  // HUD label (camera child)
  scene.add(app.camera);
  const lc = document.createElement('canvas'); lc.width = 1024; lc.height = 64;
  const ltex = new THREE.CanvasTexture(lc); ltex.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1, 1 / 16), new THREE.MeshBasicMaterial({ map: ltex, transparent: true, depthTest: false, toneMapped: false }));
  label.renderOrder = 999; app.camera.add(label);
  return { scene, jesus, big, bigAnchors, seated, note, label, lc, ltex, lastLabel: '', look: { bloom: 0.32, bloomThreshold: 0.85, vignette: 0.22, warm: 0.1 } };
}

export async function update(t, app, s) {
  s.t = t;
  const tt = ((t % DURATION) + DURATION) % DURATION;
  const sg = seg.find((x) => tt >= x.t0 && tt < x.t1) || seg[0];
  s.big.visible = false; s.seated.visible = false; s.note.visible = false;
  s.big.position.set(0.92, 0, -0.06); s.big.rotation.y = 0; s.big.updateMatrixWorld(true);
  Object.assign(s.big.userData, s.bigAnchors());
  // pass 1 (dry): get the shot so the camera is final before the rig reads it (catchlights, gaze 'camera')
  const real = s.jesus;
  s.jesus = s.proxy || (s.proxy = { update() {}, walkRate: (x) => real.walkRate(x), walkSpeed: (x) => real.walkSpeed(x) });
  const r0 = sg.fn(tt - sg.t0, s, app) || {};
  s.jesus = real;
  applyShot(app.camera, r0.shot, t);
  app.camera.updateMatrixWorld(true);
  sg.fn(tt - sg.t0, s, app);
  if (s.note.visible) s.note.position.y = 1.95 + 0.03 * Math.sin(t * 2);
  // label
  const txt = `${sg.name}   [${sg.t0.toFixed(1)}–${sg.t1.toFixed(1)}s]`;
  if (txt !== s.lastLabel) {
    const g = s.lc.getContext('2d'); g.clearRect(0, 0, 1024, 64);
    g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(0, 0, 1024, 64);
    g.fillStyle = '#fff'; g.font = 'bold 38px sans-serif'; g.textBaseline = 'middle'; g.fillText(txt, 18, 33);
    s.ltex.needsUpdate = true; s.lastLabel = txt;
  }
  const d = 1, h = 2 * d * Math.tan((app.camera.fov * Math.PI / 180) / 2), w = h * app.camera.aspect;
  s.label.position.set(0, h / 2 - h * 0.1, -d); s.label.scale.set(w, w, 1);
}
