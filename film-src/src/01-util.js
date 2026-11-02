// ============================================================================
//  UTIL — math, easing, noise, keyframe tracks, seeded random
// ============================================================================
const TAU = Math.PI * 2;
const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, v) => clamp((v - a) / (b - a));
const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const smoother = t => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const range = (a, b, v) => smooth(inv(a, b, v));          // smooth 0..1 between a and b
const Ease = {
  linear: t => t,
  in: t => t * t * t,
  out: t => 1 - Math.pow(1 - t, 3),
  inOut: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  sine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  expoOut: t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t),
  back: t => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  smooth, smoother,
};
// envelope: 0 before a, ramps to 1 by b, holds, ramps down from c to 0 at d
const env = (t, a, b, c, d) => t <= a || t >= d ? 0 : t < b ? smooth((t - a) / (b - a)) : t <= c ? 1 : smooth((d - t) / (d - c));

// Keyframe track: K([[t,v],[t,v,'ease'],...]) -> f(t). Ease on a key shapes the segment arriving at it.
function K(keys) {
  return t => {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const k = keys[i];
      if (t <= k[0]) {
        const p = keys[i - 1];
        const e = Ease[k[2] || 'inOut'];
        return lerp(p[1], k[1], e((t - p[0]) / (k[0] - p[0] || 1)));
      }
    }
    return keys[keys.length - 1][1];
  };
}

// Seeded RNG (mulberry32)
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// 2D simplex noise (compact) — returns -1..1
const Noise = (() => {
  const R = rng(1337), p = new Uint8Array(512), g = [];
  const perm = [...Array(256).keys()];
  for (let i = 255; i > 0; i--) { const j = (R() * (i + 1)) | 0; [perm[i], perm[j]] = [perm[j], perm[i]]; }
  for (let i = 0; i < 512; i++) p[i] = perm[i & 255];
  for (let i = 0; i < 256; i++) { const a = R() * TAU; g.push([Math.cos(a), Math.sin(a)]); }
  const F2 = .5 * (Math.sqrt(3) - 1), G2 = (3 - Math.sqrt(3)) / 6;
  function n2(x, y) {
    const s = (x + y) * F2, i = Math.floor(x + s), j = Math.floor(y + s);
    const t = (i + j) * G2, x0 = x - (i - t), y0 = y - (j - t);
    const i1 = x0 > y0 ? 1 : 0, j1 = 1 - i1;
    const x1 = x0 - i1 + G2, y1 = y0 - j1 + G2, x2 = x0 - 1 + 2 * G2, y2 = y0 - 1 + 2 * G2;
    const ii = i & 255, jj = j & 255;
    let n = 0, tt;
    tt = .5 - x0 * x0 - y0 * y0; if (tt > 0) { const q = g[p[ii + p[jj]]]; tt *= tt; n += tt * tt * (q[0] * x0 + q[1] * y0); }
    tt = .5 - x1 * x1 - y1 * y1; if (tt > 0) { const q = g[p[ii + i1 + p[jj + j1]]]; tt *= tt; n += tt * tt * (q[0] * x1 + q[1] * y1); }
    tt = .5 - x2 * x2 - y2 * y2; if (tt > 0) { const q = g[p[ii + 1 + p[jj + 1]]]; tt *= tt; n += tt * tt * (q[0] * x2 + q[1] * y2); }
    return 70 * n;
  }
  const n1 = x => n2(x, 0.5);
  const fbm = (x, y, o = 3) => { let v = 0, a = .5, f = 1; for (let i = 0; i < o; i++) { v += a * n2(x * f, y * f); f *= 2; a *= .5; } return v; };
  return { n2, n1, fbm };
})();

// Colors
function hexRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
const rgba = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const mix = (c1, c2, t) => [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)];
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
