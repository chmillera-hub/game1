'use strict';
// Fantasy-version compositor: generated stills with depth parallax, animated
// faces, per-shot effects, scripture, subtitles, title and end card.
//   node --expose-gc fantasy/render.js --build DIR --real DIR --from 0 --to 30 | ffmpeg -f image2pipe ...
//   node fantasy/render.js --build DIR --real DIR --stills 1,20 --outdir DIR
//   node fantasy/render.js --build DIR --real DIR --shots shots.json --export-poses poses.jsonl

const fs = require('fs');
const path = require('path');
// the canvas package is installed with the 2D renderer (render/node_modules)
const { createCanvas } = require('module').createRequire(path.join(__dirname, '..', 'render', 'package.json'))('@napi-rs/canvas');
const lib = (p) => require(path.join(__dirname, '..', 'render', 'lib', p));
const S = lib('stage');
const { photos } = lib('photos');
const { Subtitles, drawTitle, drawVerse, drawEndCard } = lib('text');
const { clamp, smooth, lerp, fbm } = lib('util');
const { loadDirection } = require('./direction');
const V = require('./vfx');

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const BUILD = args.build || '/opt/work/fantasy/build';
const REAL = args.real || '/opt/work/fantasy';
const FPS = 24;
const W = S.W, H = S.H;
const D = loadDirection(BUILD, REAL);
const { timeline, shots } = D;
const P = photos(REAL);

// ------------------------------------------------------------------ camera
// Each shot eases in over a little more than its length, so it is still moving
// when it cuts (or dissolves) away.
function camAt(sh, t) {
  const c = sh.cam;
  const u = smooth(clamp((t - sh.t) / (sh.t1 - sh.t + 1.5)));
  const z = lerp(c.z0, c.z1, u);
  const f0 = c.f || P.focus(sh.img), f1 = c.f1 || f0;
  let x = lerp(f0[0], f1[0], u), y = lerp(f0[1], f1[1], u);
  const hx = W / (2 * z), hy = H / (2 * z);
  x = clamp(x, hx, W - hx); y = clamp(y, hy, H - hy);
  let dx = 0, dy = 0;
  for (const [t0, dur, amp] of sh.shake || []) {
    const k = clamp(1 - (t - t0) / dur) * (t >= t0 ? 1 : 0);
    if (k > 0) { dx += amp * k * fbm(t * 23, 1); dy += amp * k * fbm(t * 23, 2); }
  }
  return { z, x, y, dx, dy, z0: c.z0 };
}
function applyCam(ctx, cam, z = cam.z) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.translate(W / 2 + cam.dx, H / 2 + cam.dy);
  ctx.scale(z, z);
  ctx.translate(-cam.x, -cam.y);
}
function cover(ctx, img) {
  const { s, ox, oy } = P.fit(img);
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, ox, oy, img.width * s, img.height * s);
}

// ------------------------------------------------------------------ depth parallax
// depth/<name>_mid.png and _near.png are alpha masks of the nearer parts of a
// still. During a push-in the nearer layers zoom a little faster than the
// photo behind them; growing layers never uncover anything, so no holes.
const maskCache = new Map();
function masks(name) {
  if (!maskCache.has(name)) {
    const out = [];
    for (const [suffix, k] of [['mid', 0.45], ['near', 1.0]]) {
      const p = path.join(REAL, 'depth', `${name}_${suffix}.png`);
      if (fs.existsSync(p)) out.push({ img: P.loadImg(p), k });
    }
    maskCache.set(name, out);
  }
  return maskCache.get(name);
}
function paintParallax(ctx, name, img, cam) {
  applyCam(ctx, cam);
  cover(ctx, img);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const ms = masks(name);
  if (!ms.length || cam.z <= cam.z0 + 1e-4) return;
  for (const m of ms) {
    const Lr = S.layer();
    const lc = Lr.getContext('2d');
    cover(lc, img);
    lc.globalCompositeOperation = 'destination-in';
    cover(lc, m.img);
    lc.globalCompositeOperation = 'source-over';
    applyCam(ctx, cam, cam.z * Math.pow(cam.z / cam.z0, 1.2 * m.k));
    ctx.drawImage(Lr, 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.release(Lr);
  }
}

// ------------------------------------------------------------------ special paints
// The hall splits along a jagged seam; the pieces drift apart over a chasm of
// light. A horizontal seam (y) parts the family across the table from Maya in
// the foreground; a vertical one (x) parts left from right.
function paintSplit(ctx, sh, t, img, cam) {
  const { t0 } = sh.split;
  const horiz = sh.split.y !== undefined;
  const at0 = horiz ? sh.split.y : sh.split.x;
  const Lr = S.layer();
  paintParallax(Lr.getContext('2d'), sh.img, img, cam);
  const sp = (t < t0 ? 0 : 1 - Math.pow(1 - clamp((t - t0) / 2.8), 3)) * 95;
  const seam = [];
  const span = horiz ? W : H;
  for (let u = -20; u <= span + 20; u += 60) {
    const off = fbm(u * 0.004, 9) * 70 + Math.sin(u * 0.013) * 18;
    seam.push(horiz ? [u, at0 + off] : [at0 + off, u]);
  }
  const piece = (side) => {
    ctx.save();
    ctx.beginPath();
    if (horiz) ctx.moveTo(-20, side < 0 ? -10 : H + 10); else ctx.moveTo(side < 0 ? -10 : W + 10, -20);
    for (const [x, y] of seam) ctx.lineTo(x, y);
    if (horiz) ctx.lineTo(W + 20, side < 0 ? -10 : H + 10); else ctx.lineTo(side < 0 ? -10 : W + 10, H + 20);
    ctx.closePath(); ctx.clip();
    if (horiz) ctx.drawImage(Lr, 0, side * sp); else ctx.drawImage(Lr, side * sp, 0);
    ctx.restore();
  };
  if (sp > 0.5) {
    // the chasm: dark, with light rising from deep inside
    ctx.fillStyle = '#05070c'; ctx.fillRect(0, 0, W, H);
    V.withAdd(ctx, () => {
      const g = horiz ? ctx.createLinearGradient(0, at0 - sp - 60, 0, at0 + sp + 60) : ctx.createLinearGradient(at0 - sp - 60, 0, at0 + sp + 60, 0);
      g.addColorStop(0, 'rgba(160,200,255,0)'); g.addColorStop(0.5, `rgba(225,238,255,${0.75 * clamp(sp / 60)})`); g.addColorStop(1, 'rgba(160,200,255,0)');
      ctx.fillStyle = g;
      if (horiz) ctx.fillRect(0, at0 - sp - 60, W, sp * 2 + 120); else ctx.fillRect(at0 - sp - 60, 0, sp * 2 + 120, H);
    });
  }
  piece(-1); piece(1);
  S.release(Lr);
  if (sp > 0.5) {
    const area = horiz ? { x0: 0, x1: W, y0: at0 - sp - 40, y1: at0 + sp + 40 } : { x0: at0 - sp - 40, x1: at0 + sp + 40, y0: 0, y1: H };
    V.motes(ctx, t, { n: 40, rgb: [230, 240, 255], alpha: 0.8, area, rise: horiz ? 30 : -160, size: 3, seed: 33 });
  }
}
// Seen through water: rippling strips, a cool tint, the round edge of the basin.
function paintWater(ctx, sh, t, img, cam) {
  const Lr = S.layer();
  paintParallax(Lr.getContext('2d'), sh.img, img, cam);
  V.rippleDraw(ctx, Lr, t, { amp: 6, strip: 10 });
  S.release(Lr);
  ctx.save();
  const g = ctx.createRadialGradient(W / 2, H * 0.42, H * 0.3, W / 2, H * 0.42, H * 0.62);
  g.addColorStop(0, 'rgba(5,10,20,0)'); g.addColorStop(1, 'rgba(5,10,20,0.85)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

function paintShot(ctx, sh, t) {
  const f = Math.round(t * FPS);
  const img = P.plate(sh.img, f);
  const cam = camAt(sh, t);
  ctx.save();
  if (sh.split) paintSplit(ctx, sh, t, img, cam);
  else if (sh.water) paintWater(ctx, sh, t, img, cam);
  else paintParallax(ctx, sh.img, img, cam);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  if (sh.fx) sh.fx(ctx, t, sh, cam);
  ctx.restore();
  S.vignette(ctx, 0.42);
}

// ------------------------------------------------------------------ overlays
const subs = new Subtitles(createCanvas(8, 8).getContext('2d'), timeline);
const verses = timeline.lines.filter((l) => l.verse);
const lastVerseOf = {};
for (const l of verses) lastVerseOf[l.scene] = l.id;
const sceneById = Object.fromEntries(timeline.scenes.map((s) => [s.id, s]));
function verseShade(ctx, a, y1 = 950) {
  if (a <= 0) return;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createLinearGradient(0, 0, 0, y1);
  g.addColorStop(0, `rgba(0,0,0,${0.62 * a})`); g.addColorStop(0.6, `rgba(0,0,0,${0.4 * a})`); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, y1);
  ctx.restore();
}
function drawVerses(ctx, t) {
  for (let i = 0; i < verses.length; i++) {
    const l = verses[i], next = verses[i + 1];
    const out = next && next.scene === l.scene ? next.start - 0.3 : l.end + 1.4;
    const a = clamp((t - (l.start - 0.5)) / 0.6) * (1 - clamp((t - out) / 0.6));
    if (a <= 0) continue;
    verseShade(ctx, a);
    const cite = lastVerseOf[l.scene] === l.id ? sceneById[l.scene].verse : undefined;
    drawVerse(ctx, l, t, { y: 330, size: l.text.length > 150 ? 50 : 56, cite, alpha: a });
  }
}

const frame = createCanvas(W, H);
const fctx = frame.getContext('2d');
const tEnd = D.end('N27', 0.8);
function renderFrame(t) {
  const ctx = fctx;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const i = D.shotIndex(t);
  const sh = shots[i];
  paintShot(ctx, sh, t);
  const [type, d] = sh.trans || ['cut', 0];
  if (i > 0 && type === 'dissolve' && t < sh.t + d) {
    const Lr = S.layer();
    paintShot(Lr.getContext('2d'), shots[i - 1], t);
    ctx.save(); ctx.globalAlpha = 1 - smooth((t - sh.t) / d); ctx.drawImage(Lr, 0, 0); ctx.restore();
    S.release(Lr);
  }
  if (type === 'flash' && t < sh.t + d) V.flash(ctx, Math.pow(1 - (t - sh.t) / d, 2) * 0.95);
  drawVerses(ctx, t);
  drawTitle(ctx, 1 - smooth((t - 3.8) / 1.0));
  const endA = clamp((t - tEnd) / 1.2);
  if (endA > 0) { ctx.fillStyle = `rgba(20,10,5,${0.35 * endA})`; ctx.fillRect(0, 0, W, H); drawEndCard(ctx, endA); }
  else subs.draw(ctx, t, 1440);
  return frame;
}
async function frameAt(t) {
  renderFrame(t);
  if (P.pending.size) { await P.settle(); renderFrame(t); }
  return frame;
}

// ------------------------------------------------------------------ poses for the face renderer
const POSE_KEYS = ['yaw', 'pitch', 'roll', 'headX', 'headY', 'gazeX', 'gazeY', 'blink', 'lid', 'lidL', 'lidR', 'squint',
  'wide', 'browIn', 'browOut', 'browKnit', 'browTalk', 'smile', 'open', 'mouthWide', 'round', 'press', 'jawOpen', 'wet',
  'blush', 'slump', 'shoulderUp', 'breath', 'asym'];
function exportPoses(file, shotsFile) {
  const faces = Object.fromEntries(JSON.parse(fs.readFileSync(shotsFile, 'utf8')).map((s) => [s.id, s.faces || []]));
  const out = fs.openSync(file, 'w');
  const n1 = Math.round((timeline.duration + 0.5) * FPS);
  for (let n = 0; n < n1; n++) {
    const t = n / FPS;
    const i = D.shotIndex(t);
    const sh = shots[i];
    const imgs = [sh.img];
    // a dissolving shot keeps acting until it has gone
    if (i > 0 && sh.trans && sh.trans[0] === 'dissolve' && t < sh.t + sh.trans[1]) imgs.push(shots[i - 1].img);
    const actors = {};
    for (const img of imgs) {
      for (const [scene, who] of faces[img] || []) {
        const key = `${scene}:${who}`;
        const a = D.actors[key];
        if (!a || actors[key]) continue;
        const Pz = a.pose(t);
        const o = {};
        for (const k of POSE_KEYS) o[k] = Math.round((Pz[k] || 0) * 1000) / 1000;
        actors[key] = o;
      }
    }
    fs.writeSync(out, JSON.stringify({ f: n, t: Math.round(t * 1000) / 1000, scene: D.sceneAt(t).id, shot: `${i}:${sh.img}`,
      real: [...new Set(imgs)].map((img) => ({ img })), actors }) + '\n');
  }
  fs.closeSync(out);
  console.error('exported', n1, 'frames');
}

async function main() {
  if (args['export-poses']) return exportPoses(args['export-poses'], args.shots || path.join(REAL, 'shots.json'));
  await P.preload();
  if (args.stills) {
    const out = args.outdir || path.join(REAL, 'stills');
    fs.mkdirSync(out, { recursive: true });
    for (const s of args.stills.split(',')) {
      const t = parseFloat(s);
      const p = path.join(out, `fantasy_${t.toFixed(2)}.png`);
      fs.writeFileSync(p, (await frameAt(t)).toBuffer('image/png'));
      console.error('wrote', p);
    }
    return;
  }
  const from = parseFloat(args.from || 0);
  const to = Math.min(parseFloat(args.to || timeline.duration), timeline.duration + 0.5);
  const n0 = Math.round(from * FPS), n1 = Math.round(to * FPS);
  const t0 = Date.now();
  for (let n = n0; n < n1; n++) {
    fs.writeSync(1, (await frameAt(n / FPS)).encodeSync('jpeg', 97));
    if (global.gc && n % 12 === 0) global.gc();
    if ((n - n0) % 120 === 0) console.error(`frame ${n} (${((Date.now() - t0) / Math.max(1, n - n0 + 1)).toFixed(0)} ms/f, rss ${(process.memoryUsage().rss / 1e9).toFixed(2)} GB)`);
  }
}
main().catch((e) => { console.error(e); process.exit(1); });
