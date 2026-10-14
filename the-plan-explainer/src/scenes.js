/* THE PLAN — scenes.
 *
 * Every time below is tied to the narration: Ls('id') / Le('id') are when a
 * line starts / ends, Wd('id', 'word') is when a word in it is spoken. Edit the
 * words in script.json, re-run the voice step, and the picture follows.
 */
(function () {
  'use strict';
  const {
    W, H, TL, P, E, Ls, Le, Wd, mouthOf,
    clamp, lerp, prog, tw, env, pop, rng, mix, C, M, setDrain,
    txt, measure, rr, card, circle, at, alpha, emoji, fill, check, cross, stamp, blobs, money,
    drawYou, drawPig, pigBadge, drawJar, token, scene, sfx, music, addCues,
  } = PLAN;

  // ---------------------------------------------------------------- scene boundaries
  const T = {
    money: Ls('s02') - 0.45,
    love: Ls('s07') - 0.4,
    years: Ls('y02') - 0.55,
    wait: Ls('y05') - 0.9,
    lightsOut: Le('s15') + 0.3,
    hold: Ls('y06') - 0.7,
    crowd: Ls('y10') - 0.6,
    pyramid: Ls('s19') - 0.55,
    ending: Ls('y14') - 0.6,
    card: Le('y15') + 0.55,
    cut: Le('s21'),
    end: TL.duration,
  };
  PLAN.T = T;

  // ---------------------------------------------------------------- age + colour drain
  // Age climbs during the years montage; the world loses colour as it does.
  const AGE_KEYS = [
    [Ls('y02'), 25], [Wd('y02', 'twenty'), 26], [Le('y02') + 0.2, 45], [Ls('s12'), 45],
    [Le('s12'), 51], [Le('s13'), 61], [Le('s14') + 0.4, 65],
  ];
  function ageAt(t) {
    if (t <= AGE_KEYS[0][0]) return AGE_KEYS[0][1];
    for (let i = 1; i < AGE_KEYS.length; i++) {
      const [t1, a1] = AGE_KEYS[i], [t0, a0] = AGE_KEYS[i - 1];
      if (t <= t1) return lerp(a0, a1, E.inOutQuad(prog(t, t0, t1 - t0)));
    }
    return AGE_KEYS[AGE_KEYS.length - 1][1];
  }
  setDrain((t) => {
    if (t < T.years) return 0;
    if (t < T.wait + 0.3) return ((ageAt(t) - 25) / 40) * 0.72;
    if (t < T.hold) return 0.86;
    return 0;
  });

  // ---------------------------------------------------------------- shared bits
  const you = (t) => ({ t, mouth: mouthOf('YOU', t) });
  const pigO = (t) => ({ t, mouth: mouthOf('SYS', t) });

  function chip(ctx, label, x, y, k, color, o = {}) {
    if (k <= 0) return;
    const size = o.size || 30;
    const w = measure(ctx, label, size, 700, 'round', 3) + size * 1.4;
    const h = size * 1.75;
    at(ctx, x + w / 2, y, E.outBack(clamp(k)), 0, () => {
      card(ctx, -w / 2, -h / 2, w, h, { fill: color, r: h / 2, shadowA: 0.12, blur: 14, dy: 5 });
      txt(ctx, label, 0, 2, { size, weight: 700, color: o.textColor || '#fff', spacing: 3 });
    });
  }

  function bigWord(ctx, s, x, y, k, o = {}) {
    if (k <= 0) return;
    const sc = E.outBack(clamp(k * 1.4));
    at(ctx, x, y, sc * (o.scale || 1), o.rot || 0, () => {
      txt(ctx, s, 0, 0, {
        size: o.size || 120, weight: 700, color: o.color || M(P.coral),
        stroke: o.stroke != null ? o.stroke : 16, strokeColor: o.strokeColor || M('#FFFFFF'), spacing: o.spacing || 2,
      });
    });
  }

  function starburst(ctx, x, y, r, n, color) {
    ctx.beginPath();
    for (let i = 0; i < n * 2; i++) {
      const a = (i / (n * 2)) * Math.PI * 2;
      const rad = i % 2 ? r * 0.82 : r;
      ctx.lineTo(x + Math.cos(a) * rad, y + Math.sin(a) * rad);
    }
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  }

  function sticker(ctx, lines, x, y, k, o = {}) {
    if (k <= 0) return;
    at(ctx, x, y, E.outBack(clamp(k)), o.rot != null ? o.rot : -0.14, () => {
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,0.18)';
      ctx.shadowBlur = 18;
      ctx.shadowOffsetY = 6;
      starburst(ctx, 0, 0, o.r || 150, 18, o.color || C(P.yellow));
      ctx.restore();
      lines.forEach((l, i) => txt(ctx, l, 0, (i - (lines.length - 1) / 2) * (o.size || 38) * 1.1 + 3, {
        size: o.size || 38, weight: 700, color: o.textColor || C(P.ink),
      }));
    });
  }

  function thought(ctx, x, y, w, h, k, fromX, fromY) {
    if (k <= 0) return;
    const s = E.outBack(clamp(k));
    [[0.25, 12], [0.5, 18]].forEach(([f, r]) => circle(ctx, lerp(fromX, x, f), lerp(fromY, y + h / 2, f), r * s, C('#FFFFFF')));
    at(ctx, x, y, s, 0, () => {
      card(ctx, -w / 2, -h / 2, w, h, { r: h / 2, fill: C('#FFFFFF'), shadowA: 0.12 });
    });
  }

  function dotted(ctx, x1, y1, x2, y2, color, k = 1) {
    ctx.save();
    ctx.setLineDash([3, 14]);
    ctx.lineCap = 'round';
    ctx.lineWidth = 6;
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(lerp(x1, x2, k), lerp(y1, y2, k));
    ctx.stroke();
    ctx.restore();
  }

  function supportCard(ctx, x, y, k, icon, title, sub, ok) {
    if (k <= 0) return;
    const w = 420, h = 118;
    at(ctx, x, y, E.outBack(clamp(k)), 0, () => {
      if (ok) card(ctx, -w / 2, -h / 2, w, h, { r: 24 });
      else card(ctx, -w / 2, -h / 2, w, h, { r: 24, fill: C('#F1ECE4'), shadow: false, stroke: C('#C9C2B8'), dash: [12, 10], lw: 4 });
      emoji(ctx, icon, -w / 2 + 58, 0, 52, { alpha: ok ? 1 : 0.35 });
      txt(ctx, title, -w / 2 + 104, -18, { size: 31, weight: 600, align: 'left', color: ok ? C(P.ink) : C('#A39C92') });
      txt(ctx, sub, -w / 2 + 104, 24, { size: 22, weight: 500, font: 'sans', align: 'left', color: ok ? C(P.inkSoft) : C('#B5AEA4') });
      if (ok) check(ctx, w / 2 - 30, -h / 2 + 30, 0.85, M(P.green));
      else cross(ctx, w / 2 - 30, -h / 2 + 30, 0.85, C(P.red));
    });
  }

  function paper(ctx, x, y, w, h, rot, color) {
    ctx.save();
    ctx.translate(x + w / 2, y + h / 2);
    ctx.rotate(rot);
    ctx.shadowColor = 'rgba(0,0,0,0.45)';
    ctx.shadowBlur = 40;
    ctx.shadowOffsetY = 16;
    ctx.fillStyle = color || M(P.paper);
    ctx.fillRect(-w / 2, -h / 2, w, h);
    ctx.restore();
  }

  /** A prospectus row: label ..... value, typed in as k goes 0 -> 1. */
  function row(ctx, label, value, x, y, w, k, o = {}) {
    if (k <= 0) return;
    const size = o.size || 25;
    const n = Math.floor((label.length + value.length) * clamp(k * 1.25));
    const shownLabel = label.slice(0, n);
    txt(ctx, shownLabel, x, y, { size, weight: 400, font: 'mono', align: 'left', color: M('#2A2A2A') });
    const lw = measure(ctx, label, size, 400, 'mono');
    if (n > label.length || o.redact) {
      // dotted leader
      ctx.save();
      ctx.setLineDash([2, 8]);
      ctx.strokeStyle = M('#9A958C');
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x + lw + 12, y + 8);
      ctx.lineTo(x + w - (o.valueW || 200) - 12, y + 8);
      ctx.stroke();
      ctx.restore();
    }
    if (o.redact) {
      const rk = E.outCubic(clamp((k - 0.35) / 0.5));
      const bw = (o.valueW || 200) * rk;
      ctx.fillStyle = M('#111111');
      ctx.fillRect(x + w - (o.valueW || 200), y - size * 0.62, bw, size * 1.25);
    } else if (n > label.length) {
      const v = value.slice(0, n - label.length);
      txt(ctx, v, x + w, y, { size, weight: 600, font: 'mono', align: 'right', color: o.valueColor || M('#2A2A2A') });
    }
  }

  // ---------------------------------------------------------------- 1. title
  scene({
    from: () => 0,
    to: () => T.money + 0.7,
    cues: () => [
      sfx('whoosh', 0.1, 0.6), sfx('chime', 0.55, 0.8), sfx('pop', 2.25, 0.9), sfx('sparkle', 2.9, 0.5),
      sfx('pop', Ls('s01') + 0.15, 0.7), sfx('pop', Wd('s01', 'System') + 0.1, 0.6),
    ],
    draw(ctx, t) {
      fill(ctx, C(P.cream));
      blobs(ctx, t, 3, [P.pink, P.yellow, P.teal, P.blue], 0.55);
      const up = tw(t, 1.85, 0.7, E.inOutCubic);
      // Society logo
      const ls = pop(t, 0.15, 0.6) * lerp(1, 0.42, up);
      at(ctx, 960, lerp(400, 130, up), ls, 0, () => {
        circle(ctx, 0, 0, 130, C(P.coral));
        circle(ctx, -42, -28, 14, '#fff');
        circle(ctx, 42, -28, 14, '#fff');
        const sm = tw(t, 0.45, 0.6);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 15;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.arc(0, 4, 64, Math.PI * (0.5 - 0.36 * sm), Math.PI * (0.5 + 0.36 * sm));
        ctx.stroke();
      });
      const wm = tw(t, 0.55, 0.6, E.outBack);
      alpha(ctx, wm * (1 - up), () => {
        txt(ctx, 'SOCIETY', 960, 640 + (1 - wm) * 40, { size: 124, weight: 700, color: C(P.ink), spacing: 14 });
        txt(ctx, 'Everything is fine.™', 960, 742, { size: 40, weight: 500, font: 'sans', color: C(P.inkSoft), alpha: tw(t, 1.0, 0.5) });
      });
      alpha(ctx, up, () => txt(ctx, 'SOCIETY  presents', 960, 222, { size: 30, weight: 600, color: C(P.inkSoft), spacing: 6 }));
      // title
      const ti = pop(t, 2.25, 0.6);
      const lift = tw(t, Ls('s01') + 0.05, 0.8, E.inOutCubic);
      const wiggle = Math.sin(clamp((t - Wd('s01', 'Plan')) / 0.5) * Math.PI * 3) * 0.04 * (t > Wd('s01', 'Plan') ? 1 : 0);
      at(ctx, 960, lerp(500, 380, lift), ti * lerp(1, 0.82, lift) * (1 + wiggle), 0, () => {
        txt(ctx, 'THE PLAN', -18, 0, { size: 240, weight: 700, color: C(P.ink), spacing: 8 });
        txt(ctx, '™', measure(ctx, 'THE PLAN', 240, 700, 'round', 8) / 2 + 22, -82, { size: 70, weight: 600, color: C(P.coral) });
      });
      alpha(ctx, tw(t, 2.65, 0.5) * (1 - lift), () =>
        txt(ctx, 'a helpful explainer', 960, 655, { size: 56, weight: 500, color: C(P.coral) }));
      alpha(ctx, tw(t, 3.0, 0.4), () =>
        txt(ctx, '*results may vary', 1860, 900, { size: 28, weight: 500, font: 'sans', align: 'right', color: C(P.inkSoft) }));
      // The System arrives
      const pk = pop(t, Ls('s01') + 0.15, 0.55);
      if (pk > 0) {
        const pose = t < Wd('s01', 'Welcome') + 0.3 ? 'wave' : 'idle';
        drawPig(ctx, 960, 900 + (1 - pk) * 300, 0.95, Object.assign(pigO(t), { pose }));
        pigBadge(ctx, 1290, 760, prog(t, Wd('s01', 'System'), 0.45));
      }
    },
  });

  // ---------------------------------------------------------------- 2. step one: money
  function balanceAt(t) {
    const a = Wd('s02', 'money'), b = Le('s05'), c = Le('s06');
    if (t < a) return 0;
    if (t < b) return 8450 * E.inQuad(prog(t, a, b - a));
    return lerp(8450, 9120, prog(t, b, c - b));
  }
  function coinTimes() {
    const out = [];
    let t = Wd('s02', 'money');
    const stop = Le('s05') - 0.6;
    while (t < stop) {
      out.push(t);
      t += t < Wd('s03', 'more') ? 0.42 : 0.17;
    }
    return out;
  }
  const COINS = coinTimes();

  scene({
    from: () => T.money,
    to: () => T.love + 0.7,
    enter: { type: 'wipe', dur: 0.7, color: P.coral },
    cues: () => [
      sfx('swoosh', T.money, 0.7),
      sfx('pop', Ls('s02') + 0.05, 0.7),
      ...COINS.filter((_, i) => i % 2 === 0).map((c) => sfx('coin', c + 0.7, 0.32)),
      sfx('stamp', Wd('s03', 'fine'), 0.8),
      sfx('kaching', Wd('s04', 'priority'), 0.9),
      sfx('pop', Wd('s05', 'homeless'), 0.6), sfx('buzz', Wd('s05', 'homeless') + 0.35, 0.5),
      sfx('pop', Wd('s05', 'starve'), 0.6), sfx('buzz', Wd('s05', 'starve') + 0.35, 0.5),
      sfx('pop', Wd('s06', 'calculators'), 0.6), sfx('pop', Wd('s06', 'Advisors'), 0.6),
      sfx('pop', Wd('s06', 'employer'), 0.6), sfx('pop', Wd('s06', 'Tax'), 0.6),
      sfx('pop', Wd('s06', 'statement'), 0.6), sfx('sparkle', Wd('s06', 'exactly'), 0.6),
    ],
    draw(ctx, t) {
      fill(ctx, C(P.cream));
      blobs(ctx, t, 5, [P.yellow, P.teal, P.pink], 0.4);
      const s06 = Ls('s06') - 0.1;
      const re = tw(t, s06, 0.8, E.inOutCubic); // re-layout for the support cards

      // header
      const hk = 1 - re;
      chip(ctx, 'STEP 1', 120, 98, prog(t, Ls('s02'), 0.4) * hk, C(P.coral));
      alpha(ctx, tw(t, Wd('s02', 'make'), 0.4) * hk, () =>
        txt(ctx, 'Make money.', 120, 205, { size: 112, weight: 700, align: 'left', color: C(P.ink) }));
      alpha(ctx, tw(t, s06 + 0.4, 0.5), () => {
        txt(ctx, 'MONEY:', 640, 112, { size: 60, weight: 700, align: 'right', color: C(P.ink) });
        txt(ctx, 'FULLY SUPPORTED', 660, 112, { size: 60, weight: 700, align: 'left', color: M(P.greenD) });
        check(ctx, 1240, 108, 1.3, M(P.green));
      });

      // positions
      const youX = lerp(560, 230, re), youS = lerp(0.95, 0.8, re);
      const jarX = lerp(1250, 1000, re), jarW = lerp(330, 300, re), jarH = lerp(440, 400, re);

      // support cards around the jar
      const slots = [
        [590, 320, 'calculators', '🧮', 'Calculators', 'Retire at 65? Let’s see!'],
        [590, 490, 'Advisors', '🧑‍💼', 'Advisors', 'Free consultation'],
        [590, 660, 'employer', '🤝', 'Employer match', '+4% free money'],
        [1410, 320, 'Tax', '🧾', 'Tax breaks', 'Save on every dollar'],
        [1410, 490, 'statement', '📬', 'Statements', 'Every quarter, forever'],
        [1410, 660, 'exactly', '📈', 'You’re on track!', '+7.2% this year'],
      ];
      slots.forEach(([x, y, word, icon, title, sub]) => {
        const k = prog(t, Wd('s06', word) - 0.05, 0.45);
        if (k <= 0) return;
        dotted(ctx, x + (x < 1000 ? 210 : -210), y, jarX + (x < 1000 ? -150 : 150), 640, M(P.green, 0.5), tw(t, Wd('s06', word), 0.5));
        supportCard(ctx, x, y, k, icon, title, sub, true);
      });

      // the jar + balance
      const level = 0.08 + 0.55 * clamp(balanceAt(t) / 9120);
      const pulse = t > Wd('s04', 'retirement') ? Math.max(0, 1 - (t - Wd('s04', 'retirement')) / 0.8) : 0;
      at(ctx, jarX, 860, 1 + pulse * 0.06, 0, () => drawJar(ctx, 0, 0, jarW, jarH, level, { t, glow: 0.5 + pulse }));
      alpha(ctx, tw(t, Wd('s02', 'money'), 0.4), () =>
        txt(ctx, money(balanceAt(t)), jarX, 860 - jarH - 60, { size: 64, weight: 700, color: M(P.greenD) }));
      // #1 priority rosette
      const rk = pop(t, Wd('s04', 'number'), 0.5);
      if (rk > 0) {
        at(ctx, jarX + jarW * 0.42, 860 - jarH * 0.62, rk, -0.18, () => {
          [[-26, 60], [26, 60]].forEach(([dx, dy]) => {
            ctx.beginPath();
            ctx.moveTo(dx * 0.5, 20); ctx.lineTo(dx - 14, dy + 50); ctx.lineTo(dx, dy + 36); ctx.lineTo(dx + 14, dy + 50); ctx.closePath();
            ctx.fillStyle = M(P.blueD);
            ctx.fill();
          });
          starburst(ctx, 0, 0, 78, 16, M(P.blue));
          circle(ctx, 0, 0, 56, M('#FFFFFF'));
          txt(ctx, '#1', 0, -8, { size: 50, weight: 700, color: M(P.blueD) });
          txt(ctx, 'PRIORITY', 0, 28, { size: 16, weight: 700, color: M(P.blueD), spacing: 2 });
        });
      }

      // coins flying from You into the jar
      const handX = youX + 120 * youS, handY = 860 - 300 * youS;
      COINS.forEach((c, i) => {
        const k = (t - c) / 0.7;
        if (k < 0 || k > 1) return;
        const x = lerp(handX, jarX + ((i % 5) - 2) * 18, k);
        const y = lerp(handY, 860 - jarH + 20, k) - Math.sin(k * Math.PI) * 220;
        if (i % 3 === 0) {
          at(ctx, x, y, 1, k * 6, () => {
            rr(ctx, -30, -14, 60, 28, 4);
            ctx.fillStyle = M(P.green);
            ctx.fill();
            circle(ctx, 0, 0, 7, M('#A8F0C6'));
          });
        } else {
          circle(ctx, x, y + 2, 16, M(P.goldD));
          circle(ctx, x, y, 16, M(P.gold));
          txt(ctx, '$', x, y + 1, { size: 20, weight: 700, color: M(P.goldD) });
        }
      });

      // You
      const yk = pop(t, Ls('s02') + 0.05, 0.5);
      const worried = t > Wd('s05', 'homeless') - 0.2 && t < Le('y01') + 0.2;
      const nod = t > Ls('y01') && t < Le('y01') + 0.3 ? Math.sin((t - Ls('y01')) * 14) * 0.08 : 0;
      if (yk > 0) {
        at(ctx, youX, 860, yk, 0, () => drawYou(ctx, 0, 0, youS, Object.assign(you(t), {
          mood: worried ? 'worried' : 'happy',
          pose: t < s06 ? 'hold' : 'stand',
          headTilt: nod,
          look: worried ? -0.6 : 0.6,
        })));
      }

      // "things will be fine" sticker
      alpha(ctx, 1 - prog(t, Ls('s04') + 0.3, 0.4), () =>
        sticker(ctx, ['THINGS WILL', 'BE FINE!'], 900, 360, prog(t, Wd('s03', 'fine') - 0.05, 0.4), { r: 138, size: 34 }));

      // thought bubble: homeless / starve
      const tb = prog(t, Wd('s05', 'homeless') - 0.25, 0.4) * (1 - prog(t, Le('y01') + 0.1, 0.35));
      if (tb > 0) {
        thought(ctx, 900, 410, 430, 210, tb, youX + 40, 860 - 470 * youS);
        alpha(ctx, tb, () => {
          const a = prog(t, Wd('s05', 'homeless'), 0.35), b = prog(t, Wd('s05', 'starve'), 0.35);
          at(ctx, 800, 410, E.outBack(a), 0, () => {
            emoji(ctx, '📦', 0, -8, 96);
            txt(ctx, 'homeless', 0, 66, { size: 24, weight: 600, font: 'sans', color: C(P.inkSoft) });
          });
          at(ctx, 1000, 410, E.outBack(b), 0, () => {
            emoji(ctx, '🍽️', 0, -8, 96);
            txt(ctx, 'starving', 0, 66, { size: 24, weight: 600, font: 'sans', color: C(P.inkSoft) });
          });
          stamp(ctx, 'NO', 800, 402, prog(t, Wd('s05', 'homeless') + 0.35, 0.3), { size: 56, rot: -0.2 });
          stamp(ctx, 'NO', 1000, 402, prog(t, Wd('s05', 'starve') + 0.35, 0.3), { size: 56, rot: 0.15 });
        });
      }

      // The System on the right
      const pk = pop(t, Ls('s02') + 0.3, 0.5);
      let pose = 'idle';
      if (t > Wd('s04', 'retirement') - 0.2 && t < Le('s04')) pose = 'pointL';
      if (t > Ls('s06') && t < Wd('s06', 'calculators')) pose = 'thumbs';
      if (t > Wd('s06', 'exactly') - 0.1) pose = 'thumbs';
      const lean = t > Wd('s05', 'Right') - 0.1 && t < Le('y01') ? -0.12 : 0;
      drawPig(ctx, lerp(1700, 1790, re), 870 + (1 - pk) * 400, lerp(0.75, 0.62, re), Object.assign(pigO(t), { pose, tilt: lean, look: -0.6 }));
    },
  });

  // ---------------------------------------------------------------- 3. step two: love (on the side)
  const LOVE_WORDS = [['s07', 'love', 'love'], ['s07', 'Family', 'family'], ['s07', 'Community', 'community']];

  scene({
    from: () => T.love,
    to: () => T.years + 0.8,
    enter: { type: 'wipe', dur: 0.7, color: P.pink },
    cues: () => [
      sfx('swoosh', T.love, 0.7),
      sfx('tiny', Wd('s07', 'love'), 0.6), sfx('tiny', Wd('s07', 'Family'), 0.6), sfx('tiny', Wd('s07', 'Community'), 0.6),
      sfx('slide', Wd('s07', 'side') - 0.15, 0.7),
      sfx('swipe', Wd('s08', 'online') + 0.1, 0.6), sfx('swipe', Wd('s08', 'dating') + 0.35, 0.6), sfx('swipe', Wd('s08', 'websites') + 0.4, 0.6),
      sfx('pop', Wd('s08', 'hobby'), 0.7),
      ...[0, 1, 2, 3, 4, 5].map((i) => sfx('thud', Wd('s09', 'help') + 0.05 + i * 0.09, 0.45)),
      sfx('pop', Wd('s09', 'Good'), 0.7),
    ],
    draw(ctx, t) {
      fill(ctx, C('#FFF1F3'));
      blobs(ctx, t, 9, [P.pink, P.yellow, P.purple], 0.35);
      const headerOff = 1 - tw(t, Wd('s09', 'help') - 0.5, 0.3);
      chip(ctx, 'STEP 2', 120, 98, prog(t, Ls('s07'), 0.4) * headerOff, C(P.pinkD));
      alpha(ctx, tw(t, Ls('s07') + 0.35, 0.4) * headerOff, () =>
        txt(ctx, '(optional)', 300, 100, { size: 26, weight: 500, font: 'sans', align: 'left', color: C(P.inkSoft) }));

      // The tiny words, then they slide "to the side"
      const side = tw(t, Wd('s07', 'side') - 0.15, 0.8, E.inOutCubic);
      const panelX = lerp(W + 10, 1630, side);
      if (side > 0) {
        card(ctx, panelX, 0, 300, H, { r: 0, fill: C('#FFFFFF'), shadowA: 0.12 });
        txt(ctx, 'SIDE QUEST', panelX + 150, 70, { size: 22, weight: 700, color: C(P.inkSoft), spacing: 4 });
        ctx.fillStyle = C('#E9E2DA');
        ctx.fillRect(panelX + 30, 100, 240, 3);
      }
      const shown = LOVE_WORDS.filter(([id, w]) => t >= Wd(id, w)).map((x) => x[2]);
      if (shown.length) {
        // left-aligned so earlier words stay put as new ones arrive
        const full = LOVE_WORDS.map((w) => w[2]).join(' · ');
        const size = lerp(30, 20, side);
        const x0 = lerp(960 - measure(ctx, full, 30, 600, 'sans') / 2, panelX + 150 - measure(ctx, full, 20, 600, 'sans') / 2, side);
        const y = lerp(330, 150, side);
        const s = shown.join(' · ');
        txt(ctx, s, x0, y, { size, weight: 600, font: 'sans', align: 'left', color: C(P.inkSoft) });
        // a magnifying glass follows the newest word until it all slides to the side
        const mg = tw(t, Wd('s07', 'love') + 0.1, 0.4) * (1 - tw(t, Wd('s07', 'side') - 0.55, 0.3));
        if (mg > 0.01) {
          const centers = LOVE_WORDS.map((w, i) => {
            const before = LOVE_WORDS.slice(0, i).map((v) => v[2] + ' · ').join('');
            return x0 + measure(ctx, before, 30, 600, 'sans') + measure(ctx, w[2], 30, 600, 'sans') / 2;
          });
          const c = shown.length - 1;
          const mx = c === 0 ? centers[0] : lerp(centers[c - 1], centers[c], tw(t, Wd(LOVE_WORDS[c][0], LOVE_WORDS[c][1]), 0.3, E.inOutCubic));
          const my = y + 6 + Math.sin(t * 2) * 4;
          const R = 165, Z = 1.8;
          ctx.save();
          ctx.globalAlpha *= mg;
          ctx.beginPath();
          ctx.arc(mx, my, R, 0, Math.PI * 2);
          ctx.fillStyle = C('#FFFFFF');
          ctx.fill();
          ctx.clip();
          ctx.translate(mx, my);
          ctx.scale(Z, Z);
          ctx.translate(-mx, -my);
          txt(ctx, s, x0, y, { size: 30, weight: 700, font: 'sans', align: 'left', color: C(P.coral) });
          ctx.restore();
          ctx.save();
          ctx.globalAlpha *= mg;
          ctx.lineWidth = 14;
          ctx.strokeStyle = C(P.ink);
          ctx.beginPath();
          ctx.arc(mx, my, R, 0, Math.PI * 2);
          ctx.stroke();
          ctx.lineWidth = 28;
          ctx.lineCap = 'round';
          ctx.beginPath();
          ctx.moveTo(mx + R * 0.72, my + R * 0.72);
          ctx.lineTo(mx + R * 1.3, my + R * 1.3);
          ctx.stroke();
          ctx.restore();
        }
      }
      if (side > 0.5) {
        alpha(ctx, tw(t, Wd('s07', 'side') + 0.4, 0.4), () => emoji(ctx, '❤️', 1780, 240, 40));
      }

      // main area: what you're told to try
      const offMain = tw(t, Ls('s09') - 0.1, 0.5, E.inCubic);
      const phoneK = pop(t, Wd('s08', 'online') - 0.15, 0.5);
      if (phoneK > 0) {
        at(ctx, 780, 560 + offMain * 1000, phoneK, -0.05, () => {
          card(ctx, -150, -270, 300, 540, { r: 40, fill: C('#22243A'), shadowA: 0.25 });
          rr(ctx, -132, -248, 264, 496, 28);
          ctx.fillStyle = C('#FFF7F9');
          ctx.fill();
          txt(ctx, 'match♥', 0, -212, { size: 30, weight: 700, color: C(P.pinkD) });
          // profile cards that get swiped away
          const swipes = [Wd('s08', 'online') + 0.1, Wd('s08', 'dating') + 0.35, Wd('s08', 'websites') + 0.4, 1e9];
          const cols = [P.teal, P.yellow, P.purple, P.blue];
          for (let i = swipes.length - 1; i >= 0; i--) {
            const k = tw(t, swipes[i], 0.45, E.inCubic);
            if (k >= 1) continue;
            const prev = i === 0 ? 1 : tw(t, swipes[i - 1], 0.45, E.inCubic);
            if (prev < 1 && i > 0 && t < swipes[i - 1]) {
              // waiting under the current card
            }
            at(ctx, -k * 360, 10 + k * 40, 1, -k * 0.5, () => {
              rr(ctx, -110, -160, 220, 300, 18);
              ctx.fillStyle = C(cols[i]);
              ctx.fill();
              circle(ctx, 0, -60, 46, C('#FFFFFF', 0.9));
              rr(ctx, -50, -10, 100, 70, 30);
              ctx.fillStyle = C('#FFFFFF', 0.9);
              ctx.fill();
              rr(ctx, -80, 90, 160, 16, 8);
              ctx.fillStyle = C('#FFFFFF', 0.7);
              ctx.fill();
            });
          }
          circle(ctx, -60, 205, 30, C('#FFFFFF'));
          txt(ctx, '✕', -60, 206, { size: 30, weight: 700, color: C(P.red) });
          circle(ctx, 60, 205, 30, C('#FFFFFF'));
          txt(ctx, '♥', 60, 208, { size: 32, weight: 700, color: C(P.pinkD) });
        });
      }
      const flyerK = pop(t, Wd('s08', 'hobby') - 0.1, 0.5);
      if (flyerK > 0) {
        at(ctx, 1240, 520 + offMain * 1000, flyerK, 0.06, () => {
          card(ctx, -190, -230, 380, 460, { r: 6, fill: C('#FFFDF4'), shadowA: 0.22 });
          circle(ctx, 0, -214, 12, C(P.red));
          emoji(ctx, '🏺', 0, -90, 130);
          txt(ctx, 'POTTERY CLUB', 0, 40, { size: 40, weight: 700, color: C(P.ink), spacing: 2 });
          txt(ctx, 'Thursdays · 7pm', 0, 92, { size: 28, weight: 500, font: 'sans', color: C(P.inkSoft) });
          txt(ctx, 'all welcome!', 0, 150, { size: 40, weight: 700, font: 'hand', color: C(P.coral) });
        });
      }

      // help? none. Mirror of the money support cards, all empty.
      const hk = Wd('s09', 'help');
      if (t > hk - 0.3) {
        alpha(ctx, tw(t, hk - 0.3, 0.4), () => {
          txt(ctx, 'LOVE:', 560, 112, { size: 60, weight: 700, align: 'right', color: C(P.ink) });
          txt(ctx, 'SUPPORT NOT INCLUDED', 580, 112, { size: 60, weight: 700, align: 'left', color: C(P.red) });
          cross(ctx, 1330, 108, 1.3, C(P.red));
        });
        const slots = [
          [590, 320, '🧮', 'Calculators', 'none'],
          [590, 490, '🧑‍💼', 'Advisors', 'none'],
          [590, 660, '🤝', 'Matchmaking', 'none'],
          [1410, 320, '🧾', 'Tax breaks', 'lol'],
          [1410, 490, '📬', 'Statements', 'never'],
          [1410, 660, '📈', 'Progress', 'unknown'],
        ];
        slots.forEach(([x, y, icon, title, sub], i) => supportCard(ctx, x, y, prog(t, hk + 0.05 + i * 0.09, 0.35), icon, title, sub, false));
        // an empty jar where the money jar was
        const jk = pop(t, hk + 0.1, 0.5);
        at(ctx, 1000, 860, jk, 0, () => {
          drawJar(ctx, 0, 0, 300, 400, 0, { label: false });
          ctx.save();
          ctx.translate(0, -400 * 0.42);
          rr(ctx, -108, -34, 216, 68, 10);
          ctx.fillStyle = '#FFFDF5';
          ctx.fill();
          txt(ctx, 'LOVE', 0, 2, { size: 34, weight: 700, color: C(P.coral), spacing: 2 });
          ctx.restore();
          // cobweb
          ctx.strokeStyle = C('#9A958C', 0.7);
          ctx.lineWidth = 2;
          for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            ctx.moveTo(-120, -330);
            ctx.lineTo(-120 + Math.cos(i * 0.35) * 90, -330 + Math.sin(i * 0.35) * 90);
            ctx.stroke();
          }
          [30, 55, 80].forEach((r) => {
            ctx.beginPath();
            ctx.arc(-120, -330, r, 0, 1.45);
            ctx.stroke();
          });
        });
      }

      // You, swiping on a phone at first
      const yk = pop(t, Ls('s07') + 0.1, 0.5);
      const glum = t > hk;
      at(ctx, 250, 860, yk, 0, () => drawYou(ctx, 0, 0, 0.8, Object.assign(you(t), {
        pose: t > Wd('s08', 'online') - 0.2 && t < hk ? 'phone' : 'stand',
        prop: t > Wd('s08', 'online') - 0.2 && t < hk ? 'phone' : null,
        mood: glum ? 'neutral' : 'happy',
        look: 0.5,
      })));

      // The System: good luck!
      const pk = pop(t, Ls('s07') + 0.1, 0.5);
      const pose = t > Wd('s09', 'Good') - 0.1 ? 'thumbs' : t > Wd('s07', 'Sure') && t < Le('s07') ? 'shrug' : 'idle';
      drawPig(ctx, 1490 - side * 0 + (t > hk ? 300 : 0) * tw(t, hk - 0.4, 0.5), 870 + (1 - pk) * 400, 0.62, Object.assign(pigO(t), { pose, look: -0.5 }));
      // pinned to the side quest panel
      sticker(ctx, ['GOOD', 'LUCK!'], 1780, 470, prog(t, Wd('s09', 'luck') - 0.05, 0.4), { r: 104, size: 34, rot: 0.14, color: C(P.yellow) });
    },
  });

  // ---------------------------------------------------------------- 4. the years
  const ACTIVITIES = [
    { pose: 'phone', prop: 'phone', label: 'Dating apps', icon: '📱' },
    { pose: 'lift', prop: 'dumbbell', label: 'The gym', icon: '🏋️' },
    { pose: 'hold', prop: '🏺', label: 'Pottery club', icon: '🏺' },
    { pose: 'hold', prop: '🎸', label: 'Guitar lessons', icon: '🎸' },
    { pose: 'hold', prop: '♟️', label: 'Board game night', icon: '♟️' },
    { pose: 'hold', prop: '🧗', label: 'Climbing gym', icon: '🧗' },
    { pose: 'hold', prop: '📚', label: 'Book club', icon: '📚' },
    { pose: 'phone', prop: 'phone', label: 'Dating apps (again)', icon: '📲' },
    { pose: 'hold', prop: '🎨', label: 'Painting class', icon: '🎨' },
    { pose: 'hold', prop: '🎾', label: 'Tennis league', icon: '🎾' },
    { pose: 'hold', prop: '🧶', label: 'Knitting circle', icon: '🧶' },
    { pose: 'lift', prop: 'dumbbell', label: 'The gym (again)', icon: '💪' },
    { pose: 'hold', prop: '📷', label: 'Photo walks', icon: '📷' },
    { pose: 'hold', prop: '🎲', label: 'Trivia night', icon: '🎲' },
    { pose: 'hold', prop: '🧘', label: 'Yoga', icon: '🧘' },
    { pose: 'phone', prop: 'phone', label: 'Dating apps (premium)', icon: '💎' },
    { pose: 'hold', prop: '🍞', label: 'Sourdough', icon: '🍞' },
    { pose: 'hold', prop: '🛶', label: 'Kayaking', icon: '🛶' },
    { pose: 'hold', prop: '🎻', label: 'Violin', icon: '🎻' },
    { pose: 'hold', prop: '🥁', label: 'Drum circle', icon: '🥁' },
  ];
  const RAIN_ICONS = ['🎸', '🏺', '🎨', '🎾', '🧶', '📷', '🎲',
    '♟️', '📚', '🧘', '🏀', '🎣', '🪁', '🎹', '🥋',
    '🎿', '🛹', '🎯', '🧩', '🎳', '🪕', '🏈', '🌱', '🧵'];

  // activity schedule: switches faster as the montage speeds up
  function activitySchedule() {
    const out = [];
    let t = Ls('y02') - 0.2, i = 0;
    const freeze0 = Ls('y03') - 0.2, freeze1 = Le('y04') + 0.2, end = Le('s14') + 1.2;
    while (t < end) {
      if (t >= freeze0 && t < freeze1) { t = freeze1; continue; }
      const fast = t > Ls('s12');
      out.push({ t, a: ACTIVITIES[i % ACTIVITIES.length] });
      t += fast ? 0.95 : 1.9;
      i++;
    }
    return out;
  }
  const SCHED = activitySchedule();
  function activityAt(t) {
    let cur = SCHED[0];
    for (const s of SCHED) if (s.t <= t) cur = s;
    return cur;
  }
  // the hobby pile: every finished activity leaves something behind, then it rains hobbies
  const PILE = [];
  const PILE_X = 665;
  (function buildPile() {
    const r = rng(42);
    SCHED.forEach((s, i) => {
      if (i === 0) return;
      PILE.push({ t: s.t, icon: SCHED[i - 1].a.icon, fall: 0.5 });
    });
    // twenty years of gear piles up quietly...
    const early0 = Ls('y02') + 0.3, early1 = Ls('y03') - 0.5;
    for (let i = 0; i < 24; i++) {
      PILE.push({ t: early0 + ((early1 - early0) * i) / 24 + r() * 0.15, icon: RAIN_ICONS[(i * 7) % RAIN_ICONS.length], fall: 0.6 });
    }
    // ...then it rains hobbies
    const rainT = Wd('s12', 'more');
    for (let i = 0; i < 70; i++) {
      PILE.push({ t: rainT + i * 0.05 + r() * 0.04, icon: RAIN_ICONS[i % RAIN_ICONS.length], fall: 0.8 });
    }
    PILE.sort((a, b) => a.t - b.t);
    const rr2 = rng(7);
    PILE.forEach((p, i) => {
      const h = Math.sqrt(i) * 30;
      const spread = Math.max(28, 215 - h * 0.85);
      p.x = PILE_X + (rr2() - 0.5) * spread * 2;
      p.y = 856 - h - rr2() * 12;
      p.rot = (rr2() - 0.5) * 1.2;
      p.size = 58 + rr2() * 16;
      p.dx = (rr2() - 0.5) * 360;
    });
  })();

  function savingsAt(t) {
    const age = ageAt(t);
    return 9120 * Math.pow(1.128, age - 25);
  }

  scene({
    from: () => T.years,
    to: () => T.wait + 0.8,
    enter: { type: 'iris', dur: 0.8 },
    cues: () => {
      const c = [sfx('swoosh', T.years, 0.6)];
      SCHED.forEach((s, i) => { if (i > 0 && (i % 2 === 0 || s.t > Ls('s12'))) c.push(sfx('tick', s.t, 0.35)); });
      c.push(sfx('pop', Ls('s10') - 0.1, 0.6), sfx('kaching', Wd('s10', 'savings'), 0.7));
      c.push(sfx('drop', Wd('s11', 'hobby'), 0.7));
      PILE.filter((p) => p.t > Wd('s12', 'more') - 0.01).forEach((p, i) => { if (i % 3 === 0) c.push(sfx('drop', p.t + p.fall, 0.35)); });
      PILE.filter((p) => p.t < Ls('y03')).forEach((p, i) => { if (i % 2 === 0) c.push(sfx('drop', p.t + p.fall, 0.18)); });
      c.push(sfx('pop', Wd('s12', 'tried'), 0.6), sfx('pop', Wd('s12', 'bro'), 0.8));
      ['Keep', 'Keep', 'Keep'].forEach((w, i) => c.push(sfx('stamp', Wd('s13', w, i), 0.75)));
      c.push(sfx('sparkle', Wd('s13', 'least'), 0.6), sfx('balloonpop', Wd('s13', 'expect') + 0.7, 0.8));
      c.push(sfx('stamp', Wd('s14', 'Keep'), 0.9));
      return c;
    },
    draw(ctx, t) {
      fill(ctx, C(P.cream));
      blobs(ctx, t, 21, [P.teal, P.yellow, P.pink], 0.35);
      const age = ageAt(t);
      const ageK = (age - 25) / 40;
      const freeze = t > Ls('y03') - 0.2 && t < Le('y04') + 0.2;
      const kinetic = t > Wd('s12', 'more') - 0.2 && t < Le('s14') + 0.9;
      const zoom = tw(t, Ls('y04') - 0.2, 0.6, E.inOutCubic) * (1 - tw(t, Ls('s12') - 0.1, 0.5, E.inOutCubic));
      ctx.save();
      ctx.translate(PILE_X, 720);
      ctx.scale(1 + zoom * 0.14, 1 + zoom * 0.14);
      ctx.translate(-PILE_X, -720);

      // age counter
      alpha(ctx, tw(t, Ls('y02') - 0.3, 0.4), () => {
        txt(ctx, 'AGE', 960, 66, { size: 28, weight: 700, font: 'sans', color: C(P.inkSoft), spacing: 8 });
        txt(ctx, String(Math.floor(age)), 960, 142, { size: 110, weight: 700, color: C(P.ink) });
      });

      // trackers (right)
      const ck = tw(t, Ls('y02'), 0.6, E.outBack);
      const cx = 1530 + (1 - ck) * 700;
      at(ctx, cx, 385, 1, 0, () => {
        const pulse = t > Wd('s10', 'savings') - 0.1 && t < Le('s10') ? 0.5 + 0.5 * Math.sin((t - Wd('s10', 'savings')) * 10) : 0;
        card(ctx, -310, -150, 620, 300, { r: 30, fill: C('#FFFFFF'), stroke: pulse ? M(P.green, pulse) : null, lw: 8 });
        txt(ctx, 'RETIREMENT SAVINGS', -270, -100, { size: 25, weight: 700, font: 'sans', align: 'left', color: M(P.greenD), spacing: 3 });
        txt(ctx, '↗ on track', 270, -100, { size: 24, weight: 600, font: 'sans', align: 'right', color: M(P.greenD) });
        txt(ctx, money(savingsAt(t)), -270, -18, { size: 84, weight: 700, align: 'left', color: M(P.green) });
        // the line only ever goes up
        ctx.save();
        ctx.beginPath();
        const n = 40, span = Math.max(0.5, age - 25);
        for (let i = 0; i <= n; i++) {
          const v = Math.pow(1.128, (i / n) * span) / Math.pow(1.128, span);
          const x = -270 + (i / n) * 540, y = 112 - v * 72;
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = M(P.green);
        ctx.lineWidth = 7;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.stroke();
        ctx.restore();
      });
      at(ctx, cx, 745, 1, 0, () => {
        const zero = t > Ls('y03') - 0.1 && t < Le('y03') + 0.8;
        card(ctx, -310, -165, 620, 320, { r: 30, fill: C('#FFFFFF'), stroke: zero ? C(P.red, 0.8) : null, lw: 8 });
        txt(ctx, 'LOVE · FAMILY · VILLAGE', -270, -118, { size: 25, weight: 700, font: 'sans', align: 'left', color: C(P.coral), spacing: 3 });
        ctx.save();
        ctx.translate(-238, -38);
        ctx.rotate(freeze ? 0 : t * 5);
        ctx.strokeStyle = C(P.coral);
        ctx.lineWidth = 9;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.arc(0, 0, 28, 0, Math.PI * 1.4);
        ctx.stroke();
        ctx.restore();
        txt(ctx, zero ? 'No results.' : 'Searching…', -186, -38, { size: 48, weight: 700, align: 'left', color: zero ? C(P.red) : C(P.ink) });
        rr(ctx, -270, 20, 540, 20, 10);
        ctx.fillStyle = C('#EFE8E0');
        ctx.fill();
        rr(ctx, -270, 20, 8, 20, 4);
        ctx.fillStyle = C(P.coral);
        ctx.fill();
        txt(ctx, '0%', 270, -2, { size: 22, weight: 700, font: 'sans', align: 'right', color: C(P.inkSoft) });
        const dates = Math.floor((age - 25) * 2.4);
        txt(ctx, `First dates: ${dates}  ·  Second dates: ${Math.floor(dates / 14)}`, -270, 82, { size: 24, weight: 500, font: 'sans', align: 'left', color: C(P.inkSoft) });
        txt(ctx, 'Village: not found', -270, 120, { size: 24, weight: 600, font: 'sans', align: 'left', color: C(P.inkSoft) });
      });

      // the pile
      PILE.forEach((p) => {
        if (t < p.t) return;
        const k = clamp((t - p.t) / p.fall);
        const y = k < 1 ? lerp(-120, p.y, E.inQuad(k)) : p.y;
        const x = k < 1 ? lerp(p.x + p.dx, p.x, E.outQuad(k)) : p.x;
        const bounce = k >= 1 ? Math.max(0, 1 - (t - p.t - p.fall) / 0.25) * Math.sin((t - p.t - p.fall) * 30) * 8 : 0;
        emoji(ctx, p.icon, x, y - Math.abs(bounce), p.size, { rot: p.rot * k });
      });
      if (zoom > 0.01) {
        alpha(ctx, zoom, () => {
          txt(ctx, 'my hobbies', 880, 470, { size: 58, weight: 700, font: 'hand', color: C(P.coral) });
          ctx.strokeStyle = C(P.coral);
          ctx.lineWidth = 6;
          ctx.lineCap = 'round';
          ctx.beginPath();
          ctx.moveTo(860, 505);
          ctx.quadraticCurveTo(840, 560, 770, 600);
          ctx.stroke();
        });
      }

      // You
      const act = activityAt(t);
      const a = freeze ? { pose: 'stand', prop: null, label: '' } : act.a;
      const pose = t > Ls('y04') - 0.1 && t < Le('y04') + 0.2 ? 'shrug' : a.pose;
      const lk = clamp((t - act.t) / 0.3);
      drawYou(ctx, 330, 860, 0.95, Object.assign(you(t), {
        age: ageK, pose, prop: pose === 'shrug' ? null : a.prop,
        mood: freeze ? 'sad' : ageK > 0.5 ? 'tired' : 'neutral', look: 0.4,
      }));
      if (a.label && t > Ls('y02') - 0.2 && !kinetic) {
        alpha(ctx, lk, () => {
          const w = measure(ctx, a.label, 30, 600, 'round') + 50;
          card(ctx, 330 - w / 2, 272, w, 56, { r: 28, fill: C(P.ink), shadowA: 0.1 });
          txt(ctx, a.label, 330, 301, { size: 30, weight: 600, color: '#fff' });
        });
      }
      ctx.restore(); // zoom

      // a heart that shows up when you least expect it... and pops
      const hb = Wd('s13', 'least');
      if (t > hb && t < hb + 1.1) {
        const k = (t - hb) / 0.7;
        if (k < 1) emoji(ctx, '💗', 820 + Math.sin(t * 6) * 20, lerp(900, 500, E.outCubic(k)), 90, { money: true });
        else {
          const b = (t - hb - 0.7) / 0.4;
          for (let i = 0; i < 8; i++) {
            const ang = (i / 8) * Math.PI * 2;
            circle(ctx, 820 + Math.cos(ang) * b * 90, 500 + Math.sin(ang) * b * 90, 8 * (1 - b), M(P.pink));
          }
        }
      }

      // kinetic words: The System stays in full colour
      bigWord(ctx, 'HOBBIES!', 760, 300, prog(t, Wd('s12', 'more'), 0.35) * (1 - prog(t, Wd('s12', 'tried') - 0.1, 0.1)), { rot: -0.08 });
      bigWord(ctx, 'HOBBIES?', 760, 300, prog(t, Wd('s12', 'tried'), 0.35) * (1 - prog(t, Wd('s12', 'Come') - 0.1, 0.1)), { rot: 0.06, color: M(P.purple) });
      bigWord(ctx, 'HOBBIES, BRO!', 760, 300, prog(t, Wd('s12', 'Hobbies', 2) - 0.05, 0.35) * (1 - prog(t, Le('s12') + 0.2, 0.15)), { rot: -0.05, size: 100 });
      const keeps = [
        [Wd('s13', 'Keep', 0), 'KEEP DOING THE HOBBY GROUPS'],
        [Wd('s13', 'Keep', 1), 'KEEP GOING TO THE GYM'],
        [Wd('s13', 'Keep', 2), 'KEEP DOING THE ONLINE DATING'],
      ];
      keeps.forEach(([kt, label], i) => {
        const k = prog(t, kt, 0.3) * (1 - prog(t, Le('s14') + 0.3, 0.3));
        stamp(ctx, label, 760, 235 + i * 92, k, { size: 34, rot: (i - 1) * 0.04, color: M(P.coral), alpha: 0.95 });
      });
      const kb = prog(t, Wd('s14', 'Keep') - 0.05, 0.35) * (1 - prog(t, Le('s14') + 0.7, 0.3));
      bigWord(ctx, 'KEEP GOING, BUDDY!', 760, 560, kb, { size: 84, color: M(P.coral), rot: -0.04 });

      // The System pops up to help
      const pin = Ls('s10') - 0.25, pout = Le('s14') + 0.6;
      const pk = tw(t, pin, 0.5, E.outBack) * (1 - tw(t, pout, 0.4, E.inBack));
      if (pk > 0) {
        let pose = 'idle';
        if (t > Wd('s10', 'retirement') - 0.2 && t < Le('s10')) pose = 'point';
        if (t > Wd('s11', 'know') - 0.3 && t < Le('s11')) pose = 'shrug';
        if (t > Ls('s12') && t < Le('s12')) pose = 'thumbs';
        if (t > Ls('s13')) pose = 'thumbs';
        drawPig(ctx, 1015, 880 + (1 - pk) * 420, 0.6, Object.assign(pigO(t), { pose }));
      }
      // quiet beat on "I never found love."
      const quiet = tw(t, Ls('y03') - 0.2, 0.4) * (1 - tw(t, Le('y03') + 0.5, 0.5));
      if (quiet > 0) {
        ctx.save();
        const g = ctx.createRadialGradient(330, 600, 150, 330, 600, 1300);
        g.addColorStop(0, 'rgba(18,20,23,0)');
        g.addColorStop(1, `rgba(18,20,23,${0.55 * quiet})`);
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
        ctx.restore();
      }
    },
  });

  // ---------------------------------------------------------------- 5. the waiting room
  scene({
    from: () => T.wait,
    to: () => T.hold + 0.1,
    enter: { type: 'fade', dur: 0.9 },
    cues: () => {
      const c = [sfx('dingdong', T.wait + 0.9, 0.55)];
      for (let x = T.wait + 1.2; x < T.lightsOut; x += 1) c.push(sfx('clock', x, 0.25));
      c.push(sfx('door', Ls('s15') - 0.45, 0.6), sfx('switch', T.lightsOut, 0.9));
      return c;
    },
    draw(ctx, t) {
      const push = tw(t, T.wait, T.lightsOut - T.wait, E.inOutQuad);
      ctx.save();
      ctx.translate(680, 620);
      ctx.scale(1 + push * 0.07, 1 + push * 0.07);
      ctx.translate(-680, -620);
      fill(ctx, C('#D7E5DD'));
      ctx.fillStyle = C('#B9C8BF');
      ctx.fillRect(0, 760, W, H - 760);
      ctx.fillStyle = C('#A9B7AE');
      ctx.fillRect(0, 752, W, 14);
      // wall clock, hands racing
      at(ctx, 400, 250, 1, 0, () => {
        circle(ctx, 0, 0, 92, C('#5B5E7A'));
        circle(ctx, 0, 0, 80, C('#FFFFFF'));
        for (let i = 0; i < 12; i++) {
          const a = (i / 12) * Math.PI * 2;
          circle(ctx, Math.cos(a) * 64, Math.sin(a) * 64, 4, C('#5B5E7A'));
        }
        ctx.strokeStyle = C(P.ink);
        ctx.lineCap = 'round';
        const m = (t - T.wait) * 2.4, h = m / 12;
        ctx.lineWidth = 7;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.sin(h) * 40, -Math.cos(h) * 40); ctx.stroke();
        ctx.lineWidth = 5;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.sin(m) * 62, -Math.cos(m) * 62); ctx.stroke();
        circle(ctx, 0, 0, 7, C(P.ink));
      });
      // poster
      at(ctx, 880, 280, 1, 0.02, () => {
        card(ctx, -150, -120, 300, 240, { r: 6, fill: C('#FFF6E0'), shadowA: 0.15 });
        emoji(ctx, '🎨', 0, -48, 70);
        txt(ctx, 'HAVE YOU TRIED', 0, 36, { size: 28, weight: 700, color: C(P.ink) });
        txt(ctx, 'HOBBIES?', 0, 76, { size: 40, weight: 700, color: C(P.coral) });
      });
      // now serving display
      at(ctx, 1330, 250, 1, 0, () => {
        card(ctx, -190, -90, 380, 180, { r: 14, fill: C('#2A2D36') });
        txt(ctx, 'NOW SERVING', 0, -50, { size: 26, weight: 700, font: 'sans', color: '#DDD', spacing: 5 });
        const blink = Math.floor((t - T.wait) * 1.5) % 2 === 0;
        txt(ctx, blink ? '0007' : '0007', 0, 26, { size: 84, weight: 600, font: 'mono', color: M('#FF4D4D') });
      });
      // door
      const doorOpen = tw(t, Ls('s15') - 0.5, 0.5, E.outCubic);
      ctx.fillStyle = C('#3C4250');
      ctx.fillRect(1600, 380, 200, 380);
      if (doorOpen > 0) {
        const pk = tw(t, Ls('s15') - 0.3, 0.45, E.outBack);
        drawPig(ctx, 1700 + (1 - pk) * 160, 790, 0.8, Object.assign(pigO(t), { pose: t > Wd('s15', 'Goodbye') - 0.1 ? 'wave' : t > Wd('s15', 'sucks') - 0.2 && t < Wd('s15', 'Anyway') ? 'shrug' : 'idle', look: -1 }));
      }
      ctx.save();
      ctx.translate(1600, 380);
      ctx.scale(1 - doorOpen * 0.85, 1);
      ctx.fillStyle = C('#8C7A66');
      ctx.fillRect(0, 0, 200, 380);
      circle(ctx, 170, 200, 10, C('#E0C080'));
      ctx.restore();
      // chairs
      [330, 560, 790, 1020, 1250].forEach((x) => {
        ctx.fillStyle = C('#6B7A8F');
        ctx.fillRect(x - 70, 712, 8, 140);
        ctx.fillRect(x + 62, 712, 8, 140);
        rr(ctx, x - 90, 690, 180, 32, 10);
        ctx.fillStyle = C(P.teal);
        ctx.fill();
        rr(ctx, x - 90, 520, 180, 150, 18);
        ctx.fill();
      });
      // plant
      at(ctx, 1440, 860, 1, 0, () => {
        rr(ctx, -50, -110, 100, 110, 12);
        ctx.fillStyle = C('#B5654A');
        ctx.fill();
        ctx.strokeStyle = C('#5E8C55');
        ctx.lineWidth = 12;
        ctx.lineCap = 'round';
        [-1, -0.4, 0.3, 1].forEach((d) => {
          ctx.beginPath();
          ctx.moveTo(0, -110);
          ctx.quadraticCurveTo(d * 60, -230, d * 120, -150 + Math.abs(d) * 40);
          ctx.stroke();
        });
      });
      // the jar has the next seat: overflowing, glowing, the only colour left
      drawJar(ctx, 790, 700, 210, 300, 1.12, { t, glow: 1 });
      // You
      drawYou(ctx, 550, 860, 0.95, Object.assign(you(t), { age: 1, pose: 'sit', prop: 'ticket', mood: 'tired', look: 0.2 }));
      ctx.restore();

      // lights out
      const off = prog(t, T.lightsOut, 0.06);
      if (off > 0) {
        ctx.fillStyle = `rgba(6,7,9,${0.96 * off})`;
        ctx.fillRect(0, 0, W, H);
        const fadeGlow = 1 - prog(t, T.lightsOut + 0.7, 1.0);
        if (fadeGlow > 0) {
          const g = ctx.createRadialGradient(800, 560, 20, 800, 560, 260);
          g.addColorStop(0, M(P.green, 0.35 * fadeGlow));
          g.addColorStop(1, M(P.green, 0));
          ctx.fillStyle = g;
          ctx.fillRect(400, 200, 800, 700);
        }
      }
    },
  });

  // ---------------------------------------------------------------- 6. hold on: the prospectus
  scene({
    from: () => T.hold,
    to: () => T.crowd + 0.7,
    enter: { type: 'fade', dur: 0.4 },
    cues: () => {
      const c = [];
      [['y07', 'odds'], ['y07', 'Expected'], ['y07', 'Risks'], ['y07', 'Fees'], ['y07', 'writing']].forEach(([id, w]) => c.push(sfx('type', Wd(id, w), 0.55)));
      c.push(sfx('paper', Ls('y07') - 0.3, 0.6), sfx('paper', Ls('y08') - 0.2, 0.6));
      c.push(sfx('type', Ls('y08') + 0.2, 0.55));
      [['y08', 'never'], ['y08', 'how'], ['y08', 'often'], ['y08', 'actually'], ['y08', 'works']].forEach(([id, w]) => c.push(sfx('marker', Wd(id, w), 0.5)));
      c.push(sfx('stamp', Wd('y09', 'honest'), 1.0));
      return c;
    },
    draw(ctx, t) {
      fill(ctx, M(P.night));
      // "Hold on."
      alpha(ctx, env(t, Ls('y06') - 0.15, Ls('y07') - 0.2, 0.25, 0.35), () =>
        txt(ctx, 'Hold on.', 960, 470, { size: 130, weight: 400, font: 'serif', color: M('#F5F1EA') }));

      // left: the money paperwork
      const lk = tw(t, Ls('y07') - 0.35, 0.7, E.outCubic);
      if (lk > 0) {
        ctx.save();
        ctx.translate(-(1 - lk) * 900, 0);
        paper(ctx, 170, 110, 740, 760, -0.015);
        ctx.save();
        ctx.translate(540, 490);
        ctx.rotate(-0.015);
        ctx.translate(-540, -490);
        txt(ctx, 'RETIREMENT FUND', 230, 175, { size: 36, weight: 600, font: 'mono', align: 'left', color: M('#1A1A1A') });
        txt(ctx, 'Prospectus · Quarterly statement', 230, 220, { size: 22, weight: 400, font: 'mono', align: 'left', color: M('#6A655C') });
        ctx.fillStyle = M('#1A1A1A');
        ctx.fillRect(230, 248, 620, 3);
        const rows = [
          ['Odds of success', '94%', 'odds'],
          ['Expected return', '7% / yr', 'Expected'],
          ['Risk level', '4 of 7', 'Risks'],
          ['Fees', '0.04%', 'Fees'],
          ['Statements', 'quarterly', 'writing'],
        ];
        rows.forEach(([label, value, w], i) => row(ctx, label, value, 230, 310 + i * 66, 620, prog(t, Wd('y07', w) - 0.05, 0.6), { valueW: 150 }));
        // growth bars
        const bk = tw(t, Wd('y07', 'quarter') - 0.2, 0.8);
        for (let i = 0; i < 12; i++) {
          const h = (40 + i * 13 + Math.sin(i * 1.7) * 10) * clamp(bk * 1.6 - i * 0.05);
          ctx.fillStyle = M(P.green);
          ctx.fillRect(240 + i * 50, 810 - h, 34, h);
        }
        txt(ctx, 'sample figures', 850, 836, { size: 16, weight: 400, font: 'mono', align: 'right', color: M('#8A857C') });
        ctx.restore();
        ctx.restore();
      }

      // right: the love paperwork
      const rk = tw(t, Ls('y08') - 0.25, 0.7, E.outCubic);
      if (rk > 0) {
        ctx.save();
        ctx.translate((1 - rk) * 900, 0);
        paper(ctx, 1010, 110, 740, 760, 0.012);
        ctx.save();
        ctx.translate(1380, 490);
        ctx.rotate(0.012);
        ctx.translate(-1380, -490);
        txt(ctx, 'THE PLAN FOR LOVE,', 1070, 160, { size: 34, weight: 600, font: 'mono', align: 'left', color: M('#1A1A1A') });
        txt(ctx, 'FAMILY & COMMUNITY', 1070, 202, { size: 34, weight: 600, font: 'mono', align: 'left', color: M('#1A1A1A') });
        txt(ctx, 'Prospectus', 1070, 242, { size: 22, weight: 400, font: 'mono', align: 'left', color: M('#6A655C') });
        ctx.fillStyle = M('#1A1A1A');
        ctx.fillRect(1070, 268, 620, 3);
        row(ctx, 'Method', 'hobbies, gym, apps', 1070, 330, 620, prog(t, Ls('y08') + 0.2, 0.7), { valueW: 300, size: 24 });
        const red = [
          ['Odds of success', 'never'],
          ['Typical wait', 'how'],
          ['Odds it never happens', 'often'],
          ['Statements', 'actually'],
          ['Support provided', 'works'],
        ];
        red.forEach(([label, w], i) => {
          const isText = label === 'Statements' || label === 'Support provided';
          row(ctx, label, isText ? (label === 'Statements' ? 'never' : 'none') : '', 1070, 400 + i * 66, 620, prog(t, Wd('y08', w) - 0.05, 0.6),
            { valueW: isText ? 120 : 210, size: 24, redact: !isText, valueColor: M(P.red) });
        });
        ctx.restore();
        ctx.restore();
        stamp(ctx, 'SUCCESS RATE\nNOT DISCLOSED', 1380, 560, prog(t, Wd('y09', 'honest') - 0.05, 0.35), { size: 62, rot: -0.2, font: 'round' });
      }
    },
  });

  // ---------------------------------------------------------------- 7. a hundred people
  const GRID = (() => {
    const r = rng(2024);
    const cells = [];
    for (let i = 0; i < 100; i++) cells.push({ i, c: i % 10, r: Math.floor(i / 10), lit: false, delay: r() });
    // pick 50 to find connection, in little clumps (couples, families, villages)
    const order = cells.map((c) => c.i).sort(() => r() - 0.5);
    let lit = 0;
    for (const i of order) {
      if (lit >= 50) break;
      if (!cells[i].lit) { cells[i].lit = true; lit++; }
      const nb = [i + 1, i + 10].filter((j) => j < 100 && (j !== i + 1 || i % 10 !== 9));
      for (const j of nb) if (lit < 50 && r() < 0.45 && !cells[j].lit) { cells[j].lit = true; lit++; }
    }
    const warm = [P.coral, P.yellow, P.pink, P.teal, '#FF9F68'];
    cells.forEach((c) => { c.col = warm[Math.floor(r() * warm.length)]; c.lightDelay = r(); });
    const links = [];
    cells.forEach((c) => {
      if (!c.lit) return;
      const right = c.c < 9 ? cells[c.i + 1] : null, down = c.r < 9 ? cells[c.i + 10] : null;
      [right, down].forEach((d) => { if (d && d.lit) links.push({ a: c, b: d, phase: Math.floor(r() * 3) }); });
    });
    return { cells, links };
  })();

  scene({
    from: () => T.crowd,
    to: () => T.pyramid + 0.7,
    enter: { type: 'fade', dur: 0.6 },
    cues: () => [
      sfx('ripple', Wd('y10', 'hundred') - 0.2, 0.7),
      sfx('tiny', Wd('y10', 'Hobbies'), 0.5), sfx('tiny', Wd('y10', 'Gym'), 0.5), sfx('tiny', Wd('y10', 'Apps'), 0.5), sfx('tiny', Wd('y10', 'All'), 0.5),
      sfx('shimmer', Wd('y11', 'fifty') - 0.1, 0.8),
      sfx('chime', Wd('y11', 'family'), 0.4), sfx('chime', Wd('y11', 'village'), 0.4),
      sfx('paper', Wd('y12', '2023') - 0.4, 0.5),
      sfx('pop', Ls('s16') - 0.2, 0.6),
      ...[0, 1, 2, 3, 4, 5, 6, 7].map((i) => sfx('coin', Wd('s16', 'money') + i * 0.1, 0.4)),
      sfx('buzz', Wd('s17', 'fifty'), 0.5),
      ...[0, 1, 2, 3, 4].map((i) => sfx('tiny', Wd('s18', 'home') + i * 0.12, 0.4)),
    ],
    draw(ctx, t) {
      fill(ctx, M('#15171C'));
      const cardIn = tw(t, Wd('y12', '2023') - 0.45, 0.6, E.outCubic);
      const cardOut = tw(t, Le('y12') + 0.2, 0.4, E.inOutQuad);
      const cardK = cardIn * (1 - cardOut);
      const gx = 960, gy = 540, cell = 66;
      const dim = 1 - cardK * 0.75;
      alpha(ctx, dim, () => {
        // header
        alpha(ctx, tw(t, Wd('y10', 'hundred') - 0.2, 0.4), () =>
          txt(ctx, '100 people follow the advice exactly.', 960, 100, { size: 44, weight: 600, font: 'sans', color: M('#F5F1EA') }));
        const chips = [['Hobbies', 'hobbies'], ['Gym', 'gym'], ['Apps', 'apps'], ['All', 'all of it']];
        chips.forEach(([w, label], i) => {
          const k = pop(t, Wd('y10', w), 0.4);
          if (k <= 0) return;
          at(ctx, 960 + (i - 1.5) * 200, 168, k, 0, () => {
            card(ctx, -88, -24, 176, 48, { r: 24, fill: M('#262A33'), shadow: false });
            txt(ctx, label + ' ✓', 0, 1, { size: 24, weight: 600, font: 'sans', color: M('#CFE8D8') });
          });
        });
        // links between people who found each other
        const lt = [Wd('y11', 'love'), Wd('y11', 'family'), Wd('y11', 'village')];
        GRID.links.forEach((l) => {
          const k = tw(t, lt[l.phase] + l.a.lightDelay * 0.3, 0.5);
          if (k <= 0) return;
          const ax = gx + (l.a.c - 4.5) * cell, ay = gy + (l.a.r - 4.5) * cell - 16;
          const bx = gx + (l.b.c - 4.5) * cell, by = gy + (l.b.r - 4.5) * cell - 16;
          ctx.strokeStyle = M(P.yellow, 0.55);
          ctx.lineWidth = 5;
          ctx.beginPath();
          ctx.moveTo(ax, ay);
          ctx.lineTo(lerp(ax, bx, k), lerp(ay, by, k));
          ctx.stroke();
        });
        // people
        const litT = Wd('y11', 'fifty') - 0.1;
        const otherT = Ls('y13');
        const bagT = Wd('s16', 'money') - 0.1;
        const homeT = Wd('s18', 'home') - 0.15;
        GRID.cells.forEach((c) => {
          const x = gx + (c.c - 4.5) * cell, y = gy + (c.r - 4.5) * cell + 16;
          const k = pop(t, Wd('y10', 'hundred') - 0.2 + (c.c + c.r) * 0.045, 0.4);
          if (k <= 0) return;
          const lk = c.lit ? tw(t, litT + c.lightDelay * 0.9, 0.35) : 0;
          const otherPulse = !c.lit && t > otherT ? Math.max(0, Math.sin(clamp((t - otherT) / 0.6) * Math.PI)) * 0.25 : 0;
          const col = c.lit ? mix('#5D6370', c.col, lk) : '#5D6370';
          token(ctx, x, y, k * (1 + otherPulse), M(col), { glow: lk > 0.5, glowColor: M(c.col, 0.12 * lk) });
          if (!c.lit) {
            const bk = pop(t, bagT + c.delay * 0.8, 0.35);
            const hk = pop(t, homeT + c.delay * 0.7, 0.35);
            if (bk > 0) emoji(ctx, '💰', x + 21, y - 30, 22 * bk, { money: true });
            if (hk > 0) emoji(ctx, '🏠', x - 21, y - 30, 21 * hk, { money: true });
          }
        });
        // counters
        const rkk = tw(t, Wd('y11', 'fifty'), 0.5);
        alpha(ctx, rkk, () => {
          txt(ctx, '50', 1590, 420, { size: 170, weight: 400, font: 'serif', color: M(P.yellow) });
          txt(ctx, 'found love, family,', 1590, 530, { size: 34, weight: 600, font: 'sans', color: M('#F5F1EA') });
          txt(ctx, 'a village', 1590, 574, { size: 34, weight: 600, font: 'sans', color: M('#F5F1EA') });
          alpha(ctx, tw(t, Wd('y12', 'guess') - 0.1, 0.4), () =>
            txt(ctx, '(my guess)', 1590, 630, { size: 30, weight: 400, font: 'sans', color: M('#9AA0AE') }));
        });
        const lkk = tw(t, Ls('y13') + 0.2, 0.5);
        alpha(ctx, lkk, () => {
          txt(ctx, '50', 330, 420, { size: 170, weight: 400, font: 'serif', color: M('#8C93A1') });
          txt(ctx, 'didn’t', 330, 530, { size: 34, weight: 600, font: 'sans', color: M('#C4C8D0') });
          alpha(ctx, tw(t, Wd('s16', 'money') - 0.1, 0.4), () =>
            txt(ctx, '+ lots of money', 330, 600, { size: 30, weight: 600, font: 'sans', color: M(P.green) }));
          alpha(ctx, tw(t, Wd('s18', 'food') - 0.1, 0.4), () =>
            txt(ctx, '+ food & a home', 330, 646, { size: 30, weight: 600, font: 'sans', color: M('#C4C8D0') }));
          const still = tw(t, Wd('s17', 'fifty') - 0.1, 0.4, E.outBack);
          alpha(ctx, clamp(still), () =>
            txt(ctx, '= still 50', 330, 720, { size: 40, weight: 700, font: 'sans', color: M('#FFFFFF') }));
        });
      });

      // the closest thing to a real number
      // "So let's guess." before the grid shows up
      alpha(ctx, env(t, Ls('y10') - 0.1, Wd('y10', 'hundred') - 0.1, 0.3, 0.3), () =>
        txt(ctx, 'Let’s guess.', 960, 470, { size: 120, weight: 400, font: 'serif', color: M('#F5F1EA') }));

      // the closest thing to a real number: slides up in, fades up and out
      if (cardK > 0) {
        at(ctx, 960, 520 + (1 - cardIn) * 700 - cardOut * 40, 1, -0.01, () => {
          ctx.globalAlpha *= 1 - cardOut;
          card(ctx, -620, -230, 1240, 460, { r: 28, fill: M(P.paper), shadowA: 0.5, blur: 50 });
          txt(ctx, '≈ 1 in 2', -330, -30, { size: 136, weight: 400, font: 'serif', color: M('#B4472F') });
          txt(ctx, 'U.S. adults report', -50, -96, { size: 44, weight: 700, font: 'sans', align: 'left', color: M('#1A1A1A') });
          txt(ctx, 'experiencing loneliness.', -50, -44, { size: 44, weight: 700, font: 'sans', align: 'left', color: M('#1A1A1A') });
          txt(ctx, 'U.S. Surgeon General’s Advisory (2023),', -50, 30, { size: 26, weight: 500, font: 'sans', align: 'left', color: M('#55524C') });
          txt(ctx, '“Our Epidemic of Loneliness and Isolation”', -50, 68, { size: 26, weight: 500, font: 'sans', align: 'left', color: M('#55524C') });
          ctx.fillStyle = M('#DDD5C6');
          ctx.fillRect(-560, 118, 1120, 2);
          txt(ctx, 'Nobody publishes how often the advice works. This is the closest thing.', 0, 168, { size: 26, weight: 500, font: 'sans', color: M('#8A857C') });
        });
      }

      // The System chimes in
      const pk = tw(t, Ls('s16') - 0.3, 0.5, E.outBack) * (1 - tw(t, Le('s18') + 0.5, 0.4, E.inBack));
      if (pk > 0) {
        let pose = 'idle';
        if (t > Wd('s16', 'money') - 0.3 && t < Le('s16')) pose = 'pointL';
        if (t > Wd('s17', 'Too') - 0.2 && t < Le('s17')) pose = 'shrug';
        if (t > Ls('s18')) pose = 'thumbs';
        drawPig(ctx, 1720, 900 + (1 - pk) * 420, 0.62, Object.assign(pigO(t), { pose, look: -0.8 }));
      }
    },
  });

  // ---------------------------------------------------------------- 8. the pyramid
  const TIERS = [
    ['Food · water · sleep', 'food'],
    ['A home · safety · savings', 'home'],
    ['Love · belonging · community', null],
    ['Esteem · being valued', null],
    ['Meaning', null],
  ];
  scene({
    from: () => T.pyramid,
    to: () => T.ending + 0.7,
    enter: { type: 'wipe', dur: 0.7, color: P.yellow },
    cues: () => [
      sfx('swoosh', T.pyramid, 0.6),
      sfx('ding', Wd('s19', 'food'), 0.7), sfx('ding', Wd('s19', 'home'), 0.7),
      sfx('shimmer', Wd('s19', 'emotional'), 0.5),
      sfx('crack', Wd('s20', 'Too') - 0.05, 0.9), sfx('thud', Wd('s20', 'Too') + 0.75, 0.9),
    ],
    draw(ctx, t) {
      fill(ctx, C(P.cream));
      blobs(ctx, t, 31, [P.yellow, P.pink, P.teal], 0.35);
      const apexY = 150, baseY = 860, half = 560, tierH = (baseY - apexY) / 5;
      const hw = (y) => (half * (y - apexY)) / (baseY - apexY);
      const fallT = Wd('s20', 'Too') - 0.05;
      TIERS.forEach(([label, word], i) => {
        const y1 = baseY - tierH * i, y0 = y1 - tierH;
        const k = tw(t, T.pyramid + 0.25 + i * 0.12, 0.45, E.outBack);
        if (k <= 0) return;
        const covered = word && t > Wd('s19', word) - 0.05;
        const ck = word ? tw(t, Wd('s19', word) - 0.05, 0.35) : 0;
        const wanted = !word && t > Wd('s19', 'emotional') - 0.1;
        const wk = !word ? tw(t, Wd('s19', 'emotional') - 0.1 + (i - 2) * 0.15, 0.5) : 0;
        const glow = !word ? tw(t, Wd('s19', 'human') - 0.1, 0.6) : 0;
        // falling off
        let dy = 0, rot = 0, fa = 1;
        if (!word && t > fallT) {
          const f = t - fallT - (4 - i) * 0.08;
          if (f > 0) { dy = 0.5 * 2600 * f * f; rot = (i - 3) * 0.5 * f; fa = 1; }
        }
        ctx.save();
        ctx.translate(960, (y0 + y1) / 2 + dy - (1 - k) * 60);
        ctx.rotate(rot);
        ctx.globalAlpha *= clamp(k) * fa;
        const ym0 = y0 - (y0 + y1) / 2, ym1 = y1 - (y0 + y1) / 2;
        ctx.beginPath();
        ctx.moveTo(-hw(y0) + 6, ym0 + 4);
        ctx.lineTo(hw(y0) - 6, ym0 + 4);
        ctx.lineTo(hw(y1) - 6, ym1 - 4);
        ctx.lineTo(-hw(y1) + 6, ym1 - 4);
        ctx.closePath();
        let fillCol = C('#EFE6DA');
        if (covered) fillCol = M(mix('#EFE6DA', P.green, ck));
        if (wanted) fillCol = C(mix('#EFE6DA', [P.coral, P.purple, P.yellow][i - 2], wk * (0.55 + 0.45 * glow)));
        ctx.fillStyle = fillCol;
        ctx.fill();
        if (!word) {
          ctx.setLineDash([14, 10]);
          ctx.lineWidth = 4;
          ctx.strokeStyle = C('#B9AE9F');
          ctx.stroke();
          ctx.setLineDash([]);
        }
        const size = i === 4 ? 30 : 34;
        txt(ctx, label, 0, 3, { size, weight: 600, color: covered ? '#FFFFFF' : C(P.ink) });
        if (covered) check(ctx, hw(y1) - 46, 0, 1, M(P.greenD));
        ctx.restore();
      });
      // brackets
      alpha(ctx, tw(t, Wd('s19', 'home'), 0.4), () => {
        ctx.strokeStyle = M(P.greenD);
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(330, baseY - tierH * 2 + 6); ctx.lineTo(300, baseY - tierH * 2 + 6); ctx.lineTo(300, baseY - 6); ctx.lineTo(330, baseY - 6);
        ctx.stroke();
        txt(ctx, 'COVERED BY', 270, baseY - tierH - 22, { size: 30, weight: 700, align: 'right', color: M(P.greenD) });
        txt(ctx, 'THE PLAN ✓', 270, baseY - tierH + 18, { size: 30, weight: 700, align: 'right', color: M(P.greenD) });
      });
      alpha(ctx, tw(t, Wd('s19', 'emotional') + 0.2, 0.4), () => {
        ctx.strokeStyle = C(P.red);
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(1590, apexY + 6); ctx.lineTo(1620, apexY + 6); ctx.lineTo(1620, baseY - tierH * 2 - 6); ctx.lineTo(1590, baseY - tierH * 2 - 6);
        ctx.stroke();
        txt(ctx, 'NOT', 1650, (apexY + baseY - tierH * 2) / 2 - 40, { size: 30, weight: 700, align: 'left', color: C(P.red) });
        txt(ctx, 'INCLUDED', 1650, (apexY + baseY - tierH * 2) / 2, { size: 30, weight: 700, align: 'left', color: C(P.red) });
      });
      alpha(ctx, tw(t, Wd('s19', 'human') - 0.1, 0.5) * (1 - tw(t, fallT, 0.3)), () =>
        txt(ctx, 'a human being →', 330, apexY + 90, { size: 52, weight: 700, font: 'hand', color: C(P.coral) }));
      // The System
      const pk = tw(t, Ls('s19') - 0.4, 0.5, E.outBack);
      let pose = 'idle';
      if (t > Wd('s19', 'human') - 0.2 && t < Le('s19')) pose = 'shrug';
      if (t > Wd('s20', 'Goodbye') - 0.1) pose = 'wave';
      drawPig(ctx, 1720, 900 + (1 - pk) * 420, 0.66, Object.assign(pigO(t), { pose, look: -0.8 }));
    },
  });

  // ---------------------------------------------------------------- 9. the point
  scene({
    from: () => T.ending,
    to: () => T.card + 0.05,
    enter: { type: 'fade', dur: 0.6 },
    cues: () => [
      sfx('paper', Wd('y14', 'Money') - 0.1, 0.6), sfx('thud', Wd('y14', 'prospectus') + 0.2, 0.5),
      sfx('tiny', Wd('y14', 'Love') - 0.05, 0.5), sfx('paper', Wd('y14', 'have') - 0.15, 0.4),
    ],
    draw(ctx, t) {
      fill(ctx, M(P.night));
      const split = 1 - tw(t, Ls('y15') - 0.35, 0.5, E.inOutCubic);
      alpha(ctx, split, () => {
        ctx.fillStyle = M('#2A2D36');
        ctx.fillRect(958, 140, 4, 680 * tw(t, T.ending + 0.3, 0.6));
        // money side
        const mk = tw(t, Wd('y14', 'Money') - 0.1, 0.5);
        alpha(ctx, mk, () => {
          txt(ctx, 'MONEY', 480, 190, { size: 46, weight: 800, font: 'sans', color: M(P.green), spacing: 10 });
          for (let i = 7; i >= 0; i--) {
            const k = tw(t, Wd('y14', 'prospectus') - 0.2 + (7 - i) * 0.05, 0.4, E.outBack);
            at(ctx, 480 + i * 3, 600 - i * 16 - (1 - k) * 80, 1, (i % 3 - 1) * 0.02, () => {
              ctx.globalAlpha *= clamp(k);
              card(ctx, -190, -230, 380, 460, { r: 6, fill: M(i === 0 ? '#FFFFFF' : '#ECE6DA'), shadowA: 0.35, blur: 18 });
            });
          }
          const k0 = tw(t, Wd('y14', 'prospectus') + 0.1, 0.4);
          alpha(ctx, k0, () => {
            txt(ctx, 'PROSPECTUS', 480, 440, { size: 36, weight: 600, font: 'mono', color: M('#1A1A1A') });
            for (let i = 0; i < 9; i++) {
              ctx.fillStyle = M('#C9C2B4');
              ctx.fillRect(330, 490 + i * 30, i % 3 === 2 ? 200 : 300, 10);
            }
            txt(ctx, 'odds · returns · risks · fees', 480, 790, { size: 19, weight: 400, font: 'mono', color: M('#6A655C') });
          });
        });
        // love side
        const lk = tw(t, Wd('y14', 'Love') - 0.1, 0.5);
        alpha(ctx, lk, () => {
          txt(ctx, 'LOVE', 1440, 190, { size: 46, weight: 800, font: 'sans', color: M(P.coral), spacing: 10 });
          const nk = tw(t, Wd('y14', 'have') - 0.15, 0.45, E.outBack);
          if (nk > 0) {
            at(ctx, 1440, 520, nk, 0.05, () => {
              ctx.save();
              ctx.shadowColor = 'rgba(0,0,0,0.4)';
              ctx.shadowBlur = 24;
              ctx.shadowOffsetY = 10;
              ctx.fillStyle = M('#FFE27A');
              ctx.fillRect(-170, -170, 340, 340);
              ctx.restore();
              ctx.fillStyle = M('#F5D25C');
              ctx.fillRect(-170, -170, 340, 40);
              txt(ctx, 'have you', 0, -50, { size: 72, weight: 700, font: 'hand', color: M('#2A2A2A') });
              txt(ctx, 'tried', 0, 20, { size: 72, weight: 700, font: 'hand', color: M('#2A2A2A') });
              txt(ctx, 'hobbies?', 0, 90, { size: 72, weight: 700, font: 'hand', color: M('#2A2A2A') });
            });
          }
        });
      });
      // the ask
      const a1 = tw(t, Ls('y15') - 0.1, 0.5);
      alpha(ctx, a1 * (1 - split) , () =>
        txt(ctx, 'If the advice really works,', 960, 400, { size: 80, weight: 400, font: 'serif', color: M('#F5F1EA') }));
      const a2 = tw(t, Wd('y15', 'show') - 0.1, 0.6);
      alpha(ctx, a2, () =>
        txt(ctx, 'show us the success rate.', 960, 540 + (1 - a2) * 20, { size: 118, weight: 400, font: 'serif', color: M(P.yellow) }));
    },
  });

  // ---------------------------------------------------------------- 10. corporate sign-off, cut short
  scene({
    from: () => T.card,
    to: () => T.cut,
    cues: () => [sfx('pop', T.card + 0.1, 0.8), sfx('sparkle', T.card + 0.3, 0.5)],
    draw(ctx, t) {
      fill(ctx, C(P.cream));
      blobs(ctx, t, 3, [P.pink, P.yellow, P.teal, P.blue], 0.55);
      const k = pop(t, T.card + 0.05, 0.5);
      at(ctx, 960, 130, k * 0.42, 0, () => {
        circle(ctx, 0, 0, 130, C(P.coral));
        circle(ctx, -42, -28, 14, '#fff');
        circle(ctx, 42, -28, 14, '#fff');
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 15;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.arc(0, 4, 64, Math.PI * 0.14, Math.PI * 0.86);
        ctx.stroke();
      });
      at(ctx, 960, 360, k, 0, () => {
        txt(ctx, 'THE PLAN', -18, 0, { size: 200, weight: 700, color: C(P.ink), spacing: 8 });
        txt(ctx, '™', measure(ctx, 'THE PLAN', 200, 700, 'round', 8) / 2 + 18, -68, { size: 60, weight: 600, color: C(P.coral) });
      });
      alpha(ctx, tw(t, T.card + 0.35, 0.4), () => {
        txt(ctx, 'Thank you for choosing Life.', 960, 520, { size: 52, weight: 500, color: C(P.coral) });
        txt(ctx, '*Results may vary. Success rate not disclosed. Love not included.', 960, 600, { size: 28, weight: 500, font: 'sans', color: C(P.inkSoft) });
      });
      drawPig(ctx, 960, 900 + (1 - k) * 300, 0.8, Object.assign(pigO(t), { pose: 'wave' }));
    },
  });

  // black after the cut: no scene draws, so the frame stays black

  // ---------------------------------------------------------------- music
  addCues(() => [
    music('plan', 0, T.wait + 0.4, { decayFrom: Ls('y02'), decayTo: T.wait, quietFrom: Ls('y03') - 0.3, quietTo: Le('y04') + 0.2 }),
    music('muzak', T.wait - 0.3, T.lightsOut, { stop: 'tape' }),
    music('sincere', Ls('y07') - 0.9, T.card, { swellAt: Ls('y15') - 0.3 }),
    music('sting', Ls('s16') - 0.12, Ls('s16') + 2.2),
    music('sting', Ls('s19') - 0.35, Ls('s19') + 2.2),
    music('jingle', T.card, T.cut, { stop: 'hard' }),
  ]);
})();
