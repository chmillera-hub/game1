// Props drawn in world or hand space.
'use strict';
const { clamp, lerp, shade, rgba, smoothClosed, capsule, noise1, TAU, smooth } = require('./core');
const { paint, softLine, P2, drawHand, HANDS } = require('./rig');
const { fonts } = require('./text');

// Nana's mug: cream ceramic with blue painted flowers; (x, y) = bottom centre resting on a surface.
function mug(ctx, x, y, s = 1, L, o = {}) {
  const w = 58 * s, h = 66 * s;
  ctx.save();
  // contact shadow on the table
  const g = ctx.createRadialGradient(x, y, 2, x, y, w * 0.9);
  g.addColorStop(0, 'rgba(40,20,10,0.35)'); g.addColorStop(1, 'rgba(40,20,10,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(x, y, w * 0.9, w * 0.22, 0, 0, TAU); ctx.fill();
  // handle on the right
  ctx.strokeStyle = '#e9e1cf'; ctx.lineWidth = 10 * s;
  ctx.beginPath(); ctx.ellipse(x + w * 0.52, y - h * 0.52, w * 0.22, h * 0.22, 0, -Math.PI / 2, Math.PI / 2); ctx.stroke();
  ctx.strokeStyle = rgba('#8a7a66', 0.6); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.ellipse(x + w * 0.52, y - h * 0.52, w * 0.22 + 5 * s, h * 0.22 + 5 * s, 0, -Math.PI / 2, Math.PI / 2); ctx.stroke();
  const body = P2((p) => { p.moveTo(x - w / 2, y - h); p.lineTo(x + w / 2, y - h); p.lineTo(x + w * 0.47, y - 4 * s); p.quadraticCurveTo(x, y + 4 * s, x - w * 0.47, y - 4 * s); p.closePath(); });
  paint(ctx, body, '#efe6d3', L, [x - w / 2, y - h, x + w / 2, y], { lw: 2 });
  // blue flowers
  ctx.save(); ctx.clip(body);
  for (const [fx, fy, r] of [[-0.18, -0.55, 0.12], [0.16, -0.35, 0.09], [0.05, -0.75, 0.07]]) {
    const cx = x + fx * w, cy = y + fy * h;
    ctx.fillStyle = '#4f78b8';
    for (let k = 0; k < 5; k++) { const a = k / 5 * TAU; ctx.beginPath(); ctx.ellipse(cx + Math.cos(a) * r * w * 0.7, cy + Math.sin(a) * r * w * 0.7, r * w * 0.45, r * w * 0.3, a, 0, TAU); ctx.fill(); }
    ctx.fillStyle = '#f2cf5b'; ctx.beginPath(); ctx.arc(cx, cy, r * w * 0.28, 0, TAU); ctx.fill();
  }
  softLine(ctx, [[x - w * 0.4, y - h * 0.08], [x + w * 0.4, y - h * 0.08], [x + w * 0.45, y - h * 0.08]], '#4f78b8', 3 * s, 0.6);
  ctx.restore();
  // rim
  ctx.fillStyle = '#5a3c2a'; ctx.beginPath(); ctx.ellipse(x, y - h, w / 2, 7 * s, 0, 0, TAU); ctx.fill();
  ctx.strokeStyle = '#f7f0e2'; ctx.lineWidth = 3 * s; ctx.stroke();
  if (o.steam) {
    for (let i = 0; i < 2; i++) {
      const tt = o.t * 0.6 + i * 0.5, ph = tt % 1;
      ctx.strokeStyle = `rgba(255,255,255,${0.18 * Math.sin(ph * Math.PI)})`; ctx.lineWidth = 4 * s;
      ctx.beginPath(); ctx.moveTo(x - 8 + i * 14, y - h - 6);
      ctx.bezierCurveTo(x - 20 + i * 14, y - h - 30 - ph * 30, x + 10 + i * 10, y - h - 50 - ph * 30, x - 4 + i * 12, y - h - 80 - ph * 40); ctx.stroke();
    }
  }
  ctx.restore();
}

// Phone lying face up on a table; buzz = 0..1 vibrates + lights the screen.
function phone(ctx, x, y, s, buzz, t, text) {
  const jit = buzz > 0 ? Math.sin(t * 90) * 2.5 * buzz : 0;
  ctx.save();
  ctx.translate(x + jit, y);
  ctx.scale(s, s * 0.55); // lying on the table: foreshortened
  ctx.rotate(-0.12);
  ctx.fillStyle = 'rgba(30,15,10,0.3)'; ctx.beginPath(); ctx.ellipse(4, 8, 70, 40, 0, 0, TAU); ctx.fill();
  ctx.fillStyle = '#1d1f24'; roundRectPath(ctx, -60, -110, 120, 220, 18); ctx.fill();
  const lit = clamp(buzz * 1.5 + (text ? 0.6 : 0), 0, 1);
  ctx.fillStyle = lit > 0.05 ? `rgba(${120 + 80 * lit},${140 + 80 * lit},${170 + 70 * lit},1)` : '#2a2e36';
  roundRectPath(ctx, -52, -100, 104, 200, 12); ctx.fill();
  if (text && lit > 0.2) {
    fonts();
    ctx.fillStyle = 'rgba(255,255,255,0.92)'; roundRectPath(ctx, -46, -60, 92, 64, 10); ctx.fill();
    ctx.fillStyle = '#222'; ctx.font = 'bold 13px InterBold'; ctx.fillText(text[0], -40, -42);
    ctx.font = '12px InterSemi'; ctx.fillText(text[1], -40, -24); ctx.fillText(text[2] || '', -40, -10);
  }
  ctx.restore();
}
function roundRectPath(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

// Clipboard held in hand space (hand frame: fingers along +x). Fingers hidden behind; thumb drawn on the front.
function clipboard(ctx, C, o) {
  const hs = C.body.hand;
  ctx.save();
  ctx.rotate(Math.PI / 2 * -o.ts * 0.0 - 0.15 * o.ts);
  const bw = hs * 2.1, bh = hs * 2.8;
  const bx = hs * 0.25, by = -bh * 0.15 * o.ts - (o.ts > 0 ? bh * 0.7 : 0);
  ctx.fillStyle = '#a77a4c'; roundRectPath(ctx, bx, by, bw, bh, 8); ctx.fill();
  ctx.strokeStyle = rgba('#5a3c22', 0.7); ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = '#fbf8f0'; ctx.fillRect(bx + 10, by + 22, bw - 20, bh - 30);
  ctx.strokeStyle = 'rgba(80,110,160,0.35)'; ctx.lineWidth = 1.5;
  for (let i = 0; i < 9; i++) { ctx.beginPath(); ctx.moveTo(bx + 16, by + 50 + i * 22); ctx.lineTo(bx + bw - 16, by + 50 + i * 22); ctx.stroke(); }
  if (o.A && o.A.note) {
    fonts();
    ctx.save(); ctx.translate(bx + bw / 2, by + bh / 2); ctx.rotate(-Math.PI / 2 * 0);
    ctx.fillStyle = '#c0392b'; ctx.font = 'bold 26px InterBold'; ctx.textAlign = 'center';
    ctx.globalAlpha = clamp(o.A.note, 0, 1);
    ctx.fillText('MOVE ON?', 0, -10);
    ctx.strokeStyle = '#c0392b'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-60, 4); ctx.lineTo(60, 2); ctx.stroke();
    ctx.restore();
  }
  ctx.fillStyle = '#9aa0a8'; ctx.fillRect(bx + bw / 2 - 26, by - 6, 52, 22);
  ctx.restore();
  // thumb on the front
  const [tx, ty] = o.hand.thumb;
  ctx.fillStyle = C.skin;
  ctx.strokeStyle = rgba(shade(C.skin, -0.45), 0.6); ctx.lineWidth = 2;
  ctx.beginPath(); capsule(ctx, hs * 0.2, ty * 0.6, hs * 0.07, tx + hs * 0.05, ty * 0.6, hs * 0.055); ctx.fill(); ctx.stroke();
}

// Bellows held in front by both hands (local coords of the actor); open = 0..1
function bellows(ctx, x, y, s, open, L) {
  ctx.save();
  ctx.translate(x, y); ctx.scale(s, s);
  const a = 0.18 + 0.32 * open;
  // nozzle
  ctx.fillStyle = '#9a7b3a'; ctx.beginPath(); ctx.moveTo(150, -10); ctx.lineTo(240, -4); ctx.lineTo(240, 4); ctx.lineTo(150, 10); ctx.fill();
  // leather between boards
  ctx.fillStyle = '#6b3f26';
  ctx.beginPath(); ctx.moveTo(150, 0); ctx.lineTo(-40, -110 * a * 2.2); ctx.lineTo(-40, 110 * a * 2.2); ctx.closePath(); ctx.fill();
  for (let k = 1; k < 4; k++) { ctx.strokeStyle = 'rgba(40,20,10,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(150, 0); ctx.lineTo(-40 + k * 8, (k % 2 ? -1 : 1) * 100 * a * 2.2); ctx.stroke(); }
  // boards
  for (const sd of [-1, 1]) {
    ctx.save(); ctx.rotate(sd * a);
    const b = P2((p) => smoothClosed(p, [[160, 0], [40, sd * 22], [-60, sd * 34], [-110, sd * 24], [-60, sd * 6], [40, sd * 4]], 0.6));
    paint(ctx, b, '#8a5a32', L, [-120, -40, 170, 40], { lw: 2 });
    ctx.restore();
  }
  ctx.restore();
}

// Recipe card held by both hands; drawn after the arms, then thumbs over the front.
function recipeCard(ctx, cx, cy, w, h, rot, C, thumbs, t, ts = 1) {
  fonts();
  ctx.save();
  ctx.translate(cx, cy); ctx.rotate(rot);
  ctx.fillStyle = 'rgba(0,0,0,0.18)'; ctx.fillRect(-w / 2 + 4, -h / 2 + 6, w, h);
  ctx.fillStyle = '#f4e9cf'; ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.strokeStyle = 'rgba(200,90,90,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-w / 2, -h / 2 + h * 0.22); ctx.lineTo(w / 2, -h / 2 + h * 0.22); ctx.stroke();
  ctx.strokeStyle = 'rgba(90,120,170,0.3)'; ctx.lineWidth = 1.2;
  for (let i = 1; i < 6; i++) { ctx.beginPath(); ctx.moveTo(-w / 2, -h / 2 + h * 0.22 + i * h * 0.13); ctx.lineTo(w / 2, -h / 2 + h * 0.22 + i * h * 0.13); ctx.stroke(); }
  ctx.fillStyle = '#3b3550';
  ctx.font = `italic ${Math.round(h * 0.13)}px InterItalic`;
  ctx.fillText("Nana's Bread", -w / 2 + w * 0.08, -h / 2 + h * 0.17);
  ctx.font = `italic ${Math.round(h * 0.085)}px InterItalic`;
  ['3 cups flour, warm water,', 'a pinch of salt, honey...', 'Knead slowly. Let it rest.', '', '— for my two ♥'].forEach((ln, i) => ctx.fillText(ln, -w / 2 + w * 0.08, -h / 2 + h * 0.34 + i * h * 0.13));
  ctx.restore();
  // thumbs on the front edge
  for (const th of thumbs || []) {
    ctx.save(); ctx.translate(th[0], th[1]); ctx.rotate(th[2]); ctx.scale(ts, ts);
    ctx.fillStyle = C.skin; ctx.strokeStyle = rgba(shade(C.skin, -0.45), 0.6); ctx.lineWidth = 2;
    ctx.beginPath(); capsule(ctx, 0, 0, C.body.hand * 0.075, C.body.hand * 0.26, 0, C.body.hand * 0.06); ctx.fill(); ctx.stroke();
    softLine(ctx, [[C.body.hand * 0.17, -4], [C.body.hand * 0.19, 0], [C.body.hand * 0.17, 4]], shade(C.skin, -0.35), 1.4, 0.4);
    ctx.restore();
  }
}

// Bread roll resting on an upturned palm, thumb over its edge (hand space).
function bread(ctx, C, o) {
  const hs = C.body.hand;
  ctx.save();
  const bx = hs * 0.62, by = -hs * 0.18 * o.ts;
  const g = ctx.createRadialGradient(bx - 8, by - 10, 4, bx, by, hs * 0.5);
  g.addColorStop(0, '#f0c27a'); g.addColorStop(0.7, '#c98a3e'); g.addColorStop(1, '#9c6428');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.ellipse(bx, by, hs * 0.48, hs * 0.32, 0, 0, TAU); ctx.fill();
  ctx.strokeStyle = 'rgba(90,50,20,0.5)'; ctx.lineWidth = 2; ctx.stroke();
  ctx.strokeStyle = 'rgba(255,230,180,0.6)'; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(bx - hs * 0.2, by - hs * 0.05); ctx.quadraticCurveTo(bx, by - hs * 0.15, bx + hs * 0.22, by - hs * 0.04); ctx.stroke();
  ctx.restore();
  const [tx, ty] = o.hand.thumb;
  ctx.fillStyle = C.skin; ctx.strokeStyle = rgba(shade(C.skin, -0.45), 0.6); ctx.lineWidth = 2;
  ctx.beginPath(); capsule(ctx, hs * 0.18, ty * 0.8, hs * 0.075, tx + hs * 0.08, ty * 0.75, hs * 0.058); ctx.fill(); ctx.stroke();
}

// Key held in a pinch (hand space)
function key(ctx, C, o) {
  const hs = C.body.hand;
  ctx.save(); ctx.translate(hs * 0.62, -hs * 0.05 * o.ts);
  ctx.fillStyle = '#c9a646';
  ctx.beginPath(); ctx.arc(0, 0, hs * 0.12, 0, TAU); ctx.fill();
  ctx.fillRect(0, -hs * 0.03, hs * 0.45, hs * 0.06);
  ctx.fillRect(hs * 0.35, 0, hs * 0.04, hs * 0.08); ctx.fillRect(hs * 0.27, 0, hs * 0.04, hs * 0.06);
  ctx.restore();
  const [tx, ty] = o.hand.thumb;
  ctx.fillStyle = C.skin; ctx.beginPath(); ctx.ellipse(tx, ty * 0.6, hs * 0.08, hs * 0.06, 0, 0, TAU); ctx.fill();
}

// Close-up of two hands on a hospital blanket: Nana's frail hand trembling inside Maya's.
function handsCloseup(ctx, cast, x, y, s, t, shake, L) {
  const nana = cast.nana, maya = cast.maya;
  const tremble = shake * (Math.sin(t * 23) * 1.6 + Math.sin(t * 31 + 1) * 1.1);
  ctx.save();
  ctx.translate(x, y); ctx.scale(s, s);
  // Nana's hand (back of hand up, from the left, fingers slightly curled), with a sleeve cuff
  ctx.save(); ctx.translate(-150 + tremble * 0.6, 10 + tremble); ctx.rotate(-0.08);
  const cuff = P2((p) => capsule(p, -260, 0, 46, -40, 4, 40));
  paint(ctx, cuff, '#b9a7c9', L, [-300, -50, 0, 50], { lw: 2 });
  ctx.fillStyle = shade('#b9a7c9', -0.5); ctx.beginPath(); ctx.ellipse(-36, 4, 12, 36, 0, 0, TAU); ctx.fill();
  ctx.translate(-34, 4);
  drawHand(ctx, { ...nana, skin: '#a87a5c' }, { ...HANDS.soft, curl: [0.3, 0.35, 0.4, 0.45], thumbA: 0.5 }, 1, 'back', L, 150);
  // age: soft veins/wrinkles
  softLine(ctx, [[20, -20], [50, -12], [80, -16]], '#7d5a48', 2, 0.4);
  softLine(ctx, [[30, 14], [55, 8], [85, 12]], '#7d5a48', 2, 0.35);
  ctx.restore();
  // Maya's hand from the right, palm down, wrapping over Nana's fingers
  ctx.save(); ctx.translate(0 + tremble * 0.25, -14 + tremble * 0.3); ctx.rotate(Math.PI + 0.1);
  const cuff2 = P2((p) => capsule(p, -280, 0, 50, -40, 0, 42));
  paint(ctx, cuff2, '#7a8450', L, [-320, -55, 0, 55], { lw: 2 });
  ctx.fillStyle = shade('#7a8450', -0.5); ctx.beginPath(); ctx.ellipse(-36, 0, 12, 38, 0, 0, TAU); ctx.fill();
  ctx.translate(-34, 0);
  drawHand(ctx, maya, { ...HANDS.soft, curl: [0.45, 0.5, 0.55, 0.6], thumbA: 0.3, spread: 0.05 }, -1, 'back', L, 160);
  ctx.restore();
  ctx.restore();
}

module.exports = { mug, phone, clipboard, bellows, recipeCard, bread, key, handsCloseup, roundRectPath };
