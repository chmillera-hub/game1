'use strict';
// Interlude 4 — "When you are persecuted in one place, flee to the next."

const S = require('../lib/stage');
const D = require('../lib/sets_day');
const { drawVerse } = require('../lib/text');
const { clamp, smooth, lerp } = require('../lib/util');

module.exports = function road(env) {
  const { L, scene } = env;
  const sc = scene('road');
  const n8 = L('N8');
  const A = env.castFor('maya', 'night');

  // a small figure seen from behind, walking toward the town
  function walker(ctx, x, y, s, t) {
    const ph = t * 6.2;
    const bob = Math.abs(Math.sin(ph)) * 4 * s;
    ctx.save();
    ctx.translate(x, y - bob);
    ctx.scale(s, s);
    for (const k of [-1, 1]) {
      const sw = Math.sin(ph + (k > 0 ? Math.PI : 0)) * 10;
      ctx.fillStyle = '#2a2d3e';
      ctx.beginPath(); ctx.moveTo(k * 9, 0); ctx.lineTo(k * 17, 0); ctx.lineTo(k * 14 + sw * 0.4, 62 + Math.max(0, -sw) * 0.4); ctx.lineTo(k * 6 + sw * 0.4, 62 + Math.max(0, -sw) * 0.4); ctx.fill();
    }
    ctx.fillStyle = A.outfit.main;
    ctx.beginPath(); ctx.moveTo(-26, -70); ctx.quadraticCurveTo(0, -84, 26, -70); ctx.lineTo(24, 4); ctx.lineTo(-24, 4); ctx.fill();
    for (const k of [-1, 1]) { // arms swing
      const sw = Math.sin(ph + (k > 0 ? 0 : Math.PI)) * 8;
      ctx.save(); ctx.translate(k * 24, -64); ctx.rotate(k * 0.12 + sw * 0.02);
      ctx.fillRect(-6, 0, 12, 56); ctx.restore();
    }
    ctx.fillStyle = A.hair;
    ctx.beginPath(); ctx.arc(0, -100, 30, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(0, -84, 36, 30, 0, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }

  function draw(ctx, t) {
    const u = clamp((t - sc.start) / (sc.end - sc.start + 1.2));
    const dawn = smooth(u) * 0.85;
    const cam = S.push(t, sc.start, sc.end + 1, 1.0, 1.1, 540, 1100, 540, 1060);
    S.applyCam(ctx, cam);
    D.road(ctx, 1080, 1920, t, dawn);
    // she walks away from us, getting smaller
    const y = lerp(1700, 1330, smooth(u));
    const s = lerp(1.6, 0.75, smooth(u));
    walker(ctx, 540 + Math.sin(t * 0.7) * 6, y, s, t);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.vignette(ctx, 0.5);
    drawVerse(ctx, n8, t, { y: 380, size: 54, cite: 'Matthew 10:22–23', alpha: clamp((t - sc.start) / 0.6) });
  }
  return { id: 'road', start: sc.start, end: sc.end, draw, actors: {}, shotAt: () => ({ name: 'road', t0: sc.start, t1: sc.end }) };
};
