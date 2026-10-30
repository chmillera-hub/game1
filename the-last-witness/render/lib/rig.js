// Procedural 2.5D character rig: head (yaw/pitch/roll), eyes with lids and gaze, brows,
// lip-synced mouth, neck with sternocleidomastoids, torso, sleeves with IK arms, and hands.
// Units: the head height is 1; st.s is the head height in pixels.
'use strict';
const U = require('./util');
const { clamp, lerp, smooth, rgba, mix, shade } = U;

// ---------------------------------------------------------------- path helpers
function smoothPath(ctx, pts, closed = true) {
  // quadratic curves through midpoints: a smooth closed outline through point list
  const n = pts.length;
  if (n < 3) return;
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  if (closed) {
    let m = mid(pts[n - 1], pts[0]);
    ctx.moveTo(m[0], m[1]);
    for (let i = 0; i < n; i++) {
      const p = pts[i], q = pts[(i + 1) % n], mm = mid(p, q);
      ctx.quadraticCurveTo(p[0], p[1], mm[0], mm[1]);
    }
    ctx.closePath();
  } else {
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < n - 1; i++) {
      const mm = mid(pts[i], pts[i + 1]);
      ctx.quadraticCurveTo(pts[i][0], pts[i][1], mm[0], mm[1]);
    }
    ctx.lineTo(pts[n - 1][0], pts[n - 1][1]);
  }
}

// filled tapered stroke along a polyline (for brows, lashes, strands)
function taper(ctx, pts, w0, w1, wMid = null) {
  const n = pts.length;
  const left = [], right = [];
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1];
    const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
    const u = i / (n - 1);
    let w = wMid != null ? (u < 0.5 ? lerp(w0, wMid, u * 2) : lerp(wMid, w1, (u - 0.5) * 2)) : lerp(w0, w1, u);
    w /= 2;
    left.push([pts[i][0] - dy * w, pts[i][1] + dx * w]);
    right.push([pts[i][0] + dy * w, pts[i][1] - dx * w]);
  }
  ctx.beginPath();
  ctx.moveTo(left[0][0], left[0][1]);
  for (let i = 1; i < n; i++) ctx.lineTo(left[i][0], left[i][1]);
  for (let i = n - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]);
  ctx.closePath();
}

function bez(p0, c0, c1, p1, n = 10) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, mt = 1 - t;
    out.push([
      mt * mt * mt * p0[0] + 3 * mt * mt * t * c0[0] + 3 * mt * t * t * c1[0] + t * t * t * p1[0],
      mt * mt * mt * p0[1] + 3 * mt * mt * t * c0[1] + 3 * mt * t * t * c1[1] + t * t * t * p1[1],
    ]);
  }
  return out;
}
function quadPts(p0, c, p1, n = 10) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, mt = 1 - t;
    out.push([mt * mt * p0[0] + 2 * mt * t * c[0] + t * t * p1[0], mt * mt * p0[1] + 2 * mt * t * c[1] + t * t * p1[1]]);
  }
  return out;
}
function poly(ctx, pts) { ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); }

// ---------------------------------------------------------------- head shape
// half-width of the head silhouette at height y (head-local), before yaw warping
function headHalfWidth(y, ch) {
  const W = ch.headW / 2;
  const top = -0.56, chin = 0.45;
  if (y <= top) return 0;
  if (y < -0.2) { // cranium: ellipse
    const u = (y - (-0.2)) / (top - (-0.2));
    return W * Math.sqrt(Math.max(0, 1 - u * u));
  }
  if (y < 0.1) return W * lerp(1, 0.95, (y + 0.2) / 0.3);
  if (y < 0.3) return W * lerp(0.95, ch.jaw, smooth((y - 0.1) / 0.2));
  const u = (y - 0.3) / (chin - 0.3); // jaw to chin
  return W * lerp(ch.jaw, ch.chinW, Math.pow(u, 1.3)) * Math.sqrt(Math.max(0, 1 - Math.pow(u, 6)));
}

function headOutline(ch, k) {
  // k = sin(yaw): + facing screen-right. Lower face shifts toward facing side,
  // back of skull extends on the other side, small brow/cheek contour on the facing side.
  const ys = [];
  for (let i = 0; i <= 26; i++) ys.push(-0.56 + (i / 26) * (0.45 + 0.56));
  const right = [], left = [];
  for (const y of ys) {
    const w = headHalfWidth(y, ch);
    const faceShift = k * (0.035 + 0.075 * smooth((y + 0.15) / 0.6));
    const back = Math.abs(k) * 0.07 * (1 - smooth((y + 0.05) / 0.5));
    const socket = Math.abs(k) * 0.03 * Math.exp(-Math.pow((y + 0.02) / 0.06, 2));
    const cheekb = Math.abs(k) * 0.012 * Math.exp(-Math.pow((y - 0.12) / 0.07, 2));
    let xr = w + faceShift, xl = -w + faceShift;
    if (k > 0) { xr += -socket + cheekb; xl -= back; } else { xl += socket - cheekb; xr += back; }
    right.push([xr, y]); left.push([xl, y]);
  }
  left.reverse();
  return right.concat(left);
}

// ---------------------------------------------------------------- hands
// Hand drawn in local space: wrist at origin, fingers toward -y. size = palm length.
// pose: open | relaxed | curl | fist | point | flat | cup | chin | pinch
const POSES = {
  open:    { curl: [0.05, 0.03, 0.05, 0.08], spread: 0.16, thumb: 0.55, thumbCurl: 0.1 },
  relaxed: { curl: [0.3, 0.35, 0.42, 0.48], spread: 0.06, thumb: 0.35, thumbCurl: 0.3 },
  curl:    { curl: [0.6, 0.65, 0.7, 0.72], spread: 0.03, thumb: 0.3, thumbCurl: 0.5 },
  fist:    { curl: [1, 1, 1, 1], spread: 0, thumb: 0.15, thumbCurl: 0.9 },
  point:   { curl: [0.0, 0.95, 1, 1], spread: 0.02, thumb: 0.2, thumbCurl: 0.8 },
  flat:    { curl: [0.04, 0.03, 0.04, 0.06], spread: 0.03, thumb: 0.2, thumbCurl: 0.1 },
  cup:     { curl: [0.35, 0.32, 0.36, 0.42], spread: 0.02, thumb: 0.45, thumbCurl: 0.25 },
  chin:    { curl: [0.55, 0.85, 0.95, 1], spread: 0.02, thumb: 0.35, thumbCurl: 0.3 },
};
function lerpPose(a, b, t) {
  const A = POSES[a] || POSES.relaxed, B = POSES[b] || POSES.relaxed;
  return {
    curl: A.curl.map((c, i) => lerp(c, B.curl[i], t)), spread: lerp(A.spread, B.spread, t),
    thumb: lerp(A.thumb, B.thumb, t), thumbCurl: lerp(A.thumbCurl, B.thumbCurl, t),
  };
}

function drawHand(ctx, x, y, ang, size, pose, opts) {
  // opts: {skin, shadow, outline, mirror (thumb on other side), back (show back of hand), light}
  const P = typeof pose === 'string' ? (POSES[pose] || POSES.relaxed) : pose;
  const sk = opts.skin, sh = opts.shadow, ol = opts.outline || shade(sh, -0.35);
  ctx.save();
  ctx.translate(x, y);
  if (opts.squash) ctx.scale(1, opts.squash);
  ctx.rotate(ang);
  ctx.scale(size * (opts.mirror ? -1 : 1), size);
  // palm (wrist at 0,0 ; knuckles at y = -1)
  const palm = [[-0.36, -0.05], [-0.42, -0.55], [-0.4, -0.98], [-0.14, -1.06], [0.14, -1.06], [0.38, -0.98], [0.42, -0.55], [0.32, -0.05]];
  // fingers: base x, length, width
  const F = [
    { bx: -0.29, len: 0.78, w: 0.17 }, // index (thumb side is -x)
    { bx: -0.095, len: 0.86, w: 0.175 },
    { bx: 0.1, len: 0.8, w: 0.165 },
    { bx: 0.28, len: 0.62, w: 0.145 },
  ];
  const fingerPts = F.map((f, i) => {
    const curl = P.curl[i];
    const spreadA = (i - 1.5) * P.spread;
    const pts = [[f.bx, -0.98]];
    let a = -Math.PI / 2 + spreadA, px = f.bx, py = -0.98;
    const segs = [0.45, 0.32, 0.23];
    for (let s = 0; s < 3; s++) {
      a += curl * (s === 0 ? 1.15 : 1.35) * (opts.back ? -1 : 1) * 0 + curl * (s === 0 ? 0.0 : 0) ;
      // curl bends fingers toward the palm, which in 2D foreshortens and folds them down
      const fold = curl * (s === 0 ? 0.55 : 0.95);
      const L = f.len * segs[s] * (1 - fold * 0.55);
      px += Math.cos(a) * L; py += Math.sin(a) * L;
      // curled segments drift down over the palm
      py += fold * 0.12 * (s + 1) * 0.6;
      pts.push([px, py]);
    }
    return { pts, w: f.w };
  });
  // thumb from palm side
  const tb = [-0.36, -0.32];
  const ta = -Math.PI / 2 - 0.55 - P.thumb * 0.9;
  const tc = P.thumbCurl;
  const t1 = [tb[0] + Math.cos(ta) * 0.36, tb[1] + Math.sin(ta) * 0.36];
  const ta2 = ta + 0.35 + tc * 1.2;
  const t2 = [t1[0] + Math.cos(ta2) * 0.3, t1[1] + Math.sin(ta2) * 0.3];
  const ta3 = ta2 + tc * 0.8;
  const t3 = [t2[0] + Math.cos(ta3) * 0.22, t2[1] + Math.sin(ta3) * 0.22];
  const thumb = { pts: [tb, t1, t2, t3], w: 0.2 };

  const strokeF = (f, color, extra) => {
    ctx.strokeStyle = color; ctx.lineWidth = f.w + extra; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); poly(ctx, f.pts); ctx.stroke();
  };
  const ow = 0.055;
  // 1) silhouette outline pass
  ctx.fillStyle = ol; ctx.beginPath(); smoothPath(ctx, palm); ctx.lineWidth = ow; ctx.strokeStyle = ol; ctx.stroke();
  for (const f of fingerPts) strokeF(f, ol, ow);
  strokeF(thumb, ol, ow);
  // 2) fill pass (covers internal outlines so only the silhouette stays)
  ctx.fillStyle = rgba(sk); ctx.beginPath(); smoothPath(ctx, palm); ctx.fill();
  for (const f of fingerPts) strokeF(f, rgba(sk), 0);
  strokeF(thumb, rgba(sk), 0);
  // 3) soft interior shading: blend at edges, no hard lines
  const g = ctx.createLinearGradient(-0.45, 0, 0.45, 0);
  g.addColorStop(0, rgba(sh, 0.0)); g.addColorStop(1, rgba(sh, 0.45));
  ctx.fillStyle = g; ctx.beginPath(); smoothPath(ctx, palm); ctx.fill();
  // finger separations: short soft lines in a shade of skin near the knuckles
  ctx.strokeStyle = rgba(sh, 0.55); ctx.lineWidth = 0.025;
  for (let i = 0; i < 3; i++) {
    const a = fingerPts[i].pts, b = fingerPts[i + 1].pts;
    const p = [(a[1][0] + b[1][0]) / 2, (a[1][1] + b[1][1]) / 2];
    const q = [(a[0][0] + b[0][0]) / 2, (a[0][1] + b[0][1]) / 2 - 0.02];
    ctx.beginPath(); ctx.moveTo(q[0], q[1]); ctx.lineTo(p[0], p[1]); ctx.stroke();
  }
  if (opts.back) { // knuckle highlights on the back of the hand
    ctx.fillStyle = rgba(shade(sk, 0.18), 0.5);
    for (const f of fingerPts) { ctx.beginPath(); ctx.ellipse(f.pts[0][0], f.pts[0][1] + 0.04, 0.06, 0.035, 0, 0, U.TAU); ctx.fill(); }
  } else { // palm crease
    ctx.strokeStyle = rgba(sh, 0.35); ctx.lineWidth = 0.022;
    ctx.beginPath(); ctx.moveTo(-0.3, -0.62); ctx.quadraticCurveTo(0.0, -0.5, 0.3, -0.78); ctx.stroke();
  }
  ctx.restore();
}

// ---------------------------------------------------------------- arms (two-bone IK)
function ik(sx, sy, wx, wy, l1, l2, bendSign) {
  let dx = wx - sx, dy = wy - sy;
  let d = Math.hypot(dx, dy);
  const maxD = (l1 + l2) * 0.999;
  if (d > maxD) { wx = sx + dx / d * maxD; wy = sy + dy / d * maxD; dx = wx - sx; dy = wy - sy; d = maxD; }
  d = Math.max(d, Math.abs(l1 - l2) + 1e-3);
  const a = Math.atan2(dy, dx);
  const cosB = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1);
  const b = Math.acos(cosB) * bendSign;
  return { ex: sx + Math.cos(a + b) * l1, ey: sy + Math.sin(a + b) * l1, wx, wy };
}

// gesture → per-arm targets in body units (origin: sternal notch, +x = screen right).
// side: 'fore' = arm on the side the character faces, 'back' = the other arm.
// Each: [elbowX, elbowY, wristX, wristY, handAngle, pose, backOfHand]
// handAngle 0 = fingers up; positive rotates clockwise (toward +x).
const GESTURES = {
  idle:        { fore: [0.86, 1.32, 0.55, 1.78, 2.5, 'relaxed', true], back: [-0.86, 1.32, -0.55, 1.78, -2.5, 'relaxed', true] },
  desk:        { fore: [0.86, 1.28, 0.46, 1.44, -1.75, 'relaxed', true], back: [-0.86, 1.28, -0.48, 1.46, 1.75, 'relaxed', true] },
  open_palm:   { fore: [0.84, 1.28, 0.66, 0.9, 0.38, 'open', false], back: [-0.84, 1.3, -0.46, 1.5, -1.95, 'relaxed', true] },
  both_palms:  { fore: [0.84, 1.28, 0.66, 0.92, 0.45, 'open', false], back: [-0.84, 1.28, -0.66, 0.92, -0.45, 'open', false] },
  hand_chest:  { fore: [0.74, 1.24, 0.22, 0.92, -1.15, 'flat', true], back: [-0.84, 1.3, -0.46, 1.5, -1.95, 'relaxed', true], drawForeLast: true },
  chin:        { fore: [0.5, 1.08, 0.12, 0.2, -0.12, 'chin', true], back: [-0.8, 1.28, -0.2, 1.22, -1.75, 'relaxed', true], drawForeLast: true, onFace: true },
  point_self:  { fore: [0.74, 1.24, 0.24, 0.86, -1.35, 'point', true], back: [-0.84, 1.3, -0.46, 1.5, -1.95, 'relaxed', true], drawForeLast: true },
  reach:       { fore: [1.02, 0.95, 1.38, 0.62, 1.15, 'open', false], back: [-0.84, 1.3, -0.46, 1.5, -1.95, 'relaxed', true] },
  clasp:       { fore: [0.8, 1.28, 0.1, 1.14, -1.35, 'curl', true], back: [-0.8, 1.28, -0.1, 1.2, 1.35, 'curl', true], drawForeLast: true },
  shrug:       { fore: [0.9, 1.16, 1.0, 0.86, 0.85, 'open', false], back: [-0.9, 1.16, -1.0, 0.86, -0.85, 'open', false], shoulders: 0.06 },
  fist:        { fore: [0.8, 1.26, 0.52, 0.88, 0.05, 'fist', true], back: [-0.84, 1.3, -0.46, 1.5, -1.95, 'relaxed', true] },
  wipe_tear:   { fore: [0.7, 0.98, 0.36, 0.02, -0.62, 'relaxed', true], back: [-0.84, 1.3, -0.46, 1.5, -1.95, 'relaxed', true], drawForeLast: true, onFace: true },
  head_in_hands: { fore: [0.56, 1.0, 0.22, 0.04, -0.28, 'cup', true], back: [-0.56, 1.0, -0.22, 0.04, 0.28, 'cup', true], drawForeLast: true, onFace: true, pitch: 0.5 },
  offer:       { fore: [0.78, 1.22, 0.42, 0.9, 1.3, 'cup', false], back: [-0.6, 1.26, 0.06, 0.95, 1.6, 'cup', false], orb: [0.26, 0.7], backInFront: true },
  hold_orb:    { fore: [0.78, 1.24, 0.17, 0.98, -1.35, 'cup', false], back: [-0.78, 1.24, -0.17, 0.98, 1.35, 'cup', false], orb: [0, 0.74], drawForeLast: true, backInFront: true },
  press_button:{ fore: [0.98, 1.05, 1.3, 1.22, 2.0, 'point', true], back: [-0.84, 1.3, -0.46, 1.5, -1.95, 'relaxed', true] },
  lean_in:     { fore: [0.8, 1.26, 0.38, 1.36, 1.8, 'relaxed', true], back: [-0.8, 1.26, -0.4, 1.38, -1.8, 'relaxed', true], lean: 0.25 },
  lean_back:   { fore: [0.86, 1.32, 0.55, 1.78, 2.5, 'relaxed', true], back: [-0.86, 1.32, -0.55, 1.78, -2.5, 'relaxed', true], lean: -0.2 },
  arms_wide:   { fore: [1.25, 0.62, 1.62, 0.3, 0.75, 'open', false], back: [-1.25, 0.62, -1.62, 0.3, -0.75, 'open', false] },
  stretch_yawn:{ fore: [0.88, -0.45, 0.42, -1.18, -0.3, 'relaxed', false], back: [-0.88, -0.45, -0.42, -1.18, 0.3, 'relaxed', false], yawn: true, shoulders: 0.08 },
  hands_together: { fore: [0.64, 1.12, 0.05, 0.66, -0.05, 'flat', false], back: [-0.64, 1.12, -0.05, 0.66, 0.05, 'flat', true], drawForeLast: true },
  nod:         { fore: [0.86, 1.32, 0.55, 1.78, 2.5, 'relaxed', true], back: [-0.86, 1.32, -0.55, 1.78, -2.5, 'relaxed', true] },
  shake:       { fore: [0.86, 1.32, 0.55, 1.78, 2.5, 'relaxed', true], back: [-0.86, 1.32, -0.55, 1.78, -2.5, 'relaxed', true] },
};

// ---------------------------------------------------------------- main draw
/*
 st: {
  x, y      : sternal-notch position in px;  s: head height px
  yaw       : -1..1 (+ faces screen-right);  pitch: -1..1 (+ down);  roll: rad
  bodyYaw   : torso yaw (defaults yaw*0.6);  lean: forward lean -1..1 (toward facing side)
  breath    : -1..1 breathing phase value
  e         : expression params (expr.js)
  mouth     : {open, wide, round, teeth} lip-sync viseme (added to expression)
  gaze      : {x,y} -1..1 eye direction relative to the head
  blink     : 0..1
  arms      : {fore:{x,y,a,pose,back}, back:{...}, foreFirst?}  (body units)
  light     : {key:[r,g,b], keyX:-1..1, rim:[r,g,b], rimX:-1..1, rimA, amb:[r,g,b], ambA, fill}
  tear      : 0..1 progress of a single tear (on the eye nearer camera)
  alpha
 }
*/
function drawCharacter(ctx, ch, st) {
  const s = st.s;
  const yaw = clamp(st.yaw || 0, -1, 1);
  const a = yaw * 0.62;
  const k = Math.sin(a);
  const facing = yaw >= 0 ? 1 : -1;
  const e = st.e || {};
  const L = st.light || {};
  const prop = ch.prop || {};
  const neckLen = prop.neck ?? 1;
  const bodyScale = prop.body ?? 1;
  const headScale = prop.head ?? 1;

  ctx.save();
  if (st.alpha != null && st.alpha < 1) ctx.globalAlpha = st.alpha;
  ctx.translate(st.x, st.y);
  ctx.scale(s, s);

  const breath = st.breath || 0;
  const lean = (st.lean || 0);
  const shoulderLift = (st.shoulderLift || 0) + breath * 0.008;

  // ----- torso (body space, origin = sternal notch)
  const bk = Math.sin((st.bodyYaw ?? yaw * 0.55) * 0.62);
  const shW = ch.shoulderW * bodyScale;

  // arms computed first so we can layer them
  const arms = st.arms || armsFor('idle', facing);
  const shoulderY = 0.24 - shoulderLift - (arms.shoulders || 0);
  const shL = [-shW * (1 - Math.max(0, bk) * 0.28) + bk * 0.05, shoulderY + (bk > 0 ? 0.02 : 0)];
  const shR = [shW * (1 - Math.max(0, -bk) * 0.28) + bk * 0.05, shoulderY + (bk < 0 ? 0.02 : 0)];
  const foreSh = facing > 0 ? shR : shL;
  const backSh = facing > 0 ? shL : shR;
  const mkArm = (sh, tgt, side) => {
    const sgn = sh[0] >= 0 ? 1 : -1;
    const sx = sh[0] - sgn * 0.1, sy = sh[1] + 0.1;
    const r = ch.reach ?? 1;
    return { sx, sy, ex: tgt.ex * r, ey: tgt.ey, wx: tgt.x * r, wy: tgt.y, a: tgt.a, pose: tgt.pose, back: tgt.back, squash: tgt.y > 1.3 ? 0.62 : null };
  };
  const foreArm = mkArm(foreSh, arms.fore, 'fore');
  const backArm = mkArm(backSh, arms.back, 'back');

  // ----- head transform
  const headCX = lean * 0.18 * facing + k * 0.02;
  const headCY = -(0.47 + 0.24 * neckLen) * 1 - breath * 0.004 + Math.max(0, lean) * 0.05;
  const pitch = clamp((st.pitch || 0) + (e.pitch || 0), -1, 1);
  const roll = (st.roll || 0) + (e.roll || 0) * facing;
  if (ch.hairBack) {
    ctx.save(); ctx.translate(headCX, headCY); ctx.rotate(roll); ctx.scale(headScale, headScale);
    ch.hairBack(ctx, ch, k, pitch, L, st);
    ctx.restore();
  }

  const want = (side) => (!st.armSides || st.armSides.includes(side));
  if (st.only === 'arms') {
    if (want('back')) drawArm(ctx, ch, backArm, L, 'back');
    if (want('fore')) drawArm(ctx, ch, foreArm, L, 'fore');
    if (arms.orb) drawOrb(ctx, arms.orb[0] * facing, arms.orb[1], st.orbGlow ?? 1);
    ctx.restore();
    return;
  }
  const armsOn = st.only !== 'body';
  // back arm behind torso unless explicitly in front (e.g. clasp)
  const backInFront = arms.backInFront;
  if (!backInFront && armsOn && want('back')) drawArm(ctx, ch, backArm, L, 'back');
  if (ch.lowerBody) ch.lowerBody(ctx, ch, st, bk, L);
  drawTorso(ctx, ch, shL, shR, bk, L, st);

  // neck (drawn in body space connecting to the head attachment)
  drawNeck(ctx, ch, headCX, headCY, k, pitch, roll, headScale, L, st);
  if (ch.collarOverNeck) ch.collarOverNeck(ctx, ch, shL, shR, bk, L, st);
  else drawCollar(ctx, ch, bk, L, st);

  if (backInFront && armsOn && want('back')) drawArm(ctx, ch, backArm, L, 'back');
  const foreLast = arms.drawForeLast;
  if (!foreLast && armsOn && want('fore')) drawArm(ctx, ch, foreArm, L, 'fore');

  ctx.save();
  ctx.translate(headCX, headCY);
  ctx.rotate(roll);
  ctx.scale(headScale, headScale);
  drawHead(ctx, ch, st, k, a, pitch, e, L);
  ctx.restore();

  if (foreLast && armsOn && want('fore')) drawArm(ctx, ch, foreArm, L, 'fore');
  if (arms.orb && armsOn) drawOrb(ctx, arms.orb[0] * facing, arms.orb[1], st.orbGlow ?? 1);
  if (ch.overlay) ch.overlay(ctx, ch, st, { shL, shR, bk, headCX, headCY });
  ctx.restore();
}

function armsFor(name, facing, extra = {}) {
  const g = GESTURES[name] || GESTURES.idle;
  const f = (v) => ({ ex: v[0] * facing, ey: v[1], x: v[2] * facing, y: v[3], a: v[4] * facing, pose: v[5], back: v[6] });
  return { fore: f(g.fore), back: f(g.back), drawForeLast: !!g.drawForeLast, backInFront: !!g.backInFront, orb: g.orb, ...extra };
}

function lightGrad(ctx, x0, x1, L, base, shadow, strength = 1) {
  // horizontal key-light gradient across a shape: lit on the key side, shadow on the other
  const g = ctx.createLinearGradient(x0, 0, x1, 0);
  const kx = L.keyX ?? -0.5; // -1 key from screen-left
  const lo = rgba(shadow, 0.55 * strength), hi = rgba(shadow, 0);
  if (kx < 0) { g.addColorStop(0, hi); g.addColorStop(0.55, rgba(shadow, 0.08 * strength)); g.addColorStop(1, lo); }
  else { g.addColorStop(0, lo); g.addColorStop(0.45, rgba(shadow, 0.08 * strength)); g.addColorStop(1, hi); }
  return g;
}

function rimStroke(ctx, L, width = 0.02, alpha = 1) {
  if (!L.rim || !(L.rimA > 0)) return;
  // the current path is stroked with a gradient that only shows on the rim side
  const g = ctx.createLinearGradient(-1.2, 0, 1.2, 0);
  const c = L.rim, A = L.rimA * alpha;
  if ((L.rimX ?? 1) > 0) { g.addColorStop(0, rgba(c, 0)); g.addColorStop(0.62, rgba(c, 0)); g.addColorStop(0.85, rgba(c, A)); g.addColorStop(1, rgba(c, A)); }
  else { g.addColorStop(0, rgba(c, A)); g.addColorStop(0.15, rgba(c, A)); g.addColorStop(0.38, rgba(c, 0)); g.addColorStop(1, rgba(c, 0)); }
  ctx.strokeStyle = g; ctx.lineWidth = width; ctx.stroke();
}

// ---------------------------------------------------------------- torso & clothes
function drawTorso(ctx, ch, shL, shR, bk, L, st) {
  const c = ch.cloth;
  const bodyH = ch.bodyH ?? 2.8;
  const waist = ch.waistW ?? 0.78;
  const nx = bk * 0.06;
  // neck base → trapezius slope → rounded deltoid → side → waist (and mirrored)
  const pts = [
    [-0.2 + nx, -0.03], [lerp(-0.2 + nx, shL[0], 0.55), lerp(-0.03, shL[1], 0.62) - 0.02], [shL[0] + 0.05, shL[1] - 0.03],
    [shL[0] - 0.06, shL[1] + 0.12], [shL[0] - 0.07, shL[1] + 0.42], [shL[0] + 0.02, 1.0],
    [-waist + nx, bodyH], [waist + nx, bodyH],
    [shR[0] - 0.02, 1.0], [shR[0] + 0.07, shR[1] + 0.42], [shR[0] + 0.06, shR[1] + 0.12], [shR[0] - 0.05, shR[1] - 0.03],
    [lerp(0.2 + nx, shR[0], 0.55), lerp(-0.03, shR[1], 0.62) - 0.02], [0.2 + nx, -0.03],
  ];
  ctx.save();
  ctx.beginPath(); smoothPath(ctx, pts);
  ctx.fillStyle = rgba(c.base); ctx.fill();
  ctx.save(); ctx.clip();
  if (L.amb && L.ambA) { ctx.fillStyle = rgba(L.amb, L.ambA); ctx.fillRect(-3, -1, 6, 5); }
  ctx.fillStyle = lightGrad(ctx, -1.1, 1.1, L, c.base, c.shadow, 1);
  ctx.fillRect(-3, -1, 6, 5);
  // soft shoulder/underarm shading that blends into the fabric (no hard lines)
  for (const sh of [shL, shR]) {
    const g = ctx.createRadialGradient(sh[0] * 0.92, sh[1] + 0.75, 0.05, sh[0] * 0.92, sh[1] + 0.75, 0.6);
    g.addColorStop(0, rgba(c.shadow, 0.22)); g.addColorStop(1, rgba(c.shadow, 0));
    ctx.fillStyle = g; ctx.fillRect(sh[0] - 0.8, sh[1], 1.6, 1.6);
  }
  const hg = ctx.createLinearGradient(0, -0.05, 0, 0.35);
  hg.addColorStop(0, rgba(shade(c.base, 0.12), 0.35)); hg.addColorStop(1, rgba(shade(c.base, 0.12), 0));
  ctx.fillStyle = hg; ctx.fillRect(-2, -0.1, 4, 0.5);
  // fabric folds: soft, low-contrast curves
  ctx.strokeStyle = rgba(c.shadow, 0.22); ctx.lineWidth = 0.03; ctx.lineCap = 'round';
  for (const f of (ch.folds || [[-0.36, 0.62, -0.28, 1.12, -0.4, 1.6], [0.34, 0.66, 0.24, 1.15, 0.38, 1.7], [0.02, 1.15, 0.06, 1.5, -0.02, 1.95]])) {
    ctx.beginPath(); ctx.moveTo(f[0] + nx, f[1]); ctx.quadraticCurveTo(f[2] + nx, f[3], f[4] + nx, f[5]); ctx.stroke();
  }
  if (ch.torsoDetail) ch.torsoDetail(ctx, ch, shL, shR, bk, L, st);
  ctx.restore();
  ctx.beginPath(); smoothPath(ctx, pts);
  rimStroke(ctx, L, 0.035, 0.8);
  ctx.strokeStyle = rgba(c.shadow, 0.35); ctx.lineWidth = 0.01; ctx.stroke();
  ctx.restore();
}

function drawCollar(ctx, ch, bk, L, st) {
  const c = ch.cloth;
  const type = ch.collar || 'crew';
  ctx.save();
  if (type === 'crew' || type === 'knit') {
    ctx.beginPath();
    ctx.moveTo(-0.3 + bk * 0.06, -0.07);
    ctx.quadraticCurveTo(0 + bk * 0.08, 0.2, 0.3 + bk * 0.06, -0.07);
    ctx.quadraticCurveTo(0.34 + bk * 0.06, 0.02, 0.3 + bk * 0.06, 0.05);
    ctx.quadraticCurveTo(0 + bk * 0.08, 0.3, -0.3 + bk * 0.06, 0.05);
    ctx.quadraticCurveTo(-0.34 + bk * 0.06, 0.02, -0.3 + bk * 0.06, -0.07);
    ctx.fillStyle = rgba(c.collar || shade(c.base, -0.12)); ctx.fill();
    ctx.strokeStyle = rgba(c.shadow, 0.35); ctx.lineWidth = 0.012; ctx.stroke();
  } else if (type === 'vneck') {
    ctx.beginPath();
    ctx.moveTo(-0.28 + bk * 0.06, -0.06); ctx.lineTo(0 + bk * 0.08, 0.32); ctx.lineTo(0.28 + bk * 0.06, -0.06);
    ctx.strokeStyle = rgba(c.collar || shade(c.base, -0.15)); ctx.lineWidth = 0.05; ctx.lineJoin = 'round'; ctx.stroke();
  } else if (type === 'flight') {
    // jacket with fold-down collar over a dark undershirt
    ctx.beginPath();
    ctx.moveTo(-0.32 + bk * 0.06, -0.1); ctx.lineTo(-0.05 + bk * 0.08, 0.42); ctx.lineTo(-0.42 + bk * 0.05, 0.2); ctx.closePath();
    ctx.moveTo(0.32 + bk * 0.06, -0.1); ctx.lineTo(0.05 + bk * 0.08, 0.42); ctx.lineTo(0.42 + bk * 0.05, 0.2); ctx.closePath();
    ctx.fillStyle = rgba(c.collar || shade(c.base, -0.1)); ctx.fill();
    ctx.strokeStyle = rgba(c.shadow, 0.4); ctx.lineWidth = 0.012; ctx.stroke();
  }
  ctx.restore();
}

function drawNeck(ctx, ch, hx, hy, k, pitch, roll, hs, L, st) {
  const nw = 0.128 * (ch.neckW ?? 1);
  // attachment under the head (jaw back) follows head translation; base at the collar
  const topY = hy + 0.2 * hs, baseY = 0.06;
  const tx = hx + k * 0.035;
  const pts = [
    [tx - nw * 1.05, topY], [tx + nw * 1.05, topY],
    [nw * 1.12 + (tx) * 0.25, (topY + baseY) / 2], [nw * 1.35, baseY], [-nw * 1.35, baseY], [-nw * 1.12 + tx * 0.25, (topY + baseY) / 2],
  ];
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(tx - nw, topY);
  ctx.bezierCurveTo(tx - nw * 1.02, topY + 0.12, -nw * 1.1, baseY - 0.12, -nw * 1.5, baseY + 0.02);
  ctx.lineTo(nw * 1.5, baseY + 0.02);
  ctx.bezierCurveTo(nw * 1.1, baseY - 0.12, tx + nw * 1.02, topY + 0.12, tx + nw, topY);
  ctx.closePath();
  ctx.fillStyle = rgba(ch.skin); ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = lightGrad(ctx, -0.3, 0.3, L, ch.skin, ch.skinShadow, 1.1); ctx.fillRect(-1, -1.5, 2, 2);
  // cast shadow under the jaw
  const g = ctx.createLinearGradient(0, topY - 0.02, 0, topY + 0.16);
  g.addColorStop(0, rgba(ch.skinShadow, 0.75)); g.addColorStop(1, rgba(ch.skinShadow, 0));
  ctx.fillStyle = g; ctx.fillRect(-1, topY - 0.1, 2, 0.3);
  // sternocleidomastoids: soft V from behind each ear to the notch between the collarbones
  ctx.lineCap = 'round';
  for (const sgn of [-1, 1]) {
    const sg = ctx.createLinearGradient(0, topY, 0, baseY);
    sg.addColorStop(0, rgba(ch.skinShadow, 0)); sg.addColorStop(0.35, rgba(ch.skinShadow, ch.holo ? 0.14 : 0.2)); sg.addColorStop(1, rgba(ch.skinShadow, ch.holo ? 0.18 : 0.26));
    ctx.strokeStyle = sg; ctx.lineWidth = 0.03;
    ctx.beginPath();
    ctx.moveTo(tx + sgn * nw * 0.9, topY + 0.02);
    ctx.quadraticCurveTo(sgn * nw * 0.75 + tx * 0.5, (topY + baseY) / 2 + 0.05, sgn * 0.03, baseY + 0.005);
    ctx.stroke();
  }
  // notch
  ctx.fillStyle = rgba(ch.skinShadow, 0.35);
  ctx.beginPath(); ctx.ellipse(0, baseY + 0.005, 0.03, 0.014, 0, 0, U.TAU); ctx.fill();
  ctx.restore();
  ctx.restore();
}

// ---------------------------------------------------------------- arm
function capsule(ctx, p0, p1, r0, r1) {
  const dx = p1[0] - p0[0], dy = p1[1] - p0[1], L = Math.hypot(dx, dy) || 1e-6;
  const nx = -dy / L, ny = dx / L, ang = Math.atan2(dy, dx);
  ctx.moveTo(p0[0] + nx * r0, p0[1] + ny * r0);
  ctx.lineTo(p1[0] + nx * r1, p1[1] + ny * r1);
  ctx.arc(p1[0], p1[1], r1, ang + Math.PI / 2, ang - Math.PI / 2, true);
  ctx.lineTo(p0[0] - nx * r0, p0[1] - ny * r0);
  ctx.arc(p0[0], p0[1], r0, ang - Math.PI / 2, ang + Math.PI / 2, true);
  ctx.closePath();
}

function drawArm(ctx, ch, arm, L, side) {
  const c = ch.cloth;
  const sleeve = ch.sleeve || c.base;
  const w = (ch.armW ?? 0.22);
  const dark = side === 'back' ? -0.1 : 0;
  const S = [arm.sx, arm.sy], E = [arm.ex, arm.ey], Wr = [arm.wx, arm.wy];
  ctx.save();
  // sleeve: upper arm + forearm as one soft shape
  ctx.beginPath();
  capsule(ctx, S, E, w * 0.62, w * 0.5);
  capsule(ctx, E, Wr, w * 0.5, w * 0.42);
  ctx.fillStyle = rgba(shade(sleeve, dark)); ctx.fill();
  ctx.save(); ctx.clip();
  if (L.amb && L.ambA) { ctx.fillStyle = rgba(L.amb, L.ambA); ctx.fillRect(-3, -2, 6, 5); }
  ctx.fillStyle = lightGrad(ctx, Math.min(S[0], Wr[0]) - 0.3, Math.max(S[0], Wr[0]) + 0.3, L, sleeve, c.shadow, 0.9);
  ctx.fillRect(-3, -2, 6, 5);
  // inner-arm shade + elbow fold
  ctx.strokeStyle = rgba(c.shadow, 0.3); ctx.lineWidth = w * 0.35; ctx.lineCap = 'round';
  const ex = E[0] - S[0], ey = E[1] - S[1], el = Math.hypot(ex, ey) || 1;
  const inx = (S[0] >= 0 ? -1 : 1) * 0.06;
  ctx.beginPath(); ctx.moveTo(S[0] + inx, S[1] + 0.1); ctx.lineTo(E[0] + inx, E[1]); ctx.stroke();
  ctx.strokeStyle = rgba(c.shadow, 0.35); ctx.lineWidth = 0.018;
  ctx.beginPath(); ctx.arc(E[0], E[1], w * 0.3, Math.atan2(ey, ex) + 0.9, Math.atan2(ey, ex) + 2.0); ctx.stroke();
  ctx.restore();
  ctx.beginPath(); capsule(ctx, S, E, w * 0.62, w * 0.5); capsule(ctx, E, Wr, w * 0.5, w * 0.42);
  ctx.strokeStyle = rgba(c.shadow, 0.4); ctx.lineWidth = 0.01; ctx.stroke();
  rimStroke(ctx, L, 0.025, 0.7);
  // hand emerging from the cuff opening
  const fa = Math.atan2(Wr[1] - E[1], Wr[0] - E[0]);
  const handSize = 0.36 * (ch.handScale ?? 1);
  if (!ch.noHands) {
    drawHand(ctx, Wr[0] + Math.cos(fa) * 0.03, Wr[1] + Math.sin(fa) * 0.03, arm.a, handSize, arm.pose, {
      skin: ch.handSkin || ch.skin, shadow: ch.skinShadow, outline: ch.handOutline,
      mirror: arm.wx < 0 ? !arm.back : arm.back, back: arm.back, squash: arm.squash,
    });
  }
  // cuff rim drawn over the wrist so the hand sits inside the sleeve opening
  ctx.save(); ctx.translate(Wr[0] - Math.cos(fa) * 0.01, Wr[1] - Math.sin(fa) * 0.01); ctx.rotate(fa + Math.PI / 2);
  ctx.fillStyle = rgba(shade(ch.cuff || sleeve, dark - 0.08));
  ctx.beginPath(); ctx.ellipse(0, 0, w * 0.48, 0.045, 0, 0, U.TAU); ctx.fill();
  ctx.strokeStyle = rgba(c.shadow, 0.45); ctx.lineWidth = 0.008; ctx.stroke();
  ctx.restore();
  ctx.restore();
}

function drawOrb(ctx, x, y, glow) {
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(x, y, 0, x, y, 0.42);
  g.addColorStop(0, rgba([255, 244, 214], 0.95 * glow)); g.addColorStop(0.18, rgba([255, 210, 140], 0.75 * glow));
  g.addColorStop(0.5, rgba([255, 170, 90], 0.18 * glow)); g.addColorStop(1, rgba([255, 150, 80], 0));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 0.42, 0, U.TAU); ctx.fill();
  ctx.restore();
}

// ---------------------------------------------------------------- head
function drawHead(ctx, ch, st, k, a, pitch, e, L) {
  const outline = headOutline(ch, k);
  const fy = pitch * 0.045; // facial features slide down when looking down
  const skin = ch.skin, sh = ch.skinShadow;


  // ears (behind or in front depending on yaw)
  const ears = [-1, 1].map((sgn) => {
    const th = sgn * 1.45 + a;
    const vis = Math.cos(th);
    const x = 0.37 * Math.sin(th) * (ch.headW / 0.74) + k * 0.035;
    return { sgn, vis, x };
  });
  for (const ear of ears) if (ear.vis < 0.12 && ear.vis > -0.55) drawEar(ctx, ch, ear, fy, L, false);

  // head fill
  ctx.beginPath(); smoothPath(ctx, outline);
  ctx.fillStyle = rgba(skin); ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = lightGrad(ctx, -0.42, 0.42, L, skin, sh, 1);
  ctx.fillRect(-1, -1, 2, 2);
  // ambient tint
  if (L.amb && L.ambA) { ctx.fillStyle = rgba(L.amb, L.ambA); ctx.fillRect(-1, -1, 2, 2); }
  // jaw/underside soft shadow and cheek warmth
  const jg = ctx.createLinearGradient(0, 0.28 + fy, 0, 0.47);
  jg.addColorStop(0, rgba(sh, 0)); jg.addColorStop(1, rgba(sh, 0.35));
  ctx.fillStyle = jg; ctx.fillRect(-1, 0.2, 2, 0.4);
  const cheekA = (ch.blushA ?? 0.18) + (e.cheek || 0) * 0.12;
  for (const sgn of [-1, 1]) {
    const th = sgn * 0.62 + a, f = Math.cos(th);
    if (f < 0.05) continue;
    const cx = 0.37 * Math.sin(th) * 0.95 + k * 0.03, cy = 0.13 + fy - (e.cheek || 0) * 0.015;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, 0.11);
    g.addColorStop(0, rgba(ch.blush, cheekA * f)); g.addColorStop(1, rgba(ch.blush, 0));
    ctx.fillStyle = g; ctx.fillRect(cx - 0.12, cy - 0.12, 0.24, 0.24);
  }
  if (ch.stubble) {
    const sg = ctx.createRadialGradient(k * 0.08, 0.33 + fy, 0.05, k * 0.08, 0.33 + fy, 0.3);
    sg.addColorStop(0, rgba(ch.stubbleColor || [70, 55, 50], ch.stubble)); sg.addColorStop(1, rgba(ch.stubbleColor || [70, 55, 50], 0));
    ctx.fillStyle = sg; ctx.fillRect(-0.5, 0.05, 1, 0.5);
  }
  if (ch.faceDetail) ch.faceDetail(ctx, ch, st, k, a, fy, e, L);
  ctx.restore();
  // rim light on the silhouette
  ctx.beginPath(); smoothPath(ctx, outline);
  rimStroke(ctx, L, 0.025, 1);
  // a very soft darker contour keeps the head readable against light backgrounds
  ctx.strokeStyle = rgba(shade(sh, -0.3), 0.28); ctx.lineWidth = 0.008; ctx.stroke();

  for (const ear of ears) if (ear.vis >= 0.12) drawEar(ctx, ch, ear, fy, L, true);

  // face features
  const eyeY = -0.02 + fy;
  const eyes = [-1, 1].map((sgn) => {
    const th = sgn * 0.48 * (ch.eyeSpread ?? 1) + a;
    const f = Math.cos(th);
    return { sgn, f, x: 0.37 * Math.sin(th) + k * 0.035, y: eyeY };
  });
  drawNose(ctx, ch, k, a, fy, L);
  drawMouth(ctx, ch, st, k, a, fy, e, L);
  for (const eye of eyes) drawEye(ctx, ch, st, eye, e, L, k);
  for (const eye of eyes) drawBrow(ctx, ch, eye, e, k, fy);
  if (ch.age > 0.3) drawAgeLines(ctx, ch, eyes, k, a, fy, e);
  if (st.tear > 0) drawTear(ctx, ch, eyes, st.tear, k);

  // front hair over the forehead
  if (ch.hairFront) ch.hairFront(ctx, ch, k, pitch, L, st, outline);
  if (ch.headOverlay) ch.headOverlay(ctx, ch, st, k, a, fy, e, L, outline);
}

function drawEar(ctx, ch, ear, fy, L, front) {
  const x = ear.x, y = 0.02 + fy * 0.6;
  const w = 0.075 * Math.max(0.35, Math.abs(Math.sin(ear.sgn * 1.45))) * (0.55 + 0.45 * Math.min(1, Math.abs(ear.vis) + 0.4));
  const h = 0.15 * (ch.earSize ?? 1);
  ctx.save();
  ctx.translate(x, y);
  ctx.beginPath();
  ctx.ellipse(ear.sgn * 0.012, 0, w * (front ? 0.85 : 1), h / 2, ear.sgn * -0.12, 0, U.TAU);
  ctx.fillStyle = rgba(ch.earColor || shade(ch.skin, -0.04)); ctx.fill();
  ctx.strokeStyle = rgba(ch.skinShadow, 0.5); ctx.lineWidth = 0.008; ctx.stroke();
  // inner ear shading
  ctx.fillStyle = rgba(ch.skinShadow, 0.45);
  ctx.beginPath(); ctx.ellipse(ear.sgn * 0.004, 0.004, w * 0.45, h * 0.28, ear.sgn * -0.12, 0, U.TAU); ctx.fill();
  ctx.restore();
}

function drawNose(ctx, ch, k, a, fy, L) {
  const ns = ch.noseSize ?? 1;
  const tipX = k * 0.12 * ns + k * 0.035, tipY = 0.17 + fy;
  const sh = ch.skinShadow;
  ctx.save();
  // bridge shadow on the side away from the light / facing side
  const side = k >= 0 ? 1 : -1;
  const bg = ctx.createLinearGradient(0, 0.02 + fy, 0, tipY);
  bg.addColorStop(0, rgba(sh, 0)); bg.addColorStop(1, rgba(sh, 0.12 + Math.abs(k) * 0.25));
  ctx.strokeStyle = bg; ctx.lineWidth = 0.02; ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(k * 0.08 + side * 0.03, 0.03 + fy);
  ctx.quadraticCurveTo(tipX + side * 0.035, 0.1 + fy, tipX + side * 0.025, tipY - 0.005);
  ctx.stroke();
  // tip & nostril wings
  ctx.fillStyle = rgba(sh, 0.28);
  ctx.beginPath(); ctx.ellipse(tipX, tipY + 0.012, 0.045 * ns, 0.022 * ns, 0, 0, U.TAU); ctx.fill();
  ctx.fillStyle = rgba(shade(sh, -0.35), 0.55);
  for (const sgn of [-1, 1]) {
    const f = Math.cos(sgn * 0.5 + a);
    if (f < 0.25) continue;
    ctx.beginPath();
    ctx.ellipse(tipX + sgn * 0.024 * ns * f, tipY + 0.022, 0.012 * f, 0.007, sgn * 0.3, 0, U.TAU);
    ctx.fill();
  }
  // highlight
  ctx.fillStyle = rgba(shade(ch.skin, 0.35), 0.35);
  ctx.beginPath(); ctx.ellipse(tipX - 0.008, tipY - 0.004, 0.014, 0.01, 0, 0, U.TAU); ctx.fill();
  ctx.restore();
}

function drawEye(ctx, ch, st, eye, e, L, k) {
  if (eye.f < 0.08) return;
  const es = ch.eyeSize ?? 1;
  const f = Math.pow(eye.f, 0.8);
  const w = 0.125 * es * f, h = 0.062 * es;
  const x = eye.x, y = eye.y;
  const inner = eye.sgn < 0 ? 1 : -1; // direction toward nose in x
  const blink = clamp(st.blink || 0);
  const lidUp = clamp((e.lidUp ?? 1) * (1 - blink), 0, 1.45);
  const lidLow = clamp((e.lidLow || 0) + (e.cheek || 0) * 0.25, 0, 1);
  const tilt = (ch.eyeTilt ?? 0.012);
  const pIn = [x + inner * w * 0.5, y + 0.004];
  const pOut = [x - inner * w * 0.5, y - tilt];
  // lid curves
  const upH = h * 1.0 * lidUp;
  const loH = h * 0.6 * (1 - lidLow * 0.55);
  const upC1 = [lerp(pIn[0], pOut[0], 0.28), y - upH * 1.05 - 0.004];
  const upC2 = [lerp(pIn[0], pOut[0], 0.72), y - upH * 0.95];
  const loC1 = [lerp(pIn[0], pOut[0], 0.3), y + loH];
  const loC2 = [lerp(pIn[0], pOut[0], 0.72), y + loH * 0.9];
  const upper = bez(pIn, upC1, upC2, pOut, 14);
  const lower = bez(pIn, loC1, loC2, pOut, 14);
  const closed = lidUp < 0.06;
  ctx.save();
  // socket shading above the eye
  const sg = ctx.createRadialGradient(x, y - h * 0.6, 0, x, y - h * 0.6, w * 0.95);
  sg.addColorStop(0, rgba(ch.skinShadow, 0.22)); sg.addColorStop(1, rgba(ch.skinShadow, 0));
  ctx.fillStyle = sg; ctx.fillRect(x - w, y - h * 1.8, w * 2, h * 2.2);
  if (!closed) {
    ctx.beginPath(); poly(ctx, upper); for (let i = lower.length - 1; i >= 0; i--) ctx.lineTo(lower[i][0], lower[i][1]); ctx.closePath();
    ctx.save(); ctx.clip();
    ctx.fillStyle = rgba(ch.eyeWhite || [245, 240, 232]); ctx.fillRect(x - w, y - h * 2, w * 2, h * 4);
    // iris & pupil follow gaze; eyes converge slightly toward the side faced
    const gx = clamp((st.gaze?.x || 0), -1, 1), gy = clamp((st.gaze?.y || 0), -1, 1);
    const ir = 0.034 * es * (ch.irisScale ?? 1);
    const ix = x + gx * w * 0.3 + k * w * 0.08, iy = y + gy * h * 0.42 - upH * 0.08 + (1 - lidUp) * h * 0.1;
    ctx.save(); ctx.translate(ix, iy); ctx.scale(lerp(0.75, 1, f), 1);
    const ig = ctx.createRadialGradient(0, 0, ir * 0.2, 0, 0, ir);
    ig.addColorStop(0, rgba(shade(ch.iris, 0.25))); ig.addColorStop(0.75, rgba(ch.iris)); ig.addColorStop(1, rgba(shade(ch.iris, -0.45)));
    ctx.fillStyle = ig; ctx.beginPath(); ctx.arc(0, 0, ir, 0, U.TAU); ctx.fill();
    ctx.fillStyle = rgba(ch.pupil || [18, 12, 10]);
    ctx.beginPath(); ctx.arc(0, 0, ir * (ch.pupilScale ?? 0.45), 0, U.TAU); ctx.fill();
    if (ch.eyeGlow) {
      ctx.globalCompositeOperation = 'lighter';
      const gg = ctx.createRadialGradient(0, 0, 0, 0, 0, ir * 1.6);
      gg.addColorStop(0, rgba(ch.eyeGlow, 0.55)); gg.addColorStop(1, rgba(ch.eyeGlow, 0));
      ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(0, 0, ir * 1.6, 0, U.TAU); ctx.fill();
      ctx.globalCompositeOperation = 'source-over';
    }
    // catch-lights
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.beginPath(); ctx.arc(-ir * 0.35, -ir * 0.38, ir * 0.24, 0, U.TAU); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.beginPath(); ctx.arc(ir * 0.32, ir * 0.3, ir * 0.1, 0, U.TAU); ctx.fill();
    ctx.restore();
    // upper lid shadow on the eyeball
    const lg = ctx.createLinearGradient(0, y - upH, 0, y - upH + h * 0.7);
    lg.addColorStop(0, rgba(ch.skinShadow, 0.45)); lg.addColorStop(1, rgba(ch.skinShadow, 0));
    ctx.fillStyle = lg; ctx.fillRect(x - w, y - h * 2, w * 2, h * 3);
    ctx.restore();
  }
  // lid skin above the lash line (covers eyeball when lids lower), crease
  const lashC = ch.lash || [40, 26, 22];
  if (closed) {
    const lidLine = bez(pIn, [loC1[0], y + loH * 0.35], [loC2[0], y + loH * 0.3], pOut, 12);
    ctx.strokeStyle = rgba(lashC, 0.9); ctx.lineWidth = 0.011; ctx.lineCap = 'round';
    ctx.beginPath(); poly(ctx, lidLine); ctx.stroke();
  } else {
    taper(ctx, upper, 0.006, 0.012, 0.017);
    ctx.fillStyle = rgba(lashC, 0.95); ctx.fill();
    // a few outer lashes
    if (ch.lashes) {
      ctx.strokeStyle = rgba(lashC, 0.8); ctx.lineWidth = 0.006;
      for (let i = 0; i < 3; i++) {
        const p = upper[10 + i];
        ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(p[0] - inner * 0.012, p[1] - 0.016 + i * 0.003); ctx.stroke();
      }
    }
    // lower lid: soft line
    ctx.strokeStyle = rgba(ch.skinShadow, 0.55); ctx.lineWidth = 0.006;
    ctx.beginPath(); poly(ctx, lower.slice(2, 13)); ctx.stroke();
  }
  // crease
  const cr = bez([pIn[0] - inner * 0.004, pIn[1] - 0.012], [upC1[0], y - upH * 0.95 - 0.03 - (1 - lidUp) * 0.01], [upC2[0], y - upH * 0.9 - 0.026], [pOut[0] + inner * 0.006, pOut[1] - 0.008], 10);
  ctx.strokeStyle = rgba(ch.skinShadow, 0.42); ctx.lineWidth = 0.007;
  ctx.beginPath(); poly(ctx, cr.slice(1, 10)); ctx.stroke();
  ctx.restore();
}

function drawBrow(ctx, ch, eye, e, k, fy) {
  if (eye.f < 0.05) return;
  const f = Math.pow(eye.f, 0.7);
  const inner = eye.sgn < 0 ? 1 : -1;
  const bw = 0.15 * f * (ch.browW ?? 1);
  const by = -0.105 + fy;
  const asym = (e.asym || 0) * eye.sgn * 0.5;
  const rIn = (e.browIn || 0) * 0.045 - (e.furrow || 0) * 0.02 + asym * 0.03;
  const rOut = (e.browOut || 0) * 0.04 - (e.furrow || 0) * 0.006 + asym * 0.035 - (e.browIn || 0) * 0.006;
  const xIn = eye.x + inner * bw * 0.5 - inner * (e.furrow || 0) * -0.01;
  const xOut = eye.x - inner * bw * 0.55;
  const pIn = [xIn, by - rIn + 0.008];
  const pMid = [lerp(xIn, xOut, 0.45), by - (rIn + rOut) * 0.5 - 0.022 - (e.browIn || 0) * 0.008];
  const pOut = [xOut, by - rOut + 0.012];
  const pts = quadPts(pIn, [pMid[0], pMid[1] - 0.006], pOut, 12);
  const th = 0.03 * (ch.browThick ?? 1);
  taper(ctx, pts, th * 1.05, th * 0.35, th * 0.9);
  ctx.fillStyle = rgba(ch.brow || ch.hair); ctx.fill();
  // furrow crease between brows
  if ((e.furrow || 0) > 0.25 && inner === 1) {
    ctx.strokeStyle = rgba(ch.skinShadow, (e.furrow - 0.25) * 0.5); ctx.lineWidth = 0.007;
    ctx.beginPath(); ctx.moveTo(k * 0.05 + 0.012, by - 0.02); ctx.lineTo(k * 0.05 + 0.006, by + 0.03); ctx.stroke();
  }
  if ((e.browIn || 0) > 0.5 && inner === 1) { // worry lines on the forehead
    ctx.strokeStyle = rgba(ch.skinShadow, (e.browIn - 0.5) * 0.35); ctx.lineWidth = 0.006;
    ctx.beginPath(); ctx.moveTo(k * 0.05 - 0.06, by - 0.07); ctx.quadraticCurveTo(k * 0.05, by - 0.095, k * 0.05 + 0.06, by - 0.07); ctx.stroke();
  }
}

function drawMouth(ctx, ch, st, k, a, fy, e, L) {
  const m = st.mouth || { open: 0, wide: 0, round: 0, teeth: 0 };
  const yawn = st.yawn || 0;
  const smile = clamp((e.smile || 0) - m.round * 0.2, -1, 1);
  let open = clamp((e.open || 0) + m.open * (1 - (e.press || 0) * 0.5) + yawn * 0.9, 0, 1.2);
  const wide = m.wide + Math.max(0, smile) * 0.25;
  const round = m.round;
  const mx = k * 0.1 + k * 0.035, my = 0.275 + fy;
  const mw = 0.1 * (ch.mouthW ?? 1) * (1 + wide * 0.25 - round * 0.38 + Math.max(0, smile) * 0.12 - yawn * 0.15);
  const cL = -0.33 + a, cR = 0.33 + a;
  const fL = Math.max(0.15, Math.cos(cL)), fR = Math.max(0.15, Math.cos(cR));
  const xl = mx - mw * fL * 1.0, xr = mx + mw * fR * 1.0;
  const cornerLift = smile * 0.028;
  const yl = my - cornerLift - (e.asym || 0) * -0.004, yr = my - cornerLift + (e.asym || 0) * -0.004;
  const lipC = ch.lip;
  const openH = open * 0.095;
  const upperTop = my - 0.016 * (ch.lipFull ?? 1) - openH * 0.18;
  const lowerBot = my + 0.022 * (ch.lipFull ?? 1) + openH * 1.0;
  ctx.save();
  // smile lines (nasolabial) appear with smiles
  if (smile > 0.3) {
    ctx.strokeStyle = rgba(ch.skinShadow, (smile - 0.3) * 0.5); ctx.lineWidth = 0.008; ctx.lineCap = 'round';
    for (const [x0, y0, sgn] of [[xl, yl, -1], [xr, yr, 1]]) {
      ctx.beginPath(); ctx.moveTo(x0 + sgn * 0.035, y0 - 0.085); ctx.quadraticCurveTo(x0 + sgn * 0.05, y0 - 0.02, x0 + sgn * 0.022, y0 + 0.012); ctx.stroke();
    }
  }
  // lower lip shadow / chin dimple
  const lg = ctx.createRadialGradient(mx, lowerBot + 0.025, 0, mx, lowerBot + 0.025, 0.06);
  lg.addColorStop(0, rgba(ch.skinShadow, 0.35)); lg.addColorStop(1, rgba(ch.skinShadow, 0));
  ctx.fillStyle = lg; ctx.fillRect(mx - 0.08, lowerBot - 0.02, 0.16, 0.1);

  const midUpper = my - openH * 0.25;
  const midLower = my + openH;
  if (open > 0.04) {
    // mouth interior
    ctx.beginPath();
    ctx.moveTo(xl, yl);
    ctx.bezierCurveTo(lerp(xl, mx, 0.4), midUpper - 0.004, lerp(mx, xr, 0.6), midUpper - 0.004, xr, yr);
    ctx.bezierCurveTo(lerp(mx, xr, 0.6), midLower + 0.004, lerp(xl, mx, 0.4), midLower + 0.004, xl, yl);
    ctx.closePath();
    ctx.fillStyle = rgba(ch.mouthIn || [70, 22, 26]); ctx.fill();
    ctx.save(); ctx.clip();
    // tongue
    ctx.fillStyle = rgba(ch.tongue || [176, 82, 84], 0.9);
    ctx.beginPath(); ctx.ellipse(mx, midLower + 0.006, mw * 0.55, openH * 0.38 + 0.006, 0, 0, U.TAU); ctx.fill();
    // upper teeth
    const tA = clamp(0.35 + m.teeth * 0.65 + yawn * -0.3, 0, 1);
    ctx.fillStyle = rgba(ch.teeth || [242, 236, 226], tA);
    ctx.beginPath(); ctx.ellipse(mx, midUpper - 0.004, mw * 0.72, 0.016 + openH * 0.12, 0, 0, Math.PI); ctx.fill();
    ctx.restore();
  }
  // lips
  ctx.fillStyle = rgba(shade(lipC, -0.08));
  ctx.beginPath(); // upper lip with a soft cupid's bow
  ctx.moveTo(xl, yl);
  ctx.bezierCurveTo(lerp(xl, mx, 0.45), upperTop + 0.004, mx - 0.012, upperTop - 0.003, mx, upperTop + 0.003);
  ctx.bezierCurveTo(mx + 0.012, upperTop - 0.003, lerp(mx, xr, 0.55), upperTop + 0.004, xr, yr);
  ctx.bezierCurveTo(lerp(mx, xr, 0.6), midUpper + 0.002, lerp(xl, mx, 0.4), midUpper + 0.002, xl, yl);
  ctx.fill();
  ctx.fillStyle = rgba(lipC);
  ctx.beginPath(); // lower lip
  ctx.moveTo(xl, yl);
  ctx.bezierCurveTo(lerp(xl, mx, 0.4), midLower - 0.002, lerp(mx, xr, 0.6), midLower - 0.002, xr, yr);
  ctx.bezierCurveTo(lerp(mx, xr, 0.55), lowerBot + 0.002, lerp(xl, mx, 0.45), lowerBot + 0.002, xl, yl);
  ctx.fill();
  // lip highlight
  ctx.fillStyle = rgba(shade(lipC, 0.3), 0.35);
  ctx.beginPath(); ctx.ellipse(mx - 0.008, lerp(midLower, lowerBot, 0.45), mw * 0.35, 0.005, 0, 0, U.TAU); ctx.fill();
  // mouth line when closed
  if (open <= 0.04) {
    ctx.strokeStyle = rgba(shade(lipC, -0.45), 0.85); ctx.lineWidth = 0.008; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(xl, yl);
    ctx.bezierCurveTo(lerp(xl, mx, 0.4), my + 0.002 + smile * 0.008, lerp(mx, xr, 0.6), my + 0.002 + smile * 0.008, xr, yr);
    ctx.stroke();
  }
  // corner accents
  ctx.fillStyle = rgba(ch.skinShadow, 0.45);
  for (const [x0, y0] of [[xl, yl], [xr, yr]]) { ctx.beginPath(); ctx.arc(x0, y0, 0.006, 0, U.TAU); ctx.fill(); }
  ctx.restore();
}

function drawAgeLines(ctx, ch, eyes, k, a, fy, e) {
  const A = (ch.age - 0.3) / 0.7;
  ctx.save();
  ctx.strokeStyle = rgba(ch.skinShadow, 0.35 * A); ctx.lineWidth = 0.006; ctx.lineCap = 'round';
  for (const eye of eyes) {
    if (eye.f < 0.3) continue;
    // under-eye bags
    ctx.beginPath(); ctx.moveTo(eye.x - 0.045 * eye.f, eye.y + 0.05); ctx.quadraticCurveTo(eye.x, eye.y + 0.075, eye.x + 0.045 * eye.f, eye.y + 0.048); ctx.stroke();
    // crow's feet
    const out = eye.sgn;
    for (let i = 0; i < 2; i++) {
      ctx.beginPath(); ctx.moveTo(eye.x + out * 0.075 * eye.f, eye.y - 0.01 + i * 0.022); ctx.lineTo(eye.x + out * 0.1 * eye.f, eye.y - 0.02 + i * 0.03); ctx.stroke();
    }
  }
  // forehead lines
  ctx.beginPath(); ctx.moveTo(-0.1 + k * 0.05, -0.27 + fy); ctx.quadraticCurveTo(k * 0.05, -0.285 + fy, 0.1 + k * 0.05, -0.27 + fy); ctx.stroke();
  ctx.restore();
}

function drawTear(ctx, ch, eyes, p, k) {
  // one tear from the eye nearer the camera, as a single object that runs down and fades
  const eye = eyes.reduce((b, x) => (x.f > b.f ? x : b), eyes[0]);
  const run = clamp(p * 1.25);
  const fade = 1 - smooth((p - 0.75) / 0.25);
  const x = eye.x + (eye.sgn > 0 ? 0.02 : -0.02) + Math.sin(run * 3) * 0.004;
  const y = eye.y + 0.04 + run * 0.2;
  ctx.save();
  ctx.globalAlpha *= fade;
  // wet trail
  ctx.strokeStyle = 'rgba(190,220,255,0.28)'; ctx.lineWidth = 0.008; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(eye.x + (eye.sgn > 0 ? 0.02 : -0.02), eye.y + 0.04); ctx.lineTo(x, y - 0.012); ctx.stroke();
  const g = ctx.createRadialGradient(x - 0.004, y - 0.004, 0, x, y, 0.016);
  g.addColorStop(0, 'rgba(240,250,255,0.95)'); g.addColorStop(0.6, 'rgba(150,200,255,0.75)'); g.addColorStop(1, 'rgba(110,170,240,0.35)');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(x, y - 0.022); ctx.quadraticCurveTo(x + 0.012, y, x, y + 0.012); ctx.quadraticCurveTo(x - 0.012, y, x, y - 0.022); ctx.fill();
  ctx.restore();
}

function headCenter(ch, st) {
  const neckLen = (ch.prop || {}).neck ?? 1;
  return [st.x, st.y - (0.47 + 0.24 * neckLen) * st.s];
}

module.exports = {
  headCenter, capsule, drawCharacter, drawHand, armsFor, GESTURES, POSES, lerpPose, smoothPath, taper, bez, quadPts, poly,
  headOutline, headHalfWidth, lightGrad, rimStroke,
};
