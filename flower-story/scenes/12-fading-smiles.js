/* ==========================================================================
   12 · The Parking Lot — the hikers burst out of Embarrassment’s Flowers,
   beaming, the $200 flower held up like a trophy. Embarrassment leans in the
   doorway shaking his head. They cross a sunny parking lot toward a big shiny
   SUV, and with every step the glow leaks out of them: smiles flatten, the
   trophy sinks, a petal drops, a cloud slides over the sun and the colour
   drains. At the car the flower goes into the trunk — thunk — and three
   blank faces look back at us.

   Staging: an eye-level 2.5D set. Each depth plane k (1 = the walking line)
   is drawn with plane(); the asphalt's stall lines are true one-point
   perspective, so the lot shears as the camera trucks right.
   Reuses window.TownKit from scene 10 (shopfront, backdrop, town strip).
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;
  const D = 24;

  /* ---------------- TownKit (scene 10) with a minimal fallback ---------------- */
  const TK = (() => {
    if (window.TownKit) return window.TownKit;
    const F = {};
    F.path = (t, keys) => U.keys(t, keys.map(([a, b]) => [a, b, 'inOutSine']));
    F.backdrop = (g, P, o = {}) => {
      Art.ridge(g, { seed: 21, y: (o.y || 500) - 30, amp: 200, color: P.far, x0: -500, x1: W + 500 });
      return Art.summit(g, { x: o.sx || 1300, y: (o.y || 500) + 40, h: o.sh || 330, w: o.sw || 580, P, t: o.t || 0 });
    };
    F.townStrip = () => ({ tiers: [], wins: [], x0: 0, x1: 1, y0: 0, y1: 1 });
    F.drawStrip = () => {};
    F.lamp = (g, x, y, s) => { g.fillStyle = '#2d3836'; g.fillRect(x - 4 * s, y - 300 * s, 8 * s, 300 * s); };
    F.shopfront = (ctx, x, y, s, t, o = {}) => {
      ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
      ctx.fillStyle = '#efe3cf'; ctx.fillRect(-300, -880, 600, 880);
      ctx.fillStyle = '#3b2a25'; ctx.fillRect(-290, -566, 580, 94); ctx.fillRect(84, -406, 160, 406);
      ctx.fillStyle = '#4f7a5a'; ctx.fillRect(-292, -462, 554, 70);
      ctx.restore();
      if (o.between) o.between(ctx);
      return { door: { x: x + 164 * s, y } };
    };
    F.C = { brass: '#cda24c' };
    return F;
  })();

  /* ---------------- set geometry ---------------- */
  const HY = 560, CAMH = 300;             // horizon (eye level) and camera height, walking-line units
  const K_SHOP = 0.82, K_SUV = 0.93, K_BACK = 0.56, K_CARS = 0.68;
  const SHOP_S = 1;
  const DOOR = { x0: 84, x1: 244, top: -406 };   // shop-local door opening
  const P0 = U.mixDeep(Art.TOD.morning, Art.TOD.golden, 0.14);
  const PGREY = Art.desatPalette(U.mixDeep(Art.TOD.morning, Art.TOD.dusk, 0.12), 0.55);

  // beats (local seconds)
  const T = {
    emb: [0.95, 1.65], flash: 1.95, petal1: 11.2, glint: 10.9,
    sweep: [12.4, 14.6], stop: 17.3,
    hatchUp: [17.75, 18.75], load: [18.7, 19.75], reach: [19.75, 20.25], slam: [20.25, 20.55],
    turn: [21.05, 21.55],
  };
  const THUNK = T.slam[1];
  const NARR = [
    [1.5, 4.9, 'Embarrassment watches them leave, shaking his head.'],
    [8.4, 11.6, 'Before they even make it to their car,'],
    [12.0, 15.4, 'their smiles have already started to fade.'],
  ];

  /* ---------------- walking: one shared speed, per-character phase ---------------- */
  const VK = [[0, 96], [0.6, 150], [4.0, 148], [9.0, 122], [14.0, 100], [16.2, 76], [17.3, 0], [24, 0]];
  const SK = [[0, 1.05], [5, 1.0], [12, 0.86], [16.0, 0.74], [17.3, 0], [24, 0]];
  const CAST = ['h1', 'h2', 'h4'];
  const SCALE = { h1: 1, h2: 1, h4: 1 };
  const PH0 = { h1: 0.4, h2: 2.3, h4: 4.4 };
  const stepLen = (who) => 29.5 * SCALE[who] * (Art.CAST[who].height || 1);
  /** integrate distance (shared) and each walker's phase from 0 to t (pure; fixed steps) */
  function walk(t) {
    const tt = clamp(t, 0, T.stop + 0.05), n = Math.max(1, Math.ceil(tt * 50)), dt = tt / n;
    let d = 0;
    const ph = { h1: PH0.h1, h2: PH0.h2, h4: PH0.h4 };
    for (let i = 0; i < n; i++) {
      const tm = (i + 0.5) * dt, v = Math.max(0, TK.path(tm, VK)), st = TK.path(tm, SK);
      d += v * dt;
      if (st > 0.05) {
        const f = Math.sin(0.42 * st) / Math.sin(0.42);
        for (const w of CAST) ph[w] += (v / (stepLen(w) * f)) * dt;
      }
    }
    return { d, ph, stride: Math.max(0, TK.path(t, SK)) };
  }
  const DTOT = walk(T.stop + 1).d;
  const X0 = { h1: 470, h2: 330, h4: 205 };     // start positions (just out of the door)
  const K0 = { h1: 0.92, h2: 0.88, h4: 0.85 };  // start depth (stepping off the threshold)
  const K1 = { h1: 1.0, h2: 0.965, h4: 1.04 };  // walking depth

  /* ---------------- camera ---------------- */
  // holds on the shop while the hikers burst out, then catches up and tracks them; tighter
  // while the smiles fade; wider at the car; a slow push on the blank faces at the end
  const CX0 = 700;
  const ZK = [[0, 0.92], [3.8, 0.96], [7.8, 1.3], [14, 1.32], [17.0, 1.06], [20.8, 1.08], [24, 1.46]];
  const OFFK = [[0, 370], [4, 200], [8, 110], [14, 100], [17.3, 300], [21, 270], [24, 150]];
  const camAt = (t, d) => {
    const z = TK.path(t, ZK);
    const track = X0.h2 + d + TK.path(t, OFFK);
    return { x: lerp(CX0, track, U.ease(t, 2.4, 6.6, 'inOutSine')), z, fy: 860 - 350 / z };
  };
  const XREST = CX0;
  /** transform into depth plane k (world units, ground at y = 0) */
  const plane = (ctx, c, k) => { ctx.translate(960 - c.z * k * c.x, 540 + c.z * (HY + k * CAMH - c.fy)); ctx.scale(c.z * k, c.z * k); };
  const proj = (c, k, X, Y = 0) => ({ x: 960 + c.z * k * (X - c.x), y: 540 + c.z * (HY + k * (CAMH + Y) - c.fy) });
  /** far layers designed in rest-screen coordinates, parallax p */
  const far = (ctx, c, p) => {
    const zf = 1 + (c.z - 1) * p, hz = 540 + c.z * (HY - c.fy);
    ctx.translate(960 - zf * (960 + p * (c.x - XREST)), hz - zf * HY);
    ctx.scale(zf, zf);
  };

  // where h1 stops; the SUV's rear is placed just to his right (computed for the final camera)
  const camEnd = camAt(T.stop, DTOT);
  const H1END = X0.h1 + DTOT;
  const SUV_REAR = camEnd.x + ((960 + camEnd.z * (H1END - camEnd.x) + 92) - 960) / (camEnd.z * K_SUV);
  const SUV_X = SUV_REAR + 416;

  /* ---------------- light: the cloud over the sun ---------------- */
  const sunK = (t) => 1 - U.ease(t, T.sweep[0], T.sweep[1], 'inOutSine');   // 1 sunny → 0 flat

  /* ---------------- the $200 flower (matches scene 11) ---------------- */
  const DUSTY_COL = { petal: '#d8c25a', tip: '#efe2a0', inner: '#a08a2a' };
  function potShape(c, x, y, w, h, col) {
    c.fillStyle = col;
    c.beginPath(); c.moveTo(x - w * 0.38, y); c.lineTo(x + w * 0.38, y); c.lineTo(x + w * 0.5, y - h * 0.84); c.lineTo(x - w * 0.5, y - h * 0.84); c.closePath(); c.fill();
    c.fillStyle = U.shade(col, 0.1);
    Art.roundRect(c, x - w * 0.56, y - h, w * 1.12, h * 0.22, 3); c.fill();
    c.fillStyle = 'rgba(40,20,10,0.14)';
    c.beginPath(); c.moveTo(x + w * 0.1, y); c.lineTo(x + w * 0.38, y); c.lineTo(x + w * 0.5, y - h * 0.8); c.lineTo(x + w * 0.2, y - h * 0.8); c.closePath(); c.fill();
    return y - h;
  }
  /** (x, y) = pot bottom centre; o = { droop, petals, sway, tag } → flower head (caller coords) */
  function dusty(c, x, y, s, t, o = {}) {
    c.save();
    c.translate(x, y); c.scale(s, s); c.translate(-x, -y);
    const pc = '#a98a72';
    const rim = potShape(c, x, y, 46, 38, U.mix(pc, '#b9ad98', 0.35));
    c.fillStyle = U.shade(pc, -0.35);
    c.beginPath(); c.moveTo(x + 10, rim); c.lineTo(x + 20, rim); c.lineTo(x + 15, rim + 7); c.closePath(); c.fill();
    c.strokeStyle = U.shade(pc, -0.4); c.lineWidth = 1.2;
    c.beginPath(); c.moveTo(x + 15, rim + 7); c.lineTo(x + 12, rim + 15); c.lineTo(x + 16, rim + 22); c.stroke();
    c.fillStyle = '#6b5440'; c.beginPath(); c.ellipse(x, rim + 3, 21, 4, 0, 0, TAU); c.fill();
    const f = Art.flower(c, { x, y: rim + 4, s: 0.52, kind: 'wild', droop: o.droop === undefined ? 0.58 : o.droop, dust: 1, colors: DUSTY_COL, stemH: 120, t, sway: o.sway === undefined ? 0.12 : o.sway, seed: 9, face: 0.65, petals: o.petals || 6 });
    c.strokeStyle = 'rgba(240,236,226,0.55)'; c.lineWidth = 0.8;
    const ax = x - 22, ay = rim + 1, bx = x - 2, by = rim - 40;
    for (let i = 0; i <= 4; i++) { const k = i / 4; c.beginPath(); c.moveTo(ax, ay); c.lineTo(lerp(ax, bx, 0.5 + k * 0.5), lerp(ay, by, k)); c.stroke(); }
    for (let r = 8; r < 34; r += 8) { c.beginPath(); c.arc(ax, ay, r, -1.4, -0.2); c.stroke(); }
    c.fillStyle = 'rgba(200,190,170,0.6)';
    for (let i = 0; i < 9; i++) c.fillRect(x - 18 + U.hash(i, 5) * 36, rim + 6 + U.hash(i, 6) * 26, 1.6, 1.6);
    if (o.tag !== false) {
      c.strokeStyle = '#8a7a60'; c.lineWidth = 1;
      c.beginPath(); c.moveTo(x - 20, rim + 2); c.quadraticCurveTo(x - 30, rim + 10, x - 30, rim + 16); c.stroke();
      c.save(); c.translate(x - 32, rim + 26); c.rotate(-0.16 + (o.tagSwing || 0));
      c.fillStyle = '#f1e6c8'; c.beginPath(); c.moveTo(-18, -10); c.lineTo(14, -10); c.lineTo(20, 0); c.lineTo(14, 10); c.lineTo(-18, 10); c.closePath(); c.fill();
      c.fillStyle = '#3b2a25'; c.beginPath(); c.arc(15, 0, 1.8, 0, TAU); c.fill();
      c.font = Art.font(10, 'hand', 700); c.textAlign = 'center'; c.textBaseline = 'middle';
      c.fillStyle = 'rgba(59,42,37,0.6)'; c.fillText('$4', -9, -4);
      c.strokeStyle = '#b8352a'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(-15, -3); c.lineTo(-3, -5); c.stroke();
      c.fillStyle = '#b8352a'; c.font = Art.font(13, 'hand', 700); c.fillText('$200', 0, 4);
      c.restore();
    }
    c.restore();
    return { x: x + (f.head.x - x) * s, y: y + (f.head.y - y) * s };
  }
  /** one fallen petal (pale, dusty), lying or tumbling */
  function petal(c, x, y, s, rot, flat) {
    c.save();
    c.translate(x, y);
    c.rotate(rot);
    c.scale(s, s * (flat ? 0.38 : 1));
    const col = U.mix('#e4d58a', '#b9ad98', 0.45);
    const g = c.createLinearGradient(0, 0, 0, -22);
    g.addColorStop(0, U.mix(col, '#a08a2a', 0.4)); g.addColorStop(1, col);
    c.fillStyle = g;
    c.beginPath(); c.moveTo(0, 0); c.bezierCurveTo(9, -5, 9, -18, 0, -22); c.bezierCurveTo(-9, -18, -9, -5, 0, 0); c.fill();
    c.restore();
  }

  /* ---------------- the SUV (side view, facing right) ---------------- */
  // local: origin = ground under the middle of the car. Tall, boxy, big wheels, high clearance.
  const WHX = [-246, 252], WR = 82, WY = -84;
  const BODY = [[-408, -80], [-416, -294], [-414, -328, -390, -338], [98, -338], [122, -336, 134, -324], [224, -216], [392, -206], [416, -202, 420, -182], [424, -96], [424, -70, 400, -68], [-392, -68], [-408, -68, -408, -80]];
  function bodyPath(g) {
    g.beginPath();
    g.moveTo(BODY[0][0], BODY[0][1]);
    for (let i = 1; i < BODY.length; i++) { const p = BODY[i]; if (p.length === 4) g.quadraticCurveTo(p[0], p[1], p[2], p[3]); else g.lineTo(p[0], p[1]); }
    g.closePath();
  }
  const HINGE = { x: -392, y: -337 };
  // the tailgate: a slab along the rear face that swings up and out about the roof hinge
  const GATE = [[-392, -338], [-410, -330], [-417, -298], [-418, -124], [-396, -124], [-394, -298], [-380, -330]];
  const GATE_OPEN = 2.05;   // radians (positive = up and out, away from the car)
  const rotAbout = (p, a) => { const dx = p[0] - HINGE.x, dy = p[1] - HINGE.y, ca = Math.cos(a), sa = Math.sin(a); return [HINGE.x + dx * ca - dy * sa, HINGE.y + dx * sa + dy * ca]; };
  function poly(g, pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath(); }
  function suv(g, t, o) {
    const L = o.shine, gate = o.gate || 0, bob = o.bob || 0;
    const paint = '#1b2130';
    g.fillStyle = 'rgba(12,14,22,0.42)';
    g.beginPath(); g.ellipse(0, 2, 440, 20, 0, 0, TAU); g.fill();
    if (L > 0.02) {
      g.fillStyle = U.rgba('#0c0e16', 0.22 * L);
      g.beginPath(); g.moveTo(-410, 0); g.lineTo(420, 0); g.lineTo(560, 36); g.lineTo(-280, 36); g.closePath(); g.fill();
    }
    // tyres sit still while the body bounces on its springs
    for (const wx of WHX) { g.fillStyle = '#121216'; g.beginPath(); g.arc(wx, WY, WR, 0, TAU); g.fill(); }
    g.save();
    g.translate(0, bob);
    bodyPath(g);
    const pg = g.createLinearGradient(0, -338, 0, -68);
    pg.addColorStop(0, U.mix(paint, '#8396b6', 0.36 + 0.14 * L)); pg.addColorStop(0.36, U.mix(paint, '#4a5a78', 0.32));
    pg.addColorStop(0.5, U.mix(paint, '#b3c3da', 0.24 * L + 0.08)); pg.addColorStop(0.53, paint);
    pg.addColorStop(0.84, U.mix(paint, '#000000', 0.25)); pg.addColorStop(1, U.mix(paint, '#6b5a4a', 0.25));
    g.fillStyle = pg; g.fill();
    g.save();
    bodyPath(g); g.clip();
    if (gate > 0.01) { g.fillStyle = '#0b0d12'; poly(g, GATE); g.fill(); }
    g.fillStyle = U.rgba('#dfe9f6', 0.26 + 0.42 * L);
    g.fillRect(-420, -170, 850, 3);
    g.fillStyle = U.rgba('#ffffff', 0.09 + 0.16 * L);
    for (const [x0, w] of [[-300, 70], [-150, 24], [60, 90], [250, 30]]) { g.beginPath(); g.moveTo(x0, -68); g.lineTo(x0 + w, -68); g.lineTo(x0 + w + 120, -340); g.lineTo(x0 + 120, -340); g.closePath(); g.fill(); }
    g.fillStyle = '#15171c'; g.fillRect(-430, -106, 870, 40);
    g.restore();
    // windows (tinted) + reflections
    const glass = (pts) => {
      poly(g, pts);
      const gg = g.createLinearGradient(0, -326, 0, -220);
      gg.addColorStop(0, U.mix('#2a3444', '#8ea6c4', 0.34 * L + 0.1)); gg.addColorStop(1, '#1e2531');
      g.fillStyle = gg; g.fill();
    };
    glass([[-394, -318], [-384, -326], [-266, -326], [-266, -220], [-398, -220]]);
    glass([[-242, -326], [-46, -326], [-46, -220], [-242, -220]]);
    glass([[-22, -326], [96, -326], [116, -320], [206, -222], [-22, -220]]);
    g.save();
    g.beginPath(); g.rect(-400, -328, 610, 110); g.clip();
    g.fillStyle = U.rgba('#ffffff', 0.07 + 0.22 * L);
    for (const x0 of [-340, -130, 60]) { g.beginPath(); g.moveTo(x0, -218); g.lineTo(x0 + 42, -218); g.lineTo(x0 + 112, -328); g.lineTo(x0 + 70, -328); g.closePath(); g.fill(); }
    g.restore();
    g.strokeStyle = U.mix('#9aa3ad', '#e8eef4', L); g.lineWidth = 3;
    g.beginPath(); g.moveTo(-400, -217); g.lineTo(210, -217); g.stroke();
    g.fillStyle = '#0d0f14'; g.fillRect(-266, -328, 24, 110); g.fillRect(-46, -328, 24, 110);
    // roof rails
    g.fillStyle = '#2a2f38'; g.fillRect(-360, -352, 430, 8); g.fillRect(-340, -346, 11, 9); g.fillRect(50, -346, 11, 9);
    g.fillStyle = U.rgba('#ffffff', 0.22 + 0.32 * L); g.fillRect(-360, -352, 430, 2);
    // door seams + handles + mirror
    g.strokeStyle = 'rgba(0,0,0,0.55)'; g.lineWidth = 2;
    for (const sx of [-254, -34, 212]) { g.beginPath(); g.moveTo(sx, -216); g.quadraticCurveTo(sx - 4, -140, sx + 4, -106); g.stroke(); }
    g.fillStyle = U.mix('#8d96a1', '#e6edf3', L);
    Art.roundRect(g, -150, -206, 36, 8, 3); g.fill();
    Art.roundRect(g, 86, -206, 36, 8, 3); g.fill();
    g.fillStyle = paint; g.beginPath(); g.ellipse(234, -232, 19, 13, -0.2, 0, TAU); g.fill();
    g.fillStyle = U.rgba('#ffffff', 0.14 + 0.3 * L); g.fillRect(224, -240, 14, 3);
    // front: lamp, grille, bumper; rear bumper
    g.fillStyle = '#fff6dc'; Art.roundRect(g, 398, -198, 26, 26, 6); g.fill();
    g.fillStyle = U.mix('#7d858f', '#d9e0e7', L); for (let i = 0; i < 3; i++) g.fillRect(410, -164 + i * 14, 16, 6);
    g.fillStyle = '#15171c'; Art.roundRect(g, 396, -118, 44, 52, 8); g.fill();
    g.fillStyle = '#15171c'; Art.roundRect(g, -432, -128, 44, 60, 8); g.fill();
    g.fillStyle = U.mix('#7d858f', '#d9e0e7', L); g.fillRect(-150, -66, 320, 7);
    // wheel arches (flared) + rims
    for (const wx of WHX) {
      g.fillStyle = '#0b0c10';
      g.beginPath(); g.arc(wx, WY + 6, 100, Math.PI, TAU); g.lineTo(wx + 100, -66); g.lineTo(wx - 100, -66); g.closePath(); g.fill();
      g.fillStyle = '#121216'; g.beginPath(); g.arc(wx, WY - bob, WR, 0, TAU); g.fill();
      const rg = g.createRadialGradient(wx - 14, WY - bob - 16, 4, wx, WY - bob, 54);
      rg.addColorStop(0, U.mix('#9aa1aa', '#f3f6f9', L)); rg.addColorStop(1, '#5c636c');
      g.fillStyle = rg; g.beginPath(); g.arc(wx, WY - bob, 53, 0, TAU); g.fill();
      g.strokeStyle = '#2b2f36'; g.lineWidth = 8;
      for (let i = 0; i < 5; i++) { const a = i / 5 * TAU + 0.3; g.beginPath(); g.moveTo(wx + Math.cos(a) * 13, WY - bob + Math.sin(a) * 13); g.lineTo(wx + Math.cos(a) * 50, WY - bob + Math.sin(a) * 50); g.stroke(); }
      g.fillStyle = '#2b2f36'; g.beginPath(); g.arc(wx, WY - bob, 14, 0, TAU); g.fill();
      g.fillStyle = U.mix('#9aa1aa', '#ffffff', L); g.beginPath(); g.arc(wx, WY - bob, 6, 0, TAU); g.fill();
    }
    // the tailgate (with its tall tail-light strip)
    const ga = gate * GATE_OPEN;
    g.save();
    g.translate(HINGE.x, HINGE.y); g.rotate(ga); g.translate(-HINGE.x, -HINGE.y);
    poly(g, GATE);
    g.fillStyle = U.mix(paint, '#4a5a78', 0.3 + 0.1 * Math.min(1, gate * 3)); g.fill();
    g.fillStyle = '#a81f1b'; g.fillRect(-418, -300, 10, 96);
    g.fillStyle = U.rgba('#ffd2c8', 0.55); g.fillRect(-416, -294, 4, 30);
    g.fillStyle = '#15171c'; g.fillRect(-418, -150, 22, 26);
    g.restore();
    // a glint on the roof rail: the promise
    const gl = o.glint || 0;
    if (gl > 0.01) {
      const gx = -300, gy = -352;
      Art.glow(g, gx, gy, 130, '#ffffff', 0.75 * gl);
      g.save(); g.globalAlpha *= gl; g.fillStyle = '#ffffff'; g.translate(gx, gy); g.rotate(0.2 + t * 0.6);
      g.beginPath(); g.moveTo(0, -50); g.lineTo(5, -5); g.lineTo(50, 0); g.lineTo(5, 5); g.lineTo(0, 50); g.lineTo(-5, 5); g.lineTo(-50, 0); g.lineTo(-5, -5); g.closePath(); g.fill(); g.restore();
    }
    g.restore();
  }
  /** a car-local point → coordinates in depth plane k (accounts for the body bounce) */
  function carToPlane(c, k, lx, ly, bob) {
    const sx = 960 + c.z * K_SUV * (SUV_X + lx - c.x), sy = 540 + c.z * (HY + K_SUV * (CAMH + ly + bob) - c.fy);
    return { x: c.x + (sx - 960) / (c.z * k), y: (sy - 540) / (c.z * k) - (HY - c.fy) / k - CAMH };
  }

  /* ---------------- the lot ---------------- */
  // background town + back-of-lot row
  const TOWN12 = TK.townStrip('town12', {
    seed: 1212, bottom: 980, ground: ['#a3b49a', '#93a88b'],
    tiers: [
      { x0: -900, x1: 3600, y: (x) => 640 - 16 * Math.sin(x * 0.002 + 0.9), wMin: 40, wMax: 66, hMin: 30, hMax: 52, gapMin: 16, gapMax: 80, treeK: 0.7 },
      { x0: -900, x1: 3600, y: (x) => 690 - 12 * Math.sin(x * 0.003 + 2.2), wMin: 56, wMax: 96, hMin: 40, hMax: 74, gapMin: 12, gapMax: 60, treeK: 0.9 },
    ],
  });
  const LOTROW12 = TK.townStrip('lotrow12', {
    seed: 3131, bottom: 60, ground: ['#9fb090'],
    walls: ['#efe0c4', '#e9c9a0', '#cfdde2', '#f0cfc0', '#e8dcc6', '#d6e2c4'],
    tiers: [{ x0: 500, x1: 4800, y: () => 0, wMin: 190, wMax: 300, hMin: 190, hMax: 300, gapMin: 40, gapMax: 160, treeK: 2.6 }],
  });
  function drawGround(ctx, c, t, P) {
    const yb = proj(c, K_BACK, 0).y, y1 = H + 10;
    // grass verge behind the lot
    const hz = proj(c, 0.4, 0).y;
    ctx.fillStyle = U.mix(P.grass, '#9db48c', 0.4);
    ctx.fillRect(0, hz, W, yb - hz + 2);
    // asphalt
    const ag = ctx.createLinearGradient(0, yb, 0, y1);
    ag.addColorStop(0, '#9a9590'); ag.addColorStop(1, '#6f6b68');
    ctx.fillStyle = ag;
    ctx.fillRect(0, yb, W, y1 - yb);
    // curb at the back
    ctx.fillStyle = '#c9c2b6'; ctx.fillRect(0, yb - 3, W, 7);
    // sidewalk in front of the shop and its neighbour (left part of the set)
    const s0 = proj(c, K_SHOP, 0), s1 = proj(c, 0.9, 0);
    const xr = proj(c, K_SHOP, 330).x, xr2 = proj(c, 0.9, 330).x;
    if (xr > -50) {
      ctx.fillStyle = '#d8d0c3';
      ctx.beginPath(); ctx.moveTo(-10, s0.y); ctx.lineTo(xr, s0.y); ctx.lineTo(xr2, s1.y); ctx.lineTo(-10, s1.y); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#b9b1a4'; ctx.fillRect(-10, s1.y, xr2 + 10, 4);
    }
    // stall lines (true one-point perspective), back row and front row
    ctx.fillStyle = 'rgba(250,248,240,0.82)';
    const line = (X, ka, kb) => {
      const a = proj(c, ka, X), b = proj(c, kb, X), wa = 2.4 * c.z * ka, wb = 2.4 * c.z * kb;
      if (Math.max(a.x, b.x) < -40 || Math.min(a.x, b.x) > W + 40) return;
      ctx.beginPath(); ctx.moveTo(a.x - wa, a.y); ctx.lineTo(a.x + wa, a.y); ctx.lineTo(b.x + wb, b.y); ctx.lineTo(b.x - wb, b.y); ctx.closePath(); ctx.fill();
    };
    for (let i = 0; i < 16; i++) { const X = 620 + i * 330; line(X, 0.6, 0.86); line(X, 1.16, 1.6); }
    const e0 = proj(c, 0.6, 620), e1 = proj(c, 0.6, 620 + 15 * 330);
    ctx.fillRect(e0.x, e0.y - 1.5, e1.x - e0.x, 3);
    // oil stains and cracks
    for (let i = 0; i < 14; i++) {
      const X = 700 + U.hash(i, 31) * 4200, k = 0.66 + U.hash(i, 32) * 0.5;
      const p = proj(c, k, X);
      if (p.x < -80 || p.x > W + 80) continue;
      ctx.fillStyle = 'rgba(40,38,40,0.16)';
      ctx.beginPath(); ctx.ellipse(p.x, p.y, (22 + U.hash(i, 33) * 26) * c.z * k, (5 + U.hash(i, 34) * 4) * c.z * k, 0, 0, TAU); ctx.fill();
    }
  }
  function frontCar(g, x, col, seed) {
    // a little car in the back row, seen nose-on (local: ground at 0)
    g.fillStyle = 'rgba(15,15,25,0.3)'; g.beginPath(); g.ellipse(x, 2, 104, 10, 0, 0, TAU); g.fill();
    g.fillStyle = '#16181d'; g.fillRect(x - 86, -34, 24, 34); g.fillRect(x + 62, -34, 24, 34);
    g.fillStyle = col; Art.roundRect(g, x - 98, -110, 196, 82, 20); g.fill();
    g.fillStyle = U.shade(col, -0.12); Art.roundRect(g, x - 76, -170, 152, 70, 22); g.fill();
    g.fillStyle = '#9fbfd3'; Art.roundRect(g, x - 64, -160, 128, 50, 12); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.3)'; g.beginPath(); g.moveTo(x - 50, -110); g.lineTo(x - 26, -110); g.lineTo(x + 6, -160); g.lineTo(x - 18, -160); g.closePath(); g.fill();
    g.fillStyle = '#fff4d6'; g.beginPath(); g.ellipse(x - 66, -80, 15, 11, 0, 0, TAU); g.ellipse(x + 66, -80, 15, 11, 0, 0, TAU); g.fill();
    g.fillStyle = U.shade(col, -0.35); Art.roundRect(g, x - 34, -72, 68, 20, 6); g.fill();
    g.fillStyle = '#e9e4da'; g.fillRect(x - 26, -46, 52, 12);
  }
  function hedgeRow(g, t, P) {
    // back of the lot (plane coords): hedge, trees, lamp posts
    for (let i = -2; i < 22; i++) {
      const X = i * 240 + U.hash(i, 41) * 60;
      const col = U.mix(P.trees[1], '#6f9a5c', 0.3);
      if (i % 2 === 0) Art.roundTree(g, X + 80, 0, 360 + U.hash(i, 42) * 120, U.shade(col, -0.05), { sway: U.wind(t, X, i) * 4, light: U.shade(col, 0.12), seed: i });
      Art.bush(g, X, 0, 70 + U.hash(i, 43) * 20, U.shade(col, -0.12), U.shade(col, 0.05), i);
    }
    for (let i = 0; i < 6; i++) TK.lamp(g, 900 + i * 900, 0, 1.25, {});
  }

  /* ---------------- characters ---------------- */
  // eye-style switches happen on a blink, so the change is never seen popping
  function eyesAt(t, keys) { let e = keys[0][1]; for (const [k, v] of keys) if (t >= k) e = v; return e; }
  function blinkAt(t, keys, seed) {
    let b = U.blink(t, seed);
    for (const [k] of keys) if (k > 0) b = Math.max(b, U.bump(t, k, 0.09));
    return b;
  }
  const FACE = {
    h1: { smile: [[0, 1], [5.5, 0.9], [8.5, 0.55], [11, 0.25], [13.6, 0.02], [16, -0.06], [24, -0.06]], eyes: [[0, 'sparkle'], [6.6, 'happy'], [9.2, 'open'], [14.0, 'distant']], open: [[0, 0.5], [3.5, 0.3], [6, 0], [24, 0]] },
    h2: { smile: [[0, 1], [4.5, 0.8], [8.2, 0.42], [10.8, 0.12], [13.2, -0.04], [24, -0.06]], eyes: [[0, 'happy'], [5.6, 'open'], [13.2, 'distant']], open: [[0, 0.55], [2.5, 0.25], [5, 0], [24, 0]] },
    h4: { smile: [[0, 1], [2.6, 0.95], [4.6, 0.5], [7.2, 0.18], [10.2, -0.02], [24, -0.06]], eyes: [[0, 'sparkle'], [3.9, 'open'], [10.6, 'distant']], open: [[0, 0.45], [2.4, 0.3], [3.6, 0], [24, 0]] },
  };
  const TIRED = [[0, 0], [8, 0.04], [11, 0.2], [14.5, 0.52], [17.3, 0.6], [24, 0.6]];
  const BOUNCE = [[0, 1], [3, 0.85], [6.5, 0.3], [9, 0], [24, 0]];
  function faceOf(who, t, extra) {
    const F = FACE[who];
    const eyes = eyesAt(t, F.eyes);
    return Object.assign({
      smile: TK.path(t, F.smile), open: Math.max(0, TK.path(t, F.open)), eyes,
      blink: Math.max(t > 21.2 ? 0 : blinkAt(t, F.eyes, who.charCodeAt(1) * 13), U.bump(t, 22.35, 0.1)),
      brow: t > 12 ? 0.25 * U.ease(t, 12, 15) : 0, browUp: t < 4 ? 0.5 : 0,
    }, extra || {});
  }
  // h1's two-handed hold on the pot: pot centre in body-local units (+x forward, up −)
  const HOLD = [[0, [62, -192]], [4, [60, -188]], [7.5, [56, -178]], [9.5, [50, -156]], [13.0, [44, -140]], [15.5, [38, -124]], [17.3, [38, -122]]];
  const holdAt = (t) => {
    let i = 0;
    while (i < HOLD.length - 2 && t > HOLD[i + 1][0]) i++;
    const [ta, a] = HOLD[i], [tb, b] = HOLD[i + 1];
    const k = U.E.inOutSine(clamp((t - ta) / (tb - ta)));
    return [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
  };

  const DROOP = [[0, 0.56], [6, 0.6], [10, 0.7], [11.2, 0.78], [14, 0.86], [17, 0.92], [24, 0.94]];
  const droopAt = (t) => TK.path(t, DROOP);
  /** pot bottom (plane coords) for h1 at time t (hands land exactly on the IK targets) */
  const potBottomAt = (t, X, S) => { const [lx, ly] = holdAt(t); return { x: X + lx * S, y: ly * S + 3 * S + 26 * S * 0.86 }; };
  /** where the flower's head is (mirrors Art.flower's geometry for the dusty pot) */
  const flowerHeadAt = (t, X, S) => {
    const p = potBottomAt(t, X, S), k = 0.86 * S, dr = droopAt(t);
    return { x: p.x + dr * 34 * 0.52 * k, y: p.y + (-34 - 62.4 * (1 - dr * 0.28)) * k };
  };

  /* ---------------- the scene ---------------- */
  Film.scene({
    id: 'fading-smiles',
    order: 12,
    title: 'The Parking Lot',
    duration: D,
    mood: 'parking',
    fadeIn: 0.8,
    fadeOut: 1.0,
    sfx: [
      [0.05, 'bell', { gain: 0.6 }], [0.25, 'laugh', { gain: 0.45 }], [0.7, 'footsteps', { gain: 0.4 }],
      [T.flash - 0.02, 'pop', { gain: 0.3 }], [3.55, 'sigh', { gain: 0.6 }], [T.glint, 'sparkle', { gain: 0.35 }],
      [T.petal1, 'petal', { gain: 0.7 }], [T.sweep[0], 'wind', { gain: 0.35 }],
      [T.hatchUp[0], 'tap', { gain: 0.35 }], [THUNK, 'car-door', { gain: 0.9 }], [THUNK + 0.35, 'petal', { gain: 0.35 }],
    ],
    post: (t) => ({ vignette: 0.3 + 0.12 * (1 - sunK(t)), grain: 0.045, letterbox: 1 }),

    render(ctx, t) {
      const ws = walk(t);
      const c = camAt(t, ws.d);
      const L = sunK(t);
      const P = U.mixDeep(P0, PGREY, 1 - L);

      /* ---- sky, sun, clouds ---- */
      const hz = 540 + c.z * (HY - c.fy);
      Art.sky(ctx, P, { horizon: hz + 120 });
      const sun = { x: 330, y: 238 };
      Art.sun(ctx, sun.x, sun.y, 40, P.sun, 0.35 + 0.6 * L);
      if (L > 0.02) Art.rays(ctx, { x: sun.x, y: sun.y, angle: 0.75, spread: 0.6, count: 7, len: 1900, color: P.light, alpha: 0.07 * L, t, seed: 12 });
      const cloudCol = U.mix('#ffffff', '#c3c8d0', 1 - L);
      Art.clouds(ctx, { seed: 21, count: 5, y0: 160, y1: 260, offset: t * 14 + (c.x - XREST) * 0.02, color: cloudCol, alpha: 0.75, scale: 0.6 });
      // THE cloud: slides in from the right and swallows the sun
      const cx = lerp(1640, sun.x + 40, U.ease(t, 7.5, 14.2, 'inOutSine')) - Math.max(0, t - 14.2) * 6;
      Art.cloud(ctx, cx, 232, 1.35, U.mix('#f4f5f7', '#b7bdc7', 1 - L), 0.96, 7, U.mix('#c9ced6', '#8f97a3', 1 - L));
      Art.cloud(ctx, cx + 210, 270, 0.9, U.mix('#eef0f3', '#b0b7c1', 1 - L), 0.9, 9, U.mix('#c4c9d1', '#8a929e', 1 - L));
      // overcast veil once the sun is gone
      if (L < 0.98) { ctx.fillStyle = U.rgba('#a9b1bd', 0.35 * (1 - L)); ctx.fillRect(0, 0, W, hz + 140); }

      /* ---- far layers ---- */
      ctx.save(); far(ctx, c, 0.03);
      TK.backdrop(ctx, P, { t, y: 500, sx: 1250, sh: 330, sw: 580, glow: 0.42 * L });
      ctx.restore();
      ctx.save(); far(ctx, c, 0.1);
      Art.ridge(ctx, { seed: 35, y: 668, amp: 64, freq: 0.0022, color: U.mix(P.trees[0], P.fog, 0.4), x0: -900, x1: W + 900, step: 14 });
      Art.forest(ctx, { seed: 45, y: 652, spacing: 38, hMin: 40, hMax: 76, color: U.mix(P.trees[0], P.fog, 0.36), light: U.mix(P.trees[0], P.light, 0.2) });
      ctx.restore();
      ctx.save(); far(ctx, c, 0.25);
      const fz = 1 + (c.z - 1) * 0.25, fxc = 960 + 0.25 * (c.x - XREST);
      TK.drawStrip(ctx, TOWN12, 'town12', { haze: [0.5, 0.32], hazeC: P0.fog, vx0: fxc - 980 / fz, vx1: fxc + 980 / fz });
      ctx.restore();
      // the row of houses facing the lot (behind the hedge)
      ctx.save(); plane(ctx, c, 0.42);
      TK.drawStrip(ctx, LOTROW12, 'lotrow12', { haze: [0.2], hazeC: P0.fog, vx0: c.x - 960 / (c.z * 0.42) - 200, vx1: c.x + 960 / (c.z * 0.42) + 200 });
      ctx.restore();

      /* ---- the lot ---- */
      drawGround(ctx, c, t, P);
      ctx.save(); plane(ctx, c, K_BACK); hedgeRow(ctx, t, P); ctx.restore();
      ctx.save(); plane(ctx, c, K_CARS);
      frontCar(ctx, 1170, '#7d97b5', 1); frontCar(ctx, 2160, '#c9b27a', 2); frontCar(ctx, 3810, '#9c6d6d', 3);
      ctx.restore();

      /* ---- the shop, its neighbour, Embarrassment in the doorway ---- */
      const shopVis = proj(c, K_SHOP, 700).x > -50;
      if (shopVis) {
        ctx.save(); plane(ctx, c, K_SHOP);
        // neighbour (pale blue, red door, bicycle) — as in scene 10
        ctx.fillStyle = '#bcd2de'; ctx.fillRect(-668, -940, 368, 940);
        ctx.fillStyle = '#f3ead9'; ctx.fillRect(-676, -952, 384, 16);
        for (const wx of [-588, -398]) { ctx.fillStyle = '#f3ead9'; ctx.fillRect(wx - 48, -860, 96, 150); ctx.fillStyle = '#5f7389'; ctx.fillRect(wx - 40, -852, 80, 134); }
        ctx.fillStyle = '#f3ead9'; ctx.fillRect(-448, -430, 104, 430); ctx.fillStyle = '#a33d3a'; Art.roundRect(ctx, -438, -420, 84, 420, 4); ctx.fill();
        // the P sign at the lot entrance and a lamp
        ctx.fillStyle = '#5e6a70'; ctx.fillRect(452, -330, 9, 330);
        ctx.fillStyle = '#2f6fb3'; Art.roundRect(ctx, 414, -410, 86, 86, 9); ctx.fill();
        ctx.save(); ctx.font = Art.font(66, 'sans', 900); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#ffffff'; ctx.fillText('P', 457, -366); ctx.restore();
        TK.lamp(ctx, 640, 0, 1.1, {});
        // door: thrown open by the hikers, swings back, Embarrassment catches it
        const swing = t < T.emb[0] ? 0.82 + 0.18 * Math.cos(t * 7) * Math.exp(-t * 2.2) : lerp(0.86, 1, U.ease(t, T.emb[0], T.emb[1]));
        const shake = U.fade(t, 1.6, 5.4, 0.4, 0.9);
        const step = U.ease(t, T.emb[0], T.emb[1], 'outCubic');
        TK.shopfront(ctx, 0, 0, SHOP_S, t, {
          doorOpen: swing, bell: 0.5, bellT: 0, lit: 0.3 * L,
          between: (g) => {
            if (step <= 0) return;
            g.save();
            g.beginPath(); g.rect(DOOR.x0 - 8, DOOR.top - 60, DOOR.x1 - DOOR.x0 + 16, -DOOR.top + 70); g.clip();
            const ph = (t - 1.6) * 5.6;
            Art.person(g, {
              x: lerp(DOOR.x1 + 60, 176, step), y: -8, s: 1, look: 'emb', t, facing: 1,
              lean: -0.04, gesture: 'hips', gw: 0.75,
              head: { tilt: Math.sin(ph) * 0.1 * shake + 0.04, turn: 0.45 + Math.sin(ph) * 0.4 * shake },
              face: { eyes: 'flat', smile: -0.12, brow: 0.35, mouth: t > 3.5 && t < 3.9 ? 'o' : undefined, open: t > 3.5 && t < 3.9 ? 0.4 : 0 },
              alpha: 0.4 + 0.6 * step,
            });
            // a little sigh puff
            const sp = U.prog(t, 3.55, 4.6);
            if (sp > 0 && sp < 1) for (let i = 0; i < 3; i++) { g.fillStyle = U.rgba('#ffffff', 0.55 * (1 - sp)); g.beginPath(); g.arc(214 + sp * 50 + i * 12, -300 - sp * 30 - i * 6, (6 + i * 3) * (0.6 + sp), 0, TAU); g.fill(); }
            g.restore();
          },
        });
        ctx.restore();
      }

      /* ---- the SUV ---- */
      const gate = U.ease(t, T.hatchUp[0], T.hatchUp[1], 'inOutSine') * (1 - U.ease(t, T.slam[0], T.slam[1], 'inQuad'));
      const bt = t - THUNK;
      const bob = bt > 0 ? 7 * Math.exp(-bt * 4.5) * Math.sin(bt * 21) : 0;
      const glint = U.bump(t, T.glint + 0.3, 0.5) * L;
      ctx.save(); plane(ctx, c, K_SUV);
      ctx.translate(SUV_X, 0);
      suv(ctx, t, { shine: L, gate, bob, glint });
      ctx.restore();

      /* ---- the hikers (back to front) ---- */
      const order = CAST.slice().sort((a, b) => K1[a] - K1[b]);
      const tired = TK.path(t, TIRED), bounce = Math.max(0, TK.path(t, BOUNCE));
      const turn = U.ease(t, T.turn[0], T.turn[1], 'inOutSine');
      const glance = U.fade(t, T.petal1 + 0.15, T.petal1 + 1.6, 0.25, 0.4);
      for (const who of order) {
        const k = lerp(K0[who], K1[who], U.ease(t, 0, 2.6, 'inOutSine'));
        const X = X0[who] + ws.d;
        const look = Art.CAST[who];
        const S = SCALE[who] * look.height;
        const o = {
          x: X, y: 0, s: SCALE[who], look: who, t, facing: 1, poles: false,
          walk: ws.ph[who], stride: ws.stride, tired, bounce: bounce * (who === 'h1' ? 0.8 : 1),
          head: { tilt: (t < 5 ? -0.06 : 0) + (who === 'h2' ? 0.16 * glance : 0), turn: turn * 0.85 },
          face: faceOf(who, t, who === 'h2' && glance > 0.3 ? { lookX: -0.3, lookY: 0.9, brow: 0.5 } : null),
        };
        ctx.save(); plane(ctx, c, k);
        // the long sunny cast shadow (shrinks to nothing under the cloud)
        if (L > 0.02) { ctx.fillStyle = U.rgba('#0c0e16', 0.2 * L); ctx.beginPath(); ctx.ellipse(X + 58 * S, 6, 74 * S, 9 * S, 0.04, 0, TAU); ctx.fill(); }
        if (who === 'h2') {
          const ch = U.fade(t, 0, 1.6, 0.01, 0.6);
          if (ch > 0.01) { o.gesture = 'cheer'; o.gw = ch * 0.9; }
        }
        if (who === 'h4') {
          const selfie = U.fade(t, 0.9, 2.7, 0.35, 0.45), look2 = U.fade(t, 2.8, 8.9, 0.4, 0.5);
          const glowS = U.bump(t, T.flash, 0.12);
          if (selfie > 0.01) { o.gesture = 'phone'; o.gw = selfie; o.face.lookX = -0.4; }
          else if (look2 > 0.01) { o.gesture = 'phoneLook'; o.gw = look2; o.face.lookY = 0.9 * look2; o.head.tilt += 0.12 * look2; }
          o.holdF = TK.phone ? TK.phone(selfie > 0.01 ? 0.6 + glowS : look2 > 0.01 ? 0.55 : 0, { rot: selfie > 0.01 ? 0.3 : -0.3 }) : undefined;
        }
        if (who === 'h1') {
          // the pot rides out in front in both hands, sinking as the walk goes on…
          let pot = potBottomAt(t, X, S);
          const loadK = U.ease(t, T.load[0], T.load[1], 'inOutSine');
          if (loadK > 0) {
            // …and is slid into the trunk
            const tgt = carToPlane(c, k, -360, -128, 0);
            pot = { x: lerp(pot.x, tgt.x, loadK), y: lerp(pot.y, tgt.y, loadK) };
            o.lean = 0.22 * U.fade(t, T.load[0], T.load[1] + 0.3, 0.4, 0.3);
          }
          const grip = { x: pot.x + 1 * S, y: pot.y - 26 * S * 0.86 - 3 * S };
          o.reachF = { x: grip.x + 13 * S, y: grip.y + 4 * S };
          o.reachB = { x: grip.x - 15 * S, y: grip.y + 2 * S };
          if (t > T.load[1]) {
            // reach up for the tailgate's edge, follow it down on the slam, let the arm drop
            const ga = gate * GATE_OPEN;
            const edge = rotAbout([-407, -126], ga);
            const e = carToPlane(c, k, edge[0], edge[1], bob);
            const rest = { x: X + 16 * S, y: -112 * S };
            const up = U.ease(t, T.reach[0], T.reach[1], 'inOutSine') * (1 - U.ease(t, THUNK + 0.2, THUNK + 0.85, 'inOutSine'));
            o.reachF = { x: lerp(rest.x, e.x, up), y: lerp(rest.y, e.y, up) };
            o.reachB = { x: X - 10 * S, y: -112 * S };
            o.lean = 0.08 * up;
          }
          const A = Art.person(ctx, o);
          if (t < T.load[1]) {
            const inK = U.prog(t, T.load[0] + 0.35, T.load[1]);
            ctx.save();
            if (inK > 0) {
              const xr = carToPlane(c, k, -414, 0, 0).x;
              ctx.beginPath(); ctx.rect(xr - 4000, -3000, 4000, 4000); ctx.clip();
            }
            dusty(ctx, pot.x, pot.y, 0.86 * S, t, { droop: droopAt(t) + 0.1 * U.bump(t, T.petal1 + 0.05, 0.22), petals: t < T.petal1 ? 6 : 5, sway: 0.12 + U.bump(t, T.petal1 + 0.08, 0.3) * 3, tagSwing: Math.sin(t * 6) * 0.15 * bounce });
            ctx.restore();
            ctx.fillStyle = look.skin;
            for (const h of [A.handF, A.handB]) { ctx.beginPath(); ctx.arc(h.x, h.y, 7.5 * S, 0, TAU); ctx.fill(); }
          }
        } else {
          Art.person(ctx, o);
        }
        if (who === 'h4') { const fl = U.bump(t, T.flash, 0.12); if (fl > 0.01) Art.glow(ctx, X + 60 * S, -330 * S, 260, '#ffffff', fl); }
        ctx.restore();
      }

      /* ---- petals ---- */
      // 1: drops off the sinking trophy and is left behind on the asphalt
      if (t > T.petal1) {
        const S1 = Art.CAST.h1.height, X1 = X0.h1 + walk(T.petal1).d;
        const p0 = flowerHeadAt(T.petal1, X1, S1);
        const f = U.prog(t, T.petal1, T.petal1 + 2.2);
        const fx = p0.x - 34 * f + Math.sin(f * 9) * 14 * (1 - f), fy = lerp(p0.y, -2, U.E.inQuad(f) * 0.6 + f * 0.4);
        ctx.save(); plane(ctx, c, K1.h1);
        petal(ctx, fx, fy, 1.45, f < 1 ? Math.sin(f * 11) * 1.2 + f * 3 : 1.3, f >= 1);
        ctx.restore();
      }
      // 2: shaken loose by the slam, out of the tailgate seam
      if (t > THUNK + 0.05) {
        const f = U.prog(t, THUNK + 0.05, THUNK + 2.4);
        const fx = SUV_X - 424 - 76 * f + Math.sin(f * 8) * 18 * (1 - f), fy = lerp(-214, -2, U.E.inQuad(f) * 0.5 + f * 0.5);
        ctx.save(); plane(ctx, c, K_SUV);
        petal(ctx, fx, fy, 1.45, f < 1 ? Math.sin(f * 10) * 1.3 - f * 2 : -0.4, f >= 1);
        ctx.restore();
      }

      /* ---- a gust ahead of the cloud: a few leaves skitter across ---- */
      if (t > T.sweep[0] - 0.4 && t < T.sweep[1] + 1.2) {
        ctx.save(); plane(ctx, c, 1.08);
        for (let i = 0; i < 5; i++) {
          const t0 = T.sweep[0] - 0.4 + i * 0.32, f = (t - t0) / 1.9;
          if (f < 0 || f > 1) continue;
          const lx = c.x + 1150 - f * 2300 + i * 40, ly = -8 - Math.abs(Math.sin(f * 9 + i)) * (30 + i * 9);
          ctx.save(); ctx.translate(lx, ly); ctx.rotate(f * 14 + i); ctx.scale(1, 0.55 + 0.45 * Math.abs(Math.cos(f * 11 + i)));
          ctx.fillStyle = ['#9a8d52', '#7f8f4f', '#a8874e', '#8a9a5c', '#b0985a'][i];
          ctx.beginPath(); ctx.ellipse(0, 0, 12, 6, 0, 0, TAU); ctx.fill();
          ctx.restore();
        }
        ctx.restore();
      }

      /* ---- the cloud's shadow sweeps across, colour drains ---- */
      const sw = U.prog(t, T.sweep[0] - 0.2, T.sweep[1]);
      if (sw > 0) {
        const ex = lerp(W + 500, -700, U.E.inOutSine(sw));
        const sg = ctx.createLinearGradient(ex - 260, 0, ex + 260, 0);
        sg.addColorStop(0, 'rgba(24,28,40,0)'); sg.addColorStop(1, 'rgba(24,28,40,0.2)');
        ctx.fillStyle = sg; ctx.fillRect(ex - 260, 0, 520, H);
        ctx.fillStyle = 'rgba(24,28,40,0.2)'; ctx.fillRect(ex + 260, 0, Math.max(0, W - ex - 260), H);
      }
      Art.desaturate(ctx, 0.62 * (1 - L));
      // the selfie flash pops the whole frame for a blink
      const fl = U.bump(t, T.flash, 0.08);
      if (fl > 0.01) { ctx.fillStyle = U.rgba('#ffffff', 0.22 * fl); ctx.fillRect(0, 0, W, H); }

      Art.captions(ctx, t, NARR);
    },
  });
})();
