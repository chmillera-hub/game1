'use strict';
// Night sets: bathroom mirror, bedroom, and the AI chat screen.

const { clamp, lerp, rgbStr, rng, smooth } = require('./util');
const { grad, radial } = require('./sets');
const { roundRect } = require('./body');
const { wrap } = require('./text');

function bathroom(ctx, w, h) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, [40, 58, 62]], [0.6, [62, 84, 86]], [1, [28, 38, 40]]]);
  ctx.fillRect(0, 0, w, h);
  // tiles
  ctx.strokeStyle = 'rgba(200,230,230,0.08)'; ctx.lineWidth = 3;
  for (let y = 0; y < h; y += 96) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
  for (let x = 0; x < w; x += 96) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
  // vanity light glow
  ctx.fillStyle = radial(ctx, 340, 150, 10, 700, [[0, [235, 245, 230], 0.5], [0.4, [170, 200, 190], 0.15], [1, [0, 0, 0], 0]]);
  ctx.fillRect(0, 0, w, h);
  // sink counter
  ctx.fillStyle = grad(ctx, 0, 1560, 0, h, [[0, [210, 214, 206]], [0.1, [150, 156, 150]], [1, [60, 64, 62]]]);
  ctx.fillRect(0, 1560, w, h - 1560);
}
function vanityLight(ctx, x, y, wdt) {
  ctx.save();
  ctx.fillStyle = '#d8dccf';
  roundRect(ctx, x - wdt / 2, y - 18, wdt, 36, 18); ctx.fill();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = radial(ctx, x, y, 5, wdt * 0.7, [[0, [240, 250, 235], 0.5], [1, [0, 0, 0], 0]]);
  ctx.beginPath(); ctx.arc(x, y, wdt * 0.7, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
// Mirror frame + glass; the reflection is drawn by the scene inside the clip.
function mirrorGlass(ctx, r) {
  ctx.fillStyle = grad(ctx, r.x, r.y, r.x + r.w, r.y + r.h, [[0, [54, 70, 74]], [1, [30, 40, 44]]]);
  roundRect(ctx, r.x, r.y, r.w, r.h, 26); ctx.fill();
}
function mirrorFrame(ctx, r, crack = 0) {
  ctx.save();
  // glass sheen
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = 'rgba(255,255,255,0.05)';
  ctx.beginPath(); ctx.moveTo(r.x + r.w * 0.55, r.y); ctx.lineTo(r.x + r.w * 0.8, r.y); ctx.lineTo(r.x + r.w * 0.3, r.y + r.h); ctx.lineTo(r.x + r.w * 0.05, r.y + r.h); ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = '#b9b6a8'; ctx.lineWidth = 16;
  roundRect(ctx, r.x, r.y, r.w, r.h, 26); ctx.stroke();
  ctx.restore();
}

function bedroom(ctx, w, h, o = {}) {
  ctx.fillStyle = grad(ctx, 0, 0, 0, h, [[0, [16, 20, 40]], [0.6, [26, 30, 54]], [1, [10, 10, 20]]]);
  ctx.fillRect(0, 0, w, h);
  // window with the city at night
  const win = o.window || { x: 600, y: 260, w: 420, h: 560 };
  ctx.fillStyle = grad(ctx, 0, win.y, 0, win.y + win.h, [[0, [14, 22, 52]], [1, [48, 50, 92]]]);
  ctx.fillRect(win.x, win.y, win.w, win.h);
  const r = rng(9);
  for (let i = 0; i < 26; i++) {
    const bx = win.x + r() * win.w, bh = win.h * (0.15 + r() * 0.35);
    ctx.fillStyle = 'rgba(8,10,24,0.9)';
    ctx.fillRect(bx, win.y + win.h - bh, 30 + r() * 40, bh);
    for (let k = 0; k < 4; k++) if (r() < 0.6) { ctx.fillStyle = `rgba(255,${200 + r() * 40},${130 + r() * 60},0.8)`; ctx.fillRect(bx + 6 + r() * 20, win.y + win.h - bh + 10 + r() * (bh - 20), 5, 7); }
  }
  ctx.fillStyle = 'rgba(240,240,255,0.85)'; ctx.beginPath(); ctx.arc(win.x + win.w * 0.75, win.y + 90, 34, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = radial(ctx, win.x + win.w * 0.75, win.y + 90, 30, 200, [[0, [200, 210, 255], 0.25], [1, [0, 0, 0], 0]]);
  ctx.fillRect(win.x, win.y, win.w, win.h);
  ctx.strokeStyle = '#2a2c44'; ctx.lineWidth = 16; ctx.strokeRect(win.x, win.y, win.w, win.h);
  ctx.lineWidth = 8;
  ctx.beginPath(); ctx.moveTo(win.x + win.w / 2, win.y); ctx.lineTo(win.x + win.w / 2, win.y + win.h); ctx.moveTo(win.x, win.y + win.h / 2); ctx.lineTo(win.x + win.w, win.y + win.h / 2); ctx.stroke();
  // fairy lights along the wall
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 14; i++) {
    const x = 40 + i * 42, y = 300 + Math.sin(i * 0.7) * 30 + i * 6;
    ctx.fillStyle = radial(ctx, x, y, 1, 40, [[0, [255, 210, 140], 0.55], [1, [255, 170, 80], 0]]);
    ctx.beginPath(); ctx.arc(x, y, 40, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
  // headboard + bed
  ctx.fillStyle = grad(ctx, 0, 1050, 0, 1500, [[0, [56, 46, 70]], [1, [30, 24, 40]]]);
  roundRect(ctx, 80, 1050, 920, 460, 40); ctx.fill();
  ctx.fillStyle = grad(ctx, 0, 1450, 0, h, [[0, [120, 120, 150]], [1, [40, 40, 60]]]);
  ctx.fillRect(0, 1450, w, h - 1450);
}

// The chat app on a screen. msgs: [{from:'me'|'ai', text, t0, t1}] (t1 = fully typed)
function chatScreen(ctx, r, t, msgs, orb) {
  ctx.save();
  ctx.fillStyle = '#0d1018';
  roundRect(ctx, r.x, r.y, r.w, r.h, 30); ctx.fill();
  ctx.beginPath(); roundRect(ctx, r.x, r.y, r.w, r.h, 30); ctx.clip();
  ctx.fillStyle = grad(ctx, 0, r.y, 0, r.y + r.h, [[0, [22, 26, 40]], [1, [12, 14, 22]]]);
  ctx.fillRect(r.x, r.y, r.w, r.h);
  // orb
  const ox = r.x + r.w / 2, oy = r.y + 170;
  const pulse = orb.level || 0;
  const breathe = 0.5 + 0.5 * Math.sin(t * 1.6);
  ctx.globalCompositeOperation = 'lighter';
  for (const [rad, a] of [[150 + pulse * 70, 0.14], [100 + pulse * 40, 0.22], [62 + pulse * 18, 0.5]]) {
    ctx.fillStyle = radial(ctx, ox, oy, 2, rad, [[0, [190, 225, 255], a + 0.1 * breathe], [0.6, [120, 170, 255], a * 0.4], [1, [80, 120, 220], 0]]);
    ctx.beginPath(); ctx.arc(ox, oy, rad, 0, Math.PI * 2); ctx.fill();
  }
  // ripples while it speaks
  for (let k = 0; k < 3; k++) {
    const ph = ((t * 0.9 + k / 3) % 1);
    ctx.strokeStyle = `rgba(170,210,255,${(1 - ph) * 0.35 * clamp(pulse * 3)})`;
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(ox, oy, 60 + ph * 140, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.globalCompositeOperation = 'source-over';
  // messages (newest at the bottom)
  ctx.font = '46px InterMed';
  ctx.textBaseline = 'top';
  const pad = 28, maxW = r.w * 0.8;
  let y = r.y + r.h * 0.8;
  const visible = msgs.filter((m) => t >= m.t0).slice(-2).reverse();
  for (const m of visible) {
    const n = Math.floor(m.text.length * clamp((t - m.t0) / Math.max(0.01, m.t1 - m.t0)));
    const shown = m.text.slice(0, n) + (n < m.text.length && Math.floor(t * 3) % 2 ? '|' : '');
    const rows = wrap(ctx, shown || ' ', maxW - pad * 2);
    const bh = rows.length * 58 + pad * 1.4;
    y -= bh;
    const bw = Math.min(maxW, Math.max(...rows.map((q) => ctx.measureText(q).width)) + pad * 2);
    const bx = m.from === 'me' ? r.x + r.w - bw - 30 : r.x + 30;
    ctx.fillStyle = m.from === 'me' ? 'rgba(92,110,170,0.95)' : 'rgba(36,44,66,0.95)';
    roundRect(ctx, bx, y, bw, bh, 24); ctx.fill();
    ctx.fillStyle = m.from === 'me' ? '#f2f4ff' : '#d6e8ff';
    rows.forEach((q, i) => ctx.fillText(q, bx + pad, y + pad * 0.7 + i * 58));
    y -= 22;
  }
  ctx.restore();
  // bezel
  ctx.save(); ctx.strokeStyle = '#2b2f3a'; ctx.lineWidth = 10; roundRect(ctx, r.x, r.y, r.w, r.h, 30); ctx.stroke(); ctx.restore();
}

module.exports = { bathroom, vanityLight, mirrorGlass, mirrorFrame, bedroom, chatScreen };
