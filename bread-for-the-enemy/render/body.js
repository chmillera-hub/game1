// Bodies, arms, hands and props. Units: s = head unit (half face width) in px.
'use strict';
const L = require('./lib');
const { clamp, lerp, mix, rgba, shade, smooth } = L;

const lit = (c, Lt) => L.mul(c, Lt.key || '#ffffff');
const shd = (c, Lt) => L.mul(shade(c, 0.6), Lt.amb || '#ffffff');

// ---------------------------------------------------------------- torso
// B: neck base (screen). by: body yaw (-0.6..0.6), lean: tilt radians, sh: shoulder raise (units)
function torsoPts(B, s, by, sh, len = 9) {
  const c = Math.cos(by), sn = Math.sin(by);
  const X = (x, y) => {
    const z = 0.9 * Math.sqrt(Math.max(0, 1 - Math.pow(x / 2.6, 2)));
    return [B[0] + (x * c + z * sn) * s, B[1] + y * s];
  };
  const R = [[0.55, -0.18], [1.3, 0.18 - sh * 0.5], [1.92, 0.62 - sh], [2.0, 1.35 - sh * 0.6], [1.86, 2.3], [1.66, 3.7], [1.8, 4.9], [2.05, len]];
  const right = R.map(([x, y]) => X(x, y));
  const left = R.map(([x, y]) => X(-x, y));
  return { X, right, left };
}

function drawTorso(ctx, B, s, st, Lt, o) {
  const by = o.by || 0, sh = o.shoulder || 0, len = o.len || 9;
  const cl = st.cloth;
  const { X, right, left } = torsoPts(B, s, by, sh, len);
  const lw = (Lt.lineW || 1) * s * 0.02;
  const side = Lt.side || -1;
  const outline = [...left.slice().reverse(), ...right];
  // body base
  ctx.save();
  ctx.beginPath();
  L.crPath(ctx, outline, false, 0.45);
  ctx.closePath();
  ctx.fillStyle = lit(cl.tunic, Lt);
  ctx.fill();
  ctx.clip();
  // shadow side
  const mid = X(-side * 1.25, 0);
  const g = ctx.createLinearGradient(mid[0] + side * s * 0.5, 0, mid[0] - side * s * 0.1, 0);
  g.addColorStop(0, rgba(shd(cl.tunic, Lt), 0));
  g.addColorStop(1, rgba(shd(cl.tunic, Lt), 0.92));
  ctx.fillStyle = g;
  ctx.fillRect(B[0] - 20 * s, B[1] - 4 * s, 40 * s, 30 * s);
  // chin/head shadow on chest
  ctx.fillStyle = L.radial(ctx, B[0], B[1] + s * 0.3, 0, s * 1.6, [[0, rgba(shd(cl.tunic, Lt), 0.9)], [1, rgba(shd(cl.tunic, Lt), 0)]]);
  ctx.fillRect(B[0] - s * 2, B[1] - s, s * 4, s * 3);
  // neckline
  const skin = lit(st.skin, Lt), skinSh = L.mul(st.skinShadow, Lt.amb || '#fff');
  if (cl.neck === 'v') {
    const p = [X(-0.62, -0.3), X(0, 1.7), X(0.62, -0.3)];
    ctx.beginPath(); ctx.moveTo(...p[0]); ctx.lineTo(...p[1]); ctx.lineTo(...p[2]); ctx.closePath();
    ctx.fillStyle = skinSh; ctx.fill();
    L.strokeSmooth(ctx, [X(-0.75, -0.25), X(-0.05, 1.8)], rgba(st.line, 0.9), lw);
    L.strokeSmooth(ctx, [X(0.75, -0.25), X(0.05, 1.8)], rgba(st.line, 0.9), lw);
    // collarbone hint
    L.strokeSmooth(ctx, [X(-0.5, 0.35), X(-0.15, 0.55)], rgba(st.line, 0.35), lw * 0.7);
  } else {
    const p = [X(-0.7, -0.3), X(-0.45, 0.35), X(0, 0.5), X(0.45, 0.35), X(0.7, -0.3)];
    ctx.beginPath(); L.crPath(ctx, p, false); ctx.closePath(); ctx.fillStyle = skinSh; ctx.fill();
    L.strokeSmooth(ctx, p, rgba(st.line, 0.9), lw);
    L.strokeSmooth(ctx, [X(-0.82, -0.25), X(-0.55, 0.48), X(0, 0.66), X(0.55, 0.48), X(0.82, -0.25)], rgba(shade(cl.tunic, 0.5), 0.8), lw * 1.6);
  }
  // armor (guard)
  if (cl.armor) {
    const m = st.metal || '#8a8d92';
    for (let i = 0; i < 5; i++) {
      const y = 1.0 + i * 0.75;
      const band = [X(-2.4, y), X(-1.2, y + 0.18), X(0, y + 0.22), X(1.2, y + 0.18), X(2.4, y)];
      const band2 = [X(2.4, y + 0.7), X(1.2, y + 0.88), X(0, y + 0.92), X(-1.2, y + 0.88), X(-2.4, y + 0.7)];
      ctx.beginPath(); L.crPath(ctx, band, false); ctx.lineTo(...band2[0]); L.crPath({ moveTo() {}, bezierCurveTo: (...a) => ctx.bezierCurveTo(...a) }, band2, false); ctx.closePath();
      ctx.fillStyle = i % 2 ? lit(m, Lt) : lit(shade(m, 0.85), Lt); ctx.fill();
      ctx.strokeStyle = rgba(st.line, 0.8); ctx.lineWidth = lw * 0.8; ctx.stroke();
    }
    const sp = [X(-2.3, 0.55), X(-1.6, 0.2), X(-1.0, 0.25), X(-1.4, 1.2), X(-2.4, 1.3)];
    for (const mirror of [1, -1]) {
      const pts = sp.map((p, i) => mirror > 0 ? p : X(-[[-2.3, 0.55], [-1.6, 0.2], [-1.0, 0.25], [-1.4, 1.2], [-2.4, 1.3]][i][0], [[-2.3, 0.55], [-1.6, 0.2], [-1.0, 0.25], [-1.4, 1.2], [-2.4, 1.3]][i][1]));
      ctx.beginPath(); L.crPath(ctx, pts, true); ctx.fillStyle = lit(shade(m, 1.1), Lt); ctx.fill(); ctx.strokeStyle = rgba(st.line, 0.8); ctx.stroke();
    }
  }
  // mantle draped over one shoulder (screen side o.mantleSide)
  if (cl.mantle && !cl.armor) {
    const ms = o.mantleSide || 1;
    const pts = [X(ms * 0.8, -0.3), X(ms * 1.7, 0.15), X(ms * 2.45, 0.8), X(ms * 2.5, 2.4), X(ms * 2.2, 5.0), X(ms * 1.2, 6.2),
      X(-ms * 0.4, 6.0), X(-ms * 1.2, 5.2), X(-ms * 1.9, 4.6), X(-ms * 1.0, 3.6), X(ms * 0.2, 2.2), X(ms * 0.6, 0.6)];
    ctx.beginPath(); L.crPath(ctx, pts, true, 0.45);
    ctx.fillStyle = lit(cl.mantle, Lt); ctx.fill();
    ctx.save(); ctx.clip();
    ctx.fillStyle = shd(cl.mantle, Lt);
    if (side < 0) ctx.fillRect(X(ms * 1.4, 0)[0] - (ms > 0 ? 0 : 0), B[1] - 4 * s, 20 * s, 30 * s); else ctx.fillRect(X(ms * 1.4, 0)[0] - 20 * s, B[1] - 4 * s, 20 * s, 30 * s);
    // fold lines
    for (let i = 0; i < 4; i++) {
      const a = X(ms * (0.9 + i * 0.35), 0.5 + i * 0.3), b = X(ms * (0.2 - i * 0.5), 3.4 + i * 0.6), m2 = X(ms * (0.9 - i * 0.1), 2.0 + i * 0.4);
      L.strokeSmooth(ctx, [a, m2, b], rgba(shade(cl.mantle, 0.45), 0.7), lw * 0.8);
    }
    ctx.restore();
    ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.stroke();
    if (cl.trim) {
      L.strokeSmooth(ctx, [X(ms * 0.62, 0.55), X(ms * 0.25, 2.2), X(-ms * 0.9, 3.6), X(-ms * 1.85, 4.55)], lit(cl.trim, Lt), s * 0.1);
    }
  }
  // tunic folds
  for (let i = 0; i < 5; i++) {
    const x = -1.6 + i * 0.8;
    const a = X(x * 0.6, 1.2 + (i % 2) * 0.4), b = X(x, 4.5 + (i % 3) * 0.6);
    L.strokeSmooth(ctx, [a, b], rgba(shade(cl.tunic, 0.5), 0.45), lw * 0.7);
  }
  // belt
  if (o.belt !== false && len > 4.5) {
    const bp = [X(-1.95, 4.0), X(0, 4.2), X(1.95, 4.0)];
    L.strokeSmooth(ctx, bp, lit(cl.trim || '#3a2a20', Lt), s * 0.32);
  }
  ctx.restore();
  // outline
  ctx.beginPath();
  L.crPath(ctx, outline, false, 0.45);
  ctx.strokeStyle = st.line; ctx.lineWidth = lw * 1.1; ctx.lineJoin = 'round'; ctx.stroke();
  // rim light on body
  if (Lt.rim && (Lt.rimA || 0) > 0) {
    const pts = Lt.rimSide > 0 ? right : left;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    L.strokeSmooth(ctx, pts.slice(1, 6), rgba(Lt.rim, Lt.rimA * 0.8), s * 0.06);
    ctx.restore();
  }
  return { X, right, left, shoulderR: X(1.68, 0.85 - sh), shoulderL: X(-1.68, 0.85 - sh) };
}

// ---------------------------------------------------------------- arms
function ik(S, W, l1, l2, bend) {
  let dx = W[0] - S[0], dy = W[1] - S[1];
  let d = Math.hypot(dx, dy);
  const maxd = (l1 + l2) * 0.999;
  if (d > maxd) { W = [S[0] + dx / d * maxd, S[1] + dy / d * maxd]; dx = W[0] - S[0]; dy = W[1] - S[1]; d = maxd; }
  const a = Math.atan2(dy, dx);
  const cosA = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1);
  const A = Math.acos(cosA) * bend;
  const E = [S[0] + Math.cos(a + A) * l1, S[1] + Math.sin(a + A) * l1];
  return { E, W };
}

function armJoint(S, W, l1, l2, side, out = 0) {
  // Two solutions blended smoothly: a "hanging elbow" (forearm foreshortens toward the
  // camera) for hands held near the body, and plain IK for reaching/raised arms.
  // The blend weight is continuous, so breathing or small target changes never make
  // the elbow jump between solutions.
  const dx = W[0] - S[0], dy = W[1] - S[1];
  const d = Math.hypot(dx, dy) || 1;
  const sol = ik(S, W, l1, l2, side);
  const dir = [dx / d, dy / d];
  let ux = lerp(0, dir[0], 0.42) + side * (0.04 + out), uy = lerp(1, dir[1], 0.42);
  const ul = Math.hypot(ux, uy); ux /= ul; uy /= ul;
  let E = [S[0] + ux * l1 * 0.92, S[1] + uy * l1 * 0.92];
  const fd = Math.hypot(sol.W[0] - E[0], sol.W[1] - E[1]);
  if (fd > l2) {
    const k = (fd - l2) / fd;
    E = [E[0] + (sol.W[0] - E[0]) * k, E[1] + (sol.W[1] - E[1]) * k];
  }
  const wReach = smooth((d - (l1 + l2 * 0.4)) / (l2 * 0.35));
  const wRaise = smooth((-dy / l1 - 0.05) / 0.3);
  const w = Math.max(wReach, wRaise);
  return { E: [lerp(E[0], sol.E[0], w), lerp(E[1], sol.E[1], w)], W: sol.W };
}

function drawArm(ctx, S, W, s, st, Lt, o) {
  const l1 = 2.85 * s, l2 = 2.5 * s;
  const { E, W: W2 } = armJoint(S, W, l1, l2, o.bend || 1, o.out || 0);
  const col = o.sleeve || st.cloth.tunic;
  const lw = (Lt.lineW || 1) * s * 0.02;
  // sleeve polygon along S->E->W with widths
  const seg = (A, B2, wa, wb) => {
    const dx = B2[0] - A[0], dy = B2[1] - A[1], d = Math.hypot(dx, dy) || 1;
    const nx = -dy / d, ny = dx / d;
    return [[A[0] + nx * wa, A[1] + ny * wa], [B2[0] + nx * wb, B2[1] + ny * wb], [B2[0] - nx * wb, B2[1] - ny * wb], [A[0] - nx * wa, A[1] - ny * wa]];
  };
  const wS = 0.55 * s, wE = 0.44 * s, wW = (o.loose == null ? 0.56 : o.loose) * s;
  const a = seg(S, E, wS, wE), b = seg(E, W2, wE, wW);
  const poly = [a[0], a[1], b[1], b[2], a[2], a[3]];
  ctx.beginPath();
  L.crPath(ctx, poly, true, 0.25);
  ctx.fillStyle = o.dark ? shd(col, Lt) : lit(col, Lt);
  ctx.fill();
  ctx.save(); ctx.clip();
  // shading strip on the lower side
  ctx.strokeStyle = rgba(shd(col, Lt), 0.55);
  ctx.lineWidth = s * 0.3;
  ctx.beginPath(); ctx.moveTo(a[3][0], a[3][1]); ctx.lineTo(E[0], E[1]); ctx.lineTo(b[2][0], b[2][1]); ctx.stroke();
  // elbow folds
  L.strokeSmooth(ctx, [[E[0] - s * 0.25, E[1] - s * 0.1], [E[0], E[1] + s * 0.05], [E[0] + s * 0.25, E[1] - s * 0.05]], rgba(shade(col, 0.45), 0.7), lw * 0.8);
  ctx.restore();
  ctx.strokeStyle = st.line; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke();
  // cuff edge
  const ang = Math.atan2(W2[1] - E[1], W2[0] - E[0]);
  ctx.strokeStyle = rgba(shd(shade(col, 0.7), Lt), 0.9);
  ctx.lineWidth = s * 0.12;
  ctx.beginPath(); ctx.moveTo(b[1][0], b[1][1]); ctx.lineTo(b[2][0], b[2][1]); ctx.stroke();
  if (o.hand !== false) drawHand(ctx, W2, ang + (o.handRot || 0), s, st, Lt, o.hand || 'relax', o.mirror || 1);
  if (o.shackle) drawShackle(ctx, W2, ang, s, Lt);
  return { E, W: W2, ang };
}

// stylised anime hand drawn as a clean silhouette. ang: forearm direction.
// pose: relax/open/offer/hold/fist/grip/point/cup/knock
const HANDS = {
  open: { sil: [[0, -0.34], [0.35, -0.4], [0.5, -0.5], [0.92, -0.8], [1.04, -0.7], [0.78, -0.4], [1.62, -0.36], [1.78, -0.24], [1.86, -0.04], [1.8, 0.15], [1.58, 0.32], [1.44, 0.4], [0.82, 0.42], [0, 0.36]],
    lines: [[[0.98, -0.2], [1.72, -0.2]], [[1.0, -0.02], [1.8, 0.0]], [[0.98, 0.18], [1.62, 0.2]]] },
  relax: { sil: [[0, -0.34], [0.62, -0.42], [1.08, -0.38], [1.38, -0.2], [1.46, 0.04], [1.36, 0.26], [1.12, 0.4], [0.62, 0.42], [0, 0.36]],
    lines: [[[0.95, -0.24], [1.3, -0.12], [1.36, 0.02]], [[0.98, -0.04], [1.28, 0.08], [1.3, 0.2]], [[0.95, 0.16], [1.16, 0.28]]],
    thumb: [[0.3, -0.36], [0.7, -0.52], [0.98, -0.42]] },
  fist: { sil: [[0, -0.36], [0.55, -0.44], [0.98, -0.42], [1.2, -0.28], [1.26, -0.04], [1.22, 0.2], [1.08, 0.38], [0.72, 0.44], [0, 0.38]],
    lines: [[[1.02, -0.3], [1.14, -0.16]], [[1.06, -0.08], [1.16, 0.06]], [[1.02, 0.12], [1.1, 0.26]]],
    thumb: [[0.32, -0.4], [0.78, -0.36], [1.02, -0.12]] },
};
HANDS.hold = HANDS.fist; HANDS.grip = HANDS.fist; HANDS.knock = HANDS.fist; HANDS.point = HANDS.relax;
HANDS.offer = HANDS.open; HANDS.cup = HANDS.relax;
function drawHand(ctx, W, ang, s, st, Lt, pose, mirror = 1) {
  const skin = lit(st.skin, Lt), skinSh = L.mul(st.skinShadow, Lt.amb || '#fff');
  const lw = (Lt.lineW || 1) * s * 0.02;
  const h = HANDS[pose] || HANDS.relax;
  ctx.save();
  ctx.translate(W[0], W[1]);
  ctx.rotate(ang);
  ctx.scale(s * 0.8, s * 0.8 * mirror);
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.beginPath(); L.crPath(ctx, h.sil, true, 0.45);
  ctx.fillStyle = skin; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = rgba(skinSh, 0.55);
  ctx.beginPath(); ctx.ellipse(0.6, 0.42, 1.2, 0.2, 0, 0, L.TAU); ctx.fill();
  ctx.restore();
  ctx.beginPath(); L.crPath(ctx, h.sil, true, 0.45);
  ctx.lineWidth = lw / s * 0.95; ctx.strokeStyle = st.line; ctx.stroke();
  for (const ln of h.lines) { ctx.beginPath(); L.crPath(ctx, ln, false); ctx.strokeStyle = rgba(st.line, 0.6); ctx.lineWidth = lw / s * 0.7; ctx.stroke(); }
  if (h.thumb) { ctx.beginPath(); L.crPath(ctx, h.thumb, false); ctx.strokeStyle = rgba(st.line, 0.85); ctx.lineWidth = lw / s * 0.85; ctx.stroke(); }
  ctx.restore();
}
function drawShackle(ctx, W, ang, s, Lt) {
  const c = lit('#5d5a58', Lt);
  ctx.save();
  ctx.translate(W[0], W[1]); ctx.rotate(ang);
  ctx.fillStyle = c; ctx.strokeStyle = '#1a1614'; ctx.lineWidth = s * 0.04;
  ctx.beginPath(); ctx.ellipse(-s * 0.15, 0, s * 0.22, s * 0.58, 0, 0, L.TAU); ctx.fill(); ctx.stroke();
  ctx.fillStyle = rgba('#ffffff', 0.25);
  ctx.beginPath(); ctx.ellipse(-s * 0.2, -s * 0.3, s * 0.07, s * 0.16, 0, 0, L.TAU); ctx.fill();
  ctx.restore();
}

// ---------------------------------------------------------------- props
// round country loaf: domed crust, three baked score cuts (clipped to the loaf), flour dust
function loafPath(ctx, r) {
  ctx.beginPath();
  ctx.moveTo(-r, r * 0.12);
  ctx.bezierCurveTo(-r * 1.02, -r * 0.42, -r * 0.55, -r * 0.72, 0, -r * 0.72);
  ctx.bezierCurveTo(r * 0.55, -r * 0.72, r * 1.02, -r * 0.42, r, r * 0.12);
  ctx.bezierCurveTo(r * 0.92, r * 0.42, -r * 0.92, r * 0.42, -r, r * 0.12);
  ctx.closePath();
}
function drawBread(ctx, x, y, r, Lt, o = {}) {
  const amb = Lt.amb || '#fff';
  const crustTop = L.mul('#c98a3e', Lt.key || '#fff'), crust = L.mul('#a8642a', Lt.key || '#fff'), crustD = L.mul('#6e3a16', amb);
  ctx.save();
  ctx.translate(x, y); ctx.rotate(o.rot || 0);
  // contact shadow
  ctx.fillStyle = rgba('#000000', 0.25);
  L.ellipse(ctx, 0, r * 0.36, r * 0.95, r * 0.12); ctx.fill();
  loafPath(ctx, r);
  ctx.fillStyle = L.linear(ctx, 0, -r * 0.75, 0, r * 0.4, [[0, crustTop], [0.55, crust], [1, crustD]]);
  ctx.fill();
  ctx.save();
  loafPath(ctx, r);
  ctx.clip();
  // soft dome highlight
  ctx.fillStyle = L.radial(ctx, -r * 0.3, -r * 0.45, r * 0.05, r * 0.9, [[0, rgba('#ffe2a8', 0.55)], [1, rgba('#ffe2a8', 0)]]);
  ctx.fillRect(-r * 1.2, -r, r * 2.4, r * 1.6);
  // baked score cuts: torn-open slashes showing paler crumb, with darker scorched lips
  for (const [cx, cy, ang, len] of [[-0.42, -0.22, -0.55, 0.62], [0.0, -0.32, -0.55, 0.7], [0.42, -0.22, -0.55, 0.62]]) {
    ctx.save();
    ctx.translate(cx * r, cy * r);
    ctx.rotate(ang);
    const L2 = len * r, W2 = r * 0.075;
    ctx.fillStyle = L.mul('#f0d39a', Lt.key || '#fff');
    ctx.beginPath(); ctx.ellipse(0, 0, L2 / 2, W2, 0, 0, L.TAU); ctx.fill();
    ctx.strokeStyle = rgba(L.mul('#7a4018', amb), 0.85);
    ctx.lineWidth = r * 0.035;
    ctx.beginPath(); ctx.ellipse(0, -W2 * 0.35, L2 / 2, W2 * 0.9, 0, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
    ctx.restore();
  }
  // flour dusting
  for (let i = 0; i < 26; i++) {
    const px = (L.hash01(i * 7 + 3) - 0.5) * 1.6 * r, py = -r * 0.62 + L.hash01(i * 13 + 1) * r * 0.55;
    ctx.fillStyle = rgba('#fff6e6', 0.28 + 0.25 * L.hash01(i * 5));
    ctx.beginPath(); ctx.arc(px, py, r * (0.012 + 0.018 * L.hash01(i * 11)), 0, L.TAU); ctx.fill();
  }
  ctx.restore();
  loafPath(ctx, r);
  ctx.strokeStyle = '#3a1e0c'; ctx.lineWidth = r * 0.035; ctx.stroke();
  ctx.restore();
}
// half of a torn loaf: crust shell with a score cut, and a soft, holey crumb face where it tore
function drawHalfBread(ctx, x, y, r, Lt, o = {}) {
  const f = o.face || 1;
  const amb = Lt.amb || '#fff';
  const crustTop = L.mul('#c98a3e', Lt.key || '#fff'), crust = L.mul('#a8642a', Lt.key || '#fff'), crustD = L.mul('#6e3a16', amb);
  const crumb = L.mul('#f2dfb6', Lt.key || '#fff'), crumbD = L.mul('#d2b47e', amb);
  ctx.save();
  ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.scale(f, 1);
  // irregular torn edge along x ~ 0
  const tear = [];
  for (let i = 0; i <= 9; i++) {
    const t = i / 9;
    tear.push([r * (0.06 + 0.07 * Math.sin(i * 2.1 + 0.5) + 0.04 * L.hash(i * 17)), -r * 0.68 + t * r * 1.04]);
  }
  // crust shell (left half of a dome)
  const shell = () => {
    ctx.beginPath();
    ctx.moveTo(tear[0][0], tear[0][1]);
    ctx.bezierCurveTo(-r * 0.55, -r * 0.74, -r * 1.02, -r * 0.42, -r, r * 0.12);
    ctx.bezierCurveTo(-r * 0.92, r * 0.4, -r * 0.3, r * 0.42, tear[tear.length - 1][0], tear[tear.length - 1][1]);
    for (let i = tear.length - 1; i >= 0; i--) ctx.lineTo(tear[i][0], tear[i][1]);
    ctx.closePath();
  };
  shell();
  ctx.fillStyle = L.linear(ctx, 0, -r * 0.75, 0, r * 0.4, [[0, crustTop], [0.55, crust], [1, crustD]]);
  ctx.fill();
  ctx.save();
  shell(); ctx.clip();
  ctx.fillStyle = L.radial(ctx, -r * 0.45, -r * 0.45, r * 0.05, r * 0.8, [[0, rgba('#ffe2a8', 0.5)], [1, rgba('#ffe2a8', 0)]]);
  ctx.fillRect(-r * 1.2, -r, r * 1.4, r * 1.6);
  // one score cut on the crust
  ctx.translate(-r * 0.45, -r * 0.3); ctx.rotate(-0.55);
  ctx.fillStyle = L.mul('#f0d39a', Lt.key || '#fff');
  ctx.beginPath(); ctx.ellipse(0, 0, r * 0.3, r * 0.07, 0, 0, L.TAU); ctx.fill();
  ctx.strokeStyle = rgba(L.mul('#7a4018', amb), 0.85); ctx.lineWidth = r * 0.035;
  ctx.beginPath(); ctx.ellipse(0, -r * 0.025, r * 0.3, r * 0.065, 0, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
  ctx.restore();
  shell();
  ctx.strokeStyle = '#3a1e0c'; ctx.lineWidth = r * 0.035; ctx.stroke();
  // crumb face, seen slightly from the side: a soft lens bulging out of the tear
  const face = () => {
    ctx.beginPath();
    ctx.moveTo(tear[0][0], tear[0][1]);
    ctx.bezierCurveTo(r * 0.42, -r * 0.5, r * 0.44, r * 0.18, tear[tear.length - 1][0], tear[tear.length - 1][1]);
    for (let i = tear.length - 1; i >= 0; i--) ctx.lineTo(tear[i][0], tear[i][1]);
    ctx.closePath();
  };
  face();
  ctx.fillStyle = L.linear(ctx, 0, -r * 0.6, r * 0.3, r * 0.3, [[0, crumb], [1, crumbD]]);
  ctx.fill();
  ctx.save();
  face(); ctx.clip();
  // airy crumb holes and torn fibres
  for (let i = 0; i < 16; i++) {
    const hx = r * (0.1 + 0.26 * L.hash01(i * 7 + 2)), hy = -r * 0.55 + r * 0.85 * L.hash01(i * 3 + 9);
    ctx.fillStyle = rgba(L.mul('#b8935a', amb), 0.55);
    ctx.beginPath(); ctx.ellipse(hx, hy, r * (0.018 + 0.03 * L.hash01(i * 5)), r * (0.012 + 0.02 * L.hash01(i * 9)), 0.4, 0, L.TAU); ctx.fill();
  }
  ctx.restore();
  face();
  ctx.strokeStyle = rgba('#7a5a30', 0.9); ctx.lineWidth = r * 0.03; ctx.stroke();
  // thin crust rim visible along the tear
  ctx.strokeStyle = crustD; ctx.lineWidth = r * 0.045;
  ctx.beginPath(); ctx.moveTo(tear[0][0], tear[0][1]); for (const p of tear) ctx.lineTo(p[0], p[1]); ctx.stroke();
  ctx.restore();
}
function drawJar(ctx, x, y, h, Lt) {
  const c = lit('#a4583a', Lt), d = L.mul('#6a321e', Lt.amb || '#fff');
  ctx.save(); ctx.translate(x, y);
  const pts = [[-0.18, -1], [-0.22, -0.82], [-0.45, -0.55], [-0.5, -0.1], [-0.36, 0.3], [-0.2, 0.42], [0.2, 0.42], [0.36, 0.3], [0.5, -0.1], [0.45, -0.55], [0.22, -0.82], [0.18, -1]].map(([a, b]) => [a * h, b * h]);
  ctx.beginPath(); L.crPath(ctx, pts, true, 0.4); ctx.fillStyle = c; ctx.fill();
  ctx.save(); ctx.clip(); ctx.fillStyle = d; ctx.fillRect(h * 0.1, -h * 1.2, h, h * 2); ctx.restore();
  ctx.strokeStyle = '#2a140c'; ctx.lineWidth = h * 0.025; ctx.stroke();
  ctx.strokeStyle = rgba('#e0b090', 0.5); ctx.lineWidth = h * 0.03;
  ctx.beginPath(); ctx.ellipse(0, -h * 0.35, h * 0.47, h * 0.06, 0, 0, Math.PI); ctx.stroke();
  ctx.fillStyle = '#2a140c'; L.ellipse(ctx, 0, -h, h * 0.18, h * 0.05); ctx.fill();
  ctx.restore();
}
function drawChain(ctx, a, b, s, Lt, sag = 1.0, links = 14) {
  const c = lit('#4e4a48', Lt);
  ctx.save();
  ctx.strokeStyle = c; ctx.lineWidth = s * 0.06;
  for (let i = 0; i < links; i++) {
    const t = (i + 0.5) / links;
    const x = lerp(a[0], b[0], t), y = lerp(a[1], b[1], t) + Math.sin(t * Math.PI) * sag * s;
    const t2 = (i + 1.5) / links;
    const x2 = lerp(a[0], b[0], t2), y2 = lerp(a[1], b[1], t2) + Math.sin(t2 * Math.PI) * sag * s;
    const ang = Math.atan2(y2 - y, x2 - x);
    ctx.beginPath();
    ctx.ellipse(x, y, s * 0.2, i % 2 ? s * 0.05 : s * 0.11, ang, 0, L.TAU);
    ctx.stroke();
  }
  ctx.restore();
}
function drawScroll(ctx, x, y, w, h, Lt, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0);
  const paper = lit('#e8d9b5', Lt);
  ctx.fillStyle = paper;
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.fillStyle = rgba(L.mul('#b49a6e', Lt.amb || '#fff'), 0.5);
  ctx.fillRect(-w / 2, -h / 2, w * 0.08, h);
  ctx.fillRect(w / 2 - w * 0.08, -h / 2, w * 0.08, h);
  // text lines
  ctx.strokeStyle = rgba('#3a2a1a', 0.55); ctx.lineWidth = h * 0.02;
  for (let i = 0; i < 9; i++) {
    const yy = -h * 0.38 + i * h * 0.09;
    ctx.beginPath();
    let xx = -w * 0.36;
    while (xx < w * 0.36) { const ww = w * (0.03 + 0.05 * L.hash01(i * 31 + Math.floor(xx))); ctx.moveTo(xx, yy); ctx.lineTo(Math.min(xx + ww, w * 0.36), yy); xx += ww + w * 0.025; }
    ctx.stroke();
  }
  // rollers
  for (const sx of [-1, 1]) {
    ctx.fillStyle = lit('#6a4428', Lt);
    ctx.fillRect(sx * w / 2 - w * 0.05, -h * 0.6, w * 0.1, h * 1.2);
    ctx.strokeStyle = '#2a1a10'; ctx.lineWidth = w * 0.01; ctx.strokeRect(sx * w / 2 - w * 0.05, -h * 0.6, w * 0.1, h * 1.2);
  }
  ctx.restore();
}
function drawTorch(ctx, x, y, s, t, Lt, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  ctx.fillStyle = lit('#4a3020', Lt);
  ctx.beginPath(); ctx.moveTo(-s * 0.12, 0); ctx.lineTo(s * 0.12, 0); ctx.lineTo(s * 0.08, s * 2.2); ctx.lineTo(-s * 0.08, s * 2.2); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#2a1a10'; ctx.fillRect(-s * 0.2, -s * 0.15, s * 0.4, s * 0.35);
  drawFlame(ctx, 0, -s * 0.1, s * (o.size || 1), t, o.seed || 0);
  ctx.restore();
}
function drawFlame(ctx, x, y, s, t, seed = 0) {
  ctx.save();
  ctx.translate(x, y);
  const n1 = L.fbm1(t * 3.1 + seed, seed + 3), n2 = L.fbm1(t * 4.3 + seed * 2, seed + 7);
  ctx.globalCompositeOperation = 'lighter';
  L.glow(ctx, 0, -s * 0.5, s * 3.2, '#ff8a2a', 0.35 + 0.08 * n1);
  const layers = [['#ff5a10', 1.0], ['#ffa030', 0.75], ['#fff0b0', 0.42]];
  for (const [c, k] of layers) {
    const h = s * (1.5 + 0.35 * n1) * k, w = s * 0.42 * k * (1 + 0.1 * n2);
    ctx.fillStyle = rgba(c, 0.85);
    ctx.beginPath();
    ctx.moveTo(-w, 0);
    ctx.quadraticCurveTo(-w * 1.1, -h * 0.45, n2 * s * 0.15, -h);
    ctx.quadraticCurveTo(w * 1.1, -h * 0.45, w, 0);
    ctx.quadraticCurveTo(0, w * 0.6, -w, 0);
    ctx.fill();
  }
  ctx.restore();
}
function drawCup(ctx, x, y, h, Lt) {
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = lit('#9a6a3a', Lt);
  ctx.beginPath(); ctx.moveTo(-h * 0.45, -h); ctx.quadraticCurveTo(-h * 0.4, -h * 0.2, -h * 0.1, -h * 0.1); ctx.lineTo(-h * 0.08, h * 0.3); ctx.lineTo(-h * 0.3, h * 0.42); ctx.lineTo(h * 0.3, h * 0.42); ctx.lineTo(h * 0.08, h * 0.3); ctx.lineTo(h * 0.1, -h * 0.1); ctx.quadraticCurveTo(h * 0.4, -h * 0.2, h * 0.45, -h); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#2a1a10'; ctx.lineWidth = h * 0.03; ctx.stroke();
  ctx.fillStyle = '#4a1a24'; L.ellipse(ctx, 0, -h, h * 0.45, h * 0.1); ctx.fill(); ctx.stroke();
  ctx.restore();
}

module.exports = { armJoint, drawTorso, drawArm, drawHand, drawBread, drawHalfBread, drawJar, drawChain, drawScroll, drawTorch, drawFlame, drawCup, drawShackle, ik, torsoPts };
