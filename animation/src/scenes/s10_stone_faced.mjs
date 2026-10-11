// s10 · stone_faced · backOfMind (dissolve in)
// NARRATOR: "And the Void stood there, stone-faced, its shadow filling half the room." / silent: Fear turns its back.
import { clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette, TAU } from '../engine.mjs';
import { EXPR } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawCage, cagePoint } from '../sets/props.mjs';

export const id = 's10';

// ---- staging constants (data/staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const CAGE_B = [430, 1630, 0.952];
const SET = { lightsDim: 0.35, mist: 0.65 };
const COLD = 0.65, VIG = 0.55;
const NUDGE = -8;                       // Fear's x nudge so no bar crosses an eye (as in the staging check)

export const sfx = [
  { at: 's10b01+2.2', name: 'rumble_low', gain: -14 },                      // swells to 'half the room' (peak +4.8)
  { at: 's10b01+2.72', name: 'sob', gain: -24, pan: -0.15 },                // a small hiccup in the gap after 'stone-faced'
  { at: 's10b02+1.05', name: 'cloth_rustle', gain: -19, pan: -0.15 },       // turns around in place
  { at: 's10b02+1.55', name: 'cage_creak', gain: -19, pan: -0.15, until: 's10b02+2.4' },  // pulls at the bars
  { at: 's10b02+1.75', name: 'sob', gain: -16, pan: -0.15 },
];

// ---------------------------------------------------------------- local helpers
function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
const sstep = (a, b, x) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };
/** irregular little after-sob hiccups: 0..1 pulses */
function hiccup(t, times, dur = 0.32) {
  let v = 0;
  for (const h of times) { const d = t - h; if (d >= 0 && d < dur) v = Math.max(v, Math.sin((d / dur) * Math.PI) * (d < dur * 0.3 ? 1 : 1)); }
  return v;
}

/** an extra soft floor shadow spilling from the Void's hem toward the camera (world coords, backOfMind) */
function shadowPour(g, k) {
  if (k <= 0) return;
  const cx = lerp(690, 600, k), cy = lerp(1630, 1700, k);
  const rx = lerp(320, 1050, k), ry = lerp(110, 400, k);
  g.save();
  g.translate(cx, cy);
  g.scale(1, ry / rx);
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, rx);
  gr.addColorStop(0, `rgba(4,3,10,${0.62 * k})`);
  gr.addColorStop(0.6, `rgba(4,3,10,${0.42 * k})`);
  gr.addColorStop(1, 'rgba(4,3,10,0)');
  g.fillStyle = gr;
  g.beginPath(); g.arc(0, 0, rx, 0, TAU); g.fill();
  g.restore();
}

// ---------------------------------------------------------------- render
export function render(g, t, S) {
  const b2 = S.T('s10b02');
  // very slow pull-back during the line; it settles and LOCKS for b02 (only Fear moves). The pull-back lands on the
  // locked two-shot itself (staging: wide 0.72 then a cut to {545,958,0.8} — a near-identical framing = jump cut).
  const c = S.k(t, [['scene.start', { x: 560, y: 1000, zoom: 0.9 }], ['s10b02-0.3', { x: 545, y: 958, zoom: 0.8 }, 'sine']]);
  const amp = 2.2 * (1 - sstep(b2 - 1.6, b2 - 0.3, t));
  const d = drift(t, 1, 10);
  g.save();
  applyCamera(g, { x: c.x + d.dx * amp / c.zoom, y: c.y + d.dy * amp / c.zoom, zoom: c.zoom, rot: d.dr * 0.5 * amp });
  const st = { t, ...SET };
  drawHQ(g, 'backOfMind', st);
  const shadowSpread = S.k(t, [['scene.start', 0.4], ['s10b02', 1.0, 'out']]);
  // On the near-black cavern floor the Void's own spill barely registers, so a soft extra pour darkens the floor's
  // glowing pathways from its hem toward us, landing on the words "its shadow filling half the room" (+3.7 → +5.96).
  // Continuous (the Void's sprite steps in 0.05 increments); it stays below the horizon, so the far glow is untouched.
  shadowPour(g, S.k(t, [['scene.start', 0.12], ['s10b01+3.6', 0.3], ['s10b01+5.9', 1, 'inOut']]));
  drawVoid(g, ...VOID_B, { t, ...STARE_B, idle: 0, shadowSpread });

  // ---- the cage and Fear
  const turned = t >= S.T('s10b02+1.2');
  const facing = turned ? -1 : 1;
  const pullT = [1.7, 2.15, 2.6].map((x) => b2 + x);
  let pull = 0;
  for (const p of pullT) { const dd = t - p; if (dd > -0.1 && dd < 0.45) pull = Math.max(pull, Math.sin(clamp((dd + 0.1) / 0.55) * Math.PI)); }
  const cst = { t, door: 0, locked: 1, shake: turned ? 0.45 * pull : 0 };
  drawCage(g, ...CAGE_B, { ...cst, layer: 'back' });
  const [ox, oy] = cagePoint('occupantSide', ...CAGE_B, cst);
  const fs = CAGE_B[2];
  const fx = ox + NUDGE, fy = oy;
  const fp = fearPose(t, S, cst, fx, fy, fs, facing, pull);
  drawFear(g, fx, fy, fs, fp);
  drawCage(g, ...CAGE_B, { ...cst, layer: 'front', grips: fp.gripping ? ['gripL'] : undefined, gripScale: 1 });

  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  grade(g, COLD, 0);
  vignette(g, VIG);
}

function fearPose(t, S, cst, fx, fy, fs, facing, pull) {
  const b2 = S.T('s10b02');
  const loc = (p) => [((p[0] - fx) / fs) * facing, (p[1] - fy) / fs];
  // ---------- b01: curled at the far side, knees up, peeking up-right at the hood; hiccups; eyes never leave it
  const hic = hiccup(t, [0.4, 2.15, 3.0, 4.6, 6.4].map((x) => S.T('s10b01') + x));
  const sink = S.k(t, [['s10b01+3.6', 0], ['s10b01+4.6', 1], ['s10b01+6.4', 0.6]]);   // 'its shadow' reaches it
  let face, armL, armR, crouch = 1, headDY = 0, headTilt = 0, headTurn = 0, tremble = 0.5, lean = 0;
  if (t < b2 + 1.2) {
    // eyes dart over the hood (b02), one deliberate blink; then nothing comes and the brows crumple
    const dart = S.k(t, [['s10b02', 0.36], ['s10b02+0.22', 0.5], ['s10b02+0.45', 0.28], ['s10b02+0.7', 0.44], ['s10b02+0.9', 0.36]], 'outCubic');
    const crumple = sstep(b2 + 0.85, b2 + 1.15, t);
    face = {
      ...EXPR.scared, browIn: 0.95, browUp: 0.45 - 0.25 * crumple, lidU: -0.12 - 0.15 * sink + 0.2 * crumple, pupil: 0.7, smile: -0.5 - 0.2 * crumple,
      open: 0.06 + 0.3 * hic, wide: 0.1, tears: 0.75, stream: 0.45, lidTilt: 0.2 + 0.4 * crumple,
      lookX: (t < b2 ? 0.38 + fbm(t * 0.5, 21) * 0.05 : dart), lookY: lerp(-1, -0.55, crumple),
      blink: blinkAt(t, S.T('s10b02+0.58'), 0.32),
    };
    face.noAutoBlink = t > b2 - 0.2;                                          // the waiting stare
    armL = 'hugSelf'; armR = 'hugSelf';
    headDY = -9 * hic + 4 * sink; headTilt = -0.05 + 0.04 * hic; headTurn = 0.12;
    crouch = 1 - 0.22 * hic;                                                  // the little hiccup lifts the shoulders
    tremble = 0.5 - 0.15 * sstep(b2, b2 + 0.8, t);
    // anticipation of the turn: the head goes first (to screen-left), the body gathers
    const ant = sstep(b2 + 0.95, b2 + 1.2, t);
    headTurn = lerp(0.12, -0.45, ant);
    face.lookX = lerp(face.lookX, -0.6, ant);
    crouch = Math.min(crouch, 1 - 0.15 * ant);
  } else {
    // ---------- turned: back to the Void, both hands on the left jamb bar, face lifted to the far glow, crying
    const u = sstep(b2 + 1.2, b2 + 1.55, t);                                 // rises out of the crouch
    const gk = sstep(b2 + 1.3, b2 + 1.65, t);                                // hands up to the bar
    const gl = loc(cagePoint('gripL', ...CAGE_B, cst));
    const glHi = loc([cagePoint('gripL', ...CAGE_B, cst)[0], cagePoint('gripL', ...CAGE_B, cst)[1] - 20 * fs]);
    const hitch = hiccup(t, [1.75, 2.15, 2.5, 2.85, 3.2].map((x) => b2 + x), 0.26);
    crouch = lerp(0.85, 0.3, u);
    armL = { target: [lerp(10, glHi[0] - 6, gk), lerp(-110, glHi[1] + 3 * pull, gk)], bend: 1, front: true, hand: gk > 0.7 ? 'grip' : 'fist' };
    armR = { target: [lerp(-10, gl[0] + 6, gk), lerp(-110, gl[1] + 3 * pull, gk)], bend: -1, front: true, hand: gk > 0.7 ? 'grip' : 'fist' };
    const up = sstep(b2 + 1.35, b2 + 1.9, t);
    face = {
      ...EXPR.crying, browUp: 0.35 + 0.15 * up, lidU: 0.2, lidL: 0.25, open: 0.18 + 0.2 * hitch, tears: 1, stream: 0.6,
      lookX: -0.15 + fbm(t * 0.6, 23) * 0.04, lookY: lerp(-0.4, -0.85, up),
      tearL: S.k(t, [['s10b02+1.8', 0], ['s10b02+3.3', 1, 'linear']]),
      tearR: S.k(t, [['s10b02+2.25', 0], ['s10b02+3.75', 1, 'linear']]),
    };
    if (t < S.T('s10b02+1.8')) face.tearL = 0;
    if (t < S.T('s10b02+2.25')) face.tearR = 0;
    headTilt = 0.12 * up; headDY = -5 * up - 2 * hitch; headTurn = lerp(-0.3, -0.1, up);
    tremble = 0.55 + 0.15 * hitch;
    lean = -0.04 * pull;
  }
  return {
    t, facing, crouch, tremble, lean, headDY, headTilt, headTurn, breathe: 1.4, breathRate: 0.6,
    face, armL, armR, gripping: t >= b2 + 1.2 && sstep(b2 + 1.3, b2 + 1.65, t) > 0.7,
  };
}
