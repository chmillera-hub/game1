// Shared math, easing, deterministic noise, colour and path helpers.
'use strict';

const TAU = Math.PI * 2;
const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const invLerp = (a, b, v) => clamp((v - a) / (b - a));
const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const smoother = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const easeInOut = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const easeOut = (t) => { t = clamp(t); return 1 - Math.pow(1 - t, 3); };
const easeIn = (t) => { t = clamp(t); return t * t * t; };
const easeOutBack = (t) => { t = clamp(t); const c = 1.4; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
// smooth 0->1->0 pulse between a and b with ramp r
const window01 = (t, a, b, r = 0.3) => smooth((t - a) / r) * (1 - smooth((t - (b - r)) / r));

// ---- deterministic hash noise ----
function hash(n) {
  n = (n << 13) ^ n;
  return 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0;
}
function hash2(i, j) { return hash((i | 0) * 73856093 ^ (j | 0) * 19349663); }
function seeded(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}
// 1D value noise, smooth, range ~[-1,1]
function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash2(i, seed), b = hash2(i + 1, seed);
  return lerp(a, b, smoother(f));
}
// fractal 1D noise
function fbm1(x, seed = 0, oct = 3) {
  let v = 0, amp = 0.5, fr = 1, norm = 0;
  for (let o = 0; o < oct; o++) { v += amp * noise1(x * fr, seed + o * 31); norm += amp; amp *= 0.5; fr *= 2.03; }
  return v / norm;
}

// ---- colour ----
function hexToRgb(h) {
  if (typeof h !== 'string') return h;
  if (h.startsWith('rgb')) {
    const m = h.match(/[\d.]+/g).map(Number);
    return { r: m[0], g: m[1], b: m[2], a: m[3] === undefined ? 1 : m[3] };
  }
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const n = parseInt(h.slice(0, 6), 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255, a: h.length === 8 ? parseInt(h.slice(6), 16) / 255 : 1 };
}
const rgba = (c, a = 1) => { const o = hexToRgb(c); return `rgba(${o.r | 0},${o.g | 0},${o.b | 0},${(a * o.a).toFixed(3)})`; };
function mix(c1, c2, t) {
  const a = hexToRgb(c1), b = hexToRgb(c2);
  return `rgb(${lerp(a.r, b.r, t) | 0},${lerp(a.g, b.g, t) | 0},${lerp(a.b, b.b, t) | 0})`;
}
const shade = (c, amt) => (amt < 0 ? mix(c, '#000000', -amt) : mix(c, '#ffffff', amt));
// multiply-tint a colour by another (lighting), amount 0..1
function tint(c, t, amt) {
  const a = hexToRgb(c), b = hexToRgb(t);
  const m = { r: (a.r * b.r) / 255, g: (a.g * b.g) / 255, b: (a.b * b.b) / 255 };
  return `rgb(${lerp(a.r, m.r, amt) | 0},${lerp(a.g, m.g, amt) | 0},${lerp(a.b, m.b, amt) | 0})`;
}

// ---- paths ----
// Closed smooth path through points (Catmull-Rom -> bezier). pts: [[x,y],...]
function smoothClosed(ctx, pts, tension = 1) {
  const n = pts.length;
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
    const k = tension / 6;
    ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k,
      p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k, p2[0], p2[1]);
  }
  ctx.closePath();
}
// Open smooth path through points
function smoothOpen(ctx, pts, tension = 1, move = true) {
  const n = pts.length;
  if (move) ctx.moveTo(pts[0][0], pts[0][1]); else ctx.lineTo(pts[0][0], pts[0][1]);
  for (let i = 0; i < n - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n - 1, i + 2)];
    const k = tension / 6;
    ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k,
      p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k, p2[0], p2[1]);
  }
}
// Tapered limb outline between two points with radii r1, r2 (capsule)
function capsule(ctx, x1, y1, r1, x2, y2, r2) {
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1e-6;
  const a = Math.atan2(dy, dx);
  const s = Math.asin(clamp((r1 - r2) / L, -1, 1));
  ctx.moveTo(x1 + r1 * Math.cos(a + Math.PI / 2 + s), y1 + r1 * Math.sin(a + Math.PI / 2 + s));
  ctx.arc(x1, y1, r1, a + Math.PI / 2 + s, a - Math.PI / 2 - s);
  ctx.arc(x2, y2, r2, a - Math.PI / 2 - s, a + Math.PI / 2 + s);
  ctx.closePath();
}
const rot = (x, y, a) => [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)];

// two-bone IK: from root (x0,y0) to target (tx,ty) with lengths l1,l2; bend = +1/-1
function ik2(x0, y0, tx, ty, l1, l2, bend) {
  let dx = tx - x0, dy = ty - y0;
  let d = Math.hypot(dx, dy);
  const maxd = (l1 + l2) * 0.999, mind = Math.abs(l1 - l2) + 1e-3;
  if (d > maxd) { dx *= maxd / d; dy *= maxd / d; d = maxd; }
  if (d < mind) { dx *= mind / d; dy *= mind / d; d = mind; }
  const a = Math.atan2(dy, dx);
  const cosA = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1);
  const a1 = a - bend * Math.acos(cosA);
  const ex = x0 + l1 * Math.cos(a1), ey = y0 + l1 * Math.sin(a1);
  return { ex, ey, hx: x0 + dx, hy: y0 + dy, a1, a2: Math.atan2(y0 + dy - ey, x0 + dx - ex) };
}

module.exports = {
  TAU, clamp, lerp, invLerp, smooth, smoother, easeInOut, easeOut, easeIn, easeOutBack, window01,
  hash, hash2, seeded, noise1, fbm1, hexToRgb, rgba, mix, shade, tint,
  smoothClosed, smoothOpen, capsule, rot, ik2,
};
