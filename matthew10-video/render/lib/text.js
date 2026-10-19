'use strict';
// Subtitles, scripture panels and title cards.

const { GlobalFonts } = require('@napi-rs/canvas');
const { clamp, smooth } = require('./util');
const { W, H } = require('./stage');

GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 'InterSemi');
GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-MediumItalic.otf', 'InterItalic');
GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-Medium.otf', 'InterMed');
GlobalFonts.registerFromPath('/opt/fonts/EBGaramond[wght].ttf', 'Garamond');
GlobalFonts.registerFromPath('/opt/fonts/EBGaramond-Italic[wght].ttf', 'GaramondItalic');

const norm = (w) => w.toLowerCase().replace(/[^a-z']/g, '');

// Map each script word to a start/end time using ASR words when available.
function wordTimes(line) {
  const words = line.text.split(/\s+/).filter(Boolean);
  const n = words.length;
  const dur = line.end - line.start;
  const asr = (line.words || []).filter((w) => norm(w[2]).length);
  if (asr.length >= 2) {
    return words.map((w, i) => {
      const j = Math.min(asr.length - 1, Math.round((i * (asr.length - 1)) / Math.max(1, n - 1)));
      return { w, s: line.start + asr[j][0], e: line.start + asr[j][1] };
    });
  }
  // fallback: proportional to character count
  const total = words.reduce((a, w) => a + w.length + 1, 0);
  let acc = 0;
  return words.map((w) => {
    const s = line.start + (acc / total) * dur;
    acc += w.length + 1;
    return { w, s, e: line.start + (acc / total) * dur };
  });
}

function wrap(ctx, text, maxW) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines = [];
  let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (ctx.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t;
  }
  if (cur) lines.push(cur);
  return lines;
}

// Split a line into subtitle chunks (≤ 2 rows each) with timings.
function chunks(ctx, line, font, maxW) {
  ctx.font = font;
  const wt = wordTimes(line);
  const out = [];
  let cur = [];
  const flush = () => { if (cur.length) { out.push(cur); cur = []; } };
  for (let i = 0; i < wt.length; i++) {
    cur.push(wt[i]);
    const text = cur.map((x) => x.w).join(' ');
    const rows = wrap(ctx, text, maxW).length;
    const endSentence = /[.!?—]$/.test(wt[i].w) || /\.\.\.$/.test(wt[i].w);
    if (rows > 2) { // too long: break at the last comma/period inside the chunk if there is one
      cur.pop();
      let cutAt = -1;
      for (let j = cur.length - 1; j >= Math.floor(cur.length * 0.4); j--) if (/[,.;:!?]$/.test(cur[j].w)) { cutAt = j; break; }
      if (cutAt >= 0 && cutAt < cur.length - 1) {
        const rest = cur.slice(cutAt + 1);
        cur = cur.slice(0, cutAt + 1); flush(); cur = rest;
      } else flush();
      cur.push(wt[i]);
    } else if (endSentence && text.length > 24 && i < wt.length - 1) {
      flush();
    }
  }
  flush();
  return out.map((ws, k) => ({
    text: ws.map((x) => x.w).join(' '),
    s: k === 0 ? line.start - 0.05 : ws[0].s - 0.08,
    e: k === out.length - 1 ? line.end + 0.35 : out[k + 1][0].s - 0.08,
  }));
}

const STYLE = {
  default: { font: '600 50px InterSemi', color: '#ffffff', lh: 64 },
  ai: { font: '50px InterItalic', color: '#d6f1ff', lh: 64 },
  narrator: { font: '58px GaramondItalic', color: '#fbefdc', lh: 68 },
};

function drawSubtitle(ctx, text, style, alpha, y) {
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.font = style.font;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const rows = wrap(ctx, text, 880);
  const y0 = y - ((rows.length - 1) * style.lh) / 2;
  ctx.globalAlpha = alpha;
  ctx.lineJoin = 'round';
  rows.forEach((r, i) => {
    const yy = y0 + i * style.lh;
    ctx.shadowColor = 'rgba(0,0,0,0.75)';
    ctx.shadowBlur = 14;
    ctx.strokeStyle = 'rgba(10,8,8,0.82)';
    ctx.lineWidth = 7;
    ctx.strokeText(r, W / 2, yy);
    ctx.shadowBlur = 0;
    ctx.fillStyle = style.color;
    ctx.fillText(r, W / 2, yy);
  });
  ctx.restore();
}

class Subtitles {
  constructor(ctx, timeline) {
    this.items = [];
    for (const line of timeline.lines) {
      if (line.verse) continue;
      const st = STYLE[line.who] || STYLE.default;
      for (const c of chunks(ctx, line, st.font, 880)) this.items.push({ ...c, style: st, who: line.who });
    }
    this.items.sort((a, b) => a.s - b.s);
    // Avoid overlaps: clip each chunk's end at the next chunk's start.
    for (let i = 0; i < this.items.length - 1; i++) this.items[i].e = Math.min(this.items[i].e, this.items[i + 1].s - 0.02);
  }
  draw(ctx, t, y = 1440) {
    for (const it of this.items) {
      if (t < it.s - 0.01 || t > it.e + 0.12) continue;
      const a = clamp((t - it.s) / 0.12) * (1 - clamp((t - it.e) / 0.12));
      if (a > 0) drawSubtitle(ctx, it.text, it.style, a, y);
    }
  }
}

// Scripture panel: the verse in serif, words brightening as they are read.
function drawVerse(ctx, line, t, opts = {}) {
  const wt = wordTimes(line);
  const fontSize = opts.size || 58;
  const lh = Math.round(fontSize * 1.28);
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.font = `${fontSize}px Garamond`;
  ctx.textBaseline = 'middle';
  const maxW = opts.maxW || 900;
  const prefix = '> “';
  const words = wt.map((x, i) => (i === 0 ? prefix + x.w : x.w) + (i === wt.length - 1 ? '”' : ''));
  if (opts.cite) words.push(`(${opts.cite})`);
  // layout rows
  const rows = [];
  let cur = [];
  let curW = 0;
  const space = ctx.measureText(' ').width;
  for (let i = 0; i < words.length; i++) {
    const w = ctx.measureText(words[i]).width;
    if (cur.length && curW + space + w > maxW) { rows.push({ items: cur, w: curW }); cur = []; curW = 0; }
    cur.push({ i, text: words[i], w });
    curW += (cur.length > 1 ? space : 0) + w;
  }
  if (cur.length) rows.push({ items: cur, w: curW });
  const y0 = (opts.y || 520) - ((rows.length - 1) * lh) / 2;
  const fade = opts.alpha ?? 1;
  rows.forEach((r, k) => {
    let x = W / 2 - r.w / 2;
    const y = y0 + k * lh;
    for (const it of r.items) {
      const isCite = it.i >= wt.length;
      const ws = isCite ? wt[wt.length - 1].e : wt[it.i].s;
      const lit = smooth((t - ws + 0.1) / 0.3);
      const a = fade * (0.34 + 0.66 * lit);
      ctx.globalAlpha = a;
      ctx.shadowColor = 'rgba(0,0,0,0.9)';
      ctx.shadowBlur = 16;
      ctx.fillStyle = isCite ? '#f3dcc0' : '#fff7ea';
      ctx.fillText(it.text, x, y);
      ctx.shadowBlur = 0;
      x += it.w + space;
    }
  });
  ctx.restore();
}

function drawTitle(ctx, alpha, opts = {}) {
  if (alpha <= 0) return;
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = alpha;
  const band = ctx.createLinearGradient(0, 0, 0, 560);
  band.addColorStop(0, 'rgba(8,4,2,0.72)');
  band.addColorStop(0.6, 'rgba(8,4,2,0.45)');
  band.addColorStop(1, 'rgba(8,4,2,0)');
  ctx.fillStyle = band; ctx.fillRect(0, 0, W, 560);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.shadowColor = 'rgba(0,0,0,0.85)';
  ctx.shadowBlur = 18;
  ctx.font = '600 30px InterSemi';
  ctx.fillStyle = '#f5d9b0';
  ctx.fillText('M A T T H E W   1 0', W / 2, opts.y0 || 210);
  ctx.font = '86px Garamond';
  ctx.fillStyle = '#fff6e8';
  ctx.fillText('Not Peace,', W / 2, (opts.y0 || 210) + 92);
  ctx.fillText('But a Sword', W / 2, (opts.y0 || 210) + 186);
  ctx.restore();
}

function drawEndCard(ctx, alpha) {
  if (alpha <= 0) return;
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = alpha;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.shadowColor = 'rgba(0,0,0,0.85)';
  ctx.shadowBlur = 18;
  ctx.font = '66px Garamond';
  ctx.fillStyle = '#fff6e8';
  const rows = ['> “So don’t be afraid;', 'you are worth more', 'than many sparrows.”'];
  rows.forEach((r, i) => ctx.fillText(r, W / 2, 380 + i * 84));
  ctx.font = '44px Garamond';
  ctx.fillStyle = '#f3dcc0';
  ctx.fillText('(Matthew 10:31)', W / 2, 380 + 3 * 84 + 10);
  ctx.restore();
}

module.exports = { Subtitles, drawVerse, drawTitle, drawEndCard, wordTimes, wrap };
