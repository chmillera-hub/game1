// s02 and_jesus_appears — an empty bend in the path waits (the joke), Jesus is simply there on "Now.", strolls; the
// screaming user skids onto their backside at his feet; the Void arrives and gives them room; Jesus takes it all in
// and has an idea; he strolls past the user toward the Void ("one sec"); the Void can't believe it's for it.
// Shots: BEND (locked reverse toward the sun) · SCREAM (tracking close-up on the user) · ARRIVE (low side two-shot for
// the burst-in, pushes/arcs in to a medium two-shot through the fall) · REV (low angle from behind the user's raised
// hand up to the Void) · JCU (close on Jesus, slow push) · W7A (reverse from the Void's side: Jesus passes the user,
// palm-down "one sec") · W7B (Void single: the glance behind it, round eyes, hands knot).
// MIRRORED vs the script per docs/STAGING.md: the user comes from frame RIGHT, Jesus is frame LEFT in ARRIVE; the
// phone is in the user's LEFT hand, the RIGHT hand is the raised "defend" hand.
import * as THREE from 'three';
import { T, k } from '../core/timeline.js';
import { applyShot } from '../core/camera.js';
import { clamp, lerp, smooth, noise1, fbm1 } from '../core/util.js';
import { Particles, CELL } from '../core/particles.js';
import { glowSprite } from '../core/materials.js';
import { EDGE, todAt, voidSkyAt, lookFor, sy } from './marks.js';
import { VX } from '../chars/void.js';
import { UX } from '../chars/user.js';
import { JX } from '../chars/jesus.js';
import { ownedGroup, cast, G, bump, jiggle, V3, WD, fitCam } from './kit_s0102.js';
import { hideDuring } from './edgeprops.js';

const M = EDGE.M;
const TAU = Math.PI * 2;
const L2 = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u)];
const P2 = (m) => [m.p[0], m.p[2]];
const fwdL = (y) => [Math.sin(y), Math.cos(y)];
/** root-local offset (x = the character's left, z = forward) -> stage-local offset for a character at local yaw y */
const rotL = (o, y) => [o[0] * Math.cos(y) + o[1] * Math.sin(y), -o[0] * Math.sin(y) + o[1] * Math.cos(y)];

// ------------------------------------------------------------------------------------------------ JESUS paths
// (1) the stroll J0 -> J1 from "Now." (stroll, hands behind), decelerating to a stop as the user arrives;
// (2) the walk J1 -> past the user (camera side) -> JV from s02b07 (continues into s03b01: import jesusWalkS02).
const STROLL = 0.9, WALK = 1.05;
function travel(t, tA, t1, t2, dist) {          // distance along a path: constant speed, linear decel to 0 at t2
  const v0 = dist / ((t1 - tA) + (t2 - t1) / 2);
  if (t <= tA) return { s: 0, v0, amt: 0 };
  if (t <= t1) return { s: v0 * (t - tA), v0, amt: 1 };
  const d = Math.min(t, t2) - t1, L = t2 - t1;
  return { s: v0 * (t1 - tA) + v0 * (d - d * d / (2 * L)), v0, amt: t >= t2 ? 0 : 1 - d / L };
}
function strollAt(t) {
  const J0 = P2(M.J0), J1 = P2(M.J1);
  const dist = Math.hypot(J1[0] - J0[0], J1[1] - J0[1]);
  const tA = T('s02b02'), t2 = T('s02b03+0.14'), t1 = t2 - 0.55;
  const r = travel(t, tA, t1, t2, dist);
  const p = L2(J0, J1, r.s / dist);
  return { p, yaw: M.J0.yaw, phase: 0.32 + r.s / STROLL, amt: t < tA ? 0 : Math.max(r.amt, 0), moving: r.amt };
}
// the s02b07 walk: quadratic bezier J1 -> (passes (-0.6, 1.4) on the camera side of the user) -> JV
const WALKPATH = (() => {
  const P0 = P2(M.J1), W1 = [-0.6, 1.4], P2_ = P2(M.JV);
  const C = [2 * W1[0] - 0.5 * (P0[0] + P2_[0]), 2 * W1[1] - 0.5 * (P0[1] + P2_[1])];
  const pts = [], cum = [0];
  for (let i = 0; i <= 64; i++) {
    const u = i / 64, a = (1 - u) * (1 - u), b = 2 * u * (1 - u), c = u * u;
    pts.push([a * P0[0] + b * C[0] + c * P2_[0], a * P0[1] + b * C[1] + c * P2_[1]]);
    if (i) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  }
  return { pts, cum, len: cum[64] };
})();
function pathPoint(s) {
  const { pts, cum, len } = WALKPATH;
  s = clamp(s, 0, len);
  let i = 1; while (i < 64 && cum[i] < s) i++;
  const u = (s - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]);
  const p = L2(pts[i - 1], pts[i], u);
  const d = [pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]];
  return { p, yaw: Math.atan2(d[0], d[1]) };
}
/** Jesus's walk from J1 to JV, starting at s02b07 (0.35 s ease-in, ~1.05 m/s, eases into JV). Stage-local. */
export function jesusWalkS02(t) {
  const tW = T('s02b07'), v = WALK * 1.0, acc = 0.35;
  const len = WALKPATH.len;
  let s = t <= tW ? 0 : t < tW + acc ? v * (t - tW) ** 2 / (2 * acc) : v * (t - tW - acc / 2);
  const tEnd = tW + acc / 2 + len / v;                 // reach JV (with a soft stop over the last 0.4 s)
  let amt = t <= tW ? 0 : t < tW + acc ? (t - tW) / acc : 1;
  if (t > tEnd - 0.4) { const d = Math.min(t, tEnd + 0.4) - (tEnd - 0.4); s = Math.min(len, v * (tEnd - 0.4 - tW - acc / 2) + v * (d - d * d / 1.6)); amt = Math.max(0, 1 - d / 0.8); }
  const q = pathPoint(s);
  const yaw0 = M.J1.yaw - 0.72;
  const turn = smooth(clamp((t - tW) / 0.45));
  return { pos: q.p, yaw: lerp(yaw0, q.yaw, turn), phase: s / WALK + 0.1, amt, s };
}
/** times of Jesus's footfalls (for the cue file): stroll (s02b02..) and walk (s02b07..) */
export function jesusFootfalls() {
  const out = [];
  for (let f = Math.round(T('s02b02') * 240); f < Math.round(T('s02b03+0.2') * 240); f++) {
    const t0 = f / 240, t1 = (f + 1) / 240, a = strollAt(t0).phase * 2, b = strollAt(t1).phase * 2;
    if (Math.floor(b) > Math.floor(a) && strollAt(t1).amt > 0.05) out.push(+t1.toFixed(3));
  }
  for (let f = Math.round(T('s02b07') * 240); f < Math.round(T('s02.end') * 240); f++) {
    const t0 = f / 240, t1 = (f + 1) / 240, a = jesusWalkS02(t0).phase * 2, b = jesusWalkS02(t1).phase * 2;
    if (Math.floor(b) > Math.floor(a) && jesusWalkS02(t1).amt > 0.05) out.push(+t1.toFixed(3));
  }
  return out;
}

// ------------------------------------------------------------------------------------------------ VOID path
const V_STRIDE = 0.38, V_CPS = 1.05;
function voidAt(t) {
  const Vp = P2(M.V), U = P2(M.U);
  const toU = [U[0] - Vp[0], U[1] - Vp[1]], n = Math.hypot(...toU);
  const Vstop = [Vp[0] + toU[0] / n * 0.15, Vp[1] + toU[1] / n * 0.15];
  const Vstart = [1.35, -3.4];
  const dist = Math.hypot(Vstop[0] - Vstart[0], Vstop[1] - Vstart[1]);
  const tS = T('s02b05+0.32');                           // stops on one foot
  const v = 2 * V_STRIDE * V_CPS, tA = tS - dist / v;
  const s = clamp((t - tA) * v, 0, dist);
  let p = L2(Vstart, Vstop, s / dist);
  // phase: chosen so that at tS the LEFT foot is mid-swing (u = 0.74)
  const phAtStop = dist / (2 * V_STRIDE);
  const ph0 = 0.74 - (phAtStop - Math.floor(phAtStop));
  let phase = s / (2 * V_STRIDE) + ph0, amt = t < tA ? 0 : 1;
  const tPlant = tS + 0.42;                             // wobble on one foot, then set it down
  if (t > tS) phase += 0.26 * smooth(clamp((t - tS - 0.22) / 0.2));
  if (t > tPlant) amt = 1 - smooth(clamp((t - tPlant) / 0.3));
  // one tiny half-step back to V near the end of b05
  const tB = T('s02b05.end-0.62'), tB1 = tB + 0.5;
  const ub = smooth(clamp((t - tB) / (tB1 - tB)));
  if (t > tB) { p = L2(Vstop, Vp, ub); phase -= 0.5 * ub; amt = Math.max(amt, Math.sin(Math.PI * ub) * 0.9); }
  return { pos: p, yaw: M.V.yaw, phase, amt, tS, tPlant, tB, tA, ph0, moving: t < tS };
}

// ------------------------------------------------------------------------------------------------ USER blocking
// Runs in from upstage-right (frame right in ARRIVE) straight at Jesus -> trips at USKID: the skid spins them, the legs
// shoot out PAST his downstage (camera) side and the backside lands well short of him -> the twist continues the same
// rotation (yaw increasing: the face passes the lens) pivoting on the backside -> scoot, scoot until the back meets his
// shins at U. Only the back ever reaches Jesus: the feet/knees keep >= 0.35 m from J1 (checked by probe, see report).
const RUN_YAW = -0.72;        // local heading of the run-in
const SPIN_YAW = 0.15;        // heading of the legs when the slide stops (past Jesus's downstage side)
const TRIP = [-0.55, 0.6];    // = USKID: the trip point (root)
const D_LAND = 0.5, D_TWIST = 0.24;   // hip distance from its final spot (toward the Void) on landing / after the twist
function userTimes() {
  const tF = T('s02b04');
  return { tR: T('s02b03'), tF, tImpact: tF + 0.62, tTw0: tF + 0.76, tTw1: tF + 1.22, tSc0: tF + 1.26, tSc1: tF + 1.9 };
}
function userBlock(t, hipL) {
  const UT = userTimes();
  const U = P2(M.U), Uy = M.U.yaw, fU = fwdL(Uy);
  const hu = rotL(hipL, Uy), hipFin = [U[0] + hu[0], U[1] + hu[1]];
  const hipAt = (D) => [hipFin[0] + fU[0] * D, hipFin[1] + fU[1] * D];
  const rootFromHip = (h, y) => { const o = rotL(hipL, y); return [h[0] - o[0], h[1] - o[1]]; };
  const Hs = hipAt(D_LAND), Rs = rootFromHip(Hs, SPIN_YAW);
  const o = { p: null, yaw: 0, sit: 0, run: 0, phase: 0, scoot: 0, scootPh: 0 };
  if (t < UT.tF) {                                   // the run in, braking a little (3.1 -> 2.2 m/s)
    const dt = UT.tF - t, dist = 2.2 * dt + 0.6 * dt * dt, f = fwdL(RUN_YAW);
    o.p = [TRIP[0] - f[0] * dist, TRIP[1] - f[1] * dist]; o.yaw = RUN_YAW; o.run = 1; o.phase = 0.15 - dist / 1.9;
  } else if (t < UT.tTw0) {                          // trip: skid + spin + fall onto the backside, slide to a stop
    const u = clamp((t - UT.tF) / (UT.tTw0 - UT.tF)), e = 1 - (1 - u) * (1 - u);
    o.p = L2(TRIP, Rs, e);
    o.yaw = lerp(RUN_YAW, SPIN_YAW, smooth(clamp((u - 0.08) / 0.8)));
    o.run = 1 - smooth(clamp((t - UT.tF) / 0.22)); o.phase = 0.15 + (t - UT.tF) * 1.2;
    o.sit = clamp((t - UT.tF) / 0.75);
  } else if (t < UT.tSc0) {                          // twist round on the backside (yaw increasing), a push back
    const u = smooth(clamp((t - UT.tTw0) / (UT.tTw1 - UT.tTw0)));
    o.yaw = lerp(SPIN_YAW, Uy, u);
    o.p = rootFromHip(L2(Hs, hipAt(D_TWIST), u), o.yaw); o.sit = 1;
  } else {                                           // scoot, scoot, bump
    const u = clamp((t - UT.tSc0) / (UT.tSc1 - UT.tSc0));
    o.scootPh = 2 * u; o.scoot = t < UT.tSc1 + 0.1 ? 1 : 1 - smooth((t - UT.tSc1 - 0.1) / 0.2);
    o.yaw = Uy; o.p = rootFromHip(hipAt(D_TWIST * (1 - u)), Uy); o.sit = 1;
  }
  return o;
}

// ------------------------------------------------------------------------------------------------ shots / timing
const T7B = () => T('s02b07+0.72');                 // W7A -> W7B (Void single)
function shotOf(t) {
  return t < T('s02b03') ? 'BEND' : t < T('s02b03+0.42') ? 'SCREAM' : t < T('s02b05') ? 'ARRIVE' : t < T('s02b06') ? 'REV'
    : t < T('s02b07') ? 'JCU' : t < T7B() ? 'W7A' : 'W7B';
}

export default {
  id: 's02',
  async setup(app) {
    const set = await app.set('EDGE');
    const user = await app.char('USER'), vd = await app.char('VOID'), jesus = await app.char('JESUS');
    const st = { set, scene: set.scene, user, vd, jesus, look: {} };
    st.own = ownedGroup(st, 's02.own'); st.scene.add(st.own);
    st.fx = new Particles({ max: 60, intensity: 1.6 }); st.own.add(st.fx.mesh);
    st.fx2 = new Particles({ max: 40, blending: 'normal', intensity: 1.15, renderOrder: 6 }); st.own.add(st.fx2.mesh);   // gold sparkles that read on the pale sky
    // Jesus's arrival shimmer (3 frames) — a soft golden column, no disc
    st.shim = glowSprite(0xffe2a0, 1.0, 0.0); st.shim.scale.set(1.3, 2.3, 1); st.own.add(st.shim);
    // the hero thought-seed that floats down into the empty bend (the set's own seed sprite)
    const smap = set.props.seeds && set.props.seeds.mat ? set.props.seeds.mat.uniforms.uMap.value : null;
    st.seed = new THREE.Sprite(new THREE.SpriteMaterial({ map: smap, color: 0xfff1d6, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    st.seed.scale.set(0.42, 0.42, 1); st.own.add(st.seed);
    // seated hip offset (root-local) so the twist / scoot pivot on the backside, not on the feet
    user.update(0, { pos: [0, 0, 0], yaw: 0, body: { sit: 1 } });
    const h = user.anchor('hip'); st.hipL = [h.x, h.z];
    // the raised "defend" hand target, same as s03's defendTargetStd (continuity across the cut): out at the right-front
    // of the shoulder, a little above it, so the face reads past it and it reads beside the head from behind
    user.update(0, { pos: EDGE.W(M.U.p), yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.55, hunch: 0.25 } });
    { const sh = user.anchor('shoulderR'), a = EDGE.Y(M.U.yaw) - 0.95; st.defendStd = sh.clone().add(V3(Math.sin(a) * 0.3, 0.2, Math.cos(a) * 0.3)); }
    // the rose-gold crystal tree (the hero tree at the bend) would stand right behind Jesus's head as the ARRIVE camera
    // arcs round: it is off to the side in this angle, so drop it for the shot (s04 does the same for its low angle)
    const tw = EDGE.TREE_WORLD, hero = (set.props.trees || []).find((tr) => Math.hypot(tr.position.x - tw[0], tr.position.z - tw[2]) < 1.5);
    if (hero) { hideDuring(hero, 's02b03+0.42', 's02b05'); hideDuring(hero, 's02b07', 's02.end'); }
    fitShots(st);
    return st;
  },

  async update(t, app, st) {
    st.__t = t;
    const { set, user, vd, jesus } = st;
    const cam = app.camera;
    const shot = shotOf(t);
    const jesusIn = t >= T('s02b02');
    const names = { BEND: jesusIn ? ['JESUS'] : [], SCREAM: ['USER'], ARRIVE: ['JESUS', 'USER'], REV: ['USER', 'VOID'], JCU: ['JESUS', 'USER'], W7A: ['JESUS', 'USER'], W7B: ['VOID'] }[shot];
    cast(app, st.scene, names);
    const UT = userTimes();

    // ============================================================================ positions (no rig updates yet)
    // --- Jesus
    let J;
    if (t < T('s02b07')) {
      const s = strollAt(t);
      J = { pos: s.p, yaw: s.yaw, phase: s.phase, amt: s.amt, style: 'stroll' };
    } else {
      const w = jesusWalkS02(t);
      J = { pos: w.pos, yaw: w.yaw, phase: w.phase, amt: w.amt, style: 'walk' };
    }
    // cheat his facing toward the side camera once he has stopped (ARRIVE .. JCU)
    if (t >= T('s02b03') && t < T('s02b07')) J.yaw -= 0.72;
    const JW = G(set, J.pos[0], J.pos[1]);
    // --- Void
    const VV = voidAt(t);
    const VW = G(set, VV.pos[0], VV.pos[1]);
    // --- User
    const B = userBlock(t, st.hipL);
    const uPos = EDGE.W(B.p[0], 0, B.p[1]);

    // ============================================================================ camera (before rig updates)
    let shotDef = null;
    if (shot === 'BEND') shotDef = { ...EDGE.cam('BEND'), drift: 0.15 };
    else if (shot === 'ARRIVE') shotDef = arriveShot(t, st);
    else if (shot === 'REV') {
      // low angle from just behind the user's raised right hand up to the Void (fitted), a very slow push
      const c = st.camREV, push = 0.16 * smooth((t - T('s02b05')) / 1.7);
      const dir = V3(...c.look).sub(V3(...c.pos)).normalize();
      shotDef = { pos: V3(...c.pos).addScaledVector(dir, push).toArray(), look: c.look, fov: c.fov, drift: 0.2 };
    } else if (shot === 'W7A') shotDef = w7aShot(t, st);
    else if (shot === 'W7B') shotDef = w7bShot(t, st);
    if (shotDef) applyShot(cam, shotDef, t);
    const DB = (typeof window !== 'undefined' && window.DBG_S02) || null;   // camera exploration hook (probe only)
    if (DB && DB.cam && DB.cam[shot]) applyShot(cam, DB.cam[shot](t, st), t);

    // ============================================================================ USER (provisional: anchors)
    let ue0 = null;
    if (t >= T('s02b03')) {
      user.update(t, { pos: uPos, yaw: EDGE.Y(B.yaw), walk: { amount: B.run, style: 'run', phase: B.phase }, body: { sit: B.sit, sitPath: 'fall', scoot: B.scoot, scootPhase: B.scootPh }, armL: t >= T('s02b05') ? { preset: 'clutch' } : undefined, armR: t >= T('s02b05') ? { preset: 'defend', target: st.defendStd.toArray() } : undefined });
      ue0 = user.anchor('eyes');
    }
    if (shot === 'SCREAM') {
      // tracking close-up, a little off the run axis toward camera-right: the tall O and both wide eyes
      const ry = EDGE.Y(RUN_YAW), fwd = V3(Math.sin(ry), 0, Math.cos(ry)), side = V3(Math.cos(ry), 0, -Math.sin(ry));
      const cp = ue0.clone().addScaledVector(fwd, 1.42).addScaledVector(side, 0.55).add(V3(0, -0.06, 0));
      applyShot(cam, frame(ue0.toArray(), cp, 33, 0.37), t);
    }
    // Jesus provisional (position/walk only) -> anchors for gazes and the close-up camera
    const jPre = { pos: JW, yaw: EDGE.Y(J.yaw), walk: { amount: J.amt, style: J.style, phase: J.phase } };
    if (jesusIn) jesus.update(t, jPre);
    // ============================================================================ VOID (pose; updated even when off-cast for anchors)
    const vEyesGuess = V3(VW[0], VW[1] + 2.16, VW[2]);
    vd.update(t, voidPose(t, st, VV, VW, ue0 || vEyesGuess));
    const vEyes = vd.anchor('eyes');

    // ============================================================================ JESUS
    const jPose = jesusPose(t, st, J, JW, ue0, vEyes);
    if (jesusIn) {
      if (shot === 'JCU') {
        const eyes = jesus.anchor('eyes');
        const u = smooth(clamp((t - T('s02b06')) / (T('s02b07') - T('s02b06'))));
        applyShot(cam, EDGE.shot(EDGE.L(eyes), { dist: lerp(1.6, 1.3, u), yaw: 110, pitch: 1, fov: 33, screenY: sy(415), drift: 0.15 }), t);
      }
      jesus.update(t, jPose.full(jesus));
    }
    const jHead = jesusIn ? jesus.anchor('eyes') : null;

    // ============================================================================ USER (final)
    if (t >= T('s02b03')) user.update(t, userPose(t, st, UT, B, uPos, jHead, vEyes, jesus));

    // ============================================================================ FX: shimmer, sparkles, seed
    const tA = T('s02b02');
    // in front of him (toward the lens) so his body does not hide the shimmer and sparkles
    const jc = V3(JW[0], JW[1] + 0.95, JW[2]).add(cam.position.clone().sub(V3(JW[0], JW[1] + 0.95, JW[2])).setY(0).normalize().multiplyScalar(0.42));
    const sh = bump(t, tA - 0.001, tA + 0.13, 0.01);
    st.shim.visible = sh > 0.001 && shot === 'BEND';
    st.shim.position.copy(jc); st.shim.material.opacity = 0.55 * sh;
    st.fx.begin(); st.fx2.begin();
    if (shot === 'BEND' && t >= tA) {
      // a small puff of warm sparkles (no flash, no halo): gold stars drift out and up from his middle, twinkle out
      st.fx2.burst({ t, seed: 21, at: tA, count: 16, jitter: 0.06, life: 1.3, origin: [jc.x, jc.y + 0.1, jc.z],
        vel: [0, 0.45, 0], spread: [1.25, 0.9, 0.6], drag: 2.4, gravity: [0, -0.05, 0], size: [0.06, 0.11],
        color: [0xffb938, 0xffcf5c, 0xffe08a], alpha: 0.95, fade: [0.06, 0.5], cell: CELL.star, twinkle: true, spin: 1.0 });
    }
    if (shot === 'ARRIVE') {
      // a puff of pale path dust where the backside lands and where the heels plough
      const hp = EDGE.W(...((() => { const h = rotL(st.hipL, M.U.yaw); const U = P2(M.U), fU = fwdL(M.U.yaw); return [U[0] + h[0] + fU[0] * D_LAND, 0.05, U[1] + h[1] + fU[1] * D_LAND]; })()));
      st.fx.burst({ t, seed: 33, at: UT.tImpact - 0.02, count: 7, jitter: 0.04, life: 1.1, origin: hp, vel: [0, 0.25, 0], spread: [0.7, 0.18, 0.7],
        drag: 2.6, gravity: [0, -0.04, 0], size: [0.12, 0.22], grow: 1.2, color: [0xf6e6d2, 0xeedcc6], alpha: 0.45, fade: [0.05, 0.6], cell: CELL.puff, blending: 'normal' });
    }
    st.fx.end(); st.fx2.end();
    // the hero seed: floats down into the empty bend, bobs once, drifts off right (b01 + pause)
    {
      const s0 = T('s02b01-0.2'), s1 = T('s02b02-0.1');
      const u = clamp((t - s0) / (s1 - s0));
      st.seed.visible = shot === 'BEND' && u > 0 && u < 1;
      if (st.seed.visible) {
        const J0w = EDGE.W(M.J0.p), right = WD(0.55, 0.83).normalize();   // screen-right in BEND ~ local (+x,+z)
        const down = k(t, [[s0, 2.45], [T('s02b01+1.2'), 1.42, 'out'], [T('s02b01+1.55'), 1.36, 'inOut'], [T('s02b01+1.95'), 1.48, 'inOut'], [s1, 1.9, 'in']]);
        const side = k(t, [[s0, -0.35], [T('s02b01+1.6'), -0.05], [s1, 1.6, 'in']]);
        st.seed.position.set(J0w[0] + right.x * side, down, J0w[2] + right.z * side);
        st.seed.material.opacity = smooth(u / 0.1) * smooth((1 - u) / 0.12) * 0.9;
        st.seed.material.rotation = 0.25 * Math.sin(t * 1.3);
      }
    }

    // ============================================================================ set + look
    const shadowAt = shot === 'BEND' ? EDGE.W(-2.0, 0, 2.2) : EDGE.W(-0.6, 0, 0.6);
    const clear = [[...[EDGE.W(M.U.p)].map((w) => [w[0], w[2], 0.9])[0]], [...[EDGE.W(-0.9, 0, 1.0)].map((w) => [w[0], w[2], 0.8])[0]]];
    set.update(t, { tod: todAt(t), voidSky: voidSkyAt(t) * (shot === 'BEND' ? 0.0 : 1), voidPos: VW, voidRadius: 28,
      // BEND looks into the sun: swing the key round toward the sun's azimuth so his shadow falls toward the lens
      sunShift: shot === 'BEND' ? -0.09 : 0, keyYaw: shot === 'BEND' ? -0.12 : undefined, fillMul: shot === 'BEND' ? 1.15 : undefined,
      sunGlow: shot === 'BEND' ? 0.75 : shot === 'JCU' ? 0.7 : 1, shadowAt, clear, seeds: shot === 'BEND' ? 0.6 : shot === 'ARRIVE' || shot === 'JCU' ? 0.45 : 1, ...((DB && DB.opts) || {}) });
    st.look = lookFor('s02', set.look);
  },
};

// ------------------------------------------------------------------------------------------------ cameras
/** a shot from camera position cp looking so that `look` (world) lands at screen height syF (0..1) */
function frame(look, cp, fov, syF) {
  const L = V3(...look), d = L.clone().sub(cp), dist = d.length();
  const off = (syF - 0.5) * 2 * dist * Math.tan(fov * Math.PI / 360);
  return { pos: cp.toArray(), look: [L.x, L.y + off, L.z], fov, drift: 0.2 };
}
const lerpA = (a, b, u) => a.map((v, i) => lerp(v, b[i], u));
/** ARRIVE: side two-shot for the burst-in, dips with the fall, then pushes/arcs in to a medium two-shot */
function arriveShot(t, st) {
  const A = st.camARR_A, Bc = st.camARR_B;
  const dn = smooth(clamp((t - T('s02b04+0.1')) / 0.7));            // tilt down with the fall
  const w = smooth(clamp((t - T('s02b04+0.62')) / 1.22));           // push in from the THUD to the hand going up
  const lookA = [A.look[0], A.look[1] - 0.2 * dn, A.look[2]];
  return { pos: lerpA(A.pos, Bc.pos, w), look: lerpA(lookA, Bc.look, w), fov: lerp(A.fov, Bc.fov, w), drift: 0.2 };
}
/** W7A: reverse from the Void's side, low: the user's 3/4 face at frame-right, Jesus walks past them toward us */
function w7aShot(t, st) {
  const c = st.camW7A, u = smooth(clamp((t - T('s02b07')) / 0.72));
  const P = V3(...c.pos), L = V3(...c.look);
  const dir = L.clone().sub(P).normalize(), right = dir.clone().cross(V3(0, 1, 0)).normalize();
  // a gentle follow: the frame drifts a touch left with him and eases in
  return { pos: P.clone().addScaledVector(dir, 0.12 * u).toArray(), look: L.clone().addScaledVector(right, -0.06 * u).toArray(), fov: c.fov, drift: 0.18 };
}
/** W7B: the Void single (from the user's side, inside its hood cone): the glance behind, round eyes, hands knot */
function w7bShot(t, st) {
  const c = st.camW7B, u = smooth(clamp((t - T7B()) / 0.9));
  const P = V3(...c.pos), L = V3(...c.look), dir = L.clone().sub(P).normalize();
  return { pos: P.clone().addScaledVector(dir, 0.1 * u).toArray(), look: c.look, fov: c.fov, drift: 0.15 };
}

// ------------------------------------------------------------------------------------------------ VOID acting
function voidPose(t, st, VV, VW, userEyes) {
  const tS = VV.tS;
  // stop on one foot -> wobble -> settle; a slow blink at the palm; outer wisps sink; lids to 70 %, lower lids up;
  // the hand lowers back into the sleeve; the hem drops; one tiny half-step back.
  const wob = t > tS ? Math.exp(-(t - tS) * 4.5) * Math.sin((t - tS) * TAU * 2.4) : 0;
  const sadden = smooth(clamp((t - T('s02b05+0.75')) / 0.55));
  const handDown = smooth(clamp((t - T('s02b05+0.8')) / 0.75));
  const hemDown = smooth(clamp((t - T('s02b05+0.9')) / 0.45));
  // b07 (seen in W7B): sees him coming, eyes widen -> a quick glance over its LEFT shoulder (nobody) -> back, round,
  // uncertain -> hands knot at its middle
  const tb = T7B();
  const widen = smooth(clamp((t - tb + 0.12) / 0.2));
  const gl = k(t, [[tb + 0.06, 0], [tb + 0.26, 1, 'out'], [tb + 0.56, 1], [tb + 0.66, 0, 'in']]);
  const back = smooth(clamp((t - tb - 0.6) / 0.12));
  const knot = smooth(clamp((t - tb - 0.58) / 0.28));
  let face = VX('hopeful', { lidU: 1.12, browIn: 0.7, browOut: 0.15, mOpen: 0.06, mRound: 0.5, mSmile: 0.08 });
  const sadF = VX('sadSmile', { mSmile: 0.05, lidU: 0.72, lidL: 0.42, browIn: 0.85, browOut: -0.42, lidSad: 0.55, wet: 0.4 });
  for (const kk in sadF) face[kk] = lerp(face[kk], sadF[kk], sadden);
  const t7 = T('s02b07');
  if (t >= t7) {
    const rnd = VX('surprised', { mOpen: 0.08, mRound: 0.75, lidU: 1.36, lidL: 0.0, browIn: 0.75, browOut: 0.6, pupil: 0.9, lidSad: 0 });
    const look = VX('curious', { lidU: 1.18, browIn: 0.55, browOut: 0.3, browAsym: 0.4, mOpen: 0.03, mRound: 0.4, mPress: 0.2 });
    const unc = VX('awkward', { mWide: 0.3, mPress: 0.5, mSmile: 0.0, lidU: 1.3, browIn: 0.95, browOut: 0.4, mWavy: 0.6, saccade: 0.2, pupil: 0.85 });
    face = { ...sadF };
    for (const kk in rnd) face[kk] = lerp(face[kk], rnd[kk], widen);
    for (const kk in look) face[kk] = lerp(face[kk], look[kk], gl);
    for (const kk in unc) face[kk] = lerp(face[kk], unc[kk], Math.max(back * (1 - gl), knot));
    face.autoBlink = 0;
  }
  // the glance: head yaw <= 0.35 rad over its LEFT shoulder (screen-right in W7B) + the eyes do the rest
  const gazeBehind = V3(VW[0], VW[1] + 2.2, VW[2]).add(WD(1.0, -0.8).normalize().multiplyScalar(3));
  let gaze = userEyes;
  let blinkAt = [T('s02b05+0.62')];
  if (t >= t7) {
    const jE = st.jesus.anchor('eyes') || userEyes;
    gaze = gl > 0.5 ? gazeBehind : jE;
    blinkAt = [tb + 0.64];                                // the thought change: a blink as the eyes snap back to him
  }
  const raised = 1 - handDown;
  return {
    pos: VW, yaw: EDGE.Y(VV.yaw + (t >= t7 ? 0.1 : 0)),
    walk: { amount: VV.amt, style: 'waddle', phase: VV.phase },
    body: { bounce: 0.012 * wob + (VV.moving ? jiggle(VV.phase, V_CPS, 0.012) : 0), tilt: 0.05 * wob + 0.04 * gl, twist: 0.22 * gl, recoil: 0.06 * widen * (1 - knot), shrug: 0.3 * knot + 0.12 * gl },
    head: { yaw: 0.35 * gl, pitch: 0.06 + (t >= t7 ? -0.05 * widen : 0.05 * sadden), roll: -0.06 * gl },
    gaze, face, blinkAt,
    armL: t >= t7 ? (knot > 0 ? { preset: 'belly', from: 'rest', mix: knot, offset: WD(-0.35, 0.3).multiplyScalar(0.18 * knot).toArray(), hand: { curl: 0.55, cup: 0.6 } } : { preset: 'rest' })
      : { preset: 'wave', from: 'rest', mix: 0.55 * raised, hand: { spread: 0.5 * raised + 0.1, curl: 0.12 + 0.3 * handDown } },
    armR: t >= t7 ? (knot > 0 ? { preset: 'belly', from: 'rest', mix: knot, offset: WD(0.35, 0.3).multiplyScalar(0.18 * knot).toArray(), hand: { curl: 0.55, cup: 0.6 } } : { preset: 'rest' })
      : { preset: 'rest', hand: { curl: 0.7, thumb: 0.85, cup: 0.5 } },
    extra: { hem: 0.5 * (1 - hemDown) * (t < t7 ? 1 : 0), motes: 1.1, rim: 1.05 },
  };
}

// ------------------------------------------------------------------------------------------------ JESUS acting
function jesusPose(t, st, J, JW, ue, vEyes) {
  const tA = T('s02b02');
  const user = st.user;
  const pre = { pos: JW, yaw: EDGE.Y(J.yaw), walk: { amount: J.amt, style: J.style, phase: J.phase } };
  const full = (jesus) => {
    const P = { ...pre };
    const uEyes = ue || V3(...EDGE.W(M.U.p)).add(V3(0, 0.9, 0));
    const phone = t >= T('s02b03') ? user.anchor('phone') : null;
    // ---------------- BEND: content, looking up at the sky, hands behind
    if (t < T('s02b03')) {
      P.face = JX('content', { lidU: 0.52, autoBlink: 0 });
      P.head = { pitch: -0.42, roll: 0.06 };
      P.gaze = null; P.face.gazePitch = 0.12;
      P.armL = { preset: 'behind' }; P.armR = { preset: 'behind' };
      P.body = { breathe: 1.5, breathRate: 0.3 };
      P.blinkAt = [T('s02b08+0.35')];
      P.glow = 1 + 1.6 * Math.exp(-Math.max(0, t - tA) * 5);
      return P;
    }
    // ---------------- ARRIVE: the scream (blink, brows up, polite tilt) -> looks down at the kid at his feet,
    // sympathy, soft "oh", hands come out from behind his back, open
    if (t < T('s02b05')) {
      const t3 = T('s02b03'), t4 = T('s02b04');
      const sur = bump(t, t3 + 0.4, t4 + 0.45, 0.22);
      const down = smooth(clamp((t - t4 - 0.35) / 0.5));
      const oh = bump(t, t4 + 0.85, t4 + 1.9, 0.35);
      const open = smooth(clamp((t - t4 - 1.0) / 0.6));
      let f = JX('content', { lidU: 0.6 });
      const fs = JX('surprised', { mOpen: 0.1, mRound: 0.35, lidU: 1.25 });
      const fc = JX('compassion', { lidU: 1.0, browIn: 1.05 });
      for (const kk in fs) f[kk] = lerp(f[kk], fs[kk], sur);
      for (const kk in fc) f[kk] = lerp(f[kk], fc[kk], down * (1 - sur * 0.5));
      f.mOpen = Math.max(f.mOpen, 0.18 * oh); f.mRound = Math.max(f.mRound, 0.7 * oh); f.mPress = f.mPress * (1 - oh);
      P.face = f;
      P.gaze = uEyes;
      P.head = { look: uEyes, follow: lerp(0.2, 0.55, down), roll: 0.14 * sur + 0.06 * down, pitch: lerp(-0.2, 0, Math.max(sur, down)) };
      P.blinkAt = [t3 + 0.45, t4 + 0.6];
      const behindW = 1 - open;
      P.armL = { preset: [['behind', behindW], ['open', open]], hand: { cup: 0.35 } };
      P.armR = { preset: [['behind', behindW], ['open', open]], hand: { cup: 0.35 } };
      P.body = { lean: 0.09 * down, recoil: 0.06 * sur };
      return P;
    }
    // ---------------- JCU: "And he sees all of this." — user (12 f) -> phone (6 f) -> up to the Void, recognition
    // (warm crinkle, one corner up: oh, it's you) -> back to the user -> slow blink on "this" -> eyes open bright, a
    // corner tucks up (an idea, mouth closed) -> small nod
    if (t < T('s02b07')) {
      const b = T('s02b06');
      const tPh = b + 0.42, tV = b + 0.66, tRec = b + 0.8, tBack = b + 1.0, tBl = T('s02b06+1.04'), tIdea = tBl + 0.42, tNod = tIdea + 0.3;
      let gaze = uEyes;
      if (t >= tPh && t < tV) gaze = phone || uEyes;
      else if (t >= tV && t < tBack) gaze = vEyes;
      const rec = bump(t, tRec - 0.05, tBl + 0.1, 0.4);
      const idea = smooth(clamp((t - tIdea) / 0.3));
      let f = JX('compassion', { lidU: 1.0, mSmile: 0.02 });
      // recognition: lower lids up (a warm crinkle), outer brows up, mouth CLOSED with one corner up
      const fr = { browOut: 0.6, browIn: 0.35, browSq: 0, lidSad: 0.1, lidL: 0.5, lidU: 0.98, mSmile: 0.16, mAsym: 0.42, mOpen: 0, mRound: 0, mPress: 0.65, wet: 0.35 };
      for (const kk in fr) f[kk] = lerp(f[kk], fr[kk], rec);
      // the idea: lids open bright (~1.2), mouth closed, an asymmetric corner tuck, catchlight-bright
      const fi = { lidU: 1.2, lidL: 0.18, lidSad: 0, pupil: 1.12, wet: 0.55, browIn: 0.32, browOut: 0.42, browSq: 0, browAsym: 0.25, mSmile: 0.14, mAsym: 0.4, mPress: 0.7, mOpen: 0, mRound: 0, mTeethU: 0, mTeethL: 0 };
      for (const kk in fi) f[kk] = lerp(f[kk], fi[kk], idea);
      // slow blink (manual, ~0.4 s) on "this"
      f.blink = bump(t, tBl, tBl + 0.42, 0.45);
      f.autoBlink = 0;
      P.face = f; P.gaze = gaze;
      const lookUp = t >= tV && t < tBack + 0.12 ? 1 : 0;
      P.head = { look: gaze, follow: 0.35 + 0.15 * lookUp, pitch: 0.13 * bump(t, tNod, tNod + 0.55, 0.4) - 0.04 * idea, roll: 0.05 };
      P.armL = { preset: 'open', reach: 0.65, hand: { cup: 0.4 } };
      P.armR = { preset: 'open', reach: 0.65, hand: { cup: 0.4 } };
      P.body = { breathe: 1.2, lean: 0.04 };
      return P;
    }
    // ---------------- W7: walks past the user; the hand on the user's side floats out palm-down ("one sec, stay
    // there"), a small reassuring smile and a nod to them without breaking stride; then eyes ahead to the Void
    const t7 = T('s02b07');
    const sec = bump(t, t7 + 0.04, t7 + 1.0, 0.45);
    const toUser = bump(t, t7 - 0.05, t7 + 0.95, 0.35);
    const lookP = toUser > 0.02 ? uEyes : vEyes;
    P.face = JX('warm', { mSmile: 0.5 + 0.12 * toUser, lidL: 0.38, lidU: 0.92, browIn: 0.4, mOpen: 0, autoBlink: 0 });
    P.gaze = lookP;
    P.head = { look: lookP, follow: 0.6 * toUser + 0.3 * (1 - toUser), pitch: 0.15 * bump(t, t7 + 0.22, t7 + 0.66, 0.45), roll: 0.06 * toUser };
    // the hand on the side the user is actually on (in his own frame)
    const onLeft = jesus.root.worldToLocal(uEyes.clone()).x > 0, side = onLeft ? 'L' : 'R';
    const sh = jesus.anchor('shoulder' + side);
    const sideW = V3(onLeft ? 1 : -1, 0, 0).transformDirection(jesus.root.matrixWorld), fwdW = V3(0, 0, 1).transformDirection(jesus.root.matrixWorld);
    // palm-down at hip height, out to the side and a little forward: a gentle "stay there" pat on the air
    const pat = 0.035 * Math.sin(clamp((t - t7 - 0.25) / 0.5) * Math.PI * 2) * bump(t, t7 + 0.2, t7 + 0.8, 0.5);
    const tgt = sh ? sh.clone().addScaledVector(sideW, 0.3).addScaledVector(fwdW, 0.22).add(V3(0, -0.33 - pat, 0)) : uEyes;
    const gest = sec > 0.01 ? { preset: 'stop', target: tgt.toArray(), reach: sec, palm: [0, -1, 0], fingers: sideW.clone().multiplyScalar(0.4).addScaledVector(fwdW, 0.9).normalize().toArray(), hand: { curl: 0.06, spread: 0.3, cup: 0.12, thumb: 0.45 } } : { preset: 'rest' };
    P.armL = onLeft ? gest : { preset: 'rest' };
    P.armR = onLeft ? { preset: 'rest' } : gest;
    return P;
  };
  return { pre, full };
}

// ------------------------------------------------------------------------------------------------ USER acting
function userPose(t, st, UT, B, uPos, jEyes, vEyes, jesus) {
  const P = { pos: uPos, yaw: EDGE.Y(B.yaw), walk: { amount: B.run, style: 'run', phase: B.phase, flail: 0.8 },
    body: { sit: B.sit, sitPath: 'fall', scoot: B.scoot, scootPhase: B.scootPh, pant: 1, hunch: 0.25 } };
  const t3 = T('s02b03');
  if (t < T('s02b04')) {
    // still looking back as they burst in -> head snaps forward -> a whole person, right there: SCREAM
    const lb = 0.6 * (1 - smooth(clamp((t - t3 - 0.02) / 0.09)));
    P.body = { ...P.body, lookBack: lb, recoil: 0.32 * smooth(clamp((t - t3 - 0.1) / 0.12)), shrug: 0.5 * smooth(clamp((t - t3 - 0.08) / 0.1)) };
    // tall open oval, pinpoint pupils, sky-high lids and brows; held (lip-sync only lightly blended)
    P.face = UX('gasp', { mOpen: 1.25, mRound: 0.62, mWide: 0.12, mTeethU: 0.7, mTeethL: 0.5, mTremble: 0.25, lidU: 1.58, lidL: 0, lidDrop: 0.9, pupil: 0.25, browIn: 1.15, browOut: 1.0, browSq: 0.3, talk: 0.2, autoBlink: 0, wet: 1 });
    P.gaze = t > t3 + 0.04 ? jEyes : vEyes;
    // arms flung up; the phone pops out of the LEFT hand at the side (shoulder height, clear of the mouth) and is caught
    const fl = smooth(clamp((t - t3 - 0.08) / 0.12));
    const fum = bump(t, t3 + 0.12, t3 + 0.5, 0.35);
    const yw = EDGE.Y(B.yaw), left = V3(Math.cos(yw), 0, -Math.sin(yw)), fw = V3(Math.sin(yw), 0, Math.cos(yw));
    P.armR = { preset: 'wave', reach: fl, offset: left.clone().multiplyScalar(-0.06).addScaledVector(fw, -0.05).toArray(), hand: { curl: 0.05, spread: 1, splay: 0.8 } };
    P.armL = { preset: 'stop', reach: fl, offset: left.clone().multiplyScalar(0.15 + 0.07 * fum).addScaledVector(fw, -0.04).add(V3(0, -0.02 + 0.06 * fum, 0)).toArray(),
      palm: fw.clone().multiplyScalar(0.3).add(V3(0, 0.5, 0)).addScaledVector(left, -0.6).normalize().toArray(), hand: { curl: 0.1 * (1 - fum), spread: 0.6 * fum } };
    P.extra = { phone: 0.85, tears: 0.8, phoneUp: 0 };
    P.walk.flail = 1;
    return P;
  }
  const t4 = T('s02b04');
  if (t < T('s02b05')) {
    // the skid (eyes wide, O mouth, phone held up high) -> THUD (face compresses, glasses jump) -> frantic twist round
    // -> scoot, scoot, bump -> RIGHT hand shoots up, palm out at the Void; LEFT clutches the phone
    const def = smooth(clamp((t - UT.tSc1 + 0.05) / 0.16));
    P.face = k(t, [[t4, UX('gasp', { lidU: 1.5, pupil: 0.3 })], [UT.tImpact - 0.03, UX('gasp', { lidU: 1.5, pupil: 0.3, mOpen: 0.85 })],
      [UT.tImpact + 0.03, UX('scrunch', { mOpen: 0.3 }), 'out'], [UT.tImpact + 0.15, UX('scrunch', { mOpen: 0.3 })],
      [UT.tTw0 + 0.05, UX('terror', { lidU: 1.45 }), 'out'], [UT.tSc1, UX('terror', { lidU: 1.5, pupil: 0.34, lidL: 0.3 })]]);
    P.gaze = t > UT.tTw0 + 0.12 ? vEyes : jEyes;
    P.body = { ...P.body, shrug: 0.25 + 0.35 * def, tremble: 0.5 * def, recoil: 0.1 * def, flinch: 0.5 * bump(t, UT.tImpact - 0.03, UT.tImpact + 0.2, 0.25) };
    P.armR = def > 0 ? { preset: 'defend', target: st.defendStd.toArray(), reach: def, tremble: 1, hand: { spread: 1, splay: 1, curl: 0 } } : { preset: 'rest' };
    P.armL = def > 0 ? { preset: 'clutch', reach: def } : { preset: 'hold' };
    P.extra = { phone: 0.85, tears: 0.7 };
    if (t > UT.tSc1 - 0.05) P.blinkAt = [];
    return P;
  }
  // seated at U from here: hand up, trembling, phone clutched
  const P2_ = { ...P, body: { sit: 1, shrug: 0.6, tremble: 0.55, pant: 1, hunch: 0.25, recoil: 0.12 }, walk: { amount: 0 } };
  P2_.extra = { phone: 0.85, tears: 0.6 };
  P2_.armL = { preset: 'clutch' };
  P2_.armR = { preset: 'defend', target: st.defendStd.toArray(), tremble: 1, hand: { spread: 1, splay: 1, curl: 0 } };
  P2_.face = UX('terror', { lidU: 1.42, pupil: 0.38, lidL: 0.32, mOpen: 0.32 });
  P2_.gaze = vEyes;
  if (t >= T('s02b07')) {
    // eyes follow Jesus as he passes (eyes lead, head follows slower); the raised hand bends at the wrist in confusion;
    // the mouth closes ... the eyes flick on to where he's heading (the Void) ... and the mouth falls open: oh no.
    const t7 = T('s02b07');
    const jp = jEyes || vEyes;
    const bend = smooth(clamp((t - t7 - 0.2) / 0.3));
    const close = smooth(clamp((t - t7 - 0.12) / 0.16)) * (1 - smooth(clamp((t - t7 - 0.5) / 0.14)));
    const fall = smooth(clamp((t - t7 - 0.5) / 0.16));
    const ahead = t > t7 + 0.4 && t < t7 + 0.62;
    P2_.gaze = ahead ? vEyes : jp;
    P2_.head = { look: jp, follow: 0.4 * smooth(clamp((t - t7 - 0.08) / 0.45)) };
    // a little lean away (to their left) as he steps right past them; the eyes stay on him
    const away = bump(t, t7 + 0.1, t7 + 0.75, 0.45);
    P2_.body = { ...P2_.body, tremble: 0.3, shrug: 0.5 + 0.15 * away, tilt: 0.13 * away, recoil: 0.12 + 0.1 * away };
    // the hand stays up, out in front at chest height (it sagged while he looked: during JCU, offscreen; it rises back to
    // the s03 height during W7B, offscreen) and bends at the wrist in confusion
    const yw = EDGE.Y(M.U.yaw), fw = V3(Math.sin(yw), 0, Math.cos(yw)), rt = V3(-Math.cos(yw), 0, Math.sin(yw));
    const toV = V3(vEyes.x - uPos[0], 0, vEyes.z - uPos[2]).normalize();
    P2_.armR = { preset: 'stop', reach: 1, offset: rt.clone().multiplyScalar(0.11).addScaledVector(fw, 0.05).add(V3(0, -0.01, 0)).toArray(),
      palm: toV.clone().add(V3(0, 0.15, 0)).normalize().toArray(), tremble: 0.35, hand: { spread: 0.7, splay: 0.55, curl: 0.4 * bend, thumb: 0.7 } };
    // the wrist flops forward: fingers from "up" to pointing at the Void, a little down (palm turns down with it)
    P2_.armR.fingers = V3(0, 1, 0).multiplyScalar(1 - 0.85 * bend).addScaledVector(toV, 0.95 * bend).add(V3(0, -0.2 * bend, 0)).normalize().toArray();
    if (bend > 0) P2_.armR.palm = toV.clone().multiplyScalar(1 - 0.7 * bend).add(V3(0, 0.15 - 1.0 * bend, 0)).normalize().toArray();
    const f = UX('disbelief', { mOpen: lerp(0.3, 0.0, close) + 0.42 * fall, mRound: 0.3 * fall, mPress: 0.4 * close, lidU: 1.2 + 0.25 * fall, browIn: 0.65 + 0.35 * fall, browOut: 0.35 + 0.35 * fall, autoBlink: 0 });
    P2_.face = f;
    P2_.blinkAt = [t7 + 0.38];
  }
  return P2_;
}

// ------------------------------------------------------------------------------------------------ camera fits
// Reference poses -> fitted cameras whose subjects land on the staging plan's screen heights. Done once in setup
// (pure, deterministic).
function fitShots(st) {
  const { set, user, vd, jesus } = st;
  const Uw = G(set, M.U.p[0], M.U.p[2]), Jw = G(set, M.J1.p[0], M.J1.p[2]);
  const LW = (x, y, z) => EDGE.W(x, y, z);
  const yU = EDGE.Y(M.U.yaw);
  // --- the final seated pose (hand up at the Void), Jesus at J1 looking down at the kid
  const VVr = voidAt(T('s02b05+0.4')), VWr = G(set, VVr.pos[0], VVr.pos[1]);
  vd.update(T('s02b05+0.4'), voidPose(T('s02b05+0.4'), st, VVr, VWr, V3(Uw[0], 0.9, Uw[2])));
  const veR = vd.anchor('eyes'), vhR = vd.anchor('handL');
  user.update(0, { pos: Uw, yaw: yU, body: { sit: 1, shrug: 0.6 }, armR: { preset: 'defend', target: st.defendStd.toArray() }, armL: { preset: 'clutch' } });
  jesus.update(0, { pos: Jw, yaw: EDGE.Y(M.J1.yaw - 0.72), body: { lean: 0.09 }, head: { look: user.anchor('eyes'), follow: 0.55 } });
  const ue = user.anchor('eyes'), uh = user.anchor('handR'), je = jesus.anchor('eyes');
  // ARRIVE B (end of the push): medium two-shot from the right of the pair, low (it compresses the two faces
  // together): Jesus's eyes ~y 340 at left, the kid's 3/4 face ~y 740 in front of his robe, both faces >= ~110 px
  {
    const g0 = EDGE.shot([-1.45, 1.2, 1.6], { dist: 3.0, yaw: 84, pitch: -9, fov: 36, screenY: 0.42 });
    const f = fitCam([[je, 300, 340, 1], [ue, 420, 740, 1]], 36, g0.pos, g0.look, { reg: 0.3, yMin: 0.4, yMax: 0.65 });
    st.camARR_B = { ...f, fov: 36 };
    console.log(`s02 ARRIVE_B fit ${f.err.toFixed(1)}px local ${EDGE.L(f.pos).map((v) => v.toFixed(2))}`);
  }
  // ARRIVE A (the burst-in): side two-shot, Jesus frame-left (3/4), the kid bursts in from frame right, falls mid-frame
  st.camARR_A = { ...EDGE.shot([-1.05, 1.0, 1.15], { dist: 4.0, yaw: 62, pitch: -3, fov: 42, screenY: 0.5 }), fov: 42 };
  // REV: from just behind the user's raised right hand up to the Void (hand soft in the foreground ~y 700, eyes ~y 285,
  // the Void's own raised hand in frame at right so its slow lowering is the motion we watch)
  {
    user.update(0, { pos: Uw, yaw: yU, body: { sit: 1, shrug: 0.6 }, armR: { preset: 'defend', target: st.defendStd.toArray() }, armL: { preset: 'clutch' } });
    const ue2 = user.anchor('eyes'), uh2 = user.anchor('handR');
    const back = V3(-Math.sin(yU), 0, -Math.cos(yU)), right = V3(-Math.cos(yU), 0, Math.sin(yU));
    const g = ue2.clone().addScaledVector(back, 0.7).addScaledVector(right, 0.3).add(V3(0, -0.08, 0));
    const f = fitCam([[veR, 310, 285, 1], [uh2, 260, 735, 0.6], [vhR, 560, 450, 0.6]], 54, g.toArray(), veR.toArray(), { reg: 0.3, yMin: ue2.y - 0.25, yMax: ue2.y + 0.05 });
    st.camREV = { ...f, fov: 54 }; console.log(`s02 REV fit ${f.err.toFixed(1)}px local ${EDGE.L(f.pos).map((v) => v.toFixed(2))} hand ${vhR.toArray().map((v) => v.toFixed(2))}`);
  }
  // W7A: reverse from the Void's side, low (the user's eye height): the user's 3/4 face lower right, Jesus walking
  // past them toward us at upper left (reference: t7 + 0.4)
  {
    const tr = T('s02b07+0.4'), w = jesusWalkS02(tr);
    jesus.update(tr, { pos: G(set, w.pos[0], w.pos[1]), yaw: EDGE.Y(w.yaw), walk: { amount: w.amt, style: 'walk', phase: w.phase } });
    user.update(0, { pos: Uw, yaw: yU, body: { sit: 1, shrug: 0.6 }, armR: { preset: 'defend', target: st.defendStd.toArray() }, armL: { preset: 'clutch' } });
    const jw = jesus.anchor('eyes'), uw = user.anchor('eyes');
    const a = 106 * Math.PI / 180, g = [M.U.p[0] + 2.4 * Math.sin(a), 0.92, M.U.p[2] + 2.4 * Math.cos(a)];
    const f = fitCam([[jw, 290, 300, 1], [uw, 450, 690, 1]], 42, LW(...g), uw.toArray(), { reg: 0.5, yMin: 0.86, yMax: 0.98 });
    st.camW7A = { ...f, fov: 42 };
    console.log(`s02 W7A fit ${f.err.toFixed(1)}px local ${EDGE.L(f.pos).map((v) => v.toFixed(2))}`);
  }
  // W7B: the Void single from the user's side (yaw -45 local: inside its hood cone, Jesus's path stays out of frame at
  // right, 40+ deg off s03's opening axis): eyes ~y 400, the whole hood and the knotted hands in frame
  {
    const Vw = G(set, M.V.p[0], M.V.p[2]);
    vd.update(T('s02b07+1.5'), { pos: Vw, yaw: EDGE.Y(M.V.yaw + 0.1), armL: { preset: 'belly' }, armR: { preset: 'belly' } });
    const ve = vd.anchor('eyes');
    st.camW7B = { ...EDGE.shot(EDGE.L(ve), { dist: 5.0, yaw: -45, pitch: -3, fov: 40, screenY: sy(400) }), fov: 40 };
    console.log(`s02 W7B cam local ${EDGE.L(st.camW7B.pos).map((v) => v.toFixed(2))}`);
  }
}
