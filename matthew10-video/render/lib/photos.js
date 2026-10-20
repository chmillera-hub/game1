'use strict';
// Generated photographs on the frame: cover-fitted at their own size, with the
// animated face patch for a frame on top (render_faces.py writes the patches).
// Shared by the realistic and fantasy compositors.

const fs = require('fs');
const path = require('path');
const { createCanvas, Image } = require('@napi-rs/canvas');
const S = require('./stage');

const W = S.W, H = S.H;

function photos(REAL) {
  // Images decode off-thread: width/height are known at once but the pixels only
  // after onload, so drawing in the same tick paints nothing. Photos are
  // preloaded; a frame that needs a not-yet-decoded patch is drawn again later.
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
  const meta = {};
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
  // blink must not start early) or begins a new run. During dissolves a shot is
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
  // every photograph decoded before the first frame
  async function preload() {
    const dir = path.join(REAL, 'base');
    for (const f of fs.readdirSync(dir)) if (f.endsWith('.jpg')) base(f.slice(0, -4));
    await settle();
  }
  async function settle() { while (pending.size) await Promise.all([...pending]); }

  return { loadImg, base, faceInfo, fit, plate, drawPhoto, focus, preload, settle, pending };
}

module.exports = { photos };
