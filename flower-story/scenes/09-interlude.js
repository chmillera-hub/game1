/* ==========================================================================
   09 · Interlude — a deep-night card. A single magenta petal from the flower
   drifts across the dark, and the line "But the story doesn’t end there."
   writes itself in the petal's wake. A soft light sweeps across like a page
   turning, and we fade into Part Two.
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, clamp, lerp } = U;
  const D = 8;
  const TEXT = 'But the story doesn’t end there.';
  const SIZE = 82;
  const TY = 536; // text line (centre of the picture area)

  /* ---------------- the petal's flight ---------------- */
  // s: 0..1 progress across the frame (slight ease so it glides in and out)
  const T0 = 0.25, T1 = 5.7;
  const prog = (t) => {
    const s = clamp((t - T0) / (T1 - T0));
    return lerp(s, U.E.inOutSine(s), 0.3);
  };
  // height profile: swoops down from the upper left, skims the line, lifts away
  const YK = [[0, 318], [0.25, 506, 'outSine'], [0.74, 516, 'inOutSine'], [1, 404, 'inSine']];
  const petalAt = (t) => {
    const s = prog(t);
    const x = lerp(-120, W + 120, s);
    const y = U.keys(s, YK) + Math.sin(t * 2.3 + 0.6) * 15 + Math.sin(t * 5.1) * 3;
    // tumbling: spin + a 3D flip about the long axis
    const rot = -0.9 + t * 1.15 + Math.sin(t * 1.9) * 0.45;
    // never fully edge-on for long: keep a little width so it reads as a petal
    const c = Math.cos(t * 2.3 + 0.4);
    const flip = U.sign(c) * (0.22 + 0.78 * Math.abs(c));
    return { x, y, rot, flip, s };
  };

  /** one hero petal (same palette as Art.flower), slightly curled and
   *  asymmetric so it never reads as a symmetric lens; length L */
  function petal(c, L, flip) {
    const w = L * 0.42;
    const back = flip < 0;
    const F = Art.FLOWER;
    c.save();
    c.scale(Math.max(0.06, Math.abs(flip)), 1);
    c.translate(0, L * 0.5);
    const gr = c.createLinearGradient(0, 0, L * 0.1, -L);
    gr.addColorStop(0, back ? U.shade(F.inner, -0.1) : F.inner);
    gr.addColorStop(0.4, back ? U.shade(F.petal, -0.2) : F.petal);
    gr.addColorStop(1, back ? U.shade(F.tip, -0.14) : F.tip);
    c.fillStyle = gr;
    const tipX = L * 0.16;
    c.beginPath();
    c.moveTo(0, 0);
    c.bezierCurveTo(w * 1.05, -L * 0.18, w * 1.12 + tipX * 0.5, -L * 0.74, tipX + w * 0.18, -L * 0.98);
    c.quadraticCurveTo(tipX - w * 0.1, -L * 1.04, tipX - w * 0.32, -L * 0.94); // rounded, slightly notched tip
    c.bezierCurveTo(-w * 0.7, -L * 0.8, -w * 0.92, -L * 0.3, 0, 0);
    c.fill();
    // the curl: a darker fold along one edge
    c.fillStyle = U.rgba(back ? '#3d0620' : F.inner, 0.28);
    c.beginPath();
    c.moveTo(0, 0);
    c.bezierCurveTo(-w * 0.92, -L * 0.3, -w * 0.7, -L * 0.8, tipX - w * 0.32, -L * 0.94);
    c.bezierCurveTo(-w * 0.35, -L * 0.7, -w * 0.45, -L * 0.3, 0, 0);
    c.fill();
    // central vein
    c.strokeStyle = U.rgba(F.inner, back ? 0.22 : 0.38);
    c.lineWidth = 1.3;
    c.beginPath(); c.moveTo(0, -L * 0.1); c.quadraticCurveTo(w * 0.16, -L * 0.5, tipX * 0.8, -L * 0.88); c.stroke();
    c.restore();
  }

  let textW = 0, textFont = '';
  function measure(ctx) {
    const f = Art.font(SIZE, 'serif', 500, 'italic');
    if (f !== textFont || !textW) {
      ctx.save(); ctx.font = f; textW = ctx.measureText(TEXT).width; ctx.restore();
      textFont = f;
    }
    return textW;
  }

  Film.scene({
    id: 'interlude',
    order: 9,
    title: 'Interlude',
    duration: D,
    mood: 'silence',
    sfx: [[0.35, 'whoosh', { gain: 0.28 }], [1.5, 'petal', { gain: 0.45 }], [4.35, 'chime', { gain: 0.3 }], [6.55, 'paper', { gain: 0.6 }], [6.75, 'whoosh', { gain: 0.22 }]],
    fadeIn: 1.0,
    fadeOut: 1.0,
    post: { vignette: 0.6, grain: 0.06, letterbox: 1 },

    render(ctx, t) {
      const p = petalAt(t);
      const turn = U.ease(t, 6.45, 7.35, 'inOutSine'); // the page turn at the end

      /* ---- the night card ---- */
      ctx.fillStyle = '#04050b';
      ctx.fillRect(0, 0, W, H);
      const bg = ctx.createRadialGradient(W / 2, TY, 40, W / 2, TY, 1050);
      bg.addColorStop(0, '#171126');
      bg.addColorStop(0.55, '#0b0a17');
      bg.addColorStop(1, '#030308');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);
      Art.stars(ctx, { seed: 91, count: 110, t, alpha: 0.28 * (1 - turn * 0.6), y0: 150, y1: 930 });
      // the petal lights the dark around it
      const inFrame = p.x > -200 && p.x < W + 200;
      if (inFrame) {
        Art.glow(ctx, p.x, p.y, 420, '#7a1f4f', 0.32);
        Art.glow(ctx, p.x, p.y, 150, '#ff6f9c', 0.22);
      }
      // a faint warm bloom where the words will sit
      const tw = measure(ctx);
      const x0 = W / 2 - tw / 2, x1 = W / 2 + tw / 2;
      const written = clamp((p.x - x0 + 30) / tw);
      Art.glow(ctx, W / 2, TY, 760, '#3b1830', 0.25 * written * (1 - turn));

      /* ---- the words, written in the petal's wake (deferred above grain) ---- */
      const n = [...TEXT].length;
      let reveal = clamp(((p.x - x0 + 30) / tw) * n / (n + 6));
      if (t > T1) reveal = 1;
      reveal = Math.max(reveal, U.ease(t, 4.6, 5.2) * 1); // guarantee completion
      const textA = 1 - U.ease(t, 6.5, 7.25, 'inOutSine');
      Art.title(ctx, TEXT, {
        x: W / 2 - turn * 46, y: TY, size: SIZE, reveal, alpha: textA,
        color: '#f6ece0', glow: 'rgba(255,111,156,0.42)', now: false,
      });

      /* ---- the petal and its glittering trail (above the words) ---- */
      if (inFrame) {
        Art.later((c) => {
          // pollen shed by the petal: each mote is born on the path and
          // drifts down and fades (deterministic: indexed by birth time)
          const step = 0.07, now = Math.floor(t / step);
          for (let j = now; j > now - 26; j--) {
            const tb = j * step;
            if (tb < T0) break;
            const age = t - tb;
            const q = petalAt(tb);
            const r1 = U.hash(j, 3), r2 = U.hash(j, 4), r3 = U.hash(j, 5);
            const mx = q.x + (r1 - 0.5) * 34 + age * (r3 - 0.5) * 24;
            const my = q.y + (r2 - 0.5) * 22 + age * (14 + r3 * 22);
            const a = Math.max(0, 1 - age / 1.8) * (0.35 + 0.5 * r3) * (0.6 + 0.4 * Math.sin(t * 9 + j));
            if (a <= 0.01) continue;
            const rr = 0.9 + r1 * 1.9;
            c.globalAlpha = a;
            c.fillStyle = r2 > 0.7 ? '#ffe2a8' : '#ffb3cc';
            c.beginPath(); c.arc(mx, my, rr, 0, U.TAU); c.fill();
            if (r3 > 0.82) { // the odd twinkle
              c.globalAlpha = a * 0.7;
              c.fillRect(mx - rr * 4, my - 0.6, rr * 8, 1.2);
              c.fillRect(mx - 0.6, my - rr * 4, 1.2, rr * 8);
            }
          }
          c.globalAlpha = 1;
          Art.glow(c, p.x, p.y, 70, '#ff8db0', 0.5);
          c.save();
          c.translate(p.x, p.y);
          c.rotate(p.rot);
          c.shadowColor = 'rgba(255,111,156,0.75)';
          c.shadowBlur = 18;
          petal(c, 66, p.flip);
          c.restore();
        });
      }

      /* ---- page turn: a slanted sheen + its soft shadow sweep right → left,
              like the edge of a turning page catching the light ---- */
      if (turn > 0 && turn < 1) {
        const sx = lerp(W + 520, -520, U.E.inOutSine(turn));
        const k = Math.sin(turn * Math.PI);
        Art.later((c) => {
          c.save();
          c.beginPath(); c.rect(0, Art.PIC.top, W, Art.PIC.h); c.clip();
          c.translate(sx, H / 2);
          c.transform(1, 0, -0.32, 1, 0, 0); // slant the band
          // shadow just ahead of the edge (the page lifting)
          const sh = c.createLinearGradient(-420, 0, -20, 0);
          sh.addColorStop(0, 'rgba(0,0,0,0)');
          sh.addColorStop(1, `rgba(0,0,0,${0.32 * k})`);
          c.fillStyle = sh;
          c.fillRect(-420, -H, 400, H * 2);
          // the bright edge
          c.globalCompositeOperation = 'lighter';
          const g = c.createLinearGradient(-20, 0, 220, 0);
          g.addColorStop(0, `rgba(255,222,234,${0.16 * k})`);
          g.addColorStop(0.25, `rgba(255,214,228,${0.07 * k})`);
          g.addColorStop(1, 'rgba(255,214,228,0)');
          c.fillStyle = g;
          c.fillRect(-20, -H, 240, H * 2);
          c.restore();
        });
      }
    },
  });
})();
