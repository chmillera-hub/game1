// Every shot of the film as a function draw(ctx, p) on the 720x1280 frame.
// p: { t (film time), lt (time in shot), u (0..1 shot progress), seg, params, song, actors }
'use strict';
const path = require('path');
const LW = path.join(__dirname, '../../../the-last-witness/render/lib');
const U = require(path.join(LW, 'util'));
const FX = require(path.join(LW, 'fx'));
const R = require(path.join(LW, 'rig'));
const { exprParams } = require(path.join(LW, 'expr'));
const CAST = require('./cast');
const { rgba, mix, shade, lerp, clamp, smooth, easeInOut, TAU } = U;
const W = 720, H = 1280;

// ---------------------------------------------------------------- shared helpers
function grad(ctx, y0, y1, stops) {
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  stops.forEach(([o, c]) => g.addColorStop(o, typeof c === 'string' ? c : rgba(c)));
  return g;
}
function overcastSky(ctx, h0, t, dark = 0) {
  ctx.fillStyle = grad(ctx, 0, h0, [[0, mix([118, 128, 140], [40, 44, 56], dark)], [1, mix([196, 198, 196], [90, 88, 92], dark)]]);
  ctx.fillRect(0, 0, W, h0);
  // slow cloud bands
  for (let i = 0; i < 5; i++) {
    const y = 60 + i * h0 * 0.17, x = ((t * (4 + i) + i * 220) % (W + 600)) - 300;
    FX.glow(ctx, x, y, 260 + i * 30, mix([150, 156, 164], [60, 62, 74], dark), 0.25, false);
  }
}
function plain(ctx, hy, t, speed = 0) {
  ctx.fillStyle = grad(ctx, hy, H, [[0, [150, 140, 116]], [1, [96, 88, 72]]]);
  ctx.fillRect(0, hy, W, H - hy);
  // distant hills
  ctx.fillStyle = rgba([132, 132, 128]);
  ctx.beginPath(); ctx.moveTo(0, hy);
  for (let x = 0; x <= W; x += 40) ctx.lineTo(x, hy - 18 - 14 * Math.sin(x * 0.012) - 8 * Math.sin(x * 0.031));
  ctx.lineTo(W, hy); ctx.fill();
  // dry grass tufts, static
  const rnd = U.rng(4);
  ctx.strokeStyle = rgba([110, 100, 76], 0.5); ctx.lineWidth = 1.5;
  for (let i = 0; i < 40; i++) { const x = rnd() * W, y = hy + 20 + rnd() * (H - hy); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 3, y - 6 - rnd() * 6); ctx.stroke(); }
}
function poles(ctx, hy, t, speed, y0 = 0) {
  // telegraph poles sliding past (parallax), leaning, wires sagging
  const gap = 260, off = (t * speed) % gap;
  ctx.strokeStyle = rgba([60, 56, 52]); ctx.lineWidth = 6;
  for (let x = -off - gap; x < W + gap; x += gap) {
    ctx.beginPath(); ctx.moveTo(x, hy + 30 + y0); ctx.lineTo(x + 4, hy - 170 + y0); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x - 20, hy - 150 + y0); ctx.lineTo(x + 26, hy - 152 + y0); ctx.stroke();
  }
  ctx.strokeStyle = rgba([60, 56, 52], 0.5); ctx.lineWidth = 1.5;
  for (let x = -off - gap; x < W + gap; x += gap) { ctx.beginPath(); ctx.moveTo(x - 20, hy - 150 + y0); ctx.quadraticCurveTo(x + gap / 2, hy - 120 + y0, x + gap - 20, hy - 150 + y0); ctx.stroke(); }
}
function dust(ctx, t, n = 24, col = [200, 190, 170], a = 0.35) {
  const rnd = U.rng(9);
  for (let i = 0; i < n; i++) {
    const x = ((rnd() * W + t * (20 + rnd() * 30)) % (W + 40)) - 20, y = rnd() * H + Math.sin(t + i) * 12;
    ctx.fillStyle = rgba(col, a * rnd()); ctx.beginPath(); ctx.arc(x, y, 1 + rnd() * 2, 0, TAU); ctx.fill();
  }
}
function push(ctx, u, amt = 0.08, cx = W / 2, cy = H / 2) {
  const z = 1 + amt * easeInOut(u);
  ctx.translate(cx, cy); ctx.scale(z, z); ctx.translate(-cx, -cy);
}

// ---------------------------------------------------------------- the bus
const BUS = [206, 152, 48], RUST = [120, 72, 40], GLASS = [52, 64, 72];
function wheel(ctx, x, y, r, ang, opts = {}) {
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = rgba([28, 28, 30]); ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();
  ctx.strokeStyle = rgba([60, 58, 56]); ctx.lineWidth = r * 0.06; ctx.beginPath(); ctx.arc(0, 0, r * 0.82, 0, TAU); ctx.stroke();
  const hg = ctx.createRadialGradient(-r * 0.15, -r * 0.15, 0, 0, 0, r * 0.6);
  hg.addColorStop(0, rgba([196, 196, 190])); hg.addColorStop(1, rgba([110, 108, 104]));
  ctx.fillStyle = hg; ctx.beginPath(); ctx.arc(0, 0, r * 0.58, 0, TAU); ctx.fill();
  ctx.rotate(ang);
  ctx.strokeStyle = rgba([80, 78, 74]); ctx.lineWidth = r * 0.07;
  for (let i = 0; i < 6; i++) { ctx.rotate(TAU / 6); ctx.beginPath(); ctx.moveTo(r * 0.12, 0); ctx.lineTo(r * 0.5, 0); ctx.stroke(); }
  ctx.fillStyle = rgba([60, 58, 56]);
  for (let i = 0; i < 8; i++) { const a = i * TAU / 8; ctx.beginPath(); ctx.arc(Math.cos(a) * r * 0.36, Math.sin(a) * r * 0.36, r * 0.045, 0, TAU); ctx.fill(); }
  // tread marks rotating so the turn reads
  ctx.strokeStyle = rgba([52, 52, 52]); ctx.lineWidth = r * 0.05;
  for (let i = 0; i < 16; i++) { const a = i * TAU / 16; ctx.beginPath(); ctx.moveTo(Math.cos(a) * r * 0.86, Math.sin(a) * r * 0.86); ctx.lineTo(Math.cos(a) * r * 0.98, Math.sin(a) * r * 0.98); ctx.stroke(); }
  if (opts.mud) { ctx.fillStyle = rgba([92, 74, 52], 0.5); ctx.beginPath(); ctx.arc(r * 0.3, r * 0.4, r * 0.25, 0, TAU); ctx.fill(); }
  ctx.restore();
}
// side view, facing screen-right; (x, y) = bottom-left of the body; L = length
function busSide(ctx, x, y, L, t, opts = {}) {
  const Hb = L * 0.31;
  ctx.save(); ctx.translate(x, y + (opts.shake ? Math.sin(t * 31) * 1.5 : 0));
  // shadow
  ctx.fillStyle = 'rgba(20,18,14,0.35)'; ctx.beginPath(); ctx.ellipse(L * 0.5, L * 0.1, L * 0.55, L * 0.03, 0, 0, TAU); ctx.fill();
  // body + hood
  ctx.fillStyle = rgba(BUS);
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(0, -Hb + 14); ctx.quadraticCurveTo(0, -Hb, 14, -Hb);
  ctx.lineTo(L * 0.8, -Hb); ctx.quadraticCurveTo(L * 0.82, -Hb, L * 0.82, -Hb * 0.9);
  ctx.lineTo(L * 0.84, -Hb * 0.55); ctx.lineTo(L * 0.97, -Hb * 0.5); ctx.quadraticCurveTo(L * 1.0, -Hb * 0.48, L * 1.0, -Hb * 0.3);
  ctx.lineTo(L * 1.0, 0); ctx.closePath(); ctx.fill();
  // grime gradient and rust
  ctx.save(); ctx.clip();
  ctx.fillStyle = grad(ctx, -Hb, 0, [[0, 'rgba(255,255,255,0.08)'], [0.6, 'rgba(0,0,0,0)'], [1, 'rgba(60,40,20,0.35)']]); ctx.fillRect(0, -Hb, L, Hb);
  const rnd = U.rng(3);
  for (let i = 0; i < 9; i++) { ctx.fillStyle = rgba(RUST, 0.35 + rnd() * 0.3); ctx.beginPath(); ctx.ellipse(rnd() * L, -rnd() * Hb * 0.35, 8 + rnd() * 22, 4 + rnd() * 9, 0, 0, TAU); ctx.fill(); }
  ctx.restore();
  // black stripes
  ctx.fillStyle = rgba([30, 26, 22]);
  ctx.fillRect(0, -Hb * 0.5, L * 0.84, 5); ctx.fillRect(0, -Hb * 0.28, L * 1.0, 5);
  // windows with passengers' silhouettes swaying in unison
  const nW = 7;
  for (let i = 0; i < nW; i++) {
    const wx = L * 0.05 + i * L * 0.1, wy = -Hb * 0.9, ww = L * 0.085, wh = Hb * 0.3;
    ctx.fillStyle = rgba(GLASS); ctx.fillRect(wx, wy, ww, wh);
    ctx.fillStyle = 'rgba(200,210,220,0.12)'; ctx.fillRect(wx, wy, ww, wh * 0.35);
    if (opts.passengers !== false && i < nW) {
      const sway = Math.sin(t * (opts.songRate || 1.6) + (opts.sync ? 0 : i)) * 2.5;
      ctx.fillStyle = rgba([28, 30, 34]);
      ctx.beginPath(); ctx.ellipse(wx + ww * 0.5 + sway, wy + wh * 0.62, ww * 0.18, wh * 0.26, 0, 0, TAU); ctx.fill();
      ctx.fillRect(wx + ww * 0.22 + sway, wy + wh * 0.82, ww * 0.56, wh * 0.18);
    }
  }
  // windshield with the empty driver's seat behind it
  ctx.fillStyle = rgba(GLASS); ctx.beginPath(); ctx.moveTo(L * 0.76, -Hb * 0.9); ctx.lineTo(L * 0.81, -Hb * 0.9); ctx.lineTo(L * 0.83, -Hb * 0.58); ctx.lineTo(L * 0.76, -Hb * 0.58); ctx.fill();
  // headlight, bumper
  ctx.fillStyle = rgba([220, 210, 170], 0.7); ctx.beginPath(); ctx.arc(L * 0.985, -Hb * 0.4, 5, 0, TAU); ctx.fill();
  ctx.fillStyle = rgba([34, 32, 30]); ctx.fillRect(L * 0.94, -8, L * 0.075, 10); ctx.fillRect(-8, -8, 12, 10);
  // wheels turning
  const ang = (opts.wheelAng ?? t * 6);
  wheel(ctx, L * 0.2, 0, L * 0.075, ang, { mud: true }); wheel(ctx, L * 0.86, 0, L * 0.075, ang, { mud: true });
  ctx.restore();
}
// front view, low angle: a hulking carcass. (cx, gy) = centre on the ground; Wd = width
function busFront(ctx, cx, gy, Wd, t) {
  ctx.save(); ctx.translate(cx, gy);
  const Hb = Wd * 1.25;
  // body trapezoid (low angle: wider at the bottom)
  ctx.fillStyle = rgba(BUS);
  ctx.beginPath(); ctx.moveTo(-Wd * 0.52, -Wd * 0.1); ctx.lineTo(-Wd * 0.44, -Hb); ctx.quadraticCurveTo(0, -Hb - Wd * 0.06, Wd * 0.44, -Hb); ctx.lineTo(Wd * 0.52, -Wd * 0.1); ctx.closePath(); ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = grad(ctx, -Hb, 0, [[0, 'rgba(255,255,255,0.06)'], [1, 'rgba(50,30,14,0.4)']]); ctx.fillRect(-Wd, -Hb - 40, Wd * 2, Hb + 40);
  const rnd = U.rng(8);
  for (let i = 0; i < 8; i++) { ctx.fillStyle = rgba(RUST, 0.3 + rnd() * 0.3); ctx.beginPath(); ctx.ellipse((rnd() - 0.5) * Wd, -rnd() * Hb * 0.4 - 10, 10 + rnd() * 30, 5 + rnd() * 12, 0, 0, TAU); ctx.fill(); }
  ctx.restore();
  // windshield: two panes, the left one shows the empty driver's seat
  for (const sg of [-1, 1]) {
    ctx.fillStyle = rgba(GLASS);
    ctx.beginPath(); ctx.moveTo(sg * Wd * 0.02, -Hb * 0.93); ctx.lineTo(sg * Wd * 0.4, -Hb * 0.92); ctx.lineTo(sg * Wd * 0.42, -Hb * 0.6); ctx.lineTo(sg * Wd * 0.02, -Hb * 0.6); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(210,220,230,0.1)'; ctx.fill();
  }
  ctx.fillStyle = rgba([70, 52, 40]);
  ctx.beginPath(); ctx.roundRect(-Wd * 0.28, -Hb * 0.74, Wd * 0.16, Wd * 0.16, 8); ctx.fill();
  ctx.strokeStyle = rgba([40, 36, 34]); ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(-Wd * 0.2, -Hb * 0.62, Wd * 0.1, Wd * 0.03, 0, 0, TAU); ctx.stroke();
  // hood + grille (a jaw)
  ctx.fillStyle = rgba(shade(BUS, -0.08));
  ctx.beginPath(); ctx.moveTo(-Wd * 0.34, -Hb * 0.55); ctx.lineTo(Wd * 0.34, -Hb * 0.55); ctx.lineTo(Wd * 0.38, -Wd * 0.18); ctx.lineTo(-Wd * 0.38, -Wd * 0.18); ctx.closePath(); ctx.fill();
  ctx.fillStyle = rgba([36, 32, 30]); ctx.fillRect(-Wd * 0.2, -Hb * 0.46, Wd * 0.4, Hb * 0.26);
  ctx.strokeStyle = rgba([150, 146, 140]); ctx.lineWidth = 5;
  for (let i = -4; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(i * Wd * 0.045, -Hb * 0.45); ctx.lineTo(i * Wd * 0.045, -Hb * 0.21); ctx.stroke(); }
  // hollow headlights, dim
  for (const sg of [-1, 1]) {
    ctx.fillStyle = rgba([40, 38, 36]); ctx.beginPath(); ctx.arc(sg * Wd * 0.29, -Hb * 0.36, Wd * 0.065, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba([210, 200, 160], 0.35 + 0.05 * Math.sin(t * 3)); ctx.beginPath(); ctx.arc(sg * Wd * 0.29, -Hb * 0.36, Wd * 0.045, 0, TAU); ctx.fill();
  }
  // bumper and wheels
  ctx.fillStyle = rgba([30, 28, 26]); ctx.fillRect(-Wd * 0.5, -Wd * 0.2, Wd, Wd * 0.08);
  ctx.fillStyle = rgba([24, 24, 26]);
  for (const sg of [-1, 1]) { ctx.beginPath(); ctx.roundRect(sg * Wd * 0.42 - Wd * 0.08, -Wd * 0.15, Wd * 0.16, Wd * 0.17, 10); ctx.fill(); }
  ctx.restore();
}
function road(ctx, hy, vx, t, speed, width = 520, opts = {}) {
  ctx.fillStyle = rgba([66, 66, 70]);
  ctx.beginPath(); ctx.moveTo(vx - 4, hy); ctx.lineTo(vx + 4, hy); ctx.lineTo(W / 2 + width, H); ctx.lineTo(W / 2 - width, H); ctx.fill();
  // centre dashes rushing toward the camera
  for (let i = 0; i < 14; i++) {
    const z = ((i / 14 + t * speed * 0.05) % 1);
    const zz = Math.pow(z, 2.2);
    const y = hy + zz * (H - hy), half = 2 + zz * 18, len = 6 + zz * 90;
    ctx.fillStyle = rgba([200, 190, 150], 0.7);
    ctx.fillRect(vx + (W / 2 - vx) * zz - half / 2, y, half, len);
  }
}

// ---------------------------------------------------------------- passengers
const ROWS = [
  { z: 0.85, left: 'elder', right: 'child' },
  { z: 1.35, left: 'suit', right: 'teen' },
  { z: 1.95, left: 'woman', right: 'beard' },
];
const VP = [360, 470], F = 480;
function crowdState(name, mode, p, isChild) {
  const t = p.t, song = p.song;
  const singing = mode === 'sing' || mode === 'sing_loud' || mode === 'drone';
  let e = exprParams('neutral', 0), mouth = { open: 0, wide: 0, round: 0, teeth: 0 };
  const note = singing ? song(t) : 0;
  if (mode === 'sing') { e = exprParams('peaceful', 0.8); e.lidUp = 0.62; mouth = { open: 0.12 + note * 0.45, wide: 0.1, round: 0.75, teeth: 0.1 }; }
  if (mode === 'sing_loud') { e = exprParams('smile', 0.6); e.lidUp = 0.66; mouth = { open: 0.2 + note * 0.7, wide: 0.3, round: 0.5, teeth: 0.3 }; }
  if (mode === 'drone') { e = exprParams('sleepy', 0.9); e.lidUp = 0.12; mouth = { open: 0.04 + note * 0.18, wide: 0, round: 0.9, teeth: 0 }; }
  if (mode === 'stop') {
    const k = smooth((t - p.songEnd) / 0.5), k2 = smooth((t - p.songEnd - 1.4) / 1.2);
    e = exprParams('surprised', 0.6 * k + 0.2);
    const w = exprParams('fearful', 0.6); for (const key in e) e[key] = lerp(e[key], w[key], k2 * 0.8);
    if (t < p.songEnd) { e = exprParams('sleepy', 0.9); e.lidUp = 0.12; mouth = { open: 0.1, wide: 0, round: 0.9, teeth: 0 }; }
  }
  if (isChild) {
    if (mode === 'notice') { e = exprParams('worried', 0.8); }
    if (mode === 'fear') { e = exprParams('fearful', 0.75); }
    if (mode === 'resolve') { e = exprParams('determined', 0.85); }
    if (mode === 'sing') { e.lidUp = 0.9; }
  }
  const unison = Math.sin(t * TAU / 1.2);
  const sway = singing ? (mode === 'drone' ? 0.6 : 1) * unison : 0;
  return { e, mouth, sway };
}
function passenger(ctx, ch, x, y, s, side, mode, p, isChild, extra = {}) {
  const cs = crowdState(ch.name, mode, p, isChild);
  const seed = ch.name.length * 13;
  const yaw = side * -0.14 + (extra.yaw || 0) + 0.03 * U.fbm1(p.t * 0.2, seed);
  const gaze = extra.gaze || { x: -side * 0.1, y: 0.05 };
  const blinkPh = (p.t * 0.27 + seed * 0.13) % 1;
  const st = {
    x: x + cs.sway * s * 0.05, y, s, yaw, pitch: (mode === 'drone' ? 0.12 : 0) + 0.02 * U.fbm1(p.t * 0.17, seed + 1),
    roll: cs.sway * 0.05, e: { ...cs.e, ...(extra.e || {}) }, mouth: cs.mouth, gaze, blink: blinkPh < 0.03 ? 1 - Math.abs(blinkPh - 0.015) / 0.015 : 0,
    arms: R.armsFor(extra.gesture || 'idle', side > 0 ? -1 : 1), breath: Math.sin(p.t * 1.4 + seed), t: p.t, tear: extra.tear || 0,
    light: { keyX: side > 0 ? 0.4 : -0.4, rim: [210, 220, 230], rimX: side > 0 ? 1 : -1, rimA: 0.35, amb: [120, 130, 150], ambA: 0.1 },
  };
  R.drawCharacter(ctx, ch, st);
}
function seatBack(ctx, x, y, s) {
  // green vinyl bench back with a chrome top rail
  const w = s * 2.2, h = s * 3.2;
  ctx.fillStyle = grad(ctx, y, y + h, [[0, [66, 104, 84]], [1, [36, 60, 48]]]);
  ctx.beginPath(); ctx.roundRect(x - w / 2, y, w, h, s * 0.25); ctx.fill();
  ctx.strokeStyle = rgba([170, 176, 180]); ctx.lineWidth = s * 0.06; ctx.beginPath(); ctx.moveTo(x - w / 2 + s * 0.1, y + s * 0.04); ctx.lineTo(x + w / 2 - s * 0.1, y + s * 0.04); ctx.stroke();
  ctx.strokeStyle = rgba([30, 50, 40], 0.5); ctx.lineWidth = s * 0.03; ctx.beginPath(); ctx.moveTo(x, y + s * 0.3); ctx.lineTo(x, y + h); ctx.stroke();
}
function interiorShell(ctx, t, opts = {}) {
  // ceiling, walls, aisle in perspective toward the back of the bus
  ctx.fillStyle = grad(ctx, 0, VP[1], [[0, [190, 186, 172]], [1, [150, 148, 140]]]); ctx.fillRect(0, 0, W, VP[1]);
  ctx.fillStyle = grad(ctx, VP[1], H, [[0, [70, 68, 64]], [1, [40, 38, 36]]]); ctx.fillRect(0, VP[1], W, H - VP[1]);
  // ceiling ribs
  ctx.strokeStyle = rgba([150, 146, 136]); ctx.lineWidth = 3;
  for (let i = 1; i < 7; i++) { const z = i * 0.45, y = VP[1] - 1.5 * F / z * 0.55; if (y < 0) continue; ctx.beginPath(); ctx.moveTo(VP[0] - 0.9 * F / z, y); ctx.lineTo(VP[0] + 0.9 * F / z, y); ctx.stroke(); }
  // side windows: landscape streaks receding into the vanishing point
  for (const sg of [-1, 1]) {
    ctx.save();
    ctx.beginPath(); ctx.moveTo(VP[0] + sg * 1.25 * F / 0.7, VP[1] - 0.35 * F / 0.7); ctx.lineTo(VP[0] + sg * 1.25 * F / 4, VP[1] - 0.35 * F / 4);
    ctx.lineTo(VP[0] + sg * 1.25 * F / 4, VP[1] + 0.15 * F / 4); ctx.lineTo(VP[0] + sg * 1.25 * F / 0.7, VP[1] + 0.15 * F / 0.7); ctx.closePath(); ctx.clip();
    ctx.fillStyle = grad(ctx, 0, H, [[0, [176, 182, 188]], [0.45, [196, 196, 190]], [0.5, [150, 140, 116]], [1, [120, 110, 90]]]); ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 10; i++) {
      const ph = ((i / 10) + t * 0.35) % 1, z = lerp(0.7, 4, ph);
      const x = VP[0] + sg * 1.25 * F / z;
      ctx.strokeStyle = rgba([80, 74, 66], 0.5); ctx.lineWidth = 30 / z;
      ctx.beginPath(); ctx.moveTo(x, VP[1] - 0.35 * F / z); ctx.lineTo(x, VP[1] + 0.15 * F / z); ctx.stroke();
    }
    if (opts.blur) { ctx.fillStyle = `rgba(230,120,200,${0.12 + 0.08 * Math.sin(t * 3)})`; ctx.fillRect(0, 0, W, H); }
    ctx.restore();
  }
  // floor aisle
  ctx.fillStyle = rgba([44, 42, 40]);
  ctx.beginPath(); ctx.moveTo(VP[0] - 10, VP[1] + 1.5 * F / 4); ctx.lineTo(VP[0] + 10, VP[1] + 1.5 * F / 4); ctx.lineTo(VP[0] + 120, H); ctx.lineTo(VP[0] - 120, H); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(0, 0, W, H);
  // far rows: simple swaying silhouettes
  for (let z = 4.2; z >= 2.6; z -= 0.8) {
    const s = 0.24 * F / z;
    for (const sg of [-1, 1]) {
      const x = VP[0] + sg * 0.45 * F / z, y = VP[1] + 0.25 * F / z;
      seatBack(ctx, x, y + s * 0.25, s);
      const sway = opts.singing ? Math.sin(t * TAU / 1.2) * s * 0.06 : 0;
      ctx.fillStyle = rgba([70, 66, 64]);
      ctx.beginPath(); ctx.ellipse(x + sway, y - s * 0.35, s * 0.36, s * 0.47, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.roundRect(x - s * 0.75 + sway, y + s * 0.12, s * 1.5, s * 1.4, s * 0.4); ctx.fill();
    }
  }
}
function drawRows(ctx, p, mode, childMode, opts = {}) {
  for (let r = ROWS.length - 1; r >= 0; r--) {
    const row = ROWS[r], z = row.z, s = 0.24 * F / z;
    for (const [side, key] of [[-1, row.left], [1, row.right]]) {
      const x = VP[0] + side * 0.45 * F / z, hy = VP[1] + 0.25 * F / z;
      seatBack(ctx, x, hy + s * 0.28, s);
      const isChild = key === 'child';
      if (isChild && opts.childStanding) continue;
      const ch = isChild ? CAST.CHILD : CAST.PASSENGERS[key];
      const notchY = hy + 0.6 * s;
      const extra = isChild ? (opts.childExtra || {}) : (opts.extra || {});
      passenger(ctx, ch, x, notchY, s, side, isChild ? (childMode || mode) : mode, p, isChild, extra);
    }
  }
}
function barrier(ctx) {
  // the white panel and stanchion behind the driver, in the foreground
  ctx.fillStyle = grad(ctx, 890, H, [[0, [206, 204, 196]], [1, [150, 148, 140]]]);
  ctx.fillRect(0, 890, W, H - 890);
  ctx.fillStyle = rgba([120, 120, 118]); ctx.fillRect(0, 886, W, 8);
  ctx.strokeStyle = rgba([196, 198, 200]); ctx.lineWidth = 14; ctx.beginPath(); ctx.moveTo(26, H); ctx.lineTo(26, 560); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,255,255,0.4)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(22, H); ctx.lineTo(22, 560); ctx.stroke();
}

// ---------------------------------------------------------------- part I shots
const S = {};
S.bus_wide = (ctx, p) => {
  ctx.save(); if (p.params.push) push(ctx, p.u, 0.12, 360, 700);
  overcastSky(ctx, 700, p.t); plain(ctx, 700, p.t);
  poles(ctx, 700, p.t, 30, -10);
  // the road runs across the plain; the bus crosses it side-on
  ctx.fillStyle = rgba([70, 70, 74]); ctx.fillRect(0, 800, W, 110);
  ctx.fillStyle = rgba([200, 190, 150], 0.6);
  for (let i = 0; i < 6; i++) ctx.fillRect(((i * 160 - p.t * 120) % 960 + 960) % 960 - 120, 852, 70, 5);
  busSide(ctx, 70, 880, 520, p.t, { sync: true });
  dust(ctx, p.t, 30, [210, 200, 180], 0.4);
  ctx.restore();
};
S.bus_front = (ctx, p) => {
  ctx.save(); push(ctx, p.u, 0.1, 360, 760);
  overcastSky(ctx, 820, p.t, 0.15); plain(ctx, 820, p.t);
  road(ctx, 820, 360, p.t, 1, 420);
  busFront(ctx, 360, 1010 + Math.sin(p.t * 9) * 2, 470, p.t);
  dust(ctx, p.t, 26);
  ctx.restore();
};
S.wheel_cu = (ctx, p) => {
  const fast = p.params.fast;
  ctx.fillStyle = grad(ctx, 0, H, [[0, [150, 112, 44]], [0.55, [190, 140, 46]], [1, [70, 70, 74]]]); ctx.fillRect(0, 0, W, H);
  // fender arch with rust, and the road racing underneath
  ctx.fillStyle = rgba([40, 36, 32]); ctx.beginPath(); ctx.arc(360, 700, 330, Math.PI, TAU); ctx.fill();
  ctx.fillStyle = grad(ctx, 880, H, [[0, [76, 76, 80]], [1, [50, 50, 54]]]); ctx.fillRect(0, 880, W, H - 880);
  for (let i = 0; i < 12; i++) {
    const x = ((i * 140 - p.t * (fast ? 900 : 420)) % 1000 + 1000) % 1000 - 140;
    ctx.fillStyle = 'rgba(200,190,160,0.25)'; ctx.fillRect(x, 900 + (i % 3) * 60, 120, 4);
  }
  const ang = p.t * (fast ? 9 : 4.5);
  wheel(ctx, 360, 700, 290, ang, { mud: true });
  // the mindless insistence: a faint repeating tick at the rim
  const k = (p.t * (fast ? 3 : 1.5)) % 1;
  FX.glow(ctx, 360 + Math.cos(-Math.PI / 2) * 290, 700 - 290, 30, [255, 230, 180], 0.25 * (1 - k));
};
S.bus_side = (ctx, p) => {
  overcastSky(ctx, 720, p.t); plain(ctx, 720, p.t);
  // an ever-receding horizon: a glimmering city of promises that slides further away
  const k = easeInOut(p.u);
  const cx = 600 + k * 40, cs = 1 - k * 0.55;
  ctx.save(); ctx.globalAlpha = 0.8;
  for (let i = 0; i < 9; i++) {
    const bw = 16 * cs, bh = (30 + (i % 4) * 22) * cs;
    ctx.fillStyle = rgba([150, 160, 180]); ctx.fillRect(cx + (i - 4) * 18 * cs, 718 - bh, bw, bh);
  }
  FX.glow(ctx, cx, 700, 120 * cs, [255, 230, 170], 0.45);
  ctx.restore();
  poles(ctx, 720, p.t, 60, 0);
  ctx.fillStyle = rgba([66, 66, 70]); ctx.fillRect(0, 800, W, 120);
  ctx.fillStyle = rgba([200, 190, 150], 0.6);
  for (let i = 0; i < 6; i++) ctx.fillRect(((i * 160 - p.t * 300) % 960 + 960) % 960 - 120, 858, 70, 5);
  busSide(ctx, 40, 875, 560, p.t, { sync: true });
  dust(ctx, p.t, 20);
};
S.steering_cu = (ctx, p) => {
  // windshield view over an empty dashboard; the wheel turns a little by itself
  overcastSky(ctx, 600, p.t, 0.2); plain(ctx, 600, p.t);
  road(ctx, 600, 360, p.t, 1.2, 360);
  ctx.fillStyle = grad(ctx, 660, H, [[0, [52, 50, 48]], [1, [26, 24, 22]]]); ctx.fillRect(0, 660, W, H - 660);
  ctx.fillStyle = rgba([40, 38, 36]); ctx.fillRect(0, 0, W, 70); ctx.fillRect(0, 0, 40, 660); ctx.fillRect(680, 0, 40, 660);
  const ang = Math.sin(p.lt * 0.7) * 0.25 + Math.sin(p.lt * 1.9) * 0.05;
  ctx.save(); ctx.translate(330, 900); ctx.rotate(ang);
  ctx.strokeStyle = rgba([30, 28, 28]); ctx.lineWidth = 38; ctx.beginPath(); ctx.arc(0, 0, 250, 0, TAU); ctx.stroke();
  ctx.strokeStyle = rgba([80, 76, 72], 0.6); ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(0, 0, 262, Math.PI * 1.1, Math.PI * 1.6); ctx.stroke();
  ctx.lineWidth = 30; ctx.strokeStyle = rgba([36, 34, 34]);
  for (const a of [Math.PI * 0.5, Math.PI * 1.17, Math.PI * 1.83]) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * 240, Math.sin(a) * 240); ctx.stroke(); }
  ctx.fillStyle = rgba([60, 56, 52]); ctx.beginPath(); ctx.arc(0, 0, 60, 0, TAU); ctx.fill();
  ctx.restore();
};
S.compass_cu = (ctx, p) => {
  overcastSky(ctx, 700, p.t, 0.55);
  FX.stars(ctx, W, 520, p.t, 5, 26, { fade: () => 0.35 });
  plain(ctx, 700, p.t);
  ctx.fillStyle = grad(ctx, 720, H, [[0, [50, 48, 46]], [1, [24, 22, 22]]]); ctx.fillRect(0, 720, W, H - 720);
  // dashboard compass: the card wanders and spins without settling
  const cx = 360, cy = 760, r = 170;
  ctx.fillStyle = rgba([30, 30, 32]); ctx.beginPath(); ctx.arc(cx, cy, r + 26, 0, TAU); ctx.fill();
  const dg = ctx.createRadialGradient(cx - 50, cy - 60, 10, cx, cy, r);
  dg.addColorStop(0, 'rgba(240,236,220,1)'); dg.addColorStop(1, 'rgba(176,170,150,1)');
  ctx.fillStyle = dg; ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.fill();
  const spin = p.lt * 1.6 + Math.sin(p.lt * 2.3) * 1.2;
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(spin);
  ctx.strokeStyle = rgba([60, 56, 50]); ctx.lineWidth = 3;
  for (let i = 0; i < 36; i++) { const a = i * TAU / 36, L = i % 9 === 0 ? 30 : 14; ctx.beginPath(); ctx.moveTo(Math.cos(a) * (r - 6), Math.sin(a) * (r - 6)); ctx.lineTo(Math.cos(a) * (r - 6 - L), Math.sin(a) * (r - 6 - L)); ctx.stroke(); }
  ctx.fillStyle = rgba([200, 50, 40]); ctx.beginPath(); ctx.moveTo(0, -r + 40); ctx.lineTo(16, 0); ctx.lineTo(-16, 0); ctx.fill();
  ctx.fillStyle = rgba([70, 70, 74]); ctx.beginPath(); ctx.moveTo(0, r - 40); ctx.lineTo(16, 0); ctx.lineTo(-16, 0); ctx.fill();
  ctx.restore();
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.beginPath(); ctx.ellipse(cx - 60, cy - 80, 70, 30, -0.5, 0, TAU); ctx.fill();
};
S.empty_seat = (ctx, p) => {
  ctx.save(); push(ctx, p.u, 0.12, 360, 620);
  // windshield light from the front, the worn driver's seat from behind-left
  ctx.fillStyle = grad(ctx, 0, H, [[0, [70, 72, 78]], [1, [28, 26, 26]]]); ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = grad(ctx, 120, 520, [[0, [196, 200, 204]], [1, [150, 146, 136]]]); ctx.fillRect(60, 120, 600, 400);
  ctx.strokeStyle = rgba([40, 38, 36]); ctx.lineWidth = 18; ctx.strokeRect(60, 120, 600, 400);
  // light shaft with dust motes
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = grad(ctx, 200, 1100, [[0, 'rgba(255,250,230,0.16)'], [1, 'rgba(255,250,230,0)']]);
  ctx.beginPath(); ctx.moveTo(200, 200); ctx.lineTo(560, 200); ctx.lineTo(700, 1100); ctx.lineTo(120, 1100); ctx.fill();
  ctx.restore();
  dust(ctx, p.t * 0.3, 40, [255, 250, 230], 0.5);
  // steering wheel ahead of the seat
  ctx.strokeStyle = rgba([24, 22, 22]); ctx.lineWidth = 22; ctx.beginPath(); ctx.ellipse(470, 560, 130, 48, -0.15, 0, TAU); ctx.stroke();
  // the seat: cracked brown vinyl, empty, seatbelt hanging
  // headrest, a tall backrest with side bolsters and stitched panels, the cushion below
  ctx.fillStyle = rgba([96, 60, 40]); ctx.beginPath(); ctx.roundRect(225, 400, 190, 110, 36); ctx.fill();
  ctx.fillStyle = rgba([70, 70, 74]); ctx.fillRect(285, 500, 14, 40); ctx.fillRect(340, 500, 14, 40);
  ctx.fillStyle = grad(ctx, 520, 960, [[0, [116, 74, 48]], [1, [64, 40, 28]]]);
  ctx.beginPath(); ctx.moveTo(170, 960); ctx.lineTo(160, 590); ctx.quadraticCurveTo(160, 530, 220, 530); ctx.lineTo(420, 530); ctx.quadraticCurveTo(480, 530, 480, 590); ctx.lineTo(470, 960); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = rgba([60, 36, 24], 0.6); ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(220, 560); ctx.lineTo(225, 940); ctx.moveTo(420, 560); ctx.lineTo(415, 940); ctx.moveTo(230, 740); ctx.lineTo(410, 740); ctx.stroke();
  ctx.fillStyle = 'rgba(255,240,220,0.08)'; ctx.beginPath(); ctx.roundRect(180, 560, 40, 380, 20); ctx.fill();
  ctx.fillStyle = rgba([86, 54, 36]); ctx.beginPath(); ctx.roundRect(140, 930, 420, 140, 34); ctx.fill();
  ctx.strokeStyle = rgba([50, 30, 20], 0.7); ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(240, 560); ctx.lineTo(262, 610); ctx.lineTo(250, 650); ctx.moveTo(380, 700); ctx.lineTo(360, 760); ctx.stroke();
  ctx.strokeStyle = rgba([40, 40, 44]); ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(450, 520); ctx.quadraticCurveTo(500, 760, 470, 980); ctx.stroke();
  ctx.fillStyle = rgba([150, 150, 150]); ctx.fillRect(458, 975, 26, 34);
  ctx.restore();
};
S.interior = (ctx, p) => {
  const mode = p.seg.crowd || 'sing', child = p.seg.child || mode;
  ctx.save(); push(ctx, p.u, p.params.loud ? 0.06 : 0.03, 360, 600);
  interiorShell(ctx, p.t, { singing: mode !== 'stop' || p.t < p.songEnd });
  const extra = {};
  if (mode === 'stop') extra.gaze = { x: 0, y: 0 };
  const childExtra = {};
  if (child === 'notice' || child === 'fear') childExtra.gaze = { x: -0.5, y: -0.1 };
  drawRows(ctx, p, mode, child, { extra, childExtra });
  ctx.restore();
  barrier(ctx);
};
S.singers_cu = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [170, 166, 156]], [1, [80, 78, 74]]]); ctx.fillRect(0, 0, W, H);
  FX.glow(ctx, 360, 300, 500, [230, 230, 220], 0.3, false);
  seatBack(ctx, 200, 700, 200); seatBack(ctx, 540, 700, 200);
  passenger(ctx, CAST.PASSENGERS.elder, 200, 760, 230, -1, 'sing', p, false);
  passenger(ctx, CAST.PASSENGERS.suit, 530, 790, 220, 1, 'sing', p, false);
};
S.child_cu = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [160, 158, 150]], [1, [70, 68, 64]]]); ctx.fillRect(0, 0, W, H);
  seatBack(ctx, 360, 640, 240);
  // the child stops singing and glances toward the empty driver's seat
  const k = smooth(p.lt / 0.8);
  const extra = { gaze: { x: lerp(0, -0.85, k), y: -0.05 }, yaw: lerp(0, -0.35, k) };
  passenger(ctx, CAST.CHILD, 360, 820, 270, 1, 'notice', p, true, extra);
};
S.gears_cu = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [40, 36, 34]], [1, [16, 14, 14]]]); ctx.fillRect(0, 0, W, H);
  const gear = (x, y, r, n, ang, col) => {
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
    ctx.fillStyle = rgba(col);
    ctx.beginPath();
    for (let i = 0; i < n * 2; i++) { const a = i * Math.PI / n, rr = i % 2 ? r : r * 1.14; ctx.lineTo(Math.cos(a - 0.12) * rr, Math.sin(a - 0.12) * rr); ctx.lineTo(Math.cos(a + 0.12) * rr, Math.sin(a + 0.12) * rr); }
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = rgba(shade(col, -0.35)); ctx.beginPath(); ctx.arc(0, 0, r * 0.35, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba(shade(col, 0.2), 0.4); ctx.beginPath(); ctx.arc(-r * 0.2, -r * 0.2, r * 0.6, 3.6, 4.6); ctx.lineTo(0, 0); ctx.fill();
    ctx.restore();
  };
  // gears grind with a stutter
  const jerk = p.lt * 2.2 + Math.max(0, Math.sin(p.lt * 7)) * 0.15;
  gear(270, 560, 210, 14, jerk, [110, 100, 88]);
  gear(530, 800, 150, 10, -jerk * 1.4 + 0.2, [96, 88, 78]);
  // sparks at the contact, bursting on the screech
  const burst = 1 + 2.5 * smooth((p.lt - 1.2) / 0.3) * (1 - smooth((p.lt - 2.4) / 0.6));
  for (let i = 0; i < 18 * burst; i++) {
    const ph = ((p.lt * 2.3 + U.hash(i)) % 1);
    const a = -0.9 + U.hash(i * 7) * 1.4, d = ph * (120 + U.hash(i * 3) * 160);
    FX.glow(ctx, 430 + Math.cos(a) * d, 690 + Math.sin(a) * d + ph * ph * 120, 8, [255, 190, 90], 0.9 * (1 - ph));
  }
};
S.brake_cu = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [50, 48, 46]], [1, [20, 18, 18]]]); ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = rgba([34, 32, 30]); ctx.fillRect(0, 980, W, 300);
  // the pedal sags; its rod hangs loose from a frayed cable
  const snap = smooth((p.lt - 1.0) / 0.15);
  const sag = 0.2 + snap * 0.35;
  ctx.save(); ctx.translate(380, 420); ctx.rotate(sag);
  ctx.fillStyle = rgba([90, 88, 86]); ctx.fillRect(-12, 0, 24, 420);
  ctx.fillStyle = rgba([60, 58, 56]); ctx.beginPath(); ctx.roundRect(-90, 400, 180, 90, 14); ctx.fill();
  ctx.strokeStyle = rgba([110, 108, 104]); ctx.lineWidth = 4;
  for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(-70, 420 + i * 16); ctx.lineTo(70, 420 + i * 16); ctx.stroke(); }
  ctx.restore();
  ctx.strokeStyle = rgba([150, 146, 140]); ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(380, 420); ctx.quadraticCurveTo(240, 330 - snap * 60, 150 - snap * 40, 300 + snap * 160); ctx.stroke();
  ctx.lineWidth = 2;
  for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.moveTo(150 - snap * 40, 300 + snap * 160); ctx.lineTo(150 - snap * 40 + Math.cos(i) * 18, 300 + snap * 160 + Math.sin(i) * 18); ctx.stroke(); }
  if (p.lt > 1.0 && p.lt < 1.6) FX.glow(ctx, 150, 330, 60, [255, 200, 120], 0.6 * (1 - (p.lt - 1.0) / 0.6));
};
S.cliff_approach = (ctx, p) => {
  overcastSky(ctx, 560, p.t, 0.3);
  // plain that ends in a cliff edge: beyond, mist and nothing
  ctx.fillStyle = grad(ctx, 560, H, [[0, [140, 132, 110]], [1, [90, 84, 68]]]); ctx.fillRect(0, 560, W, H - 560);
  ctx.fillStyle = grad(ctx, 500, 600, [[0, 'rgba(210,212,214,0)'], [1, 'rgba(210,212,214,0.9)']]); ctx.fillRect(0, 500, W, 70);
  ctx.fillStyle = rgba([60, 56, 50]); ctx.fillRect(0, 556, W, 10);
  road(ctx, 560, 360, p.t, 1.5, 300);
  // the bus small and receding toward the edge (seen from behind)
  const k = easeInOut(p.u), bx = 360, by = lerp(820, 640, k), bw = lerp(150, 70, k);
  ctx.fillStyle = rgba(BUS); ctx.beginPath(); ctx.roundRect(bx - bw / 2, by - bw * 1.1, bw, bw * 1.1, bw * 0.08); ctx.fill();
  ctx.fillStyle = rgba(GLASS); ctx.fillRect(bx - bw * 0.38, by - bw * 0.98, bw * 0.76, bw * 0.34);
  ctx.fillStyle = rgba([30, 28, 26]); ctx.fillRect(bx - bw * 0.52, by - bw * 0.08, bw * 1.04, bw * 0.08);
  ctx.fillStyle = rgba([200, 40, 30], 0.8); ctx.fillRect(bx - bw * 0.45, by - bw * 0.3, bw * 0.1, bw * 0.07); ctx.fillRect(bx + bw * 0.35, by - bw * 0.3, bw * 0.1, bw * 0.07);
  dust(ctx, p.t, 18);
};
S.child_window = (ctx, p) => {
  // the child pressed to the window, seeing the edge ahead
  ctx.fillStyle = grad(ctx, 0, H, [[0, [150, 146, 140]], [1, [60, 58, 56]]]); ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.beginPath(); ctx.roundRect(360, 240, 330, 560, 30); ctx.clip();
  overcastSky(ctx, 560, p.t, 0.3);
  ctx.fillStyle = rgba([130, 122, 100]); ctx.fillRect(360, 560, 330, 240);
  ctx.fillStyle = rgba([210, 212, 214], 0.8); ctx.fillRect(360, 520, 330, 40);
  ctx.fillStyle = rgba([50, 46, 42]); ctx.fillRect(360, 556, 330, 6);
  ctx.restore();
  ctx.strokeStyle = rgba([110, 108, 104]); ctx.lineWidth = 16; ctx.beginPath(); ctx.roundRect(360, 240, 330, 560, 30); ctx.stroke();
  seatBack(ctx, 210, 720, 210);
  passenger(ctx, CAST.CHILD, 250, 860, 250, -1, 'fear', p, true, { yaw: 0.8, gaze: { x: 0.7, y: -0.05 }, gesture: 'reach' });
};
S.window_blur = (ctx, p) => {
  ctx.fillStyle = rgba([90, 88, 84]); ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.beginPath(); ctx.roundRect(60, 160, 600, 760, 40); ctx.clip();
  ctx.fillStyle = grad(ctx, 160, 920, [[0, [150, 150, 160]], [1, [110, 100, 90]]]); ctx.fillRect(0, 0, W, H);
  // fleeting distractions: bright screens, hearts and glints streaking past
  for (let i = 0; i < 16; i++) {
    const sp = 500 + U.hash(i) * 700, y = 200 + U.hash(i * 5) * 680, w = 60 + U.hash(i * 9) * 160;
    const x = ((U.hash(i * 3) * 1400 - p.t * sp) % 1400 + 1400) % 1400 - 300;
    const col = [[255, 90, 160], [90, 200, 255], [255, 210, 80], [140, 255, 150], [200, 120, 255]][i % 5];
    ctx.fillStyle = rgba(col, 0.55);
    ctx.beginPath(); ctx.roundRect(x, y, w * 1.6, w * 0.7, 12); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.5)'; ctx.fillRect(x + w * 1.6, y + w * 0.3, w * 1.8, 3);
    if (i % 4 === 0) { ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.beginPath(); ctx.arc(x + w * 0.8, y + w * 0.35, w * 0.14, 0, TAU); ctx.fill(); }
  }
  // a placid passenger's reflection in the glass
  ctx.globalAlpha = 0.22;
  passenger(ctx, CAST.PASSENGERS.teen, 360, 760, 220, 1, 'sing', p, false);
  ctx.restore();
  ctx.strokeStyle = rgba([60, 58, 56]); ctx.lineWidth = 22; ctx.beginPath(); ctx.roundRect(60, 160, 600, 760, 40); ctx.stroke();
};
S.bus_momentum = (ctx, p) => {
  overcastSky(ctx, 700, p.t, 0.35); plain(ctx, 700, p.t);
  ctx.fillStyle = rgba([50, 46, 42]); ctx.fillRect(560, 690, 160, 14);
  ctx.fillStyle = 'rgba(210,212,214,0.7)'; ctx.fillRect(580, 640, 140, 50);
  ctx.fillStyle = rgba([66, 66, 70]); ctx.fillRect(0, 790, W, 130);
  for (let i = 0; i < 10; i++) { ctx.fillStyle = 'rgba(220,210,180,0.6)'; ctx.fillRect(((i * 120 - p.t * 900) % 1200 + 1200) % 1200 - 120, 850, 80, 5); }
  // speed lines
  for (let i = 0; i < 14; i++) { const y = 300 + U.hash(i) * 600, x = ((U.hash(i * 3) * 900 - p.t * 1200) % 900 + 900) % 900; ctx.fillStyle = 'rgba(240,236,220,0.25)'; ctx.fillRect(x - 200, y, 200, 2); }
  busSide(ctx, 60 + Math.sin(p.t * 3) * 6, 870, 520, p.t, { shake: true, wheelAng: p.t * 14, sync: true, songRate: 1.0 });
  dust(ctx, p.t * 3, 30, [200, 190, 170], 0.5);
};
S.window_cliff = (ctx, p) => {
  // through the windshield: the road runs straight off the edge, nearer every second
  const k = easeInOut(p.u);
  const edgeY = lerp(560, 780, k);
  overcastSky(ctx, edgeY, p.t, 0.3);
  ctx.fillStyle = grad(ctx, edgeY - 120, edgeY, [[0, 'rgba(220,222,224,0)'], [1, 'rgba(220,222,224,0.95)']]); ctx.fillRect(0, edgeY - 120, W, 120);
  ctx.fillStyle = rgba([130, 122, 100]); ctx.fillRect(0, edgeY, W, H - edgeY);
  ctx.fillStyle = rgba([56, 52, 46]); ctx.fillRect(0, edgeY - 4, W, 10);
  road(ctx, edgeY, 360, p.t, 2.5, 420);
  ctx.fillStyle = grad(ctx, 880, H, [[0, [46, 44, 42]], [1, [24, 22, 22]]]); ctx.fillRect(0, 880, W, H - 880);
  ctx.fillStyle = rgba([36, 34, 32]); ctx.fillRect(0, 0, W, 90); ctx.fillRect(0, 0, 50, 900); ctx.fillRect(670, 0, 50, 900);
  ctx.strokeStyle = rgba([28, 26, 26]); ctx.lineWidth = 30; ctx.beginPath(); ctx.arc(200, 1080, 230, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
};
S.child_stand = (ctx, p) => {
  interiorShell(ctx, p.t, { singing: false });
  drawRows(ctx, p, 'stop', 'stop', { childStanding: true, extra: { gaze: { x: 0.2, y: 0 } } });
  // the child stands in the aisle, facing the empty driver's seat, ready to act
  const k = smooth(p.lt / 1.2);
  const g = k > 0.5 ? 'reach' : 'fist';
  passenger(ctx, CAST.CHILD, 400, lerp(900, 770, k), 300, 1, 'resolve', p, true, { yaw: -0.55, gaze: { x: -0.7, y: 0.1 }, gesture: g });
  barrier(ctx);
};

// ---------------------------------------------------------------- part II helpers
function brickWall(ctx, x0, y0, w, h, scale = 1, dusk = 1) {
  ctx.fillStyle = rgba(mix([118, 66, 52], [70, 42, 40], dusk * 0.6)); ctx.fillRect(x0, y0, w, h);
  const bw = 64 * scale, bh = 26 * scale;
  const rnd = U.rng(17);
  for (let r = 0; r * bh < h + bh; r++) {
    for (let c = -1; c * bw < w + bw; c++) {
      const x = x0 + c * bw + (r % 2) * bw / 2, y = y0 + r * bh;
      const v = rnd() * 0.25 - 0.12;
      ctx.fillStyle = rgba(shade(mix([128, 72, 56], [78, 46, 42], dusk * 0.6), v));
      ctx.fillRect(x + 2 * scale, y + 2 * scale, bw - 4 * scale, bh - 4 * scale);
      if (rnd() < 0.12) { ctx.fillStyle = rgba([40, 30, 26], 0.25); ctx.fillRect(x + rnd() * bw * 0.6, y + 3, bw * 0.3, bh * 0.4); }
    }
  }
  // water stains running down
  for (let i = 0; i < 6; i++) { const x = x0 + rnd() * w; ctx.fillStyle = grad(ctx, y0, y0 + h, [[0, 'rgba(20,16,20,0.25)'], [1, 'rgba(20,16,20,0)']]); ctx.fillRect(x, y0, 10 + rnd() * 30, h * (0.4 + rnd() * 0.5)); }
}
function pipe(ctx, x, y0, y1, r, opts = {}) {
  const col = opts.chrome ? [210, 220, 226] : opts.copper ? [176, 110, 70] : [138, 150, 160];
  const g = ctx.createLinearGradient(x - r, 0, x + r, 0);
  g.addColorStop(0, rgba(shade(col, -0.45))); g.addColorStop(0.3, rgba(shade(col, opts.chrome ? 0.5 : 0.15))); g.addColorStop(0.45, rgba(col)); g.addColorStop(1, rgba(shade(col, -0.5)));
  ctx.fillStyle = g; ctx.fillRect(x - r, y0, r * 2, y1 - y0);
  // joints / brackets, embossed symbols of promotion and currency on the old spout
  ctx.fillStyle = rgba(shade(col, -0.3));
  for (let y = y0 + (opts.offset || 0) % 220; y < y1; y += 220) {
    ctx.fillRect(x - r * 1.12, y, r * 2.24, r * 0.3);
    if (opts.symbols) {
      ctx.strokeStyle = rgba(shade(col, 0.25), 0.6); ctx.lineWidth = r * 0.08;
      ctx.beginPath(); ctx.moveTo(x - r * 0.3, y + r * 1.6); ctx.lineTo(x, y + r * 1.2); ctx.lineTo(x + r * 0.3, y + r * 1.6); ctx.moveTo(x, y + r * 1.2); ctx.lineTo(x, y + r * 2.1); ctx.stroke();
      ctx.beginPath(); ctx.arc(x, y + r * 3.0, r * 0.32, 0, TAU); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x, y + r * 2.8); ctx.lineTo(x, y + r * 3.2); ctx.stroke();
    }
  }
  if (opts.rust) { const rnd = U.rng(5); for (let i = 0; i < 14; i++) { ctx.fillStyle = rgba([120, 70, 40], 0.22 + rnd() * 0.15); ctx.beginPath(); ctx.ellipse(x + (rnd() - 0.5) * r * 1.4, y0 + rnd() * (y1 - y0), Math.min(14, r * 0.09), Math.min(30, r * 0.2), 0, 0, TAU); ctx.fill(); } }
  if (opts.beads) { for (let i = 0; i < 14; i++) { const by = y0 + ((U.hash(i) * (y1 - y0)) + opts.beads * 40 * U.hash(i * 3)) % (y1 - y0); ctx.fillStyle = 'rgba(240,250,255,0.6)'; ctx.beginPath(); ctx.ellipse(x - r * 0.2 + U.hash(i * 7) * r * 0.6, by, 3, 5, 0, 0, TAU); ctx.fill(); } }
}
function rain(ctx, t, n, heavy = 0, faces = false, col = [150, 160, 180]) {
  for (let i = 0; i < n; i++) {
    const sp = 700 + U.hash(i) * 500, x = U.hash(i * 3) * W + Math.sin(i) * 10;
    const y = ((U.hash(i * 5) * H + t * sp) % (H + 100)) - 50;
    ctx.strokeStyle = rgba(col, 0.35 + heavy * 0.2); ctx.lineWidth = 1.5 + heavy;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 4, y + 26 + heavy * 20); ctx.stroke();
  }
  if (faces) {
    // larger drops that carry faint sorrowing faces: the unmourned griefs
    for (let i = 0; i < 9; i++) {
      const x = 80 + U.hash(i * 11) * 560, y = ((U.hash(i * 13) * H + t * 260) % (H + 200)) - 100, r = 26 + U.hash(i) * 14;
      ctx.fillStyle = 'rgba(150,165,190,0.35)';
      ctx.beginPath(); ctx.moveTo(x, y - r * 1.5); ctx.quadraticCurveTo(x + r, y, x, y + r); ctx.quadraticCurveTo(x - r, y, x, y - r * 1.5); ctx.fill();
      ctx.fillStyle = 'rgba(60,70,90,0.45)';
      ctx.beginPath(); ctx.arc(x - r * 0.3, y - r * 0.1, r * 0.08, 0, TAU); ctx.arc(x + r * 0.3, y - r * 0.1, r * 0.08, 0, TAU); ctx.fill();
      ctx.strokeStyle = 'rgba(60,70,90,0.45)'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, y + r * 0.45, r * 0.25, Math.PI * 1.2, Math.PI * 1.8); ctx.stroke();
    }
  }
}
function wetGround(ctx, y, t) {
  ctx.fillStyle = grad(ctx, y, H, [[0, [52, 50, 56]], [1, [30, 28, 34]]]); ctx.fillRect(0, y, W, H - y);
  ctx.fillStyle = 'rgba(160,170,190,0.15)'; ctx.beginPath(); ctx.ellipse(380, y + 90, 200, 30, 0, 0, TAU); ctx.fill();
  for (let i = 0; i < 4; i++) { const ph = (t * 0.6 + i * 0.25) % 1; FX.ring(ctx, 380 + (i - 1.5) * 60, y + 90, ph * 50, 2, [200, 210, 230], 0.4 * (1 - ph)); }
}
function spiderState(mood, p, extra = {}) {
  const m = CAST.SPIDER_MOODS[mood] || CAST.SPIDER_MOODS.shy;
  const blinkPh = (p.t * 0.3) % 1;
  return { ...m, blink: blinkPh < 0.04 ? 1 - Math.abs(blinkPh - 0.02) / 0.02 : 0, t: p.t, ...extra };
}
function duskBg(ctx) {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [44, 46, 60]], [1, [24, 24, 32]]]); ctx.fillRect(0, 0, W, H);
}

// ---------------------------------------------------------------- part II shots
S.wall_wide = (ctx, p) => {
  ctx.save(); if (p.params.push) push(ctx, p.u, 0.15, 400, 960);
  brickWall(ctx, 0, 0, W, 1000, 1, 1);
  pipe(ctx, 400, 0, 950, 34, { rust: true, symbols: true });
  // the spout bends out over a puddle, dripping
  ctx.fillStyle = rgba([120, 132, 142]); ctx.beginPath(); ctx.roundRect(366, 920, 130, 60, 20); ctx.fill();
  const dph = (p.t * 0.8) % 1;
  ctx.fillStyle = 'rgba(190,210,235,0.8)'; ctx.beginPath(); ctx.ellipse(480, 990 + dph * 70, 4, 7, 0, 0, TAU); ctx.fill();
  wetGround(ctx, 1000, p.t);
  CAST.spider(ctx, 360, 1060, 9, spiderState('shy', p));
  FX.glow(ctx, 600, 200, 400, [255, 190, 120], 0.12, false);
  ctx.restore();
};
S.spider_cu = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [70, 76, 86]], [1, [40, 42, 50]]]); ctx.fillRect(0, 0, W, H);
  pipe(ctx, 360, 0, H, 300, { rust: true, beads: p.t });
  const st = spiderState('shy', p, { gaze: { x: Math.sin(p.lt * 0.6) * 0.3, y: p.lt > 2 ? -0.6 : 0 } });
  CAST.spider(ctx, 360, 560, 120, st);
};
S.spout_up = (ctx, p) => {
  // looking up the towering spout, its top lost in a bright promise
  brickWall(ctx, 0, 0, W, H, 1.3, 1);
  ctx.save();
  ctx.translate(360, H); ctx.scale(1, 1);
  const g = ctx.createLinearGradient(-120, 0, 120, 0);
  g.addColorStop(0, '#50585f'); g.addColorStop(0.35, '#a7b4bd'); g.addColorStop(1, '#3c4248');
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-130, 0); ctx.lineTo(-28, -H); ctx.lineTo(28, -H); ctx.lineTo(130, 0); ctx.fill();
  ctx.strokeStyle = 'rgba(210,220,230,0.45)'; ctx.lineWidth = 3;
  for (let i = 1; i < 9; i++) { const k = 1 - Math.pow(i / 9, 0.7); const y = -H * (1 - k); const w = lerp(28, 130, k); ctx.beginPath(); ctx.moveTo(-w, y); ctx.lineTo(w, y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-w * 0.3, y - 30 * k); ctx.lineTo(0, y - 60 * k); ctx.lineTo(w * 0.3, y - 30 * k); ctx.stroke(); }
  ctx.restore();
  FX.glow(ctx, 360, 0, 360, [255, 236, 190], 0.5, false);
  CAST.spider(ctx, 360, 1080, 14, spiderState('hopeful', p, { climb: true, legPhase: p.lt * 0.8 }));
};
S.spider_climb = (ctx, p) => {
  const pole = p.params.pole;
  if (pole) { ctx.fillStyle = grad(ctx, 0, H, [[0, [200, 236, 222]], [1, [250, 214, 196]]]); ctx.fillRect(0, 0, W, H); }
  else brickWall(ctx, 0, 0, W, H, 1.4, 1);
  const scroll = p.lt * 60;
  pipe(ctx, 360, -40, H + 40, 110, pole ? { chrome: true, offset: scroll } : { rust: true, symbols: true, offset: scroll });
  const mood = p.seg.spider || 'hopeful';
  const st = spiderState(mood, p, { climb: true, legPhase: p.lt * 1.4, burden: true, gaze: { x: 0, y: -0.75 } });
  CAST.spider(ctx, 360, 600 + Math.sin(p.lt * TAU * 1.4) * 6, 64, st);
};
S.spider_burden = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [60, 64, 74]], [1, [30, 32, 40]]]); ctx.fillRect(0, 0, W, H);
  pipe(ctx, 360, 0, H, 280, { rust: true });
  const tear = clamp((p.u - 0.45) / 0.45);
  CAST.spider(ctx, 360, 520, 110, spiderState('sad', p, { burden: true, tear, climb: false, legSpread: 0.15 }));
};
S.spider_slip = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [60, 66, 76]], [1, [30, 32, 40]]]); ctx.fillRect(0, 0, W, H);
  pipe(ctx, 360, 0, H, 200, { beads: p.t * 2 });
  // slides down a little, scrabbles, slides again
  const slide = (p.lt % 1.6) < 0.5 ? (p.lt % 1.6) * 80 : 40;
  CAST.spider(ctx, 360, 500 + slide, 80, spiderState('strain', p, { climb: true, legPhase: p.lt * 3, burden: true, legSpread: Math.sin(p.lt * 9) * 0.1 }));
};
S.rain_begins = (ctx, p) => {
  brickWall(ctx, 0, 0, W, H, 1.4, 1);
  pipe(ctx, 360, -40, H + 40, 110, { rust: true });
  ctx.fillStyle = grad(ctx, 0, 300, [[0, 'rgba(20,22,30,0.85)'], [1, 'rgba(20,22,30,0)']]); ctx.fillRect(0, 0, W, 300);
  rain(ctx, p.t, Math.floor(30 + p.u * 60), p.u * 0.4);
  CAST.spider(ctx, 360, 640, 64, spiderState('worried', p, { burden: true, wet: p.u }));
};
S.rain_faces = (ctx, p) => {
  duskBg(ctx);
  // a little schoolhouse in the mist, its smallest members huddled outside in the downpour
  ctx.fillStyle = rgba([70, 72, 86]);
  ctx.fillRect(420, 620, 200, 140); ctx.beginPath(); ctx.moveTo(410, 620); ctx.lineTo(520, 540); ctx.lineTo(630, 620); ctx.fill();
  ctx.fillRect(505, 500, 30, 50);
  ctx.fillStyle = rgba([110, 110, 120], 0.6); ctx.fillRect(500, 690, 40, 70);
  for (let i = 0; i < 4; i++) FX.figure(ctx, 440 + i * 50, 800, 70, 'hold', { color: [90, 96, 116], child: true, rim: [180, 190, 210] });
  ctx.fillStyle = 'rgba(160,170,190,0.18)'; ctx.fillRect(0, 0, W, H);
  pipe(ctx, 150, 0, H, 70, { rust: true });
  wetGround(ctx, 800, p.t);
  rain(ctx, p.t, p.params.heavy ? 160 : 100, p.params.heavy ? 0.8 : 0.3, true);
};
S.washout = (ctx, p) => {
  brickWall(ctx, 0, 0, W, 900, 1.2, 1);
  pipe(ctx, 300, 0, 700, 70, { rust: true });
  ctx.fillStyle = rgba([120, 132, 142]); ctx.beginPath(); ctx.roundRect(232, 680, 200, 80, 26); ctx.fill();
  wetGround(ctx, 900, p.t);
  // the torrent gushes out of the spout and throws the spider into the puddle
  for (let i = 0; i < 30; i++) {
    const ph = (p.lt * 1.6 + U.hash(i)) % 1;
    const x = 430 + ph * 140 + U.hash(i * 3) * 30, y = 720 + ph * ph * 280;
    ctx.fillStyle = `rgba(150,170,200,${0.5 * (1 - ph)})`; ctx.beginPath(); ctx.ellipse(x, y, 14, 30, 0.6, 0, TAU); ctx.fill();
  }
  rain(ctx, p.t, 120, 0.8);
  const k = clamp(p.lt / 1.6);
  const sx = lerp(440, 560, k), sy = lerp(720, 960, k * k), ang = k * 6;
  CAST.spider(ctx, sx, sy, 34, spiderState(k < 1 ? 'panic' : 'dazed', p, { angle: k < 1 ? ang : 0.3, burden: true, wet: 1, legSpread: 0.2 }));
  if (k >= 1) { const sp = (p.lt - 1.6); FX.ring(ctx, 560, 980, sp * 120, 3, [200, 210, 230], Math.max(0, 0.6 - sp)); }
};
S.sun_appears = (ctx, p) => {
  const k = easeInOut(clamp(p.u * 1.4));
  ctx.fillStyle = grad(ctx, 0, H, [[0, mix([60, 66, 84], [150, 190, 220], k)], [1, mix([40, 40, 50], [230, 210, 170], k)]]); ctx.fillRect(0, 0, W, H);
  CAST.sun(ctx, 360, lerp(520, 320, k), 150, { t: p.t, smile: 0.9, lid: 0.55, browUp: 0.6, gaze: { x: 0, y: 0.6 } });
  // clouds parting
  for (const sg of [-1, 1]) for (let i = 0; i < 3; i++) FX.glow(ctx, 360 + sg * (160 + k * 300 + i * 90), 300 + i * 70, 230, [90, 96, 110], 0.6 * (1 - k * 0.6), false);
  wetGround(ctx, 1020, p.t);
  CAST.spider(ctx, 360, 1080, 22, spiderState('dazed', p, { wet: 1 - k, burden: true }));
};
S.pills = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [150, 190, 220]], [1, [230, 210, 170]]]); ctx.fillRect(0, 0, W, H);
  CAST.sun(ctx, 360, 230, 120, { t: p.t, smile: 0.85, lid: 0.6, gaze: { x: 0, y: 0.8 } });
  // a beam lowers a capsule; the spider takes it and its gaze goes flat
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = grad(ctx, 300, 900, [[0, 'rgba(255,230,160,0.35)'], [1, 'rgba(255,230,160,0.05)']]);
  ctx.beginPath(); ctx.moveTo(330, 330); ctx.lineTo(390, 330); ctx.lineTo(460, 860); ctx.lineTo(260, 860); ctx.fill();
  ctx.restore();
  const k = clamp(p.u / 0.5);
  if (k < 1) {
    const py = lerp(380, 780, easeInOut(k));
    ctx.save(); ctx.translate(360, py); ctx.rotate(0.6);
    ctx.fillStyle = '#e8eef4'; ctx.beginPath(); ctx.roundRect(-34, -14, 34, 28, [14, 0, 0, 14]); ctx.fill();
    ctx.fillStyle = '#d65a6a'; ctx.beginPath(); ctx.roundRect(0, -14, 34, 28, [0, 14, 14, 0]); ctx.fill();
    ctx.restore();
  }
  ctx.fillStyle = rgba([120, 140, 110]); ctx.fillRect(0, 920, W, H - 920);
  const numb = smooth((p.u - 0.5) / 0.3);
  CAST.spider(ctx, 360, 860, 70, spiderState(numb > 0.5 ? 'numb' : 'dazed', p, { burden: true, open: k > 0.8 && k < 1 ? 0.5 : 0 }));
};
S.therapist = (ctx, p) => {
  // a quiet office: muted teal wall, a lamp, an abstract print, the therapist in an armchair
  ctx.fillStyle = grad(ctx, 0, H, [[0, [86, 112, 114]], [1, [54, 70, 72]]]); ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = rgba([60, 50, 44]); ctx.fillRect(0, 1000, W, H - 1000);
  ctx.fillStyle = rgba([200, 190, 170]); ctx.fillRect(420, 180, 200, 150); ctx.fillStyle = rgba([150, 120, 100]); ctx.beginPath(); ctx.arc(480, 260, 40, 0, TAU); ctx.fill(); ctx.fillStyle = rgba([90, 120, 130]); ctx.fillRect(520, 220, 70, 80);
  FX.glow(ctx, 90, 420, 260, [255, 210, 150], 0.3, false);
  // the "different tube": a tall glass column standing on the floor
  const tx = 600;
  ctx.fillStyle = 'rgba(200,230,240,0.3)'; ctx.fillRect(tx - 34, 360, 68, 650);
  ctx.strokeStyle = 'rgba(230,245,255,0.7)'; ctx.lineWidth = 4; ctx.strokeRect(tx - 34, 360, 68, 650);
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillRect(tx - 24, 370, 8, 620);
  // armchair
  ctx.fillStyle = rgba([150, 110, 60]); ctx.beginPath(); ctx.roundRect(60, 560, 360, 520, 60); ctx.fill();
  ctx.fillStyle = rgba([130, 94, 50]); ctx.beginPath(); ctx.roundRect(330, 820, 140, 70, 24); ctx.fill();
  const g = p.lt > 0.6 ? 'open_palm' : 'idle';
  R.drawCharacter(ctx, CAST.THERAPIST, {
    x: 240, y: 720, s: 140, yaw: 0.55, pitch: 0.05, e: exprParams('tender', 0.6), gaze: { x: 0.5, y: 0.25 },
    blink: ((p.t * 0.25) % 1) < 0.03 ? 1 : 0, arms: R.armsFor(g, 1), breath: Math.sin(p.t * 1.3), t: p.t,
    mouth: { open: 0, wide: 0, round: 0, teeth: 0 }, light: { keyX: -0.6, rim: [255, 220, 170], rimX: -1, rimA: 0.3, amb: [80, 110, 110], ambA: 0.1 },
  });
  CAST.spider(ctx, 420, 800, 22, spiderState('unsure', p, { gaze: { x: 0.8, y: -0.4 } }));
};
S.sun_cu = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [150, 196, 230]], [1, [240, 220, 180]]]); ctx.fillRect(0, 0, W, H);
  const k = smooth(p.lt / 1.5);
  // the benign smile; a sweep of light gestures toward a new structure off to the side
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = `rgba(255,236,170,${0.3 * k})`;
  ctx.beginPath(); ctx.moveTo(400, 520); ctx.lineTo(720, 700 - 60 * k); ctx.lineTo(720, 900 + 60 * k); ctx.closePath(); ctx.fill();
  ctx.restore();
  CAST.sun(ctx, 330, 480, 230, { t: p.t, smile: 0.95, lid: lerp(0.6, 0.45, k), browUp: 0.8, gaze: { x: lerp(0, 0.9, k), y: 0.2 } });
};
S.wellness_pole = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [196, 236, 220]], [1, [252, 214, 196]]]); ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 10; i++) {
    const x = 80 + U.hash(i) * 560, y = ((U.hash(i * 3) * 900 + p.t * 18) % 1000) + 80;
    ctx.save(); ctx.translate(x, y); ctx.rotate(Math.sin(p.t + i) * 0.4);
    ctx.fillStyle = 'rgba(110,170,120,0.5)'; ctx.beginPath(); ctx.ellipse(0, 0, 18, 8, 0, 0, TAU); ctx.fill(); ctx.restore();
  }
  pipe(ctx, 360, 60, 1060, 60, { chrome: true });
  // a lotus emblem plate on the pole
  ctx.fillStyle = rgba([240, 244, 246]); ctx.beginPath(); ctx.arc(360, 540, 80, 0, TAU); ctx.fill();
  ctx.fillStyle = rgba([230, 150, 170]);
  for (let i = -2; i <= 2; i++) { ctx.save(); ctx.translate(360, 560); ctx.rotate(i * 0.42); ctx.beginPath(); ctx.ellipse(0, -30, 13, 34, 0, 0, TAU); ctx.fill(); ctx.restore(); }
  for (let i = 0; i < 5; i++) { const ph = (p.t * 0.7 + i * 0.2) % 1; FX.light(ctx, 330 + U.hash(i) * 50, 120 + ph * 900, 2.5, [255, 255, 255], Math.sin(ph * Math.PI)); }
  ctx.fillStyle = rgba([190, 200, 196]); ctx.fillRect(0, 1060, W, H - 1060);
};
S.pole_flaws = (ctx, p) => {
  ctx.fillStyle = grad(ctx, 0, H, [[0, [150, 170, 166]], [1, [120, 110, 106]]]); ctx.fillRect(0, 0, W, H);
  pipe(ctx, 360, 260, H, 220, { chrome: true, beads: p.t * 3 });
  // it, too, ends in a spout and a drain
  ctx.fillStyle = rgba([150, 160, 166]); ctx.beginPath(); ctx.roundRect(140, 160, 440, 120, 50); ctx.fill();
  ctx.fillStyle = rgba([40, 44, 48]); for (let i = 0; i < 6; i++) ctx.fillRect(200 + i * 56, 196, 34, 50);
  const ph = (p.t * 0.7) % 1;
  ctx.fillStyle = 'rgba(220,240,255,0.8)'; ctx.beginPath(); ctx.ellipse(300, 300 + ph * 700, 7, 12, 0, 0, TAU); ctx.fill();
};
S.cycle_loop = (ctx, p) => {
  duskBg(ctx);
  const cx = 360, cy = 560, r = 230, rot = p.t * 0.25;
  ctx.strokeStyle = 'rgba(200,210,230,0.35)'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.stroke();
  const icons = ['pipe', 'rain', 'fall', 'sun', 'pole'];
  icons.forEach((ic, i) => {
    const a = rot + i * TAU / 5 - Math.PI / 2, x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r;
    ctx.fillStyle = 'rgba(30,32,44,0.9)'; ctx.beginPath(); ctx.arc(x, y, 62, 0, TAU); ctx.fill();
    ctx.strokeStyle = 'rgba(200,210,230,0.5)'; ctx.lineWidth = 3; ctx.stroke();
    ctx.save(); ctx.translate(x, y);
    if (ic === 'pipe') { ctx.fillStyle = '#8796a3'; ctx.fillRect(-12, -40, 24, 80); }
    if (ic === 'rain') { ctx.fillStyle = '#5a6070'; ctx.beginPath(); ctx.ellipse(0, -14, 34, 18, 0, 0, TAU); ctx.fill(); ctx.strokeStyle = '#9fb0cc'; ctx.lineWidth = 3; for (let k = -1; k <= 1; k++) { ctx.beginPath(); ctx.moveTo(k * 14, 8); ctx.lineTo(k * 14 - 4, 30); ctx.stroke(); } }
    if (ic === 'fall') { ctx.strokeStyle = '#c8d0e0'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0, -30); ctx.lineTo(0, 24); ctx.lineTo(-10, 14); ctx.moveTo(0, 24); ctx.lineTo(10, 14); ctx.stroke(); }
    if (ic === 'sun') { ctx.fillStyle = '#ffd060'; ctx.beginPath(); ctx.arc(0, 0, 24, 0, TAU); ctx.fill(); }
    if (ic === 'pole') { ctx.fillStyle = '#d8e2e8'; ctx.fillRect(-9, -40, 18, 80); ctx.fillStyle = '#e696aa'; ctx.beginPath(); ctx.arc(0, -4, 12, 0, TAU); ctx.fill(); }
    ctx.restore();
  });
  // the spider travels the ring, forever
  const a = rot * 3 - Math.PI / 2;
  CAST.spider(ctx, cx + Math.cos(a) * r, cy + Math.sin(a) * r, 26, spiderState('determined', p, { climb: true, legPhase: p.t * 2, angle: a + Math.PI, burden: true }));
};
S.montage = (ctx, p) => {
  // "The climb, the rain, the fall, the superficial drying, the redirection to another treacherous ascent."
  const parts = ['spider_climb', 'rain_begins', 'washout', 'drying', 'sun_cu'];
  const i = Math.min(4, Math.floor(p.u * 5));
  const sub = { ...p, lt: (p.u * 5 - i) * (p.seg.end - p.seg.start) / 5, u: p.u * 5 - i };
  if (parts[i] === 'drying') {
    ctx.fillStyle = grad(ctx, 0, H, [[0, [150, 190, 220]], [1, [230, 210, 170]]]); ctx.fillRect(0, 0, W, H);
    CAST.sun(ctx, 360, 250, 120, { t: p.t, smile: 0.9 });
    ctx.fillStyle = rgba([140, 130, 110]); ctx.fillRect(0, 900, W, H - 900);
    for (let k = 0; k < 6; k++) { const ph = (p.t * 0.8 + k / 6) % 1; ctx.fillStyle = `rgba(255,255,255,${0.3 * (1 - ph)})`; ctx.beginPath(); ctx.ellipse(330 + k * 12, 840 - ph * 140, 10, 16, 0, 0, TAU); ctx.fill(); }
    CAST.spider(ctx, 360, 860, 60, spiderState('numb', p, { burden: true }));
  } else S[parts[i]](ctx, sub);
};
S.many_spouts = (ctx, p) => {
  duskBg(ctx);
  ctx.fillStyle = grad(ctx, 560, H, [[0, [50, 50, 60]], [1, [26, 26, 32]]]); ctx.fillRect(0, 560, W, H - 560);
  // spouts and poles receding in rows; a tiny climber on each, and one human among them
  for (let row = 5; row >= 0; row--) {
    const z = 1 + row * 0.7, y = 560 + 420 / z;
    for (let c = -3; c <= 3; c++) {
      const x = 360 + c * 230 / z, h = 700 / z, r = 16 / z;
      const chrome = (c + row) % 2 === 0;
      pipe(ctx, x, y - h, y, r, chrome ? { chrome: true } : { rust: true });
      const cy = y - h * (0.2 + 0.6 * ((p.t * 0.05 + U.hash(row * 9 + c)) % 1));
      if (row === 1 && c === 1) FX.figure(ctx, x + r * 2, cy + 60 / z, 120 / z, 'reach', { color: [70, 70, 84], rim: [180, 190, 210] });
      else CAST.spider(ctx, x, cy, 6 / z + 2, spiderState('determined', p, { climb: true, legPhase: p.t + c }));
    }
  }
  rain(ctx, p.t, 60, 0.1);
};
S.final_spider = (ctx, p) => {
  ctx.save(); push(ctx, 1 - p.u, 0.12, 360, 700);
  brickWall(ctx, 0, 0, W, 980, 1.1, 1);
  pipe(ctx, 360, 0, 960, 60, { copper: true });
  wetGround(ctx, 960, p.t);
  rain(ctx, p.t, Math.floor(20 + p.u * 60), 0.2);
  CAST.spider(ctx, 360, 900, 42, spiderState('final', p, { burden: true, wet: p.u }));
  ctx.restore();
};

module.exports = { S, W, H };
