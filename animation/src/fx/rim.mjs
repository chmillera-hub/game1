// Light from a visible source on a character: a soft fill that keeps it readable (never near-black against a bright
// doorway, lamp or glow) and a rim of the source's colour along the silhouette edge that faces it.
//
//   drawLit(g, (g2) => drawSelf(g2, x, y, s, pose), { dir: [-1, -0.3], color: '#ffe2a8', strength: 0.8,
//                                                    width: 4, fill: '#9a8fd0', fillAlpha: 0.12 })
//     drawFn  draws the character into an offscreen layer with g's current transform (and alpha) — call it exactly
//             as you would on g
//     dir     screen direction TOWARD the light (any length); omit for fill only
//     color   rim colour (the source's light);  strength 0..1;  width rim thickness in screen px (default 3.5)
//     fill    fill colour lifting the darks;   fillAlpha 0..1 (default 0)
//     soft    0..1 how far the rim fades inward (default 0.6)
//     box     [x0, y0, x1, y1] screen-px region around the character (much cheaper than the full frame)
// Cost: a few full-frame drawImage calls per character (reused canvases).

import { createCanvas } from '@napi-rs/canvas';
import { W, H, rgba } from '../engine.mjs';

let L = null, T = null, U = null;
function layers() {
  if (!L) {
    L = createCanvas(W, H); T = createCanvas(W, H); U = createCanvas(W, H);
    // faces drawn on the layer still count for caption placement (render.mjs --place-subs)
    if (globalThis.__FACE_CANVASES) globalThis.__FACE_CANVASES.add(L);
  }
  if (globalThis.__FACE_CANVASES && !globalThis.__FACE_CANVASES.has(L)) globalThis.__FACE_CANVASES.add(L);
  return [L.getContext('2d'), T.getContext('2d'), U.getContext('2d')];
}

export function drawLit(g, drawFn, opts = {}) {
  const [gl, gt, gu] = layers();
  // work region in screen px (opts.box = [x0, y0, x1, y1] around the character keeps the cost down)
  const B = opts.box;
  const bx = B ? Math.max(0, Math.floor(B[0])) : 0, by = B ? Math.max(0, Math.floor(B[1])) : 0;
  const bw = B ? Math.min(W, Math.ceil(B[2])) - bx : W, bh = B ? Math.min(H, Math.ceil(B[3])) - by : H;
  if (bw <= 0 || bh <= 0) return;
  const copy = (dst, src, dx = 0, dy = 0) => dst.drawImage(src, bx, by, bw, bh, bx + dx, by + dy, bw, bh);
  const m = g.getTransform();
  gl.setTransform(1, 0, 0, 1, 0, 0);
  gl.globalAlpha = 1;
  gl.globalCompositeOperation = 'source-over';
  gl.clearRect(bx, by, bw, bh);
  gl.save();
  gl.beginPath(); gl.rect(bx, by, bw, bh); gl.clip();   // nothing lands outside the region (it is only cleared there)
  gl.setTransform(m);
  drawFn(gl);
  gl.restore();
  gl.setTransform(1, 0, 0, 1, 0, 0);

  // fill light: lift the darks a little, only where the character is
  if (opts.fillAlpha > 0) {
    gl.globalCompositeOperation = 'source-atop';
    gl.fillStyle = rgba(opts.fill || '#9a8fd0', opts.fillAlpha);
    gl.fillRect(bx, by, bw, bh);
    gl.globalCompositeOperation = 'source-over';
  }

  let rim = false;
  if (opts.dir && (opts.strength ?? 0.8) > 0.01) {
    rim = true;
    const [dx0, dy0] = opts.dir;
    const dl = Math.hypot(dx0, dy0) || 1;
    const w = opts.width ?? 3.5;
    const ux = dx0 / dl, uy = dy0 / dl;
    // edge facing the light: the silhouette minus itself shifted away from the light (T = L − L(shifted))
    for (const [gg, k, a] of [[gt, 1, 1], [gu, 2.6, (opts.soft ?? 0.6) * 0.5]]) {
      gg.setTransform(1, 0, 0, 1, 0, 0);
      gg.globalCompositeOperation = 'source-over';
      gg.clearRect(bx, by, bw, bh);
      copy(gg, L);
      gg.globalCompositeOperation = 'destination-out';
      copy(gg, L, -ux * w * k, -uy * w * k);
      gg.globalCompositeOperation = 'source-in';
      gg.fillStyle = rgba(opts.color || '#ffe2a8', a);
      gg.fillRect(bx, by, bw, bh);
      gg.globalCompositeOperation = 'source-over';
    }
    // the wider, fainter band fades the rim inward instead of stopping on a hard line
    copy(gt, U);
  }

  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  copy(g, L);
  if (rim) {
    const a = g.globalAlpha;
    g.globalCompositeOperation = 'screen';
    g.globalAlpha = a * (opts.strength ?? 0.8);
    copy(g, T);
  }
  g.restore();
}
