// Side-effect-free frame composer shared by render.mjs and sheet.mjs.
import fs from 'fs';
import path from 'path';
import { W, H } from './core.mjs';
import { makeCtx, ROOT_DIR } from './timeline.mjs';
import { drawOverlays } from './overlays.mjs';

const SHOTS = {};
for (const f of fs.readdirSync(path.join(ROOT_DIR, 'render/shots')).filter(f => /^s\d+\.mjs$/.test(f)).sort()) {
  try { Object.assign(SHOTS, (await import(path.join(ROOT_DIR, 'render/shots', f))).default); }
  catch (e) { console.error(`!! failed to load shots/${f}: ${e.message}`); }
}
const ctxCache = new Map();
export const ctxFor = shot => { if (!ctxCache.has(shot.id)) ctxCache.set(shot.id, makeCtx(shot)); return ctxCache.get(shot.id); };

function placeholder(g, shot, t) {
  g.fillStyle = '#334'; g.fillRect(0, 0, W, H); g.fillStyle = '#fff'; g.font = '28px UISans';
  g.fillText(`${shot.id}  t=${t.toFixed(2)}`, 30, 60);
  let line = '', y = 120;
  for (const w of shot.desc.split(' ')) { if ((line + w).length > 40) { g.fillText(line, 30, y); y += 36; line = ''; } line += w + ' '; }
  g.fillText(line, 30, y);
}

export function drawFrameAt(g, shot, t) {
  const ctx = ctxFor(shot);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  const fn = SHOTS[shot.id];
  if (fn) fn(g, t, ctx); else placeholder(g, shot, t);
  g.restore();
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); drawOverlays(g, shot, t, ctx); g.restore();
}
