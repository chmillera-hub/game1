// s04 cosmic_laughter — the release, built in threes: dead-still hold, a snort (1 star), a giggle (2 stars), then the
// enormous maniacal laugh that coughs up stars and a little spiral galaxy (it rolls down to the user's sneaker) and,
// at the peak, the beach-ball galaxy that hangs in the sky for the rest of Part One.
// Staging: docs/STAGING.md §4 s04 + §1.6 (sky galaxy, little rolling galaxy). Everything keyed to beat refs / words.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth, fbm1, noise1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { speechAt } from '../core/speech.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
import { VX } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, scopeVisible, voidSurface, ensureLittleGalaxy, littleGalaxyAt, drawSkyGalaxy, LITTLE_GALAXY, fitShot, faceSeq, fmix } from './edgeprops.js';

const DEBUG = false;
const M = EDGE.M;
const W = (p) => EDGE.W(p);
const JYAW = 0.2;
const BELLY = { curl: 0.62, spread: 0.12, cup: 0.5, thumb: 0.4 };   // hands clutching its round belly                                       // Jesus's local facing at JV (s03 ends here)

// ---------------------------------------------------------------------------------------------------------- timing
function times() {
  const w = (b, word, fb) => wordT(b, word, fb);
  const S = {
    s: T('s04'), end: T('s04.end'),
    b01: T('s04b01'), b02: T('s04b02'), b03: T('s04b03'), b04: T('s04b04'), b05: T('s04b05'), b06e: T('s04b06.end'),
    laughingW: w('s04b05', 'laughing,', 1.02), maniW: w('s04b05', 'maniacally.', 2.24),
    b07: T('s04b07'), coughingW: w('s04b07', 'coughing', 0.86), starsW: w('s04b07', 'stars', 1.32),
    b09: T('s04b09'), galaxiesW: w('s04b09', 'galaxies.', 0.28), b10: T('s04b10'),
    b11: T('s04b11'), b11e: T('s04b11.end'), b13: T('s04b13'),
  };
  // vocal onsets measured from the vocal files (lip-sync envelopes): snort +0.04, giggle pulses, cough peaks
  S.snort = S.b02 + 0.05;
  S.star1 = S.b02 + 0.1;
  S.gig1 = S.b03 + 0.3; S.gig2 = S.b03 + 0.75;
  S.burst = S.b04;                                                 // the burst lands exactly on the cut
  S.cough1 = T('s04b08') + 0.04; S.cough2 = T('s04b08') + 0.37;
  S.hic1 = S.b10 + 0.04; S.pop = S.b10 + 0.39;                  // the big hiccup: the little galaxy (= edgeprops tPop)
  S.launch = S.b11 + 0.32;                                         // the beach-ball galaxy leaves the mouth
  S.slap1 = S.laughingW + 0.25; S.slap2 = S.slap1 + 0.36;
  S.stamp = S.maniW + 0.02;                                        // the fat-leg stamp lands on "Maniacally"
  S.double = S.b11 + 1.45;                                         // doubles over (the dip between laugh phrases)
  return S;
}

// sanitized Void lip-sync (the s04b10 envelope ends in a NaN in data/lipsync.json)
function voidSpeech(t) {
  const sp = speechAt('VOID', t);
  if (!sp) return null;
  for (const kk of ['open', 'wide', 'round', 'close']) if (!Number.isFinite(sp[kk])) sp[kk] = 0;
  return sp;
}

// the beach-ball galaxy's launch: mouth -> out over the user's head -> up to EDGE.GALAXY.from (world) by s04b11.end
function bigGalaxyFlight(t, S, from) {
  if (t < S.launch) return null;
  if (t >= S.b11e) return null;                                    // from then on marks.galaxyAt() owns it
  const u = clamp((t - S.launch) / (S.b11e - S.launch));
  const a = toV(from), c = V3(...EDGE.W(-1.6, 3.4, 2.2)), b = toV(EDGE.GALAXY.from);
  const e = u < 0.62 ? 0.5 * (1 - Math.pow(1 - u / 0.62, 1.6)) : 0.5 + 0.5 * smooth((u - 0.62) / 0.38);   // sails out over the user, then up into place
  const p = a.clone().multiplyScalar((1 - e) * (1 - e)).addScaledVector(c, 2 * e * (1 - e)).addScaledVector(b, e * e);
  return { pos: p, size: lerp(0.32, EDGE.GALAXY.size, smooth(u * 1.4)), rot: S.launch * 0.15 + 2.2 * (1 - e) + 0.15 * (t - S.launch) };
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  const heads = EDGE.shot([0.45, 1.86, -0.68], { dist: 4.4, yaw: 0, fov: 33, screenY: sy(470), drift: 0.15 });
  const headsIn = EDGE.shot([0.45, 1.86, -0.68], { dist: 3.95, yaw: 0, fov: 33, screenY: sy(470), drift: 0.15 });
  const low = (yaw, dist = 4.2) => EDGE.shot([0.55, 1.95, -0.85], { dist, yaw, pitch: -10, fov: 54, screenY: sy(340), drift: 0.2 });   // yaw >= -16: keeps the seated user out of frame
  const mouthCU = EDGE.shot(EDGE.L(R.voidMouth), { dist: 3.3, yaw: -18, pitch: -4, fov: 33, screenY: sy(470), drift: 0.15 });
  const mouthCU2 = EDGE.shot(EDGE.L(R.voidMouth), { dist: 3.0, yaw: -18, pitch: -4, fov: 33, screenY: sy(470), drift: 0.15 });
  const med = low(-14, 3.4);
  // follow-pan down with the little galaxy: aim at its bounce point, then where it rolls out of frame
  const bp = LITTLE_GALAXY.bounce;
  const medDown = EDGE.shot([bp[0] - 0.05, 0.75, bp[2] + 0.05], { dist: 3.2, yaw: -14, pitch: 6, fov: 54, screenY: sy(560), drift: 0.15 });
  const ots = { ...EDGE.cam('OTS'), fov: 54, drift: 0.25 }; ots.look = EDGE.W(0.3, 0.38, -1.33);
  const otsUp = { ...ots, look: EDGE.W(0.15, 0.72, -1.2) };     // tilts up a little with the galaxy sailing over
  const lost = R.lostShot;
  return [
    [S.s, heads], [S.b03, heads], [S.b04 - 0.01, headsIn, 'inOut'],
    [S.b04, low(-16)], [S.b07 - 0.01, low(-11), 'inOut'],
    [S.b07, mouthCU], [S.b09 - 0.01, mouthCU2, 'linear'],
    [S.b09, med], [S.pop + 0.08, med], [S.pop + 0.75, medDown, 'inOut'], [S.b11 - 0.01, medDown],
    [S.b11, ots], [S.launch + 0.2, ots], [S.launch + 1.1, otsUp, 'inOut'], [S.b13 - 0.01, otsUp],
    [S.b13, lost], [S.end, lost.end],
  ];
}

// ---------------------------------------------------------------------------------------------------------- module
export default {
  id: 's04',
  async setup(app) {
    await loadWords();
    const set = await app.set('EDGE');
    const jesus = await app.char('JESUS'), vd = await app.char('VOID'), user = await app.char('USER');
    const fx = new Particles({ max: 160 });
    scopeVisible(fx.mesh, 's04', 's05');
    set.scene.add(fx.mesh);
    const lg = ensureLittleGalaxy(set);                   // shared prop (self-updating; later scenes call ensureLittleGalaxy too)
    const st = { scene: set.scene, set, jesus, vd, user, fx, lg, look: lookFor('s04', set.look) };
    // reference anchors at fixed times (pure): the Void's mouth when the little galaxy pops / the big one launches
    const S = times();
    st.R = {};
    user.update(S.s, { pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.5, hunch: 0.25 } });
    st.R.userShoulderR = user.anchor('shoulderR');
    st.R.toPair = V3(...W(M.V.p)).setY(1.8).sub(st.R.userShoulderR).normalize().toArray();
    const at = (tt) => { poseAll(tt, S, st, null); return { mouth: vd.anchor('mouth'), eyes: vd.anchor('eyes'), jEyes: jesus.anchor('eyes'), uEyes: user.anchor('eyes'), feet: [user.anchor('footL'), user.anchor('footR')] }; };
    const a0 = at(S.b07 + 0.5);
    st.R.voidMouth = a0.mouth;
    st.R.popFrom = at(S.pop).mouth;
    st.R.launchFrom = at(S.launch).mouth;
    lg.from = st.R.popFrom;
    const a1 = at(S.b13 + 0.5);
    st.R.uEyes = a1.uEyes; st.R.feet = a1.feet;
    // b13 low at sneaker height from the user's right-front (fitted): the right sneaker + the little galaxy in the lower
    // foreground, the user's face 3/4 looking frame-right (up the hill at the pair, who are off-frame right, laughing)
    const ue = EDGE.L(a1.uEyes), ub = EDGE.M.U.yaw - Math.PI / 2 + 0.62;     // bearing: their right, a little to the front
    const pos0 = EDGE.W(ue[0] + 2.35 * Math.sin(ub), 0.42, ue[2] + 2.35 * Math.cos(ub)), look0 = a1.uEyes.toArray();
    const rest = EDGE.W(LITTLE_GALAXY.rest);
    const pts = [[a1.uEyes, 250, 430, 2], [a1.feet[1], 360, 790, 1], [rest, 430, 820, 1]];
    const f1 = fitShot(pts, 44, pos0, look0, { posReg: 1.0, yMin: 0.3, yMax: 0.5, drift: 0.12 });
    const f2 = fitShot(pts.map(([w, x, y, wt]) => [w, x - 10, y + 10, wt]), 40, f1.pos, f1.look, { posReg: 1.0, yMin: 0.3, yMax: 0.5, drift: 0.12 });
    console.log('s04 b13 fit err', f1.err.toFixed(1), f2.err.toFixed(1), JSON.stringify(EDGE.L(f1.pos).map((x) => +x.toFixed(2))));
    st.R.lostShot = f1; st.R.lostShot.end = f2;
    return st;
  },

  async update(t, app, st) {
    const { set, jesus, vd, user, fx, lg } = st;
    st.scene.add(jesus.root, vd.root, user.root);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const S = times();
    applyShot(app.camera, shotAt(t, cams(S, st.R)), t, 4);
    poseAll(t, S, st, app);

    // ---- the little galaxy (shared prop) and the sky galaxy
    const lgs = lg.update(t, { from: st.R.popFrom });
    fx.begin();
    const big = bigGalaxyFlight(t, S, st.R.launchFrom);
    if (big) fx.add(big.pos.toArray(), big.size, 0xd8c0ff, 0.9, big.rot, CELL.galaxy);
    drawSkyGalaxy(fx, t);
    starFx(t, S, st);
    fx.end();

    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t), voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]) });
    st.look = lookFor('s04', set.look);
    if (DEBUG) {
      const f = (v) => '[' + EDGE.L(v).map((x) => x.toFixed(2)).join(',') + ']';
      const pxs = (v) => px(app.camera, v).join(',');
      console.log(`t=${t.toFixed(2)} V.eyes@${pxs(vd.anchor('eyes'))} V.mouth@${pxs(vd.anchor('mouth'))} J.eyes@${pxs(jesus.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} U.feet ${f(user.anchor('footL'))} ${f(user.anchor('footR'))} LG ${lgs ? f(lgs.pos) + '@' + pxs(lgs.pos) + ' ' + lgs.phase : '-'} big ${big ? pxs(big.pos) : '-'}`);
    }
  },
};

// ======================================================================================================== all poses
function poseAll(t, S, st, app) {
  const { jesus, vd, user } = st;
  jesus.update(t, jesusPose(t, S, st, null));          // pre-pass (anchors for the Void's gaze / hand)
  vd.update(t, voidPose(t, S, st));
  jesus.update(t, jesusPose(t, S, st, vd));
  user.update(t, userPose(t, S, st));
}

// ---------------------------------------------------------------------------------------------------------- particles
function starFx(t, S, st) {
  const { fx, vd } = st;
  const mouth = vd.anchor('mouth'), md = vd.anchor('mouthDir');
  const hand = vd.anchor('handL');
  const COLS = [0xffffff, 0xe0d4ff, 0xb8f0ff, 0xffe0f4];
  // b02: ONE star pops out between the fingers, arcs up and twinkles away
  fx.burst({ t, at: S.star1, count: 1, seed: 401, life: 1.7, origin: hand.clone().add(V3(0, 0.06, 0)).addScaledVector(md, 0.1).toArray(),
    vel: [md.x * 0.35, 0.9, md.z * 0.35], spread: [0.02, 0.02, 0.02], gravity: [0, -0.5, 0], drag: 0.5, size: [0.085, 0.085], grow: 0.5,
    color: [0xffffff], fade: [0.03, 0.5], cell: CELL.star, twinkle: true, spin: 1.2 });
  // b03: TWO more squeeze out between the fingers and float up
  for (const [i, at] of [[0, S.gig1], [1, S.gig2]]) {
    fx.burst({ t, at, count: 1, seed: 410 + i, life: 2.0, origin: hand.clone().add(V3(0, 0.04, 0)).addScaledVector(md, 0.12).toArray(),
      vel: [md.x * 0.25 + (i ? 0.12 : -0.12), 0.6, md.z * 0.25], spread: [0.02, 0.02, 0.02], gravity: [0, -0.15, 0], drag: 0.6, size: [0.075, 0.075], grow: 0.5,
      color: [i ? 0xd8f4ff : 0xfff0d8], fade: [0.04, 0.5], cell: CELL.star, twinkle: true, spin: 1 });
  }
  // b04-b06: a few stars escape the laughing crescent on the big "HA"s (sparse, slow)
  const base = { t, life: 2.4, gravity: [0, -0.12, 0], drag: 0.5, size: [0.05, 0.1], grow: 0.6, color: COLS, fade: [0.08, 0.5], twinkle: true, spin: 1.5, wobble: 0.04 };
  const mo = (tb) => vd.anchor('mouth').addScaledVector(md, 0.15).toArray();
  fx.stream({ ...base, seed: 420, t0: S.burst, t1: S.b06e, rate: 3.2, origin: mouth.clone().addScaledVector(md, 0.15).toArray(), vel: [md.x * 0.7, 0.75, md.z * 0.7], spread: [0.35, 0.2, 0.35] });
  // b07/b08: coughs pop out puffs of stars (+ a small nebula wisp), then laughing spills more while the line says it
  for (const [i, at, n] of [[0, S.cough1, 7], [1, S.cough2, 10]]) {
    fx.burst({ ...base, t, at, count: n, seed: 430 + i, life: 2.6, jitter: 0.06, origin: mouth.clone().addScaledVector(md, 0.15).toArray(),
      vel: [md.x * 1.6, 0.9, md.z * 1.6], spread: [0.45, 0.35, 0.45], drag: 0.9, size: [0.04, 0.08], alpha: 0.85 });
    fx.burst({ t, at, count: 1, seed: 440 + i, life: 2.0, origin: mouth.clone().addScaledVector(md, 0.2).toArray(), vel: [md.x * 1.1, 0.12, md.z * 1.1],
      spread: [0.05, 0.05, 0.05], drag: 1.2, size: [0.24, 0.24], grow: 1.6, color: [0xb89cff], alpha: 0.2, fade: [0.1, 0.6], cell: CELL.nebula, spin: 0.4 });
  }
  fx.stream({ ...base, seed: 450, t0: S.coughingW - 0.1, t1: S.starsW + 0.45, rate: 7, origin: mouth.clone().addScaledVector(md, 0.15).toArray(), vel: [md.x * 1.0, 0.85, md.z * 1.0], spread: [0.4, 0.3, 0.4],
    cell: (r) => (r() < 0.12 ? CELL.galaxy : CELL.star) });
  // b09/b10: the first small cough (a few stars) and the big hiccup (stars around the galaxy)
  fx.burst({ ...base, t, at: S.hic1, count: 5, seed: 460, origin: mouth.clone().addScaledVector(md, 0.15).toArray(), vel: [md.x * 1.2, 0.8, md.z * 1.2], spread: [0.35, 0.3, 0.35] });
  fx.burst({ ...base, t, at: S.pop, count: 6, seed: 461, origin: mouth.clone().addScaledVector(md, 0.15).toArray(), vel: [md.x * 1.4, 0.7, md.z * 1.4], spread: [0.5, 0.35, 0.5] });
  // b11: the peak laugh — the air above them fills with slowly drifting stars (sparse; fading out by the end of s04)
  fx.stream({ ...base, seed: 470, t0: S.b11, t1: S.double + 0.5, rate: 9, life: 3.0, origin: mouth.clone().addScaledVector(md, 0.15).toArray(),
    vel: [md.x * 0.9, 1.0, md.z * 0.9], spread: [0.6, 0.35, 0.6], gravity: [0, -0.05, 0], cell: (r) => (r() < 0.15 ? CELL.galaxy : CELL.star) });
  fx.burst({ ...base, t, at: S.launch, count: 10, seed: 480, life: 2.6, origin: mouth.clone().addScaledVector(md, 0.2).toArray(), vel: [md.x * 1.3, 1.4, md.z * 1.3], spread: [0.7, 0.5, 0.7] });
}

// ---------------------------------------------------------------------------------------------------------- the Void
function voidPose(t, S, st) {
  const { jesus } = st;
  const P = { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw), body: {}, head: {}, extra: { stars: 1.6 } };
  const jE = jesus.anchor('eyes');
  // laugh intensity over the scene (0 still, snort/giggle small, the burst, the cough-laugh, the peak, wheezy tail)
  const laugh = k(t, [[S.burst - 0.02, 0], [S.burst + 0.06, 1, 'out'], [S.b06e, 1], [S.b06e + 0.4, 0.55], [S.cough1, 0.25], [S.cough2 + 0.5, 0.35],
    [S.starsW - 0.3, 1, 'inOut'], [S.b09 + 0.2, 0.8], [S.hic1, 0.3], [S.pop + 0.4, 0.3], [S.pop + 0.75, 0.9], [S.b11, 0.9], [S.b11 + 0.15, 1],
    [S.double, 1], [S.double + 0.4, 0.6], [S.b11e, 0.45], [S.b13 + 0.6, 0.18], [S.end, 0.12]]);
  P.extra.laugh = laugh;
  // ---- body
  const hold = 1 - ramp(t, S.snort - 0.02, S.snort + 0.05);
  const snortJolt = pulse(t, S.snort, 0.05, 0.02, 0.3);
  const gig = t > S.b03 && t < S.b03 + 1.3 ? (voidSpeech(t)?.open || 0) : 0;
  const rock = ramp(t, S.b05 - 0.3, S.b05 + 0.3) * (1 - ramp(t, S.b06e, S.b06e + 0.5));
  const coughJ = pulse(t, S.cough1 - 0.03, 0.06, 0.02, 0.3) + pulse(t, S.cough2 - 0.03, 0.06, 0.02, 0.32) + 0.6 * pulse(t, S.hic1 - 0.03, 0.06, 0, 0.25) + 1.2 * pulse(t, S.pop - 0.04, 0.06, 0.03, 0.35);
  const rear = ramp(t, S.b11 + 0.02, S.b11 + 0.3, 'out') * (1 - ramp(t, S.double - 0.15, S.double + 0.35));
  const dbl = ramp(t, S.double - 0.1, S.double + 0.4, 'inOut') * (1 - 0.4 * ramp(t, S.b13 + 0.3, S.end));
  const launchJ = pulse(t, S.launch - 0.05, 0.05, 0.02, 0.35);
  P.body = {
    shrug: 0.55 * snortJolt + 0.18 * gig + 0.12 * (1 - hold) * (t < S.burst ? 1 : 0),
    bounce: 0.022 * snortJolt + 0.018 * gig - 0.01 * coughJ,
    lean: 0.07 * rock * Math.sin((t - S.b05) * 2 * Math.PI * 0.62) + 0.13 * coughJ - 0.12 * rear + 0.32 * dbl + 0.1 * launchJ,
    stretch: 0.06 * rear,
    breathe: t < S.snort ? 0.15 : 1,
    tilt: 0.04 * rock * Math.sin((t - S.b05) * 2 * Math.PI * 0.31),
  };
  const sway = laugh * (0.07 * Math.sin((t - S.burst) * 2 * Math.PI * 0.45) + 0.03 * Math.sin((t - S.burst) * 2 * Math.PI * 1.1));
  // (the rig throws the head back by 0.34 * laugh; counter most of it after the snap so the big crescent faces the lens)
  const face2cam = 0.2 * laugh * ramp(t, S.burst + 0.5, S.burst + 1.0) * (1 - rear);
  P.head = { pitch: -0.18 * pulse(t, S.burst - 0.02, 0.07, 0.15, 0.6) + face2cam + 0.12 * coughJ - 0.15 * rear + 0.12 * dbl + 0.1 * launchJ, roll: sway, yaw: 0.6 * sway };
  // ---- the fat-leg stamp on "Maniacally" (one step in place: right foot lifts and slams)
  const stampU = clamp((t - (S.stamp - 0.34)) / 0.42);
  if (stampU > 0 && stampU < 1) { P.walk = { amount: Math.sin(Math.PI * stampU), phase: 0.5 * stampU, style: 'stomp' }; P.extra.hem = 0.7 * Math.sin(Math.PI * stampU); }
  P.body.bounce += -0.02 * pulse(t, S.stamp, 0.03, 0, 0.18);
  // ---- arms
  const off = ramp(t, S.burst - 0.02, S.burst + 0.12, 'out');            // hand flies off the mouth
  const press = 0.025 * snortJolt;
  if (off < 1) {
    P.armL = { preset: 'cover_mouth', hand: { curl: 0.18, cup: 0.45, spread: 0.1 + 0.5 * (gig > 0 ? 1 : 0) }, offset: [0, 0, -press] };
    if (off > 0) P.armL = { preset: 'belly', from: 'cover_mouth', mix: off };
  } else {
    P.armL = { preset: 'belly', hand: BELLY };
  }
  P.armR = { preset: 'belly', hand: BELLY };
  // slaps the side of its cloak (its LEFT hand, camera side), twice
  const slap = pulse(t, S.slap1 - 0.12, 0.12, 0, 0.12) + pulse(t, S.slap2 - 0.12, 0.12, 0, 0.14);
  if (slap > 0) {
    const sideP = voidSurface(st.vd, 0.9, 0.55, 0.03 + 0.2 * slap);      // the front-left of its round belly (camera side)
    P.armL = { preset: 'pat', target: sideP, reach: Math.min(1, slap * 1.4), hand: { curl: 0.1, spread: 0.3 } };
  }
  // b09/b10: the hand (LEFT) reaches after the little galaxy and misses (behind it, too late)
  const grab = pulse(t, S.pop + 0.08, 0.16, 0.12, 0.3);
  if (grab > 0) {
    const lgs = littleGalaxyAt(t - 0.12, { from: st.R?.popFrom });
    if (lgs) P.armL = { preset: 'reach', target: lgs.pos.clone().add(V3(0, 0.18, 0)), reach: grab, hand: { curl: 0.2 + 0.6 * ramp(t, S.pop + 0.3, S.pop + 0.45), spread: 0.4 } };
  }
  // b11: arms flung wide as it rears up; then doubles over — RIGHT hand onto Jesus's (near, left) shoulder for support
  const wide = rear;
  if (wide > 0) { P.armL = { preset: 'up', from: 'belly', mix: wide }; P.armR = { preset: 'up', from: 'belly', mix: wide }; }
  const lean = ramp(t, S.double + 0.05, S.double + 0.45, 'out');
  if (lean > 0) {
    const sh = jesus.anchor('shoulderL').add(V3(0, 0.07, 0));
    P.armR = { preset: 'pat', target: sh, reach: lean, hand: { curl: 0.25, spread: 0.2, cup: 0.4 } };
    P.armL = { preset: 'belly', hand: BELLY };
  }
  // b13: wiping one eye (its LEFT hand at its eye), still shaking with leftover giggles
  const wipe = ramp(t, S.b13 + 0.25, S.b13 + 0.65) * (1 - ramp(t, S.end - 0.35, S.end));
  if (wipe > 0) {
    const e = st.vd.anchor('eyes').add(V3(0, -0.05, 0)).addScaledVector(st.vd.anchor('mouthDir'), 0.18);
    P.armL = { preset: 'chin', target: e, reach: wipe };
  }
  // ---- face
  let face;
  if (t < S.burst) {
    // dead still: arcs -> blank round eyes -> slow blink -> lower lids twitch -> snort squeeze -> giggle
    const round = ramp(t, S.s + 0.05, S.s + 0.3);
    face = VX('neutral', { lidU: lerp(0.28, 1.12, round), lidL: lerp(1, 0.04, round), browIn: 0.35, browOut: 0.25, mPress: 0.85, mSmile: 0.35, saccade: 0, autoBlink: 0, wet: 0.6 });
    const tw = pulse(t, S.b01 + 0.55, 0.04, 0.02, 0.08) + 0.8 * pulse(t, S.b01 + 0.7, 0.04, 0.02, 0.08) + pulse(t, S.b01 + 0.8, 0.03, 0.04, 0.06);
    face.lidL += 0.32 * tw;
    const sq = ramp(t, S.snort - 0.02, S.snort + 0.06, 'out');
    face.lidU = lerp(face.lidU, 0.2, sq); face.lidL = lerp(face.lidL, 1, sq);
    const flutter = t > S.b03 ? 0.18 * Math.sin((t - S.b03) * 2 * Math.PI * 4.4) * (gig > 0.05 ? 1 : 0.3) : 0;
    face.browIn = lerp(face.browIn, 0.55, sq) + flutter; face.browOut = lerp(face.browOut, 0.4, sq) + 0.6 * flutter;
    face.wet = lerp(0.6, 1, sq); face.tearL = 0.3 * ramp(t, S.b03, S.b03 + 0.6); face.tearR = face.tearL;
    face.mSmile = lerp(0.35, 0.8, sq); face.blush = 0.35 * sq;
  } else {
    face = VX('laugh', { tearL: 0.22, tearR: 0.22, wet: 1, mOpen: 0.78, mWide: 1.0 });       // lip-sync of the laugh vocal pumps the mouth wider on each HA
    face.lidU = 0.22 - 0.08 * Math.max(0, Math.sin(t * 2 * Math.PI * 1.6)); face.lidL = 1;
    face.browIn += 0.15 * pulse(t, S.burst, 0.06, 0.2, 0.6); face.browOut += 0.2 * pulse(t, S.burst, 0.06, 0.2, 0.6);
    // b07: eyes pop open in surprise at the first puff, it looks at its stars; then laughs harder
    const popOpen = pulse(t, S.cough1 + 0.02, 0.06, 0.65, 0.25);
    face.lidU = lerp(face.lidU, 1.38, popOpen); face.lidL = lerp(face.lidL, 0.05, popOpen);
    face.mRound = lerp(face.mRound, 0.8, popOpen); face.mWide = lerp(face.mWide, 0.1, popOpen);
    face.browIn += 0.35 * popOpen; face.browOut += 0.3 * popOpen;
    // b09: the hiccup: eyes go wide and cross for 4 frames as the galaxy shoots out
    const cross = pulse(t, S.pop - 0.01, 0.03, 0.17, 0.12);
    face.lidU = lerp(face.lidU, 1.42, cross); face.lidL = lerp(face.lidL, 0.0, cross); face.mRound = lerp(face.mRound, 0.9, cross);
    // b11: eyes clenched, mouth enormous; then the wheezy squeak
    face.mOpen = lerp(face.mOpen, 1.0, 0.6 * ramp(t, S.b11, S.b11 + 0.2)) ;
    const wheeze = ramp(t, S.double + 0.2, S.double + 0.6);
    face.mOpen = lerp(face.mOpen, 0.45, wheeze); face.mRound = lerp(face.mRound, 0.45, wheeze);
    // b13: leftover giggles
    const tail = ramp(t, S.b13 + 0.1, S.b13 + 0.8);
    const g = VX('giggle', { tearL: 0.25, tearR: 0.25, wet: 1, lidU: 0.3, lidL: 1 });
    for (const kk in g) if (typeof g[kk] === 'number' && typeof face[kk] === 'number') face[kk] = lerp(face[kk], g[kk], tail);
    face.autoBlink = 0; face.saccade = 0;
  }
  P.face = face;
  // gaze: on Jesus during the hold; up at its stars after the first cough; crossed at the galaxy; else eyes are closed arcs
  const md = st.vd.anchor('mouthDir'), mo = st.vd.anchor('mouth');
  const blank = () => st.vd.anchor('eyes').addScaledVector(st.vd.anchor('mouthDir'), 3).add(V3(0, -0.25, 0));
  P.gaze = gazeSched(t, [
    [S.s, blank], [S.snort - 0.05, () => jE, 0.08],
    [S.cough1 + 0.08, () => mo.clone().addScaledVector(md, 0.9).add(V3(0, 0.8, 0)), 0.12],
    [S.cough2 + 0.15, () => mo.clone().addScaledVector(md, 0.7).add(V3(0, 1.2, 0)), 0.2],
    [S.pop - 0.01, () => mo.clone().addScaledVector(md, 0.28), 0.04],
    [S.pop + 0.2, () => littleGalaxyAt(t, { from: st.R?.popFrom })?.pos || mo, 0.1],
  ]);
  P.blinkAt = [S.b01 + 0.32];
  P.speech = voidSpeech(t) || false;
  return P;
}

// ---------------------------------------------------------------------------------------------------------- Jesus
function jesusPose(t, S, st, vd) {
  const { jesus } = st;
  const P = { pos: W(M.JV.p), yaw: EDGE.Y(JYAW), body: {}, head: {}, armR: { preset: 'clasp' } };
  const vEyes = vd ? vd.anchor('eyes') : V3(...EDGE.W(0.78, 2.15, -0.7));
  // ---- arm around: LEFT palm on the velvet of its upper side; pats its back in rhythm at the peak
  if (vd) {
    const sh = jesus.anchor('shoulderL');
    const hgt = lerp(1.5, 1.32, ramp(t, S.b11, S.b11 + 0.3));
    let best = null, bd = 1e9;
    for (let a = -1.4; a <= -0.6; a += 0.04) {
      const p = voidSurface(vd, hgt, a, 0.015);
      const d = Math.abs(p.distanceTo(sh) - 0.42) + 0.6 * Math.abs(a + 1.0);
      if (d < bd) { bd = d; best = p; }
    }
    const patOn = ramp(t, S.b11 + 0.3, S.b11 + 0.5) * (1 - ramp(t, S.b13 + 0.2, S.b13 + 0.5));
    const pat = patOn * Math.max(0, Math.sin((t - S.b11) * 2 * Math.PI * 2.1));
    best.add(V3(0, 0.07 * pat, 0));
    P.armL = { preset: 'around', target: best, reach: 1 };
  }
  // ---- body
  const giggle = k(t, [[S.b03 + 0.1, 0], [S.b03 + 0.3, 0.8], [S.burst, 0.8], [S.burst + 0.1, 1], [S.b07, 0.9], [S.pop, 0.4], [S.pop + 0.5, 0.2], [S.pop + 0.7, 0.9], [S.b11e, 0.9], [S.b13 + 0.4, 0.6]]);
  P.body.giggle = giggle;
  const dodge = pulse(t, S.pop + 0.02, 0.12, 0.25, 0.4);
  P.body.recoil = 0.28 * dodge + 0.06 * ramp(t, S.burst, S.burst + 0.3);
  P.body.breathe = t < S.snort ? 0.2 : 1;
  // ---- head / gaze
  const lgs = littleGalaxyAt(t, { from: st.R?.popFrom });
  P.gaze = gazeSched(t, [
    [S.s, () => vEyes],
    [S.pop + 0.05, () => (lgs ? lgs.pos : vEyes), 0.06],
    [S.pop + 0.95, () => vEyes, 0.15],
    [S.launch + 0.35, () => (bigGalaxyFlight(t, S, st.R?.launchFrom || vEyes)?.pos || toV(EDGE.GALAXY.from)), 0.12],
    [S.launch + 1.05, () => vEyes, 0.15],
  ]);
  const nod = 0.12 * pulse(t, S.snort + 0.25, 0.12, 0.05, 0.2) + 0.1 * pulse(t, S.snort + 0.55, 0.1, 0.05, 0.2);
  const back = 0.2 * ramp(t, S.burst, S.burst + 0.25) * (1 - ramp(t, S.b07, S.b07 + 0.3)) + 0.25 * ramp(t, S.b13, S.b13 + 0.4);
  P.head = { look: P.gaze, follow: 0.45 - 0.1 * dodge, pitch: nod - back };
  // ---- arms (right): belt -> hand on chest for the giggle -> knuckle wipes an eye -> belt
  const heart = ramp(t, S.b03 + 0.15, S.b03 + 0.5) * (1 - ramp(t, S.burst + 0.6, S.burst + 1.0));
  const wipe = ramp(t, S.laughingW - 0.3, S.laughingW + 0.15) * (1 - ramp(t, S.maniW + 0.1, S.maniW + 0.5));
  if (heart > 0) P.armR = { preset: [['clasp', 1 - heart], ['heart', heart]] };
  if (wipe > 0) P.armR = { preset: [['clasp', 1 - wipe], ['wipe_eye', wipe]] };
  // ---- face (segments cross-fade; the burst is a cut)
  const fHold = () => JX('pressed', { browIn: 0.6, browOut: 0.55, lidU: 1.05, mPress: 0.95, mSmile: 0.25 });
  const fRight = () => JX('beam', { mOpen: 0.05, browIn: 0.65, browOut: 0.7 });          // "right?"
  const fGiggle = () => JX('giggle', { mOpen: 0.08, mTeethU: 1, lidU: 0.45, lidL: 0.8, browIn: 0.5 });
  const fLaugh = () => {
    const f = JX('laugh', { mOpen: 0.42 });
    const ooh = pulse(t, S.pop + 0.02, 0.08, 0.5, 0.25);
    const o2 = JX('ooh', { mOpen: 0.32 });
    for (const kk in o2) if (typeof o2[kk] === 'number') f[kk] = lerp(f[kk], o2[kk], ooh);
    const up = pulse(t, S.launch + 0.35, 0.1, 0.55, 0.2);
    f.lidU = lerp(f.lidU, 1.15, up); f.lidL = lerp(f.lidL, 0.2, up); f.browIn += 0.4 * up; f.browOut += 0.5 * up; f.mRound = lerp(f.mRound, 0.6, up);
    return f;
  };
  const face = faceSeq(t, [[S.s, fHold], [S.snort + 0.12, fRight, 0.25], [S.b03 + 0.05, fGiggle, 0.25], [S.burst - 0.06, fLaugh, 0.12]]);
  P.face = face;
  P.blinkAt = [S.b01 + 0.6];
  if (!(t >= T('s04b12') && t <= T('s04b12.end'))) P.speech = false;     // only his soft laugh vocal drives his mouth
  return P;
}

// ---------------------------------------------------------------------------------------------------------- user
// the raised RIGHT hand: palm out toward the pair, out at their right-front at head height (face stays clear)
function defendTarget(st) {
  const sh = st.R.userShoulderR, a = EDGE.Y(M.U.yaw) - 0.95;
  return sh.clone().add(V3(Math.sin(a) * 0.3, 0.2, Math.cos(a) * 0.3));
}
function userPose(t, S, st) {
  const { jesus, vd } = st;
  const P = {
    pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw),
    body: { sit: 1, shrug: 0.5, tremble: 0.4, pant: 0.6, hunch: 0.25 },
    armR: { preset: 'defend', tremble: 0.6, target: defendTarget(st), reach: 1, palm: st.R.toPair },
    extra: { phone: 0.85, tears: 0.45, glisten: 0.6 },
  };
  // phone shield (from s03) lowers back to the prop as the laugh erupts; flattens back on the elbows at the peak
  // phone still up as a shield (s03 end) -> drops to prop on the ground behind them as they flatten back at the peak
  const shield = 1 - ramp(t, S.launch, S.launch + 0.5);
  P.armL = shield > 0 ? { preset: [['prop', 1 - shield], ['shield', shield]] } : { preset: 'prop' };
  const flat = ramp(t, S.launch + 0.1, S.launch + 0.6, 'out');
  const sitUp = ramp(t, S.b13 + 0.15, S.b13 + 0.7);                // leans in to look at the thing by the sneaker
  P.body.recoil = 0.1 * ramp(t, S.burst, S.burst + 0.3) + 0.4 * flat * (1 - 0.55 * sitUp);
  P.body.lean = -0.1 * flat * (1 - sitUp) + 0.12 * sitUp * (1 - 0.6 * ramp(t, S.b13 + 1.0, S.end));
  // gaze: the pair -> the big galaxy (tracks it up) -> the little galaxy at the sneaker -> slowly back up at the pair
  const lgs = littleGalaxyAt(t, {});
  const big = () => bigGalaxyFlight(t, S, st.R?.launchFrom || vd.anchor('mouth'))?.pos || toV(EDGE.GALAXY.from);
  P.gaze = gazeSched(t, [
    [S.s, () => vd.anchor('eyes')],
    [S.launch + 0.15, big, 0.1],
    [S.b13 + 0.25, () => (lgs ? lgs.pos : vd.anchor('eyes')), 0.12],
    [S.b13 + 1.05, () => jesus.anchor('eyes').lerp(vd.anchor('eyes'), 0.5), 0.55],
  ]);
  const upTrack = ramp(t, S.launch + 0.1, S.b11e) * (1 - ramp(t, S.b13, S.b13 + 0.3));
  const down = ramp(t, S.b13 + 0.2, S.b13 + 0.5) * (1 - ramp(t, S.b13 + 1.0, S.b13 + 1.6));
  P.head = { follow: 0.25 + 0.35 * upTrack + 0.3 * down, pitch: 0 };
  // face: terror -> jaw drops as the galaxy passes -> b13 the brows can't decide (left up, right down), jaw hanging
  const drop = ramp(t, S.launch + 0.2, S.launch + 0.7);
  const face = UX([['terror', 1 - 0.5 * drop], ['disbelief', 0.5 * drop]], { pupil: 0.55 });
  face.mOpen = lerp(face.mOpen, 0.6, drop);
  const undecided = ramp(t, S.b13 + 0.8, S.b13 + 1.3);
  face.browInL = face.browIn + 0.35 * undecided; face.browOutL = face.browOut + 0.45 * undecided;
  face.browInR = face.browIn - 0.45 * undecided; face.browOutR = face.browOut - 0.35 * undecided;
  face.autoBlink = 0;
  P.face = face;
  P.blinkAt = [S.b13 + 1.25];
  P.speech = false;
  return P;
}
