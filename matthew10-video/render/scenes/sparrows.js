'use strict';
// Interlude 3 — "You are worth more than many sparrows."

const S = require('../lib/stage');
const D = require('../lib/sets_day');
const { drawVerse } = require('../lib/text');
const { clamp, smooth, lerp, rng } = require('../lib/util');

module.exports = function sparrows(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('sparrows');
  const n6 = L('N6'), n7 = L('N7');
  const A = { ...env.castFor('maya', 'work'), headphones: true };
  const maya = env.actor('maya', 'work', { seed: 606, idle: 0.6 });
  maya.lines = [];
  const tLand = n7.start + 0.4;
  maya.expr(0, 'tender', 0.01).set('lid', 0, 0.8, 0.01).look(0, { pitch: -0.08, roll: -0.05 }, 0.01);
  maya.set('lid', tLand + 0.8, 0, 0.6).look(tLand + 1.0, { yaw: 0.35, pitch: 0.1, gazeX: 0.8, gazeY: 0.5, roll: 0.04 }, 0.6);  // sees the bird on her shoulder
  maya.expr(tLand + 1.3, 'joy', 1.2);

  const r = rng(61);
  const flock = Array.from({ length: 46 }, () => ({
    x0: -300 - r() * 900, y0: 1350 + r() * 600, vx: 260 + r() * 140, vy: 120 + r() * 90,
    amp: 20 + r() * 50, ph: r() * 6, size: 0.45 + r() * 0.6, flapRate: 28 + r() * 14,
  }));
  const feathers = Array.from({ length: 14 }, () => ({ x: r() * 1080, y0: -100 - r() * 900, v: 60 + r() * 50, sway: r() * 6, s: 0.7 + r() * 0.8 }));

  function sky(ctx, t) {
    ctx.drawImage(S.cachedBg('golden-sky', (c, W, H) => {
      c.fillStyle = (function () { const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#4d5a96'); g.addColorStop(0.35, '#d98e6a'); g.addColorStop(0.7, '#ffcf8a'); g.addColorStop(1, '#ffe2a8'); return g; })();
      c.fillRect(0, 0, W, H);
      const g2 = c.createRadialGradient(W * 0.6, H * 0.72, 10, W * 0.6, H * 0.72, H * 0.6);
      g2.addColorStop(0, 'rgba(255,248,220,0.95)'); g2.addColorStop(0.15, 'rgba(255,220,160,0.5)'); g2.addColorStop(1, 'rgba(255,200,140,0)');
      c.fillStyle = g2; c.fillRect(0, 0, W, H);
      // a few long clouds lit from below
      c.fillStyle = 'rgba(255,190,150,0.35)';
      for (const [x, y, w] of [[200, 520, 420], [760, 640, 360], [420, 900, 500]]) { c.beginPath(); c.ellipse(x, y, w, 26, 0, 0, Math.PI * 2); c.fill(); }
    }), 0, 0);
  }
  function feathersDraw(ctx, t, a) {
    ctx.save();
    for (const f of feathers) {
      const y = f.y0 + (t - sc.start) * f.v;
      if (y < -50 || y > 2000) continue;
      const x = f.x + Math.sin((t + f.sway) * 1.3) * 40;
      ctx.translate(x, y); ctx.rotate(Math.sin((t + f.sway) * 1.7) * 0.8); ctx.scale(f.s, f.s);
      ctx.fillStyle = `rgba(150,110,80,${0.8 * a})`;
      ctx.beginPath(); ctx.ellipse(0, 0, 22, 7, 0, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = `rgba(90,60,40,${0.8 * a})`; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(-26, 0); ctx.lineTo(22, 0); ctx.stroke();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    }
    ctx.restore();
  }

  function drawFlock(ctx, t) {
    sky(ctx, t);
    const k = t - sc.start;
    for (const b of flock) {
      const x = b.x0 + b.vx * k, y = b.y0 - b.vy * k + Math.sin(k * 1.4 + b.ph) * b.amp;
      if (x < -120 || x > 1200 || y < -120) continue;
      D.sparrow(ctx, x, y, b.size, { flap: (t + b.ph) * b.flapRate, flying: true });
    }
    feathersDraw(ctx, t, 1);
  }

  function drawShoulder(ctx, t) {
    const cam = S.push(t, n7.start - 0.6, sc.end + 1, 1.0, 1.1, 520, 900);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('golden-sky-blur', (c, W, H) => D.park(c, W, H, { sunX: 860, sunY: 820, tree: false }), 18), 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = { ...maya.pose(t), x: 520, y: 1330, scale: 520 };
    S.drawLit(ctx, A, P, { key: { y0: 500, y1: 1700, top: [255, 215, 150], topA: 0.18, bottom: [60, 20, 30], bottomA: 0.2 }, light: { x: 0.7, y: -0.6 }, rim: { color: [255, 210, 150], a: 0.9, side: 1 } }, cam);
    // the sparrow lands on her shoulder
    S.applyCam(ctx, cam);
    const fly = smooth((t - (tLand - 1.1)) / 1.1);
    const bx = lerp(1250, 830, fly), by = lerp(700, 1330 + 0.05 * 520 - 46, fly) - Math.sin(fly * Math.PI) * 140;
    if (t > tLand - 1.1) {
      const landed = t >= tLand;
      const hop = landed ? 0 : 0;
      D.sparrow(ctx, bx, by, 1.5, { flip: true, flap: landed ? null : t * 34, flying: !landed, hop, look: landed ? (t > tLand + 1.2 ? -0.8 : 0.4) : 0 });
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; S.glowDisc(ctx, 880, 820, 560, [255, 205, 140], 0.22); ctx.restore();
    feathersDraw(ctx, t, 0.6);
    S.vignette(ctx, 0.4, [50, 15, 20]);
  }

  function draw(ctx, t) {
    const toShoulder = n7.start - 0.6;
    if (t < toShoulder) drawFlock(ctx, t);
    else drawShoulder(ctx, t);
    const k = t - toShoulder;
    if (k >= 0 && k < 0.8) {
      const Ly = S.layer(); drawFlock(Ly.getContext('2d'), t);
      ctx.save(); ctx.globalAlpha = 1 - smooth(k / 0.8); ctx.drawImage(Ly, 0, 0); ctx.restore();
      S.release(Ly);
    }
    const a6 = clamp((t - sc.start) / 0.6) * (1 - clamp((t - n7.start + 0.4) / 0.5));
    if (a6 > 0) drawVerse(ctx, n6, t, { y: 330, size: 54, alpha: a6 });
    const a7 = clamp((t - n7.start + 0.3) / 0.5);
    if (a7 > 0) drawVerse(ctx, n7, t, { y: 300, size: 58, cite: 'Matthew 10:29–31', alpha: a7 });
  }
  return { id: 'sparrows', start: sc.start, end: sc.end, draw, actors: { maya }, shotAt: (t) => (t < n7.start - 0.6 ? { name: 'flock', t0: sc.start, t1: n7.start - 0.6 } : { name: 'shoulder', t0: n7.start - 0.6, t1: sc.end }), tLand };
};
