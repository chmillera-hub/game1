// s19 · the_scene_changed · front view · dissolve in (from s18) and out (to s20, through the screen bloom)
// The new normal: the five at the console, Fear on its stool between ANGER and SADNESS; the Void in the
// back, no longer a threat (faint stars in its hood); the rusted cage a speck at its feet.
//   A  S.start → s19b02   warm medium along the row (TOP SHADE): Fear's concentrated press (tongue tip),
//                          lights up, glances at JOY, proud wiggle; SADNESS rests its head against Fear;
//                          JOY leans in past SADNESS beaming → Fear's silent giggle (hand over the mouth);
//                          ANGER presses its lips, a smile leaks out of one corner anyway.
//   B  s19b02 → end       Consciousness's POV from the screen ('establish' → 'wide'): Fear glances back at the
//                          Void once, small smile; CALM reaches across ANGER (who makes room) and points at the
//                          next button (it glows), Fear's eyes follow, it presses; Fear leans its head on SADNESS
//                          (CALM's slow blink); a star twinkles in the hood; JOY looks up at us.
//   Work faces look down at the console with the lids following the gaze, so every look-up reads.
//   Beat 23 "pressing the buttons": in A the presses are staged over the rim (pressMove) — Fear (+0.3), JOY (+0.85),
//   ANGER (+4.0), JOY (+4.38) — each with its station-coloured light (stationPulse) and soft console_beeps.
import { W, H, TAU, clamp, lerp, ease, env, kf, blinkAt, applyCamera, drift, vignette, fbm } from '../engine.mjs';
import { EXPR, makeExpr } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawEmotion } from '../chars/emotions.mjs';
import { drawVoid, voidRig } from '../chars/void.mjs';
import { drawCage, CAGE_PRESETS } from '../sets/props.mjs';
import { drawHQ, drawHQForeground, HQ_PRESETS, HQ_STATIONS } from '../sets/hq.mjs';

export const id = 's19';

// --- staging constants (data/staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const COSMOS_RESIDUE = 0.5;
const CAGE_F = [302, 846, 0.3];
const ROW_S19 = { CALM: 205, ANGER: 330, FEAR: 450, SADNESS: 570, JOY: 695 };
const ROW_Y = 1384, FEAR_Y = 1328, SC = 0.799;
// idle-life time offsets (§5.11)
const TOFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 };

export const sfx = [
  // Fear's concentrated press lights its button (blips start 0.02 into the file)
  { at: 's19b01+0.30', name: 'console_beeps', gain: -21 },
  // JOY's press, right after Fear's (gold button, blips a little softer and farther)
  { at: 's19b01+0.83', name: 'console_beeps', gain: -28 },
  // SADNESS settles its head against Fear / JOY leans in (soft fabric)
  { at: 's19b01+1.45', name: 'cloth_rustle', gain: -20 },
  // back to work: ANGER's firm press, then JOY's
  { at: 's19b01+3.98', name: 'console_beeps', gain: -26 },
  { at: 's19b01+4.36', name: 'console_beeps', gain: -30 },
  // Fear's first press in the POV shot (fearPress bump at s19b02+2.33; same action, same sound as the second)
  { at: 's19b02+2.31', name: 'console_beeps', gain: -27 },
  // the next button, pointed out by CALM (POV, farther away: quieter)
  { at: 's19b03+1.08', name: 'console_beeps', gain: -25 },
  // a single star twinkles in the hood
  { at: 's19b03+1.48', name: 'twinkle', gain: -18 },
];

function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, W, H); }
  g.restore();
}

// ---------------------------------------------------------------- small helpers
/** sum of short 0→1→0 bumps (taps / presses), `at` absolute seconds */
function bumps(t, ats, up = 0.09, down = 0.2) {
  let v = 0;
  for (const a of ats) v = Math.max(v, env(t, a, up, 0.03, down));
  return v;
}
/** smooth window 0→1→0 with eased edges (absolute seconds) */
const win = (t, a, b, c, d) => (t <= a || t >= d ? 0 : t < b ? ease.sine((t - a) / (b - a)) : t <= c ? 1 : 1 - ease.sine((t - c) / (d - c)));

// ---- presses that READ in the front view (beat 23: "my emotions pressing the buttons on the console"). The buttons sit
// on the console top behind the rim, so a press is staged as: the hand rises over the rim (fingertip down), dips behind
// it onto the button at `a` (absolute s), rests a beat and settles back to its working height; the button's light
// answers in the station colour on the rim and from below on the operator's face (stationPulse).
function pressMove(t, a, base, peak) {
  return {
    y: kf(t, [[a - 0.42, base], [a - 0.14, peak, 'out'], [a, base + 12, 'in'], [a + 0.22, base + 12], [a + 0.62, base, 'sine']]),
    pulse: env(t, a - 0.03, 0.07, 0.14, 0.8),
  };
}
const STATION_RGB = { JOY: '255,204,80', SADNESS: '110,175,255', ANGER: '255,118,88', CALM: '110,228,165' };
const rimY = (x) => 1247 + ((x - 450) / 450) ** 2 * 21;
/** a button lighting up behind the rim at world x: an uplight in the station colour on the operator's chest and face, the
 *  rim tinted where the light spills over it, and a small hot core on the edge */
function stationPulse(g, x, rgb, k, reach = 1) {
  if (k <= 0.01) return;
  const y = rimY(x), R = 200 * reach;
  g.save();
  g.translate(x, y + 4); g.scale(0.72, 1);
  g.globalCompositeOperation = 'screen';
  let gr = g.createRadialGradient(0, 0, 0, 0, 0, R);
  gr.addColorStop(0, `rgba(${rgb},${0.8 * k})`); gr.addColorStop(0.45, `rgba(${rgb},${0.38 * k})`); gr.addColorStop(1, `rgba(${rgb},0)`);
  g.fillStyle = gr; g.fillRect(-R, -R, 2 * R, R + 6);
  g.restore();
  g.save();
  gr = g.createRadialGradient(x, y, 0, x, y, 78);
  gr.addColorStop(0, `rgba(${rgb},${0.95 * k})`); gr.addColorStop(0.5, `rgba(${rgb},${0.5 * k})`); gr.addColorStop(1, `rgba(${rgb},0)`);
  g.fillStyle = gr;
  g.beginPath(); g.ellipse(x, y + 3, 78, 17, 0, 0, TAU); g.fill();
  g.globalCompositeOperation = 'lighter';
  g.fillStyle = `rgba(255,248,225,${0.45 * k})`;
  g.beginPath(); g.ellipse(x, y + 1, 16, 3, 0, 0, TAU); g.fill();
  g.restore();
}

/** where Fear's mouth is in world coords (mirrors fear.mjs: neck → head tilt → face → mouth; lean about the feet) */
function fearMouth(x, y, s, pose) {
  const br = Math.sin(pose.t * TAU * 0.28) * (pose.breathe ?? 1);
  const crouch = pose.crouch || 0;
  const neck = [pose.headDX || 0, -148 + crouch * 20 + br * 1.2 + (pose.headDY || 0)];
  const ht = pose.headTilt || 0, mx = (pose.headTurn || 0) * 32 * 0.45;
  const m = [neck[0] + mx * Math.cos(ht) - (-20) * Math.sin(ht), neck[1] + mx * Math.sin(ht) + (-20) * Math.cos(ht)];
  const L = pose.lean || 0;
  return [x + s * (m[0] * Math.cos(L) - m[1] * Math.sin(L)), y + s * (m[0] * Math.sin(L) + m[1] * Math.cos(L)), ht + L];
}
/** Fear's tongue tip poking out of the right mouth corner (concentration) — no face parameter exists for it */
function tongueTip(g, x, y, s, rot, k) {
  if (k <= 0.02) return;
  g.save();
  g.translate(x, y); g.rotate(rot); g.scale(s, s);
  g.translate(12, 1 + 3 * (1 - k));
  g.rotate(-0.35);
  g.scale(k, k);
  // the tongue tip pokes out of the right corner, slightly down and sideways
  g.fillStyle = '#ef8199'; g.strokeStyle = '#4b1d45'; g.lineWidth = 2.4;
  g.beginPath(); g.moveTo(-6, -1); g.bezierCurveTo(-6, 8, 2, 11, 6, 8); g.bezierCurveTo(10, 5, 8, -2, 4, -2.5); g.closePath(); g.fill(); g.stroke();
  g.strokeStyle = 'rgba(170,60,90,0.7)'; g.lineWidth = 1.4;
  g.beginPath(); g.moveTo(0.5, 0); g.quadraticCurveTo(2, 4, 1.5, 6.5); g.stroke();
  g.fillStyle = 'rgba(255,255,255,0.55)'; g.beginPath(); g.ellipse(4.5, 3, 1.6, 1.1, 0, 0, TAU); g.fill();
  g.restore();
}
/** soft amber flare where a button is pressed (in front of the console rim, additive) */
function pressFlare(g, x, k) {
  if (k <= 0.01) return;
  g.save(); g.globalCompositeOperation = 'lighter';
  const y = 1236;
  let gr = g.createRadialGradient(x, y, 0, x, y, 120);
  gr.addColorStop(0, `rgba(255,207,122,${0.28 * k})`); gr.addColorStop(0.5, `rgba(255,170,90,${0.09 * k})`); gr.addColorStop(1, 'rgba(255,170,90,0)');
  g.fillStyle = gr; g.fillRect(x - 120, y - 120, 240, 240);
  gr = g.createRadialGradient(x, y + 6, 0, x, y + 6, 26);
  gr.addColorStop(0, `rgba(255,240,200,${0.55 * k})`); gr.addColorStop(1, 'rgba(255,220,150,0)');
  g.fillStyle = gr; g.fillRect(x - 26, y - 20, 52, 52);
  g.restore();
}
/** ANGER's one mouth corner curling up (screen-right) — the face rig only has symmetric smiles. Mirrors
 *  emotions.mjs's head placement for ANGER (neck −216 + breath, head centre −64, face +8, mouth +38). */
function angerCornerCurl(g, x, y, s, pose, k) {
  const u = 400 / 330, br = Math.sin(pose.t * TAU * 0.36 + 53);
  const tilt = pose.headTilt || 0, lean = pose.lean || 0;
  const px = (pose.headDX || 0) - Math.sin(tilt) * -18, py = -216 + br * 1.2 * u + (pose.headDY || 0) + Math.cos(tilt) * -18;
  const wx = x + s * (px * Math.cos(lean) - py * Math.sin(lean)), wy = y + s * (px * Math.sin(lean) + py * Math.cos(lean));
  const e = pose.face, smile = clamp(e.smile || 0, -1, 1), pressed = clamp(e.pressed || 0);
  const W0 = 25, hw = W0 * (1 + 0.32 * (e.wide || 0) + 0.12 * Math.abs(smile)) * (1 - pressed * 0.12);
  const cy = -smile * W0 * 0.32;
  g.save();
  g.translate(wx, wy); g.rotate(lean + tilt); g.scale(s, s);
  g.strokeStyle = '#561812'; g.lineCap = 'round';
  g.lineWidth = 2.6 * 1.15 * (1 + pressed * 0.35);
  g.beginPath();
  g.moveTo(hw - 7, cy + 0.5);
  g.quadraticCurveTo(hw + 1, cy + 1 - 1.5 * k, hw + 3 + 1.5 * k, cy - 7.5 * k);
  g.stroke();
  g.restore();
}
/** single 4-point star glint (world coords) */
function glint(g, x, y, r, k) {
  if (k <= 0.01) return;
  g.save(); g.globalCompositeOperation = 'lighter';
  const gr = g.createRadialGradient(x, y, 0, x, y, r * 2.2);
  gr.addColorStop(0, `rgba(230,220,255,${0.5 * k})`); gr.addColorStop(0.4, `rgba(150,130,255,${0.16 * k})`); gr.addColorStop(1, 'rgba(140,120,255,0)');
  g.fillStyle = gr; g.fillRect(x - r * 2.2, y - r * 2.2, r * 4.4, r * 4.4);
  g.fillStyle = `rgba(255,252,240,${Math.min(1, k)})`;
  const w = r * 0.13;
  g.beginPath();
  g.moveTo(x - r, y); g.lineTo(x, y - w); g.lineTo(x + r, y); g.lineTo(x, y + w); g.closePath();
  g.moveTo(x, y - r * 1.2); g.lineTo(x + w, y); g.lineTo(x, y + r * 1.2); g.lineTo(x - w, y); g.closePath();
  g.fill();
  g.restore();
}

// ---------------------------------------------------------------- expressions
// work faces look DOWN at the console: lookY ~1 alone barely moves these big irises (they read as looking at the
// camera), so the upper lids follow the gaze down (lidU ≈ 0.3). That also makes every look-up / glance read.
const F_CONC = makeExpr({ lookY: 1, lookX: 0.12, browSquish: 0.8, browIn: -0.32, browUp: -0.12, lidU: 0.36, lidL: 0.48, pressed: 0.25 });
const F_LIT = makeExpr({ lookY: 0.7, lookX: 0.1, browUp: 0.5, browIn: 0.1, lidU: -0.22, open: 0.26, round: 0.5, pupil: 1.25, sparkle: 0.55 });
const F_PLEASED = makeExpr({ lookY: 0.9, lookX: 0.15, browUp: 0.25, lidU: 0.12, lidL: 0.3, smile: 0.55, sparkle: 0.3 });
const F_PROUD = makeExpr({ lookX: 0.95, lookY: -0.05, browUp: 0.3, lidL: 0.45, smile: 0.72, blush: 0.35, sparkle: 0.2 });
const F_GIGGLE = makeExpr({ lidU: 0.88, lidL: 0.65, browUp: 0.35, browIn: 0.1, smile: 0.9, blush: 0.55 });
const F_WORK = makeExpr({ lookY: 1, lookX: 0.05, browSquish: 0.25, lidU: 0.3, smile: 0.25 });

export function render(g, t, S) {
  const T = (a) => S.T(a);
  const B2 = T('s19b02');
  const shotB = t >= B2;

  // ---------------- camera
  let cam;
  if (!shotB) {
    // A drift along the row (only four of the five fit at a medium; all five need zoom ≤ 1.18, which would bring
    // the Void's robe into the top half before the b02 reveal). It follows Fear's eyeline to JOY: JOY's near eye
    // is in frame when Fear glances over (b01+1.08) and its whole face for the lean-in (b01+1.85 → +4.1), so the
    // shot ends further right than the plan's 490. CALM is at the left edge for the press. Peak ≈ 37 px/s.
    const x = S.k(t, [['scene.start', 440], ['s19b02', 530, 'sine']]);
    const z = S.k(t, [['scene.start', 1.45], ['s19b02', 1.49, 'sine']]);
    const d = drift(t, 2.5);
    cam = { x: x + d.dx / z, y: 1150 + d.dy / z, zoom: z, rot: d.dr * 0.5 };
  } else {
    const z = S.k(t, [['s19b02', 0.9], ['s19b03+3.0', 0.8, 'inOut']]);
    const d = drift(t, 2);
    cam = { x: 450 + d.dx / z, y: 800 + d.dy / z, zoom: z, rot: d.dr * 0.4 };
  }

  const st = { ...HQ_PRESETS.dawn, t, voidShadow: 0.1, consolePress: {} };

  // ================= FEAR =================
  const fearT = t;
  let fFace, fHeadTurn = 0, fHeadTilt = 0, fLean = 0, fHeadDX = 0, fHeadDY = 0;
  let armR, armL = { target: [-42, -104], bend: -1, front: true, hand: 'open' };
  let tongue = 0, fearPress = 0;
  if (!shotB) {
    // --- A: press → light → glance at JOY + proud wiggle → giggle → back to work
    fFace = S.k(t, [
      ['scene.start', F_CONC], ['s19b01+0.3', F_CONC],
      ['s19b01+0.55', F_LIT, 'out'],
      ['s19b01+0.85', F_PLEASED],
      ['s19b01+0.9', F_PLEASED],
      ['s19b01+1.08', { ...F_PLEASED, lookX: 0.95, lookY: -0.05, smile: 0.6 }, 'out'], // eyes lead
      ['s19b01+1.35', F_PROUD],
      ['s19b01+2.35', F_PROUD],
      ['s19b01+2.6', F_GIGGLE],
      ['s19b01+3.55', F_GIGGLE],
      ['s19b01+3.85', { ...F_PROUD, lookX: 0.7, lookY: 0.1, smile: 0.6 }],
      ['s19b01+4.25', { ...F_WORK, smile: 0.35 }],
    ]);
    // a quick blink as the eyes swing over to JOY (and the button's light settles)
    fFace = { ...fFace, blink: blinkAt(t, T('s19b01+0.97'), 0.16) };
    fHeadTurn = S.k(t, [['s19b01+1.05', 0], ['s19b01+1.35', 0.25], ['s19b01+3.7', 0.2], ['s19b01+4.2', 0.02]]);
    // proud wiggle: two small side-to-side head tilts with the body
    const wig = win(t, T('s19b01+1.15'), T('s19b01+1.35'), T('s19b01+1.75'), T('s19b01+2.0'));
    const ph = (t - T('s19b01+1.15')) * TAU * 2.4;
    fHeadTilt = 0.075 * Math.sin(ph) * wig;
    fLean = 0.03 * Math.sin(ph - 0.6) * wig;
    // the silent giggle: shoulders and head bounce under the hand
    const gig = win(t, T('s19b01+2.55'), T('s19b01+2.75'), T('s19b01+3.35'), T('s19b01+3.7'));
    fHeadDY = -4 * Math.abs(Math.sin((t - T('s19b01+2.55')) * TAU * 1.9)) * gig;
    fHeadTilt += 0.05 * gig;
    // the pressing hand: hover → tiny lift (anticipation) → press (behind the rim) → rest → covers the mouth
    // (the lift brings the hand up over the rim so the press reads: it dips out of sight onto the button)
    const press = S.k(t, [['s19b01-0.08', 0], ['s19b01+0.18', -1, 'inOut'], ['s19b01+0.3', 1, 'in'], ['s19b01+0.55', 1], ['s19b01+0.8', 0]]);
    const rx = 42, ry = -106 + (press > 0 ? press * 16 : press * 26);
    const cover = S.k(t, [['s19b01+2.36', 0], ['s19b01+2.64', 1, 'out'], ['s19b01+3.6', 1], ['s19b01+3.95', 0]]);
    // the palm lands ON the mouth (wrist under the chin, fingers up over the lips); the old target (10,−164) put
    // the hand beside the mouth corner, where it read as a little wave next to the smile
    armR = cover > 0.001
      ? { target: [lerp(rx, -5, cover), lerp(-108, -157, cover)], bend: 1, front: true, hand: cover > 0.5 ? 'palm' : 'open' }
      : { target: [rx, ry], bend: 1, front: true, hand: 'open' };
    tongue = S.k(t, [['scene.start', 1], ['s19b01+0.33', 1], ['s19b01+0.45', 0]]);
    fearPress = S.k(t, [['s19b01+0.28', 0], ['s19b01+0.36', 1, 'out'], ['s19b01+1.6', 0.15, 'sine'], ['s19b01+3.0', 0]]);
  } else {
    // --- B: a glance back at the Void (once), back to work; CALM's point → press; head on SADNESS's shoulder
    const lookBackW = win(t, T('s19b02+0.6'), T('s19b02+0.95'), T('s19b02+1.4'), T('s19b02+1.85'));
    const eyesBack = win(t, T('s19b02+0.5'), T('s19b02+0.7'), T('s19b02+1.45'), T('s19b02+1.7'));
    const toCalm = win(t, T('s19b03+0.45'), T('s19b03+0.65'), T('s19b03+1.0'), T('s19b03+1.3'));
    const lit = S.k(t, [['s19b03+1.05', 0], ['s19b03+1.25', 1, 'out'], ['s19b03+2.2', 0, 'sine']]);
    const lean = win(t, T('s19b03+2.3'), T('s19b03+3.1'), T('s19b03+4.7'), T('s19b03+5.5'));
    // the eyes close as the head settles and open (quickly, before the head lifts) when it is over
    const leanFace = win(t, T('s19b03+2.5'), T('s19b03+3.05'), T('s19b03+4.5'), T('s19b03+4.75'));
    let f = makeExpr(F_WORK);
    f = lerpE(f, { ...F_WORK, lookX: -0.3, lookY: -0.95, browUp: 0.3, browSquish: 0, lidU: 0, smile: 0.2 }, eyesBack);
    const smileBack = S.k(t, [['s19b02+0.95', 0], ['s19b02+1.3', 1], ['s19b02+1.9', 0.4]]);
    f.smile += 0.3 * smileBack * eyesBack + 0.12 * smileBack; f.lidL += 0.25 * smileBack * eyesBack;
    f = lerpE(f, { ...F_WORK, lookX: -0.75, lookY: 0.55, browUp: 0.2, browSquish: 0.1 }, toCalm);
    f = lerpE(f, { ...f, lidU: -0.1, browUp: 0.3, smile: 0.5, sparkle: 0.45, pupil: 1.15 }, lit);
    f = lerpE(f, { lidU: 0.95, lidL: 0.55, browUp: 0.12, browIn: 0.25, smile: 0.62, blush: 0.4, lookX: 0.05, lookY: 0.6 }, leanFace);
    f.smile += 0.15 * lean * (1 - leanFace);
    f.blink = blinkAt(t, T('s19b02+1.15'), 0.22);
    fFace = f;
    fHeadTurn = -0.4 * lookBackW;
    fHeadTilt = -0.1 * lookBackW + 0.26 * lean;
    fHeadDY = -2 * lookBackW;
    fHeadDX = 7 * lean;
    fLean = 0.055 * lean;
    const press = bumps(t, [T('s19b02+2.3'), T('s19b03+1.05')], 0.1, 0.25);
    armR = { target: [42 + 4 * lean, -106 + press * 16], bend: 1, front: true, hand: 'open' };
    fearPress = S.k(t, [['s19b03+1.0', 0], ['s19b03+1.1', 1, 'out'], ['s19b03+2.4', 0, 'sine']]) + 0.5 * bumps(t, [T('s19b02+2.33')], 0.08, 0.6);
  }
  const fearPose = {
    t: fearT, face: fFace, headTurn: fHeadTurn, headTilt: fHeadTilt, headDX: fHeadDX, headDY: fHeadDY, lean: fLean,
    armL, armR, shadow: false,
  };

  // ================= EMOTIONS =================
  const em = {};
  // coloured button-light pulses [station, world x, 0..1] (drawn after the console foreground)
  const pulses = [];
  let jPressY = -182;
  // ---- JOY (695): taps → notices Fear's glance → leans in past SADNESS, beaming → back to work;
  //      B: humming smile, star tuft in time; looks up at us (Consciousness) and smiles
  {
    const tt = t + TOFF.JOY;
    const lean = win(t, T('s19b01+1.85'), T('s19b01+2.4'), T('s19b01+3.5'), T('s19b01+4.1'));
    const look = win(t, T('s19b01+1.1'), T('s19b01+1.3'), T('s19b01+3.6'), T('s19b01+3.9'));
    // at work: eyes down on its buttons (lids follow the gaze), humming smile
    let f = makeExpr(EXPR.softSmile, { lookY: 1, lookX: -0.15, lidU: 0.33 });
    f = lerpE(f, { ...EXPR.softSmile, lookX: -0.9, lookY: 0.1, browUp: 0.35, lidU: -0.05 }, look);
    f = lerpE(f, { ...EXPR.beaming, lookX: -0.95, lookY: 0.12, open: 0.22, lidL: 0.4 }, lean);
    let headDY = 0, headTilt = -0.07 * lean, armDY = 0;
    if (shotB) {
      const hum = Math.sin((t - B2) * TAU * 1.05);
      headTilt += 0.035 * hum;
      f.smile = Math.max(f.smile, 0.5);
      // b03 end: the eyes lift first (to the screen = to us), then the chin, and the smile grows
      const eyesUp = win(t, T('s19b03+4.4'), T('s19b03+4.65'), T('s19b03+5.9'), T('s19b03+6.3'));
      const up = win(t, T('s19b03+4.55'), T('s19b03+4.95'), T('s19b03+5.8'), T('s19b03+6.3'));
      f = lerpE(f, { ...f, lookX: -0.05, lookY: -0.12, lidU: -0.05, browUp: 0.25 }, eyesUp);
      f = lerpE(f, { ...EXPR.smile, smile: 0.9, lidL: 0.35, lookX: -0.05, lookY: -0.12, browUp: 0.35, blush: 0.35 }, up);
      headDY = -5 * up;
      headTilt += 0.05 * up;
      armDY = 7 * bumps(t, [T('s19b02+0.4'), T('s19b02+1.3'), T('s19b02+2.2'), T('s19b03+0.6'), T('s19b03+1.7'), T('s19b03+3.2')]);
    } else {
      armDY = 7 * bumps(t, [T('scene.start+0.3'), T('s19b01+0.1')]);
      // presses that read (beat 23): the near hand rises over the rim and dips onto the gold button — once right after
      // Fear's (Fear's proud glance at +1.08 goes to a busy, glowing JOY), once back at work after the lean-in
      const p1 = pressMove(t, T('s19b01+0.85'), -182, -208), p2 = pressMove(t, T('s19b01+4.38'), -182, -210);
      jPressY = t < T('s19b01+2.6') ? p1.y : p2.y;
      pulses.push(['JOY', ROW_S19.JOY - 52, Math.max(p1.pulse, p2.pulse)]);
    }
    // B (wide): its taps light its gold buttons softly
    if (shotB) pulses.push(['JOY', ROW_S19.JOY + 30, 0.35 * armDY / 7]);
    const arm = (side) => ({ preset: 'pressButton', atY: side < 0 ? jPressY : -182, dy: side > 0 ? armDY : armDY * 0.3 });
    em.JOY = { pose: { t: tt, face: f, lean: -0.075 * lean, headDX: -10 * lean, headTilt, headDY, armL: arm(-1), armR: arm(1), shadow: false },
      press: armDY / 7 };
  }
  // ---- SADNESS (570): turning its dial, content → rests its head against Fear → back; B: sleepy content blinks;
  //      Fear leans on its shoulder (it leans back a little into it)
  {
    const tt = t + TOFF.SADNESS;
    const rest = win(t, T('s19b01+1.45'), T('s19b01+2.1'), T('s19b01+3.75'), T('s19b01+4.4'));
    const glance = win(t, T('s19b01+1.2'), T('s19b01+1.4'), T('s19b01+1.6'), T('s19b01+1.9'));
    let f = makeExpr({ lookY: 1, lookX: 0.05, lidU: 0.32, smile: 0.28, browIn: -0.1 });
    f = lerpE(f, { lookY: 0.15, lookX: -0.75, lidU: 0.1, smile: 0.38, browIn: 0 }, glance);
    // eyes close as the head settles; they open again (looking back down at the dial) before the head lifts
    const restFace = win(t, T('s19b01+1.6'), T('s19b01+2.1'), T('s19b01+3.55'), T('s19b01+3.8'));
    f = lerpE(f, { lookY: 0.9, lookX: -0.1, lidU: 0.92, lidL: 0.5, smile: 0.62, blush: 0.3, browIn: 0.2, browUp: 0.1 }, restFace);
    f.smile += 0.12 * rest * (1 - restFace);
    let headTilt = -0.13 * rest, lean = -0.04 * rest, headDX = -9 * rest;
    if (shotB) {
      const fl = win(t, T('s19b03+2.5'), T('s19b03+3.2'), T('s19b03+4.7'), T('s19b03+5.4'));
      headTilt = 0.06 + -0.05 * fl; // head tilted (content), leaning slightly toward Fear when Fear leans on it
      f = makeExpr({ lookY: 1, lookX: -0.1, lidU: 0.36, smile: 0.32, browIn: -0.05 });
      f = lerpE(f, { lookY: 0.4, lookX: -0.6, lidU: 0.45, lidL: 0.3, smile: 0.5, blush: 0.25 }, fl);
      f.blink = Math.max(blinkAt(t, T('s19b02+0.7'), 0.5), blinkAt(t, T('s19b02+2.3'), 0.55), blinkAt(t, T('s19b03+0.6'), 0.5));
    }
    // the dial: a small circular turn of the right hand
    const dph = t * TAU * 0.55;
    const dial = { preset: 'pressButton', atY: -184 + 2 * Math.cos(dph), dx: 3 * Math.sin(dph) };
    em.SADNESS = { pose: { t: tt, face: f, headTilt, lean, headDX, armL: { preset: 'pressButton', atY: -181 }, armR: dial, shadow: false },
      press: 0.35 };
  }
  // ---- ANGER (330): working its lever; during the giggle its eyes slide over, the lips press hard, a smile leaks
  //      through anyway (one corner curls up: local overlay, the rig's smile is symmetric), it catches itself and
  //      looks back down at its lever with the corner still up. B: brows relaxed out of the V; as CALM's long
  //      arm reaches across in front of it, it glances down at it and lifts its chin / leans aside to make room.
  let angerCurl = 0;
  {
    const tt = t + TOFF.ANGER;
    let f, lean = 0, headTilt = 0, headDY = 0;
    if (!shotB) {
      const side = win(t, T('s19b01+2.6'), T('s19b01+2.85'), T('s19b01+3.75'), T('s19b01+4.1'));
      const press = S.k(t, [['s19b01+2.8', 0], ['s19b01+3.0', 1], ['s19b01+3.85', 1], ['s19b01+4.3', 0.55]]);
      // the leak: rises against the pressed lips, is caught (+3.7) and settles to a residue
      const leak = S.k(t, [['s19b01+3.05', 0], ['s19b01+3.35', 1, 'out'], ['s19b01+3.65', 1], ['s19b01+3.9', 0.45, 'sine']]);
      f = makeExpr({ lookY: 1, lookX: 0.05, browIn: 0.12, pressed: 0.3, smile: 0.02, lidU: 0.24 });
      f = lerpE(f, { ...f, lookX: 0.9, lookY: 0.2, lidU: 0.12 }, side);
      f.pressed = lerp(f.pressed, 0.9, press);
      f.smile += 0.5 * leak;
      f.browIn += 0.2 * leak * side;                  // the V softens while it watches…
      f.browSquish = 0.25 * press * (1 - side);       // …and knits again as it looks back to work
      f.blush = 0.25 * leak;
      headTilt = 0.04 * leak;
      angerCurl = leak;
    } else {
      const glance = win(t, T('s19b03+0.25'), T('s19b03+0.55'), T('s19b03+1.55'), T('s19b03+1.95'));
      f = makeExpr({ lookY: 1, lookX: 0.05, browIn: 0.32, smile: 0.05, lidU: 0.24 });
      f = lerpE(f, { ...f, lookX: -0.5, lookY: 0.8, lidU: 0.05, browUp: 0.2 }, glance);
      lean = 0.035 * glance; headTilt = 0.05 * glance; headDY = -7 * glance;
    }
    // the lever: a slow pull down and back (left hand), the right hand resting
    const lv = 0.5 - 0.5 * Math.cos((t + 0.7) * TAU * 0.32);
    // A: caught smiling, it gets back to work with one firm, businesslike press (the near hand over the rim and down)
    let aPressY = -180;
    if (!shotB) {
      const pm = pressMove(t, T('s19b01+4.0'), -180, -205);
      aPressY = pm.y; pulses.push(['ANGER', ROW_S19.ANGER + 50, pm.pulse]);
    }
    em.ANGER = { pose: { t: tt, face: f, lean, headTilt, headDY, armL: { preset: 'pressButton', atY: -186, dy: 11 * lv }, armR: { preset: 'pressButton', atY: aPressY }, shadow: false },
      press: lv };
  }
  // ---- CALM (205): serene half lids, closed smile, sliding a slider, watching Fear; a small nod when Fear's
  //      button lights up (A, while CALM is still in frame); B: points at the next button with one long finger
  //      (+ nod), then the slow blink as Fear leans on SADNESS
  let calmPoint = 0;
  {
    const tt = t + TOFF.CALM;
    let f = makeExpr({ lookY: 0.65, lookX: 0.4, lidU: 0.12, smile: 0.32 });
    const nodA = env(t, T('s19b01+0.62'), 0.3, 0.12, 0.45);
    let headDY = 6 * nodA, lean = 0, armR;
    f.smile += 0.12 * nodA;
    const sl = Math.sin(tt * TAU * 0.18);
    armR = { preset: 'pressButton', atY: -186, dx: 5 * sl };
    if (shotB) {
      // one long, nearly straight arm across in front of ANGER (it makes room), the finger turned toward Fear's
      // next button (the old bent arm hooked the forearm down across ANGER's face)
      const pt = win(t, T('s19b03+0.15'), T('s19b03+0.6'), T('s19b03+1.5'), T('s19b03+2.0'));
      const nod = env(t, T('s19b03+0.7'), 0.25, 0.05, 0.4);
      headDY = 6 * nod;
      lean = 0.03 * pt;
      f = lerpE(f, { lookY: 0.55, lookX: 0.85, lidU: 0.0, smile: 0.42, browUp: 0.15 }, pt);
      const sb = win(t, T('s19b03+3.1'), T('s19b03+3.25'), T('s19b03+3.8'), T('s19b03+4.1'));
      f.blink = sb;                       // CALM's slow blink (held closed for half a second)
      f.smile += 0.12 * win(t, T('s19b03+3.0'), T('s19b03+3.4'), T('s19b03+5.0'), T('s19b03+5.6'));
      if (pt > 0.001) armR = { target: [lerp(46, 128, pt), lerp(-186, -194, pt)], bend: 1, hand: 'point', layer: 'over', handAng: lerp(Math.PI / 2, 0.15, pt) };
      calmPoint = pt;
    }
    em.CALM = { pose: { t: tt, face: f, headDY, lean, armL: { preset: 'pressButton', atY: -182 }, armR, shadow: false }, press: 0.2 };
  }

  // console presses → the set's amber spill per station (+ our own flare for Fear's spot)
  for (const n of ['JOY', 'SADNESS', 'ANGER', 'CALM']) st.consolePress[HQ_STATIONS[n].buttons[0]] = clamp(em[n].press);

  // ================= DRAW =================
  g.save();
  applyCamera(g, cam);
  drawHQ(g, 'front', st);
  // the Void: "like a mountain behind a village", faint stars in the hood
  const vPose = { t, ...STARE_F, idle: 0.5, cosmos: COSMOS_RESIDUE, cosmosOpts: { seed: 7, glyphs: 0 } };
  drawVoid(g, ...VOID_F, vPose);
  // the rusted cage at its feet, barely visible
  drawCage(g, ...CAGE_F, { t, ...CAGE_PRESETS.barelyVisible });
  // the row (left → right; SADNESS over JOY so JOY leans in from behind it), then Fear in the middle on top.
  // CALM over ANGER: in B its long arm reaches across in front of ANGER, who lifts its chin out of the way.
  drawEmotion(g, 'ANGER', ROW_S19.ANGER, ROW_Y, SC, em.ANGER.pose);
  if (angerCurl > 0.01) angerCornerCurl(g, ROW_S19.ANGER, ROW_Y, SC, em.ANGER.pose, angerCurl);
  drawEmotion(g, 'CALM', ROW_S19.CALM, ROW_Y, SC, em.CALM.pose);
  drawEmotion(g, 'JOY', ROW_S19.JOY, ROW_Y, SC, em.JOY.pose);
  drawEmotion(g, 'SADNESS', ROW_S19.SADNESS, ROW_Y, SC, em.SADNESS.pose);
  drawFear(g, ROW_S19.FEAR, FEAR_Y, SC, fearPose);
  if (tongue > 0) {
    const [mx, my, mr] = fearMouth(ROW_S19.FEAR, FEAR_Y, SC, fearPose);
    tongueTip(g, mx, my, SC, mr, tongue);
  }
  drawHQForeground(g, 'front', st);
  for (const [n, x, k] of pulses) stationPulse(g, x, STATION_RGB[n], clamp(k), shotB ? 0.8 : 1);
  // while CALM points, the next button at Fear's spot glows softly ("this one"), then flares when pressed
  const ready = 0.3 * calmPoint * (0.75 + 0.25 * Math.sin((t - T('s19b03')) * TAU * 2.2));
  pressFlare(g, 480, clamp(Math.max(fearPress, ready)));
  // the single star twinkling in the hood (s19b03+1.5, 0.8 s)
  if (shotB) {
    const k = env(t, T('s19b03+1.5'), 0.25, 0.1, 0.45);
    if (k > 0) {
      const fc = voidRig(vPose).face;
      glint(g, VOID_F[0] + fc[0] * VOID_F[2] + 4, VOID_F[1] + fc[1] * VOID_F[2] - 6, 11, k);
    }
  }
  g.restore();

  // ---------------- light
  if (!shotB) {   // TOP SHADE (§5.9): keeps the back of the mind quiet at the top of the medium
    const gr = g.createLinearGradient(0, 0, 0, 300);
    gr.addColorStop(0, 'rgba(8,6,20,0.55)'); gr.addColorStop(1, 'rgba(8,6,20,0)');
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = gr; g.fillRect(0, 0, W, 300); g.restore();
  }
  // the screen's warm morning light (behind the camera) spills over the console and the row in the POV shot
  const ks = shotB ? S.k(t, [['s19b02+0.5', 0], ['s19b03+3.0', 1]]) : 0;
  if (ks > 0) {
    const gr = g.createLinearGradient(0, 1280, 0, 700);
    gr.addColorStop(0, `rgba(255,214,160,${0.16 * ks})`); gr.addColorStop(1, 'rgba(255,214,160,0)');
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'screen'; g.fillStyle = gr; g.fillRect(0, 700, W, 580); g.restore();
  }
  grade(g, 0, S.k(t, [['scene.start', 0.8], ['scene.end', 0.9]]));
  // screen bloom (§5.10): the screen of consciousness behind the camera brightens → the dissolve to the real room
  const kb = S.k(t, [['scene.end-2.0', 0], ['scene.end+0.9', 1]]);
  if (kb > 0) {
    const gr = g.createLinearGradient(0, 1280, 0, 300);
    gr.addColorStop(0, `rgba(255,236,200,${0.55 * kb})`); gr.addColorStop(1, 'rgba(255,236,200,0)');
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'screen'; g.fillStyle = gr; g.fillRect(0, 0, W, H); g.restore();
  }
  vignette(g, 0.3);
}

/** blend two expression objects (missing fields = 0) */
function lerpE(a, b, k) {
  if (k <= 0) return a;
  const o = { ...a };
  for (const key in b) if (typeof b[key] === 'number') o[key] = lerp(typeof a[key] === 'number' ? a[key] : 0, b[key], k);
  for (const key in a) if (!(key in b) && typeof a[key] === 'number' && key !== 't' && key !== 'pupil' && key !== 'iris') o[key] = lerp(a[key], 0, k);
  return o;
}
