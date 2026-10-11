// REAL_ROOM — a cozy night bedroom corner (portrait 720x1280). The film's first frame.
//
//   drawRealRoom(g, state)             background: wall, window + night sky, curtains, fairy lights,
//                                      shelf, plants, and the desk top surface
//   drawRealRoomForeground(g, state)   desk top (again, over the narrator's waist), desk front, lamp,
//                                      mug + steam, books, crayons, dust motes in the lamp light
//   drawLitByRoom(g, state, drawFn, box?)  draws a character lit like the room (warm lamp key / night blue)
//   REALROOM = { width, height, camera, cameras, anchors: { name: [x, y, scale] }, deskY, deskNearY, titleBox, ... }
//
// state: { t, lamp 0..1, moon 0..1, dusk 0..1, fairy 0..1, starHood 0..1, starWink 0..1, deskTop bool, motes bool,
//          steam bool }
// Static art is cached once per (lamp on/off, moon, dusk, resolution) in offscreen canvases;
// the lamp fades by cross-dissolving the "off" and "on" caches. Full API: docs/props.md.

import { createCanvas } from '@napi-rs/canvas';
import { clamp, lerp, TAU, rgba, mixColor, ellipse, circle } from '../engine.mjs';
import { drawDeskLamp, LAMP_ANCHORS, hrand as rand, vfbm as fbm } from './props.mjs';

const RW = 840, RH = 1280; // stage is wider than the frame: the default camera centres x = 420
const DESK_Y = 905, DESK_NEAR = 1030, DESK_LIP = 1047;
const WIN = { x0: 254, x1: 610, y0: 114, y1: 540, rail: 362, cx: 432 };
const ROD_Y = 84, TIE_Y = 404, CURT_BOT = 664;
const LAMP_POS = [124, 984, 0.86];
const LAMP_MOUTH = [LAMP_POS[0] + LAMP_ANCHORS.bulb[0] * LAMP_POS[2], LAMP_POS[1] + LAMP_ANCHORS.bulb[1] * LAMP_POS[2]];
const LAMP_HEAD = [LAMP_POS[0] + LAMP_ANCHORS.head[0] * LAMP_POS[2], LAMP_POS[1] + LAMP_ANCHORS.head[1] * LAMP_POS[2]];
const MOON = [556, 414, 27]; // a low moonrise over the rooftops keeps the upper sky clean for a title
const MUG = [628, 1004];

export const REALROOM = {
  width: RW,
  height: RH,
  camera: { x: 420, y: 640, zoom: 1 }, // default full-room framing (shows world x 60..780)
  // verified framings (pass to applyCamera). opening = the screenplay's first frame / thumbnail: title box fully
  // in the upper third, face in the middle third, notebook on the desk in the lower third above the bottom 15 %.
  cameras: {
    full: { x: 420, y: 640, zoom: 1 },
    opening: { x: 420, y: 655, zoom: 1.12 },   // push-in target for the 2 % creep: zoom 1.142
    desk: { x: 424, y: 760, zoom: 1.5 },        // SELF + notebook + lamp pool ("close on SELF at the desk")
    face: { x: 424, y: 680, zoom: 2.2 },        // face close-up (lamp glints in the eyes come from SELF's module)
    window: { x: 432, y: 450, zoom: 1.45 },     // the window / stars / star-hood (ending)
  },
  anchors: {
    selfSeated: [420, DESK_Y, 1.0],   // drawSelf seated origin: body meets the desk top's far edge
    notebook: [430, 984, 0.6],        // notebook lying flat on the desk (use flat: 1)
    notebookHeld: [410, 846, 0.62],   // notebook held upright against the desk edge, cover to camera (flat: 0)
    notebookInsert: [420, 640, 1.45], // notebook spread filling the default frame for an insert shot
    lamp: LAMP_POS,                   // desk-lamp base (drawn by the foreground)
    lampLight: [LAMP_MOUTH[0], LAMP_MOUTH[1], 1], // the bulb: light source for scene lighting
    mug: [MUG[0], MUG[1], 1],
    window: [WIN.cx, (WIN.y0 + WIN.y1) / 2, 1],
    moon: [MOON[0], MOON[1], 1],
    faceCloseUp: [424, 680, 1],       // camera target for a close-up on the seated narrator's face (scale 1 self)
    starWink: [412, 196, 1],          // the star that twinkles inside the star-hood's opening (state.starWink)
  },
  deskY: DESK_Y,
  deskNearY: DESK_NEAR,
  deskFrontY: DESK_LIP,
  window: { x0: WIN.x0, x1: WIN.x1, y0: WIN.y0, y1: WIN.y1, rail: WIN.rail },
  titleBox: { x: WIN.x0 + 12, y: WIN.y0 + 18, w: WIN.x1 - WIN.x0 - 24, h: WIN.rail - WIN.y0 - 34 }, // clean sky for a title
};

// ------------------------------------------------------------------ palette
const NIGHT_TINT = '#141331';
const COL = {
  wallTop: '#1f1834', wallBot: '#36284a',
  frame: '#d8c7a6', frameNight: '#59607f',
  curtain: '#a2646f', curtainNight: '#3c2a47', curtainDk: '#6a3a4a',
  wood: '#a46c45', woodDk: '#5e3a24', woodHi: '#d29a68',
  desk: '#a8704a', deskFar: '#6e4630', deskFront: '#5a3624', deskFrontDk: '#311c13', line: '#2a1810',
  plant: '#4f7d58', plantDk: '#2c4b3a', pot: '#c06a48',
  books: ['#7d4f6b', '#4f7a74', '#c08a3e', '#a8584a', '#5d6a96', '#8a7a52'],
};
const nightOf = (c, k = 0.6) => mixColor(c, NIGHT_TINT, k);

// lamp light falloff (0..1) at a world point
function lampK(x, y, r = 760) {
  const d = Math.hypot(x - LAMP_MOUTH[0], (y - LAMP_MOUTH[1]) * 1.1);
  return Math.pow(clamp(1 - d / r), 1.6);
}
// colour of a surface at (x,y) given lamp level L (0 or 1 in caches)
const litCol = (c, x, y, L, nightK = 0.62, boost = 1) => mixColor(nightOf(c, nightK), c, clamp(L * lampK(x, y) * boost * 1.25));

// ------------------------------------------------------------------ cache plumbing
const layers = new Map();
// cache resolution follows the on-screen pixel scale in 0.5 steps (1, 1.5, 2, 2.5, 3), so the opening still at
// zoom ~1.1 is rendered sharp instead of a 1x bitmap stretched; a 2% push-in never changes the step.
function curRes(g) {
  try { const m = g.getTransform(); const s = Math.hypot(m.a, m.b); return clamp(Math.ceil(s * 2 - 0.1) / 2, 1, 3); } catch { return 1; }
}
const LAYER_PX_BUDGET = 30e6; // ≈ 120 MB of cached bitmaps max (LRU)
let layerPx = 0;
function layer(key, x, y, w, h, res, build) {
  const k = `${key}@${res}`;
  let L = layers.get(k);
  if (L) { layers.delete(k); layers.set(k, L); } // LRU touch
  else {
    const c = createCanvas(Math.ceil(w * res), Math.ceil(h * res));
    const g = c.getContext('2d');
    g.scale(res, res);
    g.translate(-x, -y);
    build(g);
    L = { c, x, y, w, h };
    layers.set(k, L);
    layerPx += c.width * c.height;
    while (layers.size > 2 && (layerPx > LAYER_PX_BUDGET || layers.size > 12)) { // bounded memory, LRU
      const k0 = layers.keys().next().value, c0 = layers.get(k0).c;
      layerPx -= c0.width * c0.height;
      layers.delete(k0);
    }
  }
  return L;
}
const blit = (g, L, alpha = 1) => {
  if (alpha <= 0.002) return;
  if (alpha < 0.998) { g.save(); g.globalAlpha *= alpha; g.drawImage(L.c, L.x, L.y, L.w, L.h); g.restore(); }
  else g.drawImage(L.c, L.x, L.y, L.w, L.h);
};

function norm(state) {
  return {
    t: state.t || 0,
    lamp: clamp(state.lamp ?? 1),
    moon: clamp(state.moon ?? 1),
    dusk: clamp(state.dusk ?? 0),
    fairy: clamp(state.fairy ?? 1),
    starHood: clamp(state.starHood ?? 0),
    starWink: clamp(state.starWink ?? 0),
  };
}

// ======================================================================== BACKGROUND
export function drawRealRoom(g, state = {}) {
  const s = norm(state);
  const res = curRes(g);
  const mq = Math.round(s.moon * 10) / 10, dq = Math.round(s.dusk * 10) / 10;
  const bg = (L) => layer(`bg|${L}|${mq}|${dq}`, 0, 0, RW, RH, res, (cg) => buildBackground(cg, L, mq, dq));
  g.save();
  if (s.lamp < 0.998) blit(g, bg(0));
  if (s.lamp > 0.002) blit(g, bg(1), s.lamp);
  drawStarHood(g, s);
  drawStars(g, s);
  drawFairyBulbs(g, s);
  g.restore();
}

// ======================================================================== FOREGROUND
export function drawRealRoomForeground(g, state = {}) {
  const s = norm(state);
  const res = curRes(g);
  const top = (L) => layer(`top|${L}`, 0, DESK_Y - 12, RW, DESK_NEAR - DESK_Y + 24, res, (cg) => drawDeskTop(cg, L));
  const rest = (L) => layer(`fg|${L}`, 0, 560, RW, RH - 560, res, (cg) => buildForeground(cg, L));
  g.save();
  if (state.deskTop !== false) {
    if (s.lamp < 0.998) blit(g, top(0));
    if (s.lamp > 0.002) blit(g, top(1), s.lamp);
  }
  if (s.lamp < 0.998) blit(g, rest(0));
  if (s.lamp > 0.002) blit(g, rest(1), s.lamp);
  if (state.steam !== false) drawSteam(g, s);
  if (state.motes !== false && s.lamp > 0.02) drawMotes(g, s);
  g.restore();
}

// ======================================================================== CHARACTER LIGHT
// drawLitByRoom(g, state, drawFn): draws a character (drawFn(ctx) in the SAME world coords as g) on an offscreen
// layer, lights it like the room, and composites it onto g:
//   lamp on  → warm amber light from the lamp side (below-left), the far side stays cooler (screenplay s01)
//   lamp off → the character sinks into the same soft night blue as the room (s20 ending)
//   moon     → (lamp dimming only) a faint cool wash from the window behind / above on hair and shoulders
// Call it once per character pass (e.g. Self 'body' and Self 'front').
// box = [x, y, w, h] WORLD rect that contains the character (default: the seated narrator); only that region is
// processed, so the cost is ≈ 2–4 ms per call at the full camera (more when the box fills the frame in close-ups).
const LIT_BOX = [150, 470, 560, 620]; // seated SELF incl. hair, elbows and hands on the desk
let litLayer = null;
export function drawLitByRoom(g, state, drawFn, box = LIT_BOX) {
  const s = norm(state);
  const cw = (g.canvas && g.canvas.width) || 720, ch = (g.canvas && g.canvas.height) || 1280;
  const m = g.getTransform();
  // device-space rect of the box
  const [bx, by, bw, bh] = box;
  const xs = [], ys = [];
  for (const [px, py] of [[bx, by], [bx + bw, by], [bx, by + bh], [bx + bw, by + bh]]) { xs.push(m.a * px + m.c * py + m.e); ys.push(m.b * px + m.d * py + m.f); }
  const dx = Math.max(0, Math.floor(Math.min(...xs))), dy = Math.max(0, Math.floor(Math.min(...ys)));
  const dw = Math.min(cw, Math.ceil(Math.max(...xs))) - dx, dh = Math.min(ch, Math.ceil(Math.max(...ys))) - dy;
  if (dw <= 0 || dh <= 0) return;
  // offscreen sized to the box (rounded up to 64 px so a moving camera rarely reallocates); copying a small
  // canvas back is what keeps this cheap
  const lw = Math.ceil(dw / 64) * 64, lh = Math.ceil(dh / 64) * 64;
  if (!litLayer || litLayer.width !== lw || litLayer.height !== lh) litLayer = createCanvas(lw, lh);
  const lg = litLayer.getContext('2d');
  lg.setTransform(1, 0, 0, 1, 0, 0);
  lg.globalCompositeOperation = 'source-over';
  lg.globalAlpha = 1;
  lg.clearRect(0, 0, lw, lh);
  lg.save();
  lg.beginPath(); lg.rect(0, 0, dw, dh); lg.clip();
  lg.setTransform(m.a, m.b, m.c, m.d, m.e - dx, m.f - dy);
  lg.save();
  drawFn(lg);
  lg.restore();
  lg.globalCompositeOperation = 'source-atop';
  // night: the room's blue swallows the figure as the lamp goes off
  const night = 1 - s.lamp;
  if (night > 0.004) { lg.fillStyle = rgba(NIGHT_TINT, 0.42 * night); lg.fillRect(bx, by, bw, bh); }
  // warm lamp key from below-left
  if (s.lamp > 0.004) {
    const [mx, my] = LAMP_MOUTH;
    const gl = lg.createRadialGradient(mx + 40, my + 20, 10, mx + 40, my + 20, 470);
    gl.addColorStop(0, `rgba(255,186,110,${0.2 * s.lamp})`);
    gl.addColorStop(0.5, `rgba(255,170,100,${0.06 * s.lamp})`);
    gl.addColorStop(1, 'rgba(255,160,100,0)');
    lg.fillStyle = gl; lg.fillRect(bx, by, bw, bh);
  }
  // cool window light from behind / above (only once the lamp dims: keeps the lit face clean and saturated)
  if (s.moon > 0.01 && night > 0.004) {
    const gm = lg.createRadialGradient(WIN.cx + 60, WIN.y1 - 40, 20, WIN.cx + 60, WIN.y1 - 40, 360);
    gm.addColorStop(0, `rgba(150,180,255,${0.16 * night * s.moon})`);
    gm.addColorStop(1, 'rgba(130,160,255,0)');
    lg.fillStyle = gm; lg.fillRect(bx, by, bw, bh);
  }
  lg.restore(); // clip + composite op
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(litLayer, 0, 0, dw, dh, dx, dy, dw, dh);
  g.restore();
}

// ------------------------------------------------------------------ background build
function buildBackground(g, L, moon, dusk) {
  // wall
  const gw = g.createLinearGradient(0, 0, 0, DESK_Y);
  gw.addColorStop(0, COL.wallTop); gw.addColorStop(1, COL.wallBot);
  g.fillStyle = gw; g.fillRect(0, 0, RW, DESK_Y + 10);
  // very soft wide wallpaper stripes
  g.fillStyle = 'rgba(255,255,255,0.022)';
  for (let x = 12; x < RW; x += 52) g.fillRect(x, 0, 22, DESK_Y);
  // cool moon spill around the window
  if (moon > 0) {
    const gm = g.createRadialGradient(WIN.cx, (WIN.y0 + WIN.y1) / 2, 100, WIN.cx, (WIN.y0 + WIN.y1) / 2, 460);
    gm.addColorStop(0, `rgba(110,140,220,${0.16 * moon})`); gm.addColorStop(1, 'rgba(110,140,220,0)');
    g.fillStyle = gm; g.fillRect(0, 0, RW, DESK_Y);
  }
  // warm lamp light on the wall
  if (L) {
    const gl = g.createRadialGradient(LAMP_MOUTH[0] + 30, LAMP_MOUTH[1] - 40, 10, LAMP_MOUTH[0] + 90, LAMP_MOUTH[1] - 110, 860);
    gl.addColorStop(0, 'rgba(255,196,128,0.8)');
    gl.addColorStop(0.16, 'rgba(240,156,106,0.55)');
    gl.addColorStop(0.4, 'rgba(190,110,104,0.3)');
    gl.addColorStop(0.7, 'rgba(120,76,104,0.1)');
    gl.addColorStop(1, 'rgba(90,60,100,0)');
    g.fillStyle = gl; g.fillRect(0, 0, RW, DESK_Y + 10);
  }
  // soft warm bloom behind the narrator's head: the focal point of the room
  if (L) {
    const gh = g.createRadialGradient(430, 700, 20, 430, 700, 300);
    gh.addColorStop(0, 'rgba(255,190,140,0.2)'); gh.addColorStop(0.6, 'rgba(230,150,130,0.07)'); gh.addColorStop(1, 'rgba(230,150,130,0)');
    g.fillStyle = gh; g.fillRect(130, 400, 600, 505);
  }
  // shadow on the wall right above the desk's far edge
  const gs = g.createLinearGradient(0, DESK_Y - 26, 0, DESK_Y);
  gs.addColorStop(0, 'rgba(10,6,20,0)'); gs.addColorStop(1, 'rgba(10,6,20,0.45)');
  g.fillStyle = gs; g.fillRect(0, DESK_Y - 26, RW, 26);

  drawWindow(g, L, moon, dusk);
  drawShelf(g, L);
  drawCurtains(g, L);
  drawFairyWire(g, L);
  drawRightFrame(g, L);
  drawHangingPlant(g, L);
  drawDeskTop(g, L);
}

function skyColors(dusk) {
  const n = ['#0b1435', '#15275e', '#28468c', '#3e64a8'];
  const d = ['#1b1b4e', '#3f3a86', '#8a5c9c', '#e09078'];
  return n.map((c, i) => mixColor(c, d[i], dusk));
}

function drawWindow(g, L, moon, dusk) {
  const { x0, x1, y0, y1, rail, cx } = WIN;
  // casing (outer frame)
  const caseC = (x) => litCol(COL.frame, x, 360, L, 0.55);
  const gc = g.createLinearGradient(x0 - 24, 0, x1 + 24, 0);
  gc.addColorStop(0, caseC(x0)); gc.addColorStop(1, caseC(x1));
  g.fillStyle = gc; g.strokeStyle = rgba(COL.line, 0.8); g.lineWidth = 3;
  g.beginPath(); g.rect(x0 - 22, y0 - 22, x1 - x0 + 44, y1 - y0 + 30); g.fill(); g.stroke();
  // glass: sky
  const [s0, s1, s2, s3] = skyColors(dusk);
  const gsk = g.createLinearGradient(0, y0, 0, y1);
  gsk.addColorStop(0, s0); gsk.addColorStop(0.45, s1); gsk.addColorStop(0.8, s2); gsk.addColorStop(1, s3);
  g.fillStyle = gsk; g.fillRect(x0, y0, x1 - x0, y1 - y0);
  g.save();
  g.beginPath(); g.rect(x0, y0, x1 - x0, y1 - y0); g.clip();
  // moon + glow
  if (moon > 0.01) {
    const [mx, my, mr] = MOON;
    const gl = g.createRadialGradient(mx, my, mr * 0.8, mx, my, mr * 5);
    gl.addColorStop(0, `rgba(220,230,255,${0.32 * moon})`); gl.addColorStop(0.3, `rgba(170,190,250,${0.12 * moon})`); gl.addColorStop(1, 'rgba(150,170,240,0)');
    g.fillStyle = gl; g.fillRect(mx - mr * 5, my - mr * 5, mr * 10, mr * 10);
    // crescent drawn on a scratch canvas
    const S = 4, size = Math.ceil(mr * 2.6);
    const mc = createCanvas(size * S, size * S), mg = mc.getContext('2d');
    mg.scale(S, S); mg.translate(size / 2, size / 2);
    const gm = mg.createRadialGradient(-mr * 0.3, -mr * 0.3, 2, 0, 0, mr);
    gm.addColorStop(0, '#fffbe9'); gm.addColorStop(1, '#f2e4bd');
    mg.fillStyle = gm; circle(mg, 0, 0, mr); mg.fill();
    mg.fillStyle = 'rgba(200,180,140,0.35)';
    for (const [dx, dy, r] of [[-8, -6, 5], [6, 8, 4], [-2, 12, 3]]) { circle(mg, dx, dy, r); mg.fill(); }
    mg.globalCompositeOperation = 'destination-out';
    mg.fillStyle = 'rgba(0,0,0,0.93)'; circle(mg, mr * 0.52, -mr * 0.28, mr * 0.92); mg.fill();
    g.globalAlpha = moon;
    g.drawImage(mc, mx - size / 2, my - size / 2, size, size);
    g.globalAlpha = 1;
  }
  // soft clouds (static)
  for (const [cx0, cy0, w, a] of [[350, 250, 160, 0.13], [520, 330, 120, 0.1], [300, 170, 90, 0.07], [480, 440, 120, 0.12]]) {
    const gcl = g.createRadialGradient(cx0, cy0, 4, cx0, cy0, w);
    gcl.addColorStop(0, `rgba(150,170,230,${a * (0.6 + moon * 0.4)})`); gcl.addColorStop(1, 'rgba(150,170,230,0)');
    g.save(); g.translate(cx0, cy0); g.scale(1, 0.22); g.translate(-cx0, -cy0);
    g.fillStyle = gcl; g.fillRect(cx0 - w, cy0 - w, w * 2, w * 2);
    g.restore();
  }
  // distant hills + rooftops with a few warm windows
  const hill = mixColor('#16244e', '#3b2a5a', dusk);
  g.fillStyle = hill;
  g.beginPath(); g.moveTo(x0, y1 - 68);
  g.bezierCurveTo(330, y1 - 96, 400, y1 - 78, 450, y1 - 88); g.bezierCurveTo(520, y1 - 100, 570, y1 - 83, x1, y1 - 92);
  g.lineTo(x1, y1); g.lineTo(x0, y1); g.closePath(); g.fill();
  const roof = mixColor('#0f1838', '#2a1c42', dusk);
  g.fillStyle = roof;
  const houses = [[272, y1 - 48, 46, 34], [330, y1 - 60, 40, 50], [392, y1 - 40, 58, 30], [470, y1 - 52, 44, 42], [530, y1 - 36, 60, 28], [586, y1 - 48, 40, 40]];
  for (const [hx, hy, hw, hh] of houses) {
    g.beginPath(); g.moveTo(hx, y1); g.lineTo(hx, hy); g.lineTo(hx + hw / 2, hy - hh * 0.45); g.lineTo(hx + hw, hy); g.lineTo(hx + hw, y1); g.closePath(); g.fill();
  }
  // tree blobs
  g.fillStyle = mixColor('#0c1430', '#24173a', dusk);
  for (const [tx, ty, r] of [[300, y1 - 40, 22], [318, y1 - 50, 16], [500, y1 - 42, 20], [612, y1 - 52, 26]]) { circle(g, tx, ty, r); g.fill(); }
  g.fillStyle = 'rgba(255,205,120,0.9)';
  for (const [wx, wy] of [[345, y1 - 40], [482, y1 - 32], [404, y1 - 28], [600, y1 - 26]]) g.fillRect(wx, wy, 6, 7);
  // lamp reflection in the glass (lit)
  if (L) {
    const gr = g.createRadialGradient(x0 + 40, y1 - 40, 4, x0 + 40, y1 - 40, 120);
    gr.addColorStop(0, 'rgba(255,200,130,0.22)'); gr.addColorStop(1, 'rgba(255,200,130,0)');
    g.fillStyle = gr; g.fillRect(x0, y1 - 160, 160, 160);
  }
  // faint glass sheen
  g.strokeStyle = 'rgba(200,220,255,0.035)'; g.lineWidth = 22;
  g.beginPath(); g.moveTo(x0 + 30, y0 + 200); g.lineTo(x0 + 170, y0 + 30); g.stroke();
  g.restore();
  // sash bars
  const barC = (x) => litCol(COL.frame, x, 380, L, 0.5);
  const bar = (x, y, w, h) => {
    const gb = g.createLinearGradient(x, 0, x + w, 0);
    gb.addColorStop(0, barC(x)); gb.addColorStop(1, barC(x + w));
    g.fillStyle = gb; g.fillRect(x, y, w, h);
    g.strokeStyle = rgba(COL.line, 0.55); g.lineWidth = 1.5; g.strokeRect(x, y, w, h);
  };
  bar(x0 - 2, rail - 7, x1 - x0 + 4, 15);         // meeting rail
  bar(cx - 5, rail + 8, 10, y1 - rail - 8);       // lower muntin
  // inner frame lip (shadow inside the casing)
  g.strokeStyle = 'rgba(10,8,25,0.35)'; g.lineWidth = 4;
  g.strokeRect(x0 + 2, y0 + 2, x1 - x0 - 4, y1 - y0 - 4);
  // sill
  const sillC = litCol(COL.frame, x0, 600, L, 0.5, 1.2);
  g.fillStyle = mixColor(sillC, '#ffffff', 0.12); g.strokeStyle = rgba(COL.line, 0.8); g.lineWidth = 2.5;
  g.beginPath(); g.rect(x0 - 40, y1 + 2, x1 - x0 + 80, 9); g.fill(); g.stroke();
  g.fillStyle = mixColor(sillC, '#000000', 0.18);
  g.beginPath(); g.rect(x0 - 36, y1 + 11, x1 - x0 + 72, 14); g.fill(); g.stroke();
  // cool moon highlight on the sill top
  g.fillStyle = `rgba(170,190,255,${0.25 * moon})`; g.fillRect(x0 + 10, y1 + 3, x1 - x0 - 20, 3);
  // little succulent on the sill
  const px = 298, py = y1 + 2;
  g.fillStyle = litCol(COL.pot, px, py, L, 0.6); g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 2;
  g.beginPath(); g.moveTo(px - 16, py - 26); g.lineTo(px + 16, py - 26); g.lineTo(px + 12, py); g.lineTo(px - 12, py); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = litCol(COL.plant, px, py, L, 0.55);
  for (const [dx, dy, rx, ry, r] of [[-9, -36, 7, 14, -0.5], [9, -36, 7, 14, 0.5], [0, -42, 7, 17, 0], [-14, -30, 5, 10, -1.1], [14, -30, 5, 10, 1.1]]) {
    ellipse(g, px + dx, py + dy, rx, ry, r); g.fill(); g.stroke();
  }
}

function curtainPath(g, side) {
  // side -1 = left curtain, +1 = right (mirrored around the window centre)
  const m = (x) => (side < 0 ? x : 2 * WIN.cx - x);
  const T = TIE_Y, B = CURT_BOT, R = ROD_Y;
  g.beginPath();
  g.moveTo(m(186), R);
  g.lineTo(m(300), R);
  g.bezierCurveTo(m(296), lerp(R, T, 0.43), m(268), lerp(R, T, 0.84), m(258), T);
  g.bezierCurveTo(m(270), lerp(T, B, 0.35), m(300), lerp(T, B, 0.7), m(306), B - 6);
  g.bezierCurveTo(m(280), B + 4, m(250), B - 10, m(226), B);
  g.bezierCurveTo(m(205), B + 8, m(190), B - 4, m(176), B);
  g.bezierCurveTo(m(184), lerp(T, B, 0.6), m(190), lerp(T, B, 0.27), m(194), T);
  g.bezierCurveTo(m(190), lerp(R, T, 0.6), m(186), lerp(R, T, 0.3), m(186), R);
  g.closePath();
}
function drawCurtains(g, L) {
  for (const side of [-1, 1]) {
    const cxm = side < 0 ? 240 : 2 * WIN.cx - 240;
    const base = litCol(COL.curtain, cxm, TIE_Y, L, 0.62, 1.15);
    const dk = litCol(COL.curtainDk, cxm, TIE_Y, L, 0.62, 1.15);
    curtainPath(g, side);
    g.fillStyle = base; g.fill();
    g.save();
    curtainPath(g, side); g.clip();
    // folds: soft vertical bands that pinch at the tieback
    for (let i = 0; i < 6; i++) {
      const u = i / 5;
      const xTop = lerp(186, 300, u), xTie = lerp(196, 258, u), xBot = lerp(178, 304, u);
      const m = (x) => (side < 0 ? x : 2 * WIN.cx - x);
      const gf = g.createLinearGradient(m(xTie) - 12, 0, m(xTie) + 12, 0);
      gf.addColorStop(0, rgba(dk, 0)); gf.addColorStop(0.5, rgba(dk, 0.55)); gf.addColorStop(1, rgba(dk, 0));
      g.strokeStyle = rgba(dk, 0.5); g.lineWidth = 9;
      g.beginPath(); g.moveTo(m(xTop + 6), ROD_Y); g.bezierCurveTo(m(xTop + 4), lerp(ROD_Y, TIE_Y, 0.6), m(xTie), TIE_Y - 50, m(xTie), TIE_Y); g.bezierCurveTo(m(xTie), TIE_Y + 70, m(xBot), CURT_BOT - 90, m(xBot), CURT_BOT + 10); g.stroke();
      g.strokeStyle = rgba('#ffffff', 0.06 + (side < 0 ? 0.06 * L : 0)); g.lineWidth = 4;
      g.beginPath(); g.moveTo(m(xTop - 7), ROD_Y); g.bezierCurveTo(m(xTop - 8), lerp(ROD_Y, TIE_Y, 0.6), m(xTie - 6), TIE_Y - 50, m(xTie - 6), TIE_Y); g.bezierCurveTo(m(xTie - 6), TIE_Y + 70, m(xBot - 8), CURT_BOT - 90, m(xBot - 8), CURT_BOT + 10); g.stroke();
    }
    // warm light on the left curtain / shade on the inner edge of the right one
    const gl = g.createLinearGradient(0, TIE_Y - 120, 0, CURT_BOT + 10);
    gl.addColorStop(0, 'rgba(0,0,0,0.15)'); gl.addColorStop(1, `rgba(255,170,110,${side < 0 ? 0.2 * L : 0.05 * L})`);
    g.fillStyle = gl; g.fillRect(0, ROD_Y, RW, CURT_BOT - ROD_Y + 20);
    g.restore();
    curtainPath(g, side);
    g.strokeStyle = rgba(COL.line, 0.75); g.lineWidth = 2.6; g.stroke();
    // tieback
    const m = (x) => (side < 0 ? x : 2 * WIN.cx - x);
    g.fillStyle = litCol('#e2b85c', cxm, TIE_Y, L, 0.6); g.strokeStyle = rgba(COL.line, 0.8); g.lineWidth = 2.2;
    g.beginPath();
    g.moveTo(m(190), TIE_Y - 8); g.quadraticCurveTo(m(226), TIE_Y - 14, m(262), TIE_Y - 8); g.lineTo(m(262), TIE_Y + 6); g.quadraticCurveTo(m(226), TIE_Y, m(190), TIE_Y + 6);
    g.closePath(); g.fill(); g.stroke();
  }
  // rod
  const rodC = litCol('#8a6a4a', 240, ROD_Y, L, 0.55);
  g.strokeStyle = rgba(COL.line, 0.9); g.lineWidth = 9; g.lineCap = 'round';
  g.beginPath(); g.moveTo(170, ROD_Y - 4); g.lineTo(694, ROD_Y - 4); g.stroke();
  g.strokeStyle = rodC; g.lineWidth = 5;
  g.beginPath(); g.moveTo(170, ROD_Y - 4); g.lineTo(694, ROD_Y - 4); g.stroke();
  for (const fx of [166, 698]) {
    g.fillStyle = rodC; g.strokeStyle = rgba(COL.line, 0.9); g.lineWidth = 2;
    circle(g, fx, ROD_Y - 4, 8); g.fill(); g.stroke();
  }
}

// fairy lights: wire draped along the rod
const FAIRY_N = 13;
const fairyX = (i) => lerp(198, 666, i / (FAIRY_N - 1));
const wireY = (x) => {
  // two shallow swags
  const u = (x - 198) / (666 - 198);
  return ROD_Y + 4 + Math.abs(Math.sin(u * Math.PI * 2)) * 30 + 6;
};
const FAIRY_COLS = ['#ffd27a', '#ffb3a0', '#fff0b0', '#ffc070'];
function drawFairyWire(g, L) {
  g.strokeStyle = rgba('#2a2230', 0.85); g.lineWidth = 1.6;
  g.beginPath();
  for (let x = 198; x <= 666; x += 6) { const y = wireY(x); if (x === 198) g.moveTo(x, y); else g.lineTo(x, y); }
  g.stroke();
}
function drawFairyBulbs(g, s) {
  if (s.fairy <= 0.01) return;
  for (let i = 0; i < FAIRY_N; i++) {
    const x = fairyX(i), y = wireY(x) + 6;
    const b = s.fairy * (0.72 + 0.28 * Math.sin(s.t * 0.8 + i * 2.1));
    const col = FAIRY_COLS[i % FAIRY_COLS.length];
    const gr = g.createRadialGradient(x, y, 0, x, y, 18);
    gr.addColorStop(0, rgba(col, 0.5 * b)); gr.addColorStop(1, rgba(col, 0));
    g.fillStyle = gr; g.fillRect(x - 18, y - 18, 36, 36);
    g.fillStyle = mixColor('#6a5040', '#fff6dc', b);
    ellipse(g, x, y, 3.2, 4.2); g.fill();
  }
}

// stars (few, small, gentle twinkle) — drawn over the cached sky
// (all positions verified to sit on open glass: clear of both curtains and the sash bars)
const STARS = [[318, 150, 2.6], [352, 132, 2], [408, 196, 1.8], [470, 140, 2.4], [546, 170, 2.6], [558, 228, 1.8], [500, 262, 1.6], [300, 236, 1.9], [566, 316, 2], [372, 318, 1.6], [298, 334, 1.7], [452, 300, 1.4], [300, 404, 1.5], [394, 392, 1.3], [490, 384, 1.2]];
function drawStars(g, s) {
  const a0 = 1 - s.dusk * 0.6;
  const night = 1 - s.lamp; // eyes adjust once the lamp is off: the stars brighten and grow a touch
  for (let i = 0; i < STARS.length; i++) {
    const [x, y, r] = STARS[i];
    const tw = 0.6 + 0.4 * Math.sin(s.t * (0.7 + (i % 4) * 0.23) + i * 1.9);
    g.fillStyle = `rgba(255,248,225,${Math.min(1, (0.85 + 0.15 * night) * tw * a0)})`;
    const rr = r * (0.85 + 0.3 * tw) * (1 + 0.25 * night);
    g.beginPath();
    g.moveTo(x, y - rr * 2); g.quadraticCurveTo(x, y, x + rr * 2, y); g.quadraticCurveTo(x, y, x, y + rr * 2); g.quadraticCurveTo(x, y, x - rr * 2, y); g.quadraticCurveTo(x, y, x, y - rr * 2);
    g.fill();
    g.fillStyle = `rgba(200,215,255,${(0.18 + 0.1 * night) * tw * a0})`;
    circle(g, x, y, rr * 3); g.fill();
  }
}

// ---- s20 ending: "a faint hooded shape made of stars seems to stand among them; one star twinkles"
// Star points of a tall hood standing on the far hills (world coords, in the window glass).
const HOOD_STARS = [[412, 150, 2.2], [389, 163, 1.6], [377, 190, 1.8], [380, 222, 1.5], [435, 163, 1.6], [447, 190, 1.8], [444, 222, 1.5],
  [340, 252, 2], [484, 252, 2], [324, 340, 1.7], [500, 340, 1.7], [316, 436, 1.9], [412, 446, 1.5], [508, 434, 1.9]];
// polylines through HOOD_STARS: left edge (peak → hood → shoulder → hem), right edge, hem
const HOOD_LINES = [[0, 1, 2, 3, 7, 9, 11], [0, 4, 5, 6, 8, 10, 13], [11, 12, 13]];
const HOOD_FACE = [412, 196, 12, 17]; // the dark hood opening; its centre star is the one that twinkles
function hoodOutline(g) {
  const P = HOOD_STARS;
  g.beginPath();
  g.moveTo(P[0][0], P[0][1]);
  for (const i of [1, 2, 3, 7, 9, 11, 12, 13, 10, 8, 6, 5, 4]) g.lineTo(P[i][0], P[i][1]);
  g.closePath();
}
function glassClip(g) {
  const { x0, x1, y0, y1, rail, cx } = WIN;
  g.beginPath();
  g.rect(x0, y0, x1 - x0, rail - 8 - y0);
  g.rect(x0, rail + 8, cx - 5 - x0, y1 - rail - 8);
  g.rect(cx + 5, rail + 8, x1 - cx - 5, y1 - rail - 8);
  g.clip();
}
function drawStarHood(g, s) {
  const k = s.starHood, wink = s.starWink;
  if (k <= 0.005 && wink <= 0.005) return;
  g.save();
  glassClip(g);
  if (k > 0.005) {
    // a whisper of the Void's violet filling the silhouette, the face opening darker
    hoodOutline(g);
    g.fillStyle = `rgba(138,108,255,${0.07 * k})`; g.fill();
    const [fx, fy, fr, fh] = HOOD_FACE;
    const gf = g.createRadialGradient(fx, fy, 2, fx, fy, fh * 1.3);
    gf.addColorStop(0, `rgba(4,6,24,${0.45 * k})`); gf.addColorStop(1, 'rgba(4,6,24,0)');
    g.fillStyle = gf; ellipse(g, fx, fy, fr * 1.3, fh * 1.3); g.fill();
    // constellation lines
    g.strokeStyle = `rgba(190,205,255,${0.2 * k})`; g.lineWidth = 1.1; g.lineJoin = 'round';
    for (const L of HOOD_LINES) {
      g.beginPath();
      L.forEach((i, j) => (j ? g.lineTo(HOOD_STARS[i][0], HOOD_STARS[i][1]) : g.moveTo(HOOD_STARS[i][0], HOOD_STARS[i][1])));
      g.stroke();
    }
    g.strokeStyle = `rgba(190,205,255,${0.12 * k})`;
    ellipse(g, fx, fy, fr, fh); g.stroke();
    // the stars of the shape
    for (let i = 0; i < HOOD_STARS.length; i++) {
      const [x, y, r] = HOOD_STARS[i];
      const tw = 0.75 + 0.25 * Math.sin(s.t * (0.6 + (i % 3) * 0.2) + i * 2.3);
      g.fillStyle = `rgba(200,215,255,${0.22 * k * tw})`; circle(g, x, y, r * 3.2); g.fill();
      g.fillStyle = `rgba(255,250,235,${0.95 * k * tw})`; sparkle(g, x, y, r * 1.9);
    }
  }
  if (wink > 0.005) {
    // the single twinkle, inside the dark hood opening
    const [fx, fy] = HOOD_FACE;
    const R = 3 + 11 * wink;
    const gw = g.createRadialGradient(fx, fy, 0, fx, fy, R * 1.6);
    gw.addColorStop(0, `rgba(235,240,255,${0.5 * wink})`); gw.addColorStop(1, 'rgba(200,215,255,0)');
    g.fillStyle = gw; g.fillRect(fx - R * 1.6, fy - R * 1.6, R * 3.2, R * 3.2);
    g.fillStyle = `rgba(255,252,240,${Math.min(1, 0.4 + wink)})`;
    sparkle(g, fx, fy, R);
  }
  g.restore();
}
function sparkle(g, x, y, r) {
  g.beginPath();
  g.moveTo(x, y - r); g.quadraticCurveTo(x, y, x + r, y); g.quadraticCurveTo(x, y, x, y + r); g.quadraticCurveTo(x, y, x - r, y); g.quadraticCurveTo(x, y, x, y - r);
  g.fill();
}

function drawShelf(g, L) {
  const sx0 = 70, sx1 = 176, sy = 330;
  // picture frame with a child's crayon drawing
  g.save();
  g.translate(122, 226); g.rotate(-0.035);
  g.fillStyle = 'rgba(10,5,20,0.3)'; g.fillRect(-40, -46, 88, 100);
  g.fillStyle = litCol(COL.wood, 104, 250, L, 0.6); g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 2.4;
  g.fillRect(-44, -50, 88, 100); g.strokeRect(-44, -50, 88, 100);
  g.fillStyle = litCol('#f3ead2', 104, 250, L, 0.55); g.fillRect(-34, -40, 68, 80);
  // crayon sun + house + little lavender figure
  g.fillStyle = litCol('#f2b632', 104, 250, L, 0.6); circle(g, 18, -22, 9); g.fill();
  g.strokeStyle = litCol('#f2b632', 104, 250, L, 0.6); g.lineWidth = 1.6;
  for (let k = 0; k < 8; k++) { const a = k * TAU / 8; g.beginPath(); g.moveTo(18 + Math.cos(a) * 12, -22 + Math.sin(a) * 12); g.lineTo(18 + Math.cos(a) * 16, -22 + Math.sin(a) * 16); g.stroke(); }
  g.fillStyle = litCol('#d9584a', 104, 250, L, 0.6);
  g.beginPath(); g.moveTo(-26, 4); g.lineTo(-10, -12); g.lineTo(6, 4); g.closePath(); g.fill();
  g.fillStyle = litCol('#6a8fd0', 104, 250, L, 0.6); g.fillRect(-23, 4, 26, 22);
  g.fillStyle = litCol('#a98ee6', 104, 250, L, 0.6); ellipse(g, 20, 18, 7, 9); g.fill();
  g.fillStyle = litCol('#5aa060', 104, 250, L, 0.6); g.fillRect(-34, 30, 68, 10);
  g.restore();
  // books on the shelf
  const books = [[64, 60, 14, 0], [79, 70, 16, 1], [96, 64, 12, 2], [109, 72, 15, 3], [125, 58, 13, 4]];
  for (const [bx, h, w, ci] of books) {
    const c = litCol(COL.books[ci], bx, sy, L, 0.62);
    g.fillStyle = c; g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 2;
    g.beginPath(); g.roundRect(bx, sy - h, w, h, 2); g.fill(); g.stroke();
    g.fillStyle = 'rgba(255,240,210,0.35)'; g.fillRect(bx + 3, sy - h + 10, w - 6, 3); g.fillRect(bx + 3, sy - 16, w - 6, 2);
  }
  // a leaning book
  g.save(); g.translate(141, sy); g.rotate(0.32);
  g.fillStyle = litCol(COL.books[5], 120, sy, L, 0.62); g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 2;
  g.beginPath(); g.roundRect(0, -60, 14, 60, 2); g.fill(); g.stroke();
  g.restore();
  // pot + trailing plant
  const px = 160, py = sy;
  g.fillStyle = litCol(COL.pot, px, py, L, 0.6); g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 2.2;
  g.beginPath(); g.moveTo(px - 18, py - 34); g.lineTo(px + 18, py - 34); g.lineTo(px + 14, py); g.lineTo(px - 14, py); g.closePath(); g.fill(); g.stroke();
  g.fillRect(px - 20, py - 40, 40, 8); g.strokeRect(px - 20, py - 40, 40, 8);
  // shelf board + brackets
  const gb = g.createLinearGradient(0, sy, 0, sy + 12);
  gb.addColorStop(0, litCol(COL.woodHi, 100, sy, L, 0.6)); gb.addColorStop(1, litCol(COL.woodDk, 100, sy, L, 0.6));
  g.fillStyle = gb; g.strokeStyle = rgba(COL.line, 0.9); g.lineWidth = 2.4;
  g.beginPath(); g.rect(sx0 - 40, sy, sx1 - sx0 + 40, 12); g.fill(); g.stroke();
  g.fillStyle = 'rgba(10,5,20,0.3)'; g.fillRect(sx0 - 40, sy + 12, sx1 - sx0 + 40, 8);
  for (const bx of [60, 158]) {
    g.fillStyle = litCol(COL.woodDk, bx, sy, L, 0.6);
    g.beginPath(); g.moveTo(bx - 4, sy + 12); g.lineTo(bx + 4, sy + 12); g.lineTo(bx + 4, sy + 36); g.closePath(); g.fill(); g.stroke();
  }
  // vines draping from the pot (in front of the shelf edge)
  const leafC = litCol(COL.plant, 150, 420, L, 0.55), leafDk = litCol(COL.plantDk, 150, 420, L, 0.55);
  const vines = [[[px - 2, py - 36], [px + 12, py - 10], [px + 18, py + 60], [px + 12, py + 140], [px + 18, py + 190]], [[px - 6, py - 36], [px - 22, py + 10], [px - 24, py + 70], [px - 14, py + 120]], [[px + 4, py - 38], [px + 26, py - 40], [px + 30, py + 20], [px + 24, py + 80]], [[px - 2, py - 40], [px - 12, py - 70], [px - 28, py - 66]]];
  vines.forEach((v, vi) => {
    g.strokeStyle = leafDk; g.lineWidth = 2.2;
    g.beginPath(); g.moveTo(v[0][0], v[0][1]);
    for (let i = 1; i < v.length; i++) { const m = [(v[i - 1][0] + v[i][0]) / 2, (v[i - 1][1] + v[i][1]) / 2]; g.quadraticCurveTo(v[i - 1][0], v[i - 1][1], m[0], m[1]); }
    g.lineTo(v[v.length - 1][0], v[v.length - 1][1]); g.stroke();
    for (let i = 1; i < v.length; i++) {
      for (const k of [0.35, 0.85]) {
        const x = lerp(v[i - 1][0], v[i][0], k), y = lerp(v[i - 1][1], v[i][1], k);
        const side = (i + (k > 0.5 ? 1 : 0) + vi) % 2 ? 1 : -1;
        drawLeaf(g, x + side * 6, y, 9, 7, side * 0.9 + 0.3, leafC, leafDk);
      }
    }
  });
}
function drawLeaf(g, x, y, l, w, ang, c, dk) {
  g.save(); g.translate(x, y); g.rotate(ang);
  g.fillStyle = c; g.strokeStyle = rgba(COL.line, 0.75); g.lineWidth = 1.6;
  g.beginPath(); g.moveTo(-l, 0); g.quadraticCurveTo(0, -w, l, 0); g.quadraticCurveTo(0, w, -l, 0); g.closePath(); g.fill(); g.stroke();
  g.strokeStyle = rgba(dk, 0.8); g.lineWidth = 1; g.beginPath(); g.moveTo(-l * 0.7, 0); g.lineTo(l * 0.7, 0); g.stroke();
  g.restore();
}

function drawRightFrame(g, L) {
  // small framed doodle on the right wall (a crayon heart + stars)
  const x = 748, y = 478;
  g.save(); g.translate(x, y); g.rotate(0.04);
  g.fillStyle = 'rgba(10,5,20,0.3)'; g.fillRect(-30, -34, 66, 76);
  g.fillStyle = litCol(COL.woodDk, x, y, L, 0.6); g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 2.2;
  g.fillRect(-34, -38, 66, 76); g.strokeRect(-34, -38, 66, 76);
  g.fillStyle = litCol('#f3ead2', x, y, L, 0.55); g.fillRect(-26, -30, 50, 60);
  g.fillStyle = litCol('#e0465a', x, y, L, 0.55);
  g.beginPath(); g.moveTo(-1, 14); g.bezierCurveTo(-20, -2, -12, -18, -1, -7); g.bezierCurveTo(10, -18, 18, -2, -1, 14); g.fill();
  g.fillStyle = litCol('#f2c53d', x, y, L, 0.55);
  for (const [sx, sy] of [[-16, -20], [14, -22], [12, 20]]) { circle(g, sx, sy, 3); g.fill(); }
  g.restore();
}

function drawHangingPlant(g, L) {
  const px = 742, py = 206;
  g.strokeStyle = rgba('#d8c7a6', 0.35 + 0.2 * L); g.lineWidth = 1.6;
  for (const dx of [-26, 0, 26]) { g.beginPath(); g.moveTo(px, 0); g.lineTo(px + dx, py - 26); g.stroke(); }
  const leafC = litCol(COL.plant, 640, 300, L, 0.62), leafDk = litCol(COL.plantDk, 640, 300, L, 0.62);
  // trailing strands
  const strands = [[[px - 10, py], [px - 30, py + 60], [px - 38, py + 130], [px - 30, py + 210]], [[px + 10, py], [px, py + 80], [px + 10, py + 170]], [[px - 22, py - 10], [px - 50, py + 30], [px - 62, py + 100]], [[px + 24, py - 6], [px + 40, py + 60], [px + 34, py + 120]]];
  for (const v of strands) {
    g.strokeStyle = leafDk; g.lineWidth = 2;
    g.beginPath(); g.moveTo(v[0][0], v[0][1]);
    for (let i = 1; i < v.length; i++) g.lineTo(v[i][0], v[i][1]);
    g.stroke();
    for (let i = 1; i < v.length; i++) {
      const x = lerp(v[i - 1][0], v[i][0], 0.6), y = lerp(v[i - 1][1], v[i][1], 0.6);
      drawLeaf(g, x - 6, y, 10, 8, 2.2 + i * 0.3, leafC, leafDk);
      drawLeaf(g, x + 6, y + 14, 9, 7, 0.9 - i * 0.2, leafC, leafDk);
    }
  }
  g.fillStyle = litCol('#d8c7a6', px, py, L, 0.6); g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 2.2;
  g.beginPath(); g.moveTo(px - 32, py - 28); g.lineTo(px + 32, py - 28); g.quadraticCurveTo(px + 30, py + 10, px, py + 12); g.quadraticCurveTo(px - 30, py + 10, px - 32, py - 28); g.closePath(); g.fill(); g.stroke();
  for (const [dx, a] of [[-22, -2.2], [-8, -1.7], [10, -1.3], [24, -0.9]]) drawLeaf(g, px + dx, py - 34, 13, 9, a, leafC, leafDk);
}

// ------------------------------------------------------------------ desk
function drawDeskTop(g, L) {
  const gd = g.createLinearGradient(0, DESK_Y, 0, DESK_NEAR);
  gd.addColorStop(0, litCol(COL.deskFar, 380, DESK_Y, L, 0.62));
  gd.addColorStop(1, litCol(COL.desk, 380, DESK_NEAR, L, 0.62));
  g.fillStyle = gd;
  g.fillRect(0, DESK_Y, RW, DESK_NEAR - DESK_Y);
  // plank seams + grain (converge gently toward a vanishing point high above)
  g.strokeStyle = rgba(COL.line, 0.18); g.lineWidth = 1.4;
  for (const y of [DESK_Y + 38, DESK_Y + 84]) { g.beginPath(); g.moveTo(0, y); g.lineTo(RW, y); g.stroke(); }
  g.strokeStyle = rgba('#000000', 0.06); g.lineWidth = 1;
  for (let i = 0; i < 6; i++) {
    const y = DESK_Y + 12 + i * 20;
    g.beginPath(); g.moveTo(0, y);
    for (let x = 0; x <= RW; x += 40) g.lineTo(x, y + Math.sin(x * 0.011 + i * 1.3) * 3);
    g.stroke();
  }
  // lamp light pool
  if (L) {
    const cx = 340, cy = 980;
    g.save(); g.translate(cx, cy); g.scale(1, 0.3);
    const gp = g.createRadialGradient(0, 0, 10, 0, 0, 330);
    gp.addColorStop(0, 'rgba(255,224,160,0.6)'); gp.addColorStop(0.4, 'rgba(255,196,120,0.3)'); gp.addColorStop(1, 'rgba(255,180,110,0)');
    g.fillStyle = gp; g.fillRect(-330, -330, 660, 660);
    g.restore();
  }
  // far edge: a crisp dark line + soft contact shadow
  g.strokeStyle = rgba(COL.line, 0.7); g.lineWidth = 2;
  g.beginPath(); g.moveTo(0, DESK_Y); g.lineTo(RW, DESK_Y); g.stroke();
  const gsh = g.createLinearGradient(0, DESK_Y, 0, DESK_Y + 16);
  gsh.addColorStop(0, 'rgba(20,10,8,0.35)'); gsh.addColorStop(1, 'rgba(20,10,8,0)');
  g.fillStyle = gsh; g.fillRect(0, DESK_Y, RW, 16);
}

function buildForeground(g, L) {
  // front lip
  const gl = g.createLinearGradient(0, DESK_NEAR, 0, DESK_LIP);
  gl.addColorStop(0, litCol(COL.woodHi, 300, DESK_NEAR, L, 0.62, 1.3));
  gl.addColorStop(1, litCol(COL.desk, 300, DESK_NEAR, L, 0.62));
  g.fillStyle = gl; g.fillRect(0, DESK_NEAR, RW, DESK_LIP - DESK_NEAR);
  g.strokeStyle = rgba(COL.line, 0.8); g.lineWidth = 2;
  g.beginPath(); g.moveTo(0, DESK_NEAR); g.lineTo(RW, DESK_NEAR); g.stroke();
  // front panel
  const gf = g.createLinearGradient(0, DESK_LIP, 0, RH);
  gf.addColorStop(0, litCol(COL.deskFront, 300, DESK_LIP + 60, L, 0.6, 0.9));
  gf.addColorStop(1, COL.deskFrontDk);
  g.fillStyle = gf; g.fillRect(0, DESK_LIP, RW, RH - DESK_LIP);
  g.beginPath(); g.moveTo(0, DESK_LIP); g.lineTo(RW, DESK_LIP); g.stroke();
  const gsh = g.createLinearGradient(0, DESK_LIP, 0, DESK_LIP + 26);
  gsh.addColorStop(0, 'rgba(10,5,5,0.45)'); gsh.addColorStop(1, 'rgba(10,5,5,0)');
  g.fillStyle = gsh; g.fillRect(0, DESK_LIP, RW, 26);
  // drawer
  const dx0 = 200, dx1 = 640, dy0 = DESK_LIP + 34, dy1 = DESK_LIP + 150;
  g.strokeStyle = rgba('#000000', 0.45); g.lineWidth = 3;
  g.beginPath(); g.roundRect(dx0, dy0, dx1 - dx0, dy1 - dy0, 6); g.stroke();
  g.strokeStyle = rgba(litCol(COL.woodHi, 300, dy0, L, 0.6), 0.35); g.lineWidth = 1.5;
  g.beginPath(); g.moveTo(dx0 + 6, dy1 + 2); g.lineTo(dx1 - 4, dy1 + 2); g.stroke();
  const kx = (dx0 + dx1) / 2, ky = (dy0 + dy1) / 2;
  const gk = g.createRadialGradient(kx - 3, ky - 3, 1, kx, ky, 10);
  gk.addColorStop(0, litCol('#ffe2a0', kx, ky, L, 0.6)); gk.addColorStop(1, litCol('#a87a3a', kx, ky, L, 0.6));
  g.fillStyle = gk; g.strokeStyle = rgba(COL.line, 0.9); g.lineWidth = 2;
  circle(g, kx, ky, 9); g.fill(); g.stroke();
  // book stack (right back of desk)
  drawBookStack(g, L, 700, 950);
  // crayons near the notebook spot
  drawCrayons(g, L, 520, 1008);
  // mug
  drawMug(g, L, MUG[0], MUG[1]);
  // lamp (with light cone + halo when lit)
  drawDeskLamp(g, LAMP_POS[0], LAMP_POS[1], LAMP_POS[2], { on: L, t: 0, cone: 0.45, night: L ? 0 : 0.85, nightColor: NIGHT_TINT });
  // warm light kissing the lip near the lamp
  if (L) {
    g.save(); g.translate(260, DESK_NEAR + 6); g.scale(1, 0.12);
    const gp = g.createRadialGradient(0, 0, 4, 0, 0, 300);
    gp.addColorStop(0, 'rgba(255,220,160,0.45)'); gp.addColorStop(1, 'rgba(255,220,160,0)');
    g.fillStyle = gp; g.fillRect(-300, -300, 600, 600);
    g.restore();
  }
}

function drawBookStack(g, L, x, y) {
  const books = [[0, 0, 128, 18, 1], [6, -18, 112, 16, 3], [-2, -34, 120, 14, 4]];
  for (const [dx, dy, w, h, ci] of books) {
    const c = litCol(COL.books[ci], x, y, L, 0.62);
    g.fillStyle = c; g.strokeStyle = rgba(COL.line, 0.9); g.lineWidth = 2.2;
    g.beginPath(); g.roundRect(x + dx - w / 2, y + dy - h, w, h, 3); g.fill(); g.stroke();
    g.fillStyle = litCol('#efe2c4', x, y, L, 0.6);
    g.fillRect(x + dx + w / 2 - 14, y + dy - h + 3, 10, h - 6);
    g.fillStyle = 'rgba(255,240,210,0.3)'; g.fillRect(x + dx - w / 2 + 8, y + dy - h + 4, 30, 3);
  }
  g.fillStyle = 'rgba(20,10,8,0.3)';
  ellipse(g, x, y + 3, 72, 6); g.fill();
}

function drawCrayons(g, L, x, y) {
  const cr = [[0, 0, -0.18, '#e0303a'], [26, 10, 0.12, '#f2c53d'], [10, 22, -0.05, '#8a6ad8']];
  for (const [dx, dy, a, col] of cr) {
    g.save(); g.translate(x + dx, y + dy); g.rotate(a);
    g.fillStyle = 'rgba(20,10,8,0.3)'; g.beginPath(); g.roundRect(-26, 1, 52, 7, 3); g.fill();
    g.fillStyle = litCol(col, x, y, L, 0.55, 1.2); g.strokeStyle = rgba(COL.line, 0.85); g.lineWidth = 1.6;
    g.beginPath(); g.moveTo(-26, -4); g.lineTo(18, -4); g.lineTo(28, 0); g.lineTo(18, 4); g.lineTo(-26, 4); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(-10, -4, 14, 8);
    g.restore();
  }
}

function drawMug(g, L, x, y) {
  const w = 58, h = 62;
  g.fillStyle = 'rgba(20,10,8,0.35)'; ellipse(g, x + 6, y + 2, 40, 7); g.fill();
  const body = litCol('#e9dcc6', x, y, L, 0.58, 1.3), bodyDk = litCol('#a8987e', x, y, L, 0.6);
  // handle
  g.strokeStyle = rgba(COL.line, 0.9); g.lineWidth = 11;
  g.beginPath(); g.ellipse(x + w / 2 + 4, y - h / 2, 15, 17, 0, -1.3, 1.3); g.stroke();
  g.strokeStyle = body; g.lineWidth = 6;
  g.beginPath(); g.ellipse(x + w / 2 + 4, y - h / 2, 15, 17, 0, -1.3, 1.3); g.stroke();
  // body
  const gb = g.createLinearGradient(x - w / 2, 0, x + w / 2, 0);
  gb.addColorStop(0, mixColor(body, '#ffffff', 0.2)); gb.addColorStop(0.45, body); gb.addColorStop(1, bodyDk);
  g.fillStyle = gb; g.strokeStyle = rgba(COL.line, 0.9); g.lineWidth = 2.4;
  g.beginPath();
  g.moveTo(x - w / 2, y - h);
  g.lineTo(x - w / 2 + 2, y - 6); g.quadraticCurveTo(x, y + 6, x + w / 2 - 2, y - 6);
  g.lineTo(x + w / 2, y - h);
  g.closePath(); g.fill(); g.stroke();
  // rim + cocoa
  g.fillStyle = mixColor(body, '#ffffff', 0.15);
  ellipse(g, x, y - h, w / 2, 8); g.fill(); g.stroke();
  g.fillStyle = litCol('#6a3a24', x, y, L, 0.6);
  ellipse(g, x, y - h + 1, w / 2 - 5, 5.5); g.fill();
  // little heart
  g.fillStyle = litCol('#d9534f', x, y, L, 0.55, 1.2);
  const hx = x - 4, hy = y - 30, s = 1.1;
  g.beginPath();
  g.moveTo(hx, hy + 6 * s);
  g.bezierCurveTo(hx - 10 * s, hy - 2 * s, hx - 6 * s, hy - 10 * s, hx, hy - 4 * s);
  g.bezierCurveTo(hx + 6 * s, hy - 10 * s, hx + 10 * s, hy - 2 * s, hx, hy + 6 * s);
  g.fill();
}

// ------------------------------------------------------------------ dynamic foreground bits
function drawSteam(g, s) {
  const [x, y] = MUG;
  const top = y - 66;
  g.save();
  g.lineCap = 'round';
  for (let k = 0; k < 2; k++) {
    const ph = s.t * 0.35 + k * 0.5;
    const cyc = ph - Math.floor(ph);           // rising cycle 0..1
    const a = Math.sin(cyc * Math.PI) * 0.16;
    const ox = (k ? 9 : -7);
    g.strokeStyle = `rgba(255,245,230,${a})`;
    g.lineWidth = 5 - cyc * 2;
    g.beginPath();
    const y0 = top - cyc * 18;
    g.moveTo(x + ox, y0);
    for (let i = 1; i <= 6; i++) {
      const yy = y0 - i * 11;
      const xx = x + ox + Math.sin(i * 0.9 + s.t * 0.9 + k * 2) * (3 + i * 1.4);
      g.lineTo(xx, yy);
    }
    g.stroke();
  }
  g.restore();
}

function drawMotes(g, s) {
  const [mx, my] = LAMP_MOUTH;
  g.save();
  for (let i = 0; i < 11; i++) {
    const u = rand(i, 301), v = rand(i, 302);
    // along the cone, drifting slowly
    const along = 40 + u * 190 + fbm(s.t * 0.07 + i, 303) * 30;
    const across = (v - 0.5) * (40 + along * 0.7) + fbm(s.t * 0.09 + i * 3, 304) * 18;
    const dx = 0.58, dy = 0.81; // lamp direction (facing right)
    const rise = ((s.t * 3 + i * 17) % 40) / 40;   // slow rise, faded in/out so the wrap never pops
    const x = mx + dx * along - dy * across, y = my + dy * along + dx * across - rise * 40;
    const tw = (0.5 + 0.5 * Math.sin(s.t * 1.1 + i * 2.3)) * Math.sin(Math.PI * rise);
    g.fillStyle = `rgba(255,236,190,${0.32 * s.lamp * tw})`;
    circle(g, x, y, 1.3 + (i % 3) * 0.5); g.fill();
  }
  g.restore();
}
