'use strict';
// Actor: turns direction (expression changes, looks, gestures, lines spoken)
// plus procedural life (blinks, saccades, breathing, idle drift, speech beats,
// hair sway) into a pose for any time t. Stateless in t, so frames can be
// rendered in any order or in parallel.

const { clamp, lerp, EASE, rng, fbm, mixValue, smooth } = require('./util');
const { EXPR } = require('./expressions');

function evalSegs(segs, t, init, mixer) {
  let v = init;
  for (let i = 0; i < segs.length; i++) {
    const s = segs[i];
    if (t < s.t0) break;
    const next = segs[i + 1];
    const tEnd = Math.min(t, next ? next.t0 : Infinity);
    const u = s.t1 > s.t0 ? clamp((tEnd - s.t0) / (s.t1 - s.t0)) : 1;
    v = mixer(v, s.v, (EASE[s.ease] || EASE.inout)(u));
  }
  return v;
}
const numMix = (a, b, u) => lerp(a, b, u);

class Actor {
  constructor(id, A, opts = {}) {
    this.id = id;
    this.A = A;
    this.seed = opts.seed ?? hashStr(id);
    this.exprSegs = [];
    this.tracks = {};        // param -> segments (additive numeric)
    this.armSegs = { armL: [], armR: [] };
    this.blinks = [];        // explicit blinks [{t, close, hold, open, depth}]
    this.tearList = [];
    this.lines = [];         // [{start, end, env}]
    this.idleAmp = opts.idle ?? 1;
    this.talkAmp = opts.talk ?? 1;
    this.blinkMean = opts.blinkMean ?? 3.4;
    this.extra = {};
    this._autoBlinks = null;
    this._saccades = null;
  }

  // ---- direction API ----
  expr(t, name, dur = 0.45, ease = 'inout') {
    if (!EXPR[name]) throw new Error(`unknown expression ${name}`);
    this.exprSegs.push({ t0: t, t1: t + dur, v: EXPR[name], ease });
    this.exprSegs.sort((a, b) => a.t0 - b.t0);
    return this;
  }
  set(param, t, v, dur = 0.35, ease = 'inout') {
    (this.tracks[param] ||= []).push({ t0: t, t1: t + dur, v, ease });
    this.tracks[param].sort((a, b) => a.t0 - b.t0);
    return this;
  }
  look(t, obj, dur = 0.35, ease = 'inout') {
    for (const [k, v] of Object.entries(obj)) this.set(k, t, v, dur, ease);
    // people usually blink as they shift gaze substantially
    if (dur > 0.12 && (obj.yaw !== undefined || obj.gazeX !== undefined) && (obj.blink ?? true)) this.blinkAt(t + 0.02);
    return this;
  }
  arm(side, t, spec, dur = 0.5, ease = 'inout') {
    const k = side === 'L' ? 'armL' : 'armR';
    this.armSegs[k].push({ t0: t, t1: t + dur, v: spec, ease });
    this.armSegs[k].sort((a, b) => a.t0 - b.t0);
    return this;
  }
  blinkAt(t, opt = {}) {
    this.blinks.push({ t, close: opt.close ?? 0.07, hold: opt.hold ?? 0.03, open: opt.open ?? 0.12, depth: opt.depth ?? 1 });
    return this;
  }
  slowBlink(t, hold = 0.35) { return this.blinkAt(t, { close: 0.16, hold, open: 0.28 }); }
  tear(side, t0, dur = 1.6) { this.tearList.push({ side, t0, dur }); return this; }
  say(start, env, dur) { this.lines.push({ start, end: start + dur, env }); return this; }

  // ---- procedural schedules ----
  autoBlinks(T) {
    if (this._autoBlinks) return this._autoBlinks;
    const r = rng(this.seed * 7 + 3);
    const out = [];
    let t = r() * 2;
    while (t < T) {
      out.push(t);
      if (r() < 0.14) out.push(t + 0.22 + r() * 0.08); // occasional double blink
      t += this.blinkMean * (0.45 + r() * 1.1);
    }
    this._autoBlinks = out;
    return out;
  }
  saccades(T) {
    if (this._saccades) return this._saccades;
    const r = rng(this.seed * 13 + 5);
    const out = [];
    let t = 0;
    while (t < T) {
      out.push({ t, x: (r() - 0.5) * 0.22, y: (r() - 0.5) * 0.14 });
      t += 0.45 + r() * 1.9;
    }
    this._saccades = out;
    return out;
  }

  blinkValue(t) {
    let v = 0;
    const shape = (b, dt) => {
      if (dt < 0) return 0;
      if (dt < b.close) return smooth(dt / b.close) * b.depth;
      if (dt < b.close + b.hold) return b.depth;
      if (dt < b.close + b.hold + b.open) return (1 - smooth((dt - b.close - b.hold) / b.open)) * b.depth;
      return 0;
    };
    const auto = this.autoBlinks(t + 10);
    // binary search the last auto blink before t
    let lo = 0, hi = auto.length - 1, idx = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (auto[m] <= t) { idx = m; lo = m + 1; } else hi = m - 1; }
    for (let i = Math.max(0, idx - 1); i <= idx; i++) if (i >= 0) v = Math.max(v, shape({ close: 0.07, hold: 0.03, open: 0.12, depth: 1 }, t - auto[i]));
    for (const b of this.blinks) v = Math.max(v, shape(b, t - b.t));
    return v * (this.extra.noBlink ? 0 : 1);
  }
  saccadeValue(t) {
    const S = this.saccades(t + 5);
    let lo = 0, hi = S.length - 1, idx = 0;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (S[m].t <= t) { idx = m; lo = m + 1; } else hi = m - 1; }
    const cur = S[idx], prev = S[Math.max(0, idx - 1)];
    const u = smooth((t - cur.t) / 0.045);
    return { x: lerp(prev.x, cur.x, u), y: lerp(prev.y, cur.y, u) };
  }

  speechAt(t) {
    for (const L of this.lines) {
      if (t >= L.start - 0.18 && t <= L.end + 0.15) {
        const env = L.env;
        const f = (t - L.start) * env.fps;
        const i = Math.floor(f), k = f - i;
        const get = (arr, j) => (j < 0 || j >= arr.length ? 0 : arr[j]);
        let open = lerp(get(env.open, i), get(env.open, i + 1), k);
        const wide = lerp(get(env.wide, i), get(env.wide, i + 1), k);
        const slow = lerp(get(env.slow, i), get(env.slow, i + 1), k);
        // slight parting of the lips just before speaking (an intake of breath)
        if (t < L.start) open = Math.max(open, 0.12 * smooth((t - (L.start - 0.18)) / 0.18));
        return { open, wide, slow, speaking: t >= L.start && t <= L.end };
      }
    }
    return { open: 0, wide: 0, slow: 0, speaking: false };
  }

  // Base pose without hair sway (also used to compute sway from motion history).
  basePose(t) {
    const P = mixValue({}, evalSegs(this.exprSegs, t, {}, mixValue), 1);
    for (const [k, segs] of Object.entries(this.tracks)) {
      P[k] = (P[k] || 0) + evalSegs(segs, t, 0, numMix);
    }
    const idle = this.idleAmp * (1 - clamp(P.still || 0));
    const sd = this.seed;
    P.yaw = (P.yaw || 0) + idle * 0.035 * fbm(t * 0.33, sd);
    P.pitch = (P.pitch || 0) + idle * 0.03 * fbm(t * 0.29, sd + 1);
    P.roll = (P.roll || 0) + idle * 0.018 * fbm(t * 0.23, sd + 2);
    P.headX = (P.headX || 0) + idle * 0.006 * fbm(t * 0.21, sd + 3);
    return P;
  }

  pose(t) {
    const base = this.basePose(t);
    const P = { ...base };
    // speech
    const sp = this.speechAt(t);
    if (sp.open > 0 || sp.speaking) {
      P.open = clamp((P.open || 0) + sp.open * (P.mouthAmp ?? 1));
      P.mouthWide = sp.wide * 0.6;   // lip-sync mouth width; P.wide stays the eye-widening expression
      const beat = clamp(sp.open - sp.slow, -0.4, 0.6);
      P.pitch += -0.06 * beat * this.talkAmp;
      P.browTalk = (P.browTalk || 0) + Math.max(0, beat) * 0.35 * this.talkAmp;
      P.yaw += 0.025 * this.talkAmp * fbm(t * 1.3, this.seed + 7) * (sp.speaking ? 1 : 0);
    }
    // eyes
    const sac = this.saccadeValue(t);
    const sacAmp = P.sacAmp ?? 1;
    P.gazeX = (P.gazeX || 0) + sac.x * sacAmp;
    P.gazeY = (P.gazeY || 0) + sac.y * sacAmp;
    P.blink = Math.max(P.blink || 0, this.blinkValue(t));
    // breathing (phase integrated so rate changes stay smooth)
    const phase = this.breathPhase(t);
    P.breath = Math.sin(phase) * (0.6 + (P.breathDeep || 0)) * (1 - clamp(P.holdBreath || 0)) + (P.breathHold || 0);
    // tears
    if (this.tearList.length) {
      P.tears = this.tearList.filter((tr) => t >= tr.t0).map((tr) => {
        const u = (t - tr.t0) / tr.dur;
        return { side: tr.side, t: clamp(u), a: 1 - clamp((u - 1) / 2.5) };
      }).filter((x) => x.a > 0.01);
    }
    // arms
    for (const k of ['armL', 'armR']) {
      const segs = this.armSegs[k];
      if (segs.length) P[k] = evalSegs(segs, t, segs[0].v, mixValue);
    }
    // hair sway from recent head motion (lagging secondary motion)
    let sx = 0, sy = 0;
    const cur = base;
    const W = [0.35, 0.3, 0.2, 0.15];
    for (let i = 0; i < 4; i++) {
      const past = this.basePose(t - (i + 1) * 0.06);
      sx += W[i] * ((past.yaw - cur.yaw) * 0.9 + (past.roll - cur.roll) * 3 + ((past.headX || 0) - (cur.headX || 0)) * 6);
      sy += W[i] * ((past.pitch - cur.pitch) * 0.6);
    }
    P.sway = { x: clamp(sx * 3, -1.2, 1.2), y: clamp(sy * 3, -1, 1) };
    return P;
  }

  breathPhase(t) {
    // numerically integrate rate; cache at 0.05 s resolution
    if (!this._bp) this._bp = [0];
    const step = 0.05;
    const n = Math.floor(Math.max(0, t) / step);
    while (this._bp.length <= n + 1) {
      const i = this._bp.length - 1;
      const tt = i * step;
      const fast = this.tracks.breathFast ? evalSegs(this.tracks.breathFast, tt, 0, numMix) : 0;
      this._bp.push(this._bp[i] + step * (2 * Math.PI / 4.2) * (1 + fast));
    }
    const k = (Math.max(0, t) - n * step) / step;
    return lerp(this._bp[n], this._bp[n + 1], k) + (this.seed % 7);
  }
}

function hashStr(s) { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return (h >>> 0) % 100000; }

module.exports = { Actor, evalSegs };
