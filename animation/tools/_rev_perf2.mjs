import { createCanvas } from '@napi-rs/canvas';
import { applyCamera } from '../src/engine.mjs';
import { drawHQ, drawHQForeground } from '../src/sets/hq.mjs';
import { drawCage } from '../src/sets/props.mjs';
import { drawVoid } from '../src/chars/void.mjs';
import { drawFear } from '../src/chars/fear.mjs';
const c = createCanvas(720, 1280), g = c.getContext('2d');
const cam = { x: 440, y: 1430, zoom: 3.0 };
const st = { t: 1, lightsDim: 0.3, mist: 0.48 };
const tests = {
  hq: (t) => drawHQ(g, 'backOfMind', { ...st, t }),
  voidC: (t) => drawVoid(g, 700, 1600, 0.9, { t, headTurn: -0.65, headDown: 0.12, idle: 0.5, cosmos: 0.5, cosmosOpts: { seed: 7, glyphs: 0 }, shadowSpread: 0.7, handL: { bend: 1, show: 0, defer: 'hand' } }),
  void0: (t) => drawVoid(g, 700, 1600, 0.9, { t, headTurn: -0.65, headDown: 0.12, idle: 0.5, cosmos: 0, shadowSpread: 0.7, handL: { bend: 1, show: 0, defer: 'hand' } }),
  voidNoShadow: (t) => drawVoid(g, 700, 1600, 0.9, { t, headTurn: -0.65, headDown: 0.12, idle: 0.5, cosmos: 0, shadow: false, handL: { bend: 1, show: 0, defer: 'hand' } }),
  cage: (t) => { drawCage(g, 430, 1630, 0.952, { t, door: 0.9, locked: 0, layer: 'back' }); drawCage(g, 430, 1630, 0.952, { t, door: 0.9, locked: 0, layer: 'front' }); },
  fear: (t) => drawFear(g, 440, 1648, 0.97, { t, facing: -1, face: { tears: 0.6 } }),
  fg: (t) => drawHQForeground(g, 'backOfMind', { ...st, t }),
};
for (const [k, fn] of Object.entries(tests)) {
  const ms = [];
  for (let i = 0; i < 40; i++) {
    g.setTransform(1,0,0,1,0,0); g.fillStyle='#000'; g.fillRect(0,0,720,1280); g.getImageData(0,0,1,1);
    g.save(); applyCamera(g, cam);
    const s0 = performance.now(); fn(1 + i / 24); g.getImageData(0, 0, 1, 1); ms.push(performance.now() - s0);
    g.restore();
  }
  ms.sort((a, b) => a - b); console.log(k.padEnd(14), ms[20].toFixed(1));
}
