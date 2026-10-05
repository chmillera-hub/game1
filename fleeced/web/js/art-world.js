/* FLEECED - world art: skies, terrain, farm set, city, weather, props. */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp, hash, noise, ellipse, circle, rrect, text, mix, rgba, applyCam, FONT_UI, FONT_TITLE } = F;
  const A = window.A;
  const C = A.C, OUT = A.OUT;

  A.PAL = {
    day: { skyTop: '#5fb3f2', skyBot: '#d4f0ff', far: '#9fd08f', mid: '#7cbf69', ground: '#6db45a', ground2: '#549a45', sun: '#fff4b8', cloud: '#ffffff', tint: '#000000', tk: 0, stars: 0 },
    morning: { skyTop: '#79bff0', skyBot: '#ffe6c2', far: '#a6cf94', mid: '#80bc6b', ground: '#70af59', ground2: '#5a9a48', sun: '#fff0b0', cloud: '#fff6ea', tint: '#ffcf9a', tk: 0.05, stars: 0 },
    golden: { skyTop: '#f0a560', skyBot: '#ffe0a0', far: '#c4b27a', mid: '#9fa95e', ground: '#90a553', ground2: '#7a9046', sun: '#fff1c1', cloud: '#ffe9cc', tint: '#ffb36b', tk: 0.1, stars: 0 },
    dusk: { skyTop: '#3a3170', skyBot: '#ff9a66', far: '#7a6a8c', mid: '#566e52', ground: '#4d6a40', ground2: '#3e5a34', sun: '#ffcb7a', cloud: '#f7b9a0', tint: '#4b2f60', tk: 0.3, stars: 0.2 },
    night: { skyTop: '#060d24', skyBot: '#1c2a52', far: '#1d2946', mid: '#16301f', ground: '#15301e', ground2: '#0f2417', sun: '#e9eefc', cloud: '#2a3658', tint: '#0b1534', tk: 0.55, stars: 1 },
    storm: { skyTop: '#1b2029', skyBot: '#3f4955', far: '#2f393e', mid: '#21352a', ground: '#1f3325', ground2: '#182a1e', sun: '#cfd8e6', cloud: '#3a434f', tint: '#151b24', tk: 0.5, stars: 0 },
    red: { skyTop: '#25060e', skyBot: '#d2502e', far: '#561920', mid: '#290c10', ground: '#1b090b', ground2: '#130608', sun: '#ffb070', cloud: '#7a2a24', tint: '#2a0710', tk: 0.5, stars: 0 },
    riot: { skyTop: '#3a0d14', skyBot: '#f07a3a', far: '#7a3a3a', mid: '#5a3a2a', ground: '#5d5a32', ground2: '#4a4628', sun: '#ffcf7a', cloud: '#c86a4a', tint: '#5a1a10', tk: 0.22, stars: 0 },
  };
  A.setTint = function (pal, extra = 0) {
    A.tint.color = pal.tint;
    A.tint.k = clamp(pal.tk + extra);
  };

  // ------------------------------------------------------------------ sky
  A.sky = function (ctx, pal) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, pal.skyTop);
    g.addColorStop(0.75, pal.skyBot);
    g.addColorStop(1, pal.skyBot);
    ctx.fillStyle = g;
    ctx.fillRect(-20, -20, W + 40, H + 40);
  };
  A.stars = function (ctx, t, alpha) {
    if (alpha <= 0) return;
    ctx.save();
    for (let i = 0; i < 140; i++) {
      const x = hash(i * 3.7) * W, y = hash(i * 5.3 + 1) * H * 0.62;
      const tw = 0.55 + 0.45 * Math.sin(t * (1 + hash(i) * 3) + i);
      ctx.globalAlpha = alpha * tw * (0.4 + 0.6 * hash(i * 9.1));
      ctx.fillStyle = '#fff';
      circle(ctx, x, y, 1 + hash(i * 2.2) * 2);
      ctx.fill();
    }
    ctx.restore();
  };
  A.sun = function (ctx, x, y, r, color, glow = 1) {
    const g = ctx.createRadialGradient(x, y, r * 0.5, x, y, r * 3.2);
    g.addColorStop(0, rgba(color, 0.55 * glow));
    g.addColorStop(1, rgba(color, 0));
    ctx.fillStyle = g;
    circle(ctx, x, y, r * 3.2);
    ctx.fill();
    ctx.fillStyle = color;
    circle(ctx, x, y, r);
    ctx.fill();
  };
  A.moon = function (ctx, x, y, r, alpha = 1) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    const g = ctx.createRadialGradient(x, y, r * 0.8, x, y, r * 3);
    g.addColorStop(0, 'rgba(220,230,255,0.25)');
    g.addColorStop(1, 'rgba(220,230,255,0)');
    ctx.fillStyle = g;
    circle(ctx, x, y, r * 3);
    ctx.fill();
    ctx.fillStyle = '#eef2ff';
    circle(ctx, x, y, r);
    ctx.fill();
    ctx.fillStyle = 'rgba(160,170,200,0.35)';
    circle(ctx, x - r * 0.3, y - r * 0.2, r * 0.18); ctx.fill();
    circle(ctx, x + r * 0.25, y + r * 0.3, r * 0.12); ctx.fill();
    ctx.restore();
  };
  function cloud(ctx, x, y, s, color, alpha) {
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = color;
    ctx.beginPath();
    for (const [cx, cy, r] of [[-70, 10, 42], [-25, -18, 56], [35, -8, 50], [80, 14, 36], [0, 18, 46]]) {
      ctx.moveTo(x + cx * s + r * s, y + cy * s);
      ctx.arc(x + cx * s, y + cy * s, r * s, 0, TAU);
    }
    ctx.fill();
    ctx.restore();
  }
  A.clouds = function (ctx, t, pal, cam, alpha = 0.9) {
    ctx.save();
    applyCam(ctx, cam, 0.12);
    for (let i = 0; i < 7; i++) {
      const span = 3200;
      const x = ((hash(i * 7.1) * span + t * (8 + hash(i) * 10)) % span) - 600;
      const y = 120 + hash(i * 3.3) * 260;
      cloud(ctx, x, y, 0.8 + hash(i * 1.7) * 0.8, pal.cloud, alpha * (0.6 + 0.4 * hash(i * 4.4)));
    }
    ctx.restore();
  };
  /** heavy storm clouds rolling in; k = coverage 0..1 */
  A.stormClouds = function (ctx, t, k, cam, light = 0) {
    if (k <= 0) return;
    ctx.save();
    applyCam(ctx, cam, 0.2);
    for (let row = 0; row < 3; row++) {
      for (let i = 0; i < 9; i++) {
        const x = -700 + i * 420 + noise(t * 0.2 + i + row * 10) * 60 + (1 - k) * (row % 2 ? -1 : 1) * 1600;
        const y = -60 + row * 150 + hash(i + row * 9) * 50 + (1 - k) * -200;
        const col = mix(row === 2 ? '#2a313c' : '#1c222b', '#c8d4ff', light * 0.6);
        cloud(ctx, x, y, 2.2 + hash(i * 2 + row) * 0.8, col, clamp(k * 1.4) * 0.97);
      }
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ terrain
  const farY = x => 610 - 38 * Math.sin(x * 0.0042 + 0.6) - 22 * Math.sin(x * 0.011 + 1.2) - 150 * Math.exp(-(((x - A.HILL_X) / 190) ** 2));
  const midY = x => 712 - 28 * Math.sin(x * 0.0061 + 2) - 16 * Math.sin(x * 0.017);
  A.HILL_X = 1260;
  A.hillTop = () => farY(A.HILL_X);

  A.farHills = function (ctx, pal, cam, o = {}) {
    ctx.save();
    applyCam(ctx, cam, 0.35);
    ctx.beginPath();
    ctx.moveTo(-1500, 1400);
    for (let x = -1500; x <= 3500; x += 16) ctx.lineTo(x, farY(x));
    ctx.lineTo(3500, 1400);
    ctx.closePath();
    ctx.fillStyle = pal.far;
    ctx.fill();
    if (o.cross > 0) {
      ctx.globalAlpha = clamp(o.cross);
      A.crossShape(ctx, A.HILL_X, farY(A.HILL_X) + 6, 0.32, o.crossSheep ? 1 : 0, mix(pal.far, '#000000', 0.55));
    }
    ctx.restore();
  };
  A.midHills = function (ctx, pal, cam) {
    ctx.save();
    applyCam(ctx, cam, 0.6);
    ctx.beginPath();
    ctx.moveTo(-1500, 1400);
    for (let x = -1500; x <= 3500; x += 16) ctx.lineTo(x, midY(x));
    ctx.lineTo(3500, 1400);
    ctx.closePath();
    ctx.fillStyle = pal.mid;
    ctx.fill();
    // distant trees
    for (let i = 0; i < 16; i++) {
      const x = -900 + i * 300 + hash(i * 3) * 120;
      const y = midY(x) + 6;
      ctx.fillStyle = mix(pal.mid, '#000000', 0.18);
      circle(ctx, x, y - 26, 26 + hash(i) * 10); ctx.fill();
      circle(ctx, x + 18, y - 14, 20); ctx.fill();
    }
    ctx.restore();
  };
  A.GROUND = 800;
  A.ground = function (ctx, pal, cam) {
    ctx.save();
    applyCam(ctx, cam, 1);
    const g = ctx.createLinearGradient(0, 770, 0, 1400);
    g.addColorStop(0, pal.ground);
    g.addColorStop(1, pal.ground2);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.moveTo(-2000, 790);
    for (let x = -2000; x <= 4000; x += 40) ctx.lineTo(x, 786 + 5 * Math.sin(x * 0.01));
    ctx.lineTo(4000, 2200);
    ctx.lineTo(-2000, 2200);
    ctx.closePath();
    ctx.fill();
    // grass tufts
    ctx.strokeStyle = mix(pal.ground, '#000000', 0.18);
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    for (let i = 0; i < 120; i++) {
      const x = -1200 + hash(i * 1.3) * 4200, y = 815 + hash(i * 2.9) * 380;
      ctx.beginPath();
      ctx.moveTo(x - 8, y); ctx.lineTo(x - 12, y - 14);
      ctx.moveTo(x, y); ctx.lineTo(x, y - 18);
      ctx.moveTo(x + 8, y); ctx.lineTo(x + 13, y - 13);
      ctx.stroke();
    }
    for (let i = 0; i < 40; i++) {
      const x = -1200 + hash(i * 7.7) * 4200, y = 830 + hash(i * 5.1) * 360;
      ctx.fillStyle = C(['#fff6d6', '#ffd1e0', '#fff27a'][i % 3]);
      circle(ctx, x, y, 5); ctx.fill();
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ farm set
  A.FARM = { barnX: 420, feederX: 1010, houseX: 1770, chairX: 1405, jarX: 1508, porch0: 1285, porch1: 1580 };

  A.tree = function (ctx, x, y, s = 1) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    rrect(ctx, -22, -190, 44, 194, 14); ctx.fillStyle = C(OUT); ctx.fill();
    rrect(ctx, -17, -190, 34, 190, 12); ctx.fillStyle = C('#7a5233'); ctx.fill();
    const pts = [[-70, -220, 70], [0, -280, 86], [72, -220, 70], [-30, -180, 60], [40, -170, 60]];
    ctx.fillStyle = C(OUT);
    for (const [cx, cy, r] of pts) { circle(ctx, cx, cy, r + 6); ctx.fill(); }
    ctx.fillStyle = C('#4f9a45');
    for (const [cx, cy, r] of pts) { circle(ctx, cx, cy, r); ctx.fill(); }
    ctx.fillStyle = C('#69b55a');
    for (const [cx, cy, r] of pts) { circle(ctx, cx - r * 0.25, cy - r * 0.3, r * 0.45); ctx.fill(); }
    ctx.restore();
  };

  A.barn = function (ctx, x, y, o = {}) {
    const door = o.door ?? 0;
    ctx.save();
    ctx.translate(x, y);
    const w = 420, h = 262;
    const red = C('#b8412f'), redDark = C('#8f2f23'), trim = C('#f4efe4'), outline = C(OUT);
    // roof
    ctx.beginPath();
    ctx.moveTo(-w / 2 - 26, -h);
    ctx.lineTo(-w / 2 + 34, -h - 96);
    ctx.lineTo(0, -h - 158);
    ctx.lineTo(w / 2 - 34, -h - 96);
    ctx.lineTo(w / 2 + 26, -h);
    ctx.closePath();
    ctx.fillStyle = C('#6e2620'); ctx.fill();
    ctx.lineWidth = 6; ctx.strokeStyle = outline; ctx.lineJoin = 'round'; ctx.stroke();
    // walls
    ctx.beginPath();
    ctx.rect(-w / 2, -h, w, h);
    ctx.moveTo(-w / 2 + 30, -h);
    ctx.lineTo(-w / 2 + 30 + 20, -h - 80);
    ctx.lineTo(0, -h - 132);
    ctx.lineTo(w / 2 - 50, -h - 80);
    ctx.lineTo(w / 2 - 30, -h);
    ctx.fillStyle = red; ctx.fill();
    ctx.save(); ctx.clip();
    ctx.strokeStyle = redDark; ctx.lineWidth = 4;
    for (let px = -w / 2 + 26; px < w / 2; px += 26) { ctx.beginPath(); ctx.moveTo(px, -h - 140); ctx.lineTo(px, 0); ctx.stroke(); }
    ctx.restore();
    ctx.strokeStyle = outline; ctx.lineWidth = 6; ctx.strokeRect(-w / 2, -h, w, h);
    // trim
    ctx.strokeStyle = trim; ctx.lineWidth = 9;
    ctx.strokeRect(-w / 2 + 8, -h + 8, w - 16, h - 12);
    // loft window
    rrect(ctx, -40, -h - 92, 80, 64, 6); ctx.fillStyle = C('#3a1c14'); ctx.fill(); ctx.strokeStyle = trim; ctx.lineWidth = 8; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-40, -h - 92); ctx.lineTo(40, -h - 28); ctx.moveTo(40, -h - 92); ctx.lineTo(-40, -h - 28); ctx.stroke();
    // doorway
    const dw = 190, dh = 205;
    ctx.fillStyle = C('#2a140e');
    ctx.fillRect(-dw / 2, -dh, dw, dh);
    if (o.inside) o.inside(ctx, dw, dh);
    // sliding doors
    for (const side of [-1, 1]) {
      const px = side < 0 ? -dw / 2 - door * 92 : door * 92;
      ctx.save();
      ctx.translate(px, -dh);
      ctx.fillStyle = red; ctx.fillRect(0, 0, dw / 2, dh);
      ctx.strokeStyle = trim; ctx.lineWidth = 8;
      ctx.strokeRect(5, 5, dw / 2 - 10, dh - 10);
      ctx.beginPath(); ctx.moveTo(5, 5); ctx.lineTo(dw / 2 - 5, dh - 5); ctx.moveTo(dw / 2 - 5, 5); ctx.lineTo(5, dh - 5); ctx.stroke();
      ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.strokeRect(0, 0, dw / 2, dh);
      ctx.restore();
    }
    ctx.fillStyle = C('#5b5b5b'); ctx.fillRect(-dw / 2 - 100, -dh - 14, dw + 200, 10);
    if (o.lock > 0) {
      const k = F.E.back(clamp(o.lock));
      ctx.save();
      ctx.translate(0, -dh * 0.5);
      ctx.scale(k, k);
      ctx.lineWidth = 9; ctx.strokeStyle = outline;
      ctx.beginPath(); ctx.arc(0, -18, 20, Math.PI, 0); ctx.stroke();
      ctx.lineWidth = 5; ctx.strokeStyle = C('#b9c2c9');
      ctx.beginPath(); ctx.arc(0, -18, 20, Math.PI, 0); ctx.stroke();
      rrect(ctx, -28, -20, 56, 46, 8); ctx.fillStyle = C('#f2b830'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
      circle(ctx, 0, 0, 6); ctx.fillStyle = outline; ctx.fill();
      ctx.restore();
    }
    ctx.restore();
  };

  A.fence = function (ctx, x0, x1, y) {
    const outline = C(OUT), wood = C('#c79a63'), woodDark = C('#9c7243');
    for (const ry of [y - 70, y - 36]) {
      rrect(ctx, x0, ry - 7, x1 - x0, 14, 5); ctx.fillStyle = outline; ctx.fill();
      rrect(ctx, x0 + 2, ry - 4, x1 - x0 - 4, 8, 4); ctx.fillStyle = wood; ctx.fill();
    }
    for (let x = x0; x <= x1; x += 90) {
      rrect(ctx, x - 9, y - 96, 18, 98, 4); ctx.fillStyle = outline; ctx.fill();
      rrect(ctx, x - 6, y - 93, 12, 93, 3); ctx.fillStyle = woodDark; ctx.fill();
    }
  };

  A.turnstile = function (ctx, x, y, o = {}) {
    const outline = C(OUT);
    ctx.save();
    ctx.translate(x, y);
    rrect(ctx, -14, -120, 28, 120, 6); ctx.fillStyle = C('#8a949c'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    // arms (rotating)
    const rot = o.rot || 0;
    for (let i = 0; i < 3; i++) {
      const a = rot + (i * TAU) / 3;
      const dx = Math.cos(a) * 70, dz = Math.sin(a);
      ctx.strokeStyle = outline; ctx.lineWidth = 12; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(0, -78); ctx.lineTo(dx, -78 + dz * 14); ctx.stroke();
      ctx.strokeStyle = C('#c9d1d8'); ctx.lineWidth = 7;
      ctx.beginPath(); ctx.moveTo(0, -78); ctx.lineTo(dx, -78 + dz * 14); ctx.stroke();
    }
    rrect(ctx, -34, -170, 68, 54, 8); ctx.fillStyle = C('#e0473a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    rrect(ctx, -14, -158, 28, 6, 3); ctx.fillStyle = '#1b1210'; ctx.fill();
    text(ctx, '1 TOKEN', 0, -133, { size: 14, weight: 700, fill: '#fff' });
    if (o.light) {
      circle(ctx, 0, -184, 11);
      ctx.fillStyle = o.light === 'green' ? '#4cff7a' : '#ff3030';
      ctx.shadowColor = ctx.fillStyle; ctx.shadowBlur = 20; ctx.fill(); ctx.shadowBlur = 0;
      ctx.strokeStyle = outline; ctx.lineWidth = 3; ctx.stroke();
    }
    ctx.restore();
  };

  A.feeder = function (ctx, x, y, o = {}) {
    const outline = C(OUT), wood = C('#b98a52'), dark = C('#8a6234');
    ctx.save();
    ctx.translate(x, y);
    for (const lx of [-90, 90]) { rrect(ctx, lx - 8, -60, 16, 60, 4); ctx.fillStyle = dark; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke(); }
    // hay
    const hk = o.hay ?? 0.4;
    ctx.fillStyle = C('#f2cf5b');
    for (let i = 0; i < 9; i++) { circle(ctx, -95 + i * 24, -96 - hk * 26 - (i % 2) * 8, 22); ctx.fill(); }
    ctx.beginPath(); ctx.moveTo(-120, -110); ctx.lineTo(120, -110); ctx.lineTo(100, -55); ctx.lineTo(-100, -55); ctx.closePath();
    ctx.fillStyle = wood; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    ctx.strokeStyle = dark; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(-112, -90); ctx.lineTo(112, -90); ctx.stroke();
    // coin box (or, once food is free, a FREE sign)
    rrect(ctx, -170, -150, 14, 150, 4); ctx.fillStyle = C('#8a949c'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    const free = o.free || 0;
    if (free < 0.5) {
      const k = 1 - free * 2;
      ctx.save(); ctx.translate(-163, -177); ctx.scale(k, k); ctx.translate(163, 177);
      rrect(ctx, -200, -215, 74, 76, 10); ctx.fillStyle = C('#e0473a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
      rrect(ctx, -176, -198, 26, 7, 3); ctx.fillStyle = '#1b1210'; ctx.fill();
      text(ctx, 'INSERT', -163, -172, { size: 15, weight: 700, fill: '#fff' });
      text(ctx, 'TOKEN', -163, -155, { size: 15, weight: 700, fill: '#fff' });
      ctx.restore();
    } else {
      const k = F.E.back(clamp((free - 0.5) * 2));
      ctx.save(); ctx.translate(-163, -185); ctx.scale(k, k);
      rrect(ctx, -52, -40, 104, 74, 12); ctx.fillStyle = C('#3fae5a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
      text(ctx, 'FREE', 0, -12, { size: 30, font: FONT_TITLE, weight: 400, fill: '#fff' });
      text(ctx, 'FOOD', 0, 18, { size: 17, weight: 700, fill: '#eaffef' });
      ctx.restore();
    }
    if (o.flash > 0) {
      ctx.save(); ctx.globalAlpha *= o.flash;
      circle(ctx, -163, -228, 10); ctx.fillStyle = '#4cff7a'; ctx.shadowColor = '#4cff7a'; ctx.shadowBlur = 20; ctx.fill();
      ctx.restore();
    }
    ctx.restore();
  };

  A.rocker = function (ctx, x, y, s = 1, front = false) {
    const outline = C(OUT), wood = C('#9a6a3a'), dark = C('#7a5028');
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.lineCap = 'round';
    if (!front) {
      for (const sx of [-1, 1]) {
        ctx.strokeStyle = outline; ctx.lineWidth = 16;
        ctx.beginPath(); ctx.moveTo(sx * 62, -96); ctx.lineTo(sx * 70, -330); ctx.stroke();
        ctx.strokeStyle = wood; ctx.lineWidth = 9;
        ctx.beginPath(); ctx.moveTo(sx * 62, -96); ctx.lineTo(sx * 70, -330); ctx.stroke();
      }
      for (const yy of [-320, -270, -220]) {
        rrect(ctx, -70, yy - 8, 140, 16, 6); ctx.fillStyle = outline; ctx.fill();
        rrect(ctx, -67, yy - 5, 134, 10, 5); ctx.fillStyle = dark; ctx.fill();
      }
      rrect(ctx, -80, -108, 160, 22, 8); ctx.fillStyle = outline; ctx.fill();
      rrect(ctx, -76, -104, 152, 14, 6); ctx.fillStyle = wood; ctx.fill();
    } else {
      for (const sx of [-1, 1]) {
        ctx.strokeStyle = outline; ctx.lineWidth = 14;
        ctx.beginPath(); ctx.moveTo(sx * 70, -90); ctx.lineTo(sx * 74, 0); ctx.moveTo(sx * 88, -160); ctx.lineTo(sx * 80, -96); ctx.stroke();
        ctx.strokeStyle = wood; ctx.lineWidth = 8;
        ctx.beginPath(); ctx.moveTo(sx * 70, -90); ctx.lineTo(sx * 74, 0); ctx.moveTo(sx * 88, -160); ctx.lineTo(sx * 80, -96); ctx.stroke();
        rrect(ctx, sx * 88 - 26, -170, 52, 14, 6); ctx.fillStyle = outline; ctx.fill();
        rrect(ctx, sx * 88 - 23, -167, 46, 8, 4); ctx.fillStyle = wood; ctx.fill();
      }
      ctx.strokeStyle = outline; ctx.lineWidth = 14;
      ctx.beginPath(); ctx.moveTo(-120, -4); ctx.quadraticCurveTo(0, 22, 120, -4); ctx.stroke();
      ctx.strokeStyle = dark; ctx.lineWidth = 8;
      ctx.beginPath(); ctx.moveTo(-120, -4); ctx.quadraticCurveTo(0, 22, 120, -4); ctx.stroke();
    }
    ctx.restore();
  };

  A.jarTable = function (ctx, x, y, o = {}) {
    const outline = C(OUT);
    ctx.save();
    ctx.translate(x, y);
    // table
    for (const lx of [-34, 34]) { rrect(ctx, lx - 6, -86, 12, 86, 3); ctx.fillStyle = C('#7a5028'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 3; ctx.stroke(); }
    rrect(ctx, -56, -98, 112, 16, 5); ctx.fillStyle = C('#9a6a3a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    if (o.jar !== false) {
      ctx.save();
      const tip = o.tip || 0;
      ctx.translate(36, -98);
      ctx.rotate(tip * 1.45);
      ctx.translate(-36, 0);
      const fill = o.fill ?? 1;
      rrect(ctx, -34, -112, 68, 112, 18); ctx.fillStyle = 'rgba(220,240,255,0.35)'; ctx.fill();
      ctx.save(); ctx.clip();
      for (let i = 0; i < 24; i++) {
        const cx = -26 + (i % 4) * 17 + ((i / 4) | 0) % 2 * 8, cy = -8 - ((i / 4) | 0) * 15;
        if (cy > -112 * fill) A.token(ctx, cx, cy, 9, 0.3);
      }
      ctx.restore();
      rrect(ctx, -34, -112, 68, 112, 18); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.5)'; ctx.fillRect(-24, -96, 7, 70);
      rrect(ctx, -30, -126, 60, 16, 5); ctx.fillStyle = C('#d65a3a'); ctx.fill(); ctx.strokeStyle = outline; ctx.stroke();
      text(ctx, 'TOKENS', 0, -60, { size: 13, weight: 700, fill: '#5a2a10' });
      ctx.restore();
    }
    ctx.restore();
  };

  A.house = function (ctx, x, y, o = {}) {
    const outline = C(OUT), wall = C('#f1e2c2'), wallDark = C('#d8c49e'), roof = C('#4d6a8c'), wood = C('#a87a48');
    const P0 = A.FARM.porch0 - x, P1 = A.FARM.porch1 - x;
    ctx.save();
    ctx.translate(x, y);
    const w = 400, h = 300;
    // chimney
    rrect(ctx, 90, -h - 170, 50, 120, 4); ctx.fillStyle = C('#a2483a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    // walls
    ctx.fillStyle = wall; ctx.fillRect(-w / 2, -h, w, h);
    ctx.strokeStyle = wallDark; ctx.lineWidth = 3;
    for (let yy = -h + 22; yy < 0; yy += 22) { ctx.beginPath(); ctx.moveTo(-w / 2, yy); ctx.lineTo(w / 2, yy); ctx.stroke(); }
    ctx.strokeStyle = outline; ctx.lineWidth = 6; ctx.strokeRect(-w / 2, -h, w, h);
    // roof
    ctx.beginPath(); ctx.moveTo(-w / 2 - 40, -h + 4); ctx.lineTo(0, -h - 150); ctx.lineTo(w / 2 + 40, -h + 4); ctx.closePath();
    ctx.fillStyle = roof; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 6; ctx.lineJoin = 'round'; ctx.stroke();
    // window (can be lit, with content)
    const wx = -95, wy = -230, ww = 120, wh = 104;
    ctx.fillStyle = o.lit ? C('#ffd27a') : C('#8fc3e6');
    ctx.fillRect(wx, wy, ww, wh);
    if (o.lit) {
      const g = ctx.createRadialGradient(wx + ww / 2, wy + wh / 2, 10, wx + ww / 2, wy + wh / 2, 200);
      g.addColorStop(0, 'rgba(255,200,110,0.35)'); g.addColorStop(1, 'rgba(255,200,110,0)');
      ctx.save(); ctx.fillStyle = g; ctx.fillRect(wx - 200, wy - 200, ww + 400, wh + 400); ctx.restore();
    }
    if (o.windowContent) { ctx.save(); ctx.beginPath(); ctx.rect(wx, wy, ww, wh); ctx.clip(); o.windowContent(ctx, wx, wy, ww, wh); ctx.restore(); }
    ctx.strokeStyle = C('#ffffff'); ctx.lineWidth = 8; ctx.strokeRect(wx, wy, ww, wh);
    ctx.beginPath(); ctx.moveTo(wx + ww / 2, wy); ctx.lineTo(wx + ww / 2, wy + wh); ctx.moveTo(wx, wy + wh / 2); ctx.lineTo(wx + ww, wy + wh / 2); ctx.stroke();
    ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.strokeRect(wx - 4, wy - 4, ww + 8, wh + 8);
    // door
    rrect(ctx, 60, -170, 80, 170, 6); ctx.fillStyle = C('#6b8f5a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    circle(ctx, 124, -86, 6); ctx.fillStyle = C('#f2c94c'); ctx.fill();
    // porch (left of house)
    ctx.fillStyle = wood;
    rrect(ctx, P0, -22, P1 - P0, 24, 4); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    for (const px of [P0 + 14, P1 - 6]) { rrect(ctx, px - 8, -300, 16, 280, 3); ctx.fillStyle = C('#e8dcc0'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(P0 - 30, -290); ctx.lineTo(P1, -330); ctx.lineTo(P1, -296); ctx.lineTo(P0 - 30, -270); ctx.closePath();
    ctx.fillStyle = roof; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    ctx.restore();
  };

  /** Full farm backdrop (sky -> ground -> set). o: {lit, door, lock, cross, hay, feederFlash, gateRot, gateLight, jar, jarTip, jarFill, chairBack(fn)} */
  A.farmSet = function (ctx, t, cam, pal, o = {}) {
    A.sky(ctx, pal);
    if (pal.stars) A.stars(ctx, t, pal.stars * (o.starK ?? 1));
    if (o.moon !== undefined) A.moon(ctx, o.moon[0], o.moon[1], 46, o.moon[2] ?? 1);
    else if (o.sun !== false) A.sun(ctx, o.sunX ?? 1500, o.sunY ?? 190, 64, pal.sun, 1);
    if (o.clouds !== false) A.clouds(ctx, t, pal, cam, o.cloudA ?? 0.9);
    A.farHills(ctx, pal, cam, { cross: o.cross, crossSheep: o.crossSheep });
    A.midHills(ctx, pal, cam);
    A.ground(ctx, pal, cam);
    ctx.save();
    applyCam(ctx, cam, 1);
    A.tree(ctx, -120, A.GROUND + 6, 1.1);
    A.tree(ctx, 2160, A.GROUND + 6, 1.2);
    A.fence(ctx, -320, 190, A.GROUND + 10);
    A.fence(ctx, 650, 820, A.GROUND + 10);
    A.barn(ctx, A.FARM.barnX, A.GROUND + 4, { door: o.door ?? 0.35, lock: o.lock || 0, inside: o.barnInside });
    const gate = o.gate ?? 1;
    if (gate > 0) {
      ctx.save();
      ctx.translate(A.FARM.barnX + 150, A.GROUND + 12);
      ctx.scale(gate, gate);
      A.turnstile(ctx, 0, 0, { rot: o.gateRot || 0, light: o.gateLight });
      ctx.restore();
    }
    if (gate < 1) {
      const k = F.E.back(clamp((1 - gate) * 1.4 - 0.25));
      ctx.save();
      ctx.translate(A.FARM.barnX + 150, A.GROUND + 12);
      ctx.scale(k, k);
      rrect(ctx, -7, -130, 14, 130, 4); ctx.fillStyle = C('#9c7243'); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 4; ctx.stroke();
      rrect(ctx, -62, -196, 124, 76, 12); ctx.fillStyle = C('#3fae5a'); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 4; ctx.stroke();
      text(ctx, 'FREE', 0, -168, { size: 30, font: FONT_TITLE, weight: 400, fill: '#fff' });
      text(ctx, 'SHELTER', 0, -138, { size: 17, weight: 700, fill: '#eaffef' });
      ctx.restore();
    }
    A.feeder(ctx, A.FARM.feederX, A.GROUND + 14, { hay: o.hay ?? 0.4, flash: o.feederFlash || 0, free: o.free || 0 });
    ctx.save();
    if (o.porchShake) ctx.translate(Math.sin(t * 90) * 6 * o.porchShake, Math.cos(t * 70) * 3 * o.porchShake);
    A.house(ctx, A.FARM.houseX, A.GROUND + 4, { lit: o.lit, windowContent: o.windowContent });
    if (o.chair !== false) {
      A.rocker(ctx, A.FARM.chairX, A.GROUND - 14, 1, false);
      A.rocker(ctx, A.FARM.chairX, A.GROUND - 14, 1, true);
    }
    if (o.jar !== false) A.jarTable(ctx, A.FARM.jarX, A.GROUND - 14, { tip: o.jarTip || 0, fill: o.jarFill ?? 1 });
    ctx.restore();
    ctx.restore();
  };

  // ------------------------------------------------------------------ props & fx
  A.hayPile = function (ctx, x, y, s = 1) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    const pts = [[-40, -14, 26], [-10, -26, 30], [24, -18, 28], [44, -8, 20], [0, -8, 30]];
    ctx.fillStyle = C(OUT);
    for (const [cx, cy, r] of pts) { circle(ctx, cx, cy, r + 4); ctx.fill(); }
    ctx.fillStyle = C('#f2cf5b');
    for (const [cx, cy, r] of pts) { circle(ctx, cx, cy, r); ctx.fill(); }
    ctx.strokeStyle = C('#c9a336'); ctx.lineWidth = 3;
    for (let i = 0; i < 8; i++) { ctx.beginPath(); ctx.moveTo(-40 + i * 11, -10); ctx.lineTo(-32 + i * 11, -34); ctx.stroke(); }
    ctx.restore();
  };

  A.hayBale = function (ctx, x, y, s = 1) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    rrect(ctx, -58, -70, 116, 70, 12); ctx.fillStyle = '#e9c45a'; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 5; ctx.stroke();
    ctx.strokeStyle = '#c99d36'; ctx.lineWidth = 3;
    for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.moveTo(-50 + i * 4, -60 + i * 10); ctx.lineTo(50 - i * 3, -62 + i * 10); ctx.stroke(); }
    ctx.strokeStyle = '#8a5a2a'; ctx.lineWidth = 6;
    for (const bx of [-26, 26]) { ctx.beginPath(); ctx.moveTo(bx, -70); ctx.lineTo(bx, 0); ctx.stroke(); }
    ctx.restore();
  };
  A.miniBarn = function (ctx, x, y, s = 1) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.beginPath(); ctx.moveTo(-40, -50); ctx.lineTo(0, -80); ctx.lineTo(40, -50); ctx.lineTo(40, 0); ctx.lineTo(-40, 0); ctx.closePath();
    ctx.fillStyle = '#b8412f'; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 4; ctx.lineJoin = 'round'; ctx.stroke();
    ctx.fillStyle = '#2a140e'; ctx.fillRect(-14, -32, 28, 32);
    ctx.restore();
  };
  A.miniHouse = function (ctx, x, y, s = 1) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.fillStyle = '#f1e2c2'; ctx.fillRect(-40, -50, 80, 50); ctx.strokeStyle = OUT; ctx.lineWidth = 4; ctx.strokeRect(-40, -50, 80, 50);
    ctx.beginPath(); ctx.moveTo(-50, -48); ctx.lineTo(0, -88); ctx.lineTo(50, -48); ctx.closePath(); ctx.fillStyle = '#4d6a8c'; ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#ffd27a'; ctx.fillRect(-26, -38, 20, 18);
    ctx.restore();
  };
  A.plate = function (ctx, x, y, s = 1) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ellipse(ctx, 0, 0, 46, 16); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 4; ctx.stroke();
    ctx.fillStyle = '#c96a3a'; ellipse(ctx, -8, -8, 16, 10); ctx.fill();
    ctx.fillStyle = '#6aa84f'; ellipse(ctx, 14, -6, 10, 7); ctx.fill();
    ctx.restore();
  };

  A.calendar = function (ctx, x, y, s, flip, alpha = 1) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.globalAlpha *= alpha;
    rrect(ctx, -80, -100, 160, 190, 12); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 5; ctx.stroke();
    rrect(ctx, -80, -100, 160, 50, [12, 12, 0, 0]); ctx.fillStyle = '#d64535'; ctx.fill(); ctx.stroke();
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG'];
    const i = Math.floor(flip) % months.length;
    text(ctx, months[i], 0, -74, { size: 30, weight: 700, fill: '#fff' });
    text(ctx, 'RENT', 0, -12, { size: 30, weight: 700, fill: '#2b1d16' });
    text(ctx, 'DUE', 0, 30, { size: 30, weight: 700, fill: '#d64535' });
    const f = flip - Math.floor(flip);
    if (f > 0 && f < 1) {
      ctx.save();
      ctx.translate(0, -50);
      ctx.scale(1, Math.cos(f * Math.PI));
      rrect(ctx, -80, 0, 160, 140, 8); ctx.fillStyle = 'rgba(245,245,245,0.97)'; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 3; ctx.stroke();
      ctx.restore();
    }
    for (const rx of [-40, 40]) { circle(ctx, rx, -100, 8); ctx.fillStyle = '#888'; ctx.fill(); }
    ctx.restore();
  };

  A.rain = function (ctx, t, k, wind = 0.25) {
    if (k <= 0) return;
    ctx.save();
    ctx.strokeStyle = 'rgba(190,210,255,0.5)';
    ctx.lineWidth = 2.2;
    ctx.lineCap = 'round';
    const n = Math.floor(320 * k);
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const v = 1500 + 600 * hash(i * 1.7);
      const y = ((hash(i * 3.1) * (H + 200) + t * v) % (H + 200)) - 100;
      const x = ((hash(i * 7.3) * (W + 400) + y * wind) % (W + 400)) - 200;
      ctx.moveTo(x, y);
      ctx.lineTo(x - wind * 34, y - 34);
    }
    ctx.stroke();
    ctx.restore();
  };
  A.bolt = function (ctx, x, y0, y1, seed, alpha) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha *= alpha;
    ctx.strokeStyle = '#f4f7ff';
    ctx.shadowColor = '#b9c8ff';
    ctx.shadowBlur = 30;
    ctx.lineWidth = 6;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    let px = x;
    ctx.moveTo(px, y0);
    const steps = 9;
    for (let i = 1; i <= steps; i++) {
      px += (hash(seed * 13 + i) - 0.5) * 120;
      ctx.lineTo(px, lerp(y0, y1, i / steps));
    }
    ctx.stroke();
    ctx.lineWidth = 2.5;
    ctx.stroke();
    ctx.restore();
  };
  A.flash = function (ctx, k, color = '#ffffff') {
    if (k <= 0) return;
    ctx.save();
    ctx.globalAlpha = clamp(k);
    ctx.fillStyle = color;
    ctx.fillRect(-10, -10, W + 20, H + 20);
    ctx.restore();
  };
  A.dust = function (ctx, x, y, k, s = 1) {
    if (k <= 0 || k >= 1) return;
    ctx.save();
    for (let i = 0; i < 7; i++) {
      const a = Math.PI + (i / 6) * Math.PI;
      const r = (20 + 70 * F.E.out(k)) * s;
      ctx.globalAlpha = (1 - k) * 0.7;
      ctx.fillStyle = '#d9c7a3';
      circle(ctx, x + Math.cos(a) * r, y + Math.sin(a) * r * 0.35, (14 + 16 * k) * s);
      ctx.fill();
    }
    ctx.restore();
  };
  A.sparkle = function (ctx, x, y, s, alpha = 1, rot = 0) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.scale(s, s);
    ctx.globalAlpha *= alpha;
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const r = i % 2 ? 7 : 26;
      const a = (i / 8) * TAU;
      ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
    }
    ctx.closePath();
    ctx.fillStyle = '#fffbe0';
    ctx.shadowColor = '#ffe680';
    ctx.shadowBlur = 16;
    ctx.fill();
    ctx.restore();
  };
  A.steam = function (ctx, x, y, t, alpha) {
    if (alpha <= 0) return;
    ctx.save();
    for (let i = 0; i < 6; i++) {
      const k = (t * 1.4 + i / 6) % 1;
      ctx.globalAlpha = alpha * (1 - k) * 0.9;
      ctx.fillStyle = '#f4f4f4';
      circle(ctx, x + Math.sin(k * 7 + i) * 10 + (i % 2 ? 1 : -1) * k * 30, y - k * 110, 10 + k * 22);
      ctx.fill();
    }
    ctx.restore();
  };
  A.stamp = function (ctx, str, x, y, k, rot = -0.15, color = '#d62f2f') {
    if (k <= 0) return;
    const sc = lerp(2.6, 1, F.E.out(clamp(k * 1.6)));
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.scale(sc, sc);
    ctx.globalAlpha *= clamp(k * 3);
    ctx.font = `400 72px ${FONT_TITLE}`;
    const w = ctx.measureText(str).width + 60;
    rrect(ctx, -w / 2, -52, w, 104, 14);
    ctx.lineWidth = 10; ctx.strokeStyle = color; ctx.stroke();
    text(ctx, str, 0, 6, { size: 72, font: FONT_TITLE, weight: 400, fill: color });
    ctx.restore();
  };
  A.meter = function (ctx, x, y, v, o = {}) {
    ctx.save();
    ctx.translate(x, y);
    ctx.globalAlpha *= o.alpha ?? 1;
    const w = 620, h = 64;
    text(ctx, 'COGNITIVE ABILITY', 0, -64, { size: 44, font: FONT_TITLE, weight: 400, fill: '#fff', stroke: OUT, lw: 9, ls: 2 });
    rrect(ctx, -w / 2, -h / 2, w, h, 20); ctx.fillStyle = '#2b1d16'; ctx.fill();
    const col = v < 0.3 ? '#e2483a' : v < 0.7 ? '#f2b830' : '#45c46a';
    if (v > 0.005) { rrect(ctx, -w / 2 + 8, -h / 2 + 8, (w - 16) * clamp(v), h - 16, 14); ctx.fillStyle = col; ctx.fill(); }
    rrect(ctx, -w / 2, -h / 2, w, h, 20); ctx.strokeStyle = '#fff'; ctx.lineWidth = 5; ctx.stroke();
    text(ctx, Math.round(v * 100) + '%', w / 2 + 70, 2, { size: 46, weight: 700, fill: col, stroke: OUT, lw: 8 });
    if (o.low) text(ctx, 'LOW', 0, 64, { size: 40, font: FONT_TITLE, weight: 400, fill: '#ff5a4a', stroke: OUT, lw: 8, alpha: o.low });
    ctx.restore();
  };
  A.basin = function (ctx, x, y, t, splash = 0) {
    ctx.save();
    ctx.translate(x, y);
    for (const lx of [-50, 50]) { ctx.strokeStyle = C(OUT); ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(lx * 0.8, -60); ctx.lineTo(lx, 0); ctx.stroke(); ctx.strokeStyle = C('#7a5028'); ctx.lineWidth = 5; ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(-80, -100); ctx.lineTo(80, -100); ctx.lineTo(60, -60); ctx.lineTo(-60, -60); ctx.closePath();
    ctx.fillStyle = C('#aab4bd'); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 5; ctx.stroke();
    ellipse(ctx, 0, -100, 78, 12); ctx.fillStyle = C('#7fc4ef'); ctx.fill(); ctx.stroke();
    if (splash > 0) {
      for (let i = 0; i < 8; i++) {
        const a = -Math.PI * (0.15 + 0.7 * hash(i * 3.3));
        const r = 30 + 60 * splash;
        ctx.globalAlpha = 1 - splash;
        ctx.fillStyle = '#bfe6ff';
        circle(ctx, Math.cos(a) * r, -104 + Math.sin(a) * r * 0.9, 6);
        ctx.fill();
      }
    }
    ctx.restore();
  };

  /** market stall: striped awning, LUXURIES sign, priced goods. `front` draws only the counter (over a shopkeeper). */
  A.stall = function (ctx, x, y, t, o = {}) {
    const outline = C(OUT), wood = C('#a8743e'), dark = C('#7a5028');
    const w = 520;
    ctx.save();
    ctx.translate(x, y);
    if (!o.front) {
      for (const px of [-w / 2 + 16, w / 2 - 16]) { rrect(ctx, px - 9, -480, 18, 480, 4); ctx.fillStyle = dark; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke(); }
      // awning
      const stripes = 8, sw = (w + 40) / stripes;
      for (let i = 0; i < stripes; i++) {
        ctx.beginPath();
        ctx.moveTo(-w / 2 - 20 + i * sw, -480);
        ctx.lineTo(-w / 2 - 20 + (i + 1) * sw, -480);
        ctx.lineTo(-w / 2 - 20 + (i + 1) * sw, -440);
        ctx.quadraticCurveTo(-w / 2 - 20 + (i + 0.5) * sw, -412, -w / 2 - 20 + i * sw, -440);
        ctx.closePath();
        ctx.fillStyle = C(i % 2 ? '#fff6e6' : '#d6453a');
        ctx.fill();
        ctx.strokeStyle = outline; ctx.lineWidth = 3.5; ctx.stroke();
      }
      rrect(ctx, -170, -556, 340, 70, 14); ctx.fillStyle = C('#2b1d16'); ctx.fill();
      text(ctx, 'LUXURIES', 0, -518, { size: 46, font: FONT_TITLE, weight: 400, fill: '#ffd166', ls: 3 });
      return ctx.restore();
    }
    // counter + goods
    rrect(ctx, -w / 2, -130, w, 130, 10); ctx.fillStyle = wood; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    ctx.strokeStyle = dark; ctx.lineWidth = 3;
    for (let yy = -100; yy < 0; yy += 30) { ctx.beginPath(); ctx.moveTo(-w / 2 + 6, yy); ctx.lineTo(w / 2 - 6, yy); ctx.stroke(); }
    rrect(ctx, -w / 2 - 12, -146, w + 24, 22, 8); ctx.fillStyle = C('#c8955a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    const goods = [[-180, 'GOLD CHAIN', '50'], [0, 'WOOL SPA', '20'], [180, 'FANCY HAY', '8']];
    for (const [gx, name, price] of goods) {
      ctx.save();
      ctx.translate(gx, -146);
      if (name === 'GOLD CHAIN') {
        ctx.strokeStyle = C('#f2b830'); ctx.lineWidth = 7; ctx.setLineDash([9, 5]);
        ctx.beginPath(); ctx.ellipse(0, -40, 34, 30, 0, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
        A.token(ctx, 0, -10, 16, 0.3 + Math.sin(t * 2) * 0.3);
      } else if (name === 'WOOL SPA') {
        rrect(ctx, -18, -76, 36, 70, 10); ctx.fillStyle = C('#9ad0f5'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 3.5; ctx.stroke();
        rrect(ctx, -9, -92, 18, 18, 4); ctx.fillStyle = C('#e9e2d4'); ctx.fill(); ctx.stroke();
        for (let i = 0; i < 3; i++) { F.circle(ctx, 20 + i * 8, -84 - i * 14 - ((t * 20) % 10), 5 + i); ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.fill(); }
      } else {
        A.hayBale(ctx, 0, -6, 0.55);
        ctx.strokeStyle = C('#d6453a'); ctx.lineWidth = 6;
        ctx.beginPath(); ctx.moveTo(-20, -40); ctx.lineTo(20, -40); ctx.stroke();
      }
      ctx.restore();
      rrect(ctx, gx - 66, -112, 132, 74, 10); ctx.fillStyle = '#fffdf6'; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 3.5; ctx.stroke();
      text(ctx, name, gx, -90, { size: 19, weight: 700, fill: '#2b1d16' });
      A.token(ctx, gx - 22, -60, 12, 0);
      text(ctx, price, gx + 12, -58, { size: 26, weight: 700, fill: '#b8412f' });
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ calvary
  A.crossShape = function (ctx, x, y, s, sheep, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = color;
    ctx.fillRect(-11, -300, 22, 300);
    ctx.fillRect(-96, -244, 192, 20);
    if (sheep) {
      // a small bowed lamb silhouette on the beam
      const pts = [[-46, -196, 24], [-16, -206, 28], [16, -200, 26], [40, -190, 20], [0, -184, 30], [-30, -180, 22]];
      ctx.beginPath();
      for (const [cx, cy, r] of pts) { ctx.moveTo(cx + r, cy); ctx.arc(cx, cy, r, 0, TAU); }
      ctx.fill();
      ellipse(ctx, 56, -170, 16, 22, 0.6); ctx.fill();
      ctx.fillRect(-70, -238, 14, 40);
      ctx.fillRect(56, -238, 14, 40);
      ctx.fillRect(-26, -170, 12, 46);
      ctx.fillRect(10, -170, 12, 46);
    }
    ctx.restore();
  };

  A.calvary = function (ctx, t, k, cam, o = {}) {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, mix('#2a0610', '#05030a', k));
    g.addColorStop(0.65, mix('#c4452b', '#3a0d14', k));
    g.addColorStop(1, mix('#f08a4a', '#5a1a14', k));
    ctx.fillStyle = g;
    ctx.fillRect(-20, -20, W + 40, H + 40);
    ctx.save();
    applyCam(ctx, cam, 0.15);
    A.sun(ctx, 760, 760 + k * 120, 120, mix('#ffb070', '#7a2a20', k), 1 - k * 0.7);
    ctx.restore();
    // far ridge
    ctx.save();
    applyCam(ctx, cam, 0.4);
    ctx.fillStyle = mix('#5a1a20', '#1a0508', k);
    ctx.beginPath();
    ctx.moveTo(-800, 1400);
    for (let x = -800; x <= 2800; x += 20) ctx.lineTo(x, 760 - 40 * Math.sin(x * 0.004) - 20 * Math.sin(x * 0.013));
    ctx.lineTo(2800, 1400);
    ctx.fill();
    ctx.restore();
    // the hill
    ctx.save();
    applyCam(ctx, cam, 1);
    const sil = '#0d0405';
    ctx.fillStyle = sil;
    ctx.beginPath();
    ctx.moveTo(400, 1300);
    ctx.bezierCurveTo(800, 900, 1050, 560, 1300, 550);
    ctx.bezierCurveTo(1550, 560, 1800, 820, 2300, 1100);
    ctx.lineTo(2300, 1300);
    ctx.closePath();
    ctx.fill();
    A.crossShape(ctx, 1300, 556, 1.05, true, sil);
    // onlookers at the foot of the hill
    for (let i = 0; i < 9; i++) {
      const x = 640 + i * 70 + hash(i) * 30, y = 1010 + hash(i * 2) * 30;
      const s = 0.42 + hash(i * 3) * 0.08;
      ctx.beginPath();
      for (let j = 0; j < 6; j++) { const a = (j / 6) * TAU; ctx.moveTo(x + Math.cos(a) * 60 * s + 24 * s, y - 90 * s + Math.sin(a) * 30 * s); ctx.arc(x + Math.cos(a) * 60 * s, y - 90 * s + Math.sin(a) * 30 * s, 24 * s, 0, TAU); }
      ctx.fill();
      ellipse(ctx, x + 80 * s * (i % 2 ? 1 : -1), y - 110 * s, 22 * s, 28 * s);
      ctx.fill();
      ctx.fillRect(x - 50 * s, y - 70 * s, 12 * s, 70 * s);
      ctx.fillRect(x + 40 * s, y - 70 * s, 12 * s, 70 * s);
    }
    ctx.restore();
    // birds leaving
    if (o.birds !== undefined && o.birds > 0) {
      ctx.save();
      applyCam(ctx, cam, 0.8);
      ctx.strokeStyle = '#0d0405';
      ctx.lineWidth = 4;
      for (let i = 0; i < 7; i++) {
        const bk = o.birds;
        const bx = 1300 + (hash(i) - 0.3) * 200 + bk * (300 + hash(i * 2) * 500);
        const by = 520 - bk * (200 + hash(i * 3) * 250) + Math.sin(bk * 20 + i) * 8;
        const fl = Math.sin(t * 14 + i) * 8;
        ctx.beginPath(); ctx.moveTo(bx - 14, by - fl); ctx.quadraticCurveTo(bx - 6, by - 6, bx, by); ctx.quadraticCurveTo(bx + 6, by - 6, bx + 14, by - fl); ctx.stroke();
      }
      ctx.restore();
    }
  };

  // ------------------------------------------------------------------ city
  A.CITY = { office: 520, apts: 1260, grocery: 2000, tower: 1520, street: 900 };
  function building(ctx, x, w, h, base, col, rows, cols, lit, seed) {
    ctx.fillStyle = col;
    ctx.fillRect(x - w / 2, base - h, w, h);
    ctx.strokeStyle = OUT; ctx.lineWidth = 5; ctx.strokeRect(x - w / 2, base - h, w, h);
    const cw = w / (cols + 1), rh = Math.min(70, h / (rows + 1));
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const on = hash(seed + r * 7 + c * 13) < lit;
      ctx.fillStyle = on ? '#ffd98a' : '#2f3550';
      ctx.fillRect(x - w / 2 + cw * (c + 0.65), base - h + rh * (r + 0.6), cw * 0.7, rh * 0.55);
    }
  }
  A.city = function (ctx, t, cam, o = {}) {
    const pal = { skyTop: '#2e2f66', skyBot: '#f29b72' };
    A.sky(ctx, pal);
    A.sun(ctx, 980, 640, 90, '#ffcf8a', 0.9);
    ctx.save();
    applyCam(ctx, cam, 0.3);
    for (let i = 0; i < 26; i++) {
      const x = -600 + i * 140, w = 110 + hash(i) * 60, h = 180 + hash(i * 3) * 260;
      ctx.fillStyle = '#5b4f7e';
      ctx.fillRect(x - w / 2, 860 - h, w, h + 200);
    }
    ctx.restore();
    ctx.save();
    applyCam(ctx, cam, 0.6);
    for (let i = 0; i < 18; i++) {
      const x = -500 + i * 220, w = 150 + hash(i * 5) * 50, h = 260 + hash(i * 7) * 220;
      building(ctx, x, w, h, 960, '#47426a', Math.floor(h / 60), 3, 0.45, i * 31);
    }
    ctx.restore();
    ctx.save();
    applyCam(ctx, cam, 0.85);
    // the tower with the penthouse
    const tx = A.CITY.tower;
    building(ctx, tx, 260, 900, 960, '#3b4466', 12, 4, 0.5, 999);
    ctx.fillStyle = '#ffd27a';
    ctx.fillRect(tx - 100, 960 - 900 + 30, 200, 90);
    ctx.save();
    ctx.beginPath(); ctx.rect(tx - 100, 960 - 900 + 30, 200, 90); ctx.clip();
    A.farmer(ctx, { x: tx + 30, y: 960 - 900 + 30 + 250, s: 0.6, t, pose: A.POSE.cup, prop: { r: 'cup' }, mood: 'smile', noShadow: true });
    ctx.restore();
    ctx.strokeStyle = OUT; ctx.lineWidth = 5; ctx.strokeRect(tx - 100, 960 - 900 + 30, 200, 90);
    ctx.restore();
    // street level
    ctx.save();
    applyCam(ctx, cam, 1);
    const st = A.CITY.street;
    ctx.fillStyle = '#4a4a5c'; ctx.fillRect(-1000, st, 4500, 400);
    ctx.fillStyle = '#6a6a7e'; ctx.fillRect(-1000, st - 16, 4500, 30);
    ctx.fillStyle = '#e8e3d0';
    for (let x = -1000; x < 3500; x += 140) ctx.fillRect(x, st + 120, 70, 10);
    const shops = [
      [A.CITY.office, 'OFFICE', '#5a7fa8', 'EARN TOKENS'],
      [A.CITY.apts, 'APARTMENTS', '#a8584a', 'RENT: 900 TOKENS'],
      [A.CITY.grocery, 'GROCERY', '#5a9a62', 'FOOD: 80 TOKENS'],
    ];
    for (const [x, name, col, sign] of shops) {
      building(ctx, x, 420, 520, st - 14, col, 5, 4, 0.6, x);
      ctx.fillStyle = '#2b1d16'; ctx.fillRect(x - 70, st - 184, 140, 170);
      rrect(ctx, x - 190, st - 560, 380, 70, 12); ctx.fillStyle = '#2b1d16'; ctx.fill();
      text(ctx, name, x, st - 524, { size: 46, font: FONT_TITLE, weight: 400, fill: '#ffd166', ls: 2 });
      rrect(ctx, x - 150, st - 250, 300, 48, 10); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 4; ctx.stroke();
      text(ctx, sign, x, st - 225, { size: 26, weight: 700, fill: '#2b1d16' });
      A.turnstile(ctx, x + 120, st, { rot: o.gateRot ? o.gateRot(x) : 0, light: o.gateLight ? o.gateLight(x) : null });
    }
    ctx.restore();
  };
})();
