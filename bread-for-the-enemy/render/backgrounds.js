// Environment painters. All coordinates in the 1080x1920 virtual frame.
'use strict';
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade } = L;
const B = require('./body');

const VW = 1080, VH = 1920;

function fillGrad(ctx, stops, x0 = 0, y0 = 0, x1 = 0, y1 = VH) {
  ctx.fillStyle = L.linear(ctx, x0, y0, x1, y1, stops);
  ctx.fillRect(-200, -200, VW + 400, VH + 400);
}
function vignette(ctx, a = 0.5, color = '#000000', inner = 0.45) {
  ctx.fillStyle = L.radial(ctx, VW / 2, VH * 0.45, VH * inner * 0.5, VH * 0.85, [[0, rgba(color, 0)], [1, rgba(color, a)]]);
  ctx.fillRect(0, 0, VW, VH);
}
function stones(ctx, x0, y0, x1, y1, o) {
  // irregular stone blocks
  const r = L.rng(o.seed || 7);
  const bh = o.bh || 110;
  let y = y0;
  let row = 0;
  while (y < y1) {
    const h = bh * (0.8 + r() * 0.4);
    let x = x0 - (row % 2 ? bh * 0.7 : 0) - r() * bh;
    while (x < x1) {
      const w = bh * (1.3 + r() * 1.2);
      const c = mix(o.base, o.var || shade(o.base, 1.15), r());
      ctx.fillStyle = c;
      ctx.beginPath();
      const rr = 10 + r() * 14;
      ctx.roundRect(x + 4, y + 4, w - 8, h - 8, rr);
      ctx.fill();
      // top highlight / bottom shade
      ctx.fillStyle = rgba('#ffffff', 0.05 + r() * 0.04);
      ctx.fillRect(x + 10, y + 6, w - 20, h * 0.18);
      ctx.fillStyle = rgba('#000000', 0.12);
      ctx.fillRect(x + 8, y + h - h * 0.22, w - 16, h * 0.16);
      x += w;
    }
    y += h;
    row++;
  }
}
function lightShaft(ctx, top, bottom, wTop, wBot, color, a) {
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createLinearGradient(top[0], top[1], bottom[0], bottom[1]);
  g.addColorStop(0, rgba(color, a));
  g.addColorStop(0.7, rgba(color, a * 0.45));
  g.addColorStop(1, rgba(color, 0));
  ctx.fillStyle = g;
  ctx.filter = 'blur(14px)';
  ctx.beginPath();
  ctx.moveTo(top[0] - wTop / 2, top[1]);
  ctx.lineTo(top[0] + wTop / 2, top[1]);
  ctx.lineTo(bottom[0] + wBot / 2, bottom[1]);
  ctx.lineTo(bottom[0] - wBot / 2, bottom[1]);
  ctx.closePath();
  ctx.fill();
  ctx.filter = 'none';
  ctx.restore();
}
function dust(ctx, t, region, n, color, seed = 3, a = 0.6, size = 3) {
  // floating motes inside a region {x,y,w,h}
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const hx = L.hash01(i * 13 + seed), hy = L.hash01(i * 29 + seed * 3), hs = L.hash01(i * 7 + seed * 5);
    const x = region.x + ((hx * region.w + Math.sin(t * 0.3 + i) * 18 + t * 6 * (hs - 0.5)) % region.w + region.w) % region.w;
    const y = region.y + ((hy * region.h - t * (8 + hs * 10)) % region.h + region.h) % region.h;
    const tw = 0.5 + 0.5 * Math.sin(t * (1 + hs * 2) + i);
    ctx.fillStyle = rgba(color, a * tw);
    ctx.beginPath(); ctx.arc(x, y, size * (0.6 + hs), 0, L.TAU); ctx.fill();
  }
  ctx.restore();
}
function bokeh(ctx, pts, color, a = 0.35) {
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (const [x, y, r] of pts) {
    ctx.fillStyle = L.radial(ctx, x, y, r * 0.6, r, [[0, rgba(color, a)], [0.85, rgba(color, a * 0.8)], [1, rgba(color, 0)]]);
    ctx.beginPath(); ctx.arc(x, y, r, 0, L.TAU); ctx.fill();
  }
  ctx.restore();
}

// =================================================================== UPPER ROOM
function upperRoom(ctx, o = {}) {
  fillGrad(ctx, [[0, '#2a1810'], [0.45, '#4a2c1a'], [1, '#1e120c']]);
  // plaster wall variation
  ctx.fillStyle = L.radial(ctx, 380, 700, 50, 900, [[0, rgba('#a8673a', 0.55)], [1, rgba('#a8673a', 0)]]);
  ctx.fillRect(0, 0, VW, VH);
  // arched window (night)
  const wx = 820, wy = 380, ww = 260, wh = 420;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(wx - ww / 2, wy + wh / 2); ctx.lineTo(wx - ww / 2, wy - wh / 2 + ww / 2);
  ctx.arc(wx, wy - wh / 2 + ww / 2, ww / 2, Math.PI, 0); ctx.lineTo(wx + ww / 2, wy + wh / 2); ctx.closePath();
  ctx.fillStyle = L.linear(ctx, 0, wy - wh / 2, 0, wy + wh / 2, [[0, '#0d1a3a'], [1, '#24365e']]);
  ctx.fill();
  ctx.clip();
  for (let i = 0; i < 18; i++) {
    const x = wx - ww / 2 + L.hash01(i * 3) * ww, y = wy - wh / 2 + L.hash01(i * 5 + 1) * wh * 0.8;
    ctx.fillStyle = rgba('#ffffff', 0.5 + 0.5 * L.hash01(i));
    ctx.beginPath(); ctx.arc(x, y, 1.6 + L.hash01(i * 9) * 1.8, 0, L.TAU); ctx.fill();
  }
  // distant city silhouette
  ctx.fillStyle = '#0a1024';
  ctx.beginPath(); ctx.moveTo(wx - ww / 2, wy + wh / 2);
  for (let i = 0; i <= 8; i++) ctx.lineTo(wx - ww / 2 + i * ww / 8, wy + wh / 2 - 60 - 40 * L.hash01(i * 7));
  ctx.lineTo(wx + ww / 2, wy + wh / 2); ctx.fill();
  ctx.restore();
  ctx.strokeStyle = '#1a0e08'; ctx.lineWidth = 18;
  ctx.beginPath(); ctx.moveTo(wx - ww / 2, wy + wh / 2); ctx.lineTo(wx - ww / 2, wy - wh / 2 + ww / 2); ctx.arc(wx, wy - wh / 2 + ww / 2, ww / 2, Math.PI, 0); ctx.lineTo(wx + ww / 2, wy + wh / 2); ctx.stroke();
  // wall niche lamp glow (left)
  L.glow(ctx, 170, 640, 420, '#ffb060', 0.5);
  // wooden beams top
  ctx.fillStyle = '#1a0e08';
  ctx.fillRect(0, 0, VW, 90);
  ctx.fillStyle = rgba('#000000', 0.35);
  ctx.fillRect(0, 90, VW, 40);
  // table
  const ty = o.tableY || 1500;
  ctx.fillStyle = L.linear(ctx, 0, ty, 0, VH, [[0, '#6a3f22'], [0.08, '#4a2a16'], [1, '#2a170c']]);
  ctx.fillRect(0, ty, VW, VH - ty);
  ctx.fillStyle = rgba('#ffcf8a', 0.25);
  ctx.fillRect(0, ty, VW, 10);
  // wood grain
  ctx.strokeStyle = rgba('#20100a', 0.35); ctx.lineWidth = 3;
  for (let i = 0; i < 9; i++) { const y = ty + 40 + i * 50; ctx.beginPath(); ctx.moveTo(0, y); ctx.bezierCurveTo(300, y + 10, 700, y - 12, VW, y + 6); ctx.stroke(); }
  // table lamps (bokeh)
  bokeh(ctx, [[120, ty - 30, 70], [960, ty - 40, 90], [700, ty + 60, 50]], '#ffb35a', 0.45);
  vignette(ctx, 0.55);
}
function upperRoomDyn(ctx, t, o = {}) {
  const f = 0.85 + 0.15 * L.fbm1(t * 2.2, 5);
  L.glow(ctx, 170, 640, 260, '#ffc070', 0.18 * f);
  L.glow(ctx, 960, (o.tableY || 1500) - 40, 160, '#ffb050', 0.25 * f);
}

// =================================================================== STREET NIGHT
function streetNight(ctx, o = {}) {
  fillGrad(ctx, [[0, '#070c1c'], [0.3, '#0f1a33'], [1, '#0a0f1c']]);
  // moon glow upper right
  L.glow(ctx, 900, 160, 380, '#9fb8ff', 0.35);
  ctx.fillStyle = '#eef3ff';
  ctx.beginPath(); ctx.arc(900, 160, 46, 0, L.TAU); ctx.fill();
  // prison wall (big stone)
  // the wall stands on the street: the door's sill is level with the cobbles (y = GROUND)
  const GROUND = 1370;
  ctx.save();
  ctx.beginPath(); ctx.rect(0, 260, VW, GROUND - 260);
  ctx.clip();
  grimyStones(ctx, -40, 260, VW + 40, GROUND + 20, { base: '#343b48', var: '#444a54', bh: 120, seed: 11 });
  // soot blackening above the torch, and grime and splashed mud gathered where the wall meets the street
  ctx.fillStyle = L.radial(ctx, 195, 560, 0, 260, [[0, rgba('#020203', 0.55)], [1, rgba('#020203', 0)]]);
  ctx.fillRect(0, 300, 460, 520);
  ctx.fillStyle = L.linear(ctx, 0, GROUND - 190, 0, GROUND, [[0, rgba('#0a0806', 0)], [0.7, rgba('#140e08', 0.4)], [1, rgba('#0a0806', 0.7)]]);
  ctx.fillRect(0, GROUND - 190, VW, 190);
  const rs = L.rng(77);
  for (let i = 0; i < 60; i++) {
    const x = rs() * VW, y = GROUND - rs() * 120, r = 4 + rs() * 16;
    ctx.fillStyle = rgba(rs() < 0.5 ? '#1e140a' : '#0c0a08', 0.25 + rs() * 0.3);
    ctx.beginPath(); ctx.ellipse(x, y, r, r * (0.5 + rs() * 0.5), 0, 0, L.TAU); ctx.fill();
  }
  ctx.restore();
  // wall darkening toward top
  ctx.fillStyle = L.linear(ctx, 0, 260, 0, 900, [[0, rgba('#05070e', 0.75)], [1, rgba('#05070e', 0)]]);
  ctx.fillRect(0, 260, VW, 700);
  // door
  const dx = 540, dy = 1020, dw = 400, dh = 700;
  if (o.noDoor) {
    // only the dark frame of the doorway: the leaf is drawn by the shot (so it can swing open)
    ctx.fillStyle = '#0a0806';
    ctx.beginPath(); ctx.roundRect(dx - dw / 2 - 30, dy - dh / 2 - 30, dw + 60, dh + 60, [200, 200, 0, 0]); ctx.fill();
  } else {
  ctx.fillStyle = '#0a0806';
  ctx.beginPath(); ctx.roundRect(dx - dw / 2 - 30, dy - dh / 2 - 30, dw + 60, dh + 60, [200, 200, 0, 0]); ctx.fill();
  ctx.fillStyle = L.linear(ctx, dx - dw / 2, 0, dx + dw / 2, 0, [[0, '#4a3020'], [0.5, '#3a2416'], [1, '#2a180e']]);
  ctx.beginPath(); ctx.roundRect(dx - dw / 2, dy - dh / 2, dw, dh, [180, 180, 0, 0]); ctx.fill();
  ctx.strokeStyle = rgba('#140a04', 0.8); ctx.lineWidth = 5;
  for (let i = 1; i < 5; i++) { ctx.beginPath(); ctx.moveTo(dx - dw / 2 + i * dw / 5, dy - dh / 2 + 20); ctx.lineTo(dx - dw / 2 + i * dw / 5, dy + dh / 2); ctx.stroke(); }
  // iron bands + studs
  for (const by of [dy - dh * 0.28, dy + dh * 0.05, dy + dh * 0.36]) {
    ctx.fillStyle = '#1c1c20'; ctx.fillRect(dx - dw / 2, by - 16, dw, 32);
    ctx.fillStyle = rgba('#9aa6c8', 0.25); ctx.fillRect(dx - dw / 2, by - 16, dw, 6);
    for (let i = 0; i < 7; i++) { ctx.fillStyle = '#2c2c30'; ctx.beginPath(); ctx.arc(dx - dw / 2 + 30 + i * (dw - 60) / 6, by, 9, 0, L.TAU); ctx.fill(); }
  }
  // grille window in door
  ctx.fillStyle = '#050403'; ctx.fillRect(dx - 60, dy - dh * 0.42, 120, 70);
  ctx.strokeStyle = '#2a2a2e'; ctx.lineWidth = 7;
  for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(dx - 45 + i * 30, dy - dh * 0.42); ctx.lineTo(dx - 45 + i * 30, dy - dh * 0.42 + 70); ctx.stroke(); }
  // weathering on the planks
  ctx.save(); ctx.beginPath(); ctx.roundRect(dx - dw / 2, dy - dh / 2, dw, dh, [180, 180, 0, 0]); ctx.clip();
  const rw = L.rng(23);
  for (let i = 0; i < 40; i++) {
    const x = dx - dw / 2 + rw() * dw, y = dy - dh / 2 + rw() * dh;
    ctx.strokeStyle = rgba(rw() < 0.5 ? '#0e0804' : '#6a4a32', 0.25); ctx.lineWidth = 1 + rw() * 2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (rw() - 0.5) * 6, y + 30 + rw() * 90); ctx.stroke();
  }
  ctx.fillStyle = L.linear(ctx, 0, dy + dh * 0.2, 0, dy + dh / 2, [[0, rgba('#0a0604', 0)], [1, rgba('#0a0604', 0.5)]]);
  ctx.fillRect(dx - dw / 2, dy, dw, dh / 2);
  ctx.restore();
  }
  // the street: worn cobbles in perspective, from the foot of the wall toward the camera (eye level at
  // HZ; rows at even steps of depth grow toward the bottom of the frame), puddles catching the torch
  {
    const HZ = 837, K = (GROUND - HZ) * 4.0;
    ctx.fillStyle = L.linear(ctx, 0, GROUND, 0, VH + 400, [[0, '#121622'], [1, '#0a0c14']]);
    ctx.fillRect(0, GROUND, VW, VH + 400 - GROUND);
    const rc = L.rng(91);
    for (let d = 4.0; d > 0.9; d -= 0.24) {
      const y0 = HZ + K / d, y1 = HZ + K / (d - 0.24), sc = K / d / (GROUND - HZ);
      const w = 0.3 * 333 * sc, off = rc() * w;
      for (let x = -off - w; x < VW + w; x += w * (0.85 + rc() * 0.3)) {
        const cx = x + w / 2, cy = (y0 + y1) / 2, rx = w * (0.42 + rc() * 0.06), ry = (y1 - y0) * (0.4 + rc() * 0.06);
        ctx.fillStyle = mix('#2a3040', '#3c4456', rc());
        ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, (rc() - 0.5) * 0.1, 0, L.TAU); ctx.fill();
        ctx.fillStyle = rgba('#8090b0', 0.08 + rc() * 0.06);
        ctx.beginPath(); ctx.ellipse(cx - rx * 0.1, cy - ry * 0.35, rx * 0.7, ry * 0.4, 0, 0, L.TAU); ctx.fill();
        ctx.fillStyle = rgba('#05060a', 0.35);
        ctx.beginPath(); ctx.ellipse(cx, cy + ry * 0.55, rx * 0.85, ry * 0.35, 0, 0, L.TAU); ctx.fill();
      }
    }
    // a gutter of dark wet mud along the base of the wall
    ctx.fillStyle = L.linear(ctx, 0, GROUND - 6, 0, GROUND + 40, [[0, rgba('#05060a', 0.9)], [1, rgba('#05060a', 0)]]);
    ctx.fillRect(0, GROUND - 6, VW, 46);
    // puddles with the torchlight in them
    for (const [px, py, pr] of [[230, 1460, 120], [760, 1640, 170]]) {
      ctx.fillStyle = rgba('#0a0e18', 0.8);
      ctx.beginPath(); ctx.ellipse(px, py, pr, pr * 0.16, 0, 0, L.TAU); ctx.fill();
      ctx.fillStyle = L.radial(ctx, px - pr * 0.2, py, 0, pr, [[0, rgba('#ff9a50', 0.22)], [1, rgba('#ff9a50', 0)]]);
      ctx.beginPath(); ctx.ellipse(px, py, pr, pr * 0.16, 0, 0, L.TAU); ctx.fill();
    }
  }
  // torch bracket left of door
  ctx.fillStyle = '#18181c'; ctx.fillRect(170, 760, 50, 22);
  vignette(ctx, 0.6, '#02030a');
}
function streetNightDyn(ctx, t, o = {}) {
  // torch flame + flicker light on wall
  const f = 0.8 + 0.2 * L.fbm1(t * 3.3, 2);
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = L.radial(ctx, 200, 720, 20, 640, [[0, rgba('#ff9a40', 0.32 * f)], [0.5, rgba('#ff7a20', 0.12 * f)], [1, rgba('#ff7a20', 0)]]);
  ctx.fillRect(0, 100, VW, 1400);
  ctx.restore();
  B.drawTorch(ctx, 195, 740, 30, t, { key: '#ffffff' }, { size: 1.15, seed: 1 });
}

// =================================================================== HOUSE CHURCH
function houseChurch(ctx, o = {}) {
  fillGrad(ctx, [[0, '#1c1008'], [0.5, '#3c2414'], [1, '#160c06']]);
  L.glow(ctx, o.lampX || 520, o.lampY || 900, 900, '#ffb060', 0.55);
  ctx.fillStyle = L.radial(ctx, 520, 800, 100, 900, [[0, rgba('#c08050', 0.4)], [1, rgba('#c08050', 0)]]);
  ctx.fillRect(0, 0, VW, VH);
  // arches in the back wall
  ctx.strokeStyle = rgba('#120a04', 0.6); ctx.lineWidth = 26;
  for (const ax of [140, 940]) { ctx.beginPath(); ctx.moveTo(ax - 120, 1400); ctx.lineTo(ax - 120, 600); ctx.arc(ax, 600, 120, Math.PI, 0); ctx.lineTo(ax + 120, 1400); ctx.stroke(); }
  vignette(ctx, 0.6);
}
function silhouettes(ctx, list, color, rim, rimA = 0.4, t = 0) {
  // listeners seen from behind: head and neck, sloping shoulders, upper arms hanging at the sides.
  // Each one breathes and now and then turns or tilts the head a little (never frozen).
  // list: [x, y(top of head), scale, turn]
  list.forEach(([x, y, s, turn], i) => {
    const br = Math.sin(t * 1.4 + i * 1.9) * 0.035 * s;
    const look = L.noise1(t * 0.22 + i * 3.1, 11 + i) * 0.12 + (turn || 0) * 0.15;
    const nod = Math.max(0, Math.sin(t * 0.5 + i * 2.3) - 0.8) * 0.4 * s;
    const hx = x + look * s, hy = y + nod;
    ctx.fillStyle = color;
    // body: neck, trapezius slope, round shoulders, arms down the sides
    ctx.beginPath();
    ctx.moveTo(x - s * 0.42, y + s * 1.9);
    ctx.lineTo(x - s * 0.5, y + s * 2.35 - br);
    ctx.quadraticCurveTo(x - s * 1.7, y + s * 2.45 - br, x - s * 2.35, y + s * 2.95 - br);
    ctx.quadraticCurveTo(x - s * 2.85, y + s * 3.3 - br, x - s * 2.8, y + s * 4.1);
    ctx.lineTo(x - s * 2.95, y + s * 6.2);
    ctx.lineTo(x + s * 2.95, y + s * 6.2);
    ctx.lineTo(x + s * 2.8, y + s * 4.1);
    ctx.quadraticCurveTo(x + s * 2.85, y + s * 3.3 - br, x + s * 2.35, y + s * 2.95 - br);
    ctx.quadraticCurveTo(x + s * 1.7, y + s * 2.45 - br, x + s * 0.5, y + s * 2.35 - br);
    ctx.lineTo(x + s * 0.42, y + s * 1.9);
    ctx.closePath(); ctx.fill();
    // head (turning a little)
    ctx.save(); ctx.translate(hx, hy + s * 1.1); ctx.rotate(look * 0.5);
    ctx.beginPath(); ctx.ellipse(0, 0, s * 0.95, s * 1.15, 0, 0, L.TAU); ctx.fill();
    ctx.restore();
    if (rim) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(rim, rimA); ctx.lineWidth = s * 0.12;
      ctx.beginPath(); ctx.ellipse(hx, hy + s * 1.1, s * 0.95, s * 1.15, look * 0.5, -1.9 + (turn || 0), -0.4 + (turn || 0)); ctx.stroke();
      // light catching the shoulder and down the arm on the lamp side, and the arm's inner edge
      const sd = (turn || 0) >= 0 ? 1 : -1;
      ctx.strokeStyle = rgba(rim, rimA * 0.55); ctx.lineWidth = s * 0.09;
      ctx.beginPath(); ctx.moveTo(x + sd * s * 1.2, y + s * 2.55 - br);
      ctx.quadraticCurveTo(x + sd * s * 2.7, y + s * 2.9 - br, x + sd * s * 2.82, y + s * 4.2); ctx.stroke();
      ctx.strokeStyle = rgba(rim, rimA * 0.25); ctx.lineWidth = s * 0.06;
      for (const k of [-1, 1]) { ctx.beginPath(); ctx.moveTo(x + k * s * 2.05, y + s * 3.7); ctx.lineTo(x + k * s * 2.12, y + s * 6.2); ctx.stroke(); }
      ctx.restore();
    }
  });
}

// =================================================================== CELL
// rough, filthy prison masonry: uneven blocks, chipped edges, damp streaks, mould, soot, cracks
function grimyStones(ctx, x0, y0, x1, y1, o) {
  const r = L.rng(o.seed || 7);
  const bh = o.bh || 110;
  // dark mortar bed
  ctx.fillStyle = '#0a0c0e'; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  let y = y0, row = 0;
  while (y < y1) {
    const h = bh * (0.75 + r() * 0.5);
    let x = x0 - (row % 2 ? bh * 0.7 : 0) - r() * bh;
    while (x < x1) {
      const w = bh * (1.1 + r() * 1.4);
      const c = mix(o.base, o.var, r());
      // irregular block outline (no neat rounded rectangles)
      const pts = [];
      const g = 5 + r() * 6;
      const corners = [[x + g, y + g], [x + w - g, y + g], [x + w - g, y + h - g], [x + g, y + h - g]];
      for (let k = 0; k < 4; k++) {
        const a = corners[k], b = corners[(k + 1) % 4];
        for (let j = 0; j < 4; j++) {
          const t = j / 4;
          pts.push([lerp(a[0], b[0], t) + (r() - 0.5) * 7, lerp(a[1], b[1], t) + (r() - 0.5) * 7]);
        }
      }
      ctx.beginPath(); L.crPath(ctx, pts, true, 0.25);
      ctx.fillStyle = c; ctx.fill();
      ctx.save(); ctx.clip();
      // pitted surface
      for (let k = 0; k < 26; k++) {
        ctx.fillStyle = r() < 0.5 ? rgba('#000000', 0.08 + r() * 0.12) : rgba('#ffffff', 0.03 + r() * 0.04);
        ctx.beginPath(); ctx.arc(x + r() * w, y + r() * h, 1.5 + r() * 5, 0, L.TAU); ctx.fill();
      }
      // grime gathers along the bottom of each block; a dull top edge
      ctx.fillStyle = L.linear(ctx, 0, y, 0, y + h, [[0, rgba('#ffffff', 0.05)], [0.18, rgba('#ffffff', 0)], [0.7, rgba('#000000', 0)], [1, rgba('#000000', 0.32)]]);
      ctx.fillRect(x, y, w, h);
      // chipped corner
      if (r() < 0.35) { ctx.fillStyle = rgba('#05060a', 0.7); ctx.beginPath(); ctx.moveTo(x + w - g, y + g); ctx.lineTo(x + w - g - 14 - r() * 18, y + g); ctx.lineTo(x + w - g, y + g + 12 + r() * 16); ctx.fill(); }
      ctx.restore();
      x += w;
    }
    y += h;
    row++;
  }
  // damp streaks running down from the joints and the window
  for (let i = 0; i < 70; i++) {
    const sx = x0 + r() * (x1 - x0), sy = y0 + r() * (y1 - y0) * 0.75, len = 160 + r() * 700, wd = 8 + r() * 30;
    const gr = ctx.createLinearGradient(0, sy, 0, sy + len);
    const dirt = r() < 0.4 ? '#1a120a' : '#05070a';
    gr.addColorStop(0, rgba(dirt, 0.55)); gr.addColorStop(0.6, rgba(dirt, 0.3)); gr.addColorStop(1, rgba(dirt, 0));
    ctx.fillStyle = gr;
    ctx.beginPath(); ctx.moveTo(sx - wd / 2, sy); ctx.bezierCurveTo(sx - wd, sy + len * 0.4, sx + wd * 0.3, sy + len * 0.7, sx, sy + len); ctx.bezierCurveTo(sx + wd * 0.6, sy + len * 0.6, sx + wd, sy + len * 0.3, sx + wd / 2, sy); ctx.fill();
  }
  // mould and slime, thickest near the floor and in the corners
  for (let i = 0; i < 110; i++) {
    const mx = x0 + r() * (x1 - x0), my = lerp(y0, y1, Math.pow(r(), 0.4));
    const rr = 24 + r() * 110;
    ctx.fillStyle = L.radial(ctx, mx, my, 0, rr, [[0, rgba(r() < 0.5 ? '#16220e' : '#2a1e10', 0.55)], [0.6, rgba('#16220e', 0.2)], [1, rgba('#16220e', 0)]]);
    ctx.fillRect(mx - rr, my - rr, rr * 2, rr * 2);
  }
  // cracks
  ctx.strokeStyle = rgba('#020304', 0.85); ctx.lineCap = 'round';
  for (let i = 0; i < 18; i++) {
    let cx = x0 + r() * (x1 - x0), cy = y0 + r() * (y1 - y0);
    ctx.lineWidth = 1.5 + r() * 2.5;
    ctx.beginPath(); ctx.moveTo(cx, cy);
    for (let k = 0; k < 7; k++) { cx += (r() - 0.5) * 60; cy += 18 + r() * 40; ctx.lineTo(cx, cy); }
    ctx.stroke();
  }
  // fine grain over everything
  for (let i = 0; i < 1400; i++) {
    ctx.fillStyle = rgba(r() < 0.6 ? '#000000' : '#c8c8c0', 0.05 + r() * 0.07);
    ctx.fillRect(x0 + r() * (x1 - x0), y0 + r() * (y1 - y0), 1 + r() * 2.2, 1 + r() * 2.2);
  }
}

function cell(ctx, o = {}) {
  fillGrad(ctx, [[0, '#0e1218'], [0.5, '#1a2028'], [1, '#0c0f14']]);
  grimyStones(ctx, -60, 0, VW + 60, 1500, { base: '#262a2c', var: '#383630', bh: 130, seed: 5 });
  // overall dinginess: a brown-black wash that is heavier toward the floor
  ctx.fillStyle = L.linear(ctx, 0, 0, 0, 1500, [[0, rgba('#120c06', 0.15)], [1, rgba('#120c06', 0.45)]]);
  ctx.fillRect(0, 0, VW, 1500);
  // soot stain above the lamp niche, and rust bleeding from the chain ring
  if (o.lamp !== false) {
    const lx = o.lampX || 880, ly = o.lampY || 1050;
    ctx.fillStyle = L.radial(ctx, lx, ly - 260, 20, 300, [[0, rgba('#020202', 0.55)], [1, rgba('#020202', 0)]]);
    ctx.fillRect(lx - 320, ly - 600, 640, 640);
  }
  {
    const rx = o.ringX || 150, ry = o.ringY || 1150;
    const gr = ctx.createLinearGradient(0, ry, 0, ry + 260);
    gr.addColorStop(0, rgba('#5a2a12', 0.5)); gr.addColorStop(1, rgba('#5a2a12', 0));
    ctx.fillStyle = gr; ctx.fillRect(rx - 26, ry, 52, 260);
  }
  // ambient falloff
  ctx.fillStyle = L.radial(ctx, o.lightX || 330, o.lightY || 900, 100, 1300, [[0, rgba('#000000', 0)], [1, rgba('#000000', 0.6)]]);
  ctx.fillRect(0, 0, VW, VH);
  // floor
  ctx.fillStyle = L.linear(ctx, 0, 1480, 0, VH, [[0, '#2a2620'], [1, '#14120e']]);
  ctx.fillRect(0, 1480, VW, VH - 1480);
  ctx.fillStyle = rgba('#000000', 0.45); ctx.fillRect(0, 1470, VW, 26);
  // filth on the floor: damp patches and grit
  for (let i = 0; i < 40; i++) {
    const x = L.hash01(i * 17 + 3) * VW, y = 1490 + L.hash01(i * 29 + 7) * 420, rr = 20 + 60 * L.hash01(i * 13);
    ctx.fillStyle = L.radial(ctx, x, y, 0, rr, [[0, rgba(i % 3 ? '#0a0806' : '#1a1e14', 0.45)], [1, rgba('#0a0806', 0)]]);
    ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.35); ctx.translate(-x, -y); ctx.fillRect(x - rr, y - rr, rr * 2, rr * 2); ctx.restore();
  }
  for (let i = 0; i < 500; i++) {
    ctx.fillStyle = rgba(i % 2 ? '#000000' : '#8a7a5a', 0.12);
    ctx.fillRect(L.hash01(i * 7 + 1) * VW, 1490 + L.hash01(i * 3 + 5) * 430, 2, 2);
  }
  // straw
  ctx.strokeStyle = rgba('#a68a4a', 0.55); ctx.lineWidth = 3;
  for (let i = 0; i < 140; i++) {
    const x = L.hash01(i * 3) * VW * 0.75, y = 1500 + L.hash01(i * 7) * 380, a = L.hash(i * 11) * 1.2, l = 30 + 40 * L.hash01(i * 5);
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l * 0.3); ctx.stroke();
  }
  // window (high, upper-left)
  const wx = o.winX || 250, wy = o.winY || 330;
  ctx.fillStyle = '#c8d8ff';
  ctx.fillRect(wx - 90, wy - 70, 180, 140);
  ctx.fillStyle = L.radial(ctx, wx, wy, 10, 140, [[0, '#ffffff'], [1, '#9fb4e8']]);
  ctx.fillRect(wx - 90, wy - 70, 180, 140);
  ctx.fillStyle = '#111418';
  for (let i = 0; i < 4; i++) ctx.fillRect(wx - 82 + i * 52, wy - 70, 14, 140);
  ctx.fillRect(wx - 90, wy - 6, 180, 12);
  ctx.strokeStyle = '#0a0c0e'; ctx.lineWidth = 16; ctx.strokeRect(wx - 90, wy - 70, 180, 140);
  L.glow(ctx, wx, wy, 300, '#cfe0ff', 0.45);
  // chain ring on wall
  ctx.strokeStyle = '#2a2a2c'; ctx.lineWidth = 12;
  ctx.beginPath(); ctx.arc(o.ringX || 150, o.ringY || 1150, 34, 0, L.TAU); ctx.stroke();
  ctx.fillStyle = '#202024'; ctx.fillRect((o.ringX || 150) - 22, (o.ringY || 1150) - 60, 44, 30);
  // lamp niche (right)
  if (o.lamp !== false) {
    const lx = o.lampX || 880, ly = o.lampY || 1050;
    ctx.fillStyle = '#0a0806'; ctx.beginPath(); ctx.roundRect(lx - 70, ly - 90, 140, 130, [60, 60, 4, 4]); ctx.fill();
    ctx.fillStyle = '#6a3a1e'; ctx.beginPath(); ctx.ellipse(lx, ly + 10, 40, 16, 0, 0, L.TAU); ctx.fill();
  }
  // door (right side)
  if (o.door !== false) {
    const dx = o.doorX || 930, dy = o.doorY || 1000;
    ctx.fillStyle = '#060504'; ctx.fillRect(dx - 150, dy - 520, 300, 1000);
    ctx.fillStyle = L.linear(ctx, dx - 130, 0, dx + 130, 0, [[0, '#3a2818'], [1, '#22160c']]);
    ctx.fillRect(dx - 130, dy - 500, 260, 980);
    for (const by of [dy - 330, dy, dy + 330]) { ctx.fillStyle = '#18181a'; ctx.fillRect(dx - 130, by - 14, 260, 28); }
  }
  vignette(ctx, 0.5, '#020305');
}
function cellDyn(ctx, t, o = {}) {
  const wx = o.winX || 250, wy = o.winY || 330;
  const a = (o.shaftA == null ? 0.22 : o.shaftA);
  lightShaft(ctx, [wx + 10, wy], [o.shaftX || 560, o.shaftY || 1750], 170, 480, o.shaftColor || '#cfe0ff', a);
  dust(ctx, t, { x: wx, y: wy + 60, w: 520, h: 1300 }, 20, '#e8f0ff', 5, 0.5, 2.6);
  if (o.lamp !== false) {
    const lx = o.lampX || 880, ly = o.lampY || 1050;
    B.drawFlame(ctx, lx, ly - 6, 16, t, 4);
    const f = 0.8 + 0.2 * L.fbm1(t * 3, 8);
    L.glow(ctx, lx, ly - 30, 520, '#ff9a40', 0.22 * f);
  }
}

// =================================================================== JERUSALEM NIGHT
function jerusalemNight(ctx, o = {}) {
  fillGrad(ctx, [[0, '#060a16'], [0.4, '#101a30'], [1, '#080a10']]);
  // house walls (pale stone)
  ctx.fillStyle = '#2a3446';
  ctx.fillRect(0, 300, VW, 1300);
  stones(ctx, 0, 300, VW, 1600, { base: '#3a4458', var: '#46506a', bh: 100, seed: 21 });
  ctx.fillStyle = L.linear(ctx, 0, 300, 0, 1000, [[0, rgba('#040610', 0.85)], [1, rgba('#040610', 0.1)]]);
  ctx.fillRect(0, 300, VW, 800);
  // a doorway (blue door)
  ctx.fillStyle = '#1c3a66'; ctx.fillRect(760, 900, 220, 520);
  ctx.fillStyle = '#060a12'; ctx.fillRect(740, 880, 20, 560); ctx.fillRect(980, 880, 20, 560);
  ctx.fillStyle = L.linear(ctx, 0, 1600, 0, VH, [[0, '#1a1c24'], [1, '#08090c']]);
  ctx.fillRect(0, 1600, VW, VH - 1600);
  vignette(ctx, 0.6, '#010205');
}
function jerusalemDyn(ctx, t, o = {}) {
  const f = 0.8 + 0.2 * L.fbm1(t * 3.1, 4);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (const [x, y] of (o.torches || [[260, 760], [640, 700]])) {
    ctx.fillStyle = L.radial(ctx, x, y, 10, 520, [[0, rgba('#ff8a30', 0.35 * f)], [1, rgba('#ff8a30', 0)]]);
    ctx.fillRect(x - 520, y - 520, 1040, 1040);
  }
  ctx.restore();
  for (const [x, y, sd] of (o.torches || [[260, 760, 1], [640, 700, 2]])) B.drawTorch(ctx, x, y, 26, t, { key: '#fff' }, { seed: sd || 1 });
}

// =================================================================== DESERT
function desert(ctx, o = {}) {
  fillGrad(ctx, [[0, '#6a9ed8'], [0.35, '#b8d4ea'], [0.52, '#f2e2c4'], [1, '#d8a868']]);
  L.glow(ctx, o.sunX || 760, o.sunY || 260, 520, '#fffbe8', 0.75);
  ctx.fillStyle = '#fffef6'; ctx.beginPath(); ctx.arc(o.sunX || 760, o.sunY || 260, 70, 0, L.TAU); ctx.fill();
  // distant mountains
  ctx.fillStyle = '#b8a8b8';
  ctx.beginPath(); ctx.moveTo(0, 980);
  for (let i = 0; i <= 12; i++) ctx.lineTo(i * 90, 900 - 90 * L.hash01(i * 5) - 40 * Math.sin(i));
  ctx.lineTo(VW, 1000); ctx.lineTo(0, 1000); ctx.fill();
  ctx.fillStyle = '#c8a888';
  ctx.beginPath(); ctx.moveTo(0, 1040);
  for (let i = 0; i <= 10; i++) ctx.lineTo(i * 108, 990 - 50 * L.hash01(i * 9 + 3));
  ctx.lineTo(VW, 1100); ctx.lineTo(0, 1100); ctx.fill();
  // sand
  ctx.fillStyle = L.linear(ctx, 0, 1000, 0, VH, [[0, '#e0bc84'], [1, '#c08a4c']]);
  ctx.fillRect(0, 1030, VW, VH);
  // road
  ctx.fillStyle = rgba('#a8804c', 0.7);
  ctx.beginPath(); ctx.moveTo(500, 1040); ctx.lineTo(580, 1040); ctx.lineTo(980, VH); ctx.lineTo(160, VH); ctx.closePath(); ctx.fill();
  // rocks
  for (let i = 0; i < 14; i++) {
    const x = L.hash01(i * 3 + 1) * VW, y = 1100 + L.hash01(i * 7 + 2) * 800, r = 10 + 30 * L.hash01(i * 11) * (y - 1000) / 900;
    ctx.fillStyle = rgba('#8a6438', 0.6); ctx.beginPath(); ctx.ellipse(x, y, r * 1.6, r * 0.6, 0, 0, L.TAU); ctx.fill();
  }
}
function desertDyn(ctx, t, o = {}) {
  // heat shimmer band (very subtle)
}

// =================================================================== DIVINE LIGHT
function heavenLight(ctx, t, o = {}) {
  const cx = o.x || 540, cy = o.y || 420;
  fillGrad(ctx, [[0, '#fff6dc'], [0.5, '#ffe9b0'], [1, '#e8b870']]);
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  const n = 22;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * L.TAU + t * 0.05 * (i % 2 ? 1 : -1);
    const w = 0.06 + 0.04 * L.hash01(i * 3);
    ctx.fillStyle = rgba('#ffffff', 0.12 + 0.06 * Math.sin(t * 0.8 + i));
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(a - w) * 2600, cy + Math.sin(a - w) * 2600);
    ctx.lineTo(cx + Math.cos(a + w) * 2600, cy + Math.sin(a + w) * 2600);
    ctx.closePath(); ctx.fill();
  }
  L.glow(ctx, cx, cy, 900, '#ffffff', 0.9);
  ctx.restore();
}

// =================================================================== DAWN ROAD
function pine(ctx, x, y, s, color) {
  // Roman umbrella pine silhouette
  ctx.fillStyle = color;
  ctx.fillRect(x - s * 0.05, y - s * 1.0, s * 0.1, s * 1.0);
  ctx.beginPath(); ctx.moveTo(x, y - s * 0.9); ctx.lineTo(x - s * 0.25, y - s * 1.25); ctx.lineTo(x - s * 0.2, y - s * 1.27); ctx.lineTo(x + 0.02 * s, y - s * 0.95); ctx.fill();
  ctx.beginPath();
  ctx.ellipse(x - s * 0.05, y - s * 1.35, s * 0.62, s * 0.2, 0, 0, L.TAU);
  ctx.ellipse(x + s * 0.25, y - s * 1.42, s * 0.42, s * 0.16, 0, 0, L.TAU);
  ctx.ellipse(x - s * 0.35, y - s * 1.3, s * 0.36, s * 0.14, 0, 0, L.TAU);
  ctx.fill();
}
function cypress(ctx, x, y, s, color) {
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.moveTo(x, y - s * 1.6); ctx.quadraticCurveTo(x + s * 0.22, y - s * 0.8, x + s * 0.12, y); ctx.lineTo(x - s * 0.12, y); ctx.quadraticCurveTo(x - s * 0.22, y - s * 0.8, x, y - s * 1.6); ctx.fill();
}
function dawnRoad(ctx, o = {}) {
  const hz = o.horizon || 1080;
  fillGrad(ctx, [[0, '#1b2350'], [0.25, '#4a3c74'], [0.45, '#c86a5a'], [0.56, '#f4a35a'], [0.6, '#ffd28a'], [1, '#2a1c18']]);
  L.glow(ctx, o.sunX || 600, hz - 30, 700, '#ffd28a', 0.8);
  ctx.fillStyle = '#fff4d0'; ctx.beginPath(); ctx.arc(o.sunX || 600, hz - 10, 80, Math.PI, 0); ctx.fill();
  // clouds
  ctx.fillStyle = rgba('#ffb08a', 0.35);
  for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.ellipse(120 + i * 230, 620 + (i % 2) * 90, 220, 26, 0.02, 0, L.TAU); ctx.fill(); }
  // distant city walls / hills
  ctx.fillStyle = '#4a2c3a';
  ctx.beginPath(); ctx.moveTo(0, hz);
  for (let i = 0; i <= 14; i++) ctx.lineTo(i * 80, hz - 30 - 25 * L.hash01(i * 3) - (i > 2 && i < 6 ? 40 : 0));
  ctx.lineTo(VW, hz + 20); ctx.lineTo(0, hz + 20); ctx.fill();
  // ground
  ctx.fillStyle = L.linear(ctx, 0, hz, 0, VH, [[0, '#3a2420'], [1, '#140c0a']]);
  ctx.fillRect(0, hz, VW, VH - hz);
  // road with perspective toward sun
  ctx.fillStyle = L.linear(ctx, 0, hz, 0, VH, [[0, '#c88a5a'], [1, '#5a3a2a']]);
  ctx.beginPath(); ctx.moveTo((o.sunX || 600) - 18, hz + 2); ctx.lineTo((o.sunX || 600) + 18, hz + 2); ctx.lineTo(1000, VH); ctx.lineTo(80, VH); ctx.closePath(); ctx.fill();
  // paving lines
  ctx.strokeStyle = rgba('#2a1810', 0.45); ctx.lineWidth = 3;
  for (let i = 1; i < 14; i++) { const y = hz + Math.pow(i / 14, 2.2) * (VH - hz); const w = lerp(36, 920, (y - hz) / (VH - hz)); ctx.beginPath(); ctx.moveTo((o.sunX || 600) - w / 2, y); ctx.lineTo((o.sunX || 600) + w / 2 + (y - hz) * 0.05, y); ctx.stroke(); }
  // pines & cypress silhouettes along the road
  const dark = '#1a0e12';
  for (const [x, s] of [[90, 520], [990, 600], [300, 180], [820, 220], [430, 90], [700, 110]]) pine(ctx, x, hz + s * 0.18, s, dark);
  for (const [x, s] of [[200, 260], [900, 300], [520, 70]]) cypress(ctx, x, hz + s * 0.1, s, dark);
}
function dawnDyn(ctx, t, o = {}) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const hz = o.horizon || 1080, sx = o.sunX || 600;
  for (let i = 0; i < 9; i++) {
    const a = -Math.PI / 2 + (i - 4) * 0.22 + 0.02 * Math.sin(t * 0.3 + i);
    ctx.fillStyle = rgba('#ffd890', 0.07);
    ctx.beginPath(); ctx.moveTo(sx, hz - 20);
    ctx.lineTo(sx + Math.cos(a - 0.05) * 2000, hz + Math.sin(a - 0.05) * 2000);
    ctx.lineTo(sx + Math.cos(a + 0.05) * 2000, hz + Math.sin(a + 0.05) * 2000);
    ctx.closePath(); ctx.fill();
  }
  ctx.restore();
  dust(ctx, t, { x: 0, y: 600, w: VW, h: 1100 }, 14, '#ffe0b0', 9, 0.4, 2.5);
}

module.exports = {
  VW, VH, upperRoom, upperRoomDyn, streetNight, streetNightDyn, houseChurch, silhouettes, cell, cellDyn,
  jerusalemNight, jerusalemDyn, desert, desertDyn, heavenLight, dawnRoad, dawnDyn, vignette, lightShaft, dust, bokeh, fillGrad, stones,
};
