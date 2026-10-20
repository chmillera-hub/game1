// Loads build/timeline.json + build/lines.json and builds the per-shot context passed to shot draw functions.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { clamp, lerp } from './core.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/timeline.json'), 'utf8'));
const LINES = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/lines.json'), 'utf8'));
export const ROOT_DIR = ROOT;

export const shotById = id => TL.shots.find(s => s.id === id);
export const shotAt = T => TL.shots.find(s => T >= s.start && T < s.end) ?? TL.shots[TL.shots.length - 1];

const norm = w => w.toLowerCase().replace(/[^a-z0-9']/g, '');

// ctx API (all times are LOCAL to the shot, in seconds, 0 = shot start):
//   ctx.dur                      shot duration
//   ctx.line(id)                 {start, end, text, speaker, vo, words:[{w,start,end}]}  (local times)
//   ctx.lines                    array of the shot's lines (local times)
//   ctx.word(lineId, key)        {start,end} of a word: key = word text (case/punct-insensitive) or index
//   ctx.mouth(speaker, t)        {open, wide, round, press} lip-sync for an on-screen speaker (0s when silent/VO)
//   ctx.talking(speaker, t)      0..1 how strongly the speaker is currently voicing (on-screen, non-VO lines)
//   ctx.speaking(speaker, t)     true while ANY line (incl. VO) of speaker is active
//   ctx.T0                       absolute start time of the shot in the film
//   ctx.shot                     raw shot record (id, desc, framing...)
export function makeCtx(shot) {
  const lines = shot.lines.map(l => ({ ...l, start: l.start - shot.start, end: l.end - shot.start,
    words: l.words.map(w => ({ ...w, start: w.start - shot.start, end: w.end - shot.start })) }));
  const byId = Object.fromEntries(lines.map(l => [l.id, l]));
  const ctx = {
    dur: shot.dur, T0: shot.start, shot, lines,
    line: id => { const l = byId[id]; if (!l) throw new Error(`line ${id} not in shot ${shot.id}`); return l; },
    word(lineId, key) {
      const l = ctx.line(lineId);
      const w = typeof key === 'number' ? l.words[key] : l.words.find(w => norm(w.w) === norm(key));
      if (!w) throw new Error(`word ${key} not in ${lineId}`); return w;
    },
    mouth(speaker, t) {
      const r = { open: 0, wide: 0, round: 0, press: 0 };
      for (const l of lines) {
        if (l.speaker !== speaker || l.vo || t < l.start || t > l.end + 0.05) continue;
        const m = LINES[l.id].mouth, i = (t - l.start) * m.hz, i0 = Math.floor(i), f = i - i0;
        const at = (arr) => lerp(arr[clamp(i0, 0, arr.length - 1)] ?? 0, arr[clamp(i0 + 1, 0, arr.length - 1)] ?? 0, f);
        r.open = at(m.open); r.wide = at(m.wide); r.round = at(m.round); r.press = at(m.press);
      }
      return r;
    },
    talking(speaker, t) { const m = ctx.mouth(speaker, t); return clamp(m.open * 1.4 + m.press * 0.3); },
    speaking(speaker, t) { return lines.some(l => l.speaker === speaker && t >= l.start && t <= l.end); },
  };
  return ctx;
}
