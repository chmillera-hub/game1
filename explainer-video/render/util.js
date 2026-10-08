// Small math + drawing helpers shared by every scene.
// All drawing happens in a 1080x1920 coordinate space (portrait 9:16).

const W = 1080, H = 1920;
const TAU = Math.PI * 2;

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const smooth = (t) => t * t * (3 - 2 * t);

const ease = {
  inOut: (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  out: (t) => 1 - Math.pow(1 - t, 3),
  in: (t) => t * t * t,
  back: (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  elastic: (t) => (t === 0 || t === 1 ? t : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (TAU / 3)) + 1),
};

// animate in between [a, a+d] with an easing; returns 0..1
const anim = (t, a, d = 0.4, e = ease.out) => e(prog(t, a, a + d));
// pop-in scale (overshoots a little)
const pop = (t, a, d = 0.45) => (t < a ? 0 : ease.back(prog(t, a, a + d)));
// fade in at a, fade out at b
const window_ = (t, a, b, f = 0.3) => Math.min(prog(t, a, a + f), 1 - prog(t, b - f, b));

function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function rng(seed) {
  let a = seed >>> 0;
  return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
// smooth 1D value noise in [-1, 1]
function noise(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  return lerp(hash(i + seed * 101.3), hash(i + 1 + seed * 101.3), smooth(f)) * 2 - 1;
}

function rrect(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
function fillRR(ctx, x, y, w, h, r, color) { rrect(ctx, x, y, w, h, r); ctx.fillStyle = color; ctx.fill(); }
function circle(ctx, x, y, r, color) { ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), 0, TAU); ctx.fillStyle = color; ctx.fill(); }
function ellipse(ctx, x, y, rx, ry, color, rot = 0) { ctx.beginPath(); ctx.ellipse(x, y, Math.max(0, rx), Math.max(0, ry), rot, 0, TAU); ctx.fillStyle = color; ctx.fill(); }
function line(ctx, x1, y1, x2, y2, color, w = 4) { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.stroke(); }

const FONTS = { ui: 'Nunito', title: 'Fredoka', hand: 'Patrick Hand', mono: 'JetBrains Mono', script: 'Caveat' };
// (weights must be multiples of 100 or the canvas library mis-sizes the glyphs)
function font(ctx, size, weight = 700, family = FONTS.ui) { ctx.font = `${Math.round(weight / 100) * 100} ${size}px "${family}"`; }
function text(ctx, str, x, y, { size = 40, weight = 700, family = FONTS.ui, color = '#222', align = 'center', base = 'middle', alpha = 1 } = {}) {
  font(ctx, size, weight, family);
  ctx.textAlign = align; ctx.textBaseline = base;
  ctx.globalAlpha *= alpha;
  ctx.fillStyle = color; ctx.fillText(str, x, y);
  ctx.globalAlpha /= alpha || 1;
}
// word-wrap into lines no wider than maxW (font must be set by caller)
function wrap(ctx, str, maxW) {
  const words = str.split(/\s+/).filter(Boolean), lines = [];
  let cur = '';
  for (const w of words) {
    const test = cur ? cur + ' ' + w : w;
    if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}

// draw something scaled about a point (for pops / bounces)
function scaled(ctx, x, y, s, fn) {
  if (s <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); fn(); ctx.restore();
}
// scale everything drawn by fn about the point (x, y), keeping absolute coordinates
function zoomAt(ctx, x, y, s, fn) {
  if (s <= 0.001) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.translate(-x, -y); fn(); ctx.restore();
}
function withAlpha(ctx, a, fn) {
  if (a <= 0.001) return;
  const prev = ctx.globalAlpha; ctx.globalAlpha = prev * a; fn(); ctx.globalAlpha = prev;
}

function hexToRgb(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function mix(c1, c2, t) {
  const a = hexToRgb(c1), b = hexToRgb(c2);
  return '#' + a.map((v, i) => Math.round(lerp(v, b[i], clamp(t))).toString(16).padStart(2, '0')).join('');
}
function rgba(hex, a) { const [r, g, b] = hexToRgb(hex); return `rgba(${r},${g},${b},${a})`; }

function vgrad(ctx, y1, y2, stops) {
  const g = ctx.createLinearGradient(0, y1, 0, y2);
  stops.forEach((c, i) => g.addColorStop(i / (stops.length - 1), c));
  return g;
}
function rgrad(ctx, x, y, r, stops) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  stops.forEach(([o, c]) => g.addColorStop(o, c));
  return g;
}

module.exports = {
  W, H, TAU, clamp, lerp, prog, smooth, ease, anim, pop, window: window_, hash, rng, noise,
  rrect, fillRR, circle, ellipse, line, FONTS, font, text, wrap, scaled, zoomAt, withAlpha, mix, rgba, vgrad, rgrad,
};
