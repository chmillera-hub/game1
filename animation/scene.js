'use strict';
// The Spark in the Storm — procedural renderer.
// renderFrame(t) draws the frame at time t (seconds) of the loaded part.

const W = 1280, H = 720;
const cv = document.getElementById('c');
const g = cv.getContext('2d');
const oc = document.createElement('canvas'); oc.width = W; oc.height = H;
const og = oc.getContext('2d');
let TL = null;

// ------------------------------------------------------------------ math
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const sstep = (t, a, b) => { const u = clamp((t - a) / (b - a)); return u * u * (3 - 2 * u); };
const ease = u => u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
const TAU = Math.PI * 2;
function hrand(n) { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
function noise1(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hrand(i), hrand(i + 1), u) * 2 - 1; }
// piecewise keyframes [[t, v], ...] with eased interpolation (holds outside)
function kf(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t < keys[i][0]) {
      const [t0, v0] = keys[i - 1], [t1, v1] = keys[i];
      return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0));
    }
  }
  return keys[keys.length - 1][1];
}
// pulse that rises over `a`, holds, falls over `b`
const pulse = (t, t0, t1, a = .5, b = .5) => sstep(t, t0, t0 + a) * (1 - sstep(t, t1 - b, t1));

const _rgb = {};
function rgb(hex) {
  if (!_rgb[hex]) {
    if (hex[0] === '#') { const n = parseInt(hex.slice(1), 16); _rgb[hex] = [n >> 16 & 255, n >> 8 & 255, n & 255]; }
    else _rgb[hex] = hex.match(/[\d.]+/g).slice(0, 3).map(Number);
  }
  return _rgb[hex];
}
function mix(a, b, u, alpha = 1) {
  const A = rgb(a), B = rgb(b);
  return `rgba(${Math.round(lerp(A[0], B[0], u))},${Math.round(lerp(A[1], B[1], u))},${Math.round(lerp(A[2], B[2], u))},${alpha})`;
}
function rgba(hex, a) { const c = rgb(hex); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; }

// ------------------------------------------------------------------ timing helpers
function makeBlinks(seed) {
  const arr = []; let t = 0.6 + hrand(seed) * 2, k = 0;
  while (t < 240) { arr.push(t); k++; t += 1.8 + hrand(seed * 13 + k) * 3.4; }
  return arr;
}
const BLINKS = { listener: makeBlinks(3), singer: makeBlinks(7), jesus: makeBlinks(11), passer: makeBlinks(5), huddled: makeBlinks(9) };
function blink(t, who) {
  let v = 0;
  for (const b of BLINKS[who]) {
    const d = t - b;
    if (d < 0) break;
    if (d < 0.07) v = d / 0.07; else if (d < 0.2) v = 1 - (d - 0.07) / 0.13;
  }
  return v;
}
function env(name, t) { if (!TL || !TL.env[name]) return 0; return TL.env[name][Math.floor(t * TL.fps)] || 0; }
// tiny eye jitter so eyes never look frozen
function micro(t, seed) { return [noise1(t * 1.3 + seed) * 0.08, noise1(t * 1.1 + seed + 50) * 0.06]; }
function drops(t, events, dur = 1.8) {
  const out = [];
  for (const [te, side] of events) { const p = (t - te) / dur; if (p > 0 && p < 1.15) out.push({ side, p }); }
  return out;
}

// ------------------------------------------------------------------ camera
let CAM = { x: W / 2, y: H / 2, z: 1, r: 0 };
function setCam(x, y, z, r = 0) { CAM = { x, y, z, r }; }
function applyCam(c) {
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.translate(W / 2, H / 2); c.rotate(CAM.r); c.scale(CAM.z, CAM.z); c.translate(-CAM.x, -CAM.y);
}
function toScreen(x, y) {
  const dx = (x - CAM.x) * CAM.z, dy = (y - CAM.y) * CAM.z, cr = Math.cos(CAM.r), sr = Math.sin(CAM.r);
  return [W / 2 + dx * cr - dy * sr, H / 2 + dx * sr + dy * cr];
}

// draw something to the offscreen layer, light it, then put it on the frame
function lit(drawFn, lights = [], shade = null) {
  og.setTransform(1, 0, 0, 1, 0, 0);
  og.globalCompositeOperation = 'source-over';
  og.globalAlpha = 1;
  og.clearRect(0, 0, W, H);
  applyCam(og);
  drawFn(og);
  og.setTransform(1, 0, 0, 1, 0, 0);
  og.globalCompositeOperation = 'source-atop';
  if (shade) { og.fillStyle = shade; og.fillRect(0, 0, W, H); }
  for (const L of lights) {
    const [sx, sy] = L.world ? toScreen(L.x, L.y) : [L.x, L.y];
    const r = L.world ? L.r * CAM.z : L.r;
    const gr = og.createRadialGradient(sx, sy, 0, sx, sy, r);
    gr.addColorStop(0, L.c); gr.addColorStop(1, L.c1 || 'rgba(0,0,0,0)');
    og.fillStyle = gr; og.fillRect(0, 0, W, H);
  }
  og.globalCompositeOperation = 'source-over';
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(oc, 0, 0);
}

// ------------------------------------------------------------------ palettes
const PAL = {
  listener: { skin: '#d8a283', skinS: '#b07658', hair: '#231a17', hairH: '#3e2f28', top: '#3a4762', topS: '#262f45',
    iris: '#5b3a26', lip: '#9c5a50', pants: '#1e2330', shoe: '#14161c' },
  jesus: { hair: '#4b3122', hairH: '#70503a', top: '#eee7d8', topS: '#cbbfa9', iris: '#6f4a2a',
    mantle: '#9b2a23', mantleS: '#6c1a16' },
  singer: { skin: '#ecc7b0', skinS: '#c99880', hair: '#5a2a24', hairH: '#80433a', top: '#6b6773', topS: '#4c4955',
    iris: '#3d6a5a', lip: '#b06b66', pants: '#2d2a33', shoe: '#1c1a20', blanket: '#4b6676', blanketS: '#334a56' },
  passer: { skin: '#c48e6c', skinS: '#9e6c50', hair: '#1a1514', hairH: '#2e2420', top: '#5b4b3e', topS: '#3e332a',
    iris: '#3b2a1e', lip: '#8e5446', pants: '#25262c', shoe: '#121214' },
  huddled: { skin: '#b98a6e', skinS: '#91664e', hair: '#5d5650', hairH: '#7a726a', top: '#4d5248', topS: '#353930',
    iris: '#4a3a2a', lip: '#8a5a50', pants: '#2a2a26', shoe: '#151513', blanket: '#5a4c40', blanketS: '#3e342c' },
};
function palette(P) {
  const base = PAL[P.kind];
  const j = P.jesus || 0;
  if (!j) return base;
  const J = PAL.jesus;
  return Object.assign({}, base, {
    hair: mix(base.hair, J.hair, j), hairH: mix(base.hairH, J.hairH, j), iris: mix(base.iris, J.iris, j),
  });
}

// ------------------------------------------------------------------ characters
// All character drawing happens in "head units": head radius = 1, head centre = (0,0).

function facePath(c, tx) {
  c.beginPath();
  c.moveTo(-0.8 + tx * 0.1, -0.15);
  c.bezierCurveTo(-0.84 + tx * 0.1, -1.08, 0.84 + tx * 0.1, -1.08, 0.8 + tx * 0.1, -0.15);
  c.bezierCurveTo(0.8 + tx * 0.05, 0.38, 0.5 + tx * 0.6, 0.8, 0.04 + tx * 1.1, 0.97);
  c.bezierCurveTo(-0.42 + tx * 0.9, 0.82, -0.8 + tx * 0.1, 0.38, -0.8 + tx * 0.1, -0.15);
  c.closePath();
}

function drawEye(c, side, s, pal, tx) {
  const turn = s.turn || 0;
  const far = Math.max(0, side * turn);
  const f = 1 - 0.45 * far;
  const ex = side * 0.34 + tx * 1.05 - side * far * 0.05, ey = 0.1;
  const b = clamp(Math.max(s.blink || 0, s.droop || 0) + (s.squint || 0) * 0.35);
  c.save();
  c.translate(ex, ey); c.scale(side * f * (s.eyeScale || 1), s.eyeScale || 1);
  const shape = () => {
    c.beginPath(); c.moveTo(-0.16, 0.03);
    c.bezierCurveTo(-0.08, -0.15, 0.1, -0.15, 0.17, -0.03);
    c.bezierCurveTo(0.1, 0.1, -0.06, 0.115, -0.16, 0.03); c.closePath();
  };
  const lidY1 = lerp(-0.15, 0.1, b), lidY2 = lerp(-0.15, 0.115, b);
  if (b < 0.98) {
    c.save(); shape(); c.clip();
    c.fillStyle = s.red > 0.5 ? mix('#f2ece6', '#ffb0a0', s.red - 0.5) : '#f2ece6';
    c.fillRect(-0.2, -0.2, 0.4, 0.4);
    // iris (gaze is in face space, so un-mirror the x)
    const gx = (s.gx || 0) * 0.065 * side, gy = (s.gy || 0) * 0.04;
    const ir = 0.078, red = s.red || 0;
    const ic = red > 0 ? mix(pal.iris, '#ff2a14', red) : pal.iris;
    c.fillStyle = ic; c.beginPath(); c.arc(gx, gy, ir, 0, TAU); c.fill();
    const gr2 = c.createLinearGradient(0, gy - ir, 0, gy + ir);
    gr2.addColorStop(0, 'rgba(0,0,0,0.55)'); gr2.addColorStop(0.6, 'rgba(0,0,0,0)'); gr2.addColorStop(1, 'rgba(255,255,255,0.15)');
    c.fillStyle = gr2; c.beginPath(); c.arc(gx, gy, ir, 0, TAU); c.fill();
    // pupil (slit when demonic)
    c.fillStyle = '#0b0606';
    const pr = 0.032 * (s.dilate || 1);
    if (red > 0.6) { c.beginPath(); c.ellipse(gx, gy, pr * 0.35, pr * 1.8, 0, 0, TAU); c.fill(); }
    else { c.beginPath(); c.arc(gx, gy, pr, 0, TAU); c.fill(); }
    // highlights (light from upper left in screen space)
    c.fillStyle = 'rgba(255,255,255,0.92)';
    c.beginPath(); c.arc(gx - 0.03 * side, gy - 0.032, 0.022, 0, TAU); c.fill();
    c.fillStyle = 'rgba(255,255,255,0.6)';
    c.beginPath(); c.arc(gx + 0.028 * side, gy + 0.03, 0.01, 0, TAU); c.fill();
    if (s.gold) { // warm glints of the divine
      c.fillStyle = `rgba(255,214,130,${0.6 * s.gold})`;
      c.beginPath(); c.arc(gx + 0.02 * side, gy - 0.01, 0.014, 0, TAU); c.fill();
      c.strokeStyle = `rgba(255,220,150,${0.5 * s.gold})`; c.lineWidth = 0.008;
      c.beginPath(); c.arc(gx, gy, ir * 0.8, 0, TAU); c.stroke();
    }
    // tears welling along the lower lid
    const tr = s.tears || 0;
    if (tr > 0) {
      const wy = lerp(0.09, 0.05, tr);
      const gw = c.createLinearGradient(0, wy - 0.04, 0, 0.12);
      gw.addColorStop(0, 'rgba(200,230,255,0)'); gw.addColorStop(1, `rgba(200,230,255,${0.45 * tr})`);
      c.fillStyle = gw; c.fillRect(-0.2, wy - 0.04, 0.4, 0.2);
      c.strokeStyle = `rgba(240,250,255,${0.85 * tr})`; c.lineWidth = 0.012;
      c.beginPath(); c.moveTo(-0.13, 0.045); c.quadraticCurveTo(0, wy + 0.02, 0.14, 0.0); c.stroke();
      // glisten sparkles that shimmer on the wet eye
      const sp = 0.5 + 0.5 * Math.sin((s.time || 0) * 3 + side);
      c.fillStyle = `rgba(255,255,255,${0.7 * tr * sp})`;
      c.beginPath(); c.arc(gx + 0.035 * side, gy + 0.045, 0.012, 0, TAU); c.fill();
    }
    // shadow of the upper lid
    const gl = c.createLinearGradient(0, -0.15, 0, 0.02);
    gl.addColorStop(0, 'rgba(60,30,20,0.45)'); gl.addColorStop(1, 'rgba(60,30,20,0)');
    c.fillStyle = gl; c.fillRect(-0.2, -0.2, 0.4, 0.25);
    // the lid itself, closing
    c.fillStyle = pal.skin;
    c.beginPath(); c.moveTo(-0.2, -0.3); c.lineTo(0.2, -0.3); c.lineTo(0.2, -0.03);
    c.lineTo(0.17, -0.03); c.bezierCurveTo(0.1, lidY1, -0.08, lidY2, -0.16, 0.03); c.lineTo(-0.2, 0.03); c.closePath(); c.fill();
    c.restore();
  }
  // lash line along the lid edge
  c.strokeStyle = '#1a100d'; c.lineCap = 'round';
  c.lineWidth = 0.028;
  c.beginPath(); c.moveTo(-0.16, 0.03); c.bezierCurveTo(-0.08, lidY2, 0.1, lidY1, 0.17, -0.03);
  c.lineTo(0.205, -0.065); c.stroke();
  c.lineWidth = 0.01; c.globalAlpha = 0.5;
  c.beginPath(); c.moveTo(-0.12, 0.075); c.bezierCurveTo(-0.04, 0.115, 0.08, 0.1, 0.15, 0.0); c.stroke();
  c.globalAlpha = 1;
  if (b < 0.6) { // crease above the eye
    c.strokeStyle = 'rgba(90,45,35,0.35)'; c.lineWidth = 0.012;
    c.beginPath(); c.moveTo(-0.12, -0.12); c.bezierCurveTo(-0.05, -0.2, 0.08, -0.2, 0.16, -0.1); c.stroke();
  }
  c.restore();
  if (s.red > 0.3 && b < 0.95) { // demonic glow
    c.save(); c.globalCompositeOperation = 'lighter';
    const gr = c.createRadialGradient(ex, ey, 0, ex, ey, 0.35);
    gr.addColorStop(0, `rgba(255,60,20,${0.55 * (s.red - 0.3)})`); gr.addColorStop(1, 'rgba(255,0,0,0)');
    c.fillStyle = gr; c.beginPath(); c.arc(ex, ey, 0.35, 0, TAU); c.fill(); c.restore();
  }
}

function drawBrows(c, s, pal, tx) {
  const turn = s.turn || 0;
  const sad = s.sad || 0, ang = s.angry || 0, up = s.browUp || 0;
  c.fillStyle = pal.hair;
  for (const side of [-1, 1]) {
    const far = Math.max(0, side * turn), f = 1 - 0.45 * far;
    const cx = tx * 1.05 - side * far * 0.05;
    const ix = cx + side * 0.13 * f, ox = cx + side * 0.53 * f;
    const iy = -0.2 - sad * 0.1 + ang * 0.08 - up * 0.07, oy = -0.21 + sad * 0.035 - ang * 0.035 - up * 0.05;
    const my = Math.min(iy, oy) - 0.05 + ang * 0.02;
    c.beginPath();
    c.moveTo(ix, iy + 0.025);
    c.quadraticCurveTo((ix + ox) / 2, my + 0.025, ox, oy + 0.005);
    c.quadraticCurveTo((ix + ox) / 2, my - 0.025, ix, iy - 0.03);
    c.closePath(); c.fill();
  }
}

function drawMouth(c, s, pal, tx) {
  const o = clamp(s.mouth || 0), sm = s.smile || 0, rd = s.round || 0;
  const mx = tx * 1.08, my = 0.6 + (s.tremble || 0) * 0.008 * Math.sin((s.time || 0) * 31);
  const w = 0.21 * (1 - 0.42 * rd * o) * (1 + 0.12 * sm);
  const h = 0.01 + o * 0.16 * (1 + 0.25 * rd);
  const cy = my - sm * 0.035;
  c.lineCap = 'round';
  if (s.grit > 0.05) {
    const gw = 0.24, gh = 0.035 + 0.05 * s.grit;
    c.fillStyle = '#2a1012';
    c.beginPath(); c.moveTo(mx - gw / 2, my + 0.02); c.quadraticCurveTo(mx, my - gh, mx + gw / 2, my + 0.02);
    c.quadraticCurveTo(mx, my + gh * 1.1, mx - gw / 2, my + 0.02); c.fill();
    c.save(); c.clip();
    c.fillStyle = '#e8ded6'; c.fillRect(mx - gw / 2, my - gh * 0.55, gw, gh * 1.1);
    c.strokeStyle = 'rgba(80,60,60,0.6)'; c.lineWidth = 0.008;
    c.beginPath(); c.moveTo(mx - gw / 2, my + 0.005); c.lineTo(mx + gw / 2, my + 0.005);
    for (let k = -3; k <= 3; k++) { c.moveTo(mx + k * 0.032, my - gh); c.lineTo(mx + k * 0.032, my + gh); }
    c.stroke(); c.restore();
    c.strokeStyle = pal.lip; c.lineWidth = 0.016;
    c.beginPath(); c.moveTo(mx - gw / 2, my + 0.02); c.quadraticCurveTo(mx, my - gh, mx + gw / 2, my + 0.02); c.stroke();
    return;
  }
  if (h < 0.028) {
    c.strokeStyle = pal.lip; c.lineWidth = 0.022;
    c.beginPath(); c.moveTo(mx - w / 2, cy); c.quadraticCurveTo(mx, my + 0.012 + sm * 0.035, mx + w / 2, cy); c.stroke();
  } else {
    c.fillStyle = '#3a181a';
    c.beginPath(); c.moveTo(mx - w / 2, cy);
    c.quadraticCurveTo(mx, my - h * 0.45, mx + w / 2, cy);
    c.quadraticCurveTo(mx, my + h * 1.15, mx - w / 2, cy); c.closePath(); c.fill();
    c.save(); c.clip();
    if (o > 0.3) { c.fillStyle = '#efe6e0'; c.fillRect(mx - w / 2, my - h * 0.5, w, h * 0.28); }
    c.fillStyle = '#a5505a'; c.beginPath(); c.ellipse(mx, my + h * 0.75, w * 0.32, h * 0.35, 0, 0, TAU); c.fill();
    c.restore();
    c.strokeStyle = pal.lip; c.lineWidth = 0.016;
    c.beginPath(); c.moveTo(mx - w / 2, cy); c.quadraticCurveTo(mx, my - h * 0.45, mx + w / 2, cy); c.stroke();
  }
  // lower lip shading
  c.strokeStyle = rgba('#000000', 0.12); c.lineWidth = 0.02;
  c.beginPath(); c.moveTo(mx - w * 0.25, my + h * 0.6 + 0.05); c.quadraticCurveTo(mx, my + h * 0.6 + 0.07, mx + w * 0.25, my + h * 0.6 + 0.05); c.stroke();
}

function drawTearDrops(c, s, tx) {
  for (const d of s.drops || []) {
    const side = d.side, far = Math.max(0, side * (s.turn || 0)), f = 1 - 0.45 * far;
    const ex = side * 0.34 + tx * 1.05 - side * far * 0.05;
    const x0 = ex + side * 0.03 * f, y0 = 0.2;
    const p = clamp(d.p), pe = p * p * 0.6 + p * 0.4;
    const x = x0 + side * 0.07 * f * pe, y = y0 + 0.75 * pe;
    const a = d.p > 1 ? clamp(1 - (d.p - 1) / 0.15) : 1;
    c.strokeStyle = `rgba(220,240,255,${0.35 * a})`; c.lineWidth = 0.014; c.lineCap = 'round';
    c.beginPath(); c.moveTo(x0, y0); c.quadraticCurveTo(x0 + side * 0.02, (y0 + y) / 2, x, y); c.stroke();
    if (d.p < 1) {
      const r = 0.034;
      const gr = c.createRadialGradient(x - r * 0.3, y - r * 0.2, 0, x, y, r * 1.3);
      gr.addColorStop(0, 'rgba(255,255,255,0.95)'); gr.addColorStop(0.5, 'rgba(190,225,255,0.7)'); gr.addColorStop(1, 'rgba(150,200,240,0.2)');
      c.fillStyle = gr;
      c.beginPath(); c.moveTo(x, y - r * 2.1); c.quadraticCurveTo(x + r * 1.1, y - r * 0.2, x, y + r); c.quadraticCurveTo(x - r * 1.1, y - r * 0.2, x, y - r * 2.1); c.fill();
    }
  }
}

function hairShortBack(c, tx, pal) {
  c.fillStyle = pal.hair;
  c.beginPath(); c.moveTo(-0.9 + tx * 0.1, 0.15);
  c.bezierCurveTo(-1.05 + tx * 0.1, -1.3, 1.05 + tx * 0.1, -1.3, 0.9 + tx * 0.1, 0.15);
  c.lineTo(0.75 + tx * 0.1, 0.2); c.lineTo(-0.75 + tx * 0.1, 0.2); c.closePath(); c.fill();
}
function hairShortFront(c, tx, pal, wind, t) {
  const sx = tx * 0.55;
  c.fillStyle = pal.hair;
  c.beginPath();
  c.moveTo(-0.9 + tx * 0.1, 0.05);
  c.bezierCurveTo(-1.0 + tx * 0.1, -1.25, 1.0 + tx * 0.1, -1.25, 0.9 + tx * 0.1, 0.05);
  const n = 7;
  for (let i = n; i >= 0; i--) {
    const u = i / n, x = lerp(-0.86, 0.86, u) + sx;
    const tip = (i % 2 === 0);
    const w = wind ? wind * 0.09 * noise1(t * 2 + i * 1.7) : 0;
    const y = tip ? -0.3 - 0.08 * Math.sin(u * Math.PI * 1.3) : -0.58;
    c.lineTo(x + (tip ? w + 0.03 : 0), y + (tip ? 0.04 * Math.abs(u - 0.5) * 2 : 0));
  }
  c.closePath(); c.fill();
}
function hairLongBack(c, tx, pal, len, wind, t) {
  c.fillStyle = pal.hair;
  const L = len;
  const w = wind ? wind * 0.12 : 0;
  c.beginPath(); c.moveTo(-0.92 + tx * 0.1, 0);
  c.bezierCurveTo(-1.08 + tx * 0.1, -1.32, 1.08 + tx * 0.1, -1.32, 0.92 + tx * 0.1, 0);
  c.bezierCurveTo(1.0, L * 0.5, 1.15 + w * noise1(t * 1.3), L * 0.85, 1.05 + w * noise1(t * 1.1 + 3), L);
  for (let i = 0; i <= 6; i++) {
    const u = i / 6;
    c.lineTo(lerp(1.05, -1.05, u) + w * noise1(t * 1.5 + i), L + (i % 2 ? 0.12 : 0) + 0.05 * Math.sin(u * 9));
  }
  c.bezierCurveTo(-1.15 + w * noise1(t * 1.2 + 5), L * 0.85, -1.0, L * 0.5, -0.92 + tx * 0.1, 0);
  c.closePath(); c.fill();
}
function hairLongFront(c, tx, pal, len, t) {
  const px = tx * 0.7;
  c.fillStyle = pal.hair;
  // crown
  c.beginPath(); c.moveTo(-0.9 + tx * 0.1, -0.05);
  c.bezierCurveTo(-1.02 + tx * 0.1, -1.28, 1.02 + tx * 0.1, -1.28, 0.9 + tx * 0.1, -0.05);
  c.bezierCurveTo(0.7 + px * 0.3, -0.7, 0.2 + px, -0.9, px, -0.88);
  c.bezierCurveTo(-0.2 + px, -0.9, -0.7 + px * 0.3, -0.7, -0.9 + tx * 0.1, -0.05);
  c.closePath(); c.fill();
  // side curtains framing the face
  for (const side of [-1, 1]) {
    c.beginPath();
    c.moveTo(px, -0.88);
    c.bezierCurveTo(px + side * 0.55, -0.85, side * 0.82 + tx * 0.1, -0.4, side * 0.8 + tx * 0.1, 0.2);
    c.bezierCurveTo(side * 0.82 + tx * 0.1, len * 0.6, side * 0.95, len * 0.85, side * 0.88, len * 0.95);
    c.lineTo(side * 1.0, len * 0.9);
    c.bezierCurveTo(side * 1.05, len * 0.5, side * 0.98 + tx * 0.1, -0.2, side * 0.92 + tx * 0.1, -0.5);
    c.bezierCurveTo(side * 0.8, -0.95, px + side * 0.3, -1.05, px, -0.88);
    c.fill();
  }
}
function drawBeard(c, tx, pal, a) {
  if (a <= 0) return;
  c.save(); c.globalAlpha = a * 0.92; c.fillStyle = pal.hair;
  const mx = tx * 1.08;
  c.beginPath();
  c.moveTo(-0.76 + tx * 0.1, 0.2);
  c.bezierCurveTo(-0.74 + tx * 0.1, 0.55, -0.42 + tx * 0.9, 0.98, 0.04 + tx * 1.1, 1.06);
  c.bezierCurveTo(0.5 + tx * 0.6, 0.98, 0.76 + tx * 0.05, 0.55, 0.76 + tx * 0.1, 0.2);
  c.bezierCurveTo(0.66 + tx * 0.1, 0.5, 0.42 + tx * 0.6, 0.66, mx + 0.16, 0.72);
  c.quadraticCurveTo(mx, 0.79, mx - 0.16, 0.72);
  c.bezierCurveTo(-0.42 + tx * 0.6, 0.66, -0.66 + tx * 0.1, 0.5, -0.76 + tx * 0.1, 0.2);
  c.fill();
  // moustache
  c.beginPath(); c.moveTo(mx - 0.17, 0.6);
  c.quadraticCurveTo(mx, 0.5, mx + 0.17, 0.6);
  c.quadraticCurveTo(mx, 0.55, mx - 0.17, 0.6); c.fill();
  c.restore();
}
function drawHood(c, tx, pal, a) {
  if (a <= 0) return;
  c.save(); c.globalAlpha = a; c.fillStyle = pal.top;
  c.beginPath();
  c.moveTo(-1.15, 1.3); c.bezierCurveTo(-1.35, -1.5, 1.35, -1.5, 1.15, 1.3);
  c.lineTo(0.75, 1.1);
  c.bezierCurveTo(0.95 + tx * 0.1, -0.2, 0.75, -1.12, tx * 0.2, -1.12);
  c.bezierCurveTo(-0.75, -1.12, -0.95 + tx * 0.1, -0.2, -0.75, 1.1);
  c.closePath(); c.fill();
  c.strokeStyle = pal.topS; c.lineWidth = 0.06;
  c.beginPath(); c.moveTo(-0.75, 1.1); c.bezierCurveTo(-0.95 + tx * 0.1, -0.2, -0.75, -1.12, tx * 0.2, -1.12);
  c.bezierCurveTo(0.75, -1.12, 0.95 + tx * 0.1, -0.2, 0.75, 1.1); c.stroke();
  c.restore();
}
function hornPath(c, side, grow, crumble) {
  // centreline sampled along a cubic, tapered polygon
  const p0 = [side * 0.42, -0.72], p1 = [side * 1.0, -1.0], p2 = [side * 1.25, -1.85], p3 = [side * 0.8, -2.25];
  const pts = [];
  const N = 18, upto = grow * (1 - crumble);
  for (let i = 0; i <= N; i++) {
    const u = (i / N) * upto, v = 1 - u;
    pts.push([v * v * v * p0[0] + 3 * v * v * u * p1[0] + 3 * v * u * u * p2[0] + u * u * u * p3[0],
      v * v * v * p0[1] + 3 * v * v * u * p1[1] + 3 * v * u * u * p2[1] + u * u * u * p3[1], u]);
  }
  const L = [], R = [];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const d = Math.hypot(dx, dy) || 1; dx /= d; dy /= d;
    const w = 0.2 * (1 - pts[i][2]) + 0.012;
    L.push([pts[i][0] - dy * w, pts[i][1] + dx * w]); R.push([pts[i][0] + dy * w, pts[i][1] - dx * w]);
  }
  c.beginPath(); c.moveTo(L[0][0], L[0][1]);
  for (const p of L) c.lineTo(p[0], p[1]);
  for (let i = R.length - 1; i >= 0; i--) c.lineTo(R[i][0], R[i][1]);
  c.closePath();
  return pts;
}
function drawHorns(c, s) {
  const grow = s.horns || 0;
  if (grow <= 0.01) return;
  for (const side of [-1, 1]) {
    c.save();
    hornPath(c, side, grow, s.crumble || 0);
    const gr = c.createLinearGradient(side * 0.4, -0.7, side * 0.9, -2.2);
    gr.addColorStop(0, '#120707'); gr.addColorStop(1, '#3d0f0c');
    c.fillStyle = gr; c.fill();
    c.shadowColor = `rgba(255,40,10,${0.8 * grow})`; c.shadowBlur = 25;
    c.strokeStyle = `rgba(255,70,30,${0.55 * grow})`; c.lineWidth = 0.025; c.stroke();
    c.shadowBlur = 0;
    // ridges
    c.clip();
    c.strokeStyle = 'rgba(0,0,0,0.5)'; c.lineWidth = 0.02;
    for (let k = 1; k < 9; k++) { c.beginPath(); c.arc(side * 0.42, -0.72, k * 0.2, 0, TAU); c.stroke(); }
    // golden cracks of light
    if (s.crack > 0) {
      c.strokeStyle = `rgba(255,220,140,${s.crack})`; c.lineWidth = 0.03;
      c.shadowColor = 'rgba(255,210,120,1)'; c.shadowBlur = 20;
      c.beginPath();
      let x = side * 0.45, y = -0.75;
      for (let k = 0; k < 9; k++) { x += side * (0.06 + 0.04 * hrand(k + side * 7)); y -= 0.17; c.lineTo(x + (hrand(k * 3 + side) - 0.5) * 0.15, y); }
      c.stroke();
    }
    c.restore();
  }
}
function drawHalo(c, s, tx) {
  const a = s.halo || 0;
  if (a <= 0) return;
  c.save();
  const cx = tx * 0.25, cy = -0.35;
  const gr = c.createRadialGradient(cx, cy, 0.4, cx, cy, 2.0);
  gr.addColorStop(0, `rgba(255,236,180,${0.55 * a})`); gr.addColorStop(0.55, `rgba(255,214,140,${0.22 * a})`); gr.addColorStop(1, 'rgba(255,200,120,0)');
  c.fillStyle = gr; c.beginPath(); c.arc(cx, cy, 2.0, 0, TAU); c.fill();
  c.strokeStyle = `rgba(255,240,200,${0.85 * a})`; c.lineWidth = 0.05;
  c.shadowColor = 'rgba(255,220,150,1)'; c.shadowBlur = 30;
  c.beginPath(); c.arc(cx, cy, 1.28, 0, TAU); c.stroke();
  c.lineWidth = 0.015; c.beginPath(); c.arc(cx, cy, 1.4, 0, TAU); c.stroke();
  c.restore();
}

function drawHead(c, s, pal) {
  const tx = (s.turn || 0) * 0.3;
  const j = s.jesus || 0;
  const longHair = s.kind === 'singer' || s.kind === 'huddled';
  if (s.back) { // seen from behind: just hair
    c.fillStyle = pal.skinS;
    c.fillRect(-0.25, 0.5, 0.5, 0.8);
    if (longHair || j > 0.5) hairLongBack(c, 0, pal, longHair ? 1.7 : 1.35, s.wind, s.time || 0);
    c.fillStyle = pal.hair;
    c.beginPath(); c.ellipse(0, -0.12, 0.9, 1.0, 0, 0, TAU); c.fill();
    drawHood(c, 0, pal, s.hood || 0);
    return;
  }
  c.fillStyle = pal.skinS;
  c.beginPath(); c.moveTo(-0.25 + tx * 0.2, 0.55); c.lineTo(0.25 + tx * 0.2, 0.55); c.lineTo(0.28 + tx * 0.1, 1.35); c.lineTo(-0.28 + tx * 0.1, 1.35); c.fill();
  // ears
  c.fillStyle = pal.skin;
  for (const side of [-1, 1]) {
    if (side * (s.turn || 0) > 0.55) continue;
    c.beginPath(); c.ellipse(side * 0.8 + tx * 0.1, 0.12, 0.13, 0.2, side * 0.2, 0, TAU); c.fill();
  }
  facePath(c, tx); c.fillStyle = pal.skin; c.fill();
  // soft shading on the far side and under the brow
  c.save(); facePath(c, tx); c.clip();
  const sd = (s.turn || 0) >= 0 ? -1 : 1;
  const gs = c.createLinearGradient(sd * 0.9, 0, -sd * 0.2, 0);
  gs.addColorStop(0, rgba('#5a2e20', 0.35)); gs.addColorStop(1, rgba('#5a2e20', 0));
  c.fillStyle = gs; c.fillRect(-1, -1.2, 2, 2.4);
  // cheeks flush when crying
  const blush = 0.12 + 0.25 * (s.tears || 0);
  for (const side of [-1, 1]) {
    const bx = side * 0.45 + tx * 1.0, by = 0.38;
    const gb = c.createRadialGradient(bx, by, 0, bx, by, 0.22);
    gb.addColorStop(0, `rgba(230,110,110,${blush})`); gb.addColorStop(1, 'rgba(230,110,110,0)');
    c.fillStyle = gb; c.fillRect(bx - 0.3, by - 0.3, 0.6, 0.6);
  }
  if (s.underlight) { // red light from below (the demon)
    const gu = c.createLinearGradient(0, 1, 0, -0.6);
    gu.addColorStop(0, `rgba(255,40,20,${0.45 * s.underlight})`); gu.addColorStop(1, 'rgba(255,40,20,0)');
    c.fillStyle = gu; c.fillRect(-1, -1.2, 2, 2.4);
  }
  c.restore();
  drawEye(c, -1, s, pal, tx);
  drawEye(c, 1, s, pal, tx);
  drawBrows(c, s, pal, tx);
  // nose
  c.strokeStyle = pal.skinS; c.lineWidth = 0.025; c.lineCap = 'round';
  c.beginPath(); c.moveTo(tx * 1.2 + 0.015, 0.22); c.quadraticCurveTo(tx * 1.25 + 0.07, 0.37, tx * 1.15 - 0.02, 0.4); c.stroke();
  drawMouth(c, s, pal, tx);
  drawBeard(c, tx, pal, s.kind === 'listener' ? sstep(j, 0.3, 1) : 0);
  drawTearDrops(c, s, tx);
  // hair
  if (s.kind === 'listener') {
    if (j < 1) { c.save(); c.globalAlpha = 1 - sstep(j, 0.35, 0.75); hairShortFront(c, tx, pal, s.wind, s.time || 0); c.restore(); }
    if (j > 0) { c.save(); c.globalAlpha = sstep(j, 0.35, 0.75); hairLongFront(c, tx, pal, 1.35, s.time || 0); c.restore(); }
  } else if (longHair) {
    hairLongFront(c, tx, pal, 1.7, s.time || 0);
  } else {
    hairShortFront(c, tx, pal, s.wind, s.time || 0);
  }
  drawHood(c, tx, pal, s.hood || 0);
  drawHorns(c, s);
}

function drawBackHair(c, s, pal) {
  if (s.back) return;
  const tx = (s.turn || 0) * 0.3;
  const j = s.jesus || 0;
  if (s.kind === 'singer' || s.kind === 'huddled') { hairLongBack(c, tx, pal, 1.75, s.wind, s.time || 0); return; }
  if (s.kind === 'listener' && j > 0) {
    c.save(); c.globalAlpha = sstep(j, 0.35, 0.75); hairLongBack(c, tx, pal, 1.4, s.wind, s.time || 0); c.restore();
  }
  if (j < 1) { c.save(); c.globalAlpha = 1 - sstep(j, 0.35, 0.75); hairShortBack(c, tx, pal); c.restore(); }
}

// clothing --------------------------------------------------------------
function torsoPath(c, sw, hw, hy) {
  c.beginPath();
  c.moveTo(-0.32, 1.1);
  c.bezierCurveTo(-0.9, 1.15, -sw, 1.3, -sw, 1.9);
  c.lineTo(-hw, hy); c.lineTo(hw, hy); c.lineTo(sw, 1.9);
  c.bezierCurveTo(sw, 1.3, 0.9, 1.15, 0.32, 1.1);
  c.closePath();
}
function drawBody(c, s, pal) {
  const pose = s.pose || 'bust';
  const j = s.kind === 'listener' ? (s.jesus || 0) : 0;
  const J = PAL.jesus;
  const t = s.time || 0;
  const walk = s.walk || 0; // phase in radians, 0 = standing
  const stride = s.walking ? Math.sin(walk) : 0;
  const robe = j > 0.5 && pose !== 'bust';

  // legs
  if (pose === 'stand' && !robe) {
    c.strokeStyle = pal.pants; c.lineWidth = 0.6; c.lineCap = 'round';
    for (const side of [-1, 1]) {
      const st = side * stride * 0.75;
      c.beginPath(); c.moveTo(side * 0.45, 3.9);
      c.quadraticCurveTo(side * 0.5 + st * 0.6, 5.9 - Math.max(0, st * side) * 0.2, side * 0.45 + st, 7.7);
      c.stroke();
      c.fillStyle = pal.shoe; c.beginPath(); c.ellipse(side * 0.45 + st + side * 0.08, 7.95, 0.38, 0.2, 0, 0, TAU); c.fill();
    }
  }
  if (pose === 'sit') {
    // crate
    if (s.crate !== false) {
      c.fillStyle = '#4a3624'; c.fillRect(-1.5, 3.6, 3.0, 3.1);
      c.strokeStyle = '#2c2015'; c.lineWidth = 0.08;
      for (let k = 0; k < 4; k++) { c.beginPath(); c.moveTo(-1.5, 3.6 + k * 0.78); c.lineTo(1.5, 3.6 + k * 0.78); c.stroke(); }
      c.strokeRect(-1.5, 3.6, 3.0, 3.1);
    }
    c.strokeStyle = pal.pants; c.lineWidth = 0.6; c.lineCap = 'round';
    for (const side of [-1, 1]) {
      if (s.crate === false) { // on the ground, knees drawn up
        c.beginPath(); c.moveTo(side * 0.5, 3.8); c.lineTo(side * 1.05, 3.05); c.lineTo(side * 0.95, 4.55); c.stroke();
        c.fillStyle = pal.shoe; c.beginPath(); c.ellipse(side * 1.0, 4.7, 0.35, 0.18, 0, 0, TAU); c.fill();
      } else {
        c.beginPath(); c.moveTo(side * 0.5, 3.7); c.lineTo(side * 0.6, 4.3); c.lineTo(side * 0.65, 6.4); c.stroke();
        c.fillStyle = pal.shoe; c.beginPath(); c.ellipse(side * 0.7, 6.6, 0.35, 0.18, 0, 0, TAU); c.fill();
      }
    }
  }

  // torso
  const hy = pose === 'bust' ? 5 : pose === 'sit' ? 3.9 : 4.1;
  const bob = s.walking ? Math.abs(Math.cos(walk)) * 0.06 : 0;
  c.save(); c.translate(0, -bob);
  if (robe) {
    const kneel = s.kneel || 0;
    const hem = lerp(7.9, 5.6, kneel), hw = lerp(1.45, 2.1, kneel);
    // feet peeking out while walking
    if (s.walking && kneel < 0.1) {
      c.fillStyle = '#6b4a33';
      for (const side of [-1, 1]) { c.beginPath(); c.ellipse(side * 0.45 + side * stride * 0.5, hem + 0.05, 0.32, 0.14, 0, 0, TAU); c.fill(); }
    }
    c.fillStyle = J.top;
    c.beginPath(); c.moveTo(-0.32, 1.1); c.bezierCurveTo(-0.9, 1.15, -1.35, 1.3, -1.35, 1.9);
    c.quadraticCurveTo(-1.45, 4.5, -hw + stride * 0.1, hem);
    c.quadraticCurveTo(0, hem + 0.15, hw + stride * 0.1, hem);
    c.quadraticCurveTo(1.45, 4.5, 1.35, 1.9); c.bezierCurveTo(1.35, 1.3, 0.9, 1.15, 0.32, 1.1); c.closePath(); c.fill();
    c.strokeStyle = J.topS; c.lineWidth = 0.05;
    for (const k of [-0.6, 0.1, 0.7]) { c.beginPath(); c.moveTo(k * 0.8, 2.5); c.quadraticCurveTo(k + stride * 0.1, 5, k * 1.2 + stride * 0.15, hem - 0.1); c.stroke(); }
  } else if (pose === 'sit' && s.kind === 'singer') {
    c.fillStyle = pal.top; torsoPath(c, 1.25, 1.1, hy); c.fill();
  } else {
    c.fillStyle = pal.top; torsoPath(c, 1.35, 1.05, hy); c.fill();
    // shading
    c.save(); torsoPath(c, 1.35, 1.05, hy); c.clip();
    const gs = c.createLinearGradient(-1.4, 0, 1.4, 0);
    gs.addColorStop(0, rgba('#000000', 0.25)); gs.addColorStop(0.5, rgba('#000000', 0)); gs.addColorStop(1, rgba('#000000', 0.2));
    c.fillStyle = gs; c.fillRect(-2, 1, 4, 5);
    c.restore();
    if (s.kind === 'listener' || s.kind === 'passer') {
      // hood bunched behind the neck + drawstrings
      if (!s.hood && s.kind === 'listener') {
        c.fillStyle = pal.topS;
        c.beginPath(); c.ellipse(0, 1.15, 0.75, 0.28, 0, Math.PI, TAU); c.fill();
      }
      c.strokeStyle = '#c9c4bb'; c.lineWidth = 0.035;
      if (s.kind === 'listener') for (const side of [-1, 1]) { c.beginPath(); c.moveTo(side * 0.2, 1.25); c.lineTo(side * 0.24, 2.2); c.stroke(); }
    }
    // the white robe and red mantle appearing over the hoodie (bust)
    if (j > 0) {
      c.save(); c.globalAlpha = sstep(j, 0.3, 0.8);
      c.fillStyle = J.top; torsoPath(c, 1.35, 1.05, hy); c.fill();
      c.strokeStyle = J.topS; c.lineWidth = 0.04;
      c.beginPath(); c.moveTo(-0.3, 1.12); c.lineTo(0, 1.8); c.lineTo(0.3, 1.12); c.stroke();
      c.restore();
    }
  }
  // mantle
  if (j > 0) {
    c.save(); c.globalAlpha = sstep(j, 0.45, 0.9);
    c.fillStyle = J.mantle;
    const hem = robe ? lerp(6.8, 5.2, s.kneel || 0) : hy;
    c.beginPath(); c.moveTo(-1.3, 1.6); c.bezierCurveTo(-0.9, 1.1, -0.4, 1.2, -0.1, 1.5);
    c.quadraticCurveTo(0.6, 3.0, 1.3, Math.min(hem, 4.2)); c.lineTo(0.7, Math.min(hem, 4.6));
    c.quadraticCurveTo(-0.6, 3.6, -1.38, 2.6); c.closePath(); c.fill();
    c.strokeStyle = J.mantleS; c.lineWidth = 0.05;
    c.beginPath(); c.moveTo(-1.0, 1.7); c.quadraticCurveTo(0.2, 2.8, 1.0, 4.0); c.stroke();
    c.restore();
  }
  // singer's blanket around the shoulders
  if (s.kind === 'singer' || s.kind === 'huddled') {
    const by = pose === 'sit' ? (s.crate === false ? 3.9 : 4.9) : hy;
    c.fillStyle = pal.blanket;
    c.beginPath(); c.moveTo(-0.5, 1.05);
    c.bezierCurveTo(-1.3, 1.0, -1.6, 1.6, -1.65, 2.4);
    c.quadraticCurveTo(-1.8, 4.0, -1.5, by); c.quadraticCurveTo(0, by + 0.3, 1.5, by);
    c.quadraticCurveTo(1.8, 4.0, 1.65, 2.4); c.bezierCurveTo(1.6, 1.6, 1.3, 1.0, 0.5, 1.05);
    c.quadraticCurveTo(0.25, 2.0, 0.15, by - 0.3); c.lineTo(-0.1, by - 0.3); c.quadraticCurveTo(-0.25, 2.0, -0.5, 1.05);
    c.closePath(); c.fill();
    c.strokeStyle = pal.blanketS; c.lineWidth = 0.06;
    for (const k of [-1.1, -0.6, 0.7, 1.15]) { c.beginPath(); c.moveTo(k * 0.9, 1.7); c.quadraticCurveTo(k * 1.1, 3.2, k, by - 0.1); c.stroke(); }
    // hands holding it closed
    if (pose !== 'bust') {
    c.fillStyle = pal.skin;
    c.beginPath(); c.ellipse(-0.12, 2.35, 0.2, 0.16, 0.3, 0, TAU); c.fill();
    c.beginPath(); c.ellipse(0.16, 2.55, 0.2, 0.16, -0.3, 0, TAU); c.fill();
    }
  }
  // arms for standing figures
  if (pose === 'stand' || pose === 'kneel' || s.umbrella) {
    const sleeve = robe ? J.top : pal.top;
    c.strokeStyle = sleeve; c.lineWidth = robe ? 0.62 : 0.5; c.lineCap = 'round';
    for (const side of [-1, 1]) {
      const sw = -side * stride * 0.5;
      let hx = side * 1.55 + sw * 1.4, hyy = 4.2;
      if (s.reach && side === 1) { hx = lerp(hx, 2.9, s.reach); hyy = lerp(hyy, 2.6, s.reach); }
      if (s.umbrella && side === 1) { hx = 0.9; hyy = 2.6; }
      const ex = side * 1.6 + sw * 0.6, ey = 2.9;
      c.beginPath(); c.moveTo(side * 1.25, 1.55); c.quadraticCurveTo(ex, ey, hx, hyy); c.stroke();
      c.fillStyle = pal.skin; c.beginPath(); c.arc(hx, hyy + 0.1, 0.2, 0, TAU); c.fill();
      if (s.umbrella && side === 1) {
        c.strokeStyle = '#222'; c.lineWidth = 0.08;
        c.beginPath(); c.moveTo(hx, hyy + 0.3); c.lineTo(hx, -2.6); c.stroke();
        c.fillStyle = s.umbrellaColor || '#1d2633';
        c.beginPath(); c.moveTo(hx - 2.6, -1.9); c.quadraticCurveTo(hx, -4.0, hx + 2.6, -1.9);
        for (let k = 0; k < 4; k++) c.quadraticCurveTo(hx + 2.6 - (k + 0.5) * 1.3, -2.2, hx + 2.6 - (k + 1) * 1.3, -1.9);
        c.fill();
        c.strokeStyle = sleeve; c.lineWidth = 0.5;
      }
    }
  }
  c.restore();
}

function person(c, P) {
  c.save();
  c.translate(P.x, P.y); c.scale(P.R, P.R);
  if (P.flip) c.scale(-1, 1);
  const pal = palette(P);
  const tilt = P.tilt || 0;
  const head = () => { c.translate(0, 1.0); c.rotate(tilt); c.translate(0, -1.0); };
  c.save(); head(); drawHalo(c, P, (P.turn || 0) * 0.3); drawBackHair(c, P, pal); c.restore();
  drawBody(c, P, pal);
  c.save(); head(); drawHead(c, P, pal); c.restore();
  c.restore();
}

// soft chest glow (drawn on the main canvas, additive)
function chestGlow(x, y, r, a, t) {
  if (a <= 0) return;
  applyCam(g);
  g.save(); g.globalCompositeOperation = 'lighter';
  const fl = 1 + 0.06 * Math.sin(t * 5) + 0.04 * Math.sin(t * 13);
  const gr = g.createRadialGradient(x, y, 0, x, y, r * fl);
  gr.addColorStop(0, `rgba(255,250,230,${a})`); gr.addColorStop(0.15, `rgba(255,225,160,${0.6 * a})`);
  gr.addColorStop(0.5, `rgba(255,190,110,${0.18 * a})`); gr.addColorStop(1, 'rgba(255,170,90,0)');
  g.fillStyle = gr; g.beginPath(); g.arc(x, y, r * fl, 0, TAU); g.fill();
  g.restore();
}
