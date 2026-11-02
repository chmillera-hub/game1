// ============================================================================
//  FX — camera, offscreen layers, transitions, light streams
// ============================================================================
const FX = (() => {
  // ---- camera: world box -> screen transform. Portrait frames tighter on width.
  // shot = { cx, cy, w } world width visible in landscape; h derived from 16:9.
  function camera(ctx, shot, W, H, DPR, shake = 0, t = 0) {
    const land = W >= H;
    const w = land ? shot.w : shot.w * (shot.pw ?? 0.62);
    const h = land ? shot.w * 9 / 16 : shot.w * (shot.ph ?? 1.15);
    const S = Math.min(W / w, H / h);
    const cy = land ? shot.cy : (shot.pcy ?? shot.cy);
    const cx = land ? shot.cx : (shot.pcx ?? shot.cx);
    const sx = shake ? Noise.n2(t * 31, 1.7) * shake * 2.4 : 0, sy = shake ? Noise.n2(4.2, t * 29) * shake * 2.4 : 0;
    ctx.setTransform(DPR * S, 0, 0, DPR * S, DPR * (W / 2 - cx * S + sx), DPR * (H / 2 - cy * S + sy));
    return { S, cx, cy, toScreen: (x, y) => [W / 2 + (x - cx) * S, H / 2 + (y - cy) * S] };
  }
  // interpolate between shots with easing
  function shotAt(t, keys) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      if (t <= keys[i][0]) {
        const [t0, a] = keys[i - 1], [t1, b, e] = keys[i];
        const k = (Ease[e || 'sine'])((t - t0) / (t1 - t0 || 1));
        const o = {};
        for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
          const va = a[key] ?? b[key], vb = b[key] ?? a[key];
          o[key] = lerp(va, vb, k);
        }
        return o;
      }
    }
    return keys[keys.length - 1][1];
  }

  // ---- make every frame independent of what was drawn before
  function resetState(g) {
    g.filter = 'none'; g.lineCap = 'butt'; g.lineJoin = 'miter'; g.lineWidth = 1; g.shadowBlur = 0; g.shadowColor = 'rgba(0,0,0,0)';
    g.textAlign = 'start'; g.textBaseline = 'alphabetic'; g.setLineDash([]);
  }
  // ---- offscreen layer (same size as the main canvas)
  const layers = {};
  function layer(name, cv) {
    let L = layers[name];
    if (!L || L.c.width !== cv.width || L.c.height !== cv.height) {
      const c = L ? L.c : document.createElement('canvas');
      c.width = cv.width; c.height = cv.height;
      L = layers[name] = { c, g: c.getContext('2d') };
    }
    L.g.setTransform(1, 0, 0, 1, 0, 0);
    L.g.globalAlpha = 1; L.g.globalCompositeOperation = 'source-over'; resetState(L.g);
    L.g.clearRect(0, 0, L.c.width, L.c.height);
    return L;
  }
  // composite a layer onto ctx with a transition mask in screen space
  // kind: 'fade' | 'bloom' (noisy radial from point) | 'rise' (wavy line from bottom) | 'iris'
  function composite(ctx, L, k, kind, o = {}) {
    k = clamp(k);
    if (k <= 0.001) return;
    const cw = L.c.width, ch = L.c.height;
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (k >= 0.999 || kind === 'fade') {
      ctx.globalAlpha = kind === 'fade' ? k : 1;
      ctx.drawImage(L.c, 0, 0);
      ctx.restore(); return;
    }
    const t = o.t || 0;
    ctx.beginPath();
    if (kind === 'bloom' || kind === 'iris') {
      const px = (o.x ?? 0.5) * cw, py = (o.y ?? 0.5) * ch;
      const R = Math.hypot(Math.max(px, cw - px), Math.max(py, ch - py)) * 1.15 * (kind === 'iris' ? 1 : 1.1);
      const r = R * Ease.inOut(k);
      const N = 90;
      for (let i = 0; i <= N; i++) {
        const a = i / N * TAU;
        const wob = kind === 'bloom' ? 1 + 0.16 * Noise.n2(Math.cos(a) * 1.6 + 3, Math.sin(a) * 1.6 + t * 0.4) + 0.05 * Math.sin(a * 9 + t) : 1;
        const x = px + Math.cos(a) * r * wob, y = py + Math.sin(a) * r * wob;
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      }
    } else if (kind === 'rise') {
      const y0 = ch * (1 - Ease.inOut(k) * 1.12);
      ctx.moveTo(0, ch);
      for (let x = 0; x <= cw; x += cw / 60) ctx.lineTo(x, y0 + Math.sin(x / cw * 9 + t * 2) * ch * 0.02 + Noise.n2(x / cw * 3, t) * ch * 0.02);
      ctx.lineTo(cw, ch); ctx.closePath();
    } else if (kind === 'wipe') {
      const x0 = cw * Ease.inOut(k) * 1.2 - cw * 0.1;
      ctx.moveTo(0, 0);
      for (let y = 0; y <= ch; y += ch / 40) ctx.lineTo(x0 + Noise.n2(y / ch * 4, t) * cw * 0.05, y);
      ctx.lineTo(0, ch); ctx.closePath();
    }
    ctx.clip();
    ctx.drawImage(L.c, 0, 0);
    ctx.restore();
    // a soft light along the leading edge of organic reveals
    if (o.edge && kind !== 'fade') {
      ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 0.18 * Math.sin(k * Math.PI);
      ctx.globalCompositeOperation = 'lighter';
      ctx.fillStyle = o.edge; ctx.fillRect(0, 0, cw, ch);
      ctx.restore();
    }
  }

  // ---- streams of coloured light flowing from a to b (used for joining / merging)
  function stream(ctx, ax, ay, bx, by, c, k, t, seed = 0, n = 26, width = 30) {
    if (k <= 0.001) return;
    for (let i = 0; i < n; i++) {
      const ph = ((t * 0.35 + i / n + seed * 0.13) % 1);
      const u = ph;
      const bend = Math.sin(u * Math.PI) * width * (1 + 0.6 * Noise.n2(i, seed));
      const nx = -(by - ay), ny = bx - ax, nl = Math.hypot(nx, ny) || 1;
      const x = lerp(ax, bx, u) + nx / nl * bend * Math.sin(i * 1.7 + seed);
      const y = lerp(ay, by, u) + ny / nl * bend * Math.sin(i * 1.7 + seed);
      Draw.glow(ctx, x, y, 4 + 6 * Math.sin(u * Math.PI), c, k * Math.sin(u * Math.PI) * 0.9, 1);
    }
  }

  // ---- expanding ring (touch / heartbeat)
  function ring(ctx, x, y, r, c, a, w = 2) {
    if (a <= 0.003) return;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    ctx.strokeStyle = rgba(c, a); ctx.lineWidth = w;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.stroke();
    ctx.restore();
  }

  // full-frame tint (screen space)
  function wash(ctx, W, H, DPR, c, a, op = 'source-over') {
    if (a <= 0.002) return;
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = op; ctx.fillStyle = rgba(c, a);
    ctx.fillRect(0, 0, W * DPR, H * DPR);
    ctx.restore();
  }

  // ---- bloom: chained downsample of the frame, screened back on top
  const BL = {};
  function bloom(ctx, cv, amount) {
    if (amount <= 0.001) return;
    const mk = (k, d) => {
      let c = BL[k];
      const w = Math.max(2, Math.round(cv.width / d)), h = Math.max(2, Math.round(cv.height / d));
      if (!c || c.width !== w || c.height !== h) { c = BL[k] = document.createElement('canvas'); c.width = w; c.height = h; c._g = c.getContext('2d'); }
      return c;
    };
    const a = mk('a', 4), b = mk('b', 8), c = mk('c', 16);
    a._g.globalCompositeOperation = 'copy'; a._g.drawImage(cv, 0, 0, a.width, a.height);
    b._g.globalCompositeOperation = 'copy'; b._g.drawImage(a, 0, 0, b.width, b.height);
    c._g.globalCompositeOperation = 'copy'; c._g.drawImage(b, 0, 0, c.width, c.height);
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.globalCompositeOperation = 'screen';
    ctx.globalAlpha = clamp(amount * 0.55); ctx.drawImage(c, 0, 0, cv.width, cv.height);
    ctx.globalAlpha = clamp(amount * 0.35); ctx.drawImage(b, 0, 0, cv.width, cv.height);
    ctx.restore();
  }

  // gentle filmic contrast: deepen the mids so light reads as light
  function tone(ctx, cv, k = 1) {
    if (k <= 0) return;
    const L = layer('tone', cv);
    L.g.drawImage(cv, 0, 0);
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.filter = `contrast(${(1 + 0.14 * k).toFixed(3)}) saturate(${(1 + 0.08 * k).toFixed(3)}) brightness(${(1 - 0.03 * k).toFixed(3)})`;
    ctx.drawImage(L.c, 0, 0);
    ctx.restore();
  }

  return { camera, shotAt, layer, composite, stream, ring, wash, bloom, tone, resetState };
})();
