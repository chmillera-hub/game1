// Preview renderer for src/bg/hearth.js — writes build/preview/hearth_*.png (540x960)
// usage: node tools/preview_hearth.js [filterSubstring]
'use strict';
const path = require('path'), fs = require('fs');
const { createCanvas } = require('@napi-rs/canvas');
const H = require('../src/bg/hearth.js');
const OUT = path.join(__dirname, '..', 'build', 'preview');
fs.mkdirSync(OUT, { recursive: true });
const filt = process.argv[2] || '';

const full = createCanvas(1080, 1920), ctx = full.getContext('2d');
const small = createCanvas(540, 960), sctx = small.getContext('2d');

function standing(c, x, y, col) { // feet at (x,y), 950 tall
  c.save(); c.fillStyle = col; c.globalAlpha = 0.35;
  c.beginPath(); c.ellipse(x, y - 875, 62, 75, 0, 0, 7); c.fill();
  c.beginPath(); c.moveTo(x - 120, y - 760); c.lineTo(x + 120, y - 760); c.lineTo(x + 95, y - 430); c.lineTo(x + 70, y); c.lineTo(x - 70, y); c.lineTo(x - 95, y - 430); c.closePath(); c.fill();
  c.restore();
}
function seated(c, x, y, col) { // hip at (x,y)
  c.save(); c.fillStyle = col; c.globalAlpha = 0.35;
  c.beginPath(); c.ellipse(x, y - 455, 62, 75, 0, 0, 7); c.fill();
  c.beginPath(); c.moveTo(x - 115, y - 345); c.lineTo(x + 115, y - 345); c.lineTo(x + 90, y); c.lineTo(x - 90, y); c.closePath(); c.fill();
  c.fillRect(x - 90, y - 30, 180, 40); c.fillRect(x + 60, y, 40, 190);
  c.restore();
}
function floorSit(c, x, y, col) { // sitting on floor, hip at (x,y)
  c.save(); c.fillStyle = col; c.globalAlpha = 0.35;
  c.beginPath(); c.ellipse(x, y - 455, 60, 72, 0, 0, 7); c.fill();
  c.beginPath(); c.moveTo(x - 110, y - 345); c.lineTo(x + 110, y - 345); c.lineTo(x + 95, y); c.lineTo(x - 95, y); c.closePath(); c.fill();
  c.beginPath(); c.ellipse(x + 90, y - 10, 140, 34, 0, 0, 7); c.fill();
  c.restore();
}

function render(name, cam, o, opt = {}) {
  if (filt && !name.includes(filt)) return null;
  const t = opt.t ?? 12.3;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#ff00ff'; ctx.fillRect(0, 0, 1080, 1920);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.translate(540, 960); ctx.scale(cam.zoom, cam.zoom); ctx.translate(-cam.x, -cam.y);
  const t0 = process.hrtime.bigint();
  H.drawBack(ctx, t, o); ctx.getImageData(0, 0, 1, 1);
  const t1 = process.hrtime.bigint();
  if (opt.vision) { H.drawVision(ctx, t, opt.vision); ctx.getImageData(0, 0, 1, 1); }
  const t2 = process.hrtime.bigint();
  if (opt.figs !== false) {
    const A = H.ENV.anchors;
    seated(ctx, A.angerSeat.x, A.angerSeat.y, '#d0402f');
    seated(ctx, A.mayaSeat.x, A.mayaSeat.y, '#7a8450');
    standing(ctx, A.annoyWindow.x, A.annoyWindow.y, '#ffd84a');
    standing(ctx, (A.fearPace.x0 + A.fearPace.x1) / 2, A.fearPace.y, '#ff9a3c');
    floorSit(ctx, A.sadCorner.x, A.sadCorner.y, '#7fb2e5');
  }
  const t3 = process.hrtime.bigint();
  H.drawFront(ctx, t, o); ctx.getImageData(0, 0, 1, 1);
  const t4 = process.hrtime.bigint();
  const ms = { back: Number(t1 - t0) / 1e6, vision: Number(t2 - t1) / 1e6, front: Number(t4 - t3) / 1e6 };
  sctx.drawImage(full, 0, 0, 540, 960);
  fs.writeFileSync(path.join(OUT, `hearth_${name}.png`), small.toBuffer('image/png'));
  console.log(name.padEnd(28), `back ${ms.back.toFixed(1)}ms  vision ${ms.vision.toFixed(1)}ms  front ${ms.front.toFixed(1)}ms`);
  return ms;
}

const tc0 = process.hrtime.bigint();
H.drawBack(createCanvas(10, 10).getContext('2d'), 0, {}); // build cache
console.log('cache build', (Number(process.hrtime.bigint() - tc0) / 1e6).toFixed(0), 'ms');

const W = { x: 800, y: 1000, zoom: 0.72 };
render('wide', W, {});
render('wide_t2', W, {}, { t: 40.7 });
render('wide_night', W, { view: 'night' });
render('wide_dawn', W, { view: 'dawn' });
render('wide_nana', W, { view: 'nana' });
render('wide_fire03', W, { fire: 0.3 });
render('wide_fire2', W, { fire: 2 });
render('wide_door05', W, { doorOpen: 0.5 });
render('wide_door1', W, { doorOpen: 1 });
render('wide_corner1', W, { cornerLight: 1 });
render('wide_nochairs', W, { chairs: { c700: false, c960: false, c1100: false }, bellowsHidden: true }, { figs: false });
render('wide_empty', W, {}, { figs: false });
render('extreme_wide', { x: 800, y: 950, zoom: 0.62 }, {}, { figs: false });
render('med_table', { x: 830, y: 1250, zoom: 1.6 }, {});
render('med_window', { x: 560, y: 1000, zoom: 1.6 }, {});
render('med_hearth', { x: 1450, y: 1150, zoom: 1.6 }, {});
render('med_hearth_fire2', { x: 1450, y: 1150, zoom: 1.6 }, { fire: 2 });
render('med_hearth_fire03', { x: 1450, y: 1150, zoom: 1.6 }, { fire: 0.3 });
render('med_corner', { x: 200, y: 1350, zoom: 1.6 }, {});
render('med_corner_lit', { x: 200, y: 1350, zoom: 1.6 }, { cornerLight: 1 });
render('med_door0', { x: 230, y: 1250, zoom: 1.6 }, {}, { figs: false });
render('med_door03', { x: 230, y: 1250, zoom: 1.6 }, { doorOpen: 0.3 }, { figs: false });
render('med_door05', { x: 230, y: 1250, zoom: 1.6 }, { doorOpen: 0.5 }, { figs: false });
render('med_door1', { x: 230, y: 1250, zoom: 1.6 }, { doorOpen: 1 }, { figs: false });
render('close_fire', { x: 1525, y: 1300, zoom: 3 }, {}, { figs: false });
render('close_fire2', { x: 1525, y: 1250, zoom: 3 }, { fire: 2 }, { figs: false });
render('close_fire03', { x: 1525, y: 1300, zoom: 3 }, { fire: 0.3 }, { figs: false });
render('close_mantel', { x: 1500, y: 900, zoom: 3 }, {}, { figs: false });
render('close_bellows', { x: 1340, y: 1250, zoom: 3 }, {}, { figs: false });
render('close_window', { x: 650, y: 700, zoom: 3 }, {}, { figs: false });
render('close_window_night', { x: 650, y: 700, zoom: 3 }, { view: 'night' }, { figs: false });
render('close_shelves', { x: 1110, y: 640, zoom: 3 }, {}, { figs: false });
render('close_tea', { x: 120, y: 1640, zoom: 3 }, {}, { figs: false });
render('close_door', { x: 200, y: 1200, zoom: 3 }, { doorOpen: 0.6 }, { figs: false });
render('close_wall', { x: -200, y: 700, zoom: 3 }, {}, { figs: false });
render('close_ceiling', { x: 800, y: 0, zoom: 1.6 }, {}, { figs: false });
render('close_floor_front', { x: 800, y: 2100, zoom: 1.6 }, {}, { figs: false });
render('close_angerSeat', { x: 700, y: 1100, zoom: 3 }, {});
render('close_sad', { x: 200, y: 1450, zoom: 3 }, {});
render('viewfn', { x: 650, y: 700, zoom: 1.6 }, { viewFn: (c, x, y, r) => { c.fillStyle = '#88aa88'; c.fillRect(x - r, y - r, 2 * r, 2 * r); } }, { figs: false });
// visions
const VZ = { x: 1525, y: 650, zoom: 1.5 };
render('vis_words', VZ, {}, { t: 20, figs: false, vision: { kind: 'words', alpha: 1, items: [{ text: 'Name-calling.', t0: 15 }, { text: 'Labeling without consent.', t0: 16 }, { text: 'Dismissiveness.', t0: 18 }, { text: 'Invalidation.', t0: 19.6 }] } });
render('vis_words_fade', VZ, {}, { t: 20, figs: false, vision: { kind: 'words', alpha: 0.4, items: [{ text: 'Name-calling.', t0: 15 }, { text: 'Labeling without consent.', t0: 16 }] } });
for (const p of [0, 0.25, 0.5, 0.75, 1]) render(`vis_tiger_${p}`, VZ, {}, { figs: false, vision: { kind: 'tiger', p, alpha: 1 } });
for (const p of [0, 0.5, 1]) render(`vis_coaster_${p}`, VZ, {}, { figs: false, vision: { kind: 'coaster', p, alpha: 1 } });
for (const p of [0.15, 0.4, 0.9]) render(`vis_water_${p}`, { x: 1525, y: 650, zoom: 1.5 }, {}, { figs: false, vision: { kind: 'water', p, alpha: 1 } });
render('vis_tiger_wide', W, {}, { vision: { kind: 'tiger', p: 0.5, alpha: 1 } });

// full-res timing over a few frames (wide + close)
if (!filt) {
  for (const [nm, cam, o] of [['wide', W, {}], ['wide_door_fire2', W, { doorOpen: 0.7, fire: 2, cornerLight: 0.5 }], ['wide_fire03', W, { fire: 0.3 }], ['medium', { x: 830, y: 1250, zoom: 1.6 }, {}], ['close_fire', { x: 1525, y: 1300, zoom: 3 }, {}], ['close_fire2', { x: 1525, y: 1250, zoom: 3 }, { fire: 2 }], ['close_corner', { x: 150, y: 1500, zoom: 3 }, { cornerLight: 0.6 }]]) {
    let mx = 0, sum = 0;
    for (let i = 0; i < 24; i++) {
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.translate(540, 960); ctx.scale(cam.zoom, cam.zoom); ctx.translate(-cam.x, -cam.y);
      const a = process.hrtime.bigint(); H.drawBack(ctx, i / 24, o); H.drawFront(ctx, i / 24, o); ctx.getImageData(0, 0, 1, 1); /* flush deferred raster */ const d = Number(process.hrtime.bigint() - a) / 1e6;
      mx = Math.max(mx, d); sum += d;
    }
    console.log(`TIMING ${nm}: mean ${(sum / 24).toFixed(1)}ms max ${mx.toFixed(1)}ms (back+front, 1080x1920)`);
  }
  // determinism check
  const snap = () => { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.translate(540, 960); ctx.scale(0.72, 0.72); ctx.translate(-800, -1000); H.drawBack(ctx, 3.3, { fire: 1.4 }); H.drawFront(ctx, 3.3, {}); H.drawVision(ctx, 3.3, { kind: 'tiger', p: 0.4, alpha: 0.8 }); return full.toBuffer('image/png'); };
  console.log('deterministic:', Buffer.compare(snap(), snap()) === 0);
}
