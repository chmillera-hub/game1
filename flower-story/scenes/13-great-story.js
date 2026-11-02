/* ==========================================================================
   13 · A Great Story — back inside the shop, late afternoon. The camera pulls
   back from a steaming mug to reveal the narrator on the window bench: he saw
   the whole thing. Embarrassment comes back in and sweeps the muddy trail to
   the counter. "That’s going to make a great story…" — a smirk — "$300?" —
   a big real laugh, a bashful chuckle, and the price sign gets flipped.

   Reuses window.ShopKit (defined by scenes/11-shop.js). If it's missing,
   a simple warm fallback card keeps the scene (and its words) intact.
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 30;
  const E = (t, a, b, e) => U.ease(t, a, b, e || 'inOutSine');
  const win = (t, a, b, fi = 0.25, fo = 0.25) => U.fade(t, a, b, fi, fo);

  /**
   * Depth of field, cheaper than Art.blurred (same transform contract: drawFn
   * draws in the caller's space). The layer is rendered at 1/f of film
   * resolution into a fixed-size buffer per blur step and stretched back with
   * bilinear filtering — the result is soft anyway, and the bicubic upscale
   * Art.blurred uses costs ~2× in software raster. dof ≈ Art.blurred amount.
   */
  function soft(ctx, dof, key, drawFn) {
    const f = Math.round((1 + dof * 0.4) * 4) / 4;
    if (f < 1.3) { drawFn(ctx); return; }
    const base = Art._base || new DOMMatrix();
    const rel = base.inverse().multiply(ctx.getTransform());
    const cw = Math.ceil(W / f), ch = Math.ceil(H / f);
    const c = Art.canvas('s13:' + key + ':' + f, cw, ch);
    const c2 = c.getContext('2d');
    c2.setTransform(1, 0, 0, 1, 0, 0);
    c2.clearRect(0, 0, cw, ch);
    c2.globalAlpha = 1; c2.globalCompositeOperation = 'source-over';
    c2.setTransform(new DOMMatrix().scale(cw / W, ch / H).multiply(rel));
    drawFn(c2);
    ctx.save();
    ctx.setTransform(base);
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(c, 0, 0, W, H);
    ctx.restore();
  }

  /* ---------------- words ---------------- */
  const CAP = [
    [1.2, 5.6, 'Meanwhile, I’m sitting nearby, watching the whole thing unfold.'],
    [10.8, 13.4, 'Embarrassment smirks.'],
    [18.8, 21.6, '…and I laugh.'],
  ];
  const BUB = [
    [6.0, 10.4, 'That’s going to make a great story, don’t you think?', { who: 'me', maxW: 470 }],
    [13.7, 18.4, 'Yeah, and maybe they would’ve been happier if I charged $300?', { who: 'emb', maxW: 500 }],
  ];

  /* ---------------- fallback (no ShopKit) ---------------- */
  function fallback(ctx, t) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#f1ddc0'); g.addColorStop(0.72, '#e2c49c'); g.addColorStop(0.73, '#c8925a'); g.addColorStop(1, '#deaa6e');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    Art.glow(ctx, 420, 520, 520, '#ffcf8a', 0.35);
    const laugh = win(t, 18.8, 22.5, 0.2, 0.6);
    const me = Art.person(ctx, { look: 'me', x: 560, y: 860, s: 1, pose: 'bench', pack: false, t, head: { turn: 0.3, tilt: -0.22 * laugh }, face: { smile: 0.6 + 0.4 * laugh, eyes: laugh > 0.3 ? 'squeeze' : 'happy', open: laugh, talk: Art.talkingAt(t, BUB, 'me') } });
    const emb = Art.person(ctx, { look: 'emb', x: 1250, y: 880, s: 1, facing: -1, t, head: { turn: 0.3 }, face: { eyes: 'flat', smirk: E(t, 10.8, 11.4), blush: 0.8 + 0.8 * E(t, 19.2, 20), talk: Art.talkingAt(t, BUB, 'emb') } });
    Art.bubbles(ctx, t, [
      [6.0, 10.4, BUB[0][2], { who: 'me', x: 700, y: 330, tx: me.mouth.x + 30, ty: me.mouth.y, maxW: 470 }],
      [13.7, 18.4, BUB[1][2], { who: 'emb', x: 1000, y: 300, tx: emb.mouth.x - 30, ty: emb.mouth.y, maxW: 500 }],
    ]);
  }

  /* ======================================================================
     THE SCENE (with ShopKit)
     ====================================================================== */
  let built = null;
  function build() {
    const K = window.ShopKit;
    const PD = K.PAL.day, PA = K.PAL.afternoon;
    const EMB_SWEEP_Y = 858;

    // the hikers' way out (scene 12 happened in between): fainter, half-dry prints
    const SPOT = K.SPOT || { h1: [990, 879], h2: [840, 885], h4: [690, 876] };
    const exits = [
      K.walker(Object.assign({ look: 'h1', facing: -1, mud: 0.38 }, K.trap(0, 3.2, SPOT.h1[0] - 6, SPOT.h1[1], 96, 842, 0.3, 0.2))),
      K.walker(Object.assign({ look: 'h2', facing: -1, mud: 0.38 }, K.trap(0.2, 3.4, SPOT.h2[0], SPOT.h2[1] + 6, 104, 846, 0.3, 0.2))),
      K.walker(Object.assign({ look: 'h4', facing: -1, mud: 0.38 }, K.trap(0.4, 3.4, SPOT.h4[0], SPOT.h4[1] + 4, 112, 850, 0.3, 0.2))),
    ];
    const PRINTS = [].concat(K.PRINTS_IN || [], exits[0].prints, exits[1].prints, exits[2].prints).map((p) => Object.assign({}, p, { t: -1 }));

    // Embarrassment is back inside, sweeping a bit of the mud up to his counter…
    const SWEEP = K.walker(Object.assign({ look: 'emb', facing: 1, strideMax: 0.5, vNom: 120 }, K.trap(0.2, 6.0, 868, 856, 972, EMB_SWEEP_Y, 0.8, 0.7)));
    const SWEEP_T0 = 0.0, SWEEP_T1 = 6.0;
    // …then steps around the end of the counter and back behind it
    const pathWalk = (t0, t1, pts, acc, dec) => {
      const L = [0];
      for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
      const tr = K.trap(t0, t1, 0, 0, L[L.length - 1], 0, acc, dec);
      const pos = (t) => {
        const d = tr.pos(t)[0];
        let i = 1; while (i < pts.length - 1 && L[i] < d) i++;
        const k = clamp((d - L[i - 1]) / ((L[i] - L[i - 1]) || 1));
        return [lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)];
      };
      return { pos, t0, t1, vNom: tr.vNom };
    };
    const AROUND = K.walker(Object.assign({ look: 'emb', facing: 1, strideMax: 0.8 }, pathWalk(6.3, 9.8, [[972, EMB_SWEEP_Y], [957, 838], [963, 819], [1000, 810], [1160, 809]], 0.45, 0.7)));
    // broom head on the floor: ahead of him, swishing back and forth
    const broomHead = (t, x, y, s) => {
      const sw = t > SWEEP_T0 && t < SWEEP_T1 ? Math.sin((t - SWEEP_T0) * 5.4) * 34 * s * win(t, SWEEP_T0 - 0.5, SWEEP_T1, 0.4, 0.5) : 0;
      return { x: x + 58 * s + sw, y: y - 2 };
    };
    // when did the broom first pass over each print? (precomputed; scrubbing-safe)
    const embPosAt = (t) => (t < 6.3 ? SWEEP.at(t) : AROUND.at(t));
    for (const p of PRINTS) p.swept = Infinity;
    for (let t = SWEEP_T0; t <= SWEEP_T1; t += 1 / 60) {
      const e = embPosAt(t), s = K.sAt(e.y) * 1.1;
      const b = broomHead(t, e.x, e.y, s);
      for (const p of PRINTS) if (p.swept === Infinity && Math.abs(p.x - b.x) < 30 && Math.abs(p.y - b.y) < 26) p.swept = t;
    }
    return { K, PD, PA, PRINTS, SWEEP, AROUND, broomHead, EMB_SWEEP_Y, embPosAt };
  }

  // precompute at load time (ShopKit is defined by 11-shop.js, which loads first)
  try { if (window.ShopKit) built = build(); } catch (e) { built = null; }

  /* ---------------- the camera ---------------- */
  function camAt(t) {
    if (t < 10.65) { // one unbroken pull-back from his face and mug to the two-shot (no jump cut)
      const k = U.ease(t, 0.2, 6.6, 'inOutCubic'), d = E(t, 6.6, 10.65);
      return { x: lerp(478, 700, k) + 16 * d, y: lerp(690, 616, k), zoom: lerp(3.0, 1.36, k) + 0.03 * d, dof: lerp(5, 0, U.ease(t, 1.5, 5.0)) };
    }
    if (t < 18.55) { const k = E(t, 10.65, 18.55); return { x: lerp(1088, 1082, k), y: lerp(580, 576, k), zoom: lerp(2.0, 2.18, k), dof: 3, blurCorner: true }; }
    if (t < 21.8) { const k = E(t, 18.55, 21.8); return { x: lerp(476, 484, k), y: lerp(652, 646, k), zoom: lerp(2.25, 2.42, k), dof: 3 }; } // the laugh: close, pushing in
    if (t < 26.6) { const k = E(t, 21.8, 26.6); return { x: lerp(1094, 1100, k), y: 594, zoom: lerp(1.8, 1.9, k), dof: 2, blurCorner: true }; }
    const k = E(t, 26.6, D + 1);
    return { x: lerp(720, 706, k), y: lerp(612, 606, k), zoom: lerp(1.3, 1.25, k) };
  }
  const toScreen = (cam, p) => ({ x: (p.x - cam.x) * cam.zoom + W / 2, y: (p.y - cam.y) * cam.zoom + H / 2 });

  /* ---------------- the narrator ---------------- */
  function meState(t, K) {
    const s = K.sAt(K.ME.y), x = K.ME.x, y = K.ME.y;
    const sips = [[1.8, 3.6], [11.2, 12.9]];
    let sip = 0; for (const [a, b] of sips) sip = Math.max(sip, win(t, a, b, 0.5, 0.6));
    const laugh = Math.max(win(t, 18.75, 22.6, 0.12, 0.8), 0.75 * win(t, 24.6, 28.6, 0.2, 0.9));
    const talk = Art.talkingAt(t, BUB, 'me');
    // during the line he gestures with the mug toward Embarrassment
    const gest = win(t, 6.0, 10.2, 0.4, 0.6);
    const rest = { x: x + 38 * s, y: y - 84 * s }, lip = { x: x + 12 * s, y: y - 170 * s }, out = { x: x + 64 * s, y: y - 112 * s };
    let hand = { x: lerp(rest.x, lip.x, sip), y: lerp(rest.y, lip.y, sip) };
    hand = { x: lerp(hand.x, out.x, gest), y: lerp(hand.y, out.y, gest) };
    // laughing: the mug comes down to the lap, safely
    hand = { x: lerp(hand.x, x + 30 * s, laugh), y: lerp(hand.y, y - 70 * s, laugh) + Math.sin(t * 19) * 2 * laugh };
    const shake = laugh * (0.5 + 0.5 * Math.sin(t * 18));
    return {
      look: 'me', x, y, s, t, pose: 'bench', pack: false, seed: 3,
      head: { turn: lerp(0.3, 0.55, laugh) + 0.1 * gest, tilt: -0.08 * sip - 0.24 * laugh + Math.sin(t * 17) * 0.025 * laugh },
      shrug: 0.32 * shake,
      lean: -0.06 * laugh,
      face: {
        smile: lerp(0.5, 1, Math.max(laugh, 0.3 * gest)) + 0.2 * talk,
        // eyes open while he watches (the reveal); a blink, then the warm ^ ^ for his line
        eyes: laugh > 0.3 ? 'squeeze' : sip > 0.85 ? 'closed' : t < 5.9 ? 'open' : t < 5.98 ? 'closed' : 'happy',
        open: laugh * (0.75 + 0.25 * Math.sin(t * 18)),
        browUp: 0.35 * gest,
        talk,
        lookX: 0.5,
      },
      reachF: hand,
      holdF: (c) => K.mug(c, sip * 0.7, (1 - sip) * (1 - laugh * 0.5), t),
    };
  }

  /* ---------------- Embarrassment ---------------- */
  function embState(t, B) {
    const K = B.K;
    const p = B.embPosAt(t);
    const o = { look: 'emb', t, facing: 1, seed: 5, x: p.x, y: p.y, s: K.sAt(p.y) * 1.02, head: { turn: 0.22, tilt: 0.16 }, face: { eyes: 'flat', smile: -0.05, lookY: 0.5 } };
    if (p.moving) { o.walk = p.walk; o.stride = p.stride; }
    const S = o.s * 1.1;
    const ex = {};
    // ---- 0 – 10.4: sweeping (until 6.0), then pushing the broom around the counter ----
    if (t < 10.4) {
      const bh = B.broomHead(t, o.x, o.y, S);
      const top = { x: o.x - 14 * S, y: o.y - 236 * S };
      ex.broomHead = bh; ex.broomTop = top;
      const at = (k) => ({ x: lerp(top.x, bh.x, k), y: lerp(top.y, bh.y, k) });
      // hands low enough on the handle that the elbows drop naturally (no "wing")
      o.reachB = at(0.38); o.reachF = at(0.54);
      o.lean = 0.12 + 0.04 * Math.sin(t * 5.4) * win(t, -1, 6.0, 0.1, 0.5);
      ex.sweeping = t < 6.0;
      // he glances over as the narrator starts talking
      const gl = win(t, 6.2, 10.4, 0.5, 0.3);
      o.head = { turn: 0.22 + 0.3 * gl, tilt: lerp(0.16, 0.0, gl) };
      o.face = { eyes: 'flat', smile: -0.05, lookY: lerp(0.5, 0, gl), lookX: -0.6 * gl };
    }
    // ---- 10.4 →: turns to the narrator and leans on the broom; the smirk ----
    if (t >= 10.4) {
      o.facing = -1;
      const settle = E(t, 10.4, 10.9);
      const top = { x: o.x - lerp(10, 44, settle) * S, y: o.y - 196 * S };
      const head = { x: o.x - 76 * S, y: o.y - 2 };
      ex.broomHead = head; ex.broomTop = { x: top.x - 6 * S, y: top.y - 30 * S };
      o.reachF = { x: top.x, y: top.y }; o.reachB = { x: top.x + 4 * S, y: top.y + 6 * S };
      o.lean = 0.12 * settle;
      const sm = E(t, 10.95, 11.6, 'outBack');
      o.head = { turn: 0.38, tilt: -0.04 * sm };
      o.face = { eyes: 'flat', smirk: clamp(sm), smile: 0.18 * sm, browUp: 0.22 * sm, blush: 0.9, talk: Art.talkingAt(t, BUB, 'emb') };
    }
    // ---- chuckles too, blushing harder (hand to his mouth) ----
    const ch = win(t, 19.3, 23.2, 0.3, 0.5) + 0.85 * win(t, 25.1, 29.8, 0.4, 1.2);
    if (ch > 0) {
      const c1 = clamp(ch);
      o.face = { eyes: c1 > 0.4 ? 'closed' : 'flat', smile: 0.6 * c1, smirk: 0.4, blush: 0.9 + 1.0 * c1, open: 0.18 * c1 * (0.5 + 0.5 * Math.sin(t * 13)) };
      o.head = { turn: 0.38, tilt: 0.1 * c1 + Math.sin(t * 12) * 0.022 * c1 };
      o.shrug = 0.2 * c1 * (0.5 + 0.5 * Math.sin(t * 13));
      if (t < 23.0 || t > 25.2) { o.gesture = 'chin'; o.gw = c1; o.reachF = undefined; }
      ex.glow = c1;
    }
    // ---- 23.0 – 25.0: from behind the counter, flips the price sign: $200 → $300 ----
    if (t >= 23.0 && t < 25.0) {
      const k = win(t, 23.0, 25.0, 0.45, 0.5);
      o.gesture = undefined;
      // fingertips on the card's top corner, flicking it over (never covering the price)
      const flick = t > 23.7 && t < 24.0 ? Math.sin((t - 23.7) / 0.3 * Math.PI) * 10 : 0;
      const c = { x: SIGN.x + 30, y: SIGN.y - 100 };
      o.reachF = { x: lerp(o.x - 30 * S, c.x, k) - flick, y: lerp(o.y - 150 * S, c.y, k) - flick * 0.4 };
      o.lean = 0.16 * k;
      o.head = { turn: 0.32, tilt: 0.08 * k };
      o.face = { eyes: 'flat', smirk: 0.85, smile: 0.25, blush: 1.4, lookY: 0.4 * k, lookX: 0.2 * k };
    }
    if (t >= 25.0 && ch < 0.25) o.face = { eyes: 'flat', smirk: 1, smile: 0.25, blush: 1.45, browUp: 0.3 };
    ex.behind = p.y < 838;
    return { o, ex };
  }

  /** the little price sign on the counter: card flips about its vertical axis */
  const SIGN = { x: 1036, y: 684 }; // base on the counter top, at its left end
  function priceSign(ctx, t) {
    const x = SIGN.x, y = SIGN.y;
    const th = U.ease(t, 23.7, 24.15, 'inOutCubic') * Math.PI + Math.sin(clamp((t - 24.15) / 0.5) * Math.PI) * 0.12 * (t > 24.15 && t < 24.65 ? 1 : 0);
    ctx.save();
    // stand
    ctx.fillStyle = '#5a3a26'; ctx.fillRect(x - 3, y - 50, 6, 50);
    ctx.fillRect(x - 16, y - 6, 32, 6);
    // card
    const sx = Math.cos(th), back = sx < 0;
    ctx.translate(x, y - 74);
    ctx.scale(Math.max(0.04, Math.abs(sx)), 1);
    ctx.fillStyle = '#3b2a25'; Art.roundRect(ctx, -38, -28, 76, 56, 6); ctx.fill();
    ctx.fillStyle = back ? '#f6e9cc' : '#f4ecd8'; Art.roundRect(ctx, -34, -24, 68, 48, 4); ctx.fill();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = '#4f7a5a'; ctx.font = Art.font(11, 'sans', 900); ctx.fillText('RARE', 0, -13);
    ctx.fillStyle = '#b8352a'; ctx.font = Art.font(26, 'hand', 700); ctx.fillText(back ? '$300' : '$200', 0, 7);
    ctx.restore();
    // a twinkle when it lands
    const tw = win(t, 24.15, 24.9, 0.05, 0.5);
    if (tw > 0) {
      ctx.save(); ctx.globalAlpha = tw; ctx.strokeStyle = '#fff3c4'; ctx.lineWidth = 2.5; ctx.lineCap = 'round';
      for (let i = 0; i < 6; i++) { const a = -Math.PI / 2 + (i - 2.5) * 0.45, r0 = 52 + (1 - tw) * 10; ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r0, y - 74 + Math.sin(a) * r0 * 0.8); ctx.lineTo(x + Math.cos(a) * (r0 + 12), y - 74 + Math.sin(a) * (r0 + 12) * 0.8); ctx.stroke(); }
      ctx.restore();
    }
  }

  function broom(ctx, top, head, s) {
    ctx.save();
    ctx.strokeStyle = '#a07a4a'; ctx.lineWidth = 5 * s; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(top.x, top.y); ctx.lineTo(head.x, head.y - 18 * s); ctx.stroke();
    const a = Math.atan2(head.y - top.y, head.x - top.x) - Math.PI / 2;
    ctx.translate(head.x, head.y);
    ctx.rotate(a * 0.6);
    ctx.fillStyle = '#c9a85c'; ctx.beginPath(); ctx.moveTo(-20 * s, 0); ctx.lineTo(20 * s, 0); ctx.lineTo(12 * s, -22 * s); ctx.lineTo(-12 * s, -22 * s); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#a8873e'; ctx.lineWidth = 1.2 * s;
    for (let i = -3; i <= 3; i++) { ctx.beginPath(); ctx.moveTo(i * 5 * s, -2); ctx.lineTo(i * 3.6 * s, -20 * s); ctx.stroke(); }
    ctx.fillStyle = '#7a5a2e'; ctx.fillRect(-13 * s, -26 * s, 26 * s, 6 * s);
    ctx.restore();
  }

  /** tail-aware balloon placement (same rules as scene 11) */
  function segHit(ax, ay, bx, by, cx, cy, r) {
    const dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy || 1;
    const u = clamp(((cx - ax) * dx + (cy - ay) * dy) / L2);
    return Math.hypot(ax + u * dx - cx, ay + u * dy - cy) < r;
  }
  function placeBubble(ctx, text, o, spk, heads) {
    const size = o.size || 34;
    ctx.save(); ctx.font = Art.font(size, 'sans', 800);
    const lines = Art.wrap(ctx, text, o.maxW || 540);
    let tw = 0; for (const l of lines) tw = Math.max(tw, ctx.measureText(l).width);
    ctx.restore();
    const w = tw + 56, h = lines.length * size * 1.22 + 40;
    const f = spk.facing || 1;
    const tip = { x: spk.x + f * (spk.r * 1.06 + 8), y: spk.mouth.y + 4 };
    const all = heads.concat([spk]);
    for (let lift = 0; lift <= 320; lift += 20) {
      for (const k of [0.42, 0.25, 0.6, 0.08, -0.12, 0.8]) {
        const x = clamp(tip.x + f * w * k, w / 2 + 30, W - w / 2 - 30);
        const y = spk.top - 22 - h / 2 - lift;
        if (y - h / 2 < Art.PIC.top + 8) continue;
        const L = x - w / 2, R = x + w / 2, T = y - h / 2, B = y + h / 2;
        let bad = false;
        for (const hd of all) { const cy = hd.y - hd.r * 0.15; if (Math.hypot(clamp(hd.x, L, R) - hd.x, clamp(cy, T, B) - cy) < hd.r * 1.28) { bad = true; break; } }
        if (!bad) { const ax = clamp(tip.x, L + 40, R - 40); for (const hd of all) if (segHit(ax, B - 4, tip.x, tip.y, hd.x, hd.y - hd.r * 0.1, hd.r * 1.08 + 6)) { bad = true; break; } }
        if (!bad) return { x, y, tip };
      }
    }
    return { x: clamp(spk.x, w / 2 + 30, W - w / 2 - 30), y: Math.max(Art.PIC.top + h / 2 + 8, spk.top - 22 - h / 2), tip };
  }

  Film.scene({
    id: 'great-story',
    order: 13,
    title: 'A Great Story',
    duration: D,
    mood: 'shop',
    sfx: [
      [0.6, 'bell', { gain: 0.3 }], [2.25, 'bell', { gain: 0.16 }], [3.2, 'scratch', { gain: 0.22 }], [4.4, 'scratch', { gain: 0.2 }],
      [5.6, 'scratch', { gain: 0.18 }], [7.6, 'scratch', { gain: 0.16 }], [9.2, 'scratch', { gain: 0.14 }], [10.9, 'tap', { gain: 0.18 }],
      [18.85, 'laugh', { gain: 0.9 }], [19.5, 'chuckle', { gain: 0.65 }], [23.75, 'paper', { gain: 0.6 }], [24.2, 'ding', { gain: 0.35 }],
      [25.1, 'laugh', { gain: 0.5 }], [25.4, 'chuckle', { gain: 0.4 }],
    ],
    fadeIn: 1.0,
    fadeOut: 1.5,
    post: { vignette: 0.34, grain: 0.04, letterbox: 1 },

    render(ctx, t) {
      Art.captions(ctx, t, CAP);
      if (!window.ShopKit) { fallback(ctx, t); return; }
      if (!built) built = build();
      const B = built, K = B.K, PD = B.PD, PA = B.PA;
      const cam = camAt(t);
      const A = {};
      ctx.save();
      Art.cam(ctx, cam);

      // ---------- the room, late afternoon ----------
      const back = (c) => {
        K.staticSet(c);
        K.windowLettering(c, PD);
        K.bucketTags(c);
        K.clockHands(c, t, 1306, 290, 34, 16 * 3600 + 18 * 60);
        K.hangers(c, t, PD);
        K.beads(c, t, null);
        K.floor(c, PA);
        K.floorLight(c, t, PA, 'afternoon', 1);
        K.drawPrints(c, B.PRINTS, t, (p) => 1 - clamp((t - p.swept) / 0.45));
      };
      // the narrator, and the plants that half-hid him in scene 11: during the
      // pull-back they slide apart (foreground parallax, out of focus) — the reveal
      const plants = (c) => {
        K.monstera(c, 214, 830, 0.94, t);
        K.pampas(c, 690, 833, 0.9, t);
      };
      const blurCorner = cam.dof > 0.6 && cam.blurCorner;
      if (cam.dof > 0.6) soft(ctx, cam.dof, 'bg', (c) => { back(c); if (blurCorner) { A.me = Art.person(c, meState(t, K)); plants(c); } });
      else back(ctx);
      if (!blurCorner) {
        A.me = Art.person(ctx, meState(t, K));
        const fgBlur = t < 5.8 ? 7 * (1 - U.ease(t, 0.5, 4.8)) : 0; // closer than him: soft while we're tight on his face
        if (fgBlur > 0.6) soft(ctx, fgBlur, 'fg', plants); else plants(ctx);
      }

      // ---------- Embarrassment (+ his broom); behind the counter once he's round it ----------
      const { o, ex } = embState(t, B);
      const FL = [10.4];
      const drawEmb = () => {
        if (ex.glow) Art.glow(ctx, o.x, o.y - 240 * o.s, 170, '#ff8db0', 0.16 * ex.glow);
        A.emb = K.person ? K.person(ctx, o, FL) : Object.assign(Art.person(ctx, o), { facing: o.facing });
        const tk = K.turnK ? K.turnK(t, FL) : 1;
        if (tk < 0.995) {
          ex.broomTop = { x: o.x + (ex.broomTop.x - o.x) * tk, y: ex.broomTop.y };
          ex.broomHead = { x: o.x + (ex.broomHead.x - o.x) * tk, y: ex.broomHead.y };
        }
        broom(ctx, ex.broomTop, ex.broomHead, o.s * 1.05);
        ctx.fillStyle = Art.CAST.emb.skin; // fingers over the handle
        if (!o.gesture && !(t >= 23.0 && t < 25.0)) { ctx.beginPath(); ctx.arc(A.emb.handF.x, A.emb.handF.y, 7.5 * o.s * 1.1, 0, TAU); ctx.fill(); }
        if (t >= 10.4) { ctx.beginPath(); ctx.arc(A.emb.handB.x, A.emb.handB.y, 7 * o.s * 1.1, 0, TAU); ctx.fill(); }
        if (ex.sweeping) { // dust kicked up by the bristles
          for (let i = 0; i < 3; i++) {
            const ph = U.fract(t * 0.86 + i / 3);
            K.puff(ctx, ex.broomHead.x + (i - 1) * 10, ex.broomHead.y - 6, ph, 1, 0.55, '#d8c3a0', -0.6);
          }
        }
      };
      if (ex.behind) drawEmb();

      // ---------- the counter, the unsold tulip, the price sign ----------
      K.counter(ctx, PD);
      K.register(ctx, {});
      K.tulip(ctx, 1240, 684, 0.9, t);
      priceSign(ctx, t);
      if (!ex.behind) drawEmb();
      else if (t > 23.2 && t < 24.7 && A.emb) { // fingertips over the card's corner while he flicks it
        ctx.fillStyle = Art.CAST.emb.skin;
        ctx.beginPath(); ctx.arc(A.emb.handF.x, A.emb.handF.y, 7.5 * o.s * 1.1, 0, TAU); ctx.fill();
      }

      // ---------- door + bell (still swaying: the hikers have just left) ----------
      K.door(ctx, PD, 0, t);
      K.bell(ctx, K.swing(t, [[-0.9, 0.34]], 2.6, 1.4));

      // ---------- light in the air: long, low, golden ----------
      K.shafts(ctx, t, PA, 'afternoon', 1.1);
      ctx.restore();

      // ---------- warm afternoon grade; a golden swell at the end ----------
      // (only over the picture area: the letterbox bars cover the rest anyway)
      ctx.save();
      ctx.globalCompositeOperation = 'soft-light'; ctx.globalAlpha = 0.1; ctx.fillStyle = '#ff9a48';
      ctx.fillRect(0, Art.PIC.top, W, Art.PIC.h);
      ctx.restore();
      const swell = U.ease(t, 26.0, D, 'inOutSine');
      if (swell > 0) {
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        const g = ctx.createRadialGradient(560, 520, 50, 560, 520, 1300);
        g.addColorStop(0, `rgba(255,200,120,${0.22 * swell})`); g.addColorStop(1, 'rgba(255,170,90,0)');
        ctx.fillStyle = g; ctx.fillRect(0, Art.PIC.top, W, Art.PIC.h);
        ctx.restore();
      }

      // ---------- balloons ----------
      const heads = [], sp = {};
      for (const k of ['me', 'emb']) {
        if (!A[k]) continue;
        const h = toScreen(cam, A[k].head), m = toScreen(cam, A[k].mouth), tp = toScreen(cam, A[k].top);
        const r = A[k].head.r * cam.zoom;
        sp[k] = { x: h.x, y: h.y, r, top: Math.min(tp.y, h.y - r * 1.2), mouth: m, facing: A[k].facing || 1 };
        heads.push(sp[k]);
      }
      const cues = [];
      for (const [t0, t1, text, bo] of BUB) {
        if (t < t0 - 0.01 || t > t1 + 0.01) continue;
        const spk = sp[bo.who]; if (!spk) continue;
        const pos = placeBubble(ctx, text, bo, spk, heads.filter((h) => h !== spk));
        cues.push([t0, t1, text, Object.assign({}, bo, { x: pos.x, y: pos.y, tx: pos.tip.x, ty: pos.tip.y })]);
      }
      Art.bubbles(ctx, t, cues);
    },
  });
})();
