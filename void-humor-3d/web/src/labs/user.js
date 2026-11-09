// Lab: USER ("the Twitter user") — turntable (0–4 s), expression sheet (1 s each), then key poses / actions with
// placeholder partners (a big plump "Void" stand-in, a Jesus-height stand-in).
//   node tools/render.js sheet --lab user --from 0 --to 3.5 --n 8 --cols 4 --out out/sheets/user_turn.jpg
//   node tools/render.js stills --lab user --t 4.5,5.5 ...      (segment names are printed in the HUD label)
import * as THREE from 'three';
import { applyShot, orbitPos } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { clamp, lerp, smooth, noise1, hash1, schedule } from '../core/util.js';
import { headShake } from '../chars/user.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
// camera helper: look point lands at screen height screenY (0 = top, 1 = bottom), camera translated, not tilted
function framed(look, { dist = 2, yaw = 0, pitch = 0, fov = 35, screenY = 0.4, drift = 0, roll = 0 } = {}) {
  const pos = orbitPos(look, dist, yaw, pitch);
  const off = (screenY - 0.5) * 2 * dist * Math.tan((fov * Math.PI / 180) / 2);
  return { pos: [pos[0], pos[1] + off, pos[2]], look: [look[0], look[1] + off, look[2]], fov, drift, roll };
}
const seg = [];
let T0 = 0;
function S(name, dur, fn) { seg.push({ name, t0: T0, t1: T0 + dur, fn }); T0 += dur; }

// synthetic lip-sync for talking demos
const talkSample = (t, k = 1) => {
  const o = Math.max(0, Math.sin(t * 11.3) * 0.55 + Math.sin(t * 4.1 + 1) * 0.3 + 0.1) * (0.55 + 0.45 * noise1(t * 2.5, 7));
  return { open: clamp(o * k, 0, 0.75), wide: 0.3 + 0.3 * noise1(t * 3, 9), round: clamp(0.4 * noise1(t * 2.2, 11)), close: o < 0.08 ? 0.6 : 0 };
};
const ramp = (lt, a, b) => smooth((lt - a) / (b - a));
// thumb-tap pulses (0..1) from a deterministic schedule
const TAPS = schedule(77, -2, 400, 0.22, 0.55);
const tapAt = (t) => { let v = 0; for (const e of TAPS) { if (e > t) break; const d = t - e; if (d < 0.14) v = Math.max(v, Math.sin(Math.PI * d / 0.14)); } return v; };

// ---------------------------------------------------------------------------------- expression sheet
const EX = [
  ['idle (default, guarded)', { face: 'idle' }],
  ['scroll (phone up, glow)', { face: 'scroll', phone: true }],
  ['sob + tears', { face: 'sob', extra: { tears: 1 }, body: { shrug: 0.3 } }],
  ['terror + tears', { face: 'terror', extra: { tears: 0.7 }, body: { shrug: 0.5, tremble: 0.6 } }],
  ['silent scream', { face: 'scream', body: { shrug: 0.4 } }],
  ['gasp', { face: 'gasp', body: { recoil: 0.3 } }],
  ['what the actual—', { face: 'wtf', body: { jut: 1 } }],
  ['scrunch (the bleep)', { face: 'scrunch', body: { shrug: 0.4 } }],
  ['deadpan', { face: 'deadpan' }],
  ['hell no', { face: 'hellno' }],
  ['pout (chin up)', { face: 'pout', head: { pitch: -0.12 } }],
  ['smirk', { face: 'smirk', head: { roll: 0.06 } }],
  ['suspicious squint', { face: 'suspicious' }],
  ['glare', { face: 'glare', head: { pitch: 0.08 } }],
  ['gulp', { face: 'gulp', body: { shrug: 0.5 } }],
  ['guilt flicker', { face: 'guilt', head: { pitch: 0.06 } }],
  ['softening (glisten)', { face: 'soften', extra: { glisten: 1 } }],
  ['lip tremble', { face: 'tremble' }],
  ['dawning "…you?"', { face: 'dawning' }],
  ['not-quite smile', { face: 'notquite', head: { roll: 0.08 } }],
  ['nervous grimace', { face: 'nervous', body: { shrug: 0.4 } }],
  ['storm (angry pout)', { face: 'storm', head: { pitch: 0.06 } }],
  ['disbelief (half-mast)', { face: 'disbelief' }],
  ['talking (lip-sync)', { face: 'idle', talk: 1 }],
];

S('turntable', 4, (lt, s) => {
  s.user.update(s.t, { yaw: (lt / 4) * Math.PI * 2, face: 'idle', gaze: null, extra: { phone: 0.6 } });
  return { shot: framed([0, 0.86, 0], { dist: 4.1, yaw: 0, pitch: 3, fov: 32, screenY: 0.45, drift: 0 }) };
});
for (const [name, e] of EX) {
  S('expr: ' + name, 1, (lt, s) => {
    const t = s.t, U = s.user;
    const pose = { face: { expr: e.face, autoBlink: 0 }, body: e.body, head: { ...(e.head || {}) }, gaze: 'camera', extra: { phone: 0.5, ...(e.extra || {}) } };
    pose.speech = e.talk ? talkSample(t) : false;
    if (e.phone) { pose.extra = { phone: 1, phoneUp: 1, tap: tapAt(t) }; pose.gaze = U.anchor('phoneScreen'); pose.head.pitch = 0.22; }
    U.update(t, pose);
    if (e.phone) { pose.gaze = U.anchor('phoneScreen'); U.update(t, pose); }
    return { shot: framed([0, 1.42, 0], { dist: 1.5, yaw: 10, pitch: 2, fov: 30, screenY: 0.42, drift: 0 }) };
  });
}

// ---------------------------------------------------------------------------------- actions
S('idle: phone up, scroll + thumb taps', 3, (lt, s) => {
  const U = s.user, up = ramp(lt, 0.2, 0.8);
  const pose = { face: up > 0.5 ? 'scroll' : 'idle', extra: { phone: 1, phoneUp: up, tap: tapAt(s.t), scroll: lt * 0.35 }, head: { pitch: 0.12 + 0.12 * up } };
  pose.gaze = U.anchor('phoneScreen'); U.update(s.t, pose); pose.gaze = U.anchor('phoneScreen'); U.update(s.t, pose);
  return { shot: framed([0, 1.25, 0], { dist: 2.0, yaw: 20, pitch: 2, fov: 30, screenY: 0.42, drift: 0 }) };
});
S('walk (3/4), phone low', 3, (lt, s) => {
  const U = s.user, rate = U.walkRate('walk'), sp = U.walkSpeed('walk') * rate;
  const z = -1.2 + sp * lt;
  U.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'walk' }, face: 'idle', gaze: V(0, 1.4, z + 3), extra: { phone: 0.6 } });
  return { shot: framed([0, 0.86, z], { dist: 4.0, yaw: 35, pitch: 3, fov: 32, screenY: 0.45, drift: 0 }) };
});
S('panicked run (front), sobbing, look back', 3, (lt, s) => {
  const U = s.user, rate = U.walkRate('run'), sp = U.walkSpeed('run') * rate;
  const z = -3.2 + sp * lt;
  const lb = ramp(lt, 1.0, 1.25) * (1 - ramp(lt, 1.7, 1.95));
  U.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'run' }, face: lb > 0.4 ? 'scream' : 'sob', body: { lookBack: lb * 0.85 },
    gaze: lb > 0.3 ? V(1.5, 1.6, z - 4) : 'camera', extra: { tears: 1, phone: 0.8 } });
  return { shot: framed([0, 1.0, z], { dist: 3.4 + 0.0 * lt, yaw: 8, pitch: 2, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('panicked run (side)', 2, (lt, s) => {
  const U = s.user, rate = U.walkRate('run'), sp = U.walkSpeed('run') * rate;
  const z = -2 + sp * lt;
  U.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'run' }, face: 'sob', extra: { tears: 1 } });
  return { shot: framed([0, 0.9, z], { dist: 4.2, yaw: 82, pitch: 2, fov: 32, screenY: 0.45, drift: 0 }) };
});
S('stumble + fall onto backside (sit 0→1), defend', 3.5, (lt, s) => {
  const U = s.user, rate = U.walkRate('run'), sp = U.walkSpeed('run') * rate;
  const run = 1 - ramp(lt, 0.55, 0.75);
  const sit = ramp(lt, 0.55, 1.3);
  const d = Math.min(lt, 0.55) * sp + (lt > 0.55 ? 0.55 * (1 - Math.exp(-(lt - 0.55) * 4)) : 0) - 2.0;
  const yaw = 0.45, dir = V(Math.sin(yaw), 0, Math.cos(yaw)), p = dir.clone().multiplyScalar(d);
  const after = ramp(lt, 1.3, 1.7);
  U.update(s.t, { pos: [p.x, 0, p.z], yaw, walk: { amount: run, phase: lt * rate, style: 'run' }, body: { sit, shrug: 0.5 * after, tremble: 0.5 * after },
    face: lt < 0.55 ? 'sob' : lt < 1.25 ? 'gasp' : 'terror', gaze: p.clone().add(V(-0.6, 1.6, -3)),
    armR: { preset: 'defend', reach: after, tremble: after }, armL: { preset: 'prop', reach: ramp(lt, 1.15, 1.5) }, extra: { tears: 0.6, phone: 0.7 } });
  const fp = dir.clone().multiplyScalar(Math.max(d, -1.2));
  return { shot: framed([fp.x, 0.75, fp.z], { dist: 4.2, yaw: 70, pitch: 5, fov: 32, screenY: 0.47, drift: 0 }) };
});
S('seated terror: tears, trembling splayed hand', 2.5, (lt, s) => {
  const U = s.user;
  U.update(s.t, { yaw: 0.35, body: { sit: 1, shrug: 0.6, tremble: 0.7, pant: 1 }, face: 'terror', gaze: V(1.2, 2.2, 2.5),
    armR: { preset: 'defend', tremble: 1 }, armL: { preset: 'prop' }, extra: { tears: 0.8, phone: 0.8 } });
  return { shot: framed([0.1, 0.62, 0.25], { dist: 2.7, yaw: 35, pitch: 7, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('scoot backward (seated)', 3, (lt, s) => {
  const U = s.user, rate = 1.6;
  const z = 0.4 - U.scootSpeed(1) * rate * lt;
  U.update(s.t, { pos: [0, 0, z], body: { sit: 1, scoot: 1, scootPhase: lt * rate, shrug: 0.5 }, face: 'terror', gaze: V(0.3, 2, 3),
    armR: { preset: 'defend', tremble: 0.6 }, armL: { preset: 'prop' }, extra: { tears: 0.5 } });
  return { shot: framed([0, 0.6, z], { dist: 3.0, yaw: 70, pitch: 6, fov: 32, screenY: 0.45, drift: 0 }) };
});
S('"what the actual—": lean forward, flap', 2.5, (lt, s) => {
  const U = s.user;
  const lean = ramp(lt, 0.2, 0.6);
  const flap = Math.sin(Math.PI * clamp((lt - 0.9) / 0.4)) * (lt > 0.9 && lt < 1.3 ? 1 : 0);
  U.update(s.t, { yaw: 0.25, body: { sit: 1, jut: lean, lean: 0.12 * lean, flinch: lt > 1.6 ? 0.4 * ramp(lt, 1.6, 1.7) : 0 }, face: lt > 1.6 ? 'scrunch' : 'wtf', gaze: 'camera', speech: lt > 0.4 && lt < 1.6 ? talkSample(s.t) : false,
    armR: { preset: 'defend', flap, threat: [-0.7, 1.9, 2.8] }, armL: { preset: [['prop', 1 - lean * 0.6], ['knee', lean * 0.6]] } });
  return { shot: framed([0.05, 0.72, 0.25], { dist: 2.5, yaw: 35, pitch: 5, fov: 32, screenY: 0.4, drift: 0 }) };
});
S('"hell no": head shake (scene drives head.yaw)', 2.5, (lt, s) => {
  const U = s.user;
  const hs = headShake(lt, 0.5, { count: 2.5, dur: 0.85, amp: 0.38 });
  U.update(s.t, { yaw: 0.2, body: { sit: 1 }, face: 'hellno', head: { yaw: hs.yaw }, gaze: 'camera', speech: lt > 0.4 && lt < 1.2 ? talkSample(s.t, 0.7) : false,
    extra: { hairSwing: hs.hairSwing }, armL: { preset: 'prop' }, armR: { preset: 'knee' } });
  return { shot: framed([0.05, 0.85, 0.2], { dist: 1.6, yaw: 15, pitch: 5, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('jab phone at partner, then cross arms + pout', 3.5, (lt, s) => {
  const U = s.user;
  s.big.visible = true;
  const B = s.bigAnchors();
  const jab = ramp(lt, 0.2, 0.5) * (1 - ramp(lt, 1.6, 1.9));
  const cr = ramp(lt, 1.8, 2.2);
  U.update(s.t, { yaw: 0.6, body: { sit: 1, lean: 0.1 * jab, recoil: 0.25 * cr }, face: cr > 0.5 ? 'pout' : 'hellno', gaze: B.eye, head: { follow: 0.5, pitch: -0.12 * cr },
    armL: cr > 0.01 ? { preset: [['crossed', cr], ['look', 0]], reach: 1 } : { preset: 'jab', target: U.anchor('shoulderL').lerp(B.eye, 0.45), reach: jab, tremble: 0.6 },
    armR: cr > 0.01 ? { preset: 'crossed', reach: cr } : { preset: 'prop' }, extra: { phone: 0.9 } });
  return { shot: framed([0.12, 0.62, 0.15], { dist: 3.3, yaw: 64, pitch: 8, fov: 34, screenY: 0.48, drift: 0 }) };
});
S('hug the phone to chest (armL clutch)', 2.5, (lt, s) => {
  const U = s.user, a = ramp(lt, 0.2, 0.6);
  U.update(s.t, { body: { shrug: 0.45 * a, hunch: 0.4 }, face: 'gulp', gaze: V(0.8, 1.5, 2), armL: { preset: 'clutch', reach: a }, armR: { preset: 'hug', reach: a }, extra: { phone: 0.5 } });
  return { shot: framed([0, 1.2, 0], { dist: 1.9, yaw: 15, pitch: 2, fov: 30, screenY: 0.42, drift: 0 }) };
});
S('softening flicker: hand on heart, lip tremble, glisten', 3, (lt, s) => {
  const U = s.user, a = ramp(lt, 0.4, 1.0);
  U.update(s.t, { body: { sit: 1 }, face: lt < 0.5 ? 'guarded' : lt < 1.8 ? 'soften' : 'tremble', gaze: 'camera', head: { roll: 0.06 * a },
    armR: { preset: [['heart', a], ['knee', 1 - a]] }, armL: { preset: 'lap' }, extra: { glisten: a, phone: 0.6, tears: ramp(lt, 2.0, 2.8) * 0.5 } });
  return { shot: framed([0, 0.85, 0.2], { dist: 1.5, yaw: 12, pitch: 4, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('phone face-down in lap (screen off)', 2, (lt, s) => {
  const U = s.user;
  U.update(s.t, { body: { sit: 1, slump: 0.4 }, face: 'tremble', gaze: V(0, 0.2, 0.6), armL: { preset: 'lap', palm: [0, -1, 0] }, armR: { preset: 'knee' }, extra: { phone: 0, screen: 'off' } });
  return { shot: framed([0, 0.7, 0.2], { dist: 2.0, yaw: 25, pitch: 10, fov: 30, screenY: 0.42, drift: 0 }) };
});
S('get up (sit 1→0, rise path)', 2.5, (lt, s) => {
  const U = s.user, sit = 1 - ramp(lt, 0.2, 1.8);
  U.update(s.t, { yaw: 0.9, body: { sit, sitPath: 'rise' }, face: 'storm', gaze: V(2, 1.5, 1.5), armL: { preset: 'hold' }, armR: { preset: [['knee', sit > 0.5 ? 1 : 0], ['rest', sit > 0.5 ? 0 : 1]] } });
  return { shot: framed([0, 0.75, 0], { dist: 3.4, yaw: 0, pitch: 4, fov: 32, screenY: 0.45, drift: 0 }) };
});
S('storm off (stomp, side)', 3, (lt, s) => {
  const U = s.user, rate = U.walkRate('stomp'), sp = U.walkSpeed('stomp') * rate;
  const z = -1.4 + sp * lt;
  U.update(s.t, { pos: [0, 0, z], walk: { amount: 1, phase: lt * rate, style: 'stomp' }, face: 'storm', speech: lt > 1 && lt < 2 ? talkSample(s.t, 0.5) : false, extra: { phone: 0.5 } });
  return { shot: framed([0, 0.9, z], { dist: 4.0, yaw: 75, pitch: 3, fov: 32, screenY: 0.45, drift: 0 }) };
});
S('stomp away + look back over the shoulder', 3, (lt, s) => {
  const U = s.user, rate = U.walkRate('stomp'), sp = U.walkSpeed('stomp') * rate;
  const z = -0.5 - sp * lt;
  const lb = ramp(lt, 1.0, 1.35) * (1 - ramp(lt, 2.0, 2.35));
  U.update(s.t, { pos: [0, 0, z], yaw: Math.PI, walk: { amount: 1, phase: lt * rate, style: 'stomp' }, body: { lookBack: lb }, face: lb > 0.3 ? 'guilt' : 'storm', gaze: lb > 0.3 ? V(-1.2, 1.4, z + 3) : null, extra: { phone: 0.5 } });
  return { shot: framed([0, 0.9, z], { dist: 3.6, yaw: -24, pitch: 4, fov: 32, screenY: 0.45, drift: 0 }) };
});
S('thumb-tap Block -> blocked (insert)', 3, (lt, s) => {
  const U = s.user;
  const scr = lt < 1.6 ? 'block' : 'blocked';
  const tap = Math.max(bumpT(lt, 1.2, 0.16), bumpT(lt, 1.45, 0.16));
  const pose = { face: 'glare', extra: { phoneUp: 1, screen: scr, tap, thumb: ramp(lt, 0.3, 0.9) }, head: { pitch: 0.1 } };
  pose.gaze = U.anchor('phoneScreen'); U.update(s.t, pose);
  const p = U.anchor('phoneScreen'); pose.gaze = p; U.update(s.t, pose);
  const ph = U.anchor('phoneScreen'), hd = U.anchor('eyes');
  const n = V(0, 0, 1).transformDirection(U.phone.matrixWorld), up = V(0, 1, 0).transformDirection(U.phone.matrixWorld);
  const cp = ph.clone().addScaledVector(n, 0.24).addScaledVector(up, -0.03);
  // roll the camera so the phone reads upright
  const m = new THREE.Matrix4().lookAt(cp, ph, V(0, 1, 0)), inv = m.clone().invert();
  const upc = up.clone().transformDirection(inv);
  return { shot: { pos: [cp.x, cp.y, cp.z], look: [ph.x, ph.y + 0.01, ph.z], fov: 30, drift: 0, roll: Math.atan2(upc.x, upc.y) } };
});
function bumpT(t, at, d) { const u = (t - at) / d; return u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0; }
S('show phone over the shoulder (screen back)', 2, (lt, s) => {
  const U = s.user, a = ramp(lt, 0.2, 0.6), rate = U.walkRate('stomp');
  U.update(s.t, { yaw: Math.PI, walk: { amount: 0.6, phase: lt * rate, style: 'stomp' }, pos: [0, 0, -0.6 * lt], face: 'smirk', armL: { preset: 'show', reach: a }, extra: { phone: 1, screen: 'blocked' } });
  return { shot: framed([0, 1.25, -0.6 * lt], { dist: 2.8, yaw: 20, pitch: 4, fov: 32, screenY: 0.42, drift: 0 }) };
});
S('defend toward the partner (arm target), eyes locked', 2.5, (lt, s) => {
  const U = s.user;
  s.big.visible = true;
  const B = s.bigAnchors();
  const a = ramp(lt, 0.2, 0.5);
  U.update(s.t, { yaw: 0.6, body: { sit: 1, shrug: 0.7, recoil: 0.2, tremble: 0.5 }, face: 'terror', gaze: B.eye, head: { follow: 0.6 },
    armR: { preset: 'defend', threat: B.eye, reach: a, tremble: 1 }, armL: { preset: 'prop' }, extra: { tears: 0.5 } });
  return { shot: framed([0.12, 0.62, 0.15], { dist: 3.3, yaw: 64, pitch: 8, fov: 34, screenY: 0.48, drift: 0 }) };
});
S('wipe tear, push glasses up, glare', 3, (lt, s) => {
  const U = s.user;
  const w = ramp(lt, 0.2, 0.5) * (1 - ramp(lt, 1.1, 1.4)), g = ramp(lt, 1.5, 1.8) * (1 - ramp(lt, 2.4, 2.7));
  U.update(s.t, { body: { sit: 1 }, face: lt < 1.4 ? 'tremble' : 'glare', gaze: 'camera',
    armR: w > 0.01 ? { preset: 'wipe', reach: w } : g > 0.01 ? { preset: 'glasses', reach: g } : { preset: 'knee' }, armL: { preset: 'lap' },
    extra: { glassesSlip: lt < 1.6 ? 1 : 1 - ramp(lt, 1.6, 1.8), tears: 0.4 * (1 - ramp(lt, 0.4, 1.0)), phone: 0.6 } });
  return { shot: framed([0, 0.85, 0.2], { dist: 1.5, yaw: 10, pitch: 4, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('phone glow in the dark (dusk light)', 2.5, (lt, s) => {
  const U = s.user;
  s.dim = 0.18;
  const pose = { face: lt < 1.2 ? 'scroll' : 'dawning', extra: { phone: 1, phoneUp: 1, tap: tapAt(s.t), scroll: lt * 0.3 }, head: { pitch: 0.22 } };
  pose.gaze = U.anchor('phoneScreen'); U.update(s.t, pose); pose.gaze = U.anchor('phoneScreen'); U.update(s.t, pose);
  return { shot: framed([0, 1.32, 0], { dist: 1.3, yaw: 25, pitch: -2, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('kneel + crouch (generic)', 2.5, (lt, s) => {
  const U = s.user, k = ramp(lt, 0.2, 1.2) * (1 - ramp(lt, 1.6, 2.2)), c = ramp(lt, 1.6, 2.2);
  U.update(s.t, { body: { kneel: k, crouch: c * 0.8 }, face: 'idle', gaze: 'camera', extra: { phone: 0.6 } });
  return { shot: framed([0, 0.7, 0], { dist: 3.4, yaw: 45, pitch: 4, fov: 32, screenY: 0.45, drift: 0 }) };
});

// ---------------------------------------------------------------------------------- probes (review fixes) + bench framings
S('phone hold close-up (cradle grip, orbit)', 3, (lt, s) => {
  const U = s.user;
  const pose = { face: 'idle', head: { pitch: 0.18 }, extra: { phone: 0.85 } };
  U.update(s.t, pose); pose.gaze = U.anchor('phoneScreen'); U.update(s.t, pose);
  const p = U.anchor('phone');
  return { shot: framed([p.x, p.y + 0.02, p.z], { dist: 0.75, yaw: -70 + 140 * (lt / 3), pitch: 12, fov: 30, screenY: 0.5, drift: 0 }) };
});
S('defend: from the threat POV, then 3/4', 3, (lt, s) => {
  const U = s.user;
  s.big.visible = lt >= 1.5;
  const B = s.bigAnchors();
  U.update(s.t, { yaw: 0.6, body: { sit: 1, shrug: 0.5, tremble: 0.5 }, face: 'terror', gaze: B.eye, head: { follow: 0.6 },
    armR: { preset: 'defend', threat: B.eye, tremble: 0.6 }, armL: { preset: 'clutch' }, extra: { tears: 0.5 } });
  if (lt < 1.5) { const e = U.anchor('eyes'); const c = B.eye.clone().lerp(e, 0.15); return { shot: { pos: c.toArray(), look: e.toArray(), fov: 24, drift: 0 } }; }
  const e = U.anchor('eyes');
  return { shot: framed([e.x, e.y - 0.2, e.z], { dist: 2.5, yaw: -25, pitch: 8, fov: 32, screenY: 0.4, drift: 0 }) };
});
S('look back (3/4-back camera, close)', 2.5, (lt, s) => {
  const U = s.user, rate = U.walkRate('stomp');
  const lb = ramp(lt, 0.3, 0.7) * (1 - ramp(lt, 1.9, 2.3));
  U.update(s.t, { yaw: Math.PI, walk: { amount: 1, phase: lt * rate, style: 'stomp' }, body: { lookBack: lb }, face: 'guilt', gaze: lb > 0.3 ? 'camera' : null, extra: { phone: 0.5 } });
  return { shot: framed([0, 1.4, 0], { dist: 1.7, yaw: -32, pitch: 3, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('bench: head close-up (USER)', 1, (lt, s) => {
  s.user.update(s.t, { face: 'terror', gaze: 'camera', extra: { tears: 0.6, phone: 0.85 } });
  return { shot: framed([0, 1.43, 0], { dist: 0.85, yaw: 15, pitch: 2, fov: 30, screenY: 0.4, drift: 0 }) };
});
S('bench: head close-up (set only)', 1, (lt, s) => {
  s.user.update(s.t, { face: 'terror', gaze: 'camera', extra: { tears: 0.6, phone: 0.85 } });
  s.user.root.visible = false;
  return { shot: framed([0, 1.43, 0], { dist: 0.85, yaw: 15, pitch: 2, fov: 30, screenY: 0.4, drift: 0 }) };
});
export const DURATION = T0;
export const SEGMENTS = seg.map((x) => ({ name: x.name, t0: x.t0, t1: x.t1 }));

// ---------------------------------------------------------------------------------- set
export async function setup(app) {
  const scene = new THREE.Scene();
  const sky = new THREE.Mesh(new THREE.SphereGeometry(60, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: 'varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 a = vec3(1.0,0.8,0.66), b = vec3(0.56,0.55,0.8); gl_FragColor = vec4(mix(a, b, smoothstep(-0.05, 0.6, h)), 1.0);\n#include <colorspace_fragment>\n}',
  }));
  scene.add(sky);
  const ground = new THREE.Mesh(new THREE.CircleGeometry(30, 48), new THREE.MeshLambertMaterial({ color: 0xd9b6a0 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  const dots = new THREE.InstancedMesh(new THREE.CircleGeometry(0.035, 12), new THREE.MeshBasicMaterial({ color: 0xbf9580 }), 400);
  let n = 0; const m = new THREE.Matrix4();
  for (let i = -10; i < 10; i++) for (let j = -10; j < 10; j++) { m.makeRotationX(-Math.PI / 2).setPosition(i * 0.5, 0.002, j * 0.5); dots.setMatrixAt(n++, m); }
  scene.add(dots);
  const hemi = new THREE.HemisphereLight(0xffe6cc, 0x6d5a78, 1.05); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffe0bc, 2.5); key.position.set(2.2, 4, 3.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 15 }); key.shadow.bias = -0.0005;
  scene.add(key); scene.add(key.target);
  const rim = new THREE.DirectionalLight(0xa9bfff, 1.6); rim.position.set(-3, 2.6, -3); scene.add(rim);
  EYE_LIGHT.uKeyDir.value.copy(key.position).normalize();
  EYE_LIGHT.uKeyColor.value.set(1.0, 0.93, 0.84);
  const user = await app.char('USER');
  scene.add(user.root);
  // big plump partner stand-in (Void-ish, ~2.8 m)
  const big = new THREE.Group();
  const vm = new THREE.MeshStandardMaterial({ color: 0x2a2450, roughness: 0.6, emissive: 0x120c30 });
  const body = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 28), vm); body.scale.set(0.9, 1.25, 0.8); body.position.y = 1.25; big.add(body);
  const eyeM = new THREE.MeshBasicMaterial({ color: 0xe8fbff });
  for (const x of [-0.18, 0.18]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 12), eyeM); e.position.set(x, 2.05, 0.66); big.add(e); }
  big.scale.setScalar(0.6); big.position.set(0.68, 0, 1.0); big.rotation.y = -2.55; big.visible = false; scene.add(big);
  const bigAnchors = () => { big.updateMatrixWorld(true); const w = (x, y, z) => V(x, y, z).applyMatrix4(big.matrixWorld); return { eye: w(0, 2.05, 0.7), chest: w(0, 1.3, 0.8) }; };
  // HUD label (camera child)
  scene.add(app.camera);
  const lc = document.createElement('canvas'); lc.width = 1024; lc.height = 64;
  const ltex = new THREE.CanvasTexture(lc); ltex.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1, 1 / 16), new THREE.MeshBasicMaterial({ map: ltex, transparent: true, depthTest: false, toneMapped: false }));
  label.renderOrder = 999; app.camera.add(label);
  return { scene, user, big, bigAnchors, label, lc, ltex, lastLabel: '', lights: [[key, 2.5], [rim, 1.6], [hemi, 1.05]], sky, look: { bloom: 0.32, bloomThreshold: 0.85, vignette: 0.22, warm: 0.08 } };
}

export async function update(t, app, s) {
  s.t = t;
  const tt = ((t % DURATION) + DURATION) % DURATION;
  const sg = seg.find((x) => tt >= x.t0 && tt < x.t1) || seg[0];
  s.big.visible = false; s.dim = 1; s.user.root.visible = true;
  // pass 1: run the segment to get the shot (the rig needs the final camera for catchlights / gaze 'camera')
  const r0 = sg.fn(tt - sg.t0, s, app) || {};
  applyShot(app.camera, r0.shot, t);
  app.camera.updateMatrixWorld(true);
  sg.fn(tt - sg.t0, s, app);
  for (const [l, b] of s.lights) l.intensity = b * s.dim;
  // the eyeball shader is lit by EYE_LIGHT, not the scene lights: dim it with them
  if (!s.eyeK) s.eyeK = [EYE_LIGHT.uKeyColor.value.clone(), EYE_LIGHT.uAmbient.value.clone()];
  EYE_LIGHT.uKeyColor.value.copy(s.eyeK[0]).multiplyScalar(s.dim); EYE_LIGHT.uAmbient.value.copy(s.eyeK[1]).multiplyScalar(Math.max(0.25, s.dim));
  s.sky.visible = s.dim >= 1; s.scene.background = s.dim >= 1 ? null : s.darkBg || (s.darkBg = new THREE.Color(0x141a2c));
  s.look.exposure = s.dim < 1 ? 1.15 : 1.0;
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
