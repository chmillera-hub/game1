// ===== Shot engine =====
const TL = window.TIMELINE || {};
const CAPS = TL.captions || [];
const MOUTHS = TL.mouth || {};
function mouthAt(face, t, gain = 1.4) {
  const a = MOUTHS[face]; if (!a) return 0;
  const i = Math.round(t * 24);
  const v = ((a[i - 1] || 0) + 2 * (a[i] || 0) + (a[i + 1] || 0)) / 4;
  return clamp(v * gain);
}
function charLit(ctx, p, light = {}) {
  const g = layer(1);
  drawCharacter(g, p);
  g.globalCompositeOperation = 'source-atop';
  if (light.amb) { g.fillStyle = rgba(light.amb[0], light.amb[1]); g.fillRect(0, 0, W, H); }
  for (const k of light.keys || []) {
    const [col, amt, x0, y0, r] = k;
    const gr = g.createRadialGradient(x0, y0, 0, x0, y0, r); gr.addColorStop(0, rgba(col, amt)); gr.addColorStop(1, rgba(col, 0));
    g.fillStyle = gr; g.fillRect(0, 0, W, H);
  }
  if (light.flash) { g.fillStyle = rgba([225, 225, 255], light.flash); g.fillRect(0, 0, W, H); }
  g.globalCompositeOperation = 'source-over';
  ctx.drawImage(LAYER[1], 0, 0);
}
function runShots(ctx, t, shots) {
  for (let i = 0; i < shots.length; i++) {
    const s = shots[i], nx = shots[i + 1];
    const b = nx ? nx.a + (nx.xf || 0) : 1e9;
    if (t < s.a || t >= b) continue;
    const a = s.xf ? ss(s.a, s.a + s.xf, t) : 1;
    if (a >= 0.999) s.f(ctx, t, t - s.a);
    else { const g = layer(0); s.f(g, t, t - s.a); ctx.save(); ctx.globalAlpha = a; ctx.drawImage(LAYER[0], 0, 0); ctx.restore(); }
  }
}
function shake(ctx, t, amt) { if (amt > 0) ctx.translate(noise1(t * 23) * amt, noise1(t * 19 + 5) * amt); }
function saccade(t, seed, amt = 0.08) { const k = Math.floor(t * 2.3 + seed); return [noise1(k * 1.7) * amt, noise1(k * 2.9 + 4) * amt * 0.6]; }
function camera(ctx, cx, cy, z) { ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-cx, -cy); }

// ===================== PART 1 =====================
const P1 = [];
P1.push({ a: 0, f(ctx, t) {
  ctx.fillStyle = '#04050a'; ctx.fillRect(0, 0, W, H);
  rainStreaks(ctx, t, 180, 1300, 0.12, 0.12, 2, 26);
  titleCard(ctx, t, 'THE SONG IN THE STORM', 'Part One — The Storm', fade(t, 1.2, 9.2, 1.8, 1.2));
} });
P1.push({ a: 9, xf: 1.5, f(ctx, t, lt) {
  const camY = 960 * easeIO(clamp((lt - 0.5) / 9.5));
  const hx = lerp(1180, 560, clamp((lt - 3) / 9));
  drawCity(ctx, t, camY, { him: { x: hx, phase: t * 5.4, headDown: 0.7 } });
  vignette(ctx, 0.7);
} });
P1.push({ a: 19.5, xf: 0.8, f(ctx, t, lt) {
  const bg = ctx.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, '#070912'); bg.addColorStop(1, '#141826');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  const r = rng(12);
  for (let i = 0; i < 40; i++) {
    const depth = 0.3 + r(), x = ((r() * 2600 + t * 90 * depth) % 2600) - 600, y = 120 + r() * 520, rr = (14 + r() * 40) * depth;
    const warm = r() > 0.35;
    const gr = ctx.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, warm ? 'rgba(255,180,100,0.28)' : 'rgba(130,170,255,0.22)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gr; ctx.fillRect(x - rr, y - rr, rr * 2, rr * 2);
  }
  const bob = Math.abs(Math.sin(t * 2.7)) * 10;
  const look = kf(t, [[19.5, 0], [26.0, 0], [26.4, 1], [27.6, 1], [28.0, 0]]);
  const [sx, sy] = saccade(t, 3, 0.06);
  const lamp = ((lt * 260) % 1700) - 300;
  charLit(ctx, { who: 'him', x: 640, y: 390 + bob, s: 1.42, t, tilt: Math.sin(t * 2.7) * 0.015 + look * 0.04, gx: lerp(-0.15, 0.85, look) + sx, gy: lerp(0.55, 0.05, look) + sy, open: lerp(0.68, 0.92, look), tired: 0.6, sad: lerp(0.2, 0.6, look), blink: blinkAt(t, 1), wind: 0.4 },
    { amb: [[10, 20, 55], 0.38], keys: [[[255, 180, 110], 0.28, W - lamp, 160, 520]] });
  rainStreaks(ctx, t, 200, 1600, 0.08, 0.28, 4, 34);
  vignette(ctx, 0.75);
} });
P1.push({ a: 30.8, xf: 0.6, f(ctx, t, lt) {
  const fl = bulbFlicker(t);
  drawStationBG(ctx, t, { doorOpen: kf(lt, [[0, 0.1], [0.5, 1], [1.9, 1], [2.4, 0]]) });
  drawFigure(ctx, { who: 'her', x: 300, y: 560, h: 210, pose: 'sit', dir: 1, eyesClosed: 1, headDown: 0.6, t });
  const walking = lt < 5.6;
  drawFigure(ctx, { who: 'him', x: kf(lt, [[0.8, 1130], [5.6, 820]]), y: 615, h: 250, pose: walking && lt > 0.8 ? 'walk' : 'stand', phase: t * 5, dir: -1, bag: true, headDown: 0.7, t });
  drawStationLight(ctx, t, fl);
  vignette(ctx, 0.6);
} });
P1.push({ a: 37.5, xf: 0.5, f(ctx, t, lt) {
  const fl = bulbFlicker(t);
  stationCloseBG(ctx, t, 760, 330, 1.7, { fl });
  const lift = ss(44.6, 45.4, t), turn = ss(45.2, 46.4, t);
  const [sx, sy] = saccade(t, 7, 0.05);
  const breath = kf(t, [[39, 0], [40, 1.5], [41.5, 0]]);
  charLit(ctx, { who: 'him', x: 700 - turn * 30, y: 400, s: 1.45, t, breath, tilt: -0.03 * turn, gx: lerp(lerp(-0.1, -0.2, lift), -0.95, turn) + sx, gy: lerp(0.9, -0.05, lift) + sy, open: lerp(0.55, 1.0, lift), surprise: 0.35 * lift * (1 - ss(47, 49, t)), tired: 0.7 * (1 - lift * 0.5), sad: 0.25, blink: blinkAt(t, 2) },
    { amb: [[8, 12, 30], 0.32 + (1 - fl) * 0.25], keys: [[[255, 190, 120], 0.3 * fl, 520, 60, 600]] });
  vignette(ctx, 0.65);
} });
P1.push({ a: 49.5, xf: 1.0, f(ctx, t, lt) {
  const fl = bulbFlicker(t, 0.4);
  ctx.save(); camera(ctx, lerp(560, 380, easeIO(lt / 9)), lerp(380, 430, easeIO(lt / 9)), lerp(1.0, 1.45, easeIO(lt / 9)));
  drawStationBG(ctx, t);
  drawFigure(ctx, { who: 'her', x: 300, y: 560, h: 210, pose: 'sit', dir: 1, eyesClosed: 1, headDown: 0.15, mouth: mouthAt('her', t), t });
  drawStationLight(ctx, t, fl);
  ctx.restore();
  vignette(ctx, 0.6);
} });
P1.push({ a: 58.5, xf: 1.0, f(ctx, t, lt) {
  stationCloseBG(ctx, t, 300, 300, 2.0, { fl: 1 });
  const look = kf(t, [[65.5, 0], [66.3, 1], [69.8, 1], [70.8, 0]]);
  const m = mouthAt('her', t);
  charLit(ctx, { who: 'her', x: 640, y: 370, s: 1.5, t, tilt: Math.sin(t * 0.9) * 0.05, mouth: m * 0.85, round: 0.35, open: look * 0.6, gx: 0.3 * look, gy: -0.75 * look, sad: 0.45, smile: 0.05, blink: look > 0.5 ? blinkAt(t, 9) : 0, wind: 0.15 },
    { amb: [[10, 14, 34], 0.28], keys: [[[255, 190, 120], 0.28, 1000, 80, 700], [[120, 160, 255], 0.15, 200, 200, 500]] });
  vignette(ctx, 0.6);
} });
P1.push({ a: 72.5, xf: 0.8, f(ctx, t, lt) {
  const z = lerp(1.5, 1.72, easeIO(lt / 16));
  stationCloseBG(ctx, t, 780, 330, 1.8, { fl: 1 });
  const sad = kf(t, [[73.5, 0], [78, 0.8]]), surprise = kf(t, [[72.5, 0.5], [74.5, 0.5], [77, 0]]);
  const [sx, sy] = saccade(t, 11, 0.06);
  charLit(ctx, { who: 'him', x: 660, y: 395 + (z - 1.5) * 120, s: z, t, gx: -0.55 + sx, gy: -0.05 + sy, open: 1.0 - sad * 0.12, surprise, sad, tears: kf(t, [[74, 0], [80, 0.9]]), mouth: 0.12 * (1 - ss(76, 78, t)),
    drops: [{ p: (t - 82) / 2.4, side: 1 }, { p: (t - 85.2) / 2.6, side: -1 }], blink: blinkAt(t, 4, 5.5), tired: 0.3 },
    { amb: [[8, 12, 30], 0.3], keys: [[[255, 190, 120], 0.3, 420, 80, 650]] });
  vignette(ctx, 0.65);
} });
const MEM = [[88.5, 0], [91.8, 1], [95.2, 2], [97.8, 3], [101.4, 4], [103.4, 5], [110.5, -1]];
P1.push({ a: 88.5, xf: 1.2, f(ctx, t, lt) {
  const dark = ss(88.5, 108, t);
  stationCloseBG(ctx, t, 780, 330, 1.8, { fl: 1, dark: 0.3 + dark * 0.55 });
  stormClouds(ctx, t, { seed: 21, n: 40, y0: -100, y1: H + 100, col: [6, 2, 6], col2: [50, 10, 16], speed: 0.6, alpha: 0.25 + dark * 0.7 });
  for (let i = 0; i < MEM.length - 1; i++) {
    const [a, k] = MEM[i], b = MEM[i + 1][0];
    const al = fade(t, a, b + 0.3, 0.35, 0.45);
    if (al <= 0) continue;
    const cx = 360 + noise1(t * 0.3 + i) * 30, cy = 300 + noise1(t * 0.25 + i * 3) * 20;
    drawMemory(ctx, k, t - a, cx, cy, 210, al);
  }
  const sw = noise1(t * 1.3) * 0.15;
  const drops = []; for (let k = 0; k < 9; k++) drops.push({ p: (t - (88.8 + k * 2.4)) / 2.3, side: k % 2 ? -1 : 1 });
  const [sx, sy] = saccade(t, 13, 0.12);
  charLit(ctx, { who: 'him', x: 900, y: 400, s: 1.4, t, gx: -0.9 + sw + sx, gy: -0.1 + sy, sad: 0.95, angry: kf(t, [[96, 0], [110, 0.45]]), tears: 1, drops, blink: blinkAt(t, 6, 4), breath: 0.6, tilt: -0.04 },
    { amb: [[6, 6, 18], 0.35 + dark * 0.15], keys: [[[255, 80, 60], 0.32, 360, 300, 700]] });
  vignette(ctx, 0.75);
} });
const P1_BOLTS = [110.5, 116.2, 121.4, 127.5];
P1.push({ a: 110.5, xf: 0.4, f(ctx, t, lt) {
  const L = lightningSchedule(t, P1_BOLTS);
  drawMindSky(ctx, t, { flash: L.f, swirl: 0.6, cy: 380 });
  if (L.idx >= 0) lightningBolt(ctx, 200 + hash(L.idx) * 900, -20, 150 + hash(L.idx + 9) * 1000, 500, 100 + L.idx, L.f);
  demonShadow(ctx, 640, 360, 0.95, ss(122, 130, t) * 0.75, t, ss(126, 130, t));
  ctx.save(); shake(ctx, t, 2 + L.f * 6);
  const [sx, sy] = saccade(t, 17, 0.07);
  const m = mouthAt('him', t);
  charLit(ctx, { who: 'him', x: 640, y: 420, s: 1.32, t, gx: sx, gy: 0.05 + sy, angry: kf(t, [[110.5, 0.5], [113, 0.85]]), sad: 0.55, tears: 1, grit: 1, mouth: m * 0.6, breath: 1.2, wind: 0.6, blink: blinkAt(t, 8, 4.5),
    drops: [{ p: (t - 111) / 2.2, side: 1 }, { p: (t - 114.5) / 2.2, side: -1 }, { p: (t - 119) / 2.2, side: 1 }, { p: (t - 124) / 2.2, side: -1 }] },
    { amb: [[20, 6, 20], 0.38], keys: [[[255, 60, 40], 0.22, 640, 900, 700]], flash: L.f * 0.5 });
  ctx.restore();
  rainStreaks(ctx, t, 160, 1700, 0.25, 0.18 + lt * 0.006, 6, 30);
  vignette(ctx, 0.75, [10, 0, 0]);
} });
const P1_BOLTS2 = [131, 138.2, 143.4, 149.3];
P1.push({ a: 130.5, xf: 0.5, f(ctx, t, lt) {
  const L = lightningSchedule(t, P1_BOLTS2);
  ctx.save(); camera(ctx, 640, 420, lerp(1.0, 1.18, easeIO(lt / 11)));
  drawMindSky(ctx, t, { flash: L.f, swirl: 1 });
  demonShadow(ctx, 640, 330, 1.0, lerp(0.6, 0.9, lt / 11), t, 1);
  if (L.idx >= 0) lightningBolt(ctx, 300 + hash(L.idx + 3) * 700, -40, 250 + hash(L.idx + 7) * 800, 560, 300 + L.idx, L.f, 4);
  drawRock(ctx, 640, 540, 1);
  drawFigure(ctx, { who: 'him', x: 650, y: 542, h: 120, pose: 'stand', dir: 1, headDown: 0.3, t });
  ctx.restore();
  rainStreaks(ctx, t, 300, 1900, 0.35, 0.22, 7, 36);
  vignette(ctx, 0.8, [10, 0, 0]);
} });
P1.push({ a: 141.5, xf: 0.4, f(ctx, t, lt) {
  const L = lightningSchedule(t, P1_BOLTS2);
  drawMindSky(ctx, t, { flash: L.f, swirl: 1.2, cy: 300 });
  demonShadow(ctx, 640, 380, 1.2, 0.85, t, 1);
  ctx.save(); shake(ctx, t, 3 + L.f * 6);
  const red = kf(t, [[145, 0], [147.5, 0.65]]);
  const m = mouthAt('him', t);
  charLit(ctx, { who: 'him', x: 640, y: 440, s: 1.25, t, gx: 0, gy: 0.1, angry: 1, sad: 0.35, tears: 1, grit: 1, mouth: m * 0.5, wind: 1.2, breath: 1.4, horns: kf(t, [[141.5, 0.05], [150.5, 0.6]]), red, slit: red * 0.6, blink: red > 0.3 ? 0 : blinkAt(t, 3),
    drops: [{ p: (t - 142) / 2, side: 1, red: red > 0.3 }, { p: (t - 145.5) / 2, side: -1, red: true }] },
    { amb: [[24, 4, 14], 0.4], keys: [[[255, 50, 30], 0.3, 640, 900, 800]], flash: L.f * 0.5 });
  ctx.restore();
  rainStreaks(ctx, t, 240, 2000, 0.4, 0.2, 8, 36);
  vignette(ctx, 0.8, [15, 0, 0]);
} });
const P1_BOLTS3 = [155.0, 159.6, 163.6, 165.6, 166.4, 167.0, 167.3];
const P1_SONG_END_T = 167.65;
P1.push({ a: 150.5, xf: 0.25, f(ctx, t, lt) {
  const L = lightningSchedule(t, P1_BOLTS3, 0.4);
  drawMindSky(ctx, t, { flash: L.f, swirl: 1.6, speed: 1.4, cy: 250 });
  demonShadow(ctx, 640, 420, 1.5, 0.9, t, 1);
  if (L.idx >= 0) lightningBolt(ctx, hash(L.idx * 3) * W, -30, hash(L.idx * 5) * W, 420, 700 + L.idx, L.f, 5, [255, 200, 220]);
  ctx.save(); shake(ctx, t, 2 + lt * 0.5 + L.f * 8);
  const z = lerp(1.65, 1.95, easeIO(lt / 17));
  const red = kf(t, [[150.5, 0.65], [158, 1]]);
  charLit(ctx, { who: 'him', x: 640, y: 470 + (z - 1.65) * 80, s: z, t, gx: noise1(t * 0.7) * 0.1, gy: 0.05, angry: 1, sad: 0.25, tears: 0.8, grit: 1, wind: 1.4, breath: 1.6, horns: kf(t, [[150.5, 0.6], [160, 1]]), red, slit: red,
    drops: [{ p: (t - 152) / 1.8, side: 1, red: true }, { p: (t - 156) / 1.8, side: -1, red: true }, { p: (t - 160) / 1.8, side: 1, red: true }] },
    { amb: [[30, 4, 10], 0.45], keys: [[[255, 40, 20], 0.4, 640, 900, 800]], flash: L.f * 0.55 });
  ctx.restore();
  rainStreaks(ctx, t, 260, 2100, 0.45, 0.2, 9, 40);
  vignette(ctx, 0.85, [20, 0, 0]);
  if (t > P1_SONG_END_T) { ctx.fillStyle = rgba([255, 250, 255], 1); ctx.fillRect(0, 0, W, H); }
} });
P1.push({ a: 168.0, f(ctx, t, lt) {
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  if (t < 168.3) { ctx.fillStyle = rgba([255, 250, 255], 1 - (t - 168) / 0.3); ctx.fillRect(0, 0, W, H); }
  const a = fade(t, 168.6, 175, 1.2, 3);
  for (const sx of [-1, 1]) { glow(ctx, 640 + sx * 58, 380, 50, [255, 30, 10], 0.6 * a); ctx.fillStyle = rgba([255, 120, 80], a); ctx.beginPath(); ctx.ellipse(640 + sx * 58, 380, 14, 4, sx * 0.2, 0, 7); ctx.fill(); }
  rainStreaks(ctx, t, 120, 1300, 0.12, 0.06, 2, 26);
} });
P1.push({ a: 176.0, f(ctx, t, lt) {
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const a = fade(t, 176.5, 186, 1.5, 1.5);
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.font = 'italic 300 26px Inter, sans-serif'; ctx.fillStyle = 'rgba(190,190,205,0.9)'; ctx.fillText('to be continued', W / 2, H / 2 - 90); ctx.restore();
  titleCard(ctx, t, 'PART TWO', 'The Spark', a * ss(178, 180, t), { glow: [255, 230, 160] });
  glow(ctx, W / 2, H / 2 + 120, 30, [255, 240, 200], 0.8 * a * ss(180, 182, t) * (0.8 + 0.2 * Math.sin(t * 3)));
} });

let P2 = [];  // filled by scenes2.js

function renderFrame(t) {
  const ctx = document.getElementById('c').getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  runShots(ctx, t, window.PART === 'part2' ? P2 : P1);
  grain(ctx, t, 0.035);
  drawCaptions(ctx, t, CAPS);
}
