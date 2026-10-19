'use strict';
// Scene 4 — the phone call. A boundary, held with love; then the AI.

const S = require('../lib/stage');
const D = require('../lib/sets_day');
const N = require('../lib/sets_night');
const { roundRect } = require('../lib/body');
const { clamp, smooth, lerp, fbm, easeInOut } = require('../lib/util');

module.exports = function call(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('call');
  const l = (id) => L(id);
  const A = env.castFor('maya', 'night');
  const maya = env.actor('maya', 'night', { seed: 707, blinkMean: 3.0 });
  const mom = env.actor('mom', null, { seed: 708, talk: 1.1 });
  const ai = env.actor('ai', null);
  const t31 = l('L31'), t32 = l('L32'), t33 = l('L33'), t34 = l('L34'), t35 = l('L35'), t36 = l('L36'), t37 = l('L37'), t38 = l('L38'), t39 = l('L39');
  const s0 = sc.start;
  const tAnswer = t31.start - 0.9;
  const tHang = t36.end + 0.5;

  const phoneEarR = { hx: 0.4, hy: -0.4, ex: 0.6, ey: 0.66, ew: 1, pose: 'hold', front: true, prop: 'phone', propAngle: 0.1, wrist: 0.15, flip: 1 };
  const phoneLow = { hx: 0.16, hy: 0.98, ex: 0.62, ey: 0.8, ew: 1, pose: 'hold', front: true, prop: 'phone', propAngle: 1.25, screen: '#9fc4ef' };
  const rest = (s) => ({ hx: s * 0.62, hy: 1.9, pose: 'relaxed', front: false });

  // ------------------------------------------------------------ Maya
  maya.expr(0, 'anxious', 0.01).look(0, { pitch: 0.3, gazeY: 0.6, yaw: 0.05 }, 0.01);
  maya.arm('R', 0, phoneLow, 0.01).arm('L', 0, rest(-1), 0.01);
  maya.set('shoulderUp', s0 + 0.8, 0.35, 0.5).set('breathDeep', s0 + 0.8, 0.6, 0.5).set('shoulderUp', tAnswer, 0.1, 0.6);
  maya.set('press', s0 + 1.3, 0.5, 0.12).set('press', s0 + 1.5, 0, 0.2);                    // swallow
  maya.arm('R', tAnswer, phoneEarR, 0.6);
  maya.look(tAnswer + 0.2, { pitch: 0.12, gazeY: 0.25, yaw: -0.1, gazeX: -0.2 }, 0.5);
  maya.slowBlink(Wd('L31', 10), 0.3).set('press', Wd('L31', 10), 0.45, 0.3).set('press', t31.end + 0.4, 0.1, 0.5);
  // trembling hand, steady voice
  for (let t = t32.start - 0.3, k = 0; t < t34.end; t += 0.11, k++) maya.arm('R', t, { ...phoneEarR, hx: phoneEarR.hx + (k % 2 ? 0.008 : -0.008), hy: phoneEarR.hy + (k % 3 ? 0.006 : -0.006) }, 0.1, 'linear');
  maya.arm('R', t34.end + 0.1, phoneEarR, 0.3);
  maya.expr(t32.start, 'tender', 0.4).look(t32.start, { pitch: 0.18, gazeY: 0.35 }, 0.5);
  maya.expr(Wd('L32', 4), 'resolved', 0.6).look(Wd('L32', 4), { pitch: 0.02, gazeY: 0.05, gazeX: -0.1 }, 0.5);
  maya.blinkAt(Wd('L33', 2)).set('headY', Wd('L33', 2), -0.015, 0.1).set('headY', Wd('L33', 2) + 0.25, 0, 0.3);   // flinch at "dramatic"
  maya.expr(Wd('L33', 3), 'hurt', 0.4).set('lid', t33.end - 0.2, 0.8, 0.4).set('breathDeep', t33.end, 0.7, 0.6);
  maya.set('lid', t34.start - 0.3, 0, 0.4).expr(t34.start - 0.3, 'resolved', 0.5);
  maya.look(t34.start, { pitch: 0.05, gazeY: 0.0, gazeX: -0.1 }, 0.5).set('sacAmp', t34.start, 0.3, 0.3);
  maya.expr(t34.end + 0.6, 'vulnerable', 0.8).set('sacAmp', t34.end + 0.4, 1.2, 0.3).set('press', t34.end + 0.6, 0.4, 0.4);
  maya.expr(Wd('L35', 3), 'tender', 0.8).set('press', t35.start, 0, 0.3).set('wet', t35.start, 0.7, 1.4);
  maya.tear(-1, t36.start + 0.6, 1.8);
  maya.arm('R', tHang, phoneLow, 1.0);                                                       // lowers the phone
  maya.arm('L', tHang + 0.7, { hx: -0.04, hy: -0.4, ex: -0.5, ey: 0.55, ew: 1, pose: 'open', front: true, wrist: -0.25 }, 0.6);   // hand over her mouth
  maya.expr(tHang + 0.5, 'crying', 1.0).set('breathFast', tHang + 0.4, 1.2, 0.6).set('breathFast', t37.start, 0.3, 1.5);
  maya.arm('L', t37.start - 0.4, rest(-1), 0.6);
  maya.look(t37.start - 0.3, { pitch: 0.28, gazeY: 0.55, yaw: 0.05 }, 0.5);
  maya.expr(t37.start, 'relief', 0.5).expr(Wd('L37', 3), 'crying', 0.6);
  maya.expr(t38.start + 1, 'vulnerable', 1.0).set('breathFast', t38.start, 0, 1.5);
  maya.set('pitch', Wd('L38', 14), 0.4, 0.3).set('pitch', Wd('L38', 14) + 0.35, 0.22, 0.4);  // a nod
  maya.tear(1, Wd('L38', 15), 2.0);
  maya.expr(t39.start + 0.6, 'relief', 1.2).set('lid', Wd('L39', 6), 0.85, 0.8).set('breathDeep', Wd('L39', 6), 0.9, 1);
  maya.set('lid', t39.end + 0.4, 0.1, 1.0).look(t39.end + 0.4, { pitch: -0.02, gazeY: -0.1 }, 1.2);

  // ------------------------------------------------------------ Mom
  mom.expr(0, 'tight', 0.01).look(0, { yaw: -0.15, pitch: 0.1, gazeX: -0.2, gazeY: 0.15 }, 0.01);
  mom.arm('L', 0, { hx: -0.4, hy: -0.4, ex: -0.6, ey: 0.66, ew: 1, pose: 'hold', front: true, prop: 'phone', propAngle: 0.1, wrist: -0.15 }, 0.01);
  mom.arm('R', 0, rest(1), 0.01);
  mom.expr(t32.start + 0.6, 'brittle', 0.5).set('press', t32.end - 0.5, 0.5, 0.4);
  mom.look(Wd('L32', 6), { gazeX: -0.5, yaw: -0.3 }, 0.3);                                 // looks away
  mom.expr(t33.start - 0.1, 'exasperated', 0.3);
  mom.look(t33.start, { gazeY: -0.6, gazeX: 0.2 }, 0.25).look(t33.start + 0.35, { gazeY: 0.1, gazeX: -0.3 }, 0.3);   // eye roll
  mom.set('yaw', Wd('L33', 3), -0.3, 0.25).set('yaw', Wd('L33', 3) + 0.3, 0.0, 0.25).set('yaw', Wd('L33', 3) + 0.6, -0.15, 0.3);
  mom.expr(Wd('L34', 8), 'stung', 0.4).set('wet', Wd('L34', 10), 0.4, 1.0);
  mom.look(Wd('L34', 14), { pitch: 0.35, gazeY: 0.55, yaw: -0.2 }, 0.8);
  for (let k = 0; k < 5; k++) mom.set('press', t34.end + 0.2 + k * 0.18, k % 2 ? 0.15 : 0.5, 0.09);   // lip trembles
  mom.expr(t34.end + 0.3, 'cracking', 1.0).set('wet', t34.end + 0.3, 0.75, 1.4);
  mom.arm('R', t34.end + 0.6, { hx: 0.12, hy: -1.06, ex: 0.66, ey: 0.2, ew: 1, pose: 'open', front: true, wrist: 0.2, flip: 1 }, 0.7);   // hand to her forehead
  mom.arm('R', t35.start + 0.2, rest(1), 0.8);
  mom.look(t35.start, { pitch: 0.2, gazeY: 0.3, yaw: -0.1 }, 0.6);
  mom.slowBlink(Wd('L36', 4), 0.6).tear(1, Wd('L36', 5), 1.8);
  mom.set('pitch', Wd('L36', 6), 0.3, 0.4).set('pitch', Wd('L36', 6) + 0.4, 0.18, 0.4);    // small nod
  mom.arm('L', tHang - 0.2, { hx: -0.2, hy: 0.98, ex: -0.62, ey: 0.8, ew: 1, pose: 'hold', front: true, prop: 'phone', propAngle: 1.2 }, 1.0);

  const shots = env.cuts([
    [s0, 'maya'],
    [s0 + 1.0, 'phone'],
    [s0 + 2.0, 'maya'],
    [t31.start - 0.25, 'split'],
    [tHang + 1.3, 'maya'],
    [t38.start - 0.2, 'screen'],
    [t38.start + 2.6, 'maya'],
  ]);
  const msgs = [
    { from: 'me', text: t37.text, t0: t37.start - 0.3, t1: t37.end },
    { from: 'ai', text: t38.text, t0: t38.start, t1: t38.end },
    { from: 'ai', text: t39.text, t0: t39.start, t1: t39.end },
  ];
  const lampKey = (y0, y1) => ({ y0, y1, top: [255, 210, 160], topA: 0.12, bottom: [20, 10, 20], bottomA: 0.3 });

  function mayaRoom(ctx, cam, blur) {
    S.applyCam(ctx, cam);
    ctx.drawImage(S.cachedBg('living' + blur, (c, W, H) => D.livingRoom(c, W, H), blur), 0, 0);
  }
  function drawMaya(ctx, t, y = 1310, scale = 510, cam = null, glow = 0) {
    const P = S.tuckArms({ ...maya.pose(t), x: 540, y, scale }, 1.6);
    S.drawLit(ctx, A, P, { key: lampKey(y - scale * 1.4, y + scale * 0.6), light: { x: 0.6, y: -0.7 }, rim: { color: [255, 190, 120], a: 0.55, side: 1 }, glow: glow > 0 ? { x: 560, y: y + 300, r: 700, color: [170, 200, 255], a: glow } : null }, cam);
  }
  function drawPhoneInsert(ctx, t) {
    ctx.fillStyle = '#121218'; ctx.fillRect(0, 0, 1080, 1920);
    const buzz = Math.sin(t * 60) * 6 * (Math.sin(t * 9) > 0 ? 1 : 0);
    ctx.save(); ctx.translate(buzz, 0);
    ctx.fillStyle = '#1c1d24'; roundRect(ctx, 190, 240, 700, 1440, 70); ctx.fill();
    ctx.fillStyle = (function () { const g = ctx.createLinearGradient(0, 300, 0, 1600); g.addColorStop(0, '#3a3256'); g.addColorStop(1, '#141420'); return g; })();
    roundRect(ctx, 215, 265, 650, 1390, 56); ctx.fill();
    ctx.fillStyle = '#c28c68'; ctx.beginPath(); ctx.arc(540, 640, 120, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#5b3b2a'; ctx.beginPath(); ctx.arc(540, 610, 120, Math.PI, 0); ctx.fill();
    ctx.textAlign = 'center'; ctx.fillStyle = '#ffffff'; ctx.font = '76px InterSemi'; ctx.fillText('Mom', 540, 860);
    ctx.font = '36px InterMed'; ctx.fillStyle = '#b8b8cc'; ctx.fillText('incoming call…', 540, 920);
    ctx.fillStyle = '#e0544f'; ctx.beginPath(); ctx.arc(390, 1450, 70, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#4fbf6a'; ctx.beginPath(); ctx.arc(690, 1450, 70, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    S.vignette(ctx, 0.5);
  }
  function drawSplit(ctx, t) {
    const close = smooth((t - tHang) / 1.2);
    const half = 960;
    const topOff = -close * half;          // Mom's half slides away when the call ends
    // bottom: Maya
    ctx.save();
    ctx.beginPath(); ctx.rect(0, half + topOff, 1080, 1920); ctx.clip();
    const camB = { x: 540, y: lerp(1300, 960, close), zoom: 1 };
    mayaRoom(ctx, camB, 12);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    drawMaya(ctx, t, lerp(1720, 1330, close), lerp(400, 510, close), null);
    S.vignette(ctx, 0.45);
    ctx.restore();
    // top: Mom
    if (close < 1) {
      ctx.save();
      ctx.translate(0, topOff);
      ctx.beginPath(); ctx.rect(0, 0, 1080, half); ctx.clip();
      ctx.drawImage(S.cachedBg('kitchen', (c, W, H) => D.kitchen(c, W, H), 12), 0, -480);
      const P = { ...mom.pose(t), x: 520, y: 800, scale: 390 };
      const Ly = S.layer(); const lc = Ly.getContext('2d');
      S.drawLit(lc, env.cast.mom, P, { key: lampKey(200, 1000), light: { x: -0.6, y: -0.7 }, rim: { color: [255, 200, 140], a: 0.4, side: -1 } });
      ctx.drawImage(Ly, 0, 0); S.release(Ly);
      ctx.fillStyle = 'rgba(0,0,0,0.25)';
      const g = ctx.createLinearGradient(0, half - 160, 0, half); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.55)');
      ctx.fillStyle = g; ctx.fillRect(0, half - 160, 1080, 160);
      ctx.restore();
      // the divider
      ctx.fillStyle = 'rgba(255,236,210,0.85)'; ctx.fillRect(0, half + topOff - 3, 1080, 6);
    }
  }
  function drawScreen(ctx, t) {
    ctx.fillStyle = '#05060a'; ctx.fillRect(0, 0, 1080, 1920);
    N.chatScreen(ctx, { x: 60, y: 230, w: 960, h: 1480 }, t, msgs, { level: ai.speechAt(t).open });
    S.vignette(ctx, 0.5);
  }

  function draw(ctx, t) {
    const sh = shots(t);
    switch (sh.name) {
      case 'phone': drawPhoneInsert(ctx, t); break;
      case 'split': drawSplit(ctx, t); break;
      case 'screen': drawScreen(ctx, t); break;
      case 'maya': {
        const cam = S.push(t, sh.t0, sh.t1, 1.0, sh.t0 > t37.start ? 1.12 : 1.05, 540, 900);
        mayaRoom(ctx, cam, 14);
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        const level = ai.speechAt(t).open;
        drawMaya(ctx, t, 1310, 510, cam, 0.12 + 0.15 * level);
        S.vignette(ctx, 0.5);
        break;
      }
      default: break;
    }
  }
  const subY = (t) => (shots(t).name === 'split' && t < tHang + 0.6 ? 960 : 1440);
  const subs = (t) => shots(t).name !== 'screen' && shots(t).name !== 'phone';
  return { id: 'call', start: sc.start, end: sc.end, draw, subY, subs, actors: { maya, mom, ai }, shotAt: shots, tHang, msgs, drawPhoneInsert };
};
