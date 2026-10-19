'use strict';
// Loads a build (timeline + lip-sync), builds the shared direction (actors,
// scenes, shot lists) and composes frames: scene drawing, transitions, the
// opening title and subtitles. Both the 2D renderer and the realistic
// compositor use this; they differ only in how a scene is drawn.

const fs = require('fs');
const path = require('path');
const { createCanvas } = require('@napi-rs/canvas');
const S = require('./stage');
const { Actor } = require('./anim');
const { makeCast, BASE, OUTFITS } = require('./cast');
const { Subtitles, drawTitle, wordTimes } = require('./text');
const { smooth } = require('./util');

const SCENES = ['table', 'sword', 'mask', 'cross', 'office', 'park', 'sparrows', 'call', 'road', 'epilogue'];
// Transitions into each scene: crossfade where compositions differ, a brief dip
// through near-black where two close-ups would otherwise ghost over each other.
const TRANS = {
  sword: ['dissolve', 0.9], mask: ['dip', 1.0], cross: ['cut', 0], office: ['dip', 0.6], park: ['dip', 0.9],
  sparrows: ['dissolve', 0.8], call: ['dip', 1.0], road: ['dissolve', 1.0], epilogue: ['dissolve', 1.2],
};

function loadProject(BUILD) {
  const timeline = JSON.parse(fs.readFileSync(path.join(BUILD, 'timeline.json'), 'utf8'));
  const lips = JSON.parse(fs.readFileSync(path.join(BUILD, 'lipsync.json'), 'utf8'));
  const lineById = Object.fromEntries(timeline.lines.map((l) => [l.id, { ...l, dur: l.end - l.start }]));
  const sceneById = Object.fromEntries(timeline.scenes.map((s) => [s.id, s]));
  const wtCache = {};
  const cast = makeCast();
  const env = {
    timeline, lips, cast,
    L: (id) => { const l = lineById[id]; if (!l) throw new Error('no line ' + id); return l; },
    W: (id, i) => {
      const l = env.L(id);
      const wt = (wtCache[id] ||= wordTimes(l));
      return wt[Math.max(0, Math.min(wt.length - 1, i))].s;
    },
    scene: (id) => sceneById[id],
    castFor: (who, outfit) => {
      const A = { ...BASE[who] };
      if (outfit && OUTFITS[who] && OUTFITS[who][outfit]) A.outfit = OUTFITS[who][outfit];
      return A;
    },
    actor: (who, outfit, opts = {}) => {
      const a = new Actor(who + (outfit ? ':' + outfit : ''), env.castFor(who, outfit), { seed: opts.seed, ...opts });
      for (const l of timeline.lines) if (l.who === who && lips[l.id]) a.say(l.start, lips[l.id], l.end - l.start);
      return a;
    },
    cuts: (list) => (t) => {
      let k = 0;
      for (let i = 0; i < list.length; i++) if (t >= list[i][0]) k = i;
      return { name: list[k][1], t0: list[k][0], t1: k + 1 < list.length ? list[k + 1][0] : list[k][0] + 30, i: k };
    },
  };
  const scenes = [];
  for (const id of SCENES) {
    const f = path.join(__dirname, '..', 'scenes', id + '.js');
    if (fs.existsSync(f)) scenes.push(require(f)(env));
  }
  const subs = new Subtitles(createCanvas(8, 8).getContext('2d'), timeline);
  const sceneAt = (t) => {
    for (let i = scenes.length - 1; i >= 0; i--) if (t >= scenes[i].start) return i;
    return 0;
  };

  // drawScene(ctx, scene, t, index) paints one scene; this adds transitions and overlays.
  function compose(ctx, t, drawScene) {
    const paint = (c, sc, idx) => {
      c.save();
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.globalAlpha = 1; c.filter = 'none'; c.globalCompositeOperation = 'source-over';
      drawScene(c, sc, t, idx);
      c.restore();
    };
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, S.W, S.H);
    const i = sceneAt(t);
    const sc = scenes[i];
    paint(ctx, sc, i);
    const [type, d] = TRANS[sc.id] || ['cut', 0];
    if (i > 0 && type === 'dissolve' && t < sc.start + d) {
      const Lr = S.layer();
      paint(Lr.getContext('2d'), scenes[i - 1], i - 1);
      ctx.save();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1 - smooth((t - sc.start) / d);
      ctx.drawImage(Lr, 0, 0);
      ctx.restore();
      S.release(Lr);
    }
    // dips: darken into the boundary (end of this scene's predecessor) and out of it
    const dip = (k) => { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = `rgba(4,3,2,${0.94 * k})`; ctx.fillRect(0, 0, S.W, S.H); ctx.restore(); };
    if (type === 'dip' && t < sc.start + d / 2) dip(1 - smooth((t - sc.start) / (d / 2)));
    const next = scenes[i + 1];
    if (next) {
      const [nt, nd] = TRANS[next.id] || ['cut', 0];
      if (nt === 'dip' && t > next.start - nd / 2) dip(smooth((t - (next.start - nd / 2)) / (nd / 2)));
    }
    // title card on the opening (visible on the very first frame)
    drawTitle(ctx, 1 - smooth((t - 3.6) / 1.0));
    if (!sc.subs || sc.subs(t) !== false) subs.draw(ctx, t, sc.subY ? sc.subY(t) : 1440);
  }

  return { timeline, lips, env, scenes, sceneAt, subs, compose, TRANS };
}

// Stream frames [from, to) as JPEG (q97) to stdout. In this canvas build,
// canvas.data() and getImageData() leak a frame of native memory per call;
// encodeSync does not.
function streamFrames(renderFrame, from, to, fps) {
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps);
  const t0 = Date.now();
  for (let n = n0; n < n1; n++) {
    const c = renderFrame(n / fps, n);
    fs.writeSync(1, c.encodeSync('jpeg', 97));
    if (global.gc && n % 12 === 0) global.gc();   // canvas objects hold native memory V8 cannot see
    if ((n - n0) % 120 === 0) console.error(`frame ${n} (${((Date.now() - t0) / Math.max(1, n - n0 + 1)).toFixed(0)} ms/f, rss ${(process.memoryUsage().rss / 1e9).toFixed(2)} GB)`);
  }
}

module.exports = { loadProject, streamFrames, SCENES, TRANS };
