'use strict';
// Epilogue — the next town: a kinder room, a brother reaching back, a sparrow.

const S = require('../lib/stage');
const D = require('../lib/sets_day');
const { roundRect } = require('../lib/body');
const { drawEndCard } = require('../lib/text');
const { clamp, smooth, lerp } = require('../lib/util');

module.exports = function epilogue(env) {
  const { L, W: Wd, scene, timeline } = env;
  const sc = scene('epilogue');
  const l = (id) => L(id);
  const A = env.castFor('maya', 'new');
  const maya = env.actor('maya', 'new', { seed: 909 });
  const priya = env.actor('priya', null, { talk: 1.2 });
  const t40 = l('L40'), t41 = l('L41'), n9 = l('N9');
  const s0 = sc.start;
  const tBuzz = t41.end + 0.6;
  const tWindow = n9.start - 0.4;
  const tEnd = timeline.duration;

  const rest = (s) => ({ hx: s * 0.62, hy: 1.9, pose: 'relaxed', front: false });
  maya.expr(0, 'attentive', 0.01).look(0, { yaw: 0.3, gazeX: 0.4, pitch: 0.05 }, 0.01);
  maya.arm('L', 0, rest(-1), 0.01).arm('R', 0, rest(1), 0.01);
  maya.look(s0 + 0.6, { yaw: 0.1, gazeX: 0.1, gazeY: -0.3, pitch: -0.1 }, 0.5);                 // looks around the room
  maya.expr(s0 + 0.5, 'anxious', 0.6);
  maya.look(t40.start + 0.1, { yaw: -0.38, gazeX: -0.45, gazeY: 0, pitch: 0 }, 0.3);
  maya.expr(t40.start + 0.2, 'attentive', 0.4);
  maya.look(Wd('L40', 6), { gazeY: -0.6, pitch: -0.15 }, 0.4).look(Wd('L40', 9), { gazeY: 0, pitch: 0 }, 0.4);   // glances up at the dark lights
  maya.expr(t40.end - 0.4, 'surprised', 0.3);
  maya.expr(t41.start + 0.4, 'joy', 0.8).set('wet', t41.start, 0.5, 1.0);
  maya.look(tBuzz + 0.2, { pitch: 0.3, gazeY: 0.6, yaw: 0.05 }, 0.4);                                  // phone buzzes
  maya.arm('R', tBuzz + 0.1, { hx: 0.16, hy: 0.98, ex: 0.62, ey: 0.8, ew: 1, pose: 'hold', front: true, prop: 'phone', propAngle: 1.25, screen: '#cfe2f7' }, 0.5);
  maya.expr(tBuzz + 1.8, 'moved', 0.8).set('wet', tBuzz + 1.8, 0.85, 1.2);
  maya.arm('L', tBuzz + 2.4, { hx: -0.04, hy: -0.4, ex: -0.5, ey: 0.55, ew: 1, pose: 'open', front: true, wrist: -0.25 }, 0.5);  // hand to her mouth
  maya.tear(-1, tBuzz + 2.6, 1.8);
  maya.arm('L', tBuzz + 4.3, rest(-1), 0.6);
  maya.expr(tBuzz + 4.2, 'joy', 0.8);
  // at the window
  maya.look(tWindow, { yaw: 0.35, gazeX: 0.5, pitch: 0.12, gazeY: 0.4 }, 0.01);
  maya.arm('R', tWindow, rest(1), 0.01).arm('L', tWindow, rest(-1), 0.01);
  maya.expr(tWindow, 'tender', 0.01).set('wet', tWindow, 0.4, 0.01);
  maya.expr(Wd('N9', 12), 'joy', 1.4);

  priya.expr(0, 'neutral', 0.01).look(0, { yaw: 0.3, pitch: 0.2, gazeY: 0.5, gazeX: 0.3 }, 0.01);
  priya.arm('L', 0, rest(-1), 0.01).arm('R', 0, rest(1), 0.01);
  priya.look(t40.start - 0.4, { yaw: 0.45, pitch: 0.0, gazeY: 0.0, gazeX: 0.5 }, 0.4);
  priya.expr(t40.start - 0.3, 'warm', 0.4);
  priya.arm('R', Wd('L40', 4), { hx: 0.62, hy: -1.45, ex: 0.92, ey: -0.3, ew: 1, pose: 'open', front: true, wrist: -0.2, flip: 1 }, 0.4);   // points up at the lights
  priya.arm('R', Wd('L40', 9), rest(1), 0.5);
  priya.set('roll', Wd('L40', 12), 0.08, 0.4);
  priya.expr(t41.end - 0.2, 'smile', 0.6);

  const shots = env.cuts([
    [s0, 'two'],
    [t41.start - 0.15, 'mayaCU'],
    [tBuzz + 0.7, 'phone'],
    [tBuzz + 2.2, 'mayaCU'],
    [tBuzz + 4.0, 'phone2'],
    [tWindow, 'window'],
  ]);
  const day = (y0, y1) => ({ y0, y1, top: [255, 240, 215], topA: 0.16, bottom: [60, 40, 30], bottomA: 0.18 });

  function room(ctx, cam, blur) {
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('newoffice' + blur, (c, W, H) => D.newOffice(c, W, H), blur), 0, 0);
  }
  function drawTwo(ctx, t) {
    const sh = shots(t);
    const cam = S.push(t, sh.t0, sh.t1, 1.0, 1.04, 540, 1000);
    room(ctx, cam, 4);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.drawLit(ctx, env.cast.priya, { ...priya.pose(t), x: 260, y: 1250, scale: 300 }, { key: day(700, 1600), light: { x: -0.7, y: -0.6 }, rim: { color: [255, 236, 200], a: 0.5, side: -1 } }, cam);
    S.drawLit(ctx, A, { ...maya.pose(t), x: 780, y: 1270, scale: 320 }, { key: day(700, 1600), light: { x: -0.7, y: -0.6 }, rim: { color: [255, 236, 200], a: 0.5, side: -1 } }, cam);
    S.applyCam(ctx, cam);
    ctx.fillStyle = '#d8c4a0'; ctx.fillRect(0, 1640, 1080, 280);
    ctx.fillStyle = 'rgba(120,90,60,0.3)'; ctx.fillRect(0, 1640, 1080, 8);
    D.plant(ctx, 540, 1640, 0.6);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.vignette(ctx, 0.3);
  }
  function drawMayaCU(ctx, t) {
    const sh = shots(t);
    const cam = S.push(t, sh.t0, sh.t1, 1.0, 1.06, 560, 880);
    room(ctx, cam, 16);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = S.tuckArms({ ...maya.pose(t), x: 560, y: 1310, scale: 510 }, 1.6);
    S.drawLit(ctx, A, P, { key: day(500, 1700), light: { x: -0.7, y: -0.6 }, rim: { color: [255, 236, 200], a: 0.6, side: -1 } }, cam);
    S.vignette(ctx, 0.3);
  }
  function drawPhone(ctx, t, reply) {
    ctx.fillStyle = '#e9e2d6'; ctx.fillRect(0, 0, 1080, 1920);
    ctx.fillStyle = '#1c1d24'; roundRect(ctx, 150, 200, 780, 1520, 80); ctx.fill();
    ctx.fillStyle = '#f4f5f8'; roundRect(ctx, 176, 226, 728, 1468, 60); ctx.fill();
    ctx.fillStyle = '#e6e8ee'; ctx.fillRect(176, 226, 728, 170);
    ctx.textAlign = 'center'; ctx.fillStyle = '#1d1f26'; ctx.font = '54px InterSemi'; ctx.fillText('Jordan', 540, 330);
    ctx.textAlign = 'left';
    const msg = ['hey. what you said at dinner…', 'i think i feel that way too.', 'can we talk?'];
    const k = clamp((t - (tBuzz + 0.75)) / 0.25);
    ctx.globalAlpha = k;
    ctx.fillStyle = '#e3e5ea'; roundRect(ctx, 210, 520, 600, 230, 40); ctx.fill();
    ctx.fillStyle = '#1d1f26'; ctx.font = '42px InterMed';
    msg.forEach((m, i) => ctx.fillText(m, 240, 590 + i * 58));
    ctx.globalAlpha = 1;
    if (reply) {
      const n = Math.floor(9 * clamp((t - (tBuzz + 4.1)) / 0.9));
      const txt = 'Anytime.'.slice(0, n);
      ctx.fillStyle = '#4a7bd6'; roundRect(ctx, 520, 800, 340, 110, 40); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.font = '46px InterSemi'; ctx.fillText(txt, 556, 872);
      if (n >= 9 || t > tBuzz + 5.1) heart(ctx, 800, 852, 22);
    }
    S.vignette(ctx, 0.35);
  }
  function heart(ctx, x, y, r) {
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.moveTo(x, y + r * 0.9);
    ctx.bezierCurveTo(x - r * 1.4, y - r * 0.1, x - r * 0.7, y - r * 1.2, x, y - r * 0.4);
    ctx.bezierCurveTo(x + r * 0.7, y - r * 1.2, x + r * 1.4, y - r * 0.1, x, y + r * 0.9);
    ctx.fill();
  }
  function drawWindow(ctx, t) {
    const cam = S.push(t, tWindow, tEnd + 1, 1.0, 1.1, 520, 920);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('sunrise', (c, W, H) => {
      const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#7f8fc4'); g.addColorStop(0.4, '#f2b38a'); g.addColorStop(0.75, '#ffd9a0'); g.addColorStop(1, '#c8946c');
      c.fillStyle = g; c.fillRect(0, 0, W, H);
      const sg = c.createRadialGradient(820, 880, 10, 820, 880, 900); sg.addColorStop(0, 'rgba(255,250,225,1)'); sg.addColorStop(0.12, 'rgba(255,225,170,0.7)'); sg.addColorStop(1, 'rgba(255,200,140,0)');
      c.fillStyle = sg; c.fillRect(0, 0, W, H);
      c.fillStyle = 'rgba(120,90,110,0.55)';
      for (let i = 0; i < 14; i++) c.fillRect(i * 80, 1180 - (i * 37 % 140), 70, 400);
    }, 6), 0, 0);
    // window frame
    ctx.strokeStyle = '#f3ece0'; ctx.lineWidth = 30; ctx.strokeRect(40, 160, 1000, 1240);
    ctx.lineWidth = 18; ctx.beginPath(); ctx.moveTo(540, 160); ctx.lineTo(540, 1400); ctx.moveTo(40, 760); ctx.lineTo(1040, 760); ctx.stroke();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = S.tuckArms({ ...maya.pose(t), x: 380, y: 1430, scale: 560 }, 1.6);
    S.drawLit(ctx, A, P, { key: day(600, 1800), light: { x: 0.8, y: -0.5 }, rim: { color: [255, 225, 170], a: 1.0, side: 1 } }, cam);
    S.applyCam(ctx, cam);
    // sill and the sparrow that lands on it
    ctx.fillStyle = '#efe6d6'; ctx.fillRect(0, 1560, 1080, 60);
    ctx.fillStyle = 'rgba(80,60,40,0.25)'; ctx.fillRect(0, 1616, 1080, 14);
    const land = Wd('N9', 6);
    const fly = smooth((t - (land - 1.0)) / 1.0);
    if (t > land - 1.0) {
      const bx = lerp(1250, 860, fly), by = lerp(1100, 1520, fly) - Math.sin(fly * Math.PI) * 120;
      D.sparrow(ctx, bx, by, 1.6, { flip: true, flap: t < land ? t * 34 : null, flying: t < land, look: t > land + 1.5 ? -0.9 : 0.3 });
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; S.glowDisc(ctx, 820, 880, 640, [255, 220, 170], 0.25); ctx.restore();
    S.vignette(ctx, 0.35, [60, 30, 20]);
    const endA = clamp((t - (n9.end + 0.6)) / 1.0);
    if (endA > 0) {
      ctx.fillStyle = `rgba(20,10,5,${0.35 * endA})`; ctx.fillRect(0, 0, 1080, 1920);
      drawEndCard(ctx, endA);
    }
  }

  function draw(ctx, t) {
    const sh = shots(t);
    switch (sh.name) {
      case 'two': drawTwo(ctx, t); break;
      case 'mayaCU': drawMayaCU(ctx, t); break;
      case 'phone': drawPhone(ctx, t, false); break;
      case 'phone2': drawPhone(ctx, t, true); break;
      case 'window': drawWindow(ctx, t); break;
      default: break;
    }
  }
  const subs = (t) => !shots(t).name.startsWith('phone');
  return { id: 'epilogue', start: sc.start, end: sc.end, draw, subs };
};
