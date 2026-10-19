'use strict';
// Scene 2 — The Mask. The mirror rehearsal, then the late-night conversation.

const S = require('../lib/stage');
const N = require('../lib/sets_night');
const { drawCharacter } = require('../lib/character');
const { clamp, smooth, lerp, rgbStr } = require('../lib/util');

module.exports = function mask(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('mask');
  const l = (id) => L(id);
  const real = env.actor('maya', 'night', { seed: 101 });
  const refl = env.actor('maya', 'night', { seed: 101 });
  const bed = env.actor('maya', 'night', { seed: 202, blinkMean: 3.8 });
  const ai = env.actor('ai', null);

  // ------------------------------------------------------------ mirror
  const t14 = l('L14'), t15 = l('L15');
  for (const a of [real, refl]) {
    a.expr(0, 'hollow', 0.01).look(0, { yaw: -0.5, pitch: 0.05, gazeX: -0.35 }, 0.01);
    a.set('shoulderUp', sc.start + 0.1, 0.3, 0.4).set('shoulderUp', t14.start, 0, 0.5);         // gathers herself
    a.expr(t14.start - 0.3, 'fake_smile', 0.22);
    a.set('pitch', t14.start + 0.3, -0.1, 0.15).set('pitch', t14.start + 0.6, 0.05, 0.2).set('pitch', t14.start + 1.0, -0.06, 0.2);
    a.set('roll', Wd('L14', 4), 0.1, 0.3).set('roll', t14.end + 0.2, 0.02, 0.5);
  }
  // the real smile drains; the reflection's stays a beat too long
  real.expr(t14.end + 0.45, 'fading', 0.9).expr(t14.end + 1.3, 'unsettled', 0.8);
  real.look(t14.end + 1.4, { gazeY: 0.15, gazeX: -0.45 }, 0.3).set('lean', t14.end + 1.6, -0.15, 1.0).set('headX', t14.end + 1.6, -0.03, 1.0);
  real.slowBlink(t14.end + 1.2, 0.1);
  refl.expr(t14.end + 1.9, 'fading', 1.1).expr(t14.end + 2.9, 'unsettled', 0.6);
  refl.look(t14.end + 1.4, { gazeY: 0.15, gazeX: -0.45 }, 0.3).set('lean', t14.end + 1.6, -0.15, 1.0).set('headX', t14.end + 1.6, -0.03, 1.0);
  for (const a of [real, refl]) {
    a.set('yaw', t15.start + 0.2, -0.42, 0.3).set('yaw', t15.start + 0.5, -0.56, 0.3).set('yaw', t15.end, -0.5, 0.4);
    a.set('mouthAmp', t15.start - 0.1, -0.35, 0.1);   // whispered: smaller mouth
  }

  // ------------------------------------------------------------ bedroom
  const t16 = l('L16'), t17 = l('L17'), t18 = l('L18'), t19 = l('L19'), t20 = l('L20'), t21 = l('L21');
  const bedStart = t15.end + 0.7;
  const typing = { hx: 0.25, hy: 2.2, pose: 'relaxed', front: false };
  const hugL = { hx: 0.25, hy: 1.45, pose: 'relaxed', front: true, wrist: -0.6 };
  const hugR = { hx: -0.25, hy: 1.5, pose: 'relaxed', front: true, wrist: 0.6 };
  bed.expr(0, 'hollow', 0.01).look(0, { yaw: 0.05, pitch: 0.32, gazeY: 0.55 }, 0.01);
  bed.arm('L', 0, { ...typing, hx: -0.3 }, 0.01).arm('R', 0, typing, 0.01);
  bed.expr(t16.start, 'hurt', 0.8);
  // reading the reply: sweeping saccades along each line of text
  const read = (t0, t1, a) => {
    a.set('sacAmp', t0, 0.3, 0.2).set('sacAmp', t1, 1, 0.3);
    for (let t = t0, k = 0; t < t1 - 0.4; t += 1.6, k++) {
      a.set('gazeX', t, -0.35, 0.12);
      a.set('gazeX', t + 0.12, 0.35, 1.25, 'linear');
      a.set('gazeY', t, 0.45 + (k % 3) * 0.06, 0.12);
    }
    a.set('gazeX', t1 - 0.2, 0, 0.3);
  };
  read(t17.start + 0.3, t17.end, bed);
  bed.expr(t17.start + 1.5, 'vulnerable', 1.0).set('wet', t17.start + 2, 0.35, 2).slowBlink(Wd('L17', 20), 0.25);
  bed.arm('L', t18.start - 0.6, hugR, 0.7).arm('R', t18.start - 0.6, hugL, 0.7);                // knees up, arms around them
  bed.set('pitch', t18.start - 0.5, 0.12, 0.6).set('headY', t18.start - 0.5, 0.04, 0.6);
  bed.expr(t18.start, 'hurt', 0.4).look(t18.start + 0.1, { yaw: 0.22, gazeX: 0.45, gazeY: 0.25 }, 0.4);
  bed.look(t19.start + 0.2, { yaw: 0.05, gazeX: 0, gazeY: 0.45, pitch: 0.25 }, 0.5);
  read(t19.start + 0.5, t19.end, bed);
  bed.set('wet', Wd('L19', 14), 0.75, 1.5).slowBlink(Wd('L19', 20), 0.4).tear(1, Wd('L19', 22), 1.8);
  bed.expr(Wd('L19', 18), 'crying', 1.2);
  bed.set('pitch', t20.start - 1.2, 0.2, 0.8).set('headY', t20.start - 1.2, 0.07, 0.8);         // chin toward her knees
  bed.expr(t20.start - 0.4, 'vulnerable', 0.8).look(t20.start - 0.2, { gazeY: 0.3, gazeX: -0.2, yaw: -0.05 }, 0.6);
  bed.set('mouthAmp', t20.start - 0.1, -0.2, 0.2);
  bed.look(t21.start + 0.2, { gazeX: 0, gazeY: 0.45 }, 0.5);
  read(t21.start + 0.4, t21.end - 1.0, bed);
  bed.expr(Wd('L21', 9), 'tender', 1.4).set('shoulderUp', Wd('L21', 9), -0.25, 1.2).tear(-1, Wd('L21', 12), 2.2);
  bed.set('pitch', t21.end, 0.12, 1.2).set('headY', t21.end, 0.02, 1.2);

  const msgs = [
    { from: 'me', text: t16.text, t0: t16.start - 0.6, t1: t16.end - 0.2 },
    { from: 'ai', text: t17.text, t0: t17.start, t1: t17.end },
    { from: 'me', text: t18.text, t0: t18.start - 0.2, t1: t18.end },
    { from: 'ai', text: t19.text, t0: t19.start, t1: t19.end },
    { from: 'me', text: t20.text, t0: t20.start - 0.2, t1: t20.end },
    { from: 'ai', text: t21.text, t0: t21.start, t1: t21.end },
  ];

  const shots = env.cuts([
    [sc.start, 'mirror'],
    [bedStart, 'bedWide'],
    [t16.start - 0.6, 'screen'],
    [t16.start + 1.6, 'bedCU'],
    [t17.start - 0.2, 'screen'],
    [t17.start + 2.6, 'bedCU'],
    [t19.start - 0.1, 'screen'],
    [t19.start + 2.4, 'bedCU'],
    [t20.start - 1.4, 'bedCU2'],
  ]);

  const mirrorRect = { x: 40, y: 200, w: 640, h: 980 };
  const coolKey = (y0, y1) => ({ y0, y1, top: [225, 240, 235], topA: 0.1, bottom: [5, 15, 20], bottomA: 0.35 });
  const pj = '#8b84a3';

  function drawMirror(ctx, t) {
    const cam = S.push(t, sc.start, bedStart, 1.0, 1.07, 540, 960, 520, 900);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('bathroom', (c, W, H) => N.bathroom(c, W, H)), 0, 0);
    N.mirrorGlass(ctx, mirrorRect);
    // reflection: a true mirror image of Maya facing back toward herself
    ctx.save();
    ctx.beginPath(); ctx.rect(mirrorRect.x, mirrorRect.y, mirrorRect.w, mirrorRect.h); ctx.clip();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const L1 = S.layer(); const l1 = L1.getContext('2d');
    S.applyCam(l1, cam);
    l1.translate(360, 0); l1.scale(-1, 1); l1.translate(-360, 0);
    const pr = { ...refl.pose(t), x: 360, y: 1235, scale: 400 };
    drawCharacter(l1, env.castFor('maya', 'night'), pr, { light: { x: 0.5, y: -0.9 } });
    l1.setTransform(1, 0, 0, 1, 0, 0);
    l1.globalCompositeOperation = 'source-atop';
    l1.fillStyle = 'rgba(40,70,80,0.22)'; l1.fillRect(0, 0, 1080, 1920);
    S.applyCam(ctx, cam);
    ctx.beginPath(); ctx.rect(mirrorRect.x + 8, mirrorRect.y + 8, mirrorRect.w - 16, mirrorRect.h - 16); ctx.clip();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(L1, 0, 0);
    S.release(L1);
    ctx.restore();
    S.applyCam(ctx, cam);
    N.mirrorFrame(ctx, mirrorRect);
    N.vanityLight(ctx, 360, 160, 420);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    // Maya herself, foreground right
    const p = { ...real.pose(t), x: 800, y: 1470, scale: 410 };
    S.drawLit(ctx, env.castFor('maya', 'night'), p, { key: coolKey(900, 1700), light: { x: -0.7, y: -0.8 }, rim: { color: [220, 240, 230], a: 0.35, side: -1 } }, cam);
    S.vignette(ctx, 0.55);
  }

  function knees(ctx, cx, y, s) {
    ctx.save();
    for (const k of [-1, 1]) {
      const g = ctx.createRadialGradient(cx + k * 0.3 * s, y - 0.2 * s, 0.05 * s, cx + k * 0.3 * s, y, 0.6 * s);
      g.addColorStop(0, '#a7a0bd'); g.addColorStop(1, '#5c5670');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.ellipse(cx + k * 0.3 * s, y + 0.25 * s, 0.36 * s, 0.6 * s, k * 0.08, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }
  function drawBedCU(ctx, t, z0, z1, t0, t1) {
    const cam = S.push(t, t0, t1, z0, z1, 540, 900, 540, 880);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('bedroom-cu', (c, W, H) => N.bedroom(c, W, H, { window: { x: 560, y: 160, w: 480, h: 640 } }), 18), 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = { ...bed.pose(t), x: 540, y: 1330, scale: 520 };
    const kneesUp = smooth((t - (t18.start - 0.6)) / 0.7);
    const look = {
      key: coolKey(700, 1700), light: { x: 0.0, y: 0.6 },
      glow: { x: 540, y: 1650, r: 950, color: [175, 205, 255], a: 0.38 },
      tint: [70, 90, 160], tintA: 0.14,
      rim: { color: [255, 190, 120], a: 0.45, side: -1 },
      parts: 'base',
    };
    S.drawLit(ctx, env.castFor('maya', 'night'), P, look, cam);
    if (kneesUp > 0.01) {
      S.applyCam(ctx, cam);
      ctx.globalAlpha = kneesUp;
      knees(ctx, 540, lerp(2100, 1730, kneesUp), 520);
      ctx.globalAlpha = 1;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    }
    S.drawLit(ctx, env.castFor('maya', 'night'), P, { ...look, parts: 'front', glow: { ...look.glow, a: 0.12 } }, cam);
    // laptop edge glowing at the bottom of frame
    S.applyCam(ctx, cam);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    S.glowDisc(ctx, 540, 1980, 520, [150, 190, 255], 0.35);
    ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.vignette(ctx, 0.6);
  }
  function drawBedWide(ctx, t) {
    const cam = S.push(t, bedStart, t16.start, 1.0, 1.06, 540, 1100);
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('bedroom-wide', (c, W, H) => N.bedroom(c, W, H)), 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = { ...bed.pose(t), x: 520, y: 1300, scale: 240 };
    S.drawLit(ctx, env.castFor('maya', 'night'), P, { light: { x: 0, y: 0.6 }, glow: { x: 520, y: 1500, r: 500, color: [170, 200, 255], a: 0.4 }, tint: [40, 50, 110], tintA: 0.3 }, cam);
    S.applyCam(ctx, cam);
    // duvet over her legs and the glowing laptop
    ctx.fillStyle = '#4a4a6e'; ctx.beginPath(); ctx.ellipse(540, 1620, 520, 200, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#20232e'; ctx.beginPath(); ctx.moveTo(400, 1560); ctx.lineTo(680, 1560); ctx.lineTo(650, 1420); ctx.lineTo(430, 1420); ctx.fill();
    ctx.fillStyle = 'rgba(170,205,255,0.9)'; ctx.beginPath(); ctx.moveTo(444, 1548); ctx.lineTo(636, 1548); ctx.lineTo(612, 1432); ctx.lineTo(468, 1432); ctx.fill();
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; S.glowDisc(ctx, 540, 1480, 420, [150, 190, 255], 0.3); ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.vignette(ctx, 0.6);
  }
  function drawScreen(ctx, t) {
    ctx.fillStyle = '#05060a'; ctx.fillRect(0, 0, 1080, 1920);
    const cam = S.push(t, 0, 1, 1, 1);
    S.applyCam(ctx, cam);
    const level = ai.speechAt(t).open;
    N.chatScreen(ctx, { x: 60, y: 230, w: 960, h: 1480 }, t, msgs, { level });
    // keyboard glow below
    ctx.fillStyle = 'rgba(40,48,70,0.9)'; ctx.fillRect(0, 1760, 1080, 160);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.vignette(ctx, 0.5);
  }

  function draw(ctx, t) {
    const sh = shots(t);
    switch (sh.name) {
      case 'mirror': drawMirror(ctx, t); break;
      case 'bedWide': drawBedWide(ctx, t); break;
      case 'screen': drawScreen(ctx, t); break;
      case 'bedCU': drawBedCU(ctx, t, 1.0, 1.04, sh.t0, sh.t1); break;
      case 'bedCU2': drawBedCU(ctx, t, 1.0, 1.14, sh.t0, sc.end + 1); break;
      default: break;
    }
  }

  // the chat screen already shows the words being typed, so hide subtitles there
  const subs = (t) => shots(t).name !== 'screen';
  return { id: 'mask', start: sc.start, end: sc.end, draw, subs, mirrorRect, actors: { real, refl, bed } };
};
