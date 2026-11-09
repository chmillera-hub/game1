// s10 rolls_its_eyes — the Void covers its hurt with theatrical attitude: an epic eye-roll, two nebula huffs, a turned
// back, a sulky plop onto the grass. Then the storyteller takes us round to the side the user can't see.
//   b01 VOID_CU: a slow, theatrical full eye-roll on "rolls its eyes" (lids lift to let the irises pass), hood lolls back;
//       the roll's end face melts into the first huff's wind-up (no pop).
//   b02-b03 easing back to include the hood top and a drifting thought-seed: huff (cheeks/hood puff up, BLAST: a glowing
//       violet-teal nebula puff with star specks out of the hood rim like a kettle), huff #2's puff front shoves the
//       seed (hanging in its path above the hood) clean out of frame; a last little "hmph".
//   b04 wide (reframed so the whole Void stays in): three stomps, the hem lifting on each plant so the fat feet peek
//       out (bob + squash + hem swing), turning in place (face sweeps past camera -> profile -> back), arms folded, hood
//       up and away. Jesus's mouth comes open; the user flinches at each stomp.
//   b05 same: PLOP onto its backside (squash + 2 damped wobbles), hood droops; star motes lift off its back; Jesus's
//       eyebrow bounce; the user blinks.
//   b06 CUT ROUND to the front: one big finger picks at the grass (plucks held ~0.8 s before the push), the sulk melts
//       into a sad pout, eyes down, a star mote slides down like a tear on "it hears that a lot", slow blink on "a lot".
//   b07 close 3/4 on the user: six-frame guilt flicker, jaw sets, eyes slide away, the phone comes up in front of the
//       chest to "check" it (eyes on the screen, glow eased down so the face doesn't wash out).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, hash1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, galaxyAt, galaxySpin, sy } from './marks.js';
import { VX, eyeRoll } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { scopeVisible, ensureLittleGalaxy } from './edgeprops.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, fitShot, mixShot, W, WY, MARKS as M, starSprite, seedSprite, headAim } from './armour_shared.js';
import { userPos, sceneLook, updateVoid, userTurnAway } from './armour_common.js';

let S = null;
const TAU = Math.PI * 2;

export default {
  id: 's10',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const st = { scene: set.scene, set, jesus, vd, user };
    st.fx = new Particles({ max: 64 }); set.scene.add(st.fx.mesh);                                   // additive: glows, specks
    st.puffs = new Particles({ max: 24, blending: 'normal', intensity: 1.0 }); set.scene.add(st.puffs.mesh);   // the cloud body
    st.seed = seedSprite(0.42); set.scene.add(st.seed);
    st.tear = starSprite(0xdff4ff, 0.08); set.scene.add(st.tear);
    ensureLittleGalaxy(set);                                       // the shared little galaxy by the sneaker (edgeprops)
    for (const o of [st.fx.mesh, st.puffs.mesh, st.seed, st.tear]) scopeVisible(o, 's10', 's11');
    S = st.S = statics(st);
    return st;
  },
  async update(t, app, st) {
    const { set, jesus, vd, user } = st;
    st.scene.add(jesus.root, vd.root, user.root, st.fx.mesh, st.puffs.mesh, st.seed, st.tear);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 10);
    const vp = voidPose(t);
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (shot.vsk ?? 1), voidPos: vp.pos, sunShift: shot.sunShift ?? 0, sunGlow: shot.sunGlow ?? 1 });

    const up = userPose(t);
    user.update(t, up);
    if (up.screenGaze) { up.gaze = user.anchor('phoneScreen'); up.head.look = up.gaze; user.update(t, up); }   // eyes on the screen
    updateVoid(vd, t, { ...vp, gaze: voidGazeOf(t, user) });
    jesus.update(t, jesusPose(t, user, vd));

    // ---- particles: sky galaxy, huff puffs (normal-blend body + additive glow core + star specks), plop motes
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
    st.look = sceneLook('s10', set.look, t);
  },
};

// ------------------------------------------------------------------------------------------------ key times
const KT = () => {
  const b1 = T('s10b01'), b3 = T('s10b03'), b4 = T('s10b04'), b5 = T('s10b05'), b6 = T('s10b06'), b7 = T('s10b07');
  const rolls = wordT('s10b01', 'rolls', { fallback: 0.27 });
  const rollA = rolls - 0.06, rollB = rolls + 1.08;
  const huffA = b3 + 0.02, huffB = b3 + 0.72, huffC = b3 + 1.4;    // the vocal's two huffs + a trailing "hmph" (air at 1.4)
  const plant = [b4 + 0.42, b4 + 0.92, b4 + 1.42];                 // stomp plants, 0.5 s apart (matches the stomp cues)
  const sitA = b5 + 0.1, contact = b5 + 0.44;
  const hears = wordT('s10b06', 'hears', { fallback: 0.6 }), lot = wordT('s10b06', 'lot.', { fallback: 0.82 });
  const pushA = b6 + 1.45;                                          // the push-in starts after ~0.8 s of held plucks
  return { b1, b3, b4, b5, b6, b7, rollA, rollB, huffA, huffB, huffC, plant, sitA, contact, hears, lot, pushA };
};

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { vd, user } = st;
  const K = KT();
  const out = {};
  user.update(K.b4, userPose(K.b4, true));
  out.uEyes = user.anchor('eyes'); out.uHead = user.anchor('head');
  const vs = voidPose(K.b1);
  vd.update(K.b1, { ...vs, gaze: out.uEyes });
  out.vEyes = vd.anchor('eyes'); out.hoodTop = vd.anchor('hoodTop');
  const v6 = voidPose(K.b6 + 1.2);
  vd.update(K.b6 + 1.2, { ...v6, gaze: null });
  out.vEyesSit = vd.anchor('eyes'); out.vBackSit = vd.anchor('back'); out.vHeadSit = vd.anchor('head'); out.vHoodSit = vd.anchor('hoodTop');
  out.vSit = toV(W(M.VSIT));
  const vMid = toV(W(M.V)).lerp(out.vSit, 0.25);
  // cameras. b01 VOID_CU -> b02/b03 easing back for the hood top + the seed (yaw cheated so Jesus stays out of frame)
  out.VCU_A = EDGE.shot(EDGE.L(out.vEyes), { dist: 3.5, yaw: -30, pitch: -4, fov: 33, screenY: sy(385), drift: 0.2 });
  out.VCU_M = EDGE.shot(EDGE.L(out.vEyes), { dist: 4.6, yaw: -24, pitch: -3, fov: 33, screenY: sy(560), drift: 0.2 });
  out.VCU_B = EDGE.shot(EDGE.L(out.vEyes), { dist: 5.6, yaw: -19, pitch: -3, fov: 33, screenY: sy(690), drift: 0.2 });
  // b04-b05 wide: the master's angle, panned + pulled back so the whole Void (2.2 m wide) stays in frame through the
  // turn, the rise and the plop; user lower-left, Jesus centre
  const MS = EDGE.cam('MASTER', { drift: 0.2 });
  const jE = V3(...EDGE.W(-0.45, 1.55, -0.06));
  const vL = vMid.clone().add(V3(0, 1.2, 0)), vTop = vMid.clone().add(V3(0, 3.1, 0));
  // (lowered to ~1.35 m so the fat feet read under the lifting hem on each stomp)
  out.MASTER = fitShot([[jE, 315, 430, 0.6], [vL, 450, 560, 1], [vTop, 465, 170, 0.5], [out.uEyes, 135, 700, 0.6]], 44, MS.pos, MS.look, { posReg: 0.02, yMin: 1.2, yMax: 1.45, drift: 0.2 });
  out.MASTER_B = fitShot([[jE, 320, 440, 0.6], [out.vSit.clone().add(V3(0, 1.0, 0)), 510, 590, 1], [out.vSit.clone().add(V3(0, 2.4, 0)), 510, 360, 0.4], [out.uEyes, 140, 710, 0.6]], 44, MS.pos, MS.look, { posReg: 0.02, yMin: 1.2, yMax: 1.45, drift: 0.15 });
  // b06 the cut round: starts medium-wide (the big hand picking at the grass reads above the subtitle band), pushes in
  // to the face for "a lot". Camera a little above the eye line so the hood's lower lining stays tucked
  out.ROUND = EDGE.shot(EDGE.L(out.vEyesSit), { dist: 5.6, yaw: 128, pitch: -2, fov: 40, screenY: sy(300), drift: 0.2 });
  out.ROUND_B = EDGE.shot(EDGE.L(out.vEyesSit), { dist: 3.6, yaw: 124, pitch: -5, fov: 33, screenY: sy(380), drift: 0.15 });
  // b07: close 3/4 on the user looking off frame-right at the Void's back (the Void sits 3.3 m straight ahead of the
  // user, so no portrait frame holds both a readable face and its back: the face wins — the guilt flicker must read)
  out.LOST = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.55, yaw: 108, pitch: 4, fov: 33, screenY: sy(420), drift: 0.15 });
  out.LOST_B = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.42, yaw: 108, pitch: 4, fov: 33, screenY: sy(420), drift: 0.15 });
  // camera right vector for the huff shot (to place the seed / puffs)
  const c = toV(out.VCU_B.pos), l = toV(out.VCU_B.look), f = l.sub(c).normalize();
  out.camRight = V3(-f.z, 0, f.x).normalize();
  out.camFwd = V3(f.x, 0, f.z).normalize();
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const K = KT();
  if (t < K.b4 - 0.04) {      // close on the roll; eases back so the first puff is already in frame; then a bit more
    if (t < K.huffA + 0.25) return { ...mixShot(S.VCU_A, S.VCU_M, ramp(t, K.rollB - 0.25, K.huffA + 0.25, 'inOut')), vsk: 1.0 };
    return { ...mixShot(S.VCU_M, S.VCU_B, ramp(t, K.huffA + 0.25, K.huffB + 0.25, 'out')), vsk: 1.0 };
  }
  if (t < K.b6 - 0.03) return mixShot(S.MASTER, S.MASTER_B, ramp(t, K.plant[2], K.b6, 'inOut'));
  if (t < K.b7 - 0.12) return { ...mixShot(S.ROUND, S.ROUND_B, ramp(t, K.pushA, K.lot + 0.3, 'inOut')), sunGlow: 0.7 };
  return { ...mixShot(S.LOST, S.LOST_B, ramp(t, K.b7 - 0.12, T('s10.end'), 'linear')), sunGlow: 0.6, sunShift: -0.12 };
}

// ------------------------------------------------------------------------------------------------ the Void
/** turn-in-place progress: each stomp turns ~60 deg during its swing (the 0.45 s before its plant) */
function turnProg(t, K) {
  let s = 0;
  for (const p of K.plant) s += smooth(clamp((t - (p - 0.45)) / 0.45));
  return s / 3;
}
const mixFace = (a, b, w) => { const o = { ...a }; for (const key in b) { if (typeof b[key] === 'number') o[key] = lerp(typeof a[key] === 'number' ? a[key] : 0, b[key], w); } return o; };
function voidPose(t) {
  const K = KT();
  const y0 = WY(M.V), y1 = WY(M.VSIT);
  const tp = turnProg(t, K);
  const yaw = lerp(y0, y1, tp);
  const p0 = W(M.V), p1 = W(M.VSIT);
  const pos = [lerp(p0[0], p1[0], tp), 0, lerp(p0[2], p1[2], tp)];
  // ---- three fat-legged stomps: phase 0 (L plant) at plant[0], 0.5 (R) at plant[1], 1.0 (L) at plant[2]
  const wAmt = 0.95 * ramp(t, K.b4 + 0.0, K.b4 + 0.15) * (1 - ramp(t, K.plant[2], K.plant[2] + 0.22));
  const walk = { amount: wAmt, phase: (t - K.plant[0]) * 1.0, style: 'stomp' };
  let hem = 0, squash = 0, swing = 0;
  K.plant.forEach((p, i) => {
    hem = Math.max(hem, pulse(t, p - 0.38, 0.24, 0.14, 0.3));          // the hem lifts as the foot swings + plants
    squash += pulse(t, p - 0.01, 0.05, 0.03, 0.22);                    // the body drops onto the planted foot
    swing += (i % 2 ? -1 : 1) * pulse(t, p - 0.2, 0.2, 0.05, 0.4);     // the hem swings with the step
  });
  // ---- the eye roll (b01)
  const uRoll = ramp(t, K.rollA, K.rollB, 'linear');
  const er0 = eyeRoll(0, -1), er = eyeRoll(uRoll, -1);
  const roll = Math.sin(Math.PI * uRoll);
  // ---- huffs: puff up (anticipation) -> BLAST; the first wind-up starts only after the roll's end face has settled
  const puffUp = (a, d, amp = 1) => amp * (ramp(t, a - d, a - 0.02, 'out') * (1 - ramp(t, a - 0.02, a + 0.14, 'out')));
  const puff = Math.max(puffUp(K.huffA, K.huffA - (K.rollB + 0.06)), puffUp(K.huffB, 0.42), puffUp(K.huffC, 0.25, 0.4));
  const blast = (a) => pulse(t, a - 0.02, 0.05, 0.05, 0.35);
  const bl = Math.max(blast(K.huffA), blast(K.huffB), 0.5 * blast(K.huffC));
  // ---- plop (b05)
  const rise = pulse(t, K.b5 - 0.05, 0.13, 0.02, 0.1);
  const sit = ease3(clamp((t - K.sitA) / (K.contact - K.sitA)));
  const jig = wobble(t, K.contact, 2.3, 4.2);
  // ---- b06 picking at the grass, b07 deflate
  const pick = ramp(t, K.b6 + 0.15, K.b6 + 0.6) * (1 - ramp(t, K.b7 - 0.1, K.b7 + 0.5));
  const deflate = ramp(t, K.b7 + 0.1, K.b7 + 0.8);
  const cutR = ramp(t, K.b6 - 0.06, K.b6 - 0.03);                     // posture change hidden in the cut round
  const body = {
    sit,
    swell: 0.35 * puff - 0.12 * bl,
    shrug: 0.18 * puff + 0.12 * (1 - tp) * ramp(t, K.b4, K.b4 + 0.2) * (1 - ramp(t, K.plant[2], K.plant[2] + 0.4)) - 0.15 * deflate,
    stretch: 0.03 * rise - 0.07 * Math.max(0, jig) * (t > K.contact ? 1 : 0) - 0.035 * squash,
    bounce: 0.04 * rise - 0.03 * jig * (t > K.contact ? 1 : 0) - 0.03 * squash,
    // (from the cut round on: no forward lean and little slump — both tip the hood's lower brim up into a lit band under
    // the mouth for the front camera; the sadness is in the eyes and brows)
    lean: -0.06 * puff + 0.08 * bl + 0.04 * ramp(t, K.contact, K.contact + 0.5) * (1 - cutR),
    tilt: 0.04 * swing,
    slump: 0.22 * ramp(t, K.contact + 0.2, K.contact + 0.8) * (1 - 0.8 * cutR) + 0.25 * deflate,
    breathe: t < K.b4 ? 0.6 : 1,
  };
  // ---- head (the post-plop nod kept small: a deep nod opens the hood's lower lining to the cut-round camera)
  const headUp = ramp(t, K.b4 - 0.1, K.b4 + 0.3) * (1 - ramp(t, K.contact, K.contact + 0.35));
  const head = {
    pitch: -0.14 * (t < K.b4 ? 1 : 0) * (1 - ramp(t, K.rollA - 0.4, K.rollA)) - 0.13 * roll - 0.06 * puff + 0.05 * bl
      - 0.18 * headUp + 0.1 * ramp(t, K.contact + 0.05, K.contact + 0.6) * (1 - cutR) - 0.04 * cutR + 0.04 * deflate,
    yaw: 0.3 * headUp * (1 - tp * 0.5) + 0.18 * ramp(t, K.rollB, K.rollB + 0.3) * (1 - ramp(t, K.b4, K.b4 + 0.4)),
    roll: 0.07 * roll + 0.06 * headUp,
  };
  // ---- face
  const faceRoll = (tt) => {
    if (tt < K.rollA) {
      const pre = VX('scowl', { lidAngry: 1.55, lidU: 0.55, browIn: -1.0, mSmile: -0.95, mPress: 0.75 });   // (s09's clamp)
      const f = k(tt, [[K.rollA - 0.35, pre], [K.rollA, VX('annoyed', { ...er0, gazePitch: er0.gazePitch - 0.08, lidU: 0.5, mAsym: 0.45, mPress: 0.7, mSmile: -0.4 })]]);
      const a = ramp(tt, K.rollA - 0.35, K.rollA);
      f.gazeYaw = lerp(-0.04, er0.gazeYaw, a); f.gazePitch = lerp(-0.2, er0.gazePitch - 0.08, a);
      return f;
    }
    const e = eyeRoll(ramp(tt, K.rollA, K.rollB, 'linear'), -1);
    return VX('annoyed', { ...e, mAsym: 0.45, mPress: 0.7, mSmile: -0.4, lidU: e.lidU });
  };
  const faceHuff = () => {
    const base = VX('huff', { puff: 0, gazeYaw: 0.5, gazePitch: -0.08, lidU: 0.55, saccade: 0, autoBlink: 0 });
    const puffed = VX('huff', { puff: 1, gazeYaw: 0.5, gazePitch: 0.0, lidU: 0.4, lidL: 0.7, saccade: 0, autoBlink: 0 });
    const f = mixFace(base, puffed, puff);
    f.puff = puff;
    f.mOpen = Math.max(f.mOpen || 0, 0.25 * bl); f.mRound = Math.max(f.mRound || 0, 0.8 * bl);
    return f;
  };
  let face;
  const wH = ramp(t, K.rollB - 0.06, K.rollB + 0.24, 'inOut');         // the roll's end face melts into the huff base
  if (t < K.b4 + 0.05) {
    face = wH <= 0 ? faceRoll(t) : wH >= 1 ? faceHuff() : mixFace(faceRoll(Math.min(t, K.rollB)), faceHuff(), wH);
    face.autoBlink = 0; face.saccade = 0;
  } else if (t < K.b6 + 0.1) {         // the turn: "hmph" (eyes shut haughtily, chin up) -> plop
    face = k(t, [
      [K.b4, VX('annoyed', { gazeYaw: 0.5, lidU: 0.5, mAsym: 0.45, mPress: 0.75, autoBlink: 0 })],
      [K.b4 + 0.3, VX('annoyed', { lidU: 0.05, lidL: 0.3, browIn: -0.25, browSq: 0.5, mAsym: 0.4, mPress: 0.85, mSmile: -0.45, autoBlink: 0, saccade: 0 })],
      [K.contact - 0.02, VX('annoyed', { lidU: 0.05, lidL: 0.3, browIn: -0.25, browSq: 0.5, mAsym: 0.4, mPress: 0.85, mSmile: -0.45, autoBlink: 0, saccade: 0 })],
      [K.contact + 0.08, VX('flinch', { lidU: 0.9, mOpen: 0.06, mRound: 0.4, autoBlink: 0, saccade: 0 })],
      [K.contact + 0.45, VX('annoyed', { lidU: 0.45, gazePitch: -0.3, mPout: 0.25, mPress: 0.6, browIn: -0.15, autoBlink: 0, saccade: 0 })],
    ]);
  } else {                             // b06: the sulk melts into a sad pout (the side nobody sees); eyes on the picking finger
    face = k(t, [
      [K.b6 + 0.1, VX('annoyed', { lidU: 0.45, gazePitch: -0.3, mPout: 0.25, mPress: 0.6, browIn: -0.15, saccade: 0 })],
      [K.b6 + 1.0, VX('sad', { gazePitch: -0.36, gazeYaw: -0.1, lidU: 0.62, lidSad: 0.75, browIn: 1.0, browOut: -0.45, mPout: 0.12, mSmile: -0.75, mPress: 0.2, wet: 0.6, saccade: 0.2 })],
      [K.lot, VX('sad', { gazePitch: -0.4, gazeYaw: -0.12, lidU: 0.5, lidSad: 0.85, browIn: 1.1, browOut: -0.5, mPout: 0.18, mSmile: -0.85, mPress: 0.25, mTremble: 0.3, wet: 0.8, saccade: 0.2 })],
      [K.b7 + 0.6, VX('sad', { gazePitch: -0.42, lidU: 0.46, lidSad: 0.85, browIn: 1.0, browOut: -0.5, mPout: 0.12, mSmile: -0.8, mPress: 0.2, wet: 0.7 })],
    ]);
    face.autoBlink = 0;
    face.blink = Math.max(face.blink || 0, pulse(t, K.lot + 0.05, 0.16, 0.18, 0.3));   // a slow blink on "a lot"
  }
  // ---- arms: folded all along (body-relative); in b06 the RIGHT hand (toward the cut-round camera) drops to pick
  // at the grass beside its right foot, in plain view
  const fold = { mixL: 1, mixR: 1 };
  if (pick > 0.001) {
    const grass = groundPick(t, K, yaw, pos);
    const fp = [Math.sin(yaw) * 0.25 - Math.cos(yaw) * 0.55, -0.8, Math.cos(yaw) * 0.25 + Math.sin(yaw) * 0.55];
    const curl = 0.15 + 0.5 * pluck(t, K);
    fold.armR = (A) => {
      const fd = toV(A.fingers), tip0 = toV(A.target).addScaledVector(fd, 0.3);
      return { preset: 'tip', from: 'crossed', mix: pick, reach: 1, at: 'tip', target: tip0.lerp(grass, pick),
        fingers: fd.lerp(toV(fp).normalize(), pick).normalize().toArray(), palm: toV(A.palm).lerp(V3(0, -1, 0), pick).normalize().toArray(),
        pole: toV(A.pole).lerp(V3(-Math.cos(yaw), -0.3, Math.sin(yaw)).normalize(), pick).normalize().toArray(),
        handScale: 0.8, hand: { point: pick, curl: lerp(0.42, curl, pick), thumb: 0.3, spread: 0.06, cup: 0.3 } };
    };
  }
  const extra = { motes: t > K.contact - 0.1 && t < K.contact + 0.5 ? 0 : 1, stars: t > K.b6 ? 0.8 : 1, hem: hem };
  return { pos, yaw, walk, body, head, face, armL: { preset: 'crossed' }, armR: { preset: 'crossed' }, fold, extra, blinkAt: [] };
}
function ease3(u) { return u * u * (1.6 - 0.6 * u); }   // accelerate into the plop (gravity), no slow-down
/** 0..1 plucks: the finger hooks a blade (curl), tugs it up, lets go — held ~0.8 s before the push-in, then slower */
function pluck(t, K) {
  const a = K.b6 + 0.55;
  if (t < a) return 0;
  const ph = ((t - a) * 1.25) % 1;
  return smooth(ph / 0.35) * (1 - smooth((ph - 0.6) / 0.3));
}
function groundPick(t, K, yaw, pos) {
  // grass just outside its RIGHT foot, toward the cut-round camera: hand + finger in plain view
  const f = V3(Math.sin(yaw), 0, Math.cos(yaw)), r = V3(-Math.cos(yaw), 0, Math.sin(yaw));
  const pl = pluck(t, K);
  return toV(pos).addScaledVector(f, 1.22).addScaledVector(r, 0.98).add(V3(0, 0.03 + 0.07 * pl, 0)).addScaledVector(f, -0.03 * pl);
}
function voidGazeOf(t, user) {
  const K = KT();
  if (t < K.rollA - 0.35) return user.anchor('eyes');     // still glaring at the user (from s09)
  return null;                                             // then: face params (roll, pointed look away, downcast)
}

// ------------------------------------------------------------------------------------------------ particles
/**
 * Kettle-steam nebula puffs out of the hood rim: a violet cloud body (normal blend, light enough to read against the
 * lilac sky), a glowing violet/teal core (additive) and a few twinkling star specks. Slow rise (<= ~0.35 m in the first
 * 0.5 s, ~0.6 m in all), spreading as they go, so the plume stays below the phone UI band.
 */
function puffP(i, seed, amp, age) {
  const h1 = hash1(seed * 31 + i), h2 = hash1(seed * 17 + i * 3), h3 = hash1(seed * 7 + i * 11);
  const v0 = (0.72 + 0.25 * h2) * amp, kk = 2.8;
  const rise = v0 * (1 - Math.exp(-age * kk)) / kk + 0.035 * age;
  const side = (h3 - 0.5) * 0.55 * amp * (1 - Math.exp(-age * 1.8));
  // born just above the top of the hood, on the camera side of the peak (so the hood doesn't hide the first wisps)
  const p = S.hoodTop.clone().addScaledVector(S.camFwd, -0.16).add(V3(0, 0.1 + rise, 0)).addScaledVector(S.camRight, side);
  return { p, h1, h2, h3, rise };
}
function huffPuffs(t, ps, fx) {
  const K = KT();
  const blasts = [[K.huffA, 1, 11], [K.huffB, 1.25, 23], [K.huffC, 0.55, 37]];
  if (t > K.b4 - 0.04) return;           // the wide would only show the last wisps in the phone-UI band: gone at the cut
  for (const [a, amp, seed] of blasts) {
    if (t < a - 0.02 || t > a + 2.4) continue;
    const n = Math.round(3 + 2 * amp);
    for (let i = 0; i < n; i++) {
      const age = t - (a + 0.04 * i);
      if (age < 0) continue;
      const q = puffP(i, seed, amp, age);
      const life = 1.7 + 0.6 * q.h1;
      if (age > life) continue;
      const u = age / life;
      const size = (0.22 + 0.62 * amp * Math.sqrt(u)) * (0.8 + 0.4 * q.h1);
      const fade = smooth(u / 0.08) * (1 - smooth((u - 0.35) / 0.65));
      ps.add(q.p.toArray(), size, i % 2 ? 0x8a4fd0 : 0x7446c4, 0.62 * fade, q.h1 * 6.28 + age * 0.4 * (q.h2 - 0.5), CELL.puff);
      fx.add(q.p.toArray(), size * 0.6, i % 2 ? 0xc68cff : 0x4fd8e6, 0.6 * fade, q.h2 * 6.28 - age * 0.3, CELL.nebula);   // glowing violet/teal core
      if (i < 3) {                                                    // star specks inside the cloud
        const sp = q.p.clone().addScaledVector(S.camRight, (q.h2 - 0.5) * size * 0.6).add(V3(0, (q.h1 - 0.5) * size * 0.4, 0)).addScaledVector(S.camFwd, -0.1);
        const tw = 0.75 + 0.25 * Math.sin(age * 9 + i * 2);
        fx.add(sp.toArray(), 0.1 + 0.035 * q.h3, 0xfff6e0, fade * tw, q.h2 * 6, CELL.star);
      }
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
/** the thought-seed drifts in and hangs right in the second huff's path, ~0.4 m over the hood; the puff front shoves it
 *  up and away out of frame */
function seedState(t) {
  const K = KT();
  const t0 = K.huffA - 0.5, hang = K.huffA + 0.25;
  const hit = K.huffB + 0.28;                                  // the 2nd puff's front (centre + half its size) arrives
  if (t < t0 || t > hit + 1.4 || t > K.b4) return { p: V3(), a: 0, rot: 0 };
  const R = S.camRight;
  const spot = S.hoodTop.clone().addScaledVector(S.camFwd, -0.16).add(V3(0, 0.42, 0)).addScaledVector(R, 0.06);
  const u = smooth(clamp((t - t0) / (hang - t0)));
  const p = spot.clone().addScaledVector(R, 0.75 * (1 - u)).add(V3(0, 0.12 * (1 - u) + 0.025 * Math.sin(t * 1.9), 0));
  let rot = 0.15 * Math.sin(t * 1.3);
  if (t > hit) {
    const d = t - hit, e = (1 - Math.exp(-d * 2.4)) / 2.4;
    p.addScaledVector(R, -1.1 * e).add(V3(0, 2.6 * e + 0.4 * d, 0));       // shoved up and away (out the top-left)
    rot += d * 6;
  }
  return { p, a: smooth((t - t0) / 0.35), rot };
}
/** the single star mote that slides down from beside the eye like a tear (b06, on "hears") */
function tearState(t) {
  const K = KT();
  const t0 = K.hears - 0.1;
  if (t < t0 || t > K.b7 - 0.12) return { p: V3(), a: 0, s: 1 };
  const d = t - t0;
  const e = S.vEyesSit;
  const toCam = toV(S.ROUND.pos).sub(e).setY(0).normalize();
  const side = V3(-toCam.z, 0, toCam.x);
  const p = e.clone().addScaledVector(toCam, 0.32).addScaledVector(side, -0.16).add(V3(0, -0.12 - 0.11 * d - 0.02 * d * d, 0));
  return { p, a: 0.95 * smooth(d / 0.3) * (1 - smooth((d - 1.6) / 0.7)), s: 1 + 0.15 * Math.sin(d * 5) };
}

// ------------------------------------------------------------------------------------------------ the user
function userPose(t, statOnly = false) {
  const K = KT();
  const phoneA = K.b7 + 0.5, phoneT = K.b7 + 0.62;
  let gaze = null;
  if (S && !statOnly && t < phoneA) {
    const back = S.vBackSit.clone().add(V3(0, 0.55 - 0.3 * ramp(t, K.contact - 0.2, K.contact + 0.3), 0));
    gaze = t < K.b4 + 0.7 ? S.vEyes : back;           // the Void's face -> as it turns, its back
    if (t > K.b4 + 0.55 && t < K.b4 + 0.85) gaze = S.vEyes.clone().lerp(back, smooth((t - K.b4 - 0.55) / 0.3));
  }
  const flinch = K.plant.reduce((m, p) => Math.max(m, pulse(t, p + 0.02, 0.06, 0.02, 0.18)), 0) + 0.8 * pulse(t, K.contact + 0.02, 0.06, 0.03, 0.22);
  const phoneUp = ramp(t, phoneA, phoneA + 0.35);
  const ta = userTurnAway(t);                                       // s09's huffy look-away easing back (offscreen)
  const P = {
    pos: userPos(t), yaw: WY(M.U), gaze,
    body: { sit: 1, sitPath: 'plain', hunch: 0.18 + 0.1 * phoneUp, shrug: 0.12, tremble: 0.15, flinch: 0.45 * flinch, lookBack: ta.lookBack },
    armL: { preset: 'crossed', tremble: 0.1 },
    armR: { preset: 'crossed', tremble: 0.1 },
    head: { follow: 0.4 * (1 - ta.chin), pitch: -0.12 * (1 - phoneUp) - 0.14 * ta.chin + 0.2 * phoneUp },
    extra: { phone: lerp(0.85, 0.4, phoneUp), phoneUp: 0.72 * phoneUp, screen: 'feed', scroll: Math.max(0, t - phoneT) * 0.6 },
  };
  if (!statOnly && phoneUp > 0.3) P.screenGaze = true;              // eyes on the screen (second pass in update)
  if (t > phoneA + 0.2) { P.extra.thumb = 1; P.extra.tap = pulse(t, K.b7 + 0.8, 0.06, 0.03, 0.1); }   // one "checking" tap
  P.face = k(t, [
    ['s10', UX('pout', { lidU: 0.66, mPout: 1.1 })],
    [K.b4 + 0.1, UX('pout', { lidU: 0.75, mPout: 0.9 })],
    [K.b4 + 0.6, UX('suspicious', { lidU: 0.92, browIn: 0.1, mPout: 0.4 })],          // the brows lift a fraction
    [K.contact + 0.3, UX('disbelief', { lidU: 0.85, mPout: 0.3 })],
    [K.b7 + 0.12, UX('pout', { lidU: 0.8, mPout: 0.6 })],
    [K.b7 + 0.17, UX('guilt', { browIn: 0.85, mPout: 0, mPress: 0.1 })],              // six frames of guilt
    [K.b7 + 0.42, UX('guilt', { browIn: 0.8, mPout: 0, mPress: 0.1 })],
    [K.b7 + 0.52, UX('hellno', { mPress: 0.8, lidU: 0.7 })],                            // jaw sets, eyes slide away
    [phoneT + 0.15, UX('scroll', { mPress: 0.5 })],                                    // pretend to check the phone
  ]);
  if (t > K.b7 + 0.5 && t < phoneA + 0.1) P.face.gazeYaw = -0.35 * smooth((t - K.b7 - 0.5) / 0.08);   // eyes slide away
  P.blinkAt = [K.contact + 0.12, K.b7 + 0.47];
  return P;
}

// ------------------------------------------------------------------------------------------------ Jesus
function jesusPose(t, user, vd) {
  const K = KT();
  const vEye = vd.anchor('eyes').add(V3(0, -0.25, 0)), vBack = vd.anchor('back');
  const target = t < K.contact ? vEye : vBack.clone().add(V3(0, 0.3, 0));
  const gaze = t < K.b7 + 0.6 ? target : gazeSched(t, [['s10', target], [K.b7 + 0.6, () => user.anchor('eyes'), 0.1]]);
  const pos = W(M.JM), yaw = WY(M.JM);
  const aim = headAim(pos, yaw, gaze, { fy: 0.6, fp: 0.45, up: 0.18, down: 0.25 });
  const bounce = pulse(t, K.contact + 0.04, 0.07, 0.05, 0.25);
  const face = k(t, [
    ['s10', JX('pressed', { mSmile: 0.05, mPress: 0.95, browIn: 0.92, browOut: 0.8, lidU: 1.16 })],
    [K.b4 + 0.3, JX('oh', { mOpen: 0.13, mRound: 0.35, browIn: 0.6, browOut: 0.55, lidU: 1.18 })],    // mouth slightly open
    [K.contact + 0.5, JX('oh', { mOpen: 0.08, mRound: 0.3, browIn: 0.55, browOut: 0.5, lidU: 1.05 })],
    [K.b7, JX('concerned', { mPress: 0.5, browIn: 0.55 })],
  ]);
  face.browIn += 0.35 * bounce; face.browOut += 0.4 * bounce; face.lidU += 0.1 * bounce;
  return {
    pos, yaw, face, gaze,
    head: { yaw: aim.yaw, pitch: aim.pitch, roll: 0.03, follow: 0 },
    body: { shrug: 0.1, recoil: 0.04 * bounce },
    armL: { preset: [['clasp', 0.7], ['clasp_chest', 0.3]] },
    armR: { preset: [['clasp', 0.7], ['clasp_chest', 0.3]] },
    blinkAt: [K.b4 + 0.05, K.contact + 0.25],
  };
}
