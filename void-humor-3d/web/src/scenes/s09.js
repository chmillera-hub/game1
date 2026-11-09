// s09 hell_no — refusal as armour. The user's fear comes out as sarcasm, their body ends up mirroring the Void's
// exactly, and on "scary" the Void's mask slips for 8 frames (the frozen mote finally falls).
//   b01 USER_CU (phone glow on the chin; the raised RIGHT hand still up beside the face, trembling): slow blink; eyes
//       Jesus -> up to the Void's scowl -> Jesus; mouth opens, closes; jaw sets.
//   b02 hold: "Hell no." sharp head shake on "no" (hair swings), brows crushed, lips pressed after.
//   b03 split: USER_CU through "I'm not talking to that" — on "that" the phone jabs out at the Void screen-first,
//       trembling (frame-right), the raised hand drops; the wobble lands on the face at the start of "scary".
//       CUT to the three-shot on "scary": the Void's two fast blinks, its 8-frame hurt, the mote drops and winks out,
//       the scowl clamps back harder; on "thing" the user's arms snap crossed, chin up, a huffy turn-away (head and
//       chest cheated toward camera so the pout and the folded arms read in profile), a 2.5 cm scoot. Jesus's eyes
//       close slowly, open; his head turns to the Void; his body squares up to camera.
//   b04 the three-shot pushes to the symmetrical read: two crossed-arm scowls; Jesus between, eyes user -> Void ->
//       user -> Void, eyes first, head follows, lips pressed, brows climbing each time.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, galaxyAt, galaxySpin, sy } from './marks.js';
import { JX } from '../chars/jesus.js';
import { UX, headShake } from '../chars/user.js';
import { scopeVisible, ensureLittleGalaxy } from './edgeprops.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, fitShot, mixShot, W, WY, faceYaw, MARKS as M, starSprite, headAim } from './armour_shared.js';
import { voidArmour, moteState, userSeated, sceneLook, computeMote, scaryT, scaryCutT, slipT, updateVoid, defendRef, userTurnAway, assertLipsync } from './armour_common.js';

let S = null;

export default {
  id: 's09',
  async setup(app) {
    await loadWords();
    assertLipsync('s09');
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const st = { scene: set.scene, set, jesus, vd, user };
    st.fx = new Particles({ max: 24 }); set.scene.add(st.fx.mesh);
    st.mote = starSprite(0xfff2d0, 0.2); set.scene.add(st.mote);
    ensureLittleGalaxy(set);                                       // the shared little galaxy by the sneaker (edgeprops)
    for (const o of [st.fx.mesh, st.mote]) scopeVisible(o, 's09', 's10');
    S = st.S = statics(st);
    return st;
  },
  async update(t, app, st) {
    const { set, jesus, vd, user } = st;
    st.scene.add(jesus.root, vd.root, user.root, st.fx.mesh, st.mote);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 9);
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (shot.vsk ?? 1), voidPos: W(M.V), sunShift: shot.sunShift ?? 0, sunGlow: shot.sunGlow ?? 1 });

    user.update(t, userPose(t));
    updateVoid(vd, t, voidArmour(t, { gaze: user.anchor('eyes') }));
    jesus.update(t, jesusPose(t, user, vd));

    st.fx.begin();
    const g = galaxyAt(t);
    if (g) st.fx.add(g, EDGE.GALAXY.size, 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
    st.fx.end();
    const ms = moteState(t, S.MOTE);
    st.mote.visible = ms.a > 0.01;
    st.mote.position.copy(ms.p); st.mote.material.opacity = ms.a; st.mote.scale.setScalar(0.2 * ms.s);
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
  out.R = defendRef(user, T('s08b05'));
  const t0 = T('s09b01');
  user.update(t0, userSeated(t0, { gaze: out.jEyes, R: out.R }));
  out.uEyes = user.anchor('eyes'); out.uShL = user.anchor('shoulderL');
  vd.update(t0, voidArmour(t0, { gaze: out.uEyes }));
  out.vEyes = vd.anchor('eyes');
  out.MOTE = computeMote(vd, out.uEyes);                         // same point as s08
  // the jab: out at the Void, screen first, a little up (a flashlight at a monster)
  out.jab = out.uShL.clone().lerp(out.vEyes, 0.0).add(out.vEyes.clone().sub(out.uShL).setY(0).normalize().multiplyScalar(0.42)).add(V3(0, 0.2, 0));
  // world wrists for the arm transitions (snapshots of the rig's own presets at the moments the blends meet them)
  S = out;
  const that = wordT('s09b03', 'that', { fallback: 0.45 }), thing = wordT('s09b03', 'thing', { fallback: 0.7 });
  const wr = (side) => user.root.localToWorld(user.arms[side].wrist.clone());
  user.update(that - 0.15, userPose(that - 0.15)); const holdL = wr('L');
  user.update(thing + 0.17, userPose(thing + 0.17)); const crossL = wr('L'), crossR = wr('R');
  const uy = WY(M.U);
  out.W = { holdL, crossL, crossR, inward: V3(-Math.sin(uy), -0.3, -Math.cos(uy)).normalize() };
  // cameras: USER_CU (room for the raised hand at frame-left and the phone jabbing in at frame-right)
  out.UCU_A = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.95, yaw: 122, pitch: 3, fov: 33, screenY: sy(400), drift: 0.2 });
  out.UCU_B = EDGE.shot(EDGE.L(out.uEyes), { dist: 1.72, yaw: 120, pitch: 3, fov: 33, screenY: sy(405), drift: 0.2 });
  // the three-shot from the master side (user lower-left, Jesus centre, the Void upper-right), pushing in through b04
  const jEnd = V3(jm[0] + Math.sin(jYawEnd()) * 0.14, 1.55, jm[2] + Math.cos(jYawEnd()) * 0.14);
  // (from the OTS side: over the user's right shoulder, so the huffy look-away over that shoulder turns the user's
  // face toward us; stacked in depth: user lower-left, Jesus centre, the Void upper-right)
  const OT = EDGE.cam('OTS', { drift: 0.2 });
  out.THREE_A = fitShot([[jEnd, 340, 445], [out.vEyes, 560, 235, 0.7], [out.uEyes, 150, 700, 0.8]], 42, OT.pos, OT.look, { posReg: 0.03, yMin: 1.4, yMax: 2.3, drift: 0.2 });
  out.THREE_B = fitShot([[jEnd, 350, 455], [out.vEyes, 585, 225, 0.7], [out.uEyes, 140, 730, 0.8]], 38, OT.pos, OT.look, { posReg: 0.03, yMin: 1.4, yMax: 2.3, drift: 0.12 });
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const cut = scaryCutT();
  if (t < cut) return { ...mixShot(S.UCU_A, S.UCU_B, ramp(t, T('s09'), cut, 'inOut')), sunShift: -0.12, sunGlow: 0.6 };
  return mixShot(S.THREE_A, S.THREE_B, ramp(t, T('s09b03.end') - 0.2, T('s09.end'), 'inOut'));
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
  const P = userSeated(t, { gaze, R: S.R });
  // ---- head: shake on "no", chin up + the huffy turn-away on "thing"
  const hs = headShake(t, no - 0.06, { count: 2.5, dur: 0.62, amp: 0.3 });
  const ta = userTurnAway(t);
  const look = gazeSched(t - 0.1, gk.map(([a, b]) => [a, b, 0.3]));
  P.head = { look, follow: 0.35 * (1 - ta.chin), yaw: hs.yaw, pitch: -0.16 * ta.chin + 0.05 * pulse(t, b2 - 0.05, 0.1, 0.1, 0.25) };
  P.extra.hairSwing = hs.hairSwing;
  // after the turn the eyes slide back to the Void (side-eye from the turned head)
  if (ta.chin > 0) P.gaze = vE;
  // ---- arms: right hand still up (defend, trembling) -> it drops as the phone jabs on "that" -> both arms snap
  // crossed on "thing" (every in-between is in motion, nothing half-blended is held on screen)
  const jabU = ramp(t, that - 0.14, that + 0.06, 'out');
  const cross = ramp(t, thing - 0.06, thing + 0.16, 'out');
  const jab = jabU * (1 - cross);
  const rX = ramp(t, that - 0.05, thing + 0.16, 'inOut');
  const snap = !S.W;                                              // setup snapshots: presets only
  if (snap) P.armL = { preset: cross >= 1 ? 'crossed' : 'hold' };
  else if (t < that - 0.14) P.armL = { preset: 'hold' };
  else if (cross >= 1) P.armL = { preset: 'crossed', tremble: 0.15 };
  else P.armL = { preset: [['hold', (1 - jabU) * (1 - cross) + 1e-4], ['jab', jab], ['crossed', cross]], tremble: 0.7 * jab + 0.15 * cross,
    target: S.W.holdL.clone().lerp(S.jab, jabU).lerp(S.W.crossL, cross), reach: 1 };
  const dA = P.armR;
  if (snap) P.armR = rX >= 1 ? { preset: 'crossed' } : dA;
  else if (rX >= 1) P.armR = { preset: 'crossed', tremble: 0.15 };
  else if (rX > 0) P.armR = { preset: [['defend', 1 - rX + 1e-4], ['crossed', rX]], tremble: 0.3 * (1 - rX) + 0.15 * rX,
    target: S.R.clear.clone().lerp(S.W.crossR, rX), reach: 1, palm: S.R.toVoid.clone().lerp(S.W.inward, rX).normalize() };
  // ---- body
  const jabLean = pulse(t, that - 0.14, 0.18, 0.12, 0.3);
  P.body = { ...P.body,
    lean: 0.14 * jabLean - 0.06 * cross + 0.06 * pulse(t, b2 + 0.0, 0.08, 0.15, 0.3),
    recoil: 0.1 * pulse(t, thing + 0.02, 0.1, 0.05, 0.4),
    scoot: pulse(t, thing + 0.02, 0.08, 0.12, 0.12), scootPhase: (t - thing) * 1.6,
    tremble: 0.12 + 0.25 * jab + 0.15 * ramp(t, b4, b4 + 0.4),
    hunch: 0.3 - 0.14 * ta.chin,
    lookBack: ta.lookBack,
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
    [b2 + 0.02, UX('hellno', { mPress: 0.0 })],                                // (lips free for the words)
    [b2 + 0.4, UX('hellno', { mPress: 0.05 })],
    [b2 + 0.62, UX('hellno', { mPress: 1, mPout: 0.3 })],                      // lips pressed tight after
    [b3 - 0.05, UX('glare', { mPress: 0.0, lidU: 0.72 })],
    [that, UX('glare', { mPress: 0.0, lidU: 0.85, browIn: -0.6 })],
    [scary - 0.04, UX('scared', { lidU: 1.2, browIn: 0.75, mTremble: 0.6, mOpen: 0.1, wet: 0.5 })],   // the wobble gives it away
    [scary + 0.2, UX('scared', { lidU: 1.1, browIn: 0.55, mTremble: 0.4 })],
    [thing + 0.08, UX('pout', { lidU: 0.72, browIn: -0.5 })],
    [b4 + 0.2, UX('pout', { lidU: 0.66, mPout: 1.1 })],
  ]);
  P.face.autoBlink = t < b1 + 0.6 ? 0 : 1;
  P.blinkAt = [b2 + 0.7, thing + 0.3, b4 + 0.9];
  return P;
}

// ------------------------------------------------------------------------------------------------ Jesus
function jesusPose(t, user, vd) {
  const b3 = T('s09b03'), b4 = T('s09b04');
  const slip = slipT();
  const uE = user.anchor('eyes'), vE = vd.anchor('eyes').add(V3(0, -0.3, 0));
  // eyes lead, head follows: user -> (scary) Void -> b04: user -> Void -> user -> Void
  const gk = [
    ['s09', uE],
    [slip + 0.55, vE, 0.12],
    [b4 + 0.1, uE, 0.09],
    [b4 + 0.55, vE, 0.09],
    [b4 + 1.0, uE, 0.09],
    [b4 + 1.42, vE, 0.09],
  ];
  const gaze = gazeSched(t, gk);
  const look = gazeSched(t - 0.12, gk.map(([a, b]) => [a, b, 0.26]));
  const turn = ramp(t, slip + 0.5, b4 + 0.2);                   // body squares up to camera, between them
  const yaw = lerp(jYawTalk(), jYawEnd(), turn);
  const pos = W(M.JM);
  const aim = headAim(pos, yaw, look, { fy: 0.62, fp: 0.4, up: 0.18, down: 0.25 });
  const shut = pulse(t, slip + 0.04, 0.22, 0.12, 0.3);          // eyes close slowly... open: ah.
  const face = k(t, [
    ['s09', JX('hopeful', { mOpen: 0, mTeethU: 0, browIn: 0.6, browOut: 0.5, lidU: 1.06 })],
    [T('s09b02') + 0.2, JX('oh', { mOpen: 0.05, browIn: 0.55, browOut: 0.5 })],            // (off) "Hell no."
    [b3 - 0.1, JX('concerned', { mPress: 0.3, browIn: 0.5 })],
    [slip, JX('compassion', { mPress: 0.45, browIn: 0.7 })],
    [slip + 0.6, JX('concerned', { mPress: 0.6, browIn: 0.6 })],
    [b4 + 0.1, JX('pressed', { mSmile: 0.05, mPress: 0.85, browIn: 0.45, browOut: 0.35, lidU: 1.0 })],
    [b4 + 0.55, JX('pressed', { mSmile: 0.05, mPress: 0.9, browIn: 0.62, browOut: 0.5, lidU: 1.06 })],
    [b4 + 1.0, JX('pressed', { mSmile: 0.05, mPress: 0.95, browIn: 0.8, browOut: 0.68, lidU: 1.12 })],
    [b4 + 1.42, JX('pressed', { mSmile: 0.05, mPress: 0.95, browIn: 0.92, browOut: 0.8, lidU: 1.16 })],
  ]);
  face.blink = shut; face.autoBlink = shut > 0 ? 0 : 1;
  return {
    pos, yaw, face, gaze,
    head: { yaw: aim.yaw, pitch: aim.pitch + 0.04 * shut, roll: 0.1 * (1 - turn), follow: 0 },
    body: { lean: 0.02 * (1 - turn), shrug: 0.12 * ramp(t, b4, b4 + 1.4) },
    armL: { preset: [['clasp', 0.4 + 0.3 * turn], ['clasp_chest', 0.6 - 0.3 * turn]] },
    armR: { preset: [['clasp', 0.4 + 0.3 * turn], ['clasp_chest', 0.6 - 0.3 * turn]] },
    blinkAt: [b4 + 0.07, b4 + 0.98],
  };
}
