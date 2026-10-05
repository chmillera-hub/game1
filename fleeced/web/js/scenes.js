/* FLEECED - scene choreography. Every beat is keyed to timeline cues/lines. */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp, inv, E, hash, noise, cue: c, S: s, End: e, P, win, talk, camPath, applyCam, hitShake, shake, text, FONT_TITLE, mix } = F;
  const A = window.A;
  const PAL = A.PAL;
  const FARM = A.FARM;
  const G = A.GROUND;

  const blink = (t, seed) => ((t * 0.9 + hash(seed) * 7) % (3.4 + hash(seed + 2) * 2)) < 0.13;
  const within = (t, a, b) => t >= a && t < b;
  const pop = (t, at, d = 0.35) => E.back(clamp((t - at) / d));
  const steps = (t, times, d = 0.4) => times.reduce((acc, x) => acc + E.inOut(clamp((t - x) / d)), 0);
  /** bleat mouth envelope for decorative bleats (no voice line) */
  const baa = (t, at, d = 0.7) => (t >= at && t < at + d ? Math.sin(((t - at) / d) * Math.PI) * (0.7 + 0.3 * Math.sin(t * 70)) : 0);
  const farmerY = G + 105; // standing in the yard
  const porchY = G - 12;   // standing / sitting on the porch

  function world(ctx, cam, fn) {
    ctx.save();
    applyCam(ctx, cam, 1);
    fn();
    ctx.restore();
  }
  function withShake(cam, sh) {
    return { x: cam.x + sh.x, y: cam.y + sh.y, z: cam.z, r: cam.r || 0 };
  }
  function blackout(ctx, k) {
    if (k <= 0) return;
    ctx.fillStyle = `rgba(0,0,0,${clamp(k)})`;
    ctx.fillRect(-10, -10, W + 20, H + 20);
  }
  function seatedFarmer(ctx, t, o) {
    const rock = Math.sin(t * 1.6) * 0.035 * (o.rock ?? 1);
    ctx.save();
    ctx.translate(FARM.chairX, porchY);
    ctx.rotate(rock);
    A.rocker(ctx, 0, 0, 1, false);
    A.farmer(ctx, Object.assign({ x: 0, y: -6, t, sit: 1, noShadow: true }, o));
    A.rocker(ctx, 0, 0, 1, true);
    ctx.restore();
  }

  const HERD = [
    { x: 560, y: 930, dir: 1, seed: 1 },
    { x: 1165, y: 922, dir: -1, seed: 2 },
    { x: 690, y: 980, dir: 1, seed: 3 },
    { x: 1035, y: 985, dir: -1, seed: 4 },
    { x: 425, y: 968, dir: 1, seed: 5 },
    { x: 1300, y: 968, dir: -1, seed: 6 },
  ];
  const SPEAKER_OF = { 2: 'sheepA', 3: 'sheepB', 1: 'sheepC' };

  const SC = {};

  // ================================================================ TITLE
  SC.title = (ctx, t, sc) => {
    const pal = PAL.day;
    A.setTint(pal);
    const panK = P(t, c('titlePan'), sc.end - c('titlePan') + 0.2, E.inOut);
    const cam = { x: 960, y: lerp(-320, 540, panK), z: 1 };
    A.farmSet(ctx, t, cam, pal, { sunX: 1500, sunY: 190 });
    world(ctx, cam, () => {
      const k = P(t, c('titleDrop'), c('titleLand') - c('titleDrop'), E.in);
      const land = t - c('titleLand');
      const sq = land > 0 ? Math.exp(-land * 7) * Math.sin(land * 28) * 0.22 : 0;
      ctx.save();
      ctx.translate(960, lerp(-1100, -360, k));
      ctx.scale(1 + sq, 1 - sq);
      text(ctx, 'FLEECED', 0, 0, { size: 270, font: FONT_TITLE, weight: 400, fill: '#fff6e0', stroke: '#2b1d16', lw: 26, shadow: 'rgba(43,29,22,0.35)', sx: 0, sy: 16, ls: 8 });
      ctx.restore();
      const sa = P(t, c('titleSub'), 0.7);
      text(ctx, F.TL.subtitle, 960, -190, { size: 56, weight: 600, fill: '#2b1d16', alpha: sa });
      for (let i = 0; i < 3; i++) A.token(ctx, 960 + (i - 1) * 380, -540 + Math.sin(t * 2 + i) * 14, 40, t * 3 + i, { alpha: sa });
    });
  };

  // ================================================================ FARM
  SC.farm = (ctx, t, sc) => {
    const pal = PAL.day;
    A.setTint(pal);
    const cam = camPath(t, [[sc.start, { x: 960, y: 540, z: 1 }], [sc.end, { x: 900, y: 610, z: 1.14 }, E.sine]]);
    A.farmSet(ctx, t, cam, pal, {});
    world(ctx, cam, () => {
      HERD.forEach((h, i) => {
        const at = c('sheepPop' + (i + 1));
        if (t < at) return;
        const k = pop(t, at);
        A.sheep(ctx, Object.assign({}, h, { s: 0.82 * k, t, blink: blink(t, h.seed), mood: 'neutral', talk: baa(t, c('sheepBaa') + i * 0.14, 0.75), look: { x: h.dir, y: -0.2 } }));
      });
      const fp = c('farmerPop');
      if (t >= fp) {
        const k = pop(t, fp, 0.4);
        const waving = within(t, fp + 0.25, s('n_sheep') + 0.5);
        const pose = waving ? A.mixPose(A.POSE.idle, A.POSE.wave, P(t, fp + 0.25, 0.25)) : A.mixPose(A.POSE.wave, A.POSE.idle, P(t, s('n_sheep') + 0.5, 0.3));
        if (waving) pose.r = [pose.r[0] + Math.sin(t * 12) * 26, pose.r[1]];
        A.farmer(ctx, { x: 860, y: farmerY, s: k, t, pose, mood: 'smile', blink: blink(t, 99) });
      }
    });
  };

  // ================================================================ TOKENS
  SC.tokens = (ctx, t, sc) => {
    const pal = PAL.day;
    A.setTint(pal);
    const cam = camPath(t, [
      [sc.start, { x: 860, y: 700, z: 1.38 }],
      [s('s_okay') - 0.4, { x: 880, y: 720, z: 1.42 }],
      [s('s_okay') + 0.2, { x: 900, y: 760, z: 1.6 }],
      [sc.end, { x: 930, y: 770, z: 1.65 }],
    ]);
    A.farmSet(ctx, t, cam, pal, {});
    const tUp = c('tokenUp'), tRain = c('tokensRain');
    const hand = [860 + 96, farmerY - 436 - 30];
    world(ctx, cam, () => {
      HERD.forEach((h, i) => {
        const spk = SPEAKER_OF[i];
        const land = tRain + i * 0.11 + 0.55;
        const got = t >= land;
        let mood = got ? 'happy' : 'neutral';
        if (spk && talk(spk, t) > 0.02) mood = 'happy';
        const lookUp = within(t, tUp - 0.2, land);
        const nod = spk === 'sheepA' ? Math.sin(clamp((t - s('s_okay')) / 0.8) * Math.PI * 2) * 0.12 : 0;
        A.sheep(ctx, Object.assign({}, h, {
          s: 0.82, t, blink: blink(t, h.seed), mood, talk: spk ? talk(spk, t) : 0,
          look: lookUp ? { x: (860 - h.x) / 400, y: -1 } : { x: h.dir, y: 0 }, headTilt: nod,
          badge: got ? 3 : null, badgeS: pop(t, land, 0.3),
        }));
        if (within(t, tUp, land)) A.mark(ctx, '?', h.x + 10 * h.dir, h.y - 250, 0.8, P(t, tUp, 0.2) * (1 - P(t, land - 0.2, 0.2)));
      });
      // hearts
      for (const [id, i] of [['heartB', 3], ['heartC', 1]]) {
        const at = c(id), h = HERD[i];
        if (within(t, at, at + 1.6)) {
          const k = (t - at) / 1.6;
          A.heart(ctx, h.x + 60 * h.dir, h.y - 270 - k * 80, 1.4 * pop(t, at, 0.25), 1 - k * k);
        }
      }
      const holding = within(t, tUp - 0.35, s('f_food') + 0.3);
      const pose = holding ? A.mixPose(A.POSE.idle, A.POSE.hold, P(t, tUp - 0.35, 0.3)) : t < tUp ? A.POSE.idle : A.mixPose(A.POSE.hold, A.POSE.idle, P(t, s('f_food') + 0.3, 0.3));
      A.farmer(ctx, { x: 860, y: farmerY, t, pose, talk: talk('farmer', t), mood: 'smile', blink: blink(t, 99), prop: holding && t > tUp - 0.2 ? { r: 'token' } : null, tokenSpin: t * 4 });
      if (within(t, tUp, tUp + 0.8)) A.sparkle(ctx, hand[0] + 30, hand[1] - 30, 1.4, 1 - P(t, tUp, 0.8, E.lin), t * 3);
      // flying tokens
      HERD.forEach((h, i) => {
        const t0 = tRain + i * 0.11, k = (t - t0) / 0.55;
        if (k < 0 || k > 1) return;
        const tx = h.x + 8 * h.dir, ty = h.y - 215 * 0.82;
        const x = lerp(hand[0], tx, k), y = lerp(hand[1], ty, k) - Math.sin(k * Math.PI) * 160;
        A.token(ctx, x, y, 20, t * 12 + i);
      });
      // food / shelter bubbles
      const bOut = P(t, s('f_month') - 0.1, 0.3);
      A.bubble(ctx, 600, 470, 300, 170, {
        k: pop(t, c('iconFood'), 0.35) * (1 - bOut), thought: true,
        draw: (g) => { A.token(g, -78, -4, 30, 0); A.mark(g, '→', -8, -2, 0.7); A.hayBale(g, 74, 30, 0.75); },
      });
      A.bubble(ctx, 1110, 470, 300, 170, {
        k: pop(t, c('iconShelter'), 0.35) * (1 - bOut), thought: true,
        draw: (g) => { A.token(g, -78, -4, 30, 0); A.mark(g, '→', -8, -2, 0.7); A.miniBarn(g, 76, 34, 0.9); },
      });
      const calK = pop(t, c('calendar'), 0.35) * (1 - P(t, s('s_okay') + 0.2, 0.3));
      if (calK > 0) A.calendar(ctx, 1110, 470, 0.95 * calK, 1 + P(t, c('calendar') + 0.15, e('f_month') - c('calendar') + 0.3, E.lin) * 3);
    });
  };

  // ================================================================ SMILE (night lock-out)
  SC.smile = (ctx, t, sc) => {
    const tLock = s('n_locks') - 0.12, tOut = c('rainStart') - 0.1;
    if (t < tLock) {
      // close-up of the grin, day sliding to dusk
      const k = P(t, sc.start, tLock - sc.start, E.lin);
      const pal = F.mixPal(PAL.day, PAL.dusk, k);
      A.setTint(pal);
      const cam = { x: 860, y: farmerY - 330, z: lerp(2.7, 3.15, E.sine(k)) };
      A.farmSet(ctx, t, cam, pal, { sunY: 190 + k * 260 });
      world(ctx, cam, () => {
        const grin = P(t, s('n_smiles') + 0.35, 0.5) > 0.5;
        A.farmer(ctx, { x: 860, y: farmerY, t, mood: grin ? 'grin' : 'smile', blink: !grin && blink(t, 99) });
        const g = c('grin');
        if (within(t, g, g + 0.9)) A.sparkle(ctx, 878, farmerY - 300, 0.9, 1 - P(t, g, 0.9, E.lin), t * 4);
      });
      return;
    }
    if (t < tOut) {
      // dusk: tokened sheep file into the barn, farmer slams + locks the door
      const k = P(t, tLock, tOut - tLock, E.lin);
      const pal = F.mixPal(PAL.dusk, PAL.night, k * 0.8);
      A.setTint(pal);
      const slam = c('doorSlam');
      const sh = hitShake(t, [slam], 14, 0.25);
      const cam = withShake({ x: 520, y: 650, z: 1.55 }, sh);
      const door = t < slam - 0.12 ? 1 : 1 - P(t, slam - 0.12, 0.12, E.in);
      A.farmSet(ctx, t, cam, pal, { door, lock: P(t, c('lockClick'), 0.25, E.lin), sun: false, sunY: 600 });
      world(ctx, cam, () => {
        for (let i = 0; i < 3; i++) {
          const t0 = tLock + i * 0.38;
          const x = lerp(820 + i * 120, FARM.barnX, P(t, t0, 1.1, E.lin));
          const a = 1 - P(t, t0 + 0.85, 0.25, E.lin);
          if (a > 0) A.sheep(ctx, { x, y: G + 70, s: 0.7, dir: -1, t, seed: 10 + i, walk: x * 0.05, badge: 3, alpha: a, badgeA: a });
        }
        const pushing = t > slam - 0.45;
        A.farmer(ctx, { x: 800, y: G + 96, s: 0.95, t, pose: pushing ? A.POSE.point : A.POSE.hips, mood: 'grin', dir: -1 });
      });
      return;
    }
    // night + rain: sheep without tokens stuck outside
    const pal = PAL.night;
    const th = c('thunder1');
    const flashK = within(t, th, th + 0.5) ? Math.exp(-(t - th) * 7) : 0;
    A.setTint(pal, -flashK * 0.4);
    const cam = camPath(t, [[tOut, { x: 770, y: 740, z: 1.55 }], [sc.end, { x: 800, y: 755, z: 1.66 }, E.sine]]);
    A.farmSet(ctx, t, cam, pal, { door: 0, lock: 1, sun: false, moon: [380, 150, 0.4], cloudA: 0.5 });
    const keel = c('keel'), gh = c('ghost');
    world(ctx, cam, () => {
      const fall = P(t, keel - 0.3, 0.32, E.in);
      A.sheep(ctx, { x: 600, y: G + 104, s: 0.95, dir: 1, t, seed: 21, mood: t > keel ? 'shock' : 'sad', shiver: 1, droop: 1, badge: 0, look: { x: t > keel ? 1 : 0, y: 0.3 }, blink: blink(t, 21) });
      A.sheep(ctx, { x: 990, y: G + 112, s: 0.95, dir: -1, t, seed: 22, mood: fall > 0.6 ? 'dead' : 'sad', shiver: 1 - fall, droop: 1, fall, badge: fall > 0.6 ? null : 0 });
      if (t > gh) {
        const k = (t - gh) / 2.6;
        A.ghostSheep(ctx, 990 + Math.sin(k * 8) * 20, G - 20 - k * 560, 0.75, t, Math.min(1, k * 4) * (1 - clamp((k - 0.7) / 0.3)) * 0.9);
      }
    });
    A.rain(ctx, t, P(t, c('rainStart'), 1.2, E.lin), 0.3);
    if (flashK > 0) {
      A.bolt(ctx, 1500, -20, 520, 3, flashK);
      A.flash(ctx, flashK * 0.55);
    }
  };

  // ================================================================ HERD (self-herding montage)
  SC.herd = (ctx, t, sc) => {
    const tPen = s('n_pen') - 0.15, tFeed = s('n_feeders') - 0.15, tCorral = s('n_corral') - 0.15, tGave = s('n_gave') - 0.15;
    if (t < tPen) {
      const pal = PAL.morning;
      A.setTint(pal);
      const cam = camPath(t, [[sc.start, { x: 900, y: 590, z: 1.08 }], [tPen, { x: 820, y: 600, z: 1.12 }, E.sine]]);
      A.farmSet(ctx, t, cam, pal, { sunX: 1400, sunY: 230 });
      world(ctx, cam, () => {
        seatedFarmer(ctx, t, { pose: A.POSE.sitCup, prop: { r: 'cup' }, mood: 'smile', blink: blink(t, 99) });
        for (let i = 0; i < 6; i++) {
          const x = 1260 + i * 150 - (t - sc.start) * 190;
          A.sheep(ctx, { x, y: G + 120, s: 0.78, dir: -1, t, seed: 30 + i, walk: t * 9, badge: 3, mood: 'happy' });
        }
        const wantA = pop(t, s('n_want') + 0.5, 0.3), wantB = pop(t, s('n_want') + 0.9, 0.3);
        const x0 = 1260 - (t - sc.start) * 190;
        A.bubble(ctx, x0 + 150 + 30, G - 150, 170, 120, { k: wantA, thought: true, draw: (g) => A.hayBale(g, 0, 26, 0.62) });
        A.bubble(ctx, x0 + 450 + 30, G - 150, 170, 120, { k: wantB, thought: true, draw: (g) => A.miniBarn(g, 0, 34, 0.75) });
      });
      return;
    }
    if (t < tFeed) {
      // dusk: queue through the token turnstile into the barn
      const pal = PAL.dusk;
      A.setTint(pal);
      const gates = [c('gate1'), c('gate2'), c('gate3'), c('gate4')];
      const q = steps(t, gates, 0.45);
      const cam = { x: 600, y: 660, z: 1.6 };
      const rot = q * (TAU / 3);
      const green = gates.some(g => within(t, g, g + 0.35));
      A.farmSet(ctx, t, cam, pal, { door: 1, sun: false, gateRot: rot, gateLight: green ? 'green' : null });
      world(ctx, cam, () => {
        for (let k = 3; k >= 0; k--) {
          const slot = k - q;
          const x = slot >= 0 ? 700 + slot * 125 : 700 + slot * 300;
          const a = clamp(1 + slot * 1.6);
          if (a <= 0) continue;
          A.sheep(ctx, { x, y: G + 70, s: 0.68, dir: -1, t, seed: 40 + k, walk: x * 0.05, badge: 3 - (slot < -0.2 ? 1 : 0), alpha: a, badgeA: a, mood: 'happy' });
        }
        gates.forEach(g => {
          const k = (t - g + 0.25) / 0.3;
          if (k > 0 && k < 1) A.token(ctx, lerp(705, FARM.barnX + 150, k), lerp(G - 70, G - 140, k) - Math.sin(k * Math.PI) * 60, 12, t * 10);
        });
      });
      return;
    }
    if (t < tCorral) {
      // morning: insert token at the feeder, hay drops, munch
      const pal = PAL.morning;
      A.setTint(pal);
      const cam = { x: 930, y: 690, z: 1.75 };
      const hay = 0.15 + 0.85 * E.bounce(P(t, c('hayDrop'), 0.4, E.lin));
      A.farmSet(ctx, t, cam, pal, { hay, feederFlash: win(t, c('feedCoin') + 0.1, c('feedCoin') + 0.6, 0.1), sunX: 1500, sunY: 260 });
      world(ctx, cam, () => {
        const x = lerp(560, 740, P(t, tFeed, 0.5, E.out)) + P(t, c('hayDrop') + 0.1, 0.35) * 70;
        const munching = t > c('munch') - 0.1;
        A.sheep(ctx, {
          x, y: G + 74, s: 0.82, dir: 1, t, seed: 50, walk: x * 0.05, badge: t > c('feedCoin') ? 2 : 3,
          mood: munching ? 'happy' : 'neutral', talk: munching ? 0.35 + 0.35 * Math.sin(t * 18) : 0,
          headDy: munching ? 14 + Math.sin(t * 9) * 6 : 0, headTilt: munching ? 0.25 : 0, look: { x: 1, y: -0.5 },
        });
        const f = c('feedCoin');
        const k = (t - f + 0.3) / 0.35;
        if (k > 0 && k < 1) A.token(ctx, lerp(x + 10, FARM.feederX - 163, k), lerp(G - 105, G - 186, k) - Math.sin(k * Math.PI) * 70, 13, t * 12);
        if (within(t, c('hayDrop'), c('hayDrop') + 0.7)) A.sparkle(ctx, FARM.feederX, G - 140, 1, 1 - P(t, c('hayDrop'), 0.7, E.lin), t * 3);
      });
      return;
    }
    if (t < tGave) {
      // farmer on the porch tosses the shepherd's crook - no longer needed
      const pal = PAL.day;
      A.setTint(pal);
      const cam = { x: 1430, y: 620, z: 1.85 };
      A.farmSet(ctx, t, cam, pal, { chair: false });
      const toss = c('crookToss'), land = c('crookLand');
      world(ctx, cam, () => {
        const raising = t < toss;
        const pose = raising ? A.mixPose(A.POSE.sit, A.POSE.sitToss, P(t, toss - 0.45, 0.4)) : A.mixPose(A.POSE.sitToss, A.POSE.sitCup, P(t, toss + 0.2, 0.4));
        seatedFarmer(ctx, t, { pose, prop: raising ? { r: 'crook' } : t > toss + 0.4 ? { r: 'cup' } : null, crookRot: lerp(-0.2, 0.5, P(t, toss - 0.45, 0.4)), mood: 'smile', blink: blink(t, 99) });
        if (!raising) {
          const k = clamp((t - toss) / (land - toss));
          const x = lerp(FARM.chairX + 80, FARM.chairX + 330, k), y = lerp(G - 400, G + 40, k) - Math.sin(k * Math.PI) * 260;
          ctx.save();
          ctx.translate(x, y);
          A.crook(ctx, 0, 0, 0.5 + k * 5.6 + (t > land ? 0 : 0));
          ctx.restore();
        }
      });
      return;
    }
    {
      // the token "sun"
      const pal = PAL.day;
      A.setTint(pal);
      const ts = c('tokenSign');
      const rise = P(t, ts - 0.7, 0.8, E.back);
      const cam = { x: 960, y: 560, z: 1.0 };
      A.farmSet(ctx, t, cam, pal, { sun: false });
      ctx.save();
      const g = ctx.createRadialGradient(1500, 230, 40, 1500, 230, 360);
      g.addColorStop(0, `rgba(255,214,90,${0.45 * rise})`);
      g.addColorStop(1, 'rgba(255,214,90,0)');
      ctx.fillStyle = g;
      ctx.fillRect(1100, -150, 800, 800);
      A.token(ctx, 1500, lerp(520, 230, rise), 110, t * 1.4);
      for (let i = 0; i < 6; i++) A.sparkle(ctx, 1500 + Math.cos(i + t) * 170, 230 + Math.sin(i * 2 + t) * 130, 0.8, rise * (0.5 + 0.5 * Math.sin(t * 5 + i)), t);
      ctx.restore();
      world(ctx, cam, () => {
        for (let i = 0; i < 5; i++) {
          const x = 300 + i * 170 + (t - tGave) * 40;
          A.sheep(ctx, { x, y: G + 120 + (i % 2) * 30, s: 0.75, dir: 1, t, seed: 60 + i, walk: t * 8, badge: 3, mood: 'happy', look: { x: 1, y: -1 } });
        }
        seatedFarmer(ctx, t, { pose: A.POSE.sitCup, prop: { r: 'cup' }, mood: 'smile', blink: blink(t, 99) });
      });
    }
  };

  // ================================================================ BRAINS (cognitive ability -> humans)
  SC.brains = (ctx, t, sc) => {
    const tCity = s('n_control') - 0.25, morph = c('morph');
    if (t < tCity) {
      const pal = PAL.day;
      A.setTint(pal);
      const cam = camPath(t, [[sc.start, { x: 960, y: 700, z: 1.5 }], [morph, { x: 960, y: 690, z: 1.62 }, E.sine]]);
      A.farmSet(ctx, t, cam, pal, {});
      const bite = c('bite');
      world(ctx, cam, () => {
        if (t < morph) {
          const lift = P(t, bite - 0.45, 0.3);
          const chomp = within(t, bite, bite + 0.5);
          const filled = P(t, c('meterFill'), e('n_once') - c('meterFill') - 0.2, E.inOut);
          A.sheep(ctx, {
            x: 860, y: 905, s: 1.25, dir: 1, t, seed: 70,
            mood: filled > 0.85 ? 'happy' : filled > 0.1 ? 'shock' : chomp ? 'neutral' : 'neutral', cross: chomp,
            headDy: lerp(28, 0, lift), headTilt: lerp(0.35, 0, lift) + (chomp ? Math.sin((t - bite) * 40) * 0.05 : 0),
            talk: chomp ? 0.2 + 0.3 * Math.abs(Math.sin((t - bite) * 22)) : 0, look: { x: 1, y: 0.6 }, blink: blink(t, 70),
          });
          const tx = lerp(1030, 860 + 1.25 * 104, lift), ty = lerp(905, 905 - 1.25 * 104, lift);
          A.token(ctx, tx, ty, 24, lift * 0.5, { alpha: 1 - P(t, bite + 0.6, 0.2) });
          if (within(t, bite, bite + 0.6)) A.sparkle(ctx, tx + 20, ty - 20, 0.8, 1 - P(t, bite, 0.6, E.lin), t * 5);
          if (within(t, bite + 0.4, s('n_once'))) A.mark(ctx, '?', 960, 905 - 330, 1.0, P(t, bite + 0.4, 0.2));
          if (filled > 0.6) for (let i = 0; i < 5; i++) A.sparkle(ctx, 960 + Math.cos(t * 2 + i * 1.3) * 140, 640 + Math.sin(t * 3 + i) * 60, 0.6, filled, t * 2);
        } else {
          A.human(ctx, { x: 900, y: 905, s: 1.35, dir: 1, t, shirt: '#6c7a96', tie: true, token: true, face: 0 });
        }
      });
      // meter (screen space)
      const show = P(t, s('n_cognitive') + 0.1, 0.35, E.back) * (1 - P(t, morph - 0.1, 0.2));
      if (show > 0) {
        const v = 0.03 + 0.97 * P(t, c('meterFill'), e('n_once') - c('meterFill') - 0.2, E.inOut);
        const low = t > c('meterLow') && t < c('meterFill') ? (Math.sin((t - c('meterLow')) * 14) > 0 ? 1 : 0.2) : 0;
        A.meter(ctx, 960, 190, v, { alpha: show, low });
      }
      A.flash(ctx, within(t, morph, morph + 0.7) ? 1 - (t - morph) / 0.7 : 0);
      return;
    }
    // the city: same choreography, but humans
    const tFreeze = c('cityFreeze');
    const pan = P(t, tCity, tFreeze - tCity, E.lin);
    const freezeT = Math.min(t, tFreeze);
    const leader = 9 * 135;
    let cam = { x: lerp(560, 1650, E.sine(pan)), y: 600, z: 1.0 };
    const zoomK = P(t, tFreeze + 0.2, sc.end - tFreeze, E.inOut);
    const humanX = (i) => -500 + i * 135 + (freezeT - tCity) * 290;
    const starIdx = 6;
    cam = F.lerpCam(cam, { x: humanX(starIdx), y: 735, z: 2.4 }, zoomK);
    A.setTint({ tint: '#000000', tk: 0 });
    const gateRot = (x) => {
      let r = 0;
      for (let i = 0; i < 12; i++) r += E.inOut(clamp((humanX(i) - (x + 120) + 20) / 60)) * (TAU / 3);
      return r;
    };
    A.city(ctx, t, cam, { gateRot, gateLight: (x) => (Array.from({ length: 12 }, (_, i) => Math.abs(humanX(i) - (x + 120)) < 45).some(Boolean) ? 'green' : null) });
    world(ctx, cam, () => {
      const shirts = ['#6c7a96', '#8a6c96', '#5f8a7a', '#9a7a5a', '#6c7a96', '#7a8a9a', '#8a5f5f', '#5f6f8a', '#7a6c5a', '#6c8a6c', '#96806c', '#5a6a7a'];
      for (let i = 0; i < 12; i++) {
        const x = humanX(i);
        const face = i === starIdx ? P(t, tFreeze + 0.15, 0.25) : 0;
        A.human(ctx, { x, y: A.CITY.street + 6, s: 1.0, dir: 1, t, walk: freezeT * 8, shirt: shirts[i], tie: i % 3 === 0, bag: i % 4 === 1, token: true, face, skin: ['#e0b08c', '#c58c5c', '#f0c8a0', '#8d5a3c'][i % 4], hair: ['#3a2a20', '#1a1410', '#6a4a2a', '#2a2a2a'][i % 4] });
      }
    });
    blackout(ctx, P(t, sc.end - 0.55, 0.5, E.lin));
  };

  // ================================================================ ANNOYING (getting rid of tokens)
  SC.annoying = (ctx, t, sc) => {
    const tNight = c('deniedRain'), tWash = c('washStart');
    const richK = pop(t, c('richStep'), 0.45);
    const annoyIn = c('annoyIn');
    const jar = c('jarBump'), spill = c('jarSpill');
    const press = c('buttonPress'), drain = c('tokenDrain');
    if (t < tNight) {
      const pal = PAL.day;
      A.setTint(pal);
      const cam = camPath(t, [
        [sc.start, { x: 1400, y: 610, z: 1.6 }],
        [annoyIn - 0.8, { x: 1360, y: 620, z: 1.55 }],
        [annoyIn - 0.1, { x: 1270, y: 640, z: 1.35 }],
        [s('n_risk') - 0.2, { x: 1290, y: 630, z: 1.35 }],
        [s('n_risk') + 0.3, { x: 1380, y: 560, z: 1.5 }],
        [s('n_findaway') - 0.2, { x: 1380, y: 580, z: 1.5 }],
        [s('n_findaway') + 0.3, { x: 1290, y: 640, z: 1.45 }],
      ]);
      A.farmSet(ctx, t, cam, pal, { jarTip: P(t, jar + 0.05, 0.3, E.in), jarFill: 1 - P(t, spill, 0.8, E.lin) * 0.8, porchShake: within(t, jar, jar + 0.45) ? 1 - (t - jar) / 0.45 : 0 });
      world(ctx, cam, () => {
        // farmer
        const remoteK = P(t, c('remoteOut') - 0.25, 0.3);
        let pose = A.POSE.hips;
        if (t > s('n_risk') - 0.1) pose = A.mixPose(A.POSE.hips, A.POSE.neck, P(t, s('n_risk') - 0.1, 0.3));
        if (remoteK > 0) pose = A.mixPose(A.POSE.neck, A.POSE.remote, remoteK);
        let mood = 'smile';
        if (t > annoyIn + 0.3) mood = 'frown';
        if (t > jar) mood = 'shock';
        if (t > s('n_risk')) mood = 'worried';
        if (t > c('remoteOut')) mood = 'grin';
        const pr = within(t, press - 0.08, press + 0.25) ? 1 : 0;
        A.farmer(ctx, { x: 1420, y: porchY, s: 0.95, t, pose, mood, prop: remoteK > 0.5 ? { r: 'remote' } : null, press: pr, blink: blink(t, 99), look: { x: -1, y: 0.2 } });
        if (within(t, c('remoteOut'), c('remoteOut') + 0.8)) A.sparkle(ctx, 1420 + 112, porchY - 260, 1.1, 1 - P(t, c('remoteOut'), 0.8, E.lin), t * 4);
        // rich sheep (drawn after the farmer so their balances stay readable)
        if (richK > 0) {
          A.sheep(ctx, { x: 1290, y: porchY, s: 0.74 * richK, dir: 1, t, seed: 80, wool: '#fbf0d6', badge: richK > 0.6 ? 488 : null, mood: t > annoyIn + 0.3 && t < tNight ? 'angry' : 'smug', fluff: 1.08, blink: blink(t, 80) });
          A.sheep(ctx, { x: 1665, y: G + 40, s: 0.78 * richK, dir: -1, t, seed: 81, wool: '#fbf0d6', badge: richK > 0.6 ? 531 : null, mood: t > annoyIn + 0.3 ? 'angry' : 'smug', fluff: 1.08, blink: blink(t, 81) });
        }
        // scruffy sheep
        if (t > annoyIn - 0.6) {
          let x = lerp(500, 1080, P(t, annoyIn - 0.6, 0.6, E.out));
          x += P(t, jar - 0.45, 0.45, E.in) * 120 - P(t, jar + 0.1, 0.5, E.out) * 160;
          const hop = Math.abs(Math.sin(t * 9)) * 26 * (within(t, annoyIn + 0.2, jar - 0.5) ? 1 : 0);
          const yelling = baa(t, annoyIn, 0.95) + baa(t, c('annoyBaa2'), 0.95);
          const n = t < drain ? 7 : Math.max(0, 7 - Math.floor(((t - drain) / 0.8) * 8));
          let m = 'angry';
          if (t > press) m = 'shock';
          if (t > drain + 0.9) m = 'sad';
          A.sheep(ctx, { x, y: G + 98 - hop, s: 0.85, dir: 1, t, seed: 90, wool: '#d8d2c6', punk: true, mood: yelling > 0.05 ? 'yell' : m, talk: yelling, walk: within(t, annoyIn - 0.6, annoyIn) || within(t, jar - 0.45, jar + 0.6) ? t * 14 : null, badge: n, badgeS: t > drain ? 1.25 : 1, droop: t > drain + 0.9 ? 1 : 0 });
          for (const at of [annoyIn, c('annoyBaa2')]) {
            const k = within(t, at, at + 1.0) ? pop(t, at, 0.2) * (1 - P(t, at + 0.8, 0.2)) : 0;
            A.bubble(ctx, x + 40, G - 250 - hop, 250, 150, { k, burst: true, text: 'BAAA!', size: 52, fill: '#fff27a' });
          }
        }
        if (within(t, jar, jar + 0.5)) A.sparkle(ctx, 1262, G - 90, 1.6, 1 - P(t, jar, 0.5, E.lin), 0.3);
        // spilled coins
        if (t > spill) {
          for (let i = 0; i < 18; i++) {
            const tt = t - spill - i * 0.04;
            if (tt < 0) continue;
            const vx = 120 + hash(i * 3.3) * 420, vy = -300 - hash(i * 7.7) * 380;
            const x0 = FARM.jarX + 40, y0 = porchY - 150;
            let x = x0 + vx * Math.min(tt, 1.1), y = y0 + vy * tt + 900 * tt * tt;
            const floor = G + 20 + hash(i * 5.5) * 80;
            if (y > floor) y = floor;
            A.token(ctx, x, y, 12, tt * 12 * (y < floor ? 1 : 0) + i);
          }
        }
        // AT RISK thought
        const riskK = pop(t, s('n_risk') + 0.2, 0.35) * (1 - P(t, c('remoteOut') - 0.5, 0.3));
        A.bubble(ctx, 1170, 360, 300, 190, { k: riskK, thought: true, draw: (g) => { A.miniHouse(g, -60, 40, 0.95); A.plate(g, 70, 20, 0.9); } });
        if (riskK > 0) A.stamp(ctx, 'AT RISK', 1170, 360, P(t, c('riskStamp') - 0.05, 0.35, E.lin) * riskK, -0.18);
      });
      return;
    }
    if (t < tWash) {
      // night, rain: denied at the turnstile
      const pal = PAL.night;
      A.setTint(pal);
      const den = c('denied');
      const cam = { x: 560, y: 690, z: 1.6 };
      A.farmSet(ctx, t, cam, pal, { door: 0, lock: 1, sun: false, moon: [300, 140, 0.3], gateLight: t > den ? 'red' : null, cloudA: 0.4 });
      world(ctx, cam, () => {
        const x = lerp(900, 735, P(t, tNight, 0.8, E.out));
        const jolt = within(t, den, den + 0.4) ? Math.sin((t - den) * 60) * 6 : 0;
        A.sheep(ctx, { x: x + jolt, y: G + 70, s: 0.85, dir: -1, t, seed: 90, wool: '#cfc9bd', punk: true, mood: 'sad', droop: 1, shiver: t > den + 0.5 ? 1 : 0, badge: 0, walk: t < tNight + 0.8 ? x * 0.05 : null });
        const dk = pop(t, den, 0.25);
        if (dk > 0) A.stamp(ctx, 'DENIED', FARM.barnX + 150, G - 330, P(t, den, 0.3, E.lin), 0.1);
      });
      A.rain(ctx, t, 1, 0.25);
      return;
    }
    // washing hands (day, porch)
    const pal = PAL.day;
    A.setTint(pal);
    const cam = camPath(t, [[tWash, { x: 1460, y: 600, z: 1.75 }], [sc.end, { x: 1440, y: 590, z: 1.85 }, E.sine]]);
    A.farmSet(ctx, t, cam, pal, { jarFill: 0.2, jarTip: 0 });
    world(ctx, cam, () => {
      A.sheep(ctx, { x: 1240, y: porchY + 10, s: 0.74, dir: 1, t, seed: 80, wool: '#fbf0d6', badge: 488, mood: 'smug', fluff: 1.08, headTilt: Math.sin(t * 5) * 0.05 * (t > s('n_alldid') ? 1 : 0), blink: blink(t, 80) });
      const washing = t < s('n_alldid') - 0.1;
      let pose;
      if (washing) {
        pose = A.mixPose(A.POSE.idle, A.POSE.wash, P(t, tWash, 0.3));
        const wob = Math.sin(t * 16) * 10;
        pose = { r: [pose.r[0] + wob, pose.r[1]], l: [pose.l[0] - wob, pose.l[1]], rb: pose.rb, lb: pose.lb };
      } else pose = A.mixPose(A.POSE.wash, A.POSE.hips, P(t, s('n_alldid') - 0.1, 0.4));
      const whistling = t > c('whistle') - 0.2;
      A.farmer(ctx, { x: 1430, y: porchY - 10, s: 0.95, t, pose, mood: whistling ? 'smile' : 'smile', look: whistling ? { x: 1, y: -1 } : { x: 0, y: 0.6 }, blink: blink(t, 99), headTilt: whistling ? 0.08 : 0 });
      A.basin(ctx, 1430, porchY + 18, t, P(t, c('wash'), 0.5, E.lin) * (t < c('wash') + 0.5 ? 1 : 0));
      if (washing) for (let i = 0; i < 3; i++) A.sparkle(ctx, 1430 + (i - 1) * 46, porchY - 120 - i * 14, 0.6, 0.5 + 0.5 * Math.sin(t * 8 + i), t);
      if (whistling) {
        for (let i = 0; i < 3; i++) {
          const k = ((t - c('whistle')) * 0.7 + i / 3) % 1;
          text(ctx, '♪', 1460 + k * 90, porchY - 330 - k * 110, { size: 44, fill: '#fff', stroke: '#2b1d16', lw: 6, alpha: Math.sin(k * Math.PI) });
        }
      }
    });
  };

  // ================================================================ JESUS SHEEP
  SC.jesus = (ctx, t, sc) => {
    const tFarmer = s('f_goaway') - 0.3;
    if (t < tFarmer) {
      const pal = PAL.golden;
      A.setTint(pal);
      const glow = P(t, c('jesusGlow'), 1.2, E.inOut);
      const cam = camPath(t, [[sc.start, { x: 760, y: 640, z: 1.25 }], [tFarmer, { x: 760, y: 660, z: 1.5 }, E.sine]]);
      A.farmSet(ctx, t, cam, pal, { sunX: 600, sunY: 300 });
      // light beam
      ctx.save();
      ctx.globalAlpha = 0.35 * glow;
      const g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, 'rgba(255,240,190,0.9)');
      g.addColorStop(1, 'rgba(255,240,190,0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(760 - 120, -20); ctx.lineTo(760 + 120, -20); ctx.lineTo(760 + 340, H); ctx.lineTo(760 - 340, H);
      ctx.fill();
      ctx.restore();
      world(ctx, cam, () => {
        A.hayPile(ctx, 770, G + 150, 1.1);
        const poor = [[500, G + 80, 1], [1030, G + 78, -1], [580, G + 160, 1], [960, G + 165, -1]];
        const eatK = P(t, s('n_imagining') + 1.2, 0.6);
        poor.slice(0, 2).forEach(([x, y, d], i) => {
          const eat = 0.5 + 0.5 * Math.sin(t * 9 + i * 2);
          A.sheep(ctx, { x: lerp(x - d * 120, x, P(t, c('jesusGlow') + 0.3, 1.2)), y, s: 0.7, dir: d, t, seed: 100 + i, thin: true, wool: '#e2dccf', mood: eatK > 0.5 ? 'happy' : 'sad', badge: 0, badgeS: 0.8, talk: eatK * eat * 0.35, headDy: eatK * 12, headTilt: eatK * 0.25 });
        });
        A.sheep(ctx, { x: 770, y: G + 95, s: 1.0, dir: 1, t, seed: 7, wool: '#ffffff', mood: 'kind', halo: glow, alpha: glow, look: { x: 0, y: 0.5 } });
        poor.slice(2).forEach(([x, y, d], i) => {
          const eat = 0.5 + 0.5 * Math.sin(t * 9 + i * 3);
          A.sheep(ctx, { x: lerp(x - d * 160, x, P(t, c('jesusGlow') + 0.6, 1.2)), y, s: 0.74, dir: d, t, seed: 102 + i, thin: true, wool: '#e2dccf', mood: eatK > 0.5 ? 'happy' : 'sad', badge: 0, badgeS: 0.8, talk: eatK * eat * 0.35, headDy: eatK * 12, headTilt: eatK * 0.25 });
        });
        if (glow > 0.3) for (let i = 0; i < 6; i++) A.sparkle(ctx, 770 + Math.cos(t + i) * 220, G - 120 + Math.sin(t * 1.3 + i * 2) * 90, 0.5, glow * (0.5 + 0.5 * Math.sin(t * 4 + i)), t);
        A.label(ctx, 'JESUS SHEEP', 770, 430, 790, G - 150, P(t, s('n_imagining') + 0.5, 0.45, E.lin));
        if (glow > 0.6) A.heart(ctx, 600, G - 140 - ((t * 0.5) % 1) * 60, 1.0, 1 - ((t * 0.5) % 1));
      });
      return;
    }
    const pal = PAL.golden;
    A.setTint(pal);
    const cam = camPath(t, [[tFarmer, { x: 1405, y: 590, z: 1.9 }], [sc.end, { x: 1405, y: 600, z: 2.05 }, E.sine]]);
    A.farmSet(ctx, t, cam, pal, { chair: false, sunX: 600, sunY: 300 });
    const hat = c('hatOver');
    world(ctx, cam, () => {
      const talking = t < e('f_nothing');
      let pose = talking ? A.mixPose(A.POSE.sit, A.POSE.sitDismiss, P(t, tFarmer + 0.2, 0.3)) : A.POSE.sit;
      if (talking) pose = { r: [pose.r[0] + Math.sin(t * 7) * 14 * (t > s('f_goaway') ? 1 : 0), pose.r[1]], l: pose.l, rb: pose.rb, lb: pose.lb };
      if (within(t, hat - 0.45, hat + 0.4)) pose = A.mixPose(A.POSE.sit, A.POSE.sitHat, Math.sin(clamp((t - hat + 0.45) / 0.85) * Math.PI));
      const asleep = t > c('snore') - 0.2;
      seatedFarmer(ctx, t, { pose, talk: talk('farmer', t), mood: asleep ? 'sleep' : 'tired', hatOver: P(t, hat - 0.1, 0.35), rock: asleep ? 0.6 : 1 });
      if (asleep) A.zzz(ctx, FARM.chairX + 60, porchY - 330, t, P(t, c('snore') - 0.2, 0.4));
    });
  };

  // ================================================================ PHARISEES
  // Pharisee sheep: no jewelry, the wealth is all in the account (hundreds of tokens vs. the poor sheep's 0)
  const PHAR = { wool: '#fbefd0', fluff: 1.16 };
  const PHAR_BAL = [503, 547, 612];
  SC.pharisees = (ctx, t, sc) => {
    const tField = s('n_lessmoney') - 0.2, tClose = s('p_gone') - 0.15;
    const pin = c('pharIn'), wake = c('wake');
    if (t < tField) {
      const pal = PAL.day;
      A.setTint(pal);
      const cam = camPath(t, [[sc.start, { x: 1120, y: 640, z: 1.28 }], [s('p_dosomething') - 0.2, { x: 1160, y: 650, z: 1.3 }], [s('p_dosomething') + 0.3, { x: 1260, y: 690, z: 1.5 }]]);
      A.farmSet(ctx, t, cam, pal, { chair: false });
      world(ctx, cam, () => {
        const awake = t > wake;
        seatedFarmer(ctx, t, { pose: A.POSE.sit, mood: awake ? (t > s('p_dosomething') + 0.3 ? 'worried' : 'shock') : 'sleep', hatOver: awake ? 1 - P(t, wake, 0.15) : 1, hatPop: awake ? Math.sin(clamp((t - wake) / 0.4) * Math.PI) : 0, rock: awake ? 0.2 : 0.6, look: { x: -1, y: 0.3 } });
        if (!awake) A.zzz(ctx, FARM.chairX + 60, porchY - 330, t, 1);
        if (within(t, wake, wake + 0.8)) A.mark(ctx, '!', FARM.chairX + 10, porchY - 470, 1.2, 1 - P(t, wake + 0.5, 0.3));
        const xs = [880, 1035, 1190];
        xs.forEach((tx, i) => {
          const k = P(t, pin - 0.3, 2.6, E.out);
          const x = lerp(tx - 760, tx, k);
          const lead = i === 2;
          const tk = lead ? talk('phar1', t) : 0;
          const tap = within(t, s('n_demanding') + 0.5, wake) ? Math.max(0, Math.sin(t * 9 + i)) * 0.7 : 0;
          A.sheep(ctx, Object.assign({ x, y: G + 105 - i * 6, s: 0.84, dir: 1, t, seed: 110 + i, walk: k < 0.98 ? x * 0.04 : null, mood: tk > 0.02 ? 'angry' : 'smug', talk: tk, headTilt: -0.12, stomp: tap, blink: blink(t, 110 + i), badge: PHAR_BAL[i] }, PHAR));
        });
        A.label(ctx, 'PHARISEE SHEEP', 1060, 470, 1060, G - 110, P(t, s('n_wealthier') + 1.4, 0.45, E.lin) * (1 - P(t, s('p_dosomething') - 0.3, 0.3)));
      });
      return;
    }
    if (t < tClose) {
      const pal = PAL.day;
      const red = P(t, s('n_pissoff') + 0.4, 1.2);
      A.setTint(pal);
      const cam = camPath(t, [[tField, { x: 860, y: 660, z: 1.3 }], [tClose, { x: 880, y: 680, z: 1.45 }, E.sine]]);
      A.farmSet(ctx, t, cam, pal, {});
      world(ctx, cam, () => {
        // Jesus sheep in the background, glowing
        A.sheep(ctx, { x: 330, y: G + 40, s: 0.6, dir: 1, t, seed: 7, wool: '#ffffff', mood: 'kind', halo: 1 });
        const ph = [[810, G + 105, 1], [960, G + 100, -1]];
        ph.forEach(([x, y, d], i) => {
          A.sheep(ctx, Object.assign({ x, y, s: 0.86, dir: d, t, seed: 120 + i, mood: red > 0.2 ? 'angry' : 'smug', red: red * 0.75, headTilt: -0.12, blink: blink(t, 120 + i), badge: PHAR_BAL[2 - i] }, PHAR));
          if (t > c('steam') - 0.1) A.steam(ctx, x + d * 60, y - 190, t, P(t, c('steam') - 0.1, 0.3));
        });
        const poor = [[560, G + 112, 1], [660, G + 145, 1], [1170, G + 115, -1], [1270, G + 150, -1]];
        poor.forEach(([x, y, d], i) => {
          const speaker = i === 1;
          const tk = speaker ? talk('poor', t) : 0;
          A.sheep(ctx, { x: x + Math.sin(t * 2 + i) * 6, y, s: 0.7, dir: d, t, seed: 130 + i, thin: true, wool: '#e2dccf', mood: 'sad', cup: true, cupLift: speaker && tk > 0 ? 1 : 0.3 + 0.3 * Math.sin(t * 3 + i), talk: tk, badge: 0, look: { x: d, y: -0.4 } });
        });
        const ask = s('n_lessmoney') + 0.9;
        A.bubble(ctx, 540, G - 140, 220, 110, { k: pop(t, ask, 0.3) * (1 - P(t, s('s_spare') - 0.2, 0.2)), text: 'token?', size: 40, tail: 30, tailDx: 20 });
        A.bubble(ctx, 1290, G - 140, 220, 110, { k: pop(t, ask + 0.6, 0.3) * (1 - P(t, s('s_spare') - 0.2, 0.2)), text: 'please?', size: 40, tail: -30, tailDx: -20 });
      });
      return;
    }
    // close-up: "We want that damn Jesus sheep gone!"
    const pal = PAL.day;
    A.setTint(pal);
    const tk = talk('phar1', t);
    const cam = withShake({ x: 870, y: 790, z: 2.5 }, shake(t, tk * 8));
    A.farmSet(ctx, t, cam, pal, {});
    world(ctx, cam, () => {
      A.sheep(ctx, Object.assign({ x: 810, y: G + 105, s: 0.86, dir: 1, t, seed: 120, mood: 'angry', red: 0.8, talk: tk, headTilt: -0.05, badge: PHAR_BAL[2] }, PHAR));
      A.steam(ctx, 870, G - 85, t, 1);
    });
  };

  // ================================================================ SIGH
  SC.sigh = (ctx, t, sc) => {
    const pal = PAL.day;
    A.setTint(pal);
    const cam = camPath(t, [[sc.start, { x: 1420, y: 520, z: 2.3 }], [sc.end, { x: 1420, y: 510, z: 2.55 }, E.sine]]);
    A.farmSet(ctx, t, cam, pal, {});
    const sg = c('sighSfx');
    world(ctx, cam, () => {
      const slump = Math.sin(clamp((t - sg) / 1.6) * Math.PI) * 1 + P(t, sg + 1.2, 0.5) * 0.3;
      const pose = t > s('f_notgood') - 0.3 ? A.mixPose(A.POSE.idle, A.POSE.neck, P(t, s('f_notgood') - 0.3, 0.4)) : A.POSE.idle;
      A.farmer(ctx, { x: 1420, y: porchY, s: 0.95, t, pose, slump, mood: t > sg + 0.2 ? 'worried' : 'tired', talk: talk('farmer', t), blink: blink(t, 99), look: { x: -0.6, y: 0.4 } });
      if (within(t, sg + 0.6, sg + 2.0)) {
        const k = (t - sg - 0.6) / 1.4;
        ctx.save();
        ctx.globalAlpha = (1 - k) * 0.8;
        ctx.fillStyle = '#ffffff';
        F.circle(ctx, 1420 - 30 - k * 120, porchY - 300 * 0.95 + k * 30, 14 + k * 30);
        ctx.fill();
        ctx.restore();
      }
    });
  };

  // ================================================================ RIOT
  SC.riot = (ctx, t, sc) => {
    const stomps = [1, 2, 3, 4, 5].map(i => c('stomp' + i));
    const tTwo = s('p_ourtokens') - 0.2, crowd = c('crowdRise'), hit = c('riotHit');
    const redK = P(t, sc.start, 3.5, E.inOut);
    const pal = F.mixPal(PAL.day, PAL.riot, redK);
    A.setTint(pal);
    const stompVal = (i) => {
      let v = 0;
      for (const T of stomps) {
        const T2 = T + i * 0.04;
        if (within(t, T2 - 0.28, T2)) v = Math.max(v, E.out((t - (T2 - 0.28)) / 0.28));
      }
      return v;
    };
    let cam;
    if (t < tTwo) cam = camPath(t, [[sc.start, { x: 1060, y: 700, z: 1.38 }], [tTwo, { x: 1050, y: 700, z: 1.46 }, E.sine]]);
    else if (t < hit) cam = camPath(t, [[tTwo, { x: 1150, y: 640, z: 1.35 }], [crowd - 0.1, { x: 1170, y: 640, z: 1.4 }], [crowd + 1.0, { x: 1060, y: 560, z: 0.98 }], [hit, { x: 1080, y: 560, z: 1.02 }]]);
    else cam = { x: 1420, y: porchY - 300, z: lerp(1.02, 2.8, P(t, hit, 0.18, E.out)) };
    cam = withShake(cam, hitShake(t, stomps.concat([hit]), 18, 0.22));
    A.farmSet(ctx, t, cam, pal, { chair: true, sunY: 420 + redK * 200, cloudA: 0.6 });
    world(ctx, cam, () => {
      // the mob
      const ck = P(t, crowd - 0.2, 1.4, E.lin);
      if (ck > 0) {
        for (let i = 0; i < 26; i++) {
          const kk = clamp(ck * 2.2 - (i % 9) * 0.12);
          const row = Math.floor(i / 9);
          const x = 160 + (i % 9) * 120 + row * 55 + hash(i) * 30;
          const y = G - 10 - row * 30 + (1 - E.back(kk)) * 140;
          if (kk > 0) A.sheep(ctx, { x, y, s: 0.5 - row * 0.05, dir: 1, t, seed: 200 + i, mood: 'angry', torch: i % 2 === 0, talk: baa(t, crowd + hash(i) * 2.5, 0.6), noShadow: true, wool: '#e9e2d4', bob: 0 });
        }
      }
      seatedFarmer(ctx, t, { pose: t > hit ? A.POSE.sit : A.POSE.sit, mood: t > s('p_ourtokens') ? 'shock' : 'worried', rock: 0, look: { x: -1, y: 0.3 } });
      const xs = [800, 940, 1080];
      xs.forEach((x, i) => {
        const who = i === 2 ? 'phar1' : i === 1 ? 'phar2' : null;
        const tk = who ? talk(who, t) : 0;
        const yelling = within(t, c('angryBaas'), c('angryBaas') + 2.3) ? baa(t, c('angryBaas') + i * 0.35, 0.6) + baa(t, c('angryBaas') + 1.1 + i * 0.3, 0.6) : 0;
        const sv = stompVal(i);
        const flaunt = i === 2 ? win(t, s('p_ourtokens') + 0.9, e('p_ourtokens') + 0.4, 0.25) : 0;
        A.sheep(ctx, Object.assign({ x, y: G + 110 - i * 5, s: 0.88, dir: 1, t, seed: 140 + i, mood: tk > 0.02 || yelling > 0.05 ? 'yell' : 'angry', talk: Math.max(tk, yelling), red: 0.5, stomp: sv, headTilt: -0.08,
          badge: PHAR_BAL[i], badgeS: 1 + flaunt * (0.32 + 0.06 * Math.sin(t * 12)), badgeGlow: flaunt }, PHAR));
        for (const T of stomps) A.dust(ctx, x + 50, G + 110, (t - T - i * 0.04) / 0.6, 0.8);
        if (yelling > 0.3) A.bubble(ctx, x + 30, G - 150 - i * 26, 190, 120, { k: 1, burst: true, text: 'BAA!', size: 44, fill: '#ff8a5a' });
      });
    });
    if (t > hit) A.flash(ctx, 1 - P(t, hit, 0.35, E.lin), '#ffffff');
  };

  // ================================================================ FACEPALM
  SC.facepalm = (ctx, t, sc) => {
    const pal = PAL.riot;
    A.setTint(pal);
    const sl = c('slap');
    const cam = withShake({ x: 1420, y: porchY - 290, z: 2.5 }, hitShake(t, [sl], 12, 0.2));
    A.farmSet(ctx, t, cam, pal, { chair: false, sunY: 620, cloudA: 0.6 });
    world(ctx, cam, () => {
      const k = P(t, sl - 0.16, 0.16, E.in);
      const slide = P(t, e('f_okay') + 0.1, 0.9) * 40;
      const pose = A.mixPose(A.POSE.idle, Object.assign({}, A.POSE.facepalm, { r: [8, -334 + slide], re: [44, -212 + slide * 0.5] }), k);
      A.farmer(ctx, { x: 1420, y: porchY + 10, s: 0.95, t, pose, armFront: 'r', mood: t > sl ? 'tired' : 'shock', talk: talk('farmer', t) * 0.6, slump: P(t, sl, 0.4) * 0.6, look: { x: -1, y: 0.2 } });
    });
  };

  // ================================================================ CROSS
  SC.cross = (ctx, t, sc) => {
    A.setTint({ tint: '#000000', tk: 0 });
    const k = P(t, s('n_crucify'), sc.end - s('n_crucify'), E.inOut);
    const cam = { x: lerp(1180, 1260, E.sine(P(t, sc.start, sc.end - sc.start, E.lin))), y: lerp(640, 600, k), z: lerp(1.0, 1.16, k) };
    A.calvary(ctx, t, k * 0.75, cam, { birds: P(t, c('bell'), 4.5, E.out) });
    blackout(ctx, 1 - P(t, sc.start, 0.9, E.lin));
    blackout(ctx, P(t, sc.end - 1.3, 1.2, E.lin));
  };

  // ================================================================ QUIET
  SC.quiet = (ctx, t, sc) => {
    const air = s('n_air'), cons = s('n_consequences'), crack = c('finalCrack'), rumble = c('rumble');
    const storm = P(t, air, crack - air, E.inOut);
    const pal = F.mixPal(PAL.night, PAL.storm, storm * 0.7);
    const fl = (at, d = 0.6) => (within(t, at, at + d) ? Math.exp(-(t - at) * 8) : 0);
    const flashK = fl(rumble) * 0.35 + fl(crack) * 1.0;
    A.setTint(pal, -flashK * 0.35);
    const cam = camPath(t, [
      [sc.start, { x: 1000, y: 560, z: 1.0 }],
      [air, { x: 1060, y: 560, z: 1.08 }],
      [e('n_air') + 0.5, { x: 1700, y: 588, z: 3.0 }],
      [cons + 0.2, { x: 1700, y: 588, z: 3.05 }],
      [crack, { x: 1150, y: 430, z: 0.92 }],
    ]);
    A.farmSet(ctx, t, cam, pal, {
      door: 0, lock: 1, lit: true, sun: false, moon: [420, 160, 1 - storm], cross: 1, crossSheep: false, cloudA: 0.35, starK: 1 - storm,
      windowContent: (g, wx, wy, ww, wh) => {
        g.fillStyle = '#ffcf7a'; g.fillRect(wx, wy, ww, wh);
        const lamp = g.createRadialGradient(wx + ww - 20, wy + wh - 20, 4, wx + ww - 20, wy + wh - 20, 120);
        lamp.addColorStop(0, 'rgba(255,255,220,0.9)'); lamp.addColorStop(1, 'rgba(255,200,120,0)');
        g.fillStyle = lamp; g.fillRect(wx, wy, ww, wh);
        A.farmer(g, { x: wx + ww * 0.7, y: wy + 204, s: 0.42, t, mood: 'worried', look: { x: -1, y: -0.3 }, noShadow: true, pose: A.POSE.idle, blink: blink(t, 99) });
      },
    });
    A.stormClouds(ctx, t, storm, cam, flashK);
    if (fl(crack) > 0) {
      ctx.save();
      applyCam(ctx, cam, 0.35);
      A.bolt(ctx, A.HILL_X + 40, -400, A.hillTop() - 40, 11, fl(crack));
      ctx.restore();
    }
    A.flash(ctx, flashK * 0.6, '#e8eeff');
    blackout(ctx, t > crack + 0.18 ? 1 : 0);
  };

  // ================================================================ FIX (one way to fix it)
  SC.fix = (ctx, t, sc) => {
    const tMend = s('e_paywall') - 0.3, tShop = c('stallIn'), tPay = c('fixPress') - 0.4;
    const gone = c('gateGone'), freeAt = c('feederFree'), flock = c('flock');
    if (t < tMend) {
      // dawn: the storm clears; the turnstile and coin box are still there
      const k = P(t, sc.start, 3.5, E.inOut);
      const pal = F.mixPal(PAL.storm, PAL.morning, k);
      A.setTint(pal);
      const cam = camPath(t, [[sc.start, { x: 960, y: 560, z: 1.0 }], [tMend, { x: 900, y: 600, z: 1.07 }, E.sine]]);
      A.farmSet(ctx, t, cam, pal, { door: 0, lock: 1, cross: 1, sunX: 1450, sunY: lerp(700, 250, P(t, sc.start, 5.5, E.out)), cloudA: 0.6 });
      A.stormClouds(ctx, t, 1 - P(t, sc.start, 4.5, E.inOut), cam, 0);
      world(ctx, cam, () => {
        A.sheep(ctx, { x: 700, y: G + 120, s: 0.72, dir: 1, t, seed: 301, thin: true, wool: '#e2dccf', mood: 'tired', droop: 1, badge: 0 });
        A.sheep(ctx, { x: 1180, y: G + 135, s: 0.72, dir: -1, t, seed: 302, thin: true, wool: '#e2dccf', mood: 'sad', droop: 1, badge: 0 });
        A.farmer(ctx, { x: 920, y: farmerY, t, pose: A.POSE.hips, mood: 'tired', look: { x: 1, y: -0.6 }, blink: blink(t, 99) });
      });
      blackout(ctx, 1 - P(t, sc.start, 1.4, E.lin));
      return;
    }
    if (t < tShop) {
      // the paywall comes down
      const pal = PAL.morning;
      A.setTint(pal);
      const cam = camPath(t, [[tMend, { x: 690, y: 640, z: 1.32 }], [tShop, { x: 720, y: 650, z: 1.38 }, E.sine]]);
      const gate = 1 - P(t, gone, 0.32, E.in);
      const free = P(t, freeAt - 0.25, 0.6, E.lin);
      A.farmSet(ctx, t, cam, pal, {
        door: P(t, gone + 0.2, 0.7, E.inOut), lock: 1 - P(t, gone - 0.05, 0.2, E.lin), gate, free,
        hay: lerp(0.25, 1, E.bounce(P(t, freeAt, 0.5, E.lin))), cross: 1, sunX: 1450, sunY: 250,
      });
      world(ctx, cam, () => {
        A.dust(ctx, FARM.barnX + 150, G + 12, (t - gone) / 0.7, 1.3);
        if (within(t, gone, gone + 0.8)) A.sparkle(ctx, FARM.barnX + 150, G - 120, 1.2, 1 - P(t, gone, 0.8, E.lin), t * 3);
        if (within(t, freeAt, freeAt + 0.8)) A.sparkle(ctx, FARM.feederX - 163, G - 200, 1.2, 1 - P(t, freeAt, 0.8, E.lin), t * 3);
        // a mixed flock: no tokens, some tokens, rich - everyone eats, everyone sleeps inside
        const eaters = [
          { seed: 311, from: 1500, to: 905, y: G + 92, thin: true, wool: '#e2dccf', badge: 0, d: 0.0 },
          { seed: 312, from: 1620, to: 1045, y: G + 100, badge: 3, d: 0.35 },
        ];
        eaters.forEach((h, i) => {
          const k = P(t, flock + h.d, 2.0, E.out);
          const x = lerp(h.from, h.to, k);
          const eating = t > flock + h.d + 2.0;
          A.sheep(ctx, { x, y: h.y, s: 0.74, dir: -1, t, seed: h.seed, thin: h.thin, wool: h.wool, walk: eating ? null : x * 0.05, badge: h.badge,
            mood: eating ? 'happy' : 'neutral', talk: eating ? 0.3 + 0.3 * Math.sin(t * 17 + i) : 0, headDy: eating ? 16 : 0, headTilt: eating ? 0.3 : 0 });
          if (eating) A.heart(ctx, x - 40, h.y - 190 - ((t * 0.6 + i * 0.5) % 1) * 60, 0.9, 1 - ((t * 0.6 + i * 0.5) % 1));
        });
        const sleepers = [
          { seed: 313, from: 980, badge: 0, thin: true, wool: '#e2dccf', d: 0.6 },
          { seed: 314, from: 1180, badge: 540, rich: true, d: 1.1 },
          { seed: 315, from: 1380, badge: 0, punk: true, wool: '#d8d2c6', d: 1.6 },
        ];
        sleepers.forEach((h) => {
          const k = P(t, flock + h.d, 2.6, E.inOut);
          const x = lerp(h.from, FARM.barnX, k);
          const a = 1 - P(t, flock + h.d + 2.3, 0.35, E.lin);
          if (a <= 0) return;
          A.sheep(ctx, Object.assign({ x, y: G + 62, s: 0.62, dir: -1, t, seed: h.seed, walk: x * 0.05, badge: h.badge, alpha: a, badgeA: a, mood: 'happy',
            thin: h.thin, wool: h.wool, punk: h.punk }, h.rich ? { wool: '#fbefd0', fluff: 1.12 } : {}));
        });
      });
      const st = P(t, c('freeStamp') - 0.05, 0.35, E.lin);
      if (st > 0) A.stamp(ctx, 'BASIC NEEDS: FREE', W / 2, 150, st, -0.06, '#2f9e4f');
      return;
    }
    if (t < tPay) {
      // luxuries: the farmer can charge whatever he likes
      const pal = PAL.morning;
      A.setTint(pal);
      const cam = camPath(t, [[tShop, { x: 1300, y: 570, z: 1.3 }], [tPay, { x: 1290, y: 580, z: 1.36 }, E.sine]]);
      A.farmSet(ctx, t, cam, pal, { gate: 0, free: 1, door: 1, hay: 1, cross: 1, sunX: 1450, sunY: 250 });
      const ch = c('chaching');
      world(ctx, cam, () => {
        const k = pop(t, tShop, 0.45);
        ctx.save();
        ctx.translate(1380, G + 80);
        ctx.scale(k, k);
        ctx.translate(-1380, -(G + 80));
        A.stall(ctx, 1380, G + 80, t, {});
        A.farmer(ctx, { x: 1380, y: G + 40, s: 0.85, t, pose: t > ch ? A.POSE.hold : A.POSE.hips, prop: t > ch ? { r: 'smallToken' } : null, tokenSpin: t * 5, mood: t > ch - 0.2 ? 'grin' : 'smile', look: { x: -1, y: 0.4 }, noShadow: true });
        A.stall(ctx, 1380, G + 80, t, { front: true, sold: t > ch ? ['GAME CONSOLE'] : [] });
        ctx.restore();
        const bought = t > ch;
        A.sheep(ctx, Object.assign({ x: 1020, y: G + 112, s: 0.8, dir: 1, t, seed: 320, badge: bought ? 112 : 612, mood: bought ? 'happy' : 'neutral', headTilt: -0.1, blink: blink(t, 320) },
          { wool: '#fbefd0', fluff: 1.14 }));
        if (bought) A.console(ctx, 990, G + 112 - 0.8 * 150, 0.8 * pop(t, ch, 0.35));
        for (let i = 0; i < 6; i++) {
          const kk = (t - ch + 0.35 - i * 0.05) / 0.4;
          if (kk > 0 && kk < 1) A.token(ctx, lerp(1030, 1250, kk), lerp(G - 70, G - 120, kk) - Math.sin(kk * Math.PI) * 90, 14, t * 10 + i);
        }
        if (within(t, ch, ch + 0.9)) A.sparkle(ctx, 1000, G - 30, 1.2, 1 - P(t, ch, 0.9, E.lin), t * 4);
      });
      return;
    }
    // the token remote no longer gets rid of anyone
    const pal = PAL.morning;
    A.setTint(pal);
    const toss = c('remoteToss'), land = c('remoteLand'), press = c('fixPress'), drain = c('fixDrain'), shrug = c('fixShrug');
    const cam = camPath(t, [[tPay, { x: 820, y: 660, z: 1.45 }], [toss - 0.2, { x: 830, y: 660, z: 1.5 }], [sc.end, { x: 900, y: 600, z: 1.15 }]]);
    A.farmSet(ctx, t, cam, pal, { gate: 0, free: 1, door: 1, hay: 1, cross: 1, sunX: 1450, sunY: 250 });
    world(ctx, cam, () => {
      const n = t < drain ? 4 : Math.max(0, 4 - Math.floor(((t - drain) / 0.8) * 5));
      const lookAtBadge = within(t, drain + 0.2, shrug + 0.4);
      const eating = !lookAtBadge;
      const wig = within(t, shrug, shrug + 0.6) ? Math.sin((t - shrug) * 22) * 0.12 : 0;
      A.sheep(ctx, { x: 855, y: G + 92, s: 0.85, dir: 1, t, seed: 90, wool: '#d8d2c6', punk: true, badge: n, badgeS: t > drain && t < drain + 1.5 ? 1.2 : 1,
        mood: eating ? 'happy' : 'neutral', look: lookAtBadge ? { x: -0.3, y: -1 } : { x: 1, y: 0.4 },
        talk: eating ? 0.3 + 0.3 * Math.sin(t * 17) : 0, headDy: eating ? 16 : 0, headTilt: (eating ? 0.3 : -0.1) + wig });
      if (within(t, shrug + 0.5, shrug + 2.0)) A.heart(ctx, 900, G - 150 - P(t, shrug + 0.5, 1.5, E.lin) * 60, 1, 1 - P(t, shrug + 1.4, 0.6, E.lin));
      const pr = within(t, press - 0.08, press + 0.25) ? 1 : 0;
      let pose = A.POSE.remote, prop = { r: 'remote' }, mood = 'frown';
      if (t > drain + 0.9) mood = 'shock';
      if (t > shrug + 1.0) mood = 'tired';
      if (t > toss - 0.45) { pose = A.mixPose(A.POSE.remote, A.POSE.hold, P(t, toss - 0.45, 0.4)); }
      if (t > toss) { prop = null; pose = A.mixPose(A.POSE.hold, A.POSE.hips, P(t, toss + 0.3, 0.5)); mood = 'smile'; }
      A.farmer(ctx, { x: 560, y: farmerY, t, pose, prop, press: pr, mood, look: t > shrug + 0.6 && t < toss ? { x: 0.6, y: 0.8 } : { x: 1, y: 0.2 }, blink: blink(t, 99) });
      if (t > toss && t < land + 2) {
        const k = clamp((t - toss) / (land - toss));
        const x = lerp(560 + 96, 1250, k), y = lerp(farmerY - 440, G + 40, k) - Math.sin(k * Math.PI) * 300;
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(t < land ? (t - toss) * 14 : 1.4);
        A.remote(ctx, 0, 0, 0);
        ctx.restore();
      }
    });
  };

  // ================================================================ END
  SC.end = (ctx, t, sc) => {
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    const k = P(t, c('endBoom'), 1.2) * (1 - P(t, sc.end - 1.2, 1.1, E.lin));
    const sc2 = lerp(0.92, 1, P(t, c('endBoom'), 4, E.out));
    ctx.save();
    ctx.translate(W / 2, H / 2 - 20);
    ctx.scale(sc2, sc2);
    text(ctx, 'FLEECED', 0, 0, { size: 220, font: FONT_TITLE, weight: 400, fill: '#f3e6c8', alpha: k, ls: 10 });
    ctx.restore();
    text(ctx, F.TL.subtitle, W / 2, H / 2 + 130, { size: 44, weight: 500, fill: '#bfae8e', alpha: k * P(t, c('endBoom') + 0.8, 1) });
  };

  window.SCENES = SC;
})();
