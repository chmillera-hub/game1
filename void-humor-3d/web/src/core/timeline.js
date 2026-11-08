// Timeline: absolute (play-time) seconds for every scene/beat, and keyframe helpers.
//
//   T('s03b02')            -> start of beat s03b02
//   T('s03b02.end-0.3')    -> 0.3 s before it ends
//   T('s03.start+1.2')     -> scene start + 1.2
//   T(12.5)                -> 12.5 (numbers pass through)
//   k(t, [['s03b02', 0], ['s03b02+0.4', 1, 'outBack'], ['s03b02.end', 0, 'inOut']])
//       keyframes: [time, value, easeIntoThisKey?]. Values: number | number[] | {k: number}.
//       Before the first key -> first value; after the last -> last value.
import { ease as EASE, clamp } from './util.js';

export const TL = { data: null, fps: 24 };

export async function loadTimeline(url = '../data/timeline.json') {
  const r = await fetch(url);
  TL.data = await r.json();
  TL.fps = TL.data.fps || 24;
  return TL.data;
}

const cache = new Map();
export function T(ref) {
  if (typeof ref === 'number') return ref;
  if (cache.has(ref)) return cache.get(ref);
  const m = /^([a-z0-9_]+?)(?:\.(start|end|mid))?([+-]\d*\.?\d+)?$/i.exec(ref.replace(/\s+/g, ''));
  if (!m) throw new Error('bad time ref ' + ref);
  const [, id, which = 'start', off] = m;
  const d = TL.data;
  let rec = d.beats[id] || d.scenes.find((s) => s.id === id);
  if (!rec) throw new Error('unknown beat/scene ' + id);
  let t = which === 'end' ? rec.end : which === 'mid' ? (rec.start + rec.end) / 2 : rec.start;
  if (off) t += parseFloat(off);
  cache.set(ref, t);
  return t;
}

export const beat = (id) => TL.data.beats[id];
export const scene = (id) => TL.data.scenes.find((s) => s.id === id);
export const beatsOf = (sceneId) => TL.data.order.filter((b) => TL.data.beats[b].scene === sceneId);
// Beats of a scene spoken by a speaker (for lip-sync / talking state)
export const linesOf = (speaker) => TL.data.order.filter((b) => TL.data.beats[b].speaker === speaker && TL.data.beats[b].kind !== 'silent');

function mix(a, b, u) {
  if (typeof a === 'number') return a + (b - a) * u;
  if (Array.isArray(a)) return a.map((x, i) => x + (b[i] - x) * u);
  const o = {};
  for (const key in a) o[key] = (typeof a[key] === 'number' && typeof b[key] === 'number') ? a[key] + (b[key] - a[key]) * u : (u < 0.5 ? a[key] : b[key]);
  for (const key in b) if (!(key in o)) o[key] = b[key];
  return o;
}

export function k(t, keys) {
  if (!keys.length) return 0;
  const ks = keys.map((kk) => [T(kk[0]), kk[1], kk[2] || 'inOut']);
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) {
    if (t < ks[i][0]) {
      const [t0, v0] = ks[i - 1];
      const [t1, v1, e] = ks[i];
      const u = t1 > t0 ? clamp((t - t0) / (t1 - t0)) : 1;
      const f = EASE[e] || EASE.inOut;
      return mix(v0, v1, f(u));
    }
  }
  return ks[ks.length - 1][1];
}

// 0 -> 1 -> 0 envelope: rises over [a, a+fin], holds, falls over [b-fout, b]
export function env(t, a, b, fin = 0.3, fout = 0.3) {
  a = T(a); b = T(b);
  if (t <= a || t >= b) return 0;
  const up = fin > 0 ? clamp((t - a) / fin) : 1;
  const dn = fout > 0 ? clamp((b - t) / fout) : 1;
  return EASE.inOut(Math.min(up, dn));
}

export const between = (t, a, b) => t >= T(a) && t < T(b);
// Local 0..1 progress of t through [a,b]
export const prog = (t, a, b, e = 'linear') => EASE[e](clamp((t - T(a)) / (T(b) - T(a))));
