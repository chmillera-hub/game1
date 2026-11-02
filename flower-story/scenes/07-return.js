/* ==========================================================================
   07 · The Return — dusk at the flower spot. The hikers trudge back down the
   trail (walking LEFT), spent and glassy-eyed. "me" has spent the afternoon
   with his flower; he rises to meet them, asks his question, gets a shrug,
   and beams.
   Shots: A wide crane-down · B tracking the hikers → pull back as they arrive
   · C2 two-shot (question) · C3 the group shrug · C4 two-shot (h1) · C5 MCU me.
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 37.2;
  const K = U.keys;

  /* ------------------------------------------------------------------ world */
  const GO = { y: 870, amp: 16, offset: 2100 };          // the trail-scene ground line
  const gy = (x) => Art.groundY(x, GO);
  const TR = 20;                                          // walking surface, on the trail band
  const S = 0.8;                                          // cast scale
  const FX = 820;                                         // the hero flower
  const FY = gy(FX) + 60;                                 // ...just in front of the trail
  const MEX = 702;                                        // me: hip x while sitting
  const MEY = gy(MEX) + TR;
  const ME_DX = 34;                                       // rises forward onto his feet (local units)
  const ME_SX = MEX + ME_DX * S;                          // standing x
  const SEED = { me: 763, h1: 11, h2: 23, h3: 37, h4: 41 };
  const P = Art.TOD.dusk;                                 // 07 holds at dusk; 08 deepens it
  const TINT = U.mix(P.sky[0], P.sky[1], 0.45);           // ambient dusk light on the cast
  const WARM = '#ffb48a';                                 // the flower's light

  /* ------------------------------------------------------------- camera */
  // 2.5D camera: a layer at depth d (0 = sky, 1 = the action plane, >1 = foreground)
  const camD = (c, d) => ({ x: 960 + (c.x - 960) * d, y: 540 + (c.y - 540) * d, z: 1 + (c.z - 1) * d });
  const applyCam = (ctx, c, d) => { const k = camD(c, d); ctx.translate(960, 540); ctx.scale(k.z, k.z); ctx.translate(-k.x, -k.y); return k; };
  const toScreen = (c, p, d = 1) => { const k = camD(c, d); return { x: 960 + (p.x - k.x) * k.z, y: 540 + (p.y - k.y) * k.z }; };

  /* --------------------------------------------------------------- gait */
  // Art.person's walk legs, replicated so feet can be planted exactly. The
  // nominal stance leg is B while cos(ph) >= 0, F otherwise.
  const legA = (ph, st, leg) => leg * 0.42 * st * Math.sin(ph);
  const legK = (ph, st, leg) => -(0.12 + Math.max(0, leg * Math.cos(ph)) * 0.75 * st);
  const footX = (ph, st, leg) => { const a = legA(ph, st, leg); return 3 * leg + 58 * Math.sin(a) + 56 * Math.sin(a + legK(ph, st, leg)); };
  const footY = (ph, st, leg) => {
    const a = legA(ph, st, leg);
    return -118 + Math.abs(Math.sin(ph)) * 5 * st - 3 * st + 58 * Math.cos(a) + 56 * Math.cos(a + legK(ph, st, leg));
  };
  const gaitD = (ph, stf) => { // body travel (local units) from ph = -PI/2
    const P0 = -Math.PI / 2;
    const n = Math.max(0, Math.floor((ph - P0) / Math.PI));
    let d = 0;
    for (let i = 0; i <= n; i++) {
      const a = P0 + i * Math.PI, b = Math.min(ph, a + Math.PI), leg = i % 2 ? 1 : -1;
      d += footX(a, stf(a), leg) - footX(b, stf(b), leg);
    }
    return d;
  };
  const makeWalker = (o) => {
    const w = Object.assign({ facing: -1, st0: 0.68, st1: 0.16, Td: 1.3, n: 9, v: 64 }, o);
    w.S = S * Art.CAST[w.k].height;
    w.phEnd = Math.PI / 2 + TAU * w.n;
    w.stf = (p) => (p < w.phEnd - Math.PI ? w.st0 : lerp(w.st0, w.st1, U.smooth((p - (w.phEnd - Math.PI)) / Math.PI)));
    const C = (footX(-Math.PI / 2, w.st0, -1) - footX(Math.PI / 2, w.st0, -1)) / Math.PI;
    w.r0 = w.v / (C * w.S);
    w.dEnd = gaitD(w.phEnd, w.stf);
    return w;
  };
  const walkAt = (w, t) => {
    const tau = w.tStop - t;
    const R = tau <= 0 ? 0 : tau < w.Td ? (w.r0 * tau * tau) / (2 * w.Td) : w.r0 * (tau - w.Td / 2);
    const ph = w.phEnd - R;
    const st = w.stf(ph);
    const x = w.x + w.facing * w.S * (gaitD(ph, w.stf) - w.dEnd);
    // seat the lowest foot on the ground (the kit's walk floats a few px)
    const lift = (-3.1 - Math.max(footY(ph, st, 1), footY(ph, st, -1))) * w.S;
    return { x, y: gy(x) + TR + lift, gy: gy(x) + TR, ph, st, moving: tau > 0 };
  };
  // the walk rig's arm swing (for blending into gestures once stopped)
  const walkArms = (ph, st, tired) => {
    const sw = Math.sin(ph) * 0.5 * st * (1 - tired * 0.5);
    return [-sw * 0.9 + 0.04, 0.25 + Math.max(0, -sw) * 0.6, sw * 0.9 - 0.04, 0.25 + Math.max(0, sw) * 0.6];
  };
  const HIKERS = [
    makeWalker({ k: 'h1', x: FX + 250, tStop: 13.0 }),
    makeWalker({ k: 'h2', x: FX + 402, tStop: 13.35 }),
    makeWalker({ k: 'h3', x: FX + 545, tStop: 13.7 }),
    makeWalker({ k: 'h4', x: FX + 694, tStop: 14.1 }),
  ];

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
  const SHRUG = [0.42, 2.0, -0.12, 1.9];                 // forearms up, palms up — reads in profile
  // light the cast: every look color pulled toward the dusk ambient (+ warm spill)
  const LOOK_KEYS = ['skin', 'hair', 'hatColor', 'shirt', 'shirt2', 'pants', 'shoes', 'pack', 'beard'];
  const lit = (key, amt, warm) => {
    const b = Art.CAST[key], o = Object.assign({}, b);
    for (const k of LOOK_KEYS) if (b[k]) o[k] = U.mix(U.mix(b[k], TINT, amt), WARM, warm);
    return o;
  };

  /* -------------------------------------------------------------- shots */
  const SHOTS = [
    { id: 'A', t0: 0 }, { id: 'B', t0: 6.8 }, { id: 'C2', t0: 16.0 },
    { id: 'C3', t0: 21.4 }, { id: 'C4', t0: 23.6 }, { id: 'C5', t0: 28.6 },
  ];
  const shotAt = (t) => { let s = SHOTS[0]; for (const x of SHOTS) if (t >= x.t0) s = x; return s; };
  const groupCenter = (t) => { let a = 0; for (const w of HIKERS) a += walkAt(w, t).x; return a / HIKERS.length; };
  function camAt(t, still) {
    const s = shotAt(t);
    let c;
    if (s.id === 'A') {
      const [x, y, z] = K(t, [[0, [1030, 330, 1.12]], [5.9, [1062, 650, 1.0], 'inOutSine'], [6.8, [1066, 652, 1.0], 'outSine']]);
      c = { x, y, z };
    } else if (s.id === 'B') {
      // track the trudging group, then ease off and pull back as they arrive
      const k = U.ease(t, 11.2, 14.4, 'inOutSine');
      c = { x: lerp(groupCenter(t) - 110, 985, k), y: lerp(718, 690, k), z: lerp(1.55, 1.22, k) };
    } else if (s.id === 'C2') {
      c = { x: 905, y: 712, z: lerp(1.62, 1.7, U.ease(t, 16, 21.4, 'inOutSine')) };
    } else if (s.id === 'C3') {
      c = { x: 1302, y: 708, z: lerp(1.44, 1.5, U.ease(t, 21.4, 23.6, 'inOutSine')) };
    } else if (s.id === 'C4') {
      c = { x: 935, y: 712, z: lerp(1.66, 1.73, U.ease(t, 23.6, 28.6, 'inOutSine')) };
    } else {
      c = { x: lerp(772, 780, U.ease(t, 28.6, D, 'inOutSine')), y: 694, z: lerp(2.12, 2.3, U.ease(t, 28.6, D + 1, 'inOutSine')) };
    }
    if (!still) {
      const sh = Art.shake(t, s.id === 'A' ? 0.25 : 0.35, 7);
      c.x += sh.x / c.z; c.y += sh.y / c.z;
    }
    c.id = s.id;
    return c;
  }
  // each static shot's rest camera (mid-shot, no handheld drift): its backdrop plate is built from it
  const refCam = (id) => {
    const i = SHOTS.findIndex((s) => s.id === id);
    const t1 = i + 1 < SHOTS.length ? SHOTS[i + 1].t0 : D + 1;
    return camAt((SHOTS[i].t0 + t1) / 2, true);
  };

  /* ----------------------------------------------------------- dialogue */
  const TALK = [
    [16.3, 21.3, 'Did you find the meaning you were looking for at the summit?', { who: 'me' }],
    [23.75, 26.0, 'It was fine, I guess.', { who: 'h1' }],
    [26.35, 28.5, 'What about you?', { who: 'h1' }],
    [29.25, 31.6, 'I found a flower.', { who: 'me' }],
    [31.95, 36.7, 'And not just any flower—a flower I gave meaning to.', { who: 'me' }],
  ];
  const NARR = [
    [1.2, 4.7, 'Later, when the hikers come back down,'],
    [7.1, 11.9, 'they’re sweaty and tired, with a distant look in their eyes.'],
  ];

  /* ------------------------------------------------- background layers */
  // Each layer lives at its own depth. In the wide (A) they're drawn live and
  // sharp; in the closer shots they come from small cached canvases, which
  // read as a soft depth of field when scaled up — and cost nothing per frame.
  const forestW = (c, o, x0, x1) => { // Art.forest's placement, over an explicit world range
    const sp = o.spacing, i0 = Math.floor((x0 - 300) / sp), i1 = Math.ceil((x1 + 300) / sp);
    for (let i = i0; i <= i1; i++) {
      const r1 = U.hash(i, o.seed), r2 = U.hash(i, o.seed + 1), r3 = U.hash(i, o.seed + 2);
      const x = i * sp + (r2 - 0.5) * sp * 0.9;
      const h = lerp(o.hMin, o.hMax, r1);
      const col = U.shade(o.color, (r3 - 0.5) * 0.12);
      const yy = o.y + (r3 - 0.5) * 24;
      const sw = o.sway ? o.sway * U.wind(o.t, x, i) : 0;
      if (o.kind === 'mix' && r3 < 0.32) Art.roundTree(c, x, yy, h * 0.85, col, { sway: sw, light: o.light, seed: i });
      else Art.pine(c, x, yy, h, col, { sway: sw, light: o.light, w: 0.4 * (0.85 + r2 * 0.3) });
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
    { id: 'clouds', d: 0.05, r: [-560, 40, 2560, 540], draw(c, x0, x1, t) {
      skyClouds(c, P);
    } },
    { id: 'far', d: 0.09, r: [-60, 140, 2040, 1110], draw(c, x0, x1, t) {
      Art.ridge(c, { seed: 21, y: 660, amp: 180, color: U.mix(P.far, P.sky[1], 0.4), x0: x0 - 40, x1: x1 + 40, bottom: 1300 });
      const tip = Art.summit(c, { x: 1545, y: 664, h: 450, w: 790, P, glow: 0.5, t, flag: true });
      Art.glow(c, tip.x - 30, tip.y + 170, 360, U.mix(P.summit, P.snow, 0.4), 0.2);
      Art.glow(c, tip.x, tip.y + 30, 150, P.snow, 0.14);
      Art.fog(c, { y: 668, h: 210, color: P.fog, alpha: 0.5 });
    } },
    { id: 'mid', d: 0.2, r: [-60, 600, 2100, 1110], draw(c, x0, x1, t) {
      Art.ridge(c, { seed: 8, y: 742, amp: 110, color: P.mid, x0: x0 - 40, x1: x1 + 40, bottom: 1300 });
      Art.fog(c, { y: 748, h: 120, color: P.fog, alpha: 0.28 });
    } },
    { id: 'trees1', d: 0.38, r: [-80, 560, 2160, 880], draw(c, x0, x1, t) {
      forestW(c, { seed: 31, y: 800, spacing: 64, hMin: 120, hMax: 210, color: P.trees[0], light: U.mix(P.trees[0], P.sky[2], 0.14), t }, x0, x1);
      Art.fog(c, { y: 795, h: 150, color: P.fog, alpha: 0.3 });
    } },
    { id: 'trees2', d: 0.62, r: [-80, 480, 2280, 900], draw(c, x0, x1, t) {
      forestW(c, { seed: 32, y: 856, spacing: 96, hMin: 210, hMax: 330, color: P.trees[1], kind: 'mix', light: U.mix(P.trees[1], P.sky[2], 0.12), sway: 4, t }, x0, x1);
      Art.fog(c, { y: 852, h: 110, color: P.fog, alpha: 0.2 });
    } },
  ];
  const BLUR_RES = 0.36;
  const built = {};
  function layerCanvas(L) {
    const [x0, y0, x1, y1] = L.r;
    const key = 'a5r:' + L.id;
    const cv = Art.canvas(key, (x1 - x0) * BLUR_RES, (y1 - y0) * BLUR_RES);
    if (built[key] !== cv) {
      const c = cv.getContext('2d');
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, cv.width, cv.height);
      c.setTransform(BLUR_RES, 0, 0, BLUR_RES, -x0 * BLUR_RES, -y0 * BLUR_RES);
      L.draw(c, x0, x1, 0);
      built[key] = cv;
    }
    return cv;
  }
  // Cost control (software raster pays per destination pixel, ~3x more for
  // 'high' smoothing): the sky is one padded full-res plate blitted at whole
  // pixels; the tracking shot (B) draws the soft layers with bilinear
  // filtering; the static shots (C*) flatten the four depth layers once per
  // shot into a half-res plate, re-projected each frame with one scale+offset
  // at a mid depth (their slow push-ins move the layers by < 2% relative to
  // one another — invisible on a soft backdrop).
  const baseK = () => (Art._base && Art._base.a) || 1;
  function drawLayers(ctx, cam, t, soft, only) {
    for (const L of LAYERS) {
      if (only && L.id !== only) continue;
      ctx.save();
      const k = applyCam(ctx, cam, L.d);
      if (soft) {
        const [x0, y0, x1, y1] = L.r;
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'low';
        ctx.drawImage(layerCanvas(L), x0 - (L.id === 'clouds' ? t * 4 : 0), y0, x1 - x0, y1 - y0);
      } else {
        if (L.id === 'clouds') ctx.translate(-t * 4, 0);
        L.draw(ctx, k.x - 960 / k.z - 60, k.x + 960 / k.z + 60, t);
      }
      ctx.restore();
    }
  }
  const PLATE_R = 0.5, PM = 48, DREF = 0.35;
  function layerPlate(id) {
    const r = PLATE_R * baseK();
    const w = Math.ceil((W + 2 * PM) * r), h = Math.ceil((H + 2 * PM) * r);
    const cv = Art.canvas('a5r:plate', w, h);
    const key = id + ':' + w + 'x' + h;
    if (built.plate !== key) {
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
        c.drawImage(layerCanvas(L), x0, y0, x1 - x0, y1 - y0);
      }
      built.plate = key;
      built.plateCam = c0;
    }
    return cv;
  }
  function drawPlate(ctx, cam) {
    const cv = layerPlate(cam.id);
    const k = camD(cam, DREF), k0 = camD(built.plateCam, DREF);
    const A = k.z / k0.z;
    const bx = 960 * (1 - A) + (k0.x - k.x) * k.z, by = 540 * (1 - A) + (k0.y - k.y) * k.z;
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(cv, bx - PM * A, by - PM * A, (W + 2 * PM) * A, (H + 2 * PM) * A);
    ctx.restore();
  }
  const SKY_PAD = 64, SKY_H = 860;               // below ~700 px the far ridge's fill always covers the sky
  function skyPlate() {
    const k = baseK();
    const w = Math.ceil((W + 2 * SKY_PAD) * k), h = Math.ceil((SKY_H + SKY_PAD) * k);
    const cv = Art.canvas('a5r:sky', w, h);
    const key = w + 'x' + h;
    if (built.sky !== key) {
      const c = cv.getContext('2d');
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, w, h);
      c.setTransform(k, 0, 0, k, SKY_PAD * k, SKY_PAD * k);
      Art.sky(c, P, { horizon: 790 });
      Art.glow(c, 250, 780, 900, P.sun, 0.22);
      built.sky = key;
    }
    return cv;
  }
  function drawSky(ctx, cam, t) {
    // the depth-0.03 view barely zooms (≤ 4%): blit the plate anchored at the low sun / horizon
    const k = baseK(), kd = camD(cam, 0.03);
    const ox = 960 + (250 - kd.x) * kd.z - 250, oy = 540 + (790 - kd.y) * kd.z - 790;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(skyPlate(), Math.round((ox - SKY_PAD) * k), Math.round((oy - SKY_PAD) * k));
    ctx.restore();
    ctx.save();
    applyCam(ctx, cam, 0.03);
    Art.stars(ctx, { seed: 17, count: 70, t, alpha: 0.2 + 0.25 * U.ease(t, 0, D), y0: -60, y1: 380, x0: -100, x1: W + 100 });
    ctx.restore();
  }
  // out-of-focus foreground framing (wide + tracking shots only): cached once, very soft;
  // drawn as sub-rects around its four shapes so the filter never touches empty pixels
  const FG = { d: 1.45, r: [-120, 280, 2340, 1330], R: 0.2,
    parts: [[-40, 290, 450, 1330], [1100, 935, 1400, 1160], [1425, 905, 1775, 1165], [1995, 895, 2305, 1130]] };
  function fgCanvas() {
    const R = FG.R, [x0, y0, x1, y1] = FG.r;
    const cv = Art.canvas('a5r:fg', (x1 - x0) * R, (y1 - y0) * R);
    if (built.fg !== cv) {
      const c = cv.getContext('2d');
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, cv.width, cv.height);
      c.setTransform(R, 0, 0, R, -x0 * R, -y0 * R);
      const dark = U.mix(P.trees[2], '#07060c', 0.5);
      Art.pine(c, 208, 1300, 1000, dark, {});
      Art.fern(c, 1250, 1110, 1.8, dark, 0.3);
      Art.fern(c, 1600, 1110, 2.2, dark, -0.2);
      Art.fern(c, 2150, 1080, 1.9, dark, 0.4);
      built.fg = cv;
    }
    return cv;
  }
  // these small caches don't depend on the output resolution: build them at
  // load so the scene's first frames don't hitch (lazily, if this ever fails)
  try { for (const L of LAYERS) layerCanvas(L); fgCanvas(); } catch (e) { /* built on first use */ }
  function drawFG(ctx, cam) {
    const cv = fgCanvas(), R = FG.R, [x0, y0] = FG.r;
    ctx.save();
    const k = applyCam(ctx, cam, FG.d);
    const vx0 = k.x - 960 / k.z, vx1 = k.x + 960 / k.z, vy0 = k.y - 540 / k.z, vy1 = k.y + 540 / k.z;
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    for (const [px0, py0, px1, py1] of FG.parts) {
      if (px1 < vx0 || px0 > vx1 || py1 < vy0 || py0 > vy1) continue;
      ctx.drawImage(cv, (px0 - x0) * R, (py0 - y0) * R, (px1 - px0) * R, (py1 - py0) * R, px0, py0, px1 - px0, py1 - py0);
    }
    ctx.restore();
  }

  /* ------------------------------------------------------ ground plane */
  function drawGround(c, cam, t) {
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
    Art.glow(c, FX, FY - 20, 240, Art.FLOWER.tip, 0.06);
    c.restore();
  }
  function drawNearGrass(c, cam, t) {
    c.save();
    const k = applyCam(c, cam, 1);
    const x0 = k.x - 960 / k.z, x1 = k.x + 960 / k.z;
    Art.grass(c, { seed: 9, y: (x) => gy(x) + 50, x0: x0 - 30, x1: x1 + 30, spacing: 7, h: 16, color: U.shade(P.grass, -0.2), color2: U.shade(P.grass, -0.04), t, wind: 0.7 });
    c.restore();
  }

  // the verge between trail and camera: tufts, small ferns, stones (keeps the spot clear)
  function verge(c, cam, t) {
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
    c.restore();
  }

  /* --------------------------------------------------- the flower spot */
  function mossRock(c, x, y, w, h) {
    const base = U.mix('#8a8f86', TINT, 0.32);
    Art.rock(c, x, y, w, h, base, 3);
    c.save();
    c.beginPath();
    c.moveTo(x - w / 2, y);
    c.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(3, 1) * 8, y - h);
    c.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    c.lineTo(x + w / 2, y);
    c.closePath();
    c.clip();
    const moss = U.mix('#6f9446', TINT, 0.3);
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
    // the flower's warm light catching the rock's left shoulder
    c.fillStyle = U.rgba(WARM, 0.16);
    c.beginPath(); c.ellipse(x - w * 0.42, y - h * 0.5, w * 0.24, h * 0.5, 0, 0, TAU); c.fill();
    c.restore();
  }
  // the undergrowth in front of where he sits: bush, ferns, grass (hides his legs)
  function clump(c, t) {
    const x = MEX + 40, y = MEY + 26;
    const dark = U.mix(P.trees[2], P.grass, 0.35), mid = U.mix(P.grass, P.trees[2], 0.2), fern = U.shade(P.grass, 0.06);
    Art.bush(c, x - 8, y + 2, 47, dark, null, 4);
    Art.fern(c, x - 34, y + 4, 0.86, mid, U.wind(t, x, 2) * 0.7);
    Art.grass(c, { seed: 77, y: y + 8, x0: x - 82, x1: x + 70, spacing: 5, h: 40, hVar: 0.7, color: dark, color2: mid, t, wind: 0.6 });
    Art.fern(c, FX - 52, FY + 4, 1.05, fern, U.wind(t, FX, 3) * 0.9);   // the spot's fern
  }
  function drawFlower(c, t, glow) {
    Art.glow(c, FX + 4, FY - 108, 150, Art.FLOWER.tip, 0.12 * glow);
    const f = Art.flower(c, { x: FX, y: FY, s: 0.66, stemH: 160, t, glow: 0.42 * glow, face: 0.84, sway: 0.55, seed: 2 });
    Art.grass(c, { seed: 12, y: FY + 4, x0: FX - 40, x1: FX + 36, spacing: 6, h: 22, color: U.shade(P.grass, -0.1), color2: U.shade(P.grass, 0.08), t, wind: 0.7 });
    return f;
  }

  /* ----------------------------------------------------------------- me */
  // sit → rise → stand. While rising, his legs are behind the bush, so the
  // upper body (all we see) can move continuously: a standing figure, sunk
  // and clipped at the ground, rides up with lean and push-off arms.
  const RISE0 = 13.9, RISE1 = 15.1;
  const HANDS_F = { x: MEX - 26 * S, y: MEY - 4 * S }, HANDS_B = { x: MEX - 34 * S, y: MEY - 3 * S };
  function meFace(t) {
    const beam = U.ease(t, 28.75, 29.2, 'outBack');
    const notice = U.ease(t, 12.3, 12.8, 'outCubic');
    const f = {
      smile: lerp(lerp(0.42, 0.72, notice), 1, beam),
      eyes: t >= 28.85 ? 'sparkle' : t < 2.6 ? 'happy' : 'open',
      browUp: notice * 0.35 * (1 - U.ease(t, 15.5, 16.5)) + beam * 0.5 + U.bump(t, 27.6, 0.6) * 0.6,
      open: beam * (0.28 + 0.1 * Math.sin(t * 2.1)),
      talk: Art.talkingAt(t, TALK, 'me'),
      blush: 0.15 + beam * 0.3,
    };
    if (t >= 28.6 && t < 28.85) { f.eyes = 'wide'; f.blink = 0; }
    return f;
  }
  function drawMe(c, t) {
    const beamK = U.ease(t, 28.75, 29.4, 'outCubic');
    const look = lit('me', 0.2 - beamK * 0.08, 0.1 + beamK * 0.08);
    const face = meFace(t);
    const lean0 = -0.12 * (1 - U.ease(t, 12.5, 13.4));                // sitting back on his hands
    const tilt = K(t, [[0, 0.16], [12.3, 0.16], [12.8, -0.06, 'outCubic'], [RISE0, -0.04]]);
    const k = U.prog(t, RISE0, RISE1);
    if (t < RISE0) {
      return Art.person(c, { x: MEX, y: MEY, s: S, look, pose: 'sit', t, seed: SEED.me, lean: lean0, head: { tilt: tilt + Math.sin(t * 0.7) * 0.02 }, face, reachF: HANDS_F, reachB: HANDS_B, shadow: false });
    }
    if (k < 1) {
      const h = K(k, [[0, 22], [0.18, 22], [0.8, 118.6, 'inOutCubic'], [1, 117, 'inOutSine']]);
      const dx = K(k, [[0, 0], [0.16, 0], [0.76, ME_DX, 'inOutSine'], [1, ME_DX]]);
      const lean = K(k, [[0, lean0], [0.24, 0.4, 'inOutSine'], [0.58, 0.24], [0.86, -0.05], [1, 0]]);
      const xd = MEX + dx * S, yd = MEY + S * (117 - h);
      const loc = (p) => ({ x: (p.x - xd) / S, y: (p.y - yd) / S });
      const sh = shoulders(t, SEED.me, lean, 0, -117, 0);
      const ikF = ik(sh.F, loc(HANDS_F)), ikB = ik(sh.B, loc(HANDS_B));
      const w = U.ease(k, 0.32, 0.9, 'inOutSine');
      const sw = Math.sin(U.prog(k, 0.32, 1) * Math.PI) * 0.4;
      const A = mixA([ikF[0], ikF[1], ikB[0], ikB[1]], [STAND[0] + sw, STAND[1] + sw * 0.6, STAND[2] + sw * 0.5, STAND[3] + sw * 0.3], w);
      c.save();
      c.beginPath(); c.rect(-4000, -4000, 9000, MEY + 4002); c.clip();
      const a = Art.person(c, { x: xd, y: yd, s: S, look, pose: 'stand', t, seed: SEED.me, lean, head: { tilt: lerp(-0.04, -0.1, Math.sin(k * Math.PI)) }, face, armF: [A[0], A[1]], armB: [A[2], A[3]], shadow: false });
      c.restore();
      return a;
    }
    // standing: gestures as explicit arm angles (blendable), IK for presenting/heart
    const sh = shoulders(t, SEED.me, 0, 0, -117, 0);
    const locW = (p) => ({ x: (p.x - ME_SX) / S, y: (p.y - MEY) / S });
    const wobble = Math.sin(t * 10) * 0.32;
    const wave = U.fade(t, 15.15, 15.95, 0.3, 0.35);
    const point = U.fade(t, 18.0, 20.3, 0.35, 0.5);
    const openG = U.fade(t, 16.4, 21.0, 0.5, 0.6) * (1 - point);
    const joy = U.ease(t, 28.75, 29.25, 'outBack') * (1 - U.ease(t, 29.4, 30.0));
    const sway = Math.sin(t * 1.7 + SEED.me) * 0.015;
    let A = [STAND[0] + sway, STAND[1], STAND[2], STAND[3]];
    A = mixA(A, [2.15, 0.62 + wobble, -0.06, 0.16], wave);
    A = mixA(A, [0.85, 0.55, -0.45, 0.38], openG * 0.75);
    A = mixA(A, [1.66, 0.14, -0.12, 0.2], point);                 // an open palm: "up there"
    A = mixA(A, [0.7, 0.9, -0.5, 0.6], joy);
    // present the flower, then the hand finds his heart
    const present = U.fade(t, 29.35, 32.6, 0.55, 0.7);
    const heart = U.ease(t, 33.0, 33.9, 'inOutSine');
    if (present > 0) {
      const p = ik(sh.F, locW({ x: FX - 6, y: FY - 108 }));
      A = mixA(A, [p[0], p[1], A[2], A[3]], present);
    }
    if (heart > 0) {
      const p = ik(sh.F, { x: 16 + sh.F.x - 3, y: -184 });
      A = mixA(A, [p[0], p[1], A[2], A[3]], heart);
    }
    const lookFlower = U.fade(t, 29.5, 31.2, 0.45, 0.6);
    const bob = -Math.abs(Math.sin(U.prog(t, 28.75, 29.55) * Math.PI)) * 4;
    const nod = U.bump(t, 24.9, 0.35) * 0.08 + U.bump(t, 27.4, 0.3) * 0.06;
    return Art.person(c, {
      x: ME_SX, y: MEY + bob, s: S, look, pose: 'stand', t, seed: SEED.me,
      lean: -0.03 * joy, shrug: U.bump(t, 28.5, 0.35) * 0.3,
      head: { tilt: -0.04 + lookFlower * 0.2 - joy * 0.08 + nod - point * 0.1, turn: 0.12 * U.fade(t, 15.1, 21.3, 0.4, 0.4) },
      face, armF: [A[0], A[1]], armB: [A[2], A[3]], shadow: false,
    });
  }
  const meX = (t) => (t < RISE0 ? MEX + 30 : lerp(MEX + 30, ME_SX, U.ease(t, RISE0, RISE1)));

  /* ------------------------------------------------------------- hikers */
  function hikerFace(i, t, w, h) {
    const talk = i === 0 ? Art.talkingAt(t, TALK, 'h1') : 0;
    const shrug = U.fade(t, 22.0, 23.35, 0.2, 0.45);
    const pant = w.moving ? 0.12 + 0.1 * Math.abs(Math.sin(t * 4.2 + i)) : 0.1 * (1 - U.ease(t, h.tStop, h.tStop + 3)) * Math.abs(Math.sin(t * 3.6 + i));
    const f = { eyes: 'distant', smile: -0.16, sweat: 1 - 0.4 * U.ease(t, 20, 30), open: pant, talk, brow: 0.15 };
    if (shrug > 0.5) { f.eyes = i === 1 ? 'closed' : 'flat'; f.smile = -0.32; f.browUp = 1; f.brow = -0.05; f.open = 0; f.blink = 0; }
    if (i === 0 && t > 23.6 && t < 26.2) { f.eyes = 'flat'; f.smile = -0.08; f.brow = 0.3; }
    if (i === 0 && t >= 26.2 && t < 28.7) { f.eyes = 'open'; f.smile = 0.05; f.brow = 0.2; f.browUp = 0.25; }
    if (t >= 28.7) { // the beam lands: blank, polite incomprehension
      f.eyes = 'open'; f.smile = -0.06; f.browUp = 0.25 + 0.35 * U.ease(t, 31.5, 34) + (i === 2 ? 0.2 : 0); f.open = i === 3 ? 0.12 : 0; f.sweat = 0.5;
      if (i === 1 && t > 34.6) f.eyes = 'wide';
    }
    return f;
  }
  function drawHiker(c, i, t) {
    const h = HIKERS[i];
    const w = walkAt(h, t);
    const tired = w.moving ? 1 : lerp(1, 0.8, U.ease(t, h.tStop, h.tStop + 2));
    const face = hikerFace(i, t, w, h);
    const shrugK = U.ease(t, 21.95, 22.25, 'outBack') * (1 - U.ease(t, 22.95, 23.4, 'inOutSine'));
    const lift = U.ease(t, 15.6 + i * 0.12, 16.9 + i * 0.12, 'inOutSine');
    const glance = i > 0 ? U.fade(t, 21.45 + i * 0.05, 21.95, 0.15, 0.15) : 0;
    const head = {
      tilt: -0.3 * lift - 0.16 * shrugK + (i === 0 ? Math.sin(t * 2.3) * 0.03 * Art.talkingAt(t, TALK, 'h1') : 0) + 0.05 * Math.sin(t * 0.8 + i),
      turn: 0.38 * shrugK + 0.35 * glance,
    };
    const warm = Math.max(0, 0.08 - Math.abs(w.x - FX) / 6000);
    const idle = w.moving ? 0 : 0.022 * Math.sin(t * 0.9 + i * 1.7) * U.ease(t, h.tStop, h.tStop + 1.5);
    const o = { x: w.x, y: w.y, s: S, look: lit(h.k, 0.22, warm), facing: -1, pose: 'walk', walk: w.ph, stride: w.st, tired, lean: idle, t, seed: SEED[h.k], face, head, shadow: false };
    // arms: the walk swing until they stop, then settle to standing, then the shrug
    if (!w.moving || h.tStop - t < 0.2) {
      const settle = U.ease(t, h.tStop - 0.15, h.tStop + 0.8, 'inOutSine');
      let A = mixA(walkArms(w.ph, w.st, tired), [STAND[0], STAND[1] + 0.06, STAND[2], STAND[3] + 0.04], settle);
      A = mixA(A, SHRUG, shrugK);
      if (i === 0) A = mixA(A, [0.42, 1.05, A[2], A[3]], U.fade(t, 24.0, 25.6, 0.35, 0.5) * 0.8); // a limp flap on "fine"
      o.armF = [A[0], A[1]]; o.armB = [A[2], A[3]];
      o.shrug = shrugK + (w.moving ? 0 : 0.12 * Math.max(0, Math.sin(t * 3.6 + i)) * (1 - U.ease(t, h.tStop, h.tStop + 3.5)));
    }
    if (h.k === 'h4') { // the dead phone
      const raise = U.fade(t, 9.0, 11.0, 0.45, 0.7);
      o.gesture = 'phoneLook';
      o.gw = lerp(0.42, 1, raise) * (1 - shrugK * 0.55);
      delete o.armF;
      const tap = U.bump(t, 9.62, 0.08) + U.bump(t, 9.95, 0.08);
      o.holdF = phone(U.fade(t, 9.66, 10.25, 0.04, 0.2));
      o.head.tilt += 0.16 * raise - 0.05 * tap;
      if (raise > 0.3 && t < 10.6) face.lookY = 0.6;
      if (t >= 10.25 && t < 10.9) { face.eyes = 'flat'; face.smile = -0.4; }
    }
    shadow(c, w.x, w.gy, 40 * h.S / S);
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
  function shadow(ctx, x, y, w, a = 0.3) {
    ctx.fillStyle = `rgba(14,10,24,${a})`;
    ctx.beginPath(); ctx.ellipse(x, y + 2, w, w * 0.17, 0, 0, TAU); ctx.fill();
  }
  // the dead phone (h4) — drawn at the hand, +x forward
  const phone = (flash) => (c) => {
    c.save();
    c.rotate(-0.32);
    c.fillStyle = '#20232c';
    Art.roundRect(c, -3, -33, 19, 34, 4); c.fill();
    c.fillStyle = '#06070b';
    Art.roundRect(c, -0.8, -30.5, 14.6, 27.5, 2.6); c.fill();
    if (flash > 0.01) { // empty-battery glyph blinks once, then nothing
      c.globalAlpha *= flash;
      c.strokeStyle = '#d9dde6'; c.lineWidth = 1.4;
      c.strokeRect(1.8, -20, 8.6, 5.2);
      c.fillStyle = '#d9dde6'; c.fillRect(10.4, -18.4, 1.4, 2);
      c.fillStyle = '#ff4a3d'; c.fillRect(2.6, -19.2, 1.6, 3.6);
    }
    c.globalAlpha = 1;
    c.strokeStyle = 'rgba(255,255,255,0.12)'; c.lineWidth = 1.2;
    c.beginPath(); c.moveTo(1.5, -28); c.lineTo(11, -19); c.stroke();
    c.restore();
  };

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
  // Above the speaker and out in front of the face: the tail drops in front of
  // the face to the mouth, never across it, and the box clears every head.
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

  Film.scene({
    id: 'return',
    order: 7,
    title: 'The Return',
    duration: D,
    mood: 'dusk',
    sfx: [
      [0.3, 'wind', { gain: 0.25 }],
      [3.0, 'footsteps', { gain: 0.28 }],
      [7.0, 'footsteps', { gain: 0.45 }],
      [9.62, 'tap', { gain: 0.35 }],
      [9.95, 'tap', { gain: 0.3 }],
      [10.35, 'sigh', { gain: 0.45 }],
      [11.2, 'footsteps', { gain: 0.4 }],
      [13.4, 'sigh', { gain: 0.32 }],
      [15.0, 'step', { gain: 0.35 }],
      [22.1, 'pop', { gain: 0.3 }],
      [23.0, 'sigh', { gain: 0.4 }],
      [28.85, 'sparkle', { gain: 0.6 }],
      [29.05, 'shimmer', { gain: 0.35 }],
      [33.6, 'chime', { gain: 0.3 }],
    ],
    fadeIn: 1.2,
    fadeOut: 0,
    post: { vignette: 0.42, grain: 0.05, letterbox: 1 },

    render(ctx, t) {
      const cam = camAt(t);

      // ---- sky and the layered backdrop (soft focus in the closer shots)
      drawSky(ctx, cam, t);
      if (cam.id === 'A') drawLayers(ctx, cam, t, false);
      else if (cam.id === 'B') drawLayers(ctx, cam, t, true);
      else { drawLayers(ctx, cam, t, true, 'clouds'); drawPlate(ctx, cam); }
      ctx.save(); applyCam(ctx, cam, 0.09); // the summit's promise-glow breathes
      Art.glow(ctx, 1569, 222, 110, P.light, 0.12 + 0.06 * Math.sin(t * 1.4));
      ctx.restore();
      ctx.save(); applyCam(ctx, cam, 0.62);   // fireflies back among the trees
      Art.motes(ctx, { seed: 51, count: 12, x0: 0, x1: 2600, y0: 560, y1: 840, t, color: '#ffe9a6', size: 1.5, drift: 4, wander: 50, glow: 0.9, blink: 1, alpha: 0.7 * U.ease(t, 2, 12) });
      ctx.restore();
      drawGround(ctx, cam, t);

      // ---- the action plane
      const beam = U.ease(t, 28.75, 29.4, 'outCubic');
      const flowerGlow = 0.85 + 0.12 * Math.sin(t * 1.3) + 0.35 * beam;
      ctx.save();
      applyCam(ctx, cam, 1);
      if (beam > 0) Art.glow(ctx, ME_SX + 4, MEY - 150, 210, '#ffd38a', 0.24 * beam);
      shadow(ctx, meX(t), MEY, 40);
      const A = {};
      for (let i = HIKERS.length - 1; i >= 0; i--) A[HIKERS[i].k] = drawHiker(ctx, i, t);
      A.me = drawMe(ctx, t);
      clump(ctx, t);
      mossRock(ctx, FX + 64, gy(FX + 64) + 48, 104, 64);
      drawFlower(ctx, t, flowerGlow);
      ctx.restore();
      verge(ctx, cam, t);
      drawNearGrass(ctx, cam, t);

      // sparkles around him when he beams
      if (beam > 0) {
        ctx.save(); applyCam(ctx, cam, 1);
        const hd = A.me.head;
        for (let i = 0; i < 9; i++) {
          const per = 1.6 + U.hash(i, 5) * 1.2;
          const ph = U.fract((t - 28.75) / per + U.hash(i, 6));
          const life = Math.sin(ph * Math.PI);
          let ang = -2.8 + U.hash(i, 7) * 3.1;
          if (Math.abs(ang + 1.62) < 0.34) ang += ang < -1.62 ? -0.34 : 0.34;   // keep clear of the pompom
          const rr = hd.r * (1.6 + U.hash(i, 8) * 0.9) + ph * 10;
          sparkle(ctx, hd.x + Math.cos(ang) * rr, hd.y + Math.sin(ang) * rr * 0.9, (4 + U.hash(i, 9) * 6) * life, life * beam, t * 0.6 + i, '#ffe7a8');
        }
        ctx.restore();
      }

      // fireflies near the spot
      ctx.save(); applyCam(ctx, cam, 1);
      Art.motes(ctx, { seed: 52, count: 12, x0: 300, x1: 2300, y0: 600, y1: 900, t, color: '#fff0a8', size: 2.0, drift: 3, wander: 46, glow: 1, blink: 1, alpha: 0.85 * U.ease(t, 4, 16) });
      Art.motes(ctx, { seed: 53, count: 7, x0: 560, x1: 1100, y0: 640, y1: 900, t, color: '#fff3b8', size: 2.2, drift: 2, wander: 38, glow: 1, blink: 1, alpha: 0.9 * U.ease(t, 18, 30) });
      ctx.restore();

      // ---- out-of-focus foreground framing (wide + tracking only)
      if (cam.id === 'A' || cam.id === 'B') drawFG(ctx, cam);

      // ---- dialogue (screen space)
      const sp = (k) => {
        const a = A[k];
        const hs = toScreen(cam, a.head);
        return { f: k === 'me' ? 1 : -1, head: hs, r: a.head.r * cam.z, mouth: toScreen(cam, a.mouth), top: toScreen(cam, a.top) };
      };
      const heads = Object.keys(A).map((k) => { const hs = toScreen(cam, A[k].head); return { x: hs.x, y: hs.y, r: A[k].head.r * cam.z * 1.25 }; });
      const cues = [];
      for (const q of TALK) {
        if (t < q[0] - 0.05 || t > q[1] + 0.05) continue;
        const who = q[3].who;
        cues.push([q[0], q[1], q[2], Object.assign({ who }, place(ctx, q[2], sp(who), heads, who === 'me' ? 600 : 520))]);
      }
      for (const q of cues) balloon(ctx, t, q[0], q[1], q[2], q[3]);
      Art.captions(ctx, t, NARR);
    },
  });
})();
