'use strict';
// Interlude 2 — "Whoever loses their life ... will find it." The performed
// smile cracks and falls away; then the window lays a cross of light on her.

const S = require('../lib/stage');
const N = require('../lib/sets_night');
const { drawCharacter } = require('../lib/character');
const { drawVerse } = require('../lib/text');
const { clamp, smooth, lerp, rng, easeIn } = require('../lib/util');

module.exports = function cross(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('cross');
  const n4 = L('N4'), n5 = L('N5');
  const words = n4.text.split(/\s+/);
  const wi = (w, from = 0) => { for (let i = from; i < words.length; i++) if (words[i].toLowerCase().startsWith(w)) return i; return 0; };
  const tCrack = Wd('N4', wi('whoever', 2));              // "Whoever finds their life..."
  const tFall = Wd('N4', wi('loses'));                      // "...loses their life"
  const tFound = Wd('N4', words.length - 1);                // "...will find it."

  const maskA = env.actor('maya', 'night', { seed: 303, idle: 0 });
  const trueA = env.actor('maya', 'night', { seed: 304, idle: 0.7 });
  const moon = env.actor('maya', 'night', { seed: 305, idle: 0.6 });
  for (const a of [maskA, trueA, moon]) a.lines = [];
  maskA.expr(0, 'fake_smile', 0.01).look(0, { yaw: 0, pitch: 0, gazeX: 0, gazeY: 0, sacAmp: 0 }, 0.01);
  maskA.extra.noBlink = true;
  trueA.expr(0, 'crying', 0.01).look(0, { yaw: 0.0, pitch: 0.12, gazeY: 0.3 }, 0.01);
  trueA.tear(1, tFall + 0.2, 2.2);
  trueA.look(tFound - 0.3, { pitch: -0.02, gazeY: 0 }, 1.2).expr(tFound - 0.2, 'relief', 1.6);
  moon.expr(0, 'tired', 0.01).set('lid', 0, 0.75, 0.01).look(0, { pitch: 0.15, yaw: -0.1 }, 0.01);
  moon.set('breathDeep', n5.start, 0.6, 1.5);
  moon.set('lid', Wd('N5', 14), 0, 1.2).look(Wd('N5', 14), { pitch: -0.05, yaw: 0.0, gazeY: -0.05 }, 1.6);
  moon.expr(Wd('N5', 20), 'tender', 2.0);
  moon.arm('R', 0, { hx: 0.6, hy: 1.9, pose: 'relaxed', front: false }, 0.01);
  moon.arm('R', n5.start + 1.0, { hx: 0.04, hy: 0.6, ex: 0.62, ey: 0.88, ew: 1, pose: 'open', front: true, wrist: 0.1, flip: 1 }, 1.0);

  // mirror shards: a fan of jagged triangles around the impact point
  const cx = 540, cy = 860;
  const r = rng(77);
  const shards = [];
  let a0 = 0;
  while (a0 < Math.PI * 2 - 0.05) {
    const a1 = Math.min(Math.PI * 2, a0 + 0.22 + r() * 0.35);
    const rr0 = 70, rr1 = 1300;
    const ring = [[cx + Math.cos(a0) * rr0, cy + Math.sin(a0) * rr0], [cx + Math.cos(a0) * rr1, cy + Math.sin(a0) * rr1],
      [cx + Math.cos(a1) * rr1, cy + Math.sin(a1) * rr1], [cx + Math.cos(a1) * rr0, cy + Math.sin(a1) * rr0]];
    shards.push({ poly: ring, delay: r() * 0.9, spin: (r() - 0.5) * 1.2, drift: (r() - 0.5) * 200, mid: (a0 + a1) / 2 });
    a0 = a1;
  }
  shards.push({ poly: Array.from({ length: 9 }, (_, i) => [cx + Math.cos(i / 9 * Math.PI * 2) * 70, cy + Math.sin(i / 9 * Math.PI * 2) * 70]), delay: 0.0, spin: 0.4, drift: 0, mid: 0 });

  function crackLines(ctx, k) {
    const rr = rng(78);
    ctx.save();
    ctx.strokeStyle = `rgba(255,250,240,${0.85})`;
    ctx.lineCap = 'round';
    for (const s of shards.slice(0, -1)) {
      const len = 1300 * clamp(k * (0.7 + rr() * 0.6));
      ctx.lineWidth = 2 + rr() * 2.5;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      let px = cx, py = cy;
      for (let seg = 1; seg <= 6; seg++) {
        const d = (len * seg) / 6;
        const jit = (rr() - 0.5) * 0.12;
        px = cx + Math.cos(s.mid + jit) * d; py = cy + Math.sin(s.mid + jit) * d;
        ctx.lineTo(px, py);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  function faceLayer(actor, t, look) {
    const Ly = S.layer();
    const c = Ly.getContext('2d');
    c.fillStyle = look.bg; c.fillRect(0, 0, 1080, 1920);
    const P = { ...actor.pose(t), x: 540, y: 1520, scale: 700 };
    drawCharacter(c, env.castFor('maya', 'night'), { ...P, rim: look.rim }, { light: { x: -0.4, y: -0.8 } });
    c.globalCompositeOperation = 'source-atop';
    c.fillStyle = look.tint; c.fillRect(0, 0, 1080, 1920);
    return Ly;
  }

  function drawMirrorPhase(ctx, t) {
    const cam = S.push(t, sc.start, n5.start, 1.0, 1.06, 540, 900);
    // underneath: her true face, warm and present
    const under = faceLayer(trueA, t, { bg: '#2a140c', tint: 'rgba(255,170,100,0.18)', rim: { color: [255, 190, 120], a: 0.6, side: 1 } });
    S.applyCam(ctx, cam);
    ctx.drawImage(under, 0, 0);
    S.release(under);
    S.embers(ctx, t, 30, 8, { x0: 0, x1: 1080, y0: 200, y1: 1920 }, [255, 170, 90], clamp((t - tFall) / 1.5));
    // on top: the mask, cracking and falling away in shards
    const top = faceLayer(maskA, t, { bg: '#1b2628', tint: 'rgba(225,235,240,0.32)' });
    const crackK = smooth((t - tCrack) / 1.4);
    if (t < tFall) {
      // intact (if cracked) mirror: one piece, so no seams between shards show
      S.applyCam(ctx, cam);
      ctx.drawImage(top, 0, 0);
    } else for (const s of shards) {
      const ft = t - tFall - s.delay;
      const y = ft > 0 ? 0.5 * 2600 * ft * ft : 0;
      if (y > 2200) continue;
      ctx.save();
      S.applyCam(ctx, cam);
      const mx = s.poly.reduce((a, p) => a + p[0], 0) / s.poly.length, my = s.poly.reduce((a, p) => a + p[1], 0) / s.poly.length;
      ctx.translate(mx + (ft > 0 ? s.drift * ft : 0), my + y);
      ctx.rotate(ft > 0 ? s.spin * ft : 0);
      ctx.translate(-mx, -my);
      ctx.beginPath(); s.poly.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
      ctx.clip();
      ctx.drawImage(top, 0, 0);
      if (crackK > 0) { // glints along shard edges
        ctx.strokeStyle = `rgba(255,255,255,${0.5 * crackK})`; ctx.lineWidth = 3;
        ctx.beginPath(); s.poly.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); ctx.stroke();
      }
      ctx.restore();
    }
    S.release(top);
    if (crackK > 0 && t < tFall + 0.2) { S.applyCam(ctx, cam); crackLines(ctx, crackK); }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const fl = clamp(1 - (t - tFall) / 0.5) * (t >= tFall ? 1 : 0);
    if (fl > 0) { ctx.fillStyle = `rgba(255,245,230,${0.5 * fl})`; ctx.fillRect(0, 0, 1080, 1920); }
    const bloom = clamp((t - tFound) / 1.5) * (1 - clamp((t - n5.start + 0.6) / 0.6));
    if (bloom > 0) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; S.glowDisc(ctx, 540, 820, 900, [255, 200, 140], 0.25 * bloom); ctx.restore(); }
    S.vignette(ctx, 0.6);
    drawVerse(ctx, n4, t, { y: 300, size: 52, cite: 'Matthew 10:38–39', alpha: clamp((t - sc.start) / 0.6) * (1 - clamp((t - n5.start + 0.5) / 0.6)) });
  }

  function drawMoonPhase(ctx, t) {
    const cam = S.push(t, n5.start - 0.5, sc.end + 1, 1.0, 1.12, 540, 900, 540, 860);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('bedroom-moon', (c, W, H) => N.bedroom(c, W, H, { window: { x: 600, y: 120, w: 440, h: 620 } }), 14), 0, 0);
    ctx.fillStyle = 'rgba(5,8,20,0.45)'; ctx.fillRect(0, 0, 1080, 1920);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = { ...moon.pose(t), x: 540, y: 1360, scale: 540 };
    S.drawLit(ctx, env.castFor('maya', 'night'), P, { light: { x: 0.6, y: -0.6 }, tint: [40, 60, 120], tintA: 0.35, dark: 0.15, rim: { color: [190, 210, 255], a: 0.6, side: 1 } }, cam);
    // moonlight through the window: four panes of light with the cross of the frame left dark
    S.applyCam(ctx, cam);
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    const grow = smooth((t - n5.start + 0.3) / 2.5);
    const bx = 120, by = 380, bw = 860, bh = 1500, bar = 70;
    const panes = [[bx, by, (bw - bar) / 2, (bh - bar) / 2], [bx + (bw + bar) / 2, by, (bw - bar) / 2, (bh - bar) / 2],
      [bx, by + (bh + bar) / 2, (bw - bar) / 2, (bh - bar) / 2], [bx + (bw + bar) / 2, by + (bh + bar) / 2, (bw - bar) / 2, (bh - bar) / 2]];
    for (const [x, y, w, h] of panes) {
      const g = ctx.createLinearGradient(x, y, x + w, y + h);
      g.addColorStop(0, `rgba(170,190,255,${0.2 * grow})`); g.addColorStop(1, `rgba(120,150,230,${0.08 * grow})`);
      ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
    }
    ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.vignette(ctx, 0.65);
  }

  function draw(ctx, t) {
    if (t < n5.start - 0.5) drawMirrorPhase(ctx, t);
    else drawMoonPhase(ctx, t);
    // quick dissolve between the two phases
    const k = t - (n5.start - 0.5);
    if (k >= 0 && k < 0.6) {
      const Ly = S.layer();
      drawMirrorPhase(Ly.getContext('2d'), t);
      ctx.save(); ctx.globalAlpha = 1 - smooth(k / 0.6); ctx.drawImage(Ly, 0, 0); ctx.restore();
      S.release(Ly);
    }
  }

  return { id: 'cross', start: sc.start, end: sc.end, draw, actors: { maskA, trueA, moon }, shotAt: (t) => (t < n5.start - 0.5 ? { name: 'mirror', t0: sc.start, t1: n5.start - 0.5 } : { name: 'moon', t0: n5.start - 0.5, t1: sc.end }), tCrack, tFall, tFound, shards };
};
