// s03 the_whisper — "So Jesus walks right up to the void, / Uh. Sir? That's the void. / puts his arm around it, /
// and starts whispering in its ear. / (whispers a joke) / Nobody knows what he said. I have theories."
// Staging: docs/STAGING.md §4 s03 (marks JV / V / U, cameras two-shot -> USER_CU -> tighter two-shot -> WHISPER ->
// VOID_CU -> pull back to OTS). Everything is keyed to beat refs / word times (re-timed audio re-times the picture).
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth, fbm1, noise1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
const DEBUG = true;
import { VX } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX, headShake } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, scopeVisible, voidSurface } from './edgeprops.js';

const M = EDGE.M;
const W = (p) => EDGE.W(p);
const L3 = (x, y, z) => V3(...EDGE.W(x, y, z));      // local -> world Vector3
const JWALK0 = [-0.1, 0, 0.4];                         // s02 -> s03 continuity: Jesus mid-walk here at the cut
const JSTRIDE = 1.05, JRATE = 0.85;
const JYAW = 0.45;                                     // Jesus's local facing at JV in s03 (open to the camera, the Void on his left)                    // Jesus 'walk' (metres per cycle, cycles/s) — phase = t * rate in s02

// ---------------------------------------------------------------------------------------------------------- timing
function times() {
  const w = (b, word, fb, o) => wordT(b, word, fb, o);
  const S = {
    s: T('s03'), end: T('s03.end'),
    b01: T('s03b01'), voidW: w('s03b01', 'void.', 1.52), rightW: w('s03b01', 'right', 0.82),
    b02: T('s03b02'), sirW: w('s03b02', 'sir,', 0.38), thatsW: w('s03b02', "that's", 1.2), voidW2: w('s03b02', 'void.', 1.62),
    b03: T('s03b03'), armW: w('s03b03', 'arm', 0.32), aroundW: w('s03b03', 'around', 0.56), itW: w('s03b03', 'it', 0.92),
    b04: T('s03b04'), whispW: w('s03b04', 'whispering', 0.32), earW: w('s03b04', 'ear.', 1.16),
    b05: T('s03b05'), b05e: T('s03b05.end'),
    b06: T('s03b06'), saidW: w('s03b06', 'said.', 1.06), iW: w('s03b06', 'i', 2.08), theoriesW: w('s03b06', 'theories.', 2.4),
  };
  S.arrive = S.voidW + 0.06;                           // Jesus's hop lands on "void"
  S.contact = S.aroundW + 0.16;                        // palm lands on the velvet
  return S;
}

// Jesus's walk: decelerating along a straight line from the s02 hand-off to JV, feet planted (phase follows distance)
function jesusWalk(t, S) {
  const a = V3(...W(JWALK0)), b = V3(...W(M.JV.p));
  const len = a.distanceTo(b), v0 = JSTRIDE * JRATE;
  const dur = S.arrive - 0.12 - S.s;                   // feet stop just before the hop lands
  const p = 1.6;                                       // s(u) = len * (1 - (1-u)^p) has initial speed p*len/dur
  const durN = Math.max(dur, (p * len) / v0);
  const u = clamp((t - S.s) / durN);
  const s = len * (1 - Math.pow(1 - u, p));
  const phase0 = S.s * JRATE;                          // continuous with s02's phase = t * rate at the cut
  return { pos: a.clone().lerp(b, s / len), phase: phase0 + s / JSTRIDE, amount: 1 - smooth((u - 0.55) / 0.45), u, dir: b.clone().sub(a).normalize() };
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  const two = EDGE.shot([0.45, 1.75, -0.9], { dist: 5.7, yaw: -5, pitch: 3, fov: 44, screenY: sy(420), drift: 0.3 });
  const twoIn = EDGE.shot([0.45, 1.75, -0.9], { dist: 5.3, yaw: -5, pitch: 3, fov: 44, screenY: sy(420), drift: 0.3 });
  const userCU = EDGE.shot(EDGE.L(R.userEyes), { dist: 1.5, yaw: 118, pitch: 3, fov: 33, screenY: sy(420), drift: 0.25 });
  const userCU2 = EDGE.shot(EDGE.L(R.userEyes), { dist: 1.38, yaw: 118, pitch: 3, fov: 33, screenY: sy(420), drift: 0.25 });
  const tight = EDGE.shot([0.45, 1.62, -0.85], { dist: 3.6, yaw: -15, pitch: 3, fov: 44, screenY: sy(450), drift: 0.3 });
  const whisper = EDGE.shot([0.36, 1.62, -0.6], { dist: 3.3, yaw: 2, pitch: 2, fov: 33, screenY: sy(410), drift: 0.25 });
  const cuLook = EDGE.L(R.voidEyesBent); cuLook[0] -= 0.3; cuLook[1] -= 0.06; cuLook[2] += 0.02;
  const voidCU = EDGE.shot(cuLook, { dist: 3.4, yaw: -6, pitch: -3, fov: 33, screenY: sy(390), drift: 0.2 });
  const voidCU2 = EDGE.shot(cuLook, { dist: 3.1, yaw: -6, pitch: -3, fov: 33, screenY: sy(380), drift: 0.2 });
  const ots = EDGE.cam('OTS', { drift: 0.3 });
  return [
    [S.s, two], [S.b02 - 0.04, twoIn, 'linear'],
    [S.b02 - 0.04 + 1e-3, userCU], [S.b03 - 0.06, userCU2, 'linear'],
    [S.b03 - 0.06 + 1e-3, tight], [S.b04 + 0.1, tight],
    [S.b05 - 0.02, whisper, 'inOut'],
    [S.b05 - 0.02 + 1e-3, voidCU], [S.b06 + 0.05, voidCU2, 'linear'],
    [S.b06 + 2.0, ots, 'inOut'], [S.end, ots],
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
    // reference anchors (for camera aims): pose once at the marks
    const t0 = T('s03b05');
    user.update(t0, userBase(t0));
    vd.update(t0, { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw), ...listenBend(1) });
    const R = { userEyes: user.anchor('eyes'), userShoulderR: user.anchor('shoulderR'), voidEyesBent: vd.anchor('eyes') };
    vd.update(t0, { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw) });
    R.voidEyes = vd.anchor('eyes'); R.voidMouth = vd.anchor('mouth');
    jesus.update(t0, { pos: W(M.JV.p), yaw: EDGE.Y(M.JV.yaw) });
    R.jesusEyes = jesus.anchor('eyes'); R.jesusMouth = jesus.anchor('mouth');
    return { scene: set.scene, set, jesus, vd, user, fx, R, look: lookFor('s03', set.look) };
  },

  async update(t, app, st) {
    const { set, jesus, vd, user, fx, R } = st;
    st.scene.add(jesus.root, vd.root, user.root);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const S = times();
    // camera first (eye catchlights read CTX.camera during the rig updates)
    applyShot(app.camera, shotAt(t, cams(S, R)), t, 3);

    // ---------------------------------------------------------------- JESUS pre-pass (for the Void's gaze)
    const jp0 = jesusPose(t, S, st, null);
    jesus.update(t, jp0);
    // ---------------------------------------------------------------- VOID
    const vp = voidPose(t, S, st);
    vd.update(t, vp);
    // ---------------------------------------------------------------- JESUS final (arm around the Void's real surface)
    jesus.update(t, jesusPose(t, S, st, vd));
    // ---------------------------------------------------------------- USER
    user.update(t, userPose(t, S, st));

    // ---------------------------------------------------------------- particles: the star mote that pops off its shoulder
    fx.begin();
    const tp = S.arrive + 0.1;
    if (t >= tp && t < tp + 2.2) {
      const sh = vd.anchor('shoulderL');
      fx.burst({ t, at: tp, count: 1, seed: 31, life: 1.9, origin: sh.toArray(), vel: [0.05, 0.62, 0.12], spread: [0.02, 0.03, 0.02],
        gravity: [0, -0.18, 0], drag: 0.6, size: [0.07, 0.07], grow: 0.4, color: [0xe8deff], fade: [0.04, 0.55], cell: CELL.star, twinkle: true, spin: 0.6 });
    }
    fx.end();

    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (t >= S.b04 && t < S.b06 ? 0.85 : 1), voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]) });
    st.look = lookFor('s03', set.look);
    if (DEBUG) {
      const f = (v) => '[' + EDGE.L(v).map((x) => x.toFixed(2)).join(',') + ']';
      const pxs = (v) => px(app.camera, v).join(',');
      console.log(`t=${t.toFixed(2)} J.mouth ${f(jesus.anchor('mouth'))} V.rim ${f(hoodRimR(vd))} d=${jesus.anchor('mouth').distanceTo(hoodRimR(vd)).toFixed(2)} V.eyes ${f(vd.anchor('eyes'))}@${pxs(vd.anchor('eyes'))} J.eyes@${pxs(jesus.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} J.handL ${f(jesus.anchor('handL'))} V.handR ${f(vd.anchor('handR'))} J.root ${f(jesus.root.position)}`);
    }
  },
};

// ======================================================================================================== poses
// the raised RIGHT hand: palm out toward the Void at shoulder/chin height, forward of the face (never across it)
function defendTarget(st) {
  const sh = st.R.userShoulderR;                         // setup reference (pure: never read a rig's previous frame)
  const toV = V3(...W(M.V.p)).setY(1.6).sub(sh).normalize();
  return sh.clone().addScaledVector(toV, 0.36).add(V3(0, 0.12, 0));
}
function userBase(t) {
  return {
    pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw),
    body: { sit: 1, shrug: 0.5, tremble: 0.45, pant: 0.6, hunch: 0.25 },
    face: UX('terror', { mOpen: 0.28, pupil: 0.55 }),
    armR: { preset: 'defend', tremble: 0.7 }, armL: { preset: 'prop' },
    extra: { phone: 0.85, tears: 0.45, glisten: 0.6 },
  };
}

function userPose(t, S, st) {
  const P = userBase(t);
  const { jesus, vd } = st;
  const jE = jesus.anchor('eyes'), vE = vd.anchor('eyes');
  // b02: whisper-yell — lean forward, eyes flick Jesus/Void x2, feeble flap, two tiny head shakes on "void"
  const lean = k(t, [[S.b02 - 0.2, 0], [S.b02 + 0.15, 0.2, 'out'], [S.b03 - 0.2, 0.17], [S.b03 + 0.4, 0.04]]);
  P.body.lean = lean;
  P.body.shrug = 0.5 + 0.15 * pulse(t, S.voidW2 - 0.1, 0.12, 0.2, 0.3);
  P.gaze = gazeSched(t, [
    [S.s, () => vE],
    [S.b02 - 0.15, () => jE], [S.b02 + 0.2, () => vE, 0.07], [S.sirW - 0.04, () => jE, 0.07],
    [S.thatsW - 0.1, () => vE, 0.07], [S.voidW2 - 0.2, () => jE, 0.07], [S.voidW2 + 0.35, () => vE, 0.07],
    [S.b03 + 0.5, () => jesus.anchor('handL'), 0.12], [S.b04 + 0.4, () => vE, 0.12],
  ]);
  const sh = headShake(t, S.voidW2 + 0.02, { count: 2, dur: 0.42, amp: 0.13 });
  P.head = { yaw: sh.yaw, pitch: -0.05 + 0.08 * pulse(t, S.b02, 0.2, 1.6, 0.4), follow: 0.35 };
  P.extra.hairSwing = sh.hairSwing;
  // the face: terror softened into an urgent whisper-yell during the line (lip-sync rides on top)
  const yell = ramp(t, S.b02 - 0.15, S.b02 + 0.1) * (1 - ramp(t, S.b03 - 0.1, S.b03 + 0.4));
  P.face = UX([['terror', 1 - 0.55 * yell], ['worried', 0.55 * yell]], { browIn: 1.0, browSq: 0.5, mWide: 0.4 + 0.5 * pulse(t, S.voidW2 - 0.05, 0.1, 0.18, 0.25), pupil: 0.55 });
  P.armR = { preset: 'defend', tremble: 0.7, flap: pulse(t, S.sirW + 0.02, 0.14, 0.04, 0.22), target: defendTarget(st), reach: 1 };
  // b03..: watching the arm go around (mouth falls open); b06: phone up as a shield, one slow blink
  const shield = ramp(t, S.b06 + 0.35, S.b06 + 0.85, 'out');
  if (shield > 0) P.armL = { preset: [['prop', 1 - shield], ['shield', shield]] };
  P.blinkAt = [S.b02 + 1.35, S.iW - 0.3];
  if (t > S.b03) P.face.mOpen = Math.max(P.face.mOpen, 0.32 * ramp(t, S.contact, S.contact + 0.3));
  return P;
}

// The Void's "listening" bend toward Jesus (its right): body like whisperPose(-1, d), hood tipped so its right ear goes down
function listenBend(a, d = 1) {
  // bends its knees (crouch) and tips its hood toward its RIGHT (roll +: the right side goes down) so the front-right rim
  // of the hood comes down beside Jesus's mouth; hardly any forward lean (he stands right at its front-right corner)
  return {
    body: { lean: 0.04 * d * a, crouch: 0.6 * d * a, tilt: -0.04 * a, twist: 0.1 * a },
    head: { yaw: 0.5 * a, pitch: 0.04 * a, roll: 0.45 * a },
  };
}
/** the point on the front-right rim of the hood that Jesus whispers into (world) */
export function hoodRimR(vd) { return vd.headGroup.localToWorld(V3(-0.6, -0.05, 0.5)); }

function voidPose(t, S, st) {
  const { jesus } = st;
  const P = { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw), body: {}, head: {}, extra: { stars: 1 } };
  const jE = jesus.anchor('eyes');
  // ---- body: knotted hands -> recoil on his arrival -> freeze/shrug at the arm -> listening bend -> clamp + quiver
  const recoil = k(t, [[S.arrive - 0.32, 0], [S.arrive - 0.05, 0.34, 'out'], [S.arrive + 0.35, 0.24], [S.b03, 0.18], [S.contact, 0.12], [S.b04 + 0.2, 0]]);
  const bendA = k(t, [[S.b04 + 0.15, 0], [S.earW + 0.25, 1, 'inOut'], [S.b06 + 0.05, 1], [S.b06 + 0.75, 0, 'inOut']]);
  const B = listenBend(bendA);
  const freeze = pulse(t, S.contact - 0.02, 0.1, 0.45, 0.4);
  const quiver = ramp(t, S.b06 + 0.05, S.b06 + 0.35);
  P.body = { ...B.body, recoil, shrug: 0.4 * freeze + 0.12 * quiver };
  P.body.bounce = 0.008 * quiver * Math.sin(t * 2 * Math.PI * 7.3) + 0.004 * quiver * Math.sin(t * 2 * Math.PI * 4.1);
  P.body.breathe = 1 - 0.8 * freeze;
  P.head = { ...B.head };
  P.head.pitch = (P.head.pitch || 0) - 0.06 * pulse(t, S.arrive - 0.15, 0.2, 0.3, 0.5);
  // ---- arms: hands knotted at its middle (s02 end) -> float up 4 cm at the arm, sink -> left hand clamps over its mouth
  const chest = vd => vd;
  // hands knotted at its middle, a little toward its LEFT (Jesus stands at its front-right: keep the right hand off him)
  const vdd = st.vd;
  const knot = (side) => {
    const lift = 0.04 * pulse(t, S.contact + 0.05, 0.22, 0.2, 0.35);
    const tgt = voidSurface(vdd, 0.9 - 0.12 * bendA + lift, side === 'L' ? 0.45 : 0.15, 0.1);
    return { preset: 'belly', target: tgt, reach: 1, hand: { curl: 0.55, spread: 0.05, cup: 0.5 } };
  };
  P.armR = knot('R');
  const clamp1 = ramp(t, S.b06 - 0.02, S.b06 + 0.22, 'out');
  P.armL = clamp1 > 0 ? { preset: 'cover_mouth', from: 'belly', mix: clamp1, hand: { curl: 0.18, cup: 0.45, spread: 0.1 } } : knot('L');
  // ---- feet: a small involuntary shuffle-dance under the hem while it fights the laugh
  if (quiver > 0) { P.walk = { amount: 0.22 * quiver, phase: (t - S.b06) * 1.9, style: 'waddle' }; P.extra.hem = 0.3 * quiver; }
  P.extra.stars = 1 + 0.6 * quiver;
  // ---- face
  const b5 = S.b05;
  let face;
  if (t < S.b04) {
    // round, uncertain eyes on the approaching stranger -> wide-eyed small 'o' recoil -> frozen at the arm
    const surpr = pulse(t, S.arrive - 0.25, 0.18, 0.9, 0.9);
    face = VX([['hopeful', 1 - surpr], ['surprised', surpr]], {});
    face.browIn += 0.15 * surpr; face.browOut += 0.15 * surpr;
    face.mOpen = lerp(0.04, 0.16, surpr); face.mRound = lerp(0.3, 0.95, surpr); face.mWide = -0.3 * surpr;
    if (t > S.contact - 0.1) {
      const fz = ramp(t, S.contact - 0.05, S.contact + 0.08);
      const f2 = VX('flinch', { mOpen: 0.08, mRound: 0.6, browIn: 0.7, browOut: 0.6, lidU: 1.3 });
      for (const kk in f2) if (typeof f2[kk] === 'number') face[kk] = lerp(face[kk], f2[kk], fz);
    }
    face.saccade = 0.3;
  } else {
    // the staged read of the joke (screenplay s03b05 timings) — listening -> skeptical brow -> really? -> smile behind the eyes
    const lis = VX('listen', { mPress: 0.3, mSmile: 0.02, lidU: 0.98, browAsym: 0.1, saccade: 0 });
    face = { ...lis };
    const skept = ramp(t, b5 + 0.8, b5 + 1.0, 'out');
    const really = ramp(t, b5 + 1.4, b5 + 1.6);
    const lowerUp = ramp(t, b5 + 2.0, b5 + 2.25);
    const arcs = ramp(t, b5 + 3.2, b5 + 3.32, 'out');
    face.browOutL = (face.browOut ?? 0) + 0.65 * skept;             // its LEFT outer wisp (camera side) lifts
    face.browOutR = (face.browOut ?? 0) - 0.05 * skept;
    face.browInL = face.browIn; face.browInR = face.browIn - 0.15 * skept;
    face.lidU = lerp(face.lidU, 0.76, really) ; face.lidL = lerp(face.lidL, 0.3, really);
    face.lidL = lerp(face.lidL, 0.62, lowerUp);
    face.mPress = lerp(0.3, 0.75, ramp(t, b5 + 1.9, b5 + 2.1)); face.mSmile = 0.02;
    // the crescent corners twitch twice (2.6 s), then the eyes squeeze into upturned arcs (3.2 s)
    const tw = pulse(t, b5 + 2.6, 0.06, 0.04, 0.1) + pulse(t, b5 + 2.86, 0.06, 0.05, 0.12);
    face.mSmile += 0.32 * tw + 0.22 * ramp(t, b5 + 3.05, b5 + 3.25);
    face.mAsym = 0.15 * tw;
    face.lidU = lerp(face.lidU, 0.3, arcs); face.lidL = lerp(face.lidL, 1, arcs);
    face.browIn = lerp(face.browIn, 0.5, arcs); face.browInL = lerp(face.browInL, 0.5, arcs); face.browInR = lerp(face.browInR, 0.5, arcs);
    face.browOutL = lerp(face.browOutL, 0.35, arcs); face.browOutR = lerp(face.browOutR, 0.3, arcs);
    // b06: hand clamped over the mouth, wet shining arcs, cheeks puffed with the held laugh
    const held = ramp(t, S.b06, S.b06 + 0.3);
    face.mPress = lerp(face.mPress, 0.9, held); face.mSmile = lerp(face.mSmile, 0.6, held); face.wet = 0.9 * held; face.blush = 0.35 * held;
    face.tearL = 0.25 * held; face.tearR = 0.25 * held;
    face.lidU = lerp(face.lidU, 0.24 + 0.04 * Math.sin(t * 2 * Math.PI * 3.1), held);
    face.autoBlink = arcs > 0.5 ? 0 : 1;
  }
  P.face = face;
  // ---- gaze: on Jesus walking in; at the arm (down to his hand) / his face / the arm; then unfocused listening; to him
  const hand = () => jesus.anchor('handL');
  const unfocus = () => vdFwd(st.vd, 3.0, -0.35);
  P.gaze = gazeSched(t, [
    [S.s, () => jE],
    [S.contact + 0.02, hand, 0.06], [S.contact + 0.32, () => jE, 0.08], [S.contact + 0.55, hand, 0.06],
    [S.b04 + 0.25, () => jE, 0.2], [S.earW + 0.1, unfocus, 0.35],
    [b5 + 1.4, () => jesus.anchor('eyes'), 0.18],
  ]);
  P.blinkAt = [S.contact + 0.42, S.contact + 0.66, S.arrive + 0.55];
  P.speech = false;
  return P;
}
// a point `dist` m in front of the Void's face, dropped by `drop` (unfocused listening stare)
function vdFwd(vd, dist, drop) {
  const e = vd.anchor('eyes'), m = vd.anchor('mouthDir');
  return e.clone().addScaledVector(m, dist).add(V3(0, drop, 0));
}

function jesusPose(t, S, st, vd) {
  const { user, jesus } = st;
  const P = { body: {}, head: {}, armL: { preset: 'rest' }, armR: { preset: 'rest' } };
  // ---- the walk in (continues s02's walk), little hop on the last step, landing on "void"
  const w = jesusWalk(t, S);
  P.pos = w.pos.toArray();
  const yawWalk = Math.atan2(w.dir.x, w.dir.z);                 // world yaw along travel (back to camera)
  const yawMark = EDGE.Y(JYAW);                                   // cheated open to camera: the Void at his left
  // turn toward the Void during the hop (decreasing local yaw: he swings round to his left first)
  let dy = yawMark - yawWalk; while (dy > Math.PI) dy -= 2 * Math.PI; while (dy < -Math.PI) dy += 2 * Math.PI;
  const turn = ramp(t, S.arrive - 0.5, S.arrive + 0.15, 'inOut');
  P.yaw = yawWalk + dy * turn;
  P.walk = { amount: w.amount, phase: w.phase, style: 'walk' };
  const hop = k(t, [[S.arrive - 0.42, 0], [S.arrive - 0.3, -0.022, 'inOut'], [S.arrive - 0.14, 0.065, 'out'], [S.arrive, 0, 'in'], [S.arrive + 0.06, -0.022, 'out'], [S.arrive + 0.3, 0, 'inOut']]);
  P.body.bounce = hop;
  P.body.crouch = 0.12 * pulse(t, S.arrive - 0.02, 0.06, 0.03, 0.25) + 0.06 * pulse(t, S.arrive - 0.36, 0.06, 0, 0.1);
  // ---- gaze/head targets
  const vEyes = vd ? vd.anchor('eyes') : st.R.voidEyes.clone();
  const vEarR = vd ? hoodRimR(vd) : st.R.voidEyes.clone();
  const lookUp = ramp(t, S.arrive - 0.45, S.arrive + 0.05);
  P.gaze = vEyes;
  P.head = { look: vEyes, follow: 0.3 + 0.25 * lookUp };
  // ---- arm around (b03): LEFT palm onto the velvet curve of its side, ~0.45 m from his shoulder
  const reach = k(t, [[S.armW - 0.18, 0], [S.contact, 1, 'inOut']]);
  if (vd && reach > 0) {
    const hgt = 1.5;
    const sh = jesus.anchor('shoulderL');
    // pick the surface angle on the Void's RIGHT flank nearest to a point 0.42 m behind-left of his shoulder
    let best = null, bd = 1e9;
    for (let a = -1.4; a <= -0.6; a += 0.04) {
      const p = voidSurface(vd, hgt, a, 0.015);
      const d = Math.abs(p.distanceTo(sh) - 0.42) + 0.6 * Math.abs(a + 1.0);
      if (d < bd) { bd = d; best = [p, a]; }
    }
    const tgt = best[0];
    // the pat that settles it (lift 3 cm, tap)
    const pat = pulse(t, S.itW + 0.02, 0.1, 0.0, 0.12) + 0.5 * pulse(t, S.itW + 0.3, 0.08, 0, 0.1);
    tgt.y += 0.03 * pat;
    // swing: before contact the hand comes round from his side, high
    const pre = 1 - smooth((reach - 0.55) / 0.45);
    tgt.add(V3(0, 0.12 * pre * reach, 0));
    P.armL = { preset: 'around', target: tgt, reach };
  }
  // ---- whisper (b04-b05): up on his toes, RIGHT hand cupped, leaning his mouth to the side of its hood
  const wh = k(t, [[S.whispW - 0.05, 0], [S.whispW + 0.6, 1, 'inOut'], [S.b06, 1], [S.b06 + 0.45, 0, 'inOut']]);
  const cup = k(t, [[S.whispW + 0.05, 0], [S.whispW + 0.5, 1, 'out'], [S.b06 - 0.05, 1], [S.b06 + 0.3, 0, 'inOut']]);
  if (wh > 0) {
    P.body.tiptoe = 0.8 * wh;
    P.body.tilt = 0.12 * wh;
    P.body.lean = 0.05 * wh;
    P.body.twist = 0.25 * wh;
    P.head = { look: vEarR, follow: lerp(P.head.follow, 0.8, wh), roll: -0.08 * wh };
    P.armR = { preset: 'whisper', reach: cup };
  }
  // b06: back on his heels, RIGHT hand at his belt, innocent smile, one "wait for it" nod
  const heels = ramp(t, S.b06 + 0.2, S.b06 + 0.8);
  if (heels > 0) {
    P.armR = cup > 0.02 ? { preset: [['whisper', cup], ['clasp', 1 - cup]] } : { preset: 'clasp' };
    P.head = { look: vEyes, follow: 0.45 };
    P.body.recoil = 0.05 * heels;
  }
  P.head.pitch = (P.head.pitch || 0) + 0.11 * pulse(t, S.theoriesW + 0.35, 0.16, 0.05, 0.3);
  // ---- face
  let face;
  if (t < S.b03) {
    const beam = ramp(t, S.arrive - 0.2, S.arrive + 0.25);
    face = JX([['kind', 1 - beam], ['beam', beam]], {});
    face.browIn += 0.25 * beam; face.browOut += 0.3 * beam;
  } else if (t < S.whispW) {
    face = JX('beam', { mOpen: 0.12 });
    const bounce = pulse(t, S.itW + 0.18, 0.08, 0.05, 0.18);
    face.browIn += 0.45 * bounce; face.browOut += 0.55 * bounce;
  } else if (t < S.b06) {
    face = JX('whisper');
    const hops = pulse(t, S.whispW + 0.55, 0.07, 0.05, 0.12) + pulse(t, S.earW + 0.05, 0.07, 0.05, 0.12) + pulse(t, S.b05 + 1.7, 0.07, 0.05, 0.14);
    face.browIn += 0.4 * hops; face.browOut += 0.45 * hops;
    // between phrases he presses his lips to keep from laughing at his own joke (whisper audio dip ~ +1.5 s)
    const press = pulse(t, S.b05 + 1.42, 0.06, 0.12, 0.12) + pulse(t, S.b05 + 3.3, 0.06, 0.2, 0.2);
    face.mPress = 0.25 + 0.6 * press; face.talk = 0.9 * (1 - press);
    // mouthing a silent "psst" before the whisper audio
    if (t < S.b05) { face.mOpen = 0.04 + 0.08 * Math.max(0, Math.sin((t - S.earW) * 2 * Math.PI * 3.2)) * ramp(t, S.earW, S.earW + 0.2); face.mRound = 0.5; }
    face.saccade = 0.2;
  } else {
    face = JX([['innocent', 0.8], ['pressed', 0.5]], { browIn: 0.55, browOut: 0.55, mSmile: 0.35 });
  }
  P.face = face;
  P.blinkAt = [S.arrive + 0.45, S.itW + 0.5, S.b06 + 0.6, S.theoriesW + 0.15];
  // one tiny shoulder shake mid-whisper (keeping his own laugh in)
  P.body.giggle = 0.5 * pulse(t, S.b05 + 1.45, 0.08, 0.2, 0.2);
  P.body.shrug = 0.08 * pulse(t, S.b05 + 1.45, 0.08, 0.2, 0.2);
  if (t < S.b05 || t > S.b05e) P.speech = false;     // only the whisper vocal drives his mouth
  return P;
}
