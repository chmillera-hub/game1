// Frame renderer. Usage:
//   node render.js still <seconds> <out.png>         – render one frame
//   node render.js range <f0> <f1> <out.mkv>          – render frames to a lossless segment
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const { clamp, lerp, ease, rgba, roundRect, noise } = require('./lib');
const { exParams, EX_DEFAULT } = require('./face');
const C = require('./chars');
const { layer, drawHill, drawAttic, drawRoof } = require('./sets');
const script = require('./script');
const { build, evalNum, evalObj, evalCam } = require('./timeline');

const FONTS = path.join(__dirname, '../fonts');
GlobalFonts.registerFromPath(path.join(FONTS, 'Baloo2[wght].ttf'), 'Baloo');
GlobalFonts.registerFromPath(path.join(FONTS, 'MysteryQuest-Regular.ttf'), 'MysteryQuest');

const W = +(process.env.W || 720), H = Math.round((W * 16) / 9), S = W / 1080, FPS = 24;
const lines = JSON.parse(fs.readFileSync(path.join(__dirname, '../work/lines_out.json')));
const TL = build(script, lines);
if (require.main === module && process.argv[2] === 'info') {
  console.log(JSON.stringify({ total: TL.total, frames: Math.ceil(TL.total * FPS) }));
  process.exit(0);
}
fs.writeFileSync(path.join(__dirname, '../work/timeline.json'), JSON.stringify({ total: TL.total, music: TL.music, sfx: TL.sfx, cues: TL.cues, sets: TL.camKeys.filter((k) => k.set).map((k) => ({ t: k.t, set: k.set })), speech: TL.speech.map((s) => ({ idx: s.idx, who: s.who, s: s.s, e: s.e, wav: s.wav, motif: s.motif, cues: s.cues })), recs: TL.recs.map((r) => ({ i: r.i, type: r.it.type, t0: r.t0, s: r.s, e: r.e })) }));

const POSES = {
  pip: [C.PIP_BASE, C.PIP_POSES], patch: [C.PATCH_BASE, C.PATCH_POSES], bram: [C.BRAM_BASE, C.BRAM_POSES],
  rattle: [C.SKEL_BASE, C.SKEL_POSES], clatter: [C.SKEL_BASE, C.SKEL_POSES], owl: [{}, {}],
};
// precompute pose key values
const poseKeyVals = {};
for (const w in TL.poseKeys) poseKeyVals[w] = TL.poseKeys[w].map((k) => ({ ...k, v: { ...POSES[w][0], ...(POSES[w][1][k.name] || {}) } }));

const ridgeY = script.ridgeY;
const LAYOUT = {
  roof: { pip: { x: 470, s: 1 }, patch: { x: 775, s: 1 }, bram: { x: 165, s: 0.9 } },
  attic: { rattle: { x: 385, y: 1345, s: 1 }, clatter: { x: 700, y: 1345, s: 1, flip: -1 } },
  hill: { pip: { x: 566, y: 653, s: 0.12 }, owl: { x: 905, y: 1106, s: 0.6 }, rattle: { x: 528, y: 1032, s: 0.27 }, clatter: { x: 612, y: 1032, s: 0.27, flip: -1 } },
};
const BRAM_PATH = [[1300, 430], [860, 520], [420, 600], [110, 720], [40, 900], [120, 1080], [165, 1184]];

function speechAt(T) {
  for (const sp of TL.speech) if (T >= sp.s - 0.02 && T <= sp.e + 0.06) return sp;
  return null;
}
function envAt(sp, T) {
  const f = (T - sp.s + 0.035) * 48;
  const i = Math.floor(f), u = f - i;
  const g = (a, j) => a[clamp(j, 0, a.length - 1)] || 0;
  const o = Math.max(lerp(g(sp.env, i), g(sp.env, i + 1), u), g(sp.env, i - 1) * 0.7);
  return { open: clamp(Math.pow(o, 0.85) * 1.05), cent: lerp(g(sp.cent, i), g(sp.cent, i + 1), u) };
}

function charState(w, T, set, V, sp) {
  const lay = (LAYOUT[set] || {})[w];
  if (!lay) return null;
  const vis = evalNum(TL.tracks[w + '.vis'], T, 1);
  if (vis < 0.5) return null;
  const e = evalObj(TL.exKeys[w], T, EX_DEFAULT);
  const P = evalObj(poseKeyVals[w], T, { ...POSES[w][0], ...(POSES[w][1].stand || POSES[w][1].sit || POSES[w][1].holdPumpkin || {}) });
  const x = set === 'roof' ? evalNum(TL.tracks[w + '.x'], T, lay.x) : lay.x;
  const y = set === 'roof' ? ridgeY(x) : lay.y;
  const st = { w, x, y, s: lay.s, flip: lay.flip || 1, e, P, t: T, V, open: e.mOpen, round: 0, mw: 1, blink: 0, look: [0, 0], nod: 0, light: 0 };
  // lip sync
  if (sp && sp.char === w) {
    const a = envAt(sp, T);
    st.open = Math.max(e.mOpen, a.open);
    st.round = clamp(1 - a.cent * 1.6) * a.open;
    st.mw = 0.85 + a.cent * 0.3;
    st.talk = a.open;
    st.e = { ...e, tilt: e.tilt + Math.sin(T * 5.3) * 0.03 * a.open };
  }
  // blinks
  for (const b of TL.auto[w].blinks) {
    if (b.t > T) break;
    const u = (T - b.t) / b.d;
    if (u >= 0 && u <= 1) st.blink = Math.max(st.blink, u < 0.4 ? u / 0.4 : 1 - (u - 0.4) / 0.6);
  }
  // listener nods
  for (const se of TL.sentenceEnds) {
    if (se.who === w) continue;
    const d = T - se.t - 0.12;
    if (d > -0.4 && d < 0.6) st.nod = Math.max(st.nod, Math.exp(-(d * d) / 0.03));
  }
  st.climb = evalNum(TL.tracks[w + '.climb'], T, 1);
  st.sitDown = evalNum(TL.tracks[w + '.sitDown'], T, 1);
  return st;
}

function headPos(st) {
  switch (st.w) {
    case 'pip': return [st.x, st.y - 200 * st.s];
    case 'patch': return [st.x, st.y - (500 - (1 - st.climb) * 650) * st.s];
    case 'bram': return [st.x, st.y - (500 - 150 * (st.P.kneel || 0)) * st.s];
    case 'owl': return [st.x, st.y - 128 * st.s];
    default: return [st.x, st.y - 470 * st.s];
  }
}

function targetVec(tg, st, all, set) {
  const hp = headPos(st);
  let p = null;
  if (Array.isArray(tg)) p = tg;
  else switch (tg) {
    case 'cam': return [0, 0];
    case 'down': return [0, 0.9];
    case 'up': return [0, -0.95];
    case 'far': return [-0.3, -0.5];
    case 'town': p = set === 'roof' ? [230, 1040] : set === 'hill' ? [150, 1300] : null; break;
    case 'hands': p = [st.x + ((st.P.ax + st.P.bx) / 2) * st.s, st.y + ((st.P.ay + st.P.by) / 2) * st.s]; break;
    case 'pumpkin': case 'patchPumpkin': { const pa = all.patch; if (pa) p = [pa.x + pa.P.pkx * pa.s, pa.y + pa.P.pky * pa.s]; break; }
    case 'pipPumpkin': { const pp = all.pip; if (pp) p = [pp.x + pp.P.pkx * pp.s, pp.y + pp.P.pky * pp.s]; break; }
    default: if (all[tg]) p = headPos(all[tg]);
  }
  if (!p) return [0, 0];
  let dx = (p[0] - hp[0]) / 300, dy = (p[1] - hp[1]) / 300;
  if (st.flip < 0) dx = -dx;
  const m = Math.hypot(dx, dy);
  if (m > 1) { dx /= m; dy /= m; }
  return [dx, dy];
}

function resolveLooks(states, T, set) {
  for (const w in states) {
    const st = states[w];
    const keys = TL.lookKeys[w] || [];
    let v = [0, 0], prev = null;
    let idx = -1;
    for (let i = 0; i < keys.length; i++) { if (keys[i].t > T) break; idx = i; }
    if (idx >= 0) {
      const k = keys[idx];
      const cur = targetVec(k.target, st, states, set);
      const before = idx > 0 ? targetVec(keys[idx - 1].target, st, states, set) : cur;
      const u = ease.soft(clamp((T - k.t) / Math.max(0.05, k.tr)));
      v = [lerp(before[0], cur[0], u), lerp(before[1], cur[1], u)];
    }
    // micro saccades
    const sa = TL.auto[w].sacc;
    let j = 0; while (j + 1 < sa.length && sa[j + 1].t <= T) j++;
    const a0 = sa[Math.max(0, j - 1)], a1 = sa[j];
    const su = clamp((T - a1.t) / 0.06);
    v = [v[0] + lerp(a0.x, a1.x, su), v[1] + lerp(a0.y, a1.y, su)];
    st.look = v;
  }
}

// ── subtitles ──
function wrap(ctx, text, maxW) {
  const words = text.split(' ');
  const out = [];
  let cur = '';
  for (const w of words) {
    const tryS = cur ? cur + ' ' + w : w;
    if (ctx.measureText(tryS).width > maxW && cur) { out.push(cur); cur = w; } else cur = tryS;
  }
  if (cur) out.push(cur);
  return out;
}

function drawSubtitle(ctx, T) {
  let found = null;
  for (const sp of TL.speech) {
    for (let k = 0; k < sp.sentences.length; k++) {
      const s = sp.sentences[k];
      const next = sp.sentences[k + 1];
      const end = next ? next.s - 0.02 : s.e + 0.45;
      if (T >= s.s - 0.08 && T <= end) found = { sp, s, a: clamp((T - s.s + 0.08) / 0.12) * clamp((end - T) / 0.15) };
    }
  }
  if (!found) return;
  const { sp, s, a } = found;
  const cast = script.cast[sp.who];
  const nar = !cast.name;
  ctx.setTransform(S, 0, 0, S, 0, 0);
  let fs = 50;
  ctx.font = `700 ${fs}px Baloo`;
  let rows = wrap(ctx, s.text, 900);
  if (rows.length > 3) { fs = 42; ctx.font = `700 ${fs}px Baloo`; rows = wrap(ctx, s.text, 920); }
  const lh = fs * 1.18;
  const yC = 1468;
  const top = yC - (rows.length * lh) / 2;
  const maxw = Math.max(...rows.map((r) => ctx.measureText(r).width));
  ctx.globalAlpha = a;
  ctx.beginPath(); roundRect(ctx, 540 - maxw / 2 - 30, top - 22 - (nar ? 0 : 30), maxw + 60, rows.length * lh + 36 + (nar ? 0 : 30), 26);
  ctx.fillStyle = 'rgba(12,8,22,0.62)'; ctx.fill();
  if (!nar) {
    ctx.font = '800 30px Baloo'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = cast.color; ctx.fillText(cast.name.split('').join(String.fromCharCode(8202)), 540, top + 6);
    ctx.font = `700 ${fs}px Baloo`;
  }
  const hi = new Map(sp.cues.filter((c) => c.kind !== 'mark').map((c) => [c.word.toLowerCase(), c.kind]));
  rows.forEach((row, i) => {
    const y = top + (i + 0.82) * lh;
    const words = row.split(' ');
    const total = ctx.measureText(row).width;
    let x = 540 - total / 2;
    ctx.textAlign = 'left';
    for (let wi = 0; wi < words.length; wi++) {
      const wd = words[wi] + (wi < words.length - 1 ? ' ' : '');
      const bare = words[wi].replace(/[^\w']/g, '').toLowerCase();
      const kind = hi.get(bare);
      ctx.save();
      if (nar) { ctx.translate(x, y); ctx.transform(1, 0, -0.16, 1, 0, 0); ctx.translate(-x, -y); }
      ctx.lineJoin = 'round'; ctx.lineWidth = 8; ctx.strokeStyle = 'rgba(10,6,18,0.95)'; ctx.strokeText(wd, x, y);
      ctx.fillStyle = kind === 'hi' ? '#ffd56b' : kind === 'lo' ? '#a9c2ff' : nar ? '#f6ebc8' : '#fffaf0';
      ctx.fillText(wd, x, y);
      ctx.restore();
      x += ctx.measureText(wd).width;
    }
  });
  ctx.globalAlpha = 1;
  ctx.textAlign = 'left';
}

function drawTitle(ctx, a) {
  if (a < 0.01) return;
  ctx.setTransform(S, 0, 0, S, 0, 0);
  ctx.globalAlpha = a;
  ctx.textAlign = 'center';
  ctx.font = '150px MysteryQuest';
  for (const [txt, y] of [['The House', 250], ['That Hums', 400]]) {
    ctx.shadowColor = 'rgba(255,150,60,0.9)'; ctx.shadowBlur = 40;
    ctx.lineJoin = 'round'; ctx.lineWidth = 14; ctx.strokeStyle = '#140c1c'; ctx.strokeText(txt, 540, y);
    ctx.shadowBlur = 0;
    const g = ctx.createLinearGradient(0, y - 110, 0, y + 10); g.addColorStop(0, '#fff3c4'); g.addColorStop(1, '#f2a54a');
    ctx.fillStyle = g; ctx.fillText(txt, 540, y);
  }
  ctx.font = '700 40px Baloo'; ctx.fillStyle = '#d8e8e2';
  ctx.lineWidth = 7; ctx.strokeStyle = '#140c1c'; ctx.strokeText('a little Halloween story', 540, 478); ctx.fillText('a little Halloween story', 540, 478);
  ctx.globalAlpha = 1; ctx.textAlign = 'left'; ctx.shadowColor = 'rgba(0,0,0,0)';
}

function vignette(ctx) {
  ctx.setTransform(S, 0, 0, S, 0, 0);
  const g = ctx.createRadialGradient(540, 900, 500, 540, 960, 1250);
  g.addColorStop(0, 'rgba(6,3,14,0)'); g.addColorStop(1, 'rgba(6,3,14,0.6)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 1920);
}

function renderFrame(ctx, T) {
  const V = {};
  for (const k in TL.tracks) if (k.startsWith('V.')) V[k.slice(2)] = evalNum(TL.tracks[k], T, 0);
  const cam = evalCam(TL.camKeys, T);
  const view = { cam, S, W, H };
  const sp = speechAt(T);
  const set = cam.set;
  const states = {};
  for (const w of ['pip', 'patch', 'bram', 'rattle', 'clatter', 'owl']) {
    const st = charState(w, T, set, V, sp);
    if (st) states[w] = st;
  }
  // witch flight
  const bram = states.bram;
  if (bram && Math.round(bram.P.broom) === 1) {
    const fly = V.bramFly ?? 1;
    const p = require('./lib').catmull(BRAM_PATH, fly), p2 = require('./lib').catmull(BRAM_PATH, Math.min(1, fly + 0.02));
    bram.x = p[0]; bram.y = p[1] + 60 * (1 - fly); bram.flying = fly < 0.98;
    bram.rot = clamp(Math.atan2(p2[1] - p[1], Math.abs(p2[0] - p[0]) + 1e-3) * 0.5, -0.4, 0.4) * (fly < 0.98 ? 1 : 0);
    bram.flip = p2[0] > p[0] + 0.5 ? 1 : -1;
  }
  resolveLooks(states, T, set);
  // lantern light on faces
  const pipLit = V.pipLit || 0;
  if (states.pip) states.pip.light = pipLit;
  if (states.bram) states.bram.light = pipLit * 0.35;
  if (states.patch) states.patch.light = Math.max(pipLit * 0.25, (V.patchTurn || 0) * 0.2);
  const pumpkinIn = (V.pumpkinToPip || 0) >= 0.5;
  if (states.pip && pumpkinIn) states.pip.pumpkin = {};
  if (states.bram) states.bram.offerPumpkin = true;
  if (set === 'hill' && states.pip) states.pip.pumpkin = pipLit > 0.01 ? {} : null;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const draw = (fn, st) => () => { if (st) fn(ctx, st); };
  if (set === 'hill') {
    drawHill(ctx, view, T, V, {
      pip: draw(C.drawPip, states.pip),
      owl: draw(C.drawOwl, states.owl),
      skels: () => {
        if (states.rattle) C.drawSkeleton(ctx, { ...states.rattle, open: 0 }, 'rattle');
        if (states.clatter) C.drawSkeleton(ctx, { ...states.clatter, open: 0 }, 'clatter');
      },
    });
    if (states.pip && pipLit > 0.01) {
      layer(ctx, view, 1);
      const g = ctx.createRadialGradient(566, 640, 2, 566, 640, 120);
      g.addColorStop(0, rgba('#ffd27a', 0.6 * pipLit)); g.addColorStop(1, 'rgba(255,180,80,0)');
      ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(400, 500, 330, 300); ctx.globalCompositeOperation = 'source-over';
    }
  } else if (set === 'attic') {
    drawAttic(ctx, view, T, V, {
      skels: () => {
        if (states.rattle) C.drawSkeleton(ctx, states.rattle, 'rattle');
        if (states.clatter) C.drawSkeleton(ctx, states.clatter, 'clatter');
      },
    });
  } else if (set === 'roof') {
    const pa = states.patch;
    drawRoof(ctx, view, T, V, {
      behind: () => { if (pa && pa.climb < 0.995) C.drawPatch(ctx, pa); },
      front: () => {
        if (pa && pa.climb >= 0.995) C.drawPatch(ctx, pa);
        if (states.pip) {
          if (states.pip.pumpkin && (V.pumpkinToPip || 0) < 1) {
            // pumpkin travelling from the witch's hand
            const b = states.bram, u = clamp(((V.pumpkinToPip || 0) - 0.5) * 2);
            if (b) {
              const bx = (b.x + b.P.bx * b.s + 6 * b.s - states.pip.x) / states.pip.s, by = (b.y + (b.P.by - 40) * b.s - states.pip.y) / states.pip.s;
              states.pip.pumpkin = { x: lerp(bx, states.pip.P.pkx, ease.soft(u)), y: lerp(by, states.pip.P.pky, ease.soft(u)) };
            }
          }
          C.drawPip(ctx, states.pip);
        }
        if (states.bram) C.drawBram(ctx, states.bram);
      },
    }, ridgeY);
    // warm pumpkin light spill
    layer(ctx, view, 1);
    if (pipLit > 0.01 && states.pip) {
      const px = states.pip.x, py = states.pip.y - 60;
      const g = ctx.createRadialGradient(px, py, 10, px, py, 380);
      g.addColorStop(0, rgba('#ffb04a', 0.3 * pipLit)); g.addColorStop(1, 'rgba(255,160,60,0)');
      ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(px - 400, py - 400, 800, 800); ctx.globalCompositeOperation = 'source-over';
    }
  }
  vignette(ctx);
  drawTitle(ctx, V.titleA || 0);
  drawSubtitle(ctx, T);
}

function main() {
  const mode = process.argv[2];
  const canvas = createCanvas(W, H);
  const ctx = canvas.getContext('2d');
  if (mode === 'still') {
    const ts = process.argv[3].split(',').map(Number);
    const out = process.argv[4];
    if (ts.length === 1) { renderFrame(ctx, ts[0]); fs.writeFileSync(out, canvas.toBuffer('image/png')); return; }
    // contact sheet
    const cols = Math.min(4, ts.length), rows = Math.ceil(ts.length / cols);
    const sheet = createCanvas(W * cols / 2, H * rows / 2), sc = sheet.getContext('2d');
    ts.forEach((t, i) => { renderFrame(ctx, t); sc.drawImage(canvas, (i % cols) * W / 2, Math.floor(i / cols) * H / 2, W / 2, H / 2); sc.fillStyle = '#fff'; sc.font = '20px Baloo'; sc.fillText(t.toFixed(1), (i % cols) * W / 2 + 8, Math.floor(i / cols) * H / 2 + 22); });
    fs.writeFileSync(out, sheet.toBuffer('image/png'));
    return;
  }
  if (mode === 'range') {
    const f0 = +process.argv[3], f1 = +process.argv[4], out = process.argv[5];
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'ultrafast', '-qp', '0', '-pix_fmt', 'yuv444p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    let f = f0;
    const t0 = Date.now();
    const pump = () => {
      while (f < f1) {
        renderFrame(ctx, f / FPS);
        const ok = ff.stdin.write(Buffer.from(canvas.data()));
        f++;
        if (f % 120 === 0) process.stderr.write(`[${path.basename(out)}] ${f - f0}/${f1 - f0} ${((Date.now() - t0) / (f - f0)).toFixed(0)}ms/f\n`);
        if (!ok) { ff.stdin.once('drain', pump); return; }
      }
      ff.stdin.end();
    };
    ff.on('close', (code) => process.exit(code));
    pump();
  }
}
if (require.main === module) main();
module.exports = { TL, renderFrame, W, H, FPS };
