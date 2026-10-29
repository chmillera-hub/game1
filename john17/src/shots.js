// Shot definitions. Each shot's draw(ctx) returns { camera, layers, fx }.
// ctx: lt (seconds into the shot), gt (global time), dur, u (0..1 progress), take, cache.
(function () {
  const { f, clamp, lerp, rng, lg, rg, mix, shade, smooth, easeInOut } = U;
  const SH = {};
  window.SHOTS = SH;

  const once = (c, key, fn) => (c.cache[key] !== undefined ? c.cache[key] : (c.cache[key] = fn()));
  const idle = (gt, seed, amp = 1) => ({
    blink: U.blink(gt, seed),
    breathe: 0.5 + 0.5 * Math.sin(gt * 1.55 + seed),
    tilt: 1.3 * amp * U.noise(gt * 0.35, seed),
  });
  const talking = (gt) => (E.TL ? E.mouthAt(gt) : 0);
  const pick = (arr, take) => arr[(take - 1) % arr.length];
  const D = () => E.sharedDefs;

  // Lighting grades (full-frame overlays).
  const warmGrade = (cx = 0.18, cy = 0.42, k = 0.55) => S.tint('g-warm', [[0, '#ffb060', k], [0.5, '#ff9840', k * 0.33], [1, '#ff9840', 0]], cx, cy, 0.75);
  const coolShade = (left = false) => S.linearTint('g-cool', left ? [[0, '#6c5c74'], [0.45, '#ffffff'], [1, '#ffffff']] : [[0, '#ffffff'], [0.55, '#ffffff'], [1, '#6c5c74']], 0, 0, 1, 0.25);
  const nightGrade = () => S.linearTint('g-night', [[0, '#7088c0'], [1, '#30406a']], 0, 0, 0, 1);
  const grades = (k = {}) => [
    { key: 'gw', svg: warmGrade(k.cx, k.cy, k.k), par: 0, blend: 'soft-light' },
    { key: 'gc', svg: coolShade(k.left), par: 0, blend: 'multiply', opacity: k.cool === undefined ? 0.6 : k.cool },
  ];

  // ------------------------------------------------------------------ room backgrounds
  const roomA = (c) => once(c, 'roomA', () => S.roomWall({ win: { x: 815, y: 330, w: 290, h: 520 }, lamps: [[150, 800]], beamY: 110 }) +
    S.bokeh([[110, 1180, 70], [990, 1290, 60], [260, 1360, 46], [880, 1120, 40], [640, 1500, 52]], 5));
  const roomB = (c) => once(c, 'roomB', () => S.roomWall({ win: { x: 250, y: 330, w: 290, h: 520 }, lamps: [[930, 800]], beamY: 110, seed: 8 }) +
    S.bokeh([[980, 1170, 66], [100, 1300, 58], [820, 1380, 44], [420, 1480, 50]], 6));
  const roomWide = (c) => once(c, 'roomW', () => S.roomWall({ win: { x: 540, y: 290, w: 300, h: 500 }, lamps: [[110, 830], [970, 830]], beamY: 96, ledge: 1180, glowR: 620, seed: 11 }));

  const tableProps = () => [
    S.plate(250, 1488, 0.9), RIG.bread(250, 1470, 0.55), S.cup(420, 1500, 0.8), S.goblet(540, 1478, 0.9),
    S.breadPiece(650, 1492, 0.9, 6), S.jug(820, 1490, 0.8), S.cup(960, 1512, 0.75, '#8a4a2a'), S.oilLamp(80, 1500, 0.9), S.oilLamp(1010, 1460, 0.8),
  ];

  // ------------------------------------------------------------------ TITLE
  SH.title = {
    set: 'room',
    draw(c) {
      const z = 1 + 0.06 * easeInOut(c.lt / 10);
      const id = idle(c.gt, 3);
      const fg = once(c, 'fg', () => S.table({ y: 1690, props: [S.goblet(905, 1745, 1.0), S.breadPiece(160, 1740, 1, -8)] }));
      const jesus = RIG.bust({ who: 'jesus', id: 'jt', x: 540, y: 770, s: 1.58, pose: 'bread', lookY: 0.55, lid: 0.5, ...id, mouth: 0 });
      return {
        camera: { x: 0, y: -20 * easeInOut(c.lt / 10), z },
        layers: [
          { key: 'bg', svg: roomA(c), blur: 5, par: 0.5, bake: true },
          { key: 'fl', svg: S.flames(c.gt, [[150, 822, 1, 1]]), par: 0.5, blend: 'screen' },
          { key: 'ch', svg: D() + jesus, par: 1 },
          { key: 'fg', svg: fg, par: 1.15 },
          ...grades({ cx: 0.1, cy: 0.45 }),
        ],
        fx: { dust: { n: 34, seed: 4, alpha: 0.55 }, vignette: 0.85 },
      };
    },
  };

  // ------------------------------------------------------------------ JUDAS IN THE NIGHT
  RIG.cast.judas = {
    skin: '#bf8a64', skinShade: '#8e5c3e', hair: '#1a120c', hairShade: '#0e0906', hairHi: '#3a2a20', beard: '#1a120c', beardHi: '#3a2a20',
    robe: '#3a3442', robeShade: '#26222e', robeLine: '#16141c', mantle: '#2c2834', mantleShade: '#1c1a22', hairStyle: 'short', beardStyle: 'full',
  };
  SH.judas_night = {
    set: 'street',
    draw(c) {
      const take2 = c.take > 1;
      const bg = once(c, 'bg', () => S.sky('jn-sky', [[0, '#04070f'], [1, '#121c34']], -500, -500, 2080, 1000) + S.stars(60, -200, -200, 1480, 520, 9, 2) + S.moon(850, 190, 54));
      const wall = once(c, 'wall', () => S.stoneWall(-500, 330, 2080, 1160, 12, '#3a4456', '#161b24') +
        `<rect x="-500" y="1440" width="2080" height="60" fill="#1c222c"/>` + S.door(300, 1478, 230, 420, take2 ? 0 : 0.65) + S.torch(640, 760));
      const ground = once(c, 'gr', () => S.cobbles(1480, 540, 4));
      const p = take2 ? 0.35 + 0.65 * c.u : clamp((c.lt - 0.4) / Math.max(1, c.dur - 0.4));
      const walk = {
        who: 'judas', view: 'back', hood: '#2e2834', bag: true,
        x: take2 ? lerp(700, 860, p) : lerp(340, 720, p), y: take2 ? lerp(1560, 1500, p) : lerp(1640, 1540, p),
        s: take2 ? lerp(0.95, 0.75, p) : lerp(1.45, 1.05, p), phase: c.lt * 0.95,
      };
      const spill = take2 ? '' : `<defs>${rg('jn-spill', [[0, '#ffb455', 0.55], [1, '#ffb455', 0]])}</defs><path d="M190,1478 L410,1478 L640,1920 L-60,1920Z" fill="url(#jn-spill)"/>`;
      return {
        camera: { x: take2 ? 40 * c.u : 30 * c.u, y: 0, z: 1.02 + 0.05 * c.u },
        layers: [
          { key: 'sky', svg: bg, par: 0.2 },
          { key: 'wall', svg: wall, par: 0.7 },
          { key: 'gr', svg: ground, par: 0.9 },
          { key: 'spill', svg: spill, par: 0.9, blend: 'screen' },
          { key: 'fl', svg: S.flames(c.gt, [[640, 744, 1.1, 5]]), par: 0.7, blend: 'screen' },
          { key: 'ch', svg: D() + RIG.figure(walk), par: 1 },
          { key: 'gn', svg: nightGrade(), par: 0, blend: 'multiply', opacity: take2 ? 0.75 : 0.55 },
        ],
        fx: { dust: { n: 16, seed: 2, alpha: 0.35, color: '200,215,255' }, vignette: 0.95 },
      };
    },
  };

  // ------------------------------------------------------------------ WIDE UPPER ROOM
  SH.room_wide = {
    set: 'room',
    draw(c) {
      const t = c.gt, praying = c.take > 1, last = c.take >= 5;
      const disc = [];
      const bow = praying && !last ? { lookY: 0.55, lid: 0.55 } : {};
      const look = (base, sd) => (praying && !last ? {} : { lookX: base + 0.15 * U.noise(t * 0.5, sd) });
      const back = [
        RIG.bust({ who: 'andrew', id: 'wa', x: 150, y: 905, s: 0.6, turn: 0.35, ...idle(t, 11), ...look(0.75, 1), ...bow }),
        RIG.bust({ who: 'thomas', id: 'wt', x: 930, y: 905, s: 0.6, turn: -0.35, ...idle(t, 12), ...look(-0.75, 2), ...bow }),
        RIG.bust({ who: 'matthew', id: 'wm', x: 320, y: 880, s: 0.54, turn: 0.3, ...idle(t, 13), ...look(0.7, 3), ...bow }),
        RIG.bust({ who: 'james', id: 'wj', x: 760, y: 880, s: 0.54, turn: -0.3, ...idle(t, 14), ...look(-0.7, 4), ...bow }),
      ].join('');
      const jesusState = !praying ? { lookX: 0.6 * U.noise(t * 0.4, 9), mouth: 0 }
        : last ? { lookX: -0.3, smile: 0.35, mouth: talking(t) } : { open: 0, browSad: 0.2, mouth: talking(t) };
      const jo = { who: 'jesus', id: 'wjc', x: 540, y: 880, s: 0.78, pose: 'table', ...idle(t, 3, 0.6), ...jesusState };
      const jesus = RIG.bust({ ...jo, part: 'body' }), jesusArms = RIG.bust({ ...jo, part: 'arms' });
      const front = RIG.bust({ who: 'peter', id: 'wp', x: 165, y: 1070, s: 0.9, turn: 0.42, ...idle(t, 15), ...look(0.85, 5), ...bow, browSad: 0.4 }) +
        RIG.bust({ who: 'john', id: 'wk', x: 915, y: 1070, s: 0.88, turn: -0.42, ...idle(t, 16), ...look(-0.85, 6), ...bow, browSad: 0.35 });
      const table = once(c, 'table', () => S.table({ y: 1340, props: tableProps() }));
      const moves = [[-20, 0, 1.0, 1.05], [0, 0, 1.06, 1.0], [10, -10, 1.0, 1.06], [0, 20, 1.05, 1.0], [0, -10, 1.0, 1.07]];
      const [mx, my, z0, z1] = pick(moves, c.take);
      return {
        camera: { x: mx * c.u, y: my * c.u, z: lerp(z0, z1, easeInOut(c.u)) },
        layers: [
          { key: 'bg', svg: roomWide(c), par: 0.4, blur: 3, bake: true },
          { key: 'fl', svg: S.flames(t, [[110, 852, 0.9, 1], [970, 852, 0.9, 2]]), par: 0.4, blend: 'screen' },
          { key: 'back', svg: D() + back, par: 0.75 },
          { key: 'jes', svg: D() + jesus, par: 0.85 },
          { key: 'front', svg: D() + front, par: 1 },
          { key: 'table', svg: table, par: 0.85 },
          { key: 'jarms', svg: D() + jesusArms, par: 0.85 },
          { key: 'tfl', svg: S.flames(t, [[134, 1408, 0.7, 3], [1058, 1369, 0.6, 4]]), par: 0.85, blend: 'screen' },
          ...grades({ cx: 0.5, cy: 0.5, k: 0.45, cool: 0.35 }),
        ],
        fx: { dust: { n: 30, seed: 6, alpha: 0.5 }, vignette: 0.85 },
      };
    },
  };

  // ------------------------------------------------------------------ JESUS CLOSE-UPS
  SH.jesus_talk = {
    set: 'room',
    draw(c) {
      const t = c.gt;
      const v = pick([{ turn: -0.22, lookX: -0.55, smile: 0.15 }, { turn: -0.22, lookX: -0.55, smile: 0.2 }, { turn: 0.18, lookX: 0.5, smile: 0.35 }, { turn: -0.12, lookX: -0.35, smile: 0.45 }], c.take);
      const jesus = RIG.bust({ who: 'jesus', id: 'jk', x: 540, y: 830, s: 1.78, pose: 'rest', ...idle(t, 3), ...v, browSad: 0.15, mouth: talking(t) });
      return {
        camera: { x: 0, y: -10 * c.u, z: 1 + 0.05 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: roomA(c), blur: 7, par: 0.45, bake: true },
          { key: 'fl', svg: S.flames(t, [[150, 822, 1, 1]]), par: 0.45, blend: 'screen' },
          { key: 'ch', svg: D() + jesus, par: 1 },
          ...grades({ cx: 0.1, cy: 0.42 }),
        ],
        fx: { dust: { n: 30, seed: 3, alpha: 0.5 }, vignette: 0.85 },
      };
    },
  };

  SH.jesus_lookup = {
    set: 'room',
    draw(c) {
      const t = c.gt;
      const up = c.take === 1 ? smooth((c.lt - 1.3) / 1.6) : 1;
      const jesus = RIG.bust({
        who: 'jesus', id: 'ju', x: 540, y: 860, s: 1.74, pose: 'rest', ...idle(t, 3, 0.5),
        lookY: lerp(0.15, -0.95, up), lookX: lerp(-0.3, 0.22, up), browUp: 0.35 * up, browSad: 0.25, mouth: talking(t), pitch: -0.9 * up, tilt: 2 * up,
      });
      const shaft = `<defs>${lg('ju-shaft', [[0, '#dfe8ff', 0.5], [1, '#dfe8ff', 0]], 0, 0, 0, 1)}</defs><path d="M760,-100 L1000,-100 L760,1500 L240,1500Z" fill="url(#ju-shaft)"/>`;
      const rays = once(c, 'rays', () => S.rays('ju-rays', 820, -160, 22, 1700, '#ffe7b0', 0.35, 0, 0.45));
      return {
        camera: { x: 0, y: -12 * c.u, z: 1 + 0.06 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: roomA(c), blur: 7, par: 0.45, bake: true },
          { key: 'fl', svg: S.flames(t, [[150, 822, 1, 1]]), par: 0.45, blend: 'screen' },
          { key: 'shaft', svg: once(c, 'shaft', () => shaft), par: 0.5, blend: 'screen', blur: 30, bake: true, opacity: 0.55 + 0.35 * up },
          { key: 'rays', svg: rays, par: 0.3, blend: 'screen', blur: 6, bake: true, region: [820 - 1700, -160 - 1700, 3400, 3400], rot: c.gt * 2, pivot: [820, -160], opacity: up },
          { key: 'ch', svg: D() + jesus, par: 1 },
          ...grades({ cx: 0.1, cy: 0.42, cool: 0.5 }),
        ],
        fx: { dust: { n: 40, seed: 8, alpha: 0.6 }, vignette: 0.85 },
      };
    },
  };

  SH.jesus_pray = {
    set: 'room',
    draw(c) {
      const t = c.gt;
      const v = pick([{ x: 540, y: 740, s: 1.45 }, { x: 540, y: 820, s: 1.72 }, { x: 560, y: 760, s: 1.52, turn: 0.12 }, { x: 520, y: 800, s: 1.62, turn: -0.12 }], c.take);
      const jesus = RIG.bust({ who: 'jesus', id: 'jp', pose: 'pray', ...idle(t, 3, 0.5), ...v, open: 0, browSad: 0.22, mouth: talking(t) });
      const glow = `<circle cx="${v.x}" cy="${v.y + 430 * v.s}" r="${320 * v.s}" fill="url(#warmGlow)" opacity="${f(0.35 + 0.05 * U.noise(t * 4, 2))}"/>`;
      return {
        camera: { x: 0, y: -10 * c.u, z: 1 + 0.05 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: roomA(c), blur: 6, par: 0.45, bake: true },
          { key: 'fl', svg: S.flames(t, [[150, 822, 1, 1]]), par: 0.45, blend: 'screen' },
          { key: 'ch', svg: D() + jesus, par: 1 },
          { key: 'gl', svg: D() + glow, par: 1, blend: 'screen' },
          ...grades({ cx: 0.15, cy: 0.5 }),
        ],
        fx: { dust: { n: 34, seed: 5, alpha: 0.55 }, vignette: 0.85 },
      };
    },
  };

  SH.jesus_mcu = {
    set: 'room',
    draw(c) {
      const t = c.gt;
      const v = pick([{ lookY: -0.65, browUp: 0.3, lookX: 0.1 }, { open: 0, browSad: 0.2 }, { lookX: -0.45, smile: 0.3, turn: -0.12 }], c.take);
      const jo = { who: 'jesus', id: 'jm', x: 540, y: 790, s: 1.3, pose: 'table', ...idle(t, 3, 0.6), ...v, mouth: talking(t) };
      const jesus = RIG.bust({ ...jo, part: 'body' }), jesusArms = RIG.bust({ ...jo, part: 'arms' });
      const table = once(c, 'tb', () => S.table({ y: 1545, props: [S.cup(880, 1640, 1.0), S.breadPiece(200, 1630, 1.2, -6), S.oilLamp(990, 1610, 1)] }));
      return {
        camera: { x: 0, y: 0, z: 1.03 + 0.04 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: roomA(c), blur: 5, par: 0.45, bake: true },
          { key: 'fl', svg: S.flames(t, [[150, 822, 1, 1]]), par: 0.45, blend: 'screen' },
          { key: 'ch', svg: D() + jesus, par: 1 },
          { key: 'tb', svg: table, par: 1 },
          { key: 'jarms', svg: D() + jesusArms, par: 1 },
          { key: 'tfl', svg: S.flames(t, [[1048, 1596, 0.9, 6]]), par: 1, blend: 'screen' },
          ...grades({ cx: 0.12, cy: 0.45 }),
        ],
        fx: { dust: { n: 30, seed: 7, alpha: 0.5 }, vignette: 0.85 },
      };
    },
  };

  // ------------------------------------------------------------------ DISCIPLE CLOSE-UPS
  SH.peter_cu = {
    set: 'room',
    draw(c) {
      const t = c.gt;
      const v = pick([{ browSad: 0.6 }, { browSad: 0.35, lid: 0.2 }], c.take);
      const peter = RIG.bust({ who: 'peter', id: 'pc', x: 520, y: 860, s: 1.72, turn: 0.3, lookX: 0.62, ...idle(t, 21), ...v, lightSide: 1 });
      return {
        camera: { x: 0, y: -8 * c.u, z: 1 + 0.05 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: roomB(c), blur: 7, par: 0.45, bake: true },
          { key: 'fl', svg: S.flames(t, [[930, 822, 1, 7]]), par: 0.45, blend: 'screen' },
          { key: 'ch', svg: D() + peter, par: 1 },
          ...grades({ cx: 0.9, cy: 0.42, left: true }),
        ],
        fx: { dust: { n: 28, seed: 9, alpha: 0.5 }, vignette: 0.88 },
      };
    },
  };

  SH.john_cu = {
    set: 'room',
    draw(c) {
      const t = c.gt;
      const tear = c.take === 1 ? 0.6 * smooth(c.lt / Math.max(2, c.dur)) : c.take === 2 ? 0.7 : 0.85;
      const john = RIG.bust({ who: 'john', id: 'kc', x: 545, y: 870, s: 1.72, turn: -0.28, lookX: -0.6, ...idle(t, 22), browSad: 0.5, tear, smile: c.take === 3 ? 0.15 : 0 });
      return {
        camera: { x: 0, y: -8 * c.u, z: 1 + 0.05 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: roomA(c), blur: 7, par: 0.45, bake: true },
          { key: 'fl', svg: S.flames(t, [[150, 822, 1, 1]]), par: 0.45, blend: 'screen' },
          { key: 'ch', svg: D() + john, par: 1 },
          ...grades({ cx: 0.1, cy: 0.42 }),
        ],
        fx: { dust: { n: 28, seed: 10, alpha: 0.5 }, vignette: 0.88 },
      };
    },
  };

  SH.disciples = {
    set: 'room',
    draw(c) {
      const t = c.gt;
      const bow = c.take === 1 ? { lookY: 0.35, lid: 0.3 } : { lookY: 0.15 };
      const back = RIG.bust({ who: 'thomas', id: 'dt', x: 560, y: 800, s: 0.9, turn: 0.12, lookX: 0.4, ...idle(t, 31), ...bow, lightSide: 1 });
      const front = RIG.bust({ who: 'andrew', id: 'da', x: 230, y: 900, s: 1.02, turn: 0.3, lookX: 0.6, ...idle(t, 32), ...bow, lightSide: 1 }) +
        RIG.bust({ who: 'matthew', id: 'dm', x: 875, y: 920, s: 1.02, turn: 0.1, lookX: 0.45, ...idle(t, 33), ...bow, lightSide: 1, browSad: 0.3 });
      const table = once(c, 'tb', () => S.table({ y: 1600, props: [S.cup(300, 1690, 1.1), RIG.bread(640, 1660, 0.7), S.goblet(900, 1690, 1.1)] }));
      return {
        camera: { x: lerp(-40, 40, easeInOut(c.u)), y: 0, z: 1.06 },
        layers: [
          { key: 'bg', svg: roomB(c), blur: 6, par: 0.4, bake: true },
          { key: 'fl', svg: S.flames(t, [[930, 822, 1, 7]]), par: 0.4, blend: 'screen' },
          { key: 'back', svg: D() + back, par: 0.85 },
          { key: 'front', svg: D() + front, par: 1 },
          { key: 'tb', svg: table, par: 1.1 },
          ...grades({ cx: 0.88, cy: 0.42, left: true, cool: 0.45 }),
        ],
        fx: { dust: { n: 30, seed: 11, alpha: 0.5 }, vignette: 0.85 },
      };
    },
  };

  // ------------------------------------------------------------------ GOLGOTHA (foreshadowing)
  SH.golgotha = {
    set: 'golgotha',
    draw(c) {
      const sky = once(c, 'sky', () => S.sky('gg-sky', [[0, '#1c1430'], [0.35, '#4e2440'], [0.58, '#a4423e'], [0.72, '#e2844a'], [0.8, '#f6c26c'], [1, '#3a1a20']]) +
        `<circle cx="540" cy="1150" r="520" fill="url(#warmGlow)" opacity="0.9"/><circle cx="540" cy="1150" r="70" fill="#fff0c8"/>` +
        [[-100, 560, 700, 40], [500, 640, 800, 34], [120, 760, 600, 30], [640, 860, 560, 26]].map(([x, y, w, h], i) =>
          `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${h / 2}" fill="${i % 2 ? '#6a2c44' : '#4a2040'}" opacity="0.75"/><rect x="${x + 20}" y="${y + h - 8}" width="${w - 40}" height="6" rx="3" fill="#ff9a5a" opacity="0.5"/>`).join(''));
      const far = once(c, 'far', () => S.hill([[-300, 1240], [100, 1190], [400, 1230], [800, 1180], [1380, 1220]], '#4a2234') + S.hill([[-300, 1300], [200, 1270], [700, 1300], [1380, 1260]], '#331826'));
      const hill = once(c, 'hill', () => S.hill([[-300, 1520], [200, 1400], [440, 1300], [540, 1290], [640, 1300], [880, 1400], [1380, 1520]], '#1a0c14') +
        S.cross(540, 1300, 300, '#140a10') + S.cross(410, 1338, 220, '#140a10') + S.cross(670, 1338, 220, '#140a10'));
      const birds = `<path d="${[[300, 700], [340, 680], [720, 640], [760, 666]].map(([x, y], i) => { const xx = x + c.lt * 18 + i * 3, yy = y + Math.sin(c.lt * 3 + i) * 4; return `M${f(xx - 14)},${f(yy - 6)} Q${f(xx - 6)},${f(yy - 10)} ${f(xx)},${f(yy)} Q${f(xx + 6)},${f(yy - 10)} ${f(xx + 14)},${f(yy - 6)}`; }).join('')}" fill="none" stroke="#1a0c14" stroke-width="3"/>`;
      return {
        camera: { x: 0, y: -20 * c.u, z: 1 + 0.08 * easeInOut(c.u) },
        layers: [
          { key: 'sky', svg: sky, par: 0.2, blur: 5, bake: true },
          { key: 'rays', svg: once(c, 'rays', () => S.rays('gg-rays', 540, 1150, 28, 1400, '#ffd28a', 0.22, 0, 0.5)), par: 0.2, blend: 'screen', blur: 4, bake: true, region: [540 - 1400, 1150 - 1400, 2 * 1400, 2 * 1400], rot: c.gt * 1.5, pivot: [540, 1150] },
          { key: 'far', svg: far, par: 0.5 },
          { key: 'birds', svg: birds, par: 0.6 },
          { key: 'hill', svg: hill, par: 1 },
        ],
        fx: { dust: { n: 20, seed: 12, alpha: 0.4, color: '255,210,160' }, vignette: 0.9 },
      };
    },
  };

  // ------------------------------------------------------------------ COSMOS (before the world began)
  SH.cosmos = {
    set: 'cosmos',
    draw(c) {
      const bg = once(c, 'bg', () => `<rect x="-600" y="-600" width="2280" height="3120" fill="#03040b"/>` + S.nebula(4, ['#3a2a7a', '#1f4a7a', '#7a2a6a', '#c08a3a']) + S.stars(420, -500, -500, 2080, 2920, 31, 2.2));
      const near = once(c, 'near', () => S.stars(90, -400, -400, 1880, 2720, 41, 3.4, 1));
      const pulse = 0.85 + 0.15 * Math.sin(c.gt * 1.2);
      const light = `<circle cx="540" cy="900" r="560" fill="url(#whiteGlow)"/><circle cx="540" cy="900" r="90" fill="#ffffff"/>`;
      return {
        camera: { x: 0, y: 0, z: 1 + 0.12 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: bg, par: 0.3, rot: c.gt * 0.4 },
          { key: 'near', svg: near, par: 1.2 },
          { key: 'rays', svg: once(c, 'rays', () => S.rays('cs-rays', 540, 900, 48, 1500, '#fff0c8', 0.14, 0, 0.3)), par: 0.6, blend: 'screen', blur: 14, bake: true, region: [540 - 1500, 900 - 1500, 2 * 1500, 2 * 1500], rot: c.gt * 3, pivot: [540, 900] },
          { key: 'light', svg: once(c, 'light', () => light), par: 0.6, blend: 'screen', blur: 10, bake: true, scale: pulse },
        ],
        fx: { dust: { n: 30, seed: 13, alpha: 0.6, color: '255,240,210' }, vignette: 0.7 },
      };
    },
  };

  // ------------------------------------------------------------------ GLORY
  const gloryBG = (c, sunset) => once(c, 'gbg' + sunset, () => (sunset
    ? S.sky('gl-sky2', [[0, '#2a1d4a'], [0.35, '#6a3c74'], [0.6, '#e08a5a'], [0.75, '#f8c070'], [1, '#5a2a3a']])
    : S.sky('gl-sky', [[0, '#fff2cf'], [0.4, '#ffdc96'], [0.75, '#e9a858'], [1, '#b8742e']])) +
    `<circle cx="540" cy="${sunset ? 1250 : 760}" r="700" fill="url(#whiteGlow)" opacity="${sunset ? 0.55 : 0.85}"/>` +
    [[-100, 1500, 560, 120], [400, 1560, 700, 140], [-200, 1680, 900, 160], [600, 1700, 700, 150]].map(([x, y, w, h]) =>
      `<ellipse cx="${x + w / 2}" cy="${y}" rx="${w / 2}" ry="${h / 2}" fill="${sunset ? '#f2b48a' : '#fff6e0'}" opacity="0.8"/>`).join(''));
  const glory = (c, sunset) => {
    const t = c.gt;
    const jesus = RIG.bust({ who: 'jesus', id: 'jg', x: 540, y: 760, s: 1.32, pose: 'open', halo: true, ...idle(t, 3, 0.5), lookY: 0.05, smile: sunset ? 0.5 : 0.35, mouth: sunset ? 0 : talking(t) });
    return {
      camera: { x: 0, y: -10 * c.u, z: 1 + 0.05 * easeInOut(c.u) },
      layers: [
        { key: 'bg', svg: gloryBG(c, sunset), par: 0.3, blur: 6, bake: true },
        { key: 'rays', svg: once(c, 'rays', () => S.rays('gl-rays', 540, 740, 30, 1600, '#ffffff', sunset ? 0.25 : 0.5, 0, 0.42)), par: 0.3, blend: 'screen', blur: 3, bake: true, region: [540 - 1600, 740 - 1600, 2 * 1600, 2 * 1600], rot: c.gt * 2.5, pivot: [540, 740] },
        { key: 'ch', svg: D() + jesus, par: 1 },
        { key: 'soft', svg: S.tint('gl-soft', [[0, '#fff8e8', 0.0], [0.6, '#fff0d0', 0.12], [1, '#ffe0a0', 0.4]], 0.5, 0.45, 0.8), par: 0, blend: 'screen' },
      ],
      fx: { dust: { n: 46, seed: 14, alpha: 0.75, color: '255,246,220', dy: 0.6 }, vignette: sunset ? 0.7 : 0.35 },
    };
  };
  SH.glory = { set: 'glory', draw: (c) => glory(c, false) };
  SH.glory_end = { set: 'glory_end', draw: (c) => glory(c, true) };

  // ------------------------------------------------------------------ CITY AT NIGHT
  SH.city_night = {
    set: 'city',
    draw(c) {
      const dark = c.take > 1;
      const sky = once(c, 'sky', () => S.sky('cn-sky', [[0, '#03060f'], [0.6, '#0e1a36'], [1, '#22355e']], -500, -500, 2080, 1900) + S.stars(110, -300, -300, 1680, 1100, 51, 2.2) + S.moon(250, 330, 62));
      const far = once(c, 'far', () => S.hill([[-300, 1020], [200, 960], [600, 1000], [1000, 940], [1380, 980]], '#0e172c') +
        // temple on the far right
        `<rect x="760" y="830" width="300" height="170" fill="#1a2440"/><rect x="800" y="760" width="220" height="80" fill="#1e2a48"/>` +
        Array.from({ length: 8 }, (_, i) => `<rect x="${772 + i * 36}" y="850" width="12" height="140" fill="#2a3858"/>`).join(''));
      const houses = once(c, 'houses', () => {
        let s = '';
        const r = rng(61);
        for (let i = 0; i < 12; i++) s += S.house(-200 + i * 120 + r() * 40, 1120 + r() * 30, 110 + r() * 60, 120 + r() * 90, '#1b2640', 100 + i, 0.25);
        for (let i = 0; i < 8; i++) s += S.house(-260 + i * 190 + r() * 40, 1300 + r() * 30, 170 + r() * 50, 170 + r() * 80, '#222e4c', 200 + i, 0.18);
        return s;
      });
      const main = once(c, 'main', () => {
        // two-storey house with an outside stair; the upper room window is lit
        let s = `<defs>${lg('cn-wall', [[0, '#34405f'], [1, '#222b44']], 0, 0, 1, 0)}</defs>`;
        s += `<rect x="300" y="1040" width="480" height="760" fill="url(#cn-wall)"/>`;
        s += `<rect x="290" y="1026" width="500" height="20" fill="#46557a"/>`;
        s += `<rect x="290" y="1388" width="500" height="12" fill="#2a3452"/>`;
        s += S.stoneWall(300, 1400, 480, 400, 71, '#2a3452', '#151b2c');
        s += `<path d="M300,1720 L150,1720 L150,1790 L300,1790Z M300,1640 L190,1640 L190,1720 L300,1720Z M300,1560 L230,1560 L230,1640 L300,1640Z M300,1480 L262,1480 L262,1560 L300,1560Z" fill="#1c2438" stroke="#10151f" stroke-width="3"/>`;
        s += `<path d="${S.archPath(540, 1125, 190, 220)}" fill="#ffbf62"/>`;
        s += `<path d="${S.archPath(540, 1125, 190, 220)}" fill="none" stroke="#141b2e" stroke-width="14"/>`;
        // lattice
        s += `<path d="M540,1125 L540,1345 M445,1215 L635,1215 M445,1280 L635,1280" stroke="#3a2412" stroke-width="7"/>`;
        s += `<circle cx="540" cy="1190" r="16" fill="#fff4c8" opacity="0.9"/>`;
        s += `<path d="${S.archPath(420, 1520, 90, 150)}" fill="#0f1422"/><path d="${S.archPath(660, 1520, 90, 150)}" fill="#0f1422"/>`;
        s += `<rect x="-400" y="1790" width="1880" height="400" fill="#121827"/>`;
        s += S.house(-260, 1830, 330, 260, '#1a2236', 301, 0.15) + S.house(840, 1850, 360, 300, '#1a2236', 302, 0.2);
        return s;
      });
      const glow = `<circle cx="540" cy="1230" r="${f(400 + 20 * U.noise(c.gt * 3, 4))}" fill="url(#warmGlow)" opacity="0.85"/>`;
      const fog = dark ? `<defs>${rg('cn-fog', [[0, '#000000', 0.8], [1, '#000000', 0]])}</defs>` +
        [0, 1, 2, 3, 4].map((i) => `<ellipse cx="${f((i * 300 + c.gt * 30) % 1600 - 260)}" cy="${1500 + (i % 2) * 120}" rx="420" ry="200" fill="url(#cn-fog)"/>`).join('') : '';
      return {
        camera: { x: 0, y: lerp(0, 80, easeInOut(c.u)), z: lerp(1, dark ? 1.25 : 1.15, easeInOut(c.u)) },
        layers: [
          { key: 'sky', svg: sky, par: 0.15 },
          { key: 'far', svg: far, par: 0.35 },
          { key: 'houses', svg: houses, par: 0.6 },
          { key: 'main', svg: main, par: 1 },
          { key: 'glow', svg: D() + glow, par: 1, blend: 'screen' },
          { key: 'fog', svg: fog, par: 1.1 },
        ],
        fx: { dust: { n: 14, seed: 15, alpha: 0.3, color: '200,215,255' }, vignette: 0.95 },
      };
    },
  };

  // ------------------------------------------------------------------ SCROLL
  SH.scroll = {
    set: 'scroll',
    draw(c) {
      const bg = once(c, 'bg', () => `<rect x="-500" y="-500" width="2080" height="2920" fill="#160d07"/>` +
        `<defs>${lg('scr-table', [[0, '#2a190d'], [1, '#6a4225']])}</defs><path d="M-500,520 L1580,520 L1580,2400 L-500,2400Z" fill="url(#scr-table)"/>` +
        S.bokeh([[150, 300, 80], [880, 240, 60], [560, 380, 40]], 9) + S.scroll(540, 1080, 640, 560, 3));
      const lamp = once(c, 'lamp', () => S.oilLamp(850, 1560, 2.2));
      return {
        camera: { x: lerp(30, -30, easeInOut(c.u)), y: lerp(20, -20, easeInOut(c.u)), z: 1.08 + 0.05 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: bg, par: 0.9 },
          { key: 'lamp', svg: lamp, par: 1 },
          { key: 'fl', svg: S.flames(c.gt, [[978, 1529, 2.0, 3]]), par: 1, blend: 'screen' },
          ...grades({ cx: 0.85, cy: 0.75, k: 0.7, left: true, cool: 0.4 }),
        ],
        fx: { dust: { n: 40, seed: 16, alpha: 0.6 }, vignette: 0.95 },
      };
    },
  };

  // ------------------------------------------------------------------ SENT INTO THE WORLD (sunrise road)
  SH.road = {
    set: 'road',
    draw(c) {
      const sky = once(c, 'sky', () => S.sky('rd-sky', [[0, '#2c2458'], [0.3, '#5a3c7a'], [0.48, '#c9686a'], [0.56, '#f4a65a'], [0.6, '#ffe6a0'], [1, '#ffe6a0']], -500, -500, 2080, 1560) +
        `<circle cx="540" cy="1040" r="600" fill="url(#whiteGlow)" opacity="0.7"/><circle cx="540" cy="1050" r="80" fill="#fff8e0"/>`);
      const land = once(c, 'land', () => {
        let s = S.hill([[-300, 1060], [200, 1030], [540, 1050], [900, 1020], [1380, 1060]], '#5a3a4a');
        s += `<defs>${lg('rd-ground', [[0, '#4a2c2a'], [1, '#1e120e']])}${lg('rd-road', [[0, '#e0a868'], [1, '#7a4c2c']])}</defs>`;
        s += `<rect x="-500" y="1060" width="2080" height="1400" fill="url(#rd-ground)"/>`;
        s += `<path d="M528,1060 L552,1060 L900,2000 L180,2000Z" fill="url(#rd-road)"/>`;
        s += `<path d="M528,1060 L180,2000 M552,1060 L900,2000" stroke="#3a2214" stroke-width="3" opacity="0.6"/>`;
        const col = '#24141c';
        s += S.cypress(110, 1120, 1.4, col) + S.cypress(980, 1110, 1.3, col) + S.cypress(250, 1080, 0.7, col) + S.cypress(830, 1076, 0.6, col);
        s += S.pine(-60, 1300, 1.25, col) + S.pine(1140, 1260, 1.15, col) + S.pine(330, 1090, 0.45, col) + S.pine(760, 1084, 0.4, col);
        return s;
      });
      const walkers = [['peter', 0.0], ['andrew', 0.12], ['john', 0.22], ['thomas', 0.36], ['matthew', 0.5]].map(([who, d], i) => {
        const p = clamp(0.1 + d + c.lt * 0.018);
        const y = lerp(1900, 1110, Math.pow(p, 0.7)), s = lerp(1.5, 0.12, Math.pow(p, 0.7));
        const x = 540 + (i % 2 ? 1 : -1) * lerp(110, 4, Math.pow(p, 0.7)) * (0.6 + 0.2 * i);
        return { y, svg: RIG.figure({ who, view: 'back', x, y, s, phase: c.lt * 0.9 + i * 0.3, shadow: true }) };
      }).sort((a, b) => a.y - b.y).map((w) => w.svg).join('');
      return {
        camera: { x: 0, y: -20 * c.u, z: 1 + 0.06 * easeInOut(c.u) },
        layers: [
          { key: 'sky', svg: sky, par: 0.2 },
          { key: 'rays', svg: once(c, 'rays', () => S.rays('rd-rays', 540, 1050, 32, 1500, '#ffffff', 0.3, 0, 0.45)), par: 0.2, blend: 'screen', blur: 3, bake: true, region: [540 - 1500, 1050 - 1500, 2 * 1500, 2 * 1500], rot: c.gt * 1.5, pivot: [540, 1050] },
          { key: 'land', svg: land, par: 0.8 },
          { key: 'walk', svg: D() + walkers, par: 1 },
          { key: 'warm', svg: warmGrade(0.5, 0.55, 0.4), par: 0, blend: 'soft-light' },
        ],
        fx: { dust: { n: 30, seed: 17, alpha: 0.6, color: '255,230,190' }, vignette: 0.8 },
      };
    },
  };

  // ------------------------------------------------------------------ CANDLES (the message spreads)
  SH.candles = {
    set: 'candles',
    draw(c) {
      const t = c.gt;
      const people = [
        { kind: 'female', seed: 101, x: 150 }, { kind: 'male', seed: 102, x: 410 }, { kind: 'male', seed: 103, x: 680, old: true }, { kind: 'female', seed: 104, x: 935 },
      ];
      let chars = '', glow = '';
      people.forEach((pp, i) => {
        const lit = i === 0 ? smooth((c.lt - 0.2) / 0.5) : smooth((c.lt - 3.4 - (i - 1) * 0.95) / 0.5);
        const { pal } = RIG.person(pp.seed, { kind: pp.kind, old: pp.old });
        chars += RIG.bust({ pal, id: 'cd' + i, x: pp.x, y: 900, s: 0.66, pose: 'candle', flame: lit, t, seed: i + 1, lookY: 0.35, lid: 0.25, ...idle(t, 40 + i), smile: 0.25 * lit });
        glow += `<circle cx="${pp.x}" cy="${f(900 + 410 * 0.66)}" r="${f(260 * (0.95 + 0.05 * U.noise(t * 5, i)))}" fill="url(#warmGlow)" opacity="${f(0.75 * lit)}"/>`;
      });
      const dark = once(c, 'bg', () => S.sky('cd-bg', [[0, '#05060c'], [1, '#140c12']]) + S.stars(40, -200, -200, 1480, 800, 71, 1.6, 0.6));
      return {
        camera: { x: 0, y: 0, z: 1 + 0.06 * easeInOut(c.u) },
        layers: [
          { key: 'bg', svg: dark, par: 0.3 },
          { key: 'ch', svg: D() + chars, par: 1 },
          { key: 'shade', svg: S.linearTint('cd-sh', [[0, '#3a3450'], [0.5, '#8a7a90'], [1, '#3a3450']], 0, 0, 0, 1), par: 0, blend: 'multiply' },
          { key: 'glow', svg: D() + glow, par: 1, blend: 'screen' },
        ],
        fx: { dust: { n: 24, seed: 18, alpha: 0.5 }, vignette: 0.9 },
      };
    },
  };

  // ------------------------------------------------------------------ CROWD OF BELIEVERS
  SH.crowd = {
    set: 'crowd',
    draw(c) {
      const t = c.gt;
      const rows = [
        { n: 11, y: 860, s: 0.32, blur: 2.4, seed: 300, spread: 1320 },
        { n: 8, y: 1010, s: 0.46, blur: 1.2, seed: 400, spread: 1260 },
        { n: 5, y: 1210, s: 0.7, blur: 0, seed: 500, spread: 1200 },
      ];
      const layers = [];
      const sky = once(c, 'sky', () => S.sky('cr-sky', [[0, '#0a0f24'], [0.35, '#2a2350'], [0.55, '#7a4a6a'], [0.7, '#d08a6a'], [1, '#20141c']]) +
        `<circle cx="540" cy="760" r="620" fill="url(#whiteGlow)" opacity="0.45"/>`);
      layers.push({ key: 'sky', svg: sky, par: 0.2 });
      layers.push({ key: 'rays', svg: once(c, 'rays', () => S.rays('cr-rays', 540, -120, 26, 2100, '#ffe8b8', 0.3, 80, 0.4)), par: 0.2, blend: 'screen', blur: 6, bake: true, region: [540 - 2100, -120 - 2100, 2 * 2100, 2 * 2100], rot: 4 * Math.sin(t * 0.3), pivot: [540, -120] });
      rows.forEach((row, ri) => {
        const animate = ri === 2;
        const build = () => {
          let s = '', g = '';
          for (let i = 0; i < row.n; i++) {
            const x = 540 + (i - (row.n - 1) / 2) * (row.spread / row.n) + (ri % 2 ? 20 : -10);
            const { pal, kind } = RIG.person(row.seed + i);
            const sc = row.s * (kind === 'child' ? 0.82 : 1);
            const yy = row.y + (kind === 'child' ? 60 * row.s : 0) + ((i * 37) % 3) * 6;
            s += RIG.bust({ pal, id: `cr${ri}_${i}`, x, y: yy, s: sc, pose: 'candle', flame: 1, t: animate ? t : 0, seed: i + ri * 10, lookY: -0.4, browUp: 0.2, smile: 0.3,
              turn: ((i % 3) - 1) * 0.15, ...(animate ? idle(t, 60 + i) : {}) });
            g += `<circle cx="${f(x)}" cy="${f(yy + 410 * sc)}" r="${f(260 * sc)}" fill="url(#warmGlow)" opacity="0.8"/>`;
          }
          return { s, g };
        };
        const r = animate ? build() : once(c, 'row' + ri, build);
        layers.push({ key: 'row' + ri, svg: D() + r.s, par: 0.6 + ri * 0.2, blur: row.blur, bake: !animate });
        layers.push({ key: 'rowg' + ri, svg: D() + r.g, par: 0.6 + ri * 0.2, blend: 'screen', blur: row.blur, bake: !animate, opacity: 0.85 + 0.1 * U.noise(t * 4, ri) });
      });
      layers.push({ key: 'shade', svg: S.linearTint('cr-sh', [[0, '#ffffff'], [0.55, '#d8c8d0'], [1, '#4a3a50']], 0, 0, 0, 1), par: 0, blend: 'multiply' });
      return { camera: { x: 0, y: 0, z: lerp(1.14, 1.0, easeInOut(c.u)) }, layers, fx: { dust: { n: 30, seed: 19, alpha: 0.6, color: '255,236,200' }, vignette: 0.8 } };
    },
  };

  // ------------------------------------------------------------------ KIDRON VALLEY
  SH.kidron = {
    set: 'kidron',
    draw(c) {
      const t = c.gt;
      const sky = once(c, 'sky', () => S.sky('kd-sky', [[0, '#03060f'], [0.55, '#0f1c3a'], [1, '#26365e']], -600, -500, 3600, 1900) + S.stars(160, -500, -400, 3400, 1200, 81, 2.2) + S.moon(820, 330, 58));
      const far = once(c, 'far', () => {
        // Jerusalem's wall and gate on the left, the Mount of Olives rising on the right
        let s = S.hill([[-600, 1020], [400, 1000], [900, 960], [1500, 900], [2100, 860], [2900, 930]], '#0d1730');
        s += S.stoneWall(-600, 760, 980, 330, 33, '#26314e', '#141b2c');
        for (let x = -600; x < 380; x += 64) s += `<rect x="${x}" y="736" width="36" height="30" fill="#26314e"/>`;
        s += `<path d="${S.archPath(160, 900, 120, 190)}" fill="#ffb84a" opacity="0.9"/>`;
        s += `<rect x="-420" y="560" width="360" height="180" fill="#1e2846"/><rect x="-380" y="500" width="280" height="70" fill="#222d4e"/>`;
        s += S.house(-560, 760, 140, 120, '#1c2640', 7, 0.5) + S.house(10, 760, 120, 90, '#1e2844', 8, 0.5);
        return s;
      });
      const mid = once(c, 'mid', () => {
        let s = `<rect x="-600" y="1240" width="3600" height="1400" fill="#0b1322"/>`;
        s += `<path d="M-600,1390 C0,1370 600,1410 1200,1385 C1800,1360 2400,1400 3000,1380" fill="none" stroke="#5a7aaa" stroke-width="7" opacity="0.55"/>`;
        s += S.olive(980, 1300, 0.8, 5, '#121a28', '#1a2840', '#2a3e5c') + S.olive(1300, 1290, 0.9, 6, '#121a28', '#1a2840', '#2a3e5c') +
          S.olive(1640, 1300, 0.85, 7, '#121a28', '#1a2840', '#2a3e5c') + S.olive(1960, 1290, 0.95, 8, '#121a28', '#1a2840', '#2a3e5c') + S.olive(2300, 1300, 0.9, 9, '#121a28', '#1a2840', '#2a3e5c');
        return s;
      });
      const ground = once(c, 'ground', () => {
        let s = `<defs>${lg('kd-gr', [[0, '#141e30'], [1, '#05080e']])}</defs>`;
        s += `<path d="M-600,1460 C200,1440 900,1480 1600,1450 C2200,1430 2700,1450 3200,1440 L3200,2600 L-600,2600Z" fill="url(#kd-gr)"/>`;
        s += `<path d="M-600,1600 C200,1585 900,1615 1600,1595 C2200,1580 2700,1595 3200,1590" fill="none" stroke="#2c3a58" stroke-width="110" stroke-linecap="round"/>`;
        const r = rng(91);
        for (let i = 0; i < 40; i++) { const x = -500 + r() * 3600, y = 1600 + r() * 300; s += `<ellipse cx="${f(x)}" cy="${f(y)}" rx="${f(14 + r() * 30)}" ry="${f(6 + r() * 10)}" fill="#1c2638" opacity="0.8"/>`; }
        s += S.olive(2500, 1700, 1.6, 12, '#0c121c', '#121c2c', '#1e2c44') + S.olive(-380, 1760, 1.5, 13, '#0c121c', '#121c2c', '#1e2c44');
        return s;
      });
      // the procession: Jesus leads, the eleven follow in two loose rows
      const order = [['jesus', 0, 0], ['peter', 1, 1], ['john', 2, 0], ['james', 3, 1], ['andrew', 4, 0], ['thomas', 5, 1], ['matthew', 6, 0],
        ['peter', 7, 1, '#5a4a3a'], ['andrew', 8, 0, '#3f4a5a'], ['james', 9, 1, '#6a3a3a'], ['thomas', 10, 0, '#4a5a3a'], ['matthew', 11, 1, '#5a4060']];
      const lead = 640 + c.lt * 62;
      const items = order.map(([who, i, row, robe]) => {
        const x = lead - i * 104 - row * 14, y = row ? 1575 : 1640;
        const pal = robe ? { robe, robeShade: shade(robe, -0.25) } : {};
        return { y, svg: RIG.figure({ who, pal, view: 'side', x, y, s: row ? 0.86 : 0.96, phase: c.lt * 0.95 + i * 0.37, lantern: i === 1, shadow: true }) };
      }).sort((a, b) => a.y - b.y).map((w) => w.svg).join('');
      const lx = lead - 104 - 14 + (10 + 22 * Math.sin((c.lt * 0.95 + 0.37) * Math.PI * 2)) * 0.86, ly = 1575 - 130 * 0.86;
      const fl = `<circle cx="${f(lx + 6)}" cy="${f(ly + 10)}" r="${f(190 + 10 * U.noise(t * 5, 3))}" fill="url(#warmGlow)" opacity="0.75"/>`;
      const camx = lerp(0, 820, c.u);
      return {
        camera: { x: camx, y: 60, z: 1.0 },
        layers: [
          { key: 'sky', svg: sky, par: 0.1 },
          { key: 'far', svg: far, par: 0.3 },
          { key: 'mid', svg: mid, par: 0.6 },
          { key: 'ground', svg: ground, par: 1 },
          { key: 'walk', svg: D() + items, par: 1 },
          { key: 'fl', svg: D() + fl, par: 1, blend: 'screen' },
          { key: 'gn', svg: nightGrade(), par: 0, blend: 'multiply', opacity: 0.3 },
        ],
        fx: { dust: { n: 12, seed: 20, alpha: 0.3, color: '200,215,255' }, vignette: 0.95, subY: 1150 },
      };
    },
  };

  // ------------------------------------------------------------------ END CARD
  SH.end = {
    set: 'end',
    fadeIn: 1.0,
    draw(c) {
      const bg = once(c, 'bg', () => S.sky('en-sky', [[0, '#120c24'], [0.35, '#3a2450'], [0.5, '#a0605a'], [0.58, '#f0b070'], [0.7, '#5a2c3a'], [1, '#0c0810']]) +
        `<circle cx="540" cy="1040" r="640" fill="url(#whiteGlow)" opacity="0.55"/>`);
      return {
        camera: { x: 0, y: 0, z: 1 + 0.04 * c.u },
        layers: [
          { key: 'bg', svg: D() + bg, par: 0.3 },
          { key: 'rays', svg: once(c, 'rays', () => S.rays('en-rays', 540, 1040, 32, 1700, '#ffe2b0', 0.35, 0, 0.45)), par: 0.3, blend: 'screen', blur: 4, bake: true, region: [540 - 1700, 1040 - 1700, 2 * 1700, 2 * 1700], rot: c.gt * 2, pivot: [540, 1040] },
        ],
        fx: { dust: { n: 40, seed: 21, alpha: 0.7, color: '255,236,200', dy: 0.5 }, vignette: 0.75 },
      };
    },
  };
})();
