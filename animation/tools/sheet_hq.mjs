// Contact sheet for the MIND HQ set (src/sets/hq.mjs).
//   node tools/sheet_hq.mjs                 -> out/sheet_hq.png (+ timing report)
//   node tools/sheet_hq.mjs --full          -> also out/hq_<cell>.png at 720x1280 for close inspection
//   node tools/sheet_hq.mjs --clean         -> no anchor labels / placeholders (pure set)
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { W, H, applyCamera, TAU, rgba, vignette } from '../src/engine.mjs';
import { drawHQ, drawHQForeground, drawAlarmLight, drawConsole, drawAlarmStation, drawScreenContent, HQ_VIEWS } from '../src/sets/hq.mjs';
import { drawFear } from '../src/chars/fear.mjs';
import { EXPR } from '../src/face.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
for (const [f, n] of [['Caveat.ttf', 'Caveat'], ['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand']]) {
  GlobalFonts.registerFromPath(path.join(ROOT, 'assets/fonts', f), n);
}
const args = process.argv.slice(2);
const FULL = args.includes('--full');
const CLEAN = args.includes('--clean');

// ---------------------------------------------------------------- placeholders
function phVoid(g, x, y, s, opt = {}) {
  const h = 1700 * s, w = 640 * s;
  g.save();
  g.translate(x, y);
  // cloak
  g.beginPath();
  g.moveTo(-w * 0.55, 0);
  g.bezierCurveTo(-w * 0.5, -h * 0.4, -w * 0.42, -h * 0.7, -w * 0.3, -h * 0.82);
  g.bezierCurveTo(-w * 0.28, -h * 0.97, w * 0.28, -h * 0.97, w * 0.3, -h * 0.82);
  g.bezierCurveTo(w * 0.42, -h * 0.7, w * 0.5, -h * 0.4, w * 0.55, 0);
  g.quadraticCurveTo(0, h * 0.02, -w * 0.55, 0);
  g.closePath();
  g.fillStyle = '#0a0914'; g.fill();
  g.strokeStyle = rgba('#8a6cff', 0.6); g.lineWidth = 4 * s + 1; g.stroke();
  // hood opening
  g.fillStyle = '#000000';
  g.beginPath(); g.ellipse(0, -h * 0.84, w * 0.16, h * 0.07, 0, 0, TAU); g.fill();
  g.strokeStyle = rgba('#5ad1ff', 0.25); g.lineWidth = 2; g.stroke();
  g.restore();
}
function phEmotion(g, x, y, s, col, back = false, hgt = 460) {
  const h = hgt * s, w = 190 * s;
  g.save();
  g.translate(x, y);
  g.fillStyle = 'rgba(0,0,0,0.3)'; g.beginPath(); g.ellipse(0, 0, w * 0.6, w * 0.12, 0, 0, TAU); g.fill();
  g.fillStyle = col; g.strokeStyle = '#2a1f40'; g.lineWidth = 3 * s;
  g.beginPath(); g.roundRect(-w * 0.35, -h * 0.55, w * 0.7, h * 0.55, w * 0.3); g.fill(); g.stroke();
  g.beginPath(); g.ellipse(0, -h * 0.74, w * 0.42, h * 0.2, 0, 0, TAU); g.fill(); g.stroke();
  if (!back) {
    g.fillStyle = '#fff';
    for (const sd of [-1, 1]) { g.beginPath(); g.ellipse(sd * w * 0.15, -h * 0.76, w * 0.09, w * 0.11, 0, 0, TAU); g.fill(); }
    g.fillStyle = '#20163a';
    for (const sd of [-1, 1]) { g.beginPath(); g.arc(sd * w * 0.15, -h * 0.75, w * 0.05, 0, TAU); g.fill(); }
    g.strokeStyle = '#2a1f40'; g.lineWidth = 3 * s; g.beginPath(); g.arc(0, -h * 0.68, w * 0.1, 0.3, Math.PI - 0.3); g.stroke();
  }
  g.restore();
}
function phCEO(g, x, y, s, back = false) {
  const h = 600 * s;
  g.save(); g.translate(x, y);
  g.fillStyle = 'rgba(0,0,0,0.3)'; g.beginPath(); g.ellipse(0, 0, 70 * s, 12 * s, 0, 0, TAU); g.fill();
  g.strokeStyle = '#1c1a26'; g.lineWidth = 3 * s;
  g.fillStyle = '#2b2e3a'; g.beginPath(); g.roundRect(-40 * s, -h * 0.45, 80 * s, h * 0.45, 12 * s); g.fill(); g.stroke();
  g.fillStyle = '#3a3d4a'; g.beginPath(); g.roundRect(-62 * s, -h * 0.8, 124 * s, h * 0.38, 30 * s); g.fill(); g.stroke();
  g.fillStyle = '#4f8c8a'; g.beginPath(); g.moveTo(-18 * s, -h * 0.8); g.lineTo(18 * s, -h * 0.8); g.lineTo(0, -h * 0.6); g.fill();
  g.fillStyle = back ? '#2f2433' : '#d9a27e'; g.beginPath(); g.ellipse(0, -h * 0.89, 46 * s, 54 * s, 0, 0, TAU); g.fill(); g.stroke();
  g.fillStyle = '#2f2433'; g.beginPath(); g.ellipse(0, -h * 0.94, 50 * s, 30 * s, 0, Math.PI, 0); g.fill();
  g.restore();
}
function phCage(g, x, y, s, open = 0) {
  const h = 400 * s, w = 250 * s;
  g.save(); g.translate(x, y);
  g.strokeStyle = '#8a7a6a'; g.lineWidth = 4 * s;
  g.beginPath(); g.ellipse(0, 0, w / 2, w * 0.12, 0, 0, TAU); g.stroke();
  for (let i = 0; i <= 8; i++) {
    const u = -1 + (2 * i) / 8, xx = u * w / 2;
    g.beginPath(); g.moveTo(xx, 0); g.lineTo(xx, -h * 0.72); g.quadraticCurveTo(xx * 0.6, -h * 0.98, 0, -h); g.stroke();
  }
  g.beginPath(); g.ellipse(0, -h * 0.72, w / 2, w * 0.1, 0, 0, TAU); g.stroke();
  g.fillStyle = '#d9c9a8'; g.fillRect(-36 * s, -h * 0.55, 72 * s, 26 * s);
  g.restore();
}
function label(g, x, y, text, col = '#ffe08a') {
  if (CLEAN) return;
  g.save();
  const m = g.getTransform();
  const z = Math.hypot(m.a, m.b);
  g.translate(x, y);
  g.scale(1 / z, 1 / z);
  g.fillStyle = col; g.beginPath(); g.arc(0, 0, 5, 0, TAU); g.fill();
  g.strokeStyle = '#000'; g.lineWidth = 1.5; g.stroke();
  g.font = 'bold 15px Fraunces';
  g.lineWidth = 4; g.strokeStyle = 'rgba(0,0,0,0.85)';
  g.strokeText(text, 8, -6); g.fillStyle = col; g.fillText(text, 8, -6);
  g.restore();
}
const EMO = ['#ffc94a', '#6fa8e8', '#f0634f', '#7fd6b0'];
const EMO_H = [430, 470, 400, 520];

function stage(g, view, st, cam, cast) {
  g.save();
  applyCamera(g, cam);
  drawHQ(g, view, st);
  if (!CLEAN) cast(g);
  drawHQForeground(g, view, st);
  drawAlarmLight(g, view, st);
  const A = HQ_VIEWS[view].anchors;
  for (const k in A) label(g, A[k][0], A[k][1], `${k} ${A[k][2] || ''}`);
  g.restore();
}

const fear = (g, a, extra = {}) => drawFear(g, a[0], a[1], a[2], { t: 1.3, face: EXPR.worried, ...extra });

const castFront = (fearPose = {}) => (g) => {
  const A = HQ_VIEWS.front.anchors;
  phVoid(g, ...A.voidSpot);
  phCage(g, ...A.cageSpot);
  phCEO(g, ...A.ceoSpot);
  fear(g, A.fearSpot, { face: EXPR.scared, armR: 'reachUp', ...fearPose });
  for (let i = 0; i < 4; i++) phEmotion(g, ...A[`consoleSlot${i + 1}`], EMO[i], false, EMO_H[i]);
};
const castBack = (g) => {
  const A = HQ_VIEWS.back.anchors;
  for (let i = 0; i < 4; i++) phEmotion(g, ...A[`consoleBack${i + 1}`], EMO[i], true, EMO_H[i]);
  phCage(g, ...A.cageSpot);
  phCEO(g, ...A.ceoSpot, true);
  fear(g, A.fearSpot, { face: EXPR.sad });
  phVoid(g, ...A.voidEdge);
};
const castAlarm = (pulled) => (g) => {
  const A = HQ_VIEWS.alarm.anchors;
  phCEO(g, ...A.ceoBeside);
  const [hx, hy] = [A.handle[0], A.handle[1] + pulled * 26 * A.handle[2]];
  const [fx, fy, fs] = A.fearAtAlarm;
  fear(g, A.fearAtAlarm, { face: { ...EXPR.terrified, lookX: 0.7, lookY: -0.3 }, tremble: 0.6, lean: 0.06, armR: { target: [(hx - fx) / fs, (hy - fy) / fs], bend: 1, hand: 'grip', front: true } });
};
const castBOM = (g) => {
  const A = HQ_VIEWS.backOfMind.anchors;
  phVoid(g, ...A.void);
  phCage(g, ...A.cage);
  fear(g, A.fearInCage, { face: EXPR.crying });
  fear(g, A.fearOutside, { face: { ...EXPR.scared, lookX: 0.6, lookY: -0.8 }, headTilt: -0.15 });
  phCEO(g, ...A.ceo);
};

const T = 2.15;
const cells = [
  ['front · wide (calm)', 'front', { t: T }, HQ_VIEWS.front.cams.wide, castFront()],
  ['front · alarm=1, pulled', 'front', { t: T, alarm: 1, alarmPulled: 1 }, HQ_VIEWS.front.cams.wide, castFront()],
  ['front · voidShadow=1 mist=.8', 'front', { t: T, voidShadow: 1, mist: 0.8, lightsDim: 0.25 }, HQ_VIEWS.front.cams.wide, castFront()],
  ['front · zoom 1 (thumbnail)', 'front', { t: T, doorOpen: 0 }, HQ_VIEWS.front.cams.establish, castFront()],
  ['back · screen room', 'back', { t: T, screenMode: 'room' }, HQ_VIEWS.back.cams.wide, castBack],
  ['back · calm + press', 'back', { t: T, screenMode: 'calm', consolePress: { 0: 1, 9: 1 } }, HQ_VIEWS.back.cams.wide, castBack],
  ['back · alarm + voidShadow', 'back', { t: T, screenMode: 'alarm', alarm: 1, voidShadow: 1 }, HQ_VIEWS.back.cams.wide, castBack],
  ['alarm · quiet', 'alarm', { t: T }, HQ_VIEWS.alarm.cams.wide, castAlarm(0)],
  ['alarm · ringing, pulled', 'alarm', { t: T, alarm: 1, alarmPulled: 1 }, HQ_VIEWS.alarm.cams.medium, castAlarm(1)],
  ['backOfMind · wide', 'backOfMind', { t: T, mist: 0.5 }, HQ_VIEWS.backOfMind.cams.wide, castBOM],
  ['backOfMind · voidShadow=1', 'backOfMind', { t: T, voidShadow: 1, mist: 0.7 }, HQ_VIEWS.backOfMind.cams.ground, castBOM],
  ['front · door open, dim', 'front', { t: T, doorOpen: 1, lightsDim: 0.6, consoleGlow: 1.2 }, HQ_VIEWS.front.cams.door, castFront()],
];

const TW = 360, TH = 640, cols = 4, rows = Math.ceil(cells.length / cols);
const sheet = createCanvas(TW * cols, (TH + 30) * rows);
const gs = sheet.getContext('2d');
gs.fillStyle = '#111'; gs.fillRect(0, 0, sheet.width, sheet.height);
const frame = createCanvas(W, H);
const gf = frame.getContext('2d');
cells.forEach(([name, view, st, cam, cast], i) => {
  gf.setTransform(1, 0, 0, 1, 0, 0);
  gf.fillStyle = '#000'; gf.fillRect(0, 0, W, H);
  stage(gf, view, st, cam, cast);
  vignette(gf, 0.3);
  const x = (i % cols) * TW, y = Math.floor(i / cols) * (TH + 30);
  gs.drawImage(frame, x, y + 30, TW, TH);
  gs.fillStyle = '#fff'; gs.font = '17px Fraunces'; gs.fillText(name, x + 6, y + 21);
  if (FULL) fs.writeFileSync(path.join(ROOT, `out/hq_${i}.png`), frame.toBuffer('image/png'));
});
fs.writeFileSync(path.join(ROOT, 'out/sheet_hq.png'), sheet.toBuffer('image/png'));

// ---------------------------------------------------------------- timing
const tg = gf;
function time(label, fn, n = 50) {
  fn(0); // warm caches
  tg.getImageData(0, 0, 1, 1);
  const t0 = performance.now();
  for (let i = 0; i < n; i++) { fn(i); }
  tg.getImageData(0, 0, 1, 1);
  const ms = (performance.now() - t0) / n;
  console.log(`${label.padEnd(44)} ${ms.toFixed(2)} ms`);
}
for (const view of ['front', 'back', 'alarm', 'backOfMind']) {
  for (const camName of Object.keys(HQ_VIEWS[view].cams).slice(0, 3)) {
    const cam = HQ_VIEWS[view].cams[camName];
    time(`drawHQ ${view} cam=${camName} z=${cam.zoom}`, (i) => {
      tg.setTransform(1, 0, 0, 1, 0, 0);
      tg.save(); applyCamera(tg, cam);
      drawHQ(tg, view, { t: i / 24, alarm: 1, voidShadow: 0.7, mist: 0.6, consolePress: { 2: 0.5 }, screenMode: 'calm' });
      drawHQForeground(tg, view, { t: i / 24, mist: 0.6 });
      drawAlarmLight(tg, view, { t: i / 24, alarm: 1 });
      tg.restore();
    });
  }
}
time('drawConsole controls w=700 s=1', (i) => { tg.setTransform(1, 0, 0, 1, 0, 0); drawConsole(tg, 360, 900, 700, 1, { t: i / 24, consolePress: { 1: 1 } }); });
time('drawAlarmStation s=1.8 alarm', (i) => { tg.setTransform(1, 0, 0, 1, 0, 0); drawAlarmStation(tg, 360, 900, 1.8, { t: i / 24, alarm: 1, alarmPulled: 0.5 }); });
time('drawScreenContent 640x500 calm', (i) => { tg.setTransform(1, 0, 0, 1, 0, 0); drawScreenContent(tg, 40, 100, 640, 500, i / 24, 'calm'); });
time('drawAlarmLight front', (i) => { tg.setTransform(1, 0, 0, 1, 0, 0); drawAlarmLight(tg, 'front', { t: i / 24, alarm: 1 }); });
