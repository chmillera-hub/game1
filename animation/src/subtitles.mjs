// Burned-in captions (data/subtitles.json from tools/build_subtitles.py; positions from `render.mjs --place-subs`).
// Times are PLAY time. Narration and inner thoughts are italic; on-screen speakers get a soft tint of their colour.
// Positions keep clear of the social-app UI: the bottom 15% (captions/buttons) and the right-hand button column.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { clamp } from './engine.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const FILE = path.join(ROOT, 'data/subtitles.json');

export const SUB_STYLE = {
  size: 32, lineH: 42, padX: 18, padY: 11, maxW: 520, cx: 350, radius: 16,
  box: 'rgba(13,10,28,0.64)', edge: 'rgba(255,255,255,0.10)',
  colors: { NARRATOR: '#ffffff', CONSCIOUSNESS: '#fff0d4', FEAR: '#ded4ff', JOY: '#ffe39a', SADNESS: '#d4e7ff', ANGER: '#ffcfc4', CALM: '#cff3e2' },
};
// vertical centre of the caption block for each placement
export const SUB_POS = { low: 1022, mid: 868, upper: 372, top: 214 };

let CAPS = null;
export function loadSubtitles() {
  CAPS = fs.existsSync(FILE) ? JSON.parse(fs.readFileSync(FILE, 'utf8')).captions : [];
  return CAPS;
}
export const captions = () => CAPS || loadSubtitles();

const fontFor = (c) => `${c.speaker === 'NARRATOR' || c.inner ? 'italic ' : ''}600 ${SUB_STYLE.size}px Inter`;
const layoutCache = new Map();

/** split a caption into 1–3 balanced lines that fit the box */
export function layout(g, c) {
  const key = c.beat + ':' + c.idx;
  if (layoutCache.has(key)) return layoutCache.get(key);
  g.save();
  g.font = fontFor(c);
  const words = c.text.split(' ');
  const width = (ws) => g.measureText(ws.join(' ')).width;
  let lines;
  if (width(words) <= SUB_STYLE.maxW) lines = [words.join(' ')];
  else {
    let best = null;
    for (let i = 1; i < words.length; i++) {
      const a = width(words.slice(0, i)), b = width(words.slice(i));
      if (a > SUB_STYLE.maxW || b > SUB_STYLE.maxW) continue;
      const score = Math.max(a, b) + (/[,.?!]$/.test(words[i - 1]) ? -40 : 0);
      if (!best || score < best.score) best = { score, i };
    }
    if (best) lines = [words.slice(0, best.i).join(' '), words.slice(best.i).join(' ')];
    else {
      lines = []; let cur = [];
      for (const w of words) {
        if (cur.length && width([...cur, w]) > SUB_STYLE.maxW) { lines.push(cur.join(' ')); cur = []; }
        cur.push(w);
      }
      if (cur.length) lines.push(cur.join(' '));
    }
  }
  const tw = Math.max(...lines.map((l) => g.measureText(l).width));
  g.restore();
  const out = { lines, w: tw + SUB_STYLE.padX * 2, h: lines.length * SUB_STYLE.lineH + SUB_STYLE.padY * 2 - 6 };
  layoutCache.set(key, out);
  return out;
}

/** screen rectangle of a caption at a placement */
export function captionRect(g, c, pos) {
  const L = layout(g, c);
  const cy = SUB_POS[pos] ?? SUB_POS.low;
  return { x0: SUB_STYLE.cx - L.w / 2, x1: SUB_STYLE.cx + L.w / 2, y0: cy - L.h / 2, y1: cy + L.h / 2 };
}

export function activeCaption(t) {
  for (const c of captions()) if (t >= c.start && t < c.end) return c;
  return null;
}

export function drawSubtitles(g, t) {
  const c = activeCaption(t);
  if (!c) return;
  const a = clamp(Math.min((t - c.start) / 0.12, (c.end - t) / 0.12));
  if (a <= 0) return;
  const L = layout(g, c);
  const r = captionRect(g, c, c.pos_override || c.pos || 'low');
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = a;
  g.globalCompositeOperation = 'source-over';
  g.beginPath();
  g.roundRect(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0, SUB_STYLE.radius);
  g.fillStyle = SUB_STYLE.box;
  g.fill();
  g.strokeStyle = SUB_STYLE.edge;
  g.lineWidth = 1.5;
  g.stroke();
  g.font = fontFor(c);
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillStyle = c.inner ? '#cbbcff' : (SUB_STYLE.colors[c.speaker] || '#ffffff');
  const top = r.y0 + SUB_STYLE.padY + SUB_STYLE.lineH / 2 - 3;
  L.lines.forEach((line, i) => g.fillText(line, (r.x0 + r.x1) / 2, top + i * SUB_STYLE.lineH));
  g.restore();
}
