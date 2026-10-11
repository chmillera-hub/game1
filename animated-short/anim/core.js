// Keyframe tracks, easing, noise and small math helpers.

const ease = {
  linear: (t) => t,
  smooth: (t) => t * t * (3 - 2 * t),
  inOut: (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  out: (t) => 1 - Math.pow(1 - t, 3),
  in: (t) => t * t * t,
  back: (t) => {
    const c1 = 1.4, c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  },
};

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;

function upperBound(keys, t) {
  let lo = 0, hi = keys.length;
  while (lo < hi) {
    const m = (lo + hi) >> 1;
    if (keys[m].t <= t) lo = m + 1; else hi = m;
  }
  return lo;
}

// A numeric track: each key starts a transition from wherever the value is
// at that moment toward key.v, taking key.dur seconds.
class Track {
  constructor(initial) {
    this.keys = [{ t: -1e9, v: initial, sv: initial, dur: 1e-4, e: 'linear' }];
    this.dirty = false;
  }
  set(t, v, dur = 0.4, e = 'inOut') {
    this.keys.push({ t, v, dur: Math.max(dur, 1e-4), e });
    this.dirty = true;
    return this;
  }
  _prepare() {
    this.keys.sort((a, b) => a.t - b.t);
    const k = this.keys;
    k[0].sv = k[0].v;
    for (let i = 1; i < k.length; i++) k[i].sv = this._eval(i - 1, k[i].t);
    this.dirty = false;
  }
  _eval(i, t) {
    const k = this.keys[i];
    const f = clamp((t - k.t) / k.dur, 0, 1);
    return lerp(k.sv, k.v, ease[k.e](f));
  }
  at(t) {
    if (this.dirty) this._prepare();
    const i = upperBound(this.keys, t) - 1;
    return this._eval(Math.max(i, 0), t);
  }
}

// Discrete track (strings/objects): value switches at key time.
class Steps {
  constructor(initial) { this.keys = [{ t: -1e9, v: initial }]; this.dirty = false; }
  set(t, v) { this.keys.push({ t, v }); this.dirty = true; return this; }
  at(t) {
    if (this.dirty) { this.keys.sort((a, b) => a.t - b.t); this.dirty = false; }
    return this.keys[Math.max(upperBound(this.keys, t) - 1, 0)].v;
  }
  // value plus the key it came from (for transitions)
  keyAt(t) {
    if (this.dirty) { this.keys.sort((a, b) => a.t - b.t); this.dirty = false; }
    const i = Math.max(upperBound(this.keys, t) - 1, 0);
    return { cur: this.keys[i], prev: this.keys[Math.max(i - 1, 0)] };
  }
}

// deterministic smooth 1D noise in [-1, 1]
function hash(n) {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return (s - Math.floor(s)) * 2 - 1;
}
function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const u = f * f * (3 - 2 * f);
  return lerp(hash(i + seed * 57.3), hash(i + 1 + seed * 57.3), u);
}
function fbm(x, seed = 0) {
  return 0.65 * noise1(x, seed) + 0.35 * noise1(x * 2.13 + 7.7, seed + 3);
}

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function mixColor(a, b, t) {
  const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
  const r = Math.round(lerp((pa >> 16) & 255, (pb >> 16) & 255, t));
  const g = Math.round(lerp((pa >> 8) & 255, (pb >> 8) & 255, t));
  const bl = Math.round(lerp(pa & 255, pb & 255, t));
  return '#' + ((1 << 24) | (r << 16) | (g << 8) | bl).toString(16).slice(1);
}

function rgba(hex, a) {
  const p = parseInt(hex.slice(1), 16);
  return `rgba(${(p >> 16) & 255},${(p >> 8) & 255},${p & 255},${a})`;
}

module.exports = { ease, clamp, lerp, Track, Steps, noise1, fbm, mulberry32, mixColor, rgba };
