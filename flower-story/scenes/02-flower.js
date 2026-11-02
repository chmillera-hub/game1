/* ==========================================================================
   02 · The Flower — the walk continues from 01. A single magenta flower
   scrolls in from the right at the trail's edge. Nobody notices it but the
   one at the back. Time slows: the world drains of colour and goes soft, the
   flower stays vivid and begins to glow, pollen hangs in the air. "me" turns,
   slows, stops; the others drift on, out of focus. Push in. "I stop."
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU } = U;
  const D = 26;

  /* ---------------- shared trail layout (scenes 01–03) ---------------- */
  const GY = 870, GAMP = 16;          // ground line: Art.groundY(x, {y: 870, amp: 16, offset: worldX})
  const FOOT = 18;                    // feet stand this far below the ground line, on the trail
  const S = 0.8;                      // character scale in the wide walking shot
  const RATE = 6.0;                   // walk phase rate (rad/s) for a height-1.0 character
  // Foot travel of the kit's walk cycle per radian of phase per unit scale, at stride k.
  // (Measured from Art.person's leg rig — exact over the stance phase.)
  const KF = (k) => 72.32 * Math.sin(0.42 * k);
  const V0 = KF(1) * RATE * S;        // ≈ 141.6 px/s: the skate-free tracking speed at the ground plane
  const gOpt = (off) => ({ y: GY, amp: GAMP, offset: off });
  const CX = W / 2, CY = H / 2;
  const PIC = Art.PIC;

  /* ---------------- timing ---------------- */
  const T_DEC0 = 6.3, T_STOP = 12.3;                  // "me" (and the tracking camera) slow to a stop
  const G_KEYS = [[T_DEC0, 1], [T_STOP, 0]];           // me's speed factor
  const TAU_O = [[5.6, 1], [10.2, 0.5]];               // the others walk on, in slow motion
  const TAU_A = [[5.6, 1], [10.6, 0.14]];              // ambient time: grass, leaves, pollen all but stop
  const T_PUSH0 = 13.8, T_PUSH1 = 20.6;                // dolly in to the flower
  const ZOOM_END = 6.0;                                // trail-plane magnification at the close-up
  const CLOSE = { x: 1040, y: 640 };                   // where the flower head lands in the close-up

  /* ---------------- pure-function motion helpers ---------------- */
  // rate defined by keys [[t, r], ...], smoothstep between keys, constant outside
  function rateAt(t, keys) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const a = keys[i - 1], b = keys[i];
      if (t <= b[0]) return a[1] + (b[1] - a[1]) * U.smooth((t - a[0]) / (b[0] - a[0]));
    }
    return keys[keys.length - 1][1];
  }
  // exact integral of rateAt from 0 to t
  function rateInt(t, keys) {
    const t0 = keys[0][0];
    if (t <= t0) return keys[0][1] * t;
    let acc = keys[0][1] * t0;
    for (let i = 1; i < keys.length; i++) {
      const a = keys[i - 1], b = keys[i], T = b[0] - a[0];
      if (t <= b[0]) {
        const x = (t - a[0]) / T;
        return acc + a[1] * (t - a[0]) + (b[1] - a[1]) * T * (x * x * x - (x * x * x * x) / 2);
      }
      acc += a[1] * T + (b[1] - a[1]) * T * 0.5;
    }
    const l = keys[keys.length - 1];
    return acc + l[1] * (t - l[0]);
  }
  function simpson(f, a, b, n) {
    if (b <= a) return 0;
    n = Math.max(2, n + (n & 1));
    const h = (b - a) / n;
    let s = f(a) + f(b);
    for (let i = 1; i < n; i++) s += f(a + i * h) * (i & 1 ? 4 : 2);
    return (s * h) / 3;
  }

  // "me": steps get slower AND shorter as he stops, so his legs come together
  const strideOf = (g) => 0.2 + 0.8 * Math.pow(g, 0.6);
  const meSpeed = (u) => { const g = rateAt(u, G_KEYS); return KF(strideOf(g)) * RATE * g * S; };
  const DEC = simpson(meSpeed, T_DEC0, T_STOP, 1200);
  const CAM_END = V0 * T_DEC0 + DEC;
  // The tracking camera follows me exactly: his feet never slide and he holds x = 540.
  function camXAt(t) {
    if (t <= T_DEC0) return V0 * t;
    if (t >= T_STOP) return CAM_END;
    return V0 * T_DEC0 + simpson(meSpeed, T_DEC0, t, Math.ceil((t - T_DEC0) * 120));
  }
  // land me's last step on double support (both knees straight) so he settles into 'stand'
  const ME_PH0 = (((Math.PI / 2 - RATE * (T_DEC0 + 0.5 * (T_STOP - T_DEC0))) % Math.PI) + Math.PI) % Math.PI;

  /* ---------------- cast & set ---------------- */
  const ME_X = 540;
  const CREW = [
    { k: 'h1', x: 1250, ph: 0.4 },
    { k: 'h2', x: 1080, ph: 2.3 },
    { k: 'h3', x: 910, ph: 4.1 },
    { k: 'h4', x: 740, ph: 5.6 },
  ];
  const GAP = 222;                          // the flower ends up this far right of me
  const FX = ME_X + CAM_END + GAP;          // flower world x — it enters at the right edge at t≈0
  const FY = 912, FS = 0.55;                // flower base y, scale in the wide shot
  const F_HEAD_Y = FY - 150 * FS;           // flower head (unswayed)
  const ROCK = { dx: 46, y: 905, w: 66, h: 42 };
  const FERN = { dx: -48, y: 915, s: 0.66 };
  const ROCK_GREY = '#8a8f86';

  /* ---------------- drawing helpers ---------------- */
  // Depth of field: like Art.blurred, but ramps continuously from sharp (no pop), renders only a
  // screen-space region, never caches one canvas per blur amount, and stays smooth at big blurs.
  const SOFT_W = Math.ceil(W / 1.5) + 4, SOFT_H = Math.ceil(H / 1.5) + 4;
  function soft(ctx, amount, drawFn, key, region) {
    if (amount < 1.0) { drawFn(ctx); return; }
    const r0 = region || { x: 0, y: 0, w: W, h: H };
    if (r0.w <= 0 || r0.h <= 0) return;
    const want = U.clamp(1 + (amount - 1) * 0.55, 1, 30);
    // pad the region so the blur's soft edge falls outside it (no dark seams at the frame edge)
    const m = Math.ceil(2.5 * want);
    const r = { x: r0.x - m, y: r0.y - m, w: r0.w + 2 * m, h: r0.h + 2 * m };
    const fMin = Math.max(1, (r.w + 2) / (SOFT_W - 4), (r.h + 2) / (SOFT_H - 4));
    if (want < fMin) {
      // below what the canvas can hold: blend sharp → softest-available, so the ramp never pops
      drawFn(ctx);
      const k = (want - 1) / (fMin - 1);
      if (k > 0.02) { ctx.save(); ctx.globalAlpha *= k; softPass(ctx, fMin, drawFn, r, key); ctx.restore(); }
      return;
    }
    softPass(ctx, want, drawFn, r, key);
  }
  // One exactly-sized canvas per pass. (A single shared canvas looked thriftier, but rewriting a
  // canvas that the not-yet-flushed main canvas still references forces a full copy-on-write.)
  function softPass(ctx, f, drawFn, r, key) {
    const cw = Math.ceil(r.w / f) + 2, ch = Math.ceil(r.h / f) + 2;
    const c = Art.canvas('a2:' + key, cw + 2, ch + 2);
    const c2 = c.getContext('2d');
    c2.setTransform(1, 0, 0, 1, 0, 0);
    c2.clearRect(0, 0, cw + 2, ch + 2);
    const base = Art._base || new DOMMatrix();
    const rel = base.inverse().multiply(ctx.getTransform());
    c2.setTransform(new DOMMatrix().scale(1 / f, 1 / f).translate(-r.x, -r.y).multiply(rel));
    c2.globalAlpha = 1;
    c2.globalCompositeOperation = 'source-over';
    drawFn(c2);
    // Big magnifications of a tiny canvas facet under bilinear filtering. Pre-blurring the tiny
    // canvas by ~1px removes the hard low-res edges, so a cheap bilinear upscale stays smooth
    // (much cheaper than imageSmoothingQuality 'high').
    let src = c;
    if (f > 3) {
      const cb = Art.canvas('a2:' + key + ':b', cw + 2, ch + 2);
      const xb = cb.getContext('2d');
      xb.setTransform(1, 0, 0, 1, 0, 0);
      xb.globalCompositeOperation = 'source-over';
      xb.globalAlpha = 1;
      xb.clearRect(0, 0, cw + 2, ch + 2);
      // 4-tap sub-pixel box blur: shifted copies summed at 1/4 (exact average in premultiplied space)
      xb.globalCompositeOperation = 'lighter';
      xb.globalAlpha = 0.25;
      const o = 0.7;
      xb.drawImage(c, 0, 0, cw, ch, -o, -o, cw, ch);
      xb.drawImage(c, 0, 0, cw, ch, o, -o, cw, ch);
      xb.drawImage(c, 0, 0, cw, ch, -o, o, cw, ch);
      xb.drawImage(c, 0, 0, cw, ch, o, o, cw, ch);
      xb.globalAlpha = 1;
      xb.globalCompositeOperation = 'source-over';
      src = cb;
    }
    ctx.save();
    ctx.setTransform(base);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(src, 0, 0, cw, ch, r.x, r.y, cw * f, ch * f);
    ctx.restore();
  }
  function rockPath(ctx, x, y, w, h, seed) { // the same outline as Art.rock (to clip the moss)
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(seed, 1) * 8, y - h);
    ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    ctx.lineTo(x + w / 2, y);
    ctx.closePath();
  }
  function mossyRock(ctx, x, y, w, h, moss, seed) {
    Art.rock(ctx, x, y, w, h, ROCK_GREY, seed);
    ctx.save();
    rockPath(ctx, x, y, w, h, seed);
    ctx.clip();
    ctx.fillStyle = moss;
    ctx.beginPath();
    ctx.moveTo(x - w * 0.6, y - h * 1.2);
    ctx.lineTo(x + w * 0.6, y - h * 1.2);
    for (let i = 0; i <= 10; i++) {
      const k = 1 - i / 10;
      ctx.lineTo(x - w * 0.6 + w * 1.2 * k, y - h * (0.62 + 0.18 * Math.sin(k * 3.1)) + Math.sin(i * 2.3 + seed) * h * 0.06);
    }
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = U.shade(moss, 0.16);
    for (let i = 0; i < 6; i++) {
      const px = x - w * 0.28 + U.hash(i, seed + 5) * w * 0.55, py = y - h * (0.78 + U.hash(i, seed + 6) * 0.16);
      ctx.beginPath(); ctx.ellipse(px, py, w * 0.07, h * 0.05, 0, 0, TAU); ctx.fill();
    }
    ctx.fillStyle = 'rgba(20,24,18,0.22)';
    ctx.fillRect(x - w, y - h * 0.18, w * 2, h * 0.3);
    ctx.restore();
  }
  function glint(ctx, x, y, r, color, a) {
    if (a <= 0.01) return;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha *= U.clamp(a);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x, y - r); ctx.quadraticCurveTo(x, y, x + r * 0.16, y);
    ctx.quadraticCurveTo(x, y, x, y + r); ctx.quadraticCurveTo(x, y, x - r * 0.16, y);
    ctx.quadraticCurveTo(x, y, x, y - r);
    ctx.moveTo(x - r * 0.7, y); ctx.quadraticCurveTo(x, y, x, y - r * 0.11);
    ctx.quadraticCurveTo(x, y, x + r * 0.7, y); ctx.quadraticCurveTo(x, y, x, y + r * 0.11);
    ctx.quadraticCurveTo(x, y, x - r * 0.7, y);
    ctx.fill();
    ctx.restore();
    Art.glow(ctx, x, y, r * 1.5, color, a * 0.6);
  }
  const phone = (c) => {
    c.save();
    c.rotate(-0.15);
    c.fillStyle = '#23262e';
    Art.roundRect(c, -3, -24, 7, 26, 2.5); c.fill();
    c.fillStyle = '#9fd8ff';
    c.fillRect(-3.4, -22, 1.6, 22);
    c.restore();
  };

  // shade every colour in a palette toward black (amt < 0) or white
  const shadePal = (P, amt) => {
    const f = (v) => (typeof v === 'string' ? U.shade(v, amt) : Array.isArray(v) ? v.map(f) : v);
    const o = {};
    for (const k of Object.keys(P)) o[k] = f(P[k]);
    return o;
  };
  // a soft, feathered shaft of light from (x0,y0) down to (x1,y1), widths w0 → w1 (screen space)
  function beam(ctx, x0, y0, x1, y1, w0, w1, color, a, blur) {
    if (a <= 0.004) return;
    const nx = -(y1 - y0), ny = x1 - x0, nl = Math.hypot(nx, ny) || 1;
    const ux = nx / nl, uy = ny / nl;
    const m = Math.max(w0, w1) + blur * 2;
    const bx0 = Math.max(0, Math.min(x0, x1) - m), by0 = Math.max(0, Math.min(y0, y1) - m);
    const bx1 = Math.min(W, Math.max(x0, x1) + m), by1 = Math.min(H, Math.max(y0, y1) + m);
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    soft(ctx, blur, (c) => {
      const gr = c.createLinearGradient(x0, y0, x1, y1);
      gr.addColorStop(0, U.rgba(color, 0));
      gr.addColorStop(0.65, U.rgba(color, a * 0.6));
      gr.addColorStop(1, U.rgba(color, a));
      c.fillStyle = gr;
      for (const k of [1, 0.6]) {   // a core inside a wider veil
        c.globalAlpha = k === 1 ? 0.55 : 0.6;
        c.beginPath();
        c.moveTo(x0 - ux * w0 * k, y0 - uy * w0 * k); c.lineTo(x0 + ux * w0 * k, y0 + uy * w0 * k);
        c.lineTo(x1 + ux * w1 * k, y1 + uy * w1 * k); c.lineTo(x1 - ux * w1 * k, y1 - uy * w1 * k);
        c.closePath(); c.fill();
      }
    }, 'beam', { x: bx0, y: by0, w: bx1 - bx0, h: by1 - by0 });
    ctx.restore();
  }

  /* ---------------- camera ---------------- */
  // Each layer has a parallax factor p (1 = trail plane); scroll offsets are camX * p.
  // The push-in is a true dolly: a layer's magnification is 1 / (1 - cz * p), so the
  // flower swells while the far forest barely grows.
  function cameraAt(t) {
    const camX = camXAt(t);
    const kz = U.ease(t, T_PUSH0, T_PUSH1, 'inOutSine');
    const creep = U.ease(t, T_PUSH1, D + 2, 'linear') * 0.05;
    const Zt = Math.exp(Math.log(ZOOM_END) * kz + creep);
    const cz = 1 - 1 / Zt;
    // the flower head (trail-plane coords, zoom 1) glides to its close-up mark
    const ax = FX - camX, ay = F_HEAD_Y;
    const sx = U.lerp(ax, CLOSE.x, kz), sy = U.lerp(ay, CLOSE.y, kz);
    let dx = ax - CX - (sx - CX) / Zt, dy = ay - CY - (sy - CY) / Zt;
    // gentle handheld float, calmer as time stops
    const sh = Art.shake(t * 0.7, 0.45, 23);
    const calm = 1 - 0.75 * U.ease(t, 6, 12);
    dx += (sh.x * calm) / Zt; dy += (sh.y * calm) / Zt;
    return { camX, cz, dx, dy, Zt };
  }
  const zoomOf = (cam, p) => 1 / (1 - cam.cz * p);
  function layer(ctx, cam, p, fn) {
    ctx.save();
    Art.cam(ctx, { x: CX + cam.dx * p, y: CY + cam.dy * p, zoom: zoomOf(cam, p) });
    fn(ctx, cam.camX * p);
    ctx.restore();
  }
  // trail-plane point (zoom-1 screen coords after scrolling) → screen
  const toScreen = (cam, x, y) => ({ x: CX + cam.Zt * (x - CX - cam.dx), y: CY + cam.Zt * (y - CY - cam.dy) });

  /* ---------------- scene ---------------- */
  Film.scene({
    id: 'flower',
    order: 2,
    title: 'The Flower',
    duration: D,
    moods: [[0, 'forest'], [5.8, 'wonder']],
    sfx: [
      [0.2, 'footsteps', { gain: 0.35 }],
      [2.15, 'sparkle', { gain: 0.35 }],
      [5.9, 'chime', { gain: 0.55 }],
      [6.3, 'shimmer', { gain: 0.45 }],
      [12.3, 'heartbeat', { gain: 0.35 }],
      [13.9, 'swell', { gain: 0.3 }],
      [19.7, 'chime', { gain: 0.4 }],
      [21.6, 'breath', { gain: 0.35 }],
    ],
    crossIn: 0.8,
    fadeIn: 0,
    fadeOut: 0,
    post: (t) => ({ vignette: 0.32 + 0.22 * U.ease(t, 6, 12), grain: 0.045, letterbox: 1 }),

    render(ctx, t) {
      const P = U.mixDeep(Art.TOD.morning, Art.TOD.golden, 0.2 + 0.1 * U.clamp(t / D));
      const cam = cameraAt(t);
      const wa = rateInt(t, TAU_A);          // ambient (world) time
      const wo = rateInt(t, TAU_O);          // the others' time
      const slowK = U.ease(t, 5.9, 11);      // how far time has stopped
      const dsat = 0.8 * U.ease(t, 5.9, 10.8, 'inOutSine');
      const closeK = U.ease(t, T_PUSH0 + 1.5, T_PUSH1);
      const bgBlur = 10 * U.ease(t, 6.2, 11.2) + 34 * U.ease(t, T_PUSH0, T_PUSH1 - 1);
      // macro depth of field as we push in: the trail behind the flower melts, its neighbours soften
      const groundBlur = 38 * U.ease(t, T_PUSH0 + 0.5, T_PUSH1 + 0.4, 'inOutSine');
      const spotBlur = 5.5 * U.ease(t, T_PUSH0 + 2, T_PUSH1 + 0.4);
      const frontBlur = 22 * U.ease(t, T_PUSH0 + 0.5, T_PUSH1);
      const meBlur = 11 * U.ease(t, T_PUSH0 + 0.3, T_PUSH0 + 4);
      const oBlur = 7 * U.ease(t, 6.8, 11.6) + 6 * U.ease(t, T_PUSH0, T_PUSH1);
      const Pbg = U.mixDeep(P, shadePal(Art.desatPalette(P, 0.6), -0.22), 0.55 * slowK);  // the far world dims as it greys
      const fGlow = 0.16 * U.bump(t, 2.3, 0.55) + 0.8 * U.ease(t, 5.8, 12.5, 'inOutSine');

      const flowerScr = toScreen(cam, FX - cam.camX, FY);
      const groundLow = toScreen(cam, 0, GY + GAMP + 8).y;  // below the lowest dip of the ground line
      const groundTop = toScreen(cam, 0, GY - GAMP - 44).y; // above the tallest shrubs on the back edge

      /* ---------- far world (goes soft as time stops) ---------- */
      soft(ctx, bgBlur, (c) => {
        const P = Pbg;
        layer(c, cam, 0, (c2) => {
          Art.sky(c2, P, { horizon: 720 });
          Art.glow(c2, 1760, 90, 470, P.sun, 0.32);
          Art.rays(c2, { x: 1720, y: 40, angle: 2.2, spread: 0.8, count: 5, len: 1250, color: P.light, alpha: 0.12 * (1 - 0.5 * slowK) * U.ease(t, 0.7, 1.7), t: wa, seed: 4, width: 0.06 });
        });
        layer(c, cam, 0.02, (c2, off) => Art.clouds(c2, { seed: 2, count: 4, y0: 190, y1: 330, offset: off + wa * 5, color: '#ffffff', alpha: 0.55 }));
        layer(c, cam, 0.04, (c2, off) => Art.ridge(c2, { seed: 21, y: 615, amp: 150, color: U.mix(P.far, P.sky[1], 0.4), offset: off }));
        layer(c, cam, 0.03, (c2, off) => Art.summit(c2, { x: 1610 - off, y: 655, h: 440, w: 700, P, glow: 0.55, t: wa }));
        layer(c, cam, 0.05, (c2) => Art.fog(c2, { y: 650, h: 170, color: P.fog, alpha: 0.5 }));
        layer(c, cam, 0.09, (c2, off) => Art.ridge(c2, { seed: 8, y: 718, amp: 100, color: P.mid, offset: off }));
        layer(c, cam, 0.18, (c2, off) => {
          Art.forest(c2, { seed: 31, y: 770, offset: off, spacing: 64, hMin: 110, hMax: 190, color: P.trees[0], light: U.shade(P.trees[0], 0.1), kind: 'mix' });
          Art.fog(c2, { y: 772, h: 120, color: P.fog, alpha: 0.32 });
        });
        layer(c, cam, 0.34, (c2, off) => {
          // (all pines here: a round crown blurs into a ring in the close-up)
          Art.forest(c2, { seed: 32, y: 828, offset: off, spacing: 84, hMin: 200, hMax: 300, color: P.trees[1], light: U.shade(P.trees[1], 0.12), kind: 'pine', sway: 4, t: wa });
        });
        layer(c, cam, 0.55, (c2, off) => {
          Art.forest(c2, { seed: 33, y: 874, offset: off, spacing: 230, hMin: 400, hMax: 520, color: U.mix(P.trees[2], P.trees[1], 0.3), light: U.shade(P.trees[1], 0.04), kind: 'pine', sway: 3, t: wa, jitterY: 8 });
        });
      }, 'bg', { x: 0, y: 0, w: W, h: Math.min(H, groundLow + 10) });

      /* ---------- trail plane ---------- */
      const drawGround = (c) => layer(c, cam, 1, (c2, off) => {
        const go = gOpt(off);
        // shrubs along the back edge
        const i0 = Math.floor((off - 200) / 150), i1 = Math.ceil((off + W + 200) / 150);
        for (let i = i0; i <= i1; i++) {
          if (U.hash(i, 61) < 0.45) continue;
          const x = i * 150 + U.hash(i, 62) * 90 - off;
          Art.bush(c2, x, Art.groundY(x, go) + 3, 20 + U.hash(i, 63) * 18, U.mix(P.trees[2], P.grass, 0.25), U.shade(P.grass, 0.06), i);
        }
        Art.ground(c2, { y: GY, amp: GAMP, offset: off, color: P.ground, color2: P.ground2 });
        Art.trail(c2, { y: GY, amp: GAMP, offset: off, color: P.trail });
        // dappled light on the trail
        c2.save();
        c2.globalCompositeOperation = 'lighter';
        const j0 = Math.floor((off - 100) / 120), j1 = Math.ceil((off + W + 100) / 120);
        for (let j = j0; j <= j1; j++) {
          if (U.hash(j, 71) < 0.4) continue;
          const x = j * 120 + U.hash(j, 72) * 80 - off;
          const y = Art.groundY(x, go) + 14 + U.hash(j, 73) * 22;
          c2.fillStyle = U.rgba(P.light, (0.07 + U.hash(j, 74) * 0.06) * (1 - 0.6 * slowK));
          c2.beginPath(); c2.ellipse(x, y, 26 + U.hash(j, 75) * 34, 5 + U.hash(j, 76) * 4, 0, 0, TAU); c2.fill();
        }
        c2.restore();
        Art.grass(c2, { seed: 5, y: (x) => Art.groundY(x, go) + 1, offset: off, spacing: 8, h: 22, width: 2.9, color: P.grass, color2: U.shade(P.grass, 0.14), t: wa, wind: 0.7 });
      });

      // the others: screen-space bounds so their soft pass only touches where they are
      const crew = CREW.map((m) => {
        const look = Art.CAST[m.k];
        const x = m.x + V0 * wo - cam.camX;
        return { m, look, x, walk: m.ph + (RATE / look.height) * wo };
      });
      const leftmost = toScreen(cam, Math.min(...crew.map((c) => c.x)) - 70, 0).x;
      const drawOthers = (c) => layer(c, cam, 1, (c2, off) => {
        const go = gOpt(off);
        for (let i = crew.length - 1; i >= 0; i--) {
          const { m, x, walk } = crew[i];
          if (x < -200 || x > W / Math.max(1, cam.Zt) + 600) continue;
          const o = { x, y: Art.groundY(x, go) + FOOT, s: S, look: m.k, t: wo, walk };
          if (m.k === 'h1') { o.head = { tilt: -0.06 }; o.face = { smile: 0.12, brow: -0.15 }; }
          if (m.k === 'h2') {
            const talk = t < 5.5 && U.noise1(t * 1.3, 4) > 0.05 ? 1 : 0;
            o.head = { tilt: -0.02 }; o.face = { smile: 0.35, talk, lookX: 1 };
          }
          if (m.k === 'h3') { o.head = { tilt: -0.17 }; o.face = { smile: 0.3, lookY: -0.8, lookX: 0.6 }; }
          if (m.k === 'h4') {
            o.gesture = 'phone'; o.gw = 1;
            o.head = { tilt: -0.08 }; o.face = { smile: 0.05, lookY: -0.7, lookX: 0.7 };
            o.holdF = phone;
          }
          Art.person(c2, o);
        }
      });
      const othersVisible = leftmost < W + 40;

      const meScr = toScreen(cam, ME_X + 60, 0).x;   // his right-most edge on screen
      const meVisible = meScr > -40;
      const drawMe = (c) => layer(c, cam, 1, (c2, off) => {
        const go = gOpt(off);
        const x = ME_X + cam.camX - off; // = 540 while tracking
        const y = Art.groundY(x, go) + FOOT;
        const g = rateAt(t, G_KEYS);
        // where is the flower relative to his eyes? he tracks it
        const hx = x + 6, hy = y - 205;
        const ang = Math.atan2(F_HEAD_Y - hy, FX - off - hx);
        const att = U.ease(t, 1.95, 2.55, 'outBack');          // it catches his eye
        const near = U.ease(t, 9, 13);
        const wander = U.noise1(t * 0.5, 12);                    // before: looking around at the trees
        const tilt = U.lerp(-0.13 + 0.05 * wander, ang * 0.42 + 0.04, att);
        const face = {
          smile: 0.22 + 0.26 * U.ease(t, 8, 13),
          browUp: 0.55 * U.bump(t, 2.3, 0.9) + 0.3 * U.ease(t, 6, 10),
          lookX: U.lerp(0.25 + 0.3 * wander, Math.cos(ang) * 1.1, att),
          lookY: U.lerp(-0.7, Math.sin(ang) * 1.25, att),
          eyes: t > 13.2 ? 'sparkle' : 'open',
        };
        // eyes stay open while he locks on; one slow blink once he has stopped
        if (t > 1.8 && t < 13) face.blink = U.bump(t, 1.88, 0.07);
        else if (t >= 13) face.blink = U.bump(t, 13.15, 0.16);
        const settle = U.ease(t, T_STOP - 0.4, T_STOP + 1.6);   // he leans in, just a little
        const o = { x, y, s: S, look: 'me', t, face, lean: 0.07 * settle, head: { tilt: tilt + 0.05 * settle, turn: 0.28 * near } };
        if (t < T_STOP + 0.02) { o.walk = ME_PH0 + RATE * rateInt(t, G_KEYS); o.stride = strideOf(g); } else o.pose = 'stand';
        Art.person(c2, o);
      });

      const drawSpot = (c) => layer(c, cam, 1, (c2, off) => {
        const fx = FX - off;
        if (fx < -260 || fx > W + 260) return;
        c2.fillStyle = U.shade(P.ground, -0.08);              // a little mossy island at the trail's edge
        c2.beginPath(); c2.ellipse(fx + 6, FY + 4, 96, 13, 0, 0, TAU); c2.fill();
        mossyRock(c2, fx + ROCK.dx, ROCK.y, ROCK.w, ROCK.h, U.mix(P.grass, P.trees[2], 0.25), 7);
        Art.fern(c2, fx + FERN.dx, FERN.y, FERN.s, U.mix(P.grass, P.trees[2], 0.45), U.wind(wa, fx, 2) * 0.6);
        Art.fern(c2, fx + FERN.dx + 22, FERN.y + 2, FERN.s * 0.6, U.mix(P.grass, P.trees[2], 0.2), U.wind(wa, fx + 30, 3) * 0.6);
      });
      const frontGrass = (c2, off, x0, x1, dsatAmt) => {
        const go = gOpt(off);
        Art.grass(c2, {
          seed: 9, y: (x) => Art.groundY(x, go) + 46, offset: off, spacing: 7, h: 17, hVar: 0.8, width: 2.8,
          color: U.desat(U.shade(P.grass, -0.12), dsatAmt), color2: U.desat(U.shade(P.grass, 0.02), dsatAmt), t: wa, wind: 0.6, x0, x1,
        });
      };
      const drawFront = (c) => layer(c, cam, 1, (c2, off) => frontGrass(c2, off, -20, W + 20, 0));

      const nearTop = Math.max(0, groundTop);
      const nearRegion = { x: 0, y: nearTop, w: W, h: H - nearTop };
      soft(ctx, groundBlur, drawGround, 'near', nearRegion);
      if (othersVisible) soft(ctx, oBlur, drawOthers, 'others', { x: Math.max(0, leftmost - 20), y: PIC.top - 20, w: W - Math.max(0, leftmost - 20), h: PIC.h + 40 });
      if (meVisible) soft(ctx, meBlur, drawMe, 'me', { x: 0, y: PIC.top - 20, w: Math.min(W, meScr + 80), h: PIC.h + 40 });
      soft(ctx, spotBlur, drawSpot, 'spot', nearRegion);
      soft(ctx, frontBlur, drawFront, 'front', nearRegion);

      /* ---------- the world loses its colour… ---------- */
      Art.desaturate(ctx, dsat);
      // bokeh: out-of-focus sunlight through the canopy, blooming as the background melts
      const bok = U.ease(t, T_PUSH0 + 1.2, T_PUSH1);
      if (bok > 0.01) {
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        const spread = 0.82 + 0.18 * bok;
        for (let i = 0; i < 18; i++) {
          const bx = CX + (U.hash(i, 81) * 2 - 1) * 900 * spread + U.noise1(t * 0.07 + i, 3) * 14;
          const by = 230 + U.hash(i, 82) * 520 + U.noise1(t * 0.06 + i, 5) * 10;
          if (Math.abs(bx - CX) < 330 && by < 470) continue;            // keep the words clean
          if (Math.abs(bx - CLOSE.x) < 210 && Math.abs(by - CLOSE.y) < 200) continue; // and the flower
          const r = (22 + U.hash(i, 83) * 40) * (0.7 + 0.3 * bok);
          const tw = 0.75 + 0.25 * Math.sin(t * (0.35 + U.hash(i, 84) * 0.4) + i * 2.1);
          const col = U.mix(P.light, '#ffd9e6', U.hash(i, 85) * 0.7);
          const gr = ctx.createRadialGradient(bx, by, 0, bx, by, r);
          gr.addColorStop(0, U.rgba(col, 0.085 * bok * tw));
          gr.addColorStop(0.72, U.rgba(col, 0.075 * bok * tw));
          gr.addColorStop(1, U.rgba(col, 0));
          ctx.fillStyle = gr;
          ctx.beginPath(); ctx.arc(bx, by, r, 0, TAU); ctx.fill();
        }
        ctx.restore();
      }
      // in the close-up, burn in the top of frame so the words sit on shadow
      if (closeK > 0.01) {
        const gr = ctx.createLinearGradient(0, PIC.top, 0, 620);
        gr.addColorStop(0, `rgba(14,18,22,${0.5 * closeK})`);
        gr.addColorStop(1, 'rgba(14,18,22,0)');
        ctx.fillStyle = gr;
        ctx.fillRect(0, PIC.top, W, 620 - PIC.top);
      }

      /* ---------- …except the flower ---------- */
      if (flowerScr.x > -400 && flowerScr.x < W + 400) {
        const fs = FS * cam.Zt;
        const headR = 52 * fs;
        const sway = U.wind(t, 1000, 3) * 9 * fs * 0.9;
        const hx = flowerScr.x + sway, hy = flowerScr.y - 150 * fs;
        // as time stops, one warm shaft of sunlight finds the flower
        const beamA = 0.26 * U.ease(t, 6.4, 11.5) * (1 - 0.7 * closeK);
        beam(ctx, hx + 430 * Math.min(cam.Zt, 2), PIC.top - 80, hx + 4 * cam.Zt, hy + 46 * fs, 70 * Math.min(cam.Zt, 2.5), 26 * fs + 14, P.light, beamA, 18 + 10 * closeK);
        // a warm pool of light on the ground, and the halo (radii capped: the close-up stays cheap)
        Art.glow(ctx, flowerScr.x, flowerScr.y - 6 * fs, Math.min(130 * cam.Zt, 280), '#ffb8cf', 0.18 * fGlow * (1 - closeK));
        const haloR = headR * U.lerp(5.2, 2.3, closeK);
        Art.glow(ctx, hx, hy, haloR, '#ff8db0', 0.5 * fGlow);
        Art.glow(ctx, hx, hy, headR * 1.7, '#fff2d6', 0.32 * fGlow);
        ctx.save();
        ctx.translate(flowerScr.x - 1000, 0);   // fixed x for the wind, so the sway doesn't drift with the camera
        Art.flower(ctx, { x: 1000, y: flowerScr.y, s: fs, t, seed: 3, face: 0.72, sway: 0.9 });
        ctx.restore();
        glint(ctx, hx + 3, hy - 6, 22 * Math.sqrt(cam.Zt), '#fff4e0', U.bump(t, 2.3, 0.45) * 0.9);
        // the verge grass that stands in front of the stem, in the world's colour
        soft(ctx, frontBlur, (c) => layer(c, cam, 1, (c2, off) => frontGrass(c2, off, FX - off - 26, FX - off + 26, dsat)), 'front2',
          { x: flowerScr.x - 40 * cam.Zt, y: Math.max(0, flowerScr.y - 40 * cam.Zt), w: 80 * cam.Zt, h: 90 * cam.Zt });
        // pollen hangs in the air (ambient time all but stops)
        const pk = U.ease(t, 5.5, 11);
        if (pk > 0) {
          layer(ctx, cam, 1, (c2, off) => {
            const fx = FX - off;
            const gz = 1 / Math.sqrt(cam.Zt);
            Art.motes(c2, { seed: 17, count: 20, x0: fx - 190, x1: fx + 210, y0: F_HEAD_Y - 120, y1: FY + 5, t: wa + 3, color: '#ffe3a1', size: 1.4, drift: 9, glow: 0.8 * gz, alpha: 0.75 * pk, wander: 22 });
            Art.motes(c2, { seed: 18, count: 8, x0: fx - 70, x1: fx + 80, y0: F_HEAD_Y - 70, y1: F_HEAD_Y + 50, t: wa + 9, color: '#ffd0e0', size: 1.1, drift: 5, glow: 0.9 * gz, alpha: 0.7 * pk, wander: 14 });
          });
        }
      }

      /* ---------- words ---------- */
      Art.captions(ctx, t, [
        [0.9, 4.5, '…a single flower catches my attention.'],
        [11.0, 16.2, 'It’s small, unassuming, standing alone in the middle of the forest.'],
      ]);
      const titleA = U.ease(t, 19.5, 20.3) * (1 - U.ease(t, 23.5, 24.6));
      Art.title(ctx, 'I stop.', {
        y: 322, size: 140, reveal: U.ease(t, 19.5, 20.9, 'outSine'), alpha: titleA,
        color: '#fbf3e6', glow: 'rgba(255,120,165,0.55)', now: false,
      });
    },
  });
})();
