/* ==========================================================================
   11 · Embarrassment’s Flowers — the shop interior, the hikers barge in,
   the $10 tulip, the trudge to the back room, the dusty $200 flower, the
   hikers don’t flinch, and the celebration.

   Also defines window.ShopKit — the shop interior set, its props and the
   mud footprints — reused by scenes/13-great-story.js.

   World space = the wide shot (1920×1080 film units at zoom 1). The set is
   staged like a box set with a mild, cheated perspective:
     - back wall parallel to the screen (base y = 790), shelves, a clock,
       the bead-curtain doorway to the back room at the right;
     - the shop front as an angled left wall: the green glass door (near,
       far left) and the big front window with the bench (deeper);
     - horizontal oak floorboards; a character standing at floor y has
       scale K.sAt(y) (1.0 at y = 880).
   ========================================================================== */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp } = U;

  /* ======================================================================
     SHOPKIT — geometry
     ====================================================================== */
  const K = {};
  K.HZ = 213;
  /** character / prop scale for something standing on the floor at y */
  K.sAt = (y) => (y - K.HZ) / 667;
  K.BACK_Y = 790;      // back wall base
  K.CORNER_X = 640;    // left wall meets back wall
  K.X0 = -420; K.X1 = 2320; // world extent drawn
  /** floor line of the angled left wall (shop front) */
  K.leftFloorY = (x) => K.BACK_Y + (K.CORNER_X - x) * 0.075;
  /** point on the left wall at x, h reference-px above the floor */
  K.leftPt = (x, h) => { const fy = K.leftFloorY(x); return { x, y: fy - h * K.sAt(fy) }; };
  K.WIN = { x0: 250, x1: 600, sill: 103, top: 489 };
  K.DOOR = { x0: 30, x1: 200, top: 369 };
  K.COUNTER = { x0: 1010, x1: 1600, topF: 691, topB: 668, base: 845 };
  K.CURTAIN = { x0: 1680, x1: 1830, top: 452 };
  K.REG = { x: 1532, y: 682 };
  K.BENCH = { x0: 300, x1: 584, y: 812, seat: 753 };
  K.ME = { x: 446, y: 812 };   // narrator on the bench
  K.EMB = { x: 1400, y: 808 }; // shopkeeper behind the counter

  /* ======================================================================
     SHOPKIT — palettes: 'day' (scene 11) and 'afternoon' (scene 13)
     ====================================================================== */
  K.PAL = {
    day: {
      wall: '#efe3cf', wallHi: '#f6ecdb', wallLo: '#dccab0', leftWall: '#e4d3b8',
      trim: '#3b2a25', wood: '#7a5238', woodHi: '#a2744d', woodLo: '#563826',
      floorFar: '#c99a63', floorNear: '#dcb07a', seam: '#9d7044',
      light: '#fff0c6', lightA: 1, outside: '#fff9ec', outside2: '#fbe9c9',
      counter: '#6e4630', counterLo: '#4e3122', counterTop: '#c08a5a', counterTopHi: '#dcae7c',
      grade: null,
    },
    afternoon: {
      wall: '#f1ddc0', wallHi: '#f8e6c8', wallLo: '#d9bf9c', leftWall: '#e2c9a6',
      trim: '#3b2a25', wood: '#7a4f33', woodHi: '#a8704a', woodLo: '#553522',
      floorFar: '#c8925a', floorNear: '#deaa6e', seam: '#9a6a3e',
      light: '#ffcf8a', lightA: 1.25, outside: '#fff0d4', outside2: '#ffd9a0',
      counter: '#6e4630', counterLo: '#4e3122', counterTop: '#c4895a', counterTopHi: '#e3ac74',
      grade: '#ff9a48',
    },
  };

  /* ======================================================================
     SHOPKIT — small drawing helpers
     ====================================================================== */
  const rr = (c, x, y, w, h, r) => Art.roundRect(c, x, y, w, h, r);
  function poly(c, pts) { c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]); c.closePath(); }
  function leaf(c, x, y, len, wid, ang, col) {
    c.save(); c.translate(x, y); c.rotate(ang);
    c.fillStyle = col;
    c.beginPath(); c.moveTo(0, 0);
    c.quadraticCurveTo(wid, -len * 0.45, 0, -len);
    c.quadraticCurveTo(-wid, -len * 0.45, 0, 0);
    c.fill();
    c.restore();
  }
  /** pot styles. (x,y) = bottom centre; returns rim y */
  function pot(c, x, y, w, h, style) {
    const cols = { terra: '#c66a43', cream: '#ece2d0', sage: '#86a88c', blue: '#6f8ea8', white: '#f3eee4', rust: '#b5543a', tin: '#a9b0b4', charcoal: '#4a4a4f', mustard: '#d9a441' };
    const col = cols[style] || style || cols.terra;
    if (style === 'tin') { bucket(c, x, y, w, h); return y - h; }
    c.fillStyle = col;
    c.beginPath();
    c.moveTo(x - w * 0.38, y); c.lineTo(x + w * 0.38, y); c.lineTo(x + w * 0.5, y - h * 0.84); c.lineTo(x - w * 0.5, y - h * 0.84); c.closePath(); c.fill();
    c.fillStyle = U.shade(col, 0.1);
    rr(c, x - w * 0.56, y - h, w * 1.12, h * 0.22, 3); c.fill();
    c.fillStyle = 'rgba(40,20,10,0.14)';
    c.beginPath(); c.moveTo(x + w * 0.1, y); c.lineTo(x + w * 0.38, y); c.lineTo(x + w * 0.5, y - h * 0.8); c.lineTo(x + w * 0.2, y - h * 0.8); c.closePath(); c.fill();
    if (style === 'cream' || style === 'white' || style === 'sage' || style === 'blue') { // glazed stripe
      c.fillStyle = U.rgba(U.shade(col, -0.25), 0.55);
      c.fillRect(x - w * 0.45, y - h * 0.55, w * 0.9, h * 0.08);
    }
    return y - h;
  }
  /** galvanized bucket. (x,y) bottom centre */
  function bucket(c, x, y, w, h) {
    const g = c.createLinearGradient(x - w / 2, 0, x + w / 2, 0);
    g.addColorStop(0, '#8b9398'); g.addColorStop(0.35, '#d4d9dc'); g.addColorStop(0.6, '#aab1b5'); g.addColorStop(1, '#7c8489');
    c.fillStyle = g;
    c.beginPath();
    c.moveTo(x - w * 0.4, y); c.lineTo(x + w * 0.4, y); c.lineTo(x + w * 0.5, y - h); c.lineTo(x - w * 0.5, y - h); c.closePath(); c.fill();
    c.strokeStyle = 'rgba(70,78,84,0.45)'; c.lineWidth = Math.max(1, w * 0.03);
    for (const k of [0.25, 0.7]) { const yy = y - h * k, ww = lerp(w * 0.4, w * 0.5, k); c.beginPath(); c.moveTo(x - ww, yy); c.lineTo(x + ww, yy); c.stroke(); }
    c.fillStyle = '#c3c9cc'; c.fillRect(x - w * 0.52, y - h - 2, w * 1.04, 4);
  }
  /** a bunch of cut flowers rising from (x,y) — simple heads, deterministic */
  function bunch(c, x, y, w, h, kind, seed, col, col2) {
    const n = 7 + Math.floor(U.hash(seed, 1) * 4);
    c.strokeStyle = '#4c7a3e'; c.lineWidth = 2; c.lineCap = 'round';
    const heads = [];
    for (let i = 0; i < n; i++) {
      const a = (U.hash(i, seed) - 0.5) * 0.7;
      const L = h * (0.75 + U.hash(i, seed + 2) * 0.3);
      const hx = x + (U.hash(i, seed + 3) - 0.5) * w * 0.5 + Math.sin(a) * L, hy = y - Math.cos(a) * L;
      c.beginPath(); c.moveTo(x + (U.hash(i, seed + 4) - 0.5) * w * 0.3, y); c.quadraticCurveTo(x + Math.sin(a) * L * 0.4, y - L * 0.5, hx, hy); c.stroke();
      heads.push([hx, hy, i]);
    }
    // a few leaves
    for (let i = 0; i < 4; i++) leaf(c, x + (U.hash(i, seed + 9) - 0.5) * w * 0.5, y - h * 0.25, h * 0.32, h * 0.08, (U.hash(i, seed + 10) - 0.5) * 1.6, '#5b8f47');
    heads.sort((a, b) => a[1] - b[1]);
    for (const [hx, hy, i] of heads) {
      const r = w * (0.11 + U.hash(i, seed + 5) * 0.04);
      if (kind === 'daisy') {
        c.fillStyle = col || '#fbf7ee';
        for (let k = 0; k < 8; k++) { const an = k / 8 * TAU; c.beginPath(); c.ellipse(hx + Math.cos(an) * r * 0.7, hy + Math.sin(an) * r * 0.5, r * 0.45, r * 0.22, an, 0, TAU); c.fill(); }
        c.fillStyle = '#f2b822'; c.beginPath(); c.arc(hx, hy, r * 0.36, 0, TAU); c.fill();
      } else if (kind === 'sun') {
        c.fillStyle = col || '#f2c230';
        for (let k = 0; k < 10; k++) { const an = k / 10 * TAU; c.beginPath(); c.ellipse(hx + Math.cos(an) * r * 0.8, hy + Math.sin(an) * r * 0.6, r * 0.5, r * 0.2, an, 0, TAU); c.fill(); }
        c.fillStyle = '#6b3d1c'; c.beginPath(); c.arc(hx, hy, r * 0.5, 0, TAU); c.fill();
      } else if (kind === 'tulip') {
        c.fillStyle = (i % 3 === 0 && col2) ? col2 : (col || '#e0483a');
        c.beginPath(); c.moveTo(hx - r * 0.7, hy - r * 0.2); c.quadraticCurveTo(hx - r * 0.8, hy + r * 0.9, hx, hy + r * 0.8); c.quadraticCurveTo(hx + r * 0.8, hy + r * 0.9, hx + r * 0.7, hy - r * 0.2);
        c.lineTo(hx + r * 0.35, hy + r * 0.1); c.lineTo(hx, hy - r * 0.4); c.lineTo(hx - r * 0.35, hy + r * 0.1); c.closePath(); c.fill();
      } else if (kind === 'lav') {
        c.fillStyle = col || '#9a86c8';
        for (let k = 0; k < 5; k++) { c.beginPath(); c.ellipse(hx, hy + k * r * 0.45, r * 0.24, r * 0.3, 0, 0, TAU); c.fill(); }
      } else if (kind === 'rose') {
        c.fillStyle = col || '#f2a07e'; c.beginPath(); c.arc(hx, hy, r * 0.62, 0, TAU); c.fill();
        c.strokeStyle = U.shade(col || '#f2a07e', -0.25); c.lineWidth = 1.2;
        c.beginPath(); c.arc(hx, hy, r * 0.32, 0.5, 4.5); c.stroke();
      } else { // eucalyptus / greenery
        c.fillStyle = col || '#8fb3a0';
        for (let k = 0; k < 4; k++) { c.beginPath(); c.arc(hx + (k % 2 ? r * 0.4 : -r * 0.4), hy + k * r * 0.5, r * 0.32, 0, TAU); c.fill(); }
      }
    }
  }
  /** simple houseplants (base at x,y — the pot rim) */
  const PLANT = {
    succulent(c, x, y, r, col) {
      for (let ring = 2; ring >= 0; ring--) {
        const n = 7 - ring, rad = r * (1 - ring * 0.25);
        c.fillStyle = U.shade(col, ring * 0.1);
        for (let i = 0; i < n; i++) { const a = -Math.PI / 2 + (i - (n - 1) / 2) * (2.4 / n); leaf(c, x, y, rad, rad * 0.32, a + Math.PI / 2 + (a + Math.PI / 2) * 0.2, U.shade(col, ring * 0.1 - (i % 2) * 0.05)); }
      }
    },
    leafy(c, x, y, r, col, seed) {
      for (let i = 0; i < 9; i++) {
        const a = -Math.PI / 2 + (U.hash(i, seed) - 0.5) * 2.6;
        const L = r * (0.6 + U.hash(i, seed + 1) * 0.5);
        c.save(); c.translate(x, y); c.rotate(a + Math.PI / 2);
        c.fillStyle = U.shade(col, (U.hash(i, seed + 2) - 0.5) * 0.2);
        c.beginPath(); c.ellipse(0, -L * 0.6, L * 0.32, L * 0.45, 0, 0, TAU); c.fill();
        c.restore();
      }
    },
    snake(c, x, y, h, col) {
      const blades = [[-0.18, 0.8], [0.05, 1], [0.22, 0.85], [-0.05, 0.65], [0.3, 0.55]];
      for (const [a, k] of blades) {
        const L = h * k, bw = h * 0.07;
        c.save(); c.translate(x + a * h * 0.3, y); c.rotate(a * 0.5);
        c.fillStyle = col;
        c.beginPath(); c.moveTo(-bw, 0); c.quadraticCurveTo(-bw * 1.2, -L * 0.6, 0, -L); c.quadraticCurveTo(bw * 1.2, -L * 0.6, bw, 0); c.closePath(); c.fill();
        c.strokeStyle = U.rgba('#e8e4a0', 0.55); c.lineWidth = 1;
        c.beginPath(); c.moveTo(-bw * 0.9, -2); c.quadraticCurveTo(-bw * 1.05, -L * 0.6, -bw * 0.1, -L * 0.96); c.stroke();
        c.restore();
      }
    },
    cactus(c, x, y, h, col) {
      c.fillStyle = col;
      rr(c, x - h * 0.16, y - h, h * 0.32, h, h * 0.16); c.fill();
      rr(c, x + h * 0.12, y - h * 0.7, h * 0.22, h * 0.42, h * 0.11); c.fill();
      rr(c, x - h * 0.32, y - h * 0.55, h * 0.2, h * 0.3, h * 0.1); c.fill();
      c.strokeStyle = U.rgba(U.shade(col, -0.3), 0.5); c.lineWidth = 1;
      c.beginPath(); c.moveTo(x, y - h + 4); c.lineTo(x, y); c.stroke();
      c.fillStyle = '#f2a6b8'; c.beginPath(); c.arc(x, y - h, h * 0.07, 0, TAU); c.fill();
    },
    fern(c, x, y, s, col) { Art.fern(c, x, y, s, col, 0); },
    trailing(c, x, y, len, col, seed, sway) {
      sway = sway || 0;
      for (let v = 0; v < 3; v++) {
        const dx = (v - 1) * 9, L = len * (0.6 + U.hash(v, seed) * 0.5);
        c.strokeStyle = U.shade(col, -0.25); c.lineWidth = 1.6;
        c.beginPath(); c.moveTo(x + dx, y); c.quadraticCurveTo(x + dx + 10 + sway * 0.5, y + L * 0.5, x + dx + 4 + sway, y + L); c.stroke();
        for (let i = 1; i <= 7; i++) {
          const k = i / 7;
          const px = x + dx + (10 * 2 * k * (1 - k)) + (4 + sway) * k * k, py = y + L * k;
          c.fillStyle = U.shade(col, ((i + v) % 3 - 1) * 0.08);
          c.beginPath(); c.ellipse(px + (i % 2 ? 4 : -4), py, 4.5, 3, i % 2 ? 0.6 : -0.6, 0, TAU); c.fill();
        }
      }
      PLANT.leafy(c, x, y, len * 0.35, col, seed + 3);
    },
    flowers(c, x, y, s, kind, colors, seed) {
      for (let i = 0; i < 3; i++) Art.flower(c, { x: x + (i - 1) * 8 * s, y, s: s * (0.28 + U.hash(i, seed) * 0.06), kind, colors, stemH: 90 + U.hash(i, seed + 1) * 40, sway: 0, seed: seed + i, face: 0.8 });
    },
  };
  K.PLANT = PLANT;
  K.pot = pot;
  K.bucket = bucket;
  K.bunch = bunch;

  /* ======================================================================
     SHOPKIT — the static set (drawn once into a cache)
     ====================================================================== */
  function drawBackWall(c, P) {
    // wall: lit lower, a touch darker toward the ceiling; warm bounce near the window corner
    const g = c.createLinearGradient(0, 120, 0, K.BACK_Y);
    g.addColorStop(0, P.wallLo); g.addColorStop(0.45, P.wall); g.addColorStop(1, P.wallHi);
    c.fillStyle = g;
    c.fillRect(K.CORNER_X, 0, K.X1 - K.CORNER_X, K.BACK_Y + 2);
    const gb = c.createRadialGradient(780, 640, 20, 780, 640, 700);
    gb.addColorStop(0, U.rgba(P.light, 0.32)); gb.addColorStop(1, U.rgba(P.light, 0));
    c.fillStyle = gb; c.fillRect(K.CORNER_X, 0, 1200, K.BACK_Y);
    // stucco texture: faint blotches
    for (let i = 0; i < 70; i++) {
      const x = K.CORNER_X + U.hash(i, 71) * (K.X1 - K.CORNER_X), y = 150 + U.hash(i, 72) * 620;
      c.fillStyle = U.rgba(i % 2 ? '#ffffff' : '#b89c7a', 0.05 + U.hash(i, 73) * 0.04);
      c.beginPath(); c.ellipse(x, y, 20 + U.hash(i, 74) * 50, 8 + U.hash(i, 75) * 20, U.hash(i, 76) * 3, 0, TAU); c.fill();
    }
    // ceiling beam + crown
    c.fillStyle = P.trim; c.fillRect(K.CORNER_X - 20, 104, K.X1, 50);
    c.fillStyle = U.shade(P.trim, 0.12); c.fillRect(K.CORNER_X - 20, 150, K.X1, 6);
    c.fillStyle = 'rgba(40,24,14,0.18)'; c.fillRect(K.CORNER_X, 156, K.X1, 14);
    // chair rail + wainscot (painted sage below the rail)
    const wy = 640;
    c.fillStyle = '#9fb59b'; c.fillRect(K.CORNER_X, wy, K.X1 - K.CORNER_X, K.BACK_Y - wy);
    c.fillStyle = 'rgba(255,255,255,0.12)'; c.fillRect(K.CORNER_X, wy + 6, K.X1 - K.CORNER_X, 8);
    c.strokeStyle = 'rgba(60,80,60,0.25)'; c.lineWidth = 2;
    for (let x = K.CORNER_X + 30; x < K.X1; x += 64) { c.beginPath(); c.moveTo(x, wy + 18); c.lineTo(x, K.BACK_Y - 26); c.stroke(); }
    c.fillStyle = P.wood; c.fillRect(K.CORNER_X, wy - 6, K.X1 - K.CORNER_X, 10);
    c.fillStyle = P.woodHi; c.fillRect(K.CORNER_X, wy - 6, K.X1 - K.CORNER_X, 3);
    // baseboard
    c.fillStyle = P.trim; c.fillRect(K.CORNER_X, K.BACK_Y - 22, K.X1 - K.CORNER_X, 24);
    c.fillStyle = U.shade(P.trim, 0.15); c.fillRect(K.CORNER_X, K.BACK_Y - 22, K.X1 - K.CORNER_X, 3);
  }

  function shelf(c, P, x0, x1, y) {
    // soft shadow on the wall beneath
    const sg = c.createLinearGradient(0, y + 8, 0, y + 30);
    sg.addColorStop(0, 'rgba(60,35,20,0.22)'); sg.addColorStop(1, 'rgba(60,35,20,0)');
    c.fillStyle = sg; c.fillRect(x0 + 4, y + 8, x1 - x0 - 8, 22);
    // brackets
    c.fillStyle = P.trim;
    for (const bx of [x0 + 26, (x0 + x1) / 2, x1 - 26]) { c.beginPath(); c.moveTo(bx - 4, y + 8); c.lineTo(bx + 4, y + 8); c.lineTo(bx + 4, y + 34); c.closePath(); c.fill(); }
    // plank: top + front
    c.fillStyle = P.woodHi; c.fillRect(x0, y - 4, x1 - x0, 5);
    c.fillStyle = P.wood; c.fillRect(x0, y + 1, x1 - x0, 9);
    c.fillStyle = P.woodLo; c.fillRect(x0, y + 8, x1 - x0, 2);
  }

  // shelf contents: [x, kind, potStyle, potW, potH, plantColor, extra]
  const SHELVES = [
    { x0: 688, x1: 1196, y: 330, items: [
      [716, 'trailing', 'cream', 34, 28, '#4f8a4a', 110], [778, 'succulent', 'terra', 30, 24, '#7fae96'], [842, 'snake', 'white', 34, 34, '#3f7048', 90],
      [912, 'flowers', 'blue', 30, 26, ['bell', { petal: '#8fa3e8' }]], [972, 'cactus', 'terra', 26, 22, '#6a9a5c', 46], [1036, 'leafy', 'sage', 36, 30, '#4e8f5a', 34],
      [1104, 'trailing', 'terra', 32, 26, '#5e9a4e', 140], [1166, 'succulent', 'cream', 28, 22, '#9cc0a0'],
    ] },
    { x0: 688, x1: 1196, y: 455, items: [
      [720, 'fern', 'terra', 36, 30, '#4b8a44', 0.55], [796, 'flowers', 'cream', 30, 26, ['daisy', { petal: '#ffffff', tip: '#fffaf0', inner: '#f0e6c8' }]],
      [858, 'leafy', 'rust', 34, 28, '#3f7a48', 30], [926, 'succulent', 'sage', 30, 24, '#86b49a'], [992, 'trailing', 'white', 34, 28, '#4a8a52', 120],
      [1060, 'snake', 'terra', 30, 30, '#4a7a4e', 80], [1128, 'flowers', 'terra', 30, 26, ['tulip', { petal: '#f6c142', tip: '#ffe58a', inner: '#c98b12' }]],
    ] },
    { x0: 688, x1: 1196, y: 580, items: [
      [714, 'succulent', 'blue', 30, 24, '#8ab8a0'], [774, 'leafy', 'terra', 40, 32, '#4c8c50', 36], [846, 'cactus', 'cream', 26, 22, '#6f9f62', 50],
      [906, 'flowers', 'sage', 30, 26, ['rose', { petal: '#f29a72', inner: '#b8553a' }]], [968, 'fern', 'white', 34, 28, '#55904a', 0.5],
      [1040, 'trailing', 'mustard', 32, 28, '#4f8a4a', 70], [1110, 'leafy', 'charcoal', 34, 28, '#5b9a5a', 30], [1168, 'succulent', 'terra', 26, 20, '#93b98f'],
    ] },
    { x0: 1450, x1: 1648, y: 330, items: [[1484, 'trailing', 'terra', 32, 26, '#4f8a4a', 130], [1552, 'snake', 'cream', 30, 30, '#3f7048', 84], [1616, 'succulent', 'sage', 28, 22, '#8ab8a0']] },
    { x0: 1450, x1: 1648, y: 455, items: [[1482, 'leafy', 'white', 34, 28, '#4e8f5a', 32], [1550, 'flowers', 'terra', 30, 26, ['daisy', { petal: '#ffd8a8', tip: '#fff1dc', inner: '#e8a868' }]], [1614, 'cactus', 'blue', 26, 22, '#6a9a5c', 44]] },
    { x0: 1450, x1: 1648, y: 580, items: [[1486, 'succulent', 'cream', 30, 24, '#7fae96'], [1552, 'trailing', 'sage', 32, 26, '#5e9a4e', 60], [1616, 'leafy', 'terra', 30, 26, '#467f4c', 26]] },
  ];
  function drawShelfItems(c, sh) {
    for (const [x, kind, ps, pw, ph, col, ex] of sh.items) {
      const rim = pot(c, x, sh.y - 4, pw, ph, ps);
      if (kind === 'trailing') PLANT.trailing(c, x, rim + 2, ex, col, x);
      else if (kind === 'succulent') PLANT.succulent(c, x, rim + 4, pw * 0.75, col);
      else if (kind === 'snake') PLANT.snake(c, x, rim + 3, ex, col);
      else if (kind === 'cactus') PLANT.cactus(c, x, rim + 2, ex, col);
      else if (kind === 'leafy') PLANT.leafy(c, x, rim + 4, ex, col, x);
      else if (kind === 'fern') PLANT.fern(c, x, rim + 4, ex, col);
      else if (kind === 'flowers') PLANT.flowers(c, x, rim + 3, 1, col[0], col[1], x);
    }
  }

  function drawClockFace(c, x, y, r) {
    c.fillStyle = '#3b2a25'; c.beginPath(); c.arc(x, y + 3, r + 6, 0, TAU); c.fill();
    c.fillStyle = '#5c4033'; c.beginPath(); c.arc(x, y, r + 6, 0, TAU); c.fill();
    c.fillStyle = '#f7f0e2'; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill();
    c.strokeStyle = '#3b2a25';
    for (let i = 0; i < 12; i++) {
      const a = i / 12 * TAU, l = i % 3 ? 4 : 8;
      c.lineWidth = i % 3 ? 1.5 : 2.5;
      c.beginPath(); c.moveTo(x + Math.cos(a) * (r - 3), y + Math.sin(a) * (r - 3)); c.lineTo(x + Math.cos(a) * (r - 3 - l), y + Math.sin(a) * (r - 3 - l)); c.stroke();
    }
  }
  /** clock hands — minutes advance with t; the second hand ticks */
  K.clockHands = (c, t, x = 1306, y = 290, r = 34, t0 = 11 * 3600 + 42 * 60 + 10) => {
    const T = t0 + Math.floor(t);
    const sec = T % 60, min = (T / 60) % 60, hr = (T / 3600) % 12;
    const hand = (a, l, w, col) => { c.strokeStyle = col; c.lineWidth = w; c.lineCap = 'round'; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.sin(a) * l, y - Math.cos(a) * l); c.stroke(); };
    hand(hr / 12 * TAU, r * 0.5, 3.4, '#2d221e');
    hand(min / 60 * TAU, r * 0.78, 2.4, '#2d221e');
    hand(sec / 60 * TAU, r * 0.84, 1.1, '#c0392b');
    c.fillStyle = '#2d221e'; c.beginPath(); c.arc(x, y, 2.6, 0, TAU); c.fill();
  };

  function drawDoorway(c, P) {
    const { x0, x1, top } = K.CURTAIN;
    // opening: the dim back room
    const g = c.createLinearGradient(0, top, 0, K.BACK_Y);
    g.addColorStop(0, '#2a1d18'); g.addColorStop(1, '#3d2b22');
    c.fillStyle = g; c.fillRect(x0, top, x1 - x0, K.BACK_Y - top);
    // hints of the storeroom: a shelf with boxes, stacked pots
    c.fillStyle = '#4a3428'; c.fillRect(x0 + 10, 560, 90, 6);
    c.fillStyle = '#5a4030'; c.fillRect(x0 + 18, 532, 30, 28); c.fillRect(x0 + 54, 540, 24, 20);
    c.fillStyle = '#6b4a36'; for (let i = 0; i < 3; i++) { c.beginPath(); c.moveTo(x1 - 46 + i * 2, 790 - i * 16); c.lineTo(x1 - 16 - i * 2, 790 - i * 16); c.lineTo(x1 - 20 - i * 2, 774 - i * 16); c.lineTo(x1 - 42 + i * 2, 774 - i * 16); c.closePath(); c.fill(); }
    // frame
    c.fillStyle = P.trim;
    c.fillRect(x0 - 16, top - 18, x1 - x0 + 32, 18);
    c.fillRect(x0 - 16, top, 16, K.BACK_Y - top);
    c.fillRect(x1, top, 16, K.BACK_Y - top);
    c.fillStyle = U.shade(P.trim, 0.14);
    c.fillRect(x0 - 16, top - 18, x1 - x0 + 32, 3);
    c.fillRect(x0 - 3, top, 3, K.BACK_Y - top);
    // curtain rod
    c.fillStyle = '#8a6a3c'; c.fillRect(x0 - 4, top + 2, x1 - x0 + 8, 5);
  }

  function drawBenchCorner(c, P) {
    const b = K.BENCH;
    // the narrator's olive pack, leaning against the bench end
    c.save();
    c.translate(b.x0 - 2, b.y);
    c.rotate(-0.1);
    c.fillStyle = '#4e5a2c'; rr(c, -26, -76, 50, 76, 16); c.fill();                 // body
    c.fillStyle = '#6b7a3f'; rr(c, -24, -74, 44, 72, 14); c.fill();
    c.fillStyle = '#5c6a35'; rr(c, -24, -78, 44, 26, 10); c.fill();                 // top flap
    c.fillStyle = '#3f4a24'; c.fillRect(-4, -56, 4, 10);                             // buckle strap
    c.fillStyle = '#c9a54a'; c.fillRect(-5, -48, 6, 4);
    c.fillStyle = '#5c6a35'; rr(c, -18, -38, 32, 30, 8); c.fill();                  // front pocket
    c.strokeStyle = '#46512a'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(-14, -30); c.lineTo(10, -30); c.stroke();
    c.strokeStyle = '#3f4a24'; c.lineWidth = 3; c.beginPath(); c.moveTo(-12, -78); c.quadraticCurveTo(-2, -92, 8, -77); c.stroke(); // grab loop
    c.fillStyle = '#c9b48a'; rr(c, -22, -90, 44, 12, 6); c.fill();                  // bedroll
    c.restore();
    // bench: legs, seat, cushion
    const sy = b.seat;
    c.fillStyle = P.woodLo;
    for (const lx of [b.x0 + 14, b.x1 - 22]) c.fillRect(lx, sy + 8, 9, b.y - sy - 8);
    c.fillStyle = P.wood; c.fillRect(b.x0, sy, b.x1 - b.x0, 11);
    c.fillStyle = P.woodHi; c.fillRect(b.x0, sy, b.x1 - b.x0, 3);
    c.fillStyle = '#c4785e'; rr(c, b.x0 + 18, sy - 12, b.x1 - b.x0 - 36, 14, 7); c.fill();
    c.fillStyle = 'rgba(255,255,255,0.15)'; rr(c, b.x0 + 24, sy - 11, b.x1 - b.x0 - 48, 4, 2); c.fill();
    c.fillStyle = 'rgba(40,20,10,0.18)'; c.beginPath(); c.ellipse((b.x0 + b.x1) / 2, b.y + 2, (b.x1 - b.x0) * 0.55, 8, 0, 0, TAU); c.fill();
  }

  function drawLeftWall(c, P) {
    const L = K.leftPt;
    // wall plane (in light shadow — the sun comes through its window)
    const top = -60;
    poly(c, [[K.X0, top], [K.CORNER_X, top], [K.CORNER_X, K.BACK_Y], [K.X0, K.leftFloorY(K.X0)]]);
    const g = c.createLinearGradient(K.X0, 0, K.CORNER_X, 0);
    g.addColorStop(0, U.shade(P.leftWall, -0.1)); g.addColorStop(1, P.leftWall);
    c.fillStyle = g; c.fill();
    // ceiling beam continues (angled slightly)
    poly(c, [[K.X0, 92], [K.CORNER_X, 104], [K.CORNER_X, 156], [K.X0, 150]]);
    c.fillStyle = P.trim; c.fill();
    // wainscot + chair rail on the left wall
    const rail = 150;
    poly(c, [[K.X0, L(K.X0, rail).y], [K.CORNER_X, L(K.CORNER_X, rail).y], [K.CORNER_X, K.BACK_Y], [K.X0, K.leftFloorY(K.X0)]]);
    c.fillStyle = U.shade('#9fb59b', -0.08); c.fill();
    poly(c, [[K.X0, L(K.X0, rail).y - 6], [K.CORNER_X, L(K.CORNER_X, rail).y - 6], [K.CORNER_X, L(K.CORNER_X, rail).y + 4], [K.X0, L(K.X0, rail).y + 4]]);
    c.fillStyle = P.wood; c.fill();
    // baseboard
    poly(c, [[K.X0, K.leftFloorY(K.X0) - 24], [K.CORNER_X, K.BACK_Y - 22], [K.CORNER_X, K.BACK_Y + 1], [K.X0, K.leftFloorY(K.X0) + 1]]);
    c.fillStyle = P.trim; c.fill();
    // corner post
    c.fillStyle = U.shade(P.trim, 0.05); c.fillRect(K.CORNER_X - 9, 150, 18, K.BACK_Y - 150);
    c.fillStyle = U.shade(P.trim, 0.2); c.fillRect(K.CORNER_X - 9, 150, 4, K.BACK_Y - 150);
    // coat hook between door and window with a canvas tote hanging from it
    const hk = L(226, 330);
    c.fillStyle = '#a7782c'; c.beginPath(); c.arc(hk.x, hk.y, 3.5, 0, TAU); c.fill();
    c.fillStyle = '#e6dcc4';
    c.beginPath(); c.moveTo(hk.x - 14, hk.y + 26); c.lineTo(hk.x + 12, hk.y + 26); c.lineTo(hk.x + 14, hk.y + 70); c.lineTo(hk.x - 16, hk.y + 70); c.closePath(); c.fill();
    c.strokeStyle = '#d4c7aa'; c.lineWidth = 2; c.beginPath(); c.moveTo(hk.x - 9, hk.y + 26); c.quadraticCurveTo(hk.x, hk.y - 6, hk.x + 8, hk.y + 26); c.stroke();
    c.fillStyle = '#4f7a5a'; c.beginPath(); c.arc(hk.x - 1, hk.y + 48, 6, 0, TAU); c.fill();
  }

  /** the front window: bright street outside, mullions, sill, ledge plants */
  function drawWindow(c, P) {
    const { x0, x1, sill, top } = K.WIN;
    const L = K.leftPt;
    const A = L(x0, top), B = L(x1, top), C = L(x1, sill), D = L(x0, sill);
    // outside (over-exposed sunny street)
    c.save();
    poly(c, [[A.x, A.y], [B.x, B.y], [C.x, C.y], [D.x, D.y]]);
    c.clip();
    const g = c.createLinearGradient(0, A.y, 0, D.y);
    g.addColorStop(0, P.outside); g.addColorStop(0.55, P.outside2); g.addColorStop(1, '#f3dcb5');
    c.fillStyle = g; c.fillRect(x0 - 10, A.y - 10, x1 - x0 + 20, D.y - A.y + 20);
    // the building across the street, soft and pale
    c.fillStyle = 'rgba(232,186,150,0.55)'; c.fillRect(x0 - 10, A.y + 70, 220, 300);
    c.fillStyle = 'rgba(206,214,222,0.5)'; c.fillRect(x0 + 230, A.y + 40, 200, 330);
    c.fillStyle = 'rgba(255,255,255,0.45)';
    for (let i = 0; i < 4; i++) for (let j = 0; j < 3; j++) c.fillRect(x0 + 20 + i * 48, A.y + 100 + j * 70, 26, 40);
    c.fillStyle = 'rgba(150,170,190,0.35)';
    for (let i = 0; i < 3; i++) for (let j = 0; j < 4; j++) c.fillRect(x0 + 250 + i * 60, A.y + 70 + j * 64, 30, 38);
    // awning across the street + a lamp post
    c.fillStyle = 'rgba(214,120,104,0.45)'; c.beginPath(); c.moveTo(x0 - 10, A.y + 250); c.lineTo(x0 + 200, A.y + 250); c.lineTo(x0 + 186, A.y + 280); c.lineTo(x0 - 10, A.y + 280); c.closePath(); c.fill();
    c.fillStyle = 'rgba(90,80,70,0.35)'; c.fillRect(x0 + 205, A.y + 60, 5, 330); c.beginPath(); c.arc(x0 + 207, A.y + 56, 11, 0, TAU); c.fill();
    // sidewalk
    c.fillStyle = 'rgba(214,196,170,0.6)'; c.fillRect(x0 - 10, D.y - 40, x1 - x0 + 20, 50);
    c.restore();
    // window glow spill on the surrounding wall
    Art.glow(c, (x0 + x1) / 2, (A.y + D.y) / 2, 380, P.light, 0.28);
    // frame
    c.strokeStyle = P.trim; c.lineJoin = 'miter';
    c.lineWidth = 16; poly(c, [[A.x, A.y], [B.x, B.y], [C.x, C.y], [D.x, D.y]]); c.stroke();
    c.lineWidth = 7;
    for (const k of [1 / 3, 2 / 3]) { // vertical mullions
      const xx = lerp(x0, x1, k), p = L(xx, top), q = L(xx, sill);
      c.beginPath(); c.moveTo(p.x, p.y); c.lineTo(q.x, q.y); c.stroke();
    }
    for (const hh of [lerp(sill, top, 0.36), lerp(sill, top, 0.72)]) { // transoms
      const p = L(x0, hh), q = L(x1, hh);
      c.beginPath(); c.moveTo(p.x, p.y); c.lineTo(q.x, q.y); c.stroke();
    }
    // glass sheen
    c.save();
    poly(c, [[A.x, A.y], [B.x, B.y], [C.x, C.y], [D.x, D.y]]); c.clip();
    c.fillStyle = 'rgba(255,255,255,0.18)';
    c.beginPath(); c.moveTo(x0 + 40, A.y); c.lineTo(x0 + 110, A.y); c.lineTo(x0 - 10, D.y); c.lineTo(x0 - 80, D.y); c.closePath(); c.fill();
    c.restore();
    // deep sill / display ledge
    const s0 = L(x0 - 14, sill), s1 = L(x1 + 14, sill);
    poly(c, [[s0.x, s0.y - 2], [s1.x, s1.y - 2], [s1.x + 10, s1.y + 14], [s0.x - 6, s0.y + 18]]);
    c.fillStyle = P.wood; c.fill();
    poly(c, [[s0.x, s0.y - 2], [s1.x, s1.y - 2], [s1.x, s1.y + 3], [s0.x, s0.y + 3]]);
    c.fillStyle = P.woodHi; c.fill();
    // ledge plants: crowded at both ends, the middle kept clear (behind his head)
    const ledge = [[x0 + 18, 'snake', 'terra', 28, 24, '#3d6e45', 74], [x0 + 54, 'leafy', 'cream', 30, 24, '#4b8b50', 30], [x0 + 88, 'succulent', 'blue', 24, 18, '#8ab8a0'],
      [x1 - 92, 'flowers', 'terra', 26, 22, ['tulip', { petal: '#f05a3c', tip: '#ff9d6b', inner: '#a8281a' }]], [x1 - 58, 'cactus', 'cream', 22, 18, '#5f9a58', 40], [x1 - 22, 'trailing', 'sage', 28, 22, '#4f8a4a', 60]];
    for (const [x, kind, ps, pw, ph, col, ex] of ledge) {
      const by = L(x, sill).y + 4, sc = K.sAt(K.leftFloorY(x)) / 0.9;
      c.save(); c.translate(x, by); c.scale(sc, sc); c.translate(-x, -by);
      const rim = pot(c, x, by, pw, ph, ps);
      if (kind === 'snake') PLANT.snake(c, x, rim + 3, ex, col);
      else if (kind === 'leafy') PLANT.leafy(c, x, rim + 4, ex, col, x);
      else if (kind === 'succulent') PLANT.succulent(c, x, rim + 4, pw * 0.75, col);
      else if (kind === 'flowers') PLANT.flowers(c, x, rim + 3, 0.95, col[0], col[1], x);
      else if (kind === 'cactus') PLANT.cactus(c, x, rim + 2, ex, col);
      else if (kind === 'trailing') PLANT.trailing(c, x, rim + 2, ex, col, x);
      c.restore();
    }
    // the teapot on the sill beside him
    const tp = L(x0 + 150, sill);
    c.save(); c.translate(tp.x, tp.y + 2);
    c.fillStyle = '#5f8f8a'; c.beginPath(); c.ellipse(0, -14, 19, 15, 0, 0, TAU); c.fill();
    c.fillRect(-12, -3, 24, 4);
    c.strokeStyle = '#5f8f8a'; c.lineWidth = 4; c.beginPath(); c.moveTo(17, -16); c.quadraticCurveTo(30, -18, 31, -28); c.stroke();
    c.beginPath(); c.arc(-20, -14, 7, Math.PI * 0.5, Math.PI * 1.5); c.stroke();
    c.fillStyle = '#4c7a75'; c.beginPath(); c.ellipse(0, -28, 8, 3, 0, 0, TAU); c.fill();
    c.fillStyle = 'rgba(255,255,255,0.35)'; c.beginPath(); c.ellipse(-6, -19, 5, 4, -0.5, 0, TAU); c.fill();
    c.restore();
  }

  function drawDoorFrame(c, P) {
    const L = K.leftPt;
    const { x0, x1, top } = K.DOOR;
    const A = L(x0, top), B = L(x1, top), C = L(x1, 0), D = L(x0, 0);
    // the doorway opening (seen when the door opens): bright street
    poly(c, [[A.x, A.y], [B.x, B.y], [C.x, C.y], [D.x, D.y]]);
    const g = c.createLinearGradient(0, A.y, 0, D.y);
    g.addColorStop(0, P.outside); g.addColorStop(0.6, P.outside2); g.addColorStop(1, '#e9cfa6');
    c.fillStyle = g; c.fill();
    c.fillStyle = 'rgba(232,186,150,0.45)'; c.fillRect(A.x + 10, A.y + 40, 60, 200);
    c.fillStyle = 'rgba(206,214,222,0.45)'; c.fillRect(A.x + 90, A.y + 20, 70, 230);
    // frame
    c.strokeStyle = P.trim; c.lineWidth = 14; c.lineJoin = 'miter';
    c.beginPath(); c.moveTo(D.x, D.y); c.lineTo(A.x, A.y); c.lineTo(B.x, B.y); c.lineTo(C.x, C.y); c.stroke();
    // threshold
    poly(c, [[D.x - 8, D.y - 2], [C.x + 8, C.y - 2], [C.x + 12, C.y + 6], [D.x - 6, D.y + 7]]);
    c.fillStyle = '#8a6a3c'; c.fill();
    // bell bracket (the bell itself is animated, drawn live)
    const bp = L(x1 - 26, top + 22);
    c.strokeStyle = '#a7782c'; c.lineWidth = 3; c.lineCap = 'round';
    c.beginPath(); c.moveTo(bp.x - 4, bp.y + 6); c.lineTo(bp.x - 4, bp.y - 10); c.quadraticCurveTo(bp.x + 14, bp.y - 16, bp.x + 14, bp.y + 2); c.stroke();
    c.beginPath(); c.arc(bp.x + 8, bp.y + 4, 4, 0, Math.PI * 1.3); c.stroke();
  }
  K.bellPivot = () => { const bp = K.leftPt(K.DOOR.x1 - 26, K.DOOR.top + 22); return { x: bp.x + 14, y: bp.y + 2 }; };

  /** hanging planters (live: they sway a touch) */
  K.hangers = (c, t, P) => {
    const list = [[178, 214, 150, 0], [904, 232, 120, 1], [1572, 218, 160, 2]];
    for (const [x, y, len, i] of list) {
      const sw = Math.sin(t * 0.7 + i * 2.1) * 0.025;
      c.save();
      c.translate(x, 0); c.rotate(sw); c.translate(-x, 0);
      c.strokeStyle = '#b89a6a'; c.lineWidth = 1.6;
      c.beginPath(); c.moveTo(x, 90); c.lineTo(x - 18, y - 12); c.moveTo(x, 90); c.lineTo(x + 18, y - 12); c.moveTo(x, 90); c.lineTo(x, y - 12); c.stroke();
      c.fillStyle = i === 1 ? '#ece2d0' : '#c66a43';
      c.beginPath(); c.moveTo(x - 26, y - 14); c.lineTo(x + 26, y - 14); c.quadraticCurveTo(x + 24, y + 12, x, y + 14); c.quadraticCurveTo(x - 24, y + 12, x - 26, y - 14); c.fill();
      PLANT.trailing(c, x - 4, y - 10, len, i === 2 ? '#5e9a4e' : '#4f8a4a', 20 + i, Math.sin(t * 0.9 + i) * 4);
      c.restore();
    }
  };

  /** buckets of cut flowers along the back wall (left of the counter) */
  const BACK_BUCKETS = [[690, 'daisy', null, 1], [742, 'sun', null, 2], [796, 'tulip', '#e0483a', 3, '#f6c142'], [850, 'lav', null, 4], [904, 'rose', '#f2a07e', 5], [958, 'green', null, 6]];
  function drawBackBuckets(c) {
    const s = K.sAt(K.BACK_Y);
    for (const [x, kind, col, seed, col2] of BACK_BUCKETS) {
      const bw = 46 * s, bh = 44 * s;
      bunch(c, x, K.BACK_Y - bh + 10, bw * 1.2, 90 * s, kind, seed * 7, col, col2);
      bucket(c, x, K.BACK_Y + 2, bw, bh);
      c.fillStyle = '#f6efdf'; c.fillRect(x - 9, K.BACK_Y - bh * 0.62, 18, 11);
    }
  }
  /** the little price cards on those buckets (live: needs the web font) */
  K.bucketTags = (c) => {
    const s = K.sAt(K.BACK_Y);
    c.fillStyle = '#4a3428'; c.font = Art.font(8, 'sans', 800); c.textAlign = 'center'; c.textBaseline = 'middle';
    for (const [x, , , seed] of BACK_BUCKETS) c.fillText('$' + (4 + seed % 4 * 2), x, K.BACK_Y - 44 * s * 0.62 + 6);
  };

  /** right side, past the doorway: a tall plant stand and a palm */
  function drawRightSide(c, P) {
    shelf(c, P, 1868, 2160, 410);
    shelf(c, P, 1868, 2160, 560);
    pot(c, 1900, 406, 30, 26, 'cream'); PLANT.succulent(c, 1900, 384, 22, '#8ab8a0');
    pot(c, 1980, 406, 34, 28, 'terra'); PLANT.trailing(c, 1980, 380, 120, '#4f8a4a', 41);
    pot(c, 2070, 406, 30, 26, 'blue'); PLANT.cactus(c, 2070, 382, 44, '#6a9a5c');
    pot(c, 1930, 556, 34, 28, 'sage'); PLANT.leafy(c, 1930, 532, 30, '#4e8f5a', 44);
    pot(c, 2030, 556, 30, 26, 'white'); PLANT.snake(c, 2030, 533, 80, '#3f7048');
    // tall palm in a big pot
    const px = 2210, py = 792;
    for (let i = 0; i < 9; i++) {
      const a = -Math.PI / 2 + (i - 4) * 0.32;
      c.strokeStyle = '#3f7a44'; c.lineWidth = 3;
      const ex = px + Math.cos(a) * 260, ey = py - 150 + Math.sin(a) * 240;
      c.beginPath(); c.moveTo(px, py - 120); c.quadraticCurveTo(px + Math.cos(a) * 150, py - 150 + Math.sin(a) * 200, ex, ey); c.stroke();
      for (let k = 1; k < 10; k++) {
        const u = k / 10, qx = lerp(px, ex, u), qy = lerp(py - 120, ey, u) - Math.sin(u * Math.PI) * 30;
        leaf(c, qx, qy, 46 * (1 - u * 0.5), 6, a + Math.PI / 2 + 0.9, '#4a8a4c');
        leaf(c, qx, qy, 46 * (1 - u * 0.5), 6, a + Math.PI / 2 - 0.9 + Math.PI, '#3f7a44');
      }
    }
    pot(c, px, py + 2, 110, 100, 'terra');
  }

  /** draw the complete static set (no animation, no text that needs web fonts) */
  function drawStatic(c, P) {
    drawBackWall(c, P);
    for (const sh of SHELVES) shelf(c, P, sh.x0, sh.x1, sh.y);
    for (const sh of SHELVES) drawShelfItems(c, sh);
    drawClockFace(c, 1306, 290, 34);
    // a framed botanical print on the plain wall behind the counter (above his head)
    c.fillStyle = P.trim; c.fillRect(1236, 372, 76, 96);
    c.fillStyle = '#f4ecd8'; c.fillRect(1243, 379, 62, 82);
    Art.flower(c, { x: 1274, y: 452, s: 0.3, kind: 'rose', colors: { petal: '#e8857a', inner: '#9c3b30' }, sway: 0, stemH: 160, face: 0.9 });
    c.fillStyle = P.trim; c.fillRect(1338, 380, 70, 70);
    c.fillStyle = '#efe8d6'; c.fillRect(1345, 387, 56, 56);
    Art.flower(c, { x: 1373, y: 434, s: 0.26, kind: 'daisy', colors: { petal: '#ffffff', tip: '#fffaf0', inner: '#f0e6c8' }, sway: 0, stemH: 120, face: 0.9 });
    drawDoorway(c, P);
    drawRightSide(c, P);
    drawBackBuckets(c);
    // a soft, warm veil of air over the far wall: separates it from the actors
    const veil = c.createLinearGradient(0, 120, 0, K.BACK_Y);
    veil.addColorStop(0, 'rgba(246,236,218,0.16)'); veil.addColorStop(1, 'rgba(246,236,218,0.08)');
    c.fillStyle = veil; c.fillRect(K.CORNER_X, 80, K.X1 - K.CORNER_X, K.BACK_Y - 80);
    drawLeftWall(c, P);
    drawWindow(c, P);
    drawDoorFrame(c, P);
    drawBenchCorner(c, P);
  }

  /** cached static set — rendered once at backing resolution. It is built at
   *  load time (scale 1) so the first frame of the scene doesn't pay for it;
   *  rebuilt lazily only if the display's backing scale is clearly higher. */
  const CACHE_Y0 = 80, CACHE_Y1 = 960;
  function buildStatic(k) {
    const cv = Art.canvas('shopkit:static', (K.X1 - K.X0) * k, (CACHE_Y1 - CACHE_Y0) * k);
    const c = cv.getContext('2d');
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.clearRect(0, 0, cv.width, cv.height);
    c.setTransform(k, 0, 0, k, -K.X0 * k, -CACHE_Y0 * k);
    drawStatic(c, K.PAL.day);
    cv._built = k;
    return cv;
  }
  let staticCv = null;
  try { staticCv = buildStatic(1); } catch (e) { staticCv = null; }
  K.staticSet = (ctx) => {
    const want = Math.max(1, Math.min(2, Art._base ? Art._base.a : 1));
    if (!staticCv || (want > staticCv._built + 0.2)) staticCv = buildStatic(want);
    ctx.drawImage(staticCv, K.X0, CACHE_Y0, K.X1 - K.X0, CACHE_Y1 - CACHE_Y0);
  };

  /* ======================================================================
     SHOPKIT — live layers: window lettering, floor, light, door, curtain
     ====================================================================== */
  /** the shop name painted on the window glass, read from inside (mirrored) */
  K.windowLettering = (c, P) => {
    const { x0, x1, top } = K.WIN;
    const p = K.leftPt((x0 + x1) / 2, top - 70);
    c.save();
    c.translate(p.x, p.y);
    c.transform(-1, 0.02, 0, 1, 0, 0); // mirrored, following the wall's slight angle
    c.font = Art.font(40, 'hand', 700);
    c.textAlign = 'center'; c.textBaseline = 'middle';
    c.globalAlpha = 0.5;
    c.fillStyle = '#c96b62'; c.fillText('Embarrassment’s Flowers', 0, 2);
    c.globalAlpha = 0.85;
    c.fillStyle = '#f2a59e'; c.fillText('Embarrassment’s Flowers', 0, 0);
    c.restore();
  };

  /** floorboards. Live (crisp in close-ups). */
  K.floor = (c, P) => {
    const yb = K.BACK_Y;
    c.beginPath();
    c.moveTo(K.X0, K.leftFloorY(K.X0));
    c.lineTo(K.CORNER_X, yb); c.lineTo(K.X1, yb); c.lineTo(K.X1, 1100); c.lineTo(K.X0, 1100); c.closePath();
    const g = c.createLinearGradient(0, yb, 0, 1080);
    g.addColorStop(0, P.floorFar); g.addColorStop(1, P.floorNear);
    c.fillStyle = g; c.fill();
    // seams: plank rows in perspective (spacing grows toward camera)
    c.save();
    c.clip();
    let y = yb, row = 0;
    c.lineWidth = 1.4;
    while (y < 1090) {
      const s = K.sAt(y);
      const gap = 15 * (s / 0.865) * (s / 0.865);
      c.strokeStyle = U.rgba(P.seam, 0.5);
      c.beginPath(); c.moveTo(K.X0, y); c.lineTo(K.X1, y); c.stroke();
      // staggered butt joints, leaning toward the vanishing point
      const plankL = 260 * s;
      const off = U.hash(row, 13) * plankL;
      c.strokeStyle = U.rgba(P.seam, 0.38);
      c.beginPath();
      for (let x = K.X0 + off; x < K.X1; x += plankL) {
        const lean = (x - 960) * 0.0016 * gap;
        c.moveTo(x, y); c.lineTo(x + lean, y + gap);
      }
      c.stroke();
      // grain tint per plank row
      c.fillStyle = U.rgba(row % 2 ? '#ffffff' : '#7a5230', row % 2 ? 0.035 : 0.04);
      c.fillRect(K.X0, y, K.X1 - K.X0, gap);
      y += gap; row++;
    }
    c.restore();
  };

  /** sunlight through the front window: floor patches (pane by pane) */
  K.lightGeom = (mode) => mode === 'afternoon'
    ? { a: 1.95, b: 330, c: 0.29, base: 806 }
    : { a: 1.22, b: 250, c: 0.32, base: 804 };
  const winPt = (u, v) => { // u 0..1 across the window, v 0..1 sill→top
    const x = lerp(K.WIN.x0, K.WIN.x1, u);
    return K.leftPt(x, lerp(K.WIN.sill, K.WIN.top, v));
  };
  const floorPt = (u, v, G) => { // where the ray through window point (u,v) lands
    const x = lerp(K.WIN.x0, K.WIN.x1, u);
    const h = lerp(0, K.WIN.top - K.WIN.sill, v);
    return { x: x + G.b + h * G.a, y: G.base + h * G.c };
  };
  K.floorLight = (c, t, P, mode, amt = 1) => {
    const G = K.lightGeom(mode);
    const panes = [];
    const us = [[0.02, 0.31], [0.35, 0.64], [0.68, 0.98]], vs = [[0.02, 0.33], [0.39, 0.69], [0.75, 0.98]];
    for (const [u0, u1] of us) for (const [v0, v1] of vs) panes.push([u0, u1, v0, v1]);
    c.save();
    c.globalCompositeOperation = 'lighter';
    const flick = 0.92 + 0.08 * Math.sin(t * 0.6);
    for (const [u0, u1, v0, v1] of panes) {
      const a = floorPt(u0, v0, G), b = floorPt(u1, v0, G), d = floorPt(u1, v1, G), e = floorPt(u0, v1, G);
      poly(c, [[a.x, a.y], [b.x, b.y], [d.x, d.y], [e.x, e.y]]);
      c.fillStyle = U.rgba(P.light, 0.2 * P.lightA * amt * flick);
      c.fill();
    }
    c.restore();
  };
  /** volumetric shafts from the window into the room (+ motes in them) */
  K.shafts = (c, t, P, mode, amt = 1) => {
    const G = K.lightGeom(mode);
    c.save();
    c.globalCompositeOperation = 'lighter';
    const cols = [[0.02, 0.31], [0.35, 0.64], [0.68, 0.98]];
    cols.forEach(([u0, u1], i) => {
      const w0 = winPt(u0, 0.98), w1 = winPt(u1, 0.98), w2 = winPt(u1, 0.02), w3 = winPt(u0, 0.02);
      const f0 = floorPt(u0, 0.98, G), f1 = floorPt(u1, 0.98, G), f2 = floorPt(u1, 0.02, G), f3 = floorPt(u0, 0.02, G);
      // hull: top edge of the window to the far floor patch edge
      poly(c, [[w0.x, w0.y], [w1.x, w1.y], [f1.x, f1.y], [f2.x, f2.y], [w2.x, w2.y], [w3.x, w3.y], [f3.x, f3.y], [f0.x, f0.y]]);
      const g = c.createLinearGradient(w0.x, w0.y, f1.x, f1.y);
      const a = (0.075 + 0.02 * Math.sin(t * 0.5 + i * 1.7)) * P.lightA * amt;
      g.addColorStop(0, U.rgba(P.light, a));
      g.addColorStop(0.7, U.rgba(P.light, a * 0.55));
      g.addColorStop(1, U.rgba(P.light, a * 0.15));
      c.fillStyle = g; c.fill();
    });
    c.restore();
    // dust motes drifting in the light
    c.save();
    const w0 = winPt(0, 1), f1 = floorPt(1, 1, G), f2 = floorPt(1, 0, G), w3 = winPt(0, 0);
    poly(c, [[w0.x, w0.y], [winPt(1, 1).x, winPt(1, 1).y], [f1.x, f1.y], [f2.x, f2.y], [floorPt(0, 0, G).x, floorPt(0, 0, G).y], [w3.x, w3.y]]);
    c.clip();
    Art.motes(c, { seed: 17, count: 46, x0: K.WIN.x0, x1: f1.x, y0: K.WIN.x0 > 0 ? 360 : 360, y1: 900, t, color: '#fff3d2', size: 1.7, drift: 5, alpha: 0.55 * amt, wander: 40 });
    c.restore();
  };

  /** door: o = 0 closed .. 1 flung open (~100°). Hinge on the near (left) edge. */
  K.door = (c, P, o, t) => {
    const L = K.leftPt;
    const { x0, x1, top } = K.DOOR;
    const th = o * 1.75; // radians
    const A = L(x0, top), D = L(x0, 0);
    const wdt = (x1 - x0) * Math.cos(th);
    const near = Math.sin(th); // the free edge swings toward the camera
    const fx = x0 + wdt + near * 8;
    const B0 = L(x1, top), C0 = L(x1, 0);
    const ftop = lerp(B0.y, B0.y - 40, near) + (A.y - B0.y) * (1 - Math.cos(th)) * 0.5;
    const fbot = lerp(C0.y, C0.y + 46, near) + (D.y - C0.y) * (1 - Math.cos(th)) * 0.5;
    const face = Math.cos(th) >= 0;
    const col = '#4f7a5a';
    c.save();
    poly(c, [[A.x, A.y], [fx, ftop], [fx, fbot], [D.x, D.y]]);
    c.fillStyle = face ? col : U.shade(col, -0.2); c.fill();
    // panes (only meaningful while the face is visible and not too edge-on)
    const vis = Math.abs(Math.cos(th));
    if (vis > 0.12) {
      const P2 = (u, v) => ({ x: lerp(A.x, fx, u), y: lerp(lerp(A.y, ftop, u), lerp(D.y, fbot, u), v) });
      for (let i = 0; i < 2; i++) for (let j = 0; j < 3; j++) {
        const u0 = 0.14 + i * 0.38, u1 = u0 + 0.3, v0 = 0.08 + j * 0.17, v1 = v0 + 0.14;
        const a = P2(u0, v0), b = P2(u1, v0), cc = P2(u1, v1), d = P2(u0, v1);
        poly(c, [[a.x, a.y], [b.x, b.y], [cc.x, cc.y], [d.x, d.y]]);
        c.fillStyle = o < 0.02 ? P.outside : U.rgba('#fff4dc', 0.85); c.fill();
      }
      // lower panel inset + brass handle
      const a = P2(0.14, 0.62), b = P2(0.86, 0.62), cc = P2(0.86, 0.92), d = P2(0.14, 0.92);
      poly(c, [[a.x, a.y], [b.x, b.y], [cc.x, cc.y], [d.x, d.y]]);
      c.strokeStyle = U.shade(col, -0.25); c.lineWidth = 3; c.stroke();
      const hd = P2(0.86, 0.52);
      c.fillStyle = '#d9a940'; c.beginPath(); c.arc(hd.x, hd.y, 5, 0, TAU); c.fill();
    }
    // frame edge of the door leaf
    c.strokeStyle = U.shade(col, -0.35); c.lineWidth = 3;
    poly(c, [[A.x, A.y], [fx, ftop], [fx, fbot], [D.x, D.y]]); c.stroke();
    c.restore();
  };
  /** the brass bell over the door, swinging by angle a */
  K.bell = (c, a) => {
    const p = K.bellPivot();
    c.save();
    c.translate(p.x, p.y); c.rotate(a);
    c.strokeStyle = '#8a6420'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 6); c.stroke();
    const g = c.createLinearGradient(-9, 0, 9, 0);
    g.addColorStop(0, '#a7782c'); g.addColorStop(0.4, '#f0cf73'); g.addColorStop(1, '#8a6420');
    c.fillStyle = g;
    c.beginPath(); c.moveTo(-3, 6); c.quadraticCurveTo(-9, 10, -10, 22); c.lineTo(10, 22); c.quadraticCurveTo(9, 10, 3, 6); c.closePath(); c.fill();
    c.fillStyle = '#6b4c18'; c.beginPath(); c.arc(Math.sin(-a * 2) * 3, 24, 2.6, 0, TAU); c.fill();
    c.restore();
  };
  /** damped swing response to kicks at given times: kicks = [[t0, amp], ...] */
  K.swing = (t, kicks, freq = 2.6, damp = 2.4) => {
    let v = 0;
    for (const [t0, amp] of kicks) { const d = t - t0; if (d > 0) v += amp * Math.exp(-damp * d) * Math.sin(TAU * freq * d); }
    return v;
  };

  /** bead curtain: wooden beads + bamboo tubes on strings, a pink accent bead
   *  every so often. push(xStrand, yBead, i, j) → x displacement */
  K.beads = (c, t, push) => {
    const { x0, x1, top } = K.CURTAIN;
    const n = 8;
    for (let i = 0; i < n; i++) {
      const sx = x0 + 10 + i * ((x1 - x0 - 20) / (n - 1));
      const pts = [];
      const len = K.BACK_Y - top - 22 - (i % 3) * 6;
      for (let j = 0; j <= 16; j++) {
        const by = top + 8 + (j / 16) * len;
        const dx = (push ? push(sx, by, i, j) : 0) + Math.sin(t * 0.8 + i * 1.3) * 0.6 * (j / 16);
        pts.push([sx + dx, by]);
      }
      c.strokeStyle = 'rgba(40,26,16,0.55)'; c.lineWidth = 1;
      c.beginPath(); pts.forEach(([x, y], j) => (j ? c.lineTo(x, y) : c.moveTo(x, y))); c.stroke();
      for (let j = 1; j < pts.length; j++) {
        const [bx, by] = pts[j];
        const [ax, ay] = pts[j - 1];
        const kind = (i * 7 + j * 3) % 5;
        if (kind === 0) { // bamboo tube between beads
          c.strokeStyle = '#b9925a'; c.lineWidth = 3.4; c.lineCap = 'round';
          c.beginPath(); c.moveTo(lerp(ax, bx, 0.25), lerp(ay, by, 0.25)); c.lineTo(lerp(ax, bx, 0.85), lerp(ay, by, 0.85)); c.stroke();
        } else {
          const col = (i + j) % 7 === 0 ? '#e88f86' : kind === 2 ? '#7a4a2a' : kind === 3 ? '#a8693a' : '#d8a35e';
          c.fillStyle = col;
          c.beginPath(); c.ellipse(bx, by - 4, 3.4, 4.2, 0, 0, TAU); c.fill();
          c.fillStyle = 'rgba(255,240,210,0.35)';
          c.beginPath(); c.arc(bx - 1.1, by - 5.4, 1.1, 0, TAU); c.fill();
        }
      }
    }
  };

  /* ======================================================================
     SHOPKIT — the counter, the register, the flowers
     ====================================================================== */
  K.counter = (c, P) => {
    const { x0, x1, topF, topB, base } = K.COUNTER;
    // front face
    const g = c.createLinearGradient(0, topF, 0, base);
    g.addColorStop(0, P.counter); g.addColorStop(1, P.counterLo);
    c.fillStyle = g; c.fillRect(x0, topF, x1 - x0, base - topF);
    // inset panels
    const nP = 3, pw = (x1 - x0 - 40) / nP;
    for (let i = 0; i < nP; i++) {
      const px = x0 + 20 + i * pw;
      c.fillStyle = U.shade(P.counter, -0.1); c.fillRect(px + 8, topF + 22, pw - 16, base - topF - 52);
      c.fillStyle = U.shade(P.counter, 0.12); c.fillRect(px + 8, base - 32, pw - 16, 3);
      c.fillStyle = U.shade(P.counter, -0.28); c.fillRect(px + 8, topF + 22, pw - 16, 3);
    }
    // kick plate
    c.fillStyle = P.trim; c.fillRect(x0, base - 14, x1 - x0, 14);
    // left end grain
    c.fillStyle = U.shade(P.counter, -0.25); c.fillRect(x0 - 5, topF, 6, base - topF);
    // top surface (seen slightly from above)
    poly(c, [[x0 - 6, topF], [x1 + 4, topF], [x1 - 26, topB], [x0 - 2, topB]]);
    const gt = c.createLinearGradient(0, topB, 0, topF);
    gt.addColorStop(0, U.shade(P.counterTop, -0.08)); gt.addColorStop(1, P.counterTop);
    c.fillStyle = gt; c.fill();
    c.fillStyle = P.counterTopHi; c.fillRect(x0 - 6, topF - 2, x1 - x0 + 10, 3);
    c.fillStyle = U.shade(P.counter, -0.15); c.fillRect(x0 - 6, topF + 1, x1 - x0 + 10, 6);
    // contact shadow on the floor
    c.fillStyle = 'rgba(50,28,14,0.25)'; c.fillRect(x0 - 10, base - 2, x1 - x0 + 20, 8);
  };

  /** the old brass cash register. o = { drawer 0..1, ring 0..1 (crank),
   *  tabs: string shown in the window, pop 0..1 } */
  K.register = (c, o = {}) => {
    const x = K.REG.x, y = K.REG.y;
    c.save();
    c.translate(x, y); c.scale(0.84, 0.84); c.translate(-x, -y);
    const brass = (x0, x1) => { const g = c.createLinearGradient(x0, 0, x1, 0); g.addColorStop(0, '#6e4c14'); g.addColorStop(0.22, '#d9b04e'); g.addColorStop(0.4, '#f3d67e'); g.addColorStop(0.62, '#b5852e'); g.addColorStop(1, '#5e4010'); return g; };
    c.lineJoin = 'round';
    const dr = o.drawer || 0;
    // dark silhouette behind everything for a crisp outline
    c.fillStyle = '#3a2810';
    c.beginPath(); c.moveTo(x - 65, y + 2 + dr * 14); c.lineTo(x + 65, y + 2 + dr * 14); c.lineTo(x + 61, y - 26); c.lineTo(x + 53, y - 84); c.lineTo(x + 43, y - 114); c.quadraticCurveTo(x, y - 140, x - 43, y - 114); c.lineTo(x - 53, y - 84); c.lineTo(x - 61, y - 26); c.closePath(); c.fill();
    // drawer (slides toward camera = down a little)
    if (dr > 0.01) {
      c.fillStyle = '#3a2a1a'; c.fillRect(x - 54, y - 22, 108, 10 + dr * 8);
      c.fillStyle = '#7fae6a'; c.fillRect(x - 46, y - 18, 30, 6 + dr * 6); c.fillRect(x - 12, y - 18, 30, 6 + dr * 6);
      c.fillStyle = '#c8c8c0'; c.beginPath(); c.arc(x + 30, y - 14 + dr * 4, 4, 0, TAU); c.arc(x + 40, y - 13 + dr * 4, 4, 0, TAU); c.fill();
    }
    c.fillStyle = brass(x - 62, x + 62);
    c.fillRect(x - 62, y - 24 + dr * 14, 124, 24);
    c.fillStyle = '#5a3d10'; c.fillRect(x - 10, y - 14 + dr * 14, 20, 4);
    // body
    c.fillStyle = brass(x - 58, x + 58);
    c.beginPath(); c.moveTo(x - 58, y - 24); c.lineTo(x + 58, y - 24); c.lineTo(x + 50, y - 82); c.lineTo(x - 50, y - 82); c.closePath(); c.fill();
    // embossed scrolls
    c.strokeStyle = 'rgba(110,70,15,0.55)'; c.lineWidth = 1.4;
    for (const sx of [-1, 1]) { c.beginPath(); c.arc(x + sx * 40, y - 34, 6, 0, Math.PI * 1.6); c.stroke(); }
    // keys (3 rows)
    for (let r = 0; r < 3; r++) for (let k = 0; k < 6; k++) {
      const kx = x - 36 + k * 14.5 + r * 2, ky = y - 72 + r * 12;
      const pressed = o.key === r * 6 + k ? 2 : 0;
      c.fillStyle = '#3a2a1a'; c.beginPath(); c.arc(kx, ky + 1.5, 5, 0, TAU); c.fill();
      c.fillStyle = '#f3ead6'; c.beginPath(); c.arc(kx, ky + pressed, 4.2, 0, TAU); c.fill();
    }
    // crest + display window
    c.fillStyle = brass(x - 44, x + 44);
    c.beginPath(); c.moveTo(x - 46, y - 82); c.lineTo(x + 46, y - 82); c.lineTo(x + 40, y - 112); c.quadraticCurveTo(x, y - 136, x - 40, y - 112); c.closePath(); c.fill();
    c.fillStyle = '#2b2118'; rr(c, x - 30, y - 112, 60, 22, 3); c.fill();
    const pop = o.pop || 0;
    if (o.tabs && pop > 0) {
      c.save(); c.beginPath(); c.rect(x - 30, y - 112, 60, 22); c.clip();
      const chars = [...o.tabs];
      chars.forEach((ch, i) => {
        const k = clamp(pop * 1.6 - i * 0.18);
        const ty = y - 90 + (1 - U.E.outBack(k)) * 22;
        c.fillStyle = '#f6efdc'; c.fillRect(x - 28 + i * 14.5, ty - 19, 12.5, 18);
        c.fillStyle = '#2b2118'; c.font = Art.font(13, 'sans', 900); c.textAlign = 'center'; c.textBaseline = 'middle';
        c.fillText(ch, x - 21.8 + i * 14.5, ty - 9.5);
      });
      c.restore();
    }
    c.fillStyle = 'rgba(255,255,255,0.15)'; c.fillRect(x - 28, y - 110, 56, 5);
    // crank on the right side
    const ra = -0.4 + (o.ring || 0) * 2.2;
    c.strokeStyle = '#7a5518'; c.lineWidth = 5; c.lineCap = 'round';
    c.beginPath(); c.moveTo(x + 56, y - 48); c.lineTo(x + 56 + Math.cos(ra) * 22, y - 48 + Math.sin(ra) * 22); c.stroke();
    c.fillStyle = '#3a2a1a'; c.beginPath(); c.arc(x + 56 + Math.cos(ra) * 22, y - 48 + Math.sin(ra) * 22, 5, 0, TAU); c.fill();
    c.fillStyle = '#c9973a'; c.beginPath(); c.arc(x + 56, y - 48, 5, 0, TAU); c.fill();
    // a darker band between body and drawer + the "ka-ching" sparkle
    c.fillStyle = 'rgba(60,40,10,0.45)'; c.fillRect(x - 58, y - 27, 116, 3);
    if (o.ding > 0) {
      c.save();
      c.globalAlpha = clamp(o.ding);
      c.strokeStyle = '#fff3c4'; c.lineWidth = 3; c.lineCap = 'round';
      for (let i = 0; i < 5; i++) {
        const a = -Math.PI / 2 + (i - 2) * 0.42, r0 = 40 + (1 - o.ding) * 18, r1 = r0 + 16;
        c.beginPath(); c.moveTo(x + Math.cos(a) * r0, y - 118 + Math.sin(a) * r0 * 0.7); c.lineTo(x + Math.cos(a) * r1, y - 118 + Math.sin(a) * r1 * 0.7); c.stroke();
      }
      c.restore();
    }
    c.restore();
  };

  const TULIP_COL = { petal: '#ff8a3d', tip: '#ffd36b', inner: '#c2410c' };
  const DUSTY_COL = { petal: '#d8c25a', tip: '#efe2a0', inner: '#a08a2a' };
  K.TULIP_COL = TULIP_COL; K.DUSTY_COL = DUSTY_COL;
  /** the $10 tulip in a terracotta pot. (x,y) = pot bottom; s ~ 0.9 on the counter */
  K.tulip = (c, x, y, s, t, o = {}) => {
    c.save();
    c.translate(x, y); c.scale(s, s); c.translate(-x, -y);
    const rim = pot(c, x, y, 42, 36, 'terra');
    c.fillStyle = '#5a3a26'; c.beginPath(); c.ellipse(x, rim + 3, 20, 4, 0, 0, TAU); c.fill();
    Art.flower(c, { x, y: rim + 4, s: 0.5, kind: 'tulip', colors: TULIP_COL, stemH: 130, t, sway: o.sway === undefined ? 0.15 : o.sway, seed: 4, bloom: 0.92 });
    // tidy price tag
    c.fillStyle = '#fbf6ea'; c.save(); c.translate(x + 14, rim + 16); c.rotate(0.12); c.fillRect(-12, -7, 24, 14);
    c.fillStyle = '#3b2a25'; c.font = Art.font(10, 'sans', 800); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('$10', 0, 0.5); c.restore();
    c.restore();
  };
  /** the $200 flower: droopy, dusty, pale yellow; chipped pot, cobweb, tag.
   *  o = { droop, dust (0..1), tag:true } */
  K.dusty = (c, x, y, s, t, o = {}) => {
    c.save();
    c.translate(x, y); c.scale(s, s); c.translate(-x, -y);
    const pc = '#a98a72';
    const rim = pot(c, x, y, 46, 38, U.mix(pc, '#b9ad98', 0.35));
    // the chip out of the rim + a crack
    c.fillStyle = U.shade(pc, -0.35);
    c.beginPath(); c.moveTo(x + 10, rim); c.lineTo(x + 20, rim); c.lineTo(x + 15, rim + 7); c.closePath(); c.fill();
    c.strokeStyle = U.shade(pc, -0.4); c.lineWidth = 1.2;
    c.beginPath(); c.moveTo(x + 15, rim + 7); c.lineTo(x + 12, rim + 15); c.lineTo(x + 16, rim + 22); c.stroke();
    c.fillStyle = '#6b5440'; c.beginPath(); c.ellipse(x, rim + 3, 21, 4, 0, 0, TAU); c.fill();
    const f = Art.flower(c, { x, y: rim + 4, s: 0.52, kind: 'wild', droop: o.droop === undefined ? 0.5 : o.droop, dust: o.dust === undefined ? 1 : o.dust, colors: DUSTY_COL, stemH: 120, t, sway: 0.1, seed: 9, face: 0.65 });
    // cobweb strung between the rim and the stem
    if ((o.dust === undefined ? 1 : o.dust) > 0.3) {
      c.strokeStyle = 'rgba(240,236,226,0.55)'; c.lineWidth = 0.8;
      const ax = x - 22, ay = rim + 1, bx = x - 2, by = rim - 40;
      for (let i = 0; i <= 4; i++) { const k = i / 4; c.beginPath(); c.moveTo(ax, ay); c.lineTo(lerp(ax, bx, 0.5 + k * 0.5), lerp(ay, by, k)); c.stroke(); }
      for (let r = 8; r < 34; r += 8) { c.beginPath(); c.arc(ax, ay, r, -1.4, -0.2); c.stroke(); }
    }
    // dust specks on the pot
    c.fillStyle = 'rgba(200,190,170,0.6)';
    for (let i = 0; i < 9; i++) c.fillRect(x - 18 + U.hash(i, 5) * 36, rim + 6 + U.hash(i, 6) * 26, 1.6, 1.6);
    // the hand-written tag on a string. 'old': "$4" (as it sat for weeks);
    // 'new' (default): the $4 crossed out and "$200" scrawled in red
    if (o.tag !== false) {
      c.strokeStyle = '#8a7a60'; c.lineWidth = 1;
      c.beginPath(); c.moveTo(x - 20, rim + 2); c.quadraticCurveTo(x - 30, rim + 10, x - 30, rim + 16); c.stroke();
      c.save(); c.translate(x - 32, rim + 26); c.rotate(-0.16);
      c.fillStyle = '#f1e6c8'; c.beginPath(); c.moveTo(-18, -10); c.lineTo(14, -10); c.lineTo(20, 0); c.lineTo(14, 10); c.lineTo(-18, 10); c.closePath(); c.fill();
      c.fillStyle = '#3b2a25'; c.beginPath(); c.arc(15, 0, 1.8, 0, TAU); c.fill();
      c.font = Art.font(10, 'hand', 700); c.textAlign = 'center'; c.textBaseline = 'middle';
      if (o.tag === 'old') {
        c.fillStyle = '#3b2a25'; c.font = Art.font(14, 'hand', 700); c.fillText('$4', -2, 0.5);
      } else {
        c.fillStyle = 'rgba(59,42,37,0.6)'; c.fillText('$4', -9, -4);
        c.strokeStyle = '#b8352a'; c.lineWidth = 1.2; c.beginPath(); c.moveTo(-15, -3); c.lineTo(-3, -5); c.stroke();
        c.fillStyle = '#b8352a'; c.font = Art.font(13, 'hand', 700); c.fillText('$200', 0, 4);
      }
      c.restore();
    }
    c.restore();
    return { head: { x: x + (f.head.x - x) * s, y: y + (f.head.y - y) * s } };
  };

  /* ======================================================================
     SHOPKIT — walkers & muddy footprints (deterministic from t)
     ====================================================================== */
  const SK = { thigh: 58, shin: 56 };
  /** foot positions for Art.person's walk pose (mirrors art.js) */
  K.legs = (o) => {
    const look = typeof o.look === 'string' ? Art.CAST[o.look] : o.look;
    const lank = look.lanky ? 1.1 : 1;
    const th = SK.thigh * lank, sh = SK.shin * lank;
    const S = (o.s || 1) * (look.height || 1);
    const st = o.stride === undefined ? 1 : o.stride;
    const ph = o.walk || 0;
    let hipY = -(th + sh + 4);
    const sw = 0.42 * st;
    const aF = Math.sin(ph) * sw, aB = -aF;
    const kF = -(0.12 + Math.max(0, Math.cos(ph)) * 0.75 * st);
    const kB = -(0.12 + Math.max(0, -Math.cos(ph)) * 0.75 * st);
    hipY += Math.abs(Math.sin(ph)) * 5 * st - 3 * st;
    const leg = (hx, a1, k) => ({ x: hx + Math.sin(a1) * th + Math.sin(a1 + k) * sh, y: hipY + Math.cos(a1) * th + Math.cos(a1 + k) * sh, a2: a1 + k });
    const F = leg(3, aF, kF), B = leg(-3, aB, kB);
    const f = o.facing === undefined ? 1 : o.facing;
    const wx = (p) => ({ x: o.x + p.x * S * f, y: o.y + p.y * S, a2: p.a2 });
    return { F: wx(F), B: wx(B), S };
  };
  /**
   * Build a walker: keys = [[t, x, y, ease?], ...] floor positions over time.
   * Precomputes walk phase (from distance, so feet don't skate), stride (from
   * speed) and heel strikes → footprints. Returns { at(t) → pose, prints }.
   */
  K.walker = (def) => {
    const look = Art.CAST[def.look];
    const lank = look.lanky ? 1.1 : 1;
    let posFn = def.pos, t0 = def.t0, t1 = def.t1;
    if (!posFn) {
      const keys = def.keys.map((k) => [k[0], [k[1], k[2]], k[3] || 'inOutSine']);
      t0 = keys[0][0]; t1 = keys[keys.length - 1][0];
      posFn = (t) => U.keys(t, keys);
    }
    const dt = 1 / 120, n = Math.ceil((t1 - t0) / dt) + 2;
    const X = new Float64Array(n), Y = new Float64Array(n), PH = new Float64Array(n), ST = new Float64Array(n);
    const prints = [];
    const vNom = def.vNom || 190;
    let ph = def.ph0 || 0;
    let prev = posFn(t0);
    let lastF = Math.floor((ph - Math.PI / 2) / TAU), lastB = Math.floor((ph - 1.5 * Math.PI) / TAU);
    let step = 0;
    for (let i = 0; i < n; i++) {
      const t = t0 + i * dt;
      const p = posFn(t);
      const d = Math.hypot(p[0] - prev[0], p[1] - prev[1]);
      const speed = d / dt;
      const s = (def.s || K.sAt)(p[1]);
      const S = s * (look.height || 1) * lank;
      const st = Math.pow(clamp(speed / vNom), 0.55) * (def.strideMax || 1);
      ph += d / (29.7 * S * Math.max(st, 0.22));
      X[i] = p[0]; Y[i] = p[1]; PH[i] = ph; ST[i] = st;
      // heel strikes → prints
      const cf = Math.floor((ph - Math.PI / 2) / TAU), cb = Math.floor((ph - 1.5 * Math.PI) / TAU);
      if (i > 0 && st > 0.25) {
        const f = def.facing === undefined ? 1 : def.facing;
        const mk = (which) => {
          const L = K.legs({ look: def.look, x: p[0], y: p[1], s, walk: ph, stride: st, facing: f });
          const foot = which === 'F' ? L.F : L.B;
          const dir = Math.atan2(p[1] - prev[1], p[0] - prev[0]);
          prints.push({ t, x: foot.x + Math.cos(dir) * 6 * s, y: p[1] + (which === 'F' ? 3.5 : -3.5) * s, s, dir, who: def.look, n: step++, side: which, mud: def.mud === undefined ? 1 : def.mud });
        };
        if (cf !== lastF) mk('F');
        if (cb !== lastB) mk('B');
      }
      lastF = cf; lastB = cb;
      prev = p;
    }
    const idx = (t) => clamp((t - t0) / dt, 0, n - 1);
    return {
      t0, t1, prints, look: def.look,
      at(t) {
        const f = idx(t), i = Math.floor(f), j = Math.min(n - 1, i + 1), k = f - i;
        const x = lerp(X[i], X[j], k), y = lerp(Y[i], Y[j], k);
        const st = lerp(ST[i], ST[j], k);
        return { x, y, s: (def.s || K.sAt)(y), walk: lerp(PH[i], PH[j], k), stride: st, moving: st > 0.03 && t > t0 && t < t1 };
      },
    };
  };
  /** mud footprints. list items {t,x,y,s,dir,n,who,mud}; alphaFn(p) → 0..1.
   *  Each print is a boot sole lying on the floor (drawn in floor space,
   *  then squashed by the floor's foreshortening). */
  const SOLE = new Path2D('M14,0 C14,-5 10,-7.5 4,-7.5 C-1,-7.5 -3,-5.5 -5,-5 L-6,-5 C-7,-5 -7,5 -6,5 L-5,5 C-3,5.5 -1,7.5 4,7.5 C10,7.5 14,5 14,0 Z');
  const HEEL = new Path2D('M-9,-5.5 C-12,-5.5 -16,-5 -16,0 C-16,5 -12,5.5 -9,5.5 C-8,5.5 -7.6,3 -7.6,0 C-7.6,-3 -8,-5.5 -9,-5.5 Z');
  K.drawPrints = (c, list, t, alphaFn) => {
    for (const p of list) {
      if (p.t > t) continue;
      let a = (0.7 * Math.pow(0.88, p.n) + 0.14) * (p.mud === undefined ? 1 : p.mud);
      a *= clamp((t - p.t) / 0.06);
      if (alphaFn) a *= alphaFn(p);
      if (a < 0.01) continue;
      const s = p.s * 1.05;
      const th = Math.atan2(Math.sin(p.dir) / 0.42, Math.cos(p.dir)); // direction on the floor plane
      c.save();
      c.translate(p.x, p.y);
      c.scale(s, s * 0.42);
      c.rotate(th + (p.side === 'F' ? 0.06 : -0.06));
      c.globalAlpha = a;
      c.fillStyle = '#5b3d26';
      c.fill(SOLE); c.fill(HEEL);
      // lugs: rows of little bars that read as tread
      c.fillStyle = 'rgba(30,18,8,0.55)';
      for (let i = 0; i < 4; i++) { const x = -2 + i * 4; c.fillRect(x, -5.2, 1.6, 4.2); c.fillRect(x + 1.2, 1.0, 1.6, 4.2); }
      c.fillRect(-14, -3.5, 1.6, 7); c.fillRect(-11, -3.5, 1.6, 7);
      // a smear and a couple of mud crumbs (more on the first, muddiest steps)
      c.fillStyle = '#5b3d26';
      const crumbs = p.n < 3 ? 5 : 2;
      for (let i = 0; i < crumbs; i++) {
        const r1 = U.hash(p.n * 7 + i, p.who.charCodeAt(1) + 3), r2 = U.hash(p.n * 7 + i, 91);
        c.globalAlpha = a * (0.5 + 0.5 * r2);
        c.beginPath(); c.arc(-20 + r1 * 40, (r2 - 0.5) * 22, 0.9 + r2 * (p.n < 3 ? 2.6 : 1.4), 0, TAU); c.fill();
      }
      c.restore();
    }
  };

  /* ======================================================================
     SHOPKIT — little props held in hands (local units: +x forward)
     ====================================================================== */
  K.mug = (c, tilt = 0, steam = 0, t = 0) => {
    c.save();
    c.rotate(-tilt);
    c.fillStyle = '#b5543a'; rr(c, 2, -18, 20, 22, 4); c.fill();
    c.strokeStyle = '#b5543a'; c.lineWidth = 4; c.beginPath(); c.arc(1, -7, 6, Math.PI * 0.5, Math.PI * 1.5); c.stroke();
    c.fillStyle = '#d06a4e'; c.fillRect(4, -16, 4, 18);
    c.fillStyle = '#6b3a1e'; c.beginPath(); c.ellipse(12, -18, 9.5, 2.6, 0, 0, TAU); c.fill();
    c.restore();
    if (steam > 0.02) {
      c.save(); c.strokeStyle = `rgba(255,255,255,${0.35 * steam})`; c.lineWidth = 2; c.lineCap = 'round';
      for (let i = 0; i < 2; i++) {
        const ph = t * 1.4 + i * 1.7;
        c.beginPath();
        for (let k = 0; k <= 10; k++) { const yy = -22 - k * 4.2, xx = 9 + i * 7 + Math.sin(ph + k * 0.6) * 3.5 * (k / 10); k ? c.lineTo(xx, yy) : c.moveTo(xx, yy); }
        c.stroke();
      }
      c.restore();
    }
  };
  K.phone = (c, o = {}) => { // held upright, screen toward the holder
    c.save();
    c.rotate(o.rot || -0.2);
    c.fillStyle = '#1d1f26'; rr(c, -5, -24, 14, 26, 3); c.fill();
    c.fillStyle = o.screen || '#6fb7ff'; c.globalAlpha = 0.9; rr(c, -3.5, -22, 11, 21, 2); c.fill();
    c.globalAlpha = 1;
    if (o.rec) { c.fillStyle = '#ff3b3b'; c.beginPath(); c.arc(2, -27, 2.4, 0, TAU); c.fill(); }
    c.restore();
  };

  /** straight walk with a trapezoidal speed profile → { pos(t), t0, t1, v } */
  K.trap = (t0, t1, x0, y0, x1, y1, acc = 0.2, dec = 0.7) => {
    const T = t1 - t0, dist = Math.hypot(x1 - x0, y1 - y0);
    const v = dist / Math.max(0.01, T - (acc + dec) / 2);
    const pos = (t) => {
      const tau = clamp(t - t0, 0, T);
      let s;
      if (tau < acc) s = v * tau * tau / (2 * acc);
      else if (tau <= T - dec) s = v * (tau - acc / 2);
      else { const r = T - tau; s = dist - v * r * r / (2 * dec); }
      const k = dist > 0 ? clamp(s / dist) : 0;
      return [lerp(x0, x1, k), lerp(y0, y1, k)];
    };
    return { pos, t0, t1, vNom: v };
  };

  /** big monstera in a pot (the plant "me" half-hides behind). (x,y) pot bottom */
  K.monstera = (c, x, y, s, t) => {
    c.save();
    c.translate(x, y); c.scale(s, s);
    const leaves = [[-0.95, 170, 70, -0.5], [-0.45, 230, 84, -0.2], [0.05, 250, 90, 0.05], [0.55, 215, 82, 0.35], [1.0, 160, 66, 0.6], [-0.15, 150, 64, -0.1]];
    leaves.forEach(([a, len, sz, tilt], i) => {
      const sw = Math.sin(t * 0.8 + i * 1.7) * 0.015;
      const ex = Math.sin(a + sw) * len, ey = -70 - Math.cos(a + sw) * len * 0.9;
      c.strokeStyle = '#3f6e3a'; c.lineWidth = 4; c.lineCap = 'round';
      c.beginPath(); c.moveTo(0, -60); c.quadraticCurveTo(ex * 0.4, -60 + ey * 0.6, ex, ey); c.stroke();
      c.save();
      c.translate(ex, ey); c.rotate(a * 0.8 + tilt + sw);
      const col = i % 2 ? '#3e7b45' : '#478a4d';
      c.fillStyle = col;
      c.beginPath();
      c.moveTo(0, sz * 0.15);
      c.bezierCurveTo(sz * 0.95, sz * 0.1, sz * 0.85, -sz * 1.05, 0, -sz * 0.95);
      c.bezierCurveTo(-sz * 0.85, -sz * 1.05, -sz * 0.95, sz * 0.1, 0, sz * 0.15);
      c.fill();
      // fenestrations: darker slits + midrib
      c.strokeStyle = U.shade(col, -0.32); c.lineWidth = 2.2;
      c.beginPath(); c.moveTo(0, sz * 0.1); c.lineTo(0, -sz * 0.9); c.stroke();
      c.lineWidth = 3;
      for (let k = 0; k < 3; k++) {
        const yy = -sz * (0.2 + k * 0.24);
        c.beginPath(); c.moveTo(sz * 0.62 - k * 4, yy - 4); c.lineTo(sz * 0.3, yy + 2); c.stroke();
        c.beginPath(); c.moveTo(-sz * 0.62 + k * 4, yy - 4); c.lineTo(-sz * 0.3, yy + 2); c.stroke();
      }
      c.fillStyle = 'rgba(255,255,240,0.12)';
      c.beginPath(); c.ellipse(sz * 0.25, -sz * 0.6, sz * 0.18, sz * 0.3, 0.4, 0, TAU); c.fill();
      c.restore();
    });
    c.restore();
    c.save(); c.translate(x, y); c.scale(s, s); c.translate(-x, -y);
    pot(c, x, y, 92, 70, 'cream');
    c.fillStyle = 'rgba(40,20,10,0.22)'; c.beginPath(); c.ellipse(x, y + 2, 52, 8, 0, 0, TAU); c.fill();
    c.restore();
  };
  /** a tall bucket of pampas grass + eucalyptus. (x,y) bucket bottom */
  K.pampas = (c, x, y, s, t) => {
    c.save();
    c.translate(x, y); c.scale(s, s); c.translate(-x, -y);
    for (let i = 0; i < 6; i++) {
      const a = (i - 2.5) * 0.17 + Math.sin(t * 0.7 + i) * 0.01;
      const L = 230 + U.hash(i, 31) * 70;
      const tx = x + Math.sin(a) * L, ty = y - 60 - Math.cos(a) * L;
      c.strokeStyle = '#b8a27a'; c.lineWidth = 2;
      c.beginPath(); c.moveTo(x + (i - 2.5) * 4, y - 50); c.quadraticCurveTo(x + Math.sin(a) * L * 0.5, y - 60 - L * 0.5, tx, ty); c.stroke();
      // feathery plume
      c.fillStyle = i % 2 ? '#efe2c4' : '#e6d4ae';
      c.save(); c.translate(tx, ty); c.rotate(a);
      c.beginPath(); c.ellipse(0, 26, 13, 46, 0, 0, TAU); c.fill();
      c.fillStyle = 'rgba(255,255,255,0.25)'; c.beginPath(); c.ellipse(-4, 16, 5, 30, 0, 0, TAU); c.fill();
      c.restore();
    }
    bunch(c, x, y - 52, 80, 150, 'green', 77, '#8fb3a0');
    bucket(c, x, y, 66, 64);
    c.restore();
  };

  /** scissors (local units, at the hand, +x forward). open 0..1 */
  K.scissors = (c, open = 0) => {
    const a = 0.08 + open * 0.38;
    c.save();
    c.lineCap = 'round';
    for (const sgn of [1, -1]) {
      c.save(); c.rotate(-0.25 + sgn * a / 2);
      c.strokeStyle = '#cfd5da'; c.lineWidth = 3.2;
      c.beginPath(); c.moveTo(4, 0); c.lineTo(30, 0); c.stroke();
      c.strokeStyle = '#4f7a5a'; c.lineWidth = 3;
      c.beginPath(); c.ellipse(-3, sgn * 2, 6, 4, 0, 0, TAU); c.stroke();
      c.restore();
    }
    c.fillStyle = '#8a9096'; c.beginPath(); c.arc(4, 0, 2, 0, TAU); c.fill();
    c.restore();
  };
  /** a little stack of bills. (local or world units) */
  K.bills = (c, x, y, s = 1, fan = 0) => {
    c.save(); c.translate(x, y); c.scale(s, s);
    for (let i = 0; i < 4; i++) {
      c.save(); c.rotate((i - 1.5) * 0.12 * fan + (i - 1.5) * 0.04);
      c.fillStyle = i % 2 ? '#86b36f' : '#7aa863';
      c.fillRect(-17, -7 - i * 1.4, 34, 14);
      c.strokeStyle = '#4f7a40'; c.lineWidth = 1; c.strokeRect(-14, -5 - i * 1.4, 28, 10);
      c.fillStyle = '#5b8a4a'; c.beginPath(); c.arc(0, -i * 1.4, 3.4, 0, TAU); c.fill();
      c.restore();
    }
    c.restore();
  };
  /** a puff of breath / dust. k 0..1 life, dir ±1, drop = how much it sinks */
  K.puff = (c, x, y, k, dir = 1, size = 1, col = '#ffffff', drop = 0.3) => {
    if (k <= 0 || k >= 1) return;
    c.save();
    const e = U.E.outCubic(k);
    const cx = x + dir * (10 + e * 46) * size, cy = y + e * 22 * drop * size;
    const a = (1 - U.E.inQuad(k)) * 0.82;
    const lobes = [[0, 0, 11], [dir * 12, -4, 9], [dir * -10, 3, 8], [dir * 4, 7, 8], [dir * 20, 4, 6.5]];
    // soft darker underside, then the lit body
    c.globalAlpha = a * 0.35;
    c.fillStyle = U.shade(col, -0.25);
    c.beginPath(); for (const [lx, ly, r] of lobes) { const rr0 = r * size * (0.7 + e * 0.6); c.moveTo(cx + lx * size + rr0, cy + ly * size + 2.5 * size); c.arc(cx + lx * size, cy + ly * size + 2.5 * size, rr0, 0, TAU); } c.fill();
    c.globalAlpha = a;
    c.fillStyle = col;
    c.beginPath(); for (const [lx, ly, r] of lobes) { const rr0 = r * size * (0.7 + e * 0.6); c.moveTo(cx + lx * size + rr0, cy + ly * size); c.arc(cx + lx * size, cy + ly * size, rr0, 0, TAU); } c.fill();
    // a little trailing wisp back to the mouth
    c.globalAlpha = a * 0.6 * (1 - e);
    c.strokeStyle = col; c.lineWidth = 3 * size; c.lineCap = 'round';
    c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(lerp(x, cx, 0.5), y + 6 * size, cx - dir * 8 * size, cy); c.stroke();
    c.restore();
  };

  /**
   * Art.person with a quick cut-out style turn: around each time in `flips`
   * (when the caller switches `facing`) the figure squashes horizontally
   * to ~40% and back over 2×w seconds, so a facing change never pops (and
   * never collapses into a one-pixel sliver). Anchors are corrected.
   */
  K.turnK = (t, flips, w = 0.09) => {
    let k = 1;
    if (flips) for (const tf of flips) { const d = Math.abs(t - tf); if (d < w) k = Math.min(k, 0.4 + 0.6 * U.smooth(d / w)); }
    return k;
  };
  K.person = (ctx, o, flips, w = 0.09) => {
    const k = K.turnK(o.t || 0, flips, w);
    o.facing = o.facing === undefined ? 1 : o.facing;
    if (k > 0.995) { const A = Art.person(ctx, o); A.facing = o.facing; return A; }
    ctx.save(); ctx.translate(o.x, 0); ctx.scale(k, 1); ctx.translate(-o.x, 0);
    const A = Art.person(ctx, o);
    ctx.restore();
    for (const key of ['head', 'top', 'mouth', 'handF', 'handB', 'shoulder', 'chest', 'hip']) if (A[key]) A[key].x = o.x + (A[key].x - o.x) * k;
    A.facing = o.facing;
    return A;
  };

  window.ShopKit = K;

  /* ======================================================================
     SCENE 11
     ====================================================================== */
  const D = 69.6;
  const PD = K.PAL.day;
  const muddy = (k) => Object.assign({}, Art.CAST[k], { shoes: U.mix(Art.CAST[k].shoes, '#5b3d26', 0.72) });
  const LOOK = { h1: muddy('h1'), h2: muddy('h2'), h4: muddy('h4') };
  const SPOT = { h1: [990, 879], h2: [840, 885], h4: [690, 876] };
  const EMB_Y = 812;
  const DUSTY_AT = 1150, TULIP_AT = 1240; // where the flowers end up on the counter
  const DOOR_T = 3.0; // the moment the door bangs open (the bored establishing beat comes first)

  // ---- the hikers barge in, one after another ----
  const ENTER = {
    h1: K.walker(Object.assign({ look: 'h1' }, K.trap(DOOR_T + 0.07, DOOR_T + 3.85, 92, 840, SPOT.h1[0], SPOT.h1[1], 0.12, 0.85))),
    h2: K.walker(Object.assign({ look: 'h2' }, K.trap(DOOR_T + 0.57, DOOR_T + 4.4, 96, 840, SPOT.h2[0], SPOT.h2[1], 0.12, 0.85))),
    h4: K.walker(Object.assign({ look: 'h4' }, K.trap(DOOR_T + 1.07, DOOR_T + 4.8, 100, 840, SPOT.h4[0], SPOT.h4[1], 0.12, 0.85))),
  };
  const PRINTS = [].concat(ENTER.h1.prints, ENTER.h2.prints, ENTER.h4.prints).sort((a, b) => a.y - b.y);
  K.PRINTS_IN = PRINTS;
  K.SPOT = SPOT;
  // ---- Embarrassment's trudge to the back room, and back ----
  const TRUDGE = K.walker(Object.assign({ look: 'emb', strideMax: 1.12, s: () => K.sAt(EMB_Y) * 1.07 }, K.trap(34.2, 37.4, 1300, EMB_Y, 1872, 800, 0.5, 0.05)));
  const RETURN = K.walker(Object.assign({ look: 'emb', facing: -1, strideMax: 1.1, s: () => K.sAt(EMB_Y) * 1.07 }, K.trap(41.9, 44.0, 1716, 805, 1290, EMB_Y, 0.05, 0.5)));
  const EMB_S = K.sAt(EMB_Y) * 1.07; // he stands on a little step behind the counter

  /* ---------------- words ---------------- */
  const CAP = [
    [1.0, 5.4, '…some of the hikers show up at Embarrassment’s flower shop,'],
    [5.8, 8.8, 'tracking mud all over the floor.'],
    [19.8, 23.0, 'Embarrassment, the shop owner, rolls his eyes.'],
    [33.0, 37.0, 'Embarrassment sighs, trudges to the back of the shop,'],
    [37.5, 41.7, 'and grabs some random flower he’s been ignoring for weeks.'],
    [49.9, 52.9, 'The hikers don’t even flinch.'],
    [53.5, 58.95, 'They hand over the money, grinning like they’ve just bought the secret to happiness.'],
    [59.4, 63.2, 'They gather around the flower, beaming and congratulating themselves.'],
  ];
  const BUB = [
    [9.0, 12.0, 'Hey, we’re here for the best flower.', { who: 'h1' }],
    [12.4, 17.0, 'We heard you were talking about how meaningful his flower was.', { who: 'h2', maxW: 600 }],
    [17.3, 19.5, 'We want that.', { who: 'h2' }],
    [23.4, 26.6, 'Sure, here’s a flower. That’ll be $10.', { who: 'emb', maxW: 420 }],
    [27.0, 29.6, '$10? That’s not meaningful enough.', { who: 'h1', maxW: 470 }],
    [29.9, 32.7, 'We want something rare, something special!', { who: 'h4', maxW: 460 }],
    [44.3, 46.5, 'Here.', { who: 'emb' }],
    [46.8, 49.6, 'This one’s very rare. $200.', { who: 'emb', maxW: 440 }],
    [63.3, 68.1, 'This is it! This is the meaning we’ve been looking for!', { who: 'all', style: 'shout', maxW: 560, size: 36 }],
  ];
  const talking = (t, who) => Math.max(Art.talkingAt(t, BUB, who), who !== 'emb' && who !== 'me' ? Art.talkingAt(t, BUB, 'all') : 0);

  /* ---------------- little time helpers ---------------- */
  const E = (t, a, b, e) => U.ease(t, a, b, e || 'inOutSine');
  const win = (t, a, b, fi = 0.25, fo = 0.25) => U.fade(t, a, b, fi, fo);
  const kicks = (list) => list; // readability
  const BELL = kicks([[DOOR_T + 0.05, 0.55], [DOOR_T + 3.07, 0.22]]);
  const GRIN = (t, d0) => E(t, 53.35 + d0, 53.95 + d0, 'outBack');
  /** an index finger drawn at a hand (holdF, person-local units), along direction (dx, dy) */
  const finger = (dx, dy, skin, len = 15) => (c) => {
    const n = Math.hypot(dx, dy) || 1;
    c.strokeStyle = skin; c.lineWidth = 4.6; c.lineCap = 'round';
    c.beginPath(); c.moveTo(dx / n * 3, dy / n * 3); c.lineTo(dx / n * len, dy / n * len); c.stroke();
  };
  /** a camera flash: instant attack on the click, fast exponential decay */
  const pulse = (t, t0, tau) => { if (t < t0) return 0; const v = Math.exp(-(t - t0) / tau); return v < 0.01 ? 0 : v; };
  const SNAPS = [24.45, 45.0, 61.7]; // h4's phone clicks (tulip, dusty flower, the selfie)
  /** the end of the scene: everyone looks into h4's phone, then straight into the shout */
  const SELFIE = (t) => win(t, 60.9, 63.4, 0.3, 0.32);
  const CHEER = (t) => E(t, 63.05, 63.5, 'outBack');
  /** the high-five: h4's free (back) hand meets h2's front hand at HF.m on the slap */
  const HF = { t: 56.2, m: { x: 772, y: 607 } }; // up between their heads (as high as their reach allows)
  function highFive(t, o, side, hand) {
    const up = win(t, 55.62, 56.85, 0.36, 0.42);
    const gap = t < HF.t ? 42 * (1 - E(t, 55.88, HF.t, 'inQuad')) : 10 * E(t, HF.t, HF.t + 0.16, 'outQuad');
    const wind = t < HF.t ? 18 * (1 - E(t, 55.88, HF.t, 'inQuad')) : 0;
    const look = typeof o.look === 'string' ? Art.CAST[o.look] : o.look;
    const f = o.facing || 1, S = o.s * (look.height || 1);
    // rest = where that hand hangs in the stand pose (so the IK takes over without a pop)
    const rest = hand === 'F' ? { x: o.x + f * 21 * S, y: o.y - 103 * S } : { x: o.x - f * 7 * S, y: o.y - 100 * S };
    const tgt = { x: HF.m.x + side * gap, y: HF.m.y - wind };
    // the hand swings up on an outward arc (toward the partner), never across the face
    const ctl = { x: lerp(rest.x, tgt.x, 0.5) + f * 70, y: lerp(rest.y, tgt.y, 0.55) };
    const u = up, v = 1 - u;
    const p = { x: v * v * rest.x + 2 * u * v * ctl.x + u * u * tgt.x, y: v * v * rest.y + 2 * u * v * ctl.y + u * u * tgt.y };
    if (hand === 'F') o.reachF = p; else o.reachB = p;
    o.lean = (o.lean || 0) + 0.21 * up;
    return up;
  }

  /* ======================================================================
     CHARACTERS — each returns Art.person options for time t
     ====================================================================== */
  const ROLL = (t) => win(t, 20.25, 21.95, 0.22, 0.3); // eye-roll envelope

  function embState(t) {
    const o = { look: 'emb', t, facing: -1, y: EMB_Y, s: EMB_S, seed: 5, head: { turn: 0.28, tilt: 0 }, face: { eyes: 'flat', smile: -0.08 } };
    let x = 1340;
    const ex = { held: null, heldAbove: false, layer: 'counter' };
    // --- position along the counter
    x = U.keys(t, [[0, 1340], [22.3, 1340], [22.7, 1300, 'inOutSine'], [53.85, 1300], [54.35, 1432, 'inOutSine'], [55.0, 1432], [55.45, 1300, 'inOutSine']]);
    if (t >= 41.9) x = U.keys(t, [[41.9, 1716], [44.0, 1290]]);
    if (t >= 44.0 && t < 53.85) x = 1290;
    if (t >= 53.85) x = U.keys(t, [[53.85, 1290], [54.35, 1432, 'inOutSine'], [55.0, 1432], [55.45, 1300, 'inOutSine']]);
    o.x = x;
    // breathing idle on the counter: hands resting just above its back edge
    const restF = { x: x - 70, y: 662 }, restB = { x: x - 44, y: 664 };
    o.reachF = restF; o.reachB = restB;
    // ---- 0 – 6.0: trimming stems, bored ----
    if (t < 6.2) {
      let bump = 0; for (const s0 of SNIPS) bump = Math.max(bump, U.bump(t, s0, 0.16));
      const stop = E(t, DOOR_T + 0.05, DOOR_T + 0.35); // freezes when the door bangs
      o.reachF = { x: x - 74 + bump * 3, y: 650 + bump * 3 };
      o.reachB = { x: x - 52, y: 660 };
      o.holdF = (c) => K.scissors(c, (1 - bump) * (1 - stop * 0.6) * 0.9 + 0.1);
      o.face = { eyes: 'flat', smile: -0.12, lookY: lerp(0.65, -0.1, stop), lookX: stop * 0.6 };
      o.head.tilt = lerp(0.12, 0.02, stop);
      o.head.turn = lerp(0.22, 0.3, stop);
      if (t > 5.6) { const k = E(t, 5.6, 6.2); o.reachF = { x: lerp(x - 74, restF.x, k), y: lerp(650, 682, U.bump(t, 5.9, 0.3)) * 0 + lerp(650, restF.y, k) }; }
    }
    // ---- listening (flat, slow blinks) ----
    if (t >= 6.2 && t < 19.9) {
      o.face = { eyes: 'flat', smile: -0.1, lookX: 0.4 };
      // the tiniest eyebrow lift at "his flower"
      o.face.browUp = 0.5 * win(t, 15.0, 16.6, 0.2, 0.4);
    }
    // ---- 19.9 – 22.3: the eye-roll ----
    if (t >= 19.9 && t < 22.4) {
      const r = ROLL(t);
      // a real roll: the pupils sweep up and over in an arc (side → top → other
      // side) while the head lolls back with them; a blink-frame on either side
      // of the roll hides the switch between the lidded and the rolled eyes.
      const R0 = 20.36, R1 = 21.8, e = U.E.inOutSine(clamp((t - R0) / (R1 - R0)));
      const rolled = t > R0 && t < R1;
      const blinkFrame = Math.abs(t - R0) < 0.045 || Math.abs(t - R1) < 0.045;
      o.face = {
        eyes: blinkFrame ? 'closed' : rolled ? 'roll' : 'flat', smile: -0.15 - 0.15 * r, blink: 0,
        lookX: rolled ? -0.95 * Math.cos(Math.PI * e) : 0.2, lookY: rolled ? 0.35 * (1 - Math.sin(Math.PI * e)) : 0,
      };
      o.head.tilt = -0.14 * r - (rolled ? 0.06 * Math.sin(Math.PI * e) : 0);
      o.head.turn = 0.28 + 0.22 * r;
      o.shrug = 0.25 * win(t, 20.0, 20.7, 0.3, 0.3);
      o.lean = -0.05 * r;
    }
    // ---- 22.3 – 24.2: fetch the tulip from under the counter and set it down ----
    const dip = win(t, 22.35, 23.35, 0.35, 0.45);
    if (t >= 22.3 && t < 24.4) {
      o.lean = 0.42 * dip;
      o.head.tilt = 0.18 * dip;
      o.face = { eyes: 'flat', smile: -0.1, lookY: 0.4 * dip };
      // hand goes down behind the counter, comes up with the pot, places it
      const hx = U.keys(t, [[22.3, restF.x], [22.75, x - 50], [23.15, x - 60], [23.55, TULIP_AT + 16], [23.9, TULIP_AT + 16], [24.35, restF.x]]);
      const hy = U.keys(t, [[22.3, restF.y], [22.75, 735], [23.15, 700], [23.55, 640], [23.9, 652, 'outQuad'], [24.35, restF.y]]);
      o.reachF = { x: hx, y: hy };
      if (t >= 22.8 && t < 23.9) { ex.held = 'tulip'; ex.heldAbove = t >= 23.3; }
    }
    // ---- talking about the tulip; then flat through the hikers' lines ----
    if (t >= 24.4 && t < 33.0) {
      o.face = { eyes: 'flat', smile: -0.08, lookX: 0.35 };
      if (t > 23.4 && t < 26.6) o.face.smile = 0.0;
      // taps the $10 tag as he says the price
      if (t > 25.2 && t < 26.3) { const k = win(t, 25.2, 26.3, 0.25, 0.3); o.reachF = { x: lerp(restF.x, TULIP_AT + 16, k), y: lerp(restF.y, 650 + 3 * Math.sin(t * 18) * k, k) }; }
    }
    // ---- 33.0 – 34.2: the sigh ----
    if (t >= 32.9 && t < 34.25) {
      const inh = E(t, 32.95, 33.45), exh = E(t, 33.45, 34.05);
      o.shrug = 0.55 * inh * (1 - exh);
      o.head.tilt = -0.08 * inh * (1 - exh) + 0.14 * exh;
      o.face = { eyes: t < 33.45 ? 'flat' : 'closed', smile: -0.2, open: 0.25 * win(t, 33.45, 34.0, 0.08, 0.2) };
      o.tired = 0.6 * exh;
      ex.puff = clamp((t - 33.45) / 0.95);
    }
    // ---- 34.2 – 37.4: trudge to the bead curtain, and through it ----
    if (t >= 34.2 && t < 37.4) {
      const w = TRUDGE.at(t);
      Object.assign(o, { x: w.x, y: w.y, s: w.s, facing: 1, walk: w.walk, stride: w.stride, tired: 0.75, head: { turn: 0.15, tilt: 0.1 } });
      o.face = { eyes: 'flat', smile: -0.2 };
      o.reachF = o.reachB = undefined;
      if (w.x > K.CURTAIN.x0 + 26) ex.layer = 'doorway';
      ex.dark = clamp((w.x - (K.CURTAIN.x0 + 30)) / 90);
    }
    // ---- 41.9 – 44.0: back with the dusty flower ----
    if (t >= 41.9 && t < 44.0) {
      const w = RETURN.at(t);
      Object.assign(o, { x: w.x, y: w.y, s: w.s, facing: -1, walk: w.walk, stride: w.stride, tired: 0.7, head: { turn: 0.2, tilt: 0.08 } });
      o.face = { eyes: 'flat', smile: -0.2 };
      o.reachB = undefined;
      o.reachF = { x: w.x - 30, y: 712 + Math.sin(w.walk) * 2 }; // carried low, like a sack
      ex.held = 'dusty'; ex.heldAbove = false;
    }
    // ---- 43.5 – 44.4: lift it onto the counter, set it down (thud) ----
    if (t >= 43.5 && t < 44.6) {
      const hx = U.keys(t, [[43.5, 1290 - 30], [43.8, DUSTY_AT + 34], [44.1, DUSTY_AT + 34], [44.6, 1290 - 70]]);
      const hy = U.keys(t, [[43.5, 712], [43.8, 628, 'outQuad'], [44.1, 640, 'inQuad'], [44.6, 662]]);
      o.reachF = { x: hx, y: hy };
      o.lean = 0.28 * win(t, 43.5, 44.6, 0.3, 0.4);
      if (t < 44.1) { ex.held = 'dusty'; ex.heldAbove = t >= 43.72; }
      o.face = { eyes: 'flat', smile: -0.15 };
    }
    // ---- 44.3 – 49.6: "Here." / "This one’s very rare. $200." ----
    if (t >= 44.6 && t < 53.4) {
      o.face = { eyes: 'flat', smile: -0.05, lookX: 0.3 };
      // a finger on the tag as he names the price
      if (t > 47.9 && t < 49.7) {
        const k = win(t, 47.9, 49.7, 0.3, 0.35);
        o.reachF = { x: lerp(1290 - 70, DUSTY_AT + 36, k), y: lerp(662, 642, k) }; o.lean = 0.22 * k;
        // …a deadpan index finger aimed at the sad flower's head ("this one")
        if (k > 0.6) o.holdF = finger((DUSTY_AT + 6 - o.reachF.x) * o.facing, 604 - o.reachF.y, Art.CAST.emb.skin, 14);
      }
    }
    // ---- 53.4 – 55.5: pockets the bills, ka-ching, back ----
    if (t >= 53.4 && t < 55.6) {
      o.face = { eyes: 'flat', smile: -0.05 };
      const grab = win(t, 53.45, 53.95, 0.2, 0.2);
      if (t < 53.95) { o.reachF = { x: lerp(restF.x, 1215, grab), y: lerp(662, 664, grab) }; o.lean = 0.3 * grab; }
      if (t >= 53.85 && t < 55.05) {
        o.facing = 1;
        o.head = { turn: 0.25, tilt: 0.05 };
        const press = win(t, 54.3, 54.7, 0.1, 0.2);
        o.reachF = { x: K.REG.x - 20 + press * 4, y: 612 + press * 10 };
        o.reachB = { x: K.REG.x - 52, y: 650 };
      }
      ex.billsInHand = t > 53.8 && t < 54.6;
    }
    // ---- 55.5 →: watches the celebration, deadpan; then looks at us ----
    if (t >= 55.6) {
      const look = E(t, 66.6, 67.3);
      o.face = { eyes: 'flat', smile: -0.08, lookX: 0.35 * (1 - look) };
      o.head.turn = lerp(0.28, 1, look);
      o.head.tilt = lerp(0, -0.02, look);
      if (t > 68.0) o.face.blink = U.bump(t, 68.4, 0.12);
    }
    // ---- talking + a slow idle drift of the head ----
    o.face.talk = talking(t, 'emb');
    if (o.walk === undefined) o.head.tilt = (o.head.tilt || 0) + 0.02 * Math.sin(t * 0.5 + 0.7);
    return { o, ex };
  }

  /* ---- the hikers ---- */
  const BASE_FACE = { smile: 0.38, eyes: 'open', browUp: 0.25 };
  const SNIPS = [0.9, 1.75, 2.55];
  const FLIPS = { emb: [34.2, 53.85, 55.05], h2: [55.6, 56.9], h1: [58.2], h4: [] };
  function hikerAt(who, t) {
    const w = ENTER[who];
    const o = { look: LOOK[who], t, facing: 1, seed: { h1: 11, h2: 23, h4: 41 }[who], poles: false };
    const ex = {};
    if (t < w.t0) return null;
    const p = w.at(t);
    o.x = p.x; o.y = p.y; o.s = p.s;
    if (t < w.t1 && p.moving) { o.walk = p.walk; o.stride = p.stride; o.bounce = 0.25; }
    o.face = Object.assign({}, BASE_FACE);
    o.head = { turn: 0.18, tilt: 0 };
    // ---- the deadpan "don't flinch" hold, then the grins ----
    const g = GRIN(t, who === 'h1' ? 0 : who === 'h2' ? 0.18 : 0.32);
    if (t >= 46.0 && t < 53.4) {
      o.face = { smile: 0.05, eyes: 'open', browUp: 0 };
      if (t > 49.8) o.face = { smile: 0, eyes: 'open', blink: U.bump(t, 51.62, 0.1) };
      o.head.turn = t > 49.8 ? 0.62 : 0.2;
      if (t > 49.8) o.head.tilt = 0.03 * U.bump(t, 51.62, 0.5); // the tiniest synchronized tilt with the blink
    }
    if (t >= 53.35) {
      o.face = { smile: lerp(0.1, 1, clamp(g)), eyes: g > 0.5 ? 'happy' : 'open', open: 0.32 * clamp(g), browUp: 0.4 * clamp(g) };
    }
    o.face.talk = talking(t, who);
    // idle life: a little head drift and the odd glance (not during the deadpan hold)
    const sd = { h1: 1.3, h2: 2.9, h4: 4.7 }[who];
    const still = t > 49.6 && t < 53.4 ? 0 : 1;
    o.head.tilt = (o.head.tilt || 0) + still * 0.025 * Math.sin(t * 0.63 + sd);
    o.head.turn = (o.head.turn || 0) + still * 0.06 * U.noise1(t * 0.35, sd * 7);
    if (o.face.lookX === undefined) o.face.lookX = still * 0.5 * U.noise1(t * 0.3, sd * 3);
    return { o, ex, p };
  }

  function h1State(t) {
    const r = hikerAt('h1', t); if (!r) return null;
    const { o, ex } = r;
    const counterHand = { x: 1032, y: 684 };
    if (t < DOOR_T + 0.55) { o.gesture = 'reach'; o.gw = 1 - E(t, DOOR_T + 0.07, DOOR_T + 0.55); }
    if (t >= DOOR_T + 3.95 && t < 26.9) { // leaning on the counter
      const k = E(t, DOOR_T + 3.95, DOOR_T + 4.55);
      o.reachF = { x: lerp(o.x + 30, counterHand.x, k), y: lerp(760, counterHand.y, k) };
      o.lean = 0.08 * k;
      if (t >= 9.0 && t < 12.0) { o.face = Object.assign(o.face, { smile: 0.55, browUp: 0.45 }); o.head.turn = 0.3; }
      if (t >= 22.4 && t < 26.6) o.face.lookY = 0.35 * win(t, 23.0, 26.6); // looks at the tulip
    }
    if (t >= 26.9 && t < 31.6) { // "$10? That's not meaningful enough."
      const k = win(t, 26.9, 31.6, 0.25, 0.5);
      o.gesture = 'hips'; o.gw = k;
      o.lean = -0.07 * k;
      o.face = { smile: -0.55 * k, eyes: 'open', brow: -0.85 * k, browUp: 0, talk: talking(t, 'h1') };
      o.head.tilt = -0.05 * k;
    }
    if (t >= 31.6 && t < 46.0) { // waiting; drums fingers on the counter while he's gone
      const k = E(t, 31.6, 32.2);
      const drum = t > 34.5 && t < 37.4 ? Math.abs(Math.sin(t * 11)) * 4 : 0;
      o.reachF = { x: lerp(o.x + 20, counterHand.x, k), y: lerp(770, counterHand.y - drum, k) };
      o.face = Object.assign({}, BASE_FACE, { smile: 0.15, lookX: 0.3 });
      if (t > 42.0) o.face.lookY = 0.3;
    }
    if (t >= 46.0 && t < 53.4) { // hand drifts to the pocket during the hold
      const k = E(t, 52.75, 53.0);
      o.gesture = 'pocket'; o.gw = k;
      o.reachF = k > 0.99 ? undefined : { x: lerp(counterHand.x, o.x + 14, k), y: lerp(counterHand.y, 760, k) };
      if (t > 52.95) { // SLAP
        const s = E(t, 52.95, 53.12, 'inQuad');
        o.reachF = { x: lerp(o.x + 14, 1104, s), y: lerp(760, 676, s) };
        o.lean = 0.26 * s;
        ex.bills = s < 0.999;
      }
    }
    if (t >= 53.12 && t < 57.0) {
      const k = 1 - E(t, 53.5, 54.1);
      o.reachF = { x: lerp(o.x + 30, 1104, k), y: lerp(770, 676, k) };
      o.lean = 0.26 * k;
    }
    // ---- grabs the flower, lifts it, turns to his friends ----
    if (t >= 57.0) {
      const reach = win(t, 57.0, 57.6, 0.3, 0.1);
      if (t < 57.6) { o.reachF = { x: lerp(o.x + 30, DUSTY_AT - 22, reach), y: lerp(760, 650, reach) }; o.lean = 0.32 * reach; }
      if (t >= 57.5) {
        ex.carry = true;
        const up = E(t, 57.5, 58.1);
        const S1 = o.s * 1.08, f1 = t >= 58.2 ? -1 : 1, ox = t >= 58.2 ? SPOT.h1[0] - 6 : o.x;
        const holdF = { x: ox + f1 * 46 * S1, y: o.y - 128 * S1 }, holdB = { x: ox + f1 * 38 * S1, y: o.y - 124 * S1 };
        const restB = { x: ox - f1 * 7 * S1, y: o.y - 100 * S1 }; // where the free hand hangs
        o.reachF = { x: lerp(DUSTY_AT - 22, holdF.x, up), y: lerp(650, holdF.y, up) };
        o.reachB = { x: lerp(restB.x, holdB.x, up), y: lerp(restB.y, holdB.y, up) };
        o.lean = 0.32 * (1 - up);
      }
      if (t >= 58.2) {
        o.facing = -1; o.x = SPOT.h1[0] - 6;
        // the selfie (everyone looks into h4's phone), then straight into the shout
        const sk = SELFIE(t), ch = CHEER(t), c1 = clamp(ch);
        o.head = { turn: lerp(lerp(0.35, 1, sk), 0.55, c1), tilt: lerp(0.06 - 0.1 * sk, -0.16, c1) };
        o.face = { smile: 1, eyes: 'happy', open: lerp(0.35 + 0.15 * sk, 0.6, c1), browUp: 0.4 + 0.2 * Math.max(sk, c1) };
        o.lean = 0.1 + 0.12 * sk * (1 - c1) - 0.2 * c1;
        if (t >= 63.0) { // the trophy: raised up and out over the group (clear of his face)
          const S1 = o.s * 1.08, f1 = o.facing;
          o.reachF = { x: o.x + f1 * lerp(46, 66, ch) * S1, y: o.y - lerp(128, 286, ch) * S1 };
          o.reachB = { x: o.x + f1 * lerp(38, 54, ch) * S1, y: o.y - lerp(124, 292, ch) * S1 };
          o.face.talk = talking(t, 'h1');
          ex.trophy = c1;
          ex.dustFall = clamp((t - 63.4) / 1.4);
        }
      }
    }
    return r;
  }

  function h2State(t) {
    const r = hikerAt('h2', t); if (!r) return null;
    const { o } = r;
    if (t >= 12.3 && t < 17.1) { // "We heard you were talking about how meaningful his flower was."
      const k = win(t, 12.3, 17.1, 0.35, 0.4);
      o.gesture = 'open'; o.gw = k * (0.85 + 0.15 * Math.sin(t * 3));
      o.face = { smile: 0.45, eyes: 'open', browUp: 0.7 * k, talk: talking(t, 'h2') };
      o.head.turn = 0.3;
    }
    if (t >= 17.15 && t < 19.8) { // "We want that." — a firm jab of the finger past h1, at the shopkeeper
      const k = win(t, 17.15, 19.8, 0.22, 0.45);
      const jab = U.E.outBack(clamp((t - 17.22) / 0.34));
      o.armF = [lerp(0.1, 2.12, k), lerp(0.18, lerp(0.7, 0.04, jab), k)];
      o.face = { smile: 0.12, eyes: 'open', brow: -0.5 * k, talk: talking(t, 'h2') };
      o.lean = 0.08 * k;
      o.head.tilt = 0.05 * k; // chin down: she means it
      const a2 = o.armF[0] + o.armF[1];
      if (k > 0.55) o.holdF = finger(Math.sin(a2), Math.cos(a2), Art.CAST.h2.skin);
    }
    if (t >= 26.9 && t < 33.0) o.face = Object.assign({}, BASE_FACE, { smile: 0.05, brow: -0.25 * win(t, 27, 30.5, 0.3, 0.5) });
    if (t >= 34.0 && t < 44.0) { // looking around the shop while he's gone
      o.head.turn = 0.18 + 0.4 * win(t, 34.5, 37.2, 0.5, 0.5);
      o.face = Object.assign({}, BASE_FACE, { smile: 0.25, lookY: -0.4 * win(t, 34.5, 37.2) });
    }
    // high-five with h4: turns to face him; her front hand meets his at HF.m
    if (t >= 55.6 && t < 56.9) {
      o.facing = -1;
      const up = highFive(t, o, 1, 'F');
      o.head = { turn: 0.3, tilt: -0.08 * up };
      o.face.talk = 0;
    }
    if (t >= 58.2) {
      const sk = SELFIE(t), ch = CHEER(t), c1 = clamp(ch);
      o.lean = 0.14 * E(t, 58.2, 58.8) - 0.26 * sk * (1 - c1); // leans back toward h4's phone
      o.head = { turn: lerp(lerp(0.18, 1, sk), 0.6, c1), tilt: lerp(0.1 * sk, -0.08, c1) };
      o.face = { smile: 1, eyes: 'happy', open: lerp(0.35 + 0.15 * sk, 0.6, c1), browUp: 0.45 + 0.15 * Math.max(sk, c1) };
      if (t >= 63.0) {
        o.gesture = 'cheer'; o.gw = ch;
        o.face.talk = talking(t, 'h2');
        o.bob = -Math.abs(Math.sin(t * 7)) * 4 * c1;
      }
    }
    return r;
  }

  function h4State(t) {
    const r = hikerAt('h4', t); if (!r) return null;
    const { o, ex } = r;
    // phone up, filming everything (red dot)
    o.gesture = 'phone'; o.gw = 1;
    ex.phone = 'F'; ex.rec = true;
    o.face = Object.assign(o.face, { lookY: -0.1 });
    if (t >= 29.8 && t < 32.9) { // lowers it to say his line
      const k = win(t, 29.8, 32.9, 0.3, 0.4);
      o.gw = 1 - 0.75 * k;
      o.face = { smile: 0.55, eyes: 'wide', browUp: 1 * k, talk: talking(t, 'h4') };
      o.head.turn = 0.32;
    }
    // the phone comes down for the deadpan "don't flinch" hold, then back up
    if (t >= 45.3 && t < 53.4) o.gw = 1 - 0.7 * E(t, 45.3, 46.0);
    if (t >= 53.4 && t < 57.4) o.gw = lerp(0.3, 1, E(t, 53.6, 54.2));
    if (t >= 55.5 && t < 56.95) { // high-five with his free (back) hand; the phone stays up in the other
      const up = highFive(t, o, -1, 'B');
      o.gw = 1 - 0.7 * up; // the phone hand drops to his chest (clear of h2's head) for the slap
      o.head.tilt = -0.06 * up;
    }
    if (t >= 57.4 && t < 60.9) o.gw = 1 - 0.1 * E(t, 57.4, 57.9);
    if (t >= 60.9) { // the selfie: phone out at arm's length… then straight into the cheer
      const sk = SELFIE(t), ch = CHEER(t), c1 = clamp(ch);
      const sIn = E(t, 60.9, 61.3);
      const phone = [lerp(0.1, 2.15, 0.9), lerp(0.18, 0.75, 0.9)], selfie = [2.78, 0.14], cheer = [2.45, 0.38];
      const a = [lerp(phone[0], selfie[0], sIn), lerp(phone[1], selfie[1], sIn)];
      o.armF = [lerp(a[0], cheer[0], ch), lerp(a[1], cheer[1], ch)];
      o.gesture = 'cheer'; o.gw = ch; // the back arm joins the cheer
      ex.selfie = sk * (1 - c1); ex.rec = false;
      o.head = { turn: lerp(lerp(0.2, 1, sk), 0.55, c1), tilt: lerp(-0.05 * sk, -0.08, c1) };
      o.lean = 0.12 * sk * (1 - c1);
      o.face = { smile: 1, eyes: 'happy', open: lerp(0.45, 0.6, c1), browUp: 0.5 + 0.1 * c1, talk: t >= 63.0 ? talking(t, 'h4') : 0 };
      o.bob = -Math.abs(Math.sin(t * 7 + 1)) * 4 * c1;
    }
    // photo flashes (tulip, dusty flower) + the selfie flash: instant on the click, quick decay
    ex.flash = Math.max(...SNAPS.map((s) => pulse(t, s, 0.07)));
    return r;
  }

  /* ---- the narrator, unfeatured, sipping tea on the bench ---- */
  const SIPS = [4.6, 15.6, 31.4, 45.2, 58.6];
  function meState(t) {
    const s = K.sAt(K.ME.y), x = K.ME.x, y = K.ME.y;
    let sip = 0; for (const s0 of SIPS) sip = Math.max(sip, win(t, s0, s0 + 1.7, 0.45, 0.6));
    // at "his flower" he pauses mid-sip and glances over
    const glance = win(t, 15.2, 17.6, 0.3, 0.6);
    sip *= 1 - glance * 0.85;
    const rest = { x: x + 38 * s, y: y - 84 * s }, lip = { x: x + 12 * s, y: y - 170 * s };
    const hand = { x: lerp(rest.x, lip.x, sip), y: lerp(rest.y, lip.y, sip) - glance * 30 * s };
    const steam = 1 - sip;
    return {
      look: 'me', x, y, s, t, pose: 'bench', pack: false, seed: 3,
      head: { turn: 0.3 + 0.15 * glance, tilt: -0.1 * sip },
      face: { smile: 0.32 + 0.2 * glance + 0.25 * E(t, 63.5, 64.5), eyes: sip > 0.85 ? 'closed' : 'open', browUp: 0.55 * glance, lookX: 0.4 },
      reachF: hand,
      holdF: (c) => K.mug(c, sip * 0.7, steam, t),
    };
  }

  /* ======================================================================
     CAMERA — shots (world coords)
     ====================================================================== */
  const MED = { x: 1040, y: 600, zoom: 1.32 };
  function camAt(t) {
    if (t < 5.8) { const k = E(t, 0, 5.8); return { x: 960 + 12 * k, y: 540 + 4 * k, zoom: 1 + 0.03 * k }; }
    if (t < 7.9) { const k = E(t, 5.8, 7.9); return { x: lerp(640, 800, k), y: 826, zoom: 2.75, insert: true }; }
    if (t < 12.2) { const k = E(t, 7.9, 12.2); return { x: 1040 + 6 * k, y: 600, zoom: 1.3 + 0.03 * k }; }
    if (t < 17.15) { const k = E(t, 12.2, 17.15); return { x: 872 + 10 * k, y: 614, zoom: 1.6 + 0.06 * k }; } // h2's long line: the hikers
    if (t < 19.8) { const k = E(t, 17.15, 19.8); return { x: 1046, y: 600, zoom: 1.33 + 0.02 * k }; }
    if (t < 22.3) { const k = E(t, 19.8, 22.3, 'outSine'); return { x: 1318, y: 560, zoom: 2.5 + 0.08 * k, dof: 4 }; }
    if (t < 26.8) { const k = E(t, 22.3, 26.8); return { x: 1048 - 4 * k, y: 600, zoom: 1.33 + 0.02 * k }; }
    if (t < 29.75) { const k = E(t, 26.8, 29.75); return { x: 1150 - 8 * k, y: 598, zoom: 1.62 + 0.05 * k }; } // "$10?" — h1 vs Embarrassment
    if (t < 34.0) { const k = E(t, 29.75, 34.0); return { x: 1044 - 4 * k, y: 600, zoom: 1.34 + 0.01 * k }; }
    if (t < 37.4) { const k = E(t, 34.0, 37.2); return { x: lerp(1040, 1440, k), y: lerp(600, 585, k), zoom: lerp(1.35, 1.26, k) }; }
    if (t < 41.9) return { x: 985, y: 575, zoom: 1.1 + 0.05 * E(t, 37.4, 41.9), back: true };
    if (t < 49.9) { const k = E(t, 42.4, 45.0); return { x: lerp(1150, 1062, k), y: 598, zoom: lerp(1.3, 1.34, k) }; }
    if (t < 53.0) { const k = E(t, 49.9, 53.0); return { x: 800, y: 620, zoom: 2.28 + 0.05 * k, dof: 4 }; }
    // one slow drift out from the money to the celebration (room above for the shout)
    if (t < 66.4) { const k = E(t, 53.0, 63.3); return { x: lerp(1040, 950, k), y: lerp(600, 574, k), zoom: lerp(1.32, 1.2, k) }; }
    const k = E(t, 66.4, 69.6, 'inOutSine');
    return { x: lerp(950, 1150, k), y: lerp(574, 560, k), zoom: lerp(1.2, 1.62, k) };
  }
  const toScreen = (cam, p) => ({ x: (p.x - cam.x) * cam.zoom + W / 2, y: (p.y - cam.y) * cam.zoom + H / 2 });

  /* ======================================================================
     BUBBLE PLACEMENT (screen space): above the speaker, clear of all faces
     ====================================================================== */
  const bubbleBox = (ctx, text, o) => {
    const size = o.size || 34;
    ctx.save(); ctx.font = Art.font(size, 'sans', 800);
    const lines = Art.wrap(ctx, text, o.maxW || 540);
    let tw = 0; for (const l of lines) tw = Math.max(tw, ctx.measureText(l).width);
    ctx.restore();
    let w = tw + 56, h = lines.length * size * 1.22 + 40;
    if (o.style === 'shout') { w *= 1.26; h *= 1.45; }
    return { w, h };
  };
  /** does segment A→B pass within r of point C? */
  function segHit(ax, ay, bx, by, cx, cy, r) {
    const dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy || 1;
    const u = clamp(((cx - ax) * dx + (cy - ay) * dy) / L2);
    return Math.hypot(ax + u * dx - cx, ay + u * dy - cy) < r;
  }
  /**
   * Tail-aware placement. The tail tip sits just in front of the speaker's
   * face at mouth height (never on the face); candidates are tried from
   * "above and in front" outward and upward until neither the balloon nor
   * its tail touches any head (speaker included).
   */
  function placeBubble(ctx, text, o, spk, heads) {
    const { w, h } = bubbleBox(ctx, text, o);
    const f = spk.facing || 1;
    const tip = { x: spk.x + f * (spk.front + 8), y: spk.mouth.y + 4 };
    const all = heads.concat([spk]);
    const offs = o.style === 'shout' ? [0, 0.15, -0.15, 0.3, -0.3] : [0.42, 0.25, 0.6, 0.08, -0.12, 0.8];
    let best = null;
    for (let lift = 0; lift <= 300 && !best; lift += 20) {
      for (const k of offs) {
        const x = clamp((o.style === 'shout' ? spk.x : tip.x) + f * w * k, w / 2 + 30, W - w / 2 - 30);
        const y = spk.top - 22 - h / 2 - lift;
        if (y - h / 2 < Art.PIC.top + 8) continue;
        const L = x - w / 2, R = x + w / 2, T = y - h / 2, B = y + h / 2;
        let bad = false;
        for (const hd of all) { // balloon vs heads (with hair/hat headroom)
          const cy = hd.y - hd.r * 0.15, rr2 = hd.r * 1.28;
          if (Math.hypot(clamp(hd.x, L, R) - hd.x, clamp(cy, T, B) - cy) < rr2) { bad = true; break; }
        }
        if (!bad && o.style !== 'shout') { // tail vs heads
          const ax = clamp(tip.x, L + 40, R - 40), ay = B - 4;
          for (const hd of all) {
            if (segHit(ax, ay, tip.x, tip.y, hd.x, hd.y - hd.r * 0.1, hd.r * 1.08 + 6)) { bad = true; break; }
          }
        }
        if (!bad) { best = { x, y }; break; }
      }
    }
    if (!best) best = { x: clamp(spk.x, w / 2 + 30, W - w / 2 - 30), y: Math.max(Art.PIC.top + h / 2 + 8, spk.top - 22 - h / 2) };
    best.tip = tip;
    return best;
  }

  /** screen-space heads (+ the raised trophy as an obstacle) for balloon placement */
  function speakersOf(A, cam, t) {
    const heads = [], sp = {};
    for (const k of ['h1', 'h2', 'h4', 'emb', 'me']) {
      if (!A[k]) continue;
      const h = toScreen(cam, A[k].head), m = toScreen(cam, A[k].mouth), tp = toScreen(cam, A[k].top);
      const r = A[k].head.r * cam.zoom;
      // how far the head reaches forward (h1's cap brim sticks out)
      const front = r * (k === 'h1' ? 1.62 : 1.06);
      sp[k] = { x: h.x, y: h.y, r, top: Math.min(tp.y, h.y - r * 1.2), mouth: m, facing: A[k].facing || 1, front };
      heads.push(sp[k]);
    }
    if (A.h1 && t > 63.0) { // keep the raised trophy flower (pot + droopy head) clear of the shout
      const S1 = A.h1.scale, c = toScreen(cam, { x: A.h1.handF.x, y: A.h1.handF.y - 52 * S1 }), r = 50 * S1 * cam.zoom;
      heads.push({ x: c.x, y: c.y, r, top: c.y - r, facing: 1, front: 0, obstacle: true });
    }
    return { heads, sp };
  }
  function speakerFor(bo, sp) {
    if (bo.who !== 'all') return sp[bo.who] || null;
    const g = ['h1', 'h2', 'h4'].map((k) => sp[k]).filter(Boolean);
    if (!g.length) return null;
    return { x: g.reduce((a, b) => a + b.x, 0) / g.length, y: g[0].y, r: 0, front: 0, facing: 1, top: Math.min(...g.map((b) => b.top)), mouth: g[0].mouth };
  }
  /** the cast's anchors at time t, laid out on a scratch canvas (nothing visible is drawn) */
  function anchorsAt(t) {
    const c = Art.canvas('shop11:layout', 4, 4).getContext('2d');
    c.setTransform(1, 0, 0, 1, 0, 0);
    const A = { me: Art.person(c, meState(t)), emb: K.person(c, embState(t).o, FLIPS.emb) };
    for (const [who, fn] of [['h4', h4State], ['h2', h2State], ['h1', h1State]]) { const st = fn(t); if (st) A[who] = K.person(c, st.o, FLIPS[who]); }
    return A;
  }
  /**
   * Each balloon is placed once — clear of every face — at a reference moment
   * of its line, then pinned in WORLD space: it rides the camera smoothly and
   * never hops between candidate spots as heads drift. (The tail tip still
   * follows the speaker's mouth every frame.) A cache of a pure computation.
   */
  const PINS = new Map();
  function pinFor(ctx, i) {
    const [t0, t1, text, bo] = BUB[i];
    // keyed by the measured balloon width, so a late-loading web font re-places it
    const key = i + ':' + Math.round(bubbleBox(ctx, text, bo).w);
    if (PINS.has(key)) return PINS.get(key);
    const tr = Math.min(t1 - 0.2, t0 + (bo.ref || 0.5));
    const cam = camAt(tr);
    const { heads, sp } = speakersOf(anchorsAt(tr), cam, tr);
    const spk = speakerFor(bo, sp);
    if (!spk) return null;
    const pos = placeBubble(ctx, text, bo, spk, heads.filter((h) => h !== spk));
    const pin = { x: (pos.x - W / 2) / cam.zoom + cam.x, y: (pos.y - H / 2) / cam.zoom + cam.y };
    PINS.set(key, pin);
    return pin;
  }

  /* ======================================================================
     THE BACK ROOM (insert) — its own little set
     ====================================================================== */
  const BR = { flowerX: 1096, shelfY: 704 };
  function backRoom(ctx, t) {
    const u = t - 37.4;
    // walls & floor
    const g = ctx.createLinearGradient(0, 120, 0, 960);
    g.addColorStop(0, '#2a1d18'); g.addColorStop(0.7, '#3a2a22'); g.addColorStop(1, '#2c201a');
    ctx.fillStyle = g; ctx.fillRect(-200, 0, W + 400, H);
    ctx.fillStyle = '#3f2e24'; ctx.fillRect(-200, 840, W + 400, 260);
    ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(-200, 840, W + 400, 8);
    // the small high window and its dusty beam
    ctx.fillStyle = '#e9c98a'; ctx.fillRect(1290, 196, 150, 96);
    ctx.fillStyle = 'rgba(120,90,60,0.35)'; for (let i = 0; i < 18; i++) ctx.fillRect(1290 + U.hash(i, 3) * 140, 196 + U.hash(i, 4) * 86, 6, 6);
    ctx.strokeStyle = '#2a1d18'; ctx.lineWidth = 8; ctx.strokeRect(1290, 196, 150, 96);
    ctx.beginPath(); ctx.moveTo(1365, 196); ctx.lineTo(1365, 292); ctx.stroke();
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    const bg = ctx.createLinearGradient(1360, 240, 1080, 700);
    bg.addColorStop(0, 'rgba(255,214,150,0.32)'); bg.addColorStop(1, 'rgba(255,214,150,0.06)');
    ctx.fillStyle = bg;
    ctx.beginPath(); ctx.moveTo(1290, 210); ctx.lineTo(1440, 280); ctx.lineTo(1220, 760); ctx.lineTo(960, 720); ctx.closePath(); ctx.fill();
    ctx.restore();
    // shelves with forgotten things
    const shelfB = (x0, x1, y) => { ctx.fillStyle = '#4a3428'; ctx.fillRect(x0, y, x1 - x0, 12); ctx.fillStyle = '#5c4232'; ctx.fillRect(x0, y, x1 - x0, 4); };
    shelfB(260, 760, 470); shelfB(260, 760, 650); shelfB(900, 1400, BR.shelfY); shelfB(1480, 1800, 560);
    for (let i = 0; i < 4; i++) { const x = 300 + i * 26; ctx.fillStyle = U.shade('#8e5a3c', -i * 0.05); ctx.beginPath(); ctx.moveTo(x - 20, 470); ctx.lineTo(x + 20, 470); ctx.lineTo(x + 26, 440 - i * 4); ctx.lineTo(x - 26, 440 - i * 4); ctx.closePath(); ctx.fill(); }
    ctx.fillStyle = '#5a4a3a'; ctx.fillRect(470, 400, 90, 70); ctx.fillRect(580, 420, 70, 50); ctx.fillStyle = '#6b5846'; ctx.fillRect(470, 400, 90, 10);
    ctx.fillStyle = '#6f7a80'; ctx.beginPath(); ctx.ellipse(380, 630, 40, 22, 0, 0, TAU); ctx.fill(); ctx.fillRect(340, 600, 80, 30); ctx.strokeStyle = '#6f7a80'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(420, 610); ctx.lineTo(470, 580); ctx.stroke();
    ctx.fillStyle = '#4e3b2e'; ctx.fillRect(560, 600, 120, 50); ctx.fillStyle = '#d8ccb0'; ctx.fillRect(570, 588, 100, 14);
    ctx.fillStyle = '#5a4434'; ctx.fillRect(1520, 500, 60, 60); ctx.fillRect(1600, 520, 50, 40); ctx.fillRect(1680, 470, 80, 90);
    ctx.fillStyle = '#4a3a2e'; ctx.save(); ctx.translate(1560, 830); ctx.rotate(-0.08); ctx.fillRect(-90, -60, 180, 60); ctx.restore();
    // a mop leaning in the corner
    ctx.strokeStyle = '#8a6a44'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(1840, 840); ctx.lineTo(1760, 380); ctx.stroke();
    ctx.fillStyle = '#b8ab92'; ctx.beginPath(); ctx.ellipse(1846, 840, 30, 14, 0, 0, TAU); ctx.fill();
    // cobwebs in the upper corners
    ctx.strokeStyle = 'rgba(230,222,206,0.35)'; ctx.lineWidth = 1;
    for (const [cx, cy, dir] of [[150, 150, 1], [1830, 150, -1]]) {
      for (let i = 0; i < 6; i++) { const a = i / 5 * Math.PI / 2; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + dir * Math.cos(a) * 170, cy + Math.sin(a) * 170); ctx.stroke(); }
      for (let r = 30; r < 170; r += 30) { ctx.beginPath(); ctx.arc(cx, cy, r, dir > 0 ? 0 : Math.PI / 2, dir > 0 ? Math.PI / 2 : Math.PI); ctx.stroke(); }
    }
    // a tiny spider bobbing on its thread over the flower
    const spY = 520 + Math.sin(t * 2.2) * 14;
    ctx.strokeStyle = 'rgba(230,222,206,0.5)'; ctx.beginPath(); ctx.moveTo(1150, 420); ctx.lineTo(1150, spY); ctx.stroke();
    ctx.fillStyle = '#1a1210'; ctx.beginPath(); ctx.arc(1150, spY + 4, 5, 0, TAU); ctx.fill();
    ctx.strokeStyle = '#1a1210'; ctx.lineWidth = 1.3;
    for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(1150, spY + 4); ctx.lineTo(1150 - 9, spY + i * 3); ctx.moveTo(1150, spY + 4); ctx.lineTo(1150 + 9, spY + i * 3); ctx.stroke(); }
    // dust motes in the beam
    Art.motes(ctx, { seed: 61, count: 40, x0: 960, x1: 1440, y0: 220, y1: 740, t, color: '#ffe3b0', size: 1.6, drift: 4, alpha: 0.55, wander: 30 });

    // ---- Embarrassment ----
    const s = 1.22;
    const inX = U.keys(u, [[0.3, 520], [1.5, 900, 'outSine']]);
    const outX = U.keys(u, [[3.35, 900], [4.5, 470, 'inSine']]);
    const walkingIn = u < 1.5, walkingOut = u >= 3.35;
    const x = walkingOut ? outX : inX;
    const facing = u >= 3.2 ? -1 : 1;
    const o = { look: 'emb', x, y: 905, s, t, facing, seed: 5, tired: 0.55, head: { turn: 0.25, tilt: 0.12 }, face: { eyes: 'flat', smile: -0.2 } };
    const dist = walkingOut ? (900 - outX) : (inX - 520);
    if ((walkingIn && u > 0.3) || walkingOut) { o.walk = dist / (29.7 * s * 1.1 * 1.1 * 0.9); o.stride = 0.9 * clamp(walkingIn ? (1.5 - u) / 0.3 : 1) ; }
    // pick it up, blow the dust off
    const grab = 2.2, lifted = u >= grab;
    const handTo = U.keys(u, [[1.6, [870, 735]], [2.1, [BR.flowerX + 32, BR.shelfY - 50]], [2.25, [BR.flowerX + 32, BR.shelfY - 50]], [2.65, [1012, 640], 'outQuad'], [3.1, [1008, 646]], [3.35, [880, 735]]]);
    if (u >= 1.6) o.reachF = { x: handTo[0], y: handTo[1] };
    if (walkingOut) o.reachF = { x: x - 40, y: 765 + Math.sin(o.walk || 0) * 3 };
    if (u > 1.5 && u < 3.2) o.face = { eyes: 'flat', smile: -0.15, lookY: u < 2.3 ? 0.5 : 0.1 };
    const blow = win(u, 2.62, 3.0, 0.06, 0.2);
    if (blow > 0) { o.face = { eyes: 'flat', mouth: 'o', open: 0.4 * blow, smile: 0 }; o.head.tilt = 0.05; }
    // the flower (on the shelf, then in his hand)
    let fx = BR.flowerX, fy = BR.shelfY;
    const A = Art.person(ctx, o);
    if (lifted) { fx = A.handF.x + 8 * facing; fy = A.handF.y + 50; }
    const dustLeft = 1 - 0.55 * clamp((u - 2.7) / 0.4);
    K.dusty(ctx, fx, fy, 1.45, t, { dust: dustLeft, tag: 'old' });
    if (lifted) { ctx.fillStyle = '#f2a59e'; ctx.beginPath(); ctx.arc(A.handF.x, A.handF.y, 8.5, 0, TAU); ctx.fill(); }
    // the puff of breath and the cloud of dust it raises
    if (u > 2.62 && u < 3.8) {
      const k = (u - 2.62) / 1.1;
      K.puff(ctx, A.mouth.x + 4 * facing, A.mouth.y + 2, k * 1.3, facing, 1.1, '#fff8ea', -0.2);
      ctx.save();
      for (let i = 0; i < 16; i++) {
        const a = U.hash(i, 8) * TAU, sp = 40 + U.hash(i, 9) * 90;
        const px = fx + 10 + Math.cos(a) * sp * k + k * 70 * facing, py = fy - 120 + Math.sin(a) * sp * k * 0.6 - k * 20;
        ctx.globalAlpha = (1 - k) * 0.45;
        ctx.fillStyle = '#d9cdb2';
        ctx.beginPath(); ctx.arc(px, py, 6 + k * 14 * U.hash(i, 10), 0, TAU); ctx.fill();
      }
      ctx.restore();
    }
    Art.vignette(ctx, 0.55, '#120a06');
  }

  /* ======================================================================
     RENDER
     ====================================================================== */
  function drawBackground(c, t, cam) {
    K.staticSet(c);
    K.windowLettering(c, PD);
    K.bucketTags(c);
    K.clockHands(c, t);
    K.hangers(c, t, PD);
    K.floor(c, PD);
    const doorO = doorOpen(t);
    K.floorLight(c, t, PD, 'day', 1);
    if (doorO > 0.05) doorSpill(c, doorO);
    K.drawPrints(c, PRINTS, t);
  }
  function doorOpen(t) {
    if (t < DOOR_T - 0.05) return 0;
    if (t < DOOR_T + 2.45) return clamp(U.spring(t - (DOOR_T - 0.05), 1.6, 6.5) * 0.9);
    return 0.9 * (1 - E(t, DOOR_T + 2.45, DOOR_T + 3.05, 'inQuad'));
  }
  function doorSpill(c, o) {
    // sunlight from the open doorway washing across the floor
    const L = K.leftPt;
    const a = L(K.DOOR.x0, 0), b = L(K.DOOR.x1, 0);
    c.save();
    c.globalCompositeOperation = 'lighter';
    const g = c.createLinearGradient(a.x, a.y, a.x + 520, a.y + 120);
    g.addColorStop(0, U.rgba(PD.light, 0.32 * o)); g.addColorStop(1, U.rgba(PD.light, 0));
    c.fillStyle = g;
    poly(c, [[a.x, a.y], [b.x, b.y], [b.x + 520, b.y + 70], [a.x + 420, a.y + 150]]);
    c.fill();
    c.restore();
  }
  function beadPush(t) {
    // strands swing after he pushes through (out at ~36.9, back at ~41.6)
    return (sx, by, i, j) => {
      const k = (by - K.CURTAIN.top) / (K.BACK_Y - K.CURTAIN.top);
      const ph = i * 0.7;
      let d = K.swing(t, [[36.75 + i * 0.03, 16], [41.78 + (7 - i) * 0.03, -14]], 1.3, 1.6);
      d *= Math.sin(ph + 1.2) * 0.4 + 0.8;
      return d * k * k;
    };
  }

  Film.scene({
    id: 'shop',
    order: 11,
    title: 'Embarrassment’s Flowers',
    duration: D,
    moods: [[0, 'shop'], [53.0, 'comedy']],
    sfx: [
      [0.9, 'tap', { gain: 0.12 }], [1.75, 'tap', { gain: 0.12 }], [2.55, 'tap', { gain: 0.12 }], [2.45, 'footsteps', { gain: 0.3 }],
      [2.97, 'thud', { gain: 0.5 }], [3.05, 'bell', { gain: 0.7 }], [3.6, 'footsteps', { gain: 0.55 }],
      [6.07, 'bell', { gain: 0.3 }], [6.0, 'squelch', { gain: 0.5 }], [6.6, 'squelch', { gain: 0.4 }], [7.2, 'squelch', { gain: 0.32 }],
      [20.3, 'whoosh', { gain: 0.14 }], [23.88, 'thud', { gain: 0.32 }], [24.45, 'tap', { gain: 0.35 }],
      [33.0, 'sigh', { gain: 0.85 }], [34.4, 'footsteps', { gain: 0.28 }], [36.75, 'shimmer', { gain: 0.4 }],
      [40.0, 'breath', { gain: 0.6 }], [41.8, 'shimmer', { gain: 0.35 }], [44.08, 'thud', { gain: 0.5 }], [45.0, 'tap', { gain: 0.32 }],
      [51.0, 'clock', { gain: 0.4 }], [53.1, 'cash', { gain: 0.85 }], [54.5, 'register', { gain: 0.9 }],
      [56.2, 'pop', { gain: 0.6 }], [61.7, 'tap', { gain: 0.5 }], [61.7, 'sparkle', { gain: 0.35 }], [63.3, 'swell', { gain: 0.45 }],
    ],
    fadeIn: 0.8,
    fadeOut: 0.8,
    post: { vignette: 0.3, grain: 0.04, letterbox: 1 },

    render(ctx, t, S) {
      const cam = camAt(t);
      Art.captions(ctx, t, CAP);
      if (cam.back) {
        ctx.save();
        Art.cam(ctx, cam);
        backRoom(ctx, t);
        ctx.restore();
        return;
      }
      const A = {};
      ctx.save();
      Art.cam(ctx, cam);

      // ---------- background + the narrator's corner (blurred in close-ups) ----------
      const corner = (c) => {
        A.me = Art.person(c, meState(t));
        K.monstera(c, 346, 830, 0.94, t);
        K.pampas(c, 590, 833, 0.9, t);
      };
      if (cam.dof) Art.blurred(ctx, cam.dof, (c) => { drawBackground(c, t, cam); corner(c); }, 'shop11bg');
      else drawBackground(ctx, t, cam);

      // ---------- Embarrassment (behind the counter, or in the doorway) ----------
      const { o: eo, ex: ee } = embState(t);
      const doorway = ee.layer === 'doorway';
      if (!doorway) K.beads(ctx, t, beadPush(t));
      if (doorway) {
        ctx.save();
        ctx.beginPath(); ctx.rect(K.CURTAIN.x0, K.CURTAIN.top, K.CURTAIN.x1 - K.CURTAIN.x0, K.BACK_Y - K.CURTAIN.top + 20); ctx.clip();
        A.emb = K.person(ctx, eo, FLIPS.emb);
        ctx.fillStyle = U.rgba('#1e1410', 0.75 * ee.dark);
        ctx.fillRect(K.CURTAIN.x0, K.CURTAIN.top, K.CURTAIN.x1 - K.CURTAIN.x0, K.BACK_Y - K.CURTAIN.top);
        ctx.restore();
        K.beads(ctx, t, beadPush(t));
      }

      // ---------- the narrator in the corner + the plants that half-hide him ----------
      if (!cam.dof) corner(ctx);

      if (!doorway) {
        A.emb = K.person(ctx, eo, FLIPS.emb);
        if (ee.puff > 0) K.puff(ctx, A.emb.mouth.x - 4, A.emb.mouth.y + 2, ee.puff, -1, 1.05, '#ffffff', -0.9);
      }
      // a flower held below the counter top (hidden behind its front)
      const heldPos = (kind) => ({ x: A.emb.handF.x - 12, y: A.emb.handF.y + (kind === 'tulip' ? 32 : 36) });
      if (ee.held && !ee.heldAbove) {
        const p = heldPos(ee.held);
        if (ee.held === 'tulip') K.tulip(ctx, p.x, p.y, 0.9, t); else K.dusty(ctx, p.x, p.y, 0.9, t);
      }

      // ---------- the counter and what's on it ----------
      K.counter(ctx, PD);
      const ring = win(t, 54.2, 54.75, 0.15, 0.3);
      const pop = E(t, 54.45, 54.9, 'outQuad');
      K.register(ctx, { drawer: E(t, 54.45, 54.6, 'outBack') * (1 - E(t, 58.5, 59.0)), ring, tabs: '$200', pop: pop * (1 - E(t, 64, 64.6)), ding: win(t, 54.45, 55.0, 0.04, 0.4), key: t > 54.3 && t < 54.5 ? 8 : -1 });
      // the trimmed stems (and the scissors once he puts them down)
      drawStems(ctx, t);
      if (t >= 23.9) K.tulip(ctx, TULIP_AT, 684, 0.9, t);
      const dustyOnCounter = t >= 44.1 && t < 57.5;
      if (dustyOnCounter) K.dusty(ctx, DUSTY_AT, 684, 0.9, t, { droop: 0.5 + 0.06 * E(t, 47.5, 49.0) });
      if (t >= 44.08 && t < 45.2) K.puff(ctx, DUSTY_AT - 10, 676, (t - 44.08) / 1.1, 1, 1.2, '#d8ccb0');
      // the bills: slapped down, slide across, scooped up
      if (t >= 53.12 && t < 53.95) {
        const k = E(t, 53.12, 53.4, 'outCubic');
        K.bills(ctx, lerp(1104, 1196, k), 676, 0.9, 1 - k);
      }
      if (ee.held && ee.heldAbove) {
        const p = heldPos(ee.held);
        if (ee.held === 'tulip') K.tulip(ctx, p.x, p.y, 0.9, t); else K.dusty(ctx, p.x, p.y, 0.9, t);
        ctx.fillStyle = Art.CAST.emb.skin; ctx.beginPath(); ctx.arc(A.emb.handF.x, A.emb.handF.y, 7.5 * eo.s * 1.1, 0, TAU); ctx.fill();
      }
      if (ee.billsInHand) K.bills(ctx, A.emb.handF.x, A.emb.handF.y - 4, 0.75, 0.3);

      // ---------- the hikers (back to front) ----------
      const hs = [['h4', h4State(t)], ['h2', h2State(t)], ['h1', h1State(t)]].filter((h) => h[1]).sort((a, b) => a[1].o.y - b[1].o.y);
      for (const [who, st] of hs) {
        const o = st.o, ex = st.ex;
        if (who === 'h4') {
          const facing = o.facing || 1;
          const ph = (c) => { K.phone(c, { rec: ex.rec && Math.floor(t * 2) % 2 === 0, rot: ex.selfie ? -0.1 : -0.25, screen: ex.selfie ? '#f2e8d8' : '#6fb7ff' }); };
          if (ex.phone === 'B') o.holdB = ph; else o.holdF = ph;
        }
        if (who === 'h1' && ex.bills) o.holdF = (c) => K.bills(c, 6, -2, 0.8, 0.4);
        if (who === 'h1' && ex.carry) {
          const f = o.facing || 1;
          const lift = ex.trophy || 0; // over his head the pot sits on top of his hands
          o.holdF = (c) => { c.save(); c.scale(f, 1); K.dusty(c, f * 4, lerp(10, -4, lift), 0.86, t, { droop: 0.58 }); c.restore(); };
        }
        A[who] = K.person(ctx, o, FLIPS[who]);
        if (who === 'h4' && ex.flash > 0) Art.glow(ctx, A.h4.handF.x, A.h4.handF.y - 22, 110, '#ffffff', 0.85 * ex.flash);
        if (who === 'h1' && ex.dustFall > 0 && ex.dustFall < 1) {
          // dust sifts down out of the trophy onto his cap
          ctx.save(); ctx.fillStyle = '#d8ccb0';
          for (let i = 0; i < 12; i++) {
            const k = clamp(ex.dustFall * 1.4 - U.hash(i, 3) * 0.4);
            if (k <= 0 || k >= 1) continue;
            ctx.globalAlpha = (1 - k) * 0.7;
            ctx.beginPath(); ctx.arc(A.h1.handF.x - 20 + U.hash(i, 4) * 50, A.h1.handF.y - 30 + k * 120, 2 + U.hash(i, 5) * 2.5, 0, TAU); ctx.fill();
          }
          ctx.restore();
        }
      }
      // high-five impact (where the two palms meet)
      const hf = win(t, HF.t - 0.02, HF.t + 0.33, 0.02, 0.3);
      if (hf > 0 && A.h2 && A.h4) {
        const mx = (A.h2.handF.x + A.h4.handB.x) / 2, my = (A.h2.handF.y + A.h4.handB.y) / 2 - 6;
        ctx.save(); ctx.strokeStyle = '#fff6d0'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.globalAlpha = hf;
        for (let i = 0; i < 7; i++) { const a = i / 7 * TAU, r0 = 16 + (1 - hf) * 14; ctx.beginPath(); ctx.moveTo(mx + Math.cos(a) * r0, my + Math.sin(a) * r0); ctx.lineTo(mx + Math.cos(a) * (r0 + 14), my + Math.sin(a) * (r0 + 14)); ctx.stroke(); }
        ctx.restore();
      }

      // ---------- the door (in front of whoever is still in the doorway) + bell ----------
      K.door(ctx, PD, doorOpen(t), t);
      K.bell(ctx, K.swing(t, BELL));
      // silhouettes approaching behind the door glass
      if (t > DOOR_T - 0.85 && t < DOOR_T + 0.01) ghostInDoor(ctx, t);

      // ---------- light in the air ----------
      K.shafts(ctx, t, PD, 'day', 1);

      ctx.restore();

      // ---------- selfie flash (whole picture): instant on the click, gone in a blink ----------
      const fl = pulse(t, SNAPS[2], 0.06);
      if (fl > 0) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = `rgba(255,252,240,${0.45 * fl})`; ctx.fillRect(0, Art.PIC.top, W, Art.PIC.h); ctx.restore(); }

      // ---------- speech bubbles (screen space; each pinned in world space) ----------
      const { sp } = speakersOf(A, cam, t);
      const cues = [];
      BUB.forEach(([t0, t1, text, bo], i) => {
        if (t < t0 - 0.01 || t > t1 + 0.01) return;
        const spk = speakerFor(bo, sp);
        const pin = spk && pinFor(ctx, i);
        if (!pin) return;
        const c = toScreen(cam, pin), f = spk.facing || 1;
        cues.push([t0, t1, text, Object.assign({}, bo, { x: c.x, y: c.y, tx: spk.x + f * (spk.front + 8), ty: spk.mouth.y + 4 })]);
      });
      Art.bubbles(ctx, t, cues);
    },
  });

  /** trimmed stems on the counter; the scissors set down at ~6 s */
  function drawStems(ctx, t) {
    ctx.save();
    ctx.strokeStyle = '#4c7a3e'; ctx.lineCap = 'round'; ctx.lineWidth = 2.4;
    for (let i = 0; i < 6; i++) {
      const y = 676 + (i % 3) * 3, x0 = 1258 + i * 5, len = 46 + U.hash(i, 2) * 20;
      ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x0 + len, y - 3 - U.hash(i, 3) * 4); ctx.stroke();
    }
    // a few cut ends fall from the snips
    for (const s0 of SNIPS) {
      if (t < s0) continue;
      const k = clamp((t - s0) / 0.35);
      const y = lerp(652, 682, k * k);
      ctx.beginPath(); ctx.moveTo(1262 + s0 * 3, y); ctx.lineTo(1268 + s0 * 3, y + 1); ctx.stroke();
    }
    ctx.restore();
    if (t >= 6.05) { ctx.save(); ctx.translate(1310, 680); ctx.scale(-0.85, 0.85); K.scissors(ctx, 0.15); ctx.restore(); }
  }
  /** blurry shapes of the hikers approaching behind the door's glass */
  function ghostInDoor(ctx, t) {
    const L = K.leftPt;
    const a = L(K.DOOR.x0, K.DOOR.top), b = L(K.DOOR.x1, K.DOOR.top), c2 = L(K.DOOR.x1, 140), d = L(K.DOOR.x0, 140);
    ctx.save();
    poly(ctx, [[a.x, a.y], [b.x, b.y], [c2.x, c2.y], [d.x, d.y]]); ctx.clip();
    const k = E(t, DOOR_T - 0.85, DOOR_T - 0.05);
    ctx.globalAlpha = 0.45 * k;
    ctx.fillStyle = '#3a4a5c';
    for (const [dx, sc] of [[70, 1], [130, 0.9]]) {
      const x = a.x + dx + (1 - k) * 30, y = a.y + 150 - 30 * k * sc;
      ctx.beginPath(); ctx.arc(x, y, 26 * sc * (0.8 + 0.3 * k), 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.ellipse(x, y + 80, 46 * sc, 60, 0, 0, TAU); ctx.fill();
    }
    ctx.restore();
  }
})();
