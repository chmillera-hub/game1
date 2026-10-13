// Shared articulated hand for Consciousness/Self, Fear and the other emotions: a palm, separate fingers and a
// thumb, built in 3D (hand-local) and projected, so the thumb is always where anatomy puts it for the hand's
// chirality and how far the wrist is rolled. Drawn as ONE silhouette with a single outer outline; where one
// part overlaps another (curled fingers, the thumb across the palm) the boundary is a soft, darker skin tone
// that blends into the surrounding skin — never a hard line or a small outlined oval.
//
//   drawHand(g, style, opts)
//     drawn at the current transform: origin = wrist, opts.ang = direction the hand points (radians)
//     style : makeHandStyle({...}) — proportions (HUMAN | TOON3), size (wrist → middle fingertip, px), colours
//     opts  : { ang, shape, roll, chir, curl, spread, pitch, alpha }
//       shape  'rest' | 'open' | 'palm' | 'wave' | 'flat' | 'drape' | 'cup' | 'point' | 'fist' | 'grip' | 'pinch' |
//              'claw' | 'hold' (a flat object between fingers and thumb) | 'edge' (fingers hooked over an edge)
//              or a pose object { f: [[mcp,pip,dip] x fingers], spread, thumb: [abd, opp, flex] }
//       roll   how the hand is turned about its own long axis (radians or a view name):
//              'back' 0 (back of the hand toward camera) · 'palm' PI · 'thumb' PI/2 (thumb side toward camera)
//              · 'pinky' -PI/2. In between = three-quarter views.
//       palmDir  instead of roll: where the palm faces, [x right, y down, z toward the camera] in the drawing frame
//              (e.g. [0,0,-1] palm on the face/chest, [0,0,1] palm to the viewer, [-side,0,0] hanging by the side)
//       chir   -1 = the character's RIGHT hand, +1 = LEFT hand (as drawn on screen; a mirrored character mirrors it)
//       holding true when an object fills the grip (no fist filler)
//       whiten 0..1 knuckles paling with a tight grip
//       only   draw a subset of parts: ['thumb'], ['palm','finger'], ... (layering around a held object: e.g. the
//              palm and fingers behind a clipboard, then the thumb over its front edge)
//       pitch  radians: tip the fingers toward (+) / away from (-) the camera (foreshortening)
//       curl   0..1 extra curl blended toward a fist;  spread: override finger spread
//
// Hand-local 3D: x toward the fingertips, y toward the thumb, z out of the BACK of the hand. Flexion turns the
// fingers toward -z (the palm side). After roll (about x) and pitch (about y) the screen position of a point is
// (u, v) = (x', chir·y'), its depth toward the camera z'.

import { clamp, lerp, mixColor, rgba, shade } from './engine.mjs';

const V = {
  back: 0, palm: Math.PI, thumb: Math.PI / 2, pinky: -Math.PI / 2,
};

// ---------------------------------------------------------------- proportions (units: straight hand ≈ 100 long)
export const HUMAN = {
  name: 'human',
  len: 100,
  // palm outline in the palm plane (z = 0), counter-clockwise from the wrist on the pinky side; thumb side = +y
  palm: [[0, -13], [10, -17.5], [30, -20.5], [44, -19.5], [49, -14.5], [51.5, -4], [51, 6], [49.5, 15.5], [45, 20], [33, 21.5],
    [20, 21], [9, 17], [1, 12]],
  T: 12,            // palm thickness
  wristW: 13,       // half width at the wrist
  fingers: [        // knuckle [x, y], phalanx lengths, radii [knuckle, pip, dip, tip], spread weight
    { base: [48.5, 13], len: [21, 13, 10], r: [5.7, 5.2, 4.7, 4.1], sp: 1.0 },     // index
    { base: [50.5, 3.8], len: [24, 15, 10.5], r: [5.9, 5.4, 4.9, 4.3], sp: 0.33 }, // middle
    { base: [49, -5.6], len: [22, 14, 10], r: [5.5, 5.0, 4.5, 4.0], sp: -0.4 },    // ring
    { base: [44.5, -14], len: [17, 10.5, 9], r: [4.8, 4.4, 4.0, 3.6], sp: -1.15 }, // pinky
  ],
  thumb: { base: [7, 13, -4], len: [19, 15, 12], r: [8.4, 6.6, 5.6, 4.9] },
  nails: true,
  creases: true,
};

// chubby cartoon hand: three fingers + thumb (Fear and the other emotions)
export const TOON3 = {
  name: 'toon',
  len: 100,
  palm: [[0, -14], [8, -19], [26, -23], [38, -21], [44, -13], [46, 0], [44, 13], [38, 21], [26, 23], [12, 21], [2, 14]],
  T: 14,
  wristW: 13,
  fingers: [
    { base: [41, 12], len: [21, 13, 10], r: [9.2, 8.8, 8.4, 8.0], sp: 1.0 },
    { base: [44, 0], len: [23, 14, 11], r: [9.4, 9.0, 8.6, 8.2], sp: 0.0 },
    { base: [40, -12], len: [20, 12, 10], r: [9.0, 8.6, 8.2, 7.8], sp: -1.0 },
  ],
  thumb: { base: [9, 14, -4], len: [16, 14, 11], r: [10, 9.4, 8.8, 8.3] },
  nails: false,
  creases: false,
};

// ---------------------------------------------------------------- poses
// f: per finger [mcp, pip, dip] flexion (radians, toward the palm), index first.  spread: fan angle (radians)
// thumb: [abd (away from the index in the palm plane), opp (swing across, in front of the palm), flex (curl)]
const P4 = (mcp, pip, dip, inc = 0) => [0, 1, 2, 3].map((i) => [mcp + inc * i, pip + inc * i * 1.2, dip + inc * i * 0.6]);
export const HAND_POSES = {
  rest: { f: P4(0.32, 0.5, 0.28, 0.07), spread: 0.05, thumb: [0.3, 0.42, 0.28] },
  open: { f: P4(0.12, 0.2, 0.12, 0.04), spread: 0.15, thumb: [0.62, 0.2, 0.12] },
  palm: { f: P4(0.02, 0.05, 0.04, 0.02), spread: 0.24, thumb: [0.9, 0.05, 0.05] },
  wave: { f: P4(0.0, 0.04, 0.03, 0.02), spread: 0.3, thumb: [1.0, 0.0, 0.05] },
  flat: { f: P4(0.0, 0.03, 0.03, 0.01), spread: 0.035, thumb: [0.22, 0.15, 0.08] },
  drape: { f: P4(0.3, 0.42, 0.3, 0.04), spread: 0.06, thumb: [0.32, 0.25, 0.15] },
  cup: { f: P4(0.5, 0.5, 0.25, 0.05), spread: 0.06, thumb: [0.6, 0.55, 0.2] },
  claw: { f: P4(0.35, 0.95, 0.6, 0.03), spread: 0.2, thumb: [0.7, 0.3, 0.5] },
  point: { f: [[0.04, 0.06, 0.04], [1.5, 1.72, 0.9], [1.52, 1.75, 0.92], [1.5, 1.72, 0.9]], spread: 0.03, thumb: [0.12, 0.92, 0.55] },
  fist: { f: P4(1.48, 1.72, 0.92, 0.0), spread: 0, thumb: [0.12, 0.95, 0.62] },
  grip: { f: P4(1.0, 1.42, 0.78, 0.03), spread: 0, thumb: [0.3, 0.72, 0.35] },
  pinch: { f: [[0.55, 0.85, 0.42], [0.95, 1.3, 0.7], [1.1, 1.45, 0.75], [1.2, 1.5, 0.78]], spread: 0.02, thumb: [0.45, 0.8, 0.28] },
  // a flat object (board, book cover, letter) between the straight-ish fingers and the opposed thumb
  hold: { f: P4(0.16, 0.22, 0.12, 0.03), spread: 0.03, thumb: [0.35, 0.95, 0.12] },
  // fingers hooked over the edge of a flat object (a book's side, a ledge): bent at the knuckles, then straight
  edge: { f: P4(1.3, 0.3, 0.12, 0.02), spread: 0.02, thumb: [0.4, 0.55, 0.12] },
};
const DEFAULT_ROLL = {
  rest: 1.15, open: 0.55, palm: V.palm, wave: V.palm, flat: 0.1, drape: 0.25, cup: 2.5, claw: 0.3,
  point: 0.95, fist: 0.8, grip: 0.7, pinch: 0.9, hold: 0.2, edge: 1.2,
};
export const handDefaultRoll = (shape) => DEFAULT_ROLL[shape] ?? 0.6;

/** a pose part-way between two (named or pose objects), e.g. a fist opening into a pointing finger */
export function blendHand(a, b, k) {
  const A = typeof a === 'object' ? a : HAND_POSES[a], B = typeof b === 'object' ? b : HAND_POSES[b];
  k = clamp(k);
  if (k <= 0) return A;
  if (k >= 1) return B;
  return {
    f: A.f.map((f, i) => f.map((v, j) => lerp(v, B.f[i][j], k))),
    spread: lerp(A.spread, B.spread, k),
    thumb: A.thumb.map((v, j) => lerp(v, B.thumb[j], k)),
  };
}

// ---------------------------------------------------------------- style
/** style = proportions + size (px, wrist → middle fingertip) + colours { skin, light, shade, line } */
export function makeHandStyle(model, size, colors, lineW = 2.4) {
  return { model, size, k: size / model.len, colors, lineW };
}

// ---------------------------------------------------------------- 3D helpers
const nrm = (v) => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; };
const addv = (a, b, s = 1) => [a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
/** rotate v about unit axis k by angle a (Rodrigues) */
function rotAxis(v, k, a) {
  const c = Math.cos(a), s = Math.sin(a), d = k[0] * v[0] + k[1] * v[1] + k[2] * v[2];
  const kx = cross(k, v);
  return [v[0] * c + kx[0] * s + k[0] * d * (1 - c), v[1] * c + kx[1] * s + k[1] * d * (1 - c), v[2] * c + kx[2] * s + k[2] * d * (1 - c)];
}

function resolvePose(shape, opts) {
  let P = typeof shape === 'object' && shape ? shape : HAND_POSES[shape] || HAND_POSES.rest;
  const curl = clamp(opts.curl || 0);
  if (curl > 0) {
    const F = HAND_POSES.fist;
    P = {
      f: P.f.map((f, i) => f.map((v, j) => lerp(v, F.f[Math.min(i, 3)][j], curl))),
      spread: lerp(P.spread, 0, curl),
      thumb: P.thumb.map((v, j) => lerp(v, F.thumb[j], curl * 0.8)),
    };
  }
  if (opts.spread != null) P = { ...P, spread: opts.spread };
  return P;
}

/** joints of every digit in hand-local 3D */
function buildHand(M, P) {
  const nf = M.fingers.length;
  const digits = [];
  M.fingers.forEach((F, i) => {
    // toon (3 fingers) takes the index, middle and ring/pinky-average flexions
    const fi = nf === 4 ? i : [0, 1, 3][i];
    const fl = P.f[Math.min(fi, P.f.length - 1)];
    const fan = P.spread * F.sp;
    let dir = [Math.cos(fan), Math.sin(fan), 0];
    const axis = nrm([-Math.sin(fan), Math.cos(fan), 0]); // flexion axis (across the finger); +rotation → toward -z
    let p = [F.base[0], F.base[1], 0];
    const pts = [p];
    for (let j = 0; j < 3; j++) {
      dir = rotAxis(dir, axis, fl[j]);
      p = addv(p, dir, F.len[j]);
      pts.push(p);
    }
    digits.push({ pts, r: F.r, kind: 'finger', i });
  });
  // thumb: the metacarpal leaves the palm's thumb-side base, swings out in the palm plane (abd) and forward, in
  // front of the palm (opp); its phalanges curl toward the fingers — alongside the index when relaxed, across
  // the folded fingers in a fist
  const [abd, opp, flex] = P.thumb;
  const T = M.thumb;
  const th = 0.32 + 0.66 * abd;
  let dir = nrm([Math.cos(th), Math.sin(th) - 0.55 * opp, -(0.28 + 0.6 * opp)]);
  const fisty = clamp((P.f[0][0] + P.f[1][0]) / 3);
  const span = M.fingers[0].base[0];
  const target = [lerp(span * 1.22, span * 0.98, fisty), lerp(M.fingers[0].base[1] * 0.3, -2, fisty), lerp(-M.T * 0.55, -M.T * 2.4, fisty)];
  let p = [...T.base];
  const pts = [p];
  for (let j = 0; j < 3; j++) {
    if (j > 0) {
      const want = nrm([target[0] - p[0], target[1] - p[1], target[2] - p[2]]);
      const dot = clamp(dir[0] * want[0] + dir[1] * want[1] + dir[2] * want[2], -1, 1);
      const ang = Math.acos(dot);
      if (ang > 1e-3) {
        const ax = nrm(cross(dir, want));
        dir = rotAxis(dir, ax, Math.min(ang, (0.12 + 0.95 * flex) * (j === 1 ? 1 : 0.85)));
      }
    }
    p = addv(p, dir, T.len[j]);
    pts.push(p);
  }
  digits.push({ pts, r: T.r, kind: 'thumb' });
  return digits;
}

// ---------------------------------------------------------------- 2D helpers
/** convex hull (monotone chain) */
function hull(points) {
  const P = points.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (P.length < 3) return P;
  const crossZ = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const p of P) { while (lo.length >= 2 && crossZ(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
  for (let i = P.length - 1; i >= 0; i--) { const p = P[i]; while (up.length >= 2 && crossZ(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p); }
  up.pop(); lo.pop();
  return lo.concat(up);
}
/** smooth closed path through polygon midpoints (rounded corners) */
function roundPoly(g, pts, grow = 0, cx = 0, cy = 0) {
  const n = pts.length;
  const q = grow ? pts.map(([x, y]) => { const dx = x - cx, dy = y - cy, l = Math.hypot(dx, dy) || 1; return [x + dx / l * grow, y + dy / l * grow]; }) : pts;
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  let m = mid(q[n - 1], q[0]);
  g.moveTo(m[0], m[1]);
  for (let i = 0; i < n; i++) {
    const p = q[i], nx = q[(i + 1) % n];
    m = mid(p, nx);
    g.quadraticCurveTo(p[0], p[1], m[0], m[1]);
  }
  g.closePath();
}
/** tapered capsule chain (round ends) through 2D points with radii — appended to the current path */
function chainPath(g, pts, rs, grow = 0) {
  for (let i = 0; i < pts.length - 1; i++) capsule(g, pts[i][0], pts[i][1], rs[i] + grow, pts[i + 1][0], pts[i + 1][1], rs[i + 1] + grow);
}
function capsule(g, x1, y1, r1, x2, y2, r2) {
  const dx = x2 - x1, dy = y2 - y1, d = Math.hypot(dx, dy);
  if (d < Math.abs(r1 - r2) + 0.01) {
    const [x, y, r] = r1 > r2 ? [x1, y1, r1] : [x2, y2, r2];
    g.moveTo(x + r, y); g.arc(x, y, r, 0, Math.PI * 2);
    return;
  }
  const a = Math.atan2(dy, dx), b = Math.acos(clamp((r1 - r2) / d, -1, 1));
  g.moveTo(x1 + Math.cos(a + b) * r1, y1 + Math.sin(a + b) * r1);
  g.arc(x1, y1, r1, a + b, a - b + Math.PI * 2, false);
  g.arc(x2, y2, r2, a - b, a + b, false);
  g.closePath();
}

// ---------------------------------------------------------------- main
export function drawHand(g, style, opts = {}) {
  const M = style.model, k = style.k, col = style.colors;
  const P = resolvePose(opts.shape || 'rest', opts);
  const chir = opts.chir === -1 ? -1 : 1;
  let roll = opts.roll;
  if (typeof roll === 'string') roll = V[roll] ?? 0;
  if (roll == null && opts.palmDir) roll = rollForPalm(opts.ang || 0, chir, opts.palmDir);
  if (roll == null) roll = handDefaultRoll(typeof opts.shape === 'string' ? opts.shape : 'rest');
  const pitch = opts.pitch || 0;
  const cr = Math.cos(roll), sr = Math.sin(roll), cp = Math.cos(pitch), sp = Math.sin(pitch);
  // hand-local 3D → (u, v, depth)
  const proj = (p) => {
    // roll about x, then pitch about the screen-vertical axis of the hand (tips toward/away from camera)
    const y1 = p[1] * cr - p[2] * sr, z1 = p[1] * sr + p[2] * cr;
    const x2 = p[0] * cp - z1 * sp, z2 = p[0] * sp + z1 * cp;
    return [x2, chir * y1, z2];
  };

  const digits = buildHand(M, P);
  // palm slab: front and back faces of the palm outline, swept through its thickness → convex hull
  const palm3 = [];
  for (const [x, y] of M.palm) for (const z of [M.T / 2, -M.T / 2]) palm3.push(proj([x, y, z * (x < 6 ? 0.8 : 1)]));
  const palm2 = hull(palm3.map(([u, v]) => [u, v]));
  let pcx = 0, pcy = 0;
  for (const [u, v] of palm2) { pcx += u; pcy += v; }
  pcx /= palm2.length; pcy /= palm2.length;

  // parts with depth; a digit is one part (its segments union without seams)
  let parts = [{ kind: 'palm', depth: 0 }];
  for (const d of digits) {
    const pp = d.pts.map(proj);
    const depth = pp.slice(1).reduce((s, q) => s + q[2], 0) / (pp.length - 1);
    parts.push({ kind: d.kind, i: d.i, pts: pp.map(([u, v]) => [u, v]), z: pp.map((q) => q[2]), r: d.r, depth: depth + (d.kind === 'finger' ? 0.6 : 0) });
  }
  parts.sort((a, b) => a.depth - b.depth);
  // a subset (for layering around a held object): only: ['thumb'] | ['palm', 'finger'] ...
  const zs = parts.filter((p) => p.kind !== 'palm').map((p) => p.depth);   // shading range of the whole hand
  if (opts.only) parts = parts.filter((p) => opts.only.includes(p.kind));
  if (!parts.length) return;

  const ol = style.lineW / k;            // outline width in hand units
  const soft = Math.max(1.0, 1.05 / k);   // soft separation band
  const pathOf = (pt, grow, edge = false) => {
    if (pt.kind === 'palm') { roundPoly(g, palm2, grow, pcx, pcy); return; }
    if (edge) {
      // no edge where the digit grows out of the palm: start partway along the first phalanx
      const [a, b] = pt.pts;
      const q = [[lerp(a[0], b[0], 0.45), lerp(a[1], b[1], 0.45)], ...pt.pts.slice(1)];
      const r = [lerp(pt.r[0], pt.r[1], 0.45), ...pt.r.slice(1)];
      chainPath(g, q, r, grow);
    } else chainPath(g, pt.pts, pt.r, grow);
  };

  g.save();
  if (opts.alpha != null) g.globalAlpha *= clamp(opts.alpha);
  g.rotate(opts.ang || 0);
  g.scale(k, k);
  g.lineJoin = 'round';
  g.lineCap = 'round';

  // a closed fist has no hole: the folded fingers press into the palm (fill the gap behind everything)
  const fisty = clamp((P.f[1][0] + P.f[1][1] - 2.4) / 0.8);
  let filler = null;
  if (fisty > 0 && !opts.holding && !opts.only) {
    const all = [...palm2];
    for (const pt of parts) if (pt.kind !== 'palm') all.push(...pt.pts);
    filler = hull(all);
  }

  // pass 1: one silhouette outline for the whole hand
  g.fillStyle = col.line;
  g.beginPath();
  for (const pt of parts) pathOf(pt, ol);
  g.fill('nonzero');
  if (filler) {
    g.fillStyle = mixColor(col.shade, col.skin, 0.55);
    g.beginPath(); roundPoly(g, filler, -2, pcx, pcy); g.fill();
  }

  // pass 2: flat, depth-shaded parts back-to-front. A digit gets a soft darker-skin edge under its own fill, so
  // where it overlaps something behind it a thin soft band shows; the palm and the digits' roots have none.
  const zMin = Math.min(0, ...zs), zMax = Math.max(0, ...zs);
  const edgeCol = rgba(shade(col.skin, -0.3), 0.5);
  const showsBack = Math.cos(roll) * Math.cos(pitch) > 0.2;     // back of the hand faces the camera
  const showsPalm = Math.cos(roll) * Math.cos(pitch) < -0.2;
  for (const pt of parts) {
    const dk = zMax > zMin ? (pt.depth - zMin) / (zMax - zMin) : 1;   // 0 = farthest, 1 = nearest
    const base = mixColor(col.shade, col.skin, 0.5 + 0.5 * dk);
    if (pt.kind !== 'palm') { g.fillStyle = edgeCol; g.beginPath(); pathOf(pt, soft, true); g.fill(); }
    g.fillStyle = pt.kind === 'palm' && showsPalm ? mixColor(col.skin, col.light, 0.18) : base;
    g.beginPath(); pathOf(pt, 0); g.fill();
    if (pt.kind === 'palm') {
      if (showsPalm && M.creases) palmCreases(g, chir * (Math.cos(roll) < 0 ? -1 : 1), col, k);
      if (showsBack) knuckleLights(g, parts, col, k);
    } else if (pt.kind === 'finger' && M.nails && showsBack) nail(g, pt, col, k, roll, pitch);
  }

  // knuckles whitening with the grip (opts.whiten 0..1): soft pale light on the front-most knuckles, no outline
  if (opts.whiten > 0.01) {
    for (const pt of parts) {
      if (pt.kind !== 'finger') continue;
      // the joint nearest the camera of the first two (knuckle, middle joint)
      const j = pt.z[1] > pt.z[0] ? 1 : 0;
      const [x, y] = pt.pts[j], r = pt.r[j] * 1.05;
      const gw = g.createRadialGradient(x, y, 0, x, y, r);
      gw.addColorStop(0, rgba('#fff8f2', 0.75 * opts.whiten)); gw.addColorStop(1, rgba('#fff8f2', 0));
      g.fillStyle = gw;
      g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
    }
  }

  // pass 3: one soft light across the whole hand (from the screen's upper left), clipped to the silhouette
  const m = g.getTransform();
  const det = m.a * m.d - m.b * m.c || 1;
  // screen direction (-1,-1) (toward the light) in hand-local coordinates
  const lx = (-m.d + m.c) / det, ly = (m.b - m.a) / det, ll = Math.hypot(lx, ly) || 1;
  const ux = lx / ll, uy = ly / ll;
  let lo = Infinity, hi = -Infinity;
  for (const pt of parts) for (const [x, y] of pt.kind === 'palm' ? palm2 : pt.pts) { const d = x * ux + y * uy; lo = Math.min(lo, d); hi = Math.max(hi, d); }
  // (filled as the silhouette path itself — no clip: inside a scene's own clip Skia could drop a nested clip and paint
  // the whole gradient rectangle)
  const gr = g.createLinearGradient(ux * lo, uy * lo, ux * hi, uy * hi);
  gr.addColorStop(0, rgba(col.shade, 0.22)); gr.addColorStop(0.45, rgba(col.skin, 0)); gr.addColorStop(1, rgba(col.light, 0.38));
  g.beginPath();
  for (const pt of parts) pathOf(pt, 0);
  g.fillStyle = gr;
  g.fill('nonzero');
  g.restore();
}

function palmCreases(g, s, col, k) {
  // two soft creases: the heart line across the top of the palm and the curve around the thumb's mound
  const w = Math.max(1.0, 0.9 / k);
  const line = (x0, y0, cx, cy, x1, y1) => {
    const gr = g.createLinearGradient(x0, y0, x1, y1);
    const c = shade(col.skin, -0.3);
    gr.addColorStop(0, rgba(c, 0)); gr.addColorStop(0.3, rgba(c, 0.32)); gr.addColorStop(0.7, rgba(c, 0.32)); gr.addColorStop(1, rgba(c, 0));
    g.strokeStyle = gr; g.lineWidth = w;
    g.beginPath(); g.moveTo(x0, y0); g.quadraticCurveTo(cx, cy, x1, y1); g.stroke();
  };
  line(40, -17 * s, 34, 0, 41, 12 * s);
  line(14, 6 * s, 26, -2 * s, 38, 0);
}

function knuckleLights(g, parts, col, k) {
  for (const pt of parts) {
    if (pt.kind !== 'finger') continue;
    const [x, y] = pt.pts[0];
    const gr = g.createRadialGradient(x - 1, y, 0, x - 1, y, pt.r[0] * 0.9);
    gr.addColorStop(0, rgba(col.light, 0.35)); gr.addColorStop(1, rgba(col.light, 0));
    g.fillStyle = gr;
    g.beginPath(); g.arc(x - 1, y, pt.r[0] * 0.9, 0, Math.PI * 2); g.fill();
  }
}

function nail(g, pt, col, k, roll, pitch) {
  const a = pt.pts[2], b = pt.pts[3];
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
  // the nail faces the camera only while the last phalanx is not curled away
  if (L < 5 || pt.z[3] < pt.z[2] - 4) return;
  const r = pt.r[3];
  g.save();
  g.translate(a[0] + dx * 0.68, a[1] + dy * 0.68);
  g.rotate(Math.atan2(dy, dx));
  const gr = g.createLinearGradient(-L * 0.3, 0, L * 0.3, 0);
  gr.addColorStop(0, rgba(col.light, 0)); gr.addColorStop(0.35, rgba(mixColor(col.light, '#ffd9d0', 0.4), 0.55)); gr.addColorStop(1, rgba(col.light, 0.65));
  g.fillStyle = gr;
  g.beginPath(); g.ellipse(0, 0, L * 0.32, r * 0.6, 0, 0, Math.PI * 2); g.fill();
  g.restore();
}

/** wrist roll that turns the palm toward `palmDir` ([x right, y down, z toward camera] in the drawing frame) for a
 *  hand pointing along `ang` with chirality `chir` */
export function rollForPalm(ang, chir, d) {
  const ev = [-Math.sin(ang), Math.cos(ang)];
  return Math.atan2(chir * (d[0] * ev[0] + d[1] * ev[1]), -(d[2] || 0));
}

/** chirality of a hand: -1 = the character's right hand. side = -1 for the screen-left arm (facing 1);
 *  seen from behind the screen-left arm is the LEFT hand. */
export const handChir = (side, back = false) => (back ? -side : side);
