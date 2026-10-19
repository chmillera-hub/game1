'use strict';
// Interlude 1 — "Not peace, but a sword." The dinner table in firelit
// silhouette; a blade of light falls and the table splits in two.

const S = require('../lib/stage');
const sets = require('../lib/sets');
const { drawVerse } = require('../lib/text');
const { clamp, smooth, lerp, easeOut, rgbStr } = require('../lib/util');

module.exports = function sword(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('sword');
  const n1 = L('N1'), n2 = L('N2'), n3 = L('N3');
  const nw1 = n1.text.split(/\s+/).length;
  const tStrike = Wd('N1', nw1 - 1) + 0.15;   // the word "sword"
  const mom = env.actor('mom', null, { idle: 0.5 });
  const dad = env.actor('dad', null, { idle: 0.4 });
  const jordan = env.actor('jordan', null, { idle: 0.5 });
  const maya = env.actor('maya', 'dinner', { idle: 0.6 });
  // everyone is silent here; clear lip-sync so nobody mouths along
  for (const a of [mom, dad, jordan, maya]) a.lines = [];

  // family faces Maya (to their right), then turns away word by word
  mom.expr(0, 'tight', 0.01).look(0, { yaw: 0.75, bodyYaw: 0.5, pitch: 0.1 }, 0.01);
  dad.expr(0, 'closed', 0.01).look(0, { yaw: 0.7, bodyYaw: 0.5, pitch: 0.15 }, 0.01);
  jordan.expr(0, 'guilty', 0.01).look(0, { yaw: 0.7, bodyYaw: 0.45, pitch: 0.25 }, 0.01);
  maya.expr(0, 'hurt', 0.01).look(0, { yaw: -0.75, bodyYaw: -0.5, pitch: 0.3 }, 0.01);
  const nw2 = n2.text.split(/\s+/);
  const idx = (word) => Math.max(0, nw2.findIndex((x) => x.toLowerCase().startsWith(word)));
  dad.look(Wd('N2', idx('father')), { yaw: -0.85, bodyYaw: -0.3, lean: -0.5 }, 0.9);
  mom.look(Wd('N2', idx('mother')), { yaw: -0.85, bodyYaw: -0.3, lean: -0.5 }, 0.9);
  jordan.look(Wd('N2', idx('household')) - 0.6, { yaw: -0.85, bodyYaw: -0.2, pitch: 0.4, lean: -0.6 }, 1.0);
  maya.look(n3.start + 2.0, { pitch: -0.05 }, 2.5);                 // she lifts her head
  maya.expr(n3.start + 2.0, 'resolved', 2.5);

  const sil = (rim, rimA = 0.85) => ({ silhouette: { color: [14, 5, 3], rim, rimA, dx: 4, dy: -3, rimBlur: 3 }, light: { x: 0, y: -1 } });

  function backdrop(ctx, t) {
    const bg = S.cachedBg('ember-bg', (c, W, H) => {
      c.fillStyle = sets.radial(c, W / 2, H * 0.62, 50, H * 0.8, [[0, [120, 34, 10]], [0.45, [52, 14, 6]], [1, [8, 2, 2]]]);
      c.fillRect(0, 0, W, H);
    });
    ctx.drawImage(bg, 0, 0);
    // fire glow licking up from below
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 7; i++) {
      const x = 80 + i * 150 + Math.sin(t * 1.3 + i) * 30;
      const hgt = 380 + 120 * Math.sin(t * 2.1 + i * 1.7) + 60 * Math.sin(t * 5.3 + i);
      ctx.save();
      ctx.translate(x, 1920);
      ctx.scale(0.42, 1);
      const g = ctx.createRadialGradient(0, 0, 10, 0, 0, hgt);
      g.addColorStop(0, 'rgba(255,150,50,0.42)');
      g.addColorStop(0.5, 'rgba(200,60,20,0.16)');
      g.addColorStop(1, 'rgba(120,20,5,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(0, 0, hgt, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
    ctx.restore();
  }

  function tableScene(ctx, t) {
    backdrop(ctx, t);
    S.embers(ctx, t, 55, 3, { x0: 0, x1: 1080, y0: 300, y1: 1920 }, [255, 160, 70], 0.9);
    const rim = [255, 150, 60];
    const pm = mom.pose(t), pd = dad.pose(t), pj = jordan.pose(t), py = maya.pose(t);
    const y = 1270;
    S.drawLit(ctx, env.cast.dad, { ...pd, x: 255, y: y - 18, scale: 158 }, sil(rim));
    S.drawLit(ctx, env.cast.mom, { ...pm, x: 95, y: y + 6, scale: 150 }, sil(rim));
    S.drawLit(ctx, env.cast.jordan, { ...pj, x: 405, y: y + 4, scale: 148 }, sil(rim));
    S.drawLit(ctx, env.castFor('maya', 'dinner'), { ...py, x: 880, y: y + 2, scale: 165 }, sil([255, 200, 120], 1.0));
    // the table, side on
    ctx.fillStyle = '#120604';
    ctx.fillRect(-20, y + 70, 1120, 46);
    ctx.fillRect(60, y + 110, 26, 420); ctx.fillRect(990, y + 110, 26, 420);
    ctx.fillStyle = 'rgba(255,150,60,0.35)'; ctx.fillRect(-20, y + 70, 1120, 3);
    // candles still burning on the table
    sets.candle(ctx, 640, y + 72, t, 0.8);
  }

  // Commentary: close on Maya, lit by the blade, lifting her head.
  const tCU = n3.start - 0.4;
  function drawMayaCU(ctx, t) {
    const cam = S.push(t, tCU, sc.end + 1, 1.0, 1.1, 540, 900);
    S.applyCam(ctx, cam);
    backdrop(ctx, t);
    S.embers(ctx, t, 45, 5, { x0: 0, x1: 1080, y0: 300, y1: 1920 }, [255, 160, 70], 0.9);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createLinearGradient(0, 0, 300, 0);
    g.addColorStop(0, 'rgba(255,215,160,0.55)'); g.addColorStop(1, 'rgba(255,170,90,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 300, 1920);
    ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = { ...maya.pose(t), x: 600, y: 1330, scale: 520, yaw: maya.pose(t).yaw * 0.4 - 0.15 };
    S.drawLit(ctx, env.castFor('maya', 'dinner'), P, { light: { x: -0.9, y: -0.3 }, tint: [120, 40, 10], tintA: 0.35, dark: 0.25, rim: { color: [255, 210, 150], a: 0.95, side: -1 } }, cam);
    S.vignette(ctx, 0.6);
  }

  function draw(ctx, t) {
    if (t >= tCU) {
      drawMayaCU(ctx, t);
      const k = t - tCU;
      if (k < 0.7) { const Ly = S.layer(); drawTable(Ly.getContext('2d'), t); ctx.save(); ctx.globalAlpha = 1 - smooth(k / 0.7); ctx.drawImage(Ly, 0, 0); ctx.restore(); S.release(Ly); }
      return;
    }
    drawTable(ctx, t);
  }

  function drawTable(ctx, t) {
    const cam = S.push(t, sc.start, sc.end, 1.0, 1.08, 540, 1100, 660, 1080);
    const Lr = S.layer();
    const lc = Lr.getContext('2d');
    S.applyCam(lc, cam);
    tableScene(lc, t);
    lc.setTransform(1, 0, 0, 1, 0, 0);
    // split after the strike
    const sp = easeOut((t - tStrike - 0.2) / 3.5) * 46;
    ctx.save();
    ctx.beginPath(); ctx.rect(0, 0, 540, 1920); ctx.clip();
    ctx.drawImage(Lr, -sp, 0);
    ctx.restore();
    ctx.save();
    ctx.beginPath(); ctx.rect(540, 0, 540, 1920); ctx.clip();
    ctx.drawImage(Lr, sp, 0);
    ctx.restore();
    S.release(Lr);
    // the gap glows
    if (sp > 0.5) {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const g = ctx.createLinearGradient(540 - sp - 40, 0, 540 + sp + 40, 0);
      g.addColorStop(0, 'rgba(255,170,80,0)'); g.addColorStop(0.5, 'rgba(255,220,160,0.55)'); g.addColorStop(1, 'rgba(255,170,80,0)');
      ctx.fillStyle = g; ctx.fillRect(540 - sp - 40, 0, sp * 2 + 80, 1920);
      ctx.restore();
    }
    // the blade
    const fall = clamp((t - (tStrike - 0.55)) / 0.55);
    if (fall > 0) {
      const tipY = lerp(-500, 1290, Math.pow(fall, 2.2));
      drawBlade(ctx, 540, tipY, t);
    }
    // impact flash
    const fl = clamp(1 - (t - tStrike) / 0.7) * (t >= tStrike ? 1 : 0);
    if (fl > 0) { ctx.save(); ctx.fillStyle = `rgba(255,230,190,${0.75 * fl * fl})`; ctx.fillRect(0, 0, 1080, 1920); ctx.restore(); }
    // verse panel
    const va = (line, a0, a1) => clamp((t - a0) / 0.6) * (1 - clamp((t - a1) / 0.6));
    const cite = 'Matthew 10:34–36';
    if (t < n2.start - 0.2) drawVerse(ctx, n1, t, { y: 470, size: 58, alpha: va(n1, sc.start, n2.start - 0.8) });
    if (t > n2.start - 0.8 && t < n3.start + 0.5) drawVerse(ctx, n2, t, { y: 470, size: 54, cite, alpha: va(n2, n2.start - 0.8, n3.start - 0.2) });
    S.vignette(ctx, 0.55);
  }

  function drawBlade(ctx, x, tipY, t) {
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    const len = 1150;
    const top = tipY - len;
    const shimmer = 0.85 + 0.15 * Math.sin(t * 9);
    const glow = ctx.createLinearGradient(x - 70, 0, x + 70, 0);
    glow.addColorStop(0, 'rgba(255,160,80,0)'); glow.addColorStop(0.5, `rgba(255,210,150,${0.5 * shimmer})`); glow.addColorStop(1, 'rgba(255,160,80,0)');
    ctx.fillStyle = glow; ctx.fillRect(x - 70, top, 140, len);
    ctx.fillStyle = `rgba(255,248,230,${0.95})`;
    ctx.beginPath(); ctx.moveTo(x - 13, top + 140); ctx.lineTo(x + 13, top + 140); ctx.lineTo(x + 9, tipY - 60); ctx.lineTo(x, tipY); ctx.lineTo(x - 9, tipY - 60); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(255,220,170,0.95)';
    ctx.fillRect(x - 85, top + 120, 170, 22);           // crossguard
    ctx.fillRect(x - 9, top, 18, 120);                  // grip
    ctx.beginPath(); ctx.arc(x, top - 6, 20, 0, Math.PI * 2); ctx.fill(); // pommel
    ctx.restore();
  }

  return { id: 'sword', start: sc.start, end: sc.end, draw };
};
