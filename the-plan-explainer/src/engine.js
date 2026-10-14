/* THE PLAN — a tiny deterministic canvas animation engine.
 *
 * Every frame is a pure function of time t (seconds): nothing depends on wall
 * clock or previous frames. That lets the browser preview and the frame-by-frame
 * renderer (tools/render.mjs) produce identical pictures.
 */
(function () {
  'use strict';

  const W = 1920, H = 1080;
  const TL = window.TIMELINE;

  // ------------------------------------------------------------------ timeline
  function L(id) {
    const l = TL.lines[id];
    if (!l) throw new Error('unknown line id ' + id + ' (check script.json)');
    return l;
  }
  const Ls = (id) => L(id).start;
  const Le = (id) => L(id).end;
  const normW = (s) => s.toLowerCase().replace(/[^a-z0-9*]/g, '');
  function findWord(id, word, n) {
    const target = normW(word);
    let k = 0;
    for (const w of L(id).words) {
      if (normW(w.w).startsWith(target) && k++ === n) return w;
    }
    console.warn('word not found:', id, word);
    return { s: L(id).start, e: L(id).end };
  }
  /** Time the nth occurrence of `word` starts in line `id`. */
  const Wd = (id, word, n = 0) => findWord(id, word, n).s;
  /** Time it ends. */
  const WdE = (id, word, n = 0) => findWord(id, word, n).e;

  /** Which voice is talking at t, and how open its mouth is (0..1). */
  function mouthOf(who, t) {
    for (const id of TL.order) {
      const l = TL.lines[id];
      if (l.who !== who || t < l.start || t >= l.end) continue;
      const f = (t - l.start) * TL.fps;
      const i = Math.floor(f), k = f - i;
      const a = l.mouth[i] || 0, b = l.mouth[i + 1] || 0;
      return (a + (b - a) * k) / 100;
    }
    return 0;
  }
  const speaking = (who, t) => TL.order.some((id) => {
    const l = TL.lines[id];
    return l.who === who && t >= l.start && t < l.end;
  });

  // ------------------------------------------------------------------ math
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const E = {
    linear: (k) => k,
    inQuad: (k) => k * k,
    outQuad: (k) => 1 - (1 - k) * (1 - k),
    inOutQuad: (k) => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2),
    inCubic: (k) => k * k * k,
    outCubic: (k) => 1 - Math.pow(1 - k, 3),
    inOutCubic: (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    outQuart: (k) => 1 - Math.pow(1 - k, 4),
    inBack: (k) => 2.70158 * k * k * k - 1.70158 * k * k,
    outBack: (k) => 1 + 2.70158 * Math.pow(k - 1, 3) + 1.70158 * Math.pow(k - 1, 2),
    outElastic: (k) => (k === 0 || k === 1 ? k : Math.pow(2, -10 * k) * Math.sin((k * 10 - 0.75) * (2 * Math.PI) / 3) + 1),
  };
  /** 0..1 progress of t through [t0, t0+d]. */
  const prog = (t, t0, d) => (d <= 0 ? (t >= t0 ? 1 : 0) : clamp((t - t0) / d));
  /** Eased progress. */
  const tw = (t, t0, d, ease = E.outCubic) => ease(prog(t, t0, d));
  /** Fade in at t0, fade out to be gone by t1. */
  const env = (t, t0, t1, fin = 0.3, fout = 0.3) => Math.min(prog(t, t0, fin), 1 - prog(t, t1 - fout, fout));
  /** Pop-in scale with overshoot. */
  const pop = (t, t0, d = 0.45) => (t < t0 ? 0 : E.outBack(prog(t, t0, d)));

  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let r = Math.imul(a ^ (a >>> 15), 1 | a);
      r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ------------------------------------------------------------------ colour
  // DRAIN (0..1) greys out the "world" as the years go by. Money and The System
  // are drawn with M(), which ignores it, so they stay vivid.
  const P = {
    cream: '#FFF4E6', cream2: '#FCE9D2', ink: '#1F2140', inkSoft: '#5B5E7A',
    coral: '#FF6B6B', pink: '#FF9EB5', pinkD: '#F27A9B', yellow: '#FFD166',
    teal: '#2EC4B6', blue: '#4D96FF', blueD: '#3B7DDD', purple: '#9B5DE5',
    green: '#1FBF5F', greenD: '#12924A', greenL: '#7BE3A4', gold: '#F5B83D', goldD: '#D99A1E',
    red: '#E63946', white: '#FFFFFF', gray: '#9CA3AF', night: '#121417', paper: '#F6F1E7',
  };
  let DRAIN = 0;
  const rgbCache = {};
  function rgb(hex) {
    if (rgbCache[hex]) return rgbCache[hex];
    const h = hex.replace('#', '');
    const v = [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    return (rgbCache[hex] = v);
  }
  /** World colour (fades with DRAIN). */
  function C(hex, a = 1) {
    const [r, g, b] = rgb(hex);
    const y = 0.3 * r + 0.59 * g + 0.11 * b;
    const k = DRAIN;
    return `rgba(${Math.round(r + (y - r) * k)},${Math.round(g + (y - g) * k)},${Math.round(b + (y - b) * k)},${a})`;
  }
  /** Money / System colour (never fades). */
  function M(hex, a = 1) {
    const [r, g, b] = rgb(hex);
    return `rgba(${r},${g},${b},${a})`;
  }
  function mix(h1, h2, k) {
    const a = rgb(h1), b = rgb(h2);
    const c = a.map((v, i) => Math.round(v + (b[i] - v) * clamp(k)));
    return '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');
  }

  // ------------------------------------------------------------------ drawing
  const FONTS = {
    round: '"Fredoka", "Inter", sans-serif',
    sans: '"Inter", sans-serif',
    serif: '"DM Serif Display", Georgia, serif',
    mono: '"IBM Plex Mono", "DejaVu Sans Mono", monospace',
    hand: '"Caveat", cursive',
    emoji: '"Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", sans-serif',
  };
  function setFont(ctx, size, weight = 600, fam = 'round') {
    ctx.font = `${weight} ${size}px ${FONTS[fam]}`;
  }
  function txt(ctx, s, x, y, o = {}) {
    ctx.save();
    setFont(ctx, o.size || 40, o.weight || 600, o.font || 'round');
    ctx.textAlign = o.align || 'center';
    ctx.textBaseline = o.baseline || 'middle';
    ctx.letterSpacing = (o.spacing || 0) + 'px';
    if (o.alpha != null) ctx.globalAlpha *= o.alpha;
    if (o.stroke) {
      ctx.lineWidth = o.stroke;
      ctx.strokeStyle = o.strokeColor || C(P.white);
      ctx.lineJoin = 'round';
      ctx.strokeText(s, x, y);
    }
    ctx.fillStyle = o.color || C(P.ink);
    ctx.fillText(s, x, y);
    ctx.restore();
  }
  function measure(ctx, s, size, weight = 600, fam = 'round', spacing = 0) {
    ctx.save();
    setFont(ctx, size, weight, fam);
    ctx.letterSpacing = spacing + 'px';
    const w = ctx.measureText(s).width;
    ctx.restore();
    return w;
  }
  function rr(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  function card(ctx, x, y, w, h, o = {}) {
    ctx.save();
    if (o.shadow !== false) {
      ctx.shadowColor = 'rgba(31,33,64,' + (o.shadowA != null ? o.shadowA : 0.16) + ')';
      ctx.shadowBlur = o.blur != null ? o.blur : 30;
      ctx.shadowOffsetY = o.dy != null ? o.dy : 10;
    }
    rr(ctx, x, y, w, h, o.r != null ? o.r : 26);
    ctx.fillStyle = o.fill || C(P.white);
    ctx.fill();
    ctx.restore();
    if (o.stroke) {
      ctx.save();
      rr(ctx, x, y, w, h, o.r != null ? o.r : 26);
      ctx.lineWidth = o.lw || 4;
      ctx.strokeStyle = o.stroke;
      if (o.dash) ctx.setLineDash(o.dash);
      ctx.stroke();
      ctx.restore();
    }
  }
  function circle(ctx, x, y, r, fill) {
    ctx.beginPath();
    ctx.arc(x, y, Math.max(0, r), 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
  }
  function ellipse(ctx, x, y, rx, ry, fill, rot = 0) {
    ctx.beginPath();
    ctx.ellipse(x, y, Math.max(0, rx), Math.max(0, ry), rot, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
  }
  /** Run fn with ctx translated to (x, y), scaled by s, rotated by r. */
  function at(ctx, x, y, s, r, fn) {
    ctx.save();
    ctx.translate(x, y);
    if (r) ctx.rotate(r);
    if (s !== 1) ctx.scale(s, s);
    fn();
    ctx.restore();
  }
  function alpha(ctx, a, fn) {
    if (a <= 0.001) return;
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    fn();
    ctx.restore();
  }
  /** Colour emoji glyph, greyed with the world unless o.money.
   *  Glyphs are pre-rendered once per grey level: a canvas filter on every
   *  draw call is far too slow when a hundred hobbies pile up. */
  const EMOJI_REF = 128;
  const emojiCache = new Map();
  function emojiBitmap(ch, level) {
    const key = ch + '|' + level;
    let c = emojiCache.get(key);
    if (c) return c;
    c = document.createElement('canvas');
    c.width = c.height = Math.ceil(EMOJI_REF * 1.5);
    const g = c.getContext('2d');
    if (level > 0) g.filter = `saturate(${(1 - level).toFixed(3)})`;
    g.font = `${EMOJI_REF}px ${FONTS.emoji}`;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillStyle = '#000';
    g.fillText(ch, c.width / 2, c.height / 2 + EMOJI_REF * 0.04);
    emojiCache.set(key, c);
    return c;
  }
  function emoji(ctx, ch, x, y, size, o = {}) {
    if (size <= 0.5) return;
    const level = o.money ? 0 : Math.round(DRAIN * 25) / 25;
    const bmp = emojiBitmap(ch, level);
    const w = (bmp.width * size) / EMOJI_REF;
    ctx.save();
    if (o.alpha != null) ctx.globalAlpha *= o.alpha;
    ctx.imageSmoothingQuality = 'high';
    ctx.translate(x, y);
    if (o.rot) ctx.rotate(o.rot);
    ctx.drawImage(bmp, -w / 2, -w / 2, w, w);
    ctx.restore();
  }
  function fill(ctx, color) {
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, W, H);
  }
  function check(ctx, x, y, s, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    circle(ctx, 0, 0, 20, color);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(-9, 1);
    ctx.lineTo(-3, 8);
    ctx.lineTo(10, -7);
    ctx.stroke();
    ctx.restore();
  }
  function cross(ctx, x, y, s, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    circle(ctx, 0, 0, 20, color);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(-7, -7); ctx.lineTo(7, 7);
    ctx.moveTo(7, -7); ctx.lineTo(-7, 7);
    ctx.stroke();
    ctx.restore();
  }
  /** Rubber stamp text: thick rotated frame. */
  function stamp(ctx, label, x, y, k, o = {}) {
    if (k <= 0) return;
    const s = lerp(1.9, 1, E.outCubic(clamp(k * 1.6))) * (o.scale || 1);
    const a = clamp(k * 3);
    const size = o.size || 64;
    const color = o.color || M(P.red);
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(o.rot != null ? o.rot : -0.12);
    ctx.scale(s, s);
    ctx.globalAlpha *= a * (o.alpha != null ? o.alpha : 0.92);
    const lines = label.split('\n');
    setFont(ctx, size, 700, o.font || 'round');
    ctx.letterSpacing = (o.spacing != null ? o.spacing : 4) + 'px';
    const w = Math.max(...lines.map((l) => ctx.measureText(l).width)) + size * 0.9;
    const h = lines.length * size * 1.05 + size * 0.5;
    rr(ctx, -w / 2, -h / 2, w, h, size * 0.22);
    ctx.lineWidth = size * 0.12;
    ctx.strokeStyle = color;
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    lines.forEach((l, i) => ctx.fillText(l, 0, (i - (lines.length - 1) / 2) * size * 1.05 + size * 0.04));
    ctx.restore();
  }
  /** Soft drifting blobs behind corporate scenes. */
  function blobs(ctx, t, seed, colors, a = 0.5) {
    const r = rng(seed);
    for (let i = 0; i < 9; i++) {
      const bx = r() * W, by = r() * H, br = 80 + r() * 220, sp = 0.05 + r() * 0.12, ph = r() * 6.28;
      const c = colors[i % colors.length];
      circle(ctx, bx + Math.sin(t * sp + ph) * 60, by + Math.cos(t * sp * 1.3 + ph) * 40, br, C(c, a * (0.16 + r() * 0.22)));
    }
  }
  function money(v) {
    return '$' + Math.round(v).toLocaleString('en-US');
  }

  // ------------------------------------------------------------------ characters
  const SKIN = '#E9B48C', SKIN_D = '#CF956A', HAIR = '#3A2A22', HAIR_OLD = '#D4D4D4',
    SHIRT = '#4D96FF', SHIRT_D = '#3B7DDD', PANTS = '#2E3A66', SHOE = '#1F2140';

  /**
   * "You": feet at (x, y). o = { t, age 0..1, pose, mood, mouth 0..1, tag, prop, look }
   * poses: stand, wave, phone, lift, hold, shrug, sit, slump
   */
  function drawYou(ctx, x, y, s, o = {}) {
    const t = o.t || 0;
    const age = o.age || 0;
    const pose = o.pose || 'stand';
    const mood = o.mood || 'happy';
    const mouth = o.mouth || 0;
    const sit = pose === 'sit';
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s * (o.flip ? -1 : 1), s);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const breathe = Math.sin(t * 2.1) * 2.5;
    const hipY = sit ? -150 : -140;

    // legs + shoes
    ctx.strokeStyle = C(PANTS);
    ctx.lineWidth = 32;
    if (sit) {
      [-22, 22].forEach((dx) => {
        ctx.beginPath();
        ctx.moveTo(dx, hipY);
        ctx.lineTo(dx + 100, hipY + 2);
        ctx.lineTo(dx + 104, -22);
        ctx.stroke();
        ellipse(ctx, dx + 118, -10, 30, 13, C(SHOE));
      });
    } else {
      [-22, 22].forEach((dx) => {
        ctx.beginPath();
        ctx.moveTo(dx, hipY);
        ctx.lineTo(dx * 1.15, -22);
        ctx.stroke();
        ellipse(ctx, dx * 1.15 + 8, -10, 30, 13, C(SHOE));
      });
    }

    // body pivots at the hips; age adds a hunch
    ctx.save();
    ctx.translate(0, hipY);
    ctx.rotate((sit ? 0.05 : 0.02) + age * 0.07 + (pose === 'slump' ? 0.08 : 0));
    const torsoTop = -195 + breathe * 0.4;

    // arms behind torso for most poses
    const sh = { l: [-60, torsoTop + 34], r: [60, torsoTop + 34] };
    const hands = armPose(pose, t, torsoTop, o);
    const drawArm = (side) => {
      const [sx, sy] = sh[side];
      const [hx, hy] = hands[side];
      const ex = (sx + hx) / 2 + (side === 'l' ? -18 : 18), ey = (sy + hy) / 2 + 10;
      ctx.strokeStyle = C(SHIRT_D);
      ctx.lineWidth = 26;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.quadraticCurveTo(ex, ey, hx, hy);
      ctx.stroke();
      circle(ctx, hx, hy, 15, C(SKIN));
    };

    // torso
    rr(ctx, -74, torsoTop, 148, -torsoTop + 14, 58);
    ctx.fillStyle = C(SHIRT);
    ctx.fill();
    // collar
    ctx.beginPath();
    ctx.moveTo(-22, torsoTop + 2);
    ctx.lineTo(0, torsoTop + 26);
    ctx.lineTo(22, torsoTop + 2);
    ctx.strokeStyle = C(SHIRT_D);
    ctx.lineWidth = 6;
    ctx.stroke();

    // name tag
    if (o.tag !== false) {
      ctx.save();
      ctx.translate(-30, torsoTop + 50);
      ctx.rotate(-0.06);
      rr(ctx, 0, 0, 70, 48, 6);
      ctx.fillStyle = C('#FFFFFF');
      ctx.fill();
      rr(ctx, 0, 0, 70, 16, 6);
      ctx.fillStyle = C(P.red);
      ctx.fill();
      ctx.fillRect(0, 9, 70, 7);
      txt(ctx, 'HELLO', 35, 8.5, { size: 10, weight: 800, font: 'sans', color: '#fff', spacing: 1 });
      txt(ctx, 'YOU', 35, 33, { size: 25, weight: 700, font: 'hand', color: C(P.ink) });
      ctx.restore();
    }

    drawArm('l');
    drawArm('r');
    if (o.prop) drawProp(ctx, o.prop, hands.r[0], hands.r[1], t);

    // head
    const tiltDown = pose === 'phone' ? 0.1 : 0;
    ctx.save();
    ctx.translate(0, torsoTop - 66);
    ctx.rotate(tiltDown + (o.headTilt || 0));
    circle(ctx, -68, 6, 14, C(SKIN_D));
    circle(ctx, 68, 6, 14, C(SKIN_D));
    circle(ctx, 0, 0, 72, C(SKIN));
    // hair
    const hairCol = mix(HAIR, HAIR_OLD, age);
    ctx.save();
    ctx.beginPath();
    ctx.arc(0, 0, 76, 0, Math.PI * 2);
    ctx.clip();
    ctx.beginPath();
    const recede = age * 14;
    ctx.moveTo(-80, -6 - recede * 0.3);
    ctx.quadraticCurveTo(-60, -40 - recede, -10, -44 - recede);
    ctx.quadraticCurveTo(30, -30 - recede, 82, -18);
    ctx.lineTo(82, -90);
    ctx.lineTo(-82, -90);
    ctx.closePath();
    ctx.fillStyle = C(hairCol);
    ctx.fill();
    ctx.restore();
    // eyes
    const blink = (t + (o.blinkOffset || 0)) % 3.9 < 0.13 ? 0.15 : 1;
    const lx = (o.look || 0) * 6;
    const eyeY = 2 + (pose === 'phone' ? 6 : 0);
    ellipse(ctx, -25 + lx, eyeY, 7.5, 9.5 * blink, C(P.ink));
    ellipse(ctx, 25 + lx, eyeY, 7.5, 9.5 * blink, C(P.ink));
    // brows
    ctx.strokeStyle = C(mix(HAIR, HAIR_OLD, age));
    ctx.lineWidth = 6;
    const browTilt = mood === 'worried' || mood === 'sad' ? 6 : mood === 'tired' ? 2 : 0;
    ctx.beginPath();
    ctx.moveTo(-36, -18 + browTilt * 0.2);
    ctx.lineTo(-15, -20 - browTilt);
    ctx.moveTo(36, -18 + browTilt * 0.2);
    ctx.lineTo(15, -20 - browTilt);
    ctx.stroke();
    // eyelids when tired / old
    if (mood === 'tired' || mood === 'sad') {
      ctx.fillStyle = C(SKIN);
      ctx.fillRect(-36, eyeY - 12, 22, 9);
      ctx.fillRect(14, eyeY - 12, 22, 9);
    }
    // mouth
    ctx.strokeStyle = C('#7A3B2E');
    ctx.lineWidth = 6;
    if (mouth > 0.05) {
      ellipse(ctx, 0, 33, 13 + mouth * 3, 3 + mouth * 13, C('#7A2E2E'));
    } else if (mood === 'happy') {
      ctx.beginPath();
      ctx.arc(0, 22, 20, 0.2 * Math.PI, 0.8 * Math.PI);
      ctx.stroke();
    } else if (mood === 'sad') {
      ctx.beginPath();
      ctx.arc(0, 48, 17, 1.2 * Math.PI, 1.8 * Math.PI);
      ctx.stroke();
    } else if (mood === 'worried') {
      ellipse(ctx, 0, 36, 7, 8, C('#7A2E2E'));
    } else {
      ctx.beginPath();
      ctx.moveTo(-14, 36);
      ctx.lineTo(14, 36);
      ctx.stroke();
    }
    // glasses later in life
    if (age > 0.7) {
      ctx.globalAlpha *= clamp((age - 0.7) / 0.1);
      ctx.strokeStyle = C('#4B4B4B');
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(-25, eyeY, 16, 0, Math.PI * 2);
      ctx.moveTo(41, eyeY);
      ctx.arc(25, eyeY, 16, 0, Math.PI * 2);
      ctx.moveTo(-9, eyeY);
      ctx.lineTo(9, eyeY);
      ctx.stroke();
    }
    ctx.restore(); // head
    ctx.restore(); // body
    ctx.restore();
  }

  function armPose(pose, t, top, o) {
    const down = { l: [-88, top + 150], r: [88, top + 150] };
    switch (pose) {
      case 'wave': {
        const a = Math.sin(t * 9) * 14;
        return { l: down.l, r: [128 + a * 0.3, top - 38 + Math.abs(a) * 0.4] };
      }
      case 'phone':
        return { l: [-36, top + 92], r: [26, top + 88] };
      case 'lift': {
        const k = (Math.sin(t * 4.2) + 1) / 2;
        return { l: down.l, r: [104, lerp(top + 120, top + 10, k)] };
      }
      case 'hold':
        return { l: down.l, r: [118, top + 96] };
      case 'shrug':
        return { l: [-122, top + 40], r: [122, top + 40] };
      case 'sit':
        return { l: [-30, top + 168], r: [60, top + 150] };
      case 'slump':
        return { l: [-70, top + 172], r: [70, top + 172] };
      default:
        return down;
    }
  }

  function drawProp(ctx, prop, hx, hy, t) {
    if (prop === 'phone') {
      ctx.save();
      ctx.translate(hx + 2, hy - 30);
      rr(ctx, -24, -40, 48, 82, 9);
      ctx.fillStyle = C('#22243A');
      ctx.fill();
      rr(ctx, -19, -33, 38, 66, 5);
      ctx.fillStyle = C('#FF8FAB');
      ctx.fill();
      emoji(ctx, '❤️', 0, -2, 22);
      ctx.restore();
    } else if (prop === 'dumbbell') {
      ctx.save();
      ctx.translate(hx, hy);
      ctx.fillStyle = C('#444A63');
      ctx.fillRect(-46, -5, 92, 10);
      rr(ctx, -56, -22, 18, 44, 5); ctx.fill();
      rr(ctx, 38, -22, 18, 44, 5); ctx.fill();
      ctx.restore();
    } else if (prop === 'ticket') {
      ctx.save();
      ctx.translate(hx + 10, hy - 18);
      ctx.rotate(-0.25);
      rr(ctx, -34, -22, 68, 44, 5);
      ctx.fillStyle = C('#FFF7D6');
      ctx.fill();
      txt(ctx, '4812', 0, 2, { size: 20, weight: 600, font: 'mono', color: C(P.ink) });
      ctx.restore();
    } else {
      emoji(ctx, prop, hx + 10, hy - 26, 64);
    }
  }

  const PIG = '#FF9EB5', PIG_D = '#F27A9B', PIG_DD = '#C9506F', TIE = '#2B59C3', TIE_D = '#1D3F91';

  /**
   * The System: a piggy bank in a tie. Feet at (x, y). Always full colour.
   * o = { t, mouth, pose: idle|wave|point|thumbs|shrug, blink, squash, look }
   */
  function drawPig(ctx, x, y, s, o = {}) {
    const t = o.t || 0;
    const mouth = o.mouth || 0;
    const pose = o.pose || 'idle';
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s * (o.flip ? -1 : 1), s);
    if (o.tilt) ctx.rotate(o.tilt);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const hop = o.still ? 0 : Math.abs(Math.sin(t * 3.1)) * 5 + mouth * 4;
    const sq = 1 + (o.squash || 0);

    // legs
    rr(ctx, -62, -46, 38, 46, 12); ctx.fillStyle = M(PIG_D); ctx.fill();
    rr(ctx, 24, -46, 38, 46, 12); ctx.fill();
    ellipse(ctx, -43, -4, 19, 7, M(PIG_DD));
    ellipse(ctx, 43, -4, 19, 7, M(PIG_DD));

    ctx.translate(0, -hop);
    ctx.scale(1 / sq, sq);

    // arms (behind body)
    const armL = [-104, -120], armR = [104, -120];
    let hl = [-128, -66], hr = [128, -66];
    if (pose === 'wave') { const a = Math.sin(t * 10) * 16; hl = [-128, -66]; hr = [150 + a * 0.4, -232 + Math.abs(a) * 0.3]; }
    if (pose === 'point') hr = [178, -150];
    if (pose === 'pointL') hl = [-178, -150];
    if (pose === 'thumbs') hr = [154, -200];
    if (pose === 'shrug') { hl = [-160, -178]; hr = [160, -178]; }
    ctx.strokeStyle = M(PIG_D);
    ctx.lineWidth = 30;
    [[armL, hl], [armR, hr]].forEach(([a, h]) => {
      ctx.beginPath();
      ctx.moveTo(a[0], a[1]);
      ctx.lineTo(h[0], h[1]);
      ctx.stroke();
      circle(ctx, h[0], h[1], 19, M(PIG_D));
    });
    if (pose === 'thumbs') {
      rr(ctx, hr[0] - 7, hr[1] - 44, 15, 32, 7);
      ctx.fillStyle = M(PIG_D);
      ctx.fill();
    }

    // ears
    ctx.fillStyle = M(PIG_D);
    [[-1, 1], [1, 1]].forEach(([d]) => {
      ctx.beginPath();
      ctx.moveTo(d * 46, -226);
      ctx.lineTo(d * 98, -262 + Math.sin(t * 2 + d) * 3);
      ctx.lineTo(d * 92, -192);
      ctx.closePath();
      ctx.fill();
    });
    // body
    circle(ctx, 0, -132, 120, M(PIG));
    ctx.save();
    ctx.beginPath();
    ctx.arc(0, -132, 120, 0, Math.PI * 2);
    ctx.clip();
    ellipse(ctx, 18, -40, 140, 50, M(PIG_D, 0.45));
    ctx.restore();
    // coin slot
    rr(ctx, -34, -252, 68, 11, 5);
    ctx.fillStyle = M('#8E3552');
    ctx.fill();
    // shine
    ellipse(ctx, -58, -192, 30, 13, M('#FFFFFF', 0.5), -0.7);
    // eyes
    const blink = (t + 1.3) % 3.4 < 0.12 ? 0.12 : 1;
    const lx = (o.look || 0) * 5;
    ellipse(ctx, -40 + lx, -170, 10, 13 * blink, M(P.ink));
    ellipse(ctx, 40 + lx, -170, 10, 13 * blink, M(P.ink));
    circle(ctx, -37 + lx, -175, 3.2 * blink, M('#FFFFFF'));
    circle(ctx, 43 + lx, -175, 3.2 * blink, M('#FFFFFF'));
    // cheeks
    circle(ctx, -78, -122, 17, M(PIG_D, 0.55));
    circle(ctx, 78, -122, 17, M(PIG_D, 0.55));
    // snout
    ellipse(ctx, 0, -128, 42, 30, M(PIG_D));
    ellipse(ctx, -14, -128, 6.5, 10, M('#A83A5E'));
    ellipse(ctx, 14, -128, 6.5, 10, M('#A83A5E'));
    // mouth
    if (mouth > 0.04) {
      ellipse(ctx, 0, -78, 20 + mouth * 4, 4 + mouth * 15, M('#7A1E3E'));
      ellipse(ctx, 0, -72 + mouth * 6, 10, 4 + mouth * 5, M('#FF7096'));
    } else {
      ctx.strokeStyle = M('#7A1E3E');
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.arc(0, -96, 24, 0.22 * Math.PI, 0.78 * Math.PI);
      ctx.stroke();
    }
    // collar + tie
    ctx.fillStyle = M('#FFFFFF');
    ctx.beginPath();
    ctx.moveTo(-34, -50); ctx.lineTo(0, -38); ctx.lineTo(-12, -24); ctx.closePath(); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(34, -50); ctx.lineTo(0, -38); ctx.lineTo(12, -24); ctx.closePath(); ctx.fill();
    ctx.fillStyle = M(TIE_D);
    ctx.beginPath();
    ctx.moveTo(-10, -44); ctx.lineTo(10, -44); ctx.lineTo(7, -30); ctx.lineTo(-7, -30); ctx.closePath(); ctx.fill();
    ctx.fillStyle = M(TIE);
    ctx.beginPath();
    ctx.moveTo(-7, -30); ctx.lineTo(7, -30); ctx.lineTo(14, 2); ctx.lineTo(0, 16); ctx.lineTo(-14, 2); ctx.closePath(); ctx.fill();
    // tail
    ctx.strokeStyle = M(PIG_D);
    ctx.lineWidth = 7;
    ctx.beginPath();
    ctx.moveTo(116, -100);
    ctx.bezierCurveTo(146, -110, 140, -140, 128, -130);
    ctx.bezierCurveTo(118, -122, 140, -96, 156, -112);
    ctx.stroke();
    ctx.restore();
  }

  function pigBadge(ctx, x, y, k) {
    if (k <= 0) return;
    at(ctx, x, y, E.outBack(clamp(k)), 0, () => {
      const w = 270, h = 54;
      card(ctx, -w / 2, -h / 2, w, h, { fill: M(P.coral), r: 27, shadowA: 0.2 });
      txt(ctx, 'THE SYSTEM', 0, 2, { size: 30, weight: 700, color: '#fff', spacing: 3 });
    });
  }

  /** Glass jar filled with money. Bottom-centre at (x, y). Always full colour. */
  function drawJar(ctx, x, y, w, h, level, o = {}) {
    ctx.save();
    ctx.translate(x, y);
    const t = o.t || 0;
    // glow
    if (o.glow) {
      const g = ctx.createRadialGradient(0, -h / 2, 10, 0, -h / 2, h);
      g.addColorStop(0, M(P.green, 0.35 * o.glow));
      g.addColorStop(1, M(P.green, 0));
      ctx.fillStyle = g;
      ctx.fillRect(-h, -h * 1.5, h * 2, h * 2);
    }
    // contents
    ctx.save();
    rr(ctx, -w / 2 + 8, -h + 40, w - 16, h - 48, 40);
    ctx.clip();
    const fillH = (h - 60) * clamp(level);
    const top = -8 - fillH;
    ctx.fillStyle = M(P.greenD);
    ctx.fillRect(-w / 2, top, w, fillH + 10);
    // bills + coins texture
    const r = rng(7);
    for (let i = 0; i < (level > 0 ? 70 : 0); i++) {
      const bx = (r() - 0.5) * w, by = -8 - r() * (h - 60);
      if (by < top - 6) continue;
      if (r() < 0.55) {
        ctx.save();
        ctx.translate(bx, by);
        ctx.rotate((r() - 0.5) * 0.9);
        rr(ctx, -34, -15, 68, 30, 4);
        ctx.fillStyle = M(r() < 0.5 ? P.green : '#3DDC84');
        ctx.fill();
        circle(ctx, 0, 0, 7, M('#A8F0C6'));
        ctx.restore();
      } else {
        circle(ctx, bx, by, 15, M(P.goldD));
        circle(ctx, bx, by - 2, 15, M(P.gold));
      }
    }
    ctx.restore();
    // overflow pile
    if (level > 1) {
      const over = clamp(level - 1, 0, 1.2);
      const r2 = rng(11);
      for (let i = 0; i < 40 * over; i++) {
        const a = r2() * Math.PI, rad = r2() * w * 0.55;
        circle(ctx, Math.cos(a) * rad, -h + 30 - Math.sin(a) * 40 * over - r2() * 30 * over, 15, M(r2() < 0.5 ? P.gold : P.green));
      }
    }
    // glass
    rr(ctx, -w / 2, -h + 30, w, h - 30, 46);
    ctx.fillStyle = 'rgba(210,235,255,0.18)';
    ctx.fill();
    ctx.lineWidth = 7;
    ctx.strokeStyle = 'rgba(120,150,180,0.85)';
    ctx.stroke();
    ellipse(ctx, -w / 2 + 34, -h / 2, 9, h * 0.28, 'rgba(255,255,255,0.55)');
    // lid
    rr(ctx, -w / 2 + 18, -h + 4, w - 36, 34, 10);
    ctx.fillStyle = M(P.goldD);
    ctx.fill();
    rr(ctx, -w / 2 + 18, -h + 4, w - 36, 14, 8);
    ctx.fillStyle = M(P.gold);
    ctx.fill();
    // label
    if (o.label !== false) {
      ctx.save();
      ctx.translate(0, -h * 0.42);
      ctx.rotate(-0.02);
      rr(ctx, -w * 0.36, -34, w * 0.72, 68, 10);
      ctx.fillStyle = '#FFFDF5';
      ctx.fill();
      txt(ctx, o.labelText || 'RETIREMENT', 0, 2, { size: Math.min(34, w * 0.1), weight: 700, color: M(P.greenD), spacing: 2 });
      ctx.restore();
    }
    ctx.restore();
  }

  /** A simple standing person token used in crowds. */
  function token(ctx, x, y, s, col, o = {}) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    if (o.glow) {
      circle(ctx, 0, -18, 29, o.glowColor || 'rgba(255,209,102,0.25)');
    }
    circle(ctx, 0, -38, 11, col);
    rr(ctx, -13, -24, 26, 30, 11);
    ctx.fillStyle = col;
    ctx.fill();
    ctx.restore();
  }

  // ------------------------------------------------------------------ captions
  const CAPTION = {
    SYS: { label: 'THE SYSTEM', chip: P.coral, now: '#FFB3C6' },
    YOU: { label: 'YOU', chip: P.blue, now: '#FFD166' },
  };
  let captionsOn = true;
  function drawCaptions(ctx, t) {
    if (!captionsOn) return;
    let line = null, page = null, pageEnd = 0;
    for (let li = 0; li < TL.order.length; li++) {
      const l = TL.lines[TL.order[li]];
      const next = TL.lines[TL.order[li + 1]];
      // a line that is cut off vanishes with the cut
      const hold = l.cut != null ? l.end : Math.min(l.end + 0.5, next ? next.start - 0.05 : l.end + 0.5);
      if (t < l.words[0].s - 0.12 || t > hold) continue;
      for (let pi = 0; pi < l.pages.length; pi++) {
        const [i0, i1] = l.pages[pi];
        const ps = l.words[i0].s - 0.12;
        const pe = pi + 1 < l.pages.length ? l.words[l.pages[pi + 1][0]].s - 0.12 : hold;
        if (t >= ps && t < pe) { line = l; page = [i0, i1]; pageEnd = pe; }
      }
    }
    if (!line) return;
    const style = CAPTION[line.who];
    const words = line.words.slice(page[0], page[1]);
    const size = 44;
    const gap = measure(ctx, ' ', size, 600, 'sans');
    const widths = words.map((w) => measure(ctx, w.w, size, 600, 'sans'));
    const total = widths.reduce((a, b) => a + b, 0) + gap * (words.length - 1);
    const boxW = total + 72, boxH = 86;
    const cx = W / 2, cy = 992;
    const a = Math.min(prog(t, words[0].s - 0.12, 0.12), 1 - prog(t, pageEnd - 0.1, 0.1));
    alpha(ctx, a, () => {
      card(ctx, cx - boxW / 2, cy - boxH / 2, boxW, boxH, { fill: 'rgba(22,24,40,0.86)', r: 22, shadowA: 0.25, blur: 20, dy: 6 });
      // speaker chip
      const lw = measure(ctx, style.label, 20, 700, 'round', 2) + 28;
      card(ctx, cx - boxW / 2 + 22, cy - boxH / 2 - 17, lw, 34, { fill: style.chip, r: 17, shadow: false });
      txt(ctx, style.label, cx - boxW / 2 + 22 + lw / 2, cy - boxH / 2 + 1, { size: 20, weight: 700, color: '#fff', spacing: 2 });
      let wx = cx - total / 2;
      words.forEach((w, i) => {
        const said = t >= w.s;
        const now = t >= w.s && t < w.e + 0.05;
        const censored = w.w.includes('*');
        let col = said ? '#FFFFFF' : 'rgba(255,255,255,0.42)';
        if (now) col = style.now;
        if (censored && said) {
          rr(ctx, wx - 4, cy - 26, widths[i] + 8, 50, 6);
          ctx.fillStyle = '#000';
          ctx.fill();
          txt(ctx, w.w, wx, cy + 2, { size: size, weight: 600, font: 'sans', align: 'left', color: '#FFD166' });
        } else {
          txt(ctx, w.w, wx, cy + 2, { size: size, weight: 600, font: 'sans', align: 'left', color: col });
        }
        wx += widths[i] + gap;
      });
    });
  }

  // ------------------------------------------------------------------ scenes / renderer
  const scenes = [];
  const extraCues = [];
  let drainFn = () => 0;

  function scene(def) { scenes.push(def); return def; }

  function transitionClip(ctx, type, k) {
    const e = E.inOutCubic(k);
    ctx.beginPath();
    switch (type) {
      case 'wipe': { // diagonal wipe left -> right
        const x = lerp(-400, W + 400, e);
        ctx.moveTo(-10, -10); ctx.lineTo(x + 200, -10); ctx.lineTo(x - 200, H + 10); ctx.lineTo(-10, H + 10);
        break;
      }
      case 'iris':
        ctx.arc(W / 2, H / 2, lerp(0, 1150, e), 0, Math.PI * 2);
        break;
      case 'up':
        ctx.rect(0, lerp(H, 0, e), W, H);
        break;
      default:
        ctx.rect(0, 0, W, H);
    }
    ctx.clip();
  }

  function renderAt(ctx, t) {
    DRAIN = clamp(drainFn(t));
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.filter = 'none';
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    const active = scenes.filter((s) => t >= s.from() && t < s.to());
    active.forEach((s, i) => {
      ctx.save();
      const local = t - s.from();
      if (i > 0 && s.enter) {
        const k = prog(local, 0, s.enter.dur);
        if (k < 1) {
          if (s.enter.type === 'fade') ctx.globalAlpha = E.inOutQuad(k);
          else transitionClip(ctx, s.enter.type, k);
        }
      }
      s.draw(ctx, t, local);
      ctx.restore();
      if (i > 0 && s.enter && s.enter.type === 'wipe') {
        const k = prog(local, 0, s.enter.dur);
        if (k > 0 && k < 1) {
          // coloured leading edge of the wipe
          const x = lerp(-400, W + 400, E.inOutCubic(k));
          ctx.save();
          ctx.beginPath();
          ctx.moveTo(x + 200, -10); ctx.lineTo(x + 260, -10); ctx.lineTo(x - 140, H + 10); ctx.lineTo(x - 200, H + 10);
          ctx.closePath();
          ctx.fillStyle = M(s.enter.color || P.coral);
          ctx.fill();
          ctx.restore();
        }
      }
    });
    ctx.save();
    drawCaptions(ctx, t);
    ctx.restore();
  }

  function collectCues() {
    const sfx = [], music = [];
    const push = (c) => (c.kind === 'music' ? music : sfx).push(c);
    scenes.forEach((s) => (s.cues ? s.cues() : []).forEach(push));
    extraCues.forEach((f) => f().forEach(push));
    sfx.sort((a, b) => a.t - b.t);
    music.sort((a, b) => a.t0 - b.t0);
    return { duration: TL.duration, fps: TL.fps, sfx, music };
  }
  const sfx = (name, t, gain = 1, extra = {}) => Object.assign({ kind: 'sfx', name, t: +t.toFixed(3), gain }, extra);
  const music = (name, t0, t1, extra = {}) => Object.assign({ kind: 'music', name, t0: +t0.toFixed(3), t1: +t1.toFixed(3) }, extra);

  window.PLAN = {
    W, H, TL, P, E, FONTS,
    L, Ls, Le, Wd, WdE, mouthOf, speaking,
    clamp, lerp, prog, tw, env, pop, rng, mix,
    C, M, setDrain: (f) => (drainFn = f), drain: () => DRAIN,
    setFont, txt, measure, rr, card, circle, ellipse, at, alpha, emoji, fill, check, cross, stamp, blobs, money,
    drawYou, drawPig, pigBadge, drawJar, token,
    scene, renderAt, collectCues, sfx, music, addCues: (f) => extraCues.push(f),
    setCaptions: (on) => (captionsOn = on),
  };
})();
