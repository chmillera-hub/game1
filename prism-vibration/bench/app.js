// APP-BEGIN
(() => {
const $ = id => document.getElementById(id);
const TAU = Math.PI * 2;
const BW = 960, BH = 420;                 // wall image buffer (full quality)
const SPOT_SIGMA = 1.3, SLIT_H = 30;      // mm
const C_LIGHT = 2.998e11;                 // mm/s

const DEFAULTS = { target: 'prism', wave: 'sine', slideH: 0, turnH: 0, fH: 100, slideV: 0, turnV: 0, fV: 100, phase: 90,
  light: 'white', beam: 'spot', theta: 64, dist: 1.0 };
const PRESETS = [
  { id: 'still', name: 'Still prism', s: {},
    note: '<b>A still prism.</b> A clean spectrum about 18 cm wide. Violet is bent most and spreads widest; red is bent least.' },
  { id: 'slideH', name: 'Shake sideways 5 mm', s: { slideH: 5 },
    note: '<b>Sliding the prism barely matters.</b> Every colour moves the same 2.5–3.4 mm, so nothing overlaps. Sliding changes no angles, and angles are what separate the colours.' },
  { id: 'slideV', name: 'Shake up/down 5 mm', s: { slideV: 5 },
    note: '<b>Nothing happens at all.</b> The prism looks identical all along its edge, so sliding it along that edge changes no ray. The table reads 0.0 mm.' },
  { id: 'lightV', name: 'Shake the light up/down', s: { target: 'light', slideV: 5 },
    note: '<b>The rainbow smears into a 10 mm tall band</b> with brighter top and bottom edges, because the light lingers at the turning points. Each colour moves straight up and down, so colours never mix.' },
  { id: 'rock', name: 'Rock ±4.5° → pink', s: { turnH: 4.5, theta: 75 },
    note: '<b>Pink appears</b> (about −3 cm), a colour that is in no rainbow. The rainbow spends most of its time at the two ends of its swing, so you see two ghost rainbows. Where one\'s red lands on the other\'s violet, the light adds up to pink.' },
  { id: 'square', name: 'Snap ±4.5° → magenta', s: { turnH: 4.5, theta: 75, wave: 'square' },
    note: '<b>Two crisp rainbows overlap</b>, with vivid magenta where red meets violet. Try "Steady" instead: the light spreads evenly and the middle washes out to grey.' },
  { id: 'freeze', name: 'Freeze one colour', s: { turnH: 1.5, theta: 64.82 },
    note: '<b>Blue-green (480 nm) barely moves</b> (see the table) while violet and red swing in opposite directions. The prism rocks about that colour\'s minimum-deviation angle, where its bending stops changing. Switch to Slow motion to watch the rainbow breathe around it, or move the prism angle to freeze a different colour.' },
  { id: 'mercury', name: 'Mercury lines split', s: { turnH: 2.5, theta: 65.88, light: 'mercury' },
    note: '<b>Each spectral line splits into a pair</b> (the turning points again), except the 436 nm line, which sits at its minimum deviation and stays single and sharp.' },
  { id: 'circle', name: 'Light moves in a circle', s: { target: 'light', slideH: 5, slideV: 5, phase: 90 },
    note: '<b>Each colour traces its own small ring.</b> Left-right and up-down motion add as separate directions, and the rainbow becomes a ribbon with bright rims. The rings are slightly squashed because sideways light shifts are scaled by the prism.' },
  { id: 'smile', name: 'Aim the light up/down ±6°', s: { target: 'light', turnV: 6 },
    note: '<b>The rainbow curves into a smile.</b> Light that crosses the prism at a slant meets the glass at a steeper effective angle and bends more, so every colour slides toward the violet side as it rises or falls. Violet slides the furthest.' },
  { id: 'nod', name: 'Nod the prism ±6°', s: { turnV: 6 },
    note: '<b>The rainbow swings like a fan.</b> Nodding the prism lifts violet higher than red, so the line tilts. Shaking it up and down sweeps out a bow-tie shape.' },
  { id: 'lissajous', name: 'Two speeds at once', s: { target: 'light', turnH: 0.6, fH: 100, slideV: 6, fV: 150, phase: 0 },
    note: '<b>Different left-right and up-down speeds</b> (100 and 150 per second) make each colour trace a figure-of-eight pattern (see the path panel). Averaged by your eye, the figures fill a band that is brightest along its top and bottom edges, where the motion turns around.' },
  { id: 'camera', name: 'Film it with a phone', s: { turnH: 3, theta: 75, fH: 240, beam: 'slit', view: 'cam' },
    note: '<b>A phone camera reads its sensor row by row</b> over about 25 ms. With the prism rocking 240 times a second, each row sees the rainbow at a different moment, and straight bands become snakes. Set the speed to 30 per second to see the camera make fast shaking look slow.' },
];

let S = { ...DEFAULTS, ...PRESETS[4].s };
let view = 'eye';
let activePreset = 'rock';

// ---------- controls
const fToS = f => Math.round(Math.log10(Math.max(1, f)) / 3 * 100);
const sToF = s => { const f = Math.pow(10, s / 100 * 3); return f < 10 ? Math.round(f * 10) / 10 : f < 100 ? Math.round(f) : Math.round(f / 5) * 5; };
const sliders = ['slideH', 'turnH', 'fH', 'slideV', 'turnV', 'fV', 'phase', 'theta', 'dist'];
function writeControls() {
  for (const k of sliders) $(k).value = (k === 'fH' || k === 'fV') ? fToS(S[k]) : S[k];
  for (const g of ['target', 'wave', 'light', 'beam']) $(`${g}-${S[g]}`).checked = true;
  $(`view-${view}`).checked = true;
  writeOutputs();
}
function writeOutputs() {
  const light = S.target === 'light';
  $('slideH-o').textContent = `±${S.slideH.toFixed(1)} mm`;
  $('slideV-o').textContent = `±${S.slideV.toFixed(1)} mm`;
  $('turnH-o').textContent = `±${S.turnH.toFixed(1)}°`;
  $('turnV-o').textContent = `±${S.turnV.toFixed(1)}°`;
  $('fH-o').textContent = `${S.fH} per second`;
  $('fV-o').textContent = `${S.fV} per second`;
  $('phase-o').textContent = S.phase === 0 ? 'together' : S.phase === 90 ? '¼ cycle apart' : S.phase === 180 ? 'opposite' : `${S.phase}°`;
  $('theta-o').textContent = `${S.theta.toFixed(1)}°`;
  $('dist-o').textContent = `${S.dist.toFixed(1)} m`;
  $('turnH-l').textContent = light ? 'Aim left/right' : 'Rock (turn left/right)';
  $('turnV-l').textContent = light ? 'Aim up/down' : 'Nod (tilt up/down)';
  $('slideH').previousElementSibling.previousElementSibling.textContent = light ? 'Slide the light sideways' : 'Slide the prism sideways';
  $('slideV').previousElementSibling.previousElementSibling.textContent = light ? 'Slide the light up/down' : 'Slide the prism up/down';
  const frozen = invMinDev(S.theta);
  $('thetaHint').textContent = frozen ? `At this angle ${Math.round(frozen)} nm is at minimum deviation. Rocking here freezes that colour.`
    : S.theta < 62.36 ? 'Below every colour\'s minimum-deviation angle; violet becomes very sensitive.' : 'Above every colour\'s minimum-deviation angle.';
  $('wallTitle').textContent = `${S.dist.toFixed(1)} m from the prism · 1 cm grid`;
  $('distCap').textContent = `${S.dist.toFixed(1)} m`;
}
function invMinDev(th) {
  // wavelength whose minimum-deviation incidence equals th (or null)
  let lo = 390, hi = 700;
  const g = l => minDevIncidence(l) - th;
  if (g(lo) < 0 || g(hi) > 0) return null;
  for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (g(m) > 0) lo = m; else hi = m; }
  return (lo + hi) / 2;
}
function onInput(e) {
  const k = e.target.id;
  if (sliders.includes(k)) S[k] = (k === 'fH' || k === 'fV') ? sToF(+e.target.value) : +e.target.value;
  else if (e.target.name === 'view') { view = e.target.value; writeOutputs(); invalidate(false); return; }
  else if (e.target.name) S[e.target.name] = e.target.value;
  activePreset = null;
  markPreset();
  writeOutputs();
  invalidate(true);
}
document.querySelector('.panel').addEventListener('input', onInput);
document.querySelector('.wall-head').addEventListener('input', onInput);
function applyPreset(p) {
  S = { ...DEFAULTS, ...p.s };
  delete S.view;
  view = p.s.view || (view === 'cam' ? 'eye' : view);
  activePreset = p.id;
  writeControls(); markPreset(); invalidate(false);
}
function markPreset() {
  for (const b of $('presets').children) b.setAttribute('aria-pressed', String(b.dataset.id === activePreset));
}
for (const p of PRESETS) {
  const b = document.createElement('button');
  b.type = 'button'; b.textContent = p.name; b.dataset.id = p.id;
  b.addEventListener('click', () => applyPreset(p));
  $('presets').appendChild(b);
}

// ---------- motion
const activeH = () => S.slideH > 0 || S.turnH > 0;
const activeV = () => S.slideV > 0 || S.turnV > 0;
function motionAt(t) {
  const h = activeH() ? wave(S.wave, TAU * S.fH * t) : 0;
  const v = activeV() ? wave(S.wave, TAU * S.fV * t + S.phase * DEG) : 0;
  return { target: S.target, slideH: S.slideH * h, turnH: S.turnH * DEG * h, slideV: S.slideV * v, turnV: S.turnV * DEG * v, h, v };
}
function gcd(a, b) { a = Math.round(a); b = Math.round(b); while (b) [a, b] = [b, a % b]; return Math.max(1, a); }
function sampleTimes(quality) {
  const H = activeH(), V = activeV();
  let T, N;
  if (!H && !V) return [0];
  if (H && V && S.fH !== S.fV) {
    const g = gcd(S.fH, S.fV);
    T = 1 / g; N = Math.min(9000, Math.max(720, Math.round(360 * Math.max(S.fH, S.fV) / g)));
  } else { T = 1 / (H ? S.fH : S.fV); N = 720; }
  N = Math.max(48, Math.round(N * quality));
  return Array.from({ length: N }, (_, k) => (k + 0.5) / N * T);
}
const fastest = () => Math.max(activeH() ? S.fH : 0, activeV() ? S.fV : 0);

// ---------- simulation cache
let src, bench, times, hits, still, win, exposureStill, readoutLams;
function rebuild(quality) {
  src = makeSource(S.light);
  bench = makeBench(S.theta, S.dist * 1000);
  times = sampleTimes(quality);
  const nl = src.n.length;
  hits = new Float32Array(times.length * nl * 2);
  const tmp = new Float64Array(nl * 2);
  let blocked = 0;
  times.forEach((t, k) => {
    spectrumOnWall(bench, configure(bench, motionAt(t)), src, tmp);
    hits.set(tmp, k * nl * 2);
    for (let i = 0; i < nl; i++) if (Number.isNaN(tmp[2 * i])) blocked++;
  });
  hits.blocked = blocked / (times.length * nl);
  still = spectrumOnWall(bench, configure(bench, { target: S.target, slideH: 0, slideV: 0, turnH: 0, turnV: 0 }), src, new Float64Array(nl * 2));
  win = fitWindow();
}
function fitWindow() {
  let u0 = Infinity, u1 = -Infinity, v0 = Infinity, v1 = -Infinity;
  const nl = src.n.length, use = i => !src.continuous || src.lams[i] >= 400;
  const add = (u, v) => { if (u < u0) u0 = u; if (u > u1) u1 = u; if (v < v0) v0 = v; if (v > v1) v1 = v; };
  for (let k = 0; k < hits.length / (2 * nl); k++) for (let i = 0; i < nl; i++) {
    if (!use(i)) continue;
    const u = hits[(k * nl + i) * 2], v = hits[(k * nl + i) * 2 + 1];
    if (!Number.isNaN(u)) add(u, v);
  }
  for (let i = 0; i < nl; i++) if (use(i) && !Number.isNaN(still[2 * i])) add(still[2 * i], still[2 * i + 1]);
  if (!Number.isFinite(u0)) { u0 = -100; u1 = 100; v0 = -40; v1 = 40; }
  const padU = 14, padV = (S.beam === 'slit' ? SLIT_H / 2 : 4) + 10;
  u0 -= padU; u1 += padU; v0 -= padV; v1 += padV;
  let s = Math.max((u1 - u0) / BW, (v1 - v0) / BH, 0.12);
  s = Math.ceil(s * 50) / 50;
  const cu = (u0 + u1) / 2, cv = (v0 + v1) / 2;
  return { u0: cu - s * BW / 2, vtop: cv + s * BH / 2, s };
}

// ---------- image formation
function makeBuf(w, h) { return { w, h, X: new Float32Array(w * h), Y: new Float32Array(w * h), Z: new Float32Array(w * h) }; }
function deposit(buf, px, py, x, y, z) {
  const i0 = Math.floor(px), j0 = Math.floor(py);
  if (i0 < 0 || j0 < 0 || i0 >= buf.w - 1 || j0 >= buf.h - 1) return;
  const fx = px - i0, fy = py - j0;
  const ws = [(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy];
  const id = [j0 * buf.w + i0, j0 * buf.w + i0 + 1, (j0 + 1) * buf.w + i0, (j0 + 1) * buf.w + i0 + 1];
  for (let q = 0; q < 4; q++) { buf.X[id[q]] += ws[q] * x; buf.Y[id[q]] += ws[q] * y; buf.Z[id[q]] += ws[q] * z; }
}
// lay one instantaneous spectrum (positions arr at offset off) into the buffer; continuous sources are drawn as
// line segments between neighbouring wavelengths so wide spectra stay gap-free
function layDown(buf, arr, off, scale, w, rowFilter) {
  const nl = src.n.length, xyz = src.xyz;
  const toPx = u => (u - win.u0) / scale, toPy = v => (win.vtop - v) / scale;
  const put = (u, v, x, y, z) => {
    if (rowFilter) { const wv = rowFilter(v); if (wv > 0) deposit(buf, toPx(u), rowFilter.row, x * wv, y * wv, z * wv); }
    else deposit(buf, toPx(u), toPy(v), x, y, z);
  };
  if (!src.continuous) {
    for (let i = 0; i < nl; i++) {
      const u = arr[off + 2 * i], v = arr[off + 2 * i + 1];
      if (!Number.isNaN(u)) put(u, v, xyz[i][0] * w, xyz[i][1] * w, xyz[i][2] * w);
    }
    return;
  }
  for (let i = 0; i < nl - 1; i++) {
    const ua = arr[off + 2 * i], va = arr[off + 2 * i + 1], ub = arr[off + 2 * i + 2], vb = arr[off + 2 * i + 3];
    if (Number.isNaN(ua) || Number.isNaN(ub)) continue;
    const len = Math.hypot(ub - ua, vb - va) / scale;
    const m = Math.max(1, Math.ceil(len * 1.5));
    const A = xyz[i], B = xyz[i + 1];
    for (let j = 0; j < m; j++) {
      const s = (j + 0.5) / m, ww = w / m;
      put(ua + (ub - ua) * s, va + (vb - va) * s,
        (A[0] + (B[0] - A[0]) * s) * ww, (A[1] + (B[1] - A[1]) * s) * ww, (A[2] + (B[2] - A[2]) * s) * ww);
    }
  }
}
function kernel(sigmaPx, boxPx) {
  const r = Math.ceil(3 * sigmaPx + boxPx / 2);
  const k = new Float32Array(2 * r + 1);
  let sum = 0;
  for (let i = -r; i <= r; i++) {
    let v;
    if (boxPx > 0) { // box of width boxPx with gaussian-soft edges
      const a = (i + boxPx / 2) / (sigmaPx * Math.SQRT2), b = (i - boxPx / 2) / (sigmaPx * Math.SQRT2);
      v = erf(a) - erf(b);
    } else v = Math.exp(-0.5 * (i / sigmaPx) ** 2);
    k[i + r] = v; sum += v;
  }
  for (let i = 0; i < k.length; i++) k[i] /= sum;
  return k;
}
function erf(x) { const t = 1 / (1 + 0.3275911 * Math.abs(x)); const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x); return x >= 0 ? y : -y; }
function blur(buf, kx, ky) {
  const { w, h } = buf, tmp = new Float32Array(w * h);
  for (const ch of ['X', 'Y', 'Z']) {
    const a = buf[ch];
    if (kx) { const r = (kx.length - 1) / 2;
      for (let y = 0; y < h; y++) { const row = y * w;
        for (let x = 0; x < w; x++) { let s = 0; const lo = Math.max(0, x - r), hi = Math.min(w - 1, x + r);
          for (let i = lo; i <= hi; i++) s += a[row + i] * kx[i - x + r]; tmp[row + x] = s; } }
      a.set(tmp); }
    if (ky) { const r = (ky.length - 1) / 2;
      for (let x = 0; x < w; x++) for (let y = 0; y < h; y++) { let s = 0; const lo = Math.max(0, y - r), hi = Math.min(h - 1, y + r);
        for (let i = lo; i <= hi; i++) s += a[i * w + x] * ky[i - y + r]; tmp[y * w + x] = s; }
      a.set(tmp); }
  }
}
function linearRGB(buf) {
  const n = buf.w * buf.h, out = new Float32Array(n * 3);
  const M = XYZ2RGB;
  for (let p = 0; p < n; p++) {
    const x = buf.X[p], y = buf.Y[p], z = buf.Z[p];
    for (let c = 0; c < 3; c++) out[p * 3 + c] = (M[c][0] * x + M[c][1] * y + M[c][2] * z) / WHITE_BAL[c];
  }
  return out;
}
function autoExposure(rgb) {
  const vals = [];
  for (let p = 0; p < rgb.length; p += 9) { const m = Math.max(rgb[p], rgb[p + 1], rgb[p + 2]); if (m > 0) vals.push(m); }
  if (!vals.length) return 1;
  vals.sort((a, b) => a - b);
  const top = vals[Math.min(vals.length - 1, Math.floor(vals.length * 0.997))];
  return top > 0 ? 1 / top : 1;
}
function toImage(rgb, w, h, ex, img) {
  const d = img.data;
  const enc = v => v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055;
  for (let p = 0; p < w * h; p++) {
    let r = rgb[p * 3] * ex, g = rgb[p * 3 + 1] * ex, b = rgb[p * 3 + 2] * ex;
    const mn = Math.min(r, g, b);
    if (mn < 0) { r -= mn; g -= mn; b -= mn; }
    const mx = Math.max(r, g, b);
    if (mx > 0.75) { const soft = 0.75 + 0.25 * Math.tanh((mx - 0.75) / 0.25); r *= soft / mx; g *= soft / mx; b *= soft / mx; }
    d[p * 4] = 255 * enc(Math.min(1, r)); d[p * 4 + 1] = 255 * enc(Math.min(1, g)); d[p * 4 + 2] = 255 * enc(Math.min(1, b)); d[p * 4 + 3] = 255;
  }
}
function kernelsFor(scale) {
  const sg = SPOT_SIGMA / scale;
  return { kx: kernel(sg, 0), ky: S.beam === 'slit' ? kernel(sg, SLIT_H / scale) : kernel(sg, 0) };
}
function renderAverage(res) {
  const w = Math.round(BW * res), h = Math.round(BH * res), scale = win.s / res;
  const buf = makeBuf(w, h), nl = src.n.length;
  const N = hits.length / (2 * nl);
  for (let k = 0; k < N; k++) layDown(buf, hits, k * nl * 2, scale, 1 / N);
  const { kx, ky } = kernelsFor(scale);
  blur(buf, kx, ky);
  return { rgb: linearRGB(buf), w, h };
}
function stillExposure(res) {
  const w = Math.round(BW * res), h = Math.round(BH * res), scale = win.s / res;
  const buf = makeBuf(w, h);
  layDown(buf, still, 0, scale, 1);
  const { kx, ky } = kernelsFor(scale);
  blur(buf, kx, ky);
  return autoExposure(linearRGB(buf));
}
function renderInstant(t, res) {
  const w = Math.round(BW * res), h = Math.round(BH * res), scale = win.s / res;
  const buf = makeBuf(w, h), arr = new Float64Array(src.n.length * 2);
  spectrumOnWall(bench, configure(bench, motionAt(t)), src, arr);
  layDown(buf, arr, 0, scale, 1);
  const { kx, ky } = kernelsFor(scale);
  blur(buf, kx, ky);
  return { rgb: linearRGB(buf), w, h, arr };
}
function renderCamera(t0, res) {
  // rolling shutter: row r is read out at t0 + r/h * 25 ms
  const w = Math.round(BW * res), h = Math.round(BH * res), scale = win.s / res;
  const buf = makeBuf(w, h), arr = new Float64Array(src.n.length * 2);
  const sg = SPOT_SIGMA, halfSlit = SLIT_H / 2;
  for (let r = 0; r < h; r++) {
    const t = t0 + (r / h) * 0.025;
    spectrumOnWall(bench, configure(bench, motionAt(t)), src, arr);
    const vRow = win.vtop - (r + 0.5) * scale;
    const filt = v => {
      const dv = vRow - v;
      if (S.beam === 'slit') return 0.5 * (erf((dv + halfSlit) / (sg * Math.SQRT2)) - erf((dv - halfSlit) / (sg * Math.SQRT2))) / SLIT_H * scale;
      return Math.exp(-0.5 * (dv / sg) ** 2) / (sg * Math.sqrt(TAU)) * scale;
    };
    filt.row = r;
    layDown(buf, arr, 0, scale, 1, filt);
  }
  const { kx } = kernelsFor(scale);
  blur(buf, kx, null);
  return { rgb: linearRGB(buf), w, h };
}

// ---------- wall drawing
const wall = $('wall'), wctx = wall.getContext('2d');
const off = document.createElement('canvas'), octx = off.getContext('2d');
function sizeCanvas(c) {
  const dpr = Math.min(2, window.devicePixelRatio || 1), cw = c.clientWidth;
  const ar = c === wall ? BH / BW : 0.82;
  const W = Math.round(cw * dpr), H = Math.round(cw * ar * dpr);
  if (c.width !== W || c.height !== H) { c.width = W; c.height = H; }
  return { W, H, dpr };
}
function drawWall(rgb, w, h, ex, extra) {
  off.width = w; off.height = h;
  const img = octx.createImageData(w, h);
  toImage(rgb, w, h, ex, img);
  octx.putImageData(img, 0, 0);
  const { W, H, dpr } = sizeCanvas(wall);
  wctx.fillStyle = '#040507'; wctx.fillRect(0, 0, W, H);
  wctx.imageSmoothingEnabled = true; wctx.imageSmoothingQuality = 'high';
  // grid first (light adds on top of it)
  const k = W / BW;            // display px per buffer px
  const mm = k / win.s;        // display px per mm
  const X = u => (u - win.u0) * mm, Y = v => (win.vtop - v) * mm;
  const uA = win.u0, uB = win.u0 + win.s * BW, vB = win.vtop - win.s * BH;
  const minor = mm * 10 >= 5 * dpr ? 10 : 50, major = minor === 10 ? 50 : 100;
  wctx.lineWidth = 1;
  for (let u = Math.ceil(uA / minor) * minor; u <= uB; u += minor) {
    wctx.strokeStyle = u % major === 0 ? 'rgba(255,255,255,0.17)' : 'rgba(255,255,255,0.07)';
    wctx.beginPath(); wctx.moveTo(Math.round(X(u)) + 0.5, 0); wctx.lineTo(Math.round(X(u)) + 0.5, H); wctx.stroke(); }
  for (let v = Math.ceil(vB / minor) * minor; v <= win.vtop; v += minor) {
    wctx.strokeStyle = v % major === 0 ? 'rgba(255,255,255,0.17)' : 'rgba(255,255,255,0.07)';
    wctx.beginPath(); wctx.moveTo(0, Math.round(Y(v)) + 0.5); wctx.lineTo(W, Math.round(Y(v)) + 0.5); wctx.stroke(); }
  wctx.globalCompositeOperation = 'lighter';
  wctx.drawImage(off, 0, 0, W, H);
  wctx.globalCompositeOperation = 'source-over';
  // labels
  wctx.font = `${11 * dpr}px "IBM Plex Mono", monospace`;
  wctx.fillStyle = 'rgba(201,208,220,0.75)';
  wctx.textBaseline = 'bottom'; wctx.textAlign = 'center';
  for (let u = Math.ceil(uA / major) * major; u <= uB; u += major) if (X(u) > 20 * dpr && X(u) < W - 20 * dpr) wctx.fillText(`${u / 10} cm`, X(u), H - 4 * dpr);
  wctx.textAlign = 'left'; wctx.textBaseline = 'middle';
  for (let v = Math.ceil(vB / major) * major; v <= win.vtop; v += major) if (Y(v) > 12 * dpr && Y(v) < H - 22 * dpr) wctx.fillText(`${v / 10} cm`, 5 * dpr, Y(v));
  // still-position ticks along the top edge
  const ticks = src.continuous ? [450, 550, 650] : src.lams.filter((_, i) => i !== 4);
  wctx.textAlign = 'center'; wctx.textBaseline = 'top';
  for (const l of ticks) {
    const i = src.lams.reduce((b, x, j) => Math.abs(x - l) < Math.abs(src.lams[b] - l) ? j : b, 0);
    const u = still[2 * i]; if (Number.isNaN(u)) continue;
    const x = X(u);
    wctx.fillStyle = 'rgba(201,208,220,0.85)';
    wctx.beginPath(); wctx.moveTo(x - 5 * dpr, 2 * dpr); wctx.lineTo(x + 5 * dpr, 2 * dpr); wctx.lineTo(x, 9 * dpr); wctx.fill();
    wctx.fillText(l === 577 ? '577/579' : `${Math.round(l)}`, x, 11 * dpr);
  }
  if (extra) { wctx.textAlign = 'left'; wctx.fillStyle = 'rgba(255,204,102,0.95)'; wctx.fillText(extra, 8 * dpr, 4 * dpr); }
}

// ---------- side panels
const topC = $('top'), tctx = topC.getContext('2d');
function spectralCSS(l, a = 1) {
  const c = cmf(l); let rgb = XYZ2RGB.map(r => r[0] * c[0] + r[1] * c[1] + r[2] * c[2]);
  const mn = Math.min(...rgb); if (mn < 0) rgb = rgb.map(v => v - mn);
  const mx = Math.max(...rgb); rgb = rgb.map(v => v / mx);
  const e = v => Math.round(255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055));
  return `rgba(${e(rgb[0])},${e(rgb[1])},${e(rgb[2])},${a})`;
}
const DIAG_L = Array.from({ length: 14 }, (_, i) => 400 + 300 * i / 13);
function drawTop(t) {
  const { W, H, dpr } = sizeCanvas(topC);
  tctx.fillStyle = '#07090d'; tctx.fillRect(0, 0, W, H);
  const xs = [-110, 150], sc = W / (xs[1] - xs[0]);
  const X = x => (x - xs[0]) * sc, Y = y => H * 0.16 - y * sc;
  const m = motionAt(t), cfg = configure(bench, m);
  // wall, drawn 150 mm out along the still exit ray
  const A = bench.axis, U = bench.uh, D = 150, c0 = [A[0] * D, A[1] * D];
  tctx.strokeStyle = '#c9d0dc'; tctx.lineWidth = 4 * dpr; tctx.lineCap = 'round';
  tctx.beginPath(); tctx.moveTo(X(c0[0] - 55 * U[0]), Y(c0[1] - 55 * U[1])); tctx.lineTo(X(c0[0] + 55 * U[0]), Y(c0[1] + 55 * U[1])); tctx.stroke();
  // rays
  const lams = src.continuous ? DIAG_L : src.lams;
  let p1 = null;
  for (const l of lams) {
    const r = traceRay(cfg.p0, cfg.d0, nGlass(l), cfg.pose);
    if (!r) continue;
    p1 = r.p1;
    const den = r.d2[0] * A[0] + r.d2[1] * A[1];
    const tt = ((c0[0] - r.p2[0]) * A[0] + (c0[1] - r.p2[1]) * A[1]) / den;
    tctx.strokeStyle = spectralCSS(l, 0.9); tctx.lineWidth = 1.6 * dpr;
    tctx.beginPath(); tctx.moveTo(X(r.p1[0]), Y(r.p1[1])); tctx.lineTo(X(r.p2[0]), Y(r.p2[1])); tctx.lineTo(X(r.p2[0] + tt * r.d2[0]), Y(r.p2[1] + tt * r.d2[1])); tctx.stroke();
  }
  // incoming beam
  const start = [cfg.p0[0], cfg.p0[1]];
  const end = p1 ? p1 : [cfg.p0[0] + 300 * cfg.d0[0], cfg.p0[1] + 300 * cfg.d0[1]];
  tctx.strokeStyle = '#ffffff'; tctx.lineWidth = 2.4 * dpr;
  tctx.beginPath(); tctx.moveTo(X(start[0]), Y(start[1])); tctx.lineTo(X(end[0]), Y(end[1])); tctx.stroke();
  // prism outline (slice through the beam height)
  tctx.beginPath();
  for (let i = 0; i < 3; i++) {
    const v = [PV[i][0], PV[i][1], 0], q = [cfg.pose.M[0][0] * v[0] + cfg.pose.M[0][1] * v[1] + cfg.pose.T[0], cfg.pose.M[1][0] * v[0] + cfg.pose.M[1][1] * v[1] + cfg.pose.T[1]];
    i ? tctx.lineTo(X(q[0]), Y(q[1])) : tctx.moveTo(X(q[0]), Y(q[1]));
  }
  tctx.closePath(); tctx.fillStyle = 'rgba(140,190,240,0.22)'; tctx.fill(); tctx.strokeStyle = '#cfe3ff'; tctx.lineWidth = 1.6 * dpr; tctx.stroke();
  tctx.font = `${11 * dpr}px "IBM Plex Sans", sans-serif`; tctx.fillStyle = '#8d97aa'; tctx.textBaseline = 'top';
  tctx.fillText(S.target === 'light' ? 'light source (wobbling) ←' : 'light from the left', 6 * dpr, Y(BEAM_Y) - 22 * dpr);
}
const pathC = $('path'), pctx = pathC.getContext('2d');
function drawPath(t) {
  const { W, H, dpr } = sizeCanvas(pathC);
  pctx.fillStyle = '#07090d'; pctx.fillRect(0, 0, W, H);
  const cx = W / 2, cy = H / 2, R = Math.min(W, H) * 0.36;
  pctx.strokeStyle = 'rgba(255,255,255,0.12)'; pctx.lineWidth = 1;
  pctx.beginPath(); pctx.moveTo(cx - R * 1.15, cy); pctx.lineTo(cx + R * 1.15, cy); pctx.moveTo(cx, cy - R * 1.15); pctx.lineTo(cx, cy + R * 1.15); pctx.stroke();
  const H_ = activeH(), V_ = activeV();
  pctx.font = `${11 * dpr}px "IBM Plex Sans", sans-serif`; pctx.fillStyle = '#8d97aa';
  pctx.textAlign = 'center'; pctx.textBaseline = 'bottom';
  pctx.fillText('up', cx, cy - R * 1.17); pctx.textBaseline = 'top'; pctx.fillText('down', cx, cy + R * 1.17);
  pctx.textAlign = 'left'; pctx.textBaseline = 'middle'; pctx.fillText('left', 4 * dpr, cy - 9 * dpr); pctx.textAlign = 'right'; pctx.fillText('right', W - 4 * dpr, cy - 9 * dpr);
  if (!H_ && !V_) { pctx.textAlign = 'center'; pctx.fillStyle = '#c9d0dc'; pctx.fillText('not moving', cx, cy + 24 * dpr); }
  const T = times.length > 1 ? times[times.length - 1] + times[0] : 1;
  pctx.strokeStyle = '#82a8ff'; pctx.lineWidth = 1.6 * dpr; pctx.beginPath();
  const n = 1200;
  for (let k = 0; k <= n; k++) { const m = motionAt(k / n * T); const x = cx + R * m.h, y = cy - R * m.v; k ? pctx.lineTo(x, y) : pctx.moveTo(x, y); }
  pctx.stroke();
  const m = motionAt(t);
  pctx.fillStyle = '#ffffff'; pctx.beginPath(); pctx.arc(cx + R * m.h, cy - R * m.v, 5 * dpr, 0, TAU); pctx.fill();
  const who = S.target === 'light' ? 'Light source' : 'Prism';
  const parts = [];
  if (H_) parts.push(`left↔right ${S.slideH ? `±${S.slideH} mm` : ''}${S.slideH && S.turnH ? ' + ' : ''}${S.turnH ? `±${S.turnH}°` : ''} at ${S.fH}/s`);
  if (V_) parts.push(`up↕down ${S.slideV ? `±${S.slideV} mm` : ''}${S.slideV && S.turnV ? ' + ' : ''}${S.turnV ? `±${S.turnV}°` : ''} at ${S.fV}/s`);
  $('pathCap').textContent = `${who} motion, seen from behind the light: ${parts.length ? parts.join('; ') : 'still'}. Each axis is scaled to fill the box.`;
}

// ---------- readouts
function updateReadout() {
  const lams = src.continuous ? [420, 480, 530, 650] : [404.7, 435.8, 546.1, 577.0];
  const names = src.continuous ? ['violet', 'blue', 'green', 'red'] : ['405 violet', '436 blue', '546 green', '577 yellow'];
  const fake = { n: lams.map(nGlass) }, arr = new Float64Array(lams.length * 2);
  const ru = lams.map(() => [Infinity, -Infinity]), rv = lams.map(() => [Infinity, -Infinity]);
  const ts = times.length > 1 ? times.filter((_, i) => i % Math.max(1, Math.floor(times.length / 720)) === 0) : times;
  for (const t of ts) {
    spectrumOnWall(bench, configure(bench, motionAt(t)), fake, arr);
    lams.forEach((_, i) => { const u = arr[2 * i], v = arr[2 * i + 1]; if (Number.isNaN(u)) return;
      ru[i][0] = Math.min(ru[i][0], u); ru[i][1] = Math.max(ru[i][1], u); rv[i][0] = Math.min(rv[i][0], v); rv[i][1] = Math.max(rv[i][1], v); });
  }
  const span = r => Number.isFinite(r[0]) ? r[1] - r[0] : NaN;
  const tot = lams.map((_, i) => Math.hypot(span(ru[i]), span(rv[i])));
  const big = Math.max(...tot.filter(Number.isFinite));
  const rows = lams.map((l, i) => {
    const frozen = big > 3 && tot[i] < 0.3 * big;
    const f = v => Number.isNaN(v) ? '—' : `${v.toFixed(1)} mm`;
    return `<tr><td><span class="sw" style="background:${spectralCSS(l)}"></span>${names[i]}${frozen ? '<span class="pill">nearly frozen</span>' : ''}</td><td>${f(span(ru[i]))}</td><td>${f(span(rv[i]))}</td></tr>`;
  });
  $('readout').querySelector('tbody').innerHTML = rows.join('');
  const facts = [];
  const fmax = fastest();
  if (fmax > 0) {
    const vPeak = TAU * Math.max(activeH() ? S.fH * (S.slideH + S.turnH * DEG * 23) : 0, activeV() ? S.fV * (S.slideV + S.turnV * DEG * 23) : 0);
    const ratio = vPeak / C_LIGHT;
    facts.push(`Doppler colour shift from the motion: at most ${ratio.toExponential(1).replace('e-', ' × 10⁻').replace(/(\d+)$/, d => d.split('').map(c => '⁰¹²³⁴⁵⁶⁷⁸⁹'[c]).join(''))} of the frequency (${(550 * ratio).toExponential(0).replace('e-', ' × 10⁻').replace(/(\d+)$/, d => d.split('').map(c => '⁰¹²³⁴⁵⁶⁷⁸⁹'[c]).join(''))} nm). Far too small to see.`);
    if (view === 'eye' && fmax < 40) facts.push(`<span class="warn">At ${fmax} per second your eye can still follow the motion. This view shows the average; switch to Slow motion to see it move.</span>`);
  }
  if (hits.blocked > 0.001) facts.push(`<span class="warn">Part of the time (${(hits.blocked * 100).toFixed(0)}%) light misses the exit face or is reflected inside the prism, so it never reaches the wall.</span>`);
  if (view === 'cam' && S.beam === 'spot') facts.push('Tip: the rolling-shutter effect shows best with the tall slit beam.');
  $('facts').innerHTML = facts.map(f => `<li>${f}</li>`).join('');
  const p = PRESETS.find(q => q.id === activePreset);
  $('notice').innerHTML = p ? p.note : '<b>Your own settings.</b> Grid squares are 1 cm. The table shows how far each colour travels during one cycle. Pick an experiment to compare.';
}

// ---------- scheduling
let dirty = true, refineTimer = null, avgCache = null, exStill = 1, camFrame = 0;
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function invalidate(dragging) {
  dirty = true;
  quality = dragging ? 0.25 : 1;
  clearTimeout(refineTimer);
  if (dragging) refineTimer = setTimeout(() => { dirty = true; quality = 1; }, 220);
}
let quality = 1, t0 = performance.now();
function frame(now) {
  if (dirty) {
    rebuild(quality);
    avgCache = null;
    exStill = stillExposure(view === 'eye' ? 1 : 0.5);
    updateReadout();
    dirty = false;
  }
  const slowF = fastest() > 0 ? 0.35 / fastest() : 0;
  const tau = reduceMotion ? 0 : (now - t0) / 1000 * slowF;
  if (view === 'eye') {
    if (!avgCache) { const r = renderAverage(quality < 1 ? 0.5 : 1); r.ex = autoExposure(r.rgb); avgCache = r; drawWall(r.rgb, r.w, r.h, r.ex); }
  } else if (view === 'slow') {
    const r = renderInstant(tau, 0.5); drawWall(r.rgb, r.w, r.h, exStill, fastest() ? `slow motion: one swing every ${(1 / 0.35).toFixed(1)} s` : '');
    avgCache = null;
  } else {
    const r = renderCamera(camFrame / 30, 0.5); camFrame++;
    drawWall(r.rgb, r.w, r.h, exStill, `camera at 30 frames/s, frame ${camFrame}`);
    avgCache = null;
  }
  drawTop(tau); drawPath(tau);
  requestAnimationFrame(frame);
}
window.addEventListener('resize', () => { avgCache = null; });
writeControls(); markPreset();
requestAnimationFrame(frame);
})();
// APP-END
