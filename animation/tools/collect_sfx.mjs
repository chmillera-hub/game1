// Gather `export const sfx = [...]` from every scene module, resolve anchors to absolute seconds.
//   node tools/collect_sfx.mjs  -> data/sfx_events.json
import fs from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { loadTimeline, resolveAnchor, storyToPlay } from '../src/timeline.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TL = loadTimeline();
const events = [];
const RHYTHMIC = new Set(['footsteps', 'heartbeat', 'console_beeps']);
for (const f of fs.readdirSync(path.join(ROOT, 'src/scenes')).filter((f) => f.endsWith('.mjs')).sort()) {
  const m = await import(pathToFileURL(path.join(ROOT, 'src/scenes', f)).href);
  if (!m.id || !m.sfx) continue;
  const sc = TL.scenes.find((s) => s.id === m.id);
  for (const e of m.sfx) {
    try {
      // anchors resolve in story time; the soundtrack is assembled in play time
      const at = storyToPlay(resolveAnchor(e.at, sc));
      const until = e.until != null ? storyToPlay(resolveAnchor(e.until, sc)) : null;
      // rhythmic multi-hit samples inside a sped-up line follow the picture's tempo (steps stay on the feet)
      let rate = e.rate ?? 1;
      if (RHYTHMIC.has(e.name)) {
        const s0 = resolveAnchor(e.at, sc);
        const slope = (storyToPlay(s0 + 0.4) - storyToPlay(s0)) / 0.4;
        if (slope < 0.99) rate *= 1 / slope;
      }
      events.push({ scene: m.id, name: e.name, at: +at.toFixed(3), until: until != null ? +until.toFixed(3) : null,
        gain: e.gain ?? 0, loop: !!e.loop, pan: e.pan ?? 0, fade: e.fade ?? 0.3, rate: +rate.toFixed(4) });
    } catch (err) {
      console.error(`bad sfx in ${f}:`, e, err.message);
    }
  }
}
events.sort((a, b) => a.at - b.at);
fs.writeFileSync(path.join(ROOT, 'data/sfx_events.json'), JSON.stringify(events, null, 1));
console.log(`${events.length} sfx events`);
