/* EMOTIONAL CHAD - scene choreography. Every beat is keyed to timeline cues/lines. */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp, E, hash, cue: c, S: s, End: e, P, talk, camPath, applyCam, lerpCam, hitShake, shake, text, FONT_TITLE, mix, mixPal, line, TL } = F;
  const A = window.A;
  const CP = A.CPAL;
  const PP = A.PP;

  const blink = (t, seed) => ((t * 0.9 + hash(seed) * 7) % (3.4 + hash(seed + 2) * 2)) < 0.13;
  const within = (t, a, b) => t >= a && t < b;
  const pop = (t, at, d = 0.35) => E.back(clamp((t - at) / d));
  /** fake mouth movement for someone talking under the narration */
  const chatter = (t) => Math.max(0, 0.15 + 0.45 * Math.sin(t * 13) * Math.sin(t * 5.3 + 1));
  /** roughly when `word` is spoken inside line `id` */
  function wAt(id, word) {
    const l = line(id), i = l.text.indexOf(word);
    if (i < 0) throw new Error(`"${word}" not in ${id}`);
    return l.start + (i / l.text.length) * (l.end - l.start);
  }
  function step(t, keys) {
    let v = keys[0][1];
    for (const [k, x] of keys) if (t >= k) v = x;
    return v;
  }
  function poseTrack(t, keys, d = 0.35) {
    const get = (k) => (typeof k === 'string' ? PP[k] : k);
    let p = get(keys[0][1]);
    for (let i = 1; i < keys.length && t >= keys[i][0]; i++) p = A.mixPP(p, get(keys[i][1]), E.inOut(clamp((t - keys[i][0]) / d)));
    return p;
  }
  /** camera that eases to a framing for whoever is speaking (by line id, then by speaker) */
  function shotCam(t, sc, shots, def, d = 0.7) {
    let prev = def, cur = def, at = -1e9;
    for (const l of TL.lines) {
      if (l.start < sc.start || l.start >= sc.end || t < l.start - 0.35) continue;
      const nx = shots[l.id] || shots[l.who] || def;
      if (nx !== cur) { prev = lerpCam(prev, cur, E.inOut(clamp((l.start - 0.35 - at) / d))); cur = nx; at = l.start - 0.35; }
    }
    return lerpCam(prev, cur, E.inOut(clamp((t - at) / d)));
  }
  function world(ctx, cam, fn) {
    ctx.save();
    applyCam(ctx, cam, 1);
    fn();
    ctx.restore();
  }
  const withShake = (cam, sh) => ({ x: cam.x + sh.x, y: cam.y + sh.y, z: cam.z, r: cam.r || 0 });
  function toScreen(cam, x, y, depth = 1) {
    const z = 1 + (cam.z - 1) * depth;
    return { x: W / 2 + (x - (W / 2 + (cam.x - W / 2) * depth)) * z, y: H / 2 + (y - (H / 2 + (cam.y - H / 2) * depth)) * z, z };
  }
  function flashAt(ctx, t, at, d = 0.35, color = '#ffffff', peak = 0.9) {
    if (t >= at && t < at + d) A.flash(ctx, peak * (1 - (t - at) / d), color);
  }
  function caption(ctx, str, y, k, color = '#ffd166') {
    if (k <= 0) return;
    ctx.save();
    ctx.translate(W / 2, y);
    const sc = lerp(0.7, 1, E.back(clamp(k)));
    ctx.scale(sc, sc);
    text(ctx, str, 0, 0, { size: 60, font: FONT_TITLE, weight: 400, fill: color, stroke: A.OUT, lw: 12, alpha: clamp(k * 2), ls: 3 });
    ctx.restore();
  }

  // ------------------------------------------------------------------ cast
  const VIL = [
    { outfit: { top: '#5f8a7a', top2: '#4a6e61' }, hair: '#3a2a20', hairStyle: 0 },
    { outfit: { top: '#c46a8a', top2: '#a8506e', pants: '#4a4a6a' }, hair: '#7a3a1a', hairStyle: 1 },
    { outfit: { top: '#e0b03a', top2: '#c4962a', pants: '#5a4a3a', skin: '#c99068' }, hair: '#1a1410', hairStyle: 2 },
    { outfit: { top: '#6a7ad0', top2: '#5060b0', skin: '#a8724e' }, hair: '#2a1a12', hairStyle: 0 },
    { outfit: { top: '#e07050', top2: '#c05a3a', pants: '#3a4a5a' }, hair: '#d8b070', hairStyle: 1 },
    { outfit: { top: '#8ab060', top2: '#6a9048', skin: '#f2d0b0' }, hair: '#6a6a6a', hairStyle: 2 },
  ];
  function vil(ctx, i, o) {
    const v = VIL[i % VIL.length];
    A.person(ctx, Object.assign({ kind: 'villager', blink: blink(o.t, 40 + i) }, v, o, { outfit: Object.assign({}, v.outfit, o.outfit || {}) }));
  }
  function chad(ctx, o) {
    A.person(ctx, Object.assign({ kind: 'chad', blink: blink(o.t, 7) }, o));
  }
  const auraCol = (sup) => mix('#bfe6ff', '#ffd23a', sup);
  function goku(ctx, t, o) {
    const sc = o.s ?? 1;
    if (o.aura > 0) A.aura(ctx, o.x, o.y + (o.legs === 'fly' ? 40 * sc : 0), sc * 1.05, t, o.aura, o.auraColor || auraCol(o.super || 0));
    A.person(ctx, Object.assign({ kind: 'goku', t }, o));
    if (o.sparks) A.sparks(ctx, o.x, o.y, sc, t, o.sparks);
  }
  function alien(ctx, t, o) {
    const sc = o.s ?? 1;
    if (o.aura > 0) A.aura(ctx, o.x, o.y + (o.legs === 'fly' ? 40 * sc : 0), sc, t, o.aura, '#7ad7ff');
    A.person(ctx, Object.assign({ kind: 'alien', t, mood: 'calm' }, o));
  }
  /** light rays fanning out behind Chad */
  function glory(ctx, x, y, t, k, big = 1) {
    if (k <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.globalAlpha *= clamp(k);
    const g = ctx.createRadialGradient(0, 0, 10, 0, 0, 420 * big);
    g.addColorStop(0, 'rgba(255,248,200,0.75)');
    g.addColorStop(1, 'rgba(255,240,170,0)');
    ctx.fillStyle = g;
    F.circle(ctx, 0, 0, 420 * big); ctx.fill();
    ctx.rotate(t * 0.12);
    for (let i = 0; i < 18; i++) {
      ctx.rotate(TAU / 18);
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-36 * big, -1100 * big); ctx.lineTo(36 * big, -1100 * big); ctx.closePath();
      ctx.fillStyle = i % 2 ? 'rgba(255,240,170,0.2)' : 'rgba(255,255,255,0.1)';
      ctx.fill();
    }
    ctx.restore();
  }
  /** "mind blown": a burst of sparkles and a light bulb */
  function mindBlown(ctx, x, y, t, at) {
    const k = t - at;
    if (k < 0) return;
    if (k < 1.2) {
      for (let i = 0; i < 9; i++) {
        const a = (i / 9) * TAU + 0.3, r = 40 + 170 * E.out(clamp(k / 0.8));
        A.sparkle(ctx, x + Math.cos(a) * r, y + 20 + Math.sin(a) * r * 0.7, 0.7, 1 - clamp(k / 1.2), k * 3 + i);
      }
    }
    A.bulb(ctx, x, y - 6 * Math.sin(t * 3 + x), 0.9 * clamp(pop(t, at, 0.4), 0.01, 2), 1);
  }
  function phoneUI(ctx, x, y, t, k, vm) {
    A.bubble(ctx, x, y, 400, 124, { k, tail: -110, tailDx: -30, draw: (cx) => {
      if (!vm) {
        text(cx, 'Calling: Universe Guy', 0, -18, { size: 30, weight: 700, fill: '#2b1d16' });
        const n = 1 + (Math.floor(t * 3) % 3);
        text(cx, '• '.repeat(n).trim(), 0, 26, { size: 40, weight: 700, fill: '#5a7a9a' });
      } else {
        text(cx, 'VOICEMAIL', 0, -14, { size: 46, font: FONT_TITLE, weight: 400, fill: '#d6453a' });
        text(cx, 'leave a message after the beep', 0, 32, { size: 24, weight: 600, fill: '#6a5a50' });
      }
    } });
  }
  function space(ctx, t) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#07041a'); g.addColorStop(1, '#2a1652');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    for (const [x, y, r, col] of [[420, 360, 300, '#7a3aa0'], [1500, 760, 360, '#2a5aa0']]) {
      const n = ctx.createRadialGradient(x, y, 10, x, y, r);
      n.addColorStop(0, F.rgba(col, 0.45)); n.addColorStop(1, F.rgba(col, 0));
      ctx.fillStyle = n; F.circle(ctx, x, y, r); ctx.fill();
    }
    A.stars(ctx, t, 1);
    ctx.save();
    ctx.translate(1520, 260);
    F.circle(ctx, 0, 0, 90); ctx.fillStyle = '#e0884a'; ctx.fill(); ctx.strokeStyle = A.OUT; ctx.lineWidth = 6; ctx.stroke();
    ctx.strokeStyle = '#f6d6a0'; ctx.lineWidth = 12; F.ellipse(ctx, 0, 0, 160, 34, -0.25); ctx.stroke();
    ctx.restore();
    F.circle(ctx, 300, 860, 60); ctx.fillStyle = '#5ab0a0'; ctx.fill(); ctx.strokeStyle = A.OUT; ctx.lineWidth = 6; ctx.stroke();
    F.circle(ctx, 1760, 980, 30); ctx.fillStyle = '#c0c0d0'; ctx.fill(); ctx.stroke();
  }

  const SC = {};

  // ================================================================ TITLE
  SC.title = (ctx, t, sc) => {
    const pal = CP.canyon;
    A.setTint(pal);
    const panK = P(t, c('titlePan'), sc.end - c('titlePan') + 0.3, E.inOut);
    const cam = { x: 960, y: lerp(-330, 600, panK), z: 1 };
    A.canyon(ctx, t, cam, pal, { peaks: [{ x: 1720 }], sunX: 1480, sunY: 170 });
    world(ctx, cam, () => {
      goku(ctx, t, { x: 960, y: 980, s: 1.1, legs: 'wide', pose: PP.power, eyesClosed: true, mood: 'scowl', aura: 0.35 * panK, dir: 1 });
      const k = P(t, c('titleDrop'), c('titleLand') - c('titleDrop'), E.in);
      const land = t - c('titleLand');
      const sq = land > 0 ? Math.exp(-land * 7) * Math.sin(land * 28) * 0.2 : 0;
      ctx.save();
      ctx.translate(960, lerp(-1200, -420, k));
      ctx.scale(1 + sq, 1 - sq);
      const o = { font: FONT_TITLE, weight: 400, stroke: '#2b1d16', lw: 24, shadow: 'rgba(43,29,22,0.35)', sx: 0, sy: 14, ls: 6 };
      text(ctx, 'EMOTIONAL', 0, -95, Object.assign({ size: 170, fill: '#9fd8ff' }, o));
      text(ctx, 'CHAD', 0, 95, Object.assign({ size: 250, fill: '#fff6e0' }, o));
      ctx.restore();
      const sa = P(t, c('titleSub'), 0.7);
      text(ctx, TL.subtitle, 960, -150, { size: 60, weight: 700, fill: '#2b1d16', alpha: sa });
    });
  };

  // ================================================================ CHARGE (power-up intercut with the village)
  SC.charge = (ctx, t, sc) => {
    const vc = c('villageCut'), gc = c('gokuCut'), vc2 = c('villageCut2'), gc2 = c('gokuCut2');
    if (t < vc || within(t, gc, vc2) || t >= gc2) {
      // ---- Goku powering up in the canyon
      const storm = t < vc ? P(t, sc.start, vc - sc.start, E.lin) * 0.7 : t < vc2 ? 0.85 : 1;
      const pal = mixPal(CP.canyon, CP.canyonStorm, storm);
      A.setTint(pal);
      let cam, sup, lvl, eyesClosed = true, mood = 'yell', tk = 0, aura;
      if (t < vc) {
        cam = camPath(t, [[sc.start, { x: 960, y: 640, z: 1 }], [vc, { x: 960, y: 650, z: 1.3 }]]);
        sup = P(t, c('hair1'), 0.5);
        lvl = 0.4 * P(t, c('hair2'), 1.0);
        aura = 0.35 + 0.65 * P(t, c('hair1'), 0.4);
      } else if (t < vc2) {
        cam = camPath(t, [[gc, { x: 960, y: 700, z: 1.55 }], [vc2, { x: 960, y: 690, z: 1.75 }]]);
        sup = 1;
        lvl = lerp(0.4, 1, P(t, c('yell2'), c('level5') - c('yell2'), E.inOut));
        aura = 1;
      } else {
        const eo = c('eyesOpen');
        cam = camPath(t, [[gc2, { x: 960, y: 640, z: 2.0 }], [eo, { x: 960, y: 640, z: 2.25 }], [s('g_where'), { x: 960, y: 640, z: 2.3 }],
          [s('g_where') + 0.7, { x: 960, y: 700, z: 1.35 }, E.out], [sc.end, { x: 960, y: 690, z: 1.25 }]]);
        sup = 1; lvl = 1;
        eyesClosed = t < eo;
        mood = t < eo ? 'scowl' : 'yell';
        tk = talk('goku', t);
        if (t >= eo && t < s('g_where')) mood = 'scowl';
        aura = t < eo ? 0.75 : 1;
      }
      const amp = t < vc ? 2 + 6 * P(t, sc.start, 6, E.lin) : t < vc2 ? 8 : t < c('eyesOpen') ? 3 : 5;
      let sh = shake(t, amp);
      const hs = hitShake(t, [c('quake1'), c('level5'), c('eyesOpen')], 26, 0.3);
      cam = withShake(cam, { x: sh.x + hs.x, y: sh.y + hs.y });
      A.canyon(ctx, t, cam, pal, { peaks: [{ x: 1720 }, { x: 180 }], sunX: 1480, sunY: 170 });
      world(ctx, cam, () => {
        A.rocks(ctx, 960, 980, t, t < vc ? P(t, sc.start + 0.6, 5) : 1, 3);
        goku(ctx, t, { x: 960, y: 980, s: 1.1, legs: 'wide', pose: t >= s('g_where') ? poseTrack(t, [[0, 'power'], [s('g_where'), 'explain'], [wAt('g_where', 'I know'), 'power']]) : PP.power,
          eyesClosed, mood, talk: tk, super: sup, level: lvl, aura, sparks: sup > 0.5 ? 0.9 : 0, dir: 1 });
      });
      // eyes snap open: two glints
      if (within(t, c('eyesOpen'), c('eyesOpen') + 0.5)) {
        const p = toScreen(cam, 960, 980 - 1.1 * 300);
        const k = 1 - (t - c('eyesOpen')) / 0.5;
        for (const sx of [-1, 1]) A.sparkle(ctx, p.x + sx * 18 * 1.1 * p.z, p.y, 1.6 * k, k, t * 5);
      }
      flashAt(ctx, t, c('hair1'), 0.45);
      flashAt(ctx, t, gc, 0.25);
      flashAt(ctx, t, gc2, 0.25);
      flashAt(ctx, t, c('level5'), 0.4, '#fff6c0');
      if (within(t, gc, vc2)) A.stamp(ctx, 'SUPER SAIYAN 5', 470, 200, P(t, wAt('n_level5', 'fifth'), 0.5, E.lin), -0.06, '#ffb13b');
      return;
    }

    // ---- Chad in the village
    const pal = CP.village;
    A.setTint(pal);
    if (t < gc) {
      // one by one
      const cam = camPath(t, [[vc, { x: 1110, y: 650, z: 1.05 }], [gc, { x: 1100, y: 640, z: 1.14 }]]);
      A.village(ctx, t, cam, pal, {});
      world(ctx, cam, () => {
        glory(ctx, 700, 700, t, 0.55);
        chad(ctx, { x: 700, y: 990, t, dir: 1, pose: poseTrack(t, [[0, 'explain'], [c('mind2') - 0.3, 'shrug'], [c('mind3') - 0.2, 'explain']]), mood: 'smile', talk: chatter(t) });
        ['mind1', 'mind2', 'mind3'].forEach((m, i) => {
          const x = 1050 + i * 250, at = c(m);
          const mood = t < at ? 'neutral' : t < at + 0.7 ? 'shock' : 'happy';
          vil(ctx, i, { x, y: 990 - i * 6, t, dir: -1, mood, look: { x: -1, y: 0 }, pose: t > at + 0.7 ? poseTrack(t, [[0, 'idle'], [at + 0.7, 'heart']]) : PP.idle });
          mindBlown(ctx, x, 990 - 470, t, at);
        });
      });
    } else {
      // the whole village
      const cam = camPath(t, [[vc2, { x: 960, y: 620, z: 0.98 }], [gc2, { x: 960, y: 600, z: 0.92 }]]);
      A.village(ctx, t, cam, pal, {});
      const m4 = c('mind4');
      world(ctx, cam, () => {
        glory(ctx, 960, 680, t, 0.45 + 0.55 * P(t, m4, 0.6), 1 + 0.5 * P(t, m4, 0.8));
        const crowd = [[380, 930, 1, 1], [640, 900, 1, 0.92], [1290, 900, -1, 0.92], [1550, 930, -1, 1], [500, 1060, 1, 1.08], [1420, 1060, -1, 1.08]];
        const back = crowd.filter(q => q[1] < 1000), front = crowd.filter(q => q[1] >= 1000);
        const drawV = ([x, y, dir, sc2]) => {
          const i = crowd.findIndex(q => q[0] === x);
          const at = m4 + i * 0.09;
          vil(ctx, i, { x, y, s: sc2, t, dir, mood: t < at ? 'neutral' : t < at + 0.6 ? 'shock' : 'happy', look: { x: dir > 0 ? 1 : -1, y: -0.3 },
            pose: t > at + 0.6 ? poseTrack(t, [[0, 'idle'], [at + 0.6, 'yellUp']]) : PP.idle });
          mindBlown(ctx, x, y - 470 * sc2, t, at);
        };
        back.forEach(drawV);
        chad(ctx, { x: 960, y: 960, t, dir: 1, pose: poseTrack(t, [[0, 'explain'], [m4 - 0.5, 'shrug']]), mood: 'smile', talk: chatter(t) });
        front.forEach(drawV);
      });
    }
  };

  // ================================================================ VILLAGE (helping a villager with his anger)
  SC.village = (ctx, t, sc) => {
    const pal = CP.village;
    A.setTint(pal);
    const calm = c('calm'), fy = c('farYell'), jo = c('jogOff');
    const cam0 = { x: 980, y: 640, z: 1.08 };
    let cam = camPath(t, [[sc.start, cam0], [fy, { x: 990, y: 640, z: 1.12 }], [fy + 0.6, { x: 1040, y: 630, z: 1.04 }], [sc.end, { x: 1200, y: 630, z: 1.02 }]]);
    cam = withShake(cam, hitShake(t, [fy], 7, 0.3));
    A.village(ctx, t, cam, pal, { flashes: within(t, fy, fy + 1.4) ? Math.exp(-(t - fy) * 2.5) : 0, flashX: 1900 });
    const heard = t >= fy + 0.15;
    world(ctx, cam, () => {
      vil(ctx, 0, { x: 260, y: 905, s: 0.85, t, dir: 1, mood: heard ? 'shock' : 'smile', look: heard ? { x: 1, y: -0.3 } : { x: 1, y: 0 } });
      vil(ctx, 1, { x: 1660, y: 905, s: 0.85, t, dir: -1, mood: heard ? 'shock' : 'smile', look: heard ? { x: 1, y: -0.3 } : { x: -1, y: 0 } });
      // the angry villager
      const ang = 1 - P(t, calm, 0.8);
      const vx = 1150;
      vil(ctx, 3, { x: vx, y: 990, t, dir: -1, mood: ang > 0.5 ? 'scowl' : heard ? 'neutral' : 'smile', look: heard ? { x: 1, y: -0.2 } : { x: -1, y: 0 },
        outfit: { skin: mix('#a8724e', '#d9503a', ang) }, pose: poseTrack(t, [[0, 'power'], [calm, 'idle'], [calm + 0.3, 'heart'], [fy + 0.2, 'idle']]),
        talk: t < calm - 0.5 ? chatter(t + 3) * 0.8 : 0, rot: ang > 0.3 ? Math.sin(t * 30) * 0.015 : 0 });
      A.steam(ctx, vx - 40, 990 - 480, t, ang);
      A.steam(ctx, vx + 40, 990 - 480, t + 0.3, ang);
      if (within(t, calm + 0.2, calm + 2.2)) A.heart(ctx, vx, 990 - 500 - P(t, calm + 0.2, 2, E.lin) * 80, 1.6, 1 - P(t, calm + 1.6, 0.6, E.lin));
      // Chad
      const jog = t >= jo;
      const x = jog ? 820 + (t - jo) * 780 : 820;
      chad(ctx, { x, y: 1000, t, dir: 1, legs: jog ? 'jog' : 'stand', jog: t * 14,
        pose: poseTrack(t, [[0, 'heart'], [calm - 0.6, 'explain'], [fy + 0.15, 'idle'], [wAt('c_onesec_village', "I'll"), 'wave'], [e('c_onesec_village') - 0.3, 'jog']]),
        mood: t < fy + 0.15 ? 'calm' : t < s('c_onesec_village') ? 'shock' : 'smile', talk: t < calm ? chatter(t) : talk('chad', t),
        look: heard && t < s('c_onesec_village') + 0.6 ? { x: 1, y: -0.3 } : { x: 0, y: 0 } });
      if (heard) A.mark(ctx, '!', x + 10, 1000 - 520, 1.1, 1 - P(t, fy + 1.2, 0.4, E.lin));
    });
  };

  // ================================================================ MEET + PANG (the canyon conversation)
  const GX = 1260, CX = 700, GY = 980;
  function gokuMeet(ctx, t, o) {
    goku(ctx, t, Object.assign({ x: GX, y: GY, s: 1.05, dir: -1, super: 1, level: 1, blink: blink(t, 3), talk: talk('goku', t) }, o));
  }

  SC.meet = (ctx, t, sc) => {
    const pal = CP.canyon;
    A.setTint(pal);
    const arr = c('chadArrive'), arrEnd = arr + 2.8;
    const wide = { x: 960, y: 640, z: 1 };
    const gShot = { x: 1170, y: 620, z: 1.42 };
    const cShot = { x: 780, y: 660, z: 1.42 };
    let cam = shotCam(t, sc, {
      goku: gShot, chad: cShot, g_runaway: { x: 1000, y: 640, z: 1.05 }, n_breath: cShot,
      g_omega: { x: 1110, y: 560, z: 1.12 }, c_boundary: { x: 900, y: 640, z: 1.15 },
    }, wide);
    const planet = c('planet');
    cam = withShake(cam, hitShake(t, [planet, wAt('g_amazing', 'amazing')], 12, 0.3));
    A.canyon(ctx, t, cam, pal, { peaks: [{ x: 2300 }, { x: -400 }], sunX: 1500, sunY: 180 });
    world(ctx, cam, () => {
      // Goku
      const om = s('g_omega');
      const flare = P(t, om, 0.4) * (1 - P(t, e('g_omega') + 0.4, 0.8));
      gokuMeet(ctx, t, {
        aura: 0.55 + 0.12 * Math.sin(t * 3) + 0.45 * flare, sparks: 0.4 + 0.6 * flare,
        pose: poseTrack(t, [[0, 'cross'], [wAt('g_runaway', "Don't"), 'power'], [e('g_runaway') + 0.3, 'cross'], [om, 'power'], [wAt('g_omega', 'I can'), 'explain'],
          [planet - 0.15, 'punch'], [e('g_omega') + 0.3, 'cross'], [s('g_amazing'), 'yellUp'], [e('g_amazing') + 0.3, 'cross'], [s('g_destroy'), 'punch'],
          [e('g_destroy') + 0.3, 'cross'], [s('g_none'), 'shrug'], [wAt('g_none', 'But'), 'explain'], [e('g_none') + 0.3, 'cross']]),
        mood: step(t, [[0, 'scowl'], [s('c_sorry') + 2.5, 'flat'], [s('g_omega'), 'scowl'], [s('g_amazing'), 'yell'], [e('g_amazing') + 0.2, 'smile'], [s('g_destroy'), 'scowl'],
          [s('c_enemies'), 'flat'], [s('g_none'), 'flat'], [wAt('g_none', 'But'), 'scowl'], [s('c_boundary'), 'neutral']]),
        look: t >= arr ? { x: 1, y: 0.2 } : { x: 1, y: 0 },
      });
      // the planet he could destroy
      const pb0 = wAt('g_omega', 'I can'), pb1 = e('g_omega') + 0.8;
      const bk = P(t, pb0, 0.35, E.back) * (1 - P(t, pb1, 0.3, E.lin));
      if (bk > 0) {
        A.bubble(ctx, 1560, 290, 330, 240, { k: bk, thought: true, draw: (cx) => {
          if (t < planet + 0.1) {
            F.circle(cx, 0, 0, 62); cx.fillStyle = '#4a8fd6'; cx.fill(); cx.strokeStyle = A.OUT; cx.lineWidth = 5; cx.stroke();
            cx.fillStyle = '#6cc46a';
            F.ellipse(cx, -18, -14, 22, 16, 0.3); cx.fill(); F.ellipse(cx, 22, 18, 18, 12, -0.4); cx.fill();
          }
          A.explosion(cx, 0, 0, t - planet, 110);
          if (t > planet) text(cx, '0.5 sec', 0, 84, { size: 26, weight: 700, fill: '#d6453a', alpha: P(t, planet + 0.2, 0.3) });
        } });
      }
      // Chad
      const jogging = t < arrEnd;
      const x = jogging ? lerp(-260, CX, clamp((t - arr) / (arrEnd - arr))) : CX;
      const st = c('straighten');
      const bent = 1 - P(t, st, 0.5);
      const shock = s('c_holy');
      chad(ctx, {
        x, y: GY + 10, t, dir: 1, legs: jogging ? 'jog' : 'stand', jog: t * 13,
        pose: poseTrack(t, [[0, 'jog'], [arrEnd, 'hipsBend'], [c('handUp'), 'handUp'], [st, 'idle'], [wAt('c_sorry', 'that is'), 'explain'], [e('c_sorry') + 0.2, 'idle'],
          [shock, 'shrug'], [s('c_whatdo'), 'explain'], [e('c_whatdo') + 0.2, 'idle'], [s('c_enemies'), 'explain'], [e('c_enemies') + 0.2, 'idle'], [s('c_boundary'), 'heart'],
          [wAt('c_boundary', 'Your power'), 'thumbs'], [wAt('c_boundary', "I'm not"), 'heart']]),
        crouch: jogging ? 0 : 0.7 * bent, slump: jogging ? 0 : bent, headTilt: 0.14 * bent,
        sweat: t < arr ? 0 : t < st ? 1 : 1 - P(t, st, 6, E.lin),
        mood: step(t, [[0, 'tired'], [st, 'smile'], [shock, 'shock'], [shock + 1.1, 'smile'], [s('c_enemies'), 'flat'], [s('c_boundary'), 'calm']]),
        talk: talk('chad', t) || (within(t, c('pant1') - 1.5, c('handUp')) ? 0 : 0),
        look: within(t, s('c_enemies'), e('c_enemies') + 0.4) ? { x: Math.sin((t - s('c_enemies')) * 7), y: 0 } : { x: 1, y: -0.2 },
      });
      if (!jogging && t < st) {
        // panting puffs
        const k = (t * 1.6) % 1;
        ctx.fillStyle = `rgba(255,255,255,${0.7 * (1 - k)})`;
        F.circle(ctx, x + 60 + k * 50, GY - 330 + k * -20, 10 + k * 14); ctx.fill();
      }
    });
    const lv = wAt('g_omega', 'Level sixteen');
    if (t < e('g_omega') + 0.8) A.stamp(ctx, 'OMEGA GOD LEVEL', 430, 130, P(t, wAt('g_omega', 'Omega'), 0.5, E.lin), -0.08, '#ffb13b');
    if (t < e('g_omega') + 0.8) A.stamp(ctx, 'SUPER SAIYAN 16', 470, 270, P(t, lv, 0.5, E.lin), 0.05, '#d6453a');
    flashAt(ctx, t, s('g_omega'), 0.3, '#fff6c0', 0.6);
  };

  SC.pang = (ctx, t, sc) => {
    const pal = mixPal(CP.canyon, CP.canyonGold, P(t, sc.start, sc.end - sc.start, E.lin));
    A.setTint(pal);
    const hp = c('heartPang'), ta = c('turnAway'), wo = c('waveOff'), hz = c('horizon');
    const cShot = { x: 780, y: 660, z: 1.42 };
    let cam = shotCam(t, sc, {
      n_pause: { x: 1240, y: 650, z: 1.85 }, g_wait: { x: 1220, y: 640, z: 1.6 }, c_sohard: cShot, n_scowl: { x: 1250, y: 640, z: 1.95 },
      g_careful: { x: 1180, y: 640, z: 1.45 }, c_gotta: cShot, n_waves: { x: 960, y: 640, z: 1 }, n_horizon: { x: 1480, y: 600, z: 1.25 },
    }, { x: 960, y: 640, z: 1 }, 0.9);
    A.canyon(ctx, t, cam, pal, { peaks: [{ x: 2300 }, { x: -400 }], sunX: 1500 + 200 * P(t, hz, 4), sunY: lerp(190, 470, P(t, sc.start, sc.end - sc.start, E.lin)) });
    world(ctx, cam, () => {
      const sk = wAt('n_scowl', 'shakes');
      const turned = t >= ta;
      const waveL = within(t, wo, wo + 1.6) ? Math.sin((t - wo) * 14) * 26 : 0;
      gokuMeet(ctx, t, {
        dir: turned ? 1 : -1,
        aura: (t < hp ? 0.55 : 0.4 - 0.2 * P(t, hz, 2)) + 0.1 * Math.sin(t * 3),
        pose: poseTrack(t, [[0, 'cross'], [hp, 'heart'], [s('g_wait'), 'idle'], [s('g_careful') - 0.4, 'cross'], [wo, { r: [72, -130], l: [-150 + waveL, -280], rb: -1, lb: -1 }],
          [wo + 1.6, 'cross'], [hz, 'idle']], 0.3),
        mood: step(t, [[0, 'scowl'], [hp, 'wince'], [s('g_wait'), 'shock'], [e('g_wait') + 0.3, 'sad'], [s('c_sohard') + 3, 'flat'], [wAt('n_scowl', 'fades'), 'flat'],
          [wAt('n_scowl', 'jaw'), 'slack'], [sk, 'flat'], [s('g_careful'), 'scowl'], [e('g_careful') + 0.4, 'flat'], [hz, 'sad']]),
        headTilt: within(t, sk, sk + 1.3) ? Math.sin((t - sk) * 16) * 0.13 : 0,
        look: turned ? { x: 1, y: t > hz ? -0.2 : 0 } : { x: 1, y: 0.2 },
      });
      if (within(t, hp, hp + 3)) {
        const k = t - hp;
        A.heartCrack(ctx, GX - 20, GY - 300 - k * 30, 2.6, clamp(k * 3) * (1 - P(t, hp + 2.3, 0.6, E.lin)));
      }
      // Chad
      const jo = wo + 0.7;
      const jog = t >= jo;
      const x = jog ? CX - (t - jo) * 700 : CX;
      if (x > -300) {
        chad(ctx, {
          x, y: GY + 10, t, dir: jog ? -1 : 1, legs: jog ? 'jog' : 'stand', jog: t * 13,
          pose: poseTrack(t, [[0, 'heart'], [s('c_sohard'), 'explain'], [wAt('c_sohard', 'first person'), 'heart'], [wAt('c_sohard', 'because'), 'yellUp'],
            [e('c_sohard') + 0.3, 'idle'], [s('c_gotta'), 'thumbs'], [wAt('c_gotta', "I've"), 'explain'], [e('c_gotta') + 0.2, 'idle'], [jo, 'jog']]),
          mood: step(t, [[0, 'calm'], [s('c_sohard'), 'smile'], [wAt('c_sohard', 'because'), 'happy'], [e('c_sohard') + 0.4, 'smile'], [jo, 'happy']]),
          talk: talk('chad', t), look: { x: 1, y: -0.2 },
        });
      }
    });
  };

  // ================================================================ GOLF
  SC.golf = (ctx, t, sc) => {
    const pal = CP.village;
    A.setTint(pal);
    const pt = c('putt'), bs = c('boomShake'), hpu = c('handPutter'), jo = c('jogOff2');
    let cam = camPath(t, [[sc.start, { x: 900, y: 650, z: 1 }], [bs, { x: 900, y: 650, z: 1.04 }], [s('c_finish') - 0.2, { x: 900, y: 650, z: 1.04 }],
      [s('c_finish') + 0.5, { x: 640, y: 680, z: 1.25 }], [jo, { x: 700, y: 680, z: 1.25 }], [sc.end, { x: 1000, y: 660, z: 1.05 }]]);
    cam = withShake(cam, hitShake(t, [bs], 22, 0.4));
    A.village(ctx, t, cam, pal, { golf: 960, windShake: within(t, bs, bs + 1.2) ? 0.2 : 0, flashes: within(t, bs, bs + 1.5) ? Math.exp(-(t - bs) * 2) : 0, flashX: 1900 });
    const sunk = pt + 1.7;
    const heard = t >= bs + 0.1;
    world(ctx, cam, () => {
      // ball
      if (t < sunk) {
        const k = E.out(clamp((t - pt) / (sunk - pt)));
        F.circle(ctx, lerp(700, 1260, k), lerp(1050, 1010, k), 10); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = A.OUT; ctx.lineWidth = 3; ctx.stroke();
      }
      const cheer = t >= sunk && t < bs;
      const vMood = heard ? (t < s('c_finish') ? 'shock' : 'smile') : cheer ? 'happy' : 'neutral';
      const got = t >= hpu;
      vil(ctx, 0, { x: 300, y: 985, t, dir: 1, mood: vMood, pose: got ? poseTrack(t, [[0, 'explain'], [hpu + 0.4, 'idle']]) : cheer ? PP.yellUp : PP.idle, prop: got ? { r: 'putter' } : null,
        look: heard && t < s('c_finish') ? { x: 1, y: -0.3 } : { x: 1, y: 0.3 } });
      vil(ctx, 2, { x: 1560, y: 960, s: 0.95, t, dir: -1, mood: vMood, pose: cheer ? PP.yellUp : PP.idle, look: heard ? { x: 1, y: -0.3 } : { x: -1, y: 0.3 } });
      const byeA = s('v_bye');
      vil(ctx, 4, { x: 1780, y: 1010, t, dir: -1, mood: t >= byeA ? 'happy' : vMood, talk: talk('villager', t),
        pose: t >= byeA - 0.3 ? poseTrack(t, [[0, 'idle'], [byeA - 0.3, { r: [128 + Math.sin(t * 12) * 20, -380], l: [-72, -135], rb: 1, lb: 1 }]]) : cheer ? PP.yellUp : PP.idle,
        look: heard ? { x: -1, y: 0 } : { x: -1, y: 0.3 } });
      // Chad
      const jog = t >= jo;
      const x = jog ? 600 + (t - jo) * 900 : 600;
      const swing = t < pt ? Math.sin(clamp((t - sc.start - 0.3) / (pt - sc.start - 0.3)) * Math.PI) * -30 : 0;
      const putt = { r: [18 + swing, -150], l: [-6 + swing, -160], rb: -1, lb: 1 };
      chad(ctx, {
        x, y: 1010, t, dir: jog ? 1 : t >= s('c_finish') ? -1 : 1, legs: jog ? 'jog' : 'stand', jog: t * 14,
        pose: poseTrack(t, [[0, putt], [sunk, 'yellUp'], [bs, 'idle'], [s('c_finish') + 0.3, 'explain'], [hpu + 0.2, 'wave'], [jo, 'jog']]),
        prop: t < hpu ? { r: 'putter' } : null,
        mood: step(t, [[0, 'calm'], [sunk, 'happy'], [bs, 'shock'], [s('c_finish'), 'smile']]),
        talk: talk('chad', t), look: heard && t < s('c_finish') ? { x: 1, y: -0.3 } : { x: 0.6, y: t < sunk ? 0.6 : 0 },
      });
    });
  };

  // ================================================================ VOICEMAIL (the universe martial artist)
  SC.voicemail = (ctx, t, sc) => {
    const cut = s('g_wherehe') - 0.4;
    if (t < cut) {
      A.setTint(CP.canyon);
      A.tint.k = 0;
      space(ctx, t);
      const bob = Math.sin(t * 2) * 14;
      const punching = Math.floor(t * 2.5) % 2 === 0;
      ctx.save();
      ctx.translate(W / 2, H / 2 + 60);
      const z = lerp(1.0, 1.15, P(t, sc.start, cut - sc.start, E.lin));
      ctx.scale(z, z);
      alien(ctx, t, { x: 0, y: 300 + bob, s: 1.05, legs: 'fly', dir: 1, aura: 0.8, pose: A.mixPP(PP.power, PP.punch, punching ? 1 : 0.2), mood: 'scowl' });
      ctx.restore();
      caption(ctx, 'A MARTIAL ARTIST', 120, P(t, wAt('n_friend', 'a martial'), 0.4));
      caption(ctx, 'FROM ACROSS THE UNIVERSE', 196, P(t, wAt('n_friend', 'from across'), 0.4));
      A.flash(ctx, 1 - P(t, sc.start, 0.35, E.lin), '#000000');
      return;
    }
    const pal = CP.canyon;
    A.setTint(pal);
    const r1 = c('rumble1'), sm = c('smash1'), b1 = c('boom1'), pd = c('phoneDrop');
    const PX = 2350;
    const hitPeak = sm + 0.9;
    let cam = camPath(t, [[cut, { x: 960, y: 640, z: 1.05 }], [s('c_said'), { x: 900, y: 650, z: 1.15 }], [c('dial') + 0.4, { x: 820, y: 640, z: 1.35 }],
      [r1, { x: 960, y: 640, z: 1.1 }], [sm - 0.05, { x: 980, y: 640, z: 1.15 }], [hitPeak, { x: 1800, y: 560, z: 0.85 }, E.out], [b1, { x: 1820, y: 560, z: 0.82 }],
      [pd - 0.25, { x: 1820, y: 560, z: 0.8 }], [pd + 0.25, { x: 860, y: 650, z: 1.3 }, E.out], [sc.end, { x: 900, y: 650, z: 1.2 }]]);
    const rumble = within(t, r1, sm) ? 2 + 7 * P(t, r1, sm - r1, E.lin) : 0;
    const sh0 = shake(t, rumble), sh1 = hitShake(t, [sm, hitPeak, b1], 30, 0.35);
    cam = withShake(cam, { x: sh0.x + sh1.x, y: sh0.y + sh1.y });
    A.canyon(ctx, t, cam, pal, { peaks: [{ x: PX, gone: P(t, b1 + 0.05, 0.5) }, { x: -500 }], sunX: 1400, sunY: 170 });
    const hit = t >= sm;
    world(ctx, cam, () => {
      if (rumble > 0) A.rocks(ctx, 960, 1000, t, 0.12 * P(t, r1, 1), 8);
      // Goku
      if (!hit) {
        goku(ctx, t, {
          x: 1150, y: GY, s: 1.0, dir: -1, super: 0, aura: 0, blink: blink(t, 4), talk: talk('goku', t),
          pose: poseTrack(t, [[0, 'cross'], [s('g_wherehe'), 'shrug'], [e('g_wherehe') + 0.2, 'cross']]),
          mood: step(t, [[0, 'scowl'], [wAt('n_shake', 'raises'), 'neutral']]), browUp: P(t, wAt('n_shake', 'raises'), 0.3),
          headTilt: within(t, c('tap'), c('tap') + 1.4) ? Math.sin((t - c('tap')) * 12) * 0.05 : 0,
          look: t >= wAt('n_shake', 'raises') ? { x: -0.6, y: -0.5 } : { x: 1, y: 0.2 },
        });
      } else {
        const k = clamp((t - sm) / (hitPeak - sm));
        if (k < 1) {
          const x = lerp(1150, PX - 40, E.in(k) * 0.4 + k * 0.6), y = lerp(GY - 100, 620, k) - Math.sin(k * Math.PI) * 120;
          goku(ctx, t, { x, y, s: 1, dir: -1, legs: 'fly', rot: -(t - sm) * 9, mood: 'shock', pose: PP.shrug, super: 0 });
        } else if (t < b1 + 0.1) {
          // stuck in the mountainside
          goku(ctx, t, { x: PX - 40, y: 640, s: 0.9, dir: -1, legs: 'fly', rot: -0.4, mood: 'slack', pose: PP.yellUp, super: 0 });
          A.dust(ctx, PX - 40, 560, clamp((t - hitPeak) / 1.2), 2);
        }
        A.explosion(ctx, PX - 20, 520, t - b1, 480);
      }
      // the universe martial artist
      const comeIn = sm - 0.35;
      if (t >= comeIn) {
        const k = clamp((t - comeIn) / (sm - comeIn));
        const ax = lerp(-300, 980, E.in(k)), ay = lerp(500, GY - 60, k);
        const settled = P(t, sm + 0.8, 0.8);
        alien(ctx, t, { x: ax, y: lerp(ay, GY - 40, settled) + Math.sin(t * 2) * 8 * settled, s: 1, dir: t >= pd + 0.4 ? -1 : 1, legs: 'fly', aura: 0.6,
          pose: poseTrack(t, [[0, 'punch'], [sm + 1.2, 'power'], [pd + 0.6, { r: [128 + Math.sin(t * 12) * 20, -380], l: [-72, -135], rb: 1, lb: 1 }]]),
          mood: t >= pd + 0.4 ? 'smile' : 'scowl', look: { x: 1, y: 0 } });
      }
      // Chad
      const dropped = t >= pd;
      chad(ctx, {
        x: 720, y: GY + 10, t, dir: 1, talk: talk('chad', t),
        pose: poseTrack(t, [[0, 'idle'], [wAt('c_said', 'Let me'), 'watch'], [c('dial'), 'phone'], [pd, 'idle'], [s('c_friend'), 'thumbs']]),
        prop: !dropped && t >= wAt('c_said', 'Let me') ? { r: 'phone' } : null,
        mood: step(t, [[0, 'flat'], [s('c_said'), 'smile'], [r1 + 0.6, 'flat'], [sm, 'shock'], [pd, 'slack'], [s('c_friend'), 'smile']]),
        look: hit ? { x: 1, y: -0.2 } : t > r1 ? { x: Math.sin(t * 3), y: 0.3 } : { x: 1, y: 0 },
      });
      if (dropped && t < pd + 0.6) {
        const k = (t - pd) / 0.6;
        ctx.save(); ctx.translate(720 + 50 + k * 30, GY - 330 + k * k * 320); ctx.rotate(k * 7);
        F.rrect(ctx, -9, -17, 18, 34, 4); ctx.fillStyle = '#22262e'; ctx.fill(); ctx.strokeStyle = A.OUT; ctx.lineWidth = 3; ctx.stroke();
        ctx.restore();
      }
      const ui0 = c('dial') + 0.1, vm = c('beep') - 0.4;
      const uk = P(t, ui0, 0.3, E.back) * (1 - P(t, e('c_message') + 0.3, 0.3, E.lin));
      if (uk > 0) phoneUI(ctx, 980, 330, t, uk, t >= vm);
    });
    if (within(t, sm - 0.35, sm + 0.3)) A.speedLines(ctx, t, 1, 0);
    flashAt(ctx, t, sm, 0.3);
    flashAt(ctx, t, b1, 0.5, '#fff2c0');
  };

  // ================================================================ DINNER
  SC.dinner = (ctx, t, sc) => {
    const pal = CP.dusk;
    A.setTint(pal);
    const fb1 = c('farBlast1'), fb2 = c('farBlast2'), wl = c('watchLook'), sk = c('skyCut'), fr = c('freeze');
    const wo = c('wideEyes'), cl = c('chadLeaves'), ww = s('g_wherewere'), sm2 = c('smash2'), b2 = c('boom2');
    const PKX = 2000, PKY = 520; // the far mountain (depth 0.35)
    const flyEnd = sm2 + 1.3;
    const fightCam = { x: 960, y: 180, z: 1.5 };
    let cam = camPath(t, [[sc.start, { x: 960, y: 600, z: 1 }], [wl - 0.3, { x: 960, y: 610, z: 1.04 }], [wl + 0.4, { x: 960, y: 660, z: 1.3 }],
      [sk - 0.01, { x: 960, y: 640, z: 1.3 }], [sk, fightCam, E.lin], [s('g_busy') - 0.3, { x: 960, y: 175, z: 1.5 }], [s('g_busy') + 0.5, { x: 960, y: 520, z: 0.95 }],
      [ww - 0.4, { x: 960, y: 520, z: 0.95 }], [ww + 0.2, { x: 1000, y: 230, z: 1.3 }], [sm2, { x: 1000, y: 230, z: 1.3 }], [flyEnd, { x: 2400, y: 400, z: 1.0 }, E.inOut],
      [sc.end, { x: 2420, y: 400, z: 1.04 }]]);
    cam = withShake(cam, hitShake(t, [sm2, b2], 18, 0.35));
    // distant flashes on the horizon while they fight far away
    const blasts = [fb1, fb2, fb1 + 2.1, fb2 + 1.7, fb2 + 2.9];
    let fl = 0;
    for (const b of blasts) if (t >= b && t < sk) fl = Math.max(fl, Math.exp(-(t - b) * 2.2));
    A.village(ctx, t, cam, pal, {
      flashes: fl, flashX: 1500, sunX: 300, sunY: 560,
      far: (fc) => {
        // the mountain Goku is about to fly into
        const gone = P(t, b2 + 0.05, 0.6);
        fc.save(); fc.translate(PKX, 650); fc.scale(1, 1 - gone * 0.75);
        fc.beginPath(); fc.moveTo(-260, 0); fc.lineTo(-120, -170); fc.lineTo(-30, -250); fc.lineTo(40, -200); fc.lineTo(120, -240); fc.lineTo(260, 0); fc.closePath();
        fc.fillStyle = mix(pal.far, '#a06a5a', 0.55); fc.fill();
        fc.restore();
        for (const [i, b] of blasts.entries()) if (t < sk) A.explosion(fc, 1500 + i * 90, 600 - hash(i) * 40, t - b, 60);
        if (t >= flyEnd && t < b2) A.dust(fc, PKX, 520, clamp((t - flyEnd) / 1.4), 1.2);
        A.explosion(fc, PKX, PKY + 20, t - b2, 320);
      },
    });
    const frozen = t >= fr;
    const tf = frozen ? fr : t; // their animation clock stops when they freeze
    world(ctx, cam, () => {
      // the fight overhead (from the sky cut on)
      if (t >= sk) {
        const bob = Math.sin(tf * 3) * 10;
        const jab = Math.floor(tf * 5) % 2 === 0;
        const gPose = frozen ? PP.punch : jab ? PP.punch : PP.power;
        const aPose = frozen ? PP.punch : jab ? PP.power : PP.punch;
        const flying = t >= sm2;
        const busy = s('g_busy');
        if (!flying) {
          goku(ctx, tf, { x: 830, y: 330 + bob, s: 0.62, dir: 1, legs: 'fly', super: 1, level: 1, aura: 0.7, sparks: frozen ? 0 : 0.5, talk: talk('goku', t),
            pose: t < busy ? gPose : poseTrack(t, [[0, PP.punch], [busy, 'explain'], [e('g_busy') + 0.2, 'punch'], [s('g_okay'), 'handUp'], [ww, 'punch']]),
            mood: step(t, [[0, 'yell'], [fr, 'scowl'], [busy, 'scowl'], [wo, 'shock'], [s('g_okay'), 'yell'], [e('g_okay') + 0.2, 'flat'], [ww, 'scowl']]),
            look: within(t, busy - 0.2, ww) ? { x: 0.4, y: 1 } : { x: 1, y: 0 } });
        }
        const pk = flying ? E.out(clamp((t - sm2) / 0.18)) : 0;
        alien(ctx, tf, { x: 1075 - pk * 60, y: 330 - bob, s: 0.62, dir: -1, legs: 'fly', aura: 0.6, pose: flying ? PP.punch : aPose,
          mood: within(t, wo, ww) ? 'shock' : 'scowl', look: within(t, s('g_busy'), ww) ? { x: -0.3, y: 1 } : { x: 1, y: 0 } });
        if (!frozen) {
          for (let i = 0; i < 3; i++) if (hash(Math.floor(t * 6) + i) > 0.6) A.sparkle(ctx, 950 + (hash(i + Math.floor(t * 6)) - 0.5) * 80, 260 + (hash(i * 3 + Math.floor(t * 6)) - 0.5) * 80, 1.2, 0.9, t * 6);
        }
      }
      // Chad on the ground
      const walk = t >= cl;
      const x = walk ? 960 - (t - cl) * 420 : 960;
      if (x > -300) {
        chad(ctx, {
          x, y: 990, t, dir: walk ? -1 : 1, legs: walk ? 'jog' : 'stand', jog: t * 10, talk: talk('chad', t),
          pose: poseTrack(t, [[0, 'idle'], [wl, 'watch'], [wAt('n_watch', 'He yells'), 'cup'], [e('c_dinner') + 0.3, 'idle'], [s('c_casserole'), 'shrug'], [e('c_casserole'), 'idle'], [cl, 'jog']]),
          prop: within(t, wl - 0.2, wAt('n_watch', 'He yells')) ? { r: 'watch' } : null,
          mood: step(t, [[0, 'calm'], [wl, 'flat'], [s('c_dinner'), 'yell'], [e('c_dinner') + 0.2, 'smile'], [s('c_casserole'), 'smile'], [cl, 'happy']]),
          look: within(t, wl, wAt('n_watch', 'He yells')) ? { x: 0.3, y: 1 } : t >= wAt('n_watch', 'He yells') && t < cl ? { x: 0, y: -1 } : { x: 0.5, y: 0 },
        });
      }
    });
    // Goku launched into the distance (screen space so he can shrink toward the far mountain)
    if (t >= sm2 && t < flyEnd) {
      const k = clamp((t - sm2) / (flyEnd - sm2));
      const a = toScreen(cam, 830, 330), b = toScreen(cam, PKX, PKY, 0.35);
      const sx = lerp(a.x, b.x, E.in(k) * 0.3 + k * 0.7), sy = lerp(a.y, b.y, k) - Math.sin(k * Math.PI) * 120;
      ctx.save();
      ctx.translate(sx, sy);
      const scl = lerp(0.62 * a.z, 0.12, E.out(k));
      goku(ctx, t, { x: 0, y: 0, s: scl, dir: 1, legs: 'fly', rot: (t - sm2) * 11, mood: 'shock', pose: PP.shrug, super: 1, level: 1 });
      ctx.restore();
    }
    if (within(t, sm2 - 0.1, sm2 + 0.5)) A.speedLines(ctx, t, 1, 0);
    flashAt(ctx, t, sk, 0.2);
    flashAt(ctx, t, sm2, 0.3);
    flashAt(ctx, t, b2, 0.5, '#fff2c0', 0.8);
    if (within(t, fr, fr + 0.25)) A.flash(ctx, 0.25 * (1 - (t - fr) / 0.25), '#9fd8ff');
  };

  // ================================================================ END
  SC.end = (ctx, t, sc) => {
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    const k = P(t, c('endBoom'), 1.0) * (1 - P(t, sc.end - 1.2, 1.1, E.lin));
    const z = lerp(0.92, 1, P(t, c('endBoom'), 4, E.out));
    ctx.save();
    ctx.translate(W / 2, H / 2 - 40);
    ctx.scale(z, z);
    text(ctx, 'EMOTIONAL', 0, -80, { size: 130, font: FONT_TITLE, weight: 400, fill: '#9fd8ff', alpha: k, ls: 8 });
    text(ctx, 'CHAD', 0, 70, { size: 190, font: FONT_TITLE, weight: 400, fill: '#f3e6c8', alpha: k, ls: 10 });
    ctx.restore();
    text(ctx, TL.subtitle, W / 2, H / 2 + 170, { size: 44, weight: 500, fill: '#bfae8e', alpha: k * P(t, c('endBoom') + 0.8, 1) });
  };

  window.SCENES = SC;
})();
