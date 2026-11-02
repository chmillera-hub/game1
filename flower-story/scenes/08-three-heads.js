/* ==========================================================================
   08 · Three Heads — the conversation goes on as dusk deepens into blue hour.
   He glows, hand on heart; the hikers stare; for one beat he literally has
   three beaming heads. Then inside his head: five emotions on a cosy couch
   facepalm in perfect sync. "They’ll never get it."
   Shots: S1 two-shot · S2 MCU me · S3 the stare · S4 THREE HEADS ·
   S5 two-shot (h1) → rush into his head · S7 the mind-space.
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 37.0;
  const K = U.keys;
  const MIND = 28.9;                                      // cut inside his head

  /* ---------------------------------------------- world (same as 07) */
  const GO = { y: 870, amp: 16, offset: 2100 };
  const gy = (x) => Art.groundY(x, GO);
  const TR = 20, S = 0.8, FX = 820, FY = gy(FX) + 60, FS = 0.66;
  const MEX = 702, MEY = gy(MEX) + TR, ME_SX = MEX + 34 * S;
  const SEED = { me: 763, h1: 11, h2: 23, h3: 37, h4: 41 };
  const WARM = '#ffb48a';

  /* ------------------------------------------- dusk → blue hour */
  const P0 = Art.TOD.dusk, P1 = U.mixDeep(Art.TOD.dusk, Art.TOD.night, 0.5);
  const nightK = (t) => U.ease(t, 0.5, 27, 'inOutSine');       // 0 → 1 (P0 → P1)
  const pal = (t) => U.mixDeep(P0, P1, nightK(t));
  const tintOf = (P) => U.mix(P.sky[0], P.sky[1], 0.45);

  /* ------------------------------------------------------------- camera */
  const camD = (c, d) => ({ x: 960 + (c.x - 960) * d, y: 540 + (c.y - 540) * d, z: 1 + (c.z - 1) * d });
  const applyCam = (ctx, c, d) => { const k = camD(c, d); ctx.translate(960, 540); ctx.scale(k.z, k.z); ctx.translate(-k.x, -k.y); return k; };
  const toScreen = (c, p, d = 1) => { const k = camD(c, d); return { x: 960 + (p.x - k.x) * k.z, y: 540 + (p.y - k.y) * k.z }; };

  /* ------------------------------------- the hikers, where 07 left them */
  const legA = (ph, st, leg) => leg * 0.42 * st * Math.sin(ph);
  const legK = (ph, st, leg) => -(0.12 + Math.max(0, leg * Math.cos(ph)) * 0.75 * st);
  const footY = (ph, st, leg) => { const a = legA(ph, st, leg); return -118 + Math.abs(Math.sin(ph)) * 5 * st - 3 * st + 58 * Math.cos(a) + 56 * Math.cos(a + legK(ph, st, leg)); };
  const PH = Math.PI / 2 + TAU * 9, ST = 0.16;
  const HIKERS = [['h1', FX + 250], ['h2', FX + 402], ['h3', FX + 545], ['h4', FX + 694]].map(([k, x], i) => {
    const s = S * Art.CAST[k].height;
    const lift = (-3.1 - Math.max(footY(PH, ST, 1), footY(PH, ST, -1))) * s;
    return { k, i, x, y: gy(x) + TR + lift, gy: gy(x) + TR, s };
  });

  /* ---------------------------------------------------------------- rig */
  const shoulders = (t, seed, lean, hipX, hipY, shrug) => {
    const top = 88 + Math.sin(t * 1.7 + seed) * 1.3 * 0.3;
    const shX = hipX + Math.sin(lean) * top, shY = hipY - Math.cos(lean) * top;
    const y = shY + 7 - shrug * 8;
    return { F: { x: shX + 3, y }, B: { x: shX - 6, y: y + 1 } };
  };
  const ik = (sh, p) => Art.ik2(sh.x, sh.y, p.x, p.y, 50, 47, -1);
  const mixA = (a, b, k) => a.map((v, i) => v + (b[i] - v) * k);
  const STAND = [0.1, 0.18, -0.08, 0.14];
  // light the cast (as 07): the dusk ambient, the same for every look, then the flower's warm
  // spill multiplied in (each channel scaled by its own value), so every garment keeps its value
  // relative to the others: his dark-teal trousers stay dark (mixing toward the light peach washed
  // them to mid-grey; see also unveil). h1's poles: dark steel with a dim sheen, not pale sticks.
  const LOOK_KEYS = ['skin', 'hair', 'hatColor', 'shirt', 'shirt2', 'pants', 'shoes', 'pack', 'beard', 'pole', 'poleHi'];
  const AMB = 0.22;                                       // 07's dusk ambient (deepens with the night)
  const WARM_K = U.rgb(WARM).map((v) => v / 255);
  const spill = (x) => Math.max(0, 0.08 - Math.abs(x - FX) / 6000);   // its warm spill on the hikers
  const ME_WARM = 0.15 + 0.07;                            // ...and on him (07's, once he beams)
  const STEEL = (b) => ({ pole: U.mix(b.pole || '#6f7680', '#272b35', 0.4), poleHi: U.mix(b.poleHi || '#d3d7dd', '#272b35', 0.45) });
  const lit = (key, tint, amt, warm) => {
    const b = Object.assign({}, Art.CAST[key]);
    if (b.poles) Object.assign(b, STEEL(b));
    const o = Object.assign({}, b), T0 = U.rgb(tint);
    for (const k of LOOK_KEYS) {
      if (!b[k]) continue;
      const c = U.rgb(b[k]);
      o[k] = U.hex(...c.map((v, i) => lerp(v, T0[i], amt) * (1 + warm * WARM_K[i])));
    }
    return o;
  };

  /* -------------------------------------------------------------- shots */
  const SHOTS = [
    { id: 'S1', t0: 0 }, { id: 'S2', t0: 5.9 }, { id: 'S3', t0: 13.8 },
    { id: 'S4', t0: 17.6 }, { id: 'S5', t0: 22.0 }, { id: 'S7', t0: MIND },
  ];
  const shotAt = (t) => { let s = SHOTS[0]; for (const x of SHOTS) if (t >= x.t0) s = x; return s; };
  const HEAD = { x: ME_SX + 8, y: MEY - 200 };              // his head, for the rush-in
  function camAt(t, still) {
    const s = shotAt(t);
    let c;
    if (s.id === 'S1') c = { x: 905, y: 712, z: lerp(1.66, 1.71, U.ease(t, 0, 5.9)) };
    else if (s.id === 'S2') c = { x: 772, y: 690, z: lerp(2.2, 2.36, U.ease(t, 5.9, 13.8)) };
    else if (s.id === 'S3') c = { x: 1300, y: 706, z: lerp(1.46, 1.56, U.ease(t, 13.8, 17.6, 'inOutSine')) };
    else if (s.id === 'S4') c = { x: 868, y: 682, z: lerp(1.74, 1.79, U.ease(t, 17.6, 22.0)) };
    else {
      // two-shot, then the camera rushes into his head
      const k = U.ease(t, 27.75, MIND, 'inExpo');
      const z = lerp(1.66, 1.71, U.ease(t, 22, 27.75));
      c = { x: lerp(905, HEAD.x, U.ease(t, 27.75, MIND - 0.15, 'inOutCubic')), y: lerp(712, HEAD.y, U.ease(t, 27.75, MIND - 0.15, 'inOutCubic')), z: z * Math.pow(7, k) };
    }
    if (!still) {
      const sh = Art.shake(t, 0.35, 8);
      c.x += sh.x / c.z; c.y += sh.y / c.z;
    }
    c.id = s.id;
    return c;
  }
  // each shot's rest camera (mid-shot, no drift; S5's is the two-shot before the rush)
  const refCam = (id) => {
    const i = SHOTS.findIndex((s) => s.id === id);
    const t1 = id === 'S5' ? 27.75 : SHOTS[i + 1].t0;
    return camAt((SHOTS[i].t0 + t1) / 2, true);
  };

  /* ----------------------------------------------------------- dialogue */
  const TALK = [
    [0.6, 5.4, 'It wasn’t important until I saw it and made it matter.', { who: 'me' }],
    [6.1, 13.75, 'It was something small, but when I gave it a part of my soul, it felt meaningful to me.', { who: 'me' }],
    [22.3, 24.6, 'Bro, are you okay?', { who: 'h1' }],
    [25.0, 27.45, 'That sounds… intense.', { who: 'h1' }],
  ];
  const NARR = [
    [14.0, 18.6, 'The hikers stare at me like I’ve grown three heads.'],
    [29.6, 32.6, 'My emotions collectively facepalm, muttering,'],
  ];

  /* ------------------------------------------------- background layers */
  const forestW = (c, o, x0, x1) => {
    const sp = o.spacing, i0 = Math.floor((x0 - 300) / sp), i1 = Math.ceil((x1 + 300) / sp);
    for (let i = i0; i <= i1; i++) {
      const r1 = U.hash(i, o.seed), r2 = U.hash(i, o.seed + 1), r3 = U.hash(i, o.seed + 2);
      const x = i * sp + (r2 - 0.5) * sp * 0.9;
      const h = lerp(o.hMin, o.hMax, r1);
      const col = U.shade(o.color, (r3 - 0.5) * 0.12);
      const yy = o.y + (r3 - 0.5) * 24;
      if (o.kind === 'mix' && r3 < 0.32) Art.roundTree(c, x, yy, h * 0.85, col, { light: o.light, seed: i });
      else Art.pine(c, x, yy, h, col, { light: o.light, w: 0.4 * (0.85 + r2 * 0.3) });
    }
  };
  // Art.clouds' layout (seed 6, offset 120), minus the cloud that doubled up
  // with its neighbour right behind the summit's tip: the peak and its
  // promise-glow now stand against one soft cloud instead of two tangled outlines
  // (07 and 08 share this sky — keep them identical)
  function skyClouds(c, P) {
    const seed = 6, span = W + 900, color = U.mix(P.sky[1], P.sky[0], 0.35), shade = U.mix(P.sky[2], P.haze, 0.35);
    for (let i = 0; i < 5; i++) {
      if (i === 3) continue;
      const x = ((((U.hash(i, seed) * span - 120) % span) + span) % span) - 450;
      const s = 1.15 * (0.6 + U.hash(i, seed + 2) * 0.8);
      Art.cloud(c, x, lerp(190, 360, U.hash(i, seed + 1)), s, color, 0.5 * (0.6 + 0.4 * U.hash(i, seed + 3)), i + seed * 13, shade);
    }
  }
  const LAYERS = [
    { id: 'clouds', d: 0.05, r: [-560, 40, 2560, 540], draw(c, P, x0, x1) {
      skyClouds(c, P);
    } },
    { id: 'far', d: 0.09, r: [-60, 140, 2040, 1110], draw(c, P, x0, x1) {
      Art.ridge(c, { seed: 21, y: 660, amp: 180, color: U.mix(P.far, P.sky[1], 0.4), x0: x0 - 40, x1: x1 + 40, bottom: 1300 });
      const tip = Art.summit(c, { x: 1545, y: 664, h: 450, w: 790, P, glow: 0.5, t: 0, flag: true });
      Art.glow(c, tip.x - 30, tip.y + 170, 360, U.mix(P.summit, P.snow, 0.4), 0.2);
      Art.glow(c, tip.x, tip.y + 30, 150, P.snow, 0.14);
      Art.fog(c, { y: 668, h: 210, color: P.fog, alpha: 0.5 });
    } },
    { id: 'mid', d: 0.2, r: [-60, 600, 2100, 1110], draw(c, P, x0, x1) {
      Art.ridge(c, { seed: 8, y: 742, amp: 110, color: P.mid, x0: x0 - 40, x1: x1 + 40, bottom: 1300 });
      Art.fog(c, { y: 748, h: 120, color: P.fog, alpha: 0.28 });
    } },
    { id: 'trees1', d: 0.38, r: [-80, 560, 2160, 880], draw(c, P, x0, x1) {
      forestW(c, { seed: 31, y: 800, spacing: 64, hMin: 120, hMax: 210, color: P.trees[0], light: U.mix(P.trees[0], P.sky[2], 0.14) }, x0, x1);
      Art.fog(c, { y: 795, h: 150, color: P.fog, alpha: 0.3 });
    } },
    { id: 'trees2', d: 0.62, r: [-80, 480, 2280, 900], draw(c, P, x0, x1) {
      forestW(c, { seed: 32, y: 856, spacing: 96, hMin: 210, hMax: 330, color: P.trees[1], kind: 'mix', light: U.mix(P.trees[1], P.sky[2], 0.12) }, x0, x1);
      Art.fog(c, { y: 852, h: 110, color: P.fog, alpha: 0.2 });
    } },
  ];
  const BLUR_RES = 0.36;
  const built = {};
  function layerCanvas(L, set) {
    const [x0, y0, x1, y1] = L.r;
    const key = 'a5h:' + L.id + set;
    const cv = Art.canvas(key, (x1 - x0) * BLUR_RES, (y1 - y0) * BLUR_RES);
    if (built[key] !== cv) {
      const c = cv.getContext('2d');
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, cv.width, cv.height);
      c.setTransform(BLUR_RES, 0, 0, BLUR_RES, -x0 * BLUR_RES, -y0 * BLUR_RES);
      L.draw(c, set ? P1 : P0, x0, x1);
      built[key] = cv;
    }
    return cv;
  }
  // these small caches don't depend on the output resolution: build them at
  // load so the scene's first frames don't hitch (lazily, if this ever fails)
  try { for (const L of LAYERS) { layerCanvas(L, 0); layerCanvas(L, 1); } } catch (e) { /* built on first use */ }
  // Cost control (software raster pays per destination pixel, ~3x more for
  // 'high' smoothing). Dusk → blue hour is a linear blend of two palettes, so
  // every cached plate exists twice (P0, P1) and is mixed by m = nightK(t):
  //  · sky (gradient + low sun): padded full-res plates blitted at whole pixels;
  //  · clouds: the two small caches are mixed off-screen, drawn once (bilinear);
  //  · far/mid/trees: flattened once per shot into half-res plates, mixed
  //    off-screen each frame and re-projected with one scale+offset at a mid
  //    depth (the slow push-ins move the layers < 2% relative to one another).
  const baseK = () => (Art._base && Art._base.a) || 1;
  const SKY_PAD = 64, SKY_H = 860;               // below ~700 px the far ridge's fill always covers the sky
  function skyPlate(set) {
    const k = baseK();
    const w = Math.ceil((W + 2 * SKY_PAD) * k), h = Math.ceil((SKY_H + SKY_PAD) * k);
    const cv = Art.canvas('a5h:sky' + set, w, h);
    const key = w + 'x' + h;
    if (built['sky' + set] !== key) {
      const c = cv.getContext('2d');
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, w, h);
      c.setTransform(k, 0, 0, k, SKY_PAD * k, SKY_PAD * k);
      const P = set ? P1 : P0;
      Art.sky(c, P, { horizon: 790 });
      Art.glow(c, 250, 780, 900, P.sun, 0.22 * (set ? 0.4 : 1));   // blends to 0.22·(1 − 0.6m)
      built['sky' + set] = key;
    }
    return cv;
  }
  const PLATE_R = 0.5, PM = 48, DREF = 0.35;
  function layerPlate(id, set) {
    const r = PLATE_R * baseK();
    const w = Math.ceil((W + 2 * PM) * r), h = Math.ceil((H + 2 * PM) * r);
    const cv = Art.canvas('a5h:plate' + set, w, h);
    const key = id + ':' + w + 'x' + h;
    if (built['plate' + set] !== key) {
      const c0 = refCam(id);
      const c = cv.getContext('2d');
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, w, h);
      c.imageSmoothingEnabled = true;
      c.imageSmoothingQuality = 'low';
      for (const L of LAYERS) {
        if (L.id === 'clouds') continue;           // clouds drift: drawn live
        c.setTransform(r, 0, 0, r, PM * r, PM * r);
        applyCam(c, c0, L.d);
        const [x0, y0, x1, y1] = L.r;
        c.drawImage(layerCanvas(L, set), x0, y0, x1 - x0, y1 - y0);
      }
      built['plate' + set] = key;
      built['plateCam' + set] = c0;
    }
    return cv;
  }
  // off-screen mix of a P0/P1 pair: P1 laid over P0 at m (as drawing both would)
  function mixed(key, a, b, m) {
    if (m <= 0.004) return a;
    if (m >= 0.996) return b;
    const cv = Art.canvas(key, a.width, a.height);
    const c = cv.getContext('2d');
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.globalAlpha = 1;
    c.globalCompositeOperation = 'copy';
    c.drawImage(a, 0, 0);
    c.globalCompositeOperation = 'source-over';
    c.globalAlpha = m;
    c.drawImage(b, 0, 0);
    c.globalAlpha = 1;
    return cv;
  }
  function drawBackdrop(ctx, P, cam, t) {
    const m = nightK(t);
    const k = baseK();
    // sky: the depth-0.03 view barely zooms (≤ 4%); blit anchored at the low sun / horizon
    const kd = camD(cam, 0.03);
    const ox = 960 + (250 - kd.x) * kd.z - 250, oy = 540 + (790 - kd.y) * kd.z - 790;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.imageSmoothingEnabled = false;
    const sx = Math.round((ox - SKY_PAD) * k), sy = Math.round((oy - SKY_PAD) * k);
    if (m < 0.996) ctx.drawImage(skyPlate(0), sx, sy);
    if (m > 0.004) { ctx.globalAlpha = m < 0.996 ? m : 1; ctx.drawImage(skyPlate(1), sx, sy); }
    ctx.restore();
    ctx.save();
    applyCam(ctx, cam, 0.03);
    Art.stars(ctx, { seed: 17, count: 90, t, alpha: 0.42 + 0.5 * m, y0: -60, y1: 420, x0: -100, x1: W + 100 });
    ctx.restore();
    // clouds keep drifting from 07
    const CL = LAYERS[0];
    const cl = m > 0.004 ? mixed('a5h:cloudmix', layerCanvas(CL, 0), layerCanvas(CL, 1), m) : layerCanvas(CL, 0);
    ctx.save();
    applyCam(ctx, cam, CL.d);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(cl, CL.r[0] - (37.2 + t) * 4, CL.r[1], CL.r[2] - CL.r[0], CL.r[3] - CL.r[1]);
    ctx.restore();
    if (t > 27.75) {
      // the rush into his head zooms ×7: one flat plate would lose the depth, so the
      // layers go individually (at the rush's first frame the plate is exact: no seam)
      for (const L of LAYERS) {
        if (L.id === 'clouds') continue;
        const lc = mixed('a5h:mix:' + L.id, layerCanvas(L, 0), layerCanvas(L, 1), m);
        ctx.save();
        applyCam(ctx, cam, L.d);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'low';
        ctx.drawImage(lc, L.r[0], L.r[1], L.r[2] - L.r[0], L.r[3] - L.r[1]);
        ctx.restore();
      }
    } else {
      // far ridge + summit, mid ridge, two tree bands: this shot's plate
      const p0 = m < 0.996 ? layerPlate(cam.id, 0) : null;
      const pl = m <= 0.004 ? p0 : m >= 0.996 ? layerPlate(cam.id, 1) : mixed('a5h:platemix', p0, layerPlate(cam.id, 1), m);
      const kr = camD(cam, DREF), k0 = camD(built[m >= 0.996 ? 'plateCam1' : 'plateCam0'], DREF);
      const A = kr.z / k0.z;
      const bx = 960 * (1 - A) + (k0.x - kr.x) * kr.z, by = 540 * (1 - A) + (k0.y - kr.y) * kr.z;
      ctx.save();
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'low';
      ctx.drawImage(pl, bx - PM * A, by - PM * A, (W + 2 * PM) * A, (H + 2 * PM) * A);
      ctx.restore();
    }
    ctx.save(); applyCam(ctx, cam, 0.09);
    Art.glow(ctx, 1569, 222, 110, P.light, (0.12 + 0.06 * Math.sin(t * 1.4)) * (1 - 0.5 * m));
    ctx.restore();
    ctx.save(); applyCam(ctx, cam, 0.62);
    Art.motes(ctx, { seed: 51, count: 14, x0: 0, x1: 2600, y0: 560, y1: 840, t: t + 37.2, color: '#ffe9a6', size: 1.5, drift: 4, wander: 50, glow: 0.9, blink: 1, alpha: 0.75 });
    ctx.restore();
  }

  /* ------------------------------------------------------ ground plane */
  function drawGround(c, P, cam, t) {
    c.save();
    const k = applyCam(c, cam, 1);
    const x0 = k.x - 960 / k.z, x1 = k.x + 960 / k.z;
    c.save();
    c.translate(x0, 0);
    const go = { y: GO.y, amp: GO.amp, offset: GO.offset + x0 };
    Art.ground(c, Object.assign({ color: P.ground, color2: P.ground2 }, go));
    Art.trail(c, Object.assign({ color: P.trail, depth: 46 }, go));
    c.restore();
    Art.grass(c, { seed: 4, y: gy, x0: x0 - 30, x1: x1 + 30, spacing: 8, h: 24, color: U.shade(P.grass, -0.08), color2: U.shade(P.grass, 0.1), t, wind: 0.8 });
    Art.glow(c, FX, FY - 20, 240, Art.FLOWER.tip, 0.07);
    c.restore();
  }
  function verge(c, P, cam, t) {
    c.save();
    const k = applyCam(c, cam, 1);
    const x0 = k.x - 960 / k.z, x1 = k.x + 960 / k.z;
    const sp = 150, i0 = Math.floor(x0 / sp) - 1, i1 = Math.ceil(x1 / sp) + 1;
    for (let i = i0; i <= i1; i++) {
      const h = U.hash(i, 71);
      const x = i * sp + U.hash(i, 72) * sp;
      if (Math.abs(x - FX) < 170 || Math.abs(x - MEX - 30) < 130) continue;
      const y = gy(x) + 72 + U.hash(i, 73) * 40;
      const col = U.mix(P.trees[2], P.grass, 0.25 + U.hash(i, 74) * 0.3);
      if (h < 0.4) Art.fern(c, x, y, 0.42 + U.hash(i, 75) * 0.3, col, U.wind(t, x, i) * 0.6);
      else if (h < 0.78) Art.grass(c, { seed: 100 + i, y, x0: x - 26, x1: x + 26, spacing: 5, h: 18 + U.hash(i, 76) * 14, color: col, color2: U.shade(col, 0.12), t, wind: 0.7 });
      else { c.fillStyle = U.mix(P.trail, P.ground2, 0.45); c.beginPath(); c.ellipse(x, y, 8 + h * 7, 4.5 + h * 2.5, 0, 0, TAU); c.fill(); }
    }
    Art.grass(c, { seed: 9, y: (x) => gy(x) + 50, x0: x0 - 30, x1: x1 + 30, spacing: 7, h: 16, color: U.shade(P.grass, -0.2), color2: U.shade(P.grass, -0.04), t, wind: 0.7 });
    c.restore();
  }

  /* --------------------------------------------------- the flower spot */
  function mossRock(c, x, y, w, h, tint) {
    Art.rock(c, x, y, w, h, U.mix('#8a8f86', tint, 0.32), 3);
    c.save();
    c.beginPath();
    c.moveTo(x - w / 2, y);
    c.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(3, 1) * 8, y - h);
    c.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    c.lineTo(x + w / 2, y);
    c.closePath();
    c.clip();
    const moss = U.mix('#6f9446', tint, 0.3);
    c.fillStyle = moss;
    c.beginPath();
    c.ellipse(x - w * 0.08, y - h * 0.98, w * 0.42, h * 0.3, -0.1, 0, TAU);
    c.ellipse(x + w * 0.22, y - h * 0.8, w * 0.2, h * 0.2, 0.4, 0, TAU);
    for (let i = 0; i < 5; i++) {
      const px = x - w * 0.36 + i * w * 0.16, py = y - h * (0.74 + 0.18 * Math.sin(i * 1.7));
      c.moveTo(px + 5, py); c.ellipse(px, py, 5, 7 + (i % 2) * 3, 0, 0, TAU);
    }
    c.fill();
    c.fillStyle = U.shade(moss, 0.16);
    c.beginPath(); c.ellipse(x - w * 0.02, y - h * 1.02, w * 0.26, h * 0.13, -0.1, 0, TAU); c.fill();
    c.fillStyle = U.rgba(WARM, 0.16);
    c.beginPath(); c.ellipse(x - w * 0.42, y - h * 0.5, w * 0.24, h * 0.5, 0, 0, TAU); c.fill();
    c.restore();
  }
  function clump(c, P, t) {
    const x = MEX + 40, y = MEY + 26;
    const dark = U.mix(P.trees[2], P.grass, 0.35), mid = U.mix(P.grass, P.trees[2], 0.2), fern = U.shade(P.grass, 0.06);
    Art.bush(c, x - 8, y + 2, 47, dark, null, 4);
    Art.fern(c, x - 34, y + 4, 0.86, mid, U.wind(t, x, 2) * 0.7);
    Art.grass(c, { seed: 77, y: y + 8, x0: x - 82, x1: x + 70, spacing: 5, h: 40, hVar: 0.7, color: dark, color2: mid, t, wind: 0.6 });
    Art.fern(c, FX - 52, FY + 4, 1.05, fern, U.wind(t, FX, 3) * 0.9);
  }
  function drawFlower(c, P, t, glow) {
    // (its glows, halo + Art.flower's own, are mirrored by bloom(): keep the two in step)
    Art.glow(c, FX + 4, FY - 108, 150, Art.FLOWER.tip, 0.12 * glow);
    Art.flower(c, { x: FX, y: FY, s: FS, stemH: 160, t, glow: 0.42 * glow, face: 0.84, sway: 0.55, seed: 2 });
    Art.grass(c, { seed: 12, y: FY + 4, x0: FX - 40, x1: FX + 36, spacing: 6, h: 22, color: U.shade(P.grass, -0.1), color2: U.shade(P.grass, 0.08), t, wind: 0.7 });
  }

  /* ----------------------------------------------------------------- me */
  const HEADS0 = 17.9, HEADS1 = 20.6;                     // the gag: in, out
  function meFace(t) {
    const soul = U.fade(t, 10.25, 12.7, 0.25, 0.35);       // "part of my soul": eyes close
    const f = {
      smile: 0.95 - 0.1 * soul,
      eyes: soul > 0.5 ? 'closed' : 'sparkle',
      open: 0.25 + 0.08 * Math.sin(t * 2.1),
      talk: Art.talkingAt(t, TALK, 'me'),
      blush: 0.45 + 0.15 * soul,
      browUp: 0.35,
    };
    return f;
  }
  // the extra heads: grown from the shoulders, beaming in unison
  function extraHeads(c, a, look, t) {
    const hd = a.head, r = hd.r;
    const sh = a.shoulder;
    const specs = [
      { side: -1, t0: HEADS0, t1: HEADS1 + 0.15, turn: 0.55, facing: -1 },
      { side: 1, t0: HEADS0 + 0.25, t1: HEADS1, turn: 0.2, facing: 1 },
    ];
    const drawn = [];
    for (const s of specs) {
      if (t < s.t0 || t > s.t1 + 0.3) continue;
      const kin = U.ease(t, s.t0, s.t0 + 0.42, 'outBack');
      const kout = U.ease(t, s.t1, s.t1 + 0.28, 'inBack');
      const k = Math.max(0, kin - kout);
      if (k <= 0.01) continue;
      const wob = Math.exp(-4 * Math.max(0, t - s.t0)) * Math.sin((t - s.t0) * 18) * 0.25;
      const tilt = s.side * (0.38 + wob) + Math.sin(t * 2.3 + s.side) * 0.04 + (U.bump(t, 19.35, 0.35) * 0.18 * s.side);
      // far enough out that all three beaming faces read whole (the centre head
      // overlaps them only at the beanie brims), each on its own neck
      const hx = hd.x + s.side * r * 2.0 * k, hy = hd.y + r * (0.34 + (1 - k) * 1.0);
      // neck, from the collar to the new head
      const nx = sh.x + s.side * r * 0.45 - (s.side < 0 ? r * 0.25 : 0), ny = sh.y + r * 0.1;
      c.strokeStyle = U.shade(look.skin, -0.12);
      c.lineCap = 'round';
      c.lineWidth = 15 * a.scale * Math.min(1, k * 1.3);
      c.beginPath(); c.moveTo(nx, ny); c.quadraticCurveTo(lerp(nx, hx, 0.5) + s.side * r * 0.2, lerp(ny, hy, 0.6), hx - s.side * r * 0.1, hy + r * 0.55); c.stroke();
      Art.head(c, hx, hy, r * clamp(k, 0, 1.2), look, { eyes: 'sparkle', smile: 1, open: 0.45 + 0.1 * Math.sin(t * 6 + s.side), blush: 0.5, browUp: 0.4, blink: U.bump(t, 19.9, 0.09) }, { facing: s.facing, turn: s.turn, t, tilt: tilt * s.facing, seed: 5 + s.side });
      drawn.push({ x: hx, y: hy, r: r * clamp(k, 0, 1.2) });
    }
    return drawn;
  }
  function drawMe(c, P, t) {
    const look = lit('me', tintOf(P), AMB + 0.08 * nightK(t), ME_WARM);
    const face = meFace(t);
    const sh = shoulders(t, SEED.me, 0, 0, -117, 0);
    const heart = ik(sh.F, { x: 16 + sh.F.x - 3, y: -184 });
    const press = U.bump(t, 0.5, 0.35) * 0.12 + U.bump(t, 10.0, 0.4) * 0.14;      // presses the hand to his chest
    let A = [heart[0] - press, heart[1] + press * 0.6, STAND[2], STAND[3]];
    A = mixA(A, [A[0], A[1], -0.42, 0.55], U.fade(t, 6.4, 13.2, 0.8, 0.8) * 0.8);     // the other hand opens, earnest
    const nod = U.bump(t, 26.3, 0.28) * 0.12 + U.bump(t, 26.85, 0.25) * 0.08;      // a happy nod at "intense"
    const breath = U.bump(t, 0.45, 0.4) * 0.35 + U.bump(t, 9.85, 0.35) * 0.3;
    const o = {
      x: ME_SX, y: MEY, s: S, look, pose: 'stand', t, seed: SEED.me, lean: -0.02, shrug: breath,
      head: { tilt: -0.06 + nod - 0.05 * U.fade(t, 10.25, 12.7, 0.3, 0.4), turn: 0.1 },
      face, armF: [A[0], A[1]], armB: [A[2], A[3]], shadow: false,
    };
    // during the gag: anchors first (the extra heads sit behind him), then him
    let extra = [];
    if (t > HEADS0 - 0.05 && t < HEADS1 + 0.7) {
      const probe = Art.person(c, Object.assign({}, o, { alpha: 0, shadow: false }));
      extra = extraHeads(c, probe, look, t);
    }
    const a = Art.person(c, o);
    a.extra = extra;
    return a;
  }

  // The flower's bloom (drawn last, over everything near it) greyed his dark trousers: on its own
  // it lifted them ~20-28 levels. So it is taken back off his legs ahead of time (as 07): his
  // figure, drawn again off-screen at half resolution, takes the bloom's colour (never more than
  // his own), is kept on his legs only and subtracted before the bloom goes on (his face and
  // hands keep it). Only that box is touched. a: his anchors; glow: drawFlower's argument.
  const flowerHead = (t) => ({ x: FX + 0.55 * U.wind(t, FX, 2) * 9 * FS, y: FY - 160 * FS });   // Art.flower's own placement
  const UNVEIL = 0.85, URES = 0.5;
  function unveil(ctx, draw, a, t, glow) {
    if (glow <= 0) return;
    // his legs (standing): feathered up into the jacket, and at the front, so a hand held out low
    // (presenting the flower) keeps its glow
    const S_ = a.scale, fy0 = a.hip.y - 26 * S_, fy1 = a.hip.y + 4 * S_, fx0 = a.hip.x + 22 * S_;
    const bx0 = a.hip.x - 46 * S_, bx1 = a.hip.x + 36 * S_, by0 = fy0, by1 = a.feet.y + 6;
    const m = ctx.getTransform(), cv = ctx.canvas;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const [px, py] of [[bx0, by0], [bx1, by0], [bx0, by1], [bx1, by1]]) {
      const p = m.transformPoint({ x: px, y: py });
      x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y);
    }
    const base = Art._base || new DOMMatrix();         // within the picture: the letterbox covers the rest
    const pt = base.transformPoint({ x: 0, y: Art.PIC.top }).y, pb = base.transformPoint({ x: 0, y: Art.PIC.bottom }).y;
    x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(pt), Math.floor(y0));
    x1 = Math.min(cv.width, Math.ceil(x1)); y1 = Math.min(cv.height, Math.ceil(pb), Math.ceil(y1));
    if (x1 - x0 < 2 || y1 - y0 < 2) return;
    const w = Math.ceil((x1 - x0) * URES), h = Math.ceil((y1 - y0) * URES);
    const off = new DOMMatrix().scale(URES, URES).translate(-x0, -y0).multiply(m);
    const begin = (c) => {           // a fresh state, clipped to the box (destination-in is unbounded)
      c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
      c.save(); c.beginPath(); c.rect(0, 0, w, h); c.clip();
    };
    const cw = Math.ceil(cv.width * URES) + 2, ch = Math.ceil(cv.height * URES) + 2;
    const F = Art.canvas('a5h:uvF', cw, ch), f = F.getContext('2d');
    begin(f);
    f.clearRect(0, 0, w, h);
    f.setTransform(off);
    draw(f);
    f.restore();
    const L = Art.canvas('a5h:uvL', cw, ch), l = L.getContext('2d');
    begin(l);
    l.fillStyle = '#000'; l.fillRect(0, 0, w, h);
    l.setTransform(off);
    bloom(l, t, glow);
    l.setTransform(1, 0, 0, 1, 0, 0);
    l.globalCompositeOperation = 'darken';                  // never more than his own colour
    l.drawImage(F, 0, 0, w, h, 0, 0, w, h);
    l.globalCompositeOperation = 'destination-in';          // only where he is...
    l.drawImage(F, 0, 0, w, h, 0, 0, w, h);
    l.setTransform(off);                                    // ...on his legs
    for (const g of [l.createLinearGradient(0, fy0, 0, fy1), l.createLinearGradient(bx1, 0, fx0, 0)]) {
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, '#000');
      l.fillStyle = g;
      l.fillRect(bx0, by0, bx1 - bx0, by1 - by0);
    }
    l.restore();
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'difference';
    ctx.globalAlpha *= UNVEIL;
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(L, 0, 0, w, h, x0, y0, w / URES, h / URES);
    ctx.restore();
  }
  // the flower's bloom: drawFlower's halo + Art.flower's own two glows
  function bloom(c, t, glow) {
    const hd = flowerHead(t), hr = 52 * FS;
    Art.glow(c, FX + 4, FY - 108, 150, Art.FLOWER.tip, 0.12 * glow);
    Art.glow(c, hd.x, hd.y, hr * 4.2, Art.FLOWER.tip, 0.42 * glow * 0.45);
    Art.glow(c, hd.x, hd.y, hr * 1.8, '#fff2d6', 0.42 * glow * 0.35);
  }

  /* ------------------------------------------------------------- hikers */
  function hikerFace(i, t) {
    const talk = i === 0 ? Art.talkingAt(t, TALK, 'h1') : 0;
    const wideK = i === 1 ? 1 : U.ease(t, 4 + i * 0.6, 9 + i * 0.5);
    const f = { eyes: wideK > 0.55 ? 'wide' : 'open', smile: -0.08 - 0.12 * wideK, browUp: 0.3 + 0.7 * wideK, sweat: 0.4, talk, brow: 0.1 };
    if (t >= 13.8 && t < 22.0) { // the stare: no blinking... then one slow blink, together
      f.eyes = 'wide'; f.browUp = 1; f.blink = U.bump(t, 16.25, 0.16);
      if (i === 2) { f.mouth = 'o'; f.open = 0.25; }
      if (i === 1) f.open = 0.15;
      if (t > HEADS0) { f.open = 0.3 + (i === 0 ? 0.25 : 0); f.mouth = 'o'; f.browUp = 1; f.lookY = -0.3; }
    }
    if (i === 0 && t >= 22.0) { f.eyes = 'open'; f.brow = 0.85; f.browUp = 0.4; f.smile = -0.25; f.blink = undefined; }
    if (i === 0 && t >= 24.8) { f.brow = 0.6; f.smile = -0.12; f.eyes = t > 26.6 ? 'flat' : 'open'; }
    if (i > 0 && t >= 22.0) { f.eyes = 'wide'; f.blink = undefined; f.mouth = undefined; f.open = 0.05; f.browUp = 0.8; }
    return f;
  }
  function drawHiker(c, P, h, t) {
    const i = h.i;
    const face = hikerFace(i, t);
    const recoil = (i === 0 ? U.ease(t, HEADS0 + 0.05, HEADS0 + 0.4, 'outBack') * (1 - U.ease(t, 21.0, 22.4)) : 0);
    const glance = (i === 1 || i === 2) ? U.fade(t, 25.4, 27.2, 0.3, 0.4) : 0;
    const nod = i === 0 ? U.bump(t, 26.0, 0.35) * 0.14 : i === 3 ? U.bump(t, 26.4, 0.4) * 0.1 : 0;
    const head = { tilt: -0.3 + 0.05 * Math.sin(t * 0.8 + i) - recoil * 0.12 + nod, turn: 0.32 * glance + (i === 3 ? 0.1 : 0) };
    const lean = -0.1 * recoil - (i === 0 ? 0.05 * U.fade(t, 22.2, 25.0, 0.4, 0.8) : 0) + 0.022 * Math.sin((t + 37.2) * 0.9 + i * 1.7) * (t >= 13.8 && t < 17.6 ? 0.2 : 1);
    let A = STAND.slice();
    if (i === 0) A = mixA(A, [0.55, 1.2, -0.25, 0.9], U.fade(t, 22.3, 24.4, 0.3, 0.5) * 0.7);      // palms out: "whoa"
    if (i === 0) A = mixA(A, [0.95, 0.4, A[2], A[3]], recoil * 0.6);
    const o = {
      x: h.x, y: h.y, s: S, look: lit(h.k, tintOf(P), AMB + 0.08 * nightK(t), spill(h.x)), facing: -1, pose: 'walk', walk: PH, stride: ST,
      tired: 0.75, t, seed: SEED[h.k], face, head, lean, armF: [A[0], A[1]], armB: [A[2], A[3]], shadow: false,
    };
    if (h.k === 'h4') { // the dead phone, still in hand
      o.gesture = 'phoneLook';
      o.gw = 0.42 * (1 - U.ease(t, 14.5, 15.5)) + 0.1;
      delete o.armF;
      o.holdF = phone;
    }
    shadow(c, h.x, h.gy, 40 * h.s / S);
    return Art.person(c, o);
  }

  /* ----------------------------------------------------- small helpers */
  function sparkle(ctx, x, y, r, a, rot, color) {
    if (a <= 0.01 || r <= 0.3) return;
    Art.glow(ctx, x, y, r * 2.6, color, a * 0.55);
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.fillStyle = '#fffbe9';
    ctx.beginPath();
    ctx.moveTo(0, -r);
    ctx.quadraticCurveTo(r * 0.14, -r * 0.14, r, 0);
    ctx.quadraticCurveTo(r * 0.14, r * 0.14, 0, r);
    ctx.quadraticCurveTo(-r * 0.14, r * 0.14, -r, 0);
    ctx.quadraticCurveTo(-r * 0.14, -r * 0.14, 0, -r);
    ctx.fill();
    ctx.restore();
  }
  // avoid: heads {x,y,r} a sparkle must not sit on (they dim out over a face)
  function sparkles(ctx, hd, t, n, a, seed, avoid) {
    for (let i = 0; i < n; i++) {
      const per = 1.6 + U.hash(i, seed + 5) * 1.2;
      const ph = U.fract(t / per + U.hash(i, seed + 6));
      let life = Math.sin(ph * Math.PI);
      let ang = -2.8 + U.hash(i, seed + 7) * 3.1;
      if (Math.abs(ang + 1.62) < 0.34) ang += ang < -1.62 ? -0.34 : 0.34;   // keep clear of the pompom
      const rr = hd.r * (1.6 + U.hash(i, seed + 8) * 0.9) + ph * 10;
      const x = hd.x + Math.cos(ang) * rr, y = hd.y + Math.sin(ang) * rr * 0.9;
      if (avoid) for (const o of avoid) life *= U.smooth((Math.hypot(x - o.x, y - o.y) - o.r * 1.05) / (o.r * 0.5));
      sparkle(ctx, x, y, (4 + U.hash(i, seed + 9) * 6) * life, life * a, t * 0.6 + i, '#ffe7a8');
    }
  }
  function shadow(ctx, x, y, w, a = 0.3) {
    ctx.fillStyle = `rgba(14,10,24,${a})`;
    ctx.beginPath(); ctx.ellipse(x, y + 2, w, w * 0.17, 0, 0, TAU); ctx.fill();
  }
  function phone(c) {
    c.save();
    c.rotate(-0.32);
    c.fillStyle = '#20232c';
    Art.roundRect(c, -3, -33, 19, 34, 4); c.fill();
    c.fillStyle = '#06070b';
    Art.roundRect(c, -0.8, -30.5, 14.6, 27.5, 2.6); c.fill();
    c.strokeStyle = 'rgba(255,255,255,0.12)'; c.lineWidth = 1.2;
    c.beginPath(); c.moveTo(1.5, -28); c.lineTo(11, -19); c.stroke();
    c.restore();
  }

  /* ------------------------------------------------------------ bubbles */
  // Dialogue balloons. Art.bubble keeps its full-size box while the text types
  // on (long lines sit in a big, mostly empty balloon) and pops by scaling that
  // empty box about its centre (a faint ghost far from the speaker). These are
  // laid out exactly like Art.bubble — same font, wrap, padding, colours, tail,
  // shadow, timing — but the box hugs the text typed so far, opening right and
  // down from its final top-left corner (the words never move), and it springs
  // out of the tail tip at the speaker's mouth.
  const BAL = { size: 34, padX: 28, padY: 20 };
  function balloon(ctx, t, t0, t1, text, o) {
    const alpha = U.fade(t, t0, t1, 0.12, 0.35);
    if (alpha <= 0.003) return;
    const { size, padX, padY } = BAL, lh = size * 1.22;
    ctx.save();
    ctx.font = Art.font(size, 'sans', 800);
    const lines = Art.wrap(ctx, text, o.maxW);
    const widths = lines.map((l) => ctx.measureText(l).width);
    const tw = Math.max(...widths);
    const bw = tw + padX * 2, bh = lines.length * lh + padY * 2;
    const L = o.x - bw / 2, T = o.y - bh / 2;
    const total = lines.reduce((n, l) => n + l.length, 0);
    const typeDur = Math.min(2.4, 0.15 + text.length * 0.032);
    const n = U.prog(t, t0 + 0.08, t0 + 0.08 + typeDur) * total;
    // the extent of what's been typed (fractional: the box edge leads the letters)
    let cw = 0, rows = 1, s = 0;
    for (let i = 0; i < lines.length; i++) {
      if (i > 0 && n <= s) break;
      const typed = clamp(n - s, 0, lines[i].length), k = Math.floor(typed);
      const w0 = ctx.measureText(lines[i].slice(0, k)).width;
      const w1 = k < lines[i].length ? ctx.measureText(lines[i].slice(0, k + 1)).width : w0;
      cw = Math.max(cw, (tw - widths[i]) / 2 + lerp(w0, w1, typed - k));
      if (i > 0) rows = i + U.smooth(clamp((n - s) / 1.5));   // a new row opens over ~1.5 letters
      s += lines[i].length;
    }
    const w = Math.max(cw + padX * 2, padX * 2 + 16), h = rows * lh + padY * 2;
    const tx = o.tx, ty = o.ty;
    const pop = U.prog(t, t0, t0 + 0.32);
    const sc = lerp(0.5, 1, U.E.outBack(pop));
    ctx.globalAlpha *= alpha * clamp(pop * 4);
    ctx.translate(tx, ty); ctx.scale(sc, sc); ctx.translate(-tx, -ty);
    ctx.shadowColor = 'rgba(0,0,0,0.28)';
    ctx.shadowBlur = 18;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = '#fffaf1';
    Art.roundRect(ctx, L, T, w, h, Math.min(30, h / 2));
    ctx.fill();
    const m = Math.min(40, w / 2), ax = clamp(tx, L + m, L + w - m);
    const below = ty > T + h / 2, by = below ? T + h - 2 : T + 2;
    ctx.beginPath();
    ctx.moveTo(ax - 18, by);
    ctx.quadraticCurveTo(lerp(ax, tx, 0.5) - 4, lerp(by, ty, 0.55), tx, ty);
    ctx.quadraticCurveTo(lerp(ax, tx, 0.5) + 8, lerp(by, ty, 0.4), ax + 16, by);
    ctx.closePath();
    ctx.fill();
    ctx.shadowColor = 'transparent';
    ctx.fillStyle = '#2b2530';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    let shown = Math.floor(n + 0.0001);
    lines.forEach((line, i) => {
      if (shown <= 0) return;
      ctx.fillText(line.slice(0, shown), L + padX + (tw - widths[i]) / 2, T + padY + lh * (i + 0.5) + 1);
      shown -= line.length;
    });
    ctx.restore();
  }
  function bubbleSize(ctx, text, maxW) {
    ctx.save();
    ctx.font = Art.font(34, 'sans', 800);
    const lines = Art.wrap(ctx, text, maxW);
    let tw = 0;
    for (const l of lines) tw = Math.max(tw, ctx.measureText(l).width);
    ctx.restore();
    return { w: tw + 56, h: lines.length * 34 * 1.22 + 40 };
  }
  function place(ctx, text, sp, heads, maxW) {
    const b = bubbleSize(ctx, text, maxW);
    const f = sp.f, hr = sp.r;
    const tip = { x: sp.head.x + f * hr * 1.62, y: sp.mouth.y + 2 };
    const base = sp.head.x + f * hr * 2.65;
    // every balloon opens away from its tail (it grows as the words type on), so a
    // left-facing speaker's balloon starts just above the tail and runs over his head
    let x = f > 0 ? base - 40 + b.w / 2 : tip.x - 52 + b.w / 2;
    x = clamp(x, b.w / 2 + 36, W - b.w / 2 - 36);
    let bottom = sp.top.y - 26;
    for (const o of heads) if (Math.abs(o.x - x) < b.w / 2 + o.r) bottom = Math.min(bottom, o.y - o.r - 22);
    const y = Math.max(bottom - b.h / 2, Art.PIC.top + 16 + b.h / 2);
    return { x, y, tx: tip.x, ty: tip.y, maxW };
  }

  /* ========================================================= THE MIND */
  // A cosy room inside his head: arched alcove, lamp, string lights, a couch
  // where his five emotions sit together. The set is cached once (screen space).
  const EMOS = [['dream', -2], ['calm', -1], ['wonder', 0], ['heart', 1], ['spark', 2]];
  const SEAT = 772, ES = 2.0, EX = (i) => 960 + i * 252;
  const lampX = 150, lightY = (k) => 168 + Math.sin(k * Math.PI) * 62 + Math.sin(k * Math.PI * 4) * 5;
  function roomCanvas() {
    const cv = Art.canvas('a5h:room', W, H);
    if (built.room === cv) return cv;
    const c = cv.getContext('2d');
    c.setTransform(1, 0, 0, 1, 0, 0);
    // wall: warm plum, lamplit
    let g = c.createLinearGradient(0, 120, 0, 860);
    g.addColorStop(0, '#26132c'); g.addColorStop(0.5, '#41203a'); g.addColorStop(1, '#5e2e3e');
    c.fillStyle = g; c.fillRect(0, 0, W, H);
    // the alcove: soft concentric arches
    const arch = (w, top, col) => {
      c.fillStyle = col;
      c.beginPath();
      c.moveTo(960 - w, 900); c.lineTo(960 - w, top + w * 0.5);
      c.bezierCurveTo(960 - w, top - w * 0.08, 960 + w, top - w * 0.08, 960 + w, top + w * 0.5);
      c.lineTo(960 + w, 900); c.closePath(); c.fill();
    };
    arch(900, 120, '#4c2442');
    arch(805, 178, '#5c2b46');
    arch(712, 232, '#6a324a');
    // wallpaper: faint golden-angle spirals (the same pattern as the flower's heart)
    c.save();
    c.globalAlpha = 0.085;
    for (let i = 0; i < 15; i++) {
      const x = 470 + (i % 5) * 245 + (Math.floor(i / 5) % 2) * 122, y = 300 + Math.floor(i / 5) * 140;
      Art.phyllotaxis(c, { x, y, n: 55, c: 5.4, size: 2.7, color: '#ffd7a0' });
    }
    c.restore();
    // framed pictures: his flower (straight, cherished), the summit (crooked, forgotten)
    const frame = (x, y, w, h, rot, inner) => {
      c.save(); c.translate(x, y); c.rotate(rot);
      c.fillStyle = 'rgba(0,0,0,0.28)'; c.fillRect(-w / 2 + 7, -h / 2 + 9, w, h);
      c.fillStyle = '#b07a4a'; c.fillRect(-w / 2, -h / 2, w, h);
      c.fillStyle = '#8a5a35'; c.fillRect(-w / 2 + 5, -h / 2 + 5, w - 10, h - 10);
      c.fillStyle = '#f2e4cf'; c.fillRect(-w / 2 + 11, -h / 2 + 11, w - 22, h - 22);
      inner(c);
      c.restore();
    };
    frame(640, 352, 150, 184, 0.0, (k) => { Art.flower(k, { x: 0, y: 66, s: 0.6, stemH: 150, bloom: 1, face: 0.9, sway: 0, seed: 2 }); });
    frame(1290, 340, 176, 136, -0.14, (k) => {
      k.save(); k.beginPath(); k.rect(-77, -57, 154, 114); k.clip();
      k.fillStyle = '#cfe0ea'; k.fillRect(-77, -57, 154, 114);
      Art.summit(k, { x: 0, y: 52, h: 92, w: 150, P: Art.TOD.morning, glow: 0, flag: true });
      k.restore();
    });
    // floor: warm boards + a round rug
    g = c.createLinearGradient(0, 850, 0, H);
    g.addColorStop(0, '#5a3427'); g.addColorStop(1, '#2a1715');
    c.fillStyle = g; c.fillRect(0, 850, W, H - 850);
    c.strokeStyle = 'rgba(0,0,0,0.2)'; c.lineWidth = 2;
    for (let i = 0; i < 7; i++) { const y = 862 + i * i * 4.6; c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
    c.fillStyle = '#7a3a3e';
    c.beginPath(); c.ellipse(960, 912, 780, 62, 0, 0, TAU); c.fill();
    c.strokeStyle = '#c98a5e'; c.lineWidth = 5;
    c.beginPath(); c.ellipse(960, 912, 716, 50, 0, 0, TAU); c.stroke();
    c.strokeStyle = 'rgba(201,138,94,0.5)'; c.lineWidth = 3;
    c.beginPath(); c.ellipse(960, 912, 650, 40, 0, 0, TAU); c.stroke();
    // floor lamp (left)
    c.strokeStyle = '#2a1b1c'; c.lineWidth = 9;
    c.beginPath(); c.moveTo(lampX, 880); c.lineTo(lampX, 400); c.stroke();
    c.fillStyle = '#2a1b1c'; c.beginPath(); c.ellipse(lampX, 882, 52, 13, 0, 0, TAU); c.fill();
    c.fillStyle = '#e9a45c';
    c.beginPath(); c.moveTo(lampX - 70, 400); c.lineTo(lampX + 70, 400); c.lineTo(lampX + 40, 296); c.lineTo(lampX - 40, 296); c.closePath(); c.fill();
    c.fillStyle = 'rgba(255,240,200,0.4)';
    c.beginPath(); c.moveTo(lampX - 58, 400); c.lineTo(lampX + 58, 400); c.lineTo(lampX + 54, 389); c.lineTo(lampX - 54, 389); c.closePath(); c.fill();
    // side table (right) — the flower lives in here now
    c.fillStyle = '#4a2a22';
    c.fillRect(1712, 714, 13, 150); c.fillRect(1836, 714, 13, 150);
    c.fillStyle = '#6b3d2c'; Art.roundRect(c, 1690, 696, 180, 24, 7); c.fill();
    Art.pot(c, 1780, 698, 72, 60, '#b5603e');
    // the couch: back, back cushions, arms (seat cushions drawn live, over their feet)
    const couch = '#6e2a3c', couchD = '#541f2e', couchL = '#8a3a4c';
    c.fillStyle = couchD; Art.roundRect(c, 300, 590, 1320, 210, 70); c.fill();
    c.fillStyle = couch;
    for (let i = 0; i < 3; i++) { Art.roundRect(c, 336 + i * 418, 574, 414, 190, 64); c.fill(); }
    c.fillStyle = U.rgba(couchL, 0.45);
    for (let i = 0; i < 3; i++) { Art.roundRect(c, 372 + i * 418, 588, 340, 30, 15); c.fill(); }
    c.fillStyle = couchD; Art.roundRect(c, 250, 676, 140, 210, 56); c.fill(); Art.roundRect(c, 1530, 676, 140, 210, 56); c.fill();
    c.fillStyle = couch; Art.roundRect(c, 260, 664, 120, 80, 40); c.fill(); Art.roundRect(c, 1540, 664, 120, 80, 40); c.fill();
    c.fillStyle = '#3a1520'; c.fillRect(352, 876, 28, 18); c.fillRect(1540, 876, 28, 18);
    built.room = cv;
    return cv;
  }
  function drawMind(ctx, t) {
    const smack = 30.12;
    const push = U.ease(t, MIND, D, 'inOutSine');
    const shakeK = t > smack ? Math.exp(-7 * (t - smack)) : 0;
    const shk = Art.shake(t * 3, 2.4 * shakeK, 21);
    ctx.save();
    ctx.translate(960 + shk.x, 610 + shk.y);
    ctx.scale(1.0 + push * 0.055, 1.0 + push * 0.055);
    ctx.translate(-960, -610);
    ctx.drawImage(roomCanvas(), 0, 0, W, H);
    // lamp light, string lights, the little flower
    const flick = 0.92 + 0.05 * Math.sin(t * 7.3) + 0.03 * U.noise1(t * 3, 4);
    Art.glow(ctx, lampX, 380, 460, '#ffc27a', 0.38 * flick);
    Art.glow(ctx, lampX, 880, 260, '#ffb36b', 0.12 * flick);
    ctx.strokeStyle = 'rgba(40,20,26,0.85)'; ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i <= 26; i++) { const k = i / 26, x = lerp(330, 1590, k); i ? ctx.lineTo(x, lightY(k)) : ctx.moveTo(x, lightY(k)); }
    ctx.stroke();
    for (let i = 1; i < 26; i += 2) {
      const k = i / 26, x = lerp(330, 1590, k), y = lightY(k) + 9;
      const tw = 0.6 + 0.4 * Math.sin(t * 2 + i * 1.7);
      const col = ['#ffd27a', '#ff9fb8', '#9fd8ff', '#b8f5c4'][(i >> 1) % 4];
      Art.glow(ctx, x, y, 30, col, 0.45 * tw);
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x, y, 5.5, 0, TAU); ctx.fill();
    }
    Art.glow(ctx, 1782, 560, 170, Art.FLOWER.tip, 0.24);
    Art.flower(ctx, { x: 1780, y: 642, s: 0.7, stemH: 140, t, glow: 0.5, face: 0.85, sway: 0.4, seed: 2 });
    Art.motes(ctx, { seed: 88, count: 16, x0: 330, x1: 1590, y0: 230, y1: 640, t, color: '#ffd9a8', size: 2.6, drift: 6, wander: 40, glow: 0.8, alpha: 0.38 });
    // a warm hearth-glow behind the five of them
    Art.glow(ctx, 960, 640, 640, '#ff9d7a', 0.12);

    // ---- the five emotions, in perfect sync
    const antic = U.ease(t, 29.78, 30.02, 'outCubic');       // throw their hands up, stretch...
    const hit = t >= smack;                                   // ...SMACK
    const sq = hit ? 0.55 * Math.exp(-6 * (t - smack)) * Math.cos((t - smack) * 16) : -0.35 * antic;
    const sync = U.ease(t, 29.2, 29.7);
    const shake = t > 30.7 ? Math.sin((t - 30.7) * 5.2) * 0.055 * U.fade(t, 30.7, 33.4, 0.3, 0.9) : 0;
    const mutter = U.fade(t, 32.7, 36.2, 0.3, 0.6);
    for (const [name, i] of EMOS) {
      const seed = 3 + (i + 2) * 7;
      const x = EX(i);
      const own = Math.sin(t * 2.2 + seed) * 2.5, common = Math.sin(t * 2.2 + 3) * 2.5;
      const y = SEAT - (own - common) * sync * ES - (hit ? 0 : antic * 10);
      const arms = hit ? 'facepalm' : antic > 0.35 ? 'cheer' : 'idle';
      const face = {
        eyes: antic > 0.35 && !hit ? 'closed' : 'flat',
        smile: hit ? -0.3 : -0.08,
        blink: t < 29.75 ? U.bump(t, 29.35, 0.09) : 0,
        talk: mutter * (0.55 + 0.3 * U.hash(i + 2, 3)),
        brow: hit ? 0.55 : 0.1,
      };
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(shake);
      Art.emotion(ctx, { x: 0, y: 0, s: ES, color: Art.EMO[name], t, seed, arms, face, squash: sq, glow: 0.5 });
      ctx.restore();
      if (hit && t < smack + 0.32) { // impact flicks at each face
        const a = 1 - (t - smack) / 0.32;
        ctx.save();
        ctx.strokeStyle = U.rgba('#fff3dc', a);
        ctx.lineWidth = 4; ctx.lineCap = 'round';
        for (let j = 0; j < 3; j++) {
          const ang = -2.2 + j * 0.62, r0 = 64 + (1 - a) * 18, r1 = r0 + 22;
          const cx = x + 18, cy = y - 128;
          ctx.beginPath(); ctx.moveTo(cx + Math.cos(ang) * r0, cy + Math.sin(ang) * r0); ctx.lineTo(cx + Math.cos(ang) * r1, cy + Math.sin(ang) * r1); ctx.stroke();
        }
        ctx.restore();
      }
      if (mutter > 0.02) { // muttering squiggles
        ctx.save();
        ctx.globalAlpha = mutter * (0.45 + 0.45 * Math.sin(t * 8 + i * 2));
        ctx.strokeStyle = '#f6dcc0'; ctx.lineWidth = 2.6; ctx.lineCap = 'round';
        const mx = x + 44, my = y - 96 + Math.sin(t * 3 + i) * 3;
        ctx.beginPath();
        for (let j = 0; j <= 10; j++) { const px = mx + j * 3.2, py = my - j * 1.6 + Math.sin(j * 1.6 + t * 12) * 2.6; j ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
        ctx.stroke();
        ctx.restore();
      }
    }
    // seat cushions in front of their feet: they sink in
    ctx.fillStyle = '#7b3043';
    for (let i = 0; i < 3; i++) { Art.roundRect(ctx, 340 + i * 414, SEAT - 16, 412, 78, 30); ctx.fill(); }
    ctx.fillStyle = 'rgba(255,200,170,0.10)';
    for (let i = 0; i < 3; i++) { Art.roundRect(ctx, 362 + i * 414, SEAT - 11, 366, 13, 6); ctx.fill(); }
    ctx.fillStyle = '#5a2131'; Art.roundRect(ctx, 320, SEAT + 54, 1280, 64, 24); ctx.fill();
    ctx.restore();

    // "They’ll never get it." — small, weary, handwritten
    // written on just as the narration ends, then held: the scene's own fade-out takes it
    const rv = U.ease(t, 32.85, 34.1, 'linear');
    if (rv > 0) {
      ctx.save();
      ctx.translate(960, 468 + U.ease(t, 32.85, 37) * 8);
      ctx.rotate(-0.025);
      Art.hand(ctx, 'They’ll never get it.', { x: 0, y: 0, size: 54, reveal: rv, color: '#f6dcc0', alpha: 0.92, glow: 'rgba(255,170,120,0.35)' });
      ctx.restore();
    }
  }

  Film.scene({
    id: 'three-heads',
    order: 8,
    title: 'Three Heads',
    duration: D,
    moods: [[0, 'dusk'], [13.8, 'comedy']],
    sfx: [
      [0.45, 'heartbeat', { gain: 0.35 }],
      [9.9, 'heartbeat', { gain: 0.4 }],
      [10.1, 'shimmer', { gain: 0.35 }],
      [HEADS0, 'boing', { gain: 0.6 }],
      [HEADS0 + 0.25, 'boing', { gain: 0.55 }],
      [18.6, 'sparkle', { gain: 0.4 }],
      [HEADS1, 'pop', { gain: 0.5 }],
      [HEADS1 + 0.15, 'pop', { gain: 0.45 }],
      [27.75, 'whoosh', { gain: 0.55 }],
      [MIND, 'chime', { gain: 0.3 }],
      [30.12, 'thud', { gain: 0.7 }],
      [30.6, 'sigh', { gain: 0.35 }],
      [32.8, 'whisper', { gain: 0.4 }],
    ],
    fadeIn: 0,
    fadeOut: 1.2,
    post: (t) => ({ vignette: t >= MIND ? 0.55 : 0.42, grain: 0.05, letterbox: 1 }),

    render(ctx, t) {
      if (t >= MIND) {
        drawMind(ctx, t);
        // the warm flash we came through
        const fl = 1 - U.ease(t, MIND, MIND + 0.6, 'outCubic');
        if (fl > 0.01) { ctx.fillStyle = U.rgba('#fff1d6', fl); ctx.fillRect(0, 0, W, H); }
        Art.captions(ctx, t, NARR);
        return;
      }
      const P = pal(t);
      const cam = camAt(t);
      drawBackdrop(ctx, P, cam, t);
      drawGround(ctx, P, cam, t);

      ctx.save();
      applyCam(ctx, cam, 1);
      const glowK = 0.9 + 0.1 * Math.sin(t * 1.6) + 0.25 * U.fade(t, 9.9, 12.8, 0.4, 0.8);
      Art.glow(ctx, ME_SX + 4, MEY - 150, 230, '#ffd38a', 0.28 * glowK);
      shadow(ctx, ME_SX, MEY, 40);
      const A = {};
      for (let i = HIKERS.length - 1; i >= 0; i--) A[HIKERS[i].k] = drawHiker(ctx, P, HIKERS[i], t);
      A.me = drawMe(ctx, P, t);
      const fglow = 1.2 + 0.12 * Math.sin(t * 1.3);
      unveil(ctx, (c) => drawMe(c, P, t), A.me, t, fglow);
      clump(ctx, P, t);
      mossRock(ctx, FX + 64, gy(FX + 64) + 48, 104, 64, tintOf(P));
      drawFlower(ctx, P, t, fglow);
      ctx.restore();
      verge(ctx, P, cam, t);

      // sparkles: around him (and his extra heads)
      ctx.save(); applyCam(ctx, cam, 1);
      const faces = [A.me.head].concat(A.me.extra);
      sparkles(ctx, A.me.head, t, 8, 0.9, 0, A.me.extra);
      if (t > HEADS0 && t < HEADS1 + 0.3) {
        const r = A.me.head.r;
        const k = U.fade(t, HEADS0 + 0.2, HEADS1 + 0.2, 0.3, 0.2);
        sparkles(ctx, { x: A.me.head.x - r * 2.0, y: A.me.head.y + r * 0.34, r }, t, 5, k, 30, faces);
        sparkles(ctx, { x: A.me.head.x + r * 2.0, y: A.me.head.y + r * 0.34, r }, t, 5, k, 60, faces);
      }
      Art.motes(ctx, { seed: 52, count: 14, x0: 300, x1: 2300, y0: 600, y1: 900, t: t + 37.2, color: '#fff0a8', size: 2.0, drift: 3, wander: 46, glow: 1, blink: 1, alpha: 0.9 });
      Art.motes(ctx, { seed: 53, count: 9, x0: 560, x1: 1100, y0: 640, y1: 900, t: t + 37.2, color: '#fff3b8', size: 2.2, drift: 2, wander: 38, glow: 1, blink: 1, alpha: 0.95 });
      ctx.restore();

      // the rush into his head: a warm bloom swallows the frame
      const fl = U.ease(t, 28.35, MIND, 'inCubic');
      if (fl > 0.01) {
        const hs = toScreen(cam, HEAD);
        Art.glow(ctx, hs.x, hs.y, 900, '#fff1d6', fl);
        ctx.fillStyle = U.rgba('#fff1d6', fl * fl);
        ctx.fillRect(0, 0, W, H);
      }

      // dialogue
      const sp = (k) => {
        const a = A[k];
        return { f: k === 'me' ? 1 : -1, head: toScreen(cam, a.head), r: a.head.r * cam.z, mouth: toScreen(cam, a.mouth), top: toScreen(cam, a.top) };
      };
      const heads = Object.keys(A).map((k) => { const hs = toScreen(cam, A[k].head); return { x: hs.x, y: hs.y, r: A[k].head.r * cam.z * 1.25 }; });
      const cues = [];
      for (const q of TALK) {
        if (t < q[0] - 0.05 || t > q[1] + 0.05) continue;
        const who = q[3].who;
        cues.push([q[0], q[1], q[2], Object.assign({ who }, place(ctx, q[2], sp(who), heads, who === 'me' ? 640 : 520))]);
      }
      for (const q of cues) balloon(ctx, t, q[0], q[1], q[2], q[3]);
      Art.captions(ctx, t, NARR);
    },
  });
})();
