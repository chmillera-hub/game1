// ---------- Rome ----------
function romeRoom(ctx, t, opts = {}) {
  ctx.drawImage(romeBG(), -200, -200);
  // light shaft from the high window
  ctx.save(); ctx.globalCompositeOperation = 'screen'; const g = ctx.createLinearGradient(545, 200, 300, 900); g.addColorStop(0, 'rgba(255,190,120,.22)'); g.addColorStop(1, 'rgba(255,190,120,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(480, 140); ctx.lineTo(610, 140); ctx.lineTo(420, 950); ctx.lineTo(160, 950); ctx.fill(); ctx.restore();
  door(ctx, 10, 430, 150, 460, opts.door || 0, '#5a3a22', '#3a2618');
  if (opts.doorBehind) opts.doorBehind(ctx);
}
function buildRome() {
  const T = t => t;
  const paulBase = { x: 250, y: 840, s: 1.3, look: [300, 1015], follow: .55, lid: .3, squint: .35, browIn: .2, smile: 0,
    armR: [40, 128], handR: 'pen', holdR: 'stylus', angR: -.5, armL: [-48, 134], handL: 'flat', angL: .3, nod: .5, elbowR: .6 };
  const lukeBase = { x: 565, y: 865, s: 1.15, turn: -.25, look: [250, 700], follow: .6, lid: .15, smile: .15, armL: [-60, 130], armR: [30, 140], handL: 'relax', handR: 'relax' };
  const guardBase = { x: 92, y: 700, s: .95, look: [300, 900], follow: .6, lid: .45, browIn: -.3, smile: -.3, armL: [-30, 220], armR: [26, 216], handR: 'grip', handL: 'relax' };
  // --- writing hand motion (stylus strokes) as additive key noise ---
  const writing = (st, t, on) => { if (!on) return; st.armR = [st.armR[0] + Math.sin(t * 5) * 6 + ((t * 1.2) % 1) * 18, st.armR[1] + Math.sin(t * 11) * 2]; };
  const chainTo = (ctx, from, to, t, shine) => chainPath(ctx, sampleCurve(from, [(from[0] + to[0]) / 2, Math.max(from[1], to[1]) + 70], to, 24), t, shine);
  const wristWorld = (st, arms, side) => { const w = arms[side].w; return [st.x + w[0] * st.s, st.y + w[1] * st.s]; };

  // ===== d1: establishing wide =====
  {
    const t0 = st_('d1') - .4, t1 = st_('d2') - .35;
    const tLamp = WT('d1', 'lamp'), tChain = WT('d1', 'chain'), tGuard = WT('d1', 'guard');
    const P = actor('paul', Object.assign({}, paulBase), [{ t: tChain - .1, d: .5, armL: [-48, 118] }, { t: tChain + .6, d: .6, armL: [-48, 134] }]);
    const L = actor('luke', Object.assign({}, lukeBase, { look: [300, 1015] }));
    const G = actor('guard', Object.assign({}, guardBase), [
      { t: tGuard + .1, d: .4, gaze: [-.3, -1], follow: 0, lid: .2, browIn: -.1, browOut: .4 },   // eye-roll up...
      { t: tGuard + .5, d: .5, gaze: [.6, -.6], shrug: 1, open: .25, round: .8 },                    // ...and a long sigh
      { t: tGuard + 1.2, d: .8, gaze: [0, 0], follow: .6, shrug: 0, open: 0, lid: .5, smile: -.35 },
    ]);
    const cam = { x: 360, y: 760, z: .8 };
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, W, H);
      ctx.save(); applyCam(ctx, cam); romeRoom(ctx, t); ctx.restore();
      const lampK = 1 + ramp(t, tLamp - .1, tLamp + .3) * .6 * (1 - ramp(t, tLamp + .8, tLamp + 1.6));
      const lp = toScreen(cam, 420, 960);
      let pst, parms;
      const pl = LIGHT.lamp(lp[0], lp[1], lampK);
      show(ctx, G, t, Object.assign({}, pl, { str: .12 }), cam);
      show(ctx, L, t, pl, cam);
      pst = show(ctx, P, t, pl, cam, st => { writing(st, t, t < tChain - .2 || t > tChain + 1); st.top = (c, arms) => { parms = arms; }; });
      ctx.save(); applyCam(ctx, cam);
      table(ctx, -200, 1000, 1120, 400);
      scroll(ctx, 280, 1022, 150, 40, -.04, 1, .5);
      oilLamp(ctx, 420, 990, 1.1 * lampK, t);
      if (parms) chainTo(ctx, wristWorld(pst, parms, 'L'), [118, 905], t, ramp(t, tChain - .1, tChain + .2) * (1 - ramp(t, tChain + .9, tChain + 1.4)));
      ctx.restore();
      vignette(ctx, .6);
    }, .9);
    LABELS.push({ t0: WT('d1', 'One') + .2, text: 'Paul', x: 272, y: 470 }, { t0: WT('d1', 'One') + .8, text: 'Luke', x: 524, y: 500 }, { t0: tGuard, text: 'Roman guard', x: 146, y: 405 });
  }
  // ===== d2, d3, d5, d6 two-shot; d4 close-up between =====
  const twoShot = (t0, t1, keysP, keysL, keysG, xin = 0, extra) => {
    const P = actor('paul', Object.assign({}, paulBase), keysP), L = actor('luke', Object.assign({}, lukeBase), keysL), G = actor('guard', Object.assign({}, guardBase), keysG);
    const cam = { x: 350, y: 800, z: 1.12 };
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, W, H);
      ctx.save(); applyCam(ctx, cam); romeRoom(ctx, t); ctx.restore();
      const lp = toScreen(cam, 420, 960), pl = LIGHT.lamp(lp[0], lp[1]);
      let pst, parms;
      show(ctx, G, t, Object.assign({}, pl, { str: .1 }), cam);
      pst = show(ctx, P, t, pl, cam, st => { writing(st, t, st.handR === 'pen' && st.writing !== 0 && !speaking('PAUL', t) && t < (extra && extra.stopWrite || 1e9)); st.top = (c, arms) => { parms = arms; }; });
      show(ctx, L, t, pl, cam);
      ctx.save(); applyCam(ctx, cam);
      table(ctx, -200, 1000, 1120, 400);
      scroll(ctx, 280, 1022, 150, 40, -.04, 1, clamp(.5 + (t - t0) * .02, 0, 1));
      oilLamp(ctx, 420, 990, 1.1, t);
      if (parms) chainTo(ctx, wristWorld(pst, parms, 'L'), [118, 905], t, 0);
      ctx.restore();
      vignette(ctx, .6);
    }, xin);
  };
  // d2 + d3
  twoShot(st_('d2') - .35, st_('d4') - .45, [
    { t: st_('d2'), d: .4, browIn: .3, squint: .5 },
    { t: WT('d2', 'hand'), d: .5, smile: .2 },                                      // wry: his big handwriting
    { t: WT('d2', 'Remember'), d: .6, look: [170, 1000], squint: 0, lid: .25, browIn: .7, smile: -.1 }, // glances at the chain
    { t: st_('d3') - .1, d: .7, look: [560, 700], follow: .6, lid: .2, browIn: .4, smile: 0, armR: [60, 120], handR: 'relax', holdR: 'stylus' }, // turns to Luke
    { t: WT('d3', 'Some'), d: .5, smile: .25, lid: .3, browIn: .2 },              // a tired little smile
  ], [
    { t: st_('d2') + .5, d: .6, look: [300, 1010] },
    { t: st_('d3') - .3, d: .5, look: [270, 700], smile: .35, browIn: .2, browOut: .3, armL: [-90, 110], handL: 'open', gest: 1.5 }, // encouraging
    { t: WT('d3', 'Some'), d: .5, smile: .2, browOut: 0, armL: [-60, 130], handL: 'relax', headRoll: .06 },
  ], [
    { t: st_('d2') + 1, d: 1.2, look: [300, 1015], lid: .55 },
  ]);
  // d4 close-up: abandonment, one tear
  {
    const t0 = st_('d4') - .45, t1 = st_('d5') - .5;
    const tNo = WT('d4', 'no'), tEv = WT('d4', 'Everyone');
    const P = actor('paul', { x: 360, y: 1030, s: 2.5, look: [560, 700], follow: .4, lid: .25, browIn: .4, smile: -.05, armL: [-60, 220], armR: [60, 220], handL: 'relax', handR: 'relax', nod: .4 }, [
      { t: WT('d4', 'Demas') - .1, d: .5, look: [380, 1060], lid: .4, browIn: .7 },               // glance down: recalling
      { t: WT('d4', 'deserted') + .2, d: .6, look: [560, 720], lid: .25, browIn: .9, smile: -.25 }, // back up
      { t: WT('d4', 'first'), d: 1, tearful: .9, browIn: 1.1, browY: .2 },
      { t: tEv - .1, d: 1.0, lid: .7, headPitch: .12, smile: -.35, look: [380, 1000] },             // eyes lower, head bows
      { t: en_('d4') + .3, d: 1.0, lid: .5 },
    ]);
    P.tr.base.tears = [{ side: -1, t0: tNo - .2, dur: 4.2 }];
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, W, H);
      ctx.save(); applyCam(ctx, { x: 300, y: 520, z: 1.6 }); romeRoom(ctx, t); ctx.restore();
      ctx.fillStyle = 'rgba(10,6,4,.35)'; ctx.fillRect(0, 0, W, H);
      glow(ctx, 640, 1000, 420, '#ffb35c', .35);
      show(ctx, P, t, LIGHT.lamp(660, 980, 1.1));
      vignette(ctx, .65);
    }, 0);
  }
  // d5 + d6: "Not everyone." hand on shoulder
  twoShot(st_('d5') - .5, st_('d7') - .45, [
    { t: 0, look: [300, 1015], lid: .55, browIn: .8, smile: -.3, handR: 'relax', armR: [60, 128], tearful: .5 },
    { t: WT('d5', 'everyone') + .2, d: .8, look: [560, 700], follow: .65, lid: .25, browIn: .5 },          // turns to Luke
    { t: st_('d6') - .1, d: .5, smile: .3, squint: .3, tearful: .3 },
    { t: WT('d6', 'Luke'), d: .6, smile: .55, squint: .45, browIn: .2, headRoll: -.06 },              // warm crinkled smile
  ], [
    { t: 0, look: [250, 700], smile: 0, browIn: .6, lid: .2 },
    { t: st_('d5') - .4, d: .9, armL: [-205, 118], handL: 'flat', angL: .25, smile: .2, browIn: .4 }, // rests his hand on Paul's writing hand
    { t: WT('d6', 'Luke'), d: .6, smile: .55, lid: .25, squint: .3 },
  ], [
    { t: WT('d6', 'Luke') + .2, d: .4, smile: .2, lid: .35, gaze: [.8, -.4], follow: 0 },              // guard smirks/rolls eyes
    { t: WT('d6', 'Luke') + 1.0, d: .6, smile: -.2, lid: .5, gaze: [0, 0], follow: .6 },
  ], 0, { stopWrite: 0 });
  // d7: chained like a criminal / the word is not chained
  {
    const t0 = st_('d7') - .45, t1 = st_('d8') - .05, tBut = WT('d7', 'But'), tNot = WT('d7', 'not');
    const P = actor('paul', { x: 330, y: 980, s: 1.75, look: [210, 860], follow: .55, lid: .25, browIn: .6, smile: -.1, armL: [-90, 150], handL: 'grip', armR: [50, 170], handR: 'grip', angR: 0, holdR: null, nod: .6 }, [
      { t: st_('d7') - .2, d: .9, armL: [-58, 40], angL: 0 },                                        // lifts the chained wrist
      { t: WT('d7', 'criminal'), d: .5, browIn: .9, smile: -.25, lid: .35 },
      { t: tBut - .2, d: .9, armL: [-90, 160], armR: [66, 30], angR: 0, look: [520, 380], follow: .6, browIn: .2, browOut: .4, lid: .1, smile: .2 }, // raises the letter, looks to the light
      { t: tNot, d: .6, smile: .45, browOut: .6 },
    ]);
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, W, H);
      ctx.save(); applyCam(ctx, { x: 360, y: 560, z: 1.25 }); romeRoom(ctx, t); ctx.restore();
      const swell = ramp(t, tBut, tNot + .8);
      ctx.save(); ctx.globalCompositeOperation = 'screen'; glow(ctx, 560, 280, 600, '#ffcf8a', .35 * swell); ctx.restore();
      let parms, pst;
      pst = show(ctx, P, t, LIGHT.lamp(560, 400, 1 + swell * .6), null, st => {
        st.top = (c, arms) => {
          parms = arms;
          // chain hanging from the raised wrist
          const w = arms.L.w; chainPath(c, sampleCurve([w[0], w[1] + 10], [w[0] - 20, w[1] + 140], [-180, 260], 18), t, ramp(t, st_('d7'), st_('d7') + .6) * (1 - ramp(t, tBut, tBut + .5)));
          // the rolled letter in the other hand
          const r = arms.R.w; rolledLetter(c, r[0] + 30, r[1] - 40, 120, -1.2);
        };
      });
      table(ctx, 0, 1150, W, 200);
      vignette(ctx, .6 - swell * .2);
    }, 0);
  }
  // d8: the door swings open; the letter leaves
  {
    const t0 = st_('d8') - .05, t1 = st_('e1') - .2;
    const tO = t0 + .2, tHand = t0 + 1.4;
    const P = actor('paul', Object.assign({}, paulBase, { look: [120, 650], handR: 'relax', holdR: null, armR: [60, 128], lid: .2, squint: 0, smile: .2, browIn: .3 }), [
      { t: tHand - .6, d: .7, armL: [-150, 40], handL: 'hold', angL: 0 },
      { t: tHand + .6, d: .6, armL: [-48, 134], handL: 'flat', smile: .35 },
    ]);
    const L = actor('luke', Object.assign({}, lukeBase, { look: [120, 650], smile: .3 }));
    const G = actor('guard', Object.assign({}, guardBase, { x: 92 }), [{ t: tO - .1, d: 1.0, x: -140, lid: .5, look: [80, 620], ease: ease }]);   // steps aside, reluctantly
    const CR = actor('courier', { x: 80, y: 720, s: .82, look: [250, 760], follow: .6, smile: .2, armL: [-30, 200], armR: [40, 200], handR: 'relax' }, [
      { t: tHand - .4, d: .6, armR: [130, 60], handR: 'hold' }, { t: tHand + .5, d: .6, armR: [40, 180] },
    ]);
    const cam = { x: 190, y: 740, z: 1.25 };
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, W, H);
      const op = easeIO(clamp((t - tO) / 1.1));
      ctx.save(); applyCam(ctx, cam); romeRoom(ctx, t, { door: op }); ctx.restore();
      // courier in the doorway with outdoor light behind
      if (op > .05) { ctx.save(); applyCam(ctx, cam); ctx.fillStyle = `rgba(255,200,140,${.5 * op})`; ctx.fillRect(10 + 150 * Math.cos(op * 1.35), 430, 150 - 150 * Math.cos(op * 1.35), 460); ctx.restore(); }
      const lp = toScreen(cam, 420, 960), pl = LIGHT.lamp(lp[0], lp[1]);
      if (op > .3) show(ctx, CR, t, Object.assign({}, LIGHT.lamp(toScreen(cam, 0, 600)[0], 500), { rimColor: '#ffd0a0' }), cam);
      show(ctx, G, t, Object.assign({}, pl, { str: .12 }), cam);
      let parms, pst;
      pst = show(ctx, P, t, pl, cam, st => { st.top = (c, arms) => { parms = arms; }; });
      show(ctx, L, t, pl, cam);
      ctx.save(); applyCam(ctx, cam);
      table(ctx, -200, 1000, 1120, 400); oilLamp(ctx, 420, 990, 1.1, t);
      if (parms) {
        const pw = wristWorld(pst, parms, 'L');
        chainTo(ctx, pw, [195, 905], t, 0);
        const k = clamp((t - tHand) / .5), lx = lerp(pw[0] - 20, 150, k), ly = lerp(pw[1] - 20, 750, k);
        if (t > tHand - .6) rolledLetter(ctx, lx, ly, 90, -.3 - k * .5);
      }
      ctx.restore();
      vignette(ctx, .6);
    }, 0);
  }
}
// ---------- letters travel, the official, Philippi, books ----------
function walker(ctx, x, y, s, t, col, dir = -1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s * dir, s);
  const ph = t * 6;
  ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineCap = 'round';
  for (const k of [0, 1]) { const a = Math.sin(ph + k * Math.PI) * .45; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.sin(a) * 30, Math.cos(a) * 30); ctx.lineTo(Math.sin(a) * 30 + Math.sin(a - .3 * (1 + Math.cos(ph + k * Math.PI))) * 30, Math.cos(a) * 30 + 28); ctx.stroke(); }
  ctx.beginPath(); ctx.moveTo(-14, -60); ctx.lineTo(14, -60); ctx.lineTo(18, 6); ctx.lineTo(-18, 6); ctx.fill();
  ctx.lineWidth = 8; for (const k of [0, 1]) { const a = Math.sin(ph + k * Math.PI + Math.PI) * .4; ctx.beginPath(); ctx.moveTo(0, -54); ctx.lineTo(Math.sin(a) * 26, -54 + Math.cos(a) * 26); ctx.lineTo(Math.sin(a) * 26 + 8, -54 + Math.cos(a) * 26 + 22); ctx.stroke(); }
  ctx.beginPath(); ctx.arc(2, -76, 13, 0, TAU); ctx.fill();
  ctx.fillRect(10, -40, 16, 22); // satchel
  ctx.restore();
}
function buildLetters() {
  // ===== e1 road & sea =====
  {
    const t0 = st_('e1') - .2, tSea = WT('e1', 'sea') - .25, t1 = st_('e2') - .4;
    shot(t0, tSea, (ctx, t) => {
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#41406a'); g.addColorStop(.5, '#e58a5a'); g.addColorStop(1, '#f2c27a'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      glow(ctx, 520, 640, 300, '#fff0b0', .7);
      ctx.fillStyle = '#6a4a5a'; ctx.beginPath(); ctx.moveTo(0, 760); ctx.quadraticCurveTo(200, 660, 420, 740); ctx.quadraticCurveTo(600, 690, 720, 730); ctx.lineTo(720, H); ctx.lineTo(0, H); ctx.fill();
      ctx.fillStyle = '#3a2a30'; ctx.beginPath(); ctx.moveTo(0, 880); ctx.quadraticCurveTo(360, 800, 720, 860); ctx.lineTo(720, H); ctx.lineTo(0, H); ctx.fill();
      // road receding
      ctx.fillStyle = '#7a6a5a'; ctx.beginPath(); ctx.moveTo(140, H); ctx.lineTo(380, 840); ctx.lineTo(420, 840); ctx.lineTo(620, H); ctx.fill();
      ctx.strokeStyle = 'rgba(40,30,20,.35)'; ctx.lineWidth = 2; for (let i = 0; i < 12; i++) { const y = 850 + i * i * 4; ctx.beginPath(); ctx.moveTo(400 - (y - 840) * .6, y); ctx.lineTo(400 + (y - 840) * .6, y); ctx.stroke(); }
      // cypress trees
      for (const [x, h] of [[90, 260], [620, 300], [680, 220]]) { ctx.fillStyle = '#1e2a20'; ctx.beginPath(); ctx.ellipse(x, 860 - h / 2, 24, h / 2, 0, 0, TAU); ctx.fill(); }
      const p = (t - t0) / (tSea - t0); walker(ctx, lerp(470, 400, p), lerp(1130, 900, p), lerp(1.6, 1.0, p), t, '#2a1a20', 1);
    }, .25);
    shot(tSea, t1, (ctx, t) => {
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#5a6a9a'); g.addColorStop(.55, '#f0b080'); g.addColorStop(.56, '#2a4a6a'); g.addColorStop(1, '#0e1e30'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      glow(ctx, 360, 700, 260, '#ffe0a0', .6);
      const sx = lerp(560, 240, (t - tSea) / (t1 - tSea)), bob = Math.sin(t * 2) * 6, rk = Math.sin(t * 1.6) * .04;
      ctx.save(); ctx.translate(sx, 760 + bob); ctx.rotate(rk);
      ctx.fillStyle = '#3a2418'; ctx.beginPath(); ctx.moveTo(-130, 0); ctx.lineTo(130, 0); ctx.quadraticCurveTo(110, 50, 70, 54); ctx.lineTo(-90, 54); ctx.quadraticCurveTo(-130, 40, -150, -10); ctx.fill();
      ctx.fillStyle = '#5a3a24'; ctx.fillRect(-4, -250, 8, 252);
      ctx.fillStyle = '#e8dcc0'; ctx.beginPath(); ctx.moveTo(-90, -230); ctx.quadraticCurveTo(-10, -210 + Math.sin(t * 2) * 8, 90, -230); ctx.lineTo(96, -50); ctx.quadraticCurveTo(0, -30, -96, -50); ctx.fill();
      ctx.fillStyle = '#9b2a22'; ctx.fillRect(-90, -150, 186, 14);
      ctx.restore();
      for (let r = 0; r < 7; r++) { ctx.strokeStyle = `rgba(200,220,255,${.25 - r * .02})`; ctx.lineWidth = 3; ctx.beginPath(); for (let x = 0; x <= W; x += 20) { const y = 830 + r * 60 + Math.sin(x * .03 + t * 2 + r) * 8; x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
    }, 0);
  }
  // ===== e2-e4 the official =====
  const offBase = { x: 330, y: 830, s: 1.3, look: [140, 760], follow: .6, lid: .35, browIn: -.1, smile: -.1, armL: [-70, 200], armR: [70, 200], handL: 'flat', handR: 'flat', nod: .5 };
  {
    const t0 = st_('e2') - .4, t1 = st_('e5') - .2;
    const tLand = WT('e2', 'landed'), tPick = en_('e2') + .1, tC1 = WT('e3', 'Christ'), tAgain = WT('e4', 'Again');
    const tCr = en_('e4') + .15, tThrow = tCr + .95, tHit = tThrow + .55;
    const O = actor('official', Object.assign({}, offBase), [
      { t: tLand, d: .6, look: [300, 1000] },
      { t: tPick, d: .7, armL: [-75, 105], armR: [75, 105], handL: 'hold', handR: 'hold', angL: -.9, angR: .9, look: [330, 950], follow: .5, lid: .5 }, // unrolls & reads, bored
      { t: tC1 - .05, d: .35, lid: .25, browIn: -.4, frown: .4 },                                     // the name lands
      { t: en_('e3') + .1, d: .4, look: 'cam', follow: .4, lid: .2, browIn: -.8, frown: .8, sneer: .6, smile: -.4 }, // looks up, scowling
      { t: st_('e4'), d: .3, browIn: -1, frown: 1, squint: .5, smile: -.6 },
      { t: tAgain, d: .3, lid: .4, headRoll: .06 },
      { t: tCr, d: .55, armL: [-22, 120], armR: [22, 120], handL: 'grip', handR: 'grip', look: [330, 980] },   // crumples it
      { t: tCr + .55, d: .4, armL: [-70, 200], handL: 'flat', armR: [150, 20], handR: 'grip', angR: -.4, look: [600, 860], follow: .7 }, // wind up toward the fire
      { t: tThrow, d: .2, armR: [210, 90], handR: 'open' },
      { t: tHit + .2, d: .5, armR: [40, 140], armL: [-40, 140], handL: 'flat', handR: 'flat', angL: -.8, angR: .8, look: [560, 860], smile: .25, frown: .2, sneer: .1, squint: .2, browIn: -.2 }, // dusts off his hands, smug
    ]);
    const S = actor('servant', { x: -120, y: 780, s: 1.05, look: [330, 760], follow: .6, lid: .25, browIn: .4, smile: 0, armL: [-30, 190], armR: [60, 130], handR: 'hold' }, [
      { t: t0 + .1, d: 1.4, x: 120, ease: ease },
      { t: tLand - .1, d: .6, armR: [190, 190], handR: 'hold' },
      { t: tLand + .7, d: .6, armR: [40, 200], handR: 'relax' },
      { t: tPick + .4, d: 1.4, x: -160, ease: ease },
    ]);
    shot(t0, t1, (ctx, t) => {
      ctx.drawImage(villaBG(), 0, 0);
      const flare = 1 + ramp(t, tHit, tHit + .2) * .8 * (1 - ramp(t, tHit + .5, tHit + 1.6));
      fire(ctx, 570, 890, 160, t, flare);
      const fl = LIGHT.fire(570, 860, flare);
      show(ctx, S, t, fl);
      let ost, oarms;
      ost = show(ctx, O, t, fl, null, st => {
        st.mid = (c, arms) => {
          oarms = arms;
          if (t >= tPick + .3 && t < tCr + .55) { // the open letter between his hands; crumpling as they close
            const a = arms.L.w, b = arms.R.w, k = ramp(t, tCr, tCr + .55);
            const wdt = Math.abs(b[0] - a[0]) + 30;
            if (k < .9) scroll(c, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 10, wdt * (1 - k * .7), 110 * (1 - k * .5), 0, 1, .9);
            if (k > .5) crumpled(c, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 10, 30, t);
          }
          if (t >= tCr + .55 && t < tThrow + .05) { const r = arms.R.w; crumpled(c, r[0] + 30, r[1], 28, t); }
        };
      });
      // letter on the desk before he picks it up; ball in flight into the fire
      if (t >= tLand + .3 && t < tPick + .3) rolledLetter(ctx, 330, 1015, 110, .05);
      if (t >= tThrow && t < tHit + .9) {
        const k = clamp((t - tThrow) / (tHit - tThrow));
        const x = lerp(330 + 210 * 1.3 * .9, 575, k), y = lerp(830 + 90 * 1.3, 880, k) - Math.sin(k * Math.PI) * 140;
        crumpled(ctx, x, y, 28, t, ramp(t, tHit, tHit + .9));
      }
      if (t >= tLand - .1 && t < tLand + .4) { const k = clamp((t - tLand + .1) / .5); rolledLetter(ctx, lerp(120 + 190 * 1.05, 330, k), lerp(780 + 190 * 1.05, 1015, k), 110, .05); }
      // desk across the foreground
      table(ctx, 0, 1010, W, 300, '#4a2c1c');
      vignette(ctx, .5);
    }, .3);
    LABELS.push({ t0: st_('e2') + .3, text: 'Roman official', x: 330, y: 470 });
  }
  // ===== e5: the writer laughs; the letter burns; the scowl =====
  {
    const t0 = st_('e5') - .2, tThrew = WT('e5', 'threw') - .1, tScowl = WT('e5', 'scowl') - .2, t1 = st_('e6') - .4;
    const A = actor('writer', Object.assign({ x: 360, y: 930, s: 1.9, look: [360, 560], follow: .5, lid: .7, squint: 1, smile: 1, open: .5, headPitch: -.15, headRoll: .1 }, PHONE_HOLD), [
      { t: WT('e5', 'bet'), d: .5, lid: .3, squint: .4, smile: .7, open: 0, headPitch: 0, headRoll: .04, look: [360, 600] },
      { t: WT('e5', 'crumpled'), d: .4, smile: .85, squint: .6 },
    ]);
    shot(t0, tThrew, (ctx, t) => aptWriter(ctx, t, A, 'night', {}, null), 0);
    // laughing shoulders
    A.tr.add({ t: t0, d: .01, shrug: 0 });
    shot(tThrew, tScowl, (ctx, t) => {
      ctx.fillStyle = '#0c0806'; ctx.fillRect(0, 0, W, H);
      ctx.save(); applyCam(ctx, { x: 570, y: 850, z: 2.2 }); ctx.drawImage(villaBG(), 0, 0); fire(ctx, 570, 890, 160, t, 1.1);
      crumpled(ctx, 575, 870, 28, t, clamp((t - tThrew) / 2.5)); ctx.restore();
      vignette(ctx, .5);
    }, 0);
    const O = actor('official', Object.assign({}, offBase, { x: 360, y: 1020, s: 2.3, look: [620, 1100], follow: .5, lid: .4, browIn: -1, frown: 1, squint: .5, sneer: .5, smile: -.55, armL: [-60, 260], armR: [60, 260] }));
    shot(tScowl, t1, (ctx, t) => {
      ctx.save(); applyCam(ctx, { x: 300, y: 500, z: 1.5 }); ctx.drawImage(villaBG(), 0, 0); ctx.restore();
      ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(0, 0, W, H);
      show(ctx, O, t, LIGHT.fire(700, 1100, 1.3));
      vignette(ctx, .6);
    }, 0);
  }
  // ===== e6: ashes =====
  {
    const t0 = st_('e6') - .4, t1 = st_('f1') - .3;
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#080504'; ctx.fillRect(0, 0, W, H);
      const lt = t - t0; ctx.save(); ctx.translate(0, -230);
      glow(ctx, 360, 1000, 420, '#ff6a20', .3);
      ctx.fillStyle = '#1a0e08'; ctx.fillRect(0, 980, W, 300);
      for (let i = 0; i < 3; i++) { ctx.fillStyle = '#2a1a10'; ctx.save(); ctx.translate(220 + i * 140, 990); ctx.rotate((i - 1) * .15); roundRect(ctx, -90, -14, 180, 28, 12); ctx.fill(); ctx.fillStyle = `rgba(255,${90 + i * 30},30,${.4 + .2 * Math.sin(t * 3 + i)})`; ctx.fillRect(-60, -4, 120, 6); ctx.restore(); }
      // curled charred paper
      ctx.fillStyle = '#1c1612'; ctx.beginPath(); ctx.ellipse(360, 960, 60, 16, .1, 0, TAU); ctx.fill(); ctx.strokeStyle = 'rgba(255,140,50,.7)'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = 'rgba(232,220,184,.35)'; ctx.font = 'italic 22px "DejaVu Serif"'; ctx.fillText('...Christ Jes', 300, 958);
      for (let i = 0; i < 40; i++) { const p = (lt * .18 + hash(i)) % 1, x = 360 + (hash(i + 7) - .5) * 400 + Math.sin(p * 8 + i) * 30, y = 980 - p * 900; ctx.fillStyle = `rgba(255,${120 + hash(i) * 100},40,${(1 - p) * .9})`; ctx.beginPath(); ctx.arc(x, y, 1.5 + hash(i + 2) * 2.5, 0, TAU); ctx.fill(); }
      ctx.restore(); ctx.fillStyle = '#1a0e08'; ctx.fillRect(0, 1050, W, 230);
      vignette(ctx, .4);
    }, .4);
  }
  // ===== f1: a letter that arrives =====
  {
    const t0 = st_('f1') - .3, t1 = st_('f2') - .55, tG = t0 + .6;
    const Ly = actor('lydia', { x: 480, y: 780, s: 1.2, look: [230, 820], follow: .6, lid: .15, smile: .1, browIn: .2, armL: [-40, 200], armR: [40, 200] }, [
      { t: tG, d: .7, armL: [-110, 110], armR: [-40, 120], handL: 'hold', handR: 'hold', angL: -.4, angR: .6, look: [380, 900], browOut: .4, smile: .3 },
    ]);
    const Cr = actor('courier', { x: 200, y: 800, s: 1.2, turn: .2, look: [480, 760], follow: .6, smile: .35, armL: [-30, 200], armR: [140, 120], handR: 'hold' }, [{ t: tG + .7, d: .7, armR: [40, 200], handR: 'relax' }]);
    shot(t0, t1, (ctx, t) => {
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#5a4a6a'); g.addColorStop(1, '#e09a6a'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      ctx.drawImage(cached('philippiExt', W, H, c => { bricks(c, 0, 300, W, 900, '#b89a72', 31, 110, 50, '#6a5a44'); }), 0, 0);
      ctx.fillStyle = '#2a1a10'; ctx.fillRect(390, 420, 260, 560); glow(ctx, 520, 700, 260, '#ffb35c', .5);
      const fl = LIGHT.lamp(560, 640, .8);
      show(ctx, Ly, t, fl); show(ctx, Cr, t, LIGHT.dawn(0, 300, .7));
      const k = ramp(t, tG, tG + .7); rolledLetter(ctx, lerp(200 + 140 * 1.2 + 30, 400, k), lerp(800 + 120 * 1.2 - 30, 910, k), 100, -.2);
      vignette(ctx, .5);
    }, .4);
    LABELS.push({ t0: t0 + .1, text: 'Lydia of Philippi', x: 480, y: 440, dur: 2.0 });
  }
  // ===== f2 + f3a: reading aloud =====
  const readRoom = (t0, t1, z, keysL, keysJ, keysC, narrMouth, xin, jTears) => {
    const Ly = actor('lydia', { x: 360, y: 870, s: 1.2, look: [360, 1010], follow: .55, lid: .35, browIn: .3, smile: .05, armL: [-85, 120], armR: [85, 120], handL: 'hold', handR: 'hold', angL: -1.0, angR: 1.0, nod: .5 }, keysL);
    const J = actor('jailer', { x: 120, y: 900, s: 1.25, turn: .2, look: [360, 720], follow: .6, lid: .25, browIn: .3, smile: 0, armL: [-40, 220], armR: [40, 220], nod: .3, tears: jTears || [] }, keysJ);
    const Ch = actor('child', { x: 610, y: 980, s: 1.05, turn: -.2, look: [360, 820], follow: .65, lid: .05, browOut: .4, open: .12, lean: -.06, armL: [-60, 150], armR: [30, 160] }, keysC);
    const cam = { x: 360, y: 930, z: z * 1.12 };
    shot(t0, t1, (ctx, t) => {
      ctx.fillStyle = '#1e140c'; ctx.fillRect(0, 0, W, H);
      ctx.save(); applyCam(ctx, cam);
      ctx.drawImage(cached('philippiInt', W + 400, H + 400, c => { bricks(c, 0, 0, W + 400, H + 400, '#8a6a4a', 41, 120, 54, '#4a3a2a'); stains(c, 0, 0, W + 400, H + 400, '#1a0a00', 3, 14); }), -200, -200);
      ctx.restore();
      const lp = toScreen(cam, 560, 1000), fl = LIGHT.lamp(lp[0], lp[1], 1.1);
      glow(ctx, lp[0], lp[1] - 60, 420, '#ffb35c', .3);
      show(ctx, J, t, fl, cam);
      show(ctx, Ch, t, fl, cam);
      show(ctx, Ly, t, fl, cam, st => {
        if (narrMouth) { const o = speaking('NARRATOR', t) ? Math.max(0, noise1(t * 9)) * .5 : 0; st.open = Math.max(st.open, o); }
        st.mid = (c, arms) => { const a = arms.L.w, b = arms.R.w; scroll(c, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 18, Math.abs(b[0] - a[0]) + 40, 130, 0, 1, .9); };
      });
      ctx.save(); applyCam(ctx, cam); table(ctx, -200, 1050, W + 400, 400, '#5a3a22'); oilLamp(ctx, 560, 1040, 1.1, t); ctx.restore();
      vignette(ctx, .55);
    }, xin);
  };
  {
    const tR = WT('f2', 'remember');
    readRoom(st_('f2') - .55, st_('f3') - .3, 1, [
      { t: WT('f2', 'thank'), d: .5, browIn: .7, smile: .1 },                         // voice catching
      { t: tR - .1, d: .6, look: [150, 720], follow: .55, lid: .15, smile: .45, tearful: .6, browIn: .5 }, // lifts her eyes to them
    ], [
      { t: WT('f2', 'God'), d: .8, browIn: .9, lid: .35, smile: -.15 },
      { t: tR, d: .5, look: [380, 740], smile: .2, lid: .3 },
      { t: en_('f2') + .3, d: .8, lid: .5, headPitch: .06 },
    ], [
      { t: tR, d: .5, look: [360, 760], smile: .4, open: 0 },
    ], false, .5, [{ side: 1, t0: WT('f2', 'every') - .2, dur: 3.6 }]);
  }
  {
    const tc = WT('f3', 'copied') - .15, tp = WT('f3', 'passed') - .15;
    readRoom(st_('f3') - .3, tc, .85, [{ t: 0, look: [360, 1010], lid: .35 }], [{ t: 0, lid: .3, browIn: .5 }], [{ t: 0, open: .1 }], true, 0);
    // copying by hand
    shot(tc, tp, (ctx, t) => {
      ctx.fillStyle = '#3a2618'; ctx.fillRect(0, 0, W, H);
      glow(ctx, 200, 300, 600, '#ffb35c', .3);
      scroll(ctx, 360, 380, 560, 300, -.03, 1, 1);           // the original
      const prog = clamp((t - tc) / (tp - tc));
      scroll(ctx, 360, 800, 560, 300, .02, 1, prog * .95);  // the copy filling in
      const hx = 120 + ((prog * 9) % 1) * 460, hy = 680 + Math.floor(prog * 9) * 27;
      ctx.save(); ctx.translate(hx + 30, hy + 40); ctx.scale(2.1, 2.1); ctx.rotate(-.6);
      // sleeve + hand holding the reed pen
      ctx.fillStyle = '#7a5634'; ctx.fill(P2(p => capsule(p, -180, 60, -10, 10, 30, 22))); ctx.fillStyle = shade('#7a5634', -.5); ctx.beginPath(); ctx.ellipse(-12, 10, 6, 22, -.3, 0, TAU); ctx.fill();
      ctx.fillStyle = CAST.paul.skin; ctx.fill(P2(p => capsule(p, -14, 10, 0, 0, 14, 12)));
      drawHand(ctx, CAST.luke, 'pen', -1, 'back'); drawProp(ctx, 'stylus'); drawHand(ctx, CAST.luke, 'pen', -1, 'front');
      ctx.restore();
      vignette(ctx, .5);
    }, 0);
    // map: house to house
    const cities = [['Rome', 110, 520, 10, -12], ['Corinth', 420, 690, -110, 30], ['Philippi', 470, 470, 12, 28], ['Thessalonica', 430, 410, 12, -14], ['Ephesus', 560, 650, -40, -18], ['Colossae', 650, 720, -90, 32], ['Galatia', 660, 520, -76, -16]];
    shot(tp, st_('f4') - .3, (ctx, t) => {
      ctx.drawImage(cached('map', W, H, c => {
        c.fillStyle = '#e9dcb8'; c.fillRect(0, 0, W, H); grit(c, 0, 0, W, H, '#c9b890', .8, 5, 4000);
        c.fillStyle = '#c9b48a'; c.beginPath(); spline(c, [[0, 300], [140, 340], [200, 470], [160, 560], [60, 620], [0, 600]], true, .5); c.fill(); // Italy-ish
        c.beginPath(); spline(c, [[330, 330], [520, 330], [720, 380], [720, 760], [560, 720], [470, 760], [420, 640], [360, 560], [380, 450]], true, .5); c.fill(); // Greece/Asia
        c.strokeStyle = 'rgba(90,70,40,.5)'; c.lineWidth = 2; c.stroke();
      }), 0, 0);
      const lt = t - tp;
      const routes = [[0, 1], [1, 2], [2, 3], [1, 4], [4, 5], [2, 6], [0, 4]];
      routes.forEach(([a, b], i) => {
        const k = clamp((lt - i * .35) / .8); if (k <= 0) return;
        const A = cities[a], B = cities[b], mid = [(A[1] + B[1]) / 2, Math.min(A[2], B[2]) - 70];
        const pts = sampleCurve([A[1], A[2]], mid, [B[1], B[2]], 30).slice(0, Math.max(2, Math.floor(k * 31)));
        ctx.strokeStyle = 'rgba(155,42,34,.8)'; ctx.lineWidth = 3; ctx.setLineDash([8, 6]); ctx.beginPath(); pts.forEach((p, j) => j ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.stroke(); ctx.setLineDash([]);
        const e = pts[pts.length - 1]; if (k < 1) rolledLetter(ctx, e[0], e[1], 40, 0);
      });
      ctx.font = '600 22px "DejaVu Serif"'; ctx.fillStyle = '#4a3420';
      for (const [n, x, y, ox, oy] of cities) { ctx.beginPath(); ctx.arc(x, y, 7, 0, TAU); ctx.fill(); ctx.fillText(n, x + ox, y + oy); }
      vignette(ctx, .35, '#3a2410');
    }, 0);
  }
  // ===== f4: the man who was ignored -> nearly half the books =====
  {
    const t0 = st_('f4') - .3, tE = WT('f4', 'ended') - .15, t1 = st_('g1') - .5;
    const P = actor('paul', { x: 360, y: 900, s: 1.5, look: [360, 1060], follow: .55, lid: .45, browIn: .7, smile: -.2, armL: [-60, 150], armR: [60, 150], handL: 'flat', handR: 'flat', nod: .3 }, [
      { t: WT('f4', 'ignored'), d: .8, look: [100, 700], lid: .25 },                    // looks to the door: no one
      { t: WT('f4', 'mocked'), d: .5, look: [360, 1000], browIn: 1, lid: .4 },
      { t: WT('f4', 'abandoned'), d: 1.2, lid: .65, headPitch: .12, smile: -.3 },
    ]);
    shot(t0, tE, (ctx, t) => {
      ctx.fillStyle = '#100a06'; ctx.fillRect(0, 0, W, H);
      ctx.save(); applyCam(ctx, { x: 360, y: 640, z: 1.1 }); romeRoom(ctx, t); ctx.restore();
      ctx.fillStyle = 'rgba(5,3,2,.45)'; ctx.fillRect(0, 0, W, H);
      const dim = 1 - ramp(t, WT('f4', 'abandoned'), tE) * .4;
      show(ctx, P, t, LIGHT.lamp(470, 1030, dim));
      table(ctx, 0, 1080, W, 220); oilLamp(ctx, 470, 1070, dim, t);
      vignette(ctx, .7);
    }, .4);
    const books = ['Matt', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Cor', '2 Cor', 'Gal', 'Eph', 'Phil', 'Col', '1 Thess', '2 Thess', '1 Tim', '2 Tim', 'Titus', 'Philem', 'Heb', 'James', '1 Pet', '2 Pet', '1 John', '2 John', '3 John', 'Jude', 'Rev'];
    const pauline = new Set([5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]);
    shot(tE, t1, (ctx, t) => {
      ctx.fillStyle = '#1a120c'; ctx.fillRect(0, 0, W, H);
      const lt = t - tE;
      glow(ctx, 360, 640, 600, '#ffcf8a', .15 + .25 * ramp(lt, 1, 5));
      // two shelves of spines
      [[0, 14, 420], [14, 27, 820]].forEach(([a, b, y]) => {
        ctx.fillStyle = '#3a2416'; ctx.fillRect(40, y + 10, 640, 22);
        for (let i = a; i < b; i++) {
          const x = 52 + (i - a) * 45, h = 250 + (i * 37 % 40);
          const lit = pauline.has(i) ? ramp(lt, .6 + [...pauline].indexOf(i) * .32, .9 + [...pauline].indexOf(i) * .32) : 0;
          const base = ['#5a2a22', '#2a3a4a', '#3a4a2a', '#4a3a5a'][i % 4];
          ctx.fillStyle = mix(base, '#e8c060', lit * .85); ctx.fillRect(x, y + 10 - h, 40, h);
          if (lit > .1) glow(ctx, x + 20, y - h / 2, 70, '#ffd27a', .35 * lit);
          ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(x + 34, y + 10 - h, 6, h);
          ctx.save(); ctx.translate(x + 26, y - 14); ctx.rotate(-Math.PI / 2); ctx.fillStyle = lit > .5 ? '#3a2410' : 'rgba(240,230,210,.8)'; ctx.font = '600 20px Inter'; ctx.fillText(books[i], 0, 0); ctx.restore();
        }
      });
      ctx.fillStyle = '#e4c272'; ctx.font = '600 34px "DejaVu Serif"'; ctx.textAlign = 'center'; ctx.globalAlpha = ramp(lt, 4.5, 5.2); ctx.fillText('13 of 27 books', 360, 1170); ctx.globalAlpha = 1; ctx.textAlign = 'left';
      vignette(ctx, .5);
    }, 0);
  }
}
// ---------- dawn ----------
function buildEnd(chatMsgs) {
  const dawnMsgs = chatMsgs;
  {
    const t0 = st_('g1') - .5, t1 = st_('g3') - .9;
    const tOne = WT('g2', 'one');
    const A = actor('writer', Object.assign({ x: 470, y: 1080, s: 1.5, look: [500, 400], follow: .45, lid: .3, browIn: .5, smile: -.05, turn: -.1 }, PHONE_HOLD), [
      { t: WT('g1', 'didn\'t'), d: .7, lid: .2, browIn: .3, smile: .15 },
      { t: WT('g2', 'block'), d: .6, lid: .4, look: [470, 1100], browIn: .6, smile: -.05 },   // one slow look down
      { t: tOne - .1, d: 1.0, look: [165, 330], follow: .6, lid: .15, browIn: .2, browOut: .3, smile: .1 }, // notices the lit window
      { t: en_('g2') + .2, d: .8, smile: .3, lid: .25 },
    ]);
    shot(t0, t1, (ctx, t) => aptWriter(ctx, t, A, 'dawn', {
      bulb: false,
      under: (c, t) => {
        // across the street: one lit window, someone quietly reading
        const a = ramp(t, tOne - .2, tOne + .8);
        c.fillStyle = mix('#5a5070', '#ffd890', a); c.fillRect(178, 380, 40, 52);
        if (a > 0) { c.fillStyle = `rgba(40,30,30,${a})`; c.beginPath(); c.arc(194, 398, 7, 0, TAU); c.fill(); c.fillRect(186, 405, 16, 27); c.fillStyle = `rgba(140,190,255,${a})`; c.fillRect(200, 410, 8, 10); glow(c, 198, 406, 50, '#ffd890', .4 * a); }
        // embers of the burned letters drift past early on
        const ea = 1 - ramp(t, WT('g1', 'didn\'t'), WT('g1', 'didn\'t') + 1);
        for (let i = 0; i < 14; i++) { const p = ((t - t0) * .2 + hash(i)) % 1; c.fillStyle = `rgba(255,150,60,${ea * (1 - p) * .7})`; c.beginPath(); c.arc(300 + hash(i + 3) * 400, 1000 - p * 700, 2, 0, TAU); c.fill(); }
      },
      over: (c, t) => chatPanel(c, 300, 60, 400, 600, dawnMsgs, t),
    }), .6);
  }
  {
    const t0 = st_('g3') - .9, t1 = st_('g4') + .05;
    const A = actor('writer', { x: 360, y: 1090, s: 2.6, look: [380, 600], follow: .45, lid: .25, browIn: .4, smile: .05, shrug: .6, armL: [-40, 250], armR: [40, 250] }, [
      { t: t0 + .2, d: 1.0, shrug: 0, open: .2, round: .6, lid: .45 },                         // long exhale
      { t: t0 + .9, d: .3, open: 0 },
      { t: st_('g3') - .3, d: .4, look: [380, 1100], lid: .5 },                                  // slow look down
      { t: WT('g3', 'keep') - .1, d: .5, look: [380, 640], lid: .2, smile: .4, browIn: .1 },     // up again, small smile
      { t: en_('g3') + .1, d: .6, smile: .5, squint: .25 },
    ]);
    shot(t0, t1, (ctx, t) => {
      ctx.save(); applyCam(ctx, { x: 250, y: 420, z: 1.8 }); ctx.drawImage(aptBG('dawn'), 0, 0); ctx.restore();
      ctx.filter = 'none'; glow(ctx, 0, 300, 700, '#ffcf9a', .3);
      show(ctx, A, t, LIGHT.dawn(60, 500, 1.1));
      vignette(ctx, .4);
    }, 0);
  }
  {
    const t0 = st_('g4') + .05, t1 = st_('g5') - .2, tn = t0 + .4;
    const msgs = [{ t: tn, me: false, text: 'I read your post. I needed this today.', meta: 'new comment on your post' }];
    const A = actor('writer', Object.assign({ x: 380, y: 1080, s: 1.6, look: [380, 1000], follow: .5, lid: .35, smile: .15, browIn: .2 }, PHONE_HOLD), [
      { t: tn + .1, d: .3, look: [380, 420], lid: .2 },
      { t: tn + .6, d: .4, lid: -.12, browIn: .5, browOut: .8, browY: .4 },         // eyes widen
      { t: tn + 1.4, d: .4, smile: -.05, browOut: .3 },                               // presses lips: moved
      { t: tn + 2.0, d: .7, smile: .6, squint: .35, lid: .2, tearful: .5 },
      { t: tn + 2.8, d: .8, look: [165, 330], follow: .6 },                          // glance to the morning light
    ]);
    shot(t0, t1, (ctx, t) => aptWriter(ctx, t, A, 'dawn', {
      bulb: false,
      over: (c, t) => {
        const sl = easeOut(clamp((t - tn) / .45)); if (sl <= 0) return;
        c.save(); c.translate(0, (1 - sl) * -260); c.globalAlpha = sl;
        c.shadowColor = 'rgba(0,0,0,.4)'; c.shadowBlur = 30; c.fillStyle = 'rgba(250,248,244,.97)'; roundRect(c, 40, 90, 640, 190, 30); c.fill(); c.shadowBlur = 0;
        const og = c.createRadialGradient(100, 150, 2, 100, 150, 26); og.addColorStop(0, '#fff'); og.addColorStop(.5, '#ffcf8a'); og.addColorStop(1, '#e08a4a'); c.fillStyle = og; c.beginPath(); c.arc(100, 150, 26, 0, TAU); c.fill();
        c.fillStyle = '#6a6470'; c.font = '600 22px Inter'; c.fillText('New comment on your post · now', 142, 138);
        c.fillStyle = '#1e1a22'; c.font = '600 30px Inter'; c.fillText('I read your post.', 142, 184); c.fillText('I needed this today.', 142, 224);
        c.restore();
      },
    }), 0);
  }
  {
    const t0 = st_('g5') - .2, t1 = TL.total + .5, tw = WT('g5', 'Write');
    const A = actor('writer', Object.assign({ x: 420, y: 960, s: 1.3, look: [160, 330], follow: .6, lid: .25, smile: .35, turn: -.2 }, PHONE_HOLD), [
      { t: WT('g5', 'opened'), d: .8, look: [470, 1050], lid: .35, smile: .25 },     // back to the phone, typing
      { t: tw + .2, d: .6, smile: .45 },
    ]);
    shot(t0, t1, (ctx, t) => {
      aptWriter(ctx, t, A, 'dawn', { bulb: false });
      const a = ramp(t, tw - .1, tw + .7);
      ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#fff4dc'; ctx.font = '600 64px "DejaVu Serif"'; ctx.textAlign = 'center';
      ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 18; ctx.fillText('Write it anyway.', 360, 640 - a * 10); ctx.restore();
    }, .4);
  }
}
