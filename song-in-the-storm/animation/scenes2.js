// ===================== PART 2 — The Spark =====================
const P2_THUNDER = [2.5, 9.6, 17.8, 25.3, 33, 47, 66, 76.2, 93];

function theLight(ctx, x, y, size, t, a = 1) {
  // tiny, impossibly bright point of light
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  glow(ctx, x, y, 140 * size, [255, 225, 160], 0.35 * a);
  glow(ctx, x, y, 50 * size, [255, 240, 210], 0.7 * a);
  ctx.translate(x, y); ctx.rotate(t * 0.15);
  for (let i = 0; i < 4; i++) {
    const L = (i % 2 ? 70 : 120) * size * (0.9 + 0.1 * Math.sin(t * 2 + i));
    const g = ctx.createLinearGradient(0, 0, L, 0); g.addColorStop(0, rgba([255, 250, 230], 0.8 * a)); g.addColorStop(1, rgba([255, 230, 180], 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, -1.5 * size); ctx.lineTo(L, 0); ctx.lineTo(0, 1.5 * size); ctx.fill();
    ctx.rotate(Math.PI / 2);
    const g2 = ctx.createLinearGradient(0, 0, -L, 0); g2.addColorStop(0, rgba([255, 250, 230], 0.8 * a)); g2.addColorStop(1, rgba([255, 230, 180], 0));
  }
  ctx.rotate(Math.PI / 4);
  for (let i = 0; i < 4; i++) { ctx.fillStyle = rgba([255, 240, 200], 0.25 * a); ctx.beginPath(); ctx.moveTo(0, -1); ctx.lineTo(40 * size, 0); ctx.lineTo(0, 1); ctx.fill(); ctx.rotate(Math.PI / 2); }
  ctx.restore();
  ctx.fillStyle = rgba([255, 255, 255], a); ctx.beginPath(); ctx.arc(x, y, 2.5 * size, 0, 7); ctx.fill();
}
function godRays(ctx, x, y, t, a, n = 14, len = 1400, col = [255, 220, 150]) {
  if (a <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(x, y);
  const r = rng(77);
  for (let i = 0; i < n; i++) {
    const ang = (i / n) * Math.PI * 2 + t * 0.04 + r() * 0.3, w = 0.03 + r() * 0.05, al = a * (0.12 + 0.12 * Math.sin(t * 0.8 + i * 1.7) ** 2);
    const g = ctx.createRadialGradient(0, 0, 0, 0, 0, len); g.addColorStop(0, rgba(col, al)); g.addColorStop(1, rgba(col, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, len, ang - w, ang + w); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}
function motes(ctx, t, a, seed = 5, n = 60, cx = W / 2, cy = H / 2, spread = 700) {
  if (a <= 0) return;
  const r = rng(seed);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const x = cx + (r() - .5) * spread * 2 + noise1(t * 0.3 + i) * 40, y = ((r() * H * 1.4 - t * (12 + r() * 20)) % (H * 1.4) + H * 1.4) % (H * 1.4) - H * 0.2;
    const tw = 0.5 + 0.5 * Math.sin(t * (1 + r() * 2) + i);
    ctx.fillStyle = rgba([255, 225, 160], a * tw * 0.8); ctx.beginPath(); ctx.arc(x, y, 1.2 + r() * 2, 0, 7); ctx.fill();
  }
  ctx.restore();
}
function embers(ctx, t, t0, ox, oy, s, n = 70) {
  const r = rng(91);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const st = t0 + r() * 6, side = r() > .5 ? 1 : -1, bx = ox + side * (60 + r() * 90) * s, by = oy - (130 + r() * 120) * s;
    const lt = t - st; if (lt < 0 || lt > 7) continue;
    const x = bx + noise1(i + lt * 0.6) * 60 * s + side * lt * 10, y = by - lt * (40 + r() * 50);
    const k = clamp(lt / 3), col = mixc([255, 90, 30], [255, 235, 180], k), a = (1 - lt / 7) * (0.6 + 0.4 * Math.sin(lt * 9 + i));
    ctx.fillStyle = rgba(col, a); ctx.beginPath(); ctx.arc(x, y, (1.5 + r() * 2.5) * s, 0, 7); ctx.fill();
  }
  ctx.restore();
}
function cuppedHands(ctx, x, y, s, skin) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  for (const sx of [-1, 1]) {
    ctx.fillStyle = rgba(shade(skin, 0.95)); ctx.strokeStyle = rgba(shade(skin, 0.45)); ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(sx * 8, -10); ctx.bezierCurveTo(sx * 70, -30, sx * 120, 0, sx * 130, 40); ctx.lineTo(sx * 150, 160); ctx.lineTo(sx * 40, 160); ctx.bezierCurveTo(sx * 20, 80, sx * 5, 30, sx * 8, -10); ctx.fill(); ctx.stroke();
    ctx.strokeStyle = rgba(shade(skin, 0.7), 0.6); ctx.lineWidth = 2;
    for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.moveTo(sx * (30 + k * 25), -18 + k * 2); ctx.quadraticCurveTo(sx * (40 + k * 28), 10, sx * (50 + k * 28), 30); ctx.stroke(); }
  }
  ctx.restore();
}

P2.push({ a: 0, f(ctx, t) {
  const L = lightningSchedule(t, P2_THUNDER);
  ctx.fillStyle = '#05030a'; ctx.fillRect(0, 0, W, H);
  stormClouds(ctx, t, { seed: 4, n: 30, col: [14, 8, 18], col2: [40, 16, 30], alpha: 0.5, flash: L.f * 0.6 });
  rainStreaks(ctx, t, 160, 1600, 0.3, 0.1, 2, 30);
  titleCard(ctx, t, 'THE SONG IN THE STORM', 'Part Two — The Spark', fade(t, 1.2, 8.8, 1.8, 1.2), { glow: [255, 220, 160] });
} });
P2.push({ a: 8.6, xf: 1.0, f(ctx, t, lt) {
  const L = lightningSchedule(t, P2_THUNDER);
  ctx.save(); camera(ctx, 640, 420, lerp(1.0, 1.15, easeIO(lt / 11)));
  drawMindSky(ctx, t, { flash: L.f, swirl: 1 });
  demonShadow(ctx, 640, 330, 1.0, 0.85, t, 1);
  if (L.idx >= 0) lightningBolt(ctx, 300 + hash(L.idx + 3) * 700, -40, 250 + hash(L.idx + 7) * 800, 560, 900 + L.idx, L.f, 4);
  drawRock(ctx, 640, 540, 1);
  drawFigure(ctx, { who: 'him', x: 650, y: 542, h: 120, pose: 'stand', dir: 1, headDown: 0.1, horns: 1, red: 1, t });
  ctx.restore();
  rainStreaks(ctx, t, 300, 1900, 0.35, 0.22, 7, 36);
  vignette(ctx, 0.8, [10, 0, 0]);
} });
P2.push({ a: 19.5, xf: 0.4, f(ctx, t, lt) {
  const L = lightningSchedule(t, P2_THUNDER);
  drawMindSky(ctx, t, { flash: L.f, swirl: 1.4, cy: 260 });
  demonShadow(ctx, 640, 420, 1.4, 0.85, t, 1);
  // memories flicker around him with the echoes
  for (let i = 0; i < 3; i++) { const a = fade(t, 27.3 + i * 1.15, 29.2 + i * 1.15, 0.2, 0.5) * 0.7; drawMemory(ctx, [0, 4, 2][i], t - 27, [230, 1050, 260][i], [220, 260, 520][i], 140, a); }
  ctx.save(); shake(ctx, t, 2 + L.f * 6);
  const [sx, sy] = saccade(t, 21, 0.1);
  charLit(ctx, { who: 'him', x: 640, y: 470, s: 1.7, t, gx: sx, gy: 0.05 + sy, angry: 0.9, sad: kf(t, [[19.5, 0.3], [24, 0.6]]), tears: 0.8, grit: 1, wind: 1.2, breath: 1.4, horns: 1, red: 1, slit: 1,
    drops: [{ p: (t - 22) / 2, side: 1, red: true }, { p: (t - 26) / 2, side: -1, red: true }] },
    { amb: [[28, 4, 12], 0.42], keys: [[[255, 40, 20], 0.35, 640, 900, 800]], flash: L.f * 0.5 });
  ctx.restore();
  rainStreaks(ctx, t, 240, 2000, 0.4, 0.2, 8, 36);
  vignette(ctx, 0.85, [20, 0, 0]);
} });
P2.push({ a: 31, xf: 0.5, f(ctx, t, lt) {
  const L = lightningSchedule(t, P2_THUNDER);
  const dim = ss(37.5, 40.3, t);
  drawMindSky(ctx, t, { flash: L.f, swirl: 1.2, cy: 300 });
  demonShadow(ctx, 640, 380, 1.25, 0.8, t, 1 - dim);
  ctx.save(); shake(ctx, t, 1.5 + L.f * 5);
  const down = ss(31.5, 35, t);
  charLit(ctx, { who: 'him', x: 640, y: 450 + down * 20, s: 1.3, t, gx: 0, gy: lerp(0.1, 0.9, down), open: lerp(1, 0.5, down), angry: lerp(0.8, 0.2, down), sad: lerp(0.5, 0.9, down), tears: 1, wind: 1, breath: 1.5, tilt: down * 0.06, horns: 1, red: 1, slit: 1,
    drops: [{ p: (t - 33) / 2.2, side: 1, red: true }, { p: (t - 35.5) / 2.2, side: -1, red: true }] },
    { amb: [[24, 4, 14], 0.42], keys: [[[255, 40, 20], 0.3, 640, 900, 800]], flash: L.f * 0.5 });
  ctx.restore();
  rainStreaks(ctx, t, 240, 2000, 0.4, 0.2, 8, 36);
  vignette(ctx, 0.85, [15, 0, 0]);
  ctx.fillStyle = rgba([0, 0, 0], dim * 0.85); ctx.fillRect(0, 0, W, H);
} });
// the spark appears
P2.push({ a: 40.3, xf: 0.3, f(ctx, t, lt) {
  const L = lightningSchedule(t, P2_THUNDER);
  ctx.save(); camera(ctx, lerp(640, 560, easeIO(lt / 10.7)), 380, lerp(1.0, 1.12, easeIO(lt / 10.7)));
  drawMindSky(ctx, t, { flash: L.f * 0.6, swirl: 0.4, speed: 0.5 });
  ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(-200, -200, W + 400, H + 400);
  if (L.idx >= 0) lightningBolt(ctx, 1100, -40, 1180, 380, 1300 + L.idx, L.f * 0.7, 3);
  drawRock(ctx, 860, 560, 0.8);
  const turn = ss(43, 46, t);
  drawFigure(ctx, { who: 'him', x: 865, y: 562, h: 105, pose: 'stand', dir: turn > 0.5 ? -1 : 1, headDown: 0.4 * (1 - turn), horns: 1, red: 1 - turn * 0.3, t });
  theLight(ctx, 380, 300, 0.5 + 0.5 * ss(40.3, 44, t), t, ss(40.0, 40.6, t));
  ctx.restore();
  rainStreaks(ctx, t, 200, 1500, 0.3, 0.12, 7, 32);
  vignette(ctx, 0.85);
} });
P2.push({ a: 51, xf: 0.8, f(ctx, t, lt) {
  const L = lightningSchedule(t, P2_THUNDER);
  drawMindSky(ctx, t, { flash: L.f * 0.4, swirl: 0.4, speed: 0.4, calm: ss(51, 64, t) * 0.4 });
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(0, 0, W, H);
  theLight(ctx, 130, 150, 0.9, t, 0.9);
  const red = kf(t, [[53, 1], [64, 0.35]]);
  const [sx, sy] = saccade(t, 31, 0.04);
  charLit(ctx, { who: 'him', x: 700, y: 420, s: 1.55, t, gx: -0.75 + sx, gy: -0.45 + sy, open: kf(t, [[51, 0.75], [54, 1.05]]), surprise: kf(t, [[52, 0], [54, 0.6], [62, 0.2]]), angry: kf(t, [[51, 0.6], [56, 0]]), sad: kf(t, [[54, 0.2], [62, 0.6]]), tears: 0.9, mouth: kf(t, [[53, 0], [54.5, 0.12], [59, 0.05]]),
    horns: 1, red, slit: kf(t, [[52, 1], [58, 0]]), spark: 1, wind: 0.5, blink: t > 58 ? blinkAt(t, 5, 4) : 0, tilt: -0.03,
    drops: [{ p: (t - 57) / 2.6, side: -1, red: red > 0.6 }, { p: (t - 61) / 2.6, side: 1 }] },
    { amb: [[20, 6, 18], 0.35], keys: [[[255, 230, 170], 0.32, 130, 150, 900], [[255, 40, 20], 0.18 * red, 640, 900, 700]] });
  vignette(ctx, 0.75);
} });
P2.push({ a: 64, xf: 0.8, f(ctx, t, lt) {
  const L = lightningSchedule(t, P2_THUNDER, 0.6);
  drawMindSky(ctx, t, { flash: L.f * 0.5, swirl: 0.8, speed: 1.2, cx: 640, cy: 360 });
  ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(0, 0, W, H);
  if (L.idx >= 0) { lightningBolt(ctx, 700, -40, 690, 330, 1600 + L.idx, L.f, 5); lightningBolt(ctx, 560, -40, 600, 340, 1700 + L.idx, L.f * 0.7, 3); }
  // calm pocket around the light
  radial(ctx, 640, 360, 260, [40, 30, 60], 0.35);
  theLight(ctx, 640, 360, lerp(1.4, 2.0, lt / 7), t, 1);
  rainStreaks(ctx, t, 220, 1800, 0.25, 0.14, 11, 34);
  motes(ctx, t, 0.4, 3, 30, 640, 360, 300);
  vignette(ctx, 0.8);
} });
// cupped hands, horns crumble
P2.push({ a: 71, xf: 0.8, f(ctx, t, lt) {
  const L = lightningSchedule(t, P2_THUNDER);
  drawMindSky(ctx, t, { flash: L.f * 0.45, swirl: 0.5, speed: 0.7, calm: 0.3 + ss(80, 86, t) * 0.4 });
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(0, 0, W, H);
  if (L.idx >= 0) lightningBolt(ctx, 1000, -40, 1080, 720, 1900 + L.idx, L.f, 4);
  const red = kf(t, [[71, 0.35], [79, 0]]);
  const crumble = ss(79, 85, t);
  const lx = 640, ly = 600;
  const softness = ss(80, 86, t);
  const z = lerp(1.3, 1.42, lt / 15);
  charLit(ctx, { who: 'him', x: 640, y: 400, s: z, t, gx: 0, gy: kf(t, [[71, 0.75], [82, 0.75], [84, 0.1]]), open: kf(t, [[71, 0.85], [82, 0.85], [84, 1]]), sad: lerp(0.6, 0.35, softness), angry: 0, smile: 0.3 * softness, tears: 1,
    horns: 1, red, cracks: kf(t, [[73.5, 0], [79, 1]]), crumble, wind: 0.3, blink: blinkAt(t, 12, 4.2),
    drops: [{ p: (t - 74) / 2.6, side: 1 }, { p: (t - 78) / 2.6, side: -1 }, { p: (t - 83) / 2.6, side: 1 }] },
    { amb: [[18, 10, 30], 0.3], keys: [[[255, 220, 150], 0.45, lx, ly + 40, 650]], flash: L.f * 0.25 });
  embers(ctx, t, 79, 640, 400, z);
  cuppedHands(ctx, 640, 610, 1.1, LOOK.him.skin);
  ctx.save(); ctx.globalCompositeOperation = 'source-atop'; ctx.restore();
  theLight(ctx, lx, ly - 10 + Math.sin(t * 1.2) * 4, 1.3, t, 1);
  motes(ctx, t, softness * 0.6, 8, 50);
  vignette(ctx, 0.7);
} });
// light enters his chest: transformation
P2.push({ a: 86, xf: 1.0, f(ctx, t, lt) {
  const calm = 0.6 + ss(88, 98, t) * 0.4;
  ctx.save(); camera(ctx, 650, lerp(420, 400, lt / 14), lerp(1.0, 1.35, easeIO(lt / 14)));
  drawMindSky(ctx, t, { swirl: 0.2, speed: 0.4, calm });
  // clouds part: light from above
  glow(ctx, 650, 0, 700, [255, 220, 170], 0.25 * ss(89, 97, t));
  godRays(ctx, 650, -50, t, ss(90, 97, t) * 0.7, 10, 1200, [255, 230, 180]);
  drawRock(ctx, 640, 540, 1, [16, 12, 20]);
  const tr = ss(89, 96.5, t);
  const into = ss(86.5, 89, t);
  godRays(ctx, 650, 455, t, ss(88.5, 92, t), 16, 1300);
  drawFigure(ctx, { who: 'him', x: 650, y: 542, h: 120, pose: 'stand', dir: 1, headDown: lerp(0.3, 0, tr), christ: tr, halo: ss(93, 97, t), glowChest: 0.6 * ss(88.5, 90, t), t, horns: 0 });
  theLight(ctx, lerp(650, 652, into), lerp(500, 455, into), lerp(0.8, 0.5, into), t, 1 - ss(88.6, 89.3, t) * 0.6);
  motes(ctx, t, ss(88, 92, t), 12, 90, 650, 400, 600);
  ctx.restore();
  const wf = ss(98.3, 100.2, t);
  ctx.fillStyle = rgba([255, 244, 225], wf); ctx.fillRect(0, 0, W, H);
  vignette(ctx, 0.6 * (1 - wf));
} });
// back in the station
P2.push({ a: 100, xf: 0.01, f(ctx, t, lt) {
  drawStationBG(ctx, t);
  const eyes = t > 104.5 ? 0 : 1;
  drawFigure(ctx, { who: 'her', x: 300, y: 560, h: 210, pose: 'sit', dir: 1, eyesClosed: eyes, headDown: lerp(0.15, 0, ss(104, 105, t)), mouth: mouthAt('her', t), t });
  const walk = t < 106.5;
  drawFigure(ctx, { who: 'him', x: kf(t, [[100.4, 980], [106.5, 450]]), y: 600, h: 250, pose: walk && t > 100.4 ? 'walk' : 'stand', kneel: ss(106.6, 108.4, t), phase: t * 4.4, dir: -1, christ: 1, halo: 0.6, glowChest: 0.35, t });
  drawStationLight(ctx, t, 1, { warm: 0.6 });
  ctx.fillStyle = rgba([255, 244, 225], 1 - ss(100, 101.6, t)); ctx.fillRect(0, 0, W, H);
  vignette(ctx, 0.55);
} });
const warmLight = { amb: [[30, 18, 10], 0.22], keys: [[[255, 200, 130], 0.32, 900, 120, 800]] };
function herClose(ctx, t, o) {
  stationCloseBG(ctx, t, 300, 300, 2.0, { fl: 1 });
  glow(ctx, 1100, 300, 500, [255, 210, 140], 0.25);
  charLit(ctx, Object.assign({ who: 'her', x: 600, y: 375, s: 1.5, t, wind: 0.1, blink: blinkAt(t, 14, 3.4) }, o), { amb: [[24, 14, 20], 0.2], keys: [[[255, 205, 140], 0.38, 1150, 260, 900]] });
  vignette(ctx, 0.55);
}
function christClose(ctx, t, o) {
  stationCloseBG(ctx, t, 820, 320, 1.8, { fl: 1 });
  charLit(ctx, Object.assign({ who: 'him', x: 680, y: 400, s: 1.45, t, christ: 1, halo: 0.55, tears: 0.6, smile: 0.35, sad: 0.3, blink: blinkAt(t, 15, 4.2) }, o), { amb: [[30, 18, 10], 0.18], keys: [[[255, 215, 150], 0.35, 680, 300, 700]] });
  vignette(ctx, 0.55);
}
P2.push({ a: 110.5, xf: 0.5, f(ctx, t) {
  const away = kf(t, [[111, 0], [112.5, 1], [114.5, 1], [115.5, 0]]);
  herClose(ctx, t, { gx: lerp(0.65, -0.2, away), gy: lerp(0.05, 0.6, away), open: 0.95, sad: 0.75, surprise: kf(t, [[110.5, 0.4], [112, 0]]), mouth: mouthAt('her', t) * 0.9, tears: 0.2 });
} });
P2.push({ a: 117, xf: 0.4, f(ctx, t) {
  const [sx, sy] = saccade(t, 41, 0.04);
  christClose(ctx, t, { gx: -0.55 + sx, gy: 0.15 + sy, mouth: mouthAt('him', t) * 0.85, tilt: 0.03 });
} });
P2.push({ a: 128.5, xf: 0.4, f(ctx, t) {
  const up = ss(131.5, 132.5, t);
  herClose(ctx, t, { gx: lerp(0.1, 0.6, up), gy: lerp(0.55, 0.05, up), open: 0.9, sad: 0.9, tears: kf(t, [[128.5, 0.3], [132, 0.9]]), mouth: mouthAt('her', t) * 0.9, drops: [{ p: (t - 132.6) / 2.4, side: 1 }] });
} });
P2.push({ a: 133.5, xf: 0.4, f(ctx, t) {
  const [sx, sy] = saccade(t, 43, 0.04);
  christClose(ctx, t, { gx: -0.55 + sx, gy: 0.2 + sy, mouth: mouthAt('him', t) * 0.85, sad: 0.55, smile: 0.2, tears: 0.85, drops: [{ p: (t - 135.5) / 2.6, side: -1 }] });
} });
// two-shot: coat and the paper bag
P2.push({ a: 138, xf: 0.5, f(ctx, t, lt) {
  ctx.save(); camera(ctx, 380, 450, 2.05);
  drawStationBG(ctx, t);
  const mant = ss(138.6, 140.6, t), give = ss(141.3, 143.4, t);
  const her = { who: 'her', x: 300, y: 560, h: 210, pose: 'sit', dir: 1, eyesClosed: t > 146 && t < 146.2 ? 1 : 0, mantle: mant, mouth: mouthAt('her', t), t };
  drawFigure(ctx, her);
  // the bag lands in her lap
  if (give > 0) { const bx = lerp(392, 345, give), by = lerp(440, 468, give); ctx.fillStyle = 'rgb(176,140,96)'; ctx.fillRect(bx - 15, by, 30, 36); ctx.fillStyle = 'rgba(0,0,0,0.2)'; ctx.fillRect(bx - 15, by, 30, 6); glow(ctx, bx, by + 10, 30, [255, 200, 120], 0.25 * give); }
  const reach = sh => {
    if (t < 141.3) { const k = Math.sin(Math.PI * clamp((t - 138.3) / 2.6)); return [sh, [sh[0] - 30, sh[1] - 10 - 25 * k], [sh[0] - 55 - 30 * k, sh[1] - 15 - 45 * k]]; }
    const k = Math.sin(Math.PI * clamp((t - 141.1) / 2.6)); return [sh, [sh[0] - 25, sh[1] + 30], [sh[0] - 40 - 30 * k, sh[1] + 50 - 10 * k]];
  };
  drawFigure(ctx, { who: 'him', x: 450, y: 600, h: 250, pose: 'stand', kneel: 1, dir: -1, christ: 1, halo: 0.6, glowChest: 0.3, mouth: mouthAt('him', t), arm: reach, bag: t < 141.3, t });
  drawStationLight(ctx, t, 1, { warm: 0.6 });
  ctx.restore();
  vignette(ctx, 0.55);
} });
P2.push({ a: 146, xf: 0.5, f(ctx, t) {
  const closeHappy = ss(149, 150, t);
  herClose(ctx, t, { gx: 0.6 * (1 - closeHappy), gy: 0.05, open: 0.95, sad: lerp(0.6, 0.25, ss(146, 149, t)), smile: kf(t, [[146, 0.1], [148, 0.55]]), tears: 1, mantle: 1, closedHappy: closeHappy, mouth: mouthAt('her', t) * 0.8,
    drops: [{ p: (t - 146.3) / 2.2, side: 1 }, { p: (t - 147.6) / 2.4, side: -1 }] });
} });
// he leaves, she sings again
P2.push({ a: 151, xf: 0.6, f(ctx, t, lt) {
  drawStationBG(ctx, t, { doorOpen: kf(t, [[156.6, 0], [157.4, 1]]) });
  drawFigure(ctx, { who: 'her', x: 300, y: 560, h: 210, pose: 'sit', dir: 1, eyesClosed: 1, mantle: 1, mouth: mouthAt('her', t), t });
  const up = ss(151, 152.4, t), walk = t > 152.4;
  drawFigure(ctx, { who: 'him', x: kf(t, [[152.4, 450], [157.6, 1090]]), y: 600, h: 250, pose: walk && t < 157.6 ? 'walk' : 'stand', kneel: 1 - up, phase: t * 4.4, dir: 1, christ: 1, halo: 0.6, glowChest: 0.35, t });
  drawStationLight(ctx, t, 1, { warm: 0.6 });
  vignette(ctx, 0.55);
} });
P2.push({ a: 158.5, xf: 0.5, f(ctx, t, lt) {
  // at the door, looking back
  ctx.fillStyle = '#060912'; ctx.fillRect(0, 0, W, H);
  const r = rng(51);
  for (let i = 0; i < 30; i++) { const x = r() * W, y = 100 + r() * 400, rr = 10 + r() * 30; const gr = ctx.createRadialGradient(x, y, 0, x, y, rr); gr.addColorStop(0, 'rgba(255,190,110,0.2)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = gr; ctx.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
  rainStreaks(ctx, t, 160, 1300, 0.08, 0.2, 13, 26);
  ctx.fillStyle = '#2b1f16'; ctx.fillRect(0, 0, 130, H);
  const look = kf(t, [[158.8, 0], [159.8, 1], [161.6, 1], [162.3, 0.4]]);
  charLit(ctx, { who: 'him', x: 700, y: 400, s: 1.45, t, christ: 1, halo: 0.45, gx: lerp(0.3, -0.9, look), gy: 0.05, tilt: -0.05 * look, smile: 0.5 * look, tears: 0.7, sad: 0.2, blink: blinkAt(t, 16, 3.5) },
    { amb: [[10, 16, 40], 0.3], keys: [[[255, 200, 130], 0.45 * look + 0.15, 0, 380, 800]] });
  vignette(ctx, 0.6);
} });
P2.push({ a: 162.5, xf: 0.8, f(ctx, t, lt) {
  stationCloseBG(ctx, t, 300, 300, 2.0, { fl: 1 });
  glow(ctx, 640, 400, 600, [255, 210, 150], 0.18 + 0.05 * Math.sin(t));
  const m = mouthAt('her', t);
  charLit(ctx, { who: 'her', x: 640, y: 372, s: lerp(1.5, 1.62, lt / 13.5), t, tilt: Math.sin(t * 0.9) * 0.05, mouth: m * 0.85, round: 0.3, open: 0, closedHappy: 0.6, sad: 0.15, smile: 0.25, tears: 0.6, mantle: 1, wind: 0.1 },
    { amb: [[24, 14, 20], 0.15], keys: [[[255, 210, 150], 0.38, 640, 200, 800]] });
  motes(ctx, t, 0.4, 19, 25, 640, 360, 500);
  vignette(ctx, 0.55);
} });
// exterior: he walks, the city wakes up
const STREET_B = (() => { const r = rng(808), out = []; let x = -200; while (x < 4200) { const w = 160 + r() * 200, h = 260 + r() * 300; const wins = []; for (let wy = 600 - h + 30; wy < 560; wy += 40) for (let wx = x + 20; wx < x + w - 30; wx += 38) wins.push([wx, wy, r()]); out.push({ x, w, h, col: [16 + r() * 10, 16 + r() * 8, 26 + r() * 10], wins }); x += w + 6; } return out; })();
P2.push({ a: 176, xf: 1.0, f(ctx, t, lt) {
  const hx = 300 + (t - 174) * 105; // world x of him
  const camX = hx - 540;
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#060814'); g.addColorStop(1, '#1c1a2a'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(-camX * 0.3, 0); // far skyline parallax
  ctx.fillStyle = '#0f1120'; const r2 = rng(5); for (let x = -200; x < 3000; x += 90) { const h = 150 + r2() * 260; ctx.fillRect(x, 520 - h, 86, h); }
  ctx.restore();
  ctx.save(); ctx.translate(-camX, 0);
  for (const b of STREET_B) {
    if (b.x + b.w < camX - 50 || b.x > camX + W + 50) continue;
    ctx.fillStyle = rgba(b.col); ctx.fillRect(b.x, 600 - b.h, b.w, b.h);
    for (const [wx, wy, k] of b.wins) {
      const lit = k < 0.12 ? 1 : ss(wx - 60 + k * 300, wx + 120 + k * 300, hx);
      ctx.fillStyle = rgba([30, 30, 44]); ctx.fillRect(wx, wy, 20, 24);
      if (lit > 0) { ctx.fillStyle = rgba([255, 200 + k * 30, 120 + k * 40], lit * 0.85); ctx.fillRect(wx, wy, 20, 24); if (k > 0.3) glow(ctx, wx + 10, wy + 12, 34, [255, 190, 110], lit * 0.18); }
    }
  }
  ctx.fillStyle = '#0c0d14'; ctx.fillRect(camX - 50, 600, W + 100, 140);
  ctx.fillStyle = '#1d1e28'; ctx.fillRect(camX - 50, 598, W + 100, 6);
  // someone huddled in a doorway is given an umbrella and a hand
  const px = 1500 + 400;
  ctx.fillStyle = '#2a2530'; ctx.beginPath(); ctx.ellipse(px, 575, 30, 32, 0, 0, 7); ctx.fill(); ctx.beginPath(); ctx.arc(px - 4, 538 - ss(hx - 150, hx, px) * 0 , 15, 0, 7); ctx.fill();
  const giver = clamp((hx - px + 50) / 300);
  const gx2 = lerp(px + 420, px + 60, easeIO(giver));
  drawPedestrian(ctx, gx2, 604, 170, giver < 1 ? t * 5 : 0, -1, [44, 40, 52], true);
  if (giver >= 1) { ctx.fillStyle = 'rgba(255,200,130,0.12)'; ctx.beginPath(); ctx.ellipse(px + 30, 560, 90, 50, 0, 0, 7); ctx.fill(); }
  // lamp posts
  for (let lx = 200; lx < 4200; lx += 520) { ctx.fillStyle = '#0a0a10'; ctx.fillRect(lx - 3, 360, 6, 240); glow(ctx, lx + 20, 365, 110, [255, 190, 110], 0.4); }
  drawFigure(ctx, { who: 'him', x: hx, y: 602, h: 190, pose: 'walk', phase: t * 4.4, dir: 1, christ: 1, halo: 0.5, glowChest: 0.55, t });
  ctx.restore();
  rainStreaks(ctx, t, 150, 1300, 0.1, 0.14 * (1 - ss(185, 193, t)), 15, 26);
  vignette(ctx, 0.65);
} });
P2.push({ a: 193, xf: 1.5, f(ctx, t, lt) {
  const camY = 960 * (1 - easeIO(clamp(lt / 13)));
  ctx.drawImage(CITY, 0, -camY);
  // stars as the clouds clear
  const sa = ss(196, 206, t);
  const r = rng(99);
  for (let i = 0; i < 160; i++) { const x = r() * W, y = r() * 1100 - camY; if (y < -5 || y > H) continue; ctx.fillStyle = rgba([255, 250, 235], sa * (0.3 + 0.7 * r()) * (0.7 + 0.3 * Math.sin(t * 2 + i))); ctx.fillRect(x, y, 1.6, 1.6); }
  stormClouds(ctx, t, { seed: 61, n: 26, y0: -200, y1: 600 - camY * 0.5, col: [20, 22, 36], col2: [40, 40, 60], alpha: 0.7 * (1 - ss(194, 206, t)), speed: 1.5 });
  // windows across the city wake up in a wave from where he walked
  const ox = 640, oy = CITY_GROUND - 20;
  for (let i = 0; i < CITY_DARK.length; i++) {
    const [wx, wy, ws] = CITY_DARK[i];
    const d = Math.hypot(wx - ox, (wy - oy) * 1.4);
    const k = hash(i * 1.37);
    if (k > 0.55) continue;
    const lit = ss(d / 70 + k * 3, d / 70 + k * 3 + 1.0, lt);
    if (lit <= 0) continue;
    const y = wy - camY; if (y < -10 || y > H + 10) continue;
    ctx.fillStyle = rgba([255, 205 + k * 40, 130 + k * 60], lit * (0.6 + 0.3 * k)); ctx.fillRect(wx - ws / 2, y - ws * 0.65, ws, ws * 1.3);
  }
  const gy = CITY_GROUND - camY;
  glow(ctx, 640, gy - 20, 60, [255, 225, 160], 0.6 * (1 - ss(204, 210, t)));
  vignette(ctx, 0.6);
  // closing words
  const a1 = fade(t, 207.5, 214.5, 1.5, 1.2), a2 = fade(t, 214.6, 221.5, 1.5, 1.8);
  ctx.save(); ctx.textAlign = 'center'; ctx.font = 'italic 400 40px "Liberation Serif", "DejaVu Serif", serif';
  ctx.shadowColor = 'rgba(255,210,150,0.6)'; ctx.shadowBlur = 20;
  ctx.fillStyle = rgba([255, 244, 225], a1); ctx.fillText('Something sacred is still here.', W / 2, H / 2 - 40);
  ctx.fillStyle = rgba([255, 244, 225], a2); ctx.fillText('It cannot be put out.', W / 2, H / 2 - 40);
  ctx.restore();
  ctx.fillStyle = rgba([0, 0, 0], ss(219.5, 222, t)); ctx.fillRect(0, 0, W, H);
} });
