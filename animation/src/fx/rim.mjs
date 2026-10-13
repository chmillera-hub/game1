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
  const m = g.getTransform();
  gl.setTransform(1, 0, 0, 1, 0, 0);
  gl.globalAlpha = 1;
  gl.globalCompositeOperation = 'source-over';
  gl.clearRect(0, 0, W, H);
  gl.setTransform(m);
  gl.save();
  drawFn(gl);
  gl.restore();
  gl.setTransform(1, 0, 0, 1, 0, 0);

  // fill light: lift the darks a little, only where the character is
  if (opts.fillAlpha > 0) {
    gl.globalCompositeOperation = 'source-atop';
    gl.fillStyle = rgba(opts.fill || '#9a8fd0', opts.fillAlpha);
    gl.fillRect(0, 0, W, H);
    gl.globalCompositeOperation = 'source-over';
  }

  let rim = false;
  if (opts.dir && (opts.strength ?? 0.8) > 0.01) {
    rim = true;
    const [dx0, dy0] = opts.dir;
    const dl = Math.hypot(dx0, dy0) || 1;
    const w = opts.width ?? 3.5;
    const ux = dx0 / dl, uy = dy0 / dl;
    // edge facing the light = silhouette minus the silhouette shifted toward the light... (the part of the shape
    // whose neighbour toward the light is empty): T = L − L(shifted away from the light)
    gt.setTransform(1, 0, 0, 1, 0, 0);
    gt.globalCompositeOperation = 'source-over';
    gt.clearRect(0, 0, W, H);
    gt.drawImage(L, 0, 0);
    gt.globalCompositeOperation = 'destination-out';
    gt.drawImage(L, -ux * w, -uy * w);
    // a second, wider and fainter band so the rim fades inward instead of stopping on a hard line
    gu.setTransform(1, 0, 0, 1, 0, 0);
    gu.globalCompositeOperation = 'source-over';
    gu.clearRect(0, 0, W, H);
    gu.drawImage(L, 0, 0);
    gu.globalCompositeOperation = 'destination-out';
    gu.drawImage(L, -ux * w * 2.6, -uy * w * 2.6);
    gu.globalCompositeOperation = 'source-in';
    gu.fillStyle = rgba(opts.color || '#ffe2a8', (opts.soft ?? 0.6) * 0.5);
    gu.fillRect(0, 0, W, H);
    gt.globalCompositeOperation = 'source-in';
    gt.fillStyle = rgba(opts.color || '#ffe2a8', 1);
    gt.fillRect(0, 0, W, H);
    gt.globalCompositeOperation = 'source-over';
    gt.drawImage(U, 0, 0);
  }

  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(L, 0, 0);
  if (rim) {
    const a = g.globalAlpha;
    g.globalCompositeOperation = 'screen';
    g.globalAlpha = a * (opts.strength ?? 0.8);
    g.drawImage(T, 0, 0);
  }
  g.restore();
}
