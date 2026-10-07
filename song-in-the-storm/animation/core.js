// ===== core utilities =====
const W = 1280, H = 720;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const easeIO = t => (t = clamp(t), t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const fade = (t, a, b, fi = 0.5, fo = 0.5) => ss(a, a + fi, t) * (1 - ss(b - fo, b, t));
function hash(n) { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
function noise1(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; }
function noise2(x, y) {
  const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const h = (a, b) => hash(a * 57.3 + b * 113.1);
  return lerp(lerp(h(i, j), h(i + 1, j), ux), lerp(h(i, j + 1), h(i + 1, j + 1), ux), uy) * 2 - 1;
}
function rng(seed) { let s = seed >>> 0; return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const mixc = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
const rgba = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const shade = (c, k) => [c[0] * k, c[1] * k, c[2] * k];

function blinkAt(t, seed = 0, period = 3.6) {
  const k = Math.floor(t / period);
  for (let j = k - 1; j <= k; j++) {
    const bt = j * period + hash(j * 13.7 + seed) * (period - 0.4);
    const d = t - bt;
    if (d > 0 && d < 0.17) return Math.sin(Math.PI * d / 0.17);
    // occasional double blink
    if (hash(j * 3.1 + seed) > 0.8) { const d2 = d - 0.3; if (d2 > 0 && d2 < 0.15) return Math.sin(Math.PI * d2 / 0.15); }
  }
  return 0;
}
// piecewise keyframes: kf(t, [[t0,v0],[t1,v1],...]) smooth
function kf(t, pts) {
  if (t <= pts[0][0]) return pts[0][1];
  for (let i = 0; i < pts.length - 1; i++) {
    const [a, va] = pts[i], [b, vb] = pts[i + 1];
    if (t <= b) {
      const u = easeIO((t - a) / (b - a));
      if (Array.isArray(va)) return va.map((x, k) => lerp(x, vb[k], u));
      return lerp(va, vb, u);
    }
  }
  return pts[pts.length - 1][1];
}

// offscreen helpers
function mkCanvas(w = W, h = H) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const LAYER = [mkCanvas(), mkCanvas(), mkCanvas()];
function layer(i) { const c = LAYER[i]; const g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none'; g.clearRect(0, 0, W, H); return g; }

function radial(ctx, x, y, r, c, a, a2 = 0) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(c, a)); g.addColorStop(1, rgba(c, a2));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
}
function glow(ctx, x, y, r, c, a) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(c, a)); g.addColorStop(0.25, rgba(c, a * 0.45)); g.addColorStop(1, rgba(c, 0));
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); ctx.restore();
}
function vignette(ctx, amt = 0.6, c = [0, 0, 0]) {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95);
  g.addColorStop(0, rgba(c, 0)); g.addColorStop(1, rgba(c, amt));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function grain(ctx, t, amt = 0.05) {
  const r = rng(Math.floor(t * 24) * 7919);
  ctx.save(); ctx.globalAlpha = amt;
  for (let i = 0; i < 260; i++) {
    const x = r() * W, y = r() * H, v = r() > 0.5 ? 255 : 0;
    ctx.fillStyle = `rgb(${v},${v},${v})`; ctx.fillRect(x, y, 2, 2);
  }
  ctx.restore();
}
function rainStreaks(ctx, t, n = 220, speed = 1400, ang = 0.18, alpha = 0.25, seed = 1, len = 28, col = [190, 205, 230]) {
  const r = rng(seed);
  ctx.save(); ctx.strokeStyle = rgba(col, alpha); ctx.lineWidth = 1.2; ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const x0 = r() * (W + 300) - 150, ph = r(), sp = speed * (0.7 + r() * 0.6), l = len * (0.6 + r() * 0.8);
    const y = ((ph * (H + 200) + t * sp) % (H + 200)) - 100;
    const x = x0 - (y) * ang;
    ctx.moveTo(x, y); ctx.lineTo(x - l * ang, y + l);
  }
  ctx.stroke(); ctx.restore();
}
function lightningBolt(ctx, x0, y0, x1, y1, seed, a = 1, width = 3, col = [220, 210, 255]) {
  const r = rng(seed);
  let pts = [[x0, y0], [x1, y1]];
  for (let it = 0; it < 6; it++) {
    const np = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
      const d = Math.hypot(bx - ax, by - ay);
      np.push(pts[i], [(ax + bx) / 2 + (r() - .5) * d * 0.45, (ay + by) / 2 + (r() - .5) * d * 0.15]);
    }
    np.push(pts[pts.length - 1]); pts = np;
  }
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (const [lw, al] of [[width * 6, 0.12], [width * 2.5, 0.3], [width, 1]]) {
    ctx.strokeStyle = rgba(col, al * a); ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.beginPath();
    pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
  }
  // branches
  ctx.strokeStyle = rgba(col, 0.6 * a); ctx.lineWidth = width * 0.5;
  for (let b = 0; b < 3; b++) {
    const i = Math.floor(r() * pts.length * 0.7); let [x, y] = pts[i]; ctx.beginPath(); ctx.moveTo(x, y);
    const dir = r() > .5 ? 1 : -1;
    for (let k = 0; k < 8; k++) { x += dir * (10 + r() * 25); y += 10 + r() * 30; ctx.lineTo(x, y); }
    ctx.stroke();
  }
  ctx.restore();
}

// clouds: soft blobs, cached sprite
const CLOUD = (() => {
  const c = mkCanvas(256, 256), g = c.getContext('2d');
  const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 256, 256); return c;
})();
const tintCache = {};
function tinted(col) {
  const k = col.map(v => v | 0).join(',');
  if (tintCache[k]) return tintCache[k];
  const c = mkCanvas(256, 256), g = c.getContext('2d');
  g.drawImage(CLOUD, 0, 0); g.globalCompositeOperation = 'source-in'; g.fillStyle = rgba(col, 1); g.fillRect(0, 0, 256, 256);
  if (Object.keys(tintCache).length > 400) for (const kk in tintCache) delete tintCache[kk];
  return (tintCache[k] = c);
}
function stormClouds(ctx, t, opt = {}) {
  const { seed = 3, n = 70, y0 = -100, y1 = H * 0.75, col = [40, 30, 55], col2 = [90, 60, 90], speed = 1, alpha = 0.8, swirl = 0, cx = W / 2, cy = H / 2, flash = 0 } = opt;
  const r = rng(seed);
  for (let i = 0; i < n; i++) {
    const bx = r() * (W + 600) - 300, by = lerp(y0, y1, r()), sz = 160 + r() * 260, sp = (10 + r() * 30) * speed, ph = r() * 100;
    let x = ((bx + t * sp) % (W + 600)) - 300 + noise1(t * 0.2 + ph) * 40;
    let y = by + noise1(t * 0.15 + ph * 2) * 30;
    if (swirl) {
      const a = Math.atan2(y - cy, x - cx) + swirl * t * 0.08 * (1 + 400 / (Math.hypot(x - cx, y - cy) + 200));
      const d = Math.hypot(x - cx, y - cy);
      x = cx + Math.cos(a) * d; y = cy + Math.sin(a) * d;
    }
    const k = r();
    const c = mixc(mixc(col, col2, k * 0.8), [230, 220, 255], flash * (0.4 + 0.6 * k));
    ctx.globalAlpha = alpha * (0.35 + 0.5 * r());
    ctx.drawImage(tinted(c.map(v => Math.round(v / 6) * 6)), x - sz, y - sz * 0.6, sz * 2, sz * 1.2);
  }
  ctx.globalAlpha = 1;
}
