'use strict';
// Realistic-version compositor: photographs (with LivePortrait-animated faces)
// + camera moves, effects, scripture, subtitles and UI, on the same timeline.
//   node --expose-gc main_real.js --build DIR --real DIR --from 0 --to 30 | ffmpeg -f image2pipe ...
//   node main_real.js --build DIR --real DIR --stills 1,20 --outdir DIR
const fs = require('fs');
const path = require('path');
const { createCanvas, Image } = require('@napi-rs/canvas');
const S = require('./lib/stage');
const N = require('./lib/sets_night');
const { loadProject } = require('./lib/project');
const { realLayers } = require('./realistic/cuts');
const { drawVerse, drawEndCard } = require('./lib/text');
const { clamp, smooth, lerp, easeOut, fbm } = require('./lib/util');
const { roundRect } = require('./lib/body');

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
const project = loadProject(args.build || '/opt/work/build_final');
const { timeline, env, scenes, compose } = project;
const REAL = args.real || '/opt/work/real';
const FPS = 24;
const W = S.W, H = S.H;

// ------------------------------------------------------------------ images
// Photos stay at their generated size and are cover-fitted onto the frame; an
// animated frame is the photo with that frame's face patch on top.
// Images decode off-thread: width/height are known at once but the pixels only
// after onload, so drawing in the same tick paints nothing. Photos are preloaded;
// a frame that needs a not-yet-decoded patch is drawn again once it is ready.
const pending = new Set();
function loadImg(p) {
  const img = new Image();
  img.ready = false;
  const pr = new Promise((resolve) => { img.onload = () => { img.ready = true; resolve(); }; img.onerror = () => resolve(); });
  pending.add(pr);
  pr.then(() => pending.delete(pr));
  img.src = fs.readFileSync(p);
  return img;
}
const baseCache = new Map();
const meta = {};
function base(name) {
  if (!baseCache.has(name)) {
    const p = path.join(REAL, 'base', name + '.jpg');
    if (fs.existsSync(p)) baseCache.set(name, loadImg(p));
    else {
      // previews while photos are still being made: a gray stand-in
      console.error('missing photo', name);
      const c = createCanvas(768, 1344); const x = c.getContext('2d');
      x.fillStyle = '#3a3a40'; x.fillRect(0, 0, 768, 1344);
      baseCache.set(name, c);
    }
  }
  return baseCache.get(name);
}
function faceInfo(name) {
  if (!(name in meta)) {
    const p = path.join(REAL, 'base', name + '.json');
    meta[name] = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : { faces: [] };
  }
  return meta[name];
}
function fit(img) {
  const s = Math.max(W / img.width, H / img.height);
  return { s, ox: (W - img.width * s) / 2, oy: (H - img.height * s) / 2 };
}
// The animated photo for frame f: the photo with the face patch saved at or
// before f. Between two patches the face crossfades when the later one was a
// small step (smooth drift, speech on twos) and holds when it was a jump (a
// blink must not start early) or begins a new run. During dissolves a scene is
// drawn a little past its last patch; it holds that patch.
const plates = new Map();
const patchCache = new Map();
function patchImg(name, f) {
  const p = path.join(REAL, 'plates', name, String(f).padStart(5, '0') + '.jpg');
  let img = patchCache.get(p);
  if (!img) {
    img = loadImg(p);
    patchCache.set(p, img);
    if (patchCache.size > 24) patchCache.delete(patchCache.keys().next().value);
  }
  return img;
}
function plate(name, f) {
  const b = base(name);
  let e = plates.get(name);
  if (e === undefined) {
    const dir = path.join(REAL, 'plates', name);
    const ip = path.join(dir, 'index.json');
    e = fs.existsSync(ip) ? { ...JSON.parse(fs.readFileSync(ip, 'utf8')), box: JSON.parse(fs.readFileSync(path.join(dir, 'box.json'), 'utf8')).box, key: '', cv: null } : null;
    plates.set(name, e);
  }
  if (!e || !e.frames.length || f < e.frames[0]) return b;
  // last saved patch at or before f
  let lo = 0, hi = e.frames.length - 1;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (e.frames[mid] <= f) lo = mid; else hi = mid - 1; }
  const f0 = e.frames[lo];
  if (f - f0 > 72) return b;
  const f1 = e.frames[lo + 1];
  const blend = f1 !== undefined && f > f0 && (e.why[lo + 1] === 'step' || e.why[lo + 1] === 'hold') ? (f - f0) / (f1 - f0) : 0;
  const key = f0 + ':' + blend.toFixed(3);
  if (e.key !== key) {
    e.cv ||= createCanvas(b.width, b.height);
    const c = e.cv.getContext('2d');
    c.globalAlpha = 1;
    c.drawImage(b, 0, 0);
    const p0 = patchImg(name, f0), p1 = blend > 0 ? patchImg(name, f1) : null;
    c.drawImage(p0, e.box[0], e.box[1]);
    if (p1) { c.globalAlpha = blend; c.drawImage(p1, e.box[0], e.box[1]); c.globalAlpha = 1; }
    e.key = p0.ready && (!p1 || p1.ready) ? key : '';
  }
  return e.cv;
}
function drawPhoto(ctx, img, cam) {
  S.applyCam(ctx, cam);
  const { s, ox, oy } = fit(img);
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, ox, oy, img.width * s, img.height * s);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}
// Focus point for a push-in (frame coordinates): the first face, else upper middle.
function focus(name) {
  const m = faceInfo(name);
  if (m.faces && m.faces.length) {
    const b = m.faces[0].bbox;
    const s = Math.max(W / m.w, H / m.h), ox = (W - m.w * s) / 2, oy = (H - m.h * s) / 2;
    return [ox + s * (b[0] + b[2]) / 2, oy + s * ((b[1] + b[3]) / 2 + (b[3] - b[1]) * 0.3)];
  }
  return [W / 2, H * 0.45];
}
function push(name, t, t0, t1, z1 = 1.06) {
  const [fx, fy] = focus(name);
  return S.push(t, t0, t1, 1.0, z1, fx, fy);
}

// ------------------------------------------------------------------ effects
function grade(ctx, rgb, a) {
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}
// A soft dark band behind the scripture at the top of the frame: photographs
// are brighter and busier there than the 2D backdrops were.
function verseShade(ctx, a, y1 = 900) {
  if (a <= 0) return;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createLinearGradient(0, 0, 0, y1);
  g.addColorStop(0, `rgba(0,0,0,${0.62 * a})`); g.addColorStop(0.6, `rgba(0,0,0,${0.4 * a})`); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, y1);
  ctx.restore();
}
function flash(ctx, k, rgb = [255, 235, 200]) {
  if (k <= 0) return;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${0.75 * k * k})`; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}
function drawBlade(ctx, x, tipY, t) {
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  const len = 1150, top = tipY - len;
  const shimmer = 0.85 + 0.15 * Math.sin(t * 9);
  const glow = ctx.createLinearGradient(x - 80, 0, x + 80, 0);
  glow.addColorStop(0, 'rgba(255,160,80,0)'); glow.addColorStop(0.5, `rgba(255,210,150,${0.55 * shimmer})`); glow.addColorStop(1, 'rgba(255,160,80,0)');
  ctx.fillStyle = glow; ctx.fillRect(x - 80, top, 160, len);
  ctx.fillStyle = 'rgba(255,248,230,0.95)';
  ctx.beginPath(); ctx.moveTo(x - 13, top + 140); ctx.lineTo(x + 13, top + 140); ctx.lineTo(x + 9, tipY - 60); ctx.lineTo(x, tipY); ctx.lineTo(x - 9, tipY - 60); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,220,170,0.95)';
  ctx.fillRect(x - 85, top + 120, 170, 22);
  ctx.fillRect(x - 9, top, 18, 120);
  ctx.beginPath(); ctx.arc(x, top - 6, 20, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

// The reflection is seen through glass: cooler, a soft sheen, the mirror's edge.
function mirrorGlass(ctx) {
  grade(ctx, [150, 190, 225], 0.2);
  ctx.save();
  const g = ctx.createLinearGradient(0, 0, W, H * 0.7);
  g.addColorStop(0, 'rgba(255,255,255,0.12)'); g.addColorStop(0.3, 'rgba(255,255,255,0)');
  g.addColorStop(0.52, 'rgba(255,255,255,0.06)'); g.addColorStop(0.6, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const fr = ctx.createLinearGradient(0, 0, 40, 0);
  fr.addColorStop(0, '#1d2126'); fr.addColorStop(0.45, '#8e979f'); fr.addColorStop(0.75, '#cdd4da'); fr.addColorStop(1, '#3d434a');
  ctx.fillStyle = fr; ctx.fillRect(0, 0, 40, H);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(40, 0, 6, H);
  ctx.restore();
}

// Phone screens float over a blurred, dimmed photo of the room they are in.
// drawUI paints the 2D phone screen; only the phone body (clip) is kept.
function blurredPhoto(ctx, name, dim) {
  ctx.drawImage(S.cachedBg('real:' + name, (c) => {
    const img = base(name);
    const { s, ox, oy } = fit(img);
    c.drawImage(img, ox, oy, img.width * s, img.height * s);
  }, 28), 0, 0);
  ctx.fillStyle = `rgba(0,0,0,${dim})`; ctx.fillRect(0, 0, W, H);
}
function phoneOver(ctx, bgName, drawUI, clip, extra) {
  blurredPhoto(ctx, bgName, 0.4);
  const [x, y, w, h, r] = clip;
  ctx.save(); ctx.filter = 'blur(28px)'; ctx.fillStyle = 'rgba(0,0,0,0.55)'; roundRect(ctx, x + 14, y + 40, w, h, r); ctx.fill(); ctx.restore();
  const L = S.layer();
  drawUI(L.getContext('2d'));
  ctx.save(); roundRect(ctx, x, y, w, h, r); ctx.clip(); ctx.drawImage(L, 0, 0);
  if (extra) extra(ctx);
  ctx.restore();
  S.release(L);
  S.vignette(ctx, 0.4);
}
// The AI chat, floating over the blurred room it is read in.
function chatOver(ctx, bgName, sc, t) {
  blurredPhoto(ctx, bgName, 0.5);
  ctx.save(); ctx.filter = 'blur(28px)'; ctx.fillStyle = 'rgba(0,0,0,0.55)'; roundRect(ctx, 74, 270, 960, 1480, 30); ctx.fill(); ctx.restore();
  N.chatScreen(ctx, { x: 60, y: 230, w: 960, h: 1480 }, t, sc.msgs, { level: sc.actors.ai.speechAt(t).open });
  S.vignette(ctx, 0.5);
}
// A round contact photo cut from a face in one of the photographs.
function avatar(ctx, name, cx, cy, r) {
  const img = base(name);
  const b = faceInfo(name).faces[0].bbox;
  const fx = (b[0] + b[2]) / 2, fy = (b[1] + b[3]) / 2, half = (b[2] - b[0]) * 0.95;
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.clip();
  ctx.drawImage(img, fx - half, fy - half, half * 2, half * 2, cx - r, cy - r, r * 2, r * 2);
  ctx.restore();
}

// ------------------------------------------------------------------ scenes
function drawSword(ctx, sc, sh, t, f) {
  const n1 = env.L('N1'), n2 = env.L('N2'), n3 = env.L('N3');
  if (sh.name === 'mayaCU') {
    drawPhoto(ctx, plate('sword_maya', f), push('sword_maya', t, sh.t0, sh.t1 + 1, 1.08));
    S.embers(ctx, t, 45, 5, { x0: 0, x1: W, y0: 300, y1: H }, [255, 160, 70], 0.9);
    S.vignette(ctx, 0.55);
    return;
  }
  const tStrike = sc.tStrike;
  const cam = S.push(t, sc.start, n3.start, 1.0, 1.07, 540, 1050);
  const Lr = S.layer();
  const lc = Lr.getContext('2d');
  drawPhoto(lc, base('sword_table'), cam);
  S.embers(lc, t, 55, 3, { x0: 0, x1: W, y0: 300, y1: H }, [255, 160, 70], 0.9);
  const sp = easeOut((t - tStrike - 0.2) / 3.5) * 46;
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W / 2, H); ctx.clip(); ctx.drawImage(Lr, -sp, 0); ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.rect(W / 2, 0, W / 2, H); ctx.clip(); ctx.drawImage(Lr, sp, 0); ctx.restore();
  S.release(Lr);
  if (sp > 0.5) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createLinearGradient(W / 2 - sp - 40, 0, W / 2 + sp + 40, 0);
    g.addColorStop(0, 'rgba(255,170,80,0)'); g.addColorStop(0.5, 'rgba(255,220,160,0.55)'); g.addColorStop(1, 'rgba(255,170,80,0)');
    ctx.fillStyle = g; ctx.fillRect(W / 2 - sp - 40, 0, sp * 2 + 80, H);
    ctx.restore();
  }
  const fall = clamp((t - (tStrike - 0.55)) / 0.55);
  if (fall > 0) drawBlade(ctx, W / 2, lerp(-500, 1290, Math.pow(fall, 2.2)), t);
  flash(ctx, clamp(1 - (t - tStrike) / 0.7) * (t >= tStrike ? 1 : 0));
  S.vignette(ctx, 0.5);
  const va = (a0, a1) => clamp((t - a0) / 0.6) * (1 - clamp((t - a1) / 0.6));
  verseShade(ctx, Math.max(va(sc.start, n2.start - 0.8), va(n2.start - 0.8, n3.start - 0.2)), 1050);
  if (t < n2.start - 0.2) drawVerse(ctx, n1, t, { y: 470, size: 58, alpha: va(sc.start, n2.start - 0.8) });
  if (t > n2.start - 0.8 && t < n3.start + 0.5) drawVerse(ctx, n2, t, { y: 470, size: 54, cite: 'Matthew 10:34–36', alpha: va(n2.start - 0.8, n3.start - 0.2) });
}

function drawCross(ctx, sc, sh, t, f) {
  const n4 = env.L('N4'), n5 = env.L('N5');
  if (sh.name === 'moon') {
    drawPhoto(ctx, plate('cross_moon', f), push('cross_moon', t, sh.t0, sc.end + 1, 1.1));
    grade(ctx, [60, 80, 160], 0.25);
    S.vignette(ctx, 0.6);
    return;
  }
  const cam = push('cross_true', t, sc.start, n5.start, 1.06);
  drawPhoto(ctx, plate('cross_true', f), cam);
  S.embers(ctx, t, 30, 8, { x0: 0, x1: W, y0: 200, y1: H }, [255, 170, 90], clamp((t - sc.tFall) / 1.5));
  // the performed smile, as a porcelain mask that cracks and falls away
  const top = S.layer();
  const tc = top.getContext('2d');
  drawPhoto(tc, plate('mirror_reflection', Math.min(f, Math.round(sc.tFall * FPS))), cam);
  tc.globalCompositeOperation = 'source-atop';
  tc.fillStyle = 'rgba(225,235,240,0.28)'; tc.fillRect(0, 0, W, H);
  tc.globalCompositeOperation = 'source-over';
  const crackK = smooth((t - sc.tCrack) / 1.4);
  if (t < sc.tFall) {
    ctx.drawImage(top, 0, 0);
    if (crackK > 0) {
      const R = require('./lib/util').rng(78);
      ctx.save(); ctx.strokeStyle = 'rgba(255,250,240,0.85)'; ctx.lineCap = 'round';
      for (const s of sc.shards.slice(0, -1)) {
        const len = 1300 * clamp(crackK * (0.7 + R() * 0.6));
        ctx.lineWidth = 2 + R() * 2.5;
        ctx.beginPath(); ctx.moveTo(540, 860);
        for (let seg = 1; seg <= 6; seg++) {
          const d = (len * seg) / 6, jit = (R() - 0.5) * 0.12;
          ctx.lineTo(540 + Math.cos(s.mid + jit) * d, 860 + Math.sin(s.mid + jit) * d);
        }
        ctx.stroke();
      }
      ctx.restore();
    }
  } else {
    for (const s of sc.shards) {
      const ft = t - sc.tFall - s.delay;
      const y = ft > 0 ? 0.5 * 2600 * ft * ft : 0;
      if (y > 2200) continue;
      const mx = s.poly.reduce((a, p) => a + p[0], 0) / s.poly.length, my = s.poly.reduce((a, p) => a + p[1], 0) / s.poly.length;
      ctx.save();
      ctx.translate(mx + (ft > 0 ? s.drift * ft : 0), my + y);
      ctx.rotate(ft > 0 ? s.spin * ft : 0);
      ctx.translate(-mx, -my);
      ctx.beginPath(); s.poly.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
      ctx.clip();
      ctx.drawImage(top, 0, 0);
      ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 3; ctx.stroke();
      ctx.restore();
    }
  }
  S.release(top);
  flash(ctx, clamp(1 - (t - sc.tFall) / 0.5) * (t >= sc.tFall ? 1 : 0) * 0.65, [255, 245, 230]);
  const bloom = clamp((t - sc.tFound) / 1.5) * (1 - clamp((t - n5.start + 0.6) / 0.6));
  if (bloom > 0) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; S.glowDisc(ctx, 540, 820, 900, [255, 200, 140], 0.22 * bloom); ctx.restore(); }
  S.vignette(ctx, 0.6);
  const a4 = clamp((t - sc.start) / 0.6) * (1 - clamp((t - n5.start + 0.5) / 0.6));
  verseShade(ctx, a4, 800);
  drawVerse(ctx, n4, t, { y: 300, size: 52, cite: 'Matthew 10:38–39', alpha: a4 });
}

function drawCall(ctx, sc, sh, layers, t, f) {
  if (sh.name === 'phone') {
    // same buzz as the 2D insert, so the photo avatar shakes with the phone
    const buzz = Math.sin(t * 60) * 6 * (Math.sin(t * 9) > 0 ? 1 : 0);
    phoneOver(ctx, 'call_maya_after', (c) => sc.drawPhoneInsert(c, t), [190 + buzz, 240, 700, 1440, 70],
      (c) => avatar(c, 'table_mom', 540 + buzz, 640, 124));
    return;
  }
  if (sh.name === 'screen') { chatOver(ctx, 'call_maya_after', sc, t); return; }
  if (layers.length === 2) {
    // split screen: Mom above, Maya below; Mom's half slides away when the call ends
    const close = smooth((t - sc.tHang) / 1.2);
    const half = H / 2, off = -close * half;
    const drawHalf = (name, y0, h) => {
      const img = plate(name, f);
      const { s, ox, oy } = fit(img);
      const sy = clamp(focus(name)[1] - h * 0.45, 0, H - h);   // band of the full-frame photo to show
      ctx.drawImage(img, -ox / s, (sy - oy) / s, W / s, h / s, 0, y0, W, h);
    };
    ctx.save(); ctx.beginPath(); ctx.rect(0, half + off, W, H); ctx.clip();
    const hb = lerp(half, H, close);
    drawHalf('call_maya', half + off, hb);
    ctx.restore();
    if (close < 1) {
      ctx.save(); ctx.beginPath(); ctx.rect(0, off, W, half); ctx.clip();
      drawHalf('call_mom', off, half);
      const g = ctx.createLinearGradient(0, half + off - 160, 0, half + off);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.5)');
      ctx.fillStyle = g; ctx.fillRect(0, half + off - 160, W, 160);
      ctx.restore();
      ctx.fillStyle = 'rgba(255,236,210,0.85)'; ctx.fillRect(0, half + off - 3, W, 6);
      // call badge: green dot, call time
      const secs = Math.max(0, Math.floor(t - sh.t0));
      const label = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
      ctx.save();
      ctx.globalAlpha = 1 - close;
      ctx.font = '34px InterSemi';
      const tw = ctx.measureText(label).width, bw = tw + 84, bx = W / 2 - bw / 2, by = 56 + off;   // top of the call, clear of the subtitles
      ctx.fillStyle = 'rgba(12,12,16,0.78)'; roundRect(ctx, bx, by, bw, 60, 30); ctx.fill();
      ctx.fillStyle = '#4fbf6a'; ctx.beginPath(); ctx.arc(bx + 32, by + 30, 9, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#f2f2f5'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(label, bx + 56, by + 31);
      ctx.restore();
    }
    S.vignette(ctx, 0.4);
    return;
  }
  const name = layers[0].img;
  drawPhoto(ctx, plate(name, f), push(name, t, sh.t0, sh.t1, 1.06));
  S.vignette(ctx, 0.45);
}

function drawDefault(ctx, sc, sh, layers, t, f) {
  const L0 = layers[0];
  if (!L0) return;
  if (L0.ui === 'chat') { chatOver(ctx, 'bed_cu', sc, t); return; }
  if (L0.ui === 'phoneJordan' || L0.ui === 'phoneJordanReply') {
    phoneOver(ctx, 'epi_two', (c) => sc.drawPhone(c, t, L0.ui === 'phoneJordanReply'), [150, 200, 780, 1520, 80]);
    return;
  }
  const name = L0.img;
  const wide = /wide|two|flock/.test(name);
  drawPhoto(ctx, plate(name, f), push(name, t, sh.t0, sh.t1 + (sc.id === 'epilogue' && sh.name === 'window' ? 4 : 0), wide ? 1.04 : 1.07));
  switch (sc.id) {
    case 'table': S.vignette(ctx, 0.45); break;
    case 'mask':
      if (name === 'mirror_reflection') mirrorGlass(ctx);
      S.vignette(ctx, 0.55);
      break;
    case 'office': {
      const tOver = sc.tOver;
      const fl = 0.5 + 0.5 * Math.sin(t * 37) * Math.sin(t * 11.3);
      const over = smooth((t - tOver) / 2);
      const flick = clamp((fl > 0.85 ? 0.8 : 0) + (fbm(t * 6, 3) > 0.55 ? 0.6 : 0) * (0.3 + over));
      if (flick > 0) { ctx.fillStyle = `rgba(0,0,0,${0.1 * flick})`; ctx.fillRect(0, 0, W, H); }
      if (sh.name === 'overwhelm') {
        const o = smooth((t - tOver - 0.8) / 2);
        S.vignette(ctx, 0.45 + 0.35 * o * (0.6 + 0.4 * Math.sin(t * 14)));
        if (flick * o > 0) { ctx.fillStyle = `rgba(240,255,240,${0.1 * flick * o})`; ctx.fillRect(0, 0, W, H); }
      } else S.vignette(ctx, 0.4);
      break;
    }
    case 'park': S.vignette(ctx, 0.4, [40, 10, 20]); break;
    case 'sparrows': {
      S.vignette(ctx, 0.4, [50, 15, 20]);
      const n6 = env.L('N6'), n7 = env.L('N7');
      const a6 = clamp((t - sc.start) / 0.6) * (1 - clamp((t - n7.start + 0.4) / 0.5));
      const a7 = clamp((t - n7.start + 0.3) / 0.5);
      verseShade(ctx, Math.max(a6, a7), 900);
      if (a6 > 0) drawVerse(ctx, n6, t, { y: 330, size: 54, alpha: a6 });
      if (a7 > 0) drawVerse(ctx, n7, t, { y: 300, size: 58, cite: 'Matthew 10:29–31', alpha: a7 });
      break;
    }
    case 'epilogue': {
      S.vignette(ctx, 0.3);
      if (sh.name === 'window') {
        const endA = clamp((t - (sc.n9.end + 0.6)) / 1.0);
        if (endA > 0) { ctx.fillStyle = `rgba(20,10,5,${0.35 * endA})`; ctx.fillRect(0, 0, W, H); drawEndCard(ctx, endA); }
      }
      break;
    }
    default: S.vignette(ctx, 0.45);
  }
}

function drawRoad(ctx, sc, t) {
  const u = clamp((t - sc.start) / (sc.end - sc.start + 1.2));
  const cam = S.push(t, sc.start, sc.end + 1, 1.0, 1.1, 540, 1000, 540, 960);
  drawPhoto(ctx, base('road_night'), cam);
  ctx.save(); ctx.globalAlpha = smooth(u) * 0.95; drawPhoto(ctx, base('road_dawn'), cam); ctx.restore();
  S.vignette(ctx, 0.5);
  verseShade(ctx, clamp((t - sc.start) / 0.6), 950);
  drawVerse(ctx, env.L('N8'), t, { y: 380, size: 54, cite: 'Matthew 10:22–23', alpha: clamp((t - sc.start) / 0.6) });
}

function drawReal(ctx, sc, t) {
  const sh = sc.shotAt ? sc.shotAt(t) : { name: sc.id, t0: sc.start, t1: sc.end };
  const layers = realLayers(env, sc, sh, t);
  const f = Math.round(t * FPS);
  switch (sc.id) {
    case 'sword': return drawSword(ctx, sc, sh, t, f);
    case 'cross': return drawCross(ctx, sc, sh, t, f);
    case 'call': return drawCall(ctx, sc, sh, layers, t, f);
    case 'road': return drawRoad(ctx, sc, t);
    default: return drawDefault(ctx, sc, sh, layers, t, f);
  }
}

const frame = createCanvas(W, H);
const fctx = frame.getContext('2d');
function renderFrame(t) {
  compose(fctx, t, (ctx, sc, tt) => drawReal(ctx, sc, tt));
  return frame;
}
async function frameAt(t) {
  renderFrame(t);
  if (pending.size) {
    await Promise.all([...pending]);
    renderFrame(t);
  }
  return frame;
}

async function main() {
  // every photograph decoded before the first frame
  for (const f of fs.readdirSync(path.join(REAL, 'base'))) if (f.endsWith('.jpg')) base(f.slice(0, -4));
  await Promise.all([...pending]);
  if (args.stills) {
    const out = args.outdir || '/opt/work/real_stills';
    fs.mkdirSync(out, { recursive: true });
    for (const s of args.stills.split(',')) {
      const t = parseFloat(s);
      const p = path.join(out, `real_${t.toFixed(2)}.png`);
      fs.writeFileSync(p, (await frameAt(t)).toBuffer('image/png'));
      console.error('wrote', p);
    }
    return;
  }
  // frames [from, to) as JPEG to stdout (see streamFrames in lib/project.js)
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
