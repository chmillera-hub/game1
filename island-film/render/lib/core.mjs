// Shared rendering core. Every module builds on these helpers so the film has one look.
// Coordinate space: 720 x 1280 portrait canvas, y down. All draw code must be deterministic in time t.
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';

export const W = 720, H = 1280, FPS = 24;

GlobalFonts.registerFromPath('/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf', 'TitleSerif');
GlobalFonts.registerFromPath('/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf', 'TitleSerifItalic');
GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 'UISans');
GlobalFonts.registerFromPath('/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf', 'HUDMono');
GlobalFonts.registerFromPath('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'Carved');

// ---------------------------------------------------------------- math
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => clamp((x - a) / (b - a));
export const remap = (x, a, b, c, d) => lerp(c, d, invLerp(a, b, x));
export const smoothstep = (a, b, x) => { const t = invLerp(a, b, x); return t * t * (3 - 2 * t); };
export const TAU = Math.PI * 2;
export const ease = {
  linear: t => t,
  in: t => t * t,
  out: t => 1 - (1 - t) * (1 - t),
  inOut: t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
  inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inCubic: t => t * t * t,
  outBack: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  outElastic: t => t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (TAU / 3)) + 1,
};
// eased 0..1 progress of t across [a,b]
export const seg = (t, a, b, e = ease.inOut) => e(clamp((t - a) / (b - a)));
// attack/hold/release envelope: 0 before a, ramps to 1 by a+fin, stays, back to 0 over [b-fout, b]
export const env = (t, a, b, fin = 0.3, fout = 0.3) =>
  Math.min(seg(t, a, a + fin, ease.inOutSine), 1 - seg(t, b - fout, b, ease.inOutSine));

// ---------------------------------------------------------------- deterministic randomness / noise
export function rng(seed) { // mulberry32
  let a = (seed * 2654435761) >>> 0;
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
export const hash = (n) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
// smooth 1D value noise in [-1,1]
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(hash(i + seed * 101.3), hash(i + 1 + seed * 101.3), u) * 2 - 1;
}
export function noise2(x, y, seed = 0) {
  const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const h = (a, b) => hash(a * 57.0 + b * 113.0 + seed * 7.31);
  return lerp(lerp(h(ix, iy), h(ix + 1, iy), ux), lerp(h(ix, iy + 1), h(ix + 1, iy + 1), ux), uy) * 2 - 1;
}
export const fbm1 = (x, seed = 0, oct = 3) => { let s = 0, a = 0.5, f = 1;
  for (let i = 0; i < oct; i++) { s += a * noise1(x * f, seed + i); a *= 0.5; f *= 2; } return s; };

// ---------------------------------------------------------------- color
export function hexToRgb(h) {
  if (h.startsWith('rgb')) { const m = h.match(/[\d.]+/g).map(Number); return m.slice(0, 3); }
  h = h.replace('#', ''); if (h.length === 3) h = h.split('').map(c => c + c).join('');
  const n = parseInt(h.slice(0, 6), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
export const rgbStr = ([r, g, b], a = 1) =>
  a >= 1 ? `rgb(${r | 0},${g | 0},${b | 0})` : `rgba(${r | 0},${g | 0},${b | 0},${a.toFixed(3)})`;
export const mix = (c1, c2, t, a = 1) => {
  const A = hexToRgb(c1), B = hexToRgb(c2); return rgbStr([lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t)], a);
};
export const rgba = (c, a) => rgbStr(hexToRgb(c), a);
export const shade = (c, amt) => amt >= 0 ? mix(c, '#ffffff', amt) : mix(c, '#000000', -amt);
// multiply a color by a light color (for scene lighting of character fills)
export const lit = (c, light, k = 1) => { const A = hexToRgb(c), L = hexToRgb(light);
  return rgbStr(A.map((v, i) => lerp(v, v * L[i] / 255, k))); };

// ---------------------------------------------------------------- shared palette
// Filmic 90s-cel palette: warm highlights, teal/violet shadows, slightly desaturated mids.
export const PAL = {
  ink: '#2b1d1c',            // outline color for characters & props (dark warm brown, never pure black)
  inkSoft: '#4a3530',
  hud: '#7fe7ff',            // Directive / HUD cyan
  hudDeep: '#1aa7c9',
  beam: '#ffd98a',           // lighthouse light
  beamHot: '#fff4d6',
  cellGlow: '#ffc861',       // power cell glow (gold) with cyan core
  // Keeper (android)
  kSkin: '#f1dccb', kSkinShadow: '#c9a69a', kHair: '#d9dde3', kHairShadow: '#9aa3b2', kHairHi: '#ffffff',
  kIris: '#f2a93b', kIrisRing: '#ffe08a', kSuit: '#2f4f5f', kSuitShadow: '#1d3340', kSuitFaded: '#6b8490',
  kStripe: '#d9822b', kPanel: '#1d2a44', kPanelGrid: '#4a6fa5', kSeam: '#a98577',
  // Mira (girl, 9)
  mSkin: '#a86b4a', mSkinShadow: '#7c4a33', mHair: '#2b1a14', mHairHi: '#5a3a2c', mIris: '#5a3420',
  mCoat: '#f2c14e', mCoatShadow: '#c8902c', mShirt: '#c84b3c',
  // Grandpa
  gSkin: '#c58c62', gSkinShadow: '#946144', gBeard: '#ecebe6', gBeardShadow: '#b8b6ae', gCap: '#2c3e66',
  gCapShadow: '#1c2846', gCoat: '#5b6b3a', gCoatShadow: '#3d4a26', gIris: '#4b5d6b',
  // Captain the crab
  crab: '#e0662f', crabShadow: '#a8431c', shell: '#e8d3a8', shellShadow: '#b89c6c', shellStripe: '#8a5a3b',
  // environment anchors
  sand: '#e9cf9f', sandWet: '#b99a6e', sandShadow: '#c9a77a', sea: '#2c7a8c', seaDeep: '#173f5f', foam: '#f4f1e8',
  palm: '#3f7d4a', palmShadow: '#245236', jungle: '#2f5d3a', rock: '#7d7468', rockShadow: '#4e463f', stone: '#a49c8e',
  nightSky: '#0b1430', nightSea: '#08162a',
};

// Time-of-day key lights. Use LIGHT[key].key to tint lit areas, .shadow for cel shadows, .rim for rim light.
export const LIGHT = {
  dawn:   { key: '#ffd2a8', shadow: '#7a5a8c', rim: '#ffb27a', amb: 0.35 },
  day:    { key: '#fff6e6', shadow: '#5f7f9a', rim: '#ffffff', amb: 0.25 },
  noon:   { key: '#ffffff', shadow: '#5a7896', rim: '#fffbe8', amb: 0.2 },
  dusk:   { key: '#ffb37a', shadow: '#5b4a7a', rim: '#ff8a5c', amb: 0.4 },
  night:  { key: '#8fa6d6', shadow: '#1a2448', rim: '#9fc4ff', amb: 0.6 },
  storm:  { key: '#8a9aa8', shadow: '#26323e', rim: '#cfe6ff', amb: 0.6 },
  beam:   { key: '#ffd98a', shadow: '#2a2440', rim: '#ffe7b0', amb: 0.5 },
  rain:   { key: '#9db0c4', shadow: '#2b3a4c', rim: '#d0e4ff', amb: 0.55 },
  shade:  { key: '#d9e8d2', shadow: '#3f5a4a', rim: '#f6ffd8', amb: 0.35 },
  interior:{ key: '#ffd9a6', shadow: '#5a4030', rim: '#ffe2b8', amb: 0.45 },
};

// ---------------------------------------------------------------- paths & cel shading
// Catmull-Rom spline through points [[x,y],...] -> bezier path (closed or open). Does NOT beginPath.
export function splinePath(g, pts, closed = true, tension = 0.5) {
  const n = pts.length; if (n < 2) return;
  const P = i => closed ? pts[(i + n) % n] : pts[clamp(i, 0, n - 1)];
  g.moveTo(pts[0][0], pts[0][1]);
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    const k = tension / 3 * 2;
    g.bezierCurveTo(p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2,
      p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2, p2[0], p2[1]);
  }
  if (closed) g.closePath();
}
export function polyPath(g, pts, closed = true) {
  g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
  if (closed) g.closePath();
}
// Fill a shape with a flat base color, a hard-edged cel shadow (shadowFn draws the shadow region, clipped to the
// shape), optional highlight, then an ink outline. shapeFn(g) must add a path (no beginPath needed).
export function cel(g, shapeFn, { fill, shadow = null, shadowFn = null, hi = null, hiFn = null,
  line = PAL.ink, lw = 2.2, alpha = 1 } = {}) {
  g.save(); g.globalAlpha *= alpha;
  g.beginPath(); shapeFn(g); g.fillStyle = fill; g.fill();
  if ((shadow && shadowFn) || (hi && hiFn)) {
    g.save(); g.beginPath(); shapeFn(g); g.clip();
    if (shadow && shadowFn) { g.beginPath(); shadowFn(g); g.fillStyle = shadow; g.fill(); }
    if (hi && hiFn) { g.beginPath(); hiFn(g); g.fillStyle = hi; g.fill(); }
    g.restore();
  }
  if (line && lw > 0) { g.beginPath(); shapeFn(g); g.lineJoin = 'round'; g.lineCap = 'round';
    g.strokeStyle = line; g.lineWidth = lw; g.stroke(); }
  g.restore();
}
export function ellipse(g, x, y, rx, ry, rot = 0) { g.ellipse(x, y, Math.abs(rx), Math.abs(ry), rot, 0, TAU); }
// variable-width ink stroke along points (tapered ends) - for hair strands, eyelashes, folds
export function taperStroke(g, pts, w0, w1, color = PAL.ink, wMid = null) {
  if (pts.length < 2) return;
  const n = pts.length, left = [], right = [];
  for (let i = 0; i < n; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
    const u = i / (n - 1);
    const w = wMid == null ? lerp(w0, w1, u) : (u < 0.5 ? lerp(w0, wMid, u * 2) : lerp(wMid, w1, (u - 0.5) * 2));
    left.push([pts[i][0] - dy * w / 2, pts[i][1] + dx * w / 2]); right.push([pts[i][0] + dy * w / 2, pts[i][1] - dx * w / 2]);
  }
  g.beginPath(); splinePath(g, left.concat(right.reverse()), true); g.fillStyle = color; g.fill();
}

// ---------------------------------------------------------------- light & atmosphere
export function glow(g, x, y, r, color, a = 1, mode = 'lighter') {
  g.save(); g.globalCompositeOperation = mode;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, rgba(color, a)); gr.addColorStop(0.4, rgba(color, a * 0.35)); gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); g.restore();
}
export function vignette(g, amt = 0.45, color = '#000000') {
  const gr = g.createRadialGradient(W / 2, H * 0.48, H * 0.25, W / 2, H * 0.5, H * 0.75);
  gr.addColorStop(0, rgba(color, 0)); gr.addColorStop(1, rgba(color, amt));
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
}
// full-frame tint (mode 'multiply' | 'screen' | 'overlay' | 'soft-light' | 'source-over')
export function grade(g, color, a = 0.2, mode = 'soft-light') {
  g.save(); g.globalCompositeOperation = mode; g.globalAlpha = a; g.fillStyle = color; g.fillRect(0, 0, W, H); g.restore();
}
export function vgrad(g, x0, y0, x1, y1, stops) {
  const gr = g.createLinearGradient(x0, y0, x1, y1); for (const [o, c] of stops) gr.addColorStop(o, c); return gr;
}

// ---------------------------------------------------------------- offscreen layers
const _cv = new Map();
export function canvas(key, w = W, h = H) {
  let c = _cv.get(key); if (!c || c.width !== w || c.height !== h) { c = createCanvas(w, h); _cv.set(key, c); }
  return c;
}
// Draw fn into an offscreen layer, then composite it with blur (depth of field) and alpha.
export function blurLayer(g, key, blurPx, fn, alpha = 1) {
  const c = canvas('blur:' + key); const x = c.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H); fn(x);
  g.save(); g.globalAlpha *= alpha; if (blurPx > 0.3) g.filter = `blur(${blurPx.toFixed(1)}px)`;
  g.drawImage(c, 0, 0); g.restore();
}
// Cache an expensive static painting (e.g. a background) by key; fn(ctx) paints it once.
export function cached(key, fn, w = W, h = H) {
  const k = 'cache:' + key; if (_cv.has(k)) return _cv.get(k);
  const c = createCanvas(w, h); fn(c.getContext('2d')); _cv.set(k, c); return c;
}

// ---------------------------------------------------------------- camera
// cam = {x, y, zoom, rot}: (x,y) is the world point placed at screen center. World units == pixels at zoom 1.
export function withCam(g, cam, fn, depth = 1) {
  const z = 1 + ((cam.zoom ?? 1) - 1) * depth;
  g.save(); g.translate(W / 2, H / 2); g.rotate((cam.rot ?? 0) * depth); g.scale(z, z);
  g.translate(-(W / 2 + ((cam.x ?? W / 2) - W / 2) * depth), -(H / 2 + ((cam.y ?? H / 2) - H / 2) * depth));
  fn(g); g.restore();
}
// handheld drift (subtle) - returns {x,y,rot} offsets
export const handheld = (t, amp = 4, seed = 1) =>
  ({ x: fbm1(t * 0.35, seed) * amp, y: fbm1(t * 0.3, seed + 9) * amp, rot: fbm1(t * 0.2, seed + 4) * amp * 0.0015 });
export const shake = (t, amp, freq = 9, seed = 3) => ({ x: noise1(t * freq, seed) * amp, y: noise1(t * freq, seed + 5) * amp });

// ---------------------------------------------------------------- text helpers
export function titleCard(g, text, y, a = 1, size = 46, color = '#fff8ec') {
  if (a <= 0) return;
  g.save(); g.globalAlpha = a; g.font = `${size}px TitleSerif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.letterSpacing = `${Math.round(size * 0.22)}px`;
  g.shadowColor = 'rgba(0,0,0,0.55)'; g.shadowBlur = 18; g.fillStyle = color; g.fillText(text, W / 2, y);
  g.restore();
}
export function hudText(g, text, x, y, a = 1, size = 26, align = 'left') {
  if (a <= 0) return;
  g.save(); g.globalAlpha = a; g.font = `${size}px HUDMono`; g.textAlign = align; g.textBaseline = 'middle';
  g.shadowColor = rgba(PAL.hud, 0.8); g.shadowBlur = 10; g.fillStyle = PAL.hud; g.fillText(text, x, y); g.restore();
}
