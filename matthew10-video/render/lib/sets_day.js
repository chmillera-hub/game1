'use strict';
// Day sets: office, park, kitchen, the road, the new office, the sunrise window.

const { clamp, lerp, rgbStr, rng, smooth } = require('./util');
const { grad, radial } = require('./sets');
const { roundRect } = require('./body');

// ------------------------------------------------------------ office
function office(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, [168, 176, 170]], [0.5, [130, 140, 136]], [1, [70, 76, 74]]]);
  ctx.fillRect(0, 0, w, h);
  // ceiling grid
  ctx.fillStyle = grad(ctx, 0, 0, 0, 380, [[0, [190, 196, 190]], [1, [150, 158, 154]]]);
  ctx.fillRect(0, 0, w, 380);
  ctx.strokeStyle = 'rgba(90,100,96,0.5)'; ctx.lineWidth = 3;
  for (let i = -6; i <= 6; i++) { ctx.beginPath(); ctx.moveTo(w / 2 + i * 60, 380); ctx.lineTo(w / 2 + i * 260, 0); ctx.stroke(); }
  for (const y of [60, 160, 260, 340]) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
  // far wall windows (grey daylight)
  ctx.fillStyle = 'rgba(200,212,214,0.7)';
  for (let i = 0; i < 6; i++) ctx.fillRect(30 + i * 180, 420, 140, 260);
  // rows of cubicles and coworkers in the distance
  const r = rng(12);
  for (let row = 0; row < 3; row++) {
    const y = 760 + row * 120, s = 0.6 + row * 0.25;
    for (let i = 0; i < 6; i++) {
      const x = 60 + i * 190 + (row % 2) * 80 + r() * 20;
      ctx.fillStyle = `rgba(${60 + r() * 60},${60 + r() * 50},${70 + r() * 50},0.85)`;
      ctx.beginPath(); ctx.arc(x, y - 40 * s, 22 * s, 0, Math.PI * 2); ctx.fill();
      ctx.fillRect(x - 30 * s, y - 20 * s, 60 * s, 60 * s);
      ctx.fillStyle = 'rgba(160,210,230,0.5)'; ctx.fillRect(x + 30 * s, y - 50 * s, 50 * s, 34 * s);
    }
    ctx.fillStyle = grad(ctx, 0, y, 0, y + 90 * s, [[0, [104, 112, 124]], [1, [84, 90, 100]]]);
    ctx.fillRect(0, y + 20 * s, w, 90 * s);
  }
  ctx.fillStyle = grad(ctx, 0, 1200, 0, h, [[0, [92, 96, 104]], [1, [52, 54, 60]]]);
  ctx.fillRect(0, 1200, w, h - 1200);
}
// Fluorescent panels on the ceiling; `flick` 0..1 dims one panel.
function ceilingLights(ctx, w, flick = 0, buzz = 0) {
  const panels = [[w * 0.5, 120, 340, 70], [w * 0.12, 210, 300, 60], [w * 0.88, 210, 300, 60], [w * 0.5, 300, 260, 46]];
  panels.forEach(([x, y, pw, ph], i) => {
    const a = i === 0 ? 1 - flick : 1 - buzz * 0.3;
    ctx.fillStyle = `rgba(242,250,240,${0.6 + 0.4 * a})`;
    ctx.fillRect(x - pw / 2, y - ph / 2, pw, ph);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = radial(ctx, x, y, 10, pw, [[0, [225, 245, 230], 0.35 * a], [1, [0, 0, 0], 0]]);
    ctx.beginPath(); ctx.arc(x, y, pw, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  });
}
function cubicleWall(ctx, x, y, w, h) {
  ctx.fillStyle = grad(ctx, 0, y, 0, y + h, [[0, [110, 118, 134]], [1, [78, 84, 98]]]);
  ctx.fillRect(x, y, w, h);
  ctx.fillStyle = '#c3c7cc'; ctx.fillRect(x, y - 14, w, 18);
  ctx.globalAlpha = 0.12;
  for (let i = 0; i < w; i += 8) { ctx.fillStyle = i % 16 ? '#000' : '#fff'; ctx.fillRect(x + i, y, 4, h); }
  ctx.globalAlpha = 1;
}
function monitor(ctx, x, y, w, h, glow = [170, 210, 235]) {
  ctx.fillStyle = '#1c1e24'; roundRect(ctx, x, y, w, h, 12); ctx.fill();
  ctx.fillStyle = rgbStr(glow, 0.9); ctx.fillRect(x + 14, y + 14, w - 28, h - 28);
  ctx.fillStyle = 'rgba(40,60,80,0.5)';
  for (let i = 0; i < 6; i++) ctx.fillRect(x + 30, y + 40 + i * 30, (w - 60) * (0.4 + ((i * 37) % 50) / 100), 10);
  ctx.fillStyle = '#2a2c33'; ctx.fillRect(x + w / 2 - 20, y + h, 40, 60);
}
function desk(ctx, y, w, h) {
  ctx.fillStyle = grad(ctx, 0, y, 0, h, [[0, [188, 176, 156]], [0.08, [150, 138, 120]], [1, [80, 74, 66]]]);
  ctx.fillRect(0, y, w, h - y);
}

// ------------------------------------------------------------ park at golden hour
function park(ctx, w, h, o = {}) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h * 0.62, [[0, [86, 104, 160]], [0.45, [230, 160, 120]], [1, [252, 206, 140]]]);
  ctx.fillRect(0, 0, w, h);
  // low sun
  const sx = o.sunX ?? w * 0.72, sy = o.sunY ?? h * 0.5;
  ctx.fillStyle = radial(ctx, sx, sy, 10, 600, [[0, [255, 240, 200], 0.95], [0.12, [255, 210, 150], 0.6], [1, [255, 180, 120], 0]]);
  ctx.fillRect(0, 0, w, h);
  // distant tree line
  const r = rng(4);
  ctx.fillStyle = 'rgba(70,60,70,0.7)';
  for (let i = 0; i < 18; i++) { const x = i * 70 + r() * 30; ctx.beginPath(); ctx.arc(x, h * 0.6, 60 + r() * 50, Math.PI, 0); ctx.fill(); }
  // grass
  ctx.fillStyle = grad(ctx, 0, h * 0.6, 0, h, [[0, [120, 120, 70]], [1, [40, 50, 30]]]);
  ctx.fillRect(0, h * 0.6, w, h * 0.4);
  // path
  ctx.fillStyle = 'rgba(230,200,160,0.35)';
  ctx.beginPath(); ctx.moveTo(w * 0.45, h * 0.6); ctx.lineTo(w * 0.55, h * 0.6); ctx.lineTo(w * 0.95, h); ctx.lineTo(w * 0.15, h); ctx.fill();
  // big tree silhouette on the left
  if (o.tree !== false) {
    ctx.fillStyle = '#2a2224';
    ctx.fillRect(40, h * 0.18, 70, h * 0.5);
    for (const [x, y, rr] of [[60, 220, 260], [220, 140, 200], [-60, 360, 220], [180, 380, 180], [330, 260, 140]]) { ctx.beginPath(); ctx.arc(x, y, rr, 0, Math.PI * 2); ctx.fill(); }
  }
  // lamp post
  ctx.fillStyle = '#26201f'; ctx.fillRect(w * 0.86, h * 0.28, 12, h * 0.4);
  ctx.beginPath(); ctx.arc(w * 0.86 + 6, h * 0.28, 22, 0, Math.PI * 2); ctx.fill();
}
function bench(ctx, x, y, w, s = 1) {
  ctx.fillStyle = '#4a3226';
  for (let i = 0; i < 3; i++) roundRect(ctx, x, y + i * 26 * s, w, 18 * s, 6), ctx.fill();
  ctx.fillStyle = '#3a271e';
  roundRect(ctx, x - 10, y + 96 * s, w + 20, 22 * s, 6); ctx.fill();
  ctx.fillStyle = '#22201f';
  ctx.fillRect(x + 30, y + 110 * s, 16 * s, 160 * s); ctx.fillRect(x + w - 46, y + 110 * s, 16 * s, 160 * s);
}
// A small sparrow. hop: 0..1, look: -1..1 (head turn), flap: wing phase or null
function sparrow(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s * (o.flip ? -1 : 1), s);
  const hop = o.hop || 0;
  ctx.translate(0, -Math.sin(hop * Math.PI) * 20);
  // tail
  ctx.fillStyle = '#5a4030';
  ctx.beginPath(); ctx.moveTo(-26, -8); ctx.lineTo(-58, -2); ctx.lineTo(-54, 8); ctx.lineTo(-24, 6); ctx.fill();
  // body
  ctx.fillStyle = '#8a6448';
  ctx.beginPath(); ctx.ellipse(0, 0, 32, 22, -0.15, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#d9c8b0';
  ctx.beginPath(); ctx.ellipse(6, 8, 24, 13, -0.1, 0, Math.PI * 2); ctx.fill();
  // wing
  if (o.flap !== undefined && o.flap !== null) {
    const a = Math.sin(o.flap) * 1.1;
    ctx.save(); ctx.translate(-4, -8); ctx.rotate(-0.4 - a);
    ctx.fillStyle = '#6b4a34';
    ctx.beginPath(); ctx.ellipse(-14, -10, 30, 12, -0.3, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  } else {
    ctx.fillStyle = '#6b4a34';
    ctx.beginPath(); ctx.ellipse(-6, -4, 22, 12, -0.25, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#3e2a1e'; ctx.lineWidth = 2;
    for (const k of [-10, -2, 6]) { ctx.beginPath(); ctx.moveTo(k - 8, -8); ctx.lineTo(k, 2); ctx.stroke(); }
  }
  // head
  const look = o.look || 0;
  ctx.save(); ctx.translate(28, -14); ctx.rotate(look * 0.3);
  ctx.fillStyle = '#7a5640'; ctx.beginPath(); ctx.arc(0, 0, 15, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#9a7356'; ctx.beginPath(); ctx.arc(2, -4, 11, Math.PI, 0); ctx.fill();
  ctx.fillStyle = '#dac9b2'; ctx.beginPath(); ctx.ellipse(4, 6, 9, 6, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#1a1210'; ctx.beginPath(); ctx.arc(7, -2, 3.2, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(8, -3, 1.1, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#3a2a20'; ctx.beginPath(); ctx.moveTo(13, 0); ctx.lineTo(22, 3); ctx.lineTo(13, 5); ctx.fill();
  ctx.restore();
  // legs
  if (!o.flying) { ctx.strokeStyle = '#4a3428'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(0, 18); ctx.lineTo(-2, 30); ctx.moveTo(8, 18); ctx.lineTo(8, 30); ctx.stroke(); }
  ctx.restore();
}

// ------------------------------------------------------------ Mom's kitchen (evening)
function kitchen(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, [104, 84, 66]], [1, [54, 40, 32]]]);
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = 'rgba(255,210,150,0.25)';
  ctx.fillStyle = radial(ctx, w * 0.25, h * 0.15, 10, w, [[0, [255, 214, 160], 0.45], [1, [0, 0, 0], 0]]);
  ctx.fillRect(0, 0, w, h);
  // cabinets
  ctx.fillStyle = '#6b4e38';
  for (let i = 0; i < 4; i++) { roundRect(ctx, 40 + i * 260, 60, 230, h * 0.32, 10); ctx.fill(); }
  ctx.fillStyle = '#c9c2b4'; ctx.fillRect(0, h * 0.62, w, 26);
  ctx.fillStyle = '#5a4130';
  for (let i = 0; i < 4; i++) { roundRect(ctx, 40 + i * 260, h * 0.66, 230, h * 0.34, 10); ctx.fill(); }
  // window over the sink, evening
  ctx.fillStyle = grad(ctx, 0, h * 0.4, 0, h * 0.6, [[0, [40, 50, 90]], [1, [170, 110, 90]]]);
  ctx.fillRect(w * 0.55, h * 0.38, w * 0.38, h * 0.2);
  ctx.strokeStyle = '#e8dccb'; ctx.lineWidth = 10; ctx.strokeRect(w * 0.55, h * 0.38, w * 0.38, h * 0.2);
}
// Maya's living room (evening, lamp)
function livingRoom(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, [58, 52, 70]], [1, [28, 24, 34]]]);
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = radial(ctx, w * 0.82, h * 0.42, 10, w * 0.9, [[0, [255, 200, 140], 0.5], [1, [0, 0, 0], 0]]);
  ctx.fillRect(0, 0, w, h);
  // bookshelf
  ctx.fillStyle = '#3c2e2a'; ctx.fillRect(40, 300, 360, 900);
  const r = rng(21);
  for (let s = 0; s < 4; s++) for (let i = 0; i < 9; i++) {
    ctx.fillStyle = ['#8a4a3c', '#3f5b6e', '#c49a52', '#6d7a4a', '#7a5f8a'][Math.floor(r() * 5)];
    ctx.fillRect(56 + i * 37, 330 + s * 220 + r() * 20, 30, 170 - r() * 30);
  }
  // lamp
  ctx.fillStyle = '#e8d6b8'; ctx.beginPath(); ctx.moveTo(w * 0.76, h * 0.36); ctx.lineTo(w * 0.88, h * 0.36); ctx.lineTo(w * 0.92, h * 0.46); ctx.lineTo(w * 0.72, h * 0.46); ctx.fill();
  ctx.fillStyle = '#2a2220'; ctx.fillRect(w * 0.815, h * 0.46, 10, h * 0.3);
  // sofa back
  ctx.fillStyle = grad(ctx, 0, h * 0.62, 0, h, [[0, [92, 70, 96]], [1, [44, 34, 48]]]);
  roundRect(ctx, -40, h * 0.62, w + 80, h * 0.5, 60); ctx.fill();
}

// ------------------------------------------------------------ the road at night → dawn
function road(ctx, w, h, t, dawn) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h * 0.55, [[0, [lerp(8, 70, dawn), lerp(10, 80, dawn), lerp(28, 140, dawn)]], [0.7, [lerp(20, 230, dawn), lerp(24, 150, dawn), lerp(50, 120, dawn)]], [1, [lerp(40, 255, dawn), lerp(36, 200, dawn), lerp(60, 140, dawn)]]]);
  ctx.fillRect(0, 0, w, h);
  // stars fade with the dawn
  const r = rng(31);
  for (let i = 0; i < 120; i++) {
    const x = r() * w, y = r() * h * 0.5, tw = 0.5 + 0.5 * Math.sin(t * (1 + r() * 3) + i);
    ctx.fillStyle = `rgba(255,255,255,${(1 - dawn) * (0.3 + 0.6 * tw) * r()})`;
    ctx.fillRect(x, y, 2.4, 2.4);
  }
  // sun glow on the horizon
  ctx.fillStyle = radial(ctx, w / 2, h * 0.55, 10, w, [[0, [255, 210, 150], 0.7 * dawn], [1, [255, 160, 100], 0]]);
  ctx.fillRect(0, 0, w, h);
  // hills
  ctx.fillStyle = `rgb(${lerp(10, 60, dawn)},${lerp(12, 50, dawn)},${lerp(22, 60, dawn)})`;
  ctx.beginPath(); ctx.moveTo(0, h * 0.56);
  for (let x = 0; x <= w; x += 40) ctx.lineTo(x, h * 0.55 - 30 * Math.sin(x / 170) - 20 * Math.sin(x / 61));
  ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.fill();
  // the town ahead, windows lit
  for (let i = 0; i < 16; i++) {
    const bx = w / 2 - 160 + i * 20 + r() * 6, bh = 20 + r() * 40;
    ctx.fillStyle = `rgb(${lerp(14, 70, dawn)},${lerp(14, 56, dawn)},${lerp(24, 60, dawn)})`;
    ctx.fillRect(bx, h * 0.55 - bh, 18, bh);
    ctx.fillStyle = `rgba(255,214,140,${0.9 - dawn * 0.4})`;
    ctx.fillRect(bx + 6, h * 0.55 - bh + 6, 5, 5);
  }
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = radial(ctx, w / 2, h * 0.54, 5, 260, [[0, [255, 200, 120], 0.5], [1, [255, 160, 80], 0]]);
  ctx.beginPath(); ctx.arc(w / 2, h * 0.54, 260, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
  // the road narrowing to the horizon
  ctx.fillStyle = `rgb(${lerp(26, 90, dawn)},${lerp(26, 80, dawn)},${lerp(36, 86, dawn)})`;
  ctx.beginPath(); ctx.moveTo(w / 2 - 8, h * 0.555); ctx.lineTo(w / 2 + 8, h * 0.555); ctx.lineTo(w * 0.95, h); ctx.lineTo(w * 0.05, h); ctx.fill();
  ctx.strokeStyle = `rgba(255,240,200,${0.5})`; ctx.lineWidth = 6; ctx.setLineDash([60, 70]);
  ctx.lineDashOffset = -t * 40;
  ctx.beginPath(); ctx.moveTo(w / 2, h * 0.56); ctx.lineTo(w / 2, h); ctx.stroke();
  ctx.setLineDash([]);
}

// ------------------------------------------------------------ the new office (daylight, plants)
function newOffice(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, [236, 228, 212]], [1, [196, 184, 164]]]);
  ctx.fillRect(0, 0, w, h);
  // tall windows with soft morning light
  for (let i = 0; i < 3; i++) {
    const x = 60 + i * 340;
    ctx.fillStyle = grad(ctx, 0, 120, 0, 1100, [[0, [200, 226, 240]], [1, [250, 240, 220]]]);
    ctx.fillRect(x, 120, 280, 980);
    ctx.strokeStyle = '#f7f2ea'; ctx.lineWidth = 14; ctx.strokeRect(x, 120, 280, 980);
    ctx.beginPath(); ctx.moveTo(x, 600); ctx.lineTo(x + 280, 600); ctx.stroke();
  }
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = 'rgba(255,236,200,0.18)';
  ctx.beginPath(); ctx.moveTo(60, 120); ctx.lineTo(1080, 120); ctx.lineTo(1080, 1500); ctx.lineTo(300, 1920); ctx.lineTo(0, 1920); ctx.fill();
  ctx.restore();
  // plants
  for (const [x, y, s] of [[90, 1250, 1.2], [980, 1180, 1.0], [520, 1100, 0.7]]) plant(ctx, x, y, s);
  ctx.fillStyle = grad(ctx, 0, 1340, 0, h, [[0, [214, 190, 150]], [1, [150, 126, 96]]]);
  ctx.fillRect(0, 1340, w, h - 1340);
}
function plant(ctx, x, y, s) {
  ctx.fillStyle = '#c0704a'; ctx.beginPath(); ctx.moveTo(x - 50 * s, y); ctx.lineTo(x + 50 * s, y); ctx.lineTo(x + 38 * s, y + 90 * s); ctx.lineTo(x - 38 * s, y + 90 * s); ctx.fill();
  const r = rng(Math.floor(x));
  for (let i = 0; i < 9; i++) {
    const a = -Math.PI / 2 + (r() - 0.5) * 2.2, len = (120 + r() * 120) * s;
    ctx.strokeStyle = '#4d7a3c'; ctx.lineWidth = 5 * s;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + Math.cos(a) * len * 0.5, y + Math.sin(a) * len * 0.7, x + Math.cos(a) * len, y + Math.sin(a) * len); ctx.stroke();
    ctx.fillStyle = i % 2 ? '#6c9a4a' : '#5a8a3e';
    ctx.beginPath(); ctx.ellipse(x + Math.cos(a) * len, y + Math.sin(a) * len, 34 * s, 16 * s, a, 0, Math.PI * 2); ctx.fill();
  }
}

module.exports = { office, ceilingLights, cubicleWall, monitor, desk, park, bench, sparrow, kitchen, livingRoom, road, newOffice, plant };
