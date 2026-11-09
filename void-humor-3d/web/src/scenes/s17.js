// s17 bonus_scene — dissolve from the sunset into the back room of my mind; the Void unlocks Fear's time-out cage.
//   b01 "Okay. ^Bonus scene."   OPEN: far down the dim room, a small lavender glow in a cage (Fear, sobbing at the bars)
//        beside a huge round dark shape with two soft starlight eyes; slow 2 m drift toward them.
//   b02 "Now I'm imagining, when the void opened up the cage,"   INSERT, locked, low through the bars: Fear's sobbing face
//        upper left, the brass latch lower right. The Void's big LEFT mitt comes down from the door side (camera side,
//        never over the dome), ONE fingertip lands on the lever tip and flicks it up: the click on "opened"; Fear's
//        sobbing stops dead (2 frames). The insert holds a beat, then on the creak a constant-rate log-dolly pulls back
//        to the MASTER (cage left, the Void towering, the janitor's corner established back-right) as the door swings.
//   b03 "to my fear..."   CU through the open doorway: Fear's eyes, then its head, come round over its shoulder to the
//        open door (the turn starts during the pull-back, so the cut lands on the eyes); on "my fear" the eyes widen,
//        inner brows up, a tear hangs, a caught breath and a tremble; then it shuffles round to face the doorway.
//   b04 (silent)   long lens from the camera side, tight on Fear's 3/4 face: the tear falls; the eyes start up the cloak,
//        the head a beat behind; tilt up + widen to the two-shot: the Void's soft 3/4 face above (lids at half, tiny
//        smile, utterly still, hood stars kindling), Fear below looking up in wonder.
// The Void is on voidSpot in b01; for b02 it stands 0.62 m nearer the latch, on the camera side (VC = stage (1.6, 0.5):
// probed, its left fingertip cannot reach the latch from voidSpot), hidden by the cut to the locked insert; it is back
// on voidSpot from b03 (off screen in the doorway CU), which is where s18 has it. Fear's FIN is cheated 0.2 m toward
// the latch side of the cage (stage (0.06, 0.06), more frontal) so its face sits above-left of the latch, clear of
// the TIME-OUT tag, in the insert.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { ROOM, lookFor } from './marks.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, fitShot, mixShot, logDolly, project, cast, bonusMarks, voidBowed,
  MAGPATH, BONUS_LIGHTS, bonusLook, clamp, smooth, lerp } from './kit_bonus.js';

let S = null;
const tb = (r) => T(r);
const DBG = () => globalThis.__S17 || {};          // review aid only (camera override); never set in normal renders

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
    S = st.S;
    const { set, vd, fear, mag } = st;
    cast(app, st.scene, ['VOID', 'FEAR', 'MAGICIAN']);
    const shot = DBG().cam || shotAt(t);
    applyShot(app.camera, shot, t, 17);
    // b01: the bare bulb sits just left of the hood in the far wide: soften its glass/halo so its bloom doesn't touch the
    // rim (no 'third eye'); full strength from the insert on
    set.update(t, { latch: latchAt(t), cageDoor: doorAt(t), tagSwing: 0.3 * pulse(t, S.T.click + 0.2, 0.3, 0.6, 0.9),
      lights: { ...BONUS_LIGHTS, ...(t < S.T.cutIns ? { hemi: 2.3, screen: 1.5 } : {}), bulb: t < S.T.cutIns ? 0.62 : 1 } });
    fear.update(t, fearPoseFn(t));
    vd.update(t, voidPose(t, st));
    mag.update(t, magPose(t, st));
    st.look = bonusLook(lookFor('s17', set.look), expAt(t));
  },
};

// ------------------------------------------------------------------------------------------------ times
function times() {
  const b1 = tb('s17b01'), b2 = tb('s17b02'), b3 = tb('s17b03'), b4 = tb('s17b04');
  const opened = wordT('s17b02', 'opened', { fallback: 0.6 });
  const T0 = {
    s0: tb('s17'), end: tb('s17.end'), b1, b2, b3, b4, opened,
    bonus: wordT('s17b01', 'bonus', { fallback: 0.55 }),
    my: wordT('s17b03', 'my', { fallback: 0.15 }), fearW: wordT('s17b03', 'fear', { fallback: 0.3 }),
    fearEnd: wordT('s17b03', 'fear', { which: 'end', fallback: 0.6 }),
  };
  T0.click = opened + 0.06;                              // the lever snaps up (lock_click) on "opened"
  T0.touch = T0.click - 0.42;                            // the fingertip lands on the lever tip
  T0.handA = b2 + 0.3; T0.handB = T0.touch;              // the big hand comes down
  T0.doorA = T0.click + 0.24; T0.doorB = T0.doorA + 1.05;  // creak
  T0.cutIns = b2 - 0.1;
  T0.holdEnd = T0.click + 0.25;                          // the insert stays locked until here
  T0.cutCU = b3 - 0.1;
  T0.cutTilt = b4 - 0.06;
  T0.peekA = T0.doorA + 0.25;                            // Fear's eyes, then head, start round toward the creak
  T0.turnA = T0.fearEnd + 0.12; T0.turnB = b4 - 0.08;    // Fear shuffles round to face the doorway (FIN -> FDOOR)
  return T0;
}
const latchAt = (t) => k(t, [[S.T.click - 0.28, 0], [S.T.click, 1, 'in']]);
const doorAt = (t) => k(t, [[S.T.doorA, 0], [S.T.doorB, 1, 'inOut']]);

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { set, vd, fear, mag } = st;
  const out = { T: times() };
  S = out;
  out.B = bonusMarks(set);
  const B = out.B, TT = out.T;
  // s17's FIN: a little nearer the latch side of the cage and more frontal, so in the insert Fear's sobbing face sits
  // just above-left of the latch, clear of the TIME-OUT tag (b01 / MASTER can't tell the difference)
  { const w = ROOM.W(0.06, 0, 0.06); B.FIN = [w[0], B.plate, w[2]]; B.finYaw = ROOM.Y(-0.2); }
  // the Void's reach spot for the latch (b01-b02): nearer the cage, on the camera side (probed: the left fingertip lands
  // on the lever with the forearm coming in from the door side, outside the dome)
  set.update(TT.b2, { latch: 0, cageDoor: 0 });
  out.latch0 = set.anchors.cageLatch.clone();
  out.VC = ROOM.W(1.6, 0, 0.5);
  out.latchYaw = Math.atan2(out.latch0.x - out.VC[0], out.latch0.z - out.VC[2]);
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
  // representative poses -> eye points
  vd.update(TT.b4 + 1.0, voidPose0(TT.b4 + 1.0, toV(B.FDOOR).add(V3(0, 0.62, 0))));
  out.vEyes = vd.anchor('eyes'); out.vChest = vd.anchor('chest');
  out.vHem = toV(B.V).add(V3(0, 0.55, 0)).addScaledVector(V3(Math.sin(B.vYaw), 0, Math.cos(B.vYaw)), 0.85);
  vd.update(TT.b1, voidPose0(TT.b1, toV(B.FIN).add(V3(0, 0.6, 0))));
  out.vEyesC = vd.anchor('eyes');
  vd.update(TT.cutCU - 0.05, voidPose0(TT.cutCU - 0.05, toV(B.FIN).add(V3(0, 0.6, 0))));
  out.vEyesM = vd.anchor('eyes');
  out.doorPt = set.anchors.cageDoor.clone().setY(0.6 + B.plate);
  fear.update(TT.b2 + 0.8, fearPose(TT.b2 + 0.8));
  out.fEyesFIN = fear.anchor('eyes');
  fear.update(TT.b3 + 0.5, fearPose(TT.b3 + 0.5));
  out.fEyesTurn = fear.anchor('eyes');
  fear.update(TT.b4 + 1.0, fearPose(TT.b4 + 1.0));
  out.fEyesUp = fear.anchor('eyes');
  set.update(TT.b4, { latch: 1, cageDoor: 1 });
  out.bulb = set.anchors.bulb.clone();
  // ---- cameras
  // (the OPEN preset swung ~10 deg toward the camera side so the warm bulb clears the hood: no 'third eye')
  const cOpen = { pos: ROOM.W(-7.3, 1.25, 10.3), look: ROOM.W(1.98, 0.58, -1.16), fov: 44, drift: 0.2 };
  const dirO = toV(cOpen.look).sub(toV(cOpen.pos)).normalize();
  // land Fear's glow near the frame centre (~y 610) for the dissolve from the s16 sun; start past the foreground pillar;
  // keep the warm bulb off the hood (to the left of it)
  const o0 = toV(cOpen.pos).addScaledVector(dirO, 1.3);
  out.OPEN_A = fitShot([[out.fEyesFIN, 330, 610], [out.vEyesC, 440, 470, 0.5]], 44, o0, toV(cOpen.look).addScaledVector(dirO, 1.3), { posReg: 0.08, free: [0, 0, 0] });
  out.OPEN_B = { ...out.OPEN_A, pos: toV(out.OPEN_A.pos).addScaledVector(dirO, 2.0).toArray(), look: toV(out.OPEN_A.look).addScaledVector(dirO, 2.0).toArray() };
  // INSERT (locked): low through the bars from the front-right: Fear's sobbing face upper-left, clear of the tag; the
  // latch lower-right; room above-right for the mitt coming down from the door side
  out.INS = fitShot([[out.fEyesFIN, 320, 420], [out.latch0, 400, 700]], 30, ROOM.W(...DEF.insPos), out.latch0, { posReg: 10, free: [0, 0, 0] });
  out.INS.drift = 0.08;
  // camera-aware bar grips for the insert (a prisoner's grip seen from outside the cell): the hand is behind its bar
  // and just outboard of it, fingers pointing at the lens and curling inward ACROSS THE FRONT of the bar, palm facing
  // Fear's midline; the forearm runs into the hand behind the bar. (The rig's generic grip faces the palm along
  // shoulder->bar, which from this low front-right lens left three finger loops floating beside the bar.)
  // Offsets fit core Hand at size 0.075 with grip 1: the finger loop closes round a point ~(0.035, 0.016) from the
  // wrist; the bar (r 0.0125) sits a little behind it so the curled middle/tip segments lie on its front.
  { const cam = toV(out.INS.pos);
    const grip = (bar, sx) => {
      const fd = cam.clone().sub(bar); fd.y = 0; fd.normalize();                      // fingers: toward the lens
      const pn = V3(0, 1, 0).cross(fd).normalize();                                   // palm: across the view, away
      const sh = fin.clone().addScaledVector(left, 0.17 * sx);                        // from its own shoulder (the
      const out_ = bar.clone().sub(sh); out_.y = 0;                                   // wrist stays on the arm's side
      if (pn.dot(out_) < 0) pn.negate();                                              // of the bar: no arm crossing)
      const wrist = bar.clone().addScaledVector(fd, -0.028).addScaledVector(pn, -0.024);
      return { wrist, palm: pn.toArray(), fingers: fd.toArray() };
    };
    out.gripL = grip(out.barL, 1); out.gripR = grip(out.barR, -1); }
  // MASTER: cage + Fear left, the Void towering, the janitor's corner back-right, the warm bulb clear of the hood
  // (camera position searched offline: the corner clears the Void's silhouette, the bulb clears the hood)
  out.MASTER = fitShot([[out.fEyesFIN, 120, 690], [out.vEyesM, 360, 330], [set.anchors.cornerCenter, 640, 640, 1.0]], 44, ROOM.W(-3.0, 2.2, 8.0), ROOM.cam('MASTER').look, { posReg: 10, free: [0, 0, 0] });
  // b03 CU through the open doorway (Fear turns its head over its shoulder toward it, then shuffles round to face it)
  const cuEye = out.fEyesTurn.clone();
  out.CU_A = ROOM.shot(ROOM.L(cuEye), { ...DEF.cu, drift: 0.12 });
  out.CU_B = ROOM.shot(ROOM.L(out.fEyesUp.clone().lerp(cuEye, 0.5)), { ...DEF.cu, dist: DEF.cu.dist + 0.2, drift: 0.12 });
  // b04: long lens from the camera side: tight on Fear's 3/4 face -> tilt up + widen to the stacked two-shot
  out.TILT_B = fitShot([[out.fEyesUp, 190, 680], [out.vEyes, 520, 250]], 50, ROOM.W(...DEF.tiltPos), out.vEyes, { posReg: 10, free: [0, 0, 0] });
  out.TILT_A = fitShot([[out.fEyesUp, 340, 540]], 13, out.TILT_B.pos, out.fEyesUp, { posReg: 10, free: [0, 0, 0] });
  out.TILT_A.drift = out.TILT_B.drift = 0.08;
  const L3 = (p) => ROOM.L(p).map((v) => +v.toFixed(2));
  console.log('s17 statics', JSON.stringify({ open: project(out.OPEN_A, out.fEyesFIN), ins: [project(out.INS, out.fEyesFIN), project(out.INS, out.latch0), project(out.INS, set.anchors.cageTag), out.INS.err.toFixed(1), L3(out.INS.pos)],
    master: [project(out.MASTER, out.fEyesFIN), project(out.MASTER, out.vEyesM), project(out.MASTER, set.anchors.cornerCenter), project(out.MASTER, out.bulb), out.MASTER.err.toFixed(1)],
    tilt: [out.TILT_B.err.toFixed(1), L3(out.TILT_B.pos)], fEyes: [L3(out.fEyesFIN), L3(out.fEyesTurn), L3(out.fEyesUp)], vEyes: L3(out.vEyes) }));
  return out;
}
// stage-local camera seeds (tuned against renders)
const DEF = {
  insPos: [0.2, 0.3, 1.95],
  cu: { dist: 1.3, yaw: 54, pitch: 2, fov: 33, screenY: 470 / 1280 },
  tiltPos: [1.2, 1.1, 4.8],
};

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const TT = S.T;
  if (t < TT.cutIns) return mixShot(S.OPEN_A, S.OPEN_B, ramp(t, TT.s0 - 0.6, TT.cutIns, 'inOut'));
  if (t < TT.cutCU) {
    // locked insert through the click, then a constant-rate pull back on the creak
    const u = ramp(t, TT.doorA, TT.cutCU + 0.02, 'inOut');
    const d0 = toV(S.INS.pos).distanceTo(toV(S.INS.look)), d1 = toV(S.MASTER.pos).distanceTo(toV(S.MASTER.look));
    return mixShot(S.INS, S.MASTER, logDolly(u, d0, d1));
  }
  if (t < TT.cutTilt) return mixShot(S.CU_A, S.CU_B, ramp(t, TT.turnA, TT.turnB + 0.05, 'inOut'));
  // b04: hold tight on the face while the tear falls, then tilt up + widen
  const u = ramp(t, TT.b4 + 0.32, TT.b4 + 0.98, 'inOut');
  return mixShot(S.TILT_A, S.TILT_B, u);
}

// per-shot exposure (x lookFor): the far wide needs the most; Fear's bright lavender CUs the least; the pull-back and
// the tilt ramp with their moves (no step inside a shot)
function expAt(t) {
  const TT = S.T;
  if (t < TT.cutIns) return 1.6;
  if (t < TT.cutCU) return lerp(1.25, 1.5, ramp(t, TT.doorA, TT.cutCU + 0.02, 'inOut'));
  if (t < TT.cutTilt) return 1.12;
  return lerp(1.2, 1.45, ramp(t, TT.b4 + 0.32, TT.b4 + 0.98, 'inOut'));
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
  const finP = B.FIN, doorP = B.FDOOR, finY = B.finYaw;
  const doorY = B.fdoorYaw - 0.35 * ramp(t, b4 - 0.07, b4 - 0.05);          // b04: cheated 20 deg toward the lens
  const pos = [lerp(finP[0], doorP[0], turn), finP[1], lerp(finP[2], doorP[2], turn)];
  const yaw = lerp(finY, doorY, turn);
  const vE = S.vEyes || V3(0, 2, 0), vC = S.vChest || vE, vH = S.vHem || vE;
  const door = S.doorPt || V3(0, 0.6, 0);
  // ---- head: sobbing down at the bars -> lifts at the click -> eyes then head creep round toward the creak/door
  //      -> on "my fear" all the way over its shoulder -> (turned round) the eyes climb the cloak in b04, head behind
  const peek = ramp(t, TT.peekA + 0.12, TT.cutCU + 0.1, 'inOut');           // head comes round (eyes lead by ~0.15 s)
  const look1 = ramp(t, TT.my - 0.05, TT.fearW + 0.15, 'inOut');           // ...all the way, on "my fear"
  const climbE = ramp(t, b4 + 0.28, b4 + 1.0, 'inOut');                    // eyes climb
  const climbH = ramp(t, b4 + 0.45, b4 + 1.15, 'inOut');                   // head follows
  const lookPt = door.clone().lerp(vH.clone().lerp(vC, 0.5).lerp(vE, climbH), ramp(t, turnA, b4 + 0.3));
  const headTurn = Math.max(0.55 * peek, look1);
  const head = {
    pitch: lerp(0.32, 0.12, still) * (1 - headTurn) - 0.04 * headTurn - 0.3 * climbH + 0.04 * pulse(t, click, 0.06, 0.1, 0.4),
    roll: 0.1 * still * (1 - headTurn) * ramp(t, click + 0.1, click + 0.6),
    look: lookPt, track: 0.88 * headTurn * (1 - 0.35 * turn) + 0.15 * climbH,
  };
  const gaze = gazeSched(t, [
    [TT.s0 - 1, V3(pos[0] + Math.sin(finY) * 0.5, 0.25, pos[2] + Math.cos(finY) * 0.5)],   // down at the floor beyond the bars
    [click + 0.05, V3(pos[0] + Math.sin(finY) * 0.5, 0.45, pos[2] + Math.cos(finY) * 0.5), 0.1],   // ...the click: eyes up a hair
    [TT.peekA, () => door, 0.14],                                           // the creak: eyes slide toward the door
    [TT.my - 0.08, () => door.clone().lerp(vH, 0.3), 0.08],                 // the open door
    [turnA + 0.2, () => door.clone().lerp(vH, 0.6), 0.2],
    [b4 + 0.28, () => vH.clone().lerp(vC, 0.5).lerp(vE, climbE), 0.02],     // up, up, up the cloak
  ]);
  // ---- face
  const sobF = FX('sob', { mOpen: 0.35 });
  const frozen = FX('cry', { mOpen: 0.05, mPress: 0.35, mTremble: 0.25, lidU: 0.86, browIn: 1.0, browOut: -0.2, tearL: 0.75, tearR: 0.7 });
  const listen = FX('scared', { lidU: 1.05, browIn: 0.9, browOut: 0.1, mOpen: 0.04, mPress: 0.2, mTremble: 0.2, tearL: 0.5, tearR: 0.55, wet: 0.5 });
  const turned = FX('scared', { lidU: 1.32, lidL: 0.0, browIn: 1.0, browOut: 0.35, mOpen: 0.16, mWide: -0.05, mRound: 0.25, mSmile: -0.15, mTremble: 0.45, pupil: 1.05, wet: 0.9, tearL: 0.3, tearR: 0.55 });
  const awe = FX([['wonder', 0.7], ['scared', 0.3]], { lidU: 1.25, lidL: 0.0, pupil: 1.45, mOpen: 0.2, mRound: 0.3, browIn: 0.85, browOut: 0.45, wet: 1.0, tearR: 0.55, saccade: 0.05 });
  let face = mixFace(sobF, frozen, still);
  face = mixFace(face, listen, ramp(t, TT.peekA, TT.peekA + 0.4));
  face = mixFace(face, turned, ramp(t, TT.my - 0.02, TT.fearW + 0.12));
  face = mixFace(face, awe, ramp(t, b4 + 0.3, b4 + 0.9));
  face.tearL = Math.max(face.tearL ?? 0, 0.95 * ramp(t, b4 + 0.02, b4 + 0.42, 'in'));     // the hanging tear finally falls
  face.autoBlink = 0;
  // ---- body: a caught breath on "my" (small inhale, then frozen), trembling
  const gasp = pulse(t, TT.my - 0.04, 0.14, TT.fearEnd - TT.my + 0.2, 0.5);
  const sob = 0.8 * (1 - still);
  const body = {
    cower: lerp(0.45, 0.32, still) * (1 - 0.8 * turn),
    breathe: lerp(1.3, 0.12, still) * (1 - 0.8 * gasp) + 0.4 * ramp(t, b4 + 1.0, b4 + 1.5),
    shrug: 0.12 * gasp, stretch: 0.025 * gasp + 0.02 * climbH,
    twist: 0.35 * headTurn * (1 - turn),
    lean: -0.06 * climbH,
    recoil: 0.06 * pulse(t, click, 0.05, 0.05, 0.3),
  };
  // ---- arms: grip two front bars -> let go during the turn -> hands together at the chest
  const let_ = ramp(t, TT.peekA + 0.1, TT.peekA + 0.55);          // lets go of the bars as it straightens up to listen
  // (the hands drop off the bars to its sides as it listens; they come together at the chest as it turns round)
  const gripArm = (G, bar) => (G ? { preset: 'hold', target: G.wrist, palm: G.palm, fingers: G.fingers, shoulder: [0.015, 0.015, 0.02],
    hand: { grip: 1, curl: 0.62, thumb: 0.25, spread: 0.04 }, reach: 1 - let_ } : { preset: 'grip', target: bar, reach: 1 - let_ });
  const armL = let_ < 0.999 ? gripArm(S.gripL, S.barL) : { preset: 'clasp', from: 'rest', mix: ramp(t, turnA - 0.05, turnB - 0.1) };
  const armR = let_ < 0.999 ? gripArm(S.gripR, S.barR) : { preset: 'clasp', from: 'rest', mix: ramp(t, turnA, turnB - 0.05) };
  // ---- walk: two tiny shuffle steps while turning round
  const walk = turn > 0 && turn < 1 ? { amount: Math.sin(Math.PI * turn), phase: turn * 1.0, style: 'sneak' } : { amount: 0 };
  const extra = {
    sob, cry: lerp(0.85, 0.5, still) * (1 - 0.4 * ramp(t, b3, b3 + 0.5)), tuftDroop: lerp(0.75, 0.35, still) * (1 - 0.7 * headTurn),
    tremble: lerp(0.3, 0.5, still) * (1 - 0.5 * climbH) + 0.2 * gasp, glow: lerp(1.5, 1.12, ramp(t, TT.cutIns - 0.01, TT.cutIns)),
    tuftPerk: 0.3 * look1,
  };
  const blinkAt = [TT.click + 0.02, TT.peekA + 0.02, b4 + 1.05];
  return { pos, yaw, body, head, gaze, face, armL, armR, walk, extra, blinkAt };
}

// ------------------------------------------------------------------------------------------------ the Void
function voidPose0(t, gaze) {
  const TT = S.T, B = S.B;
  const atV = t >= TT.cutCU || t < TT.cutIns;
  const P = voidBowed(t, B, atV ? { gaze, head: { pitch: 0.25, yaw: 0.3 } } : { gaze });
  if (!atV) P.pos = S.VC;
  return P;
}
function voidPose(t, st) {
  const TT = S.T, B = S.B;
  const atV = t >= TT.cutCU || t < TT.cutIns;   // on its mark in b01; nearer the latch for b02 (the cut to the insert
                                                // and the doorway CU hide both moves); back on its mark from b03
  const reach = atV ? 0 : k(t, [[TT.handA, 0], [TT.handB, 1, 'inOut'], [TT.click + 0.14, 1], [TT.cutCU - 0.05, 0.3, 'inOut']]);
  const turnIn = atV ? 0 : k(t, [[TT.handA - 0.3, 0], [TT.handB - 0.2, 1, 'inOut'], [TT.click + 0.35, 1], [TT.cutCU, 0.4, 'inOut']]);
  const latch = st.set.anchors.cageLatch.clone();
  // the fingertip rides the lever tip as it flicks up (it is live: follows the turning lever)
  const tgt = latch.clone().add(V3(0, 0.004, 0));
  // the finger comes in from the door side along the cage (never in front of the latch, never over the dome)
  const fingers = ROOM.V(-1, -0.35, -0.2).sub(ROOM.V(0, 0, 0)).normalize();
  const face = k(t, [
    [TT.s0 - 1, VX('tender', { lidU: 0.78, browIn: 0.55 })],
    [TT.bonus, VX('tender', { lidU: 0.8, browIn: 0.6, mSmile: 0.4 })],
    [TT.handA + 0.2, VX('tender', { lidU: 0.84, browIn: 0.7, mSmile: 0.3, mPress: 0.2 })],         // careful...
    [TT.click + 0.1, VX('tender', { lidU: 0.88, browIn: 0.78, mSmile: 0.36, mPress: 0.25 })],
    [TT.b3, VX('gentle', { lidU: 0.72, lidL: 0.35, browIn: 0.55, mSmile: 0.4, blush: 0.15 })],
    [TT.b4 + 0.3, VX('gentle', { lidU: 0.6, lidL: 0.42, browIn: 0.45, mSmile: 0.36, blush: 0.2 })],  // lids at half, tiny smile
  ]);
  face.saccade = 0.15; face.autoBlink = 0;
  const pos = atV ? B.V : S.VC;
  const yaw = atV ? B.vYaw : lerp(B.vYaw, S.latchYaw + 0.12, turnIn);
  const P = voidBowed(t, B, {
    gaze: st.fear,
    face,
    body: { lean: 0.12 + 0.5 * reach, crouch: 0.65 * reach, tilt: -0.04 * reach, breathe: 0.8 * (1 - 0.6 * ramp(t, TT.b3, TT.b3 + 0.4)) },
    head: { pitch: 0.25 - 0.15 * reach, yaw: t >= TT.cutCU ? 0.3 : 0.1 * reach },
    armL: reach > 0.001 ? { preset: 'tip', target: tgt, reach, tip: true, fingers: fingers.toArray(), hand: { point: reach, curl: 0.3 + 0.6 * reach, thumb: 0.3 } } : { preset: 'rest' },
    extra: { stars: lerp(1.0, 1.4, ramp(t, TT.b4 + 0.3, TT.b4 + 1.1)), cosmos: 0.18 * ramp(t, TT.b4 + 0.3, TT.b4 + 1.1), rim: lerp(1.4, 1.15, ramp(t, TT.cutIns - 0.01, TT.cutIns)) },
    blinkAt: [TT.b2 + 0.12, TT.click + 0.35],
  });
  P.pos = pos; P.yaw = yaw;
  return P;
}

// ------------------------------------------------------------------------------------------------ the magician (hidden)
function magPose(t, st) {
  return { pos: ROOM.W(MAGPATH.HIDE), yaw: S.B.lurkYaw, body: { crouch: 1, hunch: 0.2 }, face: MX('lurk'), gaze: st.fear, armR: { preset: 'dagger_low' }, armL: { preset: 'creep' }, speech: false };
}
