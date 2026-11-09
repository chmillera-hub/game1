// Shared helpers for the bonus scenes s17 / s18 / s19 (MIND_BACKROOM). Not a scene module (the registry only loads
// sNN.js). Everything here is a pure function of its inputs (no state that depends on render order).
//
//   wordT('s18b03', 'dagger')       -> absolute time of a spoken word (data/lines.json, beat-relative)
//   pulse / ramp / wobble / gazeSched / fitShot / mixShot / logDolly
//   ownedGroup(st)                  -> a Group that is only visible on frames rendered by the scene owning `st`
//   cast(app, scene, names)         -> (re)attach exactly these characters to `scene`
//   bonusMarks(set)                 -> world marks / yaws of the backroom (after ROOM.fit)
//   voidBowed(t, B, over)           -> the Void's resting pose for the bonus (bowed toward Fear, beside the cage)
//   bonusDecals(set)                -> the magician's GREY FOOTPRINTS + the numbing-dust patch (s18b03 / s18b07).
//                                      Persistent floor evidence: visible from the moment each lands until the
//                                      cosmos takes the floor in s22. s20-s22 should call `bonusDecals(set, mag)`
//                                      in their setup() (idempotent) so the prints stay on the floor in their frames.
import * as THREE from 'three';
import { T, TL } from '../core/timeline.js';
import { CTX } from '../core/context.js';
import { clamp, smooth, lerp, ease } from '../core/util.js';
import { ROOM } from './marks.js';
import { VX } from '../chars/void.js';

export const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
export const toV = (p) => (p && p.isVector3 ? p.clone() : Array.isArray(p) ? new THREE.Vector3(p[0], p[1], p[2]) : new THREE.Vector3());

// ------------------------------------------------------------------------------------------------ word times
let WORDS = null;
export async function loadWords() {
  if (WORDS) return WORDS;
  try { const r = await fetch('/data/lines.json'); WORDS = r.ok ? await r.json() : {}; } catch (e) { WORDS = {}; }
  return WORDS;
}
const norm = (w) => String(w).toLowerCase().replace(/[^a-z']/g, '');
/** absolute time of `word` (n-th occurrence) in line `beat`; falls back to a fraction of the beat. */
export function wordT(beat, word, { which = 'start', n = 0, fallback = 0.5, off = 0 } = {}) {
  const b = TL.data.beats[beat];
  const L = WORDS && WORDS[beat];
  if (L && L.words) {
    let c = 0;
    for (const w of L.words) if (norm(w.w) === norm(word)) { if (c++ === n) return b.start + (which === 'end' ? w.end : w.start) + off; }
  }
  return b.start + (b.end - b.start) * fallback + off;
}

// ------------------------------------------------------------------------------------------------ envelopes
/** 0 -> 1 (up s) -> hold -> 0 (down s), starting at absolute time a. */
export function pulse(t, a, up = 0.1, hold = 0, down = 0.2, eIn = 'inOut', eOut = 'inOut') {
  if (t <= a) return 0;
  if (t < a + up) return ease[eIn]((t - a) / up);
  if (t < a + up + hold) return 1;
  if (t < a + up + hold + down) return 1 - ease[eOut]((t - a - up - hold) / down);
  return 0;
}
/** eased 0 -> 1 between absolute times a and b. */
export const ramp = (t, a, b, e = 'inOut') => (b <= a ? (t >= b ? 1 : 0) : ease[e](clamp((t - a) / (b - a))));
/** damped wobble after a (1 at a): freq Hz, decay 1/s. */
export const wobble = (t, a, freq = 2.2, decay = 4) => (t <= a ? 0 : Math.sin((t - a) * freq * Math.PI * 2) * Math.exp(-(t - a) * decay));
/** soft overshoot-settle step: 0 before a, eases to 1 by a+dur with ~ov overshoot and a damped settle. */
export function settle(t, a, dur = 0.3, ov = 0.08) {
  if (t <= a) return 0;
  const u = clamp((t - a) / dur);
  return ease.inOut(u) + ov * Math.sin(Math.PI * clamp((t - a - dur * 0.6) / (dur * 1.6))) * (t > a + dur * 0.6 ? 1 : 0);
}

/**
 * keys: [[timeRef, target (Vector3 | [x,y,z] | () => Vector3), dur?], ...]: saccade-style switches (ease over dur,
 * default 0.09 s), holds between. Returns a Vector3.
 */
export function gazeSched(t, keys) {
  const res = (g) => toV(typeof g === 'function' ? g() : g);
  let i = -1;
  for (let j = 0; j < keys.length; j++) if (T(keys[j][0]) <= t) i = j;
  if (i <= 0) return res(keys[0][1]);
  const d = keys[i][2] ?? 0.09;
  const u = smooth((t - T(keys[i][0])) / d);
  if (u >= 1) return res(keys[i][1]);
  return res(keys[i - 1][1]).lerp(res(keys[i][1]), u);
}

// ------------------------------------------------------------------------------------------------ cameras
/**
 * Camera for vertical fov so world points land on target pixels: pts [[Vector3|[x,y,z], px, py, weight?]].
 * Deterministic coordinate descent from (pos0, look0); posReg pulls pos toward pos0; free masks pos axes.
 */
export function fitShot(pts, fov, pos0, look0, { posReg = 0.02, free = [1, 1, 1], yMin = -99, yMax = 99, drift = 0.25 } = {}) {
  const cam = new THREE.PerspectiveCamera(fov, 720 / 1280, 0.05, 400);
  const P = [...toV(pos0).toArray(), ...toV(look0).toArray()];
  const PT = pts.map(([w, x, y, wt]) => [toV(w), x, y, wt ?? 1]);
  const p0 = toV(pos0);
  const cost = (q) => {
    cam.position.set(q[0], q[1], q[2]); cam.up.set(0, 1, 0); cam.lookAt(q[3], q[4], q[5]); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
    let e = 0;
    for (const [w, x, y, wt] of PT) {
      const v = w.clone().project(cam);
      if (v.z > 1) { e += 1e7; continue; }
      const sx = (v.x * 0.5 + 0.5) * 720, sy = (1 - (v.y * 0.5 + 0.5)) * 1280;
      e += wt * ((sx - x) ** 2 + (sy - y) ** 2);
    }
    e += posReg * 1e4 * ((q[0] - p0.x) ** 2 + (q[1] - p0.y) ** 2 + (q[2] - p0.z) ** 2);
    if (q[1] < yMin) e += 1e7 * (yMin - q[1]) ** 2;
    if (q[1] > yMax) e += 1e7 * (q[1] - yMax) ** 2;
    return e;
  };
  let best = cost(P), step = 0.5;
  for (let it = 0; it < 600 && step > 0.0008; it++) {
    let improved = false;
    for (let i = 0; i < 6; i++) {
      if (i < 3 && !free[i]) continue;
      for (const d of [step, -step]) { const q = P.slice(); q[i] += d; const c = cost(q); if (c < best) { best = c; P.splice(0, 6, ...q); improved = true; } }
    }
    if (!improved) step *= 0.6;
  }
  return { pos: P.slice(0, 3), look: P.slice(3, 6), fov, drift, err: Math.sqrt(best / Math.max(1, PT.length)) };
}
/** Linear blend of two shots (u 0..1, eased by the caller). */
export function mixShot(a, b, u) {
  const L = (x, y) => x.map((v, i) => v + (y[i] - v) * u);
  return { pos: L(a.pos, b.pos), look: L(a.look, b.look), fov: lerp(a.fov, b.fov, u), drift: lerp(a.drift ?? 0.25, b.drift ?? 0.25, u), roll: lerp(a.roll || 0, b.roll || 0, u) };
}
/** Pull back / push in with a constant apparent zoom rate: u 0..1 -> blend weight for a dolly whose camera distance
 *  goes from d0 to d1 (log-distance interpolation). */
export function logDolly(u, d0, d1) {
  const r = d1 / d0;
  if (Math.abs(r - 1) < 1e-4) return u;
  return (Math.pow(r, u) - 1) / (r - 1);
}
/** screen [x, y] of a world point for a shot (no rendering) */
const _pc = new THREE.PerspectiveCamera(35, 720 / 1280, 0.05, 400);
export function project(shot, p) {
  _pc.fov = shot.fov; _pc.updateProjectionMatrix(); _pc.position.set(...shot.pos); _pc.up.set(0, 1, 0); _pc.lookAt(...shot.look); _pc.updateMatrixWorld();
  const v = toV(p).project(_pc);
  return [Math.round((v.x * 0.5 + 0.5) * 720), Math.round((1 - (v.y * 0.5 + 0.5)) * 1280)];
}

// ------------------------------------------------------------------------------------------------ scene plumbing
/** A Group for this scene's own props inside the SHARED set scene: hidden on frames not rendered by this scene. */
export function ownedGroup(st, name = 'owned') {
  const g = new THREE.Group();
  g.name = name;
  const base = THREE.Object3D.prototype.updateMatrixWorld;
  g.updateMatrixWorld = function (force) { this.visible = st.__t === CTX.t; return base.call(this, force); };
  return g;
}
/** (Re)attach exactly the characters `names` to the scene; detach other loaded characters parented to it. */
export function cast(app, scene, names) {
  for (const [nm, c] of Object.entries(app.chars)) {
    if (!c || !c.root) continue;
    if (names.includes(nm)) { if (c.root.parent !== scene) scene.add(c.root); c.root.visible = true; }
    else if (c.root.parent === scene) scene.remove(c.root);
  }
}

// ------------------------------------------------------------------------------------------------ marks
/** World marks of the bonus (ROOM.fit(set) first). Feet inside the cage stand on its base plate (y = cageInside.y). */
export function bonusMarks(set) {
  ROOM.fit(set);
  const M = ROOM.M, A = set.anchors, Y = set.yaws;
  const plate = A.cageInside ? A.cageInside.y : 0.04;
  const W = (p, y = 0) => { const w = ROOM.W(p); return [w[0], y, w[2]]; };
  return {
    V: [A.voidSpot.x, 0, A.voidSpot.z], vYaw: Y.void,
    FIN: W(M.FIN.p, plate), finYaw: ROOM.Y(M.FIN.yaw),
    FDOOR: W(M.FDOOR.p, plate), fdoorYaw: ROOM.Y(M.FDOOR.yaw),
    LURK: [A.lurkSpot.x, 0, A.lurkSpot.z], lurkYaw: Y.magicianLurk,
    PEEK: W(M.PEEK.p), peekYaw: ROOM.Y(M.PEEK.yaw),
    plate,
  };
}

/** The Void's base pose for the bonus: at its spot beside the cage, bowed toward Fear, soft. `gaze` = Fear. */
export function voidBowed(t, B, over = {}) {
  return {
    pos: B.V, yaw: B.vYaw,
    body: { lean: 0.12, breathe: 0.85, ...(over.body || {}) },
    head: { pitch: 0.25, ...(over.head || {}) },
    face: over.face || VX('tender'),
    gaze: over.gaze,
    armL: over.armL || { preset: 'rest' }, armR: over.armR || { preset: 'rest' },
    extra: { stars: 1.4, rim: 1.15, ...(over.extra || {}) },
    blinkAt: over.blinkAt,
    speech: over.speech,
  };
}

// ------------------------------------------------------------------------------------------------ floor evidence
// The magician's colour-drained footprints (s18b07, one per planted step) + the numbing-dust patch (s18b03, grows
// where the glitter lands). Grey Lambert decals with soft alpha: lit like the floor, so they read as the floor's
// warm colour drained to grey, not as glowing stickers. Visible by time (pure), faded out with the cosmos in s22.
const PRINTS_KEY = '__bonusDecals';
function printTexture() {
  const c = document.createElement('canvas'); c.width = 64; c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = 'rgba(0,0,0,0)'; g.fillRect(0, 0, 64, 128);
  g.filter = 'blur(2px)';
  g.fillStyle = 'rgba(255,255,255,0.95)';
  // a pointy, curled-toe shoe sole: toe at the top (texture v=1 -> +Z local)
  g.beginPath();
  g.moveTo(32, 6); g.quadraticCurveTo(46, 26, 47, 52); g.quadraticCurveTo(48, 74, 42, 84);
  g.lineTo(22, 84); g.quadraticCurveTo(16, 70, 18, 50); g.quadraticCurveTo(20, 24, 32, 6); g.fill();
  g.beginPath(); g.ellipse(32, 106, 12, 15, 0, 0, Math.PI * 2); g.fill();     // heel
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
function patchTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  const blob = (x, y, r, a) => { const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(255,255,255,${a})`); gr.addColorStop(0.6, `rgba(255,255,255,${a * 0.7})`); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill(); };
  blob(64, 64, 52, 0.85); blob(44, 70, 30, 0.5); blob(84, 54, 28, 0.5); blob(70, 86, 24, 0.4);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/**
 * The decal singleton for this set (idempotent). `items` = [{ kind: 'print'|'patch', pos: [x,z], yaw, t0, grow }].
 * If the list was already registered (by s18), later calls just return it. The group lives in set.scene and decides
 * visibility from CTX.t alone (pure): an item shows from its t0 (fade-in 3 frames; a patch grows over `grow` s) and
 * everything fades out over s22b02 -> s22b03 (the cosmos takes the floor).
 */
export function bonusDecals(set, items) {
  if (set[PRINTS_KEY]) return set[PRINTS_KEY];
  if (!items) return null;
  const grp = new THREE.Group(); grp.name = 'bonusDecals';
  const ptex = printTexture(), ttex = patchTexture();
  const mk = (tex, w, h) => {
    const m = new THREE.MeshLambertMaterial({ map: tex, color: 0xc2c4cb, transparent: true, opacity: 0, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
    mesh.rotation.order = 'YXZ'; mesh.receiveShadow = true; mesh.renderOrder = 1;
    return mesh;
  };
  const meshes = items.map((it) => {
    const m = it.kind === 'patch' ? mk(ttex, 1, 1) : mk(ptex, 0.13, 0.3);
    m.position.set(it.pos[0], 0.004, it.pos[1]);
    m.rotation.set(-Math.PI / 2, it.yaw || 0, 0);
    grp.add(m);
    return m;
  });
  const fadeOut = () => { try { return 1 - ramp(CTX.t, T('s22b02'), T('s22b03')); } catch (e) { return 1; } };
  const base = THREE.Object3D.prototype.updateMatrixWorld;
  grp.updateMatrixWorld = function (force) {
    const t = CTX.t, fo = fadeOut();
    let any = false;
    items.forEach((it, i) => {
      const m = meshes[i];
      const a = clamp((t - it.t0) / 0.12);
      const g = it.kind === 'patch' ? smooth(clamp((t - it.t0) / (it.grow || 1.2))) : 1;
      m.visible = a > 0 && fo > 0.001;
      if (!m.visible) return;
      any = true;
      m.material.opacity = (it.alpha ?? 0.8) * a * fo;
      const s = it.kind === 'patch' ? (it.size || 0.6) * (0.25 + 0.75 * g) : 1;
      m.scale.set(s, s, 1);
    });
    this.visible = any;
    return base.call(this, force);
  };
  set.scene.add(grp);
  set[PRINTS_KEY] = { group: grp, items };
  return set[PRINTS_KEY];
}

// ------------------------------------------------------------------------------------------------ the magician's creep
// Where he is through the bonus (ROOM-local stage points, derived from the Void's frame at voidSpot: back = local
// (0.868, -0.496), its left = local (0.496, 0.868)):
//   s18b01  crouched at PEEK (behind the Void's back-left), rises like a periscope
//   s18b02-b06  at PEEK: pressed against the back-left of the cloak, peeking round its flank toward Fear
//   s18b07  stage tiptoe PEEK -> FAR along its back (3 steps, each leaves a grey print), freezes on one foot
//   s19b01  tiptoes back FAR -> PEEK in reverse (hat brim bobbing at the edge of frame); on his toes at PEEK (-> s20)
export const MAGPATH = {
  PEEK: [3.2, 0, 0.01],
  FAR: [2.93, 0, -0.85],      // 0.9 m from PEEK, behind the Void's back (slightly to its right)
  PATCH: [2.95, 0, 0.42],      // where the numbing dust lands in s18b03 (under his pouch hand)
  STRIDE: 0.72,               // magician GAIT.sneak metres per cycle (phase = distance / STRIDE: no foot sliding)
};
const PH0 = () => 0.75 - Math.hypot(MAGPATH.FAR[0] - MAGPATH.PEEK[0], MAGPATH.FAR[2] - MAGPATH.PEEK[2]) / MAGPATH.STRIDE;
/** the tiptoe (s18b07 out, s19b01 back): { pos (world), yaw, walk, dist, phase, hold, tA, tOut, tR, tBack } — pure. */
export function magTiptoe(t) {
  const tA = T('s18b07') + 0.05, tOut = tA + 1.45;                 // out: 3 high-kneed steps
  const tR = T('s19b01') + 0.05, tBack = tR + 1.35;                // back (reverse), into view at the Void's shoulder
  const p0 = ROOM.W(MAGPATH.PEEK), p1 = ROOM.W(MAGPATH.FAR);
  const L = Math.hypot(p1[0] - p0[0], p1[2] - p0[2]);
  let f;
  if (t < tOut) f = ease.inOut(clamp((t - tA) / (tOut - tA)));
  else if (t < tR) f = 1;
  else f = 1 - ease.inOut(clamp((t - tR) / (tBack - tR)));
  const dist = f * L;
  const pos = [lerp(p0[0], p1[0], f), 0, lerp(p0[2], p1[2], f)];
  const yaw = Math.atan2(p1[0] - p0[0], p1[2] - p0[2]);
  const phase = PH0() + dist / MAGPATH.STRIDE;
  const moving = (t > tA && t < tOut + 0.6) || (t > tR - 0.1 && t < tBack + 0.15);
  const amt = t <= tA ? 0 : t >= tBack + 0.15 ? 0 : clamp((t - tA) / 0.12) * (t > tBack ? 1 - clamp((t - tBack) / 0.15) : 1);
  const hold = t > tOut && t < tR ? 1 : 0;
  return { pos, yaw, walk: { amount: amt, phase, style: 'sneak' }, dist, phase, hold, f, tA, tOut, tR, tBack, moving };
}
/** times when a foot touches down during the tiptoe (phase crosses a multiple of 0.5, either direction) in [a, b]. */
export function magSteps(a, b, dt = 1 / 96) {
  const out = [];
  let prev = magTiptoe(a).phase;
  for (let t = a + dt; t <= b; t += dt) {
    const ph = magTiptoe(t).phase;
    if (Math.floor(ph * 2) !== Math.floor(prev * 2)) out.push(+t.toFixed(3));
    prev = ph;
  }
  return out;
}
/** grey prints (analytic, from the gait): ball-of-foot contacts at mid-stance of each planted step of the walk out. */
export function magPrints() {
  const p0 = ROOM.W(MAGPATH.PEEK), p1 = ROOM.W(MAGPATH.FAR);
  const L = Math.hypot(p1[0] - p0[0], p1[2] - p0[2]);
  const yaw = Math.atan2(p1[0] - p0[0], p1[2] - p0[2]);
  const fwd = [Math.sin(yaw), Math.cos(yaw)], left = [Math.cos(yaw), -Math.sin(yaw)];
  const ph0 = PH0(), ph1 = ph0 + L / MAGPATH.STRIDE;
  const tp = magTiptoe(T('s18b07'));
  // time at which the walk-out reaches phase ph (invert the eased distance by bisection)
  const timeAt = (ph) => { let a = tp.tA, b = tp.tOut; for (let i = 0; i < 40; i++) { const m = (a + b) / 2; if (magTiptoe(m).phase < ph) a = m; else b = m; } return (a + b) / 2; };
  const out = [];
  for (const [side, s, off] of [['L', 1, 0.25], ['R', -1, 0.75]]) {
    for (let n = Math.floor(ph0) - 1; n <= Math.ceil(ph1) + 1; n++) {
      const mid = n + off;                            // mid-stance phase of this foot
      const down = mid - 0.25;                        // touchdown phase
      if (mid < ph0 - 0.25 || mid > ph1 + 0.01) continue;
      const fm = clamp((mid - ph0) * MAGPATH.STRIDE / L);
      const rx = lerp(p0[0], p1[0], fm), rz = lerp(p0[2], p1[2], fm);
      const bx = s * 0.13, bz = 0.15;                 // ball of the foot (sneak walks on the toes), toes out
      out.push({ kind: 'print', pos: [rx + left[0] * bx + fwd[0] * bz, rz + left[1] * bx + fwd[1] * bz], yaw: yaw + s * 0.25,
        t0: down <= ph0 ? tp.tA : timeAt(down + 0.02), side });
    }
  }
  return out.sort((a, b) => a.t0 - b.t0);
}

/**
 * Register the floor evidence on this BACKROOM set (idempotent; pure: computed from the timeline + marks only).
 * Call from setup() of any backroom scene from s18 on: `ensureBonusDecals(set)`.
 */
export function ensureBonusDecals(set) {
  if (set[PRINTS_KEY]) return set[PRINTS_KEY];
  ROOM.fit(set);
  const items = magPrints();
  const pw = ROOM.W(MAGPATH.PATCH);
  items.push({ kind: 'patch', pos: [pw[0], pw[2]], yaw: 0.6, t0: wordT('s18b03', 'dust', { fallback: 0.75 }) + 0.3, grow: 1.4, size: 0.62, alpha: 0.7 });
  return bonusDecals(set, items);
}

export { clamp, smooth, lerp, ease, T };
