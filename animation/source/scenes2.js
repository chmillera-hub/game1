const C = require('./core');
const { W, H, PI, TAU, clamp, lerp, ease, easeOut, ramp, hash, noise1, kf, ex, CH, ell, circ, fillE, fillC, rrect, poly, line, shade, rgba, lg, rg, glow, drawChar, fig, PROP, flame } = C;
const S_ = require('./scenes');
const { cam, actor, A, REST, TABLE, sky, vignette, tint, hills, stars, sheep, petals, smoke, house, txt, braid, kitchenScene } = S_._h;

const V = (base, o) => Object.assign({}, CH[base], o);
const davidLinen = V('davidY', { top: '#f3efe6', top2: '#d8d2c4', sash: '#c8a24a' });
const davidMid = V('davidK', { hair: '#7a3a22', beardC: '#6a4a3a' });
const bathsheba = V('abigail', { scarf: '#7a2a4a', top: '#d9c3a3', top2: '#bba582', sash: '#7a2a4a' });
const woman1 = V('abigail', { scarf: '#d8572a', top: '#f2e2c2', sash: '#d8572a' });
const woman2 = V('abigail', { scarf: '#8a3a9a', top: '#e8d0a8', sash: '#8a3a9a', skin: '#b07a52', skin2: '#90603e' });
const woman3 = V('abigail', { scarf: '#2a9a7a', top: '#efe0c8', sash: '#2a9a7a', skin: '#d6a27a', skin2: '#b6825a' });
const solTeen = V('sol', { hat: null, beard: 'stubble' });
const SCALE = 1;

// helpers
function shotSel(T, list) { let v = list[0][1]; for (const [t, s] of list) if (T >= t) v = s; globalThis.__shot = v; return v; }
function panel(g, x, y, w, h, a, fn) { // dreamy vision panel
  if (a <= 0) return;
  g.save(); g.globalAlpha = a;
  g.beginPath(); g.roundRect(x, y, w, h, 40); g.clip();
  fn(g);
  g.restore();
  g.save(); g.globalAlpha = a * 0.5; g.strokeStyle = 'rgba(255,230,180,0.6)'; g.lineWidth = 3; g.beginPath(); g.roundRect(x, y, w, h, 40); g.stroke(); g.restore();
}
function notes(g, T, x0, y0, x1, y1, n = 6) { for (let i = 0; i < n; i++) { const k = ((T * 0.35 + i / n) % 1); const x = lerp(x0, x1, k) + Math.sin(k * 9 + i) * 20, y = lerp(y0, y1, k) - Math.sin(k * PI) * 80; g.save(); g.globalAlpha = Math.sin(k * PI) * 0.9; g.fillStyle = '#ffe7a0'; ell(g, x, y, 9, 7, -0.4); g.fill(); line(g, '#ffe7a0', 3, x + 8, y, x + 8, y - 30); g.restore(); } }
function pillars(g, n, c, y0, y1, x0 = 0, x1 = W) { for (let i = 0; i < n; i++) { const x = lerp(x0, x1, (i + 0.5) / n); g.fillStyle = c; g.fillRect(x - 24, y0, 48, y1 - y0); g.fillStyle = shade(c, -0.2); g.fillRect(x + 8, y0, 16, y1 - y0); g.fillStyle = shade(c, 0.1); g.fillRect(x - 34, y0, 68, 18); g.fillRect(x - 34, y1 - 18, 68, 18); } }
function floor(g, y, c1, c2) { g.fillStyle = lg(g, 0, y, 0, H, [[0, c1], [1, c2]]); g.fillRect(-400, y, W + 800, H + 600); }
function goldPile(g, x, y, s, t) { for (let i = 0; i < 40; i++) { const a = hash(i) * PI, r = hash(i * 3) * s; const xx = x + Math.cos(a) * r * 1.6, yy = y - Math.sin(a) * r * 0.8; fillE(g, i % 3 ? '#e1b84c' : '#f3d27a', xx, yy, 14, 7); } glow(g, x, y - s * 0.3, s * 1.6, '#ffd36a', 0.35 + 0.1 * Math.sin(t * 3)); }
function tree(g, x, y, s, c = '#3e6a3a', trunk = '#5a3a22') { g.fillStyle = trunk; g.fillRect(x - s * 0.08, y - s * 0.6, s * 0.16, s * 0.6); fillC(g, c, x, y - s * 0.8, s * 0.38); fillC(g, shade(c, 0.1), x - s * 0.25, y - s * 0.65, s * 0.28); fillC(g, shade(c, -0.1), x + s * 0.25, y - s * 0.68, s * 0.3); }
function olive(g, x, y, s, c = '#1d2a28') { g.fillStyle = '#1a1512'; g.beginPath(); g.moveTo(x - s * 0.1, y); g.quadraticCurveTo(x - s * 0.2, y - s * 0.4, x, y - s * 0.6); g.lineTo(x + s * 0.06, y - s * 0.55); g.quadraticCurveTo(x + s * 0.05, y - s * 0.3, x + s * 0.12, y); g.fill(); for (let i = 0; i < 6; i++) fillE(g, c, x + Math.cos(i * 1.1) * s * 0.35, y - s * 0.75 + Math.sin(i * 1.7) * s * 0.12, s * 0.28, s * 0.14); }
function lily(g, x, y, s, t, c = '#f6f1ff', glowA = 0) { const sw = Math.sin(t * 1.5 + x * 0.05) * 0.06; g.save(); g.translate(x, y); g.rotate(sw); line(g, '#4f8a3a', s * 0.08, 0, 0, 0, -s); fillE(g, '#5f9a4a', -s * 0.18, -s * 0.4, s * 0.2, s * 0.07, -0.5); for (let i = 0; i < 5; i++) { g.save(); g.translate(0, -s); g.rotate(-1.2 + i * 0.6); fillE(g, c, 0, -s * 0.22, s * 0.1, s * 0.25); g.restore(); } fillC(g, '#e8c040', 0, -s, s * 0.06); if (glowA) glow(g, 0, -s, s * 1.2, '#fff6c0', glowA); g.restore(); }
function torchBearers(g, T, n, x0, y0, a = 1) { for (let i = 0; i < n; i++) { const x = x0 + i * 46, y = y0 + (i % 2) * 10; fig(g, { x, y, s: 110, c: 'rgba(10,8,12,0.95)', arms: [0.2, 2.6], alpha: a }); flame(g, x + 30, y - 128, 9, T + i); } }
function cracks(g, x, y, prog, seed, c = 'rgba(20,10,10,0.9)') { g.strokeStyle = c; g.lineWidth = 3; for (let k = 0; k < 7; k++) { let px = x, py = y, ang = hash(k + seed) * TAU; g.beginPath(); g.moveTo(px, py); const n = Math.floor(14 * prog); for (let i = 0; i < n; i++) { ang += (hash(i * 13 + k + seed) - 0.5) * 1.1; px += Math.cos(ang) * 22; py += Math.sin(ang) * 14; g.lineTo(px, py); } g.stroke(); } }
function palaceFacade(g, x, y, s, c = '#e8c87a') { g.fillStyle = c; g.fillRect(x - s, y - s * 0.7, s * 2, s * 0.7); poly(g, [[x - s * 1.1, y - s * 0.7], [x + s * 1.1, y - s * 0.7], [x, y - s * 1.05]]); g.fill(); g.fillStyle = shade(c, -0.25); for (let i = 0; i < 6; i++) g.fillRect(x - s * 0.85 + i * s * 0.33, y - s * 0.6, s * 0.1, s * 0.6); }
function crownIcon(g, x, y, s, c = '#e1b84c') { g.fillStyle = c; poly(g, [[x - s, y], [x - s, y - s * 0.7], [x - s * 0.5, y - s * 0.3], [x, y - s * 0.9], [x + s * 0.5, y - s * 0.3], [x + s, y - s * 0.7], [x + s, y]]); g.fill(); }

// ================= GIFTED =================
S_.gifted = (g, T, S) => {
  const L = S.L;
  const weep = L[3].c[1] ? L[3].c[1].s : L[3].s + 2.5;
  const shot = shotSel(T, [[0, 'saul'], [L[1].s - 0.2, 'jon'], [L[2].s - 0.2, 'dance'], [weep - 0.1, 'weep']]);
  if (shot === 'saul') {
    g.save(); cam(g, 360, 560, 1.18 + T * 0.01);
    sky(g, '#1d1420', '#2e1f22', 0, 800); pillars(g, 4, '#4a3830', 80, 800); floor(g, 800, '#3a2a22', '#1a120e');
    flame(g, 70, 300, 18, T); flame(g, 650, 300, 18, T);
    // throne
    g.fillStyle = '#5a3a1a'; rrect(g, 400, 330, 200, 500, 20); g.fill(); g.fillStyle = '#c8a24a'; g.fillRect(400, 330, 200, 16);
    actor(g, CH.saul, T, S, { x: 500, y: 470, s: 64, seed: 8, turn: -0.3, h: 4.7,
      ex: [[0, 'hurt|{"tears":0,"lu":0.4,"gy":0.3}'], [2.6, 'weary|{"gx":-0.5}', 1.2], [L[0].e - 0.6, 'peace|{"lu":0.75}', 1.2]],
      arms: [[0, A(0.3, -0.2, 2.2, 1.9)], [L[0].e - 0.8, A(0.3, -0.2, 0.3, -0.6)]], tiltK: [[0, 0.15], [L[0].e - 0.8, -0.05, 1.2]] });
    const strum = (T % 0.5) / 0.5;
    actor(g, CH.davidY, T, S, { x: 210, y: 590, s: 60, kneel: true, turn: 0.35, seed: 3, ex: 'peace|{"lu":0.6,"sm":0.45,"gx":0.5}', aL: { s: 0.5, e: -1.6 }, aR: { s: 0.35 + Math.sin(T * 10) * 0.08, e: -1.5 }, holdL: PROP.lyre(strum) });
    notes(g, T, 230, 560, 470, 430, 7);
    g.restore(); tint(g, '#ffb070', 'soft-light', 0.25);
  } else if (shot === 'jon') {
    const lt = T - L[1].s;
    g.save(); cam(g, 360, 600, 1.2);
    sky(g, '#8fc3e8', '#e8f0d8', 0, 620); hills(g, 600, '#7aa060', 20, 2); hills(g, 700, '#5a8a48', 24, 5);
    tree(g, 120, 640, 260); tree(g, 640, 660, 200, '#4f7a40');
    const close = ease(lt / 1.6);
    actor(g, CH.jonathan, T, S, { x: lerp(200, 280, close), y: 480, s: 64, seed: 11, turn: 0.4, ex: [[0, 'warm|{"gx":0.6}'], [1.6, 'joy|{"gx":0.6,"mo":0}']], arms: [[0, A(0.2, -1.6, 0.6, -1.3)], [1.0 + L[1].s, A(0.2, 0.1, 1.5, 0.35)]] });
    actor(g, CH.davidY, T, S, { x: lerp(520, 440, close), y: 490, s: 62, seed: 3, turn: -0.4, ex: [[0, 'surprised|{"gx":-0.6,"mo":0}'], [1.2 + L[1].s, 'teary|{"gx":-0.6}']], arms: [[0, REST], [L[1].s + 1.2, A(1.5, 0.35, 0.2, 0.1)]] });
    g.restore();
  } else if (shot === 'dance') {
    const lt = T - L[2].s;
    g.save(); cam(g, 360, 560, 1.12);
    sky(g, '#7fb6e8', '#f6e0a8', 0, 650); fillC(g, '#fff6d0', 600, 160, 50); glow(g, 600, 160, 240, '#fff0b0', 0.5);
    g.fillStyle = '#d8c09a'; g.fillRect(-400, 560, W + 800, 30); for (let i = 0; i < 8; i++) house(g, i * 100 - 20, 600, 80, 90 + hash(i) * 60, i % 2 ? '#e2c89a' : '#cfb184');
    floor(g, 600, '#d6b98a', '#b0915e');
    // ark carried behind
    const ax = 520 + Math.sin(T * 1.5) * 6;
    fig(g, { x: ax - 80, y: 640, s: 150, c: '#6a5a4a', arms: [0.2, 2.2] }); fig(g, { x: ax + 80, y: 640, s: 150, c: '#6a5a4a', arms: [2.2, 0.2] });
    g.fillStyle = '#e1b84c'; g.fillRect(ax - 70, 470, 140, 60); line(g, '#8a6a2a', 8, ax - 120, 500, ax + 120, 500); fillE(g, '#f3d27a', ax - 40, 465, 22, 12); fillE(g, '#f3d27a', ax + 40, 465, 22, 12); glow(g, ax, 490, 160, '#ffe08a', 0.5);
    for (let i = 0; i < 10; i++) fig(g, { x: 30 + i * 75, y: 720 + (i % 2) * 20, s: 120, c: ['#8a5a4a', '#5a6a8a', '#7a4a6a'][i % 3], arms: [2.5 + Math.sin(T * 5 + i) * 0.3, 2.5 + Math.cos(T * 5 + i) * 0.3] });
    const bounce = Math.abs(Math.sin(T * 5.5)) * 26;
    actor(g, davidLinen, T, S, { x: 260 + Math.sin(T * 2.2) * 30, y: 430 - bounce, s: 62, seed: 3, spk: 'DAVID', turn: Math.sin(T * 2.2) * 0.3, lean: Math.sin(T * 2.75) * 0.12,
      ex: [[0, 'joy'], [L[2].e, 'joy|{"lu":0.5}']], aL: { s: 2.6 + Math.sin(T * 5.5) * 0.3, e: 0.4 }, aR: { s: 2.4 + Math.cos(T * 5.5) * 0.3, e: 0.5 } });
    g.restore();
    petals(g, T, 14, 7, ['rgba(255,240,200,0.8)', 'rgba(255,200,200,0.8)']);
  } else {
    const lt = T - weep;
    g.save(); cam(g, 360, 470 + lt * 2, 1.7 + lt * 0.03);
    sky(g, '#0b1028', '#1a2240', 0, 700); stars(g, 60, 3, 1, T); fillC(g, '#e8e6d8', 560, 160, 30);
    hills(g, 640, '#121a30', 20, 1); floor(g, 700, '#121a30', '#0a0e1c');
    actor(g, CH.davidY, T, S, { x: 360, y: 430, s: 66, kneel: true, seed: 3, spk: 'DAVID', turn: 0,
      ex: [[0, 'grief|{"gy":0.5}'], [L[4].s - 0.2, 'pleading|{"gy":-0.7,"tears":1}'], [L[4].e - 0.4, 'grief|{"gy":-0.3}']],
      arms: [[0, A(0.3, -2.4, 0.3, -2.4)], [L[4].s, A(2.0, 0.7, 2.0, 0.7)]], tiltK: [[0, 0.1], [L[4].s, -0.12]] });
    g.restore(); tint(g, '#6070c0', 'soft-light', 0.3);
  }
  vignette(g, 0.5);
};

// ================= CHEER =================
S_.cheer = (g, T, S) => {
  const L = S.L;
  const mid = L[0].s + (L[0].e - L[0].s) * 0.52;
  const shot = shotSel(T, [[0, 'street'], [L[0].e - 1.1, 'saul'], [L[1].s + 0.2, 'david'], [L[1].c.length > 1 ? L[1].c[L[1].c.length - 1].s : L[1].e - 1.5, 'street']]);
  if (shot === 'street' || shot === 'david') {
    const z = shot === 'david' ? 2.1 : 1.15;
    g.save(); cam(g, shot === 'david' ? 360 : 360, shot === 'david' ? 460 : 560, z);
    sky(g, '#6ab0e8', '#cfe6f0', 0, 520);
    g.fillStyle = '#c8a878'; g.fillRect(-400, 250, W + 800, 300); for (let i = -2; i < 12; i++) { g.fillStyle = '#b8966a'; g.fillRect(i * 70, 230, 40, 30); }
    g.fillStyle = '#3a2a1a'; rrect(g, 40, 330, 140, 220, 70); g.fill();
    floor(g, 550, '#d8bb8a', '#a8885a');
    // crowd silhouettes
    for (let i = 0; i < 14; i++) fig(g, { x: -30 + i * 60, y: 600, s: 120, c: ['#9a6a4a', '#6a7a9a', '#8a5a7a', '#7a8a5a'][i % 4], arms: [2.4 + Math.sin(T * 6 + i) * 0.3, 2.5 + Math.cos(T * 6 + i) * 0.3] });
    // David arriving with soldiers
    for (let i = 0; i < 4; i++) { fig(g, { x: 470 + i * 50, y: 640, s: 150, c: '#4a3a30', arms: [0.2, 2.9] }); line(g, '#888', 4, 470 + i * 50 + 22, 640 - 170, 470 + i * 50 + 30, 640 - 290); }
    actor(g, CH.davidK, T, S, { x: 360, y: 430, s: 52, seed: 3, turn: 0.05, ex: [[0, 'proud'], [mid, 'joy|{"mo":0}'], [L[1].s + 2, 'proud|{"lu":0.35}']], aL: { s: 0.25, e: 0.1 }, aR: { s: 0.25, e: -0.4 }, holdR: PROP.sword(shot === 'david' ? 0.5 + 0.4 * Math.sin(T * 3) : 0.3, 2.9) });
    // women dancing in front
    const ws = [[woman1, 120], [woman2, 600], [woman3, 240]];
    ws.forEach(([w, x], i) => { const b = Math.abs(Math.sin(T * 5 + i)) * 18; actor(g, w, T, S, { x: x + Math.sin(T * 2 + i) * 20, y: 700 - b + i * 60, s: 50, seed: 20 + i, spk: 'WOMEN', ex: 'joy', turn: Math.sin(T * 2 + i) * 0.3, lean: Math.sin(T * 2.5 + i) * 0.1, aL: { s: 2.5, e: 0.3 + Math.sin(T * 10 + i) * 0.2 }, aR: { s: 1.2, e: 0.6 }, holdL: PROP.tamb(T + i) }); });
    g.restore();
    petals(g, T, 26, 4, ['#ff8fb8', '#ffe07a', '#ffffff', '#ff9d6e']);
    if (shot === 'street' && T < L[0].e) {
      txt(g, 'SAUL — 1,000s', 360, 150, 46, '#ffffff', 'InterB', 'center', ramp(T, L[0].s + 0.6, L[0].s + 1.0) * 0.9);
      txt(g, 'DAVID — 10,000s', 360, 220, 58, '#ffe07a', 'InterB', 'center', ramp(T, mid, mid + 0.4));
    }
  } else {
    g.save(); cam(g, 360, 420, 2.4);
    sky(g, '#c8a878', '#9a7a52', 0, 800); g.fillStyle = '#5a3a2a'; g.fillRect(200, 300, 340, 600);
    actor(g, CH.saul, T, S, { x: 360, y: 400, s: 64, seed: 8, turn: 0.1, ex: [[0, 'smirk'], [L[0].e - 0.6, 'jealous', 0.6]], arms: [[0, REST]] });
    g.restore(); tint(g, '#802010', 'soft-light', 0.3);
  }
  vignette(g, 0.4);
};

// ================= RAID =================
S_.raid = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'wide'], [L[0].e - 1.8, 'cu'], [L[1].s - 0.1, 'ash']]);
  if (shot === 'wide') {
    g.save(); cam(g, 360, 600, 1.1 + T * 0.02);
    sky(g, '#1a0a0e', '#5a1a10', 0, 700);
    for (let i = 0; i < 9; i++) { const x = i * 90 - 20, h = 60 + hash(i) * 70; house(g, x, 640, 70, h, '#120808'); flame(g, x + 35, 640 - h - 6, 16 + hash(i) * 14, T + i); }
    smoke(g, T, 200, 560, 10, 1); smoke(g, T, 520, 560, 10, 2);
    floor(g, 640, '#2a0e0a', '#0a0404');
    for (let i = 0; i < 6; i++) { const x = 60 + i * 120 + T * 25; fig(g, { x: x % 800 - 40, y: 820 + (i % 2) * 30, s: 170, c: '#050304', arms: [0.4, 2.6] }); line(g, '#2a2a2a', 4, (x % 800 - 40) + 30, 820 + (i % 2) * 30 - 190, (x % 800 - 40) + 50, 820 + (i % 2) * 30 - 290); }
    g.restore();
  } else if (shot === 'ash') {
    const lt = T - L[1].s;
    g.save(); cam(g, 360, 640, 1.4 + lt * 0.03);
    sky(g, '#140808', '#2a0e0a', 0, 600); floor(g, 600, '#1e0c0a', '#080303');
    smoke(g, T, 360, 600, 14, 5, 'rgba(60,40,40,0.25)');
    // overturned jar and a sandal in ash
    g.save(); g.translate(300, 720); g.rotate(1.3); g.fillStyle = '#8a5a3a'; g.beginPath(); g.ellipse(0, 0, 40, 60, 0, 0, TAU); g.fill(); g.fillStyle = '#6a3a22'; g.fillRect(-18, -80, 36, 26); g.restore();
    fillE(g, '#5a3a22', 470, 760, 44, 16, 0.2); line(g, '#3a2210', 5, 450, 752, 490, 766);
    for (let i = 0; i < 30; i++) { const k = (T * 0.2 + hash(i)) % 1; fillC(g, `rgba(255,${120 + hash(i) * 80},40,${(1 - k) * 0.8})`, 100 + hash(i * 3) * 520, 800 - k * 600, 2 + hash(i * 7) * 2); }
    fig(g, { x: 620 + lt * 10, y: 640, s: 120, c: '#050304', arms: [0.2, 0.2], alpha: 1 - ramp(lt, 2, 4) });
    g.restore();
  } else {
    const cu2 = shot === 'cu2';
    g.save(); cam(g, 360, 470, 2.3);
    sky(g, '#1a0606', '#3a0e08', 0, 900); smoke(g, T, 360, 700, 8, 3);
    actor(g, CH.davidK, T, S, { x: 360, y: 450, s: 64, seed: 3, turn: cu2 ? -0.2 : 0.2, ex: cu2 ? 'hollow|{"gx":-0.4}' : 'cold|{"gx":0.2}', arms: [[0, REST]], holdR: PROP.sword(0, 2.9) });
    g.restore();
    tint(g, '#ff6a20', 'soft-light', 0.55); glow(g, 360, 1100, 600, '#ff5a10', 0.25);
  }
  for (let i = 0; i < 18; i++) { const k = (T * 0.25 + hash(i)) % 1; fillC(g, `rgba(255,${140 + hash(i) * 60},50,${(1 - k) * 0.7})`, hash(i * 3) * W, H * (1 - k), 2 + hash(i * 7) * 2.5); }
  vignette(g, 0.6);
};

// ================= URIAH =================
S_.uriah = (g, T, S) => {
  const L = S.L;
  const loyal = L[0].c.length > 1 ? L[0].c[1].s : L[0].s + 2.8;
  const ln = L[2].c.length > 1 ? L[2].c[1].s : L[2].s + 1.8;
  const shot = shotSel(T, [[0, 'roof'], [loyal, 'uriah'], [L[1].s - 0.2, 'write'], [L[2].s - 0.1, 'walk'], [ln, 'battle']]);
  if (shot === 'roof') {
    g.save(); cam(g, 330, 560, 1.25);
    sky(g, '#3a2a5a', '#e88a5a', 0, 700); fillC(g, '#ffd08a', 560, 560, 40);
    for (let i = 0; i < 7; i++) house(g, i * 110 - 30, 760, 90, 120 + hash(i + 4) * 80, '#4a3040');
    // distant figure on another roof, tasteful silhouette
    house(g, 520, 700, 150, 60, '#5a3a4a'); fig(g, { x: 590, y: 640, s: 50, c: '#2a1a2a', scarf: '#2a1a2a', arms: [0.3, 0.3] }); fillE(g, '#3a2a3a', 560, 636, 14, 6);
    g.fillStyle = '#6a4a4a'; g.fillRect(-400, 760, W + 800, 40); floor(g, 800, '#4a3038', '#1a1018');
    actor(g, CH.davidK, T, S, { x: 230, y: 470, s: 62, seed: 3, turn: 0.45, h: 4.6, ex: [[0, 'neutral|{"gx":0.8,"gy":0.4,"lu":0.3}'], [1.2, 'smirk|{"gx":0.8,"gy":0.4,"lu":0.4,"sm":0.2}']], arms: [[0, A(0.2, -0.3, 0.6, -1.2)]] });
    g.restore(); tint(g, '#ff7040', 'soft-light', 0.25);
  } else if (shot === 'uriah') {
    g.save(); cam(g, 360, 480, 1.9);
    sky(g, '#8ab0d8', '#e0d0a8', 0, 800); hills(g, 640, '#a08a60', 20, 3);
    for (let i = 0; i < 5; i++) { fig(g, { x: 80 + i * 140, y: 760, s: 200, c: '#5a4a3a', arms: [0.2, 2.9] }); }
    actor(g, CH.uriah, T, S, { x: 360, y: 470, s: 64, seed: 13, ex: 'proud|{"sm":0.7}', arms: [[0, A(0.3, -2.3, 0.15, -0.2)]], holdR: PROP.sword(0, -0.2) });
    g.restore();
  } else if (shot === 'write') {
    const lt = T - L[1].s;
    g.save(); cam(g, 360, 500, 2.0);
    sky(g, '#140e10', '#24181a', 0, 900);
    flame(g, 520, 560, 12, T);
    actor(g, CH.davidK, T, S, { x: 330, y: 460, s: 62, seed: 3, spk: 'DAVID', turn: 0.15, ex: [[0, 'cold|{"gy":0.6,"lu":0.5}'], [lt > 0 ? 0 : 0, 'cold|{"gy":0.6,"lu":0.5}']], arms: [[0, A(0.4, -1.3, 0.4, -1.1)], [L[1].e - 0.6, A(0.4, -1.3, 0.5, -1.5)]], holdR: PROP.quill(T), blink: 0 });
    g.fillStyle = '#3a2418'; g.fillRect(-200, 690, W + 400, 400);
    g.fillStyle = '#efe2c0'; g.save(); g.translate(360, 690); g.rotate(-0.05); g.fillRect(-90, -16, 180, 30);
    g.strokeStyle = 'rgba(60,40,30,0.7)'; g.lineWidth = 2; const prog = clamp(lt / (L[1].e - L[1].s));
    for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(-80, -8 + i * 8); g.lineTo(-80 + 160 * clamp(prog * 3 - i), -8 + i * 8); g.stroke(); }
    if (T > L[1].e - 0.3) fillC(g, '#a3191f', 60, 0, 12 * ramp(T, L[1].e - 0.3, L[1].e));
    g.restore();
    g.restore(); glow(g, 520, 560, 500, '#ffb060', 0.2); tint(g, '#2a1a40', 'multiply', 0.3);
  } else if (shot === 'walk') {
    g.save(); cam(g, 360, 520, 1.6);
    sky(g, '#9ab8d0', '#e0d0a8', 0, 700); hills(g, 640, '#b0986a', 26, 1); floor(g, 700, '#c0a070', '#9a7a50');
    const step = Math.abs(Math.sin(T * 5)) * 8;
    actor(g, CH.uriah, T, S, { x: 360, y: 450 - step, s: 62, seed: 13, turn: 0.2, ex: 'warm|{"gy":0.5,"gx":0.2}', arms: [[0, A(0.5, -1.7, 0.2, 0.1)]], holdL: PROP.letter(1) });
    g.restore();
  } else {
    const lt = T - ln;
    g.save(); cam(g, 360, 580, 1.05);
    sky(g, '#c08a5a', '#6a3a2a', 0, 700); floor(g, 700, '#7a5a3a', '#3a2a1a');
    // enemy wall of spears
    for (let i = 0; i < 16; i++) { const x = i * 48; line(g, '#2a1a10', 5, x, 720, x + 10, 420); fig(g, { x, y: 740, s: 170, c: '#1a0e08' }); }
    // fellow soldiers draw back
    for (let i = 0; i < 4; i++) fig(g, { x: 180 + i * 120, y: 980 + lt * 40, s: 200 - lt * 10, c: '#3a2a1a', alpha: 1 - ramp(lt, 0.5, 2.2) });
    const fall = ramp(lt, 1.6, 2.6);
    if (fall < 1) actor(g, CH.uriah, T, S, { x: 360, y: 760, s: 46, seed: 13, ex: [[0, 'determined'], [1.3, 'surprised|{"gx":-0.7}']], arms: [[0, A(0.3, -0.5, 0.25, -0.2)]], holdR: PROP.sword(0, -0.3), alpha: 1 - fall, lean: fall * 0.5 });
    // helmet in the dust
    if (fall > 0.5) { g.save(); g.translate(380, 990 + (1 - ramp(lt, 2.0, 2.4)) * -60); g.rotate(0.6); g.fillStyle = '#b5853a'; g.beginPath(); g.ellipse(0, 0, 50, 36, 0, PI, TAU); g.fill(); g.fillStyle = '#c0302a'; fillE(g, '#c0302a', 0, -44, 10, 18); g.restore(); smoke(g, lt, 380, 1000, 6, 9, 'rgba(160,120,80,0.25)'); }
    g.restore();
  }
  vignette(g, 0.5);
};

// ================= ABIGAIL =================
S_.abigail = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'march'], [L[1].s - 0.2, 'kneel'], [L[2].s - 0.2, 'melt'], [L[3].s - 0.1, 'wide']]);
  const road = (z, cx, cy) => { g.save(); cam(g, cx, cy, z); sky(g, '#e88a4a', '#f6d29a', 0, 600); hills(g, 560, '#c08050', 24, 4); floor(g, 600, '#c8a070', '#8a6a40'); g.fillStyle = '#d8b888'; poly(g, [[300, 600], [420, 600], [700, 1400], [20, 1400]]); g.fill(); };
  if (shot === 'march') {
    road(1.2, 360, 600);
    for (let i = 0; i < 12; i++) { const x = 140 + (i % 6) * 90, y = 640 + Math.floor(i / 6) * 50; fig(g, { x, y: y + Math.abs(Math.sin(T * 5 + i)) * -6, s: 130, c: '#3a2a20', arms: [0.3, 2.8] }); line(g, '#ccc', 3, x + 25, y - 150, x + 32, y - 210); }
    const st = Math.abs(Math.sin(T * 5)) * 10;
    actor(g, CH.davidK, T, S, { x: 360, y: 640 - st, s: 56, seed: 3, ex: 'angry', turn: 0, arms: [[0, A(0.3, -0.2, 1.4, -0.7)]], holdR: PROP.sword(0.4, -0.5) });
    g.restore(); tint(g, '#c03010', 'soft-light', 0.35);
  } else if (shot === 'kneel' || shot === 'melt') {
    const melt = shot === 'melt';
    const lt = melt ? T - L[2].s : T - L[1].s;
    road(1.55, 360, 560);
    // David standing above (left), Abigail kneeling (right) with bread
    const swordDown = melt ? ramp(lt, 0.2, 1.6) : 0;
    actor(g, CH.davidK, T, S, { x: 230, y: 400, s: 62, seed: 3, spk: 'DAVID', turn: 0.4,
      ex: melt ? [[0, 'angry|{"gx":0.6,"gy":0.5}'], [0.6, 'hurt|{"gx":0.6,"gy":0.5,"tears":0.2}', 1.0], [2.4, 'tender|{"gx":0.6,"gy":0.5}', 0.8]] : [[0, 'angry|{"gx":0.6,"gy":0.5}'], [2.0, 'cold|{"gx":0.6,"gy":0.5,"bi":0}', 1.0]],
      arms: [[0, A(0.3, -0.2, lerp(1.4, 0.15, swordDown), lerp(-0.7, 0, swordDown))], [melt ? 2.6 : 99, A(-0.2, -0.9, 0.15, 0)]], holdR: PROP.sword(0, lerp(-0.5, PI - 0.15, swordDown)) });
    actor(g, CH.abigail, T, S, { x: 470, y: 560, s: 58, kneel: true, seed: 17, spk: 'ABIGAIL', turn: -0.4,
      ex: melt ? [[0, 'pleading|{"gx":-0.6,"gy":-0.6}'], [1.2, 'teary|{"gx":-0.6,"gy":-0.6,"tears":0.3}']] : 'pleading|{"gx":-0.6,"gy":-0.6}',
      arms: [[0, A(0.6, -1.5, 0.6, -1.5)], [melt ? 2.8 : 99, A(0.6, -1.5, 1.6, 0.0)]] });
    PROP.bread()(g, 540, 760, 0, 60); PROP.bread()(g, 600, 770, 0, 50); for (let i = 0; i < 6; i++) fillC(g, '#6a2a4a', 470 + i * 14, 780, 9);
    g.restore();
  } else {
    road(1.0, 360, 620);
    for (let i = 0; i < 12; i++) fig(g, { x: 60 + (i % 6) * 50, y: 760 + Math.floor(i / 6) * 40, s: 120, c: '#3a2a20' });
    house(g, 520, 640, 160, 90, '#a07a50');
    fig(g, { x: 400, y: 800, s: 150, c: '#2f6fa3', scarf: '#2f6fa3', arms: [0.4, 0.4] }); glow(g, 400, 720, 200, '#ffe0a0', 0.4);
    g.restore();
  }
  vignette(g, 0.45);
};

// ================= TEMPLE =================
S_.temple = (g, T, S) => {
  const L = S.L;
  const hands = T > L[1].s + 1.5; globalThis.__shot = hands ? 'hands' : 'plans';
  g.save(); cam(g, 360, hands ? 520 : 560, hands ? 1.7 : 1.3);
  sky(g, '#1c1418', '#2c2024', 0, 900); flame(g, 600, 420, 14, T);
  actor(g, CH.davidO, T, S, { x: 300, y: 470, s: 64, seed: 3, spk: 'DAVID_OLD', turn: 0.25, h: 4.6,
    ex: [[0, 'tender|{"gx":0.5,"gy":0.4}'], [L[1].s, 'weary|{"gx":0.3}'], [L[1].s + 1.5, 'ashamed|{"gy":0.8,"tears":0.4}', 0.8]],
    arms: [[0, A(0.3, -1.2, 0.7, -1.6)], [L[1].s + 1.3, A(0.5, -2.3, 0.5, -2.3)]] });
  actor(g, CH.solC, T, S, { x: 520, y: 600, s: 46, seed: 31, turn: -0.4, ex: [[0, 'awe|{"gx":-0.4,"gy":0.5}'], [L[1].s + 0.5, 'worried|{"gx":-0.6,"gy":-0.4}']], arms: [[0, A(0.5, -1.4, 0.3, -0.6)]] });
  g.fillStyle = '#4a2e1c'; g.fillRect(-200, 740, W + 400, 500);
  // temple plans scroll
  g.fillStyle = '#efe2c0'; g.fillRect(250, 730, 240, 50); g.strokeStyle = '#7a5a3a'; g.lineWidth = 2; g.beginPath(); g.moveTo(300, 770); g.lineTo(370, 740); g.lineTo(440, 770); g.stroke(); g.strokeRect(310, 752, 120, 18);
  g.restore();
  if (hands) tint(g, '#a01010', 'soft-light', 0.35 * ramp(T, L[1].s + 1.5, L[1].s + 2.5));
  glow(g, 600, 420, 400, '#ffb060', 0.15); vignette(g, 0.55);
};

// ================= DEATHBED =================
S_.deathbed = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'bed'], [L[2].s - 0.1, 'cu']]);
  if (shot === 'bed') {
    g.save(); cam(g, 360, 540, 1.35);
    sky(g, '#120c10', '#1e1418', 0, 900); flame(g, 120, 380, 12, T);
    // bed
    g.fillStyle = '#4a2e1c'; g.fillRect(40, 600, 420, 200);
    fillE(g, '#e8e0d0', 140, 560, 90, 40);
    g.save(); g.translate(170, 520); g.rotate(-0.35);
    drawChar(g, CH.davidO, { x: 0, y: 0, s: 50, t: T, seed: 3, half: true, talk: S.mouth('DAVID_OLD', T), ex: kf(T, [[0, ex('cold|{"gx":0.8,"lu":0.55}'.split('|')[0], { gx: 0.8, lu: 0.55 })], [L[1].s, ex('cold', { gx: 0.8, lu: 0.4, bi: -0.7 })]]),
      aL: { s: 0.2, e: -0.4 }, aR: { s: 1.3, e: -0.2 }, holdR: T > L[1].s + 0.6 && T < L[1].e + 0.6 ? PROP.sword(0, -1.2) : null });
    g.restore();
    g.fillStyle = '#5b2a6e'; g.beginPath(); g.moveTo(60, 620); g.quadraticCurveTo(260, 560, 460, 610); g.lineTo(460, 700); g.lineTo(60, 700); g.fill();
    actor(g, CH.sol, T, S, { x: 530, y: 470, s: 58, kneel: true, seed: 33, turn: -0.4, ex: [[0, 'worried|{"gx":-0.7,"gy":0.2}'], [L[1].s + 0.6, 'hollow|{"gx":-0.4,"gy":0.6}', 0.8]], arms: [[0, A(0.9, -1.6, 0.4, -1.4)]] });
    g.restore();
    glow(g, 120, 380, 500, '#ffa050', 0.18);
  } else {
    const lt = T - L[2].s;
    g.save(); cam(g, 360, 470, 2.2);
    sky(g, '#120c10', '#1e1418', 0, 900);
    actor(g, CH.sol, T, S, { x: 360, y: 450, s: 64, seed: 33, ex: [[0, 'hollow|{"gy":0.7}'], [2.4, 'grief|{"gy":0.6,"tears":0.6}', 1.2]], arms: [[0, A(0.35, -1.6, 0.35, -1.6)]], holdR: PROP.sword(0.2 + 0.2 * Math.sin(T * 4), -1.2) });
    g.restore();
    glow(g, 160, 380, 500, '#ffa050', 0.2 + 0.05 * noise1(T * 6));
  }
  vignette(g, 0.65);
};

// ================= KITCHEN 2 =================
S_.kitchen2 = (g, T, S) => {
  const L = S.L;
  return kitchenScene({
    shots: [[0, 'noa'], [L[1].s - 0.1, 'two'], [L[3].s - 0.1, 'noa'], [L[4].s - 0.1, 'teo']],
    noa: { ex: [[0, 'sad|{"gy":0.8,"gx":0.2}'], [L[1].s, 'sad|{"gx":0.6,"gy":0}'], [L[2].s + 1.6, 'hurt|{"gx":0.4,"gy":0.3,"tears":0}'], [L[3].s, 'thoughtful|{"gx":0.2,"gy":0.4}'], [L[3].s + 1.6, 'realize|{"gx":0.6,"gy":-0.1}'], [L[4].s, 'worried|{"gx":0.6}']],
      arms: [[0, A(0.3, -1.4, 0.7, -2.0)], [L[1].s, TABLE], [L[3].s + 1.4, A(0.5, -2.1, 0.5, -2.1)]], tiltK: [[0, 0.08], [L[1].s, 0], [L[3].s, 0.1]] },
    teo: { ex: [[0, 'tender|{"gx":-0.6}'], [L[1].s, 'firm|{"gx":-0.6,"bi":0.2}'], [L[2].s, 'sad|{"gx":-0.6,"gy":0.2}'], [L[3].s, 'tender|{"gx":-0.6}'], [L[4].s, 'firm|{"gx":-0.6,"bi":0.4}'], [L[4].s + 1.5, 'sad|{"gx":0.6,"gy":-0.2}', 0.8]],
      arms: [[0, TABLE], [L[1].s + 0.8, A(0.25, -1.35, 0.7, -2.4)], [L[2].s, TABLE]], nodK: [[0, 0], [L[4].s + 0.2, 0.08], [L[4].s + 0.7, 0]] },
    front: (g2, T2) => { if (T2 < 2.6) { g2.save(); g2.globalAlpha = ramp(T2, 0.8, 1.6); line(g2, '#c03030', 4, 220, 752, 300, 760); g2.restore(); txt(g2, 'chill', 260, 760, 20, '#333', 'InterSBI', 'center', 1); } },
  })(g, T, S);
};

// ================= CHILDHOOD =================
S_.childhood = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'birth'], [L[1].s - 0.1, 'tamar'], [L[2].s - 0.1, 'absalom'], [L[3].s - 0.1, 'cry'], [L[4].s - 0.1, 'surface'], [L[5].s - 0.05, 'under'], [L[6].s - 0.1, 'child']]);
  const corridor = (z, cx, cy) => { g.save(); cam(g, cx, cy, z); sky(g, '#2a1e16', '#4a3626', 0, 760); pillars(g, 5, '#8a6a3a', 100, 760); floor(g, 760, '#5a4028', '#2a1e12'); };
  if (shot === 'birth') {
    const second = L[0].c.length > 1 ? L[0].c[1].s : L[0].s + 3;
    g.save(); cam(g, T < second ? 330 : 420, 520, 1.6);
    sky(g, '#1e1414', '#2e2020', 0, 900); flame(g, 600, 380, 12, T);
    actor(g, bathsheba, T, S, { x: 300, y: 450, s: 62, seed: 41, turn: 0.2, h: 4.6, ex: [[0, 'tender|{"gy":0.6,"gx":0.2}'], [second, 'grief|{"gx":0.8,"gy":0.4,"tears":0.7}', 0.9]], arms: [[0, A(0.5, -1.9, 0.5, -1.9)]] });
    // baby bundle
    fillE(g, '#efe7d6', 300, 660, 60, 34); fillC(g, '#cf9a70', 330, 650, 18);
    // empty cradle
    g.fillStyle = '#5a3a22'; g.save(); g.translate(560, 720); g.rotate(Math.sin(T * 1.2) * 0.06); g.beginPath(); g.ellipse(0, 0, 80, 40, 0, 0, PI); g.fill(); g.fillStyle = 'rgba(240,230,210,0.5)'; g.fillRect(-60, -6, 120, 8); g.restore();
    g.restore(); glow(g, 600, 380, 500, '#ffa050', 0.15);
  } else if (shot === 'tamar') {
    const lt = T - L[1].s;
    corridor(1.25, 360, 560);
    g.fillStyle = '#1a100a'; g.fillRect(560, 400, 110, 360);
    // Tamar silhouette walking away, robe of many colours torn, hand on head
    const x = 610 - lt * 40;
    g.save(); g.globalAlpha = 0.95;
    fig(g, { x, y: 760, s: 230, c: '#2a1a24', scarf: '#2a1a24', arms: [0.3, 2.9] });
    for (let i = 0; i < 4; i++) { g.fillStyle = ['#c0392b', '#2f6fa3', '#e1b84c', '#2a9a7a'][i]; g.globalAlpha = 0.55; g.fillRect(x - 30 + i * 15, 640, 13, 110 - (i % 2) * 30); }
    g.restore();
    actor(g, CH.solC, T, S, { x: 170, y: 560, s: 46, seed: 31, turn: 0.5, ex: [[0, 'worried|{"gx":0.8}'], [1.5, 'hurt|{"gx":0.6,"tears":0.2}']], arms: [[0, A(0.9, -1.7, 0.2, -0.4)]] });
    g.fillStyle = '#8a6a3a'; g.fillRect(70, 100, 60, 660);
    g.restore();
  } else if (shot === 'absalom') {
    const lt = T - L[2].s;
    const second = L[2].c.length > 1 ? L[2].c[1].s - L[2].s : 2.5;
    g.save(); cam(g, 360, 560, 1.15);
    if (lt < second) {
      sky(g, '#2a1a12', '#3a2414', 0, 900); g.fillStyle = '#5a3a22'; g.fillRect(80, 640, 560, 30);
      const tip = ramp(lt, 0.6, 1.0);
      g.save(); g.translate(380, 640); g.rotate(tip * 1.5); g.fillStyle = '#c8a24a'; poly(g, [[-16, 0], [16, 0], [22, -50], [-22, -50]]); g.fill(); g.restore();
      g.fillStyle = 'rgba(140,10,20,0.85)'; fillE(g, 'rgba(140,10,20,0.85)', 430, 648, 70 * tip, 10 * tip);
      fig(g, { x: 220, y: 640, s: 160, c: '#100a08', arms: [0.4, 1.3] }); fig(g, { x: 560, y: 640, s: 170, c: '#100a08', arms: [1.6, 0.2], lean: tip * 0.4 });
    } else {
      sky(g, '#5a1a10', '#c05a2a', 0, 700); floor(g, 700, '#3a1a10', '#1a0a06');
      for (let i = 0; i < 9; i++) { const st = Math.abs(Math.sin(T * 4 + i)) * 8; fig(g, { x: 60 + i * 75 + (T % 100) * 18 - 120, y: 760 - st, s: 140, c: '#1a0a06', arms: [0.2, 2.6 + Math.sin(T * 4 + i) * 0.25] }); line(g, '#1a0a06', 4, 60 + i * 75 + (T % 100) * 18 - 92, 600, 60 + i * 75 + (T % 100) * 18 - 92, 520 - st); if (i % 3 === 0) { g.fillStyle = '#8a1a10'; g.beginPath(); g.moveTo(60 + i * 75 + (T % 100) * 18 - 92, 520 - st); for (let k = 0; k <= 6; k++) g.lineTo(60 + i * 75 + (T % 100) * 18 - 92 + k * 9, 520 - st + Math.sin(T * 6 + k * 0.9 + i) * 5); g.lineTo(60 + i * 75 + (T % 100) * 18 - 38, 555 - st); g.lineTo(60 + i * 75 + (T % 100) * 18 - 92, 555 - st); g.fill(); } }
      // great oak, banner falling
      g.fillStyle = '#1a0e08'; g.fillRect(480, 360, 40, 340); fillC(g, '#1a1a0e', 500, 330, 140); fillC(g, '#1e1e10', 420, 380, 90); fillC(g, '#1e1e10', 590, 370, 100);
      const fall = ramp(lt - second, 0.5, 2.0);
      fig(g, { x: 240 + fall * 80, y: 700, s: 200, c: '#100804', hairLong: '#100804', arms: [2.8, 0.4], rot: fall * 1.4, alpha: 1 - fall * 0.5 });
    }
    g.restore();
  } else if (shot === 'cry') {
    g.save(); cam(g, 360, 480, 1.8);
    sky(g, '#1a1414', '#2a2020', 0, 900); g.fillStyle = '#3a2e26'; rrect(g, 120, 160, 480, 700, 240); g.fill(); g.fillStyle = '#5a4a3a'; rrect(g, 170, 210, 380, 640, 190); g.fill();
    actor(g, davidMid, T, S, { x: 360, y: 450, s: 62, kneel: true, seed: 3, spk: 'DAVID_CRY', ex: 'grief|{"gy":-0.5,"mo":0.1}', arms: [[0, A(2.3, 0.9, 2.3, 0.9)], [S.L[3].e - 0.6, A(0.4, -2.5, 0.4, -2.5)]], tiltK: [[0, -0.15], [S.L[3].e - 0.6, 0.2]] });
    g.restore();
    // child in doorway foreground silhouette
    fig(g, { x: 620, y: 1280, s: 380, c: 'rgba(10,6,4,0.9)', arms: [0.4, 0.1] });
    vignette(g, 0.4);
  } else if (shot === 'surface' || shot === 'under') {
    const under = shot === 'under';
    const lt = under ? T - L[5].s : T - L[4].s;
    const tilt = under ? ease(lt / 1.5) : 0;
    g.save(); cam(g, 360, lerp(460, 800, tilt), 1.1);
    sky(g, '#7ab8f0', '#fff0c0', -200, 640); glow(g, 360, 200, 400, '#fff0a0', 0.6);
    palaceFacade(g, 360, 620, 220); glow(g, 360, 450, 320, '#ffe080', 0.35);
    for (let i = 0; i < 12; i++) fig(g, { x: 40 + i * 58, y: 690, s: 70, c: '#6a5a8a', kneel: true, lean: 0.4 });
    // reflection / underside
    g.save(); g.translate(0, 1300); g.scale(1, -0.9);
    g.globalAlpha = 0.35; palaceFacade(g, 360, 620, 220, '#8a7040'); g.restore();
    g.fillStyle = 'rgba(10,6,12,0.65)'; g.fillRect(-300, 700, W + 600, 900);
    if (under) cracks(g, 360, 900, ramp(lt, 1.0, 4.5), 7, 'rgba(200,40,30,0.8)');
    g.restore();
    if (!under) { const words = ['a palace', 'a beloved king', 'wealth', "God's favor"]; }
  } else {
    corridor(2.3, 360, 500);
    actor(g, CH.solC, T, S, { x: 360, y: 470, s: 46, seed: 31, spk: 'SOLOMON_CHILD', ex: 'worried|{"bi":0.9}', gaze: [[0, { x: -0.7, y: 0 }], [S.L[6].s + 0.9, { x: 0.7, y: 0 }, 0.25], [S.L[6].s + 1.8, { x: -0.5, y: 0.2 }, 0.25], [S.L[6].s + 2.8, { x: 0, y: 0 }, 0.3]], arms: [[0, A(0.9, -1.8, 0.2, -0.3)]] });
    g.fillStyle = '#8a6a3a'; g.fillRect(180, 0, 70, 1400);
    g.restore();
    tint(g, '#201008', 'multiply', 0.25);
  }
  vignette(g, 0.5);
};

// ================= EMPIRE =================
S_.empire = (g, T, S) => {
  const L = S.L;
  const c1 = L[1].c, c2 = L[2].c, c3 = L[3].c;
  const shot = shotSel(T, [[0, 'throne'], [c1[0].s - 0.1, 'wisdom'], [c1[1] ? c1[1].s : 99, 'wealth'], [c1[2] ? c1[2].s : 99, 'build'], [c1[3] ? c1[3].s : 99, 'garden'], [L[2].s - 0.1, 'wives'], [L[3].s - 0.1, 'labor'], [c3[1] ? c3[1].s : 99, 'fame'], [L[4].s - 0.1, 'throne2']]);
  const hall = () => { sky(g, '#3a2a10', '#7a5a20', 0, 800); pillars(g, 6, '#c8a24a', 60, 800); floor(g, 800, '#8a6a2a', '#3a2a10'); };
  if (shot === 'throne' || shot === 'throne2') {
    const lt = shot === 'throne' ? T : T - L[4].s;
    const z = shot === 'throne' ? lerp(2.0, 1.0, ease(lt / 3.5)) : lerp(1.1, 2.2, ease(lt / 3));
    g.save(); cam(g, 360, 520, z); hall();
    g.fillStyle = '#e1b84c'; rrect(g, 240, 260, 240, 600, 30); g.fill(); g.fillStyle = '#b8902e'; rrect(g, 270, 300, 180, 520, 20); g.fill();
    goldPile(g, 120, 900, 80, T); goldPile(g, 600, 900, 90, T);
    actor(g, CH.sol, T, S, { x: 360, y: 470, s: 62, seed: 33, h: 4.6, ex: shot === 'throne' ? 'proud' : [[0, 'proud|{"sm":0.7}'], [1.4, 'smirk|{"sm":0.25,"bi":0.3}', 0.8], [2.6, 'hollow|{"gy":0.3}', 1.4]], arms: [[0, A(0.7, -0.6, 0.7, -0.6)]] });
    g.restore(); glow(g, 360, 400, 600, '#ffd060', 0.15);
  } else if (shot === 'wisdom') {
    g.save(); cam(g, 360, 520, 1.6); hall();
    actor(g, CH.sol, T, S, { x: 360, y: 470, s: 62, seed: 33, ex: 'awe|{"gy":-0.4}', arms: [[0, A(1.6, -0.5, 1.6, -0.5)]] });
    for (let i = 0; i < 8; i++) { const a = T * 0.8 + i * TAU / 8; PROP.scroll(1)(g, 360 + Math.cos(a) * 200, 420 + Math.sin(a) * 80, 0, 26); }
    g.restore(); glow(g, 360, 420, 300, '#fff0b0', 0.3);
  } else if (shot === 'wealth') {
    const lt = T - c1[1].s;
    g.save(); cam(g, 360, 560, 1.1); hall(); goldPile(g, 360, 900, 80 + lt * 120, T); g.restore();
    txt(g, 'WEALTH', 360, 200, 64, '#ffe07a', 'SerifB', 'center', 0.85);
  } else if (shot === 'build') {
    const lt = T - c1[2].s;
    g.save(); cam(g, 360, 560, 1.0); sky(g, '#8ac0f0', '#f6e0a8', 0, 760); floor(g, 760, '#c8a878', '#8a6a40');
    for (let i = 0; i < 6; i++) { const h = 360 * ramp(lt, i * 0.08, 0.5 + i * 0.08); g.fillStyle = '#efe0c0'; g.fillRect(110 + i * 100, 760 - h, 50, h); }
    if (lt > 0.5) { g.globalAlpha = ramp(lt, 0.5, 0.8); g.fillStyle = '#e8d4a8'; poly(g, [[80, 400], [640, 400], [360, 280]]); g.fill(); g.globalAlpha = 1; }
    g.restore(); txt(g, 'BUILDINGS', 360, 200, 60, '#ffffff', 'SerifB', 'center', 0.9);
  } else if (shot === 'garden') {
    const lt = T - c1[3].s;
    g.save(); cam(g, 360, 560, 1.0); sky(g, '#8ac0f0', '#e8f0c8', 0, 700); floor(g, 700, '#5a9a4a', '#2a5a2a');
    for (let i = 0; i < 9; i++) { const s = 200 * easeOut(ramp(lt, i * 0.05, 0.6 + i * 0.05)); tree(g, 40 + i * 85, 760 + (i % 2) * 60, s, i % 2 ? '#3e7a3a' : '#5a9a3a'); }
    for (let i = 0; i < 30; i++) lily(g, hash(i) * W, 900 + hash(i * 3) * 300, 40 * ramp(lt, 0.2, 0.8), T, ['#ff8fb8', '#ffe07a', '#ffffff'][i % 3]);
    g.restore(); txt(g, 'GARDENS', 360, 200, 60, '#ffffff', 'SerifB', 'center', 0.9);
  } else if (shot === 'wives') {
    const lt = T - L[2].s;
    g.save(); cam(g, 360, 520, 1.0); sky(g, '#2a1a3a', '#5a3a4a', 0, H);
    const n = Math.floor(clamp(lt / 3.0) * 120);
    for (let i = 0; i < n; i++) { const row = Math.floor(i / 12), col = i % 12; const s = 90 - row * 6; fig(g, { x: 40 + col * 58 + (row % 2) * 20, y: 330 + row * 62, s, c: ['#c06a8a', '#8a5aaa', '#d8a04a', '#5a8aaa'][i % 4], scarf: ['#a04a6a', '#6a3a8a', '#b8802a', '#3a6a8a'][i % 4], alpha: 0.9 }); }
    g.restore();
    const second = c2[1] ? c2[1].s : L[2].e;
    txt(g, '700', 230, 190, 110, '#ffd0e0', 'SerifB', 'center', ramp(T, L[2].s, L[2].s + 0.3));
    txt(g, '300', 500, 190, 110, '#e0d0ff', 'SerifB', 'center', ramp(T, second, second + 0.3));
  } else if (shot === 'labor') {
    const lt = T - L[3].s;
    g.save(); cam(g, 360, 560, 1.0); sky(g, '#e8a050', '#f6d090', 0, 700); fillC(g, '#fff0c0', 560, 200, 70); floor(g, 700, '#c89a60', '#8a6030');
    const sx = 520 - lt * 30;
    g.fillStyle = '#9a8a70'; g.fillRect(sx, 640, 200, 140);
    for (let i = 0; i < 7; i++) { const x = sx - 60 - i * 70; line(g, '#6a4a2a', 4, x, 700, sx, 700); fig(g, { x, y: 800, s: 170, c: '#3a2416', lean: 0.55, arms: [1.6, 1.4] }); }
    fig(g, { x: 640, y: 820, s: 200, c: '#2a1a10', arms: [0.2, 2.4] }); line(g, '#2a1a10', 4, 670, 650, 720, 580);
    g.restore();
  } else {
    const lt = T - c3[1].s;
    g.save(); cam(g, 360, 560, 1.0); sky(g, '#6aa8e0', '#f6e0a8', 0, 640);
    g.fillStyle = '#3a7ab0'; g.fillRect(-300, 520, W + 600, 140);
    for (let i = 0; i < 3; i++) { const x = (i * 260 + lt * 40) % 900 - 100; g.fillStyle = '#6a4a2a'; poly(g, [[x - 70, 560], [x + 70, 560], [x + 50, 590], [x - 50, 590]]); g.fill(); g.fillStyle = '#f0e8d8'; poly(g, [[x, 470], [x, 555], [x + 55, 555]]); g.fill(); }
    floor(g, 660, '#d8b888', '#a88858');
    for (let i = 0; i < 6; i++) { fig(g, { x: 80 + i * 110, y: 900, s: 190, c: ['#7a3a6a', '#2a6a7a', '#8a5a2a'][i % 3], kneel: i % 2 === 0, lean: 0.3, arms: [1.2, 1.2] }); fillE(g, '#e1b84c', 80 + i * 110 + 30, 800, 18, 12); }
    // camel
    g.fillStyle = '#b08850'; fillE(g, '#b08850', 600, 760, 80, 40); fillE(g, '#b08850', 590, 720, 30, 30); line(g, '#b08850', 18, 670, 760, 700, 680); fillE(g, '#b08850', 712, 672, 22, 12); for (const lx of [550, 580, 620, 650]) line(g, '#b08850', 10, lx, 790, lx, 860);
    g.restore();
    txt(g, 'FAME', 360, 200, 60, '#ffffff', 'SerifB', 'center', 0.9);
  }
  vignette(g, 0.45);
};

// ================= HEVEL =================
function vapor(g, x, y, t, a, spread = 1, n = 14) { for (let i = 0; i < n; i++) { const k = (t * 0.25 + i / n) % 1; fillC(g, `rgba(235,240,255,${a * (1 - k) * 0.35})`, x + k * 160 * spread + Math.sin(k * 8 + i) * 25, y - k * 180, 14 + k * 50); } }
S_.hevel = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'wide'], [L[0].s + 1.0, 'mid'], [L[1].s - 0.1, 'grab'], [L[2].s - 0.1, 'window'], [L[3].s - 0.1, 'wind'], [L[4].s - 0.1, 'cu'], [L[5].s - 0.1, 'scroll'], [L[5].c[L[5].c.length - 1].s - 0.1, 'top']]);
  const hall = () => { sky(g, '#1e1a28', '#4a3a3a', 0, 800); for (let i = 0; i < 3; i++) { g.fillStyle = 'rgba(255,190,120,0.06)'; poly(g, [[180 + i * 160, 120], [240 + i * 160, 120], [320 + i * 160, 800], [160 + i * 160, 800]]); g.fill(); } pillars(g, 4, '#4a3e3a', 60, 820); floor(g, 820, '#3a302c', '#14100e'); for (let i = 0; i < 26; i++) { const k = (T * 0.05 + hash(i)) % 1; fillC(g, 'rgba(255,220,170,0.4)', 150 + hash(i * 3) * 420, 800 - k * 700, 1.5); } };
  const throne = () => { g.fillStyle = '#6a5a2a'; rrect(g, 250, 260, 220, 620, 26); g.fill(); g.fillStyle = '#4a3e1e'; rrect(g, 280, 300, 160, 540, 16); g.fill(); };
  if (shot === 'wide' || shot === 'mid' || shot === 'grab' || shot === 'cu') {
    const z = shot === 'wide' ? 0.95 + T * 0.1 : shot === 'mid' ? 1.6 : shot === 'grab' ? 1.5 : 2.4;
    g.save(); cam(g, 360, shot === 'cu' ? 470 : 520, z); hall(); throne();
    const grabK = shot === 'grab' ? ramp(T, L[1].e - 1.6, L[1].e - 0.9) : 0;
    actor(g, CH.solO, T, S, { x: 360, y: 470, s: 60, seed: 33, spk: 'SOLOMON', h: 4.6,
      ex: shot === 'cu' ? [[0, 'weary|{"gy":0.6}'], [L[4].s + 0.3, 'closed|{"bi":0.9,"sm":-0.6,"tears":0.5}', 0.6]] : shot === 'grab' ? [[0, 'weary|{"gx":0.5,"gy":-0.3}'], [L[1].e - 1.6, 'pleading|{"gx":0.6,"gy":-0.4,"tears":0}'], [L[1].e - 0.6, 'hollow|{"gx":0.4}']] : 'weary',
      arms: shot === 'grab' ? [[0, A(0.4, -0.6, 0.6, -0.5)], [L[1].e - 1.8, A(0.4, -0.6, 1.9, -0.2)], [L[1].e - 1.0, A(0.4, -0.6, 1.8, -0.9)]] : [[0, A(0.6, -0.6, 0.6, -0.6)]],
      tiltK: shot === 'cu' ? [[0, 0], [L[4].s + 0.3, 0.12]] : [[0, 0]], nodK: shot === 'cu' ? [[0, 0], [L[4].s + 0.3, 0.12]] : [[0, 0]] });
    if (shot === 'wide' || shot === 'mid') { const o = S.mouth('SOLOMON', T).o; vapor(g, 380, 510, T, 0.6 + o, 0.8); }
    if (shot === 'grab') { const disperse = ramp(T, L[1].e - 1.0, L[1].e); vapor(g, 470, 440, T, 1 - disperse * 0.8, 1 + disperse * 2, 18); }
    g.restore();
    if (shot === 'grab') { const a = ramp(T, L[1].s + 0.6, L[1].s + 1.2) * (1 - ramp(T, L[1].e - 0.8, L[1].e)); txt(g, 'הֶבֶל', 360, 190, 92, 'rgba(235,240,255,0.9)', 'DV', 'center', a); txt(g, 'hevel · vapor · breath', 360, 250, 34, 'rgba(235,240,255,0.85)', 'InterSBI', 'center', a); }
  } else if (shot === 'window') {
    const lt = T - L[2].s;
    g.save(); cam(g, 360, 520, 1.2);
    sky(g, '#2a2230', '#3a2e2e', 0, 900);
    g.fillStyle = '#e8a060'; rrect(g, 110, 140, 500, 420, 200); g.fill();
    g.save(); g.beginPath(); g.roundRect(110, 140, 500, 420, 200); g.clip(); sky(g, '#f0a060', '#ffd8a0', 140, 560); hills(g, 480, '#8a6a4a', 20, 2);
    const cs = L[2].c; const t1 = cs[1] ? cs[1].s - L[2].s : 1.5, t2 = cs[2] ? cs[2].s - L[2].s : 3;
    for (let i = 0; i < 5; i++) if (lt > t1 + i * 0.15) house(g, 140 + i * 90, 520, 70, 80 + hash(i) * 40, '#c8a070');
    for (let i = 0; i < 6; i++) if (lt > t2 + i * 0.12) for (let k = 0; k < 4; k++) fillC(g, '#5a7a3a', 150 + i * 80 + k * 14, 545 - k * 3, 9);
    g.restore();
    floor(g, 760, '#3a302c', '#14100e');
    actor(g, CH.solO, T, S, { x: 300, y: 560, s: 54, seed: 33, spk: 'SOLOMON', turn: 0.3, ex: 'weary|{"gx":0.5,"gy":-0.3,"sm":0.1}', arms: [[0, A(0.3, -0.2, 0.3, -0.2)], [0.6, A(0.3, -0.2, 1.9, 0.2)]] });
    g.restore();
  } else if (shot === 'wind') {
    g.save(); cam(g, 360, 500, 1.6); hall(); throne();
    for (let i = 0; i < 3; i++) { g.fillStyle = 'rgba(160,40,40,0.8)'; g.beginPath(); g.moveTo(100 + i * 260, 100); for (let y = 100; y < 800; y += 20) g.lineTo(100 + i * 260 + Math.sin(y * 0.02 + T * 4 + i) * 30 + (y - 100) * 0.15, y); g.lineTo(140 + i * 260 + 120, 800); g.lineTo(140 + i * 260, 100); g.fill(); }
    actor(g, CH.solO, T, S, { x: 360, y: 470, s: 60, seed: 33, spk: 'SOLOMON', h: 4.6, ex: 'hurt|{"gx":0.6,"gy":-0.2}', arms: [[0, A(0.6, -0.6, 0.6, -0.6)], [0.8, A(0.6, -0.6, 2.2, -0.1)], [1.8, A(0.6, -0.6, 2.0, -1.2)]] });
    for (let i = 0; i < 40; i++) { const k = (T * 0.7 + hash(i)) % 1; const x = -50 + k * 900, y = 200 + hash(i * 3) * 700 + Math.sin(k * 10 + i) * 30; line(g, 'rgba(255,240,220,0.35)', 2, x, y, x + 40, y - 4); }
    g.restore();
  } else if (shot === 'scroll') {
    const lt = T - L[5].s;
    g.save(); cam(g, 360, 600, 1.6);
    sky(g, '#1a1418', '#2a2024', 0, 900); flame(g, 560, 470, 12, T);
    g.fillStyle = '#efe2c0'; g.fillRect(170, 560, 380, 220);
    g.strokeStyle = 'rgba(60,40,30,0.75)'; g.lineWidth = 3;
    for (let i = 0; i < 7; i++) { const w = 320 * clamp(lt * 0.5 - i * 0.3); g.beginPath(); g.moveTo(200, 590 + i * 26); g.lineTo(200 + w, 590 + i * 26); g.stroke(); }
    // two hands writing: old king's & later scribe's ghost
    PROP.quill(T)(g, 200 + 320 * clamp(lt * 0.5) % 320, 600, 0, 50);
    g.save(); g.globalAlpha = 0.4 * ramp(lt, 2, 3); fig(g, { x: 560, y: 900, s: 380, c: '#d8d0ff' }); g.restore();
    g.restore(); glow(g, 560, 470, 400, '#ffb060', 0.2);
    txt(g, 'Tradition: Solomon', 360, 180, 36, '#e6c35c', 'InterSB', 'center', ramp(T, L[5].s, L[5].s + 0.4));
    txt(g, 'Many scholars: a later writer in his voice', 360, 232, 28, '#d8d0ff', 'InterSBI', 'center', ramp(T, L[5].s + 2.2, L[5].s + 2.6));
  } else {
    const lt = T - L[5].c[L[5].c.length - 1].s;
    g.save(); cam(g, 360, lerp(360, 640, ease(lt / 3)), lerp(1.8, 0.9, ease(lt / 3)));
    sky(g, '#1a1830', '#c06a3a', -200, 900);
    g.fillStyle = '#6a5a2a'; for (let i = 0; i < 14; i++) { const w = 60 + i * 50; g.fillRect(360 - w / 2, 340 + i * 50, w, 50); g.fillStyle = i % 2 ? '#6a5a2a' : '#7a6a32'; }
    goldPile(g, 160, 1050, 60, T); goldPile(g, 560, 1060, 60, T);
    fig(g, { x: 360, y: 340, s: 90, c: '#14102a', crown: true });
    g.restore();
  }
  vignette(g, 0.6);
};

// ================= PASSAGE =================
S_.passage = (g, T, S) => {
  const L = S.L;
  const idx = S.cur(T); globalThis.__shot = 'vision' + Math.max(0, idx);
  // desk scene at bottom
  g.save(); cam(g, 360, 640, 1.0);
  sky(g, '#120e18', '#1e1820', 0, H);
  const hope = idx >= 1 ? (idx === 3 ? 0.3 : 1) : 0;
  g.restore();
  // vision panel (top)
  const vA = clamp(ramp(T, 0.3, 1.0));
  panel(g, 40, 70, 640, 520, vA, (v) => {
    const warm = [0.1, 0.8, 0.8, 0.0, 0.6, 1][Math.max(0, idx)];
    v.fillStyle = lg(v, 0, 70, 0, 590, [[0, `rgb(${lerp(30, 120, warm) | 0},${lerp(30, 80, warm) | 0},${lerp(50, 50, warm) | 0})`], [1, `rgb(${lerp(20, 60, warm) | 0},${lerp(20, 40, warm) | 0},${lerp(30, 30, warm) | 0})`]]); v.fillRect(40, 70, 640, 520);
    const lt = idx >= 0 ? T - L[idx].s : T;
    const G = 'rgba(15,10,20,0.95)';
    if (idx <= 0) {
      // endless toil: pushing stone up slope; coins pile
      v.fillStyle = '#2a2430'; poly(v, [[40, 590], [680, 590], [680, 260]]); v.fill();
      const k = clamp(lt * 0.08); const x = lerp(200, 560, k), y = lerp(560, 360, k);
      fillC(v, '#5a5060', x + 50, y - 50, 50); fig(v, { x, y: y + 10, s: 110, c: G, lean: 0.7, arms: [1.6, 1.6] });
      const cs = L[0].c; const riches = cs.length ? cs[cs.length - 1].s - L[0].s : 6;
      if (lt > riches - 0.3) { goldPile(v, 180, 560, 50 + (lt - riches) * 15, T); fig(v, { x: 300, y: 580, s: 130, c: G, arms: [0.9, 0.9] }); }
    } else if (idx === 1) {
      glow(v, 360, 330, 300, '#ffd890', 0.4);
      fig(v, { x: 320 - 0 + Math.sin(T) * 4, y: 520, s: 220, c: G, arms: [0.2, 0.9] }); fig(v, { x: 400, y: 520, s: 210, c: G, arms: [0.9, 0.2] });
    } else if (idx === 2) {
      const f = ramp(lt, 0.2, 0.9), up = ramp(lt, 1.4, 2.6);
      fig(v, { x: 420, y: 540, s: 210, c: G, arms: [lerp(0.2, 1.2, up), 1.4], lean: -0.3 * up });
      fig(v, { x: 320, y: 540, s: 210, c: G, rot: lerp(0, -1.3, f) * (1 - up) , arms: [0.2, lerp(0.3, 1.9, up)] });
      glow(v, 370, 400, 200, '#ffd890', 0.3 * up);
    } else if (idx === 3) {
      const f = ramp(lt, 0.3, 1.0);
      v.fillStyle = '#4a5068'; v.fillRect(40, 70, 640, 520); v.fillStyle = `rgba(0,0,0,${0.15 + 0.25 * f})`; v.fillRect(40, 70, 640, 520);
      v.fillStyle = 'rgba(200,215,255,0.18)'; poly(v, [[320, 70], [400, 70], [520, 590], [200, 590]]); v.fill();
      fig(v, { x: 360, y: 545, s: 210, c: G, rot: lerp(0, -1.45, f), alpha: 0.95 });
      fig(v, { x: 360 + 140, y: 540, s: 200, c: 'rgba(255,255,255,0.08)', alpha: 1 - f });
    } else if (idx === 4) {
      const second = L[4].c.length > 1 ? L[4].c[1].s - L[4].s : 2.2;
      for (let i = 0; i < 40; i++) { const k = (T * 0.15 + hash(i)) % 1; fillC(v, 'rgba(255,255,255,0.7)', 40 + hash(i * 3) * 640, 70 + k * 520, 2.5); }
      if (lt < second) { flame(v, 360, 520, 22, T); fig(v, { x: 300, y: 560, s: 150, c: G, kneel: true, arms: [0.5, 1.2] }); fig(v, { x: 420, y: 560, s: 150, c: G, kneel: true, arms: [1.2, 0.5] }); v.fillStyle = 'rgba(120,60,40,0.9)'; poly(v, [[250, 470], [470, 470], [480, 560], [240, 560]]); v.fill(); }
      else { v.fillStyle = 'rgba(30,40,80,0.4)'; v.fillRect(40, 70, 640, 520); const sh = Math.sin(T * 30) * 2; fig(v, { x: 360 + sh, y: 560, s: 160, c: G, kneel: true, arms: [-0.6, -0.6] }); }
    } else {
      glow(v, 360, 330, 320, '#ffe0a0', 0.5);
      braid(v, 120, 420, 600, 300, T, ramp(lt, 0.2, 2.0), undefined, 22, 12);
    }
  });
  // Solomon at desk (lower part)
  g.save(); cam(g, 360, 520, 1.0);
  const lookUp = idx >= 1 ? 1 : 0;
  const exK = [[0, 'weary|{"gy":0.7}'], [L[1].s - 0.4, 'awe|{"gy":-0.6,"gx":0.1}', 0.8], [L[2].s, 'tender|{"gy":-0.6}'], [L[3].s, 'hurt|{"gy":-0.5,"tears":0.6}'], [L[4].s, 'sad|{"gy":-0.6}'], [L[4].s + 2, 'hurt|{"gy":-0.6}'], [L[5].s, 'awe|{"gy":-0.6,"tears":0.5}'], [L[5].s + 1.6, 'teary|{"gy":-0.5}', 0.8]];
  actor(g, CH.solO, T, S, { x: 360, y: 700, s: 64, seed: 33, spk: 'SOLOMON', half: true, ex: exK, arms: [[0, A(0.4, -1.4, 0.4, -1.2)], [L[5].s + 1.4, A(0.4, -1.4, 0.9, -2.1)]], holdR: idx <= 0 ? PROP.quill(T) : null, nodK: [[0, 0.06], [L[1].s - 0.4, -0.06]] });
  g.fillStyle = '#3a2418'; g.fillRect(-100, 940, W + 200, 500);
  g.fillStyle = '#efe2c0'; g.fillRect(220, 925, 280, 40);
  flame(g, 600, 870, 14, T); g.fillStyle = '#efe7d6'; g.fillRect(590, 885, 20, 60);
  g.restore();
  glow(g, 600, 870, 500, '#ffb060', 0.18);
  vignette(g, 0.45);
};

// ================= KITCHEN 3 =================
S_.kitchen3 = (g, T, S) => {
  const L = S.L;
  const floorStart = L[2].c.length > 1 ? L[2].c[1].s : L[2].s + 2.4;
  if (T >= floorStart - 0.1 && T < L[3].s - 0.3) {
    const lt = T - floorStart;
    sky(g, '#0e0c14', '#16121c', 0, H);
    g.fillStyle = '#1e1a26'; g.fillRect(0, 0, W, 760); g.fillStyle = '#121018'; g.fillRect(0, 760, W, H);
    // doors fading away
    for (let i = 0; i < 3; i++) { const a = 1 - ramp(lt, 0.8 + i * 0.6, 1.4 + i * 0.6); g.save(); g.globalAlpha = a; g.fillStyle = '#3a2e26'; g.fillRect(80 + i * 210, 330, 130, 430); fillC(g, '#8a7a5a', 190 + i * 210, 560, 6); g.restore(); }
    // person on the floor hugging knees
    g.save(); g.translate(360, 860);
    globalThis.__shot = 'floor';
    g.fillStyle = '#3a3450'; g.beginPath(); g.moveTo(-70, 0); g.quadraticCurveTo(-90, -150, -20, -170); g.lineTo(40, -150); g.quadraticCurveTo(70, -80, 60, 0); g.closePath(); g.fill();
    fillE(g, '#4a4262', 40, -95, 55, 70, -0.2); fillC(g, '#2a2236', 10, -175, 42); fillE(g, '#5a5070', 55, -120, 30, 16, 0.6);
    fillE(g, 'rgba(0,0,0,0.35)', 0, 6, 120, 14);
    g.restore();
    txt(g, '0 doors', 360, 240, 54, 'rgba(255,255,255,0.75)', 'InterB', 'center', ramp(lt, 2.6, 3.0));
    vignette(g, 0.7);
    return;
  }
  return kitchenScene({
    shots: [[0, 'noa'], [L[1].s - 0.1, 'two'], [L[2].s - 0.1, 'teo'], [L[3].s - 0.3, 'noa'], [L[4].s - 0.2, 'two'], [L[5].s - 0.1, 'teo']],
    noa: { ex: [[0, 'realize|{"gx":0.4}'], [L[0].e, 'awe|{"gx":0.6}'], [L[2].s, 'thoughtful|{"gx":0.6,"gy":0.2}'], [L[3].s - 0.6, 'hurt|{"gy":0.7,"gx":0.1,"tears":0.6}', 0.9], [L[3].e + 0.5, 'teary|{"gx":0.6,"gy":0.2}', 1.0], [L[5].s + 0.5, 'teary|{"gx":0.5,"sm":0.6}']],
      arms: [[0, A(0.4, -2.4, 0.3, -1.3)], [L[1].s, TABLE], [L[3].s - 0.4, A(0.3, -1.6, 0.25, -1.35)]], tiltK: [[0, 0], [L[3].s - 0.4, 0.12], [L[4].e, 0]] },
    teo: { ex: [[0, 'tender|{"gx":-0.6}'], [L[1].s, 'firm|{"gx":-0.6,"bi":0.3}'], [L[2].s, 'sad|{"gx":-0.4}'], [L[3].s, 'tender|{"gx":-0.6,"gy":0.2}'], [L[4].s, 'tender|{"gx":-0.6,"bi":0.6}'], [L[5].s, 'warm|{"gx":-0.6}'], [L[5].s + 1.4, 'smirk|{"gx":-0.4,"gy":0.5}']],
      arms: [[0, TABLE], [L[4].s - 0.4, A(1.15, -0.9, 0.25, -1.35)], [L[5].s + 1.2, A(0.25, -1.35, 0.35, -1.0)]] },
  })(g, T, S);
};

// ================= LILIES =================
S_.lilies = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'wide'], [L[1].s - 0.2, 'kneel'], [L[2].s - 0.1, 'stand']]);
  const z = shot === 'wide' ? 1.0 + T * 0.02 : shot === 'kneel' ? 1.6 : 1.35;
  g.save(); cam(g, 360, shot === 'kneel' ? 560 : 540, z);
  sky(g, '#7ec0f0', '#e8f4e0', 0, 560); fillC(g, '#fff8d8', 600, 150, 46); glow(g, 600, 150, 260, '#fff0b0', 0.5);
  hills(g, 520, '#8ac070', 24, 2); hills(g, 600, '#6aa858', 26, 4);
  for (let i = 0; i < 16; i++) fig(g, { x: 30 + i * 46, y: 640 + (i % 3) * 14, s: 70, c: ['#a07a5a', '#6a7a9a', '#9a6a7a'][i % 3], kneel: true });
  for (let i = 0; i < 46; i++) lily(g, hash(i) * W * 1.2 - 60, 700 + hash(i * 3) * 600, 40 + hash(i * 5) * 30, T, i % 4 ? '#f6f1ff' : '#c8a0e0');
  const kneel = shot === 'kneel';
  actor(g, CH.jesus, T, S, { x: kneel ? 300 : 360, y: kneel ? 520 : 450, s: 60, seed: 51, spk: 'JESUS', kneel, turn: kneel ? 0.3 : 0,
    ex: kneel ? [[0, 'warm|{"gx":0.6,"gy":0.6}'], [L[1].s + 2.2, 'warm|{"gx":-0.2}']] : shot === 'stand' ? 'firm|{"sm":0.35,"bi":0.15}' : 'warm',
    arms: kneel ? [[0, A(0.3, -0.6, 0.9, -0.9)]] : [[0, A(0.2, 0.1, 0.2, 0.1)], [L[2].s + 0.6, A(0.2, 0.1, 1.2, -0.5)]] });
  if (kneel) lily(g, 430, 760, 100, T, '#ffffff', 0.4 + 0.2 * Math.sin(T * 2));
  g.restore();
  if (kneel) { const cs = L[1].c; const t0 = cs.length > 1 ? cs[1].s : L[1].s + 2; const a = ramp(T, t0, t0 + 0.5) * (1 - ramp(T, L[1].e - 0.4, L[1].e + 0.2)); if (a > 0) { g.save(); g.globalAlpha = a * 0.55; drawChar(g, CH.sol, { x: 560, y: 260, s: 46, t: T, seed: 33, ex: ex('proud'), h: 4.6 }); goldPile(g, 560, 480, 50, T); g.restore(); } }
  vignette(g, 0.35);
};

// ================= SWORD =================
S_.sword = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'pray'], [L[0].c.length > 3 ? L[0].c[3].s : L[0].s + 4, 'friends'], [L[1].s - 0.2, 'peter'], [L[2].s - 0.1, 'stop'], [L[3].s - 0.1, 'jesus'], [L[4].s - 0.1, 'drop']]);
  const garden = (z, cx, cy) => { g.save(); cam(g, cx, cy, z); sky(g, '#0a0e22', '#1a2038', 0, 700); stars(g, 50, 9, 0.8, T); fillC(g, '#e8e6d8', 140, 140, 26); hills(g, 620, '#101828', 16, 3); floor(g, 680, '#141c26', '#06080c'); olive(g, 90, 700, 300); olive(g, 640, 690, 280); };
  if (shot === 'pray') {
    garden(1.9, 360, 470);
    g.fillStyle = '#2a2a34'; fillE(g, '#2a2a34', 360, 760, 200, 60);
    actor(g, CH.jesus, T, S, { x: 360, y: 450, s: 62, kneel: true, seed: 51, ex: 'pray', arms: [[0, A(0.4, -2.4, 0.4, -2.4)]], tiltK: [[0, -0.1]] });
    g.restore(); tint(g, '#3a4a9a', 'soft-light', 0.3);
  } else if (shot === 'friends') {
    garden(1.3, 360, 540);
    actor(g, CH.disc1, T, S, { x: 200, y: 480, s: 54, seed: 61, turn: 0.4, ex: 'tender|{"gx":0.6}' });
    actor(g, CH.peter, T, S, { x: 520, y: 490, s: 56, seed: 62, turn: -0.4, ex: 'happy|{"gx":-0.6}' });
    actor(g, CH.jesus, T, S, { x: 360, y: 460, s: 58, seed: 51, ex: 'warm', arms: [[0, A(1.3, 0.3, 1.3, 0.3)]] });
    g.restore(); tint(g, '#3a4a9a', 'soft-light', 0.3);
  } else {
    const drop = shot === 'drop';
    garden(shot === 'peter' ? 1.8 : shot === 'jesus' ? 1.9 : 1.3, shot === 'jesus' ? 300 : shot === 'peter' ? 470 : 380, shot === 'drop' ? 560 : 480);
    torchBearers(g, T, 6, 560 - (T - L[1].s) * 10 + 200, 760, 0.95);
    const lt = T - L[2].s;
    const hold = T > L[2].s + 0.6;
    actor(g, CH.peter, T, S, { x: 480, y: 480, s: 58, seed: 62, spk: 'PETER', turn: -0.3,
      ex: [[0, 'frantic|{"gx":0.6}'], [L[1].e, 'angry|{"gx":0.7}'], [L[2].s + 0.6, 'surprised|{"gx":-0.6,"mo":0}'], [L[3].s + 0.6, 'ashamed|{"gx":-0.4}'], [L[4].s, 'hurt|{"gy":0.6,"tears":0.3}']],
      arms: [[0, A(0.3, -0.4, 1.8, -0.9)], [L[1].e, A(0.3, -0.4, 2.6, -0.4)], [L[2].s + 1.0, A(0.3, -0.4, 1.0, -0.6)], [L[4].s + 0.8, A(0.3, -0.3, 0.3, -0.2)]],
      holdR: T < L[4].s + 1.0 ? PROP.sword(0.4, null) : null });
    if (T > L[4].s + 1.0) { const f = ramp(T, L[4].s + 1.0, L[4].s + 1.4); PROP.sword(0, lerp(-0.2, 1.4, f))(g, 560, lerp(560, 760, f), 0, 58); }
    actor(g, CH.jesus, T, S, { x: 270, y: 470, s: 60, seed: 51, spk: 'JESUS', turn: 0.3,
      ex: [[0, 'worried|{"gx":0.6}'], [L[2].s, 'firm|{"gx":0.7,"bi":0.3}'], [L[3].s, 'tender|{"gx":0.9,"gy":0.1}'], [L[4].s, 'peace|{"gx":0.6}']],
      arms: [[0, A(0.2, 0.1, 0.3, 0.1)], [L[2].s, A(0.2, 0.1, 1.6, -0.15)], [L[3].s + 1.6, A(0.2, 0.1, 0.4, -0.5)]] });
    if (drop) { const a = ramp(T, L[4].s + 1.0, L[4].s + 2.0) * 0.45; if (a > 0) { g.save(); g.globalAlpha = a; drawChar(g, CH.davidY, { x: 270, y: 240, s: 40, t: T, seed: 3, ex: ex('peace'), kneel: true, aL: { s: 0.5, e: -1.6 }, aR: { s: 0.35, e: -1.5 }, holdL: PROP.lyre(T) }); g.restore(); glow(g, 270, 260, 160, '#ffe0a0', a); } }
    g.restore(); tint(g, '#3a4a9a', 'soft-light', 0.25); glow(g, 640, 600, 400, '#ff9a3a', 0.12);
  }
  vignette(g, 0.55);
};

// ================= RICH MAN =================
S_.richman = (g, T, S) => {
  const L = S.L;
  const shot = shotSel(T, [[0, 'sand'], [L[1].s - 0.2, 'talk'], [L[2].s + 0.6, 'away']]);
  if (shot === 'sand') {
    g.save(); cam(g, 360, 560, 1.1);
    sky(g, '#e8b070', '#f6dcb0', 0, 700); floor(g, 700, '#d8b888', '#a88858');
    const k = ramp(T, 1.5, 4.5);
    g.save(); g.globalAlpha = 1 - k * 0.6; palaceFacade(g, 360, 700, 200, '#e1b84c'); g.restore();
    for (let i = 0; i < 80 * k; i++) { const kk = (T * 0.3 + hash(i)) % 1; fillC(g, 'rgba(216,184,136,0.8)', 160 + hash(i * 3) * 400 + kk * 200, 500 + kk * 200, 3); }
    goldPile(g, 360, 820, 80 * (1 - k * 0.8), T);
    g.restore();
  } else {
    const away = shot === 'away';
    const lt = away ? T - (L[2].s + 0.6) : 0;
    g.save(); cam(g, 360, 520, away ? 1.25 : 1.5);
    sky(g, '#8ac0e8', '#f0e0b8', 0, 640); hills(g, 600, '#a8a070', 20, 3); floor(g, 660, '#d8c090', '#a89060');
    actor(g, CH.jesus, T, S, { x: 230, y: 450, s: 60, seed: 51, spk: 'JESUS', turn: 0.35,
      ex: away ? [[0, 'tender|{"gx":0.8,"bi":0.7}'], [3.0, 'warm|{"gx":-0.6}']] : [[0, 'warm|{"gx":0.7,"gy":0.4}'], [L[1].s + 2.6, 'tender|{"gx":0.7,"gy":0.4}']],
      arms: away ? [[0, A(0.2, 0.1, 0.4, -0.3)]] : [[0, A(0.2, 0.1, 0.3, -0.2)], [L[1].s + 2.4, A(0.2, 0.1, 1.3, -0.2)]] });
    const kneel = !away;
    actor(g, CH.rich, T, S, { x: away ? 500 + lt * 50 : 500, y: kneel ? 560 : 450 + Math.abs(Math.sin(T * 4)) * -4, s: 56, seed: 71, kneel, turn: away ? 0.3 : -0.4,
      ex: away ? 'sad|{"gy":0.7,"gx":0.5}' : [[0, 'excited|{"gx":-0.7,"gy":-0.5,"mo":0}'], [L[1].s + 2.3, 'worried|{"gx":-0.7,"gy":-0.5}'], [L[1].e - 0.6, 'sad|{"gy":0.5,"gx":0.2}']],
      arms: away ? [[0, A(0.5, -1.9, 0.3, -1.2)]] : [[0, A(0.6, -1.5, 0.6, -1.5)], [L[1].e - 0.8, A(0.5, -1.9, 0.6, -1.5)]], holdL: PROP.pouch(), alpha: away ? 1 - ramp(lt, 3.2, 4.4) : 1 });
    g.restore();
  }
  vignette(g, 0.4);
};

// ================= TABLE =================
S_.table = (g, T, S) => {
  const L = S.L;
  const c0 = L[0].c, c1 = L[1].c;
  const at = (arr, i, d) => arr[i] ? arr[i].s : d;
  const shot = shotSel(T, [[0, 'fire'], [at(c0, 1, 3), 'walk'], [at(c0, 2, 5), 'eat'], [at(c0, 3, 6), 'sleep'], [L[1].s - 0.1, 'meal'], [at(c1, 1, L[1].s + 1), 'purse'], [at(c1, 2, L[1].s + 2), 'leper'], [at(c1, 3, L[1].s + 3), 'outcast'], [L[2].s - 0.1, 'lift'], [L[3].s - 0.2, 'feet'], [L[4].s - 0.2, 'gather'], [L[5].s - 0.1, 'village']]);
  const night = (z, cx, cy) => { g.save(); cam(g, cx, cy, z); sky(g, '#0e1430', '#2a2440', 0, 640); stars(g, 70, 21, 1, T); hills(g, 600, '#1a1a30', 18, 6); floor(g, 640, '#2a2220', '#100c0a'); };
  const ring = (n, cx, cy, rx, ry, cols, fn) => { for (let i = 0; i < n; i++) { const a = PI + (i / (n - 1)) * PI; fn(cx + Math.cos(a) * rx, cy + Math.sin(a) * ry * -1, i); } };
  if (shot === 'fire' || shot === 'eat') {
    night(shot === 'fire' ? 1.1 + T * 0.03 : 1.15, 360, 640);
    const cols = ['#8a6d4a', '#5a7a6a', '#7a5a3a', '#6a5a7a', '#9a7a5a', '#5a6a8a'];
    for (let i = 0; i < 12; i++) { const a = PI * 1.05 + (i / 11) * PI * 0.9; fig(g, { x: 360 + Math.cos(a) * 280, y: 760 + Math.sin(a) * 90, s: 150, c: cols[i % 6], kneel: true, lean: Math.sin(T * 1.3 + i * 1.7) * 0.06, arms: shot === 'eat' ? [1.2 + Math.sin(T * 3 + i) * 0.3, 0.5] : [0.4 + Math.max(0, Math.sin(T * 1.1 + i * 2.3)) * 0.9, 0.4] }); }
    actor(g, CH.jesus, T, S, { x: 360, y: 600, s: 46, kneel: true, seed: 51, ex: shot === 'eat' ? 'joy|{"mo":0}' : 'warm', arms: [[0, A(0.6, -1.4, 0.6, -1.4)]] });
    flame(g, 360, 800, 40, T); glow(g, 360, 760, 400, '#ff9a3a', 0.35);
    if (shot === 'eat') { PROP.bread()(g, 300, 860, 0, 60); PROP.bread()(g, 420, 860, 0, 60); }
    
    g.restore();
  } else if (shot === 'walk') {
    g.save(); cam(g, 360, 560, 1.0); sky(g, '#f0905a', '#f6d0a0', 0, 700); fillC(g, '#fff0c0', 360, 560, 70); hills(g, 640, '#7a4a3a', 20, 2); floor(g, 700, '#9a6a4a', '#5a3a2a');
    const lw = T - at(c0, 1, 3); for (let i = 0; i < 13; i++) { const x = 40 + i * 50 + lw * 22, b = Math.abs(Math.sin(T * 4 + i)) * 6; fig(g, { x, y: 760 - b, s: i === 6 ? 150 : 140, c: i === 6 ? '#efe7d6' : '#3a2416', arms: [0.3 + Math.sin(T * 4 + i) * 0.3, 0.3 - Math.sin(T * 4 + i) * 0.3] }); }
    g.restore();
  } else if (shot === 'sleep') {
    night(1.1, 360, 600);
    flame(g, 360, 760, 26, T); glow(g, 360, 740, 300, '#ff9a3a', 0.3);
    for (let i = 0; i < 8; i++) { const x = 80 + i * 80, y = 860 + (i % 2) * 50; fillE(g, '#4a3a30', x, y, 50, 16, 0.05); fillC(g, '#6a4a3a', x - 46, y - 6, 12); }
    g.restore();
  } else if (shot === 'meal' || shot === 'purse' || shot === 'outcast') {
    night(1.6, 360, 520);
    flame(g, 620, 520, 14, T);
    g.fillStyle = '#5a3a22'; g.fillRect(-100, 680, W + 200, 300);
    const lt = T - (shot === 'meal' ? L[1].s : shot === 'purse' ? at(c1, 1, 0) : at(c1, 3, 0));
    const third = shot === 'outcast' ? V('rich', { top: '#5a5a3a', top2: '#4a4a2e', trim: null }) : CH.disc2;
    actor(g, CH.peter, T, S, { x: 160, y: 470, s: 52, half: true, seed: 62, turn: 0.4, ex: shot === 'outcast' ? 'joy' : 'happy|{"gx":0.6}', arms: [[0, A(0.4, -1.3, 0.8, -1.6)]] });
    actor(g, CH.jesus, T, S, { x: 360, y: 450, s: 54, half: true, seed: 51, ex: shot === 'outcast' ? 'joy' : 'warm', arms: [[0, A(0.8, -1.8, 0.8, -1.8)]], holdL: shot === 'meal' ? PROP.bread() : null });
    actor(g, third, T, S, { x: 560, y: 470, s: 52, half: true, seed: 63, turn: -0.4, ex: shot === 'outcast' ? 'teary|{"sm":0.9,"gx":-0.6}' : 'happy|{"gx":-0.6}', arms: [[0, A(0.8, -1.6, 0.4, -1.3)]], holdL: shot === 'purse' ? PROP.pouch() : null });
    PROP.cup()(g, 250, 700, 0, 50); PROP.cup()(g, 470, 700, 0, 50); PROP.bread()(g, 360, 715, 0, 60);
    g.restore(); glow(g, 360, 500, 500, '#ffb060', 0.15);
  } else if (shot === 'leper') {
    night(2.0, 360, 480);
    actor(g, CH.leper, T, S, { x: 450, y: 470, s: 60, seed: 81, turn: -0.4, ex: [[0, 'ashamed|{"gx":-0.4}'], [0.8, 'teary|{"gx":-0.6,"gy":-0.2,"tears":1}', 0.6]], arms: [[0, A(0.3, -1.6, 0.3, -1.7)]] });
    actor(g, CH.jesus, T, S, { x: 220, y: 460, s: 60, seed: 51, turn: 0.4, ex: 'tender|{"gx":0.7}', arms: [[0, A(0.2, 0.1, 1.5, -0.25)]] });
    g.restore();
  } else if (shot === 'lift') {
    const lt = T - L[2].s;
    night(1.3, 360, 580);
    const f = ramp(lt, 0.1, 0.6), up = ramp(lt, 1.2, 2.4);
    fig(g, { x: 360, y: 760, s: 180, c: '#5a4a3a', rot: lerp(0, -1.2, f) * (1 - up) });
    for (let i = 0; i < 3; i++) { const x = [230, 490, 360][i], y = [760, 760, 700][i]; fig(g, { x: lerp(x + (x - 360) * 0.8, x, ramp(lt, 0.6, 1.2)), y, s: 180, c: ['#8a6d4a', '#5a7a6a', '#efe7d6'][i], arms: [i === 0 ? 0.2 : 1.6, i === 1 ? 0.2 : 1.6], lean: (360 - x) * 0.002 }); }
    glow(g, 360, 660, 260, '#ffd890', 0.35 * up);
    g.restore();
  } else if (shot === 'feet') {
    night(1.7, 360, 520);
    flame(g, 620, 420, 12, T);
    actor(g, CH.peter, T, S, { x: 470, y: 380, s: 56, seed: 62, turn: -0.3, h: 4.4, ex: [[0, 'surprised|{"gx":-0.5,"gy":0.6,"mo":0}'], [1.2, 'teary|{"gx":-0.5,"gy":0.6}', 0.8]], arms: [[0, A(0.4, -0.8, 0.3, -0.4)]] });
    actor(g, CH.jesus, T, S, { x: 270, y: 540, s: 56, kneel: true, seed: 51, spk: 'JESUS', turn: 0.4, ex: [[0, 'tender|{"gy":0.6,"gx":0.5}'], [L[3].s + 0.4, 'warm|{"gx":0.6,"gy":-0.6}']], arms: [[0, A(0.8, -1.6, 0.8, -1.4)]] });
    PROP.basin()(g, 420, 780, 0, 70);
    g.restore();
  } else if (shot === 'gather') {
    night(1.35, 360, 520);
    g.fillStyle = '#5a3a22'; g.fillRect(-100, 700, W + 200, 300);
    actor(g, CH.disc1, T, S, { x: 140, y: 490, s: 50, half: true, seed: 61, turn: 0.4, ex: 'warm|{"gx":0.6}' });
    actor(g, CH.disc2, T, S, { x: 580, y: 490, s: 50, half: true, seed: 64, turn: -0.4, ex: 'warm|{"gx":-0.6}' });
    actor(g, CH.jesus, T, S, { x: 360, y: 460, s: 56, half: true, seed: 51, spk: 'JESUS', ex: 'warm', arms: [[0, A(1.2, -0.6, 1.2, -0.6)]] });
    for (let i = 0; i < 3; i++) { const x = [250, 360, 470][i]; PROP.cup()(g, x, 720, 0, 50); glow(g, x, 690, 90, '#ffd890', 0.3 * ramp(T, L[4].s + 0.5 + i * 0.5, L[4].s + 1 + i * 0.5)); }
    g.restore(); glow(g, 360, 480, 500, '#ffb060', 0.15);
  } else {
    const lt = T - L[5].s;
    g.save(); cam(g, 360, lerp(600, 520, ease(lt / 4)), lerp(1.2, 0.85, ease(lt / 4)));
    sky(g, '#0a1030', '#3a2a4a', -300, 700); stars(g, 80, 31, 1, T);
    hills(g, 640, '#1a1830', 26, 3); floor(g, 700, '#1a1828', '#0a0810');
    for (let i = 0; i < 40; i++) { const x = hash(i) * W, y = 720 + hash(i * 3) * 400; house(g, x, y, 34, 26, '#2a2030'); g.fillStyle = `rgba(255,200,110,${0.6 + 0.3 * Math.sin(T * 2 + i)})`; g.fillRect(x + 12, y - 18, 10, 10); }
    braid(g, 40, 560, 680, 420, T, ramp(lt, 1.0, 3.0), undefined, 14, 8);
    g.restore();
  }
  vignette(g, 0.45);
};

// ================= ENDING =================
S_.ending = (g, T, S) => {
  const L = S.L;
  const knockT = (require('./timeline.json').sfx.find(s => s.kind === 'knock') || { t: S.start + L[1].e + 0.55 }).t - S.start;
  const doorOpen = ramp(T, knockT + 1.2, knockT + 1.9);
  const seated = T > L[4].s - 0.2;
  const amiIn = T > knockT + 1.2;
  const shots = [[0, 'noa'], [L[1].s - 0.1, 'teo'], [knockT - 0.1, 'wide'], [L[2].s - 0.1, 'ami'], [L[3].s - 0.1, 'noa'], [L[4].s - 0.2, 'final']];
  let shot = shotSel(T, shots);
  if (shot === 'ami') {
    g.save(); cam(g, 600, 470, 1.9);
    S_._h.kitchenSet(g, T, { door: 1, rain: true });
    for (let i = 0; i < 30; i++) { const x = 650 + hash(i) * 80, y = 220 + ((hash(i * 2) * 540 + T * 500) % 540); line(g, 'rgba(180,200,255,0.5)', 2, x, y, x - 3, y + 16); }
    actor(g, CH.ami, T, S, { x: 650, y: 420, s: 66, seed: 91, spk: 'AMI', turn: -0.35, h: 4.8, ex: [[0, 'sheepish|{"gx":-0.6}'], [L[2].e - 0.2, 'worried|{"gx":-0.6,"sm":0.25}']], arms: [[0, A(0.9, -1.8, 0.9, -1.8)]], holdL: PROP.pot(), nodK: [[0, 0], [L[2].e - 0.4, 0.05]] });
    g.restore(); vignette(g, 0.45); return;
  }
  if (shot === 'final') {
    const lt = T - (L[4].s - 0.2);
    g.save(); cam(g, 360, lerp(600, 560, ease(lt / 6)), lerp(1.25, 1.05, ease(lt / 6)));
    S_._h.kitchenSet(g, T, { door: 0 });
    actor(g, CH.noa, T, S, { x: 170, y: 480, s: 70, half: true, turn: 0.35, seed: 2, ex: 'teary|{"gx":0.6,"tears":0.3}', arms: [[0, TABLE]] });
    actor(g, CH.ami, T, S, { x: 360, y: 455, s: 70, half: true, turn: 0, seed: 91, ex: [[0, 'joy|{"mo":0}'], [3, 'happy|{"gx":-0.5}']], arms: [[0, A(0.3, -1.4, 0.3, -1.4)]] });
    actor(g, CH.teo, T, S, { x: 555, y: 470, s: 72, half: true, turn: -0.35, seed: 5, ex: [[0, 'happy|{"gx":-0.5}'], [3, 'warm|{"gx":-0.6}']], arms: [[0, TABLE]] });
    S_._h.kitchenTable(g, T, { mugs: [[150, '#c8503a'], [360, '#2a7f86'], [570, '#3a6a9a']], braidSteam: true });
    // three steams braid into a cord rising to the lamp (faint near faces, bright above heads)
    const p = ramp(lt, 1.0, 5.0);
    for (let k = 0; k < 3; k++) {
      const x0 = [150, 360, 570][k]; const col = [[255, 220, 160], [170, 220, 255], [255, 170, 150]][k];
      const n = 48; let px = null, py = null;
      for (let i = 0; i <= n * p; i++) {
        const f = i / n; const y = lerp(690, 150, f);
        const conv = ease(clamp((690 - y - 330) / 140));
        const x = lerp(x0, 360, conv) + Math.sin(f * 20 + k * TAU / 3 + T * 0.8) * (4 + 14 * conv);
        if (px !== null) { const a = y > 420 ? 0.12 : 0.85 * ease((420 - y) / 60); g.strokeStyle = `rgba(${col[0]},${col[1]},${col[2]},${a})`; g.lineWidth = y > 420 ? 4 : 7; g.lineCap = 'round'; g.beginPath(); g.moveTo(px, py); g.lineTo(x, y); g.stroke(); }
        px = x; py = y;
      }
    }
    glow(g, 360, 170, 220, '#ffe7a8', 0.3 * p);
    g.restore();
    const ta = ramp(T, S.dur - 2.6, S.dur - 1.8);
    if (ta > 0) { g.save(); g.fillStyle = `rgba(10,8,14,${0.55 * ta})`; g.fillRect(0, 120, W, 150); g.restore(); txt(g, 'A Table Instead of a Palace', 360, 190, 44, '#ffe7a8', 'SerifB', 'center', ta); txt(g, 'Ecclesiastes 4:9–12', 360, 240, 28, '#ffffff', 'InterSBI', 'center', ta * 0.9); }
    vignette(g, 0.4); return;
  }
  return kitchenScene({
    shots: [[0, shot]],
    set: () => ({ door: doorOpen, rain: true }),
    noa: { ex: [[0, 'tender|{"gy":0.7}'], [L[0].e, 'tender|{"gx":0.6}'], [knockT, 'surprised|{"gx":0.9,"mo":0}', 0.25], [knockT + 0.8, 'skeptical|{"gx":0.9}'], [knockT + 1.9, 'awe|{"gx":0.9}'], [L[3].s - 0.3, 'teary|{"gx":0.9,"sm":0.9}']],
      arms: [[0, A(0.3, -1.4, 0.7, -2.0)], [L[0].e, TABLE]], turnK: [[0, 0.35], [knockT, 0.7]], tiltK: [[0, 0.08], [knockT, -0.05]] },
    teo: { ex: [[0, 'tender|{"gx":-0.6}'], [L[1].s, 'warm|{"gx":-0.6}'], [knockT, 'surprised|{"gx":0.9,"mo":0}', 0.25], [knockT + 1.0, 'smirk|{"gx":0.9}'], [knockT + 1.9, 'happy|{"gx":0.9}']],
      arms: [[0, TABLE]], turnK: [[0, -0.35], [knockT, 0.35]] },
    front: (g2, T2) => { if (T2 < L[1].s) { g2.save(); g2.translate(270, 758); braid(g2, -60, 0, 60, -6, T2, ramp(T2, 0.3, 2.4), ['#7a5a2a', '#2a4a7a', '#8a2a2a'], 6, 3); g2.restore(); } },
  })(g, T, S);
};

module.exports = S_;
