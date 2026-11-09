// Lab: THE VOID — turntable (0–4 s), expression sheet (1 s each), then key poses / actions. The partner in the
// whisper / pat / arm-around segments is the REAL Jesus rig (CHARS.JESUS), checked from the front and from 3/4.
//   node tools/render.js sheet --lab void --from 0 --to 4 --n 8 --cols 4 --out out/sheets/void_turn.jpg
//   node tools/render.js sheet --lab void --from 4.5 --to 29.5 --n 26 --cols 7 --out out/sheets/void_expr.jpg
//   node tools/render.js sheet --lab void --from 30.5 --to 96 --n 30 --cols 6 --out out/sheets/void_act.jpg
//   `segments` (exported) lists every segment's [start, end, name]; the name is shown in an on-screen label.
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { clamp, lerp, smooth, ease } from '../core/util.js';
import { VX, eyeRoll, whisperPose } from '../chars/void.js';
import { JX } from '../chars/jesus.js';

const TAU = Math.PI * 2;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const sm = (a, b, x) => smooth((x - a) / (b - a));
const mixP = (a, b, u) => { const o = { ...a }; for (const k in b) o[k] = (typeof b[k] === 'number' && typeof a[k] === 'number') ? lerp(a[k], b[k], u) : (u < 0.5 ? a[k] : b[k]); return o; };

// expression sheet (1 s each)
const EXPRS = ['neutral', 'calm', 'listen', 'curious', 'gentle', 'happy', 'laugh', 'giggle', 'whisper', 'sideeye', 'peripheral', 'scowl',
  'annoyed', 'huff', 'eyeroll', 'sadSmile', 'sad', 'innocent', 'surprised', 'flinch', 'wonder', 'proud', 'determined', 'smug', 'tender', 'awkward'];
const T_EX = 4, EX_DUR = 1.0;
const T_ACT = T_EX + EXPRS.length * EX_DUR;   // 30

// Action segments [name, duration]
const ACTS = [
  ['idle', 3], ['walk', 3], ['run', 2], ['back', 2.5], ['overshoulder', 3], ['whisper', 5], ['laugh', 4], ['crossed', 4.5],
  ['rollhuff', 4.5], ['pat', 4.5], ['around', 4.5], ['shrug', 2.5], ['kick', 5], ['latch', 3.5], ['sit', 3], ['kneel', 2.5],
  ['wave', 2], ['cosmos', 3], ['silhouette', 3], ['kickback', 1.5], ['crossed34', 1],
];
export const segments = [[0, 4, 'turntable'], ...EXPRS.map((n, i) => [T_EX + i, T_EX + i + 1, 'expr:' + n])];
{ let t0 = T_ACT; for (const [n, d] of ACTS) { segments.push([t0, t0 + d, n]); t0 += d; } }
export const DURATION = segments[segments.length - 1][1];

function label() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 64;
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(0.064, 0.008), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, toneMapped: false }));
  m.renderOrder = 100; m.position.set(0.0, -0.068, -0.3);
  const st = { m, tex, c, last: '' };
  st.set = (s) => { if (s === st.last) return; st.last = s; const g = c.getContext('2d'); g.clearRect(0, 0, 512, 64); g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(0, 0, 512, 64); g.fillStyle = '#fff'; g.font = 'bold 34px sans-serif'; g.fillText(s, 14, 44); tex.needsUpdate = true; };
  return st;
}

// fallback only (if the Jesus rig is mid-edit and fails to load): a 1.75 m stand-in with Jesus's anchor layout
function standIn() {
  const root = new THREE.Group(), mat = new THREE.MeshStandardMaterial({ color: 0xd8c6a8, roughness: 0.8 });
  const robe = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.3, 1.3, 20), mat); robe.position.y = 0.65; root.add(robe);
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.25, 6, 16), mat); torso.position.y = 1.2; root.add(torso);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.13, 24, 16), new THREE.MeshStandardMaterial({ color: 0xc89070 })); head.position.y = 1.53; root.add(head);
  const A = { head: [0, 1.53, 0], eyes: [0, 1.55, 0.14], earL: [0.15, 1.52, -0.01], earR: [-0.15, 1.52, -0.01], shoulderL: [0.165, 1.35, -0.01], shoulderR: [-0.165, 1.35, -0.01], chest: [0, 1.2, 0.15], back: [0, 1.2, -0.15] };
  return { root, height: 1.75, update(t, p) { root.position.set(...(p.pos || [0, 0, 0])); root.rotation.set(0, p.yaw || 0, 0); root.updateMatrixWorld(true); },
    anchor(n) { return A[n] ? V(...A[n]).applyMatrix4(root.matrixWorld) : null; }, eyesWorld() { return this.anchor('eyes'); } };
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
  const skyU = { uTop: { value: new THREE.Color(0x2a2a6a) }, uMid: { value: new THREE.Color(0xb98ac8) }, uBot: { value: new THREE.Color(0xffc49a) }, uSun: { value: new THREE.Vector3(0, 0.1, -1) }, uSunK: { value: 0 } };
  const sky = new THREE.Mesh(new THREE.SphereGeometry(90, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: skyU,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform vec3 uTop, uMid, uBot, uSun; uniform float uSunK; varying vec3 vP; void main(){ vec3 d = normalize(vP); float h = d.y;
      vec3 c = h > 0.08 ? mix(uMid, uTop, smoothstep(0.08, 0.6, h)) : mix(uBot, uMid, smoothstep(-0.05, 0.08, h));
      float s = max(dot(d, normalize(uSun)), 0.0); c += uSunK * (vec3(1.0, 0.75, 0.45) * pow(s, 60.0) * 3.0 + vec3(1.0, 0.6, 0.4) * pow(s, 6.0) * 0.5);
      gl_FragColor = vec4(c, 1.0);
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
  let jesus;
  try { jesus = await app.char('JESUS'); } catch (e) { console.log('JESUS rig failed to load, using a stand-in: ' + e.message); jesus = standIn(); }
  scene.add(jesus.root); jesus.root.visible = false;
  const mag = dummyMagician(); scene.add(mag); mag.visible = false;
  const cg = cage(); scene.add(cg.g); cg.g.visible = false;
  scene.add(app.camera);
  const lab = label();
  app.camera.add(lab.m);
  return { scene, vd, jesus, mag, cg, sky, skyU, key, rim, hemi, groundMat, lab, look: { bloom: 0.6, bloomThreshold: 0.8, bloomRadius: 0.5, exposure: 1.0, vignette: 0.22, sat: 1.05 } };
}

function segAt(t) {
  for (const s of segments) if (t >= s[0] && t < s[1]) return { name: s[2], u: t - s[0], dur: s[1] - s[0], t0: s[0] };
  const s = segments[segments.length - 1];
  return { name: s[2], u: t - s[0], dur: s[1] - s[0], t0: s[0] };
}

const FULL = (y = 1.5, dist = 9.5, yaw = 0, pitch = 4, screenY = 0.46) => framed([0, y, 0], { dist, yaw, pitch, fov: 32, screenY, drift: 0 });

export async function update(t, app, S) {
  const vd = S.vd, J = S.jesus, seg = segAt(t);
  let u = seg.u;
  J.root.visible = false; S.mag.visible = false; S.cg.g.visible = false;
  S.skyU.uTop.value.set(0x2a2a6a); S.skyU.uMid.value.set(0xb98ac8); S.skyU.uBot.value.set(0xffc49a); S.skyU.uSunK.value = 0;
  S.key.intensity = 2.4; S.key.position.set(4, 6, 5); S.rim.intensity = 1.6; S.rim.position.set(-5, 4, -6); S.hemi.intensity = 1.1; S.groundMat.color.set(0xb79bb8);
  S.key.castShadow = true;
  S.look = { bloom: 0.6, bloomThreshold: 0.8, bloomRadius: 0.5, exposure: 1.0, vignette: 0.22, sat: 1.05 };
  let pose = { face: VX('neutral') }, shot = FULL(), jpose = null;
  let name = seg.name;
  // the camera must be set BEFORE the rigs update (core eye catchlights / gaze 'camera' read CTX.camera)
  const cam = (s) => { shot = s; applyShot(app.camera, s, t); };

  if (name === 'turntable') {
    pose = { yaw: (t / 4) * TAU, face: VX('calm') };
    cam(FULL(1.5, 9.5, 0, 4, 0.47));
  } else if (name.startsWith('expr:')) {
    const ex = name.slice(5);
    const prevIdx = EXPRS.indexOf(ex) - 1;
    const prev = prevIdx >= 0 ? VX(EXPRS[prevIdx] === 'eyeroll' ? 'annoyed' : EXPRS[prevIdx]) : VX('neutral');
    const cur = ex === 'eyeroll' ? VX('annoyed', eyeRoll(clamp((u - 0.05) / 0.85))) : VX(ex);
    const face = mixP(prev, cur, smooth(u / 0.22));
    face.autoBlink = 0; if (ex !== 'awkward' && ex !== 'eyeroll') face.saccade = 0;
    const extra = { puff: face.puff || 0, laugh: ex === 'laugh' ? 0.6 : ex === 'giggle' ? 0.25 : 0 };
    const head = { yaw: ex === 'sideeye' ? 0.15 : 0, pitch: ex === 'sad' ? 0.12 : 0, roll: ex === 'curious' ? 0.12 : ex === 'innocent' ? -0.08 : 0 };
    pose = { face, extra, head, armL: ex === 'whisper' ? { preset: 'whisper' } : {} };
    cam(framed([0, 2.0, 0.35], { dist: 3.6, yaw: 8, pitch: 4, fov: 30, screenY: 0.36, drift: 0 }));
    name = 'expr: ' + ex;
  } else if (name === 'idle') {
    cam(FULL(1.6, 8.5, 22, 6));
    pose = { face: VX('calm'), gaze: 'camera', extra: { motes: 1.5 } };
  } else if (name === 'walk' || name === 'run') {
    const cad = name === 'run' ? 1.7 : 1.05, stride = name === 'run' ? 0.66 : 0.38;
    const ph = u * cad, x = -3 + ph * 2 * stride;
    cam(framed([x, 1.3, 0], { dist: 10.5, yaw: 12, pitch: 3, fov: 32, screenY: 0.48, drift: 0 }));
    pose = { pos: [x, 0, 0], yaw: Math.PI / 2, walk: { amount: 1, phase: ph, style: name === 'run' ? 'run' : 'waddle' }, face: VX(name === 'run' ? 'determined' : 'calm'), gaze: [x + 4, 2.2, 0] };
  } else if (name === 'back') {
    cam(FULL(1.6, 8.5, 18, 8));
    pose = { yaw: Math.PI + 0.35 * Math.sin(u * 1.2), face: VX('annoyed') };
  } else if (name === 'overshoulder') {
    const w = sm(0.2, 1.3, u);
    cam(FULL(1.8, 7.5, 12, 6, 0.42));
    pose = { yaw: Math.PI, head: { yaw: -1.9 * w, pitch: -0.05 * w, roll: -0.1 * w }, body: { twist: -0.35 * w, tilt: 0.06 * w }, face: mixP(VX('annoyed'), VX('gentle'), sm(1.2, 1.8, u)), gaze: 'camera' };
  } else if (name === 'whisper') {
    // Jesus stands; the Void steps in and bends so its mouth is right at his ear (solveWhisper: depth + position)
    J.root.visible = true;
    const close = u > 2.6;
    cam(close ? framed([0.72, 1.6, 1.05], { dist: 3.6, yaw: -38, pitch: 3, fov: 30, screenY: 0.42, drift: 0 })
      : framed([0.4, 1.5, 0.6], { dist: 7.8, yaw: 25, pitch: 4, fov: 32, screenY: 0.45, drift: 0 }));
    jpose = { pos: [0.95, 0, 1.25], yaw: -0.55, face: JX('listening'), gaze: 'camera', head: { roll: 0.08 } };
    J.update(t, jpose);
    const w = sm(0.3, 1.5, u);
    const sol = vd.solveWhisper(t, { yaw: 0.35, face: VX('whisper', { gazeYaw: -0.45 }), speech: false }, J.anchor('earR'), 1);
    const W = whisperPose(1, sol.depth, w);
    pose = { pos: [lerp(-0.4, sol.pos[0], w), 0, lerp(-0.6, sol.pos[2], w)], yaw: 0.35 * w, ...W,
      face: mixP(VX('calm'), VX('whisper', { gazeYaw: -0.45 }), w),
      speech: u > 1.7 ? { open: 0.1 + 0.12 * Math.abs(Math.sin(u * 9)), round: 0.6, wide: 0, close: 0 } : false };
    S.dbg = () => console.log(`WHISPER t=${t.toFixed(2)} depth ${sol.depth.toFixed(3)} err ${sol.err.toFixed(3)} mouthY ${vd.anchor('mouth').y.toFixed(3)} earY ${J.anchor('earR').y.toFixed(3)} dist(whisper,ear) ${vd.anchor('whisper').distanceTo(J.anchor('earR')).toFixed(3)}`);
  } else if (name === 'laugh') {
    const w = sm(0.15, 0.6, u), out = sm(3.4, 4.0, u);
    cam(FULL(2.0, 7.2, 8, 4, 0.42));
    pose = { face: mixP(VX('listen'), VX('laugh'), w * (1 - out * 0.6)), extra: { laugh: w * (1 - out), cough: { t0: seg.t0 + 0.8, t1: seg.t0 + 3.2 } },
      armL: { preset: 'belly', from: 'rest', mix: w }, armR: { preset: 'belly', from: 'rest', mix: w } };
  } else if (name === 'crossed' || name === 'crossed34') {
    // front (0-1.5) -> 3/4 (1.5-3) -> profile (3-4.5); crossed34 = a closer 3/4 from its right
    const w = name === 'crossed34' ? 1 : sm(0.1, 0.9, u), view = u < 1.5 ? 0 : u < 3 ? 1 : 2;
    cam(name === 'crossed34' ? framed([0, 1.45, 0.4], { dist: 4.6, yaw: -42, pitch: 4, fov: 32, screenY: 0.45, drift: 0 }) : FULL(1.7, 7.0, [6, 40, 80][view], 4, 0.42));
    pose = { face: mixP(VX('calm'), VX('scowl'), w), armL: { preset: 'crossed', from: 'rest', mix: w }, armR: { preset: 'crossed', from: 'rest', mix: name === 'crossed34' ? 1 : sm(0.25, 1.0, u) }, body: { lean: -0.05 * w }, gaze: 'camera' };
  } else if (name === 'rollhuff') {
    // eye-roll (0.2-1.2), huff & puff (1.3-2.8), turn back (3.0-4.5)
    const roll = clamp((u - 0.2) / 0.9);
    let face = VX('annoyed', u < 1.25 ? eyeRoll(roll) : {});
    const pf = sm(1.3, 1.6, u) * (1 - sm(1.9, 2.05, u)) + sm(2.15, 2.4, u) * (1 - sm(2.6, 2.8, u));
    face = mixP(face, VX('huff'), sm(1.2, 1.4, u) * (1 - sm(2.9, 3.2, u)));
    face.puff = pf;
    const turn = sm(3.0, 4.2, u);
    cam(FULL(1.8, 7.6, 10, 4, 0.42));
    pose = { yaw: Math.PI * turn, face, extra: { puff: pf }, body: { swell: 0.3 * pf, shrug: 0.3 * pf }, head: { pitch: -0.08 * roll * (1 - roll) * 4 } };
  } else if (name === 'pat' || name === 'around') {
    // beat 14: Jesus shrugs back at the Void, it pats his near shoulder with a sad smile
    // beat 15: the Void puts an arm around him (palm on his far shoulder). Front view, then 3/4.
    J.root.visible = true;
    const isPat = name === 'pat', view34 = u > seg.dur * 0.5;
    cam(view34 ? framed([0.75, 1.5, 0.6], { dist: 5.2, yaw: isPat ? 52 : 125, pitch: 6, fov: 32, screenY: 0.42, drift: 0 })
      : framed([0.6, 1.55, 0.6], { dist: 5.6, yaw: 10, pitch: 3, fov: 32, screenY: 0.42, drift: 0 }));
    const jy = isPat ? -0.25 : 0.1;
    jpose = isPat
      ? { pos: [1.05, 0, 0.95], yaw: jy, face: JX('shrug'), gaze: [0.1, 2.12, 0.2], head: { look: [0.1, 2.12, 0.2], follow: 0.75 },
          body: { shrug: 0.7 * sm(0.0, 0.4, u) * (1 - sm(1.6, 2.2, u)) }, armL: { preset: 'shrug', reach: 0.7 * (1 - sm(1.6, 2.2, u)) }, armR: { preset: 'shrug', reach: 0.7 * (1 - sm(1.6, 2.2, u)) } }
      : { pos: [1.0, 0, 0.75], yaw: jy, face: JX('warm'), gaze: 'camera', head: { yaw: 0.15 } };
    J.update(t, jpose);
    const w = sm(isPat ? 0.5 : 0.2, isPat ? 1.3 : 1.1, u);
    pose = { yaw: 0.3, face: isPat ? VX('sadSmile') : VX('gentle'), gaze: J.anchor('eyes'),
      body: { tilt: 0.06 * w, lean: 0.08 * w }, head: { yaw: 0.22, roll: 0.1 * w },
      armL: { preset: isPat ? 'pat' : 'around', on: J, reach: w, pat: isPat ? sm(1.3, 1.6, u) * (1 - sm(3.2, 3.6, u)) : 0, patPhase: seg.t0 + 1.3 },
      extra: { laugh: isPat ? 0 : 0.0 } };
  } else if (name === 'shrug') {
    const w = sm(0.2, 0.6, u) * (1 - sm(1.8, 2.4, u));
    cam(FULL(1.6, 9.0, 8, 4, 0.45));
    pose = { face: VX('innocent'), body: { shrug: w }, armL: { preset: 'shrug', from: 'rest', mix: w }, armR: { preset: 'shrug', from: 'rest', mix: w }, head: { roll: -0.12 * w, yaw: 0.1 * w } };
  } else if (name === 'kickback' || name === 'kick') {
    // calm face toward "Fear" (camera, front-right) — peripheral glance — chamber — KICK — hold — recover — innocent shrug
    S.mag.visible = true;
    const back = name === 'kickback';
    const u0 = u;
    if (back) u = 2.3 + u * 0.2;   // hold the extension, seen from behind
    const peri = sm(0.3, 0.6, u) * (1 - sm(1.4, 1.6, u));
    const kick = u < 1.6 ? 0 : u < 1.95 ? -0.5 * sm(1.6, 1.9, u) : u < 2.1 ? lerp(-0.5, 1.12, ease.out((u - 1.95) / 0.15)) : u < 2.6 ? lerp(1.12, 1.0, (u - 2.1) / 0.5) : 1.0 * (1 - sm(2.6, 3.3, u));
    const hit = u > 2.06 ? Math.min(1, (u - 2.06) * 1.5) : 0;
    S.mag.position.set(-0.95 - hit * 1.6, hit * 1.2 * (1 - hit) * 2, -1.65 - hit * 3.0); S.mag.rotation.x = -hit * 1.4;
    const shrugW = sm(3.6, 4.0, u) * (1 - sm(4.6, 5.0, u));
    const face = u < 1.55 ? mixP(VX('calm'), VX('peripheral', { gazeYaw: -0.62 }), peri) : u < 3.4 ? VX('calm', { mSmile: 0.2, lidU: 0.8 }) : mixP(VX('calm'), VX('innocent'), sm(3.4, 3.7, u));
    cam(back ? framed([-0.3, 1.2, -0.4], { dist: 7.5, yaw: -140 + 20 * u0, pitch: 8, fov: 32, screenY: 0.47, drift: 0 })
      : framed([-0.55, 1.45, 0.15], { dist: 10.0, yaw: -42, pitch: 1, fov: 32, screenY: 0.46, drift: 0 }));
    pose = { yaw: 0.1, face, extra: { kick, kickSide: 'R', kickTarget: [-0.85, 1.25, -1.55], kickLevel: 1 }, gaze: framed([0, 2, 0], { dist: 6, yaw: -20 }).pos, body: { shrug: shrugW },
      armL: shrugW > 0 ? { preset: 'shrug', from: 'rest', mix: shrugW } : {}, armR: shrugW > 0 ? { preset: 'shrug', from: 'rest', mix: shrugW } : {} };
    S.dbg = () => console.log(`KICK t=${t.toFixed(2)} kick ${kick.toFixed(2)} foot`, vd.anchor('kickFoot').toArray().map((v) => v.toFixed(2)).join(','), 'head', vd.anchor('head').toArray().map((v) => v.toFixed(2)).join(','));
  } else if (name === 'latch') {
    S.cg.g.visible = true; S.cg.g.position.set(0.55, 0.75, 1.55); S.cg.g.rotation.y = Math.PI;
    const latch = S.cg.latch.getWorldPosition(new THREE.Vector3());
    const w = sm(0.3, 1.4, u);
    cam(framed([0.35, 1.45, 1.0], { dist: 5.2, yaw: 38, pitch: 6, fov: 32, screenY: 0.44, drift: 0 }));
    pose = { face: VX('tender', { gazePitch: -0.1 }), gaze: latch, body: { lean: 0.32 * w, crouch: 0.3 * w }, head: { pitch: 0.22 * w },
      armL: { preset: 'tip', target: latch.clone().add(V(0, 0, -0.03)), reach: w, fingers: [-0.1, -0.35, 1] } };
  } else if (name === 'sit') {
    const w = sm(0.2, 1.2, u);
    cam(FULL(1.3, 8.0, 20, 6, 0.48));
    pose = { face: VX('curious'), body: { sit: w }, armL: { preset: 'belly', from: 'rest', mix: w }, armR: { preset: 'belly', from: 'rest', mix: w }, head: { roll: 0.1 * w } };
  } else if (name === 'kneel') {
    const w = sm(0.2, 1.0, u);
    cam(FULL(1.3, 8.0, 20, 6, 0.48));
    pose = { face: VX('tender'), body: { kneel: w, lean: 0.15 * w }, armL: { preset: 'open', from: 'rest', mix: w }, armR: { preset: 'open', from: 'rest', mix: w }, head: { pitch: 0.15 * w } };
  } else if (name === 'wave') {
    cam(FULL(1.7, 9.0, 0, 4, 0.45));
    pose = { face: VX('hopeful'), armR: { preset: 'wave', from: 'rest', mix: sm(0.1, 0.5, u), offset: [0.12 * Math.sin(u * 9) * sm(0.4, 0.6, u), 0, 0] }, gaze: 'camera' };
  } else if (name === 'cosmos') {
    const c = sm(0.2, 1.5, u);
    S.look = { ...S.look, exposure: 0.9 };
    S.skyU.uTop.value.set(0x0c0a22); S.skyU.uMid.value.set(0x231a44); S.skyU.uBot.value.set(0x3a2a55); S.key.intensity = 0.9; S.hemi.intensity = 0.35; S.groundMat.color.set(0x3a3048);
    cam(FULL(1.8, 7.5, 12, 4, 0.42));
    pose = { face: VX('proud'), extra: { cosmos: c }, armL: { preset: 'open', from: 'rest', mix: c }, armR: { preset: 'open', from: 'rest', mix: c } };
  } else if (name === 'silhouette') {
    // TRUE backlight: low sun behind the Void, almost no fill -> a dark silhouette against a bright dusk sky
    S.skyU.uTop.value.set(0x4a3f8f); S.skyU.uMid.value.set(0xf09a9a); S.skyU.uBot.value.set(0xffc27a); S.skyU.uSun.value.set(0.05, 0.12, -1); S.skyU.uSunK.value = 1;
    S.key.intensity = 2.0; S.key.position.set(0.5, 1.6, -9); S.key.castShadow = false; S.rim.intensity = 0.0; S.hemi.intensity = 0.16; S.groundMat.color.set(0x6a4a60);
    S.look = { ...S.look, exposure: 1.0, bloom: 0.75 };
    cam(framed([0, 1.6, 0], { dist: 10, yaw: 0, pitch: -3, fov: 32, screenY: 0.47, drift: 0 }));
    pose = { face: VX('gentle'), yaw: 0.6 * Math.sin(u * 0.8), gaze: 'camera', extra: { rim: 1.6, eyeGlow: 1.15 } };
  }
  EYE_LIGHT.uKeyDir.value.copy(S.key.position).normalize();
  applyShot(app.camera, shot, t);
  vd.update(t, pose);
  if (S.dbg) { S.dbg(); S.dbg = null; }
  S.lab.set(`${name}  t=${t.toFixed(2)}`);
}
