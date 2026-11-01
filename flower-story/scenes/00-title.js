/* ==========================================================================
   00 · Title — pre-dawn forest. One small flower is the only warm color in
   the frame; the far-off summit glows its promise. The title writes itself.
   (Reference scene: shows the conventions every scene follows.)
   ========================================================================== */
(function () {
  'use strict';
  const { W, H } = U;
  const D = 13;

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

      ctx.save();
      Art.cam(ctx, { x: W / 2 + push * 30 + drift.x, y: H / 2 + 20 - push * 24 + drift.y, zoom: 1 + push * 0.07 });

      // sky, stars, the distant summit
      Art.sky(ctx, P, { horizon: 700 });
      Art.stars(ctx, { seed: 4, count: 260, t, alpha: 1 - dawnK * 0.8, y1: 640 });
      Art.ridge(ctx, { seed: 21, y: 640, amp: 170, color: U.mix(P.far, P.sky[1], 0.35) });
      const tip = Art.summit(ctx, { x: 1290, y: 650, h: 400, w: 640, P, glow: 0.35 + dawnK * 0.4, t, flag: false });
      Art.fog(ctx, { y: 650, h: 180, color: P.fog, alpha: 0.55 });
      Art.ridge(ctx, { seed: 8, y: 720, amp: 110, color: P.mid });

      // forest bands, back to front
      Art.forest(ctx, { seed: 31, y: 770, spacing: 64, hMin: 130, hMax: 220, color: P.trees[0] });
      Art.fog(ctx, { y: 760, h: 140, color: P.fog, alpha: 0.35 });
      Art.forest(ctx, { seed: 32, y: 830, spacing: 90, hMin: 220, hMax: 330, color: P.trees[1], kind: 'mix', sway: 4, t });
      Art.ground(ctx, { y: 880, amp: 14, color: P.ground, color2: P.ground2 });

      // the flower: the only saturated thing in the world
      const fx = 960, fy = 905;
      const bloom = U.ease(t, 1.0, 6.5, 'outCubic');
      const glowK = 0.35 + 0.65 * U.ease(t, 1.5, 7, 'inOutSine') + Math.sin(t * 1.6) * 0.06;
      Art.glow(ctx, fx, fy - 130, 520, '#ff8db0', 0.22 * glowK);
      Art.flower(ctx, { x: fx, y: fy, s: 0.78, t, bloom: 0.35 + bloom * 0.65, glow: glowK, face: 0.8 });
      Art.grass(ctx, { seed: 5, y: 905, spacing: 6, h: 34, color: P.trees[2], color2: U.shade(P.trees[2], 0.08), t, wind: 0.8 });
      Art.motes(ctx, { seed: 7, count: 26, x0: fx - 260, x1: fx + 260, y0: 520, y1: 900, t, color: '#ffd6e4', size: 1.8, drift: 16, glow: 0.8, alpha: 0.65 * glowK });

      // foreground silhouettes framing the shot
      Art.pine(ctx, 120, 1150, 820, '#06080f', { sway: U.wind(t, 0, 3) * 5 });
      Art.pine(ctx, 1830, 1170, 900, '#06080f', { sway: U.wind(t, 900, 4) * 5 });
      Art.pine(ctx, 1560, 1240, 560, '#080a12', { sway: U.wind(t, 400, 5) * 4 });
      ctx.restore();

      // a thin ray of first light from the summit
      Art.glow(ctx, tip.x, tip.y, 260, P.light, 0.12 * dawnK);

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
