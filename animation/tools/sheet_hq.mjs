// Contact sheet for the MIND HQ set (src/sets/hq.mjs).
//   node tools/sheet_hq.mjs                 -> out/sheet_hq.png (+ timing report)
//   node tools/sheet_hq.mjs --full          -> also out/hq_<cell>.png at 720x1280 for close inspection
//   node tools/sheet_hq.mjs --clean         -> no anchor labels / characters (pure set)
//   node tools/sheet_hq.mjs --placeholders  -> silhouettes instead of the real character modules
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { W, H, applyCamera, TAU, rgba, vignette } from '../src/engine.mjs';
import {
  drawHQ, drawHQForeground, drawAlarmLight, drawConsole, drawAlarmStation, drawScreenContent,
  HQ_VIEWS, HQ_PRESETS, HQ_STATIONS, ALARM_REACH, hqScaleAt,
} from '../src/sets/hq.mjs';
import { drawFear } from '../src/chars/fear.mjs';
import { EXPR } from '../src/face.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
for (const [f, n] of [['Caveat.ttf', 'Caveat'], ['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand']]) {
  GlobalFonts.registerFromPath(path.join(ROOT, 'assets/fonts', f), n);
}
const args = process.argv.slice(2);
const PH = args.includes('--placeholders');
const FULL = args.includes('--full');
const CLEAN = args.includes('--clean');
// real character / prop modules when they exist (other agents build them); placeholders otherwise
const real = {};
if (!PH) {
  for (const [k, file, names] of [['void', '../src/chars/void.mjs', ['drawVoid']], ['emo', '../src/chars/emotions.mjs', ['drawEmotion']], ['self', '../src/chars/self.mjs', ['drawSelf', 'selfLocal']], ['cage', '../src/sets/props.mjs', ['drawCage']]]) {
    try {
      const m = await import(file);
      if (names.every((n) => typeof m[n] === 'function')) real[k] = m;
    } catch (e) { console.error(`(placeholder for ${k}: ${e.message.split('\n')[0]})`); }
  }
}

// ---------------------------------------------------------------- characters (real or placeholder)
// other agents edit their modules in parallel: if a real module throws, fall back to the placeholder
const failed = new Set();
function tryReal(k, fn) {
  if (!real[k] || failed.has(k)) return false;
  try { fn(); return true; } catch (e) { failed.add(k); console.error(`(real ${k} threw, using placeholder: ${e.message.split('\n')[0]})`); return false; }
}
function drawVoidAt(g, x, y, s, opt = {}) {
  if (tryReal('void', () => { g.save(); try { real.void.drawVoid(g, x, y, s, { t: 1.3, headTurn: opt.headTurn ?? 0 }); } finally { g.restore(); } })) return;
  const h = 1700 * s, w = 640 * s;
  g.save(); g.translate(x, y);
  g.beginPath();
  g.moveTo(-w * 0.55, 0);
  g.bezierCurveTo(-w * 0.5, -h * 0.4, -w * 0.42, -h * 0.7, -w * 0.3, -h * 0.82);
  g.bezierCurveTo(-w * 0.28, -h * 0.97, w * 0.28, -h * 0.97, w * 0.3, -h * 0.82);
  g.bezierCurveTo(w * 0.42, -h * 0.7, w * 0.5, -h * 0.4, w * 0.55, 0);
  g.quadraticCurveTo(0, h * 0.02, -w * 0.55, 0);
  g.closePath();
  g.fillStyle = '#0a0914'; g.fill();
  g.strokeStyle = rgba('#8a6cff', 0.6); g.lineWidth = 4 * s + 1; g.stroke();
  g.fillStyle = '#000000';
  g.beginPath(); g.ellipse(0, -h * 0.84, w * 0.16, h * 0.07, 0, 0, TAU); g.fill();
  g.restore();
}
const EMO_COL = { JOY: '#ffc94a', SADNESS: '#6fa8e8', ANGER: '#f0634f', CALM: '#7fd6b0' };
const EMO_H = { JOY: 457, SADNESS: 419, ANGER: 394, CALM: 523 };
function drawEmo(g, name, x, y, s, pose = {}) {
  if (tryReal('emo', () => { g.save(); try { real.emo.drawEmotion(g, name, x, y, s, { t: 1.3, ...pose }); } finally { g.restore(); } })) return;
  const back = pose.view === 'back';
  const h = EMO_H[name] * s, w = 190 * s;
  g.save(); g.translate(x, y);
  if (pose.alpha != null) g.globalAlpha = pose.alpha;
  g.fillStyle = 'rgba(0,0,0,0.3)'; g.beginPath(); g.ellipse(0, 0, w * 0.6, w * 0.12, 0, 0, TAU); g.fill();
  g.fillStyle = EMO_COL[name]; g.strokeStyle = '#2a1f40'; g.lineWidth = 3 * s;
  g.beginPath(); g.roundRect(-w * 0.35, -h * 0.55, w * 0.7, h * 0.55, w * 0.3); g.fill(); g.stroke();
  g.beginPath(); g.ellipse(0, -h * 0.74, w * 0.42, h * 0.2, 0, 0, TAU); g.fill(); g.stroke();
  if (!back) {
    g.fillStyle = '#fff';
    for (const sd of [-1, 1]) { g.beginPath(); g.ellipse(sd * w * 0.15, -h * 0.76, w * 0.09, w * 0.11, 0, 0, TAU); g.fill(); }
    g.fillStyle = '#20163a';
    for (const sd of [-1, 1]) { g.beginPath(); g.arc(sd * w * 0.15, -h * 0.75, w * 0.05, 0, TAU); g.fill(); }
  }
  g.restore();
}
function drawCEO(g, x, y, s, pose = {}) {
  if (tryReal('self', () => { g.save(); try { real.self.drawSelf(g, x, y, s, { t: 1.3, outfit: 'ceo', ...pose }); } finally { g.restore(); } })) return;
  const back = pose.view === 'back';
  const h = 600 * s * (pose.kneel ? 0.72 : 1);
  g.save(); g.translate(x, y);
  g.fillStyle = 'rgba(0,0,0,0.3)'; g.beginPath(); g.ellipse(0, 0, 70 * s, 12 * s, 0, 0, TAU); g.fill();
  g.strokeStyle = '#1c1a26'; g.lineWidth = 3 * s;
  g.fillStyle = '#2b2e3a'; g.beginPath(); g.roundRect(-40 * s, -h * 0.45, 80 * s, h * 0.45, 12 * s); g.fill(); g.stroke();
  g.fillStyle = '#3a3d4a'; g.beginPath(); g.roundRect(-62 * s, -h * 0.8, 124 * s, h * 0.38, 30 * s); g.fill(); g.stroke();
  g.fillStyle = back ? '#2f2433' : '#d9a27e'; g.beginPath(); g.ellipse(0, -h * 0.89, 46 * s, 54 * s, 0, 0, TAU); g.fill(); g.stroke();
  g.restore();
}
function drawCageAt(g, x, y, s, layer = 'all', state = {}) {
  if (tryReal('cage', () => { g.save(); try { real.cage.drawCage(g, x, y, s, { t: 1.3, layer, ...state }); } finally { g.restore(); } })) return;
  if (layer === 'back') return;
  const h = 400 * s, w = 250 * s;
  g.save(); g.translate(x, y);
  g.strokeStyle = '#8a7a6a'; g.lineWidth = 4 * s;
  g.beginPath(); g.ellipse(0, 0, w / 2, w * 0.12, 0, 0, TAU); g.stroke();
  for (let i = 0; i <= 8; i++) {
    const xx = (-1 + (2 * i) / 8) * w / 2;
    g.beginPath(); g.moveTo(xx, 0); g.lineTo(xx, -h * 0.72); g.quadraticCurveTo(xx * 0.6, -h * 0.98, 0, -h); g.stroke();
  }
  g.restore();
}
const fear = (g, a, extra = {}) => drawFear(g, a[0], a[1], a[2], { t: 1.3, face: EXPR.worried, ...extra });
// FEAR's arm on the alarm handle (works for front.fearSpot and alarm.fearAtAlarm)
const pullArm = (pulled = 0) => ({ target: [ALARM_REACH[0], ALARM_REACH[1] + 26 * pulled], bend: 1, hand: 'grip', front: true });

// ---------------------------------------------------------------- labels (screen-space, de-overlapped)
let placed = [];
function label(g, x, y, text, col = '#ffe08a') {
  if (CLEAN) return;
  const m = g.getTransform();
  const sx = m.a * x + m.c * y + m.e, sy = m.b * x + m.d * y + m.f;
  if (sx < -20 || sx > W + 20 || sy < -20 || sy > H + 20) return;
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.font = 'bold 15px Fraunces';
  const tw = g.measureText(text).width;
  let ty = sy - 6;
  for (let tries = 0; tries < 6; tries++) {
    const hit = placed.find((b) => sx + 8 < b.x1 && sx + 8 + tw > b.x0 && ty - 13 < b.y1 && ty + 3 > b.y0);
    if (!hit) break;
    ty = hit.y1 + 15;
  }
  placed.push({ x0: sx + 8, x1: sx + 8 + tw, y0: ty - 13, y1: ty + 3 });
  g.fillStyle = col; g.beginPath(); g.arc(sx, sy, 5, 0, TAU); g.fill();
  g.strokeStyle = '#000'; g.lineWidth = 1.5; g.stroke();
  if (Math.abs(ty - (sy - 6)) > 1) { g.strokeStyle = rgba(col, 0.6); g.lineWidth = 1; g.beginPath(); g.moveTo(sx, sy); g.lineTo(sx + 8, ty - 4); g.stroke(); }
  g.lineWidth = 4; g.strokeStyle = 'rgba(0,0,0,0.85)';
  g.strokeText(text, sx + 8, ty); g.fillStyle = col; g.fillText(text, sx + 8, ty);
  g.restore();
}

function stage(g, view, st, cam, cast, noLabels = false) {
  placed = [];
  g.save();
  applyCamera(g, cam);
  drawHQ(g, view, st);
  if (!CLEAN && cast) cast(g, st);
  drawHQForeground(g, view, st);
  drawAlarmLight(g, view, st);
  if (!noLabels) {
    const A = HQ_VIEWS[view].anchors;
    for (const k in A) label(g, A[k][0], A[k][1], `${k}${A[k][2] ? ' ' + A[k][2] : ''}`);
  }
  g.restore();
}

// ---------------------------------------------------------------- casts
const FRONT_ORDER = Object.keys(HQ_STATIONS).map((n) => [n, HQ_STATIONS[n].front]);
const BACK_ORDER = Object.keys(HQ_STATIONS).map((n) => [n, HQ_STATIONS[n].back]);
const castFront = (opt = {}) => (g, st) => {
  const A = HQ_VIEWS.front.anchors;
  drawVoidAt(g, ...A.voidSpot);
  drawCageAt(g, ...A.cageSpot, 'all', opt.cage || {});
  if (opt.ceo !== false) drawCEO(g, ...A.ceoSpot, { face: { lookX: 0.5, lookY: -0.1 }, headTurn: 0.3 });
  if (opt.fear !== false) {
    fear(g, A.fearSpot, { face: { ...EXPR.scared, lookX: 0.6, lookY: -0.5 }, tremble: 0.5, armR: pullArm(st.alarmPulled || 0) });
  }
  const pressing = opt.press || [];
  for (const [name, key] of FRONT_ORDER) {
    if (opt.skipEmo === name) continue;
    const a = opt.spread && opt.spread[name] ? [A[key][0] + opt.spread[name], A[key][1], A[key][2]] : A[key];
    drawEmo(g, name, a[0], a[1], a[2], { view: 'front', armL: 'pressButton', armR: 'pressButton', face: pressing.includes(name) ? EXPR.smile : {} });
  }
  if (opt.consoleFear) fear(g, A.consoleFear, { face: { ...EXPR.softSmile, lookY: 0.3 } });
};
const castBack = (opt = {}) => (g) => {
  const A = HQ_VIEWS.back.anchors;
  BACK_ORDER.forEach(([name, key], i) => drawEmo(g, name, ...A[key], {
    view: 'back', armL: 'pressButton', armR: 'pressButton',
    lookBack: opt.lookBack || 0, lookSide: i < 2 ? -1 : 1, face: opt.lookBack ? { smile: 0.8, lidL: 0.4 } : {},
  }));
  if (opt.ceoMid) drawCEO(g, ...A.consoleBackMid, { view: 'back' });
  if (opt.cage !== false) drawCageAt(g, ...A.cageSpot);
  if (opt.ceo !== false) drawCEO(g, ...A.ceoSpot, { view: 'back' });
  fear(g, A.fearSpot, { face: opt.fearFace || EXPR.sad });
  if (opt.void !== false) drawVoidAt(g, ...A.voidEdge);
};
const castAlarm = (opt = {}) => (g, st) => {
  const A = HQ_VIEWS.alarm.anchors;
  const pulled = st.alarmPulled || 0;
  const [fx, fy, fs] = A.fearAtAlarm;
  if (opt.kneel) {
    // FEAR (farther) first, then CONSCIOUSNESS kneeling in the foreground, right hand on FEAR's near shoulder
    const [cx, cy, cs] = A.ceoKneel;
    fear(g, A.fearAtAlarm, { face: { ...EXPR.crying, lookX: -0.7, lookY: -0.2 }, tremble: 0.7, headTurn: -0.3, armR: pullArm(0) });
    const shoulder = [fx - 36 * fs, fy - 131 * fs];
    const tgt = real.self && !failed.has('self') ? real.self.selfLocal(cx, cy, cs, 1, shoulder[0], shoulder[1]) : null;
    drawCEO(g, cx, cy, cs, { kneel: 1, face: { ...EXPR.tender, lookX: 0.7, lookY: 0.45 }, headTilt: 0.1, armR: tgt ? { preset: 'onShoulder', target: tgt } : undefined });
    return;
  }
  fear(g, A.fearAtAlarm, { face: { ...EXPR.terrified, lookX: 0.7, lookY: -0.3 }, tremble: 0.6, lean: 0.06, armR: pullArm(pulled) });
  drawCEO(g, ...A.ceoBeside, { face: { ...EXPR.worried, lookX: 0.6, lookY: 0.5 } });
};
const castBOM = (opt = {}) => (g) => {
  const A = HQ_VIEWS.backOfMind.anchors;
  drawVoidAt(g, ...A.void, { headTurn: -0.5 });
  drawCageAt(g, ...A.cage, 'back', opt.cage || {});
  fear(g, A.fearInCage, { face: EXPR.crying, tremble: 0.5 });
  drawCageAt(g, ...A.cage, 'front', opt.cage || {});
  if (opt.outside !== false) fear(g, A.fearOutside, { face: { ...EXPR.scared, lookX: 0.6, lookY: -0.8 }, headTilt: -0.15 });
  if (opt.ceo !== false) drawCEO(g, ...A.ceo, { face: { ...EXPR.sad, lookX: 0.5 } });
};
// emotions filing out through the exit door (s05b02)
const castExit = (g) => {
  const A = HQ_VIEWS.front.anchors;
  const [dx, dy] = A.exitDoor;
  const walkers = [['JOY', dx - 4, dy + 4, 0.25], ['CALM', dx + 70, dy + 60, 1], ['SADNESS', dx + 150, dy + 74, 1], ['ANGER', dx + 260, dy + 120, 1]];
  for (const [name, x, y, alpha] of walkers) drawEmo(g, name, x, y, hqScaleAt('front', y), { view: 'front', armL: 'rest', armR: 'rest', alpha, face: EXPR.worried, headTurn: -0.5, walk: { phase: x * 0.03 } });
  drawCEO(g, ...A.ceoSpot, { face: { ...EXPR.worried, lookX: -0.7 }, headTurn: -0.4 });
};

// ---------------------------------------------------------------- cells
const T = 2.15;
const F = HQ_VIEWS.front.cams, B = HQ_VIEWS.back.cams, AL = HQ_VIEWS.alarm.cams, BM = HQ_VIEWS.backOfMind.cams;
const cells = [
  ['front · wide (calm)', 'front', { t: T }, F.wide, castFront()],
  ['front · alarm=1, pulled', 'front', { t: T, alarm: 1, alarmPulled: 1 }, F.wide, castFront()],
  ['front · voidShadow=1 mist .8 dim .25', 'front', { t: T, voidShadow: 1, mist: 0.8, lightsDim: 0.25 }, F.wide, castFront()],
  ['front · establish (thumbnail, clean)', 'front', { t: T }, F.establish, castFront(), true],
  ['back · wide, screen room', 'back', { t: T, screenMode: 'room' }, B.wide, castBack()],
  ['back · screen cam, calm, look back', 'back', { t: T, screenMode: 'calm' }, B.screen, castBack({ lookBack: 1, ceoMid: true, cage: false, ceo: false, void: false, fearFace: EXPR.wonder })],
  ['back · alarm + voidShadow', 'back', { t: T, ...HQ_PRESETS.alarm, voidShadow: 1 }, B.wide, castBack()],
  ['back · console cam, press 0 + 9', 'back', { t: T, screenMode: 'calm', consolePress: { 0: 1, 9: 1 } }, B.console, castBack({ cage: false, ceo: false, void: false })],
  ['alarm · quiet (wide)', 'alarm', { t: T }, AL.wide, castAlarm()],
  ['alarm · ringing, pulled (medium)', 'alarm', { t: T, alarm: 1, alarmPulled: 1 }, AL.medium, castAlarm()],
  ['alarm · ceoKneel, hand on shoulder', 'alarm', { t: T }, AL.twoShot, castAlarm({ kneel: true })],
  ['front · door open, dim, evacuation', 'front', { t: T, ...HQ_PRESETS.chaos }, F.door, castExit],
  ['backOfMind · wide', 'backOfMind', { t: T, mist: 0.5 }, BM.wide, castBOM()],
  ['backOfMind · voidShadow=1 (ground)', 'backOfMind', { t: T, voidShadow: 1, mist: 0.7 }, BM.ground, castBOM()],
  ['backOfMind · cage cam', 'backOfMind', { t: T, mist: 0.5 }, BM.cage, castBOM({ ceo: false })],
  ['front · console cam, dawn, press', 'front', { t: T, ...HQ_PRESETS.dawn, consolePress: { 0: 1, 13: 0.7 } }, F.console, castFront({ consoleFear: true, ceo: false, fear: false, press: ['JOY', 'CALM'], spread: { ANGER: -40, SADNESS: 40 } })],
];

const TW = 360, TH = 640, cols = 4, rows = Math.ceil(cells.length / cols);
const sheet = createCanvas(TW * cols, (TH + 30) * rows);
const gs = sheet.getContext('2d');
gs.fillStyle = '#111'; gs.fillRect(0, 0, sheet.width, sheet.height);
const frame = createCanvas(W, H);
const gf = frame.getContext('2d');
cells.forEach(([name, view, st, cam, cast, noLabels], i) => {
  gf.setTransform(1, 0, 0, 1, 0, 0);
  gf.fillStyle = '#000'; gf.fillRect(0, 0, W, H);
  stage(gf, view, st, cam, cast, noLabels);
  vignette(gf, 0.3);
  const x = (i % cols) * TW, y = Math.floor(i / cols) * (TH + 30);
  gs.drawImage(frame, x, y + 30, TW, TH);
  gs.fillStyle = '#fff'; gs.font = '17px Fraunces'; gs.fillText(name, x + 6, y + 21);
  if (FULL) fs.writeFileSync(path.join(ROOT, `out/hq_${i}.png`), frame.toBuffer('image/png'));
});
fs.writeFileSync(path.join(ROOT, 'out/sheet_hq.png'), sheet.toBuffer('image/png'));
console.log('wrote out/sheet_hq.png');

// ---------------------------------------------------------------- timing (set only, worst-case state)
const tg = gf;
function time(lbl, fn, n = 50) {
  fn(0); // warm caches
  tg.getImageData(0, 0, 1, 1);
  const t0 = performance.now();
  for (let i = 0; i < n; i++) fn(i);
  tg.getImageData(0, 0, 1, 1);
  const ms = (performance.now() - t0) / n;
  console.log(`${lbl.padEnd(48)} ${ms.toFixed(2)} ms`);
}
const WORST = (i) => ({ t: i / 24, alarm: 1, alarmPulled: 1, voidShadow: 0.7, mist: 0.6, lightsDim: 0.3, consolePress: { 2: 0.5 }, screenMode: 'calm', screenModeB: 'room', screenBlend: 0.4, doorOpen: 0.5 });
for (const view of ['front', 'back', 'alarm', 'backOfMind']) {
  for (const camName of Object.keys(HQ_VIEWS[view].cams).slice(0, 3)) {
    const cam = HQ_VIEWS[view].cams[camName];
    for (const [lbl, mk] of [['calm', (i) => ({ t: i / 24 })], ['worst', WORST]]) {
      time(`set ${view} ${camName} z=${cam.zoom} ${lbl}`, (i) => {
        const st = mk(i);
        tg.setTransform(1, 0, 0, 1, 0, 0);
        tg.save(); applyCamera(tg, cam);
        drawHQ(tg, view, st); drawHQForeground(tg, view, st); drawAlarmLight(tg, view, st);
        tg.restore();
      });
    }
  }
}
time('drawConsole controls w=700 s=1', (i) => { tg.setTransform(1, 0, 0, 1, 0, 0); drawConsole(tg, 360, 900, 700, 1, { t: i / 24, consolePress: { 1: 1 } }); });
time('drawAlarmStation s=1.8 alarm', (i) => { tg.setTransform(1, 0, 0, 1, 0, 0); drawAlarmStation(tg, 360, 900, 1.8, { t: i / 24, alarm: 1, alarmPulled: 0.5 }); });
time('drawScreenContent 640x500 calm', (i) => { tg.setTransform(1, 0, 0, 1, 0, 0); drawScreenContent(tg, 40, 100, 640, 500, i / 24, 'calm'); });
