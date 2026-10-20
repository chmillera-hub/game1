// props.mjs - island objects. All draw at (x,y) = ground/base point unless noted, scale s (1 = nominal size).
// crab(g,{x,y,s,t,flipped,legs,eyeYaw,clawRaise,walk,facing,light})  Captain. s=1 ~ 120px wide. flipped: on back,
//    legs wiggle with t (legs 0..1 amplitude). walk 0..1 scuttle amount (legs cycle with t). eyeYaw -1..1, clawRaise 0..1.
// carvedStone(g,{x,y,s,lines:['WATER'],arrow:bool,icon:'check'|'x'|null,progress 0..1,shape:'slab'|'round'|'wall',
//    light:LIGHT.x, size(font px), w,h}) engraved text appears glyph by glyph (then arrow, then icon) with progress.
// mapStone(g,{x,y,s,progress,light})  scratched island map: outline, reef marks, channel arrow.
// bush(g,{x,y,s,berry:'blue'|'red',t,light}); coconut(g,{x,y,s}); sapling(g,{x,y,s,t});
// hut(g,{x,y,s,build 0..1,view:'front'|'side',light}) base ~300px wide at s=1: posts->frame->thatch->door.
// tower(g,{x,y,s,build 0..1,lantern 0..1,beamAngle,view,light,t}) stacked-stone cairn ~520px tall at s=1;
//    returns {lx,ly} lantern center. Draws beam() itself if lantern>0 and beamAngle!=null.
// beam(g,{x,y,angle(rad, 0 = +x),length,spread(rad half-angle),intensity 0..1}) additive cone+core+flare.
// boat(g,{x,y,s,roll(rad),heave(px),sail 0..1 (0 furled),light}) ~300px long at s=1, (x,y)=waterline center.
// palm(g,{x,y,s,growth 0..1,sway -1..1,t,light}) ~600px tall at growth 1.
// powerCell(g,{x,y,s,glow 0..1}); shellTool(g,{x,y,s,rot}); markerStone(g,{x,y,s,pole}); gull(g,{x,y,s,flap 0..1 phase,facing}).
import { PAL, LIGHT, TAU, clamp, lerp, invLerp, smoothstep, noise1, hash, rng, mix, rgba, shade, cel, ellipse,
  splinePath, polyPath, taperStroke, glow } from './core.mjs';

const L0 = LIGHT.day;
const sh = (c, light) => mix(c, (light || L0).shadow, 0.45);

// ---------------------------------------------------------------- crab
export function crab(g, o = {}) {
  const { x = 0, y = 0, s = 1, t = 0, flipped = false, legs = 1, eyeYaw = 0, clawRaise = 0, walk = 0, facing = 1, light } = o;
  g.save(); g.translate(x, y); g.scale(s * facing, s);
  const lw = 2.6;
  // contact shadow
  g.fillStyle = 'rgba(40,25,20,0.25)'; g.beginPath(); ellipse(g, 0, 2, 58, 9); g.fill();
  if (flipped) {
    g.translate(0, -26);
    // shell (opening up) - spiral seen from side
    cel(g, x => { ellipse(x, 0, 6, 46, 30); }, { fill: PAL.shell, shadow: sh(PAL.shell, light),
      shadowFn: x => ellipse(x, 0, 24, 46, 18), lw });
    g.strokeStyle = PAL.shellStripe; g.lineWidth = 4; g.lineCap = 'round';
    for (const k of [-20, 0, 20]) { g.beginPath(); g.arc(k, 6, 26, -2.2, -0.9); g.stroke(); }
    // wiggling legs upward
    for (let i = 0; i < 4; i++) for (const sd of [-1, 1]) {
      const ph = t * 14 + i * 1.7 + (sd > 0 ? 0.8 : 0), w = Math.sin(ph) * 0.45 * legs;
      const bx = sd * (8 + i * 9), by = -22;
      const a = -Math.PI / 2 + sd * (0.35 + i * 0.25) + w;
      const kx = bx + Math.cos(a) * 22, ky = by + Math.sin(a) * 22;
      const b = a + sd * 0.9 + w * 0.6;
      taperStroke(g, [[bx, by], [kx, ky], [kx + Math.cos(b) * 18, ky + Math.sin(b) * 18]], 7, 3, PAL.ink);
      taperStroke(g, [[bx, by], [kx, ky], [kx + Math.cos(b) * 18, ky + Math.sin(b) * 18]], 4.5, 1.5, PAL.crab);
    }
    // claws waving
    for (const sd of [-1, 1]) {
      const w = Math.sin(t * 9 + sd) * 0.3 * legs, a = -Math.PI / 2 + sd * 0.15 + w;
      const cx = sd * 6 + Math.cos(a) * 34, cy = -20 + Math.sin(a) * 34;
      taperStroke(g, [[sd * 6, -18], [cx, cy]], 8, 6, PAL.ink); taperStroke(g, [[sd * 6, -18], [cx, cy]], 5, 4, PAL.crab);
      cel(g, x => ellipse(x, cx, cy - 6, 9, 12, w), { fill: PAL.crab, lw: 2 });
    }
    // eye stalks flailing
    for (const sd of [-1, 1]) {
      const a = -Math.PI / 2 + sd * 0.5 + Math.sin(t * 11 + sd * 2) * 0.3;
      const ex = Math.cos(a) * 24, ey = -22 + Math.sin(a) * 24;
      g.strokeStyle = PAL.ink; g.lineWidth = 3; g.beginPath(); g.moveTo(sd * 3, -24); g.lineTo(ex, ey); g.stroke();
      g.fillStyle = PAL.ink; g.beginPath(); ellipse(g, ex, ey, 4.5, 4.5); g.fill();
      g.fillStyle = '#fff'; g.beginPath(); ellipse(g, ex - 1.2, ey - 1.5, 1.4, 1.4); g.fill();
    }
    g.restore(); return;
  }
  const bob = walk ? Math.abs(Math.sin(t * 16)) * 2.5 * walk : 0;
  g.translate(0, -bob);
  // legs (behind body)
  for (let i = 0; i < 3; i++) for (const sd of [-1, 1]) {
    const ph = t * 16 + i * 2.1 + (sd > 0 ? Math.PI : 0);
    const lift = walk * Math.max(0, Math.sin(ph)) * 6, sw = walk * Math.cos(ph) * 5;
    const bx = sd * (10 + i * 7) + 6, by = -16;
    const kx = bx + sd * 20 + sw, ky = by - 10 - lift, fx = bx + sd * 30 + sw * 1.4, fy = 0 - lift * 0.6 + bob;
    taperStroke(g, [[bx, by], [kx, ky], [fx, fy]], 7, 2.5, PAL.ink);
    taperStroke(g, [[bx, by], [kx, ky], [fx, fy]], 4.5, 1.2, i === 2 ? PAL.crabShadow : PAL.crab);
  }
  // shell (spiral) behind-left
  g.save(); g.translate(-14, -40);
  cel(g, x => { splinePath(x, [[-40, 18], [-44, -8], [-22, -34], [8, -36], [30, -16], [34, 14], [10, 22]]); },
    { fill: PAL.shell, shadow: sh(PAL.shell, light), shadowFn: x => ellipse(x, -4, 28, 50, 20), lw });
  g.strokeStyle = PAL.shellStripe; g.lineWidth = 4.5; g.lineCap = 'round';
  g.beginPath(); for (let a = 0; a < 9; a += 0.15) { const r = 30 - a * 2.9, px = -6 + Math.cos(a + 2.5) * r, py = -6 + Math.sin(a + 2.5) * r * 0.85; a ? g.lineTo(px, py) : g.moveTo(px, py); } g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.55)'; g.beginPath(); ellipse(g, -18, -20, 9, 4, -0.6); g.fill();
  g.restore();
  // body / face front
  cel(g, x => ellipse(x, 18, -20, 20, 14), { fill: PAL.crab, shadow: PAL.crabShadow, shadowFn: x => ellipse(x, 18, -10, 22, 8), lw });
  // eye stalks
  for (const sd of [-1, 1]) {
    const bx = 14 + sd * 7, by = -30, a = -Math.PI / 2 + eyeYaw * 0.55 + sd * 0.18 + Math.sin(t * 1.3 + sd) * 0.05;
    const ex = bx + Math.cos(a) * 24, ey = by + Math.sin(a) * 24;
    g.strokeStyle = PAL.ink; g.lineWidth = 3.4; g.lineCap = 'round'; g.beginPath(); g.moveTo(bx, by); g.lineTo(ex, ey); g.stroke();
    g.fillStyle = PAL.ink; g.beginPath(); ellipse(g, ex, ey, 5.5, 6.5, a + Math.PI / 2); g.fill();
    g.fillStyle = '#fff'; g.beginPath(); ellipse(g, ex + 1.5 + eyeYaw * 1.5, ey - 2, 1.8, 1.8); g.fill();
  }
  // claws (front), clawRaise lifts the big one
  const claw = (bx, big, raise) => {
    const a = lerp(-0.2, -1.6, raise), r = big ? 22 : 16;
    const cx = bx + Math.cos(a) * r + 8, cy = -14 + Math.sin(a) * r;
    taperStroke(g, [[bx, -14], [cx, cy]], 8, 6, PAL.ink); taperStroke(g, [[bx, -14], [cx, cy]], 5, 4, PAL.crab);
    const sz = big ? 1 : 0.7, op = raise * 0.5 + Math.max(0, Math.sin(t * 6)) * 0.1 * raise;
    g.save(); g.translate(cx, cy); g.rotate(a + 0.6); g.scale(sz, sz);
    cel(g, x => { x.moveTo(-6, 6); x.quadraticCurveTo(-12, -10, 2, -16); x.quadraticCurveTo(10, -10, 4, -3); x.lineTo(-6, 6); },
      { fill: PAL.crab, shadow: PAL.crabShadow, shadowFn: x => ellipse(x, -4, 2, 8, 5), lw: 2.2 });
    g.rotate(-op); cel(g, x => { x.moveTo(-2, 2); x.quadraticCurveTo(14, -2, 12, -12); x.quadraticCurveTo(6, -4, -2, -2); }, { fill: PAL.crab, lw: 2 });
    g.restore();
  };
  claw(28, false, clawRaise * 0.3); claw(34, true, clawRaise);
  g.restore();
}

// ---------------------------------------------------------------- carved stone
// glyph-by-glyph reveal with an inset groove look (dark groove, light lower edge)
function carvedText(g, text, x, y, size, k, stone) {
  if (k <= 0) return;
  g.save(); g.font = `${size}px Carved`; g.textBaseline = 'middle'; g.letterSpacing = '0px';
  const full = [...text].reduce((a, c) => a + g.measureText(c).width + size * 0.08, 0) - size * 0.08; let cx = x - full / 2;
  const chars = [...text], n = chars.filter(c => c !== ' ').length || 1; let idx = 0;
  for (const c of chars) {
    const w = g.measureText(c).width + size * 0.08;
    if (c !== ' ') {
      const ck = clamp(k * n - idx); idx++;
      if (ck > 0) {
        g.save(); g.beginPath(); g.rect(cx - 2, y - size, (w + 4) * ck, size * 2); g.clip();
        g.fillStyle = shade(stone, 0.35); g.fillText(c, cx + 1.2, y + 1.6);         // light lower lip
        g.fillStyle = mix(stone, '#1c1410', 0.72); g.fillText(c, cx, y);           // groove
        g.fillStyle = mix(stone, '#1c1410', 0.45); g.fillText(c, cx + 0.8, y + 0.8); // groove floor
        g.restore();
      }
    }
    cx += w;
  }
  g.restore();
}
function groove(g, pts, k, w, stone) { // polyline revealed by length fraction k
  if (k <= 0) return; let tot = 0; const segs = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); segs.push(d); tot += d; }
  let rem = tot * clamp(k); const out = [pts[0]];
  for (let i = 1; i < pts.length && rem > 0; i++) { const f = Math.min(1, rem / segs[i - 1]); rem -= segs[i - 1];
    out.push([lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)]); }
  g.save(); g.lineCap = 'round'; g.lineJoin = 'round';
  const path = (dx, dy) => { g.beginPath(); out.forEach((p, i) => i ? g.lineTo(p[0] + dx, p[1] + dy) : g.moveTo(p[0] + dx, p[1] + dy)); };
  path(1.2, 1.6); g.strokeStyle = shade(stone, 0.35); g.lineWidth = w; g.stroke();
  path(0, 0); g.strokeStyle = mix(stone, '#1c1410', 0.72); g.lineWidth = w; g.stroke();
  path(0.7, 0.7); g.strokeStyle = mix(stone, '#1c1410', 0.45); g.lineWidth = w * 0.5; g.stroke();
  g.restore();
}
export function carvedStone(g, o = {}) {
  const { x = 0, y = 0, s = 1, lines = [], arrow = false, icon = null, progress = 1, shape = 'slab', light } = o;
  const size = o.size ?? 54, nL = lines.length;
  const w = o.w ?? Math.max(260, ...lines.map(l => l.length * size * 0.85 + 80)), h = o.h ?? (nL * size * 1.25 + (arrow || icon ? size * 1.4 : 0) + 70);
  g.save(); g.translate(x, y); g.scale(s, s);
  const stone = light ? mix(PAL.stone, light.key, 0.15) : PAL.stone;
  if (shape !== 'wall') {
    g.fillStyle = 'rgba(30,20,15,0.25)'; g.beginPath(); ellipse(g, 0, 4, w * 0.55, 14); g.fill();
    const pts = shape === 'round'
      ? [[-w / 2, 0], [-w / 2 - 8, -h * 0.5], [-w * 0.35, -h * 0.95], [0, -h - 6], [w * 0.38, -h * 0.94], [w / 2 + 6, -h * 0.5], [w / 2, 0]]
      : [[-w / 2, 0], [-w / 2 - 6, -h * 0.55], [-w / 2 + 10, -h + 6], [-w * 0.1, -h - 4], [w / 2 - 14, -h + 2], [w / 2 + 4, -h * 0.5], [w / 2 + 2, 0]];
    cel(g, x => splinePath(x, pts, true, 0.25), { fill: stone, shadow: sh(stone, light),
      shadowFn: x => { x.rect(w * 0.28, -h - 20, w, h + 40); }, hi: shade(stone, 0.12), hiFn: x => ellipse(x, -w * 0.2, -h * 0.85, w * 0.25, 10, -0.1), lw: 3 });
  }
  // sequence: lines, arrow, icon
  const parts = nL + (arrow ? 1 : 0) + (icon ? 1 : 0), P = clamp(progress) * parts;
  let yy = shape === 'wall' ? -h / 2 + size * 0.7 : -h + 40 + size * 0.55;
  lines.forEach((ln, i) => { carvedText(g, ln, 0, yy, size, clamp(P - i), stone); yy += size * 1.25; });
  let pi = nL; const iy = yy + size * 0.1;
  const gw = Math.max(4, size * 0.13);
  if (arrow) { const k = clamp(P - pi++), ax = icon ? -size * 0.6 : 0, L = size * 1.4;
    groove(g, [[ax - L / 2, iy], [ax + L / 2, iy]], k * 1.6, gw, stone);
    groove(g, [[ax + L / 2 - size * 0.35, iy - size * 0.32], [ax + L / 2, iy], [ax + L / 2 - size * 0.35, iy + size * 0.32]], k * 1.6 - 0.6, gw, stone); }
  if (icon) { const k = clamp(P - pi++), ix = arrow ? size * 1.0 : 0, r = size * 0.45;
    if (icon === 'check') groove(g, [[ix - r, iy], [ix - r * 0.25, iy + r * 0.7], [ix + r, iy - r * 0.8]], k, gw, stone);
    else { groove(g, [[ix - r, iy - r], [ix + r, iy + r]], k * 2, gw, stone); groove(g, [[ix + r, iy - r], [ix - r, iy + r]], k * 2 - 1, gw, stone); } }
  g.restore();
}
export function mapStone(g, o = {}) {
  const { x = 0, y = 0, s = 1, progress = 1, light } = o, w = 340, h = 280;
  const stone = light ? mix(PAL.stone, light.key, 0.15) : PAL.stone;
  g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = 'rgba(30,20,15,0.25)'; g.beginPath(); ellipse(g, 0, 4, w * 0.55, 14); g.fill();
  cel(g, x => splinePath(x, [[-w / 2, 0], [-w / 2 - 4, -h * 0.6], [-w * 0.3, -h], [w * 0.3, -h - 6], [w / 2 + 4, -h * 0.55], [w / 2, 0]], true, 0.3),
    { fill: stone, shadow: sh(stone, light), shadowFn: x => x.rect(w * 0.3, -h - 20, w, h + 40), lw: 3 });
  const P = clamp(progress) * 4, cy = -h * 0.5;
  const isl = []; for (let i = 0; i <= 22; i++) { const a = i / 22 * TAU, r = 70 + noise1(i * 0.9, 4) * 18 + (i % 3 === 0 ? 8 : 0);
    isl.push([-20 + Math.cos(a) * r * 1.15, cy + Math.sin(a) * r * 0.7]); }
  groove(g, isl, P, 4, stone);
  for (let i = 0; i < 7; i++) { const a = -0.9 + i * 0.32, r = 118, bx = -20 + Math.cos(a) * r * 1.15, by = cy + Math.sin(a) * r * 0.75;
    groove(g, [[bx - 7, by + 5], [bx - 2, by - 6], [bx + 3, by + 4], [bx + 8, by - 5]], (P - 1) * 7 - i, 3, stone); }
  groove(g, [[150, cy + 100], [118, cy + 70], [96, cy + 30]], P - 2, 4, stone);
  groove(g, [[84, cy + 44], [96, cy + 30], [108, cy + 46]], (P - 2.7) * 3, 4, stone);
  groove(g, [[-40, cy - 6], [-30, cy + 4]], (P - 3) * 2, 4, stone); groove(g, [[-30, cy - 6], [-40, cy + 4]], (P - 3.5) * 2, 4, stone);
  g.restore();
}

// ---------------------------------------------------------------- vegetation
export function bush(g, o = {}) {
  const { x = 0, y = 0, s = 1, berry = 'red', t = 0, light } = o, L = light || L0;
  g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = 'rgba(30,30,20,0.25)'; g.beginPath(); ellipse(g, 0, 2, 90, 12); g.fill();
  const leaf = mix(PAL.palm, L.key, 0.1), r = rng(7);
  const blobs = [[-50, -40, 42], [50, -42, 40], [0, -70, 50], [-20, -30, 40], [25, -28, 42]];
  cel(g, x => blobs.forEach(([bx, by, br]) => { x.moveTo(bx + br, by); ellipse(x, bx, by, br, br * 0.85); }),
    { fill: leaf, shadow: mix(leaf, L.shadow, 0.5), shadowFn: x => x.rect(-120, -50, 240, 60), lw: 2.5 });
  const bc = berry === 'blue' ? '#4a5fb8' : '#d23b3b';
  for (let i = 0; i < 16; i++) { const bx = (r() - 0.5) * 150, by = -20 - r() * 85;
    g.fillStyle = PAL.ink; g.beginPath(); ellipse(g, bx, by, 7, 7); g.fill();
    g.fillStyle = bc; g.beginPath(); ellipse(g, bx, by, 5.5, 5.5); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.75)'; g.beginPath(); ellipse(g, bx - 1.8, by - 1.8, 1.6, 1.6); g.fill(); }
  g.restore();
}
export function coconut(g, o = {}) {
  const { x = 0, y = 0, s = 1 } = o; g.save(); g.translate(x, y); g.scale(s, s);
  cel(g, x => ellipse(x, 0, -14, 17, 15), { fill: '#7a5230', shadow: '#4f3420', shadowFn: x => ellipse(x, 8, -6, 16, 14), lw: 2 });
  g.restore();
}
export function sapling(g, o = {}) {
  const { x = 0, y = 0, s = 1, t = 0 } = o; g.save(); g.translate(x, y); g.scale(s, s);
  const sw = Math.sin(t * 1.5) * 3;
  taperStroke(g, [[0, 0], [2, -30], [sw, -60]], 5, 3, '#6b4f2a');
  for (const sd of [-1, 1]) cel(g, x => { x.moveTo(sw, -58); x.quadraticCurveTo(sw + sd * 20, -80, sw + sd * 34, -62); x.quadraticCurveTo(sw + sd * 16, -60, sw, -58); }, { fill: PAL.palm, lw: 1.8 });
  g.restore();
}
export function palm(g, o = {}) {
  const { x = 0, y = 0, s = 1, growth = 1, sway = 0, t = 0, light } = o, L = light || L0;
  const gr = clamp(growth); if (gr <= 0) return;
  g.save(); g.translate(x, y); g.scale(s, s);
  const Ht = lerp(60, 560, gr), wob = sway * 40 + Math.sin(t * 0.9) * 6 * (0.3 + Math.abs(sway));
  const pts = [], n = 8;
  for (let i = 0; i <= n; i++) { const u = i / n; pts.push([u * u * (60 * gr + wob), -u * Ht]); }
  const top = pts[n];
  if (gr > 0.15) { const bw = lerp(8, 26, gr);
    taperStroke(g, pts, bw + 5, bw * 0.6 + 4, PAL.ink); taperStroke(g, pts, bw, bw * 0.6, mix('#9a7650', L.key, 0.1));
    g.strokeStyle = 'rgba(70,45,25,0.5)'; g.lineWidth = 2; for (let i = 1; i < 12; i++) { const u = i / 12, p = [u * u * (60 * gr + wob), -u * Ht];
      g.beginPath(); g.moveTo(p[0] - bw * 0.4, p[1]); g.lineTo(p[0] + bw * 0.4, p[1] - 3); g.stroke(); } }
  const fl = lerp(40, 230, gr), nf = 7;
  for (let i = 0; i < nf; i++) {
    const a = -Math.PI / 2 + (i - (nf - 1) / 2) * 0.48 + sway * 0.25 + Math.sin(t * 1.4 + i) * 0.05;
    const droop = 0.9 + Math.abs(i - 3) * 0.1, ex = top[0] + Math.cos(a) * fl, ey = top[1] + Math.sin(a) * fl * 0.4 + fl * 0.45 * droop * Math.abs(Math.cos(a));
    const mx = top[0] + Math.cos(a) * fl * 0.5, my = top[1] + Math.sin(a) * fl * 0.5 - 10;
    const nx = -(ey - top[1]), ny = ex - top[0], nl = Math.hypot(nx, ny) || 1, wv = fl * 0.13;
    const leaf = i % 2 ? PAL.palm : mix(PAL.palm, PAL.palmShadow, 0.5);
    cel(g, x => { x.moveTo(top[0], top[1]); x.quadraticCurveTo(mx + nx / nl * wv, my + ny / nl * wv, ex, ey); x.quadraticCurveTo(mx - nx / nl * wv * 0.3, my - ny / nl * wv * 0.3, top[0], top[1]); },
      { fill: leaf, lw: 2 });
    g.strokeStyle = rgba(PAL.palmShadow, 0.8); g.lineWidth = 1.5; g.beginPath(); g.moveTo(top[0], top[1]); g.quadraticCurveTo(mx, my, ex, ey); g.stroke();
  }
  if (gr > 0.7) for (let i = 0; i < 3; i++) coconut(g, { x: top[0] - 12 + i * 12, y: top[1] + 26, s: 0.7 });
  g.restore();
}

// ---------------------------------------------------------------- hut
export function hut(g, o = {}) {
  const { x = 0, y = 0, s = 1, build = 1, view = 'front', light } = o, L = light || L0;
  const b = clamp(build); g.save(); g.translate(x, y); g.scale(s, s);
  const W2 = view === 'side' ? 170 : 150, Hp = 150, peak = 260, wood = mix('#8a6a44', L.key, 0.1), woodS = sh('#8a6a44', L);
  g.fillStyle = 'rgba(30,20,15,0.28)'; g.beginPath(); ellipse(g, 0, 4, W2 + 30, 18); g.fill();
  const post = (px, k) => { if (k <= 0) return; const hh = Hp * k; cel(g, x => x.rect(px - 7, -hh, 14, hh), { fill: wood, shadow: woodS, shadowFn: x => x.rect(px + 2, -hh, 6, hh), lw: 2 }); };
  const kP = smoothstep(0, 0.25, b); [-W2, -W2 * 0.33, W2 * 0.33, W2].forEach((px, i) => post(px, clamp(kP * 1.6 - i * 0.2)));
  // walls (woven)
  const kW = smoothstep(0.35, 0.6, b);
  if (kW > 0) { g.save(); g.globalAlpha = kW;
    cel(g, x => { x.rect(-W2, -Hp, W2 * 2, Hp); }, { fill: mix('#c9a46a', L.key, 0.1), shadow: mix('#c9a46a', L.shadow, 0.4), shadowFn: x => x.rect(W2 * 0.3, -Hp, W2, Hp), lw: 2 });
    g.strokeStyle = 'rgba(90,60,30,0.45)'; g.lineWidth = 2; for (let yy = -Hp + 16; yy < 0; yy += 18) { g.beginPath(); g.moveTo(-W2, yy); g.lineTo(W2, yy); g.stroke(); }
    if (view === 'front') { cel(g, x => x.rect(-30, -110, 60, 110), { fill: '#3a2618', lw: 2 }); }
    g.restore(); }
  // roof frame
  const kF = smoothstep(0.2, 0.45, b);
  if (kF > 0) { const rf = (x0, y0, x1, y1) => { g.strokeStyle = PAL.ink; g.lineWidth = 9; g.lineCap = 'round'; g.beginPath(); g.moveTo(x0, y0); g.lineTo(lerp(x0, x1, kF), lerp(y0, y1, kF)); g.stroke(); g.strokeStyle = wood; g.lineWidth = 5; g.stroke(); };
    rf(-W2 - 30, -Hp + 10, 0, -peak); rf(W2 + 30, -Hp + 10, 0, -peak); rf(-W2 * 0.5, -Hp + 4, -W2 * 0.15, -peak + 30); }
  // thatch layered rows from bottom up
  const kT = smoothstep(0.55, 1, b);
  if (kT > 0) { const rows = 5;
    for (let r = 0; r < rows; r++) { const k = clamp(kT * rows - r); if (k <= 0) continue;
      const u0 = r / rows, u1 = (r + 1.25) / rows, yA = lerp(-Hp + 16, -peak, u0), yB = lerp(-Hp + 16, -peak, Math.min(1, u1));
      const wA = lerp(W2 + 44, 0, u0), wB = lerp(W2 + 44, 0, Math.min(1, u1)); const th = mix('#c8a45a', L.key, 0.12), thS = mix('#c8a45a', L.shadow, 0.45);
      g.save(); g.globalAlpha = k;
      cel(g, x => { x.moveTo(-wA, yA + 10); for (let i = 0; i <= 10; i++) x.lineTo(lerp(-wA, wA, i / 10), yA + 10 + (i % 2) * 7); x.lineTo(wB, yB); x.lineTo(-wB, yB); x.closePath(); },
        { fill: th, shadow: thS, shadowFn: x => x.rect(0, -400, 400, 420), lw: 2 });
      g.strokeStyle = 'rgba(110,80,30,0.5)'; g.lineWidth = 1.5; for (let i = -6; i <= 6; i++) { g.beginPath(); g.moveTo(i * wA / 7, yA + 10); g.lineTo(i * wB / 7, yB + 4); g.stroke(); }
      g.restore(); } }
  g.restore();
}

// ---------------------------------------------------------------- tower + beam
export function beam(g, o = {}) {
  const { x = 0, y = 0, angle = 0, length = 900, spread = 0.12, intensity = 1 } = o; if (intensity <= 0) return;
  g.save(); g.globalCompositeOperation = 'lighter'; g.translate(x, y); g.rotate(angle);
  const cone = (sp, len, a, col) => { const gr = g.createLinearGradient(0, 0, len, 0);
    gr.addColorStop(0, rgba(col, a)); gr.addColorStop(0.35, rgba(col, a * 0.45)); gr.addColorStop(1, rgba(col, 0));
    g.fillStyle = gr; g.beginPath(); g.moveTo(0, -4); g.lineTo(len, -Math.tan(sp) * len); g.quadraticCurveTo(len * 1.04, 0, len, Math.tan(sp) * len); g.lineTo(0, 4); g.closePath(); g.fill(); };
  cone(spread * 1.8, length, 0.12 * intensity, PAL.beam);
  cone(spread, length, 0.28 * intensity, PAL.beam);
  cone(spread * 0.35, length * 0.8, 0.45 * intensity, PAL.beamHot);
  g.restore();
  // flare: stronger when beam points toward camera-ish (angle near +-pi/2 down?) - simple: always + facing term
  const face = 0.5 + 0.5 * Math.abs(Math.cos(angle));
  glow(g, x, y, 90 + 120 * face, PAL.beam, 0.55 * intensity);
  glow(g, x, y, 28, PAL.beamHot, 1 * intensity);
  g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = 0.35 * intensity * face;
  const gr = g.createLinearGradient(x - 260, y, x + 260, y); gr.addColorStop(0, rgba(PAL.beam, 0)); gr.addColorStop(0.5, rgba(PAL.beamHot, 1)); gr.addColorStop(1, rgba(PAL.beam, 0));
  g.fillStyle = gr; g.fillRect(x - 260, y - 1.5, 520, 3); g.restore();
}
export function tower(g, o = {}) {
  const { x = 0, y = 0, s = 1, build = 1, lantern = 0, beamAngle = null, light, t = 0 } = o, L = light || L0;
  const b = clamp(build), rows = 14, Ht = 440, r = rng(31);
  g.save(); g.translate(x, y); g.scale(s, s);
  g.fillStyle = 'rgba(30,20,15,0.3)'; g.beginPath(); ellipse(g, 0, 4, 120, 18); g.fill();
  const shown = b * (rows + 2); const st = mix(PAL.stone, L.key, 0.12), stS = mix(PAL.rockShadow, L.shadow, 0.3);
  for (let i = 0; i < rows; i++) { const k = clamp(shown - i); const rw = lerp(105, 62, i / rows), rh = Ht / rows, y0 = -i * rh;
    const nst = 4; for (let j = 0; j < nst; j++) { const sx = -rw + (j + 0.5) * (rw * 2 / nst) + (i % 2 ? 6 : -6), sw = rw * 2 / nst * 0.55 + r() * 4, rr = r();
      if (k * nst <= j) continue;
      cel(g, x => ellipse(x, sx, y0 - rh / 2, sw, rh * 0.58), { fill: st, shadow: stS, shadowFn: x => { x.rect(sx + sw * 0.25, y0 - rh * 1.2, sw * 2, rh * 1.4); x.rect(sx - sw, y0 - rh * 0.3, sw * 2, rh); }, lw: 2 }); } }
  const lk = clamp(shown - rows), ly = -Ht - 50;
  if (lk > 0) { g.save(); g.globalAlpha = lk;
    cel(g, x => x.rect(-44, -Ht - 10, 88, 14), { fill: '#5a4636', lw: 2 });
    for (const px of [-36, 36]) cel(g, x => x.rect(px - 5, ly - 34, 10, 76), { fill: '#5a4636', lw: 2 });
    g.fillStyle = rgba('#203040', 0.55); g.fillRect(-31, ly - 34, 62, 76);
    cel(g, x => { x.moveTo(-54, ly - 32); x.lineTo(0, ly - 76); x.lineTo(54, ly - 32); x.closePath(); }, { fill: '#6b5240', shadow: '#43332a', shadowFn: x => x.rect(0, ly - 80, 60, 60), lw: 2.2 });
    g.restore(); }
  if (lantern > 0 && lk > 0) { const fl = 1 + Math.sin(t * 7) * 0.03 * lantern;
    g.fillStyle = rgba(PAL.beamHot, lantern); g.fillRect(-31, ly - 34, 62, 76);
    glow(g, 0, ly, 160 * fl, PAL.beam, 0.6 * lantern); glow(g, 0, ly, 40, PAL.beamHot, lantern);
    if (beamAngle != null) beam(g, { x: 0, y: ly, angle: beamAngle, length: 1400 / s, spread: 0.11, intensity: lantern }); }
  g.restore();
  return { lx: x, ly: y + ly * s };
}

// ---------------------------------------------------------------- boat
export function boat(g, o = {}) {
  const { x = 0, y = 0, s = 1, roll = 0, heave = 0, sail = 0, light } = o, L = light || L0;
  g.save(); g.translate(x, y + heave); g.rotate(roll); g.scale(s, s);
  const hull = mix('#7a4a2c', L.key, 0.08);
  taperStroke(g, [[10, -40], [10, -260]], 9, 6, PAL.ink); taperStroke(g, [[10, -40], [10, -260]], 6, 4, '#8a6a44');
  if (sail > 0.02) cel(g, x => { x.moveTo(16, -250); x.quadraticCurveTo(16 + 120 * sail, -150, 16, -60); x.closePath(); }, { fill: '#efe6d2', shadow: '#c8bca4', shadowFn: x => x.rect(16 + 50 * sail, -260, 200, 220), lw: 2 });
  else cel(g, x => { x.moveTo(6, -240); x.quadraticCurveTo(26, -150, 6, -70); x.lineTo(14, -70); x.quadraticCurveTo(30, -150, 14, -240); x.closePath(); }, { fill: '#e0d4bc', lw: 2 });
  g.strokeStyle = PAL.ink; g.lineWidth = 1.4; g.beginPath(); g.moveTo(10, -258); g.lineTo(-140, -18); g.moveTo(10, -258); g.lineTo(150, -18); g.stroke();
  cel(g, x => { x.moveTo(-160, -30); x.lineTo(160, -38); x.quadraticCurveTo(150, 10, 100, 18); x.lineTo(-110, 18); x.quadraticCurveTo(-150, 6, -160, -30); },
    { fill: hull, shadow: sh(hull, L), shadowFn: x => x.rect(-200, -8, 400, 40), hi: shade(hull, 0.2), hiFn: x => x.rect(-200, -36, 400, 7), lw: 2.6 });
  g.fillStyle = '#e8e0cc'; g.fillRect(-150, -24, 300, 5);
  g.restore();
}

// ---------------------------------------------------------------- small props
export function powerCell(g, o = {}) {
  const { x = 0, y = 0, s = 1, glow: gk = 1 } = o; g.save(); g.translate(x, y); g.scale(s, s);
  if (gk > 0) glow(g, 0, 0, 90, PAL.cellGlow, 0.6 * gk);
  cel(g, x => { x.roundRect(-18, -34, 36, 68, 8); }, { fill: '#3a4250', shadow: '#232a34', shadowFn: x => x.rect(4, -40, 20, 80), lw: 2.2 });
  g.fillStyle = mix('#44505e', PAL.cellGlow, gk); g.fillRect(-11, -24, 22, 48);
  if (gk > 0) { g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = rgba(PAL.hud, 0.8 * gk); g.fillRect(-3, -20, 6, 40); g.restore(); glow(g, 0, 0, 26, PAL.hud, 0.5 * gk); }
  g.fillStyle = '#9aa6b4'; g.fillRect(-8, -40, 16, 6);
  g.restore();
}
export function shellTool(g, o = {}) {
  const { x = 0, y = 0, s = 1, rot = 0 } = o; g.save(); g.translate(x, y); g.rotate(rot); g.scale(s, s);
  cel(g, x => { x.moveTo(0, 0); x.quadraticCurveTo(30, -26, 60, -6); x.quadraticCurveTo(40, 14, 0, 0); }, { fill: PAL.shell, shadow: PAL.shellShadow, shadowFn: x => x.rect(0, -2, 70, 20), lw: 2 });
  g.restore();
}
export function markerStone(g, o = {}) {
  const { x = 0, y = 0, s = 1, pole = false } = o; g.save(); g.translate(x, y); g.scale(s, s);
  if (pole) { taperStroke(g, [[0, -20], [0, -160]], 8, 6, PAL.ink); taperStroke(g, [[0, -20], [0, -160]], 5, 4, '#e8e4da'); }
  cel(g, x => splinePath(x, [[-30, 0], [-26, -26], [0, -36], [26, -24], [30, 0]], true, 0.4), { fill: '#efece4', shadow: '#b4b2ae', shadowFn: x => x.rect(6, -40, 40, 44), lw: 2.2 });
  g.restore();
}
export function gull(g, o = {}) {
  const { x = 0, y = 0, s = 1, flap = 0, facing = 1 } = o; g.save(); g.translate(x, y); g.scale(s * facing, s);
  const a = Math.sin(flap * TAU) * 0.6;
  g.strokeStyle = PAL.ink; g.lineWidth = 3; g.lineCap = 'round'; g.lineJoin = 'round';
  for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(0, 0); g.quadraticCurveTo(sd * 12, -10 - a * 14, sd * 26, -a * 22 - 2); g.stroke(); }
  g.fillStyle = '#f2f2ee'; g.beginPath(); ellipse(g, 0, 1, 6, 3.5); g.fill(); g.stroke();
  g.restore();
}
