// Preview renderer for background painter A (kitchen + porch).
// usage: node tools/preview_bg_a.js [kitchen|porch|all]
'use strict';
const path = require('path');
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const OUT = path.join(__dirname, '..', 'build', 'preview');
fs.mkdirSync(OUT, { recursive: true });

function frame(mod, cam, t, o, outW = 540, sil = []) {
  const outH = Math.round(outW * 1920 / 1080);
  const cv = createCanvas(outW, outH), ctx = cv.getContext('2d');
  ctx.fillStyle = '#ff00ff'; ctx.fillRect(0, 0, outW, outH); // magenta shows any uncovered area
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(outW / 1080, outW / 1080); ctx.translate(540, 960); ctx.scale(cam.zoom, cam.zoom); ctx.translate(-cam.x, -cam.y);
  mod.drawBack(ctx, t, o);
  for (const s of sil) silhouette(ctx, s, mod.lightAt(s.x, s.y, t, o));
  mod.drawFront(ctx, t, o);
  return cv;
}
// faint placeholder people: standing (feet at x,y) or seated (hip at x,y), 950 tall, head 150
function silhouette(ctx, s, L) {
  ctx.save(); ctx.globalAlpha = 0.38; ctx.fillStyle = '#2b3550';
  const x = s.x, y = s.y;
  if (s.seated) {
    const top = y - 520; // crown
    ctx.beginPath(); ctx.ellipse(x, top + 75, 58, 75, 0, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x - 110, top + 185); ctx.quadraticCurveTo(x, top + 150, x + 110, top + 185); ctx.lineTo(x + 95, y); ctx.lineTo(x - 95, y); ctx.closePath(); ctx.fill();
    ctx.fillRect(x - 95, y, 190, 40); // thighs forward
    ctx.fillRect(x - 85, y + 40, 50, 420); ctx.fillRect(x + 35, y + 40, 50, 420); // shins under the table
  } else {
    const top = y - 950;
    ctx.beginPath(); ctx.ellipse(x, top + 75, 58, 75, 0, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x - 115, top + 190); ctx.quadraticCurveTo(x, top + 155, x + 115, top + 190); ctx.lineTo(x + 100, top + 520); ctx.lineTo(x - 100, top + 520); ctx.closePath(); ctx.fill();
    ctx.fillRect(x - 90, top + 520, 75, 430); ctx.fillRect(x + 15, top + 520, 75, 430);
  }
  // key light direction marker
  ctx.globalAlpha = 0.9; ctx.strokeStyle = L.keyColor; ctx.lineWidth = 6;
  const cy = s.seated ? y - 330 : y - 600;
  ctx.beginPath(); ctx.moveTo(x, cy); ctx.lineTo(x + Math.cos(L.keyDir) * 140, cy + Math.sin(L.keyDir) * 140); ctx.stroke();
  ctx.strokeStyle = L.rimColor; ctx.setLineDash([10, 8]);
  ctx.beginPath(); ctx.moveTo(x, cy); ctx.lineTo(x + Math.cos(L.rimDir) * 110, cy + Math.sin(L.rimDir) * 110); ctx.stroke();
  ctx.restore();
}
function save(cv, name) { fs.writeFileSync(path.join(OUT, name + '.png'), cv.toBuffer('image/png')); }
function timeIt(mod, cam, o, anim) {
  const cv = createCanvas(1080, 1920), ctx = cv.getContext('2d');
  const run = (t) => { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.translate(540, 960); ctx.scale(cam.zoom, cam.zoom); ctx.translate(-cam.x, -cam.y);
    mod.drawBack(ctx, t, o); mod.drawFront(ctx, t, o); ctx.getImageData(0, 0, 1, 1); };
  let t0 = process.hrtime.bigint(); run(0); const first = Number(process.hrtime.bigint() - t0) / 1e6;
  const N = 12; t0 = process.hrtime.bigint();
  for (let i = 0; i < N; i++) { if (anim) Object.assign(o, anim(i)); run(1 + i / 24); }
  return { first, avg: Number(process.hrtime.bigint() - t0) / 1e6 / N };
}

function kitchen() {
  const K = require('../src/bg/kitchen.js');
  const A = K.ENV.anchors;
  const sil = [{ ...A.mayaSeat, seated: true }, { ...A.eliLean }];
  const sil2 = [{ ...A.mayaSeat, seated: true }, { ...A.eliSeat, seated: true }];
  const T = timeIt(K, { x: 800, y: 950, zoom: 0.75 }, {});
  const T2 = timeIt(K, { x: 430, y: 1000, zoom: 3 }, {});
  const T3 = timeIt(K, { x: 800, y: 1100, zoom: 1.6 }, { lamp: 0.5, dusk: 0.6 });
  console.log('kitchen timing ms: wide', T, 'close', T2, 'medium lamp.5', T3);
  const shots = [
    ['k_wide', { x: 800, y: 950, zoom: 0.75 }, {}, []],
    ['k_wide_sil', { x: 800, y: 950, zoom: 0.75 }, {}, sil],
    ['k_wide_sil_eliseat', { x: 760, y: 950, zoom: 0.8 }, {}, sil2],
    ['k_med_maya', { x: 430, y: 1050, zoom: 1.6 }, {}, sil],
    ['k_med_eli', { x: 1250, y: 1000, zoom: 1.6 }, {}, sil],
    ['k_med_two', { x: 840, y: 1050, zoom: 1.6 }, {}, sil],
    ['k_close_maya', { x: 430, y: 1000, zoom: 3 }, {}, []],
    ['k_close_mug', { x: 470, y: 1330, zoom: 3 }, {}, []],
    ['k_close_eli', { x: 1250, y: 800, zoom: 3 }, {}, []],
    ['k_close_clock', { x: 700, y: 320, zoom: 3 }, {}, []],
    ['k_close_kettle', { x: 1450, y: 1050, zoom: 3 }, {}, []],
    ['k_close_window', { x: 330, y: 760, zoom: 3 }, {}, []],
    ['k_close_left', { x: -120, y: 800, zoom: 3 }, {}, []],
    ['k_close_floor', { x: 1300, y: 1950, zoom: 3 }, {}, []],
  ];
  for (const d of [0, 0.5, 1]) shots.push(['k_dusk' + d, { x: 800, y: 950, zoom: 0.75 }, { dusk: d }, []]);
  for (const l of [0, 0.5]) shots.push(['k_lamp' + l, { x: 800, y: 950, zoom: 0.75 }, { lamp: l, dusk: 0.5 }, []]);
  shots.push(['k_med_window_dusk1', { x: 400, y: 900, zoom: 1.6 }, { dusk: 1 }, []]);
  shots.push(['k_med_window_dusk0', { x: 400, y: 900, zoom: 1.6 }, { dusk: 0 }, []]);
  // extents corners
  shots.push(['k_corner_tl', { x: -300 + 720, y: -400 + 1280, zoom: 0.75 }, {}, []]);
  shots.push(['k_corner_br', { x: 1900 - 720, y: 2300 - 1280, zoom: 0.75 }, {}, []]);
  for (const [n, cam, o, s] of shots) save(frame(K, cam, 3.3, o, 540, s), n);
}
function porch() {
  const P = require('../src/bg/porch.js');
  const A = P.ENV.anchors;
  const sil = [{ ...A.mayaAtDoor }, { ...A.eliAtDoor }];
  const T = timeIt(P, { x: 700, y: 1100, zoom: 0.75 }, { doorOpen: 0.6 });
  const T2 = timeIt(P, { x: 735, y: 1100, zoom: 3 }, { doorOpen: 0.6 });
  const T3 = timeIt(P, { x: 700, y: 1100, zoom: 0.75 }, {}, (i) => ({ doorOpen: i / 11 }));
  const T4 = timeIt(P, { x: 600, y: 1100, zoom: 3 }, {}, (i) => ({ doorOpen: i / 11 }));
  const T5 = timeIt(P, { x: 600, y: 1100, zoom: 1.6 }, {}, (i) => ({ doorOpen: i / 11 }));
  console.log('porch timing ms: wide', T, 'close', T2, 'animated door wide', T3, 'close', T4, 'medium', T5);
  const shots = [
    ['p_wide', { x: 600, y: 1000, zoom: 0.75 }, {}, []],
    ['p_wide_sil', { x: 600, y: 1000, zoom: 0.75 }, {}, sil],
    ['p_med_door', { x: 750, y: 1150, zoom: 1.6 }, {}, sil],
    ['p_med_window', { x: 1100, y: 1100, zoom: 1.6 }, {}, []],
    ['p_med_steps', { x: 1100, y: 1790, zoom: 1.6 }, {}, [{ x: 1100, y: 2300 }]],
    ['p_close_knob', { x: 735, y: 1120, zoom: 3 }, {}, []],
    ['p_close_brick', { x: 150, y: 1250, zoom: 3 }, {}, []],
    ['p_close_lantern', { x: 600, y: -75, zoom: 3 }, {}, []],
    ['p_close_box', { x: 1125, y: 1200, zoom: 3 }, {}, []],
    ['p_close_mat', { x: 600, y: 1500, zoom: 3 }, { doorOpen: 1 }, []],
    ['p_corner_tl', { x: -400 + 720, y: -400 + 1280, zoom: 0.75 }, {}, []],
    ['p_corner_br', { x: 1600 - 720, y: 2400 - 1280, zoom: 0.75 }, {}, []],
  ];
  for (const d of [0, 0.15, 0.3, 0.5, 0.75, 1]) shots.push(['p_door' + d, { x: 650, y: 1150, zoom: 1.6 }, { doorOpen: d }, sil]);
  shots.push(['p_wide_open', { x: 600, y: 1000, zoom: 0.75 }, { doorOpen: 1 }, sil]);
  shots.push(['p_close_door_half', { x: 560, y: 1150, zoom: 3 }, { doorOpen: 0.5 }, []]);
  for (const [n, cam, o, s] of shots) save(frame(P, cam, 3.3, o, 540, s), n);
}
const which = process.argv[2] || 'all';
if (which === 'kitchen' || which === 'all') kitchen();
if (which === 'porch' || which === 'all') porch();
