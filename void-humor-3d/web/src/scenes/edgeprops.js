// Shared EDGE props + helpers written for s03 / s04 (usable by every Part One scene). Not a scene module (the registry
// only loads sNN.js). Everything is a pure function of t (no state carried between frames).
//
//   await loadWords();  wordT('s03b01', 'void')        absolute time of a spoken word (data/lines.json Whisper times,
//                                                       beat-relative, so re-timed audio re-times the picture)
//   const lg = makeLittleGalaxy(); scene.add(lg.group); lg.update(t, { from })
//       the little "dinner-plate" spiral galaxy coughed up in s04b10: flies out of the Void's mouth, bounces at stage
//       (0.4, ., -0.2), rolls like a coin to the user's sneaker, wobbles like a spun coin, lies flat twinkling there
//       until the user stands up in s14b01 (drop it after s14). littleGalaxyAt(t) gives its state.
//   drawSkyGalaxy(particles, t)   the big laughed-up sky galaxy (marks.js galaxyAt / galaxySpin) as the agreed sprite
//   scopeVisible(obj, a, b)       make a prop added to the SHARED set scene render only while CTX.t is in [a, b)
//                                 (so it never leaks into a neighbouring scene's frames)
import * as THREE from 'three';
import { T, TL } from '../core/timeline.js';
import { CTX } from '../core/context.js';
import { clamp, lerp, smooth, ease, rng } from '../core/util.js';
import { CELL } from '../core/particles.js';
import { EDGE, galaxyAt, galaxySpin } from './marks.js';

export const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
export const toV = (p) => (p && p.isVector3 ? p.clone() : Array.isArray(p) ? new THREE.Vector3(p[0], p[1], p[2]) : new THREE.Vector3());

// ------------------------------------------------------------------------------------------------ word times
let WORDS = null;
export async function loadWords() {
  if (WORDS) return WORDS;
  try { const r = await fetch('/data/lines.json'); WORDS = r.ok ? await r.json() : {}; } catch (e) { WORDS = {}; }
  return WORDS;
}
const norm = (w) => String(w).toLowerCase().replace(/[^a-z']/g, '');
/** absolute time of the n-th `word` in line `beat`; `fb` = fallback offset (s from the beat start). */
export function wordT(beat, word, fb = 0, { which = 'start', n = 0 } = {}) {
  const b = TL.data.beats[beat];
  const L = WORDS && WORDS[beat];
  if (L && L.words) {
    let c = 0;
    for (const w of L.words) if (norm(w.w) === norm(word)) { if (c++ === n) return b.start + (which === 'end' ? w.end : w.start); }
  }
  return b.start + fb;
}

// ------------------------------------------------------------------------------------------------ envelopes
/** 0 -> 1 (rise `up` s) -> hold -> 0 (fall `down` s), starting at absolute time a. */
export function pulse(t, a, up = 0.1, hold = 0, down = 0.2) {
  if (t <= a) return 0;
  if (t < a + up) return smooth((t - a) / up);
  if (t < a + up + hold) return 1;
  if (t < a + up + hold + down) return 1 - smooth((t - a - up - hold) / down);
  return 0;
}
export const ramp = (t, a, b, e = 'inOut') => (b <= a ? (t >= b ? 1 : 0) : ease[e](clamp((t - a) / (b - a))));
/** damped wobble after a (0 before). */
export const wobble = (t, a, freq = 2.2, decay = 4) => (t <= a ? 0 : Math.sin((t - a) * freq * Math.PI * 2) * Math.exp(-(t - a) * decay));
/** saccade-style gaze switching: keys [[timeRef, target | () => target, dur?]] -> Vector3 (eases over dur, ~2 frames). */
export function gazeSched(t, keys) {
  const res = (g) => toV(typeof g === 'function' ? g() : g);
  let i = 0;
  for (let j = 0; j < keys.length; j++) if (T(keys[j][0]) <= t) i = j;
  const d = keys[i][2] ?? 0.09;
  if (i === 0) return res(keys[0][1]);
  const u = smooth((t - T(keys[i][0])) / d);
  if (u >= 1) return res(keys[i][1]);
  return res(keys[i - 1][1]).lerp(res(keys[i][1]), u);
}

// ------------------------------------------------------------------------------------------------ scoping
/** Make `obj` visible only while CTX.t is in [T(a), T(b)) (props added to a set scene that other scenes share). */
export function scopeVisible(obj, a, b, extra = () => true) {
  let own = true;
  Object.defineProperty(obj, 'visible', {
    configurable: true,
    get() { const t = CTX.t; return own && t >= T(a) && t < T(b) && extra(t); },
    set(v) { own = !!v; },
  });
  return obj;
}

/** The inverse: hide `obj` (a set prop shared by every scene) only while CTX.t is in [T(a), T(b)) — a per-shot cheat. */
export function hideDuring(obj, a, b) {
  if (!obj) return obj;
  const prev = Object.getOwnPropertyDescriptor(obj, 'visible');
  let own = prev && prev.get ? null : obj.visible;
  const wins = (obj.__hideWins = obj.__hideWins || []);
  if (!wins.some((w) => w[0] === a && w[1] === b)) wins.push([a, b]);
  if (!obj.__hideInstalled) {
    obj.__hideInstalled = true;
    Object.defineProperty(obj, 'visible', {
      configurable: true,
      get() { const t = CTX.t; return own !== false && !obj.__hideWins.some(([x, y]) => t >= T(x) && t < T(y)); },
      set(v) { own = !!v; },
    });
  }
  return obj;
}

// ------------------------------------------------------------------------------------------------ the Void's surface
/** world point on the Void's velvet body at rest-height y and angle ang (0 = its front, +PI/2 = its LEFT), pushed out `out` m. */
export function voidSurface(vd, y, ang, out = 0) {
  const r = vd.rAt(y) + out;
  const p = vd._xf(y, r * Math.sin(ang), 0, r * 0.9 * Math.cos(ang));     // body depth = 0.9 x width (void.js SZ)
  return vd.root.localToWorld(p);
}
/** outward surface normal (world) at that point (ellipse normal in the body frame). */
export function voidNormal(vd, y, ang) {
  const d = vd._xd(y, [Math.sin(ang) / 1, 0, Math.cos(ang) / 0.9]);
  return d.transformDirection(vd.root.matrixWorld).normalize();
}

// ------------------------------------------------------------------------------------------------ Jesus beside the Void
// s03/s04: Jesus stands JOUT further out from the Void than the JV mark (at JV his shoulder touches its velvet: no room
// for the arm around it or the whisper; STAGING §8). s04b13 (him offscreen) slides him back onto JV for s05.
export const JOUT = 0.28;
export const JV_OUT = (() => { const J = EDGE.M.JV.p, V = EDGE.M.V.p, d = [J[0] - V[0], J[2] - V[2]], n = Math.hypot(d[0], d[1]); return [J[0] + d[0] / n * JOUT, 0, J[2] + d[1] / n * JOUT]; })();
/** arm-around contact height (world): below his shoulder, on the velvet of the Void's right flank */
export const AROUND_H = 1.3;
/**
 * Jesus's LEFT palm on the Void's right flank: world height h, swept round toward its back, ~reachM from his
 * shoulder (palm on the velvet just round the curve). -> { p, a, n (outward normal), tb (tangent toward its back) }.
 * Call after both rigs were updated for this frame (reads the live surface + his shoulder).
 */
export function aroundContact(vd, jesus, h = AROUND_H, reachM = 0.45, aPref = -1.1) {
  const sh = jesus.anchor('shoulderL');
  let best = null, bd = 1e9;
  for (let a = -1.5; a <= -0.7; a += 0.025) {
    const p = voidSurface(vd, h, a, 0.012);
    const d = Math.abs(p.distanceTo(sh) - reachM) + 0.3 * Math.abs(a - aPref);
    if (d < bd) { bd = d; best = [p, a]; }
  }
  const a = best[1], n = voidNormal(vd, h, a);
  const tb = voidSurface(vd, h, a - 0.05, 0).sub(voidSurface(vd, h, a + 0.05, 0)).normalize();
  return { p: best[0], a, n, tb };
}
/** the `armL` pose for the arm around the Void: upper arm level out to his side, forearm round its curve. lift (m) / tap */
export function aroundArm(c, reach = 1, lift = 0) {
  const a = EDGE.W(1, 0, 0.35), o = EDGE.W(0, 0, 0);
  const pole = new THREE.Vector3(a[0] - o[0], -0.15 * Math.hypot(1, 0.35), a[2] - o[2]).normalize();   // stage-fixed: no elbow flips
  const tgt = c.p.clone().addScaledVector(c.n, 0.66 * lift).add(new THREE.Vector3(0, lift, 0));
  const fing = c.tb.clone().add(new THREE.Vector3(0, -0.25, 0)).addScaledVector(c.n, -0.1).normalize();
  return { preset: 'around', target: tgt, normal: c.n.toArray(), pole: pole.toArray(), fingers: fing.toArray(), reach, hand: { curl: 0.25, spread: 0.18, cup: 0.35, thumb: 0.4 } };
}

// ------------------------------------------------------------------------------------------------ set seeds
/**
 * Fade the EDGE set's drifting thought seeds that would sit on a face in this shot (call AFTER set.update() and
 * AFTER the camera is applied). pts: [[worldPoint, radiusPx], ...]. Pure: depends only on this frame's seeds + camera.
 */
export function fadeSeedsNear(set, camera, pts) {
  const S = set && set.props && set.props.seeds;
  if (!S || !S.geo || !pts.length) return;
  camera.updateMatrixWorld(); camera.updateProjectionMatrix();
  const v = new THREE.Vector3(), P = pts.map(([p, r]) => { v.copy(toV(p)).project(camera); return [(v.x * 0.5 + 0.5) * 720, (1 - (v.y * 0.5 + 0.5)) * 1280, r, v.z]; });
  const n = S.geo.instanceCount, A = S.aPos.array, Mi = S.aMisc.array;
  for (let i = 0; i < n; i++) {
    v.set(A[i * 3], A[i * 3 + 1], A[i * 3 + 2]).project(camera);
    if (v.z > 1) continue;
    const x = (v.x * 0.5 + 0.5) * 720, y = (1 - (v.y * 0.5 + 0.5)) * 1280;
    let f = 1;
    for (const [px, py, r] of P) { const d = Math.hypot(x - px, y - py); f = Math.min(f, smooth((d - r * 0.6) / (r * 0.4))); }
    if (f < 1) Mi[i * 3 + 2] *= f;
  }
  S.aMisc.needsUpdate = true;
}

/**
 * Same for the set's golden motes (core Particles): fade any that sit on a face, or that drift within `near` m of the
 * lens (they would bloom into a big blurry orb). Call AFTER set.update() and after the camera is applied.
 */
export function fadeMotesNear(set, camera, pts = [], near = 2.2) {
  const S = set && set.props && set.props.motes;
  if (!S || !S.geo) return;
  camera.updateMatrixWorld(); camera.updateProjectionMatrix();
  const v = new THREE.Vector3(), cp = camera.position;
  const P = pts.map(([p, r]) => { v.copy(toV(p)).project(camera); return [(v.x * 0.5 + 0.5) * 720, (1 - (v.y * 0.5 + 0.5)) * 1280, r]; });
  const n = S.geo.instanceCount, A = S.aPos.array, C = S.aCol.array;
  for (let i = 0; i < n; i++) {
    v.set(A[i * 3], A[i * 3 + 1], A[i * 3 + 2]);
    let f = smooth((v.distanceTo(cp) - near * 0.6) / (near * 0.4));
    v.project(camera);
    if (v.z <= 1) {
      const x = (v.x * 0.5 + 0.5) * 720, y = (1 - (v.y * 0.5 + 0.5)) * 1280;
      for (const [px, py, r] of P) f = Math.min(f, smooth((Math.hypot(x - px, y - py) - r * 0.6) / (r * 0.4)));
    }
    if (f < 1) C[i * 4 + 3] *= f;
  }
  S.aCol.needsUpdate = true;
}

// ------------------------------------------------------------------------------------------------ sky galaxy
/** the big sky galaxy sprite (from s04b11.end on), exactly as agreed in marks.js: size 1.1, 0xd8c0ff, alpha 0.9. */
export function drawSkyGalaxy(ps, t) {
  const p = galaxyAt(t);
  if (p) ps.add(p, EDGE.GALAXY.size, 0xd8c0ff, 0.9, galaxySpin(t), CELL.galaxy);
  return p;
}

// ------------------------------------------------------------------------------------------------ little galaxy
const R_LG = 0.15;                                     // "dinner plate": 0.3 m across
// stage-local key points (EDGE frame)
export const LITTLE_GALAXY = {
  bounce: [0.4, 0, -0.2],                              // first (and only) bounce on the grass
  hop: [0.18, 0, 0.02],                                // lands on its edge after the hop and starts rolling
  rest: [-0.7, 0, 1.0],                                // lies flat against the user's right sneaker (seated at U)
  fromDefault: [0.62, 1.7, -0.62],                     // the Void's mouth at the cough (s04 passes the real one)
  radius: R_LG,
};
const LG = LITTLE_GALAXY;
const tPop = () => T('s04b10') + 0.39;                 // the big hiccup in the s04b10 cough audio, on "galaxies"
const tBounce = () => tPop() + 0.34;
const tHop = () => tBounce() + 0.3;
// it rolls at a steady pace (seen small in the s04b11 wide, rolling toward the user), and the last ~0.35 m happen in
// the first 0.75 s of s04b13: it rolls into that shot from frame-right, decelerates, spirals to a stop at the sneaker
const tStop = () => T('s04b13') + 0.75;
const tFlat = () => tStop() + 0.62;
const DECEL = 0.45;                                    // s of deceleration before the wobble

// the roll path (stage x,z): a lazy loop out to the user's left, then straight down their facing axis into the sneaker
const ROLL = [[0.18, 0.02], [-0.62, -0.42], [-0.22, 0.42], [-0.7, 1.0]];
function cub(u) { const v = 1 - u, a = v * v * v, b = 3 * v * v * u, c = 3 * v * u * u, d = u * u * u; return [a * ROLL[0][0] + b * ROLL[1][0] + c * ROLL[2][0] + d * ROLL[3][0], 0, a * ROLL[0][1] + b * ROLL[1][1] + c * ROLL[2][1] + d * ROLL[3][1]]; }
const bez = (a, c, b, u) => cub(u);                    // (kept signature)
let _rollTab = null;
function rollTab() {
  if (_rollTab) return _rollTab;
  const N = 96, cum = [0]; let p = cub(0);
  for (let i = 1; i <= N; i++) { const q = cub(i / N); cum.push(cum[i - 1] + Math.hypot(q[0] - p[0], q[2] - p[2])); p = q; }
  return (_rollTab = { N, cum, L: cum[N] });
}
function rollLen() { return rollTab().L; }
/** path parameter for arc length s */
function rollU(s) {
  const { N, cum } = rollTab();
  if (s <= 0) return 0; if (s >= cum[N]) return 1;
  let i = 1; while (i < N && cum[i] < s) i++;
  return (i - 1 + (s - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1])) / N;
}
/** arc length rolled at t (steady speed, then a linear deceleration over DECEL s into tStop) */
function rollS(t) {
  const L = rollLen(), D = tStop() - tHop(), v = L / (D - DECEL / 2);
  const tt = clamp(t - tHop(), 0, D), td = D - DECEL;
  if (tt <= td) return v * tt;
  const d = tt - td;
  return v * td + v * (d - d * d / (2 * DECEL));
}

/**
 * State of the little galaxy at t: null (not born / gone) or { pos: Vector3 (world centre), quat, scale, alpha, phase }.
 * opts.from: world launch point (the Void's mouth at tPop) for the flight; default LITTLE_GALAXY.fromDefault.
 */
export function littleGalaxyAt(t, opts = {}) {
  const t0 = tPop();
  if (t < t0 || t >= T('s14.end')) return null;
  const up = V3(0, 1, 0);
  let c, N, spin = 0, scale = 1, alpha = 1, phase = 'flat';
  const W = (p) => V3(...EDGE.W(p));
  if (t < tBounce()) {                                  // flight out of the mouth, tumbling
    phase = 'fly';
    const u = (t - t0) / (tBounce() - t0);
    const a = opts.from ? toV(opts.from) : W(LG.fromDefault), b = W(LG.bounce).setY(R_LG * 0.7);
    c = a.clone().lerp(b, u); c.y = lerp(a.y, b.y, u) + 0.35 * Math.sin(Math.PI * u) * (1 - u);
    const ang = 7.5 * (t - t0);
    N = V3(Math.cos(ang), 0.6, Math.sin(ang)).normalize();
    spin = 9 * (t - t0);
    scale = 0.35 + 0.65 * smooth((t - t0) / 0.1);
  } else if (t < tHop()) {                              // hop after the bounce, still tumbling a little
    phase = 'hop';
    const u = (t - tBounce()) / (tHop() - tBounce());
    const a = W(LG.bounce), b = W(LG.hop);
    c = a.clone().lerp(b, u); c.y = R_LG * lerp(0.7, 1, u) + 0.16 * Math.sin(Math.PI * u);
    const d = b.clone().sub(a).setY(0).normalize();
    const axle = V3().crossVectors(up, d).normalize();
    const tumble = (1 - u) * 1.3;
    N = axle.clone().applyAxisAngle(d, tumble).normalize();
    spin = 9 * (tBounce() - t0) + 6 * (t - tBounce());
  } else {
    // rolling on its edge (steady, then decelerating) -> coin wobble (Euler's disk) -> flat
    const L = rollLen(), dur = tStop() - tHop();
    const ur = clamp((t - tHop()) / dur);
    const s = rollS(t);
    const uu = rollU(s);
    const p = cub(uu);
    const pw = W(p), dw = W(cub(Math.min(1, uu + 0.01))).sub(W(cub(Math.max(0, uu - 0.01)))).setY(0);
    if (dw.lengthSq() < 1e-9) dw.copy(W(ROLL[3]).sub(W(ROLL[2]))).setY(0);
    dw.normalize();
    const axle = V3().crossVectors(up, dw).normalize();
    const rollSpin = 9 * (tBounce() - t0) + 6 * (tHop() - tBounce()) + s / R_LG;
    if (t < tStop()) {
      phase = 'roll';
      const slow = clamp((t - (tStop() - DECEL)) / DECEL);
      const lean = 0.1 + 0.3 * slow * slow;              // leans more as it slows: it starts to curl in
      N = axle.clone().applyAxisAngle(dw, -lean).normalize();
      c = pw.clone().setY(R_LG * Math.cos(lean));
      spin = rollSpin;
    } else {
      // Euler's disk: tilt from the roll lean to flat, precessing faster and faster; centre stays put
      const uw = clamp((t - tStop()) / (tFlat() - tStop()));
      const lean0 = 0.4;
      const beta = lean0 + (Math.PI / 2 - lean0) * Math.pow(uw, 1.6);   // angle of the disc normal away from horizontal
      const phi0 = Math.atan2(axle.z, axle.x);
      const phi = phi0 - (2.6 * Math.PI) * Math.pow(uw, 1.35);           // precession of the normal's azimuth
      const horiz = Math.cos(beta);
      N = V3(horiz * Math.cos(phi), Math.sin(beta), horiz * Math.sin(phi)).normalize();
      if (uw >= 1) N.set(0, 1, 0);
      c = pw.clone().setY(Math.max(0.012, R_LG * Math.cos(beta)) + 0.004);
      spin = rollSpin + 1.2 * (t - tStop());
      phase = uw >= 1 ? 'flat' : 'wobble';
      if (uw >= 1) spin = rollSpin + 1.2 * (tFlat() - tStop()) + 0.22 * (t - tFlat());   // slow turning while it lies there
      alpha = 0.92 + 0.08 * Math.sin(t * 2.1);
    }
  }
  const q = new THREE.Quaternion().setFromUnitVectors(V3(0, 0, 1), N);
  q.multiply(new THREE.Quaternion().setFromAxisAngle(V3(0, 0, 1), spin));
  return { pos: c, quat: q, scale, alpha, phase, normal: N };
}

let _lgTex = null;
function lgTexture() {
  if (_lgTex) return _lgTex;
  const S = 256, cv = document.createElement('canvas'); cv.width = cv.height = S;
  const g = cv.getContext('2d'); g.translate(S / 2, S / 2);
  const rad = (r0, stops) => { const gr = g.createRadialGradient(0, 0, 0, 0, 0, r0); stops.forEach(([o, c]) => gr.addColorStop(o, c)); return gr; };
  g.fillStyle = rad(128, [[0, 'rgba(255,236,190,0.95)'], [0.12, 'rgba(255,200,150,0.75)'], [0.35, 'rgba(170,120,255,0.32)'], [0.75, 'rgba(110,80,220,0.10)'], [1, 'rgba(80,60,200,0)']]);
  g.beginPath(); g.arc(0, 0, 128, 0, 7); g.fill();
  g.lineCap = 'round';
  for (let arm = 0; arm < 2; arm++) {
    for (let pass = 0; pass < 2; pass++) {
      g.beginPath();
      for (let k = 0; k < 90; k++) { const a = arm * Math.PI + k * 0.075, r = 8 + k * 1.25; const x = Math.cos(a) * r, y = Math.sin(a) * r; k ? g.lineTo(x, y) : g.moveTo(x, y); }
      g.strokeStyle = pass ? 'rgba(255,225,170,0.85)' : 'rgba(190,150,255,0.45)';
      g.lineWidth = pass ? 5 : 16; g.stroke();
    }
  }
  const r = rng(424242);
  for (let i = 0; i < 70; i++) {
    const a = r() * 6.283, d = 14 + r() * 100, arm = Math.floor(r() * 2);
    const aa = arm * Math.PI + (d - 8) / 1.25 * 0.075 + (r() - 0.5) * 0.5;
    const x = Math.cos(i < 50 ? aa : a) * d, y = Math.sin(i < 50 ? aa : a) * d, s = 0.8 + r() * 2.2;
    g.fillStyle = r() < 0.5 ? 'rgba(255,255,255,0.9)' : 'rgba(200,230,255,0.8)';
    g.beginPath(); g.arc(x, y, s, 0, 7); g.fill();
  }
  g.fillStyle = rad(16, [[0, 'rgba(255,255,240,1)'], [1, 'rgba(255,230,180,0)']]); g.beginPath(); g.arc(0, 0, 16, 0, 7); g.fill();
  _lgTex = new THREE.CanvasTexture(cv); _lgTex.colorSpace = THREE.SRGBColorSpace;
  return _lgTex;
}
let _glowTex = null;
function glowTex() {
  if (_glowTex) return _glowTex;
  const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  _glowTex = new THREE.CanvasTexture(c); return _glowTex;
}

/** The little galaxy prop: { group, update(t, opts) -> state }. Add group to the set scene (it scopes itself to [s04, s14.end)). */
export function makeLittleGalaxy() {
  const group = new THREE.Group(); group.name = 'littleGalaxy';
  const disc = new THREE.Mesh(new THREE.CircleGeometry(R_LG, 40), new THREE.MeshBasicMaterial({
    map: lgTexture(), transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending,
    color: new THREE.Color(1.7, 1.55, 1.9) }));
  disc.renderOrder = 6;
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex(), color: new THREE.Color(0.75, 0.6, 1.0), transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false }));
  halo.scale.setScalar(0.62); halo.renderOrder = 6;
  group.add(disc, halo);
  scopeVisible(group, 's04', 's14.end');
  const api = {
    group, disc, halo, from: null,
    update(t, opts = {}) {
      const s = littleGalaxyAt(t, opts);
      if (!s) { disc.material.opacity = 0; halo.material.opacity = 0; group.position.set(0, -50, 0); return null; }
      group.position.set(0, 0, 0);
      disc.position.copy(s.pos); disc.quaternion.copy(s.quat); disc.scale.setScalar(s.scale);
      disc.material.opacity = s.alpha * (opts.alpha ?? 1);
      halo.position.copy(s.pos).add(V3(0, 0.02, 0)); halo.scale.setScalar(0.62 * s.scale);
      halo.material.opacity = 0.3 * s.alpha * (opts.alpha ?? 1);
      return s;
    },
  };
  // self-updating from the frame time (CTX.t) every time it is rendered, so any scene that shares the set shows it in
  // the right state without calling update() (pure: the state is a function of t only)
  const base = THREE.Object3D.prototype.updateMatrixWorld;
  group.updateMatrixWorld = function (force) { api.update(CTX.t, { from: api.from }); return base.call(this, force); };
  return api;
}

/**
 * The shared little galaxy of a set (created once per set, added to set.scene): every Part One scene from s04 to s14
 * can call ensureLittleGalaxy(set) in setup() and it appears at the user's sneaker by itself (no per-frame call needed).
 */
export function ensureLittleGalaxy(set) {
  if (!set.__littleGalaxy) { set.__littleGalaxy = makeLittleGalaxy(); set.scene.add(set.__littleGalaxy.group); }
  return set.__littleGalaxy;
}

// ------------------------------------------------------------------------------------------------ camera fitter
/**
 * fitShot(pts, fov, pos0, look0, opts) -> { pos, look, fov, drift, err }: a camera (vertical fov) that puts world
 * points on target pixels. pts: [[Vector3|[x,y,z], px, py, weight?]]. Deterministic coordinate descent; pos is pulled
 * toward pos0 (posReg) and kept within [yMin, yMax]. Run it in setup() on reference anchors (never per frame).
 */
export function fitShot(pts, fov, pos0, look0, { posReg = 0.02, yMin = -99, yMax = 99, drift = 0.2 } = {}) {
  const cam = new THREE.PerspectiveCamera(fov, 720 / 1280, 0.05, 400);
  const P = [...toV(pos0).toArray(), ...toV(look0).toArray()];
  const PT = pts.map(([w, x, y, wt]) => [toV(w), x, y, wt ?? 1]);
  const p0 = toV(pos0);
  const v = new THREE.Vector3();
  const cost = (q) => {
    cam.position.set(q[0], q[1], q[2]); cam.up.set(0, 1, 0); cam.lookAt(q[3], q[4], q[5]); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
    let e = 0;
    for (const [w, x, y, wt] of PT) {
      v.copy(w).project(cam);
      if (v.z > 1) { e += 1e7; continue; }
      e += wt * (((v.x * 0.5 + 0.5) * 720 - x) ** 2 + ((1 - (v.y * 0.5 + 0.5)) * 1280 - y) ** 2);
    }
    e += posReg * 1e4 * ((q[0] - p0.x) ** 2 + (q[1] - p0.y) ** 2 + (q[2] - p0.z) ** 2);
    if (q[1] < yMin) e += 1e7 * (yMin - q[1]) ** 2;
    if (q[1] > yMax) e += 1e7 * (q[1] - yMax) ** 2;
    return e;
  };
  let best = cost(P), step = 0.4;
  for (let it = 0; it < 500 && step > 0.001; it++) {
    let improved = false;
    for (let i = 0; i < 6; i++) for (const d of [step, -step]) {
      const q = P.slice(); q[i] += d; const c = cost(q);
      if (c < best) { best = c; P.splice(0, 6, ...q); improved = true; }
    }
    if (!improved) step *= 0.6;
  }
  return { pos: P.slice(0, 3), look: P.slice(3, 6), fov, drift, err: Math.sqrt(best / Math.max(1, PT.length)) };
}

// ------------------------------------------------------------------------------------------------ face blending
/** lerp two flat face-param objects (numbers blend; others switch at w = 0.5) */
export function fmix(a, b, w) {
  if (w <= 0) return a; if (w >= 1) return b;
  const o = { ...a };
  for (const kk in b) o[kk] = (typeof a[kk] === 'number' && typeof b[kk] === 'number') ? a[kk] + (b[kk] - a[kk]) * w : (w < 0.5 ? (a[kk] ?? b[kk]) : b[kk]);
  return o;
}
/**
 * faceSeq(t, [[tStart, () => face, xfade?], ...]): the face of the current segment, cross-faded from the previous
 * segment over `xfade` s (default 0.22) after each boundary (eased), so expression changes never pop. xfade 0 = a cut.
 */
export function faceSeq(t, segs) {
  let i = 0;
  for (let j = 0; j < segs.length; j++) if (t >= T(segs[j][0])) i = j;
  const cur = segs[i][1]();
  if (i === 0) return cur;
  const xf = segs[i][2] ?? 0.22;
  const u = xf > 0 ? smooth((t - T(segs[i][0])) / xf) : 1;
  return u >= 1 ? cur : fmix(segs[i - 1][1](), cur, u);
}
