'use strict';
// Scene 1 — The Table. Family dinner; Maya tells the truth and the room closes.

const S = require('../lib/stage');
const sets = require('../lib/sets');
const { drawBack } = require('../lib/character');
const { clamp, smooth, lerp } = require('../lib/util');

module.exports = function table(env) {
  const { L, W: Wd, scene } = env;
  const sc = scene('table');
  const maya = env.actor('maya', 'dinner', { blinkMean: 3.0 });
  const mom = env.actor('mom', null, { talk: 1.2 });
  const dad = env.actor('dad', null, { talk: 0.7, idle: 0.6, blinkMean: 4.2 });
  const jordan = env.actor('jordan', null, { idle: 1.2 });

  const l = (id) => L(id);
  const w = (id, i) => Wd(id, i);

  // ------------------------------------------------------------ MAYA
  maya.expr(0, 'hollow', 0.01).look(0, { yaw: -0.05, pitch: 0.3, gazeY: 0.55 }, 0.01);
  maya.look(w('L1', 7) - 0.2, { yaw: -0.2, pitch: 0.15, gazeX: -0.3, gazeY: 0.15 }, 0.4);   // glance at "no drama"
  maya.look(l('L1').end + 0.1, { yaw: -0.08, pitch: 0.3, gazeX: 0, gazeY: 0.5 }, 0.5);
  maya.look(l('L2').start + 0.25, { yaw: -0.24, pitch: 0.02, gazeX: -0.35, gazeY: 0.05 }, 0.35); // Mom says her name
  maya.expr(l('L2').end - 0.1, 'polite', 0.45);
  maya.set('pitch', l('L3').start, 0.06, 0.15).set('pitch', l('L3').start + 0.2, 0, 0.25);    // tiny nod
  const p0 = l('L4').end + 0.15;                                                              // the long beat
  maya.expr(p0 + 0.3, 'fading', 0.8).expr(p0 + 1.1, 'hollow', 0.6);
  maya.look(p0 + 0.5, { yaw: -0.05, pitch: 0.3, gazeX: 0, gazeY: 0.55 }, 0.7);
  maya.set('press', p0 + 1.25, 0.5, 0.12).set('press', p0 + 1.45, 0, 0.2);                   // swallow
  maya.set('headY', p0 + 1.25, 0.012, 0.12).set('headY', p0 + 1.45, 0, 0.2);
  maya.set('shoulderUp', p0 + 1.5, 0.25, 0.6).set('shoulderUp', l('L5').start + 0.3, 0, 0.8); // breath in
  maya.set('breathDeep', p0 + 1.4, 0.5, 0.5).set('breathDeep', l('L5').end, 0, 1);
  maya.expr(l('L5').start - 0.15, 'vulnerable', 0.5);
  maya.look(l('L5').start + 0.1, { yaw: -0.18, pitch: 0.12, gazeX: -0.25, gazeY: 0.2 }, 0.5);
  maya.look(w('L5', 4) - 0.1, { yaw: -0.25, pitch: 0.0, gazeX: -0.35, gazeY: 0.0 }, 0.35);   // "I'm not okay" — meets Mom's eyes
  maya.expr(l('L6').start + 0.3, 'earnest', 0.6).set('wet', l('L6').start, 0.3, 2);
  maya.look(w('L6', 9) - 0.15, { yaw: -0.22, pitch: -0.08, gazeX: -0.35, gazeY: -0.05 }, 0.3); // "I'm autistic" — chin up
  maya.look(w('L6', 11), { yaw: -0.05, pitch: -0.02, gazeX: -0.05 }, 0.4);                   // to Dad
  maya.set('browKnit', w('L6', 16), 0.25, 0.4).set('browKnit', l('L6').end, 0, 0.6);
  maya.set('yaw', w('L6', 16), 0.06, 0.25).set('yaw', w('L6', 16) + 0.3, -0.06, 0.25).set('yaw', w('L6', 16) + 0.6, 0, 0.3);
  maya.look(l('L6').end - 0.4, { yaw: -0.24, gazeX: -0.35 }, 0.4);
  maya.expr(w('L7', 2), 'stung', 0.25).blinkAt(w('L7', 2) + 0.05);
  maya.expr(w('L7', 7), 'hurt', 0.8);
  maya.expr(l('L8').start, 'earnest', 0.3).set('wet', l('L8').start, 0.45, 1);
  maya.set('headY', l('L8').start, 0.025, 0.4).set('headY', l('L8').end + 0.4, 0, 0.6);
  maya.arm('R', 0, { hx: 0.6, hy: 1.9, pose: 'relaxed', front: false, table: true, ex: 0.6, ey: 0.44, ew: 1 }, 0.01);
  maya.arm('R', w('L8', 9) - 0.35, { hx: 0.02, hy: 0.6, ex: 0.62, ey: 0.88, ew: 1, pose: 'open', front: true, wrist: 0.1, flip: 1 }, 0.45);   // hand to chest
  maya.arm('R', l('L8').end + 0.7, { hx: 0.6, hy: 1.9, pose: 'relaxed', front: false, table: true, ex: 0.6, ey: 0.44, ew: 1 }, 0.6);
  maya.look(l('L9').start - 0.2, { yaw: -0.05, gazeX: -0.05 }, 0.3);
  maya.expr(l('L9').end, 'stung', 0.2);
  maya.expr(l('L10').end + 0.2, 'hurt', 0.8).set('wet', l('L10').end, 0.6, 2);
  maya.blinkAt(w('L11', 9)).set('headY', w('L11', 9), -0.02, 0.12).set('headY', w('L11', 9) + 0.3, 0, 0.5); // flinch at "something heavy"
  maya.look(w('L11', 14), { pitch: 0.25, gazeY: 0.45 }, 0.6);
  maya.look(l('L12').start + 0.3, { yaw: -0.24, pitch: 0.05, gazeX: -0.3, gazeY: 0.1 }, 0.4);
  maya.set('yaw', l('L12').end - 0.6, -0.3, 0.25).set('yaw', l('L12').end - 0.3, -0.2, 0.3);  // a small disbelieving shake
  maya.look(l('L13').start + 0.1, { yaw: 0.3, pitch: 0.05, gazeX: 0.4, gazeY: 0.1 }, 0.35);
  maya.expr(l('L13').start + 0.2, 'stung', 0.3);
  const q = l('L13').end;                                                                     // the silence
  maya.expr(q + 0.4, 'hurt', 0.6);
  maya.look(q + 0.6, { yaw: -0.25, gazeX: -0.35, gazeY: 0.05 }, 0.45);
  maya.look(q + 1.4, { yaw: -0.05, gazeX: 0.0 }, 0.4);
  maya.look(q + 2.1, { yaw: 0.22, gazeX: 0.3 }, 0.4);
  maya.look(q + 2.8, { yaw: 0.0, pitch: 0.2, gazeX: 0, gazeY: 0.45 }, 0.8);
  for (let k = 0; k < 6; k++) maya.set('press', q + 1.0 + k * 0.17, k % 2 ? 0.2 : 0.55, 0.08);  // chin tremble
  maya.set('press', q + 2.1, 0.45, 0.3);
  maya.set('pitch', q + 3.0, 0.32, 0.4).set('pitch', q + 3.5, 0.18, 0.4);                    // slow nod
  maya.set('wet', q + 1.0, 0.9, 2.0).tear(-1, q + 3.1, 1.7);

  // ------------------------------------------------------------ MOM
  mom.expr(0, 'bright', 0.01).look(0, { yaw: 0.38, pitch: 0.05, gazeX: 0.3 }, 0.01);
  mom.arm('R', 0, { hx: 0.32, hy: 0.92, pose: 'hold', front: true, table: true, ex: 0.6, ey: 0.44, ew: 1, prop: 'fork', propAngle: -0.3 }, 0.01);
  mom.arm('L', 0, { hx: -0.32, hy: 0.95, pose: 'relaxed', front: true, table: true, ex: -0.6, ey: 0.44, ew: 1 }, 0.01);
  mom.look(w('L1', 4), { yaw: 0.55, gazeX: 0.5 }, 0.3);                                       // "No phones" — at Jordan
  mom.set('browOut', w('L1', 4), 0.25, 0.2).set('browOut', w('L1', 7) + 0.2, 0, 0.4);
  mom.look(l('L1').end + 0.2, { yaw: 0.3, pitch: 0.1, gazeX: 0.3, gazeY: 0.25 }, 0.4);
  mom.set('roll', l('L2').start, 0.08, 0.4).set('roll', l('L2').end + 0.3, 0, 0.5);
  mom.expr(l('L4').start - 0.1, 'bright', 0.2);
  mom.set('pitch', l('L4').start + 0.1, 0.18, 0.15).set('pitch', l('L4').start + 0.3, 0.02, 0.2).set('pitch', l('L4').start + 0.5, 0.15, 0.15).set('pitch', l('L4').start + 0.7, 0.05, 0.2);
  mom.look(l('L4').end + 0.15, { yaw: 0.1, pitch: 0.35, gazeX: 0.1, gazeY: 0.5 }, 0.4);        // back to her plate
  mom.look(w('L5', 4), { yaw: 0.3, pitch: 0.1, gazeX: 0.3, gazeY: 0.25 }, 0.35);
  mom.expr(w('L5', 4) + 0.1, 'brittle', 0.6);
  mom.look(w('L6', 9) + 0.2, { yaw: 0.18, gazeX: 0.55 }, 0.25);                                // eyes flick to Dad
  mom.blinkAt(w('L6', 10)).blinkAt(w('L6', 10) + 0.25);
  mom.look(w('L6', 12), { yaw: 0.3, gazeX: 0.3 }, 0.3);
  mom.expr(l('L7').start - 0.1, 'placating', 0.4);
  mom.set('roll', l('L7').start, 0.1, 0.5).set('roll', l('L7').end, 0.02, 0.6);
  mom.arm('L', w('L7', 2), { hx: 0.2, hy: 0.85, pose: 'open', front: true, table: true, ex: -0.6, ey: 0.44, ew: 1, wrist: 0.3 }, 0.5);   // reaching pat
  mom.arm('L', l('L7').end + 0.2, { hx: -0.32, hy: 0.95, pose: 'relaxed', front: true, table: true, ex: -0.6, ey: 0.44, ew: 1 }, 0.6);
  mom.look(w('L7', 7), { pitch: 0.3, gazeY: 0.5, yaw: 0.15 }, 0.4);                           // "You're just tired" — already looking away
  mom.expr(l('L8').start + 0.6, 'tight', 0.6);
  mom.look(l('L9').start - 0.3, { yaw: 0.2, gazeX: 0.5, pitch: 0.05, gazeY: 0.1 }, 0.3);
  mom.look(l('L11').start + 0.5, { yaw: 0.15, pitch: 0.35, gazeX: 0.2, gazeY: 0.5 }, 0.5);
  mom.expr(l('L12').start - 0.2, 'placating', 0.3);
  mom.look(l('L12').start, { yaw: 0.25, pitch: 0.05, gazeX: 0.45, gazeY: 0.05 }, 0.3);
  mom.look(w('L12', 4), { yaw: 0.32, gazeX: 0.3, gazeY: 0.2 }, 0.3);
  mom.expr(w('L12', 6), 'tight', 0.4);
  mom.look(l('L13').start + 0.1, { yaw: 0.55, gazeX: 0.5, pitch: 0.02, gazeY: 0.0 }, 0.3);
  mom.expr(l('L13').start + 0.15, 'stung', 0.3);
  mom.expr(l('L13').end + 0.6, 'tight', 0.6).look(l('L13').end + 0.6, { yaw: 0.05, pitch: 0.38, gazeX: 0, gazeY: 0.6 }, 0.6);

  // ------------------------------------------------------------ DAD
  dad.expr(0, 'closed', 0.01).look(0, { yaw: 0.05, pitch: 0.45, gazeY: 0.65 }, 0.01);
  const cut = (t0, t1, side = 'R') => {
    for (let t = t0; t < t1; t += 0.55) {
      dad.arm(side, t, { hx: 0.26, hy: 0.9, pose: 'hold', front: true, table: true, ex: 0.6, ey: 0.44, ew: 1, prop: 'fork', propAngle: -1.0 }, 0.25);
      dad.arm(side, t + 0.27, { hx: 0.34, hy: 0.86, pose: 'hold', front: true, table: true, ex: 0.6, ey: 0.44, ew: 1, prop: 'fork', propAngle: -1.0 }, 0.25);
    }
  };
  dad.arm('R', 0, { hx: 0.3, hy: 0.88, pose: 'hold', front: true, table: true, ex: 0.6, ey: 0.44, ew: 1, prop: 'fork', propAngle: -1.0 }, 0.01);
  dad.arm('L', 0, { hx: -0.3, hy: 0.95, pose: 'relaxed', front: true, table: true, ex: -0.6, ey: 0.44, ew: 1 }, 0.01);
  cut(0.6, l('L5').start);
  dad.set('pitch', l('L4').end - 0.2, 0.55, 0.15).set('pitch', l('L4').end, 0.45, 0.2);        // "mm" nod
  dad.look(w('L5', 4), { gazeY: 0.15, gazeX: 0.2 }, 0.3);                                       // eyes lift, head doesn't
  dad.look(w('L6', 9) + 0.3, { yaw: -0.25, gazeX: -0.4 }, 0.35);                               // glance at Mom
  dad.look(w('L6', 13), { yaw: 0.05, gazeX: 0.0, gazeY: 0.6 }, 0.4);
  cut(l('L7').start, l('L8').start);
  dad.arm('R', l('L8').end + 0.1, { hx: 0.3, hy: 0.98, pose: 'relaxed', front: true, table: true, ex: 0.6, ey: 0.44, ew: 1 }, 0.4);    // fork down
  dad.slowBlink(l('L8').end + 0.35, 0.45).set('shoulderUp', l('L8').end + 0.3, 0.25, 0.4).set('shoulderUp', l('L9').start - 0.1, -0.15, 0.6);
  dad.expr(l('L9').start - 0.3, 'weary', 0.4);
  dad.set('yaw', l('L9').start + 0.1, -0.08, 0.25).set('yaw', l('L9').start + 0.4, 0.08, 0.25).set('yaw', l('L9').end, 0.0, 0.3);
  dad.look(l('L10').start + 0.4, { gazeY: 0.1, gazeX: 0.2 }, 0.3);
  dad.expr(l('L11').start, 'irritated', 0.3);
  dad.look(l('L11').start + 0.1, { yaw: 0.15, pitch: 0.1, gazeX: 0.25, gazeY: 0.15 }, 0.4);
  dad.arm('L', w('L11', 8), { hx: -0.12, hy: 0.62, pose: 'open', front: true, wrist: 0.5 }, 0.35);   // "something heavy"
  dad.arm('L', w('L11', 13), { hx: -0.3, hy: 0.95, pose: 'relaxed', front: true, table: true, ex: -0.6, ey: 0.44, ew: 1 }, 0.5);
  dad.look(w('L11', 14), { yaw: -0.15, pitch: 0.35, gazeX: -0.1, gazeY: 0.45 }, 0.5);          // "Can we have one meal in peace?"
  dad.set('yaw', l('L11').end - 0.5, -0.25, 0.25).set('yaw', l('L11').end - 0.2, -0.1, 0.3);
  dad.arm('R', l('L12').start + 0.5, { hx: 0.3, hy: 0.88, pose: 'hold', front: true, table: true, ex: 0.6, ey: 0.44, ew: 1, prop: 'fork', propAngle: -1.0 }, 0.4);
  dad.look(l('L13').start + 0.15, { yaw: 0.35, gazeX: 0.4, pitch: 0.2 }, 0.3);
  dad.expr(l('L13').start + 0.2, 'irritated', 0.3);
  dad.look(l('L13').end + 0.4, { yaw: 0.0, pitch: 0.45, gazeX: 0, gazeY: 0.6 }, 0.5);
  dad.expr(l('L13').end + 0.4, 'closed', 0.6);
  cut(l('L13').end + 0.6, sc.end + 4);

  // ------------------------------------------------------------ JORDAN
  jordan.expr(0, 'neutral', 0.01).look(0, { yaw: -0.05, pitch: 0.55, gazeY: 0.8 }, 0.01);
  jordan.arm('L', 0, { hx: -0.1, hy: 1.05, pose: 'hold', front: true, table: true, ex: -0.6, ey: 0.44, ew: 1, prop: 'phone', screen: '#9fd0ff', propAngle: 1.2 }, 0.01);
  jordan.arm('R', 0, { hx: 0.3, hy: 0.95, pose: 'relaxed', front: true, table: true, ex: 0.6, ey: 0.44, ew: 1 }, 0.01);
  jordan.look(w('L1', 5), { yaw: -0.4, pitch: 0.05, gazeX: -0.5, gazeY: 0 }, 0.2);              // caught
  jordan.expr(w('L1', 5) + 0.1, 'awkward', 0.3);
  jordan.arm('L', w('L1', 6), { hx: -0.3, hy: 1.1, pose: 'relaxed', front: true, table: true, ex: -0.6, ey: 0.44, ew: 1 }, 0.4);         // phone away
  jordan.look(l('L1').end + 0.3, { yaw: -0.05, pitch: 0.4, gazeX: 0, gazeY: 0.5 }, 0.4);
  jordan.look(w('L5', 4), { yaw: -0.18, pitch: 0.1, gazeX: -0.25, gazeY: 0.3 }, 0.3);
  jordan.expr(w('L5', 4) + 0.1, 'attentive', 0.4);
  jordan.expr(l('L6').start + 1, 'guilty', 1.0).set('shoulderUp', l('L7').start, 0.3, 1.2);
  jordan.look(l('L7').start + 0.1, { yaw: -0.45, gazeX: -0.45, gazeY: 0.1 }, 0.3);
  jordan.look(l('L8').start + 0.2, { yaw: -0.18, gazeX: -0.25, gazeY: 0.3 }, 0.3);
  jordan.look(l('L9').start, { yaw: -0.3, gazeX: -0.35 }, 0.25);
  jordan.look(l('L11').start + 1.5, { yaw: -0.05, pitch: 0.45, gazeX: 0, gazeY: 0.6 }, 0.6);
  jordan.expr(l('L13').start - 0.3, 'guilty', 0.3);
  jordan.look(l('L13').start - 0.2, { pitch: 0.4, gazeY: 0.55 }, 0.3);
  jordan.look(l('L13').end - 0.4, { yaw: -0.15, gazeX: -0.35, gazeY: 0.25 }, 0.15);             // one tiny glance at Maya
  jordan.look(l('L13').end + 0.1, { yaw: 0.35, pitch: 0.3, gazeX: 0.4, gazeY: 0.4 }, 0.4);      // away
  jordan.set('headY', l('L13').end + 0.8, -0.03, 0.8);

  // ------------------------------------------------------------ shots
  const shots = env.cuts([
    [sc.start, 'wide'],
    [l('L2').start - 0.1, 'mom'],
    [l('L3').start - 0.35, 'maya'],
    [l('L4').start - 0.05, 'mom'],
    [l('L4').end + 0.25, 'maya'],
    [l('L5').end + 0.15, 'wide'],
    [l('L6').start + 2.4, 'maya'],
    [l('L7').start - 0.1, 'mom'],
    [l('L8').start - 0.1, 'maya'],
    [l('L8').end + 0.2, 'dad'],
    [l('L10').start - 0.25, 'maya'],
    [l('L11').start - 0.1, 'dad'],
    [l('L12').start - 0.1, 'mom'],
    [l('L13').start - 0.45, 'jordan'],
    [l('L13').end + 0.35, 'wide'],
    [l('L13').end + 1.6, 'mayaFinal'],
  ]);

  // ------------------------------------------------------------ painting
  const wideBg = () => S.cachedBg('dining-wide', (c, W, H) => {
    sets.diningWall(c, W, H, { window: { x: 40, y: 430, w: 300, h: 420 }, photo: { x: 760, y: 470, w: 250, h: 190 }, clock: { x: 900, y: 300, r: 52 }, wainY: 1180 });
  });
  const momBg = () => S.cachedBg('dining-mom', (c, W, H) => {
    sets.diningWall(c, W, H, { window: { x: 120, y: 300, w: 520, h: 700 }, wainY: 1350, lampX: 900, lampY: 200 });
  }, 14);
  const dadBg = () => S.cachedBg('dining-dad', (c, W, H) => {
    sets.diningWall(c, W, H, { photo: { x: 620, y: 420, w: 360, h: 270 }, clock: { x: 200, y: 330, r: 70 }, wainY: 1350, lampX: 540, lampY: 120 });
  }, 12);
  const jordanBg = () => S.cachedBg('dining-jordan', (c, W, H) => {
    sets.diningWall(c, W, H, { photo: { x: 80, y: 380, w: 380, h: 280 }, wainY: 1350, lampX: 200, lampY: 150, sconce: [{ x: 900, y: 600 }] });
  }, 14);
  const mayaBg = () => S.cachedBg('dining-maya', (c, W, H) => {
    sets.diningWall(c, W, H, { door: { x: 640, y: 420, w: 300, h: 1000 }, hutch: { x: 40, y: 640, w: 420, h: 700 }, wainY: 1380, lampX: 540, lampY: 60, sconce: [{ x: 560, y: 520 }] });
  }, 16);

  const warmKey = (y0, y1) => ({ y0, y1, top: [255, 214, 160], topA: 0.16, bottom: [30, 12, 6], bottomA: 0.35 });
  const lampRim = { color: [255, 196, 120], a: 0.55, side: 1 };

  function drawWide(ctx, t, cam) {
    S.applyCam(ctx, cam);
    ctx.drawImage(wideBg(), 0, 0);
    sets.clockHands(ctx, { x: 900, y: 300, r: 52 }, t);
    sets.pendantLamp(ctx, 540, 420, 0.95, 1);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const look = { key: warmKey(700, 1300), light: { x: 0.2, y: -1 }, parts: 'base' };
    const pDad = { ...dad.pose(t), x: 540, y: 1150, scale: 210 };
    const pMom = { ...mom.pose(t), x: 228, y: 1188, scale: 205, bodyYaw: 0.35 };
    const pJor = { ...jordan.pose(t), x: 852, y: 1192, scale: 198, bodyYaw: -0.3 };
    S.drawLit(ctx, env.cast.dad, pDad, look, cam);
    S.drawLit(ctx, env.cast.mom, pMom, { ...look, rim: { ...lampRim, side: 1 } }, cam);
    S.drawLit(ctx, env.cast.jordan, pJor, { ...look, rim: { ...lampRim, side: -1 }, glow: jordanGlow(t, 852, 1192, 198) }, cam);
    S.applyCam(ctx, cam);
    sets.diningTable(ctx, 1080, 1920, 1262);
    sets.servingDish(ctx, 540, 1350, 0.9);
    sets.plate(ctx, 228, 1330, 120, true, 1);
    sets.plate(ctx, 540, 1300, 105, true, 2);
    sets.plate(ctx, 852, 1335, 115, true, 3);
    sets.glass(ctx, 380, 1310, 1); sets.glass(ctx, 700, 1300, 0.95);
    sets.candle(ctx, 420, 1400, t, 0.9); sets.candle(ctx, 660, 1400, t + 3, 0.9);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const front = { light: { x: 0.2, y: -1 }, parts: 'front', key: warmKey(1200, 1700) };
    S.drawLit(ctx, env.cast.dad, pDad, front, cam);
    S.drawLit(ctx, env.cast.mom, pMom, front, cam);
    S.drawLit(ctx, env.cast.jordan, pJor, front, cam);
    // Maya, back to camera, in the foreground
    const pm = maya.pose(t);
    const L2 = S.layer(); const lc = L2.getContext('2d'); S.applyCam(lc, cam);
    drawBack(lc, env.castFor('maya', 'dinner'), { ...pm, yaw: -pm.yaw * 0.8 + 0.1, x: 760, y: 1985, scale: 400 });
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.filter = 'blur(3px)'; ctx.drawImage(L2, 0, 0); ctx.restore();
    S.release(L2);
  }
  function jordanGlow(t, x, y, s) {
    // phone glow on his face while he's hiding it under the table
    const on = 1 - smooth((t - (w('L1', 6) + 0.2)) / 0.5);
    if (on <= 0) return null;
    return { x, y: y - 0.3 * s, r: 1.1 * s, color: [140, 190, 255], a: 0.18 * on };
  }

  function closeUp(ctx, t, who, bg, opts) {
    const a = who === 'maya' ? maya : who === 'mom' ? mom : who === 'dad' ? dad : jordan;
    const A = who === 'maya' ? env.castFor('maya', 'dinner') : env.cast[who];
    const cam = opts.cam || null;
    S.applyCam(ctx, cam);
    ctx.drawImage(bg(), 0, 0);
    // soft bokeh from candles / lamp
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (const [bx, by, br] of opts.bokeh || []) S.glowDisc(ctx, bx, by, br, [255, 190, 120], 0.25);
    ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const P = { ...a.pose(t), x: opts.x, y: opts.y, scale: opts.scale };
    for (const k of ['armL', 'armR']) {
      if (P[k] && P[k].table) P[k] = { ...P[k], front: false, hx: (k === 'armL' ? -1 : 1) * 0.62, hy: 1.9, prop: null, ew: 0 };
    }
    S.drawLit(ctx, A, P, { key: warmKey(opts.y - opts.scale * 1.4, opts.y + opts.scale * 0.8), light: opts.light || { x: -0.5, y: -0.9 }, rim: opts.rim, glow: opts.glow }, cam);
    // table edge foreground for seated close-ups
    S.applyCam(ctx, cam);
    if (opts.tableY) {
      ctx.fillStyle = sets.grad(ctx, 0, opts.tableY, 0, 1920, [[0, [230, 214, 188]], [1, [120, 100, 80]]]);
      ctx.fillRect(0, opts.tableY, 1080, 1920 - opts.tableY);
      ctx.filter = 'none';
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  function draw(ctx, t) {
    const sh = shots(t);
    const k = t - sh.t0;
    switch (sh.name) {
      case 'wide': {
        const cam = S.push(t, sh.t0, sh.t1, 1.0, 1.035, 540, 960, 540, 1000);
        drawWide(ctx, t, cam);
        break;
      }
      case 'mom':
        closeUp(ctx, t, 'mom', momBg, { x: 480, y: 1290, scale: 500, rim: { ...lampRim, side: 1 }, bokeh: [[900, 1500, 90], [760, 1620, 60]], tableY: 1760, cam: S.push(t, sh.t0, sh.t1, 1.0, 1.03, 480, 900) });
        break;
      case 'dad':
        closeUp(ctx, t, 'dad', dadBg, { x: 540, y: 1300, scale: 500, rim: { ...lampRim, side: -1 }, bokeh: [[180, 1540, 80]], tableY: 1770, cam: S.push(t, sh.t0, sh.t1, 1.0, 1.04, 540, 900) });
        break;
      case 'jordan':
        closeUp(ctx, t, 'jordan', jordanBg, { x: 600, y: 1300, scale: 490, rim: { ...lampRim, side: -1 }, bokeh: [[150, 1500, 90]], tableY: 1770, cam: S.push(t, sh.t0, sh.t1, 1.0, 1.05, 600, 900) });
        break;
      case 'maya':
      case 'mayaFinal': {
        const z1 = sh.name === 'mayaFinal' ? 1.16 : 1.04;
        closeUp(ctx, t, 'maya', mayaBg, { x: 580, y: 1290, scale: 510, rim: { ...lampRim, side: 1 }, bokeh: [[160, 1480, 100], [330, 1640, 60]], tableY: 1790, cam: S.push(t, sh.t0, sh.t1, 1.0, z1, 580, 880, 580, 860) });
        break;
      }
      default: break;
    }
    void k;
    S.vignette(ctx, 0.5);
  }

  return { id: 'table', start: sc.start, end: sc.end, draw, actors: { maya, mom, dad, jordan } };
};
