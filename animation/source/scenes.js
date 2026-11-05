const C = require('./core');
const { W, H, PI, TAU, clamp, lerp, ease, easeOut, ramp, hash, noise1, kf, ex, CH, ell, circ, fillE, fillC, rrect, poly, line, shade, rgba, lg, rg, glow, drawChar, fig, PROP, flame } = C;

const S_ = {};
function cam(g, cx, cy, z) { g.translate(W / 2, H / 2 * 0.82); g.scale(z, z); g.translate(-cx, -cy); }
function actor(g, ch, T, S, o) {
  const p = Object.assign({ t: T + (o.seed || 1) * 10, seed: 1 }, o);
  p.ex = o.ex ? (Array.isArray(o.ex) ? kf(T, o.ex, o.tr) : C.resolve(o.ex)) : ex('neutral');
  if (o.arms) { const a = kf(T, o.arms, 0.5); p.aL = a.L; p.aR = a.R; }
  if (o.spk) p.talk = S.mouth(o.spk, T);
  if (o.turnK) p.turn = kf(T, o.turnK);
  if (o.tiltK) p.tilt = kf(T, o.tiltK);
  if (o.nodK) p.nod = kf(T, o.nodK);
  if (o.gaze) { const gz = kf(T, o.gaze); p.ex = Object.assign({}, p.ex, { gx: gz.x, gy: gz.y }); }
  drawChar(g, ch, p);
}
const A = (sL, eL, sR, eR) => ({ L: { s: sL, e: eL }, R: { s: sR, e: eR } });
const REST = A(0.15, 0.1, 0.15, 0.1);
const TABLE = A(0.25, -1.35, 0.25, -1.35);
const sky = (g, a, b, y0 = 0, y1 = H) => { g.fillStyle = a; g.fillRect(-400, y0 - 600, W + 800, 601); g.fillStyle = lg(g, 0, y0, 0, y1, [[0, a], [1, b]]); g.fillRect(-400, y0, W + 800, y1 - y0); g.fillStyle = b; g.fillRect(-400, y1 - 1, W + 800, 600); };
function vignette(g, a = 0.55) { g.fillStyle = rg(g, W / 2, H * 0.42, H * 0.25, H * 0.8, [[0, 'rgba(0,0,0,0)'], [1, `rgba(0,0,0,${a})`]]); g.fillRect(0, 0, W, H); }
function tint(g, c, mode = 'multiply', a = 1) { g.save(); g.globalCompositeOperation = mode; g.globalAlpha = a; g.fillStyle = c; g.fillRect(0, 0, W, H); g.restore(); }
function hills(g, y, c, amp, seed, freq = 0.006) {
  g.fillStyle = c; g.beginPath(); g.moveTo(-300, H + 400);
  for (let x = -300; x <= W + 300; x += 20) g.lineTo(x, y + Math.sin(x * freq + seed) * amp + Math.sin(x * freq * 2.3 + seed * 2) * amp * 0.4);
  g.lineTo(W + 300, H + 400); g.closePath(); g.fill();
}
function stars(g, n, seed, a = 1, t = 0) { for (let i = 0; i < n; i++) { const x = hash(i + seed) * W, y = hash(i * 3 + seed) * H * 0.5; fillC(g, `rgba(255,255,240,${a * (0.4 + 0.6 * hash(i * 7)) * (0.8 + 0.2 * Math.sin(t * 2 + i))})`, x, y, 1 + hash(i * 5) * 1.8); } }
function sheep(g, x, y, s, t) { const b = Math.sin(t * 2 + x) * s * 0.03; for (let i = 0; i < 6; i++) fillC(g, '#f3efe6', x + Math.cos(i) * s * 0.35, y - s * 0.3 + Math.sin(i * 2) * s * 0.12 + b, s * 0.28); fillE(g, '#3a3330', x + s * 0.55, y - s * 0.35 + b, s * 0.18, s * 0.14); line(g, '#3a3330', s * 0.08, x - s * 0.25, y - s * 0.1, x - s * 0.25, y + s * 0.15); line(g, '#3a3330', s * 0.08, x + s * 0.25, y - s * 0.1, x + s * 0.25, y + s * 0.15); }
function petals(g, t, n, seed, cols) { for (let i = 0; i < n; i++) { const x = ((hash(i + seed) * W + t * 20 * (hash(i) - 0.5)) % W + W) % W; const k = ((hash(i * 9 + seed) * H + t * (50 + 40 * hash(i * 2))) % (H * 0.8)) / (H * 0.8); g.save(); g.globalAlpha *= Math.min(1, k * 8, (1 - k) * 8); fillE(g, cols[i % cols.length], x, k * H * 0.8, 6, 3.5, t * 2 + i); g.restore(); } }
function smoke(g, t, x, y, n, seed, c = 'rgba(40,30,30,0.25)') { for (let i = 0; i < n; i++) { const k = (t * 0.15 + hash(i + seed)) % 1; g.save(); g.globalAlpha *= Math.min(1, k * 6, (1 - k) * 3); fillC(g, c, x + noise1(k * 4 + i, seed) * 60 + k * 40, y - k * 500, 30 + k * 90); g.restore(); } }
function house(g, x, y, w, h, c) { g.fillStyle = c; g.fillRect(x, y - h, w, h); g.fillRect(x - 4, y - h - 8, w + 8, 10); }
function txt(g, s, x, y, size, col, font = 'SerifB', align = 'center', a = 1) { g.save(); g.globalAlpha *= a; g.font = `${size}px ${font}`; g.textAlign = align; g.fillStyle = col; g.fillText(s, x, y); g.restore(); }
function braid(g, x0, y0, x1, y1, t, prog, cols = ['#e6c35c', '#7fc4ff', '#ff8f7a'], wAmp = 16, lw = 10) {
  const n = 80, m = Math.floor(n * clamp(prog));
  for (let k = 0; k < 3; k++) {
    g.strokeStyle = cols[k]; g.lineWidth = lw; g.lineCap = 'round'; g.beginPath();
    for (let i = 0; i <= m; i++) {
      const f = i / n; const x = lerp(x0, x1, f), y = lerp(y0, y1, f);
      const dx = y1 - y0, dy = -(x1 - x0); const L = Math.hypot(dx, dy);
      const off = Math.sin(f * 22 + k * TAU / 3 + t * 0.6) * wAmp;
      const px = x + dx / L * off, py = y + dy / L * off;
      if (i === 0) g.moveTo(px, py); else g.lineTo(px, py);
    }
    g.stroke();
  }
}

// ================= KITCHEN =================
function kitchenSet(g, T, o = {}) {
  g.fillStyle = '#2c2230'; g.fillRect(-300, -300, W + 600, 400); sky(g, '#2c2230', '#3d2c2c', 0, 760); g.fillStyle = '#3d2c2c'; g.fillRect(-300, 0, 300, 760); g.fillRect(W, 0, 300, 760);
  // wallpaper stripes subtle
  g.fillStyle = 'rgba(255,220,180,0.03)'; for (let x = 0; x < W; x += 60) g.fillRect(x, 0, 30, 760);
  // window
  g.fillStyle = '#5a3d2a'; rrect(g, 236, 150, 248, 300, 10); g.fill();
  g.fillStyle = lg(g, 0, 160, 0, 440, [[0, '#0f1a3a'], [1, '#27406b']]); g.fillRect(250, 164, 220, 272);
  g.save(); g.beginPath(); g.rect(250, 164, 220, 272); g.clip();
  for (let i = 0; i < 18; i++) fillC(g, 'rgba(255,255,230,0.8)', 250 + hash(i) * 220, 164 + hash(i * 3) * 200, 1.2 + hash(i * 5));
  fillC(g, '#f3ecd0', 420, 210, 22); fillC(g, '#27406b', 410, 203, 20);
  if (o.rain) for (let i = 0; i < 30; i++) { const x = 250 + hash(i) * 220, y = 164 + ((hash(i * 2) * 272 + T * 400) % 272); line(g, 'rgba(180,200,255,0.4)', 1.5, x, y, x - 3, y + 14); }
  hills(g, 400, '#14203a', 14, 2, 0.02);
  g.restore();
  line(g, '#5a3d2a', 8, 360, 164, 360, 436); line(g, '#5a3d2a', 8, 250, 300, 470, 300);
  // shelf left
  g.fillStyle = '#5a3d2a'; g.fillRect(20, 280, 160, 12);
  fillE(g, '#7a9a6a', 50, 262, 18, 20); g.fillStyle = '#c8763a'; g.fillRect(80, 240, 30, 40); g.fillStyle = '#d8c8a8'; g.fillRect(120, 250, 26, 30);
  // plant right
  g.fillStyle = '#7a4a2a'; g.fillRect(560, 420, 50, 50);
  for (let i = 0; i < 7; i++) { g.save(); g.translate(585, 425); g.rotate(-1.2 + i * 0.4 + Math.sin(T * 0.8 + i) * 0.03); fillE(g, i % 2 ? '#4f7a4a' : '#3e6a3a', 0, -45, 12, 45); g.restore(); }
  // door (right)
  const door = o.door || 0;
  g.fillStyle = '#4a3020'; g.fillRect(640, 210, 90, 560);
  if (door > 0) {
    g.fillStyle = lg(g, 640, 0, 730, 0, [[0, '#1a2440'], [1, '#2a3a60']]); g.fillRect(646, 216, 78 * door, 554);
    g.fillStyle = '#6a4630'; g.fillRect(646 + 78 * door, 216, 78 * (1 - door), 554);
  } else { g.fillStyle = '#6a4630'; g.fillRect(646, 216, 78, 554); fillC(g, '#d8b04a', 658, 500, 6); }
  // lamp
  line(g, '#222', 3, 360, 0, 360, 100);
  g.fillStyle = '#2a2a2a'; poly(g, [[320, 128], [400, 128], [380, 96], [340, 96]]); g.fill();
  fillE(g, '#ffe7a8', 360, 130, 28, 8);
  g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = lg(g, 0, 130, 0, 780, [[0, 'rgba(255,200,120,0.18)'], [1, 'rgba(255,200,120,0)']]); poly(g, [[330, 130], [390, 130], [700, 780], [20, 780]]); g.fill(); g.restore();
}
function kitchenTable(g, T, o = {}) {
  g.fillStyle = '#6a4228'; poly(g, [[0, 735], [W, 735], [W, 800], [0, 800]]); g.fill();
  g.fillStyle = '#7d5032'; g.fillRect(0, 725, W, 18);
  g.fillStyle = lg(g, 0, 800, 0, H, [[0, '#3a2418'], [1, '#160d09']]); g.fillRect(-300, 800, W + 600, H);
  // mugs with steam
  const mugs = o.mugs || [[150, '#c8503a'], [560, '#3a6a9a']];
  for (const [x, c] of mugs) {
    g.fillStyle = c; rrect(g, x - 22, 695, 44, 46, 6); g.fill();
    g.strokeStyle = c; g.lineWidth = 6; g.beginPath(); g.arc(x + 26, 715, 10, -1.3, 1.3); g.stroke();
    if (!o.braidSteam) for (let k = 0; k < 2; k++) { g.strokeStyle = 'rgba(255,255,255,0.18)'; g.lineWidth = 4; g.beginPath(); for (let i = 0; i < 20; i++) { const y = 690 - i * 5; const xx = x + Math.sin(i * 0.4 + T * 2 + k * 2) * 6 + k * 8 - 4; i ? g.lineTo(xx, y) : g.moveTo(xx, y); } g.stroke(); }
  }
  // notebook
  g.save(); g.translate(270, 760); g.rotate(-0.06);
  g.fillStyle = '#f2ead8'; g.fillRect(-80, -30, 160, 60); line(g, '#c9bfa8', 2, 0, -30, 0, 30);
  g.restore();
  // bible
  g.fillStyle = '#3a1f1a'; g.save(); g.translate(460, 758); g.rotate(0.05); g.fillRect(-60, -24, 120, 46); g.fillStyle = '#d8b04a'; g.fillRect(-60, 18, 120, 4); g.restore();
}
// generic kitchen scene builder: cfg = {shots:[[t,'two'|'noa'|'teo']], noa:{ex,arms,turnK}, teo:{...}, extra}
function kitchenScene(cfg) {
  return (g, T, S) => {
    let shot = cfg.shots[0][1]; for (const [t, s] of cfg.shots) if (T >= t) shot = s; globalThis.__shot = shot;
    const z = shot === 'noa' ? [215, 545, 2.1] : shot === 'teo' ? [515, 540, 2.1] : shot === 'wide' ? [370, 600, 1.0] : [360, 590, 1.22 + T * 0.004];
    g.save(); cam(g, z[0], z[1], z[2]);
    kitchenSet(g, T, cfg.set ? cfg.set(T) : {});
    if (cfg.behind) cfg.behind(g, T, S);
    actor(g, CH.noa, T, S, Object.assign({ x: 200, y: 470, s: 76, half: true, turn: 0.35, spk: 'NOA', seed: 2, arms: [[0, TABLE]] }, cfg.noa));
    actor(g, CH.teo, T, S, Object.assign({ x: 525, y: 462, s: 80, half: true, turn: -0.35, spk: 'TEO', seed: 5, arms: [[0, TABLE]] }, cfg.teo));
    if (cfg.mid) cfg.mid(g, T, S);
    kitchenTable(g, T, cfg.table ? cfg.table(T) : {});
    if (cfg.front) cfg.front(g, T, S);
    g.restore();
    if (cfg.overlay) cfg.overlay(g, T, S);
    vignette(g, 0.5);
  };
}

// ================= HOOK =================
S_.hook = (g, T, S) => {
  globalThis.__shot = 'hill';
  const z = 1.25 + T * 0.03;
  g.save(); cam(g, 380, 640, z);
  sky(g, '#f7c873', '#f3a25a', 0, 700);
  fillC(g, 'rgba(255,240,200,0.9)', 520, 330, 60); glow(g, 520, 330, 260, '#ffdca0', 0.6);
  hills(g, 560, '#d98f4e', 30, 1); hills(g, 640, '#b9773d', 26, 3); hills(g, 760, '#8f6a2e', 30, 5, 0.004); g.fillStyle = '#8f6a2e'; g.fillRect(-200, H - 5, W + 400, 400);
  for (const [x, y] of [[90, 760], [600, 800], [520, 900], [140, 920]]) sheep(g, x, y, 60, T);
  // rock
  g.fillStyle = '#7a6650'; g.beginPath(); g.moveTo(250, 830); g.quadraticCurveTo(270, 760, 380, 755); g.quadraticCurveTo(500, 760, 520, 830); g.closePath(); g.fill(); fillE(g, 'rgba(0,0,0,0.15)', 385, 835, 150, 18);
  const strum = (T % 0.6) / 0.6;
  const look = ramp(T, 3.0, 3.6);
  actor(g, CH.davidY, T, S, { x: 380, y: 560, s: 74, kneel: true, turn: lerp(0.1, 0, look), seed: 3,
    ex: [[0, 'peace|{"lu":0.85,"sm":0.5}'], [2.9, 'happy|{"gx":0,"gy":-0.1}', 0.5], [4.2, 'thoughtful|{"gx":0.0,"gy":-0.4,"sm":0.25}', 0.7]],
    aL: { s: 0.5, e: -1.6 }, aR: { s: 0.35 + Math.sin(T * 10) * 0.08, e: -1.5 + Math.sin(T * 10) * 0.12 }, holdL: PROP.lyre(strum) });
  // ghost crown appears on "succeeds completely"
  const cr = ramp(T, 2.6, 3.6);
  if (cr > 0) { g.save(); g.globalAlpha = cr * 0.55; g.translate(380, 470 - cr * 30); g.fillStyle = '#ffe28a'; poly(g, [[-60, 0], [-60, -40], [-30, -15], [0, -55], [30, -15], [60, -40], [60, 0]]); g.fill(); glow(g, 0, -20, 140, '#ffd36a', cr * 0.5); g.restore(); }
  // ghost crowd on horizon
  for (let i = 0; i < 14; i++) fig(g, { x: 40 + i * 50, y: 600, s: 60, c: `rgba(90,50,30,${0.35 * cr})`, arms: [2.6 + Math.sin(T * 6 + i) * 0.2, 2.6] });
  g.restore();
  petals(g, T, 10, 3, ['rgba(255,255,255,0.6)']);
  vignette(g, 0.35);
};

// ================= KITCHEN 1 =================
S_.kitchen1 = (g, T, S) => {
  const L = S.L;
  const showWords = T > L[0].s + 1.6 && T < L[1].s + 0.5;
  return kitchenScene({
    shots: [[0, 'two'], [L[1].s - 0.1, 'noa'], [L[2].s - 0.1, 'teo'], [L[4].s - 0.1, 'noa'], [L[5].s - 0.1, 'two'], [L[7].s - 0.1, 'noa']],
    noa: {
      ex: [[0, 'excited'], [L[0].s + 2.2, 'excited|{"gx":0.3,"gy":-0.4}'], [L[0].e - 0.6, 'joy'], [L[1].s, 'happy'], [L[1].s + 2.6, 'peace|{"lu":0.5,"sm":0.5}'], [L[1].s + 3.6, 'determined'],
           [L[2].s, 'happy|{"gx":0.6}'], [L[3].s + 0.8, 'neutral|{"gx":0.6,"bi":0.2}'], [L[4].s, 'skeptical'], [L[5].s + 1.6, 'worried|{"gx":0.6}'], [L[6].s + 0.5, 'thoughtful|{"gx":0.5,"gy":0}'], [L[7].s - 0.3, 'determined|{"sm":0.3}'], [L[7].e + 0.3, 'determined|{"gx":0.7,"gy":0.4}']],
      arms: [[0, TABLE], [L[0].s + 0.2, A(0.7, -2.2, 0.8, -2.0)], [L[0].s + 2.0, A(0.9, -2.7, 0.3, -1.0)], [L[0].s + 3.2, A(0.3, -1.0, 1.0, -2.6)], [L[1].s, A(0.5, -2.0, 0.6, -1.9)],
             [L[1].s + 2.6, A(0.9, -0.3, 0.9, -0.3)], [L[1].s + 3.8, A(0.2, -1.2, 1.6, -2.6)], [L[2].s, TABLE], [L[4].s, A(0.2, -1.4, 0.7, -2.5)], [L[5].s, TABLE], [L[7].s, A(0.3, -2.1, 0.3, -2.1)]],
      tiltK: [[0, 0], [L[1].s + 2.6, -0.12], [L[1].s + 3.8, 0.04], [L[4].s, 0.1], [L[5].s, 0]],
      turnK: [[0, 0.35], [L[1].s, 0.15], [L[2].s, 0.4]],
    },
    teo: {
      ex: [[0, 'smirk|{"gx":-0.6}'], [L[1].s, 'happy|{"gx":-0.6}'], [L[2].s, 'warm|{"gx":-0.3}'], [L[3].s, 'firm|{"gx":-0.2,"bi":0.2}'], [L[4].s, 'neutral|{"gx":-0.6}'], [L[5].s, 'firm|{"gx":-0.6,"bi":0.35}'], [L[6].s + 0.4, 'tender|{"gx":-0.6}'], [L[7].s, 'smirk|{"gx":-0.6}'], [L[7].e + 0.3, 'happy|{"gx":-0.2,"gy":0.5}']],
      arms: [[0, TABLE], [L[2].s + 1.4, A(0.25, -1.35, 0.6, -2.3)], [L[3].s + 0.5, A(0.25, -1.35, 0.9, -2.9)], [L[4].s, TABLE], [L[6].s, A(0.6, -2.3, 0.6, -2.3)], [L[7].e + 0.2, A(0.25, -1.35, 0.35, -1.0)]],
      nodK: [[0, 0], [L[2].s + 0.3, 0.06], [L[2].s + 0.8, -0.02], [L[2].s + 1.3, 0.04], [L[2].s + 1.8, 0]],
      tiltK: [[0, 0], [L[3].s, -0.06], [L[5].s, 0.05], [L[6].s, -0.03]],
    },
    overlay: (g2, T2) => {
      if (!showWords) return;
      const cs = S.L[0].c;
      const words = [['DAVID', '#ff9d6e'], ['SOLOMON', '#e6c35c'], ['JESUS', '#b8e0ff']];
      const ts = [L[0].s + 1.7, L[0].s + 2.35, L[0].s + 3.0];
      words.forEach(([w, c], i) => { const a = ramp(T, ts[i], ts[i] + 0.3) * (1 - ramp(T, L[1].s, L[1].s + 0.4)); if (a <= 0) return; txt(g2, w, 140 + i * 220, 120 + (1 - a) * 20, 40, c, 'InterB', 'center', a); if (i < 2) txt(g2, '→', 250 + i * 220, 118, 36, '#fff', 'DV', 'center', ramp(T, ts[i + 1] - 0.1, ts[i + 1] + 0.2) * a); });
      if (T > L[0].s + 4.0) { const a2 = ramp(T, L[0].s + 4.0, L[0].s + 4.4) * (1 - ramp(T, L[1].s, L[1].s + 0.4)); g2.save(); g2.globalAlpha = a2; g2.strokeStyle = '#ffffff'; g2.lineWidth = 4; g2.beginPath(); g2.moveTo(60, 150); g2.quadraticCurveTo(360, 210, 660, 150); g2.stroke(); g2.restore(); }
    },
  })(g, T, S);
};

module.exports = S_;
module.exports._h = { cam, actor, A, REST, TABLE, sky, vignette, tint, hills, stars, sheep, petals, smoke, house, txt, braid, kitchenScene, kitchenSet, kitchenTable };
