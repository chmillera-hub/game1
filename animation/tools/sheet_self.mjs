// Contact sheet for SELF / CONSCIOUSNESS: node tools/sheet_self.mjs [out.png]
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { drawSelf, SELF_EXPR, selfLocal, selfPoseAnchors, HEIGHT } from '../src/chars/self.mjs';
import { drawFear } from '../src/chars/fear.mjs';
import { EXPR } from '../src/face.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
for (const [f, n] of [['Caveat.ttf', 'Caveat'], ['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand']]) {
  const p = path.join(ROOT, 'assets/fonts', f);
  if (fs.existsSync(p)) GlobalFonts.registerFromPath(p, n);
}

const E = SELF_EXPR;
const BUST = 1.55; // expression close-ups
const FULL = 0.62; // full-body cells

function desk(g, x, y, w, s) {
  // simple stand-in desk: top surface below the desk line, front edge further down
  g.fillStyle = '#6b4a3a';
  g.fillRect(x - w / 2, y, w, 70 * s);
  g.fillStyle = '#8a6450';
  g.fillRect(x - w / 2, y, w, 6 * s);
  g.fillStyle = '#4a3226';
  g.fillRect(x - w / 2, y + 70 * s, w, 400);
}

const bust = (name, face, pose = {}) => ({
  name, w: 300, h: 330,
  draw(g, cx, top, w, h, t) {
    const s = BUST;
    drawSelf(g, cx, top + 212 + 488 * s, s, { t, face: { ...face, noAutoBlink: true }, ...pose });
  },
});
const full = (name, pose, opts = {}) => ({
  name, w: opts.w || 300, h: opts.h || 440,
  draw(g, cx, top, w, h, t) {
    if (opts.pre) opts.pre(g, cx, top, w, h, t);
    drawSelf(g, cx + (opts.dx || 0), top + h - 24 - (opts.lift || 0), opts.s || FULL, { t, ...pose, face: { noAutoBlink: true, ...(pose.face || {}) } });
  },
});

const cells = [
  bust('neutral', E.neutral, { outfit: 'sweater' }),
  bust('worried', E.worried, { outfit: 'ceo' }),
  bust('sternKind', E.sternKind, { outfit: 'ceo', headTilt: -0.04 }),
  bust('holdingBackTears', E.holdingBackTears, { outfit: 'ceo', headTilt: 0.06 }),
  bust('single tear', E.singleTear, { outfit: 'sweater', headTilt: 0.08 }),
  bust('tender smile', E.tenderSmile, { outfit: 'sweater', headTilt: -0.1 }),
  bust('tired', E.tired, { outfit: 'ceo', headTilt: 0.05 }),
  bust('wonder', { ...E.wonder, t: 2 }, { outfit: 'sweater', headDY: -3 }),
  bust('3/4 turn + look', { ...E.calm, lookX: 0.5 }, { outfit: 'ceo', headTurn: 0.55, bodyTurn: 0.3 }),
  bust('wipeTear (sweater paw)', { ...E.singleTear, tearR: 0, tears: 0.5, lidU: 0.45 }, { outfit: 'sweater', armR: 'wipeTear', headTilt: 0.1 }),
  bust('rubNeck sheepish', E.sheepish, { outfit: 'ceo', armR: 'rubNeck', headTilt: 0.08 }),
  bust('handOnHeart', E.tenderSmile, { outfit: 'sweater', armL: 'handOnHeart', headTilt: -0.06 }),
  full('sweater stand', { outfit: 'sweater', face: E.calm }),
  full('CEO + clipboard', { outfit: 'ceo', clipboard: true, face: { ...E.focused, lookY: 0.5, lookX: -0.3 }, headTilt: 0.08 }),
  full('CEO walk 0', { outfit: 'ceo', clipboard: true, walk: { phase: 0.6 }, face: E.calm }),
  full('CEO walk 1', { outfit: 'ceo', clipboard: true, walk: { phase: 0.6 + Math.PI / 2 }, face: E.calm }),
  {
    name: 'CEO kneel: hand on Fear-height shoulder (Fear at true relative scale)', w: 600, h: 440,
    draw(g, cx, top, w, h, t) {
      const s = 0.72, gy = top + h - 24;
      const sx = cx - 150, fx = sx + 172;
      const pose = { t, outfit: 'ceo', kneel: 1, facing: 1, bodyTurn: 0.45, headTurn: 0.4, face: { ...E.sternKind, lookX: 0.55, lookY: 0.55, noAutoBlink: true }, headTilt: 0.14 };
      // Fear faces Self (facing -1); its near shoulder sits just under the big head, ~34px left of centre, 128px up
      const fs_ = s;
      const target = selfLocal(sx, gy, s, 1, fx - 38 * fs_, gy - 132 * fs_);
      pose.armR = { preset: 'onShoulder', target };
      drawSelf(g, sx, gy, s, { ...pose, layer: 'body' });
      drawFear(g, fx, gy, fs_, { t, facing: -1, face: { ...EXPR.scared, lookX: -0.6, lookY: -0.4, noAutoBlink: true }, tremble: 0.5, armL: 'hugSelf', armR: 'hugSelf', crouch: 0.15 });
      drawSelf(g, sx, gy, s, { ...pose, layer: 'front' });
    },
  },
  full('kneel 0.5 (going down)', { outfit: 'ceo', kneel: 0.5, face: E.worried }),
  full('palmOut (gentle stop)', { outfit: 'ceo', armR: 'palmOut', face: E.sternKind, headTurn: 0.25 }),
  full('pointing + reachOut', { outfit: 'sweater', armR: 'pointing', armL: 'reachOut', face: E.surprised, headTurn: 0.3 }),
  full('seated: holdNotebook', { outfit: 'sweater', seated: true, armL: 'holdNotebook', armR: 'holdNotebook', face: { ...E.tenderSmile, lookY: 0.6 }, headTilt: 0.08 }, {
    s: 0.95, h: 440, lift: 86, pre: (g, cx, top, w, h) => desk(g, cx, top + h - 110, w, 0.95),
  }),
  full('seated: chinInHand', { outfit: 'sweater', seated: true, armR: 'chinInHand', armL: 'handsOnDesk', face: { ...E.tired, lookX: -0.4 }, headTilt: 0.14, lean: 0.06 }, {
    s: 0.95, h: 440, lift: 86, pre: (g, cx, top, w, h) => desk(g, cx, top + h - 110, w, 0.95),
  }),
  full('back view (CEO at console)', { outfit: 'ceo', view: 'back', face: E.neutral }),
  full('back view, over shoulder', { outfit: 'ceo', view: 'back', headTurn: 0.85, face: { ...E.worried, lookX: 1 } }),
  full('seated: showNotebook cover', { outfit: 'sweater', seated: true, armL: 'showNotebook', armR: 'showNotebook', face: { ...E.tenderSmile, lookY: 0.6 }, headTilt: 0.1, headTurn: -0.25, bodyTurn: -0.2 }, {
    s: 0.95, h: 440, lift: 86, pre: (g, cx, top, w, h) => desk(g, cx, top + h - 110, w, 0.95),
  }),
  full('sweater back view, rubEyes', { outfit: 'sweater', view: 'back', armL: 'rubEyes', armR: 'rubEyes', headTilt: 0.12 }),
  full('facing -1, 3/4 walk', { outfit: 'sweater', facing: -1, walk: { phase: 2.2 }, face: E.tenderSmile }),
  full('handsOnDesk, focused', { outfit: 'ceo', seated: true, face: E.focused, headTilt: 0.12 }, {
    s: 0.95, h: 440, lift: 86, pre: (g, cx, top, w, h) => desk(g, cx, top + h - 110, w, 0.95),
  }),
];

// pack rows of total width 1200
const SW = 1200;
const rows = [];
let row = [], rw = 0;
for (const c of cells) {
  if (rw + c.w > SW) { rows.push(row); row = []; rw = 0; }
  row.push(c); rw += c.w;
}
if (row.length) rows.push(row);
const SH = rows.reduce((s, r) => s + Math.max(...r.map((c) => c.h)), 0);
const cv = createCanvas(SW, SH), g = cv.getContext('2d');
g.fillStyle = '#2b2440';
g.fillRect(0, 0, SW, SH);
let y = 0, i = 0;
for (const r of rows) {
  const rh = Math.max(...r.map((c) => c.h));
  let x = 0;
  for (const c of r) {
    g.save();
    g.fillStyle = (i++ % 2) ? '#342b4f' : '#30284a';
    g.fillRect(x, y, c.w, rh);
    g.beginPath(); g.rect(x, y, c.w, rh); g.clip();
    c.draw(g, x + c.w / 2, y, c.w, rh, 1.3 + i * 0.37);
    g.restore();
    g.fillStyle = 'rgba(0,0,0,0.35)';
    g.fillRect(x, y, c.w, 30);
    g.fillStyle = '#fff';
    g.font = '19px "Patrick Hand", sans-serif';
    g.fillText(c.name, x + 10, y + 21);
    x += c.w;
  }
  y += rh;
}
fs.writeFileSync(process.argv[2] || path.join(ROOT, 'out/sheet_self.png'), cv.toBuffer('image/png'));

// ---- timing
const tc = createCanvas(720, 1280), tg = tc.getContext('2d');
const timings = {};
for (const [name, pose] of [
  ['standing ceo clipboard', { outfit: 'ceo', clipboard: true, face: E.worried }],
  ['walk sweater', { outfit: 'sweater', walk: { phase: 1 }, face: E.calm }],
  ['kneel onShoulder', { outfit: 'ceo', kneel: 1, armR: { preset: 'onShoulder', target: [150, -134] }, face: E.sternKind }],
  ['seated notebook', { outfit: 'sweater', seated: true, armL: 'holdNotebook', armR: 'holdNotebook', face: E.tenderSmile }],
  ['back over shoulder', { outfit: 'ceo', view: 'back', headTurn: 0.8, face: E.worried }],
]) {
  for (let j = 0; j < 5; j++) drawSelf(tg, 360, 1200, 1.8, { t: j * 0.1, ...pose });
  const N = 50, t0 = process.hrtime.bigint();
  for (let j = 0; j < N; j++) drawSelf(tg, 360, 1200, 1.8, { t: j * 0.04, ...pose });
  timings[name] = Number(process.hrtime.bigint() - t0) / 1e6 / N;
}
console.log('ms per draw:', Object.entries(timings).map(([k, v]) => `${k}=${v.toFixed(2)}`).join('  '));
console.log('anchors standing headCenter', selfPoseAnchors(0, 0, 1, {}).headCenter, 'HEIGHT', HEIGHT);
