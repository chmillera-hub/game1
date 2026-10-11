// Core animation utilities: math, easing, noise, keyframe tracks, color, camera, drawing helpers.
// Everything is deterministic in time t (seconds) so any frame can be rendered independently.

export const W = 720, H = 1280, FPS = 24;
export const TAU = Math.PI * 2;

// ---------- math ----------
export const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, k) => a + (b - a) * k;
export const invLerp = (a, b, x) => (b === a ? 0 : (x - a) / (b - a));
export const remap = (x, a, b, c, d, clampIt = true) => {
  const k = invLerp(a, b, x);
  return lerp(c, d, clampIt ? clamp(k) : k);
};
export const smoothstep = (a, b, x) => {
  const k = clamp((x - a) / (b - a));
  return k * k * (3 - 2 * k);
};
export const mix = (a, b, k) => {
  // mix numbers or flat objects of numbers
  if (typeof a === 'number') return lerp(a, b, k);
  const o = { ...a };
  for (const key in b) {
    if (typeof b[key] === 'number') o[key] = lerp(typeof a[key] === 'number' ? a[key] : 0, b[key], k);
    else if (b[key] && typeof b[key] === 'object') o[key] = mix(a[key] || {}, b[key], k);
    else if (k >= 0.5) o[key] = b[key];
  }
  return o;
};

// ---------- easing ----------
export const ease = {
  linear: (k) => k,
  in: (k) => k * k,
  out: (k) => 1 - (1 - k) * (1 - k),
  inOut: (k) => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2),
  sine: (k) => -(Math.cos(Math.PI * k) - 1) / 2,
  cubic: (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  outCubic: (k) => 1 - Math.pow(1 - k, 3),
  inCubic: (k) => k * k * k,
  outBack: (k) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
  outElastic: (k) => (k === 0 || k === 1 ? k : Math.pow(2, -10 * k) * Math.sin((k * 10 - 0.75) * (TAU / 3)) + 1),
  step: (k) => (k < 1 ? 0 : 1),
  hold: (k) => 0,
};

// ---------- deterministic noise ----------
function hash(n) {
  n = (n << 13) ^ n;
  return 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0;
}
export const rand = (i, seed = 0) => (hash((i | 0) * 7919 + (seed | 0) * 104729) + 1) / 2; // 0..1
/** smooth value noise in [-1,1] */
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash(i + seed * 1013), b = hash(i + 1 + seed * 1013);
  const u = f * f * (3 - 2 * f);
  return a + (b - a) * u;
}
/** fractal noise, 2 octaves, [-1,1]-ish */
export const fbm = (x, seed = 0) => noise1(x, seed) * 0.7 + noise1(x * 2.3, seed + 17) * 0.3;

/**
 * Natural automatic blinking. Returns lid closure 0..1 (1 = fully closed).
 * rate = average blinks per second. Deterministic per seed.
 */
export function autoBlink(t, seed = 1, rate = 0.28, dur = 0.16) {
  // blink events at quasi-random intervals
  const period = 1 / rate;
  const i = Math.floor(t / period);
  let v = 0;
  for (let j = i - 1; j <= i + 1; j++) {
    const at = j * period + rand(j, seed) * period * 0.8;
    const dt = t - at;
    if (dt >= 0 && dt < dur) {
      const k = dt / dur;
      v = Math.max(v, k < 0.4 ? k / 0.4 : 1 - (k - 0.4) / 0.6);
    }
    // occasional double blink
    if (rand(j, seed + 99) > 0.8) {
      const dt2 = t - (at + dur + 0.08);
      if (dt2 >= 0 && dt2 < dur) {
        const k = dt2 / dur;
        v = Math.max(v, k < 0.4 ? k / 0.4 : 1 - (k - 0.4) / 0.6);
      }
    }
  }
  return v;
}

/** single blink shaped pulse centred at time `at` */
export function blinkAt(t, at, dur = 0.18) {
  const dt = t - at;
  if (dt < 0 || dt > dur) return 0;
  const k = dt / dur;
  return k < 0.4 ? k / 0.4 : 1 - (k - 0.4) / 0.6;
}

/** attack-hold-release envelope 0..1 */
export function env(t, start, attack, hold, release, e = ease.sine) {
  if (t < start) return 0;
  if (t < start + attack) return e((t - start) / attack);
  if (t < start + attack + hold) return 1;
  if (t < start + attack + hold + release) return 1 - e((t - start - attack - hold) / release);
  return 0;
}

// ---------- keyframes ----------
/**
 * Keyframe interpolation.
 *   kf(t, [[t0, v0], [t1, v1, 'inOut'], ...])
 * The easing on a key applies to the segment arriving at that key. Values may be numbers or
 * flat objects of numbers (merged/interpolated per field). Times must be ascending.
 */
export function kf(t, keys, defaultEase = 'sine') {
  if (!keys.length) return 0;
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t1, v1, e] = keys[i];
    if (t <= t1) {
      const [t0, v0] = keys[i - 1];
      const k = t1 === t0 ? 1 : (t - t0) / (t1 - t0);
      const fn = typeof e === 'function' ? e : ease[e || defaultEase];
      return mix(v0, v1, fn(clamp(k)));
    }
  }
  return keys[keys.length - 1][1];
}

// ---------- color ----------
export function hexToRgb(hex) {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
export const rgba = (hex, a = 1) => {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${a})`;
};
export function mixColor(c1, c2, k) {
  const a = hexToRgb(c1), b = hexToRgb(c2);
  const r = a.map((v, i) => Math.round(lerp(v, b[i], clamp(k))));
  return '#' + r.map((v) => v.toString(16).padStart(2, '0')).join('');
}
export const shade = (hex, k) => (k >= 0 ? mixColor(hex, '#ffffff', k) : mixColor(hex, '#000000', -k));

// ---------- drawing helpers ----------
export function ellipse(g, x, y, rx, ry, rot = 0) {
  g.beginPath();
  g.ellipse(x, y, Math.max(0.01, rx), Math.max(0.01, ry), rot, 0, TAU);
}
export function circle(g, x, y, r) {
  g.beginPath();
  g.arc(x, y, Math.max(0.01, r), 0, TAU);
}
export function roundRect(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, r);
}
/** radial glow */
export function glow(g, x, y, r, color, alpha = 1) {
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, rgba(color, alpha));
  gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr;
  g.fillRect(x - r, y - r, r * 2, r * 2);
}
/** soft contact shadow ellipse */
export function groundShadow(g, x, y, rx, alpha = 0.35, ry = rx * 0.18) {
  const gr = g.createRadialGradient(x, y, 0, x, y, rx);
  gr.addColorStop(0, `rgba(0,0,0,${alpha})`);
  gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.save();
  g.translate(x, y);
  g.scale(1, ry / rx);
  g.fillStyle = gr;
  g.beginPath();
  g.arc(0, 0, rx, 0, TAU);
  g.fill();
  g.restore();
}
/** smooth closed blob through points using quadratic midpoints */
export function blobPath(g, pts) {
  const n = pts.length;
  g.beginPath();
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  let m = mid(pts[n - 1], pts[0]);
  g.moveTo(m[0], m[1]);
  for (let i = 0; i < n; i++) {
    const p = pts[i], q = pts[(i + 1) % n];
    m = mid(p, q);
    g.quadraticCurveTo(p[0], p[1], m[0], m[1]);
  }
  g.closePath();
}
/** tapered limb (two-segment) from shoulder; returns hand position */
export function limb(g, x, y, len1, len2, a1, a2, w1, w2, color, outline) {
  const ex = x + Math.cos(a1) * len1, ey = y + Math.sin(a1) * len1;
  const hx = ex + Math.cos(a1 + a2) * len2, hy = ey + Math.sin(a1 + a2) * len2;
  g.lineCap = 'round';
  g.lineJoin = 'round';
  if (outline) {
    g.strokeStyle = outline;
    g.lineWidth = w1 + 4;
    g.beginPath(); g.moveTo(x, y); g.lineTo(ex, ey); g.lineTo(hx, hy); g.stroke();
  }
  g.strokeStyle = color;
  g.lineWidth = w1;
  g.beginPath(); g.moveTo(x, y); g.lineTo(ex, ey); g.stroke();
  g.lineWidth = (w1 + w2) / 2;
  g.beginPath(); g.moveTo(ex, ey); g.lineTo(hx, hy); g.stroke();
  return { ex, ey, hx, hy };
}

/**
 * Two-bone IK: given shoulder (sx,sy), target (tx,ty), bone lengths, bend direction (+1/-1).
 * Returns angles {a1, a2} usable with limb().
 */
export function ik(sx, sy, tx, ty, l1, l2, bend = 1) {
  const dx = tx - sx, dy = ty - sy;
  let d = Math.hypot(dx, dy);
  d = clamp(d, Math.abs(l1 - l2) + 0.01, l1 + l2 - 0.01);
  const base = Math.atan2(dy, dx);
  const cosA = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d);
  const a1 = base - bend * Math.acos(clamp(cosA, -1, 1));
  const cosB = (l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2);
  const a2 = bend * (Math.PI - Math.acos(clamp(cosB, -1, 1)));
  return { a1, a2 };
}

// ---------- camera ----------
/**
 * Apply camera: world point (x,y) appears at screen centre, scaled by zoom, rotated by rot.
 * Use inside save()/restore().
 */
export function applyCamera(g, cam) {
  const { x = W / 2, y = H / 2, zoom = 1, rot = 0, shakeX = 0, shakeY = 0 } = cam;
  g.translate(W / 2 + shakeX, H / 2 + shakeY);
  if (rot) g.rotate(rot);
  g.scale(zoom, zoom);
  g.translate(-x, -y);
}
/** gentle handheld drift for a living camera; amp in px */
export function drift(t, amp = 4, seed = 3) {
  return { dx: fbm(t * 0.23, seed) * amp, dy: fbm(t * 0.19, seed + 5) * amp, dr: fbm(t * 0.17, seed + 9) * 0.002 };
}

/** full-frame vignette */
export function vignette(g, strength = 0.45, color = '#000000') {
  const gr = g.createRadialGradient(W / 2, H * 0.48, H * 0.28, W / 2, H * 0.5, H * 0.75);
  gr.addColorStop(0, rgba(color, 0));
  gr.addColorStop(1, rgba(color, strength));
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);
}
