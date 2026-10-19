'use strict';
// Scene 3b — the park bench at golden hour. Sparrows come to her.

const S = require('../lib/stage');
const D = require('../lib/sets_day');
const { drawBird } = require('../lib/birds');
const { clamp, smooth, lerp } = require('../lib/util');

module.exports = function park(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('park');
  const l = (id) => L(id);
  const A = { ...env.castFor('maya', 'work'), headphones: true };
  const maya = env.actor('maya', 'work', { seed: 505, blinkMean: 3.6 });
  const ai = env.actor('ai', null);
  const t27 = l('L27'), t28 = l('L28'), t29 = l('L29'), t30 = l('L30');
  const s0 = sc.start;

  const lap = { hx: 0.2, hy: 1.55, pose: 'hold', front: true, prop: 'phone', propAngle: 1.3, screen: '#a8c6e8' };
  const lapL = { hx: -0.2, hy: 1.6, pose: 'relaxed', front: true, wrist: 0.4 };
  maya.expr(0, 'tired', 0.01).set('lid', 0, 0.85, 0.01).look(0, { pitch: -0.12, yaw: -0.05, roll: -0.06 }, 0.01);
  maya.set('breathDeep', 0, 0.5, 0.01);
  maya.arm('R', 0, lap, 0.01).arm('L', 0, lapL, 0.01);
  maya.set('lid', s0 + 2.3, 0, 0.7).look(s0 + 2.4, { pitch: 0.12, yaw: 0.3, roll: 0, gazeX: 0.5, gazeY: 0.45 }, 0.7);   // opens her eyes, sees the bird
  maya.expr(s0 + 2.5, 'hollow', 0.6);
  maya.expr(t27.start, 'hurt', 0.5).set('wet', t27.start, 0.35, 2);
  maya.look(t27.start + 0.2, { yaw: 0.1, pitch: 0.28, gazeX: 0.1, gazeY: 0.55 }, 0.5);                                // down at the phone
  maya.look(Wd('L27', 9), { yaw: 0.3, gazeX: 0.5, gazeY: 0.4 }, 0.5);
  maya.set('mouthAmp', Wd('L27', 14), -0.15, 0.3);
  maya.expr(t28.start + 1.0, 'vulnerable', 1.0);
  maya.look(Wd('L28', 7), { yaw: 0.32, pitch: 0.15, gazeX: 0.55, gazeY: 0.35 }, 0.6);                                 // watching the sparrow
  maya.slowBlink(Wd('L28', 15), 0.25).set('wet', Wd('L28', 15), 0.55, 1.5);
  maya.expr(t29.start - 0.2, 'soft_smile', 0.8);
  maya.set('roll', t29.start, 0.07, 0.8);
  maya.expr(t30.start + 0.6, 'moved', 1.2).set('roll', t30.end, 0.03, 1.0);
  maya.look(t30.end + 0.2, { pitch: -0.05, yaw: 0.15, gazeX: 0.2, gazeY: -0.1 }, 1.4);                              // looks up at the sky

  const birds = [
    { land: s0 + 1.1, from: [1250, 900], to: [800, 1668], size: 1.05, flip: true, seed: 3 },
    { land: s0 + 2.1, from: [-200, 1100], to: [300, 1860], size: 1.2, flip: false, seed: 5 },
    { land: t28.start + 1.5, from: [1300, 1200], to: [760, 1880], size: 1.25, flip: true, seed: 7 },
  ];
  const birdsCU = [
    { land: s0 + 1.1, from: [1250, 900], to: [890, 1680], size: 2.2, flip: true, seed: 3 },
    { land: t29.start + 0.8, from: [1300, 1300], to: [700, 1720], size: 2.0, flip: true, seed: 9 },
  ];

  const shots = env.cuts([[s0, 'wide'], [t27.start - 0.15, 'cu'], [t30.end + 0.4, 'wide']]);
  const golden = (y0, y1) => ({ y0, y1, top: [255, 210, 150], topA: 0.14, bottom: [40, 20, 30], bottomA: 0.25 });

  function legs(ctx, cx, y0, s) {
    // seated: lower legs and shoes below the seat edge
    for (const k of [-1, 1]) {
      ctx.fillStyle = '#3a3f52';
      ctx.beginPath(); ctx.moveTo(cx + k * 0.08 * s, y0); ctx.lineTo(cx + k * 0.3 * s, y0); ctx.lineTo(cx + k * 0.27 * s, y0 + 0.95 * s); ctx.lineTo(cx + k * 0.1 * s, y0 + 0.95 * s); ctx.fill();
      ctx.fillStyle = '#2a2420';
      ctx.beginPath(); ctx.ellipse(cx + k * 0.2 * s, y0 + 0.98 * s, 0.16 * s, 0.07 * s, 0, 0, Math.PI * 2); ctx.fill();
    }
  }
  function drawWide(ctx, t) {
    const sh = shots(t);
    const cam = S.push(t, sh.t0, sh.t1, 1.0, 1.05, 540, 1150);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('park-wide', (c, W, H) => D.park(c, W, H)), 0, 0);
    // backrest behind her
    ctx.fillStyle = '#4a3226';
    for (let i = 0; i < 3; i++) { ctx.fillRect(170, 1400 + i * 30, 740, 20); }
    ctx.fillStyle = '#2b1e18'; ctx.fillRect(200, 1390, 20, 330); ctx.fillRect(860, 1390, 20, 330);
    legs(ctx, 520, 1770, 260);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = { ...maya.pose(t), x: 520, y: 1150, scale: 260 };
    const lapArms = (a) => (a ? { ...a, hy: a.hy + 0.35 } : a);
    P.armR = lapArms(P.armR); P.armL = lapArms(P.armL);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, 1080, 1705); ctx.clip();                      // body ends at the seat
    S.drawLit(ctx, A, P, { key: golden(800, 1700), light: { x: 0.6, y: -0.7 }, rim: { color: [255, 200, 130], a: 0.7, side: 1 }, parts: 'base' }, cam);
    ctx.restore();
    S.applyCam(ctx, cam);
    ctx.fillStyle = '#3e2a20'; ctx.fillRect(150, 1690, 780, 36);                                // seat edge in front of her
    ctx.fillStyle = '#3a3f52';                                                                   // her lap and knees
    ctx.beginPath(); ctx.ellipse(470, 1735, 70, 46, 0, 0, Math.PI * 2); ctx.ellipse(570, 1735, 70, 46, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(255,200,140,0.35)'; ctx.fillRect(150, 1690, 780, 4);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.drawLit(ctx, A, P, { key: golden(800, 1700), light: { x: 0.6, y: -0.7 }, parts: 'front' }, cam);
    S.applyCam(ctx, cam);
    for (const b of birds) drawBird(ctx, b, t);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.vignette(ctx, 0.45, [40, 10, 20]);
  }
  function drawCU(ctx, t) {
    const sh = shots(t);
    const cam = S.push(t, sh.t0, sh.t1, 1.0, 1.08, 520, 900);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('park-cu', (c, W, H) => D.park(c, W, H, { sunX: 880, sunY: 760, tree: false }), 16), 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const level = ai.speechAt(t).open;
    const P = S.tuckArms({ ...maya.pose(t), x: 500, y: 1310, scale: 500 });
    S.drawLit(ctx, A, P, {
      key: golden(500, 1700), light: { x: 0.7, y: -0.6 }, rim: { color: [255, 205, 140], a: 0.8, side: 1 },
      glow: level > 0.02 ? { x: 600, y: 1800, r: 500, color: [170, 200, 255], a: 0.12 * level } : null,
    }, cam);
    S.applyCam(ctx, cam);
    ctx.fillStyle = '#3e2a20'; ctx.fillRect(0, 1760, 1080, 200);                // bench seat in the foreground
    for (const b of birdsCU) drawBird(ctx, b, t);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; S.glowDisc(ctx, 900, 760, 520, [255, 200, 130], 0.18); ctx.restore();
    S.vignette(ctx, 0.45, [40, 10, 20]);
  }

  function draw(ctx, t) {
    if (shots(t).name === 'cu') drawCU(ctx, t); else drawWide(ctx, t);
  }
  return { id: 'park', start: sc.start, end: sc.end, draw, actors: { maya, ai }, shotAt: shots };
};
