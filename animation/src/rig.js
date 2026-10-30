// Character rig: draws a parametric 2D character from a definition (chars.js)
// and a sampled per-frame state (acting.js). Character-local units: an adult
// head is ~150 tall; root is at the feet (stand), seat (sit) or floor (floor*).
'use strict';
const { clamp, lerp, mix, shade, rgba, tint, smoothClosed, smoothOpen, capsule, rot, ik2, noise1, TAU } = require('./core');

const P2 = (fn) => { const p = new (require('@napi-rs/canvas').Path2D)(); fn(p); return p; };

// ---------------------------------------------------------------- lighting
// Paint a closed path: base fill, soft key/shadow gradient, rim light, thin outline.
function paint(ctx, path, color, L, box, o = {}) {
  const [x0, y0, x1, y1] = box;
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, r = Math.max(x1 - x0, y1 - y0) * 0.6 + 1;
  if (o.under) {
    ctx.strokeStyle = rgba(shade(color, -0.45), o.outlineA ?? 0.55);
    ctx.lineWidth = (o.lw || 2.2) * 2;
    ctx.lineJoin = 'round';
    ctx.stroke(path);
  }
  ctx.fillStyle = L && L.ambientAmt ? tint(color, L.ambient, L.ambientAmt) : color;
  ctx.fill(path);
  if (L) {
    const kd = L.keyDir - (o.rot || 0);
    const dx = Math.cos(kd), dy = Math.sin(kd);
    ctx.save();
    ctx.clip(path);
    const g = ctx.createLinearGradient(cx + dx * r, cy + dy * r, cx - dx * r, cy - dy * r);
    g.addColorStop(0, rgba(L.keyColor, (L.keyAmt || 0) * 0.22 * (o.keyMul ?? 1)));
    g.addColorStop(0.45, rgba(L.keyColor, 0));
    g.addColorStop(0.62, rgba(L.shadowColor, 0));
    g.addColorStop(1, rgba(L.shadowColor, (L.shadowAmt || 0) * (o.shadowMul ?? 1)));
    ctx.fillStyle = g;
    ctx.fillRect(x0 - 5, y0 - 5, x1 - x0 + 10, y1 - y0 + 10);
    if (L.rimAmt > 0.01 && o.rim !== false) {
      const rd = L.rimDir - (o.rot || 0);
      const rx = Math.cos(rd), ry = Math.sin(rd);
      const gr = ctx.createLinearGradient(cx + rx * r, cy + ry * r, cx, cy);
      gr.addColorStop(0, rgba(L.rimColor, L.rimAmt * 0.9 * (o.rimMul ?? 1)));
      gr.addColorStop(0.35, rgba(L.rimColor, 0));
      ctx.strokeStyle = gr;
      ctx.lineWidth = o.rimW || 7;
      ctx.stroke(path);
    }
    ctx.restore();
  }
  if (o.outline !== false && !o.under) {
    ctx.strokeStyle = rgba(shade(color, -0.45), o.outlineA ?? 0.55);
    ctx.lineWidth = o.lw || 2.2;
    ctx.stroke(path);
  }
}
const bboxOf = (pts, pad = 0) => {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const [x, y] of pts) { if (x < x0) x0 = x; if (y < y0) y0 = y; if (x > x1) x1 = x; if (y > y1) y1 = y; }
  return [x0 - pad, y0 - pad, x1 + pad, y1 + pad];
};
// Soft line (fades at both ends) for creases, folds, SCM muscles etc.
function softLine(ctx, pts, color, w, a) {
  ctx.save();
  ctx.lineCap = 'round';
  const n = pts.length;
  const [ax, ay] = pts[0], [bx, by] = pts[n - 1];
  const g = ctx.createLinearGradient(ax, ay, bx, by);
  g.addColorStop(0, rgba(color, 0));
  g.addColorStop(0.3, rgba(color, a));
  g.addColorStop(0.7, rgba(color, a));
  g.addColorStop(1, rgba(color, 0));
  ctx.strokeStyle = g;
  ctx.lineWidth = w;
  ctx.beginPath();
  smoothOpen(ctx, pts);
  ctx.stroke();
  ctx.restore();
}

// ---------------------------------------------------------------- skeleton
function skeleton(C, S) {
  const b = C.body;
  const f = clamp(S.facing || 0, -1, 1);
  const lean = (S.lean || 0) * Math.PI / 180;
  const br = (S.breath || 0);
  let hip;
  if (S.pose === 'sit') hip = [0, 0];
  else if (S.pose === 'floorHug' || S.pose === 'floorSit' || S.pose === 'floorCross') hip = [0, -b.hipH];
  else hip = [0, -b.leg + (S.crouch || 0)];
  // walking bob
  if (S.walk) hip[1] -= Math.abs(Math.sin(S.walkPhase * Math.PI)) * 6 - 3;
  const up = rot(0, -b.torso, lean);
  const chestRise = br * 2.2 + (S.sob || 0) * 4;
  const shC = [hip[0] + up[0], hip[1] + up[1] - chestRise * 0.6];
  const shrug = (S.shrug || 0) * 14;
  const neckLean = lean * 0.5 + (S.neckLean || 0) * Math.PI / 180;
  const nk = rot(0, -C.neck.len, neckLean);
  const neckTop = [shC[0] + nk[0] + f * 3, shC[1] + nk[1]];
  const tilt = (S.head?.tilt || 0) * Math.PI / 180 + lean * 0.3;
  const hc = rot(0, -C.head.h * 0.36, tilt);
  const headC = [neckTop[0] + hc[0], neckTop[1] + hc[1] + (S.head?.pitch || 0) * 4];
  // shoulders (3/4 view: far side narrower)
  const hw = b.shoulderW / 2;
  const wl = hw * (1 - 0.2 * Math.max(0, -f) + 0.03 * Math.max(0, f));
  const wr = hw * (1 - 0.2 * Math.max(0, f) + 0.03 * Math.max(0, -f));
  const sl = rot(-wl + b.armR * 0.85, b.armR * 1.3, lean);
  const sr = rot(wr - b.armR * 0.85, b.armR * 1.3, lean);
  const shL = [shC[0] + sl[0], shC[1] + sl[1] - shrug - (S.shrugL || 0) * 14];
  const shR = [shC[0] + sr[0], shC[1] + sr[1] - shrug - (S.shrugR || 0) * 14];
  return { f, lean, hip, shC, neckTop, headC, tilt, shL, shR, wl, wr, chestRise, neckLean };
}

// ---------------------------------------------------------------- head
// project an angular position on the head (theta, rad) to x given yaw
const PHI = 0.62;
const projX = (theta, yaw, R) => R * Math.sin(theta + yaw * PHI);
const foreshort = (theta, yaw) => Math.max(0.15, Math.cos(theta + yaw * PHI) / Math.max(0.2, Math.cos(theta)));

function headOutline(C, yaw, open, pitch) {
  const H = C.head.h, W = C.head.w, hd = C.head;
  const jaw = open * 0.05 * H;
  const sh = yaw * 0.07 * W;           // lower face follows the face direction
  const chinShift = yaw * 0.12 * W;
  const farR = 1 - 0.05 * Math.max(0, yaw), farL = 1 - 0.05 * Math.max(0, -yaw);
  if (hd.shape === 'brick') {
    const r = 0.16 * W;
    return [[-0.5 * W, -0.36 * H], [-0.47 * W, -0.5 * H], [0, -0.5 * H], [0.47 * W, -0.5 * H], [0.5 * W, -0.36 * H],
      [0.51 * W * farR + sh, 0.05 * H], [0.5 * W * farR + sh, 0.36 * H + jaw * 0.5], [0.4 * W + chinShift, 0.5 * H + jaw],
      [chinShift, 0.52 * H + jaw], [-0.4 * W + chinShift, 0.5 * H + jaw], [-0.5 * W * farL + sh, 0.36 * H + jaw * 0.5], [-0.51 * W * farL + sh, 0.05 * H]];
  }
  if (hd.shape === 'egg') { // tall, narrow crown, long lower face, soft chin
    return [[0, -0.5 * H], [0.3 * W, -0.44 * H], [0.45 * W, -0.25 * H], [0.5 * W * farR, 0.0], [0.49 * W * farR + sh, 0.2 * H],
      [0.4 * W + sh, 0.38 * H + jaw * 0.6], [0.2 * W + chinShift, 0.48 * H + jaw], [chinShift, 0.5 * H + jaw],
      [-0.2 * W + chinShift, 0.48 * H + jaw], [-0.4 * W + sh, 0.38 * H + jaw * 0.6], [-0.49 * W * farL + sh, 0.2 * H],
      [-0.5 * W * farL, 0.0], [-0.45 * W, -0.25 * H], [-0.3 * W, -0.44 * H]];
  }
  if (hd.shape === 'round') {
    return [[0, -0.5 * H], [0.36 * W, -0.42 * H], [0.5 * W, -0.12 * H], [0.5 * W * farR + sh * 0.6, 0.14 * H],
      [0.42 * W + sh, 0.34 * H + jaw * 0.5], [0.22 * W + chinShift, 0.47 * H + jaw], [chinShift, 0.5 * H + jaw],
      [-0.22 * W + chinShift, 0.47 * H + jaw], [-0.42 * W + sh, 0.34 * H + jaw * 0.5], [-0.5 * W * farL + sh * 0.6, 0.14 * H],
      [-0.5 * W, -0.12 * H], [-0.36 * W, -0.42 * H]];
  }
  // human
  const jw = hd.jaw ?? 0.42, cw = hd.chin ?? 0.12, ck = hd.cheek ?? 0.49;
  return [[0, -0.5 * H], [0.36 * W, -0.44 * H], [0.49 * W, -0.22 * H], [ck * W * farR + sh * 0.5, 0.04 * H],
    [(jw + 0.04) * W * farR + sh, 0.24 * H + jaw * 0.4], [jw * 0.62 * W + sh + chinShift * 0.4, 0.42 * H + jaw * 0.85],
    [cw * W + chinShift, 0.495 * H + jaw], [-cw * W + chinShift, 0.495 * H + jaw],
    [-jw * 0.62 * W + sh + chinShift * 0.4, 0.42 * H + jaw * 0.85], [-(jw + 0.04) * W * farL + sh, 0.24 * H + jaw * 0.4],
    [-ck * W * farL + sh * 0.5, 0.04 * H], [-0.49 * W, -0.22 * H], [-0.36 * W, -0.44 * H]];
}

// eye opening: returns arrays of top & bottom points
function eyeShape(ex, ey, ew, eh, side, lidU, lidL, tilt, round) {
  const N = 14, top = [], bot = [];
  const openU = clamp(1 - lidU, 0, 1), openL = clamp(1 - lidL, 0, 1);
  for (let i = 0; i <= N; i++) {
    const u = -1 + (2 * i) / N; // -1 = screen-left end
    const x = ex + u * ew / 2;
    const outer = u * side; // +1 at outer corner
    const innerDrop = -outer * eh * (round ? 0 : 0.07);
    const base = Math.pow(Math.max(0, 1 - u * u), round ? 0.5 : 0.62);
    let yb = ey + eh * (round ? 0.5 : 0.36) * Math.pow(Math.max(0, 1 - u * u), round ? 0.5 : 0.75) * (0.55 + 0.45 * openL) + innerDrop * 0.4;
    let yt = ey - eh * 0.5 * base * (2 * openU - 1) * (round ? 1 : 1) + innerDrop
      + tilt * eh * 0.28 * (outer > 0 ? outer : 0) * openU - (-tilt) * 0;
    if (tilt < 0) yt += -tilt * eh * 0.32 * (outer < 0 ? -outer : 0) * openU;
    if (yt > yb - 0.6) yt = yb - 0.6 + (yt - yb + 0.6) * 0.05;
    top.push([x, yt]); bot.push([x, yb]);
  }
  return { top, bot };
}

function drawEye(ctx, C, ex, ey, ew, eh, side, P, L, skinCol) {
  const E = C.eyes;
  const round = E.style === 'bulge' || E.style === 'round';
  const lidU = clamp(P.lidU + P.blink, 0, 1), lidL = P.lidL;
  // looking down lowers the upper lid; looking up raises it
  const lidU2 = clamp(lidU + Math.min(0.12, Math.max(0, P.gy) * 0.14) + Math.min(0, P.gy) * 0.08, 0, 0.92) + (P.blink >= 0.99 ? 0.08 : 0);
  if (E.style === 'bulge') return drawBulgeEye(ctx, C, ex, ey, ew, eh, side, { ...P, lidU: lidU2 }, L, skinCol);
  const { top, bot } = eyeShape(ex, ey, ew, eh, side, lidU2, lidL, P.tilt * side * 0 + P.tilt, round);
  const path = P2((p) => {
    p.moveTo(top[0][0], top[0][1]);
    for (const q of top) p.lineTo(q[0], q[1]);
    for (let i = bot.length - 1; i >= 0; i--) p.lineTo(bot[i][0], bot[i][1]);
    p.closePath();
  });
  const opening = top.reduce((m, q, i) => Math.max(m, bot[i][1] - q[1]), 0);
  if (opening > 1.2) {
    ctx.save();
    ctx.clip(path);
    ctx.fillStyle = E.sclera || '#f4efe8';
    ctx.fillRect(ex - ew, ey - eh, ew * 2, eh * 2);
    // iris
    const ri = eh * 0.43 * (E.iris || 1);
    const ix = ex + P.gx * ew * 0.36, iy = ey + P.gy * eh * 0.24 + eh * 0.04;
    const gi = ctx.createRadialGradient(ix, iy, ri * 0.15, ix, iy, ri);
    gi.addColorStop(0, shade(E.irisColor, 0.25));
    gi.addColorStop(0.7, E.irisColor);
    gi.addColorStop(1, shade(E.irisColor, -0.45));
    ctx.fillStyle = gi;
    ctx.beginPath(); ctx.ellipse(ix, iy, ri * 0.92, ri, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = '#120c0a';
    ctx.beginPath(); ctx.ellipse(ix, iy, ri * 0.44 * (P.pupil || 1), ri * 0.47 * (P.pupil || 1), 0, 0, TAU); ctx.fill();
    // lid shadow on the eyeball
    const gs = ctx.createLinearGradient(0, ey - eh * 0.6, 0, ey + eh * 0.15);
    gs.addColorStop(0, 'rgba(70,40,30,0.42)');
    gs.addColorStop(1, 'rgba(70,40,30,0)');
    ctx.fillStyle = gs;
    ctx.fillRect(ex - ew, ey - eh, ew * 2, eh * 2);
    // catchlights
    const cl = L ? clamp(0.75 + L.keyAmt * 0.25, 0.6, 1) : 0.9;
    ctx.fillStyle = `rgba(255,255,255,${cl})`;
    ctx.beginPath(); ctx.ellipse(ix - ri * 0.34, iy - ri * 0.36, ri * 0.24, ri * 0.22, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = `rgba(255,255,255,${cl * 0.7})`;
    ctx.beginPath(); ctx.arc(ix + ri * 0.3, iy + ri * 0.28, ri * 0.09, 0, TAU); ctx.fill();
    if (P.glisten > 0.02) {
      // wet eyes: brighter, a pooled tear line along the lower lid
      ctx.fillStyle = `rgba(255,255,255,${0.5 * P.glisten})`;
      ctx.beginPath(); ctx.ellipse(ix + ri * 0.05, iy + ri * 0.55, ri * 0.55, ri * 0.12, 0, 0, TAU); ctx.fill();
      ctx.strokeStyle = `rgba(200,225,255,${0.65 * P.glisten})`;
      ctx.lineWidth = eh * 0.09;
      ctx.beginPath();
      smoothOpen(ctx, bot.slice(2, bot.length - 2).map(([x, y]) => [x, y - eh * 0.05]));
      ctx.stroke();
    }
    ctx.restore();
  }
  // upper lid crease (follows the lid, but less)
  const crease = top.map(([x, y], i) => [x, lerp(y, ey - eh * 0.5, 0.65) - eh * 0.2]);
  softLine(ctx, crease.slice(2, crease.length - 1), shade(skinCol, -0.4), eh * 0.07, 0.35);
  // lash line
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.strokeStyle = E.lash || '#2a1712';
  ctx.lineWidth = eh * (E.lashW || 0.13);
  ctx.beginPath();
  smoothOpen(ctx, top);
  ctx.stroke();
  if (E.flick) { // small outer flick
    const o = side > 0 ? top[top.length - 1] : top[0];
    const pr = side > 0 ? top[top.length - 3] : top[2];
    const dx = o[0] - pr[0], dy = o[1] - pr[1], d = Math.hypot(dx, dy) || 1;
    ctx.lineWidth = eh * 0.08;
    ctx.beginPath(); ctx.moveTo(o[0], o[1]); ctx.lineTo(o[0] + dx / d * eh * 0.22, o[1] + dy / d * eh * 0.22 - eh * 0.1); ctx.stroke();
  }
  // lower lid
  ctx.strokeStyle = rgba(shade(skinCol, -0.5), 0.45);
  ctx.lineWidth = eh * 0.05;
  ctx.beginPath();
  smoothOpen(ctx, bot.slice(1, bot.length - 1));
  ctx.stroke();
  ctx.restore();
}

// Bulging round eyeball with heavy lids (Annoyance / Fear)
function drawBulgeEye(ctx, C, ex, ey, ew, eh, side, P, L, skinCol) {
  const E = C.eyes;
  const r = ew / 2;
  ctx.save();
  // eyeball
  const ball = P2((p) => { p.ellipse(ex, ey, r, eh / 2, 0, 0, TAU); });
  ctx.fillStyle = E.sclera || '#f6f2ea';
  ctx.fill(ball);
  ctx.save();
  ctx.clip(ball);
  const gb = ctx.createRadialGradient(ex - r * 0.3, ey - eh * 0.3, r * 0.1, ex, ey, r * 1.05);
  gb.addColorStop(0, 'rgba(255,255,255,0)'); gb.addColorStop(1, 'rgba(120,100,90,0.35)');
  ctx.fillStyle = gb; ctx.fill(ball);
  const ri = r * 0.36 * (E.iris || 1);
  const ix = ex + P.gx * r * 0.42, iy = ey + P.gy * eh * 0.28;
  ctx.fillStyle = E.irisColor;
  ctx.beginPath(); ctx.arc(ix, iy, ri, 0, TAU); ctx.fill();
  ctx.fillStyle = '#100a08';
  ctx.beginPath(); ctx.arc(ix, iy, ri * 0.55 * (P.pupil || 1), 0, TAU); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.9)';
  ctx.beginPath(); ctx.arc(ix - ri * 0.35, iy - ri * 0.38, ri * 0.25, 0, TAU); ctx.fill();
  if (P.glisten > 0.02) {
    ctx.fillStyle = `rgba(210,230,255,${0.55 * P.glisten})`;
    ctx.beginPath(); ctx.ellipse(ex, ey + eh * 0.36, r * 0.75, eh * 0.08, 0, 0, TAU); ctx.fill();
  }
  // lids: skin caps covering top and bottom
  const lu = clamp(P.lidU * 0.72 + Math.max(0, P.lidU - 0.92) * 3.5, 0, 1), ll = clamp(P.lidL, 0, 1);
  const lidY = ey - eh / 2 + eh * lu * 1.0;
  const tilt = P.tilt || 0;
  const yo = side * tilt * eh * 0.22; // + raises inner (sad droops outer)
  const capU = P2((p) => {
    p.moveTo(ex - r * 1.3, ey - eh);
    p.lineTo(ex + r * 1.3, ey - eh);
    p.lineTo(ex + r * 1.3, lidY + yo * 1);
    p.quadraticCurveTo(ex, lidY + eh * 0.12 * (1 - lu) + eh * 0.05, ex - r * 1.3, lidY - yo * 1);
    p.closePath();
  });
  ctx.fillStyle = shade(skinCol, -0.04);
  ctx.fill(capU);
  const gl = ctx.createLinearGradient(0, ey - eh / 2, 0, lidY + 2);
  gl.addColorStop(0, rgba(skinCol, 0)); gl.addColorStop(1, rgba(shade(skinCol, -0.25), 0.5));
  ctx.fillStyle = gl; ctx.fill(capU);
  const lowY = ey + eh / 2 - eh * ll * 0.8;
  const capL = P2((p) => {
    p.moveTo(ex - r * 1.3, ey + eh);
    p.lineTo(ex + r * 1.3, ey + eh);
    p.lineTo(ex + r * 1.3, lowY);
    p.quadraticCurveTo(ex, lowY - eh * 0.1 * ll, ex - r * 1.3, lowY);
    p.closePath();
  });
  ctx.fillStyle = skinCol;
  if (ll > 0.02) ctx.fill(capL);
  ctx.restore();
  // lid edge lines
  ctx.save();
  ctx.clip(ball);
  ctx.strokeStyle = rgba(shade(skinCol, -0.55), 0.85);
  ctx.lineWidth = eh * 0.06;
  ctx.beginPath();
  ctx.moveTo(ex - r * 1.3, lidY - yo); ctx.quadraticCurveTo(ex, lidY + eh * 0.12 * (1 - lu) + eh * 0.05, ex + r * 1.3, lidY + yo);
  ctx.stroke();
  if (ll > 0.02) { ctx.lineWidth = eh * 0.04; ctx.beginPath(); ctx.moveTo(ex - r * 1.3, lowY); ctx.quadraticCurveTo(ex, lowY - eh * 0.1 * ll, ex + r * 1.3, lowY); ctx.stroke(); }
  ctx.restore();
  ctx.strokeStyle = rgba(shade(skinCol, -0.5), 0.7);
  ctx.lineWidth = eh * 0.035;
  ctx.stroke(ball);
  ctx.restore();
}

function drawBrow(ctx, C, bx, by, bw, side, P, fs) {
  const B = C.brows;
  const H = C.head.h;
  const raise = P.raise * H * 0.06, inner = P.inner * H * 0.05, sq = P.squeeze * bw * 0.16;
  const ix = bx - side * bw * 0.5 * fs - side * sq;
  const ox = bx + side * bw * 0.5 * fs;
  const iy = by - raise - inner + P.squeeze * H * 0.012;
  const oy = by - raise + (B.outerDrop || 0.02) * H - P.outer * H * 0.03;
  const mx = lerp(ix, ox, 0.42), my = lerp(iy, oy, 0.42) - (B.arch || 0.03) * H - Math.max(0, P.raise) * H * 0.01;
  const t1 = (B.thick || 0.045) * H, t2 = t1 * (B.taper || 0.45);
  // tapered brow: rounded inner head, pointed tail
  const pts = 12, up = [], dn = [];
  for (let i = 0; i <= pts; i++) {
    const u = i / pts;
    const x = (1 - u) * (1 - u) * ix + 2 * u * (1 - u) * mx + u * u * ox;
    const y = (1 - u) * (1 - u) * iy + 2 * u * (1 - u) * my + u * u * oy;
    const head = Math.sin(Math.min(1, u / 0.18) * Math.PI / 2);
    const th = lerp(t1, t2 * 0.35, Math.pow(u, 1.3)) * (0.55 + 0.45 * head);
    up.push([x, y - th * 0.55]); dn.push([x, y + th * 0.45]);
  }
  const ring = [...up, ...dn.reverse()];
  ctx.save();
  ctx.fillStyle = B.color;
  ctx.globalAlpha = B.alpha ?? 0.95;
  ctx.beginPath();
  smoothClosed(ctx, ring, 0.8);
  ctx.fill();
  ctx.restore();
}

function drawMouth(ctx, C, mx, my, mw, P, fs, skinCol) {
  const H = C.head.h, M = C.mouth;
  const open = clamp(P.open, 0, 1.2), round = clamp(P.round, 0, 1), wide = P.wide || 0;
  const hw = mw / 2 * (1 + 0.22 * wide - 0.4 * round) * fs * (1 - 0.15 * open * round);
  const sm = P.smile, asym = P.asym || 0;
  const smL = sm - asym * 0.6, smR = sm + asym * 0.6;
  const k = H * 0.055;
  const press = clamp(P.press || 0, 0, 1);
  const lx = mx - hw, rx = mx + hw;
  const ly = my - smL * k + open * H * 0.02, ry = my - smR * k + open * H * 0.02;
  const oh = open * H * 0.19 * (1 + 0.25 * round);
  const topY = my - oh * 0.22 - (P.teeth || 0) * H * 0.008;
  const botY = my + oh * 0.78;
  const lipC = M.lip || shade(skinCol, -0.22);
  const sag = sm * H * 0.018; // centre dips for a smile, rises for a frown
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (oh > 1.5) {
    const curv = 0.5 + round * 0.45;
    const mouth = P2((p) => {
      p.moveTo(lx, ly);
      p.bezierCurveTo(lerp(lx, mx, curv * 0.6), topY + sag * 0.3, lerp(rx, mx, curv * 0.6), topY + sag * 0.3, rx, ry);
      p.bezierCurveTo(lerp(rx, mx, 0.25 - round * 0.1), botY + sag, lerp(lx, mx, 0.25 - round * 0.1), botY + sag, lx, ly);
      p.closePath();
    });
    ctx.fillStyle = M.inside || '#3a1b20';
    ctx.fill(mouth);
    ctx.save();
    ctx.clip(mouth);
    // upper teeth
    const tH = Math.min(oh * 0.32, H * 0.045);
    ctx.fillStyle = M.teeth || '#efe9de';
    ctx.beginPath();
    ctx.ellipse(mx, topY - tH * 0.15 + sag * 0.3, hw * 0.78, tH, 0, 0, Math.PI);
    ctx.fill();
    // lower teeth on wide open
    if (open > 0.55) {
      ctx.fillStyle = shade(M.teeth || '#efe9de', -0.08);
      ctx.beginPath(); ctx.ellipse(mx, botY + sag + H * 0.012, hw * 0.6, Math.min(oh * 0.16, H * 0.02), 0, Math.PI, TAU); ctx.fill();
    }
    // tongue
    ctx.fillStyle = M.tongue || '#b8545c';
    ctx.beginPath(); ctx.ellipse(mx, botY + sag - oh * 0.05, hw * 0.55, oh * 0.32, 0, 0, TAU); ctx.fill();
    ctx.restore();
    // lips
    ctx.strokeStyle = lipC;
    ctx.lineWidth = H * 0.016 * (1 - press * 0.5);
    ctx.stroke(mouth);
    // lower lip fullness
    ctx.strokeStyle = rgba(shade(lipC, 0.12), 0.8);
    ctx.lineWidth = H * (M.lowerLip || 0.022);
    ctx.beginPath();
    ctx.moveTo(lerp(lx, mx, 0.25), lerp(ly, botY, 0.7) + H * 0.012);
    ctx.quadraticCurveTo(mx, botY + sag + H * 0.016, lerp(rx, mx, 0.25), lerp(ry, botY, 0.7) + H * 0.012);
    ctx.stroke();
  } else {
    // closed mouth: lip line + soft lower lip
    const cy = my + sag + press * H * 0.004;
    ctx.strokeStyle = rgba(shade(lipC, -0.35), 0.9);
    ctx.lineWidth = H * (0.011 + press * 0.004);
    ctx.beginPath();
    ctx.moveTo(lx, ly);
    ctx.bezierCurveTo(lerp(lx, mx, 0.55), cy, lerp(rx, mx, 0.55), cy, rx, ry);
    ctx.stroke();
    // upper lip hint
    ctx.strokeStyle = rgba(lipC, 0.55 * (1 - press * 0.6));
    ctx.lineWidth = H * 0.012;
    ctx.beginPath();
    ctx.moveTo(lerp(lx, mx, 0.2), lerp(ly, cy, 0.4) - H * 0.012);
    ctx.quadraticCurveTo(mx - hw * 0.12, cy - H * 0.024, mx, cy - H * 0.016);
    ctx.quadraticCurveTo(mx + hw * 0.12, cy - H * 0.024, lerp(rx, mx, 0.2), lerp(ry, cy, 0.4) - H * 0.012);
    ctx.stroke();
    // lower lip
    ctx.strokeStyle = rgba(shade(lipC, 0.08), 0.6 * (1 - press * 0.7));
    ctx.lineWidth = H * (M.lowerLip || 0.022) * (1 - press * 0.5);
    ctx.beginPath();
    ctx.moveTo(lerp(lx, mx, 0.3), lerp(ly, cy, 0.7) + H * 0.016);
    ctx.quadraticCurveTo(mx, cy + H * 0.03, lerp(rx, mx, 0.3), lerp(ry, cy, 0.7) + H * 0.016);
    ctx.stroke();
  }
  // corner creases on smiles / tension
  const cr = Math.max(0, Math.abs(sm) - 0.25) + press * 0.4;
  if (cr > 0.02) {
    for (const [cx, cy, s] of [[lx, ly, -1], [rx, ry, 1]]) {
      softLine(ctx, [[cx + s * H * 0.004, cy - H * 0.022 * Math.sign(sm || 1)], [cx + s * H * 0.018, cy], [cx + s * H * 0.006, cy + H * 0.024 * Math.sign(sm || 1)]],
        shade(skinCol, -0.4), H * 0.01, clamp(cr, 0, 0.5) * 0.6);
    }
  }
  ctx.restore();
}

function drawNose(ctx, C, nx, ny, yaw, skinCol, L) {
  const H = C.head.h, N = C.nose || {};
  const s = N.size || 1;
  const side = yaw >= 0 ? 1 : -1;
  if (N.type === 'long') {
    // a long, rounded nose that sticks out a little in 3/4
    const len = H * 0.2 * s, w = H * 0.07 * s;
    const tipX = nx + yaw * H * 0.05, tipY = ny;
    const path = P2((p) => {
      p.moveTo(nx - w * 0.35, ny - len);
      p.quadraticCurveTo(nx - w * 0.7 + yaw * 4, ny - len * 0.2, tipX - w, tipY);
      p.quadraticCurveTo(tipX, tipY + w * 0.95, tipX + w, tipY);
      p.quadraticCurveTo(nx + w * 0.7 + yaw * 4, ny - len * 0.2, nx + w * 0.35, ny - len);
      p.closePath();
    });
    paint(ctx, path, shade(skinCol, 0.03), L, [nx - w, ny - len, nx + w, ny + w], { lw: 1.8, outlineA: 0.45 });
    return;
  }
  if (N.type === 'button') {
    ctx.fillStyle = rgba(shade(skinCol, -0.25), 0.55);
    ctx.beginPath(); ctx.ellipse(nx + yaw * 3, ny, H * 0.045 * s, H * 0.028 * s, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba(shade(skinCol, 0.3), 0.5);
    ctx.beginPath(); ctx.ellipse(nx + yaw * 3 - H * 0.012, ny - H * 0.01, H * 0.015, H * 0.01, 0, 0, TAU); ctx.fill();
    return;
  }
  // human: soft shading only (bridge side shadow, tip shadow, nostril wings)
  const dk = shade(skinCol, -0.38);
  const tipX = nx + yaw * H * 0.035;
  softLine(ctx, [[nx - side * H * 0.03, ny - H * 0.2], [nx - side * H * 0.035 + yaw * H * 0.01, ny - H * 0.1], [tipX - side * H * 0.04, ny - H * 0.02]], dk, H * 0.012, 0.22 + Math.abs(yaw) * 0.25);
  const g = ctx.createRadialGradient(tipX, ny + H * 0.012, 1, tipX, ny + H * 0.012, H * 0.055 * s);
  g.addColorStop(0, rgba(dk, 0.32)); g.addColorStop(1, rgba(dk, 0));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.ellipse(tipX, ny + H * 0.014, H * 0.06 * s, H * 0.03 * s, 0, 0, TAU); ctx.fill();
  // nostril wings: soft curved strokes
  for (const sd of [-1, 1]) {
    const fsd = sd === side ? 0.75 : 1.0;
    const wx = tipX + sd * H * 0.042 * s * fsd;
    softLine(ctx, [[wx - sd * H * 0.004, ny - H * 0.022], [wx + sd * H * 0.006, ny - H * 0.002], [wx - sd * H * 0.012, ny + H * 0.012]], dk, H * 0.011, 0.4);
  }
  // tip highlight
  ctx.fillStyle = rgba(shade(skinCol, 0.35), 0.35);
  ctx.beginPath(); ctx.ellipse(tipX - H * 0.008, ny - H * 0.018, H * 0.016 * s, H * 0.011 * s, 0, 0, TAU); ctx.fill();
}

function drawEar(ctx, C, x, y, side, skinCol, L) {
  const H = C.head.h, E = C.ears || {};
  const s = E.size || 1;
  const h = H * 0.2 * s, w = H * 0.075 * s;
  const path = P2((p) => {
    p.moveTo(x, y - h * 0.5);
    p.bezierCurveTo(x + side * w * 1.3, y - h * 0.6, x + side * w * 1.2, y + h * 0.25, x + side * w * 0.2, y + h * 0.5);
    p.lineTo(x - side * w * 0.2, y + h * 0.3);
    p.closePath();
  });
  paint(ctx, path, shade(skinCol, -0.04), L, [x - w, y - h / 2, x + w * 1.3, y + h / 2], { lw: 1.6, outlineA: 0.4 });
  softLine(ctx, [[x + side * w * 0.3, y - h * 0.3], [x + side * w * 0.75, y - h * 0.05], [x + side * w * 0.4, y + h * 0.25]], shade(skinCol, -0.4), H * 0.012, 0.45);
}

// Main head draw. `hc` = head centre in local coords; head is drawn in its own rotated frame.
function drawHead(ctx, C, S, sk, L, t) {
  const H = C.head.h, W = C.head.w;
  const skin = C.skin;
  const yaw = clamp(S.head?.yaw ?? sk.f * 0.7, -1, 1);
  const F = S.face;
  const open = clamp((S.mouth?.open || 0) + (F.mouthOpen || 0), 0, 1.2);
  ctx.save();
  ctx.translate(sk.headC[0], sk.headC[1]);
  ctx.rotate(sk.tilt);
  const pitch = S.head?.pitch || 0; // + = looking down
  const fy = pitch * H * 0.05; // features shift
  const R = W * 0.49;
  // ears (behind outline when turned away)
  const ears = [-1, 1].map((sd) => {
    const th = sd * 1.42;
    return { sd, th: th + yaw * PHI, x: projX(th, yaw, W * 0.5), y: H * 0.05 + fy * 0.4 };
  });
  // head shape
  const outline = headOutline(C, yaw, open, pitch);
  const headPath = P2((p) => smoothClosed(p, outline, 1));
  paint(ctx, headPath, skin, L, bboxOf(outline), { lw: 2.4, rot: sk.tilt, rimW: 9 });
  for (const e of ears) if (Math.abs(e.th) <= 1.62 && !C.noEars) drawEar(ctx, C, e.x, e.y, e.sd, skin, L);
  ctx.save();
  ctx.clip(headPath);
  // under-jaw/cheek soft shading + blush
  if (C.blush) {
    for (const sd of [-1, 1]) {
      const th = sd * 0.62;
      const bx = projX(th, yaw, R), by = H * 0.16 + fy;
      const a = (C.blush + (F.blush || 0)) * (0.5 + 0.5 * foreshort(th, yaw));
      const g = ctx.createRadialGradient(bx, by, 1, bx, by, H * 0.13);
      g.addColorStop(0, rgba(C.blushColor || '#e0786a', a * 0.45)); g.addColorStop(1, rgba(C.blushColor || '#e0786a', 0));
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.ellipse(bx, by, H * 0.14, H * 0.09, 0, 0, TAU); ctx.fill();
    }
  }
  if (C.faceExtra) C.faceExtra(ctx, C, { yaw, pitch, H, W, R, fy, F, t, L, open });
  ctx.restore();
  // ---- features
  const ey = H * (C.eyes.y ?? 0.03) + fy;
  const eTh = C.eyes.spacing ?? 0.5;
  const eyeW = W * (C.eyes.w ?? 0.2), eyeH = H * (C.eyes.h ?? 0.085);
  const browY = ey - H * (C.brows.gap ?? 0.105);
  const gaze = S.gaze || [0, 0];
  for (const sd of [-1, 1]) {
    const th = sd * eTh;
    const ex = projX(th, yaw, R);
    const fs = foreshort(th, yaw);
    if (Math.cos(th + yaw * PHI) < 0.12) continue;
    const isL = sd < 0;
    const P = {
      lidU: (isL ? F.lidUL : F.lidUR) ?? F.lidU ?? 0.15,
      lidL: (isL ? F.lidLL : F.lidLR) ?? F.lidL ?? 0,
      tilt: F.lidTilt || 0,
      blink: S.blink || 0, gx: gaze[0], gy: gaze[1], glisten: F.glisten || 0, pupil: F.pupil || 1,
    };
    drawEye(ctx, C, ex, ey, eyeW * fs, eyeH, sd, P, L, skin);
    const bx = projX(sd * (eTh + 0.05), yaw, R);
    drawBrow(ctx, C, bx, browY + (isL ? (F.browOffL || 0) : (F.browOffR || 0)), W * (C.brows.w ?? 0.24),
      sd, {
        raise: (isL ? F.browL : F.browR) ?? F.brow ?? 0,
        inner: (isL ? F.browInL : F.browInR) ?? F.browIn ?? 0,
        outer: F.browOut || 0,
        squeeze: F.browSq || 0,
      }, fs);
  }
  // under-eye tiredness / sadness
  if ((F.underEye || 0) > 0.02) {
    for (const sd of [-1, 1]) {
      const ex = projX(sd * eTh, yaw, R);
      softLine(ctx, [[ex - eyeW * 0.35, ey + eyeH * 0.75], [ex, ey + eyeH * 0.95], [ex + eyeW * 0.35, ey + eyeH * 0.75]], shade(skin, -0.35), H * 0.012, F.underEye * 0.5);
    }
  }
  // nose
  drawNose(ctx, C, projX(0, yaw, R * 1.12), H * (C.nose?.y ?? 0.2) + fy, yaw, skin, L);
  // mouth
  const my = H * (C.mouth.y ?? 0.32) + fy * 0.9;
  const mx = projX(0, yaw, R * 1.05);
  const mfs = foreshort(0.3, yaw) * 0.5 + 0.5;
  const M = {
    open,
    round: clamp((S.mouth?.round || 0) + (F.mouthRound || 0), 0, 1),
    wide: (S.mouth?.wide || 0) + (F.mouthWide || 0),
    smile: ((F.smile || 0) + (C.mouth.rest || 0)) * (1 - 0.4 * clamp(open, 0, 1)),
    asym: F.asym || 0, press: clamp((F.press || 0) + (S.mouth?.press || 0), 0, 1), teeth: S.mouth?.teeth || 0,
  };
  drawMouth(ctx, C, mx, my, W * (C.mouth.w ?? 0.34), M, mfs, skin);
  // tears
  if (S.tears) for (const tr of S.tears) drawTear(ctx, C, tr, yaw, R, ey, eTh, eyeW, eyeH, t);
  if (C.beard) C.beard(ctx, C, { yaw, H, W, R, open, fy, L });
  if (C.hairFront) C.hairFront(ctx, C, { yaw, pitch, t, H, W, L, S, R, fy });
  if (C.glasses) drawGlasses(ctx, C, yaw, R, ey, eTh, eyeW, eyeH, L);
  if (C.headTop) C.headTop(ctx, C, { yaw, H, W, t, S, L });
  ctx.restore();
}

function drawTear(ctx, C, tr, yaw, R, ey, eTh, eyeW, eyeH, t) {
  // tr: {eye: -1|1, t0, dur} — one drop forms on the lower lid, runs down the cheek and fades as a whole
  const age = t - tr.t0;
  const dur = tr.dur || 3.2;
  if (age < 0 || age > dur) return;
  const H = C.head.h;
  const th = tr.eye * (eTh + 0.06);
  if (Math.cos(th + yaw * PHI) < 0.2) return;
  const x0 = projX(th, yaw, R) + tr.eye * eyeW * 0.12;
  const y0 = ey + eyeH * 0.55;
  const form = clamp(age / 0.7, 0, 1);              // swells on the lid
  const run = clamp((age - 0.7) / (dur - 0.7), 0, 1); // then runs
  const ease = run * run * (3 - 2 * run);
  const y = y0 + ease * H * 0.3;
  const x = x0 + tr.eye * Math.sin(ease * 2.2) * H * 0.02;
  const alpha = (run < 0.65 ? 1 : 1 - (run - 0.65) / 0.35) * 0.85;
  const r = H * (0.012 + 0.008 * form);
  ctx.save();
  // faint wet trail
  if (run > 0) {
    const g = ctx.createLinearGradient(x0, y0, x, y);
    g.addColorStop(0, `rgba(190,215,250,${0.0})`);
    g.addColorStop(1, `rgba(190,215,250,${0.35 * alpha})`);
    ctx.strokeStyle = g; ctx.lineWidth = r * 0.9; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(x0 + tr.eye * H * 0.02, (y0 + y) / 2, x, y); ctx.stroke();
  }
  ctx.fillStyle = `rgba(160,200,245,${0.55 * alpha})`;
  ctx.beginPath();
  ctx.moveTo(x, y - r * 2.2);
  ctx.bezierCurveTo(x + r * 1.1, y - r * 0.6, x + r, y + r, x, y + r);
  ctx.bezierCurveTo(x - r, y + r, x - r * 1.1, y - r * 0.6, x, y - r * 2.2);
  ctx.fill();
  ctx.fillStyle = `rgba(255,255,255,${0.75 * alpha})`;
  ctx.beginPath(); ctx.arc(x - r * 0.3, y - r * 0.1, r * 0.3, 0, TAU); ctx.fill();
  ctx.restore();
}

function drawGlasses(ctx, C, yaw, R, ey, eTh, eyeW, eyeH, L) {
  const G = C.glasses;
  const H = C.head.h;
  ctx.save();
  const lens = [];
  for (const sd of [-1, 1]) {
    const th = sd * eTh;
    const c = Math.cos(th + yaw * PHI);
    if (c < 0.05) continue;
    const ex = projX(th, yaw, R * 1.04);
    const rw = G.r * H * foreshort(th, yaw), rh = G.r * H;
    lens.push([ex, ey + H * 0.005, rw, rh, sd]);
  }
  for (const [x, y, rw, rh] of lens) {
    ctx.fillStyle = 'rgba(220,235,255,0.10)';
    ctx.beginPath(); ctx.ellipse(x, y, rw, rh, 0, 0, TAU); ctx.fill();
    // lens glint
    ctx.strokeStyle = 'rgba(255,255,255,0.28)'; ctx.lineWidth = H * 0.012;
    ctx.beginPath(); ctx.ellipse(x, y, rw * 0.72, rh * 0.72, 0, Math.PI * 1.1, Math.PI * 1.45); ctx.stroke();
  }
  ctx.strokeStyle = G.color; ctx.lineWidth = H * (G.w || 0.028);
  for (const [x, y, rw, rh] of lens) { ctx.beginPath(); ctx.ellipse(x, y, rw, rh, 0, 0, TAU); ctx.stroke(); }
  if (lens.length === 2) {
    const [a, b] = lens;
    ctx.beginPath(); ctx.moveTo(a[0] + a[2], a[1] - a[3] * 0.2); ctx.quadraticCurveTo((a[0] + b[0]) / 2, a[1] - a[3] * 0.55, b[0] - b[2], b[1] - b[3] * 0.2); ctx.stroke();
  }
  // temple arms toward the visible ear
  for (const [x, y, rw, rh, sd] of lens) {
    const ox = x + sd * rw, earX = projX(sd * 1.42, yaw, C.head.w * 0.5);
    if (Math.abs(earX - ox) > rw * 0.3 && Math.sign(earX - ox) === sd) {
      ctx.beginPath(); ctx.moveTo(ox, y - rh * 0.3); ctx.lineTo(earX, y - rh * 0.1); ctx.stroke();
    }
  }
  ctx.restore();
}

// ---------------------------------------------------------------- hands
// Hand presets: curls per finger [index, middle, ring, pinky] 0..1, spread, thumb angle/curl, view.
const HANDS = {
  relax: { curl: [0.3, 0.38, 0.45, 0.5], spread: 0.08, thumbA: 0.35, thumbC: 0.25, narrow: 0.5 },
  open: { curl: [0.04, 0.03, 0.06, 0.1], spread: 0.55, thumbA: 0.85, thumbC: 0.05, narrow: 0 },
  soft: { curl: [0.12, 0.15, 0.2, 0.25], spread: 0.25, thumbA: 0.55, thumbC: 0.1, narrow: 0.1 },
  flat: { curl: [0.06, 0.05, 0.07, 0.1], spread: 0.12, thumbA: 0.45, thumbC: 0.1, narrow: 0.05 },
  fist: { curl: [1, 1, 1, 1], spread: 0, thumbA: 0.15, thumbC: 0.8, narrow: 0.05 },
  grip: { curl: [0.78, 0.82, 0.85, 0.88], spread: 0.02, thumbA: 0.35, thumbC: 0.5, narrow: 0.15 },
  point: { curl: [0, 0.92, 0.95, 0.95], spread: 0.05, thumbA: 0.2, thumbC: 0.7, narrow: 0.1 },
  pinch: { curl: [0.5, 0.6, 0.7, 0.75], spread: 0.05, thumbA: 0.5, thumbC: 0.45, narrow: 0.2 },
  cup: { curl: [0.55, 0.55, 0.6, 0.65], spread: 0.05, thumbA: 0.6, thumbC: 0.2, narrow: 0.0 },
};
function handParams(h) {
  if (!h) return HANDS.relax;
  if (typeof h === 'string') return HANDS[h] || HANDS.relax;
  if (h.base) return { ...HANDS[h.base], ...h };
  return h;
}
// Draw a hand with the wrist at (0,0) and fingers along +x; thumb on +y when ts=+1.
// view: 'back' (back of hand), 'palm'. Fingers are separate, thumb correctly placed;
// silhouette outline only (stroke-all then fill-all), soft interior creases.
function drawHand(ctx, C, hp, ts, view, L, len) {
  const hs = len || C.body.hand;
  const skin = C.skin;
  const narrow = hp.narrow || 0;
  const pw = hs * 0.42 * (1 - narrow * 0.55), pl = hs * 0.47;
  const shapes = [];
  // palm
  const palm = [[-hs * 0.02, -pw * 0.42 * ts], [pl * 0.55, -pw * 0.52 * ts], [pl, -pw * 0.5 * ts], [pl * 1.02, pw * 0.48 * ts], [pl * 0.5, pw * 0.56 * ts], [-hs * 0.02, pw * 0.44 * ts]];
  shapes.push({ kind: 'poly', pts: palm });
  // fingers: index at the thumb side
  const lens = [0.44, 0.48, 0.45, 0.36], wid = [0.1, 0.104, 0.098, 0.086];
  const fpos = [0.36, 0.12, -0.12, -0.36];
  const tips = [];
  for (let i = 0; i < 4; i++) {
    const c = clamp(hp.curl[i], 0, 1);
    const by = fpos[i] * pw * ts * (1 - narrow * 0.4);
    const bx = pl * (i === 0 || i === 3 ? 0.97 : 1.0) - (i === 3 ? hs * 0.02 : 0);
    const ang = (hp.spread || 0) * (1.5 - i) * 0.16 * ts;
    // visible length shortens as the finger curls toward/away from camera
    const vis = lens[i] * hs * (1 - 0.72 * c);
    const ex = bx + Math.cos(ang) * vis, ey = by + Math.sin(ang) * vis;
    const w = wid[i] * hs * (1 - narrow * 0.25);
    shapes.push({ kind: 'cap', x1: bx - w * 0.3, y1: by, r1: w * 0.55, x2: ex, y2: ey, r2: w * 0.46 * (1 + c * 0.2) });
    tips.push({ bx, by, ex, ey, c, w, ang });
  }
  // thumb from near the wrist on the thumb side
  const ta = (hp.thumbA ?? 0.4), tc = hp.thumbC ?? 0.2;
  const tbx = hs * 0.1, tby = pw * 0.38 * ts;
  const a1 = (0.35 + ta * 0.75) * ts;
  const l1 = hs * 0.24, l2 = hs * 0.2 * (1 - tc * 0.35);
  const jx = tbx + Math.cos(a1) * l1, jy = tby + Math.sin(a1) * l1;
  const a2 = a1 - (0.25 + tc * 1.1) * ts;
  const txe = jx + Math.cos(a2) * l2, tye = jy + Math.sin(a2) * l2;
  shapes.push({ kind: 'cap', x1: tbx, y1: tby, r1: hs * 0.075, x2: jx, y2: jy, r2: hs * 0.058 });
  shapes.push({ kind: 'cap', x1: jx, y1: jy, r1: hs * 0.058, x2: txe, y2: tye, r2: hs * 0.05 });
  const buildPath = (s, p) => {
    if (s.kind === 'poly') smoothClosed(p, s.pts, 0.6);
    else capsule(p, s.x1, s.y1, s.r1, s.x2, s.y2, s.r2);
  };
  const paths = shapes.map((s) => P2((p) => buildPath(s, p)));
  ctx.save();
  ctx.lineJoin = 'round';
  // silhouette outline
  ctx.strokeStyle = rgba(shade(skin, -0.45), 0.6);
  ctx.lineWidth = 3;
  for (const p of paths) ctx.stroke(p);
  const base = L && L.ambientAmt ? tint(skin, L.ambient, L.ambientAmt) : skin;
  ctx.fillStyle = base;
  for (const p of paths) ctx.fill(p);
  // soft finger separations (blend into skin at their ends)
  const dk = shade(skin, -0.3);
  for (let i = 0; i < 3; i++) {
    const a = tips[i], b = tips[i + 1];
    const mx0 = (a.bx + b.bx) / 2, my0 = (a.by + b.by) / 2;
    const mx1 = (a.ex + b.ex) / 2, my1 = (a.ey + b.ey) / 2;
    softLine(ctx, [[mx0 - hs * 0.03, my0], [lerp(mx0, mx1, 0.5), lerp(my0, my1, 0.5)], [mx1, my1]], dk, 1.6, 0.4);
  }
  // knuckle / crease detail
  for (const f of tips) {
    if (f.c > 0.35) { // bent finger: a soft crease where it folds
      const kx = lerp(f.bx, f.ex, 0.55), ky = lerp(f.by, f.ey, 0.55);
      softLine(ctx, [[kx, ky - f.w * 0.4], [kx + 1, ky], [kx, ky + f.w * 0.4]], dk, 1.4, 0.35);
    }
  }
  if (view === 'palm') {
    softLine(ctx, [[pl * 0.15, pw * 0.25 * ts], [pl * 0.45, pw * 0.05 * ts], [pl * 0.85, -pw * 0.2 * ts]], dk, 1.6, 0.3);
    const g = ctx.createRadialGradient(hs * 0.15, pw * 0.25 * ts, 1, hs * 0.15, pw * 0.25 * ts, hs * 0.18);
    g.addColorStop(0, rgba(shade(skin, 0.18), 0.4)); g.addColorStop(1, rgba(skin, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(hs * 0.15, pw * 0.25 * ts, hs * 0.18, 0, TAU); ctx.fill();
  } else {
    // back of hand: subtle knuckle highlights
    ctx.fillStyle = rgba(shade(skin, 0.2), 0.25);
    for (const f of tips) { ctx.beginPath(); ctx.ellipse(f.bx, f.by, f.w * 0.4, f.w * 0.3, 0, 0, TAU); ctx.fill(); }
  }
  // light gradient across the hand
  if (L) {
    const ctr = P2((p) => { for (const s of shapes) buildPath(s, p); });
    ctx.save();
    ctx.clip(ctr);
    const g = ctx.createLinearGradient(0, -hs * 0.4, 0, hs * 0.4);
    g.addColorStop(0, rgba(L.shadowColor, (L.shadowAmt || 0) * 0.5));
    g.addColorStop(1, rgba(L.keyColor, (L.keyAmt || 0) * 0.12));
    ctx.fillStyle = g;
    ctx.fillRect(-hs * 0.2, -hs * 0.7, hs * 1.4, hs * 1.4);
    ctx.restore();
  }
  ctx.restore();
  return { tips, thumb: [txe, tye] };
}

// ---------------------------------------------------------------- arms
// Arm state: {tx, ty} hand target relative to the shoulder (character local, unscaled by lean),
// bend (+1/-1 elbow side), hand (preset or params), view, rot (wrist deg), behind, hidden.
function solveArm(C, sk, side, A) {
  const b = C.body;
  const sh = side < 0 ? sk.shL : sk.shR;
  const tx = sh[0] + (A.tx ?? side * 18), ty = sh[1] + (A.ty ?? b.upper + b.fore * 0.95);
  const bend = A.bend ?? (side < 0 ? -1 : 1); // elbows bend outward by default
  const s = ik2(sh[0], sh[1], tx, ty, b.upper * (A.upperK ?? 1), b.fore * (A.foreK ?? 1), bend);
  return { sh, ...s };
}

function sleeveInfo(C) { return C.clothes.sleeve || { len: 1, color: C.clothes.top.color, cuff: true }; }

function drawArm(ctx, C, sk, side, A, L, t, props) {
  if (!A || A.hidden) return;
  const b = C.body;
  const s = solveArm(C, sk, side, A);
  const sl = sleeveInfo(C);
  const skin = C.skin;
  const r0 = b.armR, r1 = b.armR * 0.82, r2 = b.armR * 0.62;
  // skin arm (under sleeve)
  const armPath = P2((p) => { capsule(p, s.sh[0], s.sh[1], r0 * 0.9, s.ex, s.ey, r1 * 0.85); capsule(p, s.ex, s.ey, r1 * 0.8, s.hx, s.hy, r2 * 0.75); });
  if (sl.len < 1) paint(ctx, armPath, skin, L, [s.hx - 60, Math.min(s.sh[1], s.hy) - 30, s.hx + 60, Math.max(s.sh[1], s.hy) + 30], { lw: 2, under: true });
  // sleeve
  const sx = sl.len >= 1 ? s.hx : lerp(s.sh[0], s.ex, Math.min(1, sl.len * 2.2));
  const sy = sl.len >= 1 ? s.hy : lerp(s.sh[1], s.ey, Math.min(1, sl.len * 2.2));
  const puff = sl.puff || 1;
  const cuffEnd = sl.len >= 1 ? [lerp(s.ex, s.hx, 0.93), lerp(s.ey, s.hy, 0.93)] : [sx, sy];
  const sleevePath = P2((p) => {
    capsule(p, s.sh[0], s.sh[1], r0 * 1.04 * puff, s.ex, s.ey, r1 * 1.1 * puff);
    if (sl.len >= 1) capsule(p, s.ex, s.ey, r1 * 1.1 * puff, cuffEnd[0], cuffEnd[1], r2 * (sl.cuffW || 1.25) * puff);
  });
  paint(ctx, sleevePath, sl.color, L, sk.litBox || [Math.min(s.sh[0], s.hx) - 50, Math.min(s.sh[1], s.hy) - 50, Math.max(s.sh[0], s.hx) + 50, Math.max(s.sh[1], s.hy) + 50], { lw: 2.2, under: true, rot: sk.lean });
  // elbow fold
  const fa = Math.atan2(s.hy - s.ey, s.hx - s.ex);
  const ua = Math.atan2(s.ey - s.sh[1], s.ex - s.sh[0]);
  const bendAmt = Math.abs(Math.sin((fa - ua) / 2));
  if (bendAmt > 0.15) {
    const nx = Math.cos((fa + ua) / 2 + Math.PI / 2), ny = Math.sin((fa + ua) / 2 + Math.PI / 2);
    softLine(ctx, [[s.ex - nx * r1 * 0.9, s.ey - ny * r1 * 0.9], [s.ex + 2, s.ey + 2], [s.ex + nx * r1 * 0.7, s.ey + ny * r1 * 0.7]], shade(sl.color, -0.4), 2.2, 0.4 * bendAmt);
  }
  if (sl.folds) {
    for (let k = 0; k < 2; k++) {
      const u = 0.35 + k * 0.3;
      const fx = lerp(s.ex, cuffEnd[0], u), fy = lerp(s.ey, cuffEnd[1], u);
      const nx = Math.cos(fa + Math.PI / 2), ny = Math.sin(fa + Math.PI / 2);
      softLine(ctx, [[fx - nx * r1 * 0.8, fy - ny * r1 * 0.8], [fx + Math.cos(fa) * 6, fy + Math.sin(fa) * 6], [fx + nx * r1 * 0.6, fy + ny * r1 * 0.6]], shade(sl.color, -0.35), 2, 0.3);
    }
  }
  if (A.hideHand) return { ...s };
  // sleeve opening: a dark ring the wrist emerges from
  if (sl.len >= 1) {
    const ow = r2 * (sl.cuffW || 1.25) * puff;
    ctx.save();
    ctx.translate(cuffEnd[0], cuffEnd[1]);
    ctx.rotate(fa);
    ctx.fillStyle = shade(sl.color, -0.38);
    ctx.beginPath(); ctx.ellipse(0, 0, ow * 0.22, ow * 0.78, 0, 0, TAU); ctx.fill();
    if (sl.cuff) {
      ctx.strokeStyle = rgba(shade(sl.color, -0.25), 0.8); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.ellipse(-ow * 0.5, 0, ow * 0.25, ow * 0.95, 0, -Math.PI / 2, Math.PI / 2); ctx.stroke();
    }
    ctx.restore();
  } else if (sl.len > 0) {
    // short sleeve hem
    ctx.save();
    ctx.translate(sx, sy); ctx.rotate(ua);
    ctx.strokeStyle = rgba(shade(sl.color, -0.3), 0.7); ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.ellipse(0, 0, r1 * 0.3, r1 * 1.12 * puff, 0, -Math.PI / 2, Math.PI / 2); ctx.stroke();
    ctx.restore();
  }
  // wrist + hand from inside the cuff
  const hp = handParams(A.hand);
  const wr = (A.rot || 0) * Math.PI / 180;
  const ha = fa + wr * (side < 0 ? 1 : -1) * (A.rotAbs ? 0 : 1) + (A.rotAbs ? wr : 0) * 0;
  let handAng = A.rotAbs !== undefined ? A.rotAbs * Math.PI / 180 : ha;
  if (A.rotAbs !== undefined && A.follow) { // partly follow the forearm so the wrist stays continuous
    let d = fa - handAng; while (d > Math.PI) d -= TAU; while (d < -Math.PI) d += TAU;
    handAng += d * A.follow;
  }
  const view = A.view || hp.view || 'back';
  // thumb toward body midline for palm view, away for back view
  const perp = [Math.cos(handAng + Math.PI / 2), Math.sin(handAng + Math.PI / 2)];
  const toMid = Math.sign(sk.shC[0] - s.hx) || -side;
  let ts = Math.sign(perp[0] * toMid + 1e-6 * perp[1]) || 1;
  if (Math.abs(perp[0]) < 0.25) ts = Math.sign(perp[1]) * (side < 0 ? -1 : 1) * (view === 'palm' ? -1 : 1) || 1;
  if (view === 'back') ts = -ts;
  if (A.thumb) ts = A.thumb;
  const wx = lerp(s.ex, s.hx, sl.len >= 1 ? 0.975 : 1), wy = lerp(s.ey, s.hy, sl.len >= 1 ? 0.975 : 1);
  // wrist emerges from the sleeve opening along the forearm, then the hand turns at the wrist
  const wb = sl.len >= 1 ? [cuffEnd[0] + Math.cos(fa) * r2 * 0.55, cuffEnd[1] + Math.sin(fa) * r2 * 0.55] : [wx - Math.cos(fa) * r2 * 0.9, wy - Math.sin(fa) * r2 * 0.9];
  const wristPath = P2((p) => capsule(p, wb[0], wb[1], r2 * 0.6, wx, wy, r2 * 0.64));
  ctx.fillStyle = L && L.ambientAmt ? tint(skin, L.ambient, L.ambientAmt) : skin;
  ctx.fill(wristPath);
  ctx.save();
  ctx.translate(wx, wy);
  ctx.rotate(handAng);
  const res = drawHand(ctx, C, hp, ts, view, L);
  if (A.holding && props && props[A.holding]) props[A.holding](ctx, C, { side, ts, t, hand: res, A });
  ctx.restore();
  return { ...s, wx, wy, handAng, ts };
}

// ---------------------------------------------------------------- legs
function drawLegsStand(ctx, C, sk, S, L) {
  const b = C.body, cl = C.clothes;
  const hipY = sk.hip[1], hw = b.hipW / 2;
  const f = sk.f;
  const legs = [];
  for (const sd of [-1, 1]) {
    let hx = sd * hw * 0.5 + f * 6;
    let kx = sd * hw * 0.42 + f * 10, ky = hipY + b.leg * 0.5;
    let ax = sd * hw * 0.38 + f * 12, ay = -b.ankle;
    if (S.walk) {
      const ph = S.walkPhase * Math.PI * 2 + (sd < 0 ? 0 : Math.PI);
      const sw = Math.sin(ph) * (S.stride || 30);
      kx += sw * 0.55; ax += sw;
      ay -= Math.max(0, Math.cos(ph)) * 14; ky -= Math.max(0, Math.cos(ph)) * 8;
    }
    if (S.legSpread) { kx += sd * S.legSpread * 0.5; ax += sd * S.legSpread; }
    legs.push({ sd, hx, kx, ky, ax, ay });
  }
  // far leg first
  legs.sort((a, b2) => (a.sd * f) - (b2.sd * f));
  for (const lg of legs) {
    // shoe: rounded toe that points where the body faces
    const sh = cl.shoes || { color: '#3a2f2a' };
    const dir = lg.sd * 0.12 + f * 0.9;
    const fw = b.foot * (0.46 + 0.32 * Math.min(1, Math.abs(dir))), fh = b.foot * 0.3;
    const tx = lg.ax + dir * b.foot * 0.28;
    const shoe = P2((p) => smoothClosed(p, [
      [lg.ax - b.foot * 0.2, -fh * 1.25], [lg.ax + b.foot * 0.2, -fh * 1.25],
      [tx + fw * 0.5, -fh * 0.45], [tx + fw * 0.45, 0], [tx - fw * 0.45, 0], [tx - fw * 0.5, -fh * 0.45]], 0.7));
    paint(ctx, shoe, sh.color, L, [tx - fw, -fh * 1.4, tx + fw, 0], { lw: 2 });
    softLine(ctx, [[tx - fw * 0.42, -fh * 0.12], [tx, -fh * 0.06], [tx + fw * 0.42, -fh * 0.12]], shade(sh.color, 0.35), 2, 0.35);
    // pant leg / bare leg
    const lc = cl.bottom?.color || C.skin;
    const top = b.thigh || hw * 0.55;
    const leg = P2((p) => {
      const pts = [
        [lg.hx - top, hipY - 6], [lg.hx + top, hipY - 6],
        [lg.kx + top * 0.66, lg.ky], [lg.ax + top * 0.5, lg.ay - 4], [lg.ax - top * 0.5, lg.ay - 4], [lg.kx - top * 0.66, lg.ky]];
      smoothClosed(p, pts, 0.5);
    });
    paint(ctx, leg, lc, L, [lg.ax - top - 20, hipY - 10, lg.ax + top + 20, lg.ay], { lw: 2.2 });
    // knee + crease
    softLine(ctx, [[lg.kx - top * 0.4, lg.ky - 6], [lg.kx, lg.ky + 4], [lg.kx + top * 0.4, lg.ky - 6]], shade(lc, -0.4), 2, 0.3);
    softLine(ctx, [[lg.hx + lg.sd * top * 0.2, hipY + 20], [lerp(lg.hx, lg.kx, 0.5), lerp(hipY, lg.ky, 0.5)], [lg.kx + lg.sd * top * 0.1, lg.ky - 20]], shade(lc, -0.35), 2, 0.22);
  }
}

// seated on a chair, facing camera: thighs come forward (foreshortened), shins down
function drawLegsSit(ctx, C, sk, S, L) {
  const b = C.body, cl = C.clothes;
  const lc = cl.bottom?.color || C.skin;
  const hw = b.hipW / 2;
  const seatDrop = b.leg * 0.08;
  for (const sd of [-1, 1]) {
    const kx = sd * hw * 0.55 + sk.f * 20, ky = seatDrop + 10;
    const thigh = P2((p) => smoothClosed(p, [[sd * hw * 0.05, -20], [sd * hw * 1.0, -16], [kx + sd * 34, ky], [kx - sd * 30, ky + 26]], 0.6));
    paint(ctx, thigh, lc, L, [-hw - 40, -30, hw + 40, ky + 30], { lw: 2 });
    const shin = P2((p) => capsule(p, kx, ky + 4, b.thigh * 0.62, kx + sd * 6, ky + b.leg * 0.48, b.thigh * 0.42));
    paint(ctx, shin, lc, L, [kx - 50, ky, kx + 50, ky + b.leg * 0.5], { lw: 2 });
    const fy = ky + b.leg * 0.5;
    const shoe = P2((p) => { p.ellipse(kx + sd * 6, fy, b.foot * 0.36, b.foot * 0.22, 0, 0, TAU); });
    paint(ctx, shoe, cl.shoes?.color || '#3a2f2a', L, [kx - 50, fy - 20, kx + 50, fy + 20], { lw: 2 });
  }
}

// sitting on the floor: 'floorHug' (both knees up, arms around shins) or 'floorSit' (one knee up, one folded)
function drawLegsFloor(ctx, C, sk, S, L, which) {
  const b = C.body, cl = C.clothes;
  const lc = cl.bottom?.color || C.skin;
  const hw = b.hipW / 2;
  const hipY = sk.hip[1];
  const kneeH = b.leg * 0.45;
  const f = sk.f;
  const items = [];
  if (which === 'floorCross') {
    const ky = hipY - 6;
    const kL = [-hw * 1.28 + f * 16, ky], kR = [hw * 1.28 + f * 16, ky];
    const fL = [hw * 0.82 + f * 26, -10], fR = [-hw * 0.82 + f * 26, -12]; // each foot tucks under the opposite knee
    // thighs out to the knees
    for (const k of [kL, kR]) {
      const sd = Math.sign(k[0]) || 1;
      const th = P2((p) => capsule(p, sd * hw * 0.38, hipY - 2, b.thigh * 0.98, k[0], k[1], b.thigh * 0.74));
      paint(ctx, th, lc, L, [-hw * 1.6, hipY - 60, hw * 1.6, 10], { lw: 2 });
    }
    // lap shadow between the thighs
    const g = ctx.createRadialGradient(f * 16, hipY + 10, 4, f * 16, hipY + 10, hw * 0.9);
    g.addColorStop(0, rgba(shade(lc, -0.5), 0.35)); g.addColorStop(1, rgba(lc, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(f * 16, hipY + 10, hw * 0.9, b.thigh * 0.8, 0, 0, TAU); ctx.fill();
    // back shin (left knee -> right foot), then front shin (right knee -> left foot)
    const shoe = cl.shoes?.color || '#3a2f2a';
    const drawShin = (k, ft, dark) => {
      const sh = P2((p) => capsule(p, k[0], k[1] + 6, b.thigh * 0.68, ft[0], ft[1] - 6, b.thigh * 0.5));
      paint(ctx, sh, shade(lc, dark), L, [-hw * 1.6, hipY - 40, hw * 1.6, 10], { lw: 2 });
      const dir = Math.sign(ft[0] - k[0]);
      const fo = P2((p) => smoothClosed(p, [[ft[0] - dir * b.foot * 0.1, ft[1] - b.foot * 0.26], [ft[0] + dir * b.foot * 0.42, ft[1] - b.foot * 0.12], [ft[0] + dir * b.foot * 0.38, ft[1] + 2], [ft[0] - dir * b.foot * 0.12, ft[1] + 2]], 0.7));
      paint(ctx, fo, shoe, L, [ft[0] - 80, ft[1] - 40, ft[0] + 80, ft[1] + 6], { lw: 2 });
    };
    drawShin(kL, fL, -0.1);
    drawShin(kR, fR, 0);
    // knee caps + folds
    for (const k of [kL, kR]) {
      ctx.fillStyle = rgba(shade(lc, 0.3), 0.3);
      ctx.beginPath(); ctx.ellipse(k[0], k[1] - 4, b.thigh * 0.42, b.thigh * 0.32, 0, 0, TAU); ctx.fill();
      softLine(ctx, [[k[0] * 0.55, hipY - b.thigh * 0.5], [k[0] * 0.7, hipY - b.thigh * 0.2], [k[0] * 0.62, hipY + b.thigh * 0.2]], shade(lc, -0.4), 2, 0.35);
    }
    return items;
  }
  if (which === 'floorHug') {
    for (const sd of [-1, 1]) items.push({ sd, up: true, kx: sd * hw * 0.32 + f * 30, ky: hipY - kneeH, fx: sd * hw * 0.45 + f * 40, fy: -6 });
  } else {
    const upSide = S.upLeg || 1;
    items.push({ sd: -upSide, up: false, kx: -upSide * hw * 1.1 + f * 20, ky: -b.thigh * 0.6, fx: upSide * hw * 0.2, fy: -8 });
    items.push({ sd: upSide, up: true, kx: upSide * hw * 0.55 + f * 30, ky: hipY - kneeH * 0.95, fx: upSide * hw * 0.85 + f * 30, fy: -6 });
  }
  for (const it of items) {
    if (!it.up) {
      // folded leg lying on the floor: thigh out, shin tucked back toward the other hip
      const th = P2((p) => smoothClosed(p, [[0, hipY - b.thigh * 0.6], [it.kx, it.ky - b.thigh * 0.8], [it.kx + it.sd * b.thigh * 0.4, it.ky + 4], [it.fx, -2], [0, hipY + 10]], 0.6));
      paint(ctx, th, lc, L, [Math.min(0, it.kx) - 60, it.ky - 80, Math.max(0, it.kx) + 60, 5], { lw: 2 });
      softLine(ctx, [[it.kx * 0.4, it.ky - 10], [it.kx * 0.7, it.ky - 2], [it.kx * 0.95, it.ky + 2]], shade(lc, -0.4), 2, 0.3);
      const sh = P2((p) => { p.ellipse(it.fx + it.sd * 30, -14, b.foot * 0.4, b.foot * 0.2, 0, 0, TAU); });
      paint(ctx, sh, cl.shoes?.color || '#3a2f2a', L, [it.fx - 60, -40, it.fx + 60, 0], { lw: 2 });
      continue;
    }
    // shin (front) from knee down to the foot, thigh from hip to knee
    const thigh = P2((p) => capsule(p, it.sd * hw * 0.4, hipY + 5, b.thigh * 0.95, it.kx, it.ky, b.thigh * 0.72));
    paint(ctx, thigh, lc, L, [it.kx - 80, it.ky - 60, it.kx + 80, hipY + 40], { lw: 2 });
    const shin = P2((p) => capsule(p, it.kx, it.ky, b.thigh * 0.7, it.fx, it.fy - b.foot * 0.3, b.thigh * 0.48));
    paint(ctx, shin, lc, L, [it.kx - 70, it.ky - 60, it.kx + 70, 0], { lw: 2 });
    softLine(ctx, [[it.kx - b.thigh * 0.4, it.ky + 8], [it.kx, it.ky - 4], [it.kx + b.thigh * 0.4, it.ky + 8]], shade(lc, 0.25), 3, 0.35);
    const fw = b.foot * 0.34, fx2 = it.fx, fy2 = it.fy;
    const shoe = P2((p) => smoothClosed(p, [[fx2 - fw * 0.8, fy2 - b.foot * 0.36], [fx2 + fw * 0.8, fy2 - b.foot * 0.36], [fx2 + fw * 1.1, fy2 - b.foot * 0.08], [fx2 + fw * 0.8, fy2 + 2], [fx2 - fw * 0.8, fy2 + 2], [fx2 - fw * 1.1, fy2 - b.foot * 0.08]], 0.7));
    paint(ctx, shoe, cl.shoes?.color || '#3a2f2a', L, [fx2 - 50, fy2 - 40, fx2 + 50, fy2], { lw: 2 });
    softLine(ctx, [[fx2 - fw * 0.8, fy2 - b.foot * 0.1], [fx2, fy2 - b.foot * 0.04], [fx2 + fw * 0.8, fy2 - b.foot * 0.1]], shade(cl.shoes?.color || '#3a2f2a', 0.4), 2, 0.4);
  }
  return items;
}

// ---------------------------------------------------------------- neck + torso
function drawNeck(ctx, C, sk, S, L) {
  const N = C.neck, H = C.head.h;
  const yaw = S.head?.yaw ?? sk.f * 0.7;
  const w = N.w;
  const top = [sk.neckTop[0] + yaw * 4, sk.neckTop[1] - H * 0.06];
  const bot = [sk.shC[0], sk.shC[1] + 6];
  const pts = [[top[0] - w * 0.47, top[1]], [top[0] + w * 0.47, top[1]],
    [lerp(top[0], bot[0], 0.6) + w * 0.5, lerp(top[1], bot[1], 0.6)], [bot[0] + w * 0.62, bot[1]],
    [bot[0] - w * 0.62, bot[1]], [lerp(top[0], bot[0], 0.6) - w * 0.5, lerp(top[1], bot[1], 0.6)]];
  const path = P2((p) => smoothClosed(p, pts, 0.5));
  paint(ctx, path, shade(C.skin, -0.06), L, bboxOf(pts), { lw: 2 });
  ctx.save();
  ctx.clip(path);
  // shadow under the jaw
  const g = ctx.createLinearGradient(0, top[1], 0, top[1] + H * 0.18);
  g.addColorStop(0, rgba(shade(C.skin, -0.5), 0.45)); g.addColorStop(1, rgba(C.skin, 0));
  ctx.fillStyle = g; ctx.fillRect(top[0] - w, top[1], w * 2, H * 0.25);
  // sternocleidomastoids: V from behind each ear to the sternal notch
  const notch = [bot[0] + yaw * 2, bot[1] - 2];
  for (const sd of [-1, 1]) {
    const stretch = 0.16 + 0.12 * clamp(-sd * yaw, 0, 1);
    softLine(ctx, [[top[0] + sd * w * 0.44, top[1] + 4], [lerp(top[0] + sd * w * 0.3, notch[0], 0.5), lerp(top[1], notch[1], 0.5)], [notch[0] + sd * w * 0.06, notch[1]]],
      shade(C.skin, -0.45), 3.2, stretch);
  }
  ctx.restore();
}

function torsoPts(C, sk, hemY, extra = 0) {
  const b = C.body;
  const lean = sk.lean;
  const P = (x, y) => { const [rx, ry] = rot(x, y - sk.hip[1], lean); return [sk.hip[0] + rx, sk.hip[1] + ry]; };
  const sy = -b.torso - sk.chestRise * 0.6 + sk.hip[1];
  const wl = sk.wl, wr = sk.wr;
  const cw = b.chestW / 2, ww = b.waistW / 2, hw = b.hipW / 2;
  const fl = 1 - 0.18 * Math.max(0, -sk.f), fr = 1 - 0.18 * Math.max(0, sk.f);
  const nw = C.neck.w * 0.55;
  const sh = sk.shL[1] - sk.shC[1], shr = sk.shR[1] - sk.shC[1];
  return [
    P(-nw, sy - 4), P(-wl * 0.7, sy + 4 + sh * 0.6), P(-wl, sy + b.armR * 0.9 + sh), P(-cw * fl - extra, sy + b.torso * 0.3),
    P(-ww * fl - extra, sy + b.torso * 0.72), P(-hw * fl - extra, hemY - sk.hip[1] + sk.hip[1]),
    P(hw * fr + extra, hemY), P(ww * fr + extra, sy + b.torso * 0.72), P(cw * fr + extra, sy + b.torso * 0.3),
    P(wr, sy + b.armR * 0.9 + shr), P(wr * 0.7, sy + 4 + shr * 0.6), P(nw, sy - 4),
  ];
}

function drawTorso(ctx, C, sk, S, L, t) {
  const b = C.body, cl = C.clothes;
  const hemY = sk.hip[1] + (cl.top.hem ?? 20);
  const pts = torsoPts(C, sk, hemY, cl.top.extra || 0);
  const path = P2((p) => smoothClosed(p, pts, 0.55));
  paint(ctx, path, cl.top.color, L, sk.litBox || bboxOf(pts), { lw: 2.4, rot: sk.lean, rimW: 10 });
  const ctr = sk.shC[0] + sk.f * b.shoulderW * 0.12;
  const info = { pts, path, ctr, hemY, sy: sk.shC[1] };
  if (cl.top.detail) {
    ctx.save();
    ctx.clip(path);
    cl.top.detail(ctx, C, sk, info, L, t, S);
    ctx.restore();
  }
  if (cl.top.over) cl.top.over(ctx, C, sk, info, L, t, S);
  return info;
}

// Fabric over the top of the arm: flows from the neckline over the deltoid and fades into the sleeve.
function shoulderCap(ctx, C, sk, sd, L) {
  const b = C.body, sl = sleeveInfo(C);
  const j = sd < 0 ? sk.shL : sk.shR;
  const r = b.armR * (sl.puff || 1);
  const nw = C.neck.w * 0.55;
  const base = [sk.shC[0] + sd * nw, sk.shC[1] - 4];
  const pts = [base, [j[0] - sd * r * 0.2, j[1] - r * 1.22], [j[0] + sd * r * 0.72, j[1] - r * 0.95], [j[0] + sd * r * 1.06, j[1] - r * 0.1],
    [j[0] + sd * r * 0.9, j[1] + r * 0.9], [j[0] - sd * r * 1.0, j[1] + r * 1.0], [sk.shC[0] + sd * nw * 1.4, sk.shC[1] + r * 1.4]];
  const path = P2((p) => smoothClosed(p, pts, 0.6));
  paint(ctx, path, sl.color, L, sk.litBox || bboxOf(pts), { outline: false, rim: true, rot: sk.lean });
  // outline only along the top curve
  ctx.save();
  ctx.strokeStyle = rgba(shade(sl.color, -0.45), 0.55); ctx.lineWidth = 2.2; ctx.lineCap = 'round';
  ctx.beginPath(); smoothOpen(ctx, pts.slice(1, 4), 0.6); ctx.stroke();
  ctx.restore();
}

// ---------------------------------------------------------------- glow aura
function drawGlow(ctx, C, sk, S, t) {
  const G = C.glow;
  const amt = (S.glow ?? 1) * (G.amt || 1) * (1 + 0.08 * Math.sin(t * 2.1 + (G.phase || 0)));
  if (amt < 0.01) return;
  const cy = (sk.headC[1] + sk.hip[1]) / 2;
  const h = Math.abs(sk.hip[1] - sk.headC[1]) + C.head.h;
  ctx.save();
  const g = ctx.createRadialGradient(sk.shC[0], cy, 10, sk.shC[0], cy, h * 0.75);
  g.addColorStop(0, rgba(G.color, 0.5 * amt));
  g.addColorStop(0.5, rgba(G.color, 0.24 * amt));
  g.addColorStop(1, rgba(G.color, 0));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.ellipse(sk.shC[0], cy, h * 0.5, h * 0.78, 0, 0, TAU); ctx.fill();
  ctx.restore();
}

// ---------------------------------------------------------------- full character
function drawCharacter(ctx, C, S, L, t) {
  ctx.save();
  ctx.translate(S.x, S.y);
  const sc = (S.s || 1) * (C.scale || 1);
  ctx.scale(sc * (S.flip ? -1 : 1), sc);
  const sk = skeleton(C, S);
  { const tb = bboxOf(torsoPts(C, sk, sk.hip[1] + (C.clothes.top.hem ?? 20))); const pad = C.body.armR * 3; sk.litBox = [tb[0] - pad, tb[1] - pad, tb[2] + pad, tb[3]]; }
  const light = L ? { ...L } : null;
  if (light && C.glow) { // glow adds a coloured rim
    light.rimColor = mix(light.rimColor || '#ffffff', C.glow.color, 0.6);
    light.rimAmt = Math.max(light.rimAmt || 0, 0.45 * (S.glow ?? 1));
  }
  const arms = S.arms || {};
  const aL = arms.L, aR = arms.R;
  const props = C.props || {};
  const order = [[-1, aL], [1, aR]];
  if (S.armOrder === 'RL') order.reverse();
  if (S.layer === 'armsOnly') {
    for (const [sd, A] of order) if (A && !A.behind) drawArm(ctx, C, sk, sd, A, light, t, props);
    for (const [sd, A] of order) if (A && !A.behind && !A.noCap) shoulderCap(ctx, C, sk, sd, light);
    if (S.overArms) S.overArms(ctx, C, sk, S, light, t);
    ctx.restore();
    return sk;
  }
  if (C.glow) drawGlow(ctx, C, sk, S, t);
  if (C.hairBack) {
    ctx.save(); ctx.translate(sk.headC[0], sk.headC[1]); ctx.rotate(sk.tilt);
    C.hairBack(ctx, C, { yaw: clamp(S.head?.yaw ?? sk.f * 0.7, -1, 1), pitch: S.head?.pitch || 0, H: C.head.h, W: C.head.w, t, L: light, S });
    ctx.restore();
  }
  if (aL && aL.behind) drawArm(ctx, C, sk, -1, aL, light, t, props);
  if (aR && aR.behind) drawArm(ctx, C, sk, 1, aR, light, t, props);
  const pose = S.pose || 'stand';
  if (pose === 'stand') drawLegsStand(ctx, C, sk, S, light);
  if (pose === 'sit' && !S.hideLegs) drawLegsSit(ctx, C, sk, S, light);
  if (C.coatBack) C.coatBack(ctx, C, sk, S, light);
  drawNeck(ctx, C, sk, S, light);
  const torso = drawTorso(ctx, C, sk, S, light, t);
  if (pose === 'floorHug' || pose === 'floorSit' || pose === 'floorCross') drawLegsFloor(ctx, C, sk, S, light, pose);
  if (C.collar) C.collar(ctx, C, sk, torso, light, t, S);
  drawHead(ctx, C, S, sk, light, t);
  if (S.layer === 'noFrontArms') { ctx.restore(); return sk; }
  if (S.preArms) S.preArms(ctx, C, sk, S, light, t);
  for (const [sd, A] of order) if (A && !A.behind) drawArm(ctx, C, sk, sd, A, light, t, props);
  for (const [sd, A] of order) if (A && !A.behind && !A.noCap) shoulderCap(ctx, C, sk, sd, light);
  if (C.overArms) C.overArms(ctx, C, sk, S, light, t);
  if (S.overArms) S.overArms(ctx, C, sk, S, light, t);
  ctx.restore();
  return sk;
}

// world position of a character's head centre (for gaze targets and labels)
function headWorld(C, S) {
  const sk = skeleton(C, S);
  const sc = (S.s || 1) * (C.scale || 1);
  return [S.x + sk.headC[0] * sc, S.y + sk.headC[1] * sc, C.head.h * sc];
}
// world position of a point given in character local coords
function localToWorld(C, S, x, y) {
  const sc = (S.s || 1) * (C.scale || 1);
  return [S.x + x * sc, S.y + y * sc];
}

module.exports = { drawCharacter, drawHand, drawHead, skeleton, headWorld, localToWorld, paint, softLine, HANDS, handParams, P2, bboxOf, solveArm };
