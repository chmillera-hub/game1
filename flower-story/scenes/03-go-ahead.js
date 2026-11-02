/* ==========================================================================
   03 · Go On Ahead — medium-wide, colour and time restored. "me" stands by
   the flower; the group has stopped a few steps up-trail and stares back.
   He waves them on. They look at him like he's nuts, shrug in perfect sync,
   about-face and march off toward the summit. He sits down beside the
   flower, content. Birdsong returns; a little bird lands on the mossy rock.
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU } = U;
  const D = 26;
  const P = U.mixDeep(Art.TOD.morning, Art.TOD.golden, 0.3);
  const CX = W / 2, CY = H / 2;

  /* ---------------- set (medium-wide on the same trail) ---------------- */
  const S = 1.45;                       // character scale (the wide walking shot was 0.8)
  const GY = 836, GAMP = 10, OFF = 5230;  // ground line; OFF picks a gentle stretch of trail
  const FOOT = 33;                      // feet stand this far below the ground line, on the trail
  const TRAIL_D = 82;                   // the trail band, scaled up with the shot
  const gOpt = { y: GY, amp: GAMP, offset: OFF };
  const gy = (x) => Art.groundY(x, gOpt);
  // walk: foot travel per radian of phase per unit scale at stride k (measured from the kit's rig)
  const KFk = (k) => 72.32 * Math.sin(0.42 * k);

  const ME = { x: 352 };
  const FL = { x: 566, y: 934, s: 1.05 };           // the flower: just in front of the trail
  const ROCK = { x: 662, y: 929, w: 122, h: 76 };   // mossy rock behind/right of it
  const FERN = { x: 478, y: 938, s: 1.1 };          // fern to its left
  const CREW = [                                     // stopped a few steps up-trail, turned back toward him
    { k: 'h4', x: 1078, dy: 10, ds: 1.02 },          // dy/ds: a little depth so they aren't a police lineup
    { k: 'h3', x: 1266, dy: -12, ds: 0.97 },
    { k: 'h2', x: 1478, dy: 5, ds: 1.0 },
    { k: 'h1', x: 1706, dy: -7, ds: 0.985 },
  ];

  /* ---------------- beats ---------------- */
  const BUB = [
    [2.0, 4.85, 'Hey, you guys go ahead.', { who: 'me', x: 652, y: 338, size: 38 }],
    [6.6, 9.4, 'I’m good right here.', { who: 'me', x: 628, y: 338, size: 38 }],
  ];
  const CAPS = [
    [4.5, 7.0, 'I tell the group.'],
    [9.8, 12.8, 'They look at me like I’m nuts,'],
    [13.15, 16.15, 'but they shrug and keep walking.'],
  ];
  const T_ANT = 12.95, T_SHRUG = 13.25, T_HOLD = 13.55, T_SETTLE = 14.25, T_DOWN = 14.6;
  const T_TURN = 14.72, T_TURN1 = 14.98;              // synchronised about-face
  const T_GO = 15.05;                                  // ...and off they march
  // sitting down beside the flower, one continuous move: knees dip, hips sink back and down, seat lands,
  // feet slide forward into a knees-up sit, hands come to rest on the knees
  const SIT_A = 18.45, SIT_D0 = 18.7, SIT_LAND = 19.45, SIT_F0 = 19.1, SIT_F1 = 19.8;

  /* ---------------- helpers ---------------- */
  // cached soft background: the shot is locked off, so far layers are painted once at low res
  const BG_F = 2.4, OX = 80, OY = 50;   // painted at 1/2.4 res with an overscan margin
  let bgCache = null;
  function background() {
    const c = Art.canvas('a2:bg03', Math.ceil((W + 2 * OX) / BG_F), Math.ceil((H + 2 * OY) / BG_F));
    if (bgCache === c) return c;
    const x = c.getContext('2d');
    x.setTransform(1 / BG_F, 0, 0, 1 / BG_F, OX / BG_F, OY / BG_F);
    Art.sky(x, P, { horizon: 700 });
    Art.glow(x, 1880, 40, 620, P.sun, 0.38, 'screen');
    // hand-placed clouds, kept clear of the summit
    Art.cloud(x, 250, 222, 1.0, '#ffffff', 0.62, 3);
    Art.cloud(x, 760, 186, 0.78, '#ffffff', 0.58, 8);
    Art.cloud(x, 1130, 292, 0.48, '#ffffff', 0.5, 12);
    Art.ridge(x, { seed: 21, y: 600, amp: 150, color: U.mix(P.far, P.sky[1], 0.4), offset: 210 });
    Art.summit(x, { x: 1530, y: 640, h: 410, w: 660, P, glow: 0, t: 0, flag: true });
    Art.fog(x, { y: 640, h: 170, color: P.fog, alpha: 0.5 });
    Art.ridge(x, { seed: 8, y: 700, amp: 96, color: P.mid, offset: 520 });
    Art.forest(x, { seed: 41, y: 752, offset: 900, spacing: 54, hMin: 110, hMax: 190, color: P.trees[0], light: U.shade(P.trees[0], 0.1) });
    Art.fog(x, { y: 760, h: 120, color: P.fog, alpha: 0.3 });
    Art.forest(x, { seed: 42, y: 806, offset: 1700, spacing: 92, hMin: 220, hMax: 330, color: P.trees[1], light: U.shade(P.trees[1], 0.12), kind: 'mix' });
    Art.fog(x, { y: 812, h: 80, color: P.fog, alpha: 0.16 });
    Art.forest(x, { seed: 43, y: 846, offset: 2600, spacing: 250, hMin: 430, hMax: 560, color: U.mix(P.trees[2], P.trees[1], 0.3), light: U.shade(P.trees[1], 0.04), kind: 'pine', jitterY: 6 });
    bgCache = c;
    return c;
  }
  function rockPath(ctx, x, y, w, h, seed) {
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.quadraticCurveTo(x - w * 0.5, y - h * 0.8, x - w * 0.15 + U.hash(seed, 1) * 8, y - h);
    ctx.quadraticCurveTo(x + w * 0.35, y - h * 1.02, x + w / 2, y - h * 0.2);
    ctx.lineTo(x + w / 2, y);
    ctx.closePath();
  }
  function mossyRock(ctx, x, y, w, h, moss, seed) {
    Art.rock(ctx, x, y, w, h, '#8a8f86', seed);
    ctx.save();
    rockPath(ctx, x, y, w, h, seed);
    ctx.clip();
    ctx.fillStyle = moss;
    ctx.beginPath();
    ctx.moveTo(x - w * 0.6, y - h * 1.2);
    ctx.lineTo(x + w * 0.6, y - h * 1.2);
    for (let i = 0; i <= 10; i++) {
      const k = 1 - i / 10;
      ctx.lineTo(x - w * 0.6 + w * 1.2 * k, y - h * (0.62 + 0.18 * Math.sin(k * 3.1)) + Math.sin(i * 2.3 + seed) * h * 0.06);
    }
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = U.shade(moss, 0.16);
    for (let i = 0; i < 6; i++) {
      const px = x - w * 0.28 + U.hash(i, seed + 5) * w * 0.55, py = y - h * (0.78 + U.hash(i, seed + 6) * 0.16);
      ctx.beginPath(); ctx.ellipse(px, py, w * 0.07, h * 0.05, 0, 0, TAU); ctx.fill();
    }
    ctx.fillStyle = 'rgba(20,24,18,0.22)';
    ctx.fillRect(x - w, y - h * 0.18, w * 2, h * 0.3);
    ctx.restore();
  }
  const phone = (c) => {
    c.save();
    c.rotate(-0.15);
    c.fillStyle = '#23262e';
    Art.roundRect(c, -3, -24, 7, 26, 2.5); c.fill();
    c.fillStyle = '#9fd8ff';
    c.fillRect(-3.4, -22, 1.6, 22);
    c.restore();
  };
  // "turning around" in a side-view rig: a quick card-flip about the feet, face toward camera mid-turn
  function personFlip(ctx, o, k, from, to, after) {
    const facing = k < 0.5 ? from : to;
    const sx = k <= 0 || k >= 1 ? 1 : 0.36 + 0.64 * Math.abs(Math.cos(k * Math.PI));
    const hop = k <= 0 || k >= 1 ? 0 : Math.sin(k * Math.PI) * 9 * (o.s || 1);   // a little hop on the spot
    ctx.save();
    ctx.translate(o.x, -hop); ctx.scale(sx, 1); ctx.translate(-o.x, 0);
    const head = Object.assign({}, o.head || {}, { turn: Math.max((o.head && o.head.turn) || 0, k > 0 && k < 1 ? Math.sin(k * Math.PI) : 0) });
    const a = Art.person(ctx, Object.assign({}, o, { facing, head }));
    if (after) after(ctx, a, facing);
    ctx.restore();
  }
  // h1's trekking poles when he isn't walking (the kit only draws them in the walk pose): held in
  // the front hand, rigid, tips toward the ground ahead — the same geometry the kit uses mid-stride
  function heldPoles(ctx, a, facing, look) {
    const S = a.scale, L = 132 * S;
    const gx = a.handF.x, gy0 = a.handF.y - 10 * S;
    const dx = 26 * S * facing, dy = a.feet.y - gy0;
    const n = Math.hypot(dx, dy) || 1;
    ctx.strokeStyle = '#c8ccd2'; ctx.lineWidth = 3.2 * S; ctx.lineCap = 'round';
    for (const sp of [-0.035, 0.035]) {
      const c = Math.cos(sp), si = Math.sin(sp);
      const ux = (dx * c - dy * si) / n, uy = (dx * si + dy * c) / n;
      ctx.beginPath(); ctx.moveTo(gx, gy0); ctx.lineTo(gx + ux * L, gy0 + uy * L); ctx.stroke();
    }
    ctx.fillStyle = look.skin;                               // the hand closes over the grips
    ctx.beginPath(); ctx.arc(a.handF.x, a.handF.y, 7.5 * S, 0, TAU); ctx.fill();
  }
  // a little songbird; (x,y) = feet, dir 1 faces right. wing: radians of wing lift; chirp 0..1
  function songbird(ctx, x, y, s, dir, o = {}) {
    const wing = o.wing || 0, perched = o.perched !== false;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s * dir, s);
    ctx.rotate(o.tilt || 0);
    const back = '#7b5b45', belly = '#ecd2ab', dark = '#3b2a22';
    if (perched) {
      ctx.strokeStyle = dark; ctx.lineWidth = 1.6; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(-1, -7); ctx.lineTo(-2, 0); ctx.moveTo(2, -7); ctx.lineTo(3, 0); ctx.stroke();
    }
    ctx.fillStyle = U.shade(back, -0.1);           // tail
    ctx.beginPath(); ctx.moveTo(-7, -12); ctx.lineTo(-19, -17 + (o.tailUp || 0)); ctx.lineTo(-17, -11); ctx.closePath(); ctx.fill();
    ctx.fillStyle = back;                           // body
    ctx.beginPath(); ctx.ellipse(0, -12, 10.5, 7.2, -0.2, 0, TAU); ctx.fill();
    ctx.fillStyle = belly;
    ctx.beginPath(); ctx.ellipse(2.5, -9.5, 7.2, 4.4, -0.15, 0, TAU); ctx.fill();
    ctx.fillStyle = back;                           // head
    ctx.beginPath(); ctx.arc(8.5, -18, 5.6, 0, TAU); ctx.fill();
    ctx.fillStyle = '#e7a23f';                      // beak (open when it sings)
    const ch = (o.chirp || 0) * 2.2;
    ctx.beginPath(); ctx.moveTo(13.4, -19.2); ctx.lineTo(18.6, -18 - ch * 0.5); ctx.lineTo(13.6, -17.2); ctx.closePath(); ctx.fill();
    if (ch > 0.2) { ctx.beginPath(); ctx.moveTo(13.6, -17.6); ctx.lineTo(18, -16.4 + ch * 0.6); ctx.lineTo(13.4, -16.4); ctx.closePath(); ctx.fill(); }
    ctx.fillStyle = dark;
    ctx.beginPath(); ctx.arc(10.3, -19, 1.25, 0, TAU); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.beginPath(); ctx.arc(10.7, -19.5, 0.45, 0, TAU); ctx.fill();
    ctx.save();                                     // wing
    ctx.translate(-1, -14);
    ctx.rotate(-wing);
    ctx.fillStyle = U.shade(back, -0.18);
    ctx.beginPath(); ctx.moveTo(2, 0); ctx.quadraticCurveTo(-6, -5, -15, 1); ctx.quadraticCurveTo(-6, 4, 2, 0); ctx.fill();
    ctx.restore();
    ctx.restore();
  }
  // distant bird: a soft 'm' stroke
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
  // Setting off: speed and stride ramp up together over RAMP s. Returns ∫ramp (phase units) and
  // ∫KF(stride)·ramp (distance per unit scale per unit rate), so planted feet never slide.
  const RAMP = 0.6;
  const rampAt = (u) => U.smooth((u - T_GO) / RAMP);
  const RAMP_DIST = (() => { let a = 0; const n = 240; for (let i = 0; i < n; i++) { const u = T_GO + ((i + 0.5) / n) * RAMP; const r = rampAt(u); a += KFk(r) * r * (RAMP / n); } return a; })();
  function setOff(t) {
    if (t <= T_GO) return { ph: 0, dist: 0, stride: 0 };
    const d = t - T_GO;
    if (d >= RAMP) return { ph: RAMP / 2 + (d - RAMP), dist: RAMP_DIST + KFk(1) * (d - RAMP), stride: 1 };
    const x = d / RAMP;
    let dist = 0; const n = Math.max(4, Math.ceil(d * 200));
    for (let i = 0; i < n; i++) { const u = T_GO + ((i + 0.5) / n) * d; const r = rampAt(u); dist += KFk(r) * r * (d / n); }
    return { ph: RAMP * (x * x * x - (x * x * x * x) / 2), dist, stride: rampAt(t) };
  }
  // Art.rays, but SCREENED: added warm light clips to cyan on a bright blue sky
  function raysScreen(ctx, { x, y, angle, spread, count, len, color, alpha, t, seed, width = 0.05 }) {
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    for (let i = 0; i < count; i++) {
      const a = angle + (U.hash(i, seed) - 0.5) * spread;
      const wdt = width * (0.5 + U.hash(i, seed + 1));
      const flick = 0.55 + 0.45 * Math.sin(t * (0.3 + U.hash(i, seed + 2) * 0.5) + i * 2.1);
      const gr = ctx.createLinearGradient(x, y, x + Math.cos(a) * len, y + Math.sin(a) * len);
      gr.addColorStop(0, U.rgba(color, alpha * flick));
      gr.addColorStop(0.6, U.rgba(color, alpha * flick * 0.35));
      gr.addColorStop(1, U.rgba(color, 0));
      ctx.fillStyle = gr;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + Math.cos(a - wdt) * len, y + Math.sin(a - wdt) * len);
      ctx.lineTo(x + Math.cos(a + wdt) * len, y + Math.sin(a + wdt) * len);
      ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }
  // shoulder (front) in body-local units for the kit's walk pose (replicates Art.person's torso maths)
  function shoulderF(ph, stride, seed, t) {
    const hipY = -(58 + 56 + 4) + Math.abs(Math.sin(ph)) * 5 * stride - 3 * stride, lean = 0.06 * stride;
    const top = 88 + Math.sin(t * 1.7 + seed) * 1.3 * 0.3;
    return { x: Math.sin(lean) * top + 3, y: hipY - Math.cos(lean) * top + 7 };
  }
  const handAt = (sh, a) => ({ x: sh.x + 50 * Math.sin(a[0]) + 47 * Math.sin(a[0] + a[1]), y: sh.y + 50 * Math.cos(a[0]) + 47 * Math.cos(a[0] + a[1]) });
  // me's body for the sit-down: Art.person's rig and drawing order, but the legs are placed by IK from a
  // hip to two feet (all body-local units, facing right), so the pose moves continuously instead of popping
  // between the kit's discrete 'stand' / 'crouch' / 'sit' poses. o: x, y, s, t, legs {hx, hy, fF, fB},
  // lean, head, face, armF/armB (angles) or handF/handB (local IK targets), shadowX, shadowW.
  const SK = { thigh: 58, shin: 56, torso: 88, neck: 12, headR: 36, upper: 50, fore: 47, hipW: 22, shW: 27 };
  const ME_SEED = 'm'.charCodeAt(0) * 7;   // the kit's default seed for 'me'
  const limbL = (ox, oy, a1, l1, rel, l2) => {
    const x1 = ox + Math.sin(a1) * l1, y1 = oy + Math.cos(a1) * l1, a2 = a1 + rel;
    return { x0: ox, y0: oy, x1, y1, x2: x1 + Math.sin(a2) * l2, y2: y1 + Math.cos(a2) * l2, a1, a2 };
  };
  function strokeL(ctx, L, w1, w2, col) {
    ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.lineWidth = w1; ctx.beginPath(); ctx.moveTo(L.x0, L.y0); ctx.lineTo(L.x1, L.y1); ctx.stroke();
    ctx.lineWidth = w2; ctx.beginPath(); ctx.moveTo(L.x1, L.y1); ctx.lineTo(L.x2, L.y2); ctx.stroke();
  }
  function shoeL(ctx, L, col) {
    ctx.save(); ctx.translate(L.x2, L.y2); ctx.rotate(U.clamp(L.a2 * -0.25, -0.5, 0.5));
    ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(7, -2, 15, 7.5, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = U.shade(col, -0.3); ctx.fillRect(-7, 2.5, 28, 3);
    ctx.restore();
  }
  function meRig(ctx, o) {
    const look = Art.CAST.me, S = o.s, t = o.t, seed = ME_SEED;
    const head = Object.assign({ tilt: 0, turn: 0 }, o.head || {});
    const lean = o.lean || 0, L = o.legs;
    const leg = (ox, f) => { const a = Art.ik2(ox, L.hy, f.x, f.y, SK.thigh, SK.shin, 1); return limbL(ox, L.hy, a[0], SK.thigh, a[1], SK.shin); };
    const legF = leg(L.hx + 4, L.fF), legB = leg(L.hx - 4, L.fB);
    const hipX = L.hx, hipY = L.hy;
    const top = SK.torso + Math.sin(t * 1.7 + seed) * 1.3 * 0.3;
    const shX = hipX + Math.sin(lean) * top, shY = hipY - Math.cos(lean) * top;
    const hTilt = head.tilt || 0, neck = SK.neck + SK.headR;
    const hdx = shX + Math.sin(lean + hTilt * 0.6) * neck + 4, hdy = shY - Math.cos(lean + hTilt * 0.6) * neck;
    const shF = { x: shX + 3, y: shY + 7 }, shB = { x: shX - 6, y: shY + 8 };
    let aF = o.armF || [0.1, 0.18], aB = o.armB || [-0.08, 0.14];
    if (o.handF) aF = Art.ik2(shF.x, shF.y, o.handF.x, o.handF.y, SK.upper, SK.fore, -1);
    if (o.handB) aB = Art.ik2(shB.x, shB.y, o.handB.x, o.handB.y, SK.upper, SK.fore, -1);
    const armF = limbL(shF.x, shF.y, aF[0], SK.upper, aF[1], SK.fore), armB = limbL(shB.x, shB.y, aB[0], SK.upper, aB[1], SK.fore);
    ctx.save();
    ctx.translate(o.x, o.y);
    ctx.fillStyle = 'rgba(10,12,20,0.22)';
    ctx.beginPath(); ctx.ellipse((o.shadowX || 0) * S, 2, 46 * S * (o.shadowW || 1), 8 * S, 0, 0, TAU); ctx.fill();
    ctx.scale(S, S);
    strokeL(ctx, armB, 13, 12, U.shade(look.shirt, -0.2));
    ctx.fillStyle = U.shade(look.skin, -0.15); ctx.beginPath(); ctx.arc(armB.x2, armB.y2, 7, 0, TAU); ctx.fill();
    strokeL(ctx, legB, 19, 17, U.shade(look.pants, -0.22)); shoeL(ctx, legB, U.shade(look.shoes, -0.15));
    const ps = look.packSize || 1, pw = 30 * ps, ph = 70 * ps;          // backpack
    ctx.save(); ctx.translate(hipX, hipY); ctx.rotate(lean);
    ctx.fillStyle = look.pack; Art.roundRect(ctx, -SK.shW - pw + 10, -SK.torso + 6 - (ps - 1) * 30, pw, ph, 10); ctx.fill();
    ctx.fillStyle = U.shade(look.pack, -0.18); Art.roundRect(ctx, -SK.shW - pw + 8, -SK.torso + 38 - (ps - 1) * 10, pw * 0.7, ph * 0.38, 7); ctx.fill();
    ctx.restore();
    strokeL(ctx, legF, 19, 17, look.pants); shoeL(ctx, legF, look.shoes);
    ctx.save(); ctx.translate(hipX, hipY); ctx.rotate(lean);              // jacket
    const hw = SK.hipW, sw = SK.shW, th = top;
    ctx.beginPath();
    ctx.moveTo(-hw, 6); ctx.lineTo(hw + 1, 6);
    ctx.quadraticCurveTo(sw + 3, -th * 0.45, sw, -th + 9);
    ctx.quadraticCurveTo(sw - 1, -th - 2, sw - 13, -th - 2);
    ctx.lineTo(-sw + 11, -th - 2);
    ctx.quadraticCurveTo(-sw - 1, -th - 1, -sw, -th + 10);
    ctx.quadraticCurveTo(-sw - 3, -th * 0.45, -hw, 6);
    ctx.closePath();
    ctx.fillStyle = look.shirt; ctx.fill();
    ctx.save(); ctx.clip();
    ctx.fillStyle = 'rgba(0,0,0,0.12)'; ctx.fillRect(-sw - 6, -th - 10, sw * 0.75, th + 20);
    ctx.strokeStyle = U.rgba(look.shirt2, 0.55); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(sw * 0.5, -th + 2); ctx.lineTo(sw * 0.42, 4); ctx.stroke();
    ctx.fillStyle = U.rgba(look.shirt2, 0.85); ctx.fillRect(-sw, -th * 0.62, sw * 2.2, 5);
    ctx.restore();
    ctx.fillStyle = U.shade(look.shirt, -0.1);
    ctx.beginPath(); ctx.moveTo(-10, -th - 2); ctx.lineTo(10, -th - 2); ctx.lineTo(4, -th + 10); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = U.shade(look.pack, -0.25); ctx.lineWidth = 6; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-6, -th + 2); ctx.quadraticCurveTo(10, -th * 0.6, 4, -th * 0.18); ctx.stroke();
    ctx.restore();
    ctx.strokeStyle = U.shade(look.skin, -0.12); ctx.lineWidth = 15; ctx.lineCap = 'round';   // neck
    ctx.beginPath(); ctx.moveTo(shX + 1, shY + 2); ctx.lineTo(U.lerp(shX, hdx, 0.55), U.lerp(shY, hdy, 0.55)); ctx.stroke();
    ctx.save(); ctx.translate(hdx, hdy); ctx.rotate(hTilt + lean * 0.3);
    Art.drawHeadLocal(ctx, look, o.face || {}, head.turn || 0, t, seed);
    ctx.restore();
    strokeL(ctx, armF, 13.5, 12.5, look.shirt);
    ctx.fillStyle = look.skin; ctx.beginPath(); ctx.arc(armF.x2, armF.y2, 7.5, 0, TAU); ctx.fill();
    ctx.restore();
    return { knF: { x: legF.x1, y: legF.y1 }, knB: { x: legB.x1, y: legB.y1 } };
  }
  // the sit-down, as a pure function of time: hip, feet, lean, arm blend (body-local units)
  const STAND_F = { x: 4 + 58 * Math.sin(0.05) + 56 * Math.sin(0.03), y: -117 + 58 * Math.cos(0.05) + 56 * Math.cos(0.03) };
  const STAND_B = { x: -4 + 58 * Math.sin(-0.04) + 56 * Math.sin(-0.06), y: -117 + 58 * Math.cos(-0.04) + 56 * Math.cos(-0.06) };
  function sitPose(t) {
    const ant = U.ease(t, SIT_A, SIT_D0, 'inOutSine') * (1 - U.ease(t, SIT_D0, SIT_D0 + 0.25));
    const kD = U.ease(t, SIT_D0, SIT_LAND, 'inOutSine');           // hips down
    const kF = U.ease(t, SIT_F0, SIT_F1, 'inOutSine');              // feet forward
    const land = t > SIT_LAND ? Math.exp(-7 * (t - SIT_LAND)) * Math.sin(TAU * 2.2 * (t - SIT_LAND)) : 0;
    const hy = U.lerp(-117, -11, kD) + 7 * ant + 3 * land;
    const hx = -15 * Math.sin(kD * Math.PI * 0.62) / Math.sin(Math.PI * 0.62) * (1 - 0.35 * kF);   // back as he sinks
    const fF = { x: U.lerp(STAND_F.x, 80, kF), y: U.lerp(STAND_F.y, -3, kF) };
    const fB = { x: U.lerp(STAND_B.x, 67, kF), y: U.lerp(STAND_B.y, -2, kF) };
    const lean = 0.3 * Math.sin(Math.PI * Math.min(1, kD * 1.15)) * (1 - 0.5 * kF) + 0.1 * ant + 0.03 * kF;
    return { legs: { hx, hy, fF, fB }, lean, kD, kF, kArm: U.ease(t, SIT_D0 + 0.05, SIT_LAND - 0.1, 'inOutSine') };
  }
  // a smooth 0→1 that overshoots a touch (for the shrug's snap)
  const snap = (t, t0, t1) => U.E.outBack(U.prog(t, t0, t1));

  /* ---------------- scene ---------------- */
  Film.scene({
    id: 'go-ahead',
    order: 3,
    title: 'Go On Ahead',
    duration: D,
    mood: 'forest',
    sfx: [
      [1.0, 'bird', { gain: 0.25 }],
      [9.5, 'pop', { gain: 0.45 }],
      [13.3, 'boing', { gain: 0.5 }],
      [14.75, 'whoosh', { gain: 0.18 }],
      [15.15, 'footsteps', { gain: 0.45 }],
      [19.6, 'sigh', { gain: 0.35 }],
      [20.4, 'bird', { gain: 0.5 }],
      [22.3, 'bird', { gain: 0.6 }],
      [24.1, 'bird', { gain: 0.45 }],
    ],
    fadeIn: 0,
    crossIn: 0,
    fadeOut: 1.2,
    post: { vignette: 0.32, grain: 0.045, letterbox: 1 },

    render(ctx, t) {
      // the letterbox bars (y < 138.33, y > 941.67) hide the rest of the frame: don't rasterize it
      ctx.beginPath(); ctx.rect(0, 138, W, 804); ctx.clip();
      // locked-off camera with a breath of handheld drift, then a gentle push toward the two of them
      const push = U.ease(t, 20.2, D + 1.5, 'inOutSine');
      const zoom = 1 + 0.08 * push;
      const sh = Art.shake(t * 0.6, 0.35, 31);
      const fx = CX - 80 * push + sh.x, fy = CY + 30 * push + sh.y;
      const camBg = (c) => Art.cam(c, { x: CX + (fx - CX) * 0.3, y: CY + (fy - CY) * 0.3, zoom: 1 + (zoom - 1) * 0.35 });
      const cam = (c) => Art.cam(c, { x: fx, y: fy, zoom });

      /* ---------- far world (cached, soft) ---------- */
      ctx.save();
      camBg(ctx);
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'low';   // bilinear is plenty for a soft plate (and 3x cheaper than 'high')
      ctx.drawImage(background(), -OX, -OY, W + 2 * OX, H + 2 * OY);
      const tip = { x: 1530 + 660 * 0.03, y: 640 - 410 };
      Art.glow(ctx, tip.x, tip.y + 6, 120, P.light, 0.8 * (0.55 + 0.15 * Math.sin(t * 1.4)), 'screen');
      raysScreen(ctx, { x: 1900, y: 10, angle: 2.2, spread: 0.7, count: 6, len: 1500, color: P.light, alpha: 0.14, t, seed: 9 });
      // distant birds come back as the group leaves
      for (let i = 0; i < 3; i++) {
        const k = U.prog(t, 20.0 + i * 0.5, 25.5 + i * 0.4);
        if (k <= 0 || k >= 1) continue;
        farBird(ctx, U.lerp(1500 + i * 70, 760 - i * 40, k), 300 + i * 26 + Math.sin(k * 5 + i) * 10, 1 - i * 0.18, t * 11 + i * 2, U.shade(P.mid, -0.25));
      }
      ctx.restore();

      ctx.save();
      cam(ctx);

      /* ---------- trail plane ---------- */
      const i0 = Math.floor((OFF - 200) / 210), i1 = Math.ceil((OFF + W + 200) / 210);
      for (let i = i0; i <= i1; i++) {                        // shrubs on the back edge
        if (U.hash(i, 61) < 0.4) continue;
        const x = i * 210 + U.hash(i, 62) * 120 - OFF;
        Art.bush(ctx, x, gy(x) + 5, 36 + U.hash(i, 63) * 28, U.mix(P.trees[2], P.grass, 0.25), U.shade(P.grass, 0.06), i);
      }
      Art.ground(ctx, { y: GY, amp: GAMP, offset: OFF, color: P.ground, color2: P.ground2 });
      Art.trail(ctx, { y: GY, amp: GAMP, offset: OFF, color: P.trail, depth: TRAIL_D });
      ctx.save();                                             // dappled light on the trail
      ctx.globalCompositeOperation = 'lighter';
      for (let j = 0; j < 9; j++) {
        const x = 120 + j * 215 + U.hash(j, 72) * 90;
        const flick = 0.75 + 0.25 * Math.sin(t * (0.5 + U.hash(j, 77) * 0.5) + j);
        ctx.fillStyle = U.rgba(P.light, (0.08 + U.hash(j, 74) * 0.06) * flick);
        ctx.beginPath(); ctx.ellipse(x, gy(x) + 24 + U.hash(j, 73) * 40, 44 + U.hash(j, 75) * 50, 7 + U.hash(j, 76) * 5, 0, 0, TAU); ctx.fill();
      }
      ctx.restore();
      Art.grass(ctx, { seed: 5, y: (x) => gy(x) + 1, offset: OFF, spacing: 9, h: 36, width: 3.2, color: P.grass, color2: U.shade(P.grass, 0.14), t, wind: 0.7 });

      /* ---------- the group ---------- */
      const go = setOff(t);
      const turnK = U.prog(t, T_TURN, T_TURN1);
      const ant = U.ease(t, T_ANT, T_SHRUG, 'inOutSine') * (1 - U.ease(t, T_SHRUG, T_SHRUG + 0.12));
      const shrugW = snap(t, T_SHRUG, T_HOLD) * (1 - U.ease(t, T_SETTLE, T_DOWN, 'inOutSine'));
      const react = U.ease(t, 9.15, 9.75);                    // "they look at me like I'm nuts"
      const crewDraw = [];
      for (const m of CREW) {
        const look = Art.CAST[m.k];
        const Si = S * m.ds;                                  // Art.person applies look.height itself
        const rate = 6 / look.height;                         // taller legs, slower cadence: same ground speed
        const x = m.x + go.dist * Si * look.height * rate;
        if (x > W + 160) continue;
        const y = gy(x) + FOOT + m.dy;
        const o = { x, y, s: Si, look: m.k, t, seed: m.k.charCodeAt(1) * 13 };
        const face = { smile: 0.1, lookX: 0.9, lookY: 0.15 };
        const head = { tilt: 0.02 };
        // waiting, while he talks
        if (m.k === 'h1') {                                    // one hand on the hip, poles in the other
          o.gesture = 'hips'; o.gw = 1 - U.ease(t, T_ANT - 0.45, T_ANT - 0.05);
          o.armF = [U.lerp(0.1, 0.34, o.gw), U.lerp(0.18, 0.14, o.gw)];
          face.brow = -0.25; face.smile = -0.05; o.lean = -0.04;
        }
        if (m.k === 'h2') { head.tilt = 0.08 + 0.05 * Math.sin(t * 0.9); face.smile = 0.15; }
        if (m.k === 'h3') { face.smile = 0.2; }
        if (m.k === 'h4') {
          // filming him... until the reaction, when the phone comes down
          const down = U.ease(t, 9.2, 9.95, 'inOutSine');
          const up = U.ease(t, 16.1, 16.8, 'inOutSine');
          o.gesture = 'phone'; o.gw = Math.max(1 - down, up);
          o.holdF = phone;
          face.lookY = -0.4 * (1 - down);
        }
        // reactions: side-eyes, raised brows, a slow incredulous blink
        if (react > 0 && t < T_ANT) {
          face.browUp = react;
          if (m.k === 'h1') { face.eyes = 'flat'; face.brow = 0; face.smile = -0.1; }
          if (m.k === 'h4') {                                  // surprised as the phone drops… then deadpan
            if (t < 10.4) { face.eyes = 'wide'; face.mouth = 'o'; face.open = 0.25; }
            else { face.eyes = 'flat'; face.smile = -0.12; face.brow = 0.2; }
          }
          if (m.k === 'h3') {
            const glance = U.ease(t, 10.4, 10.65) * (1 - U.ease(t, 11.6, 11.85)); // looks back over his shoulder at h2
            face.lookX = U.lerp(0.9, -1.6, glance); face.lookY = U.lerp(0.15, -0.2, glance);
            head.turn = 0.75 * glance; head.tilt = 0.1 * react - 0.05 * glance;
            face.smile = -0.15; face.brow = 0.5 * glance;
          }
          if (m.k === 'h2') {
            const glance = U.ease(t, 10.7, 10.9) * (1 - U.ease(t, 11.7, 11.95)); // ...who side-eyes him right back
            face.lookX = U.lerp(0.9, 1.5, glance); face.lookY = U.lerp(0.15, 0.6, glance);
            head.tilt = 0.08 * glance;
            face.eyes = 'flat'; face.smile = -0.05 - 0.1 * glance;
          }
        }
        // the synchronised shrug: anticipation → snap → hold → settle
        if (t >= T_ANT - 0.01 && t < T_DOWN + 0.4) {
          o.bob = 5 * ant - 2 * shrugW;
          o.gesture = undefined;
          o.shrug = U.clamp(shrugW);
          // palms up on both sides: front forearm forward-up, back forearm back-up
          o.armF = [U.lerp(0.1, 0.5, shrugW) - 0.08 * ant, U.lerp(0.18, 1.55, shrugW)];
          o.armB = [U.lerp(-0.08, -0.55, shrugW) + 0.05 * ant, U.lerp(0.14, -1.45, shrugW)];
          if (m.k === 'h4') o.holdF = phone;
          head.tilt = -0.14 * shrugW; head.turn = 0.35 * shrugW;
          face.eyes = shrugW > 0.4 ? 'closed' : 'open'; face.browUp = Math.max(face.browUp || 0, shrugW); face.smile = -0.12; face.lookX = 0.6;
        }
        o.face = face; o.head = head;
        // turn and walk off toward the summit
        if (t >= T_TURN) {
          if (t >= T_GO) {
            o.walk = rate * go.ph + (m.k === 'h1' ? 0 : m.k === 'h2' ? 1.9 : m.k === 'h3' ? 3.4 : 5);
            o.stride = go.stride;
            if (m.k !== 'h4') { o.gesture = undefined; }
            else {
              const up = U.ease(t, 16.1, 16.9, 'linear');
              if (up > 0 && up < 1) {
                const sh = shoulderF(o.walk, o.stride, o.seed, t);
                const sw = Math.sin(o.walk) * 0.5 * o.stride;
                const p0 = handAt(sh, [-sw * 0.9 + 0.04, 0.25 + Math.max(0, -sw) * 0.6]);   // the walk swing
                const p1 = { x: sh.x + 30, y: sh.y + 16 };                                   // phone at the face
                const p2 = handAt(sh, [2.15, 0.75]);                                         // held high ('phone')
                const q = up < 0.5 ? U.smooth(up * 2) : U.smooth(up * 2 - 1);
                const a = up < 0.5 ? p0 : p1, b = up < 0.5 ? p1 : p2;
                const Si = S * m.ds * look.height;
                o.gesture = undefined;
                o.reachF = { x: x + U.lerp(a.x, b.x, q) * Si, y: y + U.lerp(a.y, b.y, q) * Si };
              }
            }
            o.face = { smile: 0.12, lookX: 0.6, lookY: m.k === 'h3' ? -0.6 : 0 };
            o.head = { tilt: m.k === 'h3' ? -0.12 : -0.03 };
          }
          crewDraw.push({ o, flip: turnK });
        } else crewDraw.push({ o, flip: 0 });
      }
      // draw far-to-near
      crewDraw.slice().sort((a, b) => a.o.y - b.o.y).forEach((c) => {
        const after = c.o.look === 'h1' && c.o.walk === undefined ? (cx, a, f) => heldPoles(cx, a, f, Art.CAST.h1) : null;
        personFlip(ctx, c.o, c.flip, -1, 1, after);
      });

      /* ---------- me ---------- */
      const meY = gy(ME.x) + FOOT;
      const talk = Art.talkingAt(t, BUB, 'me');
      // where he looks: the flower, then them, then (watching them go) the trail, then the flower again
      const flowerHead = { x: FL.x, y: FL.y - 150 * FL.s };
      const sp = sitPose(t);
      const headY = meY + (sp.legs.hy - 136) * S;
      const angF = Math.atan2(flowerHead.y - headY, flowerHead.x - (ME.x + 5));
      const groupX = crewDraw.length ? crewDraw.reduce((a, c) => a + c.o.x, 0) / crewDraw.length : W + 200;
      const angG = Math.atan2(-20, Math.max(200, groupX - ME.x));
      const atThem = U.ease(t, 1.05, 1.45) * (1 - U.ease(t, 18.1, 18.7));
      const ang = U.lerp(angF, angG, atThem);
      const mf = {
        smile: 0.45 + 0.2 * U.ease(t, 1.5, 2.1) + 0.1 * U.bump(t, 8.7, 1),
        lookX: Math.cos(ang) * 1.1, lookY: Math.sin(ang) * U.lerp(1.5, 1.25, atThem),
        talk, browUp: 0.35 * U.bump(t, 2.7, 1.2) + 0.25 * U.bump(t, 1.35, 0.35),
      };
      if (t > 8.6 && t < 9.8) mf.eyes = 'happy';             // "I'm good right here."
      if (t > 13.3 && t < 14.7) { mf.smirk = 0.5; mf.smile = 0.5; } // amused by the shrug
      mf.blink = U.bump(t, 1.12, 0.09) + U.bump(t, 1.75, 0.08) + U.bump(t, 5.6, 0.08) + U.bump(t, 11.6, 0.08) + U.bump(t, 17.2, 0.08) + U.bump(t, 21.6, 0.2) + U.bump(t, 24.4, 0.16);
      if (t > SIT_LAND + 0.45 && t < SIT_LAND + 1.35) mf.eyes = 'closed'; // a contented settle
      const seated = U.ease(t, SIT_LAND - 0.3, SIT_F1 + 0.3);
      const mo = { x: ME.x, y: meY, s: S, look: 'me', t, face: mf, head: { tilt: ang * U.lerp(U.lerp(0.62, 0.42, atThem), 0.8, seated) + 0.05 * atThem, turn: 0.3 * (1 - atThem) } };
      // gestures: "go on" (a friendly shooing flick), "right here" (open hand), a wave goodbye
      const goOn = U.ease(t, 2.05, 2.45) * (1 - U.ease(t, 4.35, 4.85));
      const here = U.ease(t, 6.7, 7.2) * (1 - U.ease(t, 8.8, 9.4));
      const bye = U.ease(t, 15.55, 15.95) * (1 - U.ease(t, 17.25, 17.75));
      const standF = [0.1, 0.18], standB = [-0.08, 0.14];
      let aF = standF.slice(), aB = standB.slice();
      if (goOn > 0) { const flick = 0.55 + 0.45 * Math.sin(t * 10.5); aF = [U.lerp(aF[0], 1.25 + 0.1 * flick, goOn), U.lerp(aF[1], 0.15 + 0.85 * flick, goOn)]; }
      if (here > 0) { aF = [U.lerp(aF[0], 0.6, here), U.lerp(aF[1], 0.12, here)]; aB = [U.lerp(aB[0], -0.4, here), U.lerp(aB[1], 0.28, here)]; mo.head.tilt += 0.06 * Math.sin((t - 6.7) * 6) * here; }
      if (bye > 0) { aF = [U.lerp(aF[0], 2.25, bye), U.lerp(aF[1], 0.6 + Math.sin(t * 9) * 0.35, bye)]; }
      aF[0] += Math.sin(t * 1.7) * 0.015;                     // the kit's idle breath, kept under the overrides
      mo.armF = aF; mo.armB = aB;
      if (t < SIT_A) Art.person(ctx, mo);
      else {
        // sitting down beside the flower (one continuous move, see sitPose); hands slide to the knees
        mo.legs = sp.legs; mo.lean = sp.lean;
        mo.head.tilt += 0.1 * U.bump(t, (SIT_D0 + SIT_LAND) / 2, 0.45) + 0.04 * Math.sin(t * 0.6) * seated;
        if (sp.kArm > 0) {
          // knees (local) from a dry IK pass, then hands on them, blended from the hanging arms
          const L = sp.legs, kneeOf = (ox, f) => { const a = Art.ik2(ox, L.hy, f.x, f.y, 58, 56, 1); return { x: ox + 58 * Math.sin(a[0]), y: L.hy + 58 * Math.cos(a[0]) }; };
          const kF = kneeOf(L.hx + 4, L.fF), kB = kneeOf(L.hx - 4, L.fB);
          const top = 88 + Math.sin(t * 1.7 + ME_SEED) * 0.39;
          const shX = L.hx + Math.sin(sp.lean) * top, shY = L.hy - Math.cos(sp.lean) * top;
          const hF0 = handAt({ x: shX + 3, y: shY + 7 }, aF), hB0 = handAt({ x: shX - 6, y: shY + 8 }, aB);
          const k = sp.kArm;
          mo.handF = { x: U.lerp(hF0.x, kF.x + 4, k), y: U.lerp(hF0.y, kF.y - 8, k) };
          mo.handB = { x: U.lerp(hB0.x, kB.x - 4, k), y: U.lerp(hB0.y, kB.y - 6, k) };
        }
        mo.shadowX = 30 * sp.kF; mo.shadowW = 1 + 0.5 * sp.kF;
        meRig(ctx, mo);
      }

      /* ---------- the flower spot, in front of the trail ---------- */
      ctx.fillStyle = U.shade(P.ground, -0.08);
      ctx.beginPath(); ctx.ellipse(FL.x + 14, FL.y + 4, 175, 18, 0, 0, TAU); ctx.fill();
      mossyRock(ctx, ROCK.x, ROCK.y, ROCK.w, ROCK.h, U.mix(P.grass, P.trees[2], 0.25), 7);
      Art.fern(ctx, FERN.x, FERN.y, FERN.s, U.mix(P.grass, P.trees[2], 0.45), U.wind(t, FERN.x, 2) * 0.7);
      Art.fern(ctx, FERN.x + 30, FERN.y + 3, FERN.s * 0.6, U.mix(P.grass, P.trees[2], 0.2), U.wind(t, FERN.x + 30, 3) * 0.7);
      Art.glow(ctx, FL.x, FL.y - 158, 190, '#ffb3cc', 0.12 + 0.03 * Math.sin(t * 1.3));
      Art.flower(ctx, { x: FL.x, y: FL.y, s: FL.s, t, seed: 3, face: 0.72, sway: 0.8, glow: 0.18 });
      Art.grass(ctx, { seed: 9, y: (x) => gy(x) + TRAIL_D + 2, offset: OFF, spacing: 8, h: 26, hVar: 0.8, width: 3, color: U.shade(P.grass, -0.12), color2: U.shade(P.grass, 0.02), t, wind: 0.6 });

      // the bird who comes to sit with them
      const land = 22.35;
      if (t > 20.6) {
        const perch = { x: ROCK.x + 8, y: ROCK.y - ROCK.h + 4 };
        let bx, by, wing, perched = false, tilt = 0;
        if (t < land) {
          const k = U.ease(t, 20.6, land, 'outSine');
          bx = U.lerp(1460, perch.x, k);
          by = U.lerp(330, perch.y, k) - Math.sin(k * Math.PI) * 90;
          wing = (k < 0.82 ? Math.sin(t * 26) * 0.9 : 0.9 * (1 - U.prog(k, 0.82, 1))) + 0.2;
          tilt = -0.25 * (1 - k);
        } else {
          perched = true;
          const hop = U.bump(t, 23.55, 0.18);
          bx = perch.x + 11 * U.ease(t, 23.4, 23.7); by = perch.y - 13 * hop;
          wing = 0.5 * U.bump(t, land + 0.08, 0.16) + 0.4 * hop;
          tilt = 0.12 * Math.sin(t * 2.2) * U.ease(t, 24, 24.4);
        }
        songbird(ctx, bx, by, 1.7, -1, { wing, perched, tilt, chirp: U.bump(t, 24.2, 0.12) + U.bump(t, 24.55, 0.1), tailUp: 3 * Math.sin(t * 5) * (perched ? 1 : 0) });
      }
      Art.motes(ctx, { seed: 23, count: 26, x0: 120, x1: 1500, y0: 420, y1: 900, t, color: '#fff3d0', size: 1.6, drift: 7, glow: 0.5, alpha: 0.45 });
      ctx.restore();

      /* ---------- words ---------- */
      // bubble tails find his mouth
      const mouth = { x: ME.x + 14 * S, y: meY - 237 * S };
      const bub = BUB.map(([a, b, txt, o]) => [a, b, txt, Object.assign({ tx: mouth.x + 50, ty: mouth.y - 14, maxW: 600 }, o)]);
      Art.bubbles(ctx, t, bub);
      // a "?" over h3's head
      const qa = U.fade(t, 9.5, 12.75, 0.05, 0.4);
      if (qa > 0) {
        const h3 = CREW[1];
        const pop = U.E.outBack(U.prog(t, 9.5, 9.8));
        const qx = h3.x - 8, qy = gy(h3.x) + FOOT - 462 + Math.sin(t * 3.2) * 4;
        ctx.save();
        ctx.translate(qx, qy);
        ctx.rotate(0.12 * Math.sin(t * 2.4));
        ctx.scale(0.4 + 0.6 * pop, 0.4 + 0.6 * pop);
        ctx.globalAlpha *= qa;
        ctx.font = Art.font(92, 'sans', 900);
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.lineJoin = 'round';
        ctx.lineWidth = 10; ctx.strokeStyle = 'rgba(40,32,40,0.85)';
        ctx.strokeText('?', 0, 0);
        ctx.fillStyle = '#fffaf1';
        ctx.fillText('?', 0, 0);
        ctx.restore();
      }
      Art.captions(ctx, t, CAPS);
    },
  });
})();
