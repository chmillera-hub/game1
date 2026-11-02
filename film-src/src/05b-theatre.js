// ============================================================================
//  THEATRE — the room is a set on a stage: proscenium, traveller curtain,
//  spotlight, ghost light, the house, act cards, and death's vaudeville hook.
//  World units as the room: stage floor y=190, lip at y=300.
// ============================================================================
const Theatre = (() => {
  const OPEN = { x0: -820, x1: 820, y0: -760, y1: 300 };   // proscenium opening
  const LIP = 300;
  const VELVET = [90, 14, 26];

  // spotlight from the fly gallery onto the bed: cone + pool
  function spot(ctx, k, c = [255, 227, 176], o = {}) {
    if (k <= 0.003) return;
    const sx = o.x ?? -40, sy = -1300, px = o.px ?? -30, py = 196, rx = o.rx ?? 560;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const cone = ctx.createLinearGradient(0, sy, 0, py);
    cone.addColorStop(0, rgba(c, 0.0)); cone.addColorStop(0.35, rgba(c, 0.05 * k)); cone.addColorStop(1, rgba(c, 0.09 * k));
    ctx.fillStyle = cone;
    ctx.beginPath(); ctx.moveTo(sx - 40, sy); ctx.lineTo(sx + 40, sy); ctx.lineTo(px + rx, py); ctx.lineTo(px - rx, py); ctx.closePath(); ctx.fill();
    // pool on the floor
    ctx.save(); ctx.translate(px, py + 18); ctx.scale(1, 0.13);
    const pool = ctx.createRadialGradient(0, 0, 0, 0, 0, rx * 1.05);
    pool.addColorStop(0, rgba(c, 0.32 * k)); pool.addColorStop(0.7, rgba(c, 0.16 * k)); pool.addColorStop(1, rgba(c, 0));
    ctx.fillStyle = pool; ctx.beginPath(); ctx.arc(0, 0, rx * 1.05, 0, TAU); ctx.fill();
    ctx.restore();
    ctx.restore();
  }

  // the house curtain (traveller), drawn in world space inside the proscenium.
  // p: 0 open .. 1 closed. light: how much warm light falls on it from the stage.
  function traveller(ctx, p, t, o = {}) {
    if (p <= 0.001) return;
    const W = OPEN.x1 - OPEN.x0, half = W / 2, cover = half * clamp(p) * 1.02;
    const lightX = o.lightX ?? 0, light = o.light ?? 0.4, ghost = o.ghost ?? 0;
    for (const side of [-1, 1]) {
      const outer = side < 0 ? OPEN.x0 : OPEN.x1, inner = outer - side * cover;
      const a = Math.min(outer, inner), b = Math.max(outer, inner);
      ctx.save();
      const path = new Path2D();
      path.moveTo(outer, OPEN.y0 - 20);
      path.lineTo(inner, OPEN.y0 - 20);
      for (let y = OPEN.y0; y <= LIP + 4; y += 30) {
        const sway = Math.sin(y * 0.006 + t * 0.7 + side) * 6 * (1 - p * 0.5) + (y - OPEN.y0) / (LIP - OPEN.y0) * 14 * side * -1;
        path.lineTo(inner + sway, y);
      }
      path.lineTo(outer, LIP + 4); path.closePath();
      ctx.clip(path);
      // folds: compressed toward the outer edge
      const folds = 26;
      for (let i = 0; i < folds; i++) {
        const u0 = i / folds, u1 = (i + 1) / folds;
        const x0 = side < 0 ? lerp(a, b, Math.pow(u0, 1.15)) : lerp(b, a, Math.pow(u0, 1.15));
        const x1 = side < 0 ? lerp(a, b, Math.pow(u1, 1.15)) : lerp(b, a, Math.pow(u1, 1.15));
        const l = Math.min(x0, x1), r = Math.max(x0, x1);
        const g = ctx.createLinearGradient(l, 0, r, 0);
        g.addColorStop(0, rgba(mix(VELVET, [0, 0, 0], 0.62), 1));
        g.addColorStop(0.42, rgba(mix(VELVET, [255, 140, 110], 0.12), 1));
        g.addColorStop(0.6, rgba(VELVET, 1));
        g.addColorStop(1, rgba(mix(VELVET, [0, 0, 0], 0.55), 1));
        ctx.fillStyle = g; ctx.fillRect(l, OPEN.y0 - 30, r - l + 1, LIP - OPEN.y0 + 40);
      }
      // light on the velvet: stage spill near the gap, the ghost light from below
      ctx.globalCompositeOperation = 'lighter';
      const gx = inner;
      const sg = ctx.createLinearGradient(gx - side * 260, 0, gx, 0);
      sg.addColorStop(0, 'rgba(255,170,110,0)'); sg.addColorStop(1, rgba([255, 186, 130], 0.2 * light));
      ctx.fillStyle = sg; ctx.fillRect(Math.min(gx, gx - side * 260), OPEN.y0 - 30, 260, LIP - OPEN.y0 + 40);
      if (ghost > 0) {
        const gg = ctx.createRadialGradient(0, 150, 10, 0, 150, 760);
        gg.addColorStop(0, rgba([255, 200, 140], 0.34 * ghost)); gg.addColorStop(1, 'rgba(255,200,140,0)');
        ctx.fillStyle = gg; ctx.fillRect(OPEN.x0, OPEN.y0, W, LIP - OPEN.y0 + 10);
      }
      // footlight warmth along the hem
      const fg = ctx.createLinearGradient(0, LIP, 0, LIP - 300);
      fg.addColorStop(0, rgba([255, 194, 122], 0.14 * (o.foot ?? 0.5))); fg.addColorStop(1, 'rgba(255,194,122,0)');
      ctx.fillStyle = fg; ctx.fillRect(a, LIP - 300, b - a, 304);
      ctx.restore();
      // scalloped hem shadow
      ctx.fillStyle = 'rgba(0,0,0,0.35)';
      ctx.fillRect(a, LIP - 6, b - a, 10);
    }
    // the spotlight landing on the closed curtain
    if (o.spot > 0.01 && p > 0.5) Draw.glow(ctx, -30, 60, 560, [255, 220, 170], 0.3 * o.spot * (p - 0.5) * 2);
    // the seam: a line of warm light where the halves meet, that never goes out
    if (o.seam > 0) {
      const sx = 0;
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const sg = ctx.createLinearGradient(sx - 30, 0, sx + 30, 0);
      sg.addColorStop(0, 'rgba(255,217,160,0)'); sg.addColorStop(0.5, rgba([255, 217, 160], 0.85 * o.seam)); sg.addColorStop(1, 'rgba(255,217,160,0)');
      ctx.fillStyle = sg; ctx.fillRect(sx - 30, OPEN.y0, 60, LIP - OPEN.y0);
      Draw.glow(ctx, sx, LIP - 4, 220, [255, 210, 150], 0.35 * o.seam);
      ctx.fillStyle = rgba([255, 226, 180], 0.5 * o.seam); ctx.fillRect(sx - 260, LIP - 2, 520, 3);
      ctx.restore();
    }
  }

  // proscenium: dark wall around the opening, gilt frame, valance, stage lip & footlights
  function proscenium(ctx, o = {}) {
    const big = 8000;
    ctx.save();
    // the house wall around the opening
    const wall = new Path2D();
    wall.rect(-big, -big, big * 2, big * 2);
    wall.rect(OPEN.x0, OPEN.y0, OPEN.x1 - OPEN.x0, LIP - OPEN.y0);
    ctx.fillStyle = 'rgb(9,7,9)'; ctx.fill(wall, 'evenodd');
    // stage lip and the apron below it
    ctx.fillStyle = 'rgb(14,10,9)'; ctx.fillRect(OPEN.x0 - 60, LIP, OPEN.x1 - OPEN.x0 + 120, 44);
    ctx.fillStyle = rgba([90, 64, 48], 0.9); ctx.fillRect(OPEN.x0 - 60, LIP, OPEN.x1 - OPEN.x0 + 120, 3);
    // footlights
    const fl = o.foot ?? 0.4;
    for (let i = 0; i < 17; i++) {
      const x = OPEN.x0 + 40 + i * ((OPEN.x1 - OPEN.x0 - 80) / 16);
      ctx.fillStyle = 'rgb(20,16,14)'; ctx.fillRect(x - 16, LIP + 6, 32, 10);
      Draw.glow(ctx, x, LIP + 4, 46, [255, 194, 122], 0.3 * fl, 1);
    }
    // gilt frame
    const gilt = (w, a) => { ctx.strokeStyle = rgba([138, 106, 58], a); ctx.lineWidth = w; ctx.strokeRect(OPEN.x0 - w / 2, OPEN.y0 - w / 2, OPEN.x1 - OPEN.x0 + w, LIP - OPEN.y0 + w); };
    gilt(34, 0.55); gilt(6, 0.9);
    ctx.strokeStyle = rgba([220, 180, 110], 0.3); ctx.lineWidth = 2;
    ctx.strokeRect(OPEN.x0 - 30, OPEN.y0 - 30, OPEN.x1 - OPEN.x0 + 60, LIP - OPEN.y0 + 60);
    // valance (border) across the top of the opening
    const vh = 70;
    const vg = ctx.createLinearGradient(0, OPEN.y0, 0, OPEN.y0 + vh);
    vg.addColorStop(0, rgba(mix(VELVET, [0, 0, 0], 0.6), 1)); vg.addColorStop(1, rgba(VELVET, 1));
    ctx.fillStyle = vg;
    ctx.beginPath(); ctx.moveTo(OPEN.x0, OPEN.y0); ctx.lineTo(OPEN.x1, OPEN.y0); ctx.lineTo(OPEN.x1, OPEN.y0 + vh * 0.7);
    const sw = (OPEN.x1 - OPEN.x0) / 10;
    for (let i = 10; i >= 0; i--) ctx.quadraticCurveTo(OPEN.x0 + i * sw + sw / 2, OPEN.y0 + vh * 1.2, OPEN.x0 + i * sw, OPEN.y0 + vh * 0.7);
    ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(230,180,90,0.4)'; ctx.lineWidth = 3;
    ctx.beginPath(); for (let i = 0; i <= 10; i++) { const x = OPEN.x0 + i * sw; i ? ctx.quadraticCurveTo(x - sw / 2, OPEN.y0 + vh * 1.2, x, OPEN.y0 + vh * 0.7) : ctx.moveTo(x, OPEN.y0 + vh * 0.7); } ctx.stroke();
    ctx.restore();
  }

  // the ghost light: a bare bulb on a stand, left burning on an empty stage
  function ghostLight(ctx, k, t, x = 0) {
    const y = LIP - 6;
    ctx.save();
    ctx.strokeStyle = 'rgb(16,14,14)'; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y - 170); ctx.stroke();
    ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(x, y - 6); ctx.lineTo(x - 34, y + 8); ctx.moveTo(x, y - 6); ctx.lineTo(x + 34, y + 8); ctx.moveTo(x, y - 6); ctx.lineTo(x, y + 10); ctx.stroke();
    ctx.fillStyle = 'rgb(20,18,18)'; ctx.fillRect(x - 7, y - 182, 14, 14);
    const on = clamp(k), fil = on > 0.02 ? 1 : 0;
    ctx.fillStyle = rgba(mix([60, 50, 40], [255, 242, 208], on), 0.95);
    ctx.beginPath(); ctx.arc(x, y - 194, 12, 0, TAU); ctx.fill();
    if (on > 0.01) {
      Draw.glow(ctx, x, y - 194, 520, [255, 184, 102], 0.22 * on);
      Draw.glow(ctx, x, y - 194, 120, [255, 214, 160], 0.55 * on);
      Draw.glow(ctx, x, y - 194, 18, [255, 250, 230], 0.95 * on, 1);
    } else Draw.glow(ctx, x, y - 194, 5, [255, 120, 40], 0.4 * fil * 0, 1);
    ctx.restore();
  }

  // the house: a few rows of heads and seat backs in front of the stage (screen space)
  function house(ctx, W, H, DPR, k, glow = 0) {
    if (k <= 0.003) return;
    ctx.save(); ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    const R = rng(4);
    for (let row = 0; row < 2; row++) {
      const n = row ? 9 : 11, base = H * (1.02 - row * 0.05), s = Math.min(W, H) * (row ? 0.07 : 0.085);
      for (let i = 0; i < n; i++) {
        const x = W * (i + 0.5 + (row ? 0.5 : 0) * 0 + (R() - 0.5) * 0.3) / n, y = base + R() * s * 0.2;
        ctx.fillStyle = `rgba(3,2,3,${0.96 * k})`;
        ctx.beginPath(); ctx.ellipse(x, y - s * 1.25, s * 0.42, s * 0.5, 0, 0, TAU); ctx.fill();
        ctx.beginPath(); ctx.ellipse(x, y, s * 0.95, s * 0.75, 0, Math.PI, 0); ctx.fill();
        if (glow > 0) { ctx.strokeStyle = rgba([242, 176, 94], 0.25 * glow * k); ctx.lineWidth = 1.2; ctx.beginPath(); ctx.ellipse(x, y - s * 1.25, s * 0.42, s * 0.5, 0, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); }
      }
    }
    ctx.restore();
  }

  // act card at the top of the frame, in the letterbox
  function actCard(ctx, W, H, DPR, k, text) {
    if (k <= 0.003) return;
    ctx.save(); ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    const size = Math.max(11, Math.min(W, H) * 0.022);
    ctx.font = `500 ${size}px "Jost", "Futura", system-ui, sans-serif`;
    try { ctx.letterSpacing = (size * 0.32).toFixed(1) + 'px'; } catch (e) { }
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = `rgba(214,196,160,${0.8 * k})`;
    ctx.shadowColor = 'rgba(0,0,0,0.9)'; ctx.shadowBlur = size;
    ctx.fillText(text, W / 2, H * (W > H ? 0.118 : 0.06));
    ctx.restore();
  }

  // the vaudeville stage hook: a long pole ending in a shepherd's crook
  // from (x0,y0) toward angle a, length L; returns the crook tip
  function hook(ctx, x0, y0, x1, y1, a = 1, bent = 0) {
    if (a <= 0.003) return;
    ctx.save();
    ctx.lineCap = 'round';
    const ang = Math.atan2(y1 - y0, x1 - x0);
    const cr = 22;
    const cx = x1 - Math.cos(ang) * 0, cy = y1;
    ctx.strokeStyle = `rgba(26,22,26,${a})`; ctx.lineWidth = 9;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1);
    // the crook curls up and back over
    const up = -Math.PI / 2;
    ctx.arc(x1 + Math.cos(ang + Math.PI / 2 + bent) * 0, y1 - cr, cr, Math.PI / 2, Math.PI / 2 + Math.PI * (1.15 - bent * 0.4), ang > -Math.PI / 2 && ang < Math.PI / 2);
    ctx.stroke();
    ctx.strokeStyle = rgba([170, 186, 214], 0.65 * a); ctx.lineWidth = 2.2; ctx.stroke();
    ctx.restore();
  }

  return { OPEN, LIP, spot, traveller, proscenium, ghostLight, house, actCard, hook };
})();
