// s18 the_magician_lurks — the danger only we can see, right behind the Void's big body.
//   b01 "that right behind the big body of the void,"   slow orbit round the Void (stage yaw -58 -> -24 deg, r 4.0,
//        rising 1.3 -> 1.6 m) from Fear's side toward its left flank: its soft face, then velvet sliding through the frame. The magician, crouched at HIDE pressed to the back
//        of the cloak, stays hidden behind its curve; on "big body" the dented hat rises over its shoulder silhouette
//        against the back wall like a periscope; on "void" the face comes up after it.
//   b02 "the ~depression magician was lurking."   MED, long lens from the camera side: only his head, shoulder and the
//        pouch glove clear the Void's flank; body cheated 3/4 to the lens. The sunken eyes slide toward Fear on
//        "magician", the too-wide grin spreads on "lurking", the moustache twitches twice.
//   b03 "With its dagger, and its numbing dust, ready."   low medium: the dagger rises into clean silhouette above the
//        Void's shoulder on "dagger" (eyes on the blade, glint); the pouch comes up to frame centre on "numbing", shaken
//        on "dust": grey glitter falls, the camera tilts down with it to the floor going grey; fingers wiggle on "ready".
//   b04 "And it's, like, licking its lips, going,"   CU (long lens, 3/4 front): the lick runs along the upper lip under
//        the moustache from "licking", lids drooping heavy with relish, eyes sliding to Fear.
//   b05 MAGICIAN "Ooh. Fear looks very juicy."   same CU, lip-synced whisper: the free glove pinches and twirls the
//        moustache tip ("fear looks"), the eyes half-close with a head tilt on "juicy", then re-open.
//   b06 MAGICIAN "Can't wait to knock Fear out."   camera-side layered wide-angle: his face big at right (an aside to us),
//        the Void's flank in the middle, tiny Fear far left in the open door, unaware: hunch of glee, a pinch of dust,
//        dagger higher on "knock", a glance back over his shoulder at Fear.
//   b07 (silent)   side track: high-kneed stage tiptoe along the Void's flank toward Fear (screen-left), 3 steps that
//        leave grey prints; he freezes on one foot, head cocked, listening; tilt down to the prints.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { ROOM, lookFor } from './marks.js';
import { VX } from '../chars/void.js';
import { FX, mixFace } from '../chars/fear.js';
import { MX } from '../chars/magician.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, fitShot, mixShot, project, cast, ownedGroup, bonusMarks, voidBowed,
  MAGPATH, magTiptoe, magSteps, ensureBonusDecals, clamp, smooth, lerp } from './kit_bonus.js';

let S = null;
const tb = (r) => T(r);
const DBG = () => globalThis.__S18 || {};          // review aid only (camera override); never set in normal renders

export default {
  id: 's18',
  async setup(app) {
    await loadWords();
    const set = await app.set('BACKROOM');
    const vd = await app.char('VOID'), fear = await app.char('FEAR'), mag = await app.char('MAGICIAN');
    const st = { scene: set.scene, set, vd, fear, mag };
    st.own = ownedGroup(st, 's18own'); set.scene.add(st.own);
    st.glint = glintSprite(); st.own.add(st.glint);
    st.decals = ensureBonusDecals(set);
    S = st.S = statics(st);
    console.log('s18 steps', JSON.stringify(magSteps(T('s18b07'), T('s19b05')).map((x) => [x, (x - T('s18b07')).toFixed(2), (x - T('s19b01')).toFixed(2)])));
    return st;
  },
  async update(t, app, st) {
    st.__t = t;
    const { set, vd, fear, mag } = st;
    S = st.S;
    cast(app, st.scene, ['VOID', 'FEAR', 'MAGICIAN']);
    if (st.own.parent !== st.scene) st.scene.add(st.own);
    const shot = DBG().cam || shotAt(t);
    applyShot(app.camera, shot, t, 18);
    const close = t >= S.T.cut2 && t < S.T.cut6;
    // his close shots: the Void's violet key light tints his grey face/tongue purple: half of it (he drains colour)
    set.update(t, { latch: 1, cageDoor: 1, voidLight: close ? 0.55 : 1 });
    fear.update(t, fearPoseFn(t));
    vd.update(t, voidPose(t, st));
    const mp = magPose(t, st);
    mag.update(t, mp);
    if (mp._twirl > 0.01) twirlFix(t, mag, mp);
    // the dagger's glint on "dagger" (and a smaller one as it goes higher on "knock")
    const g = Math.max(pulse(t, S.T.dagger + 0.16, 0.07, 0.07, 0.35), 0.6 * pulse(t, S.T.knock + 0.1, 0.07, 0.05, 0.3));
    st.glint.visible = g > 0.01;
    if (st.glint.visible) {
      const tip = mag.anchor('dagger'), h = mag.anchor('handR');
      st.glint.position.copy(tip.clone().lerp(h, 0.35));
      st.glint.material.opacity = g; st.glint.scale.setScalar(0.05 + 0.13 * g); st.glint.material.rotation = 0.7 * g;
    }
    st.look = lookFor('s18', set.look);
  },
};

// ------------------------------------------------------------------------------------------------ times
function times() {
  const b1 = tb('s18b01'), b2 = tb('s18b02'), b3 = tb('s18b03'), b4 = tb('s18b04'), b5 = tb('s18b05'), b6 = tb('s18b06'), b7 = tb('s18b07');
  const W = (b, w, f, o = {}) => wordT(b, w, { fallback: f, ...o });
  const T0 = {
    s0: tb('s18'), end: tb('s18.end'), b1, b2, b3, b4, b5, b6, b7,
    big: W('s18b01', 'big', 0.45), body: W('s18b01', 'body', 0.55), void1: W('s18b01', 'void', 0.85),
    magician: W('s18b02', 'magician', 0.25), lurking: W('s18b02', 'lurking', 0.7), lurkEnd: W('s18b02', 'lurking', 0.85, { which: 'end' }),
    dagger: W('s18b03', 'dagger', 0.12), numbing: W('s18b03', 'numbing', 0.5), dust: W('s18b03', 'dust', 0.65), ready: W('s18b03', 'ready', 0.75),
    licking: W('s18b04', 'licking', 0.25), lips: W('s18b04', 'lips', 0.55), going: W('s18b04', 'going', 0.65),
    ooh: W('s18b05', 'ooh', 0.05), fearW: W('s18b05', 'fear', 0.35), looks: W('s18b05', 'looks', 0.45), very: W('s18b05', 'very', 0.55),
    juicy: W('s18b05', 'juicy', 0.65), juicyEnd: W('s18b05', 'juicy', 0.8, { which: 'end' }),
    cant: W('s18b06', "can't", 0.05), knock: W('s18b06', 'knock', 0.45), fear6: W('s18b06', 'fear', 0.55), out: W('s18b06', 'out', 0.7),
  };
  // cuts
  T0.cut2 = b2 - 0.04;                 // MED on "the depression magician"
  T0.cut3 = b3 - 0.1;                  // low medium
  T0.cut4 = b4 - 0.02;                 // CU (b04 + b05)
  T0.cut6 = b6 - 0.12;                 // layered
  T0.cut7 = b7 - 0.1;                  // side track
  return T0;
}

// ------------------------------------------------------------------------------------------------ statics
function statics(st) {
  const { set, vd, fear, mag } = st;
  const out = { T: times() };
  S = out;
  const B = out.B = bonusMarks(set), TT = out.T;
  out.HIDE = ROOM.W(MAGPATH.HIDE); out.PEEK = ROOM.W(MAGPATH.PEEK); out.FAR = ROOM.W(MAGPATH.FAR); out.B6 = ROOM.W(MAGPATH.B6);
  vd.update(TT.b3, voidBowed(TT.b3, B, { gaze: toV(B.FDOOR).add(V3(0, 0.6, 0)) }));
  out.vEyes = vd.anchor('eyes'); out.vHead = vd.anchor('head'); out.vShL = vd.anchor('shoulderL');
  out.vC = toV(B.V).setY(1.45);
  fear.update(TT.b3, fearPose(TT.b3));
  out.fEyes = fear.anchor('eyes');
  // facing: toward Fear, cheated toward the camera side (+ = his left)
  const yawTo = (from, to) => Math.atan2(to.x - from[0], to.z - from[2]);
  out.yFearHide = yawTo(out.HIDE, out.fEyes); out.yFearPeek = yawTo(out.PEEK, out.fEyes);
  // representative magician poses -> anchors
  const at = (tt) => { mag.update(tt, magPose(tt, st)); const r = {}; for (const n of ['head', 'eyes', 'hat', 'hip', 'pouch', 'dagger', 'handL', 'handR', 'chest', 'mouth']) r[n] = mag.anchor(n).clone(); return r; };
  out.m1 = at(TT.void1 + 0.3); out.m2 = at(TT.lurking); out.m3 = at(TT.dagger + 0.4); out.m3d = at(TT.dust + 0.1); out.m4 = at(TT.b5 + 0.6); out.m6 = at(TT.knock);
  // ---- cameras
  // b01 orbit round the Void (radius 4.1, height 1.3), local yaw -54 -> -16 deg
  const vL = ROOM.L(B.V);
  out.orbit = (deg, r = 4.1, h = 1.3) => { const a = deg * Math.PI / 180; return ROOM.W(vL[0] + r * Math.sin(a), h, vL[2] + r * Math.cos(a)); };
  // b02 MED: long lens from the camera side, the Void's flank fills the left, his head clears its silhouette
  out.MED = fitShot([[out.m2.eyes, 455, 370]], 25, ROOM.W(...DEF.medPos), out.m2.eyes, { posReg: 10, free: [0, 0, 0] });
  // b03 low medium: face upper third, the pouch hand mid-frame; then tilt down to the floor patch
  out.LOW = fitShot([[out.m3.eyes, 380, 330], [out.m3d.pouch, 470, 590, 0.4]], 40, ROOM.W(...DEF.lowPos), out.m3.eyes, { posReg: 10, free: [0, 0, 0] });
  out.PATCH = ROOM.W(MAGPATH.PATCH);
  out.LOWD = fitShot([[out.m3d.pouch, 440, 400], [toV(out.PATCH), 430, 810, 0.8]], 52, out.LOW.pos, out.m3d.pouch, { posReg: 10, free: [0, 0, 0] });
  // b04/b05 CU: long lens, 3/4 front (from his left-front, clear of the Void)
  out.CU = fitShot([[out.m4.eyes, 390, 380]], 15.5, ROOM.W(...DEF.cuPos), out.m4.eyes, { posReg: 10, free: [0, 0, 0] });
  out.CU_B = fitShot([[out.m4.eyes, 385, 390]], 14.2, toV(out.CU.pos).lerp(out.m4.eyes, 0.03), out.m4.eyes, { posReg: 10, free: [0, 0, 0] });
  // b06 camera-side layered: his face big at right, the Void's flank middle, tiny Fear far left past its front edge
  out.LAY = fitShot([[out.m6.eyes, 525, 420]], 60, ROOM.W(...DEF.layPos), out.m6.eyes, { posReg: 10, free: [0, 0, 0] });
  // b07 side track from his front-right (he crosses screen-left toward Fear)
  out.TRK = (mp) => { const p = toV(mp); return { pos: ROOM.V(...DEF.trkOff).sub(ROOM.V(0, 0, 0)).add(p).toArray(), look: p.clone().setY(1.05).toArray(), fov: 44, drift: 0.15 }; };
  console.log('s18 statics', JSON.stringify({ med: out.MED.err.toFixed(1), low: out.LOW.err.toFixed(1), lowd: out.LOWD.err.toFixed(1), cu: out.CU.err.toFixed(1), lay: out.LAY.err.toFixed(1),
    layPos: ROOM.L(out.LAY.pos).map((v) => +v.toFixed(2)), fearLay: project(out.LAY, out.fEyes), pouch3: ROOM.L(out.m3d.pouch).map((v) => +v.toFixed(2)), m2eyes: ROOM.L(out.m2.eyes).map((v) => +v.toFixed(2)), m6eyes: ROOM.L(out.m6.eyes).map((v) => +v.toFixed(2)) }));
  return out;
}
// stage-local camera seeds (tuned against renders)
const DEF = {
  medPos: [0.6, 1.72, 3.7],
  lowPos: [3.4, 1.12, 2.45],
  cuPos: [3.55, 1.6, 3.45],
  layPos: [3.95, 1.55, 2.65],
  trkOff: [0.55, 0.9, 2.55],
};

// ------------------------------------------------------------------------------------------------ camera
function shotAt(t) {
  const TT = S.T;
  if (t < TT.cut2) {                                           // b01 orbit
    const u = ramp(t, TT.s0 - 0.05, TT.cut2 + 0.25, 'inOut');
    const deg = lerp(-58, -24, u);
    const lookA = S.vHead.clone().setY(1.75), lookB = toV(S.m1.hat).lerp(S.vShL, 0.4).setY(1.62);
    const look = lookA.lerp(lookB, smooth(clamp((u - 0.15) / 0.75)));
    return { pos: S.orbit(deg, 4.0, lerp(1.3, 1.6, u)), look: look.toArray(), fov: 42, drift: 0.15 };
  }
  if (t < TT.cut3) return mixShot(S.MED, { ...S.MED, fov: S.MED.fov - 2 }, ramp(t, TT.cut2, TT.cut3, 'inOut'));
  if (t < TT.cut4) {
    // tilt down with the falling glitter to the floor going grey, back up a little for "ready"
    const d = ramp(t, TT.dust + 0.05, TT.dust + 0.6, 'inOut');
    return mixShot(S.LOW, S.LOWD, d);
  }
  if (t < TT.cut6) return mixShot(S.CU, S.CU_B, ramp(t, TT.cut4, TT.cut6, 'inOut'));
  if (t < TT.cut7) return { ...S.LAY, pos: toV(S.LAY.pos).lerp(toV(S.LAY.look), 0.04 * ramp(t, TT.cut6, TT.cut7, 'linear')).toArray() };
  // b07: track the tiptoe, then tilt down to the prints
  const m = magTiptoe(t);
  const sh = S.TRK(m.pos); sh.fov = 50;
  const down = ramp(t, m.tOut + 0.15, TT.end + 0.05, 'inOut');
  const trail = toV(S.B6).lerp(toV(S.FAR), 0.5).setY(0.0);
  const look = toV(sh.look).lerp(trail, 0.8 * down);
  return { ...sh, look: look.toArray(), fov: 50 - 4 * down };
}
function shotStart(t) {
  const TT = S.T;
  return t < TT.cut2 ? -1e9 : t < TT.cut3 ? TT.cut2 : t < TT.cut4 ? TT.cut3 : t < TT.cut6 ? TT.cut4 : t < TT.cut7 ? TT.cut6 : TT.cut7;
}

// ------------------------------------------------------------------------------------------------ Fear (at the open door, looking up)
function fearPoseFn(t) { const s0 = shotStart(t); return (tt) => fearPose(Math.max(tt, s0)); }
function fearPose(t) {
  const TT = S.T, B = S.B;
  const vE = S.vEyes || V3(0, 2, 0);
  const sn1 = pulse(t, TT.b1 + 0.9, 0.12, 0.05, 0.3), sn2 = pulse(t, TT.knock - 0.1, 0.12, 0.05, 0.35), sn3 = pulse(t, TT.b7 + 0.9, 0.12, 0.05, 0.3);
  const sniff = sn1 + sn2 + sn3;
  const face = mixFace(FX([['wonder', 0.5], ['sniffle', 0.5]], { mOpen: 0.08, wet: 0.9, tearL: 0.6, tearR: 0.45, saccade: 0.12, lidU: 1.05 }),
    FX('sniffle', { mPout: 0.6, lidU: 0.7 }), clamp(sniff));
  return {
    pos: B.FDOOR, yaw: B.fdoorYaw,
    body: { lean: -0.05, stretch: 0.02, breathe: 1.1, shrug: 0.25 * sniff },
    head: { look: vE, track: 0.6, pitch: -0.12 + 0.08 * sniff },
    gaze: vE,
    face,
    armL: { preset: 'clasp' }, armR: { preset: 'clasp' },
    extra: { cry: 0.35, tremble: 0.18, tuftDroop: 0.2, glow: 1.1 },
    blinkAt: [TT.b2 + 0.5, TT.b5 + 1.0, TT.knock + 0.15, TT.b7 + 1.6],
  };
}

// ------------------------------------------------------------------------------------------------ the Void (still, bowed, soft)
function voidPose(t, st) {
  const TT = S.T;
  const face = VX('gentle', { lidU: 0.66, lidL: 0.4, browIn: 0.45, mSmile: 0.34, blush: 0.15, saccade: 0.15, autoBlink: 0 });
  return voidBowed(t, S.B, { gaze: st.fear, face, blinkAt: [TT.b2 + 0.9, TT.b4 + 0.4, TT.b6 + 1.6, TT.b7 + 1.2], extra: { stars: 1.4, cosmos: 0.12 } });
}

// ------------------------------------------------------------------------------------------------ the magician
function magPose(t, st) {
  const TT = S.T;
  const fearE = S.fEyes || V3(-1.3, 0.8, 0.2);
  const inB7 = t >= TT.b7 - 0.05;
  const tip = inB7 ? magTiptoe(t) : null;
  // ---- where / which way: HIDE (b01-b05) -> B6 (b06, across the cut) -> the tiptoe (b07)
  const atPeek = t >= TT.cut6 - 0.02;
  let pos = atPeek ? S.B6 : S.HIDE;
  let yaw;
  if (!atPeek) yaw = S.yFearHide + lerp(0.25, 0.42, ramp(t, TT.b1, TT.cut2)) + 0.22 * ramp(t, TT.cut3 - 0.01, TT.cut3);    // 3/4 to the lens
  else yaw = ROOM.Y(0.35);            // b06: an aside to us, Fear behind his right shoulder
  let walk = { amount: 0 };
  if (inB7) {
    pos = tip.pos;
    yaw = lerp(yaw, tip.yaw, ramp(t, TT.b7 - 0.05, tip.tA + 0.25));
    walk = tip.walk;
  }
  // ---- body
  const rise = k(t, [[TT.big - 0.12, 0], [TT.body + 0.15, 0.6, 'inOut'], [TT.void1 - 0.05, 0.63], [TT.void1 + 0.45, 0.9, 'inOut'], [TT.lurking + 0.1, 1, 'inOut']]);   // periscope
  const lean = ramp(t, TT.void1 - 0.1, TT.void1 + 0.6, 'inOut');                                // leans out round the flank
  const glee = pulse(t, TT.b6 + 0.05, 0.25, TT.out - TT.b6 + 0.15, 0.5);
  const listen = inB7 ? ramp(t, tip.tOut - 0.08, tip.tOut + 0.18) : 0;
  const body = {
    crouch: lerp(1.0, 0.1, rise) + 0.06 * glee + (inB7 ? 0.18 : 0),
    peek: inB7 ? -0.1 : atPeek ? -0.8 : 0.25 + 0.6 * lean,
    hunch: 0.28 + 0.25 * glee - 0.1 * rise + (inB7 ? 0.15 : 0),
    lean: (atPeek ? 0.12 : 0.06) + 0.08 * glee + (inB7 ? 0.1 : 0),
    shrug: 0.5 * glee,
    snicker: 0.7 * glee,
    tiptoe: inB7 ? 0.6 : 0.25 * rise,
    tilt: -0.1 * listen,
  };
  // ---- gaze: forward (the lens side) -> slides to Fear on "magician" -> the blade -> the pouch -> Fear ...
  const daggerP = () => st.mag.anchor('dagger').clone().lerp(st.mag.anchor('handR'), 0.4);
  const fwd = () => { const p = toV(pos); return p.add(V3(Math.sin(yaw) * 2, 1.45, Math.cos(yaw) * 2)); };
  const gaze = gazeSched(t, [
    [TT.s0 - 1, fwd],
    [TT.magician + 0.05, fearE, 0.32],                                // the sunken eyes slide toward Fear (slow, sly)
    [TT.dagger + 0.12, daggerP, 0.1],                                 // ooh, shiny
    [TT.numbing + 0.02, () => st.mag.anchor('pouch'), 0.1],
    [TT.ready + 0.05, fearE, 0.14],
    [TT.cut4, fearE],
    [TT.cant - 0.05, fwd, 0.1],                                       // the aside: to us
    [TT.fear6 - 0.12, fearE, 0.08],                                   // a glance back over his shoulder at Fear
    [TT.out + 0.25, fwd, 0.1],
    [TT.cut7, fearE],
    [tip ? tip.tOut + 0.05 : 1e9, fwd, 0.08],                         // listening: eyes front, wide
  ]);
  const admire = pulse(t, TT.dagger + 0.05, 0.2, 0.55, 0.3);
  const ogle = pulse(t, TT.numbing - 0.05, 0.2, 0.45, 0.3);
  const tiltJ = pulse(t, TT.juicy - 0.12, 0.3, TT.juicyEnd - TT.juicy + 0.2, 0.5);
  const head = {
    follow: 0.12 + 0.1 * lean, look: fearE,
    roll: 0.2 * tiltJ - 0.25 * listen + 0.06 * admire + 0.08 * glee,
    pitch: -0.04 * rise - 0.14 * admire + 0.06 * ogle + 0.05 * tiltJ,
    yaw: 0.22 * admire - 0.5 * pulse(t, TT.fear6 - 0.16, 0.14, 0.3, 0.25) + 0.15 * listen,
  };
  // ---- arms
  const daggerUp = ramp(t, TT.dagger - 0.16, TT.dagger + 0.2, 'out');
  const daggerDown = ramp(t, TT.ready + 0.1, TT.b4, 'inOut');
  const pouchUp = ramp(t, TT.numbing - 0.12, TT.numbing + 0.2, 'out');
  const shake = (t > TT.dust - 0.04 && t < TT.dust + 0.55) ? Math.sin((t - TT.dust) * 2 * Math.PI * 6.5) * (1 - (t - TT.dust) / 0.55) : 0;
  const twirl = pulse(t, TT.fearW - 0.45, 0.35, TT.very - TT.fearW + 0.3, 0.4);
  const higher = ramp(t, TT.knock - 0.2, TT.knock + 0.12, 'out');
  // dagger: held up beside his head, blade up, out over the Void's shoulder line (clean silhouette against the dark)
  const side = V3(Math.cos(yaw), 0, -Math.sin(yaw)), front = V3(Math.sin(yaw), 0, Math.cos(yaw));
  let armR;
  if (t < TT.cut6) {
    const up = daggerUp * (1 - daggerDown);
    // out to his right and up, away from the face: offset (world) on top of the 'dagger_ready' fist-by-the-face
    const off = V3().addScaledVector(side, -0.24 * up).addScaledVector(front, 0.08 * up).add(V3(0, (0.1 + 0.02 * Math.sin((t - TT.dagger) * 3)) * up, 0));
    armR = up > 0.001 ? { preset: [['dagger_low', 1 - up + 1e-4], ['dagger_ready', up]], offset: off.toArray() } : { preset: 'dagger_low' };
  } else if (!inB7) armR = { preset: 'dagger_ready', offset: V3().addScaledVector(side, -0.2).addScaledVector(front, -0.05).add(V3(0, 0.1 + 0.16 * higher, 0)).toArray() };
  else armR = { preset: 'dagger_ready', offset: V3().addScaledVector(side, -0.12).add(V3(0, 0.08, 0)).toArray() };   // dagger up by his ear
  let armL;
  const E = {};
  if (t < TT.numbing - 0.15) armL = { preset: 'creep', reach: clamp(rise * 1.2) };
  else if (t < TT.cut4) armL = { preset: 'pouch', offset: V3().addScaledVector(side, 0.2 * pouchUp).addScaledVector(front, 0.1 * pouchUp).add(V3(0, 0.24 * pouchUp + 0.035 * shake, 0)).toArray() };
  else if (t < TT.cut6) {
    // b04/b05: the pouch tucked away below frame; the free glove comes up and twirls the moustache tip
    E.pouch = twirl > 0.02 ? false : true;
    const tw = Math.sin(clamp((t - TT.fearW) / 0.5) * Math.PI * 2) * twirl;
    armL = twirl > 0.01 ? { preset: [['rest', 1 - twirl + 1e-4], ['whisper', twirl]], offset: [0.01 * tw, -0.02 + 0.012 * tw, 0], hand: { pinch: twirl, curl: 0.5, thumb: 0.8, point: 0.2 } } : { preset: 'rest' };
  } else if (!inB7) armL = { preset: 'pouch', offset: [0, 0.05 * glee, 0] };
  else armL = { preset: 'pouch' };
  // ---- face (baseline lids ~0.62: sunken irises visible; acting goes from there)
  const base = { lidU: 0.66, lidL: 0.14, pupil: 0.95 };
  const face = k(t, [
    [TT.s0 - 1, MX('lurk', { ...base, lidU: 0.7 })],
    [TT.magician - 0.05, MX('lurk', { ...base })],
    [TT.magician + 0.4, MX('lurk', { ...base, lidU: 0.6, lidL: 0.2, browIn: -0.45 })],                     // the slide: lids heavy
    [TT.lurking - 0.05, MX([['lurk', 0.5], ['gloat', 0.5]], { ...base, lidU: 0.58, mTeethU: 0.5 })],
    [TT.lurking + 0.3, MX('gloat', { ...base, lidU: 0.58, lidL: 0.32, mOpen: 0.1 })],                       // the grin spreads
    [TT.dagger + 0.05, MX('gloat', { ...base, lidU: 0.62, lidL: 0.3, mOpen: 0.1 })],
    [TT.dagger + 0.3, MX('curious', { lidU: 0.92, lidL: 0.2, browOut: 0.9, browIn: 0.35, mSmile: 0.75, mWide: 0.6, mOpen: 0.06 })],   // admiring
    [TT.numbing, MX('scheme', { lidU: 0.62, lidL: 0.4, mTeethU: 0.6 })],
    [TT.dust + 0.1, MX('scheme', { lidU: 0.7, lidL: 0.35, mTeethU: 0.8, mSmile: 1 })],
    [TT.ready + 0.1, MX('gloat', { lidU: 0.62, lidL: 0.45 })],
    [TT.cut4, MX('hungry', { lidU: 0.64, lidL: 0.2, mOpen: 0.12, mTongue: 0.2 })],
    [TT.licking - 0.05, MX('hungry', { lidU: 0.6, lidL: 0.22 })],
    [TT.licking + 0.45, MX('hungry', { lidU: 0.36, lidL: 0.42, browIn: 0.6, browOut: 0.05 })],              // relish
    [TT.going + 0.1, MX('hungry', { lidU: 0.42, lidL: 0.4 })],
    [TT.ooh - 0.05, MX('whisper', { lidU: 0.66, lidL: 0.2, talk: 0.95, mRound: 0.45 })],                    // "Ooh"
    [TT.fearW - 0.1, MX('whisper', { lidU: 0.62, lidL: 0.22, talk: 0.95 })],
    [TT.juicy - 0.08, MX('whisper', { lidU: 0.52, lidL: 0.3, talk: 0.95, mSmile: 0.7 })],
    [TT.juicy + 0.18, MX('whisper', { lidU: 0.24, lidL: 0.58, talk: 0.95, mSmile: 0.85, browIn: 0.5 })],   // eyes half-close on "juicy"
    [TT.juicyEnd + 0.35, MX('whisper', { lidU: 0.3, lidL: 0.55, talk: 0.95, mSmile: 0.85 })],
    [TT.juicyEnd + 0.75, MX('gloat', { lidU: 0.66, lidL: 0.4, mOpen: 0.08 })],                               // ...and re-open
    [TT.cut6, MX([['snicker', 0.4], ['gloat', 0.6]], { lidU: 0.62, lidL: 0.5, talk: 0.9 })],
    [TT.knock, MX([['snicker', 0.5], ['gloat', 0.5]], { lidU: 0.7, lidL: 0.45, browOut: 0.9, talk: 0.9 })],
    [TT.out + 0.3, MX('snicker', { lidU: 0.4, talk: 0.8 })],
    [TT.b7 - 0.05, MX('lurk', { ...base, lidU: 0.78 })],
  ]);
  if (inB7) {          // listening on one foot: eyes wide, brows up, lips pressed
    face.lidU = lerp(face.lidU, 1.2, listen); face.lidL = lerp(face.lidL, 0.05, listen); face.browOut = lerp(face.browOut, 0.95, listen); face.browIn = lerp(face.browIn, 0.55, listen);
    face.mPress = 0.45 * listen; face.mSmile = lerp(face.mSmile, 0.35, listen); face.mOpen = face.mOpen * (1 - listen);
  }
  // moustache twitch: two quick smirk flicks after "lurking"
  face.mAsym = (face.mAsym || 0) + 0.45 * pulse(t, TT.lurkEnd + 0.08, 0.05, 0.04, 0.08) - 0.4 * pulse(t, TT.lurkEnd + 0.3, 0.05, 0.04, 0.1);
  face.autoBlink = 0;
  const speech = t > TT.b5 - 0.2 && t < TT.b6 + 2.6 ? undefined : false;
  E.lick = ramp(t, TT.licking, TT.licking + 1.25, 'linear') * (t < TT.ooh - 0.1 ? 1 : 0);
  E.dust = 0.9 * pulse(t, TT.dust - 0.06, 0.1, 0.35, 0.35) + 0.4 * pulse(t, TT.knock - 0.25, 0.12, 0.2, 0.3);
  E.tap = Math.max(pulse(t, TT.ready - 0.02, 0.1, 0.55, 0.25), 0.5 * pulse(t, TT.lurking + 0.4, 0.1, 0.5, 0.3));
  if (t >= TT.cut2 && t < TT.cut3) E.daggerFace = 1;
  return { _twirl: t >= TT.cut4 && t < TT.cut6 ? twirl : 0, _twirlPh: (t - TT.fearW) / 0.55, pos, yaw, body, walk, head, gaze, face, armL, armR, extra: E, speech,
    blinkAt: [TT.magician - 0.02, TT.dagger + 0.02, TT.cut4 + 0.25, TT.ooh + 0.45, TT.cut6 + 0.15, TT.b7 + 0.1] };
}

// the moustache twirl: a second pass puts the glove's pinch (thumb + index tips) ON the left moustache tip, rolling a hair
function twirlFix(t, mag, mp) {
  const mouth = mag.anchor('mouth'), out = mag.anchor('mouthDir'), up = mag.anchor('headUp');
  const left = V3().crossVectors(up, out).normalize();
  const ph = mp._twirlPh * Math.PI * 2;
  const tip = mouth.clone().addScaledVector(left, 0.07).addScaledVector(up, 0.048 + 0.004 * Math.sin(ph)).addScaledVector(out, 0.03 + 0.004 * Math.cos(ph));
  const H = mag.arms.L.hand;
  const pinch = H.tipWorld('thumb').lerp(H.tipWorld(0, V3()), 0.5);
  const wr = mag.root.localToWorld(mag.arms.L.wrist.clone());
  const tgt = wr.add(tip.clone().sub(pinch).multiplyScalar(mp._twirl));
  const fingers = left.clone().multiplyScalar(-0.85).addScaledVector(up, 0.3).addScaledVector(out, 0.25).normalize();
  const palm = out.clone().multiplyScalar(-0.8).addScaledVector(left, -0.15).normalize();
  const P2 = { ...mp, armL: { ...mp.armL, target: tgt.toArray(), offset: undefined, fingers: fingers.toArray(), palm: palm.toArray(), pole: left.clone().addScaledVector(up, -1).addScaledVector(out, 0.3).toArray() } };
  mag.update(t, P2);
  // second correction (the new hand orientation moved the pinch)
  const pinch2 = H.tipWorld('thumb').lerp(H.tipWorld(0, V3()), 0.5);
  const wr2 = mag.root.localToWorld(mag.arms.L.wrist.clone());
  P2.armL.target = wr2.add(tip.sub(pinch2).multiplyScalar(mp._twirl)).toArray();
  mag.update(t, P2);
}

// ------------------------------------------------------------------------------------------------ props
function glintSprite() {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.18, 'rgba(255,255,255,0.7)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  g.fillStyle = 'rgba(255,255,255,0.95)';
  for (const r of [0, Math.PI / 2]) { g.save(); g.translate(32, 32); g.rotate(r); g.beginPath(); g.moveTo(-31, 0); g.quadraticCurveTo(0, 2, 31, 0); g.quadraticCurveTo(0, -2, -31, 0); g.fill(); g.restore(); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.SpriteMaterial({ map: tex, color: 0xe8f0ff, transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending, toneMapped: false });
  const s = new THREE.Sprite(m); s.renderOrder = 8;
  return s;
}
