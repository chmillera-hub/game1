// Character rigs. Every draw fn takes a state `st`:
// { x, y, s, flip, e (expression), blink, look:[lx,ly], open, round, mw, t, P (pose), V (vars), light, nod, talk }
const { TAU, clamp, lerp, ellipse, rgba, smoothPath, ik, taper, noise, roundRect, spiralPts } = require('./lib');
const { INK, eye, brow, mouth, tearDrop, hand, limb, drawPumpkin } = require('./face');

// ───────────────────────── PIP (the newest ghost) ─────────────────────────
const PIP_BASE = { ax: -112, ay: -28, bx: 112, by: -28, lean: 0, pkx: 0, pky: -60, spoon: 0 };
const PIP_POSES = {
  sit: {},
  hug: { ax: -8, ay: -70, bx: 10, by: -80, lean: -0.03 },
  handsLap: { ax: -22, ay: -44, bx: 24, by: -40, lean: 0.02 },
  mouthCover: { ax: -62, ay: -70, bx: 4, by: -152, lean: 0.05 },
  holdPumpkin: { ax: -58, ay: -64, bx: 58, by: -64 },
  carve: { ax: -60, ay: -60, bx: 30, by: -98, spoon: 1 },
  present: { ax: -62, ay: -98, bx: 62, by: -98, pky: -98, lean: -0.04 },
  gestLow: { ax: -56, ay: -64, bx: 120, by: -6 },
  gestHigh: { ax: -56, ay: -64, bx: 96, by: -262, lean: -0.05 },
};
const SHEET = '#eef2fb';

function pipBodyPath(ctx, t) {
  ctx.beginPath();
  ctx.moveTo(-128, -8);
  ctx.bezierCurveTo(-122, -70, -100, -140, -95, -200);
  ctx.arc(0, -200, 95, Math.PI, 0);
  ctx.bezierCurveTo(100, -140, 122, -70, 128, -8);
  const N = 5;
  for (let i = 0; i < N; i++) {
    const x0 = 128 - (i * 256) / N, x1 = 128 - ((i + 1) * 256) / N;
    const w = Math.sin(t * 2.6 + i * 1.4) * 4;
    ctx.quadraticCurveTo((x0 + x1) / 2, 22 + w, x1, -6 + (i === N - 1 ? -2 : 0));
  }
  ctx.closePath();
}

// bendy ghost arm: a curve whose sag grows as the hand comes closer
function noodle(sx, sy, tx, ty, L, side) {
  let dx = tx - sx, dy = ty - sy, d = Math.hypot(dx, dy) || 1;
  if (d > L) { tx = sx + dx / d * L; ty = sy + dy / d * L; dx = tx - sx; dy = ty - sy; d = L; }
  const sag = Math.sqrt(Math.max(0, L * L - d * d)) * 0.45;
  const nx = -dy / d * side, ny = dx / d * side;
  const cx = (sx + tx) / 2 - nx * sag, cy = (sy + ty) / 2 - ny * sag;
  const pts = [];
  for (let i = 0; i <= 8; i++) { const u = i / 8; pts.push([(1 - u) * (1 - u) * sx + 2 * u * (1 - u) * cx + u * u * tx, (1 - u) * (1 - u) * sy + 2 * u * (1 - u) * cy + u * u * ty]); }
  return { pts, hx: tx, hy: ty };
}

function drawPip(ctx, st) {
  const { e, t, P, V } = st;
  ctx.save();
  ctx.translate(st.x, st.y);
  ctx.scale(st.s, st.s);
  ctx.beginPath(); ellipse(ctx, 0, 4, 130, 16); ctx.fillStyle = 'rgba(8,4,18,0.32)'; ctx.fill();
  const hum = V.hum || 0;
  const bob = Math.sin(t * 2.0) * 2.5 + Math.sin(t * 2.6) * 3 * hum;
  const sway = Math.sin(t * 1.3) * 0.012 + hum * Math.sin(t * 2.6) * 0.045;
  ctx.rotate(P.lean + sway + e.tilt * 0.22 + (st.nod || 0) * 0.03);
  const sq = e.squash + (V.sigh || 0) * 0.35;
  const breath = 1 + 0.016 * Math.sin(t * 1.8);
  ctx.scale(1 + sq * 0.06, (1 - sq * 0.09) * breath);
  ctx.translate(0, -bob);

  // body
  pipBodyPath(ctx, t);
  const g = ctx.createLinearGradient(0, -295, 0, 15);
  g.addColorStop(0, '#f9fbff'); g.addColorStop(1, '#cfd9ee');
  ctx.fillStyle = g; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.beginPath(); ellipse(ctx, 70, -50, 120, 120); ctx.fillStyle = 'rgba(90,100,160,0.13)'; ctx.fill();
  ctx.beginPath(); ellipse(ctx, -38, -255, 30, 17, -0.4); ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.fill();
  ctx.restore();
  pipBodyPath(ctx, t);
  ctx.strokeStyle = INK; ctx.lineWidth = 5.5; ctx.lineJoin = 'round'; ctx.stroke();

  // scarf (orange/black stripes) with fluttering tails
  const wind = 1 + 0.5 * Math.sin(t * 0.9);
  const tail = [];
  for (let i = 0; i < 7; i++) tail.push([52 + i * 13 + Math.sin(t * 3.4 - i * 0.7) * i * 1.6 * wind, -104 + i * 15 + Math.sin(t * 2.1 - i) * i * 0.8]);
  ctx.beginPath(); taper(ctx, tail, 26, 18);
  ctx.fillStyle = '#e8872f'; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.strokeStyle = '#231a22'; ctx.lineWidth = 8;
  for (let i = 1; i < tail.length; i += 2) { ctx.beginPath(); ctx.moveTo(tail[i][0] - 20, tail[i][1] + 6); ctx.lineTo(tail[i][0] + 20, tail[i][1] - 6); ctx.stroke(); }
  ctx.restore();
  ctx.beginPath(); taper(ctx, tail, 26, 18); ctx.strokeStyle = INK; ctx.lineWidth = 3.5; ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(-90, -136); ctx.quadraticCurveTo(0, -112, 90, -136);
  ctx.lineTo(93, -110); ctx.quadraticCurveTo(0, -84, -93, -110); ctx.closePath();
  ctx.fillStyle = '#e8872f'; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.strokeStyle = '#231a22'; ctx.lineWidth = 9;
  for (let x = -110; x < 110; x += 24) { ctx.beginPath(); ctx.moveTo(x, -84); ctx.lineTo(x + 18, -140); ctx.stroke(); }
  ctx.restore();
  ctx.beginPath();
  ctx.moveTo(-90, -136); ctx.quadraticCurveTo(0, -112, 90, -136);
  ctx.lineTo(93, -110); ctx.quadraticCurveTo(0, -84, -93, -110); ctx.closePath();
  ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();

  // face
  ctx.save();
  const fx = st.look[0] * 17, fy = st.look[1] * 9;
  ctx.translate(fx, -200 + fy);
  ctx.rotate(e.tilt * 0.45);
  ctx.beginPath(); ellipse(ctx, -58, 27, 15, 8.5); ellipse(ctx, 58, 27, 15, 8.5);
  ctx.fillStyle = rgba('#ff86ab', 0.16 + e.blush * 0.5); ctx.fill();
  const eo = { rx: 23, ry: 30, irisR: 17.5, pupR: 9.5, iris: '#2f2a5c', irisRing: '#4d4a96', pup: e.pup, look: st.look, lidU: e.lidU, lidL: e.lidL, blink: st.blink, lid: SHEET, lw: 4.2, sparkle: e.sparkle, tear: e.tear, smile: e.smile, warm: (st.light || 0) * 0.35 };
  eye(ctx, { ...eo, x: -37, y: -4 });
  eye(ctx, { ...eo, x: 37, y: -4 });
  brow(ctx, { x: -37, y: -48, w: 30, th: 6, side: -1, raise: e.bU + e.bAsym * 0.55, angle: e.bA, color: '#646a88' });
  brow(ctx, { x: 37, y: -48, w: 30, th: 6, side: 1, raise: e.bU - e.bAsym * 0.55, angle: e.bA, color: '#646a88' });
  mouth(ctx, { x: 0, y: 40, w: 30, mW: e.mW * (st.mw || 1), smile: e.smile, open: st.open, round: st.round, lw: 4, inside: '#3b1d3c', tongueOut: e.tongue });
  tearDrop(ctx, -22, 30 + Math.sin(t * 2) * 2, 6.5, e.tear);
  ctx.restore();

  // pumpkin held
  if (st.pumpkin) {
    const pk = st.pumpkin;
    drawPumpkin(ctx, { x: pk.x ?? P.pkx, y: pk.y ?? P.pky, r: 46, face: 'pip', carve: V.carve || 0, lit: V.pipLit || 0, turn: 1 - (V.pipTurn || 0), t, light: (V.pipLit || 0) > 0.2 });
  }

  // arms
  const carving = V.carving || 0;
  const bx = P.bx + Math.sin(t * 11) * 9 * carving, by = P.by + Math.cos(t * 11) * 7 * carving;
  const arms = [[-82, -90, P.ax, P.ay, -1], [82, -90, bx, by, 1]];
  for (const [sx, sy, tx, ty, bend] of arms) {
    const j = noodle(sx, sy, tx, ty, 92, bend);
    limb(ctx, j.pts, 31, SHEET, INK, 4.5);
    ctx.beginPath(); ellipse(ctx, j.hx, j.hy, 17, 17); ctx.fillStyle = SHEET; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
    ctx.beginPath(); ellipse(ctx, sx, sy, 15, 15); ctx.fillStyle = SHEET; ctx.fill();
    if (bend > 0 && P.spoon > 0.5) {
      ctx.save(); ctx.translate(j.hx, j.hy); ctx.rotate(2.3 + Math.sin(t * 11) * 0.3 * carving);
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(44, 0); ctx.strokeStyle = INK; ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.stroke();
      ctx.strokeStyle = '#c9cdd8'; ctx.lineWidth = 4.5; ctx.stroke();
      ctx.beginPath(); ellipse(ctx, 50, 0, 10, 7); ctx.fillStyle = '#d9dde6'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
      ctx.restore();
    }
  }

  // warm under-light from the lantern
  if ((st.light || 0) > 0.01 && st.pumpkin) {
    ctx.save();
    pipBodyPath(ctx, t); ctx.clip();
    const px = P.pkx, py = P.pky;
    const fl = 1 + 0.05 * noise(t * 6);
    const lg = ctx.createRadialGradient(px, py, 10, px, py, 300 * fl);
    lg.addColorStop(0, rgba('#ffab52', 0.7 * st.light));
    lg.addColorStop(0.5, rgba('#ffc98a', 0.35 * st.light));
    lg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.globalAlpha = 0.3; ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = lg; ctx.fillRect(-200, -320, 400, 360);
    ctx.globalCompositeOperation = 'screen';
    const lg2 = ctx.createRadialGradient(px, py, 10, px, py, 220);
    lg2.addColorStop(0, rgba('#ff9a3a', 0.32 * st.light)); lg2.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = lg2; ctx.fillRect(-200, -320, 400, 360);
    ctx.restore();
  }
  ctx.restore();
}

// ───────────────────────── PATCH (the patchwork giant) ─────────────────────────
const PATCH_BASE = { ax: -98, ay: -78, bx: 98, by: -78, pkx: 0, pky: -78, lean: 0 };
const PATCH_POSES = {
  holdPumpkin: {},
  sit: { ax: -100, ay: 70, bx: 100, by: 70, pkx: 220, pky: -64 },
  lookHands: { ax: -66, ay: -322, bx: 58, by: -300, pkx: 220, pky: -64, lean: 0.03 },
  touchEar: { ax: -100, ay: 60, bx: 124, by: -488, pkx: 220, pky: -64 },
  handChest: { ax: -100, ay: 60, bx: 44, by: -240, pkx: 220, pky: -64, lean: 0.02 },
  showPumpkin: { ax: -172, ay: -205, bx: -12, by: -210, pkx: -92, pky: -222, lean: -0.05 },
  lean: { lean: -0.09 },
  pointSelf: { bx: 34, by: -300, pkx: -14 },
  climb: { ax: -150, ay: -2, bx: 150, by: -2, pkx: 150, pky: -66 },
};
const PSKIN = '#8fb08a', PSKIN_D = '#789872', COAT = '#46573b';

function drawPatch(ctx, st) {
  const { e, t, P, V } = st;
  const climb = st.climb ?? 1, sitDown = st.sitDown ?? 1;
  ctx.save();
  ctx.translate(st.x, st.y);
  ctx.scale(st.s, st.s);
  const shake = (V.roofShake || 0) * Math.sin(t * 60) * 4;
  ctx.translate(shake, (1 - climb) * 650 - 38 * (1 - sitDown) * (climb > 0.99 ? 1 : 0));
  const seated = climb > 0.99;
  if (seated) { ctx.beginPath(); ellipse(ctx, 0, 30, 190, 28); ctx.fillStyle = 'rgba(8,4,18,0.3)'; ctx.fill(); }

  // legs
  if (seated) {
    for (const sd of [-1, 1]) {
      limb(ctx, [[sd * 72, -10], [sd * 96, 92], [sd * 102, 300]], 92, '#3b3248', INK, 6);
      ctx.beginPath(); ellipse(ctx, sd * 98, 120, 34, 26); ctx.fillStyle = sd < 0 ? '#6b4f7a' : '#3b3248'; ctx.fill();
      if (sd < 0) { ctx.strokeStyle = '#2a2236'; ctx.lineWidth = 3; ctx.setLineDash([6, 6]); ctx.stroke(); ctx.setLineDash([]); }
      ctx.beginPath(); ellipse(ctx, sd * 110, 330, 72, 42); ctx.fillStyle = '#2b1f1b'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.stroke();
      ctx.beginPath(); ellipse(ctx, sd * 92, 318, 30, 12, -0.2 * sd); ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fill();
    }
  }
  const breath = Math.sin(t * 1.25) * 0.012;
  ctx.rotate(P.lean + e.tilt * 0.15 + Math.sin(t * 0.7) * 0.01 + (st.nod || 0) * 0.02);
  ctx.save();
  ctx.scale(1, 1 + breath);

  // torso / coat
  const torso = [[-150, 15], [-160, -120], [-174, -250], [-150, -305], [-62, -345], [62, -345], [150, -305], [174, -250], [160, -120], [150, 15], [0, 34]];
  ctx.beginPath(); smoothPath(ctx, torso, true, 0.6);
  ctx.fillStyle = COAT; ctx.fill();
  ctx.save(); ctx.clip();
  const sh = ctx.createLinearGradient(-170, 0, 170, 0);
  sh.addColorStop(0, 'rgba(255,255,220,0.06)'); sh.addColorStop(1, 'rgba(10,10,30,0.3)');
  ctx.fillStyle = sh; ctx.fillRect(-200, -360, 400, 400);
  // shirt V and lapels
  ctx.beginPath(); ctx.moveTo(-62, -350); ctx.lineTo(0, -214); ctx.lineTo(62, -350); ctx.closePath(); ctx.fillStyle = '#cbbd96'; ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  for (const sd of [-1, 1]) {
    ctx.beginPath(); ctx.moveTo(sd * 62, -350); ctx.lineTo(sd * 18, -240); ctx.lineTo(sd * 96, -292); ctx.closePath();
    ctx.fillStyle = '#38462e'; ctx.fill(); ctx.stroke();
  }
  // patches
  const patchSq = (x, y, w, h, r, c) => {
    ctx.save(); ctx.translate(x, y); ctx.rotate(r);
    ctx.beginPath(); ctx.rect(-w / 2, -h / 2, w, h); ctx.fillStyle = c; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3.5; ctx.stroke();
    ctx.strokeStyle = '#e8dcb8'; ctx.lineWidth = 2.5;
    for (let i = -w / 2 + 6; i < w / 2; i += 10) { ctx.beginPath(); ctx.moveTo(i, -h / 2 - 4); ctx.lineTo(i + 3, -h / 2 + 4); ctx.stroke(); ctx.beginPath(); ctx.moveTo(i, h / 2 - 4); ctx.lineTo(i + 3, h / 2 + 4); ctx.stroke(); }
    ctx.restore();
  };
  patchSq(-112, -205, 58, 52, 0.1, '#7b5b8f');
  patchSq(108, -110, 62, 46, -0.12, '#c48a3c');
  patchSq(-70, -60, 44, 40, 0.2, '#3f6f7a');
  ctx.restore();
  ctx.beginPath(); smoothPath(ctx, torso, true, 0.6); ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, 0, -150, 10, 10); ctx.fillStyle = '#c9a24a'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
  ctx.beginPath(); ctx.rect(-9, -98, 18, 18); ctx.fillStyle = '#8a8f9a'; ctx.fill(); ctx.stroke();
  ctx.restore();

  // pumpkin (his carved one)
  const pk = st.pumpkinPos || [P.pkx, P.pky];
  drawPumpkin(ctx, { x: pk[0], y: pk[1], r: 72, face: 'patch', lit: 1, turn: 1 - (V.patchTurn || 0), t, glow: (V.patchTurn || 0) > 0.5 });

  // neck + bolts
  ctx.beginPath(); ctx.rect(-50, -398, 100, 64); ctx.fillStyle = '#7d9b77'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-50, -352); ctx.quadraticCurveTo(0, -340, 50, -352); ctx.strokeStyle = '#33402f'; ctx.lineWidth = 3.5; ctx.stroke();
  for (let i = -4; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(i * 11 - 3, -356 + Math.abs(i) * 0.6); ctx.lineTo(i * 11 + 3, -340 + Math.abs(i) * 0.6); ctx.stroke(); }

  // head
  const hy = -500 + (st.look[1] > 0.5 ? (st.look[1] - 0.5) * 16 : 0);
  ctx.save();
  ctx.translate(0, hy);
  ctx.rotate(e.tilt * 0.5);
  // ears
  ctx.beginPath(); ellipse(ctx, -112, 5, 19, 32); ctx.fillStyle = PSKIN; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, 113, 5, 22, 30); ctx.fillStyle = '#9fbd8c'; ctx.fill(); ctx.stroke();
  const headPts = [[-96, -110], [0, -132], [96, -110], [110, -60], [108, 30], [96, 90], [50, 118], [0, 122], [-50, 118], [-96, 90], [-108, 30], [-110, -60]];
  ctx.beginPath(); smoothPath(ctx, headPts, true, 0.55);
  ctx.fillStyle = PSKIN; ctx.fill();
  ctx.save(); ctx.clip();
  const hg = ctx.createLinearGradient(-110, 0, 110, 0);
  hg.addColorStop(0, 'rgba(255,255,230,0.12)'); hg.addColorStop(0.55, 'rgba(0,0,0,0)'); hg.addColorStop(1, 'rgba(20,30,40,0.28)');
  ctx.fillStyle = hg; ctx.fillRect(-120, -130, 240, 260);
  ctx.restore();
  ctx.beginPath(); smoothPath(ctx, headPts, true, 0.55); ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.stroke();
  // earring (fisherman's ear)
  ctx.beginPath(); ctx.arc(118, 36, 9, 0, TAU); ctx.strokeStyle = '#e6b84a'; ctx.lineWidth = 4; ctx.stroke();
  // hair
  // shaggy mop of hair with a stray curl
  const hair = [[-118, -40], [-126, -96], [-104, -140], [-60, -160], [-10, -166], [44, -160], [92, -142], [122, -100], [118, -40], [100, -74], [84, -56], [70, -88], [48, -64], [26, -90], [2, -66], [-20, -92], [-44, -66], [-66, -92], [-88, -60], [-102, -82]];
  ctx.beginPath(); smoothPath(ctx, hair, true, 0.35);
  ctx.fillStyle = '#251d2e'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
  ctx.strokeStyle = '#3a2f46'; ctx.lineWidth = 3;
  for (const [x0, y0, x1, y1] of [[-80, -140, -60, -100], [-30, -156, -20, -110], [30, -154, 20, -108], [80, -138, 70, -100]]) { ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(x0 + 18, (y0 + y1) / 2, x1, y1); ctx.stroke(); }
  ctx.beginPath(); spiralPts(-4, -186, 18, 1.1, 1, Math.PI * 0.5).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1] + 22)));
  ctx.strokeStyle = INK; ctx.lineWidth = 9; ctx.lineCap = 'round'; ctx.stroke(); ctx.strokeStyle = '#251d2e'; ctx.lineWidth = 5; ctx.stroke();
  // forehead stitch
  const fx = -8 + st.look[0] * 16, fy = clamp(st.look[1], -1, 1) * 11;
  ctx.beginPath(); ctx.moveTo(-72, -58); ctx.quadraticCurveTo(-5, -70, 66, -50);
  ctx.strokeStyle = '#33402f'; ctx.lineWidth = 4; ctx.stroke();
  for (let i = 0; i < 6; i++) { const x = -60 + i * 24; const y = -58 - Math.sin((i / 5) * Math.PI) * 6 + i * 1.5; ctx.beginPath(); ctx.moveTo(x - 4, y - 9); ctx.lineTo(x + 4, y + 9); ctx.stroke(); }
  // cheek stitch
  ctx.beginPath(); ctx.moveTo(-78 + fx * 0.5, 50); ctx.lineTo(-62 + fx * 0.5, 88); ctx.stroke();
  for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.moveTo(-80 + fx * 0.5 + i * 6, 58 + i * 12); ctx.lineTo(-62 + fx * 0.5 + i * 6, 54 + i * 12); ctx.stroke(); }
  ctx.save(); ctx.translate(fx, fy);
  // eye bags
  ctx.beginPath(); ctx.arc(-46, 20, 22, 0.25 * Math.PI, 0.75 * Math.PI); ctx.moveTo(46 + 19 * Math.cos(0.25 * Math.PI), 22 + 19 * Math.sin(0.25 * Math.PI)); ctx.arc(46, 22, 19, 0.25 * Math.PI, 0.75 * Math.PI);
  ctx.strokeStyle = rgba('#45603f', 0.7); ctx.lineWidth = 3; ctx.stroke();
  const lid = clamp(e.lidU * 0.9 + 0.12, -1, 1);
  eye(ctx, { x: -46, y: 0, rx: 25, ry: 27, irisR: 15, pupR: 8, iris: '#4f86c6', irisRing: '#6fa3dd', pup: e.pup, look: st.look, lidU: lid, lidL: e.lidL, blink: st.blink, lid: PSKIN, lw: 5, sclera: '#f2f0e2', sparkle: e.sparkle, tear: e.tear, smile: e.smile, warm: st.light });
  eye(ctx, { x: 46, y: 2, rx: 21, ry: 23, irisR: 13, pupR: 7, iris: '#d39b2e', irisRing: '#e8b958', pup: e.pup, look: st.look, lidU: lid, lidL: e.lidL, blink: st.blink, lid: PSKIN, lw: 5, sclera: '#f2f0e2', sparkle: e.sparkle, tear: e.tear, smile: e.smile, warm: st.light });
  brow(ctx, { x: -46, y: -42, w: 58, th: 13, side: -1, raise: e.bU + e.bAsym * 0.5, angle: e.bA, color: '#262130', k: 1.5, arch: 4 });
  brow(ctx, { x: 46, y: -40, w: 54, th: 13, side: 1, raise: e.bU - e.bAsym * 0.5, angle: e.bA, color: '#262130', k: 1.5, arch: 4 });
  // nose
  ctx.beginPath(); ctx.moveTo(-10, 0); ctx.quadraticCurveTo(-26, 34, -16, 44); ctx.quadraticCurveTo(0, 52, 16, 44); ctx.quadraticCurveTo(26, 34, 10, 0);
  ctx.fillStyle = PSKIN_D; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  mouth(ctx, { x: 0, y: 80, w: 80, mW: e.mW * (st.mw || 1), smile: e.smile, open: st.open, round: st.round, lw: 5, inside: '#2a1520', teeth: '#efe8c8', tongueColor: '#c96a7a', creases: true });
  tearDrop(ctx, -30, 30 + Math.sin(t * 2) * 2, 9, e.tear);
  ctx.restore();
  ctx.restore();

  // arms (in front of everything else)
  const wig = V.fingers || 0;
  const arms = [[-160, -282, P.ax, P.ay, -1, '#a9c1a0'], [160, -282, P.bx, P.by, 1, PSKIN]];
  for (const [sx, sy, tx, ty, bend, skin] of arms) {
    const j = ik(sx, sy, tx, ty, 150, 140, bend);
    limb(ctx, [[sx, sy], [j.ex, j.ey], [j.hx, j.hy]], 64, COAT, INK, 6);
    const ang = Math.atan2(j.hy - j.ey, j.hx - j.ex);
    ctx.beginPath(); ctx.moveTo(j.hx - Math.cos(ang) * 46, j.hy - Math.sin(ang) * 46); ctx.lineTo(j.hx - Math.cos(ang) * 30, j.hy - Math.sin(ang) * 30);
    ctx.strokeStyle = INK; ctx.lineWidth = 76; ctx.lineCap = 'butt'; ctx.stroke(); ctx.strokeStyle = '#36442d'; ctx.lineWidth = 66; ctx.stroke();
    hand(ctx, j.hx, j.hy, ang, 40, skin, { stitch: '#3c4a38', wiggle: wig, t, lw: 5, thumbSide: bend > 0 ? -1 : 1 });
  }
  ctx.restore();
}

// ───────────────────────── AUNTIE BRAMBLE (the witch) ─────────────────────────
const BRAM_BASE = { kneel: 0, ax: -92, ay: -232, bx: 72, by: -228, broom: 0, lean: 0 };
const BRAM_POSES = {
  stand: {},
  fly: { kneel: 0.55, ax: -70, ay: -205, bx: 96, by: -470, broom: 1, lean: -0.05 },
  kneel: { kneel: 1, ax: -62, ay: -118, bx: 58, by: -112, broom: 2, lean: 0.08 },
  offer: { kneel: 1, ax: -62, ay: -118, bx: 130, by: -165, broom: 2, lean: 0.1 },
  snap: { kneel: 1, ax: -62, ay: -118, bx: 128, by: -340, broom: 2, lean: 0.05 },
  handMouth: { kneel: 1, ax: -55, ay: -120, bx: 18, by: -312, broom: 2, lean: 0.06 },
  armAround: { kneel: 1, ax: -62, ay: -118, bx: 190, by: -235, broom: 2, lean: 0.12 },
};
const BSKIN = '#a8c76a', DRESS = '#66388a';

function drawBroom(ctx, x1, y1, x2, y2) {
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
  ctx.strokeStyle = INK; ctx.lineWidth = 15; ctx.lineCap = 'round'; ctx.stroke();
  ctx.strokeStyle = '#7a5232'; ctx.lineWidth = 9; ctx.stroke();
  const a = Math.atan2(y2 - y1, x2 - x1);
  ctx.save(); ctx.translate(x2, y2); ctx.rotate(a);
  ctx.beginPath(); ctx.moveTo(-6, -12); ctx.quadraticCurveTo(60, -40, 95, -30); ctx.lineTo(100, 30); ctx.quadraticCurveTo(60, 40, -6, 12); ctx.closePath();
  ctx.fillStyle = '#c9a24a'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.strokeStyle = '#94742c'; ctx.lineWidth = 3;
  for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(20, i * 6); ctx.lineTo(92, i * 11); ctx.stroke(); }
  ctx.beginPath(); ctx.rect(-4, -14, 14, 28); ctx.fillStyle = '#8b59b8'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  ctx.restore();
}

function drawBram(ctx, st) {
  const { e, t, P, V } = st;
  const k = clamp(P.kneel, 0, 1);
  const uy = 150 * k;
  const broom = Math.round(P.broom);
  ctx.save();
  ctx.translate(st.x, st.y);
  if (st.rot) ctx.rotate(st.rot);
  ctx.scale(st.s * (st.flip || 1), st.s);
  if (!st.flying) { ctx.beginPath(); ellipse(ctx, 0, 4, 140, 18); ctx.fillStyle = 'rgba(8,4,18,0.3)'; ctx.fill(); }
  if (broom === 2) drawBroom(ctx, 40, -12, -230, -6);
  if (broom === 0) drawBroom(ctx, -92, -420, -112, -40);
  if (broom === 1) drawBroom(ctx, -200, -160 + uy * 0.4, 150, -150 + uy * 0.4);

  const hemY = -95 + 85 * k, hemW = 125 + 35 * k, waistY = -330 + uy;
  // legs
  if (k < 0.5 && !st.flying) {
    for (const sd of [-1, 1]) {
      ctx.save();
      ctx.beginPath(); ctx.rect(sd * 32 - 15, hemY - 5, 30, -hemY - 15); ctx.fillStyle = '#f2ede2'; ctx.fill();
      ctx.save(); ctx.clip(); ctx.fillStyle = '#1e1824';
      for (let y = hemY; y < -10; y += 22) ctx.fillRect(sd * 32 - 16, y, 32, 11);
      ctx.restore();
      ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
      ctx.restore();
      ctx.beginPath(); ctx.moveTo(sd * 18, -26); ctx.quadraticCurveTo(sd * 80, -30, sd * 92, -48); ctx.quadraticCurveTo(sd * 104, -60, sd * 96, -44);
      ctx.quadraticCurveTo(sd * 84, -4, sd * 18, 0); ctx.closePath(); ctx.fillStyle = '#1c1720'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
    }
  } else if (!st.flying) {
    ctx.beginPath(); ctx.moveTo(-60, -20); ctx.quadraticCurveTo(-140, -24, -156, -44); ctx.quadraticCurveTo(-164, -56, -150, -40); ctx.quadraticCurveTo(-130, 0, -60, 0); ctx.closePath();
    ctx.fillStyle = '#1c1720'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  }
  // dress
  const flow = st.flying ? 40 : 0;
  const dress = [[-58, waistY]];
  const nz = 9;
  for (let i = 0; i <= nz; i++) {
    const x = -hemW + (i * 2 * hemW) / nz + flow * (i / nz);
    const y = hemY + (i % 2 ? 22 : 0) + Math.sin(t * 2 + i) * 3;
    dress.push([x, y]);
  }
  dress.push([58, waistY]);
  ctx.beginPath(); ctx.moveTo(dress[0][0], dress[0][1]);
  ctx.quadraticCurveTo(-hemW * 0.75, (waistY + hemY) / 2, dress[1][0], dress[1][1]);
  for (let i = 2; i < dress.length - 1; i++) ctx.lineTo(dress[i][0], dress[i][1]);
  ctx.quadraticCurveTo(hemW * 0.75 + flow, (waistY + hemY) / 2, 58, waistY);
  ctx.closePath();
  const dg = ctx.createLinearGradient(-hemW, 0, hemW, 0);
  dg.addColorStop(0, '#7a48a0'); dg.addColorStop(1, '#4b2a66');
  ctx.fillStyle = dg; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.lineJoin = 'round'; ctx.stroke();
  // little stitched star patch
  ctx.save(); ctx.translate(-40, waistY + 120); ctx.beginPath();
  for (let i = 0; i < 10; i++) { const a = (i / 10) * TAU - Math.PI / 2, r = i % 2 ? 7 : 16; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
  ctx.closePath(); ctx.fillStyle = '#e8872f'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke(); ctx.restore();

  // upper body rotates around the waist
  ctx.save();
  ctx.translate(0, waistY);
  ctx.rotate(P.lean + e.tilt * 0.2 + Math.sin(t * 1.1) * 0.012 + (st.nod || 0) * 0.03);
  ctx.translate(0, -waistY);
  const shY = -420 + uy;
  const wx = (px, py) => { // body-frame helper (pose targets are in unrotated base frame)
    const a = -(P.lean + e.tilt * 0.2);
    const dx = px, dy = py - waistY;
    return [dx * Math.cos(a) - dy * Math.sin(a), waistY + dx * Math.sin(a) + dy * Math.cos(a)];
  };
  const armDraw = (sx, tx, ty, bend, props) => {
    const [ttx, tty] = wx(tx, ty);
    const j = ik(sx, shY + 6, ttx, tty, 100, 92, bend);
    limb(ctx, [[sx, shY + 6], [j.ex, j.ey], [j.hx, j.hy]], 30, DRESS, INK, 4.5);
    const ang = Math.atan2(j.hy - j.ey, j.hx - j.ex);
    ctx.save(); ctx.translate(j.hx - Math.cos(ang) * 22, j.hy - Math.sin(ang) * 22); ctx.rotate(ang);
    ctx.beginPath(); ctx.moveTo(-8, -18); ctx.lineTo(10, -26); ctx.lineTo(10, 26); ctx.lineTo(-8, 18); ctx.closePath();
    ctx.fillStyle = '#4f2b6c'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke(); ctx.restore();
    if (props) props(j, ang);
    hand(ctx, j.hx, j.hy, ang, 17, BSKIN, { long: true, lw: 3.5, thumbSide: bend > 0 ? -1 : 1, fist: props && props.fist });
    if (props && props.after) props.after(j, ang);
  };
  // torso
  ctx.beginPath(); ctx.moveTo(-58, waistY + 4); ctx.lineTo(-70, shY + 10); ctx.quadraticCurveTo(0, shY - 22, 70, shY + 10); ctx.lineTo(58, waistY + 4); ctx.closePath();
  ctx.fillStyle = DRESS; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  armDraw(-66, P.ax, P.ay, -1);
  // shawl
  ctx.beginPath(); ctx.moveTo(-80, shY + 2); ctx.quadraticCurveTo(0, shY - 18, 80, shY + 2); ctx.lineTo(10, shY + 112); ctx.lineTo(-10, shY + 112); ctx.closePath();
  ctx.fillStyle = '#c27a32'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
  ctx.strokeStyle = '#8a5222'; ctx.lineWidth = 3;
  for (let i = -3; i <= 3; i++) { ctx.beginPath(); ctx.moveTo(i * 9, shY + 105 - Math.abs(i) * 14); ctx.lineTo(i * 9 + 2, shY + 122 - Math.abs(i) * 14); ctx.stroke(); }
  // neck
  ctx.beginPath(); ctx.rect(-14, shY - 30, 28, 30); ctx.fillStyle = '#97b55c'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();

  // head
  const hy = -500 + uy;
  ctx.save();
  ctx.translate(0, hy);
  ctx.rotate(e.tilt * 0.5);
  const fx = 6 + st.look[0] * 12, fy = clamp(st.look[1], -1, 1) * 8;
  // hair back
  ctx.fillStyle = '#2a2233';
  ctx.beginPath(); ellipse(ctx, -58, -10, 40, 64, 0.3); ellipse(ctx, 58, -10, 40, 64, -0.3); ctx.fill();
  ctx.beginPath(); ellipse(ctx, 0, 0, 58, 68);
  ctx.fillStyle = BSKIN; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = 'rgba(30,40,20,0.18)'; ctx.beginPath(); ellipse(ctx, 40, 10, 40, 80); ctx.fill();
  ctx.restore();
  ctx.beginPath(); ellipse(ctx, 0, 0, 58, 68); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  // chin point
  ctx.beginPath(); ctx.moveTo(-18, 62); ctx.quadraticCurveTo(4 + fx * 0.3, 92, 22, 62); ctx.fillStyle = BSKIN; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
  ctx.beginPath(); ctx.rect(-18, 52, 40, 12); ctx.fillStyle = BSKIN; ctx.fill();
  ctx.save(); ctx.translate(fx, fy);
  ctx.beginPath(); ellipse(ctx, -34, 20, 13, 8); ellipse(ctx, 36, 20, 13, 8); ctx.fillStyle = rgba('#e0707a', 0.25 + e.blush * 0.35); ctx.fill();
  const eo = { rx: 15, ry: 16, irisR: 10, pupR: 5, iris: '#9a6a2a', irisRing: '#c49a4a', pup: e.pup, look: st.look, lidU: clamp(e.lidU * 0.9 + 0.08, -1, 1), lidL: e.lidL, blink: st.blink, lid: BSKIN, lw: 3.5, sclera: '#fbf7ea', sparkle: e.sparkle, tear: e.tear, smile: e.smile, warm: st.light };
  eye(ctx, { ...eo, x: -24, y: -14 });
  eye(ctx, { ...eo, x: 26, y: -14 });
  if (e.smile > 0.3 || e.lidL > 0.2) {
    ctx.globalAlpha = clamp((Math.max(e.smile, e.lidL * 2) - 0.3) * 2);
    ctx.strokeStyle = INK; ctx.lineWidth = 2.5; ctx.lineCap = 'round';
    for (const sd of [-1, 1]) for (let i = -1; i <= 1; i++) { ctx.beginPath(); ctx.moveTo(sd * 44 + (sd < 0 ? -2 : 4), -14 + i * 7); ctx.lineTo(sd * 54 + (sd < 0 ? -2 : 4), -16 + i * 11); ctx.stroke(); }
    ctx.globalAlpha = 1;
  }
  brow(ctx, { x: -24, y: -40, w: 26, th: 5, side: -1, raise: e.bU + e.bAsym * 0.5, angle: e.bA, color: '#4a3a55', arch: 7 });
  brow(ctx, { x: 26, y: -40, w: 26, th: 5, side: 1, raise: e.bU - e.bAsym * 0.5, angle: e.bA, color: '#4a3a55', arch: 7 });
  mouth(ctx, { x: 2, y: 38, w: 36, mW: e.mW * (st.mw || 1), smile: e.smile, open: st.open, round: st.round, lw: 3.8, inside: '#3a1428', teeth: '#f4efe0', creases: true });
  // long nose with a wart
  ctx.beginPath(); ctx.moveTo(-4, -6); ctx.quadraticCurveTo(10, 4, 34, 26); ctx.quadraticCurveTo(38, 32, 30, 32); ctx.quadraticCurveTo(14, 30, 2, 20); ctx.closePath();
  ctx.fillStyle = '#9dbd5f'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3.8; ctx.lineJoin = 'round'; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, 18, 10, 3.2, 3.2); ctx.fillStyle = '#7e9a46'; ctx.fill();
  tearDrop(ctx, -16, 4 + Math.sin(t * 2) * 1.5, 5, e.tear);
  ctx.restore();
  // hair tufts with curls
  ctx.fillStyle = '#2a2233'; ctx.strokeStyle = INK; ctx.lineWidth = 4;
  for (const sd of [-1, 1]) {
    ctx.beginPath(); ctx.moveTo(sd * 30, -62); ctx.quadraticCurveTo(sd * 90, -60, sd * 86, 0); ctx.quadraticCurveTo(sd * 84, 34, sd * 66, 52); ctx.quadraticCurveTo(sd * 60, 20, sd * 50, -30); ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.beginPath(); spiralPts(sd * 74, 58, 14, 1.2, sd, 0).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.strokeStyle = '#2a2233'; ctx.lineWidth = 6; ctx.stroke(); ctx.strokeStyle = INK; ctx.lineWidth = 4;
  }
  ctx.beginPath(); ctx.moveTo(52, -40); ctx.quadraticCurveTo(76, -10, 70, 30); ctx.strokeStyle = '#8d8696'; ctx.lineWidth = 5; ctx.stroke();
  // hat
  const fly = st.flying ? 1 : 0;
  const tipX = 50 + Math.sin(t * 1.4) * 10 + fly * 70, tipY = -330 + fly * 40;
  ctx.beginPath();
  ctx.moveTo(-60, -72);
  ctx.bezierCurveTo(-46, -150, -20, -250, tipX - 8, tipY + 10);
  ctx.bezierCurveTo(tipX * 0.55 + 20, -230, 50, -150, 62, -72);
  ctx.closePath();
  ctx.fillStyle = '#2a1f38'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.beginPath(); spiralPts(tipX + 10, tipY + 12, 20, 1.15, 1, Math.PI).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
  ctx.strokeStyle = INK; ctx.lineWidth = 13; ctx.lineCap = 'round'; ctx.stroke(); ctx.strokeStyle = '#2a1f38'; ctx.lineWidth = 7; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-58, -78); ctx.lineTo(-55, -100); ctx.quadraticCurveTo(0, -112, 57, -98); ctx.lineTo(61, -78); ctx.quadraticCurveTo(0, -88, -58, -78);
  ctx.fillStyle = '#8b59b8'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  ctx.beginPath(); ctx.rect(-12, -104, 24, 22); ctx.strokeStyle = '#e0bb4f'; ctx.lineWidth = 5; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, 0, -68, 118, 22, 0.04);
  ctx.fillStyle = '#241a30'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.restore();

  // front arm with props
  const props = (j, ang) => {
    if ((V.bramPumpkin || 0) > 0.05 && (V.pumpkinToPip || 0) < 0.5 && st.offerPumpkin) {
      ctx.save(); ctx.globalAlpha = clamp(V.bramPumpkin * 2);
      drawPumpkin(ctx, { x: j.hx + 6, y: j.hy - 40, r: 46, face: null, t });
      ctx.restore();
      if (V.bramPumpkin < 1) { // sparkle as it appears
        for (let i = 0; i < 6; i++) { const a = i * 1.05 + t * 3; const r = 60 + 20 * V.bramPumpkin; ctx.beginPath(); ellipse(ctx, j.hx + Math.cos(a) * r, j.hy - 40 + Math.sin(a) * r, 4, 4); ctx.fillStyle = rgba('#ffe9a8', 1 - V.bramPumpkin); ctx.fill(); }
      }
    }
  };
  props.after = (j) => {
    const sp = V.spark || 0;
    if (sp > 0.02) {
      const g = ctx.createRadialGradient(j.hx + 10, j.hy - 20, 2, j.hx + 10, j.hy - 20, 90);
      g.addColorStop(0, rgba('#fff6c8', sp)); g.addColorStop(0.3, rgba('#ffc04a', 0.6 * sp)); g.addColorStop(1, 'rgba(255,160,60,0)');
      ctx.fillStyle = g; ctx.beginPath(); ellipse(ctx, j.hx + 10, j.hy - 20, 90, 90); ctx.fill();
      ctx.strokeStyle = rgba('#fff3b0', sp); ctx.lineWidth = 4;
      for (let i = 0; i < 8; i++) { const a = (i / 8) * TAU + t * 2; ctx.beginPath(); ctx.moveTo(j.hx + 10 + Math.cos(a) * 26, j.hy - 20 + Math.sin(a) * 26); ctx.lineTo(j.hx + 10 + Math.cos(a) * 52, j.hy - 20 + Math.sin(a) * 52); ctx.stroke(); }
    }
  };
  armDraw(66, P.bx, P.by, 1, props);
  ctx.restore();
  ctx.restore();
}

// ───────────────────────── SKELETONS ─────────────────────────
const SKEL_BASE = { ax: -74, ay: -182, bx: 74, by: -182, fax: -40, fay: 0, fbx: 40, fby: 0, lean: 0, hip: -262, headUp: 0, dance: 0, shake: 0, fiddle: 0, hop: 0, headTilt: 0 };
const SKEL_POSES = {
  stand: {},
  dance: { dance: 1 },
  hop: { ax: 18, ay: -150, bx: 54, by: -140, fax: -30, fay: 0, fbx: 44, fby: -122, lean: 0.12, hop: 1 },
  akimbo: { ax: -54, ay: -262, bx: 54, by: -262, lean: -0.05, headTilt: 0.12 },
  point: { ax: -72, ay: -190, bx: 210, by: -400, lean: 0.08 },
  laugh: { ax: -32, ay: -300, bx: 32, by: -296, lean: -0.12, shake: 1 },
  catchJaw: { ax: -28, ay: -322, bx: 28, by: -322, lean: 0.14 },
  fiddle: { ax: -150, ay: -400, bx: 40, by: -350, fiddle: 1, lean: -0.05, headTilt: 0.22 },
  lookUp: { ax: -20, ay: -350, bx: 20, by: -350, headUp: 1 },
  shush: { ax: -72, ay: -186, bx: 8, by: -412, lean: 0.06 },
};
const BONE = '#f1ead8';

function bone(ctx, a, b, w) {
  limb(ctx, [a, b], w, BONE, INK, 4.5);
  for (const p of [a, b]) { ctx.beginPath(); ellipse(ctx, p[0], p[1], w * 0.62, w * 0.62); ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke(); }
  limb(ctx, [a, b], w - 1, BONE, BONE, 0);
}

function drawSkeleton(ctx, st, style) {
  const { e, t, V } = st;
  const P = { ...st.P };
  const dance = clamp(P.dance * (V.dance ?? 0) + 0);
  const ph = t * Math.PI * 2 * 1.05 + (style === 'clatter' ? Math.PI : 0);
  let bounce = 0;
  if (dance > 0.01) {
    const s1 = Math.sin(ph);
    P.fax = lerp(P.fax, -42 + Math.cos(ph) * 12, dance); P.fay = lerp(P.fay, -Math.max(0, s1) * 75, dance);
    P.fbx = lerp(P.fbx, 42 + Math.cos(ph) * 12, dance); P.fby = lerp(P.fby, -Math.max(0, -s1) * 75, dance);
    P.ax = lerp(P.ax, -125, dance); P.ay = lerp(P.ay, -330 - 90 * Math.max(0, s1), dance);
    P.bx = lerp(P.bx, 125, dance); P.by = lerp(P.by, -330 - 90 * Math.max(0, -s1), dance);
    P.lean = lerp(P.lean, 0.13 * s1, dance); P.headTilt = lerp(P.headTilt, -0.12 * s1, dance);
    bounce = Math.abs(Math.sin(ph * 2)) * 14 * dance;
  }
  if (P.hop > 0.01) bounce += Math.abs(Math.sin(t * 9)) * 26 * P.hop;
  const shakeY = P.shake * Math.sin(t * 26) * 4;
  ctx.save();
  ctx.translate(st.x, st.y);
  ctx.scale(st.s * (st.flip || 1), st.s);
  ctx.beginPath(); ellipse(ctx, 0, 6, 90, 14); ctx.fillStyle = 'rgba(8,4,18,0.3)'; ctx.fill();
  const R = (x, y, a) => [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)];
  const pel = [0, P.hip - bounce + shakeY];
  const lean = P.lean + (st.nod || 0) * 0.04;
  const ch = R(0, -160, lean); const chest = [pel[0] + ch[0], pel[1] + ch[1]];
  const nk = R(0, -46, lean); const neck = [chest[0] + nk[0], chest[1] + nk[1]];
  const headA = lean + P.headTilt + e.tilt * 0.6 - P.headUp * 0.0;
  const sk = R(0, -74, headA); const skull = [neck[0] + sk[0], neck[1] + sk[1]];
  // legs
  const legs = [[-30, P.fax, P.fay, -1], [30, P.fbx, P.fby, 1]];
  for (const [hx, fx, fy, bend] of legs) {
    const hip = [pel[0] + hx, pel[1] + 10];
    const j = ik(hip[0], hip[1], fx, fy - 8, 126, 122, bend);
    bone(ctx, hip, [j.ex, j.ey], 15); bone(ctx, [j.ex, j.ey], [j.hx, j.hy], 14);
    ctx.beginPath(); ellipse(ctx, j.hx + bend * 18, j.hy + 6, 30, 11); ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  }
  // pelvis
  ctx.beginPath(); ellipse(ctx, pel[0] - 20, pel[1] + 4, 28, 20, 0.3); ellipse(ctx, pel[0] + 20, pel[1] + 4, 28, 20, -0.3);
  ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, pel[0], pel[1] + 8, 8, 9); ctx.fillStyle = INK; ctx.fill();
  // spine
  for (let i = 1; i <= 3; i++) {
    const p = R(0, -i * 30, lean);
    ctx.beginPath(); roundRect(ctx, pel[0] + p[0] - 13, pel[1] + p[1] - 9, 26, 18, 7); ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  }
  // ribcage
  ctx.save(); ctx.translate(chest[0], chest[1]); ctx.rotate(lean);
  ctx.beginPath(); ellipse(ctx, 0, 16, 52, 62); ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.lineCap = 'round';
  for (let i = 0; i < 3; i++) {
    const y = -8 + i * 22;
    ctx.beginPath(); ctx.moveTo(-8, y); ctx.quadraticCurveTo(-36, y - 6, -40 + i * 4, y + 12); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(8, y); ctx.quadraticCurveTo(36, y - 6, 40 - i * 4, y + 12); ctx.stroke();
  }
  ctx.restore();
  // arms
  const sh = R(52, 6, lean);
  const armSpecs = [[[chest[0] - sh[0], chest[1] - sh[1] + 2 * sh[1] * 0], P.ax, P.ay, -1], [[chest[0] + sh[0], chest[1] + sh[1]], P.bx, P.by, 1]];
  armSpecs[0][0] = [chest[0] - sh[0], chest[1] - sh[1] + 12];
  const handsAt = [];
  for (const [s0, tx, ty, bend] of armSpecs) {
    const j = ik(s0[0], s0[1], tx, ty + shakeY, 92, 88, bend);
    bone(ctx, s0, [j.ex, j.ey], 13); bone(ctx, [j.ex, j.ey], [j.hx, j.hy], 12);
    handsAt.push([j.hx, j.hy, Math.atan2(j.hy - j.ey, j.hx - j.ex)]);
  }
  // fiddle
  if (P.fiddle > 0.5) {
    ctx.save(); ctx.translate(neck[0] - 40, neck[1] + 20); ctx.rotate(-0.5);
    ctx.beginPath(); ellipse(ctx, 0, -18, 22, 26); ellipse(ctx, 0, 22, 28, 30); ctx.fillStyle = '#8a4a22'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, -40); ctx.lineTo(0, -120); ctx.strokeStyle = INK; ctx.lineWidth = 10; ctx.stroke(); ctx.strokeStyle = '#3a2214'; ctx.lineWidth = 6; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-6, -10); ctx.lineTo(-6, 30); ctx.moveTo(6, -10); ctx.lineTo(6, 30); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
    ctx.restore();
    const hb = handsAt[1];
    ctx.beginPath(); ctx.moveTo(hb[0] - 80, hb[1] + 30 + Math.sin(t * 5) * 20); ctx.lineTo(hb[0] + 60, hb[1] - 20 - Math.sin(t * 5) * 20);
    ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.stroke(); ctx.strokeStyle = '#d9c9a0'; ctx.lineWidth = 3; ctx.stroke();
  }
  for (const [hx, hy, a] of handsAt) {
    ctx.save(); ctx.translate(hx, hy); ctx.rotate(a);
    ctx.strokeStyle = INK; ctx.lineWidth = 9; ctx.lineCap = 'round';
    for (let i = -1; i <= 1; i++) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(22, i * 9); ctx.stroke(); }
    ctx.strokeStyle = BONE; ctx.lineWidth = 5;
    for (let i = -1; i <= 1; i++) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(22, i * 9); ctx.stroke(); }
    ctx.beginPath(); ellipse(ctx, 0, 0, 11, 11); ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3.5; ctx.stroke();
    ctx.restore();
  }
  // neck bones
  bone(ctx, [chest[0] + nk[0] * 0.1, chest[1] - 40], neck, 12);
  // skull
  const jawGone = style === 'rattle' ? clamp(V.jawDrop || 0) : 0;
  ctx.save(); ctx.translate(skull[0], skull[1]); ctx.rotate(headA);
  const fx = st.look[0] * 10, fy = st.look[1] * 7 - P.headUp * 6;
  if (jawGone < 0.05) {
    // lower jaw (moves with speech)
    const jo = st.open * 18;
    ctx.beginPath(); roundRect(ctx, -38 + fx * 0.4, 30 + jo, 76, 34, 16); ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
  }
  ctx.beginPath();
  ctx.moveTo(-66, 0); ctx.bezierCurveTo(-70, -90, 70, -90, 66, 0); ctx.bezierCurveTo(64, 30, 46, 46, 30, 50); ctx.lineTo(-30, 50); ctx.bezierCurveTo(-46, 46, -64, 30, -66, 0); ctx.closePath();
  ctx.fillStyle = '#f4eedd'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.save(); ctx.translate(fx, fy);
  const eo = { rx: 20, ry: 23, irisR: 7, pupR: 0.01, iris: '#ffe7a0', pup: 1, look: st.look, lidU: e.lidU, lidL: e.lidL, blink: st.blink, lid: '#f4eedd', lw: 4, sclera: '#231a2a', sparkle: 0, smile: e.smile };
  eye(ctx, { ...eo, x: -26, y: -8 });
  eye(ctx, { ...eo, x: 26, y: -8 });
  for (const sd of [-1, 1]) {
    const o = { x: sd * 26, y: -40, w: 34, side: sd, raise: e.bU + sd * -e.bAsym * 0.5, angle: e.bA, k: 1.3, arch: 5 };
    brow(ctx, { ...o, th: 13, color: INK });
    brow(ctx, { ...o, th: 7, color: '#f4eedd' });
  }
  ctx.beginPath(); ctx.moveTo(0, 12); ctx.lineTo(-8, 24); ctx.quadraticCurveTo(0, 28, 8, 24); ctx.closePath(); ctx.fillStyle = INK; ctx.fill();
  mouth(ctx, { x: 0, y: 40, w: 58, mW: e.mW, smile: e.smile * 0.8, open: jawGone > 0.05 ? 0.7 : st.open, round: 0, lw: 4, inside: '#231a2a', teeth: '#f4eedd', tongueColor: '#231a2a' });
  if (st.open < 0.06 && jawGone < 0.05) {
    ctx.strokeStyle = INK; ctx.lineWidth = 2.5;
    for (let i = -2; i <= 2; i++) { const xx = i * 10; const yy = 40 - e.smile * 0.8 * 58 * 0.2 * (1 - Math.abs(i) / 3) + e.smile * 4; ctx.beginPath(); ctx.moveTo(xx, yy - 6); ctx.lineTo(xx, yy + 6); ctx.stroke(); }
  }
  ctx.restore();
  // accessories
  if (style === 'rattle') {
    ctx.save(); ctx.translate(22, -62); ctx.rotate(0.28);
    ctx.beginPath(); ctx.rect(-30, -70, 60, 70); ctx.fillStyle = '#3a2a52'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
    ctx.beginPath(); ctx.rect(-30, -22, 60, 14); ctx.fillStyle = '#e8872f'; ctx.fill(); ctx.stroke();
    ctx.beginPath(); ellipse(ctx, 0, 0, 52, 10); ctx.fillStyle = '#3a2a52'; ctx.fill(); ctx.stroke();
    ctx.restore();
  } else {
    const cols = ['#ff9fc6', '#ffcf6b', '#c7a0ff', '#ff9fc6', '#ffcf6b'];
    for (let i = 0; i < 5; i++) {
      const a = Math.PI * (1.18 + i * 0.16);
      const cx = Math.cos(a) * 64, cy = Math.sin(a) * 58 - 4;
      ctx.beginPath(); for (let p = 0; p < 5; p++) { const pa = (p / 5) * TAU + i; ellipse(ctx, cx + Math.cos(pa) * 9, cy + Math.sin(pa) * 9, 8, 8); }
      ctx.fillStyle = cols[i]; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 2.5; ctx.stroke();
      ctx.beginPath(); ellipse(ctx, cx, cy, 5, 5); ctx.fillStyle = '#e8872f'; ctx.fill();
    }
  }
  ctx.restore();
  // a falling / caught jaw
  if (jawGone > 0.05) {
    const hx = (handsAt[0][0] + handsAt[1][0]) / 2, hy = (handsAt[0][1] + handsAt[1][1]) / 2;
    const jx = lerp(skull[0], hx, jawGone), jy = lerp(skull[1] + 50, hy - 18, jawGone);
    ctx.save(); ctx.translate(jx, jy); ctx.rotate(Math.sin(t * 20) * 0.15 * jawGone);
    ctx.beginPath(); roundRect(ctx, -38, -14, 76, 32, 15); ctx.fillStyle = BONE; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
    ctx.strokeStyle = INK; ctx.lineWidth = 2.5; for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(i * 11, -14); ctx.lineTo(i * 11, -2); ctx.stroke(); }
    ctx.restore();
  }
  ctx.restore();
}

// ───────────────────────── OWL (narrator) ─────────────────────────
function drawOwl(ctx, st) {
  const { e, t } = st;
  ctx.save(); ctx.translate(st.x, st.y); ctx.scale(st.s, st.s);
  ctx.rotate(Math.sin(t * 0.8) * 0.02 + e.tilt * 0.3);
  ctx.beginPath(); ellipse(ctx, -55, -80, 32, 70, 0.25); ellipse(ctx, 55, -80, 32, 70, -0.25); ctx.fillStyle = '#4a4660'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-70, -60); ctx.bezierCurveTo(-80, -170, -60, -200, -48, -205); ctx.lineTo(-30, -176); ctx.quadraticCurveTo(0, -186, 30, -176); ctx.lineTo(48, -205); ctx.bezierCurveTo(60, -200, 80, -170, 70, -60); ctx.bezierCurveTo(66, 0, -66, 0, -70, -60); ctx.closePath();
  ctx.fillStyle = '#635e78'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, 0, -48, 44, 44); ctx.fillStyle = '#c4bcd2'; ctx.fill();
  ctx.strokeStyle = '#7d7592'; ctx.lineWidth = 3;
  for (let r = 0; r < 3; r++) for (let c = -1; c <= 1; c++) { const x = c * 20 + (r % 2) * 10 - 5, y = -70 + r * 18; ctx.beginPath(); ctx.moveTo(x - 6, y); ctx.lineTo(x, y + 6); ctx.lineTo(x + 6, y); ctx.stroke(); }
  ctx.beginPath(); ellipse(ctx, -28, -128, 34, 34); ellipse(ctx, 28, -128, 34, 34); ctx.fillStyle = '#8a84a0'; ctx.fill();
  const fx = st.look[0] * 6, fy = st.look[1] * 4;
  const eo = { rx: 22, ry: 22, irisR: 19, pupR: 9.5, iris: '#f4b73a', irisRing: '#ffd27a', pup: e.pup, look: st.look, lidU: e.lidU + (e.smile > 0.3 ? 0.25 : 0), lidL: e.lidL + Math.max(0, e.smile) * 0.35, blink: st.blink, lid: '#635e78', lw: 4, sclera: '#f4b73a', sparkle: e.sparkle, smile: e.smile };
  eye(ctx, { ...eo, x: -28 + fx, y: -128 + fy });
  eye(ctx, { ...eo, x: 28 + fx, y: -128 + fy });
  for (const sd of [-1, 1]) brow(ctx, { x: sd * 30 + fx, y: -160, w: 40, th: 8, side: sd, raise: e.bU, angle: e.bA, color: '#3e3a4e', arch: 4 });
  const bo = st.open * 10;
  ctx.beginPath(); ctx.moveTo(-10 + fx, -108); ctx.lineTo(10 + fx, -108); ctx.lineTo(fx, -88 - bo * 0.2); ctx.closePath(); ctx.fillStyle = '#e39a3a'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3.5; ctx.stroke();
  if (bo > 1) { ctx.beginPath(); ctx.moveTo(-7 + fx, -104 + bo); ctx.lineTo(7 + fx, -104 + bo); ctx.lineTo(fx, -92 + bo); ctx.closePath(); ctx.fillStyle = '#c7802a'; ctx.fill(); ctx.stroke(); }
  for (const sd of [-1, 1]) { ctx.beginPath(); ctx.moveTo(sd * 18 - 10, -2); ctx.lineTo(sd * 18 - 4, 10); ctx.moveTo(sd * 18, -2); ctx.lineTo(sd * 18, 12); ctx.moveTo(sd * 18 + 10, -2); ctx.lineTo(sd * 18 + 4, 10); ctx.strokeStyle = '#e0a63a'; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.stroke(); }
  ctx.restore();
}

// ───────────────────────── extras ─────────────────────────
function drawMiniGhost(ctx, x, y, s, t, o = {}) {
  ctx.save(); ctx.translate(x, y + Math.sin(t * 2 + (o.ph || 0)) * 6); ctx.scale(s * (o.flip || 1), s);
  ctx.rotate(Math.sin(t * 1.3 + (o.ph || 0)) * 0.08);
  ctx.beginPath(); ctx.moveTo(-40, 30); ctx.bezierCurveTo(-40, -10, -36, -50, 0, -52); ctx.bezierCurveTo(36, -50, 40, -10, 40, 30);
  for (let i = 0; i < 3; i++) { const x0 = 40 - i * 80 / 3, x1 = 40 - (i + 1) * 80 / 3; ctx.quadraticCurveTo((x0 + x1) / 2, 44 + Math.sin(t * 3 + i + (o.ph || 0)) * 4, x1, 30); }
  ctx.closePath(); ctx.fillStyle = o.alpha != null ? rgba('#f2f5ff', o.alpha) : '#f2f5ff'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
  const blink = ((t + (o.ph || 0)) % 4.3) < 0.12;
  ctx.fillStyle = INK;
  if (blink) { ctx.fillRect(-18, -16, 10, 3); ctx.fillRect(8, -16, 10, 3); }
  else { ctx.beginPath(); ellipse(ctx, -13, -14, 5, 7); ellipse(ctx, 13, -14, 5, 7); ctx.fill(); }
  ctx.beginPath(); ctx.arc(0, -2, 7, 0.15 * Math.PI, 0.85 * Math.PI); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, -24, -2, 6, 3.5); ellipse(ctx, 24, -2, 6, 3.5); ctx.fillStyle = 'rgba(255,130,170,0.35)'; ctx.fill();
  if (o.lantern) {
    const lx = 40, ly = 18;
    const g = ctx.createRadialGradient(lx, ly + 20, 2, lx, ly + 20, 70);
    g.addColorStop(0, rgba('#ffd27a', 0.55 * o.lantern)); g.addColorStop(1, 'rgba(255,180,80,0)');
    ctx.fillStyle = g; ctx.beginPath(); ellipse(ctx, lx, ly + 20, 70, 70); ctx.fill();
    ctx.beginPath(); ctx.moveTo(lx, ly - 4); ctx.lineTo(lx, ly + 8); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
    ctx.beginPath(); roundRect(ctx, lx - 10, ly + 8, 20, 26, 5); ctx.fillStyle = rgba('#ffcf6b', o.lantern); ctx.fill(); ctx.stroke();
  }
  ctx.restore();
}

function drawBat(ctx, x, y, s, t, ph = 0) {
  const f = Math.sin(t * 14 + ph);
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.quadraticCurveTo(-20, -20 * f - 6, -46, -14 * f);
  ctx.quadraticCurveTo(-36, 4, -30, 2); ctx.quadraticCurveTo(-22, 10, -14, 4); ctx.quadraticCurveTo(-8, 10, 0, 6);
  ctx.quadraticCurveTo(8, 10, 14, 4); ctx.quadraticCurveTo(22, 10, 30, 2); ctx.quadraticCurveTo(36, 4, 46, -14 * f);
  ctx.quadraticCurveTo(20, -20 * f - 6, 0, 0);
  ctx.fillStyle = '#1a1424'; ctx.fill();
  ctx.beginPath(); ellipse(ctx, 0, 2, 7, 8); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-5, -4); ctx.lineTo(-6, -11); ctx.lineTo(-1, -6); ctx.moveTo(5, -4); ctx.lineTo(6, -11); ctx.lineTo(1, -6); ctx.fill();
  ctx.restore();
}

function drawCat(ctx, x, y, s, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = '#15111c';
  ctx.beginPath(); ellipse(ctx, 0, -40, 34, 44); ctx.fill();
  ctx.beginPath(); ellipse(ctx, 0, -98, 28, 25); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-24, -110); ctx.lineTo(-20, -138); ctx.lineTo(-6, -118); ctx.moveTo(24, -110); ctx.lineTo(20, -138); ctx.lineTo(6, -118); ctx.fill();
  const tw = Math.sin(t * 1.4) * 0.4;
  ctx.beginPath(); spiralPts(52 + tw * 10, -70, 26, 0.9, -1, Math.PI * 0.5 + tw).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(30, -8)));
  ctx.strokeStyle = '#15111c'; ctx.lineWidth = 9; ctx.lineCap = 'round'; ctx.stroke();
  const bl = ((t + 1.7) % 5.1) < 0.14;
  ctx.fillStyle = '#ffd34a';
  if (!bl) { ctx.beginPath(); ellipse(ctx, -10, -100, 6, 7); ellipse(ctx, 10, -100, 6, 7); ctx.fill(); ctx.fillStyle = '#15111c'; ctx.fillRect(-11, -106, 2.5, 12); ctx.fillRect(9, -106, 2.5, 12); }
  else { ctx.fillRect(-15, -100, 10, 2); ctx.fillRect(5, -100, 10, 2); }
  ctx.restore();
}

module.exports = {
  PIP_BASE, PIP_POSES, PATCH_BASE, PATCH_POSES, BRAM_BASE, BRAM_POSES, SKEL_BASE, SKEL_POSES,
  drawPip, drawPatch, drawBram, drawSkeleton, drawOwl, drawMiniGhost, drawBat, drawCat, pipBodyPath,
};
