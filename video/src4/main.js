// ---------- frame assembly: shots, transitions, subtitles, name labels ----------
const OUT = document.getElementById('c'), octx = OUT.getContext('2d');
const BUF = mkCanvas(), bctx = BUF.getContext('2d');
const SPK = { NARRATOR: ['Narrator', '#f0d7a0'], JESUS: ['Jesus', '#ffb09a'], HOST: ['Host', '#8ae0d8'], KAYLA: ['Kayla', '#ffa8d0'], DANA: ['Dana', '#a8c0ff'], PRIYA: ['Priya', '#ffd27a'], MARISOL: ['Marisol', '#a8e0b8'], BARTENDER: ['Bartender', '#d8d8d8'] };
let CHUNKS = [];
function alignTokens(l) { // punctuated script tokens with the time each is spoken
  const toks = l.text.split(/\s+/), norm = s => s.toLowerCase().replace(/[^a-z0-9']/g, '');
  let wi = 0; const tt = [];
  for (const tok of toks) {
    const n = norm(tok); let t = wi < l.words.length ? l.words[wi].t : l.end; let acc = '';
    while (wi < l.words.length && acc.length < n.length) { acc += norm(l.words[wi].w); wi++; }
    tt.push([tok, t]);
  }
  return tt;
}
function buildChunks() {
  for (const l of TL.lines) {
    if (!l.sp || SUPPRESS.has(l.id)) continue;
    const tt = alignTokens(l);
    let cur = [], len = 0;
    const flush = () => { if (cur.length) { CHUNKS.push({ sp: l.sp, text: cur.map(c => c[0]).join(' '), t0: cur[0][1], line: l }); cur = []; len = 0; } };
    tt.forEach(([tok, t], i) => {
      if (len + tok.length > 30 && cur.length) flush();
      cur.push([tok, t]); len += tok.length + 1;
      if (/[.?!]$/.test(tok) || (/,$/.test(tok) && len > 14)) flush();
    });
    flush();
  }
  for (let i = 0; i < CHUNKS.length; i++) {
    const c = CHUNKS[i], n = CHUNKS[i + 1];
    c.t1 = (n && n.line === c.line) ? n.t0 : c.line.end + .35;
  }
}
function drawSubs(ctx, t) {
  const c = CHUNKS.find(c => t >= c.t0 - .05 && t < c.t1);
  if (!c || (c.line.id === 'g5' && c.text === 'Write it anyway.')) return;
  const a = clamp((t - c.t0 + .05) / .12) * clamp((c.t1 - t) / .1);
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center';
  ctx.font = '700 40px Inter';
  const lines = wrap(ctx, c.text, 620), y0 = 1030 - (lines.length - 1) * 48;
  const [name, col] = SPK[c.sp];
  ctx.font = '700 22px Inter'; ctx.letterSpacing = '3px';
  ctx.lineWidth = 5; ctx.strokeStyle = 'rgba(0,0,0,.75)'; ctx.strokeText(name.toUpperCase(), 360, y0 - 48); ctx.fillStyle = col; ctx.fillText(name.toUpperCase(), 360, y0 - 48);
  ctx.letterSpacing = '0px'; ctx.font = '700 40px Inter'; ctx.lineJoin = 'round';
  lines.forEach((ln, i) => { ctx.lineWidth = 9; ctx.strokeStyle = 'rgba(0,0,0,.82)'; ctx.strokeText(ln, 360, y0 + i * 48); ctx.fillStyle = '#ffffff'; ctx.fillText(ln, 360, y0 + i * 48); });
  ctx.restore();
}
function drawLabels(ctx, t) {
  for (const L of LABELS) {
    const D = L.dur || 3.2, d = t - L.t0; if (d < 0 || d > D) continue;
    const a = clamp(d / .3) * clamp((D - d) / .4);
    ctx.save(); ctx.globalAlpha = a; ctx.font = '600 24px Inter'; const w = ctx.measureText(L.text).width + 30;
    ctx.fillStyle = 'rgba(10,10,14,.6)'; roundRect(ctx, L.x - w / 2, L.y - 20 - (1 - a) * 6, w, 40, 20); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.fillText(L.text, L.x, L.y + 8 - (1 - a) * 6); ctx.restore();
  }
}
function drawShot(ctx, s, t) { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none'; s.draw(ctx, t); ctx.restore(); }
window.renderFrame = function (i, fmt) {
  const t = i / FPS;
  let k = SHOTS.findIndex(s => t >= s.t0 && t < s.t1); if (k < 0) k = t < SHOTS[0].t0 ? 0 : SHOTS.length - 1;
  const s = SHOTS[k];
  drawShot(octx, s, t);
  if (s.xin > 0 && k > 0 && t < s.t0 + s.xin) {
    const a = easeIO((t - s.t0) / s.xin);
    drawShot(bctx, SHOTS[k - 1], t);
    octx.save(); octx.globalAlpha = 1 - a; octx.drawImage(BUF, 0, 0); octx.restore();
  }
  drawLabels(octx, t);
  drawSubs(octx, t);
  return fmt ? OUT.toDataURL(fmt, .92) : null;
};
window.init = async function () {
  TL = window.TLDATA;
  try { await document.fonts.load('700 40px Inter'); } catch (e) {}
  buildShots(); buildChunks();
  SHOTS.sort((a, b) => a.t0 - b.t0);
  return { frames: Math.ceil((TL.total + .5) * FPS), shots: SHOTS.length };
};
