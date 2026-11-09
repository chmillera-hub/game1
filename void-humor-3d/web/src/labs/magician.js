// Lab: THE DEPRESSION MAGICIAN — turntable (0–4 s), expression sheet (1 s each), then key poses / actions with
// placeholder partners (a big plump Void stand-in to lurk behind, a little Fear bean to ogle, a fat kicking leg,
// a janitor's corner of buckets + a mop).
//   node tools/render.js sheet --lab magician --from 0 --to 4 --n 8 --cols 4 --out out/sheets/mag_turn.jpg
//   node tools/render.js sheet --lab magician --from 4.5 --to 21.5 --n 18 --cols 6 --out out/sheets/mag_expr.jpg
//   SEGMENTS (exported) lists every segment [t0, t1, name]; the HUD label shows it too.
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { contactShadow } from '../core/materials.js';
import { clamp, lerp, smooth, noise1, ease } from '../core/util.js';
import { MX } from '../chars/magician.js';

const TAU = Math.PI * 2;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const ramp = (lt, a, b) => smooth((lt - a) / (b - a));
const seg = [];
let T0 = 0;
function S(name, dur, fn) { seg.push({ name, t0: T0, t1: T0 + dur, fn }); T0 += dur; }

// synthetic lip-sync for talking demos (k scales the opening; whisper = small)
const talkSample = (t, k = 1) => {
  const o = Math.max(0, Math.sin(t * 11.3) * 0.55 + Math.sin(t * 4.1 + 1) * 0.3 + 0.1) * (0.55 + 0.45 * noise1(t * 2.5, 7));
  return { open: clamp(o * k, 0, 0.75), wide: 0.3 + 0.3 * noise1(t * 3, 9), round: clamp(0.4 * noise1(t * 2.2, 11)), close: o < 0.08 ? 0.6 : 0 };
};
// close-ups are framed on the rig's actual head anchor (two-pass in update())
const CLOSE = (yaw = 10, dist = 1.55, screenY = 0.4) => ({ close: { yaw, dist, screenY } });

// ---------------------------------------------------------------------------------- expression sheet (1 s each)
const EX = [
  ['sly (default rest)', { face: 'sly' }],
  ['lurk (peeking grin)', { face: 'lurk', gaze: [0.9, 1.4, 1.2], head: { yaw: -0.15, roll: 0.12 }, body: { peek: 0.3 } }],
  ['scheme + tapping', { face: 'scheme', armL: { preset: 'steeple' }, armR: { preset: 'steeple' }, extra: { dagger: false, pouch: false } }],
  ['gloat (too-wide grin)', { face: 'gloat', head: { pitch: -0.08 } }],
  ['hungry', { face: 'hungry', gaze: [0.6, 1.2, 1.4] }],
  ['LICK (tongue)', { face: 'hungry', lick: true }],
  ['relish', { face: 'relish', head: { roll: 0.15, pitch: -0.1 } }],
  ['gloating whisper (talk)', { face: 'whisper', talk: 0.55, armR: { preset: 'whisper' }, extra: { dagger: false }, head: { yaw: 0.25, roll: -0.1 } }],
  ['snicker', { face: 'snicker', body: { giggle: 1 }, armL: { preset: 'cover_mouth' }, extra: { pouch: false } }],
  ['innocent (who, me?)', { face: 'innocent', armL: { preset: 'behind' }, armR: { preset: 'behind' }, head: { roll: 0.15 } }],
  ['curious', { face: 'curious', head: { roll: -0.18 } }],
  ['uh-oh (sees the leg)', { face: 'uhoh', gaze: [0.5, 1.2, 1.5], body: { recoil: 0.3, shrug: 0.5 } }],
  ['popped (kicked)', { face: 'popped', extra: { eyePop: 1 } }],
  ['ow', { face: 'ow', armL: { preset: 'clutch_chest' }, extra: { pouch: false }, body: { hunch: 0.5 } }],
  ['dazed + dizzy', { face: 'dazed', extra: { dizzy: 1, tongueOut: 0.8 }, head: { roll: 0.25 } }],
  ['sulk', { face: 'sulk', head: { pitch: 0.15 }, body: { slump: 0.6 } }],
  ['annoyed', { face: 'annoyed', armL: { preset: 'crossed' }, armR: { preset: 'crossed' }, extra: { dagger: false, pouch: false } }],
  ['startled', { face: 'startled', body: { recoil: 0.5 } }],
];

S('turntable', 4, (lt, s) => ({
  pose: { yaw: (lt / 4) * TAU, face: 'sly', gaze: null, armL: { preset: 'rest' }, armR: { preset: 'rest' } },
  shot: framed([0, 1.06, 0], { dist: 4.6, yaw: 0, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }),
}));
for (const [name, e] of EX) {
  S('expr: ' + name, 1, (lt, s) => {
    const pose = { face: e.face, body: e.body, armL: e.armL, armR: e.armR, head: e.head, gaze: e.gaze ? V(...e.gaze) : 'camera', extra: { ...(e.extra || {}) } };
    pose.speech = e.talk ? talkSample(s.t, e.talk) : false;
    if (e.lick) pose.extra.lick = clamp((lt - 0.05) / 0.9);
    return { pose, ...CLOSE() };
  });
}

// ---------------------------------------------------------------------------------- actions
S('idle stoop, steepled fingers tapping', 3, (lt, s) => ({
  pose: { face: 'scheme', gaze: 'camera', armL: { preset: 'steeple' }, armR: { preset: 'steeple' }, extra: { dagger: false, pouch: false } },
  shot: framed([0, 1.1, 0], { dist: 3.6, yaw: 30, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }),
}));
S('sneak tiptoe (side)', 4, (lt, s) => {
  const M = s.mag, rate = M.walkRate('sneak'), sp = M.walkSpeed('sneak') * rate;
  const z = -1.2 + sp * lt;
  const look = Math.sin(lt * 1.7);
  return {
    pose: { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'sneak' }, face: 'lurk', head: { yaw: 0.5 * look, pitch: 0.05 }, gaze: V(2 * look, 1.2, z + 2) },
    shot: framed([0, 0.95, z], { dist: 4.4, yaw: 88, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }),
  };
});
S('sneak tiptoe (3/4 front)', 3, (lt, s) => {
  const M = s.mag, rate = M.walkRate('sneak'), sp = M.walkSpeed('sneak') * rate;
  const z = -1.0 + sp * lt;
  return {
    pose: { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate + 0.3, style: 'sneak' }, face: 'scheme', gaze: 'camera', armR: { preset: 'claw' }, armL: { preset: 'creep' }, extra: { pouch: false } },
    shot: framed([0, 1.0, z], { dist: 4.2, yaw: 32, pitch: 4, fov: 32, screenY: 0.44, drift: 0 }),
  };
});
S('walk (3/4)', 3, (lt, s) => {
  const M = s.mag, rate = M.walkRate('walk'), sp = M.walkSpeed('walk') * rate;
  const z = -1.2 + sp * lt;
  return { pose: { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'walk' }, face: 'sly', gaze: V(0, 1.5, z + 3) },
    shot: framed([0, 1.0, z], { dist: 4.4, yaw: 35, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }) };
});
S('run (side)', 2, (lt, s) => {
  const M = s.mag, rate = M.walkRate('run'), sp = M.walkSpeed('run') * rate;
  const z = -2 + sp * lt;
  return { pose: { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'run' }, face: 'startled' },
    shot: framed([0, 1.0, z], { dist: 4.8, yaw: 82, pitch: 2, fov: 32, screenY: 0.44, drift: 0 }) };
});
S('LURK: crouch, peek around the big one, tapping', 5, (lt, s) => {
  s.big.visible = true; s.fear.visible = true;
  const pk = ramp(lt, 0.4, 1.4) * (1 - 0.35 * ramp(lt, 3.6, 4.4));
  const edge = s.bigEdge();
  return {
    pos: [0, 0, 0],
    pose: { pos: [-0.05, 0, -1.05], yaw: 0.25, body: { crouch: 0.75, peek: -0.9 * pk }, face: ['lurk', 1], gaze: s.fearEyes,
      head: { follow: 0.4 * pk, roll: -0.15 * pk }, armL: { preset: 'edge', target: edge, palm: [0.6, 0, -0.8], fingers: [-0.2, 1, 0.3], reach: pk },
      armR: { preset: 'claw', reach: pk }, extra: { tap: 1, pouch: false } },
    shot: framed([0.4, 1.0, -0.5], { dist: 4.0, yaw: 22, pitch: 6, fov: 32, screenY: 0.44, drift: 0 }),
  };
});
S('LICK LIPS (close-up)', 3.2, (lt, s) => {
  s.fear.visible = true;
  const lick = lt < 0.4 ? 0 : clamp((lt - 0.4) / 1.25);
  const lick2 = lt < 1.9 ? 0 : clamp((lt - 1.9) / 1.0);
  const L = lick > 0 && lick < 1 ? lick : lick2;
  return { pose: { face: lt < 0.4 ? 'hungry' : (L > 0.1 && L < 0.9 ? ['hungry', 1] : 'gloat'), gaze: s.fearEyes, head: { pitch: -0.05, roll: 0.06 * Math.sin(lt * 2) }, extra: { lick: L }, speech: false },
    ...CLOSE(18, 1.1) };
});
S('gloating whisper-talk (lip-sync) + dagger', 4, (lt, s) => ({
  pose: { face: lt < 2 ? 'whisper' : 'gloat', speech: talkSample(s.t, 0.55), gaze: 'camera', head: { yaw: 0.2, roll: -0.08, pitch: 0.05 }, body: { hunch: 0.4 },
    armR: { preset: 'dagger_ready', reach: ramp(lt, 0.2, 0.8) }, armL: { preset: 'pouch' } },
  shot: framed([0, 1.45, 0.1], { dist: 2.3, yaw: 18, pitch: 2, fov: 30, screenY: 0.4, drift: 0 }),
}));
S('numbing dust: pouch pour', 3.5, (lt, s) => {
  const d = ramp(lt, 0.6, 1.2) * (1 - ramp(lt, 2.8, 3.3));
  return { pose: { face: d > 0.5 ? 'gloat' : 'scheme', gaze: V(0.2, 0.9, 1.4), armL: { preset: [['pouch', 1 - d], ['pour', d]] }, armR: { preset: 'dagger_low' }, extra: { dust: d } },
    shot: framed([0.1, 1.2, 0.2], { dist: 2.8, yaw: 40, pitch: 3, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('dagger stab at partner', 2.5, (lt, s) => {
  s.fear.visible = true;
  const wind = ramp(lt, 0.2, 0.7), stab = ramp(lt, 0.9, 1.05) * (1 - ramp(lt, 1.8, 2.3));
  return { pose: { face: stab > 0.5 ? 'gloat' : 'scheme', gaze: s.fearEyes, body: { lean: 0.15 * stab, recoil: 0.2 * wind * (1 - stab) },
    armR: { preset: [['dagger_ready', 1 - stab], ['dagger_stab', stab]], reach: wind }, armL: { preset: 'pouch' } },
    shot: framed([0.2, 1.2, 0.3], { dist: 3.2, yaw: 55, pitch: 3, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('KICKED in the chest -> flight', 3.2, (lt, s) => {
  s.kicker.visible = true;
  const hit = 0.8, tau = Math.max(0, lt - hit);
  // kicker leg swings in from +Z, hits the chest at `hit`
  const kick = lt < 0.45 ? 0 : lt < hit ? ease.in((lt - 0.45) / (hit - 0.45)) : 1 - ramp(lt, hit + 0.3, hit + 1.0);
  s.kickAmt = kick;
  const kicked = lt < hit ? 0 : clamp(tau / 0.06);
  const y = Math.max(0, 3.6 * tau - 3.9 * tau * tau), z = -3.0 * tau;
  const hatOff = clamp(tau / 0.25);
  const ht = tau;
  return {
    pose: { pos: [0, y, z], face: lt < 0.5 ? 'gloat' : lt < hit ? 'uhoh' : 'popped', gaze: lt < hit ? s.kickFoot() : 'camera',
      armR: { preset: 'dagger_ready' }, armL: { preset: 'pouch' }, body: { recoil: lt < hit ? 0.3 * ramp(lt, 0.5, 0.75) : 0 },
      extra: { kicked, flip: -1.3 * tau, hatOff, hatPos: [0.15, 2.05 + 3.2 * ht - 3.0 * ht * ht, 0.1 - 1.4 * ht], hatRot: [-4 * ht, 2 * ht, 1.5 * ht], dagger: true } },
    shot: framed([0, 1.35, -1.1], { dist: 6.2, yaw: 84, pitch: 4, fov: 34, screenY: 0.46, drift: 0 }),
  };
});
S('CRASH: upside-down, dizzy, bucket on head', 4.5, (lt, s) => {
  s.buckets.visible = true;
  const bk = ramp(lt, 1.6, 2.2);
  s.bucketDrop = 1 - bk;
  s.bucketOn = lt > 1.2;
  return {
    pose: { pos: [0, 0, -0.1], face: 'dazed', extra: { crashed: 1, dizzy: ramp(lt, 0.0, 0.5), hatOff: 1, hatPos: [0.55, 0.02, 0.42], hatRot: [0.1, 0.5, 1.5], dagger: false, pouch: true } },
    shot: framed([0.1, 0.62, 0.0], { dist: 3.2, yaw: 18, pitch: 8, fov: 32, screenY: 0.46, drift: 0 }),
  };
});
S('getting up -> limp off, clutching back', 4.5, (lt, s) => {
  s.buckets.visible = true;
  const M = s.mag;
  const up = 1 - ramp(lt, 0.0, 0.9);
  const w = ramp(lt, 1.0, 1.5), rate = M.walkRate('limp'), sp = M.walkSpeed('limp') * rate;
  const x = Math.max(0, lt - 1.0) * sp;
  return {
    pose: { pos: [x, 0, -0.1], yaw: Math.PI / 2 * w, walk: { amount: w, phase: Math.max(0, lt - 1.0) * rate, style: 'limp' }, face: lt < 1.2 ? 'dazed' : 'sulk',
      armL: { preset: 'clutch_back', reach: w }, armR: { preset: 'hang' }, head: { pitch: 0.12 },
      extra: { crashed: up, dizzy: 1 - ramp(lt, 0.4, 1.6), hatOff: 1 - ramp(lt, 1.6, 2.6), hatPos: [0.55, 0.02, 0.42], hatRot: [0.1, 0.5, 1.5], dagger: false } },
    shot: framed([0.8, 1.0, 0.0], { dist: 4.6, yaw: 15, pitch: 4, fov: 32, screenY: 0.44, drift: 0 }),
  };
});
S('sit (dazed) / kneel', 3.5, (lt, s) => {
  const si = ramp(lt, 0.2, 1.0) * (1 - ramp(lt, 1.8, 2.2)), kn = ramp(lt, 2.2, 2.9);
  return { pose: { face: si > 0.5 ? 'sulk' : 'scheme', gaze: 'camera', body: { sit: si, kneel: kn }, armL: { preset: si > 0.5 ? 'hang' : 'rest' }, armR: { preset: kn > 0.5 ? 'present' : 'rest' } },
    shot: framed([0, 0.75, 0], { dist: 3.8, yaw: 45, pitch: 5, fov: 32, screenY: 0.44, drift: 0 }) };
});
S('ta-da flourish / hand on hip', 2.5, (lt, s) => {
  const a = ramp(lt, 0.2, 0.6);
  return { pose: { face: 'gloat', gaze: 'camera', armL: { preset: 'hips', reach: a }, armR: { preset: 'present', reach: a }, extra: { dagger: false }, head: { roll: -0.1 * a } },
    shot: framed([0, 1.15, 0], { dist: 3.4, yaw: 20, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }) };
});
export const DURATION = T0;
export const SEGMENTS = seg.map((x) => [x.t0, x.t1, x.name]);

// ---------------------------------------------------------------------------------- set
export async function setup(app) {
  const scene = new THREE.Scene();
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 a = vec3(0.30,0.27,0.38), b = vec3(0.12,0.12,0.22); gl_FragColor = vec4(mix(a, b, smoothstep(-0.05, 0.5, h)), 1.0);\n#include <colorspace_fragment>\n}',
  }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 64), new THREE.MeshStandardMaterial({ color: 0x4a4658, roughness: 0.9 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const dots = new THREE.InstancedMesh(new THREE.CircleGeometry(0.03, 12), new THREE.MeshBasicMaterial({ color: 0x5c586c }), 400);
  let n = 0; const m = new THREE.Matrix4();
  for (let i = -10; i < 10; i++) for (let j = -10; j < 10; j++) { m.makeRotationX(-Math.PI / 2).setPosition(i * 0.5, 0.002, j * 0.5); dots.setMatrixAt(n++, m); }
  scene.add(dots);
  scene.add(new THREE.HemisphereLight(0xc8d0ff, 0x3a3448, 1.15));
  const key = new THREE.DirectionalLight(0xffe2c4, 2.4); key.position.set(2.2, 4, 3.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: 0.5, far: 18 }); key.shadow.bias = -0.0005;
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0x9fb8ff, 2.0); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  EYE_LIGHT.uKeyColor.value.set(1.0, 0.94, 0.86);
  const mag = await app.char('MAGICIAN');
  scene.add(mag.root);
  // big plump Void stand-in (lurk behind it)
  const big = new THREE.Group();
  const vm = new THREE.MeshStandardMaterial({ color: 0x2a2450, roughness: 0.6, emissive: 0x120c30 });
  const body = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 28), vm); body.scale.set(1.0, 1.25, 0.85); body.position.y = 1.2; big.add(body);
  const hd = new THREE.Mesh(new THREE.SphereGeometry(0.55, 32, 20), vm); hd.position.set(0, 2.3, 0.05); big.add(hd);
  big.position.set(0.95, 0, 0.35); big.visible = false; scene.add(big);
  const bigEdge = () => V(0.08, 1.45, -0.42);
  // little Fear bean stand-in
  const fear = new THREE.Group();
  const fm = new THREE.MeshStandardMaterial({ color: 0xcdb8ff, roughness: 0.5, emissive: 0x2a1a50 });
  const fb = new THREE.Mesh(new THREE.SphereGeometry(0.3, 24, 16), fm); fb.scale.set(1, 1.35, 1); fb.position.y = 0.42; fear.add(fb);
  for (const x of [-0.1, 0.1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffffff })); e.position.set(x, 0.6, 0.26); fear.add(e); }
  fear.position.set(1.2, 0, 1.9); fear.rotation.y = -2.6; fear.visible = false; scene.add(fear);
  const fearEyes = V(1.2, 0.6, 1.9);
  // fat kicking leg (from +Z)
  const kicker = new THREE.Group();
  const leg = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.5, 8, 20), vm); leg.position.y = -0.35; kicker.add(leg);
  const foot = new THREE.Mesh(new THREE.SphereGeometry(0.22, 24, 16), vm); foot.scale.set(1, 0.65, 1.3); foot.position.set(0, -0.72, 0.1); kicker.add(foot);
  kicker.visible = false; scene.add(kicker);
  // janitor's corner: buckets + mop
  const buckets = new THREE.Group();
  const bm = new THREE.MeshStandardMaterial({ color: 0x9aa3b0, metalness: 0.6, roughness: 0.4, side: THREE.DoubleSide });
  const mkBucket = () => { const b = new THREE.Group(); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.12, 0.26, 24, 1, true), bm); c.position.y = 0.13; b.add(c);
    const bt = new THREE.Mesh(new THREE.CircleGeometry(0.12, 24), bm); bt.rotation.x = -Math.PI / 2; bt.position.y = 0.004; b.add(bt);
    const rimT = new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.008, 6, 28), bm); rimT.rotation.x = Math.PI / 2; rimT.position.y = 0.26; b.add(rimT); return b; };
  for (const [x, z, rx, rz] of [[-0.6, -0.55, 1.5, 0.3], [0.65, -0.65, 0, 0], [-0.25, 0.5, 1.57, -0.9]]) { const b = mkBucket(); b.position.set(x, rx ? 0.15 : 0, z); b.rotation.set(rx, 0, rz); buckets.add(b); }
  const mop = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 1.3, 8), new THREE.MeshStandardMaterial({ color: 0xb08850 })); mop.position.set(0.9, 0.05, 0.1); mop.rotation.set(0, 0.4, 1.5); buckets.add(mop);
  buckets.visible = false; scene.add(buckets);
  const headBucket = mkBucket(); headBucket.visible = false; scene.add(headBucket);
  // HUD label (camera child)
  scene.add(app.camera);
  const lc = document.createElement('canvas'); lc.width = 1024; lc.height = 64;
  const ltex = new THREE.CanvasTexture(lc); ltex.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1, 1 / 16), new THREE.MeshBasicMaterial({ map: ltex, transparent: true, depthTest: false, toneMapped: false }));
  label.renderOrder = 999; app.camera.add(label);
  const st = { scene, mag, big, bigEdge, fear, fearEyes, kicker, buckets, headBucket, label, lc, ltex, lastLabel: '',
    look: { bloom: 0.35, bloomThreshold: 0.85, vignette: 0.22, warm: -0.05 } };
  st.kickFoot = () => V(0, 1.4, 0.45);
  return st;
}

export async function update(t, app, s) {
  s.t = t;
  const tt = ((t % DURATION) + DURATION) % DURATION;
  const sg = seg.find((x) => tt >= x.t0 && tt < x.t1) || seg[0];
  s.big.visible = false; s.fear.visible = false; s.kicker.visible = false; s.buckets.visible = false; s.headBucket.visible = false;
  s.kickAmt = 0; s.bucketOn = false; s.bucketDrop = 0;
  const r = sg.fn(tt - sg.t0, s) || {};
  if (r.close) {
    s.mag.update(t, r.pose || {});
    const h = s.mag.anchor('head'), c = r.close;
    r.shot = framed([h.x, h.y - 0.02, h.z], { dist: c.dist, yaw: c.yaw, pitch: 2, fov: 30, screenY: c.screenY, drift: 0 });
  }
  applyShot(app.camera, r.shot, t);
  app.camera.updateMatrixWorld(true);
  s.mag.update(t, r.pose || {});
  // kicker leg: swings from behind/up into the chest
  if (s.kicker.visible) {
    const k = s.kickAmt;
    s.kicker.position.set(0.0, 2.0, 1.15);
    s.kicker.rotation.set(-0.2 - 1.15 * k, 0, 0);
  }
  // bucket dropping onto the head (oriented along the head's up axis)
  if (s.bucketOn) {
    const top = s.mag.anchor('headTop'), up = s.mag.anchor('headUp');
    const b = s.headBucket; b.visible = true;
    const q = new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), up.clone().negate());
    b.quaternion.copy(q);
    b.position.copy(top).addScaledVector(up, 0.2 + 1.2 * s.bucketDrop * s.bucketDrop).add(V(0, 1.2 * s.bucketDrop, 0));
  }
  // label
  const txt = `${sg.name}   [${sg.t0.toFixed(1)}–${sg.t1.toFixed(1)}s]`;
  if (txt !== s.lastLabel) {
    const g = s.lc.getContext('2d'); g.clearRect(0, 0, 1024, 64);
    g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(0, 0, 1024, 64);
    g.fillStyle = '#fff'; g.font = 'bold 34px sans-serif'; g.textBaseline = 'middle'; g.fillText(txt, 18, 33);
    s.ltex.needsUpdate = true; s.lastLabel = txt;
  }
  const d = 1, h = 2 * d * Math.tan((app.camera.fov * Math.PI / 180) / 2), w = h * app.camera.aspect;
  s.label.position.set(0, h / 2 - h * 0.1, -d); s.label.scale.set(w, w, 1);
}
