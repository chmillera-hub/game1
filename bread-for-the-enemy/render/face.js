// 2.5D anime head rig.
// Head space: x right, y down, z toward viewer. Unit = half the face width.
// Eye line at y=0, chin ~ y=1.33, skull top ~ y=-1.38.
'use strict';
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade } = L;

// ------------------------------------------------------------------ projection
function makeProj(H) {
  const cy = Math.cos(H.yaw), sy = Math.sin(H.yaw);
  const cp = Math.cos(H.pitch), sp = Math.sin(H.pitch);
  const cr = Math.cos(H.roll), sr = Math.sin(H.roll);
  const s = H.s;
  const P = (x, y, z) => {
    const x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
    const y2 = y * cp + z1 * sp, z2 = -y * sp + z1 * cp;
    return [H.x + (x1 * cr - y2 * sr) * s, H.y + (x1 * sr + y2 * cr) * s, z2];
  };
  // silhouette-aware projection for contour points: far side wraps forward
  const Pc = (x, y, z) => {
    const far = Math.sign(x) === Math.sign(H.yaw) && Math.abs(H.yaw) > 0.001;
    const zz = far ? z + 0.55 * Math.abs(sy) : z;
    return P(x, y, zz);
  };
  return { P, Pc, s, H };
}

// default face geometry (can be overridden per character via style.geo)
const GEO = {
  eyeX: 0.45, eyeY: 0.02, eyeZ: 0.78, eyeW: 0.265, eyeH: 1.0, // eyeH scales lid heights
  browY: -0.32, browW: 0.075,
  noseY: 0.48, noseLen: 1.0,
  mouthY: 0.84, mouthW: 0.22,
  chinY: 1.33, jawW: 0.70, jawY: 0.92, cheekW: 0.97,
  craniumY: -0.38, craniumR: 1.0,
  neckW: 0.55,
};

function faceContour(G, open) {
  // right side from temple to chin (x>0), then mirrored; z = depth
  const jd = open * 0.13; // jaw drop
  const cw = G.cheekW;
  const R = [
    [0.96 * cw, -0.62, 0.05],
    [0.98 * cw, -0.1, 0.18],
    [0.96 * cw, 0.28, 0.22],
    [0.88 * cw, 0.6, 0.2],
    [G.jawW, G.jawY + jd * 0.5, 0.24],
    [0.44, G.chinY - 0.2 + jd * 0.9, 0.48],
    [0.2, G.chinY - 0.04 + jd, 0.64],
  ];
  const chin = [0, G.chinY + jd, 0.68];
  const left = R.map(([x, y, z]) => [-x, y, z]);
  return { R, left, chin };
}

// --------------------------------------------------------------- the head
function drawHead(ctx, H, st, F, Lt, extra = {}) {
  const pr = makeProj(H);
  const { P, Pc, s } = pr;
  const G = Object.assign({}, GEO, st.geo || {});
  const open = F.mouthOpen;

  // colours (lighting)
  const pale = F.pale || 0;
  const skinBase = mix(st.skin, '#d8d0cc', pale * 0.45);
  const skin = L.mul(skinBase, Lt.key || '#ffffff');
  const skinSh = mix(skin, L.mul(mix(st.skinShadow, '#a89ca8', pale * 0.3), Lt.amb || '#ffffff'), 0.8);
  const line = st.line || '#3a2420';
  const lw = (Lt.lineW || 1) * s * 0.02;

  // contour
  const C = faceContour(G, open);
  const lowerR = C.R.map((p) => Pc(...p));
  const lowerL = C.left.map((p) => Pc(...p));
  const chinP = P(...C.chin);
  // face polygon: left temple -> down to chin -> up right side -> over forehead
  const facePoly = [...lowerL, chinP, ...lowerR.slice().reverse()];
  const crC = P(0, G.craniumY, -0.1);
  const crR = G.craniumR * s;

  // face polygon is traced counter-clockwise on screen; the cranium ellipse must
  // use the same winding so the nonzero union fills (and clips) both parts
  const faceClip = () => {
    ctx.beginPath();
    L.crPath(ctx, facePoly, false, 0.5);
    ctx.lineTo(facePoly[0][0], facePoly[0][1]);
    ctx.closePath();
    ctx.moveTo(crC[0] + crR, crC[1]);
    ctx.ellipse(crC[0], crC[1], crR, crR * 1.02, H.roll, 0, -L.TAU, true);
  };

  // ---------------- back hair / behind-head items
  if (st.hairBack) st.hairBack(ctx, pr, st, F, Lt, extra);

  // ---------------- neck, then the body/clothes over the neck base
  if (!extra.noNeck) drawNeck(ctx, pr, st, F, Lt, skin, skinSh, line, lw, G);
  if (extra.drawBody) extra.drawBody(pr);

  // ---------------- ears
  drawEars(ctx, pr, st, skin, skinSh, line, lw);

  // ---------------- skin
  ctx.save();
  faceClip();
  ctx.fillStyle = skin;
  ctx.fill('nonzero');
  ctx.restore();

  // cel shadow (side away from light)
  ctx.save();
  faceClip();
  ctx.clip('nonzero');
  drawCelShadow(ctx, pr, G, F, Lt, skinSh, st);
  // warm cheeks / blush
  const blush = (st.blush || 0.15) + (F.blush || 0) + (F.tears || 0) * 0.35;
  if (blush > 0.01) {
    for (const sd of [-1, 1]) {
      const c = P(sd * 0.55, 0.42, 0.7);
      ctx.fillStyle = L.radial(ctx, c[0], c[1], 0, s * 0.32, [[0, rgba(st.blushColor || '#e0707a', 0.28 * blush)], [1, rgba('#e0707a', 0)]]);
      ctx.fillRect(c[0] - s * 0.4, c[1] - s * 0.4, s * 0.8, s * 0.8);
    }
    // reddened nose when crying
    if ((F.tears || 0) > 0.3) {
      const n = P(0, 0.45, 1.05);
      ctx.fillStyle = L.radial(ctx, n[0], n[1], 0, s * 0.16, [[0, rgba('#e06a6a', 0.3 * F.tears)], [1, rgba('#e06a6a', 0)]]);
      ctx.fillRect(n[0] - s * 0.2, n[1] - s * 0.2, s * 0.4, s * 0.4);
    }
  }
  // ambient occlusion around eye sockets for older/weary faces
  const sock = (st.age || 0) * 0.5 + (F.weary || 0) * 0.3 + 0.12;
  for (const sd of [-1, 1]) {
    const c = P(sd * G.eyeX, -0.12, G.eyeZ);
    ctx.fillStyle = L.radial(ctx, c[0], c[1], s * 0.05, s * 0.38, [[0, rgba(skinSh, 0.0)], [0.55, rgba(skinSh, 0.35 * sock)], [1, rgba(skinSh, 0)]]);
    ctx.fillRect(c[0] - s * 0.45, c[1] - s * 0.45, s * 0.9, s * 0.9);
  }
  if (st.hairShadow) st.hairShadow(ctx, pr, st, F, Lt, skinSh);
  ctx.restore();

  // ---------------- age lines and expression lines
  drawLines(ctx, pr, G, st, F, skinSh, line, lw);

  // ---------------- beard base (under mouth)
  if (st.beard) st.beard(ctx, pr, st, F, Lt, 'base', G);

  // ---------------- nose
  drawNose(ctx, pr, G, st, F, Lt, skinSh, line, lw);

  // ---------------- mouth
  drawMouth(ctx, pr, G, st, F, Lt, skin, skinSh, line, lw);

  // ---------------- mustache
  if (st.beard) st.beard(ctx, pr, st, F, Lt, 'top', G);

  // ---------------- face outline
  ctx.save();
  ctx.beginPath();
  L.crPath(ctx, [...lowerL, chinP, ...lowerR.slice().reverse()], false, 0.5);
  ctx.strokeStyle = line;
  ctx.lineWidth = lw * 1.1;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  if (!st.noFaceLine) ctx.stroke();
  ctx.restore();
  if (st.bald) drawCraniumLine(ctx, pr, G, line, lw);

  // ---------------- eyes
  for (const sd of [-1, 1]) drawEye(ctx, pr, G, st, F, Lt, sd, line, lw);
  // tears on cheeks
  if ((F.tearFlow || 0) > 0.01) drawTears(ctx, pr, G, F, extra.t || 0);

  // ---------------- brows
  for (const sd of [-1, 1]) drawBrow(ctx, pr, G, st, F, sd, line, lw);

  // ---------------- rim light (under the hair)
  if (Lt.rim && (Lt.rimA || 0) > 0) drawRim(ctx, pr, facePoly, crC, crR, Lt, s, st);

  // ---------------- front hair, headwear
  if (st.hairFront) st.hairFront(ctx, pr, st, F, Lt, extra);

  return pr;
}

function drawCraniumLine(ctx, pr, G, line, lw) {
  const { P, s } = pr;
  const pts = [];
  for (let a = -1.6; a <= 1.6; a += 0.2) {
    pts.push(P(Math.sin(a) * G.craniumR * 0.995, G.craniumY - Math.cos(a) * G.craniumR, 0.0 + Math.cos(a) * 0.1));
  }
  L.strokeSmooth(ctx, pts, line, lw * 1.0);
}

function drawNeck(ctx, pr, st, F, Lt, skin, skinSh, line, lw, G) {
  const { P, s, H } = pr;
  // neck is mostly vertical in screen space regardless of head pitch/yaw
  const top = P(0, 0.95, -0.25);
  const nw = (G.neckW) * s;
  const base = [H.x + (H.neckDX || 0), H.y + s * 2.25];
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(top[0] - nw * 0.95, top[1] - s * 0.3);
  ctx.lineTo(base[0] - nw * 1.12, base[1]);
  ctx.lineTo(base[0] + nw * 1.12, base[1]);
  ctx.lineTo(top[0] + nw * 0.95, top[1] - s * 0.3);
  ctx.closePath();
  ctx.fillStyle = skin;
  ctx.fill();
  ctx.clip();
  // jaw shadow on neck
  const ch = P(0, 1.2, 0.3);
  ctx.fillStyle = rgba(skinSh, 0.95);
  ctx.beginPath();
  ctx.ellipse(ch[0], ch[1] + s * 0.05, nw * 1.4, s * 0.55, 0, 0, L.TAU);
  ctx.fill();
  // side shadow
  const side = -(Lt.side || -1);
  ctx.fillStyle = rgba(skinSh, 0.8);
  ctx.fillRect(top[0] + side * nw * 0.35 - (side < 0 ? nw * 1.2 : 0), top[1], nw * 1.2, s * 3);
  ctx.restore();
  // neck lines
  ctx.strokeStyle = line;
  ctx.lineWidth = lw * 0.9;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(top[0] - nw * 0.92, top[1] + s * 0.05);
  ctx.quadraticCurveTo(top[0] - nw * 0.98, (top[1] + base[1]) / 2, base[0] - nw * 1.1, base[1] - s * 0.1);
  ctx.moveTo(top[0] + nw * 0.92, top[1] + s * 0.05);
  ctx.quadraticCurveTo(top[0] + nw * 0.98, (top[1] + base[1]) / 2, base[0] + nw * 1.1, base[1] - s * 0.1);
  ctx.stroke();
  if (st.adamsApple !== false && !st.child) {
    const a = P(0, 1.55, 0.2);
    ctx.globalAlpha = 0.5;
    ctx.beginPath();
    ctx.moveTo(a[0] - s * 0.04, a[1]);
    ctx.quadraticCurveTo(a[0], a[1] + s * 0.06, a[0] + s * 0.05, a[1] - s * 0.01);
    ctx.lineWidth = lw * 0.7;
    ctx.stroke();
    ctx.globalAlpha = 1;
  }
}

function drawEars(ctx, pr, st, skin, skinSh, line, lw) {
  const { P, s, H } = pr;
  if (st.noEars) return;
  for (const sd of [-1, 1]) {
    // hide the far ear when turned
    const far = Math.sign(sd) === Math.sign(H.yaw);
    if (far && Math.abs(H.yaw) > 0.32) continue;
    const pts = [[sd * 0.95, -0.02, -0.02], [sd * 1.12, -0.06, -0.12], [sd * 1.16, 0.18, -0.15], [sd * 1.06, 0.42, -0.1], [sd * 0.94, 0.5, -0.02]].map((p) => P(...p));
    ctx.beginPath();
    L.crPath(ctx, pts, false);
    ctx.closePath();
    ctx.fillStyle = far ? skinSh : skin;
    ctx.fill();
    ctx.strokeStyle = line;
    ctx.lineWidth = lw * 0.9;
    ctx.stroke();
    const inner = [[sd * 1.03, 0.04, -0.1], [sd * 1.08, 0.2, -0.13], [sd * 1.0, 0.36, -0.08]].map((p) => P(...p));
    L.strokeSmooth(ctx, inner, rgba(line, 0.6), lw * 0.7);
  }
}

function terminatorX(H, Lt) {
  const side = Lt.side || -1;
  const wrap = Lt.wrap == null ? 0.72 : Lt.wrap;
  return -side * Math.sin(wrap + side * H.yaw);
}
// fill the shadow side of the head (curved terminator) — used inside clipped hair/beard shapes
function shadowSide(ctx, pr, Lt, color, off = 0) {
  const { P, H } = pr;
  const side = Lt.side || -1;
  const xt = terminatorX(H, Lt) + off * -side;
  const ys = [-2.2, -1.42, -1.0, -0.5, 0, 0.6, 1.2, 2.0, 3.5];
  const pts = ys.map((y) => {
    const sk = y < -0.6 ? Math.sqrt(clamp(1 - Math.pow((y + 0.38) / 1.3, 2), 0.1, 1)) : 1;
    return P(clamp(xt * sk, -1.3, 1.3), y, 0.9);
  });
  const edge = side < 0 ? 4 : -4;
  ctx.beginPath();
  L.crPath(ctx, pts, false);
  const e1 = P(edge, 3.5, 0), e2 = P(edge, -2.2, 0);
  ctx.lineTo(e1[0], e1[1]);
  ctx.lineTo(e2[0], e2[1]);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}

function drawCelShadow(ctx, pr, G, F, Lt, skinSh, st) {
  const { P, s, H } = pr;
  const side = Lt.side || -1; // -1: light from screen-left
  const xt = terminatorX(H, Lt);
  const k = Lt.shadow == null ? 0.72 : Lt.shadow;
  // terminator path (head space): curves into the eye socket, around the
  // cheekbone and under it, then follows the jaw; wraps toward the crown
  const ys = [-1.45, -1.1, -0.75, -0.42, -0.12, 0.18, 0.42, 0.7, 1.0, 1.3, 1.7];
  const bump = [0.32, 0.16, 0.08, -0.04, -0.2, -0.04, 0.12, -0.06, 0.02, -0.02, -0.08];
  const term = ys.map((y, i) => {
    const sk = y < -0.75 ? Math.sqrt(clamp(1 - Math.pow((y + 0.38) / 1.15, 2), 0.05, 1)) : 1;
    const x = (xt + bump[i] * -side * 1.0) * sk + (y < -0.75 ? -side * (1 - sk) * 0.5 : 0);
    // keep a minimum band near the contour so the far cheek always reads as turned
    const lim = side < 0 ? Math.min(x, 0.78) : Math.max(x, -0.78);
    return [clamp(lim, -1.2, 1.2), y, 0.95 * Math.sqrt(Math.max(0, 1 - Math.pow(lim / 1.05, 2))) + 0.05];
  });
  const edge = side < 0 ? 1.6 : -1.6;
  const poly = [...term.map((p) => P(...p)), P(edge, 1.8, 0), P(edge, -1.6, 0)];
  ctx.beginPath();
  L.crPath(ctx, poly.slice(0, term.length), false);
  ctx.lineTo(poly[term.length][0], poly[term.length][1]);
  ctx.lineTo(poly[term.length + 1][0], poly[term.length + 1][1]);
  ctx.closePath();
  ctx.fillStyle = rgba(skinSh, k);
  ctx.fill();
  // soft core-shadow gradient along the terminator (painterly falloff)
  const tm = P(xt, 0.0, 0.95);
  const g = ctx.createLinearGradient(tm[0] + side * s * 0.3, 0, tm[0] - side * s * 0.02, 0);
  g.addColorStop(0, rgba(skinSh, 0));
  g.addColorStop(1, rgba(skinSh, 0.18 * k));
  ctx.fillStyle = g;
  ctx.fillRect(tm[0] - s * 1.5, tm[1] - s * 2, s * 3, s * 4);
  // nose cast shadow
  const n0 = P(0, 0.2, 1.0), n1 = P(0, 0.5, 1.1), n2 = P(-side * 0.16, 0.56, 0.96);
  ctx.beginPath();
  ctx.moveTo(n0[0], n0[1]);
  ctx.lineTo(n1[0], n1[1]);
  ctx.lineTo(n2[0], n2[1]);
  ctx.closePath();
  ctx.fillStyle = rgba(skinSh, 0.6 * k);
  ctx.fill();
  // under-lip / chin shading
  const c = P(0, G.chinY - 0.25 + F.mouthOpen * 0.12, 0.7);
  ctx.fillStyle = L.radial(ctx, c[0], c[1], 0, s * 0.25, [[0, rgba(skinSh, 0.35 * k)], [1, rgba(skinSh, 0)]]);
  ctx.fillRect(c[0] - s * 0.3, c[1] - s * 0.3, s * 0.6, s * 0.6);
}

function drawLines(ctx, pr, G, st, F, skinSh, line, lw) {
  const { P, s } = pr;
  const age = st.age || 0;
  const lc = mix(skinSh, line, 0.45);
  ctx.save();
  ctx.lineCap = 'round';
  // forehead lines: age + worry
  const fh = clamp(age * 0.7 + Math.max(0, F.browInner) * 0.5 + Math.max(0, F.browHeight) * 0.4);
  if (fh > 0.05 && !st.noForehead) {
    for (let i = 0; i < 3; i++) {
      const y = -0.72 - i * 0.12;
      const w = 0.38 - i * 0.05;
      const pts = [P(-w, y + 0.03, 0.88), P(0, y - 0.02 * (F.browInner || 0), 0.95), P(w, y + 0.03, 0.88)];
      L.strokeSmooth(ctx, pts, rgba(lc, 0.55 * fh), lw * 0.6);
    }
  }
  // brow furrow verticals
  const fu = clamp(F.browFurrow || 0);
  if (fu > 0.1) {
    for (const sd of [-1, 1]) {
      const pts = [P(sd * 0.07, -0.42, 0.97), P(sd * 0.09, -0.27, 0.97), P(sd * 0.07, -0.18, 0.97)];
      L.strokeSmooth(ctx, pts, rgba(lc, 0.7 * fu), lw * 0.7);
    }
  }
  // under-eye bags, crow's feet
  if (age > 0.2) {
    for (const sd of [-1, 1]) {
      const ex = sd * G.eyeX;
      L.strokeSmooth(ctx, [P(ex - sd * 0.15, 0.2, 0.8), P(ex, 0.27, 0.8), P(ex + sd * 0.17, 0.2, 0.74)], rgba(lc, 0.5 * age), lw * 0.6);
      for (let i = 0; i < 3; i++) {
        const y0 = -0.04 + i * 0.07;
        L.strokeSmooth(ctx, [P(sd * (G.eyeX + 0.29), y0, 0.6), P(sd * (G.eyeX + 0.39), y0 + (i - 1) * 0.04, 0.5)], rgba(lc, 0.45 * age), lw * 0.5);
      }
    }
  }
  // nasolabial folds: age + smile + cry
  const nl = clamp(age * 0.6 + Math.max(0, F.mouthSmile) * 0.5 + (F.cheekRaise || 0) * 0.4 + (F.tears || 0) * 0.15);
  if (nl > 0.08 && !st.beardHidesFolds) {
    for (const sd of [-1, 1]) {
      const pts = [P(sd * 0.2, 0.42, 0.98), P(sd * 0.33, 0.62, 0.88), P(sd * (0.33 + 0.04 * F.mouthSmile), 0.82, 0.82)];
      L.strokeSmooth(ctx, pts, rgba(lc, 0.55 * nl), lw * 0.7);
    }
  }
  // cheek raise arcs (smiling eyes)
  const cr = clamp(F.cheekRaise || 0);
  if (cr > 0.15) {
    for (const sd of [-1, 1]) {
      const ex = sd * G.eyeX;
      L.strokeSmooth(ctx, [P(ex - sd * 0.12, 0.3, 0.82), P(ex + sd * 0.05, 0.34, 0.8), P(ex + sd * 0.2, 0.28, 0.74)], rgba(lc, 0.4 * cr), lw * 0.55);
    }
  }
  ctx.restore();
}

function drawNose(ctx, pr, G, st, F, Lt, skinSh, line, lw) {
  const { P, s, H } = pr;
  const nl = G.noseLen;
  const side = Lt.side || -1;
  // bridge line on far/shadow side, more visible when turned
  const turn = clamp(Math.abs(H.yaw) * 2.6);
  const sd = H.yaw >= 0 ? 1 : -1;
  const bridge = [P(sd * 0.06, 0.02, 1.0), P(sd * 0.05, 0.25 * nl, 1.06), P(sd * 0.02, 0.44 * nl, 1.12)];
  if (turn > 0.05) L.strokeSmooth(ctx, bridge, rgba(line, 0.55 * turn), lw * 0.75);
  // tip + nostril
  const tip = [P(sd * 0.03, 0.4 * nl, 1.1), P(0, 0.5 * nl, 1.12), P(-sd * 0.07, 0.535 * nl, 1.04)];
  L.strokeSmooth(ctx, tip, rgba(line, 0.85), lw * 0.85);
  const nos = P(-sd * 0.09, 0.53 * nl, 1.0);
  ctx.fillStyle = rgba(line, 0.45);
  L.ellipse(ctx, nos[0], nos[1], s * 0.022, s * 0.014, H.roll);
  ctx.fill();
  // nose highlight
  const hl = P(side * 0.02, 0.32 * nl, 1.1);
  ctx.fillStyle = rgba('#ffffff', 0.18);
  L.ellipse(ctx, hl[0], hl[1], s * 0.02, s * 0.06, H.roll);
  ctx.fill();
}

// ------------------------------------------------------------------ mouth
function drawMouth(ctx, pr, G, st, F, Lt, skin, skinSh, line, lw) {
  const { P, s, t } = pr;
  const o = clamp(F.mouthOpen, 0, 1.2);
  const wide = clamp(F.mouthWide || 0, -1, 1);
  const smile = clamp(F.mouthSmile || 0, -1, 1);
  const press = clamp(F.mouthPress || 0);
  const asym = F.mouthAsym || 0;
  const trem = (F.mouthTremble || 0) * (F._trem || 0);
  const my = G.mouthY;
  let mw = G.mouthW * (1 + 0.28 * wide + 0.12 * Math.max(0, smile) - 0.12 * press);
  if (wide < 0) mw *= 1 + 0.15 * wide; // rounding narrows
  const cy = (sd) => my - smile * 0.075 - asym * sd * 0.05 + trem * 0.012 * sd;
  const cL = P(-mw, cy(-1), 0.8 - mw * 0.3);
  const cR = P(mw, cy(1), 0.8 - mw * 0.3);
  const upY = my - o * 0.05 - (wide < 0 ? -wide * o * 0.03 : 0) - smile * 0.02;
  const loY = my + o * 0.3 + (wide < 0 ? 0.02 * -wide : 0) + trem * 0.02;
  const roundness = wide < 0 ? -wide : 0;
  const upC = P(0, upY, 0.93);
  const loC = P(0, loY, 0.9);
  const upL = P(-mw * 0.55, upY + 0.01 - smile * 0.03, 0.88);
  const upR = P(mw * 0.55, upY + 0.01 - smile * 0.03, 0.88);
  const loL = P(-mw * (0.55 + 0.15 * roundness), lerp(my, loY, 0.85), 0.86);
  const loR = P(mw * (0.55 + 0.15 * roundness), lerp(my, loY, 0.85), 0.86);
  if (o < 0.06) {
    // closed: a single expressive line
    const mid = P(0, my + 0.008 - smile * 0.03 + press * 0.0, 0.93);
    const mL = P(-mw * 0.5, my - smile * 0.045 - asym * -0.025, 0.9);
    const mR = P(mw * 0.5, my - smile * 0.045 - asym * 0.025, 0.9);
    const pts = [cL, mL, mid, mR, cR];
    L.taperStroke(ctx, pts, line, lw * 0.6, lw * 0.6, lw * (1.25 + press * 0.4));
    // lower lip hint
    const ll = [P(-mw * 0.35, my + 0.11, 0.9), P(0, my + 0.13 + press * 0.0, 0.92), P(mw * 0.35, my + 0.11, 0.9)];
    L.strokeSmooth(ctx, ll, rgba(skinSh, 0.9), lw * 0.9);
    if (press > 0.3) {
      for (const c of [cL, cR]) {
        ctx.fillStyle = rgba(line, 0.35 * press);
        L.ellipse(ctx, c[0], c[1], lw * 0.7, lw * 0.7);
        ctx.fill();
      }
    }
    return;
  }
  // open mouth shape
  const shape = [cL, upL, upC, upR, cR, loR, loC, loL];
  ctx.save();
  ctx.beginPath();
  L.crPath(ctx, shape, true, 0.55);
  ctx.fillStyle = st.mouthIn || '#4a1a1c';
  ctx.fill();
  ctx.clip();
  // teeth (upper)
  if (o > 0.12) {
    const th = s * 0.07;
    ctx.fillStyle = '#f4ece6';
    ctx.beginPath();
    L.crPath(ctx, [P(-mw * 0.8, upY - 0.02, 0.9), P(0, upY - 0.02, 0.93), P(mw * 0.8, upY - 0.02, 0.9)], false);
    const b1 = P(mw * 0.8, upY + 0.06, 0.9), b2 = P(0, upY + 0.075, 0.93), b3 = P(-mw * 0.8, upY + 0.06, 0.9);
    ctx.lineTo(b1[0], b1[1]);
    ctx.quadraticCurveTo(b2[0], b2[1] + th * 0.1, b3[0], b3[1]);
    ctx.closePath();
    ctx.fill();
  }
  // tongue
  if (o > 0.3) {
    const tg = P(0, loY - 0.02, 0.88);
    ctx.fillStyle = '#b4545a';
    L.ellipse(ctx, tg[0], tg[1], mw * s * 0.65, s * 0.08 * o, pr.H.roll);
    ctx.fill();
  }
  ctx.restore();
  // outline: upper lip heavier
  L.taperStroke(ctx, [cL, upL, upC, upR, cR], line, lw * 0.6, lw * 0.6, lw * 1.3);
  ctx.beginPath();
  L.crPath(ctx, [cR, loR, loC, loL, cL], false, 0.55);
  ctx.strokeStyle = rgba(line, 0.75);
  ctx.lineWidth = lw * 0.75;
  ctx.stroke();
  // lower lip shadow
  const ll = [P(-mw * 0.32, loY + 0.09, 0.88), P(0, loY + 0.11, 0.9), P(mw * 0.32, loY + 0.09, 0.88)];
  L.strokeSmooth(ctx, ll, rgba(skinSh, 0.85), lw * 0.9);
}

// ------------------------------------------------------------------ eyes
function eyeShape(F, sd, st) {
  // canonical left-on-screen eye (sd=-1): inner corner at +u. We mirror for sd=+1.
  const o = clamp(F.lid * (sd < 0 ? F.lidL : F.lidR), 0, 1.4);
  const lower = clamp(F.lidLower || 0, 0, 1);
  const tilt = F.lidTilt || 0; // + angry (inner down), - sad (outer down)
  const eh = st.geo && st.geo.eyeH ? st.geo.eyeH : 1;
  // open lid
  const upOpen = [[-1.0, 0.1], [-0.62, -0.44 * eh], [0.0, -0.6 * eh], [0.56, -0.47 * eh], [1.0, -0.06]];
  const upWide = [[-1.0, 0.04], [-0.62, -0.58 * eh], [0.0, -0.78 * eh], [0.56, -0.62 * eh], [1.0, -0.12]];
  const closed = [[-1.0, 0.1], [-0.55, 0.22], [0.0, 0.26], [0.55, 0.2], [1.0, 0.04]];
  const loOpen = [[-1.0, 0.12], [-0.45, 0.42 * eh], [0.15, 0.48 * eh], [0.72, 0.32 * eh], [1.0, 0.02]];
  const up = upOpen.map((p, i) => {
    let v;
    if (o <= 1) v = lerp(closed[i][1], p[1], o);
    else v = lerp(p[1], upWide[i][1], (o - 1) / 0.4);
    // tilt: inner (u>0) / outer (u<0)
    const u = p[0];
    v += tilt * (u > 0 ? 0.32 * u : 0.12 * u) * clamp(o * 1.3);
    return [u, v];
  });
  const lo = loOpen.map((p, i) => {
    let v = p[1] - lower * (p[1] - 0.05) * 0.75;
    return [p[0], Math.max(v, up[i][1] + 0.02)];
  });
  return { up, lo, o };
}

function drawEye(ctx, pr, G, st, F, Lt, sd, line, lw) {
  const { P, s, H } = pr;
  const ex = sd * G.eyeX, ey = G.eyeY, ez = G.eyeZ;
  const E = P(ex, ey, ez);
  // local axes: u along surface (curving back toward the side), v down
  const d = 0.05;
  const slope = sd * -0.55; // dz/dx at eye
  const Pu = P(ex + d, ey, ez + slope * d);
  const Pv = P(ex, ey + d, ez + 0.0);
  let ux = (Pu[0] - E[0]) / d, uy = (Pu[1] - E[1]) / d;
  let vx = (Pv[0] - E[0]) / d, vy = (Pv[1] - E[1]) / d;
  const W = G.eyeW * (st.eyeScale || 1);
  // mirror so inner corner is +u for both eyes: for sd=-1 inner is +x already
  const mir = sd < 0 ? 1 : -1;
  ctx.save();
  ctx.transform(ux * W * mir, uy * W * mir, vx * W, vy * W, E[0], E[1]);
  const sh = eyeShape(F, sd, st);
  const { up, lo, o } = sh;
  const lwL = lw / (W * s); // line width in local units
  // gaze in local coords (mirror x)
  const gx = clamp(F.gazeX, -1.2, 1.2) * mir, gy = clamp(F.gazeY, -1, 1);
  if (o > 0.04) {
    // opening
    const openPts = [...L.sampleCR(up, 6), ...L.sampleCR(lo, 6).reverse()];
    ctx.save();
    ctx.beginPath();
    openPts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.closePath();
    ctx.fillStyle = st.sclera || '#fbf8f4';
    ctx.fill();
    ctx.clip();
    // iris
    const ir = st.irisR || 0.5;
    const ix = gx * 0.48, iy = 0.04 + gy * 0.3;
    const irisC = st.iris || '#5a3a26';
    const blind = F.blind || 0;
    ctx.fillStyle = L.linear(ctx, 0, iy - ir * 1.2, 0, iy + ir * 1.2, [[0, shade(irisC, 0.45)], [0.55, irisC], [1, shade(irisC, 1.35)]]);
    L.ellipse(ctx, ix, iy, ir, ir * 1.16);
    ctx.fill();
    // iris ring
    ctx.strokeStyle = rgba(shade(irisC, 0.35), 0.9);
    ctx.lineWidth = 0.07;
    ctx.stroke();
    // pupil
    const pr2 = (st.pupilR || 0.21) * (F.pupil || 1);
    ctx.fillStyle = rgba('#120807', 0.92 * (1 - blind * 0.7));
    L.ellipse(ctx, ix + gx * 0.03, iy + 0.02, pr2, pr2 * 1.18);
    ctx.fill();
    // blindness / glow haze
    if (blind > 0.01) {
      ctx.fillStyle = rgba('#e8eef4', 0.75 * blind);
      L.ellipse(ctx, ix, iy, ir * 1.05, ir * 1.2);
      ctx.fill();
    }
    // lid shadow band
    ctx.fillStyle = L.linear(ctx, 0, -0.7, 0, 0.2, [[0, rgba('#3a3050', 0.55)], [0.6, rgba('#3a3050', 0.12)], [1, rgba('#3a3050', 0)]]);
    ctx.beginPath();
    L.crPath(ctx, up.map(([u, v]) => [u, v - 0.1]), false);
    for (let i = up.length - 1; i >= 0; i--) ctx.lineTo(up[i][0], up[i][1] + 0.38);
    ctx.closePath();
    ctx.fill();
    // highlights
    const shake = F._irisShake || 0;
    const hx = ix - 0.2 - gx * 0.1 + shake * 0.03, hy = iy - 0.26;
    ctx.fillStyle = rgba('#ffffff', 0.95);
    L.ellipse(ctx, hx, hy, 0.16 + (F.tears || 0) * 0.04, 0.13 + (F.tears || 0) * 0.04, -0.4);
    ctx.fill();
    ctx.fillStyle = rgba('#ffffff', 0.8);
    L.ellipse(ctx, ix + 0.22, iy + 0.24, 0.07, 0.06);
    ctx.fill();
    if ((F.tears || 0) > 0.2) {
      // extra wet sparkles
      ctx.fillStyle = rgba('#ffffff', 0.7 * F.tears);
      L.ellipse(ctx, ix + 0.05, iy + 0.32, 0.12, 0.04);
      ctx.fill();
      L.ellipse(ctx, ix - 0.3, iy + 0.1, 0.05, 0.05);
      ctx.fill();
    }
    // wet lower rim
    if ((F.tears || 0) > 0.05) {
      ctx.strokeStyle = rgba('#d8ecff', 0.75 * F.tears);
      ctx.lineWidth = 0.13;
      ctx.beginPath();
      L.crPath(ctx, lo.map(([u, v]) => [u, v - 0.05]), false);
      ctx.stroke();
    }
    ctx.restore();
  }
  // upper lid line (lash line)
  const lc = st.lashColor || line;
  const wMax = (st.lashW || 0.24);
  L.taperStroke(ctx, up, lc, wMax * (0.75 + 0.25 * clamp(o)), wMax * 0.28, wMax * 0.8);
  // outer flick
  if (o > 0.2) {
    const p0 = up[0], p1 = up[1];
    ctx.fillStyle = lc;
    ctx.beginPath();
    ctx.moveTo(p0[0] + 0.05, p0[1] - 0.12);
    ctx.lineTo(p0[0] - 0.16, p0[1] - 0.1);
    ctx.lineTo(p1[0] - 0.05, p1[1] + 0.02);
    ctx.closePath();
    ctx.fill();
  }
  // crease
  if (o > 0.3) {
    const cr = up.slice(0, 4).map(([u, v]) => [u * 0.92 - 0.02, v - 0.2 - (F.lidLower || 0) * 0.02]);
    L.strokeSmooth(ctx, cr, rgba(lc, 0.45), 0.06);
  }
  // lower lid line (outer part)
  if (o > 0.04) {
    L.taperStroke(ctx, lo.slice(0, 4), rgba(lc, 0.7), 0.1, 0.02, 0.08);
  } else {
    // closed: lashes downward hint
    L.strokeSmooth(ctx, lo.slice(0, 3).map(([u, v]) => [u, v + 0.05]), rgba(lc, 0.25), 0.05);
  }
  ctx.restore();
}

// tear streams down the cheeks (two per eye side, deterministic in time)
function drawTears(ctx, pr, G, F, t) {
  const { P, s } = pr;
  const fl = clamp(F.tearFlow);
  for (const sd of [-1, 1]) {
    const x0 = sd * (G.eyeX - 0.08);
    const pts = [P(x0, 0.2, 0.84), P(x0 + sd * 0.03, 0.45, 0.82), P(x0 + sd * 0.05, 0.75, 0.74), P(x0 + sd * 0.02, 1.02, 0.66)];
    // stream (thin translucent)
    const len = fl;
    const dense = L.sampleCR(pts, 6);
    const n = Math.max(2, Math.floor(dense.length * len));
    const seg = dense.slice(0, n);
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = rgba('#cfe6ff', 0.55);
    ctx.lineWidth = s * 0.03;
    ctx.beginPath();
    seg.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.stroke();
    ctx.strokeStyle = rgba('#ffffff', 0.7);
    ctx.lineWidth = s * 0.009;
    ctx.stroke();
    // a drop travelling down
    const ph = ((t * 0.32 + (sd > 0 ? 0.47 : 0)) % 1);
    const di = Math.floor(ph * (dense.length - 1));
    if (fl > 0.5 && di < n) {
      const p = dense[di];
      ctx.fillStyle = rgba('#e6f3ff', 0.85);
      L.ellipse(ctx, p[0], p[1] + s * 0.01, s * 0.022, s * 0.03);
      ctx.fill();
      ctx.fillStyle = rgba('#ffffff', 0.95);
      L.ellipse(ctx, p[0] - s * 0.006, p[1], s * 0.007, s * 0.009);
      ctx.fill();
    }
    ctx.restore();
  }
}

// ------------------------------------------------------------------ brows
function drawBrow(ctx, pr, G, st, F, sd, line, lw) {
  const { P, s } = pr;
  const side = sd < 0 ? 'L' : 'R';
  const inner = (F.browInner || 0) + (F['browInner' + side] || 0);
  const outer = (F.browOuter || 0) + (F['browOuter' + side] || 0);
  const hgt = (F.browHeight || 0) + (F['browH' + side] || 0);
  const fur = clamp(F.browFurrow || 0);
  const by = G.browY - hgt * 0.1;
  const pIn = [sd * (0.15 - fur * 0.035 - Math.max(0, -inner) * 0.02), by + 0.045 - inner * 0.14 + fur * 0.045, 0.92];
  const pMid = [sd * 0.43, by - 0.045 - inner * 0.04 - outer * 0.03, 0.9];
  const pOut = [sd * 0.74, by + 0.03 - outer * 0.1 + inner * 0.03, 0.72];
  const pts = [pIn, pMid, pOut].map((p) => P(...p));
  const bw = (st.browW || G.browW) * s;
  const col = st.browColor || line;
  L.taperStroke(ctx, pts, col, bw * 1.05, bw * 0.35, bw * 0.95);
  if (st.bushyBrows) {
    // hairs
    for (let i = 0; i < 7; i++) {
      const t = i / 6;
      const a = [lerp(pIn[0], pOut[0], t), lerp(pIn[1], pOut[1], t) - 0.03 * Math.sin(t * 3.1), 0.88];
      const b = [a[0] + sd * 0.06, a[1] - 0.05 + (i % 2) * 0.02, 0.86];
      L.strokeSmooth(ctx, [P(...a), P(...b)], rgba(col, 0.7), lw * 0.7);
    }
  }
}

function drawRim(ctx, pr, facePoly, crC, crR, Lt, s, st) {
  // thin bright rim along the contour on the rim side
  const side = Lt.rimSide || 1;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.strokeStyle = rgba(Lt.rim, Lt.rimA);
  ctx.lineWidth = s * 0.03;
  ctx.lineCap = 'round';
  const pts = facePoly.filter((p) => (p[0] - pr.H.x) * side > s * 0.25);
  if (pts.length > 1) {
    ctx.beginPath();
    L.crPath(ctx, pts, false);
    ctx.stroke();
  }
  ctx.restore();
}

module.exports = { drawHead, makeProj, GEO, shadowSide, terminatorX };
