// Contact sheets for THE VOID and the COSMOS.
//   node tools/sheet_void.mjs            → out/sheet_void.png + out/sheet_cosmos.png (+ timing to stdout)
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { drawVoid, drawVoidGlow, drawVoidShadow, drawVoidArm, drawVoidHand, voidRig, toVoidLocal, VOID_HANDS, VOID_POSES, HEIGHT } from '../src/chars/void.mjs';
import { drawCosmos, preloadCosmos } from '../src/fx/cosmos.mjs';
import { drawFear } from '../src/chars/fear.mjs';
import { EXPR } from '../src/face.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
GlobalFonts.registerFromPath(path.join(ROOT, 'assets/fonts/PatrickHand.ttf'), 'Patrick Hand');
const out = (f) => path.join(ROOT, 'out', f);

// --- a stand-in "back of the mind" room so the silhouette is judged in context
function room(g, x, y, w, h, floorY) {
  const gw = g.createLinearGradient(0, y, 0, floorY);
  gw.addColorStop(0, '#1d1936'); gw.addColorStop(1, '#0d0b1c');
  g.fillStyle = gw; g.fillRect(x, y, w, floorY - y);
  const gf = g.createLinearGradient(0, floorY, 0, y + h);
  gf.addColorStop(0, '#15122a'); gf.addColorStop(1, '#221d3f');
  g.fillStyle = gf; g.fillRect(x, floorY, w, y + h - floorY);
}
function cage(g, cx, floorY, s, open = 0) {
  // simple placeholder time-out cage (the real one lives in the sets module)
  g.save();
  g.translate(cx, floorY); g.scale(s, s);
  g.strokeStyle = '#9b8a6a'; g.lineWidth = 4;
  g.beginPath(); g.ellipse(0, -8, 120, 18, 0, 0, Math.PI * 2); g.stroke();
  for (let i = -5; i <= 5; i++) { g.beginPath(); g.moveTo(i * 22, -8); g.lineTo(i * 22, -250 + Math.abs(i) * 6); g.stroke(); }
  g.beginPath(); g.ellipse(0, -250, 120, 40, 0, Math.PI, Math.PI * 2); g.stroke();
  g.beginPath(); g.moveTo(-120, -250); g.lineTo(-120, -8); g.moveTo(120, -250); g.lineTo(120, -8); g.stroke();
  // door frame (front-left) + latch
  g.strokeStyle = '#c9b48a'; g.lineWidth = 5;
  g.beginPath(); g.rect(-118, -200, 70, 150); g.stroke();
  g.fillStyle = '#e8c25a'; g.beginPath(); g.arc(-52, -125, 7, 0, Math.PI * 2); g.fill();
  g.restore();
  return [cx + (-52) * s, floorY - 125 * s]; // latch (world)
}

const CW = 540, CH = 1180, FLOOR = 1070, VS = 0.55;
const T0 = 3.2;
const cells = [
  ['front · darkness', (g, cx, fy, t) => { drawVoid(g, cx, fy, VS, { t, shadowSpread: 0.35 }); }],
  ['head turned left', (g, cx, fy, t) => { drawVoid(g, cx, fy, VS, { t, ...VOID_POSES.turnLeft, shadowSpread: 0.35 }); }],
  ['head down · hand on Fear', (g, cx, fy, t) => {
    const vx = cx - 100, fx = cx + 130, ffy = fy + 40;
    // Fear's near (screen-left) shoulder, in Void-local coords (Fear scale 1, Void scale VS)
    const sh = toVoidLocal(vx, fy, VS, fx - 34, ffy - 114);
    const pose = { t, ...VOID_POSES.lookDownRight, cosmos: 0, shadowSpread: 0.5, handR: { ...VOID_HANDS.shoulder(sh, 1), defer: 'hand' } };
    drawVoid(g, vx, fy, VS, pose);
    drawFear(g, fx, ffy, 1.0, { t, face: { ...EXPR.wonder, lookX: -0.55, lookY: -0.9, tears: 0.7, noAutoBlink: true }, headTurn: -0.3, headTilt: -0.12, tremble: 0.1, armL: 'chest', armR: 'rest' });
    drawVoidHand(g, vx, fy, VS, pose, 'R');
  }],
  ['unlock · one fingertip', (g, cx, fy, t) => {
    // the cage stands in FRONT of the Void: body first (arm deferred), then the cage, then the arm on top
    const vx = cx + 60, cgx = cx - 140, cgy = fy + 30;
    const latch = [cgx - 52 * 0.8, cgy - 125 * 0.8];
    const pose = { t, headTurn: -0.15, headDown: 0.1, shadowSpread: 0.5, handL: { ...VOID_HANDS.unlock(toVoidLocal(vx, fy, VS, ...latch)), defer: true } };
    drawVoid(g, vx, fy, VS, pose);
    cage(g, cgx, cgy, 0.8);
    drawVoidArm(g, vx, fy, VS, pose, 'L');
  }],
  ['cosmos 0.3', (g, cx, fy, t) => { drawVoid(g, cx, fy, VS, { t, headDown: 0.1, cosmos: 0.3, shadowSpread: 0.35 }); drawVoidGlow(g, cx, fy, VS, { t, headDown: 0.1, cosmos: 0.3 }); }],
  ['cosmos 1', (g, cx, fy, t) => { drawVoid(g, cx, fy, VS, { t, headDown: 0.1, cosmos: 1, shadowSpread: 0.35 }); drawVoidGlow(g, cx, fy, VS, { t, headDown: 0.1, cosmos: 1 }); }],
  ['silhouette · shadow 1', (g, cx, fy, t) => { drawVoidShadow(g, cx, fy, VS, { t, shadowSpread: 1 }); drawVoid(g, cx, fy, VS, { t, silhouette: true, shadow: false }); }],
  ['close-up: look down, cosmos 1', (g, cx, fy, t) => {
    const pose = { t, ...VOID_POSES.lookDownLeft, cosmos: 1 };
    const r = voidRig(pose);
    const s = 2.3;
    const oy = fy - FLOOR + 470;
    drawVoid(g, cx - r.face[0] * s, oy - r.face[1] * s, s, { ...pose, shadow: false });
    drawVoidGlow(g, cx - r.face[0] * s, oy - r.face[1] * s, s, pose);
  }],
  ['gentle push (hand behind Fear)', (g, cx, fy, t) => {
    // fingertips meet Fear's back edge; the hand is drawn BEHIND Fear (no defer)
    const vx = cx - 110, fx = cx + 150, ffy = fy + 30;
    const back = toVoidLocal(vx, fy, VS, fx - 34, ffy - 112);
    const pose = { t, headTurn: -0.2, headDown: 0.05, lean: 0.03, shadowSpread: 0.4, cosmos: 0.35, handR: VOID_HANDS.push(back, 1) };
    drawVoid(g, vx, fy, VS, pose);
    drawFear(g, fx, ffy, 1.0, { t, facing: 1, face: { ...EXPR.softSmile, lookX: -0.7, lookY: -0.5, tears: 0.4, noAutoBlink: true }, headTurn: -0.6, walk: { phase: 0.6 } });
    drawVoidGlow(g, vx, fy, VS, pose);
  }],
  ['hand emerging (show 0.5)', (g, cx, fy, t) => { drawVoid(g, cx, fy, VS, { t, handL: { show: 0.5 }, handR: { show: 1, open: 0.6, gentle: 0.4 } }); }],
  ['alpha 0.5 · offer', (g, cx, fy, t) => { drawVoid(g, cx - 60, fy, VS, { t, alpha: 0.5, headDown: 0.4, headTurn: 0.3, handR: VOID_HANDS.offer([420, -680], 1) }); }],
  ['turn right · cosmos 0.6', (g, cx, fy, t) => { const p = { t, ...VOID_POSES.turnRight, cosmos: 0.6, shadowSpread: 0.35 }; drawVoid(g, cx, fy, VS, p); drawVoidGlow(g, cx, fy, VS, p); }],
  ['near profile (turn -1) · idle 0', (g, cx, fy, t) => { drawVoid(g, cx, fy, VS, { t, headTurn: -1, headDown: 0.15, idle: 0, shadowSpread: 0.6 }); }],
  ['push-in: hood darkness (scale 4)', (g, cx, fy, t) => {
    const pose = { t, ...VOID_POSES.distance, idle: 0 };
    const r = voidRig(pose), s = 4;
    drawVoid(g, cx - r.face[0] * s, fy - FLOOR + 560 - r.face[1] * s, s, { ...pose, shadow: false });
  }],
  ['hem close-up · foldStar 1', (g, cx, fy, t) => { drawVoid(g, cx + 60, fy - 60, 1.6, { t, foldStar: 1, shadowSpread: 0.6 }); }],
  ['point · offer · cosmos 0.12 (scale 0.4)', (g, cx, fy, t) => {
    drawVoid(g, cx + 70, fy, 0.4, { t, headTurn: -0.5, cosmos: 0.12, handL: VOID_HANDS.point([-720, -820]), handR: VOID_HANDS.offer([420, -700], 1) });
  }],
];

const cols = 4, rows = Math.ceil(cells.length / cols);
const c = createCanvas(CW * cols, CH * rows), g = c.getContext('2d');
cells.forEach(([label, fn], i) => {
  const x = (i % cols) * CW, y = Math.floor(i / cols) * CH;
  g.save();
  g.beginPath(); g.rect(x, y, CW, CH); g.clip();
  room(g, x, y, CW, CH, y + FLOOR - 40);
  fn(g, x + CW / 2, y + FLOOR, T0 + i * 0.7);
  g.restore();
  g.fillStyle = 'rgba(0,0,0,0.45)'; g.fillRect(x, y, CW, 44);
  g.fillStyle = '#fff'; g.font = '30px "Patrick Hand"'; g.fillText(label, x + 14, y + 32);
  g.strokeStyle = '#000'; g.lineWidth = 2; g.strokeRect(x, y, CW, CH);
});
fs.writeFileSync(out('sheet_void.png'), c.toBuffer('image/png'));

// --- cosmos close-ups (full 720x1280 frames)
preloadCosmos();
const cc = createCanvas(720 * 3 + 40, 1280), gc = cc.getContext('2d');
gc.fillStyle = '#000'; gc.fillRect(0, 0, cc.width, cc.height);
[[1, 'reveal 1'], [0.4, 'reveal 0.4'], [0.12, 'reveal 0.12 (kindles from the centre)']].forEach(([rv, label], i) => {
  gc.save();
  gc.translate(i * 740, 0);
  gc.beginPath(); gc.rect(0, 0, 720, 1280); gc.clip();
  drawCosmos(gc, 360, 640, 380, 660, 12, { reveal: rv });
  gc.restore();
  gc.fillStyle = 'rgba(255,255,255,0.8)'; gc.font = '30px "Patrick Hand"'; gc.fillText(label, i * 740 + 16, 40);
});
fs.writeFileSync(out('sheet_cosmos.png'), cc.toBuffer('image/png'));

if (process.env.NO_TIMING) process.exit(0);
// --- timing. NOTE: @napi-rs/canvas records draw calls lazily and rasterizes on readback, so every
// sample includes a full-frame getImageData (as the renderer does) and the clear+readback baseline is
// subtracted. Min and median of 40 frames are reported (other processes add noise to the median).
const tc = createCanvas(720, 1280), tg = tc.getContext('2d');
const frame = (fn, t) => {
  const t0 = performance.now();
  tg.fillStyle = '#16132b'; tg.fillRect(0, 0, 720, 1280);
  fn(t);
  tg.getImageData(0, 0, 720, 1280);
  return performance.now() - t0;
};
const time = (label, fn) => {
  // baseline (clear + readback) frames are interleaved with the measured frames
  const a = [], b = [];
  for (let i = 0; i < 50; i++) {
    const tb = frame(() => {}, 0), ta = frame(fn, i / 24);
    if (i >= 5) { a.push(ta); b.push(tb); }
  }
  a.sort((x, y) => x - y); b.sort((x, y) => x - y);
  const med = (v) => v[v.length >> 1];
  console.log(`${label.padEnd(46)} min ${(a[0] - b[0]).toFixed(2).padStart(6)} ms   median ${(med(a) - med(b)).toFixed(2).padStart(6)} ms`);
};
time('Fear (reference)', (t) => drawFear(tg, 360, 1100, 1, { t }));
time('drawVoid 0.55 (wide, dark)', (t) => drawVoid(tg, 360, 1150, 0.55, { t, shadowSpread: 0.5 }));
time('drawVoid 0.55 cosmos 1', (t) => drawVoid(tg, 360, 1150, 0.55, { t, cosmos: 1, shadowSpread: 0.5 }));
time('drawVoid 0.55 cosmos 1 + one hand + glow', (t) => { const p = { t, cosmos: 1, headDown: 0.6, headTurn: 0.4, handR: VOID_HANDS.shoulder([300, -250]) }; drawVoid(tg, 360, 1150, 0.55, p); drawVoidGlow(tg, 360, 1150, 0.55, p); });
time('drawVoid 0.55 cosmos 1 + two hands', (t) => drawVoid(tg, 360, 1150, 0.55, { t, cosmos: 1, handR: VOID_HANDS.shoulder([300, -250]), handL: VOID_HANDS.unlock([-350, -300]) }));
time('drawVoid 1.0 (towering, cropped) cosmos 1', (t) => drawVoid(tg, 360, 1700, 1.0, { t, cosmos: 1 }));
time('drawVoid hood close-up 2.3 cosmos 1', (t) => drawVoid(tg, 360, 640 + 1500 * 2.3, 2.3, { t, cosmos: 1, shadow: false }));
time('drawVoid face fills frame 4.5 cosmos 1', (t) => drawVoid(tg, 360, 640 + 1500 * 4.5, 4.5, { t, cosmos: 1, shadow: false }));
time('drawVoid hood push-in 4.0 darkness', (t) => drawVoid(tg, 360, 640 + 1500 * 4.0, 4.0, { t, shadow: false }));
time('drawVoid hem close-up 1.6 + foldStar', (t) => drawVoid(tg, 420, 1100, 1.6, { t, foldStar: 1, shadowSpread: 0.6 }));
time('drawVoid 0.55 alpha 0.6 (layer)', (t) => drawVoid(tg, 360, 1150, 0.55, { t, alpha: 0.6 }));
time('drawVoidGlow 0.55', (t) => drawVoidGlow(tg, 360, 1150, 0.55, { t, cosmos: 1, headDown: 0.6 }));
time('drawCosmos full screen reveal 1', (t) => drawCosmos(tg, 360, 640, 380, 660, t, { reveal: 1 }));
time('drawCosmos full screen reveal 0.4', (t) => drawCosmos(tg, 360, 640, 380, 660, t, { reveal: 0.4 }));
time('drawCosmos small (hood, rx 48)', (t) => drawCosmos(tg, 360, 640, 48, 64, t, { reveal: 1, clip: 'ellipse' }));
