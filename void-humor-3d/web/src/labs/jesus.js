// Lab: JESUS — turntable (0–4 s), expression sheet (1 s each), then key poses / actions with the REAL partners
// (the Void for arm-around / whisper / listening / hand-on-shoulder / walk-off, the User seated for the kneel).
//   node tools/render.js sheet --lab jesus --from 0 --to 3.5 --n 8 --cols 8 --out out/sheets/jesus_turn.jpg
//   node tools/render.js sheet --lab jesus --from 4.5 --to 28.5 --n 25 --cols 5 --out out/sheets/jesus_expr.jpg
//   node tools/render.js sheet --lab jesus --from 29.5 --to 86.5 --n 30 --cols 6 --out out/sheets/jesus_act.jpg
// Segment list: exported SEGMENTS ({name, t0, t1}); the name is printed in a HUD label on every frame.
// Every segment is a pure function of its local time; face / preset changes crossfade with weights (no pops).
import * as THREE from 'three';
import { applyShot, framed } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { glowSprite } from '../core/materials.js';
import { JX } from '../chars/jesus.js';
import { VX, whisperPose } from '../chars/void.js';
import { UX } from '../chars/user.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const seg = [];
let T0 = 0;
// S(name, dur, shot(lt) -> shot, run(lt, s) -> void [updates the characters it uses])
function S(name, dur, shot, run) { seg.push({ name, t0: T0, t1: T0 + dur, shot, run }); T0 += dur; }

// synthetic lip-sync for talking demos
const talkSample = (t, k = 1) => {
  const o = Math.max(0, Math.sin(t * 11.3) * 0.55 + Math.sin(t * 4.1 + 1) * 0.3 + 0.1) * (0.55 + 0.45 * noise1(t * 2.5, 7));
  return { open: clamp(o * k, 0, 0.75), wide: 0.3 + 0.3 * noise1(t * 3, 9), round: clamp(0.4 * noise1(t * 2.2, 11)), close: o < 0.08 ? 0.6 : 0 };
};
const ramp = (lt, a, b) => smooth((lt - a) / (b - a));
const pulse = (lt, a, b, c, d) => ramp(lt, a, b) * (1 - ramp(lt, c, d));
const mix2 = (a, b, w) => (w <= 0.001 ? a : w >= 0.999 ? b : [[a, 1 - w], [b, w]]);   // weighted face / preset crossfade

// ---------------------------------------------------------------------------------- turntable + expression sheet
const EX = [
  ['kind (default)', { face: 'kind' }],
  ['warm smile', { face: 'warm' }],
  ['beaming', { face: 'beam' }],
  ['laugh', { face: 'laugh', body: { giggle: 0.6 } }],
  ['teehee', { face: 'teehee', body: { giggle: 1, shrug: 0.45 }, armR: { preset: 'teehee' }, head: { roll: 0.12 } }],
  ['listening (nods)', { face: 'listening', nod: 1, head: { roll: 0.1 } }],
  ['whisper', { face: 'whisper', armR: { preset: 'whisper' }, head: { yaw: 0.45, roll: -0.08 }, body: { lean: 0.08, tilt: 0.06 }, gaze: V(0.6, 1.55, 0.6) }],
  ['amused', { face: 'amused', head: { roll: -0.06 } }],
  ['awkward (darting)', { face: 'awkward', dart: 1, body: { shrug: 0.75, hunch: 0.25 }, gaze: null }],
  ['compassion', { face: 'compassion', head: { roll: 0.1 } }],
  ['tender', { face: 'tender', head: { roll: 0.14 } }],
  ['hopeful', { face: 'hopeful', armL: { preset: 'clasp_chest' }, armR: { preset: 'clasp_chest' }, head: { roll: -0.1 } }],
  ['eager', { face: 'eager', body: { lean: 0.06 } }],
  ['surprised', { face: 'surprised', body: { recoil: 0.3 } }],
  ['ooh', { face: 'ooh', head: { pitch: -0.15 }, gaze: V(-0.2, 2.4, 1.2) }],
  ['curious', { face: 'curious', head: { roll: 0.14 } }],
  ['reading (squint)', { face: 'reading', head: { pitch: 0.12 }, body: { lean: 0.08 }, gaze: V(0.0, 1.25, 0.5) }],
  ['shrug "eh, oh well"', { face: 'shrug', body: { shrug: 0.85 }, armL: { preset: 'shrug' }, armR: { preset: 'shrug' }, head: { roll: 0.12 } }],
  ['rueful', { face: 'rueful', head: { roll: 0.06 } }],
  ['sad smile', { face: 'sadSmile', head: { roll: -0.08 } }],
  ['wince', { face: 'wince', body: { shrug: 0.3 } }],
  ['content (eyes half)', { face: 'content', head: { pitch: -0.1 } }],
  ['holding in a laugh', { face: 'pressed', body: { giggle: 0.35 } }],
  ['heart / sincere', { face: 'tender', armR: { preset: 'heart' }, head: { roll: 0.1 } }],
  ['talking (lip-sync)', { face: 'kind', talk: 1, armR: { preset: 'explain' } }],
];

S('turntable', 4, () => framed([0, 0.92, 0], { dist: 4.3, yaw: 0, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }),
  (lt, s) => s.jesus.update(s.t, { yaw: (lt / 4) * Math.PI * 2, face: 'kind', gaze: null, speech: false }));
for (const [name, e] of EX) {
  S('expr: ' + name, 1, () => framed([0, 1.47, 0], { dist: 1.3, yaw: 8, pitch: 2, fov: 30, screenY: 0.56, drift: 0 }), (lt, s) => {
    const head = { ...(e.head || {}) };
    if (e.nod) head.pitch = (head.pitch || 0) + 0.12 * Math.max(0, Math.sin(lt * Math.PI * 2 * 1.6));
    s.jesus.update(s.t, { face: e.face, dart: e.dart, body: e.body, armL: e.armL, armR: e.armR, head,
      gaze: e.gaze !== undefined ? e.gaze : 'camera', speech: e.talk ? talkSample(s.t) : false });
  });
}

// ---------------------------------------------------------------------------------- solo actions
S('idle', 2.5, () => framed([0, 0.95, 0], { dist: 4.0, yaw: 20, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }),
  (lt, s) => s.jesus.update(s.t, { face: 'kind', gaze: 'camera', armL: { preset: 'clasp' }, armR: { preset: 'clasp' }, speech: false }));
const walkZ = (s, style, lt, z0) => z0 + s.jesus.walkSpeed(style) * s.jesus.walkRate(style) * lt;
S('calm walk (3/4)', 3, (lt, s) => framed([0, 0.95, walkZ(s, 'walk', lt, -1.2)], { dist: 4.2, yaw: 35, pitch: 3, fov: 32, screenY: 0.44, drift: 0 }), (lt, s) => {
  const J = s.jesus, z = walkZ(s, 'walk', lt, -1.2);
  J.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * J.walkRate('walk'), style: 'walk' }, face: 'content', gaze: V(0, 1.5, z + 3), speech: false });
});
S('calm walk (side), hands behind', 3, (lt, s) => framed([0, 0.95, walkZ(s, 'stroll', lt, -1.2)], { dist: 4.2, yaw: 88, pitch: 2, fov: 32, screenY: 0.44, drift: 0 }), (lt, s) => {
  const J = s.jesus, z = walkZ(s, 'stroll', lt, -1.2);
  J.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * J.walkRate('stroll'), style: 'stroll' }, face: 'content', head: { pitch: -0.12 }, armL: { preset: 'behind' }, armR: { preset: 'behind' }, speech: false });
});
S('run (side)', 2, (lt, s) => framed([0, 0.95, walkZ(s, 'run', lt, -2)], { dist: 4.4, yaw: 80, pitch: 2, fov: 32, screenY: 0.44, drift: 0 }), (lt, s) => {
  const J = s.jesus, z = walkZ(s, 'run', lt, -2);
  J.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * J.walkRate('run'), style: 'run' }, face: ['eager', 0.5], speech: false });
});

// ---------------------------------------------------------------------------------- kneel to the seated User
S('kneel to a seated person, open palms', 6, () => framed([0.05, 0.7, 0.8], { dist: 4.6, yaw: 36, pitch: 6, fov: 32, screenY: 0.5, drift: 0 }), (lt, s) => {
  const U = s.user;
  U.update(s.t, { pos: [0.02, 0, 1.62], yaw: Math.PI, body: { sit: 1, sitPath: 'plain' }, face: UX('terror', { mTremble: 0.3 }), gaze: s.jesus, speech: false,
    armR: { preset: 'defend' }, armL: { preset: 'prop' } });
  const kn = ramp(lt, 0.3, 1.6) - ramp(lt, 5.0, 5.9);
  const open = ramp(lt, 1.2, 1.9) * (1 - ramp(lt, 4.9, 5.5));
  const talk = pulse(lt, 2.0, 2.4, 4.4, 4.8), ex = pulse(lt, 2.2, 2.7, 4.2, 4.7);
  s.jesus.update(s.t, {
    yaw: 0, body: { kneel: kn }, face: mix2('kind', 'tender', talk), gaze: U, head: { follow: 0.6, roll: 0.08 * talk },
    speech: talk > 0.05 ? talkSample(s.t, 0.8 * talk) : false,
    armL: { preset: [['knee_rest', 0.6], ['open', 0.4]], reach: open, hand: { splay: 0.08, cup: 0.45 } },
    armR: { preset: mix2('open', 'explain', ex), reach: open, hand: { splay: 0.08, cup: 0.45 } },
  });
});

// ---------------------------------------------------------------------------------- with the real Void
// Void at the origin facing +Z; Jesus at its RIGHT flank (−X), his LEFT arm goes round its back.
const JP = [-1.17, 0, 0.16], JYAW = 0.32;
S('arm around the Void + whisper (front 3/4)', 6,
  (lt) => (lt < 2.6 ? framed([-0.7, 1.3, 0.0], { dist: 5.8, yaw: 6, pitch: 6, fov: 32, screenY: 0.5, drift: 0 })
    : framed([-0.85, 1.66, 0.2], { dist: 2.9, yaw: 28, pitch: 2, fov: 30, screenY: 0.58, drift: 0 })),
  (lt, s) => {
    const vd = s.vd, J = s.jesus;
    const around = ramp(lt, 0.3, 1.3), lean = ramp(lt, 1.6, 2.4) * (1 - ramp(lt, 5.4, 5.95)), wh = ramp(lt, 2.2, 2.8) * (1 - ramp(lt, 5.2, 5.8));
    const W = whisperPose(-1, 0.75, lean);
    vd.update(s.t, { ...W, armR: { preset: 'belly' }, armL: { preset: 'belly' }, face: VX(mix2('calm', 'listen', lean)), gaze: J, speech: false });
    const ear = vd.anchor('earR'), veyes = vd.anchor('eyes');
    J.update(s.t, {
      pos: JP, yaw: JYAW, face: mix2('warm', 'whisper', wh), gaze: wh > 0.5 ? ear : veyes,
      head: { look: wh > 0.01 ? ear.clone().lerp(veyes, 1 - wh) : veyes, follow: 0.55 + 0.25 * wh, roll: -0.1 * wh },
      body: { tiptoe: 0.8 * wh, lean: 0.04 * wh },
      speech: wh > 0.6 ? { open: 0.12 + 0.1 * Math.max(0, Math.sin(s.t * 13)), wide: 0.2, round: 0.5, close: 0 } : false,
      armL: { preset: 'around', surface: vd, reach: around },
      armR: { preset: mix2('rest', 'whisper', wh) },
    });
  });
S('arm around the Void (back 3/4)', 3, () => framed([-0.95, 1.2, -0.15], { dist: 5.0, yaw: -146, pitch: 9, fov: 32, screenY: 0.5, drift: 0 }), (lt, s) => {
  const vd = s.vd, J = s.jesus, pat = 0.02 * Math.max(0, Math.sin(lt * Math.PI * 2 * 0.8)) * ramp(lt, 1, 1.5);
  vd.update(s.t, { armR: { preset: 'belly' }, armL: { preset: 'belly' }, face: VX('calm'), gaze: J, head: { yaw: -0.4 }, speech: false });
  J.update(s.t, { pos: JP, yaw: JYAW, face: 'warm', gaze: vd.anchor('eyes'), head: { look: vd.anchor('eyes'), follow: 0.55 }, speech: false,
    armL: { preset: 'around', surface: vd, offset: [0, pat, 0] }, armR: { preset: 'rest' } });
});
S('listening nods (the Void whispers to him)', 3.5, () => framed([-1.0, 1.6, 0.2], { dist: 2.8, yaw: -30, pitch: 3, fov: 30, screenY: 0.56, drift: 0 }), (lt, s) => {
  const vd = s.vd, J = s.jesus;
  J.update(s.t, { pos: JP, yaw: JYAW, face: 'listening', armL: { preset: 'around', surface: vd }, speech: false });   // place first (ear anchor)
  const W = { ...whisperPose(-1, 1.05, 1), armL: { preset: 'belly' }, face: VX('whisper', { gazeYaw: 0.5 }), speech: { open: 0.1 + 0.08 * Math.max(0, Math.sin(s.t * 12)), wide: 0.2, round: 0.5, close: 0 } };
  W.pos = vd.solvePos(s.t, W, 'whisper', J.anchor('earL').add(V(0.02, 0.05, 0.04)));
  vd.update(s.t, W);
  const nod = 0.13 * Math.max(0, Math.sin(lt * Math.PI * 2 * 1.3)) * ramp(lt, 0.4, 0.8);
  J.update(s.t, { pos: JP, yaw: JYAW, face: 'listening', gaze: V(0.3, 1.4, 1.6), head: { roll: 0.14, pitch: nod, yaw: -0.15 }, armL: { preset: 'around', surface: vd }, speech: false });
});
S('hand on the Void\'s shoulder (front 3/4)', 4, () => framed([1.0, 1.35, 0.15], { dist: 5.0, yaw: -8, pitch: 4, fov: 32, screenY: 0.42, drift: 0 }), (lt, s) => {
  const vd = s.vd, J = s.jesus;
  const look = ramp(lt, 1.4, 2.3);
  vd.update(s.t, { yaw: Math.PI, armL: { preset: 'crossed' }, armR: { preset: 'crossed' }, face: VX(mix2('annoyed', 'gentle', look)), head: { yaw: -1.85 * look, pitch: 0.12 * look }, body: { twist: -0.33 * look }, gaze: look > 0.4 ? J : null, speech: false });
  const sh = vd.anchor('shoulderR');
  const r = ramp(lt, 0.25, 1.1);
  const awk = 1 - ramp(lt, 0.0, 0.9);
  const nod = 0.12 * pulse(lt, 2.6, 2.85, 2.95, 3.3);
  J.update(s.t, { pos: [1.3, 0, 0.15], yaw: -0.7, face: JX([['awkward', awk * (1 - ramp(lt, 2.0, 2.6))], ['kind', (1 - awk) * (1 - ramp(lt, 2.0, 2.6))], ['tender', ramp(lt, 2.0, 2.6)]]), gaze: vd, head: { follow: 0.45, pitch: nod },
    armR: { preset: 'shoulder', target: sh, surface: vd, reach: r }, body: { tiptoe: 0.25 * r, lean: 0.05 * r }, speech: false });
});

// ---------------------------------------------------------------------------------- solo beats
S('shrug, palms up', 2.5, () => framed([0, 1.2, 0], { dist: 2.8, yaw: 10, pitch: 2, fov: 32, screenY: 0.55, drift: 0 }), (lt, s) => {
  const a = ramp(lt, 0.2, 0.7) * (1 - ramp(lt, 2.0, 2.4));
  s.jesus.update(s.t, { face: mix2('kind', 'shrug', a), gaze: 'camera', body: { shrug: 0.85 * a }, armL: { preset: 'shrug', reach: a }, armR: { preset: 'shrug', reach: a }, head: { roll: 0.12 * a }, speech: false });
});
S('look at a floating notification', 3, () => framed([-0.14, 1.66, 0.22], { dist: 3.0, yaw: 22, pitch: 0, fov: 32, screenY: 0.55, drift: 0 }), (lt, s) => {
  s.note.visible = true;
  const np = s.note.position;
  const read = ramp(lt, 0.4, 0.9), surp = ramp(lt, 1.6, 1.9);
  s.jesus.update(s.t, { face: JX([['reading', read * (1 - surp)], ['oh', surp]]), gaze: np, head: { look: np, follow: 0.7 * read }, body: { lean: 0.05 * read, recoil: 0.12 * surp }, speech: false });
});
S('teehee', 2.5, () => framed([0, 1.42, 0], { dist: 1.8, yaw: 12, pitch: 2, fov: 30, screenY: 0.56, drift: 0 }), (lt, s) => {
  const a = ramp(lt, 0.15, 0.45) * (1 - ramp(lt, 2.1, 2.45));
  s.jesus.update(s.t, { face: mix2('warm', 'teehee', a), body: { giggle: a, shrug: 0.4 * a }, armR: { preset: 'teehee', reach: a }, gaze: 'camera', head: { roll: 0.12 * a }, speech: false });
});
S('awkward grimace, eyes darting', 3, () => framed([0, 1.42, 0], { dist: 1.8, yaw: 5, pitch: 2, fov: 30, screenY: 0.56, drift: 0 }), (lt, s) => {
  const a = ramp(lt, 0.2, 0.6);
  s.jesus.update(s.t, { face: ['awkward', a], dart: a, body: { shrug: 0.7 * a, hunch: 0.25 * a }, armL: { preset: 'clasp', reach: a }, armR: { preset: 'clasp', reach: a }, gaze: null, speech: false });
});
const TALK = [['explain', 'rest', 'kind'], ['open', 'open', 'hopeful'], ['heart', 'rest', 'tender'], ['offer', 'explain', 'warm']];
S('talking gestures', 5, () => framed([0, 1.2, 0], { dist: 2.8, yaw: 15, pitch: 2, fov: 32, screenY: 0.55, drift: 0 }), (lt, s) => {
  const ph = lt / 1.25, i = Math.floor(ph) % 4, n = (i + 1) % 4, f = smooth((ph - Math.floor(ph) - 0.7) / 0.3);
  s.jesus.update(s.t, { face: mix2(TALK[i][2], TALK[n][2], f), gaze: 'camera', speech: talkSample(s.t),
    armR: { preset: mix2(TALK[i][0], TALK[n][0], f) }, armL: { preset: mix2(TALK[i][1], TALK[n][1], f) } });
});
S('walk off with an arm around the Void, talking', 6,
  (lt, s) => { const p = s.walkOff(lt).mid; const fy = Math.atan2(-0.45, -1) * 180 / Math.PI; return lt < 3 ? framed([p.x, 1.3, p.z], { dist: 6.4, yaw: fy - 24, pitch: 5, fov: 32, screenY: 0.5, drift: 0 }) : framed([p.x, 1.25, p.z], { dist: 6.0, yaw: fy + 180 + 34, pitch: 10, fov: 32, screenY: 0.5, drift: 0 }); },
  (lt, s) => {
    const W = s.walkOff(lt), J = s.jesus, vd = s.vd;
    vd.update(s.t, { pos: W.vpos.toArray(), yaw: W.yaw, armL: { preset: 'belly' }, armR: { preset: 'belly' }, walk: { amount: 1, phase: lt * W.vRate, style: 'waddle' }, face: VX('giggle', { mOpen: 0.15 + 0.12 * Math.max(0, Math.sin(s.t * 9)) }), gaze: J, speech: false });
    J.update(s.t, { pos: W.jpos.toArray(), yaw: W.yaw, walk: { amount: 1, phase: lt * W.jRate, style: 'walk' }, face: 'warm', gaze: vd.anchor('eyes'), head: { look: vd.anchor('eyes'), follow: 0.5 },
      speech: talkSample(s.t, 0.8), armL: { preset: 'around', surface: vd }, armR: { preset: 'explain' } });
  });
S('crouch + sit (generic)', 3, () => framed([0, 0.7, 0], { dist: 3.6, yaw: 50, pitch: 4, fov: 32, screenY: 0.44, drift: 0 }), (lt, s) => {
  const c = ramp(lt, 0.1, 0.8) * (1 - ramp(lt, 1.3, 1.6));
  const si = ramp(lt, 1.6, 2.4);
  s.jesus.update(s.t, { face: 'kind', gaze: 'camera', body: { crouch: c, sit: si }, armL: { preset: mix2('rest', 'knee_rest', si) }, armR: { preset: 'rest' }, speech: false });
});
export const DURATION = T0;
export const SEGMENTS = seg.map((x) => ({ name: x.name, t0: x.t0, t1: x.t1 }));

// ---------------------------------------------------------------------------------- set
export async function setup(app) {
  const scene = new THREE.Scene();
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 a = vec3(1.0,0.78,0.62), b = vec3(0.55,0.52,0.78); gl_FragColor = vec4(mix(a, b, smoothstep(-0.05, 0.6, h)), 1.0);\n#include <colorspace_fragment>\n}',
  }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshLambertMaterial({ color: 0xd9b6a0 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
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
  const vd = await app.char('VOID');
  const user = await app.char('USER');
  scene.add(jesus.root);
  // floating notification card (generic social app: plain speech-bubble icon)
  const note = new THREE.Group();
  const card = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.12), new THREE.MeshBasicMaterial({ color: 0xeef6ff, toneMapped: false }));
  note.add(card);
  const ic = new THREE.Mesh(new THREE.CircleGeometry(0.035, 20), new THREE.MeshBasicMaterial({ color: 0x5aa0ff, toneMapped: false })); ic.position.set(-0.12, 0, 0.001); note.add(ic);
  const gl = glowSprite(0x9fd0ff, 0.42, 0.28); gl.position.z = -0.02; note.add(gl);
  const frame = new THREE.Mesh(new THREE.PlaneGeometry(0.37, 0.15), new THREE.MeshBasicMaterial({ color: 0x5a78a8 })); frame.position.z = -0.002; note.add(frame);
  note.position.set(-0.3, 1.95, 0.5); note.rotation.y = 0.45; note.visible = false; scene.add(note);
  // HUD label (camera child)
  scene.add(app.camera);
  const lc = document.createElement('canvas'); lc.width = 1024; lc.height = 64;
  const ltex = new THREE.CanvasTexture(lc); ltex.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1, 1 / 16), new THREE.MeshBasicMaterial({ map: ltex, transparent: true, depthTest: false, toneMapped: false }));
  label.renderOrder = 999; app.camera.add(label);
  // walk-off path: both walk along travel direction dir; the Void on his left
  const dir = V(-0.45, 0, -1).normalize(), yaw = Math.atan2(dir.x, dir.z);
  const jRate = jesus.walkRate('walk') * 0.85, speed = jesus.walkSpeed('walk') * jRate, vRate = speed / (2 * 0.38);
  const side = V(1, 0, 0).applyAxisAngle(V(0, 1, 0), yaw);
  const walkOff = (lt) => {
    const jpos = V(0.6, 0, 1.4).addScaledVector(dir, speed * lt);
    const vpos = jpos.clone().addScaledVector(side, 1.24).addScaledVector(dir, -0.1);
    return { jpos, vpos, mid: jpos.clone().lerp(vpos, 0.4), yaw, jRate, vRate };
  };
  return { scene, jesus, vd, user, note, label, lc, ltex, lastLabel: '', walkOff, look: { bloom: 0.32, bloomThreshold: 0.85, vignette: 0.22, warm: 0.1 } };
}

export async function update(t, app, s) {
  s.t = t;
  const tt = ((t % DURATION) + DURATION) % DURATION;
  const sg = seg.find((x) => tt >= x.t0 && tt < x.t1) || seg[0];
  const lt = tt - sg.t0;
  s.note.visible = false;
  // camera first (catchlights / gaze 'camera' read it), then the partners, then Jesus (his contacts read their surfaces)
  applyShot(app.camera, sg.shot(lt, s), t);
  app.camera.updateMatrixWorld(true);
  const usesVoid = /Void/.test(sg.name), usesUser = /seated/.test(sg.name);
  if (usesVoid) { if (!s.vd.root.parent) s.scene.add(s.vd.root); } else if (s.vd.root.parent) s.scene.remove(s.vd.root);
  if (usesUser) { if (!s.user.root.parent) s.scene.add(s.user.root); } else if (s.user.root.parent) s.scene.remove(s.user.root);
  sg.run(lt, s);
  if (s.note.visible) s.note.position.y = 1.95 + 0.03 * Math.sin(t * 2);
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
