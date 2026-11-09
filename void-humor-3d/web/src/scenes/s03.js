// s03 the_whisper — "So Jesus walks right up to the void, / Uh. Sir? That's the void. / puts his arm around it, /
// and starts whispering in its ear. / (whispers a joke) / Nobody knows what he said. I have theories."
// Staging: docs/STAGING.md §4 s03 (marks JV / V / U; as-built notes there). Everything is keyed to beat refs / word
// times (re-timed audio re-times the picture). Pure function of t.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
import { VX } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX, headShake } from '../chars/user.js';
import { V3, loadWords, wordT, pulse, ramp, wobble, gazeSched, scopeVisible, faceSeq, fitShot, fadeSeedsNear, fadeMotesNear, hideDuring, voidSurface, JOUT, JV_OUT, JV_HUG, hugMark, AROUND_H, aroundContact, aroundArm } from './edgeprops.js';

const DEBUG = false;
const M = EDGE.M;
const W = (p) => EDGE.W(p);
const WDR = (x, z) => { const a = EDGE.W(x, 0, z), o = EDGE.W(0, 0, 0); return V3(a[0] - o[0], 0, a[2] - o[2]); };   // = s02's WD (raw)
const WDIR = (x, z) => WDR(x, z).normalize();
// Jesus's local facing at JV (the Void at his left, open to the camera). s04 starts at JYAW_6 and s05 at 0.2.
// Jesus stands at JV_OUT (edgeprops: 28 cm further out than JV) through s03-s04b11.
const JYAW = 0.05, JYAW_W = 0.88, JYAW_6 = 0.2;
// ---------------------------------------------------------------------------------------------------------- timing
function times() {
  const w = (b, word, fb) => wordT(b, word, fb);
  const S = {
    s: T('s03'), end: T('s03.end'),
    b01: T('s03b01'), walksW: w('s03b01', 'walks', 0.36), rightW: w('s03b01', 'right', 0.82), voidW: w('s03b01', 'void.', 1.52),
    b02: T('s03b02'), sirW: w('s03b02', 'sir,', 0.38), thatsW: w('s03b02', "that's", 1.2), voidW2: w('s03b02', 'void.', 1.62), b02e: T('s03b02.end'),
    b03: T('s03b03'), armW: w('s03b03', 'arm', 0.32), aroundW: w('s03b03', 'around', 0.56), itW: w('s03b03', 'it', 0.92),
    b04: T('s03b04'), whispW: w('s03b04', 'whispering', 0.32), earW: w('s03b04', 'ear.', 1.16),
    b05: T('s03b05'), b05e: T('s03b05.end'),
    b06: T('s03b06'), saidW: w('s03b06', 'said.', 1.06), iW: w('s03b06', 'i', 2.08), theoriesW: w('s03b06', 'theories.', 2.4),
  };
  S.arrive = S.voidW + 0.06;                           // Jesus's hop lands on "void"
  S.contact = S.aroundW + 0.16;                        // palm lands on the velvet
  S.pat = S.itW + 0.04;                                // one settling pat on "it"
  S.cutCU = S.b02 - 0.04;                              // -> USER_CU (the line starts on the cut)
  S.cut3 = S.b03 - 0.12;                               // -> tight two-shot
  S.cut5 = S.b05 - 0.02;                               // -> close on the Void
  S.dip = S.b05 + 1.42;                                // the pause in the whisper audio (1.42-1.67)
  return S;
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  // b01: front two-shot from the camera side (a clear angle change from s02's high OTS); the camera slides right as
  // Jesus swings round on the hop, so his beam up at the Void reads 3/4
  const c1a = EDGE.shot([0.08, 1.62, -0.7], { dist: 5.6, yaw: -3, pitch: 2, fov: 44, screenY: sy(470), drift: 0.25 });
  const c1b = EDGE.shot([0.18, 1.8, -0.62], { dist: 3.75, yaw: 9, pitch: 3, fov: 44, screenY: sy(430), drift: 0.25 });
  // b02: USER_CU (speaking: readable face), the raised hand in front of the chest at frame-right
  const ucu = EDGE.shot(EDGE.L(R.userEyes), { dist: 1.55, yaw: 108, pitch: 2, fov: 33, screenY: sy(400), drift: 0.18 });
  const ucu2 = EDGE.shot(EDGE.L(R.userEyes), { dist: 1.42, yaw: 108, pitch: 2, fov: 33, screenY: sy(400), drift: 0.18 });
  // b03: tighter two-shot from a little left of front (sees the Void's right flank + his hand on it)
  const tight = R.tight, tight2 = R.tight2;
  // b04: slow push to the two heads (Void crouched, Jesus whispering into the side of its hood)
  const heads = R.heads;
  // b05: close on the Void's face, Jesus's cupped hand + profile soft at frame-left; very slow push
  const cu = R.cu, cu2 = R.cu2;
  const ots = EDGE.cam('OTS', { drift: 0.3 });
  const otsIn = { ...ots, pos: EDGE.W(-2.35, 1.72, 4.55) };          // a step in along the same axis (pulls back to OTS)
  const e = 1e-3;
  return [
    [S.s, c1a], [S.arrive - 0.35, c1b, 'inOut'],
    [S.cutCU - e, c1b], [S.cutCU, ucu], [S.cut3 - e, ucu2, 'linear'],
    [S.cut3, tight], [S.b04 + 0.1, tight2, 'linear'],
    [S.cut5 - e, heads, 'inOut'],
    [S.cut5, cu], [S.b06 - e, cu2, 'linear'],
    [S.b06, otsIn], [S.b06 + 2.6, ots, 'inOut'], [S.end, ots],
  ];
}

// ---------------------------------------------------------------------------------------------------------- module
export default {
  id: 's03',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const fx = new Particles({ max: 24 });
    scopeVisible(fx.mesh, 's03', 's04');
    set.scene.add(fx.mesh);
    // Jesus's walk is s02's own walk function (exact continuity across the cut); fallback: a straight walk
    let walkS02 = null;
    try { walkS02 = (await import('./s02.js')).jesusWalkS02 || null; } catch (e) { walkS02 = null; }
    const st = { scene: set.scene, set, jesus, vd, user, fx, walkS02, look: lookFor('s03', set.look) };
    // the two golden puff trees (world (18.5, 9.5) and (41, 27) on the far crest) sit right behind Jesus's head in the
    // front two-shots of b01-b05 (a halo): hide them for those shots only (they are never in the b06 OTS)
    for (const [gx, gz] of [[18.5, 9.5], [41, 27]]) {
      const gold = (set.props.trees || []).find((tr) => Math.hypot(tr.position.x - gx, tr.position.z - gz) < 1.5);
      if (gold) hideDuring(gold, 's03', 's03b06');
    }
    const S = times();
    // reference anchors (pure: computed once from fixed times)
    user.update(S.s, { pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.55, hunch: 0.25 } });
    const R = st.R = { userEyes: user.anchor('eyes'), userShoulderR: user.anchor('shoulderR'), userChest: user.anchor('chest') };
    R.toPair = V3(...W(M.V.p)).setY(1.8).sub(R.userShoulderR).normalize();
    const at = (tt) => { poseAll(tt, S, st); return { jE: jesus.anchor('eyes'), jM: jesus.anchor('mouth'), jH: jesus.anchor('head'), vE: vd.anchor('eyes'), vH: vd.anchor('head'), hand: jesus.anchor('handL'), elbow: jesus.anchor('elbowL'), sh: jesus.anchor('shoulderL') }; };
    const a3 = at(S.pat + 0.2);
    // b03: Jesus pressed against its right flank (the HUG mark), from a little high and right of front so his upper arm
    // reads going up over its curve and round behind it; face ~y 500, its eyes ~y 215, his shoulder ~y 650
    const p3 = V3(...EDGE.W(1.35, 1.85, 2.65));
    R.tight = fitShot([[a3.jE, 250, 500], [a3.vE, 480, 215, 0.6], [a3.sh, 330, 650, 0.3]], 44, p3, a3.jE, { posReg: 1.5, yMin: 1.6, yMax: 2.1, drift: 0.25 });
    R.tight2 = fitShot([[a3.jE, 255, 490], [a3.vE, 482, 205, 0.6], [a3.sh, 333, 640, 0.3]], 42, R.tight.pos, a3.jE, { posReg: 3, yMin: 1.6, yMax: 2.1, drift: 0.25 });
    const a5 = at(S.b05 + 1.0);
    R.jM5 = a5.jM; R.vE5 = a5.vE;
    // b04 end: both heads, Jesus (profile, whispering) ~y 470 at left, the Void's eyes ~y 330
    const p4 = V3(...EDGE.W(1.0, 1.7, 2.7));
    R.heads = fitShot([[a5.jE, 185, 470], [a5.jH, 150, 450, 0.5], [a5.vE, 470, 320]], 40, p4, a5.vE, { posReg: 0.4, yMin: 1.4, yMax: 2.0, drift: 0.2 });
    // b05: close on the Void (eyes ~y 380), his profile + cupped hand soft at the left edge
    const p5 = V3(...EDGE.W(1.1, 1.75, 1.7));
    R.cu = fitShot([[a5.vE, 440, 380], [a5.jE, 105, 500, 0.6], [a5.jM, 150, 560, 0.3]], 36, p5, a5.vE, { posReg: 0.6, yMin: 1.4, yMax: 2.0, drift: 0.15 });
    R.cu2 = fitShot([[a5.vE, 440, 380], [a5.jE, 90, 505, 0.6], [a5.jM, 135, 565, 0.3]], 34, R.cu.pos, a5.vE, { posReg: 3, yMin: 1.4, yMax: 2.0, drift: 0.15 });
    console.log('s03 fits', [R.tight, R.tight2, R.heads, R.cu, R.cu2].map((f) => f.err.toFixed(0) + '@' + EDGE.L(f.pos).map((x) => x.toFixed(2))).join(' '));
    return st;
  },

  async update(t, app, st) {
    const { set, jesus, vd, user, fx } = st;
    st.scene.add(jesus.root, vd.root, user.root);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const S = times();
    // camera first (eye catchlights read CTX.camera during the rig updates)
    applyShot(app.camera, globalThis.__dbgCam || shotAt(t, cams(S, st.R)), t, 3);   // DBGCAM
    poseAll(t, S, st);

    // ---------------------------------------------------------------- particles: the star mote that pops off its shoulder
    fx.begin();
    const tp = S.arrive + 0.08;
    if (t >= tp && t < tp + 2.4) {
      const sh = vd.anchor('shoulderL'), md = vd.anchor('mouthDir');
      fx.burst({ t, at: tp, count: 1, seed: 31, life: 2.1, origin: sh.clone().add(V3(0, 0.12, 0)).addScaledVector(md, 0.15).toArray(), vel: [md.x * 0.12, 0.7, md.z * 0.12], spread: [0.01, 0.01, 0.01],
        gravity: [0, -0.22, 0], drag: 0.5, size: [0.16, 0.16], grow: 0.35, color: [0xfff4ff], alpha: 1, fade: [0.03, 0.55], cell: CELL.star, twinkle: true, spin: 0.8 });
      fx.burst({ t, at: tp, count: 1, seed: 32, life: 0.9, origin: sh.clone().add(V3(0, 0.12, 0)).addScaledVector(md, 0.15).toArray(), vel: [0, 0.25, 0], spread: [0, 0, 0],
        drag: 1, size: [0.3, 0.3], grow: 0.6, color: [0xc8b4ff], alpha: 0.35, fade: [0.02, 0.8], cell: CELL.dot });
    }
    fx.end();

    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (t >= S.b04 && t < S.b06 ? 0.85 : 1), voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]) });
    // no drifting thought seed may sit on a face in this scene
    const faces = [[vd.anchor('eyes'), 260], [jesus.anchor('eyes'), 110], [user.anchor('eyes'), 160]];
    fadeSeedsNear(set, app.camera, faces); fadeMotesNear(set, app.camera, faces);
    st.look = lookFor('s03', set.look);
    if (DEBUG) debugPrint(t, app, st, S);
  },
};

function debugPrint(t, app, st, S) {
  const { jesus, vd, user } = st;
  const f = (v) => '[' + EDGE.L(v).map((x) => x.toFixed(2)).join(',') + ']';
  const pxs = (v) => px(app.camera, v).join(',');
  // clearance between Jesus's head (and hair top / face) and the Void's hood + face field
  const pts = [['head', jesus.anchor('head'), 0.14], ['top', jesus.anchor('top'), 0.03], ['eyes', jesus.anchor('eyes'), 0.02], ['mouth', jesus.anchor('mouth'), 0.02], ['earL', jesus.anchor('earL'), 0.02]];
  const v = new THREE.Vector3();
  let worst = 9, wn = '';
  for (const mesh of [vd.hood, vd.faceField]) {
    mesh.updateMatrixWorld(true);
    const P = mesh.geometry.attributes.position;
    for (let i = 0; i < P.count; i += 2) {
      v.fromBufferAttribute(P, i).applyMatrix4(mesh.matrixWorld);
      for (const [n, p, r] of pts) { const d = v.distanceTo(p) - r; if (d < worst) { worst = d; wn = n; } }
    }
  }
  console.log(`DBG user shR ${f(user.anchor('shoulderR'))} ref ${f(st.R.userShoulderR)} handR ${f(user.anchor('handR'))} eyes ${f(user.anchor('eyes'))} chest ${f(user.anchor('chest'))}`);
  console.log(`DBG t=${t.toFixed(2)} clear=${worst.toFixed(3)}(${wn}) mouth->side ${jesus.anchor('mouth').distanceTo(hoodSide(vd)).toFixed(2)} J.eyes@${pxs(jesus.anchor('eyes'))} V.eyes@${pxs(vd.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} J.handL@${pxs(jesus.anchor('handL'))} ${f(jesus.anchor('handL'))} J.shL ${f(jesus.anchor('shoulderL'))} J.elbowL ${f(jesus.anchor('elbowL'))} V.head ${f(vd.anchor('head'))} U.handR@${pxs(user.anchor('handR'))}`);
}

// ======================================================================================================== all poses
function poseAll(t, S, st) {
  const { jesus, vd, user } = st;
  jesus.update(t, jesusPose(t, S, st, null));          // pre-pass (anchors for the Void's gaze)
  vd.update(t, voidPose(t, S, st));
  jesus.update(t, jesusPose(t, S, st, vd));            // final (arm around the Void's real surface)
  user.update(t, userPose(t, S, st));
}

// ---------------------------------------------------------------------------------------------------------- user
/** the raised RIGHT hand as s04/s05 have it: palm out toward the pair, out at their right-front (face stays clear) */
export function defendTargetStd(R) {
  const sh = R.userShoulderR, a = EDGE.Y(M.U.yaw) - 0.95;
  return sh.clone().add(V3(Math.sin(a) * 0.3, 0.2, Math.cos(a) * 0.3));
}
/** b02 close-up only: the hand pulled in front of the chest toward the pair, below the chin (frame-right in USER_CU).
 *  `ch` = the live chest anchor (pre-pass of this frame). */
function defendTargetCU(ch) {
  const uy = EDGE.Y(M.U.yaw), fwd = V3(Math.sin(uy), 0, Math.cos(uy)), left = V3(Math.cos(uy), 0, -Math.sin(uy));
  return ch.clone().addScaledVector(fwd, 0.16).addScaledVector(left, 0.0).add(V3(0, 0.04, 0));
}
function userPose(t, S, st) {
  const { jesus, vd, R } = st;
  const P = {
    pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw),
    body: { sit: 1, shrug: 0.55, tremble: 0.45, pant: 0.7, hunch: 0.25, recoil: 0.1 },
    armL: { preset: 'clutch' },                                                     // s02 hands over: phone clutched
    extra: { phone: 0.85, tears: 0.5, glisten: 0.6 },
  };
  const jE = jesus.anchor('eyes'), vE = vd.anchor('eyes');
  // b02: whisper-yell — leans in (head travels toward the pair), eyes flick Jesus/Void x2, feeble flap on "sir",
  // mouth pulled wide on "void", two tiny head shakes
  const inCU = ramp(t, S.cutCU - 0.3, S.cutCU) * (1 - ramp(t, S.cut3 + 0.1, S.b04));   // the CU hand position (offscreen blends)
  const lean = k(t, [[S.b02 - 0.25, 0], [S.b02 + 0.12, 0.34, 'out'], [S.sirW + 0.3, 0.3], [S.voidW2 - 0.1, 0.36, 'inOut'], [S.b02e + 0.1, 0.3], [S.b03 + 0.6, 0.06, 'inOut']]);
  P.body.lean = lean;
  P.body.jut = 0.55 * ramp(t, S.b02 - 0.2, S.b02 + 0.15) * (1 - ramp(t, S.b02e, S.b03 + 0.5));
  P.body.shrug = 0.5 + 0.15 * pulse(t, S.voidW2 - 0.1, 0.12, 0.2, 0.3);
  P.gaze = gazeSched(t, [
    [S.s, () => vE],
    [S.b02 - 0.15, () => jE], [S.b02 + 0.24, () => vE, 0.07], [S.sirW - 0.06, () => jE, 0.07],
    [S.thatsW - 0.12, () => vE, 0.07], [S.voidW2 - 0.22, () => jE, 0.07], [S.voidW2 + 0.36, () => vE, 0.07],
    [S.contact - 0.1, () => jesus.anchor('handL'), 0.12], [S.b04 + 0.4, () => vE, 0.12],
  ]);
  const sh = headShake(t, S.voidW2 + 0.04, { count: 2, dur: 0.44, amp: 0.14 });
  P.head = { yaw: sh.yaw, pitch: -0.04 + 0.06 * pulse(t, S.b02, 0.2, 1.6, 0.4), follow: 0.35 };
  P.extra.hairSwing = sh.hairSwing;
  // the face: terror softened into an urgent whisper-yell during the line (lip-sync rides on top)
  const yell = ramp(t, S.b02 - 0.15, S.b02 + 0.1) * (1 - ramp(t, S.b03 - 0.1, S.b03 + 0.4));
  P.face = UX([['terror', 1 - 0.55 * yell], ['worried', 0.55 * yell]], { browIn: 1.0, browSq: 0.5, mWide: 0.4 + 0.55 * pulse(t, S.voidW2 - 0.05, 0.1, 0.18, 0.25), pupil: 0.55 });
  // the raised RIGHT hand: in front of the chest in the CU (the flap on "sir" reads), out at the right-front elsewhere
  let tg = defendTargetStd(R);
  if (inCU > 0) {
    st.user.update(t, { ...P, armR: { preset: 'defend', target: tg, reach: 1 } });          // pre-pass: the leaning chest
    tg = tg.lerp(defendTargetCU(st.user.anchor('chest')), inCU);
  }
  const palmDir = R.toPair.clone().lerp(R.toPair.clone().setY(0).normalize().add(V3(0, 0.15, 0)).normalize(), inCU).normalize();
  const uy = EDGE.Y(M.U.yaw), poleCU = V3(-Math.cos(uy), -1.2, Math.sin(uy)).addScaledVector(V3(Math.sin(uy), 0, Math.cos(uy)), -0.3).normalize();
  P.armR = { preset: 'defend', tremble: 0.7, pole: inCU > 0.5 ? poleCU.toArray() : undefined, flap: pulse(t, S.sirW - 0.02, 0.12, 0.05, 0.24) + 0.6 * pulse(t, S.voidW2 - 0.02, 0.1, 0.04, 0.2), target: tg, reach: 1, palm: palmDir.toArray() };
  // b06: phone up as a shield, one slow blink
  const shield = ramp(t, S.b06 + 0.35, S.b06 + 0.85, 'out');
  if (shield > 0) P.armL = { preset: [['clutch', 1 - shield], ['shield', shield]] };
  P.blinkAt = [S.b02 + 1.32, S.iW - 0.3];
  P.face.autoBlink = t > S.b02 - 0.3 && t < S.b03 ? 0 : 1;          // a held, wide stare through the line (one scripted blink)
  P.face.lidU = Math.max(P.face.lidU, 1.3 * yell + P.face.lidU * (1 - yell));
  if (t > S.b03) P.face.mOpen = Math.max(P.face.mOpen, 0.32 * ramp(t, S.contact, S.contact + 0.3));
  return P;
}

// ---------------------------------------------------------------------------------------------------------- the Void
// The listening crouch: it sinks straight down (knees out, hood lowered to Jesus's height), turns its face to the
// camera side and tips its hood a little toward him, so the SIDE of its hood (not the face opening) comes down beside
// his mouth. Kept upright (no sideways lean) so the hood never cuts into his head.
function listenCrouch(a) {
  const L = { crouch: 0.95, lean: 0.05, tilt: -0.18, twist: 0.06, hy: 0.5, hp: 0.06, hr: 0.1 };
  return {
    body: { crouch: L.crouch * a, lean: L.lean * a, tilt: L.tilt * a, twist: L.twist * a },
    head: { yaw: L.hy * a, pitch: L.hp * a, roll: L.hr * a },
  };
}
/** world point on the Void's hood side where Jesus whispers (its right "ear", a little forward) */
export function hoodSide(vd) { return vd.headGroup.localToWorld(V3(-0.8, -0.06, 0.18)); }

function voidPose(t, S, st) {
  const { jesus, vd } = st;
  const P = { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw + 0.1 * (1 - ramp(t, S.arrive - 0.3, S.arrive + 0.2))), body: {}, head: {}, extra: { stars: 1 } };
  const jE = jesus.anchor('eyes');
  // ---- body: knotted hands -> recoil on his arrival -> freeze/shrug at the arm -> listening crouch -> clamp + quiver
  const recoil = k(t, [[S.arrive - 0.32, 0], [S.arrive - 0.05, 0.34, 'out'], [S.arrive + 0.35, 0.24], [S.b03, 0.18], [S.contact, 0.12], [S.b04 + 0.2, 0]]);
  const bendA = k(t, [[S.b04 + 0.12, 0], [S.earW + 0.3, 1, 'inOut'], [S.b06 + 0.05, 1], [S.b06 + 0.85, 0, 'inOut']]);
  const B = listenCrouch(bendA);
  const freeze = pulse(t, S.contact - 0.02, 0.1, 0.45, 0.4);
  const quiver = ramp(t, S.b06 + 0.05, S.b06 + 0.35);
  P.body = { ...B.body, recoil, shrug: 0.4 * freeze + 0.12 * quiver };
  // settle of the crouch (water-balloon wobble) + the held-laugh jelly quiver (<= 1 cm, smooth)
  P.body.bounce = -0.012 * wobble(t, S.earW + 0.3, 1.6, 3.5) + 0.007 * quiver * Math.sin(t * 2 * Math.PI * 6.1) + 0.004 * quiver * Math.sin(t * 2 * Math.PI * 3.7);
  P.body.breathe = 1 - 0.8 * freeze;
  P.head = { ...B.head };
  P.head.pitch = (P.head.pitch || 0) - 0.06 * pulse(t, S.arrive - 0.15, 0.2, 0.3, 0.5);
  // ---- arms: hands knotted at its middle (s02 end) -> float up 4 cm at the arm, sink -> left hand clamps over its mouth
  // = s02's knot (belly + 8 cm toward its middle), floats up 4 cm at the arm. As Jesus steps in, its RIGHT hand also
  // comes 9 cm out from the velvet (its forearm out of the belly: the sleeve reads as a sleeve, the paw clear of his hip)
  const out = ramp(t, S.arrive - 0.4, S.arrive + 0.4);
  const knot = (side) => {
    const lift = 0.04 * pulse(t, S.contact + 0.05, 0.22, 0.2, 0.35);
    const o = WDR(side === 'L' ? -0.35 : 0.35, 0.3).multiplyScalar(0.18);
    if (side === 'R') o.addScaledVector(N_RF, 0.09 * out).addScaledVector(WDIR(0.868, 0.497), 0.03 * out);
    const hc = ramp(t, S.s, S.s + 0.6);
    return { preset: 'belly', offset: [o.x, lift + 0.02 * out * (side === 'R' ? 1 : 0) + 1e-4, o.z], hand: { curl: lerp(0.55, 0.8, hc), spread: 0.02, cup: 0.6, thumb: 0.5 } };
  };
  P.armR = knot('R');
  // b02 (offscreen) -> b03: as Jesus sidles in against its right flank, its RIGHT arm drops stiff to its side (out of
  // his arm's way: stiff as a startled cat; it floats up 4 cm at the contact with the left and sinks); back to the knot
  // as it bends down to listen (b04)
  const stiff = ramp(t, S.b02 + 0.3, S.b02e - 0.1) * (1 - ramp(t, S.b04 + 0.15, S.earW + 0.2));
  if (stiff > 0) {
    const kR = P.armR, o = kR.offset;
    P.armR = { preset: 'rest', from: 'belly', mix: stiff, offset: [o[0] * (1 - stiff), o[1], o[2] * (1 - stiff)],
      hand: { curl: lerp(kR.hand.curl, 0.12, stiff), spread: lerp(0.02, 0.42, stiff), cup: lerp(0.6, 0.2, stiff), thumb: lerp(0.5, 0.6, stiff) } };
  }
  if (globalThis.__paws) {
    const PW = globalThis.__paws, vf = WDIR(Math.sin(M.V.yaw), Math.cos(M.V.yaw)), vl = WDIR(Math.cos(M.V.yaw), -Math.sin(M.V.yaw));
    const tg = voidSurface(vd, PW.h, PW.a, PW.out);
    P.armR = { preset: 'belly', target: tg, reach: 1, pole: vf.clone().multiplyScalar(PW.pf).add(V3(0, -1, 0)).addScaledVector(vl, -PW.po).normalize().toArray(),
      palm: vf.clone().multiplyScalar(-0.3).add(V3(0, -1, 0)).normalize().toArray(), fingers: vf.clone().add(V3(0, 0.7, 0)).addScaledVector(vl, 0.3).normalize().toArray(), hand: { curl: 0.45, spread: 0.15, cup: 0.5, thumb: 0.5 } };
  }
  if (globalThis.__vpole) P.armR.pole = V3(Math.sin(M.V.yaw), 0, Math.cos(M.V.yaw)).applyAxisAngle(V3(0, 1, 0), EDGE.Y(0) ).add(V3(...globalThis.__vpole)).normalize().toArray();
  const clamp1 = ramp(t, S.b06 - 0.02, S.b06 + 0.22, 'out');
  P.armL = clamp1 > 0 ? { preset: 'cover_mouth', from: 'belly', mix: clamp1, hand: { curl: 0.18, cup: 0.45, spread: 0.1 } } : knot('L');
  // ---- feet: a small involuntary shuffle-dance under the hem while it fights the laugh
  if (quiver > 0) { P.walk = { amount: 0.22 * quiver, phase: (t - S.b06) * 1.9, style: 'waddle' }; P.extra.hem = 0.3 * quiver; }
  P.extra.stars = 1 + 0.6 * quiver;
  // ---- face
  const b5 = S.b05;
  const facePre = () => {
    // round, uncertain eyes on the approaching stranger -> wide-eyed small 'o' recoil -> frozen at the arm
    const surpr = pulse(t, S.arrive - 0.25, 0.18, 0.9, 0.9);
    const face = VX([['hopeful', 1 - surpr], ['surprised', surpr]], {});
    face.browIn += 0.18 * surpr; face.browOut += 0.22 * surpr;
    face.mOpen = lerp(0.04, 0.17, surpr); face.mRound = lerp(0.3, 0.95, surpr); face.mWide = -0.3 * surpr;
    if (t > S.contact - 0.1) {
      const fz = ramp(t, S.contact - 0.05, S.contact + 0.08);
      const f2 = VX('flinch', { mOpen: 0.08, mRound: 0.6, browIn: 0.7, browOut: 0.6, lidU: 1.3 });
      for (const kk in f2) if (typeof f2[kk] === 'number') face[kk] = lerp(face[kk], f2[kk], fz);
    }
    face.saccade = 0.3;
    return face;
  };
  const facePost = () => {
    // the staged read of the joke (screenplay s03b05 timings) — unfocused listening -> skeptical wisp -> really? ->
    // the smile behind the eyes -> the corners twitch -> squeezed arcs
    const face = VX('listen', { mPress: 0.3, mSmile: 0.02, lidU: 0.87, lidL: 0.12, browAsym: 0.05, saccade: 0, pupil: 1.15 });
    const skept = ramp(t, b5 + 0.8, b5 + 1.0, 'out');
    const really = ramp(t, b5 + 1.4, b5 + 1.6);
    const lowerUp = ramp(t, b5 + 2.0, b5 + 2.25);
    const arcs = ramp(t, b5 + 3.2, b5 + 3.32, 'out');
    face.browOutL = (face.browOut ?? 0) + 0.7 * skept;             // its LEFT outer wisp (camera side) lifts
    face.browOutR = (face.browOut ?? 0) - 0.08 * skept;
    face.browInL = face.browIn; face.browInR = face.browIn - 0.15 * skept;
    face.lidU = lerp(face.lidU, 0.74, really); face.lidL = lerp(face.lidL, 0.32, really); face.pupil = lerp(face.pupil, 0.95, really);
    face.lidL = lerp(face.lidL, 0.64, lowerUp);
    face.mPress = lerp(0.3, 0.78, ramp(t, b5 + 1.9, b5 + 2.1)); face.mSmile = 0.02;
    const tw = pulse(t, b5 + 2.6, 0.06, 0.04, 0.1) + pulse(t, b5 + 2.86, 0.06, 0.05, 0.12);
    face.mSmile += 0.34 * tw + 0.22 * ramp(t, b5 + 3.05, b5 + 3.25);
    face.mAsym = 0.15 * tw;
    face.lidU = lerp(face.lidU, 0.3, arcs); face.lidL = lerp(face.lidL, 1, arcs);
    face.browIn = lerp(face.browIn, 0.5, arcs); face.browInL = lerp(face.browInL, 0.5, arcs); face.browInR = lerp(face.browInR, 0.5, arcs);
    face.browOutL = lerp(face.browOutL, 0.35, arcs); face.browOutR = lerp(face.browOutR, 0.3, arcs);
    // b06: hand clamped over the mouth, wet shining arcs, cheeks puffed with the held laugh
    const held = ramp(t, S.b06, S.b06 + 0.3);
    face.mPress = lerp(face.mPress, 0.9, held); face.mSmile = lerp(face.mSmile, 0.6, held); face.wet = 0.9 * held; face.blush = 0.35 * held;
    face.tearL = 0.25 * held; face.tearR = 0.25 * held;
    face.lidU = lerp(face.lidU, 0.24 + 0.04 * Math.sin(t * 2 * Math.PI * 3.1), held);
    face.autoBlink = arcs > 0.5 || t < b5 + 1.4 ? 0 : 1;
    return face;
  };
  P.face = faceSeq(t, [[S.s, facePre], [S.b04 + 0.1, facePost, 0.45]]);
  // ---- gaze: on Jesus walking in; at the arm (down to his hand) / his face / the arm; then unfocused listening
  // (down, toward his side, off the lens, drifting); at 1.4 s the eyes slide to him and narrow
  const hand = () => jesus.anchor('handL');
  const unfocus = () => vd.anchor('eyes').addScaledVector(vd.anchor('mouthDir'), 2.2).addScaledVector(WDIR(-1, 0.15), 1.1)
    .add(V3(0, -1.0 + 0.06 * Math.sin(t * 1.3), 0));
  P.gaze = gazeSched(t, [
    [S.s, () => jE],
    [S.contact + 0.02, hand, 0.06], [S.contact + 0.32, () => jE, 0.08], [S.contact + 0.55, hand, 0.06],
    [S.b04 + 0.25, () => jE, 0.2], [S.earW + 0.05, unfocus, 0.45],
    [b5 + 1.4, () => jesus.anchor('eyes'), 0.2],
  ]);
  P.blinkAt = [S.contact + 0.42, S.contact + 0.66, S.arrive + 0.55, S.earW + 0.02];
  P.speech = false;
  return P;
}
/** outward horizontal normal of the Void's belly at its right-front (30 deg right of its front), stage-fixed (pure) */
const N_RF = WDIR(Math.sin(M.V.yaw - 0.3), Math.cos(M.V.yaw - 0.3));

// ---------------------------------------------------------------------------------------------------------- Jesus
function jesusPose(t, S, st, vd) {
  const { jesus } = st;
  const P = { body: {}, head: {}, armL: { preset: 'rest' }, armR: { preset: 'rest' } };
  // ---- the walk in (continues s02's walk), little hop on the last step, landing on "void"
  let w, yawWalk;
  if (st.walkS02) {
    const q = st.walkS02(t);
    w = { pos: V3(...EDGE.W(q.pos[0], 0, q.pos[1])), phase: q.phase, amount: q.amt };
    yawWalk = EDGE.Y(q.yaw);
  } else {
    const a = V3(...W([-0.1, 0, 0.4])), b = V3(...W(M.JV.p)), u = smooth(clamp((t - S.s) / (S.arrive - 0.1 - S.s)));
    w = { pos: a.clone().lerp(b, u), phase: t * 0.85, amount: 1 - smooth((u - 0.6) / 0.4) };
    yawWalk = Math.atan2(b.x - a.x, b.z - a.z);
  }
  // he finishes the walk 28 cm further out than JV (edgeprops JV_OUT), blended in over his last strides
  const off = V3(...W(JV_OUT)).sub(V3(...W(M.JV.p))).multiplyScalar(ramp(t, S.arrive - 0.75, S.arrive - 0.1));
  // during the user's close-up (b02, the pair offscreen) he sidles in round its right flank to the HUG mark (edgeprops
  // JV_HUG: 14 cm closer, swung round toward its side) so hip and sleeve touch the velvet for the arm around it
  const hug = V3(...W(globalThis.__hug ? hugMark(...globalThis.__hug) : JV_HUG)).sub(V3(...W(JV_OUT))).multiplyScalar(ramp(t, S.b02 + 0.2, S.b02e - 0.15));
  P.pos = w.pos.add(off).add(hug).toArray();
  // b04: he pivots toward the Void as he rises onto his toes (whispers into the side of its hood); b06 back to 0.2
  const JYH = globalThis.__jy ?? JYAW;
  const yawMark = EDGE.Y(k(t, [[S.b02 + 0.2, JYAW], [S.b02e - 0.1, JYH, 'inOut'], [S.whispW - 0.1, JYH], [S.whispW + 0.6, JYAW_W, 'inOut'], [S.b06 - 0.05, JYAW_W], [S.b06 + 0.6, JYAW_6, 'inOut']]));
  // turn toward the camera side during the hop (he swings round to his left)
  let dy = yawMark - yawWalk; while (dy > Math.PI) dy -= 2 * Math.PI; while (dy < -Math.PI) dy += 2 * Math.PI;
  const turn = ramp(t, S.arrive - 0.5, S.arrive + 0.15, 'inOut');
  P.yaw = yawWalk + dy * turn;
  P.walk = { amount: w.amount, phase: w.phase, style: 'walk' };
  const hop = k(t, [[S.arrive - 0.42, 0], [S.arrive - 0.3, -0.022, 'inOut'], [S.arrive - 0.14, 0.065, 'out'], [S.arrive, 0, 'in'], [S.arrive + 0.06, -0.022, 'out'], [S.arrive + 0.3, 0, 'inOut']]);
  P.body.bounce = hop;
  P.body.crouch = 0.12 * pulse(t, S.arrive - 0.02, 0.06, 0.03, 0.25) + 0.06 * pulse(t, S.arrive - 0.36, 0.06, 0, 0.1);
  // ---- gaze/head targets
  const vEyes = vd ? vd.anchor('eyes') : V3(...EDGE.W(0.62, 2.16, -0.75));
  const lookUp = ramp(t, S.arrive - 0.45, S.arrive + 0.05);
  P.gaze = vEyes;
  // on the landing his head is cheated a little toward the lens (the eyes still beam up at the Void)
  P.head = { look: vEyes, follow: 0.3 + 0.12 * lookUp, yaw: -0.18 * lookUp * (1 - ramp(t, S.b02, S.b03)) };
  // ---- arm around (b03): LEFT palm onto the velvet of its right flank, below his shoulder, round toward its back;
  // elbow down and back, forearm along the velvet
  const reach = k(t, [[S.armW - 0.22, 0], [S.contact - 0.12, 0.8, 'inOut'], [S.contact, 1, 'out']]);
  if (vd && reach > 0) {
    const c = globalThis.__ac ? aroundContact(vd, jesus, ...globalThis.__ac) : aroundContact(vd, jesus);
    // the pat that settles it on "it" (the forearm lifts 4.5 cm and taps down)
    const pat = pulse(t, S.pat - 0.1, 0.09, 0.0, 0.11);
    // swing: before contact the hand comes round from his side, a little higher and out from the velvet
    const pre = 1 - smooth((reach - 0.5) / 0.5);
    P.armL = aroundArm(c, reach, 0.045 * pat + 0.1 * pre * reach);
    const RY = globalThis.__ray;
    if (RY) { P.armL = { preset: 'around', surface: vd, height: RY.h, span: RY.span, reach, hand: { curl: 0.18, spread: 0.32, cup: 0.25, thumb: 0.45 } }; if (RY.pole) P.armL.pole = RY.pole; }
    P.body.tilt = 0.1 * reach;                          // leans into the Void (+ = toward his left)
    P.head.roll = 0.1 * reach;                          // head leans toward it too
  }
  // ---- whisper (b04-b05): up on his toes, RIGHT hand cupped, chest and head turned to the side of its hood
  const wh = k(t, [[S.whispW - 0.05, 0], [S.whispW + 0.6, 1, 'inOut'], [S.b06, 1], [S.b06 + 0.45, 0, 'inOut']]);
  const cup = k(t, [[S.whispW + 0.05, 0], [S.whispW + 0.5, 1, 'out'], [S.b06 - 0.05, 1], [S.b06 + 0.3, 0, 'inOut']]);
  if (wh > 0) {
    const side = vd ? hoodSide(vd) : vEyes;
    P.body.tiptoe = 0.85 * wh;
    P.body.tilt = (P.body.tilt || 0) + 0.06 * wh;
    P.body.lean = 0.03 * wh;
    P.body.twist = 0.12 * wh;
    P.head = { look: side, follow: lerp(P.head.follow, 0.85, wh), roll: 0.05 * wh };
    P.armR = { preset: 'whisper', reach: cup };
    P.gaze = gazeSched(t, [[S.s, vEyes], [S.whispW + 0.2, () => (vd ? vd.anchor('eyes') : vEyes), 0.2], [S.earW + 0.05, side, 0.15],
      [S.b05 + 0.9, () => (vd ? vd.anchor('eyes') : vEyes), 0.08], [S.b05 + 1.25, side, 0.1], [S.b05 + 2.5, () => (vd ? vd.anchor('eyes') : vEyes), 0.08], [S.b05 + 2.9, side, 0.1]]);
  }
  // b06: back on his heels, RIGHT hand at his belt, innocent smile, one "wait for it" nod
  const heels = ramp(t, S.b06 + 0.2, S.b06 + 0.8);
  if (heels > 0) {
    P.armR = cup > 0.02 ? { preset: [['whisper', cup], ['clasp', 1 - cup]] } : { preset: 'clasp' };
    P.head = { look: vEyes, follow: lerp(0.85, 0.5, heels) };
    P.gaze = vEyes;
    P.body.recoil = 0.05 * heels;
  }
  P.head.pitch = (P.head.pitch || 0) + 0.12 * pulse(t, S.theoriesW + 0.35, 0.16, 0.05, 0.3);
  // ---- face (segments cross-fade: no pops)
  const fWalk = () => {
    const beam = ramp(t, S.arrive - 0.2, S.arrive + 0.25);
    const f = JX([['kind', 1 - beam], ['beam', beam]], {});
    f.browIn += 0.3 * beam; f.browOut += 0.35 * beam; f.mOpen = Math.max(f.mOpen ?? 0, 0.1 * beam);
    return f;
  };
  const fArm = () => {                     // hey, buddy: wide smile, eyebrow bounce after the pat
    const f = JX('beam', { mOpen: 0.12 });
    const bounce = pulse(t, S.pat + 0.14, 0.08, 0.05, 0.18);
    f.browIn += 0.5 * bounce; f.browOut += 0.6 * bounce;
    return f;
  };
  const fWhisper = () => {
    const f = JX('whisper');
    const hops = pulse(t, S.whispW + 0.55, 0.07, 0.05, 0.12) + pulse(t, S.earW + 0.05, 0.07, 0.05, 0.12) + pulse(t, S.b05 + 1.75, 0.07, 0.05, 0.14);
    f.browIn += 0.4 * hops; f.browOut += 0.45 * hops;
    // at the dip in the whisper he presses his lips to keep from laughing at his own joke
    const press = pulse(t, S.dip, 0.06, 0.13, 0.1) + pulse(t, S.b05e - 0.08, 0.06, 0.2, 0.2);
    f.mPress = 0.25 + 0.65 * press; f.talk = 0.9 * (1 - press); f.mSmile += 0.1 * press;
    // mouthing a silent "psst" before the whisper audio
    if (t < S.b05) { f.mOpen = 0.04 + 0.08 * Math.max(0, Math.sin((t - S.earW) * 2 * Math.PI * 3.2)) * ramp(t, S.earW, S.earW + 0.2); f.mRound = 0.5; }
    f.saccade = 0.2;
    return f;
  };
  const fInnocent = () => JX([['innocent', 0.8], ['pressed', 0.5]], { browIn: 0.55, browOut: 0.55, mSmile: 0.35 });
  P.face = faceSeq(t, [[S.s, fWalk], [S.b03, fArm, 0.3], [S.whispW, fWhisper, 0.3], [S.b06 + 0.1, fInnocent, 0.35]]);
  P.blinkAt = [S.arrive + 0.45, S.itW + 0.5, S.b06 + 0.6, S.theoriesW + 0.15];
  // one tiny shoulder shake at the dip (keeping his own laugh in)
  P.body.giggle = 0.55 * pulse(t, S.dip + 0.02, 0.08, 0.18, 0.2);
  P.body.shrug = 0.1 * pulse(t, S.dip + 0.02, 0.08, 0.18, 0.2);
  if (t < S.b05 || t > S.b05e) P.speech = false;     // only the whisper vocal drives his mouth
  return P;
}
