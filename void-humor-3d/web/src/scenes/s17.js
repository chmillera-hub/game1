// s17 bonus_scene — dissolve from the sunset into the back room of my mind; the Void unlocks Fear's time-out cage.
//   b01 "Okay. ^Bonus scene."   OPEN: far down the dim room, a small lavender glow in a cage (Fear, sobbing at the bars)
//        beside a huge round dark shape with two soft starlight eyes; slow 2 m drift toward them.
//   b02 "Now I'm imagining, when the void opened up the cage,"   INSERT on the brass latch: the Void's big hand comes
//        down, ONE fingertip turns the lever (click on "opened"), Fear's sobbing stops dead; the camera pulls back
//        (constant-rate log dolly) as the door creaks open, to the MASTER (cage left, Void towering, corner back-right).
//   b03 "to my fear..."   FEAR_CU through the open doorway: the head turns over its shoulder toward the door; eyes
//        widen, heavy lids lift, a tear hangs; no breath. Then it turns round to face the door (FIN -> FDOOR).
//   b04 (silent)   tilt up from Fear's face to the Void's far above: Fear's eyes climb the cloak (head a beat
//        behind), the tear falls; the Void, utterly still, lids at half, tiny smile; stars kindle in its hood.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { EYE_LIGHT } from '../core/context.js';
import { ROOM, lookFor, sy } from './marks.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, fitShot, mixShot, logDolly, project, cast, bonusMarks, voidBowed, clamp, smooth, lerp } from './kit_bonus.js';

let S = null;
const tb = (r) => T(r);

export default {
  id: 's17',
  async setup(app) {
    await loadWords();
    const set = await app.set('BACKROOM');
    const vd = await app.char('VOID'), fear = await app.char('FEAR'), mag = await app.char('MAGICIAN');
    const st = { scene: set.scene, set, vd, fear, mag };
    S = st.S = statics(st);
    return st;
  },
  async update(t, app, st) {
    st.__t = t;
    const { set, vd, fear, mag } = st;
    cast(app, st.scene, ['VOID', 'FEAR', 'MAGICIAN']);
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 17);
    set.update(t, { latch: latchAt(t), cageDoor: doorAt(t), tagSwing: 0.3 * pulse(t, S.T.opened + 0.25, 0.3, 0.6, 0.9) });
    // close on Fear the far key grazes its eye whites into a bloom blob: soften the eye key for those shots
    if (t >= S.T.cutCU) EYE_LIGHT.uKeyColor.value.multiplyScalar(0.45);
    const fp = fearPoseFn(t);
    fear.update(t, fp);
    vd.update(t, voidPose(t, st));
    mag.update(t, magPose(t, st));
    st.look = lookFor('s17', set.look);
  },
};

// ------------------------------------------------------------------------------------------------ times
function times() {
  const b1 = tb('s17b01'), b2 = tb('s17b02'), b3 = tb('s17b03'), b4 = tb('s17b04');
  const opened = wordT('s17b02', 'opened', { fallback: 0.6 });
  const fearW = wordT('s17b03', 'fear', { fallback: 0.4 });
  return {
    s0: tb('s17'), end: tb('s17.end'), b1, b2, b3, b4, opened, fearW,
    bonus: wordT('s17b01', 'bonus', { fallback: 0.55 }),
    handA: b2 + 0.25, handB: b2 + 1.55,                         // the big hand comes down
    click: opened + 0.06,                                       // the lever snaps up (lock_click)
    doorA: opened + 0.3, doorB: opened + 1.35,                  // creak
    cutIns: b2 - 0.1, dollyA: b2 + 0.55, cutCU: b3 - 0.08, cutTilt: b4 - 0.06,
    turnA: b3 + 0.9, turnB: b4 + 0.2,                           // Fear turns round to face the door (FIN -> FDOOR)
  };
}
const latchAt = (t) => k(t, [[S.T.click - 0.3, 0], [S.T.click, 1, 'in']]);
const doorAt = (t) => k(t, [[S.T.doorA, 0], [S.T.doorB, 1, 'inOut']]);

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { set, vd, fear, mag } = st;
  const out = { T: times() };
  S = out;                       // pose functions below read S (filled progressively)
  out.B = bonusMarks(set);
  const B = out.B, TT = out.T;
  // s17 cheat: the Void stands 0.25 m nearer the latch for this scene (its arm can't reach the lock from voidSpot);
  // s18 opens on a moving orbit at voidSpot, so the cut hides it.
  { const L0 = set.anchors.cageLatch, d = V3(L0.x - B.V[0], 0, L0.z - B.V[2]).normalize(); B.V = [B.V[0] + 0.32 * d.x, 0, B.V[2] + 0.32 * d.z]; }
  // Fear's bar grips at FIN: the two fixed bars nearest its hands, in front of it
  const fy = B.finYaw, fwd = V3(Math.sin(fy), 0, Math.cos(fy)), left = V3(Math.cos(fy), 0, -Math.sin(fy));
  const fin = toV(B.FIN);
  let best = { L: null, R: null };
  for (let a = -180; a <= 180; a += 18) {
    const p = set.cageBar(a, 0.5 + B.plate);
    const d = p.clone().sub(fin); d.y = 0;
    const x = d.dot(left), z = d.dot(fwd);
    if (z < 0.05) continue;
    for (const [s, sx] of [['L', 1], ['R', -1]]) {
      const c = (x * sx - 0.17) ** 2 + 0.3 * (z - 0.3) ** 2;
      if (x * sx > 0.04 && (!best[s] || c < best[s].c)) best[s] = { p, c };
    }
  }
  out.barL = best.L ? best.L.p : fin.clone().addScaledVector(fwd, 0.3).addScaledVector(left, 0.17).setY(0.54);
  out.barR = best.R ? best.R.p : fin.clone().addScaledVector(fwd, 0.3).addScaledVector(left, -0.17).setY(0.54);
  // representative poses -> eye points (the Void first, looking at roughly where Fear's eyes will be)
  vd.update(TT.b4, voidBowed(TT.b4, B, { gaze: toV(B.FDOOR).add(V3(0, 0.6, 0)) }));
  out.vEyes = vd.anchor('eyes'); out.vChest = vd.anchor('chest'); out.vMouth = vd.anchor('mouth');
  out.vHem = toV(B.V).add(V3(0, 0.6, 0)).addScaledVector(V3(Math.sin(B.vYaw), 0, Math.cos(B.vYaw)), 0.8);
  out.doorPt = set.anchors.cageDoor.clone().setY(0.55 + B.plate);
  fear.update(TT.b1, fearPose(TT.b1));
  out.fEyesFIN = fear.anchor('eyes');
  fear.update(TT.b4 + 1.0, fearPose(TT.b4 + 1.0));
  out.fEyesUp = fear.anchor('eyes');
  out.latch = set.anchors.cageLatch.clone();
  // ---- cameras
  const cOpen = ROOM.cam('OPEN', { drift: 0.2 });
  const dirO = toV(cOpen.look).sub(toV(cOpen.pos)).normalize();
  // land Fear's glow near the frame centre (~y 600) for the dissolve from the s16 sun: fit the start
  out.OPEN_A = fitShot([[out.fEyesFIN, 330, 610], [out.vEyes, 430, 470, 0.5]], 44, cOpen.pos, cOpen.look, { posReg: 0.08, free: [0, 0, 0] });
  // (start the drift past the foreground pillar)
  const o0 = toV(cOpen.pos).addScaledVector(dirO, 1.3);
  out.OPEN_A = fitShot([[out.fEyesFIN, 330, 610], [out.vEyes, 430, 470, 0.5]], 44, o0, toV(cOpen.look).addScaledVector(dirO, 1.3), { posReg: 0.08, free: [0, 0, 0] });
  out.OPEN_B = { ...out.OPEN_A, pos: toV(out.OPEN_A.pos).addScaledVector(dirO, 2.0).toArray(), look: toV(out.OPEN_A.look).addScaledVector(dirO, 2.0).toArray() };
  // INSERT: the latch low-centre, Fear sobbing behind the bars above it, room for the big hand to come down from the right
  // (from Fear's front: its sobbing face through the bars, the latch at the right edge of the cage)
  out.INS = ROOM.shot(ROOM.L(out.latch), { dist: 1.5, yaw: -10, pitch: 2, fov: 33, screenY: sy(640) });
  out.INS.err = 0;
  out.INS.drift = 0.15;
  out.MASTER = fitShot([[out.fEyesFIN, 215, 690], [out.vEyes, 400, 300], [set.anchors.cornerCenter, 615, 560, 0.25]], 44, ROOM.cam('MASTER').pos, ROOM.cam('MASTER').look, { posReg: 0.03 });
  // FEAR_CU from the Void's side, through the open doorway (Fear's face turns toward it): framed between the cowering
  // eyes and where they are once the head has turned
  fear.update(TT.b3 + 0.7, fearPose(TT.b3 + 0.7));
  out.fEyesTurn = fear.anchor('eyes');
  const cuEye = out.fEyesFIN.clone().lerp(out.fEyesTurn, 0.7);
  out.CU_A = ROOM.shot(ROOM.L(cuEye), { dist: 1.3, yaw: 42, pitch: 2, fov: 35, screenY: sy(470) });
  out.CU_A.drift = 0.15;
  // b04 tilt (long lens from the camera side at Fear's height): start tight on Fear's face, tilt up + widen until the
  // Void's face looms above (geometry: both faces can only share a portrait frame from well off to the side)
  const tiltPos = ROOM.W(0.15, 0.75, 5.0);
  out.TILT_B = fitShot([[out.fEyesUp, 130, 720], [out.vEyes, 515, 245]], 40, tiltPos, out.vEyes, { posReg: 0.04, yMin: 0.6, yMax: 1.0 });
  out.TILT_A = fitShot([[out.fEyesUp, 330, 560]], 17, out.TILT_B.pos, out.fEyesUp, { posReg: 10, free: [0, 0, 0] });
  out.TILT_A.drift = out.TILT_B.drift = 0.1;
  console.log('s17 statics', JSON.stringify({ open: project(out.OPEN_A, out.fEyesFIN), master: [project(out.MASTER, out.fEyesFIN), project(out.MASTER, out.vEyes)], tiltErr: out.TILT_B.err.toFixed(1), insErr: out.INS.err.toFixed(1), ins: out.INS.pos.map((v) => +v.toFixed(2)), tiltPos: out.TILT_B.pos.map((v) => +v.toFixed(2)), fEyesFIN: out.fEyesFIN.toArray().map((v) => +v.toFixed(2)), fEyesUp: out.fEyesUp.toArray().map((v) => +v.toFixed(2)), vEyes: out.vEyes.toArray().map((v) => +v.toFixed(2)), cu: out.CU_A.pos.map((v) => +v.toFixed(2)), cuL: out.CU_A.look.map((v) => +v.toFixed(2)), FIN: B.FIN, bars: [out.barL.toArray().map((v) => +v.toFixed(2)), out.barR.toArray().map((v) => +v.toFixed(2))] }));
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const TT = S.T;
  if (t < TT.cutIns) return mixShot(S.OPEN_A, S.OPEN_B, ramp(t, TT.s0 - 0.6, TT.cutIns, 'inOut'));
  if (t < TT.cutCU) {
    const u = ramp(t, TT.dollyA, TT.cutCU + 0.02, 'inOut');
    const w = logDolly(u, 1.55, 7.0);
    return mixShot(S.INS, S.MASTER, w);
  }
  if (t < TT.cutTilt) {
    // follow Fear's eyes a little as it turns round toward the door
    const f = ramp(t, TT.turnA, TT.turnB + 0.1);
    const look = toV(S.CU_A.look).add(S.fEyesUp.clone().sub(S.fEyesTurn).multiplyScalar(0.6 * f));
    const pos = toV(S.CU_A.pos).add(S.fEyesUp.clone().sub(S.fEyesTurn).multiplyScalar(0.4 * f));
    return { ...S.CU_A, pos: pos.toArray(), look: look.toArray() };
  }
  // b04: slow tilt up (+ a hair of zoom out) from Fear's face to the Void's
  const u = ramp(t, TT.b4 - 0.02, TT.b4 + 1.05, 'inOut');
  return mixShot(S.TILT_A, S.TILT_B, u);
}

// ------------------------------------------------------------------------------------------------ Fear
// pose function (passed to the rig so the tuft/scarf secondary motion can look back; clamped to the shot start)
function shotStart(t) {
  const TT = S.T;
  return t < TT.cutIns ? -1e9 : t < TT.cutCU ? TT.cutIns : t < TT.cutTilt ? TT.cutCU : TT.cutTilt;
}
function fearPoseFn(t) { const s0 = shotStart(t); return (tt) => fearPose(Math.max(tt, s0)); }

function fearPose(t) {
  const TT = S.T, B = S.B;
  const { click, b3, b4, turnA, turnB } = TT;
  const still = ramp(t, click, click + 0.08, 'linear');                  // the sobbing stops dead (2 frames)
  const turn = ramp(t, turnA, turnB, 'inOut');
  const finP = B.FIN, doorP = B.FDOOR, finY = B.finYaw, doorY = B.fdoorYaw;
  const pos = [lerp(finP[0], doorP[0], turn), finP[1], lerp(finP[2], doorP[2], turn)];
  const yaw = lerp(finY, doorY, turn);
  const vE = S.vEyes, vC = S.vChest, vH = S.vHem;
  // ---- head: sobbing down at the bars -> lifts at the click -> turns over its left shoulder on "to my fear"
  //      -> (turned round) the eyes climb the cloak in b04, head a beat behind
  const look1 = ramp(t, b3 + 0.08, b3 + 0.6, 'inOut');                   // head turns toward the door/the Void
  const climbE = ramp(t, b4 + 0.05, b4 + 0.95, 'inOut');                 // eyes climb
  const climbH = ramp(t, b4 + 0.25, b4 + 1.15, 'inOut');                 // head follows
  const lookPt = vH.clone().lerp(vC, 0.5).lerp(vE, climbH);
  const head = {
    pitch: lerp(0.32, 0.12, still) * (1 - look1) - 0.05 * look1 - 0.32 * climbH + 0.04 * pulse(t, click, 0.06, 0.1, 0.4),
    roll: 0.1 * still * (1 - look1) * ramp(t, click + 0.1, click + 0.6),
    look: lookPt, track: (0.85 - 0.35 * ramp(t, b4 - 0.3, b4 + 0.4)) * look1,
  };
  const gazeT = b3 - 0.02;
  const gaze = gazeSched(t, [
    [TT.s0 - 1, V3(pos[0] + Math.sin(finY) * 0.5, 0.25, pos[2] + Math.cos(finY) * 0.5)],   // down at the floor beyond the bars
    [TT.doorA + 0.15, () => S.doorPt, 0.12],                                   // the creak: eyes slide toward it
    [TT.doorA + 0.7, V3(pos[0] + Math.sin(finY) * 0.5, 0.45, pos[2] + Math.cos(finY) * 0.5), 0.15], // ...back (not daring)
    [gazeT, () => vC.clone().lerp(vE, 0.15), 0.1],                                          // eyes lead the turn: the door, the Void
    [b4 + 0.05, () => vH.clone().lerp(vC, 0.5).lerp(vE, climbE), 0.02],
  ]);
  // ---- face
  const sobF = FX('sob', { mOpen: 0.35 });
  const frozen = FX('cry', { mOpen: 0.05, mPress: 0.35, mTremble: 0.25, lidU: 0.86, browIn: 1.0, browOut: -0.2, tearL: 0.75, tearR: 0.7 });
  const turned = FX('scared', { lidU: 1.3, mOpen: 0.13, mWide: 0.1, mTeethL: 0.2, mSmile: -0.25, mTremble: 0.3, pupil: 0.9, wet: 0.15, tearL: 0.3, tearR: 0.55 });
  const awe = FX([['wonder', 0.55], ['scared', 0.45]], { mOpen: 0.15, wet: 0.2, tearR: 0.55, saccade: 0.1 });
  let face = mixFace(sobF, frozen, still);
  face = mixFace(face, turned, ramp(t, b3 + 0.06, b3 + 0.45));
  face = mixFace(face, awe, ramp(t, b4 + 0.2, b4 + 1.0));
  face.tearL = Math.max(face.tearL ?? 0, 0.85 * ramp(t, b4 + 0.5, b4 + 0.95, 'in'));     // the hanging tear finally falls
  face.autoBlink = t > b3 ? 0 : 1;
  // ---- body
  const sob = 0.8 * (1 - still);
  const body = {
    cower: lerp(0.45, 0.32, still) * (1 - 0.8 * turn),
    breathe: lerp(1.3, 0.15, still) + 0.3 * ramp(t, b4 + 1.0, b4 + 1.6),
    twist: 0.42 * look1 * (1 - turn),
    lean: -0.06 * climbH, stretch: 0.02 * climbH,
    recoil: 0.06 * pulse(t, click, 0.05, 0.05, 0.3),
  };
  // ---- arms: grip two front bars -> let go during the turn -> hands together at the chest
  const let_ = ramp(t, turnA - 0.1, turnA + 0.35);
  const armL = let_ < 0.999 ? { preset: 'grip', target: S.barL, reach: 1 - let_ } : { preset: 'clasp', from: 'rest', mix: ramp(t, turnA + 0.2, turnB + 0.3) };
  const armR = let_ < 0.999 ? { preset: 'grip', target: S.barR, reach: 1 - let_ } : { preset: 'clasp', from: 'rest', mix: ramp(t, turnA + 0.25, turnB + 0.35) };
  // ---- walk: two tiny shuffle steps while turning round
  const walk = turn > 0 && turn < 1 ? { amount: Math.sin(Math.PI * turn), phase: turn * 1.0, style: 'sneak' } : { amount: 0 };
  const extra = {
    sob, cry: lerp(0.85, 0.45, still) * (1 - 0.5 * ramp(t, b3, b3 + 0.5)), tuftDroop: lerp(0.75, 0.35, still) * (1 - 0.6 * look1),
    tremble: lerp(0.3, 0.45, still) * (1 - 0.4 * climbH), glow: lerp(1.5, 1.12, ramp(t, TT.cutIns - 0.01, TT.cutIns)),
    tuftPerk: 0.25 * look1,
  };
  const blinkAt = [TT.click + 0.02, b4 + 0.98];
  return { pos, yaw, body, head, gaze, face, armL, armR, walk, extra, blinkAt };
}

// ------------------------------------------------------------------------------------------------ the Void
function voidPose(t, st) {
  const TT = S.T, B = S.B;
  const reach = k(t, [[TT.handA, 0], [TT.handB, 1, 'inOut'], [TT.doorA + 0.25, 1], [TT.doorB + 0.6, 0, 'inOut']]);
  const latch = st.set.anchors.cageLatch.clone();
  const toL = latch.clone().sub(toV(B.V)).setY(0).normalize();
  const fingers = toL.clone().multiplyScalar(0.55).add(V3(0, -0.85, 0)).normalize();
  // the fingertip rides the lever as it turns (tiny upward flick at the click)
  const tgt = latch.clone().addScaledVector(fingers, 0.05).add(V3(0, 0.012 + 0.02 * pulse(t, TT.click - 0.25, 0.25, 0.05, 0.35), 0));
  const face = k(t, [
    [TT.s0 - 1, VX('tender', { lidU: 0.78, browIn: 0.55 })],
    [TT.bonus, VX('tender', { lidU: 0.8, browIn: 0.6, mSmile: 0.4 })],
    [TT.handA + 0.2, VX('tender', { lidU: 0.86, browIn: 0.7, mSmile: 0.3, mPress: 0.2 })],         // careful...
    [TT.click + 0.1, VX('tender', { lidU: 0.9, browIn: 0.78, mSmile: 0.36, mPress: 0.25 })],
    [TT.b3 + 0.3, VX('gentle', { lidU: 0.82, browIn: 0.55, mSmile: 0.42, blush: 0.15 })],          // it turns: still, soft
    [TT.b4 + 0.25, VX('gentle', { lidU: 0.6, lidL: 0.42, browIn: 0.45, mSmile: 0.36, blush: 0.2 })],  // lids at half, tiny smile
  ]);
  face.saccade = 0.25; face.autoBlink = t > TT.b3 - 0.2 ? 0 : 0.7;
  const P = voidBowed(t, B, {
    gaze: st.fear,
    face,
    body: { lean: 0.12 + 0.4 * reach, crouch: 0.48 * reach, twist: -0.2 * reach, tilt: -0.08 * reach, breathe: 0.8 * (1 - 0.6 * ramp(t, TT.b3, TT.b3 + 0.4)) },
    head: { pitch: 0.25 - 0.12 * reach, yaw: 0.1 * reach },
    armR: { preset: 'tip', target: tgt, reach, tip: true, fingers: fingers.toArray(), hand: { point: reach, curl: 0.3 + 0.6 * reach, thumb: 0.3 } },
    extra: { stars: lerp(1.0, 1.4, ramp(t, TT.b4, TT.b4 + 0.9)), cosmos: 0.18 * ramp(t, TT.b4 + 0.1, TT.b4 + 1.0), rim: lerp(1.4, 1.15, ramp(t, TT.cutIns - 0.01, TT.cutIns)) },
    blinkAt: [TT.b2 + 0.12, TT.click + 0.35],
  });
  return P;
}

// ------------------------------------------------------------------------------------------------ the magician (hidden)
function magPose(t, st) {
  const B = S.B;
  return { pos: B.LURK, yaw: B.lurkYaw, body: { crouch: 0.85, hunch: 0.2 }, face: MX('lurk'), gaze: st.fear, armR: { preset: 'dagger_low' }, armL: { preset: 'pouch' }, speech: false };
}
