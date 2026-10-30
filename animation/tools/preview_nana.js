// Preview renderer for background painter C (src/bg/nana.js: kitchen, memory, hospital).
// usage: node tools/preview_nana.js [kitchen|memory|hospital|all]
'use strict';
const path = require('path');
const fs = require('fs');
const { createCanvas } = require('@napi-rs/canvas');
const N = require('../src/bg/nana.js');
const OUT = path.join(__dirname, '..', 'build', 'preview');
fs.mkdirSync(OUT, { recursive: true });

function frame(mod, cam, t, o, sil = [], outW = 540) {
  const outH = Math.round(outW * 1920 / 1080);
  const cv = createCanvas(outW, outH), ctx = cv.getContext('2d');
  ctx.fillStyle = '#ff00ff'; ctx.fillRect(0, 0, outW, outH);
  ctx.scale(outW / 1080, outW / 1080); ctx.translate(540, 960); ctx.scale(cam.z, cam.z); ctx.translate(-cam.x, -cam.y);
  mod.drawBack(ctx, t, o);
  for (const s of sil) silhouette(ctx, s, mod.lightAt(s.x, s.y - 300, t, o));
  mod.drawFront(ctx, t, o);
  return cv;
}
function silhouette(ctx, s, L) {
  const H = s.h || 950, x = s.x, y = s.y, k = H / 950, top = y - H;
  ctx.save(); ctx.globalAlpha = 0.35; ctx.fillStyle = '#2b3550';
  ctx.beginPath(); ctx.ellipse(x, top + 75 * k, 58 * k, 75 * k, 0, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.moveTo(x - 115 * k, top + 190 * k); ctx.quadraticCurveTo(x, top + 155 * k, x + 115 * k, top + 190 * k); ctx.lineTo(x + 100 * k, top + 520 * k); ctx.lineTo(x - 100 * k, top + 520 * k); ctx.closePath(); ctx.fill();
  ctx.fillRect(x - 90 * k, top + 520 * k, 75 * k, 430 * k); ctx.fillRect(x + 15 * k, top + 520 * k, 75 * k, 430 * k);
  ctx.globalAlpha = 0.9; ctx.strokeStyle = L.keyColor; ctx.lineWidth = 6;
  const cy = y - 600 * k;
  ctx.beginPath(); ctx.moveTo(x, cy); ctx.lineTo(x + Math.cos(L.keyDir) * 140, cy + Math.sin(L.keyDir) * 140); ctx.stroke();
  ctx.strokeStyle = L.rimColor; ctx.setLineDash([10, 8]);
  ctx.beginPath(); ctx.moveTo(x, cy); ctx.lineTo(x + Math.cos(L.rimDir) * 110, cy + Math.sin(L.rimDir) * 110); ctx.stroke();
  ctx.restore();
}
function save(cv, name) { fs.writeFileSync(path.join(OUT, `nana_${name}.png`), cv.toBuffer('image/png')); }
function timeIt(mod, cam, oFn) {
  const cv = createCanvas(1080, 1920), ctx = cv.getContext('2d');
  const run = (t) => { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.translate(540, 960); ctx.scale(cam.z, cam.z); ctx.translate(-cam.x, -cam.y);
    const o = oFn(t); mod.drawBack(ctx, t, o); mod.drawFront(ctx, t, o); ctx.getImageData(0, 0, 1, 1); };
  let t0 = process.hrtime.bigint(); run(0); const first = Number(process.hrtime.bigint() - t0) / 1e6;
  const n = 24; t0 = process.hrtime.bigint();
  for (let i = 0; i < n; i++) run(1 + i / 24);
  return { first: first.toFixed(0), avg: (Number(process.hrtime.bigint() - t0) / 1e6 / n).toFixed(1) };
}

function kitchen() {
  const M = N.kitchen, A = M.ENV.anchors;
  const sil = [{ ...A.eliCounter }, { ...A.mayaBeside }];
  save(frame(M, { x: 600, y: 1000, z: 0.8 }, 2, {}), 'k_wide');
  save(frame(M, { x: 600, y: 1000, z: 0.8 }, 2, {}, sil), 'k_wide_sil');
  save(frame(M, { x: 870, y: 1110, z: 1.25 }, 2, { tinOpen: 0 }), 'k_med125');
  save(frame(M, { x: 900, y: 1060, z: 1.5 }, 2, { tinOpen: 1 }, sil), 'k_med15_sil');
  save(frame(M, { x: 1065, y: 1000, z: 2.4 }, 2, { tinOpen: 1 }), 'k_eli24');
  save(frame(M, { x: 950, y: 1020, z: 1.95 }, 2, { tinOpen: 1 }), 'k_two195');
  for (const p of [0, 0.3, 0.6, 1]) save(frame(M, { x: 1040, y: 1060, z: 4 }, 2, { tinOpen: p }), `k_tin${p}`);
  save(frame(M, { x: 300, y: 1300, z: 1.5 }, 4, {}), 'k_boxes');
  console.log('kitchen timing', timeIt(M, { x: 900, y: 1060, z: 1.5 }, (t) => ({ tinOpen: (t % 2) / 2 })), timeIt(M, { x: 600, y: 1000, z: 0.8 }, () => ({})));
}
function memory() {
  const M = N.memory, A = M.ENV.anchors;
  const sil = [{ ...A.nanaAtTable, h: 1000 }, { x: A.kidStool.x, y: A.kidStool.y, h: 600 }];
  save(frame(M, { x: 600, y: 1000, z: 0.8 }, 2, {}), 'm_wide');
  save(frame(M, { x: 600, y: 1150, z: 1.25 }, 2, {}), 'm_125');
  save(frame(M, { x: 610, y: 1130, z: 1.45 }, 2, {}, sil), 'm_145_sil');
  save(frame(M, { x: 600, y: 1100, z: 1.7 }, 2, {}), 'm_17');
  console.log('memory timing', timeIt(M, { x: 600, y: 1150, z: 1.25 }, () => ({})), timeIt(M, { x: 600, y: 1000, z: 0.8 }, () => ({})));
}
function hospital() {
  const M = N.hospital;
  save(frame(M, { x: 550, y: 1050, z: 0.8 }, 2, {}), 'h_wide');
  save(frame(M, { x: 640, y: 1230, z: 2.1 }, 2, { chairEmpty: true }), 'h_hands');
  save(frame(M, { x: 1100, y: 1300, z: 1.25 }, 2, { candle: false }), 'h_chair_off');
  save(frame(M, { x: 1100, y: 1300, z: 1.25 }, 2, { candle: true }), 'h_chair_on');
  save(frame(M, { x: 1080, y: 1280, z: 1.5 }, 3.3, { candle: true }), 'h_chair15_on');
  save(frame(M, { x: -110, y: 520, z: 3 }, 2.2, {}), 'h_monitor');
  console.log('hospital timing', timeIt(M, { x: 1080, y: 1280, z: 1.5 }, () => ({ candle: true })), timeIt(M, { x: 550, y: 1050, z: 0.8 }, () => ({ candle: true })));
}
const which = process.argv[2] || 'all';
if (which === 'all' || which === 'kitchen') kitchen();
if (which === 'all' || which === 'memory') memory();
if (which === 'all' || which === 'hospital') hospital();
