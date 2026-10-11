// Frame renderer.
//   node src/render.mjs --from 0 --to 480 --out out/seg.mp4     render frames [from,to) to an intermediate video
//   node src/render.mjs --stills 3.5,10,42 --outdir out/stills    render PNG stills at given seconds
//   node src/render.mjs --sheet s05 [--n 12] --out out/s05.png     contact sheet of one scene (labelled thumbnails)
//   node src/render.mjs --sheet s05 --times 101.2,103,104.5 ...    contact sheet at explicit times
//   node src/render.mjs --place-subs                               choose caption positions that avoid faces
// All times on the command line are PLAY time (the film as heard); add --story to give story-time values
// (data/timeline.json, which scene code is authored against). --nosubs renders without captions.
// Scene modules live in src/scenes/*.mjs and export { id, render(g, t, S) }.

import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { W, H, FPS, clamp } from './engine.mjs';
import { loadTimeline, makeScene, playToStory, storyToPlay, playTimeline } from './timeline.mjs';
import { drawSubtitles, loadSubtitles, captionRect } from './subtitles.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
for (const [f, name] of [['Caveat.ttf', 'Caveat'], ['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand']]) {
  const p = path.join(ROOT, 'assets/fonts', f);
  if (fs.existsSync(p)) GlobalFonts.registerFromPath(p, name);
}

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => {
  if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
  return acc;
}, []));

const TL = loadTimeline(args.timeline ? path.resolve(args.timeline) : undefined);
const sceneMods = {};
for (const f of fs.readdirSync(path.join(ROOT, 'src/scenes')).filter((f) => f.endsWith('.mjs')).sort()) {
  const m = await import(pathToFileURL(path.join(ROOT, 'src/scenes', f)).href);
  if (m.id && m.render) sceneMods[m.id] = m;
}
const helpers = {};
const helper = (id) => (helpers[id] ||= makeScene(id));

const DISSOLVE = 0.9;

function placeholder(g, sc, t) {
  g.fillStyle = '#22203a';
  g.fillRect(0, 0, W, H);
  g.fillStyle = '#fff';
  g.font = '34px Inter';
  g.fillText(`${sc.id} ${sc.slug || ''}`, 40, 90);
  const S = helper(sc.id);
  const b = TL.beats[S.current(t)];
  g.font = '26px Inter';
  wrap(g, b ? `${b.speaker || b.kind}: ${b.text || ''}` : '', 40, 160, W - 80, 36);
}
function wrap(g, text, x, y, maxW, lh) {
  const words = text.split(' ');
  let line = '';
  for (const w of words) {
    if (g.measureText(line + w).width > maxW) { g.fillText(line, x, y); y += lh; line = ''; }
    line += w + ' ';
  }
  g.fillText(line, x, y);
}

function drawScene(g, sc, t) {
  g.save();
  const m = sceneMods[sc.id];
  try {
    if (m) m.render(g, t, helper(sc.id));
    else placeholder(g, sc, t);
  } catch (err) {
    console.error(`scene ${sc.id} t=${t.toFixed(2)}:`, err.stack || err);
    placeholder(g, sc, t);
  }
  g.restore();
}

const canvas = createCanvas(W, H);
const g = canvas.getContext('2d');
const tmp = createCanvas(W, H);
const gt = tmp.getContext('2d');
globalThis.__FACE_CANVASES = new Set([canvas, tmp]);
loadSubtitles();
const toPlay = (x) => (args.story ? storyToPlay(x) : x);

/** render the frame at PLAY time tp: scenes are evaluated at story time, captions at play time */
export function renderFrame(tp, opts = {}) {
  const t = playToStory(tp);
  renderStory(t);
  if (opts.subs !== false && !args.nosubs) drawSubtitles(g, tp);
  return canvas;
}

function renderStory(t) {
  const scenes = TL.scenes;
  let i = scenes.findIndex((s) => t >= s.start && t < s.end);
  if (i < 0) i = t < scenes[0].start ? 0 : scenes.length - 1;
  const sc = scenes[i];
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = 1;
  g.globalCompositeOperation = 'source-over';
  const dis = sc.transition_in === 'dissolve' && i > 0 ? (sc.transition_dur || DISSOLVE) : 0;
  if (dis && t < sc.start + dis) {
    drawScene(g, scenes[i - 1], t);
    gt.setTransform(1, 0, 0, 1, 0, 0);
    gt.clearRect(0, 0, W, H);
    drawScene(gt, sc, t);
    g.globalAlpha = clamp((t - sc.start) / dis);
    // Skia's default 8-bit blend rounds translucent draws one way (a visible 1-level jump on the first
    // dissolve frame); the high-quality path blends in float.
    g.imageSmoothingQuality = 'high';
    g.drawImage(tmp, 0, 0);
    g.imageSmoothingQuality = 'low';
    g.globalAlpha = 1;
  } else {
    drawScene(g, sc, t);
  }
  return canvas;
}

async function renderVideo(from, to, out) {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '6', '-pix_fmt', 'yuv444p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = from; f < to; f++) {
    renderFrame(f / FPS);
    const data = g.getImageData(0, 0, W, H).data;
    if (!ff.stdin.write(Buffer.from(data.buffer, data.byteOffset, data.byteLength))) await new Promise((r) => ff.stdin.once('drain', r));
    if ((f - from) % 240 === 0) console.error(`[${out}] frame ${f}/${to} ${((Date.now() - t0) / (f - from + 1)).toFixed(1)} ms/f`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
}

async function main() {
  if (args.stills) {
    const dir = args.outdir || path.join(ROOT, 'out/stills');
    fs.mkdirSync(dir, { recursive: true });
    for (const s of String(args.stills).split(',')) {
      const t = parseFloat(s);
      renderFrame(toPlay(t));
      fs.writeFileSync(path.join(dir, `still_${t.toFixed(2)}.png`), canvas.toBuffer('image/png'));
    }
    return;
  }
  if (args.sheet) {
    const sc = playTimeline().scenes.find((s) => s.id === args.sheet);
    let times;
    if (args.times) times = String(args.times).split(',').map(Number).map(toPlay);
    else {
      const n = parseInt(args.n || 12);
      times = Array.from({ length: n }, (_, i) => sc.start + (sc.end - sc.start) * (i + 0.5) / n);
    }
    const cols = Math.min(4, times.length), rows = Math.ceil(times.length / cols);
    const tw = 270, th = 480;
    const sheet = createCanvas(cols * tw, rows * (th + 26));
    const gs = sheet.getContext('2d');
    gs.fillStyle = '#111'; gs.fillRect(0, 0, sheet.width, sheet.height);
    times.forEach((t, i) => {
      renderFrame(t);
      const x = (i % cols) * tw, y = Math.floor(i / cols) * (th + 26);
      gs.drawImage(canvas, x, y + 26, tw, th);
      gs.fillStyle = '#fff'; gs.font = '15px Inter';
      const S = helper(sc.id);
      gs.fillText(`${t.toFixed(1)}s ${S.current(playToStory(t))}`, x + 4, y + 18);
    });
    fs.writeFileSync(args.out || path.join(ROOT, `out/sheet_${sc.id}.png`), sheet.toBuffer('image/png'));
    return;
  }
  if (args['place-subs']) return placeSubs();
  const from = parseInt(args.from || 0);
  const to = parseInt(args.to || Math.ceil(playTimeline().duration * FPS));
  await renderVideo(from, to, args.out || path.join(ROOT, 'out/render.mp4'));
}
/** For each caption, render frames across its span, collect on-screen face boxes, and pick the placement
 *  (low / top / mid) that covers none of them; keep the previous placement within a scene when it is free. */
function placeSubs() {
  const caps = loadSubtitles();
  let prevPos = 'low', prevScene = null;
  const counts = {};
  for (const c of caps) {
    if (c.pos_override) { // manual placement (data/subtitle_overrides.json) wins and sets the scene's running position
      c.pos = c.pos_override; c.pos_overlap = 0;
      counts[c.pos] = (counts[c.pos] || 0) + 1;
      prevPos = c.pos; prevScene = c.scene;
      continue;
    }
    const n = Math.max(3, Math.ceil((c.end - c.start) / 0.45) + 1);
    const faces = [];
    for (let i = 0; i < n; i++) {
      const t = c.start + 0.04 + (c.end - c.start - 0.08) * (i / (n - 1));
      globalThis.__FACE_LOG = [];
      renderFrame(t, { subs: false });
      faces.push(...globalThis.__FACE_LOG);
    }
    globalThis.__FACE_LOG = null;
    // on-screen faces; a hood opening that fills most of the frame is a backdrop, not something to avoid
    const vis = faces.filter((f) => f.x1 > 0 && f.x0 < W && f.y1 > 0 && f.y0 < H &&
      !(f.void && (Math.min(f.x1, W) - Math.max(f.x0, 0)) * (Math.min(f.y1, H) - Math.max(f.y0, 0)) > 0.35 * W * H));
    const overlap = (pos) => {
      const r = captionRect(g, c, pos);
      let a = 0;
      for (const f of vis) {
        const ix = Math.max(0, Math.min(r.x1 + 10, f.x1) - Math.max(r.x0 - 10, f.x0));
        const iy = Math.max(0, Math.min(r.y1 + 10, f.y1) - Math.max(r.y0 - 10, f.y0));
        a += ix * iy;
      }
      return a;
    };
    const base = ['low', 'top', 'upper', 'mid'];
    const order = prevScene === c.scene && prevPos !== 'low' ? [prevPos, ...base.filter((p) => p !== prevPos)] : base;
    let best = null, bestO = Infinity;
    for (const p of order) {
      const o = overlap(p);
      if (o === 0) { best = p; bestO = 0; break; }
      if (o < bestO) { best = p; bestO = o; }
    }
    c.pos = best;
    c.pos_overlap = Math.round(bestO);
    counts[best] = (counts[best] || 0) + 1;
    prevPos = best; prevScene = c.scene;
  }
  fs.writeFileSync(path.join(ROOT, 'data/subtitles.json'), JSON.stringify({ captions: caps }, null, 1));
  const covered = caps.filter((c) => c.pos_overlap > 0).map((c) => `${c.beat}:${c.idx}`);
  console.log('placements', counts, covered.length ? `still overlapping a face: ${covered.join(' ')}` : 'no caption covers a face');
}

await main();
