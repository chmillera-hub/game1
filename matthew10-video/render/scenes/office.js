'use strict';
// Scene 3a — the office. A request for accommodation, waved away.

const S = require('../lib/stage');
const D = require('../lib/sets_day');
const { clamp, smooth, lerp, fbm } = require('../lib/util');

module.exports = function office(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('office');
  const l = (id) => L(id);
  const A = { ...env.castFor('maya', 'work'), headphones: true };
  const maya = env.actor('maya', 'work', { seed: 404, blinkMean: 2.6 });
  const greg = env.actor('greg', null, { talk: 1.4, idle: 1.2 });
  const t22 = l('L22'), t23 = l('L23'), t24 = l('L24'), t25 = l('L25'), t26 = l('L26');
  const tOver = t26.end + 0.4;                         // overwhelm begins

  // ------------------------------------------------------------ Maya
  maya.expr(0, 'tired', 0.01).look(0, { yaw: 0.25, pitch: -0.2, gazeY: -0.55, gazeX: 0.2 }, 0.01);   // squinting up at the light
  maya.set('squint', 0, 0.45, 0.01).set('browKnit', 0, 0.35, 0.01);
  maya.arm('R', 0, { hx: 0.62, hy: 1.9, pose: 'relaxed' }, 0.01);
  maya.arm('L', 0, { hx: -0.62, hy: 1.9, pose: 'relaxed' }, 0.01);
  maya.arm('R', sc.start + 0.4, { hx: 0.4, hy: -0.76, ex: 0.78, ey: 0.3, ew: 1, pose: 'relaxed', front: true, wrist: 0.3 }, 0.6);   // rubs her temple
  for (let k = 0; k < 3; k++) maya.arm('R', sc.start + 1.0 + k * 0.3, { hx: 0.4 + (k % 2) * 0.03, hy: -0.74 - (k % 2) * 0.03, ex: 0.78, ey: 0.3, ew: 1, pose: 'relaxed', front: true, wrist: 0.3 }, 0.28);
  maya.arm('R', t22.start + 0.2, { hx: 0.62, hy: 1.9, pose: 'relaxed', front: false }, 0.4);
  maya.blinkAt(t22.start + 0.05).set('headY', t22.start + 0.05, -0.02, 0.1).set('headY', t22.start + 0.3, 0, 0.3);  // startle at her name
  maya.set('squint', t22.start + 0.1, 0, 0.3);
  maya.look(t22.start + 0.15, { yaw: -0.42, pitch: -0.22, gazeX: -0.45, gazeY: -0.55 }, 0.3);
  maya.expr(t22.start + 0.2, 'attentive', 0.3);
  maya.expr(Wd('L22', 6), 'anxious', 0.6);
  maya.expr(t23.start, 'earnest', 0.4);
  maya.arm('L', t23.start + 0.6, { hx: -0.1, hy: 0.85, pose: 'open', front: true, wrist: 0.6 }, 0.5);      // explaining hand
  maya.arm('L', t24.start + 0.3, { hx: -0.62, hy: 1.9, pose: 'relaxed', front: false }, 0.6);
  maya.expr(t24.start + 0.2, 'stung', 0.3).expr(Wd('L24', 6), 'hurt', 0.8);
  maya.expr(t25.start - 0.4, 'resolved', 0.6).set('pitch', t25.start - 0.4, -0.3, 0.5);                    // chin up, holds his gaze
  maya.set('sacAmp', t25.start - 0.4, 0.2, 0.3).set('sacAmp', t25.end + 0.3, 1, 0.3);
  maya.expr(Wd('L26', 6), 'hurt', 0.5).set('pitch', Wd('L26', 6), -0.18, 0.5);
  maya.look(t26.end - 0.2, { yaw: -0.15, pitch: 0.15, gazeX: -0.3, gazeY: 0.2 }, 0.8);                     // watches him go
  maya.expr(tOver, 'anxious', 0.8).set('breathFast', tOver, 1.8, 1.5).set('breathDeep', tOver, 0.6, 1.5);
  maya.look(tOver + 0.4, { yaw: 0.1, pitch: 0.1, gazeX: 0.3, gazeY: -0.2 }, 0.2);
  maya.look(tOver + 0.9, { yaw: -0.1, gazeX: -0.35, gazeY: 0.1 }, 0.15);
  maya.look(tOver + 1.3, { yaw: 0.05, gazeX: 0.2, gazeY: -0.4 }, 0.15);
  maya.expr(tOver + 1.7, 'overwhelmed', 0.6).set('lid', tOver + 1.8, 0.75, 0.4);
  maya.arm('L', tOver + 1.7, { hx: -0.44, hy: -0.7, ex: -0.86, ey: 0.15, ew: 1, pose: 'open', front: true, wrist: -0.4 }, 0.45);      // hands over her ears
  maya.arm('R', tOver + 1.75, { hx: 0.44, hy: -0.7, ex: 0.86, ey: 0.15, ew: 1, pose: 'open', front: true, wrist: 0.4, flip: 1 }, 0.45);
  maya.set('pitch', tOver + 1.8, 0.25, 0.8).set('shoulderUp', tOver + 1.8, 0.5, 0.6);

  // ------------------------------------------------------------ Greg
  greg.expr(0, 'chipper', 0.01).look(0, { yaw: 0.45, pitch: 0.28, gazeX: 0.45, gazeY: 0.55, lean: 0.25 }, 0.01);
  greg.arm('R', 0, { hx: 0.45, hy: 1.05, pose: 'relaxed', front: true, wrist: 0.2 }, 0.01);                 // leaning on the partition
  greg.arm('L', 0, { hx: -0.66, hy: 1.9, pose: 'relaxed' }, 0.01);
  greg.arm('L', Wd('L22', 7) - 0.3, { hx: -0.3, hy: -0.2, pose: 'open', front: true, wrist: -0.6 }, 0.35);  // "The lights?" — gestures up
  greg.arm('L', Wd('L22', 9) - 0.2, { hx: 0.1, hy: 0.6, pose: 'open', front: true, wrist: 0.4 }, 0.3);      // "The headphones?"
  greg.arm('L', t22.end + 0.4, { hx: -0.66, hy: 1.9, pose: 'relaxed' }, 0.5);
  greg.set('roll', t22.start, 0.08, 0.4);
  greg.expr(t23.start + 1.2, 'impatient', 0.6);
  greg.look(Wd('L23', 6), { yaw: 0.35, gazeX: 0.2, gazeY: 0.3 }, 0.4);
  greg.expr(t24.start - 0.1, 'patronizing', 0.3);
  greg.arm('L', t24.start + 0.1, { hx: -0.1, hy: 0.7, pose: 'open', front: true, wrist: 0.9 }, 0.3);       // waves it off
  greg.arm('L', t24.start + 0.45, { hx: -0.25, hy: 0.6, pose: 'open', front: true, wrist: 0.2 }, 0.25);
  greg.arm('L', t24.start + 0.75, { hx: -0.66, hy: 1.9, pose: 'relaxed' }, 0.5);
  greg.set('roll', t24.start, 0.14, 0.4).set('roll', t24.end, 0.05, 0.4);
  greg.look(t25.start + 0.3, { yaw: 0.3, gazeX: 0.4, gazeY: 0.5 }, 0.3);
  greg.expr(t25.start + 0.6, 'impatient', 0.5);
  greg.expr(t26.start - 0.1, 'chipper', 0.3);
  greg.arm('R', t26.start + 0.2, { hx: 0.4, hy: 0.95, pose: 'relaxed', front: true }, 0.18);                // pat, pat
  greg.arm('R', t26.start + 0.42, { hx: 0.45, hy: 1.05, pose: 'relaxed', front: true }, 0.18);
  greg.arm('R', t26.start + 0.64, { hx: 0.4, hy: 0.95, pose: 'relaxed', front: true }, 0.18);
  greg.arm('R', t26.start + 0.86, { hx: 0.45, hy: 1.05, pose: 'relaxed', front: true }, 0.18);
  greg.expr(Wd('L26', 6), 'patronizing', 0.3).set('roll', Wd('L26', 6), 0.16, 0.3);
  greg.look(Wd('L26', 9), { yaw: -0.4, bodyYaw: -0.6, gazeX: -0.3, gazeY: 0.1 }, 0.5);                      // already turning away
  greg.arm('R', t26.end - 0.2, { hx: 0.66, hy: 1.9, pose: 'relaxed' }, 0.5);

  const shots = env.cuts([
    [sc.start, 'mayaCU'],
    [t22.start - 0.05, 'two'],
    [t23.start + 1.2, 'mayaCUup'],
    [t24.start - 0.1, 'gregCU'],
    [t25.start - 0.5, 'mayaCUup'],
    [t26.start - 0.1, 'two'],
    [tOver - 0.1, 'overwhelm'],
  ]);

  const flick = (t) => {
    const base = 0.5 + 0.5 * Math.sin(t * 37) * Math.sin(t * 11.3);
    const over = smooth((t - tOver) / 2);
    return clamp((base > 0.85 ? 0.8 : 0) + (fbm(t * 6, 3) > 0.55 ? 0.6 : 0) * (0.3 + over));
  };
  const coolKey = (y0, y1) => ({ y0, y1, top: [230, 245, 235], topA: 0.18, bottom: [10, 20, 18], bottomA: 0.28 });

  function room(ctx, cam, t, blur) {
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('office' + blur, (c, W, H) => D.office(c, W, H), blur), 0, 0);
    D.ceilingLights(ctx, 1080, flick(t), smooth((t - tOver) / 2.5));
  }
  function grade(ctx, t) {
    // greenish fluorescent wash; brightness dips with the flicker
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = `rgba(150,190,160,${0.08})`; ctx.fillRect(0, 0, 1080, 1920);
    const f = flick(t);
    if (f > 0) { ctx.fillStyle = `rgba(0,0,0,${0.12 * f})`; ctx.fillRect(0, 0, 1080, 1920); }
    ctx.restore();
  }

  function drawTwo(ctx, t) {
    const cam = S.push(t, 0, 1, 1, 1);
    room(ctx, cam, t, 6);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    // Greg leaves frame after his last line
    const gx = 300 - smooth((t - t26.end - 0.3) / 1.4) * 600;
    const pg = { ...greg.pose(t), x: gx, y: 820, scale: 330 };
    S.drawLit(ctx, env.cast.greg, pg, { key: coolKey(300, 1300), parts: 'base', light: { x: 0.4, y: -0.9 } }, cam);
    S.applyCam(ctx, cam);
    D.cubicleWall(ctx, -20, 1160, 620, 760);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.drawLit(ctx, env.cast.greg, pg, { key: coolKey(300, 1300), parts: 'front', light: { x: 0.4, y: -0.9 } }, cam);
    S.applyCam(ctx, cam);
    D.monitor(ctx, 860, 1060, 300, 220);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const pm = { ...maya.pose(t), x: 720, y: 1365, scale: 340 };
    S.drawLit(ctx, A, pm, { key: coolKey(1000, 1800), light: { x: -0.4, y: -0.9 }, glow: { x: 1000, y: 1200, r: 500, color: [170, 210, 235], a: 0.2 } }, cam);
    S.applyCam(ctx, cam);
    D.desk(ctx, 1700, 1080, 1920);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    grade(ctx, t);
    S.vignette(ctx, 0.4);
  }
  function drawMaya(ctx, t, up, z1) {
    const sh = shots(t);
    const shake = up === 'over' ? smooth((t - tOver - 1.5) / 1.5) : 0;
    const cam = { ...S.push(t, sh.t0, sh.t1, 1.0, z1, 560, 900), dx: shake * 7 * fbm(t * 9, 1), dy: shake * 7 * fbm(t * 9, 2) };
    room(ctx, cam, t, 14);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const pm = { ...maya.pose(t), x: 580, y: 1300, scale: 500 };
    S.drawLit(ctx, A, pm, { key: coolKey(600, 1700), light: { x: -0.4, y: -0.9 }, glow: { x: 1100, y: 1000, r: 700, color: [170, 210, 235], a: 0.18 } }, cam);
    grade(ctx, t);
    if (up === 'over') {
      // sensory overload: pulsing vignette and a harsh white flicker
      const o = smooth((t - tOver - 0.8) / 2);
      S.vignette(ctx, 0.45 + 0.35 * o * (0.6 + 0.4 * Math.sin(t * 14)));
      const f = flick(t * 1.7) * o;
      if (f > 0) { ctx.fillStyle = `rgba(240,255,240,${0.12 * f})`; ctx.fillRect(0, 0, 1080, 1920); }
    } else S.vignette(ctx, 0.4);
  }
  function drawGreg(ctx, t) {
    const sh = shots(t);
    const cam = S.push(t, sh.t0, sh.t1, 1.0, 1.04, 520, 880);
    room(ctx, cam, t, 14);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const pg = { ...greg.pose(t), x: 500, y: 1330, scale: 500, gazeY: 0.45 };
    S.drawLit(ctx, env.cast.greg, pg, { key: coolKey(600, 1700), light: { x: 0.4, y: -0.9 } }, cam);
    grade(ctx, t);
    S.vignette(ctx, 0.4);
  }

  function draw(ctx, t) {
    const sh = shots(t);
    switch (sh.name) {
      case 'two': drawTwo(ctx, t); break;
      case 'mayaCU': drawMaya(ctx, t, 'idle', 1.04); break;
      case 'mayaCUup': drawMaya(ctx, t, 'up', 1.05); break;
      case 'gregCU': drawGreg(ctx, t); break;
      case 'overwhelm': drawMaya(ctx, t, 'over', 1.18); break;
      default: break;
    }
  }
  return { id: 'office', start: sc.start, end: sc.end, draw, tOver, actors: { maya, greg }, shotAt: shots };
};
