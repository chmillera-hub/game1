// env.mjs - painted 90s-anime backgrounds. Every background paints the WHOLE 720x1280 frame (opaque).
//
// Common options (all functions take (g, o)):
//   o.t      seconds (animates foam/waves/cloud drift/palm sway/rain)      default 0
//   o.tod    time of day in hours, continuous (5.5 dawn, 7 morning, 12 noon, 17.5 golden, 18.7 dusk, 20.5+ night)
//   Camera / parallax (built in - do NOT also wrap in withCam unless you want a flat move):
//   o.camX, o.camY  view offset in px (+x pans right, +y pans down); far layers move less (depth 0.1..1)
//   o.zoom   push-in factor about frame center (1 = none), applied with parallax depth
//   o.cam    alternative: core-style {x,y,zoom} (x,y = world point at center, default W/2,H/2)
//   Layers are painted with ~160 px overflow, so keep |camX|,|camY| < ~150 and zoom >= 1.
//
// Exports:
//   skyAt(tod) -> {top, mid, horizon, sun, sea, seaDeep, key, shadow, dark, night, sunX, sunY01, sunUp}
//   sunPos(tod, horizonY) -> {x, y, up}       (sun arc east(right)->west(left); moon at night)
//   sky(g, o)        {tod, horizonY=560, sunX?, clouds=1 (0..1 amount), stars? (auto by tod), t}
//   sea(g, o)        {horizonY, tod, t, rough 0..1, beam? {x, a}} paints sky too unless o.noSky
//   surfClose(g, o)  {tod=5.6, t}  close wet sand, foam sheet washing in/out
//   beach(g, o)      {horizonY=520, tod, t, shoreY=horizonY+300}  sky+sea+sand+foam
//   islandWide(g, o) {tod, t, horizonY=600, hut 0..1, tower 0..1, lantern 0..1, beamAngle (rad, 0=right),
//                     palmGrowth 0..1, boats n, keeperTiny {x,y}|true, storm 0..1}
//                     anchors exported as ISLAND = {hut:[x,y], tower:[x,y], lantern:[x,y], palm:[x,y], beach:[x,y]}
//   tideline(g, o)   {tod=7.5, t}  low-angle sand, crab ground y ~ 900
//   spring(g, o)     {t}  mossy rock lip at ~ (360, 560), pool y 860-1120
//   path(g, o)       {tod=15, t}  sandy path into jungle, flat stone area ~ (360, 1000)
//   jungleEdge(g, o) {tod=10, t}  ground y > 820
//   clearing(g, o)   {tod=11, t}  grass clearing, sea beyond (horizon 470), ground y > 760
//   reef(g, o)       {tod=12, t, horizonY=260}
//   pointNight(g, o) {tod=22, t, beamAngle?, lantern 0..1}  rock top y ~ 900
//   hutDoorway(g, o) {t, flash 0..1, rain 0..1}  door opening x 170-550, y 260-1060
//   hutInterior(g, o){t, tod=10}  rear wall free area centered (360, 560)
//   palmUp(g, o)     {tod=7.5, t}  low-angle palm, crown top-center
//   stormSea(g, o)   {t, lightning 0..1, rain 0..1, roll rad}
//   reefChannel(g, o){t, beamAngle?, lightning 0..1, rain 0..1}
//   towerBase(g, o)  {tod=8, t, tower=true}  base of tower left-center, sand y > 900
//   cove(g, o)       {tod=18.9, t, beamAngle, boats=3}
// Small helpers (also exported): smallPalm, smallHut, smallTower, smallBoat, beamCone(g,x,y,angle,len,spread,a)
import { W, H, clamp, lerp, smoothstep, TAU, hash, noise1, rng, mix, rgba, shade, lit, PAL, splinePath,
  polyPath, ellipse, taperStroke, glow, vgrad, canvas, blurLayer } from './core.mjs';

const M = 160; // layer overflow
// ---------------------------------------------------------------- time of day
const KF = [
  [0, '#060c22', '#0b1430', '#1a2546', '#dfe6ff', '#0e2038', '#060f1f', '#8fa6d6', '#1a2448', 0.78],
  [4.8, '#060c22', '#0b1430', '#1a2546', '#dfe6ff', '#0e2038', '#060f1f', '#8fa6d6', '#1a2448', 0.78],
  [5.5, '#2c3566', '#b07a8c', '#ffc49a', '#ffe2b0', '#5a6f8c', '#24344f', '#ffd2a8', '#7a5a8c', 0.32],
  [7, '#4f8fc4', '#9cc4dc', '#f3dcc0', '#fff2d6', '#3d8ca0', '#1d4f6e', '#fff0dc', '#6a7d9a', 0],
  [12, '#3d86c9', '#7fb8e0', '#cfe6ef', '#ffffff', '#2c8a9c', '#173f5f', '#ffffff', '#5a7896', 0],
  [16, '#4282c2', '#8cbadb', '#e6e4d6', '#fff8e0', '#2f8696', '#183f5c', '#fff6e6', '#5f7f9a', 0],
  [17.5, '#4a78b0', '#b7b8c0', '#ffcf8a', '#fff0c0', '#3f7f8e', '#1c4058', '#ffd59a', '#5f5a80', 0.05],
  [18.7, '#2e3a6e', '#c46a6a', '#ff9a5c', '#ffd08a', '#5a5878', '#22284a', '#ffb37a', '#5b4a7a', 0.3],
  [19.6, '#141e44', '#3d3a6a', '#7a5a7c', '#ffb070', '#262e50', '#121a33', '#a49ac0', '#2a2a50', 0.6],
  [20.5, '#060c22', '#0b1430', '#1a2546', '#dfe6ff', '#0e2038', '#060f1f', '#8fa6d6', '#1a2448', 0.78],
  [24, '#060c22', '#0b1430', '#1a2546', '#dfe6ff', '#0e2038', '#060f1f', '#8fa6d6', '#1a2448', 0.78],
];
const NAMES = ['top', 'mid', 'horizon', 'sun', 'sea', 'seaDeep', 'key', 'shadow'];
export function skyAt(tod) {
  tod = ((tod % 24) + 24) % 24;
  let i = 0; while (i < KF.length - 2 && KF[i + 1][0] <= tod) i++;
  const a = KF[i], b = KF[i + 1], u = smoothstep(a[0], b[0], tod);
  const P = {}; NAMES.forEach((n, k) => P[n] = mix(a[k + 1], b[k + 1], u));
  P.dark = lerp(a[9], b[9], u);
  P.night = clamp((P.dark - 0.3) / 0.48);
  const s = sunPos(tod, 1); P.sunX = s.x; P.sunY01 = s.y; P.sunUp = s.up; P.tod = tod;
  return P;
}
export function sunPos(tod, horizonY = 560) {
  tod = ((tod % 24) + 24) % 24;
  const f = (tod - 5.7) / (19.0 - 5.7);
  if (f > -0.05 && f < 1.05) {
    return { x: lerp(W * 0.86, W * 0.12, f), y: horizonY - Math.sin(Math.PI * clamp(f, -0.05, 1.05)) * horizonY * 1.5 + horizonY * 0.04,
      up: smoothstep(-0.04, 0.03, f) * smoothstep(1.04, 0.97, f), moon: false };
  }
  return { x: W * 0.3, y: horizonY * 0.28, up: 0, moon: true };
}
// land / object color under scene light: base lit by key, darkened at night, hazed toward horizon by `haze`
function tint(base, P, haze = 0) {
  let c = lit(base, P.key, 0.55);
  c = mix(c, '#0a1226', P.dark * 0.92);
  return mix(c, P.horizon, haze * (1 - P.dark * 0.6));
}

// ---------------------------------------------------------------- camera / layer cache
function camOf(o) {
  if (o.cam) return { x: (o.cam.x ?? W / 2) - W / 2, y: (o.cam.y ?? H / 2) - H / 2, z: o.cam.zoom ?? 1 };
  return { x: o.camX ?? 0, y: o.camY ?? 0, z: o.zoom ?? 1 };
}
function L(g, o, depth, fn) {
  const c = camOf(o), z = 1 + (c.z - 1) * depth;
  g.save(); g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-W / 2 - c.x * depth, -H / 2 - c.y * depth);
  fn(g); g.restore();
}
const _keys = new Map();
// single-entry cache per slot (repaints only when key changes - safe for continuous tod time-lapses)
function slot(name, key, fn) {
  const c = canvas('env:' + name, W + 2 * M, H + 2 * M);
  if (_keys.get(name) !== key) {
    const x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W + 2 * M, H + 2 * M);
    x.translate(M, M); fn(x); _keys.set(name, key);
  }
  return c;
}
const blit = (g, c) => g.drawImage(c, -M, -M);
const todKey = (tod) => (Math.round(tod * 200) / 200).toFixed(3);
const FULL = (g, c) => { g.fillStyle = c; g.fillRect(-M, -M, W + 2 * M, H + 2 * M); };

// ---------------------------------------------------------------- sky
function paintSky(g, P, hz, stars, sunX) {
  g.fillStyle = vgrad(g, 0, -M, 0, hz, [[0, P.top], [0.55, P.mid], [1, P.horizon]]);
  g.fillRect(-M, -M, W + 2 * M, hz + M + 2);
  g.fillStyle = vgrad(g, 0, hz, 0, H + M, [[0, P.horizon], [1, P.sea]]); g.fillRect(-M, hz, W + 2 * M, H + 2 * M - hz);
  const s = sunPos(P.tod, hz); const sx = sunX ?? s.x;
  if (stars > 0) {
    const r = rng(77);
    for (let i = 0; i < 90; i++) {
      const x = r() * (W + 2 * M) - M, y = r() * (hz + M) - M, sz = r() < 0.12 ? 2.2 : 1.1;
      const a = stars * (0.35 + 0.65 * r()) * smoothstep(hz, hz * 0.55, y);
      g.fillStyle = rgba('#eef2ff', a); g.beginPath(); g.arc(x, y, sz, 0, TAU); g.fill();
    }
  }
  if (s.moon) {
    const mk = P.night;
    glow(g, sx, s.y, 120, '#9fb4e8', 0.25 * mk);
    g.fillStyle = rgba('#f1f3ff', mk); g.beginPath(); g.arc(sx, s.y, 22, 0, TAU); g.fill();
    g.fillStyle = rgba(P.top, mk * 0.9); g.beginPath(); g.arc(sx + 9, s.y - 5, 19, 0, TAU); g.fill();
  } else if (s.up > 0) {
    const low = smoothstep(hz * 0.15, hz, s.y);
    glow(g, sx, s.y, 420, P.sun, 0.35 * s.up);
    glow(g, sx, s.y, 110, '#ffffff', 0.5 * s.up);
    g.fillStyle = rgba(mix('#ffffff', P.sun, 0.5 + low * 0.5), s.up);
    g.beginPath(); g.arc(sx, s.y, 30 + low * 8, 0, TAU); g.fill();
  }
  // horizon haze band
  g.fillStyle = vgrad(g, 0, hz - 90, 0, hz, [[0, rgba(P.horizon, 0)], [1, rgba(P.horizon, 0.7)]]);
  g.fillRect(-M, hz - 90, W + 2 * M, 90);
}
function cloud(g, x, y, s, P, seed) {
  const r = rng(seed); const blobs = [];
  for (let i = 0; i < 6; i++) blobs.push([x + (r() - 0.5) * 220 * s, y - r() * 50 * s, (40 + r() * 50) * s]);
  const body = mix(mix(P.mid, '#ffffff', 0.55), P.top, P.dark * 0.6);
  const under = mix(P.shadow, P.mid, 0.4);
  const rim = mix(P.sun, '#ffffff', 0.3);
  const shape = (gg) => { for (const [bx, by, br] of blobs) { gg.moveTo(bx + br, by); gg.ellipse(bx, by, br, br * 0.62, 0, 0, TAU); }
    gg.moveTo(x + 150 * s, y + 10 * s); gg.ellipse(x, y + 10 * s, 150 * s, 26 * s, 0, 0, TAU); };
  g.save(); g.beginPath(); shape(g); g.fillStyle = body; g.globalAlpha = 0.92; g.fill(); g.clip();
  g.globalAlpha = 0.85; g.fillStyle = under; g.beginPath(); g.ellipse(x, y + 34 * s, 260 * s, 40 * s, 0, 0, TAU); g.fill();
  g.globalAlpha = 0.5 * (1 - P.night); g.fillStyle = rim; g.beginPath();
  for (const [bx, by, br] of blobs) { g.moveTo(bx + br, by - br * 0.35); g.ellipse(bx, by - br * 0.35, br * 0.8, br * 0.3, 0, 0, TAU); } g.fill();
  g.restore();
}
function clouds(g, P, hz, t, amt) {
  if (amt <= 0) return;
  const n = Math.round(2 + amt * 4);
  for (let i = 0; i < n; i++) {
    const d = 0.4 + hash(i * 3.1) * 0.6, y = hz * (0.12 + 0.7 * hash(i + 9.7));
    const span = W + 2 * M + 400;
    const x = ((hash(i + 1.3) * span + t * 6 * d) % span) - M - 200;
    cloud(g, x, y, 0.5 + d * 0.6 * (y / hz + 0.4), P, 100 + i);
  }
}
export function sky(g, o = {}) {
  const tod = o.tod ?? 12, hz = o.horizonY ?? 560, t = o.t ?? 0, P = skyAt(tod);
  const st = o.stars ?? P.night;
  L(g, o, 0.1, (g) => {
    blit(g, slot('sky', `${todKey(tod)}|${hz}|${st}|${o.sunX}`, (x) => paintSky(x, P, hz, st, o.sunX)));
    clouds(g, P, hz, t, o.clouds ?? 1);
  });
  return P;
}

// ---------------------------------------------------------------- sea
function seaBase(g, P, hz, bottom, rough = 0) {
  g.fillStyle = vgrad(g, 0, hz, 0, bottom, [[0, mix(P.sea, P.horizon, 0.5)], [0.25, P.sea], [1, mix(P.seaDeep, '#000000', rough * 0.3)]]);
  g.fillRect(-M, hz, W + 2 * M, bottom - hz);
}
function seaAnim(g, P, hz, bottom, t, rough = 0, sunX = null, beam = null) {
  const n = Math.round(26 + rough * 20);
  const light = mix(P.horizon, '#ffffff', 0.3), dark = mix(P.seaDeep, '#000000', 0.2);
  for (let i = 0; i < n; i++) {
    const d = (i + 0.5) / n, y = hz + (bottom - hz) * Math.pow(d, 1.7) + 2;
    const dir = hash(i + 3) > 0.5 ? 1 : -1, span = W + 2 * M + 200;
    const x = ((hash(i) * span + t * (6 + 22 * d) * dir) % span + span) % span - M - 100;
    const len = (24 + 130 * d) * (0.6 + hash(i + 7)), th = 0.8 + 3.2 * d * (1 + rough);
    g.fillStyle = rgba(i % 3 === 0 ? dark : light, (i % 3 === 0 ? 0.3 : 0.22) * (1 - P.night * 0.6));
    g.beginPath(); g.ellipse(x, y + Math.sin(t * 1.2 + i) * 2 * d, len, th, 0, 0, TAU); g.fill();
  }
  const s = sunPos(P.tod, hz); const sx = sunX ?? s.x;
  const k = s.moon ? P.night * 0.5 : s.up * (0.4 + 0.6 * smoothstep(hz * 0.2, hz, s.y));
  if (k > 0.01) {
    for (let j = 0; j < 16; j++) {
      const d = j / 16, y = hz + 3 + (bottom - hz) * 0.75 * d * d;
      const x = sx + noise1(j * 1.7 + t * 0.6, 4) * (4 + 50 * d);
      g.fillStyle = rgba(mix(P.sun, '#ffffff', 0.4), k * (0.75 - d * 0.5));
      g.beginPath(); g.ellipse(x, y, 10 + 60 * d * (0.5 + hash(j)), 1 + 2.5 * d, 0, 0, TAU); g.fill();
    }
  }
  if (beam) {
    const bk = beam.a ?? 1;
    for (let j = 0; j < 10; j++) {
      const d = j / 10, y = hz + 4 + (bottom - hz) * 0.6 * d * d;
      g.fillStyle = rgba(PAL.beam, bk * 0.6 * (1 - d * 0.7));
      g.beginPath(); g.ellipse(beam.x + noise1(j + t, 9) * 20 * d, y, 14 + 50 * d, 1 + 2 * d, 0, 0, TAU); g.fill();
    }
  }
}
export function sea(g, o = {}) {
  const tod = o.tod ?? 12, hz = o.horizonY ?? 560, t = o.t ?? 0, P = skyAt(tod), rough = o.rough ?? 0;
  if (!o.noSky) sky(g, o);
  L(g, o, 0.35, (g) => {
    blit(g, slot('sea', `${todKey(tod)}|${hz}|${rough}`, (x) => seaBase(x, P, hz, H + M, rough)));
    seaAnim(g, P, hz, H + M, t, rough, o.sunX, o.beam);
  });
  return P;
}

// ---------------------------------------------------------------- small props (env-scale)
export function beamCone(g, x, y, angle, len = 900, spread = 0.12, a = 1) {
  if (a <= 0) return;
  g.save(); g.globalCompositeOperation = 'lighter';
  const ex = Math.cos(angle), ey = Math.sin(angle);
  const gr = g.createLinearGradient(x, y, x + ex * len, y + ey * len);
  gr.addColorStop(0, rgba(PAL.beamHot, 0.55 * a)); gr.addColorStop(0.3, rgba(PAL.beam, 0.25 * a)); gr.addColorStop(1, rgba(PAL.beam, 0));
  g.fillStyle = gr; g.beginPath(); g.moveTo(x, y);
  g.lineTo(x + Math.cos(angle - spread) * len, y + Math.sin(angle - spread) * len);
  g.lineTo(x + Math.cos(angle + spread) * len, y + Math.sin(angle + spread) * len); g.closePath(); g.fill();
  g.restore();
  glow(g, x, y, 60, PAL.beam, 0.7 * a);
}
export function smallPalm(g, x, y, s, { growth = 1, sway = 0, color = PAL.palm, trunk = '#6b5440', lean = 0.25 } = {}) {
  if (growth <= 0.02) return;
  const h = s * 120 * growth, top = [x + lean * h + sway * 6 * s, y - h];
  taperStroke(g, [[x, y], [x + lean * h * 0.3, y - h * 0.5], top], 8 * s * (0.4 + 0.6 * growth), 3 * s, trunk);
  const fl = s * 55 * Math.sqrt(growth);
  g.fillStyle = color;
  for (let k = 0; k < 7; k++) {
    const a = -Math.PI / 2 + (k - 3) * 0.52 + sway * 0.08, ex = top[0] + Math.cos(a) * fl, ey = top[1] + Math.sin(a) * fl * 0.6 + fl * 0.35 * Math.abs(Math.cos(a));
    const nx = -Math.sin(a) * fl * 0.12, ny = Math.cos(a) * fl * 0.12;
    g.beginPath(); g.moveTo(top[0], top[1]);
    g.quadraticCurveTo((top[0] + ex) / 2 + nx, (top[1] + ey) / 2 - fl * 0.3 + ny, ex, ey);
    g.quadraticCurveTo((top[0] + ex) / 2 - nx, (top[1] + ey) / 2 - fl * 0.18 - ny, top[0], top[1]); g.fill();
  }
}
export function smallHut(g, x, y, s, build = 1, wall = '#b08a5a', roof = '#8a7a44') {
  if (build <= 0) return;
  const w = 70 * s, h = 34 * s;
  const fb = clamp(build / 0.4), rb = clamp((build - 0.4) / 0.6);
  g.fillStyle = wall;
  for (const px of [-w / 2, -w / 6, w / 6, w / 2 - 4 * s]) g.fillRect(x + px, y - h * fb, 4 * s, h * fb);
  if (build > 0.5) { g.globalAlpha = clamp((build - 0.5) * 3); g.fillRect(x - w / 2, y - h, w, h); g.fillStyle = shade(wall, -0.45); g.fillRect(x - 8 * s, y - h * 0.75, 16 * s, h * 0.75); g.globalAlpha = 1; }
  if (rb > 0) {
    g.fillStyle = roof; g.beginPath(); g.moveTo(x - w * 0.66, y - h + 2);
    g.lineTo(x, y - h - 34 * s * rb); g.lineTo(x + w * 0.66, y - h + 2); g.closePath(); g.fill();
  }
}
export function smallTower(g, x, y, s, { build = 1, lantern = 0, stone = '#a49c8e', dark = 0 } = {}) {
  if (build <= 0) return;
  const H0 = 150 * s, h = H0 * build, bw = 36 * s, tw = 22 * s;
  const sc = mix(stone, '#101830', dark * 0.85), sh = mix(shade(stone, -0.35), '#080c1c', dark * 0.85);
  g.fillStyle = sc; g.beginPath(); g.moveTo(x - bw, y); g.lineTo(x - lerp(bw, tw, build), y - h); g.lineTo(x + lerp(bw, tw, build), y - h); g.lineTo(x + bw, y); g.fill();
  g.fillStyle = sh; g.beginPath(); g.moveTo(x + bw * 0.2, y); g.lineTo(x + lerp(bw, tw, build) * 0.2, y - h); g.lineTo(x + lerp(bw, tw, build), y - h); g.lineTo(x + bw, y); g.fill();
  g.strokeStyle = rgba('#000000', 0.18); g.lineWidth = Math.max(1, s);
  for (let k = 1; k * 18 * s < h; k++) { const yy = y - k * 18 * s, ww = lerp(bw, tw, (k * 18 * s) / H0); g.beginPath(); g.moveTo(x - ww, yy); g.lineTo(x + ww, yy); g.stroke(); }
  if (build >= 0.99) {
    const ly = y - H0;
    g.fillStyle = sh; g.fillRect(x - tw * 1.1, ly - 4 * s, tw * 2.2, 5 * s);
    g.fillStyle = lantern > 0 ? mix(sh, PAL.beamHot, lantern) : mix(sh, '#9fb2c0', 0.4);
    g.fillRect(x - tw * 0.7, ly - 26 * s, tw * 1.4, 22 * s);
    g.fillStyle = sh; g.beginPath(); g.moveTo(x - tw * 0.95, ly - 26 * s); g.lineTo(x, ly - 40 * s); g.lineTo(x + tw * 0.95, ly - 26 * s); g.fill();
    if (lantern > 0) glow(g, x, ly - 15 * s, 70 * s, PAL.beam, 0.8 * lantern);
  }
}
export function towerLanternPos(x, y, s) { return [x, y - 150 * s - 15 * s]; }
export function smallBoat(g, x, y, s, { roll = 0, hull = '#7a4f34', sail = '#efe6d2', dark = 0 } = {}) {
  g.save(); g.translate(x, y); g.rotate(roll);
  g.fillStyle = mix(hull, '#0a1020', dark * 0.8); g.beginPath(); g.moveTo(-30 * s, -6 * s); g.lineTo(30 * s, -6 * s); g.lineTo(20 * s, 4 * s); g.lineTo(-22 * s, 4 * s); g.fill();
  g.fillStyle = mix(sail, '#2a3050', dark * 0.75); g.beginPath(); g.moveTo(-2 * s, -8 * s); g.lineTo(-2 * s, -46 * s); g.lineTo(20 * s, -10 * s); g.fill();
  g.restore();
}
function tinyFigure(g, x, y, s, col) {
  g.fillStyle = col; g.beginPath(); g.arc(x, y - 9 * s, 1.8 * s, 0, TAU); g.fill();
  g.fillRect(x - 1.6 * s, y - 7.5 * s, 3.2 * s, 7.5 * s);
}

// ---------------------------------------------------------------- shore foam
function foamLine(g, P, y0, t, amp = 30, period = 7, phase = 0, x0 = -M, x1 = W + M, slope = 0) {
  const s = 0.5 + 0.5 * Math.sin((t + phase) * TAU / period);
  const fc = mix(PAL.foam, P.horizon, 0.15 + P.dark * 0.3);
  const top = [], bot = [];
  for (let x = x0; x <= x1; x += 40) {
    const yy = y0 + slope * (x - W / 2) + noise1(x * 0.012 + 3, 2) * 14;
    top.push([x, yy - 8 + noise1(x * 0.03 + t * 0.4, 5) * 3]);
    bot.push([x, yy + s * amp + noise1(x * 0.02 - t * 0.3, 6) * 8 + 6]);
  }
  // wet sand darkening behind swash
  g.fillStyle = rgba(tint(PAL.sandWet, P), 0.55);
  g.beginPath(); splinePath(g, top.concat(bot.map(([x, y]) => [x, y + amp * 0.6 + 10]).reverse()), true); g.fill();
  g.fillStyle = rgba(fc, 0.88); g.beginPath(); splinePath(g, top.concat(bot.slice().reverse()), true); g.fill();
  g.fillStyle = rgba(mix(P.sea, P.horizon, 0.3), 0.45);
  g.beginPath(); splinePath(g, top.map(([x, y]) => [x, y - 18]).concat(top.slice().reverse()), true); g.fill();
}

// ---------------------------------------------------------------- surfClose (s01a)
export function surfClose(g, o = {}) {
  const tod = o.tod ?? 5.6, t = o.t ?? 0, P = skyAt(tod);
  L(g, o, 1, (g) => {
    blit(g, slot('surfClose', todKey(tod), (x) => {
      x.fillStyle = vgrad(x, 0, -M, 0, H + M, [[0, tint('#9a7c58', P)], [0.5, tint(PAL.sandWet, P)], [1, tint(PAL.sand, P)]]);
      x.fillRect(-M, -M, W + 2 * M, H + 2 * M);
      // sky reflection sheen on wet sand
      x.fillStyle = vgrad(x, 0, -M, 0, 600, [[0, rgba(P.horizon, 0.45)], [1, rgba(P.horizon, 0)]]); x.fillRect(-M, -M, W + 2 * M, 760);
      const r = rng(5);
      for (let i = 0; i < 14; i++) { const px = r() * W, py = 650 + r() * 600, sz = 4 + r() * 10;
        x.fillStyle = tint(i % 3 ? '#8a7560' : '#efe2cc', P); x.beginPath(); ellipse(x, px, py, sz, sz * 0.6, r() * 3); x.fill(); }
    }));
    // water sheet washing in from top
    const s = 0.5 + 0.5 * Math.sin(t * TAU / 6.5 - 1.2);
    const edge = 260 + s * 360;
    const pts = []; for (let x = -M; x <= W + M; x += 60) pts.push([x, edge + noise1(x * 0.01 + t * 0.15, 3) * 40]);
    g.fillStyle = vgrad(g, 0, -M, 0, edge + 40, [[0, rgba(P.sea, 0.75)], [1, rgba(mix(P.sea, P.horizon, 0.5), 0.35)]]);
    g.beginPath(); polyPath(g, [[-M, -M], [W + M, -M]].concat(pts.slice().reverse())); g.fill();
    // lace foam edge (band + a few holes)
    g.fillStyle = rgba(PAL.foam, 0.85); g.beginPath(); splinePath(g, pts.map(([x, y]) => [x, y - 22]).concat(pts.slice().reverse()), true); g.fill();
    g.fillStyle = rgba(PAL.foam, 0.45);
    for (let i = 0; i < 12; i++) { const x = hash(i) * W, y = edge - 60 - hash(i + 4) * 160 + noise1(i + t * 0.3) * 10;
      g.beginPath(); g.ellipse(x, y, 30 + hash(i + 2) * 60, 4 + hash(i + 8) * 5, 0, 0, TAU); g.fill(); }
    // retreating film trail
    g.fillStyle = rgba(P.horizon, 0.18 * (1 - s)); g.fillRect(-M, edge, W + 2 * M, 140 * (1 - s));
  });
}

// ---------------------------------------------------------------- beach
function sandPlane(g, P, y0) {
  g.fillStyle = vgrad(g, 0, y0, 0, H + M, [[0, tint(PAL.sandWet, P, 0.2)], [0.08, tint(PAL.sand, P, 0.1)], [1, tint(shade(PAL.sand, -0.05), P)]]);
  g.fillRect(-M, y0, W + 2 * M, H + M - y0);
  // soft dune swells (crisp highlight shapes)
  g.fillStyle = rgba(tint(shade(PAL.sand, 0.25), P), 0.6);
  g.beginPath(); g.ellipse(160, y0 + 380, 300, 40, -0.05, 0, TAU); g.fill();
  g.fillStyle = rgba(tint(PAL.sandShadow, P), 0.5);
  g.beginPath(); g.ellipse(560, y0 + 520, 360, 50, 0.06, 0, TAU); g.fill();
}
export function beach(g, o = {}) {
  const tod = o.tod ?? 7, hz = o.horizonY ?? 520, t = o.t ?? 0, P = skyAt(tod), shore = o.shoreY ?? hz + 300;
  sky(g, { ...o, horizonY: hz });
  L(g, o, 0.35, (g) => {
    blit(g, slot('beachSea', `${todKey(tod)}|${hz}`, (x) => seaBase(x, P, hz, shore + 60)));
    seaAnim(g, P, hz, shore, t, 0, o.sunX);
  });
  L(g, o, 0.8, (g) => {
    blit(g, slot('beachSand', `${todKey(tod)}|${shore}`, (x) => sandPlane(x, P, shore)));
    foamLine(g, P, shore - 30, t, 22, 9, 3);
    foamLine(g, P, shore, t, 50, 7);
  });
  return P;
}

// ---------------------------------------------------------------- islandWide
export const ISLAND = { hut: [250, 700], tower: [622, 712], lantern: [622, 547], palm: [312, 742], beach: [380, 772] };
function paintIsland(g, P, hz, storm) {
  const far = tint('#5f7f8f', P, 0.7);
  // far islet
  g.fillStyle = far; g.beginPath(); g.ellipse(70, hz, 120, 26, 0, Math.PI, TAU); g.fill();
  // hill / jungle mass
  const jungle = tint(PAL.jungle, P, 0.25), jungleSh = tint(shade(PAL.jungle, -0.35), P, 0.2), jungleHi = tint('#5f9a54', P, 0.25);
  const hill = [[-60, 760], [40, 700], [140, 640], [240, 560], [330, 470], [420, 440], [500, 500], [560, 600], [600, 690], [640, 760]];
  g.fillStyle = jungle; g.beginPath(); splinePath(g, hill.concat([[640, 800], [-60, 800]]), true); g.fill();
  g.save(); g.beginPath(); splinePath(g, hill.concat([[640, 800], [-60, 800]]), true); g.clip();
  const sunLeft = P.sunX < W / 2;
  g.fillStyle = jungleSh; g.beginPath(); g.ellipse(sunLeft ? 560 : 120, 680, 260, 260, 0, 0, TAU); g.fill();
  g.fillStyle = jungleHi;
  for (let i = 0; i < 9; i++) { g.beginPath(); g.ellipse(80 + i * 60, 520 + hash(i) * 150 + Math.abs(i - 5) * 25, 34, 16, 0, 0, TAU); g.fill(); }
  g.restore();
  // clearing for hut
  g.fillStyle = tint('#8aa860', P, 0.2); g.beginPath(); g.ellipse(255, 702, 70, 14, -0.15, 0, TAU); g.fill();
  // rocky point (right)
  const rock = tint(PAL.rock, P, 0.2), rockSh = tint(PAL.rockShadow, P, 0.15);
  const pt = [[540, 790], [560, 730], [600, 712], [650, 708], [700, 722], [760, 760], [770, 800]];
  g.fillStyle = rock; g.beginPath(); polyPath(g, pt); g.fill();
  g.fillStyle = rockSh; g.beginPath(); polyPath(g, [[600, 740], [650, 724], [700, 735], [760, 770], [770, 800], [580, 800]]); g.fill();
  // beach crescent
  const sand = tint(PAL.sand, P, 0.15);
  g.fillStyle = sand; g.beginPath(); splinePath(g, [[-60, 770], [120, 756], [300, 750], [460, 756], [580, 775], [600, 800], [300, 800], [-60, 800]], true); g.fill();
  g.fillStyle = tint(PAL.sandWet, P, 0.2); g.fillRect(-M, 792, W + 2 * M, 10);
  // background palms (static)
  const pc = tint(PAL.palmShadow, P, 0.2), tr = tint('#6b5440', P, 0.2);
  for (const [px, py, ps] of [[40, 760, 0.5], [90, 758, 0.6], [150, 754, 0.45], [430, 754, 0.55], [480, 757, 0.5], [530, 762, 0.42]])
    smallPalm(g, px, py, ps, { color: pc, trunk: tr, lean: px > 300 ? 0.2 : -0.2 });
  // storm darkening
  if (storm > 0) { g.fillStyle = rgba('#1a2230', storm * 0.5); g.fillRect(-M, 0, W + 2 * M, 820); }
}
export function islandWide(g, o = {}) {
  const tod = o.tod ?? 6.2, hz = o.horizonY ?? 600, t = o.t ?? 0, P = skyAt(tod), storm = o.storm ?? 0;
  sky(g, { ...o, horizonY: hz, clouds: o.clouds ?? (1 + storm) });
  if (storm > 0) L(g, o, 0.1, (g) => { g.fillStyle = rgba('#242c3a', storm * 0.6); g.fillRect(-M, -M, W + 2 * M, hz + M); });
  L(g, o, 0.4, (g) => {
    blit(g, slot('iwSea', `${todKey(tod)}|${hz}`, (x) => seaBase(x, P, hz, H + M)));
    seaAnim(g, P, hz, H + M, t, storm, o.sunX, o.lantern > 0.3 && P.dark > 0.3 ? { x: 500, a: o.lantern * 0.5 } : null);
  });
  L(g, o, 0.5, (g) => {
    blit(g, slot('island', `${todKey(tod)}|${hz}|${storm}`, (x) => { x.translate(0, hz - 600); paintIsland(x, P, 600, storm); }));
    g.save(); g.translate(0, hz - 600);
    // shoreline foam along crescent
    const fc = rgba(mix(PAL.foam, P.horizon, 0.2 + P.dark * 0.3), 0.85);
    const sw = Math.sin(t * TAU / 6) * 3;
    g.fillStyle = fc; g.beginPath(); splinePath(g, [[-60, 800 + sw], [300, 802 + sw], [600, 803 + sw], [770, 806], [770, 812], [300, 810 + sw], [-60, 808 + sw]], true); g.fill();
    const sway = Math.sin(t * 1.3) * 0.5;
    if (o.palmGrowth != null) smallPalm(g, ISLAND.palm[0], ISLAND.palm[1], 0.9, { growth: o.palmGrowth, sway, color: tint(PAL.palm, P, 0.15), trunk: tint('#7a6048', P, 0.15) });
    smallPalm(g, 380, 758, 0.6, { sway, color: tint(PAL.palm, P, 0.2), trunk: tint('#6b5440', P, 0.2), lean: 0.3 });
    if (o.hut) smallHut(g, ISLAND.hut[0], ISLAND.hut[1], 0.75, o.hut, tint('#b08a5a', P, 0.15), tint('#9a8a50', P, 0.15));
    const lan = o.lantern ?? 0;
    if (o.tower) smallTower(g, ISLAND.tower[0], ISLAND.tower[1], 1, { build: o.tower, lantern: lan, dark: P.dark });
    if (o.keeperTiny) { const k = o.keeperTiny === true ? { x: ISLAND.beach[0], y: ISLAND.beach[1] } : o.keeperTiny;
      tinyFigure(g, k.x, k.y, 1.2, tint('#2f4f5f', P, 0.1)); }
    if (o.tower >= 1 && lan > 0 && o.beamAngle != null) beamCone(g, ISLAND.lantern[0], ISLAND.lantern[1], o.beamAngle, 900, 0.1, lan * (0.4 + P.dark * 0.6));
    g.restore();
    for (let i = 0; i < (o.boats ?? 0); i++) {
      const bx = 120 + i * 150 + hash(i) * 40, by = hz + 290 + hash(i + 5) * 120 + i * 30;
      smallBoat(g, bx, by + Math.sin(t * 1.4 + i) * 2, 0.7 + (by - hz) / 900, { roll: Math.sin(t * 1.1 + i) * 0.05, dark: P.dark });
    }
  });
  return P;
}

// ---------------------------------------------------------------- tideline (crab insert)
export function tideline(g, o = {}) {
  const tod = o.tod ?? 7.5, t = o.t ?? 0, P = skyAt(tod);
  L(g, o, 0.15, (g) => blit(g, slot('tlBg', todKey(tod), (x) => {
    x.filter = 'blur(6px)';
    paintSky(x, P, 380, 0); seaBase(x, P, 380, 640);
    x.fillStyle = rgba(PAL.foam, 0.7); x.fillRect(-M, 600, W + 2 * M, 18); x.filter = 'none';
  })));
  L(g, o, 0.9, (g) => {
    blit(g, slot('tlSand', todKey(tod), (x) => {
      x.fillStyle = vgrad(x, 0, 620, 0, H + M, [[0, tint(PAL.sandWet, P)], [0.35, tint(PAL.sandWet, P)], [0.5, tint(PAL.sand, P)], [1, tint(shade(PAL.sand, 0.08), P)]]);
      x.fillRect(-M, 620, W + 2 * M, H + M);
      x.fillStyle = rgba(P.horizon, 0.25); x.fillRect(-M, 620, W + 2 * M, 120);
      const r = rng(31);
      for (let i = 0; i < 10; i++) { const px = r() * W, py = 940 + r() * 300, sz = 6 + r() * 14 * (py / 1000);
        x.fillStyle = tint(i % 2 ? '#d6c3a2' : '#f3e6d0', P); x.beginPath(); ellipse(x, px, py, sz, sz * 0.4, 0); x.fill(); }
    }));
    foamLine(g, P, 700, t, 70, 8, 0);
  });
}

// ---------------------------------------------------------------- jungle helpers
function leaf(g, x, y, len, ang, w, col) {
  const ex = x + Math.cos(ang) * len, ey = y + Math.sin(ang) * len, nx = -Math.sin(ang) * w, ny = Math.cos(ang) * w;
  g.fillStyle = col; g.beginPath(); g.moveTo(x, y);
  g.quadraticCurveTo((x + ex) / 2 + nx, (y + ey) / 2 + ny, ex, ey);
  g.quadraticCurveTo((x + ex) / 2 - nx, (y + ey) / 2 - ny, x, y); g.fill();
}
function foliageWall(g, P, y0, y1, seed, col, haze = 0, n = 26) {
  const r = rng(seed);
  g.fillStyle = tint(col, P, haze); g.fillRect(-M, y0 + 60, W + 2 * M, y1 - y0 - 60);
  for (let i = 0; i < n; i++) {
    const x = -M + r() * (W + 2 * M), y = y0 + r() * (y1 - y0) * 0.6;
    g.fillStyle = tint(i % 4 === 0 ? shade(col, 0.15) : col, P, haze);
    g.beginPath(); g.ellipse(x, y + 40, 60 + r() * 70, 50 + r() * 40, 0, 0, TAU); g.fill();
  }
}
function fronds(g, P, x, y, s, seed, col, t = 0, sway = 1) {
  const r = rng(seed);
  for (let i = 0; i < 7; i++) {
    const a = -Math.PI / 2 + (r() - 0.5) * 2.6 + Math.sin(t * 0.9 + i) * 0.03 * sway;
    leaf(g, x, y, (120 + r() * 120) * s, a, (22 + r() * 18) * s, tint(i % 2 ? col : shade(col, -0.2), P));
  }
}
function shafts(g, P, t, xs, a = 0.16) {
  g.save(); g.globalCompositeOperation = 'lighter';
  for (const [x, w] of xs) {
    const k = a * (0.8 + 0.2 * Math.sin(t * 0.5 + x));
    g.fillStyle = vgrad(g, 0, -M, 0, 1000, [[0, rgba(P.key, k)], [1, rgba(P.key, 0)]]);
    g.beginPath(); g.moveTo(x, -M); g.lineTo(x + w, -M); g.lineTo(x + w - 260, 1000); g.lineTo(x - 260 - w * 0.5, 1000); g.fill();
  }
  g.restore();
}

// ---------------------------------------------------------------- spring
export function spring(g, o = {}) {
  const t = o.t ?? 0, P = skyAt(o.tod ?? 10);
  const S = { ...P, key: mix(P.key, '#cfe8c8', 0.5) };
  L(g, o, 0.3, (g) => blit(g, slot('springBg', todKey(P.tod), (x) => {
    x.fillStyle = vgrad(x, 0, -M, 0, H, [[0, tint('#4f7d55', S)], [1, tint('#1b3528', S)]]); x.fillRect(-M, -M, W + 2 * M, H + 2 * M);
    x.filter = 'blur(4px)'; foliageWall(x, S, -100, 700, 3, '#2c5a3a', 0.15, 20); x.filter = 'none';
  })));
  L(g, o, 0.3, (g) => shafts(g, S, t, [[380, 60], [560, 40], [250, 30]]));
  L(g, o, 0.7, (g) => {
    blit(g, slot('springFg', todKey(P.tod), (x) => {
      const rock = tint('#6f6a5e', S), rockSh = tint('#3e3a34', S), moss = tint('#5f8a3e', S), mossHi = tint('#9cbf5a', S);
      // pool
      x.fillStyle = vgrad(x, 0, 820, 0, 1140, [[0, tint('#3d6e6a', S)], [1, tint('#1b3a3c', S)]]);
      x.beginPath(); x.ellipse(360, 980, 380, 170, 0, 0, TAU); x.fill();
      // rock masses with lip at (360,560)
      const rocks = [[[-M, 420], [120, 380], [250, 470], [330, 540], [380, 560], [420, 620], [360, 740], [200, 840], [-M, 900]],
        [[W + M, 380], [600, 360], [500, 460], [430, 560], [470, 700], [600, 820], [W + M, 860]],
        [[-M, 1040], [120, 1060], [230, 1150], [260, H + M], [-M, H + M]], [[W + M, 1000], [560, 1070], [470, H + M], [W + M, H + M]]];
      for (const rk of rocks) {
        x.fillStyle = rock; x.beginPath(); splinePath(x, rk, true); x.fill();
        x.save(); x.clip(); x.fillStyle = rockSh; x.beginPath(); x.ellipse(rk[3][0] + 80, rk[3][1] + 160, 260, 200, 0, 0, TAU); x.fill();
        x.fillStyle = moss; x.beginPath(); x.ellipse(rk[1][0], rk[1][1], 200, 50, 0.1, 0, TAU); x.fill();
        x.fillStyle = mossHi; x.beginPath(); x.ellipse(rk[1][0] - 20, rk[1][1] - 18, 110, 18, 0.1, 0, TAU); x.fill(); x.restore();
      }
      x.fillStyle = mossHi; x.beginPath(); x.ellipse(372, 556, 34, 8, 0.4, 0, TAU); x.fill();
    }));
    // pool ripples
    for (let i = 0; i < 4; i++) { const k = ((t * 0.35 + i / 4) % 1);
      g.strokeStyle = rgba('#d8f0e8', 0.35 * (1 - k)); g.lineWidth = 2; g.beginPath(); g.ellipse(360, 900, 30 + k * 260, 8 + k * 70, 0, 0, TAU); g.stroke(); }
    g.fillStyle = rgba('#e8fff0', 0.18); g.beginPath(); g.ellipse(280 + Math.sin(t * 0.4) * 10, 1010, 120, 10, 0, 0, TAU); g.fill();
  });
  L(g, o, 1.2, (g) => { fronds(g, S, -40, 260, 1.1, 8, '#1f4a2c', t); fronds(g, S, W + 40, 200, 1.0, 9, '#24502f', t); });
}

// ---------------------------------------------------------------- path / jungleEdge / clearing
function groundScene(g, o, name, { tod, hz, wallTop, wallBot, ground, seaBeyond = false, opening = false }) {
  const t = o.t ?? 0, P = skyAt(tod);
  sky(g, { ...o, tod, horizonY: hz, clouds: o.clouds ?? 0.6 });
  if (seaBeyond) L(g, o, 0.3, (g) => { blit(g, slot(name + 'Sea', `${todKey(tod)}|${hz}`, (x) => seaBase(x, P, hz, wallBot))); seaAnim(g, P, hz, wallBot, t, 0); });
  L(g, o, 0.5, (g) => blit(g, slot(name + 'Wall', todKey(tod), (x) => {
    if (seaBeyond) {
      foliageWall(x, P, wallTop, wallBot, 41, '#2f5d3a', 0.15, 14);
      x.save(); x.globalCompositeOperation = 'destination-out'; x.beginPath(); x.ellipse(W / 2, wallTop, 230, wallBot - wallTop + 40, 0, 0, TAU); x.fill(); x.restore();
    } else foliageWall(x, P, wallTop, wallBot, 42, '#2f5d3a', 0.1);
    if (opening) { x.fillStyle = tint('#13261a', P); x.beginPath(); x.ellipse(W / 2 + 20, wallBot - 70, 90, 120, 0, Math.PI, TAU); x.fill(); x.fillRect(W / 2 - 70, wallBot - 70, 180, 70); }
    x.fillStyle = tint('#24452e', P); x.fillRect(-M, wallBot - 10, W + 2 * M, 20);
  })));
  L(g, o, 0.85, (g) => {
    blit(g, slot(name + 'Ground', todKey(tod), (x) => {
      const gc = ground === 'grass' ? '#7f9e55' : PAL.sand;
      x.fillStyle = vgrad(x, 0, wallBot, 0, H + M, [[0, tint(shade(gc, -0.15), P)], [1, tint(shade(gc, 0.05), P)]]);
      x.fillRect(-M, wallBot, W + 2 * M, H + M - wallBot);
      if (opening) { // sandy path receding
        x.fillStyle = tint(shade(PAL.sand, 0.12), P); x.beginPath(); x.moveTo(W / 2 - 30, wallBot); x.lineTo(W / 2 + 70, wallBot);
        x.bezierCurveTo(560, 900, 700, 1100, 760, H + M); x.lineTo(20, H + M); x.bezierCurveTo(140, 1100, 330, 900, W / 2 - 30, wallBot); x.fill();
      }
      if (ground === 'grass') { x.fillStyle = tint('#a8c06a', P); for (let i = 0; i < 6; i++) { x.beginPath(); x.ellipse(hash(i) * W, wallBot + 60 + i * 80, 120, 14, 0, 0, TAU); x.fill(); } }
      x.fillStyle = rgba(tint(P.shadow, P), 0.35); x.fillRect(-M, wallBot, W + 2 * M, 50);
    }));
  });
  L(g, o, 1.2, (g) => { fronds(g, P, -60, wallBot - 40, 1.2, 50, '#24502f', t); fronds(g, P, W + 60, wallBot - 140, 1.1, 51, '#2a5a34', t); });
  return P;
}
export function path(g, o = {}) { return groundScene(g, o, 'path', { tod: o.tod ?? 15, hz: 360, wallTop: 280, wallBot: 760, ground: 'sand', opening: true }); }
export function jungleEdge(g, o = {}) { return groundScene(g, o, 'jEdge', { tod: o.tod ?? 10, hz: 320, wallTop: 220, wallBot: 820, ground: 'sand' }); }
export function clearing(g, o = {}) { return groundScene(g, o, 'clear', { tod: o.tod ?? 11, hz: 470, wallTop: 420, wallBot: 760, ground: 'grass', seaBeyond: true }); }

// ---------------------------------------------------------------- reef
export function reef(g, o = {}) {
  const tod = o.tod ?? 12, hz = o.horizonY ?? 260, t = o.t ?? 0, P = skyAt(tod);
  sky(g, { ...o, horizonY: hz, clouds: 0.5 });
  L(g, o, 0.7, (g) => {
    blit(g, slot('reef', `${todKey(tod)}|${hz}`, (x) => {
      x.fillStyle = vgrad(x, 0, hz, 0, H + M, [[0, mix(P.sea, P.horizon, 0.4)], [0.25, tint('#2aa0a8', P)], [1, tint('#62c8bc', P)]]);
      x.fillRect(-M, hz, W + 2 * M, H + M - hz);
      const r = rng(12);
      x.filter = 'blur(2px)';
      for (let i = 0; i < 26; i++) {
        const d = r(), y = hz + 120 + d * (H - hz), s = 0.3 + d * 1.2, cx = r() * (W + 200) - 100;
        const col = ['#c46a5a', '#8a6aa0', '#d49a5a', '#5a8a7a'][i % 4];
        x.fillStyle = mix(tint(col, P), mix(P.sea, P.horizon, 0.3), 0.7 - d * 0.5);
        x.beginPath();
        for (let k = 0; k < 5; k++) { const a = -Math.PI / 2 + (k - 2) * 0.45; x.moveTo(cx, y); x.lineTo(cx + Math.cos(a) * 60 * s - 8 * s, y + Math.sin(a) * 80 * s); x.lineTo(cx + Math.cos(a) * 66 * s + 8 * s, y + Math.sin(a) * 76 * s); }
        x.ellipse(cx, y, 50 * s, 18 * s, 0, 0, TAU); x.fill();
      }
      x.filter = 'none';
    }));
    // caustic bands
    g.save(); g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 9; i++) {
      const y = hz + 120 + i * 110, pts = [];
      for (let x = -M; x <= W + M; x += 90) pts.push([x, y + Math.sin(x * 0.012 + t * 0.8 + i) * 22 + noise1(x * 0.01 + t * 0.3, i) * 12]);
      g.strokeStyle = rgba('#e8fff6', 0.12 + i * 0.01); g.lineWidth = 2 + i * 0.6; g.beginPath(); splinePath(g, pts, false); g.stroke();
    }
    g.restore();
    seaAnim(g, P, hz, hz + 140, t, 0);
  });
}

// ---------------------------------------------------------------- pointNight
export function pointNight(g, o = {}) {
  const tod = o.tod ?? 22, t = o.t ?? 0, P = skyAt(tod), hz = 720, lan = o.lantern ?? 0;
  sky(g, { ...o, tod, horizonY: hz, clouds: o.clouds ?? 0.3 });
  L(g, o, 0.4, (g) => {
    blit(g, slot('pnSea', `${todKey(tod)}`, (x) => { seaBase(x, P, hz, H + M); x.fillStyle = tint('#1a2a2a', P, 0.2); x.beginPath(); x.ellipse(80, hz, 200, 70, 0, Math.PI, TAU); x.fill(); }));
    seaAnim(g, P, hz, H + M, t, 0.2, null, lan > 0 && o.beamAngle != null && Math.cos(o.beamAngle) !== 0 ? { x: W / 2 + Math.cos(o.beamAngle) * 300, a: lan * clamp(Math.sin(o.beamAngle) + 0.3) } : null);
  });
  L(g, o, 0.85, (g) => {
    blit(g, slot('pnRock', `${todKey(tod)}`, (x) => {
      const rock = tint('#5a5550', P), sh = tint('#2a2830', P), rim = mix(P.key, '#ffffff', 0.2);
      const top = [[-M, 940], [80, 905], [220, 890], [380, 896], [520, 880], [640, 900], [W + M, 930], [W + M, H + M], [-M, H + M]];
      x.fillStyle = rock; x.beginPath(); polyPath(x, top); x.fill();
      x.fillStyle = sh; x.beginPath(); polyPath(x, [[-M, 1000], [200, 960], [420, 990], [W + M, 960], [W + M, H + M], [-M, H + M]]); x.fill();
      x.strokeStyle = rgba(rim, 0.35 + P.night * 0.2); x.lineWidth = 2; x.beginPath(); polyPath(x, top.slice(0, 7), false); x.stroke();
      // foam at rock base (static spot)
    }));
    const k = 0.5 + 0.5 * Math.sin(t * 1.1);
    g.fillStyle = rgba(PAL.foam, 0.25 + 0.2 * k); g.beginPath(); g.ellipse(-20, 935, 140, 10 + 6 * k, 0, 0, TAU); g.ellipse(W + 10, 925, 120, 9 + 5 * k, 0, 0, TAU); g.fill();
  });
}

// ---------------------------------------------------------------- hut doorway / interior
const HUT_WALL = '#7a5a3a', HUT_POLE = '#a07a4a';
function rainStreaks(g, t, n, x0, y0, x1, y1, angle = 0.15, a = 0.4) {
  g.strokeStyle = rgba('#c8d8ec', a); g.lineWidth = 1.4; g.beginPath();
  for (let i = 0; i < n; i++) {
    const sp = 1400 + hash(i) * 500, len = 30 + hash(i + 2) * 40;
    const y = y0 + ((hash(i + 5) * (y1 - y0) + t * sp) % (y1 - y0 + 80)) - 40;
    const x = x0 + hash(i + 9) * (x1 - x0) + (y - y0) * angle;
    g.moveTo(x, y); g.lineTo(x + len * angle, y + len);
  }
  g.stroke();
}
export function hutDoorway(g, o = {}) {
  const t = o.t ?? 0, fl = o.flash ?? 0, rain = o.rain ?? 1;
  L(g, o, 0.3, (g) => {
    g.fillStyle = vgrad(g, 0, -M, 0, 700, [[0, mix('#0a1226', '#9ab0d0', fl)], [1, mix('#1c2a44', '#c0d0e8', fl)]]); g.fillRect(-M, -M, W + 2 * M, 700 + M);
    g.fillStyle = mix('#0e1c30', '#5a6f8c', fl * 0.7); g.fillRect(-M, 700, W + 2 * M, H);
    for (let i = 0; i < 8; i++) { g.fillStyle = rgba('#7f94b0', 0.18); g.beginPath(); g.ellipse(hash(i) * W, 720 + i * 30 + Math.sin(t + i) * 3, 60 + i * 10, 2 + i * 0.4, 0, 0, TAU); g.fill(); }
    g.fillStyle = mix('#3a3428', '#7a7060', fl * 0.6); g.fillRect(-M, 960, W + 2 * M, H); // wet sand outside
    rainStreaks(g, t, Math.round(70 * rain), 100, 200, 620, 1080, 0.12, 0.45);
  });
  L(g, o, 1, (g) => {
    blit(g, slot('hutDoor', '1', (x) => {
      x.fillStyle = HUT_WALL; x.beginPath(); x.rect(-M, -M, W + 2 * M, H + 2 * M); x.rect(550, 260, -380, 800); x.fill('evenodd');
      x.fillStyle = shade(HUT_WALL, -0.35);
      for (let i = 0; i < 12; i++) x.fillRect(-M + i * 90, -M, 10, H + 2 * M);
      x.fillStyle = HUT_POLE; x.fillRect(140, 220, 40, 860); x.fillRect(540, 220, 40, 860); x.fillRect(110, 220, 500, 44);
      x.fillStyle = shade(HUT_POLE, -0.3); x.fillRect(166, 264, 14, 816); x.fillRect(566, 264, 14, 816);
      x.fillStyle = vgrad(x, 0, 1060, 0, H + M, [[0, '#8a6a46'], [1, '#5a4430']]); x.fillRect(-M, 1060, W + 2 * M, H);
      // warm interior falloff on frame
      const gr = x.createRadialGradient(W / 2, H + 100, 50, W / 2, H + 100, 900); gr.addColorStop(0, 'rgba(255,190,120,0.35)'); gr.addColorStop(1, 'rgba(0,0,0,0.45)');
      x.fillStyle = gr; x.beginPath(); x.rect(-M, -M, W + 2 * M, H + 2 * M); x.rect(550, 260, -380, 800); x.fill('evenodd');
    }));
    // drips off the lintel
    for (let i = 0; i < 5; i++) { const k = (t * 0.8 + hash(i)) % 1; g.fillStyle = rgba('#c8d8ec', 0.7); g.beginPath(); g.ellipse(200 + i * 75, 270 + k * 700, 2, 5, 0, 0, TAU); g.fill(); }
  });
}
export function hutInterior(g, o = {}) {
  const t = o.t ?? 0, P = skyAt(o.tod ?? 10);
  L(g, o, 0.8, (g) => {
    blit(g, slot('hutIn', '1', (x) => {
      x.fillStyle = vgrad(x, 0, -M, 0, H, [[0, '#4a3424'], [0.5, '#8a6440'], [1, '#5a3e28']]); x.fillRect(-M, -M, W + 2 * M, H + 2 * M);
      for (let i = 0; i < 16; i++) { x.fillStyle = i % 2 ? '#9a7248' : '#7c5a38'; x.fillRect(-M + i * 66, -M, 58, 1100 + M); }
      x.fillStyle = rgba('#3a2818', 0.5); for (let y = 100; y < 1100; y += 140) x.fillRect(-M, y, W + 2 * M, 8);
      x.fillStyle = '#6a4a2c'; x.fillRect(-M, 1080, W + 2 * M, 40);
      x.fillStyle = vgrad(x, 0, 1100, 0, H + M, [[0, '#a07a50'], [1, '#6a4e34']]); x.fillRect(-M, 1110, W + 2 * M, H);
      const gr = x.createRadialGradient(W / 2, 560, 80, W / 2, 600, 820); gr.addColorStop(0, 'rgba(255,214,160,0.25)'); gr.addColorStop(1, 'rgba(20,10,4,0.55)');
      x.fillStyle = gr; x.fillRect(-M, -M, W + 2 * M, H + 2 * M);
    }));
  });
  // light through gaps (shafts + spots), slow drift
  g.save(); g.globalCompositeOperation = 'lighter';
  for (const [x0, w, sp] of [[120, 14, 0], [470, 10, 1], [600, 18, 2]]) {
    const dx = Math.sin(t * 0.1 + sp) * 6, k = 0.16 * (1 - P.dark);
    g.fillStyle = vgrad(g, 0, 0, 0, 1180, [[0, rgba(P.key, k)], [1, rgba(P.key, k * 0.2)]]);
    g.beginPath(); g.moveTo(x0 + dx, 0); g.lineTo(x0 + w + dx, 0); g.lineTo(x0 - 160 + w * 3 + dx, 1180); g.lineTo(x0 - 160 + dx, 1180); g.fill();
    g.fillStyle = rgba(P.key, k * 1.6); g.beginPath(); g.ellipse(x0 - 120 + w + dx, 1170, 50, 9, 0, 0, TAU); g.fill();
  }
  g.restore();
}

// ---------------------------------------------------------------- palmUp
export function palmUp(g, o = {}) {
  const tod = o.tod ?? 7.5, t = o.t ?? 0, P = skyAt(tod);
  sky(g, { ...o, tod, horizonY: 1300, clouds: 0.8 });
  L(g, o, 0.6, (g) => {
    fronds(g, P, -80, 1300, 1.6, 60, '#2f6a3c', t); fronds(g, P, W + 80, 1320, 1.5, 61, '#2c623a', t);
  });
  L(g, o, 0.9, (g) => {
    const sw = Math.sin(t * 0.7) * 10, top = [400 + sw, 230];
    const tr = tint('#8a6e50', P), trSh = tint('#5a4634', P);
    taperStroke(g, [[300, H + 60], [330, 900], [370, 520], top], 110, 34, tr);
    taperStroke(g, [[340, H + 60], [360, 900], [390, 520], [top[0] + 8, top[1]]], 50, 14, trSh);
    g.strokeStyle = rgba('#3a2a1e', 0.35); g.lineWidth = 3;
    for (let k = 0; k < 14; k++) { const u = k / 14, y = lerp(1250, 260, u), x = lerp(300, top[0], u * u * 0.6 + u * 0.4), w = lerp(52, 16, u);
      g.beginPath(); g.moveTo(x - w, y); g.quadraticCurveTo(x, y + 10, x + w, y - 4); g.stroke(); }
    const col = tint(PAL.palm, P), colSh = tint(PAL.palmShadow, P);
    for (let k = 0; k < 9; k++) {
      const a = k / 9 * TAU + Math.sin(t * 0.9 + k) * 0.05, len = 300 + hash(k) * 80;
      leaf(g, top[0], top[1], len, a, 46, k % 2 ? col : colSh);
      g.strokeStyle = rgba(mix(P.key, '#ffffff', 0.3), 0.4); g.lineWidth = 2; g.beginPath(); g.moveTo(top[0], top[1]); g.lineTo(top[0] + Math.cos(a) * len, top[1] + Math.sin(a) * len); g.stroke();
    }
    g.fillStyle = tint('#5a4430', P); for (let k = 0; k < 4; k++) { g.beginPath(); g.arc(top[0] - 24 + k * 16, top[1] + 22 + (k % 2) * 8, 13, 0, TAU); g.fill(); }
  });
}

// ---------------------------------------------------------------- storms
function lightningBolt(g, k, seed, x0, y1) {
  if (k <= 0.05) return;
  const r = rng(seed); const pts = [[x0, -20]]; let x = x0;
  for (let y = 0; y < y1; y += 50) { x += (r() - 0.5) * 80; pts.push([x, y]); }
  g.strokeStyle = rgba('#eef4ff', k); g.lineWidth = 3; g.beginPath(); polyPath(g, pts, false); g.stroke();
  glow(g, x0, 120, 400, '#cfe6ff', 0.4 * k);
}
function stormSky(g, o, hz, fl) {
  L(g, o, 0.1, (g) => {
    g.fillStyle = vgrad(g, 0, -M, 0, hz, [[0, mix('#0d1420', '#8aa0c0', fl)], [1, mix('#2a3646', '#c0d0e0', fl)]]); g.fillRect(-M, -M, W + 2 * M, hz + M + 40);
    const t = o.t ?? 0;
    for (let i = 0; i < 7; i++) { g.fillStyle = mix(i % 2 ? '#1a2230' : '#242e3e', '#9aaec8', fl * 0.8);
      g.beginPath(); g.ellipse(((hash(i) * 1000 + t * 20) % 1100) - 200, 80 + i * hz / 8, 260, 70, 0, 0, TAU); g.fill(); }
  });
}
function waveLayer(g, base, crestY, amp, wl, speed, t, col, foamCol, phase = 0, bottom = H + M) {
  const pts = [];
  for (let x = -M; x <= W + M; x += 30) {
    const u = (x + t * speed) / wl * TAU + phase;
    pts.push([x, crestY - amp * Math.pow(0.5 + 0.5 * Math.sin(u), 2) + noise1(x * 0.01 + t * 0.2, phase * 3) * amp * 0.25]);
  }
  g.fillStyle = col; g.beginPath(); polyPath(g, pts.concat([[W + M, bottom], [-M, bottom]])); g.fill();
  g.fillStyle = foamCol; g.beginPath(); polyPath(g, pts.concat(pts.map(([x, y]) => [x, y + 10 + amp * 0.06]).reverse())); g.fill();
}
export function stormSea(g, o = {}) {
  const t = o.t ?? 0, fl = o.lightning ?? 0, hz = 520;
  g.save(); if (o.roll) { g.translate(W / 2, H / 2); g.rotate(o.roll); g.translate(-W / 2, -H / 2); }
  stormSky(g, o, hz + 200, fl);
  L(g, o, 0.2, (g) => lightningBolt(g, fl, Math.floor(t), 200 + hash(Math.floor(t)) * 300, hz));
  L(g, o, 0.5, (g) => {
    const f = (c) => mix(c, '#9ab0c8', fl * 0.6);
    waveLayer(g, 0, hz, 60, 420, 60, t, f('#1a2a3a'), rgba('#9ab0c0', 0.35), 0);
    waveLayer(g, 0, hz + 260, 180, 640, 90, t, f('#142434'), rgba('#c8d8e4', 0.55), 1.3);
  });
  L(g, o, 0.9, (g) => waveLayer(g, 0, 1080, 260, 900, 120, t, mix('#0e1a28', '#8aa0b8', fl * 0.5), rgba('#e0ecf4', 0.7), 2.1));
  g.restore();
  if ((o.rain ?? 1) > 0) rainStreaks(g, t, Math.round(110 * (o.rain ?? 1)), -100, -50, W, H, 0.22, 0.35);
}
export function reefChannel(g, o = {}) {
  const t = o.t ?? 0, fl = o.lightning ?? 0, hz = 560;
  stormSky(g, o, hz, fl);
  L(g, o, 0.15, (g) => { if (o.beamAngle != null) beamCone(g, 120, 300, o.beamAngle, 1100, 0.09, 0.9); glow(g, 120, 300, 40, PAL.beam, 0.9); });
  L(g, o, 0.45, (g) => {
    waveLayer(g, 0, hz + 30, 30, 300, 40, t, mix('#16263a', '#8aa0b8', fl * 0.5), rgba('#9ab0c0', 0.3), 0);
    waveLayer(g, 0, hz + 260, 70, 420, 50, t, mix('#122032', '#8aa0b8', fl * 0.5), rgba('#c0d0dc', 0.4), 1.7);
  });
  L(g, o, 0.85, (g) => {
    blit(g, slot('rcRocks', '1', (x) => {
      const rk = '#1e242c', rim = '#5a6a7a';
      const left = [[-M, 560], [60, 600], [120, 680], [90, 760], [200, 860], [160, 1000], [260, 1100], [220, H + M], [-M, H + M]];
      const right = [[W + M, 600], [640, 640], [600, 720], [660, 800], [540, 900], [580, 1020], [500, 1120], [540, H + M], [W + M, H + M]];
      for (const p of [left, right]) { x.fillStyle = rk; x.beginPath(); polyPath(x, p); x.fill(); x.strokeStyle = rgba(rim, 0.6); x.lineWidth = 2; x.beginPath(); polyPath(x, p.slice(0, -2), false); x.stroke(); }
      // white marker stones + pole
      x.fillStyle = '#e8e6e0'; for (const [mx, my] of [[150, 676], [182, 852], [618, 716], [560, 896], [228, 1094]]) { x.beginPath(); x.ellipse(mx, my, 16, 11, 0, 0, TAU); x.fill(); }
      x.fillStyle = '#d8d4cc'; x.fillRect(610, 560, 8, 160); x.fillStyle = '#ffffff'; x.fillRect(604, 556, 20, 26);
    }));
    const k = 0.5 + 0.5 * Math.sin(t * 2);
    g.fillStyle = rgba('#e0ecf4', 0.35 + 0.3 * k);
    for (const [fx, fy] of [[200, 870], [160, 1010], [540, 910], [580, 1030], [600, 730]]) { g.beginPath(); g.ellipse(fx, fy, 40 + 20 * k, 7, 0, 0, TAU); g.fill(); }
  });
  if ((o.rain ?? 1) > 0) rainStreaks(g, t, Math.round(100 * (o.rain ?? 1)), -100, -50, W, H, 0.2, 0.32);
}

// ---------------------------------------------------------------- towerBase
export function towerBase(g, o = {}) {
  const tod = o.tod ?? 8, t = o.t ?? 0, P = skyAt(tod), hz = 640;
  sky(g, { ...o, tod, horizonY: hz, clouds: 0.7 });
  L(g, o, 0.35, (g) => { blit(g, slot('tbSea', todKey(tod), (x) => seaBase(x, P, hz, 900))); seaAnim(g, P, hz, 900, t, 0); });
  L(g, o, 0.8, (g) => {
    blit(g, slot('tbSand', todKey(tod) + (o.tower === false), (x) => {
      sandPlane(x, P, 880);
      if (o.tower !== false) {
        const st = tint(PAL.stone, P), sh = tint(shade(PAL.stone, -0.4), P), lightLeft = P.sunX < W / 2;
        for (let row = 0; row < 16; row++) {
          const y = 900 - row * 62, half = 210 - row * 5, off = row % 2 ? 50 : 0, cx = 220;
          for (let bx = cx - half - off; bx < cx + half; bx += 100) {
            const l = Math.max(bx, cx - half), r = Math.min(bx + 96, cx + half); if (r - l < 20) continue;
            const u = ((l + r) / 2 - (cx - half)) / (2 * half);
            x.fillStyle = (lightLeft ? u > 0.62 : u < 0.38) ? sh : st;
            x.beginPath(); x.roundRect(l, y - 58, r - l, 56, 12); x.fill();
          }
        }
        x.fillStyle = rgba(tint(P.shadow, P), 0.5); x.beginPath(); x.ellipse(lightLeft ? 420 : 100, 920, 280, 40, 0, 0, TAU); x.fill();
      }
    }));
    foamLine(g, P, 870, t, 20, 8);
  });
}

// ---------------------------------------------------------------- cove (epilogue)
export function cove(g, o = {}) {
  const tod = o.tod ?? 18.9, t = o.t ?? 0, P = skyAt(tod), hz = 520;
  sky(g, { ...o, tod, horizonY: hz, clouds: 0.8 });
  L(g, o, 0.4, (g) => {
    blit(g, slot('coveSea', todKey(tod), (x) => seaBase(x, P, hz, H + M)));
    seaAnim(g, P, hz, H + M, t, 0, null, { x: 520, a: 0.4 });
  });
  L(g, o, 0.6, (g) => {
    blit(g, slot('coveLand', todKey(tod), (x) => {
      const rock = tint(PAL.rock, P, 0.1), jung = tint(PAL.jungle, P, 0.1), sand = tint(PAL.sand, P, 0.1);
      // right headland with tower point
      x.fillStyle = jung; x.beginPath(); splinePath(x, [[W + M, 380], [640, 420], [560, 520], [520, 600], [600, 640], [W + M, 650]], true); x.fill();
      x.fillStyle = rock; x.beginPath(); polyPath(x, [[470, 610], [520, 560], [600, 548], [W + M, 560], [W + M, 680], [460, 660]]); x.fill();
      // left slope with gardens
      x.fillStyle = jung; x.beginPath(); splinePath(x, [[-M, 560], [80, 600], [200, 700], [300, 860], [260, 1000], [-M, 1080]], true); x.fill();
      x.fillStyle = sand; x.beginPath(); splinePath(x, [[-M, 1000], [180, 960], [300, 880], [380, 1000], [300, 1160], [-M, 1240]], true); x.fill();
      for (let r = 0; r < 4; r++) for (let c = 0; c < 5; c++) { x.fillStyle = tint(r % 2 ? '#7aa04a' : '#a8b84a', P); x.beginPath(); x.ellipse(20 + c * 38 + r * 14, 760 + r * 40, 14, 6, 0, 0, TAU); x.fill(); }
      for (const [px, py, s] of [[230, 900, 0.8], [140, 990, 1.0], [600, 610, 0.6]]) smallPalm(x, px, py, s, { color: tint(PAL.palmShadow, P), trunk: tint('#5a4636', P) });
      smallTower(x, 620, 560, 0.9, { lantern: 0, dark: P.dark });
    }));
    const lp = towerLanternPos(620, 560, 0.9);
    glow(g, lp[0], lp[1], 70, PAL.beam, 0.9);
    if (o.beamAngle != null) beamCone(g, lp[0], lp[1], o.beamAngle, 1000, 0.08, 0.8);
  });
  L(g, o, 0.85, (g) => {
    for (let i = 0; i < (o.boats ?? 3); i++) {
      const bx = 380 + i * 100, by = 760 + i * 70 + hash(i) * 40;
      smallBoat(g, bx, by + Math.sin(t * 1.2 + i) * 3, 1 + i * 0.25, { roll: Math.sin(t + i * 2) * 0.05, dark: P.dark * 0.8 });
      g.fillStyle = rgba(mix(P.sun, '#ffffff', 0.3), 0.25); g.beginPath(); g.ellipse(bx, by + 8, 34 + i * 8, 3, 0, 0, TAU); g.fill();
    }
  });
}
