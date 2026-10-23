// ---------- core utilities ----------
const W = 720, H = 1280, FPS = 24, TAU = Math.PI * 2;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const easeIO = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const easeOut = t => { t = clamp(t); return 1 - Math.pow(1 - t, 3); };
const ramp = (t, a, b) => ease((t - a) / (b - a));
function hash(n) { n = Math.sin(n * 127.1 + 311.7) * 43758.5453; return n - Math.floor(n); }
function noise1(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; }
function fbm(x, seed = 0) { return noise1(x + seed * 17.3) * .6 + noise1(x * 2.1 + seed * 5.1) * .3 + noise1(x * 4.3 + seed * 3.7) * .1; }
function rng(seed) { let s = seed >>> 0 || 1; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function lerpV(a, b, t) {
  if (typeof a === 'number' && typeof b === 'number') return lerp(a, b, t);
  if (a && b && typeof a === 'object' && typeof b === 'object') { const o = {}; for (const k in b) o[k] = (k in a) ? lerpV(a[k], b[k], t) : b[k]; return o; }
  return t < .5 ? a : b;
}
// hex -> rgb helpers
function hex2rgb(h) { h = h.replace('#', ''); if (h.length === 3) h = h.split('').map(c => c + c).join(''); const n = parseInt(h, 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
function rgb(r, g, b, a = 1) { return `rgba(${r | 0},${g | 0},${b | 0},${a})`; }
function shade(h, f, a = 1) { // f<0 darker, f>0 lighter
  const [r, g, b] = hex2rgb(h);
  if (f < 0) return rgb(r * (1 + f), g * (1 + f), b * (1 + f), a);
  return rgb(r + (255 - r) * f, g + (255 - g) * f, b + (255 - b) * f, a);
}
function mix(h1, h2, t, a = 1) { const A = hex2rgb(h1), B = hex2rgb(h2); return rgb(lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t), a); }
function alpha(h, a) { const [r, g, b] = hex2rgb(h); return rgb(r, g, b, a); }

// Expression / pose track: keys = [{t, d, ...props}]. Each property eases from its previous value
// to the new one starting at t over duration d (default .45s).
class Track {
  constructor(base, keys = []) { this.base = base; this.keys = keys.slice().sort((a, b) => a.t - b.t); }
  add(k) { this.keys.push(k); this.keys.sort((a, b) => a.t - b.t); return this; }
  get(t) {
    const st = Object.assign({}, this.base);
    for (const k of this.keys) {
      if (k.t > t) break;
      const u = (k.ease || easeIO)((t - k.t) / (k.d === undefined ? .45 : Math.max(k.d, 1e-3)));
      for (const p in k) { if (p === 't' || p === 'd' || p === 'ease') continue; st[p] = lerpV(st[p], k[p], u); }
    }
    return st;
  }
}

// Timeline access (TL global set at load)
let TL = null;
const LINE = id => TL.lines.find(l => l.id === id);
function WT(id, word, n = 0, end = false) { // time of the n-th occurrence of word in line id
  const l = LINE(id); let c = 0;
  for (const w of l.words) { if (w.w.replace(/[^\w']/g, '').toLowerCase() === word.toLowerCase()) { if (c === n) return end ? w.t + w.d : w.t; c++; } }
  console.warn('word not found', id, word); return l.start;
}
// mouth openness for a speaker at time t
function speakAmt(sp, t) {
  for (const l of TL.lines) {
    if (l.sp !== sp || t < l.start - .02 || t > l.end + .05) continue;
    const f = (t - l.start) * FPS, i = Math.floor(f), u = f - i;
    const e = l.env, a = e[clamp(i, 0, e.length - 1)] || 0, b = e[clamp(i + 1, 0, e.length - 1)] || 0;
    // current word for vowel shaping
    let word = '';
    for (const w of l.words) if (t >= w.t - .03 && t <= w.t + w.d + .03) word = w.w;
    return { open: lerp(a, b, u), word, line: l };
  }
  return null;
}
function speaking(sp, t) { return TL.lines.some(l => l.sp === sp && t >= l.start && t <= l.end); }
