// Core: math, keyframes, expressions, character rig, generic figures & props
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 'InterSB');
GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-SemiBoldItalic.otf', 'InterSBI');
GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 'InterB');
GlobalFonts.registerFromPath('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 'SerifB');
GlobalFonts.registerFromPath('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DV');

const W = 720, H = 1280;
const PI = Math.PI, TAU = PI * 2;
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = t => Math.pow(clamp(t), 3);
const ramp = (T, a, b) => ease((T - a) / (b - a));
function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function noise1(x, seed = 0) { const i = Math.floor(x), f = x - i; const a = hash(i + seed * 57), b = hash(i + 1 + seed * 57); return lerp(a, b, f * f * (3 - 2 * f)) * 2 - 1; }

function blendVal(a, b, t) {
  if (typeof a === 'number' && typeof b === 'number') return lerp(a, b, t);
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const o = {}; const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const k of keys) {
      if (a[k] === undefined) o[k] = b[k]; else if (b[k] === undefined) o[k] = a[k]; else o[k] = blendVal(a[k], b[k], t);
    }
    return o;
  }
  return t < 0.5 ? a : b;
}
// keyframes: [[t, value, tr?], ...] -> transition starts at t, lasts tr (default .45)
function kf(T, keys, trDef = 0.45) {
  let v = resolve(keys[0][1]);
  for (let i = 1; i < keys.length; i++) {
    const [t, val, tr] = keys[i];
    if (T < t) break;
    v = blendVal(v, resolve(val), ease((T - t) / (tr === undefined ? trDef : tr)));
  }
  return v;
}

// ---------------- expressions ----------------
const EX = {
  neutral:   { bl: 0, br: 0, bi: 0, lu: .12, ll: 0, sm: .1, mo: 0, gx: 0, gy: 0, tears: 0, blush: 0 },
  happy:     { bl: .2, br: .2, bi: .1, lu: .1, ll: .35, sm: .75 },
  joy:       { bl: .5, br: .5, bi: .2, lu: 0, ll: .5, sm: 1, mo: .25 },
  excited:   { bl: .6, br: .6, bi: 0, lu: 0, ll: .1, sm: .6 },
  sad:       { bl: -.1, br: -.1, bi: .7, lu: .35, ll: .1, sm: -.5, gy: .3 },
  grief:     { bl: 0, br: 0, bi: 1, lu: .5, ll: .25, sm: -.8, tears: 1, mo: .12 },
  angry:     { bl: -.3, br: -.3, bi: -.9, lu: .2, ll: .3, sm: -.45 },
  cold:      { bl: -.2, br: -.2, bi: -.45, lu: .45, ll: .25, sm: -.1 },
  worried:   { bl: .3, br: .3, bi: .8, lu: .05, ll: 0, sm: -.3 },
  surprised: { bl: .9, br: .9, bi: .2, lu: 0, ll: 0, sm: 0, mo: .3 },
  tender:    { bl: .15, br: .15, bi: .45, lu: .3, ll: .3, sm: .45 },
  thoughtful:{ bl: .05, br: .45, bi: -.1, lu: .3, ll: .2, sm: 0, gx: .45, gy: -.35 },
  skeptical: { bl: -.25, br: .5, bi: -.2, lu: .25, ll: .25, sm: .1 },
  ashamed:   { bl: 0, br: 0, bi: .6, lu: .55, ll: 0, sm: -.3, gy: .7 },
  hollow:    { bl: 0, br: 0, bi: .25, lu: .52, ll: 0, sm: -.25, gy: .12 },
  awe:       { bl: .6, br: .6, bi: .4, lu: 0, ll: 0, sm: .2, mo: .2 },
  pleading:  { bl: .5, br: .5, bi: 1, lu: 0, ll: 0, sm: -.35 },
  weary:     { bl: 0, br: 0, bi: .3, lu: .6, ll: .05, sm: -.3, gy: .2 },
  warm:      { bl: .2, br: .2, bi: .3, lu: .22, ll: .35, sm: .55 },
  firm:      { bl: 0, br: 0, bi: -.25, lu: .2, ll: .1, sm: 0 },
  realize:   { bl: .7, br: .7, bi: .3, lu: 0, ll: 0, sm: 0, mo: .18 },
  smirk:     { bl: 0, br: .35, bi: 0, lu: .2, ll: .3, sm: .45 },
  teary:     { bl: .1, br: .1, bi: .65, lu: .3, ll: .35, sm: .55, tears: .6 },
  proud:     { bl: .1, br: .1, bi: -.1, lu: .25, ll: .3, sm: .6 },
  jealous:   { bl: -.4, br: -.1, bi: -.7, lu: .45, ll: .4, sm: -.2, gx: -.5 },
  determined:{ bl: -.1, br: -.1, bi: -.35, lu: .25, ll: .3, sm: .2 },
  hurt:      { bl: .1, br: .1, bi: .85, lu: .25, ll: .2, sm: -.45, tears: .4 },
  peace:     { bl: .1, br: .1, bi: .2, lu: .6, ll: .2, sm: .35 },
  closed:    { bl: 0, br: 0, bi: .3, lu: 1, ll: 0, sm: -.1 },
  frantic:   { bl: .7, br: .7, bi: .5, lu: 0, ll: 0, sm: -.4, mo: .2 },
  pray:      { bl: .3, br: .3, bi: 1, lu: .7, ll: .1, sm: -.4, gy: -.6, tears: .7 },
  sheepish:  { bl: .45, br: .45, bi: .55, lu: .1, ll: .25, sm: .4 },
};
function resolve(e) {
  if (typeof e === 'string') { const [name, extra] = e.split('|'); return Object.assign({}, EX.neutral, EX[name] || {}, extra ? JSON.parse(extra) : {}); }
  if (e && e._ex) return Object.assign({}, EX.neutral, EX[e._ex] || {}, e);
  return e;
}
const ex = (name, o = {}) => Object.assign({}, EX.neutral, EX[name] || {}, o);

// ---------------- characters ----------------
const CH = {
  noa:   { skin: '#c68863', skin2: '#a96d4b', hair: '#2b1a12', hairStyle: 'curlyLong', iris: '#4a2c17', fem: true, top: '#d9a43b', top2: '#b9862a', body: 'sweater', lips: '#9c4a3f', earring: '#f2d06b' },
  teo:   { skin: '#e2b48f', skin2: '#c79670', hair: '#a9a6a1', hairStyle: 'short', beard: 'trim', beardC: '#b3afa8', iris: '#3d5a6b', glasses: true, top: '#4f6b4a', top2: '#3e553b', body: 'cardigan', shirt: '#efe6d2', brow: '#8d8a85' },
  ami:   { skin: '#8a5a3c', skin2: '#6e4530', hair: '#1c1410', hairStyle: 'short', iris: '#2a1a10', top: '#2a7f86', top2: '#1f6168', body: 'jacket', hat: 'beanie', hatC: '#b8322b', beard: 'stubble', beardC: '#2a1c14' },
  davidY:{ skin: '#d49a6a', skin2: '#b77d50', hair: '#8a3b1f', hairStyle: 'curly', iris: '#3b6b3a', top: '#c9a66b', top2: '#a8874f', body: 'robe', sash: '#a83a2c', ruddy: true },
  davidK:{ skin: '#d49a6a', skin2: '#b77d50', hair: '#8a3b1f', hairStyle: 'curly', iris: '#3b6b3a', top: '#7a2d3a', top2: '#5e1f2b', body: 'robe', sash: '#d8b04a', ruddy: true, beard: 'trim', beardC: '#7a3519', hat: 'crown' },
  davidO:{ skin: '#d8a47a', skin2: '#b9865d', hair: '#e8e4dc', hairStyle: 'bald', iris: '#3b6b3a', top: '#5b2a6e', top2: '#45205a', body: 'robe', sash: '#d8b04a', beard: 'long', beardC: '#efebe4', hat: 'crown', brow: '#d9d4cb', old: true },
  saul:  { skin: '#c89067', skin2: '#a87350', hair: '#1d1712', hairStyle: 'short', iris: '#2a1d12', top: '#4a1f24', top2: '#33151a', body: 'robe', sash: '#8a6a2a', beard: 'full', beardC: '#1d1712', hat: 'crown' },
  jonathan:{ skin: '#d39d72', skin2: '#b47f57', hair: '#5a3a22', hairStyle: 'short', iris: '#4a3320', top: '#3c5a9a', top2: '#2e4678', body: 'robe', sash: '#e0c27a', beard: 'trim', beardC: '#5a3a22' },
  abigail:{ skin: '#c8956d', skin2: '#a97953', hair: '#2b1a12', hairStyle: 'scarf', scarf: '#2f6fa3', iris: '#3a2516', fem: true, top: '#e8d8b8', top2: '#cdbb98', body: 'robe', sash: '#2f6fa3', lips: '#9a5045' },
  uriah: { skin: '#8d5a3b', skin2: '#6f432a', hair: '#1a120c', hairStyle: 'short', iris: '#22160d', top: '#9c2f25', top2: '#7a221b', body: 'robe', sash: '#c8a24a', beard: 'full', beardC: '#1a120c', hat: 'helmet' },
  solC:  { skin: '#cf9a70', skin2: '#b07d55', hair: '#2a1a10', hairStyle: 'curly', iris: '#3a2618', top: '#efe7d6', top2: '#d6cbb4', body: 'robe', sash: '#3a5f9e', child: true },
  sol:   { skin: '#cf9a70', skin2: '#b07d55', hair: '#2a1a10', hairStyle: 'short', iris: '#3a2618', top: '#1f3a6e', top2: '#162a52', body: 'robe', sash: '#e1b84c', beard: 'full', beardC: '#2a1a10', hat: 'crown', trim: '#e1b84c' },
  solO:  { skin: '#d2a07a', skin2: '#b2825c', hair: '#9d9890', hairStyle: 'short', iris: '#3a2618', top: '#1f3a6e', top2: '#162a52', body: 'robe', sash: '#b99a46', beard: 'long', beardC: '#bdb8ae', hat: 'crown', trim: '#b99a46', brow: '#8f8a82', old: true },
  jesus: { skin: '#b98258', skin2: '#9a6741', hair: '#4a2e1c', hairStyle: 'long', iris: '#3a2414', top: '#ece3d0', top2: '#d4c8b0', body: 'robe', sash: '#3d6ea8', beard: 'full', beardC: '#4a2e1c', mantle: '#3d6ea8' },
  peter: { skin: '#c48a60', skin2: '#a46e47', hair: '#6b6660', hairStyle: 'curly', iris: '#3a2a1c', top: '#7a5a3a', top2: '#5e432a', body: 'robe', sash: '#3a2a1c', beard: 'full', beardC: '#77726b' },
  rich:  { skin: '#d6a77c', skin2: '#b8885e', hair: '#2a1d14', hairStyle: 'short', iris: '#2a1d14', top: '#6a2a7a', top2: '#521f60', body: 'robe', sash: '#e1b84c', trim: '#e1b84c', beard: 'stubble', beardC: '#2a1d14' },
  disc1: { skin: '#c08559', skin2: '#9f6a43', hair: '#2a1d14', hairStyle: 'short', iris: '#2a1d14', top: '#8a6d4a', top2: '#6c5338', body: 'robe', sash: '#4a3a2a', beard: 'full', beardC: '#2a1d14' },
  disc2: { skin: '#a8714a', skin2: '#8a5a38', hair: '#140e0a', hairStyle: 'curly', iris: '#140e0a', top: '#5a7a6a', top2: '#455e52', body: 'robe', sash: '#2a3a32', beard: 'trim', beardC: '#140e0a' },
  leper: { skin: '#b89a80', skin2: '#9a7e66', hair: '#5a4a3a', hairStyle: 'short', iris: '#2a2016', top: '#8f8678', top2: '#706858', body: 'robe', sash: '#5a5248', beard: 'stubble', beardC: '#5a4a3a', bandage: true },
};

// ---------------- drawing helpers ----------------
function ell(g, x, y, rx, ry, rot = 0) { g.beginPath(); g.ellipse(x, y, Math.abs(rx), Math.abs(ry), rot, 0, TAU); }
function circ(g, x, y, r) { g.beginPath(); g.arc(x, y, Math.max(0.01, r), 0, TAU); }
function fillE(g, c, x, y, rx, ry, rot = 0) { g.fillStyle = c; ell(g, x, y, rx, ry, rot); g.fill(); }
function fillC(g, c, x, y, r) { g.fillStyle = c; circ(g, x, y, r); g.fill(); }
function rrect(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function poly(g, pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath(); }
function line(g, c, w, x1, y1, x2, y2) { g.strokeStyle = c; g.lineWidth = w; g.lineCap = 'round'; g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke(); }
function shade(hex, f) { // f<0 darker, >0 lighter
  const n = parseInt(hex.slice(1), 16); let r = n >> 16, gg = (n >> 8) & 255, b = n & 255;
  if (f < 0) { r *= 1 + f; gg *= 1 + f; b *= 1 + f; } else { r += (255 - r) * f; gg += (255 - gg) * f; b += (255 - b) * f; }
  return `rgb(${r | 0},${gg | 0},${b | 0})`;
}
function rgba(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; }
function lg(g, x1, y1, x2, y2, stops) { const gr = g.createLinearGradient(x1, y1, x2, y2); stops.forEach(([o, c]) => gr.addColorStop(o, c)); return gr; }
function rg(g, x, y, r0, r1, stops) { const gr = g.createRadialGradient(x, y, r0, x, y, r1); stops.forEach(([o, c]) => gr.addColorStop(o, c)); return gr; }
function glow(g, x, y, r, c, a = 1) { g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = a; g.fillStyle = rg(g, x, y, 0, r, [[0, c], [1, 'rgba(0,0,0,0)']]); g.fillRect(x - r, y - r, r * 2, r * 2); g.restore(); }

// ---------------- the rig ----------------
// p: {x,y (head center), s (head radius px), turn(-1..1), tilt, lean, nod, ex, talk:{o,b}, t, seed,
//     aL,aR:{s,e}, half (cut body), kneel, sit, holdL, holdR (fn(g,x,y,ang,u)), alpha, scaleX}
function blinkAmt(t, seed) {
  const period = 3.2 + hash(seed) * 2.5;
  const ph = ((t + hash(seed + 3) * 5) % period);
  const d = ph < 0.16 ? Math.sin(ph / 0.16 * PI) : 0;
  return d;
}
function drawChar(g, c, p) {
  const u = p.s, t = p.t || 0, seed = p.seed || 1;
  const e = Object.assign({}, EX.neutral, p.ex || {});
  const talk = p.talk || { o: 0, b: 0.5 };
  const breath = Math.sin(t * 1.7 + seed) * 0.018 * u;
  const idleTilt = noise1(t * 0.35, seed) * 0.035 + (p.tilt || 0) + talk.o * noise1(t * 3.3, seed + 9) * 0.05;
  const turn = clamp((p.turn || 0) + noise1(t * 0.25, seed + 4) * 0.04, -1, 1);
  const nod = (p.nod || 0) * u + talk.o * 0.04 * u * Math.sin(t * 9 + seed);
  g.save();
  g.translate(p.x, p.y);
  if (p.flip) g.scale(-1, 1);
  if (p.alpha !== undefined) g.globalAlpha = p.alpha;
  g.rotate(p.lean || 0);
  const hands = drawBody(g, c, p, u, breath);
  // head
  g.save();
  g.translate(0, u * 0.9 - breath * 0.5);
  g.rotate(idleTilt);
  g.translate(0, -u * 0.9 + nod);
  drawHead(g, c, p, u, e, talk, turn, t, seed);
  g.restore();
  // hands & props on top
  for (const h of hands) {
    if (h.prop && h.behind) continue;
    if (h.prop) h.prop(g, h.x, h.y, h.ang, u);
    if (!h.hide) { fillC(g, c.skin, h.x, h.y, u * 0.21); g.strokeStyle = c.skin2; g.lineWidth = u * 0.03; circ(g, h.x, h.y, u * 0.21); g.stroke(); }
  }
  g.restore();
}

function armPts(side, a, sx, sy, u) {
  const L1 = u * 1.25, L2 = u * 1.15;
  const t1 = a.s, t2 = a.s + a.e;
  const ex = sx + side * Math.sin(t1) * L1, ey = sy + Math.cos(t1) * L1;
  const hx = ex + side * Math.sin(t2) * L2, hy = ey + Math.cos(t2) * L2;
  return { ex, ey, hx, hy, ang: Math.atan2(hy - ey, hx - ex) };
}

function drawBody(g, c, p, u, breath) {
  const top = c.top, top2 = c.top2;
  const shY = u * 1.2 - breath, shW = c.child ? u * 0.75 : u * 0.98;
  const hem = p.kneel ? u * 3.1 : (p.h || (c.child ? 3.6 : 4.9)) * u;
  const hemW = p.kneel ? u * 1.55 : u * 1.25;
  const aL = p.aL || { s: 0.12, e: 0.15 }, aR = p.aR || { s: 0.12, e: 0.15 };
  const L = armPts(-1, aL, -shW * 0.9, shY + u * 0.15, u), R = armPts(1, aR, shW * 0.9, shY + u * 0.15, u);
  // mantle behind
  if (c.mantle) { g.fillStyle = shade(c.mantle, -0.15); poly(g, [[-shW * 1.05, shY], [shW * 1.05, shY], [hemW * 1.02, hem * 0.92], [-hemW * 1.02, hem * 0.92]]); g.fill(); }
  // long hair back behind body
  if (c.hairStyle === 'curlyLong' || c.hairStyle === 'long' || c.hairStyle === 'scarf') {
    const hc = c.hairStyle === 'scarf' ? c.scarf : c.hair;
    g.fillStyle = shade(hc, -0.1);
    if (c.hairStyle === 'curlyLong') { for (let i = 0; i < 9; i++) { const a = -0.2 + i * 0.42; fillC(g, shade(hc, -0.08), Math.cos(a + 1.2) * u * 1.05, u * 0.5 + Math.sin(a) * u * 0.35 + i % 2 * u * 0.1, u * 0.45); } }
    else { rrect(g, -u * 1.0, -u * 0.2, u * 2.0, u * (c.hairStyle === 'scarf' ? 1.9 : 1.7), u * 0.5); g.fill(); }
  }
  // neck
  g.fillStyle = c.skin2; rrect(g, -u * 0.26, u * 0.6, u * 0.52, u * 0.75, u * 0.15); g.fill();
  // torso
  g.fillStyle = top;
  g.beginPath();
  g.moveTo(-shW, shY + u * 0.25);
  g.quadraticCurveTo(-shW, shY - u * 0.05, -shW * 0.55, shY - u * 0.05);
  g.lineTo(shW * 0.55, shY - u * 0.05);
  g.quadraticCurveTo(shW, shY - u * 0.05, shW, shY + u * 0.25);
  if (p.half) { g.lineTo(shW * 1.02, u * 4.2); g.lineTo(-shW * 1.02, u * 4.2); }
  else { g.lineTo(hemW, hem); g.quadraticCurveTo(0, hem + u * 0.12, -hemW, hem); }
  g.closePath(); g.fill();
  // shading fold
  g.fillStyle = top2; g.globalAlpha *= 0.5;
  g.beginPath(); g.moveTo(shW * 0.2, shY + u * 0.6); g.lineTo(p.half ? shW * 0.5 : hemW * 0.55, p.half ? u * 4.2 : hem); g.lineTo(p.half ? shW : hemW, p.half ? u * 4.2 : hem); g.lineTo(shW, shY + u * 0.3); g.closePath(); g.fill();
  g.globalAlpha /= 0.5;
  // collar / details
  if (c.body === 'sweater') { g.fillStyle = top2; ell(g, 0, shY - u * 0.02, u * 0.38, u * 0.14); g.fill(); g.fillStyle = c.skin2; ell(g, 0, shY - u * 0.06, u * 0.27, u * 0.09); g.fill(); }
  else if (c.body === 'cardigan') {
    g.fillStyle = c.shirt; poly(g, [[-u * 0.3, shY - u * 0.05], [u * 0.3, shY - u * 0.05], [u * 0.12, u * 4.2], [-u * 0.12, u * 4.2]]); g.fill();
    g.fillStyle = top2; for (let i = 0; i < 3; i++) fillC(g, shade(top, -0.35), u * 0.2, shY + u * (0.9 + i * 0.7), u * 0.06);
  } else if (c.body === 'jacket') {
    line(g, top2, u * 0.06, 0, shY, 0, u * 4.2);
    g.fillStyle = top2; poly(g, [[-u * 0.45, shY - u * 0.1], [0, shY + u * 0.5], [u * 0.45, shY - u * 0.1]]); g.fill();
  } else {
    // robe: V neck & sash
    g.fillStyle = c.skin2; poly(g, [[-u * 0.24, shY - u * 0.06], [u * 0.24, shY - u * 0.06], [0, shY + u * 0.38]]); g.fill();
    if (c.trim) { line(g, c.trim, u * 0.07, -u * 0.26, shY - u * 0.04, 0, shY + u * 0.42); line(g, c.trim, u * 0.07, u * 0.26, shY - u * 0.04, 0, shY + u * 0.42); }
    if (c.sash && !p.half) { g.fillStyle = c.sash; poly(g, [[-shW * 1.0, u * 2.55], [shW * 1.0, u * 2.45], [shW * 1.01, u * 2.75], [-shW * 1.01, u * 2.85]]); g.fill(); }
    else if (c.sash) { g.fillStyle = c.sash; poly(g, [[-shW * 1.0, u * 2.75], [shW * 1.0, u * 2.65], [shW * 1.01, u * 2.95], [-shW * 1.01, u * 3.05]]); g.fill(); }
    if (c.trim && !p.half) { line(g, c.trim, u * 0.08, -hemW, hem, hemW, hem); }
    if (c.mantle) { g.fillStyle = c.mantle; poly(g, [[shW * 0.4, shY - u * 0.05], [shW * 1.02, shY + u * 0.2], [shW * 0.2, u * 2.5], [-shW * 0.1, u * 2.4]]); g.fill(); }
  }
  if (!p.half && !p.kneel && !p.noFeet) { fillE(g, '#4a3524', -u * 0.45, hem + u * 0.05, u * 0.32, u * 0.14); fillE(g, '#4a3524', u * 0.45, hem + u * 0.05, u * 0.32, u * 0.14); }
  // arms (sleeves)
  const hands = [];
  for (const [A, side, a, hold] of [[L, -1, aL, p.holdL], [R, 1, aR, p.holdR]]) {
    const sx = side * shW * 0.9, sy = shY + u * 0.15;
    if (hold && hold.behind) hold(g, A.hx, A.hy, A.ang, u);
    g.strokeStyle = top2; g.lineCap = 'round'; g.lineJoin = 'round'; g.lineWidth = u * 0.46;
    g.beginPath(); g.moveTo(sx, sy); g.lineTo(A.ex, A.ey); g.lineTo(A.hx - (A.hx - A.ex) * 0.12, A.hy - (A.hy - A.ey) * 0.12); g.stroke();
    g.strokeStyle = top; g.lineWidth = u * 0.36; g.stroke();
    hands.push({ x: A.hx, y: A.hy, ang: A.ang, prop: hold, behind: hold && hold.behind, hide: a.hide });
  }
  return hands;
}

function drawHead(g, c, p, u, e, talk, turn, t, seed) {
  const fx = turn * u * 0.26; // feature shift
  const rx = u * 0.9, ry = u * 1.02;
  // back hair
  hairBack(g, c, u, turn);
  // ears
  if (c.hairStyle !== 'scarf' && c.hairStyle !== 'long') {
    fillE(g, c.skin2, -rx * 0.98 + fx * 0.4, u * 0.08, u * 0.17, u * 0.24);
    fillE(g, c.skin2, rx * 0.98 + fx * 0.4, u * 0.08, u * 0.17, u * 0.24);
    if (c.earring) { fillC(g, c.earring, -rx * 0.98 + fx * 0.4, u * 0.36, u * 0.07); fillC(g, c.earring, rx * 0.98 + fx * 0.4, u * 0.36, u * 0.07); }
  }
  // face
  g.fillStyle = c.skin; ell(g, fx * 0.15, 0, rx, ry); g.fill();
  // jaw shade
  g.save(); ell(g, fx * 0.15, 0, rx, ry); g.clip();
  g.fillStyle = rgba('#000000', 0.06); ell(g, fx * 0.15 - turn * u * 0.9, 0, rx, ry * 1.1); g.fill();
  g.restore();
  // cheeks
  const blush = (c.ruddy ? 0.35 : 0.12) + (e.blush || 0) + Math.max(0, e.sm) * 0.15 + (e.tears || 0) * 0.2;
  if (blush > 0) { fillE(g, rgba('#e0605a', clamp(blush * 0.45, 0, 0.5)), -u * 0.52 + fx, u * 0.32, u * 0.2, u * 0.12); fillE(g, rgba('#e0605a', clamp(blush * 0.45, 0, 0.5)), u * 0.52 + fx, u * 0.32, u * 0.2, u * 0.12); }
  if (c.bandage) { g.save(); g.globalAlpha *= 0.7; fillE(g, '#cfc6b4', -u * 0.45, -u * 0.35, u * 0.3, u * 0.12, -0.3); fillE(g, '#9a7a68', u * 0.4, u * 0.3, u * 0.14, u * 0.1); fillE(g, '#9a7a68', -u * 0.2, u * 0.65, u * 0.09, u * 0.07); g.restore(); }
  // beard
  if (c.beard) drawBeard(g, c, u, fx, talk.o + e.mo);
  // eyes
  const blink = Math.max(blinkAmt(t, seed), p.blink || 0);
  const lu = clamp(Math.max(e.lu, blink * 1.0) + (c.old ? 0.1 : 0), 0, 1);
  const gx = clamp(e.gx + noise1(t * 0.9, seed + 20) * 0.08 + (p.gx || 0), -1, 1), gy = clamp(e.gy + noise1(t * 0.7, seed + 30) * 0.06 + (p.gy || 0), -1, 1);
  const eyeY = -u * 0.04, eyeDX = u * 0.36;
  for (const side of [-1, 1]) {
    const far = side * turn < 0 ? 1 - Math.abs(turn) * 0.25 : 1;
    drawEye(g, c, fx + side * eyeDX * (1 - Math.abs(turn) * 0.12), eyeY, u * 0.19 * far, u * (c.fem ? 0.16 : 0.145), side, lu, clamp(e.ll), gx, gy, u, e.tears || 0, t);
  }
  // brows
  const browC = c.brow || shade(c.hair, -0.1);
  for (const side of [-1, 1]) {
    const raise = (side < 0 ? e.bl : e.br) + talk.o * 0.12 * (Math.sin(t * 2.3 + seed) > 0.6 ? 1 : 0);
    const bx = fx + side * eyeDX, by = -u * 0.34 - raise * u * 0.13;
    const inner = e.bi * u * 0.15;
    const ix = bx - side * u * 0.17, ox = bx + side * u * 0.2;
    g.strokeStyle = browC; g.lineCap = 'round'; g.lineWidth = u * (c.fem ? 0.075 : 0.095);
    g.beginPath(); g.moveTo(ix, by - inner); g.quadraticCurveTo(bx, by - u * 0.06 - inner * 0.3, ox, by + u * 0.03 + inner * 0.25); g.stroke();
  }
  // nose
  g.strokeStyle = c.skin2; g.lineWidth = u * 0.055; g.lineCap = 'round';
  g.beginPath(); g.moveTo(fx * 1.2 + u * 0.02, u * 0.08); g.quadraticCurveTo(fx * 1.25 + u * 0.12 * (turn >= 0 ? 1 : -1), u * 0.28, fx * 1.1 - u * 0.02, u * 0.3); g.stroke();
  // mouth
  drawMouth(g, c, u, fx * 1.1, u * 0.52, e, talk);
  // glasses
  if (c.glasses) {
    g.strokeStyle = '#3a3330'; g.lineWidth = u * 0.045;
    for (const side of [-1, 1]) { rrect(g, fx + side * eyeDX - u * 0.25, eyeY - u * 0.19, u * 0.5, u * 0.36, u * 0.12); g.stroke(); }
    line(g, '#3a3330', u * 0.045, fx - eyeDX + u * 0.25, eyeY - u * 0.05, fx + eyeDX - u * 0.25, eyeY - u * 0.05);
    g.fillStyle = 'rgba(255,255,255,0.12)'; poly(g, [[fx - eyeDX - u * 0.15, eyeY - u * 0.15], [fx - eyeDX - u * 0.02, eyeY - u * 0.15], [fx - eyeDX - u * 0.2, eyeY + u * 0.12]]); g.fill();
  }
  hairFront(g, c, u, fx, turn);
  if (c.hat) drawHat(g, c, u, fx, p);
}

function drawEye(g, c, x, y, w, h, side, lu, ll, gx, gy, u, tears, t) {
  g.save();
  // almond shape
  g.beginPath();
  g.moveTo(x - w, y + h * 0.1);
  g.bezierCurveTo(x - w * 0.6, y - h * 1.25, x + w * 0.6, y - h * 1.25, x + w, y + h * 0.05 - side * h * 0.08);
  g.bezierCurveTo(x + w * 0.55, y + h * 1.05, x - w * 0.55, y + h * 1.05, x - w, y + h * 0.1);
  g.closePath();
  g.fillStyle = '#fbf7f0'; g.fill();
  g.clip();
  const ix = x + gx * w * 0.42, iy = y + gy * h * 0.45;
  fillC(g, c.iris, ix, iy, h * 0.82);
  fillC(g, shade(c.iris, -0.6), ix, iy, h * 0.42);
  fillC(g, 'rgba(255,255,255,0.9)', ix - h * 0.3, iy - h * 0.32, h * 0.2);
  if (tears > 0.2) fillE(g, `rgba(200,230,255,${tears * 0.45})`, x, y + h * 0.6, w * 0.9, h * 0.35);
  // lids (skin) - upper
  const top = y - h * 1.3, lidY0 = lerp(y - h * 1.1, y + h * 1.0, lu);
  g.fillStyle = c.skin;
  g.beginPath(); g.moveTo(x - w * 1.3, top - h); g.lineTo(x + w * 1.3, top - h); g.lineTo(x + w * 1.3, lidY0); g.quadraticCurveTo(x, lidY0 + h * 0.35 * (1 - lu), x - w * 1.3, lidY0); g.closePath(); g.fill();
  // lower lid
  const lowY = lerp(y + h * 1.1, y + h * 0.2, ll * 0.7);
  g.beginPath(); g.moveTo(x - w * 1.3, y + h * 2); g.lineTo(x + w * 1.3, y + h * 2); g.lineTo(x + w * 1.3, lowY); g.quadraticCurveTo(x, lowY - h * 0.25, x - w * 1.3, lowY); g.closePath(); g.fill();
  g.restore();
  // lash / lid line
  const lidY = lerp(y - h * 1.1, y + h * 1.0, lu);
  g.strokeStyle = '#2a1a14'; g.lineWidth = u * (c.fem ? 0.05 : 0.038); g.lineCap = 'round';
  g.beginPath();
  if (lu > 0.92) { g.moveTo(x - w, y + h * 0.35); g.quadraticCurveTo(x, y + h * 0.75, x + w, y + h * 0.3); }
  else {
    const yy = Math.max(lidY, y - h * 0.95);
    g.moveTo(x - w, y + h * 0.1); g.quadraticCurveTo(x - w * 0.5, Math.min(yy, y - h * 0.7), x, Math.min(yy + h * 0.1, y - h * 0.75 + (yy - (y - h * 0.95)))); g.quadraticCurveTo(x + w * 0.6, Math.min(yy, y - h * 0.7), x + w, y + h * 0.05 - side * h * 0.08);
  }
  g.stroke();
  if (c.fem && lu < 0.9) { const ox = x + side * w; line(g, '#2a1a14', u * 0.035, ox, y, ox + side * u * 0.08, y - h * 0.5); }
  // lid crease
  if (lu < 0.6) { g.strokeStyle = rgba('#000000', 0.12); g.lineWidth = u * 0.025; g.beginPath(); g.moveTo(x - w * 0.8, y - h * 1.05); g.quadraticCurveTo(x, y - h * 1.6, x + w * 0.8, y - h * 1.05); g.stroke(); }
  // tear streak
  if (tears > 0.3) {
    const k = (t * 0.6 + side * 0.3) % 1;
    g.strokeStyle = `rgba(190,225,255,${0.55 * tears})`; g.lineWidth = u * 0.05;
    g.beginPath(); g.moveTo(x + side * w * 0.3, y + h); g.quadraticCurveTo(x + side * w * 0.5, y + h + u * 0.25, x + side * w * 0.4, y + h + u * 0.25 + k * u * 0.25); g.stroke();
    fillC(g, `rgba(210,235,255,${0.8 * tears})`, x + side * w * 0.4, y + h + u * 0.28 + k * u * 0.28, u * 0.045);
  }
}

function drawMouth(g, c, u, x, y, e, talk) {
  const o = clamp(talk.o * 0.95 + (e.mo || 0), 0, 1.1);
  const b = talk.b === undefined ? 0.5 : talk.b;
  const sm = e.sm;
  const w = u * (0.24 + 0.05 * sm + (b - 0.5) * 0.1 * o - 0.06 * o * (1 - b));
  const cy = -sm * u * 0.1; // corner offset (up if smile)
  const lipC = c.lips || shade(c.skin2, -0.15);
  if (o < 0.06) {
    g.strokeStyle = lipC; g.lineWidth = u * 0.055; g.lineCap = 'round';
    g.beginPath(); g.moveTo(x - w, y + cy); g.quadraticCurveTo(x, y + sm * u * 0.09, x + w, y + cy); g.stroke();
    if (sm > 0.4) { g.lineWidth = u * 0.03; g.beginPath(); g.arc(x - w - u * 0.02, y + cy - u * 0.03, u * 0.05, 0.6, 2.2); g.stroke(); g.beginPath(); g.arc(x + w + u * 0.02, y + cy - u * 0.03, u * 0.05, 0.9, 2.5); g.stroke(); }
    return;
  }
  const drop = u * 0.26 * o;
  g.beginPath();
  g.moveTo(x - w, y + cy);
  g.quadraticCurveTo(x, y - u * 0.04 + sm * u * 0.03, x + w, y + cy);
  g.quadraticCurveTo(x + w * 0.2, y + drop + sm * u * 0.06 + u * 0.02, x, y + drop + u * 0.02 + sm * u * 0.05);
  g.quadraticCurveTo(x - w * 0.2, y + drop + sm * u * 0.06 + u * 0.02, x - w, y + cy);
  g.closePath();
  g.fillStyle = '#4a1a1c'; g.fill();
  g.save(); g.clip();
  if (o > 0.2) { g.fillStyle = '#f4efe6'; g.fillRect(x - w, y - u * 0.06, w * 2, u * 0.07 + sm * u * 0.02); }
  fillE(g, '#b55a5a', x, y + drop + u * 0.03, w * 0.6, u * 0.09);
  g.restore();
  g.strokeStyle = lipC; g.lineWidth = u * 0.045; g.stroke();
}

function drawBeard(g, c, u, fx, open) {
  const bc = c.beardC;
  const jaw = clamp(open, 0, 1) * u * 0.12;
  if (c.beard === 'stubble') {
    g.fillStyle = rgba(bc, 0.09); g.beginPath(); g.ellipse(fx * 0.3, u * 0.62 + jaw * 0.5, u * 0.62, u * 0.38, 0, 0.25, PI - 0.25); g.fill(); return;
  }
  const len = c.beard === 'long' ? u * 1.5 : c.beard === 'full' ? u * 1.12 : u * 0.98;
  const top = c.beard === 'trim' ? u * 0.25 : u * 0.12;
  g.fillStyle = bc;
  g.beginPath();
  g.moveTo(-u * 0.88 + fx * 0.2, top);
  g.quadraticCurveTo(-u * 0.92 + fx * 0.2, len * 0.8 + jaw, fx * 0.5, len + jaw);
  g.quadraticCurveTo(u * 0.92 + fx * 0.2, len * 0.8 + jaw, u * 0.88 + fx * 0.2, top);
  g.quadraticCurveTo(u * 0.72 + fx * 0.3, u * 0.4, fx + u * 0.3, u * 0.42);
  g.lineTo(fx - u * 0.3, u * 0.42);
  g.quadraticCurveTo(-u * 0.72 + fx * 0.3, u * 0.4, -u * 0.88 + fx * 0.2, top);
  g.closePath(); g.fill();
  // skin island around the mouth
  fillE(g, c.skin, fx * 1.1, u * 0.56 + jaw * 0.5, u * 0.3, u * 0.12 + jaw * 0.6);
  // moustache
  g.fillStyle = bc;
  g.beginPath(); g.moveTo(fx * 1.1 - u * 0.4, u * 0.56); g.quadraticCurveTo(fx * 1.1 - u * 0.3, u * 0.32, fx * 1.1, u * 0.36); g.quadraticCurveTo(fx * 1.1 + u * 0.3, u * 0.32, fx * 1.1 + u * 0.4, u * 0.56); g.quadraticCurveTo(fx * 1.1, u * 0.44, fx * 1.1 - u * 0.4, u * 0.56); g.fill();
  if (c.beard === 'long') { g.strokeStyle = shade(bc, -0.12); g.lineWidth = u * 0.03; for (let i = -2; i <= 2; i++) { g.beginPath(); g.moveTo(fx * 0.5 + i * u * 0.15, u * 0.85); g.lineTo(fx * 0.5 + i * u * 0.12, len * 0.95); g.stroke(); } }
}

function hairBack(g, c, u, turn) {
  const h = c.hair;
  if (c.hairStyle === 'curly' || c.hairStyle === 'curlyLong') {
    g.fillStyle = h;
    const n = c.hairStyle === 'curlyLong' ? 16 : 13;
    for (let i = 0; i < n; i++) {
      const a = PI * 1.02 + (i / (n - 1)) * PI * 0.96 + (c.hairStyle === 'curlyLong' ? -0.35 + (i / (n - 1)) * 0.7 : 0);
      const rr = c.hairStyle === 'curlyLong' ? 1.12 : 1.0;
      circ(g, Math.cos(a) * u * rr, Math.sin(a) * u * 1.04 * rr - u * 0.05, u * (c.hairStyle === 'curlyLong' ? 0.36 : 0.3)); g.fill();
    }
    if (c.hairStyle === 'curlyLong') { for (const s of [-1, 1]) for (let k = 0; k < 3; k++) fillC(g, h, s * u * 1.05, u * (0.15 + k * 0.42), u * 0.36); }
  } else if (c.hairStyle === 'short') {
    g.fillStyle = h; ell(g, 0, -u * 0.12, u * 0.98, u * 1.0); g.fill();
  } else if (c.hairStyle === 'long') {
    g.fillStyle = h; ell(g, 0, -u * 0.1, u * 1.02, u * 1.1); g.fill();
    rrect(g, -u * 1.05, -u * 0.2, u * 2.1, u * 1.5, u * 0.4); g.fill();
  } else if (c.hairStyle === 'scarf') {
    g.fillStyle = c.scarf; ell(g, 0, -u * 0.08, u * 1.12, u * 1.2); g.fill();
  } else if (c.hairStyle === 'bald') {
    g.fillStyle = c.hair; fillE(g, c.hair, -u * 0.85, u * 0.0, u * 0.25, u * 0.4); fillE(g, c.hair, u * 0.85, u * 0.0, u * 0.25, u * 0.4);
  }
}
function hairFront(g, c, u, fx, turn) {
  const h = c.hair;
  if (c.hairStyle === 'curly' || c.hairStyle === 'curlyLong') {
    g.fillStyle = h;
    for (let i = 0; i < 6; i++) { const a = PI * 1.15 + i * 0.15 * PI; circ(g, Math.cos(a) * u * 0.78 + fx * 0.3, Math.sin(a) * u * 0.86 - u * 0.05, u * 0.24); g.fill(); }
  } else if (c.hairStyle === 'short') {
    g.fillStyle = h; g.beginPath(); g.moveTo(-u * 0.92, -u * 0.05); g.quadraticCurveTo(-u * 0.95, -u * 1.15, fx * 0.3, -u * 1.05); g.quadraticCurveTo(u * 0.95, -u * 1.15, u * 0.92, -u * 0.05); g.quadraticCurveTo(u * 0.75, -u * 0.6, fx * 0.4 + u * 0.1, -u * 0.62); g.quadraticCurveTo(-u * 0.6, -u * 0.72, -u * 0.92, -u * 0.05); g.fill();
  } else if (c.hairStyle === 'long') {
    g.fillStyle = h; g.beginPath(); g.moveTo(-u * 0.95, u * 0.5); g.quadraticCurveTo(-u * 1.0, -u * 1.15, fx * 0.4, -u * 1.0); g.quadraticCurveTo(u * 1.0, -u * 1.15, u * 0.95, u * 0.5); g.lineTo(u * 0.78, u * 0.3); g.quadraticCurveTo(u * 0.75, -u * 0.6, fx * 0.4, -u * 0.72); g.quadraticCurveTo(-u * 0.75, -u * 0.6, -u * 0.78, u * 0.3); g.closePath(); g.fill();
  } else if (c.hairStyle === 'scarf') {
    g.fillStyle = c.scarf; g.beginPath(); g.moveTo(-u * 1.0, u * 0.7); g.quadraticCurveTo(-u * 1.1, -u * 1.25, fx * 0.3, -u * 1.15); g.quadraticCurveTo(u * 1.1, -u * 1.25, u * 1.0, u * 0.7); g.lineTo(u * 0.8, u * 0.5); g.quadraticCurveTo(u * 0.85, -u * 0.8, fx * 0.3, -u * 0.82); g.quadraticCurveTo(-u * 0.85, -u * 0.8, -u * 0.8, u * 0.5); g.closePath(); g.fill();
    g.fillStyle = c.hair; g.beginPath(); g.ellipse(fx * 0.3, -u * 0.72, u * 0.5, u * 0.14, 0, PI, TAU); g.fill();
  } else if (c.hairStyle === 'bald') {
    g.fillStyle = 'rgba(255,255,255,0.15)'; ell(g, -u * 0.3, -u * 0.7, u * 0.25, u * 0.12, -0.4); g.fill();
  }
}
function drawHat(g, c, u, fx, p) {
  if (c.hat === 'crown') {
    const y = -u * 0.9, w = u * 0.78;
    g.fillStyle = '#e1b84c';
    g.beginPath(); g.moveTo(-w, y + u * 0.18); g.lineTo(-w, y - u * 0.25);
    for (let i = 0; i < 5; i++) { const x0 = -w + (i + 0.5) * (2 * w / 5); g.lineTo(x0, y - u * 0.5); g.lineTo(-w + (i + 1) * (2 * w / 5), y - u * 0.2); }
    g.lineTo(w, y + u * 0.18); g.closePath(); g.fill();
    g.fillStyle = '#b8902e'; g.fillRect(-w, y + u * 0.02, w * 2, u * 0.13);
    fillC(g, '#c0303a', fx * 0.3, y - u * 0.05, u * 0.08); fillC(g, '#2f6fb0', fx * 0.3 - w * 0.55, y - u * 0.02, u * 0.06); fillC(g, '#2f6fb0', fx * 0.3 + w * 0.55, y - u * 0.02, u * 0.06);
  } else if (c.hat === 'helmet') {
    g.fillStyle = '#b5853a'; g.beginPath(); g.ellipse(0, -u * 0.45, u * 1.0, u * 0.75, 0, PI, TAU); g.fill();
    g.fillRect(-u * 1.0, -u * 0.5, u * 2.0, u * 0.22);
    g.fillStyle = '#c0302a'; g.beginPath(); g.ellipse(0, -u * 1.25, u * 0.2, u * 0.35, 0, 0, TAU); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.25)'; ell(g, -u * 0.4, -u * 0.8, u * 0.25, u * 0.1, -0.5); g.fill();
  } else if (c.hat === 'beanie') {
    g.fillStyle = c.hatC; g.beginPath(); g.ellipse(0, -u * 0.5, u * 0.98, u * 0.72, 0, PI, TAU); g.fill();
    g.fillStyle = shade(c.hatC, -0.2); rrect(g, -u * 1.0, -u * 0.62, u * 2.0, u * 0.3, u * 0.1); g.fill();
  }
}

// ---------------- generic small figures (crowds, vignettes) ----------------
// pose: {x,y(feet),s(height px),c(color),head(color),lean,arms:[aL,aR] angles from down, kneel, lie}
function fig(g, f) {
  const s = f.s, c = f.c || '#222';
  g.save(); g.translate(f.x, f.y); if (f.rot) g.rotate(f.rot); if (f.flip) g.scale(-1, 1);
  if (f.alpha !== undefined) g.globalAlpha *= f.alpha;
  const hr = s * 0.11;
  const bodyH = f.kneel ? s * 0.45 : s * 0.72;
  const lean = f.lean || 0;
  g.rotate(lean);
  g.fillStyle = c;
  poly(g, [[-s * 0.13, -bodyH], [s * 0.13, -bodyH], [s * (f.kneel ? 0.26 : 0.18), 0], [-s * (f.kneel ? 0.26 : 0.18), 0]]); g.fill();
  const arms = f.arms || [0.15, 0.15];
  g.strokeStyle = c; g.lineWidth = s * 0.07; g.lineCap = 'round';
  for (const [side, a] of [[-1, arms[0]], [1, arms[1]]]) {
    const L = s * 0.36;
    g.beginPath(); g.moveTo(side * s * 0.1, -bodyH + s * 0.04); g.lineTo(side * s * 0.1 + side * Math.sin(a) * L, -bodyH + s * 0.04 + Math.cos(a) * L); g.stroke();
  }
  fillC(g, f.head || c, 0, -bodyH - hr * 0.9, hr);
  if (f.scarf) { g.fillStyle = f.scarf; g.beginPath(); g.arc(0, -bodyH - hr * 0.9, hr * 1.15, PI * 0.9, TAU + 0.1); g.lineTo(hr * 1.2, -bodyH + hr * 0.5); g.lineTo(-hr * 1.2, -bodyH + hr * 0.5); g.fill(); }
  if (f.crown) { g.fillStyle = '#e1b84c'; poly(g, [[-hr * 0.8, -bodyH - hr * 1.6], [-hr * 0.8, -bodyH - hr * 2.4], [-hr * 0.3, -bodyH - hr * 1.9], [0, -bodyH - hr * 2.5], [hr * 0.3, -bodyH - hr * 1.9], [hr * 0.8, -bodyH - hr * 2.4], [hr * 0.8, -bodyH - hr * 1.6]]); g.fill(); }
  if (f.hairLong) { g.fillStyle = f.hairLong; g.beginPath(); g.arc(0, -bodyH - hr * 0.9, hr * 1.1, PI, TAU); g.lineTo(hr * 1.1, -bodyH + hr * 1.4); g.lineTo(-hr * 1.1, -bodyH + hr * 1.4); g.fill(); }
  g.restore();
}

// ---------------- props ----------------
const PROP = {
  lyre: (strum = 0) => (g, x, y, ang, u) => {
    g.save(); g.translate(x, y); g.rotate(-0.3);
    g.strokeStyle = '#8a5a2b'; g.lineWidth = u * 0.12; g.lineCap = 'round';
    g.beginPath(); g.moveTo(-u * 0.5, u * 0.3); g.quadraticCurveTo(-u * 0.8, -u * 0.6, -u * 0.45, -u * 1.0); g.stroke();
    g.beginPath(); g.moveTo(u * 0.5, u * 0.3); g.quadraticCurveTo(u * 0.8, -u * 0.6, u * 0.45, -u * 1.0); g.stroke();
    line(g, '#6b431f', u * 0.1, -u * 0.55, -u * 0.85, u * 0.55, -u * 0.85);
    g.fillStyle = '#a06a33'; rrect(g, -u * 0.6, u * 0.15, u * 1.2, u * 0.35, u * 0.12); g.fill();
    for (let i = 0; i < 5; i++) { const xx = -u * 0.32 + i * u * 0.16; const vib = Math.sin(strum * 40 + i) * u * 0.02 * (strum > 0 ? 1 : 0); g.strokeStyle = 'rgba(255,240,200,0.8)'; g.lineWidth = u * 0.02; g.beginPath(); g.moveTo(xx, -u * 0.85); g.quadraticCurveTo(xx + vib, -u * 0.3, xx, u * 0.2); g.stroke(); }
    g.restore();
  },
  sword: (glint = 0, ang0 = null) => (g, x, y, ang, u) => {
    g.save(); g.translate(x, y); g.rotate(ang0 === null ? ang - PI / 2 : ang0);
    g.fillStyle = '#c9ccd2'; poly(g, [[-u * 0.07, 0], [u * 0.07, 0], [u * 0.05, -u * 2.2], [0, -u * 2.45], [-u * 0.05, -u * 2.2]]); g.fill();
    line(g, '#8a6a2a', u * 0.1, -u * 0.3, 0, u * 0.3, 0);
    line(g, '#5a3a1a', u * 0.09, 0, 0, 0, u * 0.35);
    if (glint > 0) glow(g, 0, -u * 1.6, u * 0.6, '#ffffff', glint);
    g.restore();
  },
  scroll: (open = 1) => (g, x, y, ang, u) => {
    g.save(); g.translate(x, y);
    g.fillStyle = '#efe2c0'; g.fillRect(-u * 0.9 * open, -u * 0.5, u * 1.8 * open, u * 1.0);
    g.strokeStyle = 'rgba(80,60,40,0.5)'; g.lineWidth = u * 0.03;
    for (let i = 0; i < 4; i++) { g.beginPath(); g.moveTo(-u * 0.7 * open, -u * 0.3 + i * u * 0.2); g.lineTo(u * 0.7 * open, -u * 0.3 + i * u * 0.2); g.stroke(); }
    fillE(g, '#c8b48a', -u * 0.9 * open, 0, u * 0.12, u * 0.55); fillE(g, '#c8b48a', u * 0.9 * open, 0, u * 0.12, u * 0.55);
    g.restore();
  },
  letter: (seal = 1) => (g, x, y, ang, u) => {
    g.save(); g.translate(x, y - u * 0.1); g.rotate(-0.2);
    g.fillStyle = '#efe2c0'; g.fillRect(-u * 0.45, -u * 0.3, u * 0.9, u * 0.6);
    if (seal) fillC(g, '#a3191f', 0, 0, u * 0.13 * seal);
    g.restore();
  },
  bread: () => (g, x, y, ang, u) => { fillE(g, '#c58a45', x, y - u * 0.15, u * 0.45, u * 0.28); fillE(g, '#e0a862', x, y - u * 0.22, u * 0.35, u * 0.15); },
  torch: (t) => (g, x, y, ang, u) => { line(g, '#5a3a1a', u * 0.12, x, y + u * 0.3, x, y - u * 1.2); flame(g, x, y - u * 1.35, u * 0.5, t); },
  pouch: () => (g, x, y, ang, u) => { fillE(g, '#8a5a2a', x, y + u * 0.2, u * 0.35, u * 0.4); line(g, '#e1b84c', u * 0.05, x - u * 0.2, y - u * 0.1, x + u * 0.2, y - u * 0.1); fillC(g, '#e1b84c', x + u * 0.15, y + u * 0.3, u * 0.06); },
  tamb: (t) => (g, x, y, ang, u) => { g.save(); g.translate(x, y); g.rotate(Math.sin(t * 12) * 0.3); g.strokeStyle = '#a06a33'; g.lineWidth = u * 0.12; circ(g, 0, 0, u * 0.45); g.stroke(); g.fillStyle = '#f0e0c0'; circ(g, 0, 0, u * 0.4); g.fill(); for (let i = 0; i < 4; i++) fillC(g, '#e1b84c', Math.cos(i * 1.57) * u * 0.45, Math.sin(i * 1.57) * u * 0.45, u * 0.08); g.restore(); },
  quill: (t) => (g, x, y, ang, u) => { g.save(); g.translate(x, y); g.rotate(-0.6 + Math.sin(t * 6) * 0.08); g.fillStyle = '#f2efe8'; g.beginPath(); g.ellipse(0, -u * 0.7, u * 0.12, u * 0.65, 0.1, 0, TAU); g.fill(); line(g, '#555', u * 0.04, 0, 0, 0, -u * 1.2); g.restore(); },
  pot: () => (g, x, y, ang, u) => { fillE(g, '#3a3a3a', x, y - u * 0.3, u * 0.75, u * 0.55); g.fillStyle = '#4a4a4a'; g.fillRect(x - u * 0.8, y - u * 0.75, u * 1.6, u * 0.18); },
  basin: () => (g, x, y, ang, u) => { fillE(g, '#9a7a5a', x, y, u * 0.9, u * 0.35); fillE(g, '#7fb6d6', x, y - u * 0.1, u * 0.75, u * 0.2); },
  cup: () => (g, x, y, ang, u) => { g.fillStyle = '#b07a4a'; poly(g, [[x - u * 0.25, y - u * 0.5], [x + u * 0.25, y - u * 0.5], [x + u * 0.15, y], [x - u * 0.15, y]]); g.fill(); },
};

function flame(g, x, y, s, t) {
  const f = 1 + noise1(t * 8, x) * 0.15;
  glow(g, x, y, s * 3, '#ff9a3a', 0.35);
  g.fillStyle = '#ff7a1a'; g.beginPath(); g.moveTo(x - s * 0.5, y + s * 0.3); g.quadraticCurveTo(x - s * 0.5, y - s * 0.6 * f, x + noise1(t * 6, x + 1) * s * 0.2, y - s * 1.3 * f); g.quadraticCurveTo(x + s * 0.5, y - s * 0.6 * f, x + s * 0.5, y + s * 0.3); g.closePath(); g.fill();
  g.fillStyle = '#ffd25a'; g.beginPath(); g.moveTo(x - s * 0.25, y + s * 0.3); g.quadraticCurveTo(x - s * 0.25, y - s * 0.2, x, y - s * 0.7 * f); g.quadraticCurveTo(x + s * 0.25, y - s * 0.2, x + s * 0.25, y + s * 0.3); g.closePath(); g.fill();
}

module.exports = { createCanvas, W, H, PI, TAU, clamp, lerp, ease, easeOut, easeIn, ramp, hash, noise1, kf, EX, ex, resolve, CH, ell, circ, fillE, fillC, rrect, poly, line, shade, rgba, lg, rg, glow, drawChar, fig, PROP, flame, blendVal };
