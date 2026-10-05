/* FLEECED - core helpers: math, easing, timeline lookups, lip-sync, camera, text. */
(function () {
  'use strict';
  const W = 1920, H = 1080;
  const TL = window.FLEECED_TIMELINE;

  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const inv = (a, b, x) => clamp((x - a) / (b - a));
  const TAU = Math.PI * 2;

  const E = {
    lin: k => k,
    in: k => k * k * k,
    out: k => 1 - Math.pow(1 - k, 3),
    inOut: k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    sine: k => 0.5 - 0.5 * Math.cos(Math.PI * k),
    back: k => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
    elastic: k => (k <= 0 ? 0 : k >= 1 ? 1 : Math.pow(2, -10 * k) * Math.sin((k * 10 - 0.75) * (TAU / 3)) + 1),
    bounce: k => {
      const n1 = 7.5625, d1 = 2.75;
      if (k < 1 / d1) return n1 * k * k;
      if (k < 2 / d1) return n1 * (k -= 1.5 / d1) * k + 0.75;
      if (k < 2.5 / d1) return n1 * (k -= 2.25 / d1) * k + 0.9375;
      return n1 * (k -= 2.625 / d1) * k + 0.984375;
    },
  };

  // deterministic hash noise
  const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453123; return x - Math.floor(x); };
  const noise = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; };

  // ---------------------------------------------------------------- timeline
  const LINES = {};
  const BY_WHO = {};
  for (const l of TL.lines) {
    LINES[l.id] = l;
    (BY_WHO[l.who] = BY_WHO[l.who] || []).push(l);
  }
  function cue(id) {
    const v = TL.cues[id];
    if (v === undefined) throw new Error('unknown cue ' + id);
    return v;
  }
  function line(id) {
    const l = LINES[id];
    if (!l) throw new Error('unknown line ' + id);
    return l;
  }
  const S = id => line(id).start;
  const End = id => line(id).end;
  /** progress 0..1 of an animation that starts at `at` and lasts `dur` seconds */
  const P = (t, at, dur = 0.5, ease = E.inOut) => ease(clamp((t - at) / dur));
  /** 1 while t in [a, b), with soft edges */
  const win = (t, a, b, f = 0.25) => clamp((t - a) / f) * clamp((b - t) / f);

  /** mouth openness for a speaker at time t (0..1) */
  function talk(who, t) {
    const ls = BY_WHO[who];
    if (!ls) return 0;
    for (const l of ls) {
      if (t >= l.start && t < l.end && l.mouth) {
        const i = (t - l.start) * TL.envFps, i0 = Math.floor(i);
        const a = +l.mouth[i0] || 0, b = +l.mouth[i0 + 1] || 0;
        return lerp(a, b, i - i0) / 9;
      }
    }
    return 0;
  }
  const speaking = (who, t) => (BY_WHO[who] || []).some(l => t >= l.start && t < l.end);

  function sceneAt(t) {
    const sc = TL.scenes;
    for (let i = 0; i < sc.length; i++) if (t < sc[i].end) return i;
    return sc.length - 1;
  }

  // ---------------------------------------------------------------- colors
  function hex(c) {
    const n = parseInt(c.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function mix(a, b, k) {
    const A = hex(a), B = hex(b);
    const r = A.map((v, i) => Math.round(lerp(v, B[i], clamp(k))));
    return '#' + r.map(v => v.toString(16).padStart(2, '0')).join('');
  }
  function rgba(c, a) {
    const [r, g, b] = hex(c);
    return `rgba(${r},${g},${b},${a})`;
  }
  function mixPal(p, q, k) {
    if (k <= 0) return p;
    if (k >= 1) return q;
    const o = {};
    for (const key in p) o[key] = typeof p[key] === 'string' && p[key][0] === '#' ? mix(p[key], q[key] || p[key], k) : lerp(p[key], q[key] ?? p[key], k);
    return o;
  }

  // ---------------------------------------------------------------- camera
  /** cam: {x, y, z, r} world point at screen centre, zoom, rotation */
  function applyCam(ctx, cam, depth = 1) {
    const z = 1 + (cam.z - 1) * depth;
    ctx.translate(W / 2, H / 2);
    if (cam.r) ctx.rotate(cam.r);
    ctx.scale(z, z);
    ctx.translate(-(W / 2 + (cam.x - W / 2) * depth), -(H / 2 + (cam.y - H / 2) * depth));
  }
  function lerpCam(a, b, k) {
    return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), z: lerp(a.z, b.z, k), r: lerp(a.r || 0, b.r || 0, k) };
  }
  /** keyframed camera: keys = [[time, cam, ease?], ...] */
  function camPath(t, keys) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      if (t < keys[i][0]) {
        const k = (t - keys[i - 1][0]) / (keys[i][0] - keys[i - 1][0]);
        return lerpCam(keys[i - 1][1], keys[i][1], (keys[i][2] || E.inOut)(k));
      }
    }
    return keys[keys.length - 1][1];
  }
  function shake(t, amp, seed = 0) {
    return { x: noise(t * 31 + seed) * amp, y: noise(t * 27 + 50 + seed) * amp };
  }
  /** decaying shake triggered at each time in `hits` */
  function hitShake(t, hits, amp = 16, decay = 0.35) {
    let a = 0;
    for (const h of hits) if (t >= h && t < h + decay * 3) a = Math.max(a, amp * Math.exp(-(t - h) / decay));
    return shake(t, a);
  }

  // ---------------------------------------------------------------- drawing utils
  function ellipse(ctx, x, y, rx, ry, rot = 0) {
    ctx.beginPath();
    ctx.ellipse(x, y, Math.max(0.01, rx), Math.max(0.01, ry), rot, 0, TAU);
  }
  function circle(ctx, x, y, r) {
    ctx.beginPath();
    ctx.arc(x, y, Math.max(0.01, r), 0, TAU);
  }
  function rrect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
  }
  function fillStroke(ctx, fill, stroke, lw) {
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke && lw) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
  }

  const FONT_TITLE = '"Luckiest Guy", "Arial Black", sans-serif';
  const FONT_UI = 'Fredoka, "Trebuchet MS", sans-serif';

  function text(ctx, str, x, y, o = {}) {
    ctx.save();
    ctx.font = `${o.weight || 600} ${o.size || 48}px ${o.font || FONT_UI}`;
    ctx.textAlign = o.align || 'center';
    ctx.textBaseline = o.baseline || 'middle';
    if (o.alpha !== undefined) ctx.globalAlpha *= o.alpha;
    if (o.ls) ctx.letterSpacing = o.ls + 'px';
    if (o.shadow) {
      ctx.fillStyle = o.shadow;
      ctx.fillText(str, x + (o.sx ?? 4), y + (o.sy ?? 6));
    }
    if (o.stroke) {
      ctx.lineJoin = 'round';
      ctx.strokeStyle = o.stroke;
      ctx.lineWidth = o.lw || 8;
      ctx.strokeText(str, x, y);
    }
    ctx.fillStyle = o.fill || '#fff';
    ctx.fillText(str, x, y);
    ctx.restore();
  }

  // ---------------------------------------------------------------- subtitles
  const chunkCache = {};
  function chunks(ctx, l) {
    if (chunkCache[l.id]) return chunkCache[l.id];
    ctx.save();
    ctx.font = `600 46px ${FONT_UI}`;
    const words = l.text.split(' ');
    const rows = [];
    let cur = '';
    for (const w of words) {
      const test = cur ? cur + ' ' + w : w;
      if (ctx.measureText(test).width > 1250 && cur) { rows.push(cur); cur = w; } else cur = test;
    }
    if (cur) rows.push(cur);
    ctx.restore();
    const groups = [];
    for (let i = 0; i < rows.length; i += 2) groups.push(rows.slice(i, i + 2));
    // time each group in proportion to its characters
    const total = groups.reduce((s, g) => s + g.join(' ').length, 0);
    let acc = 0;
    const out = groups.map(g => {
      const a = acc / total;
      acc += g.join(' ').length;
      return { rows: g, a, b: acc / total };
    });
    chunkCache[l.id] = out;
    return out;
  }

  function subtitles(ctx, t) {
    let cur = null;
    for (const l of TL.lines) if (t >= l.start - 0.05 && t < l.end + 0.3) cur = l;
    if (!cur) return;
    const k = clamp((t - cur.start) / (cur.end - cur.start), 0, 0.9999);
    const grp = chunks(ctx, cur).find(g => k >= g.a && k < g.b) || chunks(ctx, cur).slice(-1)[0];
    const color = (TL.speakers[cur.who] || {}).color || '#fff';
    const alpha = clamp((t - cur.start + 0.05) / 0.12) * clamp((cur.end + 0.3 - t) / 0.15);
    const n = grp.rows.length;
    grp.rows.forEach((row, i) => {
      text(ctx, row, W / 2, H - 70 - (n - 1 - i) * 58, {
        size: 46, weight: 600, fill: color, stroke: '#1d1410', lw: 11, alpha,
        shadow: 'rgba(0,0,0,0.35)', sx: 0, sy: 5,
      });
    });
  }

  window.F = {
    W, H, TL, TAU, clamp, lerp, inv, E, hash, noise, cue, line, S, End, P, win, talk, speaking,
    sceneAt, hex, mix, rgba, mixPal, applyCam, lerpCam, camPath, shake, hitShake,
    ellipse, circle, rrect, fillStroke, text, subtitles, FONT_TITLE, FONT_UI,
  };
})();
