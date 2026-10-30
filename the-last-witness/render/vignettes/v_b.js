// Vignettes, group b: engine_heart, bright_world, pour_into, weight_press, crack_glass, scales_balance,
// birth_light, layers_accumulate, dense_collapse, two_paths, breathing_space, face_the_shadow, teach_hands.
'use strict';
const U = require('../lib/util');
const FX = require('../lib/fx');
const { TAU, clamp, lerp, smooth, rgba, mix, shade } = U;

const GOLD = [255, 211, 138], AMBER = [255, 184, 92], CYAN = [127, 232, 255];
const CRIMSON = [214, 48, 74], BLOOD = [107, 20, 38];
const NIGHT_T = [6, 9, 21], NIGHT_B = [20, 26, 51];

function nightBg(ctx, w, h, p, starN) {
  FX.bg(ctx, w, h, NIGHT_T, NIGHT_B);
  if (starN) FX.stars(ctx, w, h, p.t, p.seed, starN);
}
function prm(p) { return p.params || {}; }

// blend two figure poses (numbers and [a,b] arrays)
function blendPose(a, b, k) {
  const o = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const key of keys) {
    const A = a[key], B = b[key];
    if (Array.isArray(A) || Array.isArray(B)) {
      const aa = A || [0, 0], bb = B || [0, 0];
      o[key] = [lerp(aa[0], bb[0], k), lerp(aa[1], bb[1], k)];
    } else if (typeof A === 'number' || typeof B === 'number') o[key] = lerp(A || 0, B || 0, k);
    else o[key] = k < 0.5 ? A : B;
  }
  return o;
}

// ---------------------------------------------------------------- soft-lit figures
// Offscreen buffers for building lit silhouettes. The canvas backend records drawImage(canvas) lazily, so a
// buffer must never be changed after it has been drawn somewhere: every stage gets a fresh canvas, and recent
// ones are kept referenced until the frame has certainly been rasterised.
const { createCanvas } = require('@napi-rs/canvas');
const _keep = []; let _keepI = 0;
function scratch(id, w, h) {
  const c = createCanvas(Math.max(2, Math.ceil(w)), Math.max(2, Math.ceil(h)));
  _keep[_keepI] = c; _keepI = (_keepI + 1) % 160;
  return [c, c.getContext('2d')];
}
// FX.figure with a soft fill light across the body, a rim light along the edges that face the light,
// and a faint halo, so it never vanishes into a dark background (no crescent marks on the head).
// o: color (body), fill (fill-light colour), fillA, rim (rim colour), rimA, rimW (rim offset, x h),
//    light [dx,dy] (screen direction toward the key light), halo (alpha), alpha, facing, child, phase,
//    shade(bctx, ax, ay, hs) optional extra painting on the body (source-atop, buffer coords: feet at ax,ay, height hs)
// Returns FX.figure's {head, handL, handR} in world coords.
function litFigure(ctx, x, y, h, pose, o = {}) {
  const fo = { facing: o.facing, child: o.child, phase: o.phase };
  let lx = (o.light || [1, -0.7])[0], ly = (o.light || [1, -0.7])[1];
  const ll = Math.hypot(lx, ly) || 1; lx /= ll; ly /= ll;
  const rimC = o.rim || [200, 220, 255];
  const d = Math.max(1.2, h * (o.rimW ?? 0.012));
  ctx.save();
  if (o.alpha != null) ctx.globalAlpha *= o.alpha;
  const base = ctx.globalAlpha;
  // halo: faint copies all around (soft edge glow so the figure separates from a dark ground)
  const haloA = o.halo ?? 0.3;
  if (haloA > 0) {
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * TAU, r = d * (i % 2 ? 2.2 : 1.3);
      ctx.globalAlpha = base * haloA * 0.12;
      FX.figure(ctx, x + Math.cos(a) * r, y + Math.sin(a) * r, h, pose, Object.assign({ color: rimC }, fo));
    }
    ctx.globalCompositeOperation = 'source-over';
  }
  // rim: copies shifted toward the light peek out from behind the body along the lit edges
  const rimA = o.rimA ?? 0.85;
  ctx.globalAlpha = base * rimA * 0.45;
  FX.figure(ctx, x + lx * d * 1.9, y + ly * d * 1.9, h, pose, Object.assign({ color: rimC }, fo));
  ctx.globalAlpha = base * rimA;
  FX.figure(ctx, x + lx * d, y + ly * d, h, pose, Object.assign({ color: mix(rimC, [255, 255, 255], 0.25) }, fo));
  ctx.globalAlpha = base;
  // body with a directional fill light, built in a small buffer (capped resolution, drawn up)
  const q = Math.min(1, 200 / h), hs = h * q;
  const pad = Math.ceil(hs * 0.66), W = pad * 2, H = Math.ceil(hs * 1.34);
  const ax = pad, ay = Math.ceil(hs * 1.25);
  const [bc, bx] = scratch('b', W, H);
  const r = FX.figure(bx, ax, ay, hs, pose, Object.assign({ color: o.color || [58, 60, 86] }, fo));
  bx.globalCompositeOperation = 'source-atop';
  const myp = ay - hs * 0.55;
  const g = bx.createLinearGradient(ax + lx * hs * 0.3, myp + ly * hs * 0.5, ax - lx * hs * 0.3, myp - ly * hs * 0.5);
  g.addColorStop(0, rgba(o.fill || rimC, o.fillA ?? 0.3)); g.addColorStop(1, rgba(o.fill || rimC, 0));
  bx.fillStyle = g; bx.fillRect(0, 0, W, H);
  if (o.shade) o.shade(bx, ax, ay, hs);
  const X0 = x - ax / q, Y0 = y - ay / q;
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(bc, 0, 0, W, H, X0, Y0, W / q, H / q);
  ctx.restore();
  const tw = (pt) => [X0 + pt[0] / q, Y0 + pt[1] / q];
  return { head: tw(r.head), handL: tw(r.handL), handR: tw(r.handR) };
}

// smooth closed path through points (quadratic midpoints)
function closedSmooth(ctx, pts) {
  const n = pts.length;
  ctx.beginPath();
  const m0 = [(pts[n - 1][0] + pts[0][0]) / 2, (pts[n - 1][1] + pts[0][1]) / 2];
  ctx.moveTo(m0[0], m0[1]);
  for (let i = 0; i < n; i++) {
    const a = pts[i], b = pts[(i + 1) % n];
    ctx.quadraticCurveTo(a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
  }
  ctx.closePath();
}

// a rounded rock shape around (x,y)
function rockPts(x, y, rx, ry, seed, n = 11, rough = 0.16) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * TAU;
    const k = 1 + (U.hash2(i, seed) - 0.5) * 2 * rough;
    pts.push([x + Math.cos(a) * rx * k, y + Math.sin(a) * ry * k]);
  }
  return pts;
}

// ---------------------------------------------------------------- gears
function gearPath(ctx, x, y, r, teeth, rot, depth, holeR) {
  ctx.beginPath();
  const n = teeth * 4;
  for (let i = 0; i <= n; i++) {
    const a = rot + (i / n) * TAU;
    const q = i % 4;
    const rr = (q === 1 || q === 2) ? r + depth : r - depth * 0.6;
    const aa = a + (q === 1 ? 0.12 : q === 2 ? -0.12 : 0) * (TAU / teeth) ;
    const px = x + Math.cos(aa) * rr, py = y + Math.sin(aa) * rr;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.closePath();
  if (holeR) { ctx.moveTo(x + holeR, y); ctx.arc(x, y, holeR, 0, TAU, true); }
}
function drawGear(ctx, x, y, r, teeth, rot, col, lightCol, holeR, unit) {
  const depth = Math.max(4, r * 0.11);
  gearPath(ctx, x, y, r, teeth, rot, depth, holeR);
  const g = ctx.createRadialGradient(x - r * 0.3, y - r * 0.35, r * 0.1, x, y, r * 1.15);
  g.addColorStop(0, rgba(shade(col, 0.25)));
  g.addColorStop(1, rgba(shade(col, -0.45)));
  ctx.fillStyle = g; ctx.fill('evenodd');
  ctx.strokeStyle = rgba(lightCol, 0.35); ctx.lineWidth = Math.max(1.5, unit * 0.003); ctx.stroke();
  if (!holeR) {
    // spokes cut-outs (soft) + hub
    ctx.fillStyle = rgba(shade(col, -0.5), 0.8);
    ctx.beginPath(); ctx.arc(x, y, r * 0.74, 0, TAU); ctx.fill();
    ctx.strokeStyle = rgba(shade(col, 0.1)); ctx.lineWidth = r * 0.14; ctx.lineCap = 'butt';
    ctx.beginPath();
    for (let i = 0; i < 3; i++) { const a = rot + i * TAU / 3; ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a) * r * 0.76, y + Math.sin(a) * r * 0.76); }
    ctx.stroke();
    ctx.fillStyle = rgba(shade(col, 0.3));
    ctx.beginPath(); ctx.arc(x, y, r * 0.16, 0, TAU); ctx.fill();
    ctx.fillStyle = rgba(shade(col, -0.6));
    ctx.beginPath(); ctx.arc(x, y, r * 0.07, 0, TAU); ctx.fill();
  }
}

const engine_heart = {
  testParams: { better: true },
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2, cy = h / 2;
    const better = !!prm(p).better;
    const k = better ? smooth((p.u - 0.08) / 0.62) : 0;
    FX.bg(ctx, w, h, mix([12, 6, 16], NIGHT_T, k), mix([30, 10, 22], [24, 30, 56], k));
    const beat = better ? 0.5 + 0.5 * Math.sin(p.t * 1.6) : Math.pow(Math.max(0, Math.sin(p.t * 2.4)), 6);
    const coreCol = mix(CRIMSON, AMBER, k);
    // ambient glow from the core
    FX.glow(ctx, cx, cy, unit * (0.55 + 0.05 * beat), coreCol, 0.22 + 0.08 * beat);
    if (h > w * 1.3) { // portrait: heat or light rising
      FX.motes(ctx, w, h, p.t, p.seed + 3, 26, mix(CRIMSON, GOLD, k), { alpha: 0.6 });
    }
    const R0 = unit * 0.19, N0 = 18;
    const speed = better ? 0.22 : 0.14;
    const stutter = better ? 0 : 0.03 * Math.sin(p.t * 3.1);
    const phi0 = p.t * speed + stutter;
    const ironA = [70, 42, 52], ironB = [58, 46, 60];
    const goldC = [228, 176, 96], tealC = [70, 175, 185];
    const sats = [
      { th: -0.5, r: unit * 0.12 }, { th: 0.75, r: unit * 0.09 }, { th: 2.05, r: unit * 0.13 },
      { th: 3.25, r: unit * 0.1 }, { th: 4.45, r: unit * 0.085 },
    ];
    sats.forEach((s, i) => {
      const n = Math.max(8, Math.round(N0 * s.r / R0));
      const rr = R0 * n / N0;
      const d = R0 + rr + unit * 0.004;
      const x = cx + Math.cos(s.th) * d, y = cy + Math.sin(s.th) * d;
      const rot = -(N0 / n) * phi0 + s.th * (1 + N0 / n) + Math.PI / n;
      const col = mix(i % 2 ? ironA : ironB, i % 2 ? tealC : goldC, k);
      drawGear(ctx, x, y, rr, n, rot, col, mix(CRIMSON, GOLD, k), 0, unit);
    });
    // central ring gear with the heart inside
    const coreR = R0 * 0.62;
    drawGear(ctx, cx, cy, R0, N0, phi0, mix([84, 46, 56], goldC, k), mix(CRIMSON, GOLD, k), coreR * 1.08, unit);
    // core: a glowing heart-sphere
    const pr = coreR * (0.92 + 0.06 * beat);
    const g = ctx.createRadialGradient(cx - pr * 0.25, cy - pr * 0.3, pr * 0.05, cx, cy, pr);
    g.addColorStop(0, rgba(mix([255, 150, 150], [255, 245, 220], k)));
    g.addColorStop(0.45, rgba(coreCol));
    g.addColorStop(1, rgba(mix(BLOOD, [200, 110, 40], k)));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, pr, 0, TAU); ctx.fill();
    FX.glow(ctx, cx, cy, pr * 2.2, coreCol, 0.35 + 0.25 * beat);
    FX.vignette(ctx, w, h, 0.5);
  },
};

// ---------------------------------------------------------------- bright_world
const bright_world = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2;
    const portrait = h > w * 1.3;
    const k = 0.3 + 0.7 * smooth(p.u / 0.8);
    const hy = h * (portrait ? 0.55 : 0.64);
    // sky
    const sky = ctx.createLinearGradient(0, 0, 0, hy);
    sky.addColorStop(0, rgba(mix([10, 12, 34], [52, 64, 128], k)));
    sky.addColorStop(0.65, rgba(mix([40, 28, 64], [200, 130, 130], k)));
    sky.addColorStop(1, rgba(mix([90, 50, 60], [255, 196, 130], k)));
    ctx.fillStyle = sky; ctx.fillRect(0, 0, w, hy + 2);
    ctx.fillStyle = rgba(mix([90, 50, 60], [255, 196, 130], k)); ctx.fillRect(0, hy + 1, w, h - hy);
    FX.stars(ctx, w, hy * 0.8, p.t, p.seed, Math.round(w * h / 9000), { fade: () => 1 - k });
    // sun rising
    const sunY = hy + unit * 0.06 - k * unit * 0.24;
    const sr = unit * 0.075;
    FX.glow(ctx, cx, sunY, unit * 0.9, AMBER, 0.35 * k + 0.1);
    FX.glow(ctx, cx, sunY, unit * 0.32, [255, 225, 170], 0.5);
    // soft rays
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 7; i++) {
      const a = -Math.PI / 2 + (i - 3) * 0.32 + Math.sin(p.t * 0.15 + i) * 0.03;
      const L = unit * (0.9 + 0.2 * U.hash(i + 3));
      const gr = ctx.createLinearGradient(cx, sunY, cx + Math.cos(a) * L, sunY + Math.sin(a) * L);
      gr.addColorStop(0, rgba(GOLD, 0.1 * k)); gr.addColorStop(1, rgba(GOLD, 0));
      ctx.fillStyle = gr; ctx.beginPath(); ctx.moveTo(cx, sunY);
      ctx.lineTo(cx + Math.cos(a - 0.06) * L, sunY + Math.sin(a - 0.06) * L);
      ctx.lineTo(cx + Math.cos(a + 0.06) * L, sunY + Math.sin(a + 0.06) * L); ctx.fill();
    }
    ctx.restore();
    ctx.fillStyle = rgba([255, 244, 220]); ctx.beginPath(); ctx.arc(cx, sunY, sr, 0, TAU); ctx.fill();
    // the world: a broad curved horizon
    const R = w * 3.2, gcY = hy + R;
    const gnd = ctx.createLinearGradient(0, hy, 0, h);
    gnd.addColorStop(0, rgba(mix([30, 26, 48], [120, 92, 78], k)));
    gnd.addColorStop(1, rgba(mix([8, 8, 18], [30, 26, 40], k)));
    ctx.fillStyle = gnd; ctx.beginPath(); ctx.arc(cx, gcY, R, 0, TAU); ctx.fill();
    // light spilling over the land
    const lg = ctx.createRadialGradient(cx, hy, 0, cx, hy, unit * 0.8);
    lg.addColorStop(0, rgba(GOLD, 0.35 * k)); lg.addColorStop(1, rgba(GOLD, 0));
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = lg;
    ctx.beginPath(); ctx.arc(cx, gcY, R, 0, TAU); ctx.fill(); ctx.restore();
    // horizon rim
    ctx.strokeStyle = rgba(GOLD, 0.5 * k + 0.1); ctx.lineWidth = Math.max(1.5, unit * 0.004);
    ctx.beginPath(); ctx.arc(cx, gcY, R, -Math.PI / 2 - 0.4, -Math.PI / 2 + 0.4); ctx.stroke();
    // small figures walking in the light
    const groundAt = (x) => gcY - Math.sqrt(R * R - (x - cx) * (x - cx));
    const people = [
      { x: -0.28, s: 0.15, ph: 0.0 }, { x: -0.2, s: 0.105, ph: 0.3, child: true },
      { x: 0.12, s: 0.14, ph: 0.6 }, { x: 0.2, s: 0.15, ph: 0.15 },
    ];
    const fy = portrait ? (h - hy) * 0.25 : (h - hy) * 0.42;
    people.forEach((q, i) => {
      const x = cx + q.x * unit + p.t * unit * 0.009;
      const y = groundAt(x) + fy * (0.6 + 0.12 * (i % 2));
      // backlit by the sun: warm rim along the sun-facing edges, soft fill so the walk reads
      FX.glow(ctx, x, y - unit * q.s * 0.6, unit * q.s * 0.6, GOLD, 0.12 * k);
      litFigure(ctx, x, y, unit * q.s, 'walk', {
        phase: p.t * 0.55 + q.ph, child: q.child, color: mix([40, 34, 50], [78, 60, 62], k),
        rim: [255, 226, 170], rimA: 0.6 + 0.3 * k, fill: [255, 196, 140], fillA: 0.18 + 0.12 * k,
        light: [cx - x, -unit * 0.25], halo: 0.25, rimW: 0.018,
      });
    });
  },
};

// ---------------------------------------------------------------- pour_into
function jug(ctx, s, liquidA) {
  // local: base at (0,0)... body centred at (0,0), mouth toward -y, spout at +x
  const body = ctx.createRadialGradient(-s * 0.25, -s * 0.2, s * 0.05, 0, 0, s * 1.1);
  body.addColorStop(0, 'rgb(150,120,150)'); body.addColorStop(1, 'rgb(46,36,64)');
  ctx.fillStyle = body;
  ctx.beginPath();
  ctx.moveTo(-s * 0.32, -s * 0.72);
  ctx.bezierCurveTo(-s * 0.36, -s * 0.5, -s * 0.78, -s * 0.35, -s * 0.72, s * 0.15);
  ctx.bezierCurveTo(-s * 0.68, s * 0.6, -s * 0.35, s * 0.72, 0, s * 0.72);
  ctx.bezierCurveTo(s * 0.35, s * 0.72, s * 0.68, s * 0.6, s * 0.72, s * 0.15);
  ctx.bezierCurveTo(s * 0.78, -s * 0.35, s * 0.36, -s * 0.5, s * 0.32, -s * 0.72);
  ctx.lineTo(s * 0.55, -s * 0.9); // spout lip
  ctx.lineTo(s * 0.36, -s * 0.84);
  ctx.lineTo(-s * 0.36, -s * 0.84);
  ctx.closePath(); ctx.fill();
  // handle
  ctx.strokeStyle = 'rgb(70,56,88)'; ctx.lineWidth = s * 0.1; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(-s * 0.36, -s * 0.62); ctx.bezierCurveTo(-s * 1.05, -s * 0.7, -s * 1.05, s * 0.1, -s * 0.66, s * 0.2); ctx.stroke();
  // highlight
  ctx.strokeStyle = 'rgba(255,230,210,0.25)'; ctx.lineWidth = s * 0.06;
  ctx.beginPath(); ctx.arc(0, 0, s * 0.55, -2.6, -1.9); ctx.stroke();
  // luminous liquid at the mouth
  FX.glow(ctx, 0, -s * 0.84, s * 0.7, GOLD, 0.45 * liquidA);
  ctx.fillStyle = rgba([255, 236, 190], liquidA);
  ctx.beginPath(); ctx.ellipse(0, -s * 0.84, s * 0.34, s * 0.06, 0, 0, TAU); ctx.fill();
}
const pour_into = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h);
    const portrait = h > w * 1.3;
    nightBg(ctx, w, h, p, Math.round(w * h / 12000));
    const groundY = portrait ? h * 0.66 : h * 0.95;
    const figH = unit * (portrait ? 0.62 : 0.56);
    const fx = w * 0.6, jx = w * (portrait ? 0.3 : 0.33), jy = groundY - figH - unit * (portrait ? 0.24 : 0.12);
    const js = unit * 0.11;
    const tip = 1.15 * U.easeInOut(p.u / 0.22);
    // ground glow
    const gg = ctx.createRadialGradient(fx, groundY, 0, fx, groundY, unit * 0.5);
    gg.addColorStop(0, rgba(GOLD, 0.18)); gg.addColorStop(1, rgba(GOLD, 0));
    ctx.fillStyle = gg; ctx.fillRect(0, groundY - unit * 0.5, w, unit);
    ctx.fillStyle = rgba([12, 14, 30], 0.7); ctx.fillRect(0, groundY, w, h - groundY);
    ctx.fillStyle = rgba(GOLD, 0.25); ctx.fillRect(fx - unit * 0.3, groundY, unit * 0.6, Math.max(1, unit * 0.003));
    // receiving figure: cool fill + rim so it reads from the start; the poured light enters at the head
    // and spreads down through the body (head first, then shoulders, chest ... feet)
    const pose = Object.assign({}, FX.FIG_POSES.stand, { head: -0.4, lean: -0.04 });
    const hit = smooth((p.u - 0.25) / 0.06);              // stream reaches the head
    const fill = smooth((p.u - 0.27) / 0.6);              // light descends
    const top = groundY - figH * 1.0;
    FX.glow(ctx, fx, top + figH * (0.1 + 0.45 * fill), figH * (0.35 + 0.3 * fill), GOLD, 0.06 + 0.16 * hit + 0.06 * fill);
    litFigure(ctx, fx, groundY, figH, pose, {
      color: [70, 74, 118], fill: [150, 160, 235], fillA: 0.28, rim: mix([190, 200, 255], GOLD, hit), rimA: 0.7,
      light: [-0.6, -1], halo: 0.25 + 0.15 * hit,
      shade: (b, ax, ay, hs) => {
        if (hit <= 0) return;
        const t0 = ay - hs * 1.02, lv = t0 + hs * (0.16 + 0.9 * fill), soft = hs * 0.14;
        const g = b.createLinearGradient(0, t0, 0, lv + soft);
        const k = clamp((lv - t0) / (lv + soft - t0), 0.01, 0.99);
        g.addColorStop(0, rgba([255, 244, 214], 0.95 * hit));
        g.addColorStop(k, rgba([255, 214, 150], 0.85 * hit));
        g.addColorStop(1, rgba(GOLD, 0));
        b.fillStyle = g; b.fillRect(0, t0 - hs * 0.1, ax * 2, lv + soft - t0 + hs * 0.1);
      },
    });
    // the jug tips; spout position in world space
    const ang = tip;
    const sp = [js * 0.55, -js * 0.9];
    const sx = jx + sp[0] * Math.cos(ang) - sp[1] * Math.sin(ang);
    const sy = jy + sp[0] * Math.sin(ang) + sp[1] * Math.cos(ang);
    // stream
    const pour = smooth((p.u - 0.16) / 0.08);
    const ex = fx + figH * 0.03, ey = top + figH * 0.03;
    if (pour > 0) {
      const front = smooth((p.u - 0.16) / 0.1);
      const cxp = sx + (ex - sx) * 0.15, cyp = sy + (ey - sy) * -0.1;
      const ptAt = (t) => [(1 - t) * (1 - t) * sx + 2 * (1 - t) * t * (cxp + unit * 0.1) + t * t * ex,
                           (1 - t) * (1 - t) * sy + 2 * (1 - t) * t * cyp + t * t * ey];
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      for (const [lw, a] of [[unit * 0.05, 0.12], [unit * 0.022, 0.4], [unit * 0.01, 0.9]]) {
        ctx.strokeStyle = rgba(lw < unit * 0.015 ? [255, 244, 210] : GOLD, a * pour);
        ctx.lineWidth = lw; ctx.beginPath();
        for (let i = 0; i <= 20; i++) { const q = ptAt((i / 20) * front); if (i === 0) ctx.moveTo(q[0], q[1]); else ctx.lineTo(q[0], q[1]); }
        ctx.stroke();
      }
      ctx.restore();
      // flowing beads of light along the stream
      for (let i = 0; i < 6; i++) {
        const t = ((p.t * 0.6 + i / 6) % 1) * front;
        const q = ptAt(t);
        FX.glow(ctx, q[0], q[1], unit * 0.025, [255, 240, 200], 0.5 * pour);
      }
      FX.glow(ctx, ex, ey, unit * 0.09, GOLD, 0.5 * pour * front);
    }
    FX.glow(ctx, jx, jy, js * 2.6, [200, 170, 255], 0.18 + 0.04 * Math.sin(p.t * 0.9));
    ctx.save(); ctx.translate(jx, jy + Math.sin(p.t * 0.7) * unit * 0.006); ctx.rotate(ang); jug(ctx, js, 1); ctx.restore();
  },
};

// ---------------------------------------------------------------- weight_press
const weight_press = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2;
    const portrait = h > w * 1.3;
    FX.bg(ctx, w, h, [8, 8, 18], [22, 20, 38]);
    const groundY = portrait ? h * 0.7 : h * 0.86;
    const press = U.easeInOut((p.u - 0.05) / 0.7);
    const sr = unit * 0.075;
    const squash = 0.38 * press;
    const sh = sr * (1 - squash), sw = sr * (1 + squash * 0.5);
    const sy = groundY - sh;
    const bright = 1 - 0.78 * press + 0.04 * Math.sin(p.t * 1.2);
    // ground
    const gr = ctx.createLinearGradient(0, groundY, 0, h);
    gr.addColorStop(0, 'rgb(28,24,40)'); gr.addColorStop(1, 'rgb(10,10,20)');
    ctx.fillStyle = gr; ctx.fillRect(0, groundY, w, h - groundY);
    // sphere light on ground + sphere
    FX.glow(ctx, cx, groundY, unit * 0.45, GOLD, 0.35 * bright);
    const sg = ctx.createRadialGradient(cx - sw * 0.3, sy - sh * 0.35, sr * 0.05, cx, sy, sr * 1.1);
    sg.addColorStop(0, rgba(mix([120, 100, 90], [255, 250, 230], bright)));
    sg.addColorStop(0.6, rgba(mix([90, 70, 60], GOLD, bright)));
    sg.addColorStop(1, rgba(mix([50, 36, 40], AMBER, bright)));
    ctx.fillStyle = sg; ctx.beginPath(); ctx.ellipse(cx, sy, sw, sh, 0, 0, TAU); ctx.fill();
    FX.glow(ctx, cx, sy, sr * 3.2, GOLD, 0.45 * bright);
    // stone descends
    const sRx = unit * 0.42, sRy = unit * 0.27;
    const contact = sy - sh; // sphere top
    const bottomY = lerp(contact - unit * 0.24, contact, smooth(p.u / 0.25) * 0.4 + press * 0.6);
    const scy = bottomY - sRy * 0.92;
    const pts = rockPts(cx + unit * 0.02, scy, sRx, sRy, 5 + (p.seed % 7), 12, 0.12);
    closedSmooth(ctx, pts);
    const rg = ctx.createLinearGradient(cx - sRx, scy - sRy, cx + sRx * 0.5, scy + sRy);
    rg.addColorStop(0, 'rgb(84,80,100)'); rg.addColorStop(0.55, 'rgb(44,42,58)'); rg.addColorStop(1, 'rgb(24,22,34)');
    ctx.fillStyle = rg; ctx.fill();
    // underside lit by the sphere's (fading) light
    ctx.save(); ctx.clip();
    const ul = ctx.createRadialGradient(cx, bottomY, 0, cx, bottomY, sRx * 0.8);
    ul.addColorStop(0, rgba(AMBER, 0.5 * bright)); ul.addColorStop(1, rgba(AMBER, 0));
    ctx.fillStyle = ul; ctx.fillRect(cx - sRx * 1.3, scy - sRy * 1.3, sRx * 2.6, sRy * 2.6);
    // a few soft facets
    ctx.strokeStyle = 'rgba(140,135,160,0.18)'; ctx.lineWidth = unit * 0.006;
    ctx.beginPath(); ctx.moveTo(cx - sRx * 0.6, scy - sRy * 0.3); ctx.quadraticCurveTo(cx - sRx * 0.1, scy - sRy * 0.55, cx + sRx * 0.4, scy - sRy * 0.4); ctx.stroke();
    ctx.restore();
    // stone shadow overhead darkening as it nears
    FX.vignette(ctx, w, h, 0.45 + 0.25 * press);
    // dust at contact
    if (press > 0.6) {
      const d = smooth((press - 0.6) / 0.4);
      for (let i = 0; i < 6; i++) {
        const side = i % 2 ? 1 : -1;
        const off = (0.6 + i * 0.25) * sr * (0.5 + d);
        FX.glow(ctx, cx + side * off * 1.6, groundY - sr * 0.15 * (i % 3), sr * 0.5, [150, 140, 160], 0.12 * d);
      }
    }
  },
};

// ---------------------------------------------------------------- crack_glass
function buildCracks(seed, unit) {
  const r = U.rng(seed * 31 + 7);
  const branches = [];
  const N = 9;
  for (let i = 0; i < N; i++) {
    let a = (i / N) * TAU + (r() - 0.5) * 0.5;
    const L = unit * (0.32 + r() * 0.42);
    const segs = 7;
    const pts = [[0, 0]];
    let x = 0, y = 0;
    for (let s = 0; s < segs; s++) {
      a += (r() - 0.5) * 0.45;
      x += Math.cos(a) * L / segs; y += Math.sin(a) * L / segs;
      pts.push([x, y]);
    }
    const delay = r() * 0.15;
    const subs = [];
    if (r() < 0.75) {
      const at = 2 + Math.floor(r() * 3);
      let b = a + (r() < 0.5 ? 0.7 : -0.7);
      const sp = [pts[at].slice()];
      let sx = pts[at][0], sy = pts[at][1];
      for (let s = 0; s < 3; s++) { b += (r() - 0.5) * 0.5; sx += Math.cos(b) * L * 0.09; sy += Math.sin(b) * L * 0.09; sp.push([sx, sy]); }
      subs.push({ pts: sp, start: at / segs });
    }
    branches.push({ pts, delay, subs });
  }
  return branches;
}
function strokePartial(ctx, pts, f) {
  const n = pts.length - 1, upto = f * n;
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i <= n; i++) {
    if (i <= upto) ctx.lineTo(pts[i][0], pts[i][1]);
    else { const k = upto - (i - 1); if (k > 0) ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)); break; }
  }
  ctx.stroke();
}
const crack_glass = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h);
    FX.bg(ctx, w, h, [10, 14, 30], [24, 22, 46]);
    // out-of-focus lights behind the glass
    const r = U.rng(p.seed + 99);
    for (let i = 0; i < 7; i++) {
      const c = [CYAN, GOLD, [180, 150, 255]][i % 3];
      FX.glow(ctx, r() * w, r() * h, unit * (0.12 + r() * 0.12), c, 0.1 + 0.04 * Math.sin(p.t * 0.3 + i));
    }
    // glass sheen
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 2; i++) {
      const x0 = w * (0.15 + i * 0.45) + Math.sin(p.t * 0.1) * unit * 0.02;
      const g = ctx.createLinearGradient(x0, 0, x0 + unit * 0.25, 0);
      g.addColorStop(0, 'rgba(200,220,255,0)'); g.addColorStop(0.5, `rgba(200,220,255,${0.05 + i * 0.02})`); g.addColorStop(1, 'rgba(200,220,255,0)');
      ctx.fillStyle = g; ctx.beginPath();
      ctx.moveTo(x0 + unit * 0.2, -10); ctx.lineTo(x0 + unit * 0.45, -10); ctx.lineTo(x0 - unit * 0.1 + unit * 0.25, h + 10); ctx.lineTo(x0 - unit * 0.35 + unit * 0.25, h + 10);
      ctx.fill();
    }
    ctx.restore();
    // pane edge frame
    ctx.strokeStyle = 'rgba(160,190,230,0.18)'; ctx.lineWidth = unit * 0.01;
    ctx.strokeRect(unit * 0.03, unit * 0.03, w - unit * 0.06, h - unit * 0.06);
    const ix = w * 0.54, iy = h * 0.46;
    const g0 = 0.14 + 0.86 * U.easeOut((p.u - 0.04) / 0.72);
    const cracks = buildCracks(p.seed, unit);
    ctx.save(); ctx.translate(ix, iy);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    // glow under the cracks
    for (const pass of [[unit * 0.014, 'rgba(127,232,255,0.10)'], [Math.max(1.6, unit * 0.0045), 'rgba(235,245,255,0.85)']]) {
      ctx.lineWidth = pass[0]; ctx.strokeStyle = pass[1];
      for (const b of cracks) {
        const f = clamp((g0 - b.delay) / (1 - b.delay));
        if (f <= 0) continue;
        strokePartial(ctx, b.pts, f);
        for (const s of b.subs) { const sf = clamp((f - s.start) / 0.35); if (sf > 0) strokePartial(ctx, s.pts, sf); }
      }
    }
    // concentric fracture ring
    const ringF = smooth((p.u - 0.3) / 0.35);
    if (ringF > 0) {
      ctx.lineWidth = Math.max(1.2, unit * 0.003); ctx.strokeStyle = `rgba(225,240,255,${0.6 * ringF})`;
      for (let i = 0; i < cracks.length; i++) {
        const a = cracks[i].pts[2], b = cracks[(i + 1) % cracks.length].pts[2];
        if (U.hash2(i, p.seed) < 0.3) continue;
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo((a[0] + b[0]) * 0.6, (a[1] + b[1]) * 0.6, lerp(a[0], b[0], ringF), lerp(a[1], b[1], ringF)); ctx.stroke();
      }
    }
    ctx.restore();
    // impact point
    FX.glow(ctx, ix, iy, unit * 0.12, [220, 240, 255], 0.3 + 0.1 * Math.sin(p.t * 0.8));
    FX.light(ctx, ix, iy, unit * 0.008, [230, 245, 255], 0.9);
  },
};

// ---------------------------------------------------------------- scales_balance
const scales_balance = {
  testParams: { tilt: 0.6 },
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2;
    const portrait = h > w * 1.3;
    nightBg(ctx, w, h, p, Math.round(w * h / 11000));
    const tilt = clamp(+(prm(p).tilt ?? 0), -1, 1);
    const baseY = portrait ? h * 0.74 : h * 0.94;
    const py = portrait ? h * 0.36 : h * 0.2;
    const L = unit * 0.33, hang = unit * (portrait ? 0.3 : 0.26);
    const a = -tilt * 0.32 * U.easeInOut((p.u - 0.08) / 0.7) + Math.sin(p.t * 0.7) * 0.012;
    FX.glow(ctx, cx, py + hang, unit * 0.6, [120, 110, 200], 0.12);
    // stand
    const metal = (x0, y0, x1, y1) => { const g = ctx.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, 'rgb(150,130,110)'); g.addColorStop(0.5, 'rgb(220,190,140)'); g.addColorStop(1, 'rgb(90,74,70)'); return g; };
    ctx.fillStyle = metal(cx - unit * 0.02, 0, cx + unit * 0.02, 0);
    ctx.fillRect(cx - unit * 0.014, py, unit * 0.028, baseY - py);
    ctx.beginPath(); ctx.ellipse(cx, baseY, unit * 0.16, unit * 0.03, 0, 0, TAU);
    ctx.fillStyle = metal(cx - unit * 0.16, 0, cx + unit * 0.16, 0); ctx.fill();
    // beam
    const ca = Math.cos(a), sa = Math.sin(a);
    const lx = cx - L * ca, ly = py - L * sa, rx = cx + L * ca, ry = py + L * sa;
    ctx.strokeStyle = metal(lx, ly, rx, ry); ctx.lineCap = 'round'; ctx.lineWidth = unit * 0.022;
    ctx.beginPath(); ctx.moveTo(lx, ly); ctx.lineTo(rx, ry); ctx.stroke();
    ctx.fillStyle = 'rgb(230,200,150)'; ctx.beginPath(); ctx.arc(cx, py, unit * 0.026, 0, TAU); ctx.fill();
    // pans
    const pan = (x, y, content) => {
      const pw = unit * 0.15, py2 = y + hang;
      ctx.strokeStyle = 'rgba(220,195,150,0.7)'; ctx.lineWidth = Math.max(1.5, unit * 0.004);
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - pw, py2); ctx.moveTo(x, y); ctx.lineTo(x + pw, py2); ctx.stroke();
      content(x, py2, pw);
      ctx.beginPath(); ctx.moveTo(x - pw * 1.05, py2); ctx.quadraticCurveTo(x, py2 + unit * 0.09, x + pw * 1.05, py2); ctx.closePath();
      ctx.fillStyle = metal(x - pw, 0, x + pw, 0); ctx.fill();
      ctx.fillStyle = 'rgba(255,230,180,0.6)'; ctx.fillRect(x - pw * 1.05, py2 - 1, pw * 2.1, Math.max(2, unit * 0.004));
    };
    pan(lx, ly, (x, y) => { // gold light
      const r = unit * 0.07;
      FX.glow(ctx, x, y - r * 0.8, unit * 0.32, GOLD, 0.45 + 0.08 * Math.sin(p.t * 1.1));
      const g = ctx.createRadialGradient(x - r * 0.3, y - r * 1.1, r * 0.1, x, y - r * 0.8, r);
      g.addColorStop(0, 'rgb(255,250,230)'); g.addColorStop(0.6, rgba(GOLD)); g.addColorStop(1, rgba(AMBER));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y - r * 0.8, r, 0, TAU); ctx.fill();
    });
    pan(rx, ry, (x, y) => { // dark stone
      const r = unit * 0.075;
      const pts = rockPts(x, y - r * 0.7, r * 1.05, r * 0.8, 3, 9, 0.14);
      closedSmooth(ctx, pts);
      const g = ctx.createLinearGradient(x - r, y - r * 1.5, x + r, y);
      g.addColorStop(0, 'rgb(70,64,84)'); g.addColorStop(1, 'rgb(16,14,24)');
      ctx.fillStyle = g; ctx.fill();
      ctx.strokeStyle = 'rgba(170,160,210,0.45)'; ctx.lineWidth = Math.max(1.5, unit * 0.004); ctx.stroke();
      FX.glow(ctx, x, y - r * 0.7, r * 2.2, [60, 20, 70], 0.25);
    });
  },
};

// ---------------------------------------------------------------- birth_light
const birth_light = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2, cy = h * 0.5;
    FX.bg(ctx, w, h, [4, 5, 14], [12, 12, 30]);
    FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 14000), { fade: () => 0.6 });
    FX.glow(ctx, cx - unit * 0.25, cy + unit * 0.15, unit * 0.5, [90, 60, 150], 0.12);
    FX.glow(ctx, cx + unit * 0.3, cy - unit * 0.2, unit * 0.4, [60, 80, 160], 0.1);
    const g = smooth(p.u / 0.6);
    const breathe = 1 + 0.04 * Math.sin(p.t * 1.1);
    const sr = unit * lerp(0.008, 0.06, g) * breathe;
    const col = mix([220, 235, 255], GOLD, g);
    // corona rays
    if (g > 0.25) {
      const ra = smooth((g - 0.25) / 0.5);
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 8; i++) {
        const a = i * TAU / 8 + p.t * 0.03;
        const Lr = sr * (3.5 + 1.2 * (i % 2)) * ra;
        const gr = ctx.createLinearGradient(cx, cy, cx + Math.cos(a) * Lr, cy + Math.sin(a) * Lr);
        gr.addColorStop(0, rgba(col, 0.35 * ra)); gr.addColorStop(1, rgba(col, 0));
        ctx.fillStyle = gr; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a + 1.57) * sr * 0.3, cy + Math.sin(a + 1.57) * sr * 0.3);
        ctx.lineTo(cx + Math.cos(a) * Lr, cy + Math.sin(a) * Lr);
        ctx.lineTo(cx + Math.cos(a - 1.57) * sr * 0.3, cy + Math.sin(a - 1.57) * sr * 0.3); ctx.fill();
      }
      ctx.restore();
    }
    FX.glow(ctx, cx, cy, unit * lerp(0.12, 0.6, g), col, lerp(0.55, 0.45, g));
    ctx.fillStyle = rgba([255, 252, 240]); ctx.beginPath(); ctx.arc(cx, cy, sr, 0, TAU); ctx.fill();
    // dust disc and a small new planet coalescing in orbit
    const d = smooth((p.u - 0.4) / 0.3), pl = smooth((p.u - 0.55) / 0.3);
    if (d > 0) {
      const orx = unit * 0.3, ory = unit * 0.08;
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(AMBER, 0.22 * d * (1 - 0.6 * pl)); ctx.lineWidth = unit * 0.02;
      ctx.beginPath(); ctx.ellipse(cx, cy, orx, ory, -0.2, 0, TAU); ctx.stroke();
      ctx.strokeStyle = rgba(GOLD, 0.25 * d); ctx.lineWidth = Math.max(1, unit * 0.003);
      ctx.beginPath(); ctx.ellipse(cx, cy, orx, ory, -0.2, 0, TAU); ctx.stroke();
      ctx.restore();
      const oa = 0.4 + p.t * 0.12;
      const ox = Math.cos(oa) * orx, oy = Math.sin(oa) * ory;
      const px = cx + ox * Math.cos(-0.2) - oy * Math.sin(-0.2), py = cy + ox * Math.sin(-0.2) + oy * Math.cos(-0.2);
      const pr = unit * 0.035 * pl;
      if (pr > 1) {
        const lx = cx - px, ly = cy - py, ll = Math.hypot(lx, ly) || 1;
        const pg = ctx.createRadialGradient(px + lx / ll * pr * 0.5, py + ly / ll * pr * 0.5, pr * 0.1, px, py, pr);
        pg.addColorStop(0, 'rgb(150,200,230)'); pg.addColorStop(0.7, 'rgb(60,90,140)'); pg.addColorStop(1, 'rgb(14,18,40)');
        ctx.fillStyle = pg; ctx.beginPath(); ctx.arc(px, py, pr, 0, TAU); ctx.fill();
        FX.glow(ctx, px, py, pr * 2.5, CYAN, 0.15 * pl);
      }
    }
  },
};

// ---------------------------------------------------------------- layers_accumulate
function bustPath(ctx, cx, bottom, s) {
  // head-and-shoulders as ONE closed outline: shoulders -> trapezius -> neck -> head -> neck -> shoulders.
  // s = overall height, bottom at `bottom`
  const top = bottom - s;
  const ry = s * 0.15, rx = ry * 0.84, hy = top + ry;
  const nw = s * 0.072;                       // neck half-width
  const nb = hy + ry + s * 0.04;               // neck base (between the collarbones)
  const th = Math.acos(clamp(nw / rx, -1, 1)); // where the neck meets the head outline
  const X = (k) => cx + k * s, Y = (k) => bottom + k * s;
  ctx.beginPath();
  ctx.moveTo(X(-0.48), bottom);
  ctx.lineTo(X(-0.47), Y(-0.3));
  ctx.bezierCurveTo(X(-0.465), Y(-0.45), X(-0.44), Y(-0.53), X(-0.34), Y(-0.565));   // deltoid / shoulder cap
  ctx.bezierCurveTo(X(-0.22), Y(-0.6), cx - nw * 1.9, nb + s * 0.005, cx - nw * 1.1, nb - s * 0.012); // trapezius
  ctx.quadraticCurveTo(cx - nw * 0.98, nb - s * 0.03, cx - nw, hy + Math.sin(th) * ry); // neck
  ctx.ellipse(cx, hy, rx, ry, 0, Math.PI - th, TAU + th, false);
  ctx.quadraticCurveTo(cx + nw * 0.98, nb - s * 0.03, cx + nw * 1.1, nb - s * 0.012);
  ctx.bezierCurveTo(cx + nw * 1.9, nb + s * 0.005, X(0.22), Y(-0.6), X(0.34), Y(-0.565));
  ctx.bezierCurveTo(X(0.44), Y(-0.53), X(0.465), Y(-0.45), X(0.47), Y(-0.3));
  ctx.lineTo(X(0.48), bottom);
  ctx.closePath();
  return hy;
}
const layers_accumulate = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2;
    const portrait = h > w * 1.3;
    nightBg(ctx, w, h, p, Math.round(w * h / 12000));
    // portrait: the bust sits above the subtitle band
    const s = portrait ? w * 0.8 : h * 0.92;
    const bottom = portrait ? h * 0.68 : h + 2;
    const top = bottom - s;
    FX.glow(ctx, cx, bottom - s * 0.45, s * 0.75, GOLD, 0.16);
    // silhouette body: a soft, lit glass body (never a black hole)
    bustPath(ctx, cx, bottom, s);
    const bg = ctx.createLinearGradient(cx - s * 0.4, top, cx + s * 0.4, bottom);
    bg.addColorStop(0, 'rgba(78,84,140,0.92)'); bg.addColorStop(1, 'rgba(36,40,82,0.92)');
    ctx.fillStyle = bg; ctx.fill();
    const N = 7, band = s * 0.143;
    const cols = [[255, 196, 120], [255, 214, 150], [127, 220, 240], [255, 184, 110], [230, 180, 230], [255, 222, 168], [255, 200, 140]];
    const amp = s * 0.018;
    for (let i = 0; i < N; i++) {
      const t0 = -0.08 + i * 0.12, arrive = U.easeInOut((p.u - t0) / 0.18);
      if (arrive <= 0) continue;
      const yRest = bottom - (i + 1) * band;
      const yStart = portrait ? top - s * 0.35 : -band * 1.3;
      const y = lerp(yStart, yRest, arrive);
      const wave = (x) => Math.sin(x * 0.012 + p.t * 0.5 + i * 1.7) * amp;
      const sheet = (thick) => {
        ctx.beginPath();
        const x0 = cx - s * 0.55, x1 = cx + s * 0.55;
        ctx.moveTo(x0, y + wave(x0));
        for (let k = 1; k <= 16; k++) { const x = lerp(x0, x1, k / 16); ctx.lineTo(x, y + wave(x)); }
        for (let k = 16; k >= 0; k--) { const x = lerp(x0, x1, k / 16); ctx.lineTo(x, y + band * thick + wave(x) * 0.6); }
        ctx.closePath();
      };
      const c = cols[i % cols.length];
      // clipped layer inside the silhouette
      ctx.save(); bustPath(ctx, cx, bottom, s); ctx.clip();
      sheet(i === 0 ? 1.3 : 1.6);
      const g = ctx.createLinearGradient(0, y, 0, y + band);
      g.addColorStop(0, rgba(shade(c, 0.3), 0.8 * arrive)); g.addColorStop(1, rgba(shade(c, -0.25), 0.8 * arrive));
      ctx.fillStyle = g; ctx.fill();
      ctx.restore();
      // falling sheet outside (fades as it settles)
      if (arrive < 1) {
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        sheet(0.6); ctx.fillStyle = rgba(c, 0.18 * (1 - arrive)); ctx.fill(); ctx.restore();
      }
    }
    // soft rim light along the edge (inner glow, no hard outline)
    ctx.save(); bustPath(ctx, cx, bottom, s); ctx.clip();
    ctx.globalCompositeOperation = 'lighter';
    bustPath(ctx, cx, bottom, s);
    for (const [lw, a] of [[0.09, 0.035], [0.06, 0.035], [0.035, 0.04], [0.015, 0.06]]) {
      ctx.strokeStyle = rgba([255, 226, 180], a); ctx.lineWidth = unit * lw; ctx.stroke();
    }
    ctx.restore();
    if (portrait) {
      ctx.fillStyle = 'rgba(6,8,20,0.9)'; ctx.fillRect(0, bottom, w, h - bottom);
      ctx.fillStyle = rgba(GOLD, 0.3); ctx.fillRect(cx - s * 0.5, bottom, s, 2);
    }
  },
};

// ---------------------------------------------------------------- dense_collapse
const dense_collapse = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2, cy = h / 2;
    FX.bg(ctx, w, h, [5, 6, 16], [16, 14, 34]);
    FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 12000), { fade: () => 0.7 });
    const c = U.easeInOut(p.u / 0.6);
    const R = unit * lerp(0.26, 0.11, c);
    const dark = smooth((p.u - 0.5) / 0.3);
    const hot = mix([255, 220, 160], [255, 245, 225], c);
    // infalling motes
    const rnd = U.rng(p.seed + 41);
    for (let i = 0; i < 60; i++) {
      const a0 = rnd() * TAU, sp = 0.08 + rnd() * 0.08, ph = rnd();
      const f = (ph + p.t * sp) % 1;
      const rr = lerp(unit * 0.62, R * 0.9, f);
      const a = a0 + f * 1.4;
      const al = smooth(f / 0.3) * (1 - smooth((f - 0.85) / 0.15)) * (0.25 + 0.5 * c);
      FX.glow(ctx, cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * 0.9, unit * 0.014, GOLD, al);
    }
    FX.glow(ctx, cx, cy, R * 3.2, AMBER, 0.25 + 0.2 * c);
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
    g.addColorStop(0, rgba([255, 255, 245])); g.addColorStop(lerp(0.3, 0.7, c), rgba(hot)); g.addColorStop(1, rgba(AMBER, 0.85));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.fill();
    // weighty gravity rings (slow contraction)
    for (let i = 0; i < 3; i++) {
      const f = ((p.t * 0.12 + i / 3) % 1);
      FX.ring(ctx, cx, cy, lerp(R * 2.6, R * 1.05, f), Math.max(1, unit * 0.004), GOLD, 0.18 * smooth(f / 0.3) * (1 - f));
    }
    if (dark > 0) {
      // accretion ring + dark core
      const cr = R * 0.55 * dark;
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba([255, 230, 180], 0.7 * dark); ctx.lineWidth = unit * 0.01;
      ctx.beginPath(); ctx.ellipse(cx, cy, R * 1.6, R * 0.32, -0.15, 0, TAU); ctx.stroke();
      ctx.restore();
      const dg = ctx.createRadialGradient(cx, cy, 0, cx, cy, cr * 1.4);
      dg.addColorStop(0, 'rgba(0,0,0,1)'); dg.addColorStop(0.7, 'rgba(2,2,6,1)'); dg.addColorStop(1, 'rgba(10,6,10,0)');
      ctx.fillStyle = dg; ctx.beginPath(); ctx.arc(cx, cy, cr * 1.4, 0, TAU); ctx.fill();
      FX.ring(ctx, cx, cy, cr * 1.02, Math.max(1.5, unit * 0.005), [255, 240, 210], 0.7 * dark);
      // front half of the ring passes over the core
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba([255, 230, 180], 0.7 * dark); ctx.lineWidth = unit * 0.01;
      ctx.beginPath(); ctx.ellipse(cx, cy, R * 1.6, R * 0.32, -0.15, 0, Math.PI); ctx.stroke();
      ctx.restore();
    }
  },
};

// ---------------------------------------------------------------- two_paths
const two_paths = {
  testParams: { left: 'Despair', right: 'Meaning' },
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2;
    const portrait = h > w * 1.3;
    const hy = h * 0.36;
    FX.bg(ctx, w, hy + 1, NIGHT_T, [40, 34, 72]);
    FX.stars(ctx, w, hy * 0.9, p.t, p.seed, Math.round(w * hy / 9000));
    const gnd = ctx.createLinearGradient(0, hy, 0, h);
    gnd.addColorStop(0, 'rgb(40,34,72)'); gnd.addColorStop(0.15, 'rgb(24,22,46)'); gnd.addColorStop(1, 'rgb(8,8,18)');
    ctx.fillStyle = gnd; ctx.fillRect(0, hy, w, h - hy);
    const reveal = 0.4 + 0.6 * U.easeInOut(p.u / 0.5);
    const lab = smooth((p.u - 0.4) / 0.25);
    const fork = [cx, portrait ? lerp(hy, h, 0.24) : lerp(hy, h, 0.42)];
    const L = [w * 0.17, hy + unit * 0.02], Rt = [w * 0.83, hy + unit * 0.02];
    // destination lights
    FX.glow(ctx, Rt[0], hy - unit * 0.02, unit * 0.45, GOLD, (0.35 + 0.06 * Math.sin(p.t * 0.9)) * (0.4 + 0.6 * reveal));
    FX.glow(ctx, L[0], hy, unit * 0.22, [110, 110, 130], 0.12);
    // a curved path as a tapered ribbon from a to b
    const ribbon = (a, ctrl, b, w0, w1, f) => {
      const pts = [], n = 24;
      for (let i = 0; i <= n; i++) {
        const t = (i / n) * f;
        const x = (1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * ctrl[0] + t * t * b[0];
        const y = (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * ctrl[1] + t * t * b[1];
        pts.push([x, y, lerp(w0, w1, t)]);
      }
      ctx.beginPath();
      pts.forEach((q, i) => { const o = pts[Math.min(i + 1, n)], pr = pts[Math.max(i - 1, 0)]; const dx = o[0] - pr[0], dy = o[1] - pr[1], d = Math.hypot(dx, dy) || 1; const x = q[0] - dy / d * q[2], y = q[1] + dx / d * q[2]; if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
      for (let i = n; i >= 0; i--) { const q = pts[i], o = pts[Math.min(i + 1, n)], pr = pts[Math.max(i - 1, 0)]; const dx = o[0] - pr[0], dy = o[1] - pr[1], d = Math.hypot(dx, dy) || 1; ctx.lineTo(q[0] + dy / d * q[2], q[1] - dx / d * q[2]); }
      ctx.closePath();
    };
    // dim left path
    const bs = [cx, fork[1] + unit * 0.07];
    // trunk
    ribbon([cx, h + 4], [cx, lerp(fork[1], h, 0.5)], fork, unit * 0.2, unit * 0.075, 1);
    ctx.fillStyle = 'rgb(70,64,92)'; ctx.fill();
    ribbon(bs, [lerp(fork[0], L[0], 0.35), lerp(fork[1], L[1], 0.75)], L, unit * 0.06, unit * 0.008, reveal);
    const lgr = ctx.createLinearGradient(bs[0], bs[1], L[0], L[1]);
    lgr.addColorStop(0, 'rgb(70,64,92)'); lgr.addColorStop(0.3, 'rgb(60,60,76)'); lgr.addColorStop(1, 'rgb(48,50,62)');
    ctx.fillStyle = lgr; ctx.fill();
    // bright right path
    ribbon(bs, [lerp(fork[0], Rt[0], 0.35), lerp(fork[1], Rt[1], 0.75)], Rt, unit * 0.06, unit * 0.008, reveal);
    const rg = ctx.createLinearGradient(fork[0], fork[1], Rt[0], Rt[1]);
    rg.addColorStop(0, 'rgb(70,64,92)'); rg.addColorStop(0.3, 'rgb(170,130,96)'); rg.addColorStop(1, 'rgb(255,226,170)');
    ctx.fillStyle = rg; ctx.fill();
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = rgba(GOLD, 0.1); ctx.fill(); ctx.restore();
    // traveller standing at the fork, seen from behind; rim-lit by the bright path, cool fill from the dim one
    const figH = unit * (portrait ? 0.27 : 0.2);
    const figY = portrait ? fork[1] + unit * 0.28 : lerp(fork[1], h, 0.42);
    FX.glow(ctx, cx, figY - figH * 0.5, figH * 0.9, GOLD, 0.1);
    litFigure(ctx, cx, figY, figH, 'stand', { color: [64, 60, 88], rim: [255, 222, 168], fill: [170, 160, 220], fillA: 0.22, light: [1, -0.8], halo: 0.22 });
    // labels: light text on a soft dark halo, sitting just above each path end
    const left = String(prm(p).left || ''), right = String(prm(p).right || '');
    if (lab > 0.01) {
      const label = (str, x, y, col, glowCol) => {
        let fs = unit * (portrait ? 0.085 : 0.072);
        ctx.save(); ctx.font = `600 ${fs}px Inter`;
        const tw = ctx.measureText(str).width; ctx.restore();
        const maxW = w * 0.44;
        if (tw > maxW) fs *= maxW / tw;
        const half = Math.min(tw, maxW) / 2;
        const xx = clamp(x, half + unit * 0.04, w - half - unit * 0.04);
        ctx.save(); ctx.globalAlpha = lab;
        ctx.font = `600 ${fs}px Inter`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.shadowColor = 'rgba(4,4,12,0.95)'; ctx.shadowBlur = fs * 0.5; ctx.fillStyle = 'rgba(4,4,12,0.9)';
        ctx.fillText(str, xx, y); ctx.fillText(str, xx, y);
        ctx.shadowColor = rgba(glowCol, 0.6); ctx.shadowBlur = fs * 0.35; ctx.fillStyle = rgba(col);
        ctx.fillText(str, xx, y);
        ctx.restore();
      };
      const ly = hy - unit * 0.075;
      if (left) label(left, L[0] + unit * 0.04, ly, [226, 226, 244], [150, 150, 210]);
      if (right) label(right, Rt[0] - unit * 0.04, ly, [255, 240, 210], AMBER);
    }
  },
};

// ---------------------------------------------------------------- breathing_space
const breathing_space = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h), cx = w / 2, cy = h / 2;
    const k = U.easeInOut((p.u - 0.06) / 0.72);
    FX.bg(ctx, w, h, mix([16, 8, 20], NIGHT_T, k), mix([30, 12, 28], [22, 30, 58], k));
    const breath = Math.sin(p.t * 0.75);
    const R = unit * lerp(0.07, 0.3, k) * (1 + 0.07 * breath * k);
    const col = mix([230, 80, 100], GOLD, k);
    FX.glow(ctx, cx, cy, R * 2.4 + unit * 0.1, mix(CRIMSON, AMBER, k), 0.25 + 0.05 * breath * k);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineJoin = 'round';
    for (let s = 0; s < 3; s++) {
      const ph = s * TAU / 3;
      ctx.beginPath();
      const n = 120;
      for (let i = 0; i <= n; i++) {
        const t = (i / n) * TAU;
        // tangled trefoil knot projection, relaxing into a circle
        const kx = Math.sin(t + ph) + 2 * Math.sin(2 * t + ph * 0.5);
        const ky = Math.cos(t + ph) - 2 * Math.cos(2 * t + ph * 0.5);
        const wob = Math.sin(t * 7 + p.t * 0.6 + s) * 0.12 * (1 - k);
        const x = lerp(kx / 3 * (1 + wob), Math.cos(t + ph * 0.2), k) * R;
        const y = lerp(ky / 3 * (1 + wob), Math.sin(t + ph * 0.2), k) * R * lerp(1, 0.96 + 0.04 * s, k);
        const rr = 1 + k * 0.06 * s;
        if (i === 0) ctx.moveTo(cx + x * rr, cy + y * rr); else ctx.lineTo(cx + x * rr, cy + y * rr);
      }
      ctx.strokeStyle = rgba(col, 0.12); ctx.lineWidth = unit * lerp(0.035, 0.045, k); ctx.stroke();
      ctx.strokeStyle = rgba(shade(col, 0.4), 0.7); ctx.lineWidth = Math.max(1.5, unit * 0.006); ctx.stroke();
    }
    ctx.restore();
    // calm motes drift outward once it opens
    if (k > 0.3) {
      const rnd = U.rng(p.seed + 5);
      for (let i = 0; i < 24; i++) {
        const a = rnd() * TAU, f = (rnd() + p.t * 0.05) % 1;
        const rr = R * 1.2 + f * unit * 0.5;
        FX.glow(ctx, cx + Math.cos(a) * rr, cy + Math.sin(a) * rr, unit * 0.012, GOLD, 0.4 * smooth((k - 0.3) / 0.4) * (1 - f));
      }
    }
    // walls of the cramped space recede
    FX.vignette(ctx, w, h, lerp(0.9, 0.3, k));
  },
};

// ---------------------------------------------------------------- face_the_shadow
const face_the_shadow = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h);
    const portrait = h > w * 1.3;
    FX.bg(ctx, w, h, [8, 7, 20], [24, 20, 44]);
    const groundY = portrait ? h * 0.66 : h * 0.88;
    const gr = ctx.createLinearGradient(0, groundY, 0, h);
    gr.addColorStop(0, 'rgb(22,18,38)'); gr.addColorStop(1, 'rgb(8,6,16)');
    ctx.fillStyle = gr; ctx.fillRect(0, groundY, w, h - groundY);
    const run = 1 - smooth((p.u - 0.18) / 0.16);       // running -> stopped
    const turn = U.easeInOut((p.u - 0.32) / 0.14);      // turning around
    const soften = smooth((p.u - 0.48) / 0.37);         // shadow softens
    // shadow, looming from the left
    // scaled so the whole shadow (head to feet, reaching arm) stays inside the frame
    const shH = Math.min(unit * lerp(0.78, 0.68, soften) * (portrait ? 1.15 : 1), groundY * 0.8);
    const shX = w * (portrait ? 0.3 : 0.27);
    const shCol = mix([52, 18, 60], [86, 70, 128], soften);
    const shA = lerp(0.97, 0.55, soften);
    FX.glow(ctx, shX, groundY - shH * 0.5, shH * 0.8, [20, 6, 24], 0, false);
    const dark = ctx.createRadialGradient(shX, groundY - shH * 0.55, 0, shX, groundY - shH * 0.55, shH * 0.75);
    dark.addColorStop(0, rgba(mix([30, 8, 36], [70, 60, 110], soften), 0.7 * shA)); dark.addColorStop(1, 'rgba(10,6,20,0)');
    ctx.fillStyle = dark; ctx.fillRect(0, 0, w, h);
    const shPose = blendPose(FX.FIG_POSES.reach, FX.FIG_POSES.stand, soften);
    shPose.lean = lerp(0.18, 0, soften);
    shPose.head = lerp(0.15, 0.1, soften);
    // the shadow faces the small figure of light (reaching toward it); its edge catches that light as it softens
    litFigure(ctx, shX, groundY + unit * 0.01, shH, shPose, {
      facing: -1, color: mix([30, 18, 44], shCol, shA), rim: mix([170, 110, 200], GOLD, soften), rimA: 0.45 + 0.4 * soften,
      fill: GOLD, fillA: 0.06 + 0.12 * soften, light: [1, -0.35], halo: 0.18, rimW: 0.01,
    });
    // the figure of light
    const fx0 = w * 0.6, fx1 = w * 0.72;
    const fx = lerp(fx0, fx1, 1 - run * run) + run * 0; // decelerates to a stop
    const runPhase = p.t * 0.9 * run + 0.25;
    const walkP = FX.figPose('walk', runPhase);
    const fpose = blendPose(blendPose(FX.FIG_POSES.stand, walkP, run * 1.3 > 1 ? 1 : run * 1.3), FX.FIG_POSES.stand, 0);
    if (run > 0) fpose.lean = lerp(0, 0.18, run);
    let facing = lerp(1, -1, turn);
    if (Math.abs(facing) < 0.18) facing = facing < 0 ? -0.18 : 0.18;
    const figH = unit * 0.3;
    FX.glow(ctx, fx, groundY - figH * 0.5, figH * 1.4, GOLD, 0.22 + 0.15 * soften);
    FX.figure(ctx, fx, groundY, figH, fpose, { color: [255, 230, 180], facing, glow: [255, 220, 160], glowA: 0.3 });
    // warm light reaching onto the shadow once faced
    if (soften > 0) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const lg = ctx.createRadialGradient(fx, groundY - figH * 0.5, 0, fx, groundY - figH * 0.5, Math.abs(fx - shX) * 1.3);
      lg.addColorStop(0, rgba(GOLD, 0.16 * soften)); lg.addColorStop(1, rgba(GOLD, 0));
      ctx.fillStyle = lg; ctx.fillRect(0, 0, w, h);
      ctx.restore();
    }
    // reflection on the ground
    FX.glow(ctx, fx, groundY + unit * 0.01, figH * 0.5, GOLD, 0.2);
  },
};

// ---------------------------------------------------------------- teach_hands
function forearm(ctx, wx, wy, ang, len, wd, col, edge, sleeve) {
  // wrist at (wx,wy), arm extends opposite the fingers (ang 0 = fingers up => arm down); len should carry it
  // past the frame edge so no cut end is visible. Soft edge, no outline. sleeve: {col, at (px from wrist)}
  const dx = -Math.sin(ang), dy = Math.cos(ang);
  const nx = Math.cos(ang), ny = Math.sin(ang);
  const ex = wx + dx * len, ey = wy + dy * len;
  const wE = wd * (0.42 + 0.0006 * len / (wd || 1) * 0 + 0.2 * Math.min(1, len / (wd * 3)));
  ctx.beginPath();
  ctx.moveTo(wx + nx * wd * 0.42, wy + ny * wd * 0.42);
  ctx.quadraticCurveTo(wx + nx * wd * 0.62 + dx * len * 0.3, wy + ny * wd * 0.62 + dy * len * 0.3, ex + nx * wE, ey + ny * wE);
  ctx.lineTo(ex - nx * wE, ey - ny * wE);
  ctx.quadraticCurveTo(wx - nx * wd * 0.6 + dx * len * 0.3, wy - ny * wd * 0.6 + dy * len * 0.3, wx - nx * wd * 0.42, wy - ny * wd * 0.42);
  ctx.closePath();
  const g = ctx.createLinearGradient(wx - nx * wd, wy - ny * wd, wx + nx * wd, wy + ny * wd);
  g.addColorStop(0, rgba(col)); g.addColorStop(1, rgba(edge));
  ctx.fillStyle = g; ctx.fill();
  if (sleeve) {
    ctx.save(); ctx.clip();
    const sx = wx + dx * sleeve.at, sy = wy + dy * sleeve.at;
    const sg = ctx.createLinearGradient(sx - nx * wd, sy - ny * wd, sx + nx * wd, sy + ny * wd);
    sg.addColorStop(0, rgba(shade(sleeve.col, 0.25))); sg.addColorStop(1, rgba(shade(sleeve.col, -0.3)));
    ctx.fillStyle = sg;
    ctx.beginPath();
    ctx.moveTo(sx + nx * wd * 2, sy + ny * wd * 2); ctx.lineTo(sx - nx * wd * 2, sy - ny * wd * 2);
    ctx.lineTo(sx - nx * wd * 2 + dx * len, sy - ny * wd * 2 + dy * len); ctx.lineTo(sx + nx * wd * 2 + dx * len, sy + ny * wd * 2 + dy * len);
    ctx.closePath(); ctx.fill();
    ctx.restore();
    // cuff: soft fold shadow on the skin just above the sleeve edge
    ctx.save(); ctx.strokeStyle = rgba(shade(sleeve.col, -0.5), 0.35); ctx.lineWidth = wd * 0.06; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(sx + nx * wd * 0.55, sy + ny * wd * 0.55); ctx.lineTo(sx - nx * wd * 0.55, sy - ny * wd * 0.55); ctx.stroke(); ctx.restore();
  }
}
function flame(ctx, x, y, s, t, a) {
  if (s < 1 || a <= 0) return;
  FX.glow(ctx, x, y - s * 0.5, s * 5, AMBER, 0.45 * a);
  const sway = Math.sin(t * 2.1) * 0.12 + Math.sin(t * 3.3) * 0.05;
  const layer = (sc, c, al) => {
    ctx.fillStyle = rgba(c, al * a);
    ctx.beginPath();
    ctx.moveTo(x, y + s * 0.35 * sc);
    ctx.bezierCurveTo(x - s * 0.55 * sc, y + s * 0.3 * sc, x - s * 0.5 * sc, y - s * 0.6 * sc, x + sway * s, y - s * 1.6 * sc);
    ctx.bezierCurveTo(x + s * 0.5 * sc, y - s * 0.6 * sc, x + s * 0.55 * sc, y + s * 0.3 * sc, x, y + s * 0.35 * sc);
    ctx.fill();
  };
  layer(1, [255, 150, 60], 0.9); layer(0.72, [255, 210, 120], 0.95); layer(0.42, [255, 250, 225], 1);
}
const teach_hands = {
  draw(ctx, w, h, p) {
    const unit = Math.min(w, h);
    const portrait = h > w * 1.3;
    nightBg(ctx, w, h, p, Math.round(w * h / 14000));
    const hs = unit * (portrait ? 0.46 : 0.46);          // hand length px
    const cx = w * 0.5, wy = portrait ? h * 0.6 : h * 0.82;
    const guide = U.easeInOut((p.u - 0.04) / 0.45);
    const cupK = U.easeInOut((p.u - 0.15) / 0.45);
    const flameK = smooth((p.u - 0.5) / 0.3);
    const B = 1 + 0.02 * Math.sin(p.t * 0.8);
    // the guiding hand gently tilts the human hand into a cup, the two moving together
    const ang = lerp(-0.12, -0.3, guide);
    const humanX = cx - unit * (portrait ? 0.14 : 0.1) + unit * 0.02 * guide, humanY = wy - unit * 0.02 * guide;
    // hand of light: comes in from the lower right, its fingertips settle against the outer edge of the human hand
    const gAng = lerp(-0.15, -0.5, guide);
    const gx = humanX + hs * lerp(1.05, 0.72, guide), gy = humanY + hs * lerp(0.4, 0.16, guide);
    FX.glow(ctx, gx - hs * 0.3, gy - hs * 0.5, hs * 1.2, CYAN, 0.2);
    const gPose = {
      curl: [0.05, 0.03, 0.05, 0.08].map((c, i) => lerp(c, [0.22, 0.2, 0.24, 0.3][i], guide)),
      spread: 0.05, thumb: 0.45, thumbCurl: 0.2,
    };
    ctx.save(); ctx.globalAlpha = 0.78;
    forearm(ctx, gx, gy, gAng, h, hs * 0.5 * B, [128, 214, 242], [70, 150, 200]);
    FX.hand(ctx, gx, gy, gAng, hs * 1.05 * B, gPose, { skin: [150, 228, 252], shadow: [70, 160, 210], outline: [120, 205, 240], mirror: true });
    ctx.restore();
    // human hand: open -> cupped, palm toward viewer, sleeve covering the forearm (no cut-off wrist)
    const pose = {
      curl: [0.05, 0.03, 0.05, 0.08].map((c, i) => lerp(c, [0.38, 0.35, 0.4, 0.46][i], cupK)),
      spread: lerp(0.16, 0.03, cupK), thumb: lerp(0.55, 0.42, cupK), thumbCurl: lerp(0.1, 0.28, cupK),
    };
    forearm(ctx, humanX, humanY, ang, h, hs * 0.48, [200, 146, 114], [140, 92, 74], { col: [62, 66, 104], at: hs * 0.32 });
    FX.hand(ctx, humanX, humanY, ang, hs, pose, { outline: [170, 116, 90] });
    // contact: the light's fingertips touch the human hand; light washes over it from that side
    const tipX = gx + Math.sin(gAng) * hs * 0.95, tipY = gy - Math.cos(gAng) * hs * 0.95;
    FX.glow(ctx, tipX, tipY, hs * 0.35, CYAN, 0.25 * guide);
    FX.glow(ctx, humanX + hs * 0.1, humanY - hs * 0.45, hs * 0.6, CYAN, 0.1 * guide);
    // the small flame sits in the cupped palm
    const palmX = humanX + Math.sin(ang) * hs * 0.32, palmY = humanY - Math.cos(ang) * hs * 0.32;
    flame(ctx, palmX, palmY + unit * 0.02, unit * 0.075 * (0.35 + 0.65 * flameK), p.t, Math.max(0.0, flameK));
  },
};

module.exports = {
  engine_heart, bright_world, pour_into, weight_press, crack_glass, scales_balance, birth_light,
  layers_accumulate, dense_collapse, two_paths, breathing_space, face_the_shadow, teach_hands,
};
