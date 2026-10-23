// ---------- per-character lighting on an offscreen layer ----------
const LAYER = document.createElement('canvas'); LAYER.width = W; LAYER.height = H;
const FX = document.createElement('canvas'); FX.width = W; FX.height = H;
const lctx = LAYER.getContext('2d'), fctx = FX.getContext('2d');
// light: {x,y,color,str, rim, rimColor, amb (shadow color), dark (0..1), key: direction of shadow falloff}
function drawLit(ctx, fn, light) {
  lctx.setTransform(1, 0, 0, 1, 0, 0); lctx.globalCompositeOperation = 'source-over'; lctx.clearRect(0, 0, W, H);
  fn(lctx);
  if (light) {
    const mask = (fill, mode, a = 1) => {
      fctx.setTransform(1, 0, 0, 1, 0, 0); fctx.globalCompositeOperation = 'source-over'; fctx.clearRect(0, 0, W, H);
      fctx.drawImage(LAYER, 0, 0); fctx.globalCompositeOperation = 'source-in'; fctx.fillStyle = fill; fctx.fillRect(0, 0, W, H);
      lctx.globalCompositeOperation = mode; lctx.globalAlpha = a; lctx.drawImage(FX, 0, 0); lctx.globalAlpha = 1; lctx.globalCompositeOperation = 'source-over';
    };
    // overall ambient tint (multiply) with falloff away from the key light
    if (light.dark > 0) {
      const g = lctx.createRadialGradient(light.x, light.y, 10, light.x, light.y, light.fall || 900);
      g.addColorStop(0, light.near || '#ffffff'); g.addColorStop(1, light.amb || '#404060');
      mask(g, 'multiply', light.dark);
    }
    if (light.str > 0) {
      const g = lctx.createRadialGradient(light.x, light.y, 0, light.x, light.y, light.rad || 600);
      g.addColorStop(0, alpha(light.color, 1)); g.addColorStop(1, alpha(light.color, 0));
      mask(g, 'screen', light.str);
    }
    if (light.rim > 0) {
      // rim: the character's silhouette minus itself shifted away from the light
      for (const r of [light]) {
        fctx.setTransform(1, 0, 0, 1, 0, 0); fctx.globalCompositeOperation = 'source-over'; fctx.clearRect(0, 0, W, H);
        fctx.drawImage(LAYER, 0, 0);
        fctx.globalCompositeOperation = 'destination-out';
        const dx = r.rimDx || 0, dy = r.rimDy || 0;
        fctx.drawImage(LAYER, dx, dy);
        fctx.globalCompositeOperation = 'source-in'; fctx.fillStyle = r.rimColor || r.color; fctx.fillRect(0, 0, W, H);
        lctx.globalCompositeOperation = 'lighter'; lctx.globalAlpha = r.rim; lctx.drawImage(FX, 0, 0); lctx.globalAlpha = 1; lctx.globalCompositeOperation = 'source-over';
      }
    }
  }
  ctx.drawImage(LAYER, 0, 0);
}
