// ---------- shots ----------
const st_ = id => LINE(id).start, en_ = id => LINE(id).end;
function actor(name, base, keys) { return { C: CAST[name], tr: new Track(Object.assign({}, BASE_STATE, base), keys || []) }; }
function show(ctx, a, t, light, cam, extra) {
  const st = resolve(a.C, a.tr, t); if (extra) extra(st);
  if (st.visible <= 0) return st;
  drawLit(ctx, c => { c.save(); if (cam) applyCam(c, cam); c.globalAlpha = st.alpha; drawChar(c, a.C, st, t); c.restore(); }, light);
  return st;
}
function applyCam(c, cam) { c.translate(W / 2, H / 2); c.scale(cam.z, cam.z); c.translate(-cam.x, -cam.y); }
function toScreen(cam, x, y) { return cam ? [(x - cam.x) * cam.z + W / 2, (y - cam.y) * cam.z + H / 2] : [x, y]; }
const LIGHT = {
  phone: (x, y, k = 1) => ({ x, y, color: '#8fbfff', str: .32 * k, rad: 420, dark: .42, near: '#ffffff', amb: '#33384f', fall: 820, rim: .3, rimColor: '#ffcf8a', rimDx: -5, rimDy: 3 }),
  lamp: (x, y, k = 1) => ({ x, y, color: '#ffb35c', str: .3 * k, rad: 520, dark: .5, near: '#fff4e0', amb: '#3a2a2a', fall: 900, rim: .5 * k, rimColor: '#ffc070', rimDx: x < 360 ? 7 : -7, rimDy: 2 }),
  fire: (x, y, k = 1) => ({ x, y, color: '#ff9a40', str: .35 * k, rad: 600, dark: .5, near: '#fff0d8', amb: '#2e2830', fall: 950, rim: .6 * k, rimColor: '#ffae55', rimDx: x < 360 ? 7 : -7, rimDy: 0 }),
  cool: (x, y) => ({ x, y, color: '#7d9ccf', str: .18, rad: 600, dark: .45, near: '#e0e8ff', amb: '#2a3048', fall: 900, rim: .45, rimColor: '#9fc0ff', rimDx: x < 360 ? 7 : -7, rimDy: 0 }),
  dawn: (x, y, k = 1) => ({ x, y, color: '#ffc58a', str: .3 * k, rad: 700, dark: .25, near: '#fff6ea', amb: '#5a4a60', fall: 1000, rim: .55 * k, rimColor: '#ffd79a', rimDx: x < 360 ? 7 : -7, rimDy: 2 }),
  party: (x, y) => ({ x, y, color: '#ffcf8a', str: .2, rad: 700, dark: .3, near: '#fff', amb: '#4a3a50', fall: 1000, rim: .35, rimColor: '#ff9ad0', rimDx: 6, rimDy: 0 }),
};
const SHOTS = [];
function shot(t0, t1, draw, xin = 0) { SHOTS.push({ t0, t1, draw, xin }); }
const SUPPRESS = new Set(['b1', 'b2', 'b6', 'g1', 'g2']); // shown as chat bubbles instead
const LABELS = []; // {t0, text, x, y}

// shared apartment writer composition --------------------------------------------------
function aptWriter(ctx, t, A, mode, opts = {}) {
  const bg = aptBG(mode);
  const cam = opts.cam || { x: 360, y: 640, z: 1 };
  ctx.save(); applyCam(ctx, cam); ctx.drawImage(bg, 0, 0); ctx.restore();
  ctx.save(); applyCam(ctx, cam);
  if (mode === 'night') rain(ctx, 52, 162, 226, 306, t, .35);
  if (opts.bulb !== false) bulb(ctx, 470, 120, t, mode === 'night');
  if (opts.under) opts.under(ctx, t);
  ctx.restore();
  // glow on the wall from the phone
  const [px, py] = toScreen(cam, A.tr.base.x + 40, A.tr.base.y - 40);
  if (mode === 'night') glow(ctx, px, py - 120, 380, '#5a8ae0', .18);
  else glow(ctx, 160, 300, 700, '#ffcf9a', .25);
  const light = mode === 'night' ? LIGHT.phone(px, py - 60) : LIGHT.dawn(160, 320);
  const st = show(ctx, A, t, light, cam);
  if (opts.over) opts.over(ctx, t, st);
  vignette(ctx, mode === 'night' ? .55 : .3);
  return st;
}
// phone-holding arm defaults (writer)
const PHONE_HOLD = { armR: [30, 112], handR: 'hold', holdR: 'phoneBack', angR: -1.3, armL: [-24, 150], handL: 'hold', angL: 1.1 };

function buildShots() {
  // ===== 1. opening: writer typing at night (first frame = this) =====
  {
    const A = actor('writer', Object.assign({ x: 360, y: 840, s: 1.8, look: [410, 1060], follow: .5, lid: .3, browIn: .35, smile: -.15 }, PHONE_HOLD), [
      { t: .9, d: .5, lid: .22 },
    ]);
    shot(0, st_('m1') - .05, (ctx, t) => aptWriter(ctx, t, A, 'night'));
    LABELS.push({ t0: 0, text: 'The Writer', x: 360, y: 400, dur: 1.55 });
  }
  // ===== 2. martyr panels =====
  const mp = [['m1', 'JOHN', panelJohn], ['m2', 'JESUS', panelCross], ['m3', 'PHILIP', panelStones], ['m4', 'MATTHEW', panelMatthew], ['m5', 'PETER', panelPeter], ['m6', 'LUKE', panelOlive], ['m7', 'JAMES', panelSword]];
  mp.forEach(([id, name, fn], i) => {
    const t0 = st_(id) - .05, t1 = i < 6 ? st_(mp[i + 1][0]) - .05 : st_('a1') - .35;
    shot(t0, t1, (ctx, t) => martyrFrame(ctx, t, t - t0, name, fn), i ? .25 : 0);
  });
  // ===== 3. a1 + a2(part 1): writer looks up from phone =====
  {
    const t0 = st_('a1') - .35, tPeople = WT('a2', 'People');
    const A = actor('writer', Object.assign({ x: 360, y: 840, s: 1.8, look: [410, 1060], follow: .5, lid: .25, browIn: .3 }, PHONE_HOLD), [
      { t: st_('a1') + .1, d: .7, look: [360, 600], follow: .45, browIn: .6, frown: .2, lid: .12 },              // looks up: "So what's the metaphor..."
      { t: WT('a1', 'me'), d: .5, browIn: .8, browOut: -.2 },
      { t: st_('a2') - .2, d: .9, look: [150, 520], follow: .6, browIn: .5, frown: .45 },                        // glance to the window: "Not in a violent way"
      { t: WT('a2', 'endure'), d: .6, look: [380, 660], follow: .5, lid: .3, browIn: .9, smile: -.3 },          // weary
      { t: WT('a2', 'abandonment'), d: 1.2, look: [380, 900], lid: .45, headRoll: .05 },                      // one slow look down
    ]);
    shot(t0, tPeople - .1, (ctx, t) => aptWriter(ctx, t, A, 'night'), .3);
  }
  // ===== 4. street window: friends drift away, shutters close =====
  {
    const tP = WT('a2', 'People') - .1, tB = WT('a2', 'Being'), t1 = st_('a3') - .4;
    const W1 = actor('writer', { x: 170, y: 840, s: 1.25, look: [500, 600], follow: .7, lid: .3, browIn: .8, smile: -.3, armL: [-40, 260], armR: [40, 260], handL: 'relax', handR: 'relax', turn: .2 }, [
      { t: tB + .2, d: .4, lid: .05, browIn: 1, browOut: .3 },   // flinch as the shutters close
      { t: tB + 1.0, d: 1.2, lid: .45, look: [420, 900], browIn: .9, smile: -.45 },
    ]);
    const F = [['f1', 450, 640, .55], ['f2', 560, 650, .55], ['f3', 650, 655, .5]].map(([n, x, y, s], i) => actor(n, { x, y, s, look: [x + 60, y - 50], follow: .6, smile: .55, armL: [-60, 160], armR: [60, 160], gest: 2 }, [
      { t: tP + .3 + i * .35, d: 2.6, x: x + 30 + i * 30, y: y - 40, s: s * .62, look: [x + 200, y - 120], smile: .3, ease: ease }, // walking off into the room, smaller
    ]));
    shot(tP, t1, (ctx, t) => {
      // inside room (behind window)
      ctx.fillStyle = '#3b2a20'; ctx.fillRect(0, 0, W, H);
      const ig = ctx.createLinearGradient(0, 360, 0, 840); ig.addColorStop(0, '#d89a58'); ig.addColorStop(1, '#8a5432'); ctx.fillStyle = ig; ctx.fillRect(330, 380, 370, 440);
      glow(ctx, 520, 470, 260, '#ffd38a', .5);
      for (const f of F) { const s = resolve(f.C, f.tr, t); if (t > tP + 3.5 && s.s < .4) s.alpha = clamp(1 - (t - tP - 3.5)); drawChar(ctx, f.C, s, t); }
      ctx.fillStyle = '#6b4a30'; ctx.fillRect(400, 740, 260, 80); // table edge inside
      // wall around window
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.rect(330, 380, 370, 440); ctx.clip('evenodd');
      bricksCached(ctx); ctx.restore();
      // shutters swinging on hinges
      const sh = ramp(t, tB, tB + 1.0);
      for (const side of [-1, 1]) {
        const hx = side < 0 ? 330 : 700, ww = 185 * Math.cos((1 - sh) * 1.45) * (sh > 0 ? 1 : 1);
        const vw = 185 * Math.sin(sh * Math.PI / 2) + 18 * (1 - sh);
        ctx.save();
        const x0 = side < 0 ? hx : hx - vw;
        const g = ctx.createLinearGradient(x0, 0, x0 + vw, 0); g.addColorStop(0, '#3e5a4a'); g.addColorStop(1, '#2a3e34');
        ctx.fillStyle = g; ctx.fillRect(x0, 380 - 6 * (1 - sh), vw, 440 + 12 * (1 - sh));
        ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 2; for (let k = 0; k < 14; k++) { ctx.beginPath(); ctx.moveTo(x0 + 4, 400 + k * 30); ctx.lineTo(x0 + vw - 4, 400 + k * 30); ctx.stroke(); }
        ctx.restore();
      }
      if (sh > .95) { ctx.fillStyle = 'rgba(255,200,120,.5)'; ctx.fillRect(513, 380, 4, 440); }
      ctx.fillStyle = 'rgba(15,25,50,.45)'; ctx.fillRect(0, 0, W, H); // night tint outside
      if (sh < 1) glow(ctx, 515, 600, 300, '#ffbe70', .25 * (1 - sh));
      rain(ctx, 0, 0, W, H, t, .3);
      // street
      ctx.fillStyle = '#16191f'; ctx.fillRect(0, 1090, W, 190);
      show(ctx, W1, t, LIGHT.cool(560, 600));
      vignette(ctx, .6);
    }, 0);
  }
  // ===== 5. party: shallow conversation =====
  {
    const t0 = st_('a3') - .4, t1 = st_('a4') - .35;
    const bubbles = [['So... busy week?', 160, 380, 0], ['Crazy weather, huh?', 560, 360, 1], ['Did you see that video?', 360, 290, 2]];
    const WR = actor('writer', { x: 360, y: 870, s: 1.25, look: [150, 560], follow: .6, smile: .35, lid: .1, armL: [-40, 250], armR: [40, 250] }, [
      { t: WT('a3', 'epidemic'), d: .5, look: [590, 560], smile: .3 },
      { t: WT('a3', 'shallow'), d: .5, look: [360, 520], smile: .12, lid: .32, browIn: .3 },
      { t: WT('a3', 'conversation'), d: .8, smile: -.05, lid: .42, browIn: .5 },
      { t: WT('a3', 'won\'t'), d: .6, look: [360, 1100], follow: .7, lid: .5, smile: -.2, browIn: .7 },
      { t: WT('a3', 'anymore'), d: 1.4, y: 900, s: 1.2, x: 330, turn: -.2, ease: ease },
    ]);
    const P1 = actor('f1', { x: 140, y: 700, s: .85, look: [360, 700], follow: .7, smile: .6, browIn: .1, browOut: .4, armL: [-40, 200], armR: [70, 150], handR: 'open', gest: 2 }, [{ t: WT('a3', 'won\'t'), d: 1, look: [560, 700], smile: .5 }]);
    const P2 = actor('f2', { x: 590, y: 710, s: .85, look: [360, 700], follow: .7, smile: .5, browOut: .3, armL: [-70, 160], armR: [40, 220], handL: 'open', gest: 2 }, [{ t: WT('a3', 'won\'t'), d: 1, look: [150, 700] }]);
    const P3 = actor('f3', { x: 370, y: 610, s: .68, look: [360, 900], follow: .7, smile: .7, armL: [-40, 200], armR: [40, 200] }, [{ t: WT('a3', 'won\'t'), d: 1, look: [570, 650] }]);
    const bt = [WT('a3', 'And') - .1, WT('a3', 'epidemic') + .3, WT('a3', 'shallow')];
    shot(t0, t1, (ctx, t) => {
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#3a2a40'); g.addColorStop(1, '#1a1420'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      // string lights
      for (let i = 0; i < 12; i++) { const x = 20 + i * 62, y = 120 + Math.sin(i * .9) * 20; glow(ctx, x, y, 50, ['#ffcf6a', '#ff8ac0', '#8ad0ff'][i % 3], .5 + .2 * Math.sin(t * 2 + i)); }
      ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.beginPath(); for (let i = 0; i < 12; i++) { const x = 20 + i * 62, y = 120 + Math.sin(i * .9) * 20; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke();
      show(ctx, P3, t, LIGHT.party(360, 200)); show(ctx, P1, t, LIGHT.party(360, 200)); show(ctx, P2, t, LIGHT.party(360, 200));
      show(ctx, WR, t, LIGHT.party(360, 300));
      // shallow talk bubbles: appear, then go hollow and pop
      bubbles.forEach(([txt, x, y, i]) => {
        const a = ramp(t, bt[i], bt[i] + .3), pop = ramp(t, WT('a3', 'won\'t') + i * .15, WT('a3', 'won\'t') + .4 + i * .15);
        if (a <= 0 || pop >= 1) return;
        ctx.save(); ctx.globalAlpha = a * (1 - pop); ctx.translate(x, y); const sc = 1 + pop * .3; ctx.scale(sc, sc);
        ctx.font = '600 26px Inter'; const w = ctx.measureText(txt).width + 36;
        ctx.fillStyle = 'rgba(255,255,255,.92)'; roundRect(ctx, -w / 2, -30, w, 56, 26); ctx.fill();
        ctx.beginPath(); ctx.moveTo(-10, 24); ctx.lineTo(0, 44); ctx.lineTo(10, 24); ctx.fill();
        ctx.fillStyle = '#3a3040'; ctx.textAlign = 'center'; ctx.fillText(txt, 0, 7); ctx.restore();
      });
      vignette(ctx, .5);
    }, 0);
  }
  // ===== 6. "So instead, I post online." =====
  {
    const t0 = st_('a4') - .35, t1 = st_('b1') - .5, tPost = WT('a4', 'post');
    const WR = actor('writer', Object.assign({ x: 380, y: 860, s: 1.7, look: [410, 1060], follow: .5, lid: .3, smile: -.05, browIn: .3, lean: -.04 }, PHONE_HOLD), [
      { t: tPost + .2, d: .3, angR: -1.15 }, { t: tPost + .5, d: .3, angR: -1.25 },
      { t: tPost + .6, d: .6, smile: .12, lid: .25 },
    ]);
    shot(t0, t1, (ctx, t) => {
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#2a2030'); g.addColorStop(1, '#120e16'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < 8; i++) glow(ctx, 40 + i * 95, 160, 70, ['#ffcf6a', '#ff8ac0', '#8ad0ff'][i % 3], .25);
      // blurred partiers in the background
      ctx.save(); ctx.filter = 'blur(6px)'; ctx.globalAlpha = .55;
      for (const [x, c] of [[90, '#b8443a'], [610, '#e0b43c'], [200, '#3a6ea8']]) { ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse(x, 760, 80, 160, 0, 0, TAU); ctx.fill(); ctx.fillStyle = '#7a5040'; ctx.beginPath(); ctx.arc(x, 560, 50, 0, TAU); ctx.fill(); }
      ctx.restore();
      show(ctx, WR, t, LIGHT.phone(420, 820));
      // "Posted" chip + paper plane
      const a = ramp(t, tPost + .1, tPost + .4);
      if (a > 0) {
        ctx.save(); ctx.globalAlpha = a * (1 - ramp(t, tPost + 2.2, tPost + 2.6));
        ctx.fillStyle = '#2f6fe0'; roundRect(ctx, 400, 760, 150, 46, 23); ctx.fill(); ctx.fillStyle = '#fff'; ctx.font = '600 22px Inter'; ctx.fillText('Posted ✓', 426, 791);
        const p = clamp((t - tPost) / 1.4); ctx.translate(470 + p * 200, 740 - p * 420); ctx.rotate(-.6); ctx.fillStyle = '#eaf2ff';
        ctx.beginPath(); ctx.moveTo(0, -14); ctx.lineTo(22, 0); ctx.lineTo(0, 14); ctx.lineTo(5, 0); ctx.closePath(); ctx.fill(); ctx.restore();
      }
      vignette(ctx, .55);
    }, 0);
  }
  // ===== 7. chatbot conversation b1-b3 =====
  const chatMsgs = [
    { t: 0, me: true, text: 'They boiled John in oil... What is the metaphor for what society is doing to me?' },
    { t: st_('b1') - .1, line: LINE('b1') },
    { t: st_('b2') - .1, line: LINE('b2') },
    { t: st_('b3') - .05, me: true, text: 'Paul?' },
    { t: st_('b6') - .1, line: LINE('b6') },
    { t: st_('g1') - .1, line: LINE('g1') },
    { t: st_('g2') - .1, line: LINE('g2') },
  ];
  {
    const t0 = st_('b1') - .5, t1 = st_('b4') - .4;
    const A = actor('writer', Object.assign({ x: 380, y: 990, s: 1.5, look: [360, 400], follow: .45, lid: .25, browIn: .5, smile: -.15 }, PHONE_HOLD), [
      { t: WT('b1', 'sword') - .1, d: .5, look: [160, 600], follow: .6, browIn: .6 },        // glances at the ghost sword on the wall
      { t: WT('b1', 'cross') - .05, d: .4, look: [600, 600] },
      { t: WT('b1', 'quieter'), d: .7, look: [360, 400], browIn: .4, lid: .2 },
      { t: WT('b1', 'unread'), d: 1.2, lid: .42, browIn: 1, smile: -.35 },                    // it lands: sorrow
      { t: st_('b2') + .2, d: .6, lid: .2, browIn: .5, smile: -.1 },
      { t: WT('b2', 'Paul'), d: .35, lid: -.05, browIn: .7, browOut: .9, browY: .5, open: .15 }, // surprise
      { t: st_('b3') - .1, d: .3, open: 0, smile: .35, headRoll: -.08, browR: .5, look: [360, 360] },
      { t: en_('b3') + .2, d: .5, smile: .5, lid: .2 },                                         // half-laugh
    ]);
    shot(t0, t1, (ctx, t) => {
      aptWriter(ctx, t, A, 'night', {
        under: (c, t) => {
          // ghost sword & cross on the wall dissolve away
          const a1 = ramp(t, WT('b1', 'sword') - .2, WT('b1', 'sword') + .3) * (1 - ramp(t, WT('b1', 'quieter'), WT('b1', 'quieter') + .8));
          const a2 = ramp(t, WT('b1', 'cross') - .2, WT('b1', 'cross') + .3) * (1 - ramp(t, WT('b1', 'quieter'), WT('b1', 'quieter') + .8));
          c.save(); c.globalAlpha = a1 * .35; c.fillStyle = '#c8d4ff'; c.translate(150, 640); c.rotate(.15); c.fillRect(-6, -150, 12, 220); c.fillRect(-40, 60, 80, 12); c.fillRect(-8, 72, 16, 40); c.restore();
          c.save(); c.globalAlpha = a2 * .35; c.fillStyle = '#c8d4ff'; c.fillRect(590, 520, 16, 230); c.fillRect(545, 580, 106, 16); c.restore();
          // the old man in lamplight, foreshadowed on the wall
          const a3 = ramp(t, WT('b2', 'Paul') - .2, WT('b2', 'Paul') + .6) * (1 - ramp(t, en_('b3') + .3, en_('b3') + 1));
          if (a3 > 0) { c.save(); c.globalAlpha = a3 * .5; glow(c, 590, 560, 140, '#ffb35c', .6); c.fillStyle = '#2a1a10'; c.beginPath(); c.arc(570, 540, 32, 0, TAU); c.fill(); c.beginPath(); c.ellipse(570, 640, 60, 70, 0, Math.PI, 0); c.fill(); c.fillRect(510, 640, 120, 30); c.restore(); }
        },
        over: (c, t) => chatPanel(c, 50, 70, 620, 560, chatMsgs, t),
      });
    }, .3);
    LABELS.push({ t0: t0 + .4, text: 'Chatbot', x: 130, y: 52 });
  }
  // ===== 8. wide: dingy apartment, letters to trolls =====
  {
    const t0 = st_('b4') - .4, t1 = st_('b5') - .25, tw = WT('b4', 'writing'), tt = WT('b4', 'trolls');
    const A = actor('writer', Object.assign({ x: 420, y: 790, s: 1.0, look: [450, 880], follow: .5, lid: .3, smile: .25, browIn: .2 }, PHONE_HOLD), [
      { t: WT('b4', 'Sitting'), d: .6, look: [300, 560], smile: .15, browIn: .5, browOut: .2 },   // looks around his room
      { t: WT('b4', 'apartment'), d: .6, look: [450, 880], smile: .2 },
      { t: tt, d: .4, look: [160, 400], browIn: -.2, frown: .3 },
    ]);
    const cam = { x: 360, y: 640, z: 1 };
    shot(t0, t1, (ctx, t) => {
      aptWriter(ctx, t, A, 'night', {
        under: (c, t) => {
          // mattress on the floor + blanket over his knees drawn later; dishes etc. are in the bg
          c.fillStyle = '#7d7a8a'; roundRect(c, 180, 1060, 500, 130, 20); c.fill(); c.fillStyle = '#9a97a6'; roundRect(c, 180, 1050, 500, 40, 18); c.fill();
          c.fillStyle = '#d8d0c0'; roundRect(c, 570, 1020, 110, 50, 20); c.fill(); // pillow
        },
        over: (c, t, st) => {
          // blanket over crossed legs, knees visible through folds
          const g = c.createLinearGradient(0, 1040, 0, 1180); g.addColorStop(0, '#8a4a3a'); g.addColorStop(1, '#5a2e24');
          c.fillStyle = g; c.beginPath(); spline(c, [[220, 1170], [250, 1080], [310, 1045], [420, 1070], [530, 1045], [600, 1080], [630, 1170]], true, .5); c.fill();
          softStroke(c, P2(p => { p.moveTo(310, 1055); p.quadraticCurveTo(340, 1110, 330, 1160); }), '#2a1410', 3, .35);
          softStroke(c, P2(p => { p.moveTo(530, 1055); p.quadraticCurveTo(500, 1110, 510, 1160); }), '#2a1410', 3, .35);
          softStroke(c, P2(p => { p.moveTo(420, 1075); p.quadraticCurveTo(425, 1120, 420, 1165); }), '#2a1410', 3, .25);
          // letters (envelopes) leaving the phone toward the window
          for (let i = 0; i < 6; i++) {
            const p = (t - tw - i * .45) / 1.6; if (p < 0 || p > 1) continue;
            const x = lerp(450, 165, easeIO(p)) + Math.sin(p * 6 + i) * 20, y = lerp(760, 300 + i * 20, easeIO(p)) - Math.sin(p * Math.PI) * 80;
            c.save(); c.translate(x, y); c.rotate(Math.sin(p * 5 + i) * .4); c.globalAlpha = 1 - ramp(p, .8, 1);
            c.fillStyle = '#f0ead8'; c.fillRect(-18, -12, 36, 24); c.strokeStyle = '#a89a78'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(-18, -12); c.lineTo(0, 2); c.lineTo(18, -12); c.stroke(); c.restore();
          }
          // troll avatars outside the window
          const ta = ramp(t, tt - .2, tt + .4);
          for (let i = 0; i < 3; i++) {
            const x = 90 + i * 70, y = 260 + (i % 2) * 70, bob = Math.sin(t * 3 + i) * 4;
            c.save(); c.globalAlpha = ta; c.translate(x, y + bob);
            c.fillStyle = '#6d7480'; c.beginPath(); c.arc(0, 0, 24, 0, TAU); c.fill();
            c.fillStyle = '#1b1d22'; c.fillRect(-11, -5, 6, 4); c.fillRect(5, -5, 6, 4);
            c.strokeStyle = '#1b1d22'; c.lineWidth = 2.5; c.beginPath(); c.moveTo(-9, 10); c.quadraticCurveTo(0, 4 + (i % 2) * 6, 9, 10); c.stroke();
            c.restore();
          }
        },
      });
    }, 0);
  }
  // ===== 9. "that's dumb" -> blocked =====
  {
    const t0 = st_('b5') - .25, t1 = st_('b6') - .45, td = WT('b5', 'that\'s'), tb = WT('b5', 'block');
    const msgs = [
      { t: 0, me: true, text: 'Paul wrote letters from a rented room in chains. Maybe that\'s what posting is for me.' },
      { t: td - .1, troll: true, text: 'that\'s dumb.', meta: 'troll_8841' },
      { t: tb, sys: true, text: 'You\'ve been blocked.' },
    ];
    const A = actor('writer', Object.assign({ x: 380, y: 990, s: 1.5, look: [360, 420], follow: .45, lid: .25, browIn: .4 }, PHONE_HOLD), [
      { t: WT('b5', 'ignore'), d: .5, lid: .4, browIn: .6 },
      { t: td + .1, d: .3, lid: .32, browIn: 0, browOut: 0, smile: -.1, frown: .2 },              // deadpan
      { t: tb + .1, d: .5, lid: .55, browR: .7, browL: -.15, smile: -.25 },                        // one brow up, lips pressed
      { t: en_('b5') + .3, d: .6, look: 'cam', follow: .7, lid: .45 },                               // looks at us
      { t: en_('b5') + 1.0, d: .25, lid: 1 }, { t: en_('b5') + 1.25, d: .3, lid: .45 },               // slow blink
    ]);
    shot(t0, t1, (ctx, t) => aptWriter(ctx, t, A, 'night', { over: (c, t) => chatPanel(c, 50, 70, 620, 560, msgs, t) }), 0);
  }
  // ===== 10. b6: Paul spent two years... -> dissolve into Rome =====
  {
    const t0 = st_('b6') - .45, t1 = st_('d1') - .4;
    const A = actor('writer', Object.assign({ x: 380, y: 990, s: 1.5, look: [360, 400], follow: .45, lid: .3, browIn: .4, smile: -.1 }, PHONE_HOLD), [
      { t: WT('b6', 'Honestly'), d: .4, browR: .4, smile: .15 },
      { t: WT('b6', 'little'), d: .5, smile: .3, lid: .25, browR: 0 },
      { t: WT('b6', 'Paul'), d: .6, smile: 0, browIn: .5, lid: .15, look: [360, 380] },
      { t: WT('b6', 'chained'), d: .7, browIn: .9, smile: -.2 },
      { t: WT('b6', 'often'), d: .8, look: [200, 380], follow: .55, lid: .35 },
    ]);
    shot(t0, t1, (ctx, t) => aptWriter(ctx, t, A, 'night', { over: (c, t) => chatPanel(c, 50, 70, 620, 560, chatMsgs, t) }), 0);
  }
  buildRome();
  buildLetters();
  buildEnd(chatMsgs);
}
let BRICKS_STREET = null;
function bricksCached(ctx) { ctx.drawImage(cached('street', W, H, c => { bricks(c, 0, 0, W, H, '#6a3a2c', 21, 80, 36, '#2a1a14'); }), 0, 0); }

// ---------- martyr panels ----------
function martyrFrame(ctx, t, lt, name, fn) {
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#2a1610'); g.addColorStop(1, '#0e0806'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(360, 120); ctx.scale(.86, .8); ctx.translate(-360, 0); ctx.beginPath(); ctx.moveTo(60, 1080); ctx.lineTo(60, 300); ctx.arc(360, 300, 300, Math.PI, 0); ctx.lineTo(660, 1080); ctx.closePath();
  ctx.save(); ctx.clip(); fn(ctx, t, lt); ctx.restore();
  ctx.strokeStyle = '#c9a24a'; ctx.lineWidth = 8; ctx.stroke(); ctx.strokeStyle = 'rgba(201,162,74,.4)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(48, 1092); ctx.lineTo(48, 300); ctx.arc(360, 300, 312, Math.PI, 0); ctx.lineTo(672, 1092); ctx.closePath(); ctx.stroke();
  ctx.restore();
  ctx.save(); ctx.globalAlpha = ramp(lt, .1, .5); ctx.fillStyle = '#e4c272'; ctx.font = '600 40px "DejaVu Serif"'; ctx.textAlign = 'center'; ctx.letterSpacing = '8px'; ctx.fillText(name, 360, 1170); ctx.restore();
  // fresco grain
  ctx.drawImage(cached('fgrain', W, H, c => grit(c, 0, 0, W, H, '#806040', .8, 99, 5000)), 0, 0);
}
function panelSky(ctx, a, b) { const g = ctx.createLinearGradient(0, 0, 0, 1080); g.addColorStop(0, a); g.addColorStop(1, b); ctx.fillStyle = g; ctx.fillRect(0, 0, W, 1100); }
function panelJohn(ctx, t, lt) {
  panelSky(ctx, '#3a1c12', '#1a0c08');
  fire(ctx, 360, 960, 300, t, 1.1);
  ctx.fillStyle = '#16120f'; ctx.beginPath(); ctx.moveTo(170, 640); ctx.quadraticCurveTo(160, 900, 360, 920); ctx.quadraticCurveTo(560, 900, 550, 640); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#2a221c'; ctx.beginPath(); ctx.ellipse(360, 640, 192, 34, 0, 0, TAU); ctx.fill();
  ctx.fillStyle = '#c08a2a'; ctx.beginPath(); ctx.ellipse(360, 646, 176, 26, 0, 0, TAU); ctx.fill(); // oil surface
  for (let i = 0; i < 9; i++) { const p = (lt * 1.3 + hash(i)) % 1, x = 220 + hash(i + 3) * 280; ctx.strokeStyle = `rgba(255,220,140,${1 - p})`; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, 646, 3 + p * 12, Math.PI, 0); ctx.stroke(); }
  for (let i = 0; i < 6; i++) { const p = (lt * .35 + hash(i + 20)) % 1; ctx.fillStyle = `rgba(220,210,200,${.18 * (1 - p)})`; ctx.beginPath(); ctx.arc(260 + i * 40 + Math.sin(p * 6 + i) * 20, 620 - p * 400, 20 + p * 50, 0, TAU); ctx.fill(); }
  ctx.strokeStyle = '#3a2c22'; ctx.lineWidth = 10; ctx.beginPath(); ctx.arc(360, 600, 210, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
}
function panelCross(ctx, t, lt) {
  panelSky(ctx, '#7a2a1a', '#e08a4a');
  for (let i = 0; i < 4; i++) { ctx.fillStyle = 'rgba(40,10,10,.35)'; ctx.beginPath(); ctx.ellipse(((i * 230 + lt * 25) % 900) - 90, 240 + i * 70, 180, 30, 0, 0, TAU); ctx.fill(); }
  ctx.fillStyle = '#1a0e0a'; ctx.beginPath(); ctx.moveTo(0, 1100); ctx.quadraticCurveTo(360, 760, 720, 1100); ctx.fill();
  const cross = (x, y, s) => { ctx.fillStyle = '#1a0e0a'; ctx.fillRect(x - 9 * s, y - 330 * s, 18 * s, 360 * s); ctx.fillRect(x - 110 * s, y - 270 * s, 220 * s, 16 * s); };
  cross(170, 940, .62); cross(550, 940, .62); cross(360, 880, 1);
  // a small, dignified silhouette, head bowed
  ctx.fillStyle = '#1a0e0a'; ctx.beginPath(); ctx.arc(360, 650, 22, 0, TAU); ctx.fill();
  ctx.beginPath(); ctx.moveTo(266, 618); ctx.lineTo(454, 618); ctx.lineTo(380, 660); ctx.lineTo(372, 790); ctx.lineTo(348, 790); ctx.lineTo(340, 660); ctx.closePath(); ctx.fill();
  // his red tunic (thin yellow stripe) lying at the foot of the cross
  ctx.fillStyle = '#9a2420'; ctx.beginPath(); ctx.moveTo(300, 905); ctx.quadraticCurveTo(360, 880, 430, 900); ctx.lineTo(440, 925); ctx.quadraticCurveTo(360, 935, 296, 925); ctx.fill();
  ctx.strokeStyle = '#d8b040'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(320, 902); ctx.quadraticCurveTo(360, 890, 400, 898); ctx.stroke();
}
function panelStones(ctx, t, lt) {
  panelSky(ctx, '#4a3424', '#1e140c');
  ctx.fillStyle = '#2a1e14'; ctx.fillRect(0, 960, W, 140);
  const r = rng(4);
  for (let i = 0; i < 16; i++) {
    const t0 = i * .09, p = clamp((lt - t0) / .55), x = 220 + r() * 280, rest = 950 - (i > 6 ? 40 + r() * 50 : r() * 20), sz = 22 + r() * 18, rot = r() * 3;
    const y = lerp(-80, rest, p * p);
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot + p * 2);
    ctx.fillStyle = mix('#8a8070', '#5a5248', r()); ctx.beginPath(); ctx.ellipse(0, 0, sz, sz * .75, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.beginPath(); ctx.ellipse(-sz * .3, -sz * .3, sz * .4, sz * .2, 0, 0, TAU); ctx.fill();
    ctx.restore();
    if (p >= 1 && lt - t0 - .55 < .6) { const d = (lt - t0 - .55) / .6; ctx.fillStyle = `rgba(160,140,110,${.3 * (1 - d)})`; ctx.beginPath(); ctx.arc(x, rest, 20 + d * 50, 0, TAU); ctx.fill(); }
  }
}
function panelMatthew(ctx, t, lt) {
  panelSky(ctx, '#2e2218', '#120c08');
  glow(ctx, 360, 760, 320, '#ffb35c', .25);
  ctx.fillStyle = '#4a3020'; ctx.fillRect(80, 860, 560, 240);
  // open book, pages turning in a draft
  ctx.fillStyle = '#e8dcbc'; ctx.beginPath(); ctx.moveTo(360, 840); ctx.quadraticCurveTo(250, 810, 150, 830); ctx.lineTo(150, 700); ctx.quadraticCurveTo(250, 680, 360, 710); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(360, 840); ctx.quadraticCurveTo(470, 810, 570, 830); ctx.lineTo(570, 700); ctx.quadraticCurveTo(470, 680, 360, 710); ctx.closePath(); ctx.fill();
  const pg = (lt * 1.1) % 1;
  ctx.fillStyle = '#f2e8cc'; ctx.beginPath(); ctx.moveTo(360, 840); ctx.lineTo(360, 710); ctx.quadraticCurveTo(360 + Math.cos(pg * Math.PI) * 120, 680 - Math.sin(pg * Math.PI) * 60, 360 + Math.cos(pg * Math.PI) * 210, 700 - Math.sin(pg * Math.PI) * 30); ctx.lineTo(360 + Math.cos(pg * Math.PI) * 210, 830 - Math.sin(pg * Math.PI) * 30); ctx.quadraticCurveTo(360 + Math.cos(pg * Math.PI) * 120, 810, 360, 840); ctx.fill();
  ctx.strokeStyle = 'rgba(80,60,40,.4)'; ctx.lineWidth = 1.5; for (let i = 0; i < 9; i++) { ctx.beginPath(); ctx.moveTo(175, 725 + i * 11); ctx.lineTo(340, 735 + i * 11); ctx.stroke(); }
  // tax coins (he was a tax collector) and a curved knife, glinting
  for (let i = 0; i < 6; i++) { ctx.fillStyle = '#c9a24a'; ctx.beginPath(); ctx.ellipse(170 + i * 14, 930 - i * 5, 22, 8, 0, 0, TAU); ctx.fill(); ctx.strokeStyle = '#7a5a20'; ctx.stroke(); }
  ctx.save(); ctx.translate(480, 940); ctx.rotate(-.2); ctx.fillStyle = '#9aa0a8'; ctx.beginPath(); ctx.moveTo(-90, 0); ctx.quadraticCurveTo(-20, -30, 40, -4); ctx.lineTo(40, 6); ctx.quadraticCurveTo(-20, -12, -90, 0); ctx.fill();
  ctx.fillStyle = '#4a3020'; ctx.fillRect(40, -6, 60, 14);
  const gl = Math.max(0, Math.sin(lt * 2.4)); ctx.fillStyle = `rgba(255,255,255,${gl * .8})`; ctx.beginPath(); ctx.arc(-20 + gl * 30, -12, 4, 0, TAU); ctx.fill(); ctx.restore();
}
function panelPeter(ctx, t, lt) {
  panelSky(ctx, '#1e2a3a', '#0a0e16');
  ctx.fillStyle = '#0c0c10'; ctx.fillRect(0, 980, W, 120);
  const rot = easeIO(clamp((lt - .2) / 1.2)) * Math.PI;
  ctx.save(); ctx.translate(360, 640); ctx.rotate(rot);
  ctx.fillStyle = '#4a3420'; ctx.fillRect(-12, -330, 24, 640); ctx.fillRect(-120, -200, 240, 22);
  ctx.fillStyle = 'rgba(255,220,160,.15)'; ctx.fillRect(-12, -330, 6, 640);
  ctx.restore();
  // crossed keys at the base
  ctx.save(); ctx.translate(360, 1030); ctx.rotate(-.08); ctx.strokeStyle = '#c9a24a'; ctx.fillStyle = '#c9a24a'; ctx.lineWidth = 9;
  ctx.beginPath(); ctx.ellipse(-95, 0, 26, 20, 0, 0, TAU); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-69, 0); ctx.lineTo(90, 0); ctx.stroke();
  ctx.fillRect(56, 0, 12, 26); ctx.fillRect(76, 0, 12, 34); ctx.fillStyle = 'rgba(255,255,255,.4)'; ctx.fillRect(-60, -3, 120, 2); ctx.restore();
}
function panelOlive(ctx, t, lt) {
  panelSky(ctx, '#3a3a5a', '#d08a5a');
  ctx.fillStyle = '#1a1612'; ctx.beginPath(); ctx.moveTo(0, 1100); ctx.quadraticCurveTo(360, 900, 720, 1100); ctx.fill();
  // gnarled trunk
  ctx.fillStyle = '#2a2018'; ctx.beginPath(); ctx.moveTo(320, 990); ctx.bezierCurveTo(300, 860, 380, 800, 330, 640); ctx.lineTo(380, 640); ctx.bezierCurveTo(420, 780, 360, 860, 410, 990); ctx.fill();
  ctx.strokeStyle = '#2a2018'; ctx.lineWidth = 22; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(350, 660); ctx.quadraticCurveTo(470, 600, 560, 620); ctx.stroke(); ctx.lineWidth = 16; ctx.beginPath(); ctx.moveTo(350, 660); ctx.quadraticCurveTo(250, 590, 170, 600); ctx.stroke();
  // silver-green leaves rustling
  const r = rng(8);
  for (let i = 0; i < 90; i++) { const x = 130 + r() * 470, y = 470 + r() * 200, a = r() * TAU + Math.sin(t * 2 + i) * .2; ctx.fillStyle = r() < .5 ? '#6a7a5a' : '#9aa88a'; ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.beginPath(); ctx.ellipse(0, 0, 14, 4, 0, 0, TAU); ctx.fill(); ctx.restore(); }
  // empty rope swaying from a branch
  const sw = Math.sin(lt * 1.6) * .12;
  ctx.save(); ctx.translate(500, 615); ctx.rotate(sw); ctx.strokeStyle = '#8a7350'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 170); ctx.stroke(); ctx.beginPath(); ctx.ellipse(0, 190, 16, 22, 0, 0, TAU); ctx.stroke(); ctx.restore();
}
function panelSword(ctx, t, lt) {
  panelSky(ctx, '#2a2a30', '#0c0c10');
  ctx.fillStyle = '#16120e'; ctx.fillRect(0, 960, W, 140);
  const p = easeOut(clamp((lt - .15) / .5)), y = lerp(-300, 760, p * p);
  ctx.save(); ctx.translate(360, y);
  const g = ctx.createLinearGradient(-14, 0, 14, 0); g.addColorStop(0, '#7a8088'); g.addColorStop(.5, '#e8ecf0'); g.addColorStop(1, '#6a7078'); ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(-14, -260); ctx.lineTo(14, -260); ctx.lineTo(12, 180); ctx.lineTo(0, 220); ctx.lineTo(-12, 180); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#8a6a2a'; ctx.fillRect(-70, -280, 140, 20); ctx.fillStyle = '#4a3018'; ctx.fillRect(-10, -380, 20, 100); ctx.fillStyle = '#c9a24a'; ctx.beginPath(); ctx.arc(0, -390, 16, 0, TAU); ctx.fill();
  ctx.restore();
  const hit = lt - .65;
  if (hit > 0 && hit < .8) { ctx.fillStyle = `rgba(255,255,255,${.5 * (1 - hit / .8)})`; ctx.beginPath(); ctx.arc(360, 960, 30 + hit * 160, 0, TAU); ctx.fill(); ctx.fillStyle = `rgba(150,130,110,${.35 * (1 - hit / .8)})`; ctx.beginPath(); ctx.ellipse(360, 965, 60 + hit * 200, 20 + hit * 30, 0, 0, TAU); ctx.fill(); }
  // scallop shell
  ctx.save(); ctx.translate(470, 1010); ctx.fillStyle = '#d8c8a8'; ctx.beginPath(); ctx.moveTo(0, 20); for (let i = 0; i <= 8; i++) { const a = Math.PI + i / 8 * Math.PI; ctx.quadraticCurveTo(Math.cos(a - .2) * 40, Math.sin(a - .2) * 40 + 10, Math.cos(a) * 34, Math.sin(a) * 34 + 10); } ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(120,100,70,.6)'; ctx.lineWidth = 1.5; for (let i = 1; i < 8; i++) { const a = Math.PI + i / 8 * Math.PI; ctx.beginPath(); ctx.moveTo(0, 20); ctx.lineTo(Math.cos(a) * 32, Math.sin(a) * 32 + 10); ctx.stroke(); } ctx.restore();
}
