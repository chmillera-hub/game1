// fx.mjs - effects. All deterministic in t.
// waterPour(g,{x0,y0 (lip),x1,y1 (hands/landing),t,flow 0..1,width=18}) glossy stream + bands + droplets + splash.
// splash(g,{x,y,s,t,k 0..1 intensity})
// sandSlide(g,{x,y,w,h (surface box: grains bead off top->bottom),t,k 0..1,n=40,color})
// sandGust(g,{t,k 0..1,y=H*0.7,dir 1|-1,n=60})
// rain(g,{t,intensity 0..1,angle (rad from vertical, default 0.18),color}) <=120 streaks
// faceDrops(g,{x,y,w,h,t,k}) small drops running down within box
// lightning(g,{k 0..1 flash, x, seed}) full-frame flash + bolt when k>0.5
// scanRing(g,{cx,cy,r,k 0..1,squash=0.32}) cyan elliptical ground ring with ticks (fades as k->1)
// glint(g,{x,y,s,k 0..1})  4-point star sparkle
// chips(g,{x,y,t (seconds since strike),s,seed}) stone chips flying ~0.6 s
// dayCounter(g,{text:'DAY 400',k 0..1 alpha,x=W/2,y=H*0.12,size=30}) HUD bracketed
// powerReadout(g,{pct (number), k alpha, x, y, size}) 'POWER 4%' with bar
// stars(g,{t,k alpha,horizonY=H*0.6,seed}) cached starfield + few twinkles
// shipLight(g,{x,y,t,k}) distant bobbing lamp
// leavesVines(g,{x,y,w,h,k 0..1 growth,seed}) vines creeping over a box (for dormant Keeper)
import { W, H, PAL, TAU, clamp, lerp, smoothstep, noise1, hash, rng, mix, rgba, shade, ellipse, glow, cached, taperStroke } from './core.mjs';

export function waterPour(g, o = {}) {
  const { x0 = 0, y0 = 0, x1 = 0, y1 = 100, t = 0, flow = 1, width = 18 } = o; if (flow <= 0) return;
  const w = width * (0.5 + 0.5 * flow), cx = x0 + (x1 - x0) * 0.15;
  const pt = u => { const a = 1 - u; return [a * a * x0 + 2 * a * u * cx + u * u * x1, a * a * y0 + 2 * a * u * (y0 + 6) + u * u * y1]; };
  const reach = clamp(flow * 3); // stream front grows in
  const N = 16, L = [], R = [];
  for (let i = 0; i <= N; i++) { const u = i / N * reach, p = pt(u), ww = w * lerp(1, 0.62, u) * (1 + noise1(u * 6 - t * 8, 2) * 0.12);
    L.push([p[0] - ww / 2, p[1]]); R.push([p[0] + ww / 2, p[1]]); }
  g.save();
  const gr = g.createLinearGradient(x1 - w, 0, x1 + w, 0);
  gr.addColorStop(0, 'rgba(120,190,215,0.75)'); gr.addColorStop(0.35, 'rgba(210,240,250,0.85)'); gr.addColorStop(0.6, 'rgba(110,180,205,0.7)'); gr.addColorStop(1, 'rgba(70,140,170,0.75)');
  g.beginPath(); L.forEach((p, i) => i ? g.lineTo(...p) : g.moveTo(...p)); R.reverse().forEach(p => g.lineTo(...p)); g.closePath(); g.fillStyle = gr; g.fill();
  g.clip();
  for (let b = 0; b < 4; b++) { const u = ((t * 1.6 + b / 4) % 1) * reach, p = pt(u);
    g.fillStyle = 'rgba(255,255,255,0.55)'; g.beginPath(); ellipse(g, p[0] - w * 0.1, p[1], w * 0.25, 9); g.fill(); }
  g.fillStyle = 'rgba(255,255,255,0.6)'; for (let i = 0; i < N * reach; i++) { const p = pt(i / N); g.fillRect(p[0] - w * 0.18, p[1], 2, w); }
  g.restore();
  if (reach >= 1) splash(g, { x: x1, y: y1, s: w / 18, t, k: flow });
  const r = rng(5); for (let i = 0; i < 6; i++) { const ph = (t * 1.3 + r()) % 1, u = 0.3 + r() * 0.7, p = pt(u * reach);
    g.fillStyle = 'rgba(220,245,255,0.8)'; g.beginPath(); ellipse(g, p[0] + (r() - 0.5) * w * 2 * ph, p[1] + ph * 30, 2.5, 3.5); g.fill(); }
}
export function splash(g, o = {}) {
  const { x = 0, y = 0, s = 1, t = 0, k = 1 } = o; if (k <= 0) return; const r = rng(11);
  g.save(); g.globalAlpha = k;
  for (let i = 0; i < 12; i++) { const ph = (t * 2.2 + i / 12) % 1, a = -Math.PI / 2 + (r() - 0.5) * 2.4, v = (30 + r() * 40) * s;
    const px = x + Math.cos(a) * v * ph, py = y + Math.sin(a) * v * ph + 90 * s * ph * ph;
    g.fillStyle = `rgba(225,245,255,${0.85 * (1 - ph)})`; g.beginPath(); ellipse(g, px, py, 3 * s, 3.5 * s); g.fill(); }
  g.fillStyle = 'rgba(235,250,255,0.55)'; g.beginPath(); ellipse(g, x, y, 22 * s * (1 + Math.sin(t * 20) * 0.08), 6 * s); g.fill();
  g.restore();
}
export function sandSlide(g, o = {}) {
  const { x = 0, y = 0, w = 100, h = 100, t = 0, k = 1, n = 40, color = PAL.sand } = o; if (k <= 0) return; const r = rng(23);
  for (let i = 0; i < n; i++) { const gx = x + r() * w, sp = 0.5 + r() * 0.8, ph = (t * sp + r()) % 1, fall = ph * ph;
    const py = y + fall * (h + 40), a = k * (ph < 0.8 ? 1 : (1 - ph) * 5) * (py > y + h ? 0.7 : 1);
    g.fillStyle = rgba(i % 3 ? color : shade(color, -0.25), a); g.beginPath(); ellipse(g, gx + Math.sin(ph * 6 + i) * 2, py, 2.2, 2.2); g.fill(); }
}
export function sandGust(g, o = {}) {
  const { t = 0, k = 1, y = H * 0.7, dir = 1, n = 60 } = o; if (k <= 0) return; const r = rng(29);
  g.save(); g.globalAlpha = k; g.lineCap = 'round';
  for (let i = 0; i < n; i++) { const sp = 0.4 + r() * 0.6, ph = (t * sp + r()) % 1, px = dir > 0 ? -40 + ph * (W + 80) : W + 40 - ph * (W + 80);
    const py = y + (r() - 0.5) * 300 + Math.sin(t * 3 + i) * 10;
    g.strokeStyle = rgba(PAL.sand, 0.55); g.lineWidth = 1.6 + r() * 1.5; g.beginPath(); g.moveTo(px, py); g.lineTo(px - dir * (8 + r() * 18), py + 2); g.stroke(); }
  const gr = g.createLinearGradient(0, y - 160, 0, y + 160); gr.addColorStop(0, rgba(PAL.sand, 0)); gr.addColorStop(0.5, rgba(PAL.sand, 0.15)); gr.addColorStop(1, rgba(PAL.sand, 0));
  g.fillStyle = gr; g.fillRect(0, y - 160, W, 320); g.restore();
}
export function rain(g, o = {}) {
  const { t = 0, intensity = 1, angle = 0.18, color = '#cfe0f0' } = o; const n = Math.round(120 * clamp(intensity)); if (!n) return; const r = rng(41);
  g.save(); g.lineCap = 'round'; const dx = Math.sin(angle), dy = Math.cos(angle);
  for (let i = 0; i < n; i++) { const sp = 1.6 + r() * 1.2, len = 40 + r() * 60, ph = (t * sp + r()) % 1, x0 = r() * (W + 300) - 150;
    const d = ph * (H + 200) - 100, px = x0 + dx * d, py = d;
    g.strokeStyle = rgba(color, 0.18 + r() * 0.3); g.lineWidth = 1 + r() * 1.2; g.beginPath(); g.moveTo(px, py); g.lineTo(px - dx * len, py - dy * len); g.stroke(); }
  g.restore();
}
export function faceDrops(g, o = {}) {
  const { x = 0, y = 0, w = 100, h = 100, t = 0, k = 1 } = o; if (k <= 0) return; const r = rng(53);
  for (let i = 0; i < 8; i++) { const sp = 0.15 + r() * 0.3, ph = (t * sp + r()) % 1, px = x + r() * w, py = y + ph * h, a = k * Math.sin(ph * Math.PI);
    g.fillStyle = `rgba(200,225,245,${0.5 * a})`; g.beginPath(); ellipse(g, px, py, 2.5, 3.5); g.fill();
    g.fillStyle = `rgba(255,255,255,${0.9 * a})`; g.beginPath(); ellipse(g, px - 0.8, py - 1.2, 0.9, 0.9); g.fill(); }
}
export function lightning(g, o = {}) {
  const { k = 0, x = W * 0.6, seed = 1 } = o; if (k <= 0) return;
  g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(190,215,255,${0.45 * k})`; g.fillRect(0, 0, W, H);
  if (k > 0.5) { const r = rng(seed); let px = x, py = 0; const pts = [[px, py]]; while (py < H * 0.5) { px += (r() - 0.5) * 70; py += 30 + r() * 40; pts.push([px, py]); }
    g.lineJoin = 'round'; g.strokeStyle = `rgba(200,225,255,${0.5 * k})`; g.lineWidth = 10; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(...p) : g.moveTo(...p)); g.stroke();
    g.strokeStyle = `rgba(255,255,255,${k})`; g.lineWidth = 3; g.stroke(); }
  g.restore();
}
export function scanRing(g, o = {}) {
  const { cx = W / 2, cy = H * 0.7, r = 300, k = 0.5, squash = 0.32 } = o; if (k <= 0 || k >= 1) return;
  const rr = r * smoothstep(0, 1, k), a = Math.sin(k * Math.PI);
  g.save(); g.globalCompositeOperation = 'lighter'; g.strokeStyle = rgba(PAL.hud, 0.8 * a); g.lineWidth = 2;
  g.shadowColor = PAL.hud; g.shadowBlur = 8;
  g.beginPath(); ellipse(g, cx, cy, rr, rr * squash); g.stroke();
  g.strokeStyle = rgba(PAL.hud, 0.3 * a); g.beginPath(); ellipse(g, cx, cy, rr * 0.92, rr * 0.92 * squash); g.stroke();
  g.lineWidth = 1.5; g.strokeStyle = rgba(PAL.hud, 0.8 * a);
  for (let i = 0; i < 24; i++) { const an = i / 24 * TAU + k, c = Math.cos(an), s = Math.sin(an), l = i % 6 ? 6 : 14;
    g.beginPath(); g.moveTo(cx + c * rr, cy + s * rr * squash); g.lineTo(cx + c * (rr + l), cy + s * (rr + l) * squash); g.stroke(); }
  g.restore();
}
export function glint(g, o = {}) {
  const { x = 0, y = 0, s = 1, k = 1 } = o; if (k <= 0) return; const L = 30 * s * k;
  g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(255,250,235,${k})`;
  g.beginPath(); for (let i = 0; i < 8; i++) { const a = i / 8 * TAU, rr = i % 2 ? L * 0.12 : (i % 4 ? L * 0.6 : L); const px = x + Math.sin(a) * rr, py = y - Math.cos(a) * rr; i ? g.lineTo(px, py) : g.moveTo(px, py); }
  g.closePath(); g.fill(); g.restore(); glow(g, x, y, L * 0.9, '#fff4d6', 0.5 * k);
}
export function chips(g, o = {}) {
  const { x = 0, y = 0, t = 0, s = 1, seed = 1 } = o; if (t < 0 || t > 0.7) return; const r = rng(seed * 7 + 3);
  for (let i = 0; i < 7; i++) { const a = -Math.PI / 2 + (r() - 0.5) * 2.6, v = (120 + r() * 160) * s;
    const px = x + Math.cos(a) * v * t, py = y + Math.sin(a) * v * t + 500 * s * t * t;
    g.fillStyle = `rgba(200,192,178,${1 - t / 0.7})`; g.beginPath(); g.rect(px, py, 3 * s, 2.5 * s); g.fill(); }
  g.fillStyle = `rgba(220,212,200,${0.4 * (1 - t / 0.7)})`; g.beginPath(); ellipse(g, x, y, 12 * s * (1 + t * 3), 8 * s * (1 + t * 3)); g.fill();
}
function brackets(g, x, y, w, h, a) {
  const c = 10; g.save(); g.strokeStyle = rgba(PAL.hud, 0.9 * a); g.lineWidth = 2; g.shadowColor = PAL.hud; g.shadowBlur = 8;
  g.beginPath(); g.moveTo(x + c, y); g.lineTo(x, y); g.lineTo(x, y + h); g.lineTo(x + c, y + h);
  g.moveTo(x + w - c, y); g.lineTo(x + w, y); g.lineTo(x + w, y + h); g.lineTo(x + w - c, y + h); g.stroke(); g.restore();
}
export function dayCounter(g, o = {}) {
  const { text = 'DAY 1', k = 1, x = W / 2, y = H * 0.12, size = 30 } = o; if (k <= 0) return;
  g.save(); g.font = `${size}px HUDMono`; g.letterSpacing = `${Math.round(size * 0.2)}px`; const tw = g.measureText(text).width; g.restore();
  const bw = tw + 50, bh = size * 1.7;
  g.save(); g.globalAlpha = k * 0.35; g.fillStyle = '#04141c'; g.fillRect(x - bw / 2, y - bh / 2, bw, bh); g.restore();
  brackets(g, x - bw / 2, y - bh / 2, bw, bh, k);
  g.save(); g.letterSpacing = `${Math.round(size * 0.2)}px`; g.restore();
  g.save(); g.globalAlpha = k; g.font = `${size}px HUDMono`; g.letterSpacing = `${Math.round(size * 0.2)}px`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.shadowColor = rgba(PAL.hud, 0.8); g.shadowBlur = 10; g.fillStyle = PAL.hud; g.fillText(text, x + size * 0.1, y); g.restore();
}
export function powerReadout(g, o = {}) {
  const { pct = 4, k = 1, x = W / 2, y = H * 0.12, size = 26 } = o; if (k <= 0) return;
  const text = `POWER ${Math.round(pct)}%`, bw = 260, bh = size * 2.6;
  g.save(); g.globalAlpha = k * 0.35; g.fillStyle = '#04141c'; g.fillRect(x - bw / 2, y - bh / 2, bw, bh); g.restore();
  brackets(g, x - bw / 2, y - bh / 2, bw, bh, k);
  const low = pct < 10, col = low ? '#ff9a6a' : PAL.hud;
  g.save(); g.globalAlpha = k; g.font = `${size}px HUDMono`; g.letterSpacing = `${Math.round(size * 0.15)}px`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.shadowColor = col; g.shadowBlur = 10; g.fillStyle = col; g.fillText(text, x, y - size * 0.4);
  g.shadowBlur = 0; g.strokeStyle = rgba(PAL.hud, 0.6); g.lineWidth = 1.5; g.strokeRect(x - 100, y + size * 0.45, 200, 10);
  g.fillStyle = col; g.fillRect(x - 98, y + size * 0.45 + 2, 196 * clamp(pct / 100), 6); g.restore();
}
export function stars(g, o = {}) {
  const { t = 0, k = 1, horizonY = H * 0.6, seed = 1 } = o; if (k <= 0) return;
  const c = cached('stars:' + seed + ':' + Math.round(horizonY), x => { const r = rng(seed);
    for (let i = 0; i < 260; i++) { const sx = r() * W, sy = Math.pow(r(), 1.4) * horizonY, b = r();
      x.fillStyle = `rgba(235,240,255,${0.25 + b * 0.6 * (1 - sy / horizonY * 0.6)})`; x.beginPath(); ellipse(x, sx, sy, 0.6 + b * 1.1, 0.6 + b * 1.1); x.fill(); } });
  g.save(); g.globalAlpha = k; g.globalCompositeOperation = 'lighter'; g.drawImage(c, 0, 0);
  const r = rng(seed + 99); for (let i = 0; i < 6; i++) { const sx = r() * W, sy = r() * horizonY * 0.7, tw = 0.5 + 0.5 * Math.sin(t * (1 + r() * 2) + i * 2);
    glow(g, sx, sy, 6, '#e8f0ff', 0.6 * tw * k); }
  g.restore();
}
export function shipLight(g, o = {}) {
  const { x = 0, y = 0, t = 0, k = 1 } = o; if (k <= 0) return; const by = y + Math.sin(t * 1.6) * 2, fl = 0.85 + 0.15 * Math.sin(t * 9);
  glow(g, x, by, 26, '#ffcf8a', 0.7 * k * fl); g.fillStyle = `rgba(255,240,210,${k})`; g.beginPath(); ellipse(g, x, by, 2, 2); g.fill();
  g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(255,200,130,${0.2 * k})`; g.fillRect(x - 1.5, by + 4, 3, 26); g.restore();
}
export function leavesVines(g, o = {}) {
  const { x = 0, y = 0, w = 200, h = 300, k = 1, seed = 3 } = o; if (k <= 0) return; const r = rng(seed);
  for (let v = 0; v < 5; v++) { const sx = x + r() * w, n = 10, pts = []; let px = sx, py = y + h;
    for (let i = 0; i <= n * k; i++) { pts.push([px, py]); px += (r() - 0.5) * 30; py -= h / n * (0.6 + r() * 0.5); }
    if (pts.length < 2) continue; taperStroke(g, pts, 5, 2, '#3f6a35');
    pts.forEach(([lx, ly], i) => { if (i % 2) return; const sd = i % 4 ? 1 : -1;
      g.fillStyle = i % 3 ? PAL.palm : PAL.palmShadow; g.beginPath(); ellipse(g, lx + sd * 9, ly, 10, 5, sd * 0.6); g.fill();
      g.strokeStyle = PAL.ink; g.lineWidth = 1.2; g.stroke(); }); }
}
