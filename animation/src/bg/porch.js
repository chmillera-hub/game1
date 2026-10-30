'use strict';
// Nana's house front porch, Saturday morning.  (background painter A)
//
// Options (o):
//   o.doorOpen  0..1, default 0   front door swings INWARD on its left hinges, 0 = closed, 1 = fully open (94 deg)
//
// Static paint (brick, trim, window, porch, garden, hallway seen through the doorway) is cached once
// at 1.25x (+ a half-res mip).  Per frame: one blit, the door leaf mapped in perspective strips,
// and the warm light spill; drawFront adds the two porch posts at the extents' edges.
const { createCanvas } = require('@napi-rs/canvas');

// ---------------------------------------------------------------- helpers
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const lerpAng = (a, b, t) => { let d = ((b - a + Math.PI * 3) % (Math.PI * 2)) - Math.PI; return a + d * t; };
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
function hex2rgb(h) { h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
function rgb2hex(c) { return '#' + c.map((v) => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0')).join(''); }
function mix(a, b, t) { const A = hex2rgb(a), B = hex2rgb(b); return rgb2hex([lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t)]); }
function rgba(h, a) { const c = hex2rgb(h); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; }
function shade(h, k) { return k >= 0 ? mix(h, '#ffffff', k) : mix(h, '#000000', -k); }
function rr(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}
function lin(ctx, x0, y0, x1, y1, stops) { const g = ctx.createLinearGradient(x0, y0, x1, y1); for (const [o, c] of stops) g.addColorStop(o, c); return g; }
function rad(ctx, x, y, r0, r1, stops) { const g = ctx.createRadialGradient(x, y, r0, x, y, r1); for (const [o, c] of stops) g.addColorStop(o, c); return g; }
function softGlow(ctx, x, y, r, col, a, sy = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(1, sy);
  ctx.fillStyle = rad(ctx, 0, 0, 0, r, [[0, rgba(col, a)], [0.35, rgba(col, a * 0.45)], [0.7, rgba(col, a * 0.12)], [1, rgba(col, 0)]]);
  ctx.fillRect(-r, -r, 2 * r, 2 * r); ctx.restore();
}
// value noise
function makeNoise(seed) {
  const R = mulberry32(seed), N = 256, p = new Float32Array(N * N);
  for (let i = 0; i < p.length; i++) p[i] = R();
  return function (x, y) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const x0 = xi & 255, y0 = yi & 255, x1 = (x0 + 1) & 255, y1 = (y0 + 1) & 255;
    const a = p[y0 * N + x0], b = p[y0 * N + x1], c = p[y1 * N + x0], d = p[y1 * N + x1];
    return lerp(lerp(a, b, u), lerp(c, d, u), v);
  };
}
// subtle luminance grain over a world rect of a cache canvas (S = cache scale)
function grain(cv, S, X0, Y0, rect, amp, freq, seed, fine = 0.35) {
  const ctx = cv.getContext('2d');
  const px = Math.max(0, Math.floor((rect[0] - X0) * S)), py = Math.max(0, Math.floor((rect[1] - Y0) * S));
  const pw = Math.min(cv.width - px, Math.ceil(rect[2] * S)), ph = Math.min(cv.height - py, Math.ceil(rect[3] * S));
  if (pw <= 0 || ph <= 0) return;
  const img = ctx.getImageData(px, py, pw, ph), d = img.data;
  const n = makeNoise(seed), R = mulberry32(seed * 7 + 3);
  const f = freq / S;
  for (let j = 0; j < ph; j++) {
    for (let i = 0; i < pw; i++) {
      const k = (j * pw + i) * 4;
      if (d[k + 3] === 0) continue;
      const wx = (px + i) * f, wy = (py + j) * f;
      const v = (n(wx, wy) * 0.6 + n(wx * 2.7 + 17, wy * 2.7 + 5) * 0.4 - 0.5) * 2 * (1 - fine) + (R() - 0.5) * 2 * fine;
      const dv = v * amp;
      d[k] = clamp(d[k] + dv, 0, 255); d[k + 1] = clamp(d[k + 1] + dv * 0.97, 0, 255); d[k + 2] = clamp(d[k + 2] + dv * 0.92, 0, 255);
    }
  }
  ctx.putImageData(img, px, py);
}


// ---------------------------------------------------------------- environment
const EXT = { x0: -400, y0: -400, x1: 1600, y1: 2400 };
const DOOR = { x0: 430, y0: 670, x1: 770, y1: 1500 };
const DOOR_MAX_DEG = 94; // fully open: the leaf sits almost edge-on against the left jamb (a sliver stays visible)
const ENV = {
  name: 'porch',
  extents: EXT,
  options: { doorOpen: 0 },
  anchors: {
    doorKnob: { x: 735, y: 1120 },
    doorHinge: { x: 430, y: 1085 },
    doorCenter: { x: 600, y: 1085 },
    mayaAtDoor: { x: 900, y: 1640 },
    eliAtDoor: { x: 1150, y: 1660 },
    stepsTop: { x: 1100, y: 1700 },
    pathBottom: { x: 1100, y: 2300 },
    window: { x: 1125, y: 1000 },
    lantern: { x: 600, y: -20 },
  },
};
const S = 1.25;
// one-point perspective used for the hallway and the swinging door (camera in front of the door)
const PV = { cx: 640, cy: 1120, D: 2200 };
const proj = (X, Y, Z) => { const s = PV.D / (PV.D + Z); return [PV.cx + (X - PV.cx) * s, PV.cy + (Y - PV.cy) * s]; };
const FVP = { x: 640, y: 1120 }; // porch-floor vanishing point (same camera)

let C = null;
function newCache(x0, y0, w, h, s = S) {
  const cv = createCanvas(Math.ceil(w * s), Math.ceil(h * s));
  const ctx = cv.getContext('2d');
  ctx.setTransform(s, 0, 0, s, -x0 * s, -y0 * s);
  return { cv, ctx, x0, y0, w, h, s };
}
function half(c) {
  const s2 = c.s * 0.5, cv = createCanvas(Math.ceil(c.w * s2), Math.ceil(c.h * s2));
  const ctx = cv.getContext('2d'); ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(c.cv, 0, 0, cv.width, cv.height);
  return { cv, x0: c.x0, y0: c.y0, w: c.w, h: c.h, s: s2 };
}
function blit(ctx, c, alpha = 1) {
  if (alpha <= 0.001) return;
  const ga = ctx.globalAlpha; ctx.globalAlpha = ga * alpha;
  ctx.drawImage(c.cv, c.x0, c.y0, c.w, c.h);
  ctx.globalAlpha = ga;
}
function pick(ctx, pair) { const m = ctx.getTransform(); return Math.hypot(m.a, m.b) < 0.62 ? pair[1] : pair[0]; }
function contactShadow(ctx, cx, cy, w, h, a, col = '30,22,18') {
  ctx.save(); ctx.translate(cx, cy); ctx.scale(1, h / w);
  ctx.fillStyle = rad(ctx, 0, 0, 0, w, [[0, `rgba(${col},${a})`], [0.6, `rgba(${col},${a * 0.4})`], [1, `rgba(${col},0)`]]);
  ctx.fillRect(-w, -w, 2 * w, 2 * w); ctx.restore();
}
function blurred(ctx, px, fn) { ctx.save(); ctx.filter = `blur(${px}px)`; fn(); ctx.restore(); }

// ---------------------------------------------------------------- brick facade
function paintBrick(ctx, R) {
  const y0 = -200, y1 = 1500, bw = 112, bh = 34, mj = 6, course = bh + mj;
  // mortar bed, itself uneven
  ctx.fillStyle = '#9f927f'; ctx.fillRect(EXT.x0, y0, EXT.x1 - EXT.x0, y1 - y0);
  for (let i = 0; i < 260; i++) softGlow(ctx, lerp(EXT.x0, EXT.x1, R()), lerp(y0, y1, R()), 20 + R() * 50, R() < 0.5 ? '#7d705f' : '#b8ab97', 0.25, 0.4);
  const pal = ['#84503f', '#7a4a3c', '#8d5a47', '#734437', '#916250', '#7f5444', '#6b4034', '#8a5e4c', '#7c4b3b', '#96705e'];
  const N = makeNoise(5);
  let row = 0;
  for (let y = y0; y < y1; y += course, row++) {
    const off = row % 2 ? -bw / 2 : 0;
    for (let x = EXT.x0 - bw + off; x < EXT.x1 + bw; x += bw + mj) {
      const lf = (N(x * 0.0025, y * 0.0025) - 0.5) * 0.16;
      let col = pal[Math.floor(R() * pal.length)];
      col = shade(col, lf + (R() - 0.5) * 0.07);
      if (R() < 0.05) col = shade(col, -0.16); // over-fired
      if (R() < 0.05) col = mix(col, '#a08878', 0.3); // weathered/dusty
      const w = bw - R() * 2.5, h = bh - R() * 2, xx = x + R() * 2, yy = y + R() * 1.5;
      // worn, slightly irregular outline
      const j = () => (R() - 0.5) * 2.2;
      ctx.beginPath();
      ctx.moveTo(xx + 2 + j(), yy + j() * 0.5);
      ctx.lineTo(xx + w * 0.5 + j(), yy + j() * 0.6);
      ctx.lineTo(xx + w - 2 + j(), yy + j() * 0.5);
      ctx.lineTo(xx + w + j() * 0.5, yy + h * 0.5 + j());
      ctx.lineTo(xx + w - 2 + j(), yy + h + j() * 0.5);
      ctx.lineTo(xx + w * 0.5 + j(), yy + h + j() * 0.6);
      ctx.lineTo(xx + 2 + j(), yy + h + j() * 0.5);
      ctx.lineTo(xx + j() * 0.5, yy + h * 0.5 + j());
      ctx.closePath();
      ctx.fillStyle = lin(ctx, 0, yy, 0, yy + h, [[0, shade(col, 0.05)], [0.5, col], [1, shade(col, -0.06)]]);
      ctx.fill();
      // mottling + grit speckles
      for (let k = 0; k < 3; k++) {
        ctx.fillStyle = rgba(R() < 0.5 ? '#4e2c22' : '#b48870', 0.08 + R() * 0.08);
        ctx.beginPath(); ctx.ellipse(xx + R() * w, yy + R() * h, 6 + R() * 16, 3 + R() * 6, 0, 0, 7); ctx.fill();
      }
      for (let k = 0; k < 16; k++) {
        ctx.fillStyle = rgba(R() < 0.6 ? '#3e2219' : '#c9a58d', 0.18 + R() * 0.2);
        ctx.beginPath(); ctx.arc(xx + 2 + R() * (w - 4), yy + 2 + R() * (h - 4), 0.6 + R() * 1.3, 0, 7); ctx.fill();
      }
      // chips: a lighter, rough notch at a corner or along an edge
      if (R() < 0.07) {
        const cx = xx + (R() < 0.5 ? 0 : w), cy = yy + (R() < 0.5 ? 0 : h), sx = cx === xx ? 1 : -1, sy = cy === yy ? 1 : -1;
        const a = 5 + R() * 10, b = 4 + R() * 8;
        ctx.fillStyle = mix(col, '#a99583', 0.55);
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + sx * a, cy); ctx.lineTo(cx + sx * a * 0.7, cy + sy * b * 0.4); ctx.lineTo(cx + sx * a * 0.35, cy + sy * b * 0.8); ctx.lineTo(cx, cy + sy * b); ctx.closePath(); ctx.fill();
        ctx.fillStyle = 'rgba(50,30,22,0.3)'; ctx.fillRect(cx + (sx < 0 ? -a : 0), cy + (sy < 0 ? -1 : 0), a, 1);
      }
      // mortar smear over an edge
      if (R() < 0.06) { ctx.fillStyle = 'rgba(170,158,140,0.4)'; ctx.beginPath(); ctx.ellipse(xx + R() * w, yy + (R() < 0.5 ? 1 : h - 1), 8 + R() * 14, 2 + R() * 2, 0, 0, 7); ctx.fill(); }
      ctx.fillStyle = 'rgba(255,225,190,0.08)'; ctx.fillRect(xx + 3, yy + 0.5, w - 6, 1.4);
      // recessed joint shadow beneath this brick (some joints eroded deeper)
      ctx.fillStyle = `rgba(40,26,20,${0.22 + (R() < 0.15 ? 0.2 : 0)})`; ctx.fillRect(xx + 1, yy + h, w - 1, 1.8 + R() * 1.2);
    }
  }
  // low-frequency weathering: soot, sun-bleached and damp patches
  for (let i = 0; i < 34; i++) softGlow(ctx, lerp(-380, 1580, R()), lerp(-150, 1460, R()), 90 + R() * 220, R() < 0.55 ? '#35251e' : '#b89a84', 0.11, 0.7);
  // grime near the ground, rising damp
  ctx.fillStyle = lin(ctx, 0, 1150, 0, 1500, [[0, 'rgba(45,32,24,0)'], [0.6, 'rgba(45,32,24,0.18)'], [1, 'rgba(40,28,20,0.38)']]);
  ctx.fillRect(EXT.x0, 1150, EXT.x1 - EXT.x0, 350);
  for (let i = 0; i < 46; i++) {
    const x = lerp(EXT.x0, EXT.x1, R()), h = 60 + R() * 180;
    ctx.fillStyle = lin(ctx, 0, 1500 - h, 0, 1500, [[0, 'rgba(50,38,28,0)'], [1, 'rgba(50,38,28,0.16)']]);
    ctx.fillRect(x, 1500 - h, 20 + R() * 60, h);
  }
  // water stains under the window sill, faint efflorescence
  for (let i = 0; i < 8; i++) {
    const x = 950 + R() * 340, w = 10 + R() * 26, h = 90 + R() * 160;
    ctx.fillStyle = lin(ctx, 0, 1330, 0, 1330 + h, [[0, 'rgba(45,32,25,0.18)'], [1, 'rgba(45,32,25,0)']]);
    ctx.fillRect(x, 1330, w, h);
  }
  for (let i = 0; i < 10; i++) softGlow(ctx, lerp(-380, 1580, R()), lerp(900, 1460, R()), 50 + R() * 90, '#d8cfc0', 0.12, 0.6);
}

// ---------------------------------------------------------------- porch ceiling + lantern
function paintCeiling(ctx, R) {
  // beadboard ceiling seen from below (soft sky-grey)
  ctx.fillStyle = lin(ctx, 0, -400, 0, -190, [[0, '#9fa8a6'], [1, '#c3c8c2']]);
  ctx.fillRect(EXT.x0, -400, EXT.x1 - EXT.x0, 210);
  for (let y = -392; y < -190; y += 14 + (y + 400) * 0.05) {
    ctx.fillStyle = 'rgba(70,75,75,0.25)'; ctx.fillRect(EXT.x0, y, EXT.x1 - EXT.x0, 1.4);
    ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.fillRect(EXT.x0, y + 1.5, EXT.x1 - EXT.x0, 1);
  }
  // beam / fascia
  ctx.fillStyle = lin(ctx, 0, -195, 0, -150, [[0, '#d9d6cc'], [0.25, '#efece2'], [1, '#c9c4b8']]);
  ctx.fillRect(EXT.x0, -196, EXT.x1 - EXT.x0, 46);
  ctx.fillStyle = 'rgba(60,55,50,0.35)'; ctx.fillRect(EXT.x0, -152, EXT.x1 - EXT.x0, 3);
  // trim board where the brick meets the beam
  ctx.fillStyle = '#e4e0d4'; ctx.fillRect(EXT.x0, -150, EXT.x1 - EXT.x0, 10);
}
function paintLantern(ctx) {
  const cx = 600;
  // canopy + chain
  ctx.fillStyle = '#2b2927'; ctx.beginPath(); ctx.ellipse(cx, -318, 26, 8, 0, 0, 7); ctx.fill();
  for (let y = -312; y < -128; y += 12) {
    ctx.strokeStyle = '#34312d'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.ellipse(cx, y + 6, (y / 12) % 2 ? 2.5 : 5, 6, 0, 0, 7); ctx.stroke();
  }
  // shadow on the wall (soft, lower left)
  blurred(ctx, 14, () => { ctx.fillStyle = 'rgba(30,18,12,0.22)'; rr(ctx, cx - 70, -70, 92, 190, 20); ctx.fill(); });
  // cap
  ctx.fillStyle = lin(ctx, cx - 60, 0, cx + 60, 0, [[0, '#1e1d1c'], [0.6, '#46423c'], [1, '#232120']]);
  ctx.beginPath(); ctx.moveTo(cx - 12, -128); ctx.lineTo(cx + 12, -128); ctx.lineTo(cx + 62, -78); ctx.lineTo(cx - 62, -78); ctx.closePath(); ctx.fill();
  ctx.fillRect(cx - 60, -80, 120, 9);
  ctx.beginPath(); ctx.arc(cx, -132, 8, 0, 7); ctx.fill();
  // glass box (slightly tapering)
  const gy0 = -70, gy1 = 50;
  ctx.fillStyle = lin(ctx, cx - 48, gy0, cx + 48, gy1, [[0, 'rgba(225,232,226,0.85)'], [0.45, 'rgba(160,170,165,0.7)'], [1, 'rgba(120,128,125,0.75)']]);
  ctx.beginPath(); ctx.moveTo(cx - 50, gy0); ctx.lineTo(cx + 50, gy0); ctx.lineTo(cx + 40, gy1); ctx.lineTo(cx - 40, gy1); ctx.closePath(); ctx.fill();
  // candle bulb inside
  ctx.fillStyle = '#e9e2cf'; rr(ctx, cx - 7, -10, 14, 50, 3); ctx.fill();
  ctx.fillStyle = 'rgba(255,250,235,0.85)'; ctx.beginPath(); ctx.ellipse(cx, -20, 8, 13, 0, 0, 7); ctx.fill();
  // frame bars
  ctx.strokeStyle = '#262422'; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(cx - 50, gy0); ctx.lineTo(cx - 40, gy1); ctx.moveTo(cx + 50, gy0); ctx.lineTo(cx + 40, gy1); ctx.moveTo(cx, gy0); ctx.lineTo(cx, gy1); ctx.stroke();
  ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cx - 47, -10); ctx.lineTo(cx + 47, -10); ctx.stroke();
  // sky reflection streak
  ctx.fillStyle = 'rgba(255,255,255,0.45)'; ctx.beginPath(); ctx.moveTo(cx + 18, gy0 + 6); ctx.lineTo(cx + 30, gy0 + 6); ctx.lineTo(cx + 22, gy1 - 8); ctx.lineTo(cx + 12, gy1 - 8); ctx.closePath(); ctx.fill();
  // base + finial
  ctx.fillStyle = '#2a2826'; ctx.fillRect(cx - 44, gy1, 88, 10);
  ctx.beginPath(); ctx.moveTo(cx - 30, gy1 + 10); ctx.lineTo(cx + 30, gy1 + 10); ctx.lineTo(cx + 8, gy1 + 30); ctx.lineTo(cx - 8, gy1 + 30); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.arc(cx, gy1 + 36, 6, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(255,240,215,0.35)'; ctx.fillRect(cx + 24, -80, 30, 3);
}

// ---------------------------------------------------------------- hallway behind the door
function paintHall(ctx, R) {
  const P = proj;
  const poly = (pts, fill) => { ctx.fillStyle = fill; ctx.beginPath(); pts.forEach(([X, Y, Z], i) => { const [x, y] = P(X, Y, Z); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.closePath(); ctx.fill(); };
  const XL = 250, XR = 960, YC = 560, YF = 1500, ZB = 2600;
  ctx.save(); ctx.beginPath(); ctx.rect(DOOR.x0, DOOR.y0, DOOR.x1 - DOOR.x0, DOOR.y1 - DOOR.y0); ctx.clip();
  // ceiling
  poly([[XL, YC, 0], [XR, YC, 0], [XR, YC, ZB], [XL, YC, ZB]], '#e8dcc4');
  // left wall (in warm shade) and right wall (sunlit)
  poly([[XL, YC, 0], [XL, YC, ZB], [XL, YF, ZB], [XL, YF, 0]], '#c9b08e');
  poly([[XR, YC, 0], [XR, YC, ZB], [XR, YF, ZB], [XR, YF, 0]], '#e8cfa6');
  // wainscot on the left wall
  poly([[XL, 1180, 0], [XL, 1180, ZB], [XL, YF, ZB], [XL, YF, 0]], '#b39570');
  // back wall
  poly([[XL, YC, ZB], [XR, YC, ZB], [XR, YF, ZB], [XL, YF, ZB]], '#ecd9b6');
  // bright doorway to the sunny kitchen at the back
  const [dx0, dy0] = P(560, 880, ZB), [dx1, dy1] = P(800, YF, ZB);
  ctx.fillStyle = lin(ctx, 0, dy0, 0, dy1, [[0, '#fff3d6'], [1, '#ffe6b8']]); ctx.fillRect(dx0, dy0, dx1 - dx0, dy1 - dy0);
  // kitchen window glimpse + table edge inside
  ctx.fillStyle = '#fffbee'; ctx.fillRect(dx0 + 16, dy0 + 14, 40, 52);
  ctx.fillStyle = 'rgba(190,150,100,0.55)'; ctx.fillRect(dx0, dy1 - 46, dx1 - dx0, 10);
  ctx.fillStyle = 'rgba(150,110,75,0.4)'; ctx.fillRect(dx0 + 8, dy1 - 36, 5, 36); ctx.fillRect(dx1 - 22, dy1 - 36, 5, 36);
  // door casing of the back doorway
  ctx.strokeStyle = '#f6efe2'; ctx.lineWidth = 6; ctx.strokeRect(dx0 - 3, dy0 - 3, dx1 - dx0 + 6, dy1 - dy0 + 3);
  // framed picture on the back wall (left of the doorway)
  const [px0, py0] = P(320, 930, ZB), [px1, py1] = P(480, 1130, ZB);
  ctx.fillStyle = '#6d4c33'; ctx.fillRect(px0, py0, px1 - px0, py1 - py0);
  ctx.fillStyle = '#d9c7a4'; ctx.fillRect(px0 + 5, py0 + 5, px1 - px0 - 10, py1 - py0 - 10);
  ctx.fillStyle = '#9fae96'; ctx.fillRect(px0 + 9, py0 + 20, px1 - px0 - 18, py1 - py0 - 30);
  // hall table against the left back with a bowl
  poly([[XL, 1220, 1500], [XL + 160, 1220, 1500], [XL + 160, 1220, 2100], [XL, 1220, 2100]], '#8a6040');
  poly([[XL + 160, 1220, 1500], [XL + 160, 1250, 1500], [XL + 160, 1250, 2100], [XL + 160, 1220, 2100]], '#6e4a30');
  for (const z of [1530, 2070]) poly([[XL + 140, 1250, z], [XL + 156, 1250, z], [XL + 156, YF, z], [XL + 140, YF, z]], '#5e3e28');
  { const [vx, vy] = P(XL + 90, 1220, 1800); ctx.fillStyle = '#7f95a0'; rr(ctx, vx - 8, vy - 36, 16, 36, 5); ctx.fill(); ctx.fillStyle = '#e8d0a0'; ctx.beginPath(); ctx.arc(vx, vy - 44, 9, 0, 7); ctx.fill(); }
  // floor boards along Z with a plum runner
  poly([[XL, YF, 0], [XR, YF, 0], [XR, YF, ZB], [XL, YF, ZB]], '#a57446');
  for (let X = XL; X <= XR; X += 70) {
    const [a, b] = P(X, YF, 0), [c, d] = P(X, YF, ZB);
    ctx.strokeStyle = 'rgba(80,50,28,0.35)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c, d); ctx.stroke();
  }
  poly([[480, YF, 120], [800, YF, 120], [790, YF, ZB - 80], [490, YF, ZB - 80]], '#7b3b55');
  poly([[500, YF, 140], [780, YF, 140], [770, YF, ZB - 100], [510, YF, ZB - 100]], '#8f5068');
  poly([[530, YF, 170], [750, YF, 170], [740, YF, ZB - 130], [540, YF, ZB - 130]], '#a8687a');
  // sunlight from the back doorway: glow on the floor + a bright patch
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const [gx, gy] = P(680, YF, ZB - 300);
  softGlow(ctx, gx, gy, 260, '#ffd9a0', 0.55, 0.45);
  const [sx, sy] = P(700, 1100, ZB);
  softGlow(ctx, sx, sy, 300, '#ffe2b0', 0.45, 0.9);
  // slanted sunbeam stripes on the right wall
  for (const z of [700, 1300]) poly([[XR, 760, z], [XR, 760, z + 260], [XR, YF, z + 520], [XR, YF, z + 260]], 'rgba(255,220,160,0.35)');
  ctx.restore();
  // depth darkening toward the door (inside face of the facade casts shade)
  ctx.fillStyle = rad(ctx, 640, 1110, 120, 420, [[0, 'rgba(60,35,20,0)'], [1, 'rgba(60,35,20,0.32)']]);
  ctx.fillRect(DOOR.x0, DOOR.y0, DOOR.x1 - DOOR.x0, DOOR.y1 - DOOR.y0);
  // jamb reveals (wall thickness 180): head (seen from below), left, right, threshold
  const T = 180;
  poly([[DOOR.x0, DOOR.y0, 0], [DOOR.x1, DOOR.y0, 0], [DOOR.x1, DOOR.y0, T], [DOOR.x0, DOOR.y0, T]], '#d8d2c4');
  poly([[DOOR.x0, DOOR.y0, 0], [DOOR.x0, DOOR.y0, T], [DOOR.x0, DOOR.y1, T], [DOOR.x0, DOOR.y1, 0]], '#cfc8b8');
  poly([[DOOR.x1, DOOR.y0, 0], [DOOR.x1, DOOR.y0, T], [DOOR.x1, DOOR.y1, T], [DOOR.x1, DOOR.y1, 0]], '#bfb7a6');
  poly([[DOOR.x0, DOOR.y1, 0], [DOOR.x1, DOOR.y1, 0], [DOOR.x1, DOOR.y1, T], [DOOR.x0, DOOR.y1, T]], '#b08a55');
  const [hx, hy] = P(DOOR.x0, DOOR.y0, T); ctx.fillStyle = 'rgba(60,40,25,0.25)'; ctx.fillRect(hx, hy, 300, 3);
  ctx.restore();
}

// ---------------------------------------------------------------- door texture (flat, door-local coords 0..340 x 0..830)
const DW = 340, DH = 830;
function paintDoorTex(ctx, R) {
  const G = '#3f5e4f';
  ctx.fillStyle = G; ctx.fillRect(0, 0, DW, DH);
  // painted wood grain, vertical on stiles
  for (let i = 0; i < 90; i++) {
    const x = R() * DW, y = R() * DH, l = 40 + R() * 160;
    ctx.strokeStyle = rgba(R() < 0.5 ? '#2f4a3e' : '#557565', 0.18); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (R() - 0.5) * 2, y + l); ctx.stroke();
  }
  // gentle light from the upper right
  ctx.fillStyle = lin(ctx, 0, 0, DW, DH, [[0, 'rgba(20,30,25,0.12)'], [0.6, 'rgba(255,255,255,0)'], [1, 'rgba(20,30,25,0.18)']]);
  ctx.fillRect(0, 0, DW, DH);
  ctx.fillStyle = lin(ctx, 0, 0, DW, 0, [[0, 'rgba(10,20,15,0.10)'], [1, 'rgba(255,245,220,0.08)']]); ctx.fillRect(0, 0, DW, DH);
  const panel = (x, y, w, h) => {
    // recess
    ctx.fillStyle = shade(G, -0.08); ctx.fillRect(x, y, w, h);
    // bevel: lit top/right edges, shaded bottom/left (light from upper right)
    const b = 12;
    ctx.fillStyle = shade(G, 0.12); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w - b, y + b); ctx.lineTo(x + b, y + b); ctx.closePath(); ctx.fill();
    ctx.fillStyle = shade(G, 0.06); ctx.beginPath(); ctx.moveTo(x + w, y); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - b, y + h - b); ctx.lineTo(x + w - b, y + b); ctx.closePath(); ctx.fill();
    ctx.fillStyle = shade(G, -0.22); ctx.beginPath(); ctx.moveTo(x, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - b, y + h - b); ctx.lineTo(x + b, y + h - b); ctx.closePath(); ctx.fill();
    ctx.fillStyle = shade(G, -0.15); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + b, y + b); ctx.lineTo(x + b, y + h - b); ctx.lineTo(x, y + h); ctx.closePath(); ctx.fill();
    // raised field
    ctx.fillStyle = lin(ctx, x + b, y + b, x + w - b, y + h - b, [[0, shade(G, 0.03)], [1, shade(G, -0.04)]]);
    ctx.fillRect(x + b, y + b, w - 2 * b, h - 2 * b);
    ctx.strokeStyle = 'rgba(15,25,20,0.35)'; ctx.lineWidth = 1.5; ctx.strokeRect(x, y, w, h);
  };
  panel(46, 262, 112, 150); panel(182, 262, 112, 150);
  panel(46, 520, 112, 236); panel(182, 520, 112, 236);
  // glass pane at the top with moulding and two muntins
  const gx = 46, gy = 40, gw = 248, gh = 186;
  ctx.fillStyle = shade(G, -0.25); ctx.fillRect(gx - 8, gy - 8, gw + 16, gh + 16);
  ctx.fillStyle = shade(G, 0.1); ctx.fillRect(gx - 8, gy - 8, gw + 16, 4); ctx.fillRect(gx + gw + 4, gy - 8, 4, gh + 16);
  ctx.fillStyle = lin(ctx, gx, gy, gx + gw, gy + gh, [[0, '#8d9a92'], [0.45, '#5e6b62'], [1, '#3f4a44']]);
  ctx.fillRect(gx, gy, gw, gh);
  // faint lace behind the glass
  ctx.fillStyle = 'rgba(235,230,215,0.28)'; ctx.fillRect(gx, gy, gw, gh);
  for (let i = 0; i < 40; i++) { ctx.fillStyle = 'rgba(250,246,235,0.25)'; ctx.beginPath(); ctx.arc(gx + 10 + R() * (gw - 20), gy + 10 + R() * (gh - 20), 3 + R() * 4, 0, 7); ctx.fill(); }
  // reflections
  ctx.fillStyle = 'rgba(255,255,255,0.28)'; ctx.beginPath(); ctx.moveTo(gx + gw * 0.55, gy); ctx.lineTo(gx + gw * 0.7, gy); ctx.lineTo(gx + gw * 0.4, gy + gh); ctx.lineTo(gx + gw * 0.25, gy + gh); ctx.closePath(); ctx.fill();
  ctx.fillStyle = G; ctx.fillRect(gx + gw / 3 - 3, gy, 6, gh); ctx.fillRect(gx + (2 * gw) / 3 - 3, gy, 6, gh);
  // brass mail slot on the lock rail
  ctx.fillStyle = lin(ctx, 0, 440, 0, 472, [[0, '#e8cf8e'], [0.5, '#b38d4a'], [1, '#7a5e2e']]); rr(ctx, 110, 440, 120, 30, 4); ctx.fill();
  ctx.fillStyle = '#4b3a20'; rr(ctx, 122, 452, 96, 7, 3); ctx.fill();
  // knob backplate, knob, keyhole (knob centre at door-local (305, 450) == world (735, 1120))
  ctx.fillStyle = 'rgba(10,20,15,0.35)'; rr(ctx, 291, 412, 30, 118, 12); ctx.fill();
  ctx.fillStyle = lin(ctx, 288, 0, 318, 0, [[0, '#7a5c2c'], [0.4, '#e3c785'], [1, '#8a6a34']]); rr(ctx, 289, 408, 30, 118, 13); ctx.fill();
  ctx.fillStyle = 'rgba(20,15,5,0.4)'; ctx.beginPath(); ctx.arc(301, 455, 17, 0, 7); ctx.fill();
  ctx.fillStyle = rad(ctx, 309, 444, 1, 19, [[0, '#fff1c2'], [0.35, '#d9b56a'], [0.8, '#9a7438'], [1, '#6a4e22']]);
  ctx.beginPath(); ctx.arc(305, 450, 17, 0, 7); ctx.fill();
  ctx.fillStyle = '#2a1e0e'; ctx.beginPath(); ctx.arc(304, 494, 4, 0, 7); ctx.fill(); ctx.beginPath(); ctx.moveTo(301, 495); ctx.lineTo(307, 495); ctx.lineTo(308, 508); ctx.lineTo(300, 508); ctx.closePath(); ctx.fill();
  // brass kick plate
  ctx.fillStyle = lin(ctx, 0, 774, 0, 818, [[0, '#d8bb78'], [0.5, '#b08a48'], [1, '#856532']]); ctx.fillRect(20, 776, 300, 44);
  ctx.fillStyle = 'rgba(255,245,210,0.25)'; ctx.fillRect(20, 776, 300, 3);
  // worn paint near the knob and bottom edge
  for (let i = 0; i < 14; i++) { ctx.fillStyle = 'rgba(120,140,125,0.25)'; ctx.beginPath(); ctx.ellipse(270 + R() * 50, 380 + R() * 180, 2 + R() * 4, 1 + R() * 2, 0, 0, 7); ctx.fill(); }
  // edges
  ctx.fillStyle = 'rgba(255,250,235,0.12)'; ctx.fillRect(DW - 3, 0, 3, DH);
  ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(0, 0, 3, DH); ctx.fillRect(0, DH - 2, DW, 2);
}

// ---------------------------------------------------------------- door trim, window, plants, floor, steps, garden
function paintDoorTrim(ctx) {
  // shadow cast by trim onto the bricks (sun upper right -> shadow lower left)
  blurred(ctx, 10, () => { ctx.fillStyle = 'rgba(30,18,12,0.35)'; ctx.fillRect(388, 618, 26, 890); ctx.fillRect(388, 612, 440, 20); });
  // header cornice
  ctx.fillStyle = lin(ctx, 0, 596, 0, 640, [[0, '#f4f1e8'], [0.4, '#e6e1d4'], [1, '#c9c3b4']]);
  ctx.fillRect(376, 598, 448, 42);
  ctx.fillStyle = '#faf8f1'; ctx.fillRect(370, 592, 460, 9);
  ctx.fillStyle = 'rgba(70,60,50,0.3)'; ctx.fillRect(376, 638, 448, 2);
  // side casings (left one in a touch of shade, right one catching the sun)
  ctx.fillStyle = lin(ctx, 400, 0, 430, 0, [[0, '#d9d4c6'], [1, '#ebe7dc']]); ctx.fillRect(400, 640, 30, 860);
  ctx.fillStyle = lin(ctx, 770, 0, 800, 0, [[0, '#ece8de'], [1, '#faf8f2']]); ctx.fillRect(770, 640, 30, 860);
  ctx.fillStyle = lin(ctx, 0, 640, 0, 670, [[0, '#e9e5da'], [1, '#d8d3c5']]); ctx.fillRect(430, 640, 340, 30);
  ctx.fillStyle = 'rgba(70,60,50,0.28)'; ctx.fillRect(428, 668, 344, 2); ctx.fillRect(428, 668, 2, 832); ctx.fillRect(770, 668, 2, 832);
  // plinth blocks
  ctx.fillStyle = '#d6d0c2'; ctx.fillRect(398, 1440, 34, 60); ctx.fillRect(768, 1440, 34, 60);
}
function paintWindow(ctx, R) {
  const x0 = 950, x1 = 1300, y0 = 760, y1 = 1240;
  blurred(ctx, 10, () => { ctx.fillStyle = 'rgba(30,18,12,0.35)'; ctx.fillRect(x0 - 40, y0 - 22, 30, y1 - y0 + 50); ctx.fillRect(x0 - 40, y0 - 30, x1 - x0 + 60, 20); });
  // trim
  ctx.fillStyle = '#ebe7dc'; ctx.fillRect(x0 - 24, y0 - 24, x1 - x0 + 48, y1 - y0 + 24);
  ctx.fillStyle = '#f7f5ee'; ctx.fillRect(x0 - 32, y0 - 34, x1 - x0 + 64, 14);
  // glass: sky + soft tree reflection
  ctx.fillStyle = lin(ctx, 0, y0, 0, y1, [[0, '#a9bccb'], [0.5, '#8c9ea9'], [1, '#6f7f86']]); ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.clip();
  for (let i = 0; i < 9; i++) { ctx.fillStyle = 'rgba(95,115,95,0.35)'; ctx.beginPath(); ctx.ellipse(x0 + R() * (x1 - x0), y0 + 280 + R() * 120, 40 + R() * 40, 30 + R() * 20, 0, 0, 7); ctx.fill(); }
  ctx.restore();
  // lace curtains inside: two gathered panels + valance, scalloped hems, dotted pattern
  const lace = (lx0, lx1, ly0, ly1, scal) => {
    ctx.save(); ctx.beginPath(); ctx.moveTo(lx0, ly0); ctx.lineTo(lx1, ly0); ctx.lineTo(lx1, ly1);
    for (let x = lx1; x > lx0; x -= scal) ctx.quadraticCurveTo(x - scal / 2, ly1 + scal * 0.5, x - scal, ly1);
    ctx.closePath(); ctx.clip();
    ctx.fillStyle = 'rgba(246,242,232,0.78)'; ctx.fillRect(lx0, ly0, lx1 - lx0, ly1 - ly0 + scal);
    for (let x = lx0 + 6; x < lx1; x += 16) for (let y = ly0 + 8; y < ly1 + scal; y += 16) {
      ctx.fillStyle = 'rgba(150,150,140,0.28)'; ctx.beginPath(); ctx.arc(x + ((y / 16) % 2) * 8, y, 3.2, 0, 7); ctx.fill();
    }
    for (let x = lx0; x < lx1; x += 22) { ctx.fillStyle = 'rgba(120,115,105,0.10)'; ctx.fillRect(x, ly0, 8, ly1 - ly0 + scal); }
    ctx.restore();
  };
  lace(x0, x0 + 120, y0, y1 - 20, 14); lace(x1 - 120, x1, y0, y1 - 20, 14);
  lace(x0, x1, y0, y0 + 90, 18);
  // sashes
  ctx.fillStyle = '#f2efe6';
  ctx.fillRect(x0, y0, x1 - x0, 14); ctx.fillRect(x0, y1 - 18, x1 - x0, 18); ctx.fillRect(x0, y0, 14, y1 - y0); ctx.fillRect(x1 - 14, y0, 14, y1 - y0);
  ctx.fillRect(x0, 990, x1 - x0, 22); ctx.fillRect((x0 + x1) / 2 - 5, y0, 10, y1 - y0);
  ctx.fillStyle = 'rgba(80,75,65,0.3)'; ctx.fillRect(x0 + 14, 1012, x1 - x0 - 28, 2); ctx.fillRect(x0 + 14, y0 + 14, x1 - x0 - 28, 2);
  // glass sheen
  ctx.fillStyle = 'rgba(255,255,255,0.14)'; ctx.beginPath(); ctx.moveTo(x0 + 200, y0); ctx.lineTo(x0 + 280, y0); ctx.lineTo(x0 + 120, y1); ctx.lineTo(x0 + 40, y1); ctx.closePath(); ctx.fill();
  // sill
  ctx.fillStyle = lin(ctx, 0, 1240, 0, 1262, [[0, '#fbfaf5'], [1, '#d4cfc2']]); ctx.fillRect(x0 - 36, 1240, x1 - x0 + 72, 22);
  // flower box on two brackets, resting under the sill
  blurred(ctx, 12, () => { ctx.fillStyle = 'rgba(30,18,12,0.4)'; ctx.fillRect(x0 - 30, 1270, x1 - x0 + 40, 90); });
  for (const bx of [x0 + 20, x1 - 40]) { ctx.fillStyle = '#d9d4c8'; ctx.beginPath(); ctx.moveTo(bx, 1330); ctx.lineTo(bx + 20, 1330); ctx.lineTo(bx + 20, 1380); ctx.closePath(); ctx.fill(); }
  // flowers & trailing ivy (behind the box front)
  const fl = (x, y, r, c) => { for (let k = 0; k < 5; k++) { const a = (k / 5) * Math.PI * 2; ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x + Math.cos(a) * r * 0.6, y + Math.sin(a) * r * 0.6, r * 0.55, 0, 7); ctx.fill(); } ctx.fillStyle = '#e8c45a'; ctx.beginPath(); ctx.arc(x, y, r * 0.3, 0, 7); ctx.fill(); };
  for (let i = 0; i < 26; i++) paintLeaf(ctx, x0 - 10 + R() * (x1 - x0 + 20), 1250 + R() * 30, 20 + R() * 8, -Math.PI / 2 + (R() - 0.5) * 2.6, R() < 0.5 ? '#557343' : '#6a8a50');
  const cols = ['#c9575a', '#e7e2da', '#a88cc0', '#d98a8f', '#efe9df'];
  for (let i = 0; i < 22; i++) fl(x0 + R() * (x1 - x0), 1236 + R() * 30, 9 + R() * 5, cols[Math.floor(R() * cols.length)]);
  ctx.fillStyle = lin(ctx, 0, 1262, 0, 1332, [[0, '#7d8f78'], [1, '#5c6c58']]); rr(ctx, x0 - 30, 1262, x1 - x0 + 60, 70, 4); ctx.fill();
  ctx.fillStyle = 'rgba(255,250,230,0.25)'; ctx.fillRect(x0 - 30, 1262, x1 - x0 + 60, 4);
  for (let x = x0 - 10; x < x1 + 20; x += 52) { ctx.fillStyle = 'rgba(40,50,38,0.25)'; ctx.fillRect(x, 1272, 2, 54); }
  for (let i = 0; i < 6; i++) { // trailing ivy over the front
    let x = x0 + R() * (x1 - x0), y = 1300;
    const len = 60 + R() * 90;
    for (let s = 0; s < len; s += 16) paintLeaf(ctx, x + Math.sin(s * 0.05 + i) * 8, y + s, 13, Math.PI / 2 + (s % 32 ? 0.8 : -0.8), '#5b7a46');
  }
}
function paintPottedPlant(ctx, cx, by, R, tall) {
  // sun upper right -> soft shadow on floor & wall to the left
  blurred(ctx, 16, () => { ctx.fillStyle = 'rgba(30,20,15,0.32)'; ctx.beginPath(); ctx.ellipse(cx - 60, by - 8, 90, 18, 0, 0, 7); ctx.fill(); ctx.fillRect(cx - 120, by - tall * 0.8, 70, tall * 0.75); });
  contactShadow(ctx, cx - 4, by, 70, 12, 0.6);
  // pot: glazed stoneware
  const pw = 112, ph = 120;
  ctx.fillStyle = lin(ctx, cx - pw / 2, 0, cx + pw / 2, 0, [[0, '#4e5a5c'], [0.55, '#7f8f90'], [0.8, '#97a6a5'], [1, '#5d6a6b']]);
  ctx.beginPath(); ctx.moveTo(cx - pw / 2, by - ph); ctx.lineTo(cx + pw / 2, by - ph); ctx.quadraticCurveTo(cx + pw / 2, by - 20, cx + pw / 2 - 16, by); ctx.lineTo(cx - pw / 2 + 16, by); ctx.quadraticCurveTo(cx - pw / 2, by - 20, cx - pw / 2, by - ph); ctx.fill();
  ctx.fillStyle = '#9aa9a8'; rr(ctx, cx - pw / 2 - 6, by - ph - 12, pw + 12, 16, 5); ctx.fill();
  ctx.fillStyle = '#3c2c22'; ctx.beginPath(); ctx.ellipse(cx, by - ph - 8, pw / 2, 6, 0, 0, 7); ctx.fill();
  // fern / boxwood mix: arching fronds
  const N = 22;
  for (let i = 0; i < N; i++) {
    const a = -Math.PI / 2 + (i / (N - 1) - 0.5) * 2.6 + (R() - 0.5) * 0.2, len = tall * (0.6 + R() * 0.4);
    const x0 = cx + (R() - 0.5) * 20, y0 = by - ph - 6;
    const ex = x0 + Math.cos(a) * len, ey = y0 + Math.sin(a) * len * 0.9 + Math.abs(Math.cos(a)) * len * 0.35;
    const mx = x0 + Math.cos(a) * len * 0.5, my = y0 + Math.sin(a) * len * 0.75;
    const col = R() < 0.5 ? '#4f6e3e' : '#62844a';
    ctx.strokeStyle = shade(col, -0.2); ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(mx, my, ex, ey); ctx.stroke();
    for (let k = 1; k < 12; k++) {
      const t = k / 12, x = (1 - t) * (1 - t) * x0 + 2 * (1 - t) * t * mx + t * t * ex, y = (1 - t) * (1 - t) * y0 + 2 * (1 - t) * t * my + t * t * ey;
      const sz = 16 * (1 - t * 0.6);
      const lit = x > cx ? 0.08 : -0.06;
      paintLeaf(ctx, x, y, sz, a - 1.2, shade(col, lit));
      paintLeaf(ctx, x, y, sz, a + 1.2 - Math.PI * 0 + Math.PI / 2 * 0, shade(col, lit - 0.05));
    }
  }
}
function paintLeaf(ctx, x, y, s, ang, col) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
  ctx.fillStyle = col;
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.bezierCurveTo(s * 0.4, -s * 0.5, s * 1.0, -s * 0.3, s * 1.2, 0); ctx.bezierCurveTo(s * 1.0, s * 0.3, s * 0.4, s * 0.5, 0, 0); ctx.fill();
  ctx.restore();
}
function paintMailbox(ctx) {
  const x = 836, y = 930, w = 78, h = 96;
  blurred(ctx, 8, () => { ctx.fillStyle = 'rgba(30,18,12,0.4)'; rr(ctx, x - 14, y + 12, w, h, 8); ctx.fill(); });
  ctx.fillStyle = lin(ctx, x, 0, x + w, 0, [[0, '#1f2322'], [0.6, '#3c4341'], [1, '#2a2f2e']]); rr(ctx, x, y, w, h, 8); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, y - 10, 0, y + 14, [[0, '#4a524f'], [1, '#262b2a']]); rr(ctx, x - 6, y - 8, w + 12, 22, 6); ctx.fill();
  ctx.fillStyle = '#c9a65e'; rr(ctx, x + w / 2 - 14, y + 40, 28, 8, 3); ctx.fill();
  ctx.fillStyle = 'rgba(255,245,220,0.18)'; ctx.fillRect(x + w - 18, y + 16, 5, h - 26);
}
function paintBench(ctx, R) {
  // slatted wooden bench against the wall, left of the door
  const x0 = -330, x1 = 170, seat = 1330;
  blurred(ctx, 18, () => { ctx.fillStyle = 'rgba(30,20,15,0.35)'; ctx.fillRect(x0 - 50, seat - 160, x1 - x0, 200); ctx.beginPath(); ctx.ellipse((x0 + x1) / 2 - 40, 1515, (x1 - x0) / 2 + 20, 18, 0, 0, 7); ctx.fill(); });
  const W = '#8a6a4c';
  // back slats
  for (let i = 0; i < 3; i++) { ctx.fillStyle = lin(ctx, 0, seat - 190 + i * 50, 0, seat - 160 + i * 50, [[0, shade(W, 0.12)], [1, shade(W, -0.1)]]); rr(ctx, x0, seat - 190 + i * 50, x1 - x0, 32, 4); ctx.fill(); }
  // legs
  for (const lx of [x0 + 20, x1 - 50]) { ctx.fillStyle = lin(ctx, lx, 0, lx + 30, 0, [[0, shade(W, -0.25)], [1, shade(W, -0.05)]]); ctx.fillRect(lx, seat - 210, 30, 1520 - seat + 210); }
  // seat (top surface + front edge) + cushion
  ctx.fillStyle = shade(W, 0.15); ctx.beginPath(); ctx.moveTo(x0 - 10, seat); ctx.lineTo(x1 + 10, seat); ctx.lineTo(x1 + 16, seat + 26); ctx.lineTo(x0 - 16, seat + 26); ctx.closePath(); ctx.fill();
  ctx.fillStyle = shade(W, -0.12); ctx.fillRect(x0 - 16, seat + 26, x1 - x0 + 32, 18);
  ctx.fillStyle = lin(ctx, 0, seat - 40, 0, seat + 6, [[0, '#c7b9a0'], [1, '#a8987e']]); rr(ctx, x0 + 10, seat - 34, 260, 44, 16); ctx.fill();
  ctx.strokeStyle = 'rgba(120,100,80,0.4)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x0 + 140, seat - 30); ctx.lineTo(x0 + 140, seat + 6); ctx.stroke();
  // a folded plaid throw at the right end
  ctx.fillStyle = '#7b5a72'; rr(ctx, x1 - 150, seat - 46, 130, 52, 10); ctx.fill();
  ctx.strokeStyle = 'rgba(230,210,200,0.35)'; ctx.lineWidth = 3; for (let k = 0; k < 4; k++) { ctx.beginPath(); ctx.moveTo(x1 - 140 + k * 32, seat - 46); ctx.lineTo(x1 - 140 + k * 32, seat + 6); ctx.stroke(); }
  ctx.beginPath(); ctx.moveTo(x1 - 150, seat - 22); ctx.lineTo(x1 - 20, seat - 22); ctx.stroke();
  contactShadow(ctx, x0 + 30, 1520, 40, 8, 0.6); contactShadow(ctx, x1 - 40, 1520, 40, 8, 0.6);
}
function paintFloor(ctx, R) {
  const y0 = 1500, y1 = 1700, base = '#958d80';
  ctx.fillStyle = base; ctx.fillRect(EXT.x0, y0, EXT.x1 - EXT.x0, y1 - y0);
  // boards run toward the camera (perpendicular to the house), in perspective
  const f = (y1 - FVP.y) / (y0 - FVP.y);
  let k = 0;
  for (let x = EXT.x0 - 400; x < EXT.x1 + 400; x += 64, k++) {
    const xa = FVP.x + (x - FVP.x) * f, xb = FVP.x + (x + 64 - FVP.x) * f;
    ctx.fillStyle = shade(base, (R() - 0.5) * 0.06);
    ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(x + 64, y0); ctx.lineTo(xb, y1); ctx.lineTo(xa, y1); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(55,50,45,0.42)'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(xa, y1); ctx.stroke();
    // worn paint flecks
    for (let j = 0; j < 3; j++) { const t = R(), y = y0 + t * 200, ff = (y - FVP.y) / (y0 - FVP.y); ctx.fillStyle = 'rgba(110,90,70,0.18)'; ctx.fillRect(FVP.x + (x + 10 + R() * 40 - FVP.x) * ff, y, 6 + R() * 16, 1.5); }
  }
  // shade near the wall, sunlight on the front half (porch roof edge)
  ctx.fillStyle = lin(ctx, 0, y0, 0, y1, [[0, 'rgba(35,28,22,0.35)'], [0.35, 'rgba(35,28,22,0.12)'], [0.55, 'rgba(255,236,200,0)'], [1, 'rgba(255,236,200,0)']]);
  ctx.fillRect(EXT.x0, y0, EXT.x1 - EXT.x0, y1 - y0);
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.filter = 'blur(14px)';
  ctx.fillStyle = 'rgba(255,230,180,0.30)';
  ctx.beginPath(); ctx.moveTo(EXT.x0 - 40, 1612); ctx.lineTo(EXT.x1 + 40, 1580); ctx.lineTo(EXT.x1 + 40, 1720); ctx.lineTo(EXT.x0 - 40, 1720); ctx.closePath(); ctx.fill();
  ctx.restore();
  // shadow of the right post across the floor (to the lower left)
  blurred(ctx, 12, () => { ctx.fillStyle = 'rgba(40,30,25,0.28)'; ctx.beginPath(); ctx.moveTo(1500, 1690); ctx.lineTo(1570, 1690); ctx.lineTo(1300, 1600); ctx.lineTo(1250, 1600); ctx.closePath(); ctx.fill(); });
  // contact shadow along the wall
  ctx.fillStyle = lin(ctx, 0, y0, 0, y0 + 26, [[0, 'rgba(25,18,14,0.5)'], [1, 'rgba(25,18,14,0)']]); ctx.fillRect(EXT.x0, y0, EXT.x1 - EXT.x0, 26);
  // front nosing board
  ctx.fillStyle = lin(ctx, 0, 1696, 0, 1722, [[0, '#f1ede3'], [1, '#c9c3b5']]); ctx.fillRect(EXT.x0, 1696, EXT.x1 - EXT.x0, 26);
}
function paintDoormat(ctx, R) {
  const pts = [[446, 1506], [754, 1506], [768, 1564], [432, 1564]];
  blurred(ctx, 5, () => { ctx.fillStyle = 'rgba(30,20,12,0.4)'; ctx.beginPath(); ctx.moveTo(436, 1512); ctx.lineTo(760, 1512); ctx.lineTo(772, 1572); ctx.lineTo(426, 1572); ctx.closePath(); ctx.fill(); });
  ctx.fillStyle = '#5e4630'; ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#a88a5d'; ctx.beginPath(); ctx.moveTo(458, 1512); ctx.lineTo(742, 1512); ctx.lineTo(753, 1557); ctx.lineTo(447, 1557); ctx.closePath(); ctx.fill();
  ctx.save(); ctx.clip();
  for (let i = 0; i < 500; i++) { const x = 440 + R() * 320, y = 1510 + R() * 50; ctx.strokeStyle = rgba(R() < 0.5 ? '#7d6342' : '#c4a676', 0.5); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (R() - 0.5) * 2, y + 3); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(80,58,35,0.65)'; ctx.lineWidth = 3;
  for (let i = 0; i < 6; i++) { const x = 500 + i * 42; ctx.beginPath(); ctx.moveTo(x, 1518); ctx.lineTo(x + 14, 1534); ctx.lineTo(x, 1550); ctx.stroke(); }
  ctx.restore();
}
function paintSteps(ctx, R) {
  // three steps down (risers face the camera), stringers on both sides
  const levels = [[1700, 1722, 1790], [1790, 1818, 1890], [1890, 1920, 2000]]; // [treadTop, treadBottom(nosing), riserBottom]
  for (let i = 0; i < 3; i++) {
    const [t0, t1, r1] = levels[i], grow = i * 16;
    const xl = 820 - grow, xr = 1380 + grow;
    if (i > 0) { // tread
      ctx.fillStyle = lin(ctx, 0, t0, 0, t1, [[0, '#a59d8f'], [1, '#beb6a6']]); ctx.fillRect(xl, t0, xr - xl, t1 - t0);
      ctx.fillStyle = 'rgba(255,240,210,0.3)'; ctx.fillRect(xl, t1 - 3, xr - xl, 3);
    }
    // riser (white paint, scuffed)
    ctx.fillStyle = lin(ctx, 0, t1, 0, r1, [[0, '#d8d3c6'], [1, '#c4beb0']]); ctx.fillRect(xl, i === 0 ? 1722 : t1, xr - xl, r1 - (i === 0 ? 1722 : t1));
    ctx.fillStyle = 'rgba(40,30,22,0.28)'; ctx.fillRect(xl, i === 0 ? 1722 : t1, xr - xl, 5);
    for (let k = 0; k < 6; k++) { ctx.fillStyle = 'rgba(120,110,95,0.25)'; ctx.fillRect(xl + R() * (xr - xl - 30), r1 - 12 - R() * 30, 10 + R() * 30, 2); }
  }
  // stringers
  ctx.fillStyle = lin(ctx, 770, 0, 820, 0, [[0, '#cfc9bb'], [1, '#e4dfd3']]);
  ctx.beginPath(); ctx.moveTo(796, 1700); ctx.lineTo(820, 1700); ctx.lineTo(788, 2000); ctx.lineTo(764, 2000); ctx.closePath(); ctx.fill();
  ctx.fillStyle = lin(ctx, 1380, 0, 1440, 0, [[0, '#f0ece2'], [1, '#d9d3c6']]);
  ctx.beginPath(); ctx.moveTo(1380, 1700); ctx.lineTo(1404, 1700); ctx.lineTo(1436, 2000); ctx.lineTo(1412, 2000); ctx.closePath(); ctx.fill();
  // post shadow on the steps
  blurred(ctx, 10, () => { ctx.fillStyle = 'rgba(40,30,25,0.18)'; ctx.fillRect(1250, 1720, 70, 280); });
}
function paintSkirt(ctx, R) {
  // lattice under the porch edge (both sides of the steps)
  for (const [x0, x1] of [[EXT.x0, 836], [1366, EXT.x1]]) {
    ctx.save(); ctx.beginPath(); ctx.rect(x0, 1722, x1 - x0, 300); ctx.clip();
    ctx.fillStyle = '#2b2622'; ctx.fillRect(x0, 1722, x1 - x0, 300);
    ctx.strokeStyle = '#d9d3c5'; ctx.lineWidth = 9;
    for (let x = x0 - 400; x < x1 + 400; x += 46) { ctx.beginPath(); ctx.moveTo(x, 1722); ctx.lineTo(x + 300, 2022); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x, 1722); ctx.lineTo(x - 300, 2022); ctx.stroke(); }
    ctx.fillStyle = lin(ctx, 0, 1722, 0, 1780, [[0, 'rgba(25,18,14,0.55)'], [1, 'rgba(25,18,14,0)']]); ctx.fillRect(x0, 1722, x1 - x0, 60);
    ctx.restore();
    ctx.fillStyle = '#e6e1d5'; ctx.fillRect(x0, 1722, x1 - x0, 12);
  }
}
function paintGarden(ctx, R) {
  // lawn
  ctx.fillStyle = lin(ctx, 0, 1990, 0, 2400, [[0, '#6f8a4f'], [1, '#86a05c']]); ctx.fillRect(EXT.x0, 1990, EXT.x1 - EXT.x0, 410);
  const N = makeNoise(77);
  for (let i = 0; i < 5200; i++) {
    const x = lerp(EXT.x0, EXT.x1, R()), y = lerp(1995, 2400, R()), h = 6 + (y - 1990) * 0.03 + R() * 8;
    const v = N(x * 0.01, y * 0.02);
    ctx.strokeStyle = rgba(v > 0.55 ? '#9db36a' : v < 0.4 ? '#56703f' : '#78944f', 0.55); ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (R() - 0.3) * 4, y - h); ctx.stroke();
  }
  // stone path from the steps toward the camera
  const pathL = (y) => lerp(900, 880, (y - 2000) / 400), pathR = (y) => lerp(1300, 1320, (y - 2000) / 400);
  let y = 2004;
  while (y < 2420) {
    const h = 34 + (y - 2000) * 0.06 + R() * 10;
    let x = pathL(y);
    while (x < pathR(y) - 20) {
      const w = 80 + R() * 70, xe = Math.min(x + w, pathR(y));
      const col = shade('#b7ab98', (R() - 0.5) * 0.12);
      contactShadow(ctx, (x + xe) / 2 - 6, y + h - 4, (xe - x) / 2 + 6, 6, 0.35);
      ctx.fillStyle = lin(ctx, 0, y, 0, y + h, [[0, shade(col, 0.08)], [1, shade(col, -0.08)]]);
      ctx.beginPath(); ctx.moveTo(x + 4 + R() * 4, y + 2); ctx.lineTo(xe - 4 - R() * 4, y + 1 + R() * 3); ctx.lineTo(xe - 2, y + h - 6); ctx.lineTo(x + 6, y + h - 4 - R() * 3); ctx.closePath(); ctx.fill();
      for (let k = 0; k < 4; k++) { ctx.fillStyle = rgba(R() < 0.5 ? '#8f8474' : '#d2c7b4', 0.35); ctx.beginPath(); ctx.ellipse(x + 10 + R() * (xe - x - 20), y + 6 + R() * (h - 14), 2 + R() * 6, 1 + R() * 3, 0, 0, 7); ctx.fill(); }
      x = xe + 8 + R() * 6;
    }
    y += h + 8;
  }
  // shrubs & hydrangeas in front of the lattice (with shadows to the left)
  const shrub = (cx, by, w, h, flowers) => {
    blurred(ctx, 16, () => { ctx.fillStyle = 'rgba(30,40,20,0.4)'; ctx.beginPath(); ctx.ellipse(cx - w * 0.35, by + 6, w * 0.6, 22, 0, 0, 7); ctx.fill(); });
    for (let i = 0; i < 26; i++) {
      const a = R() * Math.PI, r = R();
      const x = cx + Math.cos(a) * w * 0.5 * r * 1.1, yy = by - Math.sin(a) * h * r * 0.95 - 10;
      const lit = (x - cx) / w * 0.3 - (yy - by) / h * 0.12;
      ctx.fillStyle = shade('#55703f', lit - 0.05 + (R() - 0.5) * 0.08);
      ctx.beginPath(); ctx.arc(x, yy, 24 + R() * 20, 0, 7); ctx.fill();
    }
    if (flowers) for (let i = 0; i < 9; i++) {
      const x = cx + (R() - 0.5) * w * 0.8, yy = by - h * (0.3 + R() * 0.6);
      const c = flowers[Math.floor(R() * flowers.length)];
      for (let k = 0; k < 14; k++) { ctx.fillStyle = shade(c, (R() - 0.5) * 0.15); ctx.beginPath(); ctx.arc(x + (R() - 0.5) * 30, yy + (R() - 0.5) * 24, 6 + R() * 3, 0, 7); ctx.fill(); }
    }
  };
  shrub(-300, 2050, 260, 230, ['#b7b0d6', '#d7c3dd']);
  shrub(-60, 2060, 240, 190, null);
  shrub(200, 2050, 280, 240, ['#c9b6dc', '#e0cfe2', '#a9b8da']);
  shrub(480, 2060, 240, 180, null);
  shrub(690, 2050, 170, 160, ['#f0ece2']);
  shrub(1520, 2050, 260, 240, ['#c9b6dc', '#b8b4d8']);
  // low flowers edging the path
  for (let i = 0; i < 60; i++) {
    const side = i % 2 ? -1 : 1, yy = 2020 + R() * 360, x = side < 0 ? 900 - 18 - R() * 50 : 1300 + 18 + R() * 50;
    ctx.fillStyle = ['#efe9df', '#d9a7b8', '#b9a6d4', '#f2d58a'][i % 4];
    ctx.beginPath(); ctx.arc(x, yy, 4 + R() * 3, 0, 7); ctx.fill();
  }
  // sunlight warmth on the lawn
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.fillStyle = lin(ctx, EXT.x1, 2000, EXT.x0, 2400, [[0, 'rgba(255,236,190,0.22)'], [1, 'rgba(255,236,190,0.05)']]); ctx.fillRect(EXT.x0, 1990, EXT.x1 - EXT.x0, 410);
  ctx.restore();
}
function paintPost(ctx, x) {
  const w = 64;
  ctx.fillStyle = lin(ctx, x, 0, x + w, 0, [[0, '#cfc9bc'], [0.35, '#ece8de'], [0.8, '#fbf9f3'], [1, '#e2ddd0']]);
  ctx.fillRect(x, -150, w, 1850);
  ctx.fillStyle = '#f4f1e9'; ctx.fillRect(x - 8, -150, w + 16, 30); ctx.fillRect(x - 8, 1620, w + 16, 80);
  ctx.fillStyle = 'rgba(60,50,40,0.25)'; ctx.fillRect(x - 8, -120, w + 16, 3); ctx.fillRect(x - 8, 1620, w + 16, 3);
  ctx.fillStyle = lin(ctx, 0, -120, 0, 120, [[0, 'rgba(30,25,20,0.3)'], [1, 'rgba(30,25,20,0)']]); ctx.fillRect(x, -120, w, 240);
}

// ---------------------------------------------------------------- init
function init() {
  if (C) return C;
  const R = mulberry32(2024);
  const W = EXT.x1 - EXT.x0, H = EXT.y1 - EXT.y0;
  const c = newCache(EXT.x0, EXT.y0, W, H), x = c.ctx;
  paintBrick(x, R);
  grain(c.cv, S, EXT.x0, EXT.y0, [EXT.x0, -200, W, 1700], 16, 0.22, 21, 0.6);
  // porch-roof shade over the upper wall (soft)
  x.fillStyle = lin(x, 0, -150, 0, 760, [[0, 'rgba(30,22,30,0.55)'], [0.3, 'rgba(30,22,30,0.28)'], [0.7, 'rgba(30,22,30,0.06)'], [1, 'rgba(30,22,30,0)']]);
  x.fillRect(EXT.x0, -150, W, 850);
  // warm morning light raking across from the right
  x.save(); x.globalCompositeOperation = 'screen';
  x.fillStyle = lin(x, EXT.x1, 300, EXT.x0, 1500, [[0, 'rgba(255,225,180,0.22)'], [0.6, 'rgba(255,225,180,0.08)'], [1, 'rgba(255,225,180,0)']]);
  x.fillRect(EXT.x0, -150, W, 1650);
  x.restore();
  paintHall(x, R);
  paintDoorTrim(x);
  paintWindow(x, R);
  paintMailbox(x);
  paintCeiling(x, R);
  paintLantern(x);
  paintFloor(x, R);
  paintSkirt(x, R);
  paintSteps(x, R);
  paintGarden(x, R);
  paintBench(x, R);
  paintDoormat(x, R);
  paintPottedPlant(x, 330, 1532, R, 260);
  paintPottedPlant(x, 862, 1532, R, 230);
  grain(c.cv, S, EXT.x0, EXT.y0, [EXT.x0, 1500, W, 900], 6, 0.05, 23, 0.5);
  // door texture (flat) at 1.25x
  const dt = createCanvas(Math.ceil(DW * S), Math.ceil(DH * S)), dctx = dt.getContext('2d');
  dctx.scale(S, S); paintDoorTex(dctx, mulberry32(7));
  const dth = createCanvas(Math.ceil(DW * S / 2), Math.ceil(DH * S / 2)), dhx = dth.getContext('2d');
  dhx.imageSmoothingQuality = 'high'; dhx.drawImage(dt, 0, 0, dth.width, dth.height);
  // front posts
  const posts = [-380, 1500].map((px) => { const pc = newCache(px - 12, -160, 90, 1880); paintPost(pc.ctx, px); return pc; });
  C = { bg: [c, half(c)], door: dt, doorTex: [dt, dth], texData: new Uint8Array(dctx.getImageData(0, 0, dt.width, dt.height).data.buffer), posts };
  return C;
}

// ---------------------------------------------------------------- door (perspective, swings inward on left hinges)
function doorGeom(open) {
  const th = clamp(open, 0, 1) * (DOOR_MAX_DEG * Math.PI) / 180;
  const pt = (u) => { const X = DOOR.x0 + DW * u * Math.cos(th), Z = DW * u * Math.sin(th); const [x, yt] = proj(X, DOOR.y0, Z), [, yb] = proj(X, DOOR.y1, Z); return { x, yt, yb, Z }; };
  return { th, pt };
}
const WARP = { x0: 424, y0: 664, w: 352, h: 842 };
let warpCache = null;
function warpDoor(open) {
  const key = Math.round(open * 10000);
  if (warpCache && warpCache.key === key) return warpCache;
  const th = clamp(open, 0, 1) * (DOOR_MAX_DEG * Math.PI) / 180, c = Math.cos(th), sn = Math.sin(th);
  const W = Math.ceil(WARP.w * S), H = Math.ceil(WARP.h * S);
  if (!warpCache) { const cv = createCanvas(W, H); warpCache = { cv, ctx: cv.getContext('2d'), img: null }; warpCache.img = warpCache.ctx.createImageData(W, H); warpCache.u32 = new Uint32Array(warpCache.img.data.buffer); }
  const out32 = warpCache.u32; out32.fill(0);
  const T = C.texData, tw = C.door.width, tH = C.door.height;
  const { cx, cy, D } = PV;
  const xf = cx + (DOOR.x0 + DW * c - cx) * (D / (D + DW * sn)), xa = Math.min(DOOR.x0, xf), xb = Math.max(DOOR.x0, xf);
  for (let i = 0; i < W; i++) {
    const xw = WARP.x0 + (i + 0.5) / S;
    const den = DW * ((xw - cx) * sn - c * D);
    if (Math.abs(den) < 1e-9) continue;
    let u = (D * (DOOR.x0 - xw)) / den;
    // horizontal coverage: overlap of this pixel column with the leaf's screen span [xa, xb]
    const p0 = xw - 0.5 / S, p1 = xw + 0.5 / S;
    const cov = Math.min(1, Math.max(0, (Math.min(p1, xb) - Math.max(p0, xa)) * S));
    if (cov <= 0) continue;
    u = u < 0 ? 0 : u > 1 ? 1 : u;
    const sc = D / (D + DW * u * sn);
    const top = cy + (DOOR.y0 - cy) * sc, bot = cy + (DOOR.y1 - cy) * sc, hh = bot - top;
    const j0 = Math.max(0, Math.floor((top - WARP.y0) * S)), j1 = Math.min(H - 1, Math.ceil((bot - WARP.y0) * S));
    const fx = Math.min(tw - 1.001, Math.max(0, u * tw - 0.5)), ix = Math.floor(fx), ax = fx - ix;
    const dv = 1 / (S * hh), v0 = (WARP.y0 + 0.5 / S - top) / hh;
    const tw4 = tw * 4, ix4 = ix * 4, bx = 1 - ax;
    for (let j = j0; j <= j1; j++) {
      let v = v0 + j * dv, a = cov;
      if (v < 0) { a *= 1 + v / dv; v = 0; } else if (v > 1) { a *= 1 - (v - 1) / dv; v = 1; }
      if (a <= 0) continue;
      let fy = v * tH - 0.5; if (fy < 0) fy = 0; else if (fy > tH - 1.001) fy = tH - 1.001;
      const iy = fy | 0, ay = fy - iy, by = 1 - ay;
      const k00 = iy * tw4 + ix4, k10 = k00 + tw4;
      const w00 = bx * by, w01 = ax * by, w10 = bx * ay, w11 = ax * ay;
      const r = (T[k00] * w00 + T[k00 + 4] * w01 + T[k10] * w10 + T[k10 + 4] * w11 + 0.5) | 0;
      const g = (T[k00 + 1] * w00 + T[k00 + 5] * w01 + T[k10 + 1] * w10 + T[k10 + 5] * w11 + 0.5) | 0;
      const bl = (T[k00 + 2] * w00 + T[k00 + 6] * w01 + T[k10 + 2] * w10 + T[k10 + 6] * w11 + 0.5) | 0;
      const al = a >= 1 ? 255 : (a * 255 + 0.5) | 0;
      out32[j * W + i] = (r | (g << 8) | (bl << 16) | (al << 24)) >>> 0;
    }
  }
  warpCache.ctx.putImageData(warpCache.img, 0, 0);
  warpCache.key = key;
  return warpCache;
}
function drawDoor(ctx, open) {
  const { th, pt } = doorGeom(open);
  ctx.save();
  ctx.beginPath(); ctx.rect(DOOR.x0, DOOR.y0, DOOR.x1 - DOOR.x0, DOOR.y1 - DOOR.y0); ctx.clip();
  if (th < 1e-4) {
    ctx.drawImage(C.door, DOOR.x0, DOOR.y0, DW, DH);
  } else {
    // shadow the opening door throws into the hallway floor/jamb (soft)
    const fe = pt(1);
    ctx.fillStyle = rgba('#1e140c', 0.25 * Math.sin(th));
    ctx.beginPath(); ctx.moveTo(DOOR.x0, DOOR.y1); ctx.lineTo(fe.x, fe.yb); ctx.lineTo(fe.x + 30, fe.yb); ctx.lineTo(DOOR.x0 + 20, DOOR.y1); ctx.fill();
    // door leaf drawn as thin vertical strips, each mapped with its own affine transform
    // door leaf: exact perspective warp of the flat door texture (per-pixel, cached per doorOpen value)
    const wd = warpDoor(open);
    ctx.drawImage(wd.cv, WARP.x0, WARP.y0, WARP.w, WARP.h);
    // the face turns away from the daylight: darken, but keep a warm bounce from inside
    const h0 = pt(0), h1 = pt(1);
    const quad = () => { ctx.beginPath(); ctx.moveTo(h0.x, h0.yt); ctx.lineTo(h1.x, h1.yt); ctx.lineTo(h1.x, h1.yb); ctx.lineTo(h0.x, h0.yb); ctx.closePath(); };
    quad();
    ctx.fillStyle = lin(ctx, h0.x, 0, h1.x, 0, [[0, rgba('#0e1612', 0.30 * Math.sin(th))], [1, rgba('#0e1612', 0.12 * Math.sin(th))]]); ctx.fill();
    // thickness edge along the free (latch) edge, lit by the hall
    const T = 18 * Math.sin(th) * (PV.D / (PV.D + h1.Z));
    if (T > 0.3) {
      ctx.fillStyle = lin(ctx, h1.x, 0, h1.x + T, 0, [[0, '#5d7b6a'], [1, '#86a08e']]);
      ctx.beginPath(); ctx.moveTo(h1.x, h1.yt); ctx.lineTo(h1.x + T, h1.yt + T * 0.08); ctx.lineTo(h1.x + T, h1.yb - T * 0.04); ctx.lineTo(h1.x, h1.yb); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(20,30,25,0.5)'; ctx.fillRect(h1.x - 0.5, h1.yt, 1.2, h1.yb - h1.yt);
    }
  }
  // hinge knuckles on the hinge line
  for (const y of [760, 1085, 1410]) {
    ctx.fillStyle = lin(ctx, DOOR.x0 - 4, 0, DOOR.x0 + 5, 0, [[0, '#6c5428'], [0.5, '#d4b26a'], [1, '#6c5428']]);
    rr(ctx, DOOR.x0 - 1, y - 30, 7, 60, 3); ctx.fill();
  }
  ctx.restore();
}
function drawSpill(ctx, open) {
  // warm hallway light spilling out across the threshold, mat and porch floor
  const a = smooth(0.02, 0.6, open);
  if (a < 0.01) return;
  const { pt } = doorGeom(open);
  const gl = Math.max(DOOR.x0, Math.min(DOOR.x1, pt(1).x)), gr = DOOR.x1;
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const layers = 7;
  for (let i = 0; i < layers; i++) {
    const k = i / (layers - 1), grow = 8 + k * 50;
    ctx.fillStyle = lin(ctx, 0, 1500, 0, 1720, [[0, rgba('#ffd49a', 0.15 * a)], [0.6, rgba('#ffd49a', 0.07 * a)], [1, rgba('#ffd49a', 0.01 * a)]]);
    ctx.beginPath();
    ctx.moveTo(gl - grow * 0.2, 1500); ctx.lineTo(gr + grow * 0.2, 1500);
    ctx.lineTo(gr + 150 + grow, 1720); ctx.lineTo(gl - 90 - (gr - gl) * 0.15 - grow, 1720); ctx.closePath(); ctx.fill();
  }
  // glow on the threshold itself and on the trim edges
  softGlow(ctx, (gl + gr) / 2, 1500, (gr - gl) * 0.7 + 30, '#ffdcaa', 0.35 * a, 0.25);
  softGlow(ctx, gr + 15, 1100, 120, '#ffd9a0', 0.12 * a, 4);
  ctx.restore();
}

function drawBack(ctx, t, o = {}) {
  init();
  const open = clamp(o.doorOpen ?? 0, 0, 1);
  blit(ctx, pick(ctx, C.bg));
  drawDoor(ctx, open);
  drawSpill(ctx, open);
}
function drawFront(ctx, t, o = {}) {
  init();
  for (const pc of C.posts) blit(ctx, pc);
}

// ---------------------------------------------------------------- lighting for characters
function lightAt(x, y, t, o = {}) {
  const open = clamp(o.doorOpen ?? 0, 0, 1);
  const inSun = smooth(1700, 1820, y); // out from under the porch roof
  const keyDir = -0.9; // from the upper right
  const keyColor = '#fff0d0';
  const keyAmt = lerp(0.62, 0.85, inSun);
  let rimDir = -2.3, rimColor = '#cfdcec', rimAmt = 0.3; // cool sky fill from the upper left
  // warm rim from the open doorway for characters near it
  const dd = Math.hypot(x - 600, (y - 1500) * 1.5);
  const near = 1 - smooth(250, 900, dd);
  const dw = smooth(0.3, 0.75, open) * near;
  if (dw > 0.01) {
    const toDoor = Math.atan2(1100 - (y - 600), 600 - x);
    rimDir = lerpAng(rimDir, toDoor, dw); rimColor = mix(rimColor, '#ffd59a', dw); rimAmt = lerp(rimAmt, 0.6, dw);
  }
  return {
    keyDir, keyColor, keyAmt, rimDir, rimColor, rimAmt,
    shadowColor: '#4c5878', shadowAmt: lerp(0.3, 0.22, inSun),
    ambient: mix('#e6e8ee', '#eef2f6', inSun), ambientAmt: lerp(0.14, 0.08, inSun),
  };
}

module.exports = { ENV, drawBack, drawFront, lightAt };
