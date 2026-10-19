'use strict';
// Frame renderer.
//   node main.js --build DIR --stills 1.5,20,33 --outdir DIR     (PNG previews)
//   node main.js --build DIR --from 0 --to 30 --fps 24 > raw.rgba (raw RGBA frames)
const fs = require('fs');
const path = require('path');
const { createCanvas } = require('@napi-rs/canvas');
const S = require('./lib/stage');
const { Actor } = require('./lib/anim');
const { makeCast, BASE, OUTFITS } = require('./lib/cast');
const { Subtitles, drawTitle, wordTimes } = require('./lib/text');
const { clamp, smooth } = require('./lib/util');

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const BUILD = args.build || '/opt/work/build';
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

const SCENES = ['table', 'sword', 'mask', 'cross', 'office', 'park', 'sparrows', 'call', 'road', 'epilogue'];
const scenes = [];
for (const id of SCENES) {
  const f = path.join(__dirname, 'scenes', id + '.js');
  if (fs.existsSync(f)) scenes.push(require(f)(env));
}
// Transitions into each scene: crossfade where compositions differ, a brief dip
// through near-black where two close-ups would otherwise ghost over each other.
const TRANS = {
  sword: ['dissolve', 0.9], mask: ['dip', 1.0], cross: ['cut', 0], office: ['dip', 0.6], park: ['dip', 0.9],
  sparrows: ['dissolve', 0.8], call: ['dip', 1.0], road: ['dissolve', 1.0], epilogue: ['dissolve', 1.2],
};

const frame = createCanvas(S.W, S.H);
const fctx = frame.getContext('2d');
const subs = new Subtitles(fctx, timeline);

function sceneAt(t) {
  for (let i = scenes.length - 1; i >= 0; i--) if (t >= scenes[i].start) return i;
  return 0;
}
function renderScene(ctx, sc, t) {
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.filter = 'none'; ctx.globalCompositeOperation = 'source-over';
  sc.draw(ctx, t);
  ctx.restore();
}

function renderFrame(t) {
  const ctx = fctx;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, S.W, S.H);
  const i = sceneAt(t);
  const sc = scenes[i];
  renderScene(ctx, sc, t);
  const [type, d] = TRANS[sc.id] || ['cut', 0];
  if (i > 0 && type === 'dissolve' && t < sc.start + d) {
    const prev = scenes[i - 1];
    const Lr = S.layer();
    renderScene(Lr.getContext('2d'), prev, t);
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
  const ta = 1 - smooth((t - 3.6) / 1.0);
  drawTitle(ctx, ta);
  if (!sc.subs || sc.subs(t) !== false) subs.draw(ctx, t, sc.subY ? sc.subY(t) : 1440);
  return frame;
}

if (args.stills) {
  const out = args.outdir || '/opt/work/stills';
  fs.mkdirSync(out, { recursive: true });
  for (const s of args.stills.split(',')) {
    const t = parseFloat(s);
    const c = renderFrame(t);
    const f = path.join(out, `still_${t.toFixed(2)}.png`);
    fs.writeFileSync(f, c.toBuffer('image/png'));
    console.error('wrote', f);
  }
} else {
  const fps = parseFloat(args.fps || 24);
  const from = parseFloat(args.from || 0);
  const to = Math.min(parseFloat(args.to || timeline.duration), timeline.duration + 0.5);
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps);
  const t0 = Date.now();
  for (let n = n0; n < n1; n++) {
    const c = renderFrame(n / fps);
    const buf = c.data();
    fs.writeSync(1, buf);
    if ((n - n0) % 120 === 0) console.error(`frame ${n} (${((Date.now() - t0) / Math.max(1, n - n0 + 1)).toFixed(0)} ms/f)`);
  }
}
