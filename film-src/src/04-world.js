// ============================================================================
//  WORLD — the room, the bed, the man. World units: bed centred on x=0,
//  mattress top at y=0, floor at y=190, negative y is up.
// ============================================================================
const World = (() => {
  const FLOOR = 190;
  const HEAD = [-268, -46];          // centre of the man's head
  const R = rng(99);
  const STARS = Array.from({ length: 70 }, () => ({ x: R(), y: R(), s: 0.4 + R() * 1.2, p: R() * TAU, f: 0.5 + R() * 2 }));
  const MOTES = Array.from({ length: 70 }, () => ({ x: R(), y: R(), z: R(), p: R() * 100 }));
  const WIN = { x0: 40, x1: 320, y0: -560, y1: -210 };

  // smooth closed/open path through points (quadratic through midpoints)
  function smoothPath(ctx, pts, closed = true) {
    const n = pts.length;
    const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    if (closed) {
      const m0 = mid(pts[n - 1], pts[0]);
      ctx.moveTo(m0[0], m0[1]);
      for (let i = 0; i < n; i++) { const p = pts[i], m = mid(p, pts[(i + 1) % n]); ctx.quadraticCurveTo(p[0], p[1], m[0], m[1]); }
      ctx.closePath();
    } else {
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < n - 1; i++) { const p = pts[i], m = mid(p, pts[i + 1]); ctx.quadraticCurveTo(p[0], p[1], m[0], m[1]); }
      ctx.lineTo(pts[n - 1][0], pts[n - 1][1]);
    }
  }

  // light helper: paint additive light from a point, clipped to the current path
  function lightPath(ctx, path, lx, ly, r, c, a) {
    if (a <= 0.003) return;
    ctx.save(); ctx.clip(path);
    ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createRadialGradient(lx, ly, 0, lx, ly, r);
    g.addColorStop(0, rgba(c, a)); g.addColorStop(0.5, rgba(c, a * 0.35)); g.addColorStop(1, rgba(c, 0));
    ctx.fillStyle = g; ctx.fillRect(lx - r, ly - r, r * 2, r * 2);
    ctx.restore();
  }

  // ---------------------------------------------------------------- room
  function room(ctx, L, t) {
    // L: { moon, candle, cold, warm, family:[{x,y,c,a}], dark }
    const big = 6000;
    // back wall
    const wall = ctx.createLinearGradient(0, -900, 0, FLOOR);
    wall.addColorStop(0, rgba(mix([9, 10, 18], [26, 18, 16], L.warm * 0.6), 1));
    wall.addColorStop(1, rgba(mix([16, 17, 28], [38, 27, 22], L.warm * 0.7), 1));
    ctx.fillStyle = wall; ctx.fillRect(-big, -big, big * 2, big + FLOOR);
    // wallpaper: faint vertical stripes
    ctx.fillStyle = 'rgba(255,255,255,0.012)';
    for (let x = -1800; x < 1800; x += 46) ctx.fillRect(x, -1600, 14, 1600 + FLOOR);
    // floor
    const fl = ctx.createLinearGradient(0, FLOOR, 0, FLOOR + 420);
    fl.addColorStop(0, rgba(mix([13, 12, 16], [34, 22, 16], L.warm * 0.6), 1));
    fl.addColorStop(1, 'rgb(4,4,7)');
    ctx.fillStyle = fl; ctx.fillRect(-big, FLOOR, big * 2, big);
    ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 2;
    for (let i = 1; i < 9; i++) { const y = FLOOR + i * i * 6; ctx.beginPath(); ctx.moveTo(-big, y); ctx.lineTo(big, y); ctx.stroke(); }
    // baseboard
    ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(-big, FLOOR - 16, big * 2, 16);
    ctx.fillStyle = 'rgba(255,255,255,0.03)'; ctx.fillRect(-big, FLOOR - 16, big * 2, 2);

    // window with night sky
    const { x0, x1, y0, y1 } = WIN;
    const sky = ctx.createLinearGradient(0, y0, 0, y1);
    sky.addColorStop(0, rgba(mix([10, 16, 38], [30, 20, 40], L.warm * 0.3), 1));
    sky.addColorStop(1, rgba(mix([28, 38, 70], [60, 40, 50], L.warm * 0.3), 1));
    ctx.fillStyle = sky; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
    ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.clip();
    for (const s of STARS) {
      const tw = 0.5 + 0.5 * Math.sin(t * s.f + s.p);
      Draw.glow(ctx, x0 + s.x * (x1 - x0), y0 + s.y * (y1 - y0) * 0.85, 3 + s.s * 3, [220, 230, 255], 0.35 + 0.5 * tw, 1);
    }
    // moon
    const mx = x0 + (x1 - x0) * 0.66, my = y0 + 120;
    Draw.glow(ctx, mx, my, 160, [170, 195, 240], 0.45 * L.moon);
    ctx.fillStyle = rgba([232, 236, 246], 0.92 * clamp(L.moon + 0.2)); ctx.beginPath(); ctx.arc(mx, my, 26, 0, TAU); ctx.fill();
    ctx.fillStyle = 'rgba(160,170,200,0.25)'; ctx.beginPath(); ctx.arc(mx - 7, my - 5, 6, 0, TAU); ctx.arc(mx + 8, my + 7, 4, 0, TAU); ctx.fill();
    // distant hills/rooftops
    ctx.fillStyle = 'rgba(5,7,14,0.95)';
    ctx.beginPath(); ctx.moveTo(x0, y1);
    for (let x = x0; x <= x1; x += 10) ctx.lineTo(x, y1 - 30 - Noise.fbm(x * 0.008, 3) * 30 - (Math.sin(x * 0.05) > 0.7 ? 18 : 0));
    ctx.lineTo(x1, y1); ctx.closePath(); ctx.fill();
    // whatever stands outside the glass (death waits out here)
    if (L.outside) L.outside(ctx, WIN);
    // frost creeping over the pane from the corners
    if (L.frost > 0.01) {
      const corners = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]];
      for (const [cx_, cy_] of corners) {
        const g = ctx.createRadialGradient(cx_, cy_, 0, cx_, cy_, 220 * L.frost);
        g.addColorStop(0, rgba([221, 232, 245], 0.38 * L.frost)); g.addColorStop(0.6, rgba([221, 232, 245], 0.12 * L.frost)); g.addColorStop(1, rgba([221, 232, 245], 0));
        ctx.fillStyle = g; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
      }
      ctx.strokeStyle = rgba([230, 240, 255], 0.22 * L.frost); ctx.lineWidth = 0.8;
      const FR = rng(31);
      for (let i = 0; i < 40; i++) {
        const [cx_, cy_] = corners[i % 4]; let x = cx_, y = cy_, a = Math.atan2((y0 + y1) / 2 - cy_, (x0 + x1) / 2 - cx_) + (FR() - 0.5) * 1.6;
        const len = (40 + FR() * 120) * L.frost;
        ctx.beginPath(); ctx.moveTo(x, y);
        for (let k = 0; k < 6; k++) { a += (FR() - 0.5) * 0.9; x += Math.cos(a) * len / 6; y += Math.sin(a) * len / 6; ctx.lineTo(x, y); }
        ctx.stroke();
      }
    }
    ctx.restore();
    // window frame & mullions
    ctx.strokeStyle = 'rgb(12,11,15)'; ctx.lineWidth = 16; ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
    ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo((x0 + x1) / 2, y0); ctx.lineTo((x0 + x1) / 2, y1); ctx.moveTo(x0, (y0 + y1) / 2); ctx.lineTo(x1, (y0 + y1) / 2); ctx.stroke();
    ctx.fillStyle = 'rgb(14,12,16)'; ctx.fillRect(x0 - 26, y1 + 4, x1 - x0 + 52, 14); // sill
    ctx.strokeStyle = rgba([170, 195, 240], 0.15 * L.moon); ctx.lineWidth = 2; ctx.strokeRect(x0 + 8, y0 + 8, x1 - x0 - 16, y1 - y0 - 16);
    // sheer curtains, breathing in a draught
    for (const side of [-1, 1]) {
      const cx = side < 0 ? x0 - 10 : x1 + 10;
      ctx.beginPath();
      const sway = Noise.n1(t * 0.18 + side) * 14;
      ctx.moveTo(cx - side * -6, y0 - 30);
      ctx.quadraticCurveTo(cx + side * (-40 - sway), (y0 + y1) / 2, cx + side * (-10 - sway * 1.6), y1 + 60);
      ctx.lineTo(cx + side * 40, y1 + 60);
      ctx.quadraticCurveTo(cx + side * (30 + sway * 0.5), (y0 + y1) / 2, cx + side * 46, y0 - 30);
      ctx.closePath();
      ctx.fillStyle = rgba(mix([60, 70, 100], [110, 80, 60], L.warm * 0.5), 0.2 + 0.1 * L.moon); ctx.fill();
    }
    ctx.fillStyle = 'rgb(10,9,12)'; ctx.fillRect(x0 - 70, y0 - 40, x1 - x0 + 140, 9); // rod
    // heavy drapes that close over the glass at the very end
    if (L.drape > 0.001) {
      const half = (x1 - x0) / 2 + 60, cover = half * Ease.inOut(clamp(L.drape));
      for (const side of [-1, 1]) {
        const ox = side < 0 ? x0 - 60 : x1 + 60, inner = ox - side * cover;
        const g = ctx.createLinearGradient(Math.min(ox, inner), 0, Math.max(ox, inner), 0);
        const base = mix([42, 24, 22], [110, 66, 50], clamp(L.warm * 0.8));
        for (let i = 0; i <= 8; i++) g.addColorStop(i / 8, rgba(mix(base, [0, 0, 0], i % 2 ? 0.45 : 0.05), 1));
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.moveTo(ox, y0 - 36);
        ctx.lineTo(inner, y0 - 36);
        ctx.quadraticCurveTo(inner + side * 6, (y0 + y1) / 2, inner - side * 4, y1 + 70);
        ctx.lineTo(ox, y1 + 70); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = rgba([255, 190, 140], 0.12 * clamp(L.warm)); ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(inner, y0 - 36); ctx.quadraticCurveTo(inner + side * 6, (y0 + y1) / 2, inner - side * 4, y1 + 70); ctx.stroke();
      }
    }

    // the door (right) — open a crack into a deeper dark
    const dx0 = 470, dx1 = 610, dy0 = -330;
    ctx.fillStyle = 'rgb(8,8,12)'; ctx.fillRect(dx0 - 12, dy0 - 12, dx1 - dx0 + 24, FLOOR - dy0 + 12);
    ctx.fillStyle = rgba([0, 0, 0], 1); ctx.fillRect(dx0, dy0, dx1 - dx0, FLOOR - dy0);
    const open = L.door ?? 0.25;
    ctx.fillStyle = rgba(mix([18, 17, 24], [40, 29, 24], L.warm * 0.5), 1);
    ctx.fillRect(dx0 + (dx1 - dx0) * open, dy0, (dx1 - dx0) * (1 - open), FLOOR - dy0);
    ctx.fillStyle = 'rgba(255,255,255,0.03)'; ctx.fillRect(dx0 + (dx1 - dx0) * open, dy0, 3, FLOOR - dy0);
    ctx.fillStyle = 'rgba(200,170,120,0.25)'; ctx.beginPath(); ctx.arc(dx0 + (dx1 - dx0) * open + 16, -10, 5, 0, TAU); ctx.fill();

    // wall clock with a pendulum, between the window and the door
    const cx = 414, cy = -452, cr = 34;
    const tt = L.clock ?? t;
    const caseC = rgba(mix([14, 12, 14], [44, 30, 22], clamp(L.warm * 0.8)), 1);
    ctx.fillStyle = caseC;
    ctx.beginPath(); ctx.roundRect ? ctx.roundRect(cx - 24, cy + 18, 48, 150, 8) : ctx.rect(cx - 24, cy + 18, 48, 150); ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(cx - 16, cy + 34, 32, 120);
    // pendulum: one swing per second, in step with the tick
    const sw = Math.sin(tt * Math.PI) * 0.32 * (L.pendulum ?? 1);
    ctx.save(); ctx.translate(cx, cy + 30); ctx.rotate(sw);
    ctx.strokeStyle = rgba(mix([60, 60, 70], [170, 130, 80], clamp(L.warm)), 0.8); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 98); ctx.stroke();
    ctx.fillStyle = rgba(mix([90, 92, 110], [220, 170, 100], clamp(L.warm)), 0.85); ctx.beginPath(); ctx.arc(0, 104, 9, 0, TAU); ctx.fill();
    ctx.restore();
    ctx.fillStyle = caseC; ctx.beginPath(); ctx.arc(cx, cy, cr + 7, 0, TAU); ctx.fill();
    const face = mix(mix([46, 50, 64], [150, 160, 190], clamp(L.moon * 0.3)), [150, 120, 84], clamp(L.warm));
    ctx.fillStyle = rgba(face, 0.85); ctx.beginPath(); ctx.arc(cx, cy, cr, 0, TAU); ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.lineWidth = 2;
    for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * (cr - 7), cy + Math.sin(a) * (cr - 7)); ctx.lineTo(cx + Math.cos(a) * (cr - 3), cy + Math.sin(a) * (cr - 3)); ctx.stroke(); }
    const sec = Math.floor(tt + 0.5);
    const hand = (a, l, w) => { ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.sin(a) * l, cy - Math.cos(a) * l); ctx.stroke(); };
    ctx.strokeStyle = 'rgba(10,8,8,0.85)'; hand(TAU * (11.85 / 12) + tt / 43200 * TAU, cr * 0.55, 3); hand(TAU * 0.95 + tt / 3600 * TAU, cr * 0.8, 2);
    ctx.strokeStyle = 'rgba(120,30,20,0.75)'; hand(TAU * (sec % 60) / 60, cr * 0.86, 1);
  }

  // ---------------------------------------------------------------- lights onto room surfaces
  function roomLight(ctx, L) {
    // moonbeam: a slanted shaft from the window to the bed and floor
    if (L.moon > 0.01) {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      const { x0, x1, y0, y1 } = WIN;
      const sh = 380, dropY = FLOOR + 40;
      const beam = new Path2D();
      const bl = L.beamLen ?? 1;
      const bx1 = lerp(x1 - 10, x1 - sh - 20, bl), bx0 = lerp(x0 + 10, x0 - sh - 180, bl), by = lerp(y0 + 20, dropY, bl);
      beam.moveTo(x0 + 10, y0 + 20); beam.lineTo(x1 - 10, y0 + 20);
      beam.lineTo(bx1, by); beam.lineTo(bx0, by); beam.closePath();
      const g = ctx.createLinearGradient(x1, y0, x0 - sh, dropY);
      g.addColorStop(0, rgba([150, 175, 225], 0.11 * L.moon));
      g.addColorStop(0.6, rgba([150, 175, 225], 0.05 * L.moon));
      g.addColorStop(1, rgba([150, 175, 225], 0.0));
      ctx.fillStyle = g; ctx.fill(beam);
      ctx.restore();
      L._beam = beam;
    }
    // candle glow on the wall
    if (L.candle > 0.01) {
      const [fx, fy] = L.candlePos;
      Draw.glow(ctx, fx, fy, 900 * (0.7 + 0.3 * L.candle), [255, 160, 80], 0.13 * L.candle * L.flick);
      Draw.glow(ctx, fx, fy, 260, [255, 190, 120], 0.25 * L.candle * L.flick);
    }
    // family light washing the room
    for (const fl of L.family || []) {
      if (fl.a > 0.01) Draw.glow(ctx, fl.x, fl.y, fl.r || 520, fl.c, 0.042 * fl.a);
    }
  }

  // dust motes drifting through the moonlight
  function motes(ctx, L, t) {
    if (!L._beam || L.moon < 0.02) return;
    for (const m of MOTES) {
      const x = -650 + ((m.x * 1000 + Noise.n2(m.p, t * 0.05) * 120 + t * (4 + m.z * 6)) % 1000 + 1000) % 1000;
      const y = -560 + ((m.y * 760 + Noise.n2(m.p + 7, t * 0.04) * 90 + t * 3) % 760 + 760) % 760;
      if (!ctx.isPointInPath(L._beam, x, y)) continue;
      const tw = 0.5 + 0.5 * Math.sin(t * (0.6 + m.z) + m.p);
      Draw.glow(ctx, x, y, 2 + m.z * 4, [200, 215, 255], (0.25 + 0.5 * tw) * L.moon, 1);
    }
  }

  // ---------------------------------------------------------------- candle + bedside table
  function candle(ctx, L, t) {
    // table
    const tx0 = -540, tx1 = -404, ty = 22;
    ctx.fillStyle = rgba(mix([14, 12, 14], [44, 28, 20], L.candle * 0.8), 1);
    ctx.fillRect(tx0, ty, tx1 - tx0, 14);
    ctx.fillRect(tx0 + 10, ty + 14, 10, FLOOR - ty - 14); ctx.fillRect(tx1 - 20, ty + 14, 10, FLOOR - ty - 14);
    ctx.fillRect(tx0 + 4, ty + 60, tx1 - tx0 - 8, 8);
    ctx.fillStyle = rgba([255, 180, 110], 0.18 * L.candle); ctx.fillRect(tx0, ty, tx1 - tx0, 2);
    // a small framed photograph and a glass of water
    ctx.fillStyle = 'rgb(12,10,10)'; ctx.fillRect(-528, ty - 46, 34, 46);
    ctx.fillStyle = rgba(mix([30, 30, 40], [110, 85, 60], L.candle), 0.7); ctx.fillRect(-524, ty - 42, 26, 38);
    ctx.strokeStyle = rgba([200, 220, 255], 0.18 + 0.2 * L.candle); ctx.lineWidth = 2; ctx.strokeRect(-425, ty - 30, 14, 30);
    // candle body (burns down)
    const cx = -466, h = 64 * (L.wax ?? 1) + 6;
    const body = ctx.createLinearGradient(cx - 9, 0, cx + 9, 0);
    body.addColorStop(0, rgba(mix([60, 55, 50], [230, 200, 160], L.candle), 1));
    body.addColorStop(1, rgba(mix([30, 28, 26], [150, 110, 80], L.candle), 1));
    ctx.fillStyle = body; ctx.fillRect(cx - 9, ty - h, 18, h);
    ctx.fillStyle = 'rgb(20,16,14)'; ctx.beginPath(); ctx.ellipse(cx, ty - 1, 22, 5, 0, 0, TAU); ctx.fill(); // holder
    ctx.strokeStyle = 'rgba(20,10,5,.9)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(cx, ty - h); ctx.lineTo(cx + 1, ty - h - 7); ctx.stroke();
    L.candlePos = [cx, ty - h - 20];
    // flame
    const fl = L.candle;
    if (fl > 0.01) {
      const n = Noise.n1(t * 3.1), n2 = Noise.n1(t * 7.3 + 4);
      const fh = (26 + n * 4) * fl * (1 + 0.15 * (L.gutter || 0) * n2), fw = 6.5 * (0.6 + 0.4 * fl);
      const bx = cx + n2 * 1.5 * (1 + (L.gutter || 0) * 3), by = ty - h - 4;
      const tipX = bx + n * 3 * (1 + (L.gutter || 0) * 2) + Math.sin(L.candleLean || 0) * fh, tipY = by - fh * Math.cos(L.candleLean || 0);
      Draw.glow(ctx, bx, by - fh * 0.45, 60 * fl, [255, 170, 80], 0.55 * L.flick);
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const fg = ctx.createLinearGradient(0, by, 0, tipY);
      fg.addColorStop(0, rgba([120, 140, 255], 0.55)); fg.addColorStop(0.18, rgba([255, 240, 200], 0.95));
      fg.addColorStop(0.6, rgba([255, 180, 80], 0.85)); fg.addColorStop(1, rgba([255, 120, 40], 0));
      ctx.fillStyle = fg;
      ctx.beginPath(); ctx.moveTo(bx, by + 2);
      ctx.bezierCurveTo(bx - fw * 1.3, by - fh * 0.15, bx - fw * 0.7, by - fh * 0.65, tipX, tipY);
      ctx.bezierCurveTo(bx + fw * 0.7, by - fh * 0.65, bx + fw * 1.3, by - fh * 0.15, bx, by + 2);
      ctx.fill(); ctx.restore();
      Draw.glow(ctx, bx, by - fh * 0.3, 12, [255, 250, 230], 0.7 * fl, 1);
    }
    // smoke after it goes out
    if (L.smoke > 0.001) {
      ctx.save(); ctx.strokeStyle = rgba([180, 185, 200], 0.18 * L.smoke); ctx.lineWidth = 2.2; ctx.lineCap = 'round';
      for (let k = 0; k < 2; k++) {
        ctx.beginPath(); const sx = cx + 1, sy = ty - h - 8;
        ctx.moveTo(sx, sy);
        for (let i = 1; i < 30; i++) ctx.lineTo(sx + Noise.n2(i * 0.12 + k * 3, t * 0.5 - i * 0.05) * i * 2.2, sy - i * 9);
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  // ---------------------------------------------------------------- bed
  function bed(ctx, L) {
    const wood = mix([16, 12, 12], [62, 38, 24], L.warm * 0.9);
    // under-bed shadow
    ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.beginPath(); ctx.ellipse(10, FLOOR + 6, 460, 18, 0, 0, TAU); ctx.fill();
    // headboard
    ctx.fillStyle = rgba(wood, 1);
    ctx.beginPath(); ctx.moveTo(-380, FLOOR); ctx.lineTo(-380, -168); ctx.quadraticCurveTo(-366, -214, -352, -168); ctx.lineTo(-352, FLOOR); ctx.fill();
    ctx.beginPath(); ctx.arc(-366, -199, 11, 0, TAU); ctx.fill();
    // footboard
    ctx.beginPath(); ctx.moveTo(366, FLOOR); ctx.lineTo(366, -62); ctx.quadraticCurveTo(378, -96, 390, -62); ctx.lineTo(390, FLOOR); ctx.fill();
    ctx.beginPath(); ctx.arc(378, -86, 10, 0, TAU); ctx.fill();
    // frame rail + legs
    ctx.fillRect(-356, 44, 728, 30);
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(-356, 66, 728, 8);
    ctx.fillStyle = rgba(mix(wood, [255, 200, 150], 0.08 * L.warm), 1);
    ctx.fillRect(-356, 44, 728, 3);
    // mattress
    const mg = ctx.createLinearGradient(0, -4, 0, 48);
    mg.addColorStop(0, rgba(mix([40, 44, 60], [120, 100, 86], L.warm * 0.7), 1));
    mg.addColorStop(1, rgba(mix([18, 20, 30], [60, 46, 40], L.warm * 0.7), 1));
    ctx.fillStyle = mg; ctx.beginPath(); ctx.roundRect ? ctx.roundRect(-354, -4, 722, 50, 12) : ctx.rect(-354, -4, 722, 50); ctx.fill();
    // pillow
    ctx.beginPath();
    smoothPath(ctx, [[-350, -6], [-345, -40], [-300, -52], [-230, -46], [-196, -30], [-200, -4], [-270, 4]]);
    const pg = ctx.createLinearGradient(0, -52, 0, 4);
    pg.addColorStop(0, rgba(mix([70, 78, 104], [190, 170, 150], L.warm * 0.7), 1));
    pg.addColorStop(1, rgba(mix([34, 38, 54], [100, 84, 74], L.warm * 0.7), 1));
    ctx.fillStyle = pg; ctx.fill();
  }

  // blanket surface height along the body (breath raises the chest)
  function blanketTop(x, br) {
    const chest = -64 - br * 7, belly = -50 - br * 3;
    const keys = [[-216, -30], [-196, -50], [-150, chest], [-80, belly], [0, -46], [80, -44], [150, -62], [200, -50], [270, -42], [312, -76], [338, -60], [356, -18]];
    if (x <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) if (x <= keys[i][0]) { const p = keys[i - 1], k = keys[i]; return lerp(p[1], k[1], Ease.sine((x - p[0]) / (k[0] - p[0]))); }
    return keys[keys.length - 1][1];
  }

  // ---------------------------------------------------------------- the man
  // M: { breath, eyes (1 open..0 closed), wink, smile, hand:{x,y,w}, hair:{x,y,w}, inner, t, held }
  function man(ctx, L, M) {
    const t = M.t;
    const skinBase = mix([44, 34, 34], [150, 105, 84], clamp(L.warm * 0.85 + L.candle * 0.15));
    const skin = mix(skinBase, [255, 240, 220], M.inner * 0.45);
    const [hx, hy] = HEAD;
    const rise = M.breath * 2.2;
    // ---- head: an anatomically-proportioned profile, lying face-up, mostly
    //      backlit (the moon and the family are behind him) with a living rim.
    const rot0 = (M.turn || 0);   // + tucks the chin toward the chest (to look toward the feet)
    const sm = M.smile;
    // upright profile (x forward, y down; head height 100) -> lying (X along body, Y up = -forward)
    const U = [
      [-35, 0], [-22, 2], [-8, 9], [-1, 20], [1, 30], [0, 37], [-3, 42], [2, 50], [8.5, 59], [11, 63], [9.5, 66], [4, 67.5], [1, 68],
      [2.6, 72], [1.8, 75.5 + sm * 0.3], [2.2, 79], [-1.8, 84], [1, 91], [-3, 98], [-12, 101.5], [-22, 103], [-28, 106], [-31, 125], [-33, 150],
      [-80, 150], [-76, 125], [-74, 97], [-79, 77], [-85, 55], [-82, 30], [-71, 11], [-55, 2],
    ];
    const s = 0.86, X = (x, y) => [(y - 52) * s, (-x - 42) * s];
    const head = new Path2D(); smoothPath(head, U.map(([x, y]) => X(x, y)));
    const lightUp = clamp(L.warm * 0.55 + L.candle * 0.12 + M.inner * 0.6);
    const sil = mix(mix([16, 13, 16], [70, 46, 38], lightUp), [255, 236, 214], M.inner * 0.35);
    ctx.save(); ctx.translate(hx + 30, hy - rise * 0.3 + 4); ctx.rotate(rot0); ctx.translate(-30, -4);
    ctx.fillStyle = rgba(sil, 1); ctx.fill(head);
    ctx.save(); ctx.clip(head);
    // volume: subtle warmth from the candle on the crown side, cool fill on the face plane
    ctx.globalCompositeOperation = 'lighter';
    const cg = ctx.createRadialGradient(-75, 0, 5, -75, 0, 110);
    cg.addColorStop(0, rgba([255, 160, 80], 0.28 * L.candle * L.flick)); cg.addColorStop(1, rgba([255, 160, 80], 0));
    ctx.fillStyle = cg; ctx.fillRect(-60, -70, 140, 120);
    const fg = ctx.createLinearGradient(0, -48, 0, -18);
    const rimC = mix(mix([160, 185, 235], [255, 214, 170], clamp(L.warm)), [255, 244, 228], M.inner);
    fg.addColorStop(0, rgba(rimC, 0.12 + 0.12 * lightUp)); fg.addColorStop(1, rgba(rimC, 0));
    ctx.fillStyle = fg; ctx.fillRect(-60, -70, 140, 60);
    // the rim: a bright inner edge along the face profile, fading toward the pillow
    const rg = ctx.createLinearGradient(0, -50, 0, -10);
    const rimA = clamp(0.35 * L.moon + 0.55 * clamp(L.warm) + 0.4 * M.inner + (M.rim || 0));
    rg.addColorStop(0, rgba(rimC, 0.95 * rimA)); rg.addColorStop(0.6, rgba(rimC, 0.35 * rimA)); rg.addColorStop(1, rgba(rimC, 0));
    ctx.strokeStyle = rg; ctx.lineWidth = 3.2; ctx.stroke(head);
    ctx.lineWidth = 9; ctx.globalAlpha = 0.25; ctx.stroke(head); ctx.globalAlpha = 1;
    // jawline, cheekbone and eye-socket shading (very low contrast)
    ctx.globalCompositeOperation = 'source-over';
    ctx.strokeStyle = 'rgba(0,0,0,0.22)'; ctx.lineWidth = 1.2;
    ctx.beginPath(); const j0 = X(-6, 99), j1 = X(-46, 90), j2 = X(-50, 74); ctx.moveTo(j0[0], j0[1]); ctx.quadraticCurveTo(j1[0], j1[1], j2[0], j2[1]); ctx.stroke();
    ctx.fillStyle = 'rgba(0,0,0,0.16)'; const so = X(-8, 46); ctx.beginPath(); ctx.ellipse(so[0], so[1], 7, 4.5, 0, 0, TAU); ctx.fill();
    ctx.restore();
    // ear
    const ec0 = X(-49, 56);
    ctx.fillStyle = rgba(mix(sil, [255, 200, 160], 0.06 + 0.1 * lightUp), 1);
    ctx.beginPath(); ctx.ellipse(ec0[0], ec0[1], 12, 6.8, 0.12, 0, TAU); ctx.fill();
    ctx.strokeStyle = rgba(rimC, 0.25 * rimA); ctx.lineWidth = 0.9;
    ctx.beginPath(); ctx.ellipse(ec0[0], ec0[1] - 0.5, 12, 6.8, 0.12, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
    ctx.strokeStyle = 'rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.ellipse(ec0[0] + 0.5, ec0[1], 7, 3.4, 0.12, -2.4, 1.6); ctx.stroke();
    // wrinkles catching the light
    ctx.strokeStyle = rgba(rimC, 0.12 + 0.12 * lightUp); ctx.lineWidth = 0.7; ctx.lineCap = 'round';
    for (const [a0, b0, a1, b1] of [[-2, 17, -6, 21], [-1, 23, -6, 27], [-2, 29, -6, 32]]) { const p0 = X(a0, b0), p1 = X(a1, b1); ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke(); }
    ctx.strokeStyle = 'rgba(0,0,0,0.3)';
    { const p0 = X(5, 66), p1 = X(-1 - sm, 69), p2 = X(-4 - sm * 1.5, 71 - sm * 1.5); ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.quadraticCurveTo(p1[0], p1[1], p2[0], p2[1]); ctx.stroke(); } // nasolabial, ends above the mouth
    // mouth corner: lifts with the smile
    ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 1;
    { const p0 = X(1.6, 75.5), p1 = X(-3, 76 - sm * 3), p2 = X(-6.5, 75.5 - sm * 8); ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.quadraticCurveTo(p1[0], p1[1], p2[0], p2[1]); ctx.stroke(); }
    // eye: closed lid, or open with a catchlight; the wink squeezes, lifts the cheek and brow
    const open = clamp(M.eyes) * (1 - clamp(M.wink));
    const [ex, ey] = X(-6, 46);
    if (open > 0.04) {
      ctx.fillStyle = rgba([210, 205, 200], 0.45 * open);
      ctx.beginPath(); ctx.moveTo(ex - 4, ey + 0.4); ctx.quadraticCurveTo(ex, ey - 3.4 * open, ex + 4, ey + 0.2); ctx.quadraticCurveTo(ex, ey + 1.5, ex - 4, ey + 0.4); ctx.fill();
      const gx = M.gaze || 0;
      ctx.fillStyle = 'rgba(10,8,8,0.95)'; ctx.beginPath(); ctx.arc(ex + 0.4 + gx * 1.6, ey - 0.6 * open, 1.6, 0, TAU); ctx.fill();
      Draw.glow(ctx, ex + 0.9 + gx * 1.6, ey - 1.1 * open, 2.2, [255, 240, 220], 0.95 * open, 1);
    }
    ctx.strokeStyle = rgba(mix([10, 6, 6], rimC, 0.25), 0.85); ctx.lineWidth = 1.1;
    ctx.beginPath(); ctx.moveTo(ex - 4, ey + 0.5);
    ctx.quadraticCurveTo(ex, ey - (open > 0.04 ? 3.6 * open : -1.2 + M.wink * 1.8), ex + 4, ey + 0.2 - M.wink * 0.7); ctx.stroke();
    if (M.wink > 0.05) {
      ctx.strokeStyle = rgba(rimC, 0.55 * M.wink); ctx.lineWidth = 0.8;
      for (let i = -1; i <= 1; i++) { ctx.beginPath(); ctx.moveTo(ex + 5, ey + 1 + i * 1.6); ctx.lineTo(ex + 9.5, ey + 1.5 + i * 3.2); ctx.stroke(); }
    }
    if (M.glint > 0.01) {   // a four-point star glint at the corner of the winking eye
      const gk = M.glint, gx = ex + 9, gy = ey - 6;
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = rgba([255, 246, 216], 0.95 * gk);
      ctx.beginPath(); ctx.moveTo(gx, gy - 9 * gk); ctx.quadraticCurveTo(gx, gy, gx + 9 * gk, gy); ctx.quadraticCurveTo(gx, gy, gx, gy + 9 * gk); ctx.quadraticCurveTo(gx, gy, gx - 9 * gk, gy); ctx.quadraticCurveTo(gx, gy, gx, gy - 9 * gk); ctx.fill();
      ctx.restore(); Draw.glow(ctx, gx, gy, 14 * gk, [255, 240, 200], 0.8 * gk, 1);
    }
    // eyebrow: a white, wilful tuft that catches the light
    const browY = M.wink * 4.5 + sm * 0.5;
    ctx.strokeStyle = rgba(mix([220, 222, 230], rimC, 0.5), 0.55 + 0.4 * rimA); ctx.lineWidth = 0.9;
    for (let i = 0; i < 9; i++) {
      const [bx, by] = X(1 - Math.abs(i - 4) * 0.25, 33 + i * 1.3);
      ctx.beginPath(); ctx.moveTo(bx, by); ctx.quadraticCurveTo(bx + 1.6, by - 2 - browY, bx + 3.4 + (i % 2), by - 2.4 - browY - (i % 3) * 0.6); ctx.stroke();
    }
    // hair: a fine white horseshoe fringe around the back of the skull, lit from behind
    const hair = M.hair || { w: 0 };
    const hairC = mix(mix([200, 206, 222], [255, 236, 210], clamp(L.warm * 0.6)), [255, 246, 232], M.inner);
    ctx.lineCap = 'round';
    for (let i = 0; i < 54; i++) {
      const u = i / 53;
      const th = lerp(3.55, 1.55, u);                       // temple -> crown -> nape
      const bx = -5 + 41 * Math.cos(th), by = 4 + 32 * Math.sin(th);
      const nx = Math.cos(th), ny = Math.sin(th), tx = Math.sin(th), ty = -Math.cos(th);
      const len = 5 + 8 * Math.abs(Math.sin(i * 12.9898)) * (1 - Math.abs(u - 0.4) * 0.6);
      let ox = (tx * 0.75 + nx * 0.55) * len, oy = (ty * 0.75 + ny * 0.55) * len;
      if (hair.w > 0.001) {
        const [lx, ly] = Draw.rot(hair.x - (hx + 30), hair.y - (hy - rise * 0.3 + 4), -rot0);
        const qx = lx + 30, qy = ly + 4;
        const d = Math.hypot(qx - bx, qy - by), k = hair.w * Math.exp(-d * d / 420);
        ox += (qx - bx) * 0.35 * k + Math.sin(M.t * 4 + i) * 1.5 * k; oy += (qy - by) * 0.35 * k - 2 * k;
      }
      const sw = Noise.n2(i * 0.31, M.t * 0.35) * 1.2;
      const lit = 0.3 + 0.55 * clamp(1 - by / 30) * (0.4 + rimA);
      ctx.strokeStyle = rgba(hairC, clamp(lit) * (0.5 + 0.5 * Math.abs(Math.sin(i * 7.31))));
      ctx.lineWidth = 0.7;
      ctx.beginPath(); ctx.moveTo(bx, by); ctx.quadraticCurveTo(bx + ox * 0.5 + nx * 1.5 + sw, by + oy * 0.5 + ny * 1.5, bx + ox + sw, by + oy); ctx.stroke();
    }
    Draw.glow(ctx, -44, -4, 26, hairC, 0.1 + 0.15 * rimA);
    ctx.restore();

    // ---- pyjama collar where the neck meets the chest
    const collar = mix(mix([30, 32, 46], [120, 86, 74], clamp(L.warm * 0.7)), [255, 236, 210], M.inner * 0.3);
    ctx.fillStyle = rgba(collar, 1);
    ctx.beginPath(); ctx.moveTo(hx + 60, hy - 12 - rise); ctx.quadraticCurveTo(hx + 72, hy - 18 - rise, hx + 92, hy - 12 - rise * 1.5);
    ctx.lineTo(hx + 100, hy + 36); ctx.lineTo(hx + 56, hy + 36); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = rgba(mix([160, 185, 235], [255, 214, 170], clamp(L.warm)), 0.25); ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(hx + 60, hy - 12 - rise); ctx.quadraticCurveTo(hx + 72, hy - 18 - rise, hx + 92, hy - 12 - rise * 1.5); ctx.stroke();

    // ---- blanket over the body
    const br = M.breath;
    const blanket = new Path2D();
    // tug: the quilt's foot end is pulled toward +x (the reaper hooking it)
    const tug = M.tug || 0;
    const tx_ = x => x + (x > 200 ? Math.pow((x - 200) / 170, 2) * tug * 90 : 0);
    const ty_ = (x, y) => y + (x > 240 ? Math.pow((x - 240) / 130, 2) * tug * -26 : 0);
    blanket.moveTo(-222, 64);
    blanket.quadraticCurveTo(-232, 8, -216, blanketTop(-216, br));
    for (let x = -216; x <= 356; x += 6) blanket.lineTo(tx_(x), ty_(x, blanketTop(x, br)));
    blanket.quadraticCurveTo(tx_(372), ty_(372, 10), tx_(370), ty_(370, 70) + tug * 10);
    // hem with folds
    for (let x = 370; x >= -222; x -= 12) blanket.lineTo(tx_(x), ty_(x, 66 + Math.sin(x * 0.07) * 4 + Math.sin(x * 0.023) * 6) + (x > 240 ? tug * 14 : 0));
    blanket.closePath();
    M.quiltCorner = [tx_(370), ty_(370, 40)];
    const bg = ctx.createLinearGradient(0, -70, 0, 70);
    const bc = mix(mix([34, 40, 66], [120, 70, 60], L.warm * 0.8), [255, 230, 210], M.inner * 0.25);
    bg.addColorStop(0, rgba(mix(bc, [255, 255, 255], 0.06), 1)); bg.addColorStop(1, rgba(mix(bc, [0, 0, 0], 0.55), 1));
    ctx.fillStyle = bg; ctx.fill(blanket);
    // quilt stitching
    ctx.save(); ctx.clip(blanket);
    // the sheet, turned down over the quilt at his chest
    ctx.fillStyle = rgba(mix(mix([70, 78, 104], [196, 176, 156], L.warm * 0.7), [255, 240, 225], M.inner * 0.3), 1);
    ctx.beginPath(); ctx.moveTo(-240, -80); ctx.lineTo(-176, -80); ctx.quadraticCurveTo(-170, 0, -182, 80); ctx.lineTo(-240, 80); ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.22)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(-176, -80); ctx.quadraticCurveTo(-170, 0, -182, 80); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,0.045)'; ctx.lineWidth = 1.2; ctx.setLineDash([5, 6]);
    for (let x = -200; x < 370; x += 58) { ctx.beginPath(); ctx.moveTo(x, blanketTop(x, br)); ctx.quadraticCurveTo(x + 8, 10, x + 2, 70); ctx.stroke(); }
    ctx.setLineDash([]);
    ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.lineWidth = 3;
    for (const fx of [-120, 40, 230]) { ctx.beginPath(); ctx.moveTo(fx, blanketTop(fx, br) + 8); ctx.quadraticCurveTo(fx + 20, 20, fx + 4, 66); ctx.stroke(); }
    // moonlight across the blanket
    lightPath(ctx, blanket, 140, -150, 360, [150, 175, 230], 0.18 * L.moon);
    lightPath(ctx, blanket, -470, -60, 560, [255, 160, 80], 0.22 * L.candle * L.flick);
    for (const fl of L.family || []) lightPath(ctx, blanket, fl.x, fl.y, 380, fl.c, 0.055 * fl.a);
    if (M.inner > 0) lightPath(ctx, blanket, -150, -60, 600, [255, 236, 210], 0.3 * M.inner);
    ctx.restore();
    ctx.strokeStyle = rgba(mix([150, 175, 230], [255, 200, 150], L.warm), 0.15); ctx.lineWidth = 1.5;
    ctx.beginPath(); for (let x = -216; x <= 352; x += 6) x === -216 ? ctx.moveTo(x, blanketTop(x, br)) : ctx.lineTo(x, blanketTop(x, br)); ctx.stroke();

    // ---- the arm on the blanket, with a hand that can rise to hold another
    const sh = [-196, -52 - br * 4];
    const rest = [-74, blanketTop(-74, br) - 6];
    const hd = M.hand || { w: 0 };
    const tx = lerp(rest[0], hd.x ?? rest[0], clamp(hd.w)), ty = lerp(rest[1], hd.y ?? rest[1], clamp(hd.w));
    const k = Draw.ik(sh[0], sh[1], tx, ty, 78, 72, -1);
    const sleeve = Draw.qpts(sh[0], sh[1], k.ex, k.ey + 4, k.hx, k.hy, 10);
    const slc = mix(mix([30, 34, 52], [120, 88, 78], clamp(L.warm * 0.7)), [255, 236, 210], M.inner * 0.3);
    const sg_ = ctx.createLinearGradient(0, k.ey - 16, 0, k.ey + 14);
    sg_.addColorStop(0, rgba(mix(slc, [255, 230, 200], 0.08), 1)); sg_.addColorStop(1, rgba(mix(slc, [0, 0, 0], 0.35), 1));
    ctx.fillStyle = sg_; Draw.taper(ctx, sleeve.slice(0, 9), 27, 19); ctx.fill();
    ctx.strokeStyle = rgba(mix([160, 185, 235], [255, 214, 170], clamp(L.warm)), 0.18); ctx.lineWidth = 1; ctx.stroke();
    // hand: an old, bony hand resting on the quilt; fingers can curl to hold another's
    const ang = Math.atan2(k.hy - k.ey, k.hx - k.ex) * (1 - clamp(hd.w)) * 0.3;
    const curl = clamp(M.curl || 0);
    const handRim = mix(mix([160, 185, 235], [255, 214, 170], clamp(L.warm)), [255, 244, 228], M.inner);
    const handC = mix(mix([34, 26, 26], [120, 84, 66], clamp(L.warm * 0.6 + L.candle * 0.1)), [255, 236, 214], M.inner * 0.35);
    ctx.save(); ctx.translate(k.hx - 6, k.hy + 1); ctx.rotate(ang); ctx.scale(1.45, 1.45);
    // fingers first (behind the back of the hand): long, lying forward on the quilt
    ctx.fillStyle = rgba(mix(handC, [0, 0, 0], 0.1), 1);
    for (let j = 3; j >= 0; j--) {
      const kx = 23.5 + j * 0.6, ky = -5.8 + j * 1.9;
      const b0 = 0.18 + j * 0.04 + curl * 0.7, b1 = 0.38 + curl * 1.0, b2 = 0.62 + curl * 1.3;
      const L0 = 8.5 - j * 0.6, L1 = 6.5 - j * 0.4, L2 = 5 - j * 0.3;
      const p1 = [kx + Math.cos(b0) * L0, ky + Math.sin(b0) * L0];
      const p2 = [p1[0] + Math.cos(b1) * L1, p1[1] + Math.sin(b1) * L1];
      const p3 = [p2[0] + Math.cos(b2) * L2, p2[1] + Math.sin(b2) * L2];
      Draw.taper(ctx, Draw.crPts([[kx - 2, ky], p1, p2, p3], 4), 4.3 - j * 0.35, 2.4 - j * 0.15); ctx.fill();
      ctx.strokeStyle = rgba(handRim, 0.12); ctx.lineWidth = 0.5; ctx.stroke();
    }
    // back of the hand with knuckle bumps
    const back = new Path2D();
    back.moveTo(-6, 6); back.lineTo(-6, -4.5);
    back.quadraticCurveTo(6, -8, 14, -7.4);
    for (let j = 0; j < 4; j++) { const kx = 17 + j * 2.4; back.quadraticCurveTo(kx + 1.2, -9.6 + j * 1.5, kx + 2.4, -7.4 + j * 1.6); }
    back.quadraticCurveTo(29, 0, 24, 5); back.quadraticCurveTo(10, 7.5, -6, 6); back.closePath();
    ctx.fillStyle = rgba(handC, 1); ctx.fill(back);
    // thumb along the near side
    ctx.fillStyle = rgba(mix(handC, [255, 220, 190], 0.05), 1);
    Draw.taper(ctx, Draw.crPts([[4, 3], [12, 6.5 - curl * 1.5], [19, 7 - curl * 3]], 4), 5.5, 3.2); ctx.fill();
    // rim light along the top edge, veins and tendons catching it
    ctx.save(); ctx.clip(back);
    ctx.globalCompositeOperation = 'lighter';
    const hg = ctx.createLinearGradient(0, -9, 0, 7);
    hg.addColorStop(0, rgba(handRim, 0.16 * clamp(0.3 * L.moon + 0.6 * clamp(L.warm) + 0.5 * M.inner))); hg.addColorStop(1, rgba(handRim, 0));
    ctx.fillStyle = hg; ctx.fillRect(-8, -10, 40, 18);
    ctx.strokeStyle = rgba(handRim, 0.32 * clamp(0.3 * L.moon + 0.6 * clamp(L.warm) + 0.5 * M.inner)); ctx.lineWidth = 1.2; ctx.stroke(back);
    ctx.strokeStyle = rgba(handRim, 0.14); ctx.lineWidth = 0.6;
    ctx.beginPath(); ctx.moveTo(-2, -2); ctx.bezierCurveTo(5, -4.5, 10, -1.5, 16, -4.8); ctx.moveTo(1, 1.5); ctx.bezierCurveTo(8, 0, 13, 2, 20, -1.5); ctx.stroke();
    ctx.restore();
    // shirt cuff
    ctx.fillStyle = rgba(slc, 1); ctx.beginPath(); ctx.ellipse(-8, 0.8, 4, 7.5, 0, 0, TAU); ctx.fill();
    ctx.restore();
    if (M.inner > 0) Draw.glow(ctx, k.hx, k.hy, 40, [255, 236, 210], 0.4 * M.inner);
    M._hand = [k.hx, k.hy];
    // anatomy anchors for other characters to reach
    M.anchors = {
      hair: [hx - 40, hy - 14], crown: [hx - 44, hy - 4], brow: [hx - 18, hy - 46], neck: [hx + 44, hy - 6], heart: [-150, blanketTop(-150, br) + 14], gut: [-60, blanketTop(-60, br) + 14],
      shoulder: [-206, blanketTop(-206, br) - 2], chest: [-150, blanketTop(-150, br)],
      arm: [(k.ex + k.hx) / 2, (k.ey + k.hy) / 2 - 4], hand: [k.hx, k.hy],
      knee: [150, blanketTop(150, br)], shin: [240, blanketTop(240, br)], feet: [314, blanketTop(314, br)],
    };
    return M.anchors;
  }


  // anatomy anchors without drawing (same geometry as man())
  function anchors(M) {
    const br = M.breath || 0, [hx, hy] = HEAD;
    const sh = [-196, -52 - br * 4];
    const rest = [-74, blanketTop(-74, br) - 6];
    const hd = M.hand || { w: 0 };
    const tx = lerp(rest[0], hd.x ?? rest[0], clamp(hd.w)), ty = lerp(rest[1], hd.y ?? rest[1], clamp(hd.w));
    const k = Draw.ik(sh[0], sh[1], tx, ty, 78, 72, -1);
    return {
      hair: [hx - 40, hy - 14], crown: [hx - 44, hy - 4], brow: [hx - 18, hy - 46], neck: [hx + 44, hy - 6], heart: [-150, blanketTop(-150, br) + 14], gut: [-60, blanketTop(-60, br) + 14],
      shoulder: [-206, blanketTop(-206, br) - 2], chest: [-150, blanketTop(-150, br)],
      arm: [(k.ex + k.hx) / 2, (k.ey + k.hy) / 2 - 4], hand: [k.hx, k.hy],
      knee: [150, blanketTop(150, br)], shin: [240, blanketTop(240, br)], feet: [314, blanketTop(314, br)],
    };
  }

  return { FLOOR, HEAD, WIN, room, roomLight, motes, candle, bed, man, anchors, blanketTop, smoothPath, lightPath };
})();
