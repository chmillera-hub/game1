// PROPS — the TIME-OUT cage, the old "My Feelings" notebook, and the desk lamp.
//
//   drawCage(g, x, y, scale, state)       (x,y) = centre of the cage footprint on the ground
//   drawNotebook(g, x, y, scale, state)   (x,y) = centre of the notebook (closed or open spread)
//   drawDeskLamp(g, x, y, scale, state)   (x,y) = centre of the lamp base on the desk top
//
// Full API reference for scene animators: docs/props.md.
// All drawing is deterministic in state.t. Every function save()/restore()s and leaks no state.

import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import path from 'path';
import { fileURLToPath } from 'url';
import { clamp, lerp, TAU, rgba, mixColor, ellipse, circle, groundShadow, smoothstep, ease } from '../engine.mjs';

// ---------------------------------------------------------------- integer-safe noise
// (engine.mjs hrand()/vnoise() overflow float precision for larger seeds / inputs, so props use these.)
function h32(n) {
  n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
  n = Math.imul(n ^ (n >>> 15), 0x846ca68b);
  return (n ^ (n >>> 16)) >>> 0;
}
/** deterministic 0..1 */
export const hrand = (i, seed = 0) => h32(Math.imul(i | 0, 0x9e3779b1) ^ Math.imul((seed | 0) + 0x632be5ab, 0x85ebca6b)) / 4294967296;
/** smooth value noise in [-1, 1] */
export function vnoise(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hrand(i, seed) * 2 - 1, b = hrand(i + 1, seed) * 2 - 1;
  return a + (b - a) * f * f * (3 - 2 * f);
}
export const vfbm = (x, seed = 0) => vnoise(x, seed) * 0.7 + vnoise(x * 2.3, seed + 17) * 0.3;

// ---------------------------------------------------------------- fonts
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export function ensureFonts() {
  for (const [f, name] of [['Caveat.ttf', 'Caveat'], ['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand']]) {
    try { if (!GlobalFonts.has(name)) GlobalFonts.registerFromPath(path.join(ROOT, 'assets/fonts', f), name); } catch { /* ignore */ }
  }
}
ensureFonts();

// ---------------------------------------------------------------- small helpers
function poly(g, pts) {
  g.beginPath();
  g.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
}
function polyOff(g, pts, ox, oy = 0) {
  g.beginPath();
  g.moveTo(pts[0][0] + ox, pts[0][1] + oy);
  for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0] + ox, pts[i][1] + oy);
}
const pScale = (g) => {
  try { const m = g.getTransform(); return Math.hypot(m.a, m.b) || 1; } catch { return 1; }
};

// =====================================================================================
//                                     THE TIME-OUT CAGE
// =====================================================================================
// Geometry (cage-local, scale 1). A cylinder of bars seen slightly from above: a 3-D point
// (X, Y-up, Z-toward-camera) projects to screen (X, -Y + Z*CK). Origin = footprint centre.
const CK = 0.2;                 // floor-plane squash
const CR = 165;                 // bar-cylinder radius (outer width 330)
const PLINTH_R = 178, FLOOR_Y = 20;
const TOP_Y = 340, DOME_H = 108, APEX_Y = TOP_Y + DOME_H;
const DOOR_HALF = 0.5;          // door spans theta in [-0.5, 0.5] (front centre)
const DOOR_R = CR + 3, DOOR_BOT = 27, DOOR_TOP = 316, DOOR_ARCH = 12, DOOR_MID = 120;
const HINGE_TOP_Y = 292, HINGE_BOT_Y = 58, LOCK_Y = 150;
const NFIX = 13;
const FIX_STEP = (TAU - 2 * DOOR_HALF) / (NFIX - 1);
const FIXED = Array.from({ length: NFIX }, (_, j) => DOOR_HALF + j * FIX_STEP); // j=0 lock jamb (+x), j=12 hinge jamb (-x)
const HX = DOOR_R * Math.sin(-DOOR_HALF), HZ = DOOR_R * Math.cos(-DOOR_HALF);
const LOCK_X = CR * Math.sin(DOOR_HALF) + 5, LOCK_Z = CR * Math.cos(DOOR_HALF) + 8;
const SIGN_HANG_Y = APEX_Y + 16;

const proj = (X, Y, Z) => [X, -Y + Z * CK];
const barXZ = (th, r = CR) => [r * Math.sin(th), r * Math.cos(th)];

/** Cage-local anchor points at scale 1 (x right, y down, origin = footprint centre on the ground).
 *  Mirror x when state.flip = -1. Use cagePoint() to get world coordinates. */
export const CAGE_ANCHORS = {
  occupant: [0, -FLOOR_Y],                       // occupant feet, standing in the middle of the cage floor
  occupantFront: [0, -FLOOR_Y + 100 * CK],       // feet when standing right behind the front bars (to grip them)
  occupantBack: [0, -FLOOR_Y - 70 * CK],         // feet near the back bars (cowering away from the door)
  occupantSide: [-70, -FLOOR_Y + 40 * CK],       // feet in the left half (e.g. curled up away from the Void)
  floorFront: [0, 178 * CK],                     // front lip of the plinth on the ground (lowest visible point)
  doorway: [0, -FLOOR_Y + CR * CK],              // threshold centre (feet of someone stepping out)
  outside: [0, 70],                              // feet of someone standing just outside the door
  lock: proj(LOCK_X, LOCK_Y - 30, LOCK_Z),       // padlock body centre (closed); keyhole ~ +4 px lower
  lockHang: proj(LOCK_X, LOCK_Y, LOCK_Z),        // staple the padlock hangs from (Void's fingertip target)
  doorHandle: proj(DOOR_R * Math.sin(DOOR_HALF) + 3, LOCK_Y, DOOR_R * Math.cos(DOOR_HALF)), // hasp on the door's free edge, the grab point (moves with the door: use cagePoint)
  hingeTop: proj(HX, HINGE_TOP_Y, HZ),
  gripL: proj(CR * Math.sin(-DOOR_HALF), 215, CR * Math.cos(DOOR_HALF)), // on the hinge jamb bar, chest/face height for occupantFront
  gripR: proj(CR * Math.sin(DOOR_HALF), 215, CR * Math.cos(DOOR_HALF)),  // on the lock jamb bar
  gripHighL: proj(CR * Math.sin(-DOOR_HALF), 262, CR * Math.cos(DOOR_HALF)),
  gripHighR: proj(CR * Math.sin(DOOR_HALF), 262, CR * Math.cos(DOOR_HALF)),
  gripC: proj(0, 200, DOOR_R),                   // on the door's centre bar
  top: [0, -(APEX_Y + 32)],                      // top of the hanging loop
  sign: [0, -(SIGN_HANG_Y) + 87],                // centre of the TIME-OUT sign (clean cage)
  topRingFront: proj(0, TOP_Y, CR),
};
export const CAGE_SIZE = { width: PLINTH_R * 2, barWidth: CR * 2, height: APEX_Y + 32 + 178 * CK, interiorHeight: APEX_Y - FLOOR_Y, interiorWidth: CR * 2 - 20, floorY: -FLOOR_Y };

/** Ready-made cage states for the story beats (spread into state, then add t / layer / shake). */
export const CAGE_PRESETS = {
  locked: { door: 0, locked: 1, rust: 0 },            // s09/s10: Fear in time-out
  unlocked: { door: 0, locked: 0, rust: 0 },          // s11: the Void's fingertip has turned the lock
  ajar: { door: 0.3, locked: 0, rust: 0 },            // s11/s12: the gate drifts open on its own weight
  open: { door: 1, locked: 0, rust: 0 },              // s12-s20: open cage
  rustedOpen: { door: 1, locked: 0, rust: 1 },        // s21: rusted, hanging open on one hinge
  barelyVisible: { door: 1, locked: 0, rust: 1, dim: 0.85 }, // s22: far back of the mind
};

const DOOR_OPEN_ANGLE = 2.55; // radians at door = 1

function doorParams(st) {
  const sag = st.rust * (0.05 + 0.15 * st.door);
  const alpha = st.door * DOOR_OPEN_ANGLE + st.shake * 0.035 * vnoise(st.t * 15, 51) * (1 - st.locked * 0.6);
  return { sag, alpha, cb: Math.cos(sag), sb: Math.sin(sag), ca: Math.cos(alpha), sa: Math.sin(alpha) };
}
/** door point: s in [0..1] from hinge to free edge, Y height. Returns screen [x,y] (cage-local). */
function doorPt(dp, s, Y) {
  const th = -DOOR_HALF + s * 2 * DOOR_HALF;
  const X = DOOR_R * Math.sin(th), Z = DOOR_R * Math.cos(th);
  const dx = X - HX, dz = Z - HZ, dy = Y - HINGE_TOP_Y;
  const dx1 = dx * dp.cb + dy * dp.sb, dy1 = -dx * dp.sb + dy * dp.cb;
  const dx2 = dx1 * dp.ca - dz * dp.sa, dz2 = dx1 * dp.sa + dz * dp.ca;
  return proj(HX + dx2, HINGE_TOP_Y + dy1, HZ + dz2);
}

// grip names mean SCREEN sides: when the cage is mirrored, 'gripL' resolves to the bar that lands on the left
const GRIP_SWAP = { gripL: 'gripR', gripR: 'gripL', gripHighL: 'gripHighR', gripHighR: 'gripHighL' };
function anchorLocal(name, flip) {
  return CAGE_ANCHORS[flip === -1 && GRIP_SWAP[name] ? GRIP_SWAP[name] : name];
}

/** World position of a named CAGE_ANCHORS point (accounts for scale, flip, and the door for 'doorHandle'). */
export function cagePoint(name, x, y, scale = 1, state = {}) {
  let p = anchorLocal(name, state.flip);
  if (name === 'doorHandle') {
    const st = normCage(state);
    p = doorPt(doorParams(st), 1, LOCK_Y); p = [p[0] + 3, p[1]];
  }
  if (!p) return [x, y];
  const flip = state.flip === -1 ? -1 : 1;
  return [x + p[0] * scale * flip, y + p[1] * scale];
}

function normCage(state) {
  return {
    t: state.t || 0,
    door: clamp(state.door ?? 0),
    locked: clamp(state.locked ?? 1),
    rust: clamp(state.rust ?? 0),
    shake: clamp(state.shake ?? 0),
    dim: clamp(state.dim ?? 0),
  };
}

// ---- palette (cached by quantised rust/dim)
const CAGE_CLEAN = {
  base: '#4a5268', light: '#7b86a3', hi: '#cfd7ee', line: '#161827', floor: '#2b2f40', floorHi: '#454c64',
  brass: '#d8ac4c', brassHi: '#fff0b0', brassDk: '#7a5520',
  wood: '#b0794a', woodHi: '#d9a774', woodDk: '#6b4226', ink: '#3a2215', rope: '#8a6a48',
};
const CAGE_RUST = {
  base: '#7a3f25', light: '#a65a32', hi: '#d99561', line: '#2a130b', floor: '#45291b', floorHi: '#5f3a26',
  brass: '#8e5c2c', brassHi: '#c9894c', brassDk: '#45260f',
  wood: '#8d7660', woodHi: '#b09a82', woodDk: '#54402f', ink: '#3a2a20', rope: '#6b5a48',
};
const palCache = new Map();
function cagePal(rust, dim, dark, rim) {
  const key = `${Math.round(rust * 50)}|${Math.round(dim * 50)}|${dark}|${rim}`;
  let P = palCache.get(key);
  if (P) return P;
  P = {};
  const rk = smoothstep(0, 1, rust) * 0.85;
  for (const k in CAGE_CLEAN) P[k] = mixColor(mixColor(CAGE_CLEAN[k], CAGE_RUST[k], k.startsWith('wood') || k === 'ink' || k === 'rope' ? rust : rk), dark, dim * 0.82);
  P.flake = mixColor('#c7692f', dark, dim * 0.82);
  P.flakeHi = mixColor('#e8a060', dark, dim * 0.82);
  P.pit = mixColor('#3e1b0d', dark, dim * 0.82);
  P.rim = rim || '#8a6cff';
  P.rimA = 0.42 * (1 - dim) * (1 - rust * 0.5);
  P.alpha = 1 - dim * 0.4;
  if (palCache.size > 400) palCache.clear();
  palCache.set(key, P);
  return P;
}

// ---- bar stroking: dark outline, body, upper-left highlight, violet rim, rust blotches
function strokeBar(g, pts, P, w, depth, seed, rust) {
  g.lineCap = 'round';
  g.lineJoin = 'round';
  g.strokeStyle = P.line;
  g.lineWidth = w + 3.2;
  poly(g, pts); g.stroke();
  g.strokeStyle = depth > 0 ? mixColor(P.base, P.line, depth * 0.5) : P.base;
  g.lineWidth = w;
  poly(g, pts); g.stroke();
  g.strokeStyle = rgba(P.hi, 0.8 * (1 - depth * 0.65));
  g.lineWidth = Math.max(1.1, w * 0.3);
  polyOff(g, pts, -w * 0.2, 0); g.stroke();
  if (P.rimA > 0.02 && depth < 0.3) {
    g.strokeStyle = rgba(P.rim, P.rimA);
    g.lineWidth = 1.3;
    polyOff(g, pts, w * 0.36, 0); g.stroke();
  }
  if (rust > 0.04) rustSpots(g, pts, P, w, seed, rust, depth);
}

function ptAt(pts, u) {
  const f = clamp(u) * (pts.length - 1);
  const i = Math.min(pts.length - 2, Math.floor(f)), k = f - i;
  return [lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k), pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]];
}
function rustSpots(g, pts, P, w, seed, rust, depth) {
  const n = 5;
  for (let i = 0; i < n; i++) {
    const thr = hrand(seed * 11 + i, 5);
    const vis = clamp((rust * 1.25 - thr) * 4);
    if (vis <= 0.01) continue;
    const u = 0.06 + 0.88 * hrand(seed * 11 + i, 6);
    const [px, py, dx, dy] = ptAt(pts, u);
    const L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
    const len = 5 + 14 * hrand(seed * 11 + i, 7);
    const pit = hrand(seed * 11 + i, 8) > 0.62;
    g.strokeStyle = rgba(pit ? P.pit : P.flake, vis * (pit ? 0.75 : 0.9) * (1 - depth * 0.4));
    g.lineWidth = w * (pit ? 0.55 : 0.85);
    g.beginPath(); g.moveTo(px - ux * len / 2, py - uy * len / 2); g.lineTo(px + ux * len / 2, py + uy * len / 2); g.stroke();
    if (!pit && rust > 0.55 && hrand(seed * 11 + i, 9) > 0.7) {
      // a paint flake lifting off the bar edge (small, lying along the bar)
      const side = hrand(seed * 11 + i, 10) > 0.5 ? 1 : -1;
      const fx = px + (-uy) * side * w * 0.5, fy = py + ux * side * w * 0.5;
      g.fillStyle = rgba(P.flakeHi, vis * 0.9);
      g.beginPath();
      g.moveTo(fx - ux * 4, fy - uy * 4);
      g.lineTo(fx + ux * 3 + (-uy) * side * 2, fy + uy * 3 + ux * side * 2);
      g.lineTo(fx + ux * 4, fy + uy * 4);
      g.closePath(); g.fill();
    }
  }
}

function ringArc(g, Y, r, a0, a1, P, w, depth, jx = 0) {
  const pts = [];
  const N = Math.max(6, Math.ceil(Math.abs(a1 - a0) / 0.12));
  for (let i = 0; i <= N; i++) {
    const a = lerp(a0, a1, i / N);
    pts.push([Math.cos(a) * r + jx, -Y + Math.sin(a) * r * CK]);
  }
  return pts;
}
function strokeRing(g, pts, P, w, depth, seed, rust) {
  g.lineCap = 'round';
  g.lineJoin = 'round';
  g.strokeStyle = P.line; g.lineWidth = w + 3.2; poly(g, pts); g.stroke();
  g.strokeStyle = depth > 0 ? mixColor(P.base, P.line, depth * 0.5) : P.base; g.lineWidth = w; poly(g, pts); g.stroke();
  g.strokeStyle = rgba(P.hi, 0.7 * (1 - depth * 0.6)); g.lineWidth = Math.max(1, w * 0.3); polyOff(g, pts, 0, -w * 0.25); g.stroke();
  if (rust > 0.04) rustSpots(g, pts, P, w, seed, rust * 0.9, depth);
}

// per-bar rattle (lateral displacement at the bar's middle)
function barShake(st, i, weight) {
  if (st.shake <= 0) return 0;
  return st.shake * weight * (3.4 * vnoise(st.t * 17 + i * 2.31, 31) + 1.2 * Math.sin(st.t * 41 + i * 1.7));
}
function bodyBarPts(th, Y0, Y1, d) {
  const [X, Z] = barXZ(th);
  const pts = [];
  for (let i = 0; i <= 4; i++) {
    const u = i / 4;
    const [sx, sy] = proj(X, lerp(Y0, Y1, u), Z);
    pts.push([sx + d * Math.sin(Math.PI * u), sy]);
  }
  return pts;
}
function domeBarPts(th) {
  const pts = [];
  const phMax = Math.acos(15 / CR);
  for (let i = 0; i <= 9; i++) {
    const ph = (i / 9) * phMax;
    const r = CR * Math.cos(ph), Y = TOP_Y + DOME_H * Math.sin(ph);
    pts.push(proj(r * Math.sin(th), Y, r * Math.cos(th)));
  }
  return pts;
}

/**
 * Draw the TIME-OUT cage. See docs/props.md.
 * state: { layer:'back'|'front'|'all', door 0..1, locked 0..1, rust 0..1, shake 0..1, dim 0..1, t,
 *          flip 1|-1, shadow bool, grips:[[x,y]|name...], gripColor, gripLine, gripScale, rim, darkColor }
 */
export function drawCage(g, x, y, scale = 1, state = {}) {
  const layer = state.layer || 'all';
  const st = normCage(state);
  const flip = state.flip === -1 ? -1 : 1;
  const P = cagePal(st.rust, st.dim, state.darkColor || '#0d0b1c', state.rim);
  const jx = st.shake * 1.1 * vnoise(st.t * 21, 41), jy = st.shake * 0.5 * vnoise(st.t * 23, 42);
  // pixel scale of the cached static layers (quantised so slow camera moves rarely rebuild them)
  const ps = Math.abs(scale) * pScale(g);
  const res = Math.max(0.25, Math.min(3, Math.round(ps * 8) / 8));
  const rq = Math.round(st.rust * 20) / 20, dq = Math.round(st.dim * 20) / 20;
  const ckey = `${rq}|${dq}|${res}|${state.darkColor || ''}|${state.rim || ''}`;
  g.save();
  g.translate(x + jx * scale, y + jy * scale);
  g.scale(scale * flip, scale);
  if (P.alpha < 1) g.globalAlpha *= P.alpha;
  if (layer !== 'front') {
    if (state.shadow !== false) groundShadow(g, 0, 6, PLINTH_R * 1.22, 0.42 * (1 - st.dim * 0.5), PLINTH_R * 0.3);
    blitCage(g, cageCache(`back|${ckey}`, res, (cg) => cageBack(cg, { ...st, rust: rq, dim: dq }, P)));
  }
  if (layer !== 'back') cageFront(g, st, P, state, flip, ckey, res, rq, dq);
  g.restore();
}

// ---- static-layer bitmap cache (cage-local box, rendered at the current pixel scale)
const CBOX = { x: -230, y: -(APEX_Y + 46), w: 460, h: APEX_Y + 46 + 60 };
const cageBmp = new Map();
function cageCache(key, res, build) {
  let c = cageBmp.get(key);
  if (c) { cageBmp.delete(key); cageBmp.set(key, c); return c; } // LRU touch
  c = createCanvas(Math.max(1, Math.ceil(CBOX.w * res)), Math.max(1, Math.ceil(CBOX.h * res)));
  const cg = c.getContext('2d');
  cg.scale(res, res);
  cg.translate(-CBOX.x, -CBOX.y);
  build(cg);
  cageBmp.set(key, c);
  while (cageBmp.size > 28) cageBmp.delete(cageBmp.keys().next().value);
  return c;
}
const blitCage = (g, c) => g.drawImage(c, CBOX.x, CBOX.y, CBOX.w, CBOX.h);

function cageBack(g, st, P) {
  // plinth band (front face)
  const PR = PLINTH_R;
  g.beginPath();
  g.ellipse(0, 0, PR, PR * CK, 0, 0, Math.PI);
  g.lineTo(-PR, -FLOOR_Y);
  g.ellipse(0, -FLOOR_Y, PR, PR * CK, 0, Math.PI, 0, true);
  g.closePath();
  const gb = g.createLinearGradient(-PR, 0, PR, 0);
  gb.addColorStop(0, mixColor(P.base, P.line, 0.25));
  gb.addColorStop(0.28, P.light);
  gb.addColorStop(0.42, P.base);
  gb.addColorStop(1, mixColor(P.base, P.line, 0.6));
  g.fillStyle = gb;
  g.fill();
  g.strokeStyle = P.line; g.lineWidth = 3; g.stroke();
  // rivets
  for (let i = 0; i < 9; i++) {
    const a = 0.32 + i * (Math.PI - 0.64) / 8;
    const rx = Math.cos(a) * PR * 0.985, ry = -FLOOR_Y * 0.5 + Math.sin(a) * PR * CK;
    g.fillStyle = rgba(P.line, 0.7); circle(g, rx + 0.6, ry + 0.8, 2.6); g.fill();
    g.fillStyle = rgba(P.hi, 0.75); circle(g, rx - 0.3, ry - 0.3, 1.7); g.fill();
  }
  // floor plate
  const gf = g.createRadialGradient(-40, -FLOOR_Y - 10, 10, 0, -FLOOR_Y, PR);
  gf.addColorStop(0, P.floorHi);
  gf.addColorStop(1, P.floor);
  g.fillStyle = gf;
  ellipse(g, 0, -FLOOR_Y, PR, PR * CK);
  g.fill();
  g.strokeStyle = P.line; g.lineWidth = 3; g.stroke();
  // inner rim highlight + back-wall occlusion
  g.strokeStyle = rgba(P.hi, 0.35); g.lineWidth = 1.5;
  g.beginPath(); g.ellipse(0, -FLOOR_Y + 1.5, PR - 4, PR * CK - 1.5, 0, 0.15, Math.PI - 0.15); g.stroke();
  const ao = g.createLinearGradient(0, -FLOOR_Y - PR * CK, 0, -FLOOR_Y + 4);
  ao.addColorStop(0, 'rgba(0,0,0,0.35)'); ao.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = ao;
  ellipse(g, 0, -FLOOR_Y, CR - 4, CR * CK - 2); g.fill();
  // base ring + lower band (back halves)
  strokeRing(g, ringArc(g, FLOOR_Y, CR, Math.PI, TAU, P), P, 8, 0.45, 901, st.rust);
  strokeRing(g, ringArc(g, FLOOR_Y + 36, CR, Math.PI, TAU, P), P, 4.5, 0.45, 902, st.rust);
  // back body bars + dome bars (most distant first)
  const back = FIXED.map((th, i) => ({ th, i, z: Math.cos(th) })).filter((b) => b.z < 0).sort((a, b) => a.z - b.z);
  for (const b of back) strokeBar(g, bodyBarPts(b.th, FLOOR_Y, TOP_Y, 0), P, 6, 0.55 + -b.z * 0.2, b.i + 1, st.rust);
  for (const b of back) strokeBar(g, domeBarPts(b.th), P, 5, 0.55 + -b.z * 0.2, b.i + 40, st.rust);
  // top ring back half
  strokeRing(g, ringArc(g, TOP_Y, CR, Math.PI, TAU, P), P, 8, 0.45, 903, st.rust);
}

const FRONT_BARS = FIXED.map((th, i) => ({ th, i, z: Math.cos(th) })).filter((b) => b.z >= 0).sort((a, b) => a.z - b.z);
function frontBodyBars(g, st, P, live) {
  for (const b of FRONT_BARS) {
    const d = live ? barShake(st, b.i, 0.45 + 0.55 * b.z * b.z) : 0;
    strokeBar(g, bodyBarPts(b.th, FLOOR_Y, TOP_Y, d), P, 6.5, 0, b.i + 1, st.rust);
  }
}
function frontStatic(g, st, P, withBars) {
  if (withBars) frontBodyBars(g, st, P, false);
  // lower band (front), skipping the doorway
  const gapA = Math.PI / 2 - DOOR_HALF, gapB = Math.PI / 2 + DOOR_HALF;
  strokeRing(g, ringArc(g, FLOOR_Y + 36, CR, 0, gapA, P), P, 4.5, 0, 904, st.rust);
  strokeRing(g, ringArc(g, FLOOR_Y + 36, CR, gapB, Math.PI, P), P, 4.5, 0, 905, st.rust);
  // dome bars (front), including the line above the door centre
  for (const b of FRONT_BARS) strokeBar(g, domeBarPts(b.th), P, 5.5, 0, b.i + 40, st.rust);
  strokeBar(g, domeBarPts(0), P, 5.5, 0, 77, st.rust);
  // base ring + top ring (front halves)
  strokeRing(g, ringArc(g, FLOOR_Y, CR, 0, Math.PI, P), P, 8.5, 0, 906, st.rust);
  strokeRing(g, ringArc(g, TOP_Y, CR, 0, Math.PI, P), P, 9, 0, 907, st.rust);
  // dome cap + finial + hanging loop
  const capY = -(APEX_Y - 4);
  g.fillStyle = P.base; g.strokeStyle = P.line; g.lineWidth = 3;
  ellipse(g, 0, capY, 22, 7); g.fill(); g.stroke();
  const gk = g.createRadialGradient(-4, capY - 14, 1, 0, capY - 10, 13);
  gk.addColorStop(0, P.hi); gk.addColorStop(0.5, P.light); gk.addColorStop(1, P.base);
  g.fillStyle = gk;
  circle(g, 0, capY - 10, 11); g.fill(); g.stroke();
  g.strokeStyle = P.line; g.lineWidth = 7.5;
  circle(g, 0, -(APEX_Y + 24), 9); g.stroke();
  g.strokeStyle = P.light; g.lineWidth = 4;
  circle(g, 0, -(APEX_Y + 24), 9); g.stroke();
  // hinge knuckles + the padlock staple on the jambs
  drawHinges(g, st, P);
  const [sx, sy] = proj(LOCK_X, LOCK_Y, LOCK_Z);
  g.strokeStyle = P.line; g.lineWidth = 6;
  g.beginPath(); g.ellipse(sx - 1, sy - 1, 5.5, 7, 0, 0, TAU); g.stroke();
  g.strokeStyle = P.light; g.lineWidth = 3;
  g.beginPath(); g.ellipse(sx - 1, sy - 1, 5.5, 7, 0, 0, TAU); g.stroke();
}

function cageFront(g, st, P, state, flip, ckey, res, rq, dq) {
  const live = st.shake > 0.001;
  const sst = { ...st, rust: rq, dim: dq };
  if (live) frontBodyBars(g, st, P, true);
  blitCage(g, cageCache(`front${live ? '' : '+bars'}|${ckey}`, res, (cg) => frontStatic(cg, sst, P, !live)));
  // the door
  const dp = doorParams(st);
  drawDoor(g, st, P, dp);
  // padlock on the lock-jamb staple
  drawPadlockOnCage(g, st, P, dp);
  // occupant's fingers wrapped around the bars
  if (state.grips && state.grips.length) drawGrips(g, st, state, P, dp, flip);
  // sign
  drawSign(g, st, P, flip);
}

function drawHinges(g, st, P) {
  const broken = smoothstep(0.55, 0.95, st.rust);
  for (const [Y, isBottom] of [[HINGE_TOP_Y, false], [HINGE_BOT_Y, true]]) {
    const [hx, hy] = proj(HX - 3, Y, HZ + 2);
    if (isBottom && broken > 0.5) {
      // snapped lower hinge: a stub on the jamb
      g.fillStyle = P.base; g.strokeStyle = P.line; g.lineWidth = 2.4;
      g.beginPath(); g.roundRect(hx - 5.5, hy - 6, 11, 7, 2); g.fill(); g.stroke();
      g.strokeStyle = rgba(P.flake, 0.9); g.lineWidth = 2;
      g.beginPath(); g.moveTo(hx - 4, hy + 2); g.lineTo(hx - 1, hy + 4); g.lineTo(hx + 2, hy + 1.5); g.lineTo(hx + 4.5, hy + 3.5); g.stroke();
      continue;
    }
    g.fillStyle = P.base; g.strokeStyle = P.line; g.lineWidth = 2.6;
    g.beginPath(); g.roundRect(hx - 6.5, hy - 13, 13, 26, 4); g.fill(); g.stroke();
    g.strokeStyle = rgba(P.hi, 0.7); g.lineWidth = 2;
    g.beginPath(); g.moveTo(hx - 2.5, hy - 9); g.lineTo(hx - 2.5, hy + 9); g.stroke();
    g.strokeStyle = P.line; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(hx - 6.5, hy); g.lineTo(hx + 6.5, hy); g.stroke();
  }
}

function drawDoor(g, st, P, dp) {
  const N = 8;
  const rail = (Yf) => {
    const pts = [];
    for (let i = 0; i <= N; i++) { const s = i / N; pts.push(doorPt(dp, s, Yf(s))); }
    return pts;
  };
  const stile = (s, Y0, Y1) => {
    const pts = [];
    for (let i = 0; i <= 4; i++) pts.push(doorPt(dp, s, lerp(Y0, Y1, i / 4)));
    return pts;
  };
  const archY = (s) => DOOR_TOP + DOOR_ARCH * Math.sin(Math.PI * s);
  // door rattle: the free side of the door shivers in its frame
  const rat = st.shake * (1 - st.door * 0.5);
  const dShake = (pts, k) => (rat > 0 ? pts.map((p, i) => [p[0] + rat * 2.2 * vnoise(st.t * 19 + k, 55) * Math.sin(Math.PI * i / (pts.length - 1)), p[1]]) : pts);
  // edge-on darkening as the door swings toward camera
  const edgeDark = clamp(Math.abs(Math.cos(dp.alpha)) < 0.35 ? (0.35 - Math.abs(Math.cos(dp.alpha))) : 0) * 0.8;
  strokeBar(g, dShake(stile(0.5, DOOR_BOT, archY(0.5)), 2), P, 5.5, edgeDark, 61, st.rust);
  strokeRing(g, dShake(rail(() => DOOR_MID), 3), P, 5, edgeDark, 62, st.rust);
  strokeRing(g, dShake(rail(() => DOOR_BOT), 4), P, 6.5, edgeDark, 63, st.rust);
  strokeRing(g, dShake(rail(archY), 5), P, 6.5, edgeDark, 64, st.rust);
  strokeBar(g, stile(0, DOOR_BOT, DOOR_TOP), P, 7.5, edgeDark, 65, st.rust);
  strokeBar(g, dShake(stile(1, DOOR_BOT, DOOR_TOP), 6), P, 7.5, edgeDark, 66, st.rust);
  // hasp loop on the free stile (the padlock goes through it when locked)
  const h = doorPt(dp, 1, LOCK_Y);
  g.strokeStyle = P.line; g.lineWidth = 6;
  g.beginPath(); g.ellipse(h[0] + 3, h[1], 6, 7.5, 0, 0, TAU); g.stroke();
  g.strokeStyle = P.light; g.lineWidth = 3;
  g.beginPath(); g.ellipse(h[0] + 3, h[1], 6, 7.5, 0, 0, TAU); g.stroke();
}

function drawPadlockOnCage(g, st, P, dp) {
  const [sx, sy] = proj(LOCK_X, LOCK_Y, LOCK_Z);
  const open = 1 - st.locked;
  const swing = st.shake * 0.38 * vnoise(st.t * 9, 61) + Math.sin(st.t * 1.3) * 0.015;
  const ang = -0.5 * ease.outBack(clamp(open)) + swing;
  drawPadlock(g, sx, sy - 4, ang, open, P, st.rust);
}

/** Padlock: hung from (x,y) (top of shackle), rotated by ang, open 0..1 (shackle popped). Local size ~36x52. */
function drawPadlock(g, x, y, ang, open, P, rust) {
  g.save();
  g.translate(x, y);
  g.rotate(ang);
  const drop = open * 9;
  // shackle (steel U)
  const sh = (col, w) => {
    g.strokeStyle = col; g.lineWidth = w; g.lineCap = 'butt';
    g.beginPath();
    g.moveTo(-10, 22);
    g.lineTo(-10, 10);
    g.arc(0, 10, 10, Math.PI, 0);
    g.lineTo(10, 22 - (open > 0.3 ? 4 : 0));
    g.stroke();
  };
  sh(P.line, 8.5);
  sh(P.light, 5);
  g.strokeStyle = rgba(P.hi, 0.75); g.lineWidth = 1.5;
  g.beginPath(); g.arc(0, 10, 10, Math.PI * 1.05, Math.PI * 1.5); g.stroke();
  // body
  g.translate(0, drop);
  const by = 19, bw = 36, bh = 30;
  const gb = g.createLinearGradient(-bw / 2, by, bw / 2, by + bh);
  gb.addColorStop(0, P.brassHi); gb.addColorStop(0.35, P.brass); gb.addColorStop(1, P.brassDk);
  g.fillStyle = gb; g.strokeStyle = P.line; g.lineWidth = 2.8;
  g.beginPath(); g.roundRect(-bw / 2, by, bw, bh, 7); g.fill(); g.stroke();
  // keyhole
  g.fillStyle = P.line;
  circle(g, 0, by + 12, 3.6); g.fill();
  g.beginPath(); g.moveTo(-2.4, by + 13); g.lineTo(2.4, by + 13); g.lineTo(3.2, by + 22); g.lineTo(-3.2, by + 22); g.closePath(); g.fill();
  g.fillStyle = 'rgba(255,255,255,0.55)';
  g.beginPath(); g.roundRect(-bw / 2 + 4, by + 3, 8, 4, 2); g.fill();
  if (rust > 0.3) {
    g.fillStyle = rgba(P.pit, clamp((rust - 0.3) * 1.4) * 0.6);
    ellipse(g, 8, by + 22, 6, 3.5); g.fill();
    ellipse(g, -10, by + 9, 3.5, 2.5); g.fill();
  }
  g.restore();
}

function drawGrips(g, st, state, P, dp, flip) {
  const col = state.gripColor || '#b9a6ea', line = state.gripLine || '#3d2c66';
  const gs = state.gripScale ?? 1;
  // candidate front bars: [x at grip height] for fixed front bars and the closed door's bars
  for (const gp of state.grips) {
    const p = typeof gp === 'string' ? anchorLocal(gp, flip) : gp;
    if (!p) continue;
    // grips are cage-local (unmirrored) like CAGE_ANCHORS; the cage transform applies the flip
    const gx = p[0], gy = p[1];
    let best = null, bd = 1e9;
    for (let i = 0; i < FIXED.length; i++) {
      const th = FIXED[i];
      if (Math.cos(th) < 0) continue;
      const [X, Z] = barXZ(th);
      const Y = -(gy - Z * CK);
      const u = clamp((Y - FLOOR_Y) / (TOP_Y - FLOOR_Y));
      const bx = X + barShake(st, i, 0.45 + 0.55 * Math.cos(th) ** 2) * Math.sin(Math.PI * u);
      if (Math.abs(bx - gx) < bd) { bd = Math.abs(bx - gx); best = bx; }
    }
    for (const s of [0, 0.5, 1]) {
      const Y = -(gy - DOOR_R * Math.cos(-DOOR_HALF + s * 2 * DOOR_HALF) * CK);
      const q = doorPt(dp, s, Y);
      if (Math.abs(q[0] - gx) < bd && Math.abs(q[1] - gy) < 20) { bd = Math.abs(q[0] - gx); best = q[0]; }
    }
    if (best == null || bd > 26) best = gx;
    g.fillStyle = col; g.strokeStyle = line; g.lineWidth = 2.2;
    for (const k of [-1, 0, 1]) {
      ellipse(g, best + 1, gy + k * 7.2 * gs, 7.8 * gs, 4.4 * gs, -0.12);
      g.fill(); g.stroke();
    }
    g.fillStyle = 'rgba(255,255,255,0.25)';
    for (const k of [-1, 0, 1]) { ellipse(g, best - 1.5, gy + k * 7.2 * gs - 1.5, 3.5 * gs, 1.6 * gs); g.fill(); }
  }
}

// ---- TIME-OUT sign (cached bitmap at 2x per rust/dim step)
const signCache = new Map();
const SIGN_W = 172, SIGN_H = 58;
function signBitmap(P, rustQ, dimQ) {
  const key = `${rustQ}|${dimQ}|${P.wood}`;
  let c = signCache.get(key);
  if (c) return c;
  const S = 2, pad = 10;
  c = createCanvas((SIGN_W + pad * 2) * S, (SIGN_H + pad * 2) * S);
  const g = c.getContext('2d');
  g.scale(S, S);
  g.translate(pad + SIGN_W / 2, pad + SIGN_H / 2);
  const rust = rustQ / 8;
  // plank (slightly irregular), chipped corner when weathered
  const w = SIGN_W / 2, h = SIGN_H / 2;
  g.beginPath();
  g.moveTo(-w + 6, -h);
  g.lineTo(w - 5, -h + 1);
  g.quadraticCurveTo(w, -h + 1, w, -h + 6);
  if (rust > 0.6) { g.lineTo(w, h - 14); g.lineTo(w - 9, h - 6); g.lineTo(w - 13, h); }
  else { g.lineTo(w + 1, h - 6); g.quadraticCurveTo(w + 1, h, w - 5, h); }
  g.lineTo(-w + 5, h + 1);
  g.quadraticCurveTo(-w, h + 1, -w, h - 5);
  g.lineTo(-w - 1, -h + 6);
  g.quadraticCurveTo(-w, -h, -w + 6, -h);
  g.closePath();
  const gw = g.createLinearGradient(0, -h, 0, h);
  gw.addColorStop(0, P.woodHi); gw.addColorStop(0.55, P.wood); gw.addColorStop(1, P.woodDk);
  g.fillStyle = gw; g.fill();
  g.strokeStyle = P.ink; g.lineWidth = 2.6; g.stroke();
  // grain
  g.save(); g.clip();
  g.strokeStyle = rgba(P.woodDk, 0.45); g.lineWidth = 1.3;
  for (const [yy, a, ph] of [[-15, 2, 0.3], [-3, 1.5, 1.7], [13, 2.2, 3.1]]) {
    g.beginPath();
    for (let xx = -w; xx <= w; xx += 8) { const yv = yy + Math.sin(xx * 0.05 + ph) * a; if (xx === -w) g.moveTo(xx, yv); else g.lineTo(xx, yv); }
    g.stroke();
  }
  g.fillStyle = rgba(P.woodDk, 0.55);
  ellipse(g, -w * 0.55, 10, 6, 2.2); g.fill();
  if (rust > 0.6) {
    g.strokeStyle = rgba(P.ink, 0.7); g.lineWidth = 1.4;
    g.beginPath(); g.moveTo(w - 30, -h); g.lineTo(w - 36, -h + 9); g.lineTo(w - 33, -h + 16); g.stroke();
  }
  g.restore();
  // nail holes
  for (const sx of [-1, 1]) { g.fillStyle = P.ink; circle(g, sx * (w - 12), -h + 9, 3); g.fill(); }
  // lettering
  g.fillStyle = rgba(P.ink, 1 - rust * 0.35);
  g.font = '40px "Patrick Hand"';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.save();
  g.rotate(-0.025);
  g.fillText('TIME-OUT', 1, 4);
  g.restore();
  if (dimQ > 0) {
    g.globalCompositeOperation = 'source-atop';
    g.fillStyle = rgba('#0d0b1c', dimQ / 10 * 0.82);
    g.fillRect(-w - pad, -h - pad, SIGN_W + pad * 2, SIGN_H + pad * 2);
  }
  if (signCache.size > 60) signCache.clear();
  signCache.set(key, c);
  return c;
}

function drawSign(g, st, P, flip) {
  const rustQ = Math.round(st.rust * 8), dimQ = Math.round(st.dim * 10);
  const bmp = signBitmap(P, rustQ, dimQ);
  const broken = smoothstep(0.7, 1, st.rust);
  const hangY = -SIGN_HANG_Y;
  const swing = Math.sin(st.t * 0.9) * 0.02 + st.shake * 0.11 * vnoise(st.t * 6.5, 71);
  const L = 58; // string drop to plank top
  g.save();
  g.translate(0, hangY);
  g.scale(flip, 1); // keep lettering readable when the cage is mirrored
  g.rotate(swing + broken * 0.12);
  const holeL = [-(SIGN_W / 2 - 12), L + 9 - SIGN_H / 2 + SIGN_H / 2];
  // plank transform: rotate about the left hole when the right string has snapped
  const plankRot = broken * 0.42;
  const px = 0, py = L + SIGN_H / 2;
  const rot = (p) => {
    const dx = p[0] - holeL[0], dy = p[1] - holeL[1];
    const c = Math.cos(plankRot), s = Math.sin(plankRot);
    return [holeL[0] + dx * c - dy * s, holeL[1] + dx * s + dy * c];
  };
  const hl = rot([-(SIGN_W / 2 - 12), L + 9]);
  const hr = rot([SIGN_W / 2 - 12, L + 9]);
  g.strokeStyle = P.rope; g.lineWidth = 2.4; g.lineCap = 'round';
  g.beginPath(); g.moveTo(0, 0); g.lineTo(hl[0], hl[1]); g.stroke();
  if (broken < 0.5) { g.beginPath(); g.moveTo(0, 0); g.lineTo(hr[0], hr[1]); g.stroke(); }
  else {
    // snapped string: two frayed stubs
    g.beginPath(); g.moveTo(0, 0); g.lineTo(9, 16); g.stroke();
    g.beginPath(); g.moveTo(hr[0], hr[1]); g.lineTo(hr[0] + 3, hr[1] - 11); g.stroke();
  }
  // plank
  const c = rot([px, py]);
  g.translate(c[0], c[1]);
  g.rotate(plankRot);
  const pad = 10;
  g.drawImage(bmp, -SIGN_W / 2 - pad, -SIGN_H / 2 - pad, SIGN_W + pad * 2, SIGN_H + pad * 2);
  g.restore();
}

// =====================================================================================
//                                       THE NOTEBOOK
// =====================================================================================
export const NOTEBOOK_SIZE = { width: 220, height: 290, spreadWidth: 440 };
const NB_W = 220, NB_H = 290, NB_RES = 2.5;
const nbCache = {};

const NB_PALETTES = {
  // default: faded sky-blue board with a red cloth spine (reads well on the warm desk)
  blue: { cover: '#79a6d2', coverDk: '#4f7aa8', coverHi: '#a9cdf0', tape: '#c4574a', line: '#2a3350' },
  // matches the small held notebook drawn by src/chars/self.mjs (drawSelfNotebook)
  gold: { cover: '#f2d488', coverDk: '#d9b464', coverHi: '#fbe9b4', tape: '#c99d4e', line: '#6a4a2a' },
};
const NB = {
  ...NB_PALETTES.blue,
  label: '#fbf3dc', paper: '#f8f0dc', paperDk: '#e6d8b8', rule: '#9fbfe0', margin: '#e88a8a',
  pencil: '#3b4470', ink: '#2c3566',
};
export const NOTEBOOK_PALETTES = Object.keys(NB_PALETTES);

// crayon helpers (only used while building cached bitmaps)
function jitterPts(pts, amp, seed) {
  return pts.map((p, i) => [p[0] + (hrand(i, seed) - 0.5) * amp, p[1] + (hrand(i, seed + 1) - 0.5) * amp]);
}
function crayonLine(g, pts, color, w, seed = 1, passes = 3, alpha = 0.7) {
  g.lineCap = 'round'; g.lineJoin = 'round';
  for (let p = 0; p < passes; p++) {
    const q = jitterPts(pts, w * 0.45, seed * 31 + p * 7);
    g.strokeStyle = rgba(color, alpha * (p === 0 ? 1 : 0.6));
    g.lineWidth = w * (p === 0 ? 1 : 0.7);
    g.beginPath();
    g.moveTo(q[0][0], q[0][1]);
    for (let i = 1; i < q.length; i++) {
      const m = [(q[i - 1][0] + q[i][0]) / 2, (q[i - 1][1] + q[i][1]) / 2];
      g.quadraticCurveTo(q[i - 1][0], q[i - 1][1], m[0], m[1]);
    }
    g.lineTo(q[q.length - 1][0], q[q.length - 1][1]);
    g.stroke();
  }
}
/** crayon scribble fill inside the current path (call after building a path) */
function crayonFill(g, pathFn, color, bbox, seed = 1, spacing = 4.2, angle = -0.5, alpha = 0.55, w = 3.2) {
  g.save();
  pathFn(); g.clip();
  g.fillStyle = rgba(color, alpha * 0.45);
  pathFn(); g.fill();
  const [x0, y0, x1, y1] = bbox;
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, R = Math.hypot(x1 - x0, y1 - y0) / 2 + 4;
  g.translate(cx, cy); g.rotate(angle);
  g.strokeStyle = rgba(color, alpha); g.lineWidth = w; g.lineCap = 'round';
  g.beginPath();
  let k = 0;
  for (let yy = -R; yy <= R; yy += spacing) {
    const j = (hrand(k++, seed) - 0.5) * spacing * 0.6;
    if (k % 2) { g.moveTo(-R, yy + j); g.lineTo(R, yy + j + spacing * 0.5); }
    else { g.moveTo(R, yy + j); g.lineTo(-R, yy + j + spacing * 0.5); }
  }
  g.stroke();
  g.restore();
}
function crayonText(g, text, x, y, size, color, rot = 0, font = 'Caveat', weight = '700') {
  g.save();
  g.translate(x, y); g.rotate(rot);
  g.font = `${weight} ${size}px "${font}"`;
  g.textBaseline = 'alphabetic';
  g.fillStyle = rgba(color, 0.9);
  g.fillText(text, 0, 0);
  g.fillStyle = rgba(color, 0.35);
  g.fillText(text, 0.7, 0.6);
  g.restore();
}

/** little crayon Fear: lavender bean with huge eyes */
function crayonFear(g, cx, cy, s, seed, armTo = null) {
  const body = () => {
    g.beginPath();
    g.ellipse(cx, cy - 34 * s, 30 * s, 28 * s, 0, 0, TAU); // head
    g.moveTo(cx - 16 * s, cy - 12 * s);
    g.quadraticCurveTo(cx - 24 * s, cy + 14 * s, cx - 10 * s, cy + 18 * s);
    g.lineTo(cx + 10 * s, cy + 18 * s);
    g.quadraticCurveTo(cx + 24 * s, cy + 14 * s, cx + 16 * s, cy - 12 * s);
    g.closePath();
  };
  crayonFill(g, body, '#a98ee6', [cx - 32 * s, cy - 64 * s, cx + 32 * s, cy + 20 * s], seed, 3.6 * s, -0.6, 0.6, 2.6 * s);
  crayonLine(g, Array.from({ length: 17 }, (_, i) => { const a = (i / 16) * TAU; return [cx + Math.cos(a) * 30 * s, cy - 34 * s + Math.sin(a) * 28 * s]; }), '#5b3fa8', 2.4 * s, seed + 1, 2, 0.85);
  crayonLine(g, [[cx - 15 * s, cy - 10 * s], [cx - 22 * s, cy + 12 * s], [cx - 10 * s, cy + 18 * s], [cx + 10 * s, cy + 18 * s], [cx + 22 * s, cy + 12 * s], [cx + 15 * s, cy - 10 * s]], '#5b3fa8', 2.4 * s, seed + 2, 2, 0.85);
  // tuft
  crayonLine(g, [[cx + 2 * s, cy - 61 * s], [cx + 4 * s, cy - 74 * s], [cx + 14 * s, cy - 76 * s], [cx + 12 * s, cy - 68 * s]], '#5b3fa8', 2.4 * s, seed + 3, 2, 0.85);
  // huge eyes
  for (const ex of [-12, 12]) {
    g.fillStyle = '#ffffff';
    ellipse(g, cx + ex * s, cy - 38 * s, 11 * s, 13 * s); g.fill();
    g.strokeStyle = rgba('#2a2050', 0.85); g.lineWidth = 2 * s;
    ellipse(g, cx + ex * s, cy - 38 * s, 11 * s, 13 * s); g.stroke();
    g.fillStyle = '#2a2050';
    circle(g, cx + ex * s + 3 * s, cy - 41 * s, 4.6 * s); g.fill();
  }
  // worried mouth
  crayonLine(g, [[cx - 8 * s, cy - 16 * s], [cx, cy - 20 * s], [cx + 8 * s, cy - 16 * s]], '#2a2050', 2 * s, seed + 4, 2, 0.9);
  // legs
  crayonLine(g, [[cx - 8 * s, cy + 18 * s], [cx - 9 * s, cy + 36 * s]], '#5b3fa8', 2.6 * s, seed + 5, 2, 0.85);
  crayonLine(g, [[cx + 8 * s, cy + 18 * s], [cx + 9 * s, cy + 36 * s]], '#5b3fa8', 2.6 * s, seed + 6, 2, 0.85);
  // arms
  crayonLine(g, [[cx + 18 * s, cy - 2 * s], [cx + 30 * s, cy + 6 * s]], '#5b3fa8', 2.6 * s, seed + 7, 2, 0.85);
  if (armTo) {
    const [ax, ay] = armTo;
    crayonLine(g, [[cx - 20 * s, cy - 6 * s], [lerp(cx - 20 * s, ax, 0.5) - 6 * s, lerp(cy - 6 * s, ay, 0.5)], [ax, ay]], '#5b3fa8', 2.8 * s, seed + 8, 2, 0.9);
    g.fillStyle = rgba('#a98ee6', 0.95); circle(g, ax, ay, 4.5 * s); g.fill();
    g.strokeStyle = rgba('#5b3fa8', 0.9); g.lineWidth = 1.6 * s; g.stroke();
  } else crayonLine(g, [[cx - 18 * s, cy - 2 * s], [cx - 30 * s, cy + 8 * s]], '#5b3fa8', 2.6 * s, seed + 8, 2, 0.85);
}
/** crayon hooded dark figure */
function crayonVoid(g, cx, by, s, seed, stars = true) {
  const top = by - 190 * s;
  const shape = () => {
    g.beginPath();
    g.moveTo(cx - 44 * s, by);
    g.quadraticCurveTo(cx - 46 * s, by - 100 * s, cx - 30 * s, top + 40 * s);
    g.quadraticCurveTo(cx - 24 * s, top, cx, top - 4 * s);
    g.quadraticCurveTo(cx + 24 * s, top, cx + 30 * s, top + 40 * s);
    g.quadraticCurveTo(cx + 46 * s, by - 100 * s, cx + 44 * s, by);
    g.closePath();
  };
  crayonFill(g, shape, '#2a2a52', [cx - 48 * s, top - 6 * s, cx + 48 * s, by], seed, 3.6 * s, 0.7, 0.8, 3.2 * s);
  crayonFill(g, shape, '#1b1838', [cx - 48 * s, top - 6 * s, cx + 48 * s, by], seed + 9, 5 * s, -0.5, 0.45, 2.6 * s);
  // hood opening: black face
  g.fillStyle = rgba('#0c0a18', 0.92);
  ellipse(g, cx, top + 34 * s, 16 * s, 20 * s); g.fill();
  crayonLine(g, [[cx - 44 * s, by], [cx - 46 * s, by - 100 * s], [cx - 30 * s, top + 40 * s], [cx, top - 4 * s], [cx + 30 * s, top + 40 * s], [cx + 46 * s, by - 100 * s], [cx + 44 * s, by]], '#14122a', 2.6 * s, seed + 3, 2, 0.8);
  if (stars) {
    for (const [dx, dy, r] of [[-20, 80, 6], [16, 112, 5], [-8, 150, 6.5], [22, 60, 4.5]]) {
      g.fillStyle = '#f2c53d';
      starPath(g, cx + dx * s, top + dy * s, r * s); g.fill();
      g.strokeStyle = rgba('#a8780f', 0.8); g.lineWidth = 1 * s; g.stroke();
    }
  }
}
function starPath(g, x, y, r) {
  g.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = (i / 10) * TAU - Math.PI / 2;
    const rr = i % 2 ? r * 0.45 : r;
    const px = x + Math.cos(a) * rr, py = y + Math.sin(a) * rr;
    if (i === 0) g.moveTo(px, py); else g.lineTo(px, py);
  }
  g.closePath();
}
function heartPath(g, x, y, s) {
  g.beginPath();
  g.moveTo(x, y + 6 * s);
  g.bezierCurveTo(x - 10 * s, y - 2 * s, x - 6 * s, y - 10 * s, x, y - 4 * s);
  g.bezierCurveTo(x + 6 * s, y - 10 * s, x + 10 * s, y - 2 * s, x, y + 6 * s);
  g.closePath();
}

function nbCanvas() {
  const c = createCanvas(Math.ceil(NB_W * NB_RES), Math.ceil(NB_H * NB_RES));
  const g = c.getContext('2d');
  g.scale(NB_RES, NB_RES);
  return [c, g];
}

function buildCover(pal) {
  const [c, g] = nbCanvas();
  const NB = { ...NB_BASE(), ...pal };
  const W = NB_W, H = NB_H;
  // cover board
  g.beginPath(); g.roundRect(0, 0, W, H, [3, 12, 12, 3]);
  const gc = g.createLinearGradient(0, 0, W, H);
  gc.addColorStop(0, NB.coverHi); gc.addColorStop(0.35, NB.cover); gc.addColorStop(1, NB.coverDk);
  g.fillStyle = gc; g.fill();
  g.save(); g.clip();
  // worn corners + scuffs
  for (const [x, y, r] of [[W, 0, 22], [W, H, 26], [0, H, 16]]) {
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, 'rgba(240,240,230,0.55)'); gr.addColorStop(1, 'rgba(240,240,230,0)');
    g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  // faint mug ring
  g.strokeStyle = 'rgba(90,60,40,0.16)'; g.lineWidth = 3;
  g.beginPath(); g.arc(W * 0.78, H * 0.2, 26, 0.4, TAU - 0.9); g.stroke();
  // cloth spine tape
  g.fillStyle = NB.tape; g.fillRect(0, 0, 30, H);
  g.fillStyle = 'rgba(255,255,255,0.18)'; g.fillRect(4, 0, 5, H);
  g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(26, 0, 4, H);
  g.restore();
  g.strokeStyle = NB.line; g.lineWidth = 2.6;
  g.beginPath(); g.roundRect(0, 0, W, H, [3, 12, 12, 3]); g.stroke();
  // paper label, slightly crooked
  g.save();
  g.translate(W * 0.56, 84); g.rotate(-0.035);
  g.fillStyle = 'rgba(0,0,0,0.15)'; g.beginPath(); g.roundRect(-84, -42, 172, 88, 8); g.fill();
  g.fillStyle = NB.label; g.beginPath(); g.roundRect(-86, -45, 172, 86, 8); g.fill();
  g.strokeStyle = 'rgba(60,60,90,0.45)'; g.lineWidth = 1.5; g.stroke();
  g.strokeStyle = 'rgba(140,170,210,0.55)'; g.lineWidth = 1;
  for (const yy of [-6, 20]) { g.beginPath(); g.moveTo(-78, yy); g.lineTo(78, yy); g.stroke(); }
  g.textAlign = 'center';
  crayonText(g, 'My Feelings', 0, -10, 41, NB.ink, 0.02);
  // underline squiggle
  crayonLine(g, [[-62, 2], [-30, 6], [0, 2], [30, 6], [62, 1]], '#d9534f', 2.4, 3, 2, 0.75);
  crayonText(g, 'a story by me', 4, 30, 22, NB.pencil, -0.01, 'Caveat', '600');
  g.restore();
  // doodles: Fear + the dark hooded one with gold stars, a heart, little stars
  crayonVoid(g, 168, 268, 0.6, 21, true);
  crayonFear(g, 92, 236, 0.85, 31);
  g.fillStyle = rgba('#e0465a', 0.85); heartPath(g, 52, 160, 1.4); g.fill();
  g.strokeStyle = rgba('#a42638', 0.8); g.lineWidth = 1.2; g.stroke();
  for (const [x, y, r] of [[200, 150, 6], [130, 164, 4.5], [60, 270, 5]]) {
    g.fillStyle = '#f2c53d'; starPath(g, x, y, r); g.fill();
    g.strokeStyle = rgba('#a8780f', 0.7); g.lineWidth = 1; g.stroke();
  }
  return c;
}

function linedPage(g, W, H, left) {
  g.beginPath(); g.roundRect(0, 0, W, H, left ? [10, 2, 2, 10] : [2, 10, 10, 2]);
  const gp = g.createLinearGradient(left ? W : 0, 0, left ? 0 : W, 0);
  gp.addColorStop(0, NB.paperDk); gp.addColorStop(0.12, NB.paper); gp.addColorStop(1, NB.paper);
  g.fillStyle = gp; g.fill();
  g.save(); g.clip();
  g.strokeStyle = rgba(NB.rule, 0.6); g.lineWidth = 1;
  for (let yy = 46; yy < H - 8; yy += 27) { g.beginPath(); g.moveTo(0, yy); g.lineTo(W, yy); g.stroke(); }
  g.strokeStyle = rgba(NB.margin, 0.55); g.lineWidth = 1.2;
  const mx = left ? 28 : 22;
  g.beginPath(); g.moveTo(mx, 0); g.lineTo(mx, H); g.stroke();
  // spine shading
  const gs = g.createLinearGradient(left ? W : 0, 0, left ? W - 26 : 26, 0);
  gs.addColorStop(0, 'rgba(90,60,30,0.28)'); gs.addColorStop(1, 'rgba(90,60,30,0)');
  g.fillStyle = gs; g.fillRect(0, 0, W, H);
  g.restore();
}

function buildLeftPage() {
  const [c, g] = nbCanvas();
  const W = NB_W, H = NB_H;
  linedPage(g, W, H, true);
  const lines = [
    ['Inside my head there', 0.0],
    ['is a control room.', -0.01],
    ['My Fear lives there.', 0.012],
    ['It keeps pulling', -0.008],
    ['the fire alarm!!', 0.015],
    ['A big dark one', 0.0],
    ['stands in the back.', -0.012],
    ['It never moves.', 0.01],
    ['Fear is scared of it.', -0.006],
  ];
  // title line
  lines.forEach(([txt, r], i) => {
    const y = 42 + i * 27;
    crayonText(g, txt, 34 + (i % 3) * 1.5, y - 3, 23, NB.pencil, r, 'Caveat', '600');
  });
  // a crossed-out word + a tiny heart in the margin
  g.strokeStyle = rgba(NB.pencil, 0.75); g.lineWidth = 1.6;
  g.beginPath(); g.moveTo(150, 152); g.lineTo(196, 146); g.stroke();
  g.fillStyle = rgba('#e0465a', 0.8); heartPath(g, 14, 104, 0.9); g.fill();
  return c;
}

function buildRightPage() {
  const [c, g] = nbCanvas();
  const W = NB_W, H = NB_H;
  linedPage(g, W, H, false);
  // the drawing: a crayon control room
  // back wall wash
  crayonFill(g, () => { g.beginPath(); g.rect(30, 26, 178, 196); }, '#8f86c9', [30, 26, 208, 222], 51, 7, 0.25, 0.28, 3);
  // floor line
  crayonLine(g, [[26, 222], [80, 220], [140, 223], [210, 221]], '#5a4a7a', 2.6, 52, 2, 0.8);
  // the dark hooded one in the back (right)
  crayonVoid(g, 174, 222, 0.88, 53, false);
  crayonText(g, '?', 196, 72, 26, '#2a2a52', 0.15);
  // fire alarm box on the left wall, with alarm marks
  crayonFill(g, () => { g.beginPath(); g.roundRect(40, 74, 30, 38, 4); }, '#e0303a', [40, 74, 70, 112], 54, 3.4, -0.4, 0.85, 2.8);
  crayonLine(g, [[40, 74], [70, 74], [70, 112], [40, 112], [40, 74]], '#a01822', 2.2, 55, 2, 0.85);
  g.fillStyle = rgba('#ffffff', 0.9); g.fillRect(50, 88, 10, 9);
  for (const [a, l] of [[-2.4, 14], [-1.8, 16], [-1.2, 14]]) {
    const ox = 55 + Math.cos(a) * 24, oy = 70 + Math.sin(a) * 18;
    crayonLine(g, [[ox, oy], [ox + Math.cos(a) * l, oy + Math.sin(a) * l]], '#e0303a', 2.4, 56 + l, 2, 0.85);
  }
  // Fear pulling the alarm (arm up to the box)
  crayonFear(g, 98, 190, 0.95, 57, [60, 106]);
  // console at the bottom with coloured buttons
  crayonFill(g, () => { g.beginPath(); g.roundRect(26, 232, 186, 34, 6); }, '#d98a3a', [26, 232, 212, 266], 59, 3.6, 0.3, 0.7, 2.8);
  crayonLine(g, [[26, 232], [212, 232], [212, 266], [26, 266], [26, 232]], '#8a4a1a', 2.2, 60, 2, 0.8);
  [['#ffd23d', 48], ['#4aa3ff', 80], ['#ff5a4a', 112], ['#5fd39a', 144], ['#ffd23d', 176]].forEach(([col, x], i) => {
    g.fillStyle = rgba(col, 0.95); circle(g, x, 249, 7); g.fill();
    g.strokeStyle = rgba('#5a3a1a', 0.6); g.lineWidth = 1.2; g.stroke();
  });
  // labels
  crayonText(g, 'FEAR', 24, 204, 19, '#5b3fa8', -0.06);
  crayonLine(g, [[58, 196], [66, 192], [74, 190]], '#5b3fa8', 1.6, 61, 1, 0.8);
  crayonText(g, 'AAAA!!', 84, 66, 23, '#e0303a', -0.08, 'Caveat', '700');
  // gold star sticker
  g.fillStyle = '#f2c53d'; starPath(g, 196, 32, 13); g.fill();
  g.strokeStyle = rgba('#a8780f', 0.85); g.lineWidth = 1.4; g.stroke();
  return c;
}

const NB_BASE = () => NB;
function notebookBitmaps(palette) {
  const pal = NB_PALETTES[palette] ? palette : 'blue';
  if (!nbCache.left) {
    ensureFonts();
    nbCache.left = buildLeftPage();
    nbCache.right = buildRightPage();
  }
  if (!nbCache['cover_' + pal]) nbCache['cover_' + pal] = buildCover(NB_PALETTES[pal]);
  return { cover: nbCache['cover_' + pal], left: nbCache.left, right: nbCache.right, pal: { ...NB, ...NB_PALETTES[pal] } };
}

/**
 * Old childlike notebook "My Feelings".
 * state: { open 0..1, flat 0..1 (0 = facing camera, 1 = lying on the desk), rot (rad), dim 0..1, shadow bool,
 *          palette 'blue' (default) | 'gold' (matches self.mjs's held notebook), t }
 */
export function drawNotebook(g, x, y, scale = 1, state = {}) {
  const B = notebookBitmaps(state.palette);
  const NB = B.pal;
  const open = clamp(state.open ?? 0);
  const flat = clamp(state.flat ?? 0);
  const dim = clamp(state.dim ?? 0);
  const W = NB_W, H = NB_H;
  const k = ease.sine(open);
  const spine = lerp(-W / 2, 0, k);     // spine x, recentres as the book opens
  const a = open * Math.PI;              // cover leaf angle
  const cw = Math.cos(a);                // signed projected leaf width (+ right / - left)
  g.save();
  g.translate(x, y);
  if (state.rot) g.rotate(state.rot);
  g.scale(scale, scale * lerp(1, 0.5, flat));
  // shadow
  if (state.shadow !== false) {
    const sx0 = Math.min(spine - W * Math.max(0, -cw) - 5, spine) - 4, sx1 = spine + W + 8;
    g.fillStyle = `rgba(30,15,10,${0.28 * (1 - dim * 0.5)})`;
    g.beginPath(); g.roundRect(sx0 + 6, -H / 2 + 8 + flat * 6, sx1 - sx0, H + 4, 12); g.fill();
    g.fillStyle = `rgba(30,15,10,${0.14 * (1 - dim * 0.5)})`;
    g.beginPath(); g.roundRect(sx0 + 2, -H / 2 + 3, sx1 - sx0 + 8, H + 12, 16); g.fill();
  }
  // back cover (peeks around the right-hand pages)
  g.fillStyle = NB.coverDk; g.strokeStyle = NB.line; g.lineWidth = 2.4;
  g.beginPath(); g.roundRect(spine, -H / 2 - 3, W + 5, H + 7, [3, 10, 10, 3]); g.fill(); g.stroke();
  // page block edges (right)
  g.fillStyle = '#e9dfc6';
  g.beginPath(); g.roundRect(spine + 2, -H / 2 + 1, W, H, [2, 9, 9, 2]); g.fill();
  g.strokeStyle = 'rgba(120,100,70,0.5)'; g.lineWidth = 1;
  for (const o of [2, 4]) { g.beginPath(); g.moveTo(spine + W + o - 1, -H / 2 + 8); g.lineTo(spine + W + o - 1, H / 2 - 4); g.stroke(); }
  // right page (revealed under the cover)
  if (open > 0.01) {
    g.drawImage(B.right, spine, -H / 2, W, H);
    // shadow of the lifting leaf on the right page
    if (cw > 0) {
      const sh = g.createLinearGradient(spine + W * cw, 0, spine + W * cw + 40, 0);
      sh.addColorStop(0, `rgba(40,20,10,${0.3 * Math.sin(a)})`); sh.addColorStop(1, 'rgba(40,20,10,0)');
      g.fillStyle = sh; g.fillRect(spine + W * cw, -H / 2, 40, H);
    }
  }
  // cover leaf
  const lw = Math.abs(cw) * W;
  if (lw > 0.5) {
    const lift = Math.sin(a) * 10; // the leaf rises toward camera: grows a touch taller mid-flip
    if (cw >= 0) g.drawImage(B.cover, spine, -H / 2 - lift / 2, lw, H + lift);
    else {
      // turned leaf: inside of the front cover (blue border) carrying the left-hand page
      const bw = 5 * -cw;
      g.fillStyle = NB.cover; g.strokeStyle = NB.line; g.lineWidth = 2.4;
      g.beginPath(); g.roundRect(spine - lw - bw, -H / 2 - lift / 2 - 3, lw + bw, H + lift + 7, [10, 3, 3, 10]); g.fill(); g.stroke();
      g.drawImage(B.left, spine - lw, -H / 2 - lift / 2, lw, H + lift);
    }
    // flip shading
    const shadeA = Math.sin(a) * 0.35;
    if (shadeA > 0.01) {
      g.fillStyle = `rgba(30,20,40,${shadeA})`;
      g.fillRect(cw >= 0 ? spine : spine - lw, -H / 2 - lift / 2, lw, H + lift);
    }
  }
  // spine crease when open
  if (open > 0.5) {
    g.strokeStyle = 'rgba(80,50,30,0.35)'; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(spine, -H / 2 + 2); g.lineTo(spine, H / 2 - 2); g.stroke();
  }
  if (dim > 0.01) {
    g.fillStyle = `rgba(13,11,28,${dim * 0.8})`;
    g.beginPath(); g.roundRect(Math.min(spine - W * Math.max(0, -cw), spine) - 6, -H / 2 - 6, W * (1 + Math.max(0, -cw)) + 14, H + 14, 10); g.fill();
  }
  g.restore();
}

// =====================================================================================
//                                       THE DESK LAMP
// =====================================================================================
// An enamel articulated desk lamp. Origin = centre of the base where it sits on the desk.
// facing 1: shade points down-right; -1: down-left. Height ~265 at scale 1.
const LAMP_C = { enamel: '#d39a3c', enamelHi: '#f6cf7a', enamelDk: '#8a5a22', line: '#3a2414', metal: '#6b5a4a', metalHi: '#cdb89a', bulb: '#fff6d8', inner: '#f9e2a8' };
const LAMP_GEO = { pivot: [0, -36], elbow: [-34, -168], head: [58, -224], headAng: 0.95, shadeLen: 84, mouthR: 46 };
const lampMouth = () => {
  const [hx, hy] = LAMP_GEO.head, a = LAMP_GEO.headAng;
  return [hx + Math.cos(a) * LAMP_GEO.shadeLen, hy + Math.sin(a) * LAMP_GEO.shadeLen];
};
/** lamp-local anchors (facing 1, scale 1; mirror x for facing -1) */
export const LAMP_ANCHORS = { base: [0, 0], head: LAMP_GEO.head, bulb: lampMouth(), lightDir: [Math.cos(LAMP_GEO.headAng), Math.sin(LAMP_GEO.headAng)], top: [0, -265] };

/**
 * state: { on 0..1, facing 1|-1, cone bool|0..1 (light-cone strength, default 1), glow bool (halo, default true), t }
 */
export function drawDeskLamp(g, x, y, scale = 1, state = {}) {
  const on = clamp(state.on ?? 1);
  const facing = state.facing === -1 ? -1 : 1;
  const t = state.t || 0;
  const C = LAMP_C;
  const flick = on > 0 ? 1 + 0.012 * vnoise(t * 3.1, 81) : 1;
  g.save();
  g.translate(x, y);
  g.scale(scale * facing, scale);
  const [px, py] = LAMP_GEO.pivot, [ex, ey] = LAMP_GEO.elbow, [hx, hy] = LAMP_GEO.head;
  const a = LAMP_GEO.headAng;
  const [mx, my] = lampMouth();
  // light cone (behind the lamp body)
  const coneA = state.cone === false ? 0 : typeof state.cone === 'number' ? state.cone : 1;
  if (on > 0.01 && coneA > 0.01) {
    const nx = -Math.sin(a), ny = Math.cos(a);
    const R = LAMP_GEO.mouthR, L = 300;
    const dx = Math.cos(a), dy = Math.sin(a);
    const gc = g.createLinearGradient(mx, my, mx + dx * L, my + dy * L);
    gc.addColorStop(0, `rgba(255,214,140,${0.22 * on * flick * coneA})`);
    gc.addColorStop(1, 'rgba(255,214,140,0)');
    g.fillStyle = gc;
    g.beginPath();
    g.moveTo(mx + nx * R * 0.9, my + ny * R * 0.9);
    g.lineTo(mx + dx * L + nx * R * 2.6, my + dy * L + ny * R * 2.6);
    g.lineTo(mx + dx * L - nx * R * 2.6, my + dy * L - ny * R * 2.6);
    g.lineTo(mx - nx * R * 0.9, my - ny * R * 0.9);
    g.closePath(); g.fill();
  }
  // base
  groundShadow(g, 6, 2, 62, 0.35);
  const gb = g.createLinearGradient(-50, -20, 50, 4);
  gb.addColorStop(0, C.enamelHi); gb.addColorStop(0.45, C.enamel); gb.addColorStop(1, C.enamelDk);
  g.fillStyle = gb; g.strokeStyle = C.line; g.lineWidth = 3;
  g.beginPath();
  g.moveTo(-50, -4);
  g.quadraticCurveTo(-48, -26, -14, -30);
  g.lineTo(14, -30);
  g.quadraticCurveTo(48, -26, 50, -4);
  g.quadraticCurveTo(0, 8, -50, -4);
  g.closePath(); g.fill(); g.stroke();
  g.strokeStyle = rgba(C.enamelHi, 0.8); g.lineWidth = 2;
  g.beginPath(); g.moveTo(-38, -16); g.quadraticCurveTo(-30, -24, -12, -26); g.stroke();
  // arms: twin rods
  const rod = (x0, y0, x1, y1, off) => {
    const L = Math.hypot(x1 - x0, y1 - y0), nx = -(y1 - y0) / L * off, ny = (x1 - x0) / L * off;
    for (const s of [-1, 1]) {
      g.strokeStyle = C.line; g.lineWidth = 7; g.lineCap = 'round';
      g.beginPath(); g.moveTo(x0 + nx * s, y0 + ny * s); g.lineTo(x1 + nx * s, y1 + ny * s); g.stroke();
      g.strokeStyle = C.metal; g.lineWidth = 3.6;
      g.beginPath(); g.moveTo(x0 + nx * s, y0 + ny * s); g.lineTo(x1 + nx * s, y1 + ny * s); g.stroke();
      g.strokeStyle = rgba(C.metalHi, 0.8); g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(x0 + nx * s - 1, y0 + ny * s - 1); g.lineTo(x1 + nx * s - 1, y1 + ny * s - 1); g.stroke();
    }
  };
  rod(px, py, ex, ey, 5);
  rod(ex, ey, hx, hy, 5);
  // spring
  g.strokeStyle = rgba(C.metalHi, 0.9); g.lineWidth = 1.6;
  g.beginPath();
  for (let i = 0; i <= 14; i++) {
    const u = i / 14, sx = lerp(px - 8, ex + 10, u), sy = lerp(py - 22, ey + 34, u);
    if (i === 0) g.moveTo(sx, sy); else g.lineTo(sx + (i % 2 ? 4 : -4), sy);
  }
  g.stroke();
  // joints
  for (const [jx, jy, r] of [[px, py, 9], [ex, ey, 9.5], [hx, hy, 8]]) {
    g.fillStyle = C.enamel; g.strokeStyle = C.line; g.lineWidth = 2.6;
    circle(g, jx, jy, r); g.fill(); g.stroke();
    g.fillStyle = C.line; circle(g, jx, jy, 2.4); g.fill();
  }
  // shade: cone from head toward the mouth
  g.save();
  g.translate(hx, hy);
  g.rotate(a);
  const L = LAMP_GEO.shadeLen, R = LAMP_GEO.mouthR;
  // inner (lit) ellipse of the mouth
  const shadeBody = () => {
    g.beginPath();
    g.moveTo(-6, -11);
    g.quadraticCurveTo(8, -16, 20, -17);
    g.lineTo(L, -R);
    g.lineTo(L, R);
    g.lineTo(20, 17);
    g.quadraticCurveTo(8, 16, -6, 11);
    g.closePath();
  };
  const gs = g.createLinearGradient(0, -R, 0, R);
  gs.addColorStop(0, C.enamelHi); gs.addColorStop(0.4, C.enamel); gs.addColorStop(1, C.enamelDk);
  g.fillStyle = gs; g.strokeStyle = C.line; g.lineWidth = 3;
  shadeBody(); g.fill(); g.stroke();
  // top cap
  g.fillStyle = C.enamelDk; ellipse(g, -2, 0, 9, 13); g.fill(); g.stroke();
  // highlight streak
  g.strokeStyle = rgba('#fff3cf', 0.7); g.lineWidth = 3; g.lineCap = 'round';
  g.beginPath(); g.moveTo(26, -14); g.lineTo(L - 8, -R + 9); g.stroke();
  // mouth rim
  const gm = g.createRadialGradient(L, 0, 2, L, 0, R);
  gm.addColorStop(0, mixColor(C.inner, '#fffdf2', on));
  gm.addColorStop(1, mixColor('#7a5a3a', C.inner, on * 0.9));
  g.fillStyle = gm;
  ellipse(g, L, 0, 12, R); g.fill();
  g.strokeStyle = C.line; g.lineWidth = 3; g.stroke();
  // bulb peeking out
  g.fillStyle = mixColor('#d8cfb8', C.bulb, on);
  ellipse(g, L + 4, 0, 9, 18); g.fill();
  g.restore();
  // halo around the mouth
  if (on > 0.01 && state.glow !== false) {
    const gr = g.createRadialGradient(mx, my, 4, mx, my, 120);
    gr.addColorStop(0, `rgba(255,236,190,${0.75 * on * flick})`);
    gr.addColorStop(0.25, `rgba(255,205,130,${0.3 * on * flick})`);
    gr.addColorStop(1, 'rgba(255,190,110,0)');
    g.fillStyle = gr;
    g.fillRect(mx - 120, my - 120, 240, 240);
  }
  g.restore();
}
