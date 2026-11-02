/* ==========================================================================
   04 · The Flower’s Story — golden afternoon.
   Close on the narrator gazing at the flower in warm side light. He closes
   his eyes and the world turns into a storybook page (sepia ink on paper):
   a seed drifts into a dim, crowded forest floor; a small grey flower grows
   alone among towering trunks; giant boots stride past; seasons turn. Then
   warmth arrives — he came along, he saw it, he made it matter — and colour
   floods the page, repainting it into the real golden forest. We push slowly
   into the flower’s golden heart; scene 05 begins inside it.
   One world, one camera: the storybook is drawn in the same world space as
   the real shot, so the colour flood lands exactly on the real picture.
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 42;
  const P = Art.TOD.golden;
  const GA = Art.GOLDEN_ANGLE;
  const ez = U.ease;

  /* ---------------- world layout ---------------- */
  const GY = 868;                                   // trail / ground line
  const GOPT = { y: GY, amp: 8, freq: 0.0021, seed: 14 };
  const FX = 1060, FY = 920, FS = 0.92;             // the flower: stem base + scale
  const HX0 = FX, HY0 = FY - 150 * FS;              // its head at rest
  const RH = 18 * FS;                               // radius of its golden heart (full bloom)
  const MX = 748, MY = 877;                         // the narrator sits here
  const SUN = { x: 1720, y: 630 };
  const ROCK = { x: 1200, y: 934, w: 176, h: 96 };
  const FERN = { x: 956, y: 936, s: 1.08 };
  const SBS = 0.6 * FS;                             // the flower's size in the imagined past
  const ROCK_GREY = '#8a8f86';                      // the flower spot, as in scenes 02/03
  const MOSS = U.mix(P.grass, P.trees[2], 0.25);
  const FERN_C1 = U.mix(P.grass, P.trees[2], 0.45), FERN_C2 = U.mix(P.grass, P.trees[2], 0.2);
  const FSEED = 3;                                  // the same flower (petal arrangement) as 02/03
  const Z_END = 1160 / RH;                          // the heart fills the frame

  /* ---------------- timeline ---------------- */
  const TL = {
    diss0: 5.3, diss1: 8.3,
    seed0: 8.0, land: 10.9,
    sprout0: 11.0, flower0: 11.95, grown: 13.6,
    hikers: [13.8, 14.5, 15.15], cross: 1.45,
    seas0: 16.05, seas1: 18.4,
    came0: 18.45, stop: 20.4,
    saw0: 21.8, ring: 22.65,
    made0: 24.55, bloom: 24.85, flood0: 25.0, flood1: 27.6,
    push0: 28.6,
  };
  const CAPS = [
    [1.5, 5.7, 'I take a moment observing the flower, imagining a story.'],
    [8.7, 13.7, 'Maybe it grew here, all alone, thinking no one would ever notice.'],
    [14.1, 17.8, 'Maybe it felt invisible, like it didn’t matter.'],
    [18.6, 21.4, 'But then I came along.'],
    [21.8, 24.3, 'I saw it.'],
    [24.7, 27.7, 'I made it matter.'],
    [28.7, 32.4, 'I gave it more meaning within my lived experience'],
    [32.8, 37.6, 'by doing more thinking about how this flower—or maybe flowers in general—'],
    [38.0, 41.3, 'might relate to the universe we live in.'],
  ];

  /* ---------------- small helpers ---------------- */
  const camLerp = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), k)) });
  const camMatrix = (c) => new DOMMatrix().translate(W / 2, H / 2).scale(c.z).translate(-c.x, -c.y);
  const toScreen = (c, x, y) => ({ x: W / 2 + (x - c.x) * c.z, y: H / 2 + (y - c.y) * c.z });
  const applyCam = (ctx, c) => Art.cam(ctx, { x: c.x, y: c.y, zoom: c.z });

  /** offscreen canvases that only ever grow (no per-frame reallocation) */
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
  /**
   * Depth-of-field layer like Art.blurred, but upscaled in two bilinear steps
   * (the kit's 'high' quality bicubic upscale costs ~25 ms of raster per call).
   * Keep `amount` fixed per key so the offscreens are allocated once.
   */
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
  /** a soft-edged out-of-focus light disc */
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
  /** four-point twinkle */
  function twinkle(ctx, x, y, r, color, a) {
    if (a <= 0.01) return;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha *= clamp(a);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x, y - r); ctx.quadraticCurveTo(x, y, x + r * 0.26, y); ctx.quadraticCurveTo(x, y, x, y + r);
    ctx.quadraticCurveTo(x, y, x - r * 0.26, y); ctx.quadraticCurveTo(x, y, x, y - r);
    ctx.moveTo(x - r * 0.72, y); ctx.quadraticCurveTo(x, y, x, y - r * 0.18); ctx.quadraticCurveTo(x, y, x + r * 0.72, y);
    ctx.quadraticCurveTo(x, y, x, y + r * 0.18); ctx.quadraticCurveTo(x, y, x - r * 0.72, y);
    ctx.fill();
    ctx.restore();
    Art.glow(ctx, x, y, r * 1.7, color, a * 0.35);
  }

  /** the cast look with every colour replaced by one flat colour (silhouettes, rim-light copies) */
  const flatLooks = new Map();
  function flatLook(key, col) {
    const id = key + ':' + col;
    let o = flatLooks.get(id);
    if (o) return o;
    o = {};
    const L = Art.CAST[key];
    for (const k of Object.keys(L)) o[k] = typeof L[k] === 'string' && L[k][0] === '#' ? col : L[k];
    flatLooks.set(id, o);
    return o;
  }
  /**
   * A figure with a rim light: a flat light-coloured copy nudged toward the light is drawn first
   * (additively), then the figure on top, so only a thin lit edge of the copy shows.
   */
  function rimLit(ctx, o, key, rimCol, dx, dy, rimA, figLook) {
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    Art.person(ctx, Object.assign({}, o, { x: o.x + dx, y: o.y + dy, look: flatLook(key, rimCol), shadow: false, glow: 0, alpha: rimA * (o.alpha === undefined ? 1 : o.alpha) }));
    ctx.restore();
    return Art.person(ctx, Object.assign({}, o, figLook ? { look: figLook } : {}));
  }

  /* ---------------- sepia (storybook) colour mapping ---------------- */
  const INK = '#2a1b10', SEPM = '#8f6e49', PAPER = '#f3e6c9';
  function sep(c, lift = 0) {
    const [r, g, b] = U.rgb(c);
    const l = clamp(((0.299 * r + 0.587 * g + 0.114 * b) / 255) * 0.9 + 0.05 + lift);
    return l < 0.5 ? U.mix(INK, SEPM, l / 0.5) : U.mix(SEPM, PAPER, (l - 0.5) / 0.5);
  }
  const sepLooks = new Map();
  function sepLook(key, lift = 0) {
    const id = key + ':' + lift;
    let o = sepLooks.get(id);
    if (o) return o;
    o = {};
    const L = Art.CAST[key];
    for (const k of Object.keys(L)) o[k] = typeof L[k] === 'string' && L[k][0] === '#' ? sep(L[k], lift) : L[k];
    sepLooks.set(id, o);
    return o;
  }
  // the imagined flower: a small grey thing, inked dark enough to read on the page
  const SEP_FLOWER = { petal: '#8a7862', tip: '#b3a288', inner: '#4d3e2e', center: '#d9c8a2', seed: '#6a5539', stem: '#47382a', leaf: '#5b4a36' };

  /* ---------------- camera ---------------- */
  const CA0 = { x: 897, y: 770, z: 2.16 }, CA1 = { x: 904, y: 767, z: 2.27 };
  const CB0 = { x: 912, y: 752, z: 1.62 }, CB1 = { x: 915, y: 750, z: 1.67 };
  function camBase(t) {
    if (t < TL.diss0) return camLerp(CA0, CA1, ez(t, 0, TL.diss0, 'inOutSine'));
    if (t < TL.diss1 + 0.2) return camLerp(CA1, CB0, ez(t, TL.diss0, TL.diss1 + 0.2, 'inOutSine'));
    return camLerp(CB0, CB1, ez(t, TL.diss1 + 0.2, TL.push0, 'inOutSine'));
  }
  /** the slow push into the flower's golden heart (log-zoom; the head glides to centre) */
  function camAt(t) {
    if (t <= TL.push0) return camBase(t);
    const c0 = camBase(TL.push0);
    const p = U.prog(t, TL.push0, D);
    const F = 0.5 - 0.5 * Math.cos(Math.PI * Math.pow(p, 1.35));
    const z = Math.exp(lerp(Math.log(c0.z), Math.log(Z_END), F));
    const s0 = toScreen(c0, HX0, HY0);
    const v = ez(t, TL.push0, TL.push0 + 7.6, 'inOutSine');
    const sx = lerp(s0.x, W / 2, v), sy = lerp(s0.y, H / 2, v);
    return { x: HX0 - (sx - W / 2) / z, y: HY0 - (sy - H / 2) / z, z };
  }

  /* ---------------- performance states ---------------- */
  /** book: the imagined flower on the page; otherwise the real one */
  function flowerState(t, book = false) {
    const st = { s: FS, bloom: 1, droop: 0, sat: 1, glow: 0.3, face: 0.8, sway: 1, rot: 0, tremble: 0, show: true };
    if (!book && t < TL.flood0) { st.glow = 0.3 + 0.05 * Math.sin(t * 1.4); return st; }
    if (book && t < TL.flood0) {
      // the imagined past
      st.show = t >= TL.flower0;
      const grow = ez(t, TL.flower0, TL.grown + 0.3, 'outCubic');
      st.s = lerp(0.16, SBS, grow);
      st.bloom = 0.52 * ez(t, TL.flower0 + 0.55, TL.grown, 'inOutSine');
      st.droop = 0.06 * ez(t, TL.grown - 0.4, TL.grown + 0.6) + 0.3 * ez(t, TL.seas0, TL.seas1 - 0.2, 'inOutSine');
      st.bloom -= 0.1 * ez(t, TL.seas0, TL.seas1);
      st.sat = 0; st.glow = 0; st.face = 0.72;
      // "I saw it": a small dip, then the head lifts toward him
      if (t > TL.saw0) {
        const dip = U.bump(t, TL.saw0 + 0.42, 0.22) * 0.05;
        const lift = clamp(U.spring(t - (TL.saw0 + 0.55), 1.3, 3.2));
        st.droop = lerp(st.droop + dip, 0, lift);
        st.bloom = lerp(st.bloom, 0.56, ez(t, TL.saw0 + 0.5, TL.saw0 + 1.4, 'outCubic'));
        st.sat = 0.42 * ez(t, TL.ring - 0.05, TL.ring + 0.9, 'outCubic');
        st.glow = 0.45 * ez(t, TL.ring - 0.1, TL.ring + 0.5) * (1 - 0.3 * ez(t, TL.ring + 0.5, TL.ring + 1.5));
      }
      // "I made it matter": anticipation (it gathers itself), then the bloom
      if (t > TL.made0) {
        const ant = ez(t, TL.made0, TL.bloom, 'inOutSine') * (1 - ez(t, TL.bloom, TL.bloom + 0.15));
        st.s = SBS * (1 - 0.05 * ant);
        st.bloom -= 0.06 * ant;
      }
      st.tremble = trembleAt(t);
      return Object.assign(st, bloomBurst(t, st));
    }
    // the real flower, now that it matters
    Object.assign(st, bloomBurst(t, st));
    st.sway = 1 - ez(t, TL.push0, TL.push0 + 3.6, 'inOutSine');
    st.face = lerp(0.8, 1, ez(t, TL.push0 + 1, TL.push0 + 6.5, 'inOutSine'));
    return st;
  }
  /** the bloom: spring in scale, petals unfurl with a twist, colour + glow flash */
  function bloomBurst(t, st) {
    if (t < TL.bloom) return {};
    const u = t - TL.bloom;
    const sp = U.spring(u, 1.25, 3.4);
    return {
      s: lerp(SBS * 0.95, FS, sp),
      bloom: lerp(0.5, 1, ez(u, 0, 0.75, 'outCubic')),
      droop: 0,
      sat: lerp(st.sat || 0, 1, ez(u, 0, 0.55, 'outCubic')),
      glow: 0.62 + 0.9 * Math.exp(-u * 2.2) * ez(u, 0, 0.12),
      face: 0.8,
      rot: -0.6 * (1 - sp),
      tremble: 0,
    };
  }
  function trembleAt(t) {
    let a = 0;
    for (const t0 of TL.hikers) {
      const tp = t0 + TL.cross * ((FX + 420) / 2770);
      if (t > tp - 0.05) a += Math.exp(-(t - tp) * 3.2) * Math.sin((t - tp) * 21) * 0.11;
    }
    return a;
  }
  /** mode: 'real' (as is), 'sepia' (storybook ink), 'tint' (full colour at alpha = st.sat) */
  function drawFlower(ctx, t, st, mode = 'real', glowK = 1) {
    if (!st.show) return null;
    ctx.save();
    if (st.tremble) { ctx.translate(FX, FY); ctx.rotate(st.tremble); ctx.translate(-FX, -FY); }
    const o = { x: FX, y: FY, s: st.s, t, seed: FSEED, bloom: st.bloom, droop: st.droop, sat: st.sat, glow: st.glow * glowK, face: st.face, sway: st.sway, rot: st.rot };
    if (mode === 'sepia') Object.assign(o, { colors: SEP_FLOWER, sat: 1, glow: 0 });
    if (mode === 'tint') Object.assign(o, { sat: 1, alpha: st.sat });
    const r = Art.flower(ctx, o);
    ctx.restore();
    return r;
  }
  function meReal(t) {
    // shot A: gaze → lean in, curious → drift into imagining → eyes close
    if (t < TL.flood0) {
      const tilt = U.keys(t, [[0, 0.13], [2.1, 0.13], [3.1, 0.2], [4.3, 0.02], [5.4, -0.02]]);
      const lean = U.keys(t, [[0, 0.02], [2.1, 0.02], [3.1, 0.11], [4.6, 0.05]]);
      const lookY = U.keys(t, [[0, 0.75], [3.7, 0.75], [4.4, -0.75]]);
      const lookX = U.keys(t, [[0, 1], [3.7, 1], [4.4, 0.25]]);
      const smile = U.keys(t, [[0, 0.22], [2.6, 0.32], [4.6, 0.52]]);
      let face = { smile, lookX, lookY, browUp: 0.35 * U.bump(t, 3.0, 0.9) };
      if (t > 5.0) face = { smile: 0.52, eyes: 'closed' };
      return { x: MX, y: MY, look: 'me', pose: 'sit', s: 1, t, facing: 1, lean, head: { tilt }, face };
    }
    // after: beaming at the flower he made matter; he leans in a little, a slow happy blink
    const lean = 0.05 + 0.06 * ez(t, 29.2, 31.0, 'inOutSine');
    const blink = U.bump(t, 31.9, 0.22);
    const face = { smile: 0.72 + 0.1 * ez(t, 29.2, 31), eyes: 'sparkle', lookX: 1, lookY: 0.6, open: 0.12, blink };
    return { x: MX, y: MY, look: 'me', pose: 'sit', s: 1, t, facing: 1, lean, head: { tilt: 0.12 + 0.04 * ez(t, 29.2, 31) }, face };
  }

  /* ---------------- the real golden forest ---------------- */
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
  /** soft golden wash with big bokeh — what the background becomes as we close in */
  function bokehWash(ctx, t, a) {
    if (a <= 0.01) return;
    ctx.save();
    ctx.setTransform(Art._base || new DOMMatrix());
    ctx.globalAlpha = a;
    soft(ctx, 'wash', 6, (c) => {
      const g = c.createRadialGradient(W * 0.62, H * 0.42, 60, W * 0.55, H * 0.5, W * 0.75);
      g.addColorStop(0, '#ffe7b6'); g.addColorStop(0.5, '#f0b26a'); g.addColorStop(1, '#a8662e');
      c.fillStyle = g; c.fillRect(0, 0, W, H);
      for (let i = 0; i < 14; i++) {
        const x = U.hash(i, 71) * W + Math.sin(t * 0.21 + i) * 30, y = 150 + U.hash(i, 72) * 780 + Math.cos(t * 0.17 + i) * 20;
        bokeh(c, x, y, 50 + U.hash(i, 73) * 110, i % 4 ? '#ffd79a' : '#ff9fbf', 0.1 + 0.08 * Math.sin(t * 0.6 + i * 2));
      }
    });
    ctx.restore();
  }
  /** the mossy rock, in the same style as scenes 02/03 (moss cap clipped to the rock) */
  function rockOutline(ctx, x, y, w, h, seed) {
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(seed, 1) * 8, y - h);
    ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    ctx.lineTo(x + w / 2, y);
    ctx.closePath();
  }
  function rockAt(ctx, t, rockCol = ROCK_GREY, mossCol = MOSS, lit = true) {
    const { x, y, w, h } = ROCK, seed = 7;
    ctx.fillStyle = 'rgba(30,24,10,0.25)';
    ctx.beginPath(); ctx.ellipse(x + 8, y + 2, w * 0.58, 12, 0, 0, TAU); ctx.fill();
    Art.rock(ctx, x, y, w, h, rockCol, seed);
    ctx.save();
    rockOutline(ctx, x, y, w, h, seed);
    ctx.clip();
    ctx.fillStyle = mossCol;
    ctx.beginPath();
    ctx.moveTo(x - w * 0.6, y - h * 1.2);
    ctx.lineTo(x + w * 0.6, y - h * 1.2);
    for (let i = 0; i <= 10; i++) {
      const k = 1 - i / 10;
      ctx.lineTo(x - w * 0.6 + w * 1.2 * k, y - h * (0.62 + 0.18 * Math.sin(k * 3.1)) + Math.sin(i * 2.3 + seed) * h * 0.06);
    }
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = U.shade(mossCol, 0.16);
    for (let i = 0; i < 7; i++) {
      const mx = x - w * 0.38 + i * w * 0.12, my = y - h * (0.84 + 0.1 * Math.sin(i * 1.7));
      ctx.beginPath(); ctx.arc(mx, my, 3 + U.hash(i, seed) * 4, 0, TAU); ctx.fill();
    }
    ctx.restore();
    if (lit) {
      // warm light on its sun side
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = 'rgba(255,196,120,0.5)'; ctx.lineWidth = 5; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(x - w * 0.1, y - h * 0.99); ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.0, x + w * 0.49, y - h * 0.22); ctx.stroke();
      ctx.restore();
    }
  }
  function drawMe(ctx, t, o, cam) {
    if (!o) return;
    const a = toScreen(cam, o.x - 90, o.y - 250), b = toScreen(cam, o.x + 190, o.y + 20);
    if (b.x < 0 || a.x > W || b.y < 139 || a.y > 941) return;          // off screen
    ctx.fillStyle = 'rgba(30,22,10,0.24)';
    ctx.beginPath(); ctx.ellipse(o.x + 22, o.y + 2, 74, 9, 0, 0, TAU); ctx.fill();
    // warm low sun from the right: a thin lit edge on his sun side
    rimLit(ctx, Object.assign({}, o, { shadow: false, glow: 0 }), 'me', '#ffd79c', 2.3, -0.7, 0.55);
  }
  function drawReal(ctx, t, cam, o) {
    const z = cam.z;
    const zFade = 1 - ez(z, 2.4, 4.4, 'inOutSine');     // the environment dissolves into bokeh as we close in
    const washA = 1 - zFade;
    if (washA > 0) bokehWash(ctx, t, washA);
    if (zFade > 0.03) {
      ctx.save();
      ctx.globalAlpha = zFade;
      soft(ctx, 'bg', 10, (c) => backdrop(c, t));
      ctx.restore();
      // light through leaves, out of focus
      for (let i = 0; i < 10; i++) {
        const bx = 380 + U.hash(i, 61) * 1150, by = 560 + U.hash(i, 62) * 220;
        const br = 14 + U.hash(i, 63) * 24;
        bokeh(ctx, bx + Math.sin(t * 0.3 + i) * 4, by, br, i % 3 ? '#ffd9a0' : '#fff2d4', 0.14 * zFade * (0.6 + 0.4 * Math.sin(t * 0.7 + i * 1.7)));
      }
    }
    // the trail and forest floor behind the flower
    const midSoft = ez(z, 2.35, 2.9, 'linear');
    const mid = (c) => {
        Art.ground(c, Object.assign({ color: U.mix(P.ground, '#6b6a2a', 0.2), color2: P.ground2 }, GOPT));
        Art.trail(c, Object.assign({ color: P.trail, depth: 40 }, GOPT));
        // dappled light on the trail
        c.save();
        c.globalCompositeOperation = 'lighter';
        for (let i = 0; i < 7; i++) {
          const x = 420 + U.hash(i, 81) * 1100, y = Art.groundY(x, GOPT) + 16 + U.hash(i, 82) * 16;
          const rx = 40 + U.hash(i, 83) * 50;
          c.save();
          c.translate(x, y); c.scale(1, 0.16);
          const g = c.createRadialGradient(0, 0, 0, 0, 0, rx);
          g.addColorStop(0, U.rgba('#ffd28a', 0.16 + 0.06 * Math.sin(t * 0.5 + i))); g.addColorStop(1, 'rgba(255,210,138,0)');
          c.fillStyle = g; c.fillRect(-rx, -rx, rx * 2, rx * 2);
          c.restore();
        }
        c.restore();
        Art.grass(c, { seed: 9, y: (x) => Art.groundY(x, GOPT) - 1, spacing: 9, h: 22, color: U.shade(P.grass, -0.15), color2: U.mix(P.grass, '#ffd486', 0.35), t, wind: 0.7 });
    };
    const groundTop = toScreen(cam, 0, GY - 40).y;
    if (z < 9 && groundTop < 941) {
      // sharp while we're at his distance; soft once we're inside the flower's world (two fixed levels, cross-faded)
      if (midSoft < 1) { ctx.save(); ctx.globalAlpha = 1 - midSoft; mid(ctx); ctx.restore(); }
      if (midSoft > 0) { ctx.save(); ctx.globalAlpha = midSoft; soft(ctx, 'mid', 9, mid); ctx.restore(); }
    }
    // the narrator
    if (o.me && z < 4.4) drawMe(ctx, t, o.me, cam);
    // the flower spot: rock, ferns, the flower
    if (z < 12) {
      rockAt(ctx, t);
      Art.fern(ctx, FERN.x, FERN.y, FERN.s, FERN_C1, U.wind(t, FERN.x, 2) * 0.7);
      Art.fern(ctx, FERN.x + 44, FERN.y + 4, FERN.s * 0.64, FERN_C2, U.wind(t, FERN.x + 44, 3) * 0.7);
    }
    drawFlower(ctx, t, o.fl, 'real', 1 - ez(z, 2, 5));
    if (z < 12) {
      // floor grass in front of the spot
      Art.grass(ctx, { seed: 17, y: (x) => 946 + Math.sin(x * 0.01) * 6, spacing: 8, h: 34, color: U.shade(P.grass, -0.3), color2: U.mix(P.grass, '#ffd486', 0.15), t, wind: 1 });
      // pollen in the light
      Art.motes(ctx, { seed: 12, count: 30, x0: 560, x1: 1500, y0: 580, y1: 940, t, color: '#ffe9b8', size: 1.4, drift: 9, glow: 0.8, alpha: 0.6 * zFade });
    }
    // near foreground blades, very soft
    if (z < 3.4) {
      soft(ctx, 'fg', 13, (c) => {
        Art.grass(c, { seed: 23, y: 1018, x0: 380, x1: 760, spacing: 15, h: 110, hVar: 0.5, width: 5, color: '#2f3a1e', t, wind: 0.5 });
        Art.grass(c, { seed: 24, y: 1024, x0: 1380, x1: 1640, spacing: 16, h: 100, hVar: 0.5, width: 5, color: '#2c351c', t, wind: 0.5 });
      }, { x: 0, y: 740, w: W, h: 340 });
    }
  }

  /* ---------------- the storybook ---------------- */
  const FR = { x0: 70, y0: 176, x1: W - 70, y1: 904 };          // hand-drawn frame (screen space)
  function makePaper() {
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    const x = c.getContext('2d');
    const r = U.rng(404);
    x.fillStyle = '#ecdcba'; x.fillRect(0, 0, W, H);
    for (let i = 0; i < 46; i++) {
      const px = r() * W, py = r() * H, rad = 120 + r() * 380;
      const g = x.createRadialGradient(px, py, 0, px, py, rad);
      const dark = r() < 0.55;
      g.addColorStop(0, dark ? 'rgba(150,110,60,0.09)' : 'rgba(255,250,232,0.12)');
      g.addColorStop(1, 'rgba(150,110,60,0)');
      x.fillStyle = g; x.fillRect(px - rad, py - rad, rad * 2, rad * 2);
    }
    x.lineCap = 'round';
    for (let i = 0; i < 380; i++) {
      const px = r() * W, py = r() * H, L = 6 + r() * 24, a = r() * TAU;
      x.strokeStyle = r() < 0.5 ? 'rgba(120,88,48,0.10)' : 'rgba(255,255,244,0.18)';
      x.lineWidth = 0.6 + r() * 0.9;
      x.beginPath(); x.moveTo(px, py);
      x.quadraticCurveTo(px + Math.cos(a) * L * 0.5 + (r() - 0.5) * 6, py + Math.sin(a) * L * 0.5 + (r() - 0.5) * 6, px + Math.cos(a) * L, py + Math.sin(a) * L);
      x.stroke();
    }
    for (let i = 0; i < 240; i++) { x.fillStyle = `rgba(92,62,30,${0.05 + r() * 0.12})`; x.beginPath(); x.arc(r() * W, r() * H, 0.5 + r() * 1.2, 0, TAU); x.fill(); }
    const v = x.createRadialGradient(W / 2, H / 2, H * 0.42, W / 2, H / 2, H * 1.02);
    v.addColorStop(0, 'rgba(120,76,32,0)'); v.addColorStop(1, 'rgba(120,76,32,0.45)');
    x.fillStyle = v; x.fillRect(0, 0, W, H);
    return c;
  }
  function makeGrain() {
    const c = document.createElement('canvas');
    c.width = c.height = 160;
    const x = c.getContext('2d');
    const img = x.createImageData(160, 160);
    const r = U.rng(77);
    for (let i = 0; i < img.data.length; i += 4) { const v = 196 + r() * 59; img.data[i] = v; img.data[i + 1] = v * 0.96; img.data[i + 2] = v * 0.86; img.data[i + 3] = 255; }
    x.putImageData(img, 0, 0);
    return c;
  }
  /** a towering trunk, inked */
  function sbTrunk(c, x, w, tone, yb, seed, ink) {
    const top = 380, N = 12;
    const edge = (side, k) => x + side * w * 0.5 * (1 - 0.14 * k) + U.noise1(k * 3.1, seed) * w * 0.1 + U.noise1(k * 9, seed + side) * w * 0.025;
    const outline = (side) => {
      c.beginPath();
      for (let i = 0; i <= N; i++) { const k = i / N; const y = lerp(yb, top, k); i ? c.lineTo(edge(side, k), y) : c.moveTo(edge(side, k) + side * w * 0.24, yb + 2); }
    };
    c.beginPath();
    for (let i = 0; i <= N; i++) { const k = i / N; const y = lerp(yb, top, k); i ? c.lineTo(edge(-1, k), y) : c.moveTo(edge(-1, k) - w * 0.24, yb + 2); }
    for (let i = N; i >= 0; i--) { const k = i / N; c.lineTo(edge(1, k) + (i === 0 ? w * 0.24 : 0), lerp(yb, top, k) + (i === 0 ? 2 : 0)); }
    c.closePath();
    c.fillStyle = tone; c.fill();
    c.save(); c.clip();
    c.fillStyle = U.rgba(INK, 0.18 * ink);
    c.fillRect(x - w * 0.62, top, w * 0.44, yb - top + 4);
    c.strokeStyle = U.rgba(INK, 0.32 * ink); c.lineCap = 'round';
    const lines = Math.max(3, Math.round(w / 11));
    for (let j = 0; j < lines; j++) {
      const lx = x - w * 0.45 + (j + U.hash(j, seed) * 0.6) * (w * 0.9 / lines);
      c.lineWidth = 0.9 + U.hash(j, seed + 1) * 1.3 * ink;
      c.beginPath();
      let y = yb - U.hash(j, seed + 2) * 40;
      c.moveTo(lx, y);
      while (y > top) { const ny = y - 40 - U.hash(Math.round(y), seed + j) * 50; c.quadraticCurveTo(lx + (U.hash(Math.round(ny), seed) - 0.5) * 6, (y + ny) / 2, lx + (U.hash(Math.round(ny) + 3, seed) - 0.5) * 4, ny); y = ny; }
      c.stroke();
    }
    c.restore();
    c.strokeStyle = U.rgba(INK, 0.55 * ink); c.lineWidth = 1.7;
    outline(-1); c.stroke();
    outline(1); c.stroke();
  }
  function sbLeaf(c, x, y, s, a, tone) {
    c.save(); c.translate(x, y); c.rotate(a); c.scale(s, s);
    c.fillStyle = tone;
    c.beginPath(); c.moveTo(-8, 0); c.quadraticCurveTo(0, -5, 8, 0); c.quadraticCurveTo(0, 5, -8, 0); c.fill();
    c.strokeStyle = U.rgba(INK, 0.35); c.lineWidth = 0.7;
    c.beginPath(); c.moveTo(-7, 0); c.lineTo(7, 0); c.stroke();
    c.restore();
  }
  /** everything in the storybook that never moves (world space, camera CB0) */
  function sbStatic(c) {
    const r = U.rng(91);
    // dim air: shade under the canopy, a paler haze lower down
    const g = c.createLinearGradient(0, 520, 0, 880);
    g.addColorStop(0, '#957b58'); g.addColorStop(0.55, '#cdb890'); g.addColorStop(1, '#bea67e');
    c.fillStyle = g; c.fillRect(200, 300, 1500, 800);
    // a faint shaft of light from the canopy
    c.save();
    c.globalCompositeOperation = 'lighter';
    const sg = c.createLinearGradient(1290, 520, 1060, 920);
    sg.addColorStop(0, 'rgba(255,244,214,0.18)'); sg.addColorStop(1, 'rgba(255,244,214,0)');
    c.fillStyle = sg;
    c.beginPath(); c.moveTo(1230, 500); c.lineTo(1390, 500); c.lineTo(1150, 930); c.lineTo(990, 930); c.closePath(); c.fill();
    c.restore();
    // far trunks (pale), a soft haze, mid trunks, near trunks (towering)
    const far = [392, 452, 520, 584, 650, 712, 836, 904, 1176, 1236, 1300, 1362, 1426];
    far.forEach((x, i) => sbTrunk(c, x + (r() - 0.5) * 14, 14 + r() * 16, '#d6c4a0', 850 + r() * 6, i + 1, 0.35));
    const hz = c.createLinearGradient(0, 740, 0, 870);
    hz.addColorStop(0, 'rgba(232,218,188,0)'); hz.addColorStop(1, 'rgba(232,218,188,0.55)');
    c.fillStyle = hz; c.fillRect(200, 740, 1500, 130);
    const mid = [430, 618, 1290, 1404];
    mid.forEach((x, i) => sbTrunk(c, x, 40 + r() * 26, '#a98e66', 864, i + 20, 0.6));
    sbTrunk(c, 336, 200, '#6f583b', 900, 41, 1);
    sbTrunk(c, 1492, 220, '#69533a', 904, 42, 1);
    sbTrunk(c, 560, 84, '#7f6747', 878, 43, 0.9);
    sbTrunk(c, 1344, 96, '#7a6244', 884, 44, 0.9);
    // the canopy overhead: dark, uneven leaf masses with branches and hanging sprays
    c.fillStyle = '#5b4730';
    c.beginPath();
    c.rect(300, 380, 1300, 140);
    let cx = 320;
    while (cx < 1600) {
      const rr = 16 + r() * 34, y = 512 + r() * 30 + Math.sin(cx * 0.011) * 22;
      c.moveTo(cx + rr, y); c.arc(cx, y, rr, 0, TAU);
      cx += rr * (0.9 + r() * 0.7);
    }
    c.fill();
    c.strokeStyle = '#4a3a27'; c.lineCap = 'round';
    for (let i = 0; i < 5; i++) {
      const bx = 380 + r() * 1100, by = 520 + r() * 20;
      c.lineWidth = 6 + r() * 5;
      c.beginPath(); c.moveTo(bx, by); c.quadraticCurveTo(bx + 60 + r() * 40, by + 10 + r() * 20, bx + 140 + r() * 80, by - 4 + r() * 20); c.stroke();
    }
    for (let i = 0; i < 14; i++) {
      const x = 360 + r() * 1100, y = 540 + r() * 26 + Math.sin(x * 0.011) * 20;
      const n = 3 + Math.floor(r() * 4);
      for (let k = 0; k < n; k++) sbLeaf(c, x + Math.sin(k * 1.9) * 7, y + k * 10 + r() * 6, 1.25 + r() * 0.5, 1.35 + (r() - 0.5) * 0.7, k % 2 ? '#4a3a27' : '#5f4a32');
    }
    // the forest floor: dim, crowded
    c.beginPath(); c.moveTo(200, 1100);
    for (let x = 200; x <= 1700; x += 20) c.lineTo(x, Art.groundY(x, GOPT) - 2);
    c.lineTo(1700, 1100); c.closePath();
    const fg = c.createLinearGradient(0, 860, 0, 990);
    fg.addColorStop(0, '#866e4e'); fg.addColorStop(1, '#4e3d2b');
    c.fillStyle = fg; c.fill();
    c.strokeStyle = U.rgba(INK, 0.55); c.lineWidth = 1.6;
    c.beginPath(); for (let x = 200; x <= 1700; x += 20) { const y = Art.groundY(x, GOPT) - 2; x > 200 ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke();
    for (let i = 0; i < 300; i++) {
      const x = 260 + r() * 1400, y = 872 + Math.pow(r(), 0.7) * 120;
      if (Math.abs(x - FX) < 34 && Math.abs(y - FY) < 14) continue;
      sbLeaf(c, x, y, 0.8 + r() * 1.0, (r() - 0.5) * 1.2, U.mix('#5f4b33', '#b09670', r()));
    }
    c.lineCap = 'round';
    for (let i = 0; i < 90; i++) {
      const x = 260 + r() * 1400, y = 876 + r() * 110;
      if (Math.abs(x - FX) < 50 && y > 880) continue;
      const hh = 14 + r() * 30;
      c.strokeStyle = U.mix(INK, '#6f583c', r() * 0.6); c.lineWidth = 1.4;
      c.beginPath();
      for (let k = 0; k < 5; k++) { const a = -0.6 + k * 0.3 + (r() - 0.5) * 0.2; c.moveTo(x, y); c.quadraticCurveTo(x + Math.sin(a) * hh * 0.4, y - hh * 0.6, x + Math.sin(a) * hh, y - hh * Math.cos(a)); }
      c.stroke();
    }
    for (let i = 0; i < 9; i++) {
      const x = 300 + r() * 1350, y = 900 + r() * 70;
      if (Math.abs(x - FX) < 130 || Math.abs(x - MX) < 70) continue;
      Art.fern(c, x, y, 0.6 + r() * 0.5, U.mix('#5f4b33', '#86704f', r()), (r() - 0.5) * 2);
    }
    for (let i = 0; i < 7; i++) {
      const x = 330 + r() * 1300, y = 912 + r() * 60;
      if (Math.abs(x - FX) < 110) continue;
      const s = 0.8 + r() * 0.7;
      c.fillStyle = '#d8c7a4'; c.fillRect(x - 2.5 * s, y - 12 * s, 5 * s, 12 * s);
      c.fillStyle = '#7a5c3c'; c.beginPath(); c.ellipse(x, y - 12 * s, 11 * s, 7 * s, 0, Math.PI, TAU); c.fill();
      c.strokeStyle = U.rgba(INK, 0.6); c.lineWidth = 1; c.stroke();
    }
    for (let i = 0; i < 26; i++) {
      const x = 260 + r() * 1400, y = 890 + r() * 110;
      c.fillStyle = U.mix('#9d8763', '#5d4a35', r());
      c.beginPath(); c.ellipse(x, y, 4 + r() * 6, 3 + r() * 3, 0, 0, TAU); c.fill();
    }
    // the flower spot: mossy rock and fern, inked
    c.fillStyle = 'rgba(42,27,16,0.25)';
    c.beginPath(); c.ellipse(ROCK.x + 6, ROCK.y + 2, ROCK.w * 0.56, 12, 0, 0, TAU); c.fill();
    rockAt(c, 0, '#a08d6c', '#6e5a3e', false);
    c.strokeStyle = U.rgba(INK, 0.6); c.lineWidth = 1.8;
    rockOutline(c, ROCK.x, ROCK.y, ROCK.w, ROCK.h, 7); c.stroke();
    Art.fern(c, FERN.x, FERN.y, FERN.s, '#6a5538', 0);
    Art.fern(c, FERN.x + 44, FERN.y + 4, FERN.s * 0.64, '#7a6446', 0.3);
    c.fillStyle = '#5f4c35';
    c.beginPath(); c.ellipse(FX, FY + 2, 30, 6, 0, 0, TAU); c.fill();
    // a dim, close vignette inside the picture
    const vg = c.createRadialGradient(990, 760, 140, 990, 760, 760);
    vg.addColorStop(0, 'rgba(60,40,20,0)'); vg.addColorStop(1, 'rgba(60,40,20,0.38)');
    c.fillStyle = vg; c.fillRect(200, 300, 1500, 800);
    // paper tooth over the ink
    c.save();
    c.globalCompositeOperation = 'multiply';
    c.globalAlpha = 0.5;
    c.fillStyle = c.createPattern(GRAIN, 'repeat');
    c.fillRect(200, 300, 1500, 800);
    c.restore();
  }
  // built once at load (pure function of nothing): paper, grain, the static page
  const GRAIN = makeGrain();
  const PAPERTEX = makePaper();
  const SBSTATIC = (() => {
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    const x = c.getContext('2d');
    x.setTransform(camMatrix(CB0));
    sbStatic(x);
    return c;
  })();
  function drawCachedStatic(ctx) {
    ctx.save();
    ctx.setTransform(ctx.getTransform().multiply(camMatrix(CB0).inverse()));
    ctx.drawImage(SBSTATIC, 0, 0, W, H);
    ctx.restore();
  }
  /** the drifting seed: a tiny parachute */
  function pappus(c, x, y, s, ang, a) {
    c.save();
    c.translate(x, y); c.rotate(ang); c.scale(s, s);
    c.globalAlpha *= a;
    c.strokeStyle = INK; c.lineCap = 'round';
    c.lineWidth = 1.3;
    c.beginPath(); c.moveTo(0, 8); c.lineTo(0, -12); c.stroke();
    c.fillStyle = INK;
    c.beginPath(); c.moveTo(0, 6); c.quadraticCurveTo(3.2, 11, 0, 17); c.quadraticCurveTo(-3.2, 11, 0, 6); c.fill();
    c.lineWidth = 0.8;
    c.strokeStyle = U.rgba(INK, 0.85);
    c.beginPath();
    for (let i = 0; i < 15; i++) {
      const aa = -Math.PI / 2 + (i / 14 - 0.5) * 2.7;
      const L = 17 + Math.sin(i * 1.7) * 2;
      c.moveTo(0, -12); c.quadraticCurveTo(Math.cos(aa) * L * 0.5, -12 + Math.sin(aa) * L * 0.6, Math.cos(aa) * L, -12 + Math.sin(aa) * L);
    }
    c.stroke();
    c.fillStyle = U.rgba(INK, 0.7);
    for (let i = 0; i < 15; i += 2) {
      const aa = -Math.PI / 2 + (i / 14 - 0.5) * 2.7;
      const L = 17 + Math.sin(i * 1.7) * 2;
      c.beginPath(); c.arc(Math.cos(aa) * L, -12 + Math.sin(aa) * L, 0.9, 0, TAU); c.fill();
    }
    c.restore();
  }
  function seedPos(t) {
    const p = U.prog(t, TL.seed0, TL.land);
    const y = lerp(500, FY - 9, ez(p, 0, 1, 'inOutSine') * 0.35 + p * 0.65);
    const amp = 80 * (1 - p * 0.85);
    const x = FX - 60 + 60 * p + Math.sin(p * Math.PI * 2.2 + 0.4) * amp;
    const ang = Math.cos(p * Math.PI * 2.2 + 0.4) * 0.45 * (1 - p * 0.7);
    return { x, y, ang, p };
  }
  function sprout(c, t) {
    const k = U.prog(t, TL.sprout0, TL.flower0 + 0.3);
    if (k <= 0) return;
    const fade = 1 - ez(t, TL.flower0, TL.flower0 + 0.35);
    if (fade <= 0) return;
    const h = 46 * U.E.outBack(clamp(k * 1.4));
    const hook = 1 - ez(k, 0.35, 0.8, 'outBack');
    c.save();
    c.globalAlpha *= fade;
    c.strokeStyle = '#4a3a28'; c.lineWidth = 4.4; c.lineCap = 'round';
    Art.glow(c, FX, FY - h * 0.7, 46, '#fff1d0', 0.35 * fade);
    const tx = FX + hook * 6, ty = FY - h;
    c.beginPath(); c.moveTo(FX, FY); c.quadraticCurveTo(FX + 2, FY - h * 0.6, tx, ty); c.stroke();
    const open = U.E.outBack(ez(k, 0.45, 1, 'linear'));
    for (const dir of [-1, 1]) {
      c.save(); c.translate(tx, ty); c.rotate(dir * (0.25 + open * 1.0) - hook * 1.6);
      c.fillStyle = '#6d5a40';
      c.beginPath(); c.ellipse(0, -13 * open - 2, 5 + 4.5 * open, 13 * open + 2, 0, 0, TAU); c.fill();
      c.strokeStyle = U.rgba(INK, 0.7); c.lineWidth = 1; c.stroke();
      c.restore();
    }
    c.restore();
  }
  function hikerLegs(c, t) {
    const keys = ['h1', 'h2', 'h4'];
    for (let j = 0; j < 3; j++) {
      const u = (t - TL.hikers[j]) / TL.cross;
      if (u < -0.02 || u > 1.02) continue;
      const x = lerp(-420, 2350, u);
      const s = 4.2 + j * 0.15;
      const y = 958 + j * 5;
      c.fillStyle = 'rgba(42,27,16,0.28)';
      c.beginPath(); c.ellipse(x + 20, y, 46 * s, 13, 0, 0, TAU); c.fill();
      for (let k = 4; k >= 0; k--) {
        const xx = x - k * 46;
        Art.person(c, { x: xx, y, s, look: sepLook(keys[j], -0.1), walk: xx / (KF(1) * s) + j, facing: 1, t, alpha: k ? 0.13 : 0.97, shadow: false });
      }
    }
  }
  /** days and seasons turning: tone, sun/moon, leaves then snow */
  function seasons(c, t) {
    if (t < TL.seas0 - 0.3 || t > TL.seas1 + 0.4) return;
    const env = U.fade(t, TL.seas0 - 0.3, TL.seas1 + 0.4, 0.4, 0.5);
    const per = (TL.seas1 - TL.seas0) / 2;
    const u = U.fract((t - TL.seas0) / per);
    const on = t > TL.seas0 ? 1 : 0;
    const night = U.bump(u, 0.74, 0.3) * env * on;
    c.save();
    c.setTransform(Art._base || new DOMMatrix());
    c.fillStyle = U.rgba('#1c2030', 0.45 * night);
    c.fillRect(0, 0, W, H);
    const day = u < 0.5;
    const q = day ? u / 0.5 : (u - 0.5) / 0.5;
    const ax = lerp(FR.x0 + 170, FR.x1 - 170, q), ay = FR.y0 + 150 - Math.sin(q * Math.PI) * 70;
    const ia = env * Math.sin(q * Math.PI) * on;
    if (ia > 0.01) {
      c.globalAlpha = ia;
      c.strokeStyle = INK; c.lineWidth = 2.4; c.lineCap = 'round';
      if (day) {
        c.fillStyle = '#f6e7c4';
        c.beginPath(); c.arc(ax, ay, 28, 0, TAU); c.fill(); c.stroke();
        c.beginPath();
        for (let i = 0; i < 10; i++) { const a = i / 10 * TAU + t; c.moveTo(ax + Math.cos(a) * 37, ay + Math.sin(a) * 37); c.lineTo(ax + Math.cos(a) * 50, ay + Math.sin(a) * 50); }
        c.stroke();
      } else {
        c.fillStyle = '#efe4cc';
        c.beginPath(); c.arc(ax, ay, 26, 0, TAU); c.arc(ax + 12, ay - 8, 22, 0, TAU, true); c.fill('evenodd');
        c.beginPath(); c.arc(ax, ay, 26, 0.9, 5.4); c.stroke();
      }
    }
    c.restore();
    const leafA = U.fade(t, TL.seas0, TL.seas0 + per * 1.05, 0.2, 0.3);
    for (let i = 0; i < 10 && leafA > 0; i++) {
      const ph = U.fract((t - TL.seas0) * (0.5 + U.hash(i, 3) * 0.3) + U.hash(i, 4));
      const x = 420 + U.hash(i, 5) * 1000 + Math.sin(ph * 9 + i) * 34, y = 540 + ph * 420;
      sbLeaf(c, x, y, 1.7, ph * 8 + i, U.mix('#5f4b33', '#b09670', U.hash(i, 6)));
    }
    const snowA = U.fade(t, TL.seas0 + per * 0.95, TL.seas1 + 0.4, 0.25, 0.4);
    if (snowA > 0) {
      c.fillStyle = U.rgba('#fbf5e8', 0.92 * snowA);
      c.beginPath();
      for (let i = 0; i < 70; i++) {
        const sp = 0.5 + U.hash(i, 7) * 0.5;
        const y = 530 + U.fract((t - TL.seas0) * sp * 0.55 + U.hash(i, 8)) * 450;
        const x = 380 + U.hash(i, 9) * 1080 + Math.sin(t * 2 + i) * 9;
        const rr = 1.5 + U.hash(i, 10) * 2;
        c.moveTo(x + rr, y); c.arc(x, y, rr, 0, TAU);
      }
      c.fill();
    }
  }
  /** foot travel per radian of walk phase at scale 1 (mean over a step, from the kit's leg rig) */
  const KF = (stride) => 72.32 * Math.sin(0.42 * stride);
  const LEG = 114;                                   // thigh + shin of the rig
  /**
   * Body travel per radian that keeps the stance foot planted. The rig's stance leg sweeps
   * sinusoidally, so a constant rate makes the planted foot slide; we blend 65% toward the
   * exact rate (phase runs quicker through double support), cutting the slip to about a third.
   */
  function plantRate(ph, stride) {
    const exact = LEG * 0.42 * stride * Math.abs(Math.cos(ph)) * Math.cos(0.42 * stride * Math.sin(ph));
    return lerp(KF(stride), exact, 0.65);
  }
  const ARR_X0 = MX - 470, ARR_PH0 = 0.6;
  const arrX = (t) => lerp(ARR_X0, MX, ez(t, TL.came0, TL.stop, 'outSine'));
  const arrStride = (t) => 0.25 + 0.75 * clamp((1 - ez(t, TL.came0, TL.stop, 'outSine')) * 1.6);
  /** walk phase for his path (integrated, so it stays a pure function of t) */
  function arrPhase(t) {
    const t1 = clamp(t, TL.came0, TL.stop);
    const N = 72;
    let ph = ARR_PH0;
    for (let i = 0; i < N; i++) {
      const a = lerp(TL.came0, t1, i / N), b = lerp(TL.came0, t1, (i + 1) / N);
      ph += (arrX(b) - arrX(a)) / plantRate(ph, arrStride((a + b) / 2));
    }
    return ph;
  }
  /** him, arriving: a silhouette with warm light behind him */
  function arrivalPose(t) {
    const x0 = ARR_X0;
    const k = ez(t, TL.came0, TL.stop, 'outSine');
    const x = lerp(x0, MX, k);
    // a snap into the crouch (silhouettes can't cross-fade cleanly), settling down on a spring
    const crouch = t >= TL.stop ? 1 : 0;
    const settle = t >= TL.stop ? -0.34 * (1 - U.spring(t - TL.stop, 2.1, 6.5)) : 0;   // torso pitches down into it
    const look = ez(t, TL.saw0 - 0.1, TL.saw0 + 0.5, 'inOutSine');
    const lean = ez(t, TL.saw0 + 0.8, TL.made0, 'inOutSine');
    return { x, walk: arrPhase(t), stride: arrStride(t), crouch, settle, look, lean, a: ez(t, TL.came0 - 0.1, TL.came0 + 0.4) };
  }
  const SIL = '#2b1c11';
  function drawArrival(ctx, t) {
    const ap = arrivalPose(t);
    if (ap.a <= 0) return null;
    const base = { x: ap.x, y: MY, s: 1, facing: 1, t, shadow: false, alpha: ap.a, face: { eyes: 'closed', smile: 0, blink: 1 } };
    const pose = !ap.crouch ? { walk: ap.walk, stride: ap.stride }
      : { pose: 'crouch', head: { tilt: 0.04 + 0.24 * ap.look - ap.settle * 0.5 }, lean: -0.06 + ap.settle + 0.06 * ap.look + 0.05 * ap.lean };
    // warm light behind him, spreading toward the flower
    const wl = ez(t, TL.came0 - 0.2, TL.stop + 0.4, 'inOutSine');
    Art.glow(ctx, ap.x - 200, MY - 170, 900, '#ffb35c', 0.55 * wl);
    Art.glow(ctx, ap.x - 70, MY - 150, 340, '#fff0cf', 0.5 * wl);
    // a silhouette against the warm light, rim-lit on the side the light comes from
    const head = rimLit(ctx, Object.assign({}, base, pose), 'me', '#ffd08a', -3.8, -1.0, 0.95, flatLook('me', SIL)).head;
    // the kit draws some face strokes in fixed colours: fill the head so the silhouette stays pure
    ctx.save();
    ctx.globalAlpha *= ap.a;
    ctx.fillStyle = SIL;
    ctx.beginPath(); ctx.arc(head.x, head.y, head.r - 0.6, 0, TAU); ctx.fill();
    ctx.restore();
    return head;
  }
  /** draws the page; returns the flower head (world) */
  /**
   * o.alpha: fade the page in over whatever is beneath (paper outside the picture,
   * the picture inside: a true cross-dissolve without an offscreen layer).
   * o.hole(ctx): a path the page must leave uncovered (the colour flood).
   */
  function drawStorybook(ctx, t, cam, o = {}) {
    const base = Art._base || new DOMMatrix();
    const IN = [FR.x0 + 10, FR.y0 + 10, FR.x1 - FR.x0 - 20, FR.y1 - FR.y0 - 20];
    ctx.save();
    ctx.setTransform(base);
    if (o.hole) { ctx.beginPath(); ctx.rect(-10, -10, W + 20, H + 20); o.hole(ctx, true); ctx.clip('evenodd'); }
    ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha;
    ctx.save();
    ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.rect(IN[0], IN[1], IN[2], IN[3]); ctx.clip('evenodd');
    ctx.drawImage(PAPERTEX, 0, 0, W, H);
    ctx.restore();
    ctx.save();
    ctx.beginPath(); ctx.rect(IN[0], IN[1], IN[2], IN[3]); ctx.clip();
    applyCam(ctx, cam);
    drawCachedStatic(ctx);
    // the seed drifting down, catching a little light
    if (t > TL.seed0 && t < TL.land + 0.6) {
      const sp = seedPos(Math.min(t, TL.land));
      const a = t > TL.land ? 1 - ez(t, TL.land, TL.land + 0.5) : ez(t, TL.seed0, TL.seed0 + 0.4);
      Art.glow(ctx, sp.x, sp.y - 10, 60, '#fff4d6', 0.55 * a);
      pappus(ctx, sp.x, sp.y, 2.1, sp.ang, a);
      if (t > TL.land) {
        const k = U.prog(t, TL.land, TL.land + 0.6);
        ctx.fillStyle = U.rgba('#cdb894', 0.7 * (1 - k));
        for (let i = 0; i < 7; i++) { const a2 = Math.PI + (i / 6) * Math.PI; ctx.beginPath(); ctx.arc(FX + Math.cos(a2) * 28 * k, FY - 2 + Math.sin(a2) * 10 * k, 2 + 2 * k, 0, TAU); ctx.fill(); }
      }
    }
    sprout(ctx, t);
    const fl = flowerState(t, true);
    drawFlower(ctx, t, fl, 'sepia');
    hikerLegs(ctx, t);
    seasons(ctx, t);
    // "I saw it": the flower takes colour, a ring of colour pulses out of it (behind him)
    let fh = null;
    if (fl.show) fh = { x: FX + (fl.droop || 0) * 34 * fl.s, y: FY - 150 * fl.s * (1 - (fl.droop || 0) * 0.28) };
    if (fl.sat > 0.01) drawFlower(ctx, t, fl, 'tint');
    if (fh && t > TL.ring - 0.1 && t < TL.ring + 1.8) {
      for (const [d, col, w] of [[0, '#ff4f8f', 9], [0.22, '#ffc94a', 6]]) {
        const k = U.prog(t, TL.ring + d, TL.ring + d + 1.35);
        if (k <= 0 || k >= 1) continue;
        const rr = 26 + U.E.outCubic(k) * 470;
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        ctx.strokeStyle = U.rgba(col, 0.85 * (1 - k));
        ctx.lineWidth = w * (1 - k * 0.7);
        ctx.beginPath(); ctx.arc(fh.x, fh.y, rr, 0, TAU); ctx.stroke();
        ctx.strokeStyle = U.rgba(col, 0.22 * (1 - k));
        ctx.lineWidth = w * 4;
        ctx.stroke();
        ctx.restore();
      }
    }
    // him, arriving in warm light
    const head = t > TL.came0 - 0.2 && !(o.covers && o.covers(MX - 150, MY - 270, MX + 200, MY + 20)) ? drawArrival(ctx, t) : null;
    // ...and his gaze, a dotted line of light to the flower
    if (head && fh && t > TL.saw0) {
      const ga = ez(t, TL.saw0 + 0.1, TL.saw0 + 0.5) * (1 - ez(t, TL.ring + 0.3, TL.ring + 1.3));
      const ex = head.x + 16, ey = head.y + 2;
      const n = 12;
      for (let i = 1; i < n; i++) {
        const k = i / n;
        const vis = clamp((ez(t, TL.saw0 + 0.1, TL.saw0 + 0.8, 'linear') * (n + 1) - i) / 1.5);
        if (vis <= 0) continue;
        const x = lerp(ex, fh.x - 26, k), y = lerp(ey, fh.y - 4, k) - Math.sin(k * Math.PI) * 30;
        Art.glow(ctx, x, y, 14, '#ffcf7a', 0.55 * ga * vis);
        ctx.fillStyle = U.rgba('#fff2d0', 0.95 * ga * vis);
        ctx.beginPath(); ctx.arc(x, y, 3.4, 0, TAU); ctx.fill();
      }
    }
    ctx.restore();
    // paper tooth over the moving parts, then the inked frame
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.globalAlpha = 0.25;
    ctx.fillStyle = ctx.createPattern(GRAIN, 'repeat');
    ctx.fillRect(FR.x0, FR.y0, FR.x1 - FR.x0, FR.y1 - FR.y0);
    ctx.restore();
    drawFrame(ctx, ez(t, TL.diss0 + 1.2, TL.diss1, 'inOutSine'));
    ctx.restore();
    return fh;
  }
  /** the hand-inked double border, drawn on clockwise */
  function framePts(inset, seed) {
    const pts = [];
    const x0 = FR.x0 + inset, y0 = FR.y0 + inset, x1 = FR.x1 - inset, y1 = FR.y1 - inset;
    const side = (ax, ay, bx, by, n, s) => { for (let i = 0; i < n; i++) { const k = i / n; const j = U.noise1(k * 7 + s, seed) * 2.2; pts.push([lerp(ax, bx, k) + (ay === by ? 0 : j), lerp(ay, by, k) + (ay === by ? j : 0)]); } };
    side(x0, y0, x1, y0, 60, 0); side(x1, y0, x1, y1, 26, 10); side(x1, y1, x0, y1, 60, 20); side(x0, y1, x0, y0, 26, 30);
    pts.push(pts[0]);
    return pts;
  }
  const FRAME_A = framePts(0, 3), FRAME_B = framePts(11, 7);
  function drawFrame(ctx, prog) {
    if (prog <= 0) return;
    ctx.save();
    ctx.strokeStyle = U.rgba(INK, 0.85); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const [pts, lw] of [[FRAME_A, 3], [FRAME_B, 1.4]]) {
      const f = (pts.length - 1) * prog, n = Math.floor(f);
      ctx.lineWidth = lw;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) i ? ctx.lineTo(pts[i][0], pts[i][1]) : ctx.moveTo(pts[i][0], pts[i][1]);
      if (n < pts.length - 1) { const a = pts[n], b = pts[n + 1], k = f - n; ctx.lineTo(lerp(a[0], b[0], k), lerp(a[1], b[1], k)); }
      ctx.stroke();
    }
    const fa = ez(prog, 0.85, 1, 'linear');
    if (fa > 0) {
      ctx.globalAlpha = fa;
      ctx.lineWidth = 1.6;
      for (const [cx, cy, sx, sy] of [[FR.x0, FR.y0, 1, 1], [FR.x1, FR.y0, -1, 1], [FR.x1, FR.y1, -1, -1], [FR.x0, FR.y1, 1, -1]]) {
        ctx.beginPath();
        ctx.moveTo(cx + sx * 26, cy + sy * 5); ctx.quadraticCurveTo(cx + sx * 26, cy + sy * 26, cx + sx * 5, cy + sy * 26);
        ctx.moveTo(cx + sx * 18, cy + sy * 15); ctx.arc(cx + sx * 15, cy + sy * 15, 3, 0, TAU);
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  /* ---------------- the golden heart (an identical copy lives in 05) ---------------- */
  const HEART_N = 610;
  const HEART_COL = ['#8a4508', '#9f540d', '#b26414', '#c2761c', '#cf8826'];
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
  const heartRot = (t) => t * 0.05;

  /* ---------------- the scene ---------------- */
  Film.scene({
    id: 'flower-story',
    order: 4,
    title: 'The Flower’s Story',
    duration: D,
    mood: 'tender',
    sfx: [
      [0.4, 'bird', { gain: 0.3 }],
      [5.5, 'paper', { gain: 0.5 }],
      [6.6, 'scratch', { gain: 0.22 }],
      [8.2, 'wind', { gain: 0.22 }],
      [10.9, 'tap', { gain: 0.25 }],
      [11.3, 'pop', { gain: 0.2 }],
      [13.95, 'whoosh', { gain: 0.35 }],
      [14.3, 'thud', { gain: 0.45 }],
      [15.0, 'thud', { gain: 0.4 }],
      [15.65, 'thud', { gain: 0.35 }],
      [16.05, 'clock', { gain: 0.3 }],
      [18.6, 'footsteps', { gain: 0.25 }],
      [18.9, 'swell', { gain: 0.3 }],
      [21.9, 'heartbeat', { gain: 0.35 }],
      [22.65, 'chime', { gain: 0.55 }],
      [24.55, 'breath', { gain: 0.3 }],
      [24.85, 'bloom', { gain: 0.8 }],
      [25.0, 'sparkle', { gain: 0.7 }],
      [25.1, 'swell', { gain: 0.6 }],
      [27.4, 'bird', { gain: 0.35 }],
      [29.0, 'shimmer', { gain: 0.3 }],
      [38.4, 'shimmer', { gain: 0.45 }],
    ],
    fadeIn: 1.2,
    fadeOut: 0,
    post: (t) => ({
      vignette: lerp(0.4, 0.42, ez(t, 36, D)),
      grain: 0.045 + 0.02 * U.fade(t, TL.diss0, TL.flood1, 1.5, 1.0),
      letterbox: 1,
    }),

    render(ctx, t) {
      const cam = camAt(t);
      // the final frames are inside the golden heart: draw only that (05 continues it exactly)
      if (RH * cam.z >= 1105) {
        heart(ctx, W / 2, H / 2, RH * cam.z, heartRot(t));
        Art.captions(ctx, t, CAPS);
        return;
      }
      const fl = flowerState(t);
      const book = ez(t, TL.diss0 + 0.5, TL.diss1 - 0.5, 'inOutSine');      // storybook opacity
      const inBook = t > TL.diss0 + 0.5 && t < TL.flood1;
      const drawRealAll = (c) => {
        c.save();
        applyCam(c, cam);
        drawReal(c, t, cam, { me: meReal(t), fl });
        // the high-detail heart takes over from the kit's seed head as we close in
        const hk = ez(cam.z, 2.6, 6, 'linear');
        if (hk > 0) { c.save(); c.globalAlpha = hk; heart(c, HX0, HY0, RH, heartRot(t)); c.restore(); }
        c.restore();
        // warm side light from the right
        c.save();
        const wl = c.createLinearGradient(W * 0.5, 0, W, 0);
        wl.addColorStop(0, 'rgba(255,170,80,0)'); wl.addColorStop(1, 'rgba(255,170,80,0.12)');
        c.globalCompositeOperation = 'lighter';
        c.fillStyle = wl; c.fillRect(W * 0.5, 0, W * 0.5, H);
        c.restore();
      };
      if (!inBook || book < 1) {
        drawRealAll(ctx);
        // into the storybook: drain colour toward sepia
        const drain = ez(t, TL.diss0, TL.diss0 + 1.6, 'inOutSine') * (t < TL.flood0 ? 1 : 0);
        if (drain > 0) Art.colorize(ctx, '#a07a4e', 0.88 * drain);
      }
      if (inBook) {
        if (book < 1) {
          drawStorybook(ctx, t, camBase(Math.max(t, TL.diss1 + 0.2)), { alpha: book });
        } else if (t < TL.flood0) {
          drawStorybook(ctx, t, camBase(t));
        } else {
          // ---- "I made it matter": colour floods out of the flower, repainting the page ----
          const st = flowerState(t, true);
          const hs = toScreen(cam, FX, FY - 150 * st.s);
          const k = U.prog(t, TL.flood0, TL.flood1);
          const R = 1550 * (1 - Math.pow(1 - k, 2.1)) + 8;
          const wob = (a) => 0.05 * Math.sin(3 * a + 1.3) + 0.03 * Math.sin(5 * a + t * 1.7) + 0.02 * Math.sin(11 * a - t * 2.3);
          const path = (c, rr, cont) => {
            if (!cont) c.beginPath();
            for (let i = 0; i <= 96; i++) {
              const a = (i / 96) * TAU, r2 = rr * (1 + wob(a));
              i ? c.lineTo(hs.x + Math.cos(a) * r2, hs.y + Math.sin(a) * r2) : c.moveTo(hs.x + Math.cos(a) * r2, hs.y + Math.sin(a) * r2);
            }
            c.closePath();
          };
          const covers = (x0, y0, x1, y1) => {
            const a = toScreen(cam, x0, y0), b = toScreen(cam, x1, y1);
            const far = Math.max(Math.hypot(a.x - hs.x, a.y - hs.y), Math.hypot(b.x - hs.x, a.y - hs.y), Math.hypot(a.x - hs.x, b.y - hs.y), Math.hypot(b.x - hs.x, b.y - hs.y));
            return R * 0.9 > far;
          };
          drawStorybook(ctx, t, camBase(t), { hole: (c, cont) => path(c, R, cont), covers });
          // colour racing ahead of the repaint
          const fa = 1 - ez(k, 0.8, 1);
          if (fa > 0.03 && R < 1350) {
          ctx.save();
          ctx.globalCompositeOperation = 'lighter';
          const halo = ctx.createRadialGradient(hs.x, hs.y, R * 0.9, hs.x, hs.y, R * 1.25 + 60);
          halo.addColorStop(0, 'rgba(255,120,170,0.0)'); halo.addColorStop(0.25, U.rgba('#ff6aa2', 0.22 * fa)); halo.addColorStop(1, 'rgba(255,170,90,0)');
          const hr = R * 1.25 + 60;
          ctx.fillStyle = halo; ctx.fillRect(Math.max(0, hs.x - hr), Math.max(0, hs.y - hr), Math.min(W, hs.x + hr) - Math.max(0, hs.x - hr), Math.min(H, hs.y + hr) - Math.max(0, hs.y - hr));
          ctx.restore();
          }
          ctx.save();
          path(ctx, R);
          ctx.clip();
          drawRealAll(ctx);
          ctx.restore();
          // the wavefront: warm light with a magenta leading edge
          if (fa > 0.03) {
          ctx.save();
          ctx.globalCompositeOperation = 'lighter';
          path(ctx, R + 10);
          ctx.strokeStyle = U.rgba('#ff5d98', 0.55 * fa); ctx.lineWidth = 6; ctx.stroke();
          path(ctx, R);
          ctx.strokeStyle = U.rgba('#ffcf78', 0.25 * fa); ctx.lineWidth = 54; ctx.stroke();
          ctx.strokeStyle = U.rgba('#fff3d6', 0.5 * fa); ctx.lineWidth = 12; ctx.stroke();
          ctx.restore();
          for (let i = 0; i < 28; i++) {
            const a = U.hash(i, 31) * TAU;
            const rr = R * (1 + wob(a)) + (U.hash(i, 32) - 0.5) * 44;
            const x = hs.x + Math.cos(a) * rr, y = hs.y + Math.sin(a) * rr;
            if (x < -20 || x > W + 20 || y < 120 || y > 960) continue;
            twinkle(ctx, x, y, 9 + U.hash(i, 33) * 12, i % 3 ? '#fff0c8' : '#ff9cc0', fa * (0.5 + 0.5 * Math.sin(t * 12 + i * 2)));
          }
          }
        }
      }
      // light bloom at the moment it matters
      if (t > TL.bloom - 0.1 && t < TL.bloom + 2.6) {
        const st = flowerState(t, true);
        const hp = toScreen(cam, FX, FY - 150 * st.s);
        // the light swells as the petals open (it must not white them out)
        const fl2 = U.E.inOutSine(U.prog(t, TL.bloom + 0.05, TL.bloom + 0.42)) * Math.exp(-Math.max(0, t - TL.bloom - 0.42) * 2.2);
        if (fl2 > 0.05) {
          Art.glow(ctx, hp.x, hp.y, 720, '#ffdcaa', 0.3 * fl2);
          Art.glow(ctx, hp.x, hp.y, 200, '#fff6e6', 0.26 * fl2);
          ctx.save();
          ctx.translate(hp.x, hp.y); ctx.scale(5, 0.08);
          Art.glow(ctx, 0, 0, 260, '#ffd6a8', 0.42 * fl2);
          ctx.restore();
        }
        for (let i = 0; i < 18; i++) {
          const u = U.prog(t, TL.bloom + U.hash(i, 41) * 0.15, TL.bloom + 1.7 + U.hash(i, 42) * 0.7);
          if (u <= 0 || u >= 1) continue;
          const a = U.hash(i, 43) * TAU, d = U.E.outCubic(u) * (160 + U.hash(i, 44) * 260);
          twinkle(ctx, hp.x + Math.cos(a) * d, hp.y + Math.sin(a) * d * 0.8 - u * 40, 9 + U.hash(i, 45) * 9, i % 2 ? '#ffe7b0' : '#ffb3cf', (1 - u) * (0.6 + 0.4 * Math.sin(t * 14 + i)));
        }
      }
      // a slow sparkle around the newly meaningful flower
      if (t > TL.flood1 - 0.5 && cam.z < 6) {
        const st = flowerState(t);
        const hp = toScreen(cam, FX, FY - 150 * st.s);
        const a = ez(t, TL.flood1 - 0.5, TL.flood1 + 0.8) * (1 - ez(cam.z, 2.4, 5));
        for (let i = 0; i < 10; i++) {
          const ph = U.fract(t * (0.18 + U.hash(i, 51) * 0.12) + U.hash(i, 52));
          const ang = U.hash(i, 53) * TAU + t * 0.2;
          const d = (80 + U.hash(i, 54) * 140) * cam.z / 1.6;
          twinkle(ctx, hp.x + Math.cos(ang) * d, hp.y + Math.sin(ang) * d * 0.7 - ph * 60, 5 + U.hash(i, 55) * 6, '#fff1c8', a * Math.sin(ph * Math.PI) * 0.8);
        }
      }
      Art.captions(ctx, t, CAPS);
    },
  });
})();
