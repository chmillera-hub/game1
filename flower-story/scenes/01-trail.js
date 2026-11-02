/* ==========================================================================
   01 · The Trail — morning. The camera cranes down out of a bright sky,
   past out-of-focus foreground pines, onto a forest trail and tracks five
   hikers walking right, toward the far glowing summit. They talk about the
   summit; the one at the back ("me") is busy with everything else: the
   trees, a flock overhead, a falling leaf, the air itself. The camera drifts
   in on him. Called back into line, he hurries to catch up… and glances
   aside. The last frame is scene 02's first frame (same layout, walk phases,
   background stack, palette and camera), so the 0.8 s dissolve into 02
   plays as one continuous shot.
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU } = U;
  const D = 32.5;
  const PIC = Art.PIC;

  /* ---------------- shared trail layout (scenes 01–03) ---------------- */
  const GY = 870, GAMP = 16;              // ground line: Art.groundY(x, {y: 870, amp: 16, offset: worldX})
  const FOOT = 18;                        // feet stand this far below the ground line, on the trail
  const S = 0.8;                          // character scale in the wide walking shot
  const RATE = 6.0;                       // walk phase rate (rad/s) for a height-1.0 character
  const KF = 72.32 * Math.sin(0.42);      // foot travel per radian of phase per unit scale (kit leg rig)
  const V0 = KF * RATE * S;               // ≈141.6 px/s: the skate-free tracking speed at the trail plane
  const gOpt = (off) => ({ y: GY, amp: GAMP, offset: off });

  // Scene 02 opens on exactly this layout: screen x and walk phase of each hiker at its t = 0.
  const CREW = [
    { k: 'h1', x: 1250, ph: 0.4, seed: 17 },
    { k: 'h2', x: 1080, ph: 2.3, seed: 53 },
    { k: 'h3', x: 910, ph: 4.1, seed: 89 },
    { k: 'h4', x: 740, ph: 5.6, seed: 131 },
  ];
  const ME_X = 540;
  const ME_PH0 = (((Math.PI / 2 - RATE * (6.3 + 0.5 * (12.3 - 6.3))) % Math.PI) + Math.PI) % Math.PI; // 02's start phase

  /* ---------------- planted feet ---------------- */
  // The kit swings the legs sinusoidally, so a body moving at constant speed lets the planted foot
  // slide ±8 px every step. Adding this residual to the body's x pins the stance foot exactly
  // (the body surges a little through each step, as real walkers do).
  const R0 = 58 * Math.sin(0.42) + 56 * Math.sin(0.3);
  const stanceDisp = (u) => { const a = 0.42 * Math.cos(u); return R0 - (58 * Math.sin(a) + 56 * Math.sin(a - 0.12)); };
  const SWEEP = stanceDisp(Math.PI);      // ≈92.6 units: how far the stance foot travels per step
  const R_MEAN = (() => { let s = 0; const n = 256; for (let i = 0; i < n; i++) { const u = ((i + 0.5) / n) * Math.PI; s += stanceDisp(u) - KF * u; } return s / n; })();
  const plantR = (ph) => { let u = (ph + Math.PI / 2) % Math.PI; if (u < 0) u += Math.PI; return stanceDisp(u) - KF * u - R_MEAN; };

  /* ---------------- camera ---------------- */
  // Layer p (1 = trail plane) scrolls by camX·p, is shifted down by A·p + B (A = crane height,
  // B = tilt), floats with 02's handheld drift ·p, and is magnified by a dolly 1/(1 − cz·p) about F.
  // With A = −B the trail plane stays pinned while the far world rides a little higher; the final
  // move lowers it back (the horizon sinks) and trucks right onto 02's exact opening framing.
  const T_LAND0 = 0.2, T_LAND1 = 6.8;     // crane down out of the sky
  const T_END0 = 27.4;                    // final move: ease lower/right onto 02's opening frame
  const TRUCK = 36;                       // the camera trails the group by this much until the final move
  const LIFT = 26;                        // crane height held through the middle of the scene
  const OPEN_A = 420, OPEN_B = 60;        // opening: high above the trail, tilted up toward the sun
  const F = { x: ME_X + TRUCK + 20, y: 700 };   // the push-in drifts toward the narrator
  function camAt(t) {
    const kO = U.ease(t, T_LAND0, T_LAND1, 'inOutCubic');
    const kE = U.ease(t, T_END0, D, 'inOutSine');
    const zT = 1 + 0.15 * U.ease(t, 16.2, 21.8, 'inOutSine') * (1 - U.ease(t, 25.6, 29.2, 'inOutSine'));
    return {
      camX: V0 * (t - D) - TRUCK * (1 - kE),
      A: U.lerp(OPEN_A, LIFT, kO) * (1 - kE),
      B: U.lerp(OPEN_B, -LIFT, kO) * (1 - kE),
      cz: 1 - 1 / zT,
      sh: Art.shake((t - D) * 0.7, 0.45, 23),   // 02's handheld float, continuous across the cut
      kO, kE,
    };
  }
  const layerT = (cam, p) => ({ x: -cam.sh.x * p, y: cam.A * p + cam.B - cam.sh.y * p, z: 1 / (1 - cam.cz * p) });
  function layer(ctx, cam, p, fn) {
    const o = layerT(cam, p);
    ctx.save();
    if (o.z !== 1) { ctx.translate(F.x, F.y); ctx.scale(o.z, o.z); ctx.translate(-F.x, -F.y); }
    ctx.translate(o.x, o.y);
    fn(ctx, cam.camX * p);
    ctx.restore();
  }
  const toScreen = (cam, p, q) => { const o = layerT(cam, p); return { x: F.x + o.z * (q.x + o.x - F.x), y: F.y + o.z * (q.y + o.y - F.y) }; };
  const toLayer = (cam, p, q) => { const o = layerT(cam, p); return { x: (q.x - F.x) / o.z + F.x - o.x, y: (q.y - F.y) / o.z + F.y - o.y }; };
  // morning, drifting toward 02's late-morning mix (0.2) by the cut
  const palAt = (t) => U.mixDeep(Art.TOD.morning, Art.TOD.golden, t <= D ? 0.2 * U.ease(t, 3, D, 'inOutSine') : 0.2 + 0.1 * U.clamp((t - D) / 26));

  /* ---------------- beats (local seconds) ---------------- */
  const CAPS = [
    [1.2, 5.9, 'I imagine that I’m on a hike with a group of people.'],
    [16.3, 22.7, 'Everyone’s talking about how the trail is supposed to lead to this incredible view at the summit—'],
    [23.0, 26.1, 'a place where they’ll finally feel something meaningful.'],
    [29.2, 32.2, 'I’m walking with them, but halfway through…'],
  ];
  // background chatter (invented, in spirit). dx/y: bubble centre relative to the speaker's head / screen y
  const BUBS = [
    [6.5, 8.7, 'Summit or bust!', { who: 'h1', dx: -170, y: 500 }],
    [9.2, 12.9, 'The view up there is supposed to be unreal.', { who: 'h3', dx: -20, y: 486 }],
    [13.3, 15.8, 'That’s where it finally means something.', { who: 'h2', dx: 50, y: 492 }],
    [26.6, 28.8, 'Keep the pace, people!', { who: 'h1', dx: -120, y: 500 }],
  ];
  // me drifts behind while he watches the world, then hurries back into line when called
  const lagAt = (t) => (20 * U.ease(t, 18.6, 21.6) + 38 * U.ease(t, 22.8, 26.4)) * (1 - U.ease(t, 27.25, 29.6, 'inOutSine'));
  // a leaf that only he notices
  const LEAF = { t0: 16.6, tl: 20.1, x0: 1040, y0: 372, wind: 42, per: 1.75 };

  /* ---------------- small helpers ---------------- */
  // Cheap depth of field / volumetric glow: draw into a small canvas at 1/f resolution that covers only
  // `region` (screen coords), soften it with a 4-tap box, then upscale bilinearly. (Art.blurred renders the
  // whole frame and upscales with 'high' quality — ~20 ms a pass in software; this costs a fraction.)
  function soft(ctx, f, drawFn, key, region, mode) {
    const r = region;
    const cw = Math.ceil(r.w / f) + 2, ch = Math.ceil(r.h / f) + 2;
    const c = Art.canvas('a1:' + key, cw, ch), x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1;
    x.clearRect(0, 0, cw, ch);
    const base = Art._base || new DOMMatrix();
    x.setTransform(new DOMMatrix().scale(1 / f, 1 / f).translate(f - r.x, f - r.y).multiply(base.inverse().multiply(ctx.getTransform())));
    drawFn(x);
    const c2 = Art.canvas('a1:' + key + ':b', cw, ch), x2 = c2.getContext('2d');
    x2.setTransform(1, 0, 0, 1, 0, 0);
    x2.globalAlpha = 1; x2.globalCompositeOperation = 'source-over';
    x2.clearRect(0, 0, cw, ch);
    x2.globalCompositeOperation = 'lighter'; x2.globalAlpha = 0.25;          // 4-tap box: no blocky upscale
    x2.drawImage(c, -0.6, -0.6); x2.drawImage(c, 0.6, -0.6); x2.drawImage(c, -0.6, 0.6); x2.drawImage(c, 0.6, 0.6);
    x2.globalCompositeOperation = 'source-over'; x2.globalAlpha = 1;
    ctx.save();
    ctx.setTransform(base);
    if (mode) ctx.globalCompositeOperation = mode;
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(c2, r.x - f, r.y - f, cw * f, ch * f);
    ctx.restore();
  }

  const mixA = (a, b, k) => [U.lerp(a[0], b[0], k), U.lerp(a[1], b[1], k)];
  const lerpP = (a, b, k) => ({ x: U.lerp(a.x, b.x, k), y: U.lerp(a.y, b.y, k) });
  // the kit's walking arm swing, so gestures can blend out of it
  function walkArms(ph) {
    const sw = Math.sin(ph) * 0.5;
    return { F: [-sw * 0.9 + 0.04, 0.25 + Math.max(0, -sw) * 0.6], B: [sw * 0.9 - 0.04, 0.25 + Math.max(0, sw) * 0.6] };
  }
  // body-local shoulder positions in the walk pose (replicates Art.person's torso math), so IK targets
  // can be turned into arm angles and blended with the walk swing
  function shoulders(ph, lean0, seed, t, bob, shrug) {
    const hipY = -(58 + 56 + 4) + Math.abs(Math.sin(ph)) * 5 - 3 + (bob || 0);
    const lean = lean0 + 0.06, topLen = 88 + Math.sin(t * 1.7 + seed) * 1.3 * 0.3;
    const shX = Math.sin(lean) * topLen, sy = hipY - Math.cos(lean) * topLen + 7 - (shrug || 0) * 8;
    return { F: { x: shX + 3, y: sy }, B: { x: shX - 6, y: sy + 1 } };
  }
  // look at a screen point from an eye: the side-view head tilts (and turns a little toward camera to
  // look back); the eyes do the rest
  function gaze(eye, p) {
    const dx = p.x - eye.x, dy = p.y - eye.y;
    const back = U.smooth(U.remap(dx, 30, -140, 0, 1));
    const ang = Math.atan2(dy, Math.abs(dx) + 1e-3);
    return {
      tilt: U.clamp(ang * U.lerp(0.45, 0.32, back), -0.38, 0.3),
      turn: 0.3 * back,
      lookX: U.lerp(Math.cos(ang) * 1.1, -0.95, back),
      lookY: U.clamp(Math.sin(ang) * 1.25, -1.1, 1.1),
    };
  }
  function blendLook(base, g, k) {
    if (k <= 0) return;
    base.head.tilt = U.lerp(base.head.tilt, g.tilt, k);
    base.head.turn = U.lerp(base.head.turn || 0, g.turn || 0, k);
    base.face.lookX = U.lerp(base.face.lookX, g.lookX, k);
    base.face.lookY = U.lerp(base.face.lookY, g.lookY, k);
  }
  // h4's phone (the same prop as in 02/03)
  const phone = (c) => {
    c.save();
    c.rotate(-0.15);
    c.fillStyle = '#23262e';
    Art.roundRect(c, -3, -24, 7, 26, 2.5); c.fill();
    c.fillStyle = '#9fd8ff';
    c.fillRect(-3.4, -22, 1.6, 22);
    c.restore();
  };
  // distant bird: a soft flapping 'm'
  function farBird(ctx, x, y, s, flap, color) {
    const a = Math.sin(flap) * 0.55 + 0.25;
    ctx.save();
    ctx.translate(x, y);
    ctx.strokeStyle = color; ctx.lineWidth = 2.2 * s; ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(-9 * s, -Math.sin(a) * 7 * s);
    ctx.quadraticCurveTo(-4 * s, -Math.sin(a) * 9 * s - 2 * s, 0, 0);
    ctx.quadraticCurveTo(4 * s, -Math.sin(a) * 9 * s - 2 * s, 9 * s, -Math.sin(a) * 7 * s);
    ctx.stroke();
    ctx.restore();
  }
  // two flocks: one crossing the opening sky, one the narrator follows with his eyes
  const FLOCKS = [
    { t0: 0.5, t1: 7.6, x0: 1660, x1: 180, y: 392, n: 5, s: 0.95, seed: 3 },
    { t0: 10.4, t1: 15.9, x0: 1760, x1: 120, y: 248, n: 3, s: 1.15, seed: 9 },
  ];
  function birdPos(Fl, i, t) {
    const k = (t - Fl.t0 - i * 0.16) / (Fl.t1 - Fl.t0);
    return {
      x: U.lerp(Fl.x0, Fl.x1, k) + (i % 2 ? 26 : -8) * i * 0.6,
      y: Fl.y + (i % 2 ? -1 : 1) * i * 13 + Math.sin(t * 1.3 + i * 2) * 6 + U.noise1(t * 0.8 + i * 3, Fl.seed) * 8,
      k,
    };
  }
  function drawFlocks(ctx, t, color) {
    for (const Fl of FLOCKS) {
      if (t < Fl.t0 - 0.1 || t > Fl.t1 + 1.2) continue;
      for (let i = 0; i < Fl.n; i++) {
        const b = birdPos(Fl, i, t);
        if (b.k < 0 || b.k > 1) continue;
        const glide = U.smooth(U.remap(Math.sin(t * 0.9 + i * 1.7), 0.35, 0.8, 0, 1));
        const flap = U.lerp(t * 11 + i * 1.9, 0.9, glide);
        farBird(ctx, b.x, b.y, Fl.s * (1 - i * 0.06), flap, color);
      }
    }
  }
  // h1's trekking poles: each tip is planted for one step (moving with the stance foot, so it stays put
  // on the ground) while the hand rides along, then swings forward. Body-local units.
  const POLE = { TX0: 40, HX0: 25, HY: -118, CARRY: 0.6, LIFT: 8 };
  const POLE_L = Math.hypot(POLE.TX0 - POLE.HX0, POLE.HY);
  function poleState(ph) {
    let u = (ph + Math.PI / 2) % TAU; if (u < 0) u += TAU;
    if (u <= Math.PI) {
      const d = stanceDisp(u);
      return { hand: { x: POLE.HX0 - POLE.CARRY * d, y: POLE.HY }, tip: { x: POLE.TX0 - d, y: 0 } };
    }
    const q = (u - Math.PI) / Math.PI, k = U.smooth(q);
    const hand = { x: POLE.HX0 - POLE.CARRY * SWEEP * (1 - k), y: POLE.HY - POLE.LIFT * Math.sin(q * Math.PI) };
    const th0 = Math.atan2(POLE.TX0 - SWEEP - (POLE.HX0 - POLE.CARRY * SWEEP), -POLE.HY);
    const th1 = Math.atan2(POLE.TX0 - POLE.HX0, -POLE.HY);
    const th = U.lerp(th0, th1, k);
    return { hand, tip: { x: hand.x + Math.sin(th) * POLE_L, y: hand.y + Math.cos(th) * POLE_L } };
  }
  // draws a pole at the hand (as Art.person's holdF/holdB). bodyInv maps the canvas back to body-local
  // units, so the planted tip lands exactly on the ground; thPoint (weighted by gw) swings it up.
  function poleDrawer(bodyInv, ps, gw, thPoint, handCol, handR) {
    return (c) => {
      const r = bodyInv.multiply(c.getTransform());
      let tx = ps.tip.x - r.e, ty = ps.tip.y - r.f;
      if (gw > 0.001) {
        const L = Math.hypot(tx, ty), th = U.lerp(Math.atan2(tx, ty), thPoint, U.clamp(gw));
        tx = Math.sin(th) * L; ty = Math.cos(th) * L;
      }
      const L = Math.hypot(tx, ty) || 1, ux = tx / L, uy = ty / L;
      c.lineCap = 'round';
      c.strokeStyle = '#6f7680'; c.lineWidth = 4.4;                          // shaft (outlined, so it reads on sky)
      c.beginPath(); c.moveTo(-ux * 15, -uy * 15); c.lineTo(tx, ty); c.stroke();
      c.strokeStyle = '#d3d7dd'; c.lineWidth = 2.4;
      c.beginPath(); c.moveTo(-ux * 15, -uy * 15); c.lineTo(tx - ux * 1.5, ty - uy * 1.5); c.stroke();
      c.strokeStyle = '#272b35'; c.lineWidth = 5.4;                          // grip
      c.beginPath(); c.moveTo(-ux * 16, -uy * 16); c.lineTo(ux * 5, uy * 5); c.stroke();
      c.strokeStyle = '#3a3f4b'; c.lineWidth = 2.2;                          // basket
      const bx = tx - ux * 13, by = ty - uy * 13;
      c.beginPath(); c.moveTo(bx - uy * 6, by + ux * 6); c.lineTo(bx + uy * 6, by - ux * 6); c.stroke();
      c.fillStyle = handCol;                                                // the hand closes over the grip
      c.beginPath(); c.arc(0, 0, handR, 0, TAU); c.fill();
    };
  }
  // a big foreground pine, backlit (drawn inside the depth-of-field pass, layer-local coords; x = trunk
  // centre). Very tall so the crane never reveals its ends.
  function fgPine(c, x, w, P, seed) {
    const bark = '#1e1b19', rim = U.mix(bark, P.light, 0.45);
    const top = -1700, bot = 1600, n = 40;
    const edge = (side, i) => {
      const y = U.lerp(top, bot, i / n);
      return { x: x + side * (w / 2) * (0.85 + 0.3 * (i / n)) + U.noise1(i * 0.7, seed + (side > 0 ? 1 : 2)) * w * 0.06, y };
    };
    const band = (a, b) => {
      c.beginPath();
      for (let i = 0; i <= n; i++) { const p = edge(1, i); const q = { x: U.lerp(edge(-1, i).x, p.x, a), y: p.y }; i ? c.lineTo(q.x, q.y) : c.moveTo(q.x, q.y); }
      for (let i = n; i >= 0; i--) { const p = edge(1, i); c.lineTo(U.lerp(edge(-1, i).x, p.x, b), p.y); }
      c.closePath(); c.fill();
    };
    c.fillStyle = bark; band(0, 1);
    c.fillStyle = rim; band(0.86, 1);                        // the sun catches its right edge
    c.strokeStyle = bark; c.lineCap = 'round';               // broken-off lower branches
    for (let b = 0; b < 4; b++) {
      const by = -620 + b * 380 + U.hash(b, seed + 5) * 120, side = (b + seed) % 2 ? 1 : -1;
      const len = w * (0.9 + U.hash(b, seed + 6) * 0.9);
      c.lineWidth = w * 0.16;
      c.beginPath(); c.moveTo(x, by); c.lineTo(x + side * len, by - len * 0.32); c.stroke();
    }
  }
  // a tall pine standing at the trail's back edge (p≈0.9): a bare trunk rising out of frame (its crown is
  // far above). Drawn sharp — it's nearly at the hikers' depth, behind them.
  function edgePine(c, x, base, P, seed, w) {
    const bark = U.mix('#3b3029', P.trees[2], 0.3), lit = U.mix(bark, P.light, 0.32);
    const top = -500;
    // morning haze: the trunk fades toward the fog as it rises into the light
    const gr = c.createLinearGradient(0, base, 0, 160);
    gr.addColorStop(0, bark); gr.addColorStop(0.55, U.mix(bark, P.fog, 0.1)); gr.addColorStop(1, U.mix(bark, P.fog, 0.3));
    c.fillStyle = gr;
    c.beginPath();
    c.moveTo(x - w * 0.78, base + 4); c.quadraticCurveTo(x - w * 0.5, base - 18, x - w * 0.46, base - 60);
    c.lineTo(x - w * 0.36, top); c.lineTo(x + w * 0.36, top); c.lineTo(x + w * 0.46, base - 60);
    c.quadraticCurveTo(x + w * 0.5, base - 18, x + w * 0.8, base + 4); c.closePath(); c.fill();
    c.fillStyle = lit;                                       // the sun side
    c.beginPath(); c.moveTo(x + w * 0.2, top); c.lineTo(x + w * 0.36, top); c.lineTo(x + w * 0.46, base - 60); c.lineTo(x + w * 0.27, base - 60); c.closePath(); c.fill();
    c.fillStyle = U.mix(P.grass, P.trees[2], 0.45);          // moss creeping up the shady side of the root flare
    c.beginPath();
    c.moveTo(x - w * 0.78, base + 4); c.quadraticCurveTo(x - w * 0.52, base - 16, x - w * 0.47, base - 58);
    c.quadraticCurveTo(x - w * 0.3, base - 96 - U.hash(seed, 8) * 40, x - w * 0.12, base - 40); c.quadraticCurveTo(x - w * 0.2, base - 8, x - w * 0.1, base + 4);
    c.closePath(); c.fill();
    c.strokeStyle = U.shade(bark, -0.25); c.lineWidth = 2;   // bark fissures
    for (let i = 0; i < 4; i++) {
      const fx = x - w * 0.25 + U.hash(i, seed) * w * 0.4;
      c.beginPath(); c.moveTo(fx, base - 30 - U.hash(i, seed + 1) * 60); c.lineTo(fx + 2, top); c.stroke();
    }
    c.strokeStyle = U.mix(bark, P.fog, 0.12); c.lineWidth = 5; c.lineCap = 'round';   // a dead branch stub
    const sy = base - 330 - U.hash(seed, 3) * 120;
    c.beginPath(); c.moveTo(x - w * 0.3, sy); c.lineTo(x - w * 1.4, sy - 34); c.stroke();
  }
  // the leaf: a world-space path through the air, then at rest on the trail
  function leafAt(t, cam) {
    const T = Math.min(t, LEAF.tl) - LEAF.t0;
    const camAtT0 = V0 * (LEAF.t0 - D) - TRUCK;            // (the final move hasn't begun yet)
    const wx0 = LEAF.x0 + camAtT0;
    const settle = U.ease(t, LEAF.tl - 0.7, LEAF.tl);
    const sw = Math.sin((T / LEAF.per) * TAU);
    const wx = wx0 + LEAF.wind * T + 24 * sw * (1 - settle);
    const landX = wx0 + LEAF.wind * (LEAF.tl - LEAF.t0) - (V0 * (LEAF.tl - D) - TRUCK);
    const yLand = Art.groundY(landX, gOpt(V0 * (LEAF.tl - D) - TRUCK)) + 31;
    const fall = U.prog(t, LEAF.t0, LEAF.tl);
    const y = U.lerp(LEAF.y0, yLand, fall * (0.82 + 0.18 * fall)) - 7 * sw * sw * (1 - settle);
    return {
      x: wx - cam.camX, y, landed: t >= LEAF.tl,
      rot: 0.55 * Math.cos((T / LEAF.per) * TAU) * (1 - settle) + 0.12 * settle,
      flip: U.lerp(0.3 + 0.7 * Math.abs(Math.cos(t * 2.4)), 0.42, settle),
    };
  }
  function drawLeaf(ctx, L, P) {
    const col = '#e8b440';
    ctx.save();
    ctx.translate(L.x, L.y);
    ctx.rotate(L.rot);
    ctx.scale(1.5, 1.5 * L.flip);
    ctx.fillStyle = L.landed ? U.mix(col, P.trail, 0.25) : U.mix(col, '#fff3c4', 0.35 * (1 - L.flip));
    ctx.beginPath(); ctx.moveTo(-9, 0); ctx.quadraticCurveTo(0, -6.5, 9, 0); ctx.quadraticCurveTo(0, 6.5, -9, 0); ctx.fill();
    ctx.strokeStyle = U.shade(col, -0.3); ctx.lineWidth = 0.9;
    ctx.beginPath(); ctx.moveTo(-8, 0); ctx.lineTo(12, 0.5); ctx.stroke();
    ctx.restore();
    // it flashes as it turns its face to the sun
    if (!L.landed && L.flip > 0.85) Art.glow(ctx, L.x, L.y, 26, P.light, (L.flip - 0.85) * 3.2);
  }
  // soft god-ray shafts falling through the canopy from the sun (upper right), drawn into the blur pass
  function drawShafts(c, cam, t, P, a) {
    layer(c, cam, 0.62, (c2, off) => {
      const sp = 330, i0 = Math.floor((off - 900) / sp), i1 = Math.ceil((off + W + 500) / sp);
      for (let i = i0; i <= i1; i++) {
        if (U.hash(i, 151) < 0.4) continue;
        const xt = i * sp + U.hash(i, 152) * 200 - off + 260;
        const yt = 60, yb = 990, xb = xt - (yb - yt) * 0.46;
        const w0 = 16 + U.hash(i, 153) * 34, w1 = w0 * 2.3;
        const fl = a * (0.55 + 0.45 * Math.sin(t * (0.35 + U.hash(i, 154) * 0.5) + i * 1.9)) * (0.55 + 0.45 * U.hash(i, 155));
        const gr = c2.createLinearGradient(0, yt, 0, yb);
        gr.addColorStop(0, U.rgba(P.light, 0));
        gr.addColorStop(0.35, U.rgba(P.light, fl));
        gr.addColorStop(0.8, U.rgba(P.light, fl * 0.75));
        gr.addColorStop(1, U.rgba(P.light, 0));
        c2.fillStyle = gr;
        c2.beginPath(); c2.moveTo(xt - w0, yt); c2.lineTo(xt + w0, yt); c2.lineTo(xb + w1, yb); c2.lineTo(xb - w1, yb); c2.closePath(); c2.fill();
      }
    });
  }
  // Elements placed by the time they cross screen centre: world x = W/2 + camX(t)·p.
  const placeAt = (tc, p) => W / 2 + (V0 * (tc - D) - TRUCK) * p;
  // foreground undergrowth banks (p > 1, out of focus): [crossing time, parallax, scale, seed]
  // — the last one is gone before the cut
  const FERNS = [[2.6, 1.42, 1.9, 1], [8.0, 1.38, 1.7, 2], [12.6, 1.5, 2.0, 3], [17.4, 1.4, 1.8, 4], [22.4, 1.46, 1.9, 5], [26.6, 1.4, 1.75, 6]]
    .map(([tc, p, s, seed]) => ({ p, s, seed, wx: placeAt(tc, p) }));
  // one big backlit pine sweeps past the lens during the crane (gone before the group is revealed)
  const TRUNKS = [[2.3, 2.0, 128, 21]].map(([tc, p, w, seed]) => ({ p, w, seed, wx: placeAt(tc, p) }));
  // a tall pine at the trail's back edge, passing behind the group — behind him while the leaf falls,
  // never behind a speaker, gone long before the cut
  const EDGE = [[18.2, 0.88, 74, 37]].map(([tc, p, w, seed]) => ({ p, w, seed, wx: placeAt(tc, p) }));

  /* ---------------- scene ---------------- */
  Film.scene({
    id: 'trail',
    order: 1,
    title: 'The Trail',
    chapter: 'Part One · The Hike',
    duration: D,
    mood: 'forest',
    sfx: [
      [0.5, 'bird', { gain: 0.35 }],
      [2.6, 'footsteps', { gain: 0.3 }],
      [3.6, 'bird', { gain: 0.22 }],
      [10.8, 'bird', { gain: 0.3 }],
      [16.9, 'petal', { gain: 0.2 }],
      [23.2, 'breath', { gain: 0.45 }],
      [27.35, 'footsteps', { gain: 0.4 }],
      [30.6, 'shimmer', { gain: 0.15 }],
    ],
    crossIn: 1.5,
    fadeIn: 0,
    fadeOut: 0,
    post: { vignette: 0.32, grain: 0.045, letterbox: 1 },

    render(ctx, t) {
      const P = palAt(t);
      const cam = camAt(t);
      const tc = t - D;                       // shared clock with 02 (wind, blinks, breathing)
      const wa = tc;
      const kCorr = 1 - U.ease(t, D - 1.7, D - 0.15);   // planted-foot correction, faded for the hand-off
      const tilted = U.clamp(cam.B / OPEN_B);           // 1 while the camera looks up at the sun

      /* ---------- sky & far world (02's layer stack) ---------- */
      layer(ctx, cam, 0, (c) => {
        Art.sky(c, P, { horizon: 720 });
        if (tilted > 0.01) Art.sun(c, 1760, 90, 30, P.sun, 0.8 * tilted);
        Art.glow(c, 1760, 90, 470, P.sun, 0.32);
      });
      layer(ctx, cam, 0.02, (c, off) => Art.clouds(c, { seed: 2, count: 4, y0: 190, y1: 330, offset: off + wa * 5, color: '#ffffff', alpha: 0.55 }));
      layer(ctx, cam, 0.04, (c, off) => Art.ridge(c, { seed: 21, y: 615, amp: 150, color: U.mix(P.far, P.sky[1], 0.4), offset: off }));
      layer(ctx, cam, 0.03, (c, off) => Art.summit(c, { x: 1610 - off, y: 655, h: 440, w: 700, P, glow: 0.55, t: wa }));
      const sumTip = toScreen(cam, 0.03, { x: 1610 - cam.camX * 0.03 + 700 * 0.03, y: 655 - 440 });
      layer(ctx, cam, 0.05, (c) => Art.fog(c, { y: 650, h: 170, color: P.fog, alpha: 0.5 }));
      layer(ctx, cam, 0.08, (c) => drawFlocks(c, t, U.shade(P.mid, -0.42)));
      layer(ctx, cam, 0.09, (c, off) => Art.ridge(c, { seed: 8, y: 718, amp: 100, color: P.mid, offset: off }));
      layer(ctx, cam, 0.18, (c, off) => {
        Art.forest(c, { seed: 31, y: 770, offset: off, spacing: 64, hMin: 110, hMax: 190, color: P.trees[0], light: U.shade(P.trees[0], 0.1), kind: 'mix' });
        Art.fog(c, { y: 772, h: 120, color: P.fog, alpha: 0.32 });
      });
      layer(ctx, cam, 0.34, (c, off) => {
        Art.forest(c, { seed: 32, y: 828, offset: off, spacing: 84, hMin: 200, hMax: 300, color: P.trees[1], light: U.shade(P.trees[1], 0.12), kind: 'pine', sway: 4, t: wa });
        // morning mist between the bands, burning off as the sun climbs
        Art.fog(c, { y: 846, h: 150, color: P.fog, alpha: 0.34 * (1 - U.ease(t, 5, 26)) });
      });
      layer(ctx, cam, 0.55, (c, off) => {
        Art.forest(c, { seed: 33, y: 874, offset: off, spacing: 230, hMin: 400, hMax: 520, color: U.mix(P.trees[2], P.trees[1], 0.3), light: U.shade(P.trees[1], 0.04), kind: 'pine', sway: 3, t: wa, jitterY: 8 });
      });
      for (const e of EDGE) {
        const sx = toScreen(cam, e.p, { x: e.wx - cam.camX * e.p, y: 0 }).x;
        if (sx < -260 || sx > W + 260) continue;
        layer(ctx, cam, e.p, (c, offp) => edgePine(c, e.wx - offp, 874, P, e.seed, e.w));
      }

      /* ---------- trail plane ---------- */
      const off = cam.camX;
      const go = gOpt(off);
      const gy = (x) => Art.groundY(x, go);
      const lagging = V0 * (t - D) - cam.camX;          // = TRUCK·(1 − kE): the group sits this far right
      const z1 = layerT(cam, 1).z;
      const leaf = t >= LEAF.t0 - 0.01 && t < LEAF.tl + 6 ? leafAt(t, cam) : null;
      const anchors = {};
      let meEye = null;
      layer(ctx, cam, 1, (c) => {
        const bodyBase = c.getTransform();
        {
          const i0 = Math.floor((off - 200) / 150), i1 = Math.ceil((off + W + 200) / 150);
          for (let i = i0; i <= i1; i++) {                 // shrubs along the back edge
            if (U.hash(i, 61) < 0.45) continue;
            const x = i * 150 + U.hash(i, 62) * 90 - off;
            Art.bush(c, x, gy(x) + 3, 20 + U.hash(i, 63) * 18, U.mix(P.trees[2], P.grass, 0.25), U.shade(P.grass, 0.06), i);
          }
        }
        Art.ground(c, { y: GY, amp: GAMP, offset: off, color: P.ground, color2: P.ground2 });
        Art.trail(c, { y: GY, amp: GAMP, offset: off, color: P.trail });
        c.save();                                         // dappled light on the trail
        c.globalCompositeOperation = 'lighter';
        {
          const j0 = Math.floor((off - 100) / 120), j1 = Math.ceil((off + W + 100) / 120);
          for (let j = j0; j <= j1; j++) {
            if (U.hash(j, 71) < 0.4) continue;
            const x = j * 120 + U.hash(j, 72) * 80 - off;
            const y = gy(x) + 14 + U.hash(j, 73) * 22;
            c.fillStyle = U.rgba(P.light, 0.07 + U.hash(j, 74) * 0.06);
            c.beginPath(); c.ellipse(x, y, 26 + U.hash(j, 75) * 34, 5 + U.hash(j, 76) * 4, 0, 0, TAU); c.fill();
          }
        }
        c.restore();
        Art.grass(c, { seed: 5, y: (x) => gy(x) + 1, offset: off, spacing: 8, h: 22, width: 2.9, color: P.grass, color2: U.shade(P.grass, 0.14), t: wa, wind: 0.7 });
        if (leaf && leaf.landed) drawLeaf(c, leaf, P);

        /* ---------- the hikers ---------- */
        const talkOf = (who) => Art.talkingAt(t, BUBS, who);
        const crewX = (m, Sh, ph) => m.x + lagging + Sh * plantR(ph) * kCorr;
        // chatter without bubbles while the narrator says "everyone's talking…"
        const mutter = (a, b, seed) => (t > a && t < b && U.noise1(t * 2.6, seed) > -0.15 ? 1 : 0);

        // h4 — glued to his phone, filming the summit; strains it up high for "the summit shot"
        {
          const m = CREW[3], look = Art.CAST.h4;
          const ph = m.ph + (RATE / look.height) * tc;
          const x = crewX(m, S * look.height, ph), y = gy(x) + FOOT;
          const reach = U.ease(t, 23.3, 23.95, 'outBack') * (1 - U.ease(t, 25.1, 25.8));
          const wob = U.noise1(t * 1.7, 41) * 0.05 * (1 - U.ease(t, 30.5, 32.2));
          anchors.h4 = Art.person(c, {
            x, y, s: S, look: 'h4', t: tc, seed: m.seed, walk: ph,
            gesture: 'phone', gw: 1, holdF: phone,
            armF: [U.lerp(2.15, 2.78, reach) + wob, U.lerp(0.75, 0.22, reach) + wob * 0.6],
            lean: -0.04 * reach,
            head: { tilt: -0.08 - 0.12 * reach },
            face: { smile: 0.05 + 0.1 * reach, lookY: -0.7 - 0.3 * reach, lookX: 0.7, browUp: 0.35 * reach },
          });
        }
        // h3 — chatty, all hands: "The view up there is supposed to be unreal."
        {
          const m = CREW[2], look = Art.CAST.h3;
          const ph = m.ph + (RATE / look.height) * tc;
          const x = crewX(m, S * look.height, ph), y = gy(x) + FOOT;
          const wA = walkArms(ph);
          const up = U.ease(t, 9.25, 9.65, 'outBack') * (1 - U.ease(t, 10.5, 10.85));   // "up there" — sweep at the peak
          const wide = U.ease(t, 10.65, 11.0, 'outBack') * (1 - U.ease(t, 12.2, 12.8)); // "unreal" — arms flung wide
          const chat = U.ease(t, 16.6, 17.0) * (1 - U.ease(t, 19.6, 20.1));             // turns back to chat with h4
          const gest = Math.sin(t * 5.3) * 0.5 + 0.5;
          let aF = mixA(wA.F, [2.6, 0.12], up);
          aF = mixA(aF, [1.3, 0.55 + 0.1 * Math.sin(t * 7)], wide);
          aF = mixA(aF, [0.85 + 0.35 * gest, 1.0], 0.75 * chat);
          const aB = mixA(wA.B, [-1.1, -0.5], wide);
          const hand = U.ease(t, 22.3, 32.5);                                           // settles into 02's opening pose
          const o = {
            x, y, s: S, look: 'h3', t: tc, seed: m.seed, walk: ph, armF: aF, armB: aB,
            head: { tilt: -0.04 - 0.1 * up + 0.04 * Math.sin(t * 6) * wide + 0.04 * chat, turn: 0.18 * wide + 0.62 * chat },
            face: { smile: 0.3 + 0.35 * Math.max(wide, up, chat), talk: Math.max(talkOf('h3'), mutter(16.8, 19.5, 7)), browUp: 0.5 * Math.max(up, wide), lookX: U.lerp(0.8, -0.6, chat), lookY: -0.4 * up },
          };
          if (hand > 0) { o.head.tilt = U.lerp(o.head.tilt, -0.17, hand); o.face.lookY = U.lerp(o.face.lookY, -0.8, hand); o.face.lookX = U.lerp(o.face.lookX, 0.6, hand); }
          anchors.h3 = Art.person(c, o);
        }
        // h2 — under her enormous pack, hands on the straps; hitches it up; dreamy about the summit
        {
          const m = CREW[1], look = Art.CAST.h2, Sh = S * look.height;
          const ph = m.ph + (RATE / look.height) * tc;
          const x = crewX(m, Sh, ph), y = gy(x) + FOOT;
          const hitch = U.bump(t, 11.45, 0.28) + U.bump(t, 20.9, 0.26);
          const free = U.ease(t, 30.6, 32.3);                    // lets go of the straps: 02 opens on her arms swinging
          const lean = (0.1 - 0.05 * hitch) * (1 - free), bob = -4 * hitch;
          const hipY = -118 + Math.abs(Math.sin(ph)) * 5 - 3 + bob;
          const L = lean + 0.06;
          const strap = (lx, ly) => ({ x: x + (lx * Math.cos(L) - ly * Math.sin(L)) * Sh, y: y + (hipY + lx * Math.sin(L) + ly * Math.cos(L) - 7 * hitch) * Sh });
          const dream = U.ease(t, 13.25, 13.8) * (1 - U.ease(t, 15.6, 16.3));
          const palm = U.ease(t, 13.45, 13.85, 'outBack') * (1 - U.ease(t, 14.9, 15.5));  // "That's where" — an open hand to the peak
          let rF = strap(7, -58);
          if (palm > 0) rF = lerpP(rF, { x: x + 104 * Sh, y: y - 236 * Sh }, palm);
          const shd = shoulders(ph, lean, m.seed, tc, bob, 0.7 * hitch);
          const ik = (sh, q) => Art.ik2(sh.x, sh.y, (q.x - x) / Sh, (q.y - y) / Sh, 50, 47, -1);
          const wA = walkArms(ph);
          anchors.h2 = Art.person(c, {
            x, y, s: S, look: 'h2', t: tc, seed: m.seed, walk: ph, lean, bob, shrug: 0.7 * hitch,
            armF: mixA(ik(shd.F, rF), wA.F, free), armB: mixA(ik(shd.B, strap(3, -55)), wA.B, free),
            head: { tilt: -0.02 - 0.12 * dream },
            face: {
              smile: 0.35 + 0.2 * dream, lookX: 1, lookY: -0.6 * dream, browUp: 0.35 * dream, eyes: hitch > 0.6 ? 'squeeze' : 'open',
              talk: Math.max(talkOf('h2'), mutter(19.3, 21.6, 11), tc > -3 && U.noise1(tc * 1.3, 4) > 0.05 ? 1 : 0),
            },
          });
        }
        // h1 — the leader: two planted poles; "Summit or bust!" with a pole thrust at the peak;
        //      "Keep the pace, people!" over his shoulder
        {
          const m = CREW[0], look = Art.CAST.h1, Sh = S * look.height;
          const ph = m.ph + (RATE / look.height) * tc;
          const x = crewX(m, Sh, ph), y = gy(x) + FOOT;
          const pF = poleState(ph), pB = poleState(ph + Math.PI);
          const toW = (p) => ({ x: x + p.x * Sh, y: y + p.y * Sh });
          // "Summit or bust!": anticipation, thrust (two pumps), hold, recover; and again, calmer, while
          // the narration speaks of "this incredible view at the summit"
          const ant = U.bump(t, 6.22, 0.18);
          const thrust = Math.max(U.ease(t, 6.32, 6.62, 'outBack') * (1 - U.ease(t, 8.5, 9.1, 'inOutSine')), 0.8 * U.ease(t, 20.3, 20.9) * (1 - U.ease(t, 21.9, 22.6)));
          const sh = { x: x + 8 * Sh, y: y - 197 * Sh };
          const tipL = toLayer(cam, 1, sumTip);
          let thP = Math.atan2(tipL.x - sh.x, tipL.y - sh.y);                // from straight down, + forward
          thP -= 0.16 * (U.bump(t, 6.8, 0.13) + U.bump(t, 7.3, 0.13));        // pump, pump
          let handF = toW(pF.hand);
          handF = { x: handF.x - 14 * Sh * ant, y: handF.y + 10 * Sh * ant };
          if (thrust > 0) handF = lerpP(handF, { x: sh.x + Math.sin(thP) * 260 * Sh, y: sh.y + Math.cos(thP) * 260 * Sh }, U.clamp(thrust));
          // "Keep the pace, people!": looks back over his shoulder, beckons with the pole
          const call = U.ease(t, 26.45, 26.8) * (1 - U.ease(t, 28.5, 29.0));
          const beck = U.ease(t, 26.6, 26.95, 'outBack') * (1 - U.ease(t, 27.9, 28.4));
          const thB = 2.15 + 0.32 * Math.sin((t - 26.6) * 9.5);
          if (beck > 0) handF = lerpP(handF, { x: sh.x + Math.sin(thB) * 260 * Sh, y: sh.y + Math.cos(thB) * 260 * Sh }, beck * 0.85);
          const gwPole = Math.max(U.clamp(thrust), beck * 0.85);
          const thArm = thrust >= beck ? thP : thB;
          const bodyInv = bodyBase.translate(x, y).scale(Sh, Sh).inverse();
          const shout = U.clamp(U.ease(t, 6.32, 6.62) * (1 - U.ease(t, 8.5, 9.1)));
          const settle = U.ease(t, 30.6, 32.3);                  // 02's opening expression
          anchors.h1 = Art.person(c, {
            x, y, s: S, look: 'h1', t: tc, seed: m.seed, walk: ph, poles: false,
            reachF: handF, reachB: toW(pB.hand),
            holdF: poleDrawer(bodyInv, pF, gwPole, thArm, look.skin, 7.5),
            holdB: poleDrawer(bodyInv, pB, 0, 0, U.shade(look.skin, -0.15), 7),
            lean: -0.05 * ant + 0.02 * shout,
            head: { tilt: -0.05 - 0.01 * settle - 0.14 * shout + 0.04 * ant, turn: 0.82 * call },
            face: {
              smile: 0.15 - 0.03 * settle + 0.6 * shout + 0.3 * call, brow: -0.15 - 0.15 * shout, browUp: 0.25 * shout,
              talk: Math.max(talkOf('h1'), mutter(20.2, 22.0, 13)), lookX: U.lerp(0.5, -0.4, call) * (1 - settle), lookY: (-0.3 - 0.6 * shout) * (1 - settle),
            },
          });
        }

        /* ---------- me ---------- */
        {
          const lag = lagAt(t);
          const ph = ME_PH0 + RATE * tc - lag / (KF * S);
          const x = ME_X + lagging - lag + S * plantR(ph) * kCorr, y = gy(x) + FOOT;
          const eye = toScreen(cam, 1, { x: x + 14 * S, y: y - 252 * S });
          meEye = eye;
          const w1 = U.noise1(tc * 0.5, 12), w2 = U.noise1(tc * 0.37, 19);
          // base: curious, looking up into the trees, gaze wandering
          const L = {
            head: { tilt: -0.16 + 0.07 * w2, turn: 0 },
            face: { smile: 0.25, lookX: 0.35 + 0.45 * w1, lookY: -0.8, browUp: 0.15 + 0.1 * Math.max(0, w2) },
          };
          // the flock overhead (he follows the leader with his whole head)
          const kBird = U.ease(t, 10.8, 11.4) * (1 - U.ease(t, 15.0, 15.7));
          if (kBird > 0) {
            blendLook(L, gaze(eye, toScreen(cam, 0.08, birdPos(FLOCKS[1], 0, t))), kBird);
            L.face.browUp += 0.25 * kBird; L.face.smile += 0.12 * kBird;
          }
          // the leaf: from the canopy, past h4's nose, onto the trail, under his feet
          const kLeaf = leaf ? U.ease(t, 16.75, 17.3) * (1 - U.ease(t, 21.25, 21.9)) : 0;
          if (kLeaf > 0) {
            blendLook(L, gaze(eye, toScreen(cam, 1, leaf)), kLeaf);
            L.face.smile += 0.15 * kLeaf; L.face.browUp += 0.2 * kLeaf;
          }
          // breathing in the forest air
          const inh = U.ease(t, 23.15, 24.2, 'inOutSine'), exh = U.ease(t, 24.55, 25.7, 'inOutSine');
          const br = inh * (1 - exh);
          if (br > 0) {
            L.head.tilt = U.lerp(L.head.tilt, -0.27, br);
            L.face.smile = U.lerp(L.face.smile, 0.55, br);
            if (br > 0.3) L.face.eyes = 'closed';
          }
          // "Keep the pace, people!" — a start, then a sheepish hurry back into line
          const startle = U.ease(t, 27.0, 27.14) * (1 - U.ease(t, 27.45, 27.9));
          const sheep = U.ease(t, 27.3, 27.7) * (1 - U.ease(t, 29.4, 30.0));
          if (startle > 0 || sheep > 0) {
            blendLook(L, { tilt: 0.03, turn: 0, lookX: 0.9, lookY: -0.1 }, Math.max(startle, sheep));
            L.face.browUp = U.lerp(L.face.browUp, 0.9, startle);
            L.face.brow = 0.35 * sheep;
            L.face.smile = U.lerp(L.face.smile, 0.3, sheep);
            if (startle > 0.5) L.face.eyes = 'wide';
          }
          // walking with them … then a glance aside, toward the undergrowth
          const ahead = U.ease(t, 29.4, 29.9) * (1 - U.ease(t, 30.45, 30.8));
          blendLook(L, { tilt: -0.02, turn: 0, lookX: 0.9, lookY: -0.15 }, ahead);
          const aside = U.ease(t, 30.5, 30.85, 'outSine') * (1 - U.ease(t, 31.55, 32.2));
          if (aside > 0) {
            blendLook(L, { tilt: 0.15, turn: 0.24, lookX: 0.95, lookY: 0.9 }, aside);
            L.face.browUp = U.lerp(L.face.browUp, 0.35, aside);
          }
          // … and back up into the trees: 02's opening state
          const hand = U.ease(t, 31.6, 32.4);
          if (hand > 0) {
            blendLook(L, { tilt: -0.13 + 0.05 * w1, turn: 0, lookX: 0.25 + 0.3 * w1, lookY: -0.7 }, hand);
            L.face.smile = U.lerp(L.face.smile, 0.22, hand);
            L.face.browUp = U.lerp(L.face.browUp, 0, hand);
          }
          const blinks = U.bump(t, 27.02, 0.07) + U.bump(t, 30.42, 0.07);
          if (blinks > 0.02 && !L.face.eyes) L.face.blink = blinks;
          const hurry = U.ease(t, 27.25, 27.7) * (1 - U.ease(t, 29.2, 29.8));
          anchors.me = Art.person(c, {
            x, y, s: S, look: 'me', t: tc, walk: ph,
            lean: 0.09 * hurry + 0.02 * kLeaf,
            shrug: 0.4 * br,
            gesture: br > 0 ? 'open' : undefined, gw: 0.35 * br,
            head: L.head, face: L.face,
          });
        }

        if (leaf && !leaf.landed) drawLeaf(c, leaf, P);
        Art.grass(c, {
          seed: 9, y: (x) => gy(x) + 46, offset: off, spacing: 7, h: 17, hVar: 0.8, width: 2.8,
          color: U.shade(P.grass, -0.12), color2: U.shade(P.grass, 0.02), t: wa, wind: 0.6,
        });
      });

      /* ---------- light: sun rays and shafts through the canopy, pollen drifting in them ---------- */
      const shaftA = 0.11 * (1 - 0.35 * U.ease(t, 29, D));
      soft(ctx, 9, (c) => {
        layer(c, cam, 0, (c2) => Art.rays(c2, { x: 1720, y: 40, angle: 2.2, spread: 0.8, count: 5, len: 1250, color: P.light, alpha: 0.12 + 0.05 * tilted, t: wa, seed: 4, width: 0.06 }));
        drawShafts(c, cam, t, P, shaftA);
      }, 'shafts', { x: 0, y: PIC.top, w: W, h: PIC.h }, 'lighter');
      {
        const span = W + 300;
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        for (let i = 0; i < 42; i++) {
          const p = 0.8 + U.hash(i, 91) * 0.5;
          const bx = U.hash(i, 92) * span;
          const lx = ((((bx - cam.camX * p * 0.96 + U.noise1(t * 0.21 + i, 93) * 40) % span) + span) % span) - 150;
          const ly = 260 + U.hash(i, 94) * 640 - ((t * (6 + U.hash(i, 95) * 8)) % 120) + U.noise1(t * 0.3 + i * 1.7, 96) * 30;
          const q = toScreen(cam, p, { x: lx, y: ly });
          const a = 0.35 * (0.5 + 0.5 * Math.sin(t * (1 + U.hash(i, 97) * 2) + i * 3.1));
          const r = (1.1 + U.hash(i, 98) * 1.6) * layerT(cam, p).z;
          Art.glow(ctx, q.x, q.y, r * 5, P.light, a * 0.5);
          ctx.globalAlpha = a;
          ctx.fillStyle = '#fff6d8';
          ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, TAU); ctx.fill();
        }
        ctx.restore();
      }

      /* ---------- foreground: out-of-focus undergrowth and passing pines ---------- */
      const fgVisible = (wx, p, half) => { const x = toScreen(cam, p, { x: wx - cam.camX * p, y: 0 }).x; return x > -half && x < W + half; };
      const ferns = FERNS.filter((f) => fgVisible(f.wx, f.p, 360 * f.s));
      const trunks = TRUNKS.filter((tr) => fgVisible(tr.wx, tr.p, tr.w + 800));
      if (ferns.length) {
        soft(ctx, 4, (c) => {
          for (const f of ferns) {
            layer(c, cam, f.p, (c2, offp) => {
              const x = f.wx - offp, y = 972;
              const col = U.shade(P.trees[2], -0.36);
              Art.grass(c2, { seed: 40 + f.seed, y: y - 6, offset: 0, x0: x - 170 * f.s, x1: x + 190 * f.s, spacing: 7, h: 62 * f.s, hVar: 0.7, width: 4.6, color: U.shade(col, 0.04), color2: U.shade(col, 0.12), t: wa, wind: 0.5 });
              for (let k = 0; k < 4; k++) {
                const fx = x + (k - 1.5) * 70 * f.s + U.hash(k, f.seed) * 30, fs = f.s * (0.75 + 0.35 * U.hash(k, f.seed + 9));
                Art.fern(c2, fx, y + 10 + k % 2 * 8, fs, U.shade(col, 0.05 * (k % 2)), U.wind(wa, f.wx + k * 40, f.seed + k) * 0.5);
              }
            });
          }
        }, 'fgf', { x: 0, y: 760, w: W, h: PIC.bottom - 760 });
      }
      if (trunks.length) soft(ctx, 7, (c) => { for (const tr of trunks) layer(c, cam, tr.p, (c2, offp) => fgPine(c2, tr.wx - offp, tr.w, P, tr.seed)); }, 'fgt', { x: 0, y: PIC.top, w: W, h: PIC.h });

      /* ---------- words ---------- */
      const bubs = [];
      for (const [a, b, txt, bo] of BUBS) {
        if (t < a || t > b) continue;
        const an = anchors[bo.who];
        const hd = toScreen(cam, 1, an.head), hr = an.head.r * z1;
        const bx = hd.x + bo.dx, by = bo.y;
        // tail: aimed at the speaker's mouth, stopping just above the head
        const dx = bx - hd.x, dy = by - hd.y, n = Math.hypot(dx, dy) || 1;
        bubs.push([a, b, txt, { who: bo.who, x: bx, y: by, tx: hd.x + (dx / n) * (hr + 16), ty: hd.y + (dy / n) * (hr + 16), size: 33, maxW: 430 }]);
      }
      Art.bubbles(ctx, t, bubs);
      Art.captions(ctx, t, CAPS);
    },
  });
})();
