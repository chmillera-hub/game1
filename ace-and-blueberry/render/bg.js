// Backgrounds, inspired by the colours/patterns of the original pictures.
const L = require('./lib');
const { W, H, clamp, lerp, ellipse, fillStroke, rng, star, lerpColor, sparkle } = L;

const STAR_COLS = ['#F04A2B', '#2EC4C9', '#E79BD8', '#C0702A'];
function makeStars(seed, w, h, step, rmin, rmax) {
  const r = rng(seed), arr = [];
  for (let y = step * 0.5; y < h + step; y += step * 0.86) {
    for (let x = (Math.round(y / step) % 2) * step * 0.5; x < w + step; x += step) {
      arr.push({ x: x + (r() - 0.5) * step * 0.5, y: y + (r() - 0.5) * step * 0.4, r: lerp(rmin, rmax, r()),
        c: STAR_COLS[Math.floor(r() * 4)], rot: (r() - 0.5) * 0.6, tw: r() < 0.22, ph: r() * 6 });
    }
  }
  return arr;
}
const WALL_STARS = makeStars(3, W, 760, 74, 13, 24);
const BIG_WALL_STARS = makeStars(5, W, H, 120, 22, 40);

function starWall(ctx, t, horizon, big = false) {
  const g = ctx.createLinearGradient(0, 0, 0, horizon);
  g.addColorStop(0, '#FFD54F'); g.addColorStop(1, '#FFC12E');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, horizon);
  ctx.lineJoin = 'round';
  for (const s of (big ? BIG_WALL_STARS : WALL_STARS)) {
    if (s.y - s.r > horizon) continue;
    const k = s.tw ? 1 + Math.sin(t * 2.2 + s.ph) * 0.14 : 1;
    star(ctx, s.x, s.y, s.r * k, s.rot + (s.tw ? Math.sin(t * 1.3 + s.ph) * 0.12 : 0));
    fillStroke(ctx, s.c, 'rgba(90,50,20,0.45)', 1.5);
  }
}

function pinkFloor(ctx, t, horizon) {
  const g = ctx.createLinearGradient(0, horizon, 0, H);
  g.addColorStop(0, '#F6B7D2'); g.addColorStop(1, '#FAD3E4');
  ctx.fillStyle = g; ctx.fillRect(0, horizon, W, H - horizon);
  ctx.strokeStyle = 'rgba(255,255,255,0.45)'; ctx.lineWidth = 6; ctx.lineCap = 'round';
  for (let i = 0; i < 9; i++) {
    const y = horizon + 40 + i * i * 9 + i * 28;
    ctx.beginPath();
    for (let x = -20; x <= W + 20; x += 20) {
      const yy = y + Math.sin(x / 70 + i * 1.7) * (6 + i);
      x === -20 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy);
    }
    ctx.stroke();
  }
  ctx.fillStyle = 'rgba(160,60,110,0.18)'; ctx.fillRect(0, horizon, W, 6);
}

function starRoom(ctx, t, horizon = 640, big = false) {
  starWall(ctx, t, horizon, big);
  pinkFloor(ctx, t, horizon);
}

// ------------------------------------------------------------ title -----
const DOTS = (() => {
  const r = rng(11), arr = [];
  for (let i = 0; i < 70; i++) arr.push({ x: r() * W, y: r() * H, r: 18 + r() * 38, rim: r() < 0.55, ph: r() * 6 });
  return arr;
})();
function titleBg(ctx, t) {
  ctx.fillStyle = '#F9D4E4'; ctx.fillRect(0, 0, W, H);
  for (const d of DOTS) {
    const y = d.y + Math.sin(t * 0.7 + d.ph) * 3;
    ellipse(ctx, d.x, y, d.r, d.r);
    ctx.fillStyle = d.rim ? '#9FA7E8' : '#AFB4EC'; ctx.fill();
    if (d.rim) { ctx.strokeStyle = '#3FC6D6'; ctx.lineWidth = 5; ctx.stroke(); }
  }
  // wavy yellow + pink ribbons along the bottom
  for (const [col, y0, amp, lw, sp] of [['#F7DC1E', 1085, 34, 44, 1.0], ['#E58FDB', 1150, 38, 26, -1.2]]) {
    ctx.beginPath();
    for (let x = -30; x <= W + 30; x += 12) {
      const y = y0 + Math.sin(x / 95 + t * sp) * amp;
      x === -30 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.stroke();
  }
}

// -------------------------------------------------------- orange room ---
function orangeRoom(ctx, t, horizon = 660, part = 'all') {
  if (part !== 'floor') orangeWall(ctx, t, horizon);
  if (part !== 'wall') blueRug(ctx, t, horizon);
}
function orangeWall(ctx, t, horizon) {
  const g = ctx.createLinearGradient(0, 0, W, horizon);
  g.addColorStop(0, '#FFB347'); g.addColorStop(0.55, '#FFCF5C'); g.addColorStop(1, '#FFE07A');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, horizon);
  // green corner
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(150, 0); ctx.lineTo(0, 210); ctx.closePath(); ctx.fillStyle = '#7ED957'; ctx.fill();
  // scalloped red valance with white dots
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(W, 0); ctx.lineTo(W, 70);
  for (let x = W; x >= 0; x -= 90) ctx.quadraticCurveTo(x - 45, 130, x - 90, 70);
  ctx.closePath(); ctx.fillStyle = '#FF5B3A'; ctx.fill();
  ctx.fillStyle = '#FFF4E0';
  for (let x = 45; x < W; x += 90) { ellipse(ctx, x, 30, 6, 6); ctx.fill(); }
  // hanging mobile
  const sw = Math.sin(t * 1.1) * 0.08;
  ctx.save(); ctx.translate(190, 90); ctx.rotate(sw);
  ctx.strokeStyle = '#7A5A3A'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 210); ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 70, 16, 0, Math.PI * 2); ctx.lineWidth = 5; ctx.strokeStyle = '#FFFFFF'; ctx.stroke();
  ellipse(ctx, 0, 125, 13, 18); fillStroke(ctx, '#FF7A9A', '#D8436A', 2);
  for (let i = 0; i < 6; i++) { ellipse(ctx, -5 + (i % 2) * 9, 115 + i * 5, 1.5, 1.5); ctx.fillStyle = '#FFF'; ctx.fill(); }
  ellipse(ctx, 0, 190, 11, 11); fillStroke(ctx, '#5FD06A', '#2E9A3F', 2);
  ctx.restore();
  // the pink gloves, now hanging on the wall
  ctx.save(); ctx.translate(620, 250);
  ctx.strokeStyle = '#B07A4A'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-45, -60); ctx.lineTo(0, -95); ctx.lineTo(45, -60); ctx.stroke();
  ellipse(ctx, 0, -95, 5, 5); ctx.fillStyle = '#8A5A2A'; ctx.fill();
  ctx.restore();
}
function blueRug(ctx, t, horizon) {
  // floor: pale blue fluffy rug
  const g2 = ctx.createLinearGradient(0, horizon, 0, H);
  g2.addColorStop(0, '#BFD9F2'); g2.addColorStop(1, '#DCEBFA');
  ctx.fillStyle = g2; ctx.fillRect(0, horizon, W, H - horizon);
  ctx.strokeStyle = 'rgba(255,255,255,0.6)'; ctx.lineWidth = 3;
  const r = rng(9);
  for (let i = 0; i < 40; i++) {
    const x = r() * W, y = horizon + 30 + r() * (H - horizon - 60);
    ctx.beginPath(); ctx.arc(x, y, 10 + r() * 14, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
  }
  ctx.fillStyle = 'rgba(70,110,160,0.18)'; ctx.fillRect(0, horizon, W, 6);
}

// ------------------------------------------------------------ bedroom ---
const SKY_STARS = (() => {
  const r = rng(21), arr = [];
  for (let i = 0; i < 16; i++) arr.push({ x: 150 + r() * 420, y: 110 + r() * 340, r: 13 + r() * 8, ph: r() * 6, face: r() < 0.7 });
  return arr;
})();
function faceStar(ctx, x, y, r, rot, face) {
  star(ctx, x, y, r, rot, 0.5); fillStroke(ctx, '#FFE14D', '#E0A800', 1.5);
  if (face && r > 9) {
    ctx.fillStyle = '#7A4A00';
    ellipse(ctx, x - r * 0.22, y - r * 0.05, r * 0.07, r * 0.09); ctx.fill();
    ellipse(ctx, x + r * 0.22, y - r * 0.05, r * 0.07, r * 0.09); ctx.fill();
    ctx.beginPath(); ctx.arc(x, y + r * 0.08, r * 0.17, 0.2, Math.PI - 0.2);
    ctx.strokeStyle = '#7A4A00'; ctx.lineWidth = 1.4; ctx.stroke();
  }
}
// morning: 0 = night, 1 = morning
function windowSky(ctx, t, x, y, w, h, morning) {
  ctx.save(); ctx.beginPath(); ctx.roundRect(x, y, w, h, 18); ctx.clip();
  const g = ctx.createLinearGradient(0, y, 0, y + h);
  g.addColorStop(0, lerpColor('#1E3F86', '#7FCBFF', morning));
  g.addColorStop(1, lerpColor('#4E92D6', '#FFE6A6', morning));
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
  // soft diagonal light streaks (like the watercolour sky)
  ctx.globalAlpha = 0.18 * (1 - morning);
  ctx.strokeStyle = '#BFE6FF'; ctx.lineWidth = 26;
  for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(x - 50 + i * 120, y + h); ctx.lineTo(x + 100 + i * 120, y); ctx.stroke(); }
  ctx.globalAlpha = 1;
  if (morning > 0) { // sun rising
    const sy = lerp(y + h + 80, y + h * 0.42, L.easeOut(morning));
    ctx.globalAlpha = clamp(morning * 1.5);
    ellipse(ctx, x + w * 0.68, sy, 95, 95); ctx.fillStyle = 'rgba(255,240,170,0.5)'; ctx.fill();
    ellipse(ctx, x + w * 0.68, sy, 62, 62); ctx.fillStyle = '#FFD23F'; ctx.fill();
    ctx.globalAlpha = 1;
    // little clouds
    for (const [cx, cy, s] of [[x + 90, y + 90, 1], [x + w - 120, y + 60, 0.8]]) {
      ctx.globalAlpha = clamp(morning * 1.4 - 0.3);
      for (const [dx, dy, rr] of [[0, 0, 26], [28, -10, 30], [56, 0, 24]]) { ellipse(ctx, cx + dx * s, cy + dy * s, rr * s, rr * s * 0.8); ctx.fillStyle = '#fff'; ctx.fill(); }
      ctx.globalAlpha = 1;
    }
  }
  const sa = 1 - clamp(morning * 1.6);
  if (sa > 0) {
    ctx.globalAlpha = sa;
    for (const s of SKY_STARS) faceStar(ctx, s.x, s.y, s.r * (1 + Math.sin(t * 2 + s.ph) * 0.1), Math.sin(t + s.ph) * 0.15, s.face);
    ctx.globalAlpha = 1;
  }
  ctx.restore();
}
function bedroom(ctx, t, morning = 0) {
  // wall
  ctx.fillStyle = lerpColor('#5B4A9A', '#E8D9FF', morning); ctx.fillRect(0, 0, W, H);
  // window
  const wx = 130, wy = 80, ww = 460, wh = 400;
  ctx.beginPath(); ctx.roundRect(wx - 16, wy - 16, ww + 32, wh + 32, 26); ctx.fillStyle = lerpColor('#CDB8F0', '#FFFFFF', morning); ctx.fill();
  windowSky(ctx, t, wx, wy, ww, wh, morning);
  ctx.strokeStyle = lerpColor('#CDB8F0', '#FFFFFF', morning); ctx.lineWidth = 12;
  ctx.beginPath(); ctx.moveTo(wx + ww / 2, wy); ctx.lineTo(wx + ww / 2, wy + wh); ctx.moveTo(wx, wy + wh / 2); ctx.lineTo(wx + ww, wy + wh / 2); ctx.stroke();
  // curtains
  for (const s of [-1, 1]) {
    ctx.save();
    if (s > 0) { ctx.translate(W, 0); ctx.scale(-1, 1); }
    ctx.beginPath(); ctx.moveTo(-10, 30); ctx.lineTo(165, 30);
    ctx.quadraticCurveTo(110, 260, 150, 470); ctx.quadraticCurveTo(90, 520, 120, 600);
    ctx.lineTo(-10, 600); ctx.closePath();
    ctx.fillStyle = lerpColor('#8C5BC9', '#B98BE8', morning); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.22)'; ctx.lineWidth = 6;
    for (const k of [30, 70, 110]) { ctx.beginPath(); ctx.moveTo(k, 40); ctx.quadraticCurveTo(k - 10, 300, k * 0.8, 590); ctx.stroke(); }
    ctx.beginPath(); ctx.roundRect(60, 455, 90, 22, 11); ctx.fillStyle = lerpColor('#D46BB8', '#F59AD2', morning); ctx.fill();
    ctx.restore();
  }
  // valance (pink scallops, like the drawing)
  ctx.beginPath(); ctx.moveTo(0, 20); ctx.lineTo(W, 20); ctx.lineTo(W, 60);
  for (let x = W; x >= 0; x -= 80) ctx.quadraticCurveTo(x - 40, 115, x - 80, 60);
  ctx.closePath(); ctx.fillStyle = lerpColor('#D46BB8', '#F59AD2', morning); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.7)';
  for (let x = 40; x < W; x += 80) { ellipse(ctx, x, 70, 4, 4); ctx.fill(); }
  ctx.fillStyle = lerpColor('#4A3A80', '#D9C6F5', morning); ctx.fillRect(0, 0, W, 22);
  // headboard
  ctx.beginPath(); ctx.roundRect(70, 540, 580, 260, [120, 120, 10, 10]);
  ctx.fillStyle = lerpColor('#7B4FB8', '#A77BE0', morning); ctx.fill();
  ctx.strokeStyle = lerpColor('#5E3893', '#8657C2', morning); ctx.lineWidth = 8; ctx.stroke();
  // pillow
  ellipse(ctx, 330, 690, 230, 82); fillStroke(ctx, lerpColor('#D8D2F2', '#FFFFFF', morning), lerpColor('#A89ED6', '#D8CCF2', morning), 4);
}
// blanket covers everything below its top edge; drawn over Ace's head/body
function blanket(ctx, t, morning = 0, top = 790) {
  ctx.beginPath(); ctx.moveTo(0, top + 30);
  for (let x = 0; x <= W; x += 40) ctx.quadraticCurveTo(x + 20, top + (x / 40 % 2 ? 6 : -6) + Math.sin(t * 1.2) * 2, x + 40, top + Math.sin((x + 40) / 120) * 14);
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  const g = ctx.createLinearGradient(0, top, 0, H);
  g.addColorStop(0, lerpColor('#E07BB0', '#FF9CCB', morning)); g.addColorStop(1, lerpColor('#B4568D', '#F07AB5', morning));
  ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 8; ctx.stroke();
  // little hearts pattern
  ctx.fillStyle = 'rgba(255,255,255,0.22)';
  for (let y = top + 90; y < H; y += 110) for (let x = 60 + ((y / 110) % 2) * 55; x < W; x += 110) { L.heart(ctx, x, y, 14); ctx.fill(); }
}

// ------------------------------------------------------------- stage ----
function stageBack(ctx, t) {
  ctx.fillStyle = '#E9FBFB'; ctx.fillRect(0, 0, W, H);
  // crayon-ish teal scribbles
  const r = rng(77); ctx.strokeStyle = 'rgba(62,200,205,0.45)'; ctx.lineWidth = 7; ctx.lineCap = 'round';
  for (let i = 0; i < 70; i++) {
    const x = r() * W, y = 150 + r() * (H - 200);
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 60 + r() * 90, y + (r() - 0.5) * 10); ctx.stroke();
  }
  // stage floor
  ctx.fillStyle = '#5B4BC4'; ctx.fillRect(0, 1010, W, 26);
  // tree
  ctx.beginPath(); ctx.moveTo(110, 1012); ctx.quadraticCurveTo(140, 840, 128, 700); ctx.lineTo(180, 700); ctx.quadraticCurveTo(170, 840, 205, 1012); ctx.closePath();
  fillStroke(ctx, '#D9A0A8', '#5B4BC4', 5);
  ellipse(ctx, 155, 620, 118, 108); fillStroke(ctx, '#8FD14F', '#3E6E2A', 5);
  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  for (const [x, y] of [[110, 590], [190, 590], [150, 660], [90, 640], [215, 650]]) { ellipse(ctx, x, y, 12, 9); ctx.fill(); }
}
// curtains: open = 0 closed, 1 open
function stageFront(ctx, t, open) {
  const cw = lerp(W / 2 + 10, 70, L.easeInOut(open));
  for (const s of [-1, 1]) {
    ctx.save();
    if (s > 0) { ctx.translate(W, 0); ctx.scale(-1, 1); }
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(cw, 0);
    ctx.quadraticCurveTo(cw - 30, 600, cw + 10 * open, 1180); ctx.lineTo(0, 1180); ctx.closePath();
    ctx.fillStyle = '#4B3FD0'; ctx.fill();
    ctx.save(); ctx.clip();
    for (let k = 0; k < 8; k++) {
      const x = (k + 0.5) * cw / 8;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.quadraticCurveTo(x - 10, 600, x + 8 * open, 1180);
      ctx.strokeStyle = k % 2 ? '#E2559B' : '#7A6CF0'; ctx.lineWidth = 9; ctx.stroke();
    }
    ctx.restore();
    ctx.restore();
  }
  // valance
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(W, 0); ctx.lineTo(W, 100);
  for (let x = W; x >= 0; x -= 120) ctx.quadraticCurveTo(x - 60, 175, x - 120, 100);
  ctx.closePath(); ctx.fillStyle = '#FFA22E'; ctx.fill(); ctx.strokeStyle = '#4B3FD0'; ctx.lineWidth = 7; ctx.stroke();
  // bottom
  ctx.fillStyle = '#4B3FD0'; ctx.fillRect(0, 1180, W, H - 1180);
  ctx.fillStyle = '#6E61E6'; ctx.fillRect(0, 1180, W, 10);
}

module.exports = { starRoom, starWall, pinkFloor, titleBg, orangeRoom, bedroom, blanket, stageBack, stageFront, faceStar };
