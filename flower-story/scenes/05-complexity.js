/* ==========================================================================
   05 · Meaningful Complexity — abstract.
   We begin inside the flower's golden heart (exactly where 04 ends). A
   naturalist's notebook annotates it: the golden angle, 137.5°, and the
   Fibonacci numbers tracing its spirals. The seeds become stars; the spiral
   becomes a slowly turning galaxy — the same pattern at cosmic scale. One
   magenta knot in its arm becomes a flower standing in a vast field of
   identical grey marks; we pull back to feel the scale. Then warmth returns
   and the field resolves into the real golden forest floor: the flower, and
   the narrator sitting beside it (scene 06 dissolves in from this shot).
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 37.2;                                   // (06's TW and its 05-camera constants follow this)
  const D04 = 42;                                   // 04's duration: the heart's clock continues
  const P = Art.TOD.golden;
  const GA = Art.GOLDEN_ANGLE;
  const ez = U.ease;
  const CX = W / 2, CY = H / 2;

  /* ---------------- timeline ---------------- */
  // The notebook is brisk: 04's last line ("…the universe we live in.") ends just before the cut,
  // so the annotations are all drawn by ~4.6 s and the seeds start turning into stars at 5.4 s.
  const TL = {
    angle0: 0.4, fib0: 1.6, fibStep: 0.28, notesOut: 5.0,
    star0: 5.4, star1: 11.4,
    knot0: 15.4, knotAt: 17.55, dis0: 17.15, dis1: 18.5,
    pull0: 19.4, pull1: 28.2,
    warm0: 27.6, din0: 28.8, din1: 32.35, forest0: 29.4, real0: 32.3, real1: 34.4,
  };
  const CAPS = [
    [5.8, 10.6, 'Maybe the beauty of a flower represents a kind of acknowledgement'],
    [11.0, 14.1, 'of potentially meaningful complexity'],
    [19.0, 23.2, 'that stands out among an otherwise crowded, benign landscape'],
    [23.6, 27.8, 'that we might normally observe within our conscious awareness.'],
  ];

  /* ---------------- shared helpers (local copies; scenes may not share code) ---------------- */
  const POOL = new Map();
  function pooled(key, w, h) {
    let c = POOL.get(key);
    if (!c || c.width < w || c.height < h) {
      const nc = document.createElement('canvas');
      nc.width = Math.max(w, c ? c.width : 0); nc.height = Math.max(h, c ? c.height : 0);
      POOL.set(key, nc);
      c = nc;
    }
    return c;
  }
  /** depth-of-field layer: low-res render, two bilinear upscales (fixed amount per key) */
  function soft(ctx, key, amount, drawFn, rect = null) {
    const f = clamp(amount * 0.55, 1.5, 14);
    const kk = ctx.canvas.width / W;
    const R = rect || { x: 0, y: 0, w: W, h: H };
    const ox = R.x * kk, oy = R.y * kk;
    const w = Math.ceil((R.w * kk) / f), h = Math.ceil((R.h * kk) / f);
    const c = pooled(key + ':a', w, h);
    const x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalAlpha = 1;
    x.globalCompositeOperation = 'source-over';
    x.clearRect(0, 0, w + 1, h + 1);
    x.setTransform(new DOMMatrix().scale(1 / f, 1 / f).translate(-ox, -oy).multiply(ctx.getTransform()));
    drawFn(x);
    const c2 = pooled(key + ':b', w * 2, h * 2);
    const x2 = c2.getContext('2d');
    x2.setTransform(1, 0, 0, 1, 0, 0);
    x2.globalAlpha = 1;
    x2.globalCompositeOperation = 'copy';
    x2.imageSmoothingEnabled = true;
    x2.imageSmoothingQuality = 'low';
    x2.drawImage(c, 0, 0, w, h, 0, 0, w * 2, h * 2);
    x2.globalCompositeOperation = 'source-over';
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(c2, 0, 0, w * 2, h * 2, ox, oy, w * f, h * f);
    ctx.restore();
  }
  function boxLayer(ctx, key, bx, by, bw, bh, fn) {
    const m = ctx.getTransform();
    const x0 = Math.floor(m.a * bx + m.e), y0 = Math.floor(m.d * by + m.f);
    const w = Math.max(1, Math.ceil(m.a * bw) + 2), h = Math.max(1, Math.ceil(m.d * bh) + 2);
    const c = pooled(key, Math.ceil(w / 128) * 128, Math.ceil(h / 128) * 128);
    const x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalAlpha = 1;
    x.globalCompositeOperation = 'source-over';
    x.clearRect(0, 0, w + 2, h + 2);
    x.setTransform(m.a, m.b, m.c, m.d, m.e - x0, m.f - y0);
    fn(x);
    x.setTransform(1, 0, 0, 1, 0, 0);
    return { c, x, x0, y0, w, h };
  }
  function blitBox(ctx, L, alpha = 1, mode = 'source-over') {
    if (alpha <= 0.002) return;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha *= alpha;
    ctx.globalCompositeOperation = mode;
    ctx.drawImage(L.c, 0, 0, L.w, L.h, L.x0, L.y0, L.w, L.h);
    ctx.restore();
  }
  function rimOf(ctx, L, key, color, dx, dy, alpha) {
    if (alpha <= 0.01) return;
    const c = pooled(key, L.c.width, L.c.height);
    const x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalAlpha = 1;
    x.globalCompositeOperation = 'source-over';
    x.clearRect(0, 0, L.w + 2, L.h + 2);
    x.drawImage(L.c, 0, 0);
    x.globalCompositeOperation = 'source-in';
    x.fillStyle = color; x.fillRect(0, 0, c.width, c.height);
    x.globalCompositeOperation = 'destination-out';
    x.drawImage(L.c, dx, dy);
    x.globalCompositeOperation = 'source-over';
    blitBox(ctx, { c, x0: L.x0, y0: L.y0, w: L.w, h: L.h }, alpha, 'lighter');
  }
  function bokeh(ctx, x, y, r, color, a) {
    if (a <= 0.003) return;
    const g = ctx.createRadialGradient(x, y, r * 0.5, x, y, r);
    g.addColorStop(0, U.rgba(color, a));
    g.addColorStop(0.78, U.rgba(color, a * 0.85));
    g.addColorStop(1, U.rgba(color, 0));
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.restore();
  }
  /** integral of an inOutSine ramp from a to b (for smoothly accelerating rotation) */
  function rampInt(t, a, b) {
    if (t <= a) return 0;
    if (t >= b) return 0.5 * (b - a) + (t - b);
    const u = (t - a) / (b - a);
    return 0.5 * (t - a) - 0.5 * ((b - a) / Math.PI) * Math.sin(Math.PI * u);
  }

  /* ---------------- the golden heart (identical copy of 04's) ---------------- */
  const HEART_N = 610;
  const HEART_COL = ['#8a4508', '#9f540d', '#b26414', '#c2761c', '#cf8826'];
  const R0 = 1160;                                  // 04 ends with the heart at this radius, centred
  function heart(ctx, cx, cy, R, rot) {
    const c = R / Math.sqrt(HEART_N + 6);
    const m = ctx.getTransform();
    const cw = ctx.canvas.width, ch = ctx.canvas.height;
    const sc = Math.hypot(m.a, m.b);
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 1.04);
    g.addColorStop(0, '#b4600e'); g.addColorStop(0.2, '#d98c25'); g.addColorStop(0.62, '#f2af30'); g.addColorStop(1, '#ffc23d');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, cy, R * 1.04, 0, TAU); ctx.fill();
    const xs = [], ys = [], rs = [], bs = [];
    const pad = c * sc * 1.2;
    for (let i = 1; i <= HEART_N; i++) {
      const a = i * GA + rot, r = c * Math.sqrt(i);
      const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r;
      const dx = m.a * x + m.c * y + m.e, dy = m.b * x + m.d * y + m.f;
      if (dx < -pad || dx > cw + pad || dy < -pad || dy > ch + pad) continue;
      xs.push(x); ys.push(y);
      rs.push(c * 0.6 * (0.6 + 0.4 * Math.min(1, i / 34)));
      bs.push(Math.min(4, Math.floor(Math.sqrt(i / HEART_N) * 5)));
    }
    const n = xs.length;
    const detail = sc * c;
    if (detail > 5) {
      ctx.fillStyle = 'rgba(88,38,4,0.3)';
      ctx.beginPath();
      for (let k = 0; k < n; k++) { const rr = rs[k] * 1.12, x = xs[k] + c * 0.07, y = ys[k] + c * 0.09; ctx.moveTo(x + rr, y); ctx.arc(x, y, rr, 0, TAU); }
      ctx.fill();
    }
    for (let b = 0; b < 5; b++) {
      ctx.fillStyle = HEART_COL[b];
      ctx.beginPath();
      for (let k = 0; k < n; k++) { if (bs[k] !== b) continue; ctx.moveTo(xs[k] + rs[k], ys[k]); ctx.arc(xs[k], ys[k], rs[k], 0, TAU); }
      ctx.fill();
    }
    if (detail > 4) {
      ctx.fillStyle = 'rgba(255,224,146,0.5)';
      ctx.beginPath();
      for (let k = 0; k < n; k++) { const rr = rs[k] * 0.36, x = xs[k] - rs[k] * 0.32, y = ys[k] - rs[k] * 0.36; ctx.moveTo(x + rr, y); ctx.arc(x, y, rr, 0, TAU); }
      ctx.fill();
    }
    Art.glow(ctx, cx, cy, R * 0.55, '#ffd98a', 0.22);
  }
  /** the heart's rotation: continues 04's clock (t*0.05), then slowly gathers speed */
  const rotAt = (t) => (D04 + t) * 0.05 + 0.11 * rampInt(t, TL.star0 - 1, TL.star1 + 2);

  /* ---------------- the galaxy (same arms for the texture and the seed-stars) ---------------- */
  const GTEX = 1024, GRAD = 480;                    // texture size, disc radius in texture px
  const ARM_K = 3.2, ARM_R0 = 70, ARM_T0 = 0.6;
  const armTheta = (r) => ARM_T0 + ARM_K * Math.log(Math.max(8, r) / ARM_R0);
  const wrapPI = (a) => { a = (a + Math.PI) % TAU; if (a < 0) a += TAU; return a - Math.PI; };
  /** 0..1: how close a disc point (texture radius r, angle a) lies to a spiral arm */
  function armness(r, a) {
    const d = wrapPI(a - armTheta(r));
    const d2 = Math.abs(d) > Math.PI / 2 ? Math.PI - Math.abs(d) : Math.abs(d);   // two arms, π apart
    return Math.exp(-(d2 * d2) / (2 * 0.42 * 0.42));
  }
  const KNOT = { r: 318, a: armTheta(318) + 0.06 };  // the one magenta knot we fly into
  const GALAXY = (() => {
    const c = document.createElement('canvas');
    c.width = c.height = GTEX;
    const x = c.getContext('2d');
    const r = U.rng(5150);
    const o = GTEX / 2;
    x.translate(o, o);
    let g = x.createRadialGradient(0, 0, 0, 0, 0, GRAD * 1.05);
    g.addColorStop(0, 'rgba(255,236,196,0.75)'); g.addColorStop(0.1, 'rgba(255,206,150,0.35)');
    g.addColorStop(0.35, 'rgba(150,150,255,0.10)'); g.addColorStop(1, 'rgba(90,100,220,0)');
    x.fillStyle = g; x.fillRect(-o, -o, GTEX, GTEX);
    x.globalCompositeOperation = 'lighter';
    // arm haze
    for (let arm = 0; arm < 2; arm++) {
      for (let i = 0; i < 170; i++) {
        const rr = 40 + Math.pow(r(), 0.85) * (GRAD - 40);
        const th = armTheta(rr) + arm * Math.PI + (r() - 0.5) * 0.55;
        const px = Math.cos(th) * rr, py = Math.sin(th) * rr;
        const rad = 16 + r() * 34 * (0.6 + rr / GRAD);
        const gg = x.createRadialGradient(px, py, 0, px, py, rad);
        const col = rr < 140 ? '255,214,170' : r() < 0.7 ? '140,165,255' : '200,170,255';
        gg.addColorStop(0, `rgba(${col},${0.09 + r() * 0.06})`); gg.addColorStop(1, `rgba(${col},0)`);
        x.fillStyle = gg; x.fillRect(px - rad, py - rad, rad * 2, rad * 2);
      }
    }
    // dark dust lanes on the inner edge of each arm
    x.globalCompositeOperation = 'source-over';
    for (let arm = 0; arm < 2; arm++) {
      x.strokeStyle = 'rgba(6,6,20,0.35)'; x.lineCap = 'round';
      for (let k = 0; k < 3; k++) {
        x.lineWidth = 5 + k * 4;
        x.globalAlpha = 0.35 / (k + 1);
        x.beginPath();
        for (let rr = 70; rr < GRAD * 0.9; rr += 6) {
          const th = armTheta(rr) + arm * Math.PI - 0.22;
          const px = Math.cos(th) * rr, py = Math.sin(th) * rr;
          rr > 70 ? x.lineTo(px, py) : x.moveTo(px, py);
        }
        x.stroke();
      }
    }
    x.globalAlpha = 1;
    x.globalCompositeOperation = 'lighter';
    // stars, crowded along the arms
    for (let i = 0; i < 3600; i++) {
      const rr = Math.sqrt(r()) * GRAD;
      let th;
      if (r() < 0.72) th = armTheta(rr) + (r() < 0.5 ? 0 : Math.PI) + (r() + r() + r() - 1.5) * 0.55;
      else th = r() * TAU;
      const px = Math.cos(th) * rr, py = Math.sin(th) * rr;
      const s = 0.5 + Math.pow(r(), 3) * 1.6;
      const warm = rr < 150 ? 1 - rr / 150 : 0;
      x.fillStyle = warm > 0.3 ? `rgba(255,${226 + (r() * 20) | 0},${180 + (r() * 30) | 0},${0.5 + r() * 0.5})` : `rgba(${200 + (r() * 40) | 0},${215 + (r() * 30) | 0},255,${0.35 + r() * 0.6})`;
      x.beginPath(); x.arc(px, py, s, 0, TAU); x.fill();
    }
    // pink star-forming knots along the arms
    for (let i = 0; i < 30; i++) {
      const rr = 130 + r() * 300;
      const th = armTheta(rr) + (r() < 0.5 ? 0 : Math.PI) + (r() - 0.5) * 0.2;
      const px = Math.cos(th) * rr, py = Math.sin(th) * rr;
      const rad = 4 + r() * 7;
      const gg = x.createRadialGradient(px, py, 0, px, py, rad * 2.4);
      gg.addColorStop(0, 'rgba(255,130,190,0.55)'); gg.addColorStop(1, 'rgba(255,90,160,0)');
      x.fillStyle = gg; x.fillRect(px - rad * 2.4, py - rad * 2.4, rad * 4.8, rad * 4.8);
    }
    // bright core
    g = x.createRadialGradient(0, 0, 0, 0, 0, 120);
    g.addColorStop(0, 'rgba(255,248,230,0.95)'); g.addColorStop(0.25, 'rgba(255,224,170,0.5)'); g.addColorStop(1, 'rgba(255,190,120,0)');
    x.fillStyle = g; x.fillRect(-120, -120, 240, 240);
    return c;
  })();
  /** a quiet deep-space backdrop: stars + faint nebula */
  const SPACE = (() => {
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    const x = c.getContext('2d');
    const r = U.rng(808);
    const g = x.createRadialGradient(W * 0.5, H * 0.5, 0, W * 0.5, H * 0.5, W * 0.7);
    g.addColorStop(0, '#0c1030'); g.addColorStop(0.6, '#060819'); g.addColorStop(1, '#020309');
    x.fillStyle = g; x.fillRect(0, 0, W, H);
    x.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 9; i++) {
      const px = r() * W, py = 140 + r() * 800, rad = 160 + r() * 320;
      const gg = x.createRadialGradient(px, py, 0, px, py, rad);
      const col = r() < 0.5 ? '90,60,160' : '40,90,150';
      gg.addColorStop(0, `rgba(${col},0.10)`); gg.addColorStop(1, `rgba(${col},0)`);
      x.fillStyle = gg; x.fillRect(px - rad, py - rad, rad * 2, rad * 2);
    }
    for (let i = 0; i < 900; i++) {
      const px = r() * W, py = r() * H, m = r();
      x.fillStyle = `rgba(${215 + (r() * 40) | 0},${220 + (r() * 35) | 0},255,${0.2 + m * 0.7})`;
      x.beginPath(); x.arc(px, py, 0.5 + m * m * 1.6, 0, TAU); x.fill();
    }
    return c;
  })();

  /* ---------------- per-seed constants for the morph ---------------- */
  const SEEDS = [];
  for (let i = 1; i <= HEART_N; i++) {
    const rho = Math.sqrt(i / (HEART_N + 6));
    const phi = i * GA;
    const B = armness(rho * GRAD, phi);
    const hsh = U.hash(i, 71);
    const cls = rho < 0.24 ? 1 : hsh < 0.62 ? 0 : hsh < 0.88 ? 1 : 2;   // 0 blue-white, 1 warm white, 2 gold
    SEEDS.push({ i, rho, phi, B, cls, band: Math.min(4, Math.floor(Math.sqrt(i / HEART_N) * 5)), hs: 0.6 * (0.6 + 0.4 * Math.min(1, i / 34)), ss: 0.7 + U.hash(i, 72) * 1.3 });
  }
  const STAR_COL = ['#dfe8ff', '#fff1d8', '#ffd58f'];
  const BRIGHT = SEEDS.filter((s) => s.B > 0.55 && U.hash(s.i, 73) < 0.32);

  /** galaxy view at time t: centre, disc radius (screen), inclination cos, position angle, rotation */
  function galaxyView(t) {
    const u = ez(t, TL.star0 + 0.6, TL.star1, 'inOutSine');
    const R = Math.exp(lerp(Math.log(R0), Math.log(380), u));
    const tilt = ez(t, TL.star0 + 2.4, TL.star1 + 1, 'inOutSine');
    const v = { x: CX, y: CY + 6 * u, R, ci: lerp(1, 0.56, tilt), pa: -0.42 * tilt, rot: rotAt(t) };
    // a slow orbit while it turns (the disc tips and swings a little), then the push toward one magenta knot
    const orb = ez(t, TL.star1 - 1, TL.knot0 + 1, 'inOutSine');
    v.R *= 1 + 0.07 * orb;
    v.ci -= 0.07 * orb;
    v.pa -= 0.12 * orb;
    v.x += 34 * orb;
    const kp = ez(t, TL.knot0, TL.knotAt, 'inOutSine');
    const kz = ez(t, TL.knot0, TL.dis1 + 0.3, 'inSine');
    if (kz > 0) {
      v.R *= Math.exp(Math.log(3.2) * kz);
      const k = galaxyPoint(v, KNOT.r / GRAD, KNOT.a);
      const tg = fieldFlowerHead(t);
      v.x += (tg.x - k.x) * kp;
      v.y += (tg.y - k.y) * kp;
    }
    return v;
  }
  /** disc point (rho 0..1, angle in the disc) → screen */
  function galaxyPoint(v, rho, a) {
    const ang = a + v.rot;
    const px = Math.cos(ang) * rho * v.R, py = Math.sin(ang) * rho * v.R * v.ci;
    const c = Math.cos(v.pa), s = Math.sin(v.pa);
    return { x: v.x + px * c - py * s, y: v.y + px * s + py * c };
  }

  /* ---------------- the notebook ---------------- */
  const INK = '#fff4dc', INK_SHADOW = 'rgba(60,24,0,0.85)';
  const FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55];
  const FIB_TXT = FIB.join(' · ');
  // one parastichy per family: seeds i0, i0+F, i0+2F, ... over the radii where that family is visible
  const SPIRALS = (() => {
    const ref = rotAt(5);
    const c = R0 / Math.sqrt(HEART_N + 6);
    const want = { 5: -2.1, 8: 2.45, 13: -0.62, 21: 2.62, 34: 0.1 };
    const out = [];
    for (const F of [5, 8, 13, 21, 34]) {
      const iMin = Math.max(1, Math.round((F * F) / 8)), iMax = Math.min(HEART_N, Math.round((F * F) / 1.5));
      let best = null, bestD = 1e9;
      for (let i0 = iMin; i0 < iMin + F; i0++) {
        const chain = [];
        for (let i = i0; i <= iMax; i += F) chain.push(i);
        if (chain.length < 3) continue;
        const mid = chain[Math.floor(chain.length * 0.55)];
        const d = Math.abs(wrapPI(mid * GA + ref - want[F]));
        if (d < bestD) { bestD = d; best = chain; }
      }
      // the 13-spiral's innermost seed sits on "the golden angle" label: start that one a step further out
      if (best) out.push({ F, chain: F === 13 ? best.slice(1) : best, t0: TL.fib0 + FIB.lastIndexOf(F) * TL.fibStep });
    }
    void c;
    return out;
  })();
  function seedXY(i, R, rot) {
    const c = R / Math.sqrt(HEART_N + 6), a = i * GA + rot, r = c * Math.sqrt(i);
    return { x: CX + Math.cos(a) * r, y: CY + Math.sin(a) * r };
  }
  function notebook(ctx, t, R, rot, alpha) {
    if (alpha <= 0.01) return;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const ink = (a) => U.rgba(INK, a);
    /** stroke the current path as ink: a soft dark underlay, then the light line */
    const inkStroke = (w, a = 1) => {
      ctx.strokeStyle = U.rgba('#3c1800', 0.45 * a); ctx.lineWidth = w + 6; ctx.stroke();
      ctx.strokeStyle = ink(0.97 * a); ctx.lineWidth = w; ctx.stroke();
    };
    // a soft shade behind the written line so it reads on the seeds
    if (t > TL.fib0 - 0.3) {
      ctx.save();
      ctx.globalAlpha *= ez(t, TL.fib0 - 0.3, TL.fib0 + 0.4);
      ctx.translate(480, 222); ctx.scale(1, 0.22);
      const sg = ctx.createRadialGradient(0, 0, 0, 0, 0, 470);
      sg.addColorStop(0, 'rgba(70,28,0,0.4)'); sg.addColorStop(1, 'rgba(70,28,0,0)');
      ctx.fillStyle = sg; ctx.fillRect(-470, -470, 940, 940);
      ctx.restore();
    }
    // --- the golden angle between seed 1 and seed 2 ---
    const ka = ez(t, TL.angle0, TL.angle0 + 0.7, 'outCubic');
    if (ka > 0) {
      const a1 = GA + rot, a2 = 2 * GA + rot;
      const L = 250 * ka;
      ctx.beginPath(); ctx.moveTo(CX, CY); ctx.lineTo(CX + Math.cos(a1) * L, CY + Math.sin(a1) * L); inkStroke(3);
      ctx.beginPath(); ctx.moveTo(CX, CY); ctx.lineTo(CX + Math.cos(a2) * L, CY + Math.sin(a2) * L); inkStroke(3);
      ctx.fillStyle = ink(1);
      ctx.beginPath(); ctx.arc(CX, CY, 5, 0, TAU); ctx.fill();
      for (const i of [1, 2]) {
        const p = seedXY(i, R, rot);
        ctx.beginPath(); ctx.arc(p.x, p.y, 17, 0, TAU); inkStroke(2.4);
      }
      const kb = ez(t, TL.angle0 + 0.45, TL.angle0 + 1.25, 'inOutSine');
      if (kb > 0) {
        const rr = 118;
        ctx.beginPath(); ctx.arc(CX, CY, rr, a1, a1 + GA * kb); inkStroke(2.6);
        if (kb > 0.95) {
          const ae = a1 + GA;
          const hx = CX + Math.cos(ae) * rr, hy = CY + Math.sin(ae) * rr;
          const tx = -Math.sin(ae), ty = Math.cos(ae);
          ctx.beginPath(); ctx.moveTo(hx - tx * 14 + Math.cos(ae) * 7, hy - ty * 14 + Math.sin(ae) * 7); ctx.lineTo(hx, hy); ctx.lineTo(hx - tx * 14 - Math.cos(ae) * 7, hy - ty * 14 - Math.sin(ae) * 7); inkStroke(2.6);
        }
      }
      const am = a1 + GA / 2;
      const lx = CX + Math.cos(am) * 200, ly = CY + Math.sin(am) * 200;
      Art.hand(ctx, '137.5°', { x: lx, y: ly, size: 64, reveal: ez(t, TL.angle0 + 0.9, TL.angle0 + 1.7, 'linear'), color: INK, glow: INK_SHADOW });
      Art.hand(ctx, 'the golden angle', { x: lx + 6, y: ly + 50, size: 34, reveal: ez(t, TL.angle0 + 1.5, TL.angle0 + 2.4, 'linear'), color: U.rgba(INK, 0.85), glow: INK_SHADOW });
    }
    // --- the Fibonacci numbers, written as the spirals light up ---
    let shown = 0;
    const tot = FIB_TXT.length;
    let acc = 0;
    for (let n = 0; n < FIB.length; n++) {
      const part = (n ? ' · ' : '') + String(FIB[n]);
      const k = ez(t, TL.fib0 + n * TL.fibStep, TL.fib0 + n * TL.fibStep + 0.3, 'linear');
      shown = acc + part.length * k;
      acc += part.length;
      if (k < 1) break;
    }
    if (t > TL.fib0) {
      Art.hand(ctx, FIB_TXT, { x: 150, y: 220, size: 54, align: 'left', reveal: shown / tot, color: INK, glow: INK_SHADOW });
      const ul = ez(t, TL.fib0 + FIB.length * TL.fibStep, TL.fib0 + FIB.length * TL.fibStep + 0.6, 'inOutSine');
      if (ul > 0) {
        ctx.beginPath(); ctx.moveTo(146, 252); ctx.quadraticCurveTo(146 + 340 * ul, 258, 146 + 690 * ul, 249); inkStroke(2.2, 0.85);
      }
    }
    for (const sp of SPIRALS) {
      const k = ez(t, sp.t0, sp.t0 + 0.75, 'inOutSine');
      if (k <= 0) continue;
      const pts = sp.chain.map((i) => seedXY(i, R, rot));
      const n = pts.length - 1;
      const f = n * k, m = Math.floor(f);
      // seeds along it light up
      for (let j = 0; j <= Math.min(n, m + 1); j++) {
        const lit = clamp(f - j + 1);
        if (lit <= 0) continue;
        Art.glow(ctx, pts[j].x, pts[j].y, 34, '#fff1c4', 0.5 * lit);
        ctx.strokeStyle = ink(0.9 * lit); ctx.lineWidth = 2.8;
        ctx.beginPath(); ctx.arc(pts[j].x, pts[j].y, R / Math.sqrt(HEART_N + 6) * 0.54, 0, TAU); ctx.stroke();
      }
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let j = 1; j <= m && j <= n; j++) {
        const a = pts[j - 1], b = pts[j];
        ctx.quadraticCurveTo(a.x, a.y, (a.x + b.x) / 2, (a.y + b.y) / 2);
      }
      if (m < n) {
        const a = pts[m], b = pts[m + 1], q = f - m;
        ctx.lineTo(lerp(a.x, b.x, q), lerp(a.y, b.y, q));
      } else ctx.lineTo(pts[n].x, pts[n].y);
      inkStroke(3.8);
      // its number at the outer end (kept inside the picture)
      if (k > 0.85) {
        let e = pts[n];
        for (let j = n; j >= 0; j--) { const p = pts[j]; if (p.x > 90 && p.x < W - 90 && p.y > 200 && p.y < 890) { e = p; break; } }
        const dx = e.x - CX, dy = e.y - CY, dl = Math.hypot(dx, dy) || 1;
        const lx = clamp(e.x + (dx / dl) * 46, 70, W - 70), ly = clamp(e.y + (dy / dl) * 46, 190, 905);
        Art.hand(ctx, String(sp.F), { x: lx, y: ly, size: 56, reveal: ez(k, 0.85, 1, 'linear'), color: INK, glow: INK_SHADOW });
      }
    }
    ctx.restore();
  }

  /* ---------------- seeds → stars ---------------- */
  const MLEV = 8;
  /** per-seed morph 0..1: the heart opens into space from its centre outward (M runs 0 → ~1.05) */
  const seedM = (M, rho) => clamp((M - rho * 0.6) / 0.4);
  const morphM = (t) => 1.06 * ez(t, TL.star0, TL.star0 + 4.8, 'inOutSine');
  function seedStars(ctx, t, v, M) {
    const c = v.R / Math.sqrt(HEART_N + 6);
    const n = SEEDS.length;
    const px = new Float32Array(n), py = new Float32Array(n), pr = new Float32Array(n), pm = new Float32Array(n);
    const buckets = new Map();
    for (let k = 0; k < n; k++) {
      const s = SEEDS[k];
      const p = galaxyPoint(v, s.rho, s.phi);
      const m = seedM(M, s.rho);
      const mSize = ez(m, 0, 0.8, 'inOutSine'), mArm = ez(m, 0.3, 1, 'inOutSine');
      const star = s.ss * (0.22 + 1.6 * lerp(1, s.B, mArm)) * (v.R / 380) * 0.9;
      const rr = Math.max(0.5, lerp(c * s.hs, star, mSize));
      px[k] = p.x; py[k] = p.y; pr[k] = rr; pm[k] = m;
      if (p.x < -rr || p.x > W + rr || p.y < -rr || p.y > H + rr) { pr[k] = -1; continue; }
      const L = m <= 0 ? 0 : Math.min(MLEV - 1, 1 + Math.floor(ez(m, 0.02, 0.85, 'inOutSine') * (MLEV - 1)));
      const key = (s.band * 3 + s.cls) * MLEV + L;
      let b = buckets.get(key);
      if (!b) buckets.set(key, (b = []));
      b.push(k);
    }
    // seed shading (while they are still seeds)
    ctx.fillStyle = 'rgba(88,38,4,0.3)';
    ctx.beginPath();
    for (let k = 0; k < n; k++) {
      if (pr[k] < 0 || pm[k] > 0.35) continue;
      const rr = pr[k] * 1.12 * (1 - pm[k] / 0.35), x = px[k] + c * 0.07, y = py[k] + c * 0.09;
      if (rr < 0.4) continue;
      ctx.moveTo(x + rr, y); ctx.arc(x, y, rr, 0, TAU);
    }
    ctx.fill();
    for (const [key, list] of buckets) {
      const L = key % MLEV, bc = Math.floor(key / MLEV), cls = bc % 3, band = Math.floor(bc / 3);
      ctx.fillStyle = L === 0 ? HEART_COL[band] : U.mix(HEART_COL[band], STAR_COL[cls], L / (MLEV - 1));
      ctx.beginPath();
      for (const k of list) { ctx.moveTo(px[k] + pr[k], py[k]); ctx.arc(px[k], py[k], pr[k], 0, TAU); }
      ctx.fill();
    }
    ctx.fillStyle = 'rgba(255,224,146,0.5)';
    ctx.beginPath();
    for (let k = 0; k < n; k++) {
      if (pr[k] < 0 || pm[k] > 0.3) continue;
      const rr = pr[k] * 0.36 * (1 - pm[k] / 0.3), x = px[k] - pr[k] * 0.32, y = py[k] - pr[k] * 0.36;
      if (rr < 0.3) continue;
      ctx.moveTo(x + rr, y); ctx.arc(x, y, rr, 0, TAU);
    }
    ctx.fill();
    // stars born near the heart's centre catch light first; a few bright ones bloom
    for (const s of BRIGHT) {
      const m = seedM(M, s.rho);
      if (m < 0.6) continue;
      const p = galaxyPoint(v, s.rho, s.phi);
      if (p.x < -30 || p.x > W + 30 || p.y < 100 || p.y > 980) continue;
      Art.glow(ctx, p.x, p.y, 9 + s.ss * 6, STAR_COL[s.cls], 0.5 * ez(m, 0.6, 1) * (0.75 + 0.25 * Math.sin(t * 2 + s.i)));
    }
  }
  /** the heart's golden ground, opening from the centre into space */
  function heartBase(ctx, v, M) {
    const o = M * 1.45 - 0.42;                       // opening radius (fraction of R); fully closed while o <= -0.35
    if (o > 1.05) return;
    const stops = [[0, '#b4600e'], [0.2, '#d98c25'], [0.62, '#f2af30'], [1, '#ffc23d']];
    const colAt = (p) => { for (let i = 1; i < stops.length; i++) if (p <= stops[i][0]) { const a = stops[i - 1], b = stops[i]; return U.mix(a[1], b[1], (p - a[0]) / (b[0] - a[0])); } return stops[3][1]; };
    const g = ctx.createRadialGradient(v.x, v.y, 0, v.x, v.y, v.R * 1.04);
    const fo = ez(M, 0.12, 0.7, 'inOutSine');           // the rim dissolves as well: no hard coin edge
    for (let i = 0; i <= 12; i++) {
      const p = i / 12;
      g.addColorStop(p, U.rgba(colAt(p), U.smooth((p - o) / 0.35) * (1 - fo * U.smooth((p - 0.6) / 0.44))));
    }
    ctx.save();
    ctx.translate(v.x, v.y); ctx.rotate(v.pa); ctx.scale(1, v.ci); ctx.translate(-v.x, -v.y);
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(v.x, v.y, v.R * 1.04, 0, TAU); ctx.fill();
    ctx.restore();
  }
  function drawGalaxy(ctx, t, v, a) {
    if (a <= 0.003) return;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.globalCompositeOperation = 'lighter';
    ctx.translate(v.x, v.y);
    ctx.rotate(v.pa);
    ctx.scale(1, v.ci);
    ctx.rotate(v.rot);
    const s = v.R / GRAD;
    ctx.scale(s, s);
    ctx.drawImage(GALAXY, -GTEX / 2, -GTEX / 2);
    ctx.restore();
  }

  /* ---------------- the field of sameness ---------------- */
  const HZ = 318, FOC = 1000;                       // horizon (screen y), focal length
  const GS = 0.5, MH = 0.32, MW = 0.05;             // grid spacing, blade height/width (world)
  const FH = 1.45;                                  // the flower's height (world)
  /** screen position of the field flower's head at time t */
  function fieldFlowerHead(t) {
    const fc = fieldCam(t);
    const base = HZ + (FOC * fc.h) / fc.D, hgt = (FOC * FH) / fc.D;
    return { x: CX - (FOC * fc.X) / fc.D, y: base - hgt * (150 / 190) };
  }
  /** field camera: distance to the flower D, height h, lateral offset X (world) */
  function fieldCam(t) {
    const pre = ez(t, TL.dis0, TL.pull0, 'outSine');            // drifting in as the galaxy hands over
    const pb = ez(t, TL.pull0, TL.pull1, 'inOutSine');            // pulling back to reveal the scale
    const din = ez(t, TL.din0, TL.din1, 'inOutSine');             // and back down to the real flower
    const lnD = lerp(lerp(Math.log(7.2), Math.log(6), pre) + (Math.log(44) - Math.log(6)) * pb, Math.log(FINAL_FIELD.D), din);
    const Dd = Math.exp(lnD);
    const ratio = lerp(0.3, FINAL_FIELD.ratio, din);
    return { D: Dd, h: Dd * ratio, X: lerp(0, FINAL_FIELD.X, din) };
  }
  /**
   * The field: identical grey blades on a perspective grid, receding to a flat horizon.
   * warm 0..1 brings back the golden light; markA fades the marks (before the dissolve).
   */
  function fieldDraw(ctx, t, fc, warm, markA, flowerFn) {
    const { D: Dd, h, X } = fc;
    const skyTop = U.mix('#c2c2c0', '#eeb06e', warm), skyLow = U.mix('#dcdcda', '#ffe3ab', warm);
    const g0 = U.mix('#d0d0cd', '#e2cf92', warm), g1 = U.mix('#bdbdb9', U.mix(P.grass, '#d0b260', 0.45), warm), g2 = U.mix('#a9a9a5', U.mix(P.ground, P.grass, 0.4), warm);
    const sky = ctx.createLinearGradient(0, 130, 0, HZ);
    sky.addColorStop(0, skyTop); sky.addColorStop(1, skyLow);
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, HZ);
    const gr = ctx.createLinearGradient(0, HZ, 0, 941);
    // the ground starts in the sky's own colour at the horizon (no hard seam once the light warms)
    gr.addColorStop(0, skyLow); gr.addColorStop(0.12, g0); gr.addColorStop(0.3, g1); gr.addColorStop(1, g2);
    ctx.fillStyle = gr; ctx.fillRect(0, HZ, W, H - HZ);
    if (warm > 0) {
      Art.glow(ctx, 1640, HZ - 40, 900, '#ffcf7a', 0.55 * warm);
      Art.glow(ctx, 1640, HZ - 40, 260, '#fff2d2', 0.7 * warm);
    }
    const sx = (Xw, Z) => CX + (FOC * (Xw - X)) / Z;
    const sy = (Z) => HZ + (FOC * h) / Z;
    const zNear = (FOC * h) / (941 - HZ + 60);
    const zFar = Math.sqrt((FOC * h * GS) / 1.5);
    const flowerZ = Dd;
    let flowerDrawn = false;
    const k0 = Math.ceil(zNear / GS), k1 = Math.floor(zFar / GS);
    const mark = U.mix('#686866', U.mix(P.grass, '#3f5a2a', 0.35), warm), haze = U.mix(skyLow, '#ffe3ab', warm);
    const lean = 0.16;
    for (let k = k1; k >= k0; k--) {
      const Z = k * GS;
      if (!flowerDrawn && Z < flowerZ) { flowerFn(sx(0, flowerZ), sy(flowerZ), (FOC * FH) / flowerZ); flowerDrawn = true; }
      const y = sy(Z);
      if (y > 1000) continue;
      const mh = (FOC * MH) / Z, mw = Math.max(0.9, (FOC * MW) / Z);
      const fog = clamp(Math.pow(Z / (zFar * 1.05), 1.4));
      const edge = 1 - U.smooth((Z - zFar * 0.8) / (zFar * 0.2));      // the farthest rows melt away (no light band where the marks start)
      const a = markA * (1 - 0.15 * fog) * edge;
      if (a <= 0.01) continue;
      ctx.fillStyle = U.rgba(U.mix(mark, haze, fog * 0.85), a);
      const span = ((W / 2 + 40) * Z) / FOC;
      const i0 = Math.floor((X - span) / GS) - 1, i1 = Math.ceil((X + span) / GS) + 1;
      const rowOff = U.hash(k, 3) * GS;
      ctx.beginPath();
      if (mh < 6) {
        for (let i = i0; i <= i1; i++) {
          const x = sx(i * GS + rowOff * 0.5 + (U.hash(i * 31 + k, 5) - 0.5) * GS * 0.3, Z);
          ctx.rect(x - mw / 2, y - mh, mw, mh);
        }
      } else {
        const ln = mh * lean;
        for (let i = i0; i <= i1; i++) {
          const x = sx(i * GS + rowOff * 0.5 + (U.hash(i * 31 + k, 5) - 0.5) * GS * 0.3, Z);
          ctx.moveTo(x - mw * 0.5, y);
          ctx.quadraticCurveTo(x - mw * 0.25 + ln * 0.3, y - mh * 0.6, x + ln, y - mh);
          ctx.quadraticCurveTo(x + mw * 0.3 + ln * 0.35, y - mh * 0.5, x + mw * 0.5, y);
        }
      }
      ctx.fill();
    }
    if (!flowerDrawn) flowerFn(sx(0, flowerZ), sy(flowerZ), (FOC * FH) / flowerZ);
    // distance swallows the field into a soft horizon
    const yFar = sy(zFar * 0.9);
    const hz = ctx.createLinearGradient(0, HZ - 30, 0, yFar);
    hz.addColorStop(0, U.rgba(haze, 0)); hz.addColorStop(0.18, U.rgba(haze, 0.95)); hz.addColorStop(0.5, U.rgba(haze, 0.55)); hz.addColorStop(1, U.rgba(haze, 0));
    ctx.fillStyle = hz; ctx.fillRect(0, HZ - 30, W, yFar - HZ + 30);
  }

  /* ---------------- the real golden forest (as in 04) ---------------- */
  const GY = 868, GOPT = { y: GY, amp: 8, freq: 0.0021, seed: 14 };
  const FX = 1060, FY = 920, FS = 0.92, FSEED = 3;
  const MX = 748, MY = 877;
  const SUN = { x: 1720, y: 630 };
  const ROCK = { x: 1200, y: 934, w: 176, h: 96 };
  const FERN = { x: 956, y: 936, s: 1.08 };
  const ROCK_GREY = '#8a8f86', MOSS = U.mix(P.grass, P.trees[2], 0.25);
  const FERN_C1 = U.mix(P.grass, P.trees[2], 0.45), FERN_C2 = U.mix(P.grass, P.trees[2], 0.2);
  const CAM_F0 = { x: 912, y: 752, z: 1.62 }, CAM_F1 = { x: 922, y: 748, z: 1.7 };
  const camFinal = (t) => {
    const k = ez(t, TL.real1 - 0.4, D + 2, 'inSine');
    return { x: lerp(CAM_F0.x, CAM_F1.x, k), y: lerp(CAM_F0.y, CAM_F1.y, k), z: Math.exp(lerp(Math.log(CAM_F0.z), Math.log(CAM_F1.z), k)) };
  };
  // where the field flower must land so the dissolve to the real shot matches it
  const FINAL_FIELD = (() => {
    const c = CAM_F0;
    const baseY = H / 2 + (FY - c.y) * c.z, baseX = W / 2 + (FX - c.x) * c.z;
    const hgt = 190 * FS * c.z;                       // Art.flower is ~190px tall at s=1
    const Dd = (FOC * FH) / hgt;
    return { D: Dd, ratio: (baseY - HZ) / FOC, X: ((baseX - CX) * Dd) / FOC * -1 };
  })();
  /** the golden forest behind the flower spot; the summit shows through a gap in the near trees */
  const SUMMIT_P = Object.assign({}, P, { snow: U.mix(P.snow, P.summit, 0.28), summit: U.mix(P.summit, P.far, 0.3) });   // reads against the low sun
  const NEAR_TREES = [[296, 560], [418, 468], [596, 525], [790, 445], [902, 540], [1094, 498], [1216, 452], [1586, 520], [1742, 470], [1884, 548]];
  function backdrop(c, t) {
    const g = c.createLinearGradient(0, 470, 0, 880);
    g.addColorStop(0, '#d39a5e'); g.addColorStop(0.5, '#f4c684'); g.addColorStop(1, '#ffe1ab');
    c.fillStyle = g; c.fillRect(-800, 0, 3600, 1500);
    Art.glow(c, SUN.x, SUN.y, 1050, '#ffc773', 0.72);
    Art.glow(c, SUN.x, SUN.y, 300, '#fff3d2', 0.95);
    Art.summit(c, { x: 1392, y: 762, h: 182, w: 380, P: SUMMIT_P, glow: 0.8, t, flag: true });
    Art.fog(c, { y: 724, h: 110, color: '#ffdaa0', alpha: 0.42 });
    Art.forest(c, { seed: 41, y: 808, spacing: 40, hMin: 110, hMax: 176, color: U.mix(P.trees[0], '#e7b67a', 0.45), kind: 'pine', w: 0.34 });
    Art.fog(c, { y: 800, h: 170, color: '#ffd89e', alpha: 0.55 });
    const col = U.mix(P.trees[1], '#4f4128', 0.18), light = U.mix(P.trees[1], '#ffc878', 0.42);
    for (const [x, h] of NEAR_TREES) Art.pine(c, x, 866 + (U.hash(x, 3) - 0.5) * 22, h, U.shade(col, (U.hash(x, 4) - 0.5) * 0.08), { sway: 2 * U.wind(t, x, 2), light, w: 0.44 * (0.88 + U.hash(x, 5) * 0.24) });
    Art.rays(c, { x: SUN.x, y: SUN.y, angle: 2.78, spread: 0.5, count: 7, len: 1700, color: '#ffe2a8', alpha: 0.15, t, seed: 4 });
  }
  function rockOutline(ctx, x, y, w, h, seed) {
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(seed, 1) * 8, y - h);
    ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    ctx.lineTo(x + w / 2, y);
    ctx.closePath();
  }
  function rockAt(ctx) {
    const { x, y, w, h } = ROCK, seed = 7;
    ctx.fillStyle = 'rgba(30,24,10,0.25)';
    ctx.beginPath(); ctx.ellipse(x + 8, y + 2, w * 0.58, 12, 0, 0, TAU); ctx.fill();
    Art.rock(ctx, x, y, w, h, ROCK_GREY, seed);
    ctx.save();
    rockOutline(ctx, x, y, w, h, seed);
    ctx.clip();
    ctx.fillStyle = MOSS;
    ctx.beginPath();
    ctx.moveTo(x - w * 0.6, y - h * 1.2);
    ctx.lineTo(x + w * 0.6, y - h * 1.2);
    for (let i = 0; i <= 10; i++) {
      const k = 1 - i / 10;
      ctx.lineTo(x - w * 0.6 + w * 1.2 * k, y - h * (0.62 + 0.18 * Math.sin(k * 3.1)) + Math.sin(i * 2.3 + seed) * h * 0.06);
    }
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = U.shade(MOSS, 0.16);
    for (let i = 0; i < 7; i++) {
      const mx = x - w * 0.38 + i * w * 0.12, my = y - h * (0.84 + 0.1 * Math.sin(i * 1.7));
      ctx.beginPath(); ctx.arc(mx, my, 3 + U.hash(i, seed) * 4, 0, TAU); ctx.fill();
    }
    ctx.restore();
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = 'rgba(255,196,120,0.5)'; ctx.lineWidth = 5; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x - w * 0.1, y - h * 0.99); ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.0, x + w * 0.49, y - h * 0.22); ctx.stroke();
    ctx.restore();
  }
  function meFinal(t) {
    const look = U.keys(t, [[0, 0.75], [35.4, 0.75], [36.4, 0.5]]);
    return { x: MX, y: MY, look: 'me', pose: 'sit', s: 1, t, facing: 1, lean: 0.05, head: { tilt: 0.11 + 0.02 * Math.sin(t * 0.6) }, face: { smile: 0.5, lookX: 1, lookY: look } };
  }
  /**
   * Kit workaround: the beanie's pom-pom is drawn 1.3 units clear of the crown (it floats; the gap
   * grows with zoom). Seat it with a short gathered neck in the beanie colour, pom-pom on top.
   * an = Art.person anchors, o = the options it was drawn with (sitting pose: no pose lean).
   */
  const BEANIE = Art.CAST.me.hatColor, POM = U.shade(Art.CAST.me.hatColor, 0.12);
  function seatPom(ctx, an, o) {
    const S = an.scale, R = an.head.r / S;
    const rot = ((o.head && o.head.tilt) || 0) + (o.lean || 0) * 0.3;
    ctx.save();
    ctx.translate(an.head.x, an.head.y); ctx.rotate(rot); ctx.scale(S, S);
    ctx.fillStyle = BEANIE;
    // from the crown (−R−5.2 here) up into the pom-pom (bottom −R−6.5), gathered toward it
    ctx.beginPath(); ctx.moveTo(-11, -R - 2); ctx.quadraticCurveTo(-8, -R - 5, -8.5, -R - 10); ctx.lineTo(-3.5, -R - 10); ctx.quadraticCurveTo(-4, -R - 5, -1, -R - 2); ctx.closePath(); ctx.fill();
    ctx.fillStyle = POM;
    ctx.beginPath(); ctx.arc(-6, -R - 14, 7.5, 0, TAU); ctx.fill();
    ctx.restore();
  }
  function drawMe(ctx, t, o, cam) {
    ctx.fillStyle = 'rgba(30,22,10,0.24)';
    ctx.beginPath(); ctx.ellipse(o.x + 22, o.y + 2, 74, 9, 0, 0, TAU); ctx.fill();
    const L = boxLayer(ctx, 'me5', o.x - 80, o.y - 245, 260, 262, (x) => seatPom(x, Art.person(x, Object.assign({}, o, { shadow: false, glow: 0 })), o));
    blitBox(ctx, L);
    const kk = ctx.canvas.width / W;
    const d = 3.4 * cam.z * kk;
    rimOf(ctx, L, 'me5Rim', '#ffd79c', -d, d * 0.35, 0.8);
  }
  function drawRealForest(ctx, t, cam) {
    ctx.save();
    Art.cam(ctx, { x: cam.x, y: cam.y, zoom: cam.z });
    soft(ctx, 'bg5', 10, (c) => backdrop(c, t));
    for (let i = 0; i < 10; i++) {
      const bx = 380 + U.hash(i, 61) * 1150, by = 560 + U.hash(i, 62) * 220;
      bokeh(ctx, bx + Math.sin(t * 0.3 + i) * 4, by, 14 + U.hash(i, 63) * 24, i % 3 ? '#ffd9a0' : '#fff2d4', 0.14 * (0.6 + 0.4 * Math.sin(t * 0.7 + i * 1.7)));
    }
    Art.ground(ctx, Object.assign({ color: U.mix(P.ground, '#6b6a2a', 0.2), color2: P.ground2 }, GOPT));
    Art.trail(ctx, Object.assign({ color: P.trail, depth: 40 }, GOPT));
    Art.grass(ctx, { seed: 9, y: (x) => Art.groundY(x, GOPT) - 1, spacing: 9, h: 22, color: U.shade(P.grass, -0.15), color2: U.mix(P.grass, '#ffd486', 0.35), t, wind: 0.7 });
    drawMe(ctx, t, meFinal(t), cam);
    rockAt(ctx);
    Art.fern(ctx, FERN.x, FERN.y, FERN.s, FERN_C1, U.wind(t, FERN.x, 2) * 0.7);
    Art.fern(ctx, FERN.x + 44, FERN.y + 4, FERN.s * 0.64, FERN_C2, U.wind(t, FERN.x + 44, 3) * 0.7);
    Art.flower(ctx, { x: FX, y: FY, s: FS, t, seed: FSEED, face: 0.8, sway: 1, glow: 0.42 + 0.06 * Math.sin(t * 1.3) });
    Art.grass(ctx, { seed: 17, y: (x) => 946 + Math.sin(x * 0.01) * 6, spacing: 8, h: 34, color: U.shade(P.grass, -0.3), color2: U.mix(P.grass, '#ffd486', 0.15), t, wind: 1 });
    Art.motes(ctx, { seed: 12, count: 30, x0: 560, x1: 1500, y0: 580, y1: 940, t, color: '#ffe9b8', size: 1.4, drift: 9, glow: 0.8, alpha: 0.6 });
    soft(ctx, 'fg5', 13, (c) => {
      Art.grass(c, { seed: 23, y: 1018, x0: 380, x1: 760, spacing: 15, h: 110, hVar: 0.5, width: 5, color: '#2f3a1e', t, wind: 0.5 });
      Art.grass(c, { seed: 24, y: 1024, x0: 1380, x1: 1640, spacing: 16, h: 100, hVar: 0.5, width: 5, color: '#2c351c', t, wind: 0.5 });
    }, { x: 0, y: 740, w: W, h: 340 });
    ctx.restore();
    ctx.save();
    const wl = ctx.createLinearGradient(W * 0.5, 0, W, 0);
    wl.addColorStop(0, 'rgba(255,170,80,0)'); wl.addColorStop(1, 'rgba(255,170,80,0.12)');
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = wl; ctx.fillRect(W * 0.5, 0, W * 0.5, H);
    ctx.restore();
  }

  /* ---------------- the scene ---------------- */
  Film.scene({
    id: 'complexity',
    order: 5,
    title: 'Meaningful Complexity',
    duration: D,
    mood: 'cosmic',
    moods: [[0, 'cosmic'], [28.7, 'tender']],
    sfx: [
      [0.4, 'scratch', { gain: 0.3 }],          // the golden angle is drawn
      [1.4, 'chime', { gain: 0.35 }],           // "137.5°"
      [1.6, 'scratch', { gain: 0.25 }],         // the Fibonacci numbers
      [2.5, 'scratch', { gain: 0.25 }],
      [3.35, 'shimmer', { gain: 0.3 }],         // the spirals light up
      [5.4, 'swell', { gain: 0.55 }],           // seeds become stars
      [10.8, 'shimmer', { gain: 0.45 }],
      [15.6, 'whoosh', { gain: 0.35 }],
      [17.4, 'chime', { gain: 0.4 }],
      [18.8, 'wind', { gain: 0.3 }],
      [28.0, 'bloom', { gain: 0.5 }],
      [31.0, 'bird', { gain: 0.35 }],
      [34.6, 'bird', { gain: 0.4 }],
    ],
    crossIn: 0,        // 04 ends on exactly this frame (same heart, same rotation clock): a seamless cut
    fadeIn: 0,
    fadeOut: 0,
    post: (t) => {
      const space = U.fade(t, TL.star0, TL.dis1, 2.5, 1.2);
      const field = U.fade(t, TL.dis0, TL.real1, 1.2, 1.5);
      return { vignette: lerp(0.42, 0.55, space) - 0.08 * field, grain: 0.045, letterbox: 1 };
    },

    render(ctx, t) {
      const rot = rotAt(t);
      // ---- inside the golden heart: the notebook ----
      if (t < TL.star0) {
        heart(ctx, CX, CY, R0, rot);
        notebook(ctx, t, R0, rot, 1 - ez(t, TL.notesOut, TL.star0 + 0.3, 'inOutSine'));
        Art.captions(ctx, t, CAPS);
        return;
      }
      // ---- the seeds become stars; the spiral becomes a galaxy ----
      if (t < TL.dis1) {
        const v = galaxyView(t);
        const M = morphM(t);
        ctx.drawImage(SPACE, Math.sin(t * 0.05) * 10 - 10, 0, W + 20, H);
        // nearer stars drift past a little faster (depth)
        Art.stars(ctx, { seed: 77, count: 70, t, alpha: 0.85 * ez(t, TL.star0 + 1, TL.star0 + 3), x0: -200 - (t - TL.star0) * 9, x1: W + 200 - (t - TL.star0) * 9, y0: 139, y1: 941, color: '#e9efff' });
        heartBase(ctx, v, M);
        drawGalaxy(ctx, t, v, ez(t, TL.star0 + 1.6, TL.star1 + 0.4, 'inOutSine'));
        seedStars(ctx, t, v, M);
        // the heart's warm centre becomes the galaxy's core
        Art.glow(ctx, v.x, v.y, v.R * 0.55, '#ffd98a', 0.22 * (1 - ez(t, TL.star0, TL.star0 + 2)));
        Art.glow(ctx, v.x, v.y, v.R * 0.55, '#ffe6b8', 0.35 * ez(t, TL.star0 + 2, TL.star1));
        // the notebook finishes fading over the morph's first moments (the view is still the heart's until star0 + 0.6)
        if (t < TL.star0 + 0.3) notebook(ctx, t, R0, rot, 1 - ez(t, TL.notesOut, TL.star0 + 0.3, 'inOutSine'));
        // the magenta knot we fly into
        const kn = galaxyPoint(v, KNOT.r / GRAD, KNOT.a);
        const kg = ez(t, TL.star1 - 1, TL.knot0 + 1, 'inOutSine');
        const kp = ez(t, TL.knot0, TL.knotAt, 'inOutSine');
        Art.glow(ctx, kn.x, kn.y, 26 + 120 * kp, '#ff5f9e', (0.35 + 0.45 * kp) * kg);
        Art.glow(ctx, kn.x, kn.y, 8 + 30 * kp, '#ffe1ee', (0.5 + 0.4 * kp) * kg);
        // hand over to the field: it fades up beneath the galaxy
        const dk = ez(t, TL.dis0, TL.dis1, 'inOutSine');
        if (dk > 0) {
          ctx.save();
          ctx.globalAlpha = dk;
          fieldScene(ctx, t);
          ctx.restore();
          const tg = fieldFlowerHead(t);
          Art.glow(ctx, tg.x, tg.y, 140, '#ff5f9e', 0.5 * (1 - dk) * kg);
        }
        Art.captions(ctx, t, CAPS);
        return;
      }
      // ---- the field, the pull back, and warmth returning ----
      const realK = ez(t, TL.real0, TL.real1, 'inOutSine');
      if (realK > 0) drawRealForest(ctx, t, camFinal(t));
      if (realK < 1) {
        ctx.save();
        ctx.globalAlpha = 1 - realK;
        fieldScene(ctx, t);
        ctx.restore();
      }
      Art.captions(ctx, t, CAPS);
    },
  });

  function fieldScene(ctx, t) {
    const fc = fieldCam(t);
    const warm = ez(t, TL.warm0, TL.din0 + 2.6, 'inOutSine');
    const markA = 1 - ez(t, TL.real0 - 1.2, TL.real0 + 0.3, 'inOutSine');
    fieldDraw(ctx, t, fc, warm, markA, (x, y, hgt) => {
      const s = hgt / 190;
      // a soft magenta light around the one thing that stands out
      Art.glow(ctx, x, y - hgt * 0.79, Math.max(46, hgt * 0.75), '#ff6ea6', 0.34 * (1 - 0.5 * warm));
      Art.flower(ctx, { x, y, s, t, seed: FSEED, face: 0.8, sway: 1, glow: lerp(0.75, 0.42, warm) });
    });
    // the forest rises out of the haze as warmth returns
    const fa = ez(t, TL.forest0, TL.real0 + 0.8, 'inOutSine');
    const fo = 1 - ez(t, TL.real0 - 0.6, TL.real0 + 0.6, 'inOutSine');
    if (fa > 0 && fo > 0) {
      ctx.save();
      ctx.globalAlpha *= fa * fo;
      Art.forest(ctx, { seed: 41, y: HZ + 14, spacing: 22, hMin: 60 * fa, hMax: 130 * fa, color: U.mix(P.trees[0], '#f0c58a', 0.6), kind: 'pine', w: 0.34 });
      Art.forest(ctx, { seed: 44, y: HZ + 26, spacing: 34, hMin: 90 * fa, hMax: 190 * fa, color: U.mix(P.trees[1], '#e7b67a', 0.42), kind: 'pine', w: 0.36 });
      Art.fog(ctx, { y: HZ + 10, h: 120, color: '#ffe0a8', alpha: 0.55 });
      ctx.restore();
    }
  }
})();
