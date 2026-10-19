'use strict';
// Math, easing, noise, colour and keyframe helpers shared by the rig and scenes.

const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const invLerp = (a, b, v) => clamp((v - a) / (b - a));
const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const smoother = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = (t) => Math.pow(clamp(t), 3);
const easeInOut = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
// Overshoot ease for snappy, alive motion (head whips, startle).
const easeBack = (t, s = 1.4) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; };
const EASE = { linear: (t) => clamp(t), smooth, smoother, out: easeOut, in: easeIn, inout: easeInOut, back: easeBack };

// Deterministic PRNG so every render of a frame is identical.
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}

// Smooth 1D value noise in [-1, 1].
function hash(n) { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash(i + seed * 57.3), b = hash(i + 1 + seed * 57.3);
  return (lerp(a, b, smoother(f)) * 2 - 1);
}
// Fractal noise: slow drift plus a little faster texture.
function fbm(x, seed = 0) {
  return noise1(x, seed) * 0.65 + noise1(x * 2.1, seed + 9) * 0.25 + noise1(x * 4.3, seed + 21) * 0.1;
}

// ---- colour ----
function hexToRgb(h) {
  if (Array.isArray(h)) return h;
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function rgbStr(c, a = 1) {
  if (typeof c === 'string') c = hexToRgb(c);
  a = Math.max(0, Math.min(1, a));
  return a >= 1 ? `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})` : `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a.toFixed(3)})`;
}
function mix(c1, c2, t) { const a = hexToRgb(c1), b = hexToRgb(c2); return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]; }
function shade(c, k) { const a = hexToRgb(c); return k >= 0 ? mix(a, [255, 255, 255], k) : mix(a, [0, 0, 0], -k); }
function col(c, a = 1) { return rgbStr(hexToRgb(c), a); }

// ---- keyframe tracks ----
// keys: [[t, value, ease?], ...] sorted by t. Values may be numbers or objects of numbers.
function sampleTrack(keys, t, defEase = 'inout') {
  if (!keys || keys.length === 0) return undefined;
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t < keys[i][0]) {
      const [t0, v0] = keys[i - 1];
      const [t1, v1, e] = keys[i];
      const u = EASE[e || defEase]((t - t0) / (t1 - t0));
      return mixValue(v0, v1, u);
    }
  }
  return keys[keys.length - 1][1];
}
function mixValue(a, b, u) {
  if (typeof a === 'number') return lerp(a, b, u);
  const out = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) {
    const va = a[k] ?? 0, vb = b[k] ?? 0;
    out[k] = typeof va === 'number' ? lerp(va, vb, u) : (u < 0.5 ? va : vb);
  }
  return out;
}

// A pulse that rises over `rise`, holds, and falls over `fall` (for one-off gestures).
function pulse(t, t0, rise, hold, fall) {
  if (t < t0) return 0;
  if (t < t0 + rise) return smooth((t - t0) / rise);
  if (t < t0 + rise + hold) return 1;
  if (t < t0 + rise + hold + fall) return 1 - smooth((t - t0 - rise - hold) / fall);
  return 0;
}

module.exports = {
  clamp, lerp, invLerp, smooth, smoother, easeOut, easeIn, easeInOut, easeBack, EASE,
  rng, noise1, fbm, hexToRgb, rgbStr, mix, shade, col, sampleTrack, mixValue, pulse,
};
