// s08 do_you_have_a_moment — the Void's armour goes on (crossed arms, a scowl, a held breath: the frozen star mote),
// and Jesus relays its request like an official interpreter with impeccable manners.
//   b01 LOWUP (user's eyeline, 28 mm) push on the Void: arms cross on "crosses its arms" (L, then R 4 f later, velvet
//       whump), chin up; on "scowls" the scowl lands (+ the tell: inner brow tips up a hair, breath held -> the rising
//       mote freezes). Jesus glances at it, brows up; "okay, here goes" breath.
//   b02 Jesus medium: throat-clear, two tugs on the sash, hands clasp at the chest, bright formal smile.
//   b03 same, he steps JV -> JM toward the user; head tilts back toward the Void on "the void says".
//   b04 VOID_CU: on "important" chin up a notch, scowl deepens, eyes flick down to the user's raised hand and back.
//   b05 OTS over the user's raised hand: "Do you have a moment?" hopeful smile, wince on "moment", then both wait.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, fbm1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, galaxyAt, galaxySpin, lookFor, sy, px } from './marks.js';
import { VX } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, fitShot, mixShot, W, WY, faceYaw, MARKS as M, jesusStep, starSprite } from './armour_shared.js';
import { voidArmour, moteState, galaxyFloor, userSeated, sceneLook, moteFreezeT } from './armour_common.js';

let S = null;   // static points/shots (computed once in setup; pure data afterwards)

export default {
  id: 's08',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const st = { scene: set.scene, set, jesus, vd, user };
    st.fx = new Particles({ max: 24 }); set.scene.add(st.fx.mesh);
    st.mote = starSprite(0xfff2d0, 0.2); set.scene.add(st.mote);
    st.floorGal = galaxyFloor(st.fx); set.scene.add(st.floorGal.mesh);
    S = st.S = computeStatics(st);
    console.log('s08 statics', JSON.stringify({ uE: S.uEyes.toArray(), vE: S.vEyes.toArray(), jE: S.jEyesJV.toArray(), jM: S.jEyesJM.toArray(), hand: S.uHandR.toArray(), mote: S.MOTE.p.toArray().map((v) => +v.toFixed(2)), low: S.LOWUP_A.pos.map((v) => +v.toFixed(2)), jmed: S.JMED_A.pos.map((v) => +v.toFixed(2)), errJ: S.JMED_A.err.toFixed(1) }));
    return st;
  },
  async update(t, app, st) {
    globalThis.__dbg = true;
    const { set, jesus, vd, user } = st;
    st.scene.add(jesus.root, vd.root, user.root, st.fx.mesh, st.mote, st.floorGal.mesh);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 8);
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (shot.vsk ?? 1), voidPos: W(M.V), sunGlow: shot.sunGlow ?? 1 });

    user.update(t, userPose(t));
    vd.update(t, voidPose(t));
    jesus.update(t, jesusPose(t));

    // particles: the sky galaxy, the frozen mote, the little galaxy at the sneaker
    st.fx.begin();
    const g = galaxyAt(t);
    if (g) st.fx.add(g, EDGE.GALAXY.size, 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
    st.fx.end();
    const ms = moteState(t, S.MOTE);
    st.mote.visible = ms.a > 0.01;
    st.mote.position.copy(ms.p); st.mote.material.opacity = ms.a; st.mote.scale.setScalar(0.2 * ms.s);
    st.floorGal.update(t);
    if (globalThis.__dbg) console.log('mote px', t.toFixed(2), JSON.stringify(px(app.camera, ms.p)), ms.a.toFixed(2), JSON.stringify(ms.p.toArray().map((v) => +v.toFixed(2))));
    st.look = sceneLook('s08', set.look, t);
  },
};

// ------------------------------------------------------------------------------------------------ times
const tb = (r) => T(r);
const WT = (w, beat = 's08b01', o = {}) => wordT(beat, w, o);

// ------------------------------------------------------------------------------------------------ statics
function computeStatics(st) {
  const { jesus, vd, user } = st;
  const out = {};
  const jYawJV = WY(M.JV);
  const jEye = (p, yaw) => V3(p[0] + Math.sin(yaw) * 0.14, 1.55, p[2] + Math.cos(yaw) * 0.14);
  out.jEyesJV = jEye(W(M.JV), jYawJV);
  const jmYaw = jesusYawAt(T('s08b05'));
  out.jEyesJM = jEye(W(M.JM), jmYaw);
  // user (seated at U) — read the real anchors
  const t0 = T('s08b03');
  user.update(t0, userSeated(t0, { gaze: out.jEyesJV }));
  out.uEyes = user.anchor('eyes'); out.uHead = user.anchor('head'); out.uHandR = user.anchor('handR');
  // the Void at V
  vd.update(t0, voidArmour(t0, { gaze: out.uEyes }));
  out.vEyes = vd.anchor('eyes'); out.vHead = vd.anchor('head');
  // the frozen mote: shoulderL at the freeze + (0.15, 0.35, 0.10) (STAGING §1.6)
  const tf = moteFreezeT();
  vd.update(tf, voidArmour(tf, { gaze: out.uEyes }));
  // (STAGING's world offset put it inside the hood's side bulge: push it out along the Void's left + a little forward)
  const vy = WY(M.V), vl = V3(Math.cos(vy), 0, -Math.sin(vy)), vf = V3(Math.sin(vy), 0, Math.cos(vy));
  out.MOTE = { p: vd.anchor('shoulderL').addScaledVector(vl, -0.1).addScaledVector(vf, 0.75).add(V3(0, 0.34, 0)), tf };
  // ---- cameras
  const uE = out.uEyes, vE = out.vEyes, jE = out.jEyesJV, jM = out.jEyesJM;
  const towardPair = vE.clone().sub(uE).setY(0).normalize();
  const right = V3(-towardPair.z, 0, towardPair.x);                      // screen right when looking at the pair
  // LOWUP: the user's own eyeline (POV, a hair in front of their face), the whole Void towering, Jesus at its side
  // (camera 1.5 m behind the user's head at their eye height, the user just off frame right: the whole Void reads)
  const lowA = uE.clone().addScaledVector(towardPair, -1.5).addScaledVector(right, -0.72).setY(0.95);
  const lowB = lowA.clone().addScaledVector(towardPair, 0.8).addScaledVector(right, 0.12).setY(1.0);
  out.LOWUP_A = fitShot([[vE, 410, 250]], 54, lowA, vE, { free: [0, 0, 0] });
  out.LOWUP_B = fitShot([[vE, 400, 262]], 46, lowB, vE, { free: [0, 0, 0] });
  // Jesus medium (b02/b03): 30 deg off the Void->Jesus line toward the camera side (line test ok), the Void looming
  // behind-right of him; dollies 0.46 m with his step so the framing holds (numbers from a projection scan)
  const sD = jesusStep(T('s08b02')), yD = jesusYawAt(T('s08b02'));
  out.jEyesD = jEye(sD.pos, yD);
  out.JMED_A = fitShot([[out.jEyesD, 280, 450], [vE, 570, 165, 0.05]], 33, EDGE.W(-2.06, 1.25, 2.0), out.jEyesD, { free: [0, 0, 0] });
  out.JMED_B = fitShot([[jM, 285, 445], [vE, 640, 210, 0.05]], 33, EDGE.W(-2.0, 1.3, 2.5), jM, { free: [0, 0, 0] });
  // VOID_CU (b04)
  out.VCU_A = EDGE.shot(EDGE.L(vE), { dist: 3.8, yaw: -38, pitch: -4, fov: 33, screenY: sy(350) });
  out.VCU_B = EDGE.shot(EDGE.L(vE), { dist: 3.45, yaw: -37, pitch: -5, fov: 33, screenY: sy(345) });
  // OTS (b05) over the user's raised hand
  out.OTS_A = EDGE.cam('OTS', { drift: 0.25 });
  out.OTS_B = fitShot([[jM, 285, 445], [vE, 440, 300, 0.6], [out.uHandR, 150, 700, 0.3]], 44, out.OTS_A.pos, out.OTS_A.look, { posReg: 0.05, yMin: 1.4, yMax: 2.0 });
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
  return mixShot(S.OTS_A, S.OTS_B, ramp(t, cut5, tb('s08.end'), 'out'));   // b05 OTS, a breath of push
}

// ------------------------------------------------------------------------------------------------ the Void
function voidPose(t) {
  const P = voidArmour(t, { gaze: voidGaze(t) });
  // b04: on "important" the chin lifts another notch and the scowl deepens (the shared pose already carries it);
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
/** elevation angle (rad) of a world point seen from Jesus's eyes at feet position p */
function elevOf(target, p) { const d = toV(target); return Math.atan2(d.y - 1.55, Math.hypot(d.x - p[0], d.z - p[2])); }
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
  const uE = S.uEyes, vE = S.vEyes;
  const moteP = S.MOTE.p;
  // ---- gaze (eyes lead; head follows with a lag)
  const gk = [
    ['s08', uE],
    [b1 + 0.7, vE, 0.1],                // the arms go: he glances up at the Void
    [b1 + 1.85, uE, 0.09],              // back to the user (how's this landing?)
    [sc + 0.25, vE, 0.1],               // the scowl lands: look up at it
    [sc + 0.85, moteP, 0.08],           // ...and at the frozen mote. brows up a notch
    [sc + 1.45, uE, 0.1],               // okay. here goes.
  ];
  const gaze = gazeSched(t, gk);
  const headLook = gazeSched(t - 0.1, gk.map(([a, b]) => [a, b, 0.32]));
  // ---- face
  const face = k(t, [
    ['s08', JX('rueful', { mSmile: 0.18, mPress: 0.55 })],                      // "I'll ask." tight smile (s07 end)
    [b1 + 0.8, JX('curious', { browIn: 0.42, browOut: 0.45, lidU: 1.15 })],     // the arms cross: brows up
    [b1 + 1.95, JX('kind', { mPress: 0.35, browIn: 0.3 })],
    [sc + 0.3, JX('oh', { mOpen: 0.08, browIn: 0.5, browOut: 0.55 })],          // the scowl: brows up a notch
    [sc + 1.0, JX('surprised', { mOpen: 0.04, lidU: 1.22, browIn: 0.65, browOut: 0.75 })],   // the mote, frozen
    [sc + 1.6, JX('rueful', { mPress: 0.7, mSmile: 0.12, browIn: 0.4 })],      // "okay, here goes" (lips pressed, breath)
    [b2 + 0.15, JX('kind', { mPress: 0.5, browIn: 0.3, lidU: 0.92 })],          // throat clear (eyes half-close)
    [b2 + 0.55, JX('kind', { mPress: 0.3, browIn: 0.3 })],
    [b2 + 0.85, JX('beam', { mOpen: 0.06, mTeethU: 0.5, browIn: 0.5, browOut: 0.48, lidU: 1.04 })],   // bright formal smile
    [b3 + 0.1, JX('warm', { browIn: 0.45, browOut: 0.35, lidU: 1.0 })],         // speaking: warm, earnest
    [b4 + 0.3, JX('warm', { browIn: 0.55, browOut: 0.2, mSmile: 0.4 })],
    [b4 + 0.75, JX('compassion', { mSmile: 0.2, browIn: 0.65 })],               // "important" — lower, meaning it
    [b5 - 0.05, JX('hopeful', { mOpen: 0.0, mTeethU: 0, browIn: 0.6, browOut: 0.5, lidU: 1.06 })],
    [mom, JX('hopeful', { mOpen: 0.0, mTeethU: 0, mAsym: 0.32, mPress: 0.35, browIn: 0.65, browOut: 0.45, lidU: 1.02 })],   // tiny wince
    [mom + 0.35, JX('hopeful', { mOpen: 0.0, mTeethU: 0, mPress: 0.2, browIn: 0.6, browOut: 0.5, lidU: 1.06, saccade: 0.2 })],
  ]);
  // ---- body: breath / throat clear / "here goes"
  const hereGoes = pulse(t, sc + 1.5, 0.45, 0.1, 0.55);
  const throat = pulse(t, b2 - 0.1, 0.16, 0.06, 0.22);
  const body = {
    shrug: 0.25 * hereGoes + 0.18 * throat,
    lean: -0.03 * hereGoes - 0.02 * throat - 0.07 * pulse(t, st.dodge0 - 0.05, 0.18, 0.15, 0.45) + 0.04 * pulse(t, b3 + 0.05, 0.35, 0.2, 0.5) + 0.02 * pulse(t, b5, 0.3, 0.6, 0.6),
    breathe: 1 + 1.6 * hereGoes,
    tilt: -0.06 * pulse(t, st.dodge0 - 0.05, 0.18, 0.15, 0.45),
  };
  // ---- head: tilt back toward the Void on "the void says"; head tilt on "Do you have a moment?"
  const vs = pulse(t, b3 + 0.05, 0.28, 0.35, 0.4);
  const tiltQ = ramp(t, b5 - 0.1, b5 + 0.45);
  const head = {
    look: headLook, follow: (0.5 + 0.42 * smooth((elevOf(headLook, st.pos) - 0.15) / 0.35)) * (1 - 0.45 * vs),
    yaw: 0.28 * vs, roll: 0.07 * vs + 0.1 * tiltQ - 0.03 * pulse(t, mom, 0.08, 0.1, 0.3),
    pitch: 0.12 * throat - 0.05 * hereGoes,
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
  const jE = jesusEyesAt(t);
  const gaze = gazeSched(t, [
    ['s08', jE],
    [T('s08b01') + 0.4, S.vEyes, 0.09],                         // the arms cross: eyes on the Void
    [T('s08b02') - 0.1, () => jesusEyesAt(t), 0.1],             // Jesus starts: eyes to him
  ]);
  const P = userSeated(t, { gaze });
  P.body.recoil = (P.body.recoil || 0) + 0.18 * ramp(t, b5 + 0.55, b5 + 0.85);   // a tiny backward lean
  P.face = k(t, [['s08', UX('suspicious', { lidU: 0.85 })], [T('s08b01') + 2.6, UX('gulp', { lidU: 1.1 })], [T('s08b02'), UX('suspicious', { lidU: 0.9 })], [b5 + 0.6, UX('gulp')]]);
  return P;
}
function jesusEyesAt(t) {
  const st = jesusStep(t), y = jesusYawAt(t);
  return V3(st.pos[0] + Math.sin(y) * 0.14, 1.55, st.pos[2] + Math.cos(y) * 0.14);
}
