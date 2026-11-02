/* ==========================================================================
   06 · The Inner Voice — golden afternoon, then a split-screen argument.
   We dissolve in on 05's last shot: the narrator sitting with his flower.
   A warm light kindles in his head and pops out as WONDER (the amber
   emotion), who perches on his pack, taps his shoulder and writes her words
   in the air: "Let's stop the current activity / and ask ourselves—what does
   this flower mean to me?" With one stroke of light she splits the screen.
   LEFT: the summit path as a cold machine — identical hikers stamped out
   in lockstep up an escalator to a summit icon, steps counter, progress
   bars, a checklist whose "meaningful" box never ticks, selfie flashes, a
   ticking clock. RIGHT: the flower, alive in gold light and pollen.
   On "pausing and reflecting" the machine stalls; warm light spills over
   the seam and the hikers look up; the flower side widens to fill the
   frame, then we drift back to him and Wonder. Fade to black (07: dusk).
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 44;
  const ez = U.ease;
  const P = Art.TOD.golden;

  /* ---------------- the golden flower spot (same world as 04/05) ---------------- */
  const GOPT = { y: 868, amp: 8, freq: 0.0021, seed: 14 };
  const FX = 1060, FY = 920, FS = 0.92, FSEED = 3;
  const MX = 748, MY = 877;                          // he sits here (s = 1, as in 04/05)
  const SUN = { x: 1720, y: 630 };                  // (sync with 05's final shot)
  const ROCK = { x: 1200, y: 934, w: 176, h: 96 };
  const FERN = { x: 956, y: 936, s: 1.08 };
  const ROCK_GREY = '#8a8f86', MOSS = U.mix(P.grass, P.trees[2], 0.25);
  const FERN_C1 = U.mix(P.grass, P.trees[2], 0.45), FERN_C2 = U.mix(P.grass, P.trees[2], 0.2);
  const TW = 40;                                     // 05's duration: wind, sway, blinks carry on from its clock
  const WONDER = Art.EMO.wonder, INK = '#ffe9b4', INK_GLOW = 'rgba(92,40,0,0.9)';

  /* ---------------- beats (local seconds) ---------------- */
  const TL = {
    kindle: 6.3, rise: 7.2, pop: 7.95, tap1: 8.45,
    say1: 9.1, say2: 10.7, sayOut: 14.6,
    seam1: 15.45, split0: 15.25, split1: 16.45,
    unchecked: 22.2, stall0: 30.9, stall1: 32.2, look0: 32.3,
    widen0: 33.2, widen1: 36.4, back0: 38.4, back1: 42.3,
  };
  const CAPS = [
    [1.2, 5.3, 'So maybe the flower caught my eye when I was hiking'],
    [5.7, 8.9, 'because something within my mind said to me:'],
    [15.6, 20.6, 'Because it might have, unironically, more meaning than hiking to a summit'],
    [21.0, 24.4, 'that may not have been justified as meaningful'],
    [24.8, 29.8, 'beyond potentially algorithmic societal norms of performative busyness or normalcy—'],
    [30.2, 35.2, 'instead of pausing and reflecting on the vibrant, colorful expression of life'],
    [35.6, 39.3, 'from a complex living structure called a flower.'],
  ];
  const GLINT = 2.3;                                 // "…caught my eye…": the flower twinkles at him
  const SAY1 = 'Let’s stop the current activity';
  const SAY2 = 'and ask ourselves—what does this flower mean to me?';
  const SAY2_SHOWN = SAY2.replace('—', '—\n');      // keep the question whole on its own line

  /* ---------------- offscreen helpers (local; scenes may not share code) ---------------- */
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
  /** depth-of-field: render at low resolution, upscale twice (smooth, cheap). rect = screen region (film units) */
  function soft(ctx, key, amount, drawFn, rect = null) {
    const f = clamp(amount * 0.55, 1.5, 14);
    const kk = ctx.canvas.width / W;
    const R = rect || { x: 0, y: 0, w: W, h: H };
    const ox = R.x * kk, oy = R.y * kk;
    const w = Math.ceil((R.w * kk) / f), h = Math.ceil((R.h * kk) / f);
    const c = pooled(key + ':a', w, h);
    const x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
    x.clearRect(0, 0, w + 1, h + 1);
    x.setTransform(new DOMMatrix().scale(1 / f, 1 / f).translate(-ox, -oy).multiply(ctx.getTransform()));
    drawFn(x);
    const c2 = pooled(key + ':b', w * 2, h * 2);
    const x2 = c2.getContext('2d');
    x2.setTransform(1, 0, 0, 1, 0, 0);
    x2.globalAlpha = 1; x2.globalCompositeOperation = 'copy';
    x2.imageSmoothingEnabled = true; x2.imageSmoothingQuality = 'low';
    x2.drawImage(c, 0, 0, w, h, 0, 0, w * 2, h * 2);
    x2.globalCompositeOperation = 'source-over';
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(c2, 0, 0, w * 2, h * 2, ox, oy, w * f, h * f);
    ctx.restore();
  }
  function bokeh(ctx, x, y, r, color, a) {
    if (a <= 0.003) return;
    const g = ctx.createRadialGradient(x, y, r * 0.5, x, y, r);
    g.addColorStop(0, U.rgba(color, a)); g.addColorStop(0.78, U.rgba(color, a * 0.85)); g.addColorStop(1, U.rgba(color, 0));
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.restore();
  }
  const camLerp = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), k)) });
  const toScreen = (c, x, y) => ({ x: W / 2 + (x - c.x) * c.z, y: H / 2 + (y - c.y) * c.z });
  const PIC0 = 138, PIC1 = 942;                       // the picture between the letterbox bars (big fills stop here)

  /* ======================================================================
     THE GOLDEN WORLD
     ====================================================================== */
  /* The backdrop mirrors 05's final shot exactly (so the 1.2 s dissolve has no double image):
     the summit seen through a gap in the near pines, the low sun to the right. */
  const SUMMIT_P = Object.assign({}, P, { snow: U.mix(P.snow, P.summit, 0.28), summit: U.mix(P.summit, P.far, 0.3) });
  const NEAR_TREES = [[296, 560], [418, 468], [596, 525], [790, 445], [902, 540], [1094, 498], [1216, 452], [1586, 520], [1742, 470], [1884, 548]];
  function backdrop(c, t, bright) {
    const g = c.createLinearGradient(0, 470, 0, 880);
    g.addColorStop(0, '#d39a5e'); g.addColorStop(0.5, '#f4c684'); g.addColorStop(1, '#ffe1ab');
    c.fillStyle = g; c.fillRect(-800, -200, 3600, 1700);
    Art.glow(c, SUN.x, SUN.y, 1050, '#ffc773', 0.72 + 0.12 * bright);
    Art.glow(c, SUN.x, SUN.y, 300, '#fff3d2', 0.95);
    Art.summit(c, { x: 1392, y: 762, h: 182, w: 380, P: SUMMIT_P, glow: 0.8, t, flag: true });
    Art.fog(c, { y: 724, h: 110, color: '#ffdaa0', alpha: 0.42 });
    Art.forest(c, { seed: 41, y: 808, spacing: 40, hMin: 110, hMax: 176, color: U.mix(P.trees[0], '#e7b67a', 0.45), kind: 'pine', w: 0.34 });
    Art.fog(c, { y: 800, h: 170, color: '#ffd89e', alpha: 0.55 });
    const col = U.mix(P.trees[1], '#4f4128', 0.18), light = U.mix(P.trees[1], '#ffc878', 0.42);
    for (const [x, h] of NEAR_TREES) Art.pine(c, x, 866 + (U.hash(x, 3) - 0.5) * 22, h, U.shade(col, (U.hash(x, 4) - 0.5) * 0.08), { sway: 2 * U.wind(t, x, 2), light, w: 0.44 * (0.88 + U.hash(x, 5) * 0.24) });
    Art.rays(c, { x: SUN.x, y: SUN.y, angle: 2.78, spread: 0.5, count: 7, len: 1700, color: '#ffe2a8', alpha: 0.15 + 0.1 * bright, t, seed: 4 });
  }
  function rockOutline(ctx, x, y, w, h, seed) {
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(seed, 1) * 8, y - h);
    ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    ctx.lineTo(x + w / 2, y);
    ctx.closePath();
  }
  function drawRock(ctx) {
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
    ctx.closePath(); ctx.fill();
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

  /* ---------------- his performance ---------------- */
  function meOpts(t) {
    // eyes: on the flower → up, inward (the thought kindles) → back toward Wonder (her tap) → the flower again
    const lookX = U.keys(t, [[0, 1], [TL.tap1 + 0.1, 1], [TL.tap1 + 0.35, -1, 'outCubic'], [11.25, -1], [11.7, 1, 'inOutCubic'], [TL.sayOut, 1], [TL.sayOut + 0.3, 0.6]]);
    const lookY = U.keys(t, [[0, 0.5], [TL.kindle, 0.5], [TL.kindle + 0.6, -0.25], [TL.tap1 + 0.1, -0.25], [TL.tap1 + 0.35, 0.1], [11.25, 0.1], [11.7, 0.55], [TL.sayOut, 0.55], [TL.sayOut + 0.3, -0.8, 'outCubic'], [TL.widen0, -0.8], [TL.widen0 + 0.5, 0.6]]);
    const browUp = U.keys(t, [[0, 0], [TL.kindle, 0], [TL.kindle + 0.5, 0.5], [TL.tap1, 0.5], [TL.tap1 + 0.15, 0.9, 'outCubic'], [TL.tap1 + 0.9, 0.45], [12.6, 0.3], [TL.sayOut, 0.3], [TL.sayOut + 0.2, 0.8], [TL.widen0, 0.8], [TL.widen0 + 0.6, 0.1]]);
    const smile = U.keys(t, [[0, 0.5], [TL.kindle, 0.5], [TL.kindle + 0.8, 0.35], [TL.pop, 0.35], [TL.pop + 0.6, 0.55], [11.7, 0.55], [12.6, 0.78], [TL.sayOut, 0.78], [TL.widen0, 0.6], [TL.widen1, 0.75]]);
    // a tiny startle when she taps, a nod as her question lands
    const tilt = 0.11 + 0.02 * Math.sin((t + TW) * 0.6) - 0.07 * U.bump(t, TL.tap1 + 0.12, 0.22) + 0.05 * U.bump(t, 12.9, 0.45) - 0.06 * ez(t, TL.sayOut, TL.sayOut + 0.3) * (1 - ez(t, TL.widen0, TL.widen0 + 0.8));
    const late = t > TL.widen1;
    const face = { smile, lookX, lookY, browUp, eyes: late && t > 39.6 ? 'happy' : 'open' };
    if ((t > 12.6 && t < TL.sayOut) || (t > GLINT + 0.12 && t < GLINT + 1.5)) face.eyes = 'sparkle';
    face.browUp += 0.45 * U.bump(t, GLINT + 0.35, 0.5);
    return {
      x: MX, y: MY, look: 'me', pose: 'sit', s: 1, t: t + TW, facing: 1,
      lean: 0.05 - 0.025 * U.bump(t, TL.kindle + 0.5, 0.8),
      head: { tilt }, face, glow: 0.22 * ez(t, 39.0, 41.5),
    };
  }
  /* the head/pack landmarks of the sitting rig (Art.person math, sit pose, s = 1) */
  const PACK_TOP = { x: MX - 30, y: MY - 99 };
  const HEAD_C = { x: MX + 12, y: MY - 158 };

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
  /** draw him with a warm rim light from the low sun behind the flower */
  function drawMe(ctx, t, z) {
    ctx.fillStyle = 'rgba(30,22,10,0.24)';
    ctx.beginPath(); ctx.ellipse(MX + 22, MY + 2, 74, 9, 0, 0, TAU); ctx.fill();
    const base = meOpts(t);
    const o = Object.assign({}, base, { shadow: false, glow: 0 });
    const m = ctx.getTransform();
    const bx = MX - 90, by = MY - 250, bw = 280, bh = 268;
    const d = 3.4 * Math.min(z, 1.9) * (ctx.canvas.width / W);
    // his layer, clipped to the visible frame (plus room for the rim) — he is often half out of shot
    const pad = Math.ceil(d * 2) + 4;
    const bx0 = Math.floor(m.a * bx + m.e), by0 = Math.floor(m.d * by + m.f);
    const x0 = Math.max(bx0, -pad), y0 = Math.max(by0, -pad);
    const x1 = Math.min(bx0 + Math.ceil(m.a * bw) + 2, ctx.canvas.width + pad), y1 = Math.min(by0 + Math.ceil(m.d * bh) + 2, ctx.canvas.height + pad);
    if (x1 - x0 < 2 || y1 - y0 < 2) return null;
    const w = x1 - x0, h = y1 - y0;
    const c = pooled('me6', Math.ceil(w / 128) * 128, Math.ceil(h / 128) * 128);
    const x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
    x.clearRect(0, 0, w + 10, h + 10);                  // (+10: the rim pass samples a few px past w)
    x.setTransform(m.a, m.b, m.c, m.d, m.e - x0, m.f - y0);
    const an = Art.person(x, o);
    seatPom(x, an, o);
    x.setTransform(1, 0, 0, 1, 0, 0);
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(c, 0, 0, w, h, x0, y0, w, h);
    ctx.restore();
    // rim: the silhouette shifted toward the light, minus itself
    // (every pass is limited to the used w×h window: the pooled canvases can be much larger)
    const rc = pooled('me6rim', c.width, c.height), rx = rc.getContext('2d');
    rx.setTransform(1, 0, 0, 1, 0, 0);
    rx.globalAlpha = 1; rx.globalCompositeOperation = 'source-over';
    rx.save();
    rx.beginPath(); rx.rect(0, 0, w, h); rx.clip();        // bounds the unbounded composite ops too
    rx.clearRect(0, 0, w, h);
    rx.drawImage(c, 0, 0, w, h, 0, 0, w, h);
    rx.globalCompositeOperation = 'source-in';
    rx.fillStyle = '#ffd79c'; rx.fillRect(0, 0, w, h);
    rx.globalCompositeOperation = 'destination-out';
    const sw = Math.min(c.width, w + Math.ceil(d) + 1);
    rx.drawImage(c, 0, 0, sw, h, -d, d * 0.35, sw, h);
    rx.restore();
    rx.globalCompositeOperation = 'source-over';
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha *= 0.8; ctx.globalCompositeOperation = 'lighter';
    ctx.drawImage(rc, 0, 0, w, h, x0, y0, w, h);
    ctx.restore();
    if (base.glow > 0.01) Art.glow(ctx, an.chest.x, an.chest.y, 190, '#ffd38a', base.glow * 0.5);
    return an;
  }

  /* ---------------- Wonder, at home on his pack ---------------- */
  const TAP_HOLD = TL.tap1 - Math.PI / 14;
  const TAP_PH = (Math.PI / 2 + TAU * 9) / 7 - TL.tap1;        // sin(7·te) peaks at tap1 (and tap1 + 2π/7)
  function wonderPose(t) {
    // returns null while she is away (diving / inside the split)
    if (t < TL.pop || (t >= TL.sayOut + 0.02 && t < TL.widen0)) return null;
    const home = t >= TL.widen0;
    let s = 0.5 * ez(t, TL.pop, TL.pop + 0.55, 'outBack');
    let arms = 'idle', te = t, squash = 0, facing = 1, rot = 0;
    const face = { smile: 0.5, eyes: 'open', lookX: 0.6, lookY: 0.2 };
    if (home) {
      arms = 'hug'; face.eyes = t > 40.4 ? 'closed' : 'happy'; face.smile = 0.75; face.blink = t > 40.4 ? 0 : undefined;
      squash = 0.06 * Math.sin(t * 1.9); rot = -0.06;
      s = 0.5;
    } else if (t < TL.tap1 - 0.3) {
      // just born: blinks, looks around, finds him
      face.lookX = U.keys(t, [[TL.pop, 0], [TL.pop + 0.2, -0.9], [TL.pop + 0.38, -0.9], [TL.pop + 0.5, 1]]);
      face.browUp = 0.6; face.smile = 0.4;
      squash = -0.35 * U.bump(t, TL.pop + 0.08, 0.12) + 0.25 * U.bump(t, TL.pop + 0.3, 0.16);
    } else if (t < TL.say1) {
      arms = 'tap'; te = Math.max(t, TAP_HOLD) + TAP_PH; face.lookX = 1; face.lookY = 0.2; face.browUp = 0.5;
    } else if (t < TL.say2) {
      // “Let’s stop the current activity” — palms out
      arms = 'shrug'; face.talk = t < TL.say1 + 1.25 ? 1 : 0; face.lookX = 0.8; face.lookY = -0.2; face.browUp = 0.4; face.smile = 0.55;
      squash = -0.18 * U.bump(t, TL.say1 + 0.05, 0.14);
    } else if (t < 12.7) {
      // “…what does this flower mean to me?” — pointing at it
      arms = t < 11.25 ? 'shrug' : 'point'; face.talk = t < TL.say2 + 1.9 ? 1 : 0;
      face.lookX = 1; face.lookY = t < 11.25 ? -0.2 : 0.7; face.browUp = 0.7; face.smile = 0.6;
      rot = 0.18 * ez(t, 11.25, 11.6, 'outBack');
    } else {
      face.eyes = 'sparkle'; face.smile = 0.75; face.lookX = 1; face.lookY = 0.7;
      rot = 0.18 * (1 - ez(t, 12.7, 13.2));
      // anticipation before she leaps
      squash = 0.45 * ez(t, TL.sayOut - 0.32, TL.sayOut - 0.05, 'inCubic');
      if (t > TL.sayOut - 0.32) { face.eyes = 'happy'; arms = 'cheer'; }
    }
    return { x: PACK_TOP.x, y: PACK_TOP.y + 2, s, arms, te, squash, facing, rot, face };
  }
  function drawWonderHome(ctx, t) {
    const w = wonderPose(t);
    if (!w || w.s <= 0.01) return null;
    ctx.save();
    ctx.translate(w.x, w.y);
    ctx.rotate(w.rot);
    const pop = U.bump(t, TL.pop + 0.12, 0.35);
    if (pop > 0) Art.glow(ctx, 0, -20, 90, '#fff0b0', 0.6 * pop);
    const r = Art.emotion(ctx, { x: 0, y: 0, s: w.s, color: WONDER, face: w.face, arms: w.arms, t: w.te, seed: 5, squash: w.squash, facing: w.facing, glow: 0.8 });
    ctx.restore();
    if (t < TL.pop + 0.9) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const k = ez(t, TL.pop, TL.pop + 0.8, 'outCubic');
      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * TAU + 0.4;
        Art.glow(ctx, w.x + Math.cos(a) * (8 + 40 * k), w.y - 22 + Math.sin(a) * (8 + 34 * k), 7, '#ffe9a0', (1 - k) * 0.9);
      }
      ctx.restore();
    }
    return { x: w.x, y: w.y, head: r.head };
  }
  /** the thought kindling inside his head, then rising out to become her */
  function drawKindle(ctx, t) {
    if (t < TL.kindle || t > TL.pop + 0.3) return;
    const k = ez(t, TL.kindle, TL.rise, 'inOutSine');
    const pulse = 0.85 + 0.15 * Math.sin((t - TL.kindle) * 9);
    if (t < TL.rise + 0.1) {
      Art.glow(ctx, HEAD_C.x - 4, HEAD_C.y - 6, 30 + 40 * k, '#ffd36b', 0.55 * k * pulse);
      Art.glow(ctx, HEAD_C.x - 4, HEAD_C.y - 6, 10 + 8 * k, '#fff4cf', 0.8 * k);
    }
    // the spark leaves his head and arcs down onto the pack
    const r = ez(t, TL.rise, TL.pop, 'inOutCubic');
    if (t >= TL.rise && t <= TL.pop + 0.3) {
      const x = lerp(HEAD_C.x - 4, PACK_TOP.x, r), y = lerp(HEAD_C.y - 6, PACK_TOP.y - 22, r) - Math.sin(r * Math.PI) * 70;
      const a = 1 - ez(t, TL.pop, TL.pop + 0.3);
      for (let i = 1; i <= 5; i++) {
        const rr = clamp(r - i * 0.05), tx = lerp(HEAD_C.x - 4, PACK_TOP.x, rr), ty = lerp(HEAD_C.y - 6, PACK_TOP.y - 22, rr) - Math.sin(rr * Math.PI) * 70;
        Art.glow(ctx, tx, ty, 9 - i, '#ffe09a', 0.5 * a * (1 - i / 6));
      }
      Art.glow(ctx, x, y, 34, '#ffcf6a', 0.7 * a);
      Art.glow(ctx, x, y, 10, '#fffbe8', 0.95 * a);
    }
  }

  /** the whole golden world under camera c */
  function goldenWorld(ctx, t, c, o = {}) {
    const ta = t + TW;
    const bright = o.bright || 0;
    ctx.save();
    Art.cam(ctx, { x: c.x, y: c.y, zoom: c.z });
    soft(ctx, 'bg6', o.bgBlur || 10, (x) => backdrop(x, ta, bright));
    for (let i = 0; i < 10; i++) {
      const bx = 380 + U.hash(i, 61) * 1150, by = 560 + U.hash(i, 62) * 220;
      bokeh(ctx, bx + Math.sin(ta * 0.3 + i) * 4, by, 14 + U.hash(i, 63) * 24, i % 3 ? '#ffd9a0' : '#fff2d4', 0.14 * (0.6 + 0.4 * Math.sin(ta * 0.7 + i * 1.7)));
    }
    Art.ground(ctx, Object.assign({ color: U.mix(P.ground, '#6b6a2a', 0.2), color2: P.ground2 }, GOPT));
    Art.trail(ctx, Object.assign({ color: P.trail, depth: 40 }, GOPT));
    Art.grass(ctx, { seed: 9, y: (x) => Art.groundY(x, GOPT) - 1, spacing: 9, h: 22, color: U.shade(P.grass, -0.15), color2: U.mix(P.grass, '#ffd486', 0.35), t: ta, wind: 0.7 });
    let an = null, wo = null;
    if (!o.noMe) {
      an = drawMe(ctx, t, c.z);
      drawKindle(ctx, t);
      wo = drawWonderHome(ctx, t);
    }
    drawRock(ctx);
    Art.fern(ctx, FERN.x, FERN.y, FERN.s, FERN_C1, U.wind(ta, FERN.x, 2) * 0.7);
    Art.fern(ctx, FERN.x + 44, FERN.y + 4, FERN.s * 0.64, FERN_C2, U.wind(ta, FERN.x + 44, 3) * 0.7);
    const fg = 0.42 + 0.06 * Math.sin(ta * 1.3) + (o.flowerGlow || 0);
    if (o.flowerGlow) Art.glow(ctx, FX, FY - 138, 300, '#ff9ec0', 0.2 * o.flowerGlow);
    if (o.macro > 0.01) Art.glow(ctx, FX, FY - 138, 130, '#ffc7da', 0.32 * o.macro);   // a halo behind the head
    const fl = Art.flower(ctx, { x: FX, y: FY, s: FS, t: ta, seed: FSEED, face: 0.8, sway: 1 + 0.3 * bright, glow: fg });
    const gk = U.bump(t, GLINT + 0.2, 0.42);
    if (gk > 0) {
      const gx = fl.head.x - 22, gy = fl.head.y - 26;
      Art.glow(ctx, gx, gy, 70, '#fff3d6', 0.6 * gk);
      ctx.save();
      ctx.translate(gx, gy); ctx.rotate(0.3 + t * 0.8); ctx.scale(gk, gk);
      ctx.fillStyle = 'rgba(255,252,240,0.95)';
      ctx.beginPath();
      for (let i = 0; i < 4; i++) {
        const a = (i / 4) * TAU;
        ctx.lineTo(Math.cos(a) * 30, Math.sin(a) * 30);
        ctx.quadraticCurveTo(0, 0, Math.cos(a + TAU / 8) * 3, Math.sin(a + TAU / 8) * 3);
      }
      ctx.closePath(); ctx.fill();
      ctx.restore();
    }
    Art.grass(ctx, { seed: 17, y: (x) => 946 + Math.sin(x * 0.01) * 6, spacing: 8, h: 34, color: U.shade(P.grass, -0.3), color2: U.mix(P.grass, '#ffd486', 0.15), t: ta, wind: 1 });
    Art.motes(ctx, { seed: 12, count: 30, x0: 560, x1: 1500, y0: 580, y1: 940, t: ta, color: '#ffe9b8', size: 1.4, drift: 9, glow: 0.8, alpha: 0.6 });
    soft(ctx, 'fg6', 13, (x) => {
      Art.grass(x, { seed: 23, y: 1018, x0: 380, x1: 760, spacing: 15, h: 110, hVar: 0.5, width: 5, color: '#2f3a1e', t: ta, wind: 0.5 });
      Art.grass(x, { seed: 24, y: 1024, x0: 1380, x1: 1640, spacing: 16, h: 100, hVar: 0.5, width: 5, color: '#2c351c', t: ta, wind: 0.5 });
    }, { x: 0, y: 740, w: W, h: 340 });
    if (o.pollen) Art.motes(ctx, { seed: 31, count: 26, x0: FX - 220, x1: FX + 240, y0: 600, y1: 900, t: ta, color: '#ffe7a6', size: 1.6, drift: 14, glow: 1, alpha: 0.75 * o.pollen, wander: 40 });
    ctx.restore();
    // warm light from the right of frame
    ctx.save();
    const wl = ctx.createLinearGradient(W * 0.5, 0, W, 0);
    wl.addColorStop(0, 'rgba(255,170,80,0)'); wl.addColorStop(1, 'rgba(255,170,80,0.12)');
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = wl; ctx.fillRect(W * 0.5, PIC0, W * 0.5, PIC1 - PIC0);      // (the letterbox hides the rest)
    ctx.restore();
    return { an, wo, fl };
  }
  /* ======================================================================
     THE MACHINE (left panel, drawn in screen space, x 0..960)
     Flat, cold, infographic: people reduced to identical pictograms.
     ====================================================================== */
  const MC = {
    bg0: '#16202b', bg1: '#25333f', lines: 'rgba(150,185,215,0.07)',
    ink: '#c9d4df', ink2: '#9aa9b9', dim: '#5d6d7e', steel: '#2d3b49', steel2: '#3c4d5f',
    cyan: '#73d0ff', white: '#eef6ff', warm: '#ffc982',
  };
  /** the machine's own clock: runs with t, then grinds to a halt (stall0 → stall1) */
  function mclock(t) {
    const a = TL.stall0, b = TL.stall1;
    if (t <= a) return t;
    if (t >= b) return a + 0.5 * (b - a);
    const u = (t - a) / (b - a);
    return a + 0.5 * (t - a) + 0.5 * ((b - a) / Math.PI) * Math.sin(Math.PI * u);
  }
  const B0 = { x: -40, y: 912 }, T0 = { x: 652, y: 440 };
  const SPAN = T0.x - B0.x, SLOPE = (B0.y - T0.y) / SPAN;
  const TR = 52, RISE = TR * SLOPE;                     // tread run / rise
  const VB = 46;                                         // belt speed (px/s, horizontal)
  const DECK = { y: 440, x0: T0.x, x1: 960 };
  const SELFIE_X = 742, DOOR_X = 904, PAUSE_U = 44;      // where they stop for the photo; the exit
  const BADGE = { x: 806, y: 228, s: 96 };
  const LIKES = { x: 612, y: 206 };
  const marchPh = (m) => m * Math.PI * 2;               // one full left-right march per second

  /** static backdrop: gradient, blueprint grid (cached once) */
  let MBG = null;
  function machineBackdrop() {
    if (MBG) return MBG;
    const c = document.createElement('canvas');
    c.width = 980; c.height = 820;
    const x = c.getContext('2d');
    const g = x.createLinearGradient(0, 0, 0, 820);
    g.addColorStop(0, MC.bg1); g.addColorStop(1, MC.bg0);
    x.fillStyle = g; x.fillRect(0, 0, 980, 820);
    x.strokeStyle = MC.lines; x.lineWidth = 1;
    x.beginPath();
    for (let gx = 0; gx <= 980; gx += 40) { x.moveTo(gx + 0.5, 0); x.lineTo(gx + 0.5, 820); }
    for (let gy = 1; gy <= 820; gy += 40) { x.moveTo(0, gy + 0.5); x.lineTo(980, gy + 0.5); }
    x.stroke();
    x.strokeStyle = 'rgba(150,185,215,0.06)'; x.lineWidth = 2;
    x.beginPath();
    for (let gx = 0; gx <= 980; gx += 200) { x.moveTo(gx, 0); x.lineTo(gx, 820); }
    for (let gy = 1; gy <= 820; gy += 200) { x.moveTo(0, gy); x.lineTo(980, gy); }
    x.stroke();
    // a soft cold pool of light behind the summit badge
    const r = x.createRadialGradient(BADGE.x, BADGE.y - 120, 0, BADGE.x, BADGE.y - 120, 360);
    r.addColorStop(0, 'rgba(170,215,255,0.16)'); r.addColorStop(1, 'rgba(170,215,255,0)');
    x.fillStyle = r; x.fillRect(0, 0, 980, 820);
    MBG = c;
    return c;
  }
  function gear(ctx, x, y, r, teeth, ang, col, col2) {
    ctx.save();
    ctx.translate(x, y); ctx.rotate(ang);
    ctx.fillStyle = col;
    ctx.beginPath();
    const n = teeth * 2;
    for (let i = 0; i <= n * 2; i++) {
      const a = (i / (n * 2)) * TAU;
      const rr = (Math.floor(i / 2) % 2) ? r : r * 0.86;
      i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
    }
    ctx.closePath();
    ctx.arc(0, 0, r * 0.32, 0, TAU, true);
    ctx.fill('evenodd');
    ctx.strokeStyle = col2; ctx.lineWidth = r * 0.07; ctx.lineCap = 'round';
    ctx.beginPath();
    for (let i = 0; i < 4; i++) { const a = (i / 4) * TAU; ctx.moveTo(Math.cos(a) * r * 0.34, Math.sin(a) * r * 0.34); ctx.lineTo(Math.cos(a) * r * 0.74, Math.sin(a) * r * 0.74); }
    ctx.stroke();
    ctx.beginPath(); ctx.arc(0, 0, r * 0.76, 0, TAU); ctx.stroke();
    ctx.restore();
  }

  /** the escalator: truss, treads (moving), handrail, landing deck */
  function escalator(ctx, m, back) {
    const off = (m * VB) % TR;
    const yAt = (s) => B0.y - SLOPE * s;
    if (back) {
      // far handrail, behind the riders
      ctx.strokeStyle = 'rgba(120,145,170,0.35)'; ctx.lineWidth = 7; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(B0.x, yAt(0) - 70); ctx.lineTo(T0.x + 10, yAt(SPAN) - 70); ctx.lineTo(T0.x + 46, DECK.y - 70); ctx.stroke();
      return;
    }
    // truss (side panel)
    ctx.fillStyle = MC.steel;
    ctx.beginPath();
    ctx.moveTo(B0.x, yAt(0) + 4); ctx.lineTo(T0.x, yAt(SPAN) + 4); ctx.lineTo(T0.x, DECK.y + 34);
    ctx.lineTo(T0.x - 40, yAt(SPAN - 40) + 92); ctx.lineTo(B0.x, yAt(0) + 92); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = MC.steel2; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(B0.x, yAt(0) + 6); ctx.lineTo(T0.x, yAt(SPAN) + 6); ctx.stroke();
    // chasing LED dots along the side panel
    ctx.fillStyle = MC.cyan;
    for (let s = -((m * VB * 1.6) % 34); s < SPAN - 30; s += 34) {
      const x = B0.x + s, y = yAt(s) + 48;
      ctx.globalAlpha = 0.25 + 0.2 * Math.sin(s * 0.09);
      ctx.fillRect(x - 3, y - 3, 6, 6);
    }
    ctx.globalAlpha = 1;
    // treads
    ctx.fillStyle = '#4d6074';
    ctx.strokeStyle = '#8ea3b8'; ctx.lineWidth = 2;
    ctx.beginPath();
    for (let s = off - TR * 2; s < SPAN - TR + 0.01; s += TR) {
      if (s + TR < 0) continue;
      const xa = B0.x + s, y = yAt(s);
      ctx.moveTo(xa, y); ctx.lineTo(xa + TR, y); ctx.lineTo(xa + TR, y - RISE);
    }
    ctx.stroke();
    // landing deck + summit pole
    ctx.fillStyle = MC.steel2;
    ctx.fillRect(DECK.x0 - 4, DECK.y, DECK.x1 - DECK.x0 + 10, 30);
    ctx.fillStyle = '#8ea3b8';
    ctx.fillRect(DECK.x0 - 4, DECK.y - 2, DECK.x1 - DECK.x0 + 10, 4);
    ctx.fillStyle = MC.steel;
    ctx.fillRect(DECK.x0 + 40, DECK.y + 30, 18, 520);
    ctx.fillRect(DECK.x0 + 230, DECK.y + 30, 18, 520);
  }

  /**
   * One identical hiker pictogram. (x,y) = feet. o = { march, walk:{ph}, phone 0..1,
   * look 0..1 (look up into the light), smile, warm 0..1, alpha, k }
   */
  function pictogram(ctx, x, y, o) {
    const k = o.k || 1, warm = o.warm || 0;
    const col = (c) => (warm > 0 ? U.mix(c, MC.warm, warm * 0.45) : c);
    const body = col(MC.ink), limb = col(MC.ink2), pack = col('#7d8da0'), cap = col('#9fb0c2');
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(k, k);
    if (o.alpha !== undefined) ctx.globalAlpha *= clamp(o.alpha);
    let lF = 0, lB = 0, fF = 0, fB = 0, liftF = 0, liftB = 0, bob = 0, swing = 0;
    if (o.walk) {                                        // a planted walk (triangle-wave feet)
      const ph = o.walk.ph, A = 13;
      const tri = (p) => { const f = U.fract(p); return f < 0.5 ? 1 - 4 * f : -3 + 4 * f; };
      fF = A * tri(ph); fB = -fF;
      const sw = (p) => { const f = U.fract(p); return f >= 0.5 ? Math.sin((f - 0.5) * 2 * Math.PI) : 0; };
      const lk = o.walk.lift === undefined ? 1 : o.walk.lift;
      liftF = 9 * lk * sw(ph); liftB = 9 * lk * sw(ph + 0.5);
      bob = -1.5 * Math.abs(Math.sin(ph * TAU));
      swing = -fF / A;
    } else {                                             // marching in place: knee lifts, in lockstep
      const ph = o.march || 0, amp = o.amp === undefined ? 1 : o.amp;
      lF = amp * Math.pow(Math.max(0, Math.sin(ph)), 1.4); lB = amp * Math.pow(Math.max(0, -Math.sin(ph)), 1.4);
      bob = -2.2 * amp * Math.abs(Math.sin(ph));
      swing = amp * Math.sin(ph);
    }
    const hip = { x: 0, y: -50 + bob };
    const leg = (lift, fx, ly, c) => {
      const th = lift * 1.15;
      const kx = hip.x + fx * 0.5 + Math.sin(th) * 25, ky = hip.y + Math.cos(th) * 25 - ly * 0.5;
      const ax = fx + lift * 4, ay = -ly - lift * 18;
      ctx.strokeStyle = c; ctx.lineWidth = 9; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.beginPath(); ctx.moveTo(hip.x, hip.y); ctx.lineTo(kx, ky); ctx.lineTo(ax, ay - 3); ctx.stroke();
      ctx.lineWidth = 7;
      ctx.beginPath(); ctx.moveTo(ax - 2, ay - 2); ctx.lineTo(ax + 7, ay - 2); ctx.stroke();
    };
    leg(lB, fB, liftB, U.shade(limb, -0.12));
    // back arm swings opposite the front knee
    const shB = { x: -3, y: -82 + bob };
    ctx.strokeStyle = U.shade(limb, -0.12); ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(shB.x, shB.y); ctx.lineTo(shB.x - swing * 12, shB.y + 28); ctx.stroke();
    // pack, torso
    ctx.fillStyle = pack;
    Art.roundRect(ctx, -25, -86 + bob, 15, 34, 5); ctx.fill();
    ctx.fillStyle = body;
    Art.roundRect(ctx, -12, -88 + bob, 25, 44, 9); ctx.fill();
    leg(lF, fF, liftF, limb);
    // head + cap
    const hx = 2, hy = -103 + bob;
    ctx.fillStyle = body;
    ctx.beginPath(); ctx.arc(hx, hy, 12.5, 0, TAU); ctx.fill();
    ctx.fillStyle = cap;
    ctx.beginPath(); ctx.arc(hx, hy - 2, 13, Math.PI + 0.15, TAU - 0.05); ctx.closePath(); ctx.fill();
    ctx.fillRect(hx + 4, hy - 5, 15, 3.5);
    // face: one dot eye (down at the phone … up into the light), a flat mouth that can smile
    const look = o.look || 0;
    ctx.fillStyle = '#26323f';
    if ((o.happy || 0) > 0.5) {
      ctx.strokeStyle = '#26323f'; ctx.lineWidth = 2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.arc(hx + 8, hy + 0.5, 2.8, Math.PI + 0.3, TAU - 0.3); ctx.stroke();
      Art.glow(ctx, hx + 6, hy + 4, 14, '#ffb48a', 0.35 * o.happy);
    } else {
      ctx.beginPath(); ctx.arc(hx + 7 + look * 1.5, hy + 2.5 - look * 4.5, 2.1, 0, TAU); ctx.fill();
    }
    const sm = o.smile || 0;
    ctx.strokeStyle = '#26323f'; ctx.lineWidth = 1.6; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(hx + 4, hy + 8); ctx.quadraticCurveTo(hx + 7.5, hy + 8 + sm * 3.5, hx + 11, hy + 7.5 - sm * 1.2); ctx.stroke();
    // front arm: the phone held up to the face (lowered when they look up)
    const ph = clamp(o.phone === undefined ? 1 : o.phone);
    const shF = { x: 5, y: -82 + bob };
    const hand = { x: lerp(12, 24, ph), y: lerp(-52 + bob, -98 + bob, ph) };
    const elb = { x: lerp(9, 20, ph), y: lerp(-66 + bob, -70 + bob, ph) };
    ctx.strokeStyle = limb; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(shF.x, shF.y); ctx.lineTo(elb.x, elb.y); ctx.lineTo(hand.x, hand.y); ctx.stroke();
    ctx.save();
    ctx.translate(hand.x + 2, hand.y);
    ctx.rotate(lerp(1.2, -0.25, ph));
    ctx.fillStyle = '#2a3746';
    Art.roundRect(ctx, -4.5, -9, 9, 16, 2.5); ctx.fill();
    ctx.fillStyle = U.mix('#bfeaff', '#ffffff', o.flash || 0);
    ctx.globalAlpha *= 0.55 + 0.45 * ph;
    Art.roundRect(ctx, -3, -7.5, 6, 12.5, 1.5); ctx.fill();
    ctx.restore();
    if (ph > 0.4) Art.glow(ctx, hand.x - 2, hand.y - 2, 26, '#9fdcff', 0.18 * ph);
    ctx.restore();
  }

  /* ---------------- dashboard widgets ---------------- */
  const commas = (n) => String(Math.max(0, Math.floor(n))).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  function label(ctx, text, x, y, size, color, align = 'left', spacing = 0, weight = 800) {
    ctx.font = Art.font(size, 'sans', weight);
    ctx.fillStyle = color;
    ctx.textBaseline = 'middle';
    if (!spacing) { ctx.textAlign = align; ctx.fillText(text, x, y); ctx.textAlign = 'left'; return; }
    ctx.textAlign = 'left';
    let w = 0;
    for (const ch of text) w += ctx.measureText(ch).width + spacing;
    let px = align === 'center' ? x - (w - spacing) / 2 : align === 'right' ? x - w + spacing : x;
    for (const ch of text) { ctx.fillText(ch, px, y); px += ctx.measureText(ch).width + spacing; }
  }
  function tick(ctx, x, y, s, k, color, lw = 4) {
    if (k <= 0) return;
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath();
    const a = { x: x - s * 0.42, y: y + s * 0.02 }, b = { x: x - s * 0.1, y: y + s * 0.32 }, c = { x: x + s * 0.48, y: y - s * 0.36 };
    const k1 = clamp(k / 0.35), k2 = clamp((k - 0.35) / 0.65);
    ctx.moveTo(a.x, a.y); ctx.lineTo(lerp(a.x, b.x, k1), lerp(a.y, b.y, k1));
    if (k2 > 0) ctx.lineTo(lerp(b.x, c.x, k2), lerp(b.y, c.y, k2));
    ctx.stroke();
    ctx.restore();
  }
  function heartGlyph(ctx, x, y, r, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x, y + r * 0.9);
    ctx.bezierCurveTo(x - r * 1.5, y - r * 0.2, x - r * 0.6, y - r * 1.25, x, y - r * 0.45);
    ctx.bezierCurveTo(x + r * 0.6, y - r * 1.25, x + r * 1.5, y - r * 0.2, x, y + r * 0.9);
    ctx.fill();
  }
  function clockWidget(ctx, m, stalled) {
    const x = 112, y = 238, r = 56;
    ctx.fillStyle = '#cdd8e3';
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.strokeStyle = '#8ea3b8'; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.arc(x, y, r - 2, 0, TAU); ctx.stroke();
    ctx.strokeStyle = '#4b5d70'; ctx.lineCap = 'round';
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * TAU, r0 = i % 3 ? r - 13 : r - 17;
      ctx.lineWidth = i % 3 ? 2 : 3.5;
      ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r0, y + Math.sin(a) * r0); ctx.lineTo(x + Math.cos(a) * (r - 8), y + Math.sin(a) * (r - 8)); ctx.stroke();
    }
    const mA = -Math.PI / 2 + m * 0.11 + 1.2, hA = -Math.PI / 2 + m * 0.009 + 4.1;
    ctx.strokeStyle = '#2c3a48'; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(hA) * 26, y + Math.sin(hA) * 26); ctx.stroke();
    ctx.lineWidth = 3.5;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(mA) * 40, y + Math.sin(mA) * 40); ctx.stroke();
    // the second hand ticks twice a second, with a little spring on each tick
    const q = m * 2, n = Math.floor(q), since = (q - n) / 2;
    const sA = -Math.PI / 2 + (n - 1 + U.spring(since, 3.4, 11)) * (TAU / 60);
    ctx.strokeStyle = stalled ? '#7b8c9e' : '#3aa6e0'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x - Math.cos(sA) * 10, y - Math.sin(sA) * 10); ctx.lineTo(x + Math.cos(sA) * 46, y + Math.sin(sA) * 46); ctx.stroke();
    ctx.fillStyle = '#2c3a48';
    ctx.beginPath(); ctx.arc(x, y, 4.5, 0, TAU); ctx.fill();
  }
  const GOAL_T = 25.5, RESET_T = 26.8;              // the counter hits 10,000 … and starts again
  function stepsAt(t, m) {
    if (t < GOAL_T) return 9796 + 4 * Math.floor(2 * m);
    if (t < RESET_T) return 10000;
    return 4 * Math.max(0, Math.floor(2 * (m - RESET_T)));
  }
  function counterWidget(ctx, t, m, stall) {
    const x = 204, y = 186, w = 250, h = 104;
    ctx.fillStyle = 'rgba(12,20,28,0.55)';
    Art.roundRect(ctx, x, y, w, h, 14); ctx.fill();
    ctx.strokeStyle = 'rgba(142,163,184,0.45)'; ctx.lineWidth = 2;
    Art.roundRect(ctx, x, y, w, h, 14); ctx.stroke();
    const steps = stepsAt(t, m);
    const goal = t >= GOAL_T && t < RESET_T;
    if (stall > 0.5) {
      const blink = Math.sin((t - TL.stall1) * 5) > -0.3 ? 1 : 0.35;
      ctx.save(); ctx.globalAlpha *= blink;
      ctx.fillStyle = MC.warm;
      ctx.fillRect(x + 18, y + 13, 5, 16); ctx.fillRect(x + 28, y + 13, 5, 16);
      label(ctx, 'PAUSED', x + 42, y + 22, 17, MC.warm, 'left', 2.4);
      ctx.restore();
    } else label(ctx, 'STEPS TODAY', x + 18, y + 22, 16, '#8ea3b8', 'left', 2.4);
    const pop = goal ? 1 + 0.12 * U.bump(t, GOAL_T + 0.1, 0.18) : 1;
    ctx.save();
    ctx.translate(x + 18, y + 60); ctx.scale(pop, pop);
    label(ctx, commas(steps), 0, 0, 46, goal ? '#bff0ff' : MC.white, 'left', 0, 900);
    ctx.restore();
    if (goal) tick(ctx, x + w - 34, y + 58, 30, ez(t, GOAL_T + 0.05, GOAL_T + 0.35), '#7fe3ff', 5);
    // progress toward 10,000
    const f = goal ? 1 : clamp(steps / 10000);
    ctx.fillStyle = 'rgba(142,163,184,0.25)';
    Art.roundRect(ctx, x + 18, y + 86, w - 36, 7, 3.5); ctx.fill();
    ctx.fillStyle = goal ? '#bff0ff' : MC.cyan;
    Art.roundRect(ctx, x + 18, y + 86, Math.max(7, (w - 36) * f), 7, 3.5); ctx.fill();
    // a tidy, joyless burst of confetti at 10,000
    if (t > GOAL_T && t < GOAL_T + 1.6) {
      const tau = t - GOAL_T;
      for (let i = 0; i < 14; i++) {
        const a = -Math.PI / 2 + (U.hash(i, 81) - 0.5) * 2.2, v = 190 + U.hash(i, 82) * 150;
        const px = x + w * (0.2 + 0.6 * U.hash(i, 83)) + Math.cos(a) * v * tau, py = y + 4 + Math.sin(a) * v * tau + 420 * tau * tau;
        if (py > y - 4 && tau > 0.25) continue;            // pieces falling back behind the box are gone
        ctx.save();
        ctx.globalAlpha *= 1 - tau / 1.6;
        ctx.translate(px, py); ctx.rotate(tau * (4 + i));
        ctx.fillStyle = i % 3 ? '#9fdcff' : '#e6eef6';
        ctx.fillRect(-6, -2.5, 12, 5);
        ctx.restore();
      }
    }
  }
  function checklist(ctx, t, m) {
    const x = 58, y0 = 356, dy = 44;
    const rows = ['summit', 'selfie', '10,000 steps', 'meaningful'];
    for (let i = 0; i < rows.length; i++) {
      const y = y0 + i * dy;
      const isM = i === 3;
      const hi = isM ? U.fade(t, TL.unchecked - 0.2, 24.6, 0.3, 0.8) : 0;
      if (hi > 0) {
        ctx.fillStyle = U.rgba('#73d0ff', 0.12 * hi);
        Art.roundRect(ctx, x - 10, y - 20, 224, 40, 10); ctx.fill();
      }
      ctx.strokeStyle = isM ? U.mix('#8ea3b8', '#cfefff', hi) : '#8ea3b8'; ctx.lineWidth = 2.5;
      Art.roundRect(ctx, x, y - 13, 26, 26, 6); ctx.stroke();
      label(ctx, rows[i], x + 40, y + 1, 24, isM ? U.mix('#a9b8c7', '#e8f6ff', hi) : '#a9b8c7', 'left', 0, 700);
      if (i < 2) tick(ctx, x + 13, y, 22, 1, '#7fe3ff', 4);
      if (i === 2) tick(ctx, x + 13, y, 22, ez(t, GOAL_T + 0.3, GOAL_T + 0.6), '#7fe3ff', 4);
      if (isM) {
        // the tick tries … and can't quite justify itself
        const tryK = U.keys(t, [[TL.unchecked + 0.4, 0], [TL.unchecked + 0.75, 0.42, 'outCubic'], [TL.unchecked + 0.95, 0.42], [TL.unchecked + 1.25, 0, 'inCubic']]);
        tick(ctx, x + 13, y, 22, tryK, '#7fe3ff', 4);
        const q = ez(t, TL.unchecked + 1.35, TL.unchecked + 1.7, 'outBack');
        if (q > 0) {
          ctx.save(); ctx.translate(x + 13, y + 1); ctx.scale(q, q);
          label(ctx, '?', 0, 0, 24, '#cfefff', 'center', 0, 900);
          ctx.restore();
        }
        // a blinking cursor while it thinks about it
        if (t > TL.unchecked && t < TL.unchecked + 1.4 && Math.sin((t - TL.unchecked) * 14) > 0) {
          ctx.fillStyle = '#cfefff'; ctx.fillRect(x + 186, y - 12, 3, 24);
        }
      }
    }
  }
  function badge(ctx, t, flash) {
    const { x } = BADGE, s = BADGE.s, y = BADGE.y + Math.sin(t * 1.6) * 3;
    Art.glow(ctx, x, y, s * 1.3, '#a9dcff', 0.22 + 0.5 * flash);
    ctx.fillStyle = 'rgba(8,14,20,0.35)';
    ctx.beginPath(); ctx.ellipse(x, y + s / 2 + 16, s * 0.36, 5, 0, 0, TAU); ctx.fill();
    const g = ctx.createLinearGradient(0, y - s / 2, 0, y + s / 2);
    g.addColorStop(0, '#e2ecf5'); g.addColorStop(1, '#9fb4c9');
    ctx.fillStyle = g;
    Art.roundRect(ctx, x - s / 2, y - s / 2, s, s, 24); ctx.fill();
    // the summit, as an icon: same peak, same little flag
    ctx.fillStyle = '#5c7188';
    ctx.beginPath(); ctx.moveTo(x - 38, y + 30); ctx.lineTo(x - 4, y - 26); ctx.lineTo(x + 38, y + 30); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#7d93a9';
    ctx.beginPath(); ctx.moveTo(x - 44, y + 30); ctx.lineTo(x - 24, y + 2); ctx.lineTo(x - 6, y + 30); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#f4f8fc';
    ctx.beginPath(); ctx.moveTo(x - 4, y - 26); ctx.lineTo(x + 9, y - 5); ctx.lineTo(x + 2, y - 9); ctx.lineTo(x - 5, y - 2); ctx.lineTo(x - 12, y - 9); ctx.lineTo(x - 15, y - 8); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#4b5d70'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x - 4, y - 26); ctx.lineTo(x - 4, y - 44); ctx.stroke();
    ctx.fillStyle = '#c96a60';
    ctx.beginPath(); ctx.moveTo(x - 4, y - 44); ctx.lineTo(x + 10, y - 40 + Math.sin(t * 3) * 1.5); ctx.lineTo(x - 4, y - 35); ctx.closePath(); ctx.fill();
  }
  function door(ctx) {
    const x0 = 878, x1 = 930, top = 302;
    ctx.fillStyle = '#0d141b';
    Art.roundRect(ctx, x0, top, x1 - x0, DECK.y - top, 6); ctx.fill();
    const g = ctx.createLinearGradient(x0, 0, x1, 0);
    g.addColorStop(0, 'rgba(160,210,255,0.0)'); g.addColorStop(1, 'rgba(160,210,255,0.22)');
    ctx.fillStyle = g; ctx.fillRect(x0, top, x1 - x0, DECK.y - top);
    ctx.fillStyle = 'rgba(12,20,28,0.75)';
    Art.roundRect(ctx, 864, 244, 80, 50, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(169,220,255,0.35)'; ctx.lineWidth = 1.5;
    Art.roundRect(ctx, 864, 244, 80, 50, 7); ctx.stroke();
    label(ctx, 'EXIT', 904, 259, 16, '#cfefff', 'center', 2);
    label(ctx, '→ START', 904, 280, 14, '#a9dcff', 'center', 0.8);
  }

  /* ---------------- the riders ---------------- */
  function riders(t, m) {
    const out = [];
    const base = m * VB;
    const i0 = Math.ceil((-TR - base) / (2 * TR)), i1 = Math.floor((SPAN + 340 - base) / (2 * TR));
    for (let i = i0; i <= i1; i++) {
      const s = i * 2 * TR + base;
      const r = { i, s };
      const sOff = SPAN - TR / 2;                         // feet reach the top of the stairs
      if (s < sOff) {
        r.x = B0.x + s + TR / 2; r.y = B0.y - SLOPE * s; r.deck = false;
        r.prog = clamp((s + TR) / (SPAN + TR * 0.5));
        r.amp = clamp((sOff - s) / 18);                   // the march settles as they reach the top
      } else {
        const u = s - sOff;                               // distance walked on the deck
        const u1 = SELFIE_X - T0.x;
        const g = u < u1 ? u : u < u1 + PAUSE_U ? u1 : u - PAUSE_U;
        r.x = T0.x + g; r.deck = true; r.u = u; r.prog = 1;
        const up = clamp(u / 14);
        r.y = lerp(B0.y - SLOPE * sOff, DECK.y, U.smooth(up)) - Math.sin(up * Math.PI) * 6;
        // planted stride (both feet down) exactly at the photo spot; foot-lift eases in off the stairs
        r.walk = { ph: (g - u1) / 52, lift: clamp(u / 16) };
        r.snap = u - u1;                                  // > 0 once they reach the photo spot
        r.alpha = 1 - ez(r.x, DOOR_X - 8, DOOR_X + 20);
      }
      if (r.alpha === undefined) r.alpha = clamp((r.x + 30) / 40);
      out.push(r);
    }
    return out;
  }

  /**
   * The whole panel. o = { div (divider x), dx (content offset), alpha, warm (light spill 0..1), jolt }
   */
  function drawMachine(ctx, t, o) {
    const m = mclock(t);
    const stalled = ez(t, TL.stall0 + 0.6, TL.stall1);
    ctx.save();
    ctx.translate(o.dx || 0, o.jolt || 0);
    ctx.drawImage(machineBackdrop(), -10, 130);
    // gears behind everything, turning with the machine
    gear(ctx, 742, 706, 122, 14, m * 0.55, '#223040', '#2b3a4a');
    gear(ctx, 548, 872, 76, 9, -m * 0.55 * (122 / 76) + 0.2, '#223040', '#2b3a4a');
    gear(ctx, 905, 880, 64, 8, -m * 0.55 * (122 / 64) + 0.1, '#1f2c3a', '#283746');
    escalator(ctx, m, true);
    escalator(ctx, m, false);
    door(ctx);
    // the riders
    const rs = riders(t, m);
    let flash = 0;
    for (const r of rs) if (r.deck && r.snap > 0) flash = Math.max(flash, U.bump(r.snap, 3, 4.5));
    badge(ctx, t, flash);
    for (const r of rs) {
      const dl = clamp((960 - r.x) / 960) * 0.9;
      const look = ez(t, TL.look0 + dl, TL.look0 + dl + 0.9, 'inOutSine');
      const warm = (o.warm || 0) * (0.35 + 0.65 * clamp(r.x / 900));
      const smile = look * (U.hash(r.i, 5) < 0.4 ? 0.9 : 0.35);
      const myFlash = r.deck && r.snap > 0 ? U.bump(r.snap, 3, 4.5) : 0;
      const happy = U.hash(r.i, 5) < 0.4 ? ez(t, TL.look0 + dl + 0.6, TL.look0 + dl + 1.0) : 0;
      const opts = { march: marchPh(m), amp: r.amp, phone: 1 - look, look, smile, warm, alpha: r.alpha, flash: myFlash, happy };
      if (r.deck) opts.walk = r.walk;
      pictogram(ctx, r.x, r.y, opts);
      // progress bar over each head; a tick once the photo is taken
      if (r.alpha > 0.02) {
        ctx.save();
        ctx.globalAlpha *= r.alpha * (1 - 0.6 * look);
        const bx = r.x - 20, by = r.y - 132;
        const done = r.deck && r.snap > 8;
        if (!done) {
          ctx.fillStyle = 'rgba(142,163,184,0.35)';
          Art.roundRect(ctx, bx, by, 40, 6, 3); ctx.fill();
          ctx.fillStyle = r.prog >= 1 ? '#bff0ff' : MC.cyan;
          Art.roundRect(ctx, bx, by, Math.max(6, 40 * r.prog), 6, 3); ctx.fill();
        } else {
          const q = ez(r.snap, 8, 20, 'outBack');
          ctx.translate(r.x, by + 2); ctx.scale(q, q);
          ctx.fillStyle = 'rgba(115,208,255,0.25)';
          ctx.beginPath(); ctx.arc(0, 0, 14, 0, TAU); ctx.fill();
          tick(ctx, 0, 0, 18, 1, '#bff0ff', 3.5);
        }
        ctx.restore();
      }
      // the selfie: flash, then a little +1 floats up toward the likes
      if (myFlash > 0.01) {
        Art.glow(ctx, r.x + 26, r.y - 98, 140, '#ffffff', 0.9 * myFlash);
        Art.glow(ctx, r.x + 26, r.y - 98, 40, '#ffffff', myFlash);
      }
      if (r.deck && r.snap > 4 && r.snap < 60) {
        const k = (r.snap - 4) / 56;
        ctx.save();
        ctx.globalAlpha *= U.smooth(Math.min(1, (1 - k) * 3)) * r.alpha;
        const px = lerp(r.x + 30, LIKES.x + 60, k), py = lerp(r.y - 140, LIKES.y + 16, U.E.outQuad(k));
        heartGlyph(ctx, px - 14, py, 7, '#9fdcff');
        label(ctx, '+1', px - 2, py, 18, '#cfefff', 'left', 0, 900);
        ctx.restore();
      }
    }
    // likes, refreshed with every photo
    let likes = 1186;
    const shots = Math.floor((m * VB - (SPAN - TR / 2 + (SELFIE_X - T0.x) + 40)) / (2 * TR));
    likes += Math.max(0, shots + 12) * 17 + Math.floor(U.hash(shots, 9) * 9);
    heartGlyph(ctx, LIKES.x, LIKES.y, 10, '#9fdcff');
    label(ctx, commas(likes), LIKES.x + 18, LIKES.y + 1, 24, '#e2f2ff', 'left', 0, 900);
    // the dashboard
    clockWidget(ctx, m, stalled > 0.5);
    counterWidget(ctx, t, m, stalled);
    checklist(ctx, t, m);
    // after the stall: warm light spills across the seam
    if (o.warm > 0.003) {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const gx = (o.div || 960) - (o.dx || 0);
      const g = ctx.createLinearGradient(gx, 0, gx - 760, 0);
      g.addColorStop(0, U.rgba('#ffb45e', 0.34 * o.warm)); g.addColorStop(0.45, U.rgba('#ff9c4a', 0.12 * o.warm)); g.addColorStop(1, 'rgba(255,150,70,0)');
      ctx.fillStyle = g; ctx.fillRect(gx - 760, 120, 760, 840);
      ctx.restore();
    }
    ctx.restore();
  }
  /* ======================================================================
     CAMERA, SEAM, WONDER'S DIVE
     ====================================================================== */
  const C1 = { x: 878, y: 738, z: 1.84 }, C2 = { x: 888, y: 732, z: 1.9 };
  const CF = { x: 900, y: 789, z: 3.0 }, CF2 = { x: 906, y: 785, z: 3.14 };
  const CW = { x: 1060, y: 780, z: 4.3 }, CW2 = { x: 1058, y: 778, z: 4.5 };
  const CE = { x: 934, y: 752, z: 1.62 };
  const CAM05_0 = { x: 912, y: 752, z: 1.62 }, CAM05_1 = { x: 922, y: 748, z: 1.7 };
  const cam05 = (t) => camLerp(CAM05_0, CAM05_1, ez(t + TW, 36.8, 42, 'inSine'));   // 05's camera, continued
  function camAt(t) {
    let c;
    if (t < 7.9) c = camLerp(cam05(t), C1, ez(t, 1.2, 7.9, 'inOutSine'));
    else if (t < TL.split0) c = camLerp(C1, C2, ez(t, 7.9, TL.split0, 'inOutSine'));
    else if (t < TL.split1) c = camLerp(C2, CF, ez(t, TL.split0, TL.split1, 'inOutCubic'));
    else if (t < TL.widen0) c = camLerp(CF, CF2, ez(t, TL.split1, TL.widen0, 'inOutSine'));
    else if (t < TL.widen1) c = camLerp(CF2, CW, ez(t, TL.widen0, TL.widen1, 'inOutCubic'));
    else if (t < TL.back0) c = camLerp(CW, CW2, ez(t, TL.widen1, TL.back0, 'inOutSine'));
    else c = camLerp(CW2, CE, ez(t, TL.back0, TL.back1, 'inOutSine'));
    const sh = Art.shake(t, 0.25 * ez(t, 1.2, 3.5), 6);
    return { x: c.x + sh.x / c.z, y: c.y + sh.y / c.z, z: c.z };
  }
  /** divider x (screen); 0 when the machine is gone */
  function divAt(t) {
    if (t < TL.split0) return 960;
    if (t < TL.widen0) return 960;
    return 960 * (1 - ez(t, TL.widen0, TL.widen1, 'inOutCubic'));
  }
  const seamX = (d, y, t) => d + 3.5 * Math.sin(y * 0.011 + t * 1.3) + 2 * Math.sin(y * 0.027 - t * 0.9);
  function seamPath(ctx, d, t, y0 = 120, y1 = 960) {
    ctx.beginPath();
    for (let y = y0; y <= y1; y += 20) { const x = seamX(d, y, t); y > y0 ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
  }
  function drawSeam(ctx, d, t, y0, y1, a) {
    if (a <= 0.003) return;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';
    seamPath(ctx, d, t, y0, y1);
    ctx.strokeStyle = 'rgba(255,190,110,0.10)'; ctx.lineWidth = 34; ctx.stroke();
    ctx.strokeStyle = 'rgba(255,200,120,0.22)'; ctx.lineWidth = 12; ctx.stroke();
    ctx.strokeStyle = 'rgba(255,236,190,0.85)'; ctx.lineWidth = 2.6; ctx.stroke();
    ctx.restore();
    // a few motes ride the seam
    for (let i = 0; i < 6; i++) {
      const y = 139 + U.fract(U.hash(i, 44) + t * (0.05 + 0.04 * U.hash(i, 45))) * 802;
      if (y > y1 || y < y0) continue;
      Art.glow(ctx, seamX(d, y, t) + Math.sin(t * 2 + i) * 6, y, 9, '#ffe0a0', 0.5);
    }
  }
  const DIVE0 = TL.sayOut + 0.02, APEX = TL.sayOut + 0.42, DIVE1 = TL.seam1, APEX_Y = 268;
  /* The left half turns into the machine like a run of mechanical shutter slats flipping over,
     cascading down in Wonder's wake as she draws the seam (no full-frame flash). */
  const SLATS = 14, SLAT_Y0 = 139, SLAT_H = 802 / SLATS, SLAT_DUR = 0.32;
  const slatT0 = (i) => APEX + 0.06 + (DIVE1 - APEX) * Math.sqrt(clamp((SLAT_Y0 + (i + 0.5) * SLAT_H - 200) / 760));
  const SLAT_START = slatT0(0), SLAT_END = slatT0(SLATS - 1) + SLAT_DUR;
  const slatK = (i, t) => ez(t, slatT0(i), slatT0(i) + SLAT_DUR, 'outCubic');
  /** warm pollen drifting up through the flower's light (screen space) */
  function pollenFront(ctx, t, a, x0) {
    if (a <= 0.01) return;
    for (let i = 0; i < 16; i++) {
      const sp = 0.035 + 0.03 * U.hash(i, 92);
      const y = 960 - U.fract(U.hash(i, 91) + t * sp) * 860;
      const x = x0 + U.hash(i, 90) * (1940 - x0) + Math.sin(t * (0.5 + U.hash(i, 93)) + i) * 24;
      const r = 2.5 + U.hash(i, 94) * 5;
      const k = Math.sin(Math.PI * U.fract(U.hash(i, 91) + t * sp));
      Art.glow(ctx, x, y, r * 5, '#ffd98e', 0.35 * a * k);
      ctx.save(); ctx.globalAlpha *= 0.8 * a * k; ctx.fillStyle = '#fff4d6';
      ctx.beginPath(); ctx.arc(x, y, r * 0.55, 0, TAU); ctx.fill(); ctx.restore();
    }
  }
  function divePos(t) {
    const c = camAt(DIVE0);
    const p0 = toScreen(c, PACK_TOP.x, PACK_TOP.y - 20);
    if (t < APEX) {
      const u = ez(t, DIVE0, APEX, 'linear');
      return { x: lerp(p0.x, 960, U.E.inOutSine(u)), y: lerp(p0.y, APEX_Y, U.E.outQuad(u)), sq: -0.7 + 0.9 * U.smooth(u) };
    }
    const u = ez(t, APEX, DIVE1, 'linear');
    return { x: 960, y: lerp(APEX_Y, 1010, U.E.inQuad(u)), sq: -1.1 * U.smooth(u * 3) };
  }
  function drawDive(ctx, t) {
    if (t < DIVE0 || t > DIVE1 + 0.05) return;
    for (let i = 6; i >= 1; i--) {
      const q = divePos(Math.max(DIVE0, t - i * 0.03));
      Art.glow(ctx, q.x, q.y - 30, 22 - i * 2, '#ffd36b', 0.42 * (1 - i / 7));
    }
    const p = divePos(t);
    const up = t < APEX;
    Art.emotion(ctx, {
      x: p.x, y: p.y, s: 0.95, color: WONDER, t, seed: 5, squash: p.sq, glow: 0.9,
      arms: 'cheer', facing: 1,
      face: { eyes: up ? 'happy' : 'open', smile: 0.85, browUp: 0.6, lookY: up ? -0.5 : 1 },
    });
  }

  /* ---------------- Wonder's handwriting ---------------- */
  const HAND = { x: 1012, y1: 226, y2: 330, size: 58, maxW: 860 };
  function handwriting(ctx, t, wo, c) {
    const a = 1 - ez(t, TL.sayOut, TL.sayOut + 0.45, 'inOutSine');
    if (t < TL.say1 || a <= 0) return;
    const r1 = ez(t, TL.say1, TL.say1 + 1.2, 'linear'), r2 = ez(t, TL.say2, TL.say2 + 1.9, 'linear');
    const drift = Math.sin(t * 0.8) * 2;
    ctx.save();
    ctx.globalAlpha *= a * ez(t, TL.say1 - 0.2, TL.say1 + 0.5);
    ctx.translate(HAND.x, 292); ctx.scale(1, 0.3);
    const sg = ctx.createRadialGradient(0, 0, 0, 0, 0, 600);
    sg.addColorStop(0, 'rgba(74,34,4,0.46)'); sg.addColorStop(0.6, 'rgba(74,34,4,0.24)'); sg.addColorStop(1, 'rgba(74,34,4,0)');
    ctx.fillStyle = sg; ctx.fillRect(-600, -600, 1200, 1200);
    ctx.restore();
    Art.hand(ctx, SAY1, { x: HAND.x, y: HAND.y1 + drift, size: HAND.size, reveal: r1, alpha: a, color: INK, glow: INK_GLOW });
    if (t >= TL.say2) Art.hand(ctx, SAY2_SHOWN, { x: HAND.x, y: HAND.y2 + drift, size: HAND.size, reveal: r2, alpha: a, color: INK, glow: INK_GLOW, maxW: HAND.maxW });
    // the pen of light: a spark from Wonder to where the words are being written
    const writing = (t < TL.say1 + 1.2) ? { r: r1, line: 0 } : (t > TL.say2 && t < TL.say2 + 1.9) ? { r: r2, line: 1 } : null;
    if (writing && wo) {
      ctx.save();
      ctx.font = Art.font(HAND.size, 'hand', 700);
      let px, py;
      if (writing.line === 0) {
        const w = ctx.measureText(SAY1).width;
        px = HAND.x - w / 2 + w * writing.r; py = HAND.y1;
      } else {
        const lines = Art.wrap(ctx, SAY2_SHOWN, HAND.maxW);
        const tot = lines.reduce((n, l) => n + l.length, 0);
        let k = writing.r * tot, li = 0;
        while (li < lines.length - 1 && k > lines[li].length) { k -= lines[li].length; li++; }
        const lw = ctx.measureText(lines[li]).width;
        px = HAND.x - lw / 2 + ctx.measureText(lines[li].slice(0, Math.floor(k))).width;
        py = HAND.y2 - ((lines.length - 1) * HAND.size * 1.1) / 2 + li * HAND.size * 1.1;
      }
      ctx.restore();
      const src = toScreen(c, wo.head.x + 8, wo.head.y - 6);
      for (let i = 0; i < 7; i++) {
        const f = U.fract(t * 1.6 + i / 7);
        const x = lerp(src.x, px, f) + Math.sin(f * 6 + i) * 10, y = lerp(src.y, py, f) - Math.sin(f * Math.PI) * 60;
        Art.glow(ctx, x, y, 8, '#ffe2a0', 0.55 * Math.sin(f * Math.PI));
      }
      Art.glow(ctx, px, py + 6, 26, '#fff0c8', 0.55);
    }
  }

  /* ======================================================================
     THE SCENE
     ====================================================================== */
  Film.scene({
    id: 'inner-voice',
    order: 6,
    title: 'The Inner Voice',
    duration: D,
    moods: [[0, 'wonder'], [15.3, 'machine'], [33.0, 'wonder']],
    sfx: [
      [6.3, 'shimmer', { gain: 0.4 }],
      [7.95, 'sparkle', { gain: 0.55 }],
      [8.45, 'tap', { gain: 0.75 }],
      [9.1, 'chime', { gain: 0.3 }],
      [14.62, 'whoosh', { gain: 0.5 }],
      [15.1, 'paper', { gain: 0.4 }],      // the slats riffle over like a split-flap board
      [15.35, 'whoosh', { gain: 0.35 }],
      // a shutter click for every summit selfie (they fall where riders reach the photo spot)
      [16.5, 'tap', { gain: 0.22 }], [18.76, 'tap', { gain: 0.22 }], [21.02, 'tap', { gain: 0.22 }],
      [23.28, 'tap', { gain: 0.22 }], [27.8, 'tap', { gain: 0.22 }], [30.07, 'tap', { gain: 0.2 }],
      [23.15, 'boing', { gain: 0.3 }],
      [25.5, 'ding', { gain: 0.45 }],
      [30.95, 'clock', { gain: 0.4 }],
      [32.15, 'thud', { gain: 0.6 }],
      [33.2, 'swell', { gain: 0.5 }],
      [35.6, 'bloom', { gain: 0.5 }],
      [38.8, 'chime', { gain: 0.35 }],
      [40.8, 'bird', { gain: 0.35 }],
    ],
    // The first frame IS 05's last frame (same world, camera and ambient clock), so this is a
    // seamless cut, like 04 → 05. (A crossIn also works, but costs ~30 ms/frame in the engine's buffer.)
    crossIn: 0,
    fadeIn: 0,
    fadeOut: 1.0,
    post: (t) => ({ vignette: 0.42 - 0.1 * U.fade(t, TL.split0, TL.widen1, 1, 1), grain: 0.045, letterbox: 1 }),

    render(ctx, t) {
      const c = camAt(t);
      const div = divAt(t);
      const covered = t > TL.split1 && t < TL.back0;               // hidden behind the machine, then out of the macro's frame
      // the flower comes alive as the argument is made
      const flowerGlow = 0.3 * U.fade(t, 17.0, 30.5, 1.2, 2.0) + 0.55 * ez(t, 31.6, 35.2) * (1 - 0.5 * ez(t, 38.5, 42));
      const pollen = ez(t, TL.split0, TL.split1) * (0.6 + 0.4 * ez(t, 31.6, 35));
      const bright = ez(t, 31.6, 35.5) * (1 - 0.4 * ez(t, 39, 43));
      const macro = ez(t, TL.widen0 + 1.2, TL.widen1, 'inOutSine') * (1 - ez(t, TL.back0, TL.back0 + 2.4, 'inOutSine'));
      const g = goldenWorld(ctx, t, c, { noMe: covered, flowerGlow, pollen, bright, macro, bgBlur: lerp(10, 13, ez(t, TL.split0, TL.split1) * (1 - ez(t, TL.back0, TL.back1))) });
      if (t < TL.split0 + 0.1) handwriting(ctx, t, g.wo, c);
      pollenFront(ctx, t, ez(t, TL.split0, TL.split1) * (1 - 0.5 * ez(t, TL.back0, TL.back1)) + 0.5 * ez(t, 31.6, 35) * (1 - ez(t, TL.back0, TL.back1)), lerp(980, 0, ez(t, TL.widen0, TL.widen1)));
      if (macro > 0.01 && g.fl) {
        const fh = toScreen(c, g.fl.head.x, g.fl.head.y);
        const vg = ctx.createRadialGradient(fh.x, fh.y + 40, 240, fh.x, fh.y + 40, 1150);
        vg.addColorStop(0, 'rgba(46,22,8,0)'); vg.addColorStop(1, U.rgba('#2e1608', 0.45 * macro));
        ctx.fillStyle = vg; ctx.fillRect(0, PIC0, W, PIC1 - PIC0);
        // pollen lifting off the flower's golden heart
        for (let i = 0; i < 12; i++) {
          const ph = U.fract(U.hash(i, 71) + t * (0.09 + 0.05 * U.hash(i, 72)));
          const a = U.hash(i, 73) * TAU;
          const px = fh.x + Math.cos(a) * (40 + 260 * ph) + Math.sin(t * 1.3 + i) * 12;
          const py = fh.y + Math.sin(a) * (30 + 120 * ph) - ph * 220;
          const k = Math.sin(Math.PI * ph) * macro;
          Art.glow(ctx, px, py, 16, '#ffe2a0', 0.55 * k);
          ctx.save(); ctx.globalAlpha *= 0.9 * k; ctx.fillStyle = '#fff6dc';
          ctx.beginPath(); ctx.arc(px, py, 2.6, 0, TAU); ctx.fill(); ctx.restore();
        }
      }
      // ---- the machine, on the left of the seam ----
      if (t >= SLAT_START && div > 0.5) {
        const widen = ez(t, TL.widen0, TL.widen1, 'inOutCubic');
        const dx = (div - 960) * 0.55;
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(-10, 100);
        for (let y = 100; y <= 980; y += 20) ctx.lineTo(seamX(div, y, t), y);
        ctx.lineTo(-10, 980);
        ctx.closePath();
        ctx.clip();
        const opening = t < SLAT_END;
        ctx.save();
        if (opening) {
          // only the slats that have flipped over show the machine (each opens from its centre line)
          ctx.beginPath();
          for (let i = 0; i < SLATS; i++) {
            const k = slatK(i, t);
            if (k <= 0) continue;
            const hh = SLAT_H * k + 1;                     // +1: no hairline gaps between open slats
            ctx.rect(-10, SLAT_Y0 + (i + 0.5) * SLAT_H - hh / 2, 1000, hh);
          }
          ctx.clip();
        }
        const jolt = 5 * U.bump(t, TL.stall1 - 0.04, 0.12) * Math.sin(t * 90);
        const warm = ez(t, TL.stall1 - 0.1, TL.look0 + 1.3, 'inOutSine');
        drawMachine(ctx, t, { div, dx, jolt, warm });
        if (widen > 0) { ctx.fillStyle = U.rgba('#0a0e14', 0.5 * widen); ctx.fillRect(0, 0, W, H); }
        ctx.restore();
        if (opening) {
          // the slats' steel edges catch a cold light as they turn, then settle flush
          for (let i = 0; i < SLATS; i++) {
            const k = slatK(i, t);
            if (k <= 0 || k >= 1) continue;
            const yc = SLAT_Y0 + (i + 0.5) * SLAT_H, hh = SLAT_H * k;
            const a = Math.pow(1 - k, 0.8);
            ctx.fillStyle = U.rgba('#0e1620', 0.55 * a);
            ctx.fillRect(-10, yc - hh / 2 - 5, 1000, 5); ctx.fillRect(-10, yc + hh / 2, 1000, 5);
            ctx.fillStyle = U.rgba('#bfe9ff', 0.9 * a);
            ctx.fillRect(-10, yc - hh / 2 - 1.5, 1000, 2.2); ctx.fillRect(-10, yc + hh / 2 - 0.7, 1000, 2.2);
          }
        }
        ctx.restore();
      }
      // ---- the seam of light (Wonder draws it) ----
      if (t >= APEX && div > 0.5) {
        const y1 = t < DIVE1 ? divePos(t).y - 20 : 960;
        const y0 = lerp(APEX_Y - 30, 130, ez(t, APEX, APEX + 0.25, 'outCubic'));
        drawSeam(ctx, div, t, y0, y1, 1 - ez(t, TL.widen1 - 0.6, TL.widen1, 'inOutSine'));
      }
      drawDive(ctx, t);
      Art.captions(ctx, t, CAPS);
    },
  });
})();
