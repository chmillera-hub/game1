// Shared helpers: math, easing, timeline access, blinking, simple shapes.
const fs = require('fs');
const path = require('path');

const W = 720, H = 1280;
const TL = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'timeline.json'), 'utf8'));
const FPS = TL.fps;

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = t => Math.pow(clamp(t), 3);
const easeInOut = t => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const easeOutBack = (t, s = 1.70158) => { t = clamp(t); const c3 = s + 1; return 1 + c3 * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2); };
const easeOutElastic = t => {
  t = clamp(t); if (t === 0 || t === 1) return t;
  return Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3) + 1;
};
// progress of t through [a, a+d]
const prog = (t, a, d) => clamp((t - a) / d);
// 0 -> 1 -> 0 pulse inside [a, a+d]
const pulse = (t, a, d) => { const p = (t - a) / d; return p <= 0 || p >= 1 ? 0 : Math.sin(p * Math.PI); };
// value that ramps in at a over din, holds, ramps out at b over dout
const window_ = (t, a, din, b, dout) => Math.min(smooth((t - a) / din), 1 - smooth((t - b) / dout));
const lerpColor = (c1, c2, t) => {
  const p = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const a = p(c1), b = p(c2);
  return 'rgb(' + a.map((v, i) => Math.round(lerp(v, b[i], clamp(t)))).join(',') + ')';
};

// deterministic pseudo random
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

// ---- timeline -------------------------------------------------------------
const MARKS = TL.marks;
function mark(name) {
  if (!(name in MARKS)) throw new Error('missing mark ' + name);
  return MARKS[name];
}
function lineById(id) { return TL.lines.find(l => l.id === id); }
function lineStart(id) { return lineById(id).start; }
function lineEnd(id) { return lineById(id).end; }

// mouth openness (0..1) for a character at time t, from the voice envelope
function amp(who, t) {
  for (const l of TL.lines) {
    if (l.who !== who || t < l.start || t >= l.end) continue;
    const f = (t - l.start) * FPS;
    const i = Math.floor(f), fr = f - i;
    const a = l.env[i] || 0, b = l.env[i + 1] || 0;
    return clamp(lerp(a, b, fr), 0, 1.1);
  }
  return 0;
}
function talking(who, t) {
  return TL.lines.some(l => l.who === who && t >= l.start - 0.05 && t < l.end + 0.1);
}
function activeLine(t) {
  return TL.lines.find(l => t >= l.start - 0.12 && t < l.end + 0.35);
}

// ---- blinking -------------------------------------------------------------
const blinkCache = {};
function blink(who, t) {
  if (!blinkCache[who]) {
    const r = rng(who.split('').reduce((a, c) => a * 31 + c.charCodeAt(0), 7));
    const arr = []; let x = 0.8 + r() * 1.5;
    while (x < TL.duration + 10) { arr.push(x); if (r() < 0.18) arr.push(x + 0.28); x += 2.2 + r() * 3.2; }
    blinkCache[who] = arr;
  }
  const d = 0.17;
  for (const b of blinkCache[who]) {
    if (t >= b && t < b + d) return Math.sin((t - b) / d * Math.PI);
    if (b > t) break;
  }
  return 0;
}

// ---- drawing helpers -------------------------------------------------------
function ellipse(ctx, x, y, rx, ry, rot = 0) {
  ctx.beginPath(); ctx.ellipse(x, y, Math.max(0.01, rx), Math.max(0.01, ry), rot, 0, Math.PI * 2);
}
function rrect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
}
function fillStroke(ctx, fill, stroke, lw) {
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 2; ctx.stroke(); }
}
function star(ctx, x, y, r, rot = 0, inner = 0.45, pts = 5) {
  ctx.beginPath();
  for (let i = 0; i < pts * 2; i++) {
    const a = rot - Math.PI / 2 + i * Math.PI / pts;
    const rr = i % 2 ? r * inner : r;
    const px = x + Math.cos(a) * rr, py = y + Math.sin(a) * rr;
    i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.closePath();
}
function heart(ctx, x, y, s) {
  ctx.beginPath();
  ctx.moveTo(x, y + s * 0.35);
  ctx.bezierCurveTo(x - s * 1.1, y - s * 0.35, x - s * 0.45, y - s * 1.05, x, y - s * 0.45);
  ctx.bezierCurveTo(x + s * 0.45, y - s * 1.05, x + s * 1.1, y - s * 0.35, x, y + s * 0.35);
  ctx.closePath();
}
// a soft twinkle/sparkle (4-point star)
function sparkle(ctx, x, y, r, color = '#fff', alpha = 1) {
  if (r <= 0.3 || alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x, y - r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.quadraticCurveTo(x, y, x, y + r);
  ctx.quadraticCurveTo(x, y, x - r, y); ctx.quadraticCurveTo(x, y, x, y - r);
  ctx.fill(); ctx.restore();
}
function cloudShape(ctx, x, y, w, h, bumps = 9) {
  ctx.beginPath();
  for (let i = 0; i <= bumps; i++) {
    const a = (i / bumps) * Math.PI * 2;
    const px = x + Math.cos(a) * w / 2, py = y + Math.sin(a) * h / 2;
    const a2 = ((i + 0.5) / bumps) * Math.PI * 2;
    const cx = x + Math.cos(a2) * w / 2 * 1.22, cy = y + Math.sin(a2) * h / 2 * 1.25;
    if (i === 0) ctx.moveTo(px, py); else ctx.quadraticCurveTo(cxPrev, cyPrev, px, py);
    var cxPrev = cx, cyPrev = cy;
  }
  ctx.closePath();
}

module.exports = {
  W, H, FPS, TL, clamp, lerp, smooth, easeOut, easeIn, easeInOut, easeOutBack, easeOutElastic, prog, pulse,
  window_, lerpColor, rng, mark, lineById, lineStart, lineEnd, amp, talking, activeLine, blink,
  ellipse, rrect, fillStroke, star, heart, sparkle, cloudShape,
};
