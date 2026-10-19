'use strict';
// Painted set pieces (backgrounds and props). All drawn in frame pixels.

const { lerp, clamp, rgbStr, shade, col, rng, mix } = require('./util');
const { roundRect } = require('./body');

function grad(ctx, x0, y0, x1, y1, stops) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  for (const [o, c, a] of stops) g.addColorStop(o, rgbStr(c, a ?? 1));
  return g;
}
function radial(ctx, x, y, r0, r1, stops) {
  const g = ctx.createRadialGradient(x, y, r0, x, y, r1);
  for (const [o, c, a] of stops) g.addColorStop(o, rgbStr(c, a ?? 1));
  return g;
}

// ------------------------------------------------------------- dining room
function diningWall(ctx, w, h, o = {}) {
  const lampX = o.lampX ?? w / 2, lampY = o.lampY ?? 330;
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, [92, 58, 40]], [0.45, [150, 98, 64]], [1, [70, 44, 32]]]);
  ctx.fillRect(0, 0, w, h);
  // subtle wallpaper stripes
  ctx.globalAlpha = 0.07;
  for (let x = -20; x < w + 40; x += 46) { ctx.fillStyle = '#2b160c'; ctx.fillRect(x, 0, 14, h); }
  ctx.globalAlpha = 1;
  // lamp light pooling on the wall
  ctx.fillStyle = radial(ctx, lampX, lampY + 120, 10, 820, [[0, [255, 196, 130], 0.55], [0.5, [230, 150, 90], 0.18], [1, [0, 0, 0], 0]]);
  ctx.fillRect(0, 0, w, h);
  // wainscot
  const wy = o.wainY ?? 1180;
  ctx.fillStyle = grad(ctx, 0, wy, 0, h, [[0, [74, 44, 30]], [1, [40, 24, 18]]]);
  ctx.fillRect(0, wy, w, h - wy);
  ctx.fillStyle = 'rgba(255,220,180,0.18)'; ctx.fillRect(0, wy - 6, w, 8);
  ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(0, wy + 2, w, 6);
  if (o.window) window_(ctx, o.window);
  if (o.photo) photoFrame(ctx, o.photo);
  if (o.clock) clockFace(ctx, o.clock);
  if (o.door) {
    const d = o.door;
    ctx.fillStyle = 'rgba(25,14,10,0.9)'; ctx.fillRect(d.x, d.y, d.w, d.h);
    ctx.strokeStyle = 'rgba(200,150,100,0.35)'; ctx.lineWidth = 10; ctx.strokeRect(d.x - 5, d.y - 5, d.w + 10, d.h + 10);
    ctx.fillStyle = radial(ctx, d.x + d.w * 0.6, d.y + d.h * 0.3, 5, d.w, [[0, [255, 210, 150], 0.25], [1, [0, 0, 0], 0]]);
    ctx.fillRect(d.x, d.y, d.w, d.h);
  }
  if (o.hutch) hutch(ctx, o.hutch);
  if (o.sconce) for (const s of o.sconce) {
    ctx.fillStyle = radial(ctx, s.x, s.y, 2, 160, [[0, [255, 220, 160], 0.85], [0.25, [255, 170, 100], 0.35], [1, [0, 0, 0], 0]]);
    ctx.beginPath(); ctx.arc(s.x, s.y, 160, 0, Math.PI * 2); ctx.fill();
  }
}
function window_(ctx, r) {
  // night-blue dusk sky with a sliver of warm horizon
  ctx.fillStyle = grad(ctx, 0, r.y, 0, r.y + r.h, [[0, [30, 44, 86]], [0.7, [70, 80, 120]], [1, [196, 128, 96]]]);
  ctx.fillRect(r.x, r.y, r.w, r.h);
  // distant house lights
  const rr = rng(5);
  for (let i = 0; i < 9; i++) {
    ctx.fillStyle = `rgba(255,${200 + rr() * 40},${120 + rr() * 50},${0.5 + rr() * 0.4})`;
    ctx.fillRect(r.x + 10 + rr() * (r.w - 30), r.y + r.h * (0.72 + rr() * 0.2), 6, 8);
  }
  ctx.strokeStyle = '#e8d8c4'; ctx.lineWidth = 14;
  ctx.strokeRect(r.x, r.y, r.w, r.h);
  ctx.lineWidth = 8;
  ctx.beginPath(); ctx.moveTo(r.x + r.w / 2, r.y); ctx.lineTo(r.x + r.w / 2, r.y + r.h);
  ctx.moveTo(r.x, r.y + r.h * 0.45); ctx.lineTo(r.x + r.w, r.y + r.h * 0.45); ctx.stroke();
  // curtains
  for (const s of [-1, 1]) {
    const cx = s < 0 ? r.x - 20 : r.x + r.w + 20;
    ctx.fillStyle = grad(ctx, cx - 70, 0, cx + 70, 0, [[0, [120, 40, 34]], [0.5, [168, 66, 52]], [1, [110, 36, 30]]]);
    ctx.beginPath();
    ctx.moveTo(cx - 60, r.y - 40); ctx.lineTo(cx + 60, r.y - 40);
    ctx.quadraticCurveTo(cx + 30 * s, r.y + r.h * 0.5, cx + 70, r.y + r.h + 120);
    ctx.lineTo(cx - 70, r.y + r.h + 120);
    ctx.quadraticCurveTo(cx - 30 * s, r.y + r.h * 0.5, cx - 60, r.y - 40);
    ctx.fill();
    ctx.strokeStyle = 'rgba(60,15,10,0.35)'; ctx.lineWidth = 6;
    for (const k of [-25, 5, 30]) { ctx.beginPath(); ctx.moveTo(cx + k, r.y - 30); ctx.quadraticCurveTo(cx + k + 10 * s, r.y + r.h * 0.5, cx + k * 1.2, r.y + r.h + 110); ctx.stroke(); }
  }
}
// A posed family photo where everyone is smiling (the irony is the point).
function photoFrame(ctx, r) {
  ctx.fillStyle = '#3b2416'; ctx.fillRect(r.x - 14, r.y - 14, r.w + 28, r.h + 28);
  ctx.fillStyle = '#d9c7a8'; ctx.fillRect(r.x, r.y, r.w, r.h);
  ctx.fillStyle = grad(ctx, 0, r.y, 0, r.y + r.h, [[0, [120, 160, 190]], [1, [200, 190, 160]]]);
  ctx.fillRect(r.x + 10, r.y + 10, r.w - 20, r.h - 20);
  const n = 4;
  const skins = ['#c28c68', '#a26d4c', '#b67d58', '#b27752'];
  const hairs = ['#5b3b2a', '#8f8b86', '#2a1a15', '#1d1511'];
  for (let i = 0; i < n; i++) {
    const cx = r.x + r.w * (0.2 + i * 0.2), cy = r.y + r.h * 0.48, rad = r.w * 0.085;
    ctx.fillStyle = hairs[i]; ctx.beginPath(); ctx.arc(cx, cy - rad * 0.2, rad * 1.18, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = skins[i]; ctx.beginPath(); ctx.arc(cx, cy, rad, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#3a1f14'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.arc(cx, cy + rad * 0.15, rad * 0.45, 0.2, Math.PI - 0.2); ctx.stroke();
    ctx.fillStyle = ['#b98386', '#34425c', '#c4923c', '#3f5946'][i];
    ctx.fillRect(cx - rad * 1.2, cy + rad * 1.1, rad * 2.4, r.h * 0.4);
  }
  ctx.fillStyle = 'rgba(255,255,255,0.12)';
  ctx.beginPath(); ctx.moveTo(r.x, r.y); ctx.lineTo(r.x + r.w * 0.5, r.y); ctx.lineTo(r.x, r.y + r.h * 0.6); ctx.fill();
}
function clockFace(ctx, c) {
  ctx.fillStyle = '#2e1b12'; ctx.beginPath(); ctx.arc(c.x, c.y, c.r + 10, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#efe4d0'; ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#3a2a20'; ctx.lineWidth = 3;
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2;
    ctx.beginPath(); ctx.moveTo(c.x + Math.cos(a) * c.r * 0.8, c.y + Math.sin(a) * c.r * 0.8);
    ctx.lineTo(c.x + Math.cos(a) * c.r * 0.92, c.y + Math.sin(a) * c.r * 0.92); ctx.stroke();
  }
}
function clockHands(ctx, c, t) {
  const sec = Math.floor(t) % 60;
  const hands = [[(7 + 40 / 60) / 12, 0.5, 6], [(40 + t / 60) / 60, 0.75, 4], [sec / 60, 0.85, 2]];
  ctx.save();
  ctx.lineCap = 'round';
  for (const [f, len, wdt] of hands) {
    const a = f * Math.PI * 2 - Math.PI / 2;
    ctx.strokeStyle = wdt === 2 ? '#a3302a' : '#2a1d16'; ctx.lineWidth = wdt;
    ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(c.x + Math.cos(a) * c.r * len, c.y + Math.sin(a) * c.r * len); ctx.stroke();
  }
  ctx.fillStyle = '#2a1d16'; ctx.beginPath(); ctx.arc(c.x, c.y, 5, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function hutch(ctx, r) {
  ctx.fillStyle = '#4a2a1a'; ctx.fillRect(r.x, r.y, r.w, r.h);
  ctx.fillStyle = '#2c180f'; ctx.fillRect(r.x + 16, r.y + 16, r.w - 32, r.h * 0.5);
  for (let i = 0; i < 4; i++) { // plates on display
    ctx.fillStyle = '#e9e0cf'; ctx.beginPath(); ctx.arc(r.x + r.w * (0.2 + i * 0.2), r.y + r.h * 0.22, r.w * 0.075, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#7a4a40'; ctx.lineWidth = 3; ctx.stroke();
  }
  ctx.fillStyle = 'rgba(255,220,170,0.15)'; ctx.fillRect(r.x + 16, r.y + 16, r.w * 0.3, r.h * 0.5);
}

function pendantLamp(ctx, x, y, s = 1, glowA = 1) {
  ctx.save();
  ctx.strokeStyle = '#1c120c'; ctx.lineWidth = 4 * s;
  ctx.beginPath(); ctx.moveTo(x, -10); ctx.lineTo(x, y - 60 * s); ctx.stroke();
  // light cone
  ctx.globalCompositeOperation = 'lighter';
  const cone = ctx.createLinearGradient(0, y, 0, y + 900 * s);
  cone.addColorStop(0, `rgba(255,200,130,${0.22 * glowA})`);
  cone.addColorStop(1, 'rgba(255,200,130,0)');
  ctx.fillStyle = cone;
  ctx.beginPath(); ctx.moveTo(x - 120 * s, y); ctx.lineTo(x + 120 * s, y); ctx.lineTo(x + 520 * s, y + 900 * s); ctx.lineTo(x - 520 * s, y + 900 * s); ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  // shade
  ctx.fillStyle = grad(ctx, x - 140 * s, 0, x + 140 * s, 0, [[0, [46, 30, 22]], [0.5, [110, 74, 48]], [1, [40, 26, 18]]]);
  ctx.beginPath(); ctx.moveTo(x - 30 * s, y - 70 * s); ctx.lineTo(x + 30 * s, y - 70 * s);
  ctx.quadraticCurveTo(x + 140 * s, y - 40 * s, x + 145 * s, y); ctx.lineTo(x - 145 * s, y);
  ctx.quadraticCurveTo(x - 140 * s, y - 40 * s, x - 30 * s, y - 70 * s); ctx.fill();
  ctx.fillStyle = `rgba(255,236,190,${0.95 * glowA})`;
  ctx.beginPath(); ctx.ellipse(x, y, 140 * s, 18 * s, 0, 0, Math.PI * 2); ctx.fill();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = radial(ctx, x, y + 10, 4, 300 * s, [[0, [255, 210, 140], 0.6 * glowA], [1, [255, 160, 80], 0]]);
  ctx.beginPath(); ctx.arc(x, y + 10, 300 * s, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

// The table seen across from Maya's side: far edge at y0, near edge below frame.
function diningTable(ctx, w, h, y0) {
  ctx.fillStyle = grad(ctx, 0, y0, 0, h, [[0, [236, 222, 196]], [0.4, [214, 196, 168]], [1, [150, 128, 104]]]);
  ctx.beginPath(); ctx.moveTo(-40, y0 + 40); ctx.lineTo(w + 40, y0 + 40); ctx.lineTo(w + 40, h); ctx.lineTo(-40, h); ctx.fill();
  ctx.fillStyle = grad(ctx, 0, y0, 0, y0 + 60, [[0, [246, 236, 214]], [1, [226, 210, 182]]]);
  ctx.beginPath(); ctx.moveTo(-40, y0); ctx.lineTo(w + 40, y0); ctx.lineTo(w + 40, y0 + 46); ctx.lineTo(-40, y0 + 46); ctx.fill();
  ctx.fillStyle = 'rgba(80,50,30,0.25)'; ctx.fillRect(-40, y0 - 4, w + 80, 6);
}
function plate(ctx, x, y, rx, food = true, seed = 1) {
  ctx.save();
  ctx.fillStyle = 'rgba(60,40,30,0.25)';
  ctx.beginPath(); ctx.ellipse(x, y + rx * 0.12, rx * 1.02, rx * 0.36, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#f6f1e8'; ctx.beginPath(); ctx.ellipse(x, y, rx, rx * 0.33, 0, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#c9b89a'; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(x, y, rx * 0.72, rx * 0.23, 0, 0, Math.PI * 2); ctx.stroke();
  if (food) {
    const r = rng(seed);
    ctx.fillStyle = '#8a4b2c'; ctx.beginPath(); ctx.ellipse(x - rx * 0.2, y - rx * 0.04, rx * 0.3, rx * 0.12, 0.1, 0, Math.PI * 2); ctx.fill();
    for (let i = 0; i < 5; i++) {
      ctx.fillStyle = '#e8c56a';
      ctx.beginPath(); ctx.ellipse(x + rx * (0.15 + r() * 0.3), y + rx * (r() * 0.12 - 0.06), rx * 0.09, rx * 0.06, 0, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = '#5f8a3a';
    for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.ellipse(x - rx * 0.1 + r() * rx * 0.3, y + rx * 0.1, rx * 0.08, rx * 0.04, r(), 0, Math.PI * 2); ctx.fill(); }
  }
  ctx.restore();
}
function glass(ctx, x, y, s = 1) {
  ctx.save();
  ctx.fillStyle = 'rgba(220,235,245,0.35)';
  ctx.beginPath(); ctx.moveTo(x - 18 * s, y - 70 * s); ctx.lineTo(x + 18 * s, y - 70 * s); ctx.lineTo(x + 14 * s, y); ctx.lineTo(x - 14 * s, y); ctx.fill();
  ctx.fillStyle = 'rgba(150,40,50,0.6)';
  ctx.beginPath(); ctx.moveTo(x - 16 * s, y - 35 * s); ctx.lineTo(x + 16 * s, y - 35 * s); ctx.lineTo(x + 14 * s, y); ctx.lineTo(x - 14 * s, y); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(x - 10 * s, y - 64 * s); ctx.lineTo(x - 8 * s, y - 8 * s); ctx.stroke();
  ctx.restore();
}
function servingDish(ctx, x, y, s = 1) {
  ctx.save();
  ctx.fillStyle = 'rgba(60,40,30,0.3)'; ctx.beginPath(); ctx.ellipse(x, y + 14 * s, 150 * s, 40 * s, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#efe6d6'; ctx.beginPath(); ctx.ellipse(x, y, 145 * s, 46 * s, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#9c5a33'; ctx.beginPath(); ctx.ellipse(x, y - 12 * s, 95 * s, 34 * s, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(255,220,170,0.4)'; ctx.beginPath(); ctx.ellipse(x - 30 * s, y - 24 * s, 40 * s, 10 * s, -0.2, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function candle(ctx, x, y, t, s = 1) {
  ctx.save();
  ctx.fillStyle = '#efe4cc'; ctx.fillRect(x - 9 * s, y - 90 * s, 18 * s, 90 * s);
  const fl = 1 + 0.12 * Math.sin(t * 13 + x) + 0.08 * Math.sin(t * 23 + x * 2);
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = radial(ctx, x, y - 104 * s, 1, 70 * s * fl, [[0, [255, 200, 120], 0.55], [1, [255, 140, 60], 0]]);
  ctx.beginPath(); ctx.arc(x, y - 104 * s, 70 * s * fl, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(255,240,200,0.95)';
  ctx.beginPath(); ctx.ellipse(x, y - 104 * s, 6 * s, 14 * s * fl, 0, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

module.exports = {
  grad, radial, diningWall, window_, photoFrame, clockFace, clockHands, hutch, pendantLamp,
  diningTable, plate, glass, servingDish, candle, roundRect,
};
