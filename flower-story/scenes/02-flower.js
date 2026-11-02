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
  const CREW = [                            // x, walk phase and seed (breathing/blinks) exactly as 01 ends
    { k: 'h1', x: 1250, ph: 0.4, seed: 17 },
    { k: 'h2', x: 1080, ph: 2.3, seed: 53 },
    { k: 'h3', x: 910, ph: 4.1, seed: 89 },
    { k: 'h4', x: 740, ph: 5.6, seed: 131 },
  ];
  const D01 = 32.5;                         // 01's duration: its light shafts and pollen run on in 02 on clock D01 + wa
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
  function mossyRock(ctx, x, y, w, h, moss, seed, dsatAmt) {
    Art.rock(ctx, x, y, w, h, dsatAmt ? U.desat(ROCK_GREY, dsatAmt) : ROCK_GREY, seed);
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
    const bx0 = Math.max(0, Math.min(x0, x1) - m), by0 = Math.max(PIC.top, Math.min(y0, y1) - m);
    const bx1 = Math.min(W, Math.max(x0, x1) + m), by1 = Math.min(PIC.bottom, Math.max(y0, y1) + m);
    if (bx1 <= bx0 || by1 <= by0) return;
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

  /* ---------------- carried over from 01 (keep identical: 01's last frame is this scene's first) ---------------- */
  // h1's trekking poles: each tip is planted for one step, then swings forward (body-local units)
  const R0 = 58 * Math.sin(0.42) + 56 * Math.sin(0.3);
  const stanceDisp = (u) => { const a = 0.42 * Math.cos(u); return R0 - (58 * Math.sin(a) + 56 * Math.sin(a - 0.12)); };
  const SWEEP = stanceDisp(Math.PI);
  const POLE = { TX0: 40, HX0: 25, HY: -118, CARRY: 0.6, LIFT: 8 };
  const POLE_L = Math.hypot(POLE.TX0 - POLE.HX0, POLE.HY);
  function poleState(ph) {
    let u = (ph + Math.PI / 2) % TAU; if (u < 0) u += TAU;
    if (u <= Math.PI) {
      const d = stanceDisp(u);
      return { hand: { x: POLE.HX0 - POLE.CARRY * d, y: POLE.HY }, tip: { x: POLE.TX0 - d, y: 0 } };
    }
    const q = (u - Math.PI) / Math.PI, k = U.smooth(q);
    const hand = { x: POLE.HX0 - POLE.CARRY * SWEEP * (1 - k), y: POLE.HY - POLE.LIFT * Math.sin(q * Math.PI) };
    const th0 = Math.atan2(POLE.TX0 - SWEEP - (POLE.HX0 - POLE.CARRY * SWEEP), -POLE.HY);
    const th1 = Math.atan2(POLE.TX0 - POLE.HX0, -POLE.HY);
    const th = U.lerp(th0, th1, k);
    return { hand, tip: { x: hand.x + Math.sin(th) * POLE_L, y: hand.y + Math.cos(th) * POLE_L } };
  }
  function poleDrawer(bodyInv, ps, handCol, handR) {
    return (c) => {
      const r = bodyInv.multiply(c.getTransform());
      const tx = ps.tip.x - r.e, ty = ps.tip.y - r.f;
      const L = Math.hypot(tx, ty) || 1, ux = tx / L, uy = ty / L;
      c.lineCap = 'round';
      c.strokeStyle = '#6f7680'; c.lineWidth = 4.4;
      c.beginPath(); c.moveTo(-ux * 15, -uy * 15); c.lineTo(tx, ty); c.stroke();
      c.strokeStyle = '#d3d7dd'; c.lineWidth = 2.4;
      c.beginPath(); c.moveTo(-ux * 15, -uy * 15); c.lineTo(tx - ux * 1.5, ty - uy * 1.5); c.stroke();
      c.strokeStyle = '#272b35'; c.lineWidth = 5.4;
      c.beginPath(); c.moveTo(-ux * 16, -uy * 16); c.lineTo(ux * 5, uy * 5); c.stroke();
      c.strokeStyle = '#3a3f4b'; c.lineWidth = 2.2;
      const bx = tx - ux * 13, by = ty - uy * 13;
      c.beginPath(); c.moveTo(bx - uy * 6, by + ux * 6); c.lineTo(bx + uy * 6, by - ux * 6); c.stroke();
      c.fillStyle = handCol;
      c.beginPath(); c.arc(0, 0, handR, 0, TAU); c.fill();
    };
  }
  // 01's cheap soft pass: 1/f-res canvas over a screen region, 4-tap box, bilinear upscale, optional blend mode
  function softF(ctx, f, drawFn, key, r, mode) {
    const cw = Math.ceil(r.w / f) + 2, ch = Math.ceil(r.h / f) + 2;
    const c = Art.canvas('a2:' + key, cw, ch), x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
    x.clearRect(0, 0, cw, ch);
    const base = Art._base || new DOMMatrix();
    x.setTransform(new DOMMatrix().scale(1 / f, 1 / f).translate(f - r.x, f - r.y).multiply(base.inverse().multiply(ctx.getTransform())));
    drawFn(x);
    const c2 = Art.canvas('a2:' + key + ':b', cw, ch), x2 = c2.getContext('2d');
    x2.setTransform(1, 0, 0, 1, 0, 0);
    x2.globalAlpha = 1; x2.globalCompositeOperation = 'source-over';
    x2.clearRect(0, 0, cw, ch);
    x2.globalCompositeOperation = 'lighter'; x2.globalAlpha = 0.25;
    x2.drawImage(c, -0.6, -0.6); x2.drawImage(c, 0.6, -0.6); x2.drawImage(c, -0.6, 0.6); x2.drawImage(c, 0.6, 0.6);
    x2.globalCompositeOperation = 'source-over'; x2.globalAlpha = 1;
    ctx.save();
    ctx.setTransform(base);
    if (mode) ctx.globalCompositeOperation = mode;
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(c2, r.x - f, r.y - f, cw * f, ch * f);
    ctx.restore();
  }
  // soft god-ray shafts through the canopy (01's), on 01's clock
  function drawShafts(c, cam, t, P, a) {
    layer(c, cam, 0.62, (c2, off) => {
      const sp = 330, i0 = Math.floor((off - 900) / sp), i1 = Math.ceil((off + W + 500) / sp);
      for (let i = i0; i <= i1; i++) {
        if (U.hash(i, 151) < 0.4) continue;
        const xt = i * sp + U.hash(i, 152) * 200 - off + 260;
        const yt = 60, yb = 990, xb = xt - (yb - yt) * 0.46;
        const w0 = 16 + U.hash(i, 153) * 34, w1 = w0 * 2.3;
        const fl = a * (0.55 + 0.45 * Math.sin(t * (0.35 + U.hash(i, 154) * 0.5) + i * 1.9)) * (0.55 + 0.45 * U.hash(i, 155));
        const gr = c2.createLinearGradient(0, yt, 0, yb);
        gr.addColorStop(0, U.rgba(P.light, 0));
        gr.addColorStop(0.35, U.rgba(P.light, fl));
        gr.addColorStop(0.8, U.rgba(P.light, fl * 0.75));
        gr.addColorStop(1, U.rgba(P.light, 0));
        c2.fillStyle = gr;
        c2.beginPath(); c2.moveTo(xt - w0, yt); c2.lineTo(xt + w0, yt); c2.lineTo(xb + w1, yb); c2.lineTo(xb - w1, yb); c2.closePath(); c2.fill();
      }
    });
  }
  // The sky and the sun's big glow (01's layer 0), cached: a full-frame gradient plus a 940-px radial glow cost
  // ~4 ms a frame in software; blitted 1:1 they cost ~0.5. Re-rendered only when the palette (quantized to steps
  // far below one colour level) changes. Covers film y SKY_Y0 .. SKY_Y0 + SKY_H.
  const SKY_Y0 = 60, SKY_H = 940;
  function skyPlate(P, k) {
    const c = Art.canvas('a2:sky', Math.ceil(W * k), Math.ceil(SKY_H * k));
    const key = P.sky.join() + P.sun + k;
    if (c.__key !== key) {
      const x = c.getContext('2d');
      x.setTransform(k, 0, 0, k, 0, -SKY_Y0 * k);
      x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
      Art.sky(x, P, { horizon: 720 });
      Art.glow(x, 1760, 90, 470, P.sun, 0.45, 'screen');
      c.__key = key;
    }
    return c;
  }
  // the summit's flag, drawn here (not by the kit) so it greys with the world when colour is pre-desaturated
  function summitFlag(c, tip, P, t, dsatAmt) {
    c.strokeStyle = U.shade(P.summit, -0.45); c.lineWidth = 2;
    c.beginPath(); c.moveTo(tip.x, tip.y + 2); c.lineTo(tip.x, tip.y - 26); c.stroke();
    const fl = Math.sin(t * 3) * 3;
    c.fillStyle = U.desat('#e8574a', dsatAmt);
    c.beginPath(); c.moveTo(tip.x, tip.y - 26); c.lineTo(tip.x + 16, tip.y - 21 + fl); c.lineTo(tip.x, tip.y - 16); c.closePath(); c.fill();
  }
  function skyClouds(c, off) {           // Art.clouds(seed 2, count 4) minus the cloud that sat inside the big one
    const span = W + 900, seed = 2;
    for (let i = 1; i < 4; i++) {
      const x = ((((U.hash(i, seed) * span - off) % span) + span) % span) - 450;
      Art.cloud(c, x, U.lerp(190, 330, U.hash(i, seed + 1)), 0.6 + U.hash(i, seed + 2) * 0.8, '#ffffff', 0.55 * (0.6 + 0.4 * U.hash(i, seed + 3)), i + seed * 13);
    }
  }
  function pollen(ctx, tm, camX, toScr, zOf, P, k) {
    if (k <= 0.003) return;
    const span = W + 300;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = '#fff6d8';
    for (let i = 0; i < 42; i++) {
      const p = 0.8 + U.hash(i, 91) * 0.5;
      const lx = ((((U.hash(i, 92) * span - camX * p * 0.96 + U.noise1(tm * 0.21 + i, 93) * 40) % span) + span) % span) - 150;
      const rise = (tm * (6 + U.hash(i, 95) * 8)) / 120, cyc = rise - Math.floor(rise);
      const ly = 260 + U.hash(i, 94) * 640 - cyc * 120 + U.noise1(tm * 0.3 + i * 1.7, 96) * 30;
      const life = U.smooth(Math.min(cyc, 1 - cyc) * 6);
      const a = 0.35 * k * life * (0.5 + 0.5 * Math.sin(tm * (1 + U.hash(i, 97) * 2) + i * 3.1));
      if (a < 0.004) continue;
      const q = toScr(p, lx, ly), r = (1.1 + U.hash(i, 98) * 1.6) * zOf(p);
      ctx.globalAlpha = 1;
      Art.glow(ctx, q.x, q.y, r * 5, P.light, a * 0.1);
      ctx.globalAlpha = a;
      ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, TAU); ctx.fill();
    }
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
      // the letterbox bars (y < 138.33, y > 941.67) hide the rest of the frame: don't rasterize it
      ctx.beginPath(); ctx.rect(0, 138, W, 804); ctx.clip();
      const cam = cameraAt(t);
      // During the 0.8 s dissolve in from 01 the engine paints 01's frame underneath this one (Art._alpha < 1),
      // and 01's last frames are built to equal ours everywhere except where the flower spot enters at the
      // right edge. So only that patch is rasterized; elsewhere this layer stays transparent and 01's identical
      // pixels show through. Same picture, half the cost of the dissolve's double render.
      if (t < 0.8 && Art._alpha < 0.999) {
        // (edges on whole device pixels: a partly covered edge pixel would composite differently and show a seam)
        const k = (Art._base || new DOMMatrix()).a;
        const x0 = Math.floor(toScreen(cam, FX - cam.camX - 170, 0).x * k) / k, y0 = Math.floor(740 * k) / k;
        ctx.beginPath(); ctx.rect(x0, y0, W - x0, 942 - y0); ctx.clip();
      }
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

      // Colour drains out as time stops. Early on (characters and light in frame) that's one full-frame
      // 'saturation' pass; in the close-up, where everything but the flower is drawn into soft passes, the
      // same desaturation is applied to the colours themselves (desaturation is linear, so the two agree)
      // and the ~5 ms full-frame pass is skipped.
      // (only once nobody is in frame: the kit's faces have a few fixed colours a look can't desaturate)
      const crewLeft = Math.min(...CREW.map((m) => m.x)) + V0 * wo - cam.camX;
      // (me's last pixel leaves the frame at t ≈ 19.4, when his x + 30 maps left of −20; he isn't drawn after that)
      const preD = t > T_PUSH0 + 2.6 && toScreen(cam, crewLeft - 70, 0).x > W + 40 && toScreen(cam, ME_X + 30, 0).x < -20;
      const dP = preD ? dsat : 0;
      const Pd = preD ? Art.desatPalette(P, dsat) : P;

      /* ---------- far world (goes soft as time stops) ---------- */
      const PbgD = preD ? Art.desatPalette(Pbg, dsat) : Pbg;
      soft(ctx, bgBlur, (c) => {
        const P = PbgD;
        layer(c, cam, 0, (c2) => {
          if (c2.canvas === ctx.canvas && t < 5.9) {         // sharp and not yet greying: blit the cached plate
            const q = Math.round((0.2 + 0.1 * U.clamp(t / D)) * 100) / 100;
            const k = (Art._base || new DOMMatrix()).a;
            c2.save(); c2.setTransform(1, 0, 0, 1, 0, 0);
            c2.drawImage(skyPlate(U.mixDeep(Art.TOD.morning, Art.TOD.golden, q), k), 0, Math.round(SKY_Y0 * k));
            c2.restore();
          } else {
            Art.sky(c2, P, { horizon: 720 });
            Art.glow(c2, 1760, 90, 470, P.sun, 0.45, 'screen');
          }
        });
        layer(c, cam, 0.02, (c2, off) => skyClouds(c2, off + wa * 5));
        layer(c, cam, 0.04, (c2, off) => Art.ridge(c2, { seed: 21, y: 615, amp: 150, color: U.mix(P.far, P.sky[1], 0.4), offset: off }));
        layer(c, cam, 0.03, (c2, off) => {
          const tp = Art.summit(c2, { x: 1610 - off, y: 655, h: 440, w: 700, P, glow: 0, t: wa, flag: false });
          summitFlag(c2, tp, P, wa, dP);
          Art.glow(c2, tp.x, tp.y + 6, 130, P.light, 0.9 * (0.55 + 0.15 * Math.sin(wa * 1.4)), 'screen');
        });
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
      }, 'bg', { x: 0, y: PIC.top, w: W, h: Math.min(PIC.bottom, groundLow + 10) - PIC.top });

      /* ---------- trail plane ---------- */
      const drawGround = (c) => layer(c, cam, 1, (c2, off) => {
        const go = gOpt(off), P = Pd;
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
        const bodyBase = c2.getTransform();
        for (let i = crew.length - 1; i >= 0; i--) {
          const { m, x, walk } = crew[i];
          if (x < -200 || x > W / Math.max(1, cam.Zt) + 600) continue;
          const o = { x, y: Art.groundY(x, go) + FOOT, s: S, look: m.k, t: wo, walk, seed: m.seed };
          if (m.k === 'h1') {                     // 01's planted poles, hands on the grips
            const lk = Art.CAST.h1, Sh = S * lk.height, y = o.y;
            const pF = poleState(walk), pB = poleState(walk + Math.PI);
            const toW = (q) => ({ x: x + q.x * Sh, y: y + q.y * Sh });
            const bodyInv = bodyBase.translate(x, y).scale(Sh, Sh).inverse();
            o.poles = false; o.reachF = toW(pF.hand); o.reachB = toW(pB.hand);
            o.holdF = poleDrawer(bodyInv, pF, lk.skin, 7.5);
            o.holdB = poleDrawer(bodyInv, pB, U.shade(lk.skin, -0.15), 7);
            o.head = { tilt: -0.06 }; o.face = { smile: 0.12, brow: -0.15 };
          }
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
        // the walk pose throughout: once he stops, the phase is frozen on double support and the stride relaxes
        // to nothing, so he settles into a stand without a pose pop
        o.walk = ME_PH0 + RATE * rateInt(t, G_KEYS);
        o.stride = strideOf(g) * (1 - U.ease(t, T_STOP - 0.1, T_STOP + 0.7));
        Art.person(c2, o);
      });

      const drawSpot = (c) => layer(c, cam, 1, (c2, off) => {
        const fx = FX - off, P = Pd;
        if (fx < -260 || fx > W + 260) return;
        c2.fillStyle = U.shade(P.ground, -0.08);              // a little mossy island at the trail's edge
        c2.beginPath(); c2.ellipse(fx + 6, FY + 4, 96, 13, 0, 0, TAU); c2.fill();
        mossyRock(c2, fx + ROCK.dx, ROCK.y, ROCK.w, ROCK.h, U.mix(P.grass, P.trees[2], 0.25), 7, dP);
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
      const drawFront = (c) => layer(c, cam, 1, (c2, off) => frontGrass(c2, off, -20, W + 20, dP));

      // soft-pass regions: only what can be seen (the letterbox covers the rest)
      const clipPic = (r) => { const y0 = Math.max(PIC.top, r.y), y1 = Math.min(PIC.bottom, r.y + r.h), x0 = Math.max(0, r.x), x1 = Math.min(W, r.x + r.w); return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 }; };
      const nearTop = Math.max(PIC.top, groundTop);
      const nearRegion = { x: 0, y: nearTop, w: W, h: PIC.bottom - nearTop };
      if (nearRegion.h > 0) soft(ctx, groundBlur, drawGround, 'near', nearRegion);
      if (othersVisible) soft(ctx, oBlur, drawOthers, 'others', { x: Math.max(0, leftmost - 20), y: PIC.top - 20, w: W - Math.max(0, leftmost - 20), h: PIC.h + 40 });
      if (meVisible && !preD) soft(ctx, meBlur, drawMe, 'me', { x: 0, y: PIC.top - 20, w: Math.min(W, meScr + 80), h: PIC.h + 40 });
      {
        // the flower spot (island, rock, ferns) spans x FX-110..FX+102, y 852..929 on the trail plane
        const a = toScreen(cam, FX - cam.camX - 115, 846), b = toScreen(cam, FX - cam.camX + 108, 934);
        const r = clipPic({ x: a.x, y: a.y, w: b.x - a.x, h: b.y - a.y });
        if (r.w > 0 && r.h > 0) soft(ctx, spotBlur, drawSpot, 'spot', r);
        // the verge grass row in front of the trail: y = ground + 46, up to ~25 tall
        const g0 = toScreen(cam, 0, GY - GAMP + 46 - 26).y, g1 = toScreen(cam, 0, GY + GAMP + 50).y;
        const rf = clipPic({ x: 0, y: g0, w: W, h: g1 - g0 });
        if (rf.w > 0 && rf.h > 0) soft(ctx, frontBlur, drawFront, 'front', rf);
      }

      /* ---------- 01's sunlight runs on: its rays and shafts melt away as the flower takes his attention (one
                   warm shaft will find the flower instead); its pollen stills and hangs in the air as time stops ---------- */
      const lightK = 1 - U.ease(t, 1.0, 6.2, 'inOutSine');
      const t01 = D01 + wa;                                  // 01's clock, slowed with the world
      if (lightK > 0.004) softF(ctx, 9, (c) => {
        layer(c, cam, 0, (c2) => Art.rays(c2, { x: 1720, y: 40, angle: 2.2, spread: 0.8, count: 5, len: 1250, color: P.light, alpha: 0.21 * lightK, t: wa, seed: 4, width: 0.06 }));
        drawShafts(c, cam, t01, P, 0.104 * lightK);
      }, 'shafts', { x: 0, y: PIC.top, w: W, h: PIC.h }, 'screen');
      const toScrP = (p, x, y) => { const z = zoomOf(cam, p); return { x: CX + z * (x - CX - cam.dx * p), y: CY + z * (y - CY - cam.dy * p) }; };
      pollen(ctx, t01, cam.camX, toScrP, (p) => zoomOf(cam, p), P, 1 - U.ease(t, T_PUSH0 - 1, T_PUSH0 + 1));

      /* ---------- the world loses its colour… ---------- */
      if (!preD) Art.desaturate(ctx, dsat);
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
