// s08 do_you_have_a_moment — the Void's armour goes on (folded arms, a scowl, a held breath: the frozen star mote),
// and Jesus relays its request like an official interpreter with impeccable manners.
//   b01 LOWUP (over the user's RIGHT shoulder, lowered to their eyeline; the user's soft shoulder + raised hand at
//       frame-left, so Jesus looks screen-left at them exactly as in b02/b05) slow push on the Void: arms fold on
//       "crosses its arms" (L, then R 4 f later, velvet whump), chin up; on "scowls" the scowl lands (+ the tell: inner
//       brow tips up a hair, breath held -> the mote rising off its shoulder stops dead). Jesus glances up at it (eyes
//       lead, the head only follows a little: pitch capped), back to the user, at the scowl, at the mote with brows up;
//       "okay, here goes" breath.
//   b02 Jesus medium (the mote still hanging by the Void's shoulder in frame): throat-clear, two tugs on the sash, hands
//       clasp at the chest, bright formal smile.
//   b03 same, he steps JV -> JM toward the user; head tilts back toward the Void on "the void says".
//   b04 VOID_CU: on "important" chin up a notch, scowl deepens, eyes flick down to the user's raised hand and back.
//   b05 tight OTS over the user's raised hand: "Do you have a moment?" hopeful smile, wince on "moment", then both wait.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, galaxyAt, galaxySpin, sy } from './marks.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { scopeVisible, ensureLittleGalaxy } from './edgeprops.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, fitShot, mixShot, W, WY, faceYaw, MARKS as M, jesusStep, starSprite, headAim } from './armour_shared.js';
import { voidArmour, moteState, userSeated, sceneLook, computeMote, updateVoid, defendRef, assertLipsync } from './armour_common.js';

let S = null;   // static points/shots (computed once in setup; pure data afterwards)

export default {
  id: 's08',
  async setup(app) {
    await loadWords();
    assertLipsync('s08');
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const st = { scene: set.scene, set, jesus, vd, user };
    st.fx = new Particles({ max: 24 }); set.scene.add(st.fx.mesh);
    st.mote = starSprite(0xfff2d0, 0.2); set.scene.add(st.mote);
    ensureLittleGalaxy(set);                                       // the shared little galaxy by the sneaker (edgeprops)
    for (const o of [st.fx.mesh, st.mote]) scopeVisible(o, 's08', 's09');
    S = st.S = computeStatics(st);
    return st;
  },
  async update(t, app, st) {
    const { set, jesus, vd, user } = st;
    st.scene.add(jesus.root, vd.root, user.root, st.fx.mesh, st.mote);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 8);
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (shot.vsk ?? 1), voidPos: W(M.V), sunGlow: shot.sunGlow ?? 1 });

    user.update(t, userPose(t));
    updateVoid(vd, t, voidPose(t));
    jesus.update(t, jesusPose(t));

    // particles: the sky galaxy, the frozen mote, the little galaxy at the sneaker
    st.fx.begin();
    const g = galaxyAt(t);
    if (g) st.fx.add(g, EDGE.GALAXY.size, 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
    st.fx.end();
    const ms = moteState(t, S.MOTE);
    st.mote.visible = ms.a > 0.01;
    st.mote.position.copy(ms.p); st.mote.material.opacity = ms.a; st.mote.scale.setScalar(0.2 * ms.s);
    st.look = sceneLook('s08', set.look, t);
  },
};

// ------------------------------------------------------------------------------------------------ times
const tb = (r) => T(r);
const WT = (w, beat = 's08b01', o = {}) => wordT(beat, w, o);

// ------------------------------------------------------------------------------------------------ statics
function computeStatics(st) {
  const { vd, user } = st;
  const out = {};
  const jEye = (p, yaw) => V3(p[0] + Math.sin(yaw) * 0.14, 1.55, p[2] + Math.cos(yaw) * 0.14);
  out.jEyesJV = jEye(W(M.JV), WY(M.JV));
  out.jEyesJM = jEye(W(M.JM), jesusYawAt(T('s08b05')));
  // user (seated at U) — read the real anchors
  const t0 = T('s08b03');
  out.R = defendRef(user, T('s08b05'));
  user.update(t0, userSeated(t0, { gaze: out.jEyesJV, R: out.R }));
  out.uEyes = user.anchor('eyes'); out.uHead = user.anchor('head');
  const t5 = T('s08b05') + 0.3;
  user.update(t5, userSeated(t5, { gaze: out.jEyesJM, R: out.R }));
  out.uHandR = user.anchor('handR'); out.uShR = user.anchor('shoulderR');
  // the Void at V
  vd.update(t0, voidArmour(t0, { gaze: out.uEyes }));
  out.vEyes = vd.anchor('eyes');
  out.MOTE = computeMote(vd, out.uEyes);
  // ---- cameras
  const uE = out.uEyes, vE = out.vEyes, jM = out.jEyesJM;
  const towardPair = vE.clone().sub(uE).setY(0).normalize();
  const right = V3(-towardPair.z, 0, towardPair.x);                      // the user's RIGHT (camera side of the line)
  // LOWUP: over the user's RIGHT shoulder, lowered to their eyeline (STAGING §3): the user's soft shoulder / raised hand
  // at frame-left, Jesus at JV between them and the Void, the whole Void towering. Line test > 0.6.
  const lowA = uE.clone().addScaledVector(towardPair, -1.35).addScaledVector(right, 0.62).setY(0.92);
  const lowB = lowA.clone().addScaledVector(towardPair, 0.75).addScaledVector(right, -0.08).setY(0.98);
  const mp = out.MOTE.p;
  out.LOWUP_A = fitShot([[vE, 430, 245], [out.jEyesJV, 300, 470, 0.25], [mp, 560, 330, 0.3]], 52, lowA, vE, { free: [0, 0, 0] });
  out.LOWUP_B = fitShot([[vE, 420, 232], [out.jEyesJV, 285, 470, 0.15], [mp, 570, 330, 0.3]], 46, lowB, vE, { free: [0, 0, 0] });
  // Jesus medium (b02/b03): 30 deg off the Void->Jesus line toward the camera side (line test ok), the Void looming
  // behind-right of him; the frozen mote by its shoulder kept in frame; dollies with his step so the framing holds
  const sD = jesusStep(T('s08b02')), yD = jesusYawAt(T('s08b02'));
  out.jEyesD = jEye(sD.pos, yD);
  out.JMED_A = fitShot([[out.jEyesD, 270, 450], [vE, 520, 200, 0.1], [mp, 630, 330, 0.8]], 46, EDGE.W(-1.85, 1.3, 2.2), out.jEyesD, { free: [0, 0, 0] });
  out.JMED_B = fitShot([[jM, 270, 450], [vE, 560, 220, 0.1], [mp, 640, 350, 0.8]], 46, EDGE.W(-1.8, 1.3, 2.7), jM, { free: [0, 0, 0] });
  // VOID_CU (b04): yaw cheated toward its left so Jesus (at JM, screen-left) is fully out of frame
  out.VCU_A = EDGE.shot(EDGE.L(vE), { dist: 3.8, yaw: -30, pitch: -4, fov: 33, screenY: sy(345) });
  out.VCU_B = EDGE.shot(EDGE.L(vE), { dist: 3.45, yaw: -29, pitch: -5, fov: 33, screenY: sy(340) });
  // OTS (b05), tight: over the user's raised right hand (soft, lower-left), Jesus's face big enough to read the wince,
  // the Void's scowl above-right of him: one hopeful smile, one scowl
  const otsP = uE.clone().addScaledVector(towardPair, -1.15).addScaledVector(right, 0.42).setY(1.42);
  out.OTS_A = fitShot([[jM, 290, 455], [vE, 470, 250, 0.5], [mp, 630, 340, 0.4], [out.uHandR, 120, 760, 0.12]], 30, otsP, jM, { posReg: 0.08, yMin: 1.25, yMax: 1.7, drift: 0.2 });
  out.OTS_B = fitShot([[jM, 290, 450], [vE, 480, 235, 0.5], [mp, 640, 330, 0.4], [out.uHandR, 100, 790, 0.08]], 27, otsP, jM, { posReg: 0.08, yMin: 1.25, yMax: 1.7, drift: 0.15 });
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const cut2 = tb('s08b02') - 0.15, cut4 = tb('s08b04') - 0.05, cut5 = tb('s08b05') - 0.12;
  if (t < cut2) {        // b01: LOWUP slow push on the Void
    const u = ramp(t, tb('s08b01') - 0.2, tb('s08b01.end'), 'inOut');
    return { ...mixShot(S.LOWUP_A, S.LOWUP_B, u), vsk: 1.05 };
  }
  if (t < cut4) {        // b02-b03: Jesus medium; pans with his step
    const st = jesusStep(t);
    return { ...mixShot(S.JMED_A, S.JMED_B, smooth(clamp((t - st.a + 0.1) / (st.b - st.a + 0.25)))), vsk: 0.85 };
  }
  if (t < cut5) {        // b04: the Void's face
    return mixShot(S.VCU_A, S.VCU_B, ramp(t, cut4, cut5, 'linear'));
  }
  return mixShot(S.OTS_A, S.OTS_B, ramp(t, cut5, tb('s08.end'), 'out'));   // b05 tight OTS, a breath of push
}

// ------------------------------------------------------------------------------------------------ the Void
function voidPose(t) {
  const P = voidArmour(t, { gaze: voidGaze(t) });
  // b05: one slow blink while waiting
  const sb = T('s08b05') + 0.95;
  P.face.blink = Math.max(P.face.blink || 0, pulse(t, sb, 0.22, 0.12, 0.3));
  return P;
}
function voidGaze(t) {
  const imp = WT('important', 's08b04', { fallback: 0.4 });
  return gazeSched(t, [
    ['s08', S.jEyesJV],                                      // s07 continuity: "you'll ask?" -> looking at Jesus
    [T('s08b01') + 0.25, S.uEyes, 0.32],                     // eyes slide to the user (slow, deliberate)
    [imp + 0.22, () => S.uHandR, 0.08],                      // the check: is the hand still up?
    [imp + 0.5, S.uEyes, 0.08],                              // it is.
  ]);
}

// ------------------------------------------------------------------------------------------------ Jesus
function jesusYawAt(t) {
  const st = jesusStep(t);
  const y0 = WY(M.JV), y1 = faceYaw(W(M.JM), W(M.U)) + 0.12;   // at JM: facing the user, cheated 7 deg to camera
  return lerp(y0, y1, st.u);
}
function jesusPose(t) {
  const b1 = tb('s08b01'), b2 = tb('s08b02'), b3 = tb('s08b03'), b4 = tb('s08b04'), b5 = tb('s08b05');
  const sc = WT('scowls'), mom = WT('moment?', 's08b05', { fallback: 0.5 });
  const st = jesusStep(t);
  const yaw = jesusYawAt(t);
  const uE = S.uEyes;
  const vE = S.vEyes.clone().add(V3(0, -0.34, 0));   // the scowl, aimed a touch low: the core eye can't roll 30 deg up
  const moteP = S.MOTE.p;
  // ---- gaze (eyes lead; the head follows 3 frames later and only part of the way: pitch capped at 0.2 rad, so a
  // look up at the Void never tips his face to the sky — the eyes and brows carry the look)
  const gk = [
    ['s08', uE],
    [b1 + 0.7, vE, 0.1],                // the arms go: he glances up at the Void
    [b1 + 1.85, uE, 0.09],              // back to the user (how's this landing?)
    [sc + 0.25, vE, 0.1],               // the scowl lands: look up at it
    [sc + 0.72, moteP, 0.08],           // ...and at the frozen mote. brows up a notch
    [sc + 1.22, uE, 0.1],               // okay. here goes.
  ];
  const gaze = gazeSched(t, gk);
  const look = gazeSched(t - 0.12, gk.map(([a, b]) => [a, b, 0.3]));
  const aim = headAim(st.pos, yaw, look, { fy: 0.42, fp: 0.35, up: 0.2, down: 0.2 });
  // ---- face
  const face = k(t, [
    ['s08', JX('rueful', { mSmile: 0.18, mPress: 0.55 })],                      // "I'll ask." tight smile (s07 end)
    [b1 + 0.8, JX('curious', { browIn: 0.42, browOut: 0.45, lidU: 1.18 })],     // the arms cross: brows up
    [b1 + 1.95, JX('kind', { mPress: 0.35, browIn: 0.3 })],
    [sc + 0.3, JX('oh', { mOpen: 0.08, browIn: 0.5, browOut: 0.55, lidU: 1.2 })],   // the scowl: brows up a notch
    [sc + 0.8, JX('surprised', { mOpen: 0.04, lidU: 1.25, browIn: 0.7, browOut: 0.8 })],   // the mote, frozen
    [sc + 1.22, JX('rueful', { mPress: 0.7, mSmile: 0.12, browIn: 0.45, browOut: 0.3 })],  // "okay, here goes" (lips pressed, breath)
    [b2 + 0.15, JX('kind', { mPress: 0.5, browIn: 0.3, lidU: 0.92 })],          // throat clear (eyes half-close)
    [b2 + 0.55, JX('kind', { mPress: 0.3, browIn: 0.3 })],
    [b2 + 0.85, JX('beam', { mOpen: 0.06, mTeethU: 0.5, browIn: 0.5, browOut: 0.48, lidU: 1.04 })],   // bright formal smile
    [b3 + 0.1, JX('warm', { browIn: 0.45, browOut: 0.35, lidU: 1.0 })],         // speaking: warm, earnest
    [b4 + 0.3, JX('warm', { browIn: 0.55, browOut: 0.2, mSmile: 0.4 })],
    [b4 + 0.75, JX('compassion', { mSmile: 0.2, browIn: 0.65 })],               // "important" — lower, meaning it
    [b5 - 0.05, JX('hopeful', { mOpen: 0.0, mTeethU: 0, browIn: 0.6, browOut: 0.5, lidU: 1.06 })],
    [mom, JX('hopeful', { mOpen: 0.0, mTeethU: 0, mAsym: 0.4, mPress: 0.3, mSmile: 0.42, browIn: 0.72, browOut: 0.4, lidU: 0.98, lidAsym: 0.15 })],   // tiny wince
    [mom + 0.35, JX('hopeful', { mOpen: 0.0, mTeethU: 0, mPress: 0.2, browIn: 0.6, browOut: 0.5, lidU: 1.06, saccade: 0.2 })],
  ]);
  // ---- body: breath / throat clear / "here goes"
  const hereGoes = pulse(t, sc + 1.25, 0.4, 0.08, 0.45);
  const throat = pulse(t, b2 - 0.1, 0.16, 0.06, 0.22);
  const dodge = pulse(t, st.dodge0 - 0.05, 0.18, 0.15, 0.45);
  const body = {
    shrug: 0.25 * hereGoes + 0.18 * throat,
    lean: -0.02 * hereGoes - 0.02 * throat - 0.05 * dodge + 0.04 * pulse(t, b3 + 0.05, 0.35, 0.2, 0.5) + 0.02 * pulse(t, b5, 0.3, 0.6, 0.6),
    breathe: 1 + 1.6 * hereGoes,
    tilt: -0.05 * dodge,
  };
  // ---- head: tilt back toward the Void on "the void says"; head tilt on "Do you have a moment?"
  const vs = pulse(t, b3 + 0.05, 0.28, 0.35, 0.4);
  const tiltQ = ramp(t, b5 - 0.1, b5 + 0.45);
  const head = {
    yaw: aim.yaw + 0.28 * vs, roll: 0.07 * vs + 0.1 * tiltQ - 0.03 * pulse(t, mom, 0.08, 0.1, 0.3),
    pitch: aim.pitch + 0.12 * throat - 0.04 * hereGoes, follow: 0,
  };
  // ---- arms: rest -> (b02) right hand tugs the sash twice -> both clasp at the chest
  const c0 = b2 - 0.05;
  const toSash = ramp(t, c0, c0 + 0.22, 'out'), toClasp = ramp(t, c0 + 0.66, c0 + 0.92);
  const tug = pulse(t, c0 + 0.24, 0.07, 0.03, 0.08) + pulse(t, c0 + 0.44, 0.07, 0.03, 0.09);
  const fwd = V3(Math.sin(yaw), 0, Math.cos(yaw)), left = V3(Math.cos(yaw), 0, -Math.sin(yaw));
  const sashOff = left.clone().multiplyScalar(0.075).add(V3(0, 0.07 - 0.04 * tug, 0)).addScaledVector(fwd, 0.015 + 0.01 * tug);
  const wR = toSash * (1 - toClasp);
  const armR = {
    preset: [['clasp', (1 - toSash) * (1 - toClasp) + 0.4 * toClasp + 1e-4], ['heart', wR], ['clasp_chest', 0.6 * toClasp]],
    offset: sashOff.multiplyScalar(wR).toArray(),
    hand: wR > 0.5 ? { curl: 0.55, thumb: 0.75, spread: 0.02, cup: 0.5 } : undefined,
  };
  const lClasp = ramp(t, c0 + 0.55, c0 + 0.9);
  const armL = { preset: [['clasp', 1 - 0.6 * lClasp + 1e-4], ['clasp_chest', 0.6 * lClasp]] };
  // ---- the step JV -> JM
  const walk = st.u > 0 && st.u < 1 ? { amount: Math.sin(Math.PI * st.u) * 0.95, phase: 0.62 * st.u + 0.05, style: 'walk' } : { amount: 0 };
  const blinkAt = [b1 + 0.68, sc + 0.22, b2 - 0.05, b3 + 0.02, b4 + 0.7, b5 - 0.12];
  return { pos: st.pos, yaw, face, gaze, head, body, armL, armR, walk, blinkAt };
}

// ------------------------------------------------------------------------------------------------ the user
function userPose(t) {
  const b5 = tb('s08b05');
  const gaze = gazeSched(t, [
    ['s08', () => jesusEyesAt(t)],
    [T('s08b01') + 0.4, S.vEyes, 0.09],                         // the arms cross: eyes on the Void
    [T('s08b02') - 0.1, () => jesusEyesAt(t), 0.1],             // Jesus starts: eyes to him
  ]);
  const P = userSeated(t, { gaze, R: S.R });
  P.body.recoil = (P.body.recoil || 0) + 0.18 * ramp(t, b5 + 0.55, b5 + 0.85);   // a tiny backward lean
  P.face = k(t, [['s08', UX('suspicious', { lidU: 0.85 })], [T('s08b01') + 2.6, UX('gulp', { lidU: 1.1 })], [T('s08b02'), UX('suspicious', { lidU: 0.9 })], [b5 + 0.6, UX('gulp')]]);
  return P;
}
function jesusEyesAt(t) {
  const st = jesusStep(t), y = jesusYawAt(t);
  return V3(st.pos[0] + Math.sin(y) * 0.14, 1.55, st.pos[2] + Math.cos(y) * 0.14);
}
