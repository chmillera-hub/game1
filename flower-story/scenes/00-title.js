/* ==========================================================================
   00 · Title — pre-dawn forest. One small flower is the only warm color in
   the frame; the far-off summit glows its promise. The title writes itself.
   (Reference scene: shows the conventions every scene follows.)
   ========================================================================== */
(function () {
  'use strict';
  const { W, H } = U;
  const D = 13;

  // Hand-over to 01. Its 1.5 s dissolve plays this scene at t = 13 … 14.5 under 01 at u = t − 13, and 01
  // opens on its own (flagged) summit further right and lower. Once the title has cleared, the camera tilts
  // up and drifts onto 01's framing of the peak, while the peak eases into 01's on-screen 700 × 440
  // silhouette (same seed, so the same ridges and snow line): through the dissolve the two summits coincide
  // and the only change is the light. Before HAND0 every frame, the poster included, is as it was.
  const SUM0 = { x: 1590, y: 650, h: 410, w: 600 };            // the title's peak (world)
  const Z1 = Math.sqrt((440 * 700) / (SUM0.h * SUM0.w));       // settled zoom: the lens and a ~4% reshaping of
  const SUM1 = { x: SUM0.x, y: SUM0.y, h: 440 / Z1, w: 700 / Z1 };   // the peak share the size change
  const HAND0 = 12.0, HAND1 = 13.35;                            // title gone → settled as 01 starts to show
  const LIFT = 60;   // the move cranes down a touch as it tilts up: near layers rise this much (world px, × depth)
  // 01's summit tip on screen at its local time u (01's camAt: layer 0.03 scrolls by 0.03·camX with
  // camX = V0·(u − 32.5) − 44, and its crane lifts it by 0.03·A + B, A 420 → 30, B 60 → −30 over kO)
  const V01 = 72.32 * Math.sin(0.42) * 6 * 0.8;
  const tip01 = (u) => {
    const kO = U.ease(u, 0.2, 6.8, 'inOutCubic');
    return { x: 1631 - 0.03 * (V01 * (u - 32.5) - 44), y: 215 + 0.03 * U.lerp(420, 30, kO) + U.lerp(60, -30, kO) };
  };

  Film.scene({
    id: 'title',
    order: 0,
    title: 'Title',
    duration: D,
    poster: 8.2, // frame shown behind the Begin button
    mood: 'title',
    sfx: [[0.2, 'swell'], [2.2, 'chime', { gain: 0.5 }], [11.4, 'whoosh', { gain: 0.4 }]],
    fadeIn: 1.6,
    fadeOut: 0,
    post: (t) => ({ vignette: 0.5, grain: 0.05, letterbox: 1 }),

    render(ctx, t) {
      // dawn creeps in over the scene
      const dawnK = U.ease(t, 0, D, 'inOutSine');
      const P = U.mixDeep(Art.TOD.night, Art.TOD.dawn, 0.35 + dawnK * 0.5);
      const push = U.ease(t, 0, D + 2, 'inOutSine');
      const drift = Art.shake(t, 0.35, 11);
      let cam = { x: W / 2 + push * 30 + drift.x, y: H / 2 + 20 - push * 24 + drift.y, zoom: 1 + push * 0.07 };
      // the hand-over to 01 (see SUM0): the tip glides from where this camera shows it onto 01's tip, the
      // zoom eases to Z1, and the camera is solved so the (reshaping) peak's tip lands exactly there
      const tipW0 = { x: SUM0.x + SUM0.w * 0.03, y: SUM0.y - SUM0.h };
      const tipS0 = { x: W / 2 + cam.zoom * (tipW0.x - cam.x), y: H / 2 + cam.zoom * (tipW0.y - cam.y) };
      const hk = U.ease(t, HAND0, HAND1, 'inOutSine');
      let sum = SUM0, tipS = tipS0;
      if (hk > 0) {
        sum = { x: SUM0.x, y: SUM0.y, h: U.lerp(SUM0.h, SUM1.h, hk), w: U.lerp(SUM0.w, SUM1.w, hk) };
        const tw = { x: sum.x + sum.w * 0.03, y: sum.y - sum.h }, s1 = tip01(t - D), z = U.lerp(cam.zoom, Z1, hk);
        tipS = { x: U.lerp(tipS0.x, s1.x, hk), y: U.lerp(tipS0.y, s1.y, hk) };
        cam = { x: tw.x - (tipS.x - W / 2) / z, y: tw.y - (tipS.y - H / 2) / z, zoom: z };
      }

      // near layers rise against the locked far ones (a slight crane down), so the flower keeps its ground
      const lift = LIFT * hk;
      const near = (p, fn) => { if (lift <= 0) { fn(); return; } ctx.save(); ctx.translate(0, -lift * p); fn(); ctx.restore(); };

      ctx.save();
      Art.cam(ctx, cam);

      // sky, stars, the distant summit
      Art.sky(ctx, P, { horizon: 700 });
      Art.stars(ctx, { seed: 4, count: 260, t, alpha: 1 - dawnK * 0.8, y1: 640 });
      Art.ridge(ctx, { seed: 21, y: 640, amp: 170, color: U.mix(P.far, P.sky[1], 0.35) });
      // the peak stands right of the title block so no line of type touches its slopes
      const tip = Art.summit(ctx, { x: sum.x, y: sum.y, h: sum.h, w: sum.w, P, glow: 0.35 + dawnK * 0.4, t, flag: false });
      // 01's flag is planted as the camera settles: its size on screen and its flutter clock are 01's
      const flagA = U.ease(t, 12.5, 13.25);
      if (flagA > 0.01) {
        const fl = Math.sin((t - D - 32.5) * 3) * 3;
        ctx.save();
        ctx.globalAlpha *= flagA;
        ctx.translate(tip.x, tip.y);
        ctx.scale(1 / cam.zoom, 1 / cam.zoom);
        ctx.strokeStyle = U.shade(P.summit, -0.45); ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(0, 2); ctx.lineTo(0, -26); ctx.stroke();
        ctx.fillStyle = U.mix('#e8574a', P.summit, 0.3);           // still in the pre-dawn light
        ctx.beginPath(); ctx.moveTo(0, -26); ctx.lineTo(16, -21 + fl); ctx.lineTo(0, -16); ctx.closePath(); ctx.fill();
        ctx.restore();
      }
      Art.fog(ctx, { y: 650, h: 180, color: P.fog, alpha: 0.55 });
      near(0.08, () => Art.ridge(ctx, { seed: 8, y: 720, amp: 110, color: P.mid }));

      // forest bands, back to front
      near(0.2, () => {
        Art.forest(ctx, { seed: 31, y: 770, spacing: 64, hMin: 130, hMax: 220, color: P.trees[0] });
        Art.fog(ctx, { y: 760, h: 140, color: P.fog, alpha: 0.35 });
      });
      near(0.35, () => Art.forest(ctx, { seed: 32, y: 830, spacing: 90, hMin: 220, hMax: 330, color: P.trees[1], kind: 'mix', sway: 4, t }));

      // the flower: the only saturated thing in the world
      const fx = 960, fy = 905;
      near(1, () => {
        Art.ground(ctx, { y: 880, amp: 14, color: P.ground, color2: P.ground2 });
        const bloom = U.ease(t, 1.0, 6.5, 'outCubic');
        const glowK = 0.35 + 0.65 * U.ease(t, 1.5, 7, 'inOutSine') + Math.sin(t * 1.6) * 0.06;
        Art.glow(ctx, fx, fy - 130, 520, '#ff8db0', 0.22 * glowK);
        Art.flower(ctx, { x: fx, y: fy, s: 0.78, t, bloom: 0.35 + bloom * 0.65, glow: glowK, face: 0.8 });
        Art.grass(ctx, { seed: 5, y: 905, spacing: 6, h: 34, color: P.trees[2], color2: U.shade(P.trees[2], 0.08), t, wind: 0.8 });
        Art.motes(ctx, { seed: 7, count: 26, x0: fx - 260, x1: fx + 260, y0: 520, y1: 900, t, color: '#ffd6e4', size: 1.8, drift: 16, glow: 0.8, alpha: 0.65 * glowK });
      });

      // foreground silhouettes framing the shot
      near(1.15, () => {
        Art.pine(ctx, 120, 1150, 820, '#06080f', { sway: U.wind(t, 0, 3) * 5 });
        Art.pine(ctx, 1830, 1170, 900, '#06080f', { sway: U.wind(t, 900, 4) * 5 });
        Art.pine(ctx, 1560, 1240, 560, '#080a12', { sway: U.wind(t, 400, 5) * 4 });
      });
      ctx.restore();

      // a thin ray of first light from the summit (screen space; it follows the hand-over and lands on the tip)
      Art.glow(ctx, tipW0.x + (tipS.x - tipS0.x) + hk * (tipS0.x - tipW0.x), tipW0.y + (tipS.y - tipS0.y) + hk * (tipS0.y - tipW0.y), 260, P.light, 0.12 * dawnK);

      // title — deferred to the overlay pass so it sits above grain/vignette
      const out = 1 - U.ease(t, 10.2, 12.4, 'inOutSine');
      Art.title(ctx, 'The Hikers,', { y: 368, size: 112, reveal: U.ease(t, 1.6, 4.4, 'outSine'), alpha: out, glow: 'rgba(255,190,160,0.35)', now: false });
      Art.title(ctx, 'the Flower,', { y: 486, size: 112, reveal: U.ease(t, 3.2, 6.0, 'outSine'), alpha: out, color: '#ffd2df', glow: 'rgba(255,111,156,0.55)', now: false });
      Art.title(ctx, 'and the Meaning We Create', { y: 590, size: 54, reveal: U.ease(t, 5.0, 7.6, 'outSine'), alpha: out * 0.92, style: 'normal', weight: 500, spacing: 3, now: false });
      const rule = U.ease(t, 6.4, 8.2, 'inOutCubic') * out;
      if (rule > 0) {
        Art.later((c) => {
          c.strokeStyle = 'rgba(247,239,226,0.45)';
          c.lineWidth = 1.5;
          c.beginPath(); c.moveTo(W / 2 - 150 * rule, 642); c.lineTo(W / 2 + 150 * rule, 642); c.stroke();
        });
      }
      Art.caption(ctx, 'a short film about stopping', { y: 678, size: 30, alpha: U.fade(t, 7.0, 12.2, 1.2, 1.4) * 0.75, style: 'italic', weight: 400 });
    },
  });
})();
