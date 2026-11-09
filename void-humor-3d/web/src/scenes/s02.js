// s02 and_jesus_appears — an empty bend in the path waits (the joke), Jesus is simply there on "Now.", strolls; the
// screaming user skids onto their backside at his feet; the Void arrives and gives them room; Jesus takes it all in
// and has an idea; he strolls past the user toward the Void ("one sec").
// Shots: BEND (locked reverse toward the sun) · ARRIVE (low side two-shot, tilts down with the fall) · REV (low angle
// from behind the user's raised hand up to the Void) · JCU (close on Jesus, slow push) · WIDE7 (user's eye height).
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

const M = EDGE.M;
const TAU = Math.PI * 2;
const L2 = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u)];
const P2 = (m) => [m.p[0], m.p[2]];

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
  return { pos: p, yaw: M.V.yaw, phase, amt, tS, tPlant, tB, moving: t < tS };
}

// ------------------------------------------------------------------------------------------------ USER blocking
// skid in from upstage-right (frame right in ARRIVE) -> fall onto the backside sliding toward Jesus -> twist round
// (face passes the lens) -> two scoots back until the back meets Jesus's shins at U.
const USTART = (() => { const sk = [-0.55, 0.6], d = [1.05, -1.2], n = Math.hypot(...d); return [sk[0] + d[0] / n * 0.62, sk[1] + d[1] / n * 0.62]; })();
function userTimes() {
  const tF = T('s02b04');
  return { tR: T('s02b03'), tF, tSlide1: tF + 0.85, tTw0: tF + 0.88, tTw1: tF + 1.32, tSc0: tF + 1.36, tSc1: tF + 1.98, tImpact: tF + 0.8 * 0.75 };
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
    fitShots(st);
    return st;
  },

  async update(t, app, st) {
    st.__t = t;
    const { set, user, vd, jesus } = st;
    const cam = app.camera;
    const shot = t < T('s02b03') ? 'BEND' : t < T('s02b03+0.42') ? 'SCREAM' : t < T('s02b05') ? 'ARRIVE' : t < T('s02b06') ? 'REV' : t < T('s02b07') ? 'JCU' : 'WIDE7';
    const jesusIn = t >= T('s02b02');
    const names = shot === 'BEND' ? (jesusIn ? ['JESUS'] : []) : shot === 'SCREAM' ? ['USER'] : shot === 'ARRIVE' ? ['JESUS', 'USER'] : shot === 'REV' ? ['USER', 'VOID'] : shot === 'JCU' ? ['JESUS', 'USER'] : ['JESUS', 'USER', 'VOID'];
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
    const cheat = t < T('s02b03') ? 0 : t < T('s02b07') ? -0.72 : -0.72 * (1 - smooth((t - T('s02b07')) / 0.5));   // camera cheat from the cut on
    if (t < T('s02b07')) J.yaw += cheat;
    const JW = G(set, J.pos[0], J.pos[1]);
    // --- Void
    const VV = voidAt(t);
    const VW = G(set, VV.pos[0], VV.pos[1]);
    // --- User
    const hx = st.hipL[0], hz = st.hipL[1];
    const rotOff = (yawL) => { const y = EDGE.Y(yawL); return [hx * Math.cos(y) + hz * Math.sin(y), -hx * Math.sin(y) + hz * Math.cos(y)]; };
    const Uw = EDGE.W(M.U.p), Uyaw = M.U.yaw, fU = [Math.sin(EDGE.Y(Uyaw)), Math.cos(EDGE.Y(Uyaw))];
    const ro = rotOff(Uyaw);
    const hipFinal = [Uw[0] + ro[0], Uw[2] + ro[1]];
    const hipTwist = [hipFinal[0] + fU[0] * 0.18, hipFinal[1] + fU[1] * 0.18];
    const runYawL = Math.atan2(M.USKID.p[0] - USTART[0], M.USKID.p[2] - USTART[1]) - 0.35;
    let uPosW, uYawL, sit = 0, runAmt = 0, scoot = 0, scootPh = 0;
    {
      const sk = EDGE.W(M.USKID.p), st0 = EDGE.W(USTART[0], 0, USTART[1]);
      const roRun = rotOff(runYawL);
      const slideEnd = [hipTwist[0] - roRun[0], hipTwist[1] - roRun[1]];
      if (t < UT.tF) {                                   // the run in
        const u = clamp((t - UT.tR) / (UT.tF - UT.tR)), e = u * (1.55 - 0.55 * u);     // braking: 2.4 -> ~1.0 m/s
        uPosW = [lerp(st0[0], sk[0], e), lerp(st0[2], sk[2], e)]; uYawL = runYawL; runAmt = 1;
      } else if (t < UT.tTw0) {                          // skid + fall + slide toward Jesus
        const u = clamp((t - UT.tF) / (UT.tSlide1 - UT.tF));
        const e = 1 - Math.pow(1 - u, 2.2);
        uPosW = [lerp(sk[0], slideEnd[0], e), lerp(sk[2], slideEnd[1], e)]; uYawL = runYawL;
        runAmt = 1 - smooth(clamp((t - UT.tF) / 0.22));
        sit = clamp((t - UT.tF) / 0.75);
      } else if (t < UT.tSc0) {                          // twist round on the backside (yaw increasing)
        const u = smooth(clamp((t - UT.tTw0) / (UT.tTw1 - UT.tTw0)));
        uYawL = lerp(runYawL, Uyaw, u);
        const r2 = rotOff(uYawL);
        uPosW = [hipTwist[0] - r2[0], hipTwist[1] - r2[1]]; sit = 1;
      } else {                                           // scoot, scoot, bump
        const u = clamp((t - UT.tSc0) / (UT.tSc1 - UT.tSc0));
        scootPh = 2 * u; scoot = t < UT.tSc1 + 0.1 ? 1 : 1 - smooth((t - UT.tSc1 - 0.1) / 0.2);
        const back = 0.18 * u;
        uPosW = [hipTwist[0] - fU[0] * back - ro[0], hipTwist[1] - fU[1] * back - ro[1]]; uYawL = Uyaw; sit = 1;
      }
    }
    const uPos = [uPosW[0], 0, uPosW[1]];

    // ============================================================================ camera (before rig updates)
    let shotDef;
    if (shot === 'BEND') shotDef = { ...EDGE.cam('BEND'), drift: 0.15 };
    else if (shot === 'ARRIVE') {
      const c = st.camARR;
      const dn = smooth(clamp((t - T('s02b04+0.15')) / 0.9));       // tilt down with the fall
      const up0 = 0;                                   // (the burst-in is framed a touch higher)
      shotDef = { pos: [c.pos[0], c.pos[1] + 0.03 * (1 - dn), c.pos[2]], look: [c.look[0], c.look[1] + up0 - 0.3 * dn, c.look[2]], fov: 40, drift: 0.25 };
    }
    applyShotPre(cam, shotDef, t);

    // ============================================================================ USER
    let ue0 = null;
    if (t >= T('s02b03')) {
      const pre = { pos: uPos, yaw: EDGE.Y(uYawL), walk: { amount: runAmt, style: 'run', phase: (t - UT.tR) * 1.2 + 0.1 }, body: { sit, sitPath: 'fall', scoot, scootPhase: scootPh }, armL: t >= T('s02b05') ? { preset: 'clutch' } : undefined, armR: t >= T('s02b05') ? { preset: 'defend' } : undefined };
      user.update(t, pre);
      ue0 = user.anchor('eyes');
    }
    if (shot === 'SCREAM') {
      const ry = EDGE.Y(runYawL + 0.35), fwd = V3(Math.sin(ry), 0, Math.cos(ry)), side = V3(Math.cos(ry), 0, -Math.sin(ry));
      const cp = ue0.clone().addScaledVector(fwd, 1.55).addScaledVector(side, 0.3).add(V3(0, -0.06, 0));
      shotDef = frame(ue0.toArray(), cp, 33, 0.33);
      applyShotPre(cam, shotDef, t);
    }
    // Jesus provisional (position/walk only) -> anchors for the Void's gaze and the close-up camera
    const jPre = { pos: JW, yaw: EDGE.Y(J.yaw), walk: { amount: J.amt, style: J.style, phase: J.phase } };
    if (jesusIn) jesus.update(t, jPre);
    // ============================================================================ VOID (pose; updated even when off-cast for anchors)
    const vEyesGuess = V3(VW[0], VW[1] + 2.16, VW[2]);
    const vPose = voidPose(t, st, VV, VW, ue0 || vEyesGuess, shot);
    vd.update(t, vPose);
    const vEyes = vd.anchor('eyes');

    // cameras that depend on rig anchors
    if (shot === 'REV') {
      // low angle from just behind the user's raised right hand up to the Void (fitted), a very slow push
      const c = st.camREV, push = 0.18 * smooth((t - T('s02b05')) / 1.7);
      const dir = V3(...c.look).sub(V3(...c.pos)).normalize();
      shotDef = { pos: V3(...c.pos).addScaledVector(dir, push).toArray(), look: c.look, fov: 50, drift: 0.2 };
      applyShotPre(cam, shotDef, t);
    }

    // ============================================================================ JESUS
    const jPose = jesusPose(t, st, J, JW, ue0, vEyes, shot);
    if (jesusIn) {
      if (shot === 'JCU') {
        const eyes = jesus.anchor('eyes');
        const u = smooth(clamp((t - T('s02b06')) / (T('s02b07') - T('s02b06'))));
        shotDef = frameLocal(eyes, { dist: lerp(1.6, 1.3, u), yaw: 110, pitch: 1, fov: 33, screenY: sy(415), drift: 0.15 });
        applyShotPre(cam, shotDef, t);
      }
      if (shot === 'WIDE7') {
        shotDef = wide7Shot(t, st);
        applyShotPre(cam, shotDef, t);
      }
      jesus.update(t, jPose.full(jesus));
    }
    const jHead = jesusIn ? jesus.anchor('eyes') : null;

    // ============================================================================ USER (final)
    if (t >= T('s02b03')) user.update(t, userPose(t, st, UT, uPos, uYawL, sit, runAmt, scoot, scootPh, jHead, vEyes, jesus));

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
      sunShift: shot === 'BEND' ? -0.09 : 0, sunGlow: shot === 'BEND' ? 0.75 : shot === 'JCU' ? 0.7 : 1, shadowAt, clear, seeds: shot === 'BEND' ? 0.6 : shot === 'ARRIVE' || shot === 'JCU' ? 0.45 : 1 });
    st.look = lookFor('s02', set.look);
  },
};

// ------------------------------------------------------------------------------------------------ helpers
function applyShotPre(cam, s, t) { if (s) applyShot(cam, s, t); }
/** a shot from camera position cp looking so that `look` (world) lands at screen height sy (0..1) */
function frame(look, cp, fov, syF) {
  const L = V3(...look), d = L.clone().sub(cp), dist = d.length();
  const off = (syF - 0.5) * 2 * dist * Math.tan(fov * Math.PI / 360);
  return { pos: cp.toArray(), look: [L.x, L.y + off, L.z], fov, drift: 0.2 };
}
function frameLocal(eyes, o) {   // EDGE.shot on a world point (look in world, yaw in local degrees)
  return EDGE.shot(EDGE.L(eyes), o);
}
function wide7Shot(t, st) {
  const c = st.camW7, u = smooth(clamp((t - T('s02b07')) / 1.6));
  const dir = V3(...c.look).sub(V3(...c.pos)).normalize();
  return { pos: V3(...c.pos).addScaledVector(dir, 0.15 * u).toArray(), look: c.look, fov: 44, drift: 0.25 };
}

// ------------------------------------------------------------------------------------------------ VOID acting
function voidPose(t, st, VV, VW, userEyes, shot) {
  const tS = VV.tS;
  // stop on one foot -> wobble -> settle; a slow blink at the palm; outer wisps sink; lids to 70 %, lower lids up;
  // the hand lowers back into the sleeve; the hem drops; one tiny half-step back.
  const wob = t > tS ? Math.exp(-(t - tS) * 4.5) * Math.sin((t - tS) * TAU * 2.4) : 0;
  const sadden = smooth(clamp((t - T('s02b05+0.75')) / 0.55));
  const handDown = smooth(clamp((t - T('s02b05+0.85')) / 0.6));
  const hemDown = smooth(clamp((t - T('s02b05+0.9')) / 0.45));
  // b07: sees him coming -> glance over its LEFT shoulder (nobody) -> back, round, uncertain -> hands knot at its middle
  const t7 = T('s02b07');
  const widen = smooth(clamp((t - t7 - 0.1) / 0.25));
  const gl = k(t, [[t7 + 0.42, 0], [t7 + 0.62, 1, 'out'], [t7 + 0.98, 1], [t7 + 1.16, 0, 'inOut']]);
  const knot = smooth(clamp((t - t7 - 1.05) / 0.45));
  let face = VX('hopeful', { lidU: 1.12, browIn: 0.7, browOut: 0.15, mOpen: 0.06, mRound: 0.5, mSmile: 0.08 });
  const sadF = VX('sadSmile', { mSmile: 0.05, lidU: 0.72, lidL: 0.42, browIn: 0.85, browOut: -0.42, lidSad: 0.55, wet: 0.4 });
  for (const kk in sadF) face[kk] = lerp(face[kk], sadF[kk], sadden);
  if (t >= t7) {
    const rnd = VX('surprised', { mOpen: 0.1, mRound: 0.7, lidU: 1.3, browIn: 0.7, browOut: 0.55, pupil: 0.95 });
    const unc = VX('awkward', { mWide: 0.35, mPress: 0.55, mSmile: 0.0, lidU: 1.2, browIn: 0.85, browOut: 0.35 });
    face = { ...sadF };
    for (const kk in rnd) face[kk] = lerp(sadF[kk], rnd[kk], widen);
    for (const kk in unc) face[kk] = lerp(face[kk], unc[kk], knot);
  }
  const gazeBehind = V3(VW[0], VW[1] + 2.2, VW[2]).add(WD(1.0, -0.8).normalize().multiplyScalar(3));
  let gaze = userEyes;
  let blinkAt = [T('s02b05+0.62')];
  if (t >= t7) {
    gaze = t > t7 + 0.4 && t < t7 + 1.08 ? gazeBehind : (st.jesus.root.parent ? st.jesus.anchor('eyes') : userEyes);
    blinkAt = [t7 + 1.1];
  }
  const raised = 1 - handDown;
  return {
    pos: VW, yaw: EDGE.Y(VV.yaw + (t >= t7 ? 0.1 : 0)),
    walk: { amount: VV.amt, style: 'waddle', phase: VV.phase },
    body: { bounce: 0.012 * wob + (VV.moving ? jiggle(VV.phase, V_CPS, 0.012) : 0), tilt: 0.05 * wob, twist: 0.3 * gl, recoil: 0.05 * widen * (1 - knot), shrug: 0.25 * knot },
    head: { yaw: 1.45 * gl, pitch: 0.06 + (t >= t7 ? -0.05 * widen : 0.05 * sadden), roll: -0.05 * gl },
    gaze, face, blinkAt,
    armL: t >= T('s02b07') ? (knot > 0 ? { preset: 'belly', from: 'rest', mix: knot, offset: WD(-0.35, 0.3).multiplyScalar(0.18 * knot).toArray(), hand: { curl: 0.55, cup: 0.6 } } : { preset: 'rest' })
      : { preset: 'wave', from: 'rest', mix: 0.55 * raised, hand: { spread: 0.5 * raised + 0.1, curl: 0.12 + 0.3 * handDown } },
    armR: t >= T('s02b07') ? (knot > 0 ? { preset: 'belly', from: 'rest', mix: knot, offset: WD(0.35, 0.3).multiplyScalar(0.18 * knot).toArray(), hand: { curl: 0.55, cup: 0.6 } } : { preset: 'rest' })
      : { preset: 'rest', hand: { curl: 0.7, thumb: 0.85, cup: 0.5 } },
    extra: { hem: 0.5 * (1 - hemDown) * (t < T('s02b07') ? 1 : 0), motes: 1.1, rim: 1.05 },
  };
}

// ------------------------------------------------------------------------------------------------ JESUS acting
function jesusPose(t, st, J, JW, ue, vEyes, shot) {
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
      const fs = JX('surprised', { mOpen: 0.12, mRound: 0.4 });
      const fc = JX('compassion', { lidU: 1.0 });
      for (const kk in fs) f[kk] = lerp(f[kk], fs[kk], sur);
      for (const kk in fc) f[kk] = lerp(f[kk], fc[kk], down * (1 - sur * 0.5));
      f.mOpen = Math.max(f.mOpen, 0.16 * oh); f.mRound = Math.max(f.mRound, 0.6 * oh);
      P.face = f;
      P.gaze = uEyes;
      P.head = { look: uEyes, follow: lerp(0.2, 0.5, down), roll: 0.13 * sur + 0.05 * down, pitch: lerp(-0.2, 0, Math.max(sur, down)) };
      P.blinkAt = [t3 + 0.45, t4 + 0.6];
      const behindW = 1 - open;
      P.armL = { preset: [['behind', behindW], ['open', open]], hand: { cup: 0.35 } };
      P.armR = { preset: [['behind', behindW], ['open', open]], hand: { cup: 0.35 } };
      P.body = { lean: 0.05 * down, recoil: 0.06 * sur };
      return P;
    }
    // ---------------- JCU: "And he sees all of this." — user (12 f) -> phone (6 f) -> up to the Void, recognition
    // -> back to the user -> slow blink on "this" -> eyes open bright, a corner tucks up (an idea) -> small nod
    if (t < T('s02b07')) {
      const b = T('s02b06');
      const tPh = b + 0.42, tV = b + 0.66, tRec = b + 0.8, tBack = b + 1.0, tBl = T('s02b06+1.04'), tIdea = tBl + 0.42, tNod = tIdea + 0.3;
      let gaze = uEyes;
      if (t >= tPh && t < tV) gaze = phone || uEyes;
      else if (t >= tV && t < tBack) gaze = vEyes;
      const rec = bump(t, tRec - 0.05, tBl + 0.1, 0.4);
      const idea = smooth(clamp((t - tIdea) / 0.3));
      let f = JX('compassion', { lidU: 1.0, mSmile: 0.02 });
      const fr = { browOut: 0.55, browIn: 0.4, lidL: 0.42, mSmile: 0.3, mAsym: 0.32, lidU: 1.04 };
      for (const kk in fr) f[kk] = lerp(f[kk], fr[kk], rec);
      const fi = JX('warm', { lidU: 1.1, pupil: 1.18, mSmile: 0.38, mAsym: 0.38, browIn: 0.3, browOut: 0.35, wet: 0.3 });
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
    // ---------------- WIDE7: walks past the user, LEFT palm-down "one sec" + nod + small smile, on toward the Void
    const t7 = T('s02b07');
    const sec = bump(t, t7 - 0.02, t7 + 0.85, 0.32);
    const toUser = bump(t, t7 - 0.05, t7 + 0.95, 0.3);
    const lookP = toUser > 0.02 ? uEyes : vEyes;
    P.face = JX(toUser > 0.3 ? 'warm' : 'kind', { mSmile: 0.42 + 0.1 * toUser, lidL: 0.35 });
    P.gaze = lookP;
    P.head = { look: lookP, follow: 0.55 * toUser + 0.3 * (1 - toUser), pitch: 0.12 * bump(t, t7 + 0.18, t7 + 0.62, 0.45) };
    // "one sec": the palm on the user's side floats out palm-down toward the user's head height (pick the side the
    // user is actually on in his own frame)
    const onLeft = jesus.root.worldToLocal(uEyes.clone()).x > 0, side = onLeft ? 'L' : 'R';
    // the user sits right at his hip: a palm-down "stay there, one sec" held out to that side at chest height
    // (reads as a silhouette from behind), head turning to the user with a nod
    const sh = jesus.anchor('shoulder' + side);
    const sideW = V3(onLeft ? 1 : -1, 0, 0).transformDirection(jesus.root.matrixWorld), fwdW = V3(0, 0, 1).transformDirection(jesus.root.matrixWorld);
    const tgt = sh ? sh.clone().addScaledVector(sideW, 0.42).addScaledVector(fwdW, 0.12).add(V3(0, -0.22, 0)) : uEyes;
    const gest = sec > 0.01 ? { preset: 'stop', target: tgt.toArray(), reach: sec, palm: [0, -1, 0], fingers: sideW.clone().addScaledVector(fwdW, 0.3).normalize().toArray(), hand: { curl: 0.06, spread: 0.25, cup: 0.12 } } : { preset: 'rest' };
    P.armL = onLeft ? gest : { preset: 'rest' };
    P.armR = onLeft ? { preset: 'rest' } : gest;
    return P;
  };
  return { pre, full };
}

// ------------------------------------------------------------------------------------------------ USER acting
function userPose(t, st, UT, uPos, uYawL, sit, runAmt, scoot, scootPh, jEyes, vEyes, jesus) {
  const P = { pos: uPos, yaw: EDGE.Y(uYawL), walk: { amount: runAmt, style: 'run', phase: (t - UT.tR) * 1.2 + 0.1, flail: 0.8 },
    body: { sit, sitPath: 'fall', scoot, scootPhase: scootPh, pant: 1, hunch: 0.25 } };
  const t3 = T('s02b03');
  if (t < T('s02b04')) {
    // still looking back as they burst in -> head snaps forward -> a whole person, right there: SCREAM
    const lb = 0.7 * (1 - smooth(clamp((t - t3 - 0.02) / 0.09)));
    P.body = { ...P.body, lookBack: lb, recoil: 0.32 * smooth(clamp((t - t3 - 0.1) / 0.12)), shrug: 0.5 * smooth(clamp((t - t3 - 0.08) / 0.1)) };
    P.face = UX('scream', { mRound: 0.55, mWide: 0.4, mOpen: 0.9, lidU: 1.5, pupil: 0.3, talk: 0.6 });
    P.gaze = t > t3 + 0.04 ? jEyes : vEyes;
    // arms flung up; the phone pops in the LEFT hand (fumble) and is caught
    const fl = smooth(clamp((t - t3 - 0.08) / 0.12));
    const fum = bump(t, t3 + 0.16, t3 + 0.55, 0.4);
    P.armR = { preset: 'defend', reach: fl, hand: { curl: 0.05, spread: 1 } };
    P.armL = { preset: 'look', reach: fl, offset: [0, 0.16 * fum, 0], hand: { curl: 0.1 * (1 - fum), spread: 0.6 * fum } };
    P.extra = { phone: 0.85, tears: 0.8, phoneUp: 0 };
    P.walk.flail = 1;
    return P;
  }
  const t4 = T('s02b04');
  if (t < T('s02b05')) {
    // the skid (eyes wide, O mouth, phone held up high) -> THUD (face compresses, glasses jump) -> frantic twist round
    // -> scoot, scoot, bump -> RIGHT hand shoots up, palm out at the Void; LEFT clutches the phone
    const def = smooth(clamp((t - UT.tSc1 + 0.05) / 0.16));
    P.face = k(t, [[t4, UX('gasp', { lidU: 1.5, pupil: 0.35 })], [UT.tImpact - 0.02, UX('gasp', { lidU: 1.5, pupil: 0.35, mOpen: 0.8 })],
      [UT.tImpact + 0.04, UX('scrunch', { mOpen: 0.3 }), 'out'], [UT.tImpact + 0.16, UX('scrunch', { mOpen: 0.3 })],
      [UT.tTw0, UX('terror', { lidU: 1.45 }), 'out'], [UT.tSc1, UX('terror', { lidU: 1.5, pupil: 0.36, lidL: 0.3 })]]);
    P.gaze = t > UT.tTw0 + 0.12 ? vEyes : jEyes;
    P.body = { ...P.body, shrug: 0.25 + 0.35 * def, tremble: 0.5 * def, recoil: 0.1 * def };
    P.armR = def > 0 ? { preset: 'defend', reach: def, tremble: 1, hand: { spread: 1, splay: 1, curl: 0 } } : { preset: 'rest' };
    P.armL = def > 0 ? { preset: 'clutch', reach: def } : { preset: 'hold' };
    P.extra = { phone: 0.85, tears: 0.7 };
    if (t > UT.tSc1 - 0.05) P.blinkAt = [];
    return P;
  }
  // seated at U from here: hand up, trembling, phone clutched
  const P2_ = { ...P, body: { sit: 1, shrug: 0.6, tremble: 0.55, pant: 1, hunch: 0.25, recoil: 0.12 }, walk: { amount: 0 } };
  P2_.extra = { phone: 0.85, tears: 0.6 };
  P2_.armL = { preset: 'clutch' };
  P2_.armR = { preset: 'defend', tremble: 1, hand: { spread: 1, splay: 1, curl: 0 } };
  P2_.face = UX('terror', { lidU: 1.42, pupil: 0.38, lidL: 0.32, mOpen: 0.32 });
  P2_.gaze = vEyes;
  if (t >= T('s02b07')) {
    // eyes follow Jesus as he passes (head follows slower); the raised hand bends at the wrist in confusion;
    // the mouth closes ... then falls open as it dawns where he is going
    const t7 = T('s02b07');
    const jp = jEyes || vEyes;
    const bend = smooth(clamp((t - t7 - 0.45) / 0.4));
    const close = bump(t, t7 + 0.55, t7 + 1.2, 0.4), fall = smooth(clamp((t - t7 - 1.05) / 0.3));
    P2_.gaze = jp;
    P2_.head = { look: jp, follow: 0.45 * smooth(clamp((t - t7 - 0.12) / 0.5)) };
    P2_.armR = { preset: 'defend', tremble: 0.5, hand: { spread: 0.7, splay: 0.6, curl: 0.42 * bend }, fingers: null };
    const f = UX('disbelief', { mOpen: lerp(0.3, 0.02, close) + 0.32 * fall, lidU: 1.1 + 0.25 * fall, browIn: 0.6 + 0.3 * fall, browOut: 0.3 + 0.3 * fall });
    P2_.face = f;
    P2_.blinkAt = [t7 + 0.98];
  }
  return P2_;
}

// ------------------------------------------------------------------------------------------------ camera fits
// Static reference poses (user seated at U with the right hand up, Jesus at J1, the Void at V) -> fitted cameras
// whose subjects land on the staging plan's screen heights. Done once in setup (pure, deterministic).
function fitShots(st) {
  const { set, user, vd, jesus } = st;
  const Uw = G(set, M.U.p[0], M.U.p[2]), Jw = G(set, M.J1.p[0], M.J1.p[2]), Vw = G(set, M.V.p[0], M.V.p[2]);
  user.update(0, { pos: Uw, yaw: EDGE.Y(M.U.yaw), body: { sit: 1, shrug: 0.6 }, armR: { preset: 'defend' }, armL: { preset: 'clutch' } });
  jesus.update(0, { pos: Jw, yaw: EDGE.Y(M.J1.yaw - 0.72) });
  vd.update(0, { pos: Vw, yaw: EDGE.Y(M.V.yaw) });
  const ue = user.anchor('eyes'), uh = user.anchor('handR'), je = jesus.anchor('eyes'), ve = vd.anchor('eyes');
  const LW = (x, y, z) => EDGE.W(x, y, z);
  // ARRIVE: low side two-shot perpendicular to the J1 <-> USKID line: Jesus frame-left (3/4 profile, cheated), the user
  // bursts in from frame-right in profile; the rose-gold tree and the sun both stay out of frame (no halo)
  {
    const J = P2(M.J1), K = [M.USKID.p[0], M.USKID.p[2]], mid = [(J[0] + K[0]) / 2, (J[1] + K[1]) / 2];
    const az = 0.84, dc = [Math.sin(az), Math.cos(az)], toJ = [J[0] - mid[0], J[1] - mid[1]];   // tree + sun out of frame
    st.camARR = { pos: LW(mid[0] + dc[0] * 5.2, 0.66, mid[1] + dc[1] * 5.2), look: LW(mid[0] + 0.42 * toJ[0], 1.06, mid[1] + 0.42 * toJ[1]), err: 0 };
  }
  // REV: from just behind the user's raised right hand up to the Void (hand soft in the foreground ~y 700, eyes ~y 270)
  {
    const yw = EDGE.Y(M.U.yaw), back = V3(-Math.sin(yw), 0, -Math.cos(yw)), right = V3(-Math.cos(yw), 0, Math.sin(yw));
    const g = ue.clone().addScaledVector(back, 0.7).addScaledVector(right, 0.3).add(V3(0, -0.08, 0));
    const f = fitCam([[ve, 390, 285, 1], [uh, 285, 725, 0.6]], 50, g.toArray(), ve.toArray(), { reg: 0.3, yMin: ue.y - 0.25, yMax: ue.y + 0.05 });
    st.camREV = f; console.log(`s02 REV fit ${f.err.toFixed(1)}px`);
  }
  // WIDE7: medium wide at the seated user's eye height; user lower-left foreground, the Void upper-middle
  {
    const g = LW(-2.45, 0.98, 4.85);
    const f = fitCam([[ve, 470, 250, 1], [ue, 165, 660, 1]], 44, g, ve.toArray(), { reg: 0.08, yMin: 0.85, yMax: 1.15 });
    st.camW7 = f; console.log(`s02 WIDE7 fit ${f.err.toFixed(1)}px local ${EDGE.L(f.pos).map((v) => v.toFixed(2))}`);
  }
}
