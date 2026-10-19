'use strict';
// Staging helpers: offscreen layers, lit/blurred/silhouetted characters,
// cached backgrounds, camera moves and common overlays (vignette, embers).

const { createCanvas } = require('@napi-rs/canvas');
const { clamp, lerp, rgbStr, smooth, rng, hexToRgb } = require('./util');
const { drawCharacter } = require('./character');

const W = 1080, H = 1920;

const pool = [];
function layer() {
  const c = pool.pop() || createCanvas(W, H);
  const ctx = c.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  ctx.filter = 'none';
  ctx.clearRect(0, 0, W, H);
  return c;
}
function release(c) { pool.push(c); }

// Draw a character with scene lighting.
// look: { light:{x,y}, tint:[r,g,b], tintA, key:{y0,y1,top:[r,g,b],topA,bottom,bottomA},
//         glow:{x,y,r,color,a} (in pixels), rim, blur(px), silhouette:{color, rim:[r,g,b], dx, dy}, alpha }
// Close-ups: arms whose hands rest below the frame hang behind the torso instead.
function tuckArms(P, hyLimit = 1.3) {
  for (const k of ['armL', 'armR']) {
    const a = P[k];
    if (a && a.hy !== undefined && a.hy > hyLimit) P[k] = { ...a, front: false, prop: null, hx: (k === 'armL' ? -1 : 1) * 0.62, hy: 1.9, ew: 0 };
  }
  return P;
}

function drawLit(ctx, A, P, look = {}, cam = null) {
  const L = layer();
  const lc = L.getContext('2d');
  if (cam) applyCam(lc, cam);
  const parts = look.parts || 'all';
  drawCharacter(lc, A, { ...P, rim: look.rim || P.rim }, { light: look.light || { x: -0.6, y: -0.8 }, parts });
  lc.setTransform(1, 0, 0, 1, 0, 0);
  lc.globalCompositeOperation = 'source-atop';
  if (look.key) {
    const k = look.key;
    const g = lc.createLinearGradient(0, k.y0, 0, k.y1);
    g.addColorStop(0, rgbStr(k.top || [255, 230, 190], k.topA ?? 0.12));
    g.addColorStop(1, rgbStr(k.bottom || [0, 0, 0], k.bottomA ?? 0.3));
    lc.fillStyle = g; lc.fillRect(0, 0, W, H);
  }
  if (look.glow) {
    const gl = look.glow;
    const g = lc.createRadialGradient(gl.x, gl.y, 0, gl.x, gl.y, gl.r);
    g.addColorStop(0, rgbStr(gl.color, gl.a));
    g.addColorStop(1, rgbStr(gl.color, 0));
    lc.fillStyle = g; lc.fillRect(0, 0, W, H);
  }
  if (look.tint) { lc.fillStyle = rgbStr(look.tint, look.tintA ?? 0.15); lc.fillRect(0, 0, W, H); }
  if (look.dark) { lc.fillStyle = `rgba(0,0,0,${look.dark})`; lc.fillRect(0, 0, W, H); }
  if (look.silhouette) {
    const s = look.silhouette;
    lc.globalCompositeOperation = 'source-in';
    lc.fillStyle = rgbStr(s.color || [12, 6, 6], 1);
    lc.fillRect(0, 0, W, H);
    lc.globalCompositeOperation = 'source-over';
    if (s.rim) {
      // rim: draw a bright copy offset behind the silhouette
      ctx.save();
      ctx.globalAlpha = (look.alpha ?? 1) * (s.rimA ?? 0.9);
      const R = layer();
      const rc = R.getContext('2d');
      rc.drawImage(L, 0, 0);
      rc.globalCompositeOperation = 'source-in';
      rc.fillStyle = rgbStr(s.rim, 1); rc.fillRect(0, 0, W, H);
      ctx.filter = `blur(${s.rimBlur ?? 2}px)`;
      ctx.drawImage(R, s.dx ?? 3, s.dy ?? -2);
      ctx.filter = 'none';
      release(R);
      ctx.restore();
    }
  }
  ctx.save();
  ctx.globalAlpha = look.alpha ?? 1;
  if (look.blur) ctx.filter = `blur(${look.blur}px)`;
  ctx.drawImage(L, 0, 0);
  ctx.restore();
  release(L);
}

// Camera: {x, y, zoom, rot} — zoom about (x, y) which maps to the frame centre.
function applyCam(ctx, cam) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  if (!cam) return;
  const z = Math.max(1, cam.zoom ?? 1);
  // keep the frame covered: the visible window must stay inside the canvas
  const hx = W / (2 * z), hy = H / (2 * z);
  const cx = clamp(cam.x ?? W / 2, hx, W - hx), cy = clamp(cam.y ?? H / 2, hy, H - hy);
  ctx.translate(W / 2 + (cam.dx || 0), H / 2 + (cam.dy || 0));
  if (cam.rot) ctx.rotate(cam.rot);
  ctx.scale(z, z);
  ctx.translate(-cx, -cy);
}
// A slow push-in between two zooms over [t0, t1].
function push(t, t0, t1, z0, z1, fx = W / 2, fy = H / 2, fx1 = fx, fy1 = fy) {
  const u = smooth((t - t0) / Math.max(0.001, t1 - t0));
  return { x: lerp(fx, fx1, u), y: lerp(fy, fy1, u), zoom: lerp(z0, z1, u) };
}

// Cache static backgrounds keyed by name (optionally pre-blurred).
const bgCache = new Map();
function cachedBg(key, drawFn, blur = 0, w = W, h = H) {
  const k = key + '|' + blur;
  if (bgCache.has(k)) return bgCache.get(k);
  const c = createCanvas(w, h);
  const ctx = c.getContext('2d');
  drawFn(ctx, w, h);
  let out = c;
  if (blur > 0) {
    const b = createCanvas(w, h);
    const bc = b.getContext('2d');
    bc.filter = `blur(${blur}px)`;
    bc.drawImage(c, 0, 0);
    out = b;
  }
  bgCache.set(k, out);
  return out;
}

function vignette(ctx, strength = 0.45, color = [0, 0, 0]) {
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createRadialGradient(W / 2, H * 0.45, H * 0.28, W / 2, H * 0.5, H * 0.72);
  g.addColorStop(0, rgbStr(color, 0));
  g.addColorStop(1, rgbStr(color, strength));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// Drifting embers (deterministic per time).
function embers(ctx, t, n = 40, seed = 1, area = { x0: 0, x1: W, y0: 0, y1: H }, color = [255, 170, 80], alpha = 1) {
  const r = rng(seed);
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const sp = 25 + r() * 70;
    const x0 = area.x0 + r() * (area.x1 - area.x0);
    const ph = r() * 1000;
    const life = (area.y1 - area.y0) / sp;
    const tt = (t + ph) % life;
    const y = area.y1 - tt * sp;
    const x = x0 + Math.sin((t + ph) * (0.6 + r())) * 22;
    const size = 1.5 + r() * 3.5;
    const fl = 0.55 + 0.45 * Math.sin((t + ph) * (3 + r() * 4));
    const a = alpha * fl * clamp(tt / 1.5) * clamp((life - tt) / 2);
    const g = ctx.createRadialGradient(x, y, 0, x, y, size * 4);
    g.addColorStop(0, rgbStr(color, 0.9 * a));
    g.addColorStop(0.3, rgbStr(color, 0.35 * a));
    g.addColorStop(1, rgbStr(color, 0));
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, size * 4, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

// Soft light pool / bokeh disc.
function glowDisc(ctx, x, y, r, color, a) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgbStr(color, a));
  g.addColorStop(1, rgbStr(color, 0));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
}

function fillAll(ctx, color, a = 1) {
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = rgbStr(hexToRgb(color), a); ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

module.exports = { W, H, layer, release, drawLit, tuckArms, applyCam, push, cachedBg, vignette, embers, glowDisc, fillAll };
