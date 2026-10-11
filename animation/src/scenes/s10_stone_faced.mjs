// s10 · stone_faced · backOfMind (dissolve in)
// NARRATOR: "And the Void stood there, stone-faced, its shadow filling half the room." / silent: Fear turns its back.
import { createCanvas } from '@napi-rs/canvas';
import { W, H, clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette, TAU } from '../engine.mjs';
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

// ---- the shadow filling half the room (world coords, backOfMind)
// On the near-black cavern floor the Void's own spill barely registers, so the shadow is staged as a dark tide on
// the floor plane: a wedge whose edge is a floor line through the vanishing point (the far glow), swinging from the
// Void's hem (right) across the cage and Fear and on over the fan of glowing pathways left of the cage (the only lit
// floor in frame: right of the cage the floor is already near-black, so a tide that stopped at the cage changed
// almost nothing but Fear). What stays lit is a thin strip along the horizon leading to the far HQ (where
// Consciousness went). It fades out toward the horizon, so the far glow and the converging tips of the pathways are
// untouched. The sweep is keyed by the edge's angle (uniform angular speed), converted to its x at the cage floor.
const VP = [380, 1040];                  // vanishing point = the far glow on the floor horizon
const EDGE_Y = 1630;                     // edge parameterised by its x at the cage's floor line
const edgeX = (xe, y) => VP[0] + (xe - VP[0]) * (y - VP[1]) / (EDGE_Y - VP[1]);
function wedgePath(g, xe) {
  g.beginPath();
  g.moveTo(VP[0], VP[1]);
  g.lineTo(edgeX(xe, 1900), 1900);
  g.lineTo(2200, 1900);
  g.lineTo(2200, VP[1]);
  g.closePath();
}
/** the floor shadow; `xe` = the edge's x at the cage's floor, `a` = core opacity. Drawn at quarter resolution and
 *  scaled up (the bilinear upscale is the soft edge, and the big gradient fill costs 1/16). Call with identity. */
const SQ = 4;
let SHC = null;
function floorShadow(g, cam, xe, a) {
  if (a <= 0.01 || xe > 2000) return;
  const c = (SHC ||= createCanvas(W / SQ, H / SQ)), sg = c.getContext('2d');
  sg.setTransform(1, 0, 0, 1, 0, 0);
  sg.clearRect(0, 0, W / SQ, H / SQ);
  sg.scale(1 / SQ, 1 / SQ);
  applyCamera(sg, cam);
  const gr = sg.createRadialGradient(VP[0], VP[1], 40, VP[0], VP[1], 520);
  gr.addColorStop(0, 'rgba(4,3,10,0)');
  gr.addColorStop(0.35, `rgba(4,3,10,${0.55 * a})`);
  gr.addColorStop(1, `rgba(4,3,10,${a})`);
  sg.fillStyle = gr;
  wedgePath(sg, xe + 30);
  sg.fill();
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.imageSmoothingEnabled = true;
  g.drawImage(c, 0, 0, W, H);
  g.restore();
}
/** the same tide over the cage + Fear layer only (source-atop on their own layer) */
function layerShadow(lg, xe, a) {
  if (a <= 0.01) return;
  const n = 6, pa = 1 - Math.pow(1 - a, 1 / n);
  lg.save();
  lg.globalCompositeOperation = 'source-atop';
  lg.fillStyle = `rgba(6,4,16,${pa})`;
  for (let i = 0; i < n; i++) { wedgePath(lg, xe + i * 10); lg.fill(); }
  lg.restore();
}
// the cage + Fear layer covers only the cage's screen box (world x 300…570, y 1090…1730), not the full frame
const BOX = [300, 1090, 570, 1730];
const LW = 300, LH = 560;
let LAYER = null;
const layerCanvas = () => (LAYER ||= createCanvas(LW, LH));

// ---------------------------------------------------------------- render
export function render(g, t, S) {
  const b2 = S.T('s10b02');
  // a very slow pull-back during the line that settles and LOCKS for b02 (only Fear moves). It opens wide enough that
  // the whole hood opening is in frame on 'stone-faced' (the old {560,1000,0.9} start cut the face of darkness off at
  // the top edge until the end of the line) and ends with headroom over the hood and the cage clear of the bottom.
  const c = S.k(t, [['scene.start', { x: 538, y: 925, zoom: 0.78 }], ['s10b02-0.3', { x: 525, y: 895, zoom: 0.74 }, 'sine']]);
  const amp = 2.2 * (1 - sstep(b2 - 1.6, b2 - 0.3, t));
  const d = drift(t, 1, 10);
  const cam = { x: c.x + d.dx * amp / c.zoom, y: c.y + d.dy * amp / c.zoom, zoom: c.zoom, rot: d.dr * 0.5 * amp };
  g.save();
  applyCamera(g, cam);
  const st = { t, ...SET };
  drawHQ(g, 'backOfMind', st);
  const shadowSpread = S.k(t, [['scene.start', 0.4], ['s10b02', 1.0, 'out']]);
  // the tide: from under the robe (hidden) on 'its shadow', over the cage and Fear on 'filling half' (+4.73 → +4.97),
  // then across the lit fan of pathways left of the cage on 'the room' (+3.56 'its' … +5.98 'room'); it stays there
  // through b02. Edge angle 40° (down-right) → 152° (nearly level, pointing left).
  const phi = S.k(t, [['s10b01+3.4', 40], ['s10b01+6.4', 152, 'inOut']]) * Math.PI / 180;
  const xe = VP[0] + (EDGE_Y - VP[1]) * Math.cos(phi) / Math.sin(phi);
  const shA = S.k(t, [['s10b01+3.2', 0.55], ['s10b01+4.6', 0.82]]);
  floorShadow(g, cam, xe, shA);
  drawVoid(g, ...VOID_B, { t, ...STARE_B, idle: 0, shadowSpread });
  g.restore();

  // ---- the cage and Fear, on their own layer so the shadow can pass over them (and only them)
  const lc = layerCanvas(), lg = lc.getContext('2d');
  const bx = Math.floor(W / 2 + (BOX[0] - cam.x) * cam.zoom) - 12, by = Math.floor(H / 2 + (BOX[1] - cam.y) * cam.zoom) - 12;
  lg.setTransform(1, 0, 0, 1, 0, 0);
  lg.clearRect(0, 0, LW, LH);
  lg.save();
  lg.translate(-bx, -by);
  applyCamera(lg, cam);
  const turned = t >= S.T('s10b02+1.2');
  const facing = turned ? -1 : 1;
  const pullT = [1.7, 2.15, 2.6].map((x) => b2 + x);
  let pull = 0;
  for (const p of pullT) { const dd = t - p; if (dd > -0.1 && dd < 0.45) pull = Math.max(pull, Math.sin(clamp((dd + 0.1) / 0.55) * Math.PI)); }
  const cst = { t, door: 0, locked: 1, shake: turned ? 0.45 * pull : 0 };
  drawCage(lg, ...CAGE_B, { ...cst, layer: 'back' });
  const [ox, oy] = cagePoint('occupantSide', ...CAGE_B, cst);
  const fs = CAGE_B[2];
  const fx = ox + NUDGE, fy = oy;
  // the moment the tide's edge crosses Fear (its body spans x ≈ 300…420 at y 1500)
  const xeAtFear = edgeX(xe, 1500);
  const touch = sstep(430, 360, xeAtFear) * (1 - sstep(360, 290, xeAtFear));
  const fp = fearPose(t, S, cst, fx, fy, fs, facing, pull, touch);
  drawFear(lg, fx, fy, fs, fp);
  drawCage(lg, ...CAGE_B, { ...cst, layer: 'front', grips: fp.gripping ? ['gripL'] : undefined, gripScale: 1 });
  // dims Fear's lavender and the cage's rim light as it passes (kept readable: Fear's face must still read)
  layerShadow(lg, xe - 25, 0.34 * clamp(shA / 0.82));
  lg.restore();
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.drawImage(lc, bx, by);
  g.restore();

  g.save();
  applyCamera(g, cam);
  drawHQForeground(g, 'backOfMind', st);
  g.restore();
  grade(g, COLD, 0);
  vignette(g, VIG);
}

function fearPose(t, S, cst, fx, fy, fs, facing, pull, touch = 0) {
  const b2 = S.T('s10b02');
  const loc = (p) => [((p[0] - fx) / fs) * facing, (p[1] - fy) / fs];
  // ---------- b01: curled at the far side, knees up, peeking up-right at the hood; hiccups; eyes never leave it
  const hic = hiccup(t, [0.4, 2.15, 3.0, 4.6, 6.4].map((x) => S.T('s10b01') + x));
  // the shadow's edge reaches it on 'half the' (+4.9 → +5.4): it shrinks into itself, a shiver as the dark touches
  const sink = S.k(t, [['s10b01+4.75', 0], ['s10b01+5.6', 1], ['s10b01+6.6', 0.6]]);
  let face, armL, armR, crouch = 1, headDY = 0, headTilt = 0, headTurn = 0, tremble = 0.5, lean = 0;
  if (t < b2 + 1.2) {
    // eyes dart over the hood (b02), one deliberate blink; then nothing comes and the brows crumple
    const dart = S.k(t, [['s10b02', 0.36], ['s10b02+0.22', 0.5], ['s10b02+0.45', 0.28], ['s10b02+0.7', 0.44], ['s10b02+0.9', 0.36]], 'outCubic');
    const crumple = sstep(b2 + 0.85, b2 + 1.15, t);
    face = {
      ...EXPR.scared, browIn: 0.95, browUp: 0.45 - 0.25 * crumple, lidU: -0.12 - 0.15 * sink + 0.2 * crumple, pupil: 0.7, smile: -0.5 - 0.2 * crumple,
      open: 0.06 + 0.3 * hic, wide: 0.1, tears: 0.75, stream: 0.45, lidTilt: 0.2 + 0.4 * crumple,
      lookX: (t < b2 ? 0.38 + fbm(t * 0.5, 21) * 0.05 : dart), lookY: lerp(-1, -0.55, crumple),
      blink: Math.max(blinkAt(t, S.T('s10b02+0.58'), 0.32), blinkAt(t, S.T('s10b01+5.05'), 0.2)),
    };
    face.noAutoBlink = t > b2 - 0.2;                                          // the waiting stare
    armL = 'hugSelf'; armR = 'hugSelf';
    headDY = -9 * hic + 4 * sink; headTilt = -0.05 + 0.04 * hic; headTurn = 0.12;
    crouch = 1 - 0.22 * hic;                                                  // the little hiccup lifts the shoulders
    tremble = 0.5 - 0.15 * sstep(b2, b2 + 0.8, t) + 0.3 * touch;
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
