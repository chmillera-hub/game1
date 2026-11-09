// s07 the_void_whispers — the roles flip: now the Void has the secret, and the user can feel it is about them. Jesus
// listens like a good friend on the phone. The side-eye is slow-burning comic menace, until the whisper slows down and
// turns sincere: under the attitude, the Void is hurt, and the user overhears just enough to feel it.
//   open VOID_CU (s06's established angle, a clear size step from s06's two-shot): hand still over its mouth, eyes
//       narrowed at the user; a blink — decided; the hand comes down and it starts to bend (cut on the action).
//   b01-b03 WHISPER (slow push): the Void bent to Jesus's left ear, its RIGHT hand cupped BESIDE ITS OWN MOUTH (forearm
//       up, elbow down-and-out, the cuff opening downward: a hand hiding a secret, not an ear trumpet), half-lidded,
//       soft mouth shapes; Jesus tilts his ear up, eyes up-and-aside, mm-hm nods with the brows climbing; +1.0 s into
//       the whisper the Void's eyes slide to the user and park, lids flatten; +2.2 s Jesus's eyes flick to the user and back.
//   b04 ECU of the side-eye (its LEFT eye; framed high so the subtitle band holds only dark velvet): iris parked hard
//       in the corner, the lid lowers a hair, no blink.
//   b05 the Void's POV down at the user: meets the side-eye, gulps, flinches, SCOOTS back (7 cm + a little hop) ->
//       CUT on the scoot to the ECU: the iris ticks after them, the lid lowers -> back on the user: fake-scrolling with
//       thumb taps, one peek over the glasses.
//   b06-b07 OTS on the user's shoulder pushing in to a medium on Jesus (face > 200 px by "just"): steady nods, "oh
//       really?" brows, a polite glance down at the user and back, a pat on the Void's sleeve (its forearm, camera
//       side), a sympathetic wince; the user shrinks; the Void's brow-wisp nearest the user lowers when they peek.
//   b08 WHISPER: the whisper slows; the side-eye melts into hurt (sad lids, wisps up in the middle, dimmer stars, the
//       cupped hand sags). Jesus's smile fades, brows draw together.
//   b09 JESUS medium with the Void above-right (both eyes): "No, I know. That hurts." — barely above a murmur. The
//       Void's big hand comes to rest on the front of his LEFT upper arm (cuff down, well clear of his face) and his
//       RIGHT hand crosses to cover it (contact, in frame); the Void nods slowly.
//   b10 USER_CU closer: the flicker — squint drops, brows lift, two blinks, lips part, thumb stops; eyes slide away.
//   b11 JESUS_CU: small inhale, eyes to the user, to the Void and back, a quick tight smile; the Void unbends out of
//       the top of frame; both end in s08's start poses.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth, noise1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
import { VX, whisperPose } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, gazeSched, scopeVisible, ensureLittleGalaxy, drawSkyGalaxy, faceSeq, fmix } from './edgeprops.js';
import { fitShot } from './armour_shared.js';
import { M, W, WDIR, speechSafe, defendTarget, plainDefendWrist, userPosAt, camKeys, dbg, mouthFrame, coverMouth } from './kit_s05_07.js';

const DEBUG = false;
const JY0 = -0.32, JY1 = -0.5;          // Jesus's local facing: s06's -> s08's (WY(M.JV))
const DEPTH = 1.15;                      // whisperPose depth from b09 on (the hood eased up a little; s07b09's look)
const HEADYAW = 0.6;                    // fraction of whisperPose's hood yaw kept from b09 on (the face stays readable)
// b01-b08 the whisper proper: bent further from the middle and the hood leaned over onto his head (side bend + roll
// toward him, a small nod), so the hood sits BESIDE his head, its mouth ~18 cm from his left ear (verified ~0.18 m
// from 71.2 on), both eyes still readable from the WHISPER camera
const DEEP = { depth: 1.2, headYaw: 0.8, tilt: -0.1, lean: -0.06, roll: -0.3, pitch: 0.12 };
const SCOOT = 0.07;                     // the user's scoot back (m), exaggerated so it reads at phone size
// the Void's whisper vocals (audio/vocals/<beat>.wav) as 24 fps RMS envelopes (0..1): small, quick whisper mouth
// shapes in sync with what we hear (the vocal beats have no lipsync.json entry)
const WHISPER_ENV = {
  s07b02: [0.02, 0.09, 0.54, 0.89, 0.31, 0.89, 0.82, 0.20, 0.17, 0.65, 0.39, 0.30, 0.33, 0.63, 0.62, 0.07, 0.13, 0.12, 0.54, 0.86, 0.57, 0.32, 0.10, 0.39, 0.54, 0.41, 0.32, 0.56, 0.52, 0.41, 0.24, 0.11, 0.11, 0.05, 0.01, 0.00, 0.07, 0.30, 0.01, 0.16, 0.72, 0.36, 0.42, 0.37, 0.36, 0.20, 0.08, 0.02, 0.00, 0.14, 0.08, 0.26, 0.61, 0.88, 0.60, 0.12, 0.13, 0.14, 0.61, 1.00, 0.67, 0.11, 0.09, 0.06, 0.29, 0.40, 0.13, 0.01, 0.10, 0.15, 0.47, 0.46, 0.33, 0.21, 0.08, 0.09, 0.09, 0.17, 0.21, 0.08, 0.04],
  s07b07: [0.03, 0.37, 0.12, 0.08, 0.11, 0.56, 0.81, 0.60, 1.00, 0.90, 0.31, 0.02, 0.09, 0.26, 0.42, 0.39, 0.33, 0.22, 0.31, 0.26, 0.09, 0.03, 0.20, 0.20, 0.20, 0.27, 0.26, 0.22, 0.14, 0.08, 0.03, 0.07, 0.12, 0.50, 0.94, 0.43, 0.17, 0.04, 0.09, 0.35, 0.36, 0.33, 0.23, 0.05, 0.01, 0.16, 0.05, 0.00, 0.05, 0.22, 0.18, 0.08, 0.06, 0.03, 0.01, 0.01, 0.01],
  s07b08: [0.02, 0.11, 0.72, 0.77, 0.52, 1.00, 0.81, 0.22, 0.19, 0.65, 0.41, 0.35, 0.35, 0.64, 0.86, 0.06, 0.13, 0.14, 0.58, 0.89, 0.42, 0.45, 0.10, 0.37, 0.56, 0.44, 0.33, 0.57, 0.57, 0.44, 0.24, 0.13, 0.08, 0.03, 0.01, 0.00, 0.01, 0.04],
};
/** whisper lip-sync sample {open, wide, round, close} for the Void at t (null outside its whisper vocals) */
function whisperSpeech(t) {
  for (const [id, env] of Object.entries(WHISPER_ENV)) {
    const a = T(id), f = (t - a) * 24;
    if (f < -1 || f > env.length) continue;
    const i = Math.max(0, Math.min(env.length - 1, Math.floor(f))), j = Math.min(env.length - 1, i + 1), u = clamp(f - i);
    const e = clamp((env[i] + (env[j] - env[i]) * u) * (f < 0 ? 1 + f : 1));
    const slow = id === 's07b08' ? 0.75 : 1;                           // the slower, sincere one: smaller shapes
    // tiny, quick shapes: a little open on each syllable, the lips pursing/spreading from syllable to syllable
    return { open: slow * (0.03 + 0.3 * e), round: 0.55 + 0.35 * noise1(t * 6.5, 71), wide: -0.15 + 0.25 * noise1(t * 5.3, 72), close: e < 0.06 ? 0.5 : 0 };
  }
  return null;
}

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
  // open: VOID_CU, the decision blink, the hand comes down, the bend starts -> cut on the action to WHISPER
  S.decide = S.s + 0.3;
  // the bend: starts as the hand leaves its mouth, the mouth is at his ear by ~b01+0.7 (71.2), before the side-eye
  S.bendA = S.s + 0.45, S.bendB = Math.min(S.whispersW + 0.4, S.b01 + 0.68);
  S.c1 = Math.max(S.s + 0.75, S.whispersW - 0.08);
  S.unbend = S.b11 + 0.02;                                           // whisperPose -> 0 over 0.9 s
  // cuts
  S.c4 = S.b04 - 0.05; S.c5 = S.b05 - 0.08; S.c6 = S.b06 - 0.1; S.c8 = S.b08 - 0.05; S.c9 = S.b09 - 0.12; S.c10 = S.b10; S.c11 = S.b11 - 0.12;
  // the user's b05 reaction; the scoot starts on the user and we cut to the iris as it lands
  S.meet = S.sideW + 0.02, S.scoot = S.eyeingW - 0.02, S.c5i = S.scoot + 0.14, S.c5j = S.c5i + 0.5;
  S.phone = Math.max(S.twitterW - 0.05, S.c5j - 0.25), S.peek = S.userW + 0.2;
  // b06/b07 (the push is ~60 % in by "just"): "oh really?" on "nodding", the polite glance on "along", the pat
  S.c6p = S.c6 + 0.85;
  S.really = S.noddingW - 0.05, S.glance = S.alongW - 0.02, S.pat = S.alongW + 0.55;
  S.peek2 = S.glance + 0.1;                                           // the user peeks again (Jesus's glance)
  return S;
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  const e = 1e-5;                        // cut = two keys e apart (a frame can't land inside 10 us)
  return camKeys('s07', [
    [S.s, R.vcuA], [S.c1 - e, R.vcuB, 'linear'],
    [S.c1, R.whA], [S.c4 - e, R.whB, 'inOut'],
    [S.c4, R.ecuA], [S.c5 - e, R.ecuB, 'linear'],
    [S.c5, R.pov], [S.c5i - e, R.povB, 'linear'],
    [S.c5i, R.ecuC], [S.c5j - e, R.ecuD, 'linear'],
    [S.c5j, R.povB], [S.c6 - e, R.povC, 'linear'],
    [S.c6, R.ots], [S.c6p, R.otsB, 'inOut'], [S.c8 - e, R.otsC, 'linear'],
    [S.c8, R.wh8], [S.c9 - e, R.wh8b, 'linear'],
    [S.c9, R.j9], [S.c10 - e, R.j9b, 'linear'],
    [S.c10, R.u10], [S.c11 - e, R.u10b, 'linear'],
    [S.c11, R.j11], [S.end, R.j11b, 'out'],
  ]);
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
    const at = (tt) => { poseAll(tt, S, st); return { jE: jesus.anchor('eyes'), vE: vd.anchor('eyes'), uE: user.anchor('eyes'), vEyeR: vd.face.eyes[1].group.getWorldPosition(V3()), vEyeL: vd.face.eyes[0].group.getWorldPosition(V3()), vHead: vd.anchor('head'), vDir: vd.anchor('mouthDir'), jH: jesus.anchor('handL'), uHead: user.anchor('head'), uSh: user.anchor('shoulderR'), vHR: vd.anchor('handR'), jTop: jesus.anchor('top') }; };
    // open: VOID_CU on s06's established angle (no chin-brim "second mouth" at this pitch)
    const a0 = at(S.s + 0.2);
    R.vcuA = EDGE.shot(EDGE.L(a0.vE), { dist: 2.85, yaw: -32, pitch: -12, fov: 33, screenY: sy(340), drift: 0.12 });
    R.vcuB = EDGE.shot(EDGE.L(a0.vE), { dist: 2.72, yaw: -32, pitch: -12, fov: 33, screenY: sy(345), drift: 0.12 });
    const a1 = at(S.b02 + 2.0);
    // WHISPER: medium two-shot, 3/4 front on the two heads from where the hood points (its face reads), the bent hood
    // beside his head: his eyes y~460, its eyes y~330, the cupped hand + whispering mouth between them; slow push to ~80 %
    const mid = a1.jE.clone().lerp(a1.vE, 0.5);
    R.whA = { ...EDGE.shot(EDGE.L(mid), { dist: 3.4, yaw: -22, pitch: 3, fov: 33, screenY: 0.32, drift: 0.15 }), err: 0 };
    R.whB = { ...R.whA, pos: toV(R.whA.pos).lerp(mid, 0.2).toArray() };
    // b08 back to the two heads, a step closer and more in profile (faces y~360-430): the whisper turns sincere
    const a8 = at(S.b08 + 0.6), mid8 = a8.jE.clone().lerp(a8.vE, 0.5);
    R.wh8 = { ...EDGE.shot(EDGE.L(mid8), { dist: 2.75, yaw: -16, pitch: 3, fov: 33, screenY: 0.31, drift: 0.12 }), err: 0 };
    R.wh8b = { ...R.wh8, pos: toV(R.wh8.pos).lerp(mid8, 0.06).toArray() };
    // b04 ECU of the side-eye (its LEFT eye: the right one is behind the cupped hand from every camera-side angle);
    // the eye sits high (y~330) so the mouth / hand fall below the subtitle band's top... and the band stays velvet
    const a4 = at(S.b04 + 0.5);
    const toCam = toV(R.whA.pos).sub(a4.vEyeL).normalize().add(V3(0, 0.1, 0)).normalize();
    const ecuPos = a4.vEyeL.clone().addScaledVector(toCam, 1.75);
    R.ecuA = fitShot([[a4.vEyeL, 470, 300]], 17, ecuPos, a4.vEyeL, { free: [0, 0, 0], drift: 0.04 });
    R.ecuB = fitShot([[a4.vEyeL, 470, 300]], 16.2, ecuPos.clone().addScaledVector(toCam, -0.1), a4.vEyeL, { free: [0, 0, 0], drift: 0.04 });
    // b05 the Void's POV down at the user (they meet its eyes = the lens); the insert re-uses the ECU, a hair tighter
    const a5 = at(S.b05 + 0.3);
    const toV5 = a5.vE.clone().sub(a5.uE).normalize();
    const povP = a5.uE.clone().addScaledVector(toV5, 1.95).addScaledVector(WDIR(-0.2, 1), 0.14);
    R.pov = fitShot([[a5.uE, 360, 500]], 30, povP, a5.uE, { free: [0, 0, 0], drift: 0.1 });
    R.povB = fitShot([[a5.uE, 360, 505]], 28.5, povP.clone().addScaledVector(toV5, -0.06), a5.uE, { free: [0, 0, 0], drift: 0.1 });
    R.povC = fitShot([[a5.uE, 360, 510]], 27, povP.clone().addScaledVector(toV5, -0.12), a5.uE, { free: [0, 0, 0], drift: 0.1 });
    const a5i = at(S.c5i + 0.2);
    R.ecuC = fitShot([[a5i.vEyeL, 500, 320]], 16, ecuPos, a5i.vEyeL, { free: [0, 0, 0], drift: 0.03 });
    R.ecuD = fitShot([[a5i.vEyeL, 500, 320]], 15.2, ecuPos.clone().addScaledVector(toCam, -0.05), a5i.vEyeL, { free: [0, 0, 0], drift: 0.03 });
    // b06 OTS over the user's right shoulder (soft, lower-left; their raised hand clear of his hem), pushing in to a
    // medium on Jesus: face ~220 px by "just"
    const a6 = at(S.b06 + 1.0);
    const jTop6 = a6.jE.clone().add(V3(0, 0.16, 0)), jChin6 = a6.jE.clone().add(V3(0, -0.13, 0));
    const otsP = toV(EDGE.cam('OTS').pos).lerp(a6.jE, 0.3).setY(1.4);
    // (knees-up on Jesus: his feet / hem are out of frame, so the user's raised hand can't make a tangent with them)
    R.ots = fitShot([[a6.jE, 380, 430], [a6.vE, 545, 220, 0.4], [a6.uHead, 95, 1090, 0.6]], 25, otsP, a6.jE, { posReg: 0.25, yMin: 1.2, yMax: 1.9, drift: 0.12 });
    R.otsB = fitShot([[jTop6, 350, 365], [jChin6, 350, 585], [a6.vE, 545, 205, 0.8]], 26, toV(R.ots.pos).lerp(a6.jE, 0.3), a6.jE, { posReg: 0.15, drift: 0.12 });
    R.otsC = fitShot([[jTop6, 350, 355], [jChin6, 350, 595], [a6.vE, 545, 195, 0.8]], 24.5, toV(R.otsB.pos).lerp(a6.jE, 0.04), a6.jE, { free: [0, 0, 0], drift: 0.12 });
    // b09 Jesus medium, the Void above-right (both eyes), the contact on his left arm in frame
    const a9 = at(S.b09 + 1.0);
    const c9 = V3(...EDGE.shot(EDGE.L(a9.jE), { dist: 2.3, yaw: -6, pitch: 2, fov: 33, screenY: sy(470) }).pos);
    R.j9 = fitShot([[a9.jE, 290, 480], [a9.vE, 480, 215], [a9.vHR, 470, 760, 0.6]], 33, c9, a9.jE, { posReg: 0.3, yMin: 1.3, yMax: 2.0, drift: 0.1 });
    R.j9b = fitShot([[a9.jE, 292, 480], [a9.vE, 478, 222], [a9.vHR, 468, 760, 0.6]], 31.5, toV(R.j9.pos), a9.jE, { free: [0, 0, 0], drift: 0.1 });
    const a11 = at(S.b11 + 0.3);
    R.j11 = EDGE.shot(EDGE.L(a11.jE), { dist: 1.6, yaw: -20, pitch: 1, fov: 33, screenY: sy(420), drift: 0.1 });
    R.j11b = EDGE.shot(EDGE.L(a11.jE), { dist: 1.52, yaw: -20, pitch: 1, fov: 33, screenY: sy(420), drift: 0.1 });
    // b10 USER_CU closer (face right of centre: the raised hand reads whole at frame-left, like s06)
    const a10 = at(S.b10 + 0.4);
    const uy = EDGE.Y(M.U.yaw), uRt = V3(-Math.cos(uy), 0, Math.sin(uy));
    const u10L = EDGE.L(a10.uE.clone().addScaledVector(uRt, 0.07));
    R.u10 = EDGE.shot(u10L, { dist: 1.5, yaw: 112, pitch: 4, fov: 33, screenY: sy(410), drift: 0.08 });
    R.u10b = EDGE.shot(u10L, { dist: 1.42, yaw: 112, pitch: 4, fov: 33, screenY: sy(410), drift: 0.08 });
    console.log('s07 fits', R.whA.err.toFixed(1), R.wh8.err.toFixed(1), R.ots.err.toFixed(1), R.otsB.err.toFixed(1), R.j9.err.toFixed(1));
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
    // voidSky constant across the scene's cuts (STAGING §1.5)
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * 0.85, voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]),
      sunGlow: (t >= S.c10 && t < S.c11) ? 0.6 : 1 });
    st.look = lookFor('s07', set.look);
    dbg('s07', st);
    if (DEBUG) {
      const pxs = (v) => px(app.camera, v).join(',');
      const ear = jesus.anchor('earL'), wh = vd.anchor('whisper');
      console.log(`t=${t.toFixed(2)} J.eyes@${pxs(jesus.anchor('eyes'))} V.eyes@${pxs(vd.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} whisper-ear ${wh.distanceTo(ear).toFixed(2)} J.handR@${pxs(jesus.anchor('handR'))} V.handR@${pxs(vd.anchor('handR'))}`);
    }
  },
};

// ======================================================================================================== poses
function poseAll(t, S, st) {
  const { jesus, vd, user } = st;
  user.update(t, userPose(t, S, st, false));
  jesus.update(t, jesusPose(t, S, st, null));
  vd.update(t, voidPose(t, S, st));                      // pre-pass: this frame's mouth
  vd.update(t, voidPose(t, S, st, handFrames(st)));
  jesus.update(t, jesusPose(t, S, st, vd));
  user.update(t, userPose(t, S, st, true));
}

/** world frames for the Void's right hand this frame: the whisper cup beside its mouth, the rest on his left arm */
function handFrames(st) {
  const { jesus, vd } = st;
  const mf = mouthFrame(vd);
  const mo = mf.mo, ear = jesus.anchor('earL');
  const camSide = WDIR(-0.25, 1);
  const dirE = ear.clone().sub(mo).normalize();
  // the cup: beside its own mouth toward his ear, a little low and only just on the camera side (back of the hand to
  // camera): the whispering mouth stays visible just behind the hand's edge
  const cupP = mo.clone().addScaledVector(dirE, 0.1).addScaledVector(camSide, 0.02).add(V3(0, -0.06, 0));
  // the rest: its palm on the OUTER side of his LEFT upper arm (~20 cm below and well behind his jaw), the fingers
  // wrapping round to the front of the arm, the forearm going back to its body (the cuff faces away from camera)
  const q = jesus.root.getWorldQuaternion(new THREE.Quaternion());
  const fw = V3(0, 0, 1).applyQuaternion(q).setY(0).normalize();
  const shL = jesus.anchor('shoulderL'), shR = jesus.anchor('shoulderR');
  const outW = shL.clone().sub(shR).setY(0).normalize();
  const el = jesus.anchor('elbowL');
  const armP = shL.clone().lerp(el, 0.42);
  const nA = outW.clone().addScaledVector(fw, 0.12).normalize();                            // out of the arm (outer side)
  const restP = armP.clone().addScaledVector(nA, 0.08);
  const restPn = nA.clone().negate();
  const restFd = fw.clone().multiplyScalar(0.55).add(V3(0, -0.75, 0)).addScaledVector(outW, -0.1).normalize();
  const restPole = fw.clone().multiplyScalar(-0.7).add(V3(0, -0.5, 0)).addScaledVector(outW, 0.35).normalize();
  // where his hand covers it: lying over the back of its hand on the outside of his arm (his light hand on the dark
  // mitt, at his silhouette edge where it reads)
  const coverP = armP.clone().addScaledVector(nA, 0.14).addScaledVector(fw, 0.03).add(V3(0, -0.02, 0));
  return { mf, mo, ear, dirE, camSide, cupP, restP, restPn, restFd, restPole, coverP, fw, outW };
}

/** whisper bend amount 0..1 (bends in during the VOID_CU, eases up a little once the whisper is over, unbends on "I'll ask") */
const bendAt = (t, S) => k(t, [[S.bendA, 0], [S.bendB, 1, 'inOut'], [S.b09 - 0.05, 1], [S.b09 + 0.7, 0.82, 'inOut'], [S.unbend, 0.82], [S.unbend + 0.9, 0, 'inOut']]);

// ---------------------------------------------------------------------------------------------------------- the Void
function voidPose(t, S, st, F = null) {
  const { jesus, user } = st;
  const amt = bendAt(t, S);
  // the deep whisper bend (b01-b08) eases into the plain one as "No, I know" starts (b09 keeps its verified look)
  const dk = 1 - ramp(t, S.b09 - 0.05, S.b09 + 0.7), deep = amt * dk;
  const Wp = whisperPose(-1, lerp(DEPTH, DEEP.depth, dk), amt);
  Wp.body.tilt += DEEP.tilt * deep; Wp.body.lean += DEEP.lean * deep;
  Wp.head.roll += DEEP.roll * deep; Wp.head.pitch += DEEP.pitch * deep;
  // the whisper slows and turns sincere in b08: the cupped hand sags
  const hurt = ramp(t, S.b08 + 0.1, S.b08 + 0.8) * (1 - ramp(t, S.b11 - 0.2, S.b11 + 0.3));
  const sag = hurt * (1 - ramp(t, S.c9, S.b09 + 0.5));
  const P = {
    pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw),
    body: { ...Wp.body }, head: { ...Wp.head }, extra: { stars: lerp(1.15, 0.65, hurt), motes: 0.7 },
    armL: { preset: 'belly', hand: { curl: 0.5, spread: 0.12, cup: 0.5 } },
    armR: Wp.armR ? { ...Wp.armR } : { preset: 'rest' },
  };
  // s06's end: four fingers over its mouth -> the hand comes down as it decides to whisper
  const cover = 1 - ramp(t, S.decide + 0.12, S.decide + 0.5);
  if (cover > 0 && F) P.armL = coverMouth(F.mf, cover);
  P.head.yaw *= lerp(HEADYAW, DEEP.headYaw, dk);
  // whisper rhythm in the head (soft); a slow nod on "That hurts" (it agrees)
  const sp = speechSafe('VOID', t) || whisperSpeech(t);
  const wh = sp ? sp.open : 0;
  P.head.pitch += 0.03 * wh + 0.16 * pulse(t, S.thatW + 0.05, 0.45, 0.15, 0.6);
  P.body.breathe = 1 - 0.5 * amt;
  // b04 ECU: the bright mouth line stays dim (it'd fight the subtitles; the hand hides the whisper anyway)
  if (t >= S.c4 && t < S.c5) P.extra.mouthGlow = -0.6;
  // ECUs: the lit cuff lip at the lower-left corner would sit in the subtitle band: dim the rims for those shots
  if ((t >= S.c4 && t < S.c5) || (t >= S.c5i && t < S.c5j)) P.extra.rim = 0.3;
  if (F) {
    // its RIGHT hand: the cup beside its own mouth (forearm up, elbow down and out, cuff opening downward) -> sags in
    // b08 -> b09 comes to rest on the front of his left upper arm (fingers down his arm, cuff down) -> off as it unbends
    const m = clamp(amt * 1.4 - 0.2);
    const rest9 = ramp(t, S.c9 - 0.4, S.b09 + 0.35) * (1 - ramp(t, S.unbend + 0.1, S.unbend + 0.6));
    const cupTg = F.cupP.clone().lerp(F.mo, 0.25 * sag).add(V3(0, -0.07 * sag, 0)).addScaledVector(F.camSide, 0.02 * sag);
    // (the hand travels out and round, behind his shoulder line, never across his face: a waypoint outboard/back)
    const way = F.restP.clone().addScaledVector(F.outW, 0.16).addScaledVector(F.fw, -0.12).add(V3(0, 0.12, 0));
    const tg = rest9 < 0.5 ? cupTg.lerp(way, smooth(rest9 * 2)) : way.lerp(F.restP, smooth(rest9 * 2 - 1));
    const up = V3(0, 1, 0);
    // the cup: an upright mitt, fingers up, back of the hand to the camera; elbow down, toward camera, away from him
    const palmCup = F.camSide.clone().negate().addScaledVector(F.dirE, 0.25).normalize();
    const fingCup = up.clone().addScaledVector(F.dirE, 0.18).addScaledVector(F.camSide, -0.1).normalize();
    const poleCup = V3(0, -1, 0).addScaledVector(F.camSide, 0.25).addScaledVector(F.dirE, -1.0).normalize();
    const L = (a, b) => a.clone().lerp(b, rest9).normalize().toArray();
    P.armR = { preset: 'whisper', from: 'rest', mix: Math.max(m, rest9), target: tg, reach: Math.max(m, rest9), at: 'palm', handScale: lerp(0.62, 0.66, rest9),
      palm: L(palmCup, F.restPn), fingers: L(fingCup, F.restFd), pole: L(poleCup, F.restPole),
      hand: { curl: lerp(0.14 + 0.25 * sag, 0.2, rest9), cup: lerp(0.5, 0.42, rest9), spread: 0.07, thumb: lerp(0.3, 0.35, rest9) } };
  }
  // b11: hands lowering as it unbends (s08 starts from 'rest')
  const down = ramp(t, S.unbend + 0.2, S.unbend + 0.9);
  if (down > 0) P.armL = { preset: 'rest', from: 'belly', mix: down };
  // ---- face
  const uE = user.anchor('eyes'), jE = jesus.anchor('eyes');
  // side-eye depth: parks on the slide, a hair lower on "whole", a hair lower again when the user scoots
  const lid = 0.6 - 0.06 * ramp(t, S.wholeW, S.wholeW + 0.4) - 0.07 * ramp(t, S.scoot + 0.1, S.scoot + 0.4);
  // s06's end: narrowed at the user; the decision blink
  const fIdea = () => VX([['calm', 0.5], ['smug', 0.25], ['sideeye', 0.25]], { gazeYaw: 0, mPress: 0.6, lidU: 0.62, lidL: 0.45, browIn: -0.25, blush: 0.25 });
  // the whisper: conspiratorially half-lidded (the steep look down drags the uppers: lift them less, raise the lowers)
  const fWh = () => VX('whisper', { lidU: 0.76, lidL: 0.5, browAsym: 0.1, browIn: 0.05, saccade: 0.1 });
  const fSide = () => {
    const f = VX([['whisper', 0.55], ['sideeye', 0.45]], { lidU: lid, lidL: 0.36, gazeYaw: 0, saccade: 0, autoBlink: 0 });
    // when the user peeks again (b06), one brow-wisp (the one nearer the user: its RIGHT) lowers further
    const pk = ramp(t, S.peek2, S.peek2 + 0.25);
    f.browInR = (f.browIn ?? 0) - 0.4 * pk; f.browOutR = (f.browOut ?? 0) - 0.25 * pk;
    return f;
  };
  const fHurt = () => VX([['sad', 0.6], ['whisper', 0.4]], { lidU: 0.8, lidSad: 0.7, browIn: 1.0, browOut: -0.35, browSq: 0.15, wet: 0.75, saccade: 0, autoBlink: 0 });
  const fNod = () => VX('sadSmile', { lidU: 0.9, wet: 0.85, mSmile: 0.2 });
  const fHope = () => VX('hopeful', { lidU: 1.0, mSmile: 0.15, wet: 0.35 });
  P.face = faceSeq(t, [[S.s, fIdea], [S.decide + 0.2, fWh, 0.4], [S.slide - 0.05, fSide, 0.55], [S.b08 + 0.05, fHurt, 0.7], [S.thatW, fNod, 0.4], [S.b11 + 0.1, fHope, 0.5]]);
  // ---- gaze: the user (s06) -> his ear -> slides to the user (0.6 s) and parks (tracks the scoot) -> down/away (hurt) -> Jesus
  const away = () => jE.clone().lerp(uE, 0.35).add(V3(0, -0.55, 0));
  const atJ = () => jE.clone().add(V3(0, 0.3, 0));
  P.gaze = gazeSched(t, [[S.s, uE], [S.decide + 0.08, atJ, 0.15], [S.slide, () => uE, 0.6], [S.b08 + 0.25, away, 0.8], [S.b09 + 0.3, jE, 0.5], [S.b11 + 0.05, jE]]);
  // a push into the corner (toward its right = screen-left) so the iris really parks; an extra tick after the scoot
  if (t >= S.slide && t < S.b08 + 0.6) {
    const tick = 0.1 * ramp(t, S.scoot + 0.05, S.scoot + 0.3, 'out');
    P.face.gazeYaw = (P.face.gazeYaw ?? 0) - (0.2 + tick) * ramp(t, S.slide, S.slide + 0.6) * (1 - ramp(t, S.b08 + 0.1, S.b08 + 0.6));
  }
  P.blinkAt = [S.decide, S.b11 + 0.2];
  P.speech = sp || false;
  return P;
}

// ---------------------------------------------------------------------------------------------------------- Jesus
function jesusPose(t, S, st, vd) {
  const { user } = st;
  // facing: s06's -> s08's; turns toward his friend for the sincere part, back to the user on "I'll ask"
  const yawL = k(t, [[S.s, JY0], [S.bendB, JY1, 'inOut'], [S.b08 + 0.2, JY1], [S.b09 + 0.3, -0.2, 'inOut'], [S.b11 + 0.25, -0.2], [S.end - 0.05, JY1, 'inOut']]);
  const P = { pos: W(M.JV.p), yaw: EDGE.Y(yawL), body: {}, head: {}, armL: { preset: 'clasp' }, armR: { preset: 'clasp' } };
  const uE = user.anchor('eyes');
  const vE = vd ? vd.anchor('eyes') : V3(...EDGE.W(0.5, 1.75, -0.7));
  const jE0 = V3(...W(M.JV.p)).setY(1.55);
  // ---- listening: left ear tilted up toward it, eyes up-and-aside (unfocused), mm-hm nods
  const listen = ramp(t, S.b01, S.bendB) * (1 - ramp(t, S.b11 - 0.1, S.b11 + 0.4)) * (1 - 0.8 * ramp(t, S.b08 + 0.6, S.b09 + 0.2));
  const fw = V3(Math.sin(EDGE.Y(yawL)), 0, Math.cos(EDGE.Y(yawL))), lf = V3(Math.cos(EDGE.Y(yawL)), 0, -Math.sin(EDGE.Y(yawL)));
  const aside = jE0.clone().addScaledVector(fw, 1.6).addScaledVector(lf, 0.9).add(V3(0, 0.45, 0));
  const nodRate = t < S.b08 ? 1.3 : 0.8;
  const nodAmp = t < S.b03e ? 0.1 : (t >= S.b06 - 0.2 && t < S.b07e) ? 0.1 : (t >= S.b08 && t < S.b09) ? 0.1 : 0;
  const nods = nodAmp * Math.max(0, Math.sin(2 * Math.PI * nodRate * (t - S.b01)));
  // b09: "eyes lift to the Void" — capped at ~10 deg up (the head lifts the rest), never riding the top lid
  const vEcap = () => {
    const d = vE.clone().sub(jE0), h = Math.hypot(d.x, d.z);
    return jE0.clone().add(V3(d.x, Math.min(d.y, h * Math.tan(0.17)), d.z));
  };
  // ---- gaze (eyes lead)
  P.gaze = gazeSched(t, [
    [S.s, uE], [S.b01 + 0.2, aside, 0.2],
    [S.flick, uE, 0.07], [S.flick + 0.3, aside, 0.08],                    // oh, this is about them
    [S.c6, aside], [S.glance, uE, 0.16], [S.glance + 0.5, vEcap, 0.15],     // politely fascinated, then back to his friend
    [S.b08 + 0.3, vEcap, 0.2],
    [S.b11 + 0.12, uE, 0.1], [S.b11 + 0.45, vEcap, 0.1], [S.askW + 0.4, uE, 0.18],
  ]);
  P.head = { look: vE, follow: 0.12 + 0.18 * ramp(t, S.b08, S.b08 + 0.6), yaw: 0.25 * listen, roll: -0.12 * listen, pitch: nods - 0.07 * ramp(t, S.b08 + 0.3, S.b09 + 0.3) * (1 - ramp(t, S.b11, S.b11 + 0.4)) };
  if (t >= S.b11 + 0.3) P.head = { look: uE, follow: 0.6 * ramp(t, S.b11 + 0.3, S.askW + 0.6), pitch: 0 };
  // ---- body
  P.body.tilt = 0.06 * listen;
  P.body.lean = 0.02 * listen;
  P.body.twist = 0.08 * ramp(t, S.knowW - 0.2, S.knowW + 0.4) * (1 - ramp(t, S.b11, S.b11 + 0.6));
  P.body.breathe = 1 + 1.2 * pulse(t, S.b11 - 0.1, 0.25, 0.05, 0.35);   // the small inhale before "I'll ask"
  // ---- hands
  if (vd) {
    const camSide = WDIR(-0.25, 1);
    // b06/b07: his LEFT hand pats the Void's sleeve (its whisper forearm, camera side, in frame), twice
    const patW = pulse(t, S.pat - 0.28, 0.28, 0.6, 0.35);
    if (patW > 0) {
      const lm = vd.arms.R;
      const fa = vd.root.localToWorld(lm.mid.clone().lerp(lm.end, 0.08));
      const bob = 0.035 * Math.max(0, Math.sin((t - S.pat) * 2 * Math.PI * 2.2)) * ramp(t, S.pat - 0.03, S.pat + 0.05) * (1 - ramp(t, S.pat + 0.5, S.pat + 0.62));
      P.armL = { preset: [['clasp', 1 - patW], ['shoulder', patW]], target: fa.addScaledVector(camSide, 0.19 + bob), reach: patW,
        palm: camSide.clone().negate().toArray(), fingers: V3(0, 0.25, 0).addScaledVector(lf, 0.9).normalize().toArray(), hand: { curl: 0.15, spread: 0.16, cup: 0.3 } };
    }
    // b09: his RIGHT hand crosses to cover the Void's hand resting on his left upper arm (contact); off on "I'll ask"
    const cov = ramp(t, S.knowW - 0.05, S.knowW + 0.45) * (1 - ramp(t, S.unbend - 0.05, S.unbend + 0.35));
    if (cov > 0) {
      const F = handFrames(st);
      // flat on the back of its mitt, on the side the b09 camera sees (his hand on top, in front: the contact reads)
      const vh = vd.anchor('handR'), dc = st.R.j9 ? toV(st.R.j9.pos).sub(vh).normalize() : WDIR(-0.1, 1);
      const tg = vh.clone().addScaledVector(dc, 0.13 + 0.012 * pulse(t, S.askW - 0.1, 0.08, 0, 0.12)).add(V3(0, -0.02, 0));
      P.armR = { preset: [['clasp', 1 - cov], ['shoulder', cov]], target: tg, reach: cov, at: 'palm',
        palm: dc.clone().negate().toArray(), fingers: V3(0, -0.75, 0).addScaledVector(F.outW, 0.55).addScaledVector(dc, -0.2).normalize().toArray(),
        pole: V3(0, -1, 0).addScaledVector(F.fw, 0.4).addScaledVector(F.outW, -0.3).normalize().toArray(), hand: { curl: 0.28, spread: 0.1, cup: 0.4, thumb: 0.4 } };
    }
  }
  // ---- face
  const fPress = () => JX('pressed', { mSmile: 0.5, browIn: 0.55, browOut: 0.6, lidU: 0.86, lidL: 0.42 });   // s06's end
  const fListen = () => {
    const f = JX('listening', { mPress: 0.35, mSmile: 0.3, browIn: 0.5, browOut: 0.3, lidU: 1.0 });
    f.browIn += 0.3 * nods; f.browOut += 0.25 * nods;                    // the brows climb a little on each nod
    f.mSmile += 0.12 * pulse(t, S.flick + 0.05, 0.1, 0.3, 0.3);
    return f;
  };
  const fOhReally = () => {
    const f = JX([['listening', 0.6], ['pressed', 0.4]], { mSmile: 0.36, browIn: 0.5, browOut: 0.35, lidU: 1.0 });
    f.browIn += 0.3 * nods; f.browOut += 0.25 * nods;
    const really = pulse(t, S.really, 0.12, 0.35, 0.3);
    f.browIn += 0.45 * really; f.browOut += 0.6 * really; f.lidU += 0.18 * really; f.mRound = 0.45 * really; f.mSmile -= 0.15 * really;
    // the sympathetic wince with the pat: the smile goes, inner brows up, lips pressed, a squint
    const wince = pulse(t, S.pat + 0.05, 0.15, 0.4, 0.35);
    f.mSmile = lerp(f.mSmile, -0.1, wince); f.browIn += 0.55 * wince; f.browSq = 0.4 * wince; f.lidU -= 0.08 * wince; f.lidL = (f.lidL ?? 0) + 0.18 * wince;
    f.mPress = lerp(f.mPress ?? 0, 0.85, wince); f.mAsym = 0.2 * wince; f.mWide = (f.mWide ?? 0) + 0.15 * wince;
    return f;
  };
  const fConcern = () => JX('compassion', { wet: 0.6, lidU: 1.0, mPress: 0.3, browIn: 0.8 });
  // b09: quiet and sincere — inner brows up, eyes glisten, lids soft (the iris never rides the top lid)
  const fSpeak = () => JX('tender', { browIn: 1.0, browOut: -0.2, wet: 0.95, lidU: 0.86, lidSad: 0.45, mSmile: 0.08, lidL: 0.15 });
  const fAsk = () => {
    const f = JX('rueful', { mSmile: 0.18, mPress: 0.55, lidU: 0.95 });
    f.mSmile += 0.2 * pulse(t, S.askW + 0.1, 0.1, 0.15, 0.3);            // quick tight smile
    return f;
  };
  P.face = faceSeq(t, [[S.s, fPress], [S.b01 - 0.1, fListen, 0.4], [S.c6, fOhReally, 0.3], [S.b08 + 0.2, fConcern, 0.6], [S.b09 - 0.05, fSpeak, 0.3], [S.b11 - 0.1, fAsk, 0.3]]);
  P.blinkAt = [S.flick + 0.36, S.glance + 0.6, S.b08 + 0.25, S.b09 + 1.1, S.b11 + 0.05];
  if (t >= S.c6 && t < S.c8) P.face.autoBlink = 0;                       // no stray blink on "oh really?" / the glance
  // his mouth: the mm-hm vocal (closed hums) + his two lines (b09 barely above a murmur); silent under the narration
  const sp = speechSafe('JESUS', t);
  const sc = t < S.b03e + 0.05 ? 0.35 : t < S.b10 ? 0.45 : 1;
  P.speech = sp ? { ...sp, open: sc * sp.open, wide: (t >= S.b09 && t < S.b10 ? 0.6 : 1) * sp.wide } : false;
  return P;
}

// ---------------------------------------------------------------------------------------------------------- user
function userPose(t, S, st, final) {
  const { jesus, vd, user } = st;
  const R = st.R;
  const jE = final ? jesus.anchor('eyes') : V3(...EDGE.W(0.0, 1.55, -0.55));
  const vE = final ? vd.anchor('eyes') : V3(...EDGE.W(0.6, 1.75, -0.75));
  const P = {
    pos: userPosAt(t, S.scoot, SCOOT, 0.3), yaw: EDGE.Y(M.U.yaw),
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
  // ---- the raised RIGHT hand: s04's target, drops a little lower while scrolling, plain s08 'defend' by b10
  // (in b10's close-up it is already at s08's height, whole and in frame: no lone finger at the edge)
  const lowerH = ramp(t, S.phone, S.phone + 0.4) * 0.35;
  const fwdA = ramp(t, S.c8, S.c10 - 0.1), plain = ramp(t, S.c11 + 0.05, S.end - 0.1);
  const tp = toV(R.toPair).setY(0).normalize(), uRt = V3(-Math.cos(EDGE.Y(M.U.yaw)), 0, Math.sin(EDGE.Y(M.U.yaw)));
  const A = toV(R.userShoulderR).add(V3(0, 0.06, 0)).addScaledVector(tp, 0.34).addScaledVector(uRt, 0.11);
  const tg = defendTarget(R).add(V3(0, -0.12 * lowerH, 0)).lerp(A, fwdA).lerp(R.plainDefend, plain);
  P.armR = { preset: 'defend', tremble: 0.35, target: tg, reach: 1, palm: plain < 0.5 ? R.toPair : undefined,
    fingers: fwdA > 0 && plain < 0.5 ? V3(0, 1, 0).addScaledVector(tp, 0.35).normalize().toArray() : undefined,
    pole: fwdA > 0 && plain < 0.5 ? V3(0, -1, 0).addScaledVector(uRt, 0.7).normalize().toArray() : undefined };
  // ---- body: flinch when the side-eye lands; the scoot (7 cm, a little hop); shrinks behind the phone in b06
  const flinch = pulse(t, S.meet + 0.08, 0.06, 0.06, 0.2);
  P.body.flinch = 0.55 * flinch;
  const sc = pulse(t, S.scoot - 0.04, 0.1, 0.12, 0.18);
  if (sc > 0) { P.body.scoot = sc; P.body.scootPhase = clamp((t - S.scoot + 0.05) / 0.45) * 0.6; }
  P.body.bounce = 0.035 * Math.sin(Math.PI * clamp((t - S.scoot) / 0.3));
  const shrink = ramp(t, S.glance + 0.1, S.glance + 0.45) * (1 - ramp(t, S.c10 - 0.2, S.c10 + 0.6));
  P.body.shrug += 0.3 * shrink; P.body.hunch += 0.2 * shrink; P.body.slump = 0.15 * shrink;
  // ---- gaze / head
  // (pre-pass: a fixed point in front of the chest — never read the rig's own not-yet-updated anchors)
  const uy = EDGE.Y(M.U.yaw);
  const screen = () => (final ? user.anchor('phoneScreen') : V3(...W(M.U.p)).add(V3(Math.sin(uy) * 0.3, 0.95, Math.cos(uy) * 0.3)));
  const away = () => jE.clone().lerp(uEdown(R), 0.7);
  P.gaze = gazeSched(t, [
    [S.s, () => vE], [S.b02 + 0.4, () => jE.clone().lerp(vE, 0.5), 0.15],
    [S.meet, () => vE, 0.07],                       // meets the side-eye (= the lens, in the Void's POV)
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
  const fMeet = () => UX('gulp', { lidU: 1.3, wet: 0.4, pupil: 0.7 });
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
