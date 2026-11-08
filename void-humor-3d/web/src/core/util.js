// Deterministic math helpers. NEVER use Math.random / Date in render code: every frame must be a pure
// function of time so frames can be rendered out of order and in parallel browsers.
import * as THREE from 'three';

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => (x - a) / (b - a);
export const remap = (x, a, b, c, d) => lerp(c, d, clamp(invLerp(a, b, x)));
export const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
export const smoother = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
export const smoothstep = (a, b, x) => smooth(invLerp(a, b, x));
export const DEG = Math.PI / 180;

export const ease = {
  linear: (t) => t,
  in: (t) => t * t,
  out: (t) => 1 - (1 - t) * (1 - t),
  inOut: smooth,
  inOut5: smoother,
  in3: (t) => t * t * t,
  out3: (t) => 1 - Math.pow(1 - t, 3),
  outBack: (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  inBack: (t) => { const c1 = 1.70158, c3 = c1 + 1; return c3 * t * t * t - c1 * t * t; },
  outElastic: (t) => (t === 0 || t === 1) ? t : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3) + 1,
  hold: (t) => (t < 1 ? 0 : 1),
  step: (t) => (t < 1 ? 0 : 1),
};

// Seeded PRNG (mulberry32). rng(seed)() -> [0,1)
export function rng(seed) {
  let a = (seed >>> 0) || 1;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Integer hash -> [0,1)
export function hash1(n) {
  let x = Math.imul((n | 0) ^ 0x27d4eb2d, 0x165667b1);
  x ^= x >>> 15; x = Math.imul(x, 0x85ebca6b); x ^= x >>> 13; x = Math.imul(x, 0xc2b2ae35); x ^= x >>> 16;
  return (x >>> 0) / 4294967296;
}
export const hash2 = (a, b) => hash1(Math.imul(a | 0, 73856093) ^ Math.imul(b | 0, 19349663));

// Smooth 1D value noise in [-1,1]. noise1(t, seed)
export function noise1(t, seed = 0) {
  const i = Math.floor(t), f = t - i;
  const a = hash2(i, seed) * 2 - 1, b = hash2(i + 1, seed) * 2 - 1;
  return lerp(a, b, smoother(f));
}
// Fractal 1D noise in about [-1,1]
export function fbm1(t, seed = 0, oct = 3) {
  let s = 0, amp = 0.5, f = 1, norm = 0;
  for (let o = 0; o < oct; o++) { s += amp * noise1(t * f, seed + o * 101); norm += amp; amp *= 0.5; f *= 2.03; }
  return s / norm;
}

// Deterministic "event" schedule: returns sorted event times in [t0,t1) with random gaps in [gmin,gmax]
export function schedule(seed, t0, t1, gmin, gmax) {
  const r = rng(seed);
  const out = [];
  let t = t0 + r() * gmax;
  while (t < t1) { out.push(t); t += gmin + r() * (gmax - gmin); }
  return out;
}

export const v3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
export const toV3 = (a) => (a instanceof THREE.Vector3 ? a.clone() : new THREE.Vector3(a[0], a[1], a[2]));

// Critically damped spring evaluated analytically is overkill; for stateless animation use
// lagged sampling: value(t) ≈ average of f over [t-lag, t] (smooth follow-through without state).
export function lagged(f, t, lag = 0.15, n = 5) {
  let s = 0, w = 0;
  for (let i = 0; i < n; i++) { const k = i / (n - 1); const wk = 1 - 0.6 * k; s += f(t - lag * k) * wk; w += wk; }
  return s / w;
}
