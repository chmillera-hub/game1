// Lab: THE VOID — turntable (0–4 s), expression sheet (1 s each), then key poses / actions.
//   node tools/render.js sheet --lab void --from 0 --to 4 --n 8 --cols 4 --out out/sheets/void_turn.jpg
//   node tools/render.js sheet --lab void --from 4.5 --to 30.5 --n 27 --cols 6 --out out/sheets/void_expr.jpg
//   window SEGMENTS (exported `segments`) lists every segment's [start, end, name].
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT, CTX } from '../core/context.js';
import { contactShadow } from '../core/materials.js';
import { Particles, CELL } from '../core/particles.js';
import { clamp, lerp, smooth, ease, fbm1 } from '../core/util.js';
import { VX, eyeRoll, whisperPose } from '../chars/void.js';

const TAU = Math.PI * 2;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const sm = (a, b, x) => smooth((x - a) / (b - a));
const mixP = (a, b, u) => { const o = { ...a }; for (const k in b) o[k] = (typeof b[k] === 'number' && typeof a[k] === 'number') ? lerp(a[k], b[k], u) : (u < 0.5 ? a[k] : b[k]); return o; };
const XW = (name, over) => VX(name, over);

// expression sheet (1 s each)
const EXPRS = ['neutral', 'calm', 'listen', 'curious', 'gentle', 'happy', 'laugh', 'giggle', 'whisper', 'sideeye', 'peripheral', 'scowl',
  'annoyed', 'huff', 'eyeroll', 'sadSmile', 'sad', 'innocent', 'surprised', 'flinch', 'wonder', 'proud', 'determined', 'smug', 'tender', 'awkward'];
const T_EX = 4, EX_DUR = 1.0;
const T_ACT = T_EX + EXPRS.length * EX_DUR;   // 30

// Action segments [name, duration]
const ACTS = [
  ['idle', 3], ['walk', 3], ['run', 2], ['back', 2.5], ['overshoulder', 3], ['whisper', 4], ['laugh', 4], ['crossed', 3],
  ['rollhuff', 4.5], ['pat', 3], ['around', 3.5], ['shrug', 2.5], ['kick', 5], ['latch', 3.5], ['sit', 3], ['kneel', 2.5],
  ['wave', 2], ['cosmos', 3], ['silhouette', 3],
];
export const segments = [[0, 4, 'turntable'], ...EXPRS.map((n, i) => [T_EX + i, T_EX + i + 1, 'expr:' + n])];
{ let t0 = T_ACT; for (const [n, d] of ACTS) { segments.push([t0, t0 + d, n]); t0 += d; } }

function label(text) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 64;
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.01), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, toneMapped: false }));
  m.renderOrder = 100; m.position.set(-0.035, -0.074, -0.3);
  const st = { m, tex, c, last: '' };
  st.set = (s) => { if (s === st.last) return; st.last = s; const g = c.getContext('2d'); g.clearRect(0, 0, 512, 64); g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(0, 0, 512, 64); g.fillStyle = '#fff'; g.font = 'bold 34px sans-serif'; g.fillText(s, 14, 44); tex.needsUpdate = true; };
  return st;
}

function dummyHuman() {
  // a plain 1.75 m placeholder partner (faces +Z at yaw 0)
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: 0xd8c6a8, roughness: 0.8 });
  const robe = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.3, 1.35, 20), mat); robe.position.y = 0.68; g.add(robe);
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.3, 6, 16), mat); torso.position.y = 1.3; g.add(torso);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.115, 24, 16), new THREE.MeshStandardMaterial({ color: 0xc89070, roughness: 0.6 })); head.position.y = 1.62; g.add(head);
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.125, 24, 16, 0, TAU, 0, 1.6), new THREE.MeshStandardMaterial({ color: 0x3a2618 })); hair.position.y = 1.635; hair.rotation.x = -0.4; g.add(hair);
  for (const sx of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.014, 8, 6), new THREE.MeshBasicMaterial({ color: 0x201010 })); e.position.set(sx * 0.04, 1.63, 0.105); g.add(e); }
  return { g, anchors: (yaw) => {
    const q = new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), yaw);
    const at = (x, y, z) => V(x, y, z).applyQuaternion(q).add(g.position);
    return { head: at(0, 1.62, 0), earL: at(0.12, 1.61, 0), earR: at(-0.12, 1.61, 0), shoulderL: at(0.2, 1.47, 0), shoulderR: at(-0.2, 1.47, 0), back: at(0, 1.35, -0.18), chest: at(0, 1.35, 0.2) };
  } };
}

function dummyMagician() {
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: 0x6a7488, roughness: 0.8 });
  const b = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 1.1, 6, 16), mat); b.position.y = 0.95; g.add(b);
  const h = new THREE.Mesh(new THREE.SphereGeometry(0.14, 20, 14), new THREE.MeshStandardMaterial({ color: 0xb8bcc6 })); h.position.y = 1.75; g.add(h);
  const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.12, 0.3, 16), new THREE.MeshStandardMaterial({ color: 0x2a2e3a })); hat.position.y = 2.0; g.add(hat);
  return g;
}

function cage() {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: 0xc9a85a, metalness: 0.7, roughness: 0.35 });
  const n = 14, R = 0.32, Hh = 0.7;
  for (let i = 0; i < n; i++) { const a = i / n * TAU; const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, Hh, 6), m); bar.position.set(Math.cos(a) * R, Hh / 2, Math.sin(a) * R); g.add(bar); }
  for (const y of [0.01, Hh]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(R, 0.014, 6, 40), m); ring.rotation.x = Math.PI / 2; ring.position.y = y; g.add(ring); }
  const dome = new THREE.Mesh(new THREE.SphereGeometry(R, 24, 10, 0, TAU, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xc9a85a, metalness: 0.7, roughness: 0.35, wireframe: true })); dome.position.y = Hh; g.add(dome);
  const latch = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.05, 0.03), new THREE.MeshStandardMaterial({ color: 0xffd27a, metalness: 0.6, roughness: 0.3, emissive: 0x332200 }));
  latch.position.set(0, 0.42, R + 0.02); g.add(latch);
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.3, 0.75, 20), new THREE.MeshStandardMaterial({ color: 0x5a4a6a })); stand.position.y = -0.375; g.add(stand);
  g.position.y = 0.75;
  return { g, latch };
}

export async function setup(app) {
  const scene = new THREE.Scene();
  const skyU = { uTop: { value: new THREE.Color(0x2a2a6a) }, uMid: { value: new THREE.Color(0xb98ac8) }, uBot: { value: new THREE.Color(0xffc49a) } };
  const sky = new THREE.Mesh(new THREE.SphereGeometry(90, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: skyU,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform vec3 uTop, uMid, uBot; varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 c = h > 0.08 ? mix(uMid, uTop, smoothstep(0.08, 0.6, h)) : mix(uBot, uMid, smoothstep(-0.05, 0.08, h)); gl_FragColor = vec4(c, 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
  scene.add(sky);
  const groundMat = new THREE.MeshStandardMaterial({ color: 0xb79bb8, roughness: 0.95 });
  const ground = new THREE.Mesh(new THREE.CircleGeometry(60, 64), groundMat); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const hemi = new THREE.HemisphereLight(0xffe2cc, 0x4a3a66, 1.1); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffd9b8, 2.4); key.position.set(4, 6, 5); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); Object.assign(key.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5, near: 1, far: 25 }); key.shadow.bias = -0.0008;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xa8c0ff, 1.6); rim.position.set(-5, 4, -6); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const vd = await app.char('VOID');
  scene.add(vd.root);
  const partner = dummyHuman(); scene.add(partner.g); partner.g.visible = false;
  const mag = dummyMagician(); scene.add(mag); mag.visible = false;
  const cg = cage(); scene.add(cg.g); cg.g.visible = false;
  const fx = new Particles({ max: 200 }); scene.add(fx.mesh);
  scene.add(app.camera);
  const lab = label('');
  app.camera.add(lab.m);
  return { scene, vd, partner, mag, cg, sky, skyU, key, rim, hemi, groundMat, lab, fx, look: { bloom: 0.6, bloomThreshold: 0.8, bloomRadius: 0.5, exposure: 1.0, vignette: 0.22, sat: 1.05 } };
}

function segAt(t) {
  for (const s of segments) if (t >= s[0] && t < s[1]) return { name: s[2], u: t - s[0], dur: s[1] - s[0], t0: s[0] };
  const s = segments[segments.length - 1];
  return { name: s[2], u: t - s[0], dur: s[1] - s[0], t0: s[0] };
}

const FULL = (y = 1.5, dist = 9.5, yaw = 0, pitch = 4, screenY = 0.46) => framed([0, y, 0], { dist, yaw, pitch, fov: 32, screenY, drift: 0 });

export async function update(t, app, S) {
  const vd = S.vd, seg = segAt(t), u = seg.u;
  S.partner.g.visible = false; S.mag.visible = false; S.cg.g.visible = false;
  S.skyU.uTop.value.set(0x2a2a6a); S.skyU.uMid.value.set(0xb98ac8); S.skyU.uBot.value.set(0xffc49a);
  S.key.intensity = 2.4; S.key.position.set(4, 6, 5); S.rim.intensity = 1.6; S.hemi.intensity = 1.1; S.groundMat.color.set(0xb79bb8);
  EYE_LIGHT.uKeyDir.value.copy(S.key.position).normalize();
  S.look = { bloom: 0.6, bloomThreshold: 0.8, bloomRadius: 0.5, exposure: 1.0, vignette: 0.22, sat: 1.05 };
  S.fx.begin();
  S.dbg = null;
  let pose = { face: XW('neutral') }, shot = FULL();
  let name = seg.name;
  const P = S.partner;

  if (name === 'turntable') {
    pose = { yaw: (t / 4) * TAU, face: XW('calm') };
    shot = FULL(1.5, 9.5, 0, 4, 0.47);
  } else if (name.startsWith('expr:')) {
    const ex = name.slice(5);
    const prevIdx = EXPRS.indexOf(ex) - 1;
    const prev = prevIdx >= 0 ? XW(EXPRS[prevIdx] === 'eyeroll' ? 'annoyed' : EXPRS[prevIdx]) : XW('neutral');
    let cur = ex === 'eyeroll' ? XW('annoyed', eyeRoll(clamp((u - 0.05) / 0.85))) : XW(ex);
    const face = mixP(prev, cur, smooth(u / 0.22));
    face.autoBlink = 0; if (ex !== 'awkward' && ex !== 'eyeroll') face.saccade = 0;
    const extra = { puff: face.puff || 0, laugh: ex === 'laugh' ? 0.6 : ex === 'giggle' ? 0.25 : 0 };
    const head = { yaw: ex === 'sideeye' ? 0.15 : 0, pitch: ex === 'sad' ? 0.12 : 0, roll: ex === 'curious' ? 0.12 : ex === 'innocent' ? -0.08 : 0 };
    pose = { face, extra, head, armL: ex === 'whisper' ? { preset: 'whisper' } : {} };
    shot = framed([0, 2.0, 0.35], { dist: 3.6, yaw: 8, pitch: 4, fov: 30, screenY: 0.36, drift: 0 });
    name = 'expr: ' + ex;
  } else if (name === 'idle') {
    pose = { face: XW('calm'), gaze: 'camera', extra: { motes: 1.5 } };
    shot = FULL(1.6, 8.5, 22, 6);
  } else if (name === 'walk' || name === 'run') {
    const cad = name === 'run' ? 1.7 : 1.05, stride = name === 'run' ? 0.66 : 0.38;
    const ph = u * cad, x = -3 + ph * 2 * stride;
    pose = { pos: [x, 0, 0], yaw: Math.PI / 2, walk: { amount: 1, phase: ph, style: name === 'run' ? 'run' : 'waddle' }, face: XW(name === 'run' ? 'determined' : 'calm'), gaze: [x + 4, 2.2, 0] };
    shot = framed([x, 1.3, 0], { dist: 10.5, yaw: 12, pitch: 3, fov: 32, screenY: 0.48, drift: 0 });
  } else if (name === 'back') {
    pose = { yaw: Math.PI + 0.35 * Math.sin(u * 1.2), face: XW('annoyed') };
    shot = FULL(1.6, 8.5, 18, 8);
  } else if (name === 'overshoulder') {
    const w = sm(0.2, 1.3, u);
    pose = { yaw: Math.PI, head: { yaw: -1.9 * w, pitch: -0.05 * w, roll: -0.1 * w }, body: { twist: -0.35 * w, tilt: 0.06 * w }, face: mixP(XW('annoyed'), XW('gentle'), sm(1.2, 1.8, u)), gaze: 'camera' };
    shot = FULL(1.8, 7.5, 12, 6, 0.42);
  } else if (name === 'whisper') {
    // the partner stands; the Void steps in and bends so its mouth sits at the partner's ear (solvePos)
    P.g.visible = true; P.g.position.set(0.9, 0, 1.25); P.g.rotation.y = -0.6;
    const pa = P.anchors(-0.6);
    const w = sm(0.3, 1.5, u);
    const full = { yaw: 0.35, ...whisperPose(1, 0.9, 1), face: XW('whisper', { gazeYaw: -0.5 }), speech: false };
    const solved = vd.solvePos(t, full, 'whisper', pa.earR);
    const W = whisperPose(1, 0.9, w);
    pose = { pos: [lerp(-0.4, solved[0], w), 0, lerp(-0.6, solved[2], w)], yaw: 0.35 * w, ...W,
      face: mixP(XW('calm'), XW('whisper', { gazeYaw: -0.5 }), w),
      speech: u > 1.7 ? { open: 0.1 + 0.12 * Math.abs(Math.sin(u * 9)), round: 0.6, wide: 0, close: 0 } : false };
    S.dbg = () => console.log('WHISPER mouth', vd.anchor('mouth').toArray().map((v) => v.toFixed(2)), 'partner earR', pa.earR.toArray().map((v) => v.toFixed(2)), 'err', solved.err.toFixed(2));
    shot = framed([0.5, 1.5, 0.6], { dist: 7.5, yaw: 25, pitch: 4, fov: 32, screenY: 0.45, drift: 0 });
  } else if (name === 'laugh') {
    const w = sm(0.15, 0.6, u), out = sm(3.4, 4.0, u);
    pose = { face: mixP(XW('listen'), XW('laugh'), w * (1 - out * 0.6)), extra: { laugh: w * (1 - out), cough: { t0: seg.t0 + 0.8, t1: seg.t0 + 3.2, rate: 12 } },
      armL: { preset: 'belly', from: 'rest', mix: w }, armR: { preset: 'belly', from: 'rest', mix: w } };
    shot = FULL(2.0, 7.2, 8, 4, 0.42);
  } else if (name === 'crossed') {
    const w = sm(0.1, 0.9, u);
    pose = { face: mixP(XW('calm'), XW('scowl'), w), armL: { preset: 'crossed', from: 'rest', mix: w }, armR: { preset: 'crossed', from: 'rest', mix: sm(0.25, 1.0, u) }, body: { lean: -0.05 * w }, gaze: 'camera' };
    shot = FULL(1.8, 7.2, 14, 4, 0.42);
  } else if (name === 'rollhuff') {
    // eye-roll (0.2-1.2), huff & puff (1.3-2.8), turn back (3.0-4.5)
    const roll = clamp((u - 0.2) / 0.9);
    let face = XW('annoyed', u < 1.25 ? eyeRoll(roll) : {});
    const pf = sm(1.3, 1.6, u) * (1 - sm(1.9, 2.05, u)) + sm(2.15, 2.4, u) * (1 - sm(2.6, 2.8, u));
    face = mixP(face, XW('huff'), sm(1.2, 1.4, u) * (1 - sm(2.9, 3.2, u)));
    face.puff = pf;
    const turn = sm(3.0, 4.2, u);
    pose = { yaw: Math.PI * turn, face, extra: { puff: pf }, body: { swell: 0.3 * pf, shrug: 0.3 * pf }, head: { pitch: -0.08 * roll * (1 - roll) * 4 } };
    shot = FULL(1.8, 7.6, 10, 4, 0.42);
  } else if (name === 'pat' || name === 'around') {
    P.g.visible = true;
    const isPat = name === 'pat';
    P.g.position.set(1.35, 0, 0.45); P.g.rotation.y = -0.4;
    const pa = P.anchors(-0.4);
    const w = sm(0.2, 1.0, u);
    const tgt = isPat ? pa.shoulderR.clone().add(V(0, 0.06, 0)) : pa.shoulderL.clone().add(V(0.02, -0.02, -0.12));
    pose = { yaw: 0.35, face: isPat ? XW('sadSmile') : XW('giggle'), gaze: pa.head,
      body: { tilt: 0.06 * w, lean: 0.12 * w }, head: { yaw: 0.25, roll: 0.12 * w },
      armL: { preset: isPat ? 'pat' : 'around', target: tgt, reach: w, pat: isPat ? sm(1.0, 1.3, u) : 0, patPhase: seg.t0 },
      extra: { laugh: isPat ? 0 : 0.15 } };
    shot = framed([0.75, 1.45, 0.3], { dist: 8.0, yaw: 10, pitch: 4, fov: 32, screenY: 0.45, drift: 0 });
  } else if (name === 'shrug') {
    const w = sm(0.2, 0.6, u) * (1 - sm(1.8, 2.4, u));
    pose = { face: XW('innocent'), body: { shrug: w }, armL: { preset: 'shrug', from: 'rest', mix: w }, armR: { preset: 'shrug', from: 'rest', mix: w }, head: { roll: -0.12 * w, yaw: 0.1 * w } };
    shot = FULL(1.6, 9.0, 8, 4, 0.45);
  } else if (name === 'kick') {
    // calm face toward "Fear" (camera) — peripheral glance — chamber — KICK — hold — recover — innocent shrug
    S.mag.visible = true; S.mag.position.set(-0.25, 0, -1.9);
    const peri = sm(0.3, 0.6, u) * (1 - sm(1.4, 1.6, u));
    const kick = u < 1.6 ? 0 : u < 1.95 ? -0.5 * sm(1.6, 1.9, u) : u < 2.1 ? lerp(-0.5, 1.1, ease.out((u - 1.95) / 0.15)) : u < 2.6 ? lerp(1.1, 1.0, (u - 2.1) / 0.5) : 1.0 * (1 - sm(2.6, 3.3, u));
    const hit = u > 2.05 ? Math.min(1, (u - 2.05) * 1.5) : 0;
    S.mag.position.z = -1.9 - hit * 3.5; S.mag.position.y = hit * 1.2 * (1 - hit) * 2; S.mag.rotation.x = -hit * 1.4;
    const shrugW = sm(3.6, 4.0, u) * (1 - sm(4.6, 5.0, u));
    const face = u < 1.55 ? mixP(XW('calm'), XW('peripheral'), peri) : u < 3.4 ? XW('determined', { gazeYaw: 0 }) : mixP(XW('determined'), XW('innocent'), sm(3.4, 3.7, u));
    pose = { face, extra: { kick, kickSide: 'R' }, gaze: 'camera', body: { shrug: shrugW }, armL: shrugW > 0 ? { preset: 'shrug', from: 'rest', mix: shrugW } : {}, armR: shrugW > 0 ? { preset: 'shrug', from: 'rest', mix: shrugW } : {} };
    S.dbg = () => console.log('KICK foot', vd.anchor('kickFoot').toArray().map((v) => v.toFixed(2)), 'head', vd.anchor('head').toArray().map((v) => v.toFixed(2)));
    shot = framed([0, 1.4, -0.3], { dist: 9.0, yaw: 58, pitch: 4, fov: 32, screenY: 0.45, drift: 0 });
  } else if (name === 'latch') {
    S.cg.g.visible = true; S.cg.g.position.set(0.5, 0.75, 1.45); S.cg.g.rotation.y = Math.PI;
    const latch = S.cg.latch.getWorldPosition(new THREE.Vector3());
    const w = sm(0.3, 1.4, u);
    pose = { face: XW('tender', { gazePitch: -0.1 }), gaze: latch, body: { lean: 0.3 * w, crouch: 0.3 * w }, head: { pitch: 0.25 * w },
      armL: { preset: 'tip', target: latch.clone().add(V(0, 0, -0.04)), reach: w, tip: true, fingers: [-0.1, -0.3, 1] } };
    shot = framed([0.5, 1.3, 1.0], { dist: 6.0, yaw: 75, pitch: 6, fov: 32, screenY: 0.45, drift: 0 });
  } else if (name === 'sit') {
    const w = sm(0.2, 1.2, u);
    pose = { face: XW('curious'), body: { sit: w }, armL: { preset: 'belly', from: 'rest', mix: w }, armR: { preset: 'belly', from: 'rest', mix: w }, head: { roll: 0.1 * w } };
    shot = FULL(1.3, 8.0, 20, 6, 0.48);
  } else if (name === 'kneel') {
    const w = sm(0.2, 1.0, u);
    pose = { face: XW('tender'), body: { kneel: w, lean: 0.15 * w }, armL: { preset: 'open', from: 'rest', mix: w }, armR: { preset: 'open', from: 'rest', mix: w }, head: { pitch: 0.15 * w } };
    shot = FULL(1.3, 8.0, 20, 6, 0.48);
  } else if (name === 'wave') {
    pose = { face: XW('hopeful'), armR: { preset: 'wave', from: 'rest', mix: sm(0.1, 0.5, u), offset: [0.12 * Math.sin(u * 9) * sm(0.4, 0.6, u), 0, 0] }, gaze: 'camera' };
    shot = FULL(1.7, 9.0, 0, 4, 0.45);
  } else if (name === 'cosmos') {
    const c = sm(0.2, 1.5, u);
    pose = { face: XW('proud'), extra: { cosmos: c }, armL: { preset: 'open', from: 'rest', mix: c }, armR: { preset: 'open', from: 'rest', mix: c } };
    S.look = { ...S.look, exposure: 0.9 };
    S.skyU.uTop.value.set(0x0c0a22); S.skyU.uMid.value.set(0x231a44); S.skyU.uBot.value.set(0x3a2a55); S.key.intensity = 0.9; S.hemi.intensity = 0.35; S.groundMat.color.set(0x3a3048);
    shot = FULL(1.8, 7.5, 12, 4, 0.42);
  } else if (name === 'silhouette') {
    S.skyU.uTop.value.set(0x3a3a8a); S.skyU.uMid.value.set(0xe08aa0); S.skyU.uBot.value.set(0xffb070);
    S.key.intensity = 0.25; S.key.position.set(-1, 2, -8); S.rim.intensity = 3.5; S.hemi.intensity = 0.25; S.groundMat.color.set(0x5a4060);
    EYE_LIGHT.uKeyDir.value.copy(S.key.position).normalize();
    pose = { face: XW('gentle'), yaw: 0.6 * Math.sin(u * 0.8), walk: { amount: 0 }, gaze: 'camera' };
    shot = framed([0, 1.6, 0], { dist: 10, yaw: 0, pitch: -4, fov: 32, screenY: 0.45, drift: 0 });
  }

  applyShot(app.camera, shot, t);   // camera first: eye catchlights read CTX.camera during update
  vd.update(t, pose);
  if (S.dbg) { S.dbg(); S.dbg = null; }
  S.lab.set(`${name}  t=${t.toFixed(2)}`);
  S.fx.end();
}
