// Contact sheet for src/sets/props.mjs + src/sets/realroom.mjs  →  out/sheet_props.png
//   node tools/sheet_props.mjs [out.png] [--time]
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { drawCage, drawNotebook, drawDeskLamp, CAGE_ANCHORS, cagePoint } from '../src/sets/props.mjs';
import { drawFear } from '../src/chars/fear.mjs';
import { EXPR } from '../src/face.mjs';
import { drawRealRoom, drawRealRoomForeground, drawLitByRoom, REALROOM } from '../src/sets/realroom.mjs';
import { applyCamera } from '../src/engine.mjs';
let SELF = null; // the real narrator if the self module is available, else a placeholder silhouette
if (!process.argv.includes('--placeholder')) { try { SELF = await import('../src/chars/self.mjs'); } catch (e) { console.warn('self.mjs unavailable:', e.message); } }

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
for (const [f, name] of [['Caveat.ttf', 'Caveat'], ['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand']]) {
  GlobalFonts.registerFromPath(path.join(ROOT, 'assets/fonts', f), name);
}
const args = process.argv.slice(2);
const outPath = args.find((a) => !a.startsWith('--')) || path.join(ROOT, 'out/sheet_props.png');

// ---- Fear inside the cage, gripping the bars (back layer → Fear → front layer)
function fearInCage(g, cx, cy, s, t, cageState = {}) {
  const st = { t, door: 0, locked: 1, shake: 0.8, ...cageState };
  drawCage(g, cx, cy, s, { ...st, layer: 'back' });
  const [fx, fy] = cagePoint('occupantFront', cx, cy, s, st);
  const gl = cagePoint('gripL', cx, cy, s, st), gr = cagePoint('gripR', cx, cy, s, st);
  const loc = (p) => [(p[0] - fx) / s, (p[1] - fy) / s];
  drawFear(g, fx, fy, s, {
    t, tremble: 0.7, lean: 0.02,
    face: { ...EXPR.crying, tearL: 0.55, lookY: -0.1 },
    armL: { target: loc(gl), bend: 1, front: true, hand: 'grip' },
    armR: { target: loc(gr), bend: -1, front: true, hand: 'grip' },
  });
  drawCage(g, cx, cy, s, { ...st, layer: 'front', grips: ['gripL', 'gripR'] });
}

function placeholderSelf(g, x, y, s, layer = 'all', t = 2) {
  if (SELF) {
    try {
      SELF.drawSelf(g, x, y, s, { t, seated: true, layer, outfit: 'sweater', headTilt: 0.12, headTurn: 0.25, bodyTurn: 0.2,
        face: { ...(SELF.SELF_EXPR.tenderSmile || {}), lookY: 0.55, lookX: -0.1, noAutoBlink: true } });
      return;
    } catch (e) { console.warn('drawSelf failed:', e.message); }
  }
  if (layer === 'front') return;
  g.save();
  g.translate(x, y); g.scale(s, s);
  // torso (dusty teal sweater), cut at the desk line (origin)
  g.fillStyle = '#4f8c8a'; g.strokeStyle = '#1f2f35'; g.lineWidth = 3;
  g.beginPath();
  g.moveTo(-150, 0); g.bezierCurveTo(-150, -120, -120, -190, -60, -205);
  g.lineTo(60, -205); g.bezierCurveTo(120, -190, 150, -120, 150, 0);
  g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#d9a27e';
  g.beginPath(); g.roundRect(-22, -235, 44, 40, 10); g.fill(); g.stroke();
  g.beginPath(); g.ellipse(0, -300, 70, 80, 0, 0, Math.PI * 2); g.fill(); g.stroke();
  g.fillStyle = '#2f2433';
  g.beginPath(); g.ellipse(0, -340, 76, 52, 0, Math.PI, Math.PI * 2); g.fill();
  g.beginPath(); g.ellipse(-20, -345, 66, 40, -0.3, 0, Math.PI * 2); g.fill();
  g.restore();
}

// ---- timing
let flushCtx = null; // reading a pixel forces any deferred rasterisation, so timings are honest
function time(label, fn, n = 50) {
  fn(0);
  flushCtx && flushCtx.getImageData(0, 0, 2, 2);
  const t0 = performance.now();
  for (let i = 0; i < n; i++) { fn(i); if (flushCtx) flushCtx.getImageData(0, 0, 2, 2); }
  const ms = (performance.now() - t0) / n;
  console.log(`${label.padEnd(44)} ${ms.toFixed(2)} ms`);
  return ms;
}

// ---- sheet layout
const CW = 420, CH = 620, NBH = 430;
const leftW = CW * 3, roomW = 720;
const SW = leftW + roomW, SH = CH * 2 + NBH * 2;
const c = createCanvas(SW, SH), g = c.getContext('2d');
g.fillStyle = '#17142a'; g.fillRect(0, 0, SW, SH);

function cell(i, j, w, h, label, bg, fn) {
  const x = i, y = j;
  const gr = g.createLinearGradient(0, y, 0, y + h);
  gr.addColorStop(0, bg[0]); gr.addColorStop(1, bg[1]);
  g.fillStyle = gr; g.fillRect(x, y, w, h);
  g.save(); g.beginPath(); g.rect(x, y, w, h); g.clip();
  fn(x, y, w, h);
  g.restore();
  g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(x, y, w, 30);
  g.fillStyle = '#fff'; g.font = '19px sans-serif'; g.fillText(label, x + 10, y + 21);
  g.strokeStyle = 'rgba(255,255,255,0.15)'; g.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
}
const HQ_BG = ['#1d1936', '#0d0b1c'];
const cs = 0.92;
cell(0, 0, CW, CH, 'cage: closed + locked', HQ_BG, (x, y, w, h) => drawCage(g, x + w / 2, y + h - 60, cs, { t: 1 }));
cell(CW, 0, CW, CH, 'cage: door 0.5, unlocked', HQ_BG, (x, y, w, h) => drawCage(g, x + w / 2 + 20, y + h - 60, cs, { t: 1, door: 0.5, locked: 0 }));
cell(CW * 2, 0, CW, CH, 'cage: rust 1, door 1 (+ falling flake)', HQ_BG, (x, y, w, h) => drawCage(g, x + w / 2 + 40, y + h - 60, cs, { t: 1, door: 1, locked: 0, rust: 1, flake: 0.45 }));
cell(0, CH, CW, CH, 'Fear inside: back/Fear/front, shake .8', HQ_BG, (x, y, w, h) => fearInCage(g, x + w / 2, y + h - 60, cs, 2.37));
cell(CW, CH, CW, CH, 'cage: rust .5, door .25, dim .55', HQ_BG, (x, y, w, h) => drawCage(g, x + w / 2, y + h - 60, cs, { t: 1, door: 0.25, locked: 0, rust: 0.5, dim: 0.55 }));
cell(CW * 2, CH, CW, CH, 'lamp: on 1 / on 0 (facing -1)', ['#3a2a3a', '#20182a'], (x, y, w, h) => {
  drawDeskLamp(g, x + 110, y + h - 80, 1, { on: 1, t: 1 });
  drawDeskLamp(g, x + 330, y + h - 330, 0.8, { on: 0, facing: -1 });
});
const nbBG = ['#6a4a36', '#4a3020'];
cell(0, CH * 2, CW, NBH, 'notebook: closed (open 0)', nbBG, (x, y, w, h) => drawNotebook(g, x + w / 2, y + h / 2 + 10, 1.15, { open: 0 }));
cell(CW, CH * 2, CW, NBH, 'notebook: open .35 (cover lifting)', nbBG, (x, y, w, h) => drawNotebook(g, x + w / 2 + 20, y + h / 2 + 10, 0.8, { open: 0.35 }));
cell(CW * 2, CH * 2, CW, NBH, 'notebook: open .7', nbBG, (x, y, w, h) => drawNotebook(g, x + w / 2, y + h / 2 + 10, 0.8, { open: 0.7 }));
cell(0, CH * 2 + NBH, CW * 2, NBH, 'notebook: open 1 (spread) scale 1.35', nbBG, (x, y, w, h) => drawNotebook(g, x + w / 2, y + h / 2 + 12, 1.35, { open: 1 }));
cell(CW * 2, CH * 2 + NBH, CW, NBH, 'flat 1: open 1 / closed gold (default) + blue', nbBG, (x, y, w, h) => {
  drawNotebook(g, x + w / 2, y + 140, 0.75, { open: 1, flat: 1 });
  drawNotebook(g, x + w / 2 - 90, y + 320, 0.6, { open: 0, flat: 1, rot: -0.12 });
  drawNotebook(g, x + w / 2 + 90, y + 320, 0.6, { open: 0, flat: 1, rot: 0.08, palette: 'blue' });
});
// ---- the real room (full 720x1280)
function roomFrame(st, cam, nb) {
  applyCamera(g, cam);
  drawRealRoom(g, st);
  const [sx, sy, ss] = REALROOM.anchors.selfSeated;
  drawLitByRoom(g, st, (c) => placeholderSelf(c, sx, sy, ss, 'body', st.t));
  drawRealRoomForeground(g, st);
  drawLitByRoom(g, st, (c) => placeholderSelf(c, sx, sy, ss, 'front', st.t));
  const [nx, ny, ns] = REALROOM.anchors.notebook;
  if (nb) drawNotebook(g, nx, ny, ns, nb);
}
const RS = { t: 2, lamp: 1, moon: 1, dusk: 0 };
cell(leftW, 0, roomW, 1280, 'REAL_ROOM full camera, notebook open on the desk', ['#000', '#000'], (x, y) => {
  g.save(); g.translate(x, y);
  roomFrame(RS, REALROOM.cameras.full, { open: 1, flat: 1, rot: -0.04 });
  g.restore();
});
cell(leftW, 1280, roomW / 2, SH - 1280, 'opening cam + titleBox, thirds', ['#000', '#000'], (x, y, w, h) => {
  g.save(); g.translate(x, y + 90); g.scale(0.5, 0.5);
  g.save(); g.beginPath(); g.rect(0, 0, 720, 1280); g.clip();
  roomFrame(RS, REALROOM.cameras.opening, { open: 1, flat: 1, rot: -0.04 });
  const T = REALROOM.titleBox;
  g.fillStyle = '#fff3dc'; g.textAlign = 'center'; g.font = '600 52px "Caveat"';
  g.fillText('The Void', T.x + T.w / 2, T.y + T.h * 0.42);
  g.fillText('and My Fear', T.x + T.w / 2, T.y + T.h * 0.78);
  g.textAlign = 'start';
  g.strokeStyle = 'rgba(255,90,90,0.7)'; g.lineWidth = 2; g.strokeRect(T.x, T.y, T.w, T.h);
  g.restore();
  g.strokeStyle = 'rgba(120,255,140,0.6)'; g.lineWidth = 2;
  for (const yy of [427, 853, 1088]) { g.beginPath(); g.moveTo(0, yy); g.lineTo(720, yy); g.stroke(); }
  g.restore();
});
cell(leftW + roomW / 2, 1280, roomW / 2, SH - 1280, 'ending: lamp 0, starHood .9, wink', ['#000', '#000'], (x, y, w, h) => {
  g.save(); g.translate(x, y + 90); g.scale(0.5, 0.5);
  g.beginPath(); g.rect(0, 0, 720, 1280); g.clip();
  roomFrame({ t: 7, lamp: 0, moon: 1, fairy: 0.3, starHood: 0.9, starWink: 0.8 }, REALROOM.cameras.full, { open: 0, flat: 1, rot: -0.06 });
  g.restore();
});
fs.writeFileSync(outPath, c.toBuffer('image/png'));
console.log('wrote', outPath);

if (args.includes('--time')) {
  const tc = createCanvas(720, 1280), tg = tc.getContext('2d');
  flushCtx = tg;
  time('drawCage all (clean, shake 0)', (i) => drawCage(tg, 360, 900, 1, { t: i * 0.04 }));
  time('drawCage all (rust 1, door 1, shake 1)', (i) => drawCage(tg, 360, 900, 1, { t: i * 0.04, rust: 1, door: 1, locked: 0, shake: 1 }));
  time('drawCage back+front w/ grips, shake', (i) => { drawCage(tg, 360, 900, 1, { t: i * 0.04, shake: 1, layer: 'back' }); drawCage(tg, 360, 900, 1, { t: i * 0.04, shake: 1, layer: 'front', grips: ['gripL', 'gripR'] }); });
  time('drawFear (reference)', (i) => drawFear(tg, 360, 900, 1, { t: i * 0.04, face: EXPR.crying }));
  time('drawNotebook closed', (i) => drawNotebook(tg, 360, 640, 1, { open: 0 }));
  time('drawNotebook flipping', (i) => drawNotebook(tg, 360, 640, 1.5, { open: (i % 50) / 50 }));
  time('drawDeskLamp on', (i) => drawDeskLamp(tg, 360, 900, 1, { on: 1, t: i * 0.04 }));
  time('drawRealRoom zoom1', (i) => drawRealRoom(tg, { t: i * 0.04, lamp: 1, moon: 1 }));
  time('drawRealRoomForeground zoom1', (i) => drawRealRoomForeground(tg, { t: i * 0.04, lamp: 1, moon: 1 }));
  tg.save(); tg.translate(360, 640); tg.scale(1.8, 1.8); tg.translate(-400, -700);
  time('drawRealRoom zoom1.8', (i) => drawRealRoom(tg, { t: i * 0.04, lamp: 1, moon: 1 }));
  time('drawRealRoomForeground zoom1.8', (i) => drawRealRoomForeground(tg, { t: i * 0.04, lamp: 1, moon: 1 }));
  tg.restore();
  tg.save(); applyCamera(tg, REALROOM.cameras.opening);
  time('room opening cam (both layers + notebook)', (i) => { drawRealRoom(tg, { t: i * 0.04 }); drawRealRoomForeground(tg, { t: i * 0.04 }); drawNotebook(tg, ...REALROOM.anchors.notebook, { open: 1, flat: 1 }); });
  tg.restore();
  time('drawLitByRoom (empty pass, overhead only)', (i) => drawLitByRoom(tg, { t: i * 0.04, lamp: 0.5 }, () => {}));
  time('room ending (lamp 0, starHood, wink)', (i) => { drawRealRoom(tg, { t: i * 0.04, lamp: 0, starHood: 1, starWink: 0.5 }); drawRealRoomForeground(tg, { t: i * 0.04, lamp: 0 }); });
  time('room lamp fading (crossfade)', (i) => { drawRealRoom(tg, { t: i * 0.04, lamp: (i % 50) / 50, moon: 1 }); drawRealRoomForeground(tg, { t: i * 0.04, lamp: (i % 50) / 50, moon: 1 }); });
}
