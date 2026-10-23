// ---------- cast ----------
const CAST = {
  leader: { name: 'The Chieftain', voice: 'LEADER', seed: 5, skin: '#c9967a', hair: '#8a3a1c', hairStyle: 'wavy', hairBack: true, beard: 'full', beardCol: '#7a3418', beardLen: .9, eye: '#3a5a6a', faceW: 1.04, jaw: 1.1, build: 1.12, paint: '#2a4aa0', noseW: 1.1,
    cloth: { type: 'tunic', color: '#5a4632', sleeveLen: 'long', neck: 8, belt: '#2a1a10' }, mantle: { color: '#3a4a32', tartan: ['#2f6a3a', '#9a2a24'] } },
  writer: { name: 'The Writer', voice: 'WRITER', seed: 3, skin: '#a8714f', hair: '#1c1410', hairStyle: 'curly', eye: '#3b2414', lip: '#8e5446', faceW: 1, jaw: 1.02, stubble: '#2a1c14',
    cloth: { type: 'hoodie', color: '#4a5a3c', sleeveLen: 'long' }, mantle: { color: '#2a3a4a', tartan: ['#2a3a7a', '#3a7a5a'] } },
  lonely: { name: 'lonely', voice: 'LONELY', seed: 77, skin: '#d8b090', hair: '#bdb8b0', hairStyle: 'bun', old: true, eye: '#4a5a6a', lip: '#a0706a', lashes: true, faceW: .92, jaw: .9, browW: 3, browCol: '#9a948c',
    cloth: { type: 'dress', color: '#5a5a6a', sleeveLen: 'long', neck: 6 }, headwear: { type: 'veil', color: '#6a7488' } },
  gold1: { name: 'official', voice: 'G1', seed: 41, skin: '#e0b090', hair: '#3b3330', hairStyle: 'roman', gray: true, eye: '#2a2a24', faceW: 1.08, jaw: 1.08, old: true, noseW: 1.15,
    cloth: { type: 'toga', color: '#e0b84a', sleeveLen: 'mid', neck: 6, stripe: '#8a2a5a' }, mantle: { color: '#f4e6b8' } },
  gold2: { name: 'official', voice: 'G2', seed: 43, skin: '#f0c8a8', hair: '#c9963c', hairStyle: 'ponytail', eye: '#3a5a7a', lip: '#c0605a', lashes: true, faceW: .93, jaw: .88, browW: 3.2,
    cloth: { type: 'toga', color: '#f0d070', sleeveLen: 'mid', neck: 6, stripe: '#b07020' }, mantle: { color: '#fff2c8' } },
  gold3: { name: 'official', voice: 'G3', seed: 47, skin: '#8a5a3c', hair: '#141010', hairStyle: 'short', eye: '#2a1810', faceW: 1.02, jaw: 1.04,
    cloth: { type: 'toga', color: '#d8a83a', sleeveLen: 'mid', neck: 6, stripe: '#6a2a8a' }, mantle: { color: '#f2e2b0' } },
};
// the brokenhearted: a varied crowd
const SKINS = ['#e0b08c', '#c48d68', '#a8714f', '#8a5a3c', '#6e4630', '#d8a888', '#b88058', '#f0c8a8'];
const HAIRS = [['#1c1410', 'curly'], ['#2b1d14', 'wavy'], ['#c9963c', 'ponytail'], ['#141010', 'afro'], ['#5a3a20', 'short'], ['#3a2a1c', 'roman'], ['#8a3a1c', 'bun'], ['#d8c08a', 'short']];
const CLOTHS = ['#5a4a3a', '#4a5a4a', '#6a4a4a', '#4a4a5a', '#7a6a4a', '#5a5040', '#3e4a3a', '#6a5a6a'];
for (let i = 0; i < 12; i++) {
  const h = HAIRS[(i * 3) % 8];
  CAST['c' + i] = { name: 'crowd', voice: 'C' + i, seed: 200 + i * 7, skin: SKINS[(i * 5) % 8], hair: h[0], hairStyle: h[1], eye: '#2a1c14', faceW: .92 + (i % 4) * .05, jaw: .9 + (i % 3) * .08, lashes: i % 2 === 1,
    beard: i % 5 === 2 ? 'short' : null, beardLen: .3, child: i === 7,
    cloth: { type: 'tunic', color: CLOTHS[i % 8], sleeveLen: 'long', neck: 6 }, mantle: i % 3 === 0 ? { color: '#3a3a40', tartan: [['#5a2a2a', '#2a3a5a'][i % 2], '#3a5a3a'] } : null };
}
// ---------- helpers ----------
const st_ = id => LINE(id).start, en_ = id => LINE(id).end;
function actor(name, base, keys) { return { C: CAST[name], tr: new Track(Object.assign({}, BASE_STATE, base), keys || []) }; }
function applyCam(c, cam) { c.translate(W / 2, H / 2); c.scale(cam.z, cam.z); c.translate(-cam.x, -cam.y); }
function toScreen(cam, x, y) { return cam ? [(x - cam.x) * cam.z + W / 2, (y - cam.y) * cam.z + H / 2] : [x, y]; }
function show(ctx, a, t, light, cam, extra) {
  const st = resolve(a.C, a.tr, t); if (extra) extra(st);
  drawLit(ctx, c => { c.save(); if (cam) applyCam(c, cam); c.globalAlpha = st.alpha; drawChar(c, a.C, st, t); c.restore(); }, light);
  return st;
}
function showMany(ctx, list, t, light, cam) { // one lighting pass for a whole group (crowds)
  drawLit(ctx, c => { c.save(); if (cam) applyCam(c, cam); for (const a of list) { const st = resolve(a.C, a.tr, t); c.globalAlpha = st.alpha; drawChar(c, a.C, st, t); } c.restore(); }, light);
}
const LIGHT = {
  dawn: (x, y, k = 1) => ({ x, y, color: '#ffc58a', str: .3 * k, rad: 800, dark: .3, near: '#fff6ea', amb: '#4a3a5a', fall: 1100, rim: .45 * k, rimColor: '#ffd79a', rimDx: x < 360 ? 6 : -6, rimDy: 3 }),
  fire: (x, y, k = 1) => ({ x, y, color: '#ff9a40', str: .38 * k, rad: 650, dark: .5, near: '#fff0d8', amb: '#2e2830', fall: 950, rim: .55 * k, rimColor: '#ffae55', rimDx: x < 360 ? 6 : -6, rimDy: 0 }),
  gold: (x, y, k = 1) => ({ x, y, color: '#ffe08a', str: .25 * k, rad: 700, dark: .25, near: '#fffaf0', amb: '#6a5a50', fall: 1000, rim: .35 * k, rimColor: '#fff0b0', rimDx: x < 360 ? 6 : -6, rimDy: 0 }),
  storm: (x, y) => ({ x, y, color: '#9aaacf', str: .12, rad: 700, dark: .5, near: '#d0d8ee', amb: '#262a3a', fall: 900, rim: .35, rimColor: '#b0c0ff', rimDx: x < 360 ? 6 : -6, rimDy: 0 }),
};
const SHOTS = [], LABELS = [], SUPPRESS = new Set();
function shot(t0, t1, draw, xin = 0) { SHOTS.push({ t0, t1, draw, xin }); }
const shake = (ctx, amt, t) => ctx.translate((hash(Math.floor(t * 30)) - .5) * amt, (hash(Math.floor(t * 30) + 5) - .5) * amt);
function sky(ctx, mode, cam, t, cl = .2) { ctx.save(); if (cam) applyCam(ctx, cam); ctx.drawImage(highlandBG(mode), -200, -200); ctx.restore(); clouds(ctx, t, cl); }
function crowdRow(names, x0, x1, y, s, base, keysFn) {
  return names.map((n, i) => { const x = lerp(x0, x1, names.length > 1 ? i / (names.length - 1) : .5) + (hash(i + y) - .5) * 30; return actor(n, Object.assign({ x, y: y + (hash(i * 3 + y) - .5) * 16, s: s * (.95 + hash(i + 2) * .1), look: [360, 300], follow: .6, armL: [-126, 300], armR: [126, 300] }, base), keysFn ? keysFn(i, x) : []); });
}
const HOLD_SWORD = { armR: [80, 120], handR: 'grip', angR: -1.5 };
function sword(c, arms, len = 260) { const w = arms.R.w; c.save(); c.translate(w[0] + 8, w[1] - 6); c.rotate(-Math.PI / 2 + .12); const g = c.createLinearGradient(0, -6, 0, 6); g.addColorStop(0, '#9aa0a8'); g.addColorStop(.5, '#f0f4f8'); g.addColorStop(1, '#7a8088'); c.fillStyle = '#4a3018'; c.fillRect(-40, -6, 50, 12); c.fillStyle = '#c9a24a'; c.fillRect(8, -26, 12, 52); c.fillStyle = g; c.beginPath(); c.moveTo(20, -8); c.lineTo(20 + len, -3); c.lineTo(32 + len, 0); c.lineTo(20 + len, 3); c.lineTo(20, 8); c.fill(); c.restore(); }

function buildShots() {
  // ===== 1. the hill: protocol initiates (FIRST FRAME) =====
  {
    const t1 = st_('a2') - .4;
    const A = actor('writer', { x: 360, y: 820, s: 1.55, look: [400, 1000], follow: .5, lid: .3, browIn: .4, armR: [30, 112], handR: 'hold', holdR: 'phoneBack', angR: -1.3, armL: [-24, 150], handL: 'hold', angL: 1.1 }, [
      { t: WT('a1', 'Weaponize') - .2, d: .7, look: [360, 300], lid: .05, browIn: .2, browOut: .5, frown: .3 },   // looks up, resolve dawning
      { t: WT('a1', 'wound'), d: .5, browIn: -.2, frown: .6, smile: -.1, lid: .15 },
    ]);
    shot(0, t1, (ctx, t) => {
      sky(ctx, 'dawn', null, t, .22);
      show(ctx, A, t, LIGHT.dawn(470, 640, 1.1));
      windGrass(ctx, t);
      hud(ctx, ['// INITIATING PROTOCOL //', 'WEAPONIZE', 'THE WOUND'], t, st_('a1') - .1, 150);
      vignette(ctx, .45);
    });
    LABELS.push({ t0: 0, text: 'The Writer', x: 360, y: 480, dur: 1.4 });
  }
  // ===== 2. the Chieftain arrives =====
  const twoHill = (t0, t1, kL, kW, opts = {}) => {
    const L = actor('leader', Object.assign({ x: 230, y: 830, s: 1.35, turn: .25, look: [520, 680], follow: .65, lid: .15, browIn: -.1, frown: .25, smile: .05, armL: [-126, 300], armR: [126, 300], gest: 1.6 }, opts.L || {}), kL);
    const Wr = actor('writer', Object.assign({ x: 540, y: 870, s: 1.25, turn: -.25, look: [230, 680], follow: .65, lid: .2, browIn: .45, armL: [-126, 300], armR: [126, 300] }, opts.W || {}), kW);
    shot(t0, t1, (ctx, t) => {
      sky(ctx, opts.mode || 'dawn', { x: 360, y: 640, z: 1.05 }, t, .2);
      if (opts.under) opts.under(ctx, t);
      show(ctx, Wr, t, LIGHT.dawn(560, 560)); show(ctx, L, t, LIGHT.dawn(560, 560));
      windGrass(ctx, t); if (opts.over) opts.over(ctx, t);
      vignette(ctx, .45);
    }, opts.xin || 0);
  };
  twoHill(st_('a2') - .4, st_('a4') - .35, [
    { t: st_('a2') - .4, d: .01, x: 120, alpha: 1 }, { t: st_('a2') - .39, d: 1.2, x: 230, ease: ease },     // strides in
    { t: WT('a2', 'pain'), d: .4, browIn: -.3, frown: .5 },
    { t: WT('a2', 'private'), d: .5, smile: -.15, armL: [-90, 140], handL: 'point', gest: 1 },                 // points at the phone
    { t: st_('a3'), d: .5, armL: [-126, 300], handL: 'relax', frown: .2 },
  ], [
    { t: st_('a2') - .2, d: .6, look: [200, 640], lid: .05, browOut: .6, browIn: .3 },                     // startled by the stranger
    { t: WT('a2', 'logbook'), d: .5, look: [430, 1000], lid: .35 },                                          // glance at his phone
    { t: st_('a3') - .1, d: .5, look: [230, 660], lid: .15, browIn: .7, frown: .2 },
  ], { W: { armR: [30, 112], handR: 'hold', holdR: 'phoneBack', angR: -1.3, armL: [-24, 150], handL: 'hold', angL: 1.1 } });
  LABELS.push({ t0: st_('a2') + .3, text: 'The Chieftain', x: 230, y: 470 });
  // ===== 3. the forge: pain into expression =====
  {
    const t0 = st_('a4') - .35, t1 = st_('a5') - .4;
    const hits = [WT('a4', 'forge'), WT('a4', 'intense'), WT('a4', 'posts'), WT('a4', 'conversations'), WT('a4', 'art'), WT('a4', 'presence')];
    const keys = [];
    for (const h of hits) keys.push({ t: h - .45, d: .3, armR: [200, -20] }, { t: h - .12, d: .12, armR: [168, 205] });
    const L = actor('leader', { x: 260, y: 700, s: 1.25, look: [470, 960], follow: .6, lid: .25, frown: .5, browIn: -.4, armR: [168, 205], handR: 'grip', angR: 0, armL: [-60, 160], handL: 'grip', nod: .4 }, keys.concat([
      { t: WT('a4', 'longer'), d: .6, look: [360, 400], frown: .2 },
    ]));
    const icons = [['post', WT('a4', 'posts')], ['talk', WT('a4', 'conversations')], ['art', WT('a4', 'art')], ['you', WT('a4', 'presence')]];
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#140c08'; ctx.fillRect(0, 0, W, H);
      glow(ctx, 480, 1000, 600, '#ff7a2a', .35);
      bricksCached(ctx);
      let la;
      show(ctx, L, t, LIGHT.fire(480, 980, 1.2), null, st => { st.top = (c, arms) => hammer(c, arms.R); });
      anvil(ctx, 470, 1010, 1.1);
      const g = ctx.createLinearGradient(380, 0, 600, 0); g.addColorStop(0, '#ff8a2a'); g.addColorStop(.5, '#fff0a0'); g.addColorStop(1, '#ff6a1a');
      ctx.fillStyle = g; roundRect(ctx, 380, 928, 210, 16, 8); ctx.fill(); glow(ctx, 485, 936, 120, '#ffb040', .5);
      for (const h of hits) sparks(ctx, 470, 928, t, h, 26);
      icons.forEach(([k, ti], i) => {
        const p = clamp((t - ti) / 1.0); if (p <= 0) return;
        const x = 140 + i * 150, y = lerp(960, 330 + (i % 2) * 70, easeOut(p));
        ctx.save(); ctx.globalAlpha = Math.min(1, p * 3) * (1 - ramp(t, WT('a4', 'healing') - .2, WT('a4', 'healing') + .5) * .4); ctx.translate(x, y);
        glow(ctx, 0, 0, 70, '#ffb040', .4); ctx.fillStyle = '#fff3d6'; ctx.strokeStyle = '#fff3d6'; ctx.lineWidth = 5;
        if (k === 'post') { roundRect(ctx, -30, -38, 60, 76, 8); ctx.stroke(); ctx.fillRect(-18, -22, 36, 5); ctx.fillRect(-18, -8, 36, 5); ctx.fillRect(-18, 6, 24, 5); }
        if (k === 'talk') { roundRect(ctx, -36, -28, 50, 34, 12); ctx.stroke(); roundRect(ctx, -10, -2, 46, 32, 12); ctx.fill(); }
        if (k === 'art') { ctx.beginPath(); ctx.moveTo(-26, 30); ctx.lineTo(22, -30); ctx.stroke(); ctx.beginPath(); ctx.ellipse(-28, 32, 10, 6, -.8, 0, TAU); ctx.fill(); }
        if (k === 'you') { ctx.beginPath(); ctx.arc(0, -16, 14, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.ellipse(0, 26, 26, 20, 0, Math.PI, 0); ctx.fill(); }
        ctx.restore();
      });
      // "healing journey" signpost burns away
      const hp = ramp(t, WT('a4', 'healing') - .1, WT('a4', 'healing') + .2), hb = ramp(t, WT('a4', 'journey') + .3, WT('a4', 'journey') + 1.6);
      if (hp > 0 && hb < 1) { ctx.save(); ctx.globalAlpha = hp * (1 - hb); ctx.translate(560, 560); ctx.rotate(-.05); ctx.fillStyle = mix('#c9b48a', '#2a1a10', hb); ctx.fillRect(-120, -30, 240, 60); ctx.fillStyle = '#4a3a2a'; ctx.fillRect(-6, 30, 12, 120); ctx.fillStyle = mix('#3a2a1a', '#ff8a3a', hb); ctx.font = 'italic 600 30px "DejaVu Serif"'; ctx.textAlign = 'center'; ctx.fillText('healing journey', 0, 10); ctx.restore(); if (hb > 0) fire(ctx, 560, 600, 200, t, hb * (1 - hb) * 2); }
      embers(ctx, t, 30, .7);
      vignette(ctx, .55);
    }, .3);
  }
  // ===== 4. banner: communiques from the front line =====
  {
    const t0 = st_('a5') - .4, t1 = st_('b1') - .35, tR = WT('a5', 'revolution');
    const L = actor('leader', Object.assign({ x: 300, y: 850, s: 1.3, look: [500, 300], follow: .55, lid: .05, frown: .3, browIn: -.2, browOut: .4, armL: [-90, -40], handL: 'grip', angL: -.4, armR: [60, 230] }), [
      { t: tR - .2, d: .4, open: .3, smile: .2, browOut: .8, frown: .1, armR: [160, 10], handR: 'grip' },
    ]);
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'gold', { x: 360, y: 700, z: 1.1 }, t, .25);
      // ravens carrying glowing letters to the horizon
      for (let k = 0; k < 6; k++) { const p = ((t - t0) * .25 + k / 6) % 1, x = lerp(300, 760, p) + k * 20, y = lerp(560, 200 + k * 30, p); ctx.save(); ctx.translate(x, y); ctx.scale(.6 + p * -.3, .6 + p * -.3); ctx.fillStyle = '#141018'; const f = Math.sin(t * 12 + k) * 18; ctx.beginPath(); ctx.moveTo(-40, f); ctx.quadraticCurveTo(-14, -6, 0, 0); ctx.quadraticCurveTo(14, -6, 40, f); ctx.quadraticCurveTo(10, 6, 0, 6); ctx.quadraticCurveTo(-10, 6, -40, f); ctx.fill(); ctx.fillStyle = '#ffe6a0'; ctx.fillRect(-6, 8, 12, 9); glow(ctx, 0, 12, 18, '#ffcf6a', .5); ctx.restore(); }
      let la;
      show(ctx, L, t, LIGHT.dawn(560, 500, 1.2), null, st => { st.top = (c, arms) => { la = arms; }; });
      // banner pole in the raised fist
      if (la) { const st = resolve(L.C, L.tr, t); const w = la.L.w, wx = st.x + w[0] * st.s, wy = st.y + w[1] * st.s; flag(ctx, wx, wy - 330, 300, 170, t, '#7a1a1a', true, ramp(t, t0 + .2, t0 + 1.4)); ctx.fillStyle = '#3a2a1c'; ctx.fillRect(wx - 4, wy - 330, 9, 420); }
      windGrass(ctx, t);
      vignette(ctx, .4);
    }, .3);
  }
  // ===== 5. "who are we fighting?" =====
  twoHill(st_('b1') - .35, st_('b2') - .3, [{ t: 0, look: [520, 680] }, { t: en_('b1'), d: .6, look: [500, 300], frown: .6, browIn: -.6 }], [
    { t: st_('b1'), d: .4, browIn: .8, browOut: .3, open: 0 },
  ], { W: { armL: [-80, 160], handL: 'open', armR: [80, 160], handR: 'open', gest: 1.5 } });
  // ===== 6. the citadel: the machine, polite silence =====
  {
    const t0 = st_('b2') - .3, tS = WT('b2', 'successful') - .2, tSil = WT('b2', 'polite') - .1, t1 = st_('b3') - .4;
    shot(t0, tS, (ctx, t) => {
      sky(ctx, 'storm', { x: 360, y: 640, z: 1 }, t, .12);
      citadel(ctx, 360, 900, .95, t, { gears: 1, screens: 0 });
      ctx.fillStyle = 'rgba(20,20,30,.2)'; ctx.fillRect(0, 0, W, H);
      windGrass(ctx, t); vignette(ctx, .55);
    }, .4);
    const G = [actor('gold1', { x: 360, y: 760, s: 1.15, look: [600, 640], follow: .6, lid: .5, smile: .2, armL: [-40, 200], armR: [60, 150], handR: 'hold' }, [
      { t: tSil, d: .6, look: 'cam', follow: .5, lid: .35, smile: .15, armR: [10, -10], handR: 'point', angR: -.2 },   // finger to his lips: shh
    ]), actor('gold2', { x: 130, y: 800, s: .95, look: [360, 640], follow: .6, lid: .45, smile: .4 }, [{ t: WT('b2', 'avoidant'), d: .6, look: [-100, 600], lid: .5 }]),
      actor('gold3', { x: 600, y: 800, s: .95, look: [360, 640], follow: .6, lid: .4, smile: .3 }, [{ t: WT('b2', 'avoidant'), d: .6, look: [900, 600] }])];
    shot(tS, t1, (ctx, t) => {
      sky(ctx, 'gold', { x: 360, y: 400, z: 1.3 }, t, .2);
      // golden rampart in front of them
      showMany(ctx, [G[1], G[2]], t, LIGHT.gold(360, 300)); show(ctx, G[0], t, LIGHT.gold(360, 300));
      const g = ctx.createLinearGradient(0, 960, 0, 1280); g.addColorStop(0, '#e8c46a'); g.addColorStop(1, '#7a5a20'); ctx.fillStyle = g; ctx.fillRect(0, 980, W, 300);
      for (let k = 0; k < 9; k++) ctx.fillRect(k * 86, 940, 50, 44);
      gear(ctx, 600, 1150, 70, t * .6, 1); gear(ctx, 470, 1190, 44, -t * .9, 1);
      vignette(ctx, .4);
    }, 0);
    LABELS.push({ t0: tS + .3, text: 'The ones who have "made it"', x: 360, y: 500 });
  }
  // ===== 7. scripts of quiet: alone in therapy, in journals =====
  {
    const t0 = st_('b3') - .4, tInc = WT('b3', 'inconvenienced') - .3, t1 = st_('b4') - .35;
    const P = [['c1', 140, 'journal'], ['c4', 360, 'therapy'], ['c6', 580, 'journal']].map(([n, x, k], i) => actor(n, { x, y: 790, s: .78, look: [x, 1000], follow: .6, lid: .55, browIn: .8, smile: -.3, headPitch: .1, armL: [-40, 160], armR: [40, 160], handL: 'hold', handR: k === 'therapy' ? 'relax' : 'pen', angL: .9 }, [
      { t: WT('b3', 'quietly') + i * .2, d: 1, lid: .7, headPitch: .2 },
    ]));
    shot(t0, tInc, (ctx, t) => {
      ctx.fillStyle = '#0c0a10'; ctx.fillRect(0, 0, W, H);
      // three small lit cells in the citadel's shadow
      for (let i = 0; i < 3; i++) { const x = 40 + i * 220; ctx.fillStyle = '#231c24'; ctx.fillRect(x, 440, 200, 520); glow(ctx, x + 100, 820, 180, '#ffb35c', .25); ctx.strokeStyle = '#3a3040'; ctx.lineWidth = 8; ctx.strokeRect(x, 440, 200, 520); }
      ctx.save(); ctx.beginPath(); for (let i = 0; i < 3; i++) ctx.rect(44 + i * 220, 444, 192, 512); ctx.clip();
      showMany(ctx, P, t, LIGHT.fire(360, 900, .7));
      // journals, and a ticking clock for "therapy"
      for (const i of [0, 2]) { const x = 140 + (i - 1) * 0 + (i === 0 ? 0 : 440); ctx.fillStyle = '#6a3a2a'; ctx.fillRect(x - 40, 900, 80, 56); ctx.fillStyle = '#efe4c8'; ctx.fillRect(x - 36, 904, 72, 48); }
      ctx.restore();
      ctx.fillStyle = '#efe4c8'; ctx.beginPath(); ctx.arc(360, 520, 30, 0, TAU); ctx.fill(); ctx.strokeStyle = '#222'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(360, 520); ctx.lineTo(360 + Math.cos(t * 2) * 20, 520 + Math.sin(t * 2) * 20); ctx.stroke(); ctx.beginPath(); ctx.moveTo(360, 520); ctx.lineTo(372, 510); ctx.stroke();
      ctx.fillStyle = 'rgba(232,220,200,.85)'; ctx.font = '600 26px Inter'; ctx.textAlign = 'center';
      if (t > WT('b3', 'therapy') - .2) ctx.fillText('therapy', 360, 420);
      if (t > WT('b3', 'journals') - .2) { ctx.fillText('journal', 140, 420); ctx.fillText('journal', 580, 420); }
      ctx.textAlign = 'left';
      vignette(ctx, .5);
    }, .3);
    const G = actor('gold1', { x: 360, y: 860, s: 1.5, look: [420, 1080], follow: .6, lid: .55, smile: .25, armL: [-50, 160], armR: [60, 160], handR: 'hold' }, [
      { t: tInc + .6, d: .3, open: .6, lid: .9, headPitch: -.1 }, { t: tInc + 1.3, d: .5, open: 0, lid: .55, headPitch: 0 },   // a yawn
    ]);
    shot(tInc, t1, (ctx, t) => {
      sky(ctx, 'gold', { x: 360, y: 300, z: 1.5 }, t, .2);
      show(ctx, G, t, LIGHT.gold(300, 300));
      for (let k = 0; k < 7; k++) { ctx.fillStyle = '#e8c04a'; ctx.beginPath(); ctx.ellipse(300 + k * 18, 1110 - k * 9, 34, 11, 0, 0, TAU); ctx.fill(); ctx.strokeStyle = '#8a6a20'; ctx.lineWidth = 2; ctx.stroke(); }
      vignette(ctx, .4);
    }, 0);
  }
  // ===== 8. "Keep it private. Keep it manageable." =====
  {
    const t0 = st_('b4') - .35, t1 = st_('b5') - .35;
    const A = actor('writer', { x: 360, y: 900, s: 2.1, look: [360, 1100], follow: .5, lid: .45, browIn: .7, smile: -.35, armL: [-60, 170], armR: [60, 170], handL: 'hold', handR: 'hold', angL: .8, angR: -.8 }, [
      { t: WT('b4', 'manageable'), d: .6, lid: .2, look: [380, 560], browIn: .2, frown: .55, smile: -.4 },   // bitter recognition
    ]);
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'storm', { x: 360, y: 500, z: 1.4 }, t, .12);
      show(ctx, A, t, LIGHT.storm(560, 500), null, st => { st.mid = (c, arms) => { const a = arms.L.w, b = arms.R.w, k = ramp(t, WT('b4', 'Keep', 1), WT('b4', 'Keep', 1) + .6); c.fillStyle = '#6a3a2a'; const w = Math.abs(b[0] - a[0]) * (1 - k * .5) + 30; c.fillRect((a[0] + b[0]) / 2 - w / 2, (a[1] + b[1]) / 2 - 50, w, 90); c.fillStyle = '#efe4c8'; if (k < .9) c.fillRect((a[0] + b[0]) / 2 - w / 2 + 6, (a[1] + b[1]) / 2 - 44, w - 12, 78); }; });
      vignette(ctx, .55);
    }, 0);
  }
  // ===== 9. the silent army: money, power, status =====
  {
    const t0 = st_('b5') - .35, t1 = st_('c1') - .4;
    const names = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c8'];
    const back = crowdRow(names.slice(0, 4), 120, 600, 760, .75, { lid: .7, headPitch: .25, browIn: .7, smile: -.25, look: null });
    const front = crowdRow(names.slice(4), 80, 640, 930, 1.0, { lid: .7, headPitch: .28, browIn: .8, smile: -.3, look: null });
    const icons = [['coin', WT('b5', 'money')], ['crown', WT('b5', 'power')], ['laurel', WT('b5', 'status')]];
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'storm', { x: 360, y: 640, z: 1.05 }, t, .12);
      citadel(ctx, 360, 640, .45, t, { gears: 1 });
      icons.forEach(([k, ti], i) => { const a = ramp(t, ti - .1, ti + .3); if (a <= 0) return; const x = 210 + i * 150, y = 200; ctx.save(); ctx.globalAlpha = a; glow(ctx, x, y, 80, '#ffd27a', .5); ctx.fillStyle = '#ffd86a'; ctx.strokeStyle = '#ffd86a'; ctx.lineWidth = 6;
        if (k === 'coin') { ctx.beginPath(); ctx.arc(x, y, 30, 0, TAU); ctx.fill(); ctx.fillStyle = '#a07a20'; ctx.font = '700 34px Inter'; ctx.textAlign = 'center'; ctx.fillText('$', x, y + 12); }
        if (k === 'crown') { ctx.beginPath(); ctx.moveTo(x - 34, y + 20); ctx.lineTo(x - 34, y - 20); ctx.lineTo(x - 16, y); ctx.lineTo(x, y - 26); ctx.lineTo(x + 16, y); ctx.lineTo(x + 34, y - 20); ctx.lineTo(x + 34, y + 20); ctx.fill(); }
        if (k === 'laurel') { for (const s of [-1, 1]) for (let j = 0; j < 5; j++) { ctx.beginPath(); ctx.ellipse(x + s * (22 - j * 2), y + 20 - j * 11, 9, 5, s * (.9 - j * .2), 0, TAU); ctx.fill(); } }
        ctx.restore(); });
      showMany(ctx, back, t, LIGHT.storm(360, 300)); showMany(ctx, front, t, LIGHT.storm(360, 300));
      rainB(ctx, t, .3);
      vignette(ctx, .55);
    }, .3);
  }
  // ===== 10. the new mission: the rally =====
  {
    const t0 = st_('c1') - .4, t1 = st_('c2') - .35, tm = WT('c1', 'Communicate');
    const L = actor('leader', Object.assign({ x: 360, y: 640, s: 1.05, look: [360, 1000], follow: .55, lid: .1, frown: .4, browIn: -.4, browOut: .3, armL: [-60, 230], gest: 2 }, HOLD_SWORD), [
      { t: WT('c1', 'mission'), d: .5, armR: [150, -60], angR: -1.2, open: .2 },        // raises the sword
      { t: tm, d: .5, armR: [80, 120], look: [200, 1000] }, { t: WT('c1', 'systemic'), d: .5, look: [520, 1000], armL: [-150, 60], handL: 'open' },
    ]);
    const crowd = crowdRow(['c0', 'c2', 'c5', 'c9', 'c3', 'c10'], 30, 690, 1100, 1.0, { look: [360, 560], lid: .6, headPitch: .25, browIn: .7, smile: -.2 }, (i) => [{ t: tm + i * .25, d: .9, headPitch: 0, lid: .25, browIn: .4, smile: 0 }]);
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'dawn', { x: 360, y: 640, z: 1 }, t, .2);
      // a great rock to stand on
      ctx.fillStyle = '#2a2430'; ctx.beginPath(); ctx.moveTo(150, H); ctx.lineTo(210, 880); ctx.lineTo(300, 840); ctx.lineTo(450, 850); ctx.lineTo(540, 900); ctx.lineTo(600, H); ctx.fill();
      let la; show(ctx, L, t, LIGHT.dawn(560, 500, 1.2), null, st => { st.top = (c, arms) => sword(c, arms); });
      ctx.fillStyle = '#2a2430'; ctx.fillRect(150, 960, 450, 320);
      showMany(ctx, crowd, t, LIGHT.dawn(360, 300, .6));
      vignette(ctx, .45);
    }, .3);
  }
  // ===== 11. pound on the gilded door until the hinges crack =====
  {
    const t0 = st_('c2') - .35, t1 = st_('c3') - .4, tP = WT('c2', 'pound'), tC = WT('c2', 'crack');
    const beats = []; for (let b = tP; b < t1; b += .95) beats.push(b);
    shot(t0, t1, (ctx, t) => {
      let last = -9; for (const b of beats) if (b <= t) last = b; const sinceHit = t - last;
      ctx.save(); if (sinceHit < .25) shake(ctx, 14 * (1 - sinceHit / .25), t);
      sky(ctx, 'storm', { x: 360, y: 640, z: 1 }, t, .1);
      const crack = ramp(t, tC - 1.6, tC + .8);
      citadel(ctx, 360, 880, 1.1, t, { crack, shake: sinceHit < .2 ? 1 : 0 });
      // the ram: a log carried by the crowd, swinging into the door
      const ph = clamp(sinceHit / .95), swing = t < tP ? 0 : (ph < .15 ? 1 - ph / .15 : easeIO((ph - .15) / .85));
      // the ram seen end-on: the log's butt swings back toward us, then into the door
      const rr = 46 + swing * 46, rx = 360, ry = 860 + swing * 90;
      ctx.save(); ctx.translate(rx, ry);
      ctx.fillStyle = '#4a2e18'; ctx.beginPath(); ctx.ellipse(0, 18, rr * 1.05, rr * .9, 0, 0, TAU); ctx.fill();
      const rg = ctx.createRadialGradient(0, 0, 4, 0, 0, rr); rg.addColorStop(0, '#c08a5a'); rg.addColorStop(1, '#7a5030'); ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(0, 0, rr, 0, TAU); ctx.fill();
      ctx.strokeStyle = 'rgba(60,35,15,.6)'; ctx.lineWidth = 2; for (let k = 1; k < 5; k++) { ctx.beginPath(); ctx.arc(2, 2, rr * k / 5, 0, TAU); ctx.stroke(); }
      ctx.strokeStyle = '#5a5a60'; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(0, 0, rr - 4, 0, TAU); ctx.stroke();
      ctx.restore();
      // the crowd heaving it, arms raised to the log
      for (let k = 0; k < 6; k++) { const x = 70 + k * 116, lean = swing * (k < 3 ? 1 : -1) * 6, y = 1030 + swing * 24;
        ctx.fillStyle = '#2c2634'; ctx.strokeStyle = '#2c2634'; ctx.lineWidth = 22; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(x + lean, y + 30); ctx.lineTo(lerp(x, rx, .55), ry + 30); ctx.stroke();
        ctx.beginPath(); ctx.arc(x + lean, y - 50, 36, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.ellipse(x + lean, y + 90, 74, 120, 0, 0, TAU); ctx.fill();
        ctx.fillStyle = 'rgba(255,200,140,.25)'; ctx.beginPath(); ctx.arc(x + lean - 8, y - 58, 28, Math.PI * 1.1, Math.PI * 1.6); ctx.lineTo(x + lean, y - 50); ctx.fill(); }
      ctx.restore();
      if (sinceHit < .12) { ctx.fillStyle = `rgba(255,240,200,${.25 * (1 - sinceHit / .12)})`; ctx.fillRect(0, 0, W, H); }
      vignette(ctx, .5);
    }, .2);
  }
  // ===== 12. doubt, and the answer =====
  {
    const t0 = st_('c3') - .4, tD = WT('c4', 'brokenhearted') - .3, t1 = st_('c5') - .3;
    const L = actor('leader', { x: 250, y: 900, s: 1.7, turn: .25, look: [560, 660], follow: .6, lid: .2, browIn: .3, frown: .2, armL: [-50, 230], armR: [50, 230], nod: .6 }, [
      { t: st_('c4'), d: .4, browIn: .5, frown: 0, smile: -.05 },                                              // "Aye." gentle
      { t: WT('c4', 'desperately'), d: .5, look: [-100, 700], follow: .7, lid: .3 },
      { t: WT('c4', 'Ignore'), d: .5, look: [560, 660], frown: .5, browIn: -.4 },
      { t: WT('c4', 'illiteracy'), d: .5, frown: .7 },
    ]);
    const Wr = actor('writer', { x: 590, y: 960, s: 1.6, turn: -.25, look: [250, 640], follow: .6, lid: .35, browIn: .8, smile: -.25, armL: [-40, 230], armR: [40, 230] }, [
      { t: WT('c3', 'speak'), d: .5, look: [600, 1150], lid: .5 },                                             // one slow look down
      { t: WT('c3', 'abandoned'), d: .6, look: [250, 640], lid: .3, browIn: 1, tearful: .5 },
      { t: st_('c4') + .4, d: .6, browIn: .6, tearful: .3 },
    ]);
    shot(t0, tD, (ctx, t) => {
      sky(ctx, 'dawn', { x: 360, y: 450, z: 1.5 }, t, .2);
      show(ctx, Wr, t, LIGHT.dawn(500, 300)); show(ctx, L, t, LIGHT.dawn(500, 300));
      vignette(ctx, .5);
    }, .3);
    const crowd = crowdRow(['c1', 'c3', 'c5', 'c7', 'c9', 'c11'], 60, 660, 900, 1.05, { lid: .75, headPitch: .3, browIn: .9, smile: -.3, look: null });
    shot(tD, t1, (ctx, t) => {
      sky(ctx, 'storm', null, t, .1);
      showMany(ctx, crowd, t, LIGHT.storm(360, 300)); rainB(ctx, t, .3); vignette(ctx, .55);
    }, 0);
    // c5: heads lift
    const crowd2 = crowdRow(['c1', 'c3', 'c5', 'c7', 'c9', 'c11'], 60, 660, 900, 1.05, { lid: .75, headPitch: .3, browIn: .9, smile: -.3, look: null }, (i) => [
      { t: WT('c5', 'lift') - .3 + [3, 1, 4, 0, 5, 2][i] * .28, d: .9, headPitch: -.05, lid: .1, browIn: .2, browOut: .4, smile: .1, look: [360, 350] },
    ]);
    shot(t1, st_('d1') - .5, (ctx, t) => {
      const k = ramp(t, WT('c5', 'lift'), WT('c5', 'lift') + 1.8);
      sky(ctx, 'storm', null, t, .1);
      ctx.save(); ctx.globalAlpha = k; ctx.drawImage(highlandBG('dawn'), -200, -200); ctx.restore();
      showMany(ctx, crowd2, t, k > .3 ? LIGHT.dawn(360, 200, k) : LIGHT.storm(360, 300));
      if (k < 1) rainB(ctx, t, .3 * (1 - k));
      vignette(ctx, .45);
    }, 0);
  }
  // ===== 13. TACTICAL OBJECTIVE: the platitude =====
  {
    const t0 = st_('d1') - .5, t1 = st_('d3') - .35, tRoll = WT('d2', 'roll');
    const banners = [['TOP 10 WAYS TO BE HAPPY', st_('d2') + .2, 360], ['GOOD VIBES ONLY', WT('d2', 'article'), 150], ['JUST THINK POSITIVE', WT('d2', 'eyes'), 570]];
    const A = actor('writer', { x: 360, y: 1050, s: 1.3, look: [360, 400], follow: .5, lid: .2, browIn: .3, armL: [-40, 230], armR: [40, 230] }, [
      { t: tRoll, d: .25, gaze: [-.3, -1], follow: .05, lid: .25, browOut: .5 }, { t: tRoll + .35, d: .35, gaze: [.4, -1] }, { t: tRoll + .8, d: .4, gaze: [0, 0], follow: .5, lid: .4, smile: -.2, browIn: -.3 },  // a long eye-roll
      { t: WT('d2', 'numbing'), d: .6, frown: .5, browIn: -.4 },
    ]);
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'gold', { x: 360, y: 640, z: 1 }, t, .2);
      citadel(ctx, 360, 1060, 1.0, t, {});
      banners.forEach(([txt, ti, x], i) => {
        const u = ramp(t, ti, ti + .8), gray = ramp(t, WT('d2', 'numbing') + i * .2, WT('d2', 'propaganda') + .4);
        if (u <= 0) return; const h = 330 * u;
        ctx.save(); ctx.translate(x, 330); ctx.fillStyle = mix('#f6e2a0', '#8a8a8a', gray); ctx.fillRect(-90, 0, 180, h); ctx.fillStyle = '#b08a3a'; ctx.fillRect(-100, -8, 200, 12);
        ctx.beginPath(); ctx.moveTo(-90, h); ctx.lineTo(0, h + 26 * u); ctx.lineTo(90, h); ctx.fill();
        if (u > .6) { ctx.fillStyle = mix('#8a2a1a', '#4a4a4a', gray); ctx.font = '800 30px Inter'; ctx.textAlign = 'center'; wrap(ctx, txt, 150).forEach((l, k) => ctx.fillText(l, 0, 70 + k * 40)); ctx.font = '400 40px Inter'; ctx.fillText(':)', 0, h - 40); }
        ctx.restore();
      });
      hud(ctx, ['// TACTICAL OBJECTIVE //', 'END THE REIGN', 'OF THE PLATITUDE'], t, st_('d1') - .05, 120, '#ffb07d', st_('d2') + .1);
      ctx.save(); ctx.globalAlpha = 1 - ramp(t, st_('d2'), st_('d2') + .5); ctx.restore();
      show(ctx, A, t, LIGHT.gold(360, 500));
      vignette(ctx, .4);
    }, .3);
  }
  // ===== 14. write back: the treatise =====
  {
    const t0 = st_('d3') - .35, t1 = st_('d4') - .4, tSab = WT('d3', 'sabotage');
    const A = actor('writer', { x: 360, y: 900, s: 1.7, look: [380, 1100], follow: .55, lid: .35, frown: .6, browIn: -.4, smile: -.1, armR: [30, 112], handR: 'hold', holdR: 'phoneBack', angR: -1.3, armL: [-24, 150], handL: 'hold', angL: 1.1, idle: 1.5 }, [
      { t: WT('d3', 'treatise'), d: .5, frown: .8, squint: .3 },
      { t: WT('d3', 'pain'), d: .6, look: [380, 500], lid: .1, frown: .3, browOut: .4 },
    ]);
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#140c0a'; ctx.fillRect(0, 0, W, H);
      sky(ctx, 'storm', { x: 360, y: 500, z: 1.3 }, t, .1);
      ctx.fillStyle = 'rgba(20,10,8,.4)'; ctx.fillRect(0, 0, W, H);
      fire(ctx, 360, 1220, 260, t, 1.1);
      show(ctx, A, t, LIGHT.fire(360, 1150, 1.3));
      // glowing words rising into a long scroll
      const words = ['blistering', 'pro-human', 'long-form', 'hyper-validating', 'you are not', 'too much', 'your pain', 'is data', 'not noise'];
      words.forEach((wd, i) => { const p = ((t - t0) * .22 + i / words.length) % 1; ctx.save(); ctx.globalAlpha = Math.sin(p * Math.PI) * .9; ctx.fillStyle = '#ffe6b0'; ctx.shadowColor = '#ff9a3a'; ctx.shadowBlur = 14; ctx.font = 'italic 600 32px "DejaVu Serif"'; ctx.textAlign = 'center'; ctx.fillText(wd, 360 + Math.sin(i * 2.3) * 180, 760 - p * 640); ctx.restore(); });
      // the platitude banner burns at "sabotage"
      const b = ramp(t, tSab - .3, tSab + 1.4);
      if (b > 0 && b < 1) { ctx.save(); ctx.translate(560, 260); ctx.rotate(.1); ctx.globalAlpha = 1 - b; ctx.fillStyle = mix('#f6e2a0', '#2a1a10', b); ctx.fillRect(-90, -40, 180, 140); ctx.fillStyle = '#8a2a1a'; ctx.font = '800 22px Inter'; ctx.textAlign = 'center'; ctx.fillText('TOP 10 WAYS', 0, 0); ctx.fillText('TO BE HAPPY', 0, 30); ctx.restore(); fire(ctx, 560, 380, 180, t, b * 1.2); }
      const hp = ramp(t, WT('d3', 'pain') - .1, WT('d3', 'pain') + .6);
      if (hp > 0) { const st = resolve(A.C, A.tr, t); flameHeart(ctx, st.x - 30, st.y + 90, 30 + 6 * Math.sin(t * 6), t, hp); }
      embers(ctx, t, 40, .8);
      vignette(ctx, .5);
    }, .3);
  }
  // ===== 15. pound on their digital doors: glowing message-arrows =====
  {
    const t0 = st_('d4') - .4, t1 = st_('d5') - .4, tJ = WT('d4', 'justice'), tE = WT('d4', 'empty');
    const vols = [WT('d4', 'Emails'), WT('d4', 'Texts'), WT('d4', 'Comments'), WT('d4', 'Plead'), WT('d4', 'demand'), WT('d4', 'Actionable')];
    const L = actor('leader', Object.assign({ x: 170, y: 930, s: 1.3, turn: .3, look: [500, 400], follow: .6, lid: .1, frown: .5, browIn: -.5, armL: [-60, 230], gest: 2 }, HOLD_SWORD), [
      { t: st_('d4'), d: .4, armR: [160, -40], angR: -1.1 }, { t: tJ - .2, d: .4, open: .4, armL: [-140, 40], handL: 'grip' }, { t: tJ + .8, d: .5, open: 0 },
    ]);
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'dawn', { x: 360, y: 640, z: 1 }, t, .2);
      citadel(ctx, 470, 900, .85, t, { screens: ramp(t, vols[0], vols[0] + .5), crack: ramp(t, tJ, tE + 1) * .5 });
      vols.forEach((v, i) => { for (let k = 0; k < 4; k++) { const p = clamp((t - v - k * .08) / .9); if (p <= 0 || p >= 1) continue; const sx = 120 + k * 30, sy = 1000, ex = 400 + ((i * 3 + k) % 5) * 36, ey = 280 + ((i + k) % 3) * 110; const x = lerp(sx, ex, p), y = lerp(sy, ey, p) - Math.sin(p * Math.PI) * 160; ctx.save(); ctx.translate(x, y); ctx.rotate(Math.atan2(ey - sy - Math.cos(p * Math.PI) * 500, ex - sx)); glow(ctx, 0, 0, 40, ['#8fd0ff', '#9fffc0', '#ffd08a'][i % 3], .6); ctx.fillStyle = '#fff'; roundRect(ctx, -16, -10, 32, 20, 6); ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.fillRect(-60, -2, 44, 4); ctx.restore(); } });
      // "empty statements": an empty speech bubble bursts
      const eb = ramp(t, tE - .2, tE + .3), ep = ramp(t, tE + .5, tE + .8);
      if (eb > 0 && ep < 1) { ctx.save(); ctx.translate(560, 330); ctx.scale(1 + ep * .6, 1 + ep * .6); ctx.globalAlpha = eb * (1 - ep); ctx.strokeStyle = '#fff'; ctx.lineWidth = 5; ctx.setLineDash([10, 8]); roundRect(ctx, -90, -50, 180, 100, 40); ctx.stroke(); ctx.setLineDash([]); ctx.restore(); }
      show(ctx, L, t, LIGHT.dawn(560, 400, 1.1), null, st => { st.top = (c, arms) => sword(c, arms); });
      vignette(ctx, .45);
    }, .3);
  }
  // ===== 16. the happy and healthy, the wealthy and wise =====
  {
    const t0 = st_('d5') - .4, tB = WT('d5', 'behinds') - .2, tF = WT('d5', 'finger'), t1 = st_('d6') - .35;
    const G1 = actor('gold1', { x: 180, y: 800, s: 1.0, lean: .18, look: [300, 500], follow: .6, lid: .6, smile: .45, armL: [-90, 180], armR: [90, 160], handR: 'hold' }, [
      { t: tB, d: .25, lean: 0, y: 770, lid: -.15, browOut: 1, browIn: .6, smile: -.1, open: .3 }, { t: tB + .8, d: .5, open: 0, lid: .3, smile: .2 },
      { t: tF - .2, d: .6, armR: [70, 60], handR: 'point', angR: -1.2, lid: .5, smile: .3 },        // lifts... one finger, barely
      { t: tF + .9, d: .5, armR: [90, 160], handR: 'relax' },
    ]);
    const G2 = actor('gold2', { x: 400, y: 790, s: .95, lean: -.15, look: [300, 500], follow: .6, lid: .55, smile: .5, armL: [-60, 160], armR: [140, 70], handR: 'open' }, [
      { t: tB + .1, d: .25, lean: 0, lid: -.1, browOut: 1, open: .25 }, { t: tB + .9, d: .5, open: 0, lid: .3, smile: .35 },
    ]);
    const G3 = actor('gold3', { x: 600, y: 800, s: 1.0, lean: .12, look: [400, 500], follow: .6, lid: .6, smile: .35 }, [{ t: tB + .2, d: .25, lean: 0, lid: -.1, browOut: .9, open: .3 }, { t: tB + 1, d: .5, open: 0, lid: .35 }]);
    const cards = [['Good vibes!', WT('d5', 'peddling')], ['Just be grateful', WT('d5', 'stop')], ['Everything happens for a reason', WT('d5', 'platitudes')]];
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'gold', { x: 360, y: 300, z: 1.4 }, t, .2);
      // silk cushions
      for (const [x, c] of [[180, '#9a2a5a'], [400, '#2a6a8a'], [600, '#6a2a8a']]) { ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse(x, 1060, 150, 50, 0, 0, TAU); ctx.fill(); }
      showMany(ctx, [G1, G2, G3], t, LIGHT.gold(360, 300));
      const g = ctx.createLinearGradient(0, 1060, 0, 1280); g.addColorStop(0, '#e8c46a'); g.addColorStop(1, '#7a5a20'); ctx.fillStyle = g; ctx.fillRect(0, 1080, W, 200);
      cards.forEach(([txt, ti], i) => { const p = clamp((t - ti) / 1.2); if (p <= 0 || p >= 1) return; ctx.save(); ctx.translate(lerp(430, 120 + i * 230, p), lerp(720, 380 + i * 30, p) - Math.sin(p * Math.PI) * 60); ctx.rotate((p - .5) * 1.5); ctx.globalAlpha = 1 - ramp(p, .8, 1); ctx.fillStyle = '#fffaf0'; roundRect(ctx, -110, -30, 220, 60, 10); ctx.fill(); ctx.fillStyle = '#b07020'; ctx.font = '600 20px Inter'; ctx.textAlign = 'center'; ctx.fillText(txt, 0, 7); ctx.restore(); });
      vignette(ctx, .4);
    }, .3);
    LABELS.push({ t0: WT('d5', 'happy') - .1, text: 'happy & healthy', x: 180, y: 520, dur: 1.8 }, { t0: WT('d5', 'wealthy') - .1, text: 'wealthy & wise', x: 560, y: 520, dur: 1.8 });
  }
  // ===== 17. called out: the parroting stops =====
  {
    const t0 = st_('d6') - .35, t1 = st_('e1') - .4, tY = st_('d7'), tO = WT('d7', 'called'), tS = WT('d7', 'stops');
    twoHill(t0, tY - .1, [{ t: 0, look: [560, 640], frown: .1 }, { t: WT('d6', 'messy'), d: .5, frown: .4, browIn: -.3, nod: 1 }],
      [{ t: st_('d6'), d: .4, lid: .1, frown: .45, browIn: -.3, armL: [-120, 120], handL: 'open', armR: [100, 140], handR: 'open', gest: 2 }], {});
    const G = actor('gold1', { x: 360, y: 860, s: 1.5, look: [200, 600], follow: .6, lid: .45, smile: .4, armL: [-40, 200], armR: [40, 200] }, [
      { t: tO + .3, d: .25, lid: -.15, browOut: 1, browIn: .5, smile: -.3, open: .35, look: 'cam' }, { t: tS, d: .5, open: 0, smile: -.2, lid: .25 },
    ]);
    shot(tY - .1, t1, (ctx, t) => {
      const hitT = tO + .25, k = t - hitT;
      ctx.save(); if (k > 0 && k < .3) shake(ctx, 12, t);
      sky(ctx, 'gold', { x: 360, y: 300, z: 1.5 }, t, .2);
      show(ctx, G, t, LIGHT.gold(300, 300));
      // a parrot on his shoulder, squawking until it stops
      const st = resolve(G.C, G.tr, t); const px = st.x + 62 * st.s, py = st.y - 18 * st.s, sq = t < tS && Math.sin(t * 14) > 0;
      ctx.save(); ctx.translate(px, py); ctx.fillStyle = '#2aa04a'; ctx.beginPath(); ctx.ellipse(0, 0, 34, 50, .2, 0, TAU); ctx.fill(); ctx.fillStyle = '#d83a2a'; ctx.beginPath(); ctx.arc(0, -52, 26, 0, TAU); ctx.fill(); ctx.fillStyle = '#3a6ad8'; ctx.beginPath(); ctx.ellipse(-12, 40, 14, 40, .3, 0, TAU); ctx.fill();
      ctx.fillStyle = '#f0e0a0'; ctx.beginPath(); ctx.moveTo(-18, -54); ctx.lineTo(-44, -44 + (sq ? -8 : 0)); ctx.lineTo(-18, -40); ctx.fill(); if (sq) { ctx.beginPath(); ctx.moveTo(-18, -44); ctx.lineTo(-40, -30); ctx.lineTo(-18, -38); ctx.fill(); }
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(-6, -58, 7, 0, TAU); ctx.fill(); ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(-7, -58, 3.5, 0, TAU); ctx.fill(); ctx.restore();
      if (sq) { ctx.fillStyle = '#fff'; ctx.font = '800 26px Inter'; ctx.fillText('GOOD VIBES! SQUAWK!', px - 300, py - 90); }
      if (t > tS + .1) { ctx.fillStyle = 'rgba(255,255,255,.9)'; ctx.font = '800 40px Inter'; ctx.fillText('...', px - 80, py - 90); }
      // the call-out: a blazing bubble slams in
      if (k > -0.3 && k < 2.5) { const p = easeOut(clamp((k + .3) / .3)); ctx.save(); ctx.translate(lerp(-200, 170, p), 330); ctx.globalAlpha = 1 - ramp(k, 1.8, 2.5); glow(ctx, 0, 0, 140, '#ff8a3a', .5); ctx.fillStyle = '#ff6a2a'; roundRect(ctx, -110, -60, 220, 120, 40); ctx.fill(); ctx.fillStyle = '#fff'; ctx.font = '900 80px Inter'; ctx.textAlign = 'center'; ctx.fillText('!', 0, 28); ctx.restore(); }
      ctx.restore();
      vignette(ctx, .4);
    }, 0);
  }
  // ===== 18. tipping point: nowhere left to hide =====
  {
    const t0 = st_('e1') - .4, t1 = st_('e2') - .6, tA = WT('e1', 'architects'), tT = WT('e1', 'tipping'), tI = WT('e1', 'inject'), tH = WT('e1', 'hide');
    const L = actor('leader', { x: 210, y: 960, s: 1.15, turn: .3, look: [450, 500], follow: .6, lid: .1, frown: .2, browOut: .3, armL: [-126, 300], armR: [170, -130], handR: 'open', angR: -.3, gest: 1.5 });
    const Wr = actor('writer', { x: 570, y: 990, s: 1.1, turn: -.2, look: [450, 500], follow: .6, lid: .1, browOut: .4, smile: .2, armL: [-126, 300], armR: [126, 300] });
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'dawn', { x: 360, y: 640, z: 1 }, t, .2);
      const flood = ramp(t, tI, tH + .5);
      citadel(ctx, 400, 900, .7, t, { crack: .4 + flood * .6, screens: flood });
      // architects' blueprint lines tracing the scale
      const bp = ramp(t, tA - .2, tA + 1);
      ctx.save(); ctx.globalAlpha = bp * (1 - flood * .7); ctx.strokeStyle = '#8fd0ff'; ctx.lineWidth = 3; ctx.setLineDash([12, 8]);
      const tilt = ramp(t, tT, tT + 1.2) * .3;
      ctx.translate(400, 300); ctx.beginPath(); ctx.moveTo(0, -60); ctx.lineTo(0, 120); ctx.stroke(); ctx.rotate(tilt); ctx.beginPath(); ctx.moveTo(-220, 0); ctx.lineTo(220, 0); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(255,200,120,.8)'; ctx.beginPath(); ctx.arc(-200, 30, 30 + flood * 10, 0, TAU); ctx.fill(); ctx.fillStyle = 'rgba(200,200,220,.6)'; ctx.beginPath(); ctx.arc(200, 30, 22, 0, TAU); ctx.fill();
      ctx.restore();
      // streams of light poured into the system
      if (flood > 0) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; for (let k = 0; k < 14; k++) { const p = ((t * .8 + k / 14) % 1); ctx.fillStyle = `rgba(255,220,150,${.5 * flood * (1 - p)})`; ctx.beginPath(); ctx.arc(lerp(180 + k * 30, 400, p), lerp(1150, 720, p), 6, 0, TAU); ctx.fill(); } glow(ctx, 400, 700, 500 * flood, '#fff0c0', .3 * flood); ctx.restore(); }
      show(ctx, L, t, LIGHT.dawn(400, 600, 1.1)); show(ctx, Wr, t, LIGHT.dawn(400, 600, 1.1));
      vignette(ctx, .4);
    }, .3);
  }
  // ===== 19. "I am lonely" =====
  {
    const t0 = st_('e2') - .6, t1 = st_('e3') - .3;
    const Lo = actor('lonely', { x: 360, y: 930, s: 1.9, look: [380, 1150], follow: .5, lid: .5, browIn: .9, smile: -.35, armL: [-50, 200], armR: [50, 200], handL: 'relax', handR: 'relax', breathe: 1.2 }, [
      { t: WT('e2', 'lonely') + .2, d: .8, look: [400, 640], lid: .25, tearful: .6 },          // she looks up, asking
      { t: en_('e2') + .3, d: .8, lid: .4, browIn: 1.1 },
    ]);
    Lo.tr.base.tears = [{ side: 1, t0: WT('e2', 'feeling') - .2, dur: 3.4 }];
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'storm', { x: 360, y: 500, z: 1.4 }, t, .1);
      show(ctx, Lo, t, LIGHT.storm(560, 400));
      ctx.fillStyle = 'rgba(200,210,230,.1)'; for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.ellipse(((t * 20 + k * 300) % 1000) - 150, 900 + k * 80, 300, 40, 0, 0, TAU); ctx.fill(); }
      vignette(ctx, .6);
    }, .4);
  }
  // ===== 20. not a shrug, not a link =====
  {
    const t0 = st_('e3') - .3, t1 = st_('e4') - .4, tL = WT('e3', 'link');
    const G = actor('gold2', { x: 360, y: 860, s: 1.5, look: [200, 1000], follow: .6, lid: .5, smile: .25, armL: [-40, 220], armR: [40, 220] }, [
      { t: WT('e3', 'dismissive') - .2, d: .4, shrug: 1, armL: [-130, 120], handL: 'open', armR: [130, 120], handR: 'open', browOut: .7, smile: .1, headRoll: .1 },
      { t: WT('e3', 'shrug') + .5, d: .4, shrug: 0, armL: [-40, 220], handL: 'relax' },
      { t: tL - .2, d: .5, armR: [150, 60], handR: 'hold', angR: -.6 },
    ]);
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'gold', { x: 360, y: 300, z: 1.5 }, t, .2);
      let ga; show(ctx, G, t, LIGHT.gold(300, 300), null, st => { st.top = (c, arms) => { ga = arms; }; });
      const lp = ramp(t, tL - .1, tL + .4), x2 = ramp(t, WT('e3', 'blog') + .3, WT('e3', 'blog') + .7);
      if (lp > 0) { ctx.save(); ctx.translate(560, 560); ctx.globalAlpha = lp; ctx.rotate(-.1); ctx.fillStyle = '#fffaf0'; roundRect(ctx, -140, -40, 280, 80, 14); ctx.fill(); ctx.fillStyle = '#2a6ad8'; ctx.font = '600 22px Inter'; ctx.textAlign = 'center'; ctx.fillText('selfhelp.blog/cheer-up', 0, 8); ctx.fillRect(-110, 14, 220, 2);
        if (x2 > 0) { ctx.strokeStyle = '#e0302a'; ctx.lineWidth = 10; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-150 * x2, -50 * x2); ctx.lineTo(150 * x2, 50 * x2); ctx.moveTo(150 * x2, -50 * x2); ctx.lineTo(-150 * x2, 50 * x2); ctx.stroke(); }
        ctx.restore(); }
      vignette(ctx, .4);
    }, 0);
  }
  // ===== 21. a real answer: they gather around her =====
  {
    const t0 = st_('e4') - .4, t1 = st_('f1') - .5, tR = WT('e4', 'relief'), tTo = WT('e4', 'together');
    const Lo = actor('lonely', { x: 360, y: 960, s: 1.35, look: [360, 1150], follow: .5, lid: .5, browIn: .9, smile: -.3, armL: [-50, 200], armR: [50, 200], tearful: .5 }, [
      { t: WT('e4', 'validating'), d: .7, look: [180, 700], lid: .25, browIn: .7 },
      { t: tR, d: 1.0, look: [560, 700], smile: .3, browIn: .5, tearful: .7 },
      { t: tTo, d: .9, smile: .6, squint: .3, lid: .25, browIn: .3, look: [360, 600] },
    ]);
    Lo.tr.base.tears = [{ side: -1, t0: tR - .3, dur: 3.2 }];
    const L = actor('leader', { x: 110, y: 900, s: 1.3, turn: .3, look: [360, 820], follow: .6, lid: .2, browIn: .5, smile: .15, frown: 0, armL: [-50, 230], armR: [50, 230] }, [
      { t: st_('e4') + .3, d: 1, armR: [81, 138], handR: 'flat', angR: .3 },               // a hand on her shoulder
    ]);
    const Wr = actor('writer', { x: 590, y: 920, s: 1.25, turn: -.3, look: [360, 840], follow: .6, lid: .2, browIn: .6, smile: .1, armL: [-40, 230], armR: [40, 230] }, [
      { t: WT('e4', 'engagement'), d: 1, armL: [-68, 128], handL: 'flat', angL: -.3 }, { t: tTo, d: .6, smile: .5 },
    ]);
    const back = crowdRow(['c2', 'c6', 'c10', 'c11'], 140, 580, 760, .8, { look: [360, 820], follow: .6, lid: .25, browIn: .5, smile: .15 }, (i) => [{ t: tTo, d: .6, smile: .45 }]);
    shot(t0, t1, (ctx, t) => {
      const k = ramp(t, st_('e4'), tTo);
      sky(ctx, 'storm', { x: 360, y: 500, z: 1.2 }, t, .1);
      ctx.save(); ctx.globalAlpha = k; applyCam(ctx, { x: 360, y: 500, z: 1.2 }); ctx.drawImage(highlandBG('dawn'), -200, -200); ctx.restore();
      const lt = LIGHT.dawn(360, 300, .5 + k * .6);
      showMany(ctx, back, t, lt); show(ctx, Lo, t, lt); show(ctx, L, t, lt); show(ctx, Wr, t, lt);
      vignette(ctx, .45);
    }, .4);
  }
  // ===== 22. the molt: a dragon of emotional insight =====
  {
    const t0 = st_('f1') - .5, t1 = st_('f2') - .4, tQ = WT('f1', 'quiet'), tL = WT('f1', 'loud'), tG = WT('f1', 'glorious'), tD = WT('f1', 'dragon');
    const A = actor('writer', { x: 360, y: 860, s: 1.5, look: [360, 1100], follow: .5, lid: .7, browIn: .5, smile: -.1, armL: [-50, 120], armR: [50, 120], handL: 'grip', handR: 'grip', headPitch: .15 }, [
      { t: tL - .2, d: .6, look: [360, 300], lid: -.1, headPitch: -.1, browOut: .8, browIn: -.3, frown: .4, open: .3, armL: [-180, -20], armR: [180, -20], handL: 'open', handR: 'open' },   // bursts free
      { t: tG, d: .6, open: .45, smile: .3 }, { t: tD + .6, d: .6, open: 0, smile: .4, frown: .5 },
    ]);
    shot(t0, t1, (ctx, t) => {
      const fireK = ramp(t, tL - .2, tG);
      ctx.fillStyle = '#0c0808'; ctx.fillRect(0, 0, W, H);
      ctx.save(); ctx.globalAlpha = fireK; sky(ctx, 'gold', null, t, .2); ctx.restore();
      // the dragon rising behind him
      const dk = ramp(t, tD - .6, tD + 1.2);
      if (dk > 0) { ctx.save(); ctx.globalAlpha = dk; dragon(ctx, 380, lerp(700, 380, dk), 1.5, t, 1, '#8a2a14', ramp(t, tD + .4, tD + .8), 1); ctx.restore(); }
      fireWings(ctx, 360, 640, t, fireK, 1.2);
      // dark chrysalis around him until it cracks
      if (t < tL) { const cg = ctx.createRadialGradient(330, 640, 20, 360, 760, 430); cg.addColorStop(0, '#4a3a48'); cg.addColorStop(1, '#141018'); ctx.fillStyle = cg; ctx.beginPath(); ctx.ellipse(360, 760, 230, 420, 0, 0, TAU); ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,.4)'; ctx.lineWidth = 4; for (let k = 0; k < 7; k++) { ctx.beginPath(); ctx.ellipse(360, 760, 230 - k * 6, 420 - k * 40, 0, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke(); }
        glow(ctx, 360, 760, 260, '#ff8a3a', .12 + .25 * ramp(t, tQ, tL) * (.6 + .4 * Math.sin(t * 7))); const cr = ramp(t, tQ, tL); ctx.strokeStyle = `rgba(255,150,60,${cr})`; ctx.lineWidth = 3; ctx.shadowColor = '#ff8a3a'; ctx.shadowBlur = 12; ctx.beginPath(); ctx.moveTo(360, 360); for (let k = 0; k < 12 * cr; k++) ctx.lineTo(360 + Math.sin(k * 2.3) * 40, 360 + k * 50); ctx.stroke(); ctx.shadowBlur = 0; }
      else { show(ctx, A, t, LIGHT.fire(360, 500, 1.3)); shards(ctx, 360, 760, t, tL - .05); }
      embers(ctx, t, 60, fireK);
      vignette(ctx, .45);
    }, .3);
  }
  // ===== 23. the key: forged in agony, picking every lock =====
  {
    const t0 = st_('f2') - .4, tC = WT('f2', 'cage'), tT = WT('f2', 'template'), tP = WT('f2', 'prison'), t1 = st_('f3') - .4;
    shot(t0, tC - .2, (ctx, t) => {
      ctx.fillStyle = '#140c08'; ctx.fillRect(0, 0, W, H); glow(ctx, 360, 900, 600, '#ff6a20', .35);
      fire(ctx, 360, 1160, 400, t, 1.2);
      anvil(ctx, 360, 900, 1.2);
      const hot = 1 - ramp(t, WT('f2', 'agony') + .3, tC);
      glowKey(ctx, 360, 820, 1.2, 0, .3 + hot * .7);
      for (const h of [st_('f2') + .3, WT('f2', 'forged'), WT('f2', 'fires'), WT('f2', 'agony')]) sparks(ctx, 360, 810, t, h, 30);
      embers(ctx, t, 30, .7); vignette(ctx, .5);
    }, .3);
    shot(tC - .2, tT - .1, (ctx, t) => { // his own cage unlocks
      ctx.fillStyle = '#0e0a0c'; ctx.fillRect(0, 0, W, H); glow(ctx, 360, 640, 400, '#ff9a40', .2);
      const op = ramp(t, tC + .5, tC + 1.4);
      prisonDoor(ctx, 160, 260, 400, 700, op, t);
      const kx = lerp(800, 548, ramp(t, tC - .2, tC + .3)); glowKey(ctx, kx, 640 + 12, .6, ramp(t, tC + .3, tC + .6) * 1.4, .4);
      vignette(ctx, .5);
    }, 0);
    shot(tT - .1, t1, (ctx, t) => { // every prison door, one after another
      ctx.fillStyle = '#0e0a0c'; ctx.fillRect(0, 0, W, H);
      for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) { const i = r * 3 + c, ti = tP - .6 + i * .3; prisonDoor(ctx, 40 + c * 230, 170 + r * 290, 180, 240, ramp(t, ti, ti + .6), t); if (t > ti && t < ti + .5) glowKey(ctx, 40 + c * 230 + 180, 170 + r * 290 + 132, .35, 1, .5); }
      embers(ctx, t, 30, .6); vignette(ctx, .45);
    }, 0);
  }
  // ===== 24. "Then let's release the dragons!" =====
  {
    const t0 = st_('f3') - .4, t1 = st_('f4') - .1;
    const A = actor('writer', { x: 360, y: 1010, s: 2.3, look: [360, 500], follow: .5, lid: .05, browOut: .8, browIn: -.4, frown: .5, smile: .25, armL: [-50, 230], armR: [150, -60], handR: 'grip', angR: -1.4 });
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'gold', { x: 360, y: 500, z: 1.3 }, t, .2);
      fireWings(ctx, 360, 640, t, .6, 1.4);
      show(ctx, A, t, LIGHT.fire(360, 400, 1.2));
      embers(ctx, t, 40, .8); vignette(ctx, .4);
    }, 0);
  }
  // ===== 25. RELEASE THE DRAGONS =====
  {
    const t0 = st_('f4') - .1, t1 = TL.total + .5;
    const crowd = crowdRow(['c0', 'c2', 'c4', 'c6', 'c8', 'c10'], 30, 690, 1120, 1.0, { look: [360, 300], follow: .6, lid: .05, browOut: .7, smile: .55, open: .35, armL: [-175, -190], armR: [175, -190], handL: 'grip', handR: 'grip', gest: 2 });
    const L = actor('leader', Object.assign({ x: 360, y: 900, s: 1.15, look: [360, 300], follow: .6, lid: .05, smile: .5, browOut: .6, open: .4, armL: [-60, 230] }, HOLD_SWORD, { armR: [150, -80], angR: -1.2 }));
    const ds = [[1, -300, 600, .5, '#8a2a14', 0], [-1, 1000, 420, .38, '#2a5a3a', .4], [1, -400, 260, .3, '#2a3a7a', .9], [-1, 1100, 700, .55, '#6a2a7a', 1.3], [1, -300, 150, .22, '#9a6a14', 1.8]];
    shot(t0, t1, (ctx, t) => {
      sky(ctx, 'gold', null, t, .25);
      const lt = t - t0;
      citadel(ctx, 360, 900, .5, t, { crack: 1 });
      for (const [dir, x0, y, s, col, d] of ds) { const p = clamp((lt - d) / 6); if (p <= 0) continue; const x = x0 + dir * p * 1400; dragon(ctx, x, y + Math.sin(lt * 2 + d) * 30 - p * 120, s, t, dir, col, Math.sin(lt * 3 + d) > .6 ? 1 : 0, d * 3); }
      show(ctx, L, t, LIGHT.dawn(360, 300, 1.2), null, st => { st.top = (c, arms) => sword(c, arms); });
      showMany(ctx, crowd, t, LIGHT.dawn(360, 300, 1));
      const a = ramp(lt, 2.0, 2.8);
      if (a > 0) { ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.shadowColor = '#ff7a2a'; ctx.shadowBlur = 24; ctx.fillStyle = '#fff3d0'; ctx.font = '800 64px "DejaVu Serif"'; ctx.fillText('WEAPONIZE', 360, 300); ctx.fillText('THE WOUND', 360, 375); ctx.font = 'italic 600 30px "DejaVu Serif"'; ctx.fillText('Release the dragons.', 360, 430); ctx.restore(); }
      embers(ctx, t, 50, .8);
      vignette(ctx, .35);
    }, 0);
  }
}
function hammer(c, A) { // handle continues from the fist, head across its end
  const [wx, wy] = A.w, fa = Math.atan2(wy - A.e[1], wx - A.e[0]) + (A.ang || 0);
  c.save(); c.translate(wx, wy); c.rotate(fa); c.fillStyle = '#5a3a20'; c.fillRect(10, -7, 110, 14);
  const g = c.createLinearGradient(0, -34, 0, 34); g.addColorStop(0, '#8a8a92'); g.addColorStop(1, '#2a2a30'); c.fillStyle = g; c.fillRect(104, -34, 44, 68); c.restore();
}
function bricksCached(ctx) { ctx.drawImage(cached('forgewall', W, H, c => { bricks(c, 0, 0, W, H, '#4a3026', 21, 90, 40, '#1a100c'); }), 0, 0); ctx.fillStyle = 'rgba(10,5,3,.45)'; ctx.fillRect(0, 0, W, H); }
function rainB(ctx, t, a) { ctx.save(); ctx.strokeStyle = `rgba(180,195,230,${a})`; ctx.lineWidth = 1.3; for (let i = 0; i < 70; i++) { const x = (hash(i) * W + t * 60) % W, y = (hash(i + 50) * H + t * 900 * (0.8 + hash(i + 9) * .4)) % H; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 5, y + 22); ctx.stroke(); } ctx.restore(); }
