// Cast definitions: proportions, faces, hair, clothing, props.
'use strict';
const { clamp, lerp, mix, shade, rgba, smoothClosed, smoothOpen, capsule, noise1, hash2, TAU } = require('./core');
const { paint, softLine, P2, bboxOf, drawHand, handParams } = require('./rig');

const PHI = 0.62;
const projX = (theta, yaw, R) => R * Math.sin(theta + yaw * PHI);

// ---------------------------------------------------------------- hair helpers
// Fill a hair mass and add flowing strands interpolated between guide curves.
function hairMass(ctx, pts, color, L, o = {}) {
  const path = P2((p) => smoothClosed(p, pts, o.tension ?? 0.9));
  const bb = bboxOf(pts);
  paint(ctx, path, color, L, bb, { lw: 1.8, outlineA: o.outlineA ?? 0.28, rimW: 8, shadowMul: 1.1 });
  if (o.guides) {
    ctx.save();
    ctx.clip(path);
    const [A, B] = o.guides;
    const n = o.strands || 18;
    for (let k = 0; k <= n; k++) {
      const u = k / n;
      const s = A.map((a, i) => [lerp(a[0], B[i][0], u) + (hash2(k, i + 3) * (o.jit || 2)), lerp(a[1], B[i][1], u) + hash2(k + 7, i) * (o.jit || 2)]);
      const light = (k * 7) % 5 < 2;
      const va = 0.55 + 0.45 * Math.abs(hash2(k, 11));
      ctx.strokeStyle = rgba(light ? shade(color, 0.22) : shade(color, -0.28), (light ? 0.26 : 0.22) * va);
      ctx.lineWidth = (o.sw || 2.2) * (0.7 + 0.6 * Math.abs(hash2(k, 13)));
      ctx.lineCap = 'round';
      ctx.beginPath(); smoothOpen(ctx, s); ctx.stroke();
    }
    // sheen band
    if (o.sheen) {
      const [sa, sb] = o.sheen;
      const g = ctx.createLinearGradient(sa[0], sa[1], sb[0], sb[1]);
      g.addColorStop(0, rgba(shade(color, 0.5), 0)); g.addColorStop(0.5, rgba(shade(color, 0.55), 0.22)); g.addColorStop(1, rgba(shade(color, 0.5), 0));
      ctx.fillStyle = g; ctx.fillRect(bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]);
    }
    ctx.restore();
  }
  return path;
}
// Hair cap over the cranium down to the hairline, so no scalp shows past partings or tucked locks.
function scalpCap(ctx, C, o, color, line = -0.27, side = 0.02) {
  const { H, W, yaw, R } = o;
  const outer = [];
  for (let i = 0; i <= 12; i++) { const a = Math.PI * (1 + i / 12); outer.push([Math.cos(a) * W * 0.585, -0.06 * H + Math.sin(a) * H * 0.5]); }
  const inner = [];
  for (let i = 12; i >= 0; i--) {
    const th = -1.45 + (2.9 * i) / 12;
    const x = projX(th, yaw, W * 0.51);
    const y = H * (line + (side - line) * Math.pow(Math.abs(th) / 1.45, 2.2));
    inner.push([x, y]);
  }
  hairMass(ctx, [...outer, ...inner], color, o.L, { outlineA: 0.15 });
}
// curve sampler: quadratic through 3 points -> n points
function q3(a, b, c, n = 7) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const u = i / (n - 1);
    out.push([(1 - u) * (1 - u) * a[0] + 2 * u * (1 - u) * b[0] + u * u * c[0], (1 - u) * (1 - u) * a[1] + 2 * u * (1 - u) * b[1] + u * u * c[1]]);
  }
  return out;
}

// ---------------------------------------------------------------- clothing details
function cardiganDetail(inner, btn) {
  return (ctx, C, sk, info, L, t) => {
    const b = C.body;
    const top = info.sy;
    const cx = info.ctr;
    const vBot = top + b.torso * 0.42;
    // inner top in a V opening
    const v = P2((p) => {
      p.moveTo(cx - C.neck.w * 0.75, top - 8);
      p.lineTo(cx + C.neck.w * 0.75, top - 8);
      p.lineTo(cx + 14, vBot);
      p.lineTo(cx + 6, info.hemY + 20);
      p.lineTo(cx - 6, info.hemY + 20);
      p.lineTo(cx - 14, vBot);
      p.closePath();
    });
    paint(ctx, v, inner, L, [cx - 60, top - 10, cx + 60, info.hemY + 20], { lw: 1.5, outlineA: 0.3 });
    // scoop neckline of the inner top
    softLine(ctx, [[cx - C.neck.w * 0.62, top - 4], [cx, top + C.neck.w * 0.45], [cx + C.neck.w * 0.62, top - 4]], shade(inner, -0.35), 2.4, 0.5);
    // cardigan front edges (soft band)
    for (const sd of [-1, 1]) {
      softLine(ctx, [[cx + sd * C.neck.w * 0.8, top - 6], [cx + sd * 18, vBot], [cx + sd * 8, info.hemY + 12]], shade(C.clothes.top.color, -0.35), 3, 0.6);
      softLine(ctx, [[cx + sd * C.neck.w * 0.95, top], [cx + sd * 30, vBot], [cx + sd * 20, info.hemY + 12]], shade(C.clothes.top.color, 0.2), 4, 0.25);
    }
    // buttons on one edge
    for (let i = 0; i < 4; i++) {
      const y = vBot + i * (info.hemY - vBot) / 4.3;
      ctx.fillStyle = btn; ctx.beginPath(); ctx.arc(cx - 20, y, 4.5, 0, TAU); ctx.fill();
      ctx.fillStyle = rgba('#ffffff', 0.25); ctx.beginPath(); ctx.arc(cx - 21.5, y - 1.5, 1.6, 0, TAU); ctx.fill();
    }
    // ribbed hem band
    ctx.fillStyle = rgba(shade(C.clothes.top.color, -0.18), 0.6);
    ctx.fillRect(cx - b.hipW, info.hemY - 22, b.hipW * 2, 22);
    for (let x = -b.hipW; x < b.hipW; x += 7) softLine(ctx, [[cx + x, info.hemY - 21], [cx + x, info.hemY - 10], [cx + x, info.hemY]], shade(C.clothes.top.color, -0.4), 1.4, 0.25);
    // soft folds at the waist
    softLine(ctx, [[cx - b.waistW * 0.4, top + b.torso * 0.62], [cx - b.waistW * 0.25, top + b.torso * 0.7], [cx - b.waistW * 0.1, top + b.torso * 0.66]], shade(C.clothes.top.color, -0.35), 2.2, 0.3);
    softLine(ctx, [[cx + b.waistW * 0.15, top + b.torso * 0.75], [cx + b.waistW * 0.3, top + b.torso * 0.7], [cx + b.waistW * 0.45, top + b.torso * 0.74]], shade(C.clothes.top.color, -0.35), 2.2, 0.3);
  };
}
function hoodieDetail(ctx, C, sk, info, L) {
  const b = C.body, cx = info.ctr, top = info.sy, col = C.clothes.top.color;
  // drawstrings
  for (const sd of [-1, 1]) {
    ctx.strokeStyle = '#d9d4cb'; ctx.lineWidth = 4; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(cx + sd * 18, top + 10); ctx.quadraticCurveTo(cx + sd * 22, top + 60, cx + sd * 16, top + 105); ctx.stroke();
    ctx.fillStyle = '#bdb6aa'; ctx.beginPath(); ctx.ellipse(cx + sd * 16, top + 110, 4, 7, 0, 0, TAU); ctx.fill();
  }
  // kangaroo pocket
  const py = top + b.torso * 0.7;
  const pk = P2((p) => smoothClosed(p, [[cx - b.waistW * 0.42, py], [cx + b.waistW * 0.42, py], [cx + b.waistW * 0.52, info.hemY - 30], [cx - b.waistW * 0.52, info.hemY - 30]], 0.3));
  ctx.strokeStyle = rgba(shade(col, -0.4), 0.6); ctx.lineWidth = 2.4; ctx.stroke(pk);
  // ribbed hem
  ctx.fillStyle = rgba(shade(col, -0.15), 0.7); ctx.fillRect(cx - b.hipW, info.hemY - 26, b.hipW * 2, 26);
  softLine(ctx, [[cx - b.chestW * 0.35, top + 70], [cx - b.chestW * 0.2, top + 110], [cx - b.chestW * 0.28, top + 150]], shade(col, -0.4), 2.4, 0.3);
  softLine(ctx, [[cx + b.chestW * 0.3, top + 80], [cx + b.chestW * 0.22, top + 120], [cx + b.chestW * 0.3, top + 160]], shade(col, -0.4), 2.4, 0.3);
}
function hoodCollar(ctx, C, sk, info, L) {
  const cx = sk.shC[0], top = sk.shC[1], w = C.neck.w;
  const col = C.clothes.top.color;
  const hood = P2((p) => smoothClosed(p, [[cx - w * 1.25, top + 6], [cx - w * 0.95, top - 18], [cx, top - 6], [cx + w * 0.95, top - 18], [cx + w * 1.25, top + 6], [cx + w * 0.6, top + 30], [cx, top + 22], [cx - w * 0.6, top + 30]], 0.6));
  paint(ctx, hood, shade(col, 0.05), L, [cx - w * 1.3, top - 20, cx + w * 1.3, top + 30], { lw: 2 });
  softLine(ctx, [[cx - w * 0.7, top + 4], [cx, top + 14], [cx + w * 0.7, top + 4]], shade(col, -0.45), 3, 0.5);
}
function labCoat(shirt, tie) {
  return {
    detail: (ctx, C, sk, info, L) => {
      const b = C.body, cx = info.ctr, top = info.sy, col = C.clothes.top.color;
      const vBot = top + b.torso * 0.48;
      // shirt + tie in the lapel opening
      const v = P2((p) => { p.moveTo(cx - C.neck.w * 0.8, top - 8); p.lineTo(cx + C.neck.w * 0.8, top - 8); p.lineTo(cx + 6, vBot); p.lineTo(cx - 6, vBot); p.closePath(); });
      paint(ctx, v, shirt, L, [cx - 50, top - 10, cx + 50, vBot], { lw: 1.4 });
      const tieP = P2((p) => smoothClosed(p, [[cx - 7, top + 4], [cx + 7, top + 4], [cx + 11, vBot - 18], [cx, vBot], [cx - 11, vBot - 18]], 0.2));
      paint(ctx, tieP, tie, L, [cx - 12, top, cx + 12, vBot], { lw: 1.4 });
      ctx.fillStyle = shade(tie, -0.1); ctx.beginPath(); ctx.ellipse(cx, top + 6, 9, 7, 0, 0, TAU); ctx.fill();
      // shirt collar points
      for (const sd of [-1, 1]) {
        const cp = P2((p) => { p.moveTo(cx, top - 4); p.lineTo(cx + sd * C.neck.w * 0.75, top - 10); p.lineTo(cx + sd * 14, top + 20); p.closePath(); });
        paint(ctx, cp, shade(shirt, 0.08), L, [cx - 40, top - 12, cx + 40, top + 22], { lw: 1.4 });
      }
      // lapels
      for (const sd of [-1, 1]) {
        const lp = P2((p) => smoothClosed(p, [[cx + sd * C.neck.w * 0.85, top - 8], [cx + sd * (C.neck.w * 0.85 + 34), top + 20], [cx + sd * 40, vBot - 40], [cx + sd * 8, vBot + 6]], 0.4));
        paint(ctx, lp, shade(col, -0.03), L, [cx - 90, top - 10, cx + 90, vBot + 10], { lw: 1.8, outlineA: 0.4 });
      }
      // front opening below the waist shows trousers
      const opY = sk.hip[1] - 10;
      const gap = P2((p) => { p.moveTo(cx - 4, opY); p.lineTo(cx + 4, opY); p.lineTo(cx + 34, info.hemY + 4); p.lineTo(cx - 34, info.hemY + 4); p.closePath(); });
      ctx.fillStyle = shade(C.clothes.bottom.color, -0.1); ctx.fill(gap);
      softLine(ctx, [[cx, vBot], [cx + 2, (vBot + opY) / 2], [cx, opY]], shade(col, -0.35), 2.2, 0.5);
      // buttons
      for (let i = 0; i < 3; i++) { ctx.fillStyle = '#d8d2c6'; ctx.beginPath(); ctx.arc(cx - 10, vBot + 8 + i * 45, 5, 0, TAU); ctx.fill(); }
      // breast pocket with a pen, hip pockets
      const px = cx + b.chestW * 0.25;
      ctx.strokeStyle = rgba(shade(col, -0.35), 0.7); ctx.lineWidth = 2;
      ctx.strokeRect(px - 24, top + 70, 48, 44);
      ctx.fillStyle = '#3b6fb0'; ctx.fillRect(px + 6, top + 58, 6, 22);
      ctx.strokeRect(cx - b.waistW * 0.5, sk.hip[1] + 20, 56, 50);
      ctx.strokeRect(cx + b.waistW * 0.5 - 56, sk.hip[1] + 20, 56, 50);
      softLine(ctx, [[cx - b.waistW * 0.3, top + b.torso * 0.6], [cx - b.waistW * 0.2, top + b.torso * 0.8], [cx - b.waistW * 0.34, sk.hip[1]]], shade(col, -0.3), 2.4, 0.3);
    },
  };
}

// ---------------------------------------------------------------- props
const PROPS = {
  // pencil pinched between thumb and index finger, crossing the fingers like a writing grip
  pencil: (ctx, C, o) => {
    const hs = C.body.hand;
    const idx = o.hand.tips[0], [tx, ty] = o.hand.thumb;
    const mx = (idx.ex + tx) / 2, my = (idx.ey + ty) / 2;
    ctx.save();
    ctx.translate(mx, my);
    ctx.rotate(0.95 * o.ts);
    const L = hs * 1.25;
    ctx.fillStyle = '#e7b53c'; ctx.fillRect(-L * 0.55, -4, L * 0.85, 8);
    ctx.fillStyle = '#f2d8b0'; ctx.beginPath(); ctx.moveTo(L * 0.3, -4); ctx.lineTo(L * 0.45, 0); ctx.lineTo(L * 0.3, 4); ctx.fill();
    ctx.fillStyle = '#333'; ctx.beginPath(); ctx.moveTo(L * 0.4, -1.4); ctx.lineTo(L * 0.45, 0); ctx.lineTo(L * 0.4, 1.4); ctx.fill();
    ctx.fillStyle = '#e48a9a'; ctx.fillRect(-L * 0.62, -4, L * 0.08, 8);
    ctx.restore();
    // thumb tip pressed over the pencil (no hard outline)
    ctx.fillStyle = C.skin;
    ctx.beginPath(); ctx.ellipse(tx, ty, hs * 0.062, hs * 0.05, 0, 0, TAU); ctx.fill();
  },
};

// ---------------------------------------------------------------- characters
const MAYA_SKIN = '#a8714f';
function mayaHairBack(ctx, C, o) {
  const { H, W, yaw } = o;
  const sh = -yaw * W * 0.06;
  const pts = [[sh, -0.56 * H], [0.42 * W + sh, -0.48 * H], [0.6 * W + sh, -0.18 * H], [0.62 * W + sh, 0.2 * H], [0.66 * W + sh, 0.55 * H],
    [0.56 * W + sh, 0.78 * H], [0.36 * W + sh, 0.7 * H], [-0.36 * W + sh, 0.7 * H], [-0.56 * W + sh, 0.8 * H], [-0.68 * W + sh, 0.55 * H],
    [-0.62 * W + sh, 0.2 * H], [-0.6 * W + sh, -0.18 * H], [-0.42 * W + sh, -0.48 * H]];
  hairMass(ctx, pts, shade(C.hair, -0.12), o.L, {
    guides: [q3([sh, -0.5 * H], [-0.7 * W + sh, 0.1 * H], [-0.58 * W + sh, 0.78 * H]), q3([sh, -0.5 * H], [0.7 * W + sh, 0.1 * H], [0.58 * W + sh, 0.76 * H])],
    strands: 22, sw: 2.6,
  });
}
function mayaHairFront(ctx, C, o) {
  const { H, W, yaw, R } = o;
  scalpCap(ctx, C, o, shade(C.hair, -0.05), -0.26, 0.04);
  const part = projX(-0.38, yaw, R);
  const cx = projX(0, yaw, R);
  // fringe swept from a side part across the forehead, down the right side of the face
  const pts = [[part, -0.53 * H], [projX(0.5, yaw, R) + 6, -0.5 * H], [projX(1.1, yaw, W * 0.53), -0.32 * H], [projX(1.3, yaw, W * 0.55), -0.02 * H],
    [projX(1.25, yaw, W * 0.56), 0.24 * H], [projX(1.12, yaw, W * 0.53), 0.36 * H], [projX(1.05, yaw, W * 0.5), 0.12 * H],
    [projX(0.95, yaw, R), -0.14 * H], [projX(0.55, yaw, R), -0.25 * H], [cx, -0.27 * H], [part - 6, -0.3 * H],
    [projX(-0.85, yaw, R), -0.25 * H], [projX(-1.15, yaw, W * 0.52), -0.12 * H], [projX(-1.2, yaw, W * 0.53), -0.3 * H], [projX(-0.85, yaw, R), -0.47 * H]];
  hairMass(ctx, pts, C.hair, o.L, {
    guides: [q3([part, -0.5 * H], [projX(0.7, yaw, R), -0.42 * H], [projX(1.2, yaw, W * 0.54), 0.3 * H]), q3([part, -0.32 * H], [projX(0.5, yaw, R), -0.24 * H], [projX(1.0, yaw, R), -0.08 * H])],
    strands: 16, sw: 2.4, sheen: [[part, -0.5 * H], [projX(1, yaw, R), -0.1 * H]],
  });
  // left side tucked behind the ear: strands lying against the scalp over the temple
  const lp = [[part - 4, -0.5 * H], [projX(-0.9, yaw, R), -0.44 * H], [projX(-1.22, yaw, W * 0.53), -0.18 * H], [projX(-1.3, yaw, W * 0.53), -0.02 * H], [projX(-1.15, yaw, W * 0.5), -0.06 * H], [projX(-0.9, yaw, R), -0.26 * H], [part - 4, -0.3 * H]];
  hairMass(ctx, lp, C.hair, o.L, { guides: [q3([part, -0.48 * H], [projX(-1.0, yaw, R), -0.4 * H], [projX(-1.28, yaw, W * 0.53), -0.04 * H]), q3([part, -0.32 * H], [projX(-0.9, yaw, R), -0.26 * H], [projX(-1.18, yaw, W * 0.5), -0.06 * H])], strands: 9, sw: 2.2 });
}

const BASE_ADULT = {
  head: { h: 150, w: 114, shape: 'human', jaw: 0.4, chin: 0.11, cheek: 0.49 },
  neck: { len: 54, w: 50 },
  body: { shoulderW: 226, torso: 300, leg: 450, chestW: 196, waistW: 168, hipW: 204, upper: 170, fore: 150, hand: 80, armR: 23, thigh: 44, foot: 120, ankle: 40, hipH: 30 },
  eyes: { y: 0.03, spacing: 0.5, w: 0.225, h: 0.1, irisColor: '#4a2c1a', lash: '#24140f', lashW: 0.12, iris: 1.12 },
  brows: { color: '#2a1a12', thick: 0.045, gap: 0.115, w: 0.26, arch: 0.025 },
  mouth: { y: 0.32, w: 0.33 },
  nose: { y: 0.19 },
  ears: { size: 1 },
};

function maya(inner) {
  return {
    ...BASE_ADULT, id: inner ? 'innerMaya' : 'maya', label: 'Maya', color: '#9fb36a',
    skin: MAYA_SKIN, hair: '#2b1d17', blush: 0.25, blushColor: '#c9665a',
    eyes: { ...BASE_ADULT.eyes, irisColor: '#4b2e1c', flick: true },
    mouth: { y: 0.32, w: 0.33, lip: '#8c4b45', lowerLip: 0.024 },
    clothes: {
      top: { color: '#7a8450', hem: 30, detail: cardiganDetail('#efe6d2', '#5c4630') },
      sleeve: { len: 1, color: '#7a8450', cuff: true, folds: true, cuffW: 1.3 },
      bottom: { color: '#3b4a63' }, shoes: { color: '#5b4636' },
    },
    hairBack: mayaHairBack, hairFront: mayaHairFront,
    glow: inner ? { color: '#fff1c9', amt: 0.85 } : null,
    props: PROPS,
  };
}

function eliBeard(ctx, C, o) {
  const { H, W, yaw, R, open } = o;
  const jaw = open * 0.05 * H;
  const col = '#2a1c16';
  const cx = projX(0, yaw, R * 1.04);
  const pts = [[projX(-1.25, yaw, W * 0.5), 0.02 * H], [projX(-1.05, yaw, W * 0.5), 0.24 * H], [projX(-0.55, yaw, R), 0.42 * H + jaw], [cx, 0.56 * H + jaw],
    [projX(0.55, yaw, R), 0.42 * H + jaw], [projX(1.05, yaw, W * 0.5), 0.24 * H], [projX(1.25, yaw, W * 0.5), 0.02 * H],
    [projX(1.0, yaw, R), 0.2 * H], [projX(0.55, yaw, R), 0.29 * H], [cx, 0.3 * H], [projX(-0.55, yaw, R), 0.29 * H], [projX(-1.0, yaw, R), 0.2 * H]];
  const path = P2((p) => smoothClosed(p, pts, 0.7));
  ctx.save();
  ctx.clip(path);
  const g = ctx.createLinearGradient(0, 0.14 * H, 0, 0.32 * H);
  g.addColorStop(0, rgba(col, 0)); g.addColorStop(1, rgba(col, 0.82));
  ctx.fillStyle = g;
  ctx.fillRect(-W, -0.1 * H, 2 * W, H);
  for (let i = 0; i < 90; i++) {
    const x = lerp(-0.6 * W, 0.6 * W, (hash2(i, 1) + 1) / 2) + yaw * 6, y = lerp(0.12 * H, 0.55 * H, (hash2(i, 2) + 1) / 2);
    ctx.strokeStyle = rgba(i % 2 ? '#4a3428' : '#160e0a', 0.35 + 0.3 * (y / H)); ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + hash2(i, 5) * 3, y + 5); ctx.stroke();
  }
  ctx.restore();
  // mustache
  const my = 0.275 * H;
  const mu = P2((p) => smoothClosed(p, [[cx - W * 0.19, my + 7], [cx - W * 0.11, my - 3], [cx, my - 1], [cx + W * 0.11, my - 3], [cx + W * 0.19, my + 7], [cx + W * 0.1, my + 4], [cx, my + 5], [cx - W * 0.1, my + 4]], 0.6));
  ctx.fillStyle = rgba(col, 0.78); ctx.fill(mu);
}
function eliHair(ctx, C, o) {
  const { H, W, yaw, R } = o;
  const sh = yaw * W * 0.02;
  const pts = [[sh, -0.54 * H], [0.4 * W + sh, -0.48 * H], [0.52 * W, -0.25 * H], [projX(1.3, yaw, W * 0.51), -0.06 * H], [projX(1.22, yaw, W * 0.5), -0.15 * H],
    [projX(0.9, yaw, R), -0.28 * H], [projX(0.3, yaw, R), -0.34 * H], [projX(-0.3, yaw, R), -0.34 * H], [projX(-0.9, yaw, R), -0.28 * H],
    [projX(-1.22, yaw, W * 0.5), -0.15 * H], [projX(-1.3, yaw, W * 0.51), -0.06 * H], [-0.52 * W, -0.25 * H], [-0.4 * W + sh, -0.48 * H]];
  hairMass(ctx, pts, C.hair, o.L, { guides: [q3([projX(-1.2, yaw, R), -0.2 * H], [0, -0.62 * H], [projX(1.2, yaw, R), -0.2 * H]), q3([projX(-0.9, yaw, R), -0.3 * H], [0, -0.4 * H], [projX(0.9, yaw, R), -0.3 * H])], strands: 26, sw: 1.8, jit: 1.5 });
}
function eli() {
  return {
    ...BASE_ADULT, id: 'eli', label: 'Eli', color: '#8fa3b8',
    head: { h: 158, w: 124, shape: 'human', jaw: 0.44, chin: 0.15, cheek: 0.5 },
    neck: { len: 66, w: 58 },
    body: { ...BASE_ADULT.body, shoulderW: 266, torso: 318, leg: 470, chestW: 236, waistW: 206, hipW: 216, upper: 182, fore: 160, hand: 90, armR: 28, thigh: 50 },
    skin: '#9a6646', hair: '#1f1612', blush: 0.08,
    eyes: { ...BASE_ADULT.eyes, w: 0.21, h: 0.088, irisColor: '#3a2416', lashW: 0.1 },
    brows: { color: '#1e140f', thick: 0.05, gap: 0.1, w: 0.26, arch: 0.015, taper: 0.6 },
    mouth: { y: 0.33, w: 0.32, lip: '#7a4636', lowerLip: 0.02, rest: -0.12 },
    clothes: {
      top: { color: '#4f565f', hem: 34, extra: 4, detail: hoodieDetail },
      sleeve: { len: 1, color: '#4f565f', cuff: true, folds: true, cuffW: 1.2, puff: 1.08 },
      bottom: { color: '#3f4535' }, shoes: { color: '#b9b3a8' },
    },
    collar: hoodCollar,
    faceExtra: eliBeard, hairFront: eliHair,
    props: PROPS,
  };
}

function nana() {
  return {
    ...BASE_ADULT, id: 'nana', label: 'Nana', color: '#c08aa6',
    head: { h: 146, w: 116, shape: 'human', jaw: 0.4, chin: 0.12, cheek: 0.5 },
    neck: { len: 44, w: 44 },
    body: { ...BASE_ADULT.body, shoulderW: 212, torso: 280, leg: 410, chestW: 206, waistW: 196, hipW: 214, upper: 162, fore: 142, hand: 78 },
    skin: '#9b6a4c', hair: '#d9d6d2', blush: 0.2, blushColor: '#c97a6a',
    eyes: { ...BASE_ADULT.eyes, irisColor: '#3b2618', h: 0.08 },
    brows: { color: '#b9b2ab', thick: 0.032, gap: 0.11, w: 0.24, arch: 0.03 },
    mouth: { y: 0.33, w: 0.31, lip: '#82504a' },
    clothes: {
      top: { color: '#7b3b55', hem: 34, detail: cardiganDetail('#c9b8dc', '#e8d9a0') },
      sleeve: { len: 1, color: '#7b3b55', cuff: true, folds: true },
      bottom: { color: '#4d4250' }, shoes: { color: '#3a2e2a' },
    },
    faceExtra: (ctx, C, o) => { // gentle wrinkles
      const { H, W, yaw, R } = o;
      const dk = shade(C.skin, -0.35);
      for (const sd of [-1, 1]) {
        const ex = projX(sd * 0.82, yaw, R);
        softLine(ctx, [[ex, -0.0 * H], [ex + sd * 7, 0.02 * H], [ex + sd * 4, 0.06 * H]], dk, 1.6, 0.35);
        const mx = projX(sd * 0.36, yaw, R);
        softLine(ctx, [[mx + sd * 6, 0.16 * H], [mx + sd * 10, 0.26 * H], [mx + sd * 6, 0.34 * H]], dk, 2, 0.3);
      }
      softLine(ctx, [[projX(-0.4, yaw, R), -0.3 * H], [projX(0, yaw, R), -0.31 * H], [projX(0.4, yaw, R), -0.3 * H]], dk, 1.5, 0.2);
    },
    hairBack: (ctx, C, o) => {
      const { H, W, yaw } = o; const sh = -yaw * W * 0.08;
      // bun at the back-top
      hairMass(ctx, [[sh - 0.32 * W, -0.62 * H], [sh, -0.78 * H], [sh + 0.32 * W, -0.62 * H], [sh + 0.2 * W, -0.45 * H], [sh - 0.2 * W, -0.45 * H]], shade(C.hair, -0.05), o.L,
        { guides: [q3([sh - 0.3 * W, -0.6 * H], [sh, -0.85 * H], [sh + 0.3 * W, -0.6 * H]), q3([sh - 0.15 * W, -0.5 * H], [sh, -0.62 * H], [sh + 0.15 * W, -0.5 * H])], strands: 12 });
      hairMass(ctx, [[sh, -0.55 * H], [0.5 * W + sh, -0.42 * H], [0.58 * W + sh, -0.05 * H], [0.5 * W + sh, 0.12 * H], [-0.5 * W + sh, 0.12 * H], [-0.58 * W + sh, -0.05 * H], [-0.5 * W + sh, -0.42 * H]], shade(C.hair, -0.1), o.L, {});
    },
    hairFront: (ctx, C, o) => {
      const { H, W, yaw, R } = o;
      scalpCap(ctx, C, o, shade(C.hair, -0.05), -0.27, 0.0);
      const pts = [[projX(-1.25, yaw, W * 0.53), -0.02 * H], [projX(-1.0, yaw, R), -0.42 * H], [projX(0, yaw, R), -0.56 * H], [projX(1.0, yaw, R), -0.42 * H],
        [projX(1.25, yaw, W * 0.53), -0.02 * H], [projX(1.12, yaw, W * 0.5), -0.1 * H], [projX(0.7, yaw, R), -0.27 * H], [projX(0, yaw, R), -0.3 * H], [projX(-0.7, yaw, R), -0.27 * H], [projX(-1.12, yaw, W * 0.5), -0.1 * H]];
      hairMass(ctx, pts, C.hair, o.L, { guides: [q3([projX(-1.2, yaw, R), -0.05 * H], [projX(0, yaw, R), -0.6 * H], [projX(1.2, yaw, R), -0.05 * H]), q3([projX(-1.05, yaw, R), -0.12 * H], [projX(0, yaw, R), -0.34 * H], [projX(1.05, yaw, R), -0.12 * H])], strands: 18, sheen: [[0, -0.5 * H], [0, -0.3 * H]] });
    },
    props: PROPS,
  };
}

function youngMaya() {
  return {
    ...BASE_ADULT, id: 'youngMaya', label: 'Young Maya', color: '#b9a3d6',
    head: { h: 140, w: 116, shape: 'round' },
    neck: { len: 32, w: 36 },
    body: { shoulderW: 150, torso: 150, leg: 250, chestW: 136, waistW: 128, hipW: 136, upper: 108, fore: 94, hand: 52, armR: 15, thigh: 30, foot: 80, ankle: 28, hipH: 20 },
    skin: '#a8714f', hair: '#2b1d17', blush: 0.35, blushColor: '#d06a5c',
    eyes: { ...BASE_ADULT.eyes, y: 0.06, w: 0.22, h: 0.11, irisColor: '#4b2e1c', iris: 1.05 },
    brows: { color: '#2a1a12', thick: 0.035, gap: 0.12, w: 0.22, arch: 0.03 },
    mouth: { y: 0.33, w: 0.28, lip: '#9a564e' },
    nose: { y: 0.2, type: 'button', size: 0.9 },
    clothes: {
      top: { color: '#b9a3d6', hem: 26, detail: (ctx, C, sk, info) => { softLine(ctx, [[info.ctr - 20, info.sy - 4], [info.ctr, info.sy + 10], [info.ctr + 20, info.sy - 4]], shade('#b9a3d6', -0.4), 3, 0.6); } },
      sleeve: { len: 0.35, color: '#b9a3d6' },
      bottom: { color: '#4f6b8f' }, shoes: { color: '#e05b6b' },
    },
    hairBack: (ctx, C, o) => {
      const { H, W, yaw } = o; const sh = -yaw * W * 0.05;
      hairMass(ctx, [[sh, -0.56 * H], [0.5 * W + sh, -0.4 * H], [0.56 * W + sh, 0.0], [0.5 * W + sh, 0.1 * H], [-0.5 * W + sh, 0.1 * H], [-0.56 * W + sh, 0.0], [-0.5 * W + sh, -0.4 * H]], shade(C.hair, -0.1), o.L, {});
      for (const sd of [-1, 1]) { // two hair puffs, textured with curls
        const px = sd * 0.5 * W + sh, py = -0.5 * H;
        const pts = []; for (let i = 0; i < 12; i++) { const a = (i / 12) * TAU; const r = 0.28 * W * (1 + 0.08 * Math.sin(i * 2.7)); pts.push([px + Math.cos(a) * r, py + Math.sin(a) * r * 0.9]); }
        hairMass(ctx, pts, C.hair, o.L, { guides: [q3([px - 0.25 * W, py], [px, py - 0.35 * W], [px + 0.25 * W, py]), q3([px - 0.2 * W, py + 0.15 * W], [px, py + 0.2 * W], [px + 0.2 * W, py + 0.1 * W])], strands: 10, sw: 2 });
      }
    },
    hairFront: (ctx, C, o) => {
      const { H, W, yaw, R } = o;
      scalpCap(ctx, C, o, shade(C.hair, -0.05), -0.3, 0.0);
      const pts = [[projX(-1.2, yaw, W * 0.52), -0.05 * H], [projX(-0.9, yaw, R), -0.42 * H], [projX(0, yaw, R), -0.54 * H], [projX(0.9, yaw, R), -0.42 * H], [projX(1.2, yaw, W * 0.52), -0.05 * H], [projX(1.0, yaw, R), -0.2 * H], [projX(0, yaw, R), -0.33 * H], [projX(-1.0, yaw, R), -0.2 * H]];
      hairMass(ctx, pts, C.hair, o.L, { guides: [q3([projX(-1.1, yaw, R), -0.1 * H], [projX(0, yaw, R), -0.6 * H], [projX(1.1, yaw, R), -0.1 * H]), q3([projX(-0.95, yaw, R), -0.22 * H], [projX(0, yaw, R), -0.36 * H], [projX(0.95, yaw, R), -0.22 * H])], strands: 14 });
    },
    props: PROPS,
  };
}

// ---------------- emotions
function angerFlames(ctx, C, o) {
  const f = o.S.flame || 0;
  if (f < 0.01) return;
  const { H, W, t } = o;
  const n = 7;
  ctx.save();
  for (let layer = 0; layer < 3; layer++) {
    const col = ['#ff7a1a', '#ffb02e', '#fff0a8'][layer];
    const sc = [1, 0.72, 0.42][layer];
    ctx.fillStyle = rgba(col, 0.92);
    ctx.beginPath();
    ctx.moveTo(-0.47 * W * sc, -0.48 * H);
    for (let i = 0; i <= n; i++) {
      const x = lerp(-0.45 * W, 0.45 * W, i / n) * sc;
      const flick = noise1(t * 6 + i * 3.1 + layer, 5) * 0.3 + 0.7;
      const h = H * (0.35 + 0.35 * Math.sin(i * 1.7 + 1)) * f * flick * sc * (1 + 0.15 * Math.sin(t * 9 + i));
      const xm = x + noise1(t * 4 + i, 9) * 8;
      ctx.quadraticCurveTo(x - 0.06 * W * sc, -0.5 * H - h * 0.5, xm, -0.5 * H - h);
      ctx.quadraticCurveTo(x + 0.06 * W * sc, -0.5 * H - h * 0.4, x + 0.064 * W * sc * 1.5, -0.49 * H);
    }
    ctx.lineTo(0.47 * W * sc, -0.48 * H);
    ctx.closePath();
    ctx.fill();
  }
  // heat glow
  const g = ctx.createRadialGradient(0, -0.6 * H, 5, 0, -0.6 * H, H * 0.9 * f);
  g.addColorStop(0, rgba('#ffb040', 0.35 * f)); g.addColorStop(1, rgba('#ff6020', 0));
  ctx.fillStyle = g; ctx.fillRect(-W, -1.6 * H, 2 * W, 1.6 * H);
  ctx.restore();
}
function anger() {
  return {
    id: 'anger', label: 'Anger', emoji: '😡', color: '#e04a35',
    head: { h: 168, w: 158, shape: 'brick' },
    neck: { len: 52, w: 92 },
    body: { shoulderW: 268, torso: 232, leg: 214, chestW: 258, waistW: 256, hipW: 246, upper: 128, fore: 112, hand: 82, armR: 31, thigh: 56, foot: 104, ankle: 32, hipH: 26 },
    skin: '#d0402f', blush: 0,
    eyes: { y: 0.04, spacing: 0.42, w: 0.17, h: 0.085, irisColor: '#2b1410', sclera: '#f6ede4', lash: '#3b0c08', lashW: 0.1 },
    brows: { color: '#4a0f0a', thick: 0.075, gap: 0.1, w: 0.3, arch: 0.0, taper: 0.8, outerDrop: 0.01 },
    mouth: { y: 0.3, w: 0.42, lip: '#8e1f18', inside: '#3a0d0d' },
    nose: { y: 0.18, type: 'button', size: 1.4 },
    ears: { size: 0.85 },
    clothes: {
      top: { color: '#f3efe7', hem: 18, detail: (ctx, C, sk, info, L) => {
        const cx = info.ctr, top = info.sy;
        const tieP = P2((p) => smoothClosed(p, [[cx - 12, top + 8], [cx + 12, top + 8], [cx + 20, top + 150], [cx, top + 176], [cx - 20, top + 150]], 0.2));
        paint(ctx, tieP, '#6b1a1d', L, [cx - 20, top, cx + 20, top + 180], { lw: 1.6 });
        ctx.fillStyle = '#541418'; ctx.beginPath(); ctx.ellipse(cx, top + 10, 14, 11, 0, 0, TAU); ctx.fill();
        for (const sd of [-1, 1]) {
          const cp = P2((p) => { p.moveTo(cx, top - 2); p.lineTo(cx + sd * 50, top - 10); p.lineTo(cx + sd * 22, top + 30); p.closePath(); });
          paint(ctx, cp, '#ffffff', L, [cx - 55, top - 12, cx + 55, top + 32], { lw: 1.4 });
        }
        // belt
        ctx.fillStyle = '#3a2a22'; ctx.fillRect(cx - 200, info.hemY - 22, 400, 18);
        ctx.fillStyle = '#c9a646'; ctx.fillRect(cx - 14, info.hemY - 24, 28, 22);
        softLine(ctx, [[cx - 90, top + 120], [cx - 70, top + 160], [cx - 80, top + 200]], '#b9b0a2', 2.4, 0.4);
        softLine(ctx, [[cx + 80, top + 110], [cx + 70, top + 150], [cx + 84, top + 200]], '#b9b0a2', 2.4, 0.4);
      } },
      sleeve: { len: 0.32, color: '#f3efe7', puff: 1.15 },
      bottom: { color: '#4a3c35' }, shoes: { color: '#2c2420' },
    },
    noEars: false,
    headTop: angerFlames,
    props: PROPS,
  };
}

function shock(frazzled) {
  return (ctx, C, o) => {
    const { H, W, yaw, t } = o;
    const col = C.hair;
    const cx = yaw * W * 0.04;
    const base = -0.36 * H;
    // irregular tufted mass: lobes of different heights, messier when frazzled
    const lobes = frazzled ? 11 : 9;
    const mass = [[cx + 0.42 * W, base + 0.07 * H]];
    for (let i = 0; i <= lobes; i++) {
      const u = i / lobes;
      const ang = Math.PI * (0.02 + 0.96 * (1 - u));
      const wob = frazzled ? noise1(t * 2.2 + i * 1.7, 4) * 0.06 : 0;
      const r = (frazzled ? 0.68 : 0.6) + (frazzled ? 0.16 : 0.07) * Math.sin(i * 2.9 + 0.7) + wob;
      const rx = W * (frazzled ? 0.62 : 0.52) * (1 + (i % 2 ? 0.06 : -0.04));
      mass.push([cx + Math.cos(ang) * rx, base - Math.sin(ang) * H * r * 0.85 - (i % 2 ? 0.03 * H : 0)]);
    }
    mass.push([cx - 0.42 * W, base + 0.07 * H]);
    const path = P2((p) => smoothClosed(p, mass, 0.85));
    paint(ctx, path, col, o.L, bboxOf(mass), { outline: false });
    ctx.save(); ctx.strokeStyle = rgba(shade(col, -0.45), 0.3); ctx.lineWidth = 1.8;
    ctx.beginPath(); smoothOpen(ctx, mass.slice(1, mass.length - 1), 0.85); ctx.stroke(); ctx.restore();
    ctx.save(); ctx.clip(path);
    ctx.lineCap = 'round';
    const n = frazzled ? 30 : 22;
    for (let i = 0; i < n; i++) {
      const u = (i + 0.5 * hash2(i, 9)) / n;
      const x0 = cx + lerp(-0.4, 0.4, u) * W;
      const lean = lerp(-1, 1, u) * (frazzled ? 0.9 : 0.5) + hash2(i, 3) * 0.3;
      const wob = frazzled ? noise1(t * 3 + i * 1.3, 2) * 8 : 0;
      const h = H * (0.45 + 0.35 * Math.abs(hash2(i, 4)));
      const light = (i * 5) % 7 < 2;
      ctx.strokeStyle = rgba(light ? shade(col, 0.3) : shade(col, -0.28), light ? 0.45 : 0.35);
      ctx.lineWidth = 2 + 2.5 * Math.abs(hash2(i, 6));
      ctx.beginPath();
      ctx.moveTo(x0, base + 0.05 * H);
      ctx.bezierCurveTo(x0 + lean * 18, base - h * 0.35, x0 + lean * 44 + wob, base - h * 0.7, x0 + lean * 60 + wob * 1.4, base - h);
      ctx.stroke();
    }
    ctx.restore();
  };
}
function frizz(ctx, C, o) {
  const { H, W, yaw, t } = o;
  const col = C.hair;
  const cx = yaw * W * 0.05;
  const cy = -0.42 * H;
  scalpCap(ctx, C, { ...o, R: W * 0.49 }, shade(col, -0.05), -0.3, -0.05);
  // a wide frizzy cloud: spiky lobes radiating in every direction, trembling slightly
  const pts = [];
  const n = 26;
  for (let i = 0; i < n; i++) {
    const a = Math.PI * (0.96 + 1.08 * (i / (n - 1)));
    const spike = i % 2 === 0;
    const wob = noise1(t * 5 + i * 1.9, 3) * 0.05;
    const r = (spike ? 0.95 + 0.25 * Math.abs(hash2(i, 5)) : 0.7) + wob;
    pts.push([cx + Math.cos(a) * W * 0.62 * r, cy + Math.sin(a) * H * 0.42 * r]);
  }
  pts.push([cx + W * 0.5, cy + 0.2 * H]); pts.push([cx - W * 0.5, cy + 0.2 * H]);
  const path = P2((p) => smoothClosed(p, pts, 0.55));
  paint(ctx, path, col, o.L, bboxOf(pts), { lw: 1.8, outlineA: 0.3 });
  ctx.save(); ctx.clip(path); ctx.lineCap = 'round';
  for (let i = 0; i < 36; i++) {
    const a = Math.PI * (1 + (i / 35)) + hash2(i, 2) * 0.2;
    const r0 = 0.25 + 0.2 * Math.abs(hash2(i, 8)), r1 = 0.75 + 0.35 * Math.abs(hash2(i, 9));
    const wob = noise1(t * 4 + i, 6) * 6;
    const light = (i * 7) % 5 < 2;
    ctx.strokeStyle = rgba(light ? shade(col, 0.3) : shade(col, -0.3), light ? 0.4 : 0.32);
    ctx.lineWidth = 2 + 2 * Math.abs(hash2(i, 3));
    ctx.beginPath();
    ctx.moveTo(cx + Math.cos(a) * W * 0.62 * r0, cy + Math.sin(a) * H * 0.42 * r0);
    ctx.quadraticCurveTo(cx + Math.cos(a + 0.25) * W * 0.62 * (r0 + r1) / 2 + wob, cy + Math.sin(a + 0.25) * H * 0.42 * (r0 + r1) / 2,
      cx + Math.cos(a - 0.1) * W * 0.62 * r1 + wob, cy + Math.sin(a - 0.1) * H * 0.42 * r1);
    ctx.stroke();
  }
  ctx.restore();
}
function rootedShock(ctx, C, o) {
  scalpCap(ctx, C, { ...o, R: o.W * 0.49 }, shade(C.hair, -0.05), -0.31, -0.08);
  shock(false)(ctx, C, o);
}
function lanky(id, label, emoji, glowColor, tieColor, shirt, frazzled) {
  return {
    id, label, emoji, color: glowColor,
    head: { h: 196, w: 118, shape: 'egg' },
    neck: { len: 62, w: 42 },
    body: { shoulderW: 206, torso: 330, leg: 470, chestW: 172, waistW: 158, hipW: 168, upper: 186, fore: 166, hand: 86, armR: 19, thigh: 34, foot: 116, ankle: 36, hipH: 30 },
    skin: '#efc19c', hair: '#d4552a', blush: 0.15, blushColor: '#e48a72',
    eyes: { y: -0.02, spacing: 0.33, w: 0.4, h: 0.2, style: 'bulge', irisColor: '#5a7a3a', iris: 0.9 },
    brows: { color: '#b0431f', thick: 0.03, gap: 0.16, w: 0.24, arch: 0.04, alpha: 0.8 },
    mouth: { y: 0.36, w: 0.3, lip: '#b9705c' },
    nose: { y: 0.2, type: 'long', size: 1.05 },
    ears: { size: 0.9 },
    clothes: {
      top: { color: frazzled ? '#f6e4d6' : '#f5f0da', hem: 250, extra: 14, ...labCoat(shirt, tieColor) },
      sleeve: { len: 1, color: frazzled ? '#f6e4d6' : '#f5f0da', cuff: true, folds: true, cuffW: 1.45 },
      bottom: { color: '#5a5e6a' }, shoes: { color: '#3b302a' },
    },
    hairFront: frazzled ? frizz : rootedShock,
    glow: { color: glowColor, amt: 1.35, phase: frazzled ? 1.3 : 0 },
    props: PROPS,
  };
}

function sadness() {
  return {
    id: 'sadness', label: 'Sadness', emoji: '❤️', color: '#7fb2e5',
    head: { h: 150, w: 146, shape: 'round' },
    neck: { len: 34, w: 56 },
    body: { shoulderW: 196, torso: 214, leg: 196, chestW: 232, waistW: 244, hipW: 232, upper: 118, fore: 104, hand: 58, armR: 22, thigh: 44, foot: 84, ankle: 28, hipH: 24 },
    skin: '#7fb2e5', hair: '#2e5c9a', blush: 0.18, blushColor: '#5f8fd0',
    eyes: { y: 0.05, spacing: 0.44, w: 0.2, h: 0.1, irisColor: '#1f3f6e', sclera: '#f1f4fa', lash: '#173156', lashW: 0.12 },
    brows: { color: '#22477e', thick: 0.03, gap: 0.12, w: 0.22, arch: 0.02 },
    mouth: { y: 0.34, w: 0.26, lip: '#4f78b3', inside: '#1d2a48', tongue: '#d27b8c' },
    nose: { y: 0.21, type: 'button', size: 1.05 },
    glasses: { r: 0.115, color: '#1d2b4a', w: 0.03 },
    noEars: true,
    clothes: {
      top: { color: '#f2ede1', hem: 26, extra: 10, detail: (ctx, C, sk, info, L) => {
        const cx = info.ctr;
        for (let x = -150; x <= 150; x += 16) softLine(ctx, [[cx + x, info.sy + 30], [cx + x * 1.04, (info.sy + info.hemY) / 2], [cx + x, info.hemY]], shade('#f2ede1', -0.18), 2.4, 0.35);
        // small red heart knitted on the left chest
        const hx = cx - 52, hy = info.sy + 78, s = 15;
        ctx.fillStyle = '#d23a4a';
        ctx.beginPath(); ctx.moveTo(hx, hy + s * 0.9);
        ctx.bezierCurveTo(hx - s * 1.4, hy, hx - s * 0.6, hy - s * 0.95, hx, hy - s * 0.25);
        ctx.bezierCurveTo(hx + s * 0.6, hy - s * 0.95, hx + s * 1.4, hy, hx, hy + s * 0.9);
        ctx.fill();
        ctx.fillStyle = rgba('#ff9aa5', 0.6); ctx.beginPath(); ctx.ellipse(hx - s * 0.45, hy - s * 0.2, s * 0.22, s * 0.15, -0.5, 0, TAU); ctx.fill();
        ctx.fillStyle = rgba(shade('#f2ede1', -0.12), 0.8); ctx.fillRect(cx - 200, info.hemY - 24, 400, 24);
      } },
      sleeve: { len: 1, color: '#f2ede1', cuff: true, folds: true, cuffW: 1.5, puff: 1.12 },
      bottom: { color: '#2f3d66' }, shoes: { color: '#273152' },
    },
    collar: (ctx, C, sk, info, L) => { // turtleneck roll
      const cx = sk.shC[0], top = sk.shC[1], w = C.neck.w;
      const tn = P2((p) => smoothClosed(p, [[cx - w * 0.72, top + 8], [cx - w * 0.62, top - 26], [cx, top - 30], [cx + w * 0.62, top - 26], [cx + w * 0.72, top + 8], [cx, top + 14]], 0.6));
      paint(ctx, tn, '#ebe4d4', L, [cx - w, top - 32, cx + w, top + 14], { lw: 2 });
      for (let x = -w * 0.6; x <= w * 0.6; x += 8) softLine(ctx, [[cx + x, top - 26], [cx + x, top - 10], [cx + x, top + 8]], shade('#ebe4d4', -0.25), 1.8, 0.4);
    },
    hairBack: (ctx, C, o) => {
      const { H, W, yaw } = o; const sh = -yaw * W * 0.05;
      const pts = [[sh, -0.58 * H], [0.5 * W + sh, -0.45 * H], [0.6 * W + sh, -0.1 * H], [0.6 * W + sh, 0.3 * H], [0.5 * W + sh, 0.44 * H], [-0.5 * W + sh, 0.44 * H], [-0.6 * W + sh, 0.3 * H], [-0.6 * W + sh, -0.1 * H], [-0.5 * W + sh, -0.45 * H]];
      hairMass(ctx, pts, shade(C.hair, -0.12), o.L, { guides: [q3([sh, -0.5 * H], [-0.7 * W + sh, -0.1 * H], [-0.55 * W + sh, 0.44 * H]), q3([sh, -0.5 * H], [0.7 * W + sh, -0.1 * H], [0.55 * W + sh, 0.44 * H])], strands: 18 });
    },
    hairFront: (ctx, C, o) => {
      const { H, W, yaw, R } = o;
      const part = projX(0.45, yaw, R);
      // bob: side panels to the chin covering the ears, side-swept fringe
      const pts = [[part, -0.56 * H], [projX(1.0, yaw, W * 0.52), -0.45 * H], [projX(1.45, yaw, W * 0.6), -0.05 * H], [projX(1.45, yaw, W * 0.6), 0.3 * H], [projX(1.3, yaw, W * 0.6), 0.42 * H], [projX(1.15, yaw, W * 0.54), 0.36 * H],
        [projX(1.1, yaw, W * 0.52), 0.0], [projX(0.85, yaw, R), -0.22 * H], [part, -0.3 * H], [projX(-0.3, yaw, R), -0.24 * H], [projX(-0.85, yaw, R), -0.16 * H],
        [projX(-1.1, yaw, W * 0.52), 0.0], [projX(-1.15, yaw, W * 0.54), 0.36 * H], [projX(-1.3, yaw, W * 0.6), 0.42 * H], [projX(-1.45, yaw, W * 0.6), 0.3 * H], [projX(-1.45, yaw, W * 0.6), -0.05 * H], [projX(-1.0, yaw, W * 0.52), -0.45 * H]];
      hairMass(ctx, pts, C.hair, o.L, {
        guides: [q3([part, -0.52 * H], [projX(-0.9, yaw, R), -0.4 * H], [projX(-1.38, yaw, W * 0.6), 0.4 * H]), q3([part, -0.3 * H], [projX(-0.7, yaw, R), -0.18 * H], [projX(-1.1, yaw, W * 0.52), 0.34 * H])],
        strands: 20, sheen: [[part, -0.5 * H], [projX(-0.8, yaw, R), -0.2 * H]],
      });
      // strands for the right panel
      ctx.save();
      ctx.lineCap = 'round';
      for (let i = 0; i < 8; i++) {
        const u = i / 7;
        ctx.strokeStyle = rgba(i % 2 ? shade(C.hair, -0.3) : shade(C.hair, 0.25), 0.35); ctx.lineWidth = 2.2;
        ctx.beginPath(); smoothOpen(ctx, q3([part + u * 10, -0.5 * H + u * 10], [projX(1.2, yaw, W * 0.55) + u * 6, -0.2 * H], [projX(1.3, yaw, W * 0.58) - u * 6, 0.38 * H])); ctx.stroke();
      }
      ctx.restore();
    },
    props: PROPS,
  };
}

function makeCast() {
  return {
    maya: maya(false),
    innerMaya: maya(true),
    eli: eli(),
    nana: nana(),
    youngMaya: youngMaya(),
    anger: anger(),
    annoy: lanky('annoy', 'Annoyance', '😒', '#ffd84a', '#c99a1e', '#f6edc8', false),
    fear: lanky('fear', 'Fear', '😨', '#ff9a3c', '#d9772b', '#f6dcc8', true),
    sadness: sadness(),
  };
}

module.exports = { makeCast, PROPS, hairMass, q3 };
