// s04 cosmic_laughter — the release, built in threes: dead-still hold, a snort (1 star), a giggle (2 stars), then the
// enormous maniacal laugh that coughs up stars and a little spiral galaxy (it rolls down to the user's sneaker) and,
// at the peak, the beach-ball galaxy that hangs in the sky for the rest of Part One.
// Staging: docs/STAGING.md §4 s04 + §1.6 (sky galaxy, little rolling galaxy; as-built notes there). Everything keyed to
// beat refs / words / the vocal envelopes. Pure function of t.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot, shotAt } from '../core/camera.js';
import { clamp, lerp, smooth } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { speechAt } from '../core/speech.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy, px } from './marks.js';
import { VX } from '../chars/void.js';
import { JX } from '../chars/jesus.js';
import { UX } from '../chars/user.js';
import { V3, toV, loadWords, wordT, pulse, ramp, wobble, gazeSched, scopeVisible, voidSurface, voidNormal, ensureLittleGalaxy, littleGalaxyAt, drawSkyGalaxy, LITTLE_GALAXY, fitShot, faceSeq, fmix,
  fadeSeedsNear, fadeMotesNear, hideDuring, JV_OUT, JV_HUG, AROUND_H, aroundContact, contactAt, aroundArm } from './edgeprops.js';

const DEBUG = false;
const M = EDGE.M;
const W = (p) => EDGE.W(p);
const WDR = (x, z) => { const a = EDGE.W(x, 0, z), o = EDGE.W(0, 0, 0); return V3(a[0] - o[0], 0, a[2] - o[2]); };
const WDIR = (x, z) => WDR(x, z).normalize();
const JYAW = 0.2;                                                    // Jesus's local facing (s03 ends here, s05 starts here)
const BELLY = { curl: 0.62, spread: 0.12, cup: 0.5, thumb: 0.4 };   // hands clutching its round belly
// the Void's belly normal at its right-front (30 deg right of its front) and its LEFT, stage-fixed (pure)
const N_RF = WDIR(Math.sin(M.V.yaw - 0.3), Math.cos(M.V.yaw - 0.3));
const V_LEFT = WDIR(Math.cos(M.V.yaw), -Math.sin(M.V.yaw));
const V_FWD = WDIR(Math.sin(M.V.yaw), Math.cos(M.V.yaw));
/** its RIGHT hand on the belly, forearm out of the velvet (the sleeve reads as a sleeve; the paw stays off Jesus) */
const RIGHT_OUT = () => N_RF.clone().multiplyScalar(0.1).addScaledVector(V_LEFT, 0.3).add(V3(0, -0.1, 0));
/** b11 pats: Jesus's palm on the near side of its right flank (angle about its axis, 0 = its front) at this height */
const PAT_A = -0.48, PAT_H = 1.17;

// ---------------------------------------------------------------------------------------------------------- timing
function times() {
  const w = (b, word, fb) => wordT(b, word, fb);
  const S = {
    s: T('s04'), end: T('s04.end'),
    b01: T('s04b01'), b02: T('s04b02'), b03: T('s04b03'), b04: T('s04b04'), b05: T('s04b05'), b06e: T('s04b06.end'),
    laughingW: w('s04b05', 'laughing,', 1.02), maniW: w('s04b05', 'maniacally.', 2.24),
    b07: T('s04b07'), coughingW: w('s04b07', 'coughing', 0.86), starsW: w('s04b07', 'stars', 1.32),
    b09: T('s04b09'), galaxiesW: w('s04b09', 'galaxies.', 0.28), b10: T('s04b10'),
    b11: T('s04b11'), b11e: T('s04b11.end'), b12: T('s04b12'), b12e: T('s04b12.end'), b13: T('s04b13'),
  };
  // vocal onsets measured from the vocal envelopes (data/lipsync.json): the HA peaks of the laugh sample sit at
  // +0.17 +0.38 +0.54 +0.71 +0.88 +1.04 +1.58 +1.79; cough peaks +0.04 / +0.38
  S.snort = S.b02 + 0.05;
  S.star1 = S.b02 + 0.1;
  S.gig1 = S.b03 + 0.3; S.gig2 = S.b03 + 0.75;
  S.burst = S.b04;                                                 // the burst lands exactly on the cut
  S.cough1 = T('s04b08') + 0.04; S.cough2 = T('s04b08') + 0.38;
  // the visible coughs (mouth snaps to an 'O', hood dips, eyes pop, a puff of big warm stars flies out at the lens):
  // the two coughs of the s04b08 vocal, one on "COUGHING up stars", and the small first cough of s04b10
  S.coughs = [S.cough1 - 0.02, S.cough2 - 0.02, S.coughingW + 0.02, T('s04b10') + 0.02];
  S.hic1 = S.b10 + 0.04; S.pop = S.b10 + 0.38;                     // the big hiccup: the little galaxy (= edgeprops tPop)
  S.launch = S.b11 + 0.32;                                         // the beach-ball galaxy leaves the mouth
  S.slap1 = S.b05 + 1.04; S.slap2 = S.b05 + 1.58;                  // two slaps land on HA peaks ("laughing," / the next peal)
  S.stamp = S.maniW + 0.02;                                        // the fat-leg stamp lands on "Maniacally"
  S.double = S.b11 + 1.45;                                         // doubles over (the dip between laugh phrases)
  S.cut13 = S.b11 + 1.68;                                          // -> the low shot beside the user (jaw drop, then b13)
  return S;
}

// sanitized Void lip-sync (the s04b10 envelope ends in a NaN in data/lipsync.json)
function voidSpeech(t) {
  const sp = speechAt('VOID', t);
  if (!sp) return null;
  for (const kk of ['open', 'wide', 'round', 'close']) if (!Number.isFinite(sp[kk])) sp[kk] = 0;
  return sp;
}

// the beach-ball galaxy's launch: mouth -> up and out over the user's head (toward camera-left in the OTS) -> curls
// back up to EDGE.GALAXY.from (world) by s04b11.end, where marks.galaxyAt() takes over
function bigGalaxyFlight(t, S, from) {
  if (t < S.launch || t >= S.b11e) return null;
  const u = clamp((t - S.launch) / (S.b11e - S.launch));
  const a = toV(from), b = toV(EDGE.GALAXY.from);
  const c1 = V3(...EDGE.W(-1.45, 2.3, 1.45)), c2 = V3(...EDGE.W(-2.5, 3.7, 3.1));    // over the user's head, then up
  const e = 1 - Math.pow(1 - u, 1.12);                             // a quick launch, then it sails
  const v = 1 - e;
  const p = a.clone().multiplyScalar(v * v * v).addScaledVector(c1, 3 * v * v * e).addScaledVector(c2, 3 * v * e * e).addScaledVector(b, e * e * e);
  return { pos: p, size: lerp(0.34, EDGE.GALAXY.size, smooth(Math.min(1, u * 1.4))), rot: S.launch * 0.15 + 2.6 * (1 - e) + 0.15 * (t - S.launch) };
}

// ---------------------------------------------------------------------------------------------------------- cameras
function cams(S, R) {
  const e = 1e-3;
  // b04-b06: from Jesus's head height (low for the 3 m Void, high enough that the crescent clears the brim and the
  // hood/capelet junction stays tidy), 28 mm, a slow 5 deg orbit
  const low = (yaw, dist = 4.2) => { const y = yaw * Math.PI / 180, L = [0.4, 1.0, -0.82]; return EDGE.at([L[0] + dist * Math.sin(y), 1.78, L[2] + dist * Math.cos(y)], L, 54, { drift: 0.18 }); };
  // b07-b08: close on the Void, but with the whole hood and pink sky round it, so the coughed stars visibly leave the
  // dark hood and sit against the sky (a slow push)
  const mouthCU = EDGE.shot(EDGE.L(R.voidMouth), { dist: 4.7, yaw: -18, pitch: -8, fov: 38, screenY: sy(630), drift: 0.15 });
  const mouthCU2 = EDGE.shot(EDGE.L(R.voidMouth), { dist: 4.35, yaw: -18, pitch: -8, fov: 38, screenY: sy(620), drift: 0.15 });
  const med = R.med;
  // follow-pan down with the little galaxy: aim at its bounce point
  const bp = LITTLE_GALAXY.bounce;
  // the camera holds on the galaxy's arc (mouth -> up and out -> down), then tilts down with its fall so the bounce
  // lands at y ~700 (well above the subtitle band)
  const medDown = EDGE.shot([bp[0] - 0.1, 0.5, bp[2] + 0.1], { dist: 3.6, yaw: -16, pitch: 9, fov: 54, screenY: sy(700), drift: 0.15 });
  const ots = { ...EDGE.cam('OTS'), fov: 54, drift: 0.2 }; ots.look = EDGE.W(0.2, 0.5, -1.33);
  const otsUp = { ...ots, look: EDGE.W(-0.1, 1.15, -1.1) };       // tilts up a little with the galaxy sailing over
  return [
    [S.s, R.heads], [S.b03, R.heads], [S.b04 - e, R.headsIn, 'inOut'],
    [S.b04, low(-19, 4.2)], [S.b07 - e, low(-14, 4.1), 'inOut'],
    [S.b07, mouthCU], [S.b09 - e, mouthCU2, 'linear'],
    [S.b09, med], [S.pop + 0.3, med], [S.pop + 0.75, medDown, 'inOut'], [S.b11 - e, medDown],
    [S.b11, ots], [S.launch + 0.25, ots], [S.launch + 1.0, otsUp, 'inOut'], [S.cut13 - e, otsUp],
    [S.cut13, R.lowA], [S.end, R.lowB, 'inOut'],
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
    // the low shot beside the user looks sunward past the rose-gold crystal tree at the bend: it would stand right
    // behind the sneaker and fill the top-right (eyeline to a tree). Hide it for that shot only.
    const tw = EDGE.TREE_WORLD;
    const hero = (set.props.trees || []).reduce((b, tr) => (!b || Math.hypot(tr.position.x - tw[0], tr.position.z - tw[2]) < Math.hypot(b.position.x - tw[0], b.position.z - tw[2]) ? tr : b), null);
    if (hero && Math.hypot(hero.position.x - tw[0], hero.position.z - tw[2]) < 1.5) hideDuring(hero, 's04b11+1.68', 's04.end');
    const st = { scene: set.scene, set, jesus, vd, user, fx, lg, look: lookFor('s04', set.look) };
    const S = times();
    st.R = {};
    user.update(S.s, { pos: W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.5, hunch: 0.25 } });
    st.R.userShoulderR = user.anchor('shoulderR');
    st.R.toPair = V3(...W(M.V.p)).setY(1.8).sub(st.R.userShoulderR).normalize().toArray();
    // reference anchors at fixed times (pure)
    const at = (tt) => { poseAll(tt, S, st); return { mouth: vd.anchor('mouth'), eyes: vd.anchor('eyes'), jEyes: jesus.anchor('eyes'), uEyes: user.anchor('eyes'), feet: [user.anchor('footL'), user.anchor('footR')] }; };
    // close two-shot of the heads (stacked: the Void's eyes ~y 285 upper right, Jesus's face ~y 535 at the left)
    // (from a little left of front: the Void's face near-frontal, a clean pastel sky behind Jesus's head)
    st.R.heads = EDGE.at([-0.6, 1.75, 4.5], [0.3, 1.43, -0.56], 33, { drift: 0.12 });
    st.R.headsIn = EDGE.at([-0.62, 1.74, 4.1], [0.24, 1.46, -0.56], 33, { drift: 0.12 });
    const a0 = at(S.b07 + 0.5);
    st.R.voidMouth = a0.mouth;
    st.R.popFrom = at(S.pop).mouth;
    const a9 = at(S.b09 + 0.2);
    // b09 medium on both (low, from Jesus's side): Jesus's face ~y 520, the Void's eyes ~y 250
    st.R.med = fitShot([[a9.jEyes, 250, 540], [a9.eyes, 450, 240]], 50, V3(...EDGE.W(-0.6, 1.25, 2.6)), a9.eyes, { posReg: 0.5, yMin: 1.0, yMax: 1.5, drift: 0.15 });
    st.R.launchFrom = at(S.launch).mouth;
    // where each cough's star puff starts (the mouth at that cough, a little out in front of it), and the lens then
    st.R.coughFrom = S.coughs.map((c) => { poseAll(c, S, st); return vd.anchor('mouth').addScaledVector(vd.anchor('mouthDir'), 0.18); });
    lg.from = st.R.popFrom;
    const a1 = at(S.b13 + 0.5);
    st.R.uEyes = a1.uEyes; st.R.feet = a1.feet;
    // b11-end + b13: low beside the user at sneaker height, from their right-front (fitted): the right sneaker + the
    // little galaxy in the lower foreground, the face 3/4 looking up / frame-right (the pair off-frame right)
    const ue = EDGE.L(a1.uEyes), ub = EDGE.M.U.yaw - Math.PI / 2 + 0.55;
    const pos0 = EDGE.W(ue[0] + 2.0 * Math.sin(ub), 0.36, ue[2] + 2.0 * Math.cos(ub));
    const rest = EDGE.W(LITTLE_GALAXY.rest);
    const pts = [[a1.uEyes, 290, 430, 2], [a1.feet[1], 330, 800, 1], [rest, 420, 830, 1]];
    st.R.lowA = fitShot(pts, 44, pos0, a1.uEyes, { posReg: 1.0, yMin: 0.3, yMax: 0.5, drift: 0.12 });
    st.R.lowB = fitShot(pts.map(([w, x, y, wt]) => [w, x - 8, y + 6, wt]), 41, st.R.lowA.pos, a1.uEyes, { posReg: 3, yMin: 0.3, yMax: 0.5, drift: 0.12 });
    console.log('s04 fits', [st.R.med, st.R.lowA, st.R.lowB].map((f) => f.err.toFixed(0) + '@' + EDGE.L(f.pos).map((x) => x.toFixed(2))).join(' '));
    return st;
  },

  async update(t, app, st) {
    const { set, jesus, vd, user, fx, lg } = st;
    st.scene.add(jesus.root, vd.root, user.root);
    jesus.root.visible = vd.root.visible = user.root.visible = true;
    const S = times();
    applyShot(app.camera, shotAt(t, cams(S, st.R)), t, 4);
    poseAll(t, S, st);

    // ---- the little galaxy (shared prop) and the sky galaxy
    const lgs = lg.update(t, { from: st.R.popFrom });
    fx.begin();
    const big = bigGalaxyFlight(t, S, st.R.launchFrom);
    if (big) fx.add(big.pos.toArray(), big.size, 0xd8c0ff, 0.9, big.rot, CELL.galaxy);
    drawSkyGalaxy(fx, t);
    starFx(t, S, st);
    fx.end();

    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t), voidPos: vd.root.position.toArray(), shadowAt: W([0, 0, 0]) });
    const faces = [[vd.anchor('eyes'), 260], [vd.anchor('mouth'), 160], [jesus.anchor('eyes'), 110], [user.anchor('eyes'), 160]];
    fadeSeedsNear(set, app.camera, faces); fadeMotesNear(set, app.camera, faces);
    st.look = lookFor('s04', set.look);
    if (DEBUG) {
      const f = (v) => '[' + EDGE.L(v).map((x) => x.toFixed(2)).join(',') + ']';
      const pxs = (v) => px(app.camera, v).join(',');
      if (DEBUG === 'trees') console.log('DBG trees ' + set.props.trees.map((tr, i) => [i, px(app.camera, tr.position), tr.position.toArray().map((x) => x.toFixed(1))]).filter(([i, p]) => p[0] > -400 && p[0] < 1100).map((x) => JSON.stringify(x)).join(' '));
      console.log(`DBG t=${t.toFixed(2)} V.eyes@${pxs(vd.anchor('eyes'))} V.mouth@${pxs(vd.anchor('mouth'))} J.eyes@${pxs(jesus.anchor('eyes'))} U.eyes@${pxs(user.anchor('eyes'))} V.handR ${f(vd.anchor('handR'))}@${pxs(vd.anchor('handR'))} V.handL@${pxs(vd.anchor('handL'))} J.hip ${f(jesus.anchor('hip'))} LG ${lgs ? f(lgs.pos) + '@' + pxs(lgs.pos) + ' ' + lgs.phase : '-'} big ${big ? pxs(big.pos) : '-'} J.shL@${pxs(jesus.anchor('shoulderL'))}`);
    }
  },
};

// ======================================================================================================== all poses
function poseAll(t, S, st) {
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
  const mo = mouth.clone().addScaledVector(md, 0.15).toArray();
  // b02: ONE star pops out between the fingers, arcs up and twinkles away
  fx.burst({ t, at: S.star1, count: 1, seed: 401, life: 1.7, origin: hand.clone().add(V3(0, 0.06, 0)).addScaledVector(md, 0.1).toArray(),
    vel: [md.x * 0.35, 0.9, md.z * 0.35], spread: [0.02, 0.02, 0.02], gravity: [0, -0.5, 0], drag: 0.5, size: [0.1, 0.1], grow: 0.5,
    color: [0xffffff], fade: [0.03, 0.5], cell: CELL.star, twinkle: true, spin: 1.2 });
  // b03: TWO more squeeze out between the fingers and float up
  for (const [i, at] of [[0, S.gig1], [1, S.gig2]]) {
    fx.burst({ t, at, count: 1, seed: 410 + i, life: 2.0, origin: hand.clone().add(V3(0, 0.04, 0)).addScaledVector(md, 0.12).toArray(),
      vel: [md.x * 0.25 + (i ? 0.12 : -0.12), 0.6, md.z * 0.25], spread: [0.02, 0.02, 0.02], gravity: [0, -0.15, 0], drag: 0.6, size: [0.085, 0.085], grow: 0.5,
      color: [i ? 0xd8f4ff : 0xfff0d8], fade: [0.04, 0.5], cell: CELL.star, twinkle: true, spin: 1 });
  }
  // b04-b06: a few stars escape the laughing crescent on the big "HA"s (sparse, slow)
  const base = { t, life: 2.4, gravity: [0, -0.12, 0], drag: 0.5, size: [0.05, 0.1], grow: 0.6, color: COLS, fade: [0.08, 0.5], twinkle: true, spin: 1.5, wobble: 0.04 };
  fx.stream({ ...base, seed: 420, t0: S.burst, t1: S.b06e, rate: 3.2, origin: mo, vel: [md.x * 0.7, 0.75, md.z * 0.7], spread: [0.35, 0.2, 0.35] });
  // the coughs (b07/b08, "COUGHING up stars", the first b10 cough): a puff of BIG warm gold/white stars (2-3x the laugh
  // sparkles, HDR so they bloom) shot out of the mouth toward the lens and up: they clear the dark hood within ~6
  // frames and sit against the pink sky, each with a soft gold halo (same seed + motion params = same positions)
  const STARC = [new THREE.Color(1.55, 1.36, 0.95), new THREE.Color(1.6, 1.52, 1.3), new THREE.Color(1.5, 1.15, 0.62), new THREE.Color(1.55, 1.42, 1.1)];
  S.coughs.forEach((at, i) => {
    if (t < at || t > at + 2.4 || !st.R.coughFrom) return;
    const from = st.R.coughFrom[i];
    const toCam = V3(...shotAt(at, cams(S, st.R)).pos).sub(from).normalize();         // the lens at the cough (pure)
    const o = { t, at, count: [7, 8, 9, 6][i], seed: 490 + i * 3, jitter: 0.05, life: 1.9, origin: from.toArray(),
      vel: toCam.multiplyScalar(1.4).add(V3(0, 3.7, 0)).toArray(), spread: [1.5, 0.9, 1.5], gravity: [0, -1.2, 0], drag: 1.7, wobble: 0.03 };
    fx.burst({ ...o, size: [0.1, 0.17], grow: 0.7, color: STARC, alpha: 1, fade: [0.05, 0.45], cell: CELL.star, twinkle: true, spin: 2.2 });
    fx.burst({ ...o, size: [0.26, 0.34], grow: 0.7, color: [0xffd890], alpha: 0.13, fade: [0.3, 0.45], cell: CELL.dot });   // halo once clear of the mouth
    // + a small nebula wisp, low and off the eye line
    fx.burst({ t, at, count: 1, seed: 440 + i, life: 1.4, origin: mouth.clone().addScaledVector(md, 0.25).add(V3(0, -0.08, 0)).toArray(), vel: [md.x * 1.0, -0.05, md.z * 1.0],
      spread: [0.03, 0.02, 0.03], drag: 1.4, size: [0.15, 0.15], grow: 0.9, color: [0xb89cff], alpha: 0.16, fade: [0.08, 0.7], cell: CELL.nebula, spin: 0.4 });
  });
  // between the coughs a light sprinkle keeps leaking out with the laugh (small, sparse)
  fx.stream({ ...base, seed: 450, t0: S.cough1 + 0.2, t1: S.b09, rate: 3, origin: mo, vel: [md.x * 1.0, 0.9, md.z * 1.0], spread: [0.4, 0.3, 0.4], size: [0.05, 0.09] });
  fx.burst({ ...base, t, at: S.pop, count: 6, seed: 461, origin: mo, vel: [md.x * 1.4, 0.7, md.z * 1.4], spread: [0.5, 0.35, 0.5] });
  // b11: the peak laugh — the air above them fills with slowly drifting stars (sparse; fading out by the end of s04)
  fx.stream({ ...base, seed: 470, t0: S.b11, t1: S.double + 0.5, rate: 9, life: 3.0, origin: mo,
    vel: [md.x * 0.9, 1.0, md.z * 0.9], spread: [0.6, 0.35, 0.6], gravity: [0, -0.05, 0], cell: (r) => (r() < 0.15 ? CELL.galaxy : CELL.star) });
  fx.burst({ ...base, t, at: S.launch, count: 10, seed: 480, life: 2.6, origin: mouth.clone().addScaledVector(md, 0.2).toArray(), vel: [md.x * 1.3, 1.4, md.z * 1.3], spread: [0.7, 0.5, 0.7] });
}

// ---------------------------------------------------------------------------------------------------------- the Void
function voidPose(t, S, st) {
  const { jesus, vd } = st;
  const P = { pos: W(M.V.p), yaw: EDGE.Y(M.V.yaw), body: {}, head: {}, extra: { stars: 1.6 } };
  const jE = jesus.anchor('eyes');
  // laugh intensity over the scene (0 still, snort/giggle small, the burst, the cough-laugh, the peak, wheezy tail)
  const laugh = k(t, [[S.burst - 0.02, 0], [S.burst + 0.06, 1, 'out'], [S.b06e, 1], [S.b06e + 0.4, 0.55], [S.cough1, 0.25], [S.cough2 + 0.5, 0.35],
    [S.starsW - 0.3, 1, 'inOut'], [S.b09 + 0.2, 0.8], [S.hic1, 0.3], [S.pop + 0.4, 0.3], [S.pop + 0.75, 0.9], [S.b11, 0.9], [S.b11 + 0.15, 1],
    [S.double, 1], [S.double + 0.4, 0.6], [S.b11e, 0.45], [S.b13 + 0.6, 0.2], [S.end, 0.12]]);
  P.extra.laugh = laugh;
  // ---- body
  const hold = 1 - ramp(t, S.snort - 0.02, S.snort + 0.05);
  const snortJolt = pulse(t, S.snort, 0.05, 0.02, 0.3);
  const gig = t > S.b03 && t < S.b03 + 1.3 ? (voidSpeech(t)?.open || 0) : 0;
  const rock = ramp(t, S.b05 - 0.3, S.b05 + 0.3) * (1 - ramp(t, S.b06e, S.b06e + 0.5));
  // each cough jolts the body forward and dips the hood (~7 deg, snappy: 1-2 frames in, ~7 out)
  const coughJ = pulse(t, S.coughs[0] - 0.02, 0.05, 0.03, 0.3) + pulse(t, S.coughs[1] - 0.02, 0.05, 0.03, 0.32) + pulse(t, S.coughs[2] - 0.02, 0.05, 0.03, 0.3)
    + 0.8 * pulse(t, S.coughs[3] - 0.02, 0.05, 0.02, 0.25) + 1.2 * pulse(t, S.pop - 0.04, 0.06, 0.03, 0.35);
  const rear = ramp(t, S.b11 + 0.02, S.b11 + 0.3, 'out') * (1 - ramp(t, S.double - 0.15, S.double + 0.35));
  const dbl = ramp(t, S.double - 0.1, S.double + 0.4, 'inOut') * (1 - 0.35 * ramp(t, S.b13 + 0.3, S.end));
  const launchJ = pulse(t, S.launch - 0.05, 0.05, 0.02, 0.35);
  // the slaps: a jiggle of the round body on each contact
  const slapJ = wobble(t, S.slap1, 4.2, 9) + wobble(t, S.slap2, 4.2, 9);
  P.body = {
    shrug: 0.55 * snortJolt + 0.18 * gig + 0.12 * (1 - hold) * (t < S.burst ? 1 : 0),
    bounce: 0.022 * snortJolt + 0.018 * gig - 0.025 * coughJ + 0.006 * slapJ,
    lean: 0.07 * rock * Math.sin((t - S.b05) * 2 * Math.PI * 0.62) + 0.13 * coughJ - 0.12 * rear + 0.3 * dbl + 0.1 * launchJ,
    stretch: 0.06 * rear,
    breathe: t < S.snort ? 0.15 : 1,
    tilt: 0.04 * rock * Math.sin((t - S.b05) * 2 * Math.PI * 0.31),
    swell: 0.025 * Math.abs(slapJ),
  };
  const sway = laugh * (0.07 * Math.sin((t - S.burst) * 2 * Math.PI * 0.45) + 0.03 * Math.sin((t - S.burst) * 2 * Math.PI * 1.1));
  // the rig throws the head back by ~0.34 * laugh: counter most of it FROM THE FIRST FRAME OF THE BURST (the low camera
  // must see the whole starry crescent under the brim), a little less while it rears up
  const face2cam = 0.27 * laugh * (1 - 0.4 * rear);
  P.head = { pitch: -0.05 * pulse(t, S.burst - 0.02, 0.06, 0.1, 0.4) + face2cam + 0.13 * coughJ - 0.1 * rear + 0.12 * dbl + 0.1 * launchJ, roll: sway, yaw: 0.6 * sway };
  // ---- the fat-leg stamp on "Maniacally" (one step in place: right foot lifts and slams)
  const stampU = clamp((t - (S.stamp - 0.34)) / 0.42);
  if (stampU > 0 && stampU < 1) { P.walk = { amount: Math.sin(Math.PI * stampU), phase: 0.5 * stampU, style: 'stomp' }; P.extra.hem = 0.7 * Math.sin(Math.PI * stampU); }
  P.body.bounce += -0.02 * pulse(t, S.stamp, 0.03, 0, 0.18);
  // ---- arms
  const off = ramp(t, S.burst - 0.02, S.burst + 0.12, 'out');            // hand flies off the mouth
  const press = 0.025 * snortJolt;
  if (off < 1) {
    P.armL = { preset: 'cover_mouth', hand: { curl: 0.18, cup: 0.45, spread: 0.1 + 0.5 * (gig > 0 ? 1 : 0) }, offset: [0, 0, -press] };
    if (off > 0) P.armL = { preset: 'belly', from: 'cover_mouth', mix: off, hand: BELLY };
  } else {
    P.armL = { preset: 'belly', hand: BELLY };
  }
  const ro = RIGHT_OUT();
  P.armR = { preset: 'belly', hand: BELLY, offset: ro.toArray() };
  // the slaps (its LEFT hand, camera side): wind-up 15-18 cm out, a fast snap onto the velvet at the contact, a short
  // rebound; the arm never leaves the 'belly' blend (from/mix), so nothing pops
  const slapArm = (tc) => {                // offset (m) along the belly normal: 0 = on the velvet
    const d = t - tc;
    if (d < -0.3 || d > 0.32) return null;
    let o;
    if (d < -0.07) o = 0.22 * smooth((d + 0.3) / 0.23);                // wind-up (6 frames)
    else if (d < 0) o = 0.22 * (1 - Math.pow((d + 0.07) / 0.07, 2));  // snap in (accelerating)
    else o = 0.04 * Math.sin(Math.PI * Math.min(1, d / 0.14)) * Math.exp(-d * 6) + 0.0;   // contact, tiny rebound, settle
    const mix = d < 0 ? smooth((d + 0.3) / 0.08) : 1 - smooth((d - 0.16) / 0.16);
    return { o, mix };
  };
  const sl = slapArm(S.slap1) || slapArm(S.slap2);
  if (sl && t >= S.burst) {
    const sideP = voidSurface(vd, 0.95, 0.62, 0.01), nrm = voidNormal(vd, 0.95, 0.62);
    const tgt = sideP.addScaledVector(nrm, sl.o).add(V3(0, 0.08 * sl.o / 0.22, 0));
    P.armL = { preset: 'pat', from: 'belly', mix: sl.mix, target: tgt, reach: sl.mix, palm: nrm.clone().negate().toArray(), hand: { curl: 0.12, spread: 0.35, cup: 0.2 } };
  }
  // b09/b10: the hand (LEFT) reaches after the little galaxy as it falls and misses (behind it, too late; kept below
  // the mouth so the face and the arc stay clear)
  const grab = pulse(t, S.pop + 0.3, 0.15, 0.1, 0.3);
  if (grab > 0) {
    const lgs = littleGalaxyAt(t - 0.15, { from: st.R?.popFrom });
    if (lgs) {
      const tg = lgs.pos.clone().add(V3(0, 0.15, 0)).lerp(voidSurface(vd, 1.05, -0.2, 0.25), 0.3);   // trails behind it, on its side
      tg.y = Math.min(tg.y, (st.R?.popFrom?.y ?? 1.9) - 0.75);
      P.armL = { preset: 'reach', from: 'belly', mix: grab, target: tg, reach: grab, hand: { curl: 0.2 + 0.6 * ramp(t, S.pop + 0.46, S.pop + 0.6), spread: 0.4 } };
    }
  }
  // b11: arms flung wide as it rears up; then doubles over — RIGHT hand onto the top of Jesus's (near, left) shoulder,
  // toward the camera side (support), left hand back on the belly
  const wide = rear;
  if (wide > 0) { P.armL = { preset: 'up', from: 'belly', mix: wide }; P.armR = { preset: 'up', from: 'belly', mix: wide }; }
  const lean = ramp(t, S.double + 0.05, S.double + 0.45, 'out') * (1 - ramp(t, S.b13 + 0.25, S.b13 + 0.75));
  if (lean > 0) {
    const sh = jesus.anchor('shoulderL').addScaledVector(V_FWD, 0.03).add(V3(0, 0.02, 0));
    P.armR = { preset: 'pat', from: 'belly', mix: lean, target: sh, reach: lean, palm: [0, -1, 0], fingers: V_FWD.clone().addScaledVector(V_LEFT, -0.3).add(V3(0, -0.6, 0)).normalize().toArray(), hand: { curl: 0.3, spread: 0.2, cup: 0.4 }, handScale: 0.8 };
  }
  // b13 (offscreen): wiping one eye with its LEFT hand, still shaking with leftover giggles; both hands back on the belly
  // by the end (s05 starts with both on the belly, doubled over a little)
  const wipe = ramp(t, S.b13 + 0.25, S.b13 + 0.65) * (1 - ramp(t, S.end - 0.45, S.end - 0.05));
  if (wipe > 0) {
    const e = vd.anchor('eyes').add(V3(0, -0.05, 0)).addScaledVector(vd.anchor('mouthDir'), 0.18);
    P.armL = { preset: 'chin', from: 'belly', mix: wipe, target: e, reach: wipe };
  }
  if (t > S.b13 + 0.5) P.armR.offset = ro.multiplyScalar(1 - ramp(t, S.b13 + 0.5, S.end - 0.1)).toArray();
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
    face = VX('laugh', { tearL: 0.22, tearR: 0.22, wet: 1, mOpen: 0.82, mWide: 1.0 });       // lip-sync of the laugh vocal pumps the mouth wider on each HA
    face.lidU = 0.22 - 0.08 * Math.max(0, Math.sin(t * 2 * Math.PI * 1.6)); face.lidL = 1;
    face.browIn += 0.2 * pulse(t, S.burst, 0.05, 0.25, 0.6); face.browOut += 0.3 * pulse(t, S.burst, 0.05, 0.25, 0.6);
    // b07-b10 coughs: the grin snaps to a round 'O' for ~6 frames and the eyes pop open (the first time they stay
    // open: it looks at its stars; then it laughs harder)
    let oW = 0, popOpen = 0;
    S.coughs.forEach((c, i) => { oW = Math.max(oW, pulse(t, c - 0.03, 0.03, 0.13, 0.09)); popOpen = Math.max(popOpen, pulse(t, c - 0.02, 0.04, i === 0 ? 0.62 : 0.2, 0.22)); });
    face.lidU = lerp(face.lidU, 1.38, popOpen); face.lidL = lerp(face.lidL, 0.05, popOpen);
    face.mRound = lerp(face.mRound, 0.8, popOpen); face.mWide = lerp(face.mWide, 0.1, popOpen);
    face.browIn += 0.35 * popOpen; face.browOut += 0.3 * popOpen;
    face.mOpen = lerp(face.mOpen, 0.9, oW); face.mRound = lerp(face.mRound, 1, oW); face.mWide = lerp(face.mWide, -0.6, oW);
    face.mSmile = lerp(face.mSmile ?? 0, -0.05, oW); face.talk = lerp(face.talk ?? 1, 0.1, oW);
    // b09: the hiccup: eyes go wide and cross for 4 frames as the galaxy shoots out
    const cross = pulse(t, S.pop - 0.01, 0.03, 0.17, 0.12);
    face.lidU = lerp(face.lidU, 1.42, cross); face.lidL = lerp(face.lidL, 0.0, cross); face.mRound = lerp(face.mRound, 0.9, cross);
    // b11: eyes clenched, mouth enormous; then the wheezy squeak
    face.mOpen = lerp(face.mOpen, 1.0, 0.6 * ramp(t, S.b11, S.b11 + 0.2));
    const wheeze = ramp(t, S.double + 0.2, S.double + 0.6);
    face.mOpen = lerp(face.mOpen, 0.45, wheeze); face.mRound = lerp(face.mRound, 0.45, wheeze);
    // b13: leftover giggles
    const tail = ramp(t, S.b13 + 0.1, S.b13 + 0.8);
    const g = VX('giggle', { tearL: 0.25, tearR: 0.25, wet: 1, lidU: 0.3, lidL: 1, mOpen: 0.12 });
    for (const kk in g) if (typeof g[kk] === 'number' && typeof face[kk] === 'number') face[kk] = lerp(face[kk], g[kk], tail);
    face.autoBlink = 0; face.saccade = 0;
  }
  P.face = face;
  // gaze: blank stare at the hold; on Jesus at the snort; up at its stars after the first cough; crossed at the
  // galaxy; else the eyes are closed arcs
  const md = vd.anchor('mouthDir'), mo = vd.anchor('mouth');
  const blank = () => vd.anchor('eyes').addScaledVector(md, 3).addScaledVector(WDIR(-1, 0.2), 0.9).add(V3(0, -0.6, 0));
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
  // the HUG mark (edgeprops JV_HUG: pressed against its right flank, as s03 ends) through b11; during b13 (he is
  // off-frame) he settles back onto JV, where s05 picks him up
  const back = ramp(t, S.b13 + 0.2, S.b13 + 1.1);
  const pos = V3(...W(JV_HUG)).lerp(V3(...W(M.JV.p)), back);
  const P = { pos: pos.toArray(), yaw: EDGE.Y(JYAW), body: {}, head: {}, armR: { preset: 'clasp' } };
  const vEyes = vd ? vd.anchor('eyes') : V3(...EDGE.W(0.62, 2.15, -0.72));
  // ---- arm around (as s03 ends: pressed against its right flank, the arm round its curve and behind it). At the peak
  // (b11) the hand slides out round its flank onto the near side and pats it in rhythm (the scripted "there, there"
  // pats: palm flat, 9 cm lifts at 2.1 Hz, readable in the wide), then goes back round it during b13 (offscreen)
  if (vd) {
    const c0 = aroundContact(vd, jesus);
    const patW = ramp(t, S.b11 + 0.2, S.b11 + 0.55) * (1 - ramp(t, S.b13 + 0.15, S.b13 + 0.6));
    let c = c0, lift = 0;
    if (patW > 0) {
      c = contactAt(vd, lerp(AROUND_H, PAT_H, patW), lerp(c0.a, PAT_A, patW));
      lift = patW * 0.09 * Math.pow(Math.max(0, Math.sin((t - S.b11 - 0.3) * 2 * Math.PI * 2.1)), 2);
    }
    P.armL = aroundArm(c, 1, lift);
    if (patW > 0) {                                  // the patting hand: fingers up and toward its front, elbow down and out
      const fp = c.tb.clone().multiplyScalar(-0.75).add(V3(0, 0.3, 0)).addScaledVector(c.n, -0.1).normalize();
      P.armL.fingers = V3(...P.armL.fingers).lerp(fp, patW).normalize().toArray();
      P.armL.pole = V3(...P.armL.pole).lerp(c.n.clone().multiplyScalar(0.7).add(V3(0, -0.7, 0)), patW).normalize().toArray();
      P.armL.hand = { curl: 0.1, spread: 0.25, cup: 0.2, thumb: 0.45 };
    }
  }
  // pressed against it: leans into it, head tilted toward it (s03's arm-around pose)
  const lean = 1 - ramp(t, S.b13 + 0.2, S.b13 + 1.1);
  P.body.tilt = 0.1 * lean;
  // ---- body
  const giggle = k(t, [[S.b03 + 0.1, 0], [S.b03 + 0.3, 0.8], [S.burst, 0.8], [S.burst + 0.1, 1], [S.b07, 0.9], [S.pop, 0.4], [S.pop + 0.5, 0.2], [S.pop + 0.7, 0.9], [S.b11e, 0.9], [S.b13 + 0.4, 0.6]]);
  P.body.giggle = giggle;
  const dodge = pulse(t, S.pop + 0.02, 0.12, 0.25, 0.4);
  P.body.recoil = 0.28 * dodge + 0.06 * ramp(t, S.burst, S.burst + 0.3);
  P.body.breathe = t < S.snort ? 0.2 : 1;
  // b04-b06: his laugh is cheated toward the lens (chest turns to camera: the crinkled eyes + the knuckle wipe read)
  const cheat = ramp(t, S.burst - 0.2, S.burst + 0.25) * (1 - ramp(t, S.b07, S.b07 + 0.3));
  P.body.twist = -0.22 * cheat;
  // ---- head / gaze: eyes on the Void's eyes (cheated 18 cm low so the irises sit in the eye), the head follows well
  const lgs = littleGalaxyAt(t, { from: st.R?.popFrom });
  const vLook = () => vEyes.clone().add(V3(0, -0.18, 0));
  P.gaze = gazeSched(t, [
    [S.s, vLook],
    [S.pop + 0.05, () => (lgs ? lgs.pos : vLook()), 0.06],
    [S.pop + 0.95, vLook, 0.15],
    [S.launch + 0.35, () => (bigGalaxyFlight(t, S, st.R?.launchFrom || vEyes)?.pos || toV(EDGE.GALAXY.from)), 0.12],
    [S.launch + 1.05, vLook, 0.15],
  ]);
  const nod = 0.12 * pulse(t, S.snort + 0.25, 0.12, 0.05, 0.2) + 0.1 * pulse(t, S.snort + 0.55, 0.1, 0.05, 0.2);
  const tossBack = -0.1 * ramp(t, S.b13 + 0.2, S.end - 0.1);       // (offscreen) chin settles down as s05 has it
  const follow = 0.7 - 0.1 * dodge - 0.32 * cheat;
  P.head = { look: P.gaze, follow, pitch: nod - tossBack, yaw: -0.15 * cheat, roll: 0.1 * lean * (1 - cheat) };
  // ---- arms (right): belt -> hand on chest for the giggle -> knuckle wipes an eye -> belt
  const heart = ramp(t, S.b03 + 0.15, S.b03 + 0.5) * (1 - ramp(t, S.burst + 0.6, S.burst + 1.0));
  const wipe = ramp(t, S.laughingW - 0.3, S.laughingW + 0.15) * (1 - ramp(t, S.maniW + 0.1, S.maniW + 0.5));
  if (heart > 0) P.armR = { preset: [['clasp', 1 - heart], ['heart', heart]] };
  if (wipe > 0) {
    const rub = 0.008 * Math.sin((t - S.laughingW) * 2 * Math.PI * 2.4) * ramp(t, S.laughingW, S.laughingW + 0.15);
    P.armR = { preset: [['clasp', 1 - wipe], ['wipe_eye', wipe]], offset: [0, rub * wipe, 0] };
  }
  // ---- face (segments cross-fade; the burst is a cut)
  const fHold = () => JX('pressed', { browIn: 0.65, browOut: 0.6, lidU: 1.05, mPress: 0.95, mSmile: 0.25 });
  const fRight = () => JX('beam', { mOpen: 0.06, browIn: 0.7, browOut: 0.75 });          // "right?"
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
  P.face = faceSeq(t, [[S.s, fHold], [S.snort + 0.12, fRight, 0.25], [S.b03 + 0.05, fGiggle, 0.25], [S.burst - 0.06, fLaugh, 0.12]]);
  P.blinkAt = [S.b01 + 0.6];
  if (!(t >= S.b12 && t <= S.b12e)) P.speech = false;     // only his soft laugh vocal drives his mouth
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
  // phone still up as a shield (s03 end) -> drops to prop on the ground behind them as they flatten back at the peak
  const shield = 1 - ramp(t, S.launch, S.launch + 0.5);
  P.armL = shield > 0 ? { preset: [['prop', 1 - shield], ['shield', shield]] } : { preset: 'prop' };
  const flat = ramp(t, S.launch + 0.1, S.launch + 0.6, 'out');
  const sitUp = ramp(t, S.b13 + 0.15, S.b13 + 0.7);                // leans in to look at the thing by the sneaker
  P.body.recoil = 0.1 * ramp(t, S.burst, S.burst + 0.3) + 0.4 * flat * (1 - 0.55 * sitUp);
  P.body.lean = -0.1 * flat * (1 - sitUp) + 0.12 * sitUp * (1 - 0.6 * ramp(t, S.b13 + 1.0, S.end));
  // gaze: the pair -> the big galaxy (tracks it up and over) -> the little galaxy at the sneaker -> slowly back up at
  // the pair (frame-right and up, well off the lens), held
  const lgs = littleGalaxyAt(t, {});
  const big = () => bigGalaxyFlight(t, S, st.R?.launchFrom || vd.anchor('mouth'))?.pos || toV(EDGE.GALAXY.from);
  const pair = () => jesus.anchor('eyes').lerp(vd.anchor('eyes'), 0.5);
  P.gaze = gazeSched(t, [
    [S.s, () => vd.anchor('eyes')],
    [S.launch + 0.15, big, 0.1],
    [S.b13 + 0.22, () => (lgs ? lgs.pos : vd.anchor('eyes')), 0.12],
    [S.b13 + 0.95, pair, 0.6],
  ]);
  const upTrack = ramp(t, S.launch + 0.1, S.b11e) * (1 - ramp(t, S.b13 + 0.05, S.b13 + 0.3));
  const down = ramp(t, S.b13 + 0.2, S.b13 + 0.5) * (1 - ramp(t, S.b13 + 0.95, S.b13 + 1.55));
  P.head = { follow: 0.25 + 0.45 * upTrack + 0.35 * down + 0.3 * ramp(t, S.b13 + 0.95, S.b13 + 1.55), pitch: 0 };
  // face: terror -> jaw drops as the galaxy passes -> b13 the brows can't decide (left up, right down), jaw hanging
  const drop = ramp(t, S.launch + 0.3, S.launch + 0.9);
  const face = UX([['terror', 1 - 0.5 * drop], ['disbelief', 0.5 * drop]], { pupil: 0.55 });
  face.mOpen = lerp(face.mOpen, 0.62, drop);
  face.lidU = Math.max(face.lidU, lerp(face.lidU, 1.25, drop * (1 - ramp(t, S.b13, S.b13 + 0.4))));
  const undecided = ramp(t, S.b13 + 0.8, S.b13 + 1.3);
  face.browInL = face.browIn + 0.38 * undecided; face.browOutL = face.browOut + 0.5 * undecided;
  face.browInR = face.browIn - 0.45 * undecided; face.browOutR = face.browOut - 0.4 * undecided;
  face.autoBlink = 0;
  P.face = face;
  P.blinkAt = [S.b13 + 1.25];
  P.speech = false;
  return P;
}
