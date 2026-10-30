// Group a vignettes: suffering distilled into light, gifts, guardians, wounds and their healing.
'use strict';
const U = require('../lib/util');
const FX = require('../lib/fx');
const R = require('../lib/rig');

const TAU = Math.PI * 2;
const { clamp, lerp, smooth, easeInOut, rgba, mix, shade } = U;

const GOLD = [255, 211, 138], AMBER = [255, 184, 92], CYAN = [127, 232, 255];
const CRIMSON = [214, 48, 74], BLOOD = [107, 20, 38], PLUM = [92, 52, 110];
const SKIN = [205, 150, 116], SKIN_SH = [128, 78, 62];

// ---------------------------------------------------------------- shared helpers
function frame(w, h) {
  const unit = Math.min(w, h);
  return { unit, cx: w / 2, cy: h / 2, port: h > w * 1.3 };
}
function night(ctx, w, h, p, top = [6, 9, 21], bot = [20, 24, 50], starDiv = 9000) {
  FX.bg(ctx, w, h, top, bot);
  if (starDiv) FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / starDiv));
}
function groundPlane(ctx, w, h, gy, col = [16, 16, 30], rim = [90, 80, 130]) {
  const g = ctx.createLinearGradient(0, gy, 0, h);
  g.addColorStop(0, rgba(col)); g.addColorStop(1, rgba(shade(col, -0.6)));
  ctx.fillStyle = g; ctx.fillRect(0, gy, w, h - gy);
  const l = ctx.createLinearGradient(0, 0, w, 0);
  l.addColorStop(0, rgba(rim, 0)); l.addColorStop(0.5, rgba(rim, 0.35)); l.addColorStop(1, rgba(rim, 0));
  ctx.fillStyle = l; ctx.fillRect(0, gy - 1, w, 2);
}
// figure pose interpolation (pose objects from FX.FIG_POSES)
function lerpPose(a, b, k) {
  const A = typeof a === 'string' ? FX.FIG_POSES[a] : a, B = typeof b === 'string' ? FX.FIG_POSES[b] : b;
  const L2 = (x, y) => [lerp((x || [0, 0])[0], (y || [0, 0])[0], k), lerp((x || [0, 0])[1], (y || [0, 0])[1], k)];
  return {
    lean: lerp(A.lean || 0, B.lean || 0, k), head: lerp(A.head || 0, B.head || 0, k),
    armL: L2(A.armL, B.armL), armR: L2(A.armR, B.armR), legL: L2(A.legL, B.legL), legR: L2(A.legR, B.legR),
    kneel: k < 0.5 ? A.kneel : B.kneel, sit: k < 0.5 ? A.sit : B.sit,
  };
}
// Run FX.figure invisibly to learn where its hands/head land.
function probeFigure(ctx, x, y, h, pose, opts) {
  ctx.save(); ctx.globalAlpha = 0;
  const r = FX.figure(ctx, x, y, h, pose, Object.assign({}, opts, { glow: null }));
  ctx.restore();
  return r;
}
// Palm-up hand seen from the side (thumb side toward the viewer). Wrist at (x,y),
// fingers point toward `facing` (+1 right, -1 left). s = wrist-to-fingertip length.
// Soft shading, no outlines: palm wedge, four separate tapered fingers that curl up, a thumb rooted at the
// base of the palm on the near side. o: {light, alpha, tilt, curl 0..1, thumb 0..1 (grip), arm (forearm length
// in s), sleeve, deferFront}. With deferFront the near fingers + thumb are not drawn; call ret.front() after
// drawing the held object so they wrap in front of it. Returns [x,y] of the resting point on the palm.
function sideHand(ctx, x, y, s, facing, o = {}) {
  const light = !!o.light;
  const curl = o.curl ?? 0.4, grip = o.thumb ?? curl;
  const tilt = o.tilt || 0;
  const a = o.alpha ?? 1;
  const skin = light ? [168, 234, 252] : (o.skin || SKIN);
  const sh = light ? [70, 160, 205] : (o.shadow || SKIN_SH);
  const L = o.arm ?? 2.2;
  const xf = () => { ctx.translate(x, y); ctx.rotate(tilt * facing); ctx.scale(facing * s, s); ctx.globalAlpha *= a; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; };
  const col = (k, al = 1) => rgba(k >= 0 ? mix(skin, [255, 255, 255], k) : mix(skin, sh, -k), al);
  // fingers (far -> near): base y (depth), segment lengths, width, tone
  const F = [
    { yb: -0.04, len: [0.15, 0.1, 0.08], w: 0.08, k: -0.38 },   // little
    { yb: -0.015, len: [0.19, 0.12, 0.095], w: 0.088, k: -0.26 }, // ring
    { yb: 0.012, len: [0.21, 0.135, 0.1], w: 0.092, k: -0.14 },  // middle
    { yb: 0.04, len: [0.2, 0.125, 0.095], w: 0.095, k: 0.0 },    // index (nearest)
  ];
  const fingerPts = (f, i) => {
    const c = curl * (0.9 + 0.05 * i);
    let px = 0.47, py = f.yb, ang = -0.12 - c * 0.35;
    const pts = [[px, py]];
    for (let j = 0; j < 3; j++) {
      px += Math.cos(ang) * f.len[j]; py += Math.sin(ang) * f.len[j];
      pts.push([px, py]); ang -= c * (j === 0 ? 0.85 : 0.75);
    }
    return pts;
  };
  const drawFinger = (f, i) => {
    const pts = fingerPts(f, i);
    // soft separation from the finger behind (darker skin, not an outline)
    ctx.strokeStyle = col(f.k - 0.35, 0.55); ctx.lineWidth = f.w + 0.018;
    ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let j = 1; j < 4; j++) ctx.lineTo(pts[j][0], pts[j][1]); ctx.stroke();
    for (let j = 0; j < 3; j++) { // tapered segments
      ctx.strokeStyle = col(f.k); ctx.lineWidth = f.w * (1 - j * 0.12);
      ctx.beginPath(); ctx.moveTo(pts[j][0], pts[j][1]); ctx.lineTo(pts[j + 1][0], pts[j + 1][1]); ctx.stroke();
    }
    // light along the upper edge of the finger
    ctx.strokeStyle = col(Math.min(0.35, f.k + 0.3), 0.45); ctx.lineWidth = f.w * 0.25;
    ctx.beginPath();
    for (let j = 0; j < 4; j++) { const q = pts[j]; const yy = q[1] - f.w * 0.28 * (1 - j * 0.1); j ? ctx.lineTo(q[0], yy) : ctx.moveTo(q[0] + 0.02, yy); }
    ctx.stroke();
  };
  const drawThumb = () => {
    // thenar mound at the base of the palm, then two thumb segments rising to grip
    ctx.fillStyle = col(0.05);
    ctx.beginPath(); ctx.ellipse(0.13, -0.005, 0.13, 0.07, -0.22, 0, TAU); ctx.fill();
    const a1 = -0.35 - grip * 0.45, a2 = a1 - 0.25 - grip * 0.5;
    const p0 = [0.17, -0.03], p1 = [p0[0] + Math.cos(a1) * 0.15, p0[1] + Math.sin(a1) * 0.15], p2 = [p1[0] + Math.cos(a2) * 0.11, p1[1] + Math.sin(a2) * 0.11];
    ctx.strokeStyle = col(-0.3, 0.5); ctx.lineWidth = 0.1;
    ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); ctx.stroke();
    ctx.strokeStyle = col(0.06); ctx.lineWidth = 0.088;
    ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke();
    ctx.lineWidth = 0.076; ctx.beginPath(); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); ctx.stroke();
    ctx.strokeStyle = col(0.3, 0.5); ctx.lineWidth = 0.022;
    ctx.beginPath(); ctx.moveTo(p0[0] - 0.02, p0[1] - 0.035); ctx.lineTo(p1[0], p1[1] - 0.03); ctx.lineTo(p2[0], p2[1] - 0.025); ctx.stroke();
  };
  ctx.save(); xf();
  // forearm (soft top light), optional sleeve
  const forearm = () => {
    ctx.beginPath();
    ctx.moveTo(0.04, -0.085); ctx.quadraticCurveTo(-0.3, -0.07, -L, -0.15 + L * 0.42); ctx.lineTo(-L, 0.29 + L * 0.42); ctx.quadraticCurveTo(-0.3, 0.22, 0.04, 0.135); ctx.closePath();
  };
  const fg = ctx.createLinearGradient(0, -0.1, 0, 0.16);
  fg.addColorStop(0, col(0.12)); fg.addColorStop(1, col(-0.45));
  forearm(); ctx.fillStyle = fg; ctx.fill();
  if (o.sleeve && !light) {
    ctx.save(); forearm(); ctx.clip();
    const sg = ctx.createLinearGradient(0, -0.2, 0, 0.4);
    sg.addColorStop(0, rgba(shade(o.sleeve, 0.35))); sg.addColorStop(1, rgba(shade(o.sleeve, -0.3)));
    ctx.fillStyle = sg; ctx.fillRect(-L - 0.1, -1, L - 0.42, 3); ctx.restore();
  }
  // far fingers behind the palm edge
  F.slice(0, 3).forEach(drawFinger);
  // palm wedge: concave palm on top, rounded back of the hand below
  ctx.beginPath();
  ctx.moveTo(0, -0.085);
  ctx.quadraticCurveTo(0.25, -0.04, 0.5, -0.06);
  ctx.quadraticCurveTo(0.58, 0.01, 0.5, 0.085);
  ctx.quadraticCurveTo(0.25, 0.18, 0, 0.13);
  ctx.quadraticCurveTo(-0.03, 0.02, 0, -0.085);
  const pg = ctx.createLinearGradient(0, -0.08, 0, 0.14);
  pg.addColorStop(0, col(0.1)); pg.addColorStop(0.55, col(-0.05)); pg.addColorStop(1, col(-0.45));
  ctx.fillStyle = pg; ctx.fill();
  // palm hollow (soft shade) where an object would sit
  ctx.fillStyle = col(-0.25, 0.35); ctx.beginPath(); ctx.ellipse(0.31, -0.045, 0.16, 0.022, 0, 0, TAU); ctx.fill();
  ctx.restore();
  const front = () => {
    ctx.save(); xf();
    drawFinger(F[3], 3);
    drawThumb();
    ctx.restore();
  };
  if (!o.deferFront) front();
  if (light) {
    const c = Math.cos(tilt * facing), sn = Math.sin(tilt * facing);
    FX.glow(ctx, x + facing * s * 0.4 * c, y + s * 0.4 * sn * facing, s * 0.9, CYAN, 0.18 * a);
  }
  // resting point (on the palm hollow)
  const lx = 0.33 * facing * s, ly = -0.05 * s;
  const c = Math.cos(tilt * facing), sn = Math.sin(tilt * facing);
  const ret = [x + lx * c - ly * sn, y + lx * sn + ly * c];
  ret.front = o.deferFront ? front : () => {};
  return ret;
}

// ---------------------------------------------------------------- soft-lit figures
// Offscreen buffers for building lit silhouettes. The canvas backend records drawImage(canvas) lazily, so a
// buffer must never be changed after it has been drawn somewhere: every stage gets a fresh canvas, and recent
// ones are kept referenced until the frame has certainly been rasterised.
const { createCanvas } = require('@napi-rs/canvas');
const _keep = []; let _keepI = 0;
function scratch(id, w, h) {
  const c = createCanvas(Math.max(2, Math.ceil(w)), Math.max(2, Math.ceil(h)));
  _keep[_keepI] = c; _keepI = (_keepI + 1) % 160;
  return [c, c.getContext('2d')];
}
// FX.figure with a soft fill light across the body, a rim light along the edges that face the light,
// and a faint halo, so it never vanishes into a dark background (no crescent marks on the head).
// o: color (body), fill (fill-light colour), fillA, rim (rim colour), rimA, rimW (rim offset, x h),
//    light [dx,dy] (screen direction toward the key light), halo (alpha), alpha, facing, child, phase,
//    shade(bctx, ax, ay, hs) optional extra painting on the body (source-atop, buffer coords: feet at ax,ay, height hs)
// Returns FX.figure's {head, handL, handR} in world coords.
function litFigure(ctx, x, y, h, pose, o = {}) {
  const fo = { facing: o.facing, child: o.child, phase: o.phase };
  let lx = (o.light || [1, -0.7])[0], ly = (o.light || [1, -0.7])[1];
  const ll = Math.hypot(lx, ly) || 1; lx /= ll; ly /= ll;
  const rimC = o.rim || [200, 220, 255];
  const d = Math.max(1.2, h * (o.rimW ?? 0.012));
  ctx.save();
  if (o.alpha != null) ctx.globalAlpha *= o.alpha;
  const base = ctx.globalAlpha;
  // halo: faint copies all around (soft edge glow so the figure separates from a dark ground)
  const haloA = o.halo ?? 0.3;
  if (haloA > 0) {
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * TAU, r = d * (i % 2 ? 2.2 : 1.3);
      ctx.globalAlpha = base * haloA * 0.12;
      FX.figure(ctx, x + Math.cos(a) * r, y + Math.sin(a) * r, h, pose, Object.assign({ color: rimC }, fo));
    }
    ctx.globalCompositeOperation = 'source-over';
  }
  // rim: copies shifted toward the light peek out from behind the body along the lit edges
  const rimA = o.rimA ?? 0.85;
  ctx.globalAlpha = base * rimA * 0.45;
  FX.figure(ctx, x + lx * d * 1.9, y + ly * d * 1.9, h, pose, Object.assign({ color: rimC }, fo));
  ctx.globalAlpha = base * rimA;
  FX.figure(ctx, x + lx * d, y + ly * d, h, pose, Object.assign({ color: mix(rimC, [255, 255, 255], 0.25) }, fo));
  ctx.globalAlpha = base;
  // body with a directional fill light, built in a small buffer (capped resolution, drawn up)
  const q = Math.min(1, 200 / h), hs = h * q;
  const pad = Math.ceil(hs * 0.66), W = pad * 2, H = Math.ceil(hs * 1.34);
  const ax = pad, ay = Math.ceil(hs * 1.25);
  const [bc, bx] = scratch('b', W, H);
  const r = FX.figure(bx, ax, ay, hs, pose, Object.assign({ color: o.color || [58, 60, 86] }, fo));
  bx.globalCompositeOperation = 'source-atop';
  const myp = ay - hs * 0.55;
  const g = bx.createLinearGradient(ax + lx * hs * 0.3, myp + ly * hs * 0.5, ax - lx * hs * 0.3, myp - ly * hs * 0.5);
  g.addColorStop(0, rgba(o.fill || rimC, o.fillA ?? 0.3)); g.addColorStop(1, rgba(o.fill || rimC, 0));
  bx.fillStyle = g; bx.fillRect(0, 0, W, H);
  if (o.shade) o.shade(bx, ax, ay, hs);
  const X0 = x - ax / q, Y0 = y - ay / q;
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(bc, 0, 0, W, H, X0, Y0, W / q, H / q);
  ctx.restore();
  const tw = (pt) => [X0 + pt[0] / q, Y0 + pt[1] / q];
  return { head: tw(r.head), handL: tw(r.handL), handR: tw(r.handR) };
}

function orb(ctx, x, y, r, col, a = 1) {
  FX.glow(ctx, x, y, r * 4.5, col, 0.35 * a);
  const g = ctx.createRadialGradient(x - r * 0.3, y - r * 0.35, 0, x, y, r);
  g.addColorStop(0, rgba([255, 252, 238], a)); g.addColorStop(0.55, rgba(col, a)); g.addColorStop(1, rgba(shade(col, -0.25), a));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
}
// jagged polyline between two points (deterministic)
function jag(x0, y0, x1, y1, n, amp, seed) {
  const pts = [];
  const dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy), nx = -dy / len, ny = dx / len;
  for (let i = 0; i <= n; i++) {
    const k = i / n, off = (i === 0 || i === n) ? 0 : (U.hash2(seed, i) * 2 - 1) * amp;
    pts.push([x0 + dx * k + nx * off, y0 + dy * k + ny * off]);
  }
  return pts;
}
function polyLen(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
// stroke the first fraction k of a polyline
function strokePartial(ctx, pts, k) {
  if (k <= 0) return;
  const total = polyLen(pts) * clamp(k);
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  let acc = 0;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (acc + d >= total) { const f = (total - acc) / d; ctx.lineTo(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f); break; }
    ctx.lineTo(b[0], b[1]); acc += d;
  }
  ctx.stroke();
}
function strokePoly(ctx, pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.stroke(); }

// ---------------------------------------------------------------- vignettes
module.exports = {
  // storm clouds wrung; luminous drops fall into a vial that brightens
  distill_light: {
    draw(ctx, w, h, p) {
      const { unit, cx, port } = frame(w, h);
      night(ctx, w, h, p, [8, 9, 22], [22, 20, 44]);
      const wring = smooth(p.u / 0.85);
      const fill = lerp(0.12, 0.78, smooth(p.u / 0.85));
      const cY = port ? h * 0.27 : h * 0.2;
      const CW = unit * lerp(0.78, 0.6, wring), CH = unit * 0.2;
      // cloud: soft dark lobes, pinched toward the middle as it is wrung
      ctx.save();
      for (let i = 0; i < 9; i++) {
        const k = i / 8 - 0.5;
        const pinch = 1 - wring * 0.45 * Math.exp(-k * k * 10);
        const lx = cx + k * CW, ly = cY + Math.sin(i * 1.7) * CH * 0.12 + Math.sin(p.t * 0.4 + i) * unit * 0.004;
        const r = CH * (0.62 - Math.abs(k) * 0.5) * pinch * (0.9 + 0.2 * U.hash2(i, 3));
        const g = ctx.createRadialGradient(lx, ly - r * 0.3, 0, lx, ly, r * 1.25);
        g.addColorStop(0, rgba([78, 74, 108], 0.95)); g.addColorStop(0.6, rgba([46, 42, 70], 0.9)); g.addColorStop(1, rgba([30, 28, 52], 0));
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(lx, ly, r * 1.25, 0, TAU); ctx.fill();
      }
      // twist bands (helix) tightening = wringing
      const freq = lerp(1.2, 4.2, wring), ph = p.t * 0.5 + wring * 6;
      ctx.lineCap = 'round';
      for (let b = 0; b < 3; b++) {
        ctx.strokeStyle = rgba([150, 140, 190], 0.22); ctx.lineWidth = unit * 0.008;
        ctx.beginPath();
        for (let i = 0; i <= 40; i++) {
          const k = i / 40 - 0.5, x = cx + k * CW * 0.85;
          const env = Math.cos(k * Math.PI) * (1 - wring * 0.45 * Math.exp(-k * k * 10));
          const y = cY + Math.sin(k * TAU * freq * (k < 0 ? 1 : -1) + ph + b * 2.1) * CH * 0.35 * env;
          i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
        }
        ctx.stroke();
      }
      // inner gold being squeezed out
      FX.glow(ctx, cx, cY + CH * 0.2, CH * 0.9, GOLD, 0.12 + 0.12 * wring);
      ctx.restore();
      // vial
      const vb = port ? h * 0.66 : h * 0.92, vh = unit * 0.36, vw = unit * 0.15, nw = unit * 0.055;
      const vtop = vb - vh, bulbR = vw / 2, bulbY = vb - bulbR;
      const vialPath = () => {
        ctx.beginPath();
        ctx.moveTo(cx - nw / 2, vtop);
        ctx.lineTo(cx - nw / 2, vtop + vh * 0.3);
        ctx.quadraticCurveTo(cx - vw / 2, vtop + vh * 0.38, cx - vw / 2, bulbY);
        ctx.arc(cx, bulbY, bulbR, Math.PI, 0, true);
        ctx.quadraticCurveTo(cx + vw / 2, vtop + vh * 0.38, cx + nw / 2, vtop + vh * 0.3);
        ctx.lineTo(cx + nw / 2, vtop);
      };
      const bright = 0.3 + 0.7 * fill + 0.05 * Math.sin(p.t * 1.2);
      FX.glow(ctx, cx, bulbY, unit * 0.45, AMBER, 0.12 + 0.25 * fill);
      // glass body
      vialPath(); ctx.closePath(); ctx.fillStyle = rgba([120, 140, 190], 0.1); ctx.fill();
      // liquid
      ctx.save(); vialPath(); ctx.closePath(); ctx.clip();
      const ly = vb - vh * fill;
      const lg = ctx.createLinearGradient(0, ly, 0, vb);
      lg.addColorStop(0, rgba(shade(GOLD, 0.4), 0.95)); lg.addColorStop(1, rgba(AMBER, 0.9));
      ctx.globalAlpha = 0.55 + 0.45 * bright;
      ctx.fillStyle = lg;
      ctx.beginPath(); ctx.moveTo(cx - vw, ly);
      for (let i = 0; i <= 12; i++) ctx.lineTo(cx - vw + i * vw / 6, ly + Math.sin(p.t * 2 + i) * unit * 0.002);
      ctx.lineTo(cx + vw, vb + 2); ctx.lineTo(cx - vw, vb + 2); ctx.fill();
      ctx.restore();
      FX.glow(ctx, cx, (ly + vb) / 2, vw * 1.2, GOLD, 0.25 * bright);
      // glass outline + highlight + rim
      vialPath(); ctx.strokeStyle = rgba([200, 220, 255], 0.55); ctx.lineWidth = unit * 0.006; ctx.stroke();
      ctx.strokeStyle = rgba([255, 255, 255], 0.35); ctx.lineWidth = unit * 0.008;
      ctx.beginPath(); ctx.arc(cx, bulbY, bulbR * 0.75, Math.PI * 1.05, Math.PI * 1.35); ctx.stroke();
      ctx.fillStyle = rgba([200, 220, 255], 0.5); ctx.fillRect(cx - nw * 0.65, vtop - unit * 0.006, nw * 1.3, unit * 0.012);
      // drops
      const y0 = cY + CH * 0.45, y1 = ly, fallT = 1.1, period = 0.55;
      const gA = 2 * (y1 - y0) / (fallT * fallT);
      for (let k = Math.floor((p.t - fallT) / period) - 1; k <= Math.floor(p.t / period); k++) {
        const age = p.t - k * period;
        const xj = cx + (U.hash2(k, 5) - 0.5) * unit * 0.025;
        if (age < 0) continue;
        if (age < fallT) {
          const y = y0 + 0.5 * gA * age * age;
          const r = unit * 0.011 * (0.7 + 0.3 * smooth(age / 0.3));
          FX.glow(ctx, xj, y, r * 5, GOLD, 0.35);
          ctx.fillStyle = rgba([255, 245, 210], 0.95);
          ctx.beginPath(); ctx.moveTo(xj, y - r * 2.2); ctx.quadraticCurveTo(xj + r, y - r * 0.3, xj, y + r); ctx.quadraticCurveTo(xj - r, y - r * 0.3, xj, y - r * 2.2); ctx.fill();
        } else if (age < fallT + 0.6) {
          const s = (age - fallT) / 0.6;
          FX.glow(ctx, xj, y1, unit * 0.05 * (0.4 + s), GOLD, 0.35 * (1 - s));
        }
      }
    },
  },

  // human hand offers a glowing orb; a cyan hand of light receives it
  gift_orb: {
    draw(ctx, w, h, p) {
      const { unit, cx, cy, port } = frame(w, h);
      night(ctx, w, h, p, [7, 9, 22], [20, 22, 46]);
      const k = easeInOut((p.u - 0.15) / 0.55);
      const s = unit * 0.36, y = port ? cy + unit * 0.12 : cy + unit * 0.14;
      const lift = Math.sin(Math.PI * k);
      FX.glow(ctx, cx, y - unit * 0.1, unit * 0.6, [80, 70, 140], 0.15);
      const hx = cx - unit * 0.42 + k * unit * 0.05, hy = y - lift * unit * 0.03;
      const restL = sideHand(ctx, hx, hy, s, 1, { curl: 0.35, tilt: -0.05 - 0.12 * lift, sleeve: [40, 44, 70] });
      const lx = cx + unit * 0.42 - k * unit * 0.05, ly = y + (k > 0.9 ? 0 : 0) + unit * 0.01 * smooth((p.u - 0.6) / 0.15) * Math.cos((p.u - 0.6) * 20) * (1 - smooth((p.u - 0.75) / 0.1));
      const glowUp = smooth((p.u - 0.62) / 0.25);
      const restR = sideHand(ctx, lx, ly, s, -1, { light: true, curl: 0.35, alpha: 0.75 + 0.25 * glowUp });
      const r = unit * 0.06;
      const ox = lerp(restL[0], restR[0], k), oy = lerp(restL[1], restR[1], k) - r - lift * unit * 0.13;
      orb(ctx, ox, oy, r * (1 + 0.03 * Math.sin(p.t * 1.5)), GOLD);
      if (glowUp > 0) {
        FX.ring(ctx, restR[0], restR[1] - r, r * (1.2 + glowUp * 1.8), unit * 0.004, GOLD, 0.35 * (1 - glowUp));
        FX.glow(ctx, restR[0], restR[1] - r, unit * 0.35, CYAN, 0.18 * glowUp);
      }
    },
  },

  // a scarred silhouette passes clean light to an unscarred figure of light
  wounds_vs_wisdom: {
    draw(ctx, w, h, p) {
      const { unit, cx, port } = frame(w, h);
      night(ctx, w, h, p, [7, 8, 20], [22, 20, 44]);
      const gy = port ? h * 0.66 : h * 0.88, fh = unit * 0.58;
      FX.glow(ctx, cx, gy - fh * 0.5, unit * 0.7, [70, 60, 130], 0.18);
      groundPlane(ctx, w, h, gy);
      const lx = cx - unit * 0.3, rx = cx + unit * 0.3;
      const k = easeInOut((p.u - 0.15) / 0.6);
      // scarred human (left, reaching right)
      const L = litFigure(ctx, lx, gy, fh, 'reach', {
        color: [84, 68, 96], facing: -1, rim: [170, 225, 255], rimA: 0.7, fill: [150, 190, 240], fillA: 0.2, light: [1, -0.5], halo: 0.22,
      });
      // scars: glowing crimson seams on the body
      const scar = (pts) => {
        ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.strokeStyle = rgba(CRIMSON, 0.25); ctx.lineWidth = unit * 0.016; strokePoly(ctx, pts);
        ctx.strokeStyle = rgba([240, 90, 110], 0.85); ctx.lineWidth = unit * 0.005; strokePoly(ctx, pts);
        ctx.restore();
      };
      scar(jag(lx - fh * 0.07, gy - fh * 0.72, lx + fh * 0.06, gy - fh * 0.56, 5, fh * 0.012, 1));
      scar(jag(lx - fh * 0.05, gy - fh * 0.62, lx + fh * 0.02, gy - fh * 0.66, 3, fh * 0.008, 2));
      scar(jag(lx - fh * 0.03, gy - fh * 0.35, lx - fh * 0.01, gy - fh * 0.22, 3, fh * 0.01, 3));
      // figure of light (right, reaching left), brightening as it receives
      const bright = 0.55 + 0.45 * smooth((p.u - 0.55) / 0.3);
      const Rf = FX.figure(ctx, rx, gy, fh, 'reach', { color: mix([90, 170, 210], [200, 240, 255], bright), alpha: 0.9, facing: 1, glow: CYAN, glowA: 0.18 + 0.2 * bright });
      // clean light travels from the scarred hand to the hand of light
      const a = L.handR, b = Rf.handR;
      const ox = lerp(a[0], b[0], k), oy = lerp(a[1], b[1], k) - Math.sin(Math.PI * k) * unit * 0.06;
      // faint stream
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 10; i++) {
        const f = ((p.t * 0.25 + i / 10) % 1);
        const x = lerp(a[0], b[0], f), y = lerp(a[1], b[1], f) - Math.sin(Math.PI * f) * unit * 0.06;
        FX.glow(ctx, x, y, unit * 0.018, [255, 240, 210], 0.25 * Math.sin(Math.PI * f));
      }
      ctx.restore();
      orb(ctx, ox, oy, unit * 0.028, [255, 236, 190]);
    },
  },

  // a figure of light raises a dome of light over small human silhouettes
  guardian_shield: {
    draw(ctx, w, h, p) {
      const { unit, cx, port } = frame(w, h);
      night(ctx, w, h, p, [8, 7, 20], [24, 18, 40]);
      const gy = port ? h * 0.68 : h * 0.9;
      const raise = smooth(p.u / 0.6);
      const pose = lerpPose({ lean: 0, armL: [1.25, 0.5], armR: [-1.25, -0.5], legL: [0.08, 0], legR: [-0.08, 0], head: 0.1 }, 'arms_up', raise);
      const GH = unit * 0.4;
      const pr = probeFigure(ctx, cx, gy, GH, pose, {});
      const RY = (gy - Math.min(pr.handL[1], pr.handR[1])) * 1.02;
      const R0 = Math.max(RY * 1.15, Math.abs(pr.handL[0] - cx) * 1.6, unit * 0.3);
      const domeR = (x) => { const d = (x - cx) / R0; return Math.abs(d) < 1 ? gy - RY * Math.sqrt(1 - d * d) : gy; };
      // threat: dark red drops falling, stopped at the dome
      for (let i = 0; i < 14; i++) {
        const x = cx + (U.hash2(i, 9) - 0.5) * w * 0.95;
        const sp = unit * (0.12 + 0.06 * U.hash2(i, 4));
        const dx = (x - cx) / R0;
        const domeY = domeR(x);
        const y0 = -unit * 0.1, span = domeY - y0;
        const y = y0 + ((p.t * sp + U.hash2(i, 2) * span) % span);
        const near = clamp((y - (domeY - unit * 0.1)) / (unit * 0.1));
        FX.glow(ctx, x, y, unit * 0.025, CRIMSON, 0.3 * (1 - near * 0.7));
        ctx.fillStyle = rgba([150, 30, 50], 0.8 * (1 - near));
        ctx.beginPath(); ctx.arc(x, y, unit * 0.006, 0, TAU); ctx.fill();
        if (Math.abs(dx) < 1 && near > 0.6) FX.glow(ctx, x, domeY, unit * 0.04, [255, 200, 150], 0.25 * (near - 0.6));
      }
      groundPlane(ctx, w, h, gy, [16, 14, 28]);
      // guardian (behind), arms rising
      FX.glow(ctx, cx, gy - unit * 0.4, unit * 0.5, CYAN, 0.12 + 0.1 * raise);
      FX.figure(ctx, cx, gy, GH, pose, { color: [190, 236, 255], alpha: 0.8, glow: CYAN, glowA: 0.3 });
      // dome
      ctx.save();
      ctx.beginPath(); ctx.ellipse(cx, gy, R0, RY, 0, Math.PI, TAU); ctx.closePath();
      const dg = ctx.createRadialGradient(cx, gy, R0 * 0.3, cx, gy, R0 * 1.02);
      dg.addColorStop(0, rgba(GOLD, 0.05)); dg.addColorStop(0.8, rgba(CYAN, 0.1)); dg.addColorStop(1, rgba([200, 245, 255], 0.28));
      ctx.fillStyle = dg; ctx.fill();
      ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba([200, 245, 255], 0.5 + 0.08 * Math.sin(p.t * 1.3)); ctx.lineWidth = unit * 0.006;
      ctx.beginPath(); ctx.ellipse(cx, gy, R0, RY, 0, Math.PI, TAU); ctx.stroke();
      ctx.restore();
      // small humans sheltered, warm
      const sh = unit * 0.17;
      const kids = [[-0.3, 1, 'stand', false], [-0.2, 0.72, 'stand', true], [0.18, 1, 'kneel', false], [0.3, 0.95, 'stand', false], [0.38, 0.7, 'stand', true]];
      for (const [ox, sc, pose2, child] of kids) {
        litFigure(ctx, cx + ox * unit, gy, sh * sc, pose2, {
          color: [120, 92, 74], child, facing: ox < 0 ? -1 : 1, rim: [200, 240, 255], rimA: 0.7, fill: [255, 214, 160], fillA: 0.22,
          light: [-ox, -1.2], halo: 0.2,
        });
      }
      FX.glow(ctx, cx - unit * 0.25, gy - sh * 0.5, unit * 0.15, GOLD, 0.12); FX.glow(ctx, cx + unit * 0.28, gy - sh * 0.5, unit * 0.15, GOLD, 0.12);
    },
  },

  // tangled dark-red threads untangle into parallel gold lines
  untangle_knots: {
    draw(ctx, w, h, p) {
      const { unit, cx, cy } = frame(w, h);
      night(ctx, w, h, p, [7, 8, 20], [18, 18, 40], 14000);
      const N = 7, x0 = w * 0.06, x1 = w * 0.94;
      const band = unit * 0.36;
      // analysis scan: soft cyan light sweeping
      const scan = lerp(x0, x1, smooth((p.u - 0.05) / 0.75));
      FX.glow(ctx, scan, cy, unit * 0.35, CYAN, 0.12 * (1 - smooth((p.u - 0.8) / 0.1)));
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      for (let i = 0; i < N; i++) {
        const s = smooth((p.u - 0.12 - i * 0.04) / 0.55);
        const ty = cy + (i / (N - 1) - 0.5) * band;
        const ph = U.hash2(i, 1) * TAU, ph2 = U.hash2(i, 2) * TAU;
        const kf = 3 + Math.floor(U.hash2(i, 3) * 3);
        const pts = [];
        for (let j = 0; j <= 110; j++) {
          const q = j / 110;
          const bell = Math.exp(-Math.pow((q - 0.5) / 0.2, 2));
          const loop = unit * 0.07 * bell * (1 - s);
          const wave = (Math.sin(q * 7 + ph + p.t * 0.25) * 0.6 + Math.sin(q * 13 + ph2) * 0.4) * unit * 0.13 * bell * (1 - s);
          const conv = (cy - ty) * bell * 0.85 * (1 - s); // threads bunch into one knot
          const a = q * TAU * kf + ph;
          const x = lerp(x0, x1, q) + Math.cos(a) * loop;
          const y = ty + conv + wave + Math.sin(a) * loop + Math.sin(q * 9 + p.t * 0.6 + i) * unit * 0.003;
          pts.push([x, y]);
        }
        const col = mix(CRIMSON, GOLD, s);
        ctx.strokeStyle = rgba(mix(BLOOD, AMBER, s), 0.35); ctx.lineWidth = unit * 0.022; strokePoly(ctx, pts);
        ctx.strokeStyle = rgba(shade(col, 0.15), 0.95); ctx.lineWidth = unit * 0.007; strokePoly(ctx, pts);
      }
      const done = smooth((p.u - 0.6) / 0.25);
      FX.glow(ctx, cx, cy, unit * 0.5, GOLD, 0.1 * done);
    },
  },

  // glowing blueprint lines and gears assemble faster than red ripples spread
  blueprint_solutions: {
    draw(ctx, w, h, p) {
      const { unit, cx, cy, port } = frame(w, h);
      FX.bg(ctx, w, h, [6, 10, 24], [12, 18, 40]);
      // red ripples from a wound point (slow)
      const ox = port ? w * 0.2 : w * 0.12, oy = port ? h * 0.82 : h * 0.82;
      for (let k = 0; k < 4; k++) {
        const f = ((p.t * 0.09 + k / 4) % 1);
        const r = unit * (0.05 + f * 0.9);
        FX.ring(ctx, ox, oy, r, unit * 0.012, CRIMSON, 0.5 * Math.sin(Math.PI * f));
      }
      FX.glow(ctx, ox, oy, unit * 0.1, CRIMSON, 0.3);
      // blueprint field grows fast and covers the ripples
      const by = port ? cy - unit * 0.1 : cy;
      const grow = U.easeOut((p.u + 0.08) / 0.55);
      const RB = unit * (0.22 + 0.42 * grow);
      const cover = ctx.createRadialGradient(cx, by, 0, cx, by, RB);
      cover.addColorStop(0, 'rgba(8,16,36,0.95)'); cover.addColorStop(0.75, 'rgba(8,16,36,0.85)'); cover.addColorStop(1, 'rgba(8,16,36,0)');
      ctx.fillStyle = cover; ctx.fillRect(cx - RB, by - RB, RB * 2, RB * 2);
      // grid inside the field
      ctx.save();
      ctx.beginPath(); ctx.arc(cx, by, RB * 0.9, 0, TAU); ctx.clip();
      ctx.strokeStyle = rgba(CYAN, 0.07); ctx.lineWidth = 1;
      const gs = unit / 12;
      ctx.beginPath();
      for (let x = cx % gs; x < w; x += gs) { ctx.moveTo(x, 0); ctx.lineTo(x, h); }
      for (let y = by % gs; y < h; y += gs) { ctx.moveTo(0, y); ctx.lineTo(w, y); }
      ctx.stroke();
      ctx.restore();
      // gears
      const gear = (x, y, r, teeth, ang, a) => {
        if (a <= 0) return;
        ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
        ctx.beginPath();
        for (let i = 0; i < teeth * 4; i++) {
          const q = i / (teeth * 4) * TAU, rr = (i % 4 < 2) ? r : r * 0.82;
          i ? ctx.lineTo(Math.cos(q) * rr, Math.sin(q) * rr) : ctx.moveTo(Math.cos(q) * rr, Math.sin(q) * rr);
        }
        ctx.closePath();
        ctx.fillStyle = rgba([40, 110, 150], 0.18 * a); ctx.fill();
        ctx.strokeStyle = rgba(CYAN, 0.85 * a); ctx.lineWidth = unit * 0.005; ctx.stroke();
        ctx.beginPath(); ctx.arc(0, 0, r * 0.5, 0, TAU); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(-r * 0.5, 0); ctx.lineTo(r * 0.5, 0); ctx.moveTo(0, -r * 0.5); ctx.lineTo(0, r * 0.5); ctx.stroke();
        ctx.restore();
        FX.glow(ctx, x, y, r * 0.35, GOLD, 0.5 * a);
      };
      const r1 = unit * 0.13, r2 = unit * 0.085, r3 = unit * 0.065;
      const spin = p.t * 0.35;
      const g1 = [cx - unit * 0.05, by + unit * 0.02], g2 = [g1[0] + (r1 + r2) * 0.9 * Math.cos(-0.5), g1[1] + (r1 + r2) * 0.9 * Math.sin(-0.5)];
      const g3 = [g1[0] + (r1 + r3) * 0.9 * Math.cos(2.4), g1[1] + (r1 + r3) * 0.9 * Math.sin(2.4)];
      const ap = (a0) => smooth((p.u - a0) / 0.15);
      // construction lines drawn in
      ctx.save(); ctx.lineCap = 'round';
      ctx.strokeStyle = rgba(CYAN, 0.55); ctx.lineWidth = unit * 0.003;
      const fx0 = cx - unit * 0.36, fx1 = cx + unit * 0.36, fy0 = by - unit * 0.27, fy1 = by + unit * 0.27;
      strokePartial(ctx, [[fx0, fy0], [fx1, fy0], [fx1, fy1], [fx0, fy1], [fx0, fy0]], smooth((p.u - 0.0) / 0.45));
      strokePartial(ctx, [[g1[0], fy1], [g1[0], g1[1]], [g2[0], g2[1]], [fx1, g2[1]]], smooth((p.u - 0.2) / 0.35));
      strokePartial(ctx, [[fx0, g3[1]], [g3[0], g3[1]], [g1[0], g1[1]]], smooth((p.u - 0.3) / 0.35));
      ctx.setLineDash([unit * 0.01, unit * 0.012]);
      ctx.strokeStyle = rgba(CYAN, 0.35);
      ctx.beginPath(); ctx.arc(g1[0], g1[1], r1 * 1.35, 0, TAU * smooth((p.u - 0.35) / 0.4)); ctx.stroke();
      ctx.restore();
      gear(g1[0], g1[1], r1, 12, spin, Math.max(0.6, ap(0.0)));
      gear(g2[0], g2[1], r2, 8, -spin * r1 / r2 + 0.2, ap(0.15));
      gear(g3[0], g3[1], r3, 6, -spin * r1 / r3 + 0.1, ap(0.3));
      FX.glow(ctx, cx, by, unit * 0.45, CYAN, 0.08 + 0.08 * grow);
      FX.ring(ctx, cx, by, RB * 0.86, unit * 0.005, CYAN, 0.35);
      FX.ring(ctx, cx, by, RB * 0.86, unit * 0.02, CYAN, 0.08);
    },
  },

  // grandparent -> parent -> child; a dark red loop passes from one to the next
  pain_loops_generations: {
    draw(ctx, w, h, p) {
      const { unit, cx, port } = frame(w, h);
      night(ctx, w, h, p, [7, 7, 18], [26, 18, 40]);
      const gy = port ? h * 0.66 : h * 0.88;
      // dusk band so silhouettes read
      const hz = ctx.createLinearGradient(0, gy - unit * 0.5, 0, gy);
      hz.addColorStop(0, 'rgba(70,40,90,0)'); hz.addColorStop(1, 'rgba(110,60,110,0.45)');
      ctx.fillStyle = hz; ctx.fillRect(0, gy - unit * 0.5, w, unit * 0.5);
      groundPlane(ctx, w, h, gy, [14, 12, 24], [160, 90, 140]);
      const fig = [
        { x: cx - unit * 0.34, h: unit * 0.5, pose: { lean: 0.16, head: 0.35, armL: [0.35, 0.15], armR: [-0.05, -0.1], legL: [0.06, 0], legR: [-0.06, 0.05] }, child: false },
        { x: cx - unit * 0.02, h: unit * 0.56, pose: 'stand', child: false },
        { x: cx + unit * 0.27, h: unit * 0.34, pose: 'stand', child: true },
      ];
      const chest = fig.map((f) => {
        // rim-lit by the dusk glow behind them, soft fill so each pose reads against the sky
        const r = litFigure(ctx, f.x, gy, f.h, f.pose, {
          color: [70, 56, 84], child: f.child, rim: [236, 184, 220], rimA: 0.8, fill: [190, 150, 210], fillA: 0.25,
          light: [0.5, -1], halo: 0.3,
        });
        f.r = r;
        return [lerp(r.head[0], f.x, 0.45), r.head[1] + f.h * (f.child ? 0.24 : 0.2)];
      });
      // grandparent's cane
      const gp = fig[0];
      ctx.strokeStyle = rgba([92, 72, 100]); ctx.lineWidth = unit * 0.009; ctx.lineCap = 'round';
      const ch = gp.r.handR[0] > gp.r.handL[0] ? gp.r.handR : gp.r.handL;
      ctx.beginPath(); ctx.moveTo(ch[0], ch[1] - unit * 0.01); ctx.lineTo(ch[0] + unit * 0.02, gy); ctx.stroke();
      // loop travels
      const k1 = easeInOut((p.u - 0.12) / 0.28), k2 = easeInOut((p.u - 0.5) / 0.28);
      const pos = (k) => k;
      let x, y, arc;
      if (k2 <= 0) { x = lerp(chest[0][0], chest[1][0], k1); y = lerp(chest[0][1], chest[1][1], k1); arc = Math.sin(Math.PI * k1); }
      else { x = lerp(chest[1][0], chest[2][0], k2); y = lerp(chest[1][1], chest[2][1], k2); arc = Math.sin(Math.PI * k2); }
      y -= arc * unit * 0.1;
      void pos; void gp;
      const loopRing = (lx, ly, rx, a, spinA) => {
        if (a <= 0) return;
        ctx.save(); ctx.lineCap = 'round';
        FX.glow(ctx, lx, ly, rx * 1.8, CRIMSON, 0.22 * a);
        ctx.strokeStyle = rgba(BLOOD, 0.9 * a); ctx.lineWidth = unit * 0.016;
        ctx.beginPath(); ctx.ellipse(lx, ly, rx, rx * 0.36, 0, 0, TAU); ctx.stroke();
        ctx.strokeStyle = rgba(CRIMSON, 0.9 * a); ctx.lineWidth = unit * 0.006;
        ctx.beginPath(); ctx.ellipse(lx, ly, rx, rx * 0.36, 0, spinA, spinA + 2.2); ctx.stroke();
        ctx.restore();
      };
      // faint residue on those it has passed through
      loopRing(chest[0][0], chest[0][1], unit * 0.07, 0.25 + 0.75 * (1 - smooth(k1 * 3)), p.t * 1.2);
      if (k1 >= 1) loopRing(chest[1][0], chest[1][1], unit * 0.075, 0.3 + 0.7 * (1 - smooth(k2 * 3)), p.t * 1.2 + 1);
      loopRing(x, y, unit * lerp(0.075, 0.06, k2), 1, p.t * 1.6);
      // the red thread: one continuous line passed from grandparent to parent to child (large to small)
      const seg = (A, B, t) => [lerp(A[0], B[0], t), lerp(A[1], B[1], t) - Math.sin(Math.PI * t) * unit * 0.1];
      const thread = [];
      const n = 24;
      for (let i = 0; i <= n; i++) { const t = (i / n) * k1; if (k1 > 0) thread.push(seg(chest[0], chest[1], t)); }
      if (k2 > 0) for (let i = 1; i <= n; i++) thread.push(seg(chest[1], chest[2], (i / n) * k2));
      if (thread.length > 1) {
        ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        const sway = (q, i) => [q[0], q[1] + Math.sin(p.t * 0.8 + i * 0.35) * unit * 0.004];
        const path = () => { ctx.beginPath(); thread.forEach((q, i) => { const r = sway(q, i); i ? ctx.lineTo(r[0], r[1]) : ctx.moveTo(r[0], r[1]); }); };
        ctx.globalCompositeOperation = 'lighter';
        path(); ctx.strokeStyle = rgba(CRIMSON, 0.22); ctx.lineWidth = unit * 0.022; ctx.stroke();
        ctx.globalCompositeOperation = 'source-over';
        path(); ctx.strokeStyle = rgba([226, 64, 88], 0.95); ctx.lineWidth = unit * 0.007; ctx.stroke();
        path(); ctx.strokeStyle = rgba([255, 150, 160], 0.55); ctx.lineWidth = unit * 0.0025; ctx.stroke();
        ctx.restore();
      }
    },
  },

  // dark cells divide and multiply across the frame
  virus_replicate: {
    draw(ctx, w, h, p) {
      const { unit } = frame(w, h);
      FX.bg(ctx, w, h, [10, 6, 18], [24, 10, 28]);
      const D = 6;
      const gen = clamp(p.u / 0.85) * D;
      const L = Math.min(D - 1, Math.floor(gen)), f = gen - L;
      const e = gen >= D ? 1 : smooth((f - 0.35) / 0.6);
      // build k-d tree of regions down to depth L+1
      const cell = (rx, ry, rw, rh, id) => { const r = Math.min(0.36 * Math.sqrt(rw * rh), 0.46 * Math.min(rw, rh)) * (0.85 + 0.2 * U.hash2(id, 9)); return { x: rx + rw / 2 + (U.hash2(id, 4) - 0.5) * (rw - 2 * r) * 0.8, y: ry + rh / 2 + (U.hash2(id, 6) - 0.5) * (rh - 2 * r) * 0.8, r }; };
      let nodes = [{ rx: 0, ry: 0, rw: w, rh: h, id: 1 }];
      for (let d = 0; d < L; d++) nodes = nodes.flatMap(split);
      function split(n) {
        const j = 0.36 + 0.28 * U.hash2(n.id, 77);
        if (n.rw >= n.rh) return [{ rx: n.rx, ry: n.ry, rw: n.rw * j, rh: n.rh, id: n.id * 2 }, { rx: n.rx + n.rw * j, ry: n.ry, rw: n.rw * (1 - j), rh: n.rh, id: n.id * 2 + 1 }];
        return [{ rx: n.rx, ry: n.ry, rw: n.rw, rh: n.rh * j, id: n.id * 2 }, { rx: n.rx, ry: n.ry + n.rh * j, rw: n.rw, rh: n.rh * (1 - j), id: n.id * 2 + 1 }];
      }
      const drawCell = (x, y, r, id, a = 1) => {
        x += U.noise1(p.t * 0.25 + id * 1.3, 3) * r * 0.1;
        y += U.noise1(p.t * 0.25 + id * 2.1, 5) * r * 0.1;
        FX.glow(ctx, x, y, r * 1.5, CRIMSON, 0.12 * a);
        const g = ctx.createRadialGradient(x - r * 0.2, y - r * 0.25, 0, x, y, r);
        g.addColorStop(0, rgba([58, 22, 54], a)); g.addColorStop(0.75, rgba([40, 14, 40], a)); g.addColorStop(0.92, rgba([120, 34, 70], a)); g.addColorStop(1, rgba([200, 60, 90], a * 0.0));
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
        ctx.strokeStyle = rgba([190, 56, 92], 0.55 * a); ctx.lineWidth = Math.max(1, r * 0.04);
        ctx.beginPath(); ctx.arc(x, y, r * 0.9, 0, TAU); ctx.stroke();
        ctx.fillStyle = rgba([18, 6, 18], 0.85 * a);
        ctx.beginPath(); ctx.ellipse(x + r * 0.12, y + r * 0.08, r * 0.3, r * 0.25, id, 0, TAU); ctx.fill();
        FX.glow(ctx, x + r * 0.12, y + r * 0.08, r * 0.3, [140, 40, 80], 0.25 * a);
      };
      for (const n of nodes) {
        const P = cell(n.rx, n.ry, n.rw, n.rh, n.id);
        if (e <= 0) { drawCell(P.x, P.y, P.r * (1 + 0.04 * Math.sin(p.t + n.id)), n.id); continue; }
        const kids = split(n).map((c) => cell(c.rx, c.ry, c.rw, c.rh, c.id));
        // dividing: bridge between the two daughters early on
        if (e < 0.5) {
          ctx.fillStyle = rgba([40, 14, 40], 1 - e * 2);
          const mx = lerp(P.x, kids[0].x, e), my = lerp(P.y, kids[0].y, e), nx = lerp(P.x, kids[1].x, e), ny = lerp(P.y, kids[1].y, e);
          ctx.lineCap = 'round'; ctx.strokeStyle = rgba([40, 14, 40], 1 - e * 2); ctx.lineWidth = P.r * (1 - e * 1.6);
          ctx.beginPath(); ctx.moveTo(mx, my); ctx.lineTo(nx, ny); ctx.stroke();
        }
        kids.forEach((c, i) => drawCell(lerp(P.x, c.x, e), lerp(P.y, c.y, e), lerp(P.r * 0.78, c.r, e), n.id * 2 + i));
      }
      void unit;
    },
  },

  // one figure's small flame dimmed by another's shadowing hand
  gaslight_flame: {
    draw(ctx, w, h, p) {
      const { unit, cx, port } = frame(w, h);
      night(ctx, w, h, p, [6, 7, 18], [18, 16, 34], 16000);
      const gy = port ? h * 0.68 : h * 0.9;
      FX.glow(ctx, cx + unit * 0.1, gy - unit * 0.35, unit * 0.75, [90, 70, 140], 0.22);
      groundPlane(ctx, w, h, gy, [14, 12, 24]);
      const k = easeInOut((p.u - 0.1) / 0.6);
      // small figure holding a flame (left, facing right)
      const ah = unit * 0.46, ax = cx - unit * 0.16;
      const HOLD = { lean: 0, head: 0.35, armL: [0.35, -1.95], armR: [-0.35, 1.95], legL: [0.05, 0], legR: [-0.05, 0] };
      const A = probeFigure(ctx, ax, gy, ah, HOLD, { facing: -1 });
      const fxp = (A.handL[0] + A.handR[0]) / 2, fyp = Math.min(A.handL[1], A.handR[1]) - ah * 0.04;
      const fl = lerp(1, 0.4, k) * (1 + 0.06 * U.noise1(p.t * 2.2, 7));
      FX.glow(ctx, fxp, fyp, unit * 0.5 * fl, AMBER, 0.22 * fl);
      litFigure(ctx, ax, gy, ah, HOLD, {
        color: mix([58, 48, 66], [96, 68, 56], fl), facing: -1, rim: mix([170, 150, 220], [255, 200, 130], fl), rimA: 0.75,
        fill: AMBER, fillA: 0.12 + 0.2 * fl, light: [1, -0.6], halo: 0.25,
      });
      // tall shadowing figure (right) bringing a hand down over the flame
      const bh = unit * 0.64;
      const pose0 = { lean: 0.02, head: 0.1, armL: [0.12, 0.08], armR: [-0.3, -0.15], legL: [0.06, 0], legR: [-0.06, 0] };
      const pose1 = { lean: 0.3, head: 0.45, armL: [0.12, 0.08], armR: [-1.05, -0.3], legL: [0.06, 0], legR: [-0.06, 0] };
      const end = probeFigure(ctx, 0, gy, bh, pose1, {});
      const bx = fxp - end.handR[0] + unit * 0.045;
      // hand shadow over the flame
      // a dark presence, but never a void: cool rim from the sky glow, warm edge from the flame below
      const B = litFigure(ctx, bx, gy, bh, lerpPose(pose0, pose1, k), {
        color: [30, 26, 42], rim: mix([150, 140, 210], [255, 190, 120], 0.5 * fl), rimA: 0.7, fill: [120, 110, 170], fillA: 0.18,
        light: [-1, -0.5], halo: 0.22,
      });
      // the shadowing hand, palm down over the flame
      FX.hand(ctx, B.handR[0], B.handR[1], lerp(-2.9, -2.2, k), bh * 0.13, 'relaxed', { skin: [52, 44, 64], shadow: [30, 26, 40], outline: [84, 72, 104], back: true, mirror: true });
      // flame (teardrop), shrinking and swaying under the hand
      const fr = unit * 0.045 * fl, sway = U.noise1(p.t * 1.5, 2) * fr * 0.25;
      FX.glow(ctx, fxp, fyp - fr, fr * 3, GOLD, 0.6 * fl);
      const fg = ctx.createRadialGradient(fxp, fyp - fr * 0.4, 0, fxp, fyp - fr * 0.6, fr * 1.6);
      fg.addColorStop(0, rgba([255, 250, 225], 1)); fg.addColorStop(0.5, rgba(GOLD, 0.95)); fg.addColorStop(1, rgba(AMBER, 0.6));
      ctx.fillStyle = fg;
      ctx.beginPath(); ctx.moveTo(fxp + sway, fyp - fr * 2.4);
      ctx.quadraticCurveTo(fxp + fr * 0.95, fyp - fr * 0.4, fxp, fyp + fr * 0.15);
      ctx.quadraticCurveTo(fxp - fr * 0.95, fyp - fr * 0.4, fxp + sway, fyp - fr * 2.4); ctx.fill();
      // the shadow cast downward from the hand
      const hy = B.handR[1];
      const sg = ctx.createRadialGradient(B.handR[0], hy, 0, B.handR[0], hy + unit * 0.05, unit * 0.22);
      sg.addColorStop(0, `rgba(4,4,10,${0.55 * k})`); sg.addColorStop(1, 'rgba(4,4,10,0)');
      ctx.fillStyle = sg; ctx.fillRect(B.handR[0] - unit * 0.25, hy - unit * 0.2, unit * 0.5, unit * 0.45);
    },
  },

  // two silhouettes; cracks spread between them; a fist clenches the thread joining them
  break_control: {
    draw(ctx, w, h, p) {
      const { unit, cx, port } = frame(w, h);
      night(ctx, w, h, p, [8, 6, 18], [24, 14, 30], 16000);
      const gy = port ? h * 0.66 : h * 0.86;
      FX.glow(ctx, cx, gy - unit * 0.3, unit * 0.8, [100, 60, 120], 0.2);
      groundPlane(ctx, w, h, gy, [20, 14, 24], [150, 70, 100]);
      const k = easeInOut((p.u - 0.05) / 0.7);
      const fh = unit * 0.5;
      const lx = cx - unit * 0.33, rx = cx + unit * 0.33;
      // cracks spreading across the ground between them
      const crack = smooth((p.u - 0.15) / 0.65);
      ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      const paths = [
        jag(cx, gy + unit * 0.02, lx + unit * 0.06, gy + unit * 0.01, 8, unit * 0.02, 11),
        jag(cx, gy + unit * 0.02, rx - unit * 0.06, gy + unit * 0.012, 8, unit * 0.02, 12),
        jag(cx, gy + unit * 0.02, cx - unit * 0.1, h, 6, unit * 0.03, 13),
        jag(cx - unit * 0.05, gy + unit * 0.02, cx + unit * 0.12, h, 6, unit * 0.03, 14),
      ];
      paths.forEach((pts, i) => {
        const pk = smooth((crack - i * 0.12) / 0.7);
        ctx.strokeStyle = rgba(CRIMSON, 0.3); ctx.lineWidth = unit * 0.014; strokePartial(ctx, pts, pk);
        ctx.strokeStyle = rgba([6, 2, 8], 1); ctx.lineWidth = unit * 0.006; strokePartial(ctx, pts, pk);
      });
      ctx.restore();
      FX.glow(ctx, cx, gy + unit * 0.02, unit * 0.15, CRIMSON, 0.2 * crack);
      // figures reaching toward each other, holding the thread
      const lean = 0.06 * k;
      // both rim-lit from the glow between them (where the thread is seized)
      const LIT = { color: [72, 58, 84], rim: [236, 170, 200], rimA: 0.75, fill: [190, 140, 190], fillA: 0.22, halo: 0.25 };
      const L = litFigure(ctx, lx - unit * 0.02 * k, gy, fh, lerpPose('reach', { lean: -0.04, head: 0, armL: [0.1, 0.1], armR: [-1.0, -0.2], legL: [0.12, 0], legR: [-0.1, 0] }, k), Object.assign({ facing: -1, light: [1, -0.7] }, LIT));
      const Rr = litFigure(ctx, rx + unit * 0.02 * k, gy, fh, lerpPose('reach', { lean: -0.04, head: 0, armL: [0.1, 0.1], armR: [-1.0, -0.2], legL: [0.12, 0], legR: [-0.1, 0] }, k), Object.assign({ facing: 1, light: [-1, -0.7] }, LIT));
      void lean;
      // the thread, seized in the middle by a fist and pulled up into a V
      const fy = lerp(gy - fh * 0.62, port ? h * 0.3 : h * 0.3, k);
      const fxp = cx;
      ctx.save(); ctx.lineCap = 'round';
      const thread = () => { ctx.beginPath(); ctx.moveTo(L.handR[0], L.handR[1]); ctx.quadraticCurveTo(lerp(L.handR[0], fxp, 0.6), lerp(L.handR[1], fy, 0.4), fxp, fy); ctx.quadraticCurveTo(lerp(Rr.handR[0], fxp, 0.6), lerp(Rr.handR[1], fy, 0.4), Rr.handR[0], Rr.handR[1]); };
      thread(); ctx.strokeStyle = rgba(GOLD, 0.25 * (1 - k * 0.6)); ctx.lineWidth = unit * 0.014; ctx.stroke();
      thread(); ctx.strokeStyle = rgba(mix(GOLD, CRIMSON, k)); ctx.lineWidth = unit * 0.004; ctx.stroke();
      ctx.restore();
      // forearm from above
      const hs = unit * 0.085;
      const wy = fy - hs * 1.05;
      const fa = ctx.createLinearGradient(fxp - hs * 0.5, 0, fxp + hs * 0.55, 0);
      fa.addColorStop(0, rgba([110, 82, 92])); fa.addColorStop(1, rgba([62, 46, 62]));
      ctx.fillStyle = fa;
      ctx.beginPath(); ctx.moveTo(fxp - hs * 0.42, wy + hs * 0.1); ctx.lineTo(fxp - hs * 0.5, -10); ctx.lineTo(fxp + hs * 0.55, -10); ctx.lineTo(fxp + hs * 0.38, wy + hs * 0.1); ctx.fill();
      const pose = {
        curl: [0, 1, 2, 3].map((i) => lerp(0.55, 1, k)), spread: lerp(0.03, 0, k), thumb: lerp(0.3, 0.15, k), thumbCurl: lerp(0.5, 0.9, k),
      };
      R.drawHand(ctx, fxp, wy, Math.PI, hs, pose, { skin: [160, 116, 100], shadow: [96, 60, 60], outline: [120, 84, 80], back: true });
      FX.glow(ctx, fxp, fy, unit * 0.12, CRIMSON, 0.15 * k);
    },
  },

  // a spiral abyss; a small figure of light at the edge looks in, unflinching
  abyss_stare: {
    draw(ctx, w, h, p) {
      const { unit, cx, port } = frame(w, h);
      night(ctx, w, h, p, [5, 6, 16], [16, 12, 30], 14000);
      const gy = port ? h * 0.5 : h * 0.42;
      groundPlane(ctx, w, h, gy, [18, 14, 28], [120, 90, 160]);
      const ax = cx + (port ? unit * 0.08 : unit * 0.12), ay = port ? h * 0.64 : h * 0.68;
      const RX = port ? unit * 0.4 : unit * 0.52, RY = RX * (port ? 0.45 : 0.36);
      // the pit
      ctx.save();
      ctx.beginPath(); ctx.ellipse(ax, ay, RX, RY, 0, 0, TAU); ctx.clip();
      ctx.save(); ctx.translate(ax, ay); ctx.scale(1, RY / RX);
      const pg = ctx.createRadialGradient(0, 0, 0, 0, 0, RX);
      pg.addColorStop(0, '#000000'); pg.addColorStop(0.5, rgba([30, 14, 40])); pg.addColorStop(1, rgba([70, 36, 86]));
      ctx.fillStyle = pg; ctx.fillRect(-RX, -RX, RX * 2, RX * 2);
      // spiral arms turning slowly inward
      ctx.lineCap = 'round';
      const rot = p.t * 0.18;
      for (let a = 0; a < 5; a++) {
        for (let s = 0; s < 18; s++) {
          const q0 = s / 18, q1 = (s + 1) / 18;
          const r0 = RX * (1 - q0), r1 = RX * (1 - q1);
          const t0 = a * TAU / 5 + rot + q0 * 4.2, t1 = a * TAU / 5 + rot + q1 * 4.2;
          ctx.strokeStyle = rgba(mix([130, 80, 150], [20, 8, 26], q0), 0.55 * (1 - q0 * 0.8));
          ctx.lineWidth = RX * 0.11 * (1 - q0 * 0.85);
          ctx.beginPath(); ctx.moveTo(Math.cos(t0) * r0, Math.sin(t0) * r0); ctx.lineTo(Math.cos(t1) * r1, Math.sin(t1) * r1); ctx.stroke();
        }
      }
      const core = ctx.createRadialGradient(0, 0, 0, 0, 0, RX * 0.45);
      core.addColorStop(0, 'rgba(0,0,0,1)'); core.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = core; ctx.fillRect(-RX, -RX, RX * 2, RX * 2);
      ctx.restore();
      // the figure's light falling into the pit
      const steady = smooth(p.u / 0.8);
      const fx0 = ax - RX * 0.98;
      FX.glow(ctx, fx0 + RX * 0.35, ay - RY * 0.1, RX * 0.7, GOLD, 0.08 + 0.14 * steady);
      ctx.restore();
      ctx.strokeStyle = rgba([150, 120, 190], 0.4); ctx.lineWidth = unit * 0.004;
      ctx.beginPath(); ctx.ellipse(ax, ay, RX, RY, 0, Math.PI * 1.02, Math.PI * 1.98); ctx.stroke();
      // the figure at the rim, facing the pit, head tilted down to look in
      const fh = unit * 0.24, fy = ay - RY * 0.18;
      FX.glow(ctx, fx0, fy - fh * 0.5, fh * 1.4, GOLD, 0.2 + 0.15 * steady);
      FX.figure(ctx, fx0, fy, fh, { lean: 0, head: 0.45, armL: [0.1, 0.06], armR: [-0.1, -0.06], legL: [0.06, 0], legR: [-0.06, 0] }, { color: mix([230, 200, 150], [255, 245, 220], steady), facing: -1, glow: GOLD, glowA: 0.25 + 0.15 * steady + 0.03 * Math.sin(p.t) });
      // gaze line
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const gz = ctx.createLinearGradient(fx0, fy - fh * 0.9, ax, ay);
      gz.addColorStop(0, rgba(GOLD, 0.18 * steady)); gz.addColorStop(1, rgba(GOLD, 0));
      ctx.fillStyle = gz; ctx.beginPath(); ctx.moveTo(fx0 + fh * 0.05, fy - fh * 0.9); ctx.lineTo(ax - RX * 0.1, ay - RY * 0.25); ctx.lineTo(ax - RX * 0.2, ay + RY * 0.3); ctx.closePath(); ctx.fill();
      ctx.restore();
    },
  },

  // a crack fills with gold light and seals
  wound_heal_gold: {
    draw(ctx, w, h, p) {
      const { unit, cx, cy, port } = frame(w, h);
      night(ctx, w, h, p, [7, 8, 20], [20, 18, 40], 14000);
      const bw = unit * 0.66, bh = unit * 0.36;
      const rimY = (port ? cy - unit * 0.05 : cy - unit * 0.12), botY = rimY + bh;
      const ty = botY + unit * 0.02;
      // table surface
      const tg = ctx.createLinearGradient(0, ty, 0, h);
      tg.addColorStop(0, rgba([30, 26, 46])); tg.addColorStop(1, rgba([10, 10, 20]));
      ctx.fillStyle = tg; ctx.fillRect(0, ty, w, h - ty);
      const heal = smooth((p.u - 0.1) / 0.6), seal = smooth((p.u - 0.65) / 0.2);
      FX.glow(ctx, cx, rimY + bh * 0.5, unit * 0.6, AMBER, 0.06 + 0.12 * heal);
      ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.beginPath(); ctx.ellipse(cx, ty, bw * 0.38, unit * 0.025, 0, 0, TAU); ctx.fill();
      // bowl body
      const body = () => {
        ctx.beginPath(); ctx.moveTo(cx - bw / 2, rimY);
        ctx.bezierCurveTo(cx - bw * 0.5, rimY + bh * 0.75, cx - bw * 0.25, botY, cx - bw * 0.16, botY);
        ctx.lineTo(cx + bw * 0.16, botY);
        ctx.bezierCurveTo(cx + bw * 0.25, botY, cx + bw * 0.5, rimY + bh * 0.75, cx + bw / 2, rimY);
        ctx.ellipse(cx, rimY, bw / 2, bw * 0.09, 0, 0, Math.PI, false);
        ctx.closePath();
      };
      const bg = ctx.createLinearGradient(cx - bw / 2, 0, cx + bw / 2, 0);
      bg.addColorStop(0, rgba([30, 30, 50])); bg.addColorStop(0.35, rgba([84, 80, 112])); bg.addColorStop(1, rgba([26, 24, 42]));
      body(); ctx.fillStyle = bg; ctx.fill();
      // inside of rim
      ctx.fillStyle = rgba([16, 14, 28]); ctx.beginPath(); ctx.ellipse(cx, rimY, bw / 2, bw * 0.09, 0, 0, TAU); ctx.fill();
      ctx.strokeStyle = rgba([150, 145, 185], 0.55); ctx.lineWidth = unit * 0.005; ctx.stroke();
      // the crack
      const pts = jag(cx - bw * 0.06, rimY + bw * 0.085, cx + bw * 0.05, botY - bh * 0.05, 7, unit * 0.03, 21);
      const br = jag(pts[3][0], pts[3][1], pts[3][0] + bw * 0.16, pts[3][1] + bh * 0.25, 3, unit * 0.015, 22);
      ctx.save(); body(); ctx.clip(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      const wound = 1 - seal;
      ctx.strokeStyle = rgba(CRIMSON, 0.3 * wound); ctx.lineWidth = unit * 0.03; strokePoly(ctx, pts); strokePoly(ctx, br);
      ctx.strokeStyle = rgba([10, 4, 10], wound); ctx.lineWidth = unit * 0.012; strokePoly(ctx, pts);
      ctx.lineWidth = unit * 0.007; strokePoly(ctx, br);
      // gold flowing in along the crack
      const gw = lerp(unit * 0.012, unit * 0.007, seal);
      ctx.strokeStyle = rgba(AMBER, 0.45); ctx.lineWidth = gw * 2.6; strokePartial(ctx, pts, heal); strokePartial(ctx, br, smooth((heal - 0.4) / 0.6));
      ctx.strokeStyle = rgba([255, 236, 180], 1); ctx.lineWidth = gw; strokePartial(ctx, pts, heal);
      ctx.lineWidth = gw * 0.7; strokePartial(ctx, br, smooth((heal - 0.4) / 0.6));
      ctx.restore();
      // gold front glow
      const tot = polyLen(pts) * heal;
      let acc = 0, gx = pts[0][0], gyy = pts[0][1];
      for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); if (acc + d >= tot) { const f = (tot - acc) / d; gx = lerp(pts[i - 1][0], pts[i][0], f); gyy = lerp(pts[i - 1][1], pts[i][1], f); break; } acc += d; gx = pts[i][0]; gyy = pts[i][1]; }
      if (heal > 0 && seal < 1) FX.glow(ctx, gx, gyy, unit * 0.08, GOLD, 0.6 * (1 - seal));
      if (seal > 0) FX.glow(ctx, cx, rimY + bh * 0.5, unit * 0.3, GOLD, (0.12 + 0.04 * Math.sin(p.t * 0.9)) * seal);
    },
  },

  // heavy chains break and fall away into light
  chains_fall: {
    draw(ctx, w, h, p) {
      const { unit, cx, cy, port } = frame(w, h);
      night(ctx, w, h, p, [8, 8, 20], [22, 18, 40], 14000);
      const brk = 0.35;
      const free = smooth((p.u - brk) / 0.4);
      const fy = port ? cy + unit * 0.25 : h * 0.95;
      FX.glow(ctx, cx, fy - unit * 0.35, unit * (0.5 + 0.4 * free), GOLD, 0.22 + 0.25 * free);
      // figure behind the chains, head lifting as they fall
      const pose = lerpPose({ lean: 0.05, head: 0.55, armL: [0.15, 0.1], armR: [-0.15, -0.1], legL: [0.04, 0], legR: [-0.04, 0] }, { lean: -0.03, head: -0.2, armL: [0.55, 0.2], armR: [-0.55, -0.2], legL: [0.05, 0], legR: [-0.05, 0] }, free);
      litFigure(ctx, cx, fy, unit * 0.62, pose, {
        color: mix([72, 62, 84], [104, 82, 70], free), rim: GOLD, rimA: 0.6 + 0.3 * free, fill: [255, 214, 160], fillA: 0.15 + 0.2 * free,
        light: [0.3, -1], halo: 0.25,
      });
      FX.glow(ctx, cx, fy - unit * 0.5, unit * 0.31, GOLD, 0.1 + 0.2 * free);
      // chains: X across the frame
      const cyc = port ? cy - unit * 0.05 : cy;
      const ext = Math.max(w, h);
      const chains = [[-0.85, 1], [0.85, 1]].map(([s]) => {
        const dir = [Math.cos(s), Math.sin(s)];
        return { dir, a: [cx - dir[0] * ext, cyc - dir[1] * ext], b: [cx + dir[0] * ext, cyc + dir[1] * ext] };
      });
      const Ls = unit * 0.075;
      const hot = smooth((p.u - 0.05) / (brk - 0.05));
      const fallK = clamp((p.u - brk) / 0.5);
      chains.forEach((c, ci) => {
        const n = Math.ceil(ext * 2 / Ls);
        for (const side of [-1, 1]) {
          // each half falls, tilting about its own centre, and dissolves
          const drop = fallK * fallK * unit * 1.1, rot = side * (ci ? -1 : 1) * 0.35 * fallK;
          const fade = 1 - smooth(fallK * 1.3);
          if (fade <= 0) continue;
          const hc = [cx + c.dir[0] * side * ext * 0.5, cyc + c.dir[1] * side * ext * 0.5];
          ctx.save();
          ctx.translate(hc[0] + side * c.dir[0] * fallK * unit * 0.15, hc[1] + drop); ctx.rotate(rot); ctx.translate(-hc[0], -hc[1]);
          ctx.globalAlpha = fade;
          for (let i = 0; i < n / 2; i++) {
            const d = (i + 0.5 + (ci ? 0.5 : 0)) * Ls * 0.9 * side;
            const x = cx + c.dir[0] * d, y = cyc + c.dir[1] * d;
            if (x < -Ls || x > w + Ls || y < -Ls || y > h + Ls) continue;
            const ang = Math.atan2(c.dir[1], c.dir[0]);
            const heat = (1 - fade * 0 ) * hot * Math.exp(-Math.abs(d) / (unit * 0.12)) * (1 - free);
            const steel = mix([78, 80, 98], [255, 170, 90], heat);
            ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
            ctx.lineCap = 'round';
            if ((i + ci) % 2 === 0) {
              ctx.strokeStyle = rgba(shade(steel, -0.5)); ctx.lineWidth = unit * 0.022;
              ctx.beginPath(); ctx.ellipse(0, 0, Ls * 0.62, Ls * 0.34, 0, 0, TAU); ctx.stroke();
              ctx.strokeStyle = rgba(steel); ctx.lineWidth = unit * 0.014; ctx.stroke();
              ctx.strokeStyle = rgba(shade(steel, 0.45), 0.7); ctx.lineWidth = unit * 0.004;
              ctx.beginPath(); ctx.ellipse(0, 0, Ls * 0.62, Ls * 0.34, 0, Math.PI * 1.1, Math.PI * 1.6); ctx.stroke();
            } else {
              ctx.strokeStyle = rgba(shade(steel, -0.5)); ctx.lineWidth = unit * 0.024;
              ctx.beginPath(); ctx.moveTo(-Ls * 0.55, 0); ctx.lineTo(Ls * 0.55, 0); ctx.stroke();
              ctx.strokeStyle = rgba(shade(steel, 0.1)); ctx.lineWidth = unit * 0.014; ctx.stroke();
            }
            ctx.restore();
            if (heat > 0.05) FX.glow(ctx, x, y, Ls, AMBER, 0.3 * heat);
          }
          ctx.restore();
        }
      });
      // the break: a flash of gold, then motes rising out of the falling pieces
      FX.glow(ctx, cx, cyc, unit * 0.3, [255, 230, 180], 0.6 * U.pulse(p.u, brk - 0.04, brk + 0.2, 0.08));
      if (p.u > brk) {
        for (let i = 0; i < 40; i++) {
          const ci = i % 2, side = (i >> 1) % 2 ? 1 : -1;
          const d = (0.1 + U.hash2(i, 1) * 0.9) * ext * 0.5 * side;
          const x0 = cx + Math.cos(ci ? 0.85 : -0.85) * d, y0 = cyc + Math.sin(ci ? 0.85 : -0.85) * d;
          const life = clamp((p.u - brk - U.hash2(i, 2) * 0.3) / 0.35);
          if (life <= 0 || life >= 1) continue;
          const x = x0 + Math.sin(i + p.t * 0.5) * unit * 0.02, y = y0 + fallK * fallK * unit * 0.6 - life * unit * 0.15;
          FX.glow(ctx, x, y, unit * 0.02, GOLD, 0.6 * Math.sin(Math.PI * life));
        }
      }
    },
  },

  // a hand passes a heavy dark stone into a hand of light, which dips with the weight
  stone_carried: {
    draw(ctx, w, h, p) {
      const { unit, cx, cy, port } = frame(w, h);
      night(ctx, w, h, p, [7, 8, 20], [20, 20, 42]);
      const s = unit * 0.36, y = port ? cy + unit * 0.12 : cy + unit * 0.16;
      const reach = easeInOut(p.u / 0.3), give = easeInOut((p.u - 0.3) / 0.2), back = easeInOut((p.u - 0.6) / 0.25);
      FX.glow(ctx, cx, y - unit * 0.1, unit * 0.6, [80, 70, 140], 0.14);
      // light hand: dips under the weight with a damped bounce, settles lower
      const tl = clamp((p.u - 0.48) / 0.4);
      const dip = tl > 0 ? unit * 0.07 * (1 - Math.exp(-tl * 6) * Math.cos(tl * 14)) : 0;
      const lx = cx + unit * 0.3, ly = y + dip;
      // hand of light: open, then cups around the stone once it lands
      const land = smooth((p.u - 0.47) / 0.2);
      const restR = sideHand(ctx, lx, ly, s, -1, { light: true, curl: lerp(0.3, 0.78, land), thumb: lerp(0.2, 0.6, land), tilt: -0.12 * clamp(dip / (unit * 0.07)), deferFront: true });
      // human hand: palm up, fingers around the stone, comes over and tips it into the light
      const hx = cx - unit * 0.48 + reach * unit * 0.1 - back * unit * 0.08;
      const hy = y - reach * unit * 0.1 + give * unit * 0.02 + back * unit * 0.05;
      const restL = sideHand(ctx, hx, hy, s, 1, { curl: lerp(0.75, 0.3, give), thumb: lerp(0.6, 0.25, give), tilt: -0.05 + 0.2 * give - 0.15 * back, sleeve: [40, 44, 70], deferFront: true });
      // stone: rests in the human palm, arcs over, then sits in the cupped palm of light
      const r = unit * 0.062;
      const sx = lerp(restL[0], restR[0], give), sy = lerp(restL[1], restR[1], give) - r * 0.8 - Math.sin(Math.PI * give) * unit * 0.05;
      const rot = give * 0.6;
      ctx.save(); ctx.translate(sx, sy); ctx.rotate(rot);
      ctx.beginPath();
      for (let i = 0; i < 9; i++) {
        const a = i / 9 * TAU, rr = r * (0.88 + 0.18 * U.hash2(i, 31)) * (i % 2 ? 1 : 0.97);
        const px = Math.cos(a) * rr * 1.15, py = Math.sin(a) * rr * 0.86;
        i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
      }
      ctx.closePath();
      const sg = ctx.createRadialGradient(-r * 0.35, -r * 0.4, 0, 0, 0, r * 1.2);
      sg.addColorStop(0, rgba([92, 86, 104])); sg.addColorStop(0.6, rgba([44, 40, 54])); sg.addColorStop(1, rgba([18, 16, 24]));
      ctx.fillStyle = sg; ctx.fill();
      // soft edge light on the upper side (no outline)
      ctx.save(); ctx.clip();
      const eg = ctx.createRadialGradient(r * 0.2, r * 0.5, r * 0.6, 0, 0, r * 1.3);
      eg.addColorStop(0, 'rgba(0,0,0,0)'); eg.addColorStop(1, rgba(mix([150, 140, 170], CYAN, give), 0.45 + 0.2 * give));
      ctx.fillStyle = eg; ctx.fillRect(-r * 1.5, -r * 1.5, r * 3, r * 3); ctx.restore();
      ctx.restore();
      // near fingers and thumbs wrap in front of the stone
      restL.front(); restR.front();
      FX.glow(ctx, restR[0], restR[1], unit * 0.2, CYAN, 0.1 + 0.1 * smooth((p.u - 0.5) / 0.3));
    },
  },
};
