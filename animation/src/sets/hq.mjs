// MIND HQ — the control room inside the mind, its console, the screen of consciousness, the fire-alarm
// station and the deep BACK OF THE MIND where the Void stands.
//
//   drawHQ(g, view, state)            room / set for a view (call after applyCamera, before characters)
//   drawHQForeground(g, view, state)  layers that sit IN FRONT of characters (console front panel, low mist)
//   drawAlarmLight(g, view, state)    soft red alarm light (beacon sweep + gentle wash), after characters
//   drawScreenContent(g, x, y, w, h, t, mode)   what the screen of consciousness shows
//   drawConsole(g, x, y, w, scale, state)       the control console (x,y = centre of its base on the floor)
//   drawAlarmStation(g, x, y, scale, state)     pull station + bell + strobe (x,y = handle rest centre)
//   HQ_VIEWS[view] = { width, height, anchors: { name: [x, y, charScale] }, cams: { name: {x,y,zoom} } }
//   hqScaleAt(view, y)                perspective character scale for a floor point at world y
//   HQ_PRESETS (state bundles), ALARM_REACH (FEAR arm target for the handle), consoleButtonPos(), HQ_COLORS,
//   HQ_STATIONS (which emotion works which console station, and its anchor in the front / back views)
//
// Every view is its own world-coordinate stage. Static artwork is cached per view and per resolution level
// (the level is picked from the current transform, so camera push-ins stay crisp).
// See docs/hq.md for the full reference.

import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import { fileURLToPath } from 'url';
import { clamp, lerp, TAU, fbm, noise1, rand, rgba, shade, mixColor, ellipse, circle, roundRect, glow } from '../engine.mjs';
import { drawNotebook } from './props.mjs';

// ---------------------------------------------------------------- fonts
try {
  const dir = fileURLToPath(new URL('../../assets/fonts/', import.meta.url));
  for (const [f, n] of [['Fraunces.ttf', 'Fraunces'], ['PatrickHand.ttf', 'Patrick Hand'], ['Caveat.ttf', 'Caveat']]) {
    if (!GlobalFonts.has(n)) GlobalFonts.registerFromPath(dir + f, n);
  }
} catch { /* fonts optional */ }

// ---------------------------------------------------------------- palette
export const HQ_COLORS = {
  wallDeep: '#1d1936', wall: '#2b2550', wallLight: '#3a3266',
  trim: '#41377a', trimLight: '#7563b8', trimDark: '#120f24',
  floorFar: '#2e2758', floor: '#241e45', floorNear: '#1a1532',
  backMind: '#0d0b1c', haze: '#2c2356',
  line: '#151027',
  amber: '#ffcf7a', amberHot: '#fff0c8', amberDeep: '#ff9f43',
  screen: '#9fd8ff', screenLight: '#cfeeff',
  red: '#ff4d5e', redDeep: '#c92a3f', redDark: '#4e1222',
  exit: '#8dffc0', exitDeep: '#1f7a55',
  violet: '#8a6cff', cyan: '#5ad1ff', lamp: '#ffd89a', lampDeep: '#ffb35c',
};
const C = HQ_COLORS;

// ---------------------------------------------------------------- view geometry
// One-point perspective per view: world point (X, Yup, lam) -> screen (vx + lam*X, vy + lam*(eye - Yup)).
// lam = 1 on the view's reference plane, bigger = nearer the camera. Characters standing at lam get
// scale charK*lam.  f = focal length in reference-plane px (for foreshortening props on side walls).
const GEO = {
  front: { W: 900, H: 1600, vx: 450, vy: 520, eye: 320, hw: 232, spring: 450, f: 900, charK: 0.296 },
  back: { W: 900, H: 1600, vx: 450, vy: 430, eye: 330, hw: 340, spring: 520, f: 900, charK: 0.362 },
  alarm: { W: 1000, H: 1600, vx: 500, vy: 700, wallBase: 1360, charK: 1.8 / 706 },
  backOfMind: { W: 1000, H: 1778, vx: 330, vy: 1040, eye: 620, charK: 1 / 620 },
};
const proj = (G) => (X, Y, l) => [G.vx + l * X, G.vy + l * (G.eye - Y)];

// front-view console: base y (off-stage) — its top rim sits at y ~1247 (centre) .. 1268 (ends)
const FRONT_CONSOLE_Y = 1760;
// alarm station placements (handle rest centre, world) per view
const ALARM_FRONT = { lam: 1.42, yup: 180 * GEO.front.charK, cheat: 0.5 };
// FEAR's arm target (character-local) that lands its hand on the handle from the fear*/Alarm anchors
export const ALARM_REACH = [108, -176];
const ALARM_CLOSE = { x: 692, y: 1089, s: 1.8 };
const ALARM_SCONCE = [330, 600];
const ALARM_NOTE = [488, 700];

function frontAlarmHandle() {
  const G = GEO.front, P = proj(G);
  return P(G.hw, ALARM_FRONT.yup, ALARM_FRONT.lam);
}

/** perspective character scale for a floor point at world y in a view */
export function hqScaleAt(view, y) {
  const G = GEO[view] || GEO.front;
  if (view === 'alarm') return (y - G.vy) * G.charK;
  if (view === 'backOfMind') return (y - G.vy) * G.charK;
  return ((y - G.vy) / G.eye) * G.charK;
}

export const HQ_VIEWS = {
  front: {
    width: 900, height: 1600,
    anchors: {},
    cams: {
      wide: { x: 450, y: 800, zoom: 0.8 },
      establish: { x: 450, y: 800, zoom: 0.9 },
      console: { x: 450, y: 1120, zoom: 1.35 },
      alarm: { x: 700, y: 880, zoom: 1.9 },
      void: { x: 450, y: 560, zoom: 1.25 },
      door: { x: 215, y: 820, zoom: 1.7 },
    },
  },
  back: {
    width: 900, height: 1600,
    anchors: {},
    cams: {
      wide: { x: 450, y: 800, zoom: 0.8 },
      screen: { x: 450, y: 640, zoom: 1.0 },
      console: { x: 450, y: 760, zoom: 1.5 },
      foreground: { x: 450, y: 960, zoom: 1.0 },
    },
  },
  alarm: {
    width: 1000, height: 1600,
    anchors: {},
    cams: {
      wide: { x: 500, y: 800, zoom: 0.8 },
      medium: { x: 445, y: 960, zoom: 1.0 },
      twoShot: { x: 430, y: 1065, zoom: 1.2 },
      pull: { x: 630, y: 1000, zoom: 1.45 },
      bell: { x: 660, y: 640, zoom: 1.6 },
    },
  },
  backOfMind: {
    width: 1000, height: 1778,
    anchors: {},
    cams: {
      wide: { x: 500, y: 889, zoom: 0.72 },
      ground: { x: 500, y: 1138, zoom: 1.0 },
      cage: { x: 360, y: 1335, zoom: 1.45 },
      hood: { x: 675, y: 520, zoom: 1.25 },
      distance: { x: 360, y: 1040, zoom: 1.6 },
    },
  },
};

// fill anchors (computed from the perspective so they sit exactly on the floor)
{
  const G = GEO.front, P = proj(G), k = G.charK;
  const at = (x, lam) => [Math.round(x), Math.round(P(0, 0, lam)[1]), +(k * lam).toFixed(3)];
  const [hx, hy] = frontAlarmHandle();
  const fs = +(k * ALARM_FRONT.lam).toFixed(3);
  HQ_VIEWS.front.anchors = {
    consoleSlot1: at(165, 2.7), consoleSlot2: at(355, 2.7), consoleSlot3: at(545, 2.7), consoleSlot4: at(735, 2.7),
    // the middle of the console (between stations 2 and 3) on the floor: CONSCIOUSNESS at work there
    consoleMid: at(450, 2.7),
    // FEAR at the console on its step-stool (feet raised 70 px at scale 1, hidden by the console) so its
    // scarf and shoulders clear the rim like the others; same scale as the console slots
    consoleFear: [450, Math.round(P(0, 0, 2.7)[1] - 70 * k * 2.7), +(k * 2.7).toFixed(3)],
    fearSpot: [Math.round(hx - ALARM_REACH[0] * fs), Math.round(hy - ALARM_REACH[1] * fs), fs],
    alarm: [Math.round(hx), Math.round(hy), fs],
    exitDoor: [Math.round(P(-205, 0, 1.3)[0]), Math.round(P(0, 0, 1.3)[1]), +(k * 1.3).toFixed(3)],
    ceoSpot: at(300, 1.6),
    voidSpot: [450, Math.round(P(0, 0, 0.97)[1]), 0.37],
    cageSpot: [598, Math.round(P(0, 0, 1.02)[1]), 0.3],
  };
}
{
  const G = GEO.back, P = proj(G), k = G.charK;
  const at = (x, lam) => [Math.round(x), Math.round(P(0, 0, lam)[1]), +(k * lam).toFixed(3)];
  HQ_VIEWS.back.anchors = {
    consoleBack1: at(P(-206, 0, 1.5)[0], 1.5), consoleBack2: at(P(-69, 0, 1.5)[0], 1.5),
    consoleBack3: at(P(69, 0, 1.5)[0], 1.5), consoleBack4: at(P(206, 0, 1.5)[0], 1.5),
    // the middle of the console, between stations 2 and 3: CONSCIOUSNESS at work, or FEAR on its stool
    consoleBackMid: at(450, 1.5),
    fearSpot: at(420, 2.85),
    cageSpot: at(150, 3.1),
    ceoSpot: at(640, 2.6),
    voidEdge: [1080, 1600, 0.9],
  };
}

/**
 * Which emotion works which console station, and where that station is in each view. Station i is the
 * i-th from the LEFT in the 'back' view (the operators' own left to right) and its button colour matches
 * the emotion. The 'front' view looks the other way, so the order is mirrored there:
 * front consoleSlot1..4 = CALM, ANGER, SADNESS, JOY.  buttons = consolePress indices of that station.
 */
export const HQ_STATIONS = {
  JOY: { station: 0, front: 'consoleSlot4', back: 'consoleBack1', buttons: [0, 1, 2, 3] },
  SADNESS: { station: 1, front: 'consoleSlot3', back: 'consoleBack2', buttons: [4, 5, 6, 7] },
  ANGER: { station: 2, front: 'consoleSlot2', back: 'consoleBack3', buttons: [8, 9, 10, 11] },
  CALM: { station: 3, front: 'consoleSlot1', back: 'consoleBack4', buttons: [12, 13, 14, 15] },
};
{
  const A = ALARM_CLOSE;
  const fs = 1.8;
  HQ_VIEWS.alarm.anchors = {
    fearAtAlarm: [Math.round(A.x - ALARM_REACH[0] * fs), Math.round(A.y - ALARM_REACH[1] * fs), fs],
    handle: [A.x, A.y, fs],
    // CONSCIOUSNESS standing beside FEAR (a little nearer the camera; draw it after FEAR)
    ceoBeside: [238, 1475, +(hqScaleAt('alarm', 1475)).toFixed(3)],
    // CONSCIOUSNESS kneeling (kneel: 1, facing 1) in the foreground left: its raised knee stays clear of FEAR's
    // body and armR {preset:'onShoulder'} reaches FEAR's near shoulder at a gentle downward angle
    ceoKneel: [135, 1520, +(hqScaleAt('alarm', 1520)).toFixed(3)],
    bell: [A.x, Math.round(A.y - 250 * A.s), 0],
    beacon: [A.x, Math.round(A.y - 352 * A.s), 0],
  };
}
{
  HQ_VIEWS.backOfMind.anchors = {
    void: [700, 1600, 0.9],
    cage: [270, 1630, +hqScaleAt('backOfMind', 1630).toFixed(3)],
    fearInCage: [270, 1622, +hqScaleAt('backOfMind', 1622).toFixed(3)],
    fearOutside: [468, 1668, +hqScaleAt('backOfMind', 1668).toFixed(3)],
    ceo: [105, 1735, +hqScaleAt('backOfMind', 1735).toFixed(3)],
    distantLight: [380, 1032, 0],
  };
}

// ---------------------------------------------------------------- state
/** Ready-made state bundles: drawHQ(g, view, { ...HQ_PRESETS.alarm, t }) */
export const HQ_PRESETS = {
  calm: { alarm: 0, alarmPulled: 0, lightsDim: 0, screenMode: 'room', consoleGlow: 1, mist: 0.35, voidShadow: 0, doorOpen: 0 },
  alarm: { alarm: 1, alarmPulled: 1, lightsDim: 0.15, screenMode: 'alarm', consoleGlow: 0.8, mist: 0.35 },
  chaos: { alarm: 1, alarmPulled: 1, lightsDim: 0.3, screenMode: 'alarm', consoleGlow: 0.6, mist: 0.5, doorOpen: 1 },
  shadow: { alarm: 0, voidShadow: 1, lightsDim: 0.35, mist: 0.6, consoleGlow: 0.7, screenMode: 'room' },
  dawn: { alarm: 0, voidShadow: 0, lightsDim: 0, mist: 0.25, consoleGlow: 1.15, screenMode: 'calm' },
};
function norm(s = {}) {
  return {
    t: s.t || 0,
    alarm: clamp(s.alarm || 0),
    alarmPulled: clamp(s.alarmPulled || 0),
    lightsDim: clamp(s.lightsDim || 0),
    screenMode: s.screenMode || 'room',
    screenModeB: s.screenModeB || null,
    screenBlend: clamp(s.screenBlend || 0),
    consoleGlow: s.consoleGlow == null ? 1 : clamp(s.consoleGlow, 0, 1.5),
    consolePress: s.consolePress || {},
    voidShadow: clamp(s.voidShadow || 0),
    mist: s.mist == null ? 0.35 : clamp(s.mist),
    doorOpen: clamp(s.doorOpen || 0),
  };
}

// ---------------------------------------------------------------- caching
// LRU of offscreen canvases (bounded so animated sizes can't grow memory without limit)
const CACHE = new Map();
const CACHE_MAX_ENTRIES = 64, CACHE_MAX_PX = 90e6;
let cachePx = 0;
function resLevel(g) {
  const m = g.getTransform();
  const s = Math.sqrt(Math.abs(m.a * m.d - m.b * m.c));
  return s <= 0.82 ? 0.8 : s <= 1.06 ? 1 : s <= 1.56 ? 1.5 : 2;
}
function layer(key, x0, y0, w, h, res, paint) {
  const k = `${key}@${res}`;
  let c = CACHE.get(k);
  if (c) { CACHE.delete(k); CACHE.set(k, c); return c; }
  c = createCanvas(Math.max(1, Math.ceil(w * res)), Math.max(1, Math.ceil(h * res)));
  const cg = c.getContext('2d');
  cg.scale(res, res);
  cg.translate(-x0, -y0);
  paint(cg);
  CACHE.set(k, c);
  cachePx += c.width * c.height;
  while (CACHE.size > CACHE_MAX_ENTRIES || cachePx > CACHE_MAX_PX) {
    const [k0, c0] = CACHE.entries().next().value;
    if (k0 === k) break;
    CACHE.delete(k0);
    cachePx -= c0.width * c0.height;
  }
  return c;
}
/** draw a cached static layer covering world rect (x0,y0,w,h) */
function blit(g, key, x0, y0, w, h, paint, res = resLevel(g)) {
  const c = layer(key, x0, y0, w, h, res, paint);
  g.drawImage(c, x0, y0, c.width / res, c.height / res);
}

// ---------------------------------------------------------------- small helpers
// @napi-rs/canvas's restore() does not bring back fillStyle/strokeStyle, so public entry points restore them.
function keepStyles(g) {
  const f = g.fillStyle, s = g.strokeStyle;
  return () => { g.fillStyle = f; g.strokeStyle = s; };
}
function poly(g, pts) {
  g.beginPath();
  g.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
  g.closePath();
}
function softEllipse(g, x, y, rx, ry, color, a, mid = 0.45) {
  if (a <= 0.002) return;
  g.save();
  g.translate(x, y);
  g.scale(1, ry / rx);
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, rx);
  gr.addColorStop(0, rgba(color, a));
  gr.addColorStop(0.5, rgba(color, a * mid));
  gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr;
  g.fillRect(-rx, -rx, rx * 2, rx * 2);
  g.restore();
}
function linGrad(g, x0, y0, x1, y1, stops) {
  const gr = g.createLinearGradient(x0, y0, x1, y1);
  for (const [k, c] of stops) gr.addColorStop(k, c);
  return gr;
}
/** cross-section arch outline (floor-left -> up -> semicircle -> down -> floor-right) */
function archPath(g, P, lam, hw, spring, move = true) {
  const [cx, cy] = P(0, spring, lam);
  const [lx, ly] = P(-hw, 0, lam);
  if (move) g.moveTo(lx, ly); else g.lineTo(lx, ly);
  g.lineTo(lx, cy);
  g.arc(cx, cy, hw * lam, Math.PI, 0);
  g.lineTo(cx + hw * lam, ly);
}
function rib(g, P, lam, hw, spring, wpx, opt = {}) {
  const lw = wpx * lam;
  g.save();
  g.lineJoin = 'round';
  g.lineCap = 'butt';
  g.beginPath(); archPath(g, P, lam, hw + wpx * 0.12, spring);
  g.strokeStyle = rgba('#0a0816', 0.55); g.lineWidth = lw * 1.5; g.stroke();
  g.beginPath(); archPath(g, P, lam, hw, spring);
  g.strokeStyle = opt.body || '#3a3170'; g.lineWidth = lw; g.stroke();
  g.beginPath(); archPath(g, P, lam, hw - wpx * 0.28, spring);
  g.strokeStyle = opt.hi || 'rgba(170,150,240,0.33)'; g.lineWidth = Math.max(1, lw * 0.16); g.stroke();
  g.beginPath(); archPath(g, P, lam, hw + wpx * 0.36, spring);
  g.strokeStyle = 'rgba(8,6,18,0.5)'; g.lineWidth = Math.max(1, lw * 0.14); g.stroke();
  // plinths
  for (const s of [-1, 1]) {
    const [px, py] = P(s * hw, 0, lam);
    g.fillStyle = '#2c2558';
    roundRect(g, px - lw * 0.8, py - lw * 1.6, lw * 1.6, lw * 1.6, lw * 0.3); g.fill();
    g.fillStyle = 'rgba(170,150,240,0.18)';
    g.fillRect(px - lw * 0.8, py - lw * 1.6, lw * 1.6, Math.max(1, lw * 0.14));
  }
  g.restore();
}
function pendantLamp(g, x, y, r, cordTop, warm = 1) {
  g.save();
  glow(g, x, y + r * 2, r * 9, C.lampDeep, 0.16 * warm);
  glow(g, x, y, r * 3.2, C.lamp, 0.42 * warm);
  g.strokeStyle = '#100c1e'; g.lineWidth = Math.max(1.2, r * 0.09);
  g.beginPath(); g.moveTo(x, cordTop); g.lineTo(x, y - r * 1.1); g.stroke();
  // cap
  g.fillStyle = '#231c3d';
  g.beginPath();
  g.moveTo(x - r * 0.55, y - r * 0.72);
  g.quadraticCurveTo(x, y - r * 1.45, x + r * 0.55, y - r * 0.72);
  g.closePath(); g.fill();
  const gr = g.createRadialGradient(x - r * 0.3, y - r * 0.35, r * 0.05, x, y, r);
  gr.addColorStop(0, '#fffaf0'); gr.addColorStop(0.45, '#ffe6b4'); gr.addColorStop(1, '#ffb862');
  g.fillStyle = gr; circle(g, x, y, r); g.fill();
  g.restore();
}
function sconce(g, x, y, s) {
  // warm up/down wash then the lamp
  g.save();
  g.globalCompositeOperation = 'lighter';
  softEllipse(g, x, y - 46 * s, 40 * s, 95 * s, '#ffb35c', 0.13);
  softEllipse(g, x, y + 40 * s, 34 * s, 70 * s, '#ffb35c', 0.08);
  glow(g, x, y, 60 * s, C.lamp, 0.25);
  g.globalCompositeOperation = 'source-over';
  g.fillStyle = '#2a2147'; g.strokeStyle = C.line; g.lineWidth = 2 * s;
  roundRect(g, x - 5 * s, y - 2 * s, 10 * s, 26 * s, 4 * s); g.fill();
  const gr = g.createRadialGradient(x, y - 8 * s, 1, x, y, 20 * s);
  gr.addColorStop(0, '#fff4da'); gr.addColorStop(1, '#ffb35c');
  g.fillStyle = gr;
  g.beginPath();
  g.moveTo(x - 17 * s, y);
  g.quadraticCurveTo(x, y - 30 * s, x + 17 * s, y);
  g.closePath(); g.fill();
  g.restore();
}

// ================================================================= SCREEN CONTENT
const SCREEN_MODES = ['room', 'calm', 'alarm'];

// The real-room notebook (drawNotebook, open, cover 'gold' palette) rendered flat once, then keystone-warped
// onto the desk of the screen's POV painting (strip warp with perspective-correct rows). The screen painting is
// itself cached per size bucket, so this runs once per bucket.
let nbSpread = null;
function notebookSpread() {
  if (nbSpread) return nbSpread;
  const S = 2.4, NW = 220, NH = 290;                       // props.mjs NB_W / NB_H
  const x0 = -NW - 8, y0 = -NH / 2 - 6, sw = 2 * NW + 16, sh = NH + 13;
  const c = createCanvas(Math.round(sw * S), Math.round(sh * S)), x = c.getContext('2d');
  x.scale(S, S); x.translate(-x0, -y0);
  drawNotebook(x, 0, 0, 1, { open: 1, flat: 0, shadow: false });
  nbSpread = c;
  return c;
}
function drawDeskNotebook(g, w, h) {
  const img = notebookSpread();
  const cx = w * 0.5, yt = h * 0.645, yb = h * 0.985;     // page block on the desk: far edge → near edge
  const hwt = w * 0.215, hwb = w * 0.275;                  // half widths (far edge narrower: perspective)
  const r = hwt / hwb;                                      // 1/z at the far edge (near edge = 1)
  g.save();
  g.translate(cx, (yt + yb) / 2); g.rotate(-0.022); g.translate(-cx, -(yt + yb) / 2);
  // soft contact shadow on the desk
  g.fillStyle = 'rgba(30,15,10,0.32)';
  poly(g, [[cx - hwt - w * 0.006, yt + h * 0.012], [cx + hwt + w * 0.014, yt + h * 0.012], [cx + hwb + w * 0.022, yb + h * 0.012], [cx - hwb + w * 0.004, yb + h * 0.012]]);
  g.fill();
  const N = 90, IW = img.width, IH = img.height;
  let vPrev = 0, yPrev = yt;
  for (let i = 1; i <= N; i++) {
    const sN = i / N;
    const v = sN / lerp(r, 1, sN);                         // perspective-correct texture row
    const y = lerp(yt, yb, sN), sm = (i - 0.5) / N, hw = lerp(hwt, hwb, sm);
    const sy = vPrev * IH, shh = Math.max(0.5, (v - vPrev) * IH);
    g.drawImage(img, 0, sy, IW, shh, cx - hw, yPrev, hw * 2, y - yPrev + 0.6); // +0.6: no seams between strips
    vPrev = v; yPrev = y;
  }
  // the lamp (right) warms the pages; the far edge falls a touch into shadow
  g.globalCompositeOperation = 'multiply';
  g.fillStyle = linGrad(g, cx - hwb, 0, cx + hwb, 0, [[0, '#d8c8c0'], [0.6, '#fff1dc'], [1, '#ffe2bc']]);
  poly(g, [[cx - hwt, yt], [cx + hwt, yt], [cx + hwb, yb], [cx - hwb, yb]]); g.fill();
  g.globalCompositeOperation = 'source-over';
  g.restore();
}

function paintRoomPOV(g, w, h, tint = 0) {
  // the narrator's desk at night, seen through their eyes
  g.fillStyle = linGrad(g, 0, 0, 0, h, [[0, '#262c52'], [0.5, '#363458'], [0.58, '#2f2b4a']]);
  g.fillRect(0, 0, w, h);
  // lamp light on the wall
  glow(g, w * 0.78, h * 0.42, w * 0.5, '#ffbb6e', 0.33);
  // window (upper left) with night
  const wx = w * 0.07, wy = h * 0.07, ww = w * 0.34, wh = h * 0.42;
  g.fillStyle = '#1b1830'; roundRect(g, wx - w * 0.015, wy - w * 0.015, ww + w * 0.03, wh + w * 0.03, w * 0.025); g.fill();
  g.save();
  roundRect(g, wx, wy, ww, wh, w * 0.018); g.clip();
  g.fillStyle = linGrad(g, 0, wy, 0, wy + wh, [[0, '#14204a'], [0.7, '#2c4b8a'], [1, '#4a6fb0']]);
  g.fillRect(wx, wy, ww, wh);
  glow(g, wx + ww * 0.68, wy + wh * 0.27, ww * 0.35, '#cfe3ff', 0.28);
  g.fillStyle = '#f2f4ff'; circle(g, wx + ww * 0.68, wy + wh * 0.27, ww * 0.075); g.fill();
  g.fillStyle = '#2c4b8a'; circle(g, wx + ww * 0.71, wy + wh * 0.25, ww * 0.065); g.fill();
  for (let i = 0; i < 9; i++) {
    g.fillStyle = `rgba(230,240,255,${0.35 + 0.5 * rand(i, 41)})`;
    circle(g, wx + ww * rand(i, 42), wy + wh * 0.6 * rand(i, 43), Math.max(0.8, w * 0.0035)); g.fill();
  }
  // rooftops
  g.fillStyle = '#121a36';
  g.beginPath(); g.moveTo(wx, wy + wh);
  const roofs = [[0, 0.8], [0.18, 0.72], [0.3, 0.78], [0.42, 0.66], [0.6, 0.74], [0.72, 0.7], [0.86, 0.79], [1, 0.75]];
  for (const [u, v] of roofs) g.lineTo(wx + ww * u, wy + wh * v);
  g.lineTo(wx + ww, wy + wh); g.closePath(); g.fill();
  g.fillStyle = '#ffd47a';
  for (const [u, v] of [[0.22, 0.86], [0.5, 0.82], [0.78, 0.88]]) { g.fillRect(wx + ww * u, wy + wh * v, ww * 0.03, wh * 0.035); }
  g.restore();
  g.strokeStyle = '#4a3b52'; g.lineWidth = w * 0.012;
  g.beginPath(); g.moveTo(wx + ww / 2, wy); g.lineTo(wx + ww / 2, wy + wh); g.moveTo(wx, wy + wh * 0.5); g.lineTo(wx + ww, wy + wh * 0.5); g.stroke();
  // curtain
  g.fillStyle = '#5b3f6e';
  g.beginPath(); g.moveTo(wx - w * 0.03, wy - w * 0.02); g.quadraticCurveTo(wx + ww * 0.12, wy + wh * 0.5, wx - w * 0.01, wy + wh + w * 0.03);
  g.lineTo(wx - w * 0.06, wy + wh + w * 0.03); g.lineTo(wx - w * 0.06, wy - w * 0.02); g.closePath(); g.fill();
  // desk
  const dy = h * 0.58;
  g.fillStyle = linGrad(g, 0, dy, 0, h, [[0, '#6a4434'], [0.5, '#7f5440'], [1, '#5a382c']]);
  g.beginPath(); g.moveTo(-2, dy + h * 0.02); g.lineTo(w + 2, dy - h * 0.01); g.lineTo(w + 2, h + 2); g.lineTo(-2, h + 2); g.closePath(); g.fill();
  g.fillStyle = 'rgba(255,220,170,0.12)'; g.fillRect(0, dy - h * 0.01, w, h * 0.012);
  // lamp pool on desk
  g.save(); g.globalCompositeOperation = 'lighter';
  softEllipse(g, w * 0.56, h * 0.8, w * 0.42, h * 0.2, '#ffb460', 0.38);
  g.restore();
  // lamp (right): base, arm, shade
  const bx = w * 0.84, by = h * 0.74;
  g.fillStyle = '#2a2230'; ellipse(g, bx, by, w * 0.07, h * 0.022); g.fill();
  g.strokeStyle = '#2a2230'; g.lineWidth = w * 0.012; g.lineCap = 'round';
  g.beginPath(); g.moveTo(bx, by); g.lineTo(bx + w * 0.02, h * 0.5); g.lineTo(w * 0.73, h * 0.36); g.stroke();
  g.fillStyle = '#3b2f3e';
  g.beginPath(); g.moveTo(w * 0.69, h * 0.3); g.lineTo(w * 0.79, h * 0.33); g.lineTo(w * 0.74, h * 0.45); g.lineTo(w * 0.6, h * 0.42); g.closePath(); g.fill();
  g.fillStyle = '#fff1c8'; ellipse(g, w * 0.67, h * 0.435, w * 0.055, h * 0.022, -0.2); g.fill();
  glow(g, w * 0.67, h * 0.44, w * 0.12, '#ffe2a0', 0.5);
  // mug
  g.fillStyle = '#c56b5a'; roundRect(g, w * 0.13, h * 0.66, w * 0.07, h * 0.1, w * 0.012); g.fill();
  g.strokeStyle = '#c56b5a'; g.lineWidth = w * 0.01; g.beginPath(); g.arc(w * 0.2, h * 0.71, w * 0.018, -1.2, 1.2); g.stroke();
  g.fillStyle = '#4a2a24'; ellipse(g, w * 0.165, h * 0.663, w * 0.033, h * 0.01); g.fill();
  // the open notebook — the SAME book the narrator reads in the real room (props.mjs drawNotebook: the
  // story page + the crayon drawing of Fear pulling the alarm and the dark hooded one), lying on the desk in
  // gentle perspective, so the screen literally shows what the narrator sees
  drawDeskNotebook(g, w, h);
  // pencil
  g.save(); g.translate(w * 0.79, h * 0.9); g.rotate(-0.5);
  g.fillStyle = '#f2c14e'; g.fillRect(-w * 0.07, -h * 0.008, w * 0.12, h * 0.016);
  g.fillStyle = '#f0d2a8'; g.beginPath(); g.moveTo(w * 0.05, -h * 0.008); g.lineTo(w * 0.07, 0); g.lineTo(w * 0.05, h * 0.008); g.fill();
  g.restore();
  // gentle "through the eyes" vignette
  const vg = g.createRadialGradient(w / 2, h * 0.55, Math.min(w, h) * 0.35, w / 2, h * 0.5, Math.max(w, h) * 0.75);
  vg.addColorStop(0, 'rgba(10,8,25,0)'); vg.addColorStop(1, 'rgba(10,8,25,0.55)');
  g.fillStyle = vg; g.fillRect(0, 0, w, h);
  if (tint) { g.fillStyle = `rgba(0,0,0,${tint})`; g.fillRect(0, 0, w, h); }
}

function paintSunrise(g, w, h) {
  g.fillStyle = linGrad(g, 0, 0, 0, h, [[0, '#5a6db8'], [0.38, '#a497d6'], [0.62, '#f3b5c4'], [0.78, '#ffd7a6'], [1, '#ffe7bf']]);
  g.fillRect(0, 0, w, h);
  glow(g, w * 0.6, h * 0.74, w * 0.6, '#fff0c8', 0.55);
  glow(g, w * 0.6, h * 0.74, w * 0.2, '#fffaf0', 0.8);
  g.fillStyle = '#fffbea'; circle(g, w * 0.6, h * 0.76, w * 0.075); g.fill();
  // hills
  const hill = (y0, amp, col, ph) => {
    g.fillStyle = col; g.beginPath(); g.moveTo(0, h);
    for (let i = 0; i <= 24; i++) { const u = i / 24; g.lineTo(u * w, h * y0 - Math.sin(u * 3.2 + ph) * h * amp - Math.sin(u * 7.1 + ph * 2) * h * amp * 0.25); }
    g.lineTo(w, h); g.closePath(); g.fill();
  };
  hill(0.8, 0.05, '#c99bb8', 0.4);
  hill(0.86, 0.045, '#9b7fae', 2.1);
  hill(0.93, 0.04, '#76669c', 4.0);
}
function paintSunriseClouds(g, w, h, t) {
  const cl = [[0.18, 0.22, 0.16], [0.55, 0.15, 0.2], [0.85, 0.3, 0.13], [0.35, 0.42, 0.12], [1.15, 0.36, 0.15]];
  for (let i = 0; i < cl.length; i++) {
    const [u, v, s] = cl[i];
    const x = (((u + t * 0.006 * (1 + i * 0.2)) % 1.3) - 0.15) * w, y = v * h, r = s * w;
    softEllipse(g, x, y, r, r * 0.32, '#fff4f4', 0.5, 0.6);
    softEllipse(g, x + r * 0.3, y - r * 0.08, r * 0.6, r * 0.25, '#ffffff', 0.4, 0.6);
  }
}

function paintAlarmScreen(g, w, h) {
  paintRoomPOV(g, w, h, 0.25);
  g.save();
  g.globalCompositeOperation = 'multiply';
  g.fillStyle = '#ff6a72'; g.fillRect(0, 0, w, h);
  g.globalCompositeOperation = 'source-over';
  const vg = g.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.2, w / 2, h / 2, Math.max(w, h) * 0.7);
  vg.addColorStop(0, 'rgba(120,10,30,0.1)'); vg.addColorStop(1, 'rgba(90,0,20,0.6)');
  g.fillStyle = vg; g.fillRect(0, 0, w, h);
  g.restore();
}
function warningIcon(g, x, y, r, a) {
  g.save();
  g.globalAlpha = a;
  g.lineJoin = 'round';
  g.beginPath();
  g.moveTo(x, y - r); g.lineTo(x + r * 1.05, y + r * 0.78); g.lineTo(x - r * 1.05, y + r * 0.78); g.closePath();
  g.fillStyle = 'rgba(255,214,220,0.92)'; g.strokeStyle = 'rgba(255,240,242,0.95)'; g.lineWidth = r * 0.16;
  g.stroke(); g.fill();
  g.fillStyle = '#c92a3f';
  roundRect(g, x - r * 0.09, y - r * 0.42, r * 0.18, r * 0.72, r * 0.08); g.fill();
  circle(g, x, y + r * 0.52, r * 0.1); g.fill();
  g.restore();
}

/**
 * Draw what the screen of consciousness shows into the rect (x, y, w, h). Clipped to a rounded rect.
 * mode: 'room' (night desk with lamp + notebook, POV) | 'calm' (soft sunrise) | 'alarm' (red warning)
 */
function _drawScreenContent(g, x, y, w, h, t = 0, mode = 'room', radius = Math.min(w, h) * 0.05) {
  if (!SCREEN_MODES.includes(mode)) mode = 'room';
  // cache at a canonical size (aspect bucket x pixel-size bucket) so animated rects reuse it
  const m = g.getTransform();
  const dev = Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) * w;
  const bw = [240, 360, 540, 800, 1200, 1800].find((b) => b >= dev * 0.95) || 1800;
  const aspect = Math.round((h / w) * 40) / 40;
  const cw = bw, ch = Math.round(bw * aspect);
  const painter = mode === 'calm' ? paintSunrise : mode === 'alarm' ? paintAlarmScreen : paintRoomPOV;
  const c = layer(`screen:${mode}:${cw}x${ch}`, 0, 0, cw, ch, 1, (cg) => painter(cg, cw, ch));
  g.save();
  roundRect(g, x, y, w, h, radius);
  g.clip();
  g.drawImage(c, x, y, w, h);
  g.translate(x, y);
  if (mode === 'room') {
    // lamp breathes very gently
    const k = 0.5 + 0.5 * Math.sin(t * 0.9);
    g.globalCompositeOperation = 'lighter';
    softEllipse(g, w * 0.56, h * 0.8, w * 0.35, h * 0.16, '#ffb460', 0.05 + 0.04 * k);
  } else if (mode === 'calm') {
    paintSunriseClouds(g, w, h, t);
    g.globalCompositeOperation = 'lighter';
    glow(g, w * 0.6, h * 0.75, w * 0.3, '#ffe9c0', 0.12 + 0.05 * Math.sin(t * 0.7));
  } else if (mode === 'alarm') {
    const p = 0.5 + 0.5 * Math.sin(t * TAU * 1.2);
    g.globalCompositeOperation = 'lighter';
    glow(g, w / 2, h * 0.47, Math.min(w, h) * 0.55, '#ff4d5e', 0.12 + 0.12 * p);
    g.globalCompositeOperation = 'source-over';
    warningIcon(g, w / 2, h * 0.47, Math.min(w, h) * (0.16 + 0.012 * p), 0.75 + 0.2 * p);
  }
  g.restore();
}
const SCREEN_LIGHT = { room: '#ffcf96', calm: '#ffd9c0', alarm: '#ff5a66' };
function screenLightColor(st) {
  const a = SCREEN_LIGHT[st.screenMode] || SCREEN_LIGHT.room;
  if (st.screenModeB && st.screenBlend > 0) return mixColor(a, SCREEN_LIGHT[st.screenModeB] || a, st.screenBlend);
  return a;
}
function drawScreenBlend(g, x, y, w, h, st, r) {
  drawScreenContent(g, x, y, w, h, st.t, st.screenMode, r);
  if (st.screenModeB && st.screenBlend > 0.001) {
    g.save(); g.globalAlpha = st.screenBlend;
    drawScreenContent(g, x, y, w, h, st.t, st.screenModeB, r);
    g.restore();
  }
}

// ================================================================= CONSOLE
// Geometry (local, origin = centre of the base on the floor, units * scale):
//   front face up to the front lip at y = -CON.H1; slanted control deck from the lip back to y = -H1-D;
//   a low ridge with indicator lights behind the deck (top at -H1-D-R).
// Buttons: 16, four per station (station i = 0..3, left to right as seen from behind the operators):
//   4i = big amber button, 4i+1 = station-colour button, 4i+2 = amber button, 4i+3 = peach button.
const CON = { H1: 140, D: 64, R: 26 };
const STATION_COL = ['#ffc94a', '#6fa8e8', '#f0634f', '#7fd6b0'];
function consoleButtons(w) {
  const out = [], sw = w / 4;
  for (let i = 0; i < 4; i++) {
    const cx = (-0.375 + i * 0.25) * w;
    out.push({ i: 4 * i, u: cx - 0.17 * sw, v: 0.56, r: 19, col: C.amber, big: true });
    out.push({ i: 4 * i + 1, u: cx + 0.05 * sw, v: 0.3, r: 8.5, col: STATION_COL[i] });
    out.push({ i: 4 * i + 2, u: cx + 0.17 * sw, v: 0.3, r: 8.5, col: C.amber });
    out.push({ i: 4 * i + 3, u: cx + 0.11 * sw, v: 0.72, r: 8.5, col: '#ff9f6b' });
  }
  return out;
}
const deckPt = (u, v, s, dk = 1) => [u * lerp(0.93, 1, v), -CON.H1 * s - CON.D * dk * s * (1 - v)];
/** world position of a console button (controls side) for a console drawn with drawConsole(g, x, y, w, scale) */
export function consoleButtonPos(x, y, w, scale, index, deck = 1) {
  const b = consoleButtons(w).find((q) => q.i === index) || consoleButtons(w)[0];
  const [bx, by] = deckPt(b.u, b.v, scale, deck);
  return [x + bx, y + by];
}

function paintConsoleControls(g, w, s, dk = 1) {
  const H1 = CON.H1 * s, D = CON.D * dk * s, R = CON.R * s, lip = 13 * s;
  const hw = w / 2, bw = hw * 0.93, sw = w / 4;
  g.lineJoin = 'round';
  softEllipse(g, 0, 0, hw * 1.08, 30 * s, '#000000', 0.5);
  // raised ridge at the back of the deck
  g.fillStyle = linGrad(g, 0, -H1 - D - R, 0, -H1 - D, [[0, '#55479a'], [0.3, '#3a3070'], [1, '#2a2352']]);
  g.strokeStyle = C.line; g.lineWidth = 3 * s;
  roundRect(g, -bw - 6 * s, -H1 - D - R, bw * 2 + 12 * s, R + 8 * s, [12 * s, 12 * s, 2 * s, 2 * s]); g.fill(); g.stroke();
  g.fillStyle = 'rgba(200,180,255,0.22)'; roundRect(g, -bw + 6 * s, -H1 - D - R + 3 * s, bw * 2 - 12 * s, 2.5 * s, 1.2 * s); g.fill();
  // ridge light wells
  for (let i = 0; i < 4; i++) {
    const cx = (-0.375 + i * 0.25) * w;
    g.fillStyle = 'rgba(8,6,20,0.65)';
    roundRect(g, cx - sw * 0.36, -H1 - D - R * 0.62, sw * 0.72, R * 0.42, R * 0.2); g.fill();
  }
  // front face
  g.fillStyle = linGrad(g, 0, -H1, 0, 0, [[0, '#43387c'], [0.22, '#342b64'], [1, '#1a1634']]);
  g.strokeStyle = C.line; g.lineWidth = 3 * s;
  g.beginPath();
  g.moveTo(-hw, -H1);
  g.lineTo(hw, -H1);
  g.quadraticCurveTo(hw + 8 * s, -H1 * 0.5, hw - 22 * s, 0);
  g.lineTo(-hw + 22 * s, 0);
  g.quadraticCurveTo(-hw - 8 * s, -H1 * 0.5, -hw, -H1);
  g.closePath(); g.fill(); g.stroke();
  for (let i = 0; i < 4; i++) {
    const cx = (-0.375 + i * 0.25) * w;
    roundRect(g, cx - sw * 0.4, -H1 + 26 * s, sw * 0.8, H1 - 46 * s, 16 * s);
    g.fillStyle = 'rgba(10,8,26,0.25)'; g.fill();
    g.strokeStyle = 'rgba(170,150,240,0.14)'; g.lineWidth = 1.6 * s; g.stroke();
  }
  // deck
  g.fillStyle = linGrad(g, 0, -H1 - D, 0, -H1, [[0, '#3a3172'], [0.5, '#2e2760'], [1, '#3d3374']]);
  g.strokeStyle = C.line; g.lineWidth = 3 * s;
  g.beginPath();
  g.moveTo(-bw, -H1 - D); g.lineTo(bw, -H1 - D); g.lineTo(hw + 4 * s, -H1); g.lineTo(-hw - 4 * s, -H1);
  g.closePath(); g.fill(); g.stroke();
  // station plates on the deck
  for (let i = 0; i < 4; i++) {
    const cx = (-0.375 + i * 0.25) * w;
    const [ax, ay] = deckPt(cx - sw * 0.44, 0.1, s, dk), [bx2] = deckPt(cx + sw * 0.44, 0.1, s, dk);
    const [cx2, cy2] = deckPt(cx + sw * 0.44, 0.92, s, dk), [dx] = deckPt(cx - sw * 0.44, 0.92, s, dk);
    poly(g, [[ax, ay], [bx2, ay], [cx2, cy2], [dx, cy2]]);
    g.fillStyle = 'rgba(14,10,32,0.35)'; g.fill();
    g.strokeStyle = 'rgba(170,150,240,0.16)'; g.lineWidth = 1.4 * s; g.stroke();
  }
  // front lip rail
  g.fillStyle = linGrad(g, 0, -H1 - lip * 0.5, 0, -H1 + lip, [[0, '#7a68c0'], [1, '#2e2658']]);
  roundRect(g, -hw - 8 * s, -H1 - lip * 0.5, w + 16 * s, lip * 1.4, lip * 0.7); g.fill();
  g.strokeStyle = C.line; g.lineWidth = 2.4 * s; g.stroke();
  // button wells
  for (const b of consoleButtons(w)) {
    const [bx, by] = deckPt(b.u, b.v, s, dk);
    g.fillStyle = 'rgba(8,6,20,0.7)';
    ellipse(g, bx, by + 2 * s, (b.r + 4.5) * s, (b.r + 4.5) * s * 0.52); g.fill();
  }
  // per station: a lever in a slot + a little gauge
  for (let i = 0; i < 4; i++) {
    const cx = (-0.375 + i * 0.25) * w;
    const [l0x, l0y] = deckPt(cx + sw * 0.33, 0.2, s, dk), [l1x, l1y] = deckPt(cx + sw * 0.33, 0.85, s, dk);
    g.strokeStyle = 'rgba(8,6,20,0.75)'; g.lineWidth = 7 * s; g.lineCap = 'round';
    g.beginPath(); g.moveTo(l0x, l0y); g.lineTo(l1x, l1y); g.stroke();
    const kv = [0.35, 0.6, 0.45, 0.3][i];
    const [kx, ky] = deckPt(cx + sw * 0.33, kv, s, dk);
    g.strokeStyle = '#9d94c8'; g.lineWidth = 3.4 * s;
    g.beginPath(); g.moveTo(kx, ky); g.lineTo(kx + 2 * s, ky - 22 * s); g.stroke();
    g.fillStyle = i % 2 ? '#e8c25a' : '#ff8a6b'; circle(g, kx + 2 * s, ky - 24 * s, 6.5 * s); g.fill();
    g.strokeStyle = C.line; g.lineWidth = 1.8 * s; g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.5)'; circle(g, kx, ky - 26 * s, 2 * s); g.fill();
    // gauge
    const [gx, gy] = deckPt(cx - sw * 0.38, 0.45, s, dk);
    g.fillStyle = '#efe6d2'; ellipse(g, gx, gy, 12 * s, 7.5 * s); g.fill();
    g.strokeStyle = C.line; g.lineWidth = 2 * s; g.stroke();
    g.strokeStyle = '#c92a3f'; g.lineWidth = 1.6 * s;
    g.beginPath(); g.moveTo(gx, gy + 3 * s); g.lineTo(gx + (i - 1.5) * 3.5 * s, gy - 5 * s); g.stroke();
  }
}

/** outline path of the console hull seen from the screen side (origin = base centre) */
function consoleBackHull(g, w, s) {
  const H = 210 * s, hw = w / 2;
  g.beginPath();
  g.moveTo(-hw, 0);
  g.lineTo(-hw, -H + 50 * s);
  g.quadraticCurveTo(-hw, -H - 4 * s, -hw + 60 * s, -H - 4 * s);
  g.quadraticCurveTo(0, -H - 22 * s, hw - 60 * s, -H - 4 * s);
  g.quadraticCurveTo(hw, -H - 4 * s, hw, -H + 50 * s);
  g.lineTo(hw, 0);
  g.closePath();
}
function paintConsoleBack(g, w, s) {
  // seen from the screen side: rounded padded hull, warm rim from the buttons beyond. origin = base centre
  const H = 210 * s, hw = w / 2;
  const hull = () => consoleBackHull(g, w, s);
  hull();
  g.fillStyle = linGrad(g, 0, -H - 20 * s, 0, 0, [[0, '#4a3e86'], [0.12, '#3a3172'], [0.4, '#28224e'], [1, '#110e22']]);
  g.fill();
  g.save();
  hull(); g.clip();
  // machine panels: rounded inset plates with vent slots, seams between them
  const np = 7, pw = w / np;
  for (let i = 0; i < np; i++) {
    const x0 = -hw + i * pw;
    const top = -H + 58 * s + Math.pow((x0 + pw / 2) / hw, 2) * 10 * s;
    roundRect(g, x0 + 10 * s, top, pw - 20 * s, H, 16 * s);
    g.fillStyle = linGrad(g, 0, top, 0, top + 120 * s, [[0, 'rgba(150,130,230,0.09)'], [1, 'rgba(8,6,20,0.15)']]);
    g.fill();
    g.strokeStyle = 'rgba(8,6,20,0.55)'; g.lineWidth = 2.4 * s; g.stroke();
    g.strokeStyle = 'rgba(170,150,240,0.14)'; g.lineWidth = 1.2 * s;
    g.beginPath(); g.moveTo(x0 + 22 * s, top + 1.5 * s); g.lineTo(x0 + pw - 22 * s, top + 1.5 * s); g.stroke();
    if (i % 2 === 0) {
      g.fillStyle = 'rgba(8,6,20,0.5)';
      for (let k = 0; k < 3; k++) { roundRect(g, x0 + pw * 0.28, top + (24 + k * 11) * s, pw * 0.44, 4.5 * s, 2.2 * s); g.fill(); }
    } else {
      g.fillStyle = 'rgba(8,6,20,0.45)';
      roundRect(g, x0 + pw * 0.3, top + 22 * s, pw * 0.4, 30 * s, 6 * s); g.fill();
      g.fillStyle = 'rgba(255,190,110,0.55)';
      circle(g, x0 + pw * 0.5, top + 37 * s, 3.2 * s); g.fill();
    }
  }
  // band under the rim
  g.fillStyle = 'rgba(8,6,20,0.45)';
  g.beginPath(); g.moveTo(-hw, -H + 34 * s); g.quadraticCurveTo(0, -H + 18 * s, hw, -H + 34 * s); g.lineTo(hw, -H + 44 * s); g.quadraticCurveTo(0, -H + 28 * s, -hw, -H + 44 * s); g.closePath(); g.fill();
  // rim (warm light from the buttons beyond, catching the top edge)
  g.strokeStyle = 'rgba(255,207,122,0.6)'; g.lineWidth = 5 * s;
  g.beginPath(); g.moveTo(-hw, -H + 30 * s); g.quadraticCurveTo(-hw + 4 * s, -H + 2 * s, -hw + 60 * s, -H + 2 * s); g.quadraticCurveTo(0, -H - 16 * s, hw - 60 * s, -H + 2 * s); g.quadraticCurveTo(hw - 4 * s, -H + 2 * s, hw, -H + 30 * s); g.stroke();
  g.restore();
  hull(); g.strokeStyle = C.line; g.lineWidth = 3.4 * s; g.stroke();
  // small indicator lights along the band (emissive-looking, static)
  for (let i = 0; i < np; i++) {
    const x = -hw + (i + 0.5) * pw;
    const y = -H + 31 * s + Math.pow(x / hw, 2) * 8 * s - 8 * s;
    g.fillStyle = i % 3 === 1 ? '#ffb36b' : '#ffd98a';
    circle(g, x, y + 8 * s, 3.2 * s); g.fill();
  }
  // central emblem: a soft ring with a little heart
  const ey = -H + 82 * s, es = s * 0.6;
  g.fillStyle = '#231d46'; circle(g, 0, ey, 36 * es); g.fill();
  g.strokeStyle = 'rgba(255,207,122,0.35)'; g.lineWidth = 3 * es; circle(g, 0, ey, 36 * es); g.stroke();
  g.fillStyle = 'rgba(255,207,122,0.5)';
  g.save(); g.translate(0, ey); g.scale(es, es);
  g.beginPath(); g.moveTo(0, 9); g.bezierCurveTo(-16, -2, -8, -14, 0, -6); g.bezierCurveTo(8, -14, 16, -2, 0, 9); g.fill();
  g.restore();
}

/**
 * Draw the console. (x, y) = centre of its base on the floor; w = width (world px); scale = size of its
 * details (1 = matches characters drawn at scale 1: control deck front lip at 150*scale above the floor).
 * state.consoleSide: 'controls' (default — we look over the operators' shoulders at the buttons) or
 * 'back' (seen from the screen: plain back panel, warm light spilling over the top).
 * Uses state.t, consoleGlow, consolePress {index: 0..1}, lightsDim, alarm.
 */
function _drawConsole(g, x, y, w, scale = 1, state = {}) {
  const st = norm(state);
  const side = state.consoleSide || 'controls';
  const dk = state.consoleDeck || 1;
  const s = scale;
  g.save();
  g.translate(x, y);
  const pad = 40 * s;
  const H = (side === 'back' ? 240 : CON.H1 + CON.D * dk + CON.R + 10) * s;
  const key = `console:${side}:${Math.round(w)}:${s.toFixed(3)}:${dk}`;
  const x0 = -w / 2 - pad, y0 = -H - pad;
  // optional crop (internal): don't cache/draw below world y = _clipY
  const ch = state._clipY != null ? Math.max(1, Math.min(H + pad * 2, state._clipY - y - y0)) : H + pad * 2;
  const ckey = key + (state._clipY != null ? `:c${Math.round(ch)}` : '');
  const res = resLevel(g);
  const paint = (cg) => (side === 'back' ? paintConsoleBack(cg, w, s) : paintConsoleControls(cg, w, s, dk));
  blit(g, ckey, x0, y0, w + pad * 2, ch, paint, res);
  if (st.lightsDim > 0.002 && side === 'back') {
    // dimming the plain hull: just fill its outline (cheaper than a second full-size blit)
    g.fillStyle = `rgba(6,5,14,${st.lightsDim * 0.55})`;
    consoleBackHull(g, w, s);
    g.fill();
  } else if (st.lightsDim > 0.002) {
    // dimming = a cached dark silhouette of the same art laid over it (a per-frame filter costs ~4 ms)
    const a0 = g.globalAlpha;
    g.globalAlpha = a0 * st.lightsDim * 0.55;
    blit(g, ckey + ':sil', x0, y0, w + pad * 2, ch, (cg) => {
      paint(cg);
      cg.globalCompositeOperation = 'source-in';
      cg.fillStyle = '#06050e';
      cg.fillRect(x0, y0, w + pad * 2, ch);
    }, res);
    g.globalAlpha = a0;
  }
  const glowK = st.consoleGlow * (1 - st.lightsDim * 0.35);
  if (side === 'controls') {
    const H1 = CON.H1 * s, D = CON.D * dk * s, R = CON.R * s;
    // under-lip amber strip + warm haze over the deck
    g.save();
    g.globalCompositeOperation = 'lighter';
    softEllipse(g, 0, -H1 - D * 0.6, w * 0.55, 60 * s * dk, C.amber, 0.17 * glowK, 0.5);
    g.fillStyle = rgba(C.amber, 0.35 * glowK);
    roundRect(g, -w / 2 + 10 * s, -H1 + 9 * s, w - 20 * s, 3.5 * s, 2 * s); g.fill();
    g.restore();
    // ridge indicator lights: a slow gentle chase, with a soft warm halo along each station's light well
    g.save();
    g.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 4; i++) {
      const sw = w / 4;
      softEllipse(g, (-0.375 + i * 0.25) * w, -H1 - D - R * 0.41, sw * 0.42, 16 * s, C.amber, 0.16 * clamp(glowK), 0.5);
    }
    g.restore();
    for (let i = 0; i < 4; i++) {
      const cx = (-0.375 + i * 0.25) * w, sw = w / 4;
      for (let k = 0; k < 7; k++) {
        const lx = cx - sw * 0.3 + (k / 6) * sw * 0.6, ly = -H1 - D - R * 0.41;
        const on = 0.35 + 0.65 * Math.max(0, Math.sin(st.t * 1.4 - k * 0.7 - i * 1.3));
        const col = k % 3 === 0 ? STATION_COL[i] : C.amber;
        g.fillStyle = rgba(shade(col, 0.3), (0.45 + 0.55 * on) * clamp(glowK));
        circle(g, lx, ly, 3.2 * s); g.fill();
      }
    }
    for (const b of consoleButtons(w)) {
      const [bx, by] = deckPt(b.u, b.v, s, dk);
      const press = clamp(st.consolePress[b.i] || 0);
      const twinkle = 0.75 + 0.25 * Math.sin(st.t * (1.3 + (b.i % 5) * 0.37) + b.i * 1.7);
      const lit = glowK * (b.big ? 1 : twinkle) * (1 + press * 0.8);
      const r = b.r * s;
      const col = st.alarm > 0.5 && b.big ? mixColor(b.col, C.red, (st.alarm - 0.5) * 2 * 0.7) : b.col;
      g.save();
      g.globalCompositeOperation = 'lighter';
      glow(g, bx, by, r * ((b.big ? 3.4 : 4.2) + press * 1.6), col, (b.big ? 0.32 : 0.4) * lit);
      g.restore();
      const dy = press * r * 0.35;
      g.fillStyle = shade(col, -0.45);
      ellipse(g, bx, by + r * 0.28, r, r * 0.55); g.fill();
      const gr = g.createRadialGradient(bx - r * 0.3, by - r * 0.25 + dy, r * 0.1, bx, by + dy, r);
      gr.addColorStop(0, shade(col, 0.6 * clamp(lit, 0, 1)));
      gr.addColorStop(1, shade(col, -0.15 + 0.15 * clamp(lit, 0, 1)));
      g.fillStyle = gr;
      ellipse(g, bx, by + dy, r, r * 0.55); g.fill();
      g.strokeStyle = C.line; g.lineWidth = 1.6 * s; g.stroke();
      g.fillStyle = `rgba(255,255,255,${0.55 * clamp(lit, 0, 1)})`;
      ellipse(g, bx - r * 0.3, by - r * 0.18 + dy, r * 0.3, r * 0.14); g.fill();
    }
  } else {
    // warm spill over the top edge (buttons on the far side light the operators)
    const H0 = 210 * s;
    g.save();
    g.globalCompositeOperation = 'lighter';
    const fl = 0.9 + 0.1 * Math.sin(st.t * 0.9);
    softEllipse(g, 0, -H0 - 10 * s, w * 0.5, 40 * s, C.amber, 0.2 * glowK * fl, 0.6);
    for (let i = 0; i < 4; i++) {
      let press = 0;
      for (let k = 0; k < 4; k++) press = Math.max(press, clamp(st.consolePress[4 * i + k] || 0));
      // seen from the back, station 0 is on the right
      if (press > 0.01) softEllipse(g, (0.375 - i * 0.25) * w, -H0 - 10 * s, 110 * s, 34 * s, C.amber, 0.2 * glowK * press, 0.5);
    }
    g.fillStyle = rgba(C.amberHot, 0.5 * glowK);
    g.beginPath();
    g.moveTo(-w / 2 + 60 * s, -H0 - 4 * s);
    g.quadraticCurveTo(0, -H0 - 22 * s, w / 2 - 60 * s, -H0 - 4 * s);
    g.quadraticCurveTo(0, -H0 - 16 * s, -w / 2 + 60 * s, -H0 - 4 * s);
    g.fill();
    g.restore();
  }
  g.restore();
}

// ================================================================= ALARM STATION
/**
 * Pull station + conduit + bell + strobe beacon. (x, y) = rest centre of the handle; scale 1 = sized to
 * FEAR at scale 1 (box 84x148, bell r=42 at y-250, beacon dome at y-352). state: t, alarm, alarmPulled.
 * state.bell === false hides bell + beacon. Returns { handle:[x,y], bell:[x,y], beacon:[x,y] } in the
 * current coordinate space (before any transform you applied outside).
 */
function _drawAlarmStation(g, x, y, scale = 1, state = {}) {
  const st = norm(state);
  const s = scale, t = st.t, A = st.alarm;
  const pull = st.alarmPulled;
  g.save();
  g.translate(x, y);
  g.scale(s, s);
  g.lineJoin = 'round';
  const showBell = state.bell !== false;
  if (showBell) {
    // conduit
    g.strokeStyle = '#3a0f1c'; g.lineWidth = 13; g.lineCap = 'round';
    g.beginPath(); g.moveTo(0, -84); g.lineTo(0, -214); g.stroke();
    g.strokeStyle = '#b8323f'; g.lineWidth = 8;
    g.beginPath(); g.moveTo(0, -84); g.lineTo(0, -214); g.stroke();
    g.strokeStyle = 'rgba(255,170,170,0.5)'; g.lineWidth = 2;
    g.beginPath(); g.moveTo(-2, -88); g.lineTo(-2, -210); g.stroke();
    for (const cy of [-120, -180]) { g.fillStyle = '#5b5470'; roundRect(g, -9, cy - 4, 18, 8, 3); g.fill(); }
    // beacon stem (behind the bell)
    g.fillStyle = '#2a2236'; roundRect(g, -6, -330, 12, 50, 4); g.fill();
    // bell
    const vib = A > 0 ? A * 1.6 : 0;
    const bx = vib * Math.sin(t * TAU * 23), by = -250 + vib * 0.5 * Math.sin(t * TAU * 31 + 1);
    g.fillStyle = '#2a2236'; roundRect(g, -14, -232, 28, 24, 6); g.fill();
    g.save();
    g.translate(bx, by);
    g.fillStyle = '#4e1222'; circle(g, 0, 3, 44); g.fill();
    const gb = g.createRadialGradient(-14, -16, 4, 0, 0, 44);
    gb.addColorStop(0, '#ff9aa2'); gb.addColorStop(0.45, '#ef3b50'); gb.addColorStop(1, '#a51d33');
    g.fillStyle = gb; circle(g, 0, 0, 42); g.fill();
    g.strokeStyle = C.line; g.lineWidth = 3; g.stroke();
    g.strokeStyle = 'rgba(80,10,25,0.5)'; g.lineWidth = 3; circle(g, 0, 0, 30); g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.55)'; ellipse(g, -16, -20, 11, 6, -0.6); g.fill();
    const gk = g.createRadialGradient(-3, -3, 1, 0, 0, 10);
    gk.addColorStop(0, '#ffffff'); gk.addColorStop(1, '#9a96a8');
    g.fillStyle = gk; circle(g, 0, 0, 9); g.fill();
    g.strokeStyle = C.line; g.lineWidth = 2; g.stroke();
    g.restore();
    if (A > 0.01) {
      // ringing arcs
      for (const side of [-1, 1]) {
        for (let k = 0; k < 2; k++) {
          const ph = (t * 3.2 + k * 0.5) % 1;
          const r = 52 + ph * 26;
          g.strokeStyle = `rgba(255,214,220,${A * 0.7 * (1 - ph)})`;
          g.lineWidth = 3.5; g.lineCap = 'round';
          g.beginPath(); g.arc(0, -250, r, side > 0 ? -0.45 : Math.PI - 0.45, side > 0 ? 0.45 : Math.PI + 0.45); g.stroke();
        }
      }
    }
    // strobe beacon
    g.fillStyle = '#2a2236'; roundRect(g, -32, -340, 64, 16, 6); g.fill();
    g.strokeStyle = C.line; g.lineWidth = 2.5; g.stroke();
    const domeY = -340;
    g.save();
    g.beginPath(); g.ellipse(0, domeY, 26, 32, 0, Math.PI, 0); g.closePath();
    const on = A;
    const gd = g.createRadialGradient(-8, domeY - 18, 2, 0, domeY - 10, 32);
    gd.addColorStop(0, mixColor('#d1495a', '#ffe0e4', on * 0.8)); gd.addColorStop(1, mixColor('#7a1a2a', '#ff4d5e', on * 0.8));
    g.fillStyle = gd; g.fill();
    g.clip();
    if (on > 0.01) {
      const ph = t * TAU * 0.9;
      const cx = Math.cos(ph) * 18, front = 0.5 + 0.5 * Math.sin(ph);
      g.globalCompositeOperation = 'lighter';
      glow(g, cx, domeY - 12, 22, '#fff2f4', on * (0.4 + 0.6 * front));
      glow(g, -cx, domeY - 12, 14, '#ff8a96', on * 0.4 * (1 - front));
    }
    g.restore();
    g.beginPath(); g.ellipse(0, domeY, 26, 32, 0, Math.PI, 0); g.closePath();
    g.strokeStyle = C.line; g.lineWidth = 2.5; g.stroke();
    g.fillStyle = 'rgba(255,255,255,0.45)'; ellipse(g, -10, domeY - 20, 5, 8, -0.4); g.fill();
    // cage lines on the dome
    g.strokeStyle = 'rgba(30,20,40,0.55)'; g.lineWidth = 2;
    g.beginPath(); g.moveTo(0, domeY - 32); g.lineTo(0, domeY); g.moveTo(-24, domeY - 12); g.quadraticCurveTo(0, domeY - 18, 24, domeY - 12); g.stroke();
  }
  // box
  g.fillStyle = 'rgba(10,6,16,0.35)'; roundRect(g, -38, -80, 88, 152, 18); g.fill(); // drop shadow
  const gbx = g.createLinearGradient(-42, -84, 42, 64);
  gbx.addColorStop(0, '#ff6f7c'); gbx.addColorStop(0.5, '#e8384c'); gbx.addColorStop(1, '#b52438');
  g.fillStyle = gbx; roundRect(g, -42, -84, 84, 148, 16); g.fill();
  g.strokeStyle = '#4e1222'; g.lineWidth = 3.2; g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.28)'; roundRect(g, -35, -77, 9, 60, 4.5); g.fill();
  // label
  g.fillStyle = '#fff6f0'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = 'bold 23px Fraunces';
  g.fillText('FIRE', 6, -56);
  g.font = 'bold 9px Fraunces';
  g.fillText('PULL DOWN', 0, 50);
  // slot
  g.fillStyle = '#5a1424'; roundRect(g, -31, -18, 62, 58, 10); g.fill();
  g.fillStyle = 'rgba(0,0,0,0.25)'; roundRect(g, -31, -18, 62, 10, 6); g.fill();
  // arrow
  g.fillStyle = 'rgba(255,220,225,0.65)';
  g.beginPath(); g.moveTo(-6, 26 + pull * 6); g.lineTo(6, 26 + pull * 6); g.lineTo(0, 35 + pull * 6); g.closePath(); g.fill();
  // handle
  const hy = pull * 26;
  g.fillStyle = 'rgba(40,5,15,0.4)'; roundRect(g, -27, -8 + hy, 57, 22, 10); g.fill();
  const gh = g.createLinearGradient(0, -12 + hy, 0, 12 + hy);
  gh.addColorStop(0, '#ffffff'); gh.addColorStop(1, '#e6d6dc');
  g.fillStyle = gh; roundRect(g, -28, -11 + hy, 56, 22, 10); g.fill();
  g.strokeStyle = '#4e1222'; g.lineWidth = 2.6; g.stroke();
  g.fillStyle = 'rgba(200,60,80,0.5)'; roundRect(g, -16, -3 + hy, 32, 6, 3); g.fill();
  g.restore();
  return {
    handle: [x, y + pull * 26 * s],
    bell: [x, y - 250 * s],
    beacon: [x, y - 352 * s],
  };
}

// ================================================================= DOOR (exit)
// local units: world units on the wall plane, origin = bottom centre of the doorway
function drawExitDoor(g, open, t) {
  const W2 = 62, Hs = 150, R = 62; // half width, straight height, arch radius
  const doorPath = (pad = 0) => {
    g.beginPath();
    g.moveTo(-W2 - pad, 0);
    g.lineTo(-W2 - pad, -Hs);
    g.arc(0, -Hs, W2 + pad, Math.PI, 0);
    g.lineTo(W2 + pad, 0);
    g.closePath();
  };
  // frame
  doorPath(14);
  g.fillStyle = '#41377a'; g.fill();
  g.strokeStyle = C.line; g.lineWidth = 3; g.stroke();
  doorPath(14);
  g.save(); g.clip();
  g.strokeStyle = 'rgba(170,150,240,0.3)'; g.lineWidth = 3; doorPath(10); g.stroke();
  g.restore();
  // opening: outside light
  doorPath(0);
  g.save(); g.clip();
  g.fillStyle = linGrad(g, 0, -Hs - R, 0, 0, [[0, '#fff3d6'], [1, '#ffd9a0']]);
  g.fillRect(-W2 - 2, -Hs - R - 2, W2 * 2 + 4, Hs + R + 4);
  // door leaf hinged on the left, swinging away from us on its hinges: the free edge travels toward the hinge and
  // recedes (perspective: it gets shorter), and the leaf's thickness shows along that edge
  const ang = open * 1.35;
  const cA = Math.cos(ang), sA = Math.sin(ang);
  const lw = W2 * 2 * cA;
  const persp = 1 / (1 + sA * 0.22);            // the far (free) edge is further away → smaller
  if (lw > 0.5) {
    const sh = open * 0.5;
    // map leaf-local (x from -W2 at the hinge to +W2 at the free edge, y up negative) into the swung leaf
    const map = (x, y) => {
      const u = (x + W2) / (W2 * 2);            // 0 hinge … 1 free edge
      const k = lerp(1, persp, u);
      const yb = 0, ya = -Hs - R;               // floor line and top of the arch stay anchored at the hinge
      return [-W2 + u * lw, yb + (y - yb) * k + (1 - k) * (ya * 0.06)];
    };
    const leafPath = () => {
      g.beginPath();
      const N = 18;
      let p = map(-W2, 0); g.moveTo(p[0], p[1]);
      p = map(-W2, -Hs); g.lineTo(p[0], p[1]);
      for (let i = 0; i <= N; i++) {
        const a = Math.PI + (i / N) * Math.PI;
        p = map(Math.cos(a) * W2, -Hs + Math.sin(a) * W2); g.lineTo(p[0], p[1]);
      }
      p = map(W2, 0); g.lineTo(p[0], p[1]);
      g.closePath();
    };
    // the leaf's edge (thickness) catches the outside light along the free side
    const th = 7 * sA;
    if (th > 0.4) {
      const a0 = map(W2, 0), a1 = map(W2, -Hs);
      g.fillStyle = shade('#3a2a60', -sh * 0.6);
      g.beginPath(); g.moveTo(a0[0], a0[1]); g.lineTo(a1[0], a1[1]); g.lineTo(a1[0] + th, a1[1] - th * 0.15); g.lineTo(a0[0] + th, a0[1]); g.closePath();
      g.fill();
      g.strokeStyle = C.line; g.lineWidth = 2; g.stroke();
    }
    leafPath();
    g.fillStyle = linGrad(g, -W2, 0, -W2 + lw, 0, [[0, shade('#5a4290', -sh)], [1, shade('#463370', -sh * 1.2)]]);
    g.fill();
    g.strokeStyle = C.line; g.lineWidth = 2.5; g.stroke();
    // panels, porthole and knob, carried by the same swing
    g.save();
    leafPath(); g.clip();
    const seg = (pts) => { g.beginPath(); pts.forEach(([x, y], i) => { const q = map(x, y); if (i) g.lineTo(q[0], q[1]); else g.moveTo(q[0], q[1]); }); };
    g.strokeStyle = 'rgba(15,10,30,0.5)'; g.lineWidth = 2.5;
    seg([[0, -Hs - R + 4], [0, 0]]); g.stroke();
    for (const sx of [-1, 1]) {
      for (const [y0, h] of [[-Hs + 6, 70], [-64, 50]]) {
        const x0 = sx * 31 - 20, x1 = x0 + 40;
        seg([[x0, y0], [x1, y0], [x1, y0 + h], [x0, y0 + h]]); g.closePath(); g.stroke();
      }
    }
    // porthole
    const pc = map(0, -Hs - 12), pr = 18 * Math.max(0.15, cA);
    g.fillStyle = '#ffe6b0';
    g.beginPath(); g.ellipse(pc[0], pc[1], pr, 18 * lerp(1, persp, 0.5), 0, 0, TAU); g.fill();
    g.strokeStyle = '#2b2255'; g.lineWidth = 4; g.stroke();
    // knob on the free side
    const kc = map(W2 - 14, -80);
    g.fillStyle = '#e8c25a';
    g.beginPath(); g.ellipse(kc[0], kc[1], 6 * Math.max(0.3, cA), 6 * persp, 0, 0, TAU); g.fill();
    g.strokeStyle = C.line; g.lineWidth = 1.5; g.stroke();
    g.restore();
  }
  g.restore();
}
function exitSign(g, x, y, s, emis = 1) {
  // frontal EXIT sign; (x,y) centre
  g.save();
  g.globalCompositeOperation = 'lighter';
  glow(g, x, y, 90 * s, '#5dffaa', 0.2 * emis);
  softEllipse(g, x, y + 40 * s, 70 * s, 50 * s, '#5dffaa', 0.08 * emis);
  g.globalCompositeOperation = 'source-over';
  g.fillStyle = '#16301f'; roundRect(g, x - 34 * s, y - 14 * s, 68 * s, 28 * s, 8 * s); g.fill();
  g.strokeStyle = '#0c1a14'; g.lineWidth = 2.5 * s; g.stroke();
  g.fillStyle = mixColor('#3c8a63', '#b7ffd6', emis);
  g.font = `bold ${Math.round(17 * s)}px Fraunces`;
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('EXIT', x, y + 1 * s);
  g.restore();
}

// ================================================================= VOID SHADOW + MIST
// shadow shapes (screen space per view, at full spread), apex = where it grows from
const SHADOW = {
  front: {
    apex: [450, 835],
    pts: () => { const G = GEO.front, P = proj(G); return [P(-60, 0, 0.96), P(60, 0, 0.96), P(170, 0, 1.15), P(150, 0, 1.4), P(290, 0, 1.75), P(200, 0, 2.05), P(120, 0, 2.5), P(-20, 0, 2.2), P(-150, 0, 2.45), P(-230, 0, 1.95), P(-170, 0, 1.55), P(-280, 0, 1.3), P(-160, 0, 1.1)]; },
    clip: () => { const G = GEO.front, P = proj(G); return [P(-G.hw, 0, 0.9), P(G.hw, 0, 0.9), P(G.hw, 0, 4), P(-G.hw, 0, 4)]; },
  },
  back: {
    apex: [880, 1570],
    pts: () => [[900, 1330], [640, 1120], [330, 1040], [40, 1090], [-40, 1300], [120, 1600], [900, 1620]],
    clip: () => { const G = GEO.back, P = proj(G); return [P(-340, 0, 1.25), P(340, 0, 1.25), P(340, 0, 4), P(-340, 0, 4)]; },
  },
  alarm: {
    apex: [-60, 1460],
    pts: () => [[-60, 1250], [340, 1300], [700, 1380], [900, 1600], [-60, 1620]],
    clip: null,
  },
  backOfMind: {
    apex: [700, 1600],
    pts: () => [[460, 1420], [760, 1380], [1050, 1430], [1050, 1800], [200, 1800], [120, 1560]],
    clip: () => [[-20, 1060], [1020, 1060], [1020, 1800], [-20, 1800]],
  },
};
function drawVoidShadow(g, view, st) {
  const k = st.voidShadow;
  if (k <= 0.002) return;
  const G = GEO[view], S = SHADOW[view];
  const R = 0.5;
  if (!S.box) {
    const pts = S.pts();
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    x0 = Math.max(-100, Math.floor(x0 - 40)); y0 = Math.max(-100, Math.floor(y0 - 40));
    x1 = Math.min(G.W + 100, Math.ceil(x1 + 40)); y1 = Math.min(G.H + 100, Math.ceil(y1 + 40));
    S.box = [x0, y0, x1 - x0, y1 - y0];
  }
  const [bx0, by0, bw, bh] = S.box;
  const c = layer(`shadow:${view}`, bx0, by0, bw, bh, R, (cg) => {
    if (S.clip) { poly(cg, S.clip()); cg.clip(); }
    cg.filter = 'blur(9px)';
    const pts = S.pts();
    let far = pts[0], fd = 0;
    for (const p of pts) { const d = Math.hypot(p[0] - S.apex[0], p[1] - S.apex[1]); if (d > fd) { fd = d; far = p; } }
    const gr = cg.createRadialGradient(S.apex[0], S.apex[1], 0, S.apex[0], S.apex[1], fd);
    gr.addColorStop(0, 'rgba(2,1,7,0.95)'); gr.addColorStop(0.55, 'rgba(3,2,9,0.86)'); gr.addColorStop(1, 'rgba(4,3,12,0.62)');
    cg.fillStyle = gr;
    // rounded blob through the points
    const n = pts.length;
    cg.beginPath();
    const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    let m = mid(pts[n - 1], pts[0]);
    cg.moveTo(m[0], m[1]);
    for (let i = 0; i < n; i++) { const p = pts[i], q = pts[(i + 1) % n]; m = mid(p, q); cg.quadraticCurveTo(p[0], p[1], m[0], m[1]); }
    cg.closePath(); cg.fill();
    cg.filter = 'none';
  });
  const e = 1 - Math.pow(1 - k, 2);
  const sc = 0.18 + 0.82 * e;
  g.save();
  g.globalAlpha = clamp(k * 1.6);
  g.translate(S.apex[0], S.apex[1]);
  g.scale(sc, sc);
  g.translate(-S.apex[0], -S.apex[1]);
  g.drawImage(c, bx0, by0, c.width / R, c.height / R);
  g.restore();
}

const MIST = {
  front: [[450, 800, 300, 46, '#3b3274', 0.5], [330, 850, 220, 34, '#3b3274', 0.35], [600, 850, 240, 30, '#3b3274', 0.35], [450, 900, 420, 50, '#2c2558', 0.2]],
  back: [[200, 1480, 380, 70, '#2a2350', 0.4], [700, 1520, 420, 80, '#2a2350', 0.4], [450, 1380, 500, 60, '#2a2350', 0.2]],
  alarm: [[220, 1450, 400, 70, '#2c2558', 0.4], [700, 1520, 480, 80, '#2c2558', 0.3]],
  backOfMind: [[330, 1060, 520, 46, '#4a3d86', 0.38], [700, 1180, 520, 60, '#2e2660', 0.4], [200, 1300, 420, 70, '#2e2660', 0.35], [620, 1450, 600, 90, '#272052', 0.35]],
};
const MIST_FG = {
  front: [],
  back: [[300, 1600, 520, 90, '#1c1838', 0.5], [780, 1600, 420, 80, '#1c1838', 0.45]],
  alarm: [[300, 1600, 520, 80, '#231d44', 0.45], [780, 1600, 440, 80, '#231d44', 0.4]],
  backOfMind: [[250, 1740, 520, 90, '#2a2352', 0.5], [760, 1760, 560, 100, '#2a2352', 0.45], [500, 1690, 420, 50, '#3a3070', 0.25]],
};
function drawMist(g, list, st, salt = 0) {
  if (st.mist <= 0.002 || !list.length) return;
  g.save();
  for (let i = 0; i < list.length; i++) {
    const [x, y, rx, ry, col, a] = list[i];
    const dx = Math.sin(st.t * (0.07 + i * 0.013) + i * 2.3 + salt) * rx * 0.12;
    const breathe = 0.85 + 0.15 * Math.sin(st.t * (0.11 + i * 0.02) + i);
    softEllipse(g, x + dx, y, rx, ry, col, a * st.mist * breathe, 0.55);
  }
  g.restore();
}

// ================================================================= FRONT VIEW
function paintFront(g) {
  const G = GEO.front, P = proj(G), { W, H, hw, spring } = G;
  // vault / walls base
  let gr = g.createRadialGradient(G.vx, 470, 80, G.vx, 640, 1000);
  gr.addColorStop(0, '#3e3570'); gr.addColorStop(0.42, '#2d2756'); gr.addColorStop(1, '#17132c');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  // ceiling darker at the very top
  g.fillStyle = linGrad(g, 0, 0, 0, 260, [[0, 'rgba(10,8,22,0.6)'], [1, 'rgba(10,8,22,0)']]);
  g.fillRect(0, 0, W, 260);
  // side wall panels: dado band + darker lower wall
  for (const s of [-1, 1]) {
    poly(g, [P(s * hw, 0, 1), P(s * hw, 104, 1), P(s * hw, 104, 3.6), P(s * hw, 0, 3.6)]);
    g.fillStyle = 'rgba(12,9,26,0.28)'; g.fill();
    poly(g, [P(s * hw, 104, 1), P(s * hw, 114, 1), P(s * hw, 114, 3.6), P(s * hw, 104, 3.6)]);
    g.fillStyle = '#4a3f86'; g.fill();
    poly(g, [P(s * hw, 114, 1), P(s * hw, 117, 1), P(s * hw, 117, 3.6), P(s * hw, 114, 3.6)]);
    g.fillStyle = 'rgba(190,170,255,0.25)'; g.fill();
    poly(g, [P(s * hw, 0, 1), P(s * hw, 12, 1), P(s * hw, 12, 3.6), P(s * hw, 0, 3.6)]);
    g.fillStyle = '#1a1533'; g.fill();
  }

  // ---- the BACK OF THE MIND through the great arch
  g.save();
  g.beginPath(); archPath(g, P, 1, hw, spring); g.closePath(); g.clip();
  gr = g.createRadialGradient(450, 560, 10, 450, 560, 520);
  gr.addColorStop(0, '#2a2258'); gr.addColorStop(0.4, '#17132f'); gr.addColorStop(0.8, '#0d0b1c'); gr.addColorStop(1, '#09070f');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  // cavern floor
  const fy0 = P(0, 0, 0.3)[1], fy1 = P(0, 0, 1)[1];
  g.fillStyle = linGrad(g, 0, fy0, 0, fy1, [[0, '#1d183c'], [0.5, '#141029'], [1, '#100d22']]);
  g.fillRect(0, fy0, W, fy1 - fy0 + 4);
  // distant ribs of the cavern, fading into darkness
  // the cavern opens up beyond the arch: huge faint ribs, wider and taller than the room
  for (const [lam, a] of [[0.8, 0.55], [0.55, 0.32], [0.38, 0.16]]) {
    g.save();
    g.globalAlpha = a;
    g.beginPath(); archPath(g, P, lam, hw * 1.7, spring * 1.5);
    g.strokeStyle = '#08060f'; g.lineWidth = 30 * lam; g.stroke();
    g.beginPath(); archPath(g, P, lam, hw * 1.7 - 12, spring * 1.5);
    g.strokeStyle = rgba(C.violet, 0.4); g.lineWidth = 2.4 * lam; g.stroke();
    g.restore();
  }
  // a faint, impossibly far glow at the end of the cavern
  glow(g, 450, 556, 110, '#8a78e0', 0.14);
  // glow lines on the cavern floor continuing from the room
  g.lineCap = 'round';
  for (const X of [-195, -130, -65, 0, 65, 130, 195]) {
    const [x0, y0] = P(X, 0, 1), [x1, y1] = P(X, 0, 0.45);
    g.strokeStyle = linGrad(g, x0, y0, x1, y1, [[0, rgba('#8a7ae0', 0.14)], [1, rgba('#8a7ae0', 0)]]);
    g.lineWidth = 1.6;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
  }
  // haze that silhouettes the Void
  softEllipse(g, 450, 500, 210, 380, '#4a3b90', 0.42, 0.55);
  softEllipse(g, 450, 380, 120, 200, '#5a4aa6', 0.18, 0.5);
  softEllipse(g, 450, 800, 330, 70, '#3e3478', 0.5, 0.5);
  g.restore();

  // ---- floor of the room
  const fl = [P(-hw, 0, 1), P(hw, 0, 1), P(hw, 0, 3.6), P(-hw, 0, 3.6)];
  poly(g, fl);
  g.fillStyle = linGrad(g, 0, fl[0][1], 0, H, [[0, '#3c336e'], [0.2, '#30295e'], [0.55, '#272150'], [1, '#1d1839']]);
  g.fill();
  g.save();
  poly(g, fl); g.clip();
  // cool sheen at the threshold (cavern haze reflected), warm reflections under the lamps
  softEllipse(g, 450, 860, 320, 50, '#6a58c0', 0.35, 0.4);
  g.globalCompositeOperation = 'lighter';
  for (const s of [-1, 1]) {
    softEllipse(g, 450 + s * 250, 1010, 60, 200, '#ffb35c', 0.06, 0.5);
    softEllipse(g, 450 + s * 228, 875, 50, 60, '#ffb35c', 0.1, 0.5);
  }
  softEllipse(g, 450, 1420, 560, 240, '#ff9f43', 0.12, 0.5);
  g.globalCompositeOperation = 'source-over';
  // inlaid glow lines along depth
  for (const X of [-195, -130, -65, 0, 65, 130, 195]) {
    const [x0, y0] = P(X, 0, 1), [x1, y1] = P(X, 0, 3.6);
    g.strokeStyle = linGrad(g, x0, y0, x1, y1, [[0, rgba('#9a88f0', 0.22)], [0.5, rgba('#9a88f0', 0.12)], [1, rgba('#9a88f0', 0.05)]]);
    g.lineWidth = 2;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
  }
  for (const lam of [1.22, 1.52, 1.95, 2.6]) {
    const [x0, y0] = P(-hw, 0, lam), [x1] = P(hw, 0, lam);
    g.strokeStyle = rgba('#9a88f0', 0.07); g.lineWidth = 1.5 * lam;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y0); g.stroke();
  }
  // emblem ring on the floor
  for (const [R, a, lw] of [[118, 0.3, 2.6], [84, 0.18, 1.8], [30, 0.25, 1.6]]) {
    g.beginPath();
    for (let i = 0; i <= 64; i++) {
      const th = (i / 64) * TAU;
      const Z = G.f / 1.55 + R * Math.sin(th), X = R * Math.cos(th);
      const lam = G.f / Z;
      const [x, y] = P(X - 10, 0, lam);
      if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
    }
    g.strokeStyle = rgba('#c0b0ff', a); g.lineWidth = lw; g.stroke();
  }
  // contact shadow at the wall bases
  for (const s of [-1, 1]) {
    const [a0, b0] = P(s * hw, 0, 1), [a1, b1] = P(s * hw, 0, 3.6), [c1, d1] = P(s * (hw - 30), 0, 3.6), [c0, d0] = P(s * (hw - 30), 0, 1);
    g.fillStyle = linGrad(g, a1, b1, c1, d1, [[0, 'rgba(8,6,18,0.45)'], [1, 'rgba(8,6,18,0)']]);
    poly(g, [[a0, b0], [a1, b1], [c1, d1], [c0, d0]]); g.fill();
  }
  g.restore();

  // ---- ribs of the vault (arch rim + two nearer ribs)
  rib(g, P, 2.3, hw, spring, 20);
  rib(g, P, 1.55, hw, spring, 20);
  rib(g, P, 1, hw, spring, 24, { body: '#40367a', hi: 'rgba(200,180,255,0.4)' });
  // inner reveal of the great arch (thickness, in shadow)
  g.save();
  g.beginPath(); archPath(g, P, 1, hw - 13, spring);
  g.strokeStyle = 'rgba(12,9,26,0.6)'; g.lineWidth = 7; g.stroke();
  g.restore();
  // warm light catching the arch rim from the lamps
  g.save();
  g.globalCompositeOperation = 'lighter';
  for (const s of [-1, 1]) softEllipse(g, 450 + s * 228, 420, 60, 200, '#ffb35c', 0.1, 0.5);
  g.restore();

  // sconces flanking the arch
  for (const s of [-1, 1]) {
    const [x, y] = P(s * hw, 300, 1.12);
    sconce(g, x - s * 6, y, 0.9);
  }
  // pendant lamps
  for (const s of [-1, 1]) {
    const [x, y] = P(s * 158, 540, 1.62);
    pendantLamp(g, x, y, 26, 0, 1);
  }
  // pendant lamp light pools on the floor
  g.save(); g.globalCompositeOperation = 'lighter';
  for (const s of [-1, 1]) { const [x, y] = P(s * 158, 0, 1.62); softEllipse(g, x, y, 150, 22, '#ffb35c', 0.07, 0.5); }
  g.restore();
}

function drawFront(g, st) {
  const G = GEO.front, P = proj(G);
  const res = resLevel(g);
  blit(g, 'front:base', 0, 0, G.W, G.H, paintFront, res);
  // mist in the cavern / spilling over the threshold
  g.save();
  g.beginPath(); archPath(g, P, 1, G.hw, G.spring); g.lineTo(G.W, P(0, 0, 1)[1] + 140); g.lineTo(0, P(0, 0, 1)[1] + 140); g.closePath();
  g.clip();
  drawMist(g, MIST.front, st);
  g.restore();
  drawVoidShadow(g, 'front', st);
  // exit door on the left wall (dynamic: opens)
  g.save();
  wallXform(g, G, -1, 1.3, 0, 0.12);
  drawExitDoor(g, st.doorOpen, st.t);
  g.restore();
  // alarm station on the right wall
  g.save();
  wallXform(g, G, 1, ALARM_FRONT.lam, ALARM_FRONT.yup, ALARM_FRONT.cheat);
  drawAlarmStation(g, 0, 0, G.charK, st);
  g.restore();
  if (st.lightsDim > 0) {
    g.fillStyle = `rgba(6,5,14,${0.62 * st.lightsDim})`; g.fillRect(-50, -50, G.W + 100, G.H + 100);
  }
  // emissive: EXIT sign (frontal, sticks out of the wall), daylight through an open door
  {
    const [x, y] = P(-G.hw + 26, 262, 1.3);
    exitSign(g, x, y, 1.05, 1);
  }
  if (st.doorOpen > 0) {
    const [x, y] = P(-G.hw, 0, 1.3);
    g.save(); g.globalCompositeOperation = 'lighter';
    softEllipse(g, x + 70, y + 10, 160, 40, '#ffe2a8', 0.25 * st.doorOpen, 0.5);
    g.restore();
    if (st.lightsDim > 0.01) {
      // the outside light is not dimmed: redraw the doorway over the dimmed room
      g.save();
      g.globalAlpha = clamp(st.doorOpen * 1.5);
      wallXform(g, G, -1, 1.3, 0, 0.12);
      drawExitDoor(g, st.doorOpen, st.t);
      g.restore();
    }
  }
  // NOTE: the console (nearest object to the camera) is drawn by drawHQForeground('front').
}
function drawFrontConsole(g, st) {
  drawConsole(g, 450, FRONT_CONSOLE_Y, 980, 2.3, { ...st, consoleSide: 'back', _clipY: GEO.front.H + 4 });
}
function wallXform(g, G, side, lam, yup, cheat = 0) {
  const P = proj(G);
  const [ox, oy] = P(side * G.hw, yup, lam);
  const k = (lam * lam) / G.f;
  const ux = lerp(G.hw * k, lam, cheat), uy = lerp(side * (G.eye - yup) * k, 0, cheat);
  g.transform(ux, uy, 0, lam, ox, oy);
}

// ================================================================= BACK VIEW
const SCREEN_RECT = { x: 130, y: 140, w: 640, h: 500, r: 46 };
function paintBack(g) {
  const G = GEO.back, P = proj(G), { W, H, hw, spring } = G;
  // walls / vault
  let gr = g.createRadialGradient(450, 420, 100, 450, 600, 1050);
  gr.addColorStop(0, '#3a3268'); gr.addColorStop(0.5, '#2a2450'); gr.addColorStop(1, '#141127');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  // the screen wall (reference plane)
  g.save();
  g.beginPath(); archPath(g, P, 1, hw, spring); g.closePath();
  g.fillStyle = linGrad(g, 0, 0, 0, P(0, 0, 1)[1], [[0, '#2e2758'], [0.6, '#352d66'], [1, '#2a2350']]);
  g.fill();
  g.restore();
  // dado on the screen wall + side walls
  {
    const [lx, ly] = P(-hw, 100, 1), [rx] = P(hw, 100, 1);
    g.fillStyle = '#463b80'; g.fillRect(lx, ly, rx - lx, 9);
    g.fillStyle = 'rgba(190,170,255,0.22)'; g.fillRect(lx, ly - 2, rx - lx, 2);
    const [, fy] = P(0, 0, 1);
    g.fillStyle = 'rgba(12,9,26,0.3)'; g.fillRect(lx, ly + 9, rx - lx, fy - ly - 9);
  }
  for (const s of [-1, 1]) {
    poly(g, [P(s * hw, 0, 1), P(s * hw, 100, 1), P(s * hw, 100, 3.8), P(s * hw, 0, 3.8)]);
    g.fillStyle = 'rgba(12,9,26,0.3)'; g.fill();
    poly(g, [P(s * hw, 100, 1), P(s * hw, 109, 1), P(s * hw, 109, 3.8), P(s * hw, 100, 3.8)]);
    g.fillStyle = '#463b80'; g.fill();
  }
  // screen frame + wall glow are dynamic (colour follows the mode); here only the bezel recess
  const R = SCREEN_RECT;
  g.fillStyle = 'rgba(8,6,18,0.5)'; roundRect(g, R.x - 30, R.y - 26, R.w + 60, R.h + 62, R.r + 24); g.fill();
  screenFrame(g, R);
  // floor
  const fl = [P(-hw, 0, 1), P(hw, 0, 1), P(hw, 0, 3.8), P(-hw, 0, 3.8)];
  poly(g, fl);
  g.fillStyle = linGrad(g, 0, fl[0][1], 0, H, [[0, '#2f2858'], [0.22, '#262048'], [0.55, '#17132e'], [1, '#0d0b1c']]);
  g.fill();
  g.save(); poly(g, fl); g.clip();
  for (const X of [-260, -175, -90, 0, 90, 175, 260]) {
    const [x0, y0] = P(X, 0, 1), [x1, y1] = P(X, 0, 3.8);
    g.strokeStyle = linGrad(g, x0, y0, x1, y1, [[0, rgba('#9a88f0', 0.2)], [0.45, rgba('#9a88f0', 0.1)], [1, rgba('#8a6cff', 0.03)]]);
    g.lineWidth = 2;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
  }
  for (const lam of [1.15, 1.45, 1.85, 2.4, 3.1]) {
    const [x0, y0] = P(-hw, 0, lam), [x1] = P(hw, 0, lam);
    g.strokeStyle = rgba('#9a88f0', 0.06 * (lam < 2 ? 1 : 0.6)); g.lineWidth = 1.5 * lam;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y0); g.stroke();
  }
  g.restore();
  // ribs
  rib(g, P, 2.2, hw, spring, 22);
  rib(g, P, 1.5, hw, spring, 22);
  rib(g, P, 1, hw, spring, 22, { body: '#40367a', hi: 'rgba(200,180,255,0.35)' });
  // darkness of the back of the mind around the camera (bottom + edges)
  g.fillStyle = linGrad(g, 0, 1050, 0, H, [[0, 'rgba(8,6,18,0)'], [1, 'rgba(8,6,18,0.55)']]);
  g.fillRect(0, 1050, W, H - 1050);
  const vg = g.createRadialGradient(450, 650, 380, 450, 820, 1050);
  vg.addColorStop(0, 'rgba(8,6,18,0)'); vg.addColorStop(1, 'rgba(8,6,18,0.5)');
  g.fillStyle = vg; g.fillRect(0, 0, W, H);
}
function screenFrame(g, R, light) {
  // bezel (rounded, soft gold inner trim)
  g.save();
  g.lineJoin = 'round';
  roundRect(g, R.x - 22, R.y - 22, R.w + 44, R.h + 44, R.r + 18);
  g.fillStyle = linGrad(g, 0, R.y - 22, 0, R.y + R.h + 22, [[0, '#4a3e88'], [1, '#2c2556']]);
  g.fill();
  g.strokeStyle = C.line; g.lineWidth = 3.5; g.stroke();
  roundRect(g, R.x - 7, R.y - 7, R.w + 14, R.h + 14, R.r + 5);
  g.strokeStyle = '#d9b45e'; g.lineWidth = 3; g.stroke();
  roundRect(g, R.x - 1, R.y - 1, R.w + 2, R.h + 2, R.r);
  g.strokeStyle = C.line; g.lineWidth = 3; g.stroke();
  // top-left soft highlight on the bezel
  g.strokeStyle = 'rgba(210,195,255,0.25)'; g.lineWidth = 3;
  g.beginPath(); g.moveTo(R.x - 14, R.y + R.h * 0.4); g.lineTo(R.x - 14, R.y + R.r - 8); g.quadraticCurveTo(R.x - 14, R.y - 14, R.x + R.r - 8, R.y - 14); g.lineTo(R.x + R.w * 0.4, R.y - 14); g.stroke();
  g.restore();
}
function drawBack(g, st) {
  const G = GEO.back, P = proj(G);
  const res = resLevel(g);
  blit(g, 'back:base', 0, 0, G.W, G.H, paintBack, res);
  if (st.lightsDim > 0) { g.fillStyle = `rgba(6,5,14,${0.62 * st.lightsDim})`; g.fillRect(0, 0, G.W, G.H); }
  const R = SCREEN_RECT;
  const lc = screenLightColor(st);
  // light from the screen onto the wall, ceiling and floor
  g.save();
  // skip the pixels the opaque screen will cover anyway (gradient fills are the main per-frame cost)
  g.beginPath(); g.rect(-50, -50, G.W + 100, G.H + 100); g.rect(R.x + 4, R.y + 4, R.w - 8, R.h - 8);
  g.clip('evenodd');
  g.globalCompositeOperation = 'lighter';
  softEllipse(g, R.x + R.w / 2, R.y + R.h / 2 + 30, R.w * 0.82, R.h * 1.0, lc, 0.18, 0.45);
  g.restore();
  drawScreenBlend(g, R.x, R.y, R.w, R.h, st, R.r);
  // glass sheen
  g.save();
  roundRect(g, R.x, R.y, R.w, R.h, R.r); g.clip();
  g.fillStyle = linGrad(g, R.x, R.y, R.x + R.w * 0.6, R.y + R.h, [[0, 'rgba(255,255,255,0.10)'], [0.35, 'rgba(255,255,255,0.0)'], [1, 'rgba(255,255,255,0)']]);
  g.fillRect(R.x, R.y, R.w, R.h);
  g.restore();
  // mist + shadow on the floor
  drawMist(g, MIST.back, st);
  drawVoidShadow(g, 'back', st);
  // console (controls side) in the midground
  drawBackConsole(g, st);
}
const BACK_CONSOLE = { x: 450, lam: 1.42, w: 800, size: 1.0, deck: 1.7 };
function drawBackConsole(g, st) {
  const G = GEO.back, P = proj(G);
  const [, y] = P(0, 0, BACK_CONSOLE.lam);
  // the console's warm light on the wall under the screen (reads even where the operators hide the buttons)
  const glowK = st.consoleGlow * (1 - st.lightsDim * 0.35);
  if (glowK > 0.01) {
    g.save();
    g.globalCompositeOperation = 'lighter';
    softEllipse(g, BACK_CONSOLE.x, y - 150, BACK_CONSOLE.w * 0.56, 70, C.amber, 0.1 * glowK, 0.55);
    g.restore();
  }
  drawConsole(g, BACK_CONSOLE.x, y, BACK_CONSOLE.w, G.charK * BACK_CONSOLE.lam * BACK_CONSOLE.size, { ...st, consoleSide: 'controls', consoleDeck: BACK_CONSOLE.deck });
}

// ================================================================= ALARM (side wall close-up)
function paintAlarm(g) {
  const G = GEO.alarm, { W, H } = G, base = G.wallBase;
  // wall
  g.fillStyle = linGrad(g, 0, 0, 0, base, [[0, '#211c40'], [0.45, '#2e2858'], [1, '#2a2450']]);
  g.fillRect(0, 0, W, base);
  // left side darker (toward the back of the mind), right side faint cool screen-light
  g.fillStyle = linGrad(g, 0, 0, W, 0, [[0, 'rgba(8,6,18,0.55)'], [0.35, 'rgba(8,6,18,0)'], [0.75, 'rgba(159,216,255,0)'], [1, 'rgba(159,216,255,0.07)']]);
  g.fillRect(0, 0, W, base);
  // niche framing the alarm
  const nx = ALARM_CLOSE.x, nw = 300, ntop = 330, nbot = 1105;
  g.save();
  g.beginPath();
  g.moveTo(nx - nw / 2, nbot); g.lineTo(nx - nw / 2, ntop + nw / 2); g.arc(nx, ntop + nw / 2, nw / 2, Math.PI, 0); g.lineTo(nx + nw / 2, nbot); g.closePath();
  g.fillStyle = linGrad(g, 0, ntop, 0, nbot, [[0, '#1d1838'], [1, '#262049']]);
  g.fill();
  g.strokeStyle = '#41377a'; g.lineWidth = 22; g.stroke();
  g.strokeStyle = 'rgba(200,180,255,0.3)'; g.lineWidth = 3;
  g.beginPath(); g.moveTo(nx - nw / 2 - 9, nbot); g.lineTo(nx - nw / 2 - 9, ntop + nw / 2); g.arc(nx, ntop + nw / 2, nw / 2 + 9, Math.PI, -0.2); g.stroke();
  g.strokeStyle = 'rgba(8,6,18,0.5)'; g.lineWidth = 6;
  g.beginPath(); g.moveTo(nx - nw / 2 + 13, nbot); g.lineTo(nx - nw / 2 + 13, ntop + nw / 2); g.arc(nx, ntop + nw / 2, nw / 2 - 13, Math.PI, 0); g.lineTo(nx + nw / 2 - 13, nbot); g.stroke();
  g.restore();
  // wainscot
  g.fillStyle = '#251f47'; g.fillRect(0, 1105, W, base - 1105);
  g.fillStyle = '#4a3f86'; roundRect(g, -10, 1092, W + 20, 18, 9); g.fill();
  g.fillStyle = 'rgba(200,180,255,0.3)'; g.fillRect(0, 1093, W, 3);
  g.fillStyle = 'rgba(8,6,18,0.45)'; g.fillRect(0, 1110, W, 6);
  for (let i = 0; i < 4; i++) {
    const px = 95 + i * 210;
    roundRect(g, px, 1140, 175, 170, 22);
    g.fillStyle = 'rgba(12,9,26,0.22)'; g.fill();
    g.strokeStyle = 'rgba(160,140,230,0.16)'; g.lineWidth = 2.5; g.stroke();
  }
  // baseboard
  g.fillStyle = '#17132e'; g.fillRect(0, base - 26, W, 26);
  g.fillStyle = 'rgba(190,170,255,0.18)'; g.fillRect(0, base - 26, W, 2);
  // pilasters (vault ribs coming down)
  for (const px of [36, W - 36]) {
    g.fillStyle = linGrad(g, px - 40, 0, px + 40, 0, [[0, '#1d1838'], [0.35, '#463b80'], [0.7, '#3a3170'], [1, '#191530']]);
    g.fillRect(px - 40, 0, 80, base);
    g.strokeStyle = 'rgba(8,6,18,0.55)'; g.lineWidth = 3;
    g.beginPath(); g.moveTo(px - 40, 0); g.lineTo(px - 40, base); g.moveTo(px + 40, 0); g.lineTo(px + 40, base); g.stroke();
    g.fillStyle = '#2c2558'; roundRect(g, px - 48, base - 70, 96, 70, 8); g.fill();
    g.fillStyle = 'rgba(200,180,255,0.2)'; g.fillRect(px - 48, base - 70, 96, 3);
  }
  // the vault arching overhead between the pilasters
  g.save();
  g.lineCap = 'butt';
  g.strokeStyle = 'rgba(8,6,18,0.5)'; g.lineWidth = 64;
  g.beginPath(); g.arc(G.vx, 980, 900, Math.PI * 1.2, Math.PI * 1.8); g.stroke();
  g.strokeStyle = '#3a3170'; g.lineWidth = 46;
  g.beginPath(); g.arc(G.vx, 980, 900, Math.PI * 1.2, Math.PI * 1.8); g.stroke();
  g.strokeStyle = 'rgba(200,180,255,0.3)'; g.lineWidth = 3;
  g.beginPath(); g.arc(G.vx, 980, 878, Math.PI * 1.2, Math.PI * 1.8); g.stroke();
  g.restore();
  // sconce (warm practical, upper left)
  sconce(g, ALARM_SCONCE[0], ALARM_SCONCE[1], 1.8);
  // sticky note: a little joke from the past (left of the niche, level with the bell, above FEAR's head)
  g.save();
  g.translate(ALARM_NOTE[0], ALARM_NOTE[1]); g.rotate(-0.06);
  g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(-58, -48, 120, 108);
  g.fillStyle = '#ffe68a'; g.fillRect(-62, -54, 120, 108);
  g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(-30, -62, 56, 16);
  g.fillStyle = '#4a3a6a'; g.textAlign = 'center'; g.font = '25px Caveat';
  g.fillText('only for', -2, -16); g.fillText('REAL', -2, 12); g.fillText('emergencies!', -2, 38);
  g.restore();
  // floor
  g.fillStyle = linGrad(g, 0, base, 0, H, [[0, '#2a2350'], [0.3, '#211b40'], [1, '#141029']]);
  g.fillRect(0, base, W, H - base);
  g.fillStyle = 'rgba(8,6,18,0.5)'; g.fillRect(0, base, W, 8);
  g.save();
  g.beginPath(); g.rect(0, base, W, H - base); g.clip();
  for (let i = -6; i <= 6; i++) {
    const x0 = G.vx + i * 150, y0 = base;
    const t = (H - G.vy) / (base - G.vy);
    const x1 = G.vx + (x0 - G.vx) * t;
    g.strokeStyle = rgba('#9a88f0', 0.08); g.lineWidth = 2;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, H); g.stroke();
  }
  // reflections: the alarm red on the floor, sconce warm
  g.globalCompositeOperation = 'lighter';
  softEllipse(g, ALARM_SCONCE[0], base + 50, 150, 30, '#ffb35c', 0.1);
  softEllipse(g, ALARM_CLOSE.x, base + 40, 110, 22, '#ff4d5e', 0.07);
  g.restore();
}
function drawAlarmView(g, st) {
  const G = GEO.alarm;
  const res = resLevel(g);
  blit(g, 'alarm:base', 0, 0, G.W, G.H, paintAlarm, res);
  drawMist(g, MIST.alarm, st);
  drawVoidShadow(g, 'alarm', st);
  drawAlarmStation(g, ALARM_CLOSE.x, ALARM_CLOSE.y, ALARM_CLOSE.s, st);
  if (st.lightsDim > 0) { g.fillStyle = `rgba(6,5,14,${0.62 * st.lightsDim})`; g.fillRect(-50, -50, G.W + 100, G.H + 100); }
  // red glow pooled in the niche when ringing
  if (st.alarm > 0.01) {
    const p = 0.5 + 0.5 * Math.sin(st.t * TAU * 1.2);
    g.save(); g.globalCompositeOperation = 'lighter';
    softEllipse(g, ALARM_CLOSE.x, 700, 200, 380, C.red, 0.1 * st.alarm * (0.6 + 0.4 * p));
    g.restore();
  }
}

// ================================================================= BACK OF THE MIND
const BOM = { lx: 380, ly: 1032 };
// corridor projection for the back of the mind: VP at the distant light, camera height 620
const BOMP = (X, Y, l) => [BOM.lx + l * X, GEO.backOfMind.vy + l * (620 - Y)];
function paintBackOfMind(g) {
  const G = GEO.backOfMind, { W, H } = G;
  const hz = G.vy;
  // sky of the cavern: near-black violet, hazier toward the distant light
  g.fillStyle = linGrad(g, 0, 0, 0, hz, [[0, '#07060e'], [0.45, '#0d0b1c'], [0.85, '#1a1538'], [1, '#272056']]);
  g.fillRect(0, 0, W, hz + 2);
  softEllipse(g, BOM.lx + 60, hz - 60, 760, 560, '#2a2260', 0.6, 0.45);
  softEllipse(g, BOM.lx, hz - 20, 320, 170, '#4a3d90', 0.5, 0.45);
  // haze behind where the Void stands (so its silhouette separates)
  softEllipse(g, 700, 620, 380, 620, '#221b4a', 0.55, 0.5);
  // floor
  g.fillStyle = linGrad(g, 0, hz, 0, H, [[0, '#2a2358'], [0.08, '#1c1740'], [0.4, '#130f2c'], [1, '#0a0816']]);
  g.fillRect(0, hz, W, H - hz);
  // great ribs of the cavern (the HQ's vault, grown vast and fading into the dark)
  const Xc = 150, hwC = 700, spr = 900;
  const ribs = [[0.22, 0.25], [0.34, 0.35], [0.5, 0.5], [0.72, 0.7], [1.02, 0.9]];
  for (const [l, k] of ribs) {
    const [cx, cy] = BOMP(Xc, spr, l), r = hwC * l;
    const [lxL, fyL] = BOMP(Xc - hwC, 0, l), [lxR] = BOMP(Xc + hwC, 0, l);
    const lw = 46 * l;
    g.save();
    g.lineCap = 'butt';
    const body = mixColor('#211b48', '#0b0918', k);
    g.strokeStyle = body; g.lineWidth = lw;
    g.beginPath(); g.moveTo(lxL, fyL); g.lineTo(lxL, cy); g.arc(cx, cy, r, Math.PI, 0); g.lineTo(lxR, fyL); g.stroke();
    // legs dissolve into floor mist
    g.strokeStyle = rgba(C.violet, 0.12 + 0.3 * k); g.lineWidth = Math.max(1.2, 3.2 * l);
    g.beginPath(); g.arc(cx, cy, r - lw * 0.42, Math.PI * 1.04, Math.PI * 1.62); g.stroke();
    g.strokeStyle = rgba(C.cyan, 0.06 + 0.12 * k); g.lineWidth = Math.max(1, 2.2 * l);
    g.beginPath(); g.arc(cx, cy, r + lw * 0.42, Math.PI * 1.58, Math.PI * 1.92); g.stroke();
    g.strokeStyle = linGrad(g, 0, cy, 0, fyL, [[0, rgba(C.violet, 0.1 + 0.2 * k)], [0.6, rgba(C.violet, 0.05 + 0.1 * k)], [1, rgba(C.violet, 0)]]);
    g.lineWidth = Math.max(1.2, 3 * l);
    g.beginPath(); g.moveTo(lxL + lw * 0.42, cy); g.lineTo(lxL + lw * 0.42, fyL); g.stroke();
    g.restore();
    softEllipse(g, lxL, fyL, 160 * l + 40, 30 * l + 10, '#2c2560', 0.5, 0.5);
    softEllipse(g, lxR, fyL, 160 * l + 40, 30 * l + 10, '#2c2560', 0.5, 0.5);
  }
  // glow pathways converging on the distant light
  g.save();
  g.beginPath(); g.rect(0, hz, W, H - hz); g.clip();
  g.lineCap = 'round';
  const N = 11;
  for (let i = 0; i < N; i++) {
    const u = i / (N - 1);
    const X = lerp(-1500, 1700, u) + Math.sin(i * 2.3) * 90;
    const [bx, by] = BOMP(X, 0, 1.25);
    const col = i % 3 === 1 ? C.cyan : C.violet;
    const bend = Math.sin(i * 1.7 + 0.5) * 110;
    const path = () => {
      g.beginPath(); g.moveTo(BOM.lx, hz + 1);
      g.bezierCurveTo(lerp(BOM.lx, bx, 0.3) + bend, lerp(hz, by, 0.3), lerp(BOM.lx, bx, 0.65) - bend * 0.7, lerp(hz, by, 0.65), bx, by);
    };
    for (const [lw, k] of [[9, 0.25], [2.2, 1]]) {
      const gr = g.createLinearGradient(BOM.lx, hz, bx, by);
      gr.addColorStop(0, rgba(col, 0)); gr.addColorStop(0.1, rgba(col, 0.34 * k)); gr.addColorStop(0.45, rgba(col, 0.16 * k)); gr.addColorStop(1, rgba(col, 0));
      g.strokeStyle = gr; g.lineWidth = lw;
      path(); g.stroke();
    }
  }
  // depth rings on the floor around the light
  for (const [l, a] of [[0.12, 0.16], [0.25, 0.12], [0.45, 0.09], [0.75, 0.07], [1.1, 0.05]]) {
    const ry = 620 * l * 0.32, rx = ry * 4.2;
    g.strokeStyle = rgba(C.violet, a); g.lineWidth = 1.2 + l * 2;
    g.beginPath(); g.ellipse(BOM.lx, hz + 620 * l * 0.9, rx, ry, 0, Math.PI + 0.25, TAU - 0.25); g.stroke();
  }
  g.globalCompositeOperation = 'lighter';
  softEllipse(g, BOM.lx, hz + 80, 70, 150, '#cfeeff', 0.12, 0.5);
  softEllipse(g, BOM.lx, hz + 16, 340, 46, '#8a6cff', 0.16, 0.5);
  // a soft pool of light on the ground where the cage stands
  softEllipse(g, 300, 1640, 320, 70, '#4a3d8c', 0.22, 0.5);
  g.restore();
  // the distant HQ: a tiny glowing screen above a warm console line, far away
  g.save();
  g.globalCompositeOperation = 'lighter';
  glow(g, BOM.lx, BOM.ly, 380, '#5a4aa8', 0.3);
  glow(g, BOM.lx, BOM.ly - 8, 150, '#cfeeff', 0.28);
  glow(g, BOM.lx, BOM.ly + 12, 80, C.amber, 0.22);
  g.restore();
  g.fillStyle = 'rgba(225,244,255,0.85)'; roundRect(g, BOM.lx - 17, BOM.ly - 20, 34, 22, 4); g.fill();
  g.fillStyle = 'rgba(255,217,160,0.85)'; roundRect(g, BOM.lx - 15, BOM.ly + 7, 30, 3, 1.5); g.fill();
  // vignette
  const vg = g.createRadialGradient(W * 0.42, H * 0.6, H * 0.32, W * 0.5, H * 0.55, H * 0.82);
  vg.addColorStop(0, 'rgba(4,3,10,0)'); vg.addColorStop(1, 'rgba(4,3,10,0.55)');
  g.fillStyle = vg; g.fillRect(0, 0, W, H);
}
function drawBackOfMind(g, st) {
  const G = GEO.backOfMind;
  const res = resLevel(g);
  blit(g, 'bom:base', 0, 0, G.W, G.H, paintBackOfMind, res);
  if (st.lightsDim > 0) { g.fillStyle = `rgba(4,3,10,${0.5 * st.lightsDim})`; g.fillRect(0, 0, G.W, G.H); }
  // distant light breathes very slowly; turns red when the alarm rings
  const br = 0.5 + 0.5 * Math.sin(st.t * 0.5);
  g.save();
  g.globalCompositeOperation = 'lighter';
  glow(g, BOM.lx, BOM.ly, 180, st.alarm > 0 ? mixColor('#cfeeff', C.red, st.alarm) : '#cfeeff', 0.06 + 0.04 * br + st.alarm * 0.12 * (0.5 + 0.5 * Math.sin(st.t * TAU * 1.2)));
  g.restore();
  // drifting motes (few, tiny, slow)
  g.save();
  for (let i = 0; i < 14; i++) {
    const x = (rand(i, 3) * G.W + st.t * (4 + rand(i, 4) * 6)) % G.W;
    const y = 300 + rand(i, 5) * 1200 + Math.sin(st.t * 0.3 + i) * 12;
    const a = 0.12 + 0.18 * (0.5 + 0.5 * Math.sin(st.t * (0.6 + rand(i, 6)) + i * 3));
    g.fillStyle = rgba(i % 3 ? '#b9a6ff' : '#9fe3ff', a);
    circle(g, x, y, 1.6 + rand(i, 7) * 1.4); g.fill();
  }
  g.restore();
  drawMist(g, MIST.backOfMind, st);
  drawVoidShadow(g, 'backOfMind', st);
}

// ================================================================= PUBLIC: set / foreground / light
/** Draw the set for a view. state: see docs/hq.md. */
export function drawHQ(g, view = 'front', state = {}) {
  const st = norm(state);
  const back = keepStyles(g);
  g.save();
  // paint a dark margin around the stage so a camera that strays outside never shows stale pixels
  const G = GEO[view] || GEO.front, M = 3000;
  g.fillStyle = view === 'backOfMind' ? '#07060e' : '#120f24';
  g.fillRect(-M, -M, G.W + 2 * M, M); g.fillRect(-M, G.H, G.W + 2 * M, M);
  g.fillRect(-M, 0, M, G.H); g.fillRect(G.W, 0, M, G.H);
  if (view === 'back') drawBack(g, st);
  else if (view === 'alarm') drawAlarmView(g, st);
  else if (view === 'backOfMind') drawBackOfMind(g, st);
  else drawFront(g, st);
  g.restore();
  back();
}

/** Layers in front of characters: console front panel (front view), low foreground mist (others). */
function _drawHQForeground(g, view = 'front', state = {}) {
  const st = norm(state);
  g.save();
  if (view === 'front') {
    drawFrontConsole(g, st);
    // amber light rising from the console onto the operators (additive, soft)
    const glowK = st.consoleGlow * (1 - st.lightsDim * 0.35);
    g.globalCompositeOperation = 'lighter';
    softEllipse(g, 450, 1285, 430, 150, C.amber, 0.085 * glowK, 0.6);
    for (let i = 0; i < 4; i++) {
      // station i is mirrored in this view: station 0 (JOY) works at consoleSlot4 (see HQ_STATIONS)
      const [x] = HQ_VIEWS.front.anchors[`consoleSlot${4 - i}`];
      let press = 0;
      for (let k = 0; k < 4; k++) press = Math.max(press, clamp(st.consolePress[4 * i + k] || 0));
      if (press > 0.01) softEllipse(g, x, 1275, 100, 140, C.amber, 0.08 * glowK * press, 0.5);
    }
  } else {
    drawMist(g, MIST_FG[view] || [], st, 5);
  }
  g.restore();
}

// beacon position + beam size per view, and the reach of the red wash around it (the wash is partial:
// strongest on the alarm's side of the room, fading out across the frame)
const BEACON = {
  front: () => {
    const G = GEO.front, P = proj(G);
    const k = G.charK, lam = ALARM_FRONT.lam;
    const [hx, hy] = frontAlarmHandle();
    return [hx + 0, hy - 352 * k * lam, 0.55];
  },
  back: () => [-30, 520, 1.2],
  alarm: () => [ALARM_CLOSE.x, ALARM_CLOSE.y - 352 * ALARM_CLOSE.s, 1.6],
  backOfMind: () => [BOM.lx, BOM.ly - 10, 0.6],
};
// x0 -> x1: the wash ramps from nothing (x0) to full (x1) and stays full beyond x1 (a horizontal ramp is
// ~3x cheaper than a full-frame radial multiply); r: a radial wash of that radius around the beacon instead
const WASH = { front: { x0: 260, x1: 720 }, back: { x0: 640, x1: 120 }, alarm: { x0: 40, x1: 560 }, backOfMind: { r: 480 } };

/**
 * Soft red alarm light, drawn AFTER characters (world coords, same camera). Uses state.alarm (0..1)
 * and state.t. A rotating beacon sweep + a gentle red wash pulsing at 1.2 Hz (max alpha ~0.3) that covers
 * only the alarm's side of the room (partial, never a full-frame flash).
 */
function _drawAlarmLight(g, view = 'front', state = {}) {
  const st = norm(state);
  const A = st.alarm;
  if (A <= 0.002) return;
  const G = GEO[view] || GEO.front;
  const [bx, by, bs] = (BEACON[view] || BEACON.front)();
  const t = st.t;
  const pulse = 0.5 + 0.5 * Math.sin(t * TAU * 1.2 - Math.PI / 2);
  g.save();
  // gentle red wash (multiply, max alpha 0.3) on the alarm's side of the room only, fading out across it
  const wash = A * (0.2 + 0.2 * pulse) * 0.75;
  const WS = WASH[view] || WASH.front, WCOL = '#ff6472';
  g.globalCompositeOperation = 'multiply';
  if (WS.r) {
    const wg = g.createRadialGradient(bx, by, 0, bx, by, WS.r);
    wg.addColorStop(0, rgba(WCOL, wash)); wg.addColorStop(0.45, rgba(WCOL, wash * 0.75)); wg.addColorStop(1, rgba(WCOL, 0));
    g.fillStyle = wg;
    g.fillRect(bx - WS.r, by - WS.r, WS.r * 2, WS.r * 2);
  } else {
    const xa = Math.min(WS.x0, WS.x1), xb = Math.max(WS.x0, WS.x1);
    const wg = g.createLinearGradient(WS.x0, 0, WS.x1, 0);
    wg.addColorStop(0, rgba(WCOL, 0)); wg.addColorStop(0.55, rgba(WCOL, wash * 0.7)); wg.addColorStop(1, rgba(WCOL, wash));
    g.fillStyle = wg;
    g.fillRect(xa, -200, xb - xa, G.H + 400);
    g.fillStyle = rgba(WCOL, wash);
    if (WS.x1 > WS.x0) g.fillRect(xb, -200, G.W + 200 - xb, G.H + 400);
    else g.fillRect(-200, -200, xa + 200, G.H + 400);
  }
  g.globalCompositeOperation = 'lighter';
  const gr2 = 520 * Math.max(1, bs * 0.8);
  glow(g, bx, by + gr2 * 0.3, gr2, C.red, A * (0.07 + 0.12 * pulse));
  g.globalCompositeOperation = 'source-over';
  // rotating beacon sweep (two opposite beams)
  if (view !== 'backOfMind') {
    g.globalCompositeOperation = 'lighter';
    const ph = t * TAU * 0.9;
    for (const off of [0, Math.PI]) {
      const a = ph + off;
      const sx = Math.cos(a), toward = Math.sin(a);
      const len = 900 * bs * (0.35 + 0.65 * Math.abs(sx));
      const dir = sx >= 0 ? 0 : Math.PI;
      const tilt = 0.32;
      const ang = dir + (sx >= 0 ? tilt : -tilt);
      const spread = 0.28;
      const alpha = A * 0.16 * (0.4 + 0.6 * Math.abs(sx)) * (toward > 0 ? 1 : 0.6);
      const bg = g.createRadialGradient(bx, by, 0, bx, by, len);
      bg.addColorStop(0, rgba('#ff7a86', alpha));
      bg.addColorStop(1, rgba('#ff4d5e', 0));
      g.fillStyle = bg;
      g.beginPath();
      g.moveTo(bx, by);
      g.arc(bx, by, len, ang - spread, ang + spread);
      g.closePath();
      g.fill();
    }
    // halo at the beacon (brightest when the lamp faces us)
    const face = 0.5 + 0.5 * Math.sin(ph);
    glow(g, bx, by, 120 * bs, '#ff5a6a', A * (0.18 + 0.3 * face));
    glow(g, bx, by, 40 * bs, '#ffd0d6', A * (0.2 + 0.4 * face));
  }
  g.restore();
}

// ---- anchors that depend on the console geometry (computed once at load)
{
  const G = GEO.back, P = proj(G);
  const [, y] = P(0, 0, BACK_CONSOLE.lam);
  const sc = G.charK * BACK_CONSOLE.lam * BACK_CONSOLE.size;
  for (let i = 0; i < 4; i++) {
    const [bx, by] = consoleButtonPos(BACK_CONSOLE.x, y, BACK_CONSOLE.w, sc, 4 * i, BACK_CONSOLE.deck);
    HQ_VIEWS.back.anchors[`button${i + 1}`] = [Math.round(bx), Math.round(by), 0];
  }
}

// ---- public wrappers (restore fill/stroke styles, see keepStyles)
const wrap = (fn) => function (g, ...a) { const r = keepStyles(g); try { return fn(g, ...a); } finally { r(); } };
export const drawScreenContent = wrap(_drawScreenContent);
export const drawConsole = wrap(_drawConsole);
export const drawAlarmStation = wrap(_drawAlarmStation);
export const drawHQForeground = wrap(_drawHQForeground);
export const drawAlarmLight = wrap(_drawAlarmLight);
