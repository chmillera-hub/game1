// s09 hell_no — refusal as armour. The user's fear comes out as sarcasm, their body ends up mirroring the Void's
// exactly, and on "scary" the Void's mask slips for 8 frames (the frozen mote finally falls).
//   b01 USER_CU (phone glow on the chin): slow blink; eyes Jesus -> up to the Void's scowl -> Jesus; mouth opens,
//       closes; jaw sets.
//   b02 hold: "Hell no." sharp head shake on "no" (hair swings), brows crushed, lips pressed after.
//   b03 MASTER: "I'm not talking to that scary thing." jab the phone screen-first on "that" (trembling), the Void's
//       mask slip on "scary" (+ the mote drops), arms snap crossed on "thing", chin up, 5 cm scoot back. Jesus's eyes
//       close slowly on "scary", open; his head turns to the Void.
//   b04 MASTER (push to the symmetrical read): two crossed-arm scowls; Jesus between, eyes user -> Void -> user ->
//       Void, eyes first, head follows, brows climbing each time.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, galaxyAt, galaxySpin, sy } from './marks.js';
import { JX } from '../chars/jesus.js';
import { UX, headShake } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, fitShot, mixShot, W, WY, faceYaw, MARKS as M, starSprite } from './armour_shared.js';
import { voidArmour, moteState, galaxyFloor, userSeated, userPos, sceneLook, moteFreezeT, scaryT } from './armour_common.js';

let S = null;

export default {
  id: 's09',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const st = { scene: set.scene, set, jesus, vd, user };
    st.fx = new Particles({ max: 24 }); set.scene.add(st.fx.mesh);
    st.mote = starSprite(0xfff2d0, 0.2); set.scene.add(st.mote);
    st.floorGal = galaxyFloor(st.fx); set.scene.add(st.floorGal.mesh);
    S = st.S = statics(st);
    return st;
  },
  async update(t, app, st) {
    const { set, jesus, vd, user } = st;
    st.scene.add(jesus.root, vd.root, user.root, st.fx.mesh, st.mote, st.floorGal.mesh);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 9);
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (shot.vsk ?? 1), voidPos: W(M.V), sunShift: shot.sunShift ?? 0, sunGlow: shot.sunGlow ?? 1 });

    user.update(t, userPose(t));
    vd.update(t, voidArmour(t, { gaze: voidGaze(t, user) }));
    jesus.update(t, jesusPose(t, user, vd));

    st.fx.begin();
    const g = galaxyAt(t);
    if (g) st.fx.add(g, EDGE.GALAXY.size, 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
    st.fx.end();
    const ms = moteState(t, S.MOTE);
    st.mote.visible = ms.a > 0.01;
    st.mote.position.copy(ms.p); st.mote.material.opacity = ms.a; st.mote.scale.setScalar(0.2 * ms.s);
    st.floorGal.update(t);
    st.look = sceneLook('s09', set.look, t);
  },
};

// ------------------------------------------------------------------------------------------------ statics
const jYawEnd = () => WY(M.JM);                                  // facing camera, between them (s09b04 -> s11)
const jYawTalk = () => faceYaw(W(M.JM), W(M.U)) + 0.12;          // facing the user (as s08 ended)
function statics(st) {
  const { vd, user } = st;
  const out = {};
  const jm = W(M.JM);
  out.jEyes = V3(jm[0] + Math.sin(jYawTalk()) * 0.14, 1.55, jm[2] + Math.cos(jYawTalk()) * 0.14);
  const t0 = T('s09b01');
  user.update(t0, userSeated(t0, { gaze: out.jEyes }));
  out.uEyes = user.anchor('eyes'); out.uHandR = user.anchor('handR');
  vd.update(t0, voidArmour(t0, { gaze: out.uEyes }));
  out.vEyes = vd.anchor('eyes');
  // the frozen mote (same construction as s08)
  const tf = moteFreezeT();
  vd.update(tf, voidArmour(tf, { gaze: out.uEyes }));
  const vy = WY(M.V), vl = V3(Math.cos(vy), 0, -Math.sin(vy)), vf = V3(Math.sin(vy), 0, Math.cos(vy));
  out.MOTE = { p: vd.anchor('shoulderL').addScaledVector(vl, -0.1).addScaledVector(vf, 0.75).add(V3(0, 0.34, 0)), tf };
  // cameras
  out.UCU_A = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.6, yaw: 124, pitch: 3, fov: 33, screenY: sy(430), drift: 0.25 });
  out.UCU_B = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.42, yaw: 122, pitch: 3, fov: 33, screenY: sy(425), drift: 0.25 });
  out.MASTER = EDGE.cam('MASTER', { drift: 0.25 });
  // b04: push in to the symmetrical three-shot (Jesus dead centre, the two scowls at the diagonal corners)
  const jEnd = V3(jm[0] + Math.sin(jYawEnd()) * 0.14, 1.55, jm[2] + Math.cos(jYawEnd()) * 0.14);
  out.MASTER2 = fitShot([[jEnd, 360, 470], [out.vEyes, 590, 255, 0.7], [out.uEyes, 130, 760, 0.5]], 34, out.MASTER.pos, out.MASTER.look, { posReg: 0.02, drift: 0.15 });
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const cut = T('s09b03') - 0.08;
  if (t < cut) return { ...mixShot(S.UCU_A, S.UCU_B, ramp(t, T('s09'), cut, 'inOut')), sunShift: 0.08, sunGlow: 0.7 };
  return mixShot(S.MASTER, S.MASTER2, ramp(t, T('s09b03') + 1.0, T('s09.end'), 'inOut'));
}

// ------------------------------------------------------------------------------------------------ the user
function userPose(t) {
  const b1 = T('s09b01'), b2 = T('s09b02'), b3 = T('s09b03'), b4 = T('s09b04');
  const no = wordT('s09b02', 'no', { fallback: 0.3 });
  const that = wordT('s09b03', 'that', { fallback: 0.45 });
  const scary = scaryT();
  const thing = wordT('s09b03', 'thing', { fallback: 0.7 });
  const jE = S.jEyes, vE = S.vEyes;
  const gk = [
    ['s09', jE],
    [b1 + 0.62, vE, 0.14],                 // eyes slide up to the Void's scowl
    [b1 + 1.05, jE, 0.1],                  // back to Jesus
    [b3 + 0.15, vE, 0.1],                  // "I'm not talking to THAT..." — at the Void
  ];
  const gaze = gazeSched(t, gk);
  const P = userSeated(t, { gaze });
  // ---- head: shake on "no", chin up on "thing"; head turns a little toward the Void for the jab
  const hs = headShake(t, no - 0.06, { count: 2.5, dur: 0.62, amp: 0.3 });
  const chinUp = ramp(t, thing, thing + 0.22, 'out');
  P.head = { look: gazeSched(t - 0.1, gk.map(([a, b]) => [a, b, 0.3])), follow: 0.35, yaw: hs.yaw, pitch: -0.13 * chinUp + 0.05 * pulse(t, b2 - 0.05, 0.1, 0.1, 0.25) };
  P.extra.hairSwing = hs.hairSwing;
  // ---- arms: right hand still up (defend) -> sinks as the phone jabs on "that" -> both arms snap crossed on "thing"
  const jab = ramp(t, that - 0.14, that + 0.06, 'out') * (1 - ramp(t, thing - 0.06, thing + 0.16));
  const cross = ramp(t, thing - 0.06, thing + 0.16, 'out');
  const rDown = 0.55 * ramp(t, b1 + 0.15, b1 + 1.0) + 0.45 * ramp(t, that - 0.1, that + 0.25);
  P.armL = { preset: [['hold', (1 - jab) * (1 - cross) + 1e-4], ['jab', jab], ['crossed', cross]], tremble: 0.7 * jab + 0.15 * cross };
  P.armR = { preset: [['defend', (1 - rDown) * (1 - cross) + 1e-4], ['knee', rDown * (1 - cross)], ['crossed', cross]], tremble: 0.35 * (1 - rDown) + 0.15 * cross };
  // ---- body
  const jabLean = pulse(t, that - 0.14, 0.18, 0.12, 0.3);
  P.body = { ...P.body,
    lean: 0.14 * jabLean - 0.06 * cross + 0.06 * pulse(t, b2 + 0.0, 0.08, 0.15, 0.3),
    recoil: 0.1 * pulse(t, thing + 0.02, 0.1, 0.05, 0.4),
    scoot: pulse(t, thing + 0.02, 0.08, 0.12, 0.12), scootPhase: (t - thing) * 1.6,
    tremble: 0.12 + 0.25 * jab + 0.18 * ramp(t, b4, b4 + 0.4),
    hunch: 0.3 - 0.12 * chinUp,
    flinch: 0.4 * pulse(t, b1 + 0.62, 0.1, 0.05, 0.3),
  };
  // ---- face
  P.face = k(t, [
    ['s09', UX('gulp', { lidU: 1.08 })],
    [b1 + 0.12, UX('gulp', { lidU: 1.0, blink: 0 })],
    [b1 + 0.28, UX('gulp', { lidU: 0.35 })],                                  // one slow blink (lids)
    [b1 + 0.55, UX('gulp', { lidU: 1.12 })],
    [b1 + 0.75, UX('scared', { lidU: 1.22, mOpen: 0.06 })],                    // the scowl up there
    [b1 + 1.1, UX('disbelief', { lidU: 0.9 })],
    [b1 + 1.2, UX('disbelief', { mOpen: 0.22, lidU: 0.9 })],                  // mouth opens...
    [b1 + 1.38, UX('suspicious', { mOpen: 0.0, mPress: 0.6 })],               // ...closes
    [b2 - 0.08, UX('hellno', { mPress: 0.6, lidU: 0.7 })],                     // jaw sets
    [b2 + 0.35, UX('hellno')],
    [b2 + 0.62, UX('hellno', { mPress: 1, mPout: 0.3 })],                      // lips pressed tight after
    [b3 - 0.05, UX('glare', { mPress: 0.3, lidU: 0.72 })],
    [that, UX('glare', { mPress: 0.2, lidU: 0.85, browIn: -0.6 })],
    [scary - 0.02, UX('scared', { lidU: 1.18, browIn: 0.7, mTremble: 0.5, mOpen: 0.1 })],   // the wobble gives it away
    [scary + 0.2, UX('scared', { lidU: 1.1, browIn: 0.55, mTremble: 0.4 })],
    [thing + 0.08, UX('pout', { lidU: 0.72, browIn: -0.5 })],
    [b4 + 0.2, UX('pout', { lidU: 0.66, mPout: 1.1 })],
  ]);
  P.face.autoBlink = t < b1 + 0.6 ? 0 : 1;
  P.blinkAt = [b2 + 0.7, thing + 0.3, b4 + 0.9];
  return P;
}

// ------------------------------------------------------------------------------------------------ the Void
function voidGaze(t, user) {
  return user.anchor('eyes');                                    // locked on the user (their scowl back at it)
}

// ------------------------------------------------------------------------------------------------ Jesus
function jesusPose(t, user, vd) {
  const b3 = T('s09b03'), b4 = T('s09b04');
  const scary = scaryT();
  const uE = user.anchor('eyes'), vE = vd.anchor('eyes');
  // eyes lead, head follows: user -> (scary) Void -> b04: user -> Void -> user -> Void
  const gk = [
    ['s09', uE],
    [scary + 0.55, vE, 0.12],
    [b4 + 0.1, uE, 0.09],
    [b4 + 0.55, vE, 0.09],
    [b4 + 1.0, uE, 0.09],
    [b4 + 1.42, vE, 0.09],
  ];
  const gaze = gazeSched(t, gk);
  const look = gazeSched(t - 0.1, gk.map(([a, b]) => [a, b, 0.28]));
  const turn = ramp(t, scary + 0.5, b4 + 0.2);                   // body squares up to camera, between them
  const yaw = lerp(jYawTalk(), jYawEnd(), turn);
  const shut = pulse(t, scary + 0.04, 0.22, 0.12, 0.3);          // eyes close slowly... open: ah.
  const face = k(t, [
    ['s09', JX('hopeful', { mOpen: 0, mTeethU: 0, browIn: 0.6, browOut: 0.5, lidU: 1.06 })],
    [T('s09b02') + 0.2, JX('oh', { mOpen: 0.05, browIn: 0.55, browOut: 0.5 })],            // (off) "Hell no."
    [b3 - 0.1, JX('concerned', { mPress: 0.3, browIn: 0.5 })],
    [scary, JX('compassion', { mPress: 0.45, browIn: 0.7 })],
    [scary + 0.6, JX('concerned', { mPress: 0.6, browIn: 0.6 })],
    [b4 + 0.1, JX('pressed', { mSmile: 0.05, mPress: 0.85, browIn: 0.45, browOut: 0.35, lidU: 1.0 })],
    [b4 + 0.55, JX('pressed', { mSmile: 0.05, mPress: 0.9, browIn: 0.62, browOut: 0.5, lidU: 1.06 })],
    [b4 + 1.0, JX('pressed', { mSmile: 0.05, mPress: 0.95, browIn: 0.8, browOut: 0.68, lidU: 1.12 })],
    [b4 + 1.42, JX('pressed', { mSmile: 0.05, mPress: 0.95, browIn: 0.92, browOut: 0.8, lidU: 1.16 })],
  ]);
  face.blink = shut; face.autoBlink = shut > 0 ? 0 : 1;
  return {
    pos: W(M.JM), yaw, face, gaze,
    head: { look, follow: 0.6, pitch: 0.04 * shut, roll: 0.1 * (1 - turn) },
    body: { lean: 0.02 * (1 - turn), shrug: 0.12 * ramp(t, b4, b4 + 1.4) },
    armL: { preset: [['clasp', 0.4 + 0.3 * turn], ['clasp_chest', 0.6 - 0.3 * turn]] },
    armR: { preset: [['clasp', 0.4 + 0.3 * turn], ['clasp_chest', 0.6 - 0.3 * turn]] },
    blinkAt: [b4 + 0.07, b4 + 0.98],
  };
}
