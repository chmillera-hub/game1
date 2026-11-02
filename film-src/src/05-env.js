// ============================================================================
//  ENVIRONMENTS — garden of life, the sea and the ship, the curtain, the sky
// ============================================================================
const Env = (() => {
  // --------------------------------------------------------------- GARDEN
  // Plants are generated once; grow(g) 0..1 drives sprouting/blooming with per-plant delay.
  const GR = rng(2024);
  const PLANTS = [];
  function makePlants(hues) {
    PLANTS.length = 0;
    const N = 120;
    for (let i = 0; i < N; i++) {
      const zone = GR();
      let x, y, h, lean;
      if (zone < 0.66) { x = lerp(-900, 900, GR()); y = 190 + GR() * 26; h = 38 + GR() * 110; lean = (GR() - 0.5) * 0.6; }       // floor
      else if (zone < 0.88) { const side = GR() < 0.5 ? -366 : 378; x = side + (GR() - 0.5) * 18; y = 120 + GR() * 60; h = 140 + GR() * 220; lean = (GR() - 0.5) * 0.3; } // up the bedposts
      else { x = lerp(-240, 360, GR()); y = 66 + GR() * 6; h = 30 + GR() * 70; lean = (GR() - 0.5) * 0.9; }                   // along the quilt hem
      PLANTS.push({
        x, y, h, lean, d: GR() * 0.55, c: hues[(GR() * hues.length) | 0],
        petals: 5 + ((GR() * 4) | 0), size: 7 + GR() * 13, kind: GR() < 0.25 ? 'bell' : GR() < 0.6 ? 'cup' : 'star',
        sway: GR() * 10, leaves: 1 + ((GR() * 3) | 0), z: GR(),
      });
    }
    PLANTS.sort((a, b) => a.z - b.z);
  }
  function garden(ctx, g, t, light = 1, fade = null) {
    if (g <= 0.001) return;
    ctx.save();
    for (const p of PLANTS) {
      const fk = fade ? fade(p.x, p.y - p.h) : 1;
      if (fk <= 0.02) continue;
      ctx.globalAlpha = fk;
      const k = clamp((g - p.d) / 0.45);
      if (k <= 0) continue;
      const grow = Ease.out(clamp(k / 0.7)), bloom = Ease.back(clamp((k - 0.6) / 0.4));
      const sw = Math.sin(t * 0.8 + p.sway) * 0.05 + Noise.n1(t * 0.3 + p.sway) * 0.06;
      const ang = p.lean + sw;
      const L = p.h * grow;
      const tipX = p.x + Math.sin(ang) * L, tipY = p.y - Math.cos(ang) * L;
      const cx = p.x + Math.sin(ang * 0.4) * L * 0.5, cy = p.y - L * 0.55;
      // stem
      ctx.strokeStyle = rgba(mix([30, 60, 40], [90, 140, 90], light * 0.6), 0.85);
      ctx.lineWidth = 1.2 + p.size * 0.08; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.quadraticCurveTo(cx, cy, tipX, tipY); ctx.stroke();
      // leaves
      for (let j = 0; j < p.leaves; j++) {
        const u = 0.3 + j * 0.22; if (u * grow > grow) continue;
        const lx = lerp(p.x, tipX, u), ly = lerp(p.y, tipY, u), side = j % 2 ? 1 : -1;
        const ls = p.size * 0.9 * clamp(grow * 1.5 - u);
        ctx.fillStyle = rgba(mix([34, 70, 46], [110, 170, 100], light * 0.6), 0.85);
        ctx.save(); ctx.translate(lx, ly); ctx.rotate(ang + side * 0.9);
        ctx.beginPath(); ctx.ellipse(0, -ls * 0.6, ls * 0.28, ls * 0.65, 0, 0, TAU); ctx.fill(); ctx.restore();
      }
      if (bloom <= 0.01) continue;
      // blossom
      const s = p.size * bloom, c = p.c;
      ctx.save(); ctx.translate(tipX, tipY); ctx.rotate(ang);
      Draw.glow(ctx, 0, 0, s * 4, c, 0.22 * light * clamp(bloom));
      ctx.globalCompositeOperation = 'lighter';
      if (p.kind === 'bell') {
        ctx.fillStyle = rgba(mix(c, [255, 255, 255], 0.2), 0.4 * light);
        ctx.beginPath(); ctx.moveTo(-s * 0.6, 0); ctx.quadraticCurveTo(-s * 0.7, -s * 1.3, 0, -s * 1.3); ctx.quadraticCurveTo(s * 0.7, -s * 1.3, s * 0.6, 0);
        ctx.quadraticCurveTo(0, -s * 0.3, -s * 0.6, 0); ctx.fill();
      } else {
        const open = p.kind === 'cup' ? 0.55 : 1;
        for (let j = 0; j < p.petals; j++) {
          const a = (j / p.petals) * TAU * open - (open < 1 ? Math.PI * 0.5 * open + Math.PI / 2 : 0) + t * 0.05;
          ctx.save(); ctx.rotate(a);
          ctx.fillStyle = rgba(mix(c, [255, 255, 255], 0.15), 0.3 * light);
          ctx.beginPath(); ctx.ellipse(0, -s * 0.62, s * 0.3, s * 0.62, 0, 0, TAU); ctx.fill();
          ctx.restore();
        }
      }
      ctx.restore();
      Draw.glow(ctx, tipX, tipY, s * 0.9, [255, 245, 220], 0.55 * light * clamp(bloom), 1);
    }
    ctx.globalAlpha = 1;
    ctx.restore();
  }

  // floating petals / fireflies
  const FLY = Array.from({ length: 60 }, (_, i) => ({ p: i * 7.13, s: 0.4 + (i % 7) / 7, c: i % 6 }));
  function fireflies(ctx, amt, t, hues, box) {
    if (amt <= 0.01) return;
    for (const f of FLY) {
      const x = box.x0 + ((Noise.n2(f.p, t * 0.03 * f.s) * 0.5 + 0.5) * 1.3 - 0.15) * (box.x1 - box.x0);
      const y = box.y0 + ((Noise.n2(f.p + 40, t * 0.025 * f.s) * 0.5 + 0.5) * 1.3 - 0.15) * (box.y1 - box.y0);
      const tw = 0.5 + 0.5 * Math.sin(t * (1 + f.s) + f.p);
      Draw.glow(ctx, x, y, 5 + f.s * 6, hues[f.c % hues.length], amt * (0.3 + 0.7 * tw), 1);
    }
  }

  // --------------------------------------------------------------- SEA + SHIP (screen space)
  // o: { t, W, H, storm (0..1), dawn (0..1), boat:{x, scale}, family:[{c,a}], man:{a}, carry (0..1) }
  function waveY(x, t, layer, storm, W) {
    const A = (8 + storm * 30) * (1 + layer * 0.6), f = 0.006 / (1 + layer * 0.25) * (900 / Math.max(500, W));
    return Math.sin(x * f + t * (0.6 + layer * 0.15)) * A
      + Math.sin(x * f * 2.3 - t * (0.9 + layer * 0.1) + layer) * A * 0.35
      + Noise.n2(x * f * 0.8, t * 0.2 + layer * 3) * A * (0.8 + storm);
  }
  function sea(ctx, o) {
    const { W, H, t } = o, storm = o.storm || 0, dawn = o.dawn || 0;
    const hz = H * (W > H ? 0.52 : 0.5);
    // sky
    const sky = ctx.createLinearGradient(0, 0, 0, hz);
    sky.addColorStop(0, rgba(mix(mix([8, 12, 30], [3, 4, 9], storm), [60, 70, 120], dawn * 0.6), 1));
    sky.addColorStop(1, rgba(mix(mix([30, 42, 80], [12, 14, 22], storm), [250, 170, 120], dawn * 0.8), 1));
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, hz + 2);
    // stars & moon (fade under storm)
    const R = rng(7);
    for (let i = 0; i < 120; i++) {
      const x = R() * W, y = R() * hz * 0.9, tw = 0.5 + 0.5 * Math.sin(t * (0.5 + R() * 2) + i);
      Draw.glow(ctx, x, y, 2 + R() * 2.5, [220, 230, 255], (0.25 + 0.6 * tw) * (1 - storm) * (1 - dawn * 0.8), 1);
    }
    const mx = W * 0.68, my = hz * 0.3, mr = Math.min(W, H) * 0.045;
    Draw.glow(ctx, mx, my, mr * 8, [170, 195, 240], 0.4 * (1 - storm * 0.9));
    ctx.fillStyle = rgba([236, 240, 250], 0.95 * (1 - storm * 0.85)); ctx.beginPath(); ctx.arc(mx, my, mr, 0, TAU); ctx.fill();
    // storm clouds
    if (storm > 0.01) {
      for (let i = 0; i < 9; i++) {
        const cx = ((i / 9) * W * 1.4 + t * 18 * (1 + i % 3)) % (W * 1.4) - W * 0.2, cy = hz * (0.15 + (i % 4) * 0.12);
        ctx.fillStyle = `rgba(6,7,12,${0.55 * storm})`;
        ctx.beginPath(); ctx.ellipse(cx, cy, W * 0.22, hz * 0.12, 0, 0, TAU); ctx.fill();
      }
      // lightning flicker
      const fl = Math.max(0, Noise.n1(t * 2.2) - 0.55) * 2.2 * storm;
      if (fl > 0) { ctx.fillStyle = `rgba(200,210,255,${0.25 * fl})`; ctx.fillRect(0, 0, W, hz); }
    }
    // moon path on water
    const sea0 = ctx.createLinearGradient(0, hz, 0, H);
    sea0.addColorStop(0, rgba(mix(mix([20, 30, 60], [8, 10, 16], storm), [140, 100, 100], dawn * 0.5), 1));
    sea0.addColorStop(1, rgba(mix([4, 6, 14], [20, 16, 24], dawn * 0.5), 1));
    ctx.fillStyle = sea0; ctx.fillRect(0, hz, W, H - hz);
    for (let i = 0; i < 80; i++) {
      const yy = hz + Math.pow(i / 80, 1.6) * (H - hz);
      const w = (6 + (i / 80) * 70) * (0.5 + 0.5 * Math.abs(Noise.n2(i, t * 0.8)));
      ctx.fillStyle = rgba([200, 215, 250], (0.25 - i / 80 * 0.15) * (1 - storm * 0.9));
      ctx.fillRect(mx - w / 2 + Noise.n2(i * 3, t) * 14, yy, w, 1.6 + i / 40);
    }
    // waves: back to front layers; boat sits between layer 1 and 2
    const layers = 4;
    let boatState = null;
    for (let l = 0; l < layers; l++) {
      const base = hz + (H - hz) * (0.08 + l * 0.22);
      if (l === 2 && o.boat) boatState = boat(ctx, o, base - (H - hz) * 0.1, t);
      ctx.beginPath(); ctx.moveTo(0, H);
      for (let x = 0; x <= W + 8; x += 8) ctx.lineTo(x, base + waveY(x, t, l, storm, W) * (H / 900));
      ctx.lineTo(W, H); ctx.closePath();
      const g = ctx.createLinearGradient(0, base - 30, 0, H);
      const c0 = mix(mix([24, 36, 70], [12, 14, 22], storm), [120, 90, 100], dawn * 0.4);
      g.addColorStop(0, rgba(mix(c0, [0, 0, 0], l * 0.15), 0.96)); g.addColorStop(1, rgba([3, 4, 9], 1));
      ctx.fillStyle = g; ctx.fill();
      // crest highlights
      ctx.strokeStyle = rgba(mix([160, 190, 240], [255, 200, 170], dawn), 0.12 + 0.1 * storm);
      ctx.lineWidth = 1.2; ctx.beginPath();
      for (let x = 0; x <= W + 8; x += 8) { const y = base + waveY(x, t, l, storm, W) * (H / 900); x ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
      ctx.stroke();
    }
    // rain
    if (storm > 0.05) {
      ctx.strokeStyle = `rgba(170,185,220,${0.18 * storm})`; ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i < 160 * storm; i++) { const x = ((i * 97.3 + t * 900) % (W + 200)) - 100, y = ((i * 57.1 + t * 1300) % (H + 100)) - 50; ctx.moveTo(x, y); ctx.lineTo(x - 10, y + 26); }
      ctx.stroke();
    }
    return boatState;
  }

  // the boat: a small wooden hull carrying the man and his family of light
  function boat(ctx, o, baseY, t) {
    const { W, H } = o, storm = o.storm || 0;
    const sc = (o.boat.scale || 1) * Math.min(W, H) / 900;
    const bx = o.boat.x * W;
    const y0 = baseY + waveY(bx, t, 1.5, storm, W) * (H / 900);
    const slope = (waveY(bx + 20, t, 1.5, storm, W) - waveY(bx - 20, t, 1.5, storm, W)) / 40 * (H / 900);
    const ang = clamp(Math.atan(slope) * 0.9, -0.2, 0.2);
    ctx.save(); ctx.translate(bx, y0); ctx.rotate(ang); ctx.scale(sc, sc);
    // light the family carries
    const fam = o.family || [];
    fam.forEach((f, i) => Draw.glow(ctx, -90 + i * 36, -70, 140, f.c, 0.22 * f.a));
    // mast + sail
    ctx.strokeStyle = 'rgb(18,14,14)'; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(20, -10); ctx.lineTo(20, -250); ctx.stroke();
    const billow = 0.5 + 0.5 * Math.sin(t * 0.7) * (1 - storm * 0.5);
    ctx.beginPath(); ctx.moveTo(24, -240); ctx.quadraticCurveTo(100 + billow * 30, -150, 26, -40); ctx.closePath();
    ctx.fillStyle = rgba(mix([60, 66, 90], [230, 200, 170], (o.dawn || 0) * 0.6 + 0.2), 0.95); ctx.fill();
    ctx.beginPath(); ctx.moveTo(16, -230); ctx.quadraticCurveTo(-60 - billow * 20, -140, 14, -50); ctx.closePath();
    ctx.fillStyle = rgba(mix([50, 56, 80], [210, 180, 150], (o.dawn || 0) * 0.6 + 0.2), 0.9); ctx.fill();
    // passengers: family figures (small) and the man at the tiller
    const figs = [];
    const hud = o.huddle || 0, car = o.carry || 0;
    fam.forEach((f, i) => {
      if (f.small && car > 0.5) return;           // the smallest light is in his arms
      let fx = -120 + i * 42 + (i > 2 ? 30 : 0), fy = 10;
      fx = lerp(fx, -150 + i * 14, hud * 0.6);
      const ff = { x: fx, y: fy, h: 120 + (f.small ? -30 : 0), c: f.c, a: f.a * (1 - car * 0.55), t, seed: i + 20, lean: Math.sin(t * 0.8 + i) * 0.06 - ang * 0.5 - hud * 0.35, tilt: -hud * 0.3, hair: f.hair, face: -1, eyes: f.eyes ?? 0.4,
        hands: hud > 0.05 ? [{ x: -170, y: -60, w: hud }, { x: -160, y: -40, w: hud }] : f.hands };
      Draw.figureBody(ctx, ff); figs.push(ff);
    });
    // the six hold the boat up from beneath: a pair of cupped hands made of their light
    if (car > 0.01) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      fam.forEach((f, i) => { Draw.glow(ctx, -190 + i * 76, 70 + Math.sin(t * 1.5 + i) * 6, 110, f.c, 0.42 * car); Draw.glow(ctx, -190 + i * 76, 70 + Math.sin(t * 1.5 + i) * 6, 16, [255, 248, 230], 0.8 * car, 1); });
      // two cupped hands of light cradling the hull
      for (const side of [-1, 1]) {
        const hand = new Path2D();
        hand.moveTo(side * 270, -30); hand.quadraticCurveTo(side * 300, 110, side * 10, 118); hand.lineTo(side * 10, 88); hand.quadraticCurveTo(side * 250, 84, side * 236, -24); hand.closePath();
        const hg = ctx.createLinearGradient(0, -30, 0, 120);
        hg.addColorStop(0, rgba([255, 230, 190], 0)); hg.addColorStop(0.5, rgba([255, 230, 190], 0.16 * car)); hg.addColorStop(1, rgba([255, 240, 215], 0.3 * car));
        ctx.fillStyle = hg; ctx.fill(hand);
        for (let q = 0; q < 4; q++) { ctx.fillStyle = rgba([255, 236, 200], 0.14 * car); ctx.beginPath(); ctx.ellipse(side * (262 - q * 2), -40 - q * 16, 9, 20, side * 0.2, 0, TAU); ctx.fill(); }
      }
      ctx.restore();
    }
    if (o.man && o.man.a > 0.01) {
      // the man, sitting at the stern, silhouette with a warm rim
      ctx.save(); ctx.translate(-170, -6); ctx.globalAlpha = o.man.a;
      ctx.fillStyle = 'rgb(10,9,12)';
      ctx.beginPath(); ctx.ellipse(0, -66, 13, 15, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-18, -48); ctx.quadraticCurveTo(-24, -10, -16, 6); ctx.lineTo(22, 6); ctx.quadraticCurveTo(26, -30, 16, -48); ctx.quadraticCurveTo(0, -56, -18, -48); ctx.fill();
      ctx.strokeStyle = rgba([255, 214, 170], 0.5); ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(0, -66, 13.5, -1.2, 1.0); ctx.stroke();
      // arm on the tiller, or both arms around the smallest light
      ctx.strokeStyle = 'rgb(10,9,12)'; ctx.lineWidth = 8; ctx.lineCap = 'round';
      if (car > 0.5) {
        const sm = fam.find(f => f.small);
        Draw.glow(ctx, 26, -40, 46, sm ? sm.c : [255, 240, 200], 0.7 * car);
        Draw.glow(ctx, 26, -40, 12, [255, 250, 235], 0.95 * car, 1);
        ctx.beginPath(); ctx.moveTo(10, -44); ctx.quadraticCurveTo(40, -48, 38, -26); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(-8, -40); ctx.quadraticCurveTo(30, -12, 44, -34); ctx.stroke();
      } else { ctx.beginPath(); ctx.moveTo(10, -40); ctx.lineTo(34, -20); ctx.lineTo(-30, -2); ctx.stroke(); }
      ctx.restore();
    }
    // hull
    const hull = new Path2D();
    hull.moveTo(-230, -22); hull.quadraticCurveTo(-210, 34, -120, 40); hull.lineTo(150, 40);
    hull.quadraticCurveTo(220, 30, 250, -34); hull.lineTo(-230, -22); hull.closePath();
    const hg = ctx.createLinearGradient(0, -30, 0, 40);
    hg.addColorStop(0, 'rgb(46,30,24)'); hg.addColorStop(1, 'rgb(14,10,10)');
    ctx.fillStyle = hg; ctx.fill(hull);
    ctx.strokeStyle = 'rgba(255,220,180,0.18)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(-228, -20); ctx.lineTo(248, -32); ctx.stroke();
    ctx.strokeStyle = 'rgba(0,0,0,0.4)';
    for (let k = 1; k < 3; k++) { ctx.beginPath(); ctx.moveTo(-220 + k * 8, -20 + k * 18); ctx.quadraticCurveTo(0, -12 + k * 18, 240 - k * 14, -30 + k * 20); ctx.stroke(); }
    // lantern at the prow
    Draw.glow(ctx, 236, -60, 60, [255, 190, 110], 0.6);
    Draw.glow(ctx, 236, -60, 10, [255, 240, 210], 0.9, 1);
    ctx.strokeStyle = 'rgb(18,14,14)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(236, -34); ctx.lineTo(236, -52); ctx.stroke();
    // arms over the gunwale (carrying / being carried)
    figs.forEach(f => Draw.figureArms(ctx, f));
    ctx.restore();
    return { x: bx, y: y0, ang, sc };
  }

  // --------------------------------------------------------------- CURTAIN (screen space)
  // p: 0 open .. 1 closed. Warm stage light from the centre gap.
  function curtain(ctx, p, W, H, t, glowAmt = 1) {
    if (p <= 0.001) return;
    const half = W / 2, cover = half * Ease.inOut(clamp(p)) * 1.04;
    const velvet = [86, 14, 24];
    for (const side of [-1, 1]) {
      const x0 = side < 0 ? 0 : W - cover, x1 = side < 0 ? cover : W;
      ctx.save();
      const path = new Path2D();
      const edgeX = side < 0 ? x1 : x0;
      path.moveTo(side < 0 ? 0 : W, -10);
      path.lineTo(edgeX, -10);
      // edge sways slightly and gathers at the bottom
      for (let y = 0; y <= H + 20; y += 20) path.lineTo(edgeX + side * (Math.sin(y * 0.01 + t * 0.6) * 6 + (y / H) * 12) * (1 - p * 0.4), y);
      path.lineTo(side < 0 ? 0 : W, H + 20); path.closePath();
      ctx.clip(path);
      // folds: alternating light/dark vertical bands, compressed toward the outer edge
      const folds = 9;
      for (let i = 0; i < folds; i++) {
        const u0 = i / folds, u1 = (i + 1) / folds;
        const fx0 = side < 0 ? lerp(0, cover, Math.pow(u0, 0.8)) : lerp(W, W - cover, Math.pow(u0, 0.8));
        const fx1 = side < 0 ? lerp(0, cover, Math.pow(u1, 0.8)) : lerp(W, W - cover, Math.pow(u1, 0.8));
        const a = Math.min(fx0, fx1), b = Math.max(fx0, fx1);
        const g = ctx.createLinearGradient(a, 0, b, 0);
        const lit = 0.35 + 0.65 * (1 - u0) * 0 + 0.65 * u0; // brighter toward the gap
        g.addColorStop(0, rgba(mix(velvet, [0, 0, 0], 0.6), 1));
        g.addColorStop(0.45, rgba(mix(velvet, [255, 150, 110], 0.18 * lit), 1));
        g.addColorStop(1, rgba(mix(velvet, [0, 0, 0], 0.55), 1));
        ctx.fillStyle = g; ctx.fillRect(a, -10, b - a + 1, H + 30);
      }
      // warm spill near the gap
      const gx = side < 0 ? cover : W - cover;
      const sg = ctx.createLinearGradient(gx - side * 160, 0, gx, 0);
      sg.addColorStop(0, 'rgba(255,170,110,0)'); sg.addColorStop(1, rgba([255, 180, 120], 0.22 * glowAmt));
      ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = sg; ctx.fillRect(Math.min(gx, gx - side * 160), 0, 160, H);
      ctx.restore();
    }
    // valance across the top
    const vh = H * 0.09;
    const vg = ctx.createLinearGradient(0, 0, 0, vh);
    vg.addColorStop(0, rgba([40, 6, 12], 1)); vg.addColorStop(1, rgba([96, 18, 28], 1));
    ctx.fillStyle = vg;
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(W, 0); ctx.lineTo(W, vh * 0.7);
    const sw = W / 8;
    for (let i = 8; i >= 0; i--) ctx.quadraticCurveTo(i * sw + sw / 2, vh * 1.25, i * sw, vh * 0.7);
    ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(230,180,90,0.35)'; ctx.lineWidth = 2;
    ctx.beginPath(); for (let i = 0; i <= 8; i++) { const x = i * sw; i ? ctx.quadraticCurveTo(x - sw / 2, vh * 1.25, x, vh * 0.7) : ctx.moveTo(x, vh * 0.7); } ctx.stroke();
  }

  // --------------------------------------------------------------- SKY OF STARS (screen space)
  const SKY = Array.from({ length: 260 }, (_, i) => { const R = rng(500 + i); return { x: R(), y: R(), s: R(), p: R() * TAU }; });
  function starfield(ctx, a, W, H, t, drift = 0) {
    if (a <= 0.001) return;
    const bg = ctx.createRadialGradient(W * 0.5, H * 0.45, 0, W * 0.5, H * 0.5, Math.max(W, H) * 0.8);
    bg.addColorStop(0, rgba([22, 22, 48], a)); bg.addColorStop(1, rgba([3, 3, 9], a));
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    for (const s of SKY) {
      const tw = 0.5 + 0.5 * Math.sin(t * (0.4 + s.s * 1.6) + s.p);
      const x = ((s.x + drift * (0.2 + s.s) * 0.02) % 1) * W, y = s.y * H;
      Draw.glow(ctx, x, y, 1.5 + s.s * 3.5, [225, 230, 255], a * (0.2 + 0.7 * tw) * (0.4 + s.s * 0.6), 1);
    }
    // faint nebula drift in the family's colours
    const neb = [[243, 182, 109], [111, 211, 196], [185, 162, 255]];
    neb.forEach((c, i) => Draw.glow(ctx, W * (0.3 + i * 0.22) + Noise.n1(t * 0.03 + i) * W * 0.05, H * (0.35 + (i % 2) * 0.15), Math.max(W, H) * 0.35, c, 0.06 * a));
  }

  return { makePlants, garden, fireflies, sea, curtain, starfield, waveY };
})();

// ============================================================================
//  SIL — shadow-puppet people for projected memories. Pose-driven skeleton,
//  drawn as solid silhouettes (source-over) so a whole scene can be composited
//  onto the wall as light, without bright overlaps at the joints.
//  pose angles are radians from hanging straight down; + swings toward `dir`.
// ============================================================================
const Sil = (() => {
  const POSES = {
    stand: { lean: 0, head: 0, ua: [0.08, -0.08], fa: [0.05, -0.05], th: [0.04, -0.04], sh: [0, 0] },
    shield: { lean: 0.12, head: -0.05, ua: [1.7, 1.25], fa: [0.15, 0.35], th: [0.3, -0.25], sh: [0, -0.15] },
    sit: { lean: -0.08, head: 0.08, ua: [0.5, 0.3], fa: [1.4, 1.2], th: [1.5, 1.45], sh: [-0.05, 0] },
    lean: { lean: 0.35, head: 0.25, ua: [0.9, 0.7], fa: [1.4, 1.2], th: [0.05, -0.1], sh: [0, 0] },
    bow: { lean: 0.42, head: 0.35, ua: [0.25, 0.2], fa: [0.2, 0.15], th: [0, 0], sh: [0, 0] },
    cane: { lean: 0.32, head: 0.15, ua: [0.55, -0.05], fa: [0.15, 0.05], th: [0.12, -0.08], sh: [0, 0.05] },
    reach: { lean: 0.15, head: 0.05, ua: [1.2, 0.2], fa: [1.3, 0.1], th: [0.1, -0.1], sh: [0, 0] },
    hold: { lean: 0.05, head: 0.3, ua: [0.55, 0.5], fa: [1.7, 1.6], th: [0.04, -0.04], sh: [0, 0] },
    lie: { lean: 0, head: 0, ua: [0.1, 0.05], fa: [1.6, 0.05], th: [0, 0], sh: [0, 0] },
  };
  function walkPose(ph, run = 0) {
    const a = 0.42 + run * 0.3, s = Math.sin(ph);
    return { lean: 0.06 + run * 0.15, head: 0, ua: [s * a * 0.9, -s * a * 0.9], fa: [Math.max(0, s) * 0.5 + 0.2 + run * 0.6, Math.max(0, -s) * 0.5 + 0.2 + run * 0.6],
      th: [-s * a, s * a], sh: [-Math.max(0, Math.cos(ph)) * 0.9 * (0.5 + run), -Math.max(0, -Math.cos(ph)) * 0.9 * (0.5 + run)], bob: Math.abs(Math.cos(ph)) * 0.02 };
  }
  function mixPose(a, b, k) {
    const o = {};
    for (const key of ['lean', 'head', 'bob']) o[key] = lerp(a[key] || 0, b[key] || 0, k);
    for (const key of ['ua', 'fa', 'th', 'sh']) o[key] = [lerp(a[key][0], b[key][0], k), lerp(a[key][1], b[key][1], k)];
    return o;
  }
  // person: feet at (x,y), height h, facing dir (+1 right). child=true gives a child's proportions.
  // returns joint positions (hands, head) so props can attach.
  function person(ctx, x, y, h, pose, dir = 1, o = {}) {
    const P = typeof pose === 'string' ? POSES[pose] : pose;
    const child = o.child ? 1 : 0;
    const legL = h * lerp(0.47, 0.4, child), torso = h * lerp(0.31, 0.3, child), hr = h * lerp(0.068, 0.1, child);
    const out = {};
    const pt = (x0, y0, ang, len) => [x0 + Math.sin(ang) * len * dir, y0 + Math.cos(ang) * len];
    const sitting = P.th[0] > 1.2;
    const hip = [x, y - (sitting ? legL * 0.52 : legL) - (P.bob || 0) * h];
    // legs
    for (let i = 0; i < 2; i++) {
      const knee = pt(hip[0], hip[1], P.th[i], legL * 0.52);
      const foot = pt(knee[0], knee[1], P.th[i] + P.sh[i] - (sitting ? 1.5 : 0), legL * 0.5);
      Draw.taper(ctx, Draw.crPts([hip, knee, foot], 5), h * 0.075, h * 0.034); ctx.fill();
      ctx.beginPath(); ctx.ellipse(foot[0] + dir * h * 0.025, foot[1], h * 0.04, h * 0.016, 0, 0, TAU); ctx.fill();
    }
    // torso
    const neck = [hip[0] + Math.sin(P.lean) * torso * dir, hip[1] - Math.cos(P.lean) * torso];
    const nx = Math.cos(P.lean) * dir, ny = Math.sin(P.lean) * dir;  // across-body direction
    const sw = h * 0.085, hw = h * 0.07;
    ctx.beginPath();
    ctx.moveTo(neck[0] - nx * sw * 0.4, neck[1] - ny * sw * 0.4);
    ctx.quadraticCurveTo(neck[0] - nx * sw * 1.1, neck[1] - ny * sw * 1.1 + h * 0.01, lerp(neck[0], hip[0], 0.45) - nx * hw * 0.9, lerp(neck[1], hip[1], 0.45));
    ctx.lineTo(hip[0] - nx * hw, hip[1] - ny * hw + h * 0.02);
    ctx.lineTo(hip[0] + nx * hw, hip[1] + ny * hw + h * 0.02);
    ctx.lineTo(lerp(neck[0], hip[0], 0.45) + nx * hw * 0.9, lerp(neck[1], hip[1], 0.45));
    ctx.quadraticCurveTo(neck[0] + nx * sw * 1.1, neck[1] + ny * sw * 1.1 + h * 0.01, neck[0] + nx * sw * 0.4, neck[1] + ny * sw * 0.4);
    ctx.closePath(); ctx.fill();
    if (o.skirt) { ctx.beginPath(); ctx.moveTo(hip[0] - h * 0.07, hip[1] - h * 0.03); ctx.lineTo(hip[0] + h * 0.07, hip[1] - h * 0.03); ctx.lineTo(hip[0] + h * 0.11, hip[1] + h * 0.2); ctx.lineTo(hip[0] - h * 0.11, hip[1] + h * 0.2); ctx.fill(); }
    // head
    const hd = [neck[0] + Math.sin(P.lean + P.head) * hr * 1.35 * dir, neck[1] - Math.cos(P.lean + P.head) * hr * 1.35];
    ctx.beginPath(); ctx.ellipse(hd[0], hd[1], hr * 0.88, hr, (P.lean + P.head) * dir, 0, TAU); ctx.fill();
    ctx.fillRect(neck[0] - h * 0.016, neck[1] - hr * 0.5, h * 0.032, hr * 0.7);
    if (o.hat) { ctx.beginPath(); ctx.ellipse(hd[0], hd[1] - hr * 0.7, hr * 1.5, hr * 0.25, 0, 0, TAU); ctx.fill(); ctx.fillRect(hd[0] - hr * 0.7, hd[1] - hr * 1.5, hr * 1.4, hr * 0.85); }
    if (o.hair === 'long') { ctx.beginPath(); ctx.ellipse(hd[0] - dir * hr * 0.4, hd[1] + hr * 0.6, hr * 0.6, hr * 1.2, 0, 0, TAU); ctx.fill(); }
    // arms
    const shoulder = [neck[0] + Math.sin(P.lean) * h * 0.012 * dir, neck[1] + h * 0.03];
    out.hands = [];
    for (let i = 0; i < 2; i++) {
      const s0 = [shoulder[0] + (i ? 1 : -1) * nx * h * 0.035, shoulder[1]];
      const el = pt(s0[0], s0[1], P.ua[i] + P.lean, h * 0.165);
      const hn = pt(el[0], el[1], P.ua[i] + P.fa[i] + P.lean, h * 0.15);
      Draw.taper(ctx, Draw.crPts([s0, el, hn], 5), h * 0.05, h * 0.026); ctx.fill();
      ctx.beginPath(); ctx.arc(hn[0], hn[1], h * 0.02, 0, TAU); ctx.fill();
      out.hands.push(hn);
    }
    out.head = hd; out.neck = neck; out.hip = hip;
    return out;
  }
  return { POSES, walkPose, mixPose, person };
})();
