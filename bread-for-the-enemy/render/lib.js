// Core helpers: math, easing, noise, color, smooth paths.
'use strict';

const TAU = Math.PI * 2;
const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const invlerp = (a, b, v) => clamp((v - a) / (b - a));
const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const smoother = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = (t) => Math.pow(clamp(t), 3);
const easeInOut = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
// rises 0->1 between a and b
const ramp = (t, a, b) => smooth((t - a) / (b - a));
// pulse: up over [a,a+r], down over [b-r,b]
const window_ = (t, a, b, r) => Math.min(ramp(t, a, a + r), 1 - ramp(t, b - r, b));

// deterministic hash noise
function hash(n) {
  n = (n << 13) ^ n;
  return 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0;
}
function hash01(n) { return (hash(n | 0) + 1) * 0.5; }
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}
// smooth 1D value noise in [-1,1]
function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash(i * 7919 + seed * 104729), b = hash((i + 1) * 7919 + seed * 104729);
  const u = f * f * (3 - 2 * f);
  return a + (b - a) * u;
}
function fbm1(x, seed = 0, oct = 3) {
  let v = 0, amp = 0.5, f = 1;
  for (let i = 0; i < oct; i++) { v += amp * noise1(x * f, seed + i * 13); amp *= 0.5; f *= 2.03; }
  return v;
}

// ---------------------------------------------------------------- color
function hex2rgb(h) {
  if (Array.isArray(h)) return h;
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function rgb2hex(c) {
  return '#' + c.map((v) => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0')).join('');
}
function mix(a, b, t) {
  const A = hex2rgb(a), B = hex2rgb(b);
  return rgb2hex([lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t)]);
}
function rgba(c, a) {
  const C = hex2rgb(c);
  return `rgba(${Math.round(C[0])},${Math.round(C[1])},${Math.round(C[2])},${clamp(a).toFixed(4)})`;
}
function shade(c, k) { // k<1 darker, >1 lighter (toward white)
  if (k <= 1) return mix(c, '#000000', 1 - k);
  return mix(c, '#ffffff', k - 1);
}
function mul(a, b) { // multiply colors
  const A = hex2rgb(a), B = hex2rgb(b);
  return rgb2hex([A[0] * B[0] / 255, A[1] * B[1] / 255, A[2] * B[2] / 255]);
}

// ---------------------------------------------------------------- paths
// Catmull-Rom spline through points -> bezier commands on ctx (or Path2D)
function crPath(p, pts, closed = false, tension = 0.5) {
  const n = pts.length;
  if (n < 2) return;
  const get = (i) => {
    if (closed) return pts[(i + n) % n];
    return pts[Math.max(0, Math.min(n - 1, i))];
  };
  if (!closed) p.moveTo(pts[0][0], pts[0][1]);
  else p.moveTo(pts[0][0], pts[0][1]);
  const segs = closed ? n : n - 1;
  for (let i = 0; i < segs; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    const t = tension / 3 * 2;
    const c1 = [p1[0] + (p2[0] - p0[0]) * t / 2, p1[1] + (p2[1] - p0[1]) * t / 2];
    const c2 = [p2[0] - (p3[0] - p1[0]) * t / 2, p2[1] - (p3[1] - p1[1]) * t / 2];
    p.bezierCurveTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1]);
  }
  if (closed) p.closePath();
}
function fillSmooth(ctx, pts, style, closed = true, tension = 0.5) {
  ctx.beginPath(); crPath(ctx, pts, closed, tension); ctx.fillStyle = style; ctx.fill();
}
function strokeSmooth(ctx, pts, style, w, closed = false, tension = 0.5) {
  ctx.beginPath(); crPath(ctx, pts, closed, tension);
  ctx.strokeStyle = style; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
}
// sample a catmull-rom polyline into dense points
function sampleCR(pts, per = 8, closed = false) {
  const n = pts.length, out = [];
  const get = (i) => closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))];
  const segs = closed ? n : n - 1;
  for (let i = 0; i < segs; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    for (let k = 0; k < per; k++) {
      const t = k / per, t2 = t * t, t3 = t2 * t;
      const f = (a, b, c, d) => 0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  if (!closed) out.push(pts[n - 1]);
  return out;
}
// tapered stroke (calligraphic line): width profile w(t) along polyline
function taperStroke(ctx, pts, style, w0, w1, wMid = null, per = 6) {
  const s = sampleCR(pts, per, false);
  if (s.length < 2) return;
  const L = [], R = [];
  const n = s.length;
  for (let i = 0; i < n; i++) {
    const a = s[Math.max(0, i - 1)], b = s[Math.min(n - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1];
    const len = Math.hypot(dx, dy) || 1; dx /= len; dy /= len;
    const t = i / (n - 1);
    let w;
    if (wMid !== null) w = t < 0.5 ? lerp(w0, wMid, smooth(t * 2)) : lerp(wMid, w1, smooth((t - 0.5) * 2));
    else w = lerp(w0, w1, t);
    w *= 0.5;
    L.push([s[i][0] - dy * w, s[i][1] + dx * w]);
    R.push([s[i][0] + dy * w, s[i][1] - dx * w]);
  }
  ctx.beginPath();
  ctx.moveTo(L[0][0], L[0][1]);
  for (let i = 1; i < n; i++) ctx.lineTo(L[i][0], L[i][1]);
  for (let i = n - 1; i >= 0; i--) ctx.lineTo(R[i][0], R[i][1]);
  ctx.closePath();
  ctx.fillStyle = style; ctx.fill();
}
function ellipse(ctx, x, y, rx, ry, rot = 0) {
  ctx.beginPath(); ctx.ellipse(x, y, Math.max(0.01, rx), Math.max(0.01, ry), rot, 0, TAU);
}
function radial(ctx, x, y, r0, r1, stops) {
  const g = ctx.createRadialGradient(x, y, r0, x, y, r1);
  for (const [o, c] of stops) g.addColorStop(o, c);
  return g;
}
function linear(ctx, x0, y0, x1, y1, stops) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  for (const [o, c] of stops) g.addColorStop(o, c);
  return g;
}
function glow(ctx, x, y, r, color, a = 1) {
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = radial(ctx, x, y, 0, r, [[0, rgba(color, a)], [0.35, rgba(color, a * 0.35)], [1, rgba(color, 0)]]);
  ctx.fillRect(x - r, y - r, r * 2, r * 2);
  ctx.restore();
}

module.exports = {
  TAU, clamp, lerp, invlerp, smooth, smoother, easeOut, easeIn, easeInOut, ramp, window_,
  hash, hash01, rng, noise1, fbm1, hex2rgb, rgb2hex, mix, rgba, shade, mul,
  crPath, fillSmooth, strokeSmooth, sampleCR, taperStroke, ellipse, radial, linear, glow,
};
