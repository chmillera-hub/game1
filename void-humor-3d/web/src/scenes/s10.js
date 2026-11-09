// s10 rolls_its_eyes — the Void covers its hurt with theatrical attitude: an epic eye-roll, two nebula huffs, a turned
// back, a sulky plop onto the grass. Then the storyteller takes us round to the side the user can't see.
//   b01 VOID_CU: a slow, theatrical full eye-roll on "rolls its eyes" (lids lift to let the irises pass), hood lolls back.
//   b02-b03 easing back to include the hood top and a drifting thought-seed: huff (cheeks/hood puff up, BLAST: a violet
//       nebula puff out of the top of the hood like a kettle), huff #2 blows the seed clean away; a last little "hmph".
//   b04 MASTER: three shuffling fat-legged stomps, turning in place (face sweeps past camera -> profile -> back), arms
//       crossed, hood up and away. Jesus's mouth comes open; the user flinches at each stomp.
//   b05 same: PLOP onto its backside (squash + 2 damped wobbles), hood droops; star motes lift off its back; Jesus's
//       eyebrow bounce; the user blinks.
//   b06 CUT ROUND to the front: the sulk melts into a sad pout, eyes down, one star mote drifts down like a tear on
//       "it hears that a lot", one big finger picks at the grass.
//   b07 USER_LOST: six-frame guilt flicker, jaw sets, eyes slide away, phone check; the Void's back deflates, last puff.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, hash1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, galaxyAt, galaxySpin, sy, px } from './marks.js';
import { VX, eyeRoll } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, fitShot, mixShot, W, WY, MARKS as M, starSprite, seedSprite } from './armour_shared.js';
import { galaxyFloor, userPos, sceneLook } from './armour_common.js';

let S = null;
const TAU = Math.PI * 2;

export default {
  id: 's10',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const st = { scene: set.scene, set, jesus, vd, user };
    st.fx = new Particles({ max: 48 }); set.scene.add(st.fx.mesh);
    st.puffs = new Particles({ max: 24, blending: 'normal', intensity: 1.0 }); set.scene.add(st.puffs.mesh);
    st.seed = seedSprite(0.3); set.scene.add(st.seed);
    st.tear = starSprite(0xdff4ff, 0.08); set.scene.add(st.tear);
    st.floorGal = galaxyFloor(st.fx); set.scene.add(st.floorGal.mesh);
    S = st.S = statics(st);
    return st;
  },
  async update(t, app, st) {
    const { set, jesus, vd, user } = st;
    st.scene.add(jesus.root, vd.root, user.root, st.fx.mesh, st.puffs.mesh, st.seed, st.tear, st.floorGal.mesh);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 10);
    const vp = voidPose(t);
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (shot.vsk ?? 1), voidPos: vp.pos, sunShift: shot.sunShift ?? 0, sunGlow: shot.sunGlow ?? 1 });

    user.update(t, userPose(t));
    vd.update(t, { ...vp, gaze: voidGazeOf(t, user) });
    jesus.update(t, jesusPose(t, user, vd));

    // ---- particles: sky galaxy, huff puffs (normal blend), plop motes + seed + tear
    st.fx.begin(); st.puffs.begin();
    const g = galaxyAt(t);
    if (g) st.fx.add(g, EDGE.GALAXY.size, 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
    huffPuffs(t, st.puffs, st.fx);
    plopMotes(t, st.fx);
    st.fx.end(); st.puffs.end();
    const sd = seedState(t);
    st.seed.visible = sd.a > 0.01; st.seed.position.copy(sd.p); st.seed.material.opacity = sd.a; st.seed.material.rotation = sd.rot;
    const tr = tearState(t);
    st.tear.visible = tr.a > 0.01; st.tear.position.copy(tr.p); st.tear.material.opacity = tr.a; st.tear.scale.setScalar(0.08 * tr.s);
    st.floorGal.update(t);
    st.look = sceneLook('s10', set.look, t);
  },
};

// ------------------------------------------------------------------------------------------------ key times
const KT = () => {
  const b1 = T('s10b01'), b3 = T('s10b03'), b4 = T('s10b04'), b5 = T('s10b05'), b6 = T('s10b06'), b7 = T('s10b07');
  const rolls = wordT('s10b01', 'rolls', { fallback: 0.27 });
  const rollA = rolls - 0.06, rollB = rolls + 1.08;
  const huffA = b3 + 0.02, huffB = b3 + 0.72, huffC = b3 + 1.4;    // the vocal's two huffs + a trailing "hmph" (air at 1.4)
  const plant = [b4 + 0.42, b4 + 0.92, b4 + 1.42];                 // stomp plants, 0.5 s apart (matches footsteps_stomp)
  const sitA = b5 + 0.1, contact = b5 + 0.44;
  const hears = wordT('s10b06', 'hears', { fallback: 0.6 }), lot = wordT('s10b06', 'lot.', { fallback: 0.82 });
  return { b1, b3, b4, b5, b6, b7, rollA, rollB, huffA, huffB, huffC, plant, sitA, contact, hears, lot };
};

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { vd, user } = st;
  const K = KT();
  const out = {};
  user.update(K.b4, userPose(K.b4, true));
  out.uEyes = user.anchor('eyes');
  const vs = voidPose(K.b1);
  vd.update(K.b1, { ...vs, gaze: out.uEyes });
  out.vEyes = vd.anchor('eyes'); out.hoodTop = vd.anchor('hoodTop');
  const v6 = voidPose(K.b6 + 1.2);
  vd.update(K.b6 + 1.2, { ...v6, gaze: null });
  out.vEyesSit = vd.anchor('eyes'); out.vBackSit = vd.anchor('back'); out.vHeadSit = vd.anchor('head');
  out.vSit = toV(W(M.VSIT));
  // cameras
  out.VCU_A = EDGE.shot(EDGE.L(out.vEyes), { dist: 3.5, yaw: -36, pitch: -4, fov: 33, screenY: sy(385), drift: 0.2 });
  out.VCU_B = EDGE.shot(EDGE.L(out.vEyes), { dist: 6.0, yaw: -34, pitch: -3, fov: 33, screenY: sy(740), drift: 0.2 });
  out.MASTER = EDGE.cam('MASTER', { drift: 0.2 });
  out.MASTER_B = { ...EDGE.cam('MASTER', { drift: 0.15 }), fov: 42 };
  // starts medium (the big finger picking at the grass reads above the subtitle band), pushes in to the face for "a lot"
  out.ROUND = EDGE.shot(EDGE.L(out.vEyesSit), { dist: 5.4, yaw: 124, pitch: 5, fov: 33, screenY: sy(330), drift: 0.2 });
  out.ROUND_B = EDGE.shot(EDGE.L(out.vEyesSit), { dist: 3.5, yaw: 120, pitch: 5, fov: 33, screenY: sy(385), drift: 0.15 });
  // USER_LOST: close lost profile of the user (face y~420) looking frame-right at the seated Void's back
  // b07: close 3/4 on the user looking off frame-right at the Void's back (the Void sits 3.3 m straight ahead of the
  // user, so no portrait frame holds both a readable face and its back: the face wins — the guilt flicker must read)
  out.LOST = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.45, yaw: 108, pitch: 4, fov: 33, screenY: sy(430), drift: 0.15 });
  out.LOST_B = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.33, yaw: 108, pitch: 4, fov: 33, screenY: sy(430), drift: 0.15 });
  // camera right vector for the huff shot (to place the seed)
  const c = toV(out.VCU_B.pos), l = toV(out.VCU_B.look), f = l.sub(c).normalize();
  out.camRight = V3(-f.z, 0, f.x).normalize();
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const K = KT();
  if (t < K.b4 - 0.04) {
    const u = ramp(t, K.b3 - 0.25, K.huffB + 0.2, 'inOut');
    return { ...mixShot(S.VCU_A, S.VCU_B, u), vsk: 1.0 };
  }
  if (t < K.b6 - 0.03) return mixShot(S.MASTER, S.MASTER_B, ramp(t, K.b4, K.b6, 'inOut'));
  if (t < K.b7 - 0.12) return { ...mixShot(S.ROUND, S.ROUND_B, ramp(t, K.b6 + 0.6, K.lot + 0.3, 'inOut')), sunGlow: 0.7 };
  return { ...mixShot(S.LOST, S.LOST_B, ramp(t, K.b7 - 0.12, T('s10.end'), 'linear')), sunGlow: 0.6, sunShift: -0.12 };
}

// ------------------------------------------------------------------------------------------------ the Void
/** turn-in-place progress: each stomp turns ~60 deg during its swing (the 0.45 s before its plant) */
function turnProg(t, K) {
  let s = 0;
  for (const p of K.plant) s += smooth(clamp((t - (p - 0.45)) / 0.45));
  return s / 3;
}
function voidPose(t) {
  const K = KT();
  const y0 = WY(M.V), y1 = WY(M.VSIT);
  const tp = turnProg(t, K);
  const yaw = lerp(y0, y1, tp);
  const p0 = W(M.V), p1 = W(M.VSIT);
  const pos = [lerp(p0[0], p1[0], tp), 0, lerp(p0[2], p1[2], tp)];
  // ---- walk (three shuffles) — phase: L plants at plant[0] (phase 0), R at plant[1] (0.5), L at plant[2] (1.0)
  const wAmt = 0.55 * ramp(t, K.b4 + 0.0, K.b4 + 0.15) * (1 - ramp(t, K.plant[2], K.plant[2] + 0.22));
  const walk = { amount: wAmt, phase: (t - K.plant[0]) * 1.0, style: 'stomp' };
  // ---- the eye roll (b01)
  const uRoll = ramp(t, K.rollA, K.rollB, 'linear');
  const er0 = eyeRoll(0, -1), er = eyeRoll(uRoll, -1);
  const antic = ramp(t, K.rollA - 0.3, K.rollA);
  const roll = Math.sin(Math.PI * uRoll);
  // ---- huffs: puff up (anticipation) -> BLAST
  const puffUp = (a, d, amp = 1) => amp * (ramp(t, a - d, a - 0.02, 'out') * (1 - ramp(t, a - 0.02, a + 0.14, 'out')));
  const puff = Math.max(puffUp(K.huffA, 0.3), puffUp(K.huffB, 0.42), puffUp(K.huffC, 0.25, 0.4));
  const blast = (a) => pulse(t, a - 0.02, 0.05, 0.05, 0.35);
  const bl = Math.max(blast(K.huffA), blast(K.huffB), 0.5 * blast(K.huffC));
  // ---- plop (b05)
  const rise = pulse(t, K.b5 - 0.05, 0.13, 0.02, 0.1);
  const sit = ease3(clamp((t - K.sitA) / (K.contact - K.sitA)));
  const jig = wobble(t, K.contact, 2.3, 4.2);
  // ---- b06 picking at the grass, b07 deflate
  const pick = ramp(t, K.b6 + 0.35, K.b6 + 0.95) * (1 - ramp(t, K.b7 - 0.1, K.b7 + 0.5));
  const deflate = ramp(t, K.b7 + 0.1, K.b7 + 0.8);
  const body = {
    sit: sit * 1,
    swell: 0.35 * puff - 0.12 * bl,
    shrug: 0.18 * puff + 0.12 * (1 - tp) * ramp(t, K.b4, K.b4 + 0.2) * (1 - ramp(t, K.plant[2], K.plant[2] + 0.4)) - 0.15 * deflate,
    stretch: 0.03 * rise - 0.07 * Math.max(0, jig) * (t > K.contact ? 1 : 0) + 0.035 * Math.min(0, jig) * -1 * 0,
    bounce: 0.04 * rise - 0.03 * jig * (t > K.contact ? 1 : 0),
    lean: -0.06 * puff + 0.08 * bl + 0.05 * ramp(t, K.contact, K.contact + 0.5) + 0.06 * pick,
    slump: 0.25 * ramp(t, K.contact + 0.2, K.contact + 0.8) + 0.25 * deflate,
    breathe: t < K.b4 ? 0.6 : 1,
    twist: -0.12 * pick,
  };
  // ---- head
  const headUp = ramp(t, K.b4 - 0.1, K.b4 + 0.3) * (1 - ramp(t, K.contact, K.contact + 0.35));
  const head = {
    pitch: -0.14 * (t < K.b4 ? 1 : 0) * (1 - ramp(t, K.rollA - 0.4, K.rollA)) - 0.13 * roll - 0.06 * puff + 0.05 * bl
      - 0.18 * headUp + 0.26 * ramp(t, K.contact + 0.05, K.contact + 0.6) + 0.08 * ramp(t, K.b6 + 0.2, K.b6 + 1.0) + 0.06 * deflate,
    yaw: 0.3 * headUp * (1 - tp * 0.5) + 0.18 * ramp(t, K.rollB, K.rollB + 0.3) * (1 - ramp(t, K.b4, K.b4 + 0.4)),
    roll: 0.07 * roll + 0.06 * headUp,
  };
  // ---- face
  let face;
  if (t < K.rollB + 0.05) {
    const pre = VX('scowl', { lidAngry: 1.55, lidU: 0.55, browIn: -1.0, mSmile: -0.95, mPress: 0.75 });   // (s09's clamp)
    const ann = VX('annoyed', { ...er, mAsym: 0.45, mPress: 0.7, mSmile: -0.4, lidU: er.lidU });
    if (t < K.rollA) {
      const a = ramp(t, K.rollA - 0.35, K.rollA);
      face = k(t, [[K.rollA - 0.35, pre], [K.rollA, VX('annoyed', { ...er0, gazePitch: er0.gazePitch - 0.08, lidU: 0.5, mAsym: 0.45, mPress: 0.7, mSmile: -0.4 })]]);
      face.gazeYaw = lerp(-0.04, er0.gazeYaw, a); face.gazePitch = lerp(-0.2, er0.gazePitch - 0.08, a);
    } else face = ann;
  } else if (t < K.b4 + 0.05) {        // huffs: brow-wisps pinned down, eyes pointedly away
    const base = VX('huff', { puff: 0, gazeYaw: 0.5, gazePitch: -0.08, lidU: 0.55, saccade: 0, autoBlink: 0 });
    const puffed = VX('huff', { puff: 1, gazeYaw: 0.5, gazePitch: 0.0, lidU: 0.4, lidL: 0.7, saccade: 0, autoBlink: 0 });
    face = k(0, [[0, base]]);
    for (const key in puffed) if (typeof puffed[key] === 'number') face[key] = lerp(base[key], puffed[key], puff);
    face.puff = puff;
    face.mOpen = Math.max(face.mOpen, 0.25 * bl); face.mRound = Math.max(face.mRound, 0.8 * bl);
  } else if (t < K.b6 + 0.1) {         // the turn: "hmph" (eyes shut haughtily, chin up) -> plop
    face = k(t, [
      [K.b4, VX('annoyed', { gazeYaw: 0.5, lidU: 0.5, mAsym: 0.45, mPress: 0.75, autoBlink: 0 })],
      [K.b4 + 0.3, VX('annoyed', { lidU: 0.05, lidL: 0.3, browIn: -0.25, browSq: 0.5, mAsym: 0.4, mPress: 0.85, mSmile: -0.45, autoBlink: 0, saccade: 0 })],
      [K.contact - 0.02, VX('annoyed', { lidU: 0.05, lidL: 0.3, browIn: -0.25, browSq: 0.5, mAsym: 0.4, mPress: 0.85, mSmile: -0.45, autoBlink: 0, saccade: 0 })],
      [K.contact + 0.08, VX('flinch', { lidU: 0.9, mOpen: 0.06, mRound: 0.4, autoBlink: 0, saccade: 0 })],
      [K.contact + 0.45, VX('annoyed', { lidU: 0.45, gazePitch: -0.3, mPout: 0.25, mPress: 0.6, browIn: -0.15, autoBlink: 0, saccade: 0 })],
    ]);
  } else {                             // b06: the sulk melts into a sad pout (the side nobody sees)
    face = k(t, [
      [K.b6 + 0.1, VX('annoyed', { lidU: 0.45, gazePitch: -0.3, mPout: 0.25, mPress: 0.6, browIn: -0.15, saccade: 0 })],
      [K.b6 + 1.0, VX('sad', { gazePitch: -0.36, gazeYaw: -0.1, lidU: 0.62, lidSad: 0.75, browIn: 1.0, browOut: -0.45, mPout: 0.12, mSmile: -0.75, mPress: 0.2, wet: 0.6, saccade: 0.2 })],
      [K.lot, VX('sad', { gazePitch: -0.4, gazeYaw: -0.12, lidU: 0.5, lidSad: 0.85, browIn: 1.1, browOut: -0.5, mPout: 0.18, mSmile: -0.85, mPress: 0.25, mTremble: 0.3, wet: 0.8, saccade: 0.2 })],
      [K.b7 + 0.6, VX('sad', { gazePitch: -0.42, lidU: 0.46, lidSad: 0.85, browIn: 1.0, browOut: -0.5, mPout: 0.12, mSmile: -0.8, mPress: 0.2, wet: 0.7 })],
    ]);
    face.autoBlink = 0;
    face.blink = Math.max(face.blink || 0, pulse(t, K.lot + 0.05, 0.16, 0.18, 0.3));   // a slow blink on "a lot"
  }
  // ---- arms: crossed all along; in b06 the RIGHT hand (toward the cut-round camera) drops to pick at the grass
  const grass = groundPick(t, K, yaw, pos);
  const armL = { preset: 'crossed' };
  const armR = pick > 0.001
    ? { preset: 'tip', from: 'crossed', mix: pick, target: grass, reach: pick, tip: true, fingers: [Math.sin(yaw) * 0.6, -0.8, Math.cos(yaw) * 0.6] }
    : { preset: 'crossed' };
  const extra = { motes: t > K.contact - 0.1 && t < K.contact + 0.5 ? 0 : 1, stars: t > K.b6 ? 0.8 : 1 };
  return { pos, yaw, walk, body, head, face, armL, armR, extra, blinkAt: [] };
}
function ease3(u) { return u * u * (1.6 - 0.6 * u); }   // accelerate into the plop (gravity), no slow-down
function groundPick(t, K, yaw, pos) {
  // a spot of grass in front-right of the seated Void (its right = toward the cut-round camera); tiny picking strokes
  const f = V3(Math.sin(yaw), 0, Math.cos(yaw)), r = V3(-Math.cos(yaw), 0, Math.sin(yaw));
  const stroke = 0.025 * Math.max(0, Math.sin((t - K.b6) * TAU * 1.4)) * ramp(t, K.b6 + 0.95, K.b6 + 1.2);
  return toV(pos).addScaledVector(f, 1.02 - 0.6 * stroke).addScaledVector(r, 0.24).add(V3(0, 0.03 + 1.6 * stroke, 0));
}
function voidGazeOf(t, user) {
  const K = KT();
  if (t < K.rollA - 0.35) return user.anchor('eyes');     // still glaring at the user (from s09)
  return null;                                             // then: face params (roll, pointed look away, downcast)
}

// ------------------------------------------------------------------------------------------------ particles
function huffPuffs(t, ps, fx) {
  const K = KT();
  const top = S.hoodTop;
  const blasts = [[K.huffA, 1, 11], [K.huffB, 1.25, 23], [K.huffC, 0.55, 37]];
  for (const [a, amp, seed] of blasts) {
    if (t < a - 0.02 || t > a + 2.2) continue;
    const n = Math.round(4 + 2 * amp);
    for (let i = 0; i < n; i++) {
      const h1 = hash1(seed * 31 + i), h2 = hash1(seed * 17 + i * 3), h3 = hash1(seed * 7 + i * 11);
      const age = t - (a + 0.035 * i);
      if (age < 0) continue;
      const life = 1.5 + 0.6 * h1;
      if (age > life) continue;
      const u = age / life;
      const rise = (0.9 + 0.5 * h2) * amp * (1 - Math.exp(-age * 2.6)) / 2.6 * 2.2;
      const side = (h3 - 0.5) * 0.5 * amp * (1 - Math.exp(-age * 2));
      const p = top.clone().add(V3(0, 0.05 + rise, 0)).addScaledVector(S.camRight, side);
      const size = (0.3 + 0.75 * amp * Math.sqrt(u)) * (0.8 + 0.4 * h1);
      const a0 = 0.9 * smooth(u / 0.06) * (1 - smooth((u - 0.3) / 0.7));
      ps.add(p.toArray(), size, i % 2 ? 0x34266e : 0x4a3590, a0, h1 * 6.28 + age * 0.4 * (h2 - 0.5), i % 3 === 0 ? CELL.nebula : CELL.puff);
      if (i < 3) fx.add(p.clone().addScaledVector(S.camRight, (h2 - 0.5) * size * 0.5).add(V3(0, (h1 - 0.5) * size * 0.4, 0)).toArray(), 0.06, 0xe8e0ff, 0.9 * a0, h2 * 6, CELL.star);   // a soft glow in the core
    }
  }
}
function plopMotes(t, fx) {
  const K = KT();
  const a = K.contact;
  if (t < a || t > a + 3.4) return;
  const back = S.vBackSit;
  for (let i = 0; i < 7; i++) {
    const h1 = hash1(500 + i), h2 = hash1(600 + i * 7), h3 = hash1(700 + i * 13);
    const age = t - a - 0.05 * i;
    if (age < 0 || age > 2.8) continue;
    const u = age / 2.8;
    const p = back.clone().add(V3((h1 - 0.5) * 0.9, 0.1 + 0.25 * h2 + 0.32 * age, (h3 - 0.5) * 0.9));
    p.x += 0.04 * Math.sin(age * 2 + i); p.z += 0.04 * Math.cos(age * 1.7 + i);
    const al = smooth(u / 0.1) * (1 - smooth((u - 0.5) / 0.5));
    fx.add(p.toArray(), 0.07 + 0.04 * h2, i % 2 ? 0xc9b8ff : 0x9fe9ff, 0.9 * al, h1 * 6, CELL.star);
  }
}
/** the thought-seed drifting past the hood top; huff #2 blows it clean away */
function seedState(t) {
  const K = KT();
  const t0 = K.b3 - 1.2, hit = K.huffB + 0.06;
  if (t < t0 || t > hit + 1.6 || t > K.b4) return { p: V3(), a: 0, rot: 0 };
  const top = S.hoodTop, R = S.camRight;
  const base = top.clone().add(V3(0, 0.42, 0)).addScaledVector(R, -0.62);
  const drift = (Math.min(t, hit) - hit) * 0.22;              // drifting right, arriving above-left of the hood top
  const p = base.clone().addScaledVector(R, drift).add(V3(0, 0.03 * Math.sin(t * 1.9), 0));
  let rot = 0.15 * Math.sin(t * 1.3);
  if (t > hit) {
    const d = t - hit, e = (1 - Math.exp(-d * 2.2)) / 2.2;
    p.addScaledVector(R, -1.2 * e).add(V3(0, 2.3 * e, 0));       // blasted up and away (up-left, out of the top)
    rot += d * 7;
  }
  return { p, a: smooth((t - t0) / 0.4), rot };
}
/** the single star mote that drifts down from the hood edge like a tear (b06, on "it hears that a lot") */
function tearState(t) {
  const K = KT();
  const t0 = K.hears - 0.1;
  if (t < t0 || t > K.b7 - 0.12) return { p: V3(), a: 0, s: 1 };
  const d = t - t0;
  const e = S.vEyesSit, hd = S.vHeadSit;
  // start under the eye nearest the camera side, at the hood brim; slide down and a little forward
  const toCam = toV(S.ROUND.pos).sub(e).setY(0).normalize();
  const side = V3(-toCam.z, 0, toCam.x);
  const p = e.clone().addScaledVector(toCam, 0.32).addScaledVector(side, -0.16).add(V3(0, -0.12 - 0.11 * d - 0.02 * d * d, 0));
  void hd;
  return { p, a: 0.95 * smooth(d / 0.3) * (1 - smooth((d - 1.6) / 0.7)), s: 1 + 0.15 * Math.sin(d * 5) };
}

// ------------------------------------------------------------------------------------------------ the user
function userPose(t, statOnly = false) {
  const K = KT();
  const phoneT = K.b7 + 0.55;
  let gaze = null;
  if (S && !statOnly && t < phoneT) {
    const back = S.vBackSit.clone().add(V3(0, 0.55 - 0.3 * ramp(t, K.contact - 0.2, K.contact + 0.3), 0));
    gaze = t < K.b4 + 0.7 ? S.vEyes : back;           // the Void's face -> as it turns, its back
    if (t > K.b4 + 0.55 && t < K.b4 + 0.85) gaze = S.vEyes.clone().lerp(back, smooth((t - K.b4 - 0.55) / 0.3));
  }
  const flinch = K.plant.reduce((m, p) => Math.max(m, pulse(t, p + 0.02, 0.06, 0.02, 0.18)), 0) + 0.8 * pulse(t, K.contact + 0.02, 0.06, 0.03, 0.22);
  const phoneUp = ramp(t, K.b7 + 0.45, K.b7 + 0.8);
  const P = {
    pos: userPos(t), yaw: WY(M.U), gaze,
    body: { sit: 1, sitPath: 'plain', hunch: 0.18 + 0.1 * phoneUp, shrug: 0.12, tremble: 0.15, flinch: 0.45 * flinch },
    armL: { preset: [['crossed', 1 - 0.8 * phoneUp + 1e-4], ['look', 0.8 * phoneUp]], tremble: 0.1 },
    armR: { preset: 'crossed', tremble: 0.1 },
    head: { follow: 0.4, pitch: -0.12 * (1 - phoneUp) + 0.22 * phoneUp },
    extra: { phone: 0.85, screen: 'feed', scroll: Math.max(0, t - phoneT) * 0.6 },
  };
  P.face = k(t, [
    ['s10', UX('pout', { lidU: 0.66, mPout: 1.1 })],
    [K.b4 + 0.1, UX('pout', { lidU: 0.75, mPout: 0.9 })],
    [K.b4 + 0.6, UX('suspicious', { lidU: 0.92, browIn: 0.1, mPout: 0.4 })],          // the brows lift a fraction
    [K.contact + 0.3, UX('disbelief', { lidU: 0.85, mPout: 0.3 })],
    [K.b7 + 0.12, UX('pout', { lidU: 0.8, mPout: 0.6 })],
    [K.b7 + 0.17, UX('guilt', { browIn: 0.85, mPout: 0, mPress: 0.1 })],              // six frames of guilt
    [K.b7 + 0.42, UX('guilt', { browIn: 0.8, mPout: 0, mPress: 0.1 })],
    [K.b7 + 0.52, UX('hellno', { mPress: 0.8, lidU: 0.7 })],                            // jaw sets, eyes slide away
    [phoneT + 0.2, UX('scroll', { mPress: 0.5, gazePitch: -0.38, gazeYaw: 0.05 })],    // pretend to check the phone
  ]);
  if (t > K.b7 + 0.5 && t < phoneT) { P.face.gazeYaw = -0.35 * smooth((t - K.b7 - 0.5) / 0.08); }
  P.blinkAt = [K.contact + 0.12, K.b7 + 0.47];
  return P;
}

// ------------------------------------------------------------------------------------------------ Jesus
function jesusPose(t, user, vd) {
  const K = KT();
  const vEye = vd.anchor('eyes'), vBack = vd.anchor('back');
  const target = t < K.contact ? vEye : vBack.clone().add(V3(0, 0.3, 0));
  const gk = [
    ['s10', vEye],
    [K.b7 + 0.6, () => user.anchor('eyes'), 0.1],
  ];
  const gaze = t < K.b7 + 0.6 ? target : gazeSched(t, gk);
  const bounce = pulse(t, K.contact + 0.04, 0.07, 0.05, 0.25);
  const face = k(t, [
    ['s10', JX('pressed', { mSmile: 0.05, mPress: 0.95, browIn: 0.92, browOut: 0.8, lidU: 1.16 })],
    [K.b4 + 0.3, JX('oh', { mOpen: 0.13, mRound: 0.35, browIn: 0.6, browOut: 0.55, lidU: 1.18 })],    // mouth slightly open
    [K.contact + 0.5, JX('oh', { mOpen: 0.08, mRound: 0.3, browIn: 0.55, browOut: 0.5, lidU: 1.05 })],
    [K.b7, JX('concerned', { mPress: 0.5, browIn: 0.55 })],
  ]);
  face.browIn += 0.35 * bounce; face.browOut += 0.4 * bounce; face.lidU += 0.1 * bounce;
  return {
    pos: W(M.JM), yaw: WY(M.JM), face, gaze,
    head: { look: target, follow: 0.72, roll: 0.03 },
    body: { shrug: 0.1, recoil: 0.04 * bounce },
    armL: { preset: [['clasp', 0.7], ['clasp_chest', 0.3]] },
    armR: { preset: [['clasp', 0.7], ['clasp_chest', 0.3]] },
    blinkAt: [K.b4 + 0.05, K.contact + 0.25],
  };
}
