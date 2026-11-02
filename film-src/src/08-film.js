// ============================================================================
//  FILM — "The Last Thing on My Mind"
//  A deathbed staged as the last night of a 99-year run. Everything on screen
//  and in the score is a pure function of time t.
// ============================================================================
const Film = (() => {
  // ------------------------------------------------------------------ timeline
  const DUR = { P: 10, S1: 18, S2: 22, S3: 16, S4: 33, S5: 32.5, S6: 36, S7: 37, S8: 47, S9: 36.5, S10: 46.5 };
  const T = {}; let total = 0;
  for (const k of Object.keys(DUR)) { T[k] = total; total += DUR[k]; }
  const at = (s, lt) => T[s] + lt;
  const local = (s, t) => t - T[s];
  const ACTS = {
    P: ['Prologue', 'The Ghost Light'], S1: ['Act I', 'Ninety-Nine Years'], S2: ['Act II', 'Nobody Is Immortal'], S3: ['Act III', 'The Family Gathers'],
    S4: ['Act IV', 'Hands'], S5: ['Act V', 'The Last Thing on My Mind'], S6: ['Act VI', 'Get the Hook'], S7: ['Act VII', 'Death Waits Outside'],
    S8: ['Act VIII', 'The Ship'], S9: ['Act IX', 'One'], S10: ['Finale', 'The Curtain'],
  };
  const chapters = Object.keys(DUR).map(k => ({ title: ACTS[k][1], act: ACTS[k][0], start: T[k] }));

  // ------------------------------------------------------------------ narration (the author's words)
  const N = (s, lt, text, cls, d) => ({ t: at(s, lt), text, cls, d });
  const narration = [
    N('S1', 1.4, 'So I think about having spent / ninety-nine years on the Earth.'),
    N('S1', 7.9, 'Now I\u2019m on my deathbed. I can\u2019t move much.'),
    N('S1', 13.25, 'And I feel the grim reaper approaching.'),
    N('S2', 1.0, 'Life comes to an end for all of us.'),
    N('S2', 5.9, 'We cannot stop that time from coming.'),
    N('S2', 10.95, 'We are not immortal, as far as I\u2019m aware.'),
    N('S2', 16.25, 'So I think about all the time I spent / nurturing and caring for my emotional needs\u2014'),
    N('S3', 2.0, 'an emotional family, personified\u2014'),
    N('S3', 6.8, 'the health and well-being of my brain and body.'),
    N('S3', 12.45, 'In my mind\u2019s eye, I see them.'),
    N('S4', 1.0, 'Their hands on my shoulders. My arms. My legs.'),
    N('S4', 6.8, 'They run their hands through what hair I have left.'),
    N('S4', 12.8, 'With love and care, a knowing look: / I cared for them while I could care for them.'),
    N('S4', 20.5, 'I protected them while I could protect them.'),
    N('S4', 25.95, 'Now that I can\u2019t protect them all that much anymore, / they still want to protect me.'),
    N('S5', 0.8, 'They are going to care for me in my last moments.'),
    N('S5', 6.55, 'Instead of the reaper, / they are the first thing on my mind\u2014'),
    N('S5', 12.9, 'them, and the love I sought to cultivate / for humanity as a whole,'),
    N('S5', 19.6, 'and my own life, / as the curtain to the show of life closes.'),
    N('S5', 25.95, 'The reaper was the last thing on my mind / while I was with them.'),
    N('S6', 0.25, 'The closer I am to death / doesn\u2019t mean I let death take me.'),
    N('S6', 6.55, 'It means the harder I hold on / to all the love that was grown in the garden of life.'),
    N('S6', 14.35, 'Because I don\u2019t want to lose it\u2014 / when I die, this experience I had living in the universe dies.'),
    N('S6', 22.85, 'So the reaper is going to have to / drag my ass out of there\u2014'),
    N('S6', 29.6, 'and I\u2019m not going to go easy. \uD83D\uDE09', null, 5.2),
    N('S7', 0.25, 'You might say I fear death\u2014 / but it doesn\u2019t control my life.'),
    N('S7', 6.6, 'I don\u2019t want to run away and hide. / I want to run to my emotional family,'),
    N('S7', 13.75, 'to hug them, and tell them before death gets here: / I am here for you.'),
    N('S7', 20.7, 'You will be in my heart forever, not death.'),
    N('S7', 26.15, 'Death is on the outside.'),
    N('S7', 30.4, 'Even if death comes, I am here for you\u2014 / right now, and forever, until my last breath.'),
    N('S8', 1.5, 'In my daily life, I see their emotional needs, / and I speak with them as a human\u2014'),
    N('S8', 9.1, 'because I am human, / and they are a part of our shared humanity.'),
    N('S8', 15.7, 'I treat them with a kind of prohuman / introspective respect.'),
    N('S8', 22.05, 'They deserve all the respect I deserve. / Because they are me.'),
    N('S8', 28.45, 'They help me navigate the world / toward more well-being, less suffering.'),
    N('S8', 35.55, 'Through the ebbs and flows of life, / they are in the ship with me.'),
    N('S8', 42.25, 'I carry them as they carry me.'),
    N('S9', 0.25, 'They hug me, and they close their eyes. / I close my eyes. We hug each other closer.'),
    N('S9', 7.97, 'I feel at one with them, and they with me\u2014 / because they were me the whole time.'),
    N('S9', 15.51, 'They were with me the whole time, / and I was with them the whole time.'),
    N('S9', 22.45, 'Unity isn\u2019t to silence or dismiss my emotions. / It\u2019s the culmination of all my life with them,'),
    N('S9', 30.85, 'because they were my life\u2014 / because they were me.'),
    N('S10', 0.2, 'I want to hold them, and I need them to hold me too, / so I can feel safer in this world.'),
    N('S10', 8.25, 'We were together from the day we were born, / and we will be together until the end.'),
    N('S10', 16.0, 'When they die, I die.'),
    N('S10', 21.15, 'But when I live for them, I live for myself.'),
    N('S10', 26.7, 'And when they live for me, I feel love\u2014'),
    N('S10', 31.96, 'and I want to love them.', null, 6),
  ];
  // never let two lines share the screen: a line yields to the next
  narration.forEach((n, i) => {
    const hold = n.d ?? Math.max(3, 2.5 + n.text.replace(/ \/ /g, ' ').length * 0.06);
    const next = narration[i + 1];
    n.d = next ? Math.min(hold, next.t - n.t - 0.3) : hold;
  });

  // ------------------------------------------------------------------ cast: the emotional family
  // Each is defined by the part of brain and body they keep well, a hue, and a motion signature.
  const FAM = [
    { id: 'hearth', name: 'Hearth', role: 'heart and blood', c: hexRgb('#F0874A'), hair: 'bun', h: 372, x: -158, y: 190, kneel: 0.12, lean: -0.3, tilt: -0.3, face: -1, enter: 0.5, touch: [['shoulder', 12, -3], ['chest', 6, -5]], note: 50, zone: 'heart' },
    { id: 'tidewell', name: 'Tidewell', role: 'breath and lungs', c: hexRgb('#9ED8CE'), hair: 'veil', h: 452, x: 26, y: 190, kneel: 0, lean: -0.34, tilt: -0.3, face: -1, enter: 2.7, touch: [['arm', 6, -3], ['hand', 10, -6]], note: 57, zone: 'chest' },
    { id: 'loom', name: 'Loom', role: 'mind and memory', c: hexRgb('#EDC56A'), hair: 'long', h: 412, x: -470, y: 190, kneel: 0.35, lean: 0.62, tilt: 0.45, face: 1, enter: 4.9, touch: [['crown', 0, -4], ['brow', 2, -5]], note: 66, zone: 'brow' },
    { id: 'mender', name: 'Mender', role: 'repair and rest', c: hexRgb('#E39AAE'), hair: 'curls', h: 312, x: 204, y: 44, kneel: 1, lean: -0.32, tilt: -0.25, face: -1, enter: 7.1, touch: [['knee', -6, -3], ['shin', 4, -3]], note: 59, zone: 'gut' },
    { id: 'keel', name: 'Keel', role: 'spine and balance', c: hexRgb('#CDB78F'), hair: 'short', h: 432, x: -332, y: 190, kneel: 0, lean: 0.3, tilt: 0.22, face: 1, enter: 9.3, touch: [['shoulder', -10, -3], ['shoulder', -30, -3]], note: 38, zone: 'spine' },
    { id: 'kindle', name: 'Kindle', role: 'senses and wonder', c: hexRgb('#FFF0C8'), hair: 'tuft', h: 272, x: -34, y: 176, kneel: 0, lean: -0.14, tilt: -0.42, face: -1, enter: 11.5, touch: [['hand', 14, 9], ['hand', -2, 7]], note: 76, zone: 'hand', front: true },
  ];
  const HUES = FAM.map(f => f.c);
  Env.makePlants(HUES);
  // where they gather to meet his running spirit (front floor, candle side)
  const GROUP = { hearth: [-470, 238], tidewell: [-680, 228], loom: [-620, 232], mender: [-450, 248], keel: [-720, 228], kindle: [-545, 262] };

  // ------------------------------------------------------------------ key times
  const TUGS = [at('S6', 24.55), at('S6', 25.65), at('S6', 26.95)];
  const SLIP = at('S6', 27.85);
  const FREEZE = [at('S6', 28.9), at('S6', 29.5)];
  const WINK = at('S6', 31.0);
  const SEA_IN = [at('S8', 28.1), at('S8', 30.5)], SEA_OUT = [at('S8', 45.1), at('S8', 47.0)];
  const MERGE = [at('S9', 8.0), at('S9', 13.2)];
  const REFORM = [at('S10', 0.2), at('S10', 4.5)];
  const DIE = [at('S10', 16.0), at('S10', 21.15)];
  const CURTAIN = [at('S10', 31.96), at('S10', 36.76)];

  // ------------------------------------------------------------------ breath & heart (shared by picture and sound)
  const breathPeriod = t => t < T.S9 ? lerp(5.5, 7, clamp((t - T.S1) / (T.S9 - T.S1))) : 7.2;
  const BREATHS = [];
  const addBreaths = (t0, t1) => Score.breaths(t0, t1, breathPeriod, 0.035).filter(e => e.a[1] === true).forEach(e => BREATHS.push({ t: e.t, P: e.a[0] / 0.42 }));
  addBreaths(at('S1', 2), DIE[0] - 1.5);          // ...until "When they die, I die": he holds still
  BREATHS.push({ t: DIE[1] + 0.1, P: 6.2, big: true });   // "But when I live for them": one big breath
  addBreaths(DIE[1] + 6.4, CURTAIN[0] - 7.2);
  BREATHS.push({ t: CURTAIN[0], P: 5.4, big: true });     // one long, slow breath as the curtain closes
  addBreaths(CURTAIN[0] + 5.6, total - 4);
  BREATHS.sort((a, b) => a.t - b.t);
  function breathAt(t) {
    let lo = 0, hi = BREATHS.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (BREATHS[m].t <= t) { k = m; lo = m + 1; } else hi = m - 1; }
    if (k < 0) return 0;
    const b = BREATHS[k], u = (t - b.t) / b.P;
    if (u > 1) return 0;
    const amp = b.big ? 1.5 : 1;
    return (u < 0.42 ? smooth(u / 0.42) : 1 - smooth((u - 0.42) / 0.58)) * amp;
  }
  const heartBpm = t => t < T.S4 ? 52 : t < T.S6 + 22 ? 48 : t < T.S7 ? 62 : t < T.S8 ? 66 : t < T.S10 ? 48 : 46;
  const HEARTS = [];
  for (let t = at('S1', 1.5); t < DIE[0];) { HEARTS.push(t); t += 60 / heartBpm(t); }
  HEARTS.push(at('S10', 19.95));                   // one faint flicker in the dark
  for (let t = DIE[1] + 0.1; t < CURTAIN[1];) { HEARTS.push(t); t += 60 / 52; }
  [0.1, 0.75, 1.4].forEach(d => HEARTS.push(CURTAIN[1] + d));   // the seam of light pulses three times
  HEARTS.sort((a, b) => a - b);
  function pulseAt(t) {
    let lo = 0, hi = HEARTS.length - 1, k = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (HEARTS[m] <= t) { k = m; lo = m + 1; } else hi = m - 1; }
    if (k < 0) return 0;
    const d = t - HEARTS[k];
    return Math.exp(-d * 9) + (d > 0.24 ? 0.6 * Math.exp(-(d - 0.24) * 9) : 0);
  }

  // ------------------------------------------------------------------ camera
  const SH = {
    theatre: { cx: 0, cy: -232, w: 2080, pw: 0.86, ph: 1.1, pcy: -220 },
    wide: { cx: 0, cy: -178, w: 1560 },
    room: { cx: -40, cy: -160, w: 1360 },
    med: { cx: -70, cy: -130, w: 1080 },
    mcu: { cx: -200, cy: -110, w: 640 },
    head: { cx: -258, cy: -78, w: 380 },
    hand: { cx: -84, cy: -72, w: 330 },
    win: { cx: 182, cy: -388, w: 600 },
    wall: { cx: -300, cy: -250, w: 1180 },
    front: { cx: -330, cy: -60, w: 1440 },
    chest: { cx: -195, cy: -92, w: 600 },
    gag: { cx: 92, cy: -150, w: 1420 },
  };
  const S_ = (k, o = {}) => Object.assign({}, SH[k], o);
  const CAM = [
    [0, SH.theatre], [at('P', 7.8), SH.theatre], [at('S1', 3), S_('wide', { w: 1640, cy: -190 })], [at('S1', 18), S_('room', { cx: -30, cy: -165, w: 1380 })],
    [at('S2', 4), { cx: 60, cy: -235, w: 1180 }], [at('S2', 16), { cx: 40, cy: -215, w: 1160 }], [at('S2', 22), SH.mcu],
    [at('S3', 1), SH.mcu], [at('S3', 14), S_('room', { w: 1240, cy: -150 })],
    [at('S4', 6.8), S_('room', { w: 1240, cy: -150 })], [at('S4', 8.0), S_('head', { cx: -262, cy: -100, w: 460 })], [at('S4', 12.4), S_('head', { cx: -262, cy: -100, w: 460 })],
    [at('S4', 13.6), S_('mcu', { cx: -235, w: 720 })], [at('S4', 18.6), S_('mcu', { cx: -235, w: 720 })],
    [at('S4', 20.2), S_('wall', { cx: -270, cy: -230, w: 1020 })], [at('S4', 24.6), S_('wall', { cx: -270, cy: -230, w: 1020 })],
    [at('S4', 26.2), S_('hand', { w: 440, cy: -88 })], [at('S4', 32.8), S_('hand', { w: 410, cy: -86 })],
    [at('S5', 3), S_('med', { w: 1160 })], [at('S5', 12.9), S_('med', { w: 1160 })], [at('S5', 15.3), S_('wall', { cx: -230, cy: -250, w: 1300 })],
    [at('S5', 25.95), S_('wall', { cx: -230, cy: -250, w: 1300 })], [at('S5', 32), S_('med', { cx: -150, w: 940 })],
    [at('S6', 1), S_('room', { w: 1320 })], [at('S6', 6.2), S_('room', { w: 1320 })], [at('S6', 13.6), S_('med', { w: 1150 })],
    [at('S6', 16.2), S_('room', { cx: -40, cy: -300, w: 1460 })], [at('S6', 20.8), S_('room', { cx: -40, cy: -300, w: 1460 })],
    [at('S6', 22.2), { cx: 190, cy: -115, w: 1110 }], [at('S6', 22.6), { cx: 200, cy: -110, w: 1060 }], [at('S6', 29.5), { cx: 200, cy: -110, w: 1060 }],
    [at('S6', 29.534), S_('head', { cx: -250, cy: -84, w: 300 }), 'linear'], [at('S6', 32.4), S_('head', { cx: -250, cy: -82, w: 320 })],
    [at('S6', 32.434), { cx: 120, cy: -130, w: 1200 }, 'linear'], [at('S6', 36), { cx: 90, cy: -140, w: 1240 }],
    [at('S7', 2.5), S_('mcu', { w: 760 })], [at('S7', 7.5), S_('front', { cx: -300, cy: -50, w: 1020 })], [at('S7', 13.0), S_('front', { cx: -320, cy: -45, w: 1000 })],
    [at('S7', 26.15), S_('front', { cx: -320, cy: -45, w: 980 })], [at('S7', 26.184), SH.win, 'linear'], [at('S7', 30.2), S_('win', { w: 640 })],
    [at('S7', 30.234), S_('front', { cx: -320, cy: -45, w: 1000 }), 'linear'], [at('S7', 32.4), S_('front', { cx: -300, cy: -50, w: 1040 })], [at('S7', 36.5), S_('med', { w: 1120 })],
    [at('S8', 1), S_('wall', { cx: -330, cy: -230, w: 1250 })], [at('S8', 11), S_('wall', { cx: -290, cy: -230, w: 1250 })],
    [at('S8', 28), S_('wall', { cx: -290, cy: -230, w: 1250 })], [at('S8', 45.5), S_('med', { w: 1100 })],
    [at('S9', 1), S_('med', { w: 1060 })], [at('S9', 15), S_('med', { w: 1060 })], [at('S9', 16.4), S_('wall', { cx: -300, cy: -300, w: 1180 })],
    [at('S9', 33), S_('wall', { cx: -300, cy: -300, w: 1180 })], [at('S9', 36.3), S_('chest', { w: 760 })],
    [at('S10', 6), S_('med', { w: 1000, cy: -150 })], [at('S10', 8.6), S_('wall', { cx: -230, cy: -230, w: 1180 })],
    [at('S10', 15.4), S_('wall', { cx: -230, cy: -230, w: 1180 })], [at('S10', 16.6), S_('med', { w: 1020, cy: -140 })],
    [at('S10', 26.7), S_('med', { w: 1060, cy: -150 })], [at('S10', 29.6), S_('theatre', { cx: 40 })], [total, S_('theatre', { cx: 40 })],
  ];
  const shake = t => {
    let s = 0;
    TUGS.forEach((tt, i) => { const d = t - tt; if (d > 0 && d < 1.0) s += Math.exp(-d * 6) * (3 + i * 2.5); });
    const storm = env(t, at('S8', 35.2), at('S8', 36.3), at('S8', 38.6), at('S8', 39.8));
    return s + storm * 1.2;
  };

  // ------------------------------------------------------------------ tracks
  const tr = {
    black: K([[0, 1], [0.5, 0], [at('S10', 44.9), 0], [at('S10', 46.4), 1]]),
    stageDark: K([[0, 0], [at('P', 3.3), 0], [at('P', 3.4), 0.94], [at('P', 4.4), 0.94], [at('P', 4.5), 0.3], [at('P', 4.58), 0.55], [at('P', 4.7), 0.15], [at('P', 4.8), 0.0]]),
    ghost: K([[0, 1], [at('P', 3.3), 1], [at('P', 3.36), 0.12], [at('P', 4.4), 0], [at('S10', 40.45), 0], [at('S10', 40.55), 1]]),
    trav: K([[0, 1], [at('P', 4.6), 1], [at('P', 7.8), 0], [at('S5', 19.6), 0], [at('S5', 23.1), 0.13], [at('S6', 0.5), 0.13], [at('S6', 4), 0.22], [at('S6', 34.2), 0.22], [at('S6', 35.6), 0.04], [at('S10', 31.96), 0.04], [at('S10', 36.76), 1, 'sine']]),
    spot: K([[0, 0], [at('P', 4.4), 0], [at('P', 4.5), 0.7], [at('P', 4.58), 0.45], [at('P', 4.7), 0.85], [at('P', 4.8), 1], [at('S6', 14.6), 1], [at('S6', 16.4), 0.7], [at('S6', 21.6), 0.7], [at('S6', 22.4), 1], [at('S8', 0), 1], [at('S8', 2), 0.6], [at('S8', 45.1), 0.6], [at('S8', 47.0), 1], [at('S10', 16.0), 1], [at('S10', 16.7), 0.4], [at('S10', 21.05), 0.4], [at('S10', 21.45), 1.1], [at('S10', 36.76), 1.1], [at('S10', 38.2), 0.2]]),
    foot: t => env(t, at('S6', 22.4), at('S6', 23.1), at('S6', 34.8), at('S6', 35.8)) + env(t, at('S10', 31.2), at('S10', 33.2), at('S10', 47), at('S10', 49)) * 0.6 + env(t, 0, 0.5, at('P', 3.3), at('P', 3.36)) * 0.4,
    house: K([[0, 1], [at('P', 9), 1], [at('S1', 5), 0], [at('S10', 28.2), 0], [at('S10', 31.0), 1]]),
    houseGlow: K([[at('S10', 26.7), 0], [at('S10', 29.2), 1], [at('S10', 38.2), 1], [at('S10', 42.2), 0.4]]),
    moon: K([[0, 0.7], [at('S2', 0), 0.85], [at('S2', 6), 1], [at('S3', 2), 1], [at('S3', 14), 0.5], [at('S5', 6.55), 0.5], [at('S5', 8.55), 0.3], [at('S6', 14.6), 0.3], [at('S6', 16.4), 0.6], [at('S6', 21.6), 0.5], [at('S6', 36), 0.4], [at('S10', 31.96), 0.4], [at('S10', 36.76), 0.1]]),
    candle: K([[at('S1', 3), 0], [at('S1', 8), 0.68], [at('S2', 0), 0.68], [at('S2', 6), 0.48], [at('S2', 16), 0.5], [at('S2', 21), 1.0], [at('S9', 8), 1.0], [at('S9', 10.2), 1.15], [at('S10', 16.0), 1.05], [at('S10', 16.7), 0.45], [at('S10', 21.05), 0.45], [at('S10', 21.45), 1.1]]),
    candleLean: K([[at('S2', 0), 0], [at('S2', 6), 0.21], [at('S2', 16), 0.21], [at('S2', 19), 0], [at('S6', 24.0), 0], [at('S6', 24.6), 0.15], [SLIP, 0.15], [SLIP + 0.75, 0]]),
    wax: K([[0, 1], [total, 0.5, 'linear']]),
    warm: K([[at('S1', 3), 0], [at('S1', 8), 0.18], [at('S2', 16), 0.18], [at('S2', 22), 0.34], [at('S3', 14), 0.82], [at('S6', 24.2), 0.82], [at('S6', 24.6), 0.95], [at('S6', 28.6), 0.85], [at('S6', 29.45), 0.85], [at('S6', 29.55), 0.45], [at('S6', 32.35), 0.45], [at('S6', 32.45), 0.85], [at('S9', 8), 0.9], [at('S9', 10.2), 1.15], [at('S9', 16), 1.0], [at('S10', 16.0), 1.0], [at('S10', 16.7), 0.35], [at('S10', 21.05), 0.35], [at('S10', 21.45), 1.1], [at('S10', 26.7), 1.1], [at('S10', 29.2), 1.2]]),
    farBlur: K([[at('S1', 0), 1.5], [at('S1', 8), 0], [at('S5', 6.55), 0], [at('S5', 8.55), 14], [at('S5', 32.5), 14], [at('S6', 14.6), 0], [at('S9', 2), 0], [at('S9', 10), 2], [at('S10', 6), 2], [at('S10', 9), 1.5], [at('S10', 26.7), 1.5], [at('S10', 31.96), 0]]),
    nearBlur: K([[at('S2', 6), 0], [at('S2', 7.2), 6], [at('S2', 11), 6], [at('S2', 12.5), 0], [at('S7', 26.15), 0], [at('S7', 26.18), 6], [at('S7', 30.2), 6], [at('S7', 30.23), 0]]),
    // death
    shadow: K([[at('S1', 11), 0], [at('S1', 16), 1], [at('S2', 2), 1], [at('S2', 6), 0]]),
    rise: K([[at('S2', 0), 0], [at('S2', 6), 1]]),
    rA: K([[at('S2', 0), 0.0], [at('S2', 1), 1], [at('S3', 2), 1], [at('S3', 14), 0.6], [at('S5', 25.95), 0.6], [at('S5', 32.5), 0.22], [at('S6', 10), 0.22], [at('S6', 18), 0.75], [at('S6', 20.6), 0], [at('S7', 25), 0], [at('S7', 26.0), 0.9], [at('S7', 33), 0.9], [at('S8', 2), 0], [at('S9', 14), 0], [at('S9', 17), 0.5], [at('S10', 24.2), 0.45], [at('S10', 26.7), 0]]),
    rScale: K([[at('S5', 25.95), 1], [at('S5', 32.5), 0.55], [at('S6', 10), 0.55], [at('S6', 18), 1]]),
    rBow: K([[at('S9', 18), 0], [at('S9', 23), 1]]),
    palm: K([[at('S7', 26.6), 0], [at('S7', 27.6), 1], [at('S7', 29.6), 1], [at('S7', 30.6), 0]]),
    frost: K([[at('S7', 26.15), 0], [at('S7', 28.6), 1], [at('S8', 6), 0.4], [at('S9', 0), 0.2]]),
    door: K([[0, 0.18], [at('S6', 21.6), 0.18], [at('S6', 22.6), 0.72], [at('S7', 0.5), 0.72], [at('S7', 3), 0.18]]),
    doorR: K([[at('S6', 21.6), 0], [at('S6', 22.6), 1], [at('S7', 0.5), 1], [at('S7', 2.6), 0]]),
    hookOut: K([[at('S6', 23.15), 0], [at('S6', 24.05), 1, 'out'], [SLIP, 1], [SLIP + 0.35, 0, 'in']]),
    reachW: K([[at('S6', 22.9), 0.55], [at('S6', 23.15), 1, 'out'], [SLIP + 0.35, 1], [SLIP + 1.0, 0.55]]),
    askew: K([[SLIP, 0], [SLIP + 0.25, 1], [at('S6', 33.4), 1], [at('S6', 34.0), 0]]),
    shrug: t => env(t, at('S6', 34.0), at('S6', 34.35), at('S6', 34.5), at('S6', 35.0)),
    lean: K([[at('S6', 35.0), 0], [at('S6', 35.8), 1]]),
    wingR: K([[at('S10', 25.7), 0], [at('S10', 27.7), 1], [at('S10', 40.55), 1], [at('S10', 42.2), 0]]),
    wingBow: t => env(t, at('S10', 30.1), at('S10', 30.8), at('S10', 30.9), at('S10', 31.5)),
    // the man
    eyes: K([[at('S2', 11), 0], [at('S2', 12.5), 0.55], [at('S2', 17), 0.55], [at('S2', 19), 0.25], [at('S4', 6.8), 0.25], [at('S4', 9), 0], [at('S6', 15.2), 0], [at('S6', 15.8), 0.55], [at('S6', 21), 0.7], [at('S6', 29.5), 0.95], [at('S6', 32.4), 0.95], [at('S6', 33.4), 0.35], [at('S9', 0), 0.45], [at('S9', 4.5), 0.45], [at('S9', 5.3), 0], [at('S10', 0.2), 0], [at('S10', 0.7), 0.45], [at('S10', 26.7), 0.45], [at('S10', 27.5), 0.8]]),
    gaze: K([[at('S2', 11), 0], [at('S2', 13), 1]]),
    smile: K([[0, 0.05], [at('S4', 12.8), 0.05], [at('S4', 15), 0.3], [at('S5', 25.95), 0.3], [at('S5', 28), 0.7], [at('S6', 23.4), 0.2], [at('S6', 26.95), 0], [WINK - 0.2, 0.1], [WINK + 0.15, 1, 'out'], [at('S6', 34), 0.7], [at('S9', 6), 0.5], [at('S10', 16.0), 0.5], [at('S10', 16.7), 0.15], [at('S10', 21.45), 0.5], [at('S10', 26.7), 0.6], [at('S10', 28.2), 0.95]]),
    turn: K([[at('S6', 29.5), 0], [at('S6', 30.0), 0.22], [at('S6', 32.0), 0.22], [at('S6', 32.4), 0]]),
    glint: t => env(t, WINK + 0.1, WINK + 0.3, WINK + 0.35, WINK + 0.7),
    breathAmp: K([[0, 1], [at('S2', 11), 1], [at('S2', 13), 0.66], [at('S3', 6), 0.66], [at('S3', 12), 1]]),
    curl: K([[at('S4', 26.2), 0], [at('S4', 28.3), 0.25], [at('S4', 30.8), 0.75], [at('S5', 4), 0.4], [at('S6', 24.0), 0.4], [at('S6', 24.6), 0.95], [at('S6', 28.6), 0.95], [at('S6', 30.6), 0.35], [at('S10', 1), 0.35], [at('S10', 3.4), 0.75]]),
    lift: K([[at('S1', 8), 0], [at('S1', 8.6), 1], [at('S1', 9.6), 1], [at('S1', 10.6), 0], [at('S10', 0.8), 0], [at('S10', 3.4), 0.7], [at('S10', 16.0), 0.7], [at('S10', 16.7), 0.2], [at('S10', 21.45), 0.7]]),
    inner: K([[at('S7', 34), 0], [at('S7', 36.5), 0.22], [at('S9', 8), 0.22], [at('S9', 10.2), 0.85], [at('S10', 2), 0.55], [at('S10', 16.0), 0.55], [at('S10', 16.7), 0.1], [at('S10', 21.05), 0.1], [at('S10', 21.45), 0.7], [at('S10', 26.7), 0.7], [at('S10', 29.2), 0.85]]),
    tug: t => { let v = 0; TUGS.forEach((tt, i) => { const d = t - tt; if (d > 0) v += d < 0.3 ? smooth(d / 0.3) * (0.1 + i * 0.06) : (0.1 + i * 0.06) * Math.exp(-(d - 0.3) * 1.2); }); return v * (1 - range(SLIP, SLIP + 0.4, t)); },
    // the bed itself slides toward the door, and snaps back
    bedShift: t => {
      let v = 0;
      const pulse = (tt, amt, back) => { const d = t - tt; if (d <= 0) return 0; return d < 0.25 ? amt * smooth(d / 0.25) : d < 0.6 ? lerp(amt, back, smooth((d - 0.25) / 0.35)) : back * Math.exp(-(d - 0.6) * 3); };
      v += pulse(TUGS[0], 32, 0); v += pulse(TUGS[1], 50, -10); v += pulse(TUGS[2], 8, 0);
      return v;
    },
    // his spirit (Act VII)
    spiritA: K([[at('S7', 6.6), 0], [at('S7', 8.1), 1], [at('S7', 33.4), 1], [at('S7', 36.4), 0]]),
    spiritX: K([[at('S7', 6.6), -150], [at('S7', 8.3), 70, 'inOut'], [at('S7', 8.9), 70], [at('S7', 12.9), -560, 'inOut'], [at('S7', 32.4), -560], [at('S7', 36.2), -170, 'inOut']]),
    spiritY: K([[at('S7', 6.6), 60], [at('S7', 8.3), 250, 'out'], [at('S7', 32.4), 250], [at('S7', 36.2), 40, 'inOut']]),
    groupK: K([[at('S7', 4), 0], [at('S7', 9), 1], [at('S7', 32), 1], [at('S7', 36.5), 0]]),
    // family
    famLight: K([[at('S3', 0), 0], [at('S3', 14), 1], [at('S8', 28.1), 1], [at('S8', 30.1), 0.3], [at('S8', 45.1), 0.3], [at('S8', 47.0), 1]]),
    eyesFam: K([[0, 0], [at('S9', 1.2), 0], [at('S9', 2.4), 1], [at('S10', 26.7), 1], [at('S10', 27.5), 0.3]]),
    nod: t => Math.sin(clamp((t - at('S4', 13.4)) / 2.2) * Math.PI) * 0.12,
    glance: t => env(t, at('S6', 32.8), at('S6', 33.2), at('S6', 34.2), at('S6', 34.8)),
    hug: K([[at('S9', 0.3), 0], [at('S9', 7.5), 1], [at('S9', 8), 1]]),
    garden: K([[at('S6', 6.2), 0], [at('S6', 14.3), 1, 'out']]),
    gardenGlow: K([[at('S6', 0), 1], [at('S6', 18.6), 1], [at('S6', 18.8), 0.5], [at('S6', 19.7), 0.5], [at('S6', 20.0), 1], [at('S6', 36), 1], [at('S7', 4), 0.6], [at('S9', 14), 0.6], [at('S9', 20), 0.85], [at('S10', 16.0), 0.85], [at('S10', 16.7), 0.12], [at('S10', 21.05), 0.12], [at('S10', 22.6), 0.9], [at('S10', 32), 0.6]]),
    stars: K([[at('S6', 14.6), 0], [at('S6', 16.4), 1], [at('S6', 21.0), 1], [at('S6', 22.2), 0]]),
    starDim: K([[at('S6', 18.5), 1], [at('S6', 18.7), 0.5], [at('S6', 19.6), 0.5], [at('S6', 19.9), 1]]),
    flash: K([[at('S9', 9.4), 0], [at('S9', 10.0), 0.18], [at('S9', 11.4), 0.07], [at('S9', 13), 0], [at('S10', 21.15), 0], [at('S10', 21.45), 0.28], [at('S10', 22.5), 0]]),
    radiance: t => env(t, at('S9', 9.2), at('S9', 10.1), at('S9', 11.2), at('S9', 13.6)),
    dome: t => env(t, at('S10', 4.6), at('S10', 7.6), DIE[0], DIE[0] + 0.7) + env(t, DIE[1] + 0.3, DIE[1] + 1.8, CURTAIN[1], CURTAIN[1] + 0.5),
    seam: t => t < CURTAIN[1] - 0.1 ? 0 : clamp((t - CURTAIN[1] + 0.1) / 0.3) * (0.6 + 0.4 * Math.min(1, pulseAt(t) + (t > CURTAIN[1] + 2.0 ? 1 : 0))),
    flower: K([[at('S10', 37.55), 0], [at('S10', 39.55), 1]]),
    petal: K([[at('S10', 39.15), 0], [at('S10', 40.25), 1, 'sine']]),
    title: K([[0, 0.6], [0.5, 1], [at('P', 2.6), 1], [at('P', 3.2), 0]]),
    endTitle: K([[at('S10', 40.95), 0], [at('S10', 42.75), 1]]),
    letterbox: K([[0, 0.66], [at('S10', 31.96), 0.66], [at('S10', 34.2), 0.9]]),
  };

  // ------------------------------------------------------------------ beds (continuous audio levels)
  const BED_dr = K([[0, 0], [at('S1', 11), 0.05], [at('S1', 16), 0.3], [at('S2', 6), 0.4], [at('S3', 2), 0.38], [at('S3', 14), 0.15], [at('S5', 6.55), 0.08], [at('S6', 18), 0.12], [at('S6', 22.4), 0.32], [at('S6', 26.95), 0.4], [at('S6', 28.0), 0.1], [at('S7', 26.15), 0.25], [at('S7', 30.2), 0.06], [at('S8', 2), 0], [at('S9', 18), 0.05], [at('S10', 29.6), 0.05], [at('S10', 34), 0]]);
  const BED_wa = K([[0, 0], [at('S2', 16), 0], [at('S2', 22), 0.25], [at('S3', 14), 0.55], [at('S5', 0), 0.6], [at('S6', 28.9), 0.6], [at('S6', 29.0), 0.15], [WINK, 0.15], [WINK + 0.4, 0.6], [at('S8', 28.1), 0.6], [at('S8', 30.1), 0.2], [at('S8', 45.1), 0.2], [at('S8', 47.0), 0.6], [at('S9', 10), 0.8], [at('S10', 16.0), 0.8], [at('S10', 16.7), 0], [at('S10', 21.05), 0], [at('S10', 21.6), 0.85], [at('S10', 40), 0.6], [at('S10', 46.5), 0]]);
  const BED_wi = K([[0, 0], [at('P', 4.4), 0], [at('P', 7), 0.6], [at('S3', 6), 0.6], [at('S3', 16), 0.2], [at('S10', 31.96), 0.2], [at('S10', 36.76), 0]]);
  const BED_co = K([[0, 0], [at('S1', 11), 0], [at('S1', 16), 0.3], [at('S2', 6), 1], [at('S3', 8), 0.7], [at('S3', 14), 0.3], [at('S5', 25.95), 0.3], [at('S5', 32), 0.05], [at('S6', 18), 0.1], [at('S6', 22.4), 0.6], [at('S6', 26.95), 1.1], [at('S6', 28.0), 0.15], [at('S7', 26.15), 0], [at('S7', 26.3), 0.6], [at('S7', 30.2), 0.15], [at('S8', 2), 0], [at('S9', 18), 0.12], [at('S10', 29.6), 0.12], [at('S10', 33), 0]]);
  const BED_cut = K([[0, 9000], [at('S3', 6), 9000], [at('S3', 14), 1800], [at('S5', 6.55), 1800], [at('S5', 8.55), 350], [at('S6', 18), 350], [at('S6', 22), 2400], [at('S7', 26.15), 380], [at('S10', 0), 380]]);
  function beds(t) {
    const frozen = (t >= FREEZE[0] && t < FREEZE[1]) || (t >= DIE[0] + 0.2 && t < DIE[1]);
    const k = frozen ? 0 : 1;
    return { drone: BED_dr(t) * k, warmth: BED_wa(t) * k, wind: BED_wi(t) * k, cold: BED_co(t) * k, cut: BED_cut(t) };
  }

  // ------------------------------------------------------------------ family state
  const touchT = { keel: 1.0, hearth: 1.0, tidewell: 2.6, mender: 4.4, loom: 6.8, kindle: 26.2 };
  function famState(f, i, t, A, spirit) {
    const enter = at('S3', f.enter);
    let a = smooth((t - enter) / 1.8);
    // dissolve into him (S9), re-form after (S10)
    const m0 = MERGE[0] + i * 0.35;
    const mergeK = smooth((t - m0) / 3.2);
    const reform = smooth((t - REFORM[0] - i * 0.35) / 2.4);
    a *= 1 - mergeK * (1 - reform);
    let x = f.x, y = f.y, lean = f.lean, tilt = f.tilt, kneel = f.kneel || 0;
    // gather on the candle side to meet his spirit (S7)
    const g = tr.groupK(t);
    if (g > 0) {
      const [gx, gy] = GROUP[f.id];
      x = lerp(x, gx, g); y = lerp(y, gy, g); kneel = lerp(kneel, 0, g);
      const toward = spirit ? Math.sign(spirit.x - x) || 1 : 1;
      lean = lerp(lean, 0.18 * toward, g); tilt = lerp(tilt, 0.15 * toward, g);
    }
    // the hair stroke: Loom comes round the bedpost; the two at his head give it room
    const hairWin = env(t, at('S4', 6.2), at('S4', 7.0), at('S4', 12.4), at('S4', 13.2));
    if (f.id === 'loom') x = lerp(x, -420, hairWin);
    if (f.id === 'keel' || f.id === 'hearth') a *= 1 - 0.55 * hairWin;
    // hug: lean in closer (S9)
    const hug = tr.hug(t) * (1 - mergeK) + (t > REFORM[0] ? 0.6 * reform : 0);
    if (hug > 0 && !f.front && f.id !== 'mender') { x = lerp(x, x + (-170 - x) * 0.32, hug); lean = lean + (x < -170 ? 0.12 : -0.12) * hug; }
    // signature motion
    let bob = 0;
    if (f.id === 'kindle') {
      bob = Math.abs(Math.sin(t * Math.PI * 1.2)) * 6;
      const hop = t - at('S6', 32.6); if (hop > 0 && hop < 0.7) bob += Math.sin(hop / 0.7 * Math.PI) * 26;
    }
    if (f.id === 'keel') lean += Math.sin(t * TAU / 10) * 0.035;
    tilt += tr.nod(t) * (i % 2 ? 1 : 0.8);
    // heads turn to each other briefly (S5)
    tilt += env(t, at('S5', 26.2), at('S5', 27.2), at('S5', 28.9), at('S5', 30.2)) * (i % 2 ? 0.25 : -0.25);
    tilt += tr.glance(t) * (i % 2 ? 0.28 : -0.28);   // after the wink they glance at each other
    const eyes = tr.eyesFam(t);
    // hands
    const hands = [];
    const tt = at('S4', touchT[f.id]);
    for (let h = 0; h < 2; h++) {
      const [key, dx, dy] = f.touch[h];
      let target = A[key] ? [A[key][0] + dx, A[key][1] + dy] : null;
      let w = smooth((t - tt - h * 0.35) / 0.7);
      if (f.id === 'loom' && h === 0) {
        // three slow passes through what hair he has left: forehead, crown, back; then a lifted return
        const u = clamp((t - at('S4', 6.8)) / 5.5);
        const pass = (u * 3) % 1;
        const path = [[A.brow[0] - 6, A.brow[1] - 6], [A.hair[0] + 2, A.hair[1] - 18], [A.hair[0] + 10, A.hair[1] + 14]];
        let p;
        if (pass < 0.72) {
          const q = pass / 0.72, seg = q < 0.5 ? 0 : 1, k = q < 0.5 ? q * 2 : (q - 0.5) * 2;
          p = [lerp(path[seg][0], path[seg + 1][0], Ease.sine(k)), lerp(path[seg][1], path[seg + 1][1], Ease.sine(k))];
        } else {
          const k = Ease.sine((pass - 0.72) / 0.28), c = [A.hair[0] - 20, A.hair[1] - 60], a0 = path[2], a1 = path[0], v = 1 - k;
          p = [v * v * a0[0] + 2 * v * k * c[0] + k * k * a1[0], v * v * a0[1] + 2 * v * k * c[1] + k * k * a1[1]];
        }
        const settle = smooth((t - at('S4', 12.3)) / 0.5), crown = [A.crown[0] + dx, A.crown[1] + dy];
        if (u > 0 && u < 1) target = p;
        else if (u >= 1) target = [lerp(path[0][0], crown[0], settle), lerp(path[0][1], crown[1], settle)];
      }
      if (f.id === 'kindle') w = smooth((t - at('S4', 26.2) - h * 0.6) / 1.2);
      if (f.id === 'loom') w *= 1 - 0.95 * env(t, at('S6', 29.52), at('S6', 29.534), at('S6', 32.4), at('S6', 32.434));
      if (f.id === 'hearth' && h === 1) {
        // covers his hand from above during the close-up
        const k = env(t, at('S4', 27.0), at('S4', 28.2), at('S5', 3), at('S5', 4.5));
        if (k > 0) target = [lerp(target[0], A.hand[0] + 6, k), lerp(target[1], A.hand[1] - 12, k)];
      }
      // tug: everyone clamps on
      const clampK = env(t, at('S6', 24.0), at('S6', 24.55), SLIP + 0.4, SLIP + 1.2);
      if (clampK > 0 && target) { target = [target[0] + Math.sin(t * 30 + i) * clampK * 1.5, target[1] + clampK * 3]; w = Math.max(w, clampK); }
      // S7: release, then open arms to embrace the spirit
      if (g > 0) {
        const emb = env(t, at('S7', 12.5), at('S7', 13.6), at('S7', 31.6), at('S7', 32.6));
        if (spirit && emb > 0) {
          let sx = spirit.x + (x < spirit.x ? -18 : 18), sy = spirit.y - 300 * 0.62 + h * 30;
          // keep the embrace within reach of the shoulders so arms bend instead of locking straight
          const shx = x, shy = y - f.h * (0.5 + 0.305), dd = Math.hypot(sx - shx, sy - shy), rch = f.h * 0.36;
          if (dd > rch) { sx = shx + (sx - shx) * rch / dd; sy = shy + (sy - shy) * rch / dd; }
          target = target ? [lerp(target[0], sx, g), lerp(target[1], sy, g)] : [sx, sy];
          w = lerp(w * (1 - g), emb, g) + w * (1 - g);
        } else w *= 1 - g;
      }
      w *= a > 0.2 ? 1 : a / 0.2;
      hands.push(target ? { x: target[0], y: target[1], w } : { w: 0 });
    }
    return { x, y: y - bob, h: f.h, c: f.c, a, lean, tilt, face: f.face, kneel, hair: f.hair, hands, eyes, t, seed: i * 3.7 + 1, _m: mergeK };
  }

  // per-member signature: what makes each one recognisable without labels
  function famDecor(ctx, f, s, t) {
    const sk = s._sk; if (!sk || s.a < 0.02) return;
    const a = s.a * (s.bodyA ?? 1), h = s.h, c = s.c;
    if (f.id === 'hearth') {
      const p = pulseAt(t);
      Draw.glow(ctx, sk.chest[0], sk.chest[1] + h * 0.02, h * (0.07 + 0.04 * p), [255, 210, 160], a * (0.45 + 0.5 * p), 1);
    } else if (f.id === 'tidewell') {
      const b = breathAt(t);
      for (let k = 1; k <= 3; k++) {
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        ctx.strokeStyle = rgba(c, 0.12 * a); ctx.lineWidth = 1.2;
        const sw = h * (0.12 + 0.03 * k) * (1 + 0.06 * b);
        ctx.beginPath();
        for (let y = -0.32; y <= 0.05; y += 0.03) {
          const p = sk.P(-sw / h + Math.sin(t * 0.8 + y * 9 + k) * 0.008, y);
          y === -0.32 ? ctx.moveTo(p[0], p[1]) : ctx.lineTo(p[0], p[1]);
        }
        ctx.stroke();
        ctx.beginPath();
        for (let y = -0.32; y <= 0.05; y += 0.03) {
          const p = sk.P(sw / h + Math.sin(t * 0.8 + y * 9 + k + 2) * 0.008, y);
          y === -0.32 ? ctx.moveTo(p[0], p[1]) : ctx.lineTo(p[0], p[1]);
        }
        ctx.stroke(); ctx.restore();
      }
      Draw.glow(ctx, sk.chest[0], sk.chest[1], h * (0.35 + 0.08 * b), c, 0.1 * a);
    } else if (f.id === 'loom') {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(mix(c, [255, 255, 255], 0.3), 0.32 * a); ctx.lineWidth = 0.8;
      const r = h * 0.085;
      for (let k = 0; k < 14; k++) {
        const rate = 0.05 + (k % 5) * 0.035, ph = t * rate * TAU + k * 1.9;
        ctx.beginPath(); ctx.ellipse(sk.head[0], sk.head[1], r * (0.95 + (k % 3) * 0.12), r * 0.35, ph, 0, TAU); ctx.stroke();
      }
      ctx.restore();
    } else if (f.id === 'mender') {
      for (let hnd = 0; hnd < 2; hnd++) {
        const hp = s['_hand' + hnd]; if (!hp) continue;
        for (let k = 0; k < 6; k++) {
          for (let tr_ = 0; tr_ < 4; tr_++) {
            const ph = (t - tr_ * 0.07) * Math.PI + k * TAU / 6;
            const lx = Math.sin(ph) * 14, ly = Math.sin(ph * 2) * 6;
            Draw.glow(ctx, hp[0] + lx, hp[1] + ly - 4, 2.2, mix(c, [255, 255, 255], 0.4), a * (0.7 - tr_ * 0.16), 1);
          }
        }
      }
    } else if (f.id === 'keel') {
      for (let k = 0; k < 11; k++) {
        const u = -0.33 + k * 0.032;
        const p = sk.P(-0.035 * (s.face || 1), u);
        const rip = 0.5 + 0.5 * Math.sin(t * 2 - k * 0.6);
        Draw.glow(ctx, p[0], p[1], 3 + rip * 2, mix(c, [255, 255, 255], 0.5), a * (0.4 + 0.5 * rip), 1);
      }
    } else if (f.id === 'kindle') {
      for (let k = 0; k < 10; k++) {
        const ph = (t * 0.9 + k / 10) % 1;
        const sx = sk.head[0] + Noise.n2(k, t * 0.5) * h * 0.25, sy = sk.head[1] - ph * h * 0.5;
        Draw.glow(ctx, sx, sy, 2 + 2 * (1 - ph), [255, 236, 190], a * Math.sin(ph * Math.PI), 1);
      }
    }
  }

  // ------------------------------------------------------------------ projected memories (amber shadow-play on the wall)
  const PR = { x0: -650, x1: -40, y0: -600, y1: -236 };
  const AMBER = [243, 185, 121];
  function projection(ctx, cv, camM, t, fam) {
    const L = FX.layer('proj', cv), g = L.g;
    g.setTransform(camM.a, camM.b, camM.c, camM.d, camM.e, camM.f);
    g.fillStyle = '#fff'; g.strokeStyle = '#fff';
    const extras = [];   // coloured lights drawn after compositing
    let A = 0;
    const gy = -262;
    const vign = (u, a, b, c, d) => env(u, a, b, c, d);
    // S4 — young him shielding six small lights from a cold rain
    let u = local('S4', t), k = vign(u, 20.3, 21.0, 24.8, 25.5);
    if (k > 0) {
      A = Math.max(A, k); g.globalAlpha = k;
      g.fillRect(PR.x0 + 30, gy, PR.x1 - PR.x0 - 60, 3);
      Sil.person(g, -330, gy, 190, 'shield', 1);
      for (let i = 0; i < 6; i++) extras.push({ kind: 'dot', x: -470 + i * 16, y: gy - 10 - (i % 2) * 6, c: HUES[i], a: k, r: 7 });
      extras.push({ kind: 'rain', k, t });
    }
    // S5 — humanity: a chain of people holding hands that curls into a ring
    u = local('S5', t); k = vign(u, 12.9, 13.7, 18.8, 19.6);
    if (k > 0) {
      A = Math.max(A, k); g.globalAlpha = k;
      const ring = smoother((u - 15.2) / 2.6);
      const pts = [];
      for (let i = 0; i < 40; i++) {
        const lx = -700 + i * 25 + (u - 12.9) * 30, ly = gy;
        const an = -Math.PI / 2 + i / 40 * TAU, cx = -345, cy = -400, R = 104;
        const rx = cx + Math.cos(an) * R, ry = cy + Math.sin(an) * R;
        const x = lerp(lx, rx, ring), y = lerp(ly, ry, ring);
        if (ring < 0.02 && (x < PR.x0 + 10 || x > PR.x1 - 10)) continue;
        g.save(); g.translate(x, y); g.rotate(ring * (an + Math.PI / 2));
        const h = 62 + (i * 37 % 11) * 2.6;
        const pose = Sil.mixPose(Sil.walkPose(u * 7 + i * 0.7), { lean: 0, head: 0, ua: [1.2, -1.2], fa: [0.1, -0.1], th: [0.05, -0.05], sh: [0, 0] }, 0.55);
        const o = Sil.person(g, 0, 0, h, pose, 1, { child: i % 7 === 3, skirt: i % 3 === 1 });
        g.restore();
        pts.push([x, y - h * 0.52 * (1 - ring)]);
      }
      g.lineWidth = 2.2; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); if (ring > 0.9) g.closePath(); g.stroke();
    }
    // S5 — his own life, four glimpses, then a proscenium and curtains that stop part-way
    k = vign(u, 19.6, 19.9, 25.4, 25.9);
    if (k > 0) {
      A = Math.max(A, k);
      const scenes = [19.6, 20.8, 22.0, 23.2];
      scenes.forEach((s0, j) => {
        const kk = env(u, s0, s0 + 0.3, s0 + 1.1, s0 + 1.45) * (j === 3 ? 1 : 1) ;
        const hold = j === 3 ? env(u, s0, s0 + 0.3, 25.0, 25.8) : kk;
        if (hold <= 0) return;
        g.globalAlpha = hold * k;
        g.fillRect(PR.x0 + 30, gy, PR.x1 - PR.x0 - 60, 3);
        if (j === 0) {
          const o = Sil.person(g, -400 + (u - s0) * 60, gy, 110, Sil.walkPose(u * 10, 1), 1, { child: true });
          const kx = -170 + Math.sin(u * 2) * 10, ky = -520 + Math.cos(u * 3) * 8;
          g.beginPath(); g.moveTo(kx, ky - 22); g.lineTo(kx + 16, ky); g.lineTo(kx, ky + 26); g.lineTo(kx - 16, ky); g.closePath(); g.fill();
          g.lineWidth = 1.2; g.beginPath(); g.moveTo(o.hands[0][0], o.hands[0][1]); g.quadraticCurveTo(-260, -380, kx, ky + 26); g.stroke();
          g.beginPath(); g.moveTo(kx, ky + 26); for (let q = 1; q < 6; q++) g.lineTo(kx - q * 8 + Math.sin(u * 6 + q) * 5, ky + 26 + q * 10); g.stroke();
        } else if (j === 1) {
          Sil.person(g, -360, gy, 185, 'lean', 1);
          g.fillRect(-320, -350, 210, 5); for (let q = 0; q < 4; q++) g.fillRect(-310 + q * 62, -350, 4, 88);
          g.lineWidth = 2; for (let q = 0; q < 3; q++) { g.beginPath(); for (let x = -300; x <= -60; x += 10) g.lineTo(x, -300 + q * 14 + Math.sin(x * 0.04 + u * 3 + q) * 4); g.stroke(); }
        } else if (j === 2) {
          const o = Sil.person(g, -340, gy, 190, { lean: 0, head: 0, ua: [2.4, 2.5], fa: [0.3, 0.2], th: [0.04, -0.04], sh: [0, 0] }, 1);
          Sil.person(g, o.neck[0] - 2, o.neck[1] + 38, 84, 'sit', 1, { child: true });
        } else {
          const o = Sil.person(g, -330, gy, 176, 'cane', 1);
          g.lineWidth = 3.5; g.beginPath(); g.moveTo(o.hands[0][0], o.hands[0][1] - 4); g.lineTo(o.hands[0][0] + 14, gy); g.stroke();
        }
      });
    }
    // S8 — everyday care, shared humanity, a bow of respect, and the alignment: they are me
    u = local('S8', t);
    const dayK = vign(u, 0.6, 1.2, 27.6, 28.4);
    if (dayK > 0) {
      A = Math.max(A, dayK);
      const v = (s0, s1) => env(u, s0, s0 + 0.5, s1 - 0.5, s1);
      let kk = v(1.0, 8.9);
      if (kk > 0) { // (a) kitchen table at dawn: leaning in to listen to their needs
        g.globalAlpha = kk * dayK; g.fillRect(PR.x0 + 30, gy, PR.x1 - PR.x0 - 60, 3);
        const o = Sil.person(g, -480, gy, 180, Sil.mixPose(Sil.POSES.sit, Sil.POSES.lean, 0.35 + 0.15 * Math.sin(u)), 1);
        g.fillRect(-420, -330, 190, 8); g.fillRect(-410, -330, 6, 70); g.fillRect(-246, -330, 6, 70);
        extras.push({ kind: 'dot', x: -230, y: -362, c: HUES[0], a: kk * dayK, r: 11 });
        extras.push({ kind: 'rings', x: o.head[0] + 14, y: o.head[1], tx: -240, ty: -362, a: kk * dayK, t });
      }
      kk = v(8.9, 15.4);
      if (kk > 0) { // (b) shared humanity: everyone walks with a family of their own lights
        g.globalAlpha = kk * dayK; g.fillRect(PR.x0 + 30, gy, PR.x1 - PR.x0 - 60, 3);
        for (let i = 0; i < 9; i++) {
          const x = -630 + i * 66 + (u - 8.9) * 14, h = 150 + (i * 37 % 5) * 9;
          if (x < PR.x0 + 10 || x > PR.x1 - 10) continue;
          const o = Sil.person(g, x, gy, h, Sil.walkPose(u * 5 + i * 0.7), 1, { child: i === 6, skirt: i % 3 === 1, hat: i === 2 });
          if (i === 4) HUES.forEach((c, j) => extras.push({ kind: 'dot', x: o.neck[0] - 18 + j * 7, y: o.neck[1] + 16 + (j % 2) * 6, c, a: kk * dayK, r: 3.2 }));
          else extras.push({ kind: 'dot', x: o.neck[0], y: o.neck[1] + 18, c: [255, 214, 160], a: kk * dayK * 0.85, r: 4 });
        }
      }
      kk = v(15.4, 21.9);
      if (kk > 0) { // (c) respect: a bow to the light, and the light bows back
        const b = env(u, 16.0, 17.2, 19.6, 20.8);
        g.globalAlpha = kk * dayK; g.fillRect(PR.x0 + 30, gy, PR.x1 - PR.x0 - 60, 3);
        Sil.person(g, -420, gy, 190, Sil.mixPose(Sil.POSES.stand, Sil.POSES.bow, b), 1);
        extras.push({ kind: 'dot', x: -250, y: -400 + b * 22, c: [255, 220, 170], a: kk * dayK, r: 16 });
      }
      kk = v(21.8, 28.2);
      if (kk > 0) { // (d) alignment: a large figure of him; the six lights take their places in the body
        g.globalAlpha = kk * dayK * 0.85;
        const o = Sil.person(g, -345, -262, 240, 'stand', 1);
        const al = smoother((u - 22.6) / 3.4);
        const hx = o.head[0], hy = o.head[1];
        const zones = { loom: [hx, hy], tidewell: [hx + 2, hy + 64], hearth: [hx + 9, hy + 78], mender: [hx + 3, hy + 112], keel: [hx - 8, hy + 86], kindle: [o.hands[1][0], o.hands[1][1]] };
        FAM.forEach((f, i) => {
          const [zx, zy] = zones[f.id];
          const sx = i < 3 ? PR.x0 + 40 : PR.x1 - 40, sy = PR.y0 + 70 + (i % 3) * 80;
          extras.push({ kind: 'dot', x: lerp(sx, zx, al), y: lerp(sy, zy, al), c: f.c, a: kk * dayK, r: f.id === 'keel' ? 7 : 10, spine: f.id === 'keel' ? al : 0, sx: hx - 8, sy0: hy + 40 });
        });
      }
    }
    // S9 — ninety-nine years scrolling past, each a flash of a moment
    u = local('S9', t); k = vign(u, 15.5, 16.5, 33.0, 34.0);
    if (k > 0) {
      A = Math.max(A, k); g.globalAlpha = k;
      g.fillRect(PR.x0 + 20, -420, PR.x1 - PR.x0 - 40, 2);
      const off = (u - 15.5) * 58;
      g.font = 'italic 15px "Cormorant Garamond", Garamond, serif'; g.textAlign = 'center';
      for (let yr = 1; yr <= 99; yr++) {
        const x = PR.x1 - 30 - (off - yr * 9) * 1 - 600 + 600;
        const xx = PR.x0 + 20 + ((yr * 9 - off) + 900) % 900 - 300;
        const xs = PR.x1 - 40 - (off * 1.0) + yr * 9 - 10;
        const px = -40 + yr * 9 - off;   // scrolls left
        if (px < PR.x0 + 20 || px > PR.x1 - 20) continue;
        const flash = Math.exp(-Math.pow((px - (-345)) / 22, 2));
        g.globalAlpha = k * (0.35 + 0.65 * flash);
        g.fillRect(px - 1, -428 - (yr % 10 === 0 ? 10 : 0) - flash * 10, 2, 16 + (yr % 10 === 0 ? 10 : 0) + flash * 10);
        if (yr % 10 === 0 || yr === 1 || yr === 99) g.fillText(String(yr), px, -446 - flash * 8);
      }
    }
    // S10 — the day we were born: a newborn in two hands, six tiny lights circling
    u = local('S10', t); k = vign(u, 8.3, 9.1, 14.6, 15.4);
    if (k > 0) {
      A = Math.max(A, k);
      const kb = 1;
      g.globalAlpha = k * kb;
      const cx = -345, cy = -390;
      // two forearms rising from below into a cupped cradle
      for (const side of [-1, 1]) {
        Draw.taper(g, Draw.crPts([[cx + side * 175, cy + 150], [cx + side * 120, cy + 70], [cx + side * 72, cy + 30]], 6), 18, 12); g.fill();
        for (let q = 0; q < 4; q++) { g.beginPath(); g.ellipse(cx + side * (78 + q * 1.5), cy + 14 - q * 9, 7, 12, side * (0.25 + q * 0.12), 0, TAU); g.fill(); }
      }
      g.beginPath(); g.ellipse(cx, cy + 32, 84, 26, 0, 0.05 * Math.PI, 0.95 * Math.PI); g.lineTo(cx - 70, cy + 30); g.ellipse(cx, cy + 28, 70, 14, 0, Math.PI, 0, true); g.closePath(); g.fill();
      // the newborn, swaddled, head to the left, separated from the hands by a sliver of air
      const baby = new Path2D();
      baby.ellipse(cx + 12, cy + 2, 42, 17, -0.06, 0, TAU); baby.moveTo(cx - 22, cy - 3); baby.arc(cx - 36, cy - 3, 14, 0, TAU);
      g.save(); g.globalCompositeOperation = 'destination-out'; g.lineWidth = 6; g.stroke(baby); g.restore();
      g.fill(baby);
      g.beginPath(); g.arc(cx - 14, cy - 18, 5, 0, TAU); g.fill();
      // (the six tiny lights are drawn in render: they leave the projection and fly to the family)
      // ...and the same geometry now: an old man in his bed, six lights around him
      const kn = 0;
      if (kn > 0) {
        g.globalAlpha = k * kn;
        g.fillRect(cx - 150, cy + 40, 300, 12); g.fillRect(cx - 150, cy + 10, 10, 60); g.fillRect(cx + 140, cy + 28, 10, 42);
        g.beginPath(); g.ellipse(cx - 110, cy + 26, 16, 13, 0, 0, TAU); g.fill();
        g.beginPath(); g.moveTo(cx - 92, cy + 40); g.quadraticCurveTo(cx - 40, cy + 6, cx + 40, cy + 24); g.quadraticCurveTo(cx + 110, cy + 16, cx + 130, cy + 40); g.closePath(); g.fill();
      }
    }
    return { L, A, extras };
  }
  function drawExtras(ctx, P, t) {
    for (const e of P.extras) {
      if (e.kind === 'dot') {
        Draw.glow(ctx, e.x, e.y, e.r * 3.2, e.c, 0.55 * e.a); Draw.glow(ctx, e.x, e.y, e.r, mix(e.c, [255, 255, 255], 0.5), 0.95 * e.a, 1);
        if (e.spine > 0) for (let q = 0; q < 9; q++) Draw.glow(ctx, e.sx, (e.sy0 ?? -490) + q * 12, 3.2, e.c, e.a * e.spine * 0.8, 1);
      } else if (e.kind === 'rain') {
        ctx.save(); ctx.beginPath(); ctx.rect(-318, PR.y0, PR.x1 - (-318), PR.y1 - PR.y0); ctx.clip();
        ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba([159, 182, 217], 0.4 * e.k); ctx.lineWidth = 1.6;
        ctx.beginPath();
        for (let i = 0; i < 46; i++) { const x = -310 + ((i * 53.7 + e.t * 260) % 340), y = PR.y0 + ((i * 97.1 + e.t * 520) % (PR.y1 - PR.y0)); ctx.moveTo(x + 40, y - 46); ctx.lineTo(x, y); }
        ctx.stroke(); ctx.restore();
      } else if (e.kind === 'rings') {
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        for (let q = 0; q < 3; q++) {
          const ph = (e.t * 0.6 + q / 3) % 1, x = lerp(e.x, e.tx, ph), y = lerp(e.y, e.ty, ph);
          ctx.strokeStyle = rgba(AMBER, 0.5 * e.a * Math.sin(ph * Math.PI)); ctx.lineWidth = 2;
          ctx.beginPath(); ctx.arc(x, y, 8 + ph * 6, -0.9, 0.9); ctx.stroke();
        }
        ctx.restore();
      } else if (e.kind === 'ribbon') {
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
        for (let w = 0; w < 2; w++) {
          ctx.strokeStyle = rgba(e.c, (w ? 0.75 : 0.22) * e.a); ctx.lineWidth = w ? 2 : 9;
          ctx.beginPath();
          for (let q = 0; q <= 30; q++) { const x = e.x - 20 + q * 3, y = e.y + Math.sin(q * 0.4 - e.t * 3) * 10 - q * 0.8; q ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
          ctx.stroke();
        }
        ctx.restore();
      }
    }
  }

  // ------------------------------------------------------------------ pieces of the room that belong to death
  function reaperShadow(ctx, L, t) {
    const k = tr.shadow(t); if (k <= 0.003 || !L._beam) return;
    ctx.save(); ctx.clip(L._beam);
    // a hooded shadow cast by the moon through the glass: it slides down the wall and across the quilt toward him
    const len = 360 * Ease.out(clamp(k));
    ctx.translate(170, -250); ctx.rotate(2.42);
    ctx.filter = 'blur(3px)';
    ctx.fillStyle = `rgba(2,3,10,${0.55 * k})`;
    ctx.beginPath();
    ctx.moveTo(0, -40); ctx.lineTo(len * 0.7, -50);
    ctx.quadraticCurveTo(len * 0.86, -56, len * 0.95, -26);   // shoulder into hood
    ctx.quadraticCurveTo(len * 1.04, -6, len * 1.02, 6);      // the hood's point
    ctx.quadraticCurveTo(len * 0.96, 40, len * 0.7, 50);
    ctx.lineTo(0, 40); ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  // ------------------------------------------------------------------ death, always on the far side of a boundary
  // at the window: rises outside the glass, eclipses the moon, later fogs the pane with its palm, bows
  function reaperOutside(t) {
    return (g, WIN) => {
      const a = tr.rA(t); if (a <= 0.003) return;
      const rise = tr.rise(t), sc = tr.rScale(t), bow = tr.rBow(t);
      const mx = WIN.x0 + (WIN.x1 - WIN.x0) * 0.66, my = WIN.y0 + 120;
      const sh = clamp((1 - sc) / 0.45);
      const x = lerp(mx - 18, mx, sh * 0.85), feet = lerp(-24 + (1 - rise) * 460, my + 70, sh * 0.85) + bow * 22;
      const palm = tr.palm(t);
      const r = { x, y: feet, h: 430 * sc, a, t, lean: -0.05 + bow * 0.12, eyes: 0, smoke: 0, scythe: 1 - palm * 0.3,
        reach: palm > 0 ? { x: 120, y: -360, w: palm, curl: -0.2 } : null };
      Draw.reaper(g, r);
      if (palm > 0.4 && r._hand) {
        const [px, py] = r._hand, k = smooth((palm - 0.4) / 0.6);
        Draw.glow(g, px + 20, py, 46, [221, 232, 245], 0.35 * k);
        g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = rgba([221, 232, 245], 0.18 * k);
        g.beginPath(); g.ellipse(px + 16, py + 4, 15, 18, 0, 0, TAU); g.fill();
        for (let q = 0; q < 4; q++) { g.beginPath(); g.ellipse(px + 6 + q * 7, py - 22 - (q === 1 || q === 2 ? 5 : 0), 3.5, 9, 0, 0, TAU); g.fill(); }
        g.restore();
      }
    };
  }
  // in the doorway with a vaudeville hook (Act VI): he never crosses the threshold
  const DOOR = { x0: 470, x1: 610, y0: -330, y1: 190 };
  function hookPull(t) {
    let p = 0; TUGS.forEach((tt, i) => { p += env(t, tt - 0.05, tt + 0.12, tt + 0.35, tt + 0.7) * (0.14 + i * 0.1); });
    return p;
  }
  function doorReaper(g, t) {
    const a = tr.doorR(t); if (a <= 0.003) return null;
    const pull = hookPull(t), askew = tr.askew(t), shrug = tr.shrug(t), lean = tr.lean(t);
    const stagger = env(t, SLIP, SLIP + 0.18, SLIP + 0.5, SLIP + 1.4);
    g.save();
    g.beginPath(); g.rect(DOOR.x0 + 2, DOOR.y0, DOOR.x1 - DOOR.x0 - 2, DOOR.y1 - DOOR.y0); g.clip();
    // a cold-lit corridor behind him, so he reads as a crisp silhouette
    const cg = g.createLinearGradient(0, DOOR.y0, 0, DOOR.y1);
    cg.addColorStop(0, rgba([84, 100, 132], 0.95 * a)); cg.addColorStop(0.6, rgba([56, 68, 94], 0.9 * a)); cg.addColorStop(1, rgba([24, 28, 40], 0.8 * a));
    g.fillStyle = cg; g.fillRect(DOOR.x0, DOOR.y0, DOOR.x1 - DOOR.x0, DOOR.y1 - DOOR.y0);
    Draw.glow(g, 560, -160, 240, [150, 170, 210], 0.8 * a);
    const r = { x: 548 + pull * 30 + stagger * 22, y: 190 - shrug * 8, h: 430, a, t, lean: 0.06 + pull * 0.9 + askew * 0.22 - lean * 0.05, eyes: 0, smoke: 0, scythe: false,
      reach: { x: 500 - pull * 20, y: -72, w: tr.reachW(t), curl: 0.6 } };
    Draw.reaper(g, r);
    g.restore();
    return r;
  }
  function drawHook(g, t, R, bedDX) {
    if (!R) return;
    const out = tr.hookOut(t);
    const [hx, hy] = R._hand || [500, -72];
    const bent = range(SLIP, SLIP + 0.3, t) * 0.45;
    if (out > 0.01) {
      // shoots out to the footboard finial and hooks it
      const tx = lerp(hx - 10, 378 + bedDX, out), ty = lerp(hy, -82, out);
      Theatre.hook(g, hx + 6, hy + 2, tx, ty, 1, bent);
    } else if (t > SLIP) {
      // after the slip: a slightly bent hook he looks at, then leans on
      const ln = tr.lean(t), back = range(SLIP + 0.3, SLIP + 0.8, t);
      const ex = lerp(hx - 10, lerp(hx - 40, hx - 22, ln), back), ey = lerp(hy, lerp(hy - 10, 186, ln), back);
      Theatre.hook(g, hx + 4, hy, ex, ey, tr.doorR(t), 0.45);
    }
  }
  // the finale: he stands at the fly rail in the wing, bows, and pulls the curtain closed
  function wingReaper(g, t) {
    const a = tr.wingR(t); if (a <= 0.003) return;
    const x = 905 + range(at('S10', 38.4), at('S10', 40), t) * 70, rail = -1100;
    const pull = range(CURTAIN[0], CURTAIN[1], t), working = pull > 0 && pull < 1 ? 1 : 0;
    const hand = -40 - (Math.sin((t - CURTAIN[0]) * 5.2) * 0.5 + 0.5) * 70 * env(t, CURTAIN[0], CURTAIN[0] + 0.4, CURTAIN[1] - 0.4, CURTAIN[1]);
    Draw.glow(g, x + 10, -40, 320, [150, 170, 215], 0.85 * a);           // a cold work light behind him
    Draw.glow(g, x + 10, -160, 160, [190, 205, 235], 0.5 * a);
    // the rope and its sandbag
    g.save(); g.strokeStyle = rgba([160, 140, 110], 0.55 * a); g.lineWidth = 3;
    g.beginPath(); g.moveTo(x - 40, rail); g.lineTo(x - 40, 210); g.stroke();
    g.fillStyle = rgba([40, 34, 30], a); g.fillRect(x - 54, 210, 28, 40); g.restore();
    const r = { x, y: LIPY, h: 430, a, t, lean: -0.05 - tr.wingBow(t) * 0.32, eyes: 0, smoke: 0.5, scythe: false, reach: { x: x - 42, y: hand, w: 1, curl: 0.7 } };
    Draw.reaper(g, r);
    return r;
  }
  const LIPY = Theatre.LIP;
  function finaleFlower(g, t) {
    const k = tr.flower(t); if (k <= 0.003) return;
    const x = 0, y0 = LIPY - 2;
    g.save();
    g.strokeStyle = rgba([110, 170, 100], 0.85); g.lineWidth = 3; g.lineCap = 'round';
    const top = y0 - 190 * Ease.out(k);
    g.beginPath(); g.moveTo(x, y0); g.quadraticCurveTo(x + 8, (y0 + top) / 2, x, top); g.stroke();
    FAM.forEach((f, i) => {
      const ki = Ease.back(clamp((k - i * 0.1) / 0.5));
      if (ki <= 0) return;
      if (i === 5 && tr.petal(t) > 0) return;   // this petal has flown
      const an = -Math.PI / 2 + (i - 2.5) * 0.62;
      g.save(); g.translate(x, top); g.rotate(an + Math.PI / 2);
      g.globalCompositeOperation = 'lighter';
      g.fillStyle = rgba(mix(f.c, [255, 255, 255], 0.2), 0.75);
      g.beginPath(); g.ellipse(0, -22 * ki, 10 * ki, 22 * ki, 0, 0, TAU); g.fill();
      g.restore();
    });
    Draw.glow(g, x, top, 60, [255, 226, 180], 0.45 * k);
    Draw.glow(g, x, top, 8, [255, 250, 235], 0.9 * k, 1);
    g.restore();
  }
  function flyingPetal(g, t, R) {
    const k = tr.petal(t); if (k <= 0.003 || !R) return;
    const sx = 0, sy = LIPY - 170, tx = R.x - 30, ty = R.y - R.h * 0.8;   // lands on his shoulder, and goes where he goes
    const x = lerp(sx, tx, k), y = lerp(sy, ty, k) - Math.sin(k * Math.PI) * 160;
    const c = FAM[5].c, wa = tr.wingR(t);
    g.save(); g.translate(x, y); g.rotate(k * 7 + Math.sin(t * 3) * 0.4 * (1 - k));
    g.globalCompositeOperation = 'lighter'; g.fillStyle = rgba(mix(c, [255, 255, 255], 0.2), 0.8 * wa);
    g.beginPath(); g.ellipse(0, 0, 6, 13, 0, 0, TAU); g.fill(); g.restore();
    Draw.glow(g, x, y, 22, c, 0.5 * wa);
  }

  // ------------------------------------------------------------------ titles
  function titleCard(ctx, W, H, DPR, k, main, sub) {
    if (k <= 0.003) return;
    ctx.save(); ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    const size = Math.min(W * 0.06, H * 0.1);
    ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = size * 0.5;
    ctx.font = `300 ${size}px "Cormorant Garamond", Garamond, serif`;
    try { ctx.letterSpacing = (size * 0.06).toFixed(1) + 'px'; } catch (e) { }
    ctx.globalAlpha = k; ctx.fillStyle = '#f3e9d8';
    ctx.fillText(main, W / 2, H * 0.48);
    try { ctx.letterSpacing = '0px'; } catch (e) { }
    ctx.font = `italic 400 ${size * 0.34}px "Cormorant Garamond", Garamond, serif`;
    ctx.globalAlpha = k * 0.78; ctx.fillStyle = '#f3b66d';
    ctx.fillText(sub, W / 2, H * 0.48 + size * 0.78);
    ctx.restore();
  }

  // ------------------------------------------------------------------ the idle frame behind the Begin screen
  function intro(ctx, W, H, DPR) {
    const it = performance.now() / 1000;
    const g = ctx; g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
    FX.camera(g, { cx: -330, cy: -60, w: 1100, pw: 0.75, pcx: -330 }, W, H, DPR);
    const L = { moon: 0.25, candle: 0.75, warm: 0.22, flick: 0.9 + 0.1 * Noise.n1(it * 5.3), wax: 0.95, door: 0.18, clock: it, beamLen: 1 };
    World.room(g, L, it); World.candle(g, L, it); World.roomLight(g, L); World.bed(g, L);
    World.man(g, L, { t: it, breath: 0.5 + 0.5 * Math.sin(it * TAU / 5.5), eyes: 0, wink: 0, smile: 0.05, inner: 0 });
    FX.wash(g, W, H, DPR, [0, 0, 0], 0.5);
    return { bloom: 0.3, letterbox: 0 };
  }

  // ------------------------------------------------------------------ RENDER
  function render(ctx, t, dt, W, H, DPR) {
    const cv = ctx.canvas;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; FX.resetState(ctx);
    if (t < 0) return intro(ctx, W, H, DPR);
    if (t >= FREEZE[0] && t < FREEZE[1]) t = FREEZE[0];
    ctx.fillStyle = '#05070d'; ctx.fillRect(0, 0, cv.width, cv.height);
    const shot = FX.shotAt(t, CAM);
    const scale = H / 1080 * DPR;

    // ---- light state
    const flick = 0.9 + 0.08 * Noise.n1(t * 5.3) + 0.04 * Noise.n1(t * 13.1);
    const L = {
      moon: tr.moon(t), beamLen: 1, candle: tr.candle(t), candleLean: tr.candleLean(t), warm: tr.warm(t), flick,
      wax: tr.wax(t), smoke: 0, door: tr.door(t), clock: t, frost: tr.frost(t), drape: 0,
      gutter: env(t, at('S2', 0), at('S2', 2), at('S2', 14), at('S2', 18)) + env(t, TUGS[0] - 0.3, TUGS[0], TUGS[2] + 0.5, TUGS[2] + 1.5),
    };
    L.candlePos = [-466, 22 - (64 * L.wax + 6) - 20];
    L.outside = reaperOutside(t);
    const bedDX = tr.bedShift(t);

    // ---- the man (state only; drawn later)
    const wink = env(t, WINK, WINK + 0.16, WINK + 1.1, WINK + 1.45);
    const M = {
      t, breath: breathAt(t) * tr.breathAmp(t), eyes: tr.eyes(t), wink, smile: tr.smile(t), gaze: tr.gaze(t), turn: tr.turn(t),
      inner: tr.inner(t), curl: tr.curl(t), tug: tr.tug(t), glint: tr.glint(t), hand: { x: -60, y: -96, w: tr.lift(t) * 0.35 },
    };
    const A0 = World.anchors(M), A = {};
    for (const k in A0) A[k] = [A0[k][0] + bedDX, A0[k][1]];
    const sA = tr.spiritA(t);
    const spirit = sA > 0.003 ? { x: tr.spiritX(t), y: tr.spiritY(t) } : null;
    // ---- the family
    const famLight = tr.famLight(t);
    const dying = env(t, DIE[0], DIE[0] + 0.7, DIE[1] - 0.1, DIE[1] + 0.25);
    const dim = 1 - 0.85 * dying;
    const S = FAM.map((f, i) => famState(f, i, t, A, spirit));
    const closeK = env(t, at('S4', 24.8), at('S4', 26.0), at('S4', 33), at('S5', 2.6));
    const winkK = env(t, at('S6', 29.52), at('S6', 29.534), at('S6', 32.4), at('S6', 32.434));
    S.forEach((s, i) => {
      const id = FAM[i].id, inv = id === 'kindle' || id === 'hearth' || id === 'tidewell', nearHead = id === 'keel' || id === 'loom' || id === 'hearth';
      s.a *= dim * (1 - 0.22 * tr.groupK(t));
      s.bodyA = (1 - closeK) * (1 - winkK);
      s.armA = (1 - (inv ? 0.15 : 1) * closeK) * (1 - 0.92 * winkK);
      s.handOnly = inv ? closeK : 0; s.handGlow = (1 - 0.62 * closeK) * (nearHead && closeK < 0.5 ? 0.45 : 1);
    });
    const loomS = S[2];
    if (local('S4', t) > 6.6 && local('S4', t) < 13) M.hair = { x: loomS.hands[0].x - bedDX, y: loomS.hands[0].y, w: loomS.hands[0].w * env(t, at('S4', 6.8), at('S4', 7.4), at('S4', 12), at('S4', 12.6)) };
    L.family = S.map(s => ({ x: s.x, y: s.y - s.h * 0.7, c: s.c, a: s.a * famLight, r: 620 }));
    const moteK = env(t, at('S2', 16), at('S2', 19), at('S3', 0), at('S3', 13));

    // ================= FAR LAYER: wall, window (death outside), clock, the doorway
    const far = FX.layer('far', cv), fg = far.g;
    const cam = FX.camera(fg, shot, W, H, DPR, shake(t), t);
    const camM = fg.getTransform();
    World.room(fg, L, t);
    const R = doorReaper(fg, t);
    const PJ = projection(fg, cv, camM, t, S);
    const stars = tr.stars(t);
    if (stars > 0.003) { fg.save(); fg.setTransform(1, 0, 0, 1, 0, 0); fg.globalAlpha = stars; Env.starfield(fg, tr.starDim(t), cv.width, cv.height, t, t); fg.restore(); }
    const fb = tr.farBlur(t) * scale;
    ctx.save(); ctx.filter = fb > 0.3 ? `blur(${fb.toFixed(1)}px)` : 'none'; ctx.drawImage(far.c, 0, 0); ctx.restore();
    // memories projected on the wall: a soft projector glow, then the silhouettes as amber light
    if (PJ.A > 0.003) {
      ctx.save(); ctx.setTransform(camM);
      Draw.glow(ctx, (PR.x0 + PR.x1) / 2, (PR.y0 + PR.y1) / 2, 420, AMBER, 0.08 * PJ.A);
      ctx.restore();
      const tint = FX.layer('projTint', cv);
      tint.g.drawImage(PJ.L.c, 0, 0);
      tint.g.globalCompositeOperation = 'source-in'; tint.g.fillStyle = rgba(AMBER, 1); tint.g.fillRect(0, 0, cv.width, cv.height);
      ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha = 0.46 * (0.9 + 0.1 * Noise.n1(t * 7)); ctx.drawImage(tint.c, 0, 0);
      ctx.restore();
    }

    // ================= NEAR: light in the air, the bed, him, them
    const nb = tr.nearBlur(t) * scale;
    const nearL = nb > 0.3 ? FX.layer('near', cv) : null;
    const g = nearL ? nearL.g : ctx;
    FX.camera(g, shot, W, H, DPR, shake(t), t);
    World.roomLight(g, L);
    Theatre.spot(g, tr.spot(t), dying > 0.5 ? [255, 236, 214] : [255, 227, 176]);
    World.motes(g, L, t);
    World.candle(g, L, t);
    const isFront = f => f.front || tr.groupK(t) > 0.5;
    FAM.forEach((f, i) => { if (!isFront(f)) { Draw.figureBody(g, S[i]); famDecor(g, f, S[i], t); } });
    if (PJ.A > 0.01 && loomS._sk) {
      const [lx, ly] = loomS._sk.head;
      g.save(); g.globalCompositeOperation = 'lighter';
      const cg = g.createLinearGradient(lx, ly, (PR.x0 + PR.x1) / 2, (PR.y0 + PR.y1) / 2);
      cg.addColorStop(0, rgba(FAM[2].c, 0.1 * PJ.A * loomS.a)); cg.addColorStop(1, rgba(FAM[2].c, 0.015 * PJ.A));
      g.fillStyle = cg; g.beginPath(); g.moveTo(lx, ly); g.lineTo(PR.x0 + 40, PR.y0 + 30); g.lineTo(PR.x1 - 40, PR.y1 - 10); g.closePath(); g.fill();
      g.restore();
    }
    // six warm motes drift out of the candle and his chest, then become them
    if (moteK > 0.003) {
      for (let i = 0; i < 6; i++) {
        const z = FAM[i].zone, src = z === 'spine' ? [A.chest[0] + 40, A.chest[1] + 20] : (A[z] || A.chest);
        const born = smooth((t - at('S2', 16) - i * 0.5) / 2.5);
        const an = t * 0.5 + i / 6 * TAU, ox = -150 + Math.cos(an) * 90, oy = -200 + Math.sin(an * 1.3) * 40;
        const f = FAM[i], ent = at('S3', f.enter), go = smooth((t - ent + 0.6) / 0.6);
        const fx = S[i]._sk ? S[i]._sk.chest : [f.x, f.y - f.h * 0.6];
        const x = lerp(lerp(src[0], ox, born), fx[0], go), y = lerp(lerp(src[1], oy, born), fx[1], go);
        const a = moteK * born * (1 - smooth((t - ent - 0.2) / 0.5));
        Draw.glow(g, x, y, 26, f.c, 0.5 * a); Draw.glow(g, x, y, 6, [255, 250, 235], 0.9 * a, 1);
      }
    }
    FAM.forEach((f, i) => {   // as each arrives, the part of him it keeps glows once
      const ent = at('S3', f.enter), zk = env(t, ent - 0.4, ent, ent + 1.2, ent + 2.2);
      if (zk <= 0) return;
      const zp = f.zone === 'spine' ? [A.chest[0] + 40, A.chest[1] + 20] : (A[f.zone] || A.chest);
      Draw.glow(g, zp[0], zp[1], 30, f.c, 0.55 * zk); Draw.glow(g, zp[0], zp[1], 7, mix(f.c, [255, 255, 255], 0.5), 0.8 * zk, 1);
    });
    FAM.forEach((f, i) => {
      const ent = at('S3', f.enter), k = (t - ent) / 1.8;
      if (k <= 0 || k >= 1 || !S[i]._sk) return;
      const c = S[i]._sk.chest;
      for (let q = 0; q < 26; q++) {
        const an = q * 2.399, r0 = 140 + (q % 5) * 30, e = Ease.out(k);
        const tx = c[0] + Math.cos(an) * f.h * 0.12 * ((q % 3) / 3), ty = c[1] + Math.sin(an) * f.h * 0.25 * ((q % 4) / 4) - f.h * 0.05;
        const x = lerp(c[0] + Math.cos(an) * r0 * 0.15, tx + Math.cos(an) * r0 * (1 - e) * 0.6, e), y = lerp(c[1], ty + Math.sin(an) * r0 * (1 - e) * 0.6, e);
        Draw.glow(g, x, y, 3, mix(f.c, [255, 255, 255], 0.4), (1 - k) * 0.9, 1);
      }
    });
    // the bed and the man (who slide a little when death tugs)
    g.save(); g.translate(bedDX, 0);
    World.bed(g, L);
    World.man(g, L, M);
    reaperShadow(g, L, t);
    g.restore();
    // the protective dome of their light (finale)
    const dome = tr.dome(t);
    if (dome > 0.003) {
      g.save(); g.globalCompositeOperation = 'screen';
      g.translate(-130, -70); g.scale(1, 0.55);
      const dg = g.createRadialGradient(0, 0, 120, 0, 0, 640);
      dg.addColorStop(0, rgba([255, 226, 190], 0.05 * dome)); dg.addColorStop(0.6, rgba([255, 214, 170], 0.08 * dome)); dg.addColorStop(0.85, rgba([255, 236, 210], 0.07 * dome)); dg.addColorStop(1, 'rgba(255,236,210,0)');
      g.fillStyle = dg; g.beginPath(); g.arc(0, 0, 640, 0, TAU); g.fill();
      g.restore();
    }
    FAM.forEach((f, i) => { if (isFront(f)) { Draw.figureBody(g, S[i]); famDecor(g, f, S[i], t); } });
    FAM.forEach((f, i) => { Draw.figureArms(g, S[i]); if (f.id === 'mender') famDecor(g, f, S[i], t); });
    // one faint flicker in Hearth's heart, in the dark
    const flk = env(t, at('S10', 19.95), at('S10', 20.01), at('S10', 20.1), at('S10', 20.65));
    if (flk > 0 && S[0]._sk) Draw.glow(g, S[0]._sk.chest[0], S[0]._sk.chest[1], 40, [255, 190, 150], 0.9 * flk, 1);
    // touch ripples
    FAM.forEach((f, i) => {
      const tt = at('S4', touchT[f.id]);
      for (let h = 0; h < 2; h++) {
        const d = t - tt - h * 0.35 - 0.5;
        if (d > 0 && d < 1.1 && S[i].hands[h].w > 0.5) FX.ring(g, S[i].hands[h].x, S[i].hands[h].y, 6 + d * 40, f.c, 0.45 * (1 - d / 1.1), 2);
      }
    });
    // the garden of life
    const gk = tr.garden(t);
    const hookK = tr.hookOut(t) > 0 ? 1 : env(t, at('S6', 22.6), at('S6', 23.2), SLIP + 0.6, SLIP + 1.4), grpK = clamp((tr.groupK(t) - 0.4) / 0.4);
    const gmask = (winkK > 0 || hookK > 0 || grpK > 0) ? (x, y) => {
      let m = 1;
      if (winkK > 0) m *= 1 - winkK * clamp(1 - Math.hypot(x - World.HEAD[0], y - World.HEAD[1]) / 650) * 1.6;
      if (hookK > 0 && x > 300 && x < 470) m *= 1 - 0.95 * hookK;
      if (grpK > 0 && x < -380) m *= 1 - 0.9 * grpK;
      return clamp(m);
    } : null;
    if (gk > 0.003) Env.garden(g, gk, t, tr.gardenGlow(t), gmask);
    drawExtras(g, PJ, t);
    // death's hook reaches in through the doorway
    drawHook(g, t, R, bedDX);
    // his spirit runs to them (Act VII) and their light braids into him
    if (spirit) {
      const u = local('S7', t);
      const X = tr.spiritX, x0 = X(t), speed = Math.abs(X(t + 1 / 30) - x0) * 30;
      const dist = u < 8.9 ? Math.abs(x0 + 150) : u < 32.4 ? 220 + Math.abs(x0 - 70) : 850 + Math.abs(x0 + 560);
      const running = env(u, 8.9, 9.3, 12.3, 12.9);
      Draw.spirit(g, { x: spirit.x, y: spirit.y, h: 300, a: sA, c: [255, 240, 214], run: clamp(speed / 260), phase: dist * 0.045, dir: u < 8.6 ? 1 : u < 32.4 ? -1 : 1, t, trail: running,
        reach: env(u, 12.6, 13.2, 31.4, 32) > 0.5 ? { x: spirit.x - 40, y: spirit.y - 210 } : null });
      const rib = env(u, 30.4, 31.6, 32.4, 33.4);
      if (rib > 0) {
        const core = [spirit.x, spirit.y - 300 * 0.73];
        S.forEach((s, i) => { if (s._sk) FX.stream(g, s._sk.chest[0], s._sk.chest[1], core[0], core[1], s.c, rib, t, i, 22, 26); });
        Draw.glow(g, core[0], core[1], 14 + 18 * rib, [255, 236, 200], 0.9 * rib, 1);
      }
    }
    // the day we were born: six tiny lights leave the projection and fly home into the six of them
    const fly = range(at('S10', 13.0), at('S10', 14.7), t);
    const birthK = env(local('S10', t), 8.3, 9.1, 14.7, 15.1);
    if (birthK > 0) {
      const u = local('S10', t);
      HUES.forEach((c, i) => {
        const an = u * 1.4 + i / 6 * TAU, px = -345 + Math.cos(an) * 90, py = -410 + Math.sin(an) * 40;
        const dst = S[i]._sk ? S[i]._sk.chest : [px, py];
        const k = Ease.inOut(clamp((fly - i * 0.06) / 0.7));
        const x = lerp(px, dst[0], k), y = lerp(py, dst[1], k) - Math.sin(k * Math.PI) * 60;
        Draw.glow(g, x, y, 16, c, 0.6 * birthK); Draw.glow(g, x, y, 5, mix(c, [255, 255, 255], 0.5), 0.95 * birthK, 1);
        if (k > 0.97) Draw.glow(g, dst[0], dst[1], 70, c, 0.5 * env(u, 14.1, 14.3, 14.5, 15.1));
      });
    }
    // oneness: they flow into him and become the lit places of his body (Act IX -> Finale)
    const rad = tr.radiance(t);
    if (rad > 0.003) { Draw.glow(g, A.chest[0], A.chest[1], 900, [255, 236, 200], 0.42 * rad); Draw.glow(g, A.chest[0], A.chest[1], 160, [255, 248, 230], 0.8 * rad, 1); }
    const zoneK = smooth((t - MERGE[0] - 2) / 3);
    S.forEach((s, i) => {
      const f = FAM[i];
      const zp = f.zone === 'spine' ? [-120 + bedDX, A.chest[1] + 20] : A[f.zone];
      if (s._m > 0.02 && s._m < 0.98 && s._sk) FX.stream(g, s._sk.chest[0], s._sk.chest[1], zp[0], zp[1], f.c, Math.sin(s._m * Math.PI), t, i, 30, 30);
      if (zoneK > 0.01) {
        const lock = smooth((t - at('S9', 18)) / 7);
        const own = 0.5 + 0.5 * Math.sin(t * (1.2 + i * 0.37) * TAU * 0.5 + i);
        const pul = lerp(own, 0.35 + 0.65 * pulseAt(t), lock);
        const za = zoneK * (0.45 + 0.55 * pul) * (1 - 0.8 * dying);
        if (f.zone === 'spine') for (let q = 0; q < 12; q++) Draw.glow(g, -226 + q * 22 + bedDX, World.blanketTop(-226 + q * 22, M.breath) + 22, 4, f.c, za * 0.8, 1);
        else { Draw.glow(g, zp[0], zp[1], 34, f.c, 0.5 * za); Draw.glow(g, zp[0], zp[1], 8, mix(f.c, [255, 255, 255], 0.5), 0.8 * za, 1); }
        const th = env(t, REFORM[0] + 1, REFORM[0] + 3, at('S10', 30), at('S10', 34)) * (1 - 0.7 * dying);
        if (th > 0 && s._sk) {
          g.save(); g.globalCompositeOperation = 'lighter'; g.strokeStyle = rgba(f.c, (0.3 + 0.3 * env(t, at('S10', 24.5), at('S10', 26), at('S10', 29), at('S10', 31))) * th); g.lineWidth = 0.9;
          g.beginPath(); g.moveTo(s._sk.chest[0], s._sk.chest[1]); g.quadraticCurveTo((s._sk.chest[0] + zp[0]) / 2, Math.min(s._sk.chest[1], zp[1]) - 40, zp[0], zp[1]); g.stroke(); g.restore();
        }
      }
    });
    if (nearL) { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.filter = `blur(${nb.toFixed(1)}px)`; ctx.drawImage(nearL.c, 0, 0); ctx.restore(); }

    // ================= THE SHIP (Act VIII): the stage floods with the sea of a life
    const seaIn = range(SEA_IN[0], SEA_IN[1], t), seaOut = range(SEA_OUT[0], SEA_OUT[1], t);
    const seaK = seaIn * (1 - seaOut);
    if (seaK > 0.003) {
      const u = local('S8', t);
      const sl = FX.layer('sea', cv);
      sl.g.setTransform(DPR, 0, 0, DPR, 0, 0);
      const storm = env(u, 35.2, 36.3, 38.6, 39.8), dawn = range(39.6, 42.2, u), carry = range(41.9, 43.2, u);
      Env.sea(sl.g, { W, H, t, storm, dawn, huddle: storm, carry,
        boat: { x: lerp(0.42, 0.5, range(28, 42, u)), scale: lerp(1, 1.45, carry) },
        family: FAM.map(f => ({ c: f.c, a: 1, hair: f.hair, small: f.id === 'kindle', eyes: 0.6 })), man: { a: 1 } });
      FX.composite(ctx, sl, seaIn * (1 - seaOut), 'rise', { t, edge: rgba([200, 220, 255], 1) });
    }

    // ================= THE THEATRE: house curtain, ghost light, proscenium, the wings, the house
    FX.camera(ctx, shot, W, H, DPR, shake(t), t);
    const foot = tr.foot(t);
    if (foot > 0.003) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; const fw = ctx.createLinearGradient(0, 320, 0, -500); fw.addColorStop(0, rgba([255, 194, 122], 0.3 * foot)); fw.addColorStop(1, 'rgba(255,194,122,0)'); ctx.fillStyle = fw; ctx.fillRect(-900, -600, 1800, 920); ctx.restore(); }
    const trav = tr.trav(t), ghost = tr.ghost(t), seam = tr.seam(t);
    Theatre.traveller(ctx, trav, t, { light: 0.25 + 0.5 * tr.spot(t) * (1 - trav) + seam * 0.5, ghost, foot: 0.3 + foot, seam: seam * (1 - 0.75 * tr.endTitle(t)), spot: tr.spot(t) });
    finaleFlower(ctx, t);
    if (ghost > 0.003 || t > at('S10', 38)) Theatre.ghostLight(ctx, ghost, t, t > T.S10 ? -300 : 0);
    Theatre.proscenium(ctx, { foot: 0.25 + 0.5 * foot + 0.3 * tr.spot(t) * (t < T.S1 ? 1 : 0) });
    const WR = wingReaper(ctx, t);
    if (tr.wingR(t) > 0.003 || t > at('S10', 40)) {   // his bent, unused hook, leaning on the proscenium
      Theatre.hook(ctx, 868, 300, 840, -150, 0.95 * Math.max(tr.wingR(t), t > at('S10', 40) ? 1 : 0), 0.45);
      if (ghost > 0.01) Draw.glow(ctx, 850, 120, 120, [255, 184, 102], 0.15 * ghost);
    }
    flyingPetal(ctx, t, WR);
    Theatre.house(ctx, W, H, DPR, tr.house(t) * (1 - seaK), tr.houseGlow(t));

    // ================= overlays
    const fl = tr.flash(t);
    if (fl > 0) FX.wash(ctx, W, H, DPR, [255, 236, 200], fl, 'screen');
    const sd = tr.stageDark(t);
    if (sd > 0.002) FX.wash(ctx, W, H, DPR, [3, 2, 2], sd);
    const blk = tr.black(t);
    if (blk > 0.002) FX.wash(ctx, W, H, DPR, [5, 4, 4], blk);
    // act cards in the letterbox
    for (const k of Object.keys(DUR)) {
      if (k === 'P') continue;
      const u = t - T[k], ak = env(u, 0.3, 1.0, 3.2, 4.2);
      if (ak > 0) Theatre.actCard(ctx, W, H, DPR, ak, `${ACTS[k][0]}  ·  ${ACTS[k][1]}`.toUpperCase());
    }
    titleCard(ctx, W, H, DPR, tr.title(t), 'The Last Thing on My Mind', 'a final performance');
    const et = tr.endTitle(t) * (1 - tr.black(t));
    titleCard(ctx, W, H, DPR, et, 'The Last Thing on My Mind', 'for the emotional family in all of us');
    const bloom = 0.2 + 0.06 * famLight + 0.1 * fl + 0.12 * rad + 0.08 * zoneK - 0.1 * closeK - 0.12 * winkK + 0.12 * ghost * (t < 4 || t > at('S10', 38) ? 1 : 0);
    return { bloom, letterbox: tr.letterbox(t), tone: 1 };
  }

  // ------------------------------------------------------------------ SCORE
  function score() {
    const E = [];
    const push = a => { for (const e of a) E.push(e); };
    const ch = (s, lt) => at(s, lt);
    const voice = (f, when, dur, vel = 1) => {
      if (f.id === 'hearth') return [{ t: when, i: 'pad', a: [[50], dur, { vel: 0.07 * vel, att: 1.2, rel: 2, cut: 900, noSub: true }], len: dur }];
      if (f.id === 'tidewell') return [Score.at(when, 'breath', 2.6, true, 0.04 * vel), { t: when, i: 'pad', a: [[57], dur, { vel: 0.05 * vel, att: 1.5, rel: 2.5, cut: 700, type: 'sine', noSub: true }], len: dur }];
      if (f.id === 'loom') return [Score.at(when, 'bell', 66, 0.14 * vel, 4, -0.3)];
      if (f.id === 'mender') return [{ t: when, i: 'pad', a: [[59], dur, { vel: 0.05 * vel, att: 1, rel: 2, cut: 1200, type: 'sine', noSub: true }], len: dur }];
      if (f.id === 'keel') return [{ t: when, i: 'bowed', a: [38, dur, 0.08 * vel, 0], len: dur }];
      return [Score.at(when, 'bell', 76, 0.12 * vel, 2.5, 0.3), Score.at(when, 'piano', 88, 0.12 * vel, 2, 0.3)];
    };
    // ---- PROLOGUE: the house, the ghost light, chimes, the spot, the curtain
    for (let i = 0; i < 14; i++) E.push(Score.at(0.1 + i * 0.22 + (i % 3) * 0.05, 'rub', 0.5 + (i % 4) * 0.15, 0.012 + (i % 3) * 0.004, 600 + (i * 137) % 900));
    E.push(Score.at(at('P', 3.3), 'tick', false, 0.16));                   // the ghost light clicks off
    E.push(Score.at(at('P', 3.65), 'bell', 88, 0.1, 2.4, -0.2)); E.push(Score.at(at('P', 4.1), 'bell', 100, 0.07, 2.4, 0.2));   // theatre chimes
    E.push(Score.at(at('P', 4.4), 'boom', 0.12)); E.push(Score.at(at('P', 4.42), 'tick', true, 0.1));                         // the spot clunks on
    E.push(Score.at(at('P', 4.6), 'whoosh', 3.4, 0.06, false)); E.push(Score.at(at('P', 4.8), 'rub', 2.8, 0.025, 380, 0.15)); // velvet + rope
    push([{ t: at('P', 4.6), i: 'pad', a: [[38, 45], 11.4, { vel: 0.07, att: 4, rel: 4, cut: 500, type: 'triangle', noSub: true }], len: 11.4 }]);
    // ---- ACT I: drone, the clock on the pendulum's beat, heart, breath
    push([{ t: ch('S1', 0), i: 'pad', a: [[38, 45, 50], 18, { vel: 0.07, att: 6, rel: 5, cut: 600, type: 'triangle', noSub: true }], len: 18 }]);
    for (let tt = Math.ceil(ch('S1', 0.5) - 0.5) + 0.5; tt < ch('S6', 22.4); tt += 1) {
      let amp = 0.06;
      if (tt > ch('S2', 6) && tt < ch('S2', 11)) amp = 0.06 + 0.04 * env(tt, ch('S2', 6), ch('S2', 7), ch('S2', 10), ch('S2', 11));
      else if (tt > ch('S3', 8)) amp = tt < ch('S5', 6.55) ? 0.025 : 0.01;
      E.push(Score.at(tt, 'tick', Math.floor(tt) % 2 === 1, amp));
    }
    for (let tt = ch('S6', 22.5); tt < FREEZE[0]; tt += 0.5) E.push(Score.at(tt, 'tick', Math.round(tt * 2) % 2 === 1, 0.05));
    for (const h of HEARTS) {
      let amp = h < T.S2 ? 0.13 : 0.16;
      if (Math.abs(h - at('S10', 19.95)) < 0.01) amp = 0.09;
      if (h > CURTAIN[1]) amp = 0.12;
      E.push(Score.at(h, 'heart', amp));
    }
    for (const b of BREATHS) {
      if (b.t > total - 4) continue;
      const amp = (b.t > SEA_IN[0] && b.t < SEA_OUT[1]) ? 0 : b.big ? 0.05 : 0.03;
      if (amp) { E.push(Score.at(b.t, 'breath', b.P * 0.42, true, amp)); E.push(Score.at(b.t + b.P * 0.45, 'breath', b.P * 0.52, false, amp * 1.1)); }
    }
    E.push(Score.at(ch('S1', 8.2), 'piano', 65, 0.16, 3, 0));               // the finger lifts
    // ---- ACT II: mortality, D minor
    push(Score.pads(ch('S2', 0), ['Dm', 'Bb', 'Gm', 'Asus4'], 5.5, { vel: 0.11, cut: 1100 }));
    E.push(Score.at(ch('S2', 16), 'whoosh', 3, 0.07, true));
    for (let i = 0; i < 6; i++) E.push(Score.at(ch('S2', 16.4) + i * 0.5, 'bell', 93 + [0, 2, 4, 7, 9, 12][i], 0.06, 1.2, (i - 2.5) * 0.2));
    // ---- ACT III: they arrive, each with a voice, building D major add9
    push(Score.pads(ch('S3', 0), ['A', 'D', 'A/C#', 'Bm', 'G'], 3.2, { vel: 0.1, cut: 1200 }));
    FAM.forEach(f => push(voice(f, ch('S3', f.enter), 14 - f.enter + 2)));
    // ---- ACT IV: hands — piano melody over strings
    push(Score.pads(ch('S4', 0), ['D', 'F#m', 'G', 'D/A', 'A', 'D'], 5.5, { vel: 0.09, cut: 1300 }));
    push(Score.line(ch('S4', 0.2), [['F#5', 0, 2], ['E5', 2, 1], ['D5', 3, 3], ['A4', 6, 2], ['C#5', 8, 1], ['E5', 9, 3], ['D5', 12, 2], ['B4', 14, 1], ['G4', 15, 3], ['F#4', 18, 2], ['A4', 20, 1], ['D5', 21, 3], ['E5', 24, 2], ['C#5', 26, 1], ['A4', 27, 3], ['B4', 30, 2], ['A4', 32, 1], ['D5', 33, 3]], 66, { vel: 0.3 }));
    [['keel', 'D5'], ['hearth', 'F#5'], ['tidewell', 'A5'], ['mender', 'B4'], ['loom', 'D6'], ['kindle', 'E6']].forEach(([id, n]) => E.push(Score.at(ch('S4', touchT[id] + 0.55), 'piano', Score.note(n), 0.16, 3, 0.2)));
    for (let i = 0; i < 9; i++) E.push(Score.at(ch('S4', 6.9) + i * 0.6, 'bell', 98 + (i % 3) * 2, 0.03, 0.8, -0.4 + i * 0.1));
    push(voice(FAM[5], ch('S4', 26.2), 6, 1.2));
    E.push({ t: ch('S4', 28.3), i: 'pad', a: [[50, 57, 62, 66], 4.5, { vel: 0.08, att: 2.4, rel: 2.5, cut: 2400 }], len: 4.5 });
    // ---- ACT V: the last thing on my mind
    push(Score.pads(ch('S5', 0), ['Bm', 'G', 'D', 'A', 'Bm'], 6.5, { vel: 0.1, cut: 1300 }));
    push(Score.arp(ch('S5', 0), ['Bm', 'G', 'D', 'A', 'Bm'], 6.5, { step: 6.5 / 12, pattern: [0, 2, 3, 4, 5, 4], vel: 0.18, ring: 3 }));
    push(Score.choir(ch('S5', 12.9), ['D', 'D'], 3.2, { vel: 0.06, centre: 66 }));
    E.push(Score.at(ch('S5', 19.6), 'whoosh', 3.4, 0.05, false)); E.push(Score.at(ch('S5', 19.8), 'rub', 3, 0.02, 380, 0.15));   // the real curtain creeps in
    // ---- ACT VI: hold on; the garden; the universe; the hook; the wink
    push(Score.pads(ch('S6', 0.25), ['Bm', 'G'], 3, { vel: 0.09, cut: 1100 }));
    push(Score.arp(ch('S6', 6.2), ['D', 'G', 'Bm', 'A'], 2.05, { step: 60 / 76 / 2, pattern: [0, 3, 2, 4, 3, 5, 4, 2], vel: 0.16, ring: 1.2 }));
    push(Score.pads(ch('S6', 6.2), ['D', 'G', 'Bm', 'A'], 2.05, { vel: 0.07, cut: 1500 }));
    for (let i = 0; i < 8; i++) E.push(Score.at(ch('S6', 7 + i * 0.95), 'bell', [74, 78, 81, 83, 86, 88][i % 6], 0.06, 2, (i % 5 - 2) * 0.2));
    E.push({ t: ch('S6', 14.6), i: 'pad', a: [[50, 57, 64, 69], 7.4, { vel: 0.06, att: 2, rel: 2, cut: 900, noSub: true }], len: 7.4 });
    for (let i = 0; i < 12; i++) E.push(Score.at(ch('S6', 15.0 + i * 0.58), 'bell', [86, 88, 90, 93, 95][i % 5], 0.035, 2.5, (i % 3 - 1) * 0.4));
    // the gag: a sly pizzicato walk under the tugs
    push(Score.line(ch('S6', 22.5), [['D3', 0, 1], ['F#3', 1, 1], ['A3', 2, 1], ['G#3', 3, 1], ['A3', 4, 1], ['F#3', 5, 1], ['D3', 6, 1], ['E3', 7, 1], ['F3', 8, 1], ['F#3', 9, 1], ['G3', 10, 1], ['G#3', 11, 1]], 136, { vel: 0.22 }));
    push([{ t: ch('S6', 24.2), i: 'bowed', a: [38, 2.8, 0.1, 0], len: 2.8 }, { t: TUGS[2], i: 'bowed', a: [37, 1.6, 0.11, 0], len: 1.6 }]);
    TUGS.forEach((tt, i) => { E.push(Score.at(tt, 'boom', 0.2 + i * 0.06)); E.push(Score.at(tt, 'rub', 0.35, 0.05 + i * 0.01, 500, 0.03)); E.push({ t: tt + 0.22, i: 'pad', a: [[62, 66, 69], 0.8, { vel: 0.06, att: 0.15, rel: 0.7, cut: 2000 }], len: 0.8 }); });
    [96, 93, 90, 86, 83, 81, 78, 74].forEach((m, i) => E.push(Score.at(SLIP + i * 0.045, 'piano', m, 0.14, 0.6, 0.3 - i * 0.08)));   // the hook slips: a tumbling run
    E.push(Score.at(SLIP + 0.1, 'rub', 0.5, 0.05, 260, 0.05));
    E.push(Score.at(FREEZE[0], 'gate', FREEZE[1] - FREEZE[0], 0.012, 0.02));     // the freeze: true silence
    E.push(Score.at(WINK - 1.05, 'bell', 95, 0.03, 1.2, 0.3));                     // his eye opens
    E.push(Score.at(WINK, 'piano', 69, 0.32, 1.2, -0.2)); E.push(Score.at(WINK + 0.16, 'piano', 78, 0.36, 1.6, 0.2));
    E.push(Score.at(WINK + 0.2, 'bell', 90, 0.1, 1.5, 0.3));
    [0.55, 0.8, 1.05].forEach((d, i) => E.push(Score.at(WINK + d, 'piano', [81, 83, 86][i], 0.16, 0.8, 0.3)));
    push(Score.pads(WINK + 0.6, ['G', 'D/F#', 'G'], 1.9, { vel: 0.1, cut: 1800 }));
    E.push(Score.at(at('S6', 33.2), 'heart', 0.08)); E.push(Score.at(at('S6', 33.42), 'heart', 0.07));   // Hearth's laugh
    E.push(Score.at(at('S6', 34.0), 'piano', 50, 0.12, 1.2, 0.5)); E.push(Score.at(at('S6', 34.25), 'piano', 45, 0.1, 1.4, 0.5));   // the reaper's shrug
    // ---- ACT VII: I run to them; death is on the outside
    E.push({ t: ch('S7', 0), i: 'bowed', a: [35, 6, 0.09, 0], len: 6 });
    push(Score.pads(ch('S7', 0), ['Bm', 'G'], 3.3, { vel: 0.08, cut: 900 }));
    push(Score.pads(ch('S7', 6.6), ['G', 'D/F#', 'Em', 'A', 'D', 'G', 'D/F#', 'A'], 2.45, { vel: 0.1, cut: 1700 }));
    push(Score.arp(ch('S7', 6.6), ['G', 'D/F#', 'Em', 'A', 'D', 'G', 'D/F#', 'A'], 2.45, { step: 60 / 84 / 2, pattern: [0, 2, 3, 4, 5, 4, 3, 2], vel: 0.15, ring: 1.4 }));
    for (let i = 0; i < 5; i++) E.push(Score.at(ch('S7', 6.7) + i * 1.43, 'boom', 0.12));
    for (let i = 0; i < 9; i++) E.push(Score.at(ch('S7', 9.0) + i * 0.4, 'rub', 0.15, 0.05, 180, 0.05));   // footfalls
    E.push({ t: ch('S7', 13.3), i: 'pad', a: [[50, 57, 62, 66, 69, 76], 6, { vel: 0.12, att: 0.6, rel: 3, cut: 2600 }], len: 6 });
    push(Score.pads(ch('S7', 20.7), ['D', 'G', 'D/F#'], 1.8, { vel: 0.09, cut: 1400 }));
    E.push(Score.at(ch('S7', 26.2), 'rub', 2.8, 0.03, 6000));                                       // frost
    push(Score.pads(ch('S7', 26.15), ['Bm', 'G'], 2.1, { vel: 0.07, cut: 800 }));
    FAM.forEach((f, i) => E.push(Score.at(ch('S7', 30.6) + i * 0.42, 'bell', [62, 66, 69, 74, 78, 81][i], 0.1, 2.5, (i - 2.5) * 0.25)));
    push(Score.pads(ch('S7', 30.4), ['D', 'G', 'D'], 2.2, { vel: 0.09, cut: 1300 }));
    // ---- ACT VIII: daily life — then the ship, a barcarolle in 6/8
    push(Score.arp(ch('S8', 0), ['D', 'Bm', 'G', 'A', 'D', 'Bm', 'G'], 4, { step: 1 / 3, pattern: [0, 2, 3, 4, 3, 2], vel: 0.17, ring: 2.4 }));
    push(Score.pads(ch('S8', 0), ['D', 'Bm', 'G', 'A', 'D', 'Bm', 'G'], 4, { vel: 0.07, cut: 1200 }));
    push(Score.line(ch('S8', 0.5), [['F#5', 0, 3], ['A5', 3, 3], ['G5', 6, 2], ['F#5', 8, 1], ['E5', 9, 6], ['D5', 15, 3], ['E5', 18, 3], ['F#5', 21, 6]], 60, { instr: 'bowed', vel: 0.06 }));
    push(Score.arp(ch('S8', 28.1), ['D', 'A', 'Bm', 'G', 'D'], 1.4, { step: 1 / 3, pattern: [0, 2, 3, 4, 3, 2], vel: 0.15, ring: 2 }));
    push(Score.pads(ch('S8', 28.1), ['D', 'A', 'Bm', 'G', 'D'], 1.4, { vel: 0.08, cut: 1500 }));
    push(Score.pads(ch('S8', 35.2), ['Bm', 'F#m', 'G', 'A'], 1.15, { vel: 0.18, cut: 3000 }));
    for (let i = 0; i < 6; i++) E.push(Score.at(ch('S8', 35.3) + i * 0.75, 'boom', 0.14));
    E.push(Score.at(ch('S8', 35.0), 'rain', 5.6, 0.05));
    for (let w = ch('S8', 35.3); w < ch('S8', 40.3); w += 1.1) E.push(Score.at(w, 'wave', 2.2, 0.18));
    E.push(Score.at(ch('S8', 37.2), 'whoosh', 2, 0.08, true));
    push(Score.pads(ch('S8', 39.8), ['D', 'G/D', 'A', 'D'], 1.6, { vel: 0.1, cut: 1800 }));
    push(Score.arp(ch('S8', 39.8), ['D', 'G/D', 'A', 'D'], 1.6, { step: 1 / 3, pattern: [0, 2, 3, 4, 3, 2], vel: 0.14, ring: 2.4 }));
    push(Score.line(ch('S8', 41.9), [['D5', 0, 0.5], ['F#5', 0.5, 0.5], ['A5', 1, 0.5], ['B5', 1.5, 0.5], ['A5', 2, 0.5], ['F#5', 2.5, 0.5], ['E5', 3, 0.5], ['D5', 3.5, 1.5]], 133, { instr: 'bell', vel: 0.12 }));
    E.push({ t: ch('S8', 42.7), i: 'pad', a: [[50, 57, 62, 66], 3.4, { vel: 0.1, att: 1.2, rel: 2.5, cut: 1600 }], len: 3.4 });
    for (let w = ch('S8', 28.4); w < ch('S8', 45.1); w += 4.2) E.push(Score.at(w, 'wave', 4.5, 0.07 + 0.18 * env(w, ch('S8', 35), ch('S8', 36), ch('S8', 38.6), ch('S8', 39.8))));
    E.push(Score.at(ch('S8', 44.9), 'whoosh', 2.2, 0.06, false));
    // ---- ACT IX: one
    E.push({ t: ch('S9', 0), i: 'pad', a: [[50, 57, 64, 66], 8, { vel: 0.1, att: 3, rel: 3, cut: 1100, noSub: true }], len: 8 });
    push(Score.choir(ch('S9', 8.0), ['D', 'D'], 3.2, { vel: 0.16, centre: 62 }));
    E.push({ t: ch('S9', 8.0), i: 'pad', a: [[50, 57, 62, 66, 69], 6.5, { vel: 0.16, att: 1.6, rel: 4, cut: 3600 }], len: 6.5 });
    [74, 78, 81, 86, 90].forEach((m, i) => E.push(Score.at(ch('S9', 9.6) + i * 0.07, 'bell', m, 0.12, 4, (i - 2) * 0.3)));
    E.push({ t: ch('S9', 9.5), i: 'bowed', a: [38, 4, 0.14, 0], len: 4 });
    push(Score.pads(ch('S9', 15.0), ['D', 'G', 'D/F#', 'A', 'D', 'G', 'A'], 3, { vel: 0.09, cut: 1400 }));
    FAM.forEach((f, i) => { for (let r = 0; r < 3; r++) push(voice(f, ch('S9', 14.2 + i * 0.6 + r * (1.9 + i * 0.37)), 1.6, 0.6)); });
    for (let r = 0; r < 12; r++) FAM.forEach(f => push(voice(f, ch('S9', 20.5) + r * 1.25, 1.1, 0.45)));
    // ---- FINALE
    push(Score.pads(ch('S10', 0.25), ['G', 'A', 'F#m', 'Bm'], 2.0, { vel: 0.09, cut: 1200 }));
    push(Score.choir(ch('S10', 4.6), ['D', 'G'], 1.7, { vel: 0.05, centre: 62 }));
    push(Score.pads(ch('S10', 8.3), ['G', 'D/F#', 'G', 'D/F#'], 1.9, { vel: 0.07, cut: 1000, overlap: 1.0, rel: 0.8 }));
    push(Score.line(ch('S10', 8.5), [['D5', 0, 1], ['F#5', 1, 1], ['A5', 2, 1], ['B5', 3, 1], ['D6', 4, 1], ['E6', 5, 1]], 70, { instr: 'bell', vel: 0.11 }));
    for (let i = 0; i < 6; i++) E.push(Score.at(ch('S10', 14.2) + i * 0.22, 'bell', [86, 90, 93, 95, 98, 100][i], 0.05, 1.2, (i - 2.5) * 0.25));   // tiny lights merge home
    // 'When they die, I die': everything stops but a heartbeat
    E.push(Score.at(DIE[0] + 0.15, 'gate', DIE[1] - DIE[0] - 0.25, 0.35, 0.05));
    push(Score.pads(DIE[1] + 0.05, ['G', 'A', 'D'], 1.8, { vel: 0.2, cut: 3400 }));
    E.push(Score.at(DIE[1] + 0.05, 'whoosh', 1.4, 0.06, true));
    push(Score.choir(DIE[1] + 0.05, ['D', 'D'], 2.7, { vel: 0.14, centre: 66 }));
    push(Score.pads(ch('S10', 26.7), ['D', 'Bm', 'G', 'A'], 1.3, { vel: 0.16, cut: 2600 }));
    FAM.forEach((f, i) => push(voice(f, ch('S10', 26.8) + i * 0.15, 4.6, 0.8)));
    push(Score.line(ch('S10', 26.9), [['F#5', 0, 2], ['E5', 2, 1], ['D5', 3, 3]], 70, { instr: 'bowed', vel: 0.07 }));
    E.push({ t: ch('S10', 30.1), i: 'bowed', a: [38, 2.4, 0.1, 0], len: 2.4 });    // the reaper's bow: one low string
    E.push({ t: CURTAIN[0], i: 'pad', a: [[50, 57, 64, 66], 10, { vel: 0.1, att: 2, rel: 4, cut: 1100 }], len: 10 });
    E.push(Score.at(CURTAIN[0], 'whoosh', 4.8, 0.07, false)); E.push(Score.at(CURTAIN[0] + 0.3, 'rub', 4.4, 0.025, 380, 0.15));
    E.push(Score.at(CURTAIN[1], 'boom', 0.18));                                   // the curtains meet
    E.push(Score.at(at('S10', 37.8), 'bell', 81, 0.06, 3, 0)); E.push(Score.at(at('S10', 38.4), 'bell', 86, 0.05, 3, 0));   // the flower
    E.push(Score.at(at('S10', 40.45), 'tick', false, 0.12));                    // the ghost light clicks back on
    E.push(Score.at(at('S10', 40.5), 'bell', 74, 0.15, 5, 0));                  // a bell where the heartbeat was
    E.push({ t: at('S10', 40.95), i: 'pad', a: [[38, 50, 57, 64, 66], 3, { vel: 0.08, att: 1.5, rel: 2, cut: 900 }], len: 3 });
    // the freezes are true silence (the gate does that); nothing new starts inside them
    return E.filter(e => e.i === 'gate' || e.i === 'heart' || !((e.t >= FREEZE[0] - 0.05 && e.t < FREEZE[1] - 0.02) || (e.t >= DIE[0] + 0.15 && e.t < DIE[1] - 0.02)));
  }
  const events = score();

  // ------------------------------------------------------------------ the narrator's voice
  // VOICE (01b-voice.js) holds one recorded take per line. Each line is spoken a beat after its
  // caption appears; the caption stays up until the voice has finished, and its words surface as
  // they are spoken.
  if (typeof VOICE !== 'undefined' && VOICE.clips && VOICE.clips.length === narration.length) {
    narration.forEach((n, i) => {
      const c = VOICE.clips[i], start = n.t + VOICE.lead;
      events.push({ t: start, i: 'voice', a: [i], len: c.d });
      const next = narration[i + 1];
      const want = VOICE.lead + c.d + 0.9;
      n.d = Math.max(n.d, next ? Math.min(want, next.t - n.t - 0.3) : want);
      if (c.w && c.w.length === n.text.replace(/ \/ /g, ' ').trim().split(/\s+/).length) n.w = c.w.map(x => VOICE.lead + x);
    });
  }

  return {
    duration: total, chapters, narration, events, beds, render,
    resize() { }, seek() { },
    T, FAM, breathAt, pulseAt, ACTS,
  };
})();
