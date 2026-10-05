/* FLEECED - characters: sheep, farmer, humans, ghost, plus small UI-ish props. */
(function () {
  'use strict';
  const { TAU, clamp, lerp, hash, ellipse, circle, rrect, text, mix, FONT_UI, FONT_TITLE } = F;
  const A = (window.A = window.A || {});
  const OUT = '#2b1d16';

  // global night/dusk tint applied to every character & set colour
  A.tint = { color: '#0d1633', k: 0 };
  const C = (c) => (A.tint.k > 0 ? mix(c, A.tint.color, A.tint.k) : c);
  A.C = C;
  A.OUT = OUT;

  function blob(ctx, pts, grow) {
    ctx.beginPath();
    for (const [x, y, r] of pts) {
      ctx.moveTo(x + r + grow, y);
      ctx.arc(x, y, r + grow, 0, TAU);
    }
  }

  // ------------------------------------------------------------------ token
  A.token = function (ctx, x, y, r, spin = 0, o = {}) {
    const sx = Math.cos(spin);
    ctx.save();
    ctx.translate(x, y);
    if (o.alpha !== undefined) ctx.globalAlpha *= o.alpha;
    if (o.rot) ctx.rotate(o.rot);
    ctx.scale(Math.max(0.08, Math.abs(sx)), 1);
    const edge = sx < 0;
    ellipse(ctx, 0, 0, r + 2.5, r + 2.5);
    ctx.fillStyle = C(OUT);
    ctx.fill();
    ellipse(ctx, 0, 0, r, r);
    ctx.fillStyle = C(edge ? '#d39a1e' : '#f2b830');
    ctx.fill();
    ellipse(ctx, 0, 0, r * 0.74, r * 0.74);
    ctx.fillStyle = C(edge ? '#e7b23c' : '#ffd65a');
    ctx.fill();
    // embossed sheep
    ctx.fillStyle = C('#d9991f');
    for (const [bx, by, br] of [[-0.22, 0.02, 0.2], [0, -0.1, 0.22], [0.2, 0.02, 0.2], [0, 0.12, 0.2]]) {
      circle(ctx, bx * r, by * r, br * r);
      ctx.fill();
    }
    ellipse(ctx, 0.38 * r, -0.08 * r, 0.12 * r, 0.15 * r);
    ctx.fill();
    // shine
    ctx.globalAlpha *= 0.7;
    ellipse(ctx, -0.35 * r, -0.4 * r, 0.16 * r, 0.09 * r, -0.7);
    ctx.fillStyle = '#fff8d8';
    ctx.fill();
    ctx.restore();
  };

  /** token balance bubble; widens for big numbers, which get a gold tint (`glow` 0..1 pulses it) */
  A.badge = function (ctx, x, y, n, o = {}) {
    const v = Math.max(0, Math.round(n));
    const label = String(v);
    const zero = v <= 0, rich = v >= 100;
    const w = Math.max(96, 62 + 21 * label.length);
    ctx.save();
    ctx.translate(x, y);
    const sc = o.s ?? 1;
    ctx.scale(sc, sc);
    if (o.alpha !== undefined) ctx.globalAlpha *= o.alpha;
    if (o.glow > 0) {
      ctx.save();
      ctx.shadowColor = '#ffcf3a';
      ctx.shadowBlur = 36 * o.glow;
      rrect(ctx, -w / 2, -24, w, 48, 24);
      ctx.fillStyle = '#ffe9a8';
      ctx.fill();
      ctx.restore();
    }
    rrect(ctx, -w / 2, -24, w, 48, 24);
    ctx.fillStyle = zero ? '#c0392b' : rich ? '#ffe9a8' : 'rgba(255,255,255,0.95)';
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = OUT;
    ctx.stroke();
    if (rich) {
      rrect(ctx, -w / 2 + 5, -19, w - 10, 38, 19);
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = '#d9a21e';
      ctx.stroke();
    }
    A.token(ctx, -w / 2 + 28, 0, 15, 0);
    text(ctx, label, 19, 2, { size: 34, weight: 700, fill: zero ? '#fff' : '#3a2a1a' });
    ctx.restore();
  };

  // ------------------------------------------------------------------ sheep
  /**
   * o: x,y (ground), s, dir(1 right/-1 left), t, seed, wool, face, mood, talk(0..1),
   * blink, walk(phase|null), shiver, fall(0..1), look{x,y}, chain, halo, thin, fluff,
   * punk, cup, torch, stomp(0..1 front legs raised), badge(number|null), alpha, red(0..1 face flush)
   */
  A.sheep = function (ctx, o) {
    const s = o.s ?? 1, dir = o.dir ?? 1, t = o.t ?? 0, seed = o.seed ?? 0;
    const wool = C(o.wool || '#f7f3ea');
    const face = C(mix(o.face || '#4a3f3a', '#d24a3a', o.red || 0));
    const outline = C(OUT);
    ctx.save();
    ctx.translate(o.x, o.y);
    if (o.alpha !== undefined) ctx.globalAlpha *= o.alpha;
    if (!o.noShadow) {
      ctx.fillStyle = 'rgba(0,0,0,0.2)';
      ellipse(ctx, 0, 2, 80 * s, 13 * s);
      ctx.fill();
    }
    ctx.save();
    ctx.scale(dir * s, s);
    if (o.fall) {
      ctx.translate(0, o.fall * 46);
      ctx.translate(0, -100);
      ctx.rotate(o.fall * Math.PI);
      ctx.translate(0, 100);
    }
    if (o.lean) ctx.rotate(o.lean);
    const walking = o.walk !== undefined && o.walk !== null;
    const bob = walking ? -Math.abs(Math.sin(o.walk)) * 8 : Math.sin(t * 2.2 + seed * 3) * 2.2;
    const shiv = o.shiver ? Math.sin(t * 55 + seed) * 3.5 * o.shiver : 0;
    const by = -100 + bob;
    ctx.translate(shiv, 0);

    if (o.halo) {
      const g = ctx.createRadialGradient(10, by - 10, 10, 10, by - 10, 210);
      g.addColorStop(0, `rgba(255,236,170,${0.55 * o.halo})`);
      g.addColorStop(1, 'rgba(255,236,170,0)');
      ctx.fillStyle = g;
      circle(ctx, 10, by - 10, 210);
      ctx.fill();
    }

    // legs
    const legTop = by + 34;
    const legs = [[-50, 0], [-24, Math.PI], [32, Math.PI], [56, 0]];
    for (const [lx, ph] of legs) {
      let ang = walking ? Math.sin(o.walk + ph) * 0.42 : 0;
      if (o.stomp && lx > 0) ang -= o.stomp * 0.9;
      const len = -legTop - (o.stomp && lx > 0 ? o.stomp * 14 : 0);
      ctx.save();
      ctx.translate(lx * (o.thin ? 0.85 : 1), legTop);
      ctx.rotate(ang);
      rrect(ctx, -9, -6, 18, len + 6, 7);
      ctx.fillStyle = outline;
      ctx.fill();
      rrect(ctx, -6, -6, 12, len + 2, 5);
      ctx.fillStyle = face;
      ctx.fill();
      rrect(ctx, -7, len - 10, 14, 10, 3);
      ctx.fillStyle = C('#231a17');
      ctx.fill();
      ctx.restore();
    }

    // tail
    const tailWag = Math.sin(t * 7 + seed) * 0.15;
    blob(ctx, [[-88 + tailWag * 20, by - 12, 14]], 5);
    ctx.fillStyle = outline;
    ctx.fill();
    blob(ctx, [[-88 + tailWag * 20, by - 12, 14]], 0);
    ctx.fillStyle = wool;
    ctx.fill();

    // body cloud
    const fl = o.fluff || 1;
    const rx = 80 * (o.thin ? 0.82 : 1) * fl, ry = 50 * fl;
    const pts = [];
    const n = 13;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * TAU + 0.2;
      const r = (24 + 7 * hash(i * 3.1 + seed * 7.7)) * fl * (o.thin ? 0.9 : 1);
      pts.push([Math.cos(a) * rx * 0.84, by + Math.sin(a) * ry * 0.78, r]);
    }
    pts.push([0, by, ry * 0.95]);
    pts.push([-rx * 0.4, by, ry * 0.9]);
    pts.push([rx * 0.4, by, ry * 0.9]);
    blob(ctx, pts, 5);
    ctx.fillStyle = outline;
    ctx.fill();
    const g = ctx.createLinearGradient(0, by - ry - 20, 0, by + ry + 20);
    g.addColorStop(0, mix(wool, '#ffffff', 0.45));
    g.addColorStop(0.55, wool);
    g.addColorStop(1, mix(wool, '#8d8170', 0.3));
    blob(ctx, pts, 0);
    ctx.fillStyle = g;
    ctx.fill();
    // curls
    ctx.strokeStyle = mix(wool, '#8d8170', 0.35);
    ctx.lineWidth = 3;
    for (let i = 0; i < 6; i++) {
      const cx = -50 + i * 20 + hash(i + seed) * 8, cy = by - 8 + (i % 2) * 22 - 6;
      ctx.beginPath();
      ctx.arc(cx, cy, 7, 0.4, 2.8);
      ctx.stroke();
    }

    if (o.chain) {
      ctx.save();
      ctx.strokeStyle = C('#f2b830');
      ctx.lineWidth = 7;
      ctx.setLineDash([9, 5]);
      ctx.beginPath();
      ctx.moveTo(40, by - 30);
      ctx.quadraticCurveTo(52, by + 34, 84, by + 6);
      ctx.stroke();
      ctx.restore();
      A.token(ctx, 60, by + 30, 17, 0.25 + Math.sin(t * 2 + seed) * 0.25);
    }

    // head
    const hx = 86 + (o.headDx || 0), hy = by - 26 + (o.headDy || 0);
    const droop = o.droop || 0;
    const tilt = -0.22 + (o.headTilt || 0);
    // back ear
    ctx.save();
    ctx.translate(hx - 20, hy - 18);
    ctx.rotate(-2.5 - droop * 0.9 + Math.sin(t * 3 + seed) * 0.05);
    ellipse(ctx, 18, 0, 22, 11);
    ctx.fillStyle = outline;
    ctx.fill();
    ellipse(ctx, 18, 0, 18, 7.5);
    ctx.fillStyle = face;
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.translate(hx, hy);
    ctx.rotate(tilt);
    ellipse(ctx, 0, 0, 35, 41);
    ctx.fillStyle = outline;
    ctx.fill();
    ellipse(ctx, 0, 0, 30, 36);
    ctx.fillStyle = face;
    ctx.fill();
    // muzzle
    ellipse(ctx, 8, 20, 18, 13);
    ctx.fillStyle = mix(face, '#ffffff', 0.12);
    ctx.fill();
    ctx.fillStyle = C('#1d1512');
    circle(ctx, 4, 16, 2.2);
    ctx.fill();
    circle(ctx, 16, 15, 2.2);
    ctx.fill();

    // eyes
    const mood = o.mood || 'neutral';
    const blinkK = o.blink ? 0.12 : 1;
    const look = o.look || { x: 1, y: 0 };
    const eyes = [[-8, -10, 10.5], [14, -12, 9.5]];
    for (const [ex, ey, er] of eyes) {
      if (mood === 'happy' || mood === 'kind') {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.arc(ex, ey + 4, er * 0.75, Math.PI * 1.1, Math.PI * 1.9);
        ctx.stroke();
        continue;
      }
      if (mood === 'dead') {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(ex - 6, ey - 6); ctx.lineTo(ex + 6, ey + 6);
        ctx.moveTo(ex + 6, ey - 6); ctx.lineTo(ex - 6, ey + 6);
        ctx.stroke();
        continue;
      }
      if (mood === 'sleep') {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 3.5;
        ctx.beginPath();
        ctx.moveTo(ex - 7, ey + 2); ctx.lineTo(ex + 7, ey + 2);
        ctx.stroke();
        continue;
      }
      const big = mood === 'shock' ? 1.25 : 1;
      ellipse(ctx, ex, ey, er * big, er * big * blinkK);
      ctx.fillStyle = '#fff';
      ctx.fill();
      if (blinkK > 0.5) {
        const pr = mood === 'shock' ? 2.8 : mood === 'angry' ? 3.8 : 4.8;
        ctx.fillStyle = '#16100e';
        circle(ctx, ex + look.x * 3.2 + (o.cross ? (ex < 0 ? 4 : -4) : 0), ey + look.y * 3, pr);
        ctx.fill();
        ctx.fillStyle = '#fff';
        circle(ctx, ex + look.x * 3.2 + 1.5, ey + look.y * 3 - 1.8, 1.4);
        ctx.fill();
      }
      if (mood === 'smug' || mood === 'tired') {
        ctx.fillStyle = face;
        ctx.beginPath();
        ctx.ellipse(ex, ey, er + 1.5, er + 1.5, 0, Math.PI, TAU);
        ctx.lineTo(ex + er + 1.5, ey + (mood === 'tired' ? 1 : -1));
        ctx.fill();
        ctx.strokeStyle = '#16100e';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(ex - er, ey);
        ctx.lineTo(ex + er, ey);
        ctx.stroke();
      }
    }
    // brows
    if (mood === 'angry' || mood === 'worried' || mood === 'sad' || mood === 'smug') {
      ctx.strokeStyle = mix(wool, '#bbb', 0.2);
      ctx.lineWidth = 4.5;
      ctx.lineCap = 'round';
      const k = mood === 'angry' ? 1 : mood === 'smug' ? 0.3 : -1;
      ctx.beginPath();
      ctx.moveTo(-17, -27 - 4 * k); ctx.lineTo(-1, -25 + 5 * k);
      ctx.moveTo(6, -27 + 5 * k); ctx.lineTo(23, -30 - 4 * k);
      ctx.stroke();
    }
    // mouth
    const tk = clamp(o.talk || 0);
    ctx.lineCap = 'round';
    if (tk > 0.05 || mood === 'yell') {
      const open = mood === 'yell' ? Math.max(0.75, tk) : tk;
      ellipse(ctx, 10, 29, 7 + open * 4, 2 + open * 11);
      ctx.fillStyle = '#4a1414';
      ctx.fill();
      ellipse(ctx, 10, 31 + open * 5, 5 + open * 2, 1 + open * 4);
      ctx.fillStyle = '#e07b84';
      ctx.fill();
    } else if (mood === 'happy' || mood === 'kind' || mood === 'smug') {
      ctx.strokeStyle = '#16100e';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(10, 24, 8, 0.35, Math.PI - 0.35);
      ctx.stroke();
    } else if (mood === 'sad' || mood === 'worried' || mood === 'angry' || mood === 'dead') {
      ctx.strokeStyle = '#16100e';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(10, 36, 7, Math.PI + 0.5, TAU - 0.5);
      ctx.stroke();
    } else {
      ctx.strokeStyle = '#16100e';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(4, 29); ctx.lineTo(16, 28);
      ctx.stroke();
    }
    ctx.restore();

    // head tuft
    if (o.punk) {
      ctx.save();
      ctx.translate(hx, hy - 30);
      ctx.rotate(tilt);
      ctx.beginPath();
      for (let i = 0; i < 5; i++) {
        const a = -2.4 + i * 0.4;
        ctx.moveTo(Math.cos(a - 0.25) * 12, Math.sin(a - 0.25) * 12);
        ctx.lineTo(Math.cos(a) * (34 + (i % 2) * 8), Math.sin(a) * (34 + (i % 2) * 8));
        ctx.lineTo(Math.cos(a + 0.25) * 12, Math.sin(a + 0.25) * 12);
      }
      ctx.fillStyle = C('#e04f8c');
      ctx.strokeStyle = outline;
      ctx.lineWidth = 4;
      ctx.lineJoin = 'round';
      ctx.stroke();
      ctx.fill();
      ctx.restore();
    } else {
      const tuft = [[hx - 12, hy - 34, 12], [hx + 2, hy - 40, 13], [hx + 16, hy - 33, 11]];
      blob(ctx, tuft, 4.5);
      ctx.fillStyle = outline;
      ctx.fill();
      blob(ctx, tuft, 0);
      ctx.fillStyle = mix(wool, '#ffffff', 0.3);
      ctx.fill();
    }
    // front ear
    ctx.save();
    ctx.translate(hx + 22, hy - 16);
    ctx.rotate(-0.35 + droop * 1.0 - Math.sin(t * 3 + seed) * 0.05);
    ellipse(ctx, 18, 0, 22, 11);
    ctx.fillStyle = outline;
    ctx.fill();
    ellipse(ctx, 18, 0, 18, 7.5);
    ctx.fillStyle = face;
    ctx.fill();
    ellipse(ctx, 19, 0, 11, 3.5);
    ctx.fillStyle = C('#d98a8a');
    ctx.fill();
    ctx.restore();

    if (o.halo) {
      ctx.save();
      ctx.globalAlpha *= o.halo;
      ctx.strokeStyle = '#ffe28a';
      ctx.lineWidth = 7;
      ctx.shadowColor = '#ffd75a';
      ctx.shadowBlur = 18;
      ellipse(ctx, hx - 4, hy - 64 + Math.sin(t * 2) * 3, 30, 9);
      ctx.stroke();
      ctx.restore();
    }
    if (o.cup) {
      ctx.save();
      ctx.translate(hx + 30, hy + 40);
      ctx.rotate(0.1 + (o.cupLift || 0) * -0.5);
      rrect(ctx, -14, -6, 28, 30, 4);
      ctx.fillStyle = C('#b9c2c9');
      ctx.fill();
      ctx.strokeStyle = outline;
      ctx.lineWidth = 3.5;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(-14, 0);
      ctx.lineTo(-24, -8);
      ctx.stroke();
      ctx.restore();
    }
    if (o.torch) {
      ctx.save();
      ctx.translate(hx + 26, hy + 26);
      ctx.rotate(-0.55);
      rrect(ctx, -5, -120, 10, 124, 4);
      ctx.fillStyle = C('#7a4a26');
      ctx.fill();
      ctx.strokeStyle = outline;
      ctx.lineWidth = 3;
      ctx.stroke();
      const fl = 1 + Math.sin(t * 23 + seed * 5) * 0.12 + Math.sin(t * 37 + seed) * 0.08;
      ctx.translate(0, -124);
      ctx.fillStyle = 'rgba(255,170,60,0.35)';
      circle(ctx, 0, -14, 34 * fl);
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(-14, 0);
      ctx.quadraticCurveTo(-18 * fl, -30, 0, -54 * fl);
      ctx.quadraticCurveTo(18 * fl, -30, 14, 0);
      ctx.closePath();
      ctx.fillStyle = '#ff8a2a';
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(-7, 0);
      ctx.quadraticCurveTo(-8, -18, 0, -32 * fl);
      ctx.quadraticCurveTo(8, -18, 7, 0);
      ctx.closePath();
      ctx.fillStyle = '#ffe066';
      ctx.fill();
      ctx.restore();
    }
    ctx.restore(); // flip

    if (o.badge !== undefined && o.badge !== null) {
      A.badge(ctx, 10 * dir * s, (-215 + bob) * s, o.badge, { s: (o.badgeS ?? 1) * Math.max(0.75, s), alpha: o.badgeA, glow: o.badgeGlow });
    }
    ctx.restore();
  };

  A.ghostSheep = function (ctx, x, y, s, t, alpha = 0.7) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.globalAlpha *= alpha;
    const pts = [];
    for (let i = 0; i < 9; i++) {
      const a = (i / 9) * TAU;
      pts.push([Math.cos(a) * 60, Math.sin(a) * 34, 22]);
    }
    pts.push([0, 0, 40]);
    ctx.shadowColor = 'rgba(200,225,255,0.9)';
    ctx.shadowBlur = 24;
    ctx.fillStyle = '#eef6ff';
    blob(ctx, pts, 0);
    ctx.fill();
    ctx.shadowBlur = 0;
    // wavy tail
    ctx.beginPath();
    ctx.moveTo(-60, 10);
    for (let i = 0; i <= 6; i++) ctx.lineTo(-60 + i * 20, 46 + Math.sin(t * 8 + i) * 8 + (i % 2) * 10);
    ctx.lineTo(60, 10);
    ctx.fill();
    ellipse(ctx, 66, -20, 24, 28, -0.2);
    ctx.fill();
    ctx.fillStyle = '#5a6a8a';
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#5a6a8a';
    for (const ex of [58, 76]) {
      ctx.beginPath();
      ctx.moveTo(ex - 5, -28); ctx.lineTo(ex + 5, -18);
      ctx.moveTo(ex + 5, -28); ctx.lineTo(ex - 5, -18);
      ctx.stroke();
    }
    ctx.strokeStyle = '#ffe28a';
    ctx.lineWidth = 5;
    ellipse(ctx, 64, -62, 24, 7);
    ctx.stroke();
    ctx.restore();
  };

  // ------------------------------------------------------------------ farmer
  function ik(sx, sy, tx, ty, L1, L2, bend) {
    let dx = tx - sx, dy = ty - sy;
    let d = Math.hypot(dx, dy);
    d = clamp(d, Math.abs(L1 - L2) + 0.5, L1 + L2 - 0.5);
    const a = Math.atan2(dy, dx);
    const c = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1);
    const a1 = a + bend * Math.acos(c);
    const ex = sx + L1 * Math.cos(a1), ey = sy + L1 * Math.sin(a1);
    const a2 = Math.atan2(ty - ey, tx - ex);
    return { ex, ey, hx: ex + L2 * Math.cos(a2), hy: ey + L2 * Math.sin(a2), a2 };
  }

  /** standard hand targets (body space: feet at 0,0, standing) */
  A.POSE = {
    idle: { r: [80, -128], l: [-80, -128], rb: -1, lb: 1 },
    wave: { r: [128, -390], l: [-80, -128], rb: 1, lb: 1 },
    hold: { r: [96, -436], l: [-80, -128], rb: 1, lb: 1 },
    hips: { r: [64, -150], l: [-64, -150], rb: -1, lb: 1 },
    shrug: { r: [138, -215], l: [-138, -215], rb: 1, lb: -1 },
    facepalm: { r: [8, -334], l: [-74, -132], rb: -1, lb: 1, re: [44, -212], big: 'r' },
    cup: { r: [26, -298], l: [-80, -128], rb: -1, lb: 1 },
    cupDown: { r: [92, -186], l: [-80, -128], rb: -1, lb: 1 },
    remote: { r: [104, -236], l: [-80, -128], rb: -1, lb: 1 },
    wash: { r: [26, -112], l: [-26, -112], rb: -1, lb: 1 },
    neck: { r: [40, -330], l: [-80, -128], rb: 1, lb: 1 },
    point: { r: [168, -300], l: [-80, -128], rb: -1, lb: 1 },
    dismiss: { r: [120, -250], l: [-80, -128], rb: -1, lb: 1 },
    sit: { r: [76, -112], l: [-76, -112], rb: -1, lb: 1 },
    sitCup: { r: [24, -246], l: [-76, -112], rb: -1, lb: 1 },
    sitDismiss: { r: [124, -196], l: [-76, -112], rb: -1, lb: 1 },
    sitShrug: { r: [140, -170], l: [-140, -170], rb: 1, lb: -1 },
    sitHat: { r: [10, -340], l: [-76, -112], rb: 1, lb: 1 },
    sitToss: { r: [70, -330], l: [-76, -112], rb: 1, lb: 1 },
    sitRemote: { r: [96, -190], l: [-76, -112], rb: -1, lb: 1 },
  };
  A.mixPose = function (p, q, k) {
    if (k <= 0) return p;
    if (k >= 1) return q;
    const o = {
      r: [lerp(p.r[0], q.r[0], k), lerp(p.r[1], q.r[1], k)],
      l: [lerp(p.l[0], q.l[0], k), lerp(p.l[1], q.l[1], k)],
      rb: k < 0.5 ? p.rb : q.rb, lb: k < 0.5 ? p.lb : q.lb,
    };
    if (q.re && k > 0.5) { o.re = q.re; o.big = q.big; }
    else if (p.re && k <= 0.5) { o.re = p.re; o.big = p.big; }
    return o;
  };

  /**
   * o: x,y,s,dir,t, pose{r,l,rb,lb}, talk, mood('smile'|'grin'|'neutral'|'worried'|'tired'|'sleep'|'shock'|'frown'),
   * blink, sit(0..1), slump(0..1), shrug(0..1), hatOver(0..1), hatPop(0..1), prop{r:'token'|'cup'|'remote'|'crook'},
   * armFront('r'), headTilt, look
   */
  A.farmer = function (ctx, o) {
    const s = o.s ?? 1, t = o.t ?? 0, outline = C(OUT);
    const skin = C('#f1c29a'), shirt = C('#c8423b'), shirtDark = C('#9e2f2a'), denim = C('#3e6db3'), denimDark = C('#2f568f');
    const sit = o.sit || 0;
    ctx.save();
    ctx.translate(o.x, o.y);
    if (o.alpha !== undefined) ctx.globalAlpha *= o.alpha;
    if (!o.noShadow) {
      ctx.fillStyle = 'rgba(0,0,0,0.2)';
      ellipse(ctx, 0, 2, 90 * s, 14 * s);
      ctx.fill();
    }
    ctx.scale(s * (o.dir ?? 1), s);
    const breathe = Math.sin(t * 2.1) * 1.6;
    const drop = sit * 64;
    const hipY = -150 + drop;
    const shY = hipY - 112 + breathe * 0.4 + (o.slump || 0) * 12 - (o.shrug || 0) * 14;

    // legs
    ctx.lineCap = 'round';
    if (sit > 0.5) {
      for (const sx of [-1, 1]) {
        const kx = sx * 34, ky = hipY + 6;
        ctx.strokeStyle = outline; ctx.lineWidth = 46;
        ctx.beginPath(); ctx.moveTo(sx * 22, hipY - 8); ctx.lineTo(kx, ky); ctx.lineTo(sx * 30, -24); ctx.stroke();
        ctx.strokeStyle = denim; ctx.lineWidth = 38;
        ctx.beginPath(); ctx.moveTo(sx * 22, hipY - 8); ctx.lineTo(kx, ky); ctx.lineTo(sx * 30, -24); ctx.stroke();
        ellipse(ctx, kx, ky, 22, 18); ctx.fillStyle = denimDark; ctx.fill();
        rrect(ctx, sx * 30 - 26, -26, 52, 26, 10); ctx.fillStyle = C('#4a2c1a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
      }
    } else {
      for (const sx of [-1, 1]) {
        rrect(ctx, sx * 24 - 23, hipY - 10, 46, -hipY - 8, 14);
        ctx.fillStyle = outline; ctx.fill();
        rrect(ctx, sx * 24 - 19, hipY - 10, 38, -hipY - 12, 12);
        ctx.fillStyle = sx < 0 ? denim : denimDark; ctx.fill();
        rrect(ctx, sx * 26 - 27, -28, 54, 28, 11);
        ctx.fillStyle = C('#4a2c1a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
      }
    }

    // torso
    const tw = 66;
    ctx.beginPath();
    ctx.moveTo(-tw + 6, hipY + 8);
    ctx.quadraticCurveTo(-tw - 8, (hipY + shY) / 2, -tw + 4, shY);
    ctx.quadraticCurveTo(0, shY - 18, tw - 4, shY);
    ctx.quadraticCurveTo(tw + 8, (hipY + shY) / 2, tw - 6, hipY + 8);
    ctx.closePath();
    ctx.fillStyle = shirt;
    ctx.fill();
    ctx.save();
    ctx.clip();
    ctx.strokeStyle = shirtDark;
    ctx.lineWidth = 6;
    for (let x = -tw; x < tw; x += 22) { ctx.beginPath(); ctx.moveTo(x, shY - 20); ctx.lineTo(x, hipY + 10); ctx.stroke(); }
    ctx.lineWidth = 4;
    for (let y = shY; y < hipY + 10; y += 22) { ctx.beginPath(); ctx.moveTo(-tw, y); ctx.lineTo(tw, y); ctx.stroke(); }
    // bib + straps
    rrect(ctx, -38, hipY - 72, 76, 84, 8);
    ctx.fillStyle = denim; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    ctx.lineWidth = 14; ctx.strokeStyle = denim;
    ctx.beginPath(); ctx.moveTo(-32, hipY - 66); ctx.lineTo(-44, shY - 6); ctx.moveTo(32, hipY - 66); ctx.lineTo(44, shY - 6); ctx.stroke();
    ctx.fillStyle = C('#f2c94c');
    circle(ctx, -26, hipY - 60, 6); ctx.fill();
    circle(ctx, 26, hipY - 60, 6); ctx.fill();
    rrect(ctx, -16, hipY - 46, 32, 22, 4); ctx.fillStyle = denimDark; ctx.fill();
    ctx.restore();
    ctx.beginPath();
    ctx.moveTo(-tw + 6, hipY + 8);
    ctx.quadraticCurveTo(-tw - 8, (hipY + shY) / 2, -tw + 4, shY);
    ctx.quadraticCurveTo(0, shY - 18, tw - 4, shY);
    ctx.quadraticCurveTo(tw + 8, (hipY + shY) / 2, tw - 6, hipY + 8);
    ctx.closePath();
    ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();

    // arms
    const pose = o.pose || A.POSE.idle;
    const lift = drop + (shY - (-262 + drop));
    const arm = (side) => {
      const sx = side === 'r' ? 58 : -58, sy = shY + 12;
      const tgt = pose[side];
      const tx = tgt[0], ty = tgt[1] + (pose === A.POSE.idle ? lift * 0.8 : 0);
      const fixedElbow = side === 'r' ? pose.re : pose.le;
      let j;
      if (fixedElbow) {
        const [ex, ey] = fixedElbow;
        j = { ex, ey, hx: tx, hy: ty, a2: Math.atan2(ty - ey, tx - ex) };
      } else j = ik(sx, sy, tx, ty, 78, 74, side === 'r' ? pose.rb : pose.lb);
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.strokeStyle = outline; ctx.lineWidth = 34;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(j.ex, j.ey); ctx.lineTo(j.hx, j.hy); ctx.stroke();
      ctx.strokeStyle = shirt; ctx.lineWidth = 25;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(j.ex, j.ey); ctx.lineTo(j.hx, j.hy); ctx.stroke();
      // cuff
      ctx.strokeStyle = shirtDark; ctx.lineWidth = 25;
      ctx.beginPath();
      ctx.moveTo(j.hx - Math.cos(j.a2) * 16, j.hy - Math.sin(j.a2) * 16);
      ctx.lineTo(j.hx - Math.cos(j.a2) * 8, j.hy - Math.sin(j.a2) * 8);
      ctx.stroke();
      const prop = o.prop && o.prop[side];
      if (prop === 'crook') drawCrook(ctx, j.hx, j.hy, o.crookRot ?? -0.2);
      const hr = pose.big === side ? 24 : 13;
      ellipse(ctx, j.hx, j.hy, hr + 4, (hr + 4) * (pose.big === side ? 0.85 : 1)); ctx.fillStyle = outline; ctx.fill();
      ellipse(ctx, j.hx, j.hy, hr, hr * (pose.big === side ? 0.85 : 1)); ctx.fillStyle = skin; ctx.fill();
      if (prop === 'token') A.token(ctx, j.hx + 4, j.hy - 30, 26, o.tokenSpin || 0);
      if (prop === 'cup') drawCup(ctx, j.hx + 6, j.hy - 6);
      if (prop === 'remote') drawRemote(ctx, j.hx + 8, j.hy - 22, o.press || 0);
      if (prop === 'smallToken') A.token(ctx, j.hx + 16, j.hy - 14, 13, o.tokenSpin || 0);
    };
    if (o.armFront !== 'l') arm('l');
    if (o.armFront !== 'r') arm('r');

    // head
    const hx = 0, hy = shY - 66;
    ctx.save();
    ctx.translate(hx, hy + 40);
    ctx.rotate(o.headTilt || 0);
    ctx.translate(-hx, -(hy + 40));
    rrect(ctx, -16, hy + 30, 32, 30, 8); ctx.fillStyle = skin; ctx.fill();
    for (const sx of [-1, 1]) { circle(ctx, sx * 46, hy + 4, 14); ctx.fillStyle = outline; ctx.fill(); circle(ctx, sx * 46, hy + 4, 10); ctx.fillStyle = skin; ctx.fill(); }
    ellipse(ctx, 0, 0 + hy, 51, 57); ctx.fillStyle = outline; ctx.fill();
    ellipse(ctx, 0, hy, 46, 52); ctx.fillStyle = skin; ctx.fill();
    ctx.fillStyle = 'rgba(230,110,110,0.35)';
    ellipse(ctx, -28, hy + 16, 11, 7); ctx.fill();
    ellipse(ctx, 28, hy + 16, 11, 7); ctx.fill();

    const mood = o.mood || 'smile';
    const look = o.look || { x: 0, y: 0 };
    // eyes
    for (const sx of [-1, 1]) {
      const ex = sx * 17 + look.x * 3, ey = hy - 8 + look.y * 2;
      if (mood === 'sleep' || o.blink) {
        ctx.strokeStyle = '#2a1a12'; ctx.lineWidth = 3.5; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.arc(ex, ey - 2, 7, 0.2, Math.PI - 0.2); ctx.stroke();
      } else if (mood === 'grin') {
        ctx.strokeStyle = '#2a1a12'; ctx.lineWidth = 4.5; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.arc(ex, ey + 6, 8, Math.PI + 0.5, TAU - 0.5); ctx.stroke();
      } else if (mood === 'shock') {
        ellipse(ctx, ex, ey, 11, 13); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = '#2a1a12'; ctx.lineWidth = 2.5; ctx.stroke();
        circle(ctx, ex, ey, 4); ctx.fillStyle = '#2a1a12'; ctx.fill();
      } else {
        ellipse(ctx, ex, ey, 6, 8.5); ctx.fillStyle = '#2a1a12'; ctx.fill();
        circle(ctx, ex + 2, ey - 3, 2); ctx.fillStyle = '#fff'; ctx.fill();
        if (mood === 'tired') { ctx.fillStyle = skin; ctx.fillRect(ex - 9, ey - 12, 18, 10); ctx.strokeStyle = '#2a1a12'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(ex - 8, ey - 2); ctx.lineTo(ex + 8, ey - 2); ctx.stroke(); }
      }
    }
    // brows
    ctx.strokeStyle = '#6b4226'; ctx.lineWidth = 6; ctx.lineCap = 'round';
    const bk = { worried: -1, shock: -0.6, grin: 0.7, frown: 0.9, tired: -0.3 }[mood] || 0;
    ctx.beginPath();
    ctx.moveTo(-28, hy - 26 - bk * 3); ctx.lineTo(-8, hy - 25 + bk * 5);
    ctx.moveTo(8, hy - 25 + bk * 5); ctx.lineTo(28, hy - 26 - bk * 3);
    ctx.stroke();
    // nose
    ellipse(ctx, 0, hy + 8, 14, 12); ctx.fillStyle = outline; ctx.fill();
    ellipse(ctx, 0, hy + 8, 11, 9.5); ctx.fillStyle = C('#e7a07a'); ctx.fill();
    // mouth
    const tk = clamp(o.talk || 0);
    const my = hy + 31;
    if (tk > 0.05) {
      ellipse(ctx, 0, my + 2, 9 + tk * 5, 2 + tk * 13); ctx.fillStyle = '#4a1414'; ctx.fill();
      ellipse(ctx, 0, my + 6 + tk * 6, 6, 1 + tk * 4); ctx.fillStyle = '#e07b84'; ctx.fill();
    } else if (mood === 'grin') {
      ctx.beginPath(); ctx.moveTo(-24, my - 4); ctx.quadraticCurveTo(0, my + 22, 24, my - 4); ctx.closePath();
      ctx.fillStyle = '#4a1414'; ctx.fill();
      ctx.beginPath(); ctx.moveTo(-21, my - 2); ctx.quadraticCurveTo(0, my + 8, 21, my - 2); ctx.closePath();
      ctx.fillStyle = '#fff'; ctx.fill();
    } else if (mood === 'worried' || mood === 'frown' || mood === 'tired') {
      ctx.strokeStyle = '#4a1414'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(0, my + 12, 11, Math.PI + 0.6, TAU - 0.6); ctx.stroke();
    } else if (mood === 'shock') {
      ellipse(ctx, 0, my + 4, 8, 11); ctx.fillStyle = '#4a1414'; ctx.fill();
    } else if (mood !== 'sleep') {
      ctx.strokeStyle = '#4a1414'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(0, my - 6, 13, 0.5, Math.PI - 0.5); ctx.stroke();
    }
    // moustache
    ctx.fillStyle = C('#7a4a2a');
    ctx.beginPath();
    ctx.moveTo(0, hy + 18);
    ctx.bezierCurveTo(-14, hy + 12, -36, hy + 16, -34, hy + 28);
    ctx.bezierCurveTo(-22, hy + 26, -8, hy + 28, 0, hy + 22);
    ctx.bezierCurveTo(8, hy + 28, 22, hy + 26, 34, hy + 28);
    ctx.bezierCurveTo(36, hy + 16, 14, hy + 12, 0, hy + 18);
    ctx.fill();

    // hat
    const ho = o.hatOver || 0, hp = o.hatPop || 0;
    ctx.save();
    ctx.translate(0, hy - 38 + ho * 34 - hp * 40);
    ctx.rotate((o.hatTilt || 0) + ho * 0.08 - hp * 0.2);
    ellipse(ctx, 0, 0, 94, 20); ctx.fillStyle = outline; ctx.fill();
    ellipse(ctx, 0, 0, 89, 16); ctx.fillStyle = C('#e2b95a'); ctx.fill();
    ellipse(ctx, 0, 4, 70, 9); ctx.fillStyle = C('#c99d42'); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(-48, 0); ctx.bezierCurveTo(-50, -44, -30, -58, 0, -58); ctx.bezierCurveTo(30, -58, 50, -44, 48, 0); ctx.closePath();
    ctx.fillStyle = C('#ebc76a'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    ctx.save(); ctx.clip();
    ctx.fillStyle = C('#b5432f'); ctx.fillRect(-50, -16, 100, 12);
    ctx.restore();
    ctx.restore();
    ctx.restore(); // head tilt

    if (o.armFront === 'r') arm('r');
    if (o.armFront === 'l') arm('l');
    ctx.restore();
  };

  function drawCup(ctx, x, y) {
    ctx.save();
    ctx.translate(x, y);
    rrect(ctx, -12, -34, 24, 38, 5);
    ctx.fillStyle = 'rgba(255,240,150,0.85)';
    ctx.fill();
    ctx.strokeStyle = C(OUT); ctx.lineWidth = 3; ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.fillRect(-7, -28, 4, 24);
    ctx.fillStyle = C('#ffe266');
    circle(ctx, 10, -34, 7); ctx.fill();
    ctx.restore();
  }
  function drawRemote(ctx, x, y, press) {
    ctx.save();
    ctx.translate(x, y);
    rrect(ctx, -20, -34, 40, 64, 8);
    ctx.fillStyle = C('#3b3f46'); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 3.5; ctx.stroke();
    ellipse(ctx, 0, -12 + press * 2, 13, 13 - press * 3);
    ctx.fillStyle = press > 0.5 ? '#ff3b2f' : '#e0281e'; ctx.fill(); ctx.strokeStyle = '#7a120c'; ctx.lineWidth = 2.5; ctx.stroke();
    text(ctx, 'TOKENS', 0, 16, { size: 10, weight: 700, fill: '#fff' });
    ctx.restore();
  }
  function drawCrook(ctx, x, y, rot) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.strokeStyle = C(OUT); ctx.lineWidth = 13; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0, 150); ctx.lineTo(0, -150); ctx.arc(-26, -150, 26, 0, Math.PI, true); ctx.stroke();
    ctx.strokeStyle = C('#a0703c'); ctx.lineWidth = 7;
    ctx.beginPath(); ctx.moveTo(0, 150); ctx.lineTo(0, -150); ctx.arc(-26, -150, 26, 0, Math.PI, true); ctx.stroke();
    ctx.restore();
  }
  A.crook = drawCrook;
  A.remote = drawRemote;
  A.cup = drawCup;

  // ------------------------------------------------------------------ humans (city)
  A.human = function (ctx, o) {
    const s = o.s ?? 1, dir = o.dir ?? 1;
    ctx.save();
    ctx.translate(o.x, o.y);
    ctx.scale(s, s);
    const walking = o.walk !== undefined && o.walk !== null;
    const ph = walking ? o.walk : 0;
    const bob = walking ? -Math.abs(Math.sin(ph)) * 5 : 0;
    const outline = C(OUT);
    ctx.fillStyle = 'rgba(0,0,0,0.2)';
    ellipse(ctx, 0, 2, 40, 8); ctx.fill();
    ctx.lineCap = 'round';
    // legs
    for (const k of [1, -1]) {
      const a = walking ? Math.sin(ph) * 0.45 * k : 0;
      ctx.save(); ctx.translate(0, -78 + bob); ctx.rotate(a);
      ctx.strokeStyle = outline; ctx.lineWidth = 22; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 76); ctx.stroke();
      ctx.strokeStyle = C(o.pants || '#3b3f52'); ctx.lineWidth = 15; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 74); ctx.stroke();
      ctx.restore();
    }
    // back arm
    const arm = (k, front) => {
      const a = walking ? -Math.sin(ph) * 0.5 * k : 0.1;
      ctx.save(); ctx.translate(0, -150 + bob); ctx.rotate(a);
      ctx.strokeStyle = outline; ctx.lineWidth = 18; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(4 * dir, 62); ctx.stroke();
      ctx.strokeStyle = C(front ? o.shirt || '#6c7a96' : mix(o.shirt || '#6c7a96', '#000000', 0.15)); ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(4 * dir, 60); ctx.stroke();
      if (front && o.bag) { rrect(ctx, 4 * dir - 18, 58, 36, 26, 4); ctx.fillStyle = C('#5a3a22'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 3; ctx.stroke(); }
      if (front && o.token) A.token(ctx, 4 * dir, 66, 11, o.t ? o.t * 4 : 0);
      ctx.restore();
    };
    arm(-1, false);
    // torso
    rrect(ctx, -26, -164 + bob, 52, 92, 18);
    ctx.fillStyle = outline; ctx.fill();
    rrect(ctx, -22, -160 + bob, 44, 86, 15);
    ctx.fillStyle = C(o.shirt || '#6c7a96'); ctx.fill();
    if (o.tie) { ctx.fillStyle = C('#b03a3a'); ctx.beginPath(); ctx.moveTo(-5, -158 + bob); ctx.lineTo(5, -158 + bob); ctx.lineTo(7, -120 + bob); ctx.lineTo(0, -112 + bob); ctx.lineTo(-7, -120 + bob); ctx.fill(); }
    arm(1, true);
    // head
    const hy = -192 + bob;
    circle(ctx, 0, hy, 28); ctx.fillStyle = outline; ctx.fill();
    circle(ctx, 0, hy, 24); ctx.fillStyle = C(o.skin || '#e0b08c'); ctx.fill();
    ctx.fillStyle = C(o.hair || '#3a2a20');
    ctx.beginPath(); ctx.arc(0, hy - 4, 25, Math.PI * 1.05, Math.PI * 1.95); ctx.fill();
    const face = o.face ?? 0; // 0 = profile toward dir, 1 = facing camera
    ctx.fillStyle = '#1a1210';
    if (face > 0.5) {
      circle(ctx, -8, hy + 2, 3.2); ctx.fill();
      circle(ctx, 8, hy + 2, 3.2); ctx.fill();
      ctx.strokeStyle = '#1a1210'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(-6, hy + 13); ctx.lineTo(6, hy + 13); ctx.stroke();
    } else {
      circle(ctx, 12 * dir, hy + 1, 3.2); ctx.fill();
      ctx.strokeStyle = '#1a1210'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(10 * dir, hy + 12); ctx.lineTo(18 * dir, hy + 12); ctx.stroke();
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ bubbles & icons
  A.bubble = function (ctx, x, y, w, h, o = {}) {
    const k = o.k ?? 1;
    if (k <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(k, k);
    ctx.globalAlpha *= clamp(k * 1.5);
    const fill = o.fill || '#fffdf6';
    if (o.thought) {
      for (const [cx, cy, r] of [[-w * 0.3, h / 2 + 22, 11], [-w * 0.38, h / 2 + 46, 7]]) {
        circle(ctx, cx, cy, r + 3); ctx.fillStyle = OUT; ctx.fill();
        circle(ctx, cx, cy, r); ctx.fillStyle = fill; ctx.fill();
      }
      const pts = [];
      for (let i = 0; i < 10; i++) {
        const a = (i / 10) * TAU;
        pts.push([Math.cos(a) * w * 0.42, Math.sin(a) * h * 0.38, Math.min(w, h) * 0.24]);
      }
      pts.push([0, 0, Math.min(w, h) * 0.45]);
      blob(ctx, pts, 4); ctx.fillStyle = OUT; ctx.fill();
      blob(ctx, pts, 0); ctx.fillStyle = fill; ctx.fill();
    } else if (o.burst) {
      ctx.beginPath();
      const n = 14;
      for (let i = 0; i <= n * 2; i++) {
        const a = (i / (n * 2)) * TAU;
        const r = i % 2 ? 0.72 : 1;
        ctx.lineTo(Math.cos(a) * w * 0.5 * r, Math.sin(a) * h * 0.5 * r);
      }
      ctx.closePath();
      ctx.fillStyle = fill; ctx.fill();
      ctx.strokeStyle = OUT; ctx.lineWidth = 5; ctx.lineJoin = 'round'; ctx.stroke();
    } else {
      rrect(ctx, -w / 2, -h / 2, w, h, 26);
      ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 5; ctx.stroke();
      const tx = o.tail ?? -w * 0.25;
      ctx.beginPath(); ctx.moveTo(tx - 16, h / 2 - 3); ctx.lineTo(tx + (o.tailDx ?? -20), h / 2 + 34); ctx.lineTo(tx + 16, h / 2 - 3);
      ctx.fillStyle = fill; ctx.fill();
      ctx.beginPath(); ctx.moveTo(tx - 16, h / 2); ctx.lineTo(tx + (o.tailDx ?? -20), h / 2 + 34); ctx.lineTo(tx + 16, h / 2);
      ctx.stroke();
    }
    if (o.text) text(ctx, o.text, 0, 2, { size: o.size || 42, weight: 700, fill: o.color || '#2b1d16', font: o.font });
    if (o.draw) o.draw(ctx);
    ctx.restore();
  };

  A.heart = function (ctx, x, y, s, alpha = 1) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.globalAlpha *= alpha;
    ctx.beginPath();
    ctx.moveTo(0, 10);
    ctx.bezierCurveTo(-30, -12, -14, -34, 0, -18);
    ctx.bezierCurveTo(14, -34, 30, -12, 0, 10);
    ctx.fillStyle = '#ff4f7b'; ctx.fill();
    ctx.strokeStyle = OUT; ctx.lineWidth = 3.5; ctx.stroke();
    ctx.restore();
  };

  A.mark = function (ctx, ch, x, y, s, alpha = 1, color = '#fff') {
    text(ctx, ch, x, y, { size: 64 * s, font: FONT_TITLE, weight: 400, fill: color, stroke: OUT, lw: 8 * s, alpha });
  };

  A.zzz = function (ctx, x, y, t, alpha = 1) {
    for (let i = 0; i < 3; i++) {
      const k = ((t * 0.6 + i / 3) % 1);
      text(ctx, 'Z', x + k * 60 + Math.sin(k * 6) * 8, y - k * 120, { size: 26 + k * 30, font: FONT_TITLE, weight: 400, fill: '#fff', stroke: OUT, lw: 6, alpha: alpha * Math.sin(k * Math.PI) });
    }
  };

  A.label = function (ctx, str, x, y, tx, ty, k = 1) {
    if (k <= 0) return;
    ctx.save();
    ctx.globalAlpha *= clamp(k);
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 5; ctx.lineCap = 'round';
    ctx.setLineDash([2, 12]);
    ctx.beginPath(); ctx.moveTo(x, y + 26); ctx.lineTo(tx, ty); ctx.stroke();
    ctx.setLineDash([]);
    ctx.font = `400 46px ${FONT_TITLE}`;
    const w = ctx.measureText(str).width + 50;
    ctx.translate(x, y);
    ctx.scale(lerp(0.6, 1, F.E.back(clamp(k))), lerp(0.6, 1, F.E.back(clamp(k))));
    rrect(ctx, -w / 2, -34, w, 64, 14);
    ctx.fillStyle = '#2b1d16'; ctx.fill();
    text(ctx, str, 0, 2, { size: 46, font: FONT_TITLE, weight: 400, fill: '#ffd166', ls: 2 });
    ctx.restore();
  };
})();
