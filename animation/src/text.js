// Subtitles, name labels and title cards (screen space, 1080x1920 logical).
'use strict';
const { GlobalFonts } = require('@napi-rs/canvas');
const { clamp, smooth, rgba, easeOutBack } = require('./core');

let fontsReady = false;
function fonts() {
  if (fontsReady) return;
  const reg = (p, n) => { try { GlobalFonts.registerFromPath(p, n); } catch (e) { /* optional */ } };
  reg('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 'InterSemi');
  reg('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 'InterBold');
  reg('/usr/share/fonts/opentype/inter/Inter-MediumItalic.otf', 'InterItalic');
  reg('/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf', 'InterXB');
  reg('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 'Emoji');
  fontsReady = true;
}

const SPEAKER = {
  maya: { name: 'MAYA', color: '#c7d98a' }, eli: { name: 'ELI', color: '#b9cde0' }, nana: { name: 'NANA', color: '#e6b3cc' },
  anger: { name: 'ANGER', color: '#ff7a63' }, annoy: { name: 'ANNOYANCE', color: '#ffe066' }, fear: { name: 'FEAR', color: '#ffb066' },
  sad: { name: 'SADNESS', color: '#9cc8f2' }, nar: null,
};

// Split a line into subtitle chunks (<= 2 rows) with word timing.
function buildSubs(schedule, ctx) {
  fonts();
  const subs = [];
  const maxW = 880;
  for (const ln of schedule.lines) {
    const toks = ln.text.match(/\S+/g) || [];
    // map text tokens to timed words
    let wi = 0;
    const tw = toks.map((tok) => {
      const has = /[A-Za-z0-9]/.test(tok);
      const w = has ? ln.words[Math.min(wi, ln.words.length - 1)] : null;
      if (has) wi++;
      return { tok, t0: w ? w.t0 : null, t1: w ? w.t1 : null };
    });
    for (let i = 0; i < tw.length; i++) { // fill punctuation-only tokens
      if (tw[i].t0 === null) { const p = tw[i - 1] || tw[i + 1]; tw[i].t0 = p ? p.t0 : ln.t0; tw[i].t1 = p ? p.t1 : ln.t1; }
    }
    const italic = ln.sp === 'nar';
    ctx.font = `${italic ? 'italic ' : ''}54px ${italic ? 'InterItalic' : 'InterSemi'}`;
    // split into sentence-ish groups, then into chunks of <= 2 balanced rows (no orphans)
    const width = (ws) => ctx.measureText(ws.map((x) => x.tok).join(' ')).width;
    const groups = [];
    let g = [];
    tw.forEach((x, i) => { g.push(x); if (/[.?!]$/.test(x.tok) && i < tw.length - 1 && width(g) > maxW * 0.45) { groups.push(g); g = []; } });
    if (g.length) { if (groups.length && width(g) < maxW * 0.35) groups[groups.length - 1].push(...g); else groups.push(g); }
    const chunks = [];
    for (const grp of groups) {
      const total = width(grp);
      const nChunks = Math.max(1, Math.ceil(total / (maxW * 1.9)));
      const per = Math.ceil(grp.length / nChunks);
      for (let c = 0; c < grp.length; c += per) chunks.push(grp.slice(c, c + per));
    }
    for (const ch of chunks) {
      let rows;
      if (width(ch) <= maxW) rows = [ch];
      else {
        let best = null;
        for (let k = 1; k < ch.length; k++) {
          const a = width(ch.slice(0, k)), b = width(ch.slice(k));
          const score = Math.max(a, b) + (/[,.?!]$/.test(ch[k - 1].tok) ? -60 : 0);
          if (!best || score < best.score) best = { k, score };
        }
        rows = [ch.slice(0, best.k), ch.slice(best.k)];
      }
      subs.push({ sp: ln.sp, id: ln.id, rows, t0: ch[0].t0 - 0.12, t1: ch[ch.length - 1].t1, italic, lineEnd: ln.t1 });
    }
  }
  // each chunk holds until the next one starts (max +0.9 s after its last word)
  for (let i = 0; i < subs.length; i++) {
    const nx = subs[i + 1];
    subs[i].hold = Math.min(subs[i].t1 + 0.9, nx ? nx.t0 - 0.02 : subs[i].t1 + 0.9);
  }
  return subs;
}

function drawSubs(ctx, subs, T, y0 = 1460) {
  fonts();
  const s = subs.find((x) => T >= x.t0 && T <= x.hold);
  if (!s) return;
  const a = smooth((T - s.t0) / 0.12) * (1 - smooth((T - s.hold + 0.12) / 0.12));
  const font = `${s.italic ? 'italic ' : ''}54px ${s.italic ? 'InterItalic' : 'InterSemi'}`;
  ctx.save();
  ctx.font = font;
  ctx.textBaseline = 'alphabetic';
  const lh = 68;
  const widths = s.rows.map((r) => ctx.measureText(r.map((w) => w.tok).join(' ')).width);
  const maxw = Math.max(...widths);
  const tag = SPEAKER[s.sp];
  const boxH = s.rows.length * lh + 34 + (tag ? 44 : 0);
  const top = y0 - boxH;
  // soft dark box
  ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(18,12,20,0.58)';
  roundRect(ctx, 540 - maxw / 2 - 30, top, maxw + 60, boxH, 26);
  ctx.fill();
  let y = top + 22;
  if (tag) {
    ctx.font = '30px InterBold';
    ctx.fillStyle = tag.color;
    ctx.textAlign = 'center';
    ctx.fillText(tag.name, 540, y + 30);
    y += 44;
    ctx.font = font;
  }
  ctx.textAlign = 'left';
  s.rows.forEach((row, ri) => {
    const w = widths[ri];
    let x = 540 - w / 2;
    const by = y + lh * (ri + 1) - 18;
    for (let k = 0; k < row.length; k++) {
      const word = row[k];
      const spoken = T >= word.t0 - 0.03;
      ctx.fillStyle = spoken ? 'rgba(255,255,255,1)' : 'rgba(255,255,255,0.62)';
      const txt = word.tok + (k < row.length - 1 ? ' ' : '');
      ctx.fillText(txt, x, by);
      x += ctx.measureText(txt).width;
    }
  });
  ctx.restore();
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

// Name label pill near a screen point (sx, sy), pointing at it.
function drawLabel(ctx, text, emoji, color, sx, sy, age, dur = 3.2, side = 0) {
  fonts();
  if (age < 0 || age > dur) return;
  const pop = easeOutBack(clamp(age / 0.35));
  const a = smooth(age / 0.2) * (1 - smooth((age - dur + 0.4) / 0.4));
  ctx.save();
  ctx.globalAlpha = a;
  ctx.font = '40px InterBold';
  const tw = ctx.measureText(text).width;
  const ew = emoji ? 52 : 0;
  const w = tw + ew + 48, h = 66;
  let x = clamp(sx - w / 2 + side * (w / 2 + 40), 24, 1080 - 24 - w);
  let y = clamp(sy - h - 26, 140, 1700);
  ctx.translate(x + w / 2, y + h / 2);
  ctx.scale(pop, pop);
  ctx.translate(-(x + w / 2), -(y + h / 2));
  ctx.fillStyle = 'rgba(20,14,22,0.72)';
  roundRect(ctx, x, y, w, h, 33);
  ctx.fill();
  ctx.strokeStyle = color; ctx.lineWidth = 4;
  roundRect(ctx, x, y, w, h, 33); ctx.stroke();
  // pointer
  const px = clamp(sx, x + 30, x + w - 30);
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.moveTo(px - 12, y + h); ctx.lineTo(px + 12, y + h); ctx.lineTo(px, y + h + 16); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, x + 24, y + h / 2 + 2);
  if (emoji) { ctx.font = '38px Emoji'; ctx.fillText(emoji, x + 24 + tw + 12, y + h / 2 + 2); }
  ctx.restore();
}

// Centered title text with soft shadow.
function drawTitle(ctx, lines, y, a, opts = {}) {
  fonts();
  if (a <= 0.001) return;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const tot = lines.reduce((acc, l) => acc + (l.lh || 80), 0);
  const gb = ctx.createRadialGradient(540, y + tot / 2 - 40, 10, 540, y + tot / 2 - 40, 560);
  gb.addColorStop(0, 'rgba(12,8,14,0.5)'); gb.addColorStop(0.55, 'rgba(12,8,14,0.28)'); gb.addColorStop(1, 'rgba(12,8,14,0)');
  ctx.save(); ctx.translate(540, y + tot / 2 - 40); ctx.scale(1, Math.max(0.3, (tot + 120) / 1000)); ctx.translate(-540, -(y + tot / 2 - 40));
  ctx.fillStyle = gb; ctx.fillRect(0, y - 700, 1080, 1400); ctx.restore();
  let yy = y;
  for (const ln of lines) {
    ctx.font = ln.font || '64px InterXB';
    ctx.shadowColor = 'rgba(0,0,0,0.55)'; ctx.shadowBlur = 18;
    ctx.fillStyle = ln.color || '#fff8ec';
    if (ln.spacing) { // letter-spaced caps
      const chars = [...ln.text];
      const widths = chars.map((c) => ctx.measureText(c).width + ln.spacing);
      let x = 540 - widths.reduce((s, w) => s + w, 0) / 2;
      ctx.textAlign = 'left';
      chars.forEach((c, i) => { ctx.fillText(c, x, yy); x += widths[i]; });
      ctx.textAlign = 'center';
    } else ctx.fillText(ln.text, 540, yy);
    yy += ln.lh || 80;
  }
  ctx.restore();
}

module.exports = { buildSubs, drawSubs, drawLabel, drawTitle, roundRect, fonts, SPEAKER };
