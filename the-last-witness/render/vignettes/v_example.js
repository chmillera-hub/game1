// Example vignette showing the expected structure and style (whisper_words).
'use strict';
const U = require('../lib/util');
const FX = require('../lib/fx');

module.exports = {
  whisper_words: {
    testParams: { text: 'No more' },
    draw(ctx, w, h, p) {
      // 1) always paint the full background (dark, smooth, low detail)
      FX.bg(ctx, w, h, [8, 10, 24], [18, 16, 38]);
      FX.stars(ctx, w, h, p.t, p.seed, Math.round(w * h / 9000));
      // 2) one clear idea, slow motion: words drift across like breath and fade
      const text = (p.params && p.params.text) || '';
      const unit = Math.min(w, h);
      // lay the words out on one or two centred lines, each fading in like a breath, drifting slowly
      const size = Math.min(unit * 0.1, (w * 0.86) / Math.max(6, text.length * 0.42));
      ctx.save();
      ctx.font = `300 ${size}px "Inter Display"`;
      const words = text.split(' ').filter(Boolean);
      const lines = [[]];
      for (const word of words) {
        const cur = lines[lines.length - 1];
        if (cur.length && ctx.measureText([...cur, word].join(' ')).width > w * 0.82) lines.push([word]); else cur.push(word);
      }
      ctx.restore();
      let k = 0;
      lines.forEach((ln, li) => {
        ctx.save(); ctx.font = `300 ${size}px "Inter Display"`;
        const total = ctx.measureText(ln.join(' ')).width, space = ctx.measureText(' ').width;
        ctx.restore();
        let x = w / 2 - total / 2 + (p.t * unit * 0.006);
        const y = h * 0.5 + (li - (lines.length - 1) / 2) * size * 1.35 + Math.sin(p.t * 0.4 + li) * unit * 0.01;
        for (const word of ln) {
          ctx.save(); ctx.font = `300 ${size}px "Inter Display"`; const ww = ctx.measureText(word).width; ctx.restore();
          const appear = U.smooth((p.u - k * 0.06) / 0.2);
          FX.text(ctx, word, x + ww / 2, y, size, [210, 225, 255], { weight: 300, family: 'Inter Display', alpha: appear * (1 - U.smooth((p.u - 0.9) / 0.1) * 0.6) * 0.92, glow: [150, 190, 255] });
          x += ww + space; k++;
        }
      });
      // breath vapour
      FX.glow(ctx, w * 0.5, h * 0.52, unit * 0.35, [120, 150, 220], 0.12 + 0.05 * Math.sin(p.t * 0.8));
    },
  },
};
