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
//
// TIME WARP (data/timewarp.json, from tools/speed_dialogue.py): scenes are authored in STORY time
// (data/timeline.json). The film plays in PLAY time, where spoken lines are faster. The renderer maps each
// output frame with playToStory(); lip-sync data is recorded in play time and looked up via storyToPlay().
// Without timewarp.json both maps are the identity.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { clamp, kf } from './engine.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let TL = null, LIPS = null, KS = [0], KP = [0], PLAY = null;

export function loadTimeline(file = path.join(ROOT, 'data/timeline.json'), lipFile = path.join(ROOT, 'data/lipsync.json'),
  warpFile = path.join(ROOT, 'data/timewarp.json'), playFile = path.join(ROOT, 'data/timeline_play.json')) {
  TL = JSON.parse(fs.readFileSync(file, 'utf8'));
  LIPS = fs.existsSync(lipFile) ? JSON.parse(fs.readFileSync(lipFile, 'utf8')) : {};
  KS = [0]; KP = [0]; PLAY = null;
  if (fs.existsSync(warpFile) && fs.existsSync(playFile)) {
    const W = JSON.parse(fs.readFileSync(warpFile, 'utf8'));
    KS = W.knots.map((k) => k[0]);
    KP = W.knots.map((k) => k[1]);
    PLAY = JSON.parse(fs.readFileSync(playFile, 'utf8'));
  }
  return TL;
}
export const timeline = () => TL;
/** the timeline as played (line beats shortened); falls back to the story timeline */
export const playTimeline = () => PLAY || TL;

function interp(x, X, Y) {
  const n = X.length;
  if (x >= X[n - 1]) return Y[n - 1] + (x - X[n - 1]);
  if (x <= X[0]) return Y[0] + (x - X[0]);
  let lo = 0, hi = n - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (X[m] <= x) lo = m; else hi = m; }
  const k = X[hi] === X[lo] ? 0 : (x - X[lo]) / (X[hi] - X[lo]);
  return Y[lo] + (Y[hi] - Y[lo]) * k;
}
export const storyToPlay = (t) => interp(t, KS, KP);
export const playToStory = (t) => interp(t, KP, KS);

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

function lipFrame(id, tStory) {
  const L = LIPS[id];
  if (!L) return null;
  const f = (storyToPlay(tStory) - L.start) * L.fps;   // lip data is recorded in play time
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
