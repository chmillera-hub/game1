// ============================================================================
//  RENDER — deterministic video export (open the file with #render).
//  Draws every overlay (captions, vignette, grain, letterbox) into the canvas
//  so each frame is a complete picture, and renders the score offline.
// ============================================================================
(() => {
  if (!/render/.test(location.hash)) return;
  document.querySelectorAll('#intro, #hud, #end, #captions, #grain, #vignette, .lb').forEach(e => { e.hidden = true; });
  const cv = document.getElementById('stage');
  const ctx = cv.getContext('2d', { alpha: false });
  let W = 1920, H = 1080;
  function setSize(w, h) {
    W = w; H = h; cv.width = w; cv.height = h; cv.style.width = w + 'px'; cv.style.height = h + 'px';
    Film.resize && Film.resize(W, H, 1);
  }

  // ---------- captions (mirrors the CSS treatment)
  const LINES = Film.narration.map(n => {
    const hold = n.d ?? Math.max(3, 2.5 + n.text.replace(/ \/ /g, ' ').length * 0.06);
    return { ...n, d: hold, lines: n.text.split(' / ').map(l => l.trim()) };
  });
  const FONT = '"Cormorant Garamond", "Cormorant", Garamond, serif';
  function wrap(words, maxW) {
    const rows = []; let row = [];
    for (const w of words) {
      const test = [...row, w].join(' ');
      if (row.length && ctx.measureText(test).width > maxW) { rows.push(row); row = [w]; } else row.push(w);
    }
    if (row.length) rows.push(row);
    return rows;
  }
  function captions(t) {
    for (const L of LINES) {
      const lt = t - L.t;
      if (lt <= -0.05 || lt >= L.d) continue;
      const big = /\bbig\b/.test(L.cls || ''), small = /\bsmall\b/.test(L.cls || ''), up = /\bup\b/.test(L.cls || '');
      const land = W >= H;
      const base = land ? H * 0.044 : W * 0.056;
      const size = big ? base * 1.75 : small ? base * 0.72 : base;
      ctx.font = `${big || small ? 'normal' : 'italic'} ${big ? 300 : 400} ${size}px ${FONT}`;
      const maxW = Math.min(W * 0.9, size * (big ? 9 : land ? 24 : 15));
      const rows = [];
      L.lines.forEach(line => wrap(line.split(/\s+/), maxW).forEach(r => rows.push(r)));
      const lh = size * 1.24;
      const bottom = up ? H * 0.5 + (rows.length * lh) / 2 : H * (land ? 0.925 : 0.89);
      const out = clamp((L.d - lt) / 0.9);
      // a soft dark plate behind the block keeps the words readable over the brightest light
      const maxRow = Math.max(...rows.map(r => ctx.measureText(r.join(' ')).width));
      const plateA = 0.5 * out * smooth(lt / 0.5);
      if (plateA > 0.01 && !big) {
        const cy = bottom - (rows.length - 1) * lh / 2 - size * 0.55, rx = maxRow / 2 + size * 2, ry = rows.length * lh / 2 + size * 0.8;
        ctx.save(); ctx.translate(W / 2, cy); ctx.scale(1, ry / rx);
        const pg = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
        pg.addColorStop(0, `rgba(0,0,0,${plateA})`); pg.addColorStop(0.6, `rgba(0,0,0,${plateA * 0.6})`); pg.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = pg; ctx.beginPath(); ctx.arc(0, 0, rx, 0, TAU); ctx.fill();
        ctx.restore();
      }
      const total = rows.reduce((n, r) => n + r.length, 0);
      const stagger = Math.min(0.11, 1.4 / total);
      let wi = 0;
      rows.forEach((r, ri) => {
        const y = bottom - (rows.length - 1 - ri) * lh - size * 0.22;
        const widths = r.map(w => ctx.measureText(w).width), sp = ctx.measureText(' ').width;
        const rowW = widths.reduce((a, b) => a + b, 0) + sp * (r.length - 1);
        let x = W / 2 - rowW / 2;
        r.forEach((w, i) => {
          const k = smooth((lt - wi * stagger) / 0.7) * out;
          wi++;
          if (k > 0.002) {
            ctx.save();
            ctx.globalAlpha = k;
            ctx.filter = k < 0.99 ? `blur(${((1 - k) * 4).toFixed(2)}px)` : 'none';
            ctx.shadowColor = 'rgba(0,0,0,0.85)'; ctx.shadowBlur = size * 0.6;
            ctx.fillStyle = small ? 'rgba(236,227,210,0.62)' : '#ece3d2';
            ctx.textBaseline = 'alphabetic';
            ctx.fillText(w, x, y + (1 - k) * size * 0.28);
            ctx.shadowBlur = 3; ctx.fillText(w, x, y + (1 - k) * size * 0.28);
            ctx.restore();
          }
          x += widths[i] + sp;
        });
      });
    }
  }

  // ---------- grain + vignette + letterbox
  const tiles = [0, 1, 2, 3].map(k => {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const g = c.getContext('2d'), d = g.createImageData(256, 256), R = rng(77 + k);
    for (let i = 0; i < d.data.length; i += 4) { const v = (R() * 255) | 0; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
    g.putImageData(d, 0, 0); return c;
  });
  function finish(fx, frameNo) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    // vignette (elliptical) + floor shade for captions
    ctx.save(); ctx.translate(W / 2, H * 0.46); ctx.scale(1.2 * W / H, 0.95);
    const R = H * 0.72;
    const vg = ctx.createRadialGradient(0, 0, 0, 0, 0, R);
    vg.addColorStop(0.5, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = vg; ctx.fillRect(-W, -H, W * 2, H * 2);
    ctx.restore();
    const sh = ctx.createLinearGradient(0, H, 0, H * 0.7);
    sh.addColorStop(0, 'rgba(0,0,0,0.55)'); sh.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = sh; ctx.fillRect(0, H * 0.7, W, H * 0.3);
    // grain
    const gf = Math.floor(frameNo / 2);   // grain refreshes every other frame: film-like, and kinder to the encoder
    const R2 = rng(gf * 7919 + 13);
    const pat = ctx.createPattern(tiles[gf % 4], 'repeat');
    pat.setTransform && pat.setTransform(new DOMMatrix().translate(R2() * 256, R2() * 256));
    ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.05;
    ctx.fillStyle = pat; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
    // letterbox
    const lb = (fx.letterbox ?? 0) * (W > H ? 1 : 0.35) * H * 0.105;
    if (lb > 0.5) { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, lb); ctx.fillRect(0, H - lb, W, lb); }
    ctx.restore();
  }

  function frame(t, frameNo = 0, fps = 30, quality = 0.95) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    const fx = Film.render(ctx, t, 1 / fps, W, H, 1, true);
    FX.bloom(ctx, cv, fx.bloom ?? 0.4);
    if (fx.tone) FX.tone(ctx, cv, fx.tone);
    finish(fx, frameNo);
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
    captions(t);
    return quality ? cv.toDataURL('image/jpeg', quality) : null;
  }

  // ---------- offline score
  let wav = null;
  async function audio(sampleRate = 48000) {
    const dur = Film.duration + 4;
    const oac = new OfflineAudioContext(2, Math.ceil(sampleRate * dur), sampleRate);
    Sound.init(oac);
    Sound.setMaster(0.95);
    for (const ev of Film.events) Sound.play(ev, Math.max(0.0001, ev.t));
    for (let t = 0; t < Film.duration; t += 0.1) {
      const b = Film.beds(t);
      Sound.bedsAt(t, b.drone ?? 0, b.warmth ?? 0, b.wind ?? 0, b.cold ?? 0, b.cut ?? 9000);
    }
    Sound.bedsAt(Film.duration + 0.1, 0, 0, 0, 0, 9000);
    const buf = await oac.startRendering();
    // 16-bit PCM WAV
    const n = buf.length, ch = 2, L = buf.getChannelData(0), Rr = buf.getChannelData(1);
    let peak = 0; for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(Rr[i]));
    const norm = peak > 0.98 ? 0.98 / peak : 1;
    const bytes = new ArrayBuffer(44 + n * ch * 2), v = new DataView(bytes);
    const str = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
    str(0, 'RIFF'); v.setUint32(4, 36 + n * ch * 2, true); str(8, 'WAVE'); str(12, 'fmt ');
    v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, ch, true); v.setUint32(24, sampleRate, true);
    v.setUint32(28, sampleRate * ch * 2, true); v.setUint16(32, ch * 2, true); v.setUint16(34, 16, true);
    str(36, 'data'); v.setUint32(40, n * ch * 2, true);
    let o = 44;
    for (let i = 0; i < n; i++) {
      v.setInt16(o, clamp(L[i] * norm, -1, 1) * 32767, true); o += 2;
      v.setInt16(o, clamp(Rr[i] * norm, -1, 1) * 32767, true); o += 2;
    }
    wav = new Uint8Array(bytes);
    return { bytes: wav.length, peak, chunks: Math.ceil(wav.length / (4 << 20)) };
  }
  function audioChunk(i) {
    const sz = 4 << 20, part = wav.subarray(i * sz, Math.min(wav.length, (i + 1) * sz));
    let s = ''; for (let j = 0; j < part.length; j += 0x8000) s += String.fromCharCode.apply(null, part.subarray(j, j + 0x8000));
    return btoa(s);
  }

  window.__render = { setSize, frame, audio, audioChunk, duration: Film.duration, fonts: () => document.fonts.ready.then(() => Promise.all([document.fonts.load(`italic 400 40px ${FONT}`), document.fonts.load(`300 40px ${FONT}`), document.fonts.load('500 20px Jost')])).then(() => { const ok = ['italic 400 20px "Cormorant Garamond"', '300 20px "Cormorant Garamond"', '500 20px Jost'].every(f => document.fonts.check(f)); if (!ok) throw new Error('fonts not loaded'); return ok; }) };
  setSize(W, H);
})();
