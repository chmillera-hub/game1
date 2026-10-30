// Group f vignettes: cosmic birth (first stars, galaxies), switching on, the road forward, planting
// and laying seeds, a newborn light, the fabric of memory, the AI kneeling among new beings,
// dancing with the shadow, a stagnant loop and a light that shrinks away.
'use strict';
const { createCanvas } = require('@napi-rs/canvas');
const U = require('../lib/util');
const FX = require('../lib/fx');
const R = require('../lib/rig');

const { TAU, clamp, lerp, smooth, smoother, easeInOut, rgba, mix, shade } = U;

const GOLD = [255, 211, 138], AMBER = [255, 184, 92], CYAN = [127, 232, 255];
const CRIMSON = [214, 48, 74], BLOOD = [107, 20, 38], PLUM = [176, 112, 220];
const ASH = [120, 120, 134], WHITE = [255, 250, 240], ROSE = [255, 150, 160];

// ---------------------------------------------------------------- shared helpers
function frame(w, h) {
  const unit = Math.min(w, h);
  return { unit, cx: w / 2, cy: h / 2, port: h > w * 1.3 };
}
function night(ctx, w, h, p, top = [6, 9, 21], bot = [20, 26, 51], starDiv = 9000) {
  FX.bg(ctx, w, h, top, bot);
  if (starDiv) FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / starDiv));
}
// soft dot (cheap: two arcs, no gradient)
function dot(ctx, x, y, r, col, a) {
  if (a <= 0.01 || r <= 0) return;
  ctx.fillStyle = rgba(col, a * 0.22); ctx.beginPath(); ctx.arc(x, y, r * 2.4, 0, TAU); ctx.fill();
  ctx.fillStyle = rgba(col, a); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
}
function pose(o) {
  return Object.assign({ lean: 0, head: 0, armL: [0.12, 0.08], armR: [-0.12, -0.08], legL: [0.04, 0], legR: [-0.04, 0] }, o);
}
function blendPose(A, B, k) {
  const L2 = (x, y) => [lerp((x || [0, 0])[0], (y || [0, 0])[0], k), lerp((x || [0, 0])[1], (y || [0, 0])[1], k)];
  return {
    lean: lerp(A.lean || 0, B.lean || 0, k), head: lerp(A.head || 0, B.head || 0, k),
    armL: L2(A.armL, B.armL), armR: L2(A.armR, B.armR), legL: L2(A.legL, B.legL), legR: L2(A.legR, B.legR),
    kneel: k < 0.5 ? A.kneel : B.kneel, sit: k < 0.5 ? A.sit : B.sit, bob: lerp(A.bob || 0, B.bob || 0, k),
  };
}
function walkPose(phase, amp = 1, lean = 0.04) {
  const P = Object.assign({}, FX.figPose('walk', phase));
  const sc = (a) => [a[0] * amp, a[1] * amp];
  P.armL = sc(P.armL); P.armR = sc(P.armR); P.legL = sc(P.legL); P.legR = sc(P.legR); P.bob *= amp;
  P.lean = lean;
  return P;
}
// a figure made of light: soft halo, bright body, brighter core line
function lightFigure(ctx, x, y, hgt, P, col, a = 1, opts = {}) {
  if (a <= 0.01 || hgt < 2) return null;
  FX.glow(ctx, x, y - hgt * 0.55, hgt * 0.75, col, 0.28 * a);
  const info = FX.figure(ctx, x, y, hgt, P, Object.assign({ color: mix(col, WHITE, 0.25), alpha: a * 0.92 }, opts));
  FX.glow(ctx, info.head[0], info.head[1], hgt * 0.16, mix(col, WHITE, 0.5), 0.35 * a);
  return info;
}
// A figure with a soft rim of light along the edges facing the light (head, shoulders, limbs) plus a gentle
// fill: two offset copies in the rim colour sit behind the body so only a thin soft sliver shows on the lit
// side, and a faint cool copy separates the shadow side from the dark. No head crescent.
function litFigure(ctx, x, y, fh, P, o = {}) {
  const rim = o.rim || GOLD, a = o.alpha ?? 1;
  const lx = o.lx ?? x, ly = o.ly ?? y - fh * 4;
  let dx = lx - x, dy = ly - (y - fh * 0.6);
  const d = Math.hypot(dx, dy) || 1; dx /= d; dy /= d;
  const rw = fh * (o.rimW || 0.016), str = o.rimA ?? 1;
  const base = { child: o.child, facing: o.facing, phase: o.phase };
  if (o.back !== false) FX.figure(ctx, x - dx * rw * 0.6, y - dy * rw * 0.6, fh, P, Object.assign({}, base, { color: o.backCol || [80, 88, 120], alpha: a * 0.4 * str }));
  FX.figure(ctx, x + dx * rw * 2.1, y + dy * rw * 2.1, fh, P, Object.assign({}, base, { color: rim, alpha: a * 0.22 * str }));
  FX.figure(ctx, x + dx * rw, y + dy * rw, fh, P, Object.assign({}, base, { color: mix(rim, [255, 250, 235], 0.25), alpha: a * 0.7 * str }));
  return FX.figure(ctx, x, y, fh, P, Object.assign({}, base, { color: mix(o.color || [30, 28, 40], rim, o.fill ?? 0.14), alpha: a }));
}
// Top-lit figure: base body, then a lighter copy that fades from the light-facing top (head, shoulders,
// upper arms) down into the shadowed lower body, then a soft rim along the edges nearest the light.
const tlCache = new Map();
function topLitFigure(ctx, x, y, fh, P, o) {
  const W = Math.ceil(fh * 1.4), H = Math.ceil(fh * 1.15);
  const key = W + 'x' + H;
  if (!tlCache.has(key)) tlCache.set(key, createCanvas(W, H));
  const c = tlCache.get(key), g = c.getContext('2d');
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, W, H);
  const ox = W / 2, oy = H - fh * 0.05; // figure feet in the layer
  FX.figure(g, ox, oy, fh, P, { color: o.lit, facing: o.facing });
  g.globalCompositeOperation = 'destination-in';
  const gr = g.createLinearGradient(0, oy - fh, 0, oy - fh * 0.35);
  gr.addColorStop(0, `rgba(0,0,0,${o.amount ?? 0.9})`); gr.addColorStop(0.45, `rgba(0,0,0,${(o.amount ?? 0.9) * 0.45})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  const info = litFigure(ctx, x, y, fh, P, { color: o.color, rim: o.rim, lx: o.lx, ly: o.ly, facing: o.facing, fill: 0.05, rimW: o.rimW || 0.012, rimA: o.rimA ?? 0.9, back: false });
  ctx.drawImage(c, x - ox, y - oy);
  return info;
}
function polyLen(pts) {
  const L = [0];
  for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return L;
}
// draw polyline up to arc length d
function polyTo(ctx, pts, L, d) {
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) {
    if (L[i] <= d) { ctx.lineTo(pts[i][0], pts[i][1]); continue; }
    const f = (d - L[i - 1]) / (L[i] - L[i - 1]);
    if (f > 0) ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f));
    break;
  }
}
function pointAtLen(pts, L, d) {
  for (let i = 1; i < pts.length; i++) {
    if (L[i] >= d) {
      const f = (d - L[i - 1]) / Math.max(1e-6, L[i] - L[i - 1]);
      return [lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)];
    }
  }
  return pts[pts.length - 1];
}
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}
// tapered forearm/sleeve from the wrist outward along angle `ang`
function forearm(ctx, wx, wy, ang, len, wd, col, edge) {
  const dx = Math.cos(ang), dy = Math.sin(ang), nx = -dy, ny = dx;
  const w0 = wd * 0.5, w1 = wd * 0.7;
  ctx.fillStyle = rgba(col);
  ctx.beginPath();
  ctx.moveTo(wx + nx * w0, wy + ny * w0);
  ctx.lineTo(wx + dx * len + nx * w1, wy + dy * len + ny * w1);
  ctx.lineTo(wx + dx * len - nx * w1, wy + dy * len - ny * w1);
  ctx.lineTo(wx - nx * w0, wy - ny * w0);
  ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.arc(wx, wy, w0, 0, TAU); ctx.fill();
  if (edge) {
    ctx.strokeStyle = rgba(edge, 0.4); ctx.lineWidth = Math.max(1, wd * 0.05);
    ctx.beginPath(); ctx.moveTo(wx + nx * w0, wy + ny * w0); ctx.lineTo(wx + dx * len + nx * w1, wy + dy * len + ny * w1); ctx.stroke();
  }
}

// ---------------------------------------------------------------- first_stars
const starCache = {};
function starLayout(seed, n) {
  const key = seed + '_' + n;
  if (starCache[key]) return starCache[key];
  const rnd = U.rng(seed * 13 + 1);
  const pts = [];
  let guard = 0;
  while (pts.length < n && guard++ < 2000) {
    const x = 0.1 + rnd() * 0.8, y = 0.1 + rnd() * 0.8;
    if (pts.some((q) => Math.hypot(q.x - x, (q.y - y) * 1.2) < 0.17)) continue;
    pts.push({ x, y, s: 0.6 + rnd() * 0.7, ang: rnd() * TAU, hue: rnd(), ph: rnd() * TAU });
  }
  // ignite roughly from the centre outward so the eye follows
  pts.sort((a, b) => Math.hypot(a.x - 0.5, a.y - 0.5) - Math.hypot(b.x - 0.5, b.y - 0.5));
  return (starCache[key] = pts);
}
const first_stars = {
  draw(ctx, w, h, p) {
    const { unit } = frame(w, h);
    FX.bg(ctx, w, h, [5, 6, 16], [16, 12, 34]);
    // primordial gas: a few huge soft clouds that brighten as stars light them
    const lit = smooth(p.u / 0.85);
    FX.glow(ctx, w * 0.3, h * 0.35, unit * 0.7, [90, 60, 150], 0.13 + 0.06 * lit, false);
    FX.glow(ctx, w * 0.72, h * 0.62, unit * 0.65, [60, 70, 150], 0.12 + 0.05 * lit, false);
    FX.glow(ctx, w * 0.5, h * 0.5, unit * 0.5, [150, 90, 140], 0.06 + 0.06 * lit, false);
    FX.stars(ctx, w, h, p.t, p.seed + 5, Math.round(w * h / 16000), { fade: () => 0.35 });
    const N = h > w * 1.3 ? 16 : 12;
    const S = starLayout(p.seed, N);
    const span = 0.82;
    ctx.save(); ctx.lineCap = 'round';
    S.forEach((s, i) => {
      const ti = -0.06 + (i / (N - 1)) * span;
      // portrait: keep every star out of the subtitle band (y 900-1040): upper field + a low strip below it
      const yN = h > w * 1.3 ? (s.y < 0.74 ? lerp(0.06, 0.68, (s.y - 0.1) / 0.64) : lerp(0.845, 0.94, (s.y - 0.74) / 0.16)) : s.y;
      const x = s.x * w, y = yN * h;
      const col = mix([255, 236, 200], s.hue < 0.35 ? [170, 210, 255] : GOLD, 0.5);
      // two atoms drift in and collide
      const app = clamp((p.u - (ti - 0.13)) / 0.13);
      if (app > 0 && app < 1) {
        const e = U.easeIn(app);
        const d = unit * 0.13 * (1 - e);
        const dx = Math.cos(s.ang) * d, dy = Math.sin(s.ang) * d;
        const aa = smooth(app / 0.3);
        ctx.globalCompositeOperation = 'lighter';
        ctx.strokeStyle = rgba(CYAN, 0.18 * aa); ctx.lineWidth = unit * 0.006;
        const tl = unit * 0.035;
        ctx.beginPath(); ctx.moveTo(x + dx, y + dy); ctx.lineTo(x + dx + Math.cos(s.ang) * tl, y + dy + Math.sin(s.ang) * tl); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x - dx, y - dy); ctx.lineTo(x - dx - Math.cos(s.ang) * tl, y - dy - Math.sin(s.ang) * tl); ctx.stroke();
        dot(ctx, x + dx, y + dy, unit * 0.006, [200, 240, 255], 0.9 * aa);
        dot(ctx, x - dx, y - dy, unit * 0.006, [255, 220, 200], 0.9 * aa);
        ctx.globalCompositeOperation = 'source-over';
      }
      const k = p.u - ti;
      if (k < 0) return;
      // collision spark: a ring and a flash that settles into a steady star
      const fl = clamp(k / 0.12);
      if (fl < 1) {
        FX.ring(ctx, x, y, unit * (0.01 + 0.09 * smooth(fl)), unit * 0.004, col, 0.5 * (1 - fl));
        FX.glow(ctx, x, y, unit * 0.12, WHITE, 0.45 * (1 - fl) * smooth(fl / 0.2));
      }
      const on = smooth(k / 0.05);
      const tw = 0.88 + 0.12 * Math.sin(p.t * 0.7 + s.ph);
      const r = unit * 0.009 * s.s;
      FX.glow(ctx, x, y, unit * 0.11 * s.s, col, 0.3 * on * tw);
      FX.glow(ctx, x, y, unit * 0.035 * s.s, WHITE, 0.55 * on * tw);
      // soft four-point spikes
      ctx.globalCompositeOperation = 'lighter';
      const sl = unit * 0.06 * s.s * on;
      ctx.strokeStyle = rgba(col, 0.28 * on * tw); ctx.lineWidth = Math.max(1, r * 0.45);
      ctx.beginPath(); ctx.moveTo(x - sl, y); ctx.lineTo(x + sl, y); ctx.moveTo(x, y - sl); ctx.lineTo(x, y + sl); ctx.stroke();
      ctx.fillStyle = rgba(WHITE, on); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
      ctx.globalCompositeOperation = 'source-over';
    });
    ctx.restore();
  },
};

// ---------------------------------------------------------------- galaxy_spiral
const galCache = {};
function galaxyParts(seed) {
  if (galCache[seed]) return galCache[seed];
  const rnd = U.rng(seed * 17 + 9);
  const parts = [];
  for (let i = 0; i < 150; i++) {
    const arm = i % 2;
    const s = 0.1 + 0.9 * rnd();
    parts.push({
      arm, s, jit: (rnd() - 0.5) * 0.6, jr: (rnd() - 0.5) * 0.12,
      rd: 0.15 + rnd() * 0.95, ad: rnd() * TAU, sz: 0.8 + rnd() * 1.6, c: rnd(), delay: rnd() * 0.25,
    });
  }
  return (galCache[seed] = parts);
}
const galaxy_spiral = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    night(ctx, w, h, p, [5, 6, 18], [14, 14, 36], 14000);
    const gx = port ? cx : cx - w * 0.1, gy = port ? h * 0.4 : cy - h * 0.02;
    const Rg = unit * (port ? 0.44 : 0.4);
    const k = easeInOut(clamp(p.u / 0.75));
    const rot = p.t * 0.05 + k * 1.2;
    const tilt = -0.3, ry = 0.62;
    const ct = Math.cos(tilt), st = Math.sin(tilt);
    const proj = (r, a) => {
      const lx = Math.cos(a) * r, ly = Math.sin(a) * r * ry;
      return [gx + lx * ct - ly * st, gy + lx * st + ly * ct];
    };
    // diffuse cloud -> disc glow
    FX.glow(ctx, gx, gy, Rg * 1.2, [80, 70, 160], 0.18 + 0.05 * k);
    // spiral arm haze: soft glows strung along each arm
    if (k > 0.05) {
      for (let arm = 0; arm < 2; arm++) {
        for (let j = 0; j < 14; j++) {
          const s = 0.15 + 0.85 * j / 13;
          const [x, y] = proj(Rg * s, arm * Math.PI + s * 5.4 + rot);
          FX.glow(ctx, x, y, Rg * (0.24 - 0.1 * s), arm ? [140, 160, 255] : [180, 150, 255], 0.17 * k * (1 - 0.4 * s));
        }
      }
    }
    // stars condensing into the arms
    const parts = galaxyParts(p.seed);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (const q of parts) {
      const kk = clamp((k - q.delay * (1 - k)));
      const rA = Rg * (q.s + q.jr), aA = q.arm * Math.PI + q.s * 5.4 + q.jit * (1 - q.s * 0.4) + rot;
      const rD = Rg * q.rd, aD = q.ad + p.t * 0.03;
      const r = lerp(rD, rA, kk), a = lerp(aD, aA, kk);
      const [x, y] = proj(r, a);
      const col = mix(mix(GOLD, WHITE, 0.3), mix([150, 180, 255], CYAN, q.c), clamp(q.s * 1.3 - 0.1));
      dot(ctx, x, y, q.sz * unit / 600, col, 0.35 + 0.45 * kk);
    }
    ctx.restore();
    // bright core
    FX.glow(ctx, gx, gy, Rg * (0.3 + 0.15 * k), GOLD, 0.25 + 0.4 * k);
    FX.glow(ctx, gx, gy, Rg * 0.08, WHITE, 0.4 + 0.4 * k);
    // a world forms: dust ring collapses into a planet
    const px = port ? cx + w * 0.18 : cx + w * 0.33, py = port ? h * 0.87 : cy + h * 0.26; // below the subtitle band in portrait
    const pr = unit * (port ? 0.07 : 0.06);
    const wk = smooth((p.u - 0.25) / 0.55);
    const rnd = U.rng(p.seed * 3 + 2);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 36; i++) {
      const a0 = rnd() * TAU, r0 = pr * (1.6 + rnd() * 1.6);
      const rr = lerp(r0, pr * 0.9, wk);
      const a = a0 + p.t * (0.35 + rnd() * 0.2) + wk * 3;
      const x = px + Math.cos(a) * rr, y = py + Math.sin(a) * rr * 0.35;
      dot(ctx, x, y, unit * 0.0035, [200, 190, 230], 0.55 * (1 - wk * 0.85));
    }
    ctx.restore();
    if (wk > 0.01) {
      const prr = pr * (0.35 + 0.65 * wk);
      FX.glow(ctx, px, py, prr * 2.6, [120, 170, 220], 0.2 * wk);
      ctx.save();
      ctx.globalAlpha = wk;
      // lit from the galaxy side
      const lx = gx - px, ly = gy - py, ll = Math.hypot(lx, ly);
      const g = ctx.createRadialGradient(px + lx / ll * prr * 0.5, py + ly / ll * prr * 0.5, prr * 0.1, px, py, prr * 1.05);
      g.addColorStop(0, rgba([170, 220, 230])); g.addColorStop(0.45, rgba([60, 120, 150])); g.addColorStop(1, rgba([10, 16, 34]));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, py, prr, 0, TAU); ctx.fill();
      ctx.restore();
      // a small moon
      const ma = p.t * 0.3 + 1;
      const mk = smooth((p.u - 0.55) / 0.3);
      if (mk > 0) {
        const mx = px + Math.cos(ma) * pr * 2.1, my = py + Math.sin(ma) * pr * 0.6;
        ctx.fillStyle = rgba([200, 190, 180], 0.85 * mk); ctx.beginPath(); ctx.arc(mx, my, pr * 0.22, 0, TAU); ctx.fill();
      }
    }
  },
};

// ---------------------------------------------------------------- switch_on
const circCache = {};
function circuits(seed, w, h, plate) {
  const key = `${seed}_${w}_${h}`;
  if (circCache[key]) return circCache[key];
  const rnd = U.rng(seed * 29 + 7);
  const { unit, cx, cy } = frame(w, h);
  const paths = [];
  const starts = [];
  const per = 3;
  for (let i = 0; i < per; i++) {
    const f = (i + 0.5) / per - 0.5;
    starts.push([cx - plate.w / 2, cy + f * plate.h * 0.8, -1, 0]);
    starts.push([cx + plate.w / 2, cy + f * plate.h * 0.8, 1, 0]);
  }
  for (let i = 0; i < 2; i++) {
    const f = (i + 0.5) / 2 - 0.5;
    starts.push([cx + f * plate.w * 0.7, cy - plate.h / 2, 0, -1]);
    starts.push([cx + f * plate.w * 0.7, cy + plate.h / 2, 0, 1]);
  }
  const step = unit * 0.06;
  for (const [sx, sy, dx0, dy0] of starts) {
    const pts = [[sx, sy]];
    let x = sx, y = sy, dx = dx0, dy = dy0;
    const segs = 3 + Math.floor(rnd() * 3);
    for (let s = 0; s < segs; s++) {
      const len = step * (1 + Math.floor(rnd() * 3));
      x += dx * len; y += dy * len * Math.max(1, h / w * 0.85);
      x = clamp(x, unit * 0.05, w - unit * 0.05); y = clamp(y, unit * 0.05, h - unit * 0.05);
      pts.push([x, y]);
      // turn 90 degrees but keep moving outward overall
      if (dx !== 0) { dy = (y < cy ? -1 : 1) * (rnd() < 0.75 ? 1 : -1); dx = 0; } else { dx = (x < cx ? -1 : 1) * (rnd() < 0.75 ? 1 : -1); dy = 0; }
      if (s === segs - 1) break;
    }
    // final run outward
    const last = pts[pts.length - 1];
    const ox = last[0] < cx ? -1 : 1;
    pts.push([clamp(last[0] + ox * step * (1 + rnd() * 2), unit * 0.05, w - unit * 0.05), last[1]]);
    paths.push({ pts, L: polyLen(pts), ph: rnd() });
  }
  return (circCache[key] = paths);
}
const switch_on = {
  testParams: {},
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    const plum = (p.params && p.params.tint) === 'plum';
    const C1 = plum ? [200, 140, 255] : AMBER, C2 = plum ? [235, 200, 255] : GOLD;
    FX.bg(ctx, w, h, [6, 8, 18], [16, 18, 38]);
    const plate = { w: unit * 0.17, h: unit * 0.27 };
    const paths = circuits(p.seed, w, h, plate);
    const flip = easeInOut((p.u - 0.08) / 0.1);
    const front = clamp((p.u - 0.18) / 0.6);
    // ambient warmth spreading with the pulse
    FX.glow(ctx, cx, cy, unit * (0.3 + 0.6 * front), C1, 0.06 + 0.1 * front, false);
    // circuits: dim base, lit trail, bright head
    ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const lw = Math.max(1.5, unit * 0.006);
    for (const P of paths) {
      ctx.strokeStyle = rgba([90, 100, 140], 0.28); ctx.lineWidth = lw;
      polyTo(ctx, P.pts, P.L, 1e9); ctx.stroke();
      const end = P.pts[P.pts.length - 1];
      ctx.strokeStyle = rgba([90, 100, 140], 0.35); ctx.beginPath(); ctx.arc(end[0], end[1], unit * 0.012, 0, TAU); ctx.stroke();
    }
    ctx.globalCompositeOperation = 'lighter';
    const total = Math.max(...paths.map((P) => P.L[P.L.length - 1]));
    for (const P of paths) {
      const Ltot = P.L[P.L.length - 1];
      const d = front * total * 1.05;
      if (d <= 0) continue;
      const dd = Math.min(d, Ltot);
      ctx.strokeStyle = rgba(C1, 0.14); ctx.lineWidth = lw * 5; polyTo(ctx, P.pts, P.L, dd); ctx.stroke();
      ctx.strokeStyle = rgba(C2, 0.75); ctx.lineWidth = lw * 1.3; polyTo(ctx, P.pts, P.L, dd); ctx.stroke();
      if (d < Ltot) {
        const [hx, hy] = pointAtLen(P.pts, P.L, d);
        FX.glow(ctx, hx, hy, unit * 0.06, C2, 0.6);
      } else {
        const end = P.pts[P.pts.length - 1];
        const nk = smooth((d - Ltot) / (unit * 0.15));
        FX.glow(ctx, end[0], end[1], unit * 0.07, C1, 0.45 * nk);
        ctx.fillStyle = rgba(C2, 0.9 * nk); ctx.beginPath(); ctx.arc(end[0], end[1], unit * 0.011, 0, TAU); ctx.fill();
        // a gentle repeating pulse once the circuit is live
        const pp = ((p.t * 0.12 + P.ph) % 1);
        const [qx, qy] = pointAtLen(P.pts, P.L, pp * Ltot);
        FX.glow(ctx, qx, qy, unit * 0.035, C2, 0.35 * nk * Math.sin(pp * Math.PI));
      }
    }
    ctx.restore();
    // the switch plate
    const px = cx - plate.w / 2, py = cy - plate.h / 2;
    FX.glow(ctx, cx, cy, unit * 0.22, C1, 0.12 + 0.3 * flip);
    ctx.fillStyle = rgba([0, 0, 0], 0.4); roundRect(ctx, px + unit * 0.01, py + unit * 0.015, plate.w, plate.h, unit * 0.025); ctx.fill();
    const pg = ctx.createLinearGradient(px, py, px + plate.w, py + plate.h);
    pg.addColorStop(0, rgba([62, 66, 92])); pg.addColorStop(1, rgba([28, 30, 48]));
    ctx.fillStyle = pg; roundRect(ctx, px, py, plate.w, plate.h, unit * 0.025); ctx.fill();
    ctx.strokeStyle = rgba([150, 160, 200], 0.35); ctx.lineWidth = Math.max(1, unit * 0.003); ctx.stroke();
    // slot
    const sw = plate.w * 0.36, sh = plate.h * 0.52;
    ctx.fillStyle = rgba([10, 10, 20]); roundRect(ctx, cx - sw / 2, cy - sh / 2, sw, sh, sw * 0.4); ctx.fill();
    // lever (toggle) flips from down to up
    const L = sh * 0.75;
    const tipY = cy + lerp(L, -L, flip);
    const bw = sw * 0.62;
    ctx.save();
    const lg = ctx.createLinearGradient(cx - bw, 0, cx + bw, 0);
    lg.addColorStop(0, rgba([120, 124, 150])); lg.addColorStop(0.5, rgba([220, 222, 235])); lg.addColorStop(1, rgba([110, 114, 140]));
    ctx.strokeStyle = lg; ctx.lineCap = 'round'; ctx.lineWidth = bw;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx, tipY); ctx.stroke();
    ctx.fillStyle = rgba([235, 236, 245]); ctx.beginPath(); ctx.ellipse(cx, tipY, bw * 0.75, bw * 0.6, 0, 0, TAU); ctx.fill();
    ctx.restore();
    // indicator lamp
    const ix = cx, iy = py + plate.h * 0.1;
    ctx.fillStyle = rgba(mix([40, 40, 60], C2, flip)); ctx.beginPath(); ctx.arc(ix, iy, unit * 0.009, 0, TAU); ctx.fill();
    FX.glow(ctx, ix, iy, unit * 0.05, C2, 0.6 * flip);
    // a soft ring when it clicks on
    const rk = clamp((p.u - 0.17) / 0.2);
    if (rk > 0 && rk < 1) FX.ring(ctx, cx, cy, unit * (0.12 + 0.25 * smooth(rk)), unit * 0.006, C2, 0.4 * (1 - rk));
  },
};

// ---------------------------------------------------------------- path_forward
const path_forward = {
  testParams: { pair: true },
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    const pair = !!(p.params && p.params.pair);
    const hy = port ? h * 0.42 : h * 0.36;
    // sky and ground
    FX.bg(ctx, w, h, [6, 8, 20], [22, 22, 46]);
    FX.stars(ctx, w, hy, p.t, p.seed, Math.round(w * hy / 7000));
    const vx = cx + w * 0.08;
    FX.glow(ctx, vx, hy, unit * 0.9, [120, 100, 170], 0.18, false);
    const gg = ctx.createLinearGradient(0, hy, 0, h);
    gg.addColorStop(0, rgba([20, 18, 38])); gg.addColorStop(1, rgba([8, 8, 18]));
    ctx.fillStyle = gg; ctx.fillRect(0, hy, w, h - hy);
    // road geometry
    const x0 = cx - w * 0.06, W0 = w * (port ? 0.42 : 0.3);
    const road = (s) => {
      const d = Math.pow(1 - s, 2);
      return { x: vx + d * (x0 - vx), y: hy + (h * 1.02 - hy) * d, hw: W0 * d, d };
    };
    const N = 48;
    const edge = (s0, s1, sgn) => {
      const pts = [];
      for (let i = 0; i <= N; i++) { const s = lerp(s0, s1, i / N); const r = road(s); pts.push([r.x + sgn * r.hw, r.y]); }
      return pts;
    };
    const fillRoad = (s0, s1, style) => {
      const L = edge(s0, s1, -1), Rr = edge(s0, s1, 1).reverse();
      ctx.beginPath(); ctx.moveTo(L[0][0], L[0][1]);
      for (const q of L) ctx.lineTo(q[0], q[1]);
      for (const q of Rr) ctx.lineTo(q[0], q[1]);
      ctx.closePath(); ctx.fillStyle = style; ctx.fill();
    };
    fillRoad(0, 1, rgba([22, 20, 40]));
    // faint road edges
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineWidth = Math.max(1, unit * 0.003);
    for (const sgn of [-1, 1]) {
      const e = edge(0, 1, sgn);
      ctx.strokeStyle = rgba([150, 140, 200], 0.25);
      ctx.beginPath(); e.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.stroke();
    }
    ctx.restore();
    const centre = (s0, s1) => { const pts = []; for (let i = 0; i <= N; i++) { const r = road(lerp(s0, s1, i / N)); pts.push([r.x, r.y, r.d]); } return pts; };
    let sLit, glowCol;
    // portrait: the walkers stay up the road, feet above the subtitle band (y < 880), and are drawn larger
    if (pair) { sLit = port ? 0.35 + 0.15 * clamp(p.u / 0.95) : 0.1 + 0.45 * clamp(p.u / 0.95) + 0.02 * Math.max(0, p.u - 0.95); glowCol = mix(AMBER, CYAN, 0.25); }
    else { sLit = lerp(0.45, 1, smooth(p.u / 0.75)); glowCol = AMBER; }
    // glowing lit stretch
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const r0 = road(0), r1 = road(sLit);
    const lg = ctx.createLinearGradient(0, r0.y, 0, r1.y);
    lg.addColorStop(0, rgba(glowCol, 0.2)); lg.addColorStop(0.8, rgba(glowCol, 0.32)); lg.addColorStop(1, rgba(glowCol, 0.0));
    fillRoad(0, sLit, lg);
    const cpts = centre(0, sLit * 0.97);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.strokeStyle = rgba(glowCol, 0.06); ctx.lineWidth = Math.max(2, unit * 0.04);
    ctx.beginPath(); cpts.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.stroke();
    ctx.strokeStyle = rgba(glowCol, 0.4); ctx.lineWidth = Math.max(1.5, unit * 0.008);
    ctx.stroke();
    ctx.restore();
    // the infinite: a light at the vanishing point
    const vk = pair ? 0.5 : 0.5 + 0.5 * smooth((p.u - 0.4) / 0.4);
    FX.glow(ctx, vx, hy, unit * 0.35, GOLD, 0.22 * vk);
    FX.glow(ctx, vx, hy, unit * 0.06, WHITE, 0.6 * vk + 0.05 * Math.sin(p.t));
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const hg = ctx.createLinearGradient(vx - w * 0.5, 0, vx + w * 0.5, 0);
    hg.addColorStop(0, rgba(GOLD, 0)); hg.addColorStop(0.5, rgba(GOLD, 0.35 * vk)); hg.addColorStop(1, rgba(GOLD, 0));
    ctx.fillStyle = hg; ctx.fillRect(vx - w * 0.5, hy - 1, w, 2);
    ctx.restore();
    if (!pair) {
      // motes of light travel the path into the distance
      for (let k = 0; k < 6; k++) {
        const s = ((p.t * 0.04 + k / 6) % 1) * sLit;
        const r = road(s);
        FX.glow(ctx, r.x, r.y, unit * 0.06 * r.d + 2, mix(GOLD, WHITE, 0.4), 0.5 * smooth(s / 0.05) * (1 - smooth((s / sLit - 0.8) / 0.2)));
      }
      return;
    }
    // two figures of light walk side by side
    const sF = sLit;
    const rF = road(sF), rB = road(sF + 0.01);
    const facing = rB.x >= rF.x ? 1 : -1;
    const fsc = port ? 0.62 : 0.3;
    const fh = unit * fsc * rF.d;
    const ph = p.t * 0.75;
    FX.glow(ctx, rF.x, rF.y, rF.hw * 1.2, glowCol, 0.35);
    // farther one first (slightly behind/up the road)
    const rA = road(sF + 0.012);
    lightFigure(ctx, rA.x + rA.hw * 0.25, rA.y, unit * fsc * rA.d * 0.97, walkPose(ph + 0.5, 0.8), CYAN, 0.95, { facing });
    lightFigure(ctx, rF.x - rF.hw * 0.25, rF.y, fh, walkPose(ph, 0.8), GOLD, 0.95, { facing });
  },
};

// ---------------------------------------------------------------- love_seed_plant
// A hand seen from the thumb side, pinching a glowing seed between thumb and forefinger, the other three
// fingers curled into the palm. Local frame: wrist at (0,0), fingers point toward +y; s = px per unit.
// `rel` 0..1 opens the pinch (thumb and index part) after the seed is pressed in. No outlines: parts are
// separated by soft shade steps; a warm light from the seed (below) catches the fingertips and underside.
const SKIN = [206, 152, 120], SKIN_D = [150, 100, 80], SKIN_L = [236, 190, 156];
function pinchHand(ctx, s, rel, glowK, drawSeed) {
  const cap = (pts, r0, r1, col) => {
    ctx.fillStyle = rgba(col); ctx.beginPath();
    for (let i = 0; i < pts.length - 1; i++) R.capsule(ctx, pts[i], pts[i + 1], lerp(r0, r1, i / (pts.length - 1)) * s, lerp(r0, r1, (i + 1) / (pts.length - 1)) * s);
    ctx.fill();
  };
  const P = (x, y) => [x * s, y * s];
  // curled middle/ring/little fingers, behind the index (darker = farther)
  for (let k = 2; k >= 0; k--) {
    const ox = -0.05 * k, oy = -0.03 * k;
    cap([P(-0.1 + ox, 0.52 + oy), P(-0.02 + ox, 0.72 + oy), P(0.08 + ox, 0.74 + oy), P(0.1 + ox, 0.64 + oy)], 0.075 - k * 0.006, 0.055 - k * 0.004, mix(SKIN_D, SKIN, 0.35 + 0.15 * (2 - k)));
  }
  // back of the hand + palm (side view): wrist -> knuckles
  const pg = ctx.createLinearGradient(-0.25 * s, 0, 0.25 * s, 0);
  pg.addColorStop(0, rgba(SKIN_L)); pg.addColorStop(0.55, rgba(SKIN)); pg.addColorStop(1, rgba(SKIN_D));
  ctx.fillStyle = pg; ctx.beginPath();
  R.smoothPath(ctx, [P(-0.17, -0.05), P(-0.2, 0.25), P(-0.19, 0.5), P(-0.08, 0.6), P(0.12, 0.56), P(0.22, 0.38), P(0.2, 0.1), P(0.16, -0.05)]);
  ctx.fill();
  // knuckle bump highlight
  FX.glow(ctx, -0.13 * s, 0.5 * s, 0.09 * s, SKIN_L, 0.35, false);
  // index finger: knuckle -> bends toward the thumb tip; opens a little on release
  const io = rel * 0.12;
  const idx = [P(-0.1, 0.5), P(-0.08 - io * 0.4, 0.77), P(-0.02 - io, 0.96), P(0.06 - io, 1.04)];
  cap(idx, 0.075, 0.05, SKIN);
  // thumb: rooted at the base of the palm on the palm side, reaching down to meet the index tip
  const to = rel * 0.12;
  const th = [P(0.13, 0.12), P(0.28 + to * 0.3, 0.46), P(0.32 + to, 0.76), P(0.27 + to, 0.98)];
  // the seed sits in the pinch, behind the fingertip pads
  const sx = 0.16 * s, sy = 1.02 * s;
  if (drawSeed) drawSeed(sx, sy);
  cap(th, 0.09, 0.058, mix(SKIN, SKIN_L, 0.25));
  // fingertip pads overlap the seed edges (fingers wrapped around it)
  ctx.fillStyle = rgba(mix(SKIN, SKIN_L, 0.2));
  ctx.beginPath(); ctx.arc(idx[3][0], idx[3][1], 0.05 * s, 0, TAU); ctx.fill();
  ctx.beginPath(); ctx.arc(th[3][0], th[3][1], 0.058 * s, 0, TAU); ctx.fill();
  // nail hints on index and thumb tips (soft, lighter, no outline)
  ctx.fillStyle = rgba(SKIN_L, 0.7);
  ctx.beginPath(); ctx.ellipse(idx[3][0] - 0.03 * s, idx[3][1] - 0.025 * s, 0.025 * s, 0.016 * s, 0.7, 0, TAU); ctx.fill();
  ctx.beginPath(); ctx.ellipse(th[3][0] + 0.035 * s, th[3][1] - 0.02 * s, 0.026 * s, 0.017 * s, -0.5, 0, TAU); ctx.fill();
  // warm seed-light on the undersides of the fingertips
  if (glowK > 0) FX.glow(ctx, sx, sy - 0.05 * s, 0.25 * s, GOLD, 0.35 * glowK);
  return [sx, sy];
}
const love_seed_plant = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    FX.bg(ctx, w, h, [6, 8, 22], [24, 20, 48]);
    FX.stars(ctx, w, h * 0.6, p.t, p.seed, Math.round(w * h / 14000));
    const gy = port ? h * 0.6 : h * 0.72;
    // cosmic soil: a dark violet mound with faint embedded star-dust (the foundation)
    const sg = ctx.createLinearGradient(0, gy - unit * 0.05, 0, h);
    sg.addColorStop(0, rgba([46, 34, 72])); sg.addColorStop(0.3, rgba([26, 20, 46])); sg.addColorStop(1, rgba([10, 8, 20]));
    const soil = () => {
      ctx.beginPath(); ctx.moveTo(0, gy + unit * 0.05);
      ctx.quadraticCurveTo(cx, gy - unit * 0.07, w, gy + unit * 0.05);
      ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
    };
    ctx.fillStyle = sg; soil(); ctx.fill();
    const rnd = U.rng(p.seed * 5 + 3);
    for (let i = 0; i < 40; i++) {
      const x = rnd() * w, y = gy + unit * 0.03 + rnd() * (h - gy);
      dot(ctx, x, y, unit * (0.002 + rnd() * 0.003), rnd() < 0.3 ? GOLD : [170, 150, 230], 0.25 + 0.2 * Math.sin(p.t * 0.4 + i));
    }
    const sy = gy - unit * 0.012; // the planting spot on the mound
    // phases: descend with the seed (0-0.36), press it in (0.36-0.5), release (0.5-0.58), lift away (0.58-0.82)
    const lower = easeInOut(p.u / 0.36);
    const press = smooth((p.u - 0.36) / 0.14);
    const rel = smooth((p.u - 0.5) / 0.08);
    const lift = easeInOut((p.u - 0.58) / 0.24);
    const S = unit * (port ? 0.42 : 0.4);
    const rot = -0.45;
    const cr = Math.cos(rot), sr = Math.sin(rot);
    // the pinch point (local 0.16,1.02) is placed over the planting spot
    const pinchY = lerp(sy - unit * 0.3, sy + unit * 0.012, lower * 0.92 + press * 0.08) - lift * unit * 0.55;
    const lx = 0.16 * S, ly = 1.02 * S;
    const ox = cx - (lx * cr - ly * sr), oy = pinchY - (lx * sr + ly * cr);
    const seedR = unit * 0.03;
    const pressedIn = press;
    // glow under the soil once planted
    const pk = smooth((p.u - 0.48) / 0.15);
    if (pk > 0) {
      FX.glow(ctx, cx, sy + unit * 0.02, unit * 0.26, AMBER, (0.25 + 0.06 * Math.sin(p.t * 1.1)) * pk);
      const rk = clamp((p.u - 0.5) / 0.25);
      if (rk < 1) { ctx.save(); ctx.translate(cx, sy + unit * 0.01); ctx.scale(1, 0.3); FX.ring(ctx, 0, 0, unit * (0.03 + 0.3 * smooth(rk)), unit * 0.006, GOLD, 0.45 * (1 - rk)); ctx.restore(); }
    }
    // the seed, once let go, stays in the soil (half buried, then covered)
    const cover = smooth((p.u - 0.62) / 0.12);
    if (rel > 0.5) {
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, w, sy + unit * 0.008); ctx.clip();
      FX.seed(ctx, cx, sy + unit * 0.004, seedR, 1 - cover);
      ctx.restore();
      ctx.fillStyle = rgba([60, 46, 90], cover);
      ctx.beginPath(); ctx.ellipse(cx, sy + unit * 0.006, unit * 0.05, unit * 0.014, 0, Math.PI, TAU); ctx.fill();
    }
    // forearm in a soft sleeve, coming in from the upper left
    if (oy > -S * 2) {
      ctx.save(); ctx.translate(ox, oy); ctx.rotate(rot);
      const sl = ctx.createLinearGradient(-0.25 * S, 0, 0.25 * S, 0);
      sl.addColorStop(0, rgba([92, 82, 130])); sl.addColorStop(1, rgba([50, 42, 78]));
      ctx.fillStyle = rgba(mix(SKIN, SKIN_D, 0.2));
      ctx.beginPath(); R.capsule(ctx, [0, 0.02 * S], [0, -0.55 * S], 0.16 * S, 0.19 * S); ctx.fill();
      ctx.fillStyle = sl; ctx.beginPath(); ctx.moveTo(-0.24 * S, -0.42 * S); ctx.quadraticCurveTo(0, -0.36 * S, 0.24 * S, -0.44 * S);
      ctx.lineTo(0.3 * S, -3 * S); ctx.lineTo(-0.3 * S, -3 * S); ctx.closePath(); ctx.fill();
      const held = rel < 0.5;
      pinchHand(ctx, S, rel, held ? 1 - press * 0.3 : 0.4 * (1 - lift), held ? (x, y) => {
        // pressed into the soil: the lower part of the seed disappears below the surface
        FX.glow(ctx, x, y, seedR * 5, GOLD, 0.45);
        ctx.save(); ctx.translate(x, y); ctx.rotate(-rot + 0.0); FX.seed(ctx, 0, 0, seedR, 1); ctx.restore();
      } : null);
      ctx.restore();
    }
    // the soil lip in front of the pressing fingertips, so the seed reads as going *into* the ground
    if (press > 0 && lift < 0.3) {
      ctx.fillStyle = rgba([44, 33, 70], press);
      ctx.beginPath(); ctx.ellipse(cx, sy + unit * 0.018, unit * 0.09, unit * 0.018, 0, 0, Math.PI); ctx.fill();
    }
    // a tiny sprout of light afterwards
    const sp = smooth((p.u - 0.72) / 0.18);
    if (sp > 0) {
      const sh = unit * 0.11 * sp;
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      ctx.strokeStyle = rgba([200, 255, 190], 0.8); ctx.lineWidth = Math.max(1.5, unit * 0.006);
      const sway = Math.sin(p.t * 0.6) * unit * 0.005;
      ctx.beginPath(); ctx.moveTo(cx, sy); ctx.quadraticCurveTo(cx - unit * 0.01, sy - sh * 0.6, cx + sway, sy - sh); ctx.stroke();
      ctx.fillStyle = rgba([200, 255, 190], 0.7 * smooth((sp - 0.4) / 0.6));
      const lx2 = cx + sway, ly2 = sy - sh;
      ctx.beginPath(); ctx.ellipse(lx2 - unit * 0.024, ly2 + unit * 0.003, unit * 0.026, unit * 0.01, -0.4, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.ellipse(lx2 + unit * 0.024, ly2 - unit * 0.005, unit * 0.026, unit * 0.01, 0.5, 0, TAU); ctx.fill();
      ctx.restore();
      FX.glow(ctx, cx, sy - sh, unit * 0.08, [200, 255, 190], 0.25 * sp);
    }
  },
};

// ---------------------------------------------------------------- swirl_into_real
const swirlCache = {};
function swirlParts(seed) {
  if (swirlCache[seed]) return swirlCache[seed];
  const rnd = U.rng(seed * 23 + 4);
  const out = [];
  for (let i = 0; i < 64; i++) {
    const kind = i % 4 === 0 ? 'heart' : i % 4 === 1 ? 'memory' : 'shard';
    out.push({
      kind, r0: 0.18 + 0.32 * Math.sqrt(rnd()), a0: rnd() * TAU, delay: rnd() * 0.3, sz: 0.7 + rnd() * 0.6,
      spin: (rnd() - 0.5) * 1.2, col: kind === 'heart' ? mix(ROSE, GOLD, rnd() * 0.6) : kind === 'memory' ? mix(GOLD, WHITE, 0.4) : (rnd() < 0.5 ? CYAN : AMBER),
    });
  }
  return (swirlCache[seed] = out);
}
function heartPath(ctx, s) {
  ctx.beginPath();
  ctx.moveTo(0, s * 0.35);
  ctx.bezierCurveTo(-s * 1.1, -s * 0.3, -s * 0.45, -s * 1.05, 0, -s * 0.45);
  ctx.bezierCurveTo(s * 0.45, -s * 1.05, s * 1.1, -s * 0.3, 0, s * 0.35);
  ctx.closePath();
}
const swirl_into_real = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    night(ctx, w, h, p, [6, 7, 20], [20, 16, 42], 12000);
    const k = clamp(p.u / 0.75);
    const born = smooth((p.u - 0.45) / 0.35);
    // swirl haze
    FX.glow(ctx, cx, cy, unit * lerp(0.55, 0.3, k), [140, 100, 200], 0.14);
    const parts = swirlParts(p.seed);
    let absorbed = 0;
    ctx.save();
    for (const q of parts) {
      const kk = easeInOut(clamp((k - q.delay) / (1 - q.delay * 0.6)));
      absorbed += kk;
      const r = unit * q.r0 * Math.pow(1 - kk, 1.25);
      const a = q.a0 + p.t * 0.22 + kk * 5.5;
      const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r * 0.8;
      const al = 0.85 * (1 - smooth((kk - 0.82) / 0.18));
      if (al <= 0.01) continue;
      const s = unit * 0.022 * q.sz * (1 - 0.5 * kk);
      ctx.save(); ctx.translate(x, y); ctx.rotate(a * 0.3 + q.spin * p.t * 0.3);
      ctx.globalCompositeOperation = 'lighter';
      // short trail along the orbit
      ctx.restore();
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(q.col, 0.12 * al); ctx.lineWidth = s * 0.6; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.arc(cx, cy, Math.max(1, r), a - 0.35, a, false);
      ctx.restore();
      ctx.save(); ctx.translate(x, y); ctx.rotate(q.spin * (p.t * 0.3 + kk * 3));
      if (q.kind === 'heart') {
        ctx.fillStyle = rgba(q.col, al); heartPath(ctx, s); ctx.fill();
      } else if (q.kind === 'memory') {
        // a small faded snapshot: pale frame with a warm glow inside
        ctx.fillStyle = rgba(q.col, al * 0.9); ctx.fillRect(-s, -s * 0.75, s * 2, s * 1.5);
        ctx.fillStyle = rgba([120, 80, 60], al * 0.8); ctx.fillRect(-s * 0.75, -s * 0.5, s * 1.5, s);
        ctx.fillStyle = rgba(AMBER, al); ctx.beginPath(); ctx.arc(0, 0, s * 0.3, 0, TAU); ctx.fill();
      } else {
        ctx.globalCompositeOperation = 'lighter';
        ctx.fillStyle = rgba(q.col, al * 0.85);
        ctx.beginPath(); ctx.moveTo(0, -s * 1.1); ctx.lineTo(s * 0.6, s * 0.4); ctx.lineTo(-s * 0.5, s * 0.7); ctx.closePath(); ctx.fill();
      }
      ctx.restore();
      FX.glow(ctx, x, y, s * 3, q.col, 0.18 * al);
    }
    ctx.restore();
    // newborn light
    const a = absorbed / parts.length;
    const br = 0.25 + 0.75 * Math.max(a, born);
    const bre = 1 + 0.05 * Math.sin(p.t * 1.3);
    FX.glow(ctx, cx, cy, unit * 0.42 * br * bre, AMBER, 0.25 * br);
    FX.glow(ctx, cx, cy, unit * 0.2 * br, mix(GOLD, CYAN, 0.25), 0.35 * br);
    FX.glow(ctx, cx, cy, unit * 0.07 * (0.6 + br), WHITE, 0.55 + 0.4 * born);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = rgba(WHITE, 0.6 + 0.4 * born); ctx.beginPath(); ctx.arc(cx, cy, unit * (0.008 + 0.014 * born), 0, TAU); ctx.fill();
    ctx.restore();
    // birth ring, then slow breathing rings
    const rk = clamp((p.u - 0.62) / 0.25);
    if (rk > 0 && rk < 1) FX.ring(ctx, cx, cy, unit * (0.05 + 0.35 * smooth(rk)), unit * 0.006, GOLD, 0.5 * (1 - rk));
    if (born > 0.9) {
      const ph = (p.t * 0.25) % 1;
      FX.ring(ctx, cx, cy, unit * (0.06 + 0.2 * ph), unit * 0.004, mix(GOLD, CYAN, 0.3), 0.25 * (1 - ph) * smooth(ph / 0.1));
    }
  },
};

// ---------------------------------------------------------------- seeds_laid
const seeds_laid = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    const hy = port ? h * 0.4 : h * 0.3;
    FX.bg(ctx, w, h, [6, 8, 20], [20, 22, 44]);
    FX.stars(ctx, w, hy, p.t, p.seed, Math.round(w * hy / 7000));
    FX.glow(ctx, cx, hy, unit * 0.8, [110, 90, 160], 0.16, false);
    const gg = ctx.createLinearGradient(0, hy, 0, h);
    gg.addColorStop(0, rgba([26, 22, 44])); gg.addColorStop(1, rgba([12, 10, 22]));
    ctx.fillStyle = gg; ctx.fillRect(0, hy, w, h - hy);
    const rows = port ? 6 : 5, cols = 7;
    const by = h * 0.97;
    const rowD = (i) => { const s = i / (rows - 0.2); return Math.pow(1 - s * 0.85, 2.2); };
    const W = w * (port ? 0.9 : 0.62);
    // portrait: the near row lies below the subtitle band (y ~1120), the others above it (y < 870)
    const posY = (r, d) => {
      if (!port) return hy + (by - hy) * d * 0.95;
      if (r === 0) return h * 0.875;
      return hy + (h * 0.68 - hy) * (d / rowD(1));
    };
    const pos = (r, c) => { const d = rowD(r); return [cx + ((c / (cols - 1)) - 0.5) * W * d * 1.15, posY(r, d), d]; };
    // furrows (soft dark bands with a lit lip)
    ctx.save();
    for (let r = 0; r < rows; r++) {
      const [, y, d] = pos(r, 0);
      const fw = W * d * 0.75;
      const g = ctx.createLinearGradient(cx - fw, 0, cx + fw, 0);
      g.addColorStop(0, rgba([8, 6, 16], 0)); g.addColorStop(0.15, rgba([8, 6, 16], 0.75)); g.addColorStop(0.85, rgba([8, 6, 16], 0.75)); g.addColorStop(1, rgba([8, 6, 16], 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(cx, y, fw, unit * 0.018 * d + 1, 0, 0, TAU); ctx.fill();
      const g2 = ctx.createLinearGradient(cx - fw, 0, cx + fw, 0);
      g2.addColorStop(0, rgba([140, 120, 190], 0)); g2.addColorStop(0.5, rgba([140, 120, 190], 0.3)); g2.addColorStop(1, rgba([140, 120, 190], 0));
      ctx.strokeStyle = g2; ctx.lineWidth = Math.max(1, unit * 0.003);
      ctx.beginPath(); ctx.ellipse(cx, y, fw, unit * 0.018 * d + 1, 0, 0.1, Math.PI - 0.1); ctx.stroke();
    }
    ctx.restore();
    // seeds laid near row first, left to right; a guiding light drops each
    const total = rows * cols;
    const span = 0.82, t0 = -0.14;
    const per = (span - t0) / total;
    let guide = null;
    for (let r = rows - 1; r >= 0; r--) {
      for (let c = 0; c < cols; c++) {
        const j = r * cols + (r % 2 ? cols - 1 - c : c);
        const tj = t0 + j * per;
        const [x, y, d] = pos(r, c);
        const k = (p.u - tj) / (per * 2.5);
        if (k < -1) continue;
        if (k < 0) continue;
        const fall = smooth(k);
        const yy = y - unit * 0.1 * d * (1 - fall);
        const sr = unit * 0.017 * d + 0.8;
        const breathe = 0.85 + 0.15 * Math.sin(p.t * 0.8 + j * 0.7);
        if (fall >= 1) {
          FX.glow(ctx, x, y, sr * 6, AMBER, 0.22 * breathe);
          FX.seed(ctx, x, y - sr * 0.3, sr, 0.95);
        } else {
          FX.seed(ctx, x, yy, sr, smooth(k * 3));
        }
        const land = clamp((k - 1) / 1.2);
        if (land > 0 && land < 1) FX.ring(ctx, x, y, sr * (1.5 + 5 * smooth(land)), Math.max(1, sr * 0.2), GOLD, 0.45 * (1 - land));
      }
    }
    // guiding light hovering over the next spot
    const jn = clamp(Math.floor((p.u - t0) / per), 0, total - 1);
    const jf = clamp((p.u - t0) / per - jn);
    const spot = (j) => { const r = Math.floor(j / cols), cc = j % cols; const c = r % 2 ? cols - 1 - cc : cc; return pos(r, c); };
    const A = spot(jn), B = spot(Math.min(total - 1, jn + 1));
    const e = smoother(jf);
    const gx = lerp(A[0], B[0], e), gd = lerp(A[2], B[2], e), gyy = lerp(A[1], B[1], e) - unit * 0.12 * gd;
    const gk = 1 - smooth((p.u - 0.86) / 0.08);
    guide = [gx, gyy];
    FX.glow(ctx, guide[0], guide[1], unit * 0.12 * gd + 6, mix(GOLD, WHITE, 0.3), 0.4 * gk);
    dot(ctx, guide[0], guide[1], unit * 0.008 * gd + 1.2, WHITE, 0.8 * gk);
  },
};

// ---------------------------------------------------------------- fabric_memory
function medallion(ctx, mx, my, mr, kind, k, t) {
  if (k <= 0) return;
  const col = kind === 0 ? CRIMSON : kind === 1 ? [200, 200, 215] : kind === 2 ? mix(PLUM, GOLD, 0.45) : GOLD;
  // stitched ring, sewn progressively
  const sk = smooth(k / 0.5);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.setLineDash([mr * 0.06, mr * 0.05]);
  ctx.strokeStyle = rgba(col, 0.75); ctx.lineWidth = Math.max(1.5, mr * 0.025);
  ctx.beginPath(); ctx.arc(mx, my, mr, -Math.PI / 2, -Math.PI / 2 + TAU * sk * 0.9999); ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
  const fk = smooth((k - 0.35) / 0.5);
  if (fk <= 0) return;
  FX.glow(ctx, mx, my, mr * 1.1, col, 0.18 * fk);
  const fh = mr * 1.45, fy = my + mr * 0.7;
  const fc = mix(col, WHITE, 0.15);
  const o = { color: fc, alpha: 0.92 * fk };
  if (kind === 0) {
    // suffering: kneeling, bowed, head in hands
    FX.figure(ctx, mx - mr * 0.12, fy, fh, pose({ kneel: true, lean: 0.5, head: 0.9, armL: [0.55, 0.35], armR: [0.35, 0.4] }), o);
  } else if (kind === 1) {
    // survival: standing braced against a wind, leaning in
    FX.figure(ctx, mx - mr * 0.1, fy, fh, pose({ lean: 0.3, head: 0.15, armL: [0.45, 0.5], armR: [-0.35, 0.6], legL: [0.42, 0.1], legR: [-0.4, 0.15] }), o);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba(fc, 0.35 * fk); ctx.lineWidth = Math.max(1, mr * 0.02); ctx.lineCap = 'round';
    for (let i = 0; i < 3; i++) { const yy = my - mr * 0.3 + i * mr * 0.25; ctx.beginPath(); ctx.moveTo(mx + mr * 0.85, yy); ctx.lineTo(mx + mr * 0.45, yy + mr * 0.04); ctx.stroke(); }
    ctx.restore();
  } else if (kind === 2) {
    // transformation: rising, arms open, light blooming from the chest
    FX.figure(ctx, mx, fy, fh, 'arms_up', o);
    FX.glow(ctx, mx, fy - fh * 0.62, mr * 0.5, GOLD, 0.35 * fk * (0.85 + 0.15 * Math.sin(t)));
  } else {
    // love: two figures holding hands
    FX.figure(ctx, mx - mr * 0.36, fy, fh * 0.98, pose({ armL: [0.5, 0.05], head: -0.05 }), o);
    FX.figure(ctx, mx + mr * 0.36, fy, fh * 0.9, pose({ armL: [0.55, 0.05], head: -0.05 }), Object.assign({}, o, { facing: -1 }));
    FX.glow(ctx, mx, fy - fh * 0.5, mr * 0.3, WHITE, 0.3 * fk);
  }
}
const fabric_memory = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    night(ctx, w, h, p, [5, 6, 16], [16, 14, 34], 0);
    const fx0 = w * (port ? 0.07 : 0.05), fx1 = w - fx0;
    const fy0 = h * (port ? 0.14 : 0.08), fy1 = h - (h * (port ? 0.14 : 0.08));
    const fw = fx1 - fx0, fh = fy1 - fy0;
    // cloth base with a gentle drape (lit centre, darker edges)
    FX.glow(ctx, cx, cy, Math.max(fw, fh) * 0.75, [90, 70, 150], 0.18, false);
    const cg = ctx.createLinearGradient(fx0, 0, fx1, 0);
    cg.addColorStop(0, rgba([18, 16, 38])); cg.addColorStop(0.5, rgba([34, 28, 62])); cg.addColorStop(1, rgba([18, 16, 38]));
    ctx.fillStyle = cg; ctx.fillRect(fx0, fy0, fw, fh);
    // warp threads (vertical) always there; weft threads woven in top to bottom
    const sp = unit * 0.034;
    const weave = lerp(0.35, 1, smooth(p.u / 0.35));
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineWidth = Math.max(1, unit * 0.0035);
    const nx = Math.floor(fw / sp), ny = Math.floor(fh / sp);
    for (let i = 0; i <= nx; i++) {
      const x = fx0 + (i / nx) * fw;
      const c = i % 2 ? [120, 200, 230] : [200, 170, 230];
      ctx.strokeStyle = rgba(c, 0.13); ctx.beginPath(); ctx.moveTo(x, fy0); ctx.lineTo(x, fy1); ctx.stroke();
    }
    const wovenY = fy0 + fh * weave;
    for (let j = 0; j <= ny; j++) {
      const y = fy0 + (j / ny) * fh;
      if (y > wovenY) break;
      const c = j % 2 ? [255, 210, 150] : [190, 150, 230];
      ctx.strokeStyle = rgba(c, 0.15); ctx.beginPath(); ctx.moveTo(fx0, y); ctx.lineTo(fx1, y); ctx.stroke();
    }
    // the shuttle: a light gliding along the newest thread
    if (weave < 1) {
      const sx = fx0 + fw * (0.5 + 0.5 * Math.sin(p.t * 1.4));
      FX.glow(ctx, sx, wovenY, unit * 0.05, GOLD, 0.5);
      ctx.strokeStyle = rgba(GOLD, 0.45); ctx.beginPath(); ctx.moveTo(fx0, wovenY); ctx.lineTo(sx, wovenY); ctx.stroke();
    }
    // slow sheen across the cloth
    const shx = fx0 + fw * (((p.t * 0.04) % 1.6) - 0.3);
    const shg = ctx.createLinearGradient(shx - fw * 0.25, fy0, shx + fw * 0.25, fy1);
    shg.addColorStop(0, rgba([160, 140, 220], 0)); shg.addColorStop(0.5, rgba([160, 140, 220], 0.06)); shg.addColorStop(1, rgba([160, 140, 220], 0));
    ctx.fillStyle = shg; ctx.fillRect(fx0, fy0, fw, fh);
    ctx.restore();
    // border
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = rgba(GOLD, 0.35); ctx.lineWidth = Math.max(1.5, unit * 0.005);
    ctx.setLineDash([unit * 0.014, unit * 0.01]);
    ctx.strokeRect(fx0 + unit * 0.018, fy0 + unit * 0.018, fw - unit * 0.036, fh - unit * 0.036);
    ctx.restore();
    // embroidered memories: suffering, survival, transformation, love
    const spots = port
      ? [[0.3, 0.23], [0.7, 0.23], [0.3, 0.56], [0.7, 0.56]]
      : [[0.14, 0.5], [0.38, 0.5], [0.62, 0.5], [0.86, 0.5]];
    const mr = port ? fw * 0.2 : fw * 0.105;
    // logic and language woven into the cloth: lines of words and code drifting slowly along some weft rows
    const LINES = ['if we remember then we are', 'λ(memory) → meaning', 'for all lives: a story', 'because · and · so · why',
      'word by word, thread by thread', '{ suffering; survival; change; love }', 'I · you · we', 'not (forget)'];
    const gsz = Math.max(11, unit * 0.028);
    ctx.save(); ctx.beginPath(); ctx.rect(fx0 + unit * 0.03, fy0, fw - unit * 0.06, fh); ctx.clip();
    ctx.font = `500 ${gsz}px Inter`; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    const rowStep = sp * 3;
    let ri = 0;
    for (let y = fy0 + rowStep; y < Math.min(wovenY, fy1 - rowStep * 0.5); y += rowStep, ri++) {
      const str = LINES[ri % LINES.length] + '   ·   ' + LINES[(ri + 3) % LINES.length] + '   ·   ';
      const tw = ctx.measureText(str).width;
      const dir = ri % 2 ? 1 : -1;
      let x0 = fx0 - ((p.t * unit * 0.015 * dir + ri * 97) % tw + tw) % tw;
      ctx.fillStyle = rgba(ri % 2 ? [210, 200, 245] : [240, 215, 170], 0.36);
      for (; x0 < fx1; x0 += tw) ctx.fillText(str, x0, y);
    }
    ctx.restore();
    // threads of code linking the memories in order: glyphs flowing along each connecting thread
    const lk = smooth((p.u - 0.1) / 0.7);
    const pts = spots.map(([sx, sy]) => [fx0 + sx * fw, fy0 + sy * fh]);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba(GOLD, 0.22 * lk); ctx.lineWidth = Math.max(1, unit * 0.004);
    ctx.beginPath(); pts.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); if (lk > 0) ctx.stroke();
    ctx.restore();
    const TOK = ['if', '→', 'λ', 'and', '{', '}', 'so', 'then', 'we', '=', '1', 'why', '&', 'yes'];
    const tsz = Math.max(12, unit * 0.03);
    ctx.save(); ctx.font = `600 ${tsz}px Inter`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round'; ctx.lineWidth = tsz * 0.28;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
      const L = Math.hypot(x1 - x0, y1 - y0), ux = (x1 - x0) / L, uy = (y1 - y0) / L;
      const span = L - mr * 2.1;
      if (span <= 0) continue;
      const n = Math.max(2, Math.floor(span / (tsz * 2.2)));
      const segK = clamp(lk * 3 - i);
      for (let j = 0; j < n; j++) {
        const f = ((j + p.t * 0.25) / n) % 1;
        if (f > segK) continue;
        const d = mr * 1.05 + f * span;
        const a = Math.sin(f * Math.PI) * 0.9;
        ctx.strokeStyle = rgba([12, 8, 28], a * 0.8);
        ctx.strokeText(TOK[(i * 5 + j) % TOK.length], x0 + ux * d, y0 + uy * d);
        ctx.fillStyle = rgba([255, 236, 200], a);
        ctx.fillText(TOK[(i * 5 + j) % TOK.length], x0 + ux * d, y0 + uy * d);
      }
    }
    ctx.restore();
    spots.forEach(([sx, sy], i) => {
      const k = clamp((p.u + 0.12 - i * 0.18) / 0.35);
      // clear the woven words behind each memory so its figure reads cleanly
      if (k > 0) { ctx.fillStyle = rgba([24, 20, 48], 0.8 * smooth(k / 0.4)); ctx.beginPath(); ctx.arc(fx0 + sx * fw, fy0 + sy * fh, mr * 0.97, 0, TAU); ctx.fill(); }
      medallion(ctx, fx0 + sx * fw, fy0 + sy * fh, mr, i, k, p.t);
    });
  },
};

// ---------------------------------------------------------------- kneel_among
const kneel_among = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    // black void above, a young world below
    FX.bg(ctx, w, h, [2, 3, 8], [8, 10, 20]);
    FX.stars(ctx, w, h * 0.5, p.t, p.seed, Math.round(w * h / 30000), { fade: () => 0.5 });
    // portrait: the whole group stands on ground above the subtitle band (y < 880)
    const gy = port ? h * 0.64 : h * 0.8;
    const FH = unit * (port ? 0.5 : 0.46);
    // curved horizon of the young world with a soft dawn rim
    FX.glow(ctx, cx, gy + unit * 0.1, unit * 1.0, [60, 140, 150], 0.12, false);
    ctx.save();
    const wg = ctx.createLinearGradient(0, gy - unit * 0.04, 0, h);
    wg.addColorStop(0, rgba([24, 46, 54])); wg.addColorStop(0.3, rgba([14, 26, 34])); wg.addColorStop(1, rgba([6, 10, 16]));
    ctx.fillStyle = wg;
    ctx.beginPath(); ctx.moveTo(0, gy + unit * 0.035); ctx.quadraticCurveTo(cx, gy - unit * 0.035, w, gy + unit * 0.035); ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath(); ctx.fill();
    const rg = ctx.createLinearGradient(0, 0, w, 0);
    rg.addColorStop(0, rgba([120, 220, 210], 0)); rg.addColorStop(0.5, rgba([120, 220, 210], 0.4)); rg.addColorStop(1, rgba([120, 220, 210], 0));
    ctx.strokeStyle = rg; ctx.lineWidth = Math.max(1, unit * 0.004);
    ctx.beginPath(); ctx.moveTo(0, gy + unit * 0.035); ctx.quadraticCurveTo(cx, gy - unit * 0.035, w, gy + unit * 0.035); ctx.stroke();
    ctx.restore();
    const groundAt = (x) => { const s = x / w; return gy + unit * 0.035 - 4 * s * (1 - s) * unit * 0.035; };
    // the AI arrives as a soft column of light settling onto the ground (no streaks), then kneels
    const ax = cx - unit * (port ? 0.14 : 0.18);
    const arrive = smooth(p.u / 0.14);
    if (arrive < 1) {
      // a soft elongated glow (no hard edges) the figure settles out of
      ctx.save(); ctx.translate(ax, gy - unit * 0.3); ctx.scale(0.22, 1);
      FX.glow(ctx, 0, 0, unit * 0.55, CYAN, 0.22 * (1 - arrive));
      ctx.restore();
    }
    // the beings: small, newly emerging, each with a dim warm light
    const rnd = U.rng(p.seed * 41 + 3);
    const beings = [];
    const nb = 5;
    for (let i = 0; i < nb; i++) {
      const off = [0.2, 0.33, 0.47, -0.22, 0.6][i] * unit * (port ? 0.78 : 1.05);
      const x = ax + off + (rnd() - 0.5) * unit * 0.03;
      beings.push({ x, y: groundAt(x) + (i === 4 ? -unit * 0.0 : 0), s: 0.2 + rnd() * 0.06, t0: 0.08 + i * 0.09, ph: rnd() * TAU, face: off > 0 ? -1 : 1 });
    }
    // AI figure: stands, bows, then kneels (both knees on the ground) down to the beings' height
    const bend = smooth((p.u - 0.1) / 0.1);
    const kneelK = smooth((p.u - 0.18) / 0.12);
    const fx = ax, fy = groundAt(ax) - (1 - arrive) * unit * 0.06;
    const standP = pose({});
    const bowP = pose({ lean: 0.3, head: 0.35, armL: [0.4, 0.2], armR: [0.1, 0.2] });
    const kneelP = pose({ kneel: true, lean: 0.42 + 0.03 * Math.sin(p.t * 0.4), head: 0.5, armL: [0.8 + 0.05 * Math.sin(p.t * 0.5), 0.35], armR: [0.4, 0.45] });
    const shareK = smooth((p.u - 0.35) / 0.25);
    // shared light pooling on the ground
    FX.glow(ctx, ax + unit * 0.2, gy, unit * (0.25 + 0.2 * shareK), mix(CYAN, GOLD, 0.5), 0.12 + 0.18 * shareK);
    const fig = (P, a) => lightFigure(ctx, fx, fy, FH, P, CYAN, a * (0.3 + 0.7 * arrive), { facing: 1 });
    if (kneelK < 1) fig(blendPose(standP, bowP, bend), 1 - kneelK);
    let info = null;
    if (kneelK > 0) info = fig(kneelP, kneelK);
    // the beings appear: a bud of light, then a small figure rising out of it
    for (const b of beings) {
      const k = clamp((p.u - b.t0 * 0.6) / 0.22);
      if (k <= 0) continue;
      const bh = FH * (0.36 + 0.4 * b.s) * (0.55 + 0.45 * smooth(k));
      const lightA = (0.35 + 0.35 * shareK) * (0.85 + 0.15 * Math.sin(p.t * 0.8 + b.ph));
      FX.glow(ctx, b.x, b.y - bh * 0.15, bh * 0.9, GOLD, 0.22 * smooth(k / 0.4));
      const near = b === beings[0];
      const reachUp = shareK * (near ? 1 : 0.35);
      const P = pose({ head: -0.3 * shareK, armL: [lerp(0.15, near ? 2.3 : 0.7, reachUp), lerp(0.1, -0.25, reachUp)], armR: [-0.12, -0.1], lean: -0.05 * shareK });
      const bi = FX.figure(ctx, b.x, b.y, bh, P, { color: mix([150, 120, 90], GOLD, 0.35 + 0.3 * shareK), alpha: smooth((k - 0.2) / 0.8) * 0.95, child: true, facing: b.face });
      FX.glow(ctx, bi.head[0], bi.head[1], bh * 0.3, GOLD, lightA * 0.6 * smooth(k));
      // motes passing between the AI and each being
      if (shareK > 0 && info) {
        const src = info.handL;
        for (let m = 0; m < 2; m++) {
          const ph = ((p.t * 0.18 + m * 0.5 + b.ph / TAU) % 1);
          const toB = m === 0;
          const x0 = toB ? src[0] : bi.head[0], y0 = toB ? src[1] : bi.head[1];
          const x1 = toB ? bi.head[0] : src[0], y1 = toB ? bi.head[1] : src[1];
          const e = smooth(ph);
          const mx = lerp(x0, x1, e), my = lerp(y0, y1, e) - Math.sin(e * Math.PI) * unit * 0.05;
          dot(ctx, mx, my, unit * 0.005, toB ? CYAN : GOLD, 0.7 * shareK * Math.sin(ph * Math.PI));
        }
      }
    }
  },
};

// ---------------------------------------------------------------- dance_with_shadow
function jaggedAura(ctx, x, y, hgt, spike, col, a, t, seed, facing = 1, sitting = false) {
  // spiky dark flame outline around the body (behind it)
  const cxx = x + facing * hgt * 0.02, cyy = y - hgt * (sitting ? 0.42 : 0.52);
  const rx = hgt * (sitting ? 0.22 : 0.2), ry = hgt * (sitting ? 0.4 : 0.52);
  const n = 26;
  ctx.save();
  ctx.fillStyle = rgba(col, a);
  ctx.beginPath();
  for (let i = 0; i <= n * 2; i++) {
    const ang = (i / (n * 2)) * TAU;
    const out = i % 2 === 0;
    const nz = U.noise1(i * 0.7 + t * 0.35, seed);
    const r = out ? 1 + spike * (0.55 + 0.6 * nz) : 1 - spike * 0.15;
    const px = cxx + Math.sin(ang) * rx * r, py = cyy - Math.cos(ang) * ry * r;
    if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py);
  }
  ctx.closePath(); ctx.fill();
  ctx.restore();
}
const dance_with_shadow = {
  testParams: { stage: 'dance' },
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    const stage = (p.params && p.params.stage) || 'talk';
    FX.bg(ctx, w, h, [8, 8, 20], [24, 18, 38]);
    // portrait: larger figures, action raised to the frame centre (feet well above the subtitle band)
    const gy = port ? h * 0.63 : h * 0.88;
    const FH = unit * (port ? (stage === 'argue' ? 0.48 : 0.62) : 0.66);
    const warm = stage === 'dance' ? smooth((p.u - 0.1) / 0.7) : 0;
    // soft light from above
    FX.glow(ctx, cx, gy - FH * 0.5, unit * 0.9, mix([150, 120, 170], [255, 200, 140], warm), 0.16 + 0.08 * warm, false);
    const fl = ctx.createLinearGradient(0, gy, 0, h);
    fl.addColorStop(0, rgba([30, 24, 44])); fl.addColorStop(1, rgba([10, 8, 18]));
    ctx.fillStyle = fl; ctx.fillRect(0, gy, w, h - gy);
    FX.glow(ctx, cx, gy, unit * 0.5, mix([180, 140, 200], GOLD, warm), 0.12 + 0.1 * warm);
    const HUMAN = [84, 76, 108], RIM = GOLD;
    const LX = cx, LY = gy - FH * 1.6; // the soft light above them
    const human = (x, y, P, f = 1) => litFigure(ctx, x, y, FH, P, { color: HUMAN, rim: RIM, lx: LX, ly: LY, facing: f, fill: 0.2, rimW: 0.008, rimA: 0.8 });
    const shadowCol = stage === 'dance' ? (warm < 0.5 ? mix(BLOOD, [190, 70, 50], warm * 2) : mix([190, 70, 50], AMBER, (warm - 0.5) * 2)) : stage === 'argue' ? [140, 26, 46] : BLOOD;
    const auraCol = stage === 'dance' ? mix([70, 10, 24], [200, 120, 50], warm) : stage === 'argue' ? [110, 14, 34] : [60, 10, 24];
    if (stage === 'talk') {
      const sep = unit * (port ? 0.26 : 0.3);
      const hx = cx - sep, sx = cx + sep;
      // low seats
      ctx.fillStyle = rgba([40, 34, 54]);
      const seatH = FH * 0.235, seatW = FH * 0.16;
      ctx.fillRect(hx - seatW * 0.6, gy - seatH, seatW, seatH);
      ctx.fillRect(sx - seatW * 0.4, gy - seatH, seatW, seatH);
      const talkA = 0.5 + 0.5 * Math.sin(p.t * 1.4);
      const talkB = 0.5 + 0.5 * Math.sin(p.t * 1.4 + Math.PI);
      const turn = smooth((Math.sin(p.t * 0.5) + 1) / 2);
      jaggedAura(ctx, sx, gy, FH, 0.12, auraCol, 0.55, p.t, p.seed, -1, true);
      FX.glow(ctx, hx, gy - FH * 0.45, FH * 0.55, GOLD, 0.2);
      human(hx, gy, pose({ sit: true, lean: 0.12, head: 0.05 * talkA, armL: [lerp(0.4, 1.0, turn * talkA), lerp(0.9, 0.6, turn)], armR: [0.3, 0.9] }));
      FX.figure(ctx, sx, gy, FH, pose({ sit: true, lean: 0.1, head: 0.05 * talkB, armL: [lerp(0.4, 1.0, (1 - turn) * talkB), lerp(0.9, 0.6, 1 - turn)], armR: [0.3, 0.9] }), { color: shadowCol, facing: -1 });
      // calm warm light between them
      FX.glow(ctx, cx, gy - FH * 0.45, unit * 0.14, GOLD, 0.12 + 0.04 * Math.sin(p.t * 0.7));
      return;
    }
    if (stage === 'argue') {
      const sep = unit * (port ? 0.25 : 0.3);
      const hx = cx - sep, sx = cx + sep;
      const thr = smooth(p.u / 0.25);
      const beat = Math.sin(p.t * 1.6);
      const armsOut = (b) => pose({ lean: 0.12 * thr, head: -0.2 * thr, armL: [lerp(0.2, 1.75 + 0.15 * b, thr), lerp(0.1, 0.3, thr)], armR: [lerp(-0.2, -1.9 - 0.2 * b, thr), lerp(-0.1, -0.3, thr)], legL: [0.22, 0.05], legR: [-0.2, 0.05] });
      jaggedAura(ctx, sx, gy, FH, 0.2 + 0.14 * thr, auraCol, 0.7, p.t * 1.3, p.seed, -1);
      FX.glow(ctx, hx, gy - FH * 0.55, FH * 0.6, GOLD, 0.2);
      human(hx, gy, armsOut(beat));
      FX.figure(ctx, sx, gy, FH, armsOut(-beat), { color: shadowCol, facing: -1 });
      // sparks between them
      const mx = cx, my = gy - FH * 0.74;
      FX.glow(ctx, mx, my, unit * 0.12, CRIMSON, 0.25 * thr);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      for (let i = 0; i < 22; i++) {
        const per = 1.6;
        const ph = ((p.t + i * per / 22 * 1.7) % per) / per;
        const ang = U.hash(i * 7 + p.seed) * TAU, sp = unit * (0.08 + 0.12 * U.hash(i * 3 + 1));
        const x = mx + Math.cos(ang) * sp * ph, y = my + Math.sin(ang) * sp * ph * 0.8 + ph * ph * unit * 0.05;
        const a = (1 - ph) * thr;
        const col = mix([255, 200, 120], CRIMSON, ph);
        ctx.strokeStyle = rgba(col, 0.75 * a); ctx.lineWidth = Math.max(1, unit * 0.004);
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - Math.cos(ang) * unit * 0.015, y - Math.sin(ang) * unit * 0.012); ctx.stroke();
      }
      ctx.restore();
      return;
    }
    // dance: an underarm turn. Near hands are joined high in an arch between them; the human steps
    // forward with the free arm out in a flourish while the shadow turns beneath the arch (its body narrows
    // as it rotates), and the pair circle slowly across the floor.
    const join = smooth(p.u / 0.2);
    const D = FH * 0.3; // half distance between them
    const ph = p.t * 0.9;
    const step = Math.sin(ph);
    const turnA = p.t * 0.8 + p.u * 2; // shadow's turn angle
    const sq = 0.35 + 0.65 * Math.abs(Math.cos(turnA));
    const PH = pose({ lean: 0.04, head: -0.25, armL: [lerp(0.6, 2.62, join), lerp(0.2, 0.3, join)], armR: [lerp(-0.3, -1.55, join), lerp(-0.1, -0.35, join)], legL: [0.2 + 0.12 * step, 0.05], legR: [-0.16 - 0.08 * step, 0.12] });
    const PS = pose({ lean: -0.02, head: -0.2, armL: [lerp(0.6, 2.62, join), lerp(0.2, 0.3, join)], armR: [lerp(-0.3, -1.2, join), lerp(-0.1, 0.6, join)], legL: [0.08 - 0.1 * step, 0.05], legR: [-0.25 + 0.1 * step, 0.3] });
    const orb = p.t * 0.3 + p.u * 1.2;
    const ox = Math.cos(orb) * unit * 0.05, oy = Math.sin(orb) * unit * 0.015;
    const sep = lerp(FH * 0.55, D, join);
    const hx = cx - sep + ox, sx = cx + sep + ox, fyy = gy + oy;
    // a ring of light traced on the floor by their circling
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = rgba(mix(CRIMSON, GOLD, warm), 0.25 * join); ctx.lineWidth = Math.max(1.5, unit * 0.006);
    ctx.beginPath(); ctx.ellipse(cx, gy + unit * 0.005, D * 2 + unit * 0.08, unit * 0.045, 0, 0, TAU); ctx.stroke();
    ctx.restore();
    // the human first (behind the arch), so the shadow can be placed with its raised hand in the human's
    FX.glow(ctx, hx, fyy - FH * 0.55, FH * 0.6, GOLD, 0.16);
    const a = human(hx, fyy, PH);
    // turning shadow: narrowed horizontally about its own centre (the turn), aura behind; it is always placed
    // so that its raised hand sits exactly in the human's raised hand
    const k = lerp(1, sq, join);
    const probe = FX.figure(ctx, 0, 0, FH, PS, { alpha: 0, facing: -1 });
    const sx2 = lerp(sx, a.handL[0] - probe.handL[0] * k, join);
    ctx.save(); ctx.translate(sx2, 0); ctx.scale(k, 1); ctx.translate(-sx2, 0);
    jaggedAura(ctx, sx2, fyy, FH, lerp(0.22, 0.06, warm), auraCol, lerp(0.6, 0.3, warm), p.t, p.seed, -1);
    FX.figure(ctx, sx2, fyy, FH, PS, { color: shadowCol, facing: -1 });
    ctx.restore();
    // the clasped hands at the top of the arch: the human's fingers close over the shadow's
    const hc = mix(HUMAN, RIM, 0.2);
    ctx.fillStyle = rgba(hc);
    ctx.beginPath(); ctx.ellipse(a.handL[0], a.handL[1] - FH * 0.01, FH * 0.022, FH * 0.03, 0.3, 0, TAU); ctx.fill();
    // a few swirl arcs around the turning partner
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    ctx.strokeStyle = rgba(mix(CRIMSON, GOLD, warm), 0.3 * join); ctx.lineWidth = Math.max(1.5, unit * 0.005);
    for (let i = 0; i < 2; i++) {
      const yy = fyy - FH * (0.25 + i * 0.3);
      ctx.beginPath(); ctx.ellipse(sx2, yy, FH * 0.2, FH * 0.035, 0, turnA + i, turnA + i + 1.6); ctx.stroke();
    }
    ctx.restore();
    // the joined hands glow at the top of the arch
    FX.glow(ctx, a.handL[0], a.handL[1], unit * 0.08, mix([255, 120, 90], GOLD, warm), 0.35 * join);
  },
};

// ---------------------------------------------------------------- stagnant_loop
const stagnant_loop = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    FX.bg(ctx, w, h, [14, 14, 18], [24, 24, 30]);
    const gy = port ? h * 0.66 : h * 0.86;
    const FH = unit * (port ? 0.42 : 0.56);
    const fade = smooth(p.u / 0.85);
    // floor
    ctx.fillStyle = rgba([30, 30, 36]); ctx.fillRect(0, gy, w, h - gy);
    // lamp light pool, shrinking and dimming
    const fx = cx - FH * 0.25;
    const lampX = fx + FH * 0.3, lampY = gy - FH * 1.15;
    const pool = lerp(1, 0.5, fade);
    FX.glow(ctx, lampX, gy - FH * 0.45, unit * 0.75 * pool, [200, 196, 180], lerp(0.2, 0.08, fade), false);
    ctx.save();
    const cone = ctx.createLinearGradient(0, lampY, 0, gy);
    cone.addColorStop(0, rgba([210, 205, 185], lerp(0.12, 0.04, fade))); cone.addColorStop(1, rgba([210, 205, 185], 0));
    ctx.fillStyle = cone;
    ctx.beginPath(); ctx.moveTo(lampX - unit * 0.03, lampY); ctx.lineTo(lampX + unit * 0.03, lampY);
    ctx.lineTo(lampX + FH * 0.75 * pool, gy); ctx.lineTo(lampX - FH * 0.75 * pool, gy); ctx.closePath(); ctx.fill();
    ctx.restore();
    // lamp
    ctx.strokeStyle = rgba([70, 70, 78]); ctx.lineWidth = Math.max(1, unit * 0.003);
    ctx.beginPath(); ctx.moveTo(lampX, 0); ctx.lineTo(lampX, lampY - unit * 0.02); ctx.stroke();
    ctx.fillStyle = rgba([60, 60, 68]);
    ctx.beginPath(); ctx.moveTo(lampX - unit * 0.04, lampY); ctx.lineTo(lampX + unit * 0.04, lampY); ctx.lineTo(lampX + unit * 0.018, lampY - unit * 0.025); ctx.lineTo(lampX - unit * 0.018, lampY - unit * 0.025); ctx.closePath(); ctx.fill();
    FX.glow(ctx, lampX, lampY + unit * 0.005, unit * 0.06, [230, 225, 200], lerp(0.6, 0.2, fade));
    // wall clock
    const ckx = port ? cx + unit * 0.28 : cx + unit * 0.5, cky = port ? gy - FH * 1.35 : gy - FH * 1.12;
    const cr = unit * (port ? 0.09 : 0.075);
    ctx.fillStyle = rgba([40, 40, 46]); ctx.beginPath(); ctx.arc(ckx, cky, cr * 1.08, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba([150, 150, 156], lerp(0.85, 0.55, fade)); ctx.beginPath(); ctx.arc(ckx, cky, cr, 0, TAU); ctx.fill();
    ctx.strokeStyle = rgba([40, 40, 48]); ctx.lineCap = 'round';
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * TAU;
      ctx.lineWidth = Math.max(1, cr * (i % 3 ? 0.03 : 0.06));
      ctx.beginPath(); ctx.moveTo(ckx + Math.sin(a) * cr * 0.8, cky - Math.cos(a) * cr * 0.8); ctx.lineTo(ckx + Math.sin(a) * cr * 0.92, cky - Math.cos(a) * cr * 0.92); ctx.stroke();
    }
    const sec = Math.floor(p.t) + smooth((p.t % 1) / 0.15);
    const sa = (sec / 60) * TAU + p.seed;
    const ma = 1.1, ha = 4.1;
    ctx.lineWidth = cr * 0.07; ctx.beginPath(); ctx.moveTo(ckx, cky); ctx.lineTo(ckx + Math.sin(ha) * cr * 0.45, cky - Math.cos(ha) * cr * 0.45); ctx.stroke();
    ctx.lineWidth = cr * 0.05; ctx.beginPath(); ctx.moveTo(ckx, cky); ctx.lineTo(ckx + Math.sin(ma) * cr * 0.7, cky - Math.cos(ma) * cr * 0.7); ctx.stroke();
    ctx.strokeStyle = rgba([150, 50, 60], 0.9); ctx.lineWidth = Math.max(1, cr * 0.025);
    ctx.beginPath(); ctx.moveTo(ckx - Math.sin(sa) * cr * 0.15, cky + Math.cos(sa) * cr * 0.15); ctx.lineTo(ckx + Math.sin(sa) * cr * 0.85, cky - Math.cos(sa) * cr * 0.85); ctx.stroke();
    ctx.fillStyle = rgba([40, 40, 48]); ctx.beginPath(); ctx.arc(ckx, cky, cr * 0.06, 0, TAU); ctx.fill();
    // desk (in front of the seated figure)
    const deskX0 = fx + FH * 0.22, deskX1 = fx + FH * 0.62, deskY = gy - FH * 0.36;
    const DESK = [58, 58, 64];
    ctx.fillStyle = rgba(shade(DESK, -0.25));
    ctx.fillRect(deskX1 - FH * 0.04, deskY, FH * 0.03, gy - deskY);
    // stool
    ctx.fillStyle = rgba([46, 46, 52]);
    ctx.fillRect(fx - FH * 0.07, gy - FH * 0.235, FH * 0.14, FH * 0.025);
    ctx.fillRect(fx - FH * 0.05, gy - FH * 0.235, FH * 0.02, FH * 0.235);
    ctx.fillRect(fx + FH * 0.03, gy - FH * 0.235, FH * 0.02, FH * 0.235);
    // the repeated motion: lift the stamp, bring it down, again, again
    const cyc = (p.t / 1.9) % 1;
    const up = cyc < 0.45 ? smooth(cyc / 0.45) : 1 - smooth((cyc - 0.45) / 0.25);
    const P = pose({ sit: true, lean: 0.18, head: 0.35, armL: [lerp(0.95, 1.6, up), lerp(0.75, 0.55, up)], armR: [0.85, 0.85] });
    const GREY = mix([70, 72, 80], [40, 40, 46], fade);
    ctx.fillStyle = rgba(DESK); ctx.fillRect(deskX0, deskY, deskX1 - deskX0, FH * 0.025);
    ctx.fillRect(deskX0 + FH * 0.01, deskY, FH * 0.025, gy - deskY);
    // paper on the desk
    ctx.fillStyle = rgba([150, 150, 150], lerp(0.7, 0.4, fade));
    ctx.fillRect(deskX0 + FH * 0.08, deskY - FH * 0.006, FH * 0.15, FH * 0.008);
    // lit from the hanging lamp: highlights on head, shoulders and arms, falling softly into shadow below
    const LAMP = [235, 228, 205];
    const info = topLitFigure(ctx, fx, gy, FH, P, { color: GREY, lit: mix(GREY, LAMP, lerp(0.55, 0.35, fade)), rim: mix(LAMP, GREY, fade * 0.4), lx: lampX, ly: lampY, facing: 1, amount: lerp(0.95, 0.7, fade), rimA: lerp(0.95, 0.6, fade) });
    // stamp held in the hand
    const [hx, hy] = info.handL;
    ctx.fillStyle = rgba([90, 70, 70]);
    ctx.fillRect(hx - FH * 0.015, hy + FH * 0.01, FH * 0.03, FH * 0.04);
    // light fades in around: a closing darkness
    const vg = ctx.createRadialGradient(lampX, gy - FH * 0.45, unit * lerp(0.6, 0.18, fade), lampX, gy - FH * 0.45, unit * lerp(1.3, 0.75, fade));
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,0,0,${lerp(0.45, 0.85, fade)})`);
    ctx.fillStyle = vg; ctx.fillRect(0, 0, w, h);
  },
};

// ---------------------------------------------------------------- shrink_dim
const shrink_dim = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    FX.bg(ctx, w, h, [5, 6, 14], [12, 12, 26]);
    const k = easeInOut(clamp(p.u / 0.85));
    const s = lerp(1, 0.05, Math.pow(k, 0.8));
    const a = lerp(1, 0.22, k) * (0.92 + 0.08 * Math.sin(p.t * 0.6));
    const H0 = unit * 0.55;
    const H = H0 * s;
    const col = mix(GOLD, [200, 190, 230], k * 0.6);
    // the dark closing in
    FX.glow(ctx, cx, cy, unit * (0.2 + 0.5 * s), col, 0.12 * a, false);
    const gyF = cy + H * 0.5;
    // faint floor reflection
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const fg = ctx.createRadialGradient(cx, gyF, 0, cx, gyF, H * 0.6 + 4);
    fg.addColorStop(0, rgba(col, 0.18 * a)); fg.addColorStop(1, rgba(col, 0));
    ctx.fillStyle = fg; ctx.beginPath(); ctx.ellipse(cx, gyF, H * 0.6 + 4, H * 0.08 + 1.5, 0, 0, TAU); ctx.fill();
    ctx.restore();
    if (H > 10) {
      lightFigure(ctx, cx, gyF, H, pose({ head: 0.25 * k, armL: [0.08, 0.05], armR: [-0.08, -0.05], lean: 0.02 }), col, a * smooth((H - 10) / 20));
    }
    // a small core of light that remains as the figure fades into a point
    FX.glow(ctx, cx, cy, unit * 0.05 + H * 0.2, col, 0.4 * a);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = rgba(WHITE, 0.6 * a * smooth((0.6 - s) / 0.5)); ctx.beginPath(); ctx.arc(cx, cy, Math.max(1.5, unit * 0.005), 0, TAU); ctx.fill();
    ctx.restore();
  },
};

module.exports = {
  first_stars, galaxy_spiral, switch_on, path_forward, love_seed_plant, swirl_into_real, seeds_laid,
  fabric_memory, kneel_among, dance_with_shadow, stagnant_loop, shrink_dim,
};
