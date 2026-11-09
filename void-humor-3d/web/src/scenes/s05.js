// s05 a_pretty_good_sense_of_humor — the title line. Jesus, still glowing from the laugh, looks down at the terrified
// kid on the ground and tells them the Void is funny, as if that settles everything; then "Tee-hee."
//   b01 JESUS_CU medium: knuckle wipes an eye, the eyes arrive at the user on "looks", the head follows; content exhale.
//   b02 JPOV (Jesus's eyes, axial high angle): the user on their backside, hand up trembling, the little galaxy by the
//       sneaker; the hand jerks higher on "hand up".
//   b03 slow push on the same axis to an ECU of the eyes: whites all round, pinpoint pupils, quivering lower lids, a
//       tear, the sky galaxy turning as a highlight in each iris, no blink.
//   b04 LOWUP (the user's low eyeline): sheepish smile, RIGHT palm presents the Void on "void's", head tilts to it,
//       big warm smile + nod on "humor"; the Void straightens, wisps lift, bashful crescent, "oh stop it" flap.
//   b05 USER_CU: nothing but one slow blink; a tear drips off the chin.
//   b06 JESUS_CU: tee-hee (fingertips to the lips, shoulders scrunch, eyes squeezed, toes bounce); then the smile
//       holds a beat too long: a tiny dart, the corners stiffen, a slow blink.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
import { VX } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, scopeVisible, voidSurface, ensureLittleGalaxy, drawSkyGalaxy, LITTLE_GALAXY, faceSeq, fmix } from './edgeprops.js';
import { fitShot } from './armour_shared.js';
import { M, W, WDIR, speechSafe, aroundTarget, defendTarget, makeIrisGalaxy, makeTearDrop } from './kit_s05_07.js';

const DEBUG = false;
const BELLY = { curl: 0.62, spread: 0.12, cup: 0.5, thumb: 0.4 };

// ---------------------------------------------------------------------------------------------------------- timing
function times() {
  const w = (b, word, fb) => wordT(b, word, fb);
  const S = {
    s: T('s05'), end: T('s05.end'),
    b01: T('s05b01'), looksW: w('s05b01', 'looks', 0.5), userW: w('s05b01', 'user.', 1.46), b01e: T('s05b01.end'),
    b02: T('s05b02'), assW: w('s05b02', 'ass', 0.74), handW: w('s05b02', 'hand', 1.58), upW: w('s05b02', 'up?', 1.84),
    b03: T('s05b03'), terrorW: w('s05b03', 'terror', 0.1), eyesW: w('s05b03', 'eyes.', 0.74), b03e: T('s05b03.end'),
    b04: T('s05b04'), voidsW: w('s05b04', "void's", 0.06), prettyW: w('s05b04', 'pretty', 0.84), goodW: w('s05b04', 'good', 1.08),
    senseW: w('s05b04', 'sense', 1.44), humorW: w('s05b04', 'humor.', 1.92), b04e: T('s05b04.end'),
    b05: T('s05b05'), b06: T('s05b06'), b06e: T('s05b06.end'),
  };
  S.cut2 = S.b02 - 0.06;                 // -> JPOV
  S.cut4 = S.b04 - 0.22;                 // -> LOWUP (the sheepish smile reads before the line)
  S.cut5 = S.b05 - 0.18;                 // -> USER_CU
  S.cut6 = S.b06 - 0.16;                 // -> JESUS_CU (fingertips rise as anticipation)
  S.hic = [S.s + 0.22, S.s + 0.78, S.s + 1.42, S.s + 2.25];   // the Void's giggle aftershocks
  S.blinkU = S.b05 + 0.18;               // the user's one slow blink
  S.dripT0 = S.b05 + 0.05, S.dripF = S.b05 + 0.62;           // the tear slides to the chin, lets go
  S.dart = S.b06e + 0.42, S.stiff = S.b06e + 0.55, S.slowBlink = S.b06e + 0.78;
  return S;
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  const c1a = R.c1a, c1b = R.c1b;
  const pov = R.jpov, ecu = R.ecu;
  const lowA = R.lowA, lowB = R.lowB;
  const ucu = EDGE.shot(EDGE.L(R.uEyes5), { dist: 1.42, yaw: 108, pitch: 4, fov: 33, screenY: sy(420), drift: 0.12 });
  const ucu2 = EDGE.shot(EDGE.L(R.uEyes5), { dist: 1.34, yaw: 108, pitch: 4, fov: 33, screenY: sy(420), drift: 0.12 });
  const c6a = EDGE.shot(EDGE.L(R.jEyes6), { dist: 1.7, yaw: -20, pitch: 1, fov: 33, screenY: sy(400), drift: 0.15 });
  const c6b = EDGE.shot(EDGE.L(R.jEyes6), { dist: 1.58, yaw: -20, pitch: 1, fov: 33, screenY: sy(400), drift: 0.15 });
  const e = 1e-3;
  return [
    [S.s, c1a], [S.cut2 - e, c1b, 'inOut'],
    [S.cut2, pov], [S.b03, pov], [S.b03e + 0.25, ecu, 'inOut'], [S.cut4 - e, ecu],
    [S.cut4, lowA], [S.cut5 - e, lowB, 'inOut'],
    [S.cut5, ucu], [S.cut6 - e, ucu2, 'linear'],
    [S.cut6, c6a], [S.end, c6b, 'out'],
  ];
}

// ---------------------------------------------------------------------------------------------------------- module
export default {
  id: 's05',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const fx = new Particles({ max: 40 });
    scopeVisible(fx.mesh, 's05', 's06');
    set.scene.add(fx.mesh);
    ensureLittleGalaxy(set);                                    // shared prop: lies flat at the sneaker by itself
    const st = { scene: set.scene, set, jesus, vd, user, fx, look: lookFor('s05', set.look) };
    const S = times();
    // user reference (s04's shoulder reference for the raised hand)
    user.update(S.s, { pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.5, hunch: 0.25 } });
    const R = st.R = { userShoulderR: user.anchor('shoulderR') };
    R.toPair = V3(...W(M.V.p)).setY(1.8).sub(R.userShoulderR).normalize().toArray();
    st.iris = makeIrisGalaxy(user, 's05b02', 's05b04');
    st.drop = makeTearDrop(set.scene, 's05b05-0.4', 's06');
    // reference anchors at fixed times (pure)
    const at = (tt) => { poseAll(tt, S, st); return { jE: jesus.anchor('eyes'), vE: vd.anchor('eyes'), uE: user.anchor('eyes'), uH: user.anchor('handR'), uHead: user.anchor('head') }; };
    const a1 = at(S.b01 + 1.0); R.jEyes1 = a1.jE; R.vEyes1 = a1.vE;
    const a2 = at(S.b02 + 0.8); R.uEyes2 = a2.uE; R.uHand2 = a2.uH;
    const a4 = at(S.humorW); R.jEyes4 = a4.jE; R.vEyes4 = a4.vE; R.uEyes4 = a4.uE; R.uHand4 = a4.uH;
    const a5 = at(S.b05 + 0.3); R.uEyes5 = a5.uE;
    const a6 = at(S.b06 + 0.3); R.jEyes6 = a6.jE;
    // b01: medium on Jesus, near-frontal (between where he looks at first, the Void, and where he turns, the user),
    // the giggling Void soft behind-right of him
    const c10 = V3(...EDGE.W(-0.42, 1.62, 1.85));
    R.c1a = fitShot([[R.jEyes1, 300, 470], [R.vEyes1, 520, 190, 0.35]], 40, c10, R.jEyes1, { posReg: 0.6, yMin: 1.4, yMax: 1.9, drift: 0.18 });
    R.c1b = fitShot([[R.jEyes1, 300, 460], [R.vEyes1, 530, 175, 0.35]], 37, toV(R.c1a.pos).addScaledVector(R.jEyes1.clone().sub(toV(R.c1a.pos)).normalize(), 0.18), R.jEyes1, { free: [0, 0, 0], drift: 0.18 });
    // JPOV: from Jesus's eyes (b01 reference) down the axis to the user's eyes; face y~440, the raised hand in frame
    const jp = V3(...EDGE.W(M.JV.p)).add(WDIR(-0.25, 0.25).multiplyScalar(Math.SQRT2 * 0.25)).setY(1.58);
    R.jpov = fitShot([[R.uEyes2, 425, 450], [a2.uH, 150, 360, 0.5]], 38, jp, R.uEyes2, { free: [0, 0, 0], drift: 0.12 });
    const ax = R.uEyes2.clone().sub(jp).normalize();
    const ep = R.uEyes2.clone().addScaledVector(ax, -0.46);
    R.ecu = fitShot([[R.uEyes2, 360, 450]], 33, ep, R.uEyes2, { free: [0, 0, 0], drift: 0.05 });
    // LOWUP: the user's low eyeline, a hair behind their right shoulder: Jesus face ~380, the Void's eyes ~200
    // (the user's own POV: the pair are only ~10 deg apart seen from the user's eyes, so they stack in a portrait frame)
    const toPair = V3(...W(M.JV.p)).sub(R.uEyes4).setY(0).normalize();
    const uy = EDGE.Y(M.U.yaw), uLeft = V3(Math.cos(uy), 0, -Math.sin(uy));
    const l0 = R.uEyes4.clone().addScaledVector(uLeft, 0.2).addScaledVector(toPair, -0.12).add(V3(0, 0.04, 0));
    R.lowA = fitShot([[R.jEyes4, 270, 440], [R.vEyes4, 480, 230]], 36, l0, R.jEyes4, { free: [0, 0, 0], drift: 0.15 });
    R.lowB = fitShot([[R.jEyes4, 272, 430], [R.vEyes4, 482, 215]], 33, l0.clone().addScaledVector(toPair, 0.1), R.jEyes4, { free: [0, 0, 0], drift: 0.15 });
    console.log('s05 fits', R.c1a.err.toFixed(1), R.c1b.err.toFixed(1), R.jpov.err.toFixed(1), R.ecu.err.toFixed(1), R.lowA.err.toFixed(1), R.lowB.err.toFixed(1), JSON.stringify(EDGE.L(R.lowA.pos).map((x) => +x.toFixed(2))), JSON.stringify(EDGE.L(R.c1a.pos).map((x) => +x.toFixed(2))));
    return st;
  },

  async update(t, app, st) {
    const { set, jesus, vd, user, fx } = st;
    st.scene.add(jesus.root, vd.root, user.root);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const S = times();
    applyShot(app.camera, shotAt(t, cams(S, st.R)), t, 5);
    poseAll(t, S, st);
    // props
    st.iris.update(t, ramp(t, S.b03 - 0.1, S.b03 + 0.35));
    st.drop.update(t, user, S.dripT0, S.dripF, -1);
    fx.begin();
    drawSkyGalaxy(fx, t);
    starFx(t, S, st);
    fx.end();
    const two = t >= S.cut4 && t < S.cut5;
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (two ? 1.0 : 0.85), voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]),
      sunGlow: t >= S.cut5 && t < S.cut6 ? 0.6 : 1 });
    st.look = lookFor('s05', set.look);
    if (DEBUG) {
      const pxs = (v) => px(app.camera, v).join(',');
      console.log(`t=${t.toFixed(2)} J.eyes@${pxs(jesus.anchor('eyes'))} V.eyes@${pxs(vd.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} U.handR@${pxs(user.anchor('handR'))} J.handR@${pxs(jesus.anchor('handR'))}`);
    }
  },
};

// ======================================================================================================== poses
function poseAll(t, S, st) {
  const { jesus, vd, user } = st;
  user.update(t, userPose(t, S, st, false));          // pre-pass (static gaze): the user's eyes for the others
  jesus.update(t, jesusPose(t, S, st, null));          // pre-pass (anchors for the Void's hand / gaze)
  vd.update(t, voidPose(t, S, st));
  jesus.update(t, jesusPose(t, S, st, vd));
  user.update(t, userPose(t, S, st, true));            // final: eyes on the real (this-frame) partner anchors
}

// ---------------------------------------------------------------------------------------------------------- particles
function starFx(t, S, st) {
  const { fx, vd } = st;
  // the last of the laugh's drifting stars, fading out by b02 (sparse, slow)
  const fade = 1 - ramp(t, S.b01 + 0.6, S.b02 - 0.1);
  if (fade > 0) {
    const r0 = vd.anchor('hoodTop');
    for (let i = 0; i < 9; i++) {
      const a = i * 2.39996, rr = 0.55 + 0.45 * ((i * 0.618) % 1);
      const p = [r0.x + Math.cos(a) * rr + 0.05 * Math.sin(t * 0.5 + i), r0.y - 0.3 + 0.25 * ((i * 0.37) % 1) + 0.09 * (t - S.s), r0.z + Math.sin(a) * rr];
      fx.add(p, 0.05 + 0.025 * ((i * 0.53) % 1), [0xffffff, 0xe0d4ff, 0xb8f0ff, 0xffe0f4][i % 4], fade * (0.55 + 0.35 * Math.sin(t * 2.3 + i * 1.7)), t * 0.8 + i, CELL.star);
    }
  }
  // the first two aftershock hiccups each squeeze out one tiny star
  const md = vd.anchor('mouthDir'), mo = vd.anchor('mouth');
  [S.hic[0], S.hic[1]].forEach((at, i) => fx.burst({ t, at: at + 0.03, count: 1, seed: 501 + i, life: 1.5, origin: mo.clone().addScaledVector(md, 0.12).toArray(),
    vel: [md.x * 0.25, 0.55, md.z * 0.25], spread: [0.04, 0.03, 0.04], gravity: [0, -0.12, 0], drag: 0.6, size: [0.045, 0.045], grow: 0.4,
    color: [i ? 0xd8f4ff : 0xfff0d8], fade: [0.05, 0.5], cell: CELL.star, twinkle: true, spin: 1 }));
}

// ---------------------------------------------------------------------------------------------------------- Jesus
const JY0 = 0.2, JY1 = -0.28;           // local facing: s04's (toward the Void/camera) -> toward the user
function jesusPose(t, S, st, vd) {
  const { jesus, user } = st;
  const yawL = k(t, [[S.looksW + 0.1, JY0], [S.userW + 0.25, JY1, 'inOut'], [S.b04, JY1], [S.voidsW + 0.1, JY1 + 0.06, 'inOut'], [S.humorW, JY1 + 0.02], [S.b06, JY1 - 0.04]]);
  const P = { pos: W(M.JV.p), yaw: EDGE.Y(yawL), body: {}, head: {}, armR: { preset: 'clasp' } };
  const uE = user.anchor('eyes');
  const vE = vd ? vd.anchor('eyes') : V3(...EDGE.W(0.78, 2.0, -0.7));
  // ---- LEFT arm around the Void (continuing s04: palm on its right flank)
  if (vd) {
    const tg = aroundTarget(vd, jesus, 1.32);
    // one gentle settling pat as the laugh dies; a squeeze on "humor"
    tg.y += 0.03 * pulse(t, S.s + 0.5, 0.1, 0, 0.14) + 0.015 * pulse(t, S.humorW + 0.1, 0.1, 0.1, 0.2);
    P.armL = { preset: 'around', target: tg, reach: 1 };
  }
  // ---- gaze (eyes lead, head follows ~3 frames later with a softer ease)
  const vM = vd ? vd.anchor('mouth') : vE;
  const g = [
    [S.s, vM],
    [S.looksW - 0.02, uE, 0.1],                              // "looks": the eyes arrive first
    [S.voidsW - 0.04, vE, 0.08], [S.prettyW - 0.05, uE, 0.09], // glance at his friend on "void's", back to the user
    [S.b06 + 0.1, uE],
    [S.dart, () => uE.clone().add(V3(0.0, 0.0, 0)).addScaledVector(WDIR(1, 0), 0.12), 0.05], [S.dart + 0.14, uE, 0.05],   // one tiny dart
  ];
  P.gaze = gazeSched(t, g);
  const headLook = gazeSched(t - 0.12, [[S.s, vM], [S.looksW - 0.02, uE, 0.38]]);   // the head only follows the big look
  const follow = k(t, [[S.s, 0.22], [S.looksW, 0.22], [S.userW, 0.72, 'inOut'], [S.b04, 0.72], [S.voidsW, 0.62], [S.goodW + 0.2, 0.75]]);
  P.head = { look: headLook, follow };
  // head tilt toward the Void on "void's" (roll + = toward his left = the Void), nod on "humor", tilt on tee-hee
  const exhale = pulse(t, S.userW + 0.25, 0.22, 0.05, 0.6);
  const tiltV = ramp(t, S.voidsW - 0.05, S.voidsW + 0.3) * (1 - ramp(t, S.senseW, S.humorW + 0.3));
  const nod = pulse(t, S.humorW + 0.02, 0.16, 0.06, 0.3) + 0.5 * pulse(t, S.humorW + 0.5, 0.14, 0.02, 0.3);
  const tee = ramp(t, S.b06 - 0.08, S.b06 + 0.12) * (1 - ramp(t, S.b06e + 0.1, S.b06e + 0.5));
  P.head.roll = 0.13 * tiltV + 0.1 * tee;
  P.head.yaw = 0.1 * tiltV;
  // chin dips while he gets his breath back and wipes the eye, lifts as the eyes find the user
  P.head.pitch = 0.11 * nod + 0.12 * (1 - ramp(t, S.looksW - 0.15, S.looksW + 0.3)) - 0.03 * exhale;
  // ---- body: chuckle tail, content exhale, the presenting lean, the tee-hee scrunch + toe bounce
  P.body.giggle = k(t, [[S.s, 0.55], [S.looksW - 0.1, 0.25], [S.userW, 0.0]]) + 1.0 * tee;
  P.body.shrug = 0.1 * pulse(t, S.userW + 0.05, 0.2, 0.0, 0.2) + 0.35 * tee;
  P.body.breathe = 1 + 1.4 * exhale;
  P.body.recoil = 0.08 * (1 - ramp(t, S.s, S.looksW)) - 0.03 * exhale;
  P.body.lean = 0.04 * ramp(t, S.cut4, S.b04 + 0.3) + 0.025 * nod;
  P.body.tiptoe = 0.35 * (pulse(t, S.b06 + 0.02, 0.08, 0.02, 0.1) + pulse(t, S.b06 + 0.3, 0.08, 0.02, 0.12));
  P.body.tilt = 0.03 * tiltV;
  // ---- RIGHT arm: knuckle wipes one eye -> clasp -> presents the Void, palm up, on "void's" -> clasp -> teehee
  const wipe = ramp(t, S.s, S.s + 0.3) * (1 - ramp(t, S.looksW - 0.25, S.looksW + 0.1));
  if (wipe > 0) {
    const rub = 0.008 * Math.sin((t - S.s) * 2 * Math.PI * 2.2) * ramp(t, S.s + 0.25, S.s + 0.35);
    P.armR = { preset: [['clasp', 1 - wipe], ['wipe_eye', wipe]], offset: [0, (0.035 + rub) * wipe, 0] };
  }
  const pres = ramp(t, S.voidsW - 0.12, S.voidsW + 0.22, 'out') * (1 - ramp(t, S.b04e + 0.15, S.b04e + 0.6));
  if (pres > 0 && vd) {
    const ch = jesus.anchor('chest');
    const toV_ = vd.anchor('chest').sub(ch).setY(0).normalize();
    const toU = uE.clone().sub(ch).setY(0).normalize();
    const tgt = ch.clone().addScaledVector(toV_, 0.3).addScaledVector(toU, 0.26).add(V3(0, -0.04 + 0.03 * nod, 0));
    P.armR = { preset: [['clasp', 1 - pres], ['offer', pres]], target: tgt, reach: Math.max(0.02, pres),
      palm: V3(0, 1, 0).addScaledVector(toU, 0.35).normalize(), fingers: toV_.clone().addScaledVector(toU, 0.3).normalize(),
      hand: { curl: 0.08, spread: 0.32, thumb: 0.6, cup: 0.3, splay: 0.06 } };
  }
  const teeArm = ramp(t, S.b06 - 0.14, S.b06 + 0.16, 'out') * (1 - ramp(t, S.b06e + 0.25, S.b06e + 0.7));
  if (teeArm > 0) P.armR = { preset: [['clasp', 1 - teeArm], ['teehee', teeArm]] };
  // ---- face
  const fChuckle = () => {
    const f = JX('laugh', { mOpen: 0.18, lidU: 0.12, wet: 0.8 });
    const fade = ramp(t, S.s + 0.3, S.looksW);
    return fmix(f, JX('beam', { mOpen: 0.08, wet: 0.8, lidU: 0.6 }), fade);
  };
  const fLook = () => {
    // bright, wet eyes on the user; a contented closed smile after the exhale
    const f = JX('warm', { wet: 0.75, lidU: 0.86, mSmile: 0.72, browIn: 0.3, browOut: 0.22 });
    f.lidU -= 0.12 * exhale; f.lidL += 0.1 * exhale;
    return f;
  };
  const fSheep = () => JX([['warm', 0.7], ['rueful', 0.3]], { mSmile: 0.6, mAsym: 0.18, browIn: 0.45, browOut: 0.32, lidU: 0.92, wet: 0.5 });
  const fTalk = () => {
    const f = JX('warm', { browIn: 0.35, browOut: 0.42, lidU: 1.0, lidL: 0.3, wet: 0.5, mSmile: 0.6 });
    const big = ramp(t, S.senseW + 0.1, S.humorW + 0.15);
    f.mSmile = lerp(f.mSmile, 0.95, big); f.lidL = lerp(f.lidL, 0.55, big); f.browOut += 0.15 * big;
    f.browIn += 0.25 * pulse(t, S.prettyW, 0.08, 0.15, 0.2);       // the lilt on "pretty good"
    return f;
  };
  const fBeam = () => JX('beam', { mOpen: 0.06, mTeethU: 0.6, lidU: 0.8, lidL: 0.55, wet: 0.5 });
  const fTee = () => JX('teehee', {});
  const fHold = () => {
    // eyes open on the user: the smile holds a beat too long, then stiffens a millimetre
    const f = JX('beam', { mOpen: 0.03, mTeethU: 0.85, lidU: 0.82, lidL: 0.55, wet: 0.45, saccade: 0, autoBlink: 0 });
    const s = ramp(t, S.stiff, S.stiff + 0.25);
    f.mSmile -= 0.12 * s; f.mWide += 0.18 * s; f.mPress = 0.2 * s; f.lidL -= 0.18 * s; f.browIn += 0.12 * s; f.mAsym = 0.08 * s;
    return f;
  };
  P.face = faceSeq(t, [
    [S.s, fChuckle], [S.looksW, fLook, 0.3], [S.cut4, fSheep, 0], [S.voidsW - 0.05, fTalk, 0.25], [S.b04e + 0.1, fBeam, 0.3],
    [S.b06 - 0.06, fTee, 0.12], [S.b06e + 0.18, fHold, 0.2],
  ]);
  P.blinkAt = [S.looksW - 0.06, S.b04 + 0.05, S.slowBlink];
  if (t > S.b06e + 0.1) P.face.blink = pulse(t, S.slowBlink, 0.16, 0.08, 0.22);
  if (!(between(t, S.b04 - 0.05, S.b04e + 0.05) || between(t, S.b06 - 0.05, S.b06e + 0.05))) P.speech = false;
  return P;
}
const between = (t, a, b) => t >= a && t < b;

// ---------------------------------------------------------------------------------------------------------- the Void
/** the Void's chest point at rest (world) — never read the rig's own previous-frame anchors (pure frames) */
function vChest() { const vy = EDGE.Y(M.V.yaw); return V3(...W(M.V.p)).add(V3(Math.sin(vy) * 0.87, 1.2, Math.cos(vy) * 0.87)); }
function voidPose(t, S, st) {
  const { jesus, user } = st;
  const P = { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw), body: {}, head: {}, extra: { stars: 1.3 } };
  const jE = jesus.anchor('eyes'), uE = user.anchor('eyes');
  // ---- body: still doubled over a little from s04, aftershock hiccups; straightens, pleased, on "sense of humor"
  const hic = S.hic.reduce((a, h, i) => a + [1, 0.75, 0.5, 0.35][i] * pulse(t, h, 0.05, 0.02, 0.22), 0);
  const straight = ramp(t, S.senseW - 0.05, S.senseW + 0.45, 'out');
  P.body.lean = k(t, [[S.s, 0.19], [S.b02, 0.1, 'out'], [S.b04, 0.07], [S.senseW, 0.06], [S.senseW + 0.45, -0.02, 'out'], [S.humorW + 0.6, 0.01]]) + 0.04 * hic;
  P.body.shrug = 0.32 * hic + 0.12 * pulse(t, S.humorW + 0.08, 0.15, 0.25, 0.4);
  P.body.bounce = 0.012 * hic;
  P.body.stretch = 0.035 * straight * (1 - 0.5 * ramp(t, S.b04e, S.b05));
  P.body.swell = 0.08 * straight * (1 - ramp(t, S.b04e, S.b05 + 0.5));
  P.extra.laugh = k(t, [[S.s, 0.12], [S.b01e, 0.0]]);
  P.extra.motes = 0.8;
  P.head.pitch = 0.1 * (1 - ramp(t, S.s, S.b02)) - 0.06 * straight + 0.05 * hic;
  P.head.roll = 0.05 * pulse(t, S.humorW + 0.1, 0.2, 0.3, 0.5);
  // ---- arms: RIGHT hand leaning on Jesus's shoulder (s04) slides off as he turns; LEFT hand on the belly; the flap
  P.armR = { preset: 'belly', hand: BELLY };
  P.armL = { preset: 'belly', hand: BELLY };
  const flap = ramp(t, S.humorW - 0.12, S.humorW + 0.12, 'out') * (1 - ramp(t, S.humorW + 0.75, S.humorW + 1.15));
  if (flap > 0) {
    const vy = EDGE.Y(M.V.yaw);
    const fw = V3(Math.sin(vy), 0, Math.cos(vy)), rt = V3(-Math.cos(vy), 0, Math.sin(vy));      // its forward / its RIGHT (toward Jesus)
    const ch = vChest();
    const f = Math.sin(clamp((t - S.humorW - 0.05) / 0.5) * Math.PI * 2);                        // two little flaps
    const tg = ch.clone().addScaledVector(fw, 0.38).addScaledVector(rt, -0.12 + 0.07 * f).add(V3(0, 0.12 - 0.05 * Math.abs(f), 0));
    P.armL = { preset: 'belly', target: tg, reach: flap, palm: rt.clone().addScaledVector(fw, 0.4).normalize(), fingers: V3(0, 1, 0).addScaledVector(rt, 0.4 * f).normalize(),
      hand: { curl: 0.15, spread: 0.2, cup: 0.3 } };
  }
  // ---- face: giggle tail (wet arcs) -> curious about who he is looking at -> friendly -> bashful pride -> giggle along
  const fGig = () => {
    const f = VX('giggle', { tearL: 0.25, tearR: 0.25, wet: 1, lidU: 0.3, lidL: 1, mOpen: 0.12 });
    f.mOpen += 0.12 * hic; f.lidU -= 0.1 * hic;
    return f;
  };
  const fCur = () => VX([['happy', 0.6], ['curious', 0.4]], { tearL: 0.15, tearR: 0.15, wet: 0.7, mOpen: 0.04 });
  const fFriend = () => VX('happy', { mOpen: 0.06, lidU: 0.88, lidL: 0.45, wet: 0.5 });
  const fBash = () => VX([['proud', 0.7], ['gentle', 0.3]], { mSmile: 0.62, mAsym: 0.25, browIn: 0.65, browOut: 0.55, lidU: 0.76, lidL: 0.58, blush: 0.55, wet: 0.5, gazePitch: -0.05 });
  const fTee = () => VX('giggle', { mOpen: 0.1, lidU: 0.45, lidL: 0.9, blush: 0.4 });
  P.face = faceSeq(t, [[S.s, fGig], [S.userW + 0.1, fCur, 0.35], [S.b04, fFriend, 0.3], [S.senseW, fBash, 0.3], [S.b06, fTee, 0.2], [S.b06e + 0.3, fFriend, 0.4]]);
  P.face.saccade = 0.2;
  // gaze: Jesus -> (follows his look) the user -> the user; bashful look aside on "humor"; back to the user
  P.gaze = gazeSched(t, [
    [S.s, jE], [S.userW + 0.15, uE, 0.18], [S.humorW + 0.05, () => jE.clone().add(V3(0, -0.35, 0)), 0.12], [S.humorW + 0.9, uE, 0.15],
    [S.b06 + 0.05, jE, 0.1], [S.b06e + 0.4, uE, 0.12],
  ]);
  P.blinkAt = [S.userW + 0.1, S.senseW - 0.1];
  const sp = speechSafe('VOID', t);
  P.speech = sp || false;
  return P;
}

// ---------------------------------------------------------------------------------------------------------- user
function userPose(t, S, st, final) {
  const { jesus, vd } = st;
  const R = st.R;
  const P = {
    pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw),
    body: { sit: 1, sitPath: 'plain', shrug: 0.62, tremble: 0.45, pant: 1, hunch: 0.25, recoil: 0.2, lean: 0.03 },
    armL: { preset: 'prop' },
    extra: { phone: 0.85, tears: 0.55, glisten: 0.35 },
  };
  // the raised RIGHT hand (s04's target), jerking higher on "hand up", trembling harder through b02-b03
  const jerk = pulse(t, S.handW + 0.02, 0.08, 0.25, 0.4);
  const tg = defendTarget(R).add(V3(0, 0.06 * jerk, 0));
  P.armR = { preset: 'defend', tremble: 0.6 + 0.3 * ramp(t, S.b02, S.b02 + 0.3), target: tg, reach: 1, palm: R.toPair };
  // eyes: on the pair (s04 end) -> locked on Jesus once he looks at them; no blinking through the terror close-ups
  const jE = final ? jesus.anchor('eyes') : V3(...EDGE.W(0.0, 1.55, -0.55)), vE = final ? vd.anchor('eyes') : V3(...EDGE.W(0.85, 2.05, -0.9));
  P.gaze = gazeSched(t, [[S.s, () => jE.clone().lerp(vE, 0.5)], [S.looksW + 0.25, () => jE, 0.08]]);
  P.head = { follow: 0.3, pitch: -0.04 };
  P.body.shrug += 0.1 * jerk;
  // face: terror (b02-b03 pushes it to the limit), the b05 stare
  const ter = ramp(t, S.b02, S.terrorW + 0.2);
  const f = UX('terror', { pupil: lerp(0.5, 0.33, ter), lidU: lerp(1.38, 1.5, ter), mOpen: lerp(0.3, 0.38, ter), browIn: 1.0, browSq: 0.6, wet: 1 });
  f.lidL = 0.06 + 0.05 * noise1(t * 9.0, 41) * ter + 0.025 * Math.sin(t * 2 * Math.PI * 7.3) * ter;   // quivering lower lids (low: whites all round)
  f.autoBlink = 0; f.saccade = 0.1;
  // b05: the stare (mouth closes a little: past screaming)
  const stare = ramp(t, S.b04, S.b05);
  f.mOpen = lerp(f.mOpen, 0.2, stare); f.mTremble = lerp(0.6, 0.35, stare);
  f.blink = pulse(t, S.blinkU, 0.22, 0.1, 0.32);
  P.face = f;
  P.extra.tears = lerp(0.55, 0.75, ter);
  P.speech = false;
  return P;
}
