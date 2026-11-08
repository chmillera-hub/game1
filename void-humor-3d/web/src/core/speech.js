// Lip-sync lookup. data/lipsync.json: { beatId: { speaker, start, fps, open[], wide[], round[], close[] } }
//   speechAt('JESUS', t) -> { open, wide, round, close } | null   (null when that speaker isn't vocalizing)
import { TL } from './timeline.js';

let LS = null;
const bySpeaker = {};

export async function loadLipsync(url = '../data/lipsync.json') {
  try {
    const r = await fetch(url);
    LS = r.ok ? await r.json() : {};
  } catch (e) { LS = {}; }
  for (const [id, d] of Object.entries(LS)) {
    const spk = d.speaker || TL.data?.beats?.[id]?.speaker;
    if (!spk) continue;
    (bySpeaker[spk] = bySpeaker[spk] || []).push({ id, ...d, end: d.start + (d.open.length - 1) / (d.fps || 24) });
  }
  for (const k in bySpeaker) bySpeaker[k].sort((a, b) => a.start - b.start);
  return LS;
}

export function speechAt(speaker, t) {
  const arr = bySpeaker[speaker];
  if (!arr) return null;
  for (const d of arr) {
    if (t < d.start - 0.05) break;
    if (t <= d.end + 0.05) {
      const f = (t - d.start) * (d.fps || 24);
      const i = Math.max(0, Math.min(d.open.length - 1, Math.floor(f))), j = Math.min(d.open.length - 1, i + 1), u = Math.max(0, Math.min(1, f - i));
      const s = (a) => (a ? a[i] + (a[j] - a[i]) * u : 0);
      return { open: s(d.open), wide: s(d.wide), round: s(d.round), close: s(d.close), beat: d.id };
    }
  }
  return null;
}

// Is `speaker` mid-line at t? (talking state for body gestures)
export function isTalking(speaker, t) { return !!speechAt(speaker, t); }
