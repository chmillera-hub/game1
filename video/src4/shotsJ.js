// ---------- cast ----------
const CAST = {
  jesus: { name: 'Jesus', voice: 'JESUS', seed: 7, skin: '#b07a52', hair: '#3a2416', hairStyle: 'wavy', hairBack: true, beard: 'full', beardCol: '#3a2416', beardLen: .55, eye: '#3a2414', faceW: .98, jaw: 1,
    cloth: { type: 'tunic', color: '#a8261e', stripe: '#e8c040', sleeveLen: 'long', neck: 8 } },
  host: { name: 'Host', voice: 'HOST', seed: 13, skin: '#e0b896', hair: '#2a1a14', hairStyle: 'ponytail', eye: '#3a2a1a', lip: '#c05a5a', lashes: true, faceW: .93, jaw: .88, browW: 3.2, cloth: { type: 'tunic', color: '#1f7a7a', sleeveLen: 'long', neck: 4 } },
  kayla: { name: 'Kayla', voice: 'KAYLA', seed: 19, skin: '#f0caa8', hair: '#e8c878', hairStyle: 'ponytail', eye: '#3a6a8a', lip: '#d0607a', lashes: true, faceW: .9, jaw: .86, chin: .96, browW: 3, cloth: { type: 'tunic', color: '#e87aa8', sleeveLen: 'long', neck: 6 } },
  dana: { name: 'Dana', voice: 'DANA', seed: 29, skin: '#8a5a3c', hair: '#1a1414', hairStyle: 'bun', eye: '#2a1810', lip: '#8a4a40', lashes: true, faceW: .92, jaw: .9, browW: 3.4, cloth: { type: 'tunic', color: '#2a3a5a', sleeveLen: 'long', neck: 4 } },
  priya: { name: 'Priya', voice: 'PRIYA', seed: 31, skin: '#a8724e', hair: '#120c0a', hairStyle: 'wavy', hairBack: true, eye: '#2a1810', lip: '#a04a50', lashes: true, faceW: .92, jaw: .88, browW: 3.4, cloth: { type: 'tunic', color: '#d8a030', sleeveLen: 'long', neck: 6 } },
  marisol: { name: 'Marisol', voice: 'MARISOL', seed: 43, skin: '#c48d68', hair: '#2a1810', hairStyle: 'wavy', hairBack: true, eye: '#3a2414', lip: '#9a4a48', lashes: true, faceW: .93, jaw: .9, browW: 3.4, cloth: { type: 'tunic', color: '#3a5a4a', sleeveLen: 'long', neck: 4 } },
  bartender: { name: 'Bartender', voice: 'BARTENDER', seed: 53, skin: '#e0b090', hair: '#5a3a2a', hairStyle: 'short', mustache: true, beardCol: '#5a3a2a', eye: '#3a4a3a', faceW: 1.06, jaw: 1.08, cloth: { type: 'tunic', color: '#2a2a2e', sleeveLen: 'mid', neck: 4 } },
};
// ---------- helpers ----------
const st_ = id => LINE(id).start, en_ = id => LINE(id).end;
function actor(name, base, keys) { return { C: CAST[name], tr: new Track(Object.assign({}, BASE_STATE, base), keys || []) }; }
function applyCam(c, cam) { c.translate(W / 2, H / 2); c.scale(cam.z, cam.z); c.translate(-cam.x, -cam.y); }
function show(ctx, a, t, light, cam, extra) {
  const st = resolve(a.C, a.tr, t); if (extra) extra(st);
  drawLit(ctx, c => { c.save(); if (cam) applyCam(c, cam); c.globalAlpha = st.alpha; drawChar(c, a.C, st, t); c.restore(); }, light);
  return st;
}
const LIGHT = {
  candle: (x, y, k = 1) => ({ x, y, color: '#ffb35c', str: .26 * k, rad: 560, dark: .32, near: '#fff4e0', amb: '#4a3040', fall: 1000, rim: .4 * k, rimColor: '#ffc880', rimDx: x < 360 ? 6 : -6, rimDy: 2 }),
  bar: (x, y) => ({ x, y, color: '#ffcf8a', str: .22, rad: 700, dark: .25, near: '#fff', amb: '#4a3a40', fall: 1000, rim: .35, rimColor: '#ff9ad0', rimDx: x < 360 ? 6 : -6, rimDy: 0 }),
  moon: (x, y) => ({ x, y, color: '#9ab0e0', str: .15, rad: 700, dark: .5, near: '#e0e8ff', amb: '#202840', fall: 900, rim: .4, rimColor: '#b0c8ff', rimDx: x < 360 ? 6 : -6, rimDy: 0 }),
  dawn: (x, y, k = 1) => ({ x, y, color: '#ffc58a', str: .3 * k, rad: 700, dark: .22, near: '#fff6ea', amb: '#5a4a60', fall: 1000, rim: .5 * k, rimColor: '#ffd79a', rimDx: x < 360 ? 6 : -6, rimDy: 2 }),
};
const SHOTS = [], LABELS = [], SUPPRESS = new Set();
function shot(t0, t1, draw, xin = 0) { SHOTS.push({ t0, t1, draw, xin }); }
const seat = { J: [180, 760], D: [550, 770] };
const lookAt = who => who === 'J' ? [180, 625] : [550, 640];

// ---------- the wine bar ----------
function barBG() {
  return cached('bar', W + 400, H + 400, c => {
    c.translate(200, 200);
    const g = c.createLinearGradient(0, -200, 0, 900); g.addColorStop(0, '#2a1a20'); g.addColorStop(1, '#4a2e28'); c.fillStyle = g; c.fillRect(-200, -200, W + 400, 1300);
    bricks(c, -200, -200, W + 400, 620, '#6a3a2c', 7, 84, 38, '#2a1812'); c.fillStyle = 'rgba(30,15,15,.35)'; c.fillRect(-200, -200, W + 400, 620);
    // wood wainscot
    const wg = c.createLinearGradient(0, 420, 0, 1400); wg.addColorStop(0, '#5a3420'); wg.addColorStop(1, '#1a0e08'); c.fillStyle = wg; c.fillRect(-200, 420, W + 400, 1100);
    for (let x = -200; x < W + 200; x += 90) { c.fillStyle = 'rgba(0,0,0,.2)'; c.fillRect(x, 440, 4, 600); }
    // sign
    c.fillStyle = '#1a1014'; roundRect(c, 150, 60, 420, 110, 18); c.fill();
    c.font = '700 40px Inter'; c.textAlign = 'center'; c.shadowColor = '#ff6ab0'; c.shadowBlur = 20; c.fillStyle = '#ffb0d8'; c.fillText('SPEED DATING', 360, 112); c.font = '600 28px Inter'; c.shadowColor = '#ffcf6a'; c.fillStyle = '#ffe0a0'; c.fillText('Friday Night · 3 min', 360, 152); c.shadowBlur = 0;
    // other daters, soft in the background
    c.filter = 'blur(5px)';
    for (const [x, col, col2] of [[-90, '#3a6ea8', '#b8443a'], [820, '#e0b43c', '#5a7a4a']]) { c.fillStyle = '#3a2418'; c.fillRect(x - 90, 640, 180, 30); for (const [dx, cc] of [[-60, col], [60, col2]]) { c.fillStyle = cc; c.beginPath(); c.ellipse(x + dx, 600, 42, 80, 0, 0, TAU); c.fill(); c.fillStyle = '#c9906a'; c.beginPath(); c.arc(x + dx, 500, 30, 0, TAU); c.fill(); } }
    c.filter = 'none';
  });
}
function stringLights(ctx, t, y0 = 30) {
  ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.beginPath();
  for (let i = 0; i <= 12; i++) { const x = i * 60, y = y0 + Math.sin(i * .9) * 14; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke();
  for (let i = 0; i <= 12; i++) glow(ctx, i * 60, y0 + Math.sin(i * .9) * 14 + 6, 46, ['#ffcf6a', '#ff8ac0', '#8ad0ff'][i % 3], .45 + .15 * Math.sin(t * 2 + i));
}
function barRoom(ctx, t, cam) { ctx.save(); if (cam) applyCam(ctx, cam); ctx.drawImage(barBG(), -200, -200); ctx.restore(); stringLights(ctx, t); }
function wineGlass(ctx, x, y, s, fill, col = '#7a1428') {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.strokeStyle = 'rgba(230,240,255,.75)'; ctx.lineWidth = 2.5;
  if (fill > 0) { ctx.fillStyle = col; ctx.beginPath(); const h = 40 * fill; ctx.moveTo(-20 + (1 - fill) * 4, -h); ctx.quadraticCurveTo(-18, 2, 0, 4); ctx.quadraticCurveTo(18, 2, 20 - (1 - fill) * 4, -h); ctx.fill(); }
  ctx.beginPath(); ctx.moveTo(-24, -46); ctx.quadraticCurveTo(-22, 4, 0, 6); ctx.quadraticCurveTo(22, 4, 24, -46); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, 6); ctx.lineTo(0, 40); ctx.moveTo(-16, 42); ctx.lineTo(16, 42); ctx.stroke();
  ctx.restore();
}
function pitcher(ctx, x, y, s, wine) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = mix('#bfe0f0', '#7a1428', wine); ctx.globalAlpha = .85; ctx.beginPath(); ctx.moveTo(-34, -80); ctx.lineTo(34, -80); ctx.lineTo(40, 30); ctx.quadraticCurveTo(0, 44, -40, 30); ctx.closePath(); ctx.fill(); ctx.globalAlpha = 1;
  ctx.strokeStyle = 'rgba(235,245,255,.85)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-40, -110); ctx.lineTo(40, -110); ctx.lineTo(44, 34); ctx.quadraticCurveTo(0, 50, -44, 34); ctx.closePath(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(42, -90); ctx.quadraticCurveTo(80, -70, 44, -20); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.fillRect(-30, -100, 8, 120);
  ctx.restore();
}
function tableFront(ctx, t, opts = {}) {
  const g = ctx.createLinearGradient(0, 990, 0, 1280); g.addColorStop(0, '#6a3e24'); g.addColorStop(.08, '#4a2a18'); g.addColorStop(1, '#1e100a'); ctx.fillStyle = g; ctx.fillRect(0, 990, W, 290);
  ctx.fillStyle = 'rgba(255,220,170,.2)'; ctx.fillRect(0, 990, W, 4);
  flame(ctx, 360, 960, .9, t); ctx.fillStyle = '#e8dcc0'; ctx.fillRect(352, 960, 16, 34);
  if (opts.glasses !== false) { wineGlass(ctx, 250, 985, 1, opts.fill ?? .55); wineGlass(ctx, 480, 985, 1, opts.fill2 ?? .55); }
  if (opts.num) { ctx.fillStyle = '#f2ead8'; roundRect(ctx, 560, 930, 70, 56, 8); ctx.fill(); ctx.fillStyle = '#3a2a20'; ctx.font = '800 34px Inter'; ctx.textAlign = 'center'; ctx.fillText(opts.num, 595, 970); ctx.textAlign = 'left'; }
}
function ding(ctx, t, tb, x = 360, y = 300) {
  const k = t - tb; if (k < 0 || k > 1) return;
  ctx.save(); ctx.globalAlpha = 1 - ramp(k, .6, 1); ctx.translate(x, y); ctx.rotate(Math.sin(k * 30) * .15 * (1 - k));
  ctx.fillStyle = '#e8c040'; ctx.beginPath(); ctx.moveTo(-50, 30); ctx.quadraticCurveTo(-50, -50, 0, -54); ctx.quadraticCurveTo(50, -50, 50, 30); ctx.closePath(); ctx.fill(); ctx.fillStyle = '#a07a20'; ctx.fillRect(-60, 26, 120, 12); ctx.beginPath(); ctx.arc(0, -60, 10, 0, TAU); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.font = '900 54px Inter'; ctx.textAlign = 'center'; ctx.shadowColor = '#000'; ctx.shadowBlur = 10; ctx.fillText('DING!', 0, 110); ctx.restore();
}
// two-shot at a table with Jesus on the left and a date on the right
function tableShot(t0, t1, dateName, kJ, kD, opts = {}) {
  const J = actor('jesus', Object.assign({ x: seat.J[0], y: seat.J[1], s: 1.35, turn: .35, look: lookAt('D'), follow: .55, lid: .14, smile: .25, browIn: .15, armL: [-40, 205], armR: [70, 200], handL: 'relax', handR: 'flat', gest: 1.4 }, opts.J || {}), kJ);
  const D = actor(dateName, Object.assign({ x: seat.D[0], y: seat.D[1], s: 1.3, turn: -.35, look: lookAt('J'), follow: .55, lid: .15, smile: .2, armL: [-70, 200], armR: [40, 205], handL: 'flat', gest: 1.4 }, opts.D || {}), kD);
  shot(t0, t1, (ctx, t) => {
    barRoom(ctx, t, opts.cam);
    const L = LIGHT.candle(360, 930);
    show(ctx, J, t, L, null, opts.extraJ ? st => opts.extraJ(st, t) : null);
    show(ctx, D, t, L, null, opts.extraD ? st => opts.extraD(st, t) : null);
    if (opts.under) opts.under(ctx, t);
    tableFront(ctx, t, opts.table || {});
    if (opts.over) opts.over(ctx, t);
    vignette(ctx, .45);
  }, opts.xin || 0);
  return { J, D };
}
function closeShot(t0, t1, name, base, keys, opts = {}) {
  const A = actor(name, Object.assign({ x: 360, y: 1000, s: 2.3, look: [opts.lookX ?? 560, 600], follow: .5, lid: .15 }, base), keys);
  shot(t0, t1, (ctx, t) => {
    barRoom(ctx, t, { x: opts.camX ?? 360, y: 420, z: 1.5 });
    ctx.fillStyle = 'rgba(10,5,8,.25)'; ctx.fillRect(0, 0, W, H);
    glow(ctx, opts.lx ?? 600, 1100, 500, '#ffb35c', .3);
    show(ctx, A, t, LIGHT.candle(opts.lx ?? 600, 1050, 1.1));
    if (opts.over) opts.over(ctx, t);
    vignette(ctx, .5);
  }, opts.xin || 0);
  return A;
}

function buildShots() {
  // ===== 1. cold open: the doorway (FIRST FRAME) =====
  const doorJ = actor('jesus', { x: 330, y: 760, s: 1.15, look: [600, 700], follow: .6, lid: .12, smile: .4, browOut: .2, armL: [-126, 300], armR: [126, 300] }, [
    { t: 3.0, d: 1.2, look: [80, 720] }, { t: WT('n1', 'small') - .3, d: .6, look: 'cam', follow: .45, smile: .5, browIn: .2 },
  ]);
  shot(0, st_('h1') - .35, (ctx, t) => {
    barRoom(ctx, t, { x: 360, y: 640, z: 1 });
    // a doorway of street light behind him
    const g = ctx.createLinearGradient(0, 380, 0, 1000); g.addColorStop(0, '#ffe8c0'); g.addColorStop(1, '#c08a5a'); ctx.fillStyle = g; ctx.fillRect(200, 380, 260, 640);
    glow(ctx, 330, 600, 380, '#ffe0a0', .4);
    show(ctx, doorJ, t, Object.assign(LIGHT.candle(330, 450, 1), { rim: .7, rimColor: '#fff0c0' }));
    ctx.strokeStyle = '#2a160e'; ctx.lineWidth = 24; ctx.strokeRect(188, 368, 284, 680);
    // host podium in the foreground
    const pg = ctx.createLinearGradient(0, 960, 0, 1280); pg.addColorStop(0, '#5a3420'); pg.addColorStop(1, '#1e100a'); ctx.fillStyle = pg; ctx.fillRect(120, 970, 480, 320); ctx.fillStyle = '#7a4a2a'; ctx.fillRect(100, 960, 520, 22);
    // "twelve tables": little numbered cards light up along the bottom on cue
    const k = ramp(t, WT('n1', 'Twelve') - .2, WT('n1', 'Twelve') + .6) * (1 - ramp(t, WT('n1', 'one'), WT('n1', 'one') + .5));
    if (k > 0) for (let i = 0; i < 12; i++) { ctx.save(); ctx.globalAlpha = k; ctx.fillStyle = '#f2ead8'; roundRect(ctx, 30 + i * 56, 1180, 46, 40, 6); ctx.fill(); ctx.fillStyle = '#3a2a20'; ctx.font = '700 22px Inter'; ctx.textAlign = 'center'; ctx.fillText(i + 1, 53 + i * 56, 1208); ctx.restore(); }
    const k2 = ramp(t, WT('n1', 'three') - .1, WT('n1', 'three') + .3) * (1 - ramp(t, WT('n1', 'one'), WT('n1', 'one') + .5));
    if (k2 > 0) { ctx.save(); ctx.globalAlpha = k2; ctx.fillStyle = '#fff'; ctx.font = '800 60px "DejaVu Sans Mono"'; ctx.textAlign = 'center'; ctx.shadowColor = '#000'; ctx.shadowBlur = 12; ctx.fillText('03:00', 560, 300); ctx.restore(); }
    vignette(ctx, .4);
  });
  LABELS.push({ t0: WT('n1', 'one') - .2, text: 'Jesus', x: 330, y: 440, dur: 2.6 });
  // ===== 2. the host at the podium =====
  const hostBase = { x: 520, y: 820, s: 1.2, turn: -.3, look: [200, 680], follow: .6, lid: .05, smile: .7, browOut: .5, armL: [-120, 120], armR: [60, 200], handL: 'hold', gest: 2 };
  const jPod = { x: 190, y: 820, s: 1.2, turn: .35, look: [520, 680], follow: .55, lid: .12, smile: .35, armL: [-126, 300], armR: [126, 300] };
  const podium = (t0, t1, kH, kJ, over, xin = 0) => {
    const Hh = actor('host', Object.assign({}, hostBase), kH), J = actor('jesus', Object.assign({}, jPod), kJ);
    shot(t0, t1, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 600, z: 1.1 });
      const L = LIGHT.bar(360, 300);
      show(ctx, J, t, L); show(ctx, Hh, t, L, null, st => { if (st.handL === 'hold') st.top = (c, arms) => { const w = arms.L.w; c.save(); c.translate(w[0] - 30, w[1] - 20); c.rotate(-.2); c.fillStyle = '#d8283a'; roundRect(c, -40, -26, 80, 52, 6); c.fill(); c.fillStyle = '#fff'; c.fillRect(-34, -6, 68, 26); c.restore(); }; });
      const pg = ctx.createLinearGradient(0, 1000, 0, 1280); pg.addColorStop(0, '#5a3420'); pg.addColorStop(1, '#1e100a'); ctx.fillStyle = pg; ctx.fillRect(0, 1010, W, 270); ctx.fillStyle = '#7a4a2a'; ctx.fillRect(0, 1000, W, 18);
      if (over) over(ctx, t);
      vignette(ctx, .4);
    }, xin);
  };
  podium(st_('h1') - .35, st_('tag') - .05, [
    { t: st_('h1'), d: .3, smile: .85, browOut: .7 }, { t: WT('h1', 'Name'), d: .5, armL: [-210, 40], handL: 'hold', look: [200, 900] },
  ], [{ t: st_('h1') + .2, d: .5, smile: .5, browOut: .3 }]);
  LABELS.push({ t0: st_('h1') + .2, text: 'The Host', x: 520, y: 470, dur: 2.4 });
  // ===== 3. writing the name tag =====
  shot(st_('tag') - .05, st_('h2') - .1, (ctx, t) => {
    ctx.fillStyle = '#3a2418'; ctx.fillRect(0, 0, W, H); glow(ctx, 360, 640, 500, '#ffcf8a', .35);
    ctx.save(); ctx.translate(360, 600); ctx.rotate(-.04);
    ctx.fillStyle = '#d8283a'; roundRect(ctx, -280, -190, 560, 380, 30); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.font = '900 64px Inter'; ctx.textAlign = 'center'; ctx.fillText('HELLO', 0, -110); ctx.font = '600 32px Inter'; ctx.fillText('my name is', 0, -66);
    ctx.fillRect(-250, -40, 500, 200);
    const p = clamp((t - st_('tag') - .2) / 1.4);
    ctx.save(); ctx.beginPath(); ctx.rect(-250, -40, 500 * p, 200); ctx.clip();
    ctx.fillStyle = '#1a1a2a'; ctx.font = 'italic 700 110px "DejaVu Serif"'; ctx.fillText('Jesus', 0, 100); ctx.restore();
    // marker
    const mx = -170 + p * 340, my = 70 + Math.sin(p * 40) * 14;
    ctx.save(); ctx.translate(mx, my); ctx.rotate(-.7); ctx.fillStyle = '#1a1a2a'; roundRect(ctx, -12, -110, 24, 120, 6); ctx.fill(); ctx.fillStyle = '#e8e8e8'; ctx.fillRect(-12, -70, 24, 20); ctx.restore();
    ctx.restore();
    vignette(ctx, .4);
  }, 0);
  podium(st_('h2') - .1, st_('j1') - .25, [
    { t: st_('h2'), d: .4, look: [200, 900], smile: .4 }, { t: WT('h2', 'Okay'), d: .4, look: [200, 680], smile: .75, browOut: .9, browR: .4 },   // reads it, delighted, one brow up
  ], [{ t: 0, smile: .35 }]);
  closeShot(st_('j1') - .25, st_('h3') - .35, 'jesus', { smile: .3, lid: .15, browIn: .25, armL: [-126, 300], armR: [126, 300], lookX: 560 }, [
    { t: st_('j1'), d: .3, smile: .15, browIn: .1 }, { t: en_('j1') + .1, d: .5, smile: .45 },                                                         // a kind, steady smile
  ], { lx: 620 });
  podium(st_('h3') - .35, st_('j2') - .3, [
    { t: WT('h3', 'Three'), d: .3, armR: [140, 40], handR: 'point', angR: -.6 }, { t: WT('h3', 'bell'), d: .3, armR: [150, 0], handR: 'grip' },
    { t: WT('h3', 'rotate'), d: .4, armR: [60, 200], handR: 'relax' }, { t: WT('h3', 'Honestly'), d: .4, smile: .5, browR: .3, headRoll: .08 },
    { t: WT('h3', 'seven'), d: .3, armL: [-150, 30], handL: 'open', smile: .65 },
  ], [
    { t: WT('h3', 'bell'), d: .4, smile: .3 }, { t: WT('h3', 'seven'), d: .5, smile: .05, browIn: .5, lid: .1 },
  ], (ctx, t) => { const a = ramp(t, WT('h3', 'seven') - .1, WT('h3', 'seven') + .2); if (a > 0) { ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#fff'; ctx.font = '800 64px "DejaVu Sans Mono"'; ctx.textAlign = 'center'; ctx.shadowColor = '#000'; ctx.shadowBlur = 14; ctx.fillText('0:07', 360, 300); ctx.restore(); } });
  // ===== 4. "Seven seconds? To know a soul?" =====
  {
    const J = actor('jesus', { x: 360, y: 980, s: 2.0, look: [100, 640], follow: .6, lid: .12, smile: 0, browIn: .6, armL: [-126, 300], armR: [126, 300] }, [
      { t: WT('j2', 'know'), d: 1.2, look: [620, 640], browIn: .9, smile: -.1, lid: .2 },   // gazes over the room, tender
    ]);
    shot(st_('j2') - .3, st_('h4') - .3, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 500, z: 1.3 });
      // daters in the room glancing, judging in seconds (blurred, flicking)
      show(ctx, J, t, LIGHT.candle(560, 900));
      vignette(ctx, .45);
    }, 0);
  }
  // ===== 5. the sandals =====
  shot(st_('h4') - .3, st_('k1') - .5, (ctx, t) => {
    ctx.fillStyle = '#2a1812'; ctx.fillRect(0, 0, W, H);
    const fg = ctx.createLinearGradient(0, 700, 0, H); fg.addColorStop(0, '#4a2e20'); fg.addColorStop(1, '#1a0e08'); ctx.fillStyle = fg; ctx.fillRect(0, 640, W, 640);
    ctx.fillStyle = '#a8261e'; ctx.fillRect(160, 0, 400, 560); ctx.fillStyle = '#e8c040'; ctx.fillRect(250, 0, 8, 560); ctx.fillRect(462, 0, 8, 560);
    for (const s of [-1, 1]) {
      const x = 360 + s * 110, wig = Math.sin(t * 9 + s) * 4 * (t > st_('h4') + .3 ? 1 : 0);
      ctx.fillStyle = '#8a5a34'; roundRect(ctx, x - 70, 860, 140, 300, 60); ctx.fill();
      ctx.fillStyle = CAST.jesus.skin; ctx.fillRect(x - 40, 560, 80, 320); roundRect(ctx, x - 62, 840, 124, 280, 56); ctx.fill();
      for (let k = 0; k < 5; k++) { ctx.beginPath(); ctx.ellipse(x - 44 + k * 22, 1120 + (k === 0 || k === 4 ? 6 : 0) + (k % 2 ? wig : -wig), 12, 16, 0, 0, TAU); ctx.fill(); }
      ctx.fillStyle = '#5a3418'; ctx.fillRect(x - 66, 930, 132, 22); ctx.fillRect(x - 66, 1030, 132, 22); ctx.fillRect(x - 10, 860, 20, 190);
    }
    vignette(ctx, .4);
  }, 0);
  // ===== 6. date one: Kayla, live =====
  const kaylaPhone = { armR: [70, 30], handR: 'hold', angR: -.4, holdR: null, armL: [-70, 200] };
  tableShot(st_('k1') - .5, st_('j3') - .25, 'kayla', [{ t: st_('k1') + .2, d: .4, smile: .3, browOut: .4 }, { t: WT('k1', 'live'), d: .4, lid: .05, browOut: .7, smile: .2 }],
    [{ t: st_('k1'), d: .3, smile: .9, browOut: .8 }, { t: WT('k1', 'followers') - .3, d: .4, look: [560, 560], follow: .7 }],
    { D: Object.assign({ smile: .7, lid: 0 }, kaylaPhone), xin: .3, extraD: (st, t) => { st.top = (c, arms) => { const w = arms.R.w; c.save(); c.translate(w[0] + 6, w[1] - 70); c.rotate(-.25); c.fillStyle = '#e8e0e8'; roundRect(c, -34, -64, 68, 128, 12); c.fill(); c.fillStyle = '#2a2a2e'; roundRect(c, -28, -58, 56, 116, 8); c.fill(); c.fillStyle = '#ff3a5a'; roundRect(c, -24, -52, 30, 14, 4); c.fill(); c.restore(); }; } });
  LABELS.push({ t0: st_('k1') + .1, text: 'Kayla', x: 540, y: 470, dur: 2.4 });
  // phone POV: he speaks straight into the lens
  {
    const t0 = st_('j3') - .25, t1 = st_('k2') - .35;
    const J = actor('jesus', { x: 360, y: 1030, s: 2.4, look: 'cam', follow: .5, lid: .18, smile: .2, browIn: .45, armL: [-126, 300], armR: [126, 300], nod: .5 }, [
      { t: WT('j3', 'see'), d: .5, lid: .08, browIn: .6 }, { t: WT('j3', 'alone'), d: .8, smile: .4, lid: .2, tearful: .3 },
    ]);
    const comments = [['who is this', WT('j3', 'see')], ['wait', WT('j3', 'you', 0)], ['it IS 2am', WT('j3', 'morning')], ['why do i feel seen', WT('j3', 'alone') - .4], ["he's talking to ME", WT('j3', 'alone')], ['crying at 2am <3', en_('j3')], ['<3 <3 <3', en_('j3') + .3], ['me too', en_('j3') + .6]];
    shot(t0, t1, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 450, z: 1.6 });
      show(ctx, J, t, LIGHT.candle(520, 1000, 1.1));
      // phone UI frame
      ctx.strokeStyle = '#111'; ctx.lineWidth = 34; roundRect(ctx, 0, 0, W, H, 60); ctx.stroke();
      ctx.fillStyle = '#ff3a5a'; roundRect(ctx, 40, 50, 92, 40, 8); ctx.fill(); ctx.fillStyle = '#fff'; ctx.font = '800 24px Inter'; ctx.fillText('LIVE', 56, 78);
      const viewers = Math.floor(lerp(212, 48211, ease((t - t0) / (t1 - t0))));
      ctx.fillStyle = 'rgba(0,0,0,.45)'; roundRect(ctx, 144, 50, 170, 40, 8); ctx.fill(); ctx.fillStyle = '#fff'; ctx.font = '600 22px Inter'; ctx.fillText('👁 ' + viewers.toLocaleString(), 156, 78);
      comments.forEach(([txt, ti], i) => {
        const age = t - ti; if (age < 0) return;
        const shown = comments.filter(c => t >= c[1]).length, idx = comments.filter(c => t >= c[1]).findIndex(c => c[0] === txt);
        const y = 880 - (shown - 1 - idx) * 50; if (y < 600) return;
        ctx.save(); ctx.globalAlpha = Math.min(1, age * 4) * .95; ctx.fillStyle = 'rgba(0,0,0,.4)'; ctx.font = '600 24px Inter'; const w = ctx.measureText(txt).width + 30; roundRect(ctx, 40, y - 28, w, 40, 18); ctx.fill(); ctx.fillStyle = '#fff'; ctx.fillText(txt, 55, y); ctx.restore();
      });
      // floating hearts
      for (let i = 0; i < 10; i++) { const p = ((t - WT('j3', 'alone')) * .5 + i / 10) % 1; if (t < WT('j3', 'alone')) break; ctx.fillStyle = `rgba(255,90,140,${1 - p})`; ctx.font = '700 34px Inter'; ctx.fillText('♥', 620 + Math.sin(p * 8 + i) * 20, 900 - p * 500); }
    }, 0);
  }
  tableShot(st_('k2') - .35, st_('d1') - .5, 'kayla', [
    { t: 0, look: lookAt('D'), smile: .2, browIn: .3 }, { t: st_('j4'), d: .4, lid: .12, smile: .35, browIn: .4, armL: [-60, 160], handL: 'open', angL: -.4 },
  ], [
    { t: 0, look: [560, 560], follow: .7, lid: -.1, browIn: .9, browOut: .5, open: .2, tearful: .7 },                                                  // stunned at her own screen
    { t: WT('k2', 'Why', 1), d: .4, armL: [-30, 60], handL: 'flat', angL: -1.2, look: lookAt('J') },                                                     // dabs her eye
    { t: WT('j4', 'audience'), d: 1.0, armR: [60, 190], look: lookAt('J'), follow: .5, armL: [-70, 200], handL: 'flat', lid: .15, open: 0 },           // slowly lowers the phone
    { t: WT('j4', 'You') + .2, d: .8, smile: .45, browIn: .4, browOut: 0, tearful: .5 },                                                                // a real smile
  ], { D: Object.assign({ smile: .1 }, kaylaPhone), extraD: (st, t) => { st.top = (c, arms) => { const w = arms.R.w, low = ramp(t, WT('j4', 'audience'), WT('j4', 'audience') + 1); c.save(); c.translate(w[0] + 6, w[1] - 70 + low * 40); c.rotate(-.25 + low * 1.2); c.fillStyle = '#e8e0e8'; roundRect(c, -34, -64, 68, 128, 12); c.fill(); c.fillStyle = '#2a2a2e'; roundRect(c, -28, -58, 56, 116, 8); c.fill(); c.restore(); }; },
    over: (ctx, t) => ding(ctx, t, en_('j4') + .9) });
  // ===== 7. date two: Dana and the checklist =====
  {
    const t0 = st_('d1') - .5, t1 = st_('j8') - .3;
    const marks = [['Height', '✓', en_('j5') - .2], ['Income', '✗', WT('j6', 'Zero') + .1], ['Car', '✗', WT('j7', 'walk')], ['', '?', WT('j7', 'water') + .1]];
    tableShot(t0, t1, 'dana', [
      { t: 0, smile: .3 }, { t: st_('j5'), d: .3, smile: .35, browR: .3 }, { t: st_('j6'), d: .4, smile: .15, browIn: .2, lid: .2 },
      { t: st_('j7'), d: .4, smile: .25, browOut: .2 },
    ], [
      { t: 0, lid: .25, smile: 0, browIn: -.2, look: [560, 990], follow: .7 },                                                      // eyes on her clipboard
      { t: st_('d1') + .2, d: .3, look: lookAt('J'), follow: .55 }, { t: en_('d1') + .1, d: .3, look: [560, 990] },
      { t: WT('j6', 'Zero'), d: .3, look: lookAt('J'), lid: .05, browIn: -.3 }, { t: WT('j6', 'Foxes'), d: .4, look: [560, 990], smile: -.2 },
      { t: st_('d3'), d: .3, look: lookAt('J') }, { t: WT('j7', 'walk'), d: .3, look: [560, 990] },
      { t: WT('j7', 'water'), d: .25, frozen: 1, open: .25, lid: -.15, browOut: 1, browIn: .6 },                                   // the pen stops
      { t: WT('j7', 'water') + .5, d: 1.0, look: lookAt('J'), follow: .5 },                                                         // ...slowly looks up
      { t: st_('d4') - .1, d: .4, open: 0, lid: .1, browIn: .3, browOut: .5 },
    ], { D: { armL: [-30, 150], handL: 'hold', angL: .9, armR: [60, 150], handR: 'pen', gest: .6 },
      extraD: (st, t) => { st.mid = (c, arms) => { const a = arms.L.w; c.save(); c.translate(a[0] + 50, a[1] - 20); c.rotate(.15); c.fillStyle = '#8a6a40'; roundRect(c, -50, -70, 100, 130, 6); c.fill(); c.fillStyle = '#fafaf4'; c.fillRect(-42, -56, 84, 110); c.restore(); }; },
      over: (ctx, t) => {
        if (t < st_('d1') + .5) return;
        ctx.save(); ctx.translate(500, 250); ctx.rotate(.03);
        ctx.fillStyle = 'rgba(250,250,244,.96)'; roundRect(ctx, -150, -60, 300, 270, 14); ctx.fill(); ctx.fillStyle = '#2a3a5a'; ctx.font = '800 24px Inter'; ctx.fillText('MUST HAVES', -128, -22);
        marks.slice(0, 3).forEach(([lbl, m, ti], i) => { const y = 26 + i * 52; ctx.strokeStyle = '#2a2a2a'; ctx.lineWidth = 2.5; ctx.strokeRect(-128, y - 24, 30, 30); ctx.fillStyle = '#2a2a2a'; ctx.font = '600 24px Inter'; ctx.fillText(lbl, -84, y); if (t > ti) { ctx.fillStyle = m === '✓' ? '#1a8a3a' : '#d02a2a'; ctx.font = '900 32px Inter'; ctx.fillText(m, -126, y + 2); } });
        ctx.fillStyle = '#2a2a2a'; ctx.font = '600 24px Inter'; ctx.fillText('Walks on water', -84, 182); ctx.strokeRect(-128, 158, 30, 30);
        if (t > marks[3][2]) { ctx.fillStyle = '#d07a1a'; ctx.font = '900 34px Inter'; ctx.fillText('?', -120, 186); }
        ctx.restore();
        ding(ctx, t, -9);
      } });
    LABELS.push({ t0: st_('d1') - .2, text: 'Dana', x: 540, y: 470, dur: 2.2 });
  }
  // red flags: the $19 water
  {
    const t0 = st_('j8') - .3, t1 = st_('j9') - .5, tM = WT('j8', 'marketplace');
    const B = actor('bartender', { x: 430, y: 860, s: 1.25, look: [100, 760], follow: .6, lid: .12, smile: .2, armL: [-126, 300], armR: [160, 60], handR: 'hold' }, [
      { t: WT('j8', 'flip') - .1, d: .3, lid: -.1, browOut: .9, browIn: .6, smile: -.2, look: [100, 700] },                // freezes
      { t: tM, d: .4, look: [620, 560], follow: .7, smile: -.35, open: .15, round: .7 },                                     // gulps, eyes to his sign
      { t: tM + 1.0, d: .4, look: [100, 700], smile: .35, lid: .1 },                                                         // innocent grin
    ]);
    shot(t0, t1, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 600, z: 1.1 });
      for (let i = 0; i < 7; i++) { ctx.fillStyle = ['#3a5a3a', '#6a1a24', '#c9a24a', '#2a3a4a'][i % 4]; roundRect(ctx, 60 + i * 90, 470, 40, 120, 10); ctx.fill(); ctx.fillRect(72 + i * 90, 440, 16, 30); }
      ctx.fillStyle = '#3a2210'; ctx.fillRect(0, 590, W, 14);
      show(ctx, B, t, LIGHT.bar(300, 400));
      // the price sign flips from $19 to $2
      const f = ramp(t, tM + .4, tM + 1.0), sx = Math.abs(Math.cos(f * Math.PI));
      ctx.save(); ctx.translate(600, 720); ctx.scale(sx, 1); ctx.fillStyle = '#1a1a1a'; roundRect(ctx, -110, -70, 220, 140, 12); ctx.fill(); ctx.strokeStyle = '#c9a24a'; ctx.lineWidth = 4; roundRect(ctx, -110, -70, 220, 140, 12); ctx.stroke();
      ctx.fillStyle = '#f2ead8'; ctx.textAlign = 'center'; ctx.font = '600 26px "DejaVu Serif"'; ctx.fillText('Still Water', 0, -18); ctx.font = '800 54px "DejaVu Serif"'; ctx.fillText(f < .5 ? '$19' : '$2', 0, 46); ctx.restore();
      const cg = ctx.createLinearGradient(0, 1000, 0, H); cg.addColorStop(0, '#5a3018'); cg.addColorStop(1, '#1e100a'); ctx.fillStyle = cg; ctx.fillRect(0, 1000, W, 280); ctx.fillStyle = '#8a5a30'; ctx.fillRect(0, 990, W, 18);
      vignette(ctx, .4);
    }, 0);
    LABELS.push({ t0: t0 + .2, text: 'Bartender', x: 430, y: 520, dur: 2 });
  }
  tableShot(st_('j9') - .5, st_('b1') - .4, 'dana', [
    { t: 0, smile: .35, look: lookAt('D') }, { t: st_('j9'), d: .4, armR: [120, 190], handR: 'flat', angR: .2, smile: .5 },                      // pats the table: safe
    { t: en_('j9') + .2, d: .4, armR: [70, 200] }, { t: st_('j10'), d: .4, smile: .3, lid: .12, browOut: .2 },
  ], [
    { t: 0, lid: -.1, browOut: .9, browIn: .5, smile: -.2, armL: [-120, 180], handL: 'grip', armR: [130, 180], handR: 'grip' },                 // gripping the table edge
    { t: en_('j9'), d: .6, lid: .15, browOut: .3, smile: .05, armL: [-30, 150], handL: 'hold', armR: [60, 150], handR: 'pen' },
    { t: st_('d5'), d: .3, look: [560, 990] }, { t: WT('j10', 'eternities'), d: .3, look: lookAt('J'), lid: -.12, browOut: 1, open: .3 },      // drops the pen
    { t: WT('j10', 'eternities') + .8, d: .6, open: .1, smile: .15, lid: .05 },
  ], { D: { armL: [-30, 150], handL: 'hold', angL: .9, armR: [60, 150], handR: 'pen' },
    over: (ctx, t) => { const p = clamp((t - WT('j10', 'eternities')) / .5); if (p > 0 && p < 1) { ctx.save(); ctx.translate(600, lerp(960, 1080, p * p)); ctx.rotate(p * 4); ctx.fillStyle = '#1a3a8a'; ctx.fillRect(-4, -40, 8, 80); ctx.restore(); } ding(ctx, t, en_('j10') + .8); } });
  // ===== 8. out of wine -> the pitcher =====
  {
    const t0 = st_('b1') - .4, tW = st_('wine'), t1 = st_('j11') - .35;
    const B = actor('bartender', { x: 430, y: 860, s: 1.25, look: [300, 760], follow: .6, lid: -.05, browIn: .9, browOut: .5, smile: -.4, armL: [-126, 300], armR: [140, 20], handR: 'grip', angR: -2.6 }, [
      { t: en_('b1') + .3, d: .5, armR: [126, 300], handR: 'relax' },
      { t: st_('b2') - .4, d: .5, armR: [40, 40], handR: 'hold', angR: -.8, look: [400, 900], lid: .4 },                                         // sips
      { t: WT('b2', 'better'), d: .3, lid: -.15, browOut: 1, browIn: .3, smile: .6, look: [100, 640] },
    ]);
    const Hh = actor('host', { x: 150, y: 880, s: 1.05, turn: .3, look: [430, 700], follow: .6, lid: -.05, browIn: .8, browOut: .6, smile: -.3, armL: [-30, 100], handL: 'flat', angL: -1.2, armR: [126, 300] }, [
      { t: st_('h5'), d: .4, browIn: .4, browOut: .9, smile: 0, open: .1, look: [430, 1000] },
    ]);
    const barShot = (a, b) => shot(a, b, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 600, z: 1.1 });
      for (let i = 0; i < 7; i++) { ctx.fillStyle = ['#3a5a3a', '#6a1a24', '#c9a24a', '#2a3a4a'][i % 4]; roundRect(ctx, 60 + i * 90, 470, 40, 120, 10); ctx.fill(); }
      ctx.fillStyle = '#3a2210'; ctx.fillRect(0, 590, W, 14);
      const L = LIGHT.bar(300, 400);
      let bst = show(ctx, B, t, L, null, st => { st.top = (c, arms) => { const w = arms.R.w; if (t < en_('b1') + .5) { c.save(); c.translate(w[0], w[1] - 40); c.rotate(Math.PI); c.fillStyle = '#2a4a2a'; roundRect(c, -16, -60, 32, 110, 8); c.fill(); c.fillRect(-7, -90, 14, 32); c.restore(); if (Math.sin(t * 6) > .7) { c.fillStyle = '#7a1428'; c.beginPath(); c.arc(w[0], w[1] + 30, 4, 0, TAU); c.fill(); } } else if (t > st_('b2') - .4) wineGlass(c, w[0] + 20, w[1] - 10, 1.1, .5); }; });
      show(ctx, Hh, t, L);
      const cg = ctx.createLinearGradient(0, 1000, 0, H); cg.addColorStop(0, '#5a3018'); cg.addColorStop(1, '#1e100a'); ctx.fillStyle = cg; ctx.fillRect(0, 1000, W, 280); ctx.fillStyle = '#8a5a30'; ctx.fillRect(0, 990, W, 18);
      vignette(ctx, .4);
    }, 0);
    barShot(t0, tW - .1);
    shot(tW - .1, st_('h5') - .2, (ctx, t) => {   // water becomes wine, glasses fill across the room
      barRoom(ctx, t, { x: 360, y: 300, z: 1.8 });
      ctx.fillStyle = 'rgba(20,10,10,.3)'; ctx.fillRect(0, 0, W, H);
      const k = ramp(t, tW + .2, tW + 1.6);
      const tg = ctx.createLinearGradient(0, 900, 0, H); tg.addColorStop(0, '#6a3e24'); tg.addColorStop(1, '#1e100a'); ctx.fillStyle = tg; ctx.fillRect(0, 900, W, 380);
      pitcher(ctx, 280, 860, 1.8, k);
      for (let i = 0; i < 3; i++) wineGlass(ctx, 470 + i * 80, 900 + i * 20, 1.4, ramp(t, tW + 1.0 + i * .35, tW + 1.8 + i * .35));
      for (let i = 0; i < 14; i++) { const p = ((t - tW) * .6 + hash(i)) % 1; if (k <= 0) break; ctx.fillStyle = `rgba(255,240,200,${(1 - p) * k * .8})`; ctx.beginPath(); ctx.arc(280 + (hash(i + 3) - .5) * 180, 760 - p * 300, 3, 0, TAU); ctx.fill(); }
      vignette(ctx, .4);
    }, 0);
    barShot(st_('h5') - .2, t1);
  }
  {
    const J = actor('jesus', { x: 360, y: 980, s: 2.1, look: [560, 640], follow: .5, lid: .2, smile: .35, armL: [-126, 300], armR: [40, 40], handR: 'hold', angR: -.8 }, [
      { t: st_('j11') + .1, d: .4, armR: [55, 95] }, { t: WT('j11', 'last') + .2, d: .15, lidL: .9, smile: .55 }, { t: WT('j11', 'last') + .55, d: .2, lidL: 0 },   // a little wink
    ]);
    shot(st_('j11') - .35, st_('p1') - .5, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 420, z: 1.5 });
      show(ctx, J, t, LIGHT.candle(600, 1050, 1.1), null, st => { st.top = (c, arms) => { const w = arms.R.w; wineGlass(c, w[0] + 24, w[1] - 14, 1.2, .5); }; });
      vignette(ctx, .45);
    }, 0);
  }
  // ===== 9. date three: Priya, "what's your sign?" =====
  tableShot(st_('p1') - .5, st_('j12') - .25, 'priya', [{ t: 0, smile: .35 }, { t: WT('p1', 'sign'), d: .4, browOut: .4, smile: .45, lid: .1 }],
    [{ t: 0, smile: .6, lid: .1, browOut: .4 }, { t: WT('p1', 'important'), d: .4, armL: [-90, 120], handL: 'point', angL: -.6, browIn: .4, smile: .3 }, { t: WT('p1', 'sign'), d: .3, browOut: .9, smile: .5, lid: -.05 }],
    { xin: .3 });
  LABELS.push({ t0: st_('p1') - .2, text: 'Priya', x: 540, y: 470, dur: 2.2 });
  shot(st_('j12') - .25, st_('p2') - .35, (ctx, t) => {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0a0e24'); g.addColorStop(1, '#2a2440'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 80; i++) { ctx.fillStyle = `rgba(255,255,255,${.3 + .4 * hash(i)})`; ctx.fillRect(hash(i + 1) * W, hash(i + 2) * 800, 2, 2); }
    const sk = ramp(t, WT('j12', 'star') - .3, WT('j12', 'star') + .5);
    glow(ctx, 380, 260, 260 * sk, '#fff6c0', .7 * sk); ctx.save(); ctx.translate(380, 260); ctx.fillStyle = '#fff'; ctx.globalAlpha = sk; for (let k = 0; k < 4; k++) { ctx.rotate(Math.PI / 4); ctx.fillRect(-2, -60, 4, 120); } ctx.restore();
    ctx.strokeStyle = `rgba(255,246,192,${.25 * sk})`; ctx.lineWidth = 30; ctx.beginPath(); ctx.moveTo(380, 280); ctx.lineTo(380, 760); ctx.stroke();
    ctx.fillStyle = '#16121e'; ctx.beginPath(); ctx.moveTo(0, 900); ctx.quadraticCurveTo(360, 820, 720, 900); ctx.lineTo(720, H); ctx.lineTo(0, H); ctx.fill();
    ctx.fillStyle = '#2a2030'; ctx.fillRect(320, 760, 120, 90); ctx.beginPath(); ctx.moveTo(300, 760); ctx.lineTo(380, 700); ctx.lineTo(460, 760); ctx.fill(); ctx.fillStyle = '#ffcf6a'; ctx.fillRect(366, 800, 26, 40);
    const wk = ramp(t, WT('j12', 'wise') - .3, WT('j12', 'wise') + .5);
    for (let i = 0; i < 3; i++) { const x = lerp(-80, 120, (t - st_('j12')) / 5) + i * 70; ctx.save(); ctx.globalAlpha = wk; ctx.translate(x, 900); ctx.fillStyle = '#0c0a12'; ctx.beginPath(); ctx.ellipse(0, -40, 40, 22, 0, 0, TAU); ctx.fill(); ctx.fillRect(26, -90, 12, 50); ctx.beginPath(); ctx.ellipse(40, -94, 16, 9, 0, 0, TAU); ctx.fill(); for (const lx of [-26, -10, 14, 28]) ctx.fillRect(lx, -30, 6, 40 + Math.sin(t * 6 + lx) * 4); ctx.beginPath(); ctx.arc(-4, -84, 11, 0, TAU); ctx.fill(); ctx.fillRect(-14, -74, 20, 30); ctx.restore(); }
    vignette(ctx, .3);
  }, .3);
  tableShot(st_('p2') - .35, st_('n2') - .5, 'priya', [
    { t: 0, smile: .4 }, { t: st_('j13') - .1, d: .3, headPitch: -.15, headRoll: -.08, lid: .6, squint: 1, smile: .9, open: .4 },          // laughs from the belly
    { t: en_('j13') + .3, d: .6, headPitch: 0, headRoll: 0, lid: .15, squint: .2, smile: .55, open: 0 },
  ], [
    { t: 0, lid: -.12, browOut: 1, open: .3, smile: .4, lean: -.06 }, // leaning in, wide-eyed
    { t: WT('p2', 'cusp'), d: .4, open: 0, smile: .8, armL: [-90, 120], handL: 'open', armR: [126, 300], browOut: .6 },
    { t: st_('j13'), d: .4, smile: .9, squint: .5, lid: .3 },
  ], { over: (ctx, t) => ding(ctx, t, en_('j13') + .9) });
  // ===== 10. table twelve =====
  const mBase = { look: lookAt('J'), follow: .5, lid: .35, smile: 0, browIn: -.1, armL: [58, 105], handL: 'grip', armR: [-58, 95], handR: 'grip', gest: .4 };   // arms crossed
  tableShot(st_('n2') - .5, st_('j14') - .3, 'marisol', [
    { t: 0, smile: .25, lid: .14 }, { t: WT('m1', 'vanish'), d: .4, smile: .05, browIn: .35, lid: .15 },
  ], [
    { t: 0, look: [700, 900], follow: .6, lid: .5 },                                                                           // looking away, unimpressed
    { t: st_('m1') - .3, d: .5, look: lookAt('J'), lid: .35, sneer: .3, browR: .45, smile: .15 },                            // one brow up: "let me guess"
    { t: WT('m1', 'good'), d: .4, headRoll: .06, smile: .25 }, { t: WT('m1', 'vanish'), d: .5, smile: -.1, sneer: .1, browR: 0, lid: .4 },
  ], { D: mBase, table: { num: '12', fill: .3, fill2: .3 }, xin: .4,
    over: (ctx, t) => { const k = ramp(t, st_('n2'), st_('n2') + .6) * (1 - ramp(t, st_('m1') - .4, st_('m1'))); if (k > 0) { ctx.fillStyle = `rgba(0,0,0,${.35 * k})`; ctx.fillRect(0, 0, W, H); } } });
  LABELS.push({ t0: st_('n2') + .2, text: 'Marisol', x: 540, y: 470, dur: 2.4 });
  const jClose = (a, b, keys) => closeShot(a, b, 'jesus', { smile: .1, lid: .18, browIn: .55, armL: [-126, 300], armR: [126, 300], nod: .4 }, keys, { lx: 620 });
  const mClose = (a, b, keys, tears) => { const A = closeShot(a, b, 'marisol', Object.assign({}, mBase, { lid: .35, lookX: 160 }), keys, { lx: 120, camX: 300 }); if (tears) A.tr.base.tears = tears; return A; };
  jClose(st_('j14') - .3, st_('m2') - .4, [{ t: st_('j14'), d: .5, browIn: .7, lid: .2, smile: 0 }, { t: en_('j14') + .3, d: 1.2, browIn: .8 }]);   // quiet, steady
  mClose(st_('m2') - .4, st_('j15') - .45, [
    { t: st_('m2') - .4, d: .8, look: [300, 1150], lid: .55, smile: -.35, sneer: 0, browIn: .6 },                    // her eyes drop
    { t: en_('m2') + .2, d: .4, open: .08, round: .5 }, { t: en_('m2') + .6, d: .3, open: 0, smile: -.4 },           // a swallow
  ]);
  tableShot(st_('j15') - .45, st_('m3') - .35, 'marisol', [
    { t: st_('j15'), d: .5, lid: .2, browIn: .6, smile: .1, armL: [-30, 170], handL: 'open', angL: -.5, armR: [80, 170], handR: 'open', angR: .5 },   // open hands on the table
    { t: WT('j15', 'tired'), d: .6, smile: .25 },
  ], [
    { t: 0, look: [400, 1000], lid: .5, smile: -.3, browIn: .6 },
    { t: WT('j15', 'impressive'), d: .6, look: lookAt('J'), lid: .35 },
    { t: WT('j15', 'allowed') - .2, d: 1.6, armL: [-90, 200], handL: 'flat', armR: [90, 200], handR: 'flat', shrug: -.6, lid: .4, browIn: .9, smile: -.3, tearful: .4 },  // arms uncross, shoulders drop
    { t: en_('j15') + .3, d: .6, open: .1 },
  ], { D: mBase, table: { num: '12', fill: .3, fill2: .3 } });
  mClose(st_('m3') - .35, st_('j16') - .3, [
    { t: 0, look: [160, 600], lid: .3, browIn: 1, smile: -.35, tearful: .6, armL: [-90, 200], handL: 'flat', armR: [90, 200], handR: 'flat' },
  ]);
  jClose(st_('j16') - .3, st_('m4') - .4, [{ t: st_('j16'), d: .4, browIn: .65, lid: .15, smile: .05, headRoll: -.06 }, { t: en_('j16') + .2, d: .8, smile: .15 }]);
  mClose(st_('m4') - .4, st_('j17') - .4, [
    { t: 0, look: [160, 600], lid: .3, browIn: 1.1, smile: -.4, tearful: .8, armL: [-90, 200], handL: 'flat', armR: [90, 200], handR: 'flat' },
    { t: WT('m4', 'bone'), d: .6, lid: .45, look: [260, 900] },
  ], [{ side: 1, t0: WT('m4', 'Lonely') + .4, dur: 3.6 }]);
  // the garden: friends asleep
  shot(st_('j17') - .4, en_('j17') + .5, (ctx, t) => {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0a0e1e'); g.addColorStop(1, '#1a2030'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    glow(ctx, 540, 200, 200, '#e0e8ff', .5); ctx.fillStyle = '#eef2ff'; ctx.beginPath(); ctx.arc(540, 200, 46, 0, TAU); ctx.fill();
    for (const [x, s] of [[100, 1], [620, .8], [330, .7]]) { ctx.fillStyle = '#0c1018'; ctx.fillRect(x - 12 * s, 600 - 300 * s, 24 * s, 400 * s); ctx.beginPath(); ctx.ellipse(x, 600 - 300 * s, 140 * s, 80 * s, 0, 0, TAU); ctx.fill(); }
    ctx.fillStyle = '#121620'; ctx.fillRect(0, 900, W, 380);
    const sk = ramp(t, WT('j17', 'friends') - .3, WT('j17', 'asleep'));
    for (let i = 0; i < 3; i++) { const x = 120 + i * 120, sl = sk * (8 + i * 3); ctx.save(); ctx.translate(x, 960); ctx.rotate(-.3 - sl * .03); ctx.fillStyle = '#2a3040'; ctx.beginPath(); ctx.ellipse(0, 0, 50, 70, 0, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.arc(10, -70 + sl, 26, 0, TAU); ctx.fill(); ctx.restore(); if (sk > .8) { ctx.fillStyle = `rgba(220,230,255,${.6 * Math.sin(t * 2 + i) ** 2})`; ctx.font = 'italic 600 28px Inter'; ctx.fillText('z', x + 30, 860 - i * 10 - (t * 10 % 20)); } }
    // he kneels apart, praying, moonlight on him
    ctx.save(); ctx.translate(560, 960); ctx.fillStyle = '#3a1418'; ctx.beginPath(); ctx.ellipse(0, 0, 54, 80, 0, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.arc(-6, -100, 28, 0, TAU); ctx.fill(); ctx.fillStyle = 'rgba(200,215,255,.35)'; ctx.beginPath(); ctx.arc(-6, -100, 28, -1.4, .3); ctx.fill(); ctx.restore();
    vignette(ctx, .4);
  }, .4);
  // the bell, and a rule bent for a person
  {
    const tb = st_('bell'), t1 = st_('n3') - .5;
    const Hh = actor('host', { x: 640, y: 720, s: 1.05, turn: -.3, look: [360, 640], follow: .6, lid: 0, smile: .6, browOut: .5, armL: [-140, 20], handL: 'grip', armR: [126, 300] }, [
      { t: st_('j18') + .2, d: .4, look: [170, 640], smile: .2, browIn: .3 },
      { t: st_('h7'), d: .3, smile: .1, browIn: .5, lid: .1, headRoll: .05 },
      { t: WT('j19', 'Not') , d: .6, lid: .3, browIn: .8, smile: -.1 },                                                    // it lands
      { t: en_('j19') + .2, d: 1.0, armL: [-60, 230], handL: 'relax', smile: .45, lid: .2, look: [380, 760] },             // lowers the bell, softens
    ]);
    const J = actor('jesus', { x: 170, y: 790, s: 1.25, turn: .35, look: [470, 690], follow: .55, lid: .2, browIn: .6, smile: .1, armL: [-126, 300], armR: [126, 300] }, [
      { t: st_('j18') - .1, d: .5, look: [640, 610], smile: .2 }, { t: st_('j19'), d: .5, smile: .3, browIn: .3, lid: .15 }, { t: en_('j19') + .8, d: .6, look: [470, 690] },
    ]);
    const M = actor('marisol', { x: 470, y: 820, s: 1.2, turn: -.3, look: [170, 660], follow: .55, lid: .4, browIn: .9, smile: -.2, tearful: .5, armL: [-90, 200], handL: 'flat', armR: [90, 200], handR: 'flat' }, [
      { t: st_('j18') + .2, d: .6, look: [640, 610], lid: .2, browOut: .3 }, { t: en_('j19') + .6, d: .8, look: [170, 660], smile: .45, lid: .25 },
    ]);
    shot(tb - .05, t1, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 600, z: 1.05 });
      const L = LIGHT.candle(380, 960, 1.1);
      show(ctx, Hh, t, L, null, st => { st.top = (c, arms) => { const w = arms.L.w; c.save(); c.translate(w[0], w[1] - 30); c.fillStyle = '#e8c040'; c.beginPath(); c.moveTo(-28, 16); c.quadraticCurveTo(-28, -30, 0, -32); c.quadraticCurveTo(28, -30, 28, 16); c.fill(); c.fillStyle = '#a07a20'; c.fillRect(-34, 14, 68, 8); c.restore(); }; });
      show(ctx, M, t, L); show(ctx, J, t, L);
      tableFront(ctx, t, { num: '12', fill: .3, fill2: .3 });
      ding(ctx, t, tb, 560, 300);
      vignette(ctx, .45);
    }, 0);
  }
  // ===== 11. match cards =====
  {
    const t0 = st_('n3') - .5, t1 = st_('j20') + .02, tC = WT('h9', 'checked');
    const names = ['Kayla', 'Dana', 'Priya', 'Marisol', 'Host', 'Bartender', 'everyone else'];
    shot(t0, st_('h8') - .3, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 500, z: 1.3 }); ctx.fillStyle = 'rgba(10,5,8,.35)'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#c9a24a'; ctx.fillRect(210, 760, 300, 220); ctx.fillStyle = '#8a6a20'; ctx.fillRect(250, 760, 220, 18);
      for (let i = 0; i < 8; i++) { const p = clamp((t - t0 - .4 - i * .35) / .7); if (p <= 0) continue; ctx.save(); ctx.translate(lerp(i % 2 ? -100 : 820, 360, p), lerp(300 + i * 30, 770, p)); ctx.rotate((1 - p) * (i % 2 ? 2 : -2)); ctx.globalAlpha = p < 1 ? 1 : 0; ctx.fillStyle = '#fafaf4'; ctx.fillRect(-60, -40, 120, 80); ctx.fillStyle = '#d8283a'; ctx.fillRect(-60, -40, 120, 16); ctx.restore(); }
      vignette(ctx, .45);
    }, .4);
    const Hh = actor('host', { x: 520, y: 840, s: 1.2, turn: -.3, look: [520, 1000], follow: .6, lid: .2, browIn: .6, browOut: .6, smile: -.1, armL: [-120, 120], handL: 'hold', armR: [60, 120], handR: 'hold' }, [
      { t: WT('h8', 'weird'), d: .4, look: [190, 680], lid: -.1, browOut: 1, smile: .1 },
      { t: WT('h8', 'Including'), d: .3, smile: .45, lid: .25, headRoll: .06 }, { t: WT('h8', 'bartender'), d: .3, look: [700, 500] },
      { t: st_('h9'), d: .4, look: [190, 680], armL: [-200, -40], handL: 'hold', lid: -.12, browOut: 1, open: .1 },
    ]);
    const J = actor('jesus', Object.assign({}, jPod, { look: [520, 680], smile: .35 }), [
      { t: st_('j20'), d: .4, shrug: .8, armL: [-150, 140], handL: 'open', armR: [150, 140], handR: 'open', smile: .6, browOut: .4, headRoll: -.06 },
    ]);
    shot(st_('h8') - .3, t1 + 1.0, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 600, z: 1.1 });
      const L = LIGHT.bar(360, 300);
      // the bartender waving sheepishly in the back
      const wv = ramp(t, WT('h8', 'bartender'), WT('h8', 'bartender') + .3) * (1 - ramp(t, st_('h9'), st_('h9') + .4));
      if (wv > 0) { ctx.save(); ctx.globalAlpha = wv; ctx.fillStyle = '#2a2a2e'; ctx.beginPath(); ctx.ellipse(660, 560, 50, 90, 0, 0, TAU); ctx.fill(); ctx.fillStyle = '#e0b090'; ctx.beginPath(); ctx.arc(660, 450, 34, 0, TAU); ctx.fill(); ctx.strokeStyle = '#2a2a2e'; ctx.lineWidth = 16; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(690, 520); ctx.lineTo(720 + Math.sin(t * 10) * 12, 420); ctx.stroke(); ctx.restore(); }
      show(ctx, J, t, L); show(ctx, Hh, t, L);
      const pg = ctx.createLinearGradient(0, 1000, 0, 1280); pg.addColorStop(0, '#5a3420'); pg.addColorStop(1, '#1e100a'); ctx.fillStyle = pg; ctx.fillRect(0, 1010, W, 270);
      // his card: every box checked
      const ck = ramp(t, st_('h9') - .1, st_('h9') + .4);
      if (ck > 0) { ctx.save(); ctx.globalAlpha = ck; ctx.translate(360, 330); ctx.scale(lerp(.6, 1, ck), lerp(.6, 1, ck)); ctx.fillStyle = '#fafaf4'; roundRect(ctx, -200, -180, 400, 360, 16); ctx.fill(); ctx.fillStyle = '#d8283a'; ctx.fillRect(-200, -180, 400, 50); ctx.fillStyle = '#fff'; ctx.font = '800 26px Inter'; ctx.textAlign = 'center'; ctx.fillText('MATCH CARD · Jesus', 0, -145); ctx.textAlign = 'left';
        names.forEach((n, i) => { const y = -100 + i * 40; ctx.strokeStyle = '#2a2a2a'; ctx.lineWidth = 2.5; ctx.strokeRect(-170, y - 22, 26, 26); ctx.fillStyle = '#2a2a2a'; ctx.font = '600 24px Inter'; ctx.fillText(n, -130, y); if (t > st_('h9') + .2 + i * .12) { ctx.fillStyle = '#1a8a3a'; ctx.font = '900 28px Inter'; ctx.fillText('✓', -168, y + 2); } });
        ctx.restore(); }
      vignette(ctx, .4);
    }, 0);
  }
  // ===== 12. the room, chosen =====
  {
    const t0 = st_('j20') + 1.02, t1 = st_('morn') - .2;
    const people = [['kayla', 90, 900, .8], ['dana', 250, 880, .78], ['priya', 470, 880, .78], ['marisol', 630, 900, .8]].map(([n, x, y, s]) => actor(n, { x, y, s, look: [360, 560], follow: .6, lid: .15, smile: .5, browIn: .2, armL: [-126, 300], armR: [126, 300] }, [{ t: WT('n4', 'chosen', 1), d: .8, smile: .7, lid: .25 }]));
    const J = actor('jesus', { x: 360, y: 700, s: .95, look: 'cam', follow: .5, lid: .15, smile: .5, armL: [-150, 160], handL: 'open', armR: [150, 160], handR: 'open' });
    shot(t0, t1, (ctx, t) => {
      barRoom(ctx, t, { x: 360, y: 640, z: 1 });
      glow(ctx, 360, 600, 420, '#ffe0a0', .35 + .15 * ramp(t, WT('n4', 'chosen', 1), WT('n4', 'chosen', 1) + 1));
      show(ctx, J, t, Object.assign(LIGHT.candle(360, 900, 1.2), { rim: .6, rimColor: '#fff0c0' }));
      const L = LIGHT.candle(360, 700, 1); for (const p of people) show(ctx, p, t, L);
      tableFront(ctx, t, { glasses: false });
      vignette(ctx, .4);
    }, .5);
  }
  // ===== 13. morning: "Still here." =====
  {
    const t0 = st_('morn') - .2, t1 = TL.total + .5, tB = st_('morn') + .6;
    const M = actor('marisol', { x: 380, y: 950, s: 1.6, look: [160, 330], follow: .55, lid: .3, smile: .05, browIn: .3, armL: [-30, 120], handL: 'hold', angL: .9, armR: [60, 110], handR: 'hold', angR: -1.0 }, [
      { t: tB + .1, d: .4, look: [430, 1100], lid: .25 },                                                    // the phone buzzes; she looks down
      { t: tB + .9, d: .5, lid: -.08, browOut: .7, browIn: .5 },                                               // reads it: eyes widen
      { t: tB + 1.8, d: .5, smile: -.15, browIn: .9, tearful: .7 },                                            // lips press: moved
      { t: st_('m5') - .1, d: .6, smile: .6, squint: .35, lid: .2, browIn: .5 },                               // a laugh through tears
      { t: en_('m5') + .5, d: 1.2, look: [160, 330], smile: .55 },                                              // looks to the morning light
    ]);
    M.tr.base.tears = [{ side: -1, t0: st_('m5') + .1, dur: 3.2 }];
    shot(t0, t1, (ctx, t) => {
      ctx.drawImage(aptBG('dawn'), 0, 0); glow(ctx, 160, 300, 700, '#ffcf9a', .3);
      show(ctx, M, t, LIGHT.dawn(160, 320, 1.1), null, st => { st.top = (c, arms) => { const w = arms.L.w; c.save(); c.translate(w[0] - 10, w[1] - 30); c.fillStyle = '#e8e2d8'; roundRect(c, -30, -40, 60, 70, 10); c.fill(); c.strokeStyle = '#e8e2d8'; c.lineWidth = 8; c.beginPath(); c.arc(-34, -6, 16, Math.PI * .5, Math.PI * 1.5); c.stroke(); c.restore(); const r = arms.R.w; c.save(); c.translate(r[0] + 8, r[1] - 40); c.rotate(-.15 + (t > tB && t < tB + .6 ? Math.sin(t * 60) * .05 : 0)); c.fillStyle = '#1b1d22'; roundRect(c, -28, -52, 56, 104, 9); c.fill(); c.restore(); }; });
      const sl = easeOut(clamp((t - tB) / .45));
      if (sl > 0) { ctx.save(); ctx.translate(0, (1 - sl) * -240); ctx.globalAlpha = sl; ctx.shadowColor = 'rgba(0,0,0,.4)'; ctx.shadowBlur = 30; ctx.fillStyle = 'rgba(250,248,244,.97)'; roundRect(ctx, 40, 80, 640, 170, 30); ctx.fill(); ctx.shadowBlur = 0;
        ctx.fillStyle = '#a8261e'; ctx.beginPath(); ctx.arc(104, 165, 30, 0, TAU); ctx.fill(); ctx.fillStyle = '#e8c040'; ctx.font = '800 30px Inter'; ctx.textAlign = 'center'; ctx.fillText('J', 104, 176); ctx.textAlign = 'left';
        ctx.fillStyle = '#6a6470'; ctx.font = '600 22px Inter'; ctx.fillText('J · now', 150, 140); ctx.fillStyle = '#1e1a22'; ctx.font = '600 34px Inter'; ctx.fillText('Good morning. Still here.', 150, 192); ctx.restore(); }
      const a = ramp(t, en_('m5') + .6, en_('m5') + 1.4);
      if (a > 0) { ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.fillStyle = '#fff4dc'; ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 18; ctx.font = '600 66px "DejaVu Serif"'; ctx.fillText('Still here.', 360, 640); ctx.restore(); }
      vignette(ctx, .3);
    }, .4);
  }
}
