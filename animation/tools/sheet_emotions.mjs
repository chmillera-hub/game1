// Character sheet for src/chars/emotions.mjs  →  out/sheet_emotions.png
//   node tools/sheet_emotions.mjs [out.png] [--extra]     (--extra also writes out/sheet_emotions_poses.png)
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { drawEmotion, EMOTION_EXPR, EMOTION_HEIGHTS, LOOKBACK_SMILE, PANIC_FACE } from '../src/chars/emotions.mjs';
import { drawFear } from '../src/chars/fear.mjs';
import { EXPR } from '../src/face.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
GlobalFonts.registerFromPath(path.join(ROOT, 'assets/fonts/PatrickHand.ttf'), 'Patrick Hand');
GlobalFonts.registerFromPath(path.join(ROOT, 'assets/fonts/Fraunces.ttf'), 'Fraunces');

const NAMES = ['JOY', 'SADNESS', 'ANGER', 'CALM'];
const COLS = [
  ['front neutral', () => ({})],
  ['signature', (n) => ({ face: EMOTION_EXPR[n], ...SIG_POSE[n] })],
  ['back view', () => ({ view: 'back' })],
  ['lookBack = 1 smile', () => ({ view: 'back', lookBack: 1, face: LOOKBACK_SMILE })],
  ['coverEars panic', () => ({ face: PANIC_FACE, armL: 'coverEars', armR: 'coverEars', tremble: 0.7, crouch: 0.35 })],
  ['pressButton front', () => ({ face: { ...EXPR.determined, lookY: 0.7 }, armL: 'pressButton', armR: { preset: 'pressButton', dy: 6 }, lean: 0.04 })],
  ['pressButton back', () => ({ view: 'back', armL: 'pressButton', armR: { preset: 'pressButton', dy: 8 } })],
];
const SIG_POSE = {
  JOY: { armL: 'cheer', armR: 'wave' },
  SADNESS: { armL: 'hugSelf', armR: 'hugSelf', headTilt: 0.08, crouch: 0.15 },
  ANGER: { armL: 'handsOnHips', armR: 'handsOnHips', heat: 0.8 },
  CALM: { armL: 'clasp', armR: 'clasp', headTilt: -0.06 },
};

const SC = 0.92;
const cw = 330, ch = 560, head = 44, lineupH = 600;
const W = cw * COLS.length, H = head + ch * NAMES.length + lineupH;
const c = createCanvas(W, H), g = c.getContext('2d');
g.fillStyle = '#211c38'; g.fillRect(0, 0, W, H);
g.fillStyle = '#f3ecff'; g.font = '30px Fraunces';
g.fillText('THE OTHER EMOTIONS — sheet (scale ' + SC + ')', 16, 33);

const timings = {};
NAMES.forEach((n, r) => {
  COLS.forEach(([label, fn], col) => {
    const x = col * cw, y = head + r * ch;
    g.fillStyle = (r + col) % 2 ? '#2e2750' : '#2a2449'; g.fillRect(x, y, cw, ch);
    // floor line
    g.fillStyle = 'rgba(255,255,255,0.04)'; g.fillRect(x, y + ch - 34, cw, 34);
    const pose = { t: 1.7 + col * 0.53 + r * 0.31, ...fn(n) };
    pose.face = { ...(pose.face || {}), noAutoBlink: true };
    drawEmotion(g, n, x + cw / 2, y + ch - 34, SC, pose);
    g.fillStyle = '#fff'; g.font = '22px "Patrick Hand"';
    g.fillText(`${n} · ${label}`, x + 10, y + 26);
  });
});

// lineup: Fear at correct relative scale with the family + Consciousness height mark
const ly = head + ch * NAMES.length;
g.fillStyle = '#26203f'; g.fillRect(0, ly, W, lineupH);
g.fillStyle = 'rgba(255,255,255,0.05)'; g.fillRect(0, ly + lineupH - 40, W, 40);
const ls = 0.9, ground = ly + lineupH - 40;
g.strokeStyle = 'rgba(255,255,255,0.18)'; g.setLineDash([8, 8]); g.lineWidth = 2;
for (const [h, lab] of [[600, 'CONSCIOUSNESS 600'], [330, 'FEAR 330']]) {
  g.beginPath(); g.moveTo(0, ground - h * ls); g.lineTo(W, ground - h * ls); g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.5)'; g.font = '18px "Patrick Hand"'; g.fillText(lab, 10, ground - h * ls - 6);
}
g.setLineDash([]);
const lineup = [
  ['FEAR', 0.2], ['JOY', 0.35], ['SADNESS', 0.5], ['ANGER', 0.66], ['CALM', 0.82],
];
for (const [n, fx] of lineup) {
  const x = W * fx;
  const t = 2.2 + fx * 3;
  if (n === 'FEAR') drawFear(g, x, ground, ls, { t, face: { ...EXPR.softSmile, noAutoBlink: true } });
  else drawEmotion(g, n, x, ground, ls, { t, face: { ...EXPR.smile, lookX: n === 'JOY' ? -0.4 : -0.2, noAutoBlink: true } });
  g.fillStyle = '#fff'; g.font = '22px "Patrick Hand"';
  g.fillText(n + (n === 'FEAR' ? ' (drawFear)' : ' ' + EMOTION_HEIGHTS[n]), x - 50, ground + 28);
}
g.fillStyle = '#fff'; g.font = '22px "Patrick Hand"';
g.fillText('family lineup at one scale (0.9) — dashed lines: Consciousness 600, Fear 330', W - 760, ly + 28);

const out = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : path.join(ROOT, 'out/sheet_emotions.png');
fs.writeFileSync(out, c.toBuffer('image/png'));

// ---- timing: ms per drawEmotion call (front and back/lookBack), ~50 draws each
const tc = createCanvas(720, 1280), tg = tc.getContext('2d');
for (const n of NAMES) {
  for (const [lab, pose] of [['front', { face: EMOTION_EXPR[n], armL: 'wave', armR: 'pressButton' }], ['back+look', { view: 'back', lookBack: 0.8, face: LOOKBACK_SMILE, armL: 'pressButton', armR: 'pressButton' }]]) {
    for (let i = 0; i < 10; i++) drawEmotion(tg, n, 360, 1000, 1, { t: i * 0.1, ...pose });
    tg.getImageData(0, 0, 1, 1); // flush
    const t0 = performance.now();
    for (let i = 0; i < 50; i++) { drawEmotion(tg, n, 360, 1000, 1, { t: i * 0.1, ...pose }); tg.getImageData(360, 700, 1, 1); }
    const t1 = performance.now();
    for (let i = 0; i < 50; i++) tg.getImageData(360, 700, 1, 1);
    timings[`${n} ${lab}`] = ((t1 - t0 - (performance.now() - t1)) / 50).toFixed(2) + ' ms';
  }
}
console.log('wrote', out);
console.log(timings);

if (process.argv.includes('--extra')) {
  // all presets & states, for development
  const rows = [
    ['rest', {}], ['wave', { armR: 'wave', face: EXPR.smile }], ['flail', { armL: 'flail', armR: 'flail', face: PANIC_FACE, tremble: 0.6 }],
    ['handsOnHips', { armL: 'handsOnHips', armR: 'handsOnHips', face: EXPR.stern }], ['hugSelf', { armL: 'hugSelf', armR: 'hugSelf', face: EXPR.worried }],
    ['pointing', { armR: 'pointing', face: EXPR.surprised }], ['wipeEye', { armL: 'wipeEye', face: EXPR.crying }],
    ['walk', { walk: { phase: 1.2 }, face: EXPR.smile }], ['headTurn -0.7', { headTurn: -0.7, face: { lookX: -0.8 } }],
    ['back wave', { view: 'back', armR: 'wave' }], ['lookBack 0.4', { view: 'back', lookBack: 0.4, face: LOOKBACK_SMILE }],
    ['lookBack 0.7', { view: 'back', lookBack: 0.7, face: LOOKBACK_SMILE }], ['lookBack 1 L', { view: 'back', lookBack: 1, lookSide: -1, face: LOOKBACK_SMILE }],
    ['facing -1 back look', { view: 'back', facing: -1, lookBack: 1, face: LOOKBACK_SMILE, armL: 'pressButton', armR: 'pressButton' }],
  ];
  const cw2 = 260, ch2 = 520;
  const c2 = createCanvas(cw2 * rows.length, ch2 * 4), g2 = c2.getContext('2d');
  g2.fillStyle = '#211c38'; g2.fillRect(0, 0, c2.width, c2.height);
  NAMES.forEach((n, r) => rows.forEach(([lab, pose], col) => {
    const x = col * cw2, y = r * ch2;
    g2.fillStyle = (r + col) % 2 ? '#2e2750' : '#2a2449'; g2.fillRect(x, y, cw2, ch2);
    drawEmotion(g2, n, x + cw2 / 2, y + ch2 - 24, 0.8, { t: 1.3 + col * 0.41, ...pose, face: { ...(pose.face || {}), noAutoBlink: true } });
    g2.fillStyle = '#fff'; g2.font = '20px "Patrick Hand"'; g2.fillText(`${n} · ${lab}`, x + 8, y + 22);
  }));
  fs.writeFileSync(path.join(ROOT, 'out/sheet_emotions_poses.png'), c2.toBuffer('image/png'));
  console.log('wrote out/sheet_emotions_poses.png');
}
