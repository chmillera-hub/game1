// Small props and effects.
const L = require('./lib');
const { clamp, lerp, ellipse, fillStroke, sparkle, star } = L;

function lightbulb(ctx, x, y, s, t, glow = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  if (glow > 0) {
    ctx.globalAlpha = glow;
    const g = ctx.createRadialGradient(0, 0, 10, 0, 0, 120);
    g.addColorStop(0, 'rgba(255,240,120,0.9)'); g.addColorStop(1, 'rgba(255,240,120,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, 120, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#FFC400'; ctx.lineWidth = 7; ctx.lineCap = 'round';
    for (let i = 0; i < 10; i++) {
      const a = i / 10 * Math.PI * 2 + t * 0.8;
      ctx.beginPath(); ctx.moveTo(Math.cos(a) * 72, Math.sin(a) * 72); ctx.lineTo(Math.cos(a) * 98, Math.sin(a) * 98); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }
  ctx.beginPath(); ctx.arc(0, -6, 50, Math.PI * 0.78, Math.PI * 2.22); ctx.lineTo(18, 52); ctx.lineTo(-18, 52); ctx.closePath();
  fillStroke(ctx, '#FFF06A', '#E0A800', 4);
  ctx.beginPath(); ctx.moveTo(-10, 40); ctx.lineTo(-6, 8); ctx.lineTo(0, 18); ctx.lineTo(6, 8); ctx.lineTo(10, 40);
  ctx.strokeStyle = '#E08A00'; ctx.lineWidth = 3; ctx.stroke();
  for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.roundRect(-20, 52 + i * 10, 40, 9, 4); fillStroke(ctx, '#B8B8C8', '#7A7A8E', 2); }
  ellipse(ctx, -20, -24, 9, 14, -0.5); ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.fill();
  ctx.restore();
}

function polishBottle(ctx, x, y, s, colour = '#2F6BFF') {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.beginPath(); ctx.roundRect(-34, -20, 68, 72, 18); fillStroke(ctx, colour, '#1B3B9A', 3);
  ctx.fillStyle = 'rgba(255,255,255,0.45)'; ctx.fillRect(-24, -10, 8, 46);
  ctx.beginPath(); ctx.roundRect(-14, -38, 28, 20, 4); fillStroke(ctx, '#EDEDF5', '#9A9AB0', 2);
  ctx.beginPath(); ctx.roundRect(-12, -96, 24, 60, 8); fillStroke(ctx, '#FFFFFF', '#9A9AB0', 2.5);
  ctx.restore();
}

function brush(ctx, x0, y0, x1, y1, colour = '#2F6BFF') {
  ctx.lineCap = 'round';
  ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(lerp(x0, x1, 0.75), lerp(y0, y1, 0.75)); ctx.stroke();
  ctx.strokeStyle = '#9A9AB0'; ctx.lineWidth = 2; ctx.stroke();
  ctx.strokeStyle = colour; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(lerp(x0, x1, 0.75), lerp(y0, y1, 0.75)); ctx.lineTo(x1, y1); ctx.stroke();
}

// comic burst with text
function burst(ctx, x, y, s, text, fill = '#FFF35C', ink = '#E2361B') {
  if (s <= 0.01) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  star(ctx, 0, 0, 125, 0.1, 0.72, 12); fillStroke(ctx, fill, ink, 6);
  ctx.font = '96px "Luckiest Guy"'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round'; ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 12; ctx.strokeText(text, 0, 8);
  ctx.fillStyle = ink; ctx.fillText(text, 0, 8);
  ctx.restore();
}

function thoughtCloud(ctx, x, y, w, h, s, alpha = 1) {
  if (s <= 0.01) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.scale(s, s);
  L.cloudShape(ctx, 0, 0, w, h, 10);
  ctx.fillStyle = '#FFFFFF'; ctx.fill(); ctx.strokeStyle = '#B9A6E0'; ctx.lineWidth = 6; ctx.stroke();
  ctx.restore();
}
function thoughtDots(ctx, pts, t0, t) {
  pts.forEach(([x, y, r], i) => {
    const s = L.easeOutBack(L.prog(t, t0 + i * 0.18, 0.3));
    if (s <= 0) return;
    ellipse(ctx, x, y, r * s, r * s); fillStroke(ctx, '#FFFFFF', '#B9A6E0', 4);
  });
}

function checkBadge(ctx, x, y, s) {
  if (s <= 0.01) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ellipse(ctx, 0, 0, 70, 70); fillStroke(ctx, '#4CD964', '#FFFFFF', 8);
  ctx.beginPath(); ctx.moveTo(-32, 2); ctx.lineTo(-8, 28); ctx.lineTo(36, -26);
  ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 15; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
  ctx.restore();
}

function zzz(ctx, x, y, t, alpha = 1) {
  ctx.save(); ctx.font = '40px FredokaB'; ctx.textAlign = 'center';
  for (let i = 0; i < 3; i++) {
    const p = (t * 0.45 + i / 3) % 1;
    ctx.globalAlpha = alpha * Math.sin(p * Math.PI);
    ctx.fillStyle = '#FFFFFF';
    ctx.font = `${24 + p * 26}px FredokaB`;
    ctx.fillText('z', x + p * 60 + Math.sin(p * 6) * 8, y - p * 120);
  }
  ctx.restore();
}

function floatingHearts(ctx, x, y, t, t0, alpha = 1, n = 8, spread = 160) {
  const r = L.rng(99);
  for (let i = 0; i < n; i++) {
    const delay = r() * 2.5, sp = 0.5 + r() * 0.4, xo = (r() - 0.5) * spread, sz = 12 + r() * 14;
    const p = ((t - t0 - delay) * sp);
    if (p < 0) continue;
    const pp = p % 1.6;
    const a = pp < 0.2 ? pp / 0.2 : 1 - (pp - 0.2) / 1.4;
    ctx.save(); ctx.globalAlpha = clamp(a) * alpha;
    L.heart(ctx, x + xo + Math.sin(pp * 5 + i) * 14, y - pp * 260, sz);
    ctx.fillStyle = i % 3 === 0 ? '#FF6FA8' : '#FF3B5C'; ctx.fill();
    ctx.restore();
  }
}

function heartPop(ctx, x, y, t, t0, size = 34) {
  const p = t - t0;
  if (p < 0 || p > 1.6) return;
  const s = L.easeOutBack(clamp(p / 0.35)) * (1 + Math.sin(p * 10) * 0.05);
  ctx.save(); ctx.globalAlpha = 1 - L.smooth((p - 1.2) / 0.4);
  L.heart(ctx, x, y - p * 40, size * s); fillStroke(ctx, '#FF3B6B', '#FFFFFF', 3);
  ctx.restore();
}

function sparkleBurst(ctx, x, y, t, t0, colour = '#FFFFFF', n = 8, rad = 120, dur = 1.0) {
  const p = (t - t0) / dur;
  if (p < 0 || p > 1) return;
  for (let i = 0; i < n; i++) {
    const a = i / n * Math.PI * 2 + 0.3;
    const rr = rad * L.easeOut(p);
    sparkle(ctx, x + Math.cos(a) * rr, y + Math.sin(a) * rr, 16 * (1 - p) + 4, colour, 1 - p * p);
  }
}

function speedLines(ctx, x, y, dir, R, alpha) {
  if (alpha <= 0.01) return;
  ctx.save(); ctx.globalAlpha = alpha; ctx.strokeStyle = '#FFFFFF'; ctx.lineCap = 'round';
  for (let i = -2; i <= 2; i++) {
    ctx.lineWidth = 8 - Math.abs(i) * 1.5;
    const len = 140 - Math.abs(i) * 25;
    ctx.beginPath(); ctx.moveTo(x - dir * (R + 20), y + i * R * 0.35); ctx.lineTo(x - dir * (R + 20 + len), y + i * R * 0.35); ctx.stroke();
  }
  ctx.restore();
}

function calendar(ctx, x, y, s, label, sub, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.beginPath(); ctx.roundRect(-230, -230, 460, 470, 30); fillStroke(ctx, '#FFFFFF', '#3B2F55', 6);
  ctx.save(); ctx.beginPath(); ctx.roundRect(-230, -230, 460, 470, 30); ctx.clip();
  ctx.fillStyle = '#FF4F6E'; ctx.fillRect(-230, -230, 460, 120);
  ctx.restore();
  for (const sx of [-130, 130]) { ctx.beginPath(); ctx.roundRect(sx - 12, -262, 24, 64, 12); fillStroke(ctx, '#C9C3DD', '#3B2F55', 4); }
  ctx.font = '74px "Luckiest Guy"'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillStyle = '#FFFFFF'; ctx.fillText(label, 0, -164);
  if (sub) { ctx.font = '38px FredokaB'; ctx.fillStyle = '#3B2F55'; ctx.fillText(sub, 0, 196); }
  ctx.restore();
}

function plate(ctx, x, y, s) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ellipse(ctx, 0, 0, 90, 90); fillStroke(ctx, '#FFFFFF', '#9C93B8', 5);
  ellipse(ctx, 0, 0, 60, 60); ctx.strokeStyle = '#D8D2EA'; ctx.lineWidth = 4; ctx.stroke();
  // a few crumbs: dinner's done
  ctx.fillStyle = '#E8B04A'; for (const [cx, cy] of [[-12, 10], [14, -6], [4, 22]]) { ellipse(ctx, cx, cy, 4, 3); ctx.fill(); }
  ctx.fillStyle = '#B8B8C8'; ctx.strokeStyle = '#7A7A8E'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(-128, -70, 14, 140, 7); ctx.fill(); ctx.stroke();
  for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.roundRect(-131 + i * 7, -96, 4, 34, 2); ctx.fill(); }
  ctx.beginPath(); ctx.roundRect(112, -96, 16, 166, [12, 12, 6, 6]); ctx.fill(); ctx.stroke();
  ctx.restore();
}

function moon(ctx, x, y, r) {
  ctx.save();
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = '#FFE58A'; ctx.fill();
  ctx.globalCompositeOperation = 'destination-out';
  ctx.beginPath(); ctx.arc(x + r * 0.45, y - r * 0.25, r * 0.85, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

function bow(ctx, x, y, s) {
  if (s <= 0.01) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = '#FF4B4B'; ctx.strokeStyle = '#C42A2A'; ctx.lineWidth = 4; ctx.lineJoin = 'round';
  for (const d of [-1, 1]) {
    ctx.beginPath(); ctx.moveTo(d * 20, 10); ctx.lineTo(d * 70, 120); ctx.lineTo(d * 52, 100); ctx.lineTo(d * 40, 130); ctx.lineTo(d * 6, 20); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.bezierCurveTo(d * 60, -90, d * 170, -60, d * 150, 10); ctx.bezierCurveTo(d * 140, 70, d * 60, 50, 0, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(d * 30, -10); ctx.quadraticCurveTo(d * 90, -40, d * 125, -5); ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 6; ctx.stroke();
    ctx.strokeStyle = '#C42A2A'; ctx.lineWidth = 4;
  }
  ctx.beginPath(); ctx.roundRect(-28, -30, 56, 60, 18); ctx.fill(); ctx.stroke();
  ctx.restore();
}

// question mark text
function qmark(ctx, x, y, size, colour = '#8E5BD6', rot = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  ctx.font = `${size}px "Luckiest Guy"`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.lineWidth = size * 0.12; ctx.strokeStyle = '#FFFFFF'; ctx.lineJoin = 'round'; ctx.strokeText('?', 0, 0);
  ctx.fillStyle = colour; ctx.fillText('?', 0, 0);
  ctx.restore();
}

function stinkLines(ctx, x, y, t, alpha) {
  if (alpha <= 0.01) return;
  ctx.save(); ctx.globalAlpha = alpha; ctx.strokeStyle = '#7BD36B'; ctx.lineWidth = 5; ctx.lineCap = 'round';
  for (let i = 0; i < 3; i++) {
    ctx.beginPath();
    for (let k = 0; k <= 12; k++) {
      const yy = y - k * 6 - ((t * 40) % 20), xx = x + (i - 1) * 40 + Math.sin(k * 0.9 + t * 6 + i) * 8;
      k ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy);
    }
    ctx.stroke();
  }
  ctx.restore();
}

module.exports = { lightbulb, polishBottle, brush, burst, thoughtCloud, thoughtDots, checkBadge, zzz, floatingHearts, heartPop,
  sparkleBurst, speedLines, calendar, plate, moon, bow, qmark, stinkLines };
