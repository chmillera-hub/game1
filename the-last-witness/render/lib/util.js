// Math, easing, deterministic noise and colour helpers shared by the whole renderer.
'use strict';

const TAU = Math.PI * 2;
const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const invLerp = (a, b, v) => (b === a ? 0 : (v - a) / (b - a));
const remap = (v, a, b, c, d) => lerp(c, d, clamp(invLerp(a, b, v)));
const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const smoother = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = (t) => Math.pow(clamp(t), 3);
const easeInOut = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const pulse = (t, a, b, fade = 0.15) => smooth(invLerp(a, a + fade, t)) * (1 - smooth(invLerp(b - fade, b, t)));

// integer hash -> [0,1)
function hash(n) {
  n = (n | 0) ^ 0x9e3779b9;
  n = Math.imul(n ^ (n >>> 16), 0x85ebca6b);
  n = Math.imul(n ^ (n >>> 13), 0xc2b2ae35);
  n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}
function hash2(a, b) { return hash(Math.imul(a | 0, 73856093) ^ Math.imul(b | 0, 19349663)); }

// seeded PRNG (mulberry32)
function rng(seed) {
  let a = (seed | 0) + 0x6d2b79f5;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// smooth 1D value noise in [-1,1]
function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash2(i, seed) * 2 - 1, b = hash2(i + 1, seed) * 2 - 1;
  return lerp(a, b, smoother(f));
}
// fractal 1D noise, used for idle body/head drift
function fbm1(x, seed = 0, oct = 3) {
  let v = 0, amp = 0.5, f = 1, norm = 0;
  for (let o = 0; o < oct; o++) { v += amp * noise1(x * f, seed + o * 17); norm += amp; amp *= 0.5; f *= 2.03; }
  return v / norm;
}
function noise2(x, y, seed = 0) {
  const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy;
  const h = (i, j) => hash2(i + seed * 131, j) * 2 - 1;
  const sx = smoother(fx), sy = smoother(fy);
  return lerp(lerp(h(ix, iy), h(ix + 1, iy), sx), lerp(h(ix, iy + 1), h(ix + 1, iy + 1), sx), sy);
}

// ---- colour ----
function hexToRgb(h) {
  if (Array.isArray(h)) return h;
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function rgba(c, a = 1) {
  const [r, g, b] = hexToRgb(c);
  return `rgba(${r | 0},${g | 0},${b | 0},${clamp(a)})`;
}
function mix(c1, c2, t) {
  const a = hexToRgb(c1), b = hexToRgb(c2);
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
}
function shade(c, k) { // k<0 darker, k>0 lighter
  return k < 0 ? mix(c, [0, 0, 0], -k) : mix(c, [255, 255, 255], k);
}
// multiply a colour by a light colour (tints without changing hue wholesale)
function lit(c, light, amount = 1) {
  const a = hexToRgb(c), l = hexToRgb(light);
  return [lerp(a[0], a[0] * l[0] / 255, amount), lerp(a[1], a[1] * l[1] / 255, amount), lerp(a[2], a[2] * l[2] / 255, amount)];
}
function css(c, a = 1) { return rgba(c, a); }

// Critically damped spring following a piecewise-constant target. keys = [{t, v}] sorted by t.
// Precomputes position/velocity at every key so any time can be evaluated statelessly
// (frames are rendered out of order by parallel workers). w ~ 4 / settle-seconds.
class Track {
  constructor(keys, w = 8) {
    this.w = w;
    this.t = []; this.x = []; this.v = []; this.T = [];
    if (!keys.length) keys = [{ t: 0, v: 0 }];
    let x = keys[0].v, v = 0, last = keys[0].t, target = keys[0].v;
    for (let i = 0; i < keys.length; i++) {
      const k = keys[i];
      const dt = Math.max(0, k.t - last);
      const e = x - target, B = v + w * e, ex = Math.exp(-w * dt);
      x = target + (e + B * dt) * ex;
      v = (v - w * B * dt) * ex;
      target = k.v; last = k.t;
      this.t.push(k.t); this.x.push(x); this.v.push(v); this.T.push(target);
    }
  }
  at(t) {
    const ts = this.t;
    if (t <= ts[0]) return this.x[0];
    let lo = 0, hi = ts.length - 1;
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (ts[m] <= t) lo = m; else hi = m - 1; }
    const dt = t - ts[lo], w = this.w, T = this.T[lo];
    const e = this.x[lo] - T, B = this.v[lo] + w * e;
    return T + (e + B * dt) * Math.exp(-w * dt);
  }
}

module.exports = {
  TAU, clamp, lerp, invLerp, remap, smooth, smoother, easeOut, easeIn, easeInOut, pulse,
  hash, hash2, rng, noise1, fbm1, noise2, hexToRgb, rgba, mix, shade, lit, css, Track,
};
