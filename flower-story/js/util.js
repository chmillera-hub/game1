/* ==========================================================================
   util.js — math, easing, keyframes, deterministic noise, color helpers.
   Global: U
   Everything here is pure: the film is a function of time, so scenes must
   never keep accumulated state between frames (scrubbing must work).
   ========================================================================== */
(function (g) {
  'use strict';
  const U = {};
  U.W = 1920;
  U.H = 1080;
  U.TAU = Math.PI * 2;

  /* ---------------- scalar helpers ---------------- */
  U.clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
  U.lerp = (a, b, t) => a + (b - a) * t;
  U.invLerp = (a, b, x) => (x - a) / (b - a);
  /** progress 0..1 of t through [t0, t1] (clamped) */
  U.prog = (t, t0, t1) => U.clamp((t - t0) / (t1 - t0));
  /** remap x from [a,b] to [c,d] clamped */
  U.remap = (x, a, b, c, d) => c + (d - c) * U.clamp((x - a) / (b - a));
  U.smooth = (x) => { x = U.clamp(x); return x * x * (3 - 2 * x); };
  U.smoother = (x) => { x = U.clamp(x); return x * x * x * (x * (x * 6 - 15) + 10); };
  /** alpha envelope: 0 outside [t0,t1], smooth fade in over fi, fade out over fo */
  U.fade = (t, t0, t1, fi = 0.5, fo = 0.5) => {
    if (t < t0 || t > t1) return 0;
    const a = fi > 0 ? U.clamp((t - t0) / fi) : 1;
    const b = fo > 0 ? U.clamp((t1 - t) / fo) : 1;
    return U.smooth(Math.min(a, b));
  };
  /** 0 → 1 → 0 bump centered at c with half-width w */
  U.bump = (t, c, w) => { const x = 1 - Math.abs(t - c) / w; return x <= 0 ? 0 : U.smooth(x); };
  U.pingpong = (t, len = 1) => { const m = t % (2 * len); return m < len ? m : 2 * len - m; };
  U.fract = (x) => x - Math.floor(x);
  U.sign = (x) => (x < 0 ? -1 : 1);
  U.dist = (x1, y1, x2, y2) => Math.hypot(x2 - x1, y2 - y1);
  /** damped spring response to a step at t=0 (0 → 1 with overshoot) */
  U.spring = (t, freq = 2.2, damp = 4.5) => (t <= 0 ? 0 : 1 - Math.exp(-damp * t) * Math.cos(U.TAU * freq * t));

  /* ---------------- easing ---------------- */
  const E = {
    linear: (x) => x,
    inQuad: (x) => x * x,
    outQuad: (x) => 1 - (1 - x) * (1 - x),
    inOutQuad: (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2),
    inCubic: (x) => x * x * x,
    outCubic: (x) => 1 - Math.pow(1 - x, 3),
    inOutCubic: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    inQuart: (x) => x * x * x * x,
    outQuart: (x) => 1 - Math.pow(1 - x, 4),
    inOutQuart: (x) => (x < 0.5 ? 8 * x * x * x * x : 1 - Math.pow(-2 * x + 2, 4) / 2),
    inSine: (x) => 1 - Math.cos((x * Math.PI) / 2),
    outSine: (x) => Math.sin((x * Math.PI) / 2),
    inOutSine: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
    inExpo: (x) => (x === 0 ? 0 : Math.pow(2, 10 * x - 10)),
    outExpo: (x) => (x === 1 ? 1 : 1 - Math.pow(2, -10 * x)),
    inOutExpo: (x) => (x === 0 ? 0 : x === 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2),
    outBack: (x) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
    inBack: (x) => { const c1 = 1.70158, c3 = c1 + 1; return c3 * x * x * x - c1 * x * x; },
    inOutBack: (x) => {
      const c2 = 1.70158 * 1.525;
      return x < 0.5 ? (Math.pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2 : (Math.pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2;
    },
    outElastic: (x) => (x === 0 ? 0 : x === 1 ? 1 : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1),
    outBounce: (x) => {
      const n1 = 7.5625, d1 = 2.75;
      if (x < 1 / d1) return n1 * x * x;
      if (x < 2 / d1) return n1 * (x -= 1.5 / d1) * x + 0.75;
      if (x < 2.5 / d1) return n1 * (x -= 2.25 / d1) * x + 0.9375;
      return n1 * (x -= 2.625 / d1) * x + 0.984375;
    },
    step: (x) => (x < 1 ? 0 : 1),
  };
  U.E = E;
  /** eased progress: U.ease(t, t0, t1, 'outCubic') */
  U.ease = (t, t0, t1, name = 'inOutSine') => (E[name] || E.inOutSine)(U.prog(t, t0, t1));

  /**
   * Keyframe interpolation. frames = [[time, value, easeName?], ...] sorted by time.
   * The ease of a frame applies to the segment that ENDS at that frame.
   * value may be a number or an array of numbers (e.g. [x, y]).
   */
  U.keys = (t, frames) => {
    const n = frames.length;
    if (!n) return 0;
    if (t <= frames[0][0]) return frames[0][1];
    for (let i = 1; i < n; i++) {
      const f = frames[i];
      if (t <= f[0]) {
        const p = frames[i - 1];
        const span = f[0] - p[0];
        const k = span > 0 ? (t - p[0]) / span : 1;
        const e = (E[f[2]] || E.inOutSine)(k);
        if (Array.isArray(p[1])) return p[1].map((v, j) => v + (f[1][j] - v) * e);
        return p[1] + (f[1] - p[1]) * e;
      }
    }
    return frames[n - 1][1];
  };

  /* ---------------- deterministic randomness ---------------- */
  /** mulberry32 seeded PRNG: const r = U.rng(42); r() → [0,1) */
  U.rng = (seed) => {
    let s = (seed >>> 0) || 1;
    return () => {
      s = (s + 0x6d2b79f5) | 0;
      let t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  /** stateless hash → [0,1) for (n, seed) */
  U.hash = (n, s = 0) => {
    let h = Math.imul((n | 0) ^ 0x9e3779b9, 0x85ebca6b) ^ Math.imul((s | 0) + 0x632be5ab, 0xc2b2ae35);
    h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d); h ^= h >>> 12; h = Math.imul(h, 0x297a2d39); h ^= h >>> 15;
    return (h >>> 0) / 4294967296;
  };
  /** hash for float inputs */
  U.hashf = (x, s = 0) => { const v = Math.sin(x * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
  /** 1D value noise in [-1,1] */
  U.noise1 = (x, s = 0) => {
    const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
    return (U.hash(i, s) + (U.hash(i + 1, s) - U.hash(i, s)) * u) * 2 - 1;
  };
  /** 2D value noise in [-1,1] */
  U.noise2 = (x, y, s = 0) => {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const h = (a, b) => U.hash(a * 374761393 + b * 668265263, s);
    const a = h(xi, yi), b = h(xi + 1, yi), c = h(xi, yi + 1), d = h(xi + 1, yi + 1);
    return (a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v) * 2 - 1;
  };
  /** fractal 1D noise in roughly [-1,1] */
  U.fbm1 = (x, oct = 4, s = 0) => {
    let sum = 0, amp = 0.5, f = 1, norm = 0;
    for (let i = 0; i < oct; i++) { sum += amp * U.noise1(x * f, s + i * 17); norm += amp; amp *= 0.5; f *= 2.03; }
    return sum / norm;
  };
  U.fbm2 = (x, y, oct = 4, s = 0) => {
    let sum = 0, amp = 0.5, f = 1, norm = 0;
    for (let i = 0; i < oct; i++) { sum += amp * U.noise2(x * f, y * f, s + i * 31); norm += amp; amp *= 0.5; f *= 2.03; }
    return sum / norm;
  };
  /** gentle wind sway value in [-1,1] for time t and a spatial offset */
  U.wind = (t, x = 0, s = 0) => 0.65 * Math.sin(t * 1.3 + x * 0.004 + s) + 0.35 * U.noise1(t * 0.7 + x * 0.002, 7 + s);
  /** blink amount 0 (open) .. 1 (closed) — natural irregular blinking */
  U.blink = (t, seed = 0) => {
    const period = 3.2 + U.hash(seed, 3) * 2.2;
    const tt = t + U.hash(seed, 9) * period;
    const k = Math.floor(tt / period);
    const local = tt - k * period - (U.hash(k, seed) * 0.6);
    return local > 0 && local < 0.16 ? Math.sin((local / 0.16) * Math.PI) : 0;
  };

  /* ---------------- color ---------------- */
  const cache = new Map();
  /** parse '#rgb', '#rrggbb', 'rgb(...)' → [r,g,b] (0..255) */
  U.rgb = (c) => {
    if (Array.isArray(c)) return c;
    let v = cache.get(c);
    if (v) return v;
    if (c[0] === '#') {
      let h = c.slice(1);
      if (h.length === 3) h = h.split('').map((x) => x + x).join('');
      const n = parseInt(h.slice(0, 6), 16);
      v = [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    } else {
      const m = c.match(/[\d.]+/g) || [0, 0, 0];
      v = [+m[0], +m[1], +m[2]];
    }
    cache.set(c, v);
    return v;
  };
  const hx = (x) => { x = Math.round(U.clamp(x, 0, 255)); return (x < 16 ? '0' : '') + x.toString(16); };
  U.hex = (r, g, b) => '#' + hx(r) + hx(g) + hx(b);
  /** rgba string from hex + alpha */
  U.rgba = (c, a = 1) => { const [r, g, b] = U.rgb(c); return `rgba(${r},${g},${b},${U.clamp(a)})`; };
  /** mix two colors → hex */
  U.mix = (a, b, t) => {
    const A = U.rgb(a), B = U.rgb(b);
    t = U.clamp(t);
    return U.hex(A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t, A[2] + (B[2] - A[2]) * t);
  };
  /** lighten (amt>0, toward white) / darken (amt<0, toward black) */
  U.shade = (c, amt) => (amt >= 0 ? U.mix(c, '#ffffff', amt) : U.mix(c, '#000000', -amt));
  /** desaturate toward luminance grey by amt 0..1 */
  U.desat = (c, amt) => {
    const [r, g, b] = U.rgb(c);
    const l = 0.299 * r + 0.587 * g + 0.114 * b;
    return U.hex(r + (l - r) * amt, g + (l - g) * amt, b + (l - b) * amt);
  };
  /** multiply-like tint: mix toward tint color by amt */
  U.tint = (c, tint, amt) => U.mix(c, tint, amt);
  /** hsl → hex (h in degrees) */
  U.hsl = (h, s, l) => {
    h = ((h % 360) + 360) % 360; s = U.clamp(s); l = U.clamp(l);
    const k = (n) => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
    return U.hex(f(0) * 255, f(8) * 255, f(4) * 255);
  };
  /** recursively mix two palette objects/arrays of colors and numbers */
  U.mixDeep = (a, b, t) => {
    if (typeof a === 'string' && typeof b === 'string') return U.mix(a, b, t);
    if (typeof a === 'number' && typeof b === 'number') return a + (b - a) * t;
    if (Array.isArray(a) && Array.isArray(b)) return a.map((v, i) => U.mixDeep(v, b[i] !== undefined ? b[i] : v, t));
    if (a && b && typeof a === 'object') {
      const o = {};
      for (const k of Object.keys(a)) o[k] = k in b ? U.mixDeep(a[k], b[k], t) : a[k];
      return o;
    }
    return t < 0.5 ? a : b;
  };

  /* ---------------- formatting ---------------- */
  U.fmtTime = (s) => {
    s = Math.max(0, Math.floor(s));
    return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  };

  g.U = U;
})(typeof window !== 'undefined' ? window : globalThis);
