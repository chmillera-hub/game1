'use strict';
// 2D renderer.
//   node main.js --build DIR --stills 1.5,20,33 --outdir DIR [--raw 1]   (PNG previews; raw = scene only)
//   node --expose-gc main.js --build DIR --from 0 --to 30 --fps 24 | ffmpeg -f image2pipe -c:v mjpeg -framerate 24 -i - ...
//   node main.js --build DIR --export-poses poses.jsonl           (per-frame performance for the realistic version)
const fs = require('fs');
const path = require('path');
const { createCanvas } = require('@napi-rs/canvas');
const S = require('./lib/stage');
const { loadProject, streamFrames } = require('./lib/project');
const { realLayers } = require('./realistic/cuts');

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const project = loadProject(args.build || '/opt/work/build');
const { timeline, env, scenes, sceneAt, compose } = project;

const frame = createCanvas(S.W, S.H);
const fctx = frame.getContext('2d');
function renderFrame(t) {
  compose(fctx, t, (ctx, sc, tt) => sc.draw(ctx, tt));
  return frame;
}

const POSE_KEYS = ['yaw', 'pitch', 'roll', 'headX', 'headY', 'gazeX', 'gazeY', 'blink', 'lid', 'lidL', 'lidR', 'squint',
  'wide', 'browIn', 'browOut', 'browKnit', 'browTalk', 'smile', 'open', 'mouthWide', 'round', 'press', 'jawOpen', 'wet',
  'blush', 'slump', 'shoulderUp', 'breath', 'asym'];

if (args['export-poses']) {
  // Per-frame performance of every on-screen actor, for driving the realistic faces.
  const fps = parseFloat(args.fps || 24);
  const out = fs.openSync(args['export-poses'], 'w');
  const n1 = Math.round((timeline.duration + 0.5) * fps);
  for (let n = 0; n < n1; n++) {
    const t = n / fps;
    const sc = scenes[sceneAt(t)];
    const sh = sc.shotAt ? sc.shotAt(t) : { name: sc.id, t0: sc.start, t1: sc.end };
    const actors = {};
    for (const [name, a] of Object.entries(sc.actors || {})) {
      if (!a || !a.pose || !a.A || Object.keys(a.A).length === 0) continue;
      const P = a.pose(t);
      const o = {};
      for (const k of POSE_KEYS) o[k] = Math.round((P[k] || 0) * 1000) / 1000;
      if (P.tears && P.tears.length) o.tears = P.tears.map((x) => ({ side: x.side, t: Math.round(x.t * 100) / 100, a: Math.round(x.a * 100) / 100 }));
      actors[name] = o;
    }
    const real = realLayers(env, sc, sh, t);
    fs.writeSync(out, JSON.stringify({ f: n, t: Math.round(t * 1000) / 1000, scene: sc.id, shot: sh.name, s0: sh.t0, s1: sh.t1, real, actors }) + '\n');
  }
  fs.closeSync(out);
  console.error('exported', n1, 'frames');
} else if (args.stills) {
  const out = args.outdir || '/opt/work/stills';
  fs.mkdirSync(out, { recursive: true });
  for (const s of args.stills.split(',')) {
    const t = parseFloat(s);
    const f = path.join(out, `still_${t.toFixed(2)}.png`);
    if (args.raw) {
      // the scene alone: no title, subtitles or transitions (layouts for the realistic stills)
      fctx.setTransform(1, 0, 0, 1, 0, 0);
      fctx.fillStyle = '#000'; fctx.fillRect(0, 0, S.W, S.H);
      scenes[sceneAt(t)].draw(fctx, t);
    } else renderFrame(t);
    fs.writeFileSync(f, frame.toBuffer('image/png'));
    console.error('wrote', f);
  }
} else {
  const fps = parseFloat(args.fps || 24);
  const from = parseFloat(args.from || 0);
  const to = Math.min(parseFloat(args.to || timeline.duration), timeline.duration + 0.5);
  streamFrames(renderFrame, from, to, fps);
}
