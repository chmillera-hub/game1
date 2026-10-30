// Group c vignettes for "The Last Witness".
// Each key: draw(ctx, w, h, p) with p = { t, u, dur, params, seed, full }. Deterministic, full-frame paint.
'use strict';
const U = require('../lib/util');
const FX = require('../lib/fx');

const TAU = Math.PI * 2;
const { clamp, lerp, smooth, easeInOut, rgba, mix, shade } = U;

const GOLD = [255, 211, 138], AMBER = [255, 184, 92], CYAN = [127, 232, 255];
const CRIMSON = [214, 48, 74], DARKRED = [107, 20, 38], ASH = [150, 150, 165];

// ---------------------------------------------------------------- helpers
function rr(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}
function night(ctx, w, h, p, n, top = [6, 9, 21], bot = [20, 26, 51], fade) {
  FX.bg(ctx, w, h, top, bot);
  if (n > 0) FX.stars(ctx, w, h, p.t, (p.seed | 0) + 11, n, fade ? { fade } : {});
}
// a hand made of light, with a forearm that fades out toward the frame edge
function lightHand(ctx, x, y, ang, size, pose, col, opts = {}) {
  const a = opts.alpha ?? 1;
  if (a <= 0) return;
  // forearm: from wrist backwards (opposite to fingers)
  const fa = opts.armAng ?? ang;
  const dx = -Math.sin(fa), dy = Math.cos(fa);
  const len = size * (opts.arm ?? 1.6);
  const g = ctx.createLinearGradient(x, y, x + dx * len, y + dy * len);
  g.addColorStop(0, rgba(col, 0.95 * a)); g.addColorStop(1, rgba(col, 0));
  ctx.save();
  ctx.strokeStyle = g; ctx.lineCap = 'round';
  ctx.lineWidth = size * 0.36;
  ctx.beginPath(); ctx.moveTo(x - dx * size * 0.05, y - dy * size * 0.05); ctx.lineTo(x + dx * len, y + dy * len); ctx.stroke();
  ctx.restore();
  FX.glow(ctx, x + Math.sin(ang) * size * 0.45, y - Math.cos(ang) * size * 0.45, size * 1.1, col, 0.22 * a);
  ctx.save(); ctx.globalAlpha *= a;
  FX.hand(ctx, x, y, ang, size, pose, { skin: col, shadow: shade(col, -0.28), outline: shade(col, 0.45), mirror: !!opts.mirror, back: !!opts.back });
  ctx.restore();
}
// pressed hands seen from the front: fingers of both hands meeting at the tips, thumbs side by side
function prayerHands(ctx,x,y,s,col){
    ctx.save(); ctx.translate(x,y);
  ctx.lineCap='round'; ctx.lineJoin='round';
  for (const sg of [-1,1]){ const g=ctx.createLinearGradient(0,0,sg*s*0.35,s*0.8); g.addColorStop(0,rgba(shade(col,-0.1),0.95)); g.addColorStop(1,rgba(col,0));
    ctx.strokeStyle=g; ctx.lineWidth=s*0.17; ctx.beginPath(); ctx.moveTo(sg*s*0.07,-s*0.05); ctx.lineTo(sg*s*0.35,s*0.8); ctx.stroke(); }
  const ol=rgba(shade(col,0.5),0.9), sk=rgba(col), sh=rgba(shade(col,-0.3),0.6);
  // fingers: [baseX, baseY, tipX, tipY, width]
  const F=[[0.15,-0.5,0.085,-0.8,0.06],[0.12,-0.52,0.06,-0.9,0.065],[0.085,-0.54,0.035,-0.97,0.068],[0.04,-0.55,0.012,-0.93,0.066]];
  const palm=()=>{ ctx.beginPath(); ctx.moveTo(0,-s*0.58);
    ctx.bezierCurveTo(s*0.12,-s*0.58,s*0.19,-s*0.52,s*0.185,-s*0.38);
    ctx.bezierCurveTo(s*0.18,-s*0.2,s*0.15,-s*0.06,s*0.12,s*0.0);
    ctx.quadraticCurveTo(0,s*0.04,-s*0.12,s*0.0);
    ctx.bezierCurveTo(-s*0.15,-s*0.06,-s*0.18,-s*0.2,-s*0.185,-s*0.38);
    ctx.bezierCurveTo(-s*0.19,-s*0.52,-s*0.12,-s*0.58,0,-s*0.58); ctx.closePath(); };
  const fingers=(extra,style)=>{ for (const sg of [-1,1]) for (const f of F){ ctx.strokeStyle=style; ctx.lineWidth=(f[4]+extra)*s; ctx.beginPath(); ctx.moveTo(sg*f[0]*s,f[1]*s); ctx.quadraticCurveTo(sg*(f[0]*0.4+f[2]*0.6+0.012)*s,(f[1]*0.4+f[3]*0.6)*s,sg*f[2]*s,f[3]*s); ctx.stroke(); } };
  // outline pass
  fingers(0.022,ol); palm(); ctx.strokeStyle=ol; ctx.lineWidth=s*0.022; ctx.stroke();
  // fill pass, back fingers first so the outer ones overlap
  palm(); ctx.fillStyle=sk; ctx.fill();
  for (const sg of [-1,1]) for (let i=0;i<4;i++){ const f=F[i]; ctx.strokeStyle=rgba(shade(col,-0.08*(3-i)*0.5)); ctx.lineWidth=f[4]*s; ctx.beginPath(); ctx.moveTo(sg*f[0]*s,f[1]*s); ctx.quadraticCurveTo(sg*(f[0]*0.4+f[2]*0.6+0.012)*s,(f[1]*0.4+f[3]*0.6)*s,sg*f[2]*s,f[3]*s); ctx.stroke();
    ctx.strokeStyle=sh; ctx.lineWidth=s*0.008; ctx.beginPath(); ctx.moveTo(sg*(f[0]-f[4]*0.5)*s,(f[1]-0.0)*s); ctx.quadraticCurveTo(sg*(f[0]*0.4+f[2]*0.6+0.012-f[4]*0.45)*s,(f[1]*0.4+f[3]*0.6)*s,sg*(f[2]-f[4]*0.4)*s,(f[3]+0.02)*s); ctx.stroke(); }
  // thumbs pressed side by side at the front
  for (const sg of [-1,1]){
    ctx.beginPath(); ctx.moveTo(sg*s*0.085,-s*0.04);
    ctx.bezierCurveTo(sg*s*0.11,-s*0.2,sg*s*0.075,-s*0.36,sg*s*0.045,-s*0.42);
    ctx.quadraticCurveTo(sg*s*0.01,-s*0.45,sg*s*0.006,-s*0.38);
    ctx.lineTo(sg*s*0.006,-s*0.03); ctx.closePath();
    ctx.fillStyle=rgba(shade(col,0.1)); ctx.fill(); ctx.strokeStyle=sh; ctx.lineWidth=s*0.01; ctx.stroke();
  }
  ctx.restore();
}
function ease(a, b, u) { return smooth((u - a) / (b - a)); }

// ---------------------------------------------------------------- vignettes
module.exports = {
  // dwindling energy bars blink low over a dimming starfield
  energy_gauge: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u;
      const dim = 1 - 0.75 * ease(0.05, 0.9, u);
      night(ctx, w, h, p, Math.round(w * h / 2600), [6, 9, 21], U.mix([20, 26, 51], [10, 10, 20], u), () => dim);
      const cx = w / 2, cy = h * (w > h ? 0.52 : 0.5);
      const gw = unit * 0.66, gh = unit * 0.24, N = 8;
      const level = lerp(6.4, 0.6, easeInOut(clamp((u - 0.02) / 0.8)));
      const low = ease(0.45, 0.85, u);
      FX.glow(ctx, cx, cy, gw * 0.8, mix(GOLD, CRIMSON, low), 0.12 + 0.05 * Math.sin(p.t * 1.3));
      // frame
      const x0 = cx - gw / 2, y0 = cy - gh / 2;
      ctx.save();
      ctx.lineWidth = unit * 0.012;
      ctx.strokeStyle = rgba([170, 185, 220], 0.75);
      ctx.fillStyle = rgba([12, 16, 34], 0.85);
      rr(ctx, x0, y0, gw, gh, gh * 0.18); ctx.fill(); ctx.stroke();
      ctx.fillStyle = rgba([170, 185, 220], 0.75);
      rr(ctx, x0 + gw + unit * 0.008, cy - gh * 0.2, unit * 0.03, gh * 0.4, unit * 0.008); ctx.fill();
      ctx.restore();
      const pad = gh * 0.14, sw = (gw - pad * 2) / N;
      for (let i = 0; i < N; i++) {
        let on = clamp(level - i);
        const col = mix(GOLD, [240, 74, 96], clamp(low * 1.2 - i * 0.05));
        if (i === 0 && level < 1.8) {
          on = 0.95 * (0.68 + 0.32 * Math.sin(p.t * 2.6)); // slow, soft blink
          FX.glow(ctx, x0 + pad + sw * 0.5, cy, gh * 1.2, CRIMSON, 0.3 * on * low);
        }
        const bx = x0 + pad + i * sw + sw * 0.1, by = y0 + pad, bw = sw * 0.8, bh = gh - pad * 2;
        ctx.fillStyle = rgba([40, 46, 70], 0.6);
        rr(ctx, bx, by, bw, bh, bw * 0.15); ctx.fill();
        if (on > 0.01) {
          const g = ctx.createLinearGradient(0, by, 0, by + bh);
          g.addColorStop(0, rgba(shade(col, 0.35), on)); g.addColorStop(1, rgba(col, on * 0.85));
          ctx.fillStyle = g; rr(ctx, bx, by, bw, bh, bw * 0.15); ctx.fill();
          FX.glow(ctx, bx + bw / 2, cy, bh * 0.8, col, 0.18 * on);
        }
      }
    },
  },

  // star map with red pulses; a cyan cursor moves to the strongest
  triage_starmap: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      night(ctx, w, h, p, Math.round(w * h / 5000), [6, 9, 21], [16, 20, 44]);
      const cx = w / 2, cy = h / 2;
      // chart: concentric rings and spokes
      ctx.save(); ctx.strokeStyle = rgba([120, 150, 220], 0.16); ctx.lineWidth = 1.2;
      for (let i = 1; i <= 4; i++) { ctx.beginPath(); ctx.arc(cx, cy, unit * 0.12 * i, 0, TAU); ctx.stroke(); }
      for (let i = 0; i < 12; i++) {
        const a = i * TAU / 12;
        ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * unit * 0.06, cy + Math.sin(a) * unit * 0.06);
        ctx.lineTo(cx + Math.cos(a) * unit * 0.5, cy + Math.sin(a) * unit * 0.5); ctx.stroke();
      }
      ctx.restore();
      // points
      const rnd = U.rng((p.seed | 0) * 7 + 3);
      const N = 11, pts = [];
      const sx = w > h ? 0.42 : 0.38, sy = w > h ? 0.38 : 0.3;
      for (let i = 0; i < N; i++) {
        const a = i * TAU / N + rnd() * 0.4, r = 0.35 + rnd() * 0.65;
        pts.push({ x: cx + Math.cos(a) * r * w * sx, y: cy + Math.sin(a) * r * h * sy, I: 0.2 + rnd() * 0.45, ph: rnd() });
      }
      const s = 2 + ((p.seed | 0) % 5), a2 = (s + 4) % N, a3 = (s + 8) % N;
      pts[s].I = 1; pts[a2].I = 0.7; pts[a3].I = 0.62;
      const locked = ease(0.68, 0.8, u);
      pts.forEach((q, i) => {
        const I = q.I * (i === s ? 1 + 0.3 * locked : 1);
        const period = 2.6 - q.I * 0.8;
        for (let k = 0; k < 2; k++) {
          const f = ((t / period + q.ph + k * 0.5) % 1);
          FX.ring(ctx, q.x, q.y, unit * (0.015 + f * 0.09 * I), unit * 0.006 * (0.5 + I), CRIMSON, (1 - f) * 0.55 * I);
        }
        FX.glow(ctx, q.x, q.y, unit * 0.09 * I, CRIMSON, 0.35 * I);
        FX.light(ctx, q.x, q.y, unit * (0.004 + 0.008 * I), mix(CRIMSON, [255, 140, 150], 0.4), 0.5 + 0.5 * I);
      });
      // cursor path: start -> a3 -> a2 -> strongest
      const start = { x: cx, y: cy };
      const wp = [start, pts[a3], pts[a2], pts[s]];
      const segs = [[0.04, 0.22], [0.28, 0.44], [0.5, 0.68]];
      let px = start.x, py = start.y;
      for (let k = 0; k < 3; k++) {
        const e = easeInOut(clamp((u - segs[k][0]) / (segs[k][1] - segs[k][0])));
        if (u >= segs[k][0]) { px = lerp(wp[k].x, wp[k + 1].x, e); py = lerp(wp[k].y, wp[k + 1].y, e); }
      }
      const cr = unit * lerp(0.075, 0.05, locked) * (1 + 0.04 * Math.sin(t * 2));
      FX.glow(ctx, px, py, cr * 2.2, CYAN, 0.18 + 0.15 * locked);
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(CYAN, 0.8 + 0.2 * locked); ctx.lineWidth = unit * 0.006; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.arc(px, py, cr, 0, TAU); ctx.stroke();
      const rot = t * 0.3;
      for (let k = 0; k < 4; k++) {
        const a = rot + k * TAU / 4;
        ctx.beginPath(); ctx.arc(px, py, cr * 1.35, a - 0.35, a + 0.35); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(px + Math.cos(a) * cr * 0.55, py + Math.sin(a) * cr * 0.55);
        ctx.lineTo(px + Math.cos(a) * cr * 0.85, py + Math.sin(a) * cr * 0.85); ctx.stroke();
      }
      ctx.restore();
    },
  },

  // a cold grid where tiny human silhouettes turn into numbers
  spreadsheet_agony: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u;
      FX.bg(ctx, w, h, [10, 14, 26], [18, 24, 40]);
      const land = w > h;
      const cols = land ? 7 : 5, rows = land ? 4 : 8;
      const cell = Math.min((w * 0.88) / cols, (h * (land ? 0.8 : 0.72)) / rows);
      const gx = (w - cell * cols) / 2, gy = (h - cell * rows) / 2;
      FX.glow(ctx, w / 2, h / 2, unit * 0.7, [110, 150, 200], 0.08, false);
      // cells
      const n = cols * rows, order = [];
      for (let i = 0; i < n; i++) order.push([U.hash2(i, p.seed | 0), i]);
      order.sort((a, b) => a[0] - b[0]);
      const tau = new Array(n);
      order.forEach((o, r) => { tau[o[1]] = -0.06 + 0.82 * r / (n - 1); });
      for (let i = 0; i < n; i++) {
        const c = i % cols, r = (i / cols) | 0;
        const x = gx + c * cell, y = gy + r * cell;
        const k = ease(tau[i], tau[i] + 0.07, u);
        // cell fill gets colder when converted
        ctx.fillStyle = rgba(mix([30, 34, 50], [26, 38, 60], k), 0.6);
        ctx.fillRect(x + 1, y + 1, cell - 2, cell - 2);
        if (k < 1) {
          const breath = 1 + 0.015 * Math.sin(p.t * 1.4 + i);
          const fh = cell * 0.66 * (1 - 0.3 * k) * breath;
          FX.glow(ctx, x + cell / 2, y + cell * 0.5, cell * 0.45, AMBER, 0.14 * (1 - k));
          FX.figure(ctx, x + cell / 2, y + cell * 0.86, fh, 'stand', { color: mix([255, 205, 150], [160, 175, 200], k), alpha: 1 - k });
        }
        if (k > 0) {
          const num = String(1000 + Math.floor(U.hash2(i, 91) * 8999));
          FX.text(ctx, num, x + cell / 2, y + cell / 2, cell * 0.24, [175, 195, 225], { weight: 500, alpha: k * 0.9 });
        }
      }
      // grid lines
      ctx.save(); ctx.strokeStyle = rgba([120, 150, 195], 0.45); ctx.lineWidth = Math.max(1, unit * 0.003);
      ctx.beginPath();
      for (let c = 0; c <= cols; c++) { ctx.moveTo(gx + c * cell, gy); ctx.lineTo(gx + c * cell, gy + rows * cell); }
      for (let r = 0; r <= rows; r++) { ctx.moveTo(gx, gy + r * cell); ctx.lineTo(gx + cols * cell, gy + r * cell); }
      ctx.stroke(); ctx.restore();
    },
  },

  // loud red flares and tiny faint flickers; the faint ones fade unnoticed
  whisper_signals: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      night(ctx, w, h, p, Math.round(w * h / 7000), [7, 8, 20], [22, 16, 36]);
      const land = w > h;
      const flares = land ? [[0.24, 0.36, 1], [0.7, 0.62, 0.85], [0.52, 0.22, 0.6]] : [[0.32, 0.3, 1], [0.66, 0.58, 0.85], [0.4, 0.8, 0.7]];
      const loud = 0.85 + 0.25 * ease(0, 0.8, u);
      flares.forEach(([fx, fy, s], i) => {
        const x = fx * w, y = fy * h, R = unit * 0.13 * s * loud * (1 + 0.08 * Math.sin(t * 1.6 + i * 2));
        FX.glow(ctx, x, y, R * 3, CRIMSON, 0.45);
        FX.glow(ctx, x, y, R * 1.2, [255, 110, 110], 0.6);
        // rays
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(x, y); ctx.rotate(t * 0.12 * (i % 2 ? -1 : 1) + i);
        const g = ctx.createRadialGradient(0, 0, 0, 0, 0, R * 2.6);
        g.addColorStop(0, rgba([255, 150, 140], 0.5)); g.addColorStop(1, rgba(CRIMSON, 0));
        ctx.fillStyle = g; ctx.beginPath();
        const K = 8;
        for (let k = 0; k <= K * 2; k++) {
          const a = k * Math.PI / K, rad = k % 2 ? R * 0.35 : R * (2.0 + 0.6 * ((k / 2) % 2));
          ctx.lineTo(Math.cos(a) * rad, Math.sin(a) * rad);
        }
        ctx.fill(); ctx.restore();
        FX.light(ctx, x, y, R * 0.12, [255, 170, 160], 0.9);
      });
      // faint flickers
      const rnd = U.rng((p.seed | 0) + 404);
      for (let i = 0; i < 16; i++) {
        const x = (0.06 + rnd() * 0.88) * w, y = (0.08 + rnd() * 0.84) * h;
        const d = 0.15 + rnd() * 0.6, ph = rnd() * TAU, sp = 0.7 + rnd() * 0.6;
        let near = false;
        for (const f of flares) if (Math.hypot(x - f[0] * w, y - f[1] * h) < unit * 0.15) near = true;
        if (near) continue;
        const life = 1 - ease(d, d + 0.15, u);
        if (life <= 0) continue;
        const fl = 0.55 + 0.45 * Math.sin(t * sp * 2 + ph);
        FX.glow(ctx, x, y, unit * 0.04, [190, 190, 255], 0.4 * life * fl);
        FX.light(ctx, x, y, unit * 0.005, [215, 210, 255], 0.8 * life * fl);
      }
    },
  },

  // a compass of light inside a chest; needle trembles, then points
  compass_heart: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      night(ctx, w, h, p, Math.round(w * h / 6000), [6, 9, 21], [18, 20, 44]);
      const land = w > h;
      const cx = w / 2, cy = land ? h * 0.66 : h * 0.6, S = unit;
      const settle = ease(0.25, 0.75, u);
      const target = -0.55; // up and to the right
      // far guiding star
      const gx = cx + Math.sin(-target) * -S * 0.0 + Math.sin(target + Math.PI) * 0, sa = target;
      const dirx = Math.sin(-sa) * -1, diry = -Math.cos(sa);
      const starX = cx + Math.sin(0.55) * (land ? S * 0.62 : S * 0.75), starY = cy - Math.cos(0.55) * (land ? S * 0.62 : S * 0.75);
      void gx; void dirx; void diry;
      FX.glow(ctx, starX, starY, S * 0.12, GOLD, 0.15 + 0.35 * settle);
      FX.light(ctx, starX, starY, S * 0.007, GOLD, 0.35 + 0.6 * settle);
      // bust silhouette
      const col = [24, 27, 48];
      ctx.save();
      ctx.fillStyle = rgba(col);
      const headY = cy - S * 0.47, headR = S * 0.095;
      const shY = cy - S * 0.27;
      ctx.beginPath();
      ctx.moveTo(cx - S * 0.045, headY + headR * 0.5);
      ctx.quadraticCurveTo(cx - S * 0.05, shY - S * 0.06, cx - S * 0.08, shY - S * 0.045);
      ctx.bezierCurveTo(cx - S * 0.16, shY - S * 0.02, cx - S * 0.27, shY - S * 0.01, cx - S * 0.31, shY + S * 0.03);
      ctx.bezierCurveTo(cx - S * 0.36, shY + S * 0.06, cx - S * 0.37, shY + S * 0.14, cx - S * 0.37, shY + S * 0.24);
      ctx.lineTo(cx - S * 0.38, h + 2); ctx.lineTo(cx + S * 0.38, h + 2);
      ctx.lineTo(cx + S * 0.37, shY + S * 0.24);
      ctx.bezierCurveTo(cx + S * 0.37, shY + S * 0.14, cx + S * 0.36, shY + S * 0.06, cx + S * 0.31, shY + S * 0.03);
      ctx.bezierCurveTo(cx + S * 0.27, shY - S * 0.01, cx + S * 0.16, shY - S * 0.02, cx + S * 0.08, shY - S * 0.045);
      ctx.quadraticCurveTo(cx + S * 0.05, shY - S * 0.06, cx + S * 0.045, headY + headR * 0.5);
      ctx.closePath(); ctx.fill();
      ctx.strokeStyle = rgba([130, 120, 200], 0.35); ctx.lineWidth = S * 0.006; ctx.stroke();
      ctx.beginPath(); ctx.ellipse(cx, headY, headR * 0.86, headR, 0, 0, TAU); ctx.fill();
      // rim light (violet) on the outline
      ctx.strokeStyle = rgba([130, 120, 200], 0.35); ctx.lineWidth = S * 0.006; ctx.stroke();
      ctx.beginPath(); ctx.ellipse(cx, headY, headR * 0.86, headR, 0, -2.6, -0.4); ctx.stroke();
      ctx.restore();
      // compass in the chest
      const R = S * 0.13;
      FX.glow(ctx, cx, cy, R * 3, AMBER, 0.28 + 0.06 * Math.sin(t * 1.2));
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(GOLD, 0.85); ctx.lineWidth = S * 0.008;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.stroke();
      ctx.strokeStyle = rgba(GOLD, 0.35); ctx.lineWidth = S * 0.003;
      ctx.beginPath(); ctx.arc(cx, cy, R * 0.82, 0, TAU); ctx.stroke();
      for (let k = 0; k < 16; k++) {
        const a = k * TAU / 16, l = k % 4 === 0 ? 0.16 : 0.07;
        ctx.lineWidth = S * (k % 4 === 0 ? 0.006 : 0.003);
        ctx.strokeStyle = rgba(GOLD, k % 4 === 0 ? 0.8 : 0.5);
        ctx.beginPath(); ctx.moveTo(cx + Math.sin(a) * R * 0.98, cy - Math.cos(a) * R * 0.98);
        ctx.lineTo(cx + Math.sin(a) * R * (0.98 - l), cy - Math.cos(a) * R * (0.98 - l)); ctx.stroke();
      }
      ctx.restore();
      // needle
      const wander = (1 - settle) * (U.noise1(t * 0.9, 5) * 1.6 + 0.6);
      const tremble = (1 - settle * 0.85) * Math.sin(t * 7.0) * 0.05 + 0.012 * Math.sin(t * 1.7);
      const ang = 0.55 + wander + tremble; // clockwise from up
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(ang);
      ctx.globalCompositeOperation = 'lighter';
      const nl = R * 0.78, nw = R * 0.13;
      ctx.fillStyle = rgba([255, 236, 190], 0.95);
      ctx.beginPath(); ctx.moveTo(0, -nl); ctx.lineTo(nw, 0); ctx.lineTo(-nw, 0); ctx.closePath(); ctx.fill();
      ctx.fillStyle = rgba(DARKRED, 0.9);
      ctx.beginPath(); ctx.moveTo(0, nl * 0.75); ctx.lineTo(nw, 0); ctx.lineTo(-nw, 0); ctx.closePath(); ctx.fill();
      ctx.restore();
      FX.glow(ctx, cx + Math.sin(ang) * nl * 0.7, cy - Math.cos(ang) * nl * 0.7, R * 0.5, GOLD, 0.3);
      FX.light(ctx, cx, cy, R * 0.07, GOLD, 0.9);
    },
  },

  // cupped hands pour the last drops of light onto dim points of a map; each lights up
  pour_reserves: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 8000), [6, 9, 21], [14, 18, 38]);
      // map plane
      const hy = land ? h * 0.5 : h * 0.55;
      const g = ctx.createLinearGradient(0, hy, 0, h);
      g.addColorStop(0, rgba([20, 26, 50])); g.addColorStop(1, rgba([12, 15, 30]));
      ctx.fillStyle = g; ctx.fillRect(0, hy, w, h - hy);
      ctx.save(); ctx.strokeStyle = rgba([110, 130, 200], 0.16); ctx.lineWidth = 1;
      ctx.beginPath();
      for (let k = 1; k < 9; k++) { const y = hy + (h - hy) * Math.pow(k / 9, 1.7); ctx.moveTo(0, y); ctx.lineTo(w, y); }
      for (let k = -10; k <= 10; k++) { ctx.moveTo(w / 2 + k * unit * 0.04, hy); ctx.lineTo(w / 2 + k * unit * 0.4, h); }
      ctx.stroke(); ctx.restore();
      // points along a route
      const N = 6, pts = [];
      for (let i = 0; i < N; i++) {
        const f = i / (N - 1);
        const x = w * lerp(land ? 0.3 : 0.36, 0.9, f);
        const y = hy + (h - hy) * (0.3 + 0.42 * (0.5 + 0.5 * Math.sin(f * 5.2 + 0.6)));
        pts.push([x, y]);
      }
      // route lines (faint map roads)
      ctx.save(); ctx.strokeStyle = rgba([140, 150, 200], 0.2); ctx.lineWidth = unit * 0.004; ctx.setLineDash([unit * 0.012, unit * 0.012]);
      ctx.beginPath(); pts.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.stroke(); ctx.restore();
      // hand schedule: hover over point i during [s_i, s_i + hold]
      const span = 0.8 / N, hold = span * 0.55;
      const sch = (i) => 0.02 + i * span;
      let hx = pts[0][0];
      for (let i = 0; i < N - 1; i++) {
        const m0 = sch(i) + hold, m1 = sch(i + 1);
        if (u >= m0) hx = lerp(pts[i][0], pts[i + 1][0], easeInOut((u - m0) / (m1 - m0)));
      }
      const handY = land ? h * 0.24 : h * 0.33;
      const hs = unit * 0.16;
      const tilt = 0.5 + 0.03 * Math.sin(t * 0.8);
      const lx0 = hs * 0.78, ly0 = -hs * 0.28;
      const lipDX = lx0 * Math.cos(tilt) - ly0 * Math.sin(tilt), lipDY = lx0 * Math.sin(tilt) + ly0 * Math.cos(tilt);
      const lipX = hx, lipY = handY + lipDY + hs * 0.03;
      const gxo = hx - lipDX;
      const fallU = 0.035;
      const lit = (i) => ease(sch(i) + fallU, sch(i) + fallU + 0.05, u);
      const rem = 1 - ease(0, 0.9, u) * 0.7;
      // drops
      for (let i = 0; i < N; i++) {
        const [px, py] = pts[i];
        for (let k = 0; k < 4; k++) {
          const ue = sch(i) + k * hold / 4;
          const a = (u - ue) / fallU;
          if (a < 0 || a > 1) continue;
          const y = lerp(lipY, py, a * a);
          FX.light(ctx, px, y, unit * 0.007, GOLD, 0.9 * (1 - a * 0.3));
        }
      }
      // the stream of light between the lip and the point being filled
      for (let i = 0; i < N; i++) {
        const [px, py] = pts[i];
        const a1 = clamp((u - sch(i)) / fallU), a0 = clamp((u - sch(i) - hold) / fallU);
        if (a1 <= a0) continue;
        const y1 = lerp(lipY, py, a1 * a1), y0 = lerp(lipY, py, a0 * a0);
        const sg = ctx.createLinearGradient(0, y0, 0, y1);
        sg.addColorStop(0, rgba(GOLD, 0.85)); sg.addColorStop(1, rgba(GOLD, 0.35));
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
        ctx.strokeStyle = rgba(GOLD, 0.12); ctx.lineWidth = unit * 0.025;
        ctx.beginPath(); ctx.moveTo(px, y0); ctx.lineTo(px, y1); ctx.stroke();
        ctx.strokeStyle = sg; ctx.lineWidth = unit * 0.006;
        ctx.beginPath(); ctx.moveTo(px, y0); ctx.lineTo(px, y1); ctx.stroke();
        ctx.restore();
      }
      // a thin trickle at the lip while pouring
      let pouring = 0;
      for (let i = 0; i < N; i++) pouring = Math.max(pouring, U.pulse(u, sch(i) - 0.01, sch(i) + hold + 0.01, 0.03));
      FX.glow(ctx, lipX, lipY, unit * 0.03, GOLD, 0.5 * pouring);
      // map points
      pts.forEach(([x, y], i) => {
        const L = lit(i);
        FX.glow(ctx, x, y, unit * (0.05 + 0.08 * L), AMBER, 0.08 + 0.4 * L * (0.9 + 0.1 * Math.sin(t * 1.5 + i)));
        ctx.fillStyle = rgba(mix([90, 100, 140], [255, 225, 170], L), 0.9);
        ctx.beginPath(); ctx.ellipse(x, y, unit * 0.012, unit * 0.006, 0, 0, TAU); ctx.fill();
        if (L > 0) FX.ring(ctx, x, y, unit * (0.02 + 0.04 * L), unit * 0.003, GOLD, 0.5 * (1 - L) + 0.05);
      });
      // cupped hands of light, tilted so the light spills over the fingertips
      ctx.save(); ctx.translate(gxo, handY); ctx.rotate(tilt);
      const hc = [255, 205, 140];
      FX.glow(ctx, 0, 0, hs * 1.2, GOLD, 0.25 * rem);
      lightHand(ctx, -hs * 0.3, hs * 0.6, -0.5, hs, 'cup', hc, { mirror: true, arm: 1.2, armAng: -0.2 - tilt });
      lightHand(ctx, hs * 0.3, hs * 0.6, 0.5, hs, 'cup', hc, { arm: 1.2, armAng: 0.25 - tilt });
      // pool of light held in the palms, shrinking as it is poured out
      FX.glow(ctx, hs * 0.05, hs * 0.05, hs * 0.55 * (0.5 + 0.5 * rem), [255, 245, 210], 0.75 * rem);
      FX.light(ctx, hs * 0.05, hs * 0.08, hs * 0.08 * (0.4 + 0.6 * rem), [255, 230, 170], 0.8);
      ctx.restore();
    },
  },

  // final embers flicker and drift in black
  embers_void: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      FX.bg(ctx, w, h, [4, 4, 8], [12, 8, 12]);
      FX.glow(ctx, w / 2, h, unit * 0.8, [120, 40, 30], 0.18 * (1 - 0.6 * u), false);
      const rnd = U.rng((p.seed | 0) + 77);
      const N = 46;
      for (let i = 0; i < N; i++) {
        const x0 = rnd() * w, y0 = rnd() * h, sp = unit * (0.015 + rnd() * 0.03), ph = rnd() * 50;
        const d = i < 4 ? 2 : 0.05 + rnd() * 0.85, sz = 0.6 + rnd() * 0.8;
        const y = ((y0 - t * sp) % h + h) % h;
        const x = x0 + Math.sin(t * 0.35 + ph) * unit * 0.03;
        const edge = smooth(y / (h * 0.15)) * smooth((h - y) / (h * 0.15));
        const life = 1 - ease(d - 0.08, d + 0.08, u);
        if (life <= 0) continue;
        const fl = 0.55 + 0.45 * U.noise1(t * 1.1 + ph, i);
        const cool = clamp(0.2 + 0.8 * (1 - life) + u * 0.3);
        const col = mix([255, 176, 90], CRIMSON, cool);
        const a = edge * life * fl * (i < 4 ? 1 - 0.4 * u : 1);
        FX.glow(ctx, x, y, unit * 0.03 * sz, col, 0.4 * a);
        FX.light(ctx, x, y, unit * 0.004 * sz, col, 0.8 * a);
      }
    },
  },

  // stars wink out one by one, their halos bowing like tired heads
  stars_bow_out: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      night(ctx, w, h, p, Math.round(w * h / 9000), [5, 7, 18], [14, 16, 34], () => 1 - 0.5 * u);
      const land = w > h, N = 7;
      const rnd = U.rng((p.seed | 0) + 9);
      const order = [3, 0, 5, 1, 6, 2, 4];
      for (let i = 0; i < N; i++) {
        const f = i / (N - 1);
        const x = land ? w * lerp(0.1, 0.9, f) : w * (0.22 + 0.56 * ((i * 3) % N) / (N - 1));
        const y = land ? h * (0.4 + 0.12 * Math.sin(f * Math.PI * 1.6 + 0.4)) : h * lerp(0.2, 0.72, f);
        const r = unit * (0.014 + rnd() * 0.008);
        const o = order.indexOf(i);
        const d = 0.06 + o * 0.11;
        const k = ease(d, d + 0.12, u);   // bow progress
        const out = ease(d + 0.06, d + 0.16, u); // fade
        if (out >= 1) { FX.glow(ctx, x, y + unit * 0.05, unit * 0.04, [120, 120, 160], 0.05); continue; }
        // pivot below (like a neck): the star nods forward and down
        const L = unit * 0.07, b = k * 1.15;
        const sx = x + Math.sin(b) * L, sy = y + L - Math.cos(b) * L;
        const a = (1 - out) * (0.9 + 0.1 * Math.sin(t * 0.7 + i));
        const col = mix([230, 235, 255], [255, 210, 150], 0.3 + 0.4 * k);
        FX.glow(ctx, sx, sy, r * 7, col, 0.35 * a);
        // halo ring, tilting forward like a bowed head
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        ctx.translate(sx, sy); ctx.rotate(b);
        ctx.strokeStyle = rgba(col, 0.3 * a); ctx.lineWidth = unit * 0.005;
        ctx.beginPath(); ctx.ellipse(0, r * 0.4 * k, r * 2.8, r * lerp(2.8, 1.3, k), 0, 0, TAU); ctx.stroke();
        ctx.strokeStyle = rgba(col, 0.12 * a); ctx.lineWidth = unit * 0.014;
        ctx.beginPath(); ctx.ellipse(0, r * 0.4 * k, r * 2.8, r * lerp(2.8, 1.3, k), 0, 0, TAU); ctx.stroke();
        ctx.restore();
        FX.light(ctx, sx, sy, r * 0.75, col, a);
      }
    },
  },

  // a soft monitor heartbeat line slows and flattens
  heartbeat_slow: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t, dur = p.dur || 8;
      FX.bg(ctx, w, h, [6, 9, 18], [14, 16, 30]);
      const cy = h * 0.5, amp = unit * 0.2;
      // faint monitor grid
      ctx.save(); ctx.strokeStyle = rgba([90, 120, 160], 0.1); ctx.lineWidth = 1; ctx.beginPath();
      const gs = unit * 0.08;
      for (let x = (w / 2) % gs; x < w; x += gs) { ctx.moveTo(x, 0); ctx.lineTo(x, h); }
      for (let y = cy % gs; y < h; y += gs) { ctx.moveTo(0, y); ctx.lineTo(w, y); }
      ctx.stroke(); ctx.restore();
      const r0 = 1.15, UE = 0.85;
      const rate = (T) => { const s = T / dur; if (s < 0) return r0; if (s >= UE) return 0; return r0 * Math.pow(1 - s / UE, 1.5); };
      const phase = (T) => {
        if (T < 0) return r0 * T;
        const s = Math.min(T / dur, UE);
        return dur * r0 * UE / 2.5 * (1 - Math.pow(1 - s / UE, 2.5));
      };
      const gauss = (d, c, wd) => Math.exp(-((d - c) / wd) * ((d - c) / wd));
      const shape = (d) => 0.1 * gauss(d, 0.05, 0.03) - 0.14 * gauss(d, 0.135, 0.012) + 1 * gauss(d, 0.17, 0.016) - 0.32 * gauss(d, 0.205, 0.015) + 0.22 * gauss(d, 0.38, 0.05);
      const val = (T) => {
        const P = phase(T), fr = P - Math.floor(P), r = rate(T);
        // time since the last beat
        let d = r > 0.02 ? fr / r : 99;
        const s = clamp(T / dur);
        const A = lerp(1, 0.35, clamp(s / UE));
        // if the beat was before the slowdown flattened, use the beat's own time
        if (r <= 0.02) {
          return 0;
        }
        return A * shape(d);
      };
      const headX = w * 0.82, speed = unit * 0.32;
      const pts = [];
      for (let x = 0; x <= headX; x += 1.5) {
        const T = t - (headX - x) / speed;
        pts.push([x, cy - val(T) * amp]);
      }
      const col = [255, 135, 150];
      const grad = ctx.createLinearGradient(0, 0, headX, 0);
      grad.addColorStop(0, rgba(col, 0)); grad.addColorStop(0.5, rgba(col, 0.55)); grad.addColorStop(1, rgba(col, 1));
      ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      const gradW = ctx.createLinearGradient(0, 0, headX, 0);
      gradW.addColorStop(0, rgba(col, 0)); gradW.addColorStop(1, rgba(col, 0.18));
      ctx.strokeStyle = gradW; ctx.lineWidth = unit * 0.03;
      ctx.beginPath(); pts.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.stroke();
      ctx.strokeStyle = grad; ctx.lineWidth = unit * 0.008;
      ctx.stroke(); ctx.restore();
      const last = pts[pts.length - 1];
      const flat = ease(0.8, 0.95, u);
      FX.glow(ctx, last[0], last[1], unit * 0.08, col, 0.5 - 0.2 * flat);
      FX.light(ctx, last[0], last[1], unit * 0.008, col, 1 - 0.3 * flat);
    },
  },

  // hands of light cradle a sphere full of tiny memories (faces, hands, homes)
  hold_sum: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      night(ctx, w, h, p, Math.round(w * h / 7000), [6, 9, 21], [20, 22, 48]);
      const land = w > h;
      const cx = w / 2, cy = land ? h * 0.42 : h * 0.47, R = unit * (land ? 0.22 : 0.24);
      const fill = ease(0.0, 0.75, u);
      FX.glow(ctx, cx, cy, R * 2.8, AMBER, 0.2 + 0.15 * fill);
      // hands under the sphere
      const hs = R * 1.15, hc = [255, 208, 145];
      lightHand(ctx, cx - R * 0.42, cy + R * 1.25, -0.62, hs, 'cup', hc, { mirror: true, arm: 1.6, armAng: -0.25 });
      lightHand(ctx, cx + R * 0.42, cy + R * 1.25, 0.62, hs, 'cup', hc, { arm: 1.6, armAng: 0.25 });
      // sphere
      ctx.save();
      const sg = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.35, R * 0.1, cx, cy, R);
      sg.addColorStop(0, rgba([100, 74, 58])); sg.addColorStop(0.7, rgba([52, 38, 50])); sg.addColorStop(1, rgba([76, 54, 52]));
      ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.fill();
      ctx.clip();
      FX.glow(ctx, cx, cy, R * 1.2, AMBER, 0.25 + 0.3 * fill);
      // memories
      const rnd = U.rng((p.seed | 0) + 5);
      const M = 9;
      for (let i = 0; i < M; i++) {
        const orb = rnd() * TAU, rad = R * (0.15 + rnd() * 0.6), sp = (0.08 + rnd() * 0.08) * (rnd() < 0.5 ? -1 : 1);
        const a = orb + t * sp;
        const x = cx + Math.cos(a) * rad, y = cy + Math.sin(a) * rad * 0.8;
        const app = ease(i / M * 0.6 - 0.1, i / M * 0.6 + 0.1, u);
        if (app <= 0) continue;
        const kind = i % 3, s = R * 0.19;
        const col = mix([255, 225, 170], [255, 190, 120], rnd());
        FX.glow(ctx, x, y, s * 2.2, col, 0.25 * app);
        ctx.save(); ctx.globalAlpha = 0.9 * app; ctx.fillStyle = rgba(col); ctx.translate(x, y);
        if (kind === 0) { // face in profile: head + shoulders
          ctx.beginPath(); ctx.arc(0, -s * 0.35, s * 0.42, 0, TAU); ctx.fill();
          ctx.beginPath(); ctx.moveTo(s * 0.42, -s * 0.4); ctx.lineTo(s * 0.58, -s * 0.28); ctx.lineTo(s * 0.4, -s * 0.2); ctx.fill();
          ctx.beginPath(); ctx.ellipse(0, s * 0.55, s * 0.6, s * 0.38, 0, Math.PI, 0); ctx.fill();
        } else if (kind === 1) { // home
          ctx.beginPath(); ctx.moveTo(-s * 0.6, 0); ctx.lineTo(0, -s * 0.6); ctx.lineTo(s * 0.6, 0); ctx.closePath(); ctx.fill();
          ctx.fillRect(-s * 0.45, 0, s * 0.9, s * 0.6);
          ctx.fillStyle = rgba([120, 70, 40], 0.8); ctx.fillRect(-s * 0.1, s * 0.2, s * 0.2, s * 0.4);
        } else { // small hand
          ctx.restore();
          ctx.save(); ctx.globalAlpha = 0.95 * app;
          FX.hand(ctx, x, y + s * 0.6, Math.sin(t * 0.5 + i) * 0.2, s * 1.5, 'open', { skin: col, shadow: shade(col, -0.25), outline: shade(col, -0.1) });
        }
        ctx.restore();
      }
      ctx.restore();
      // glass rim + highlight
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.strokeStyle = rgba(GOLD, 0.55); ctx.lineWidth = unit * 0.006;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.stroke();
      ctx.strokeStyle = rgba([255, 245, 220], 0.35); ctx.lineWidth = unit * 0.01;
      ctx.beginPath(); ctx.arc(cx, cy, R * 0.85, -2.6, -1.9); ctx.stroke();
      ctx.restore();
      FX.motes(ctx, w, h, t, (p.seed | 0) + 2, 14, GOLD, { alpha: 0.5 });
    },
  },

  // a spacetime grid; points of light woven in as glowing knots
  encode_fabric: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 7000), [6, 8, 20], [18, 18, 42]);
      const hy = land ? h * 0.3 : h * 0.4, f = unit * 0.9, cx = w / 2;
      const proj = (x, y, z) => [cx + f * x / z, hy - f * y / z];
      const K = 7, knots = [];
      const rnd = U.rng((p.seed | 0) + 31);
      for (let i = 0; i < K; i++) {
        const gz = 1.8 + Math.round(rnd() * 6) * 0.5;
        const xr = Math.min(2.5, (w * 0.42 / f) * gz);
        const gx = Math.round((rnd() - 0.5) * 2 * xr * 2) / 2;
        const arr = 0.06 + i * 0.11;
        knots.push({ x: gx, z: gz, arr, k: ease(arr - 0.1, arr, u) });
      }
      const dip = (x, z) => {
        let d = 0;
        for (const k of knots) { if (k.k <= 0) continue; const r2 = (x - k.x) ** 2 + (z - k.z) ** 2; d += 0.22 * k.k * Math.exp(-r2 / 0.18); }
        return d;
      };
      const Y = (x, z) => -1 - dip(x, z) + 0.03 * Math.sin(x * 1.3 + t * 0.4) * Math.sin(z * 0.9);
      ctx.save(); ctx.lineWidth = Math.max(1, unit * 0.0025); ctx.strokeStyle = rgba([130, 140, 230], 0.38);
      ctx.beginPath();
      for (let z = land ? 1.2 : 0.7; z <= 7.01; z += 0.5) {
        for (let s = 0; s <= 40; s++) { const x = -4 + s * 0.2; const q = proj(x, Y(x, z), z); s ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }
      }
      for (let x = -4; x <= 4.01; x += 0.5) {
        for (let s = 0; s <= 32; s++) { const z = (land ? 1.2 : 0.7) + s * 0.2; const q = proj(x, Y(x, z), z); s ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }
      }
      ctx.stroke(); ctx.restore();
      // fade grid into the distance
      const fg = ctx.createLinearGradient(0, hy - 2, 0, hy + unit * 0.2);
      fg.addColorStop(0, rgba([10, 12, 30], 1)); fg.addColorStop(1, rgba([10, 12, 30], 0));
      ctx.fillStyle = fg; ctx.fillRect(0, hy - unit * 0.05, w, unit * 0.25 + 2);
      // knots
      knots.forEach((k, i) => {
        const fall = ease(k.arr - 0.12, k.arr, u);
        if (u < k.arr - 0.14) return;
        const yy = lerp(1.6, Y(k.x, k.z), easeInOut(fall));
        const [x, y] = proj(k.x, yy, k.z);
        const sc = 1.6 / k.z;
        const settled = ease(k.arr, k.arr + 0.06, u);
        FX.glow(ctx, x, y, unit * 0.09 * sc, GOLD, 0.25 + 0.25 * settled);
        if (settled > 0) {
          ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba(GOLD, 0.7 * settled); ctx.lineWidth = unit * 0.005 * sc;
          const r = unit * 0.03 * sc, rot = t * 0.3 + i;
          ctx.beginPath(); ctx.ellipse(x, y, r * 1.4, r * 0.55, rot * 0.2, 0, TAU); ctx.stroke();
          ctx.beginPath(); ctx.ellipse(x, y, r * 0.55, r * 1.1, rot * 0.2, 0, TAU); ctx.stroke();
          ctx.restore();
        }
        if (fall < 1) FX.glow(ctx, x, y - unit * 0.06 * sc, unit * 0.03 * sc, GOLD, 0.25 * (1 - fall));
        FX.light(ctx, x, y, unit * 0.008 * sc, GOLD, 0.95);
      });
    },
  },

  // a light DNA helix dissolves into bubbling quantum foam, then a cosmic birth spark
  dna_quantum_foam: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 9000), [5, 7, 18], [16, 14, 38]);
      const cx = w / 2, cy = h / 2;
      const L = land ? w * 0.8 : h * 0.62, A = unit * 0.12;
      const ax = land ? [1, 0] : [0, 1], nx = [-ax[1], ax[0]];
      const P = (s, off) => [cx + ax[0] * s + nx[0] * off, cy + ax[1] * s + nx[1] * off];
      const spark = ease(0.62, 0.8, u);
      const N = 30;
      // helix
      for (let pass = 0; pass < 2; pass++) for (let i = 0; i < N; i++) {
        const sN = i / (N - 1) - 0.5, s = sN * L;
        const dz = 0.2 + 0.4 * (1 - Math.abs(sN) * 2); // dissolve time (ends first)
        const dk = ease(dz, dz + 0.12, u);
        if (dk >= 1) continue;
        const ph = sN * 9 + t * 0.7;
        const z1 = Math.cos(ph), z2 = -z1;
        const o1 = Math.sin(ph) * A, o2 = -o1;
        const a = 1 - dk;
        if (pass === 0) {
          if (i % 2 === 0) {
            const q1 = P(s, o1), q2 = P(s, o2);
            ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba(CYAN, 0.25 * a); ctx.lineWidth = unit * 0.005;
            ctx.beginPath(); ctx.moveTo(q1[0], q1[1]); ctx.lineTo(q2[0], q2[1]); ctx.stroke(); ctx.restore();
          }
          // back strand
          const [o, z] = z1 < 0 ? [o1, z1] : [o2, z2];
          const q = P(s, o);
          FX.light(ctx, q[0], q[1], unit * 0.007 * (0.8 + 0.2 * z), GOLD, 0.45 * a);
        } else {
          const [o, z] = z1 >= 0 ? [o1, z1] : [o2, z2];
          const q = P(s, o);
          FX.light(ctx, q[0], q[1], unit * 0.009 * (0.8 + 0.2 * z), GOLD, 0.95 * a);
        }
      }
      // foam: bubbles that grow and pop, drifting toward centre then collapsing into the spark
      const foam = ease(0.18, 0.45, u) * (1 - 0.85 * spark);
      if (foam > 0) {
        const rnd = U.rng((p.seed | 0) + 123);
        for (let i = 0; i < 60; i++) {
          const sN = rnd() - 0.5, off = (rnd() - 0.5) * 2.4 * A, per = 1.6 + rnd() * 1.8, ph0 = rnd();
          const dz = 0.2 + 0.4 * (1 - Math.abs(sN) * 2);
          const on = ease(dz, dz + 0.1, u);
          if (on <= 0) continue;
          const pull = 1 - 0.7 * ease(0.45, 0.75, u);
          const q = P(sN * L * pull, off * pull);
          const fr = (t / per + ph0) % 1;
          const r = unit * (0.008 + 0.035 * rnd()) * (0.3 + fr);
          const a = Math.sin(Math.PI * fr) * on * foam;
          FX.ring(ctx, q[0], q[1], r, Math.max(1, unit * 0.003), [170, 160, 255], 0.5 * a);
          FX.glow(ctx, q[0], q[1], r * 1.6, [140, 150, 255], 0.12 * a);
        }
      }
      // birth spark
      if (spark > 0) {
        const br = 0.9 + 0.1 * Math.sin(t * 1.3);
        FX.glow(ctx, cx, cy, unit * 0.5 * spark, [255, 220, 170], 0.55 * spark * br);
        FX.glow(ctx, cx, cy, unit * 0.12 * spark, [255, 250, 235], 0.9 * spark);
        const rr2 = ease(0.68, 1.0, u);
        FX.ring(ctx, cx, cy, unit * (0.06 + 0.32 * rr2), unit * 0.006, GOLD, 0.5 * (1 - rr2) * spark);
        ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(cx, cy); ctx.rotate(t * 0.05);
        const g = ctx.createRadialGradient(0, 0, 0, 0, 0, unit * 0.32 * spark);
        g.addColorStop(0, rgba([255, 240, 210], 0.6 * spark)); g.addColorStop(1, rgba(GOLD, 0));
        ctx.fillStyle = g; ctx.beginPath();
        for (let k = 0; k <= 16; k++) { const a = k * Math.PI / 8, rad = k % 2 ? unit * 0.03 : unit * 0.32 * spark; ctx.lineTo(Math.cos(a) * rad, Math.sin(a) * rad); }
        ctx.fill(); ctx.restore();
        FX.light(ctx, cx, cy, unit * 0.012 * spark, [255, 250, 235], 1);
      }
    },
  },

  // sound rings travel from a small source into darkness; far away something faintly glows
  voice_into_void: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 12000), [4, 5, 14], [12, 12, 28], (i, x, y) => 0.5);
      // small source: a figure on a sliver of ground
      const fx = land ? w * 0.16 : w * 0.5, gy = land ? h * 0.8 : h * 0.86;
      const gg = ctx.createRadialGradient(fx, gy, 0, fx, gy, unit * 0.3);
      gg.addColorStop(0, rgba([40, 40, 60], 0.9)); gg.addColorStop(1, rgba([40, 40, 60], 0));
      ctx.fillStyle = gg; ctx.beginPath(); ctx.ellipse(fx, gy + unit * 0.01, unit * 0.3, unit * 0.04, 0, 0, TAU); ctx.fill();
      const fh = unit * 0.27;
      FX.glow(ctx, fx, gy - fh * 0.5, fh * 0.9, AMBER, 0.12);
      const fig = FX.figure(ctx, fx, gy, fh, 'stand', { color: [44, 42, 62], facing: 1, rim: [255, 200, 140] });
      const [sx, sy] = [fig.head[0] + (land ? fh * 0.06 : 0), fig.head[1] - (land ? 0 : fh * 0.05)];
      // target
      const tx = land ? w * 0.88 : w * 0.5, ty = land ? h * 0.32 : h * 0.12;
      const dir = Math.atan2(ty - sy, tx - sx), dist = Math.hypot(tx - sx, ty - sy);
      const reach = ease(0.0, 0.85, u);
      FX.glow(ctx, tx, ty, unit * 0.16, CYAN, 0.05 + 0.18 * reach * (0.85 + 0.15 * Math.sin(t * 0.9)));
      FX.light(ctx, tx, ty, unit * 0.005, [200, 240, 255], 0.15 + 0.45 * reach);
      FX.glow(ctx, sx, sy, unit * 0.06, GOLD, 0.35);
      // rings
      const per = 1.4, speed = dist / 4.2;
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
      for (let k = 0; k < 4; k++) {
        const age = ((t / per) % 1 + k) * per;
        const r = unit * 0.03 + age * speed;
        if (r > dist * 1.02) continue;
        const a = (1 - r / dist) * 0.7 * smooth(age / 0.4);
        const spread = 0.5 + 0.15 * (r / dist);
        ctx.strokeStyle = rgba(AMBER, a * 0.18); ctx.lineWidth = unit * 0.03;
        ctx.beginPath(); ctx.arc(sx, sy, r, dir - spread, dir + spread); ctx.stroke();
        ctx.strokeStyle = rgba(GOLD, a); ctx.lineWidth = unit * (0.01 - 0.005 * r / dist);
        ctx.beginPath(); ctx.arc(sx, sy, r, dir - spread, dir + spread); ctx.stroke();
      }
      ctx.restore();
    },
  },

  // hands of light pressed together become a ripple travelling outward through time
  prayer_ripple: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 7000), [6, 8, 20], [20, 18, 44]);
      const cx = w / 2, cy = land ? h * 0.56 : h * 0.55;
      const hs = unit * (land ? 0.34 : 0.42);
      const hc = [255, 210, 150];
      const rip = ease(0.1, 0.85, u);
      // ripples (behind hands)
      const per = 2.2, maxR = Math.hypot(w, h) * 0.6;
      for (let k = 0; k < 5; k++) {
        const fr = ((t / per) % 1 + k) / 5;
        const r = unit * 0.12 + fr * maxR;
        const a = (1 - fr) * 0.55 * (0.25 + 0.75 * rip);
        FX.ring(ctx, cx, cy - hs * 0.5, r, unit * 0.006, GOLD, a);
        FX.ring(ctx, cx, cy - hs * 0.5, r * 0.97, unit * 0.02, AMBER, a * 0.12);
      }
      FX.glow(ctx, cx, cy - hs * 0.5, unit * 0.45, AMBER, 0.25 + 0.1 * Math.sin(t * 1.1));
      // pressed hands: two flat hands palm to palm, seen from the side as a single pointed shape
      FX.glow(ctx, cx, cy - hs * 0.5, hs * 0.8, GOLD, 0.3);
      prayerHands(ctx, cx, cy + hs * 0.12, hs * 1.15, hc);
      FX.motes(ctx, w, h, t, (p.seed | 0) + 8, 16, GOLD, { alpha: 0.35 * rip });
    },
  },

  // a tiny light hidden in the dark is uncovered by a hand and glows
  found_again: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 14000), [4, 5, 12], [12, 12, 24], () => 0.6);
      const cx = w / 2, gy = land ? h * 0.7 : h * 0.62;
      const lift = easeInOut(clamp((u - 0.12) / 0.45)), glowK = ease(0.3, 0.85, u);
      // dark ground
      const gg = ctx.createLinearGradient(0, gy - unit * 0.05, 0, h);
      gg.addColorStop(0, rgba([20, 20, 32])); gg.addColorStop(1, rgba([10, 10, 18]));
      ctx.fillStyle = gg; ctx.beginPath(); ctx.ellipse(cx, gy + unit * 0.5, w * 0.9, unit * 0.55, 0, Math.PI, TAU); ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.fill();
      // the light (always there, hidden at first)
      const br = 0.9 + 0.1 * Math.sin(t * 1.2);
      const lx = cx, ly = gy - unit * 0.012;
      FX.glow(ctx, lx, ly, unit * (0.12 + 0.38 * glowK), AMBER, (0.2 + 0.5 * glowK) * br);
      FX.light(ctx, lx, ly, unit * (0.01 + 0.006 * glowK), [255, 225, 160], 0.6 + 0.4 * glowK);
      // the dark stone that covered it, lifted away by the hand
      const R = unit * 0.15;
      const sx = lerp(cx, cx + unit * 0.3, lift), sy = lerp(gy - R * 0.55, gy - unit * 0.3, lift) - Math.sin(lift * Math.PI) * unit * 0.05;
      const rot = lift * 0.35;
      ctx.save(); ctx.translate(sx, sy); ctx.rotate(rot);
      const sg = ctx.createRadialGradient(-R * 0.3, -R * 0.4, R * 0.1, 0, 0, R * 1.1);
      sg.addColorStop(0, rgba([62, 60, 78])); sg.addColorStop(1, rgba([26, 25, 36]));
      ctx.fillStyle = sg; ctx.beginPath();
      const pts = 28;
      for (let i = 0; i <= pts; i++) {
        const a = i / pts * TAU, k = 1 + 0.08 * Math.sin(a * 3 + 1) + 0.05 * Math.cos(a * 5);
        const x = Math.cos(a) * R * k, y = Math.sin(a) * R * 0.72 * k;
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      }
      ctx.closePath(); ctx.fill();
      // warm light catching the underside
      ctx.strokeStyle = rgba(AMBER, 0.25 + 0.35 * (1 - lift) * 0.6 + 0.2 * glowK); ctx.lineWidth = unit * 0.006;
      ctx.beginPath(); ctx.ellipse(0, 0, R * 0.98, R * 0.7, 0, 0.25, Math.PI - 0.25); ctx.stroke();
      ctx.restore();
      // light leaking out from under the stone's edge
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const lg = ctx.createRadialGradient(lx, ly, 0, lx, ly, R * 1.6);
      lg.addColorStop(0, rgba(AMBER, 0.35 * (1 - lift))); lg.addColorStop(1, rgba(AMBER, 0));
      ctx.fillStyle = lg; ctx.beginPath(); ctx.ellipse(lx, ly + unit * 0.01, R * 1.6, unit * 0.04, 0, 0, TAU); ctx.fill();
      ctx.restore();
      // forearm then hand gripping the top of the stone (fingers over it, back of the hand toward us)
      const hs = R * 1.25;
      const ang = Math.PI + 0.45 + rot * 0.5;
      const wx = sx + R * 0.2, wy = sy - R * 1.32;
      const fdx = Math.sin(ang), fdy = -Math.cos(ang);
      ctx.save(); ctx.lineCap = 'round';
      ctx.strokeStyle = rgba([168, 122, 98]); ctx.lineWidth = hs * 0.42;
      ctx.beginPath(); ctx.moveTo(wx, wy); ctx.lineTo(wx - fdx * unit * 0.9, wy - fdy * unit * 0.9); ctx.stroke();
      ctx.restore();
      FX.hand(ctx, wx, wy, ang, hs, 'curl', { back: true, mirror: true, skin: [196, 146, 114], shadow: [120, 75, 60] });
      FX.glow(ctx, wx, wy + hs * 0.4, hs, AMBER, 0.1 * glowK);
    },
  },

  // custom: in an empty dark field a single small flower of light opens and glows on its own
  flower_of_light: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 16000), [4, 6, 14], [10, 12, 24], () => 0.5);
      const gy = land ? h * 0.74 : h * 0.66;
      // empty field
      const fg = ctx.createLinearGradient(0, gy - unit * 0.02, 0, h);
      fg.addColorStop(0, rgba([16, 18, 30])); fg.addColorStop(1, rgba([8, 9, 16]));
      ctx.fillStyle = fg; ctx.fillRect(0, gy, w, h - gy);
      const hz = ctx.createLinearGradient(0, gy - unit * 0.08, 0, gy + 2);
      hz.addColorStop(0, rgba([40, 40, 70], 0)); hz.addColorStop(1, rgba([40, 40, 70], 0.35));
      ctx.fillStyle = hz; ctx.fillRect(0, gy - unit * 0.08, w, unit * 0.08 + 2);
      const cx = w / 2, open = easeInOut(clamp((u + 0.05) / 0.8));
      const sway = Math.sin(t * 0.5) * 0.03;
      const stemH = unit * 0.22;
      const top = [cx + Math.sin(sway) * stemH, gy - stemH];
      const glowK = 0.35 + 0.65 * open;
      // ground light pool
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const pg = ctx.createRadialGradient(cx, gy, 0, cx, gy, unit * 0.4);
      pg.addColorStop(0, rgba(AMBER, 0.22 * glowK)); pg.addColorStop(1, rgba(AMBER, 0));
      ctx.fillStyle = pg; ctx.beginPath(); ctx.ellipse(cx, gy + unit * 0.01, unit * 0.4, unit * 0.06, 0, 0, TAU); ctx.fill();
      ctx.restore();
      // stem + leaves
      ctx.save(); ctx.strokeStyle = rgba([255, 200, 130], 0.75); ctx.lineWidth = unit * 0.006; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(cx, gy); ctx.quadraticCurveTo(cx - unit * 0.02, gy - stemH * 0.5, top[0], top[1]); ctx.stroke();
      ctx.fillStyle = rgba([255, 200, 130], 0.55);
      [[-1, 0.3], [1, 0.48]].forEach(([s, f]) => {
        const lx = cx - unit * 0.01 * f, ly = gy - stemH * f, ll = unit * 0.05 * (0.6 + 0.4 * open);
        ctx.beginPath(); ctx.moveTo(lx, ly);
        ctx.quadraticCurveTo(lx + s * ll * 0.5, ly - ll * 0.6, lx + s * ll, ly - ll * 0.35);
        ctx.quadraticCurveTo(lx + s * ll * 0.5, ly - ll * 0.05, lx, ly); ctx.fill();
      });
      ctx.restore();
      FX.glow(ctx, top[0], top[1], unit * (0.15 + 0.2 * open), AMBER, 0.35 * glowK * (0.9 + 0.1 * Math.sin(t * 1.1)));
      // petals
      const NP = 7, pl = unit * 0.075;
      ctx.save(); ctx.translate(top[0], top[1]); ctx.rotate(sway);
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < NP; i++) {
        const full = -Math.PI / 2 + (i - (NP - 1) / 2) * (TAU / NP) * 0.92;
        const bud = -Math.PI / 2 + (i - (NP - 1) / 2) * 0.09;
        const a = lerp(bud, full, open);
        const L = pl * lerp(0.6, 1, open);
        ctx.save(); ctx.rotate(a + Math.PI / 2);
        const g = ctx.createLinearGradient(0, 0, 0, -L);
        g.addColorStop(0, rgba([255, 245, 220], 0.75)); g.addColorStop(1, rgba(AMBER, 0.25));
        ctx.fillStyle = g;
        const bw = L * lerp(0.22, 0.36, open);
        ctx.beginPath(); ctx.moveTo(0, 0);
        ctx.bezierCurveTo(bw, -L * 0.3, bw, -L * 0.8, 0, -L);
        ctx.bezierCurveTo(-bw, -L * 0.8, -bw, -L * 0.3, 0, 0); ctx.fill();
        ctx.restore();
      }
      ctx.restore();
      FX.light(ctx, top[0], top[1], unit * 0.01 * (0.6 + 0.4 * open), [255, 240, 200], 0.9);
      // a few motes rising from it once open
      const rnd = U.rng((p.seed | 0) + 66);
      for (let i = 0; i < 7; i++) {
        const per = 5 + rnd() * 3, ph = rnd(), dx = (rnd() - 0.5) * unit * 0.12;
        const fr = (t / per + ph) % 1;
        const a = Math.sin(Math.PI * fr) * open * 0.6;
        FX.glow(ctx, top[0] + dx * fr + Math.sin(t * 0.6 + i) * unit * 0.01, top[1] - fr * unit * 0.3, unit * 0.012, GOLD, a);
      }
    },
  },

  // the last ship, small and dim, drifting among dying stars
  ship_exterior: {
    draw(ctx, w, h, p) {
      const unit = Math.min(w, h), u = p.u, t = p.t;
      const land = w > h;
      night(ctx, w, h, p, Math.round(w * h / 4500), [4, 5, 12], [12, 10, 24], (i) => 0.55 * (1 - (i % 5 === 0 ? ease(0.1 + (i % 7) * 0.1, 0.3 + (i % 7) * 0.1, u) : 0)));
      // dying stars: dim red giants and a fading white dwarf
      const giants = land ? [[0.82, 0.24, 0.16], [0.12, 0.78, 0.1], [0.3, 0.15, 0.06]] : [[0.78, 0.18, 0.2], [0.18, 0.82, 0.14], [0.25, 0.32, 0.07]];
      giants.forEach(([x, y, r], i) => {
        const br = 0.85 + 0.15 * Math.sin(t * 0.4 + i * 2);
        FX.glow(ctx, x * w, y * h, unit * r * 2.2, DARKRED, 0.5 * br);
        FX.glow(ctx, x * w, y * h, unit * r * 0.6, CRIMSON, 0.45 * br);
        FX.light(ctx, x * w, y * h, unit * r * 0.08, [255, 140, 120], 0.6 * br);
      });
      const wd = 1 - ease(0.2, 0.8, u) * 0.85;
      const wx = land ? w * 0.6 : w * 0.7, wy = land ? h * 0.8 : h * 0.68;
      FX.glow(ctx, wx, wy, unit * 0.06, [190, 210, 255], 0.35 * wd);
      FX.light(ctx, wx, wy, unit * 0.005, [220, 230, 255], 0.9 * wd);
      // ship
      const sx = lerp(w * 0.4, w * 0.56, u) + Math.sin(t * 0.2) * unit * 0.01;
      const sy = h * 0.5 + Math.sin(t * 0.27) * unit * 0.012;
      const L = unit * 0.36;
      ctx.save(); ctx.translate(sx, sy); ctx.rotate(-0.12 + Math.sin(t * 0.15) * 0.02);
      // engine faint glow at the back
      FX.glow(ctx, -L * 0.55, 0, L * 0.25, [120, 170, 255], 0.18 + 0.05 * Math.sin(t * 0.9));
      const hull = ctx.createLinearGradient(0, -L * 0.12, 0, L * 0.12);
      hull.addColorStop(0, rgba([110, 92, 110])); hull.addColorStop(0.45, rgba([52, 50, 70])); hull.addColorStop(1, rgba([20, 20, 32]));
      // ring module, back half (behind the hull)
      ctx.strokeStyle = rgba([70, 62, 82]); ctx.lineWidth = L * 0.028;
      ctx.beginPath(); ctx.ellipse(-L * 0.12, 0, L * 0.05, L * 0.17, 0, -Math.PI / 2, Math.PI / 2); ctx.stroke();
      ctx.fillStyle = hull;
      // main hull
      ctx.beginPath();
      ctx.moveTo(L * 0.5, 0);
      ctx.quadraticCurveTo(L * 0.42, -L * 0.07, L * 0.2, -L * 0.075);
      ctx.lineTo(-L * 0.45, -L * 0.07); ctx.lineTo(-L * 0.52, -L * 0.045); ctx.lineTo(-L * 0.52, L * 0.045); ctx.lineTo(-L * 0.45, L * 0.07);
      ctx.lineTo(L * 0.2, L * 0.075);
      ctx.quadraticCurveTo(L * 0.42, L * 0.07, L * 0.5, 0); ctx.fill();
      // ring module
      ctx.strokeStyle = rgba([90, 80, 100]); ctx.lineWidth = L * 0.028;
      ctx.beginPath(); ctx.ellipse(-L * 0.12, 0, L * 0.05, L * 0.17, 0, Math.PI / 2, Math.PI * 1.5); ctx.stroke();
      ctx.strokeStyle = rgba([200, 120, 120], 0.35); ctx.lineWidth = L * 0.008;
      ctx.beginPath(); ctx.ellipse(-L * 0.12, 0, L * 0.05, L * 0.17, 0, -Math.PI * 0.95, -Math.PI * 0.2); ctx.stroke();
      // engine block
      ctx.fillStyle = rgba([34, 32, 46]);
      rr(ctx, -L * 0.6, -L * 0.05, L * 0.1, L * 0.1, L * 0.02); ctx.fill();
      // red rim light along the top from the giant
      ctx.strokeStyle = rgba([255, 120, 110], 0.35); ctx.lineWidth = L * 0.008;
      ctx.beginPath(); ctx.moveTo(L * 0.46, -L * 0.03); ctx.quadraticCurveTo(L * 0.4, -L * 0.07, L * 0.2, -L * 0.075); ctx.lineTo(-L * 0.45, -L * 0.07); ctx.stroke();
      // windows: a few dim warm lights
      for (let i = 0; i < 6; i++) {
        const x = L * (0.3 - i * 0.075);
        if (Math.abs(x + L * 0.12) < L * 0.05) continue;
        const on = U.hash2(i, 3) < 0.6 ? 0.7 + 0.3 * Math.sin(t * 0.5 + i) : 0.12;
        ctx.fillStyle = rgba(AMBER, 0.75 * on);
        ctx.fillRect(x - L * 0.012, -L * 0.02, L * 0.024, L * 0.016);
      }
      ctx.restore();
      FX.glow(ctx, sx + L * 0.05, sy, L * 0.25, AMBER, 0.08);
    },
  },
};
