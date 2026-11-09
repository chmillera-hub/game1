// s06 what_the_actual — the user's disbelief explodes exactly as the Void's laugh dies: a comic bleep, a single polite
// star-hiccup, deadpan eyes following it away, and two very different reactions to a swear word.
//   b01+b02 USER_CU (speaking -> readable; the Void's last giggles are heard): an inhale, the head juts + leans on
//       "What", the raised hand flaps once at the pair on "actual", the whole face scrunches on the bleep (3 frames,
//       flinch), the glasses slip, a glare over them; the finger heads for the bridge.
//   b03 VOID_CU: one last hiccup, a tiny star 'pip' floats off; four fingers politely over the mouth; the eyes slide
//       aside: excuse me.
//   b04 USER_CU locked (0.7 s): the finger pushes the glasses home, deadpan half-mast lids; the hiccup star drifts up
//       past the face and only the eyes follow it out of the top of frame. Then the pair two-shot: Jesus's brows rise,
//       'o' -> pressed amused line, a fair-enough nod; the Void, hand over its mouth, eyes Jesus -> user -> narrowed at
//       the user (an idea forming).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
import { VX } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, scopeVisible, ensureLittleGalaxy, drawSkyGalaxy, faceSeq, fmix } from './edgeprops.js';
import { fitShot } from './armour_shared.js';
import { M, W, WDIR, speechSafe, aroundTarget, defendTarget } from './kit_s05_07.js';

const DEBUG = false;
const BELLY = { curl: 0.62, spread: 0.12, cup: 0.5, thumb: 0.4 };
const JYAW = -0.32;                     // Jesus's local facing at JV (s05's end)

// ---------------------------------------------------------------------------------------------------------- timing
function times() {
  const w = (b, word, fb) => wordT(b, word, fb);
  const S = {
    s: T('s06'), end: T('s06.end'),
    b01: T('s06b01'), whatW: w('s06b01', 'what', 0.0), actualW: w('s06b01', 'actual', 0.8), b01e: T('s06b01.end'),
    b03: T('s06b03'), b03e: T('s06b03.end'), b04: T('s06b04'),
  };
  S.bleep = S.b01 + 1.42;                // the bleep tone in the line audio (lip-sync envelope plateau)
  S.hic1 = S.b03 + 0.02; S.hic2 = S.b03 + 0.36;                // the two hiccup peaks of the cough vocal
  S.cut3 = S.b03 - 0.03;                 // -> VOID_CU just before the hiccup
  S.cut4 = S.b04;                        // -> USER_CU locked
  S.cut4b = S.b04 + 0.7;                 // -> the pair two-shot
  S.star0 = S.b04 + 0.12, S.star1 = S.b04 + 0.66;              // the hiccup star crosses the user's frame
  return S;
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  const e = 1e-3;
  const ucu = (ref, d, scr, yaw = 108) => EDGE.shot(EDGE.L(ref), { dist: d, yaw, pitch: 4, fov: 33, screenY: sy(scr), drift: 0.1 });
  const u0 = ucu(R.uEyes0, 1.75, 440, 116), u1 = ucu(R.uEyes1, 1.72, 430, 116), u1b = ucu(R.uEyes1, 1.62, 430, 116);
  const v3a = EDGE.shot(EDGE.L(R.vEyes3), { dist: 2.9, yaw: -32, pitch: -4, fov: 33, screenY: sy(330), drift: 0.12 });
  const v3b = EDGE.shot(EDGE.L(R.vEyes3), { dist: 2.75, yaw: -32, pitch: -4, fov: 33, screenY: sy(330), drift: 0.12 });
  const u4 = { ...ucu(R.uEyes4, 1.6, 430), drift: 0 };          // locked off
  return [
    [S.s, u0], [S.whatW + 0.06, u0], [S.whatW + 0.42, u1, 'inOut'], [S.cut3 - e, u1b, 'linear'],     // the operator follows the lunge
    [S.cut3, v3a], [S.cut4 - e, v3b, 'linear'],
    [S.cut4, u4], [S.cut4b - e, u4],
    [S.cut4b, R.two], [S.end, R.twoB, 'out'],
  ];
}

// ---------------------------------------------------------------------------------------------------------- module
export default {
  id: 's06',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const fx = new Particles({ max: 24 });
    scopeVisible(fx.mesh, 's06', 's07');
    set.scene.add(fx.mesh);
    ensureLittleGalaxy(set);
    const st = { scene: set.scene, set, jesus, vd, user, fx, look: lookFor('s06', set.look) };
    const S = times();
    user.update(S.s, { pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.5, hunch: 0.25 } });
    const R = st.R = { userShoulderR: user.anchor('shoulderR') };
    R.toPair = V3(...W(M.V.p)).setY(1.8).sub(R.userShoulderR).normalize().toArray();
    const at = (tt) => { poseAll(tt, S, st); return { jE: jesus.anchor('eyes'), vE: vd.anchor('eyes'), uE: user.anchor('eyes') }; };
    R.uEyes0 = at(S.s + 0.1).uE;
    R.uEyes1 = at(S.whatW + 0.5).uE;
    R.vEyes3 = at(S.b03 + 0.3).vE;
    R.uEyes4 = at(S.b04 + 0.3).uE;
    const a5 = at(S.cut4b + 0.4);
    // the pair two-shot along the user's eyeline (a little higher): seen from there the pair stack in a portrait frame
    const uy = EDGE.Y(M.U.yaw), uLeft = V3(Math.cos(uy), 0, -Math.sin(uy)), toPair = a5.jE.clone().sub(R.uEyes4).setY(0).normalize();
    const c0 = R.uEyes4.clone().addScaledVector(uLeft, 0.05).addScaledVector(toPair, 0.12).add(V3(0, 0.38, 0));
    R.two = fitShot([[a5.jE, 250, 480], [a5.vE, 500, 255]], 44, c0, a5.jE, { free: [0, 0, 0], drift: 0.15 });
    R.twoB = fitShot([[a5.jE, 248, 470], [a5.vE, 505, 240]], 41, c0.clone().addScaledVector(toPair, 0.12), a5.jE, { free: [0, 0, 0], drift: 0.15 });
    // the star's path across the locked USER_CU frame (built in that camera's screen axes, pure)
    const u4 = EDGE.shot(EDGE.L(R.uEyes4), { dist: 1.6, yaw: 108, pitch: 4, fov: 33, screenY: sy(430) });
    const cp = toV(u4.pos), fwd = toV(u4.look).sub(cp).normalize();
    const rt = V3().crossVectors(fwd, V3(0, 1, 0)).normalize(), up = V3().crossVectors(rt, fwd).normalize();
    const base = R.uEyes4.clone().addScaledVector(fwd, -0.25);          // a plane a little in front of the face
    R.starPath = [base.clone().addScaledVector(rt, 0.15).addScaledVector(up, -0.36), base.clone().addScaledVector(rt, 0.085).addScaledVector(up, -0.02),
      base.clone().addScaledVector(rt, 0.06).addScaledVector(up, 0.38)];
    console.log('s06 fits', R.two.err.toFixed(1), R.twoB.err.toFixed(1));
    return st;
  },

  async update(t, app, st) {
    const { set, jesus, vd, user, fx } = st;
    st.scene.add(jesus.root, vd.root, user.root);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const S = times();
    applyShot(app.camera, shotAt(t, cams(S, st.R)), t, 6);
    poseAll(t, S, st);
    fx.begin();
    drawSkyGalaxy(fx, t);
    // the hiccup star: pops out of the mouth on the first hiccup, floats up and away (toward the user's side)
    const md = vd.anchor('mouthDir');
    fx.burst({ t, at: S.hic1 + 0.03, count: 1, seed: 601, life: 1.1, origin: vd.anchor('mouth').addScaledVector(md, 0.1).toArray(),
      vel: [md.x * 0.35 + 0.1, 0.55, md.z * 0.35], spread: [0.01, 0.01, 0.01], gravity: [0, 0.05, 0], drag: 0.4, size: [0.07, 0.07], grow: 0.2,
      color: [0xfff4d8], fade: [0.04, 0.35], cell: CELL.star, twinkle: true, spin: 1.5 });
    const sp = starPos(t, S, st.R);
    if (sp) fx.add(sp.p.toArray(), 0.05 * sp.s, 0xfff4d8, sp.a, t * 1.5, CELL.star);
    fx.end();
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * 0.85, voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]),
      sunGlow: (t < S.cut3 || (t >= S.cut4 && t < S.cut4b)) ? 0.6 : 1 });
    st.look = lookFor('s06', set.look);
    if (DEBUG) {
      const pxs = (v) => px(app.camera, v).join(',');
      console.log('handR', pxs(user.anchor('handR')));
      console.log(`t=${t.toFixed(2)} J.eyes@${pxs(jesus.anchor('eyes'))} V.eyes@${pxs(vd.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} star ${sp ? pxs(sp.p) : '-'}`);
    }
  },
};

/** the hiccup star drifting up past the user's face (b04), on a gentle S-curve; pure */
function starPos(t, S, R) {
  if (!R.starPath || t < S.star0 - 0.05 || t > S.star1 + 0.1) return null;
  const u = clamp((t - S.star0) / (S.star1 - S.star0));
  const [a, b, c] = R.starPath;
  const v = 1 - u;
  const p = a.clone().multiplyScalar(v * v).addScaledVector(b, 2 * u * v).addScaledVector(c, u * u);
  p.y += 0.01 * Math.sin(u * Math.PI * 3);
  return { p, a: 0.95 * smooth(clamp((t - S.star0 + 0.05) / 0.1)) * (1 - smooth(clamp((t - S.star1) / 0.1))), s: 1 + 0.12 * Math.sin(t * 14) };
}

// ======================================================================================================== poses
function poseAll(t, S, st) {
  const { jesus, vd, user } = st;
  user.update(t, userPose(t, S, st, false));
  jesus.update(t, jesusPose(t, S, st, null));
  vd.update(t, voidPose(t, S, st));
  jesus.update(t, jesusPose(t, S, st, vd));
  user.update(t, userPose(t, S, st, true));
}

// ---------------------------------------------------------------------------------------------------------- Jesus
function jesusPose(t, S, st, vd) {
  const { user } = st;
  const P = { pos: W(M.JV.p), yaw: EDGE.Y(JYAW), body: {}, head: {}, armL: { preset: 'clasp' }, armR: { preset: 'clasp' } };
  const uE = user.anchor('eyes');
  const vE = vd ? vd.anchor('eyes') : V3(...EDGE.W(0.78, 2.1, -0.75));
  // two gentle pats on its back while the user explodes (offscreen; his left arm leaves it before the two-shot)
  if (vd) {
    const off = ramp(t, S.b03, S.b04 + 0.3);
    if (off < 1) {
      const tg = aroundTarget(vd, st.jesus, 1.32);
      tg.y += 0.035 * (pulse(t, S.b01 + 0.5, 0.1, 0, 0.14) + pulse(t, S.b01 + 0.85, 0.1, 0, 0.14));
      P.armL = { preset: 'around', target: tg, reach: 1 - off };
      if (off > 0) P.armL = { preset: [['around', 1 - off], ['clasp', off]], target: tg, reach: 1 - 0.98 * off };
    }
  }
  P.gaze = gazeSched(t, [[S.s, uE], [S.cut4b + 0.55, vE, 0.1], [S.cut4b + 0.75, uE, 0.1]]);
  P.head = { look: uE, follow: 0.7 };
  // the fair-enough nod (slow) after the 'o'
  const nod = pulse(t, S.cut4b + 0.42, 0.22, 0.05, 0.35);
  P.head.pitch = 0.1 * nod;
  P.head.roll = 0.04 * ramp(t, S.cut4b, S.cut4b + 0.4);
  P.body.breathe = 1;
  const fHold = () => JX('beam', { mOpen: 0.03, mTeethU: 0.85, mSmile: 0.82, mWide: 0.18, mPress: 0.2, lidU: 0.82, lidL: 0.37, wet: 0.45, saccade: 0 });
  // two-shot: brows rise slowly; 'o'; -> a pressed, amused line; not offended in the slightest
  const fO = () => {
    const f = JX('oh', { mOpen: 0.12, mRound: 0.85, lidU: 1.12, browIn: 0.55, browOut: 0.65 });
    f.browIn += 0.2 * ramp(t, S.cut4b, S.cut4b + 0.4); f.browOut += 0.2 * ramp(t, S.cut4b, S.cut4b + 0.4);
    return f;
  };
  const fPress = () => JX('pressed', { mSmile: 0.5, browIn: 0.55, browOut: 0.6, lidU: 0.86, lidL: 0.42 });
  P.face = faceSeq(t, [[S.s, fHold], [S.cut4b - 0.15, fO, 0.3], [S.cut4b + 0.4, fPress, 0.3]]);
  P.blinkAt = [S.cut4b + 0.36];
  P.speech = false;
  return P;
}

// ---------------------------------------------------------------------------------------------------------- the Void
function voidPose(t, S, st) {
  const { jesus, user } = st;
  const P = { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw), body: {}, head: {}, extra: { stars: 1.2 }, armL: { preset: 'belly', hand: BELLY }, armR: { preset: 'belly', hand: BELLY } };
  const jE = jesus.anchor('eyes'), uE = user.anchor('eyes');
  const sp = speechSafe('VOID', t);
  const gig = t < S.b03 ? (sp?.open || 0) : 0;
  const h1 = pulse(t, S.hic1 - 0.02, 0.05, 0.03, 0.22), h2 = pulse(t, S.hic2 - 0.02, 0.05, 0.02, 0.2);
  P.body.shrug = 0.25 * gig + 0.4 * h1 + 0.22 * h2;
  P.body.bounce = 0.015 * gig + 0.012 * h1;
  P.body.lean = 0.04 + 0.05 * h1;
  P.head.pitch = 0.04 * h1 - 0.02 * h2;
  P.extra.laugh = 0.12 * (1 - ramp(t, S.b01 + 0.8, S.b03));
  // four fingers over the mouth after the first hiccup (its LEFT hand: the camera side); stays into s07's start
  const cov = ramp(t, S.hic1 + 0.08, S.hic1 + 0.3, 'out');
  if (cov > 0) P.armL = { preset: 'cover_mouth', from: 'belly', mix: cov, hand: { curl: 0.12, cup: 0.4, spread: 0.06 }, offset: [0, 0, -0.01 * h2] };
  // ---- face
  const fGig = () => {
    const f = VX('giggle', { mOpen: 0.1, lidU: 0.35, lidL: 0.95, wet: 0.7, tearL: 0.15, tearR: 0.15 });
    f.lidU -= 0.12 * gig; f.mSmile = 1;
    f.blink = 0;
    return f;
  };
  const fHic = () => {
    const f = VX('surprised', { mOpen: 0.15, mRound: 0.9, mWide: -0.3, lidU: 1.3, pupil: 0.85, browIn: 0.6, browOut: 0.7 });
    return f;
  };
  const fCover = () => {
    // excuse me: lids lower, a blush, eyes slide aside
    const f = VX([['innocent', 0.6], ['gentle', 0.4]], { mSmile: 0.3, mPress: 0.6, lidU: 0.86, lidL: 0.3, blush: 0.55, gazeYaw: 0, gazePitch: 0 });
    f.lidU += 0.25 * h2; f.browIn += 0.25 * h2;
    return f;
  };
  const fNarrow = () => {
    // hand still over its mouth; the eyes narrow at the user: an idea is forming
    const f = VX([['calm', 0.5], ['smug', 0.25], ['sideeye', 0.25]], { gazeYaw: 0, mPress: 0.6, lidU: 0.92, lidL: 0.3, blush: 0.25 });
    const nar = ramp(t, S.cut4b + 0.62, S.cut4b + 0.86, 'out');
    f.lidU = lerp(f.lidU, 0.62, nar); f.lidL = lerp(f.lidL, 0.45, nar); f.browIn = lerp(f.browIn, -0.25, nar); f.browOutL = (f.browOut ?? 0) + 0.25 * nar;
    return f;
  };
  P.face = faceSeq(t, [[S.s, fGig], [S.hic1 - 0.03, fHic, 0.05], [S.hic1 + 0.3, fCover, 0.2], [S.cut4b, fNarrow, 0.25]]);
  P.face.saccade = 0;
  // gaze: the user (offscreen, giggling at them) -> straight out at the hiccup -> aside (excuse me) -> Jesus -> user
  const aside = () => jE.clone().lerp(uE, 0.5).add(V3(0, -0.6, 0)).addScaledVector(WDIR(1, 0.3), 1.6);
  P.gaze = gazeSched(t, [
    [S.s, uE], [S.hic1, () => jE.clone().lerp(uE, 0.5), 0.05], [S.hic2 + 0.15, aside, 0.28],
    [S.cut4b + 0.08, jE, 0.12], [S.cut4b + 0.36, uE, 0.16],
  ]);
  P.blinkAt = [S.hic2 + 0.05, S.cut4b + 0.3];
  P.speech = cov > 0.5 ? false : (sp || false);
  return P;
}

// ---------------------------------------------------------------------------------------------------------- user
function userPose(t, S, st, final) {
  const { jesus, vd } = st;
  const R = st.R;
  const jE = final ? jesus.anchor('eyes') : V3(...EDGE.W(0.0, 1.55, -0.55));
  const vE = final ? vd.anchor('eyes') : V3(...EDGE.W(0.85, 2.05, -0.9));
  const P = {
    pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw),
    body: { sit: 1, sitPath: 'plain', shrug: 0.5, tremble: 0.3, pant: 0.5, hunch: 0.25, recoil: 0.18, lean: 0.03 },
    armL: { preset: 'prop' },
    extra: { phone: 0.85, tears: 0.5, glisten: 0.3 },
  };
  // ---- body: inhale (anticipation) -> jut + lean on "What" -> flinch on the bleep -> sits back for the deadpan
  const inhale = pulse(t, S.s + 0.06, 0.26, 0.04, 0.14);
  const jut = k(t, [[S.whatW - 0.05, 0], [S.whatW + 0.14, 1, 'out'], [S.bleep - 0.05, 0.85], [S.bleep + 0.1, 0.5], [S.b01e, 0.6], [S.b04, 0.15], [S.b04 + 0.3, 0.1]]);
  const flinch = pulse(t, S.bleep - 0.02, 0.04, 0.08, 0.16);
  P.body.jut = jut;
  P.body.lean = 0.03 + 0.22 * jut - 0.06 * inhale;
  P.body.recoil = 0.18 + 0.08 * inhale - 0.12 * jut;
  P.body.shrug = 0.5 + 0.15 * inhale;
  P.body.flinch = 0.5 * flinch;
  P.body.pant = t < S.b04 ? 0.5 : 0.15;
  P.body.tremble = t < S.b04 ? 0.3 : 0.12;
  // ---- the raised RIGHT hand: flaps once at the pair on "actual", snaps back; then heads for the glasses
  // (the hand comes in closer to the face as they lunge: in frame for the flap and the glasses)
  const flap = pulse(t, S.actualW - 0.04, 0.12, 0.05, 0.2);
  const tp = toV(R.toPair).setY(0).normalize();
  const closer = toV(R.userShoulderR).add(V3(0, 0.12, 0)).addScaledVector(tp, 0.3);
  const cw = ramp(t, S.s + 0.05, S.whatW + 0.15) * (1 - ramp(t, S.b04 + 0.3, S.b04 + 0.65));
  const uyR = EDGE.Y(M.U.yaw), uRight = V3(-Math.cos(uyR), 0, Math.sin(uyR));       // their right = outward, clear of the face
  const tg = defendTarget(R).lerp(closer, cw).addScaledVector(uRight, 0.12 * flap).addScaledVector(tp, 0.05 * flap).add(V3(0, 0.05 * flap, 0));
  P.armR = { preset: 'defend', tremble: 0.4, flap, target: tg, reach: 1, palm: R.toPair };
  const toG = ramp(t, S.bleep + 0.24, S.cut3 + 0.05) * (t < S.b04 ? 0.75 : 1) * (1 - ramp(t, S.b04 + 0.24, S.b04 + 0.55));
  if (toG > 0) P.armR = { preset: [['defend', 1 - toG], ['glasses', toG]], tremble: 0.2 * (1 - toG), target: toG < 0.5 ? tg : undefined, reach: 1 };
  // ---- glasses: knocked down the nose by the scrunch, pushed home at the start of b04
  const slip = k(t, [[S.bleep, 0], [S.bleep + 0.08, 0.9, 'out'], [S.b04 + 0.04, 0.9], [S.b04 + 0.2, 0, 'inOut']]);
  P.extra.glassesSlip = slip;
  P.extra.glassesTilt = 0.06 * slip;
  // ---- gaze / head
  const star = starPos(t, S, R);
  P.gaze = gazeSched(t, [[S.s, () => jE], [S.whatW, () => jE.clone().lerp(vE, 0.5), 0.1], [S.bleep + 0.15, () => jE, 0.08], [S.b04, () => jE]]);
  // the eyes (only the eyes) pick the star up as it enters and follow it out of the top of frame
  const pick = ramp(t, S.star0 + 0.02, S.star0 + 0.12);
  if (R.starPath && t >= S.star0 && t < S.cut4b + 0.15) P.gaze = P.gaze.clone().lerp(star ? star.p : R.starPath[2], pick);
  P.head = { follow: t < S.b04 ? 0.3 : 0, pitch: -0.03 };
  // ---- face
  const fStare = () => {
    const f = UX('terror', { pupil: 0.4, lidU: 1.35, lidL: 0.06, mOpen: 0.2, mTremble: 0.3, browIn: 1.0, browSq: 0.6, wet: 1 });
    f.lidU += 0.12 * inhale; f.browOut += 0.2 * inhale; f.mOpen = lerp(f.mOpen, 0.06, inhale);
    return f;
  };
  const fWtf = () => UX('wtf', { lidU: 1.3, lidL: 0.05, wet: 0.8, pupil: 0.55 });
  const fScrunch = () => UX('scrunch', {});
  const fGlare = () => UX('glare', { lidU: 0.68, wet: 0.6 });
  const fDead = () => UX('deadpan', { lidU: 0.5, lidL: 0.12, mPress: 0.45, mSmile: -0.15, saccade: 0, wet: 0.5 });
  P.face = faceSeq(t, [[S.s, fStare], [S.whatW - 0.06, fWtf, 0.1], [S.bleep - 0.02, fScrunch, 0.04], [S.bleep + 0.12, fGlare, 0.12], [S.b04, fDead, 0]]);
  P.face.autoBlink = 0;
  if (t >= S.b04) P.speech = false;
  return P;
}
