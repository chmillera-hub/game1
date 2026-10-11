// s17 · can_i_help · MIND_HQ. Fear trots back up the alarm corridor, passes under the fire alarm and does
// NOT pull it; pops up at the console beside Consciousness — "Fear." / "Can I help?" — and everyone makes room.
import { clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette } from '../engine.mjs';
import { createCanvas } from '@napi-rs/canvas';
import { drawHQ, drawHQForeground, HQ_VIEWS, hqScaleAt } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, WALK_ADVANCE, selfPoseAnchors, SELF_FACE } from '../chars/self.mjs';
import { drawEmotion } from '../chars/emotions.mjs';
import { EXPR, withSpeech } from '../face.mjs';

export const id = 's17';

// b05: the answer to "Can I help?" plays in a held close on Consciousness (E1, 2.55 s); the step-stool business
// follows in the wide (E). The business was laid out for a cut at b05+1.15: BIZ shifts it with the cut.
const E1_END = 's17b05+2.55';
const BIZ = (x) => `s17b05+${(x + 1.45).toFixed(2)}`;

export const sfx = [
  // b01: the trot up the corridor, the pause under the alarm (a breath), on again, lighter
  { at: 'scene.start+0.36', name: 'footsteps', gain: -14, rate: 2.1, until: 's17b01+0.95' },
  { at: 's17b01+0.85', name: 'breath_shaky', gain: -22, rate: 1.4 },  // in-breath ends as the eyes close (+1.5…+1.98)
  { at: 's17b01+2.0', name: 'footsteps', gain: -16, rate: 1.1, until: 's17b02+0.55' },
  // b02: the pen stops; Fear pops up behind the console
  { at: 's17b02+0.75', name: 'cloth_rustle', gain: -20, pan: 0.2 },
  // b05: Consciousness's eyes well (in-breath), the smile breaks with a laugh-breath out (the exhale, sync 1.45 in
  // the file, lands at b05+1.1), a nod, the clipboard goes down; then (wide) Calm lowers the step-stool, the row
  // scoots over, Consciousness steps aside, Fear climbs, first button
  { at: 's17b05-0.35', name: 'breath_shaky', gain: -22, rate: 1.0, until: 's17b05+2.3', fade: 0.4 },
  { at: 's17b05+2.0', name: 'cloth_rustle', gain: -19 },                       // clipboard down behind the rim
  { at: BIZ(1.05), name: 'cloth_rustle', gain: -19, pan: -0.45 },             // CALM lowers the stool, the row scoots
  { at: BIZ(1.15), name: 'footsteps', gain: -16, pan: 0.3, until: BIZ(2.45) },
  { at: BIZ(1.9), name: 'cloth_rustle', gain: -20, pan: -0.05 },              // Fear climbs onto the stool
  { at: BIZ(2.98), name: 'console_beeps', gain: -18 },
];

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const COSMOS_RESIDUE = 0.5;
const CAGE_F = [302, 846, 0.3];
const FEAR_TIPTOE_F = [532, 1350, 0.8];
const CEO_ASIDE_F = [640, 1300, 0.722];
const ROW_S19 = { CALM: 205, ANGER: 330, FEAR: 450, SADNESS: 570, JOY: 695 };
const ROW_START = { CALM: 165, ANGER: 315, SADNESS: 625, JOY: 735 };
const FA = HQ_VIEWS.front.anchors;
const AA = HQ_VIEWS.alarm.anchors;
const OFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 };
const ROW_Y = 1384, ROW_S = 0.8;

// ---------------------------------------------------------------- local helpers
function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function topShade(g) {
  const gr = g.createLinearGradient(0, 0, 0, 300); gr.addColorStop(0, 'rgba(8,6,20,0.55)'); gr.addColorStop(1, 'rgba(8,6,20,0)');
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = gr; g.fillRect(0, 0, 720, 300); g.restore();
}
const cam = (t, c, amp = 2.5) => { const d = drift(t, amp); return { ...c, shakeX: d.dx, shakeY: d.dy, rot: d.dr }; };
const seg = (t, a, b) => clamp((t - a) / (b - a));
// warm light from a console button on a face (world coords; 'screen')
function buttonLight(g, x, y, r, k) {
  if (k <= 0) return;
  g.save(); g.globalCompositeOperation = 'screen';
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, `rgba(255,214,140,${0.42 * k})`); gr.addColorStop(0.5, `rgba(255,180,90,${0.16 * k})`); gr.addColorStop(1, 'rgba(255,180,90,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore();
}
// the CEO's pen (no module draws it): tip on the clipboard, body up through the fist
function drawPen(g, x, y, s, facing, wrist, wob) {
  const wx = x + facing * wrist[0] * s, wy = y + wrist[1] * s;
  const tip = [wx - facing * (13 - wob[0]) * s, wy - (9 - wob[1]) * s];
  const top = [wx + facing * 14 * s, wy - 40 * s];
  g.save(); g.lineCap = 'round';
  g.strokeStyle = '#1d1c2a'; g.lineWidth = 6.2 * s;
  g.beginPath(); g.moveTo(tip[0], tip[1]); g.lineTo(top[0], top[1]); g.stroke();
  g.strokeStyle = '#3c4a78'; g.lineWidth = 3.8 * s;
  g.beginPath(); g.moveTo(lerp(tip[0], top[0], 0.12), lerp(tip[1], top[1], 0.12)); g.lineTo(top[0], top[1]); g.stroke();
  g.strokeStyle = '#e8c25a'; g.lineWidth = 4.2 * s;
  g.beginPath(); g.moveTo(lerp(tip[0], top[0], 0.86), lerp(tip[1], top[1], 0.86)); g.lineTo(top[0], top[1]); g.stroke();
  g.restore();
}

// The welling in E1. The rig's own `tears` band sits on the lower half of SELF's small eyes and is hidden by the
// smile's raised lower lids, so at phone size it did not read. This overlay (same recipe as s20's drawWetEyes, so the
// welling here foreshadows the narrator's tear there) draws a glossy water line on each lower lid and a bright
// catch-light on the wet iris. No drop falls: the tear is s20's.
function eyeGeom(pose, side) {
  const f = pose.face, turn = clamp(pose.headTurn ?? 0, -1, 1), at = Math.abs(turn);
  const squeeze = side * turn > 0 ? 1 - at * 0.38 : 1 + at * 0.06;
  const rx = SELF_FACE.eyeRx * squeeze, ry = SELF_FACE.eyeRy, cy = SELF_FACE.eyeY;
  const cx = side * SELF_FACE.eyeSpacing * (1 - at * 0.3) + turn * SELF_FACE.eyeSpacing * 0.55;
  const rest = SELF_FACE.restLid, lidU = f.lidU || 0, blink = clamp(f.blink || 0);
  let up = clamp(rest + lidU * (lidU < 0 ? 0.3 : 1) + blink * (1 - (rest + lidU)), -0.25, 1);
  if (lidU < 0) up = clamp(rest + lidU * 0.3 + blink * (1 - rest), -0.25, 1);
  const low = clamp(f.lidL || 0) * (1 - clamp(up, 0, 1) * 0.5);
  const bnd = (dx) => ry * Math.sqrt(clamp(1 - (dx * dx) / (rx * rx)));
  const lidY = (dx) => cy + lerp(bnd(dx) + ry * 0.05, -ry * 0.05 + (dx * dx) / (rx * rx) * ry * 0.25, low * 0.75);
  // SELF's eyes are almond-shaped: their lower edge (face.mjs eyePath) sits well above the ellipse bound the lid formula
  // starts from, so with the lower lid down the water line would float on the cheek. Sample the almond's lower bezier
  // and keep the line on whichever edge is higher (the lid's or the eye's).
  const inner = -side, outer = side, P0 = [inner * rx, -ry * 0.05], P1 = [inner * rx * 0.75, ry * 0.95], P2 = [outer * rx * 0.55, ry * 0.9], P3 = [outer * rx, -ry * 0.12];
  const bez = []; for (let i = 0; i <= 24; i++) { const u = i / 24, v = 1 - u; bez.push([0, 1].map((j) => v * v * v * P0[j] + 3 * v * v * u * P1[j] + 3 * v * u * u * P2[j] + u * u * u * P3[j])); }
  bez.sort((p, q) => p[0] - q[0]);
  const almond = (dx) => { let i = 1; while (i < bez.length - 1 && bez[i][0] < dx) i++; const [a0, b0] = [bez[i - 1], bez[i]]; return lerp(a0[1], b0[1], clamp((dx - a0[0]) / ((b0[0] - a0[0]) || 1))); };
  const lowY = (dx) => Math.min(lidY(dx), cy + almond(dx));
  const upY = (dx) => {
    const k = clamp(up, -0.25, 1), tilt = f.lidTilt || 0, outer = (dx * side) / rx;
    return cy + lerp(-bnd(dx) - ry * 0.05, ry * 0.3 - (dx * dx) / (rx * rx) * ry * 0.1, Math.max(0, k)) + (k < 0 ? k * ry * 0.35 : 0) +
      tilt * outer * ry * 0.38 * Math.min(1, Math.max(0, k) + 0.6);
  };
  const ix = cx + clamp(f.lookX || 0, -1, 1) * rx * 0.42, iy = cy + clamp(f.lookY || 0, -1, 1) * ry * 0.36 + ry * 0.04;
  return { cx, cy, rx, ry, up, lowY, upY, ix, iy, irisR: rx * 0.6 };
}
function drawWetEyes(g, C, pose, well) {
  if (well <= 0.01) return;
  const a = selfPoseAnchors(C.x, C.y, C.s, pose);
  const hc = a.headCenter, ht = a.headTop;
  g.save();
  g.translate(hc[0], hc[1]); g.rotate(Math.atan2(ht[0] - hc[0], -(ht[1] - hc[1]))); g.scale(C.s, C.s);
  g.lineCap = 'round'; g.lineJoin = 'round';
  for (const side of [-1, 1]) {
    const e = eyeGeom(pose, side);
    const open = clamp(1 - e.up) / 0.85;
    const line = (from, to, off) => {
      g.beginPath();
      for (let i = 0; i <= 10; i++) {
        const dx = lerp(from, to, i / 10) * e.rx, y = e.lowY(dx) + off;
        if (i === 0) g.moveTo(e.cx + dx, y); else g.lineTo(e.cx + dx, y);
      }
    };
    // water pooled on the lower lid: a glossy band just above the lash line, a white specular stripe on it
    g.strokeStyle = `rgba(196,230,255,${0.62 * well * open})`; g.lineWidth = 2.8;
    line(-0.8, 0.8, -1.1); g.stroke();
    g.strokeStyle = `rgba(255,255,255,${0.92 * well * open})`; g.lineWidth = 1.3;
    line(side > 0 ? -0.5 : -0.1, side > 0 ? 0.1 : 0.5, -1.5); g.stroke();
    // the bright catch-light on the wet iris, only where the upper lid leaves the iris open
    const hx = e.ix - e.irisR * 0.36, hy = e.iy - e.irisR * 0.38;
    const vis = clamp((hy - e.upY(hx - e.cx) - 1.5) / 2.5) * open;
    if (vis > 0.01) {
      const ka = well * vis;
      const gl = g.createRadialGradient(hx, hy, 0, hx, hy, e.irisR * 0.62);
      gl.addColorStop(0, `rgba(255,255,255,${0.5 * ka})`); gl.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = gl; g.fillRect(hx - e.irisR, hy - e.irisR, e.irisR * 2, e.irisR * 2);
      g.fillStyle = `rgba(255,255,255,${ka})`;
      g.beginPath(); g.arc(hx, hy, e.irisR * 0.27, 0, Math.PI * 2); g.fill();
      g.fillStyle = `rgba(255,255,255,${0.8 * ka})`;
      g.beginPath(); g.arc(e.ix + e.irisR * 0.34, e.iy + e.irisR * 0.3, e.irisR * 0.12, 0, Math.PI * 2); g.fill();
    }
  }
  g.restore();
}

// ---------------------------------------------------------------- shots
function shotOf(t, S) {
  if (t < S.T('s17b02')) return 'A';     // alarm corridor: Fear passes under the alarm
  if (t < S.T('s17b03')) return 'B';     // front: CEO at the console, Fear pops up
  if (t < S.T('s17b04')) return 'C';     // close on CEO: "Fear."
  if (t < S.T('s17b05')) return 'D';     // close on Fear: "Can I help?"
  if (t < S.T(E1_END)) return 'E1';       // held close on the CEO: the answer is on their face
  return 'E';                             // console: everyone makes room
}

export function render(g, t, S) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#0a0816'; g.fillRect(0, 0, 720, 1280); g.restore();
  const shot = shotOf(t, S);
  if (shot === 'A') renderAlarm(g, t, S);
  else renderFront(g, t, S, shot);
}

// ================================================================= A · the alarm corridor
function fearCorridor(t, S) {
  // trot in from frame-left (≈640 px/s), ease to a stop under the handle, then walk on, lighter
  const t0 = S.T('scene.start+0.3'), tStop = S.T('s17b01+1.0'), tOn = S.T('s17b01+1.95');
  const v = 640, d = 0.4, t1 = tStop - d;
  const x1 = -60 + v * (t1 - t0), xStop = x1 + v * d / 2;
  let x;
  if (t < t1) x = -60 + v * (t - t0);
  else if (t < tStop) { const u = t - t1; x = x1 + v * (u - u * u / (2 * d)); }
  else x = xStop;
  if (t > tOn) { const u = t - tOn, a = 0.35, v2 = 300; x = xStop + (u < a ? v2 * u * u / (2 * a) : v2 * (a / 2 + (u - a))); }
  return { x, moving: t > t0 && (t < tStop - 0.03 || t > tOn + 0.03) };
}

function renderAlarm(g, t, S) {
  const st = { t, alarm: 0, alarmPulled: 0, lightsDim: 0.1, mist: 0.3 };
  const k = ease.inOut(seg(t, S.T('scene.start+0.3'), S.T('s17b02')));
  g.save();
  applyCamera(g, cam(t, { x: lerp(380, 560, k), y: 960, zoom: 1.0 }, 2));
  drawHQ(g, 'alarm', st);
  const [, fy, fs] = AA.fearAtAlarm;
  const F = fearCorridor(t, S);
  if (t >= S.T('scene.start+0.3') && F.x < 1300) {
    const gx = fbm(t * 0.5, 71) * 0.06;
    // the handle (692,1089) sits at Fear's chin height, just right of its head when it stops at x≈548: the eyes
    // go right and a touch down to it (the bell above is not what tempts it)
    const look = S.k(t, [['s17b01+0.75', 0], ['s17b01+0.95', 1], ['s17b01+1.48', 1], ['s17b01+1.7', 0.2], ['s17b01+2.0', 0]]);
    const head = S.k(t, [['s17b01+0.85', 0], ['s17b01+1.15', 1], ['s17b01+1.8', 1], ['s17b01+2.1', 0]]);
    const lift = S.k(t, [['s17b01+1.25', 0], ['s17b01+1.5', 1, 'outCubic'], ['s17b01+1.8', 1], ['s17b01+2.0', 0]]);
    const breath = S.k(t, [['s17b01+1.35', 0], ['s17b01+1.65', 1], ['s17b01+2.0', 0]]);
    const release = S.k(t, [['s17b01+1.75', 0], ['s17b01+2.15', 1]]);               // a little lighter
    const ph = (F.x / 160) * Math.PI;   // cadence follows speed: ~4 steps/s at the trot
    const pose = {
      t, facing: 1, tremble: 0,
      walk: F.moving ? { phase: ph } : undefined,
      headTilt: 0.05 * head - 0.06 * breath, headTurn: 0.22 * head, headDY: 2 * head - 4 * breath - 4 * release * Math.abs(Math.sin(ph)),
      breathe: 1 + 1.5 * breath,
      face: {
        lookX: lerp(0.15, 0.85, look) + gx, lookY: lerp(-0.05, 0.18, look),
        // worried pull at the handle; the brows let go during the closed-eyed breath (the choice is made)
        browIn: 0.15 + 0.5 * look * (1 - release) * (1 - 0.7 * breath) + 0.1 * breath, browUp: 0.15 * look + 0.15 * release + 0.12 * breath,
        lidU: -0.1 * look, smile: lerp(0.15, -0.05, look * (1 - release)) + 0.12 * breath + 0.25 * release, pressed: 0.2 * breath,
        blush: 0.15, noAutoBlink: t > S.T('s17b01+1.2') && t < S.T('s17b01+2.3'),
        blink: S.k(t, [['s17b01+1.5', 0], ['s17b01+1.66', 1], ['s17b01+1.84', 1], ['s17b01+1.98', 0]]),   // a breath, eyes closed: the choice
      },
      armR: lift > 0.01 ? { target: [lerp(40, 58, lift), lerp(-78, -102, lift)], bend: -1, hand: 'open' } : 'rest',
      armL: 'rest',
    };
    if (F.moving) {
      const sw = Math.sin(ph) * 12;
      pose.armL = { target: [-38 - sw, -84], bend: 1, hand: 'open' };
      if (lift <= 0.01) pose.armR = { target: [38 - sw, -84], bend: -1, hand: 'open' };
    }
    drawFear(g, F.x, fy - (F.moving ? Math.abs(Math.sin(ph)) * 6 : 0), fs, pose);
  }
  drawHQForeground(g, 'alarm', st);
  g.restore();
  grade(g, 0, 0.4);
  vignette(g, 0.35);
}

// ================================================================= B–E · the console (front view)
function frontCam(t, S, shot) {
  if (shot === 'B') return cam(t, { x: 500, y: 1150, zoom: 1.32 + 0.04 * seg(t, S.T('s17b02'), S.T('s17b03')) }, 2);
  // C / E1: the CEO's face at ≈ 35 % of the height, Fear (on tiptoe, bottom right) with its eyes at ≈ 70 %, out of the
  // bottom 15 % caption band (the console rim may sit in it)
  if (shot === 'C') { const z = 2.4 + 0.08 * seg(t, S.T('s17b03'), S.T('s17b04')); return cam(t, { x: 452, y: 1181 - 262 / z, zoom: z }, 1.6); }
  // E1: back on the CEO (a touch closer) for the answer to "Can I help?", held 2.55 s: eyes well, the smile breaks,
  // a laugh-breath, one nod; a slow push
  // (zoom 2.8 → 3.0: the CEO's face ≈ 43 % of the frame width, eyes at ≈ 30 %; Fear's eyes held at ≈ 72 %, its hands
  // above the 85 % line; from 2.78 up the robe hem / cage feet are above the frame, so they are not drawn: ≈ 2 ms saved)
  if (shot === 'E1') { const k = ease.inOut(seg(t, S.T('s17b05'), S.T(E1_END))), z = lerp(2.8, 3.0, k); return cam(t, { x: lerp(464, 470, k), y: 1181 - 280 / z, zoom: z }, 1.4); }
  if (shot === 'D') return cam(t, { x: 528, y: 1166, zoom: 2.85 + 0.06 * seg(t, S.T('s17b04'), S.T('s17b05')) }, 1.6);
  // wide at the console: all five in frame as they make room; then a slow push toward Fear for its first button
  const k = ease.inOut(seg(t, S.T(BIZ(2.0)), S.T('scene.end+0.9')));
  return cam(t, { x: 450, y: lerp(1110, 1150, k), zoom: lerp(1.15, 1.42, k) }, 2.2);
}

// Fear behind the console: scurries in along the rim (only the tuft shows), pops up on tiptoe, then climbs its stool
function fearConsole(t, S) {
  const run = seg(t, S.T('s17b02-0.05'), S.T('s17b02+0.6'));
  const pop = seg(t, S.T('s17b02+0.55'), S.T('s17b02+1.0'));
  let x = lerp(760, FEAR_TIPTOE_F[0], ease.out(run));
  let y = lerp(1428, FEAR_TIPTOE_F[1], ease.outBack(pop));
  let s = FEAR_TIPTOE_F[2];
  // b05: down off tiptoe, step across, up onto the stool (consoleFear 450,1328)
  const across = seg(t, S.T(BIZ(1.25)), S.T(BIZ(2.0)));
  const climb = seg(t, S.T(BIZ(1.95)), S.T(BIZ(2.6)));
  if (across > 0) {
    x = lerp(FEAR_TIPTOE_F[0], FA.consoleFear[0], ease.inOut(across));
    y = FEAR_TIPTOE_F[1] + 24 * Math.sin(Math.PI * across) * 0.6 + 14 * ease.inOut(across);
  }
  if (climb > 0) {
    const base = FEAR_TIPTOE_F[1] + 14;
    y = lerp(base, FA.consoleFear[1], ease.outBack(climb)) - 10 * Math.sin(Math.PI * climb);
  }
  return { x, y, s, run, pop, across, climb, walking: (run > 0 && run < 1) || (across > 0 && across < 1) };
}

function fearPoseFront(t, S, shot, F) {
  const gx = fbm(t * 0.45, 81) * 0.06, gy = fbm(t * 0.4, 83) * 0.05;
  // eyeline to the CEO (up-left) and to the buttons (down)
  const toCEO = { lookX: -0.48, lookY: -0.78 };
  let face = { ...toCEO, browIn: 0.45, browUp: 0.25, lidU: -0.05, smile: 0.12, blush: 0.3, sparkle: 0.15 };
  let pose = { t, facing: 1, tremble: 0, headTilt: -0.1, headTurn: -0.15 };
  // shy clasped hands in front of the scarf
  pose.armL = { target: [-7, -141], bend: -1, front: true, hand: 'fist' };
  pose.armR = { target: [7, -138], bend: 1, front: true, hand: 'fist' };
  if (shot === 'B') {
    if (F.run < 1) { face = { ...face, lookX: -0.6, lookY: 0, browIn: 0.2, browUp: 0 }; pose.headTurn = -0.3; pose.walk = { phase: (760 - F.x) / 30 * Math.PI }; }
    const shy = seg(t, S.T('s17b02+0.9'), S.T('s17b02+1.3'));
    face.smile = lerp(0.05, 0.18, shy);
    face.blink = blinkAt(t, S.T('s17b02+1.18'), 0.18);
  }
  if (shot === 'C') {
    // at the frame bottom: the tuft lifts, a small nod
    const nod = S.k(t, [['s17b03+0.95', 0], ['s17b03+1.12', 1], ['s17b03+1.35', 0]]);
    const lift = S.k(t, [['s17b03+0.3', 0], ['s17b03+0.45', 1], ['s17b03+0.9', 0]]);
    // gathering courage before asking: the eyes drop to the glowing buttons and it takes a breath (D opens on that look)
    const down = S.k(t, [['s17b04-0.42', 0], ['s17b04-0.24', 1]]);
    const inhale = S.k(t, [['s17b04-0.4', 0], ['s17b04-0.1', 1]]);
    pose.headDY = -6 * lift + 6 * nod - 3 * inhale + 3 * down;
    pose.breathe = 1 + 1.2 * inhale;
    face.browUp = 0.25 + 0.25 * lift + 0.1 * down;
    face.lookX = lerp(face.lookX, 0.15, down); face.lookY = lerp(face.lookY, 0.62, down);
  }
  if (shot === 'D') {
    // looks at the glowing buttons, then up at Consciousness; brows hopeful; holds its breath after asking
    // "Can I" to the buttons, the eyes lift to Consciousness just ahead of "help?" (+0.40)
    const up = S.k(t, [['s17b04+0.26', 0], ['s17b04+0.46', 1, 'outCubic']]);
    const hold = S.k(t, [['s17b04.end+0.05', 0], ['s17b04.end+0.3', 1]]);
    face = {
      lookX: lerp(0.15, -0.5, up) + gx, lookY: lerp(0.62, -0.8, up) + gy,
      browIn: 0.55 + 0.1 * hold, browUp: lerp(0.35, 0.45, up), lidU: lerp(-0.12, -0.12, up), lidTilt: 0.1,
      smile: 0.08 - 0.05 * hold, pressed: 0.55 * hold, blush: 0.32, sparkle: 0.6, pupil: 1.2,
    };
    face = withSpeech(face, S.lip('FEAR', t));
    pose.headTilt = lerp(0.02, -0.12, up); pose.headDY = 5 * (1 - up);
    pose.breathe = lerp(1, 0.15, hold);
  }
  if (shot === 'E1') {
    // at the bottom of the CEO's close: still holding its breath, then it lets it out as the smile breaks above it;
    // at the CEO's nod its eyes light up and it bobs on its toes
    const relief = S.k(t, [['s17b05+0.55', 0], ['s17b05+0.9', 1]]);
    const sm = S.k(t, [['s17b05+0.7', 0], ['s17b05+1.4', 1, 'sine']]);
    const lit = S.k(t, [['s17b05+1.75', 0], ['s17b05+2.1', 1, 'outCubic']]);
    const bob = Math.sin(Math.PI * seg(t, S.T('s17b05+1.95'), S.T('s17b05+2.3')));
    face = { lookX: -0.48, lookY: -0.8, browIn: lerp(0.65, 0.3, sm) - 0.15 * lit, browUp: lerp(0.45, 0.3, sm) + 0.25 * lit, lidU: -0.12 - 0.1 * lit,
      lidL: 0.22 * sm, smile: lerp(0.03, 0.5, sm) + 0.15 * lit, open: 0.1 * lit, pressed: 0.55 * (1 - relief), blush: 0.32 + 0.15 * sm,
      sparkle: 0.5 + 0.3 * lit, pupil: 1.2 + 0.1 * lit };
    pose.headTilt = -0.12; pose.breathe = lerp(0.15, 1.3, relief);
    pose.headDY = 6 * relief * (1 - relief) - 6 * bob;
  }
  if (shot === 'E') {
    const shyL = S.k(t, [[BIZ(2.55), 0], [BIZ(2.65), 1], [BIZ(2.75), 1], [BIZ(2.85), 0]]);   // glance at ANGER
    const shyR = S.k(t, [[BIZ(2.7), 0], [BIZ(2.8), 1], [BIZ(2.88), 1], [BIZ(2.96), 0]]);    // and at SADNESS
    const reachB = S.k(t, [[BIZ(2.7), 0], [BIZ(2.9), 1, 'outCubic']]);                 // hand to the button
    const press = S.k(t, [[BIZ(2.92), 0], [BIZ(3.0), 1], [BIZ(3.3), 1], [BIZ(3.5), 0.35]]);
    const lit = S.k(t, [[BIZ(3.0), 0], [BIZ(3.25), 1, 'outCubic']]);
    const climbing = F.across > 0 && F.climb < 1;
    face = {
      lookX: climbing ? -0.25 : -0.45 * shyL + 0.55 * shyR, lookY: climbing ? 0.45 : lerp(0.1, 0.6, Math.max(reachB * (1 - lit), press * 0.6)) - 0.1 * lit,
      browIn: 0.35 * (1 - lit), browUp: 0.15 + 0.45 * lit, lidU: -0.25 * lit, pupil: 1 + 0.35 * lit,
      smile: 0.2 + 0.5 * lit + (climbing ? 0.1 : 0), open: 0.16 * lit, lidL: 0.15 * lit, blush: 0.35 + 0.15 * lit, sparkle: 0.2 + 0.8 * lit,
    };
    // proud little climb (look at the step), shy glances, then the careful press
    if (climbing) { pose.headTilt = 0.08; pose.walk = { phase: F.across * 2 * Math.PI + F.climb * Math.PI }; }
    if (F.across > 0 && F.climb < 0.6) {
      pose.armL = { target: [-40, -96], bend: 1, hand: 'open' };
      pose.armR = { target: [40, -96], bend: -1, hand: 'open' };
    }
    if (F.climb >= 0.6) {
      pose.armL = { target: [-9, -140], bend: -1, front: true, hand: 'fist' };
      pose.armR = { target: [lerp(9, 20, reachB), lerp(-138, -114, reachB) + 12 * press], bend: 1, front: true, hand: 'open' };
    }
    pose.headTurn = -0.12 * shyL + 0.12 * shyR;
    pose.headDY = -3 * lit;
  }
  pose.face = { ...face, lookX: (face.lookX || 0) + (shot === 'D' ? 0 : gx), lookY: (face.lookY || 0) + (shot === 'D' ? 0 : gy) };
  return pose;
}

// --- the CEO at consoleMid: writing → senses → sees Fear → "Fear." → the glance back → welling → steps aside
function ceoState(t, S, shot) {
  const step = seg(t, S.T(BIZ(1.2)), S.T(BIZ(2.25)));
  const ks = ease.inOut(step);
  const x = lerp(450, CEO_ASIDE_F[0], ks), y = lerp(ROW_Y, CEO_ASIDE_F[1], ks);
  const s = hqScaleAt('front', y);
  return { x, y, s, step };
}
function ceoPose(t, S, shot, C) {
  const gx = fbm(t * 0.4, 91) * 0.05, gy = fbm(t * 0.36, 93) * 0.04;
  const write = 1 - S.k(t, [['s17b02+0.45', 0], ['s17b02+0.6', 1]]);            // the pen stops
  const senses = S.k(t, [['s17b02+0.45', 0], ['s17b02+0.7', 1]]);              // eyes slide down-right
  const sees = S.k(t, [['s17b02+1.0', 0], ['s17b02+1.2', 1, 'outCubic']]);      // eyes widen, breath catches
  const glance = S.k(t, [['s17b03+0.85', 0], ['s17b03+0.98', 1], ['s17b03+1.32', 1], ['s17b03+1.48', 0]]);
  const glanceHead = S.k(t, [['s17b03+0.9', 0], ['s17b03+1.05', 1], ['s17b03+1.32', 1], ['s17b03+1.55', 0]]);
  const soften = S.k(t, [['s17b03+1.45', 0], ['s17b03+1.9', 1]]);
  // b05 opens on the CEO (E1, held until +2.55): the eyes well up on the lower lids, the smile breaks across the
  // whole face (open, teeth, cheeks up), a laugh-breath out (two little pulses), one nod (no words), the clipboard
  // goes down behind the rim; then (wide) they step aside
  const well = S.k(t, [['s17b04+0.6', 0], ['s17b05+0.1', 0.45], ['s17b05+0.75', 1, 'sine']]);   // welling leads the smile
  const smile = S.k(t, [['s17b05+0.3', 0], ['s17b05+1.15', 1, 'sine']]);
  const laugh = S.k(t, [['s17b05+1.02', 0], ['s17b05+1.12', 1], ['s17b05+1.3', 0.35], ['s17b05+1.4', 0.8], ['s17b05+1.75', 0]]);
  const nod = S.k(t, [['s17b05+1.75', 0], ['s17b05+1.97', 1, 'inOut'], ['s17b05+2.25', 0, 'inOut']]);
  const putDown = S.k(t, [['s17b05+1.95', 0], ['s17b05+2.5', 1]]);

  // gaze: clipboard (down-left) → Fear (down-right) → over the shoulder (back of the mind) → Fear
  let lookX = lerp(-0.1, 0.5, senses), lookY = lerp(0.5, 0.62, senses);
  lookX = lerp(lookX, -0.8, glance); lookY = lerp(lookY, -0.2, glance);
  if (shot === 'E' || shot === 'E1') { lookX = lerp(0.5, -0.45, ease.inOut(seg(t, S.T(BIZ(1.7)), S.T(BIZ(2.5))))); lookY = lerp(0.62, 0.68, C.step); }
  let face = { ...SELF_EXPR.focused, lookX: lookX + gx, lookY: lookY + gy };
  face = { ...face, lidU: lerp(0.3, 0.05, senses) - 0.25 * sees, browIn: lerp(-0.15, 0.25, senses) + 0.15 * soften, browUp: 0.55 * sees * (1 - 0.4 * soften) + 0.15 * soften,
    browSquish: 0.35 * (1 - senses), open: 0.16 * sees * (1 - soften), pupil: 1 + 0.15 * sees, smile: -0.05 + 0.2 * soften, lidL: 0.15 * soften };
  face.browIn += 0.12 * soften;                                                  // the soft, tender inner lift
  // stunned: no blink from the moment it sees Fear until the glance back (which carries the blink)
  face.noAutoBlink = t > S.T('s17b02+0.95') && t < S.T('s17b03+1.3');
  // (no slow blink as the answer lands — the eyes stay open on Fear while they fill; one quick blink after the nod)
  // (the post-nod blink sits at the bottom of the nod, so E1 ends on open eyes, not mid-blink at the cut)
  face.blink = blinkAt(t, S.T('s17b03+0.9'), 0.2) + blinkAt(t, S.T('s17b05+1.96'), 0.24);
  face = withSpeech(face, S.lip('CONSCIOUSNESS', t));
  if (shot === 'D') { // soft at the frame edge: lips parted, eyes glistening, breath held
    face = { ...face, open: 0.12, tears: 0.45 + 0.2 * well, browIn: 0.45, browUp: 0.3, lookX: 0.45, lookY: 0.7, lidU: 0.05 };
  }
  if (shot === 'E' || shot === 'E1') {
    // tears 0.6 welling on the lower lids; the broad open smile (0.9, lidL 0.4); tender inner brows that stay up
    face = { ...face, tears: 0.6 * well, sparkle: 0.2 + 0.35 * well, browIn: 0.55 - 0.2 * smile, browUp: 0.22 + 0.15 * laugh,
      smile: 0.95 * smile, wide: 0.42 * smile, lidL: 0.4 * smile + 0.15 * laugh, lidU: 0.04 + 0.12 * laugh,
      open: 0.27 * smile + 0.14 * laugh, teeth: 0.8 * smile, blush: 0.35 * smile, pressed: 0, noAutoBlink: shot === 'E1',
      lookY: face.lookY - 0.08 * smile };
  }
  const writeWob = [Math.sin(t * 9) * 2.5 * write, Math.sin(t * 13.7) * 1.5 * write];
  const pose = {
    t, outfit: 'ceo', facing: 1,
    headTurn: lerp(-0.05, 0.22, senses) * (1 - glanceHead) - 0.35 * glanceHead + (shot === 'E' ? -0.32 * ease.inOut(seg(t, S.T(BIZ(1.75)), S.T(BIZ(2.6)))) : 0),
    headTilt: 0.06 * senses + 0.05 * soften + 0.04 * smile, headDY: 4 * senses + 9 * nod - 3 * laugh,
    face, shrug: 0.25 * sees * (1 - soften) + 0.3 * laugh,
  };
  // clipboard in the left hand, pen in the right (both lowered behind the console rim in b05, then put down)
  if (putDown < 1) {
    pose.clipboard = true;
    pose.armL = { preset: 'holdClipboard', target: [-40, lerp(-290, -150, putDown)] };
    pose.armR = { target: [lerp(6, 14, putDown) + writeWob[0], lerp(-300, -160, putDown) + writeWob[1]], bend: 1, front: true, hand: 'grip' };
  } else {
    pose.armL = 'rest'; pose.armR = 'rest';
  }
  if (C.step > 0 && C.step < 1) {
    pose.walk = { phase: (C.x - 450) / (WALK_ADVANCE * C.s) * 2 * Math.PI };
    pose.bodyTurn = 0.35;
  }
  return { pose, pen: putDown < 1 ? { wrist: pose.armR.target, wob: writeWob } : null };
}

function emotionPose(name, t, S, shot) {
  const te = t + OFF[name];
  const gx = fbm(te * 0.4, 21) * 0.06, gy = fbm(te * 0.37, 23) * 0.05;
  const notice = S.k(t, [['s17b02+0.85', 0], ['s17b02+1.2', 1]]);
  const welcome = S.k(t, [['s17b05+0.1', 0], ['s17b05+0.6', 1]]);
  const scoot = ease.inOut(seg(t, S.T(BIZ(1.15)), S.T(BIZ(2.0))));
  const x = lerp(ROW_START[name], ROW_S19[name], scoot);
  const pose = { t: te, armL: 'pressButton', armR: 'pressButton' };
  let face;
  const fearX = shot === 'E' ? lerp(532, 450, seg(t, S.T(BIZ(1.25)), S.T(BIZ(2.0)))) : 532;
  const dir = Math.sign(fearX - x);                                  // which way Fear is
  if (name === 'JOY') {
    // pauses mid-button, glances over: brows up, a hopeful "oh" · b05 scoots, pats the space beside her
    const tap = Math.max(0, Math.sin((t - S.T('s17b02')) * 7)) * 6 * (1 - notice);
    face = { lookX: lerp(0.1, -0.75, notice), lookY: lerp(0.5, 0.25, notice), browUp: 0.55 * notice, open: 0.2 * notice * (1 - welcome), round: 0.7 * notice * (1 - welcome),
      smile: 0.25 * notice + 0.5 * welcome, lidL: 0.3 * welcome, blush: 0.25 * welcome };
    pose.headTurn = -0.3 * notice;
    pose.armR = { preset: 'pressButton', dy: tap };
    const pat = S.k(t, [[BIZ(1.4), 0], [BIZ(1.6), 1], [BIZ(2.5), 1], [BIZ(2.7), 0]]);
    if (pat > 0.01) pose.armL = { preset: 'pressButton', atY: -266, dx: 10, dy: 7 * Math.max(0, Math.sin((t - S.T(BIZ(1.6))) * 11)) * pat };
  } else if (name === 'SADNESS') {
    // stops turning its dial; inner brows lift; the eyes go wet · b05 leans its shoulder against Fear's
    face = { lookX: lerp(0, -0.65, notice), lookY: lerp(0.5, 0.35, notice), browIn: 0.65 * notice, browUp: 0.15 * notice, tears: 0.6 * notice,
      smile: 0.35 * welcome, lidL: 0.2 * welcome, blush: 0.2 * welcome };
    pose.headTurn = -0.25 * notice;
    const lean = S.k(t, [[BIZ(1.95), 0], [BIZ(2.55), 1], ['scene.end', 1]]);
    pose.lean = -0.07 * lean;
    pose.headTilt = -0.08 * lean;
    if (shot === 'E') { face.lookX = -0.6; face.lookY = 0.45; }
  } else if (name === 'ANGER') {
    // freezes with a hand on a lever, eyes sliding sideways; the brows ease a hair · b05 slides a lever over
    const slide = S.k(t, [['s17b02+0.65', 0], ['s17b02+0.9', 1]]);
    face = { lookX: lerp(0, 0.75, slide), lookY: 0.35, browIn: -0.3 + 0.18 * notice, pressed: 0.3 * (1 - welcome), smile: 0.3 * S.k(t, [[BIZ(1.9), 0], [BIZ(2.3), 1]]) };
    if (shot === 'E') { face.lookX = 0.05; face.lookY = 0.5; }          // "without looking"
    pose.noBase = true; face.browIn -= 0.3;
    const lever = S.k(t, [[BIZ(1.35), 0], [BIZ(1.95), 1]]);
    pose.armR = { preset: 'pressButton', dx: 22 * lever, dy: 3 };
  } else {
    // CALM: already smiling, eyelids at half; the long arm drifts toward a step-stool under the console
    face = { lidU: 0.15, smile: 0.35 + 0.1 * welcome, lookX: lerp(0.3, 0.7, notice), lookY: 0.45, lidL: 0.15 };
    const reach = S.k(t, [['s17b02+1.0', 0], ['s17b02+1.6', 0.35], [BIZ(0.6), 0.4], [BIZ(1.05), 1], [BIZ(1.6), 1], [BIZ(1.95), 0]]);
    pose.armR = { preset: 'pressButton', dx: 10 + 30 * reach, dy: 40 * reach };
    pose.lean = 0.05 * reach;
    face.blink = blinkAt(t, S.T(BIZ(2.3)), 0.45);
  }
  pose.face = { ...face, lookX: face.lookX + gx, lookY: face.lookY + gy };
  return { x, pose };
}

// soft, out-of-focus pass (rendered small and scaled up) for the CEO and SADNESS at the edges of Fear's close
let SOFT = null;
function softLayer(g, camera, draw) {
  const R = 4;
  if (!SOFT) SOFT = createCanvas(Math.ceil(720 / R), Math.ceil(1280 / R));
  const c = SOFT.getContext('2d');
  c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, SOFT.width, SOFT.height);
  c.setTransform(1 / R, 0, 0, 1 / R, 0, 0);
  c.save(); applyCamera(c, camera); draw(c); c.restore();
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.imageSmoothingEnabled = true;
  g.globalAlpha = 0.93;
  g.drawImage(SOFT, 0, 0, SOFT.width, SOFT.height, 0, 0, SOFT.width * R, SOFT.height * R); g.restore();
}

function renderFront(g, t, S, shot) {
  const pressGlow = S.k(t, [[BIZ(3.0), 0], [BIZ(3.2), 1, 'outCubic']]);
  const st = { t, lightsDim: 0.1, consoleGlow: 1.1 + 0.1 * pressGlow, mist: 0.3, voidShadow: 0.1, screenMode: 'room' };
  const camera = frontCam(t, S, shot);
  const F = fearConsole(t, S);
  const C = ceoState(t, S, shot);
  const { pose: cp, pen } = ceoPose(t, S, shot, C);
  const fp = fearPoseFront(t, S, shot, F);
  const ems = Object.fromEntries(['CALM', 'ANGER', 'SADNESS', 'JOY'].map((n) => [n, emotionPose(n, t, S, shot)]));

  g.save();
  applyCamera(g, camera);
  drawHQ(g, 'front', st);
  // the back of the mind peeks in at the top (under the TOP SHADE) — skipped when the robe hem / cage feet (y ≤ 846)
  // are above the frame (E1's tighter close): saves ≈ 2.5 ms
  if (shot !== 'D' && camera.y - 640 / camera.zoom < 850) {
    // only the lower robe shows (the hood, y≈272, is above every framing here), so its cosmos is not drawn
    drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0.5, cosmos: 0, shadow: false });
    drawCage(g, ...CAGE_F, { t, door: 0.9, locked: 0 });
  }
  // cull characters outside the frame; clip everything that stands behind the console to above its hull
  const vw = 360 / camera.zoom + 12, vh = 640 / camera.zoom + 40;
  const inView = (x, top, bottom, hw) => x + hw > camera.x - vw && x - hw < camera.x + vw && bottom > camera.y - vh && top < camera.y + vh;
  const behindConsole = (c, fn) => { c.save(); c.beginPath(); c.rect(-1e4, -1e4, 2e4, 1e4 + 1290); c.clip(); fn(); c.restore(); };
  const drawCEO = (c) => {
    if (!inView(C.x, C.y - 610 * C.s, C.y, 110 * C.s)) return;
    behindConsole(c, () => { drawSelf(c, C.x, C.y, C.s, cp); if (pen) drawPen(c, C.x, C.y, C.s, 1, pen.wrist, pen.wob); });
    if (shot === 'E1') drawWetEyes(c, C, cp, clamp((cp.face.tears || 0) / 0.6));
  };
  const drawEm = (c, n) => {
    if (!inView(ems[n].x, ROW_Y - 540 * ROW_S, ROW_Y, 100 * ROW_S)) return;   // half-width ≤ 94 local (+ arms in)
    behindConsole(c, () => drawEmotion(c, n, ems[n].x, ROW_Y, ROW_S, ems[n].pose));
  };
  if (shot === 'D') {
    g.restore();
    softLayer(g, camera, (c) => { drawEm(c, 'SADNESS'); drawCEO(c); });
    g.save(); applyCamera(g, camera);
  } else {
    // the CEO stands at the row (b02–b04) and then steps back behind SADNESS/JOY: always behind the emotions
    drawCEO(g);
    for (const n of ['CALM', 'ANGER', 'SADNESS', 'JOY']) drawEm(g, n);
  }
  if (shot !== 'B' || t >= S.T('s17b02-0.05')) behindConsole(g, () => drawFear(g, F.x, F.y, F.s, fp));
  // the console light on Fear's face (its first button) and the general amber spill from below
  const fx = F.x, fy = F.y - 200 * F.s;
  buttonLight(g, fx + 10, fy + 70, 130, (shot === 'D' ? 0.35 : 0.15) + 1.1 * pressGlow);
  drawHQForeground(g, 'front', st);
  if (pressGlow > 0) { buttonLight(g, fx + 16, 1250, 70, 1.2 * pressGlow); buttonLight(g, fx + 16, 1250, 26, 1.5 * pressGlow); }
  g.restore();
  topShade(g);
  grade(g, 0, 0.4);
  vignette(g, 0.35);
}
