// Acting: expression presets, keyframe tracks, lip-sync, blinks, idle motion.
'use strict';
const { clamp, lerp, easeInOut, smooth, noise1, fbm1, hash, seeded } = require('./core');
const { HANDS } = require('./rig');

// ---------------------------------------------------------------- expressions
const FACE_KEYS = ['lidU', 'lidUL', 'lidUR', 'lidL', 'lidLL', 'lidLR', 'lidTilt', 'brow', 'browL', 'browR', 'browIn', 'browInL', 'browInR', 'browOut', 'browSq',
  'browOffL', 'browOffR', 'smile', 'asym', 'press', 'mouthOpen', 'mouthWide', 'mouthRound', 'glisten', 'blush', 'underEye', 'pupil'];
const FACE_DEFAULT = { lidU: 0.15, pupil: 1 };
const EXPR = {
  neutral: {},
  listening: { lidU: 0.12, browIn: 0.22, smile: 0 },
  soft: { smile: 0.08, lidU: 0.14, browIn: 0.2 },
  smallSmile: { smile: 0.38, lidL: 0.14, brow: 0.05 },
  smile: { smile: 0.72, lidL: 0.3, brow: 0.12, blush: 0.15 },
  warm: { smile: 0.45, lidL: 0.2, browIn: 0.18, lidU: 0.2 },
  tender: { browIn: 0.5, lidU: 0.16, smile: 0.06, glisten: 0.35 },
  sad: { browIn: 0.6, lidU: 0.3, lidTilt: 0.35, smile: -0.32, underEye: 0.3 },
  sadDeep: { browIn: 0.85, lidU: 0.4, lidTilt: 0.5, smile: -0.5, glisten: 0.6, underEye: 0.45, press: 0.15 },
  hurt: { browIn: 0.65, browSq: 0.3, lidU: 0.24, lidTilt: 0.3, smile: -0.36, press: 0.35, glisten: 0.3 },
  tearful: { browIn: 0.8, lidU: 0.3, lidTilt: 0.42, smile: -0.25, glisten: 0.95, underEye: 0.3 },
  cry: { browIn: 0.95, browSq: 0.3, lidU: 0.45, lidL: 0.2, lidTilt: 0.5, smile: -0.6, glisten: 1, underEye: 0.5 },
  annoyed: { lidU: 0.36, browR: 0.25, browL: -0.12, browIn: -0.2, smile: -0.2, asym: -0.25, press: 0.2 },
  skeptical: { browR: 0.7, browL: -0.2, lidUL: 0.36, lidUR: 0.16, asym: 0.3, smile: -0.1 },
  grumpy: { browIn: -0.5, browSq: 0.5, lidU: 0.3, smile: -0.35, press: 0.35 },
  angry: { browIn: -0.9, browSq: 0.9, brow: -0.2, lidU: 0.18, lidL: 0.25, lidTilt: -0.4, smile: -0.5, press: 0.35 },
  furious: { browIn: -1.2, browSq: 1, brow: -0.3, lidU: 0.04, lidL: 0.15, lidTilt: -0.5, smile: -0.5, mouthWide: 0.45, mouthOpen: 0.22 },
  fear: { brow: 0.6, browIn: 0.8, lidU: 0.0, smile: -0.4, mouthWide: 0.3, mouthOpen: 0.2, pupil: 0.75 },
  worried: { brow: 0.3, browIn: 0.7, lidU: 0.06, smile: -0.28, press: 0.15 },
  surprised: { brow: 0.8, lidU: 0.0, smile: 0 },
  relieved: { brow: 0.08, browIn: 0.3, lidU: 0.36, smile: 0.25 },
  determined: { browIn: -0.15, brow: -0.05, lidU: 0.2, lidL: 0.1, press: 0.25 },
  guilty: { browIn: 0.5, lidU: 0.36, smile: -0.25, press: 0.3 },
  avoid: { lidU: 0.2, smile: -0.18, browIn: 0.1, press: 0.25 },
  tired: { lidU: 0.4, underEye: 0.4, smile: -0.1 },
  laughCry: { smile: 0.6, lidL: 0.35, lidU: 0.3, browIn: 0.5, glisten: 0.9 },
  shout: { browIn: -1, browSq: 1, brow: -0.2, lidU: 0.05, smile: -0.4, mouthWide: 0.3 },
};
function faceOf(name, amt = 1, extra) {
  const src = typeof name === 'string' ? EXPR[name] || {} : name || {};
  const f = {};
  for (const k of FACE_KEYS) {
    const d = FACE_DEFAULT[k] ?? 0;
    const v = src[k];
    f[k] = v === undefined ? (k === 'lidUL' || k === 'lidUR' || k === 'lidLL' || k === 'lidLR' || k === 'browL' || k === 'browR' || k === 'browInL' || k === 'browInR' ? NaN : d) : lerp(d, v, amt);
  }
  if (extra) for (const k in extra) f[k] = extra[k];
  return f;
}
// per-eye / per-brow channels fall back to the shared channel when NaN
function resolveFace(f) {
  const o = { ...f };
  const pairs = [['lidUL', 'lidU'], ['lidUR', 'lidU'], ['lidLL', 'lidL'], ['lidLR', 'lidL'], ['browL', 'brow'], ['browR', 'brow'], ['browInL', 'browIn'], ['browInR', 'browIn']];
  for (const [a, b] of pairs) if (o[a] === undefined || Number.isNaN(o[a])) o[a] = o[b];
  return o;
}

// ---------------------------------------------------------------- tracks
function lerpVal(a, b, t) {
  if (typeof b === 'number') return lerp(typeof a === 'number' ? a : b, b, t);
  if (Array.isArray(b)) return b.map((v, i) => lerpVal(a ? a[i] : v, v, t));
  if (b && typeof b === 'object') {
    const o = {};
    const keys = new Set([...Object.keys(a || {}), ...Object.keys(b)]);
    for (const k of keys) {
      const av = a ? a[k] : undefined, bv = b[k];
      if (bv === undefined) o[k] = av;
      else if (typeof bv === 'number' && Number.isNaN(bv)) o[k] = (typeof av === 'number' && !Number.isNaN(av)) ? (t < 1 ? av * (1 - t) + (t) * NaN : NaN) : NaN;
      else if (typeof bv === 'number' && typeof av === 'number' && Number.isNaN(av)) o[k] = bv;
      else o[k] = lerpVal(av, bv, t);
    }
    return o;
  }
  return t < 0.5 && a !== undefined ? a : b; // discrete
}

class Track {
  constructor(base) { this.base = base; this.keys = []; }
  add(t, v, dur = 0.4, ease = easeInOut) { this.keys.push({ t, v, dur: Math.max(1e-3, dur), ease }); this.keys.sort((a, b) => a.t - b.t); return this; }
  at(T) {
    let v = this.base;
    const K = this.keys;
    for (let i = 0; i < K.length; i++) {
      const k = K[i];
      if (k.t > T) break;
      const tEnd = Math.min(T, i + 1 < K.length ? K[i + 1].t : Infinity);
      const p = clamp((tEnd - k.t) / k.dur);
      v = p >= 1 ? k.v : lerpVal(v, k.v, k.ease(p));
    }
    return v;
  }
}

// ---------------------------------------------------------------- lip sync
const VIS = {
  a: [0.75, 0.25, 0], 'ɑ': [0.78, 0.15, 0.05], 'æ': [0.65, 0.45, 0], 'ʌ': [0.6, 0.15, 0], 'ɐ': [0.55, 0.15, 0],
  'ɛ': [0.5, 0.4, 0], e: [0.45, 0.45, 0], i: [0.22, 0.7, 0], 'ɪ': [0.28, 0.5, 0], 'ᵻ': [0.28, 0.45, 0], j: [0.2, 0.5, 0],
  o: [0.5, -0.1, 0.65], 'ɔ': [0.6, -0.05, 0.5], u: [0.22, -0.2, 0.9], 'ʊ': [0.25, -0.1, 0.7], w: [0.15, -0.25, 0.95],
  'ə': [0.35, 0.1, 0], 'ɚ': [0.3, 0, 0.35], 'ɜ': [0.35, 0.05, 0.3], 'ɹ': [0.2, 0, 0.45],
  p: [0, 0, 0, 1], b: [0, 0, 0, 1], m: [0, 0, 0, 0.8],
  f: [0.08, 0.15, 0, 0, 1], v: [0.08, 0.15, 0, 0, 1],
  'θ': [0.18, 0.2, 0, 0, 0.5], 'ð': [0.18, 0.2, 0, 0, 0.5],
  s: [0.1, 0.45, 0, 0, 1], z: [0.1, 0.45, 0, 0, 1], 'ʃ': [0.14, 0.1, 0.4, 0, 1], 'ʒ': [0.14, 0.1, 0.4, 0, 1], 'ʧ': [0.14, 0.1, 0.4, 0, 1], 'ʤ': [0.14, 0.1, 0.4, 0, 1],
  t: [0.2, 0.2, 0], d: [0.2, 0.2, 0], n: [0.18, 0.2, 0], l: [0.25, 0.15, 0], 'ɾ': [0.22, 0.2, 0], k: [0.25, 0.1, 0], 'ɡ': [0.25, 0.1, 0], g: [0.25, 0.1, 0], 'ŋ': [0.2, 0.1, 0], h: [0.3, 0.1, 0],
};
const REST = [0, 0, 0, 0, 0];
function visOf(ch) { const v = VIS[ch]; if (!v) return null; return [v[0], v[1], v[2], v[3] || 0, v[4] || 0]; }

class LipSync {
  constructor(lines, gain = 1) {
    this.lines = lines.map((l) => {
      // resolve length marks / unknowns to the previous viseme
      const ph = [];
      let prev = REST;
      for (const [c, a, b] of l.phones) {
        if (c === 'ˈ' || c === 'ˌ') continue;
        let v = visOf(c);
        if (c === 'ː') v = prev;
        if (!v) { if ('.,!?;:—…'.includes(c)) v = REST; else continue; }
        ph.push([a, b, v]);
        prev = v;
      }
      const stress = l.phones.filter((p) => p[0] === 'ˈ').map((p) => p[1]);
      return { t0: l.t0, t1: l.t1, ph, stress, gain: (l.shout ? 1.3 : 1) * gain };
    });
  }
  line(T) { for (const l of this.lines) if (T >= l.t0 - 0.15 && T <= l.t1 + 0.2) return l; return null; }
  sample(T) {
    const l = this.line(T);
    if (!l) return { open: 0, wide: 0, round: 0, press: 0, teeth: 0, talking: 0 };
    const acc = [0, 0, 0, 0, 0];
    let wsum = 0;
    for (let k = -3; k <= 3; k++) {
      const tt = T + 0.025 + k * 0.022;
      const w = Math.exp(-(k * k) / 4.5);
      let v = REST;
      for (const p of l.ph) if (tt >= p[0] && tt < p[1]) { v = p[2]; break; }
      for (let i = 0; i < 5; i++) acc[i] += v[i] * w;
      wsum += w;
    }
    const g = l.gain;
    return { open: clamp(acc[0] / wsum * g, 0, 1.1), wide: acc[1] / wsum, round: acc[2] / wsum, press: acc[3] / wsum * 0.5, teeth: acc[4] / wsum, talking: 1, stress: l.stress };
  }
}

// ---------------------------------------------------------------- character performance
class Actor {
  constructor(id, base, opts = {}) {
    this.id = id;
    this.tracks = {};
    this.base = base;
    this.events = { tears: [], blinks: [] };
    this.opts = { breathPeriod: 4.2, sway: 1, seed: (hash(id.length * 977 + id.charCodeAt(0)) * 1e4) | 0, talkMotion: 1, ...opts };
    this.lip = null;
    this.gazeShifts = [];
  }
  tr(path) { return this.tracks[path] || (this.tracks[path] = new Track(path === 'face' ? faceOf('neutral') : getPath(this.base, path))); }
  set(t, obj, dur = 0.4, ease) {
    for (const k in obj) {
      let v = obj[k];
      if (k === 'arms.L' || k === 'arms.R') v = normArm(v);
      if (k === 'gaze' && Array.isArray(v)) this.gazeShifts.push(t);
      this.tr(k).add(t, v, dur, ease);
    }
    return this;
  }
  expr(t, name, dur = 0.45, amt = 1, extra) { this.tr('face').add(t, faceOf(name, amt, extra), dur); return this; }
  look(t, gx, gy = 0, dur = 0.22) { this.tr('gaze').add(t, [gx, gy], dur); this.gazeShifts.push(t); return this; }
  head(t, yaw, pitch = 0, tilt = 0, dur = 0.5) { this.tr('head').add(t, { yaw, pitch, tilt }, dur); return this; }
  arm(t, side, a, dur = 0.5) { this.tr('arms.' + side).add(t, normArm(a), dur); return this; }
  tear(t, eye = -1, dur = 3.2) { this.events.tears.push({ t0: t, eye, dur }); return this; }
  blink(t) { this.events.blinks.push(t); return this; }
  // walk from current x to x1 between t0..t1
  walk(t0, t1, x1, y1, stride = 34) {
    this.walks = this.walks || [];
    this.walks.push({ t0, t1, stride });
    this.tr('x').add(t0, x1, t1 - t0, (p) => smooth(p) * 0.3 + p * 0.7);
    if (y1 !== undefined) this.tr('y').add(t0, y1, t1 - t0, (p) => smooth(p) * 0.3 + p * 0.7);
    return this;
  }
  sample(T) {
    const S = structuredCloneLite(this.base);
    for (const p in this.tracks) setPath(S, p, this.tracks[p].at(T));
    S.face = resolveFace(S.face || faceOf('neutral'));
    const o = this.opts, sd = o.seed;
    // idle: breathing, sway, head micro-motion
    S.breath = Math.sin((T / o.breathPeriod) * Math.PI * 2 + sd) * (S.breathAmt ?? 1);
    const sw = o.sway * (S.idle ?? 1);
    S.x += fbm1(T * 0.18, sd) * 4 * sw;
    S.lean = (S.lean || 0) + fbm1(T * 0.13, sd + 5) * 0.9 * sw;
    S.head = { ...(S.head || {}) };
    S.head.tilt = (S.head.tilt || 0) + fbm1(T * 0.21, sd + 9) * 1.6 * sw;
    S.head.yaw = (S.head.yaw || 0) + fbm1(T * 0.17, sd + 13) * 0.035 * sw;
    S.head.pitch = (S.head.pitch || 0) + fbm1(T * 0.19, sd + 17) * 0.06 * sw;
    // idle arms drift
    for (const side of ['L', 'R']) {
      const A = S.arms && S.arms[side];
      if (A && !A.locked) {
        A.tx = (A.tx ?? 0) + fbm1(T * 0.25, sd + (side === 'L' ? 21 : 29)) * 3 * sw;
        A.ty = (A.ty ?? 0) + fbm1(T * 0.22, sd + (side === 'L' ? 23 : 31)) * 3 * sw;
      }
    }
    // walking
    if (this.walks) {
      for (const w of this.walks) if (T >= w.t0 && T <= w.t1) {
        S.walk = true;
        const x = S.x;
        S.walkPhase = (Math.abs(x) / (w.stride * 2.2));
        S.stride = w.stride * smooth((T - w.t0) / 0.3) * smooth((w.t1 - T) / 0.3);
      }
    }
    // gaze: small saccades between keyed fixations
    const g = S.gaze || [0, 0];
    const sacc = Math.floor(T / 0.9 + hash(sd) * 3);
    const sx = hash(sacc * 13 + sd) * 0.05 * (S.saccade ?? 1), sy = hash(sacc * 17 + sd) * 0.03 * (S.saccade ?? 1);
    S.gaze = [g[0] + sx, g[1] + sy];
    // lip-sync and talking motion
    if (this.lip) {
      const m = this.lip.sample(T);
      S.mouth = m;
      if (m.talking && m.stress) {
        let nod = 0, br = 0;
        for (const st of m.stress) {
          const d = T - st - 0.06;
          if (d > -0.3 && d < 0.5) {
            const e = Math.exp(-(d * d) / 0.012);
            nod += e * (0.5 + 0.5 * hash(Math.round(st * 100)));
            br += e * (hash(Math.round(st * 100) + 3) > 0.2 ? 1 : 0);
          }
        }
        const tm = o.talkMotion * (S.talkMotion ?? 1);
        S.head.pitch += nod * 0.14 * tm;
        S.head.tilt += nod * 1.2 * tm * Math.sin(sd);
        S.face.brow = (S.face.brow || 0) + br * 0.12 * tm;
        S.face.browL += br * 0.12 * tm; S.face.browR += br * 0.12 * tm;
      }
    }
    // listening: small acknowledging nods on some of the other speaker's stressed syllables
    if (this.listenStress && !(S.mouth && S.mouth.talking)) {
      let nod = 0;
      for (const st of this.listenStress) {
        const d = T - st - 0.18;
        if (d > -0.4 && d < 0.6) nod += Math.exp(-(d * d) / 0.03);
      }
      S.head.pitch += nod * 0.06 * (S.listenAmt ?? 1);
    }
    // blinks: natural rhythm + on gaze shifts + manual
    if (!this._blinks) this._blinks = blinkTimes(sd, this.events.blinks, this.gazeShifts, this.opts.blinkRate ?? 1);
    S.blink = blinkAt(T, this._blinks);
    S.tears = this.events.tears;
    return S;
  }
}

function blinkCurve(d) { // d = time since blink start
  if (d < 0 || d > 0.24) return 0;
  if (d < 0.075) return smooth(d / 0.075);
  if (d < 0.11) return 1;
  return 1 - smooth((d - 0.11) / 0.13);
}
// Precomputed blink starts: natural rhythm + some gaze shifts + manual, at least 1.1 s apart.
function blinkTimes(seed, manual, shifts, rate, dur = 400) {
  const r = seeded(seed * 7 + 11);
  const nat = [];
  for (let t = r() * 2; t < dur; t += (3.2 + r() * 3.4) / rate) nat.push({ t, pri: 1 });
  const sh = shifts.filter((s) => hash(Math.round(s * 1000) + seed) > 0.2).map((t) => ({ t: t - 0.02, pri: 2 }));
  const man = manual.map((t) => ({ t, pri: 3 }));
  const all = [...nat, ...sh, ...man].sort((a, b) => a.t - b.t);
  const kept = [];
  for (const b of all) {
    const last = kept[kept.length - 1];
    if (last && b.t - last.t < 1.1) { if (b.pri > last.pri) kept[kept.length - 1] = b; continue; }
    kept.push(b);
  }
  return kept.map((b) => b.t);
}
function blinkAt(T, list) {
  let b = 0;
  for (const t of list) { if (t > T) break; if (T - t < 0.25) b = Math.max(b, blinkCurve(T - t)); }
  return b;
}

// arms: hand preset names -> parameter objects so they interpolate
function normArm(a) {
  const o = { ...a };
  if (typeof o.hand === 'string') o.hand = { ...HANDS[o.hand] };
  if (o.hand && o.hand.base) o.hand = { ...HANDS[o.hand.base], ...o.hand, base: undefined };
  return o;
}

function getPath(o, p) { return p.split('.').reduce((a, k) => (a ? a[k] : undefined), o); }
function setPath(o, p, v) {
  const ks = p.split('.');
  let a = o;
  for (let i = 0; i < ks.length - 1; i++) { a[ks[i]] = a[ks[i]] ? { ...a[ks[i]] } : {}; a = a[ks[i]]; }
  a[ks[ks.length - 1]] = v && typeof v === 'object' && !Array.isArray(v) ? { ...v } : v;
}
function structuredCloneLite(o) { return JSON.parse(JSON.stringify(o)); }

module.exports = { EXPR, faceOf, resolveFace, Track, Actor, LipSync, normArm };
