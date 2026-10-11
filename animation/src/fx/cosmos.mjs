// THE COSMOS — the universe inside the Void's face.
//
//   drawCosmos(g, cx, cy, rx, ry, t, opts)
//     cx, cy  : centre (current transform coords)
//     rx, ry  : half-extents of the region to fill (rect by default; see opts.clip)
//     t       : seconds (drift, twinkle, galaxy spin)
//     opts    : {
//       reveal  0..1  (default 1)  0 = pure abyss; stars kindle first (~0.05-0.6),
//                                   nebulae bloom (~0.25-0.75), then galaxies + glyphs (~0.5-1)
//       glyphs  0..1  (default 1)  visibility of the drifting "bits and pieces of meaning"
//       seed    int   (default 7)  star layout / glyph arrangement
//       drift   num   (default 1)  speed multiplier for parallax drift, spin and glyph float
//       clip    'rect' (default) | 'ellipse' | 'none'   ('none' = caller already clipped)
//       bg      bool  (default true) paint the deep-space background (false = transparent overlay)
//       alpha   0..1  (default 1)
//     }
//
// Works at any size: content density / line widths / mip levels adapt to the effective on-screen
// size (it reads g.getTransform()), so it looks right both tiny inside a hood (rx≈40-120 px) and
// as a full-screen close-up (rx≥420). Nebula + galaxy textures are generated once and cached.

import { createCanvas } from '@napi-rs/canvas';
import { clamp, lerp, TAU, smoothstep, rgba, mixColor } from '../engine.mjs';

// Local deterministic hash/noise (integer-safe; independent of engine.mjs).
function hash32(n) {
  n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
  n = Math.imul(n ^ (n >>> 15), 0x846ca68b);
  return (n ^ (n >>> 16)) >>> 0;
}
export const hrand = (i, seed = 0) => hash32((Math.imul(i | 0, 374761393) + Math.imul(seed | 0, 668265263) + 0x27d4eb2f) | 0) / 4294967296;
export function vnoise(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hrand(i, seed) * 2 - 1, b = hrand(i + 1, seed) * 2 - 1;
  const u = f * f * (3 - 2 * f);
  return a + (b - a) * u;
}
export const vfbm = (x, seed = 0) => vnoise(x, seed) * 0.7 + vnoise(x * 2.3, seed + 17) * 0.3;
const rand = hrand, fbm = vfbm;

export const COSMOS_COLORS = {
  abyss: '#040309', deep: '#05040f', mid: '#0d0a2a', core: '#1c1350',
  violet: '#7b4dff', magenta: '#d346b4', teal: '#22b8c4', gold: '#f0b45a', blue: '#3f6bff', rose: '#ff7aa8',
};
const CC = COSMOS_COLORS;

// ---------------------------------------------------------------- stars
const STAR_COLORS = ['#ffffff', '#d6e4ff', '#ffe8c8', '#e1d3ff', '#c6f4ff'];
const LAYERS = [
  // far, mid, near — density per device px², min/max counts, radius range (device px), alpha, drift (normalized units/s)
  { dens: 5.2e-4, min: 26, max: 720, r0: 0.42, r1: 0.95, a: 0.7, vx: 0.0011, vy: 0.0004, kmul: 1.0, band: 0.45 },
  { dens: 1.7e-4, min: 10, max: 240, r0: 0.7, r1: 1.55, a: 0.9, vx: 0.0024, vy: 0.0008, kmul: 0.85, band: 0.25 },
  { dens: 0.55e-4, min: 4, max: 72, r0: 1.1, r1: 2.6, a: 1.0, vx: 0.0042, vy: 0.0014, kmul: 0.55, band: 0 },
];
const starCache = new Map();
function starData(seed) {
  let d = starCache.get(seed);
  if (d) return d;
  d = LAYERS.map((L, li) => {
    const arr = [];
    for (let i = 0; i < L.max; i++) {
      const s = seed * 31 + li * 7;
      const sz = Math.pow(rand(i, s + 3), 2.2); // most stars tiny
      let u = rand(i, s + 1), v = rand(i, s + 2);
      if (rand(i, s + 9) < L.band) {
        // cluster along a soft diagonal "milky" band (gaussian-ish offset from the band line)
        const gauss = (rand(i, s + 10) + rand(i, s + 11) + rand(i, s + 12) - 1.5) * 0.16;
        v = ((0.72 - u * 0.5 + gauss) % 1 + 1) % 1;
      }
      arr.push({
        u, v, sz,
        c: Math.floor(rand(i, s + 4) * 5) % 5,
        thr: rand(i, s + 5) * L.kmul * (1 - sz * 0.5), // bigger stars kindle a little earlier
        tw: rand(i, s + 6) < (li === 0 ? 0.04 : li === 1 ? 0.16 : 0.45), // twinkler
        ph: rand(i, s + 7) * TAU, w: 1.2 + rand(i, s + 8) * 2.2,
      });
    }
    return arr;
  });
  starCache.set(seed, d);
  return d;
}

// ---------------------------------------------------------------- nebula sprites (cached, blurred once)
const NEB_N = 256;
let nebCache = null;
const NEBULAE = [
  // nx, ny (normalized), size (×S), rot, stretch, colours, alpha, reveal offset, spin dir
  { nx: -0.36, ny: 0.12, size: 1.75, rot: 0.6, sx: 1.3, cols: [CC.violet, CC.magenta, '#5a3bd8'], a: 1.0, ro: 0.0, sd: 1 },
  { nx: 0.46, ny: -0.36, size: 1.45, rot: -0.4, sx: 1.15, cols: [CC.teal, CC.blue, '#2f8fd8'], a: 0.95, ro: 0.08, sd: -1 },
  { nx: 0.3, ny: 0.66, size: 1.1, rot: 1.2, sx: 1.1, cols: ['#ffc66b', '#ff8fb0', '#ffd9a0'], a: 1.0, ro: 0.16, sd: 1 },
  { nx: -0.42, ny: -0.66, size: 1.1, rot: 2.2, sx: 1.35, cols: [CC.magenta, CC.violet, CC.rose], a: 0.85, ro: 0.12, sd: -1 },
  { nx: 0.05, ny: 0.0, size: 3.0, rot: -0.85, sx: 1.8, cols: ['#4a4fc8', '#6b5fe0', '#3a7ad0'], a: 0.75, ro: 0.04, sd: 1, band: true },
];
function makeNebula(i, cfg) {
  const N = NEB_N, h = N / 2;
  const c = createCanvas(N, N), x = c.getContext('2d');
  x.globalCompositeOperation = 'lighter';
  const blob = (bx, by, r, col, a) => {
    const gr = x.createRadialGradient(bx, by, 0, bx, by, r);
    gr.addColorStop(0, rgba(col, a));
    gr.addColorStop(0.45, rgba(col, a * 0.5));
    gr.addColorStop(1, rgba(col, 0));
    x.fillStyle = gr;
    x.fillRect(bx - r, by - r, r * 2, r * 2);
  };
  const s = 500 + i * 37;
  const cols = cfg.cols;
  const colAt = (k) => { const f = (k % 1) * cols.length; const j = Math.floor(f); return mixColor(cols[j % cols.length], cols[(j + 1) % cols.length], f - j); };
  // broad body
  for (let k = 0; k < 6; k++) {
    const a = rand(k, s) * TAU, d = rand(k, s + 1) * 0.22;
    blob(h + Math.cos(a) * d * h, h + Math.sin(a) * d * h * 0.8, (0.32 + rand(k, s + 2) * 0.2) * h, cols[k % cols.length], cfg.band ? 0.12 : 0.11);
  }
  if (!cfg.band) {
    // filaments (random walks) — wispy structure
    for (let f = 0; f < 3; f++) {
      let px = (rand(f, s + 9) - 0.5) * 0.5, py = (rand(f, s + 10) - 0.5) * 0.5, ang = rand(f, s + 11) * TAU;
      for (let k = 0; k < 44; k++) {
        const kk = k + f * 100;
        ang += (rand(kk, s + 3) - 0.5) * 0.9;
        px += Math.cos(ang) * 0.035; py += Math.sin(ang) * 0.035;
        const d = Math.hypot(px, py);
        if (d > 0.58) { px *= 0.58 / d; py *= 0.58 / d; ang += Math.PI * 0.6; }
        const col = mixColor(colAt(k / 44 + f * 0.33), '#ffffff', rand(kk, s + 4) * 0.12);
        const edge = 1 - d / 0.7;
        blob(h + px * h, h + py * h, (0.035 + rand(kk, s + 5) * 0.08) * h, col, (0.15 + rand(kk, s + 6) * 0.17) * edge);
      }
    }
    // a few bright knots
    for (let k = 0; k < 4; k++) {
      const a = rand(k, s + 12) * TAU, d = rand(k, s + 13) * 0.3;
      blob(h + Math.cos(a) * d * h, h + Math.sin(a) * d * h, (0.03 + rand(k, s + 14) * 0.03) * h, mixColor(cols[k % cols.length], '#ffffff', 0.35), 0.2);
    }
  }
  // dust lanes (soft dark bites)
  x.globalCompositeOperation = 'destination-out';
  for (let k = 0; k < 9; k++) {
    const a = rand(k, s + 15) * TAU, d = 0.08 + rand(k, s + 16) * 0.4;
    const bx = h + Math.cos(a) * d * h, by = h + Math.sin(a) * d * h, r = (0.05 + rand(k, s + 17) * 0.1) * h;
    const gr = x.createRadialGradient(bx, by, 0, bx, by, r);
    gr.addColorStop(0, 'rgba(0,0,0,0.42)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = gr; x.fillRect(bx - r, by - r, r * 2, r * 2);
  }
  // edge falloff so the sprite never shows a square border
  const gm = x.createRadialGradient(h, h, h * 0.55, h, h, h * 0.98);
  gm.addColorStop(0, 'rgba(0,0,0,0)'); gm.addColorStop(1, 'rgba(0,0,0,1)');
  x.fillStyle = gm; x.fillRect(0, 0, N, N);
  // soften once into the final sprite
  const out = createCanvas(N, N), o = out.getContext('2d');
  o.filter = cfg.band ? 'blur(8px)' : 'blur(2.5px)';
  o.drawImage(c, 0, 0);
  o.filter = 'none';
  return out;
}
function nebulae() {
  if (!nebCache) nebCache = NEBULAE.map((cfg, i) => makeNebula(i, cfg));
  return nebCache;
}

// ---------------------------------------------------------------- galaxy sprites (cached + mip chain)
const GAL_N = 512;
const galCache = new Map();
const GAL_STYLES = {
  warm: { core: '#fff3da', core2: '#ffc979', arm: '#9fb4ff', arm2: '#ffffff', knot: '#ff8fc8', haze: '#6d63ff' },
  cool: { core: '#f2f0ff', core2: '#b9a6ff', arm: '#7fe3ff', arm2: '#e7f8ff', knot: '#ff9be0', haze: '#3aa6d8' },
};
function makeGalaxy(style, seedG) {
  const N = GAL_N, h = N / 2;
  const P = GAL_STYLES[style];
  const arms = createCanvas(N, N), a = arms.getContext('2d');
  a.globalCompositeOperation = 'lighter';
  const nArms = 2;
  const dots = [];
  for (let i = 0; i < 2200; i++) {
    const arm = i % nArms;
    const s = Math.pow(rand(i, seedG + 1), 0.8);
    const th = s * 3.3 * Math.PI + arm * (TAU / nArms) + (rand(i, seedG + 2) - 0.5) * (0.35 + s * 0.25);
    const r = (0.05 + s * 0.88) * h * 0.92;
    const jit = (rand(i, seedG + 3) - 0.5) * (0.03 + s * 0.08) * h;
    const x = h + Math.cos(th) * r + jit, y = h + Math.sin(th) * r + (rand(i, seedG + 4) - 0.5) * (0.03 + s * 0.07) * h;
    dots.push([x, y, s, i]);
  }
  // arm haze: thick soft dots, blurred
  for (const [x, y, s] of dots) {
    a.fillStyle = rgba(s < 0.25 ? P.core2 : P.haze, 0.05 * (1 - s * 0.6));
    a.beginPath(); a.arc(x, y, 10 + s * 8, 0, TAU); a.fill();
  }
  const out = createCanvas(N, N), o = out.getContext('2d');
  // disk glow
  const gd = o.createRadialGradient(h, h, 0, h, h, h);
  gd.addColorStop(0, rgba(P.core, 0.95));
  gd.addColorStop(0.06, rgba(P.core2, 0.7));
  gd.addColorStop(0.18, rgba(P.haze, 0.22));
  gd.addColorStop(0.55, rgba(P.haze, 0.07));
  gd.addColorStop(1, rgba(P.haze, 0));
  o.fillStyle = gd; o.fillRect(0, 0, N, N);
  o.globalCompositeOperation = 'lighter';
  o.filter = 'blur(9px)';
  o.drawImage(arms, 0, 0);
  o.filter = 'none';
  // star dots along the arms
  for (const [x, y, s, i] of dots) {
    const knot = rand(i, seedG + 5) > 0.965;
    const col = knot ? P.knot : s < 0.3 ? P.core2 : rand(i, seedG + 6) > 0.5 ? P.arm : P.arm2;
    const r = knot ? 2.0 + rand(i, seedG + 7) * 1.6 : 0.6 + rand(i, seedG + 7) * 1.1;
    o.fillStyle = rgba(col, (knot ? 0.75 : 0.5) * (1 - s * 0.45));
    o.beginPath(); o.arc(x, y, r, 0, TAU); o.fill();
  }
  // bright core
  const gc = o.createRadialGradient(h, h, 0, h, h, h * 0.16);
  gc.addColorStop(0, rgba('#ffffff', 0.95)); gc.addColorStop(0.4, rgba(P.core, 0.55)); gc.addColorStop(1, rgba(P.core2, 0));
  o.fillStyle = gc; o.fillRect(0, 0, N, N);
  o.globalCompositeOperation = 'source-over';
  // mip chain (prevents shimmering when a large sprite is drawn small and rotated)
  const mips = [out];
  let cur = out, sz = N;
  while (sz > 16) {
    sz >>= 1;
    const m = createCanvas(sz, sz), mg = m.getContext('2d');
    mg.imageSmoothingEnabled = true; mg.imageSmoothingQuality = 'high';
    mg.drawImage(cur, 0, 0, sz, sz);
    mips.push(m); cur = m;
  }
  return mips;
}
function galaxy(style) {
  let m = galCache.get(style);
  if (!m) { m = makeGalaxy(style, style === 'warm' ? 900 : 1300); galCache.set(style, m); }
  return m;
}
function pickMip(mips, devSize) {
  let best = mips[0];
  for (const m of mips) if (m.width >= devSize * 1.1) best = m;
  return best;
}
const GALAXIES = [
  { nx: -0.38, ny: -0.3, size: 0.66, incl: 0.42, tilt: -0.5, spin: 0.05, style: 'warm', ro: 0.0, ph: 0.4 },
  { nx: 0.46, ny: 0.28, size: 0.46, incl: 0.62, tilt: 0.45, spin: -0.04, style: 'cool', ro: 0.07, ph: 2.1 },
  { nx: 0.12, ny: -0.7, size: 0.3, incl: 0.3, tilt: 1.15, spin: 0.06, style: 'cool', ro: 0.13, ph: 4.0 },
];

// ---------------------------------------------------------------- glyphs ("bits and pieces of meaning")
// Each draws line-art in a unit box (≈ -1..1), y down. `fill` glyphs paint a soft fill too.
const GL = {
  sun(g) {
    g.beginPath(); g.arc(0, 0, 0.42, 0, TAU); g.stroke();
    for (let i = 0; i < 8; i++) {
      const a = i * TAU / 8;
      g.beginPath(); g.moveTo(Math.cos(a) * 0.62, Math.sin(a) * 0.62); g.lineTo(Math.cos(a) * 0.92, Math.sin(a) * 0.92); g.stroke();
    }
  },
  house(g) {
    g.beginPath();
    g.moveTo(-0.62, -0.05); g.lineTo(0, -0.72); g.lineTo(0.62, -0.05);
    g.moveTo(-0.48, -0.18); g.lineTo(-0.48, 0.7); g.lineTo(0.48, 0.7); g.lineTo(0.48, -0.18);
    g.moveTo(-0.13, 0.7); g.lineTo(-0.13, 0.28); g.lineTo(0.13, 0.28); g.lineTo(0.13, 0.7);
    g.stroke();
    g.beginPath(); g.rect(0.22, 0.04, 0.16, 0.16); g.stroke();
  },
  heart(g) {
    g.beginPath();
    g.moveTo(0, 0.72);
    g.bezierCurveTo(-0.35, 0.42, -0.85, 0.12, -0.8, -0.28);
    g.bezierCurveTo(-0.74, -0.7, -0.18, -0.78, 0, -0.38);
    g.bezierCurveTo(0.18, -0.78, 0.74, -0.7, 0.8, -0.28);
    g.bezierCurveTo(0.85, 0.12, 0.35, 0.42, 0, 0.72);
    g.closePath(); g.stroke();
  },
  note(g) {
    g.beginPath(); g.ellipse(-0.28, 0.5, 0.26, 0.19, -0.45, 0, TAU); g.stroke();
    g.beginPath(); g.moveTo(-0.04, 0.44); g.lineTo(-0.04, -0.72);
    g.quadraticCurveTo(0.2, -0.42, 0.55, -0.36); g.quadraticCurveTo(0.42, -0.2, 0.46, 0.02); g.stroke();
  },
  pencil(g) {
    g.save(); g.rotate(-0.75);
    g.beginPath();
    g.moveTo(-0.85, -0.15); g.lineTo(0.5, -0.15); g.lineTo(0.88, 0); g.lineTo(0.5, 0.15); g.lineTo(-0.85, 0.15); g.closePath();
    g.moveTo(0.5, -0.15); g.lineTo(0.5, 0.15);
    g.moveTo(-0.62, -0.15); g.lineTo(-0.62, 0.15);
    g.stroke(); g.restore();
  },
  handprint(g) {
    g.beginPath(); g.ellipse(0, 0.32, 0.36, 0.38, 0, 0, TAU); g.stroke();
    const f = [[-0.33, -0.12, -0.4, 0.3], [-0.12, -0.24, -0.12, 0.42], [0.1, -0.24, 0.08, 0.44], [0.3, -0.12, 0.26, 0.36], [0.42, 0.38, 0.95, 0.24]];
    for (const [x, y, a, l] of f) {
      g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.sin(a) * l, y - Math.cos(a) * l); g.stroke();
    }
  },
  fear(g, P) {
    // tiny lavender Fear: bean body, big head, tuft — filled silhouette with two little eyes
    g.save();
    g.fillStyle = rgba('#b9a6ea', 0.95 * P.a);
    g.beginPath(); g.ellipse(0, -0.22, 0.42, 0.38, 0, 0, TAU); g.fill();
    g.beginPath(); g.moveTo(-0.2, 0.08); g.quadraticCurveTo(-0.34, 0.6, -0.12, 0.66); g.lineTo(0.12, 0.66); g.quadraticCurveTo(0.34, 0.6, 0.2, 0.08); g.closePath(); g.fill();
    g.beginPath(); g.moveTo(-0.06, -0.56); g.quadraticCurveTo(-0.06, -0.86, 0.14, -0.86); g.quadraticCurveTo(0.2, -0.74, 0.08, -0.72); g.quadraticCurveTo(0.04, -0.66, 0.06, -0.56); g.closePath(); g.fill();
    g.fillRect(-0.14, 0.62, 0.07, 0.24); g.fillRect(0.07, 0.62, 0.07, 0.24);
    g.fillStyle = rgba('#2a1d4d', 0.9 * P.a);
    g.beginPath(); g.arc(-0.14, -0.24, 0.085, 0, TAU); g.arc(0.14, -0.24, 0.085, 0, TAU); g.fill();
    g.restore();
  },
  notebook(g) {
    g.beginPath(); g.rect(-0.55, -0.72, 1.1, 1.44); g.stroke();
    g.beginPath();
    for (const y of [-0.3, -0.05, 0.2, 0.45]) { g.moveTo(-0.28, y); g.lineTo(0.38, y); }
    g.stroke();
    g.beginPath();
    for (const y of [-0.5, -0.2, 0.1, 0.4]) { g.moveTo(-0.7, y); g.lineTo(-0.42, y); }
    g.stroke();
  },
  key(g) {
    g.beginPath(); g.arc(-0.5, 0, 0.28, 0, TAU); g.stroke();
    g.beginPath(); g.moveTo(-0.22, 0); g.lineTo(0.85, 0); g.moveTo(0.62, 0); g.lineTo(0.62, 0.28); g.moveTo(0.8, 0); g.lineTo(0.8, 0.22); g.stroke();
  },
  leaf(g) {
    g.beginPath(); g.moveTo(-0.7, 0.62); g.bezierCurveTo(-0.7, -0.2, -0.1, -0.7, 0.72, -0.7); g.bezierCurveTo(0.7, 0.1, 0.1, 0.66, -0.7, 0.62); g.closePath(); g.stroke();
    g.beginPath(); g.moveTo(-0.82, 0.76); g.lineTo(0.35, -0.35); g.stroke();
  },
  speech(g) {
    g.beginPath();
    g.roundRect(-0.8, -0.62, 1.6, 1.0, 0.32);
    g.stroke();
    g.beginPath(); g.moveTo(-0.32, 0.38); g.lineTo(-0.5, 0.78); g.lineTo(-0.02, 0.38); g.stroke();
    g.beginPath(); for (const x of [-0.35, 0, 0.35]) { g.moveTo(x + 0.06, -0.12); g.arc(x, -0.12, 0.06, 0, TAU); } g.fill();
  },
};
export const COSMOS_GLYPHS = Object.keys(GL);
// order = priority (the first ones show even when the cosmos is tiny)
const GLYPHS = [
  { name: 'heart', col: '#ff9fc6', nx: -0.06, ny: 0.2, sz: 1.12 },
  { name: 'sun', col: '#ffd57a', nx: 0.55, ny: -0.28, sz: 1.15 },
  { name: 'fear', col: '#cdbdf5', nx: -0.42, ny: 0.34, sz: 1.2 },
  { name: 'note', col: '#9fe8ff', nx: 0.4, ny: 0.62, sz: 0.95 },
  { name: 'house', col: '#ffcf8a', nx: -0.6, ny: -0.6, sz: 1.0 },
  { name: 'handprint', col: '#ffc6a8', nx: 0.6, ny: -0.74, sz: 0.85 },
  { name: 'speech', col: '#e9e3ff', nx: -0.18, ny: -0.5, sz: 0.85 },
  { name: 'key', col: '#ffd36b', nx: 0.68, ny: 0.06, sz: 0.78 },
  { name: 'notebook', col: '#ffe9b8', nx: -0.72, ny: -0.02, sz: 0.9 },
  { name: 'leaf', col: '#9ff0b5', nx: -0.3, ny: 0.76, sz: 0.8 },
  { name: 'pencil', col: '#ffe3a3', nx: 0.14, ny: -0.16, sz: 0.72 },
];

/** draw one glowing glyph by name at (x,y) — size = half-extent in current units. Exported for scenes. */
export function drawCosmosGlyph(g, name, x, y, size, color, opts = {}) {
  const a = opts.alpha ?? 1, rot = opts.rot || 0;
  const k = devScale(g);
  const lw = (opts.lineWidth ?? clamp(1.0 + size * k / 30, 1.1, 2.6)) / k;
  g.save();
  g.globalCompositeOperation = 'lighter';
  // halo
  const hr = size * 1.9;
  const gr = g.createRadialGradient(x, y, 0, x, y, hr);
  gr.addColorStop(0, rgba(color, 0.2 * a)); gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr; g.fillRect(x - hr, y - hr, hr * 2, hr * 2);
  g.translate(x, y); g.rotate(rot); g.scale(size, size);
  g.lineCap = 'round'; g.lineJoin = 'round';
  const P = { a };
  if (name === 'fear') { GL.fear(g, P); g.restore(); return; }
  g.strokeStyle = rgba(color, 0.22 * a); g.fillStyle = rgba(color, 0.22 * a);
  g.lineWidth = (lw * 3.2) / size;
  GL[name](g, P);
  g.strokeStyle = rgba(mixColor(color, '#ffffff', 0.35), 0.95 * a); g.fillStyle = rgba(mixColor(color, '#ffffff', 0.35), 0.95 * a);
  g.lineWidth = lw / size;
  GL[name](g, P);
  g.restore();
}

function devScale(g) {
  const m = g.getTransform();
  return Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) || 1;
}

// ---------------------------------------------------------------- main
export function drawCosmos(g, cx, cy, rx, ry, t = 0, opts = {}) {
  const reveal = clamp(opts.reveal ?? 1);
  const glyphAmt = clamp(opts.glyphs ?? 1);
  const seed = opts.seed ?? 7;
  const dr = opts.drift ?? 1;
  const clipMode = opts.clip || 'rect';
  const k = devScale(g);
  const S = Math.min(rx, ry);
  const R = S * k; // effective on-screen size (device px)
  const T = t * dr;

  g.save();
  if (opts.alpha != null) g.globalAlpha *= clamp(opts.alpha);
  if (clipMode === 'rect') { g.beginPath(); g.rect(cx - rx, cy - ry, rx * 2, ry * 2); g.clip(); }
  else if (clipMode === 'ellipse') { g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, 0, TAU); g.clip(); }

  // --- background: the abyss lifts into deep indigo space
  if (opts.bg !== false) {
    const bk = smoothstep(0.0, 0.85, reveal);
    const big = Math.max(rx, ry);
    const gr = g.createRadialGradient(cx + rx * 0.1, cy - ry * 0.05, 0, cx, cy, big * 1.15);
    gr.addColorStop(0, mixColor(CC.abyss, CC.core, bk));
    gr.addColorStop(0.45, mixColor(CC.abyss, CC.mid, bk));
    gr.addColorStop(1, mixColor(CC.abyss, CC.deep, bk));
    g.fillStyle = gr;
    g.fillRect(cx - rx, cy - ry, rx * 2, ry * 2);
  }

  // --- nebulae (bloom after the first stars)
  const neb = nebulae();
  g.globalCompositeOperation = 'screen';
  NEBULAE.forEach((N, i) => {
    const nk = smoothstep(0.22 + N.ro, 0.72 + N.ro, reveal);
    if (nk <= 0.003) return;
    const x = cx + (N.nx + fbm(T * 0.012 + i * 3.1, seed + i) * 0.05) * rx;
    const y = cy + (N.ny + fbm(T * 0.011 + i * 5.3, seed + 20 + i) * 0.05) * ry;
    const sz = N.size * S * (0.82 + 0.18 * nk) * (1 + 0.025 * Math.sin(T * 0.13 + i));
    g.save();
    g.globalAlpha = (opts.alpha ?? 1) * N.a * nk;
    g.translate(x, y);
    g.rotate(N.rot + N.sd * T * 0.006);
    g.scale(N.sx, 1 / Math.sqrt(N.sx));
    g.drawImage(neb[i], -sz / 2, -sz / 2, sz, sz);
    g.restore();
  });

  // --- galaxies (cached sprites, rotated per frame)
  g.globalCompositeOperation = 'lighter';
  GALAXIES.forEach((G, i) => {
    const gk = smoothstep(0.48 + G.ro, 0.86 + G.ro, reveal);
    if (gk <= 0.003) return;
    const x = cx + (G.nx + fbm(T * 0.01 + i * 7.7, seed + 40 + i) * 0.03) * rx;
    const y = cy + (G.ny + fbm(T * 0.01 + i * 4.4, seed + 50 + i) * 0.03) * ry;
    const sz = G.size * S * (0.85 + 0.15 * gk);
    const img = pickMip(galaxy(G.style), sz * k);
    g.save();
    g.globalAlpha = (opts.alpha ?? 1) * gk * 0.95;
    g.translate(x, y);
    g.rotate(G.tilt);
    g.scale(1, G.incl);
    g.rotate(G.ph + G.spin * T);
    g.drawImage(img, -sz / 2, -sz / 2, sz, sz);
    g.restore();
  });

  // --- stars: three parallax layers, batched by colour; twinklers drawn individually
  const data = starData(seed);
  const area = 4 * rx * ry * k * k;
  const sizeMul = clamp(Math.pow(R / 420, 0.25), 0.72, 1.3);
  const kindle = smoothstep(0.03, 0.62, reveal) * 1.08; // star kindle front (0..~1.08)
  const ox = cx - rx, oy = cy - ry, W2 = rx * 2, H2 = ry * 2;
  const indiv = [];
  g.globalCompositeOperation = 'lighter';
  LAYERS.forEach((L, li) => {
    const n = Math.round(clamp(area * L.dens, L.min, L.max));
    const arr = data[li];
    const offU = T * L.vx, offV = T * L.vy;
    const bins = [[], [], [], [], []];
    for (let i = 0; i < n; i++) {
      const s = arr[i];
      const ka = clamp((kindle - s.thr) / 0.07);
      if (ka <= 0) continue;
      const u = s.u + offU, v = s.v + offV;
      const x = ox + (u - Math.floor(u)) * W2, y = oy + (v - Math.floor(v)) * H2;
      const r = (L.r0 + (L.r1 - L.r0) * s.sz) * sizeMul / k;
      if (ka < 1 || s.tw) indiv.push([x, y, r, s, L, li, ka]);
      else bins[s.c].push(x, y, r);
    }
    for (let c = 0; c < 5; c++) {
      const b = bins[c];
      if (!b.length) continue;
      g.fillStyle = rgba(STAR_COLORS[c], L.a);
      g.beginPath();
      for (let j = 0; j < b.length; j += 3) { g.moveTo(b[j] + b[j + 2], b[j + 1]); g.arc(b[j], b[j + 1], b[j + 2], 0, TAU); }
      g.fill();
    }
  });
  const spikes = R > 140;
  for (const [x, y, r, s, L, li, ka] of indiv) {
    const tw = s.tw ? 0.62 + 0.38 * Math.sin(t * s.w + s.ph) : 1;
    const a = L.a * ka * tw;
    const col = STAR_COLORS[s.c];
    if (li === 2 && s.sz > 0.45) {
      // bright star: halo + (in close-ups) a tiny 4-point glint
      const hr = r * 5.5;
      const gr = g.createRadialGradient(x, y, 0, x, y, hr);
      gr.addColorStop(0, rgba(col, 0.5 * a)); gr.addColorStop(1, rgba(col, 0));
      g.fillStyle = gr; g.fillRect(x - hr, y - hr, hr * 2, hr * 2);
      if (spikes) {
        const sl = r * (3.5 + 2.5 * tw);
        g.strokeStyle = rgba(col, 0.55 * a); g.lineWidth = Math.max(0.6 / k, r * 0.3);
        g.beginPath(); g.moveTo(x - sl, y); g.lineTo(x + sl, y); g.moveTo(x, y - sl); g.lineTo(x, y + sl); g.stroke();
      }
    }
    g.fillStyle = rgba(col, a);
    g.beginPath(); g.arc(x, y, r * (s.tw ? 0.85 + 0.25 * tw : 1), 0, TAU); g.fill();
  }

  // --- glyphs: bits and pieces of meaning, drifting slowly
  const gk0 = smoothstep(0.58, 0.98, reveal) * glyphAmt;
  if (gk0 > 0.003) {
    const small = clamp((260 - R) / 200);
    const nG = Math.round(clamp(4 + R / 38, 5, GLYPHS.length));
    const gsz = S * lerp(0.07, 0.115, small);
    g.globalCompositeOperation = 'source-over';
    for (let i = 0; i < nG; i++) {
      const G = GLYPHS[i];
      const ga = smoothstep(i * 0.04, i * 0.04 + 0.55, gk0);
      if (ga <= 0.003) continue;
      const sd = seed * 13 + i * 17;
      const x = cx + (G.nx + fbm(T * 0.045 + i * 2.3, sd) * 0.07 + Math.sin(T * 0.07 + i) * 0.025) * rx;
      const y = cy + (G.ny + fbm(T * 0.04 + i * 3.7, sd + 1) * 0.06 + Math.cos(T * 0.06 + i * 1.7) * 0.02) * ry;
      const rot = fbm(T * 0.05 + i, sd + 2) * 0.35;
      const pulse = 0.85 + 0.15 * Math.sin(t * (0.6 + rand(i, seed) * 0.5) + i * 1.3);
      const depth = lerp(0.68, 1, clamp((G.sz - 0.7) / 0.5));
      drawCosmosGlyph(g, G.name, x, y, gsz * G.sz, G.col, { alpha: (opts.alpha ?? 1) * ga * pulse * depth, rot });
    }
  }
  g.restore();
}

/** warm-up caches (call once at startup if you want the first frame to be fast) */
export function _cosmosSprites() { return { neb: nebulae(), warm: galaxy('warm'), cool: galaxy('cool') }; }
export function preloadCosmos() { nebulae(); galaxy('warm'); galaxy('cool'); starData(7); }
