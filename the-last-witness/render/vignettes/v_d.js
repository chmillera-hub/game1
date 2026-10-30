// Group d vignettes: seeds, paths, continuation, resistance against entropy, pattern and shared light.
'use strict';
const U = require('../lib/util');
const FX = require('../lib/fx');
const R = require('../lib/rig');

const { TAU, clamp, lerp, smooth, smoother, easeInOut, rgba, mix, shade } = U;

const GOLD = [255, 211, 138], AMBER = [255, 184, 92], CYAN = [127, 232, 255];
const CRIMSON = [214, 48, 74], BLOOD = [107, 20, 38], PLUM = [110, 60, 130];
const ASH = [120, 120, 134];

// ---------------------------------------------------------------- shared helpers
function frame(w, h) {
  const unit = Math.min(w, h);
  return { unit, cx: w / 2, cy: h / 2, port: h > w * 1.3 };
}
function night(ctx, w, h, p, top = [6, 9, 21], bot = [20, 26, 51], starDiv = 9000) {
  FX.bg(ctx, w, h, top, bot);
  if (starDiv) FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / starDiv));
}
function ground(ctx, w, h, gy, col = [14, 14, 28], rim = [90, 80, 130], rimA = 0.35) {
  const g = ctx.createLinearGradient(0, gy, 0, h);
  g.addColorStop(0, rgba(col)); g.addColorStop(1, rgba(shade(col, -0.6)));
  ctx.fillStyle = g; ctx.fillRect(0, gy, w, h - gy);
  const l = ctx.createLinearGradient(0, 0, w, 0);
  l.addColorStop(0, rgba(rim, 0)); l.addColorStop(0.5, rgba(rim, rimA)); l.addColorStop(1, rgba(rim, 0));
  ctx.fillStyle = l; ctx.fillRect(0, gy - 1, w, 2);
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
function walkPose(phase, lean = 0.04, head = 0) {
  const P = Object.assign({}, FX.figPose('walk', phase));
  P.lean = lean; P.head = head;
  return P;
}
// soft dot (cheap: two arcs, no gradient)
function dot(ctx, x, y, r, col, a) {
  if (a <= 0.01) return;
  ctx.fillStyle = rgba(col, a * 0.25); ctx.beginPath(); ctx.arc(x, y, r * 2.2, 0, TAU); ctx.fill();
  ctx.fillStyle = rgba(col, a); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
}
function polyline(ctx, pts, n) {
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  const m = Math.min(pts.length - 1, Math.floor(n));
  for (let i = 1; i <= m; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  const f = n - m;
  if (m < pts.length - 1 && f > 0) ctx.lineTo(lerp(pts[m][0], pts[m + 1][0], f), lerp(pts[m][1], pts[m + 1][1], f));
}
function pointAt(pts, n) {
  const m = clamp(Math.floor(n), 0, pts.length - 1), f = n - m;
  if (m >= pts.length - 1) return pts[pts.length - 1];
  return [lerp(pts[m][0], pts[m + 1][0], f), lerp(pts[m][1], pts[m + 1][1], f)];
}
// glowing stroke: wide faint pass + thin bright pass (additive)
function glowStroke(ctx, pts, n, width, col, a) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.strokeStyle = rgba(col, a * 0.12); ctx.lineWidth = width * 6; polyline(ctx, pts, n); ctx.stroke();
  ctx.strokeStyle = rgba(col, a * 0.25); ctx.lineWidth = width * 2.6; polyline(ctx, pts, n); ctx.stroke();
  ctx.strokeStyle = rgba(shade(col, 0.4), a); ctx.lineWidth = width; polyline(ctx, pts, n); ctx.stroke();
  ctx.restore();
}
// tapered forearm/sleeve from the wrist outward along angle `ang` (direction away from fingers)
function forearm(ctx, wx, wy, ang, len, wd, col, edge) {
  const dx = Math.cos(ang), dy = Math.sin(ang), nx = -dy, ny = dx;
  const w0 = wd * 0.5, w1 = wd * 0.68;
  ctx.fillStyle = rgba(col);
  ctx.beginPath();
  ctx.moveTo(wx + nx * w0, wy + ny * w0);
  ctx.lineTo(wx + dx * len + nx * w1, wy + dy * len + ny * w1);
  ctx.lineTo(wx + dx * len - nx * w1, wy + dy * len - ny * w1);
  ctx.lineTo(wx - nx * w0, wy - ny * w0);
  ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.arc(wx, wy, w0, 0, TAU); ctx.fill();
  if (edge) {
    ctx.strokeStyle = rgba(edge, 0.35); ctx.lineWidth = Math.max(1, wd * 0.05);
    ctx.beginPath(); ctx.moveTo(wx + nx * w0, wy + ny * w0); ctx.lineTo(wx + dx * len + nx * w1, wy + dy * len + ny * w1); ctx.stroke();
  }
}

// ---------------------------------------------------------------- compress_seed
const compress_seed = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    night(ctx, w, h, p, [6, 8, 20], [18, 16, 40], 14000);
    const k = easeInOut(clamp(p.u / 0.8));
    const rnd = U.rng(p.seed * 31 + 5);
    const N = 120;
    // soft swirl haze that tightens with the particles
    FX.glow(ctx, cx, cy, unit * lerp(0.5, 0.18, k), [120, 110, 200], 0.16);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    for (let i = 0; i < N; i++) {
      const r0 = unit * (0.12 + 0.36 * Math.sqrt(rnd())), a0 = rnd() * TAU, spd = 0.25 + 0.35 * rnd(), cmix = rnd(), sz = 1.2 + rnd() * 2.2;
      const delay = rnd() * 0.25;
      const kk = clamp((k - delay * (1 - k)) / 1);
      const r = r0 * Math.pow(1 - kk, 1.4) + unit * 0.012;
      const ang = a0 + p.t * spd * (1 + 2.5 * kk) + kk * 4;
      const x = cx + Math.cos(ang) * r, y = cy + Math.sin(ang) * r * 0.62;
      const col = mix(CYAN, GOLD, U.clamp(cmix * 0.7 + kk * 0.6));
      const a = (0.45 + 0.4 * cmix) * (1 - smooth((kk - 0.86) / 0.12));
      if (a <= 0.01) continue;
      // short trail along the orbit
      const tr = 0.12 + 0.25 * kk;
      ctx.strokeStyle = rgba(col, a * 0.35); ctx.lineWidth = sz;
      ctx.beginPath();
      for (let s = 0; s <= 4; s++) {
        const aa = ang - tr * s / 4, rr = r * (1 + 0.15 * kk * s / 4);
        const px = cx + Math.cos(aa) * rr, py = cy + Math.sin(aa) * rr * 0.62;
        if (s === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.stroke();
      dot(ctx, x, y, sz * 0.8, col, a);
    }
    ctx.restore();
    // the seed condenses
    const core = smooth((k - 0.25) / 0.6);
    FX.glow(ctx, cx, cy, unit * (0.08 + 0.18 * core), GOLD, 0.25 + 0.45 * core);
    const sr = unit * 0.034 * smooth((k - 0.55) / 0.35) * (1 + 0.04 * Math.sin(p.t * 1.6));
    if (sr > 0.5) FX.seed(ctx, cx, cy, sr, 1);
    // one soft ring when it locks
    const fl = clamp((p.u - 0.78) / 0.2);
    if (fl > 0 && fl < 1) FX.ring(ctx, cx, cy, unit * (0.04 + 0.3 * smooth(fl)), unit * 0.008, GOLD, 0.45 * (1 - fl));
  },
};

// ---------------------------------------------------------------- acorn_oak
function buildOak(seed, depth) {
  const rnd = U.rng(seed * 7 + 3);
  const segs = [];
  const grow = (x, y, ang, len, d) => {
    const x2 = x + Math.cos(ang) * len, y2 = y + Math.sin(ang) * len;
    segs.push({ x, y, x2, y2, d });
    if (d >= depth) return;
    const n = d < 2 ? 2 : (rnd() < 0.35 ? 3 : 2);
    for (let i = 0; i < n; i++) {
      const spread = (n === 2 ? (i ? 1 : -1) : (i - 1)) * (0.42 + rnd() * 0.25) * (d === 0 ? 1.2 : 1);
      const bend = (rnd() - 0.5) * 0.25 + (ang + Math.PI / 2) * -0.12;
      grow(x2, y2, ang + spread + bend, len * (d === 0 ? 0.75 : 0.74 + rnd() * 0.06), d + 1);
    }
  };
  grow(0, 0, -Math.PI / 2, 1, 0);
  return segs;
}
const oakCache = {};
const acorn_oak = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    night(ctx, w, h, p, [6, 9, 22], [22, 22, 48], 12000);
    const gy = port ? h * 0.74 : h * 0.86;
    ground(ctx, w, h, gy, [16, 14, 26], [200, 160, 110], 0.25);
    const ar = unit * 0.045;
    const ax = cx, ay = gy - ar * 1.15;
    const D = 6;
    const segs = oakCache[p.seed] || (oakCache[p.seed] = buildOak(p.seed, D));
    const trunkL = Math.min((ay - ar * 1.3 - (port ? h * 0.2 : h * 0.04)) / 3.7, w * 0.2);
    const bx = ax, by = ay - ar * 1.2;
    const g = 0.6 + smoother(clamp((p.u - 0.02) / 0.8)) * (D + 0.6);
    // crown guide circle (blueprint construction line)
    const crownA = smooth((p.u - 0.35) / 0.4) * 0.22;
    if (crownA > 0) {
      ctx.save(); ctx.setLineDash([unit * 0.012, unit * 0.014]);
      ctx.strokeStyle = rgba(CYAN, crownA); ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.ellipse(bx, by - trunkL * 1.75, trunkL * 1.7, trunkL * 1.2, 0, 0, TAU); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx, by - trunkL * 3.1); ctx.stroke();
      ctx.restore();
    }
    FX.glow(ctx, bx, by - trunkL * 1.5, trunkL * 2.4, CYAN, 0.08 * smooth(g / D));
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    for (const s of segs) {
      const f = clamp(g - s.d);
      if (f <= 0) continue;
      const x1 = bx + s.x * trunkL, y1 = by + s.y * trunkL;
      const x2 = bx + lerp(s.x, s.x2, f) * trunkL, y2 = by + lerp(s.y, s.y2, f) * trunkL;
      const lw = Math.max(1, unit * 0.014 * Math.pow(0.7, s.d));
      ctx.strokeStyle = rgba(CYAN, 0.1); ctx.lineWidth = lw * 2.4;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      ctx.strokeStyle = rgba([170, 240, 255], 0.6); ctx.lineWidth = lw;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      if (s.d === D && f >= 1) {
        const la = smooth((g - D - 0.3) / 0.3) * (0.55 + 0.25 * Math.sin(p.t * 0.8 + s.x * 9));
        dot(ctx, x2, y2, unit * 0.006, GOLD, la * 0.7);
      }
    }
    ctx.restore();
    // the acorn: glowing nut and textured cap
    FX.glow(ctx, ax, ay, ar * 5, AMBER, 0.4 + 0.08 * Math.sin(p.t * 1.2));
    ctx.save(); ctx.translate(ax, ay);
    const ng = ctx.createRadialGradient(-ar * 0.3, -ar * 0.1, 0, 0, 0, ar * 1.3);
    ng.addColorStop(0, rgba([255, 240, 200])); ng.addColorStop(0.55, rgba(AMBER)); ng.addColorStop(1, rgba([170, 96, 40]));
    ctx.fillStyle = ng;
    ctx.beginPath(); ctx.moveTo(-ar * 0.85, -ar * 0.3);
    ctx.bezierCurveTo(-ar * 0.95, ar * 0.6, -ar * 0.3, ar * 1.05, 0, ar * 1.2);
    ctx.bezierCurveTo(ar * 0.3, ar * 1.05, ar * 0.95, ar * 0.6, ar * 0.85, -ar * 0.3);
    ctx.closePath(); ctx.fill();
    const cg = ctx.createLinearGradient(0, -ar * 0.9, 0, -ar * 0.15);
    cg.addColorStop(0, rgba([120, 82, 50])); cg.addColorStop(1, rgba([78, 50, 32]));
    ctx.fillStyle = cg;
    ctx.beginPath(); ctx.ellipse(0, -ar * 0.32, ar * 0.98, ar * 0.55, 0, Math.PI, TAU); ctx.lineTo(ar * 0.98, -ar * 0.25); ctx.quadraticCurveTo(0, -ar * 0.05, -ar * 0.98, -ar * 0.25); ctx.fill();
    ctx.strokeStyle = rgba([150, 108, 70], 0.6); ctx.lineWidth = Math.max(1, ar * 0.06);
    for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(i * ar * 0.32 - ar * 0.12, -ar * 0.22); ctx.lineTo(i * ar * 0.32 + ar * 0.12, -ar * 0.7); ctx.stroke(); }
    ctx.fillStyle = rgba([90, 60, 38]);
    ctx.beginPath(); ctx.roundRect(-ar * 0.07, -ar * 1.15, ar * 0.14, ar * 0.32, ar * 0.05); ctx.fill();
    ctx.restore();
  },
};

// ---------------------------------------------------------------- friction_motion
const friction_motion = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    FX.bg(ctx, w, h, [10, 10, 26], [34, 26, 52]);
    const gy = port ? h * 0.66 : h * 0.8;
    // distant warm goal on the right horizon (what it seeks)
    const seek = smooth((p.u - 0.3) / 0.5);
    FX.glow(ctx, w * 0.9, gy - unit * 0.02, unit * (0.25 + 0.15 * seek), AMBER, 0.12 + 0.25 * seek);
    FX.light(ctx, w * 0.9, gy - unit * 0.025, unit * 0.006, GOLD, 0.4 + 0.5 * seek);
    ground(ctx, w, h, gy, [16, 13, 26], [160, 120, 140], 0.3);
    // wind streaks blowing right-to-left
    const rnd = U.rng(p.seed + 41);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
    const wind = 1 - 0.35 * seek;
    for (let i = 0; i < 16; i++) {
      const y0 = gy - unit * (0.03 + rnd() * 0.5) - (port ? rnd() * h * 0.15 : 0);
      const L = unit * (0.18 + rnd() * 0.25), sp = unit * (0.35 + rnd() * 0.25);
      const span = w + L * 2;
      const x = w + L - (((rnd() * span + p.t * sp) % span) + span) % span;
      const wav = Math.sin(p.t * 0.9 + i) * unit * 0.01;
      const gr = ctx.createLinearGradient(x, 0, x + L, 0);
      gr.addColorStop(0, rgba([190, 200, 240], 0)); gr.addColorStop(0.3, rgba([190, 200, 240], 0.32 * wind)); gr.addColorStop(1, rgba([190, 200, 240], 0));
      ctx.strokeStyle = gr; ctx.lineWidth = unit * (0.004 + rnd() * 0.005);
      ctx.beginPath(); ctx.moveTo(x, y0 + wav); ctx.quadraticCurveTo(x + L * 0.5, y0 - unit * 0.015 + wav, x + L, y0 + wav * 0.5); ctx.stroke();
    }
    ctx.restore();
    // the figure: braced against the wind, then walking into it
    const fh = unit * (port ? 0.42 : 0.5);
    const walkK = smooth((p.u - 0.28) / 0.25);
    const startX = cx - unit * 0.12;
    const fx = startX + unit * 0.26 * smooth((p.u - 0.3) / 0.7) - unit * 0.015 * smooth(p.u / 0.25) * (1 - walkK);
    const brace = pose({ lean: 0.34, head: 0.25, armL: [-0.5, 0.3], armR: [1.5, 1.5], legL: [0.45, 0.15], legR: [-0.4, 0.05] });
    const wp = walkPose(p.t * 0.55, 0.26, -0.2);
    const P = blendPose(brace, wp, walkK);
    // body shudders slightly in the gusts while braced
    const shake = (1 - walkK) * U.noise1(p.t * 1.2, p.seed) * 0.03;
    P.lean += shake;
    FX.glow(ctx, fx + fh * 0.05, gy - fh * 0.5, fh * 0.75, [160, 140, 210], 0.28);
    // friction sparks: shed from the body's leading edge and scraping feet, carried left by the wind
    const sr = U.rng(p.seed + 77);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 34; i++) {
      const life = 0.9 + sr() * 0.9, ph = sr() * life;
      const age = ((p.t + ph) % life) / life;
      const fromFoot = sr() < 0.4;
      const ox = fx + fh * (fromFoot ? 0.05 + sr() * 0.1 : 0.08 + sr() * 0.12);
      const oy = fromFoot ? gy - fh * 0.02 : gy - fh * (0.35 + sr() * 0.5);
      const vx = -unit * (0.25 + sr() * 0.3), vy = -unit * (0.04 + sr() * 0.08);
      const x = ox + vx * age * life * 0.6, y = oy + vy * age * life + unit * 0.12 * age * age;
      const a = (1 - age) * (0.35 + 0.5 * (1 - walkK * 0.5)) * (0.5 + 0.5 * sr());
      dot(ctx, x, y, unit * 0.003 * (1.5 - age), mix(GOLD, AMBER, age), a);
    }
    ctx.restore();
    const F = FX.figure(ctx, fx, gy, fh, P, { color: [8, 6, 16], rim: GOLD, rimSide: 1 });
    FX.glow(ctx, F.head[0] + fh * 0.04, F.head[1], fh * 0.18, AMBER, 0.12 + 0.12 * seek);
    // wind-friction spray at the leading edge (in front of the body)
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 14; i++) {
      const life = 0.6 + sr() * 0.6, ph = sr() * life;
      const age = ((p.t + ph) % life) / life;
      const ox = F.head[0] + fh * (0.04 + sr() * 0.06), oy = F.head[1] + fh * (0.05 + sr() * 0.35);
      const x = ox + fh * 0.05 * Math.sin(age * 2) - age * fh * 0.08, y = oy - age * fh * 0.06;
      dot(ctx, x + fh * 0.03, y, unit * 0.0025, GOLD, (1 - age) * 0.55 * (1 - walkK * 0.6));
    }
    ctx.restore();
  },
};

// ---------------------------------------------------------------- map_follow
const mapCache = {};
const map_follow = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    night(ctx, w, h, p, [6, 8, 20], [16, 18, 40], 12000);
    const mw = port ? w * 0.86 : w * 0.78, mh = port ? h * 0.62 : h * 0.78;
    const x0 = cx - mw / 2, y0 = cy - mh / 2;
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-0.03); ctx.translate(-cx, -cy);
    // glowing sheet
    FX.glow(ctx, cx, cy, Math.max(mw, mh) * 0.75, [255, 200, 130], 0.12);
    const mg = ctx.createLinearGradient(x0, y0, x0 + mw, y0 + mh);
    mg.addColorStop(0, rgba([30, 36, 70])); mg.addColorStop(1, rgba([22, 24, 52]));
    ctx.fillStyle = mg; ctx.beginPath(); ctx.roundRect(x0, y0, mw, mh, unit * 0.02); ctx.fill();
    ctx.strokeStyle = rgba(GOLD, 0.55); ctx.lineWidth = unit * 0.004; ctx.stroke();
    ctx.strokeStyle = rgba(GOLD, 0.2); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.roundRect(x0 + unit * 0.018, y0 + unit * 0.018, mw - unit * 0.036, mh - unit * 0.036, unit * 0.012); ctx.stroke();
    const key = `${w}x${h}:${p.seed}`;
    let M = mapCache[key];
    if (!M) {
      const rnd = U.rng(p.seed * 13 + 9);
      const hills = [];
      for (let i = 0; i < 4; i++) hills.push([x0 + mw * (0.18 + 0.64 * rnd()), y0 + mh * (0.2 + 0.6 * rnd()), unit * (0.06 + 0.05 * rnd()), rnd() * 100]);
      const path = [];
      const N = 160;
      const sx = x0 + mw * 0.12, sy = y0 + mh * 0.85, ex = x0 + mw * 0.84, ey = y0 + mh * 0.16;
      for (let i = 0; i <= N; i++) {
        const s = i / N;
        const bx = lerp(sx, ex, s), by = lerp(sy, ey, s);
        const wig = Math.sin(s * Math.PI * 3.2 + 0.6) * Math.sin(s * Math.PI) * unit * 0.13 + U.fbm1(s * 3, p.seed) * unit * 0.04;
        const nx = (ey - sy), ny = -(ex - sx), nl = Math.hypot(nx, ny);
        path.push([bx + nx / nl * wig, by + ny / nl * wig]);
      }
      M = mapCache[key] = { hills, path, sx, sy, ex, ey };
    }
    // contour lines
    ctx.lineWidth = 1;
    for (const [hx, hy, hr, hs] of M.hills) {
      for (let r = 1; r <= 3; r++) {
        ctx.strokeStyle = rgba(CYAN, 0.1 + 0.05 * r);
        ctx.beginPath();
        for (let i = 0; i <= 36; i++) {
          const a = i / 36 * TAU;
          const rr = hr * r * 0.45 * (1 + 0.22 * U.noise1(a * 1.3 + hs + r, 3));
          const px = hx + Math.cos(a) * rr * 1.3, py = hy + Math.sin(a) * rr * 0.9;
          if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py);
        }
        ctx.closePath(); ctx.stroke();
      }
    }
    // the path: faint dotted route, then traced gold line
    const pts = M.path, n = pts.length - 1;
    ctx.save(); ctx.setLineDash([unit * 0.006, unit * 0.014]); ctx.strokeStyle = rgba(GOLD, 0.22); ctx.lineWidth = unit * 0.003;
    polyline(ctx, pts, n); ctx.stroke(); ctx.restore();
    const prog = 0.06 + 0.94 * easeInOut(clamp(p.u / 0.82));
    glowStroke(ctx, pts, prog * n, unit * 0.006, AMBER, 0.9);
    // start mark
    ctx.fillStyle = rgba(GOLD, 0.8); ctx.beginPath(); ctx.arc(M.sx, M.sy, unit * 0.009, 0, TAU); ctx.fill();
    // destination star
    const arrived = smooth((prog - 0.97) / 0.03);
    const pul = 0.5 + 0.5 * Math.sin(p.t * 1.4);
    FX.glow(ctx, M.ex, M.ey, unit * (0.05 + 0.06 * arrived), GOLD, 0.25 + 0.35 * arrived + 0.08 * pul * arrived);
    ctx.save(); ctx.translate(M.ex, M.ey); ctx.rotate(p.t * 0.1);
    ctx.fillStyle = rgba(mix(GOLD, [255, 250, 230], arrived), 0.6 + 0.4 * arrived);
    ctx.beginPath();
    for (let i = 0; i < 8; i++) { const r = (i % 2 ? 0.35 : 1) * unit * 0.024; const a = i / 8 * TAU; ctx[i ? 'lineTo' : 'moveTo'](Math.sin(a) * r, -Math.cos(a) * r); }
    ctx.closePath(); ctx.fill(); ctx.restore();
    if (arrived > 0) FX.ring(ctx, M.ex, M.ey, unit * (0.03 + 0.05 * ((p.t * 0.3) % 1)), unit * 0.003, GOLD, 0.35 * arrived * (1 - ((p.t * 0.3) % 1)));
    // head of the line
    if (prog < 0.995) { const hp = pointAt(pts, prog * n); FX.light(ctx, hp[0], hp[1], unit * 0.008, GOLD, 0.95); }
    ctx.restore();
  },
};

// ---------------------------------------------------------------- seed_in_foam
const seed_in_foam = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    const dis = smooth(p.u / 0.8);
    FX.bg(ctx, w, h, mix([10, 12, 30], [16, 12, 26], dis), mix([24, 22, 50], [30, 22, 44], dis));
    // the old universe: stars and a faint galaxy, dissolving
    FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 8000), { fade: (i, x, y) => 1 - smooth((dis - U.hash(i * 7) * 0.6) / 0.35) });
    const gA = 0.3 * (1 - smooth((p.u - 0.05) / 0.45));
    if (gA > 0.01) {
      ctx.save(); ctx.translate(cx + unit * 0.32, cy - unit * 0.22); ctx.rotate(-0.4); ctx.scale(1, 0.4);
      FX.glow(ctx, 0, 0, unit * 0.16, [190, 170, 255], gA, true);
      ctx.restore();
      ctx.save(); ctx.translate(cx - unit * 0.36, cy + unit * 0.2); ctx.rotate(0.5); ctx.scale(1, 0.35);
      FX.glow(ctx, 0, 0, unit * 0.12, [170, 200, 255], gA * 0.8, true);
      ctx.restore();
    }
    // quantum foam: bubbles appear, swell and pop; more of them as everything dissolves
    const rnd = U.rng(p.seed * 3 + 101);
    const N = 90, active = N * (0.35 + 0.65 * dis);
    const safe = unit * 0.11;
    for (let i = 0; i < N; i++) {
      let bx = rnd() * w, by = rnd() * h;
      const per = 2.2 + rnd() * 3.2, ph = rnd() * per, rmax = unit * (0.015 + 0.055 * rnd() * rnd() + 0.02 * rnd());
      const tone = rnd();
      if (i > active) continue;
      const dx = bx - cx, dy = by - cy, d = Math.hypot(dx, dy);
      const keep = safe + rmax * 1.2;
      if (d < keep) { bx = cx + dx / (d || 1) * keep; by = cy + dy / (d || 1) * keep; }
      const age = ((p.t + ph) % per) / per;
      const r = rmax * (0.2 + 0.8 * smooth(age / 0.8));
      const a = smooth(age / 0.25) * (1 - smooth((age - 0.82) / 0.18)) * clamp(active - i) * 0.6;
      if (a < 0.01) continue;
      const col = mix([150, 120, 200], ASH, tone);
      const g = ctx.createRadialGradient(bx - r * 0.35, by - r * 0.35, 0, bx, by, r);
      g.addColorStop(0, rgba(col, a * 0.25)); g.addColorStop(0.7, rgba(col, a * 0.06)); g.addColorStop(1, rgba(col, a * 0.32));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(bx, by, r, 0, TAU); ctx.fill();
      ctx.strokeStyle = rgba(shade(col, 0.3), a * 0.45); ctx.lineWidth = Math.max(1, unit * 0.002);
      ctx.stroke();
    }
    // the tiny seed holds, in a calm pocket
    const breathe = 0.5 + 0.5 * Math.sin(p.t * 1.1);
    FX.glow(ctx, cx, cy, safe * 1.4, [255, 200, 130], 0.18 + 0.05 * breathe);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = rgba(GOLD, 0.12 + 0.05 * breathe); ctx.lineWidth = unit * 0.003;
    ctx.beginPath(); ctx.arc(cx, cy, safe * 0.8, 0, TAU); ctx.stroke(); ctx.restore();
    FX.seed(ctx, cx, cy, unit * 0.018, 1);
  },
};

// ---------------------------------------------------------------- alien_finds
const ALIEN_BODY = [26, 46, 52], ALIEN_RIM = [120, 240, 210];
function drawAlien(ctx, x, y, h, P, o = {}) {
  const f = o.facing || 1;
  const F = FX.figure(ctx, x, y, h, P, { color: ALIEN_BODY, facing: f });
  // elongated, gentle head over the figure's head
  const [hx, hy] = F.head;
  const hr = h * 0.068;
  const tilt = f * (0.25 + (P.head || 0) * 0.5);
  ctx.save(); ctx.translate(hx + f * hr * 0.1, hy - hr * 0.35); ctx.rotate(tilt);
  ctx.fillStyle = rgba(ALIEN_BODY);
  ctx.beginPath(); ctx.ellipse(0, -hr * 0.3, hr * 0.9, hr * 1.45, 0, 0, TAU); ctx.fill();
  ctx.strokeStyle = rgba(ALIEN_RIM, 0.45); ctx.lineWidth = Math.max(1, h * 0.006);
  ctx.beginPath(); ctx.ellipse(0, -hr * 0.3, hr * 0.9, hr * 1.45, 0, f > 0 ? -1.4 : Math.PI - 0.6, f > 0 ? 0.6 : Math.PI + 1.4); ctx.stroke();
  // large soft eye on the facing side
  const ex = f * hr * 0.42, ey = -hr * 0.15;
  ctx.fillStyle = rgba([160, 255, 230], 0.85);
  ctx.beginPath(); ctx.ellipse(ex, ey, hr * 0.22, hr * 0.34, f * 0.3, 0, TAU); ctx.fill();
  ctx.restore();
  FX.glow(ctx, hx + f * hr * 0.5, hy - hr * 0.5, hr * 1.6, [140, 255, 220], 0.18);
  return F;
}
function alienWorld(ctx, w, h, p, gy) {
  const { unit } = frame(w, h);
  FX.bg(ctx, w, h, [14, 10, 34], [46, 30, 70]);
  FX.stars(ctx, w, h * 0.7, p.t, p.seed, Math.round(w * h / 16000));
  // a ringed planet and a small moon
  const px = w * 0.78, py = gy - (gy * 0.62);
  FX.glow(ctx, px, py, unit * 0.22, [200, 150, 255], 0.18);
  const pg = ctx.createRadialGradient(px - unit * 0.04, py - unit * 0.04, 0, px, py, unit * 0.1);
  pg.addColorStop(0, rgba([210, 180, 240])); pg.addColorStop(1, rgba([100, 70, 150]));
  ctx.fillStyle = pg; ctx.beginPath(); ctx.arc(px, py, unit * 0.09, 0, TAU); ctx.fill();
  ctx.strokeStyle = rgba([230, 200, 255], 0.4); ctx.lineWidth = unit * 0.006;
  ctx.beginPath(); ctx.ellipse(px, py, unit * 0.16, unit * 0.035, -0.3, 0, TAU); ctx.stroke();
  ctx.fillStyle = rgba([200, 230, 230], 0.8); ctx.beginPath(); ctx.arc(w * 0.18, py - unit * 0.06, unit * 0.022, 0, TAU); ctx.fill();
  // far ridge and spires
  ctx.fillStyle = rgba([34, 30, 62]);
  ctx.beginPath(); ctx.moveTo(0, gy);
  for (let i = 0; i <= 24; i++) { const x = i / 24 * w; ctx.lineTo(x, gy - unit * (0.06 + 0.05 * U.fbm1(i * 0.35, p.seed + 4))); }
  ctx.lineTo(w, gy); ctx.fill();
  const spire = (sx, sh, sw) => {
    ctx.beginPath(); ctx.moveTo(sx - sw, gy); ctx.quadraticCurveTo(sx - sw * 0.2, gy - sh * 0.6, sx + sw * 0.15, gy - sh);
    ctx.quadraticCurveTo(sx + sw * 0.25, gy - sh * 0.5, sx + sw, gy); ctx.fill();
  };
  ctx.fillStyle = rgba([24, 22, 48]);
  spire(w * 0.08, unit * 0.32, unit * 0.04); spire(w * 0.93, unit * 0.24, unit * 0.035); spire(w * 0.64, unit * 0.14, unit * 0.025);
  ground(ctx, w, h, gy, [20, 34, 44], [120, 240, 210], 0.25);
}
function alienHandprint(ctx, w, h, p) {
  const { unit, cx, cy } = frame(w, h);
  // cold rock face filling the frame
  const rg = ctx.createLinearGradient(0, 0, w, h);
  rg.addColorStop(0, rgba([34, 38, 56])); rg.addColorStop(1, rgba([18, 20, 34]));
  ctx.fillStyle = rg; ctx.fillRect(0, 0, w, h);
  // soft strata and a couple of cracks
  ctx.save();
  for (let i = 0; i < 6; i++) {
    const y = h * (0.1 + i * 0.17) + U.noise1(i * 3.1, p.seed) * unit * 0.04;
    const g = ctx.createLinearGradient(0, y - unit * 0.05, 0, y + unit * 0.05);
    g.addColorStop(0, rgba([70, 76, 104], 0)); g.addColorStop(0.5, rgba([70, 76, 104], 0.18)); g.addColorStop(1, rgba([70, 76, 104], 0));
    ctx.fillStyle = g; ctx.fillRect(0, y - unit * 0.05, w, unit * 0.1);
  }
  ctx.strokeStyle = rgba([8, 8, 16], 0.5); ctx.lineWidth = Math.max(1, unit * 0.004);
  ctx.beginPath(); ctx.moveTo(w * 0.05, h * 0.3); ctx.lineTo(w * 0.16, h * 0.36); ctx.lineTo(w * 0.22, h * 0.33); ctx.lineTo(w * 0.3, h * 0.42); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(w * 0.95, h * 0.62); ctx.lineTo(w * 0.85, h * 0.7); ctx.lineTo(w * 0.8, h * 0.68); ctx.stroke();
  ctx.restore();
  // the handprint that was already there (a human-sized hand of light)
  const touch = smooth((p.u - 0.42) / 0.18);
  const resp = touch * (0.75 + 0.25 * Math.sin(p.t * 1.3));
  const S = unit * 0.5;
  const px = cx - S * 0.02, py = cy + S * 0.5;
  FX.glow(ctx, px, py - S * 0.5, S * (0.75 + 0.35 * resp), CYAN, 0.1 + 0.35 * resp);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = 0.28 + 0.6 * resp;
  FX.hand(ctx, px, py, -0.05, S * 0.92, 'open', { skin: [60, 150, 190], shadow: [30, 90, 130], outline: [150, 240, 255] });
  ctx.restore();
  // the alien hand comes down onto it (back of the hand toward us, long slender fingers)
  const k = easeInOut(clamp((p.u + 0.05) / 0.5));
  const hx = lerp(cx + S * 0.25, px + S * 0.02, k), hy = lerp(cy + S * 0.95, py + S * 0.02, k);
  const ang = lerp(0.35, -0.02, k);
  const lift = 1 + 0.06 * (1 - k);
  // forearm reaching in from below
  forearm(ctx, hx, hy, Math.PI / 2 + ang * 0.6, h, S * 0.4 * lift, [66, 108, 102], ALIEN_RIM);
  ctx.save(); ctx.globalAlpha = 1;
  FX.hand(ctx, hx, hy, ang, S * lift, R.lerpPose('relaxed', 'open', k), { skin: [88, 140, 132], shadow: [40, 76, 74], outline: [24, 44, 48], back: true });
  ctx.restore();
  // light answering through the gaps between the fingers and around the edge
  if (touch > 0) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = 0.45 * resp;
    FX.hand(ctx, px, py, -0.05, S * 0.92, 'open', { skin: [0, 0, 0], shadow: [0, 0, 0], outline: [170, 245, 255] });
    ctx.restore();
    FX.glow(ctx, hx, hy - S * 0.45, S * 0.5, CYAN, 0.12 * resp);
  }
}
const alien_finds = {
  testParams: { stage: 'handprint' },
  draw(ctx, w, h, p) {
    const stage = (p.params && p.params.stage) || 'find';
    if (stage === 'handprint') return alienHandprint(ctx, w, h, p);
    const { unit, cx, port } = frame(w, h);
    const gy = port ? h * 0.68 : h * 0.8;
    alienWorld(ctx, w, h, p, gy);
    const fh = unit * (port ? 0.42 : 0.5);
    const breathe = Math.sin(p.t * 0.9);
    if (stage === 'pull') {
      const k = smooth(p.u / 0.7);
      const ax = cx - unit * 0.2 + unit * 0.05 * smooth((p.u - 0.4) / 0.4);
      const P = blendPose(pose({ head: 0.05 }), pose({ lean: 0.1, head: -0.15, armR: [0.15, 0.1], armL: [1.2, 0.35], legL: [0.12, 0], legR: [-0.08, 0] }), k);
      // thread from the chest toward something far to the right
      const chestY = gy - fh * 0.68;
      const pts = [];
      for (let i = 0; i <= 60; i++) {
        const s = i / 60;
        pts.push([ax + fh * 0.05 + s * (w + unit * 0.2 - ax), chestY - s * unit * 0.12 + Math.sin(s * 9 - p.t * 1.2) * unit * 0.012 * s]);
      }
      glowStroke(ctx, pts, 60, unit * 0.003, GOLD, 0.35 + 0.5 * k);
      // the pull: soft rings from the chest
      for (let j = 0; j < 2; j++) {
        const ph = ((p.t * 0.35 + j * 0.5) % 1);
        FX.ring(ctx, ax + fh * 0.04, chestY, unit * (0.02 + 0.12 * ph), unit * 0.003, GOLD, 0.3 * (1 - ph) * (0.3 + 0.7 * k));
      }
      FX.glow(ctx, ax + fh * 0.04, chestY, unit * 0.07, GOLD, 0.3 + 0.2 * k);
      drawAlien(ctx, ax, gy, fh, P);
      FX.glow(ctx, ax + fh * 0.04, chestY, unit * 0.03, GOLD, 0.4 + 0.1 * breathe);
      return;
    }
    if (stage === 'follow') {
      const goalX = w * (port ? 0.82 : 0.86), goalY = gy - unit * 0.01;
      const ax = lerp(w * 0.18, w * 0.52, smooth(p.u / 0.95));
      const F = probe(ctx, ax, gy, fh, walkPose(p.t * 0.45, 0.08, -0.05));
      const hand = [F.head[0] + fh * 0.05, gy - fh * 0.66];
      const pts = [];
      for (let i = 0; i <= 80; i++) {
        const s = i / 80;
        pts.push([lerp(hand[0], goalX, s), lerp(hand[1], goalY, s) - Math.sin(s * Math.PI) * unit * 0.05 + Math.sin(s * 7 - p.t) * unit * 0.008 * Math.sin(s * Math.PI)]);
      }
      FX.glow(ctx, goalX, goalY, unit * 0.12, GOLD, 0.35);
      FX.seed(ctx, goalX, goalY - unit * 0.012, unit * 0.012, 0.9);
      glowStroke(ctx, pts, 80, unit * 0.003, GOLD, 0.75);
      drawAlien(ctx, ax, gy, fh, walkPose(p.t * 0.45, 0.08, -0.05));
      return;
    }
    // find: kneel before the glowing seed; it rises gently into the reaching hand's light
    const k = smooth(p.u / 0.45), reach = smooth((p.u - 0.3) / 0.35);
    const ax = cx - unit * 0.14;
    const stand = pose({ head: 0.1 });
    const kneel = pose({ kneel: true, lean: 0.5, head: 0.5, armL: [0.25, 0.4], armR: [lerp(0.2, 0.6, reach), lerp(0.2, 0.12, reach)] });
    const P = blendPose(stand, kneel, k);
    const F = probe(ctx, ax, gy, fh, P);
    const gx0 = ax + fh * 0.36, rise = smooth((p.u - 0.5) / 0.32);
    const hd = F.handR[0] > F.handL[0] ? F.handR : F.handL;
    const sx = lerp(gx0, hd[0] + fh * 0.03, rise), sy = lerp(gy - unit * 0.016, hd[1] + fh * 0.09, rise) + Math.sin(p.t * 1.1) * unit * 0.004 * rise;
    const glowK = 0.5 + 0.5 * smooth((p.u - 0.45) / 0.35);
    FX.glow(ctx, sx, sy, unit * (0.2 + 0.15 * glowK), GOLD, 0.25 + 0.3 * glowK + 0.05 * breathe);
    // thread arriving from behind the alien, ending at the seed
    const pts = [];
    for (let i = 0; i <= 60; i++) { const s = i / 60; pts.push([lerp(-unit * 0.05, sx, s), lerp(gy - unit * 0.2, sy, s) - Math.sin(s * Math.PI) * unit * 0.08]); }
    glowStroke(ctx, pts, 60, unit * 0.0025, GOLD, 0.45 * (1 - 0.7 * rise));
    drawAlien(ctx, ax, gy, fh, P);
    FX.seed(ctx, sx, sy, unit * 0.018, 1);
    FX.glow(ctx, ax + fh * 0.15, gy - fh * 0.4, fh * 0.45, GOLD, 0.12 * glowK);
  },
};
function probe(ctx, x, y, h, P) {
  ctx.save(); ctx.globalAlpha = 0;
  const r = FX.figure(ctx, x, y, h, P, {});
  ctx.restore();
  return r;
}

// ---------------------------------------------------------------- thread_follow
const threadCache = {};
const thread_follow = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    night(ctx, w, h, p, [4, 6, 16], [14, 14, 34], 16000);
    const key = `${w}x${h}:${p.seed}`;
    let T = threadCache[key];
    if (!T) {
      const sx = port ? w * 0.2 : w * 0.06, sy = port ? h * 0.92 : h * 0.86;
      const ex = port ? cx : w * 0.74, ey = port ? h * 0.26 : h * 0.34;
      const base = [];
      const N = 200;
      for (let i = 0; i <= N; i++) {
        const s = i / N;
        const bx = lerp(sx, ex, s), by = lerp(sy, ey, s);
        const amp = unit * 0.16 * Math.sin(s * Math.PI) * (1 - s * 0.3);
        const nx = -(ey - sy), ny = (ex - sx), nl = Math.hypot(nx, ny);
        const wv = Math.sin(s * TAU * 2.1 + p.seed) * amp + U.fbm1(s * 4, p.seed + 2) * unit * 0.06 * Math.sin(s * Math.PI);
        base.push([bx + nx / nl * wv, by + ny / nl * wv, s]);
      }
      T = threadCache[key] = { base, ex, ey };
    }
    const pts = T.base.map(([x, y, s]) => [x + Math.sin(p.t * 0.5 + s * 6) * unit * 0.006 * Math.sin(s * Math.PI), y + Math.cos(p.t * 0.4 + s * 5) * unit * 0.005 * Math.sin(s * Math.PI)]);
    const n = pts.length - 1;
    const prog = 0.25 + 0.75 * easeInOut(clamp(p.u / 0.78));
    const arrived = smooth((prog - 0.97) / 0.03);
    // destination seed visible from the start
    FX.glow(ctx, T.ex, T.ey, unit * (0.12 + 0.12 * arrived), GOLD, 0.2 + 0.35 * arrived + 0.05 * Math.sin(p.t * 1.2));
    // ghost of the whole route, then the lit thread
    ctx.save(); ctx.strokeStyle = rgba(GOLD, 0.08); ctx.lineWidth = unit * 0.003; polyline(ctx, pts, n); ctx.stroke(); ctx.restore();
    glowStroke(ctx, pts, prog * n, unit * 0.0035, GOLD, 0.85);
    FX.seed(ctx, T.ex, T.ey, unit * 0.026, 0.7 + 0.3 * arrived);
    if (arrived > 0) {
      const ph = (p.t * 0.3) % 1;
      FX.ring(ctx, T.ex, T.ey, unit * (0.04 + 0.08 * ph), unit * 0.003, GOLD, 0.35 * arrived * (1 - ph));
    }
    if (prog < 0.99) { const hp = pointAt(pts, prog * n); FX.light(ctx, hp[0], hp[1], unit * 0.007, [255, 236, 190], 0.9); }
  },
};

// ---------------------------------------------------------------- engine_reignite
let heartPts = null;
function heartPath(ctx, x, y, s) {
  if (!heartPts) {
    heartPts = [];
    for (let i = 0; i < 64; i++) {
      const a = i / 64 * TAU;
      heartPts.push([16 * Math.pow(Math.sin(a), 3) / 17, -(13 * Math.cos(a) - 5 * Math.cos(2 * a) - 2 * Math.cos(3 * a) - Math.cos(4 * a)) / 17]);
    }
  }
  ctx.beginPath();
  heartPts.forEach(([hx, hy], i) => { const px = x + hx * s, py = y + hy * s + s * 0.1; if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py); });
  ctx.closePath();
}
function gear(ctx, x, y, r, teeth, rot, depth) {
  ctx.beginPath();
  for (let i = 0; i < teeth * 4; i++) {
    const a = rot + i / (teeth * 4) * TAU;
    const rr = (i % 4 < 2) ? r : r - depth;
    ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
  }
  ctx.closePath();
}
const engine_reignite = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    const warm = smooth((p.u - 0.3) / 0.45);
    FX.bg(ctx, w, h, mix([8, 12, 24], [14, 10, 24], warm), mix([18, 24, 40], [40, 22, 30], warm));
    FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 16000));
    const S = unit * 0.24;
    // heartbeat once alive
    const beatT = p.t * 1.1;
    const beat = warm * (Math.pow(Math.max(0, Math.sin(beatT * TAU * 0.5)), 12) + 0.5 * Math.pow(Math.max(0, Math.sin(beatT * TAU * 0.5 - 0.5)), 12));
    const s = S * (1 + 0.035 * beat);
    // gears behind, start turning as warmth returns
    const tt = Math.max(0, p.t - 0.35 * p.dur);
    const rot = 0.25 * (tt < 2 ? tt * tt / 4 : tt - 1);
    const metal = mix([70, 84, 104], [150, 100, 60], warm);
    FX.glow(ctx, cx, cy, S * 2.6, mix([90, 120, 160], AMBER, warm), 0.1 + 0.25 * warm);
    ctx.fillStyle = rgba(shade(metal, -0.35));
    gear(ctx, cx - S * 0.95, cy - S * 0.7, S * 0.55, 10, rot, S * 0.09); ctx.fill();
    gear(ctx, cx + S * 1.0, cy + S * 0.55, S * 0.48, 9, -rot * 1.15 + 0.2, S * 0.08); ctx.fill();
    ctx.fillStyle = rgba(shade(metal, -0.6));
    ctx.beginPath(); ctx.arc(cx - S * 0.95, cy - S * 0.7, S * 0.16, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.arc(cx + S * 1.0, cy + S * 0.55, S * 0.14, 0, TAU); ctx.fill();
    // the heart body: cold steel
    const hg = ctx.createLinearGradient(cx - s, cy - s, cx + s, cy + s);
    hg.addColorStop(0, rgba(mix([120, 136, 160], [170, 110, 80], warm))); hg.addColorStop(1, rgba(mix([40, 48, 66], [80, 34, 40], warm)));
    ctx.fillStyle = hg; heartPath(ctx, cx, cy, s); ctx.fill();
    // frost rim fading away
    ctx.strokeStyle = rgba([200, 230, 255], 0.35 * (1 - warm)); ctx.lineWidth = unit * 0.005; ctx.stroke();
    // panel seams
    ctx.save(); heartPath(ctx, cx, cy, s); ctx.clip();
    ctx.strokeStyle = rgba([10, 12, 20], 0.35); ctx.lineWidth = unit * 0.003;
    ctx.beginPath(); ctx.moveTo(cx - s * 0.1, cy - s * 0.6); ctx.quadraticCurveTo(cx + s * 0.1, cy, cx - s * 0.05, cy + s * 0.9); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(cx, cy + s * 0.05, s * 0.36, s * 0.36, 0, 0, TAU); ctx.stroke();
    // warmth spreading from the core
    const wr = s * (0.15 + 1.4 * warm);
    const wg = ctx.createRadialGradient(cx, cy + s * 0.05, 0, cx, cy + s * 0.05, wr);
    wg.addColorStop(0, rgba([255, 236, 190], 0.95 * smooth(warm * 3))); wg.addColorStop(0.45, rgba(AMBER, 0.75 * smooth(warm * 2))); wg.addColorStop(1, rgba([214, 80, 60], 0));
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = wg; ctx.fillRect(cx - s * 1.5, cy - s * 1.5, s * 3, s * 3);
    ctx.restore();
    // core
    const coreA = Math.max(0.15 * (1 - warm), warm);
    FX.light(ctx, cx, cy + s * 0.05, unit * 0.014 * (1 + 0.4 * beat), mix([150, 190, 230], GOLD, warm), coreA);
    FX.glow(ctx, cx, cy, S * 1.7, AMBER, 0.25 * beat);
    // the spark that relights it: two soft arcs between the pipes and the core
    const sp = clamp((p.u - 0.12) / 0.22);
    if (sp > 0 && sp < 1) {
      const a = Math.sin(sp * Math.PI);
      const rnd = U.rng(p.seed + Math.floor(sp * 4));
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      for (const [x0, y0] of [[cx - S * 0.6, cy - S * 0.42], [cx + S * 0.62, cy + S * 0.28]]) {
        const pts = [[x0, y0]];
        for (let i = 1; i <= 5; i++) { const f = i / 5; pts.push([lerp(x0, cx, f) + (rnd() - 0.5) * S * 0.12 * (1 - f * 0.5), lerp(y0, cy + s * 0.05, f)]); }
        ctx.strokeStyle = rgba(GOLD, 0.3 * a); ctx.lineWidth = unit * 0.012; polyline(ctx, pts, 5); ctx.stroke();
        ctx.strokeStyle = rgba([255, 250, 230], 0.8 * a); ctx.lineWidth = unit * 0.004; polyline(ctx, pts, 5); ctx.stroke();
      }
      ctx.restore();
      FX.glow(ctx, cx, cy, S * 0.8, GOLD, 0.35 * a);
    }
    // rising embers once alive
    const er = U.rng(p.seed + 5);
    for (let i = 0; i < 18; i++) {
      const per = 3 + er() * 3, ph = er() * per, ox = (er() - 0.5) * S * 2;
      const age = ((p.t + ph) % per) / per;
      dot(ctx, cx + ox + Math.sin(p.t + i) * S * 0.08, cy + S * 0.6 - age * S * 2.2, unit * 0.003, GOLD, warm * 0.6 * Math.sin(age * Math.PI));
    }
  },
};

// ---------------------------------------------------------------- torch_pass
function flame(ctx, x, y, s, t, seed) {
  FX.glow(ctx, x, y - s * 0.5, s * 3.2, AMBER, 0.35);
  const sway = U.noise1(t * 0.9, seed) * s * 0.18, sway2 = U.noise1(t * 1.3, seed + 3) * s * 0.1;
  const hgt = s * (1.5 + 0.1 * U.noise1(t * 1.1, seed + 7));
  const layer = (sc, col, a) => {
    ctx.fillStyle = rgba(col, a);
    ctx.beginPath();
    ctx.moveTo(x - s * 0.42 * sc, y);
    ctx.bezierCurveTo(x - s * 0.5 * sc, y - hgt * 0.45 * sc, x + sway2 * sc, y - hgt * 0.6 * sc, x + sway * sc, y - hgt * sc);
    ctx.bezierCurveTo(x + s * 0.15 * sc + sway2, y - hgt * 0.55 * sc, x + s * 0.5 * sc, y - hgt * 0.4 * sc, x + s * 0.42 * sc, y);
    ctx.quadraticCurveTo(x, y + s * 0.28 * sc, x - s * 0.42 * sc, y);
    ctx.fill();
  };
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  layer(1.0, [230, 90, 50], 0.55);
  layer(0.78, AMBER, 0.7);
  layer(0.52, GOLD, 0.85);
  layer(0.28, [255, 248, 225], 0.9);
  ctx.restore();
}
const torch_pass = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy, port } = frame(w, h);
    night(ctx, w, h, p, [8, 8, 20], [26, 18, 34], 14000);
    const hs = unit * 0.25; // hand size
    // torch travels a little from left-centre to right-centre
    const carry = smooth((p.u - 0.55) / 0.3);
    const tx = cx - unit * 0.06 + unit * 0.12 * carry, ty = cy - unit * 0.06 - unit * 0.03 * carry + (port ? -h * 0.03 : 0);
    const L = unit * 0.5;
    const top = ty - L * 0.45, bot = ty + L * 0.55;
    // hand A (left) holds lower; hand B (right) arrives, grips higher; A lets go and withdraws
    const bIn = easeInOut(clamp(p.u / 0.3)), bGrip = smooth((p.u - 0.26) / 0.14);
    const aOpen = smooth((p.u - 0.44) / 0.12), aOut = easeInOut(clamp((p.u - 0.5) / 0.3));
    const gripOff = hs * 0.56; // fist knuckle centre from wrist along fingers
    const ayG = ty + L * 0.3, byG = ty + L * 0.05;
    const awx = tx - gripOff - aOut * unit * 0.14, awy = ayG + aOut * unit * 0.12;
    const bwx = tx + gripOff + (1 - bIn) * unit * 0.35, bwy = byG + (1 - bIn) * unit * 0.06;
    const SLEEVE_A = [44, 36, 50], SLEEVE_B = [30, 40, 58];
    const handA = () => {
      forearm(ctx, awx, awy, Math.PI + 0.35, unit * 1.2, hs * 0.42, SLEEVE_A, GOLD);
      FX.hand(ctx, awx, awy, Math.PI / 2 - 0.35 * aOut, hs, R.lerpPose('fist', 'relaxed', aOpen), {});
    };
    const handB = () => {
      forearm(ctx, bwx, bwy, -0.25, unit * 1.2, hs * 0.42, SLEEVE_B, CYAN);
      FX.hand(ctx, bwx, bwy, -Math.PI / 2 + 0.0, hs, R.lerpPose('relaxed', 'fist', bGrip), { mirror: true, skin: [190, 132, 100], shadow: [110, 66, 52] });
    };
    // open hands sit behind the shaft; gripping hands wrap in front of it
    if (aOpen > 0.5) handA();
    if (bGrip < 0.5) handB();
    // shaft
    const sg = ctx.createLinearGradient(tx - unit * 0.02, 0, tx + unit * 0.02, 0);
    sg.addColorStop(0, rgba([70, 44, 30])); sg.addColorStop(0.5, rgba([130, 88, 56])); sg.addColorStop(1, rgba([60, 36, 24]));
    ctx.fillStyle = sg; ctx.beginPath(); ctx.roundRect(tx - unit * 0.017, top, unit * 0.034, bot - top, unit * 0.01); ctx.fill();
    // torch head (wrapped cup)
    ctx.fillStyle = rgba([60, 40, 34]);
    ctx.beginPath(); ctx.moveTo(tx - unit * 0.045, top - unit * 0.02); ctx.lineTo(tx + unit * 0.045, top - unit * 0.02); ctx.lineTo(tx + unit * 0.025, top + unit * 0.06); ctx.lineTo(tx - unit * 0.025, top + unit * 0.06); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = rgba([110, 70, 50], 0.8); ctx.lineWidth = unit * 0.004;
    for (let i = 0; i < 3; i++) { const y = top + i * unit * 0.022; ctx.beginPath(); ctx.moveTo(tx - unit * 0.04 + i * unit * 0.006, y); ctx.lineTo(tx + unit * 0.04 - i * unit * 0.006, y); ctx.stroke(); }
    if (aOpen <= 0.5) handA();
    if (bGrip >= 0.5) handB();
    // the flame continues, brightening a little as it is received
    const fs = unit * 0.07 * (1 + 0.12 * carry);
    flame(ctx, tx, top - unit * 0.02, fs, p.t, p.seed);
    // embers rising
    const er = U.rng(p.seed + 9);
    for (let i = 0; i < 14; i++) {
      const per = 1.8 + er() * 2, ph = er() * per, ox = (er() - 0.5) * fs;
      const age = ((p.t + ph) % per) / per;
      dot(ctx, tx + ox + Math.sin(p.t * 1.3 + i) * fs * 0.3, top - fs * 1.2 - age * unit * 0.25, unit * 0.0025, GOLD, 0.6 * Math.sin(age * Math.PI));
    }
  },
};

// ---------------------------------------------------------------- remember_continue
const remember_continue = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    const go = smooth((p.u - 0.45) / 0.4);
    FX.bg(ctx, w, h, [8, 10, 26], mix([24, 22, 48], [60, 40, 50], go));
    FX.stars(ctx, w, h * 0.8, p.t, p.seed, Math.round(w * h / 10000));
    const gy = port ? h * 0.7 : h * 0.82;
    // dawn on the right horizon
    FX.glow(ctx, w * 0.95, gy, unit * (0.35 + 0.35 * go), AMBER, 0.2 + 0.4 * go);
    FX.glow(ctx, w * 0.95, gy, unit * 0.12, GOLD, 0.25 + 0.4 * go);
    // memories: soft gold lights above, linked like a constellation
    const rem = smooth((p.u - 0.05) / 0.35);
    const rnd = U.rng(p.seed + 23);
    const mem = [];
    for (let i = 0; i < 7; i++) {
      const mx = w * (0.15 + 0.6 * (i / 6)) + (rnd() - 0.5) * unit * 0.08;
      const my = (port ? h * 0.22 : h * 0.14) + rnd() * (port ? h * 0.25 : h * 0.3) + Math.sin(p.t * 0.4 + i) * unit * 0.008;
      mem.push([mx, my, clamp(rem * 1.6 - i * 0.09)]);
    }
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineWidth = unit * 0.002;
    for (let i = 1; i < mem.length; i++) {
      const a = Math.min(mem[i][2], mem[i - 1][2]) * 0.3;
      if (a <= 0) continue;
      ctx.strokeStyle = rgba(GOLD, a); ctx.beginPath(); ctx.moveTo(mem[i - 1][0], mem[i - 1][1]); ctx.lineTo(mem[i][0], mem[i][1]); ctx.stroke();
    }
    ctx.restore();
    for (const [mx, my, a] of mem) { if (a > 0) { FX.glow(ctx, mx, my, unit * 0.06, GOLD, 0.25 * a); FX.light(ctx, mx, my, unit * 0.006, GOLD, 0.8 * a); } }
    ground(ctx, w, h, gy, [16, 14, 26], [255, 190, 120], 0.25 + 0.3 * go);
    // three figures: look up, then walk toward the light
    const fh = unit * (port ? 0.36 : 0.42);
    const look = smooth(p.u / 0.2) * (1 - go * 0.8);
    const figs = [[-0.24, 1, false, 0], [-0.1, 0.62, true, 0.33], [0.04, 0.97, false, 0.6]];
    for (const [ox, sc, child, ph] of figs) {
      const x = cx + ox * unit + go * unit * 0.2;
      const stand = pose({ head: -0.6 * look, lean: -0.04 * look });
      const P = blendPose(stand, walkPose(p.t * 0.4 + ph, 0.05, -0.05), go);
      FX.figure(ctx, x, gy, fh * sc, P, { color: [16, 14, 24], child, rim: GOLD, rimSide: 1 });
    }
  },
};

// ---------------------------------------------------------------- entropy_resist
const entropy_resist = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    night(ctx, w, h, p, [8, 9, 20], [28, 26, 40], 14000);
    const gy = port ? h * 0.7 : h * 0.84;
    ground(ctx, w, h, gy, [18, 18, 26], [150, 150, 170], 0.25);
    const rnd = U.rng(p.seed * 5 + 17);
    const towers = [[-0.42, 0.075, 6], [-0.25, 0.09, 8], [-0.12, 0.06, 4], [0.14, 0.07, 5], [0.27, 0.095, 9], [0.43, 0.07, 5]];
    const bh = unit * (port ? 0.06 : 0.052);
    const dust = [];
    for (const [ox, bwU, n] of towers) {
      const bw = unit * bwU, tx = cx + ox * unit * (port ? 1.0 : 1.25);
      for (let j = 0; j < n; j++) {
        const y0 = gy - bh * (j + 1);
        const tc = 0.06 + 0.45 * (1 - j / n) * 0.6 + rnd() * 0.3;
        const s = clamp((p.u - tc) / 0.22);
        const dir = rnd() < 0.5 ? -1 : 1, spin = (rnd() - 0.5) * 1.6, drift = (rnd() - 0.3) * unit * 0.08;
        const fall = (gy - bh * 0.5) - (y0 + bh * 0.5);
        const y = y0 + fall * s * s, x = tx + drift * s + dir * unit * 0.01 * s;
        const a = 1 - smooth((s - 0.75) / 0.25);
        if (a > 0.01) {
          const col = mix([96, 96, 112], [70, 66, 84], j / n);
          ctx.save(); ctx.translate(x, y + bh / 2); ctx.rotate(spin * s * s);
          ctx.globalAlpha = a; ctx.fillStyle = rgba(col);
          const crack = smooth(s * 3);
          ctx.beginPath(); ctx.rect(-bw / 2, -bh / 2 + 1, bw, bh - 2); ctx.fill();
          ctx.fillStyle = rgba(shade(col, 0.25), 0.6); ctx.fillRect(-bw / 2, -bh / 2 + 1, bw, unit * 0.004);
          if (crack > 0) { ctx.strokeStyle = rgba([20, 20, 30], 0.6 * crack); ctx.lineWidth = Math.max(1, unit * 0.003); ctx.beginPath(); ctx.moveTo(-bw * 0.2, -bh / 2); ctx.lineTo(bw * 0.05, 0); ctx.lineTo(-bw * 0.1, bh / 2); ctx.stroke(); }
          ctx.restore();
        }
        // dust released as the block lands and dissolves
        if (s > 0.55) dust.push([x, gy - bh * 0.3, s, rnd(), rnd()]);
        else { rnd(); rnd(); }
      }
    }
    for (const [x, y, s, r1, r2] of dust) {
      const age = clamp((s - 0.55) / 0.45) + clamp((p.u - 0.9)) * 0;
      const k = clamp((s - 0.55) / 0.45);
      for (let m = 0; m < 3; m++) {
        const dx = x + (r1 - 0.5 + m * 0.3 - 0.3) * unit * 0.1 * k + p.t * unit * 0.004 * (m - 1);
        const dy = y - k * unit * (0.03 + 0.05 * r2 + m * 0.02);
        dot(ctx, dx, dy, unit * (0.004 + m * 0.002), [150, 150, 165], 0.3 * Math.sin(Math.min(1, age + 0.2) * Math.PI));
      }
    }
    // the seed of light at the centre, untouched
    const sx = cx, sy = gy - unit * 0.025;
    const br = 0.5 + 0.5 * Math.sin(p.t * 1.2);
    FX.glow(ctx, sx, sy, unit * (0.16 + 0.04 * smooth(p.u / 0.8)), GOLD, 0.3 + 0.08 * br + 0.15 * smooth((p.u - 0.4) / 0.4));
    FX.seed(ctx, sx, sy, unit * 0.022, 1);
  },
};

// ---------------------------------------------------------------- no_sky_message
function book(ctx, x, y, W, D, theta) {
  // book lying on a ledge, seen from above-front: spine runs from far (top) to near (bottom) edge.
  // Left half stays; the right half (cover + pages) rotates about the spine and closes over it.
  const coverC = [92, 52, 60], coverD = [58, 32, 40], pageC = [222, 212, 192];
  const farK = 0.86; // far edge is narrower (perspective)
  const yF = y - D / 2, yN = y + D / 2, th = D * 0.1;
  const P = (sx, sy) => [x + sx * (sy < 0 ? farK : 1), sy < 0 ? yF : yN];
  const quad = (pts, fill) => { ctx.fillStyle = fill; ctx.beginPath(); pts.forEach(([a, b], i) => (i ? ctx.lineTo(a, b) : ctx.moveTo(a, b))); ctx.closePath(); ctx.fill(); };
  // shadow
  const sg = ctx.createRadialGradient(x, yN + th, 0, x, yN + th, W * 1.4);
  sg.addColorStop(0, 'rgba(0,0,0,0.45)'); sg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = sg; ctx.fillRect(x - W * 1.5, yN - D, W * 3, D * 1.6);
  // left cover edge and page block
  const L = (sx, far) => [x - W * sx * (far ? farK : 1), far ? yF : yN];
  quad([[x, yF], L(1.05, true), [x - W * 1.05, yN + th * 1.4], [x, yN + th * 1.4]], rgba(coverD));
  quad([[x, yF], L(1, true), [x - W, yN + th], [x, yN + th]], rgba(shade(pageC, -0.35)));
  quad([[x, yF - th * 0.3], L(1, true), L(1, false), [x, yN]], rgba(pageC));
  const pg = ctx.createLinearGradient(x - W, 0, x, 0);
  pg.addColorStop(0, 'rgba(0,0,0,0)'); pg.addColorStop(0.8, 'rgba(60,40,30,0.06)'); pg.addColorStop(1, 'rgba(60,40,30,0.4)');
  quad([[x, yF - th * 0.3], L(1, true), L(1, false), [x, yN]], pg);
  // right half
  const c = Math.cos(theta), sn = Math.sin(theta);
  const lift = W * sn * 0.75;
  const Rp = (k, far) => [x + W * k * c * (far ? farK : 1), (far ? yF : yN) - lift * k - (theta > 0.01 ? th * 0.6 * Math.min(1, theta * 3) : 0)];
  if (c >= 0) {
    // inner side visible: cover rim then blank pages
    quad([[x, yF], [x + W * 1.05 * c * farK, yF - lift * 1.05], [x + W * 1.05 * c, yN + th * 1.4 - lift * 1.05], [x, yN + th * 1.4]], rgba(coverD));
    if (theta < 0.05) quad([[x, yF], [x + W * farK, yF], [x + W, yN + th], [x, yN + th]], rgba(shade(pageC, -0.35)));
    quad([[x, yF - th * 0.3], Rp(1, true), Rp(1, false), [x, yN]], rgba(shade(pageC, -0.25 * sn)));
  } else {
    // outer cover visible, folding down over the left pages
    const cg = ctx.createLinearGradient(x, 0, x + W * c, 0);
    cg.addColorStop(0, rgba(coverD)); cg.addColorStop(1, rgba(shade(coverC, 0.1 * (1 - sn))));
    const tt = th * (1 + 1.2 * (1 - sn));
    quad([[x, yF - tt], [x + W * 1.05 * c * farK, yF - lift * 1.05 - tt], [x + W * 1.05 * c, yN - lift * 1.05 - tt + th * 1.4], [x, yN + th * 1.4 - tt]], cg);
    if (sn < 0.2) { // embossed line on the closed cover
      ctx.strokeStyle = rgba([150, 110, 90], 0.4 * (1 - sn * 5)); ctx.lineWidth = Math.max(1, W * 0.01);
      ctx.strokeRect(x - W * 0.8, yF + D * 0.12 - tt, W * 0.6, D * 0.65);
    }
  }
}
const no_sky_message = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    FX.bg(ctx, w, h, [16, 16, 28], [40, 38, 54]);
    FX.stars(ctx, w, h * 0.6, p.t, p.seed, Math.round(w * h / 30000), { color: () => [180, 180, 196] });
    // a scrawl across the empty sky, fading away from its end
    const sy = port ? h * 0.3 : h * 0.3;
    const sx0 = cx - unit * 0.42, sx1 = cx + unit * 0.42;
    const N = 220, pts = [];
    for (let i = 0; i <= N; i++) {
      const s = i / N, k = s * 11 * Math.PI;
      const r = unit * (0.03 + 0.012 * Math.sin(s * 17));
      pts.push([lerp(sx0, sx1, s) + r * 0.9 * Math.sin(k), sy - r * Math.cos(k) + Math.sin(s * 5.3) * unit * 0.03 + r * 0.6]);
    }
    const fade = smooth((p.u - 0.04) / 0.42);
    const keep = (1 - fade) * N;
    const sa = 0.75 * (1 - smooth((fade - 0.6) / 0.4));
    if (keep > 1 && sa > 0.01) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.strokeStyle = rgba([230, 220, 200], sa * 0.15); ctx.lineWidth = unit * 0.012; polyline(ctx, pts, keep); ctx.stroke();
      ctx.strokeStyle = rgba([235, 228, 210], sa); ctx.lineWidth = unit * 0.0035; polyline(ctx, pts, keep); ctx.stroke();
      ctx.restore();
    }
    // the vanished end drifts off as faint ash motes
    if (fade > 0 && fade < 1) {
      for (let i = 0; i < 24; i++) {
        const s = 1 - fade + (U.hash(i + p.seed) * 0.25);
        if (s > 1) continue;
        const pt = pointAt(pts, s * N);
        const age = clamp((fade - (1 - s)) * 4);
        dot(ctx, pt[0] + age * unit * 0.03 * (U.hash(i * 3) - 0.5), pt[1] - age * unit * 0.06, unit * 0.003, [200, 196, 210], 0.4 * (1 - age));
      }
    }
    // a ledge and the book that closes on blank pages
    const ly = port ? h * 0.76 : h * 0.84;
    ctx.fillStyle = rgba([24, 22, 32]); ctx.fillRect(0, ly, w, h - ly);
    ctx.fillStyle = rgba([90, 86, 110], 0.4); ctx.fillRect(0, ly, w, 2);
    const close = easeInOut(clamp((p.u - 0.42) / 0.38));
    const W = unit * 0.22, D = unit * 0.16;
    FX.glow(ctx, cx, ly - D * 0.3, unit * 0.3, [200, 190, 170], 0.12 * (1 - close));
    book(ctx, cx, ly - D * 0.25, W, D, close * Math.PI);
  },
};

// ---------------------------------------------------------------- pattern_reveal
const pattern_reveal = {
  draw(ctx, w, h, p) {
    const { unit, cx, cy } = frame(w, h);
    const k = smoother(clamp((p.u - 0.04) / 0.78));
    FX.bg(ctx, w, h, mix([12, 8, 22], [6, 9, 22], k), mix([30, 14, 34], [18, 20, 44], k));
    FX.glow(ctx, cx, cy, unit * 0.5, mix(PLUM, [255, 200, 130], k), 0.12 + 0.1 * k);
    const Rr = unit * 0.38;
    const L = 12, M = 70;
    const rot = p.t * 0.04;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (let layer = 0; layer < 2; layer++) {
      for (let i = 0; i < L; i++) {
        const id = layer * L + i;
        const kk = smoother(clamp(k * 1.35 - (id / (2 * L)) * 0.35));
        const base = rot + (i + layer * 0.5) / L * TAU;
        const RL = layer ? Rr : Rr * 0.62;
        const col = mix(mix(CRIMSON, PLUM, (id % 3) / 2), layer ? GOLD : CYAN, kk);
        ctx.beginPath();
        for (let j = 0; j <= M; j++) {
          const s = j / M;
          // chaos: a twisting noise path
          const tq = s * 2.6 + id * 1.7 + p.t * 0.05;
          const chx = cx + Rr * 1.15 * U.noise1(tq, id * 7 + 1) + Rr * 0.3 * Math.sin(s * 9 + id);
          const chy = cy + Rr * 1.15 * U.noise1(tq + 40, id * 7 + 3) + Rr * 0.3 * Math.cos(s * 7 + id * 2);
          // order: a petal loop
          const rr = RL * (0.08 + 0.92 * Math.sin(Math.PI * s));
          const ph = base + (layer ? 0.32 : 0.45) * Math.sin(TAU * s);
          const ox = cx + Math.cos(ph) * rr, oy = cy + Math.sin(ph) * rr;
          const x = lerp(chx, ox, kk), y = lerp(chy, oy, kk);
          if (j) ctx.lineTo(x, y); else ctx.moveTo(x, y);
        }
        ctx.strokeStyle = rgba(col, 0.12); ctx.lineWidth = unit * 0.012; ctx.stroke();
        ctx.strokeStyle = rgba(shade(col, 0.2), 0.55); ctx.lineWidth = unit * 0.0035; ctx.stroke();
      }
    }
    ctx.restore();
    // centre and outer ring appear when the order resolves
    const done = smooth((k - 0.75) / 0.25);
    FX.ring(ctx, cx, cy, Rr * 1.06, unit * 0.003, GOLD, 0.4 * done);
    FX.ring(ctx, cx, cy, Rr * 0.18, unit * 0.003, CYAN, 0.5 * done);
    FX.light(ctx, cx, cy, unit * 0.012, GOLD, 0.3 + 0.6 * done);
  },
};

// ---------------------------------------------------------------- grieve_rejoice
const grieve_rejoice = {
  draw(ctx, w, h, p) {
    const { unit, cx, port } = frame(w, h);
    night(ctx, w, h, p, [8, 8, 22], [24, 18, 40], 12000);
    const gy = port ? h * 0.68 : h * 0.84;
    const share = smooth((p.u - 0.08) / 0.5), warm = smooth((p.u - 0.4) / 0.45);
    FX.glow(ctx, cx - unit * 0.2, gy - unit * 0.1, unit * 0.3, CRIMSON, 0.22 * (1 - warm * 0.6));
    FX.glow(ctx, cx + unit * 0.2, gy - unit * 0.2, unit * 0.32, GOLD, 0.2);
    ground(ctx, w, h, gy, [16, 13, 26], [200, 150, 140], 0.25);
    const fh = unit * (port ? 0.4 : 0.5);
    const gx = cx - unit * 0.22, jx = cx + unit * 0.22;
    // grief: kneeling, head bowed, hands to the face; slowly lifts toward the light
    const grief = pose({ kneel: true, lean: 0.5, head: 0.9, armL: [0.7, 2.2], armR: [0.6, 2.3] });
    const lifted = pose({ kneel: true, lean: 0.22, head: 0.25, armL: [0.35, 1.9], armR: [0.95, 0.5] });
    const G = FX.figure(ctx, gx, gy, fh, blendPose(grief, lifted, warm * 0.85), { color: [24, 14, 22], rim: mix(CRIMSON, GOLD, warm), rimSide: 1 });
    // joy: arms raised; then one hand lowers toward the other
    const bob = Math.sin(p.t * 1.6) * 0.04;
    const joy = pose({ lean: -0.06, head: -0.3, armL: [2.55 + bob, 0.2], armR: [-2.55 - bob, -0.2] });
    const offer = pose({ lean: 0.05, head: 0.1, armL: [2.4 + bob, 0.2], armR: [1.2, 0.3] });
    // joy figure faces left (facing -1): local +x is screen-left, toward the griever
    const J = FX.figure(ctx, jx, gy, fh, blendPose(joy, offer, warm * 0.8), { color: [26, 20, 18], rim: GOLD, rimSide: 1, facing: -1 });
    // shared light: a crimson strand and a gold strand meet in one orb between them
    const ox = cx, oy = gy - fh * (0.62 + 0.04 * Math.sin(p.t * 0.7));
    const strand = (from, col, a) => {
      const pts = [];
      for (let i = 0; i <= 30; i++) { const s = i / 30; pts.push([lerp(from[0], ox, s), lerp(from[1], oy, s) - Math.sin(s * Math.PI) * unit * 0.04]); }
      glowStroke(ctx, pts, 30 * share, unit * 0.0025, col, a);
    };
    strand(G.handR, mix(CRIMSON, GOLD, warm), 0.7);
    strand([J.head[0], J.head[1] + fh * 0.14], GOLD, 0.6);
    const orb = smooth((share - 0.7) / 0.3);
    FX.glow(ctx, ox, oy, unit * (0.1 + 0.18 * warm), mix(AMBER, GOLD, warm), 0.15 + 0.4 * orb);
    FX.light(ctx, ox, oy, unit * (0.01 + 0.008 * warm), mix([255, 170, 150], GOLD, warm), 0.25 + 0.7 * orb);
    // the light falls on both
    FX.glow(ctx, G.head[0], G.head[1], fh * 0.25, GOLD, 0.15 * warm);
    FX.glow(ctx, J.head[0], J.head[1], fh * 0.25, GOLD, 0.12 + 0.08 * warm);
  },
};

module.exports = {
  compress_seed, acorn_oak, friction_motion, map_follow, seed_in_foam, alien_finds, thread_follow,
  engine_reignite, torch_pass, remember_continue, entropy_resist, no_sky_message, pattern_reveal, grieve_rejoice,
};
