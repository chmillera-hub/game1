// THE OTHER EMOTIONS — JOY, SADNESS, ANGER, CALM.
// Original designs built as a family with FEAR (same line weight, shading, face rig, knobbly legs,
// mitten hands, a signature tuft + one accessory each).
//
//   drawEmotion(g, name, x, y, scale, pose)
//     name   : 'JOY' | 'SADNESS' | 'ANGER' | 'CALM'
//     x, y   : world position of the point between the feet on the ground
//     scale  : 1 = EMOTION_HEIGHTS[name] px tall (JOY 457, SADNESS 419, ANGER 394, CALM 523)
//     pose   : all optional — see docs/emotions.md for the full reference
//
// POSE fields (same names/semantics as fear.mjs, plus view/lookBack/lookSide/heat)
//   t            seconds (idle life: breathing, tuft sway, blinking, wave/flail motion)
//   view         'front' (default) | 'back' (seen from behind, e.g. working at the console)
//   lookBack     0..1  (back view only) turn the head over the shoulder toward the camera: the features come
//                round the head like on a turning sphere; at 1 a 3/4 face (one eye + brow, smile, far cheek)
//   lookSide     +1 (default) face appears on the screen-right side, -1 screen-left
//   face         expression object for drawFace (EXPR presets work). Auto-blink unless face.noAutoBlink.
//                A small per-character base expression is ADDED (pose.noBase = true to disable).
//   facing       1 | -1 mirror the body (face stays readable)
//   headTilt     radians;  headTurn -1..1 yaw (screen space, passed to the face as turn)
//   headDX, headDY  head offset px;  lean radians;  crouch 0..1;  tremble 0..1
//   breathe      amplitude (default 1);  breathRate Hz
//   armL, armR   preset name | {preset, dx, dy, atY, hand, bend, layer, fore, boneK, handAng}
//                | {target:[x,y], bend, hand, layer|front, fore, boneK, handAng}   (armL = screen-left at facing 1, both views)
//   walk         { phase } radians
//   heat         0..1 (ANGER only) heat-wisp intensity (default 0.2)
//   shadow       false to skip the ground shadow;  alpha 0..1

import { Path2D, createCanvas } from '@napi-rs/canvas';
import { clamp, lerp, TAU, fbm, noise1, autoBlink, ik, limb, ellipse, circle, groundShadow, shade, rgba, smoothstep } from '../engine.mjs';
import { drawFace, makeExpr } from '../face.mjs';

// ---------------------------------------------------------------- helpers
function roundPoly(g, pts, kr = 0.22) {
  const N = pts.length;
  g.beginPath();
  for (let i = 0; i < N; i++) {
    const p = pts[i], pv = pts[(i - 1 + N) % N], nx = pts[(i + 1) % N];
    const k = Array.isArray(kr) ? kr[i % kr.length] : kr;
    const ax = lerp(p[0], pv[0], k), ay = lerp(p[1], pv[1], k);
    const bx = lerp(p[0], nx[0], k), by = lerp(p[1], nx[1], k);
    if (i === 0) g.moveTo(ax, ay); else g.lineTo(ax, ay);
    g.quadraticCurveTo(p[0], p[1], bx, by);
  }
  g.closePath();
}
function starPts(x, y, ro, ri, rot = 0, n = 5) {
  const pts = [];
  for (let i = 0; i < n * 2; i++) {
    const a = rot - Math.PI / 2 + (i * Math.PI) / n;
    const r = i % 2 === 0 ? ro : ri;
    pts.push([x + Math.cos(a) * r, y + Math.sin(a) * r]);
  }
  return pts;
}
function band(g, path, w, col, line, lw = 2.2) {
  // stroke a path as an outlined strip (like a strap or ribbing edge)
  g.lineCap = 'round'; g.lineJoin = 'round';
  g.strokeStyle = line; g.lineWidth = w + lw * 2; path(); g.stroke();
  g.strokeStyle = col; g.lineWidth = w; path(); g.stroke();
}

// ---------------------------------------------------------------- hands
function drawHand(g, S, x, y, ang, type, fill) {
  g.save();
  g.translate(x, y);
  g.rotate(ang);
  const k = S.handS;
  g.scale(k, k);
  g.fillStyle = fill || S.col.body; g.strokeStyle = S.col.line; g.lineWidth = 2.4 / k;
  g.lineJoin = 'round';
  if (type === 'palm') {
    g.beginPath(); g.ellipse(9, 0, 15, 14, 0, 0, TAU); g.fill(); g.stroke();
    for (const f of [-9, 0, 9]) { g.beginPath(); g.ellipse(25, f * 1.05, 8, 5.2, f * 0.04, 0, TAU); g.fill(); g.stroke(); }
    g.beginPath(); g.ellipse(6, -15, 7, 5, -0.8, 0, TAU); g.fill(); g.stroke();
  } else if (type === 'fist' || type === 'grip') {
    ellipse(g, 4, 0, 10.5, 9.5); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(6, -5); g.lineTo(10, 5); g.stroke();
  } else if (type === 'point') {
    g.beginPath(); g.ellipse(19, -2, 10, 4.2, 0, 0, TAU); g.fill(); g.stroke();
    ellipse(g, 4, 1, 10.5, 9.5); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(7, -3); g.lineTo(11, 6); g.stroke();
  } else {
    // little three-finger mitten (Fear's)
    g.beginPath(); g.ellipse(5, 0, 11, 9, 0, 0, TAU); g.fill(); g.stroke();
    for (const f of [-5, 0, 5]) { g.beginPath(); g.ellipse(15, f, 5, 3.4, f * 0.05, 0, TAU); g.fill(); g.stroke(); }
  }
  g.restore();
}

// ---------------------------------------------------------------- head shapes (clockwise paths, no beginPath)
const headEllipse = (g, cx, cy, rx, ry) => g.ellipse(cx, cy, rx, ry, 0, 0, TAU);
function headDumpling(g, cx, cy, rx, ry) { // SADNESS: soft, a little wider at the bottom
  const rt = rx * 0.93, rb = rx * 1.0;
  g.moveTo(cx, cy - ry);
  g.bezierCurveTo(cx + rt * 0.58, cy - ry, cx + rt, cy - ry * 0.58, cx + rb, cy + ry * 0.06);
  g.bezierCurveTo(cx + rb, cy + ry * 0.64, cx + rb * 0.6, cy + ry, cx, cy + ry);
  g.bezierCurveTo(cx - rb * 0.6, cy + ry, cx - rb, cy + ry * 0.64, cx - rb, cy + ry * 0.06);
  g.bezierCurveTo(cx - rt, cy - ry * 0.58, cx - rt * 0.58, cy - ry, cx, cy - ry);
  g.closePath();
}
function headFlatTop(g, cx, cy, rx, ry) { // ANGER: flat top, square-ish, soft jowls
  const top = cy - ry, bot = cy + ry, r = rx * 0.36;
  g.moveTo(cx - rx + r, top + 1.5);
  g.quadraticCurveTo(cx, top - 1.5, cx + rx - r, top + 1.5);
  g.quadraticCurveTo(cx + rx, top + 1.5, cx + rx, top + r);
  g.bezierCurveTo(cx + rx * 1.03, cy + ry * 0.3, cx + rx * 1.0, bot - ry * 0.22, cx + rx * 0.74, bot - ry * 0.05);
  g.quadraticCurveTo(cx, bot + ry * 0.1, cx - rx * 0.74, bot - ry * 0.05);
  g.bezierCurveTo(cx - rx * 1.0, bot - ry * 0.22, cx - rx * 1.03, cy + ry * 0.3, cx - rx, top + r);
  g.quadraticCurveTo(cx - rx, top + 1.5, cx - rx + r, top + 1.5);
  g.closePath();
}
function headEgg(g, cx, cy, rx, ry) { // CALM: tall egg, narrower chin
  g.moveTo(cx, cy - ry);
  g.bezierCurveTo(cx + rx * 0.58, cy - ry, cx + rx, cy - ry * 0.55, cx + rx, cy - ry * 0.04);
  g.bezierCurveTo(cx + rx, cy + ry * 0.56, cx + rx * 0.52, cy + ry, cx, cy + ry);
  g.bezierCurveTo(cx - rx * 0.52, cy + ry, cx - rx, cy + ry * 0.56, cx - rx, cy - ry * 0.04);
  g.bezierCurveTo(cx - rx, cy - ry * 0.55, cx - rx * 0.58, cy - ry, cx, cy - ry);
  g.closePath();
}

// ================================================================ JOY
const JC = {
  body: '#ffc94a', shade: '#eda534', light: '#fff1bf', line: '#6b3a0c', foot: '#ea7a2e',
  petal: '#ff8f45', petal2: '#ffb978', iris: '#2f86d8', iris2: '#9ad8ff', blush: '#ff7d5c',
};
const JOY = {
  name: 'JOY', H: 460, seed: 21, col: { ...JC, arm: JC.shade, leg: JC.shade },
  hipY: -112, hipX: 18, legW: 9.5, kneeR: 7.2, footRx: 17.5, footRy: 9.5, footCol: JC.foot,
  neckY: -232, headCY: -72, headRx: 84, headRy: 80, faceDY: 10, headPath: headEllipse,
  shoulderX: 34, shoulderY: -213, L1: 54, L2: 52, armW1: 10, armW2: 8.5, handS: 1.15,
  bodyW: 55, shadowR: 76, crouchDrop: 30, breathRate: 0.32, blinkRate: 0.3, tuftBehind: true,
  baseExpr: { browUp: 0.1, smile: 0.22, lidL: 0.1 },
  face: {
    eyeSpacing: 36, eyeY: -6, eyeRx: 25, eyeRy: 29.5, eyeShape: 'round',
    white: '#fffdf6', irisColor: JC.iris, irisColor2: JC.iris2, irisR: 0.64, pupilColor: '#14213a',
    skin: JC.body, line: JC.line, lineW: 2.6, lash: 0.75, restLid: 0.03,
    browY: -50, browLen: 26, browThick: 5.8, browColor: JC.line, browArch: 0.5,
    mouthY: 40, mouthW: 22, mouthColor: '#5a1e12', tongue: '#ef7a68', blushColor: JC.blush,
    blushX: 53, blushY: 22, blushR: 16,
  },
  body(g, c) {
    const T = c.top, B = c.hipY, br = c.br;
    g.fillStyle = JC.body; g.strokeStyle = JC.line; g.lineWidth = 3;
    g.beginPath();
    g.moveTo(-28, T + 8);
    g.bezierCurveTo(-52, T + 40, -61 - br, B - 12, -40, B + 8);
    g.quadraticCurveTo(0, B + 22, 40, B + 8);
    g.bezierCurveTo(61 + br, B - 12, 52, T + 40, 28, T + 8);
    g.quadraticCurveTo(0, T - 4, -28, T + 8);
    g.closePath(); g.fill(); g.stroke();
    if (!c.back) {
      g.fillStyle = rgba(JC.light, 0.6);
      ellipse(g, -6 * c.facing, (T + B) / 2 + 14, 25, 30); g.fill();
      // a tiny sun-dot belly button star
      g.fillStyle = rgba(JC.shade, 0.9);
      roundPoly(g, starPts(-4 * c.facing, (T + B) / 2 + 20, 6.5, 3, 0.2), 0.3); g.fill();
    } else {
      g.fillStyle = rgba(JC.light, 0.35);
      ellipse(g, -14 * c.facing, (T + B) / 2, 20, 30); g.fill();
      g.strokeStyle = rgba(JC.line, 0.25); g.lineWidth = 2;
      g.beginPath(); g.moveTo(0, T + 14); g.quadraticCurveTo(2, (T + B) / 2, 0, B + 8); g.stroke();
    }
  },
  tuft(g, c) { // star-shaped cowlick
    const t = c.t;
    const sway = fbm(t * 0.7, 23) * 0.14 - c.tilt * 0.7 + Math.sin(t * TAU * 0.33 + 1) * 0.05 + c.trem * noise1(t * 24, 24) * 0.2;
    g.save();
    g.translate(c.x, c.top + 14);
    g.rotate(sway);
    g.fillStyle = c.back ? JC.shade : JC.body; g.strokeStyle = JC.line; g.lineWidth = 3;
    g.lineJoin = 'round';
    g.beginPath();
    g.moveTo(-14, 10);
    g.bezierCurveTo(-16, -12, -8, -24, 4, -34);
    g.lineTo(17, -28);
    g.bezierCurveTo(9, -20, 9, -6, 14, 10);
    g.closePath(); g.fill(); g.stroke();
    g.translate(10, -58);
    g.rotate(0.18 + sway * 0.6);
    const gr = g.createRadialGradient(-7, -9, 2, 0, 0, 36);
    gr.addColorStop(0, c.back ? JC.body : '#fff6cf');
    gr.addColorStop(0.5, c.back ? JC.shade : '#ffd766');
    gr.addColorStop(1, c.back ? shade(JC.shade, -0.08) : JC.shade);
    g.fillStyle = gr;
    roundPoly(g, starPts(0, 0, 35, 17), [0.2, 0.12]);
    g.fill(); g.stroke();
    if (!c.back) { g.fillStyle = 'rgba(255,255,255,0.75)'; g.beginPath(); g.ellipse(-8, -10, 6, 3.5, -0.6, 0, TAU); g.fill(); }
    g.restore();
  },
  neckwear(g, c) { // sunny petal collar (pointed sunflower petals around a soft band)
    const y0 = c.neckY + 9;
    g.lineJoin = 'round';
    const n = 9;
    for (let pass = 0; pass < 2; pass++) {
      for (let i = pass; i < n; i += 2) {
        const a = lerp(0.02, 0.98, i / (n - 1)) * Math.PI;
        const px = Math.cos(a) * 31, py = y0 + Math.sin(a) * 9 + 2;
        g.save(); g.translate(px, py); g.rotate(a - Math.PI / 2);
        g.fillStyle = pass ? JC.petal2 : JC.petal; g.strokeStyle = JC.line; g.lineWidth = 2.4;
        g.beginPath();
        g.moveTo(-9, 0);
        g.bezierCurveTo(-11, 10, -4, 19, 0, 23);
        g.bezierCurveTo(4, 19, 11, 10, 9, 0);
        g.closePath(); g.fill(); g.stroke();
        g.restore();
      }
    }
    g.fillStyle = JC.petal; g.strokeStyle = JC.line; g.lineWidth = 2.6;
    ellipse(g, 0, y0, 33, 10); g.fill(); g.stroke();
    g.strokeStyle = rgba('#ffffff', 0.45); g.lineWidth = 2.5;
    g.beginPath(); g.ellipse(0, y0, 25, 5, 0, Math.PI * 1.1, Math.PI * 1.55); g.stroke();
  },
};

// ================================================================ SADNESS
const SC = {
  body: '#6fa8e8', shade: '#4f86cc', light: '#bcd9fb', line: '#1f3768', foot: '#3a5f9e',
  knit: '#5866b4', knit2: '#6e7dc8', knitDark: '#465298', button: '#f4e7c8',
  iris: '#27468f', iris2: '#86b2f2', blush: '#ff97c0',
};
const SADNESS = {
  name: 'SADNESS', H: 420, seed: 37, col: { ...SC, arm: SC.knit, leg: SC.shade },
  hipY: -92, hipX: 21, legW: 10, kneeR: 7.5, footRx: 18, footRy: 10.5, footCol: SC.foot,
  neckY: -240, headCY: -74, headRx: 90, headRy: 80, faceDY: 12, headPath: headDumpling,
  shoulderX: 42, shoulderY: -222, L1: 50, L2: 50, armW1: 19, armW2: 19, handS: 1.05,
  bodyW: 72, shadowR: 86, crouchDrop: 26, breathRate: 0.22, blinkRate: 0.22, tuftBehind: false,
  baseExpr: { lidTilt: 0.25, browIn: 0.3, smile: -0.04 },
  face: {
    eyeSpacing: 37, eyeY: -2, eyeRx: 26, eyeRy: 29.5, eyeShape: 'round',
    white: '#fbfdff', irisColor: SC.iris, irisColor2: SC.iris2, irisR: 0.7, pupilColor: '#0f1a38',
    skin: SC.body, line: SC.line, lineW: 2.6, lash: 0.65, restLid: 0.2,
    browY: -45, browLen: 24, browThick: 4.6, browColor: SC.line, browArch: 0.25,
    mouthY: 42, mouthW: 17, mouthColor: '#2a1840', tongue: '#e0778f', blushColor: SC.blush,
    blushX: 56, blushY: 26, blushR: 17,
  },
  silhouette(g, c) {
    const T = c.top, B = c.hipY, br = c.br;
    g.beginPath();
    g.moveTo(-34, T + 8);
    g.bezierCurveTo(-64, T + 26, -80 - br, B - 42, -66, B - 2);
    g.quadraticCurveTo(-50, B + 24, 0, B + 24);
    g.quadraticCurveTo(50, B + 24, 66, B - 2);
    g.bezierCurveTo(80 + br, B - 42, 64, T + 26, 34, T + 8);
    g.quadraticCurveTo(0, T - 4, -34, T + 8);
    g.closePath();
  },
  body(g, c) {
    const T = c.top, B = c.hipY;
    const S = SADNESS;
    g.fillStyle = SC.knit; g.strokeStyle = SC.line; g.lineWidth = 3;
    S.silhouette(g, c); g.fill();
    g.save();
    S.silhouette(g, c); g.clip();
    // soft knit shading on the far side
    const sg = g.createLinearGradient(-70 * c.facing, 0, 70 * c.facing, 0);
    sg.addColorStop(0, rgba(SC.knit2, 0.6)); sg.addColorStop(0.5, rgba(SC.knit2, 0)); sg.addColorStop(1, rgba(SC.knitDark, 0.5));
    g.fillStyle = sg; g.fillRect(-90, T - 10, 180, B - T + 40);
    // ribbed hem
    g.fillStyle = SC.knitDark; g.fillRect(-90, B + 4, 180, 30);
    g.strokeStyle = rgba(SC.line, 0.35); g.lineWidth = 2;
    for (let xx = -84; xx <= 84; xx += 9) { g.beginPath(); g.moveTo(xx, B + 7); g.lineTo(xx, B + 26); g.stroke(); }
    g.strokeStyle = SC.line; g.lineWidth = 2.2;
    g.beginPath(); g.moveTo(-90, B + 4); g.quadraticCurveTo(0, B + 9, 90, B + 4); g.stroke();
    if (!c.back) {
      // open front showing the soft blue tummy
      const open = () => {
        g.beginPath();
        g.moveTo(-15, T + 4);
        g.quadraticCurveTo(-20, (T + B) / 2, -28, B + 30);
        g.lineTo(28, B + 30);
        g.quadraticCurveTo(20, (T + B) / 2, 15, T + 4);
        g.closePath();
      };
      open();
      const bg = g.createRadialGradient(-8, (T + B) / 2, 4, 0, (T + B) / 2 + 10, 70);
      bg.addColorStop(0, SC.light); bg.addColorStop(0.6, SC.body); bg.addColorStop(1, SC.shade);
      g.fillStyle = bg; g.fill();
      // button bands along the opening
      for (const sd of [-1, 1]) {
        band(g, () => { g.beginPath(); g.moveTo(sd * 17, T + 2); g.quadraticCurveTo(sd * 22, (T + B) / 2, sd * 30, B + 30); }, 8, SC.knit2, SC.line, 2);
      }
      // buttons
      for (let i = 0; i < 3; i++) {
        const yy = T + 40 + i * 30, xx = -lerp(19, 25, (yy - T) / (B - T));
        g.fillStyle = SC.button; g.strokeStyle = SC.line; g.lineWidth = 1.8;
        circle(g, xx - 1, yy, 4.6); g.fill(); g.stroke();
      }
    } else {
      // back seam and a little heart patch (stitched)
      g.strokeStyle = rgba(SC.line, 0.3); g.lineWidth = 2;
      g.beginPath(); g.moveTo(0, T + 10); g.lineTo(0, B + 4); g.stroke();
    }
    g.restore();
    g.strokeStyle = SC.line; g.lineWidth = 3;
    S.silhouette(g, c); g.stroke();
  },
  tuft(g, c) { // droopy lock: grows from the crown, flops over to one side and hangs like a heavy raindrop
    const t = c.t;
    const sway = fbm(t * 0.45, 38) * 0.05 - c.tilt * 0.35 + c.trem * noise1(t * 24, 39) * 0.12;
    const dr = Math.sin(t * TAU * 0.21) * 2 + fbm(t * 0.6, 40) * 1.5;
    g.save();
    g.translate(c.x - 6, c.top + 10);
    g.rotate(sway);
    g.fillStyle = c.back ? SC.shade : SC.body; g.strokeStyle = SC.line; g.lineWidth = 3;
    g.lineJoin = 'round';
    g.beginPath();
    g.moveTo(-20, 8);
    g.bezierCurveTo(-18, -40, 52, -50, 72, -10);
    g.bezierCurveTo(78, 2, 80, 10, 80 + dr * 0.3, 16);
    // the drop (hangs just past the head's edge)
    g.bezierCurveTo(92 + dr, 28, 90 + dr, 46, 78 + dr, 48);
    g.bezierCurveTo(66 + dr, 50, 62 + dr, 36, 68, 22);
    g.bezierCurveTo(70, 14, 62, -6, 34, -10);
    g.bezierCurveTo(10, -13, 0, 0, 2, 8);
    g.closePath(); g.fill(); g.stroke();
    if (!c.back) {
      g.fillStyle = rgba(SC.light, 0.75);
      g.beginPath(); g.ellipse(26, -19, 13, 4, -0.12, 0, TAU); g.fill();
      g.beginPath(); g.ellipse(74 + dr, 36, 3.5, 5.5, 0.3, 0, TAU); g.fill();
    }
    g.restore();
  },
  neckwear(g, c) { // ribbed cardigan collar
    const y0 = c.neckY + 9;
    g.fillStyle = SC.knit2; g.strokeStyle = SC.line; g.lineWidth = 2.6;
    ellipse(g, 0, y0, 38, 12); g.fill(); g.stroke();
    g.strokeStyle = rgba(SC.line, 0.35); g.lineWidth = 1.8;
    for (let a = 0.2; a < Math.PI - 0.1; a += 0.32) {
      const xx = Math.cos(a) * 34, yy = y0 + Math.sin(a) * 10;
      g.beginPath(); g.moveTo(xx * 0.8, yy - 6); g.lineTo(xx, yy + 1); g.stroke();
    }
  },
  // oversized cozy sleeves with "sweater paws"
  arm(g, S, sx, sy, a1, a2, a, side, L1, L2, hang) {
    const ex = sx + Math.cos(a1) * L1, ey = sy + Math.sin(a1) * L1;
    const ang = a1 + a2, dx = Math.cos(ang), dy = Math.sin(ang), nx = -dy, ny = dx;
    const hx = ex + dx * L2, hy = ey + dy * L2;
    const ha = hang ?? ang;
    drawHand(g, S, hx + Math.cos(ha) * 2, hy + Math.sin(ha) * 2, ha, a.hand, SC.body);
    g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = SC.line; g.lineWidth = 23;
    g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.stroke();
    const w0 = 9.5, w1 = 15;
    const fore = () => {
      g.beginPath();
      g.moveTo(ex + nx * w0, ey + ny * w0); g.lineTo(hx + nx * w1, hy + ny * w1);
      g.lineTo(hx - nx * w1, hy - ny * w1); g.lineTo(ex - nx * w0, ey - ny * w0); g.closePath();
    };
    fore(); g.lineWidth = 4.4; g.stroke(); g.fillStyle = SC.knit; g.fill();
    g.strokeStyle = SC.knit; g.lineWidth = 19;
    g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.stroke();
    g.strokeStyle = rgba(SC.knit2, 0.7); g.lineWidth = 5;
    g.beginPath(); g.moveTo(sx + nx * -3, sy + ny * -3); g.lineTo(ex + nx * -3, ey + ny * -3); g.stroke();
    // ribbed cuff
    g.save();
    g.translate(hx, hy); g.rotate(ang + 0.4 * Math.atan2(Math.sin(ha - ang), Math.cos(ha - ang)));
    g.fillStyle = SC.knit2; g.strokeStyle = SC.line; g.lineWidth = 2.4;
    g.beginPath(); g.roundRect(-9, -17.5, 15, 35, 6); g.fill(); g.stroke();
    g.strokeStyle = rgba(SC.line, 0.4); g.lineWidth = 1.6;
    for (const yy of [-11, -5.5, 0, 5.5, 11]) { g.beginPath(); g.moveTo(-5, yy); g.lineTo(3, yy); g.stroke(); }
    g.restore();
  },
};

// ================================================================ ANGER
const AC = {
  body: '#f0634f', shade: '#cf4537', light: '#ffa48d', line: '#561812', foot: '#5e2a2a',
  denim: '#3f6275', denim2: '#55798c', denimDark: '#2f4b5b', stitch: '#a9cfd9', brass: '#ffcf6e',
  iris: '#8a3510', iris2: '#ff9d4d', blush: '#c8303f',
};
const ANGER = {
  name: 'ANGER', H: 400, seed: 53, col: { ...AC, arm: AC.shade, leg: AC.shade },
  hipY: -92, hipX: 26, legW: 13.5, kneeR: 9, footRx: 22, footRy: 11.5, footCol: AC.foot,
  neckY: -216, headCY: -64, headRx: 90, headRy: 70, faceDY: 8, headPath: headFlatTop,
  shoulderX: 50, shoulderY: -199, L1: 50, L2: 48, armW1: 15, armW2: 13, handS: 1.32,
  bodyW: 62, shadowR: 84, crouchDrop: 24, breathRate: 0.36, blinkRate: 0.24, tuftBehind: true,
  baseExpr: { browIn: -0.3, browSquish: 0.2 }, defaultHeat: 0.2, cheekBump: 0.5,
  face: {
    eyeSpacing: 38, eyeY: -2, eyeRx: 19.5, eyeRy: 21, eyeShape: 'round',
    white: '#fffaf6', irisColor: AC.iris, irisColor2: AC.iris2, irisR: 0.62, pupilColor: '#2a0c06',
    skin: AC.body, line: AC.line, lineW: 2.6, lash: 0.8, restLid: 0.16,
    browY: -33, browLen: 34, browThick: 10, browColor: AC.line, browArch: 0.12,
    mouthY: 38, mouthW: 25, mouthColor: '#4a0f0b', tongue: '#e8706a', teethColor: '#fffaf0',
    blushColor: AC.blush, blushX: 62, blushY: 22, blushR: 17,
  },
  silhouette(g, c) {
    const T = c.top, B = c.hipY, br = c.br;
    g.beginPath();
    g.moveTo(-52, T + 6);
    g.bezierCurveTo(-70, T + 10, -68 - br, B - 30, -61, B - 2);
    g.quadraticCurveTo(-52, B + 18, 0, B + 18);
    g.quadraticCurveTo(52, B + 18, 61, B - 2);
    g.bezierCurveTo(68 + br, B - 30, 70, T + 10, 52, T + 6);
    g.quadraticCurveTo(0, T - 6, -52, T + 6);
    g.closePath();
  },
  body(g, c) {
    const T = c.top, B = c.hipY, S = ANGER;
    const waist = B - 46;
    // short overall legs (behind the torso)
    for (const sd of [-1, 1]) {
      g.save();
      g.translate(sd * S.hipX, B);
      g.rotate(-(c.legSwing || 0) * sd * 0.9);
      g.fillStyle = AC.denim; g.strokeStyle = AC.line; g.lineWidth = 2.6;
      g.beginPath(); g.roundRect(-17, -6, 34, 30, 7); g.fill(); g.stroke();
      g.strokeStyle = rgba(AC.stitch, 0.7); g.lineWidth = 1.6;
      g.beginPath(); g.moveTo(-13, 18); g.lineTo(13, 18); g.stroke();
      g.restore();
    }
    g.fillStyle = AC.body; g.strokeStyle = AC.line; g.lineWidth = 3;
    S.silhouette(g, c); g.fill();
    g.save();
    S.silhouette(g, c); g.clip();
    g.fillStyle = rgba(AC.light, 0.45);
    ellipse(g, -22 * c.facing, T + 26, 26, 16); g.fill();
    // overalls lower part
    g.fillStyle = AC.denim;
    g.beginPath(); g.moveTo(-80, waist + 4); g.quadraticCurveTo(0, waist - 4, 80, waist + 4); g.lineTo(80, B + 30); g.lineTo(-80, B + 30); g.closePath(); g.fill();
    g.strokeStyle = AC.line; g.lineWidth = 2.6;
    g.beginPath(); g.moveTo(-80, waist + 4); g.quadraticCurveTo(0, waist - 4, 80, waist + 4); g.stroke();
    g.fillStyle = rgba(AC.denimDark, 0.55);
    ellipse(g, 46 * c.facing, B, 22, 30); g.fill();
    if (c.back) {
      // back pockets
      for (const sd of [-1, 1]) {
        g.fillStyle = AC.denim2; g.strokeStyle = AC.line; g.lineWidth = 2.2;
        g.beginPath(); g.roundRect(sd * 26 - 13, waist + 12, 26, 22, [3, 3, 9, 9]); g.fill(); g.stroke();
        g.strokeStyle = rgba(AC.stitch, 0.75); g.lineWidth = 1.4;
        g.beginPath(); g.roundRect(sd * 26 - 9.5, waist + 15, 19, 15, [2, 2, 7, 7]); g.stroke();
      }
    }
    g.restore();
    g.strokeStyle = AC.line; g.lineWidth = 3;
    S.silhouette(g, c); g.stroke();
    if (!c.back) {
      // straps
      for (const sd of [-1, 1]) {
        band(g, () => { g.beginPath(); g.moveTo(sd * 24, waist - 36); g.quadraticCurveTo(sd * 36, T + 26, sd * 44, T + 8); }, 9, AC.denim2, AC.line, 2.2);
      }
      // bib
      g.fillStyle = AC.denim; g.strokeStyle = AC.line; g.lineWidth = 2.6;
      g.beginPath(); g.roundRect(-30, waist - 44, 60, 50, [9, 9, 2, 2]); g.fill(); g.stroke();
      g.strokeStyle = rgba(AC.stitch, 0.8); g.lineWidth = 1.6;
      g.beginPath(); g.roundRect(-14, waist - 30, 28, 18, [2, 2, 6, 6]); g.stroke();
      for (const sd of [-1, 1]) {
        g.fillStyle = AC.brass; g.strokeStyle = AC.line; g.lineWidth = 1.8;
        circle(g, sd * 21, waist - 35, 4.6); g.fill(); g.stroke();
      }
    } else {
      // straps cross on the back
      const sp = (sd) => () => { g.beginPath(); g.moveTo(sd * 22, waist + 2); g.quadraticCurveTo(0, T + 44, -sd * 44, T + 8); };
      band(g, sp(1), 9, AC.denim2, AC.line, 2.2);
      band(g, sp(-1), 9, AC.denim2, AC.line, 2.2);
      g.fillStyle = AC.denim; g.strokeStyle = AC.line; g.lineWidth = 2;
      g.beginPath(); g.roundRect(-8, waist - 34, 16, 14, 3); g.fill(); g.stroke();
    }
  },
  tuft(g, c) { // tiny heat-wisp tuft: a curl of warm steam (+ rising steam curls with heat)
    const t = c.t, heat = clamp(c.heat);
    const w = Math.sin(t * TAU * (0.6 + heat * 0.8)) * (0.5 + heat * 0.5) + fbm(t * 1.1, 41) * 0.5;
    const hgt = 1.3 + heat * 0.45;
    g.save();
    g.translate(c.x + 2, c.top + 8);
    g.rotate(-c.tilt * 0.5 + w * 0.07 + c.trem * noise1(t * 25, 42) * 0.2);
    g.scale(hgt, hgt);
    const curl = () => {
      g.beginPath();
      g.moveTo(0, 8);
      g.bezierCurveTo(-12, -6, 12 + w * 3, -14, 4 + w * 3, -28);
      g.bezierCurveTo(-1 + w * 2, -37, -12 + w, -33, -9 + w, -24);
      g.bezierCurveTo(-7 + w, -18, 0 + w, -20, 0 + w, -24);
    };
    g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = AC.line; g.lineWidth = 12 / hgt; curl(); g.stroke();
    const gr = g.createLinearGradient(0, 8, 0, -34);
    gr.addColorStop(0, c.back ? AC.shade : AC.body); gr.addColorStop(1, heat > 0.5 ? '#ffd9a8' : '#ffb59a');
    g.strokeStyle = gr; g.lineWidth = 6.5 / hgt; curl(); g.stroke();
    g.restore();
    if (heat > 0.35) {
      // rising steam curls (small, soft)
      const n = heat > 0.75 ? 3 : 2;
      for (let i = 0; i < n; i++) {
        const ph = (t * (0.55 + heat * 0.5) + i / n) % 1;
        const a = Math.sin(ph * Math.PI) * clamp((heat - 0.35) * 2.5);
        const xx = c.x + (i - (n - 1) / 2) * 34 + Math.sin(ph * 6 + i) * 5;
        const yy = c.top - 18 - ph * 60;
        g.strokeStyle = `rgba(255,236,214,${0.55 * a})`; g.lineWidth = 3.5; g.lineCap = 'round';
        g.beginPath(); g.moveTo(xx, yy + 14); g.bezierCurveTo(xx - 8, yy + 6, xx + 8, yy - 2, xx, yy - 10); g.stroke();
      }
    }
  },
  neckwear: null,
};

// ================================================================ CALM
const CC = {
  body: '#7fd6b0', shade: '#5cb993', light: '#cdf3e1', line: '#1b4d3f', foot: '#3f8f72',
  shawl: '#2f8f86', shawl2: '#47aaa0', trim: '#c8efe6', leaf: '#5dbf86', leaf2: '#a6e8b8',
  iris: '#22705a', iris2: '#86dfbd', blush: '#ff9aae',
};
const CALM = {
  name: 'CALM', H: 520, seed: 67, col: { ...CC, arm: CC.shade, leg: CC.shade },
  hipY: -156, hipX: 15, legW: 8, kneeR: 7, footRx: 17, footRy: 8.5, footCol: CC.foot,
  neckY: -314, headCY: -76, headRx: 66, headRy: 76, faceDY: 12, headPath: headEgg,
  shoulderX: 30, shoulderY: -280, L1: 66, L2: 62, armW1: 8.5, armW2: 7.2, handS: 1.08,
  bodyW: 40, shadowR: 62, crouchDrop: 32, breathRate: 0.2, blinkRate: 0.2, tuftBehind: true,
  baseExpr: { smile: 0.15 },
  face: {
    eyeSpacing: 29, eyeY: -4, eyeRx: 21, eyeRy: 20.5, eyeShape: 'almond',
    white: '#fbfffd', irisColor: CC.iris, irisColor2: CC.iris2, irisR: 0.64, pupilColor: '#0e2a22',
    skin: CC.body, line: CC.line, lineW: 2.5, lash: 0.7, restLid: 0.4,
    browY: -37, browLen: 22, browThick: 4.2, browColor: CC.line, browArch: 0.4,
    mouthY: 35, mouthW: 15, mouthColor: '#3a1a2a', tongue: '#e57d8c', blushColor: CC.blush,
    blushX: 44, blushY: 18, blushR: 13,
  },
  body(g, c) {
    const T = c.top + 18, B = c.hipY, br = c.br;
    // slender neck
    g.fillStyle = CC.shade; g.strokeStyle = CC.line; g.lineWidth = 2.6;
    g.beginPath(); g.roundRect(-10, c.neckY - 14, 20, T - c.neckY + 18, 8); g.fill(); g.stroke();
    // body: slim vase
    g.fillStyle = CC.body; g.lineWidth = 3;
    g.beginPath();
    g.moveTo(-18, T + 2);
    g.bezierCurveTo(-38, T + 6, -36, T + 40, -27 - br * 0.5, T + 72);
    g.bezierCurveTo(-22, B - 40, -42, B - 20, -34, B + 2);
    g.quadraticCurveTo(-24, B + 16, 0, B + 16);
    g.quadraticCurveTo(24, B + 16, 34, B + 2);
    g.bezierCurveTo(42, B - 20, 22, B - 40, 27 + br * 0.5, T + 72);
    g.bezierCurveTo(36, T + 40, 38, T + 6, 18, T + 2);
    g.quadraticCurveTo(0, T - 4, -18, T + 2);
    g.closePath(); g.fill(); g.stroke();
    g.fillStyle = rgba(CC.light, c.back ? 0.3 : 0.55);
    ellipse(g, -8 * c.facing, B - 34, 16, 26); g.fill();
    // shawl
    g.lineJoin = 'round';
    if (!c.back) {
      for (const sd of [-1, 1]) {
        g.fillStyle = CC.shawl; g.strokeStyle = CC.line; g.lineWidth = 2.6;
        g.beginPath();
        g.moveTo(sd * 8, T - 4);
        g.quadraticCurveTo(sd * 42, T - 2, sd * 42, T + 30);
        g.quadraticCurveTo(sd * 40, T + 72, sd * 22, T + 104);
        g.quadraticCurveTo(sd * 12, T + 60, sd * 6, T + 14);
        g.closePath(); g.fill(); g.stroke();
        g.strokeStyle = CC.trim; g.lineWidth = 2.4;
        g.beginPath(); g.moveTo(sd * 9, T + 18); g.quadraticCurveTo(sd * 14, T + 60, sd * 21, T + 96); g.stroke();
        g.fillStyle = rgba(CC.shawl2, 0.8);
        ellipse(g, sd * 30, T + 22, 7, 14, sd * -0.2); g.fill();
      }
    } else {
      g.fillStyle = CC.shawl; g.strokeStyle = CC.line; g.lineWidth = 2.6;
      g.beginPath();
      g.moveTo(-40, T + 2);
      g.quadraticCurveTo(-46, T + 34, -30, T + 64);
      g.quadraticCurveTo(-12, T + 96, 0, T + 112);
      g.quadraticCurveTo(12, T + 96, 30, T + 64);
      g.quadraticCurveTo(46, T + 34, 40, T + 2);
      g.quadraticCurveTo(0, T - 8, -40, T + 2);
      g.closePath(); g.fill(); g.stroke();
      g.strokeStyle = CC.trim; g.lineWidth = 2.4;
      g.beginPath(); g.moveTo(-26, T + 66); g.quadraticCurveTo(-10, T + 92, 0, T + 104); g.quadraticCurveTo(10, T + 92, 26, T + 66); g.stroke();
      g.fillStyle = rgba(CC.shawl2, 0.7);
      ellipse(g, -16 * c.facing, T + 30, 14, 18); g.fill();
    }
  },
  tuft(g, c) { // leaf sprout
    const t = c.t;
    const sway = fbm(t * 0.35, 68) * 0.12 + Math.sin(t * TAU * 0.18) * 0.06 - c.tilt * 0.6 + c.trem * noise1(t * 24, 69) * 0.2;
    g.save();
    g.translate(c.x, c.top + 12);
    g.rotate(sway);
    g.lineCap = 'round';
    const stem = () => { g.beginPath(); g.moveTo(0, 10); g.quadraticCurveTo(-7, -18, 2, -44); };
    g.strokeStyle = CC.line; g.lineWidth = 9; stem(); g.stroke();
    g.strokeStyle = c.back ? CC.shade : CC.leaf; g.lineWidth = 4; stem(); g.stroke();
    const leaf = (ang, len, wob) => {
      g.save(); g.translate(2, -44); g.rotate(ang + wob);
      const lg = g.createLinearGradient(0, -len * 0.3, len, len * 0.2);
      lg.addColorStop(0, c.back ? CC.shade : CC.leaf2); lg.addColorStop(1, c.back ? shade(CC.leaf, -0.15) : CC.leaf);
      g.fillStyle = lg; g.strokeStyle = CC.line; g.lineWidth = 2.6;
      g.beginPath(); g.moveTo(0, 0);
      g.bezierCurveTo(len * 0.3, -len * 0.42, len * 0.8, -len * 0.36, len, 0);
      g.bezierCurveTo(len * 0.75, len * 0.3, len * 0.3, len * 0.3, 0, 0);
      g.closePath(); g.fill(); g.stroke();
      g.strokeStyle = rgba(CC.line, 0.45); g.lineWidth = 1.6;
      g.beginPath(); g.moveTo(len * 0.1, 0); g.quadraticCurveTo(len * 0.5, -len * 0.06, len * 0.85, 0); g.stroke();
      g.restore();
    };
    const wob = fbm(t * 0.5, 70) * 0.1;
    leaf(-2.6, 42, -wob);
    leaf(-0.5, 50, wob);
    g.restore();
  },
  neckwear(g, c) { // soft rolled shawl collar
    const y0 = c.top + 16;
    g.fillStyle = CC.shawl2; g.strokeStyle = CC.line; g.lineWidth = 2.6;
    ellipse(g, 0, y0, 24, 9); g.fill(); g.stroke();
    g.strokeStyle = rgba(CC.trim, 0.8); g.lineWidth = 2;
    g.beginPath(); g.ellipse(0, y0 - 1, 17, 4.5, 0, Math.PI * 1.1, Math.PI * 1.6); g.stroke();
  },
};

const SPECS = { JOY, SADNESS, ANGER, CALM };

// ---------------------------------------------------------------- arm presets (per character)
// Each preset: (side, view, t) => { target:[x,y] (feet origin, y up negative), bend, hand, layer, follow }
//   layer: 'back' (default; behind the body in both views), 'front' (in front of the chest — drawn after the
//          head in front view, hidden behind the body in back view), 'over' (on top in both views)
//   follow: target moves with crouch/breath (presets: true, raw targets: false)
function makeArms(S) {
  const sx = S.shoulderX, sy = S.shoulderY, R = S.L1 + S.L2;
  const hcy = S.neckY + S.headCY, hrx = S.headRx, hry = S.headRy;
  const hip = S.hipY, bw = S.bodyW;
  const restX = bw + 9, restDY = Math.sqrt(Math.max(0, (0.93 * R) ** 2 - (restX - sx) ** 2));
  const pf = S.pressFront, pb = S.pressBack;
  return {
    rest: (side) => ({ target: [side * restX, sy + restDY], bend: side }),
    pressButton: (side, view) => (view === 'back'
      ? { target: [side * pb[0], pb[1]], bend: -side, boneK: [0.95, 0.45], layer: 'front', hand: 'open', handAng: -Math.PI / 2 + side * 0.25, follow: false }
      : { target: [side * pf[0], pf[1]], bend: side, fore: 0.8, layer: 'front', hand: 'point', follow: false }),
    coverEars: (side) => ({ target: [side * (hrx + (S.earOut || 6)), hcy + hry * 0.42], bend: -side, layer: 'over', hand: 'palm', handAng: -Math.PI / 2 - side * 0.32 }),
    wave: (side, view, t) => ({ target: [side * (sx + R * (0.5 + 0.16 * Math.sin(t * TAU * 1.4))), sy - R * 0.74], bend: -side, hand: 'palm' }),
    flail: (side, view, t) => ({
      target: [side * (sx + R * (0.6 + 0.22 * noise1(t * 4.2 + side * 3, 31))), sy - R * (0.42 + 0.34 * noise1(t * 5.1 + side * 5, 32))],
      bend: -side, hand: 'open',
    }),
    handsOnHips: (side) => ({ target: [side * (bw + 2), hip - (hip - sy) * 0.3], bend: side, layer: 'over', hand: 'fist' }),
    hugSelf: (side) => ({ target: [-side * bw * 0.36, sy + R * 0.3], bend: side, layer: 'front', hand: 'open' }),
    pointing: (side) => ({ target: [side * (sx + R * 0.97), sy - R * 0.14], bend: -side, hand: 'point' }),
    cheer: (side, view, t) => ({ target: [side * (sx + R * 0.42), sy - R * (0.86 + 0.04 * Math.sin(t * TAU * 1.2 + side))], bend: -side, hand: 'fist' }),
    wipeEye: (side) => ({ target: [side * S.face.eyeSpacing * 1.1, hcy + S.faceDY + S.face.eyeY + 8], bend: -side, layer: 'front', hand: 'fist' }),
    clasp: (side) => ({ target: [side * 6, sy + R * 0.42], bend: side, layer: 'front', hand: 'fist' }),
  };
}

// console contact points (hands) — tuned per character
CALM.earOut = 13;

// Head silhouette half-width table (measured once from the real head path): hw(y), y relative to head centre.
// Used by the look-back face to place features on the head like on a turning sphere.
const PROBE = createCanvas(2, 2).getContext('2d');
function headProfile(S) {
  const p = new Path2D();
  S.headPath(p, 0, 0, S.headRx, S.headRy);
  const step = 2, n = Math.ceil((2 * S.headRy) / step) + 1, w = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const y = -S.headRy + i * step;
    let lo = 0, hi = S.headRx * 1.3;
    if (!PROBE.isPointInPath(p, 0, y)) continue;
    for (let j = 0; j < 16; j++) { const m = (lo + hi) / 2; if (PROBE.isPointInPath(p, m, y)) lo = m; else hi = m; }
    w[i] = lo;
  }
  return (y) => {
    const f = clamp((y + S.headRy) / step, 0, n - 1), i = Math.floor(f), j = Math.min(n - 1, i + 1);
    return lerp(w[i], w[j], f - i);
  };
}

for (const S of Object.values(SPECS)) {
  S.u = S.H / 330;
  S.hw = headProfile(S);
  // angular half-spacing of the eyes on the "sphere" (front view eye offset vs head half-width at eye level)
  S.lookPsi = S.lookPsi ?? 1.0; // face yaw at lookBack 1 (rad, ~57°)
  S.eyeAng = Math.asin(clamp(S.face.eyeSpacing / S.hw(S.faceDY + S.face.eyeY), 0, 0.95));
  // back view: hands reach forward onto the console, just visible beside the body
  // (seen from behind: the elbow drops just outside the torso, the foreshortened forearm rises to the deck and
  //  the hand shows beside the collar, fingers pointing away from camera)
  S.pressBack = [Math.round(S.bodyW), Math.round(S.shoulderY + 0.12 * (S.hipY - S.shoulderY))];
  // front view: hands come down-forward onto a console in front of the character (elbows out)
  S.pressFront = [S.shoulderX + 8, Math.round(S.shoulderY + 0.62 * (S.L1 + S.L2))];
  S.arms = makeArms(S);
}

// ---------------------------------------------------------------- exports
export const EMOTION_NAMES = ['JOY', 'SADNESS', 'ANGER', 'CALM'];
export const EMOTION_HEIGHTS = { JOY: 457, SADNESS: 419, ANGER: 394, CALM: 523 }; // measured silhouette top at rest, scale 1
export const EMOTION_FACES = { JOY: JOY.face, SADNESS: SADNESS.face, ANGER: ANGER.face, CALM: CALM.face };
export const EMOTION_COLORS = { JOY: JC, SADNESS: SC, ANGER: AC, CALM: CC };
/** per-character arm presets, e.g. EMOTION_ARMS.JOY.wave(1, 'front', t) */
export const EMOTION_ARMS = { JOY: JOY.arms, SADNESS: SADNESS.arms, ANGER: ANGER.arms, CALM: CALM.arms };
/** each emotion's characteristic expression (feed to pose.face) */
export const EMOTION_EXPR = {
  JOY: { smile: 1, open: 0.32, teeth: 0.7, lidL: 0.45, browUp: 0.4, blush: 0.35 },
  SADNESS: { browIn: 0.7, lidTilt: 0.5, lidU: 0.3, smile: -0.5, lookY: 0.35, tears: 0.45 },
  ANGER: { browIn: -0.75, browSquish: 0.6, lidTilt: -0.35, lidU: 0.12, smile: -0.5, wide: 0.15, pressed: 0.5 },
  CALM: { smile: 0.4, lidU: 0.18, lidL: 0.22, browIn: 0.12, lookY: 0.1 },
};
/** a warm brief smile for the look-back moment */
export const LOOKBACK_SMILE = { smile: 0.85, open: 0.16, teeth: 0.5, lidL: 0.42, browUp: 0.2, blush: 0.35 };
/** panic face for the alarm (all four) */
export const PANIC_FACE = { browIn: 1, browUp: 0.8, lidU: -0.35, pupil: 0.6, smile: -0.55, open: 0.5, wide: 0.45, teeth: 0.5, tremble: 0.5 };

/** Local anchor points (scale 1, origin at feet, y up negative, facing 1). */
export const EMOTION_ANCHORS = Object.fromEntries(Object.values(SPECS).map((S) => {
  const hc = S.neckY + S.headCY;
  return [S.name, {
    height: EMOTION_HEIGHTS[S.name],
    headCenter: [0, hc], headTop: [0, hc - S.headRy], headRx: S.headRx, headRy: S.headRy,
    faceCenter: [0, hc + S.faceDY],
    eyeL: [-S.face.eyeSpacing, hc + S.faceDY + S.face.eyeY], eyeR: [S.face.eyeSpacing, hc + S.faceDY + S.face.eyeY],
    mouth: [0, hc + S.faceDY + S.face.mouthY],
    neck: [0, S.neckY], shoulderL: [-S.shoulderX, S.shoulderY], shoulderR: [S.shoulderX, S.shoulderY],
    hipY: S.hipY, bodyHalfWidth: S.bodyW, armReach: S.L1 + S.L2,
    pressFrontL: [-S.pressFront[0], S.pressFront[1]], pressFrontR: [S.pressFront[0], S.pressFront[1]],
    pressBackL: [-S.pressBack[0], S.pressBack[1]], pressBackR: [S.pressBack[0], S.pressBack[1]],
    shoulderTouch: [Math.round(S.shoulderX * 0.8), S.shoulderY - 6],
  }];
}));

// ---------------------------------------------------------------- rig
function resolveArm(S, a, side, back, t) {
  const view = back ? 'back' : 'front';
  let spec = a || 'rest';
  if (typeof spec === 'string') spec = { preset: spec };
  let r;
  if (spec.preset || !spec.target) {
    const fn = S.arms[spec.preset] || S.arms.rest;
    r = { follow: true, ...fn(side, view, t), ...spec };
  } else r = { follow: false, ...spec };
  r.tx = r.target[0] + side * (spec.dx || 0);
  r.ty = (spec.atY != null ? spec.atY : r.target[1]) + (spec.dy || 0);
  if (spec.atY != null) {
    r.follow = false;
    if (spec.preset === 'pressButton' && !back) {
      // a console top higher than the default: hands spread outward as they rise (so they clear the head/face)
      // and the fingertip points down onto the edge
      const lift = Math.max(0, S.pressFront[1] - spec.atY);
      r.tx += side * lift * 0.5;
      if (spec.atY < S.shoulderY + 25) {
        if (spec.handAng == null) r.handAng = Math.PI / 2 + side * 0.25;
        if (spec.bend == null) r.bend = side;
      }
    }
  }
  r.layer = r.layer || (r.front ? 'front' : 'back');
  return r;
}

function drawArm(g, S, side, a, c) {
  const { t, trem, u } = c;
  const sx = side * S.shoulderX, sy = c.shY;
  const off = a.follow ? c.shY - S.shoulderY : 0;
  const tx = a.tx + trem * noise1(t * 33 + side, 12) * 3 * u;
  const ty = a.ty + off + trem * noise1(t * 29 + side, 13) * 3 * u;
  // fore 0..1: the arm points into depth (toward/away from camera) -> bones foreshortened
  // boneK [upper, lower] overrides with explicit bone-length multipliers (e.g. a forearm pointing straight away)
  const fore = clamp(a.fore || 0);
  const L1 = S.L1 * (a.boneK ? a.boneK[0] : 1 - 0.32 * fore), L2 = S.L2 * (a.boneK ? a.boneK[1] : 1 - 0.45 * fore);
  const { a1, a2 } = ik(sx, sy, tx, ty, L1, L2, a.bend ?? side);
  const hang = a.handAng != null ? a.handAng : null; // absolute hand angle (local, radians)
  if (S.arm) { S.arm(g, S, sx, sy, a1, a2, a, side, L1, L2, hang); return; }
  const p = limb(g, sx, sy, L1, L2, a1, a2, S.armW1, S.armW2, S.col.arm, S.col.line);
  drawHand(g, S, p.hx, p.hy, hang ?? a1 + a2, a.hand, S.col.body);
}

function drawLegs(g, S, c) {
  const { walk, wph, crouch, back } = c;
  const len = -S.hipY, hipY = c.hipY;
  const legSwing = walk ? Math.sin(wph) * 0.42 : 0;
  c.legSwing = legSwing;
  g.lineCap = 'round';
  for (const side of [-1, 1]) {
    const hx = side * S.hipX;
    const sw = legSwing * side;
    const kneeX = hx + Math.sin(sw) * len * 0.29 + side * crouch * len * 0.13;
    const kneeY = hipY + len * 0.5 - crouch * len * 0.1;
    const footX = hx + Math.sin(sw) * len * 0.45 + side * crouch * len * 0.18;
    const footY = walk ? -Math.max(0, Math.sin(wph + (side > 0 ? 0 : Math.PI))) * len * 0.12 : 0;
    const foot = () => {
      g.fillStyle = S.footCol; g.strokeStyle = S.col.line; g.lineWidth = 2.4;
      if (back) ellipse(g, footX, footY - S.footRy * 0.55, S.footRx * 0.78, S.footRy * 0.95);
      else ellipse(g, footX + side * S.footRx * 0.36, footY - S.footRy * 0.5, S.footRx, S.footRy);
      g.fill(); g.stroke();
      g.fillStyle = 'rgba(255,255,255,0.18)';
      ellipse(g, footX + (back ? 0 : side * S.footRx * 0.2) - 3, footY - S.footRy * 0.85, S.footRx * 0.45, S.footRy * 0.28); g.fill();
    };
    if (back) foot();
    const leg = () => { g.beginPath(); g.moveTo(hx, hipY); g.quadraticCurveTo(kneeX, kneeY, footX, footY - S.footRy * 0.6); };
    g.strokeStyle = S.col.line; g.lineWidth = S.legW + 5; leg(); g.stroke();
    g.strokeStyle = S.col.leg; g.lineWidth = S.legW; leg(); g.stroke();
    g.fillStyle = S.col.leg; g.strokeStyle = S.col.line; g.lineWidth = 2.4;
    circle(g, lerp(hx, footX, 0.5) + (kneeX - hx) * 0.3, (hipY + footY) / 2 + 1, S.kneeR); g.fill(); g.stroke();
    if (!back) foot();
  }
}

function buildExpr(S, c) {
  const f = c.pose.face || {};
  const e = makeExpr(f);
  if (!c.pose.noBase && S.baseExpr) for (const k in S.baseExpr) e[k] = clamp((e[k] || 0) + S.baseExpr[k], -1, 1);
  e.t = c.t;
  if (!f.noAutoBlink) e.blink = clamp((f.blink || 0) + autoBlink(c.t, S.seed, S.blinkRate + c.trem * 0.25));
  return e;
}

function drawHead(g, S, c) {
  const { t, pose, back, facing, k, sl, trem } = c;
  const cy = S.headCY, rx = S.headRx, ry = S.headRy;
  g.save();
  g.translate((pose.headDX || 0) + (back ? sl * rx * 0.06 * c.kb : 0), c.neckY + (pose.headDY || 0) + (back ? ry * 0.05 * c.kb : 0));
  g.rotate((pose.headTilt || 0) + trem * noise1(t * 26, S.seed + 6) * 0.02 + (back ? -sl * 0.07 * c.kb : 0));
  const turnL = clamp(pose.headTurn || 0, -1, 1) * facing;
  const ox = turnL * 3;
  // tuft sits a little forward of the crown: it drifts toward wherever the face points. Seen from the back,
  // an asymmetric tuft is mirrored (anatomically the same side).
  const tc = { ...c, x: turnL * rx * 0.19 + (back ? sl * rx * 0.1 * c.kb : 0), top: cy - ry, tilt: (pose.headTilt || 0) * (back ? -1 : 1) };
  const tuft = () => {
    if (!back) { S.tuft(g, tc); return; }
    g.save(); g.translate(tc.x, 0); g.scale(-1, 1); g.translate(-tc.x, 0); S.tuft(g, tc); g.restore();
  };
  if (S.tuftBehind) tuft();

  // look-back: the face is placed on the head like on a turning sphere (see drawLookBackFace); a smiling
  // far cheek gently pushes the silhouette out (union outline: stroke both shapes, then fill both)
  const look = back && k > 0.01 ? lookBackGeom(S, c, ox) : null;
  const cheek = look && look.cheek;
  const gr = g.createRadialGradient(-rx * 0.27 * facing + turnL * rx * 0.24, cy - ry * 0.4, 10, ox, cy, rx * 1.12);
  gr.addColorStop(0, S.col.light); gr.addColorStop(0.55, S.col.body); gr.addColorStop(1, S.col.shade);
  g.lineJoin = 'round';
  g.strokeStyle = S.col.line; g.lineWidth = 6.4;
  g.beginPath(); S.headPath(g, ox, cy, rx, ry); g.stroke();
  if (cheek) { ellipse(g, cheek[0] * facing, cy + cheek[1], cheek[2], cheek[3]); g.stroke(); }
  g.fillStyle = gr;
  g.beginPath(); S.headPath(g, ox, cy, rx, ry); g.fill();
  if (cheek) { ellipse(g, cheek[0] * facing, cy + cheek[1], cheek[2], cheek[3]); g.fill(); }
  if (back) {
    // nape shading: reads as the back of the head (fades as the face comes round)
    g.save();
    g.beginPath(); S.headPath(g, ox, cy, rx, ry); g.clip();
    const ng = g.createLinearGradient(0, cy + ry * 0.2, 0, cy + ry);
    ng.addColorStop(0, rgba(S.col.shade, 0)); ng.addColorStop(1, rgba(S.col.shade, 0.75 * (1 - 0.6 * c.kb)));
    g.fillStyle = ng; g.fillRect(-rx - 4, cy, rx * 2 + 8, ry + 4);
    g.restore();
  }
  if (!S.tuftBehind) tuft();

  if (!back) {
    g.save();
    g.translate(ox, cy + S.faceDY);
    g.scale(facing, 1);
    const e = buildExpr(S, c);
    e.turn = clamp(pose.headTurn || 0, -1, 1);
    drawFace(g, S.face, e);
    g.restore();
  } else if (look) {
    drawLookBackFace(g, S, c, ox, cy, look);
  }
  g.restore();
}

// ---------------------------------------------------------------- look-back (over-the-shoulder 3/4 face)
// The head is treated like a turning sphere whose cross-section is the real head silhouette (S.hw). The face
// centre sits at yaw psi (0 = facing camera, PI/2 = on the silhouette edge, > PI/2 = hidden behind the head).
// A feature at yaw phi and height y lands at x = hw(y)·sin(phi) and is foreshortened by cos(phi), so during
// the turn the eye slides in from the edge, narrow, and widens — it is never sliced in half by the outline.
// At lookBack 1 (psi = S.lookPsi ≈ 57°): near eye + brow ≈ 0.55·hw from centre, the far eye is just past the
// edge, the smile sits well inside the head and the smiling far cheek nudges the silhouette.
const PSI_HIDDEN = (S) => Math.PI / 2 + S.eyeAng + 0.1;
function lookBackGeom(S, c, ox) {
  const F = S.face, e = buildExpr(S, c);
  const psi = lerp(PSI_HIDDEN(S), S.lookPsi, c.k);
  const s = c.s, fy = S.faceDY;
  const smile = clamp(e.smile, 0, 1);
  // far cheek bump (only when the face is nearly round and smiling)
  const cb = smoothstep(0.55, 1, c.k) * (0.35 + 0.65 * smile) * (S.cheekBump ?? 1);
  let cheek = null;
  if (cb > 0.02) {
    const yb = fy + lerp(F.blushY ?? F.eyeY + F.eyeRy * 1.4, F.mouthY, 0.3);
    const rb = S.headRx * 0.17;
    const xb = s * (S.hw(yb) - rb * (1 - 0.38 * cb)) + ox;
    cheek = [xb, yb, rb * 0.9, rb]; // x in screen space (caller multiplies by facing to get body-local)
  }
  return { e, psi, s, fy, cheek, cb };
}

function drawLookBackFace(g, S, c, ox, cy, L) {
  const { facing } = c;
  const { e, psi, s, fy, cheek, cb } = L;
  const F = S.face, rx = S.headRx, D = rx * 6;
  // features fade in as they come round the edge (the far eye stays just hidden at lookBack 1)
  const vis = (phi) => smoothstep(Math.PI / 2 - 0.16, Math.PI / 2 - 0.4, phi);
  // gaze: the default looks at the camera (iris shifted toward the head centre); face.lookX is relative to that
  const lookX = clamp((e.lookX || 0) - s * 0.6 * Math.sin(Math.min(psi, Math.PI / 2)), -1, 1);
  g.save();
  g.translate(0, cy);
  g.scale(facing, 1); // screen space from here: s is the screen side, x = 0 is the head centre
  g.beginPath();
  S.headPath(g, ox * facing, 0, rx - 1.2, S.headRy - 1.2);
  if (cheek) g.ellipse(cheek[0], cheek[1], cheek[2] - 1.2, cheek[3] - 1.2, 0, 0, TAU);
  g.clip();

  // blush: near cheek (under the near eye) + the far cheek bump
  if (e.blush > 0.01 && F.blushColor) {
    const yb = fy + (F.blushY ?? F.eyeY + F.eyeRy * 1.4), br = F.blushR ?? F.eyeRx * 0.9;
    const pB = psi - Math.asin(clamp((F.blushX ?? F.eyeSpacing * 1.05) / S.hw(yb), 0, 0.99));
    // [x, y, horizontal foreshortening, visibility]
    const spots = [[s * S.hw(yb) * Math.sin(pB), yb, Math.max(0.3, Math.cos(pB)), vis(pB)]];
    if (cheek) spots.push([cheek[0] - s * cheek[2] * 0.3, cheek[1], 0.75, cb]);
    for (const [bx, by, fxb, a] of spots) {
      if (a <= 0.01) continue;
      g.save(); g.translate(bx, by); g.scale(fxb, 1);
      const bg = g.createRadialGradient(0, 0, 0, 0, 0, br);
      bg.addColorStop(0, rgba(F.blushColor, 0.55 * e.blush * a)); bg.addColorStop(1, rgba(F.blushColor, 0));
      g.fillStyle = bg; ellipse(g, 0, 0, br, br * 0.62); g.fill();
      g.restore();
    }
  }

  // eyes + brows: one drawFace pass per eye (the partner eye/mouth of each pass land far off, clipped away)
  const yE = fy + F.eyeY;
  for (const [side, phi] of [[-s, psi - S.eyeAng], [s, psi + S.eyeAng]]) {
    const a = vis(phi);
    if (a <= 0.01) continue;
    const fx = Math.max(0.08, Math.pow(Math.max(0, Math.cos(phi)), 0.85));
    const d = D / fx; // keeps the pass's partner eye + mouth a fixed D away on screen (clipped off)
    g.save();
    if (a < 0.999) g.globalAlpha *= a;
    g.translate(s * S.hw(yE) * Math.sin(phi), fy);
    g.scale(fx, 1);
    g.translate(-side * d, 0);
    drawFace(g, { ...F, eyeSpacing: d, blushColor: null }, { ...e, lookX, turn: 0, sweat: 0 });
    g.restore();
  }

  // mouth: its own pass, foreshortened (a little cheated wider so the smile reads small)
  const yM = fy + F.mouthY, aM = vis(psi), pM = psi - 0.1; // mouth cheated a touch inward so the smile reads whole
  if (aM > 0.01) {
    const fm = lerp(Math.max(0, Math.cos(pM)), 1, 0.3);
    g.save();
    if (aM < 0.999) g.globalAlpha *= aM;
    g.translate(s * S.hw(yM) * Math.sin(pM), fy);
    g.scale(fm, 1);
    // (this pass's eyes sit far off-canvas; blink:1 makes them a single cheap stroke each)
    drawFace(g, { ...F, eyeY: -1e4, browY: -1e4, blushColor: null, mouthW: F.mouthW * 1.15 },
      { ...e, turn: 0, tears: 0, stream: 0, tearL: 0, tearR: 0, sweat: 0, blink: 1 });
    g.restore();
  }
  g.restore();
}

export function drawEmotion(g, name, x, y, scale = 1, pose = {}) {
  const S = SPECS[name];
  if (!S) throw new Error('drawEmotion: unknown emotion ' + name);
  const t = pose.t || 0;
  const back = pose.view === 'back';
  const facing = pose.facing === -1 ? -1 : 1;
  const trem = clamp(pose.tremble || 0);
  const crouch = clamp(pose.crouch || 0);
  const breathe = pose.breathe ?? 1;
  const u = S.u;
  const br = Math.sin(t * TAU * (pose.breathRate || S.breathRate + trem * 0.5) + S.seed) * breathe;
  const shiverX = trem * noise1(t * 38, S.seed + 1) * 2.4 * u;
  const shiverY = trem * noise1(t * 41, S.seed + 2) * 1.5 * u;
  const k = back ? clamp(pose.lookBack || 0) : 0;
  const s = (pose.lookSide ?? 1) < 0 ? -1 : 1;

  // @napi-rs/canvas does not restore fillStyle/strokeStyle on restore(): keep them ourselves so nothing leaks
  const fill0 = g.fillStyle, stroke0 = g.strokeStyle;
  g.save();
  if (pose.alpha != null) g.globalAlpha *= clamp(pose.alpha);
  g.translate(x, y);
  g.scale(scale, scale);
  if (pose.shadow !== false) groundShadow(g, 0, 0, S.shadowR, 0.32);
  g.scale(facing, 1);

  const walk = pose.walk;
  const wph = walk ? walk.phase || 0 : 0;
  const bob = walk ? Math.abs(Math.sin(wph)) * -5 * u : 0;
  const drop = crouch * S.crouchDrop;
  const c = {
    S, t, u, back, facing, trem, crouch, br, k, kb: Math.min(1, k), s, sl: s * facing, walk, wph, pose,
    hipY: S.hipY + drop + bob,
    top: S.neckY + 6 + drop * 0.85 + bob + br * 0.8 * u,
    neckY: S.neckY + drop * 0.92 + bob + br * 1.2 * u,
    shY: S.shoulderY + drop * 0.85 + bob + br * u,
    heat: pose.heat ?? S.defaultHeat ?? 0,
  };

  drawLegs(g, S, c);

  g.translate(shiverX, shiverY);
  g.rotate((pose.lean || 0) + trem * noise1(t * 30, S.seed + 3) * 0.015 + (back ? c.sl * 0.03 * c.kb : 0));

  const arms = [resolveArm(S, pose.armL, -1, back, t), resolveArm(S, pose.armR, 1, back, t)];
  const early = (a) => a.layer !== 'over' && (back || a.layer !== 'front');
  for (let i = 0; i < 2; i++) if (early(arms[i])) drawArm(g, S, i ? 1 : -1, arms[i], c);
  S.body(g, c);
  drawHead(g, S, c);
  if (S.neckwear) S.neckwear(g, c);
  for (let i = 0; i < 2; i++) if (!early(arms[i])) drawArm(g, S, i ? 1 : -1, arms[i], c);
  g.restore();
  g.fillStyle = fill0; g.strokeStyle = stroke0;
}
