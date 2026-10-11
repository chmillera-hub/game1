// Timeline + per-scene helper. Timing is anchored to beats so animation stays in sync with the
// generated voice audio no matter how long each line turns out to be.
//
// ANCHOR SYNTAX (anywhere a time is accepted):
//   12.5                 absolute seconds
//   's05b03'             start of beat s05b03          's05b03.end'   end of that beat
//   's05b03.mid'         middle of the beat            's05b03+1.2'   start + 1.2 s
//   's05b03.end-0.4'     end - 0.4 s                   'scene.start+2', 'scene.end-1.5'
//
// SCENE HELPER  S = makeScene(sceneId)
//   S.start, S.end, S.dur        scene bounds (absolute seconds)
//   S.T(anchor)                  -> absolute seconds
//   S.k(t, [[anchor, value, ease?], ...])   keyframes using anchors (values: numbers or flat objects)
//   S.lip(speaker, t)            -> {open, wide, round} if `speaker` has a spoken (non-inner) line at t, else null
//   S.talking(speaker, t)        -> 0..1 (smoothed: is this character mid-line?)
//   S.beat(id)                   -> beat record {start, end, speaker, text, kind, inner, scene}
//   S.current(t)                 -> id of the beat active at t in this scene (or the last one started)
//   S.p(t)                       -> 0..1 progress through the scene
//   S.lineProgress(id, t)        -> 0..1 progress through a beat

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { clamp, kf } from './engine.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let TL = null, LIPS = null;

export function loadTimeline(file = path.join(ROOT, 'data/timeline.json'), lipFile = path.join(ROOT, 'data/lipsync.json')) {
  TL = JSON.parse(fs.readFileSync(file, 'utf8'));
  LIPS = fs.existsSync(lipFile) ? JSON.parse(fs.readFileSync(lipFile, 'utf8')) : {};
  return TL;
}
export const timeline = () => TL;

export function resolveAnchor(a, scene) {
  if (typeof a === 'number') return a;
  const m = /^([A-Za-z0-9_]+)(\.(start|end|mid))?([+-][0-9.]+)?$/.exec(a.trim());
  if (!m) throw new Error('bad anchor ' + a);
  const [, id, , which = 'start', off] = m;
  let base;
  let rec;
  if (id === 'scene') rec = scene;
  else rec = TL.beats[id] || TL.scenes.find((s) => s.id === id);
  if (!rec) throw new Error('unknown anchor id ' + id);
  base = which === 'end' ? rec.end : which === 'mid' ? (rec.start + rec.end) / 2 : rec.start;
  return base + (off ? parseFloat(off) : 0);
}

function lipFrame(id, t) {
  const L = LIPS[id];
  if (!L) return null;
  const f = (t - L.start) * L.fps;
  const i = Math.floor(f);
  if (i < 0 || i >= L.open.length) return null;
  const k = f - i;
  const j = Math.min(i + 1, L.open.length - 1);
  const g = (arr) => arr[i] + (arr[j] - arr[i]) * k;
  return { open: g(L.open), wide: g(L.wide), round: g(L.round) };
}

export function makeScene(id) {
  const sc = TL.scenes.find((s) => s.id === id);
  if (!sc) throw new Error('no scene ' + id);
  const beats = TL.order.filter((b) => TL.beats[b].scene === id).map((b) => ({ id: b, ...TL.beats[b] }));
  const allLines = TL.order.map((b) => ({ id: b, ...TL.beats[b] })).filter((b) => b.kind === 'line' && !b.inner);
  const S = {
    id, start: sc.start, end: sc.end, dur: sc.end - sc.start, scene: sc, beats,
    T: (a) => resolveAnchor(a, sc),
    k: (t, keys, defaultEase) => kf(t, keys.map(([a, v, e]) => [resolveAnchor(a, sc), v, e]), defaultEase),
    beat: (b) => TL.beats[b],
    p: (t) => clamp((t - sc.start) / (sc.end - sc.start)),
    lineProgress: (b, t) => { const r = TL.beats[b]; return clamp((t - r.start) / (r.end - r.start)); },
    current: (t) => {
      let cur = beats[0] && beats[0].id;
      for (const b of beats) if (t >= b.start) cur = b.id;
      return cur;
    },
    lip: (speaker, t) => {
      for (const b of allLines) {
        if (b.speaker === speaker && t >= b.start - 0.05 && t <= b.end + 0.05) return lipFrame(b.id, t) || { open: 0, wide: 0, round: 0 };
      }
      return null;
    },
    talking: (speaker, t) => {
      let v = 0;
      for (const b of allLines) {
        if (b.speaker !== speaker) continue;
        const a = clamp((t - (b.start - 0.15)) / 0.25), z = clamp(((b.end + 0.25) - t) / 0.3);
        v = Math.max(v, Math.min(a, z));
      }
      return v;
    },
  };
  return S;
}
