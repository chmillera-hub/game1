'use strict';
// Torso, outfits, neck, IK arms, hands and hand props. Coordinates are in head
// units with the origin at the base of the neck (between the shoulders).

const { clamp, lerp, col, shade, rgbStr } = require('./util');

function torsoGeom(A, P) {
  const sw0 = A.shoulderW || (A.sex === 'f' ? 0.6 : 0.72);
  const breath = P.breath || 0;
  const slump = P.slump || 0;
  const up = (P.shoulderUp || 0) - slump * 0.6;
  const sw = sw0 * (1 + breath * 0.012 - slump * 0.04);
  const by = P.bodyYaw || 0;
  const cx = by * 0.07 + (P.lean || 0) * 0.1;
  const sy = -up * 0.075 - breath * 0.018;
  const farL = 1 - Math.max(0, by) * 0.12, farR = 1 - Math.max(0, -by) * 0.12;
  return { sw, cx, sy, by, farL, farR, slump };
}

function torsoPath(ctx, T, bottom = 2.8) {
  const { sw, cx, sy, farL, farR } = T;
  ctx.beginPath();
  ctx.moveTo(cx - 0.14, -0.06);
  ctx.bezierCurveTo(cx - 0.3, -0.02 + sy * 0.5, cx - sw * 0.7 * farL, 0.02 + sy, cx - sw * 0.88 * farL, 0.1 + sy);
  ctx.bezierCurveTo(cx - sw * 1.02 * farL, 0.16 + sy, cx - sw * 1.04 * farL, 0.36 + sy * 0.6, cx - sw * 0.98 * farL, 0.62);
  ctx.lineTo(cx * 0.5 - sw * 0.9 * farL, bottom);
  ctx.lineTo(cx * 0.5 + sw * 0.9 * farR, bottom);
  ctx.lineTo(cx + sw * 0.98 * farR, 0.62);
  ctx.bezierCurveTo(cx + sw * 1.04 * farR, 0.36 + sy * 0.6, cx + sw * 1.02 * farR, 0.16 + sy, cx + sw * 0.88 * farR, 0.1 + sy);
  ctx.bezierCurveTo(cx + sw * 0.7 * farR, 0.02 + sy, cx + 0.3, -0.02 + sy * 0.5, cx + 0.14, -0.06);
  ctx.closePath();
}

function drawNeck(ctx, A, P, head) {
  // head = {x, y} of the head pivot (top of neck) relative to root
  const skin = col(A.skin);
  const nw = A.neckW || (A.sex === 'f' ? 0.125 : 0.15);
  ctx.save();
  ctx.fillStyle = skin;
  ctx.beginPath();
  ctx.moveTo(head.x - nw, head.y);
  ctx.quadraticCurveTo(head.x - nw * 0.95, (head.y + 0) / 2, -nw * 1.25, 0.02);
  ctx.lineTo(nw * 1.25, 0.02);
  ctx.quadraticCurveTo(head.x + nw * 0.95, (head.y + 0) / 2, head.x + nw, head.y);
  ctx.closePath();
  ctx.fill();
  // shadow under the jaw
  const g = ctx.createLinearGradient(0, head.y, 0, head.y + 0.25);
  g.addColorStop(0, rgbStr(shade(A.skin, -0.35), 0.75));
  g.addColorStop(1, rgbStr(shade(A.skin, -0.35), 0));
  ctx.fillStyle = g;
  ctx.fill();
  ctx.restore();
}

function drawTorso(ctx, A, P, light) {
  const T = torsoGeom(A, P);
  const O = A.outfit || { type: 'sweater', main: '#557' };
  const main = O.main;
  ctx.save();
  ctx.lineJoin = 'round';
  // base garment
  torsoPath(ctx, T);
  ctx.fillStyle = col(main);
  ctx.fill();
  ctx.save();
  ctx.clip();
  // form shading: light side vs shadow side
  const g = ctx.createLinearGradient(-T.sw * light.x * 1.1, 0, T.sw * light.x * 1.1, 0);
  g.addColorStop(0, rgbStr(shade(main, 0.08), 0.0));
  g.addColorStop(1, rgbStr(shade(main, -0.5), 0.4));
  ctx.fillStyle = g;
  ctx.fillRect(-2, -1, 4, 5);
  // shadow cast by the head/neck onto the chest
  const hs = ctx.createRadialGradient(T.cx, 0.1, 0.02, T.cx, 0.1, 0.45);
  hs.addColorStop(0, rgbStr(shade(main, -0.5), 0.35));
  hs.addColorStop(1, rgbStr(shade(main, -0.5), 0));
  ctx.fillStyle = hs;
  ctx.fillRect(-1, -0.3, 2, 1);
  // a couple of soft folds
  ctx.strokeStyle = rgbStr(shade(main, -0.35), 0.4);
  ctx.lineWidth = 0.012; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(T.cx - T.sw * 0.6, 0.75); ctx.quadraticCurveTo(T.cx - T.sw * 0.45, 0.95, T.cx - T.sw * 0.5, 1.2); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(T.cx + T.sw * 0.62, 0.8); ctx.quadraticCurveTo(T.cx + T.sw * 0.5, 1.0, T.cx + T.sw * 0.55, 1.3); ctx.stroke();
  drawOutfitDetails(ctx, A, P, T, O);
  ctx.restore();
  // outline
  torsoPath(ctx, T);
  ctx.strokeStyle = rgbStr(shade(main, -0.55), 0.6);
  ctx.lineWidth = 0.012;
  ctx.stroke();
  ctx.restore();
  return T;
}

function drawOutfitDetails(ctx, A, P, T, O) {
  const cx = T.cx;
  const dark = (c, k = -0.3) => col(shade(c, k));
  switch (O.type) {
    case 'cardigan': {
      // inner top in the V
      ctx.fillStyle = col(O.inner);
      ctx.beginPath();
      ctx.moveTo(cx - 0.2, -0.08); ctx.lineTo(cx + 0.2, -0.08);
      ctx.lineTo(cx + 0.16, 0.9); ctx.lineTo(cx - 0.16, 0.9); ctx.closePath(); ctx.fill();
      // scoop neckline of the top
      ctx.strokeStyle = dark(O.inner, -0.2); ctx.lineWidth = 0.012;
      ctx.beginPath(); ctx.moveTo(cx - 0.16, -0.05); ctx.quadraticCurveTo(cx, 0.16, cx + 0.16, -0.05); ctx.stroke();
      // cardigan fronts
      ctx.fillStyle = col(O.main);
      for (const s of [-1, 1]) {
        ctx.beginPath();
        ctx.moveTo(cx + s * 0.17, -0.07);
        ctx.quadraticCurveTo(cx + s * 0.13, 0.45, cx + s * 0.04, 1.0);
        ctx.lineTo(cx + s * 1.2, 1.0); ctx.lineTo(cx + s * 1.2, -0.2); ctx.closePath(); ctx.fill();
        // ribbed edge
        ctx.strokeStyle = col(shade(O.main, 0.18)); ctx.lineWidth = 0.035;
        ctx.beginPath(); ctx.moveTo(cx + s * 0.19, -0.06); ctx.quadraticCurveTo(cx + s * 0.15, 0.45, cx + s * 0.07, 1.05); ctx.stroke();
      }
      ctx.fillStyle = col(shade(O.main, 0.35));
      for (const y of [0.78, 1.12]) { ctx.beginPath(); ctx.arc(cx + 0.06, y, 0.018, 0, Math.PI * 2); ctx.fill(); }
      break;
    }
    case 'hoodie': {
      // hood bunched behind the neck
      ctx.fillStyle = col(shade(O.main, -0.18));
      ctx.beginPath();
      ctx.moveTo(cx - 0.42, 0.06); ctx.quadraticCurveTo(cx, -0.25, cx + 0.42, 0.06);
      ctx.quadraticCurveTo(cx + 0.25, 0.2, cx, 0.16); ctx.quadraticCurveTo(cx - 0.25, 0.2, cx - 0.42, 0.06);
      ctx.fill();
      ctx.strokeStyle = dark(O.main, -0.4); ctx.lineWidth = 0.01;
      ctx.beginPath(); ctx.moveTo(cx - 0.18, 0.05); ctx.quadraticCurveTo(cx, 0.17, cx + 0.18, 0.05); ctx.stroke();
      // drawstrings
      ctx.strokeStyle = col(O.trim || '#eee'); ctx.lineWidth = 0.016; ctx.lineCap = 'round';
      for (const s of [-1, 1]) {
        ctx.beginPath(); ctx.moveTo(cx + s * 0.1, 0.12); ctx.quadraticCurveTo(cx + s * 0.12, 0.4, cx + s * 0.09, 0.62); ctx.stroke();
      }
      break;
    }
    case 'sweater': {
      ctx.strokeStyle = col(shade(O.main, -0.22)); ctx.lineWidth = 0.05;
      ctx.beginPath(); ctx.moveTo(cx - 0.17, -0.05); ctx.quadraticCurveTo(cx, 0.1, cx + 0.17, -0.05); ctx.stroke();
      if (O.collar) { // shirt collar peeking out (Dad)
        ctx.fillStyle = col(O.collar);
        for (const s of [-1, 1]) {
          ctx.beginPath(); ctx.moveTo(cx + s * 0.02, 0.06); ctx.lineTo(cx + s * 0.17, -0.07); ctx.lineTo(cx + s * 0.2, 0.08); ctx.closePath(); ctx.fill();
        }
      }
      if (O.lanyard) {
        ctx.strokeStyle = col(O.lanyard); ctx.lineWidth = 0.022;
        ctx.beginPath(); ctx.moveTo(cx - 0.15, -0.02); ctx.quadraticCurveTo(cx - 0.1, 0.5, cx, 0.75);
        ctx.quadraticCurveTo(cx + 0.1, 0.5, cx + 0.15, -0.02); ctx.stroke();
        ctx.fillStyle = '#f2f2f2'; ctx.fillRect(cx - 0.07, 0.74, 0.14, 0.18);
        ctx.fillStyle = col(O.lanyard); ctx.fillRect(cx - 0.07, 0.74, 0.14, 0.04);
      }
      break;
    }
    case 'shirtTie': {
      ctx.fillStyle = col(shade(O.main, 0.1));
      for (const s of [-1, 1]) { // collar
        ctx.beginPath(); ctx.moveTo(cx + s * 0.02, 0.1); ctx.lineTo(cx + s * 0.16, -0.08); ctx.lineTo(cx + s * 0.22, 0.12); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = dark(O.main, -0.3); ctx.lineWidth = 0.008; ctx.stroke();
      }
      ctx.fillStyle = col(O.tie);
      ctx.beginPath(); ctx.moveTo(cx - 0.04, 0.03); ctx.lineTo(cx + 0.04, 0.03); ctx.lineTo(cx + 0.03, 0.11); ctx.lineTo(cx - 0.03, 0.11); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(cx - 0.03, 0.11); ctx.lineTo(cx + 0.03, 0.11); ctx.lineTo(cx + 0.07, 0.95); ctx.lineTo(cx, 1.05); ctx.lineTo(cx - 0.07, 0.95); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = col(shade(O.tie, 0.25)); ctx.lineWidth = 0.012;
      for (let y = 0.25; y < 1.0; y += 0.12) { ctx.beginPath(); ctx.moveTo(cx - 0.05, y); ctx.lineTo(cx + 0.05, y + 0.06); ctx.stroke(); }
      break;
    }
    case 'blouse': {
      ctx.fillStyle = col(A.skin);
      ctx.beginPath(); ctx.moveTo(cx - 0.2, -0.08); ctx.quadraticCurveTo(cx, 0.25, cx + 0.2, -0.08); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = col(shade(O.main, -0.25)); ctx.lineWidth = 0.014;
      ctx.beginPath(); ctx.moveTo(cx - 0.2, -0.08); ctx.quadraticCurveTo(cx, 0.25, cx + 0.2, -0.08); ctx.stroke();
      if (O.pearls) {
        for (let i = 0; i <= 14; i++) {
          const t = i / 14; const x = lerp(cx - 0.17, cx + 0.17, t); const y = -0.04 + Math.sin(t * Math.PI) * 0.17;
          ctx.fillStyle = '#efe8dc'; ctx.beginPath(); ctx.arc(x, y, 0.016, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.beginPath(); ctx.arc(x - 0.004, y - 0.005, 0.005, 0, Math.PI * 2); ctx.fill();
        }
      }
      break;
    }
    case 'tee': default: {
      ctx.strokeStyle = col(shade(O.main, -0.2)); ctx.lineWidth = 0.02;
      ctx.beginPath(); ctx.moveTo(cx - 0.17, -0.06); ctx.quadraticCurveTo(cx, 0.12, cx + 0.17, -0.06); ctx.stroke();
    }
  }
}

// ---------------------------------------------------------------- arms
function shoulderJoint(A, P, T, s) {
  const farK = s < 0 ? T.farL : T.farR;
  return [T.cx + s * (T.sw - 0.12) * farK, 0.24 + T.sy];
}
function ik(S, H, L1, L2, bendSign) {
  const dx = H[0] - S[0], dy = H[1] - S[1];
  let d = Math.hypot(dx, dy);
  const maxD = L1 + L2 - 1e-3, minD = Math.abs(L1 - L2) + 1e-3;
  const dd = clamp(d, minD, maxD);
  const base = Math.atan2(dy, dx);
  const cosA = clamp((L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd), -1, 1);
  const a = base + bendSign * Math.acos(cosA);
  const E = [S[0] + Math.cos(a) * L1, S[1] + Math.sin(a) * L1];
  const ang = Math.atan2(H[1] - E[1], H[0] - E[0]);
  const W = [E[0] + Math.cos(ang) * L2, E[1] + Math.sin(ang) * L2];
  return { E, W, ang };
}

function limbPoly(ctx, A0, B0, w0, w1) {
  const dx = B0[0] - A0[0], dy = B0[1] - A0[1];
  const len = Math.hypot(dx, dy) || 1e-6;
  const nx = -dy / len, ny = dx / len;
  ctx.moveTo(A0[0] + nx * w0 / 2, A0[1] + ny * w0 / 2);
  ctx.lineTo(B0[0] + nx * w1 / 2, B0[1] + ny * w1 / 2);
  ctx.lineTo(B0[0] - nx * w1 / 2, B0[1] - ny * w1 / 2);
  ctx.lineTo(A0[0] - nx * w0 / 2, A0[1] - ny * w0 / 2);
  ctx.closePath();
}
// Tapered arm: shoulder -> elbow -> wrist with rounded joints.
function armShape(ctx, S, E, W, wS, wE, wW, grow) {
  ctx.beginPath();
  limbPoly(ctx, S, E, wS + grow, wE + grow);
  // no outline ring at the shoulder: it would draw a seam across the torso
  if (grow === 0) { ctx.moveTo(S[0] + wS / 2, S[1]); ctx.arc(S[0], S[1], wS / 2, 0, Math.PI * 2); }
  ctx.moveTo(E[0] + (wE + grow) / 2, E[1]); ctx.arc(E[0], E[1], (wE + grow) / 2, 0, Math.PI * 2);
  ctx.fill();
}
function drawArm(ctx, A, P, T, arm, s, light) {
  const S = shoulderJoint(A, P, T, s);
  const L1 = 0.86, L2 = 0.8;
  const H = arm.hand;
  const bend = arm.bend ?? (s < 0 ? -1 : 1) * (H[1] < S[1] + 0.6 ? -1 : 1) * -1;
  let { E, W, ang } = ik(S, H, L1, L2, bend);
  // Foreshortened poses (phone to ear, hand to chest) give the elbow explicitly.
  // ex/ey arrive pre-multiplied by ew while poses blend, so divide it back out.
  const ew = clamp(arm.ew || 0);
  if (ew > 1e-3 && arm.ex !== undefined) {
    const Et = [arm.ex / ew, arm.ey / ew];
    E = [lerp(E[0], Et[0], ew), lerp(E[1], Et[1], ew)];
    W = [lerp(W[0], H[0], ew), lerp(W[1], H[1], ew)];
    ang = Math.atan2(W[1] - E[1], W[0] - E[0]);
  }
  const sleeve = arm.sleeve || (A.outfit && A.outfit.main) || '#666';
  const k = A.sex === 'f' ? 0.92 : 1;
  const wS = 0.25 * k, wE = 0.19 * k, wW = 0.15 * k;
  ctx.save();
  // outline pass (slightly larger), then the sleeve
  ctx.fillStyle = rgbStr(shade(sleeve, -0.55), 0.75);
  armShape(ctx, S, E, W, wS, wE, wW, 0.022);
  ctx.beginPath(); limbPoly(ctx, E, W, wE + 0.022, wW + 0.022); ctx.fill();
  ctx.fillStyle = col(sleeve);
  armShape(ctx, S, E, W, wS, wE, wW, 0);
  ctx.fillStyle = arm.bare ? col(A.skin) : col(sleeve);
  ctx.beginPath(); limbPoly(ctx, E, W, wE, wW); ctx.fill();
  // shading along the side away from the light
  const sideSign = light.x > 0 ? 1 : -1;
  ctx.fillStyle = rgbStr(shade(sleeve, -0.5), 0.28);
  const offset = (P0, P1, w0, w1) => {
    const dx = P1[0] - P0[0], dy = P1[1] - P0[1]; const len = Math.hypot(dx, dy) || 1e-6;
    let nx = -dy / len, ny = dx / len;
    if (nx * sideSign < 0) { nx = -nx; ny = -ny; }
    ctx.beginPath();
    ctx.moveTo(P0[0] + nx * w0 * 0.1, P0[1] + ny * w0 * 0.1);
    ctx.lineTo(P1[0] + nx * w1 * 0.1, P1[1] + ny * w1 * 0.1);
    ctx.lineTo(P1[0] + nx * w1 / 2, P1[1] + ny * w1 / 2);
    ctx.lineTo(P0[0] + nx * w0 / 2, P0[1] + ny * w0 / 2);
    ctx.closePath(); ctx.fill();
  };
  offset(S, E, wS, wE); offset(E, W, wE, wW);
  // elbow crease
  ctx.strokeStyle = rgbStr(shade(sleeve, -0.5), 0.35); ctx.lineWidth = 0.01; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(E[0], E[1], wE * 0.3, ang + 2.2, ang + 3.6); ctx.stroke();
  // cuff
  if (!arm.bare) {
    const cx = W[0] - Math.cos(ang) * 0.035, cy = W[1] - Math.sin(ang) * 0.035;
    ctx.fillStyle = col(shade(sleeve, 0.1));
    ctx.beginPath(); limbPoly(ctx, [cx - Math.cos(ang) * 0.03, cy - Math.sin(ang) * 0.03], [cx + Math.cos(ang) * 0.03, cy + Math.sin(ang) * 0.03], wW + 0.012, wW + 0.012); ctx.fill();
  }
  ctx.restore();
  drawHand(ctx, A, W, ang + (arm.wrist || 0), arm.pose || 'relaxed', s, arm.prop, arm);
  return { S, E, W, ang };
}

function drawHand(ctx, A, W, ang, pose, s, prop, arm) {
  const skin = col(A.skin);
  const line = rgbStr(shade(A.skin, -0.45), 0.8);
  ctx.save();
  ctx.translate(W[0], W[1]);
  ctx.rotate(ang);
  const flip = arm && arm.flip ? -1 : 1;
  ctx.scale(1, s * flip);
  if (prop === 'phone' && pose !== 'none') drawPropBehind(ctx, prop, arm);
  ctx.fillStyle = skin; ctx.strokeStyle = line; ctx.lineWidth = 0.009; ctx.lineJoin = 'round';
  // palm
  ctx.beginPath();
  ctx.moveTo(0, -0.07);
  ctx.quadraticCurveTo(0.12, -0.085, 0.18, -0.065);
  if (pose === 'fist') {
    ctx.quadraticCurveTo(0.25, -0.05, 0.24, 0.02); ctx.quadraticCurveTo(0.23, 0.08, 0.15, 0.08);
  } else if (pose === 'open') {
    // fingers extended and slightly spread
    ctx.lineTo(0.35, -0.08); ctx.quadraticCurveTo(0.37, -0.05, 0.35, -0.035); ctx.lineTo(0.2, -0.03);
    ctx.lineTo(0.37, -0.02); ctx.quadraticCurveTo(0.39, 0.0, 0.37, 0.015); ctx.lineTo(0.2, 0.01);
    ctx.lineTo(0.35, 0.03); ctx.quadraticCurveTo(0.37, 0.05, 0.35, 0.062); ctx.lineTo(0.18, 0.06);
  } else if (pose === 'hold') {
    ctx.quadraticCurveTo(0.27, -0.06, 0.29, 0.0); ctx.quadraticCurveTo(0.29, 0.05, 0.22, 0.06);
  } else { // relaxed: fingers together, gently curled
    ctx.quadraticCurveTo(0.3, -0.06, 0.33, -0.01); ctx.quadraticCurveTo(0.34, 0.04, 0.27, 0.06);
  }
  ctx.quadraticCurveTo(0.12, 0.085, 0.0, 0.07);
  ctx.closePath(); ctx.fill(); ctx.stroke();
  // finger separations
  ctx.strokeStyle = rgbStr(shade(A.skin, -0.35), 0.55); ctx.lineWidth = 0.006;
  if (pose === 'relaxed' || pose === 'hold') {
    for (const y of [-0.025, 0.012, 0.042]) { ctx.beginPath(); ctx.moveTo(0.19, y); ctx.lineTo(pose === 'hold' ? 0.25 : 0.29, y + 0.006); ctx.stroke(); }
  } else if (pose === 'fist') {
    for (const x of [0.17, 0.2]) { ctx.beginPath(); ctx.moveTo(x, -0.05); ctx.lineTo(x + 0.01, 0.05); ctx.stroke(); }
  }
  // thumb
  ctx.fillStyle = skin; ctx.strokeStyle = line; ctx.lineWidth = 0.009;
  ctx.beginPath();
  if (pose === 'open') {
    ctx.moveTo(0.05, -0.06); ctx.quadraticCurveTo(0.14, -0.16, 0.2, -0.15); ctx.quadraticCurveTo(0.22, -0.12, 0.15, -0.08); ctx.closePath();
  } else {
    ctx.moveTo(0.06, -0.065); ctx.quadraticCurveTo(0.16, -0.11, 0.22, -0.075); ctx.quadraticCurveTo(0.2, -0.05, 0.12, -0.045); ctx.closePath();
  }
  ctx.fill(); ctx.stroke();
  if (prop && prop !== 'phone') drawPropFront(ctx, prop, arm);
  ctx.restore();
}

function drawPropBehind(ctx, prop, arm) {
  if (prop === 'phone') {
    // phone held in the palm, extending past the fingers
    ctx.save();
    ctx.translate(0.17, 0.0);
    ctx.rotate(arm.propAngle || 0);
    ctx.fillStyle = '#1b1d22';
    roundRect(ctx, -0.17, -0.09, 0.36, 0.19, 0.03); ctx.fill();
    if (arm.screen) {
      ctx.fillStyle = arm.screen;
      roundRect(ctx, -0.155, -0.077, 0.33, 0.165, 0.02); ctx.fill();
    }
    ctx.restore();
  }
}
function drawPropFront(ctx, prop, arm) {
  if (prop === 'fork') {
    ctx.save();
    ctx.translate(0.2, 0.0);
    ctx.rotate(arm.propAngle ?? -0.5);
    ctx.strokeStyle = '#c9ccd2'; ctx.lineWidth = 0.022; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-0.12, 0); ctx.lineTo(0.3, 0); ctx.stroke();
    ctx.lineWidth = 0.009;
    for (const y of [-0.025, -0.008, 0.008, 0.025]) { ctx.beginPath(); ctx.moveTo(0.3, y * 0.6); ctx.lineTo(0.4, y); ctx.stroke(); }
    ctx.restore();
  } else if (prop === 'mug') {
    ctx.save();
    ctx.translate(0.2, 0.0);
    ctx.fillStyle = arm.mugColor || '#d9cfc0';
    roundRect(ctx, -0.02, -0.14, 0.24, 0.28, 0.03); ctx.fill();
    ctx.restore();
  }
}
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}

module.exports = { torsoGeom, torsoPath, drawNeck, drawTorso, drawArm, drawHand, shoulderJoint, ik, roundRect };
