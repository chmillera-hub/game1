'use strict';
// Head and face drawing. Coordinates are in "head units": head height ~= 1,
// origin at the head centre, y pointing down. Features live on a simple 3D
// head model and are projected through yaw/pitch so turns foreshorten.

const { clamp, lerp, col, shade, mix, rgbStr } = require('./util');

const YAW_MAX = 0.55;   // radians at yaw = 1
const PITCH_MAX = 0.32; // radians at pitch = 1

// Depth of the face surface at horizontal offset x (a rounded cylinder).
function zf(x) {
  const k = clamp(1 - (x / 0.47) * (x / 0.47), 0, 1);
  return 0.4 * Math.sqrt(k);
}

function rotation(yaw, pitch) {
  const ay = yaw * YAW_MAX, ap = pitch * PITCH_MAX;
  const R = { cy: Math.cos(ay), sy: Math.sin(ay), cp: Math.cos(ap), sp: Math.sin(ap), dy: 0 };
  // Pitch pivots around the top of the neck, not the head centre.
  const piv = projRaw([0, 0.45, -0.1], R);
  R.dy = 0.45 - piv[1];
  return R;
}
function projRaw(p, R) {
  const x1 = p[0] * R.cy + p[2] * R.sy;
  const z1 = -p[0] * R.sy + p[2] * R.cy;
  const y1 = p[1] * R.cp + z1 * R.sp;
  const z2 = -p[1] * R.sp + z1 * R.cp;
  return [x1, y1, z2];
}
function proj(p, R) { const q = projRaw(p, R); q[1] += R.dy; return q; }
// Project a point lying on the face surface (depth from zf + offset).
function pf(x, y, R, dz = 0) { return proj([x, y, zf(x) + dz], R); }

// ---------------------------------------------------------------- head shape
function headOutline(A, P, R) {
  const jw = A.jaw || 0;          // wider, squarer jaw for some characters
  const chinDrop = (P.jawOpen || 0) * 0.045;
  const hw = A.headW || 1;
  const pts = [];
  // cranium arc (silhouette of a sphere does not change with yaw)
  const ccx = 0, ccy = -0.12, rx = 0.445 * hw, ry = 0.45;
  const pitchLift = R.sp * 0.05;  // nodding down shows more skull
  const sideFace = (s) => {
    // [back-of-head silhouette x, face contour 3D point]
    return [
      [0.432 * hw, [s * 0.43 * hw, 0.02, 0.08]],
      [0.418 * hw, [s * (0.415 + jw * 0.02) * hw, 0.18, 0.12]],
      [0.37 * hw, [s * (0.35 + jw * 0.05) * hw, 0.33 + chinDrop * 0.6, 0.13]],
      [null, [s * (0.185 + jw * 0.05) * hw, 0.468 + chinDrop, 0.29]],
    ];
  };
  // right side, top to bottom
  for (let a = -Math.PI / 2; a <= 0.22; a += 0.12) {
    pts.push([ccx + Math.cos(a) * rx, ccy + Math.sin(a) * ry + pitchLift * (1 - Math.sin(a + Math.PI / 2))]);
  }
  for (const [back, p3] of sideFace(1)) {
    const q = proj(p3, R);
    let x = q[0];
    if (back !== null) x = Math.max(x, back * lerp(1, 0.97, Math.abs(R.sy)));
    pts.push([x, q[1]]);
  }
  const chin = proj([0, 0.5 + chinDrop, 0.33], R);
  pts.push([chin[0], chin[1]]);
  const left = sideFace(-1).reverse();
  for (const [back, p3] of left) {
    const q = proj(p3, R);
    let x = q[0];
    if (back !== null) x = Math.min(x, -back * lerp(1, 0.97, Math.abs(R.sy)));
    pts.push([x, q[1]]);
  }
  for (let a = Math.PI - 0.22; a <= Math.PI * 1.5 + 0.001; a += 0.12) {
    pts.push([ccx + Math.cos(a) * rx, ccy + Math.sin(a) * ry + pitchLift * (1 - Math.sin(a - Math.PI / 2 + Math.PI))]);
  }
  return pts;
}

// Closed Catmull-Rom spline through points.
function smoothPath(ctx, pts, closed = true, tension = 0.5) {
  const n = pts.length;
  const get = (i) => (closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))]);
  ctx.moveTo(pts[0][0], pts[0][1]);
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    const t = tension / 3;
    ctx.bezierCurveTo(
      p1[0] + (p2[0] - p0[0]) * t, p1[1] + (p2[1] - p0[1]) * t,
      p2[0] - (p3[0] - p1[0]) * t, p2[1] - (p3[1] - p1[1]) * t,
      p2[0], p2[1]);
  }
  if (closed) ctx.closePath();
}

// ---------------------------------------------------------------- eyes
function eyeShape(A, P, R, s) {
  const sz = A.eyeSize || 1;
  const cx = s * 0.182 * (A.eyeSpacing || 1);
  const cy = 0.05;
  const w = 0.112 * sz;
  const hT = 0.079 * sz * (A.eyeH || 1);
  const hB = 0.05 * sz * (A.eyeH || 1);
  const tilt = A.eyeTilt ?? 0.012;
  const sadDroop = Math.max(0, P.browIn) * 0.008;     // outer corners sink when sad
  const side = s < 0 ? 'L' : 'R';
  let close = clamp((P.blink || 0) + (P.lid || 0) + (P['lid' + side] || 0) + Math.max(0, P.pitch) * 0.18 - (P.wide || 0) * 0.8, -0.6, 1);
  const squint = clamp((P.squint || 0) + Math.max(0, P.smile) * 0.22 + (P['squint' + side] || 0), 0, 1);
  const wideUp = Math.max(0, -close) * hT * 0.95;    // eyes widened beyond rest
  close = Math.max(0, close);
  const yInner = cy + 0.004, yOuter = cy - tilt + sadDroop;
  const ix = cx - s * w, ox = cx + s * w;
  // top lid controls, open and closed
  const tOpen1 = [cx - s * w * 0.35, cy - hT * 1.32 - wideUp];
  const tOpen2 = [cx + s * w * 0.38, cy - hT * 1.12 - wideUp];
  const closedY = cy + hB * 0.62;
  const t1 = [tOpen1[0], lerp(tOpen1[1], closedY + 0.004, close)];
  const t2 = [tOpen2[0], lerp(tOpen2[1], closedY, close)];
  // bottom lid controls; squint pushes them up
  const bBase1 = cy + hB * 1.28, bBase2 = cy + hB * 1.18;
  const bUp = cy - hT * 0.05;
  const b1 = [cx + s * w * 0.32, lerp(bBase1, bUp, squint * 0.55)];
  const b2 = [cx - s * w * 0.4, lerp(bBase2, bUp, squint * 0.55)];
  const zO = -0.015;
  const P3 = (x, y) => pf(x, y, R, zO);
  return {
    s, cx, cy, w, hT, hB, close, squint,
    inner: P3(ix, yInner), outer: P3(ox, yOuter),
    t1: P3(t1[0], t1[1]), t2: P3(t2[0], t2[1]),
    b1: P3(b1[0], b1[1]), b2: P3(b2[0], b2[1]),
    crease1: P3(tOpen1[0], lerp(tOpen1[1] - 0.034, closedY - 0.02, close * 0.6) - wideUp * 0.3),
    crease2: P3(tOpen2[0] + s * 0.01, lerp(tOpen2[1] - 0.028, closedY - 0.02, close * 0.6) - wideUp * 0.3),
    center: P3(cx, cy),
    fore: Math.abs(P3(ox, yOuter)[0] - P3(ix, yInner)[0]) / (2 * w),
  };
}
function eyeOpeningPath(ctx, E) {
  ctx.beginPath();
  ctx.moveTo(E.inner[0], E.inner[1]);
  ctx.bezierCurveTo(E.t1[0], E.t1[1], E.t2[0], E.t2[1], E.outer[0], E.outer[1]);
  ctx.bezierCurveTo(E.b1[0], E.b1[1], E.b2[0], E.b2[1], E.inner[0], E.inner[1]);
  ctx.closePath();
}
function drawEye(ctx, A, P, R, s) {
  const E = eyeShape(A, P, R, s);
  const skinD = shade(A.skin, -0.28);
  // socket shading above the eye
  ctx.save();
  const g = ctx.createRadialGradient(E.center[0], E.center[1] - 0.03, 0.01, E.center[0], E.center[1] - 0.02, 0.15);
  g.addColorStop(0, rgbStr(skinD, 0.12 + (A.tired || 0) * 0.1));
  g.addColorStop(1, rgbStr(skinD, 0));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.ellipse(E.center[0], E.center[1] - 0.02, 0.15 * E.fore + 0.02, 0.1, 0, 0, Math.PI * 2); ctx.fill();
  ctx.restore();

  // under-eye softness (tired / crying)
  const bags = clamp((A.tired || 0) + (P.tired || 0) * 0.6 + (P.wet || 0) * 0.35);
  if (bags > 0.02) {
    ctx.save();
    ctx.strokeStyle = rgbStr(shade(A.skin, -0.3), 0.35 * bags);
    ctx.lineWidth = 0.008; ctx.lineCap = 'round';
    ctx.beginPath();
    const y0 = Math.max(E.b1[1], E.b2[1]) + 0.022;
    ctx.moveTo(lerp(E.inner[0], E.center[0], 0.3), y0 - 0.004);
    ctx.quadraticCurveTo(E.center[0], y0 + 0.012, lerp(E.outer[0], E.center[0], 0.2), y0 - 0.008);
    ctx.stroke();
    if ((P.wet || 0) > 0.2) { // reddened rims when crying
      ctx.strokeStyle = rgbStr([200, 90, 90], 0.25 * P.wet);
      ctx.lineWidth = 0.012;
      ctx.beginPath(); ctx.moveTo(E.inner[0], E.inner[1]);
      ctx.bezierCurveTo(E.b2[0], E.b2[1] + 0.006, E.b1[0], E.b1[1] + 0.006, E.outer[0], E.outer[1]);
      ctx.stroke();
    }
    ctx.restore();
  }

  const openAmt = 1 - E.close;
  if (openAmt > 0.04) {
    ctx.save();
    eyeOpeningPath(ctx, E);
    ctx.fillStyle = col(A.sclera || '#f3eee8');
    ctx.fill();
    ctx.clip();
    // iris
    const gx = clamp(P.gazeX || 0, -1.2, 1.2), gy = clamp(P.gazeY || 0, -1, 1);
    const ip = pf(E.cx + gx * E.w * 0.46, E.cy + gy * E.hT * 0.5 + 0.006, R, 0.0);
    const ir = 0.061 * (A.eyeSize || 1) * (A.irisSize || 1);
    const irx = ir * Math.max(0.55, E.fore), iry = ir;
    const ig = ctx.createRadialGradient(ip[0], ip[1] + iry * 0.3, ir * 0.1, ip[0], ip[1], ir);
    ig.addColorStop(0, rgbStr(shade(A.eyeColor, 0.35)));
    ig.addColorStop(0.65, col(A.eyeColor));
    ig.addColorStop(1, rgbStr(shade(A.eyeColor, -0.45)));
    ctx.fillStyle = ig;
    ctx.beginPath(); ctx.ellipse(ip[0], ip[1], irx, iry, 0, 0, Math.PI * 2); ctx.fill();
    const pr = ir * (0.44 + (P.pupil || 0) * 0.14);
    ctx.fillStyle = '#120b09';
    ctx.beginPath(); ctx.ellipse(ip[0], ip[1], pr * Math.max(0.55, E.fore), pr, 0, 0, Math.PI * 2); ctx.fill();
    // lid shadow cast on the eyeball
    const top = Math.min(E.t1[1], E.t2[1]);
    const sh = ctx.createLinearGradient(0, top, 0, top + 0.05);
    sh.addColorStop(0, 'rgba(70,35,25,0.45)');
    sh.addColorStop(1, 'rgba(70,35,25,0)');
    ctx.fillStyle = sh;
    ctx.fillRect(E.center[0] - 0.2, top - 0.02, 0.4, 0.09);
    // catchlights (life!)
    const wet = clamp(P.wet || 0);
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.beginPath(); ctx.ellipse(ip[0] - irx * 0.32, ip[1] - iry * 0.38, ir * (0.24 + wet * 0.06), ir * (0.2 + wet * 0.05), -0.4, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = `rgba(255,255,255,${0.55 + wet * 0.3})`;
    ctx.beginPath(); ctx.arc(ip[0] + irx * 0.38, ip[1] + iry * 0.36, ir * 0.09, 0, Math.PI * 2); ctx.fill();
    // welling tears: a glossy meniscus along the lower lid
    if (wet > 0.05) {
      ctx.strokeStyle = `rgba(255,255,255,${0.55 * wet})`;
      ctx.lineWidth = 0.006 + wet * 0.006;
      ctx.beginPath();
      ctx.moveTo(lerp(E.inner[0], E.outer[0], 0.12), lerp(E.inner[1], E.outer[1], 0.12));
      ctx.bezierCurveTo(E.b2[0], E.b2[1] - 0.008, E.b1[0], E.b1[1] - 0.008, lerp(E.outer[0], E.inner[0], 0.08), lerp(E.outer[1], E.inner[1], 0.08));
      ctx.stroke();
      const wg = ctx.createLinearGradient(0, E.b1[1] - 0.03, 0, E.b1[1] + 0.01);
      wg.addColorStop(0, 'rgba(190,215,235,0)');
      wg.addColorStop(1, `rgba(190,215,235,${0.35 * wet})`);
      ctx.fillStyle = wg;
      ctx.fillRect(E.center[0] - 0.15, E.b1[1] - 0.03, 0.3, 0.05);
    }
    ctx.restore();
  }

  // lid crease
  const lash = col(A.lashColor || '#1c1210');
  ctx.save();
  ctx.lineCap = 'round';
  ctx.strokeStyle = rgbStr(shade(A.skin, -0.32), 0.55 * (1 - E.close * 0.5));
  ctx.lineWidth = 0.0065;
  ctx.beginPath();
  const ci = [lerp(E.inner[0], E.t1[0], 0.35), lerp(E.inner[1], E.t1[1], 0.35) - 0.012];
  ctx.moveTo(ci[0], ci[1]);
  ctx.bezierCurveTo(E.crease1[0], E.crease1[1], E.crease2[0], E.crease2[1], E.outer[0] + E.s * 0.012, E.outer[1] - 0.022);
  ctx.stroke();

  // upper lash line (thicker toward the outer corner)
  const lw = A.sex === 'f' ? 0.016 : 0.011;
  ctx.strokeStyle = lash;
  ctx.lineWidth = lw;
  ctx.beginPath();
  ctx.moveTo(E.inner[0], E.inner[1]);
  ctx.bezierCurveTo(E.t1[0], E.t1[1], E.t2[0], E.t2[1], E.outer[0], E.outer[1]);
  ctx.stroke();
  ctx.lineWidth = lw * 1.35;
  ctx.beginPath();
  const mid = bez(E.inner, E.t1, E.t2, E.outer, 0.55);
  ctx.moveTo(mid[0], mid[1]);
  const m2 = bez(E.inner, E.t1, E.t2, E.outer, 0.82);
  ctx.quadraticCurveTo(m2[0], m2[1], E.outer[0], E.outer[1]);
  ctx.stroke();
  if (A.sex === 'f') { // little flick at the outer corner
    ctx.lineWidth = lw * 0.7;
    ctx.beginPath();
    ctx.moveTo(E.outer[0], E.outer[1]);
    ctx.lineTo(E.outer[0] + E.s * 0.013 * E.fore, E.outer[1] - 0.009 + E.close * 0.008);
    ctx.stroke();
  }
  // lower lid line
  ctx.strokeStyle = rgbStr(shade(A.skin, -0.45), 0.6);
  ctx.lineWidth = 0.0055;
  ctx.beginPath();
  const lo = bez(E.outer, E.b1, E.b2, E.inner, 0.0);
  ctx.moveTo(lo[0], lo[1]);
  ctx.bezierCurveTo(E.b1[0], E.b1[1], E.b2[0], E.b2[1], lerp(E.inner[0], E.b2[0], 0.3), lerp(E.inner[1], E.b2[1], 0.3));
  ctx.stroke();
  ctx.restore();
  return E;
}
function bez(p0, p1, p2, p3, t) {
  const u = 1 - t;
  return [
    u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
  ];
}

// ---------------------------------------------------------------- brows
function drawBrow(ctx, A, P, R, s) {
  const side = s < 0 ? 'L' : 'R';
  const asym = (P.browAsym || 0) * s; // positive raises the screen-right brow
  const inR = (P.browIn || 0) + (P['browIn' + side] || 0) + asym * 0.5 + (P.browTalk || 0);
  const outR = (P.browOut || 0) + (P['browOut' + side] || 0) + asym + (P.browTalk || 0) * 0.6;
  const knit = P.browKnit || 0;
  const th = (A.browThick || 1) * (A.sex === 'f' ? 0.03 : 0.042);
  const baseY = -0.1 - (A.browHeight || 0);
  const inner = [s * (0.07 - knit * 0.018), baseY + 0.008 - inR * 0.08 + knit * 0.016];
  const peak = [s * 0.17, baseY - 0.032 - (inR * 0.35 + outR * 0.65) * 0.065 + Math.max(0, inR) * 0.008];
  const outer = [s * 0.29, baseY + 0.008 - outR * 0.06 + Math.max(0, inR) * 0.026];
  const pI = pf(inner[0], inner[1], R, 0.0), pP = pf(peak[0], peak[1], R, 0.0), pO = pf(outer[0], outer[1], R, -0.01);
  // tapered filled brow
  ctx.save();
  ctx.fillStyle = col(A.browColor || A.hair);
  ctx.beginPath();
  ctx.moveTo(pI[0], pI[1] - th * 0.45);
  ctx.quadraticCurveTo(pP[0], pP[1] - th * 0.55, pO[0], pO[1]);
  ctx.quadraticCurveTo(pP[0], pP[1] + th * 0.45, pI[0], pI[1] + th * 0.45);
  ctx.quadraticCurveTo(pI[0] - s * th * 0.55, pI[1], pI[0], pI[1] - th * 0.45);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
  return { inner: pI, peak: pP, outer: pO, knit, inR };
}

// ---------------------------------------------------------------- nose
function drawNose(ctx, A, P, R, light) {
  const tip = pf(0, 0.165, R, 0.1);
  const skinD = shade(A.skin, -0.3);
  const nw = 0.036 * (A.noseW || 1);
  ctx.save();
  // soft shadow under the nose
  const g = ctx.createRadialGradient(tip[0], tip[1] + 0.03, 0.005, tip[0], tip[1] + 0.03, 0.07);
  g.addColorStop(0, rgbStr(skinD, 0.32));
  g.addColorStop(1, rgbStr(skinD, 0));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.ellipse(tip[0], tip[1] + 0.03, 0.07, 0.04, 0, 0, Math.PI * 2); ctx.fill();
  // side plane on the shadow side / far side
  const far = R.sy > 0.05 ? -1 : R.sy < -0.05 ? 1 : (light.x > 0 ? -1 : 1);
  const bridgeTop = pf(far * 0.035, -0.02, R, 0.04);
  const bridgeLow = pf(far * 0.042, 0.13, R, 0.08);
  ctx.strokeStyle = rgbStr(skinD, 0.25 + Math.abs(R.sy) * 0.6);
  ctx.lineWidth = 0.007; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(bridgeTop[0], bridgeTop[1]);
  ctx.quadraticCurveTo(bridgeLow[0], bridgeLow[1], tip[0] + far * 0.01, tip[1] - 0.005);
  ctx.stroke();
  // nostril line
  const l = pf(-nw, 0.175, R, 0.06), r = pf(nw, 0.175, R, 0.06), c = pf(0, 0.198, R, 0.08);
  ctx.strokeStyle = rgbStr(shade(A.skin, -0.42), 0.75);
  ctx.lineWidth = 0.0075;
  ctx.beginPath(); ctx.moveTo(l[0], l[1]); ctx.quadraticCurveTo(c[0], c[1] + 0.006, r[0], r[1]); ctx.stroke();
  // tip highlight
  ctx.fillStyle = rgbStr(shade(A.skin, 0.35), 0.35);
  ctx.beginPath(); ctx.ellipse(tip[0] - light.x * 0.008, tip[1] - 0.012, 0.012, 0.008, 0, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

// ---------------------------------------------------------------- mouth
function mouthGeom(A, P, R) {
  const smile = clamp(P.smile || 0, -1, 1);
  const open = clamp((P.open || 0) * 0.105 + (P.jawOpen || 0) * 0.075, 0, 0.16);
  const round = clamp(P.round || 0, 0, 1);
  const press = clamp(P.press || 0, 0, 1);
  const mw = 0.1 * (A.mouthW || 1) * (1 + 0.22 * (P.wide || 0) + 0.16 * Math.max(0, smile) - 0.32 * round - 0.08 * press);
  const my = 0.3 + (A.mouthY || 0) + (P.jawOpen || 0) * 0.012;
  const asym = P.asym || 0;
  const cornerL = my - smile * 0.042 + (asym < 0 ? asym * 0.026 : 0);
  const cornerR = my - smile * 0.042 - (asym > 0 ? asym * 0.026 : 0);
  return { smile, open, round, press, mw, my, cornerL, cornerR };
}
function drawMouth(ctx, A, P, R) {
  const M = mouthGeom(A, P, R);
  const { smile, open, mw, my, press } = M;
  const lipCol = A.lip || shade(A.skin, -0.25);
  const line = rgbStr(shade(A.skin, -0.5), 0.85);
  const L = pf(-mw, M.cornerL, R, -0.01), Rr = pf(mw, M.cornerR, R, -0.01);
  const upY = my - 0.004 - open * 0.18 + Math.max(0, smile) * 0.004;
  const loY = my + open + Math.max(0, smile) * open * 0.25 + Math.max(0, -smile) * 0.0;
  const U1 = pf(-mw * 0.45, upY - 0.003, R, 0.012), U2 = pf(mw * 0.45, upY - 0.003, R, 0.012);
  const D1 = pf(mw * 0.5, loY + 0.004, R, 0.01), D2 = pf(-mw * 0.5, loY + 0.004, R, 0.01);
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  // lower-lip shadow & lip colour (gives the mouth volume even when closed)
  const lowerLip = pf(0, my + open + 0.032, R, 0.0);
  const lg = ctx.createRadialGradient(lowerLip[0], lowerLip[1], 0.004, lowerLip[0], lowerLip[1], 0.05);
  lg.addColorStop(0, rgbStr(shade(A.skin, -0.3), 0.32 * (1 - press * 0.6)));
  lg.addColorStop(1, rgbStr(shade(A.skin, -0.3), 0));
  ctx.fillStyle = lg;
  ctx.beginPath(); ctx.ellipse(lowerLip[0], lowerLip[1] + 0.006, 0.06, 0.022, 0, 0, Math.PI * 2); ctx.fill();
  if (A.sex === 'f' || A.lipAlways) {
    const lipA = 0.75 * (1 - press * 0.7);
    ctx.fillStyle = rgbStr(lipCol, lipA);
    // lower lip
    ctx.beginPath();
    ctx.moveTo(L[0], L[1]);
    ctx.bezierCurveTo(D2[0], D2[1] + 0.024, D1[0], D1[1] + 0.024, Rr[0], Rr[1]);
    ctx.bezierCurveTo(D1[0], D1[1], D2[0], D2[1], L[0], L[1]);
    ctx.fill();
    // upper lip with a soft cupid's bow
    const cb = pf(0, upY - 0.016, R, 0.015), cbl = pf(-mw * 0.28, upY - 0.022, R, 0.013), cbr = pf(mw * 0.28, upY - 0.022, R, 0.013);
    ctx.fillStyle = rgbStr(shade(lipCol, -0.08), lipA);
    ctx.beginPath();
    ctx.moveTo(L[0], L[1]);
    ctx.quadraticCurveTo(cbl[0] - 0.02, cbl[1] + 0.004, cbl[0], cbl[1]);
    ctx.quadraticCurveTo(cb[0], cb[1] + 0.012, cbr[0], cbr[1]);
    ctx.quadraticCurveTo(cbr[0] + 0.02, cbr[1] + 0.004, Rr[0], Rr[1]);
    ctx.bezierCurveTo(U2[0], U2[1], U1[0], U1[1], L[0], L[1]);
    ctx.fill();
    const gl = pf(-mw * 0.12, loY + 0.02, R, 0.012);
    ctx.fillStyle = `rgba(255,215,205,${0.16 * (1 - press)})`;
    ctx.beginPath(); ctx.ellipse(gl[0], gl[1], mw * 0.22, 0.005, -0.05, 0, Math.PI * 2); ctx.fill();
  }
  if (open > 0.012) {
    ctx.beginPath();
    ctx.moveTo(L[0], L[1]);
    ctx.bezierCurveTo(U1[0], U1[1], U2[0], U2[1], Rr[0], Rr[1]);
    ctx.bezierCurveTo(D1[0], D1[1], D2[0], D2[1], L[0], L[1]);
    ctx.closePath();
    ctx.fillStyle = '#3d1517';
    ctx.fill();
    ctx.save();
    ctx.clip();
    // upper teeth
    const tTop = Math.min(U1[1], U2[1]);
    ctx.fillStyle = '#f4efe6';
    const teethH = 0.024 + (P.teeth || 0) * 0.008;
    ctx.beginPath();
    ctx.ellipse((L[0] + Rr[0]) / 2, tTop + teethH * 0.15, mw * 0.95, teethH, 0, 0, Math.PI * 2);
    ctx.fill();
    // tongue
    if (open > 0.03) {
      ctx.fillStyle = '#b4545a';
      const tg = pf(0, loY + 0.01, R, 0.0);
      ctx.beginPath(); ctx.ellipse(tg[0], tg[1], mw * 0.75, 0.035, 0, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
    ctx.strokeStyle = line; ctx.lineWidth = 0.007;
    ctx.beginPath();
    ctx.moveTo(L[0], L[1]);
    ctx.bezierCurveTo(U1[0], U1[1], U2[0], U2[1], Rr[0], Rr[1]);
    ctx.stroke();
    ctx.lineWidth = 0.005;
    ctx.beginPath();
    ctx.moveTo(Rr[0], Rr[1]);
    ctx.bezierCurveTo(D1[0], D1[1], D2[0], D2[1], L[0], L[1]);
    ctx.stroke();
  } else {
    // closed mouth: one expressive line (with a slight dip when smiling)
    const mid = pf(0, my + smile * 0.012 + press * 0.002, R, 0.012);
    ctx.strokeStyle = line;
    ctx.lineWidth = 0.0075 * (1 - press * 0.15);
    ctx.beginPath();
    ctx.moveTo(L[0], L[1]);
    ctx.bezierCurveTo(lerp(L[0], mid[0], 0.55), mid[1] + (smile > 0 ? 0.003 : 0), lerp(Rr[0], mid[0], 0.55), mid[1] + (smile > 0 ? 0.003 : 0), Rr[0], Rr[1]);
    ctx.stroke();
  }
  // corner accents: dimples for smiles, tension for pressed lips
  const acc = Math.max(smile * 0.8, press * 0.9);
  if (acc > 0.1) {
    ctx.strokeStyle = rgbStr(shade(A.skin, -0.38), 0.5 * acc);
    ctx.lineWidth = 0.006;
    for (const [p, s] of [[L, -1], [Rr, 1]]) {
      ctx.beginPath();
      ctx.moveTo(p[0] + s * 0.008, p[1] - 0.012);
      ctx.quadraticCurveTo(p[0] + s * 0.016, p[1], p[0] + s * 0.007, p[1] + 0.012);
      ctx.stroke();
    }
  }
  ctx.restore();
  return M;
}

// ---------------------------------------------------------------- tears
// P.tears: array of {side: -1|1, t: 0..1 progress, a: alpha}
function drawTears(ctx, A, P, R) {
  if (!P.tears) return;
  ctx.save();
  ctx.lineCap = 'round';
  for (const tr of P.tears) {
    const s = tr.side;
    const a = clamp(tr.a ?? 1);
    if (a <= 0.01) continue;
    const start = [s * 0.2, 0.09];
    const path = [start, [s * 0.215, 0.17], [s * 0.225, 0.26], [s * 0.2, 0.36]];
    const pts = path.map((p) => pf(p[0], p[1], R, 0.005));
    const prog = clamp(tr.t);
    // wet streak
    ctx.strokeStyle = `rgba(225,240,255,${0.38 * a})`;
    ctx.lineWidth = 0.009;
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    const end = bez(pts[0], pts[1], pts[2], pts[3], prog);
    const steps = 12;
    for (let i = 1; i <= steps; i++) {
      const q = bez(pts[0], pts[1], pts[2], pts[3], prog * i / steps);
      ctx.lineTo(q[0], q[1]);
    }
    ctx.stroke();
    // droplet
    if (prog < 0.98) {
      ctx.fillStyle = `rgba(235,245,255,${0.85 * a})`;
      ctx.beginPath(); ctx.ellipse(end[0], end[1], 0.011, 0.015, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgba(255,255,255,${0.95 * a})`;
      ctx.beginPath(); ctx.arc(end[0] - 0.003, end[1] - 0.005, 0.004, 0, Math.PI * 2); ctx.fill();
    }
  }
  ctx.restore();
}

// ---------------------------------------------------------------- ears
function earInfo(R, s) {
  const p = [s * 0.43, 0.07, -0.05];
  const q = proj(p, R);
  const z1 = -p[0] * R.sy + p[2] * R.cy;
  return { pos: q, front: z1 > -0.03, vis: clamp((z1 + 0.32) / 0.25) };
}
function drawEar(ctx, A, R, s) {
  const E = earInfo(R, s);
  if (E.vis <= 0) return;
  const [x, y] = E.pos;
  const squash = clamp(0.55 + Math.abs(-s * R.sy + R.cy) * 0.45, 0.3, 1);
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(squash, 1);
  ctx.fillStyle = col(A.skin);
  ctx.strokeStyle = rgbStr(shade(A.skin, -0.35));
  ctx.lineWidth = 0.007;
  ctx.beginPath();
  ctx.moveTo(0, -0.07);
  ctx.bezierCurveTo(s * 0.075, -0.09, s * 0.08, 0.02, s * 0.03, 0.08);
  ctx.quadraticCurveTo(s * 0.0, 0.1, -s * 0.01, 0.06);
  ctx.closePath();
  ctx.fill(); ctx.stroke();
  ctx.strokeStyle = rgbStr(shade(A.skin, -0.3), 0.6);
  ctx.beginPath();
  ctx.moveTo(s * 0.012, -0.04);
  ctx.bezierCurveTo(s * 0.05, -0.05, s * 0.05, 0.02, s * 0.02, 0.04);
  ctx.stroke();
  if (A.earring) {
    ctx.fillStyle = A.earring;
    ctx.beginPath(); ctx.arc(s * 0.01, 0.085, 0.014, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.7)';
    ctx.beginPath(); ctx.arc(s * 0.006, 0.081, 0.005, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

module.exports = {
  zf, rotation, proj, pf, headOutline, smoothPath, eyeShape, drawEye, drawBrow, drawNose,
  drawMouth, mouthGeom, drawTears, drawEar, earInfo, bez, YAW_MAX, PITCH_MAX,
};
