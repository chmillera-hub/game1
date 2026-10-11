// Character rig: a front-facing 2D puppet with an expressive face.
// All coordinates are in "world" pixels at wide-shot scale.

const { clamp, lerp, mixColor, rgba } = require('./core');

const CHARACTERS = {
  marcus: {
    skin: '#8d5b3d', shade: '#6d4128', line: '#3b2015', lip: '#73402f', blushC: '#b5463c',
    hair: '#16100c', hairStyle: 'buzz', beard: true,
    headW: 150, headH: 176, jaw: 0.95, chin: 0.5,
    eyeW: 34, eyeH: 20, eyeSep: 62, eyeY: -2, iris: '#3b2414', headScale: 1.12,
    browW: 42, browT: 10.5, browY: -24, mouthW: 56, mouthY: 52, noseY: 24, noseW: 34,
    neckW: 64, neckLen: 24,
    shirt: '#5d6a45', shirtShade: '#48532f', shirtLine: '#2b321d', style: 'hoodie',
    pants: '#2e3341', pantsLine: '#1b1f29',
    shoulderW: 268, torsoH: 256, armW: 46, upperArm: 104, foreArm: 98, handR: 19,
  },
  theo: {
    skin: '#f1c7a5', shade: '#d9a582', line: '#7a4a33', lip: '#c9826f', blushC: '#e8786a',
    hair: '#6e4628', hairStyle: 'curly', glasses: true,
    headW: 138, headH: 168, jaw: 0.84, chin: 0.38,
    eyeW: 32, eyeH: 20, eyeSep: 58, eyeY: 0, iris: '#4d7a5a', headScale: 1.12,
    browW: 36, browT: 8, browY: -26, mouthW: 50, mouthY: 50, noseY: 22, noseW: 28,
    neckW: 52, neckLen: 26,
    shirt: '#d4a046', shirtShade: '#b9862f', shirtLine: '#6e4f1b', style: 'sweater',
    pants: '#3d4d63', pantsLine: '#232d3b',
    shoulderW: 222, torsoH: 246, armW: 39, upperArm: 98, foreArm: 92, handR: 16,
  },
  priya: {
    skin: '#b47c56', shade: '#94603f', line: '#4e2e1c', lip: '#9c4a45', blushC: '#c4544c',
    hair: '#1c1311', hairStyle: 'long', lashes: true, earrings: true,
    headW: 132, headH: 162, jaw: 0.8, chin: 0.33,
    eyeW: 32, eyeH: 20, eyeSep: 56, eyeY: 0, iris: '#3a2516', headScale: 1.12,
    browW: 34, browT: 7, browY: -25, mouthW: 46, mouthY: 48, noseY: 21, noseW: 26,
    neckW: 46, neckLen: 28,
    shirt: '#8e3a4c', shirtShade: '#742b3c', shirtLine: '#46161f', style: 'top',
    pants: '#2a3550', pantsLine: '#151b2b',
    shoulderW: 206, torsoH: 236, armW: 35, upperArm: 94, foreArm: 88, handR: 15,
  },
};

const SEAT_HIP_Y = 1218;
const FLOOR_Y = 1472;

// --- mouth shapes (Rhubarb Lip Sync) -------------------------------------
const VISEMES = {
  X: { open: 0.0, width: 1.0, round: 0.0, tt: 0, tb: 0, tongue: 0, press: 0 },
  A: { open: 0.0, width: 0.94, round: 0.0, tt: 0, tb: 0, tongue: 0, press: 1 },
  B: { open: 0.2, width: 1.04, round: 0.0, tt: 1, tb: 1, tongue: 0, press: 0 },
  C: { open: 0.38, width: 1.04, round: 0.0, tt: 1, tb: 0, tongue: 0.3, press: 0 },
  D: { open: 0.62, width: 1.08, round: 0.0, tt: 1, tb: 0, tongue: 0.6, press: 0 },
  E: { open: 0.42, width: 0.84, round: 0.45, tt: 0, tb: 0, tongue: 0.3, press: 0 },
  F: { open: 0.2, width: 0.62, round: 1.0, tt: 0, tb: 0, tongue: 0, press: 0 },
  G: { open: 0.1, width: 1.0, round: 0.0, tt: 1, tb: 0, tongue: 0, press: 0, fv: 1 },
  H: { open: 0.4, width: 1.0, round: 0.0, tt: 1, tb: 0, tongue: 0.9, press: 0, lift: 1 },
};

// --- small geometry helpers ----------------------------------------------
function bez(p0, p1, p2, p3, u) {
  const v = 1 - u;
  return [
    v * v * v * p0[0] + 3 * v * v * u * p1[0] + 3 * v * u * u * p2[0] + u * u * u * p3[0],
    v * v * v * p0[1] + 3 * v * v * u * p1[1] + 3 * v * u * u * p2[1] + u * u * u * p3[1],
  ];
}

function polyline(ctx, pts, move = true) {
  if (move) ctx.moveTo(pts[0][0], pts[0][1]);
  else ctx.lineTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
}

function smoothLine(ctx, pts) {
  // Catmull-Rom through points
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, pts.length - 1)];
    ctx.bezierCurveTo(
      p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6,
      p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6,
      p2[0], p2[1]);
  }
}

function headPath(ctx, W, H, jaw, chin, cs) {
  const w = W / 2, h = H / 2;
  ctx.beginPath();
  ctx.moveTo(0, -h);
  ctx.bezierCurveTo(w * 0.6, -h, w, -h * 0.62, w, -h * 0.1);
  ctx.bezierCurveTo(w, h * 0.28, w * jaw, h * 0.6, w * chin + cs, h * 0.92);
  ctx.quadraticCurveTo(cs, h * 1.05, -w * chin + cs, h * 0.92);
  ctx.bezierCurveTo(-w * jaw, h * 0.6, -w, h * 0.28, -w, -h * 0.1);
  ctx.bezierCurveTo(-w, -h * 0.62, -w * 0.6, -h, 0, -h);
  ctx.closePath();
}

// --- eyes ----------------------------------------------------------------
function drawEye(ctx, ch, cx, cy, w, h, side, E, L) {
  // side: -1 = eye on screen-left (inner corner on its right)
  const xi = cx - side * w / 2, xo = cx + side * w / 2;
  const open = 1 + Math.max(0, -E.lidU) * 0.7;
  const inner = [xi, cy + h * 0.12], outer = [xo, cy - h * 0.06];
  const tc1 = [lerp(xi, xo, 0.28), cy - h * 0.98 * open], tc2 = [lerp(xi, xo, 0.74), cy - h * 0.9 * open];
  const bc1 = [lerp(xi, xo, 0.3), cy + h * 0.78], bc2 = [lerp(xi, xo, 0.72), cy + h * 0.66];
  const N = 12;
  const top = [], bot = [], lid = [], low = [];
  const lidU = clamp(E.lidU, 0, 1);
  for (let i = 0; i <= N; i++) {
    const u = i / N;
    const T = bez(inner, tc1, tc2, outer, u);
    const B = bez(inner, bc1, bc2, outer, u);
    top.push(T); bot.push(B);
    // lower lid rises with squint; upper lid falls with lidU (+tilt droops the outer side)
    const lowAmt = clamp(E.lidL * 0.62, 0, 0.95);
    const Lo = [B[0], lerp(B[1], T[1], lowAmt * (0.55 + 0.45 * Math.sin(Math.PI * u)))];
    let amt = clamp(lidU + E.lidTilt * (u - 0.35) * 0.9, 0, 1);
    let Up = [T[0], lerp(T[1], B[1], amt)];
    if (Up[1] > Lo[1]) Up = [Up[0], Lo[1]];
    lid.push(Up); low.push(Lo);
  }
  let gap = 0;
  for (let i = 0; i <= N; i++) gap = Math.max(gap, low[i][1] - lid[i][1]);

  // eyelid shading between crease and lash line
  ctx.save();
  ctx.beginPath();
  const crease = top.map(([x, y], i) => [x, y - h * 0.38 - (1 - lidU) * h * 0.08 * Math.sin(Math.PI * i / N)]);
  polyline(ctx, crease);
  polyline(ctx, lid.slice().reverse(), false);
  ctx.closePath();
  ctx.fillStyle = rgba(ch.shade, 0.42);
  ctx.fill();
  ctx.restore();

  if (gap > 0.8) {
    ctx.save();
    ctx.beginPath();
    polyline(ctx, lid);
    polyline(ctx, low.slice().reverse(), false);
    ctx.closePath();
    ctx.fillStyle = '#f8f4ee';
    ctx.fill();
    ctx.clip();
    // iris
    const r = h * 0.56;
    const ix = cx + E.gx * w * 0.3, iy = cy + E.gy * h * 0.3 + h * 0.04;
    ctx.beginPath(); ctx.arc(ix, iy, r, 0, Math.PI * 2);
    ctx.fillStyle = ch.iris; ctx.fill();
    ctx.lineWidth = 1.4; ctx.strokeStyle = rgba('#000000', 0.35); ctx.stroke();
    ctx.beginPath(); ctx.arc(ix, iy, r * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = '#0d0907'; ctx.fill();
    // highlights (+ extra shine when teary)
    const shine = 1 + E.tear * 0.5;
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.beginPath(); ctx.arc(ix + r * 0.32, iy - r * 0.36, r * 0.26 * shine, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.beginPath(); ctx.arc(ix - r * 0.3, iy + r * 0.34, r * 0.12 * shine, 0, Math.PI * 2); ctx.fill();
    // upper-lid shadow on the eyeball
    ctx.beginPath();
    polyline(ctx, lid);
    polyline(ctx, lid.map(([x, y]) => [x, y + h * 0.22]).reverse(), false);
    ctx.closePath();
    ctx.fillStyle = 'rgba(60,30,30,0.12)';
    ctx.fill();
    ctx.restore();
    if (E.tear > 0.01) {
      ctx.beginPath(); polyline(ctx, low.slice(2, N - 1));
      ctx.lineWidth = 2.2; ctx.strokeStyle = `rgba(200,230,255,${0.75 * E.tear})`; ctx.stroke();
    }
  }
  // lower lid line
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); polyline(ctx, low.slice(1, N));
  ctx.lineWidth = 1.6; ctx.strokeStyle = rgba(ch.line, 0.45); ctx.stroke();
  // lash line (thicker toward the outer corner)
  ctx.beginPath(); polyline(ctx, lid);
  ctx.lineWidth = 3.4; ctx.strokeStyle = '#1d1210'; ctx.stroke();
  ctx.beginPath(); polyline(ctx, lid.slice(Math.floor(N * 0.55)));
  ctx.lineWidth = 4.6; ctx.stroke();
  if (ch.lashes) {
    const o = lid[N], o2 = lid[N - 2];
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.moveTo(o[0], o[1]); ctx.lineTo(o[0] + side * 6, o[1] - 5);
    ctx.moveTo(o2[0], o2[1]); ctx.lineTo(o2[0] + side * 5, o2[1] - 6);
    ctx.stroke();
  }
  // crease
  ctx.beginPath(); polyline(ctx, crease.slice(2, N - 1));
  ctx.lineWidth = 1.5; ctx.strokeStyle = rgba(ch.line, 0.35); ctx.stroke();
}

// --- brows ---------------------------------------------------------------
function drawBrow(ctx, ch, cx, cy, side, raise, ang, furrow, color) {
  const len = ch.browW, th = ch.browT;
  const y = cy - raise * 13 + furrow * 3;
  const xin = cx - side * (len * 0.5 - furrow * 4);
  const xout = cx + side * len * 0.5;
  const yin = y - ang * 10 + furrow * 4;
  const yout = y + ang * 3.5 - Math.max(0, -ang) * 2;
  const mx = (xin + xout) / 2, my = (yin + yout) / 2 - 5 + Math.max(0, ang) * 2;
  const N = 10, up = [], dn = [];
  for (let i = 0; i <= N; i++) {
    const u = i / N; // 0 = inner
    const x = (1 - u) * (1 - u) * xin + 2 * u * (1 - u) * mx + u * u * xout;
    const yy = (1 - u) * (1 - u) * yin + 2 * u * (1 - u) * my + u * u * yout;
    const t = th * (1 - 0.55 * u) * (0.75 + 0.25 * Math.sin(Math.PI * Math.min(1, u * 1.6)));
    up.push([x, yy - t / 2]); dn.push([x, yy + t / 2]);
  }
  ctx.beginPath(); polyline(ctx, up); polyline(ctx, dn.reverse(), false); ctx.closePath();
  ctx.fillStyle = color; ctx.lineJoin = 'round';
  ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = color; ctx.stroke();
}

// --- mouth ---------------------------------------------------------------
function drawMouth(ctx, ch, cx, cy, M) {
  const W = ch.mouthW;
  const hw = W / 2 * M.width * (1 - M.round * 0.38) * (1 + Math.max(0, M.smile) * 0.08);
  const sm = M.smile;
  const lY = cy - sm * 9 + M.smirk * 3;
  const rY = cy - sm * 9 - M.smirk * 7;
  const L = [cx - hw, lY], R = [cx + hw, rY];
  let oh = M.open * W * 0.72;
  if (M.round > 0.3) oh = Math.max(oh, M.round * W * 0.2);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';

  if (oh < 2.2) {
    // closed
    const ctrlY = cy + sm * 11 - M.press * 1.5;
    ctx.beginPath(); ctx.moveTo(L[0], L[1]);
    ctx.quadraticCurveTo(cx + M.smirk * 4, ctrlY, R[0], R[1]);
    ctx.lineWidth = 3 + M.press * 1.4; ctx.strokeStyle = ch.line; ctx.stroke();
    // lower lip hint
    ctx.beginPath();
    ctx.moveTo(cx - hw * 0.42, cy + 8 + sm * 4);
    ctx.quadraticCurveTo(cx, cy + 12 + sm * 4 + M.press * 1, cx + hw * 0.42, cy + 8 + sm * 4);
    ctx.lineWidth = 2.2; ctx.strokeStyle = rgba(ch.line, 0.28); ctx.stroke();
  } else {
    const upY = cy - oh * 0.28 - M.round * oh * 0.35 + Math.max(0, sm) * 2;
    const loY = cy + oh * 1.2 + Math.max(0, sm) * 5 - Math.max(0, -sm) * 2;
    const path = () => {
      ctx.beginPath(); ctx.moveTo(L[0], L[1]);
      ctx.quadraticCurveTo(cx, upY, R[0], R[1]);
      ctx.quadraticCurveTo(cx, loY, L[0], L[1]);
      ctx.closePath();
    };
    // lower lip fullness
    ctx.beginPath(); ctx.moveTo(L[0], L[1]);
    ctx.quadraticCurveTo(cx, loY + 9, R[0], R[1]);
    ctx.quadraticCurveTo(cx, loY, L[0], L[1]);
    ctx.fillStyle = rgba(ch.lip, 0.55); ctx.fill();

    path();
    ctx.fillStyle = '#3e1517'; ctx.fill();
    ctx.save(); path(); ctx.clip();
    if (M.tongue > 0.05) {
      const ty = M.lift ? cy + oh * 0.35 : cy + oh * 1.05;
      ctx.beginPath(); ctx.ellipse(cx, ty, hw * 0.6, Math.max(4, oh * 0.5), 0, 0, Math.PI * 2);
      ctx.fillStyle = rgba('#c25a60', clamp(M.tongue * 1.4, 0, 1)); ctx.fill();
    }
    if (M.tt > 0.05) {
      ctx.fillStyle = rgba('#f6f2ea', clamp(M.tt, 0, 1));
      ctx.beginPath(); ctx.ellipse(cx, upY - oh * 0.1, hw * 0.95, oh * 0.42 + 3, 0, 0, Math.PI * 2); ctx.fill();
    }
    if (M.tb > 0.05) {
      ctx.fillStyle = rgba('#ece6dc', clamp(M.tb, 0, 1));
      ctx.beginPath(); ctx.ellipse(cx, loY + oh * 0.05, hw * 0.75, oh * 0.38 + 2, 0, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
    path();
    ctx.lineWidth = 2.8; ctx.strokeStyle = ch.line; ctx.stroke();
    if (M.fv > 0.3) {
      // F/V: upper teeth resting on lower lip
      ctx.fillStyle = '#f6f2ea';
      ctx.fillRect(cx - hw * 0.45, cy - 2, hw * 0.9, 4);
    }
  }
  // smile lines
  if (sm > 0.45) {
    const a = clamp((sm - 0.45) * 1.6, 0, 0.6);
    ctx.lineWidth = 2; ctx.strokeStyle = rgba(ch.line, a);
    ctx.beginPath();
    ctx.moveTo(L[0] - 3, L[1] - 9); ctx.quadraticCurveTo(L[0] - 9, L[1] - 1, L[0] - 5, L[1] + 7);
    ctx.moveTo(R[0] + 3, R[1] - 9); ctx.quadraticCurveTo(R[0] + 9, R[1] - 1, R[0] + 5, R[1] + 7);
    ctx.stroke();
  }
}

// --- hair ------------------------------------------------------------------
function curlRing(cx, cy, rx, ry, a0, a1, n, r) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const a = lerp(a0, a1, i / (n - 1));
    out.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry, r * (0.85 + 0.3 * ((i * 37) % 7) / 7)]);
  }
  return out;
}

function drawCurls(ctx, curls, fill, line) {
  ctx.fillStyle = fill;
  for (const [x, y, r] of curls) { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); }
  ctx.lineWidth = 2; ctx.strokeStyle = line;
  for (const [x, y, r] of curls) {
    ctx.beginPath(); ctx.arc(x, y, r * 0.98, Math.PI * 0.85, Math.PI * 1.85); ctx.stroke();
  }
}

function hairBack(ctx, ch, W, H, fx, fy) {
  const w = W / 2, h = H / 2;
  if (ch.hairStyle === 'curly') {
    const c = curlRing(-fx * 0.25, -h * 0.18, w * 1.0, h * 0.82, Math.PI * 0.92, Math.PI * 2.08, 15, 21);
    drawCurls(ctx, c, ch.hair, mixColor(ch.hair, '#000000', 0.35));
  } else if (ch.hairStyle === 'long') {
    ctx.beginPath();
    const bx = -fx * 0.3;
    ctx.moveTo(bx - w * 1.02, -h * 0.1);
    ctx.bezierCurveTo(bx - w * 1.15, -h * 1.25, bx + w * 1.15, -h * 1.25, bx + w * 1.02, -h * 0.1);
    ctx.bezierCurveTo(bx + w * 1.12, h * 0.8, bx + w * 1.2, h * 1.6, bx + w * 1.0, h * 2.05);
    ctx.quadraticCurveTo(bx, h * 2.25, bx - w * 1.0, h * 2.05);
    ctx.bezierCurveTo(bx - w * 1.2, h * 1.6, bx - w * 1.12, h * 0.8, bx - w * 1.02, -h * 0.1);
    ctx.closePath();
    ctx.fillStyle = ch.hair; ctx.fill();
    ctx.lineWidth = 2.5; ctx.strokeStyle = '#0a0606'; ctx.stroke();
  }
}

function hairFront(ctx, ch, W, H, fx, fy) {
  const w = W / 2, h = H / 2;
  if (ch.hairStyle === 'buzz') {
    ctx.save();
    headPath(ctx, W + 2, H + 2, ch.jaw, ch.chin, 0); ctx.clip();
    ctx.beginPath();
    const hx = fx * 0.55;
    ctx.moveTo(-w - 4, h * 0.05);
    ctx.lineTo(-w * 0.86, -h * 0.2);
    ctx.bezierCurveTo(-w * 0.75, -h * 0.62 + fy * 0.3, hx - w * 0.3, -h * 0.66 + fy * 0.4, hx, -h * 0.64 + fy * 0.4);
    ctx.bezierCurveTo(hx + w * 0.3, -h * 0.66 + fy * 0.4, w * 0.75, -h * 0.62 + fy * 0.3, w * 0.86, -h * 0.2);
    ctx.lineTo(w + 4, h * 0.05);
    ctx.lineTo(w + 4, -h - 10); ctx.lineTo(-w - 4, -h - 10); ctx.closePath();
    ctx.fillStyle = rgba(ch.hair, 0.93); ctx.fill();
    ctx.restore();
  } else if (ch.hairStyle === 'curly') {
    const c = [];
    const n = 7;
    for (let i = 0; i < n; i++) {
      const u = i / (n - 1);
      const x = fx * 0.6 + lerp(-w * 0.82, w * 0.82, u);
      const y = -h * 0.74 - Math.sin(Math.PI * u) * h * 0.16 + fy * 0.4 + (i % 2) * 4;
      c.push([x, y, 19 + (i % 3) * 2]);
    }
    c.push([-w * 0.97 + fx * 0.3, -h * 0.3, 16], [w * 0.97 + fx * 0.3, -h * 0.3, 16]);
    c.push([-w * 0.98 + fx * 0.25, -h * 0.0, 14], [w * 0.98 + fx * 0.25, -h * 0.0, 14]);
    drawCurls(ctx, c, ch.hair, mixColor(ch.hair, '#000000', 0.35));
  } else if (ch.hairStyle === 'long') {
    const px = fx * 0.6 + w * 0.12; // side part
    ctx.fillStyle = ch.hair;
    ctx.beginPath();
    ctx.moveTo(px, -h * 0.98);
    ctx.bezierCurveTo(px - w * 0.9, -h * 0.95, -w * 1.08, -h * 0.5, -w * 0.98, h * 0.35);
    ctx.bezierCurveTo(-w * 1.0, h * 0.8, -w * 1.06, h * 1.2, -w * 1.12, h * 1.55);
    ctx.lineTo(-w * 0.86, h * 1.5);
    ctx.bezierCurveTo(-w * 0.86, h * 0.9, -w * 0.82, h * 0.1, -w * 0.62 + fx * 0.3, -h * 0.42 + fy * 0.3);
    ctx.bezierCurveTo(-w * 0.3 + fx * 0.4, -h * 0.66 + fy * 0.3, px - w * 0.2, -h * 0.72, px, -h * 0.66);
    ctx.bezierCurveTo(px + w * 0.4, -h * 0.72, w * 0.72 + fx * 0.3, -h * 0.5 + fy * 0.3, w * 0.8, -h * 0.05);
    ctx.bezierCurveTo(w * 0.84, h * 0.5, w * 0.86, h * 1.0, w * 0.88, h * 1.5);
    ctx.lineTo(w * 1.12, h * 1.55);
    ctx.bezierCurveTo(w * 1.06, h * 1.1, w * 1.02, h * 0.6, w * 0.99, h * 0.2);
    ctx.bezierCurveTo(w * 1.06, -h * 0.55, px + w * 0.8, -h * 0.98, px, -h * 0.98);
    ctx.closePath();
    ctx.fill();
    ctx.lineWidth = 2.4; ctx.strokeStyle = '#0a0606'; ctx.stroke();
  }
}

// --- body ------------------------------------------------------------------
function ik(s, hnd, l1, l2, hint) {
  let dx = hnd[0] - s[0], dy = hnd[1] - s[1];
  let d = Math.hypot(dx, dy);
  const dmax = l1 + l2 - 0.5, dmin = Math.abs(l1 - l2) + 1;
  let target = hnd;
  if (d > dmax) { target = [s[0] + dx / d * dmax, s[1] + dy / d * dmax]; dx = target[0] - s[0]; dy = target[1] - s[1]; d = dmax; }
  if (d < dmin) d = dmin;
  const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
  const hh = Math.sqrt(Math.max(0, l1 * l1 - a * a));
  const px = s[0] + a * dx / d, py = s[1] + a * dy / d;
  const nx = -dy / d, ny = dx / d;
  const e1 = [px + hh * nx, py + hh * ny], e2 = [px - hh * nx, py - hh * ny];
  const d1 = (e1[0] - s[0]) * hint[0] + (e1[1] - s[1]) * hint[1];
  const d2 = (e2[0] - s[0]) * hint[0] + (e2[1] - s[1]) * hint[1];
  return { elbow: d1 >= d2 ? e1 : e2, hand: target };
}

function drawArm(ctx, ch, s, hand, hint, shape, fs = 0) {
  // fs: foreshortening when the hand comes toward the camera
  const { elbow, hand: hp } = ik(s, hand, ch.upperArm * (1 - fs * 0.3), ch.foreArm * (1 - fs), hint);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(elbow[0], elbow[1]); ctx.lineTo(hp[0], hp[1]);
  ctx.lineWidth = ch.armW + 5; ctx.strokeStyle = ch.shirtLine; ctx.stroke();
  ctx.lineWidth = ch.armW; ctx.strokeStyle = ch.shirt; ctx.stroke();
  // cuff
  const fa = Math.atan2(hp[1] - elbow[1], hp[0] - elbow[0]);
  const cx = hp[0] - Math.cos(fa) * ch.handR * 0.9, cy = hp[1] - Math.sin(fa) * ch.handR * 0.9;
  ctx.beginPath(); ctx.moveTo(cx - Math.sin(fa) * ch.armW * 0.5, cy + Math.cos(fa) * ch.armW * 0.5);
  ctx.lineTo(cx + Math.sin(fa) * ch.armW * 0.5, cy - Math.cos(fa) * ch.armW * 0.5);
  ctx.lineWidth = 2.5; ctx.strokeStyle = ch.shirtLine; ctx.stroke();
  drawHand(ctx, ch, hp, fa, shape);
  return { elbow, hand: hp };
}

function drawHand(ctx, ch, p, ang, shape) {
  const r = ch.handR;
  ctx.save(); ctx.translate(p[0], p[1]); ctx.rotate(ang);
  ctx.fillStyle = ch.skin; ctx.strokeStyle = ch.line; ctx.lineWidth = 2.4;
  ctx.beginPath(); ctx.ellipse(r * 0.25, 0, r * 1.05, r * 0.85, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  if (shape !== 'fist') {
    ctx.beginPath(); ctx.ellipse(r * 0.3, -r * 0.78, r * 0.5, r * 0.3, -0.5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  }
  ctx.lineWidth = 1.4; ctx.strokeStyle = rgba(ch.line, 0.5);
  ctx.beginPath();
  ctx.moveTo(r * 0.75, -r * 0.35); ctx.lineTo(r * 1.15, -r * 0.3);
  ctx.moveTo(r * 0.8, r * 0.1); ctx.lineTo(r * 1.22, r * 0.12);
  ctx.stroke();
  ctx.restore();
}

function drawTorso(ctx, ch, P, t) {
  const sw = ch.shoulderW, th = ch.torsoH, sy = 22 - P.shoulder * 16 + P.slump * 8;
  const waist = sw * 0.41;
  ctx.beginPath();
  ctx.moveTo(-ch.neckW * 0.62, 0);
  ctx.quadraticCurveTo(-sw * 0.44, sy - 14, -sw / 2, sy + 26);
  ctx.bezierCurveTo(-sw * 0.52, th * 0.45, -waist * 1.02, th * 0.75, -waist, th + 4);
  ctx.lineTo(waist, th + 4);
  ctx.bezierCurveTo(waist * 1.02, th * 0.75, sw * 0.52, th * 0.45, sw / 2, sy + 26);
  ctx.quadraticCurveTo(sw * 0.44, sy - 14, ch.neckW * 0.62, 0);
  ctx.closePath();
  ctx.fillStyle = ch.shirt; ctx.fill();
  ctx.save(); ctx.clip();
  {
    const g = ctx.createLinearGradient(-sw / 2, 0, -sw * 0.05, 0);
    g.addColorStop(0, rgba(ch.shirtShade, 0.95)); g.addColorStop(1, rgba(ch.shirtShade, 0));
    ctx.fillStyle = g; ctx.fillRect(-sw, -20, sw * 2, th + 40);
  }
  if (ch.style === 'hoodie') {
    ctx.strokeStyle = rgba(ch.shirtLine, 0.7); ctx.lineWidth = 2.6;
    ctx.beginPath(); // kangaroo pocket
    ctx.moveTo(-sw * 0.27, th * 0.98); ctx.lineTo(-sw * 0.2, th * 0.66); ctx.lineTo(sw * 0.2, th * 0.66); ctx.lineTo(sw * 0.27, th * 0.98);
    ctx.stroke();
    ctx.fillStyle = rgba(ch.shirtShade, 0.6); ctx.fillRect(-sw * 0.45, th - 10, sw * 0.9, 16);
  } else if (ch.style === 'sweater') {
    ctx.fillStyle = rgba(ch.shirtShade, 0.75); ctx.fillRect(-sw * 0.5, th - 16, sw, 22);
    ctx.strokeStyle = rgba(ch.shirtLine, 0.25); ctx.lineWidth = 1.6;
    for (let x = -sw * 0.45; x < sw * 0.45; x += 9) { ctx.beginPath(); ctx.moveTo(x, th - 14); ctx.lineTo(x, th + 4); ctx.stroke(); }
  } else {
    ctx.strokeStyle = rgba(ch.shirtLine, 0.45); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(-sw * 0.15, th * 0.55); ctx.quadraticCurveTo(-sw * 0.05, th * 0.75, -sw * 0.12, th * 0.98); ctx.stroke();
  }
  ctx.restore();
  ctx.lineWidth = 3; ctx.strokeStyle = ch.shirtLine; ctx.stroke();
  return sy;
}

function drawNeck(ctx, ch, P) {
  const nw = ch.neckW, nl = ch.neckLen;
  ctx.fillStyle = ch.skin; ctx.strokeStyle = ch.line; ctx.lineWidth = 2.4;
  ctx.beginPath();
  ctx.moveTo(-nw / 2, -nl - 30); ctx.lineTo(-nw / 2, 4); ctx.quadraticCurveTo(0, 14, nw / 2, 4); ctx.lineTo(nw / 2, -nl - 30);
  ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-nw / 2, -nl - 10); ctx.lineTo(-nw / 2, 3); ctx.moveTo(nw / 2, -nl - 10); ctx.lineTo(nw / 2, 3); ctx.stroke();
  ctx.fillStyle = rgba(ch.shade, 0.75);
  ctx.beginPath(); ctx.ellipse(0, -nl - 12, nw * 0.62, 22, 0, 0, Math.PI * 2); ctx.fill();
}

function drawCollar(ctx, ch, P) {
  const nw = ch.neckW;
  if (ch.style === 'hoodie') {
    ctx.lineCap = 'round';
    ctx.strokeStyle = ch.shirtLine; ctx.lineWidth = 3;
    ctx.fillStyle = ch.shirtShade;
    ctx.beginPath();
    ctx.moveTo(-nw * 1.15, -2); ctx.quadraticCurveTo(0, 26, nw * 1.15, -2);
    ctx.quadraticCurveTo(nw * 0.9, 30, 0, 40); ctx.quadraticCurveTo(-nw * 0.9, 30, -nw * 1.15, -2);
    ctx.fill(); ctx.stroke();
    ctx.strokeStyle = '#e9e4d6'; ctx.lineWidth = 3.2;
    ctx.beginPath(); ctx.moveTo(-10, 30); ctx.quadraticCurveTo(-13, 62, -9, 92); ctx.moveTo(10, 30); ctx.quadraticCurveTo(13, 62, 9, 88); ctx.stroke();
  } else if (ch.style === 'sweater') {
    ctx.fillStyle = '#f2efe8'; ctx.strokeStyle = '#8f8a80'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(-nw * 0.55, -6); ctx.lineTo(-4, 22); ctx.lineTo(-nw * 0.85, 20); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(nw * 0.55, -6); ctx.lineTo(4, 22); ctx.lineTo(nw * 0.85, 20); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.strokeStyle = ch.shirtLine; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(-nw * 0.75, -2); ctx.quadraticCurveTo(0, 30, nw * 0.75, -2); ctx.stroke();
  } else {
    ctx.fillStyle = ch.skin;
    ctx.beginPath(); ctx.moveTo(-nw * 0.62, -1); ctx.lineTo(0, 46); ctx.lineTo(nw * 0.62, -1); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = ch.shirtLine; ctx.lineWidth = 2.6; ctx.beginPath();
    ctx.moveTo(-nw * 0.62, -1); ctx.lineTo(0, 46); ctx.lineTo(nw * 0.62, -1); ctx.stroke();
    ctx.strokeStyle = '#d9b45a'; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(-nw * 0.48, 3); ctx.quadraticCurveTo(0, 34, nw * 0.48, 3); ctx.stroke();
  }
}

function drawLegs(ctx, ch, P, hipY) {
  const hw = ch.shoulderW * 0.3;
  const sit = P.sit;
  const kneeY = lerp(205, 46, sit);
  const footY = FLOOR_Y - hipY;
  const walk = P.walk, ph = P.walkPhase;
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const s of [-1, 1]) {
    const swing = walk * Math.sin(ph + (s > 0 ? Math.PI : 0)) * 26;
    const hip = [s * hw * 0.55, 0];
    const knee = [s * hw * lerp(0.6, 0.75, sit) + swing * 0.5, kneeY];
    const foot = [s * hw * lerp(0.6, 0.8, sit) + swing, footY - walk * Math.max(0, Math.sin(ph + (s > 0 ? Math.PI : 0))) * 18];
    ctx.beginPath(); ctx.moveTo(hip[0], hip[1]); ctx.lineTo(knee[0], knee[1]); ctx.lineTo(foot[0], foot[1]);
    ctx.lineWidth = hw * lerp(0.62, 0.78, sit) + 5; ctx.strokeStyle = ch.pantsLine; ctx.stroke();
    ctx.lineWidth = hw * lerp(0.62, 0.78, sit); ctx.strokeStyle = ch.pants; ctx.stroke();
    if (sit > 0.5) {
      // thigh mass coming toward the camera
      ctx.globalAlpha = clamp((sit - 0.5) * 2, 0, 1);
      ctx.beginPath(); ctx.ellipse(s * hw * 0.52, 18, hw * 0.58, 44, 0, 0, Math.PI * 2);
      ctx.fillStyle = ch.pants; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = ch.pantsLine; ctx.stroke();
      ctx.fillStyle = rgba('#ffffff', 0.06);
      ctx.beginPath(); ctx.ellipse(s * hw * 0.52, 8, hw * 0.4, 24, 0, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 1;
    }
    ctx.fillStyle = '#e8e4dc'; ctx.strokeStyle = '#6b6560'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.ellipse(foot[0], foot[1] + 8, hw * 0.42, hw * 0.2, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  }
}

// --- props -----------------------------------------------------------------
function drawProp(ctx, kind, x, y, t, scale = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(scale, scale);
  ctx.lineJoin = 'round';
  if (kind === 'controller') {
    ctx.fillStyle = '#2b2d33'; ctx.strokeStyle = '#111215'; ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(-46, -10); ctx.quadraticCurveTo(0, -20, 46, -10);
    ctx.quadraticCurveTo(62, 6, 52, 22); ctx.quadraticCurveTo(40, 30, 26, 14);
    ctx.lineTo(-26, 14); ctx.quadraticCurveTo(-40, 30, -52, 22); ctx.quadraticCurveTo(-62, 6, -46, -10);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#5ad1c8'; ctx.beginPath(); ctx.arc(30, -4, 4, 0, 7); ctx.fill();
    ctx.fillStyle = '#e46a6a'; ctx.beginPath(); ctx.arc(38, 2, 4, 0, 7); ctx.fill();
  } else if (kind === 'mug') {
    ctx.fillStyle = '#e9e1d2'; ctx.strokeStyle = '#6d6455'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.arc(26, 2, 12, -1.2, 1.2); ctx.lineWidth = 6; ctx.stroke();
    ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.moveTo(-24, -26); ctx.lineTo(-21, 24); ctx.quadraticCurveTo(0, 30, 21, 24); ctx.lineTo(24, -26); ctx.closePath();
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#5a3a24'; ctx.beginPath(); ctx.ellipse(0, -26, 24, 6, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#7fa7c9'; ctx.fillRect(-20, -6, 40, 10);
  } else if (kind === 'plate') {
    ctx.fillStyle = '#f3f1ec'; ctx.strokeStyle = '#a19c92'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.ellipse(0, 0, 62, 20, 0, 0, 7); ctx.fill(); ctx.stroke();
    // very burnt toast
    ctx.fillStyle = '#2a1a12'; ctx.strokeStyle = '#120a06';
    ctx.beginPath(); ctx.moveTo(-34, -6); ctx.quadraticCurveTo(-36, -44, -14, -46); ctx.quadraticCurveTo(0, -60, 14, -46);
    ctx.quadraticCurveTo(36, -44, 34, -6); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#4a3020'; ctx.beginPath(); ctx.ellipse(-8, -28, 9, 6, 0.3, 0, 7); ctx.fill();
    // smoke wisps
    ctx.strokeStyle = 'rgba(200,200,200,0.55)'; ctx.lineWidth = 4; ctx.lineCap = 'round';
    for (let i = 0; i < 3; i++) {
      const ph = t * 1.3 + i * 2.1, b = (ph % 1);
      ctx.globalAlpha = Math.sin(Math.PI * b) * 0.8;
      ctx.beginPath();
      const x0 = -14 + i * 14, y0 = -56 - b * 50;
      ctx.moveTo(x0, y0); ctx.bezierCurveTo(x0 + 10, y0 - 14, x0 - 10, y0 - 26, x0 + 4, y0 - 40);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }
  ctx.restore();
}

// --- main draw ----------------------------------------------------------------
// P: evaluated parameters for this frame (see direction/render)
function drawCharacter(ctx, name, P, t, light) {
  const ch = CHARACTERS[name];
  const hipY = SEAT_HIP_Y - (1 - P.sit) * 160 + P.bob;
  ctx.save();
  ctx.translate(P.x, hipY);
  drawLegs(ctx, ch, P, hipY);
  ctx.rotate(P.lean);
  const th = ch.torsoH * (1 + P.breath * 0.012) - P.slump * 10;
  ctx.translate(0, -th);

  const W = ch.headW, H = ch.headH;
  // head transform
  const headX = P.lean * -20 + P.headShift;
  const headY = -ch.neckLen + P.slump * 10 - P.shoulder * 4 + P.headPitch * 6;

  // long hair sits behind the shoulders
  if (ch.hairStyle === 'long') {
    const hs = ch.headScale || 1;
    ctx.save(); ctx.translate(headX, headY); ctx.rotate(P.headTilt); ctx.translate(0, -H * 0.47 * hs); ctx.scale(hs, hs);
    hairBack(ctx, ch, W, H, P.headTurn * W * 0.2, 0);
    ctx.restore();
  }

  const shoulderY = drawTorso(ctx, ch, P, t);
  drawNeck(ctx, ch, P);
  drawCollar(ctx, ch, P);

  const sL = [-ch.shoulderW / 2 + ch.armW * 0.45, shoulderY + 20];
  const sR = [ch.shoulderW / 2 - ch.armW * 0.45, shoulderY + 20];
  const hint = (v, d) => (v === undefined ? d : v);
  const armsFront = [];
  const doArm = (side) => {
    const a = side < 0 ? P.armL : P.armR;
    const s = side < 0 ? sL : sR;
    if (a.front) { armsFront.push(side); return; }
    drawArm(ctx, ch, s, [a.x, a.y], [hint(a.hx, side * 0.6), hint(a.hy, 1)], a.shape, a.fs);
  };
  // the prop held in the lap is drawn under the hands
  if (P.prop && P.prop !== 'mugFace') {
    const pp = P.propPos || [0, 170];
    drawProp(ctx, P.prop, pp[0], pp[1], t);
  }
  doArm(-1); doArm(1);

  // ---- head
  ctx.save();
  ctx.translate(headX, headY);
  ctx.rotate(P.headTilt);
  const hs = ch.headScale || 1;
  ctx.translate(0, -H * 0.47 * hs);
  ctx.scale(hs, hs);
  const turn = P.headTurn;
  const fx = turn * W * 0.2;
  const fy = P.headPitch * H * 0.09;
  // ears (behind head)
  ctx.fillStyle = ch.skin; ctx.strokeStyle = ch.line; ctx.lineWidth = 2.4;
  for (const s of [-1, 1]) {
    const ex = s * (W / 2 - 3) - fx * 0.35 - s * Math.max(0, s * turn) * W * 0.05;
    ctx.beginPath(); ctx.ellipse(ex, H * 0.04 + fy * 0.5, 13, 22, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(ex + s * 2, H * 0.05 + fy * 0.5, 6, 12, 0, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(ch.line, 0.5); ctx.stroke(); ctx.strokeStyle = ch.line;
    if (ch.earrings) {
      ctx.fillStyle = '#e2b84f'; ctx.beginPath(); ctx.arc(ex, H * 0.04 + fy * 0.5 + 24, 4.5, 0, 7); ctx.fill();
      ctx.fillStyle = ch.skin;
    }
  }
  if (ch.hairStyle === 'curly') hairBack(ctx, ch, W, H, fx, fy);

  headPath(ctx, W, H, ch.jaw, ch.chin, fx * 0.25);
  ctx.fillStyle = ch.skin; ctx.fill();
  ctx.save(); ctx.clip();
  // soft form shading, opposite the key light
  const ls = light && light.side ? light.side : 1;
  {
    const x0 = -ls * W * 0.5 + fx * 0.3, x1 = -ls * W * 0.02 + fx * 0.3;
    const g = ctx.createLinearGradient(x0, 0, x1, 0);
    g.addColorStop(0, rgba(ch.shade, 0.6)); g.addColorStop(0.55, rgba(ch.shade, 0.22)); g.addColorStop(1, rgba(ch.shade, 0));
    ctx.fillStyle = g; ctx.fillRect(-W, -H, W * 2, H * 2);
    const g2 = ctx.createLinearGradient(0, H * 0.25, 0, H * 0.55);
    g2.addColorStop(0, rgba(ch.shade, 0)); g2.addColorStop(1, rgba(ch.shade, 0.35));
    ctx.fillStyle = g2; ctx.fillRect(-W, H * 0.25, W * 2, H);
  }
  if (ch.beard) {
    ctx.fillStyle = rgba(ch.hair, 0.26);
    ctx.beginPath();
    const by = ch.noseY + 10 + fy;
    ctx.moveTo(-W / 2, by - 30);
    ctx.quadraticCurveTo(-W * 0.38, by + 4, fx - ch.mouthW * 0.75, by + 4);
    ctx.quadraticCurveTo(fx, by - 6, fx + ch.mouthW * 0.75, by + 4);
    ctx.quadraticCurveTo(W * 0.38, by + 4, W / 2, by - 30);
    ctx.lineTo(W / 2, H); ctx.lineTo(-W / 2, H); ctx.closePath(); ctx.fill();
    // mustache
    ctx.fillStyle = rgba(ch.hair, 0.36);
    const mx = fx * 1.05, my = ch.mouthY + fy * 1.05 - 21;
    ctx.beginPath(); ctx.moveTo(mx - ch.mouthW * 0.5, my + 7);
    ctx.quadraticCurveTo(mx - ch.mouthW * 0.28, my - 3, mx, my);
    ctx.quadraticCurveTo(mx + ch.mouthW * 0.28, my - 3, mx + ch.mouthW * 0.5, my + 7);
    ctx.quadraticCurveTo(mx, my + 3, mx - ch.mouthW * 0.5, my + 7); ctx.fill();
  }
  // blush
  if (P.blush > 0.01) {
    ctx.fillStyle = rgba(ch.blushC, 0.33 * P.blush);
    for (const s of [-1, 1]) {
      ctx.beginPath(); ctx.ellipse(fx + s * ch.eyeSep * 0.62, ch.eyeY + 26 + fy, 19, 11, 0, 0, Math.PI * 2); ctx.fill();
    }
  }
  ctx.restore();
  headPath(ctx, W, H, ch.jaw, ch.chin, fx * 0.25);
  ctx.lineWidth = 3; ctx.strokeStyle = ch.line; ctx.stroke();

  // eyes
  const eyeCY = ch.eyeY + fy;
  const sep = ch.eyeSep * (1 - Math.abs(turn) * 0.12);
  for (const s of [-1, 1]) {
    const far = s * turn > 0; // eye on the side we turn toward is the far one
    const wscale = far ? 1 - Math.abs(turn) * 0.28 : 1 + Math.abs(turn) * 0.04;
    const E = {
      lidU: s < 0 ? P.lidUL : P.lidUR, lidL: P.lidL, lidTilt: P.lidTilt,
      gx: P.gx, gy: P.gy, tear: P.tear,
    };
    drawEye(ctx, ch, fx + s * sep / 2, eyeCY, ch.eyeW * wscale, ch.eyeH, s, E);
  }
  // nose
  {
    const nx = fx * 1.25, ny = ch.noseY + fy * 1.1, nw = ch.noseW;
    ctx.fillStyle = rgba(ch.shade, 0.45);
    ctx.beginPath(); ctx.ellipse(nx - ls * 4, ny + 4, nw * 0.42, 7, 0, 0, Math.PI * 2); ctx.fill();
    ctx.lineCap = 'round'; ctx.strokeStyle = ch.line; ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(nx - nw * 0.36, ny - 2);
    ctx.quadraticCurveTo(nx - nw * 0.42, ny + 7, nx - nw * 0.16, ny + 6);
    ctx.quadraticCurveTo(nx, ny + 11, nx + nw * 0.16, ny + 6);
    ctx.quadraticCurveTo(nx + nw * 0.42, ny + 7, nx + nw * 0.36, ny - 2);
    ctx.stroke();
    ctx.lineWidth = 2; ctx.strokeStyle = rgba(ch.line, 0.4);
    ctx.beginPath(); ctx.moveTo(nx + turn * 6 - ls * 5, ny - 30); ctx.quadraticCurveTo(nx + turn * 8 - ls * 9, ny - 12, nx - ls * nw * 0.3, ny - 4); ctx.stroke();
  }
  // mouth
  drawMouth(ctx, ch, fx * 1.05, ch.mouthY + fy * 1.05, P.mouth);

  if (ch.glasses) {
    const gy = eyeCY + 1;
    ctx.lineWidth = 3.2; ctx.strokeStyle = '#2a2220';
    const r = ch.eyeW * 0.78;
    const centers = [-1, 1].map((s) => {
      const far = s * turn > 0;
      const wscale = far ? 1 - Math.abs(turn) * 0.28 : 1 + Math.abs(turn) * 0.04;
      return [fx + s * sep / 2, wscale];
    });
    for (const [x, ws] of centers) {
      ctx.beginPath(); ctx.ellipse(x, gy, r * ws, r * 0.82, 0, 0, Math.PI * 2);
      ctx.fillStyle = light && light.glare ? light.glare : 'rgba(210,225,255,0.10)'; ctx.fill();
      ctx.stroke();
      ctx.save(); ctx.clip();
      ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(x - r * 0.2 * ws, gy - r); ctx.lineTo(x - r * ws, gy + r * 0.1); ctx.stroke();
      ctx.restore();
    }
    ctx.beginPath();
    ctx.moveTo(centers[0][0] + r * centers[0][1], gy - 2); ctx.quadraticCurveTo(fx * 1.2, gy - 8, centers[1][0] - r * centers[1][1], gy - 2);
    ctx.moveTo(centers[0][0] - r * centers[0][1], gy - 3); ctx.lineTo(-W / 2 + 2 - fx * 0.3, gy - 6);
    ctx.moveTo(centers[1][0] + r * centers[1][1], gy - 3); ctx.lineTo(W / 2 - 2 - fx * 0.3, gy - 6);
    ctx.stroke();
  }

  // brows
  const browCol = mixColor(ch.hair, '#000000', 0.1);
  for (const s of [-1, 1]) {
    const far = s * turn > 0;
    const bx = fx + s * sep / 2 * (far ? 1 - Math.abs(turn) * 0.1 : 1);
    drawBrow(ctx, ch, bx, eyeCY + ch.browY, s, s < 0 ? P.browL : P.browR, s < 0 ? P.angL : P.angR, P.furrow, browCol);
  }
  // furrow lines between brows
  if (P.furrow > 0.3 || (P.angL + P.angR) / 2 > 0.45) {
    const a = clamp(Math.max(P.furrow - 0.3, (P.angL + P.angR) / 2 - 0.45) * 1.2, 0, 0.5);
    ctx.strokeStyle = rgba(ch.line, a); ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(fx - 4, eyeCY + ch.browY - 4); ctx.lineTo(fx - 3, eyeCY + ch.browY + 8);
    ctx.moveTo(fx + 4, eyeCY + ch.browY - 4); ctx.lineTo(fx + 3, eyeCY + ch.browY + 8);
    ctx.stroke();
  }

  hairFront(ctx, ch, W, H, fx, fy);
  ctx.restore(); // head

  for (const side of armsFront) {
    const a = side < 0 ? P.armL : P.armR;
    drawArm(ctx, ch, side < 0 ? sL : sR, [a.x, a.y], [hint(a.hx, side), hint(a.hy, 0.6)], a.shape, a.fs);
  }
  if (P.prop === 'mugFace') drawProp(ctx, 'mug', P.propPos[0], P.propPos[1], t);
  ctx.restore();

  // world-space anchor points for camera / gaze
  return { hipY };
}

function headWorld(name, P) {
  const ch = CHARACTERS[name];
  const hipY = SEAT_HIP_Y - (1 - P.sit) * 160;
  return [P.x, hipY - ch.torsoH - ch.neckLen - ch.headH * 0.45 + P.slump * 18];
}

module.exports = { CHARACTERS, VISEMES, drawCharacter, drawProp, headWorld, SEAT_HIP_Y, FLOOR_Y };
