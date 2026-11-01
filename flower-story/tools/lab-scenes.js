/* Model sheets for the art kit (not part of the film). View: tools/lab.html?t=0 */
(function () {
  const { W, H } = U;
  const label = (ctx, s, x, y) => { ctx.font = Art.font(20, 'sans', 700); ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.fillText(s, x, y); ctx.textAlign = 'left'; };
  // 1: cast standing + walking
  Film.scene({ id: 'cast', order: 0, title: 'Cast', duration: 10, fadeIn: 0, fadeOut: 0, post: { letterbox: 0, vignette: 0, grain: 0 },
    render(ctx, t) {
      const P = Art.TOD.morning;
      Art.sky(ctx, P); Art.ground(ctx, { y: 900, color: P.ground, color2: P.ground2, amp: 0 });
      const keys = ['me', 'h1', 'h2', 'h3', 'h4', 'emb'];
      keys.forEach((k, i) => {
        const x = 170 + i * 300;
        Art.person(ctx, { x, y: 470, look: k, t, s: 1 });
        label(ctx, k, x, 505);
        Art.person(ctx, { x, y: 880, look: k, t, walk: t * 5 + i, s: 1 });
      });
    } });
  // 2: poses & gestures
  Film.scene({ id: 'poses', order: 1, title: 'Poses', duration: 10, fadeIn: 0, fadeOut: 0, post: { letterbox: 0, vignette: 0, grain: 0 },
    render(ctx, t) {
      ctx.fillStyle = '#5c6f80'; ctx.fillRect(0, 0, W, H);
      const list = [['wave', {}], ['shrug', {}], ['point', {}], ['facepalm', {}], ['hips', {}], ['hold', {}], ['cheer', {}], ['chin', {}], ['heart', {}], ['phone', {}], ['pocket', {}], ['give', {}]];
      list.forEach(([g, o], i) => {
        const x = 110 + (i % 6) * 320, y = i < 6 ? 480 : 1000;
        Art.person(ctx, Object.assign({ x, y, look: i % 2 ? 'h1' : 'me', t, gesture: g, s: 1.1 }, o));
        label(ctx, g, x, y + 35 - (i < 6 ? 0 : 50));
      });
    } });
  Film.scene({ id: 'poses2', order: 2, title: 'Poses 2', duration: 10, fadeIn: 0, fadeOut: 0, post: { letterbox: 0, vignette: 0, grain: 0 },
    render(ctx, t) {
      ctx.fillStyle = '#6d5c80'; ctx.fillRect(0, 0, W, H);
      const list = [['sit', 'me'], ['bench', 'me'], ['crouch', 'me'], ['kneel', 'me'], ['stand', 'emb'], ['walk', 'h2']];
      list.forEach(([p, k], i) => {
        const x = 160 + i * 310;
        ctx.fillStyle = '#3d3350'; ctx.fillRect(x - 140, 700, 280, 4);
        if (p === 'bench') { ctx.fillStyle = '#8a6a4a'; ctx.fillRect(x - 60, 700 - 72, 120, 12); }
        Art.person(ctx, { x, y: 700, look: k, t, pose: p, walk: p === 'walk' ? t * 5 : undefined, tired: p === 'walk' ? 1 : 0, face: p === 'walk' ? { eyes: 'distant', sweat: 1, smile: -0.2 } : {} });
        label(ctx, p, x, 740);
      });
      // three-quarter vs front
      [0, 0.5, 1].forEach((turn, i) => {
        const x = 500 + i * 300;
        Art.person(ctx, { x, y: 1040, look: 'me', t, head: { turn }, face: { smile: 0.8, eyes: 'sparkle' } });
        label(ctx, 'turn ' + turn, x, 1070);
      });
      Art.person(ctx, { x: 1500, y: 1040, look: 'h4', t, facing: -1, face: { smile: 0.3, talk: 1 } });
      label(ctx, 'facing -1, talk', 1500, 1070);
    } });
  // 3: faces
  Film.scene({ id: 'faces', order: 3, title: 'Faces', duration: 10, fadeIn: 0, fadeOut: 0, post: { letterbox: 0, vignette: 0, grain: 0 },
    render(ctx, t) {
      ctx.fillStyle = '#2f3a46'; ctx.fillRect(0, 0, W, H);
      const faces = [
        ['open', { eyes: 'open', smile: 0.2 }], ['happy', { eyes: 'happy', smile: 0.9, open: 0.4 }], ['sparkle beam', { eyes: 'sparkle', smile: 1, open: 0.5 }],
        ['wide', { eyes: 'wide', mouth: 'o', open: 0.5, browUp: 1 }], ['roll', { eyes: 'roll', smile: -0.2 }], ['distant', { eyes: 'distant', smile: -0.1, sweat: 1 }],
        ['flat', { eyes: 'flat', smile: 0 }], ['smirk', { eyes: 'flat', smirk: 1, smile: 0.2 }], ['closed', { eyes: 'closed', smile: 0.5 }],
        ['squeeze laugh', { eyes: 'squeeze', smile: 1, open: 1 }], ['angry', { eyes: 'open', brow: -1, smile: -0.6 }], ['worried', { eyes: 'open', brow: 1, smile: -0.4 }],
      ];
      faces.forEach(([n, f], i) => {
        const x = 160 + (i % 6) * 320, y = i < 6 ? 260 : 700;
        Art.head(ctx, x, y, 110, i % 3 === 2 ? 'emb' : i % 3 === 1 ? 'h3' : 'me', Object.assign({ blink: 0 }, f), { t });
        label(ctx, n, x, y + 160);
      });
    } });
  // 4: flowers & emotions
  Film.scene({ id: 'flowers', order: 4, title: 'Flowers', duration: 10, fadeIn: 0, fadeOut: 0, post: { letterbox: 0, vignette: 0, grain: 0 },
    render(ctx, t) {
      const P = Art.TOD.golden; Art.sky(ctx, P);
      ctx.fillStyle = P.ground; ctx.fillRect(0, 520, W, H);
      const kinds = [['hero', {}], ['hero bloom .3', { bloom: 0.3 }], ['hero sat 0', { sat: 0 }], ['hero glow', { glow: 1 }], ['daisy', { kind: 'daisy', colors: { petal: '#ffffff', tip: '#fffaf0', inner: '#f0e6c8' } }], ['tulip', { kind: 'tulip', colors: { petal: '#ff8a3d', tip: '#ffd36b', inner: '#c2410c' } }], ['bell', { kind: 'bell', colors: { petal: '#7b8cff' } }], ['rose', { kind: 'rose', colors: { petal: '#e63946', inner: '#8d0f1d' } }], ['dusty droop', { kind: 'wild', droop: 0.6, dust: 1, colors: { petal: '#d8c25a', tip: '#efe2a0', inner: '#a08a2a' } }]];
      kinds.forEach(([n, o], i) => {
        const x = 110 + i * 210;
        Art.flower(ctx, Object.assign({ x, y: 500, t, s: 1 }, o));
        label(ctx, n, x, 530);
      });
      Art.flower(ctx, { x: 300, y: 1060, t, s: 2.4, glow: 0.6 });
      Art.pot(ctx, 700, 1000, 90, 80); Art.flower(ctx, { x: 700, y: 935, t, s: 0.8, kind: 'tulip', colors: { petal: '#ff8a3d', tip: '#ffd36b', inner: '#c2410c' } });
      const emos = ['wonder', 'calm', 'heart', 'spark', 'dream', 'shy'];
      const arms = ['idle', 'facepalm', 'wave', 'tap', 'cheer', 'shrug'];
      emos.forEach((e, i) => {
        const x = 950 + i * 160;
        Art.emotion(ctx, { x, y: 820, s: 1.3, color: Art.EMO[e], t, arms: arms[i], seed: i });
        label(ctx, e + '/' + arms[i], x, 850);
      });
      Art.bubble(ctx, "Hey, you guys go ahead.", { x: 1300, y: 960, tx: 1150, ty: 1050 });
    } });
  // 5: environment & text
  Film.scene({ id: 'env', order: 5, title: 'Env', duration: 10, fadeIn: 0, fadeOut: 0,
    render(ctx, t) {
      const P = Art.TOD.morning, off = t * 120;
      Art.sky(ctx, P, { horizon: 640 });
      Art.sun(ctx, 1500, 210, 46, P.sun, 1);
      Art.clouds(ctx, { seed: 2, count: 5, y0: 170, y1: 330, offset: off * 0.05, color: '#ffffff', alpha: 0.75 });
      Art.ridge(ctx, { seed: 4, y: 620, amp: 190, color: P.far, offset: off * 0.08 });
      Art.summit(ctx, { x: 1350, y: 640, h: 430, w: 700, P, t });
      Art.fog(ctx, { y: 620, h: 160, color: P.fog, alpha: 0.6 });
      Art.ridge(ctx, { seed: 9, y: 700, amp: 120, color: P.mid, offset: off * 0.18 });
      Art.forest(ctx, { seed: 3, y: 740, offset: off * 0.35, spacing: 70, hMin: 140, hMax: 230, color: P.trees[0], light: U.shade(P.trees[0], 0.12) });
      Art.forest(ctx, { seed: 5, y: 800, offset: off * 0.6, spacing: 95, hMin: 230, hMax: 340, color: P.trees[1], light: U.shade(P.trees[1], 0.14), kind: 'mix', sway: 6, t });
      Art.rays(ctx, { x: 1500, y: 150, angle: 2.2, spread: 0.9, count: 8, len: 1400, color: P.light, alpha: 0.14, t });
      const gy = { y: 860, offset: off };
      Art.ground(ctx, { y: 860, offset: off, color: P.ground, color2: P.ground2 });
      Art.trail(ctx, { y: 860, offset: off, color: P.trail });
      Art.grass(ctx, { y: (x) => Art.groundY(x, gy), offset: off, color: P.grass, t });
      ['h1', 'h2', 'h3', 'h4', 'me'].forEach((k, i) => {
        const x = 1180 - i * 190;
        Art.person(ctx, { x, y: Art.groundY(x, gy) + 18, look: k, t, walk: t * 6.2 + i * 1.3, s: 0.78 });
      });
      Art.forest(ctx, { seed: 11, y: 1150, offset: off * 1.4, spacing: 420, hMin: 520, hMax: 700, color: P.trees[2], kind: 'pine' });
      Art.motes(ctx, { seed: 3, count: 50, t, color: '#fff6d8', glow: 0.6 });
      Art.bubble(ctx, "The view up there is supposed to be unreal.", { x: 1180, y: 430, tx: 1180, ty: 560 });
      Art.captions(ctx, t, [[0, 10, 'I imagine that I’m on a hike with a group of people.']]);
      Art.hand(ctx, 'let’s stop here', { x: 400, y: 300, size: 64, color: '#ffd77a', glow: '#ffb84a' });
      Art.title(ctx, 'The Hikers,', { y: 200, x: 400, size: 80 });
    } });
})();
