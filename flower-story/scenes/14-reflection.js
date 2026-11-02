/* ==========================================================================
   14 · reflection — “What My Humanity Needs” (golden → sunset → night)
   The epilogue, back at the flower spot. Society rushes up the trail as a
   stream of faceless, light-streaked silhouettes; Wonder taps him on the
   shoulder (“Can we stop here?”); the stream freezes; he sits; a warm glow
   breathes around him; he waves society on and it rushes off as light; a
   constellation lights up inside him while his emotions gather; the
   summit's promise-glow goes out; night. End card on the night sky.

   Shots (local seconds) — two cuts, then one continuous camera
     A   0.0–12.4  wide, golden hour — society streams in from the left
     B  12.4–21.0  medium on him — Wonder appears and taps; “Can we stop here?”
     C  21.0–37.4  medium-wide — the stream freezes into pale ghosts, he sits,
                   the warm glow; he waves them on and they rush off as light
     D  37.4–48.6  push in, close — a constellation within him; emotions gather
     E  48.6–54.6  reframe toward the summit — its promise-glow goes out
     F  54.6–77.0  pull back to the final wide; night; end card; fade
   Kit notes: his sit-down and wave use a local copy of Art.person (rigMe) for
   the in-between frames; end-card text is faded by hand (see render()).
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 77;
  const ease = U.ease;

  /* ---------------- world: the flower spot ---------------- */
  const GO = { y: 870, amp: 16, offset: 1500 };          // the trail's ground line
  const gy = (x) => Art.groundY(x, GO);
  const ME_S = 0.8;
  const X0 = 820, X1 = X0 - 32 * ME_S;                     // where he stands / where he sits
  const Y0 = gy(X0) + 22, Y1 = gy(X1) + 22;
  const FL = { x: 935, y: gy(935) + 50, s: 0.55 };         // the hero flower, just in front of the trail
  const ROCK = { x: 1002, y: gy(1002) + 34, w: 96, h: 64, seed: 4 };
  const FERN = { x: 893, y: gy(893) + 62, s: 0.74 };
  const SUMMIT = { x: 1460, y: 660, h: 410, w: 700 };

  /* ---------------- beats ---------------- */
  const CUT_B = 12.4, CUT_C = 21.0, PUSH0 = 37.4, PUSH1 = 39.6;
  const POP = 13.3;                          // Wonder appears on his shoulder
  const TAP1 = 14.1, TAP2 = TAP1 + TAU / 7;  // her two taps (Art.emotion's tap arm runs on sin(7t))
  const SAY0 = 17.5, SAY1 = 20.9;            // “Can we stop here?” in her handwriting (gone before the cut)
  const SIT0 = 23.4, SIT1 = 25.3;            // he sits down
  const GLOW0 = 26.4;                        // the warm breathing glow
  const WAVE0 = 32.8, WAVE1 = 36.4;          // he waves society on
  const GO_ON = 35.4;                        // …and it resumes
  const CONST0 = 39.0;                       // a constellation within him
  const DIM0 = 50.9, DIM1 = 53.8;            // the summit's promise-glow goes out
  const CARD0 = 62.4;                        // end card

  const CAPS = [
    [2.0, 5.0, 'And the story might be saying'],
    [5.6, 12.0, 'that an emotional need might not be something that society says is important or noteworthy.'],
    [12.9, 16.6, 'Because when your emotion taps you on the shoulder'],
    [17.2, 20.2, 'and says, “Can we stop here?”'],
    [21.4, 25.6, 'then you might have the courage to pause and reflect—'],
    [26.3, 31.1, 'because soul-level introspection is what brings you more well-being and peace.'],
    [32.0, 37.4, 'And then you might tell society, “Go on ahead. I’ll be okay.”'],
    [38.8, 44.8, 'Because I’m focusing on the parts of myself that make me a human being.'],
    [45.6, 49.2, 'And those are what are important to me.'],
    [50.5, 53.7, 'Not so much the summit.'],
    [55.0, 60.6, 'But what my emotion is telling me my humanity needs.'],
  ];

  /* ---------------- time of day: golden → dusk → night ---------------- */
  function tod(t) {
    const dusk = ease(t, 12, 41, 'inOutSine'), night = ease(t, 39, 60, 'inOutSine');
    let P = U.mixDeep(Art.TOD.golden, Art.TOD.dusk, dusk);
    if (night > 0) P = U.mixDeep(P, Art.TOD.night, night);
    return { P, dusk, night };
  }

  /* ---------------- camera (dolly parallax: layer depth d, 1 = subject plane) ---------------- */
  const KC = { // from C on, one continuous camera: slow push · push in to him (C→D) · reframe to the summit (E) · pull back (F)
    x: [[CUT_C, 860], [PUSH0, 848], [PUSH1, 831, 'inOutCubic'], [48.6, 832], [51.6, 1108], [54.6, 1116], [61.8, 962], [D, 960]],
    y: [[CUT_C, 686], [PUSH0, 699], [PUSH1, 742, 'inOutCubic'], [48.6, 776], [51.6, 712], [54.6, 708], [61.8, 548], [D, 532]],
    z: [[CUT_C, 1.38], [PUSH0, 1.5], [PUSH1, 2.24, 'inOutCubic'], [48.6, 2.42], [51.6, 1.8], [54.6, 1.76], [61.8, 1.0], [D, 0.985]],
    bg: [[CUT_C, 5], [PUSH0, 5], [PUSH1, 9], [48.6, 9], [51.6, 1.2], [54.6, 1.0], [58.5, 0]],
  };
  const shotAt = (t) => (t < CUT_B ? 'A' : t < CUT_C ? 'B' : 'C');
  function cam(t, shot) {
    let C;
    if (shot === 'A') { const k = ease(t, 0, CUT_B + 2); C = { x: 966 - 52 * k, y: 586 + 8 * k, z: 1 + 0.07 * k, bg: 0, sf: 2 }; }
    else if (shot === 'B') { const k = ease(t, CUT_B, CUT_C + 1); C = { x: 812 + 10 * k, y: 742 - 6 * k, z: 2.05 + 0.12 * k, bg: 9, sf: 5 }; }
    else C = { x: U.keys(t, KC.x), y: U.keys(t, KC.y), z: U.keys(t, KC.z), bg: U.keys(t, KC.bg), sf: 2.5 };
    const sh = Art.shake(t, 0.22, 14);
    C.x += sh.x / C.z; C.y += sh.y / C.z;
    C.shot = shot;
    return C;
  }
  function layer(ctx, C, d) {
    Art.cam(ctx, { x: W / 2 + (C.x - W / 2) * d, y: H / 2 + (C.y - H / 2) * d, zoom: 1 + (C.z - 1) * d });
  }
  const toScreen = (C, x, y) => ({ x: W / 2 + (x - C.x) * C.z, y: H / 2 + (y - C.y) * C.z });

  /* ---------------- offscreen helpers ---------------- */
  const baseM = () => Art._base || new DOMMatrix();
  /** draw fn into a reduced-resolution full-frame layer in ctx's coordinate space */
  function lowLayer(ctx, key, f, fn) {
    const rel = baseM().inverse().multiply(ctx.getTransform());
    const c = Art.canvas(key, W / f, H / f), c2 = c.getContext('2d');
    c2.setTransform(1, 0, 0, 1, 0, 0);
    c2.globalAlpha = 1; c2.globalCompositeOperation = 'source-over';
    c2.clearRect(0, 0, c.width, c.height);
    c2.setTransform(new DOMMatrix().scale(c.width / W, c.height / H).multiply(rel));
    const res = fn(c2);
    c2.setTransform(1, 0, 0, 1, 0, 0);
    c2.globalAlpha = 1; c2.globalCompositeOperation = 'source-over';
    return { c, res };
  }
  /** keep a layer's alpha, replace its color (→ silhouette) */
  function recolor(c, color) {
    const c2 = c.getContext('2d');
    c2.save(); c2.setTransform(1, 0, 0, 1, 0, 0); c2.globalAlpha = 1;
    c2.globalCompositeOperation = 'source-in'; c2.fillStyle = color; c2.fillRect(0, 0, c.width, c.height);
    c2.restore();
  }
  /** composite a full-frame layer, offset (dx,dy) in film units */
  function blit(ctx, c, dx, dy, a, op) {
    if (a <= 0.002) return;
    ctx.save();
    ctx.setTransform(baseM());
    ctx.globalAlpha *= clamp(a);
    if (op) ctx.globalCompositeOperation = op;
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(c, dx, dy, W, H);
    ctx.restore();
  }
  /** upsample a low-res layer in two bilinear steps (one big step shows blocky edges) */
  function upsample(c, key) {
    const m = Art.canvas(key, c.width * 2, c.height * 2), m2 = m.getContext('2d');
    m2.setTransform(1, 0, 0, 1, 0, 0); m2.globalAlpha = 1; m2.globalCompositeOperation = 'copy';
    m2.imageSmoothingEnabled = true; m2.imageSmoothingQuality = 'high';
    m2.drawImage(c, 0, 0, m.width, m.height);
    m2.globalCompositeOperation = 'source-over';
    return m;
  }
  /** depth of field: amt ≈ blur radius in film px; crossfades sharp→soft for small amounts */
  function dof(ctx, amt, key, fn) {
    if (amt < 0.35) { fn(ctx); return; }
    const f = Math.max(1.5, Math.round(amt * 0.55 * 2) / 2);
    const soft = () => { const lo = lowLayer(ctx, key + f, f, fn).c; blit(ctx, f >= 3.5 ? upsample(lo, key + 'm' + f) : lo, 0, 0, 1); };
    if (amt < 1.6) { fn(ctx); Art.withAlpha(ctx, (amt - 0.35) / 1.25, soft); return; }
    soft();
  }

  /* ======================================================================
     HIS RIG — a faithful local copy of Art.person (js/art.js) with two
     extensions the kit lacks: legs posed by hip + foot IK targets (for an
     in-between sit-down), and weighted arm overrides (to blend a gesture out
     of the sit pose's hands-on-knees IK). Used only for those frames; the
     steady stand/sit frames call Art.person itself, and the two agree exactly
     at the hand-off points.
     ====================================================================== */
  const SK = { thigh: 58, shin: 56, torso: 88, neck: 12, headR: 36, upper: 50, fore: 47, hipW: 22, shW: 27 };
  function limb(ox, oy, a1, l1, rel, l2) {
    const x1 = ox + Math.sin(a1) * l1, y1 = oy + Math.cos(a1) * l1, a2 = a1 + rel;
    return { x0: ox, y0: oy, x1, y1, x2: x1 + Math.sin(a2) * l2, y2: y1 + Math.cos(a2) * l2, a1, a2 };
  }
  function strokeLimb(ctx, L, w1, w2, col) {
    ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.lineWidth = w1; ctx.beginPath(); ctx.moveTo(L.x0, L.y0); ctx.lineTo(L.x1, L.y1); ctx.stroke();
    ctx.lineWidth = w2; ctx.beginPath(); ctx.moveTo(L.x1, L.y1); ctx.lineTo(L.x2, L.y2); ctx.stroke();
  }
  function drawShoe(ctx, L, col) {
    ctx.save();
    ctx.translate(L.x2, L.y2);
    ctx.rotate(clamp((L.a2) * -0.25, -0.5, 0.5));
    ctx.fillStyle = col;
    ctx.beginPath(); ctx.ellipse(7, -2, 15, 7.5, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = U.shade(col, -0.3);
    ctx.fillRect(-7, 2.5, 28, 3);
    ctx.restore();
  }
  const footOf = (ox, oy, a1, rel) => { const L = limb(ox, oy, a1, SK.thigh, rel, SK.shin); return { x: L.x2, y: L.y2 }; };
  // the kit's stand and sit leg geometry (local units, feet anchor at 0,0)
  const STAND = { hip: { x: 0, y: -117 }, fF: footOf(4, -117, 0.05, -0.02), fB: footOf(-4, -117, -0.04, -0.02), rootB: -4 };
  const SIT = { hip: { x: 0, y: -22 }, fF: footOf(4, -22, 2.05, -1.7), fB: footOf(-2, -22, 2.0, -1.5), rootB: -2 };
  const PACK_TOP = { x: -29.75, y: -77.5 };   // top-centre of his pack, relative to the hip (packSize 0.85)

  /**
   * o: x, y (anchor), s, t, face, head, lean, shrug, alpha,
   *    hip {x,y}, fF {x,y}, fB {x,y}, rootB (local units),
   *    sitArms 0..1 (hands-on-knees IK weight), armF/armFw, armB/armBw,
   *    shadowX (px), shadowW (width factor)
   */
  function rigMe(ctx, o) {
    const look = o.look || Art.CAST.me;
    const t = o.t || 0, seed = 'm'.charCodeAt(0) * 7;
    const facing = 1;
    const S = (o.s || 1) * (look.height || 1);
    const x = o.x || 0, y = o.y || 0;
    const thigh = SK.thigh, shin = SK.shin, upper = SK.upper, fore = SK.fore, torsoH = SK.torso;
    const head = Object.assign({ tilt: 0, turn: 0, nod: 0 }, o.head || {});
    const lean = o.lean || 0;
    const breathe = Math.sin(t * 1.7 + seed) * 1.3;
    const hipX = o.hip.x, hipY = o.hip.y, rootB = o.rootB === undefined ? -4 : o.rootB;
    const kF = Art.ik2(hipX + 4, hipY, o.fF.x, o.fF.y, thigh, shin, 1);
    const kB = Art.ik2(hipX + rootB, hipY, o.fB.x, o.fB.y, thigh, shin, 1);
    const legF = limb(hipX + 4, hipY, kF[0], thigh, kF[1], shin);
    const legB = limb(hipX + rootB, hipY, kB[0], thigh, kB[1], shin);
    const shrug = o.shrug || 0;
    const sinL = Math.sin(lean), cosL = Math.cos(lean);
    const topLen = torsoH + breathe * 0.3;
    const shX = hipX + sinL * topLen, shY = hipY - cosL * topLen;
    const shoulderY = shY + 7 - shrug * 8;
    const hTilt = (head.tilt || 0) + (head.nod || 0);
    const neckLen = SK.neck + SK.headR - shrug * 6;
    const hdx = shX + Math.sin(lean + hTilt * 0.6) * neckLen + 4, hdy = shY - Math.cos(lean + hTilt * 0.6) * neckLen;
    const shF = { x: shX + 3, y: shoulderY }, shB = { x: shX - 6, y: shoulderY + 1 };
    // arms: stand ↔ hands-on-knees, then weighted explicit overrides
    const sa = clamp(o.sitArms || 0);
    let aF = [0.1 + Math.sin(t * 1.7 + seed) * 0.015, 0.18], aB = [-0.08, 0.14];
    if (sa > 0) {
      const iF = Art.ik2(shF.x, shF.y, legF.x1 + 4, legF.y1 - 8, upper, fore, -1);
      const iB = Art.ik2(shB.x, shB.y, legB.x1 - 4, legB.y1 - 6, upper, fore, -1);
      aF = sa >= 1 ? iF : [lerp(aF[0], iF[0], sa), lerp(aF[1], iF[1], sa)];
      aB = sa >= 1 ? iB : [lerp(aB[0], iB[0], sa), lerp(aB[1], iB[1], sa)];
    }
    if (o.armF) { const w = o.armFw === undefined ? 1 : clamp(o.armFw); aF = [lerp(aF[0], o.armF[0], w), lerp(aF[1], o.armF[1], w)]; }
    if (o.armB) { const w = o.armBw === undefined ? 1 : clamp(o.armBw); aB = [lerp(aB[0], o.armB[0], w), lerp(aB[1], o.armB[1], w)]; }
    const armF = limb(shF.x, shF.y, aF[0], upper, aF[1], fore);
    const armB = limb(shB.x, shB.y, aB[0], upper, aB[1], fore);

    // ---- draw (as Art.person) ----
    ctx.save();
    if (o.alpha !== undefined) ctx.globalAlpha *= clamp(o.alpha);
    ctx.translate(x, y);
    if (o.shadow !== false) {
      ctx.fillStyle = 'rgba(10,12,20,0.22)';
      ctx.beginPath(); ctx.ellipse(o.shadowX || 0, 2, 46 * S * (o.shadowW || 1), 8 * S, 0, 0, TAU); ctx.fill();
    }
    ctx.scale(S * facing, S);
    const sleeveB = U.shade(look.shirt, -0.2), pantsB = U.shade(look.pants, -0.22);
    strokeLimb(ctx, armB, 13, 12, sleeveB);
    ctx.fillStyle = U.shade(look.skin, -0.15);
    ctx.beginPath(); ctx.arc(armB.x2, armB.y2, 7, 0, TAU); ctx.fill();
    strokeLimb(ctx, legB, 19, 17, pantsB);
    drawShoe(ctx, legB, U.shade(look.shoes, -0.15));
    const ps = look.packSize || 1;
    ctx.save();
    ctx.translate(hipX, hipY);
    ctx.rotate(lean);
    ctx.fillStyle = look.pack;
    const pw = 30 * ps, ph = 70 * ps;
    Art.roundRect(ctx, -SK.shW - pw + 10, -torsoH + 6 - (ps - 1) * 30, pw, ph, 10);
    ctx.fill();
    ctx.fillStyle = U.shade(look.pack, -0.18);
    Art.roundRect(ctx, -SK.shW - pw + 8, -torsoH + 38 - (ps - 1) * 10, pw * 0.7, ph * 0.38, 7);
    ctx.fill();
    ctx.restore();
    strokeLimb(ctx, legF, 19, 17, look.pants);
    drawShoe(ctx, legF, look.shoes);
    ctx.save();
    ctx.translate(hipX, hipY);
    ctx.rotate(lean);
    const hw = SK.hipW, sw = SK.shW, th = topLen;
    ctx.beginPath();
    ctx.moveTo(-hw, 6);
    ctx.lineTo(hw + 1, 6);
    ctx.quadraticCurveTo(sw + 3, -th * 0.45, sw, -th + 9);
    ctx.quadraticCurveTo(sw - 1, -th - 2 + shrug * -6, sw - 13, -th - 2 + shrug * -6);
    ctx.lineTo(-sw + 11, -th - 2 + shrug * -6);
    ctx.quadraticCurveTo(-sw - 1, -th - 1 + shrug * -6, -sw, -th + 10);
    ctx.quadraticCurveTo(-sw - 3, -th * 0.45, -hw, 6);
    ctx.closePath();
    ctx.fillStyle = look.shirt;
    ctx.fill();
    ctx.save();
    ctx.clip();
    ctx.fillStyle = U.rgba('#000000', 0.12);
    ctx.fillRect(-sw - 6, -th - 10, sw * 0.75, th + 20);
    ctx.strokeStyle = U.rgba(look.shirt2 || '#ffffff', 0.55);
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(sw * 0.5, -th + 2); ctx.lineTo(sw * 0.42, 4); ctx.stroke();
    ctx.fillStyle = U.rgba(look.shirt2 || '#ffffff', 0.85);
    ctx.fillRect(-sw, -th * 0.62, sw * 2.2, 5);
    ctx.restore();
    ctx.fillStyle = U.shade(look.shirt, -0.1);
    ctx.beginPath(); ctx.moveTo(-10, -th - 2); ctx.lineTo(10, -th - 2); ctx.lineTo(4, -th + 10); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = U.shade(look.pack, -0.25); ctx.lineWidth = 6; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-6, -th + 2); ctx.quadraticCurveTo(10, -th * 0.6, 4, -th * 0.18); ctx.stroke();
    ctx.restore();
    ctx.strokeStyle = U.shade(look.skin, -0.12);
    ctx.lineWidth = 15;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(shX + 1, shY + 2); ctx.lineTo(lerp(shX, hdx, 0.55), lerp(shY, hdy, 0.55)); ctx.stroke();
    ctx.save();
    ctx.translate(hdx, hdy);
    ctx.rotate(hTilt + lean * 0.3);
    Art.drawHeadLocal(ctx, look, o.face || {}, head.turn || 0, t, seed);
    ctx.restore();
    strokeLimb(ctx, armF, 13.5, 12.5, look.shirt);
    ctx.fillStyle = look.skin;
    ctx.beginPath(); ctx.arc(armF.x2, armF.y2, 7.5, 0, TAU); ctx.fill();
    ctx.restore();

    const Wp = (lx, ly) => ({ x: x + lx * S * facing, y: y + ly * S });
    const ptx = hipX + PACK_TOP.x * cosL - PACK_TOP.y * sinL, pty = hipY + PACK_TOP.x * sinL + PACK_TOP.y * cosL;
    return {
      head: Object.assign(Wp(hdx, hdy), { r: SK.headR * S }), top: Wp(hdx, hdy - SK.headR - 14), mouth: Wp(hdx + 10, hdy + 16),
      handF: Wp(armF.x2, armF.y2), handB: Wp(armB.x2, armB.y2), elbowF: Wp(armF.x1, armF.y1), elbowB: Wp(armB.x1, armB.y1),
      shoulder: Wp(shF.x, shF.y), chest: Wp(shX + 4, shY + 30), hip: Wp(hipX, hipY),
      kneeF: Wp(legF.x1, legF.y1), kneeB: Wp(legB.x1, legB.y1), footF: Wp(legF.x2, legF.y2), footB: Wp(legB.x2, legB.y2),
      pack: Wp(ptx, pty), feet: { x, y }, scale: S,
    };
  }

  /* ======================================================================
     SOCIETY — a stream of faceless hurrying silhouettes trailing streaks of
     light, up the trail toward the summit. It runs on its own clock τ
     (rate 1 = rushing) so it can freeze on “pause” and resume after he
     waves it on. Silhouettes = hikers drawn into a low-res layer, recoloured.
     ====================================================================== */
  const RATE = [[0, 1], [22.0, 1], [23.5, 0.02, 'outCubic'], [GO_ON, 0.02], [GO_ON + 1.1, 1.45, 'inQuad'], [D + 3, 1.45]];
  function tauAt(t) {
    if (t <= 22) return t;
    let s = 22, u = 22, r0 = 1;
    while (u < t - 1e-9) {
      const h = Math.min(0.025, t - u);
      const r1 = U.keys(u + h, RATE);
      s += (r0 + r1) * 0.5 * h;
      u += h; r0 = r1;
    }
    return s;
  }
  const TAU_STOP = tauAt(GO_ON);            // nobody new joins once he waves them on
  const GREY = { skin: '#777777', hair: '#777777', shirt: '#777777', shirt2: '#777777', pants: '#777777', shoes: '#777777', pack: '#777777', hatColor: '#777777' };
  const SIL = [
    { hairStyle: 'short', hat: 'cap', packSize: 0.9, poles: true, height: 1.07 },
    { hairStyle: 'ponytail', packSize: 1.25, height: 0.95 },
    { hairStyle: 'curly', hat: 'bucket', packSize: 0.9, height: 0.92, gesture: 'phoneLook' },
    { hairStyle: 'buzz', hood: true, packSize: 0.95, height: 1.02, gesture: 'phone' },
    { hairStyle: 'messy', hat: 'beanie', packSize: 1.05, height: 0.99, poles: true },
    { hairStyle: 'long', packSize: 0.8, height: 0.94, gesture: 'phoneLook' },
    { hairStyle: 'bun', packSize: 1.15, height: 0.97 },
    { hairStyle: 'short', packSize: 1.0, height: 1.04 },
  ];
  const PHONE = (c) => { c.fillStyle = '#777777'; c.fillRect(-2, -17, 8, 15); };
  const SOC = [];
  (function () {
    let acc = 3.3;
    for (let i = 0; i < 32; i++) {
      const h = (k) => U.hash(i, 140 + k);
      const base = SIL[(i * 3 + Math.floor(h(0) * 2.99)) % SIL.length];
      const look = Object.assign({ name: 's' + i }, GREY, base);
      const s = 0.63 + h(1) * 0.07;
      const v = 232 + h(2) * 46;                          // world px per society-second
      SOC.push({
        look, s, v, kw: v / (40 * s * look.height),       // walk-cycle rate that keeps feet planted (mid-stance foot speed ≈ 40 u/rad)
        ph: h(5) * TAU, lane: 3 + h(6) * 9, seed: 300 + i * 17, gest: base.gesture || null, tau0: acc, id: i,
      });
      acc += h(3) < 0.22 ? 0.42 : 0.95 + h(4) * 0.55;    // a stream, with the odd pair
    }
  })();
  const socAlpha = (t) => clamp(0.74 - 0.22 * ease(t, GLOW0 + 0.2, GLOW0 + 2.8) + 0.16 * ease(t, GO_ON - 0.4, GO_ON + 0.6) - 0.68 * ease(t, GO_ON + 0.9, GO_ON + 3.4));

  function drawSociety(ctx, t, C, T) {
    const P = T.P;
    const A = socAlpha(t);
    const tau = tauAt(t), r = U.keys(t, RATE);
    const streakA = clamp(r) * (1 + 0.9 * U.bump(t, GO_ON + 1.6, 1.6)) * (1 - ease(t, GO_ON + 2.4, GO_ON + 4.4));
    if (A <= 0.01 && streakA <= 0.01) return;
    const vis = [];
    for (const w of SOC) {
      if (w.tau0 > TAU_STOP) break;
      const x = -260 + (tau - w.tau0) * w.v;
      if (x > -320 && x < W + 320) vis.push({ w, x });
    }
    if (!vis.length) return;
    const { c, res } = lowLayer(ctx, 'a8-soc' + C.sf, C.sf, (c2) => vis.map(({ w, x }) => Art.person(c2, {
      x, y: gy(x) + w.lane, s: w.s, look: w.look, t: tau, walk: tau * w.kw + w.ph, stride: 1.1, lean: 0.1,
      shadow: false, seed: w.seed, gesture: w.gest || undefined, gw: 1, holdF: w.gest ? PHONE : undefined,
    })));
    const sp = clamp(r, 0, 1.5);
    // composite at low res: warm rim (sun side) + motion smear (trailing left) + body, then the light
    // streaks and phone glows (so they share the silhouettes' depth of field) → one smooth upsample
    const comp = Art.canvas('a8-soccomp' + C.sf, c.width, c.height), k2 = comp.getContext('2d');
    const px = c.width / W;
    k2.setTransform(1, 0, 0, 1, 0, 0); k2.globalCompositeOperation = 'source-over'; k2.globalAlpha = 1;
    k2.clearRect(0, 0, comp.width, comp.height);
    if (A > 0.01) {
      const frozen = 1 - clamp(r);              // as time stops they pale into ghosts of light
      const rimA = A * 0.85 * (1 - T.dusk * 0.6) * (1 - frozen);
      if (rimA > 0.01) { recolor(c, U.mix(P.light, '#ffffff', 0.3)); k2.globalAlpha = rimA; k2.drawImage(c, 1.8 * C.z * px, 0); }
      recolor(c, U.mix(U.mix(P.mid, '#15142a', 0.5), U.mix(P.fog, P.light, 0.35), frozen * 0.85));
      const smear = sp * 9 * C.z * px;
      for (let k = 3; k >= 1; k--) { k2.globalAlpha = A * sp * [0, 0.36, 0.2, 0.1][k]; if (k2.globalAlpha > 0.004) k2.drawImage(c, -smear * k * 1.25, 0); }
      k2.globalAlpha = A; k2.drawImage(c, 0, 0);
    }
    k2.globalAlpha = 1;
    k2.setTransform(new DOMMatrix().scale(px, comp.height / H).multiply(baseM().inverse().multiply(ctx.getTransform())));
    k2.globalCompositeOperation = 'lighter';
    k2.lineCap = 'round';
    const sc = U.mix(P.light, '#fff4e0', 0.5);
    res.forEach((an, i) => {
      const w = vis[i].w;
      if (streakA > 0.01) {
        const len = (170 + 160 * U.hash(w.id, 9)) * clamp(r, 0, 1.6);
        for (const [py, lw, a] of [[an.head.y + 4, 3.2, 0.5], [an.hip.y - 26 * w.s, 2.4, 0.36], [an.handB.y, 1.8, 0.26]]) {
          const x1 = an.head.x - 10, x0 = x1 - len * (0.7 + 0.3 * a);
          const g = k2.createLinearGradient(x0, 0, x1, 0);
          g.addColorStop(0, U.rgba(sc, 0));
          g.addColorStop(1, U.rgba(sc, a * streakA));
          k2.strokeStyle = g; k2.lineWidth = lw;
          k2.beginPath(); k2.moveTo(x0, py); k2.lineTo(x1, py); k2.stroke();
        }
      }
      if (w.gest && A > 0.01) {
        const flash = w.gest === 'phone' ? U.bump(U.fract(tau * 0.23 + w.id * 0.37), 0.5, 0.025) * clamp(r) : 0;
        Art.glow(k2, an.handF.x + 2, an.handF.y - 9, 13 + flash * 40, '#cfe6ff', A * (0.6 + flash));
      }
    });
    k2.setTransform(1, 0, 0, 1, 0, 0); k2.globalCompositeOperation = 'source-over';
    blit(ctx, C.sf >= 3.5 ? upsample(comp, 'a8-socm' + C.sf) : comp, 0, 0, 1);
  }

  /* ======================================================================
     ENVIRONMENT
     ====================================================================== */
  const sunPos = (t) => ({ x: lerp(1690, 1792, ease(t, 0, 36, 'linear')), y: lerp(368, 746, ease(t, 0, 36, 'inSine')) });
  const MOON = [[44, [190, 700]], [62, [300, 420], 'outSine'], [D, [340, 345], 'linear']];
  /** summit promise-glow (0..1): steady through the day, goes out on “Not so much the summit.” */
  function promise(t) {
    const out = ease(t, DIM0, DIM1, 'inOutSine');
    const flicker = U.bump(t, DIM0 + 0.9, 0.18) * 0.35;
    return clamp((0.3 + 0.7 * T_dusk(t)) * (1 - out) + flicker * (1 - out));
  }
  const T_dusk = (t) => ease(t, 12, 41, 'inOutSine');

  function drawSky(ctx, t, C, T) {
    const P = T.P;
    ctx.save(); layer(ctx, C, 0);
    Art.sky(ctx, P, { horizon: 700 });
    ctx.restore();
    // stars & a faint milky way
    const starA = ease(t, 40, 58);
    if (starA > 0) {
      ctx.save(); layer(ctx, C, 0.02);
      ctx.save();
      ctx.translate(1080, 330); ctx.rotate(-0.42); ctx.scale(1, 0.16);
      Art.glow(ctx, 0, 0, 1050, '#9fb2ff', 0.07 * starA);
      ctx.restore();
      Art.stars(ctx, { seed: 14, count: 320, t, alpha: starA, y0: 60, y1: 690, x0: -40, x1: W + 40 });
      Art.stars(ctx, { seed: 15, count: 90, t, alpha: starA * 0.6, y0: 140, y1: 520, x0: 520, x1: 1640, color: '#dfe6ff' });
      ctx.restore();
    }
    // the moon rises in the east (left) as the sun sets in the west (right)
    const moonA = ease(t, 43, 52);
    ctx.save(); layer(ctx, C, 0.03);
    if (moonA > 0) {
      const [mx, my] = U.keys(t, MOON);
      Art.sun(ctx, mx, my, 27, '#dfe7ff', moonA * 0.9);
      ctx.save(); ctx.globalAlpha *= moonA * 0.16; ctx.fillStyle = '#8f9cc4';
      ctx.beginPath(); ctx.ellipse(mx - 7, my - 5, 9, 7, 0.4, 0, TAU); ctx.ellipse(mx + 8, my + 6, 7, 5, -0.3, 0, TAU); ctx.ellipse(mx + 2, my - 12, 4, 3, 0, 0, TAU); ctx.fill();
      ctx.restore();
    }
    // the low sun, sinking behind the summit's shoulder
    const sun = sunPos(t), sunA = 1 - ease(t, 30, 37);
    if (sunA > 0) Art.sun(ctx, sun.x, sun.y, 34, P.sun, sunA);
    const after = U.bump(t, 36, 12) * (1 - T.night * 0.6);
    if (after > 0) Art.glow(ctx, 1760, 690, 520, P.light, 0.24 * after);
    ctx.restore();
    // clouds catching the light
    ctx.save(); layer(ctx, C, 0.05);
    const cc = U.mix(U.mix('#ffe9c9', '#f2a08c', T.dusk), '#2a3460', T.night);
    Art.clouds(ctx, { seed: 6, count: 5, y0: 190, y1: 380, offset: 220 + t * 7, color: cc, alpha: 0.5 - 0.25 * T.night, shade: U.mix(cc, P.sky[0], 0.35) });
    ctx.restore();
  }

  function drawFar(ctx, t, C, T) {
    const P = T.P;
    ctx.save(); layer(ctx, C, 0.1);
    Art.ridge(ctx, { seed: 21, y: 652, amp: 160, color: U.mix(P.far, P.sky[1], 0.35) });
    ctx.restore();
    ctx.save(); layer(ctx, C, 0.14);
    const pr = promise(t);
    const dimK = ease(t, DIM0, DIM1 + 1.4);
    const Ps = Object.assign({}, P, { summit: U.mix(P.summit, P.sky[1], 0.32 * dimK), snow: U.mix(P.snow, P.sky[1], 0.52 * dimK) });
    const tip = Art.summit(ctx, { x: SUMMIT.x, y: SUMMIT.y, h: SUMMIT.h, w: SUMMIT.w, P: Ps, glow: pr, t, flag: true });
    Art.glow(ctx, tip.x, tip.y + 10, 340, P.light, 0.26 * pr);
    Art.glow(ctx, tip.x, tip.y + 4, 64, '#fff2d6', 0.42 * pr);
    if (pr > 0.02) Art.rays(ctx, { x: tip.x, y: tip.y + 4, angle: 0, spread: TAU, count: 9, len: 150 + 120 * pr, color: P.light, alpha: 0.16 * pr * T.dusk, t, seed: 9, width: 0.025 });
    Art.fog(ctx, { y: 664, h: 180, color: P.fog, alpha: 0.5 });
    ctx.restore();
    ctx.save(); layer(ctx, C, 0.22);
    Art.ridge(ctx, { seed: 8, y: 730, amp: 110, color: P.mid });
    ctx.restore();
    ctx.save(); layer(ctx, C, 0.4);
    Art.forest(ctx, { seed: 31, y: 784, spacing: 62, hMin: 120, hMax: 205, color: P.trees[0], light: U.shade(P.trees[0], 0.1 * (1 - T.night)) });
    Art.fog(ctx, { y: 778, h: 140, color: P.fog, alpha: 0.32 });
    ctx.restore();
    ctx.save(); layer(ctx, C, 0.6);
    Art.forest(ctx, { seed: 32, y: 846, spacing: 86, hMin: 200, hMax: 320, color: P.trees[1], kind: 'mix', sway: 4, t, light: U.shade(P.trees[1], 0.12 * (1 - T.night)) });
    Art.fog(ctx, { y: 818, h: 250, color: P.fog, alpha: 0.42 - 0.16 * T.night });
    ctx.restore();
  }

  function drawGround(ctx, t, T) {
    const P = T.P;
    Art.ground(ctx, Object.assign({ color: P.ground, color2: P.ground2 }, GO));
    Art.trail(ctx, Object.assign({ color: P.trail }, GO));
    Art.grass(ctx, { seed: 41, y: (x) => gy(x) + 1, color: P.grass, color2: U.shade(P.grass, 0.12), spacing: 7, h: 20, t, wind: 0.8 });
  }
  /** the mossy grey rock (grey #8a8f86, moss-green top), lit by the time of day */
  function drawRock(ctx, t, T) {
    const { x, y, w, h, seed } = ROCK;
    const dark = T.dusk * 0.35 + T.night * 0.45;
    const base = U.mix('#8a8f86', T.P.trees[1], dark);
    Art.rock(ctx, x, y, w, h, base, seed);
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(seed, 1) * 8, y - h);
    ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    ctx.lineTo(x + w / 2, y);
    ctx.closePath();
    ctx.clip();
    const moss = U.mix('#6f8f3e', T.P.trees[2], dark * 0.9);
    ctx.fillStyle = moss;
    ctx.beginPath();
    ctx.moveTo(x - w * 0.56, y - h * 0.62);
    ctx.quadraticCurveTo(x - w * 0.3, y - h * 0.86, x - w * 0.05, y - h * 0.8);
    ctx.quadraticCurveTo(x + w * 0.2, y - h * 0.74, x + w * 0.36, y - h * 0.58);
    ctx.quadraticCurveTo(x + w * 0.5, y - h * 0.5, x + w * 0.56, y - h * 0.36);
    ctx.lineTo(x + w * 0.6, y - h * 1.2); ctx.lineTo(x - w * 0.6, y - h * 1.2);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = U.shade(moss, 0.14);
    ctx.beginPath(); ctx.ellipse(x + w * 0.02, y - h * 0.9, w * 0.2, h * 0.07, -0.05, 0, TAU); ctx.fill();
    ctx.restore();
    ctx.fillStyle = 'rgba(10,12,20,0.18)';
    ctx.beginPath(); ctx.ellipse(x, y + 1, w * 0.56, 5, 0, 0, TAU); ctx.fill();
  }
  function drawFront(ctx, t, T) {
    const P = T.P;
    Art.grass(ctx, { seed: 43, y: (x) => gy(x) + 47, color: U.shade(P.grass, -0.1), color2: U.shade(P.grass, 0.06), spacing: 6, h: 28, t, wind: 1 });
    Art.fern(ctx, FERN.x, FERN.y, FERN.s, U.mix(P.grass, P.trees[2], 0.3), U.wind(t, FERN.x, 2));
    const night = T.night;
    const fg = 0.22 + 0.25 * T.dusk + 0.55 * night + 0.06 * Math.sin(t * 1.3);
    if (night > 0) Art.glow(ctx, FL.x + 4, FL.y - 80, 280, '#ff8db0', 0.17 * night);
    const fl = Art.flower(ctx, { x: FL.x, y: FL.y, s: FL.s, t, glow: fg, face: 0.82, sway: 0.8 });
    Art.grass(ctx, { seed: 47, y: (x) => gy(x) + 60, color: U.shade(P.grass, -0.2), spacing: 9, h: 22, t, wind: 1, x0: 0, x1: W });
    // pollen in the golden light; fireflies at night
    Art.motes(ctx, { seed: 21, count: 24, x0: 420, x1: 1460, y0: 560, y1: 905, t, color: '#ffe9b8', size: 1.6, drift: 9, glow: 0.7, alpha: 0.55 * (1 - T.dusk) });
    const ff = ease(t, 44, 56);
    if (ff > 0) Art.motes(ctx, { seed: 33, count: 20, x0: 380, x1: 1540, y0: 640, y1: 915, t, color: '#fff2a6', size: 1.9, drift: 5, glow: 1.3, blink: 1, wander: 44, alpha: 0.9 * ff });
    return fl;
  }
  /** big out-of-focus foreground framing (layer d = 1.3) */
  function drawForeground(ctx, t, C, T) {
    const P = T.P;
    const col = U.mix(P.trees[2], '#05070d', 0.38);
    const amt = C.z > 1.2 ? 14 : 0;
    ctx.save(); layer(ctx, C, 1.3);
    dof(ctx, amt, 'a8-fg', (c) => {
      Art.pine(c, 70, 1180, 900, col, { sway: U.wind(t, 0, 3) * 5 });
      Art.pine(c, 1870, 1200, 960, col, { sway: U.wind(t, 900, 4) * 5 });
      if (C.z > 1.2 && t < PUSH1) { Art.fern(c, 250, 1012, 2.1, col, U.wind(t, 250, 5)); Art.fern(c, 1620, 1018, 2.4, col, U.wind(t, 1620, 6)); }
    });
    ctx.restore();
  }

  /* ======================================================================
     HIS PERFORMANCE
     ====================================================================== */
  const ME_SEED = 'm'.charCodeAt(0) * 7;
  const TR = {
    turn: [[0, 0], [TAP2 + 0.05, 0], [TAP2 + 0.55, 0.75, 'outCubic'], [19.0, 0.75], [19.8, 0.1], [32.2, 0.1], [32.8, 0.35], [36.6, 0.35], [37.4, 0.1], [D, 0.1]],
    lookX: [[0, 0.7], [7.4, 0.7], [8.6, 0.15], [10.6, 0.9], [12.0, 0.7], [TAP2 + 0.05, 0.7], [TAP2 + 0.4, -1, 'outCubic'], [19.0, -1], [19.6, 0.55], [32.2, 0.55], [32.7, 0.9], [37.4, 0.9], [37.6, 0.55], [50.3, 0.55], [50.8, 1], [53.1, 1], [53.7, 0.55], [D, 0.55]],
    lookY: [[0, -0.5], [7.4, -0.5], [8.6, -0.1], [10.6, -0.3], [12.0, -0.45], [TAP2 + 0.05, -0.45], [TAP2 + 0.4, -0.25], [19.0, -0.25], [19.7, 1], [32.2, 1], [32.7, -0.7], [36.6, -0.7], [37.4, -0.45], [37.6, 1], [50.3, 1], [50.8, -0.9], [53.1, -0.9], [53.7, 1], [D, 1]],
    tilt: [[0, -0.06], [TAP2, -0.06], [TAP2 + 0.5, 0.02], [17.6, 0.02], [18.2, 0.07], [19.0, 0.07], [19.8, 0], [26.6, 0], [27.6, -0.07], [31.6, -0.07], [32.2, 0], [32.8, -0.05], [36.6, -0.05], [37.4, 0], [50.3, 0], [50.9, -0.24], [53.1, -0.24], [53.8, 0], [D, 0]],
    nod: [[0, 0], [19.0, 0], [19.8, 0.14], [26.6, 0.14], [27.4, 0], [32.2, 0], [37.4, 0], [37.6, 0.12], [50.3, 0.12], [50.8, 0], [53.1, 0], [53.7, 0.12], [D, 0.12]],
    smile: [[0, 0.12], [TAP2 + 0.5, 0.12], [16.4, 0.55], [19.0, 0.55], [19.8, 0.7], [22.8, 0.6], [26.6, 0.55], [32.6, 0.7], [37.6, 0.6], [41.5, 0.75], [50.3, 0.75], [50.8, 0.3], [53.1, 0.3], [53.8, 0.75], [D, 0.8]],
    browUp: [[0, 0], [TAP2 + 0.05, 0], [TAP2 + 0.4, 0.75], [16.4, 0.3], [19.0, 0.3], [19.8, 0], [D, 0]],
    brow: [[0, 0], [7.4, 0], [8.6, 0.3], [11.6, 0.3], [12.4, 0], [D, 0]],
  };
  function meAct(t) {
    const k = (n) => U.keys(t, TR[n]);
    let eyes = 'open';
    if (t > 26.7 && t < 31.6) eyes = 'closed';
    else if ((t > 41.6 && t < 50.2) || t > 54.4) eyes = 'happy';
    const face = { smile: k('smile'), lookX: k('lookX'), lookY: k('lookY'), browUp: k('browUp'), brow: k('brow'), eyes };
    face.blink = Math.max(U.blink(t, ME_SEED), U.bump(t, TAP1 + 0.12, 0.1));
    if (t > TAP2 + 0.1 && t < TAP2 + 0.6) { face.mouth = 'o'; face.open = 0.15; }
    if (t > 33.3 && t < 35.1) face.talk = 1;
    const breathDeep = U.fade(t, GLOW0, 32.0, 1.0, 0.8) * (0.5 + 0.5 * Math.sin((t - GLOW0) * TAU / 4.2 - 1.2));
    const shrug = 0.35 * U.bump(t, TAP1 + 0.15, 0.3) + 0.2 * U.bump(t, 23.05, 0.35) + 0.14 * breathDeep;
    return { head: { turn: k('turn'), tilt: k('tilt'), nod: k('nod') }, face, shrug, breath: breathDeep };
  }
  /** stand → sit in-between, k 0..1: anticipation, descent on planted feet, legs slide out, settle */
  function sitPose(k) {
    const dx = (X1 - X0) / ME_S;
    const kD = U.E.inOutCubic(clamp((k - 0.14) / 0.5));
    const kL = U.E.inOutSine(clamp((k - 0.56) / 0.24));
    const rise = Math.sin(clamp(k / 0.14) * Math.PI) * 2.5;
    const hipX = lerp(0, dx + 2, kD) - 2 * kL;
    const hipY = lerp(lerp(-117, -44, kD), -22, kL) - rise + Math.sin(clamp((k - 0.76) / 0.24) * Math.PI) * 2.2;
    return {
      hip: { x: hipX, y: hipY },
      fF: { x: lerp(STAND.fF.x, SIT.fF.x + dx, kL), y: lerp(STAND.fF.y, SIT.fF.y, kL) },
      fB: { x: lerp(STAND.fB.x, SIT.fB.x + dx, kL), y: lerp(STAND.fB.y, SIT.fB.y, kL) },
      rootB: lerp(-4, -2, kL),
      lean: 0.42 * Math.sin(clamp((k - 0.1) / 0.72) * Math.PI) * (1 - kL * 0.5) - 0.05 * U.bump(k, 0.86, 0.12),
      sitArms: ease(k, 0.45, 0.95), shadowW: lerp(1, 1.5, kL), shadowX: lerp(0, dx * ME_S, kL),
    };
  }
  /** “Go on ahead”: a gentle forward sweep of the front hand */
  function waveArm(t) {
    const ph = (t - WAVE0) * TAU / 1.25;
    return { a: [1.78 + 0.14 * Math.sin(ph), 0.42 + 0.36 * Math.sin(ph + 0.9)], w: ease(t, WAVE0, WAVE0 + 0.55) * (1 - ease(t, WAVE1 - 0.4, WAVE1 + 0.35)) };
  }
  // sit-pose landmarks in local units (for the constellation)
  const SIT_LM = (() => {
    const lF = limb(4, -22, 2.05, SK.thigh, -1.7, SK.shin), lB = limb(-2, -22, 2.0, SK.thigh, -1.5, SK.shin);
    return { kneeF: { x: lF.x1, y: lF.y1 }, kneeB: { x: lB.x1, y: lB.y1 }, footF: { x: lF.x2, y: lF.y2 }, footB: { x: lB.x2, y: lB.y2 } };
  })();

  /** how he is lit: dusk ambience, the constellation's night-sky silhouette, night, the inner glow */
  function lightState(t, T) {
    const sil = ease(t, CONST0, CONST0 + 1.6);
    return {
      amb: Math.max(0.18 * T.dusk, 0.88 * sil, 0.8 * T.night), sil,
      ambCol: U.mix(U.mix('#3a2850', '#16204a', sil), '#0c1330', T.night * (1 - sil * 0.5)),
      warm: 0.3 * U.fade(t, GLOW0, CONST0 + 1, 1.6, 1.4),
      stars: ease(t, CONST0 + 0.6, CONST0 + 2.8) * (1 - 0.4 * ease(t, 48, 56)),
    };
  }
  // his colours, tinted by the light (Art.person takes a look object; no offscreen needed)
  const ME_KEYS = ['skin', 'hair', 'hatColor', 'shirt', 'shirt2', 'pants', 'shoes', 'pack', 'beard'];
  function tintLook(L) {
    const b = Art.CAST.me;
    if (L.amb < 0.004 && L.warm < 0.004) return b;
    const o = Object.assign({}, b);
    for (const k of ME_KEYS) o[k] = U.mix(U.mix(b[k], L.ambCol, L.amb), '#ffc77e', L.warm * (1 - L.amb));
    return o;
  }
  // a constellation along his limbs: [landmark, size, delay]
  const STARS = [['crown', 1.0, 0.25], ['head', 1.5, 0.0], ['neck', 1.0, 0.45], ['heart', 2.3, 0.15], ['elbowF', 1.1, 0.7],
    ['handF', 1.3, 0.95], ['hip', 1.2, 0.6], ['kneeF', 1.3, 0.85], ['footF', 1.1, 1.2], ['kneeB', 0.9, 1.05]];
  const LINES = [['crown', 'head'], ['head', 'neck'], ['neck', 'heart'], ['heart', 'hip'], ['neck', 'elbowF'], ['elbowF', 'handF'],
    ['hip', 'kneeF'], ['kneeF', 'footF'], ['hip', 'kneeB'], ['handF', 'kneeF']];
  function landmarks(an) {
    const S = an.scale, L = (p) => ({ x: an.feet.x + p.x * S, y: an.feet.y + p.y * S });
    return {
      head: { x: an.head.x - 3 * S, y: an.head.y + 2 * S }, crown: { x: an.head.x - 8 * S, y: an.head.y - 24 * S },
      neck: { x: lerp(an.shoulder.x, an.head.x, 0.3) - 6 * S, y: lerp(an.shoulder.y, an.head.y, 0.3) },
      heart: { x: an.chest.x - 2 * S, y: an.chest.y - 4 * S },
      elbowF: { x: lerp(an.shoulder.x, an.handF.x, 0.5) - 4 * S, y: lerp(an.shoulder.y, an.handF.y, 0.5) + 6 * S },
      handF: an.handF, hip: { x: an.hip.x + 2 * S, y: an.hip.y - 6 * S },
      kneeF: L(SIT_LM.kneeF), kneeB: L({ x: SIT_LM.kneeB.x - 8, y: SIT_LM.kneeB.y + 4 }), footF: L({ x: SIT_LM.footF.x - 6, y: SIT_LM.footF.y - 6 }),
    };
  }
  function drawConstellation(ctx, an, L, t) {
    if (L.stars <= 0.005) return;
    const lm = landmarks(an), S = an.scale;
    ctx.save();
    ctx.lineWidth = 1.1; ctx.lineCap = 'round';
    const kl = clamp(L.stars * 1.6 - 0.35);
    if (kl > 0) {
      ctx.strokeStyle = U.rgba('#c9d6ff', 0.5 * kl);
      ctx.beginPath();
      for (const [a, b] of LINES) { const A = lm[a], B = lm[b]; ctx.moveTo(A.x, A.y); ctx.lineTo(lerp(A.x, B.x, kl), lerp(A.y, B.y, kl)); }
      ctx.stroke();
    }
    for (const [n, sz, dl] of STARS) {
      const p = lm[n], k = clamp(L.stars * 2.2 - dl);
      if (k <= 0) continue;
      const heart = n === 'heart';
      const tw = 0.72 + 0.28 * Math.sin(t * (1.3 + sz) + dl * 9);
      const r = sz * S * 2.6 * (heart ? 1 + 0.15 * Math.sin(t * 1.9) : 1);
      Art.glow(ctx, p.x, p.y, r * 4.5, heart ? '#ff9ec0' : '#bcd0ff', 0.5 * k * tw);
      ctx.fillStyle = U.rgba(heart ? '#ffe2ec' : '#ffffff', k * tw);
      ctx.beginPath(); ctx.arc(p.x, p.y, r * 0.55, 0, TAU); ctx.fill();
    }
    ctx.restore();
  }
  function drawMe(ctx, t, T) {
    const act = meAct(t);
    const L = lightState(t, T);
    const look = tintLook(L);
    const common = { s: ME_S, t, head: act.head, face: act.face, shrug: act.shrug, look };
    let r;
    if (t < SIT0) r = Art.person(ctx, Object.assign({ x: X0, y: Y0, pose: 'stand' }, common));
    else if (t < SIT1) {
      const k = (t - SIT0) / (SIT1 - SIT0);
      r = rigMe(ctx, Object.assign({ x: X0, y: lerp(Y0, Y1, k) }, common, sitPose(k)));
    } else {
      const wa = waveArm(t);
      if (wa.w > 0.001) r = rigMe(ctx, Object.assign({ x: X1, y: Y1, hip: SIT.hip, fF: SIT.fF, fB: SIT.fB, rootB: SIT.rootB, sitArms: 1, armF: wa.a, armFw: wa.w, shadowW: 1.5 }, common));
      else r = Art.person(ctx, Object.assign({ x: X1, y: Y1, pose: 'sit' }, common));
    }
    if (!r.pack) r.pack = { x: r.hip.x + PACK_TOP.x * r.scale, y: r.hip.y + PACK_TOP.y * r.scale };
    if (L.sil > 0.01) Art.glow(ctx, r.chest.x - 4, r.chest.y + 6, 70, '#8a6ad0', 0.3 * L.sil);   // a faint nebula within
    drawConstellation(ctx, r, L, t);
    r.light = L;
    r.wonderAt = { x: r.pack.x - 3, y: r.pack.y + 3 };
    r.act = act;
    return r;
  }
  /** warm breathing glow around him (behind = before drawMe, front = after) */
  function meGlow(ctx, t, an, front) {
    const k = U.fade(t, GLOW0, CONST0 + 3, 2.2, 3) * 0.85 + 0.15 * ease(t, GLOW0, GLOW0 + 2);
    if (k <= 0.005) return;
    const br = 1 + 0.07 * Math.sin((t - GLOW0) * TAU / 4.2 - 1.2);
    const R = (80 + 250 * ease(t, GLOW0, GLOW0 + 3.2, 'outCubic')) * br;
    const cx = an ? an.chest.x : X1 + 3, cy = an ? an.chest.y : Y1 - 66;
    if (!front) { Art.glow(ctx, cx, cy, R, '#ffcf86', 0.42 * k); Art.glow(ctx, cx, cy, R * 0.45, '#fff0cc', 0.18 * k); }
    else Art.glow(ctx, cx, cy, R * 0.7, '#ffd9a0', 0.1 * k);
  }

  /* ======================================================================
     WONDER (on his shoulder) and the emotions that gather around him
     ====================================================================== */
  const TAP_HOLD = TAP1 - Math.PI / 14;                       // her arm rests until the first tap
  const TAP_PH = (Math.PI / 2 + TAU * 16) / 7 - TAP1;          // so that sin(7·te) peaks at TAP1, TAP2
  function drawWonder(ctx, t, an) {
    if (t < POP) return null;
    const p = an.wonderAt;
    let s = 0.44 * U.ease(t, POP, POP + 0.55, 'outBack');
    let arms = 'idle', te = t, rot = 0, squash = 0;
    const face = { smile: 0.45, eyes: 'open', lookX: 0.6, lookY: 0.4 };
    if (t < TAP2 + Math.PI / 14) { arms = 'tap'; te = Math.max(t, TAP_HOLD) + TAP_PH; face.browUp = 0.4; face.lookX = 1; face.lookY = 0; }
    else if (t < CUT_C) {
      arms = 'point'; rot = 0.36 * ease(t, TAP2 + 0.22, TAP2 + 0.7, 'outBack');
      face.eyes = t > SAY0 && t < SAY0 + 1.6 ? 'sparkle' : 'open';
      face.talk = t > SAY0 && t < SAY0 + 1.3 ? 1 : 0;
      face.smile = 0.6; face.browUp = 0.5; face.lookX = 1; face.lookY = 0.6;
    } else if (t < 26.6) {
      face.lookX = t > 22.1 && t < 23.6 ? -0.9 : 0.6; face.lookY = t > 22.1 && t < 23.6 ? -0.3 : 0.6;
      squash = -0.35 * U.bump(t, 25.1, 0.18) + 0.25 * U.bump(t, 25.38, 0.2);
      face.smile = 0.5 + 0.3 * ease(t, 24.8, 25.4); face.eyes = t > 25.0 ? 'happy' : 'open';
    } else if (t < 33.0) { arms = 'hug'; face.eyes = 'closed'; face.smile = 0.6; squash = 0.08 * Math.sin((t - GLOW0) * TAU / 4.2); }
    else if (t < 36.4) { arms = 'wave'; face.eyes = 'happy'; face.smile = 0.85; squash = -0.2 * U.bump(t, 33.08, 0.12); }
    else if (t < 44.0) { face.eyes = 'happy'; face.smile = 0.7; face.lookX = 0.7; face.lookY = 0.7; squash = -0.2 * U.bump(t, 36.45, 0.12); }
    else if (t > 50.4 && t < 53.6) {
      face.eyes = 'open'; face.smile = 0.3; face.lookX = 1; face.lookY = -1; face.browUp = 0.3;
      if (t > 52.5) { arms = 'shrug'; face.lookY = 0.2; face.smile = 0.55; face.eyes = 'happy'; squash = -0.18 * U.bump(t, 52.55, 0.12); }
    } else {
      arms = 'hug'; face.eyes = t > 58 ? 'closed' : 'happy'; face.smile = 0.7; face.blink = t > 58 ? 0 : undefined;
      squash = -0.25 * U.bump(t, 44.05, 0.14) - 0.2 * U.bump(t, 53.65, 0.12) + 0.1 * ease(t, 57, 60);
      rot = -0.12 * ease(t, 57, 60);
    }
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(rot);
    const pop = U.bump(t, POP + 0.12, 0.35);
    if (pop > 0) Art.glow(ctx, 0, -20, 90, '#fff0b0', 0.6 * pop);
    const r = Art.emotion(ctx, { x: 0, y: 0, s, color: Art.EMO.wonder, face, arms, t: te, seed: 5, squash, glow: 0.7 + 0.4 * an.light.sil });
    ctx.restore();
    // a little burst of sparkles when she appears
    if (t < POP + 0.9) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 7; i++) {
        const a = i / 7 * TAU + 0.4, k = ease(t, POP, POP + 0.8, 'outCubic');
        const px = p.x + Math.cos(a) * (8 + 34 * k), py = p.y - 20 + Math.sin(a) * (8 + 30 * k);
        Art.glow(ctx, px, py, 7, '#ffe9a0', (1 - k) * 0.9);
      }
      ctx.restore();
    }
    return { x: p.x, y: p.y, head: r.head };
  }
  const GATHER = [
    { col: Art.EMO.calm, t0: 40.4, from: [560, 912], to: () => [X1 - 66, gy(X1 - 66) + 34], s: 0.4, facing: 1, seed: 21, arc: 60, arms: 'idle' },
    { col: Art.EMO.dream, t0: 41.0, from: [640, 600], to: () => [X1 - 48, Y1 - 128], s: 0.36, facing: 1, seed: 22, arc: -20, float: 1, arms: 'idle' },
    { col: Art.EMO.heart, t0: 41.6, from: [880, 660], to: () => [X1 + SIT_LM.kneeF.x * ME_S + 2, Y1 + SIT_LM.kneeF.y * ME_S - 6], s: 0.33, facing: -1, seed: 23, arc: 30, arms: 'hug' },
    { col: Art.EMO.spark, t0: 42.2, from: [1180, 800], to: () => [ROCK.x - 8, ROCK.y - ROCK.h + 6], s: 0.36, facing: -1, seed: 24, arc: 70, arms: 'idle' },
  ];
  function drawGather(ctx, t) {
    for (const g of GATHER) {
      if (t < g.t0) continue;
      const p = ease(t, g.t0, g.t0 + 1.9, 'outCubic');
      const [tx, ty] = g.to();
      const x = lerp(g.from[0], tx, p), y = lerp(g.from[1], ty, p) - g.arc * Math.sin(Math.PI * p);
      const landed = t > g.t0 + 1.75;
      const squash = -0.3 * U.bump(t, g.t0 + 1.85, 0.16) + 0.18 * U.bump(t, g.t0 + 2.1, 0.18);
      const fy = g.float ? Math.sin(t * 1.4 + g.seed) * 4 * ease(t, g.t0 + 1.6, g.t0 + 2.4) : 0;
      Art.emotion(ctx, {
        x, y: y + fy, s: g.s, color: g.col, t, seed: g.seed, facing: g.facing, squash, alpha: ease(t, g.t0, g.t0 + 0.5),
        arms: landed ? g.arms : 'idle', glow: 0.8,
        face: landed ? { eyes: 'happy', smile: 0.7 } : { eyes: 'open', smile: 0.5, lookX: 0.8, lookY: 0.3 },
      });
    }
  }

  /* ======================================================================
     ORCHESTRATION
     ====================================================================== */
  function renderWorld(ctx, t, C) {
    const T = tod(t);
    drawSky(ctx, t, C, T);
    // god rays from the low sun (in the air behind the ridges)
    const rayA = 0.1 * (1 - ease(t, 18, 32));
    if (rayA > 0) { const s = sunPos(t); ctx.save(); layer(ctx, C, 0.05); Art.rays(ctx, { x: s.x, y: s.y, angle: 2.75, spread: 0.55, count: 7, len: 1700, color: T.P.light, alpha: rayA, t, seed: 3 }); ctx.restore(); }
    dof(ctx, C.bg, 'a8-bg', (c) => drawFar(c, t, C, T));
    ctx.save();
    layer(ctx, C, 1);
    drawGround(ctx, t, T);
    drawSociety(ctx, t, C, T);
    drawRock(ctx, t, T);
    meGlow(ctx, t, null, false);
    const an = drawMe(ctx, t, T);
    meGlow(ctx, t, an, true);
    if (T.night > 0.01) Art.glow(ctx, FL.x - 30, FL.y - 70, 170, '#ffb0c4', 0.22 * T.night);   // the flower lights his front
    const wo = drawWonder(ctx, t, an);
    drawGather(ctx, t);
    drawFront(ctx, t, T);
    ctx.restore();
    drawForeground(ctx, t, C, T);
    return { an, wo };
  }

  function render(ctx, t) {
    const shot = shotAt(t);
    const C = cam(t, shot);
    const out = renderWorld(ctx, t, C);
    // Wonder's words, in her handwriting
    const say = U.fade(t, SAY0, SAY1, 0.25, 0.6);
    if (say > 0 && out.wo) {
      const p = toScreen(C, out.wo.x, out.wo.y);
      Art.hand(ctx, 'Can we stop here?', { x: p.x - 250, y: p.y - 150, size: 62, reveal: ease(t, SAY0, SAY0 + 1.3, 'linear'), alpha: say, color: '#ffe2a0', glow: 'rgba(120,64,10,0.55)' });
    }
    Art.captions(ctx, t, CAPS);
    // end card on the night sky
    const card = 1; // the engine's 2.5 s fadeOut now fades deferred text too
    // the film's title, small — “the Flower,” in rose, as on the opening title card
    if (t > CARD0 - 0.1) {
      const segs = [['The Hikers, ', '#f4eadb', 'rgba(255,190,160,0.3)'], ['the Flower,', '#ffd2df', 'rgba(255,111,156,0.55)'], [' and the Meaning We Create', '#f4eadb', 'rgba(255,190,160,0.3)']];
      ctx.save(); ctx.font = Art.font(44, 'serif', 500, 'italic');
      const ws = segs.map(([s]) => ctx.measureText(s).width);
      ctx.restore();
      let x = W / 2 - (ws[0] + ws[1] + ws[2]) / 2;
      segs.forEach(([s, color, glow], i) => {
        Art.title(ctx, s, { x, y: 336, size: 44, align: 'left', reveal: ease(t, CARD0 + i * 0.75, CARD0 + 1.5 + i * 0.85, 'outSine'), alpha: card * 0.92, color, glow, now: false });
        x += ws[i];
      });
    }
    const rule = ease(t, CARD0 + 2.0, CARD0 + 3.6, 'inOutCubic');
    if (rule > 0) Art.later((c) => { c.strokeStyle = U.rgba('#f7efe2', 0.42 * card); c.lineWidth = 1.5; c.beginPath(); c.moveTo(W / 2 - 110 * rule, 384); c.lineTo(W / 2 + 110 * rule, 384); c.stroke(); });
    Art.title(ctx, 'The End', { y: 456, size: 92, reveal: ease(t, CARD0 + 2.6, CARD0 + 4.6, 'outSine'), alpha: card, glow: 'rgba(255,111,156,0.45)', now: false });
  }

  Film.scene({
    id: 'reflection',
    order: 14,
    title: 'What My Humanity Needs',
    chapter: 'Part Three · The Meaning',
    duration: D,
    mood: 'reflection',
    sfx: [
      [4.8, 'whoosh', { gain: 0.35 }], [5.1, 'footsteps', { gain: 0.3 }],
      [POP, 'sparkle', { gain: 0.5 }], [TAP1, 'tap', { gain: 0.8 }], [TAP2, 'tap', { gain: 0.8 }],
      [SAY0, 'chime', { gain: 0.3 }],
      [22.1, 'shimmer', { gain: 0.45 }],
      [24.7, 'breath', { gain: 0.5 }],
      [GLOW0, 'swell', { gain: 0.5 }],
      [GO_ON + 0.3, 'whoosh', { gain: 0.45 }],
      [CONST0 + 0.6, 'shimmer', { gain: 0.5 }], [40.6, 'sparkle', { gain: 0.3 }], [41.8, 'sparkle', { gain: 0.25 }],
      [DIM0, 'wind', { gain: 0.3 }],
      [55.4, 'bloom', { gain: 0.4 }],
      [CARD0, 'chime', { gain: 0.45 }], [CARD0 + 2.6, 'bell', { gain: 0.3 }],
    ],
    fadeIn: 1.5,
    fadeOut: 2.5,
    post: (t) => ({ vignette: 0.34 + 0.12 * ease(t, 40, 60), grain: 0.045, letterbox: 1 }),
    render,
  });
})();
