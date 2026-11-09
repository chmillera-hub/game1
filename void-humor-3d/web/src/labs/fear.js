// Lab: FEAR — turntable (0–4 s), expression sheet (1 s each), then key poses / actions (see `segments`).
//   node tools/render.js sheet --lab fear --from 0 --to 3.5 --n 8 --cols 4 --out out/sheets/fear_turn.jpg
//   node tools/render.js sheet --lab fear --from 4.6 --to 29.6 --n 26 --cols 6 --out out/sheets/fear_expr.jpg
//   node tools/render.js stills --lab fear --t 40,50 --out out/stills
// Every pose is a pure function of t; the rig gets the pose FUNCTION so tuft/scarf secondary motion can look back
// in time (clamped to the segment start so segment switches don't "whip" the tuft).
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { Particles, CELL } from '../core/particles.js';
import { glowSprite } from '../core/materials.js';
import { clamp, lerp, smooth, fbm1, noise1, hash1 } from '../core/util.js';
import { FX, mixFace, walkSpeed, WALK } from '../chars/fear.js';

const TAU = Math.PI * 2;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const sm = (a, b, x) => smooth((x - a) / (b - a));
const env = (x, a, b, fi = 0.2, fo = 0.2) => sm(a, a + fi, x) * (1 - sm(b - fo, b, x));

export const EXPRS = ['neutral', 'worried', 'nervous', 'scared', 'terror', 'flinch', 'cry', 'sob', 'sniffle', 'startle', 'listen', 'curious',
  'peek', 'wonder', 'awe', 'shy', 'shySmile', 'hopeful', 'relieved', 'happy', 'giggle', 'sad', 'gulp', 'trust', 'whimper', 'confused'];
const T_EX = 4, T_ACT = T_EX + EXPRS.length;
const ACTS = [
  ['idle', 3], ['walk', 3], ['sneak', 4], ['run', 2.5], ['noise', 5], ['tremble', 3], ['cage', 6], ['cry', 5.5], ['hug', 3.5],
  ['wonder', 5.5], ['shy', 4], ['partner', 4.5], ['cling', 3.5], ['sit', 3], ['kneel', 3], ['cower', 3], ['wave', 2.5], ['snap', 3.5], ['talk', 3],
  ['cageWide', 4], ['cageSide', 4],   // (appended so earlier segment times stay stable) cage clearance checks
];
export const segments = [[0, 4, 'turntable'], ...EXPRS.map((n, i) => [T_EX + i, T_EX + i + 1, 'expr:' + n])];
{ let t0 = T_ACT; for (const [n, d] of ACTS) { segments.push([t0, t0 + d, n]); t0 += d; } }
export const duration = segments[segments.length - 1][1];

function segAt(t) {
  for (const s of segments) if (t >= s[0] && t < s[1]) return { name: s[2], u: t - s[0], dur: s[1] - s[0], t0: s[0] };
  const s = segments[segments.length - 1];
  return { name: s[2], u: t - s[0], dur: s[1] - s[0], t0: s[0] };
}

// ---------------------------------------------------------------------------------------------------------
// props
const CAGE = { R: 0.42, H: 1.02, n: 16, pos: [0, 0, -0.02] };
const FEAR_IN_CAGE = [0, 0, 0.0];   // ~2 cm in front of the cage centre: body + scarf stay >= 2 cm inside the bars
function cage() {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: 0xb79a5a, metalness: 0.75, roughness: 0.35 });
  for (let i = 0; i < CAGE.n; i++) {
    const a = ((i + 0.5) / CAGE.n) * TAU;
    const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.0075, 0.0075, CAGE.H, 6), m);
    bar.position.set(Math.sin(a) * CAGE.R, CAGE.H / 2, Math.cos(a) * CAGE.R); g.add(bar);
  }
  for (const y of [0.012, 0.35, CAGE.H]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(CAGE.R, 0.011, 6, 48), m); ring.rotation.x = Math.PI / 2; ring.position.y = y; g.add(ring); }
  for (let i = 0; i < 8; i++) {
    const arc = new THREE.Mesh(new THREE.TorusGeometry(CAGE.R, 0.006, 5, 24, Math.PI), m);
    arc.rotation.y = (i / 8) * Math.PI; arc.position.y = CAGE.H; g.add(arc);
  }
  const base = new THREE.Mesh(new THREE.CylinderGeometry(CAGE.R + 0.03, CAGE.R + 0.04, 0.03, 40), new THREE.MeshStandardMaterial({ color: 0x5a4870, roughness: 0.8 }));
  base.position.y = -0.012; g.add(base);
  const tag = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.05, 0.004), new THREE.MeshStandardMaterial({ color: 0xe9dcc0, roughness: 0.8 }));
  tag.position.set(0.24, 0.3, CAGE.R * 0.8 + 0.02); tag.rotation.set(0, 0.6, 0.12); g.add(tag);
  g.position.set(...CAGE.pos);
  return g;
}
const barPoint = (i, y) => { const a = ((i + 0.5) / CAGE.n) * TAU; return V(CAGE.pos[0] + Math.sin(a) * CAGE.R, y, CAGE.pos[2] + Math.cos(a) * CAGE.R); };

function partnerBlob() {
  // a big soft dark stand-in (the Void's scale) with one large hand
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: 0x3a3272, roughness: 0.6, emissive: 0x161040 });
  const b = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), m); b.scale.set(1.0, 1.45, 0.9); b.position.y = 1.35; g.add(b);
  const hand = new THREE.Mesh(new THREE.SphereGeometry(0.11, 20, 14), m); hand.scale.set(1, 0.7, 1.25); g.add(hand);
  const finger = new THREE.Mesh(new THREE.CapsuleGeometry(0.035, 0.1, 4, 10), m); finger.rotation.x = Math.PI / 2; finger.position.set(0, 0, 0.12); hand.add(finger);
  for (const sx of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 12), new THREE.MeshBasicMaterial({ color: 0xe8f4ff })); e.position.set(sx * 0.25, 2.35, 0.78); g.add(e); }
  return { g, hand, finger };
}

function label() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 64;
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.01), new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, toneMapped: false }));
  m.renderOrder = 100; m.position.set(-0.035, -0.074, -0.3);
  const st = { m, last: '' };
  st.set = (s) => { if (s === st.last) return; st.last = s; const g = c.getContext('2d'); g.clearRect(0, 0, 512, 64); g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(0, 0, 512, 64); g.fillStyle = '#fff'; g.font = 'bold 34px sans-serif'; g.fillText(s, 14, 44); tex.needsUpdate = true; };
  return st;
}

// ---------------------------------------------------------------------------------------------------------
export async function setup(app) {
  const scene = new THREE.Scene();
  const skyU = { uTop: { value: new THREE.Color(0x1d1838) }, uMid: { value: new THREE.Color(0x4a3a6e) }, uBot: { value: new THREE.Color(0x6a5078) } };
  const sky = new THREE.Mesh(new THREE.SphereGeometry(40, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: skyU,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform vec3 uTop, uMid, uBot; varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 c = h > 0.0 ? mix(uMid, uTop, smoothstep(0.0, 0.5, h)) : mix(uMid, uBot, smoothstep(0.0, -0.2, h)); gl_FragColor = vec4(c, 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(12, 48), new THREE.MeshStandardMaterial({ color: 0x5c4a6a, roughness: 0.95 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const hemi = new THREE.HemisphereLight(0xd8ccff, 0x30243c, 1.0); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffe2c6, 2.3); key.position.set(2.2, 3.2, 3.4); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); Object.assign(key.shadow.camera, { left: -1.5, right: 1.5, top: 1.5, bottom: -1.5, near: 0.5, far: 12 }); key.shadow.bias = -0.0006;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x9fb4ff, 1.9); rim.position.set(-2.5, 2.2, -2.6); scene.add(rim);
  const fill = new THREE.DirectionalLight(0xc6b0ff, 0.5); fill.position.set(-2.5, 1.0, 2.0); scene.add(fill);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  const fear = await app.char('FEAR');
  scene.add(fear.root);
  const cg = cage(); scene.add(cg); cg.visible = false;
  const partner = partnerBlob(); scene.add(partner.g); partner.g.visible = false;
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.085, 1.0, 24), new THREE.MeshStandardMaterial({ color: 0x2a2450, roughness: 0.7, emissive: 0x100a28 }));
  scene.add(post); post.visible = false;
  const bucket = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.11, 0.24, 24, 1, true), new THREE.MeshStandardMaterial({ color: 0x8a96a8, metalness: 0.6, roughness: 0.4, side: THREE.DoubleSide }));
  bucket.position.set(-1.3, 0.12, 0.1); bucket.rotation.z = 1.2; scene.add(bucket); bucket.visible = false;
  const sky2 = new Particles({ max: 260, intensity: 1.5 }); scene.add(sky2.mesh);
  const cosmosGlow = glowSprite(0x8a70ff, 4.0, 0); cosmosGlow.position.set(0, 2.4, -2.5); scene.add(cosmosGlow);
  scene.add(app.camera);
  const lab = label(); app.camera.add(lab.m);
  return { scene, fear, cg, partner, post, bucket, sky2, cosmosGlow, skyU, key, rim, hemi, lab,
    look: { bloom: 0.55, bloomThreshold: 0.78, bloomRadius: 0.5, exposure: 1.05, vignette: 0.2, sat: 1.05 } };
}

// ---------------------------------------------------------------------------------------------------------
const FULL = (x = 0, y = 0.44, dist = 2.3, yaw = 0, pitch = 4, screenY = 0.46, fov = 30) => framed([x, y, 0], { dist, yaw, pitch, fov, screenY, drift: 0 });
const talkSample = (u, a, b, seed = 1) => {
  if (u < a || u > b) return false;
  const e = env(u, a, b, 0.08, 0.1);
  const o = Math.max(0, Math.sin((u - a) * TAU * 3.6 + 0.8 * Math.sin((u - a) * 7.3))) * (0.45 + 0.3 * noise1(u * 5, seed));
  return { open: o * e, wide: 0.2 + 0.2 * noise1(u * 3, seed + 1), round: 0.35 + 0.3 * noise1(u * 4, seed + 2), close: 0 };
};

/** cowering in the cage gripping two bars beside the face (bars at +-56 deg), crying, then peeking out hopeful */
function cagePose(u) {
  const c = sm(0.1, 1.2, u), cr = sm(2.4, 3.2, u);
  const g = sm(0.5, 1.4, u);
  const peek = env(u, 4.2, 6.2, 0.4, 0.3);
  let face = mixFace(FX('scared'), FX('cry'), cr);
  face = mixFace(face, FX('hopeful', { wet: 1, tearL: 0.6, tearR: 0.6 }), peek * 0.8);
  return { pos: FEAR_IN_CAGE, face, gaze: 'camera', body: { cower: 0.55 * c * (1 - 0.4 * peek), lean: 0.04 },
    head: { pitch: 0.12 * (1 - peek) - 0.1 * peek, roll: 0.08 * Math.sin(u * 0.7), up: 0.02 * peek, forward: 0.015 * peek },
    extra: { tremble: 0.6 * c * (1 - 0.5 * peek), cry: 0.8 * cr },
    armL: { preset: 'grip', target: barPoint(2, 0.46 + 0.04 * peek), reach: g }, armR: { preset: 'grip', target: barPoint(CAGE.n - 3, 0.43 + 0.04 * peek), reach: g } };
}

/** pose + shot + props at t (pure). */
function act(t) {
  const seg = segAt(t), u = seg.u;
  let name = seg.name;
  const R = { pose: { face: FX('neutral') }, shot: FULL(), props: {}, label: name };
  if (name === 'turntable') {
    R.pose = { yaw: (t / 4) * TAU, face: FX('neutral', { autoBlink: 0, saccade: 0 }) };
    R.shot = FULL(0, 0.45, 2.15, 0, 4, 0.47);
  } else if (name.startsWith('expr:')) {
    const ex = name.slice(5), i = EXPRS.indexOf(ex);
    const prev = i > 0 ? FX(EXPRS[i - 1]) : FX('neutral');
    const face = mixFace(prev, FX(ex), sm(0, 0.25, u));
    face.autoBlink = 0; if (!['nervous', 'listen', 'shy'].includes(ex)) face.saccade = 0;
    const extra = {}, head = {}, body = {};
    if (ex === 'cry' || ex === 'sob') extra.cry = ex === 'sob' ? 1 : 0.7;
    if (ex === 'sob') extra.sob = 1;
    if (ex === 'awe') extra.cry = 0.35;
    if (ex === 'scared' || ex === 'terror') extra.tremble = ex === 'terror' ? 0.8 : 0.4;
    if (ex === 'startle') extra.startle = env(u, 0, 1, 0.1, 0.5), extra.tuftPerk = 1;
    if (ex === 'listen') { head.yaw = -0.35 * sm(0, 0.3, u); head.roll = 0.12; extra.tuftPerk = 0.7; face.gazeYaw = -0.25; }
    if (ex === 'wonder' || ex === 'awe') { head.pitch = -0.22; face.gazePitch = 0.12; }
    if (ex === 'shy' || ex === 'shySmile') { head.roll = -0.12; head.pitch = 0.1; }
    if (ex === 'sad' || ex === 'whimper') { head.pitch = 0.12; extra.tuftDroop = 0.7; }
    if (ex === 'curious' || ex === 'confused') head.roll = 0.16;
    if (ex === 'flinch') { head.pitch = 0.1; head.yaw = -0.15; body.shrug = 0.6 * sm(0, 0.2, u); extra.tremble = 0.5; extra.tuftDroop = 0.4; }
    if (ex === 'sob') extra.tuftDroop = 0.6;
    if (ex === 'gulp') body.shrug = 0.3;
    R.pose = { face, extra, head, body, gaze: ex === 'shy' || ex === 'shySmile' ? null : 'camera' };
    R.shot = framed([0, 0.6, 0], { dist: 1.5, yaw: 9, pitch: 3, fov: 30, screenY: 0.4, drift: 0 });
    R.label = 'expr: ' + ex;
  } else if (name === 'idle') {
    R.pose = { face: FX('neutral'), gaze: 'camera', head: { yaw: 0.15 * Math.sin(u * 1.3), roll: 0.05 * Math.sin(u * 0.9) } };
    R.shot = FULL(0, 0.45, 2.0, 18, 5, 0.46);
  } else if (name === 'walk' || name === 'sneak' || name === 'run') {
    const st = WALK[name], sp = walkSpeed(name), ph = u * st.cad;
    const x = -0.55 * (name === 'run' ? 2.5 : name === 'sneak' ? 0.6 : 1) + u * sp;
    R.pose = { pos: [x, 0, 0], yaw: Math.PI / 2 - (name === 'sneak' ? 0.5 : 0.25), walk: { amount: 1, phase: ph, style: name },
      face: FX(name === 'run' ? 'terror' : name === 'sneak' ? 'nervous' : 'worried'), gaze: name === 'sneak' ? V(x + 1, 0.5, 1.2 * Math.sin(u * 1.4)) : null,
      head: name === 'sneak' ? { yaw: -0.5 * Math.sin(u * 1.4), pitch: 0.05 } : {}, extra: { tremble: name === 'run' ? 0 : 0.15 } };
    R.shot = framed([x, 0.42, 0], { dist: 2.25, yaw: 18, pitch: 4, fov: 30, screenY: 0.46, drift: 0 });
  } else if (name === 'noise') {
    // startle on a crash (u=0.6), head snaps toward it (screen-left), tuft perks; "what's that noise?" (1.9-3.1); gulp
    const src = V(-1.3, 0.3, 0.1);
    const st = env(u, 0.6, 1.3, 0.06, 0.5);
    const snap = sm(0.62, 0.76, u);
    const back = sm(3.6, 4.3, u);
    let face = FX('neutral');
    face = mixFace(face, FX('startle'), sm(0.6, 0.68, u));
    face = mixFace(face, FX('listen'), sm(1.2, 1.6, u));
    face = mixFace(face, FX('worried'), sm(3.2, 3.5, u));
    face = mixFace(face, FX('gulp'), env(u, 3.6, 4.4, 0.1, 0.3));
    R.pose = { face, gaze: snap > 0.5 && back < 0.5 ? src : 'camera', extra: { startle: st, tuftPerk: clamp(snap * 0.8 * (1 - back * 0.7)), tremble: 0.25 * sm(1.0, 1.5, u) },
      head: { look: src, track: 0.45 * snap * (1 - back), roll: 0.12 * sm(1.2, 1.6, u) * (1 - back) }, body: { twist: -0.18 * snap * (1 - back) },
      armL: { preset: 'up', from: 'rest', mix: env(u, 0.6, 1.5, 0.08, 0.5) * 0.7 }, armR: { preset: 'chest', from: 'rest', mix: sm(0.65, 0.9, u) * (1 - sm(3.4, 4, u)) },
      speech: talkSample(u, 1.9, 3.1, 3), blinkAt: [seg.t0 + 0.55] };
    R.shot = FULL(-0.12, 0.52, 2.1, -12, 4, 0.5);
    R.props.bucket = true;
  } else if (name === 'tremble') {
    const tr = sm(0.2, 2.0, u);
    R.pose = { face: mixFace(FX('worried'), FX('scared'), tr), gaze: 'camera', extra: { tremble: tr }, armL: { preset: 'hug', from: 'rest', mix: sm(0.2, 0.8, u) }, armR: { preset: 'hug', from: 'rest', mix: sm(0.3, 0.9, u) }, body: { shrug: 0.4 * tr } };
    R.shot = FULL(0, 0.5, 1.45, 10, 3, 0.42);
  } else if (name === 'cage' || name === 'cageWide' || name === 'cageSide') {
    const uu = name === 'cage' ? u : 1.4 + u * 1.1;     // the wide/side shots replay cower -> cry -> peek
    R.pose = cagePose(uu);
    R.props.cage = true;
    R.shot = name === 'cage' ? framed([0, 0.52, 0.02], { dist: 1.7, yaw: 6, pitch: 5, fov: 30, screenY: 0.43, drift: 0 })
      : name === 'cageWide' ? framed([0, 0.5, -0.02], { dist: 3.0, yaw: 0, pitch: 4, fov: 30, screenY: 0.47, drift: 0 })
        : framed([0, 0.5, -0.02], { dist: 2.6, yaw: 90, pitch: 2, fov: 30, screenY: 0.47, drift: 0 });
  } else if (name === 'cry') {
    const wl = env(u, 1.8, 3.5, 0.35, 0.35), wr = env(u, 3.4, 5.2, 0.35, 0.4);
    const sniff = env(u, 3.25, 3.75, 0.08, 0.35) + env(u, 4.95, 5.45, 0.08, 0.35);   // sniff + shoulders up after each rub
    let face = mixFace(FX('sob'), FX('sniffle'), sm(1.6, 2.2, u));
    face = mixFace(face, FX('sniffle', { mPout: 0.6, mPress: 0.6, lidU: 0.7, browIn: 1 }), clamp(sniff));
    R.pose = { face, gaze: 'camera', head: { pitch: 0.1 - 0.06 * sm(2, 3, u) - 0.05 * sniff },
      extra: { cry: 1 - 0.3 * sm(3, 5, u), sob: 1 - sm(1.3, 1.9, u), tuftDroop: 0.6 },
      armL: { preset: 'wipe', from: 'rest', mix: wl }, armR: { preset: 'wipe', from: 'rest', mix: wr }, body: { slump: 0.3, shrug: 0.45 * clamp(sniff), stretch: 0.02 * sniff } };
    R.shot = FULL(0, 0.55, 1.3, 10, 3, 0.42);
  } else if (name === 'hug') {
    const w = sm(0.1, 0.8, u), rock = Math.sin((u - 0.8) * TAU * 0.55) * sm(0.6, 1.2, u);
    R.pose = { face: mixFace(FX('worried'), FX('whimper', { lidU: 0.86 }), w), gaze: 'camera', extra: { tremble: 0.25 * w, tuftDroop: 0.35 * w },
      armL: { preset: 'hug', from: 'rest', mix: w }, armR: { preset: 'hug', from: 'rest', mix: sm(0.25, 0.95, u) },
      body: { shrug: 0.55 * w, hunch: 0.22 * w, squash: 0.04 * w, twist: 0.07 * rock, tilt: 0.045 * rock },
      head: { pitch: 0.1 * w, roll: -0.08 * w - 0.05 * rock } };
    R.shot = FULL(0, 0.48, 1.6, 14, 3, 0.43);
  } else if (name === 'wonder') {
    const up = sm(0.3, 1.6, u), aw = sm(2.6, 3.6, u);
    let face = mixFace(FX('curious'), FX('wonder'), up);
    face = mixFace(face, FX('awe'), aw * 0.8);
    face.gazePitch = 0.2 * up;
    R.pose = { face, gaze: null, head: { pitch: -0.6 * up, roll: 0.05 * Math.sin(u * 0.8) }, body: { lean: -0.06 * up, stretch: 0.02 * up },
      extra: { cry: 0.45 * aw, glow: 1 + 0.3 * up, tuftPerk: 0.3 * up },
      armL: { preset: 'clasp', from: 'rest', mix: sm(1.2, 2.2, u) }, armR: { preset: 'clasp', from: 'rest', mix: sm(1.3, 2.3, u) } };
    R.props.cosmos = up;
    R.shot = framed([0, 0.6, 0], { dist: 1.7, yaw: 38, pitch: -2, fov: 34, screenY: 0.6, drift: 0 });
  } else if (name === 'shy') {
    // eyes down, a small pressed smile grows; ONE quick glance up at the camera (u 2.0-2.55), then down again, smiling
    const a = sm(0.3, 1.0, u), sm2 = sm(1.2, 2.0, u), look = env(u, 2.0, 2.55, 0.08, 0.12);
    let face = mixFace(FX('neutral'), FX('shy'), a);
    face = mixFace(face, FX('shySmile'), sm2);
    face = mixFace(face, FX('shySmile', { lidU: 1.05, mSmile: 0.42, gazePitch: 0, gazeYaw: 0 }), look);
    R.pose = { face, gaze: look > 0.5 ? 'camera' : null, head: { roll: -0.15 * a, pitch: 0.14 * a * (1 - look * 0.5), yaw: 0.1 * a * (1 - look) },
      body: { twist: 0.1 * Math.sin(u * 1.8) * a, shrug: 0.25 * a },
      armL: { preset: 'fidget', from: 'rest', mix: a }, armR: { preset: 'fidget', from: 'rest', mix: a }, extra: {} };
    R.shot = FULL(0, 0.5, 1.4, 12, 3, 0.43);
  } else if (name === 'partner') {
    // a big partner (Void stand-in) at Fear's left lowers a finger; Fear looks up and takes it
    const pr = sm(0.0, 0.5, u), r = sm(1.1, 2.1, u);
    const hp = V(0.42, 0.66 - 0.05 * r, 0.3);
    R.props.partner = { hand: hp, pos: [1.05, 0, -0.55] };
    const fingerTip = hp.clone().add(V(-0.02, -0.03, 0.15));
    let face = mixFace(FX('worried'), FX('hopeful'), sm(0.6, 1.4, u));
    face = mixFace(face, FX('trust'), sm(2.4, 3.2, u));
    R.pose = { pos: [0, 0, 0.3], yaw: 0.25, face, gaze: V(0.75, 2.2, -0.1), head: { look: V(0.75, 2.2, -0.1), track: 0.55 * pr }, extra: { tuftPerk: 0.25 },
      armL: { preset: 'hold', target: fingerTip, reach: r, hand: { grip: 0.5 + 0.4 * r, curl: 0.5 } }, armR: { preset: 'chest', from: 'rest', mix: sm(0.4, 1.2, u) } };
    R.shot = framed([0.06, 0.62, 0.3], { dist: 2.9, yaw: -10, pitch: 4, fov: 32, screenY: 0.52, drift: 0 });
  } else if (name === 'cling') {
    // hides behind a big partner's leg (post), both hands on it, peeking out past its edge
    const w = sm(0.2, 1.0, u), pk = sm(1.4, 2.2, u);
    const c = V(0.13, 0, 0.27), pr = 0.08;              // post centre / radius
    R.props.post = c;
    const fp = V(-0.1, 0, 0), n = V(fp.x - c.x, 0, fp.z - c.z).normalize(), tn = V(-n.z, 0, n.x);   // post surface normal toward Fear
    const onPost = (side, y) => c.clone().addScaledVector(n, pr + 0.012).addScaledVector(tn, side * 0.035).setY(y);
    const palmIn = n.clone().negate().toArray();
    R.pose = { pos: fp.toArray(), yaw: 0.35, face: mixFace(FX('scared'), FX('peek'), pk * 0.7), gaze: 'camera', head: { yaw: -0.35 * w - 0.15 * pk, roll: 0.16 * w, forward: 0.01 * pk },
      body: { tilt: 0.12 * w, lean: 0.08 * w, shrug: 0.3 * w }, extra: { tremble: 0.35 * w },
      armL: { target: onPost(1, 0.43), reach: w, palm: palmIn, fingers: [0.1, 1, 0.1], hand: { curl: 0.55, cup: 0.5 } },
      armR: { target: onPost(-1, 0.36), reach: sm(0.4, 1.2, u), palm: palmIn, fingers: [0.1, 1, 0.1], hand: { curl: 0.6, cup: 0.5 } } };
    R.shot = FULL(0.0, 0.45, 1.9, -6, 4, 0.45);
  } else if (name === 'sit') {
    const s = sm(0.2, 1.3, u);
    R.pose = { face: mixFace(FX('neutral'), FX('relieved'), sm(1.2, 2.0, u)), gaze: 'camera', body: { sit: s }, armL: { preset: 'tummy', from: 'rest', mix: sm(1.3, 2.0, u) }, armR: { preset: 'rest' } };
    R.shot = FULL(0, 0.38, 2.0, 30, 6, 0.48);
  } else if (name === 'kneel') {
    const k = sm(0.2, 1.3, u);
    R.pose = { face: mixFace(FX('neutral'), FX('hopeful'), sm(1.0, 1.8, u)), gaze: 'camera', body: { kneel: k }, head: { pitch: -0.12 * k }, armL: { preset: 'clasp', from: 'rest', mix: sm(0.9, 1.7, u) }, armR: { preset: 'clasp', from: 'rest', mix: sm(1.0, 1.8, u) } };
    R.shot = FULL(0, 0.4, 2.0, 30, 6, 0.48);
  } else if (name === 'cower') {
    const c = sm(0.1, 0.5, u);
    R.pose = { face: mixFace(FX('scared'), FX('flinch'), c), gaze: 'camera', body: { cower: c }, head: { pitch: 0.12 * c, yaw: -0.22 * c }, extra: { tremble: 0.8 * c, tuftDroop: 0.5 * c },
      armL: { preset: 'shield', from: 'rest', mix: c }, armR: { preset: 'shield', from: 'rest', mix: sm(0.15, 0.55, u) } };
    R.shot = FULL(0, 0.42, 1.7, 10, 4, 0.45);
  } else if (name === 'wave') {
    const w = sm(0.1, 0.6, u);
    R.pose = { face: FX('shySmile'), gaze: 'camera', head: { roll: -0.12 }, armR: { preset: 'wave', from: 'rest', mix: w, wave: w }, armL: { preset: 'chest', from: 'rest', mix: w } };
    R.shot = FULL(0, 0.45, 2.0, 10, 3, 0.45);
  } else if (name === 'snap') {
    const k = Math.floor(u / 0.85), lu = u - k * 0.85;
    const from = k === 0 ? 0 : (k % 2 ? 0.9 : -0.9), to = k % 2 ? -0.9 : 0.9;
    const yaw = lerp(from, to, sm(0, 0.12, lu));
    R.pose = { face: FX('listen'), gaze: null, head: { yaw, roll: 0.08 * Math.sign(yaw) }, extra: { tuftPerk: 0.4 } };
    R.shot = FULL(0, 0.55, 1.35, 0, 3, 0.42);
  } else if (name === 'talk') {
    R.pose = { face: FX('worried'), gaze: 'camera', speech: talkSample(u, 0.2, 2.8, 9), head: { yaw: 0.08 * Math.sin(u * 2.1), pitch: 0.05 * Math.sin(u * 3.1) },
      armR: { preset: 'chest', from: 'rest', mix: env(u, 0.3, 2.8, 0.4, 0.4) } };
    R.shot = framed([0, 0.6, 0], { dist: 1.5, yaw: 12, pitch: 3, fov: 30, screenY: 0.4, drift: 0 });
  }
  return R;
}

export async function update(t, app, S) {
  const seg = segAt(t);
  const R = act(t);
  S.cg.visible = !!R.props.cage;
  S.post.visible = !!R.props.post;
  if (R.props.post) S.post.position.set(R.props.post.x, 0.5, R.props.post.z);
  S.bucket.visible = !!R.props.bucket;
  S.partner.g.visible = !!R.props.partner;
  if (R.props.partner) { S.partner.g.position.set(...(R.props.partner.pos || [0.55, 0, -0.75])); S.partner.hand.position.copy(R.props.partner.hand).sub(S.partner.g.position); }
  // cosmos (wonder)
  const cz = R.props.cosmos || 0;
  S.sky2.begin();
  if (cz > 0) {
    for (let i = 0; i < 90; i++) {
      const a = hash1(i * 3 + 1) * TAU, rr = 0.6 + 2.4 * hash1(i * 7 + 2);
      const p = [Math.cos(a) * rr * 0.9, 1.4 + 1.8 * hash1(i * 11 + 3) + 0.05 * Math.sin(t * 0.3 + i), -0.8 - 1.5 * hash1(i * 13 + 4)];
      const cell = i % 11 === 0 ? CELL.galaxy : i % 7 === 0 ? CELL.nebula : CELL.star;
      const col = [0xffffff, 0xd8c8ff, 0x9feaff, 0xffd6f0][i % 4];
      S.sky2.add(p, cell === CELL.nebula ? 0.9 : cell === CELL.galaxy ? 0.35 : 0.05 + 0.05 * hash1(i), col, cz * (cell === CELL.nebula ? 0.35 : 0.9), t * 0.05 + i, cell);
    }
  }
  S.sky2.end();
  S.cosmosGlow.material.opacity = 0.18 * cz;
  applyShot(app.camera, R.shot, t);   // camera first: the face reads it (catchlights, gaze 'camera')
  const poseAt = (tt) => act(Math.max(tt, seg.t0)).pose;
  S.fear.update(t, poseAt);
  S.lab.set(R.label + '  ' + (t - seg.t0).toFixed(2));
}
