// s19 the_corner_of_its_eye — the Void knows. Only its eyes move; its face stays soft for Fear, and it hums.
//   b01 (silent)  low on the Void's face: a soft gaze down at Fear... then, the head perfectly still, the eyes slide
//        into their far corners toward screen-right (where the magician's hat brim bobs back into view, tiptoeing in
//        reverse); the upper lids flatten, one brow-wisp twitches down at its inner end, a tiny controlled breath.
//   b02 "And the void can see it."   hold: eyes parked in the corners, no blink, the rest of the face kept sweet.
//   b03 "Just, in the corner of its eye."   ECU on its left eye (left foreground), the hat brim + dagger soft at the
//        right edge: the iris quivers in the corner; as the line ends it glides back to Fear, lids lift, smile returns.
//   b05 VOID hum   slow pull back to the dramatic-irony wide: tiny Fear smiling up at the stars (tuft lifts, nose
//        wiped on the scarf), the Void bowed over it humming (hood stars pulse), the magician rising on his toes
//        behind its shoulder, dagger high.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { ROOM, lookFor } from './marks.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, fitShot, mixShot, logDolly, project, cast, ownedGroup, bonusMarks, voidBowed,
  MAGPATH, magTiptoe, magSteps, ensureBonusDecals, clamp, smooth, lerp } from './kit_bonus.js';

let S = null;
const tb = (r) => T(r);

export default {
  id: 's19',
  async setup(app) {
    await loadWords();
    const set = await app.set('BACKROOM');
    const vd = await app.char('VOID'), fear = await app.char('FEAR'), mag = await app.char('MAGICIAN');
    const st = { scene: set.scene, set, vd, fear, mag };
    st.decals = ensureBonusDecals(set);
    S = st.S = statics(st);
    console.log('s19 steps', JSON.stringify(magSteps(T('s18b07'), T('s19b05')).map((x) => [x, (x - T('s18b07')).toFixed(2), (x - T('s19b01')).toFixed(2)])));
    return st;
  },
  async update(t, app, st) {
    st.__t = t;
    const { set, vd, fear, mag } = st;
    cast(app, st.scene, ['VOID', 'FEAR', 'MAGICIAN']);
    const shot = shotAt(t);
    applyShot(app.camera, shot, t, 19);
    set.update(t, { latch: 1, cageDoor: 1 });
    fear.update(t, fearPoseFn(t));
    vd.update(t, voidPose(t, st));
    mag.update(t, magPose(t, st));
    st.look = lookFor('s19', set.look);
  },
};

// ------------------------------------------------------------------------------------------------ times
function times() {
  const b1 = tb('s19b01'), b2 = tb('s19b02'), b3 = tb('s19b03'), b5 = tb('s19b05');
  return {
    s0: tb('s19'), end: tb('s19.end'), b1, b2, b3, b5,
    see: wordT('s19b02', 'see', { fallback: 0.55 }),
    corner: wordT('s19b03', 'corner', { fallback: 0.45 }),
    eyeEnd: wordT('s19b03', 'eye', { which: 'end', fallback: 0.95 }),
    slideA: b1 + 0.5, slideB: b1 + 1.12,           // the eyes slide into the corners (head still)
    cut3: b3 - 0.1, cut5: b5 - 0.08,
  };
}

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { set, vd, fear, mag } = st;
  const out = { T: times() };
  S = out;
  const B = out.B = bonusMarks(set), TT = out.T;
  out.PEEK = ROOM.W(MAGPATH.PEEK);
  vd.update(TT.b2, voidBowed(TT.b2, B, { gaze: toV(B.FDOOR).add(V3(0, 0.6, 0)), head: { yaw: 0.18 } }));
  out.vEyes = vd.anchor('eyes');
  // where the irises park: the far corner toward its left/back (the magician), ~0.66 rad, a hair below level
  { const vy0 = B.vYaw + 0.18, f0 = V3(Math.sin(vy0), 0, Math.cos(vy0)), l0 = V3(Math.cos(vy0), 0, -Math.sin(vy0));
    out.sideGaze = out.vEyes.clone().addScaledVector(f0, 1.0).addScaledVector(l0, 0.8).add(V3(0, -0.2, 0)); }
  const eyeL = vd.face.eyes.find((e) => e.sx > 0) || vd.face.eyes[0];
  out.vEyeL = eyeL.group.getWorldPosition(new THREE.Vector3());
  fear.update(TT.b5, fearPose(TT.b5));
  out.fEyes = fear.anchor('eyes');
  mag.update(TT.b2, magPose(TT.b2, st));
  out.mHat2 = mag.anchor('hat'); out.mHead2 = mag.anchor('head'); out.mDagger2 = mag.anchor('dagger');
  mag.update(TT.b5 + 1.2, magPose(TT.b5 + 1.2, st));
  out.mHead5 = mag.anchor('head');
  const vy = B.vYaw, vf = V3(Math.sin(vy), 0, Math.cos(vy)), vl = V3(Math.cos(vy), 0, -Math.sin(vy));
  // Geometry: the magician is right behind the Void's back-left; a close camera can't hold its face AND his hat. Long
  // lenses from slightly left of its hood axis compress the two: the hat brim just clears its left shoulder.
  const VF = (lat, fwd, h) => toV(B.V).addScaledVector(vf, fwd).addScaledVector(vl, lat).setY(h);
  // b01/b02 low on the Void's face (Fear's low angle), the hat brim at the right edge
  out.LOW = fitShot([[out.vEyes, 290, 400], [out.mHat2, 700, 360, 0.3]], 28, VF(0.85, 5.4, 1.05), out.vEyes, { posReg: 10, free: [0, 0, 0] });
  out.LOW_B = { ...out.LOW, fov: out.LOW.fov - 1.5 };
  // b03 ECU on its left eye (left foreground), long lens, past it the hat brim + dagger soft at the right edge
  out.ECU = fitShot([[out.vEyeL, 250, 400]], 16, VF(0.45, 4.2, 2.0), out.vEyeL, { posReg: 10, free: [0, 0, 0] });
  // b05 the dramatic-irony wide (KICK framing adapted to Fear at the door); pull back into it
  const kick = ROOM.cam('KICK');
  out.WIDE = fitShot([[out.fEyes, 165, 680], [out.vEyes, 330, 370], [out.mHead5, 555, 340, 0.6]], 50, kick.pos, kick.look, { posReg: 10, free: [0, 0, 0] });
  out.WIDE_A = { ...out.WIDE, pos: toV(out.WIDE.pos).lerp(toV(out.vEyes), 0.22).toArray(), fov: 48 };
  console.log('s19 statics', JSON.stringify({ low: out.LOW.err.toFixed(1), ecu: out.ECU.err.toFixed(1), wide: out.WIDE.err.toFixed(1), lowPos: ROOM.L(out.LOW.pos).map((v) => +v.toFixed(2)), ecuPos: ROOM.L(out.ECU.pos).map((v) => +v.toFixed(2)), widePos: ROOM.L(out.WIDE.pos).map((v) => +v.toFixed(2)), hat: project(out.LOW, out.mHat2), hatE: project(out.ECU, out.mHat2) }));
  return out;
}

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const TT = S.T;
  if (t < TT.cut3) return mixShot(S.LOW, S.LOW_B, ramp(t, TT.s0, TT.cut3, 'inOut'));
  if (t < TT.cut5) return { ...S.ECU, pos: toV(S.ECU.pos).lerp(toV(S.vEyeL), 0.04 * ramp(t, TT.cut3, TT.cut5, 'linear')).toArray() };
  const u = ramp(t, TT.cut5, TT.b5 + 1.75, 'inOut');
  return mixShot(S.WIDE_A, S.WIDE, logDolly(u, 0.7, 1.0));
}
function shotStart(t) { const TT = S.T; return t < TT.cut3 ? -1e9 : t < TT.cut5 ? TT.cut3 : TT.cut5; }

// ------------------------------------------------------------------------------------------------ the Void
function voidPose(t, st) {
  const TT = S.T;
  const slide = ramp(t, TT.slideA, TT.slideB, 'inOut');
  const back = ramp(t, TT.eyeEnd + 0.02, TT.eyeEnd + 0.5, 'inOut');          // glides back to Fear as the line ends
  const watch = slide * (1 - back);
  const flat = ramp(t, TT.slideA + 0.35, TT.slideB + 0.15) * (1 - back);
  const quiver = t > TT.b3 && t < TT.eyeEnd ? 0.022 * Math.sin((t - TT.b3) * 2 * Math.PI * 6.5) * ramp(t, TT.b3, TT.b3 + 0.3) : 0;
  const twitch = pulse(t, TT.slideB + 0.08, 0.07, 0.08, 0.3);
  const hum = pulse(t, TT.b5 + 0.05, 0.3, Math.max(0.1, tb('s19b05.end') - TT.b5 - 0.6), 0.35);
  const face = VX('gentle', {
    lidU: lerp(0.68, 0.56, flat) + 0.06 * back, lidL: 0.4 + 0.08 * flat + 0.12 * hum, lidAngry: 0.32 * flat,
    browIn: 0.45 - 0.12 * flat, browInL: 0.45 - 0.12 * flat - 0.45 * twitch, browOut: 0.02,
    mSmile: lerp(0.36, 0.26, watch) + 0.12 * back * (1 - hum) + 0.18 * hum, mPress: 0.12 * watch,
    blush: 0.15 + 0.1 * hum, saccade: 0.08 * (1 - watch), autoBlink: 0,
    gazeYaw: quiver,
    talk: 0.12,
  });
  const pulseStars = hum * (0.5 + 0.5 * Math.sin((t - TT.b5) * 2 * Math.PI * 1.25));
  const fe = st.fear.anchor('eyes');
  const gz = watch > 0 ? fe.lerp(S.sideGaze, smooth(watch)) : fe;
  return voidBowed(t, S.B, {
    gaze: gz, face,
    head: { yaw: t < S.T.cut5 ? 0.18 : 0.32 },
    body: { breathe: 0.45 + 0.6 * hum, swell: 0.03 * pulse(t, TT.slideB + 0.4, 0.25, 0.1, 0.5), tilt: 0.015 * hum * Math.sin((t - TT.b5) * 2 * Math.PI * 0.6) },
    extra: { stars: 1.4 + 0.55 * pulseStars, cosmos: 0.12 + 0.12 * pulseStars, eyeGlow: 1 + 0.08 * pulseStars },
    blinkAt: [back > 0 ? TT.eyeEnd + 0.62 : 1e9, TT.b5 + 1.15],
  });
}

// ------------------------------------------------------------------------------------------------ the magician
function magPose(t, st) {
  const TT = S.T, B = S.B;
  const fearE = S.fEyes || toV(B.FDOOR).add(V3(0, 0.65, 0));
  const tip = magTiptoe(t);
  const atPeek = ramp(t, tip.tBack - 0.1, tip.tBack + 0.35);
  const faceFear = Math.atan2(fearE.x - S.PEEK[0], fearE.z - S.PEEK[2]);
  const yaw = lerp(tip.yaw, faceFear + 0.55, atPeek);
  const rise = ramp(t, TT.b5 + 0.2, TT.b5 + 1.0, 'inOut');                       // up on his toes, dagger high
  const quiv = rise * 0.012 * Math.sin(t * 2 * Math.PI * 5);
  const body = { tiptoe: lerp(0.6, 1.0, rise), crouch: 0.12 - 0.1 * rise, hunch: 0.25 - 0.1 * rise, lean: 0.1 + 0.15 * atPeek, peek: 0.85 * atPeek + 0.15 * rise, tilt: -0.18 * tip.hold };
  return {
    pos: tip.pos, yaw, walk: tip.walk, body,
    head: { follow: 0.2 + 0.2 * atPeek, look: fearE, roll: 0.2 * tip.hold },
    gaze: fearE,
    face: MX(rise > 0.01 ? [['gloat', 0.5 + 0.5 * rise], ['lurk', 0.5 - 0.5 * rise]] : 'lurk', { lidU: 0.85 + 0.25 * rise }),
    armR: { preset: 'dagger_ready', offset: [0, 0.06 + 0.3 * rise + quiv, 0] },
    armL: { preset: 'pouch' },
    extra: { tap: 0.6 * atPeek * (1 - rise) },
    speech: false,
  };
}

// ------------------------------------------------------------------------------------------------ Fear
function fearPoseFn(t) { const s0 = shotStart(t); return (tt) => fearPose(Math.max(tt, s0)); }
function fearPose(t) {
  const TT = S.T, B = S.B;
  const vE = S.vEyes || V3(0, 2, 0);
  const hum = ramp(t, TT.b5 + 0.15, TT.b5 + 0.7);
  const wipe = pulse(t, TT.b5 + 0.85, 0.2, 0.45, 0.3);                           // nose wiped on the scarf
  const wig = wipe * Math.sin((t - TT.b5 - 0.85) * 2 * Math.PI * 2.4);
  const face = mixFace(FX([['wonder', 0.45], ['sniffle', 0.55]], { mOpen: 0.06, wet: 0.8, tearL: 0.55, tearR: 0.4, saccade: 0.1 }),
    FX([['shySmile', 0.6], ['hopeful', 0.4]], { mTremble: 0.25, wet: 0.7, tearL: 0.4, tearR: 0.3, lidU: 0.86, lidL: 0.3 }), hum);
  if (wipe > 0) { face.lidU = lerp(face.lidU, 0.5, wipe); face.mPout = lerp(face.mPout || 0, 0.5, wipe); }
  return {
    pos: B.FDOOR, yaw: B.fdoorYaw,
    body: { lean: -0.05 + 0.08 * wipe, stretch: 0.02, breathe: 1.0 - 0.3 * hum, shrug: 0.2 * wipe },
    head: { look: vE, track: 0.6 * (1 - 0.6 * wipe), pitch: -0.12 + 0.42 * wipe, yaw: 0.12 * wig, roll: 0.06 * hum },
    gaze: wipe > 0.5 ? null : vE,
    face,
    armL: { preset: 'clasp' }, armR: { preset: 'clasp' },
    extra: { cry: 0.3 * (1 - 0.5 * hum), tremble: 0.15 * (1 - 0.6 * hum), tuftPerk: 0.45 * hum, tuftDroop: 0.2 * (1 - hum), glow: 1.1 + 0.15 * hum },
    blinkAt: [TT.b2 + 0.4, TT.b5 + 0.6, TT.b5 + 1.7],
  };
}
