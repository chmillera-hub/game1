import { createCanvas } from '@napi-rs/canvas';
import fs from 'fs';
import { applyCamera } from '../src/engine.mjs';
import { drawHQ, drawHQForeground, HQ_VIEWS } from '../src/sets/hq.mjs';
import { drawEmotion } from '../src/chars/emotions.mjs';
const out = createCanvas(4 * 300, 300); const go = out.getContext('2d');
const c = createCanvas(720, 1280); const g = c.getContext('2d');
for (let i = 0; i < 4; i++) {
  g.setTransform(1,0,0,1,0,0);
  g.save(); applyCamera(g, { x: 450, y: 655, zoom: 0.95 });
  const st = { t: 10, consoleGlow: 1, consolePress: { [i]: 1 } };
  drawHQ(g, 'back', st);
  drawEmotion(g, 'JOY', ...HQ_VIEWS.back.anchors.consoleBack1, { t: 10, view: 'back', armL: 'pressButton', armR: 'pressButton' });
  drawHQForeground(g, 'back', st); g.restore();
  go.drawImage(c, 0, 520, 300, 300, i * 300, 0, 300, 300);
}
fs.writeFileSync('/tmp/claude-0/-home-user-game1/431c6cf3-9061-55b0-82f1-1947bb12410c/scratchpad/btn.png', out.toBuffer('image/png'));
