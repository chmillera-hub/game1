// s07 the_void_whispers — the roles flip: now the Void has the secret, and the user can feel it is about them. Jesus
// listens like a good friend on the phone. The side-eye is slow-burning comic menace, until the whisper slows down and
// turns sincere: under the attitude, the Void is hurt, and the user overhears just enough to feel it.
//   b01-b03 WHISPER (slow push): the Void bends to Jesus's left ear, right hand cupped, soft mouth shapes; Jesus tilts
//       his ear up, eyes up-and-aside, mm-hm nods; +1.0 s into the whisper the Void's eyes slide to the user and park,
//       lids flatten; +2.2 s Jesus's eyes flick to the user and back.
//   b04 ECU of the Void's eye nearest the user: iris parked in the corner, the lid lowers a hair, no blink.
//   b05 over-the-hood: the user meets the side-eye, flinches, scoots back an inch (the iris follows exactly), fake-
//       scrolls fast, peeks once over the glasses.
//   b06-b07 OTS -> slow push on Jesus: steady nods, "oh really?" brows, a polite glance down at the user, a pat on the
//       Void's sleeve, a sympathetic wince, a slow nod. The user shrinks behind the phone.
//   b08 WHISPER: the whisper slows; the side-eye melts into hurt (outer lids droop, wisps up in the middle, the stars
//       in the velvet dim, the cupped hand sags). Jesus's smile fades, brows draw together, eyes up to the Void's.
//   b09 JESUS_CU, hood edge soft at right: "No, I know. That hurts." — his right hand rests flat on its velvet; the
//       Void nods once, slowly.
//   b10 USER_CU closer: the flicker — squint drops, brows lift, two blinks, lips part, thumb stops; eyes slide away.
//   b11 JESUS_CU: small inhale, eyes to the user and back, a quick tight smile; the Void unbends out of frame.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
import { VX, whisperPose } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, scopeVisible, voidSurface, ensureLittleGalaxy, drawSkyGalaxy, faceSeq, fmix } from './edgeprops.js';
import { fitShot, mixShot } from './armour_shared.js';
import { M, W, WDIR, speechSafe, defendTarget, plainDefendWrist, userPosAt } from './kit_s05_07.js';

const DEBUG = false;
const JY0 = -0.32, JY1 = -0.5;          // Jesus's local facing: s06's -> s08's (WY(M.JV))
const DEPTH = 1.15;                      // whisperPose depth (STAGING: mouth just above his left ear)
const HEADYAW = 0.6;                    // fraction of whisperPose's hood yaw kept (the face stays readable to camera)

// ---------------------------------------------------------------------------------------------------------- timing
function times() {
  const w = (b, word, fb) => wordT(b, word, fb);
  const S = {
    s: T('s07'), end: T('s07.end'),
    b01: T('s07b01'), whispersW: w('s07b01', 'whispers', 0.6), earW: w('s07b01', 'ear.', 2.04), b02: T('s07b02'), b02e: T('s07b02.end'), b03e: T('s07b03.end'),
    b04: T('s07b04'), wholeW: w('s07b04', 'whole', 0.2), b04e: T('s07b04.end'),
    b05: T('s07b05'), sideW: w('s07b05', 'side', 0.18), eyeingW: w('s07b05', '-eyeing', 0.38), twitterW: w('s07b05', 'twitter', 0.88), userW: w('s07b05', 'user.', 1.08), b05e: T('s07b05.end'),
    b06: T('s07b06'), justW: w('s07b06', 'just', 0.8), noddingW: w('s07b06', 'nodding', 0.98), alongW: w('s07b06', 'along.', 1.36), b06e: T('s07b06.end'),
    b07e: T('s07b07.end'), b08: T('s07b08'), b08e: T('s07b08.end'),
    b09: T('s07b09'), noW: w('s07b09', 'no,', 0.0), knowW: w('s07b09', 'know', 0.38), b09e: T('s07b09.end'),
    b10: T('s07b10'), b10e: T('s07b10.end'), b11: T('s07b11'), askW: w('s07b11', 'ask', 0.22), b11e: T('s07b11.end'),
  };
  S.thatW = S.b09 + 1.46; S.hurtsW = S.b09 + 1.62;                   // second phrase (lip-sync envelope; Whisper merged it)
  S.slide = S.b02 + 1.0;                                             // the Void's eyes slide to the user
  S.flick = S.b02 + 2.2;                                             // Jesus's eyes flick to the user and back
  S.bendA = S.s + 0.05, S.bendB = S.whispersW + 0.1;                 // the bend
  S.unbend = S.b11 + 0.02;                                           // whisperPose 1 -> 0 over 0.9 s
  // cuts
  S.c4 = S.b04 - 0.05; S.c5 = S.b05 - 0.08; S.c6 = S.b06 - 0.1; S.c8 = S.b08 - 0.05; S.c9 = S.b09 - 0.12; S.c10 = S.b10; S.c11 = S.b11 - 0.12;
  // the user's b05 reaction
  S.meet = S.sideW + 0.02, S.scoot = S.eyeingW + 0.06, S.phone = S.twitterW - 0.05, S.peek = S.userW + 0.18;
  S.peek2 = S.alongW - 0.15;                                         // b06: the user peeks again
  S.glance = S.justW + 0.25;                                          // b06: Jesus's polite glance down at the user
  S.pat = S.alongW + 0.15;                                            // b06/b07: the pat on its sleeve
  return S;
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  const e = 1e-3;
  return [
    [S.s, R.whA], [S.c4 - e, R.whB, 'inOut'],
    [S.c4, R.ecuA], [S.c5 - e, R.ecuB, 'linear'],
    [S.c5, R.hood], [S.c6 - e, R.hoodB, 'linear'],
    [S.c6, R.ots], [S.b06 + 0.6, R.ots], [S.c8 - e, R.otsB, 'inOut'],
    [S.c8, R.wh8], [S.c9 - e, R.wh8b, 'linear'],
    [S.c9, R.j9], [S.c10 - e, R.j9b, 'linear'],
    [S.c10, R.u10], [S.c11 - e, R.u10b, 'linear'],
    [S.c11, R.j11], [S.end, R.j11b, 'out'],
  ];
}

// ---------------------------------------------------------------------------------------------------------- module
export default {
  id: 's07',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const fx = new Particles({ max: 24 });
    scopeVisible(fx.mesh, 's07', 's08');
    set.scene.add(fx.mesh);
    ensureLittleGalaxy(set);
    const st = { scene: set.scene, set, jesus, vd, user, fx, look: lookFor('s07', set.look) };
    const S = times();
    user.update(S.s, { pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.5, hunch: 0.25 } });
    const R = st.R = { userShoulderR: user.anchor('shoulderR') };
    R.toPair = V3(...W(M.V.p)).setY(1.8).sub(R.userShoulderR).normalize().toArray();
    R.plainDefend = plainDefendWrist(user, S.end, { pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, sitPath: 'plain', tremble: 0, hunch: 0.3, shrug: 0.15 } });
    const at = (tt) => { poseAll(tt, S, st); return { jE: jesus.anchor('eyes'), vE: vd.anchor('eyes'), uE: user.anchor('eyes'), vEyeR: vd.face.eyes[1].group.getWorldPosition(V3()), vEyeL: vd.face.eyes[0].group.getWorldPosition(V3()), vHead: vd.anchor('head'), vDir: vd.anchor('mouthDir'), jH: jesus.anchor('handL') }; };
    const a1 = at(S.b02 + 2.0);
    // WHISPER: front 3/4 on the two heads; slow push to ~80 %
    R.whA = fitShot([[a1.jE, 300, 470], [a1.vE, 450, 300]], 33, V3(...EDGE.W(-1.09, 1.40, 3.30)), a1.jE, { posReg: 0.2, yMin: 1.2, yMax: 1.8, drift: 0.15 });
    const mid = a1.jE.clone().lerp(a1.vE, 0.5);
    R.whB = { ...R.whA, pos: toV(R.whA.pos).lerp(mid, 0.2).toArray() };
    R.wh8 = fitShot([[a1.jE, 290, 420], [a1.vE, 450, 300]], 33, toV(R.whA.pos).lerp(mid, 0.22), a1.jE, { posReg: 0.5, yMin: 1.2, yMax: 1.8, drift: 0.12 });
    R.wh8b = { ...R.wh8, pos: toV(R.wh8.pos).lerp(mid, 0.06).toArray() };
    // b04 ECU of its RIGHT eye (nearest the user), frontal to the hood
    const a4 = at(S.b04 + 0.5);
    // (its LEFT eye: the right one is behind the cupped hand from every camera-side angle)
    const toCam = toV(R.whA.pos).sub(a4.vEyeL).normalize().add(V3(0, 0.08, 0)).normalize();
    const ecuPos = a4.vEyeL.clone().addScaledVector(toCam, 1.9);
    R.ecuDbg = a4.vEyeL.clone();
    R.ecuA = fitShot([[a4.vEyeL, 400, 420]], 21, ecuPos, a4.vEyeL, { free: [0, 0, 0], drift: 0.04 });
    R.ecuB = fitShot([[a4.vEyeL, 400, 420]], 20, ecuPos.clone().addScaledVector(toCam, -0.12), a4.vEyeL, { free: [0, 0, 0], drift: 0.04 });
    // b05 over the hood: from just beside the Void's left eye, looking at the user (user face ~560, the eye glow at right)
    const a5 = at(S.b05 + 0.8);
    const loc = (x, y, z) => V3(...EDGE.W(x, y, z)).sub(V3(...EDGE.W(0, 0, 0)));
    const hp = a5.vHead.clone().add(loc(0.62, 0.42, 0.05));
    R.hood = fitShot([[a5.uE, 300, 560]], 25, hp, a5.uE, { free: [0, 0, 0], drift: 0.08 });
    R.hoodB = fitShot([[a5.uE, 302, 552]], 23, hp.clone().lerp(a5.uE, 0.04), a5.uE, { free: [0, 0, 0], drift: 0.08 });
    R.hoodP = hp;
    // b06 OTS (user small lower-left) -> slow push on Jesus (face ~400)
    const a6 = at(S.b06 + 1.2);
    R.ots = EDGE.cam('OTS', { drift: 0.2 });
    R.otsB = fitShot([[a6.jE, 330, 400], [a6.vE, 520, 250, 0.3]], 30, toV(R.ots.pos).lerp(a6.jE, 0.35), a6.jE, { posReg: 0.3, drift: 0.15 });
    // b09 / b11 JESUS_CU, the hood edge soft in the right foreground
    const a9 = at(S.b09 + 1.0);
    const j9p = V3(...EDGE.shot(EDGE.L(a9.jE), { dist: 1.9, yaw: -8, pitch: 1, fov: 33, screenY: sy(400) }).pos);
    R.j9 = fitShot([[a9.jE, 290, 400], [a9.jH, 520, 620, 0.6]], 33, j9p, a9.jE, { free: [0, 0, 0], drift: 0.1 });
    R.j9b = fitShot([[a9.jE, 292, 395], [a9.jH, 525, 620, 0.6]], 31, j9p, a9.jE, { free: [0, 0, 0], drift: 0.1 });
    const a11 = at(S.b11 + 0.3);
    R.j11 = EDGE.shot(EDGE.L(a11.jE), { dist: 1.6, yaw: -20, pitch: 1, fov: 33, screenY: sy(420), drift: 0.1 });
    R.j11b = EDGE.shot(EDGE.L(a11.jE), { dist: 1.52, yaw: -20, pitch: 1, fov: 33, screenY: sy(420), drift: 0.1 });
    // b10 USER_CU closer
    const a10 = at(S.b10 + 0.4);
    R.u10 = EDGE.shot(EDGE.L(a10.uE), { dist: 1.4, yaw: 112, pitch: 4, fov: 33, screenY: sy(400), drift: 0.08 });
    R.u10b = EDGE.shot(EDGE.L(a10.uE), { dist: 1.32, yaw: 112, pitch: 4, fov: 33, screenY: sy(400), drift: 0.08 });
    console.log('s07 fits', R.whA.err.toFixed(1), R.wh8.err.toFixed(1), R.hood.err.toFixed(1), R.otsB.err.toFixed(1), R.j9.err.toFixed(1));
    return st;
  },

  async update(t, app, st) {
    const { set, jesus, vd, user, fx } = st;
    st.scene.add(jesus.root, vd.root, user.root);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const S = times();
    applyShot(app.camera, shotAt(t, cams(S, st.R)), t, 7);
    poseAll(t, S, st);
    fx.begin();
    drawSkyGalaxy(fx, t);
    fx.end();
    const close = (t >= S.c4 && t < S.c6) || t >= S.c9;
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (close ? 0.75 : 0.9), voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]),
      sunGlow: (t >= S.c10 && t < S.c11) ? 0.6 : 1 });
    st.look = lookFor('s07', set.look);
    if (DEBUG) {
      const pxs = (v) => px(app.camera, v).join(',');
      const ear = jesus.anchor('earL'), wh = vd.anchor('whisper');
      const eR = vd.face.eyes[1].group.getWorldPosition(V3()), eL = vd.face.eyes[0].group.getWorldPosition(V3());
      const yl = EDGE.Y(-0.12), jc = jesus.anchor('chest');
      const tgt = velvetNear(vd, jc.clone().addScaledVector(V3(Math.cos(yl), 0, -Math.sin(yl)), 0.28).addScaledVector(V3(Math.sin(yl), 0, Math.cos(yl)), 0.12).add(V3(0, 0.16, 0))).p;
      const js = jesus.anchor('shoulderR'), jl = jesus.anchor('shoulderL');
      { const vn = velvetNear(vd, jesus.anchor('shoulderL').addScaledVector(V3(...W(M.V.p)).sub(V3(...W(M.JV.p))).setY(0).normalize(), 0.3).add(V3(0, -0.12, 0)));
        console.log('velvet', vn.y.toFixed(2), vn.a.toFixed(2), 'from shL', vn.p.distanceTo(jesus.anchor('shoulderL')).toFixed(2), 'hL', jesus.anchor('handL').distanceTo(vn.p).toFixed(2), '@', pxs(vn.p)); }
      console.log('hands', 'J.R', pxs(jesus.anchor('handR')), 'V.R', pxs(vd.anchor('handR')), 'J.shL', pxs(jesus.anchor('shoulderL')), jesus.anchor('handR').distanceTo(vd.anchor('handR')).toFixed(2));
      console.log('cand', ['shoulderR', 'shoulderL', 'earR', 'chest', 'sideR', 'hood', 'head'].map((n) => n + ' ' + vd.anchor(n).distanceTo(js).toFixed(2) + '/' + vd.anchor(n).distanceTo(jl).toFixed(2) + ' y' + vd.anchor(n).y.toFixed(2)).join(' | '));
      console.log(`eyeR@${pxs(eR)} eyeL@${pxs(eL)} ref ${st.R.ecuDbg ? pxs(st.R.ecuDbg) : ''} cam ${app.camera.position.distanceTo(eR).toFixed(2)} handR-tgt ${jesus.anchor('handR').distanceTo(tgt).toFixed(2)} tgt@${pxs(tgt)} hand@${pxs(jesus.anchor('handR'))} handL@${pxs(jesus.anchor('handL'))} chest@${pxs(jc)} tgt-shoulder ${jesus.anchor('shoulderR').distanceTo(tgt).toFixed(2)}`);
      console.log(`t=${t.toFixed(2)} J.eyes@${pxs(jesus.anchor('eyes'))} V.eyes@${pxs(vd.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} whisper-ear ${wh.distanceTo(ear).toFixed(2)} dy ${(wh.y - ear.y).toFixed(2)} J.handR@${pxs(jesus.anchor('handR'))}`);
    }
  },
};

// ======================================================================================================== poses
function poseAll(t, S, st) {
  const { jesus, vd, user } = st;
  user.update(t, userPose(t, S, st, false));
  jesus.update(t, jesusPose(t, S, st, null));
  vd.update(t, voidPose(t, S, st));                      // pre-pass: this frame's mouth
  const mo = vd.anchor('mouth'), ear = jesus.anchor('earL');
  const camSide = WDIR(-0.25, 1);
  const cup = { mouth: mo, p: mo.clone().lerp(ear, 0.42).addScaledVector(camSide, 0.04).add(V3(0, -0.1, 0)), palm: camSide.clone().negate(), fing: V3(0, 1, 0).addScaledVector(ear.clone().sub(mo).normalize(), 0.35).normalize() };
  vd.update(t, voidPose(t, S, st, cup));
  jesus.update(t, jesusPose(t, S, st, vd));
  user.update(t, userPose(t, S, st, true));
}

/** whisper bend amount 0..1 (bends in on the narration, unbends on "I'll ask") */
const bendAt = (t, S) => k(t, [[S.bendA, 0], [S.bendB, 1, 'inOut'], [S.unbend, 1], [S.unbend + 0.9, 0, 'inOut']]);

// ---------------------------------------------------------------------------------------------------------- the Void
function voidPose(t, S, st, cup = null) {
  const { jesus, user } = st;
  const amt = bendAt(t, S);
  const Wp = whisperPose(-1, DEPTH, amt);
  // the whisper slows and turns sincere in b08: the cupped hand sags, the bend deepens a touch (leaning on him)
  const hurt = ramp(t, S.b08 + 0.1, S.b08 + 0.8) * (1 - ramp(t, S.b11 - 0.2, S.b11 + 0.3));
  const sag = hurt * (1 - ramp(t, S.c9 + 0.6, S.b09e));
  const P = {
    pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw),
    body: { ...Wp.body }, head: { ...Wp.head }, extra: { stars: lerp(1.15, 0.7, hurt), motes: 0.7 },
    armL: { preset: 'belly', hand: { curl: 0.5, spread: 0.12, cup: 0.5 } },
    armR: Wp.armR ? { ...Wp.armR } : { preset: 'rest' },
  };
  P.head.yaw *= HEADYAW;
  // whisper rhythm in the body (soft); a slow nod on "That hurts"
  const sp = speechSafe('VOID', t);
  const wh = sp ? sp.open : 0;
  P.head.pitch += 0.03 * wh - 0.0 + 0.14 * pulse(t, S.thatW + 0.05, 0.4, 0.15, 0.55);
  P.body.breathe = 1 - 0.5 * amt;
  if (Wp.armR) {
    P.armR.offset = [0, -0.12 * sag, 0];
    if (cup) {
      // the cupped hand between its mouth and his ear, back of the hand to the camera (it hides the secret)
      const m = clamp(amt * 1.4 - 0.2);
      const tg = cup.p.clone().lerp(cup.mouth, 0.35 * sag).add(V3(0, -0.07 * sag, 0));
      P.armR = { preset: 'whisper', from: 'rest', mix: m, target: tg, reach: m, palm: cup.palm, fingers: cup.fing,
        hand: { curl: 0.32 + 0.2 * sag, cup: 0.85, spread: 0.06, thumb: 0.2 } };
    }
  }
  // ---- face
  const fListen = () => {
    const f = JX('listening', { mPress: 0.35, mSmile: 0.3, browIn: 0.5, browOut: 0.3, lidU: 1.0 });
    f.browIn += 0.25 * nods; f.browOut += 0.2 * nods;                    // the brows climb a little on each nod
    f.mSmile += 0.12 * pulse(t, S.flick + 0.05, 0.1, 0.3, 0.3);
    return f;
  };
  const fOhReally = () => {
    const f = JX([['listening', 0.6], ['pressed', 0.4]], { mSmile: 0.36, browIn: 0.5, browOut: 0.35, lidU: 1.0 });
    const really = pulse(t, S.justW - 0.12, 0.12, 0.35, 0.3);
    f.browIn += 0.35 * really; f.browOut += 0.45 * really; f.lidU += 0.15 * really; f.mRound = 0.4 * really;
    const wince = pulse(t, S.pat + 0.5, 0.15, 0.25, 0.3);
    f.mSmile -= 0.25 * wince; f.browIn += 0.25 * wince; f.browSq = 0.3 * wince; f.lidU -= 0.12 * wince; f.mAsym = 0.25 * wince;
    return f;
  };
  const fConcern = () => JX('compassion', { wet: 0.6, lidU: 1.0, mPress: 0.3 });
  const fSpeak = () => JX('tender', { browIn: 0.95, browOut: -0.2, wet: 0.95, lidU: 0.92, mSmile: 0.1, lidSad: 0.45 });
  const fAsk = () => {
    const f = JX('rueful', { mSmile: 0.18, mPress: 0.55, lidU: 0.95 });
    f.mSmile += 0.18 * pulse(t, S.askW + 0.1, 0.1, 0.15, 0.3);            // quick tight smile
    return f;
  };
  P.face = faceSeq(t, [[S.s, fListen], [S.c6, fOhReally, 0.3], [S.b08 + 0.2, fConcern, 0.6], [S.b09 - 0.05, fSpeak, 0.3], [S.b11 - 0.1, fAsk, 0.3]]);
  P.blinkAt = [S.flick + 0.36, S.b08 + 0.25, S.b09 + 1.1, S.b11 + 0.05];
  // his mouth: the mm-hm vocal (closed hums) + his two lines; silent under the narration otherwise
  const sp = speechSafe('JESUS', t);
  P.speech = sp ? { ...sp, open: (t < S.b03e + 0.05 ? 0.35 : 1) * sp.open } : false;
  return P;
}
/** the point on the Void's velvet nearest a desired world point (coarse search over rest height / angle) -> {p, y, a} */
function velvetNear(vd, want, out = 0.012, yMax = 1.55) {
  let best = null, bd = 1e9;
  for (let y = 0.8; y <= yMax + 0.01; y += 0.05) for (let a = -1.5; a <= 0.31; a += 0.06) {
    const p = voidSurface(vd, y, a, out), d = p.distanceToSquared(want);
    if (d < bd) { bd = d; best = { p, y, a }; }
  }
  return best;
}
function voidNormal_(vd, y, ang) {
  // outward normal at that point, flipped: the palm faces INTO the velvet
  const a = voidSurface(vd, y, ang, 0), b = voidSurface(vd, y, ang, 0.1);
  return a.sub(b).normalize();
}

// ---------------------------------------------------------------------------------------------------------- user
function userPose(t, S, st, final) {
  const { jesus, vd, user } = st;
  const R = st.R;
  const jE = final ? jesus.anchor('eyes') : V3(...EDGE.W(0.0, 1.55, -0.55));
  const vE = final ? vd.anchor('eyes') : V3(...EDGE.W(0.6, 1.75, -0.75));
  const P = {
    pos: userPosAt(t, S.scoot), yaw: EDGE.Y(M.U.yaw),
    body: { sit: 1, sitPath: 'plain', shrug: 0.4, tremble: 0.15, pant: 0.1, hunch: 0.28, recoil: 0.12, lean: 0.03 },
    extra: { phone: 0.85, tears: 0.35, glisten: 0.25, screen: 'feed' },
  };
  // ---- phone hand: prop -> holds the phone (offscreen in b01-b03) -> phone up to fake-scroll (b05) -> down (b11)
  const hold = ramp(t, S.b02 + 0.5, S.b02 + 1.4);
  P.armL = hold < 1 ? { preset: [['prop', 1 - hold], ['hold', hold + 1e-4]] } : { preset: 'hold' };
  const up = ramp(t, S.phone, S.phone + 0.3, 'out') * (1 - ramp(t, S.b11 + 0.2, S.end - 0.1));
  P.extra.phoneUp = up * (1 - 0.3 * ramp(t, S.c10 - 0.3, S.c10));
  P.extra.scroll = 2.6 * Math.max(0, Math.min(t, S.b10 + 0.3) - S.phone) - 0.6 * Math.max(0, Math.min(t, S.b10 + 0.3) - S.b05e);
  const tapOn = t > S.phone + 0.25 && t < S.b10 + 0.3 ? 1 : 0;
  if (tapOn) { P.extra.tap = Math.max(0, Math.sin((t - S.phone) * 2 * Math.PI * 3.2)) * (t > S.b10 + 0.2 ? 0 : 1); P.extra.thumb = 1; }
  // ---- the raised RIGHT hand: s04's target, drops a little lower while scrolling, plain s08 'defend' by the end
  const lowerH = ramp(t, S.phone, S.phone + 0.4) * 0.35;
  const plain = ramp(t, S.b10, S.end);
  const tg = defendTarget(R).lerp(R.plainDefend, plain).add(V3(0, -0.12 * lowerH, 0));
  P.armR = { preset: 'defend', tremble: 0.35, target: tg, reach: 1, palm: plain < 1 ? R.toPair : undefined };
  // ---- body: flinch when the side-eye lands; the scoot (2.5 cm); shrinks behind the phone in b06
  const flinch = pulse(t, S.meet + 0.08, 0.06, 0.06, 0.2);
  P.body.flinch = 0.45 * flinch;
  const sc = pulse(t, S.scoot - 0.04, 0.1, 0.08, 0.15);
  if (sc > 0) { P.body.scoot = sc; P.body.scootPhase = clamp((t - S.scoot + 0.05) / 0.4) * 0.6; }
  const shrink = ramp(t, S.glance + 0.1, S.glance + 0.45) * (1 - ramp(t, S.c10 - 0.2, S.c10 + 0.6));
  P.body.shrug += 0.3 * shrink; P.body.hunch += 0.2 * shrink; P.body.slump = 0.15 * shrink;
  // ---- gaze / head
  const screen = () => user.anchor('phoneScreen');
  const away = () => jE.clone().lerp(uEdown(R), 0.7);
  P.gaze = gazeSched(t, [
    [S.s, () => vE], [S.b02 + 0.4, () => jE.clone().lerp(vE, 0.5), 0.15],
    [S.meet, () => vE, 0.07],                       // meets the side-eye
    [S.phone + 0.05, screen, 0.1],                  // pretend to read
    [S.peek, () => vE, 0.08], [S.peek + 0.42, screen, 0.09],   // peeks over the glasses: still being watched
    [S.peek2, () => vE, 0.08], [S.peek2 + 0.35, screen, 0.09],
    [S.c10 + 0.05, () => jE.clone().lerp(vE, 0.5), 0.12],      // b10: overheard "That hurts" — looks up at them
    [S.c10 + 0.62, away, 0.25],                                 // eyes slide away
  ]);
  const look = ramp(t, S.phone, S.phone + 0.3) * (1 - ramp(t, S.c10, S.c10 + 0.2));
  P.head = { follow: 0.25 * (1 - look), pitch: 0.2 * look + 0.05 * shrink };
  // ---- face
  const fSus = () => UX('suspicious', { lidU: 0.78, wet: 0.3 });
  const fMeet = () => UX('gulp', { lidU: 1.25, wet: 0.4 });
  const fScroll = () => UX([['scroll', 0.65], ['suspicious', 0.35]], { wet: 0.3 });
  const fShrink = () => UX([['scroll', 0.5], ['tremble', 0.5]], { mTremble: 0.5, wet: 0.4 });
  const fFlicker = () => {
    const f = UX('soften', { mOpen: 0.12, wet: 0.7, pupil: 1.15 });
    const set_ = ramp(t, S.c10 + 0.62, S.c10 + 0.95);
    f.mOpen = lerp(f.mOpen, 0.0, set_); f.mPress = lerp(0, 0.6, set_); f.browIn = lerp(f.browIn, 0.35, set_); f.lidU = lerp(f.lidU, 0.85, set_);
    return f;
  };
  const fAfter = () => UX('suspicious', { lidU: 0.85, mPress: 0.6 });
  P.face = faceSeq(t, [[S.s, fSus], [S.meet, fMeet, 0.08], [S.phone + 0.1, fScroll, 0.25], [S.glance + 0.1, fShrink, 0.3], [S.c10 + 0.08, fFlicker, 0.18], [S.b11 + 0.3, fAfter, 0.5]]);
  P.blinkAt = [S.c10 + 0.2, S.c10 + 0.45, S.b02 + 0.2];
  P.face.autoBlink = t > S.c10 - 0.2 && t < S.c11 ? 0 : 1;
  P.speech = false;
  return P;
}
function uEdown(R) { return toV(R.userShoulderR).add(V3(0, -0.6, 0)).addScaledVector(WDIR(-1, 0.6), 0.8); }
