// Timeline helpers: look up lines/scenes, estimate when a word is spoken,
// read the lip-sync envelope, blend facial-expression keyframes, build captions.
const U = require('./util');
const { clamp, lerp, prog, ease } = U;

module.exports = function makeHelpers(TL) {
  const fps = TL.fps;
  const L = (id) => { const l = TL.lines[id]; if (!l) throw new Error('unknown line ' + id); return l; };
  const S = (id) => { const s = TL.scenes.find((x) => x.id === id); if (!s) throw new Error('unknown scene ' + id); return s; };

  // Approximate time a word/phrase is spoken: position in the text, weighted so
  // punctuation pauses ("...", ".", ",") take up time like they do in the audio.
  const PAUSE = { '.': 6, '?': 6, '!': 6, ',': 3, ':': 3, ';': 3 };
  function weights(text) {
    const w = [];
    for (let i = 0; i < text.length; i++) w.push(1 + (PAUSE[text[i]] || 0) * 1.4);
    return w;
  }
  const cache = {};
  function wt(id, phrase, occ = 0) {
    const l = L(id), low = l.text.toLowerCase();
    let idx = -1;
    for (let i = 0; i <= occ; i++) { idx = low.indexOf(phrase.toLowerCase(), idx + 1); if (idx < 0) throw new Error(`"${phrase}" not in ${id}`); }
    const w = cache[id] || (cache[id] = weights(l.text));
    let before = 0, total = 0;
    for (let i = 0; i < w.length; i++) { total += w[i]; if (i < idx) before += w[i]; }
    return l.start + l.dur * (before / total);
  }

  const bySpk = {};
  for (const l of Object.values(TL.lines)) (bySpk[l.spk] = bySpk[l.spk] || []).push(l);
  // mouth openness/width for a speaker at time t (0 when not speaking)
  function talk(spk, t) {
    for (const l of bySpk[spk] || []) {
      if (t >= l.start && t < l.end) {
        const f = (t - l.start) * fps, i = Math.floor(f), k = f - i;
        const o = lerp(l.open[i] || 0, l.open[i + 1] || 0, k), w = lerp(l.width[i] || 0, l.width[i + 1] || 0, k);
        return { open: o, width: w, talking: 1, line: l };
      }
    }
    return { open: 0, width: 0.4, talking: 0, line: null };
  }
  // smooth 0..1 "is this speaker in the middle of a line" (for head motion / glow)
  function speaking(spk, t, fade = 0.25) {
    let v = 0;
    for (const l of bySpk[spk] || []) v = Math.max(v, Math.min(prog(t, l.start - fade, l.start), 1 - prog(t, l.end, l.end + fade)));
    return v;
  }

  const DEF = { lids: 0.9, gx: 0, gy: 0, brow: 0, browTilt: 0, smile: 0, squint: 0, blush: 0, shine: 0, tilt: 0, mouthO: 0, tear: 0 };
  // keys: [[time, {props}, duration?], ...] sorted by time
  function face(t, keys) {
    const out = Object.assign({}, DEF, keys[0][1]);
    let prevArms = out.arms || 'down', curArms = prevArms, armK = 1;
    for (let i = 1; i < keys.length; i++) {
      const [kt, props, d = 0.45] = keys[i];
      const k = ease.inOut(prog(t, kt, kt + d));
      if (k <= 0) break;
      for (const [name, v] of Object.entries(props)) {
        if (name === 'arms') { if (v !== curArms) { prevArms = curArms; curArms = v; armK = k; } }
        else if (typeof v === 'number') out[name] = lerp(out[name] != null ? out[name] : DEF[name] || 0, v, k);
        else out[name] = v;
      }
    }
    out.arms = prevArms !== curArms && armK < 1 ? { a: prevArms, b: curArms, k: armK } : curArms;
    return out;
  }

  // world point (wx,wy) appears at screen (sx,sy) with zoom
  function camera(ctx, zoom, wx, wy, sx = U.W / 2, sy = U.H / 2) {
    ctx.translate(sx, sy); ctx.scale(zoom, zoom); ctx.translate(-wx, -wy);
  }

  // ---------- captions ----------
  const NOCAP = new Set(['r_comment']); // shown as on-screen typing instead
  function chunkLine(l) {
    const words = l.text.replace(/\s+/g, ' ').trim().split(' ');
    const chunks = []; let cur = [];
    const len = (a) => a.join(' ').length;
    for (const w of words) {
      // too long with this word? break at the last comma/period in the chunk if there is one
      if (cur.length && len([...cur, w]) > 44) {
        let j = -1;
        cur.forEach((x, i) => { if (/[,.;:?!]["”]?$/.test(x) && len(cur.slice(0, i + 1)) >= 12) j = i; });
        if (j >= 0 && j < cur.length - 1) { chunks.push(cur.slice(0, j + 1).join(' ')); cur = cur.slice(j + 1); } else { chunks.push(cur.join(' ')); cur = []; }
      }
      cur.push(w);
      const endSentence = /[.?!]["”]?$/.test(w) || /\.\.\.$/.test(w);
      const soft = /[,:;]$/.test(w);
      if ((endSentence && len(cur) > 14) || (soft && len(cur) > 30)) { chunks.push(cur.join(' ')); cur = []; }
    }
    if (cur.length) { if (chunks.length && len(cur) < 10) chunks[chunks.length - 1] += ' ' + cur.join(' '); else chunks.push(cur.join(' ')); }
    const wts = chunks.map((c) => c.length + 8);
    const tot = wts.reduce((a, b) => a + b, 0);
    let acc = 0;
    return chunks.map((c, i) => { const a = l.start + l.dur * acc / tot; acc += wts[i]; return { text: c, start: a, end: l.start + l.dur * acc / tot, spk: l.spk }; });
  }
  const CAPS = Object.values(TL.lines).filter((l) => !NOCAP.has(l.id)).flatMap(chunkLine).sort((a, b) => a.start - b.start);
  for (let i = 0; i < CAPS.length; i++) { // linger briefly after speech unless the next caption starts
    const next = CAPS[i + 1];
    CAPS[i].hold = Math.min(CAPS[i].end + 0.5, next ? next.start : Infinity);
  }
  const SPK = { riley: { name: 'Riley', col: '#6fd0dc' }, alex: { name: 'Alex', col: '#ffc85c' }, grandma: { name: 'Grandma', col: '#ffa6b8' } };
  function captions(ctx, t, opts = {}) {
    const c = CAPS.find((x) => t >= x.start && t < x.hold);
    if (!c) return;
    const a = Math.min(prog(t, c.start, c.start + 0.12), 1 - prog(t, c.hold - 0.12, c.hold));
    const y = opts.y || 1492;
    U.font(ctx, 50, 800);
    const lines = U.wrap(ctx, c.text, 860);
    const lh = 62, h = lines.length * lh + 34;
    const w = Math.max(...lines.map((s) => ctx.measureText(s).width)) + 70;
    U.withAlpha(ctx, a, () => {
      U.fillRR(ctx, U.W / 2 - w / 2, y - h / 2, w, h, 30, 'rgba(22,20,34,0.78)');
      const sp = SPK[c.spk];
      U.font(ctx, 28, 900);
      const nw = ctx.measureText(sp.name).width + 36;
      U.fillRR(ctx, U.W / 2 - w / 2 + 24, y - h / 2 - 24, nw, 44, 22, sp.col);
      U.text(ctx, sp.name, U.W / 2 - w / 2 + 24 + nw / 2, y - h / 2 - 1, { size: 28, weight: 900, color: '#1e1b2e' });
      lines.forEach((s, i) => U.text(ctx, s, U.W / 2, y - h / 2 + 17 + lh / 2 + i * lh, { size: 50, weight: 800, color: '#ffffff' }));
    });
  }

  return { TL, fps, L, S, wt, talk, speaking, face, camera, captions, CAPS };
};
