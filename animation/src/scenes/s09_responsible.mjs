// s09 · responsible · front view
// NARRATOR: "I told myself it was the responsible thing to do." / "And I felt sadness."
import { clamp, lerp, ease, fbm, blinkAt, applyCamera, drift, vignette, TAU, ik } from '../engine.mjs';
import { EXPR, makeExpr } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawSelf, SELF_EXPR, selfLocal, selfPoseAnchors, WALK_ADVANCE } from '../chars/self.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawEmotion, EMOTION_ARMS, EMOTION_ANCHORS } from '../chars/emotions.mjs';
import { drawHQ, drawHQForeground, hqScaleAt } from '../sets/hq.mjs';
import { drawCage, cagePoint } from '../sets/props.mjs';
import { blendHand } from '../hand.mjs';
import { drawLit } from '../fx/rim.mjs';

export const id = 's09';

// ---- staging constants (data/staging.md §1.4)
const VOID_F = [450, 830, 0.37];
const STARE_F = { headTurn: 0, headDown: 0.1 };
const CAGE_F = [302, 846, 0.3];
const OFF = { JOY: 1.3, SADNESS: 2.9, ANGER: 4.1, CALM: 5.7 };
const SET = { lightsDim: 0.4, consoleGlow: 0.7, mist: 0.45, voidShadow: 0.6 };
const COLD = 0.6, VIG = 0.45;
const MID = [450, 1384, 0.8];          // consoleMid
const SAD_AT = [590, 1390];            // SADNESS at the CEO's elbow (staging 530: her wide head then covered the very
                                       // sleeve she touches; 600 keeps the CEO's right elbow clear of it). Drawn in front.

export const sfx = [
  { at: 'scene.start-0.02', name: 'door_whoosh', gain: -16, pan: -0.7 },          // the EXIT door swings shut behind CALM
  { at: 'scene.start+0.05', name: 'footsteps', gain: -15, rate: 1.1, until: 'scene.start+1.75', fade: 0.15, pan: -0.3 },
  { at: 'scene.start+0.2', name: 'footsteps', gain: -24, rate: 1.4, until: 'scene.start+1.3', fade: 0.12, pan: -0.7 },
  { at: 'scene.start+1.55', name: 'paper_rustle', gain: -15 },                    // picks up the clipboard (swish ≈ +2.05)
  { at: 's09b01.end+0.05', name: 'paper_rustle', gain: -24 },                   // the clipboard lowered back to the console
  { at: 's09b02-0.05', name: 'cloth_rustle', gain: -17 },                        // hand up to the mouth
  { at: 's09b02+1.05', name: 'cloth_rustle', gain: -22, pan: 0.3 },              // SADNESS's hand on the sleeve
];

// ---------------------------------------------------------------- local helpers
function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function cam(g, c, t, amp = 2.5) {
  const d = amp ? drift(t, amp, 9) : { dx: 0, dy: 0, dr: 0 };
  applyCamera(g, { x: c.x + d.dx / c.zoom, y: c.y + d.dy / c.zoom, zoom: c.zoom, rot: d.dr * 0.5 });
}
const sstep = (a, b, x) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };
const life = (t, seed, amp = 0.08) => fbm(t * 0.4, seed) * amp;   // tiny gaze drift

// ---------------------------------------------------------------- the CEO
function ceoState(t, S) {
  const t0 = S.start, tArr = S.T('scene.start+1.6');
  const u = clamp((t - t0) / (tArr - t0));
  const k = 1 - Math.pow(1 - u, 1.7);                    // walking in, easing into the stop
  const x = lerp(190, MID[0], k), y = lerp(1170, MID[1], k);
  return { x, y, s: hqScaleAt('front', y), walking: u < 1, u };
}

// ---------------------------------------------------------------- render
export function render(g, t, S) {
  const close = t >= S.T('s09b02');
  g.save();
  if (!close) {
    // medium at the console: first frame {400,1060,1.2} (= the staging), then it widens with the CEO's walk so the
    // whole row (CALM … JOY) is in frame for their reactions, and settles into a very slow push
    // (over 3 s, sine: the tilt peaks at ≈85 px/s on screen; over 2.1 s inOut it hit ≈160 px/s. JOY is in frame by
    // her smile at b01+2.1)
    cam(g, S.k(t, [['scene.start', { x: 400, y: 1060, zoom: 1.2 }],
      ['scene.start+3.0', { x: 450, y: 905, zoom: 1.0 }, 'sine'], ['s09b02', { x: 452, y: 915, zoom: 1.05 }, 'sine']]), t, 2.5);
  } else {
    // close on the CEO with SADNESS at their elbow (staging {480,1020,2.0}→{470,1010,2.15}), centred between them and
    // far enough right that the little cage (world x ≤ 356, top-left) stays out of frame instead of peeking in as a
    // sliver at the corner; ANGER and JOY are reduced to faceless edges of colour at the frame sides
    cam(g, S.k(t, [['s09b02', { x: 526, y: 1032, zoom: 2.2 }], ['scene.end+0.9', { x: 522, y: 1024, zoom: 2.3 }, 'sine']]), t, 2);
  }
  const doorOpen = S.k(t, [['scene.start', 0.6], ['scene.start+1.0', 0, 'inOut']]);
  const st = { t, ...SET, doorOpen };
  drawHQ(g, 'front', st);
  drawVoid(g, ...VOID_F, { t, ...STARE_F, idle: 0, shadow: false });

  // ---- Fear in the cage (background, small): still crying at the bars
  const cst = { t, door: 0, locked: 1, shake: 0.15 * Math.max(0, Math.sin(t * 2.1)) };
  drawCage(g, ...CAGE_F, { ...cst, layer: 'back' });
  const [fx, fy] = cagePoint('occupantFront', ...CAGE_F, cst);
  const fl = (p) => [(p[0] - fx) / CAGE_F[2], (p[1] - fy) / CAGE_F[2]];
  const gl = fl(cagePoint('gripL', ...CAGE_F, cst)), gr = fl(cagePoint('gripR', ...CAGE_F, cst));
  drawFear(g, fx, fy, CAGE_F[2], {
    t, tremble: 0.6, breathe: 1.7, breathRate: 0.7,
    face: { ...EXPR.crying, open: 0.25, lidU: 0.45, stream: 0.75, lookY: -0.1 },
    armL: { target: gl, bend: 1, front: true, hand: 'grip' }, armR: { target: gr, bend: -1, front: true, hand: 'grip' },
  });
  drawCage(g, ...CAGE_F, { ...cst, layer: 'front', grips: ['gripL', 'gripR'] });

  // ---- characters back to front
  const list = [];
  const c = ceoState(t, S);
  // the open EXIT door behind-left of the CEO as they walk in: a warm rim on the edge facing it, fading as it shuts
  const doorLight = close ? 0 : clamp(doorOpen / 0.6);
  list.push({ y: c.y, draw: () => (doorLight > 0.02
    ? drawLit(g, (g2) => drawCEO(g2, t, S, c), { dir: [-1, -0.35], color: '#ffe6bd', strength: 0.55 * doorLight, width: 3 })
    : drawCEO(g, t, S, c)) });
  // CALM finishes its walk in from the door to slot 1
  const calmK = sstep(S.start, S.T('scene.start+1.2'), t);
  const calm = [lerp(120, 165, calmK), lerp(1262, 1384, calmK)];
  if (!close) list.push({ y: calm[1], draw: () => drawCalm(g, t, S, calm, calmK) });   // off-frame in the close
  list.push({ y: 1384, draw: () => drawAnger(g, t, S) });
  if (!close) list.push({ y: 1384.5, draw: () => drawJoy(g, t, S) });       // off-frame in the close (else one eye peeks in)
  list.push({ y: SAD_AT[1], draw: () => drawSadness(g, t, S, c) });
  list.sort((a, b) => a.y - b.y).forEach((o) => o.draw());

  drawHQForeground(g, 'front', st);
  g.restore();
  grade(g, COLD, 0);
  vignette(g, VIG);
}

function drawCEO(g, t, S, c) {
  const b2 = S.T('s09b02');
  // walk: bodyTurn toward the console, ends on a passing pose and turns to camera as they arrive
  const turn = 1 - sstep(S.T('scene.start+1.3'), S.T('scene.start+1.9'), t);
  const phase = ((c.x - MID[0]) / (WALK_ADVANCE * 0.7)) * TAU + Math.PI / 2;
  // clipboard (armL): reaches down to the console (+1.65), lifts it into view (+2.0 → +2.55); put back down on the
  // console at the end of the line (b01.end → the cut at b02)
  const reach = sstep(S.T('scene.start+1.6'), S.T('scene.start+1.95'), t);
  // (the board is still in the lowered hand at the rim when we cut to the close: it never pops out of the hand on screen)
  const lift = sstep(S.T('scene.start+2.0'), S.T('scene.start+2.55'), t) * (1 - sstep(S.T('s09b01.end'), S.T('s09b02+0.05'), t));
  const holding = t < S.T('s09b02') && reach > 0;
  // b02: the left hand presses over the mouth; after the eyes reopen it slides down to rest beside the right one, its
  // fingers behind the console rim. The move starts on the cut (it used to start 0.1 s before it, and for the last
  // frames of the medium the board jumped below the rising hand).
  const close = t >= S.T('s09b02');
  const toMouth = sstep(S.T('s09b02'), S.T('s09b02+0.6'), t);
  const lower = sstep(S.T('s09b02+2.7'), S.T('s09b02+3.6'), t);
  const k = c.s;
  // face (every key a complete expression: a field missing from the next key used to hold, then drop to 0 in one
  // frame — the lower lids, pressed lips and the tear gloss popped at +1.0 / +2.2)
  // The narrator sheds no tear before the last scene: the sadness stays in the lids, the pressed mouth, the hand and
  // the shoulders, with at most a glisten on the lower lids (tears ≤ 0.35).
  const X = (...p) => makeExpr(...p);
  const flat = X(SELF_EXPR.tired, { lidU: 0.5, lookY: 0.72, lookX: 0.05, smile: -0.1, pressed: 0.35, browIn: 0.35, tears: 0.12 });
  let face = S.k(t, [
    ['scene.start', X(SELF_EXPR.holdingBackTears, { tears: 0.32, lookY: 0.2 })],
    ['scene.start+1.0', X(SELF_EXPR.tired, { lookY: 0.35, tears: 0.25, pressed: 0.3 })],
    ['scene.start+2.2', flat],
    // 'responsible' — the jaw sets a fraction, a slow blink (they don't believe it)
    ['s09b01+2.4', flat], ['s09b01+3.0', X(flat, { pressed: 0.7, browIn: 0.5, lidU: 0.56 })],
    ['s09b02-0.1', X(flat, { pressed: 0.7, browIn: 0.6, lidU: 0.56, tears: 0.3 })],
    // the eyes close behind the hand on 'sadness'
    ['s09b02+0.55', X(SELF_EXPR.holdingBackTears, { lidU: 1, tears: 0.35, lookY: 0.4 })],
    ['s09b02+1.9', X(SELF_EXPR.holdingBackTears, { lidU: 1, tears: 0.35, lookY: 0.4 })],
    // they open again, heavy, gaze low; the lower lids just glisten
    ['s09b02+2.6', X(SELF_EXPR.sad, { lidU: 0.55, lidTilt: 0.55, tears: 0.33, lookY: 0.6, lookX: 0.12, pressed: 0.5, smile: -0.3 })],
  ]);
  face = {
    ...face,
    lookX: (face.lookX || 0) + life(t, 41, 0.05),
    blink: blinkAt(t, S.T('s09b01+2.75'), 0.42),
  };
  if (t > S.T('s09b02+0.4') && t < S.T('s09b02+2.4')) face.noAutoBlink = true;
  // shoulders round forward after the eyes reopen; a small catch of breath before 'sadness'
  const round = sstep(S.T('s09b02+1.9'), S.T('s09b02+3.0'), t);
  const kat = Math.sin(clamp((t - S.T('s09b02+0.48')) / 0.3) * Math.PI);
  // arriving: the walk ends on a passing pose (hips 5 units up, the walk's 0.045 forward lean); settle both out over
  // ~0.45 s instead of dropping them in one frame (the head jumped ~5 px sideways at +1.6)
  const settle = c.walking ? 0 : ease.sine(clamp((t - S.T('scene.start+1.6')) / 0.45));
  const x = c.x, y = c.y - (c.walking ? 0 : 5 * k * (1 - settle));
  const pose = {
    t, outfit: 'ceo', facing: 1, clipboard: holding && lift > 0,
    walk: c.walking ? { phase } : null, bodyTurn: c.walking || turn > 0 ? 0.4 * turn : 0,
    lean: c.walking ? 0 : 0.045 * (1 - settle),
    headTurn: 0.2 * turn + 0.02,
    headTilt: 0.05 + 0.04 * round, headDY: 2 + 5 * round + 2 * kat,
    shrug: 0.3 * round + 0.25 * kat,
    face,
  };

  // ---- arms
  let armL = 'rest';
  if (close) {
    // the coverMouth preset's own target, head point (-34, 47) — the mouth (the old fixed [-34,-455] sat ~20 units
    // higher: the hand popped down onto the mouth as the move ended and jumped back up to the eyes as it began to lower)
    const A = selfPoseAnchors(x, y, k, pose);
    const m = selfLocal(x, y, k, 1, A.mouth[0], A.mouth[1]), ch = selfLocal(x, y, k, 1, A.chin[0], A.chin[1]);
    const th = Math.atan2(-(ch[0] - m[0]), ch[1] - m[1]), cs = Math.cos(th), sn = Math.sin(th);
    const cover = [m[0] - 34 * cs - 10 * sn, m[1] - 34 * sn + 10 * cs];
    if (lower > 0) {
      // the hand slides down off the mouth, in front of the chest, into the resting pose of the other arm (wrist
      // above the rim, the relaxed fingers behind it, palm to the body)
      const e = ease.sine(lower), kh = sstep(0.35, 0.9, e);
      const p = e < 0.5 ? [lerp(cover[0], -14, e * 2), lerp(cover[1], -335, e * 2)] : [lerp(-14, -70, e * 2 - 1), lerp(-335, -198, e * 2 - 1)];
      armL = { preset: 'coverMouth', target: p, reach1: lerp(0.45, 1, e), hand: blendHand('flat', 'rest', kh),
        handAngle: lerp(th - 0.19, 1.62, e), palmDir: [lerp(0, 0.9, kh), 0, lerp(-1, -0.45, kh)] };
    } else {
      const e = ease.out(toMouth);
      armL = { preset: 'coverMouth', target: [lerp(-70, cover[0], e), lerp(-215, cover[1], e)] };
    }
  } else if (holding && lift > 0) {
    // the lift: gripped by its top edge below the rim (hidden behind the console), the board rises into view and the
    // grip comes round to its side, in front of the chest; the forearm foreshortens as the board comes toward us.
    // (The board used to appear in front of the chest in one frame, with the elbow jumping as the forearm shortened.)
    const e = ease.sine(lift), eh = sstep(0, 0.45, lift);
    armL = { preset: 'holdClipboard', target: [lerp(-55, -30, lift), lerp(-178, -290, ease.out(lift))], reach2: lerp(1, 0.55, e),
      board: [lerp(6, 24, e), lerp(45, -38, e), lerp(-0.08, 0.12, e)],
      hand: blendHand('rest', 'hold', eh), handAngle: lerp(1.35, -0.25, eh), palmDir: [lerp(0.9, 0, eh), 0, lerp(-0.45, 1, eh)] };
  } else if (reach > 0) {
    // reaching down over the console deck: the hand goes behind the rim (the relaxed 'rest' hand, as it hangs)
    armL = { target: [lerp(-70, -55, reach), lerp(-198, -178, reach)], bend: -1, front: true, hand: 'rest',
      handAngle: lerp(1.62, 1.35, reach) };
  }
  drawSelf(g, x, y, k, { ...pose, armL, armR: 'rest' });
}

function drawCalm(g, t, S, p, k) {
  const tt = t + OFF.CALM;
  const s = hqScaleAt('front', p[1]);
  // watches Consciousness (to its right), head tilted; one slow concerned blink
  const face = {
    ...EXPR.tender, smile: -0.05, browIn: 0.55, lidU: 0.25,
    lookX: S.k(t, [['scene.start+1.2', 0.2], ['scene.start+1.8', 0.55]]) + life(t, 51),
    lookY: S.k(t, [['scene.start+1.8', 0], ['s09b01+2.5', 0.15]]),
    blink: blinkAt(t, S.T('s09b01+3.1'), 0.5),
  };
  // three steps that land with the feet together as it stops (phase 3π), and the hands come up onto the console over
  // the last steps (the walk used to stop mid-stride and both arms snapped from the sides to the console in a frame)
  const reachK = sstep(0.55, 1, k);
  drawEmotion(g, 'CALM', p[0], p[1], s, {
    t: tt, face, headTurn: S.k(t, [['scene.start+1.3', 0.05], ['scene.start+2.0', 0.22]]), headTilt: S.k(t, [['scene.start+2.0', 0], ['s09b01+1.0', 0.07]]),
    // it comes mostly toward the camera (and a little right): the feet point that way, front-on as it stops
    walk: k < 1 ? { phase: k * 3 * Math.PI } : null, feetTurn: 0.3 * (1 - sstep(0.6, 1, k)),
    armL: emotionArmBlend('CALM', -1, 'rest', 'pressButton', reachK), armR: emotionArmBlend('CALM', 1, 'rest', 'pressButton', reachK),
  });
}

// emotions' arm bones (emotions.mjs SPECS L1/L2) — to know where a preset's hand points (the forearm direction)
const ARM_LEN = { JOY: [54, 52], SADNESS: [50, 50], ANGER: [50, 48], CALM: [66, 62] };
function presetHandAng(name, side, spec) {
  if (spec.handAng != null) return spec.handAng;
  const [L1, L2] = ARM_LEN[name], f = clamp(spec.fore || 0);
  const sh = EMOTION_ANCHORS[name][side < 0 ? 'shoulderL' : 'shoulderR'];
  const { a1, a2 } = ik(sh[0], sh[1], spec.target[0], spec.target[1], L1 * (1 - 0.32 * f), L2 * (1 - 0.45 * f), spec.bend ?? side);
  return a1 + a2 + (spec.wrist || 0);
}
/** an emotion's arm part-way between two arm specs (front view; preset names or {target,...} specs): target,
 *  foreshortening, hand shape, palm direction and hand angle all move together */
function emotionArmBlend(name, side, a, b, k, bendAt = 0.5, layerAt = 0.5) {
  if (k <= 0) return a;
  if (k >= 1) return b;
  const spec = (s) => (typeof s === 'string' ? EMOTION_ARMS[name][s](side, 'front', 0) : s);
  const A = spec(a), B = spec(b);
  const pd = (s) => s.palmDir || [-side * 0.9, 0, -0.45];
  const PA = pd(A), PB = pd(B);
  let ha = presetHandAng(name, side, A), hb = presetHandAng(name, side, B);
  while (hb - ha > Math.PI) hb -= 2 * Math.PI;
  while (ha - hb > Math.PI) hb += 2 * Math.PI;
  return {
    preset: typeof (k < layerAt ? a : b) === 'string' ? (k < layerAt ? a : b) : undefined,
    target: [lerp(A.target[0], B.target[0], k), lerp(A.target[1], B.target[1], k)],
    bend: k < bendAt ? (A.bend ?? side) : (B.bend ?? side), fore: lerp(A.fore || 0, B.fore || 0, k),
    layer: k < layerAt ? (A.layer || 'back') : (B.layer || 'back'),
    hand: blendHand(A.hand || 'open', B.hand || 'open', k), palmDir: [0, 1, 2].map((i) => lerp(PA[i], PB[i], k)),
    handAng: lerp(ha, hb, k),
  };
}

function drawAnger(g, t, S) {
  // arms crossed (under the console rim), jaw working side to side, brows low, eyes on the floor
  const chew = Math.sin(t * TAU * 0.55);
  const face = {
    ...EXPR.stern, browIn: -0.55, lidU: 0.3, smile: -0.25, pressed: 0.6 + 0.3 * Math.abs(chew), wide: -0.15 + 0.2 * chew,
    lookY: 0.7, lookX: 0.15 + life(t, 61, 0.06),
    blink: blinkAt(t, S.T('s09b01+3.0'), 0.2),
  };
  // a glance up at the CEO on 'responsible', then back down
  const glance = S.k(t, [['s09b01+2.3', 0], ['s09b01+2.5', 1], ['s09b01+3.3', 1], ['s09b01+3.6', 0]]);
  face.lookY = lerp(face.lookY, -0.15, glance); face.lookX = lerp(face.lookX, 0.65, glance);
  drawEmotion(g, 'ANGER', 315, 1384, 0.8, {
    t: t + OFF.ANGER, face, heat: 0.3, headTilt: 0.03 * chew, headDX: 1.2 * chew, headTurn: 0.08 + 0.1 * glance,
    // arms crossed high on the chest so the folded forearms clear the console rim
    armL: { target: [30, -201], bend: -1, layer: 'front', hand: 'fist' },
    armR: { target: [-30, -193], bend: 1, layer: 'front', hand: 'fist' },
  });
}

function drawJoy(g, t, S) {
  // glances toward the back of the room (the cage, up-left behind her), then at Consciousness;
  // the corners of the mouth lift, falter and fall; brows tilted inner-up
  const b = 's09b01';
  const look = S.k(t, [
    [`${b}+0.3`, { x: 0, y: 0.1, ht: 0 }], [`${b}+0.6`, { x: -0.7, y: -0.6, ht: -0.45 }], [`${b}+1.6`, { x: -0.7, y: -0.6, ht: -0.45 }],
    [`${b}+2.0`, { x: -0.75, y: 0.0, ht: -0.25 }], [`${b}+3.75`, { x: -0.75, y: 0.0, ht: -0.25 }],
    [`${b}+4.4`, { x: -0.3, y: 0.35, ht: -0.04 }],                      // the smile gone, her eyes drop to the console
  ]);
  // the encouraging smile tries to come (on 'responsible'), wobbles, and falls
  const smile = S.k(t, [[`${b}+2.1`, 0.0], [`${b}+2.5`, 1.15], [`${b}+2.85`, 0.72], [`${b}+3.0`, 0.95], [`${b}+3.65`, -0.2]]);
  const lidL = S.k(t, [[`${b}+2.1`, 0], [`${b}+2.5`, 0.45], [`${b}+2.9`, 0.3], [`${b}+3.65`, 0.05]]);
  const wobble = S.k(t, [[`${b}+2.6`, 0], [`${b}+2.8`, 0.9], [`${b}+3.3`, 0.7], [`${b}+3.8`, 0.2]]);   // the smile shakes
  const fall = S.k(t, [[`${b}+3.0`, 0], [`${b}+3.65`, 1]]);                                          // brows give up
  const face = {
    browIn: 0.6 + 0.3 * fall, browUp: 0.15 + 0.1 * (1 - fall), lidTilt: 0.25 + 0.2 * fall, lidU: 0.12 + 0.08 * fall, lidL,
    smile: smile - 0.22, open: 0.05 * clamp(smile), wide: 0.15 * clamp(smile), tremble: wobble, t,
    lookX: look.x + life(t, 71, 0.05), lookY: look.y + 0.25 * fall,
    blink: Math.max(blinkAt(t, S.T(`${b}+1.75`), 0.2), blinkAt(t, S.T(`${b}+3.7`), 0.3)), noBase: true,
  };
  drawEmotion(g, 'JOY', 735, 1384, 0.8, { t: t + OFF.JOY, face, noBase: true, headTurn: look.ht,
    headTilt: 0.06 * clamp(smile) - 0.04 * fall, headDY: 3 * fall, armL: 'pressButton', armR: 'pressButton' });
}

function drawSadness(g, t, S, c) {
  const close = t >= S.T('s09b02');
  // b01: at the CEO's elbow, looking back toward the cage (up-left), inner brows up, lower lip tucked in
  // b02: looks up at Consciousness, then rests a small blue hand on their sleeve
  const walkK = sstep(S.start, S.T('scene.start+0.9'), t);
  const x = lerp(612, SAD_AT[0], walkK);
  const look = S.k(t, [
    ['scene.start+1.0', { x: -0.3, y: 0.1, ht: -0.1 }], ['scene.start+1.6', { x: -0.7, y: -0.6, ht: -0.45 }],
    ['s09b01+3.3', { x: -0.7, y: -0.6, ht: -0.45 }], ['s09b01+3.8', { x: -0.55, y: -0.35, ht: -0.15 }],
    ['s09b02+0.15', { x: -0.55, y: -0.35, ht: -0.15 }], ['s09b02+0.5', { x: -0.6, y: -0.9, ht: -0.2 }],
    ['s09b02+2.4', { x: -0.6, y: -0.9, ht: -0.2 }], ['s09b02+3.1', { x: -0.45, y: -0.55, ht: -0.15 }],
  ]);
  const face = {
    ...EXPR.sad, browIn: 0.95, browUp: 0.15, lidU: 0.2, smile: -0.35, pressed: 0.55, lookX: look.x + life(t, 81, 0.04), lookY: look.y,
    tears: 0.35, blink: blinkAt(t, S.T('s09b02+0.62'), 0.35),
  };
  // the hand on the CEO's sleeve: it comes up off the console (from the pressing pose, out of sight below the rim)
  // and settles on the CEO's right forearm, the back of the hand to us (it used to appear on the sleeve in a frame)
  const touch = sstep(S.T('s09b02+1.0'), S.T('s09b02+1.7'), t);
  const s = 0.8;
  const sleeve = [508, 1212];                                   // the CEO's right forearm (arm hanging at rest)
  const loc = [(sleeve[0] - x) / s, (sleeve[1] - SAD_AT[1]) / s];
  const onSleeve = { target: loc, bend: 1, layer: 'over', hand: 'open', handAng: -Math.PI - 0.45, palmDir: [0.3, 0.35, -0.9] };
  // (in the close the pressing arm already bends its elbow down-and-out like the arm on the sleeve: the blend then
  // never flips the elbow; the cut hides the change from the medium's pose)
  const press = close ? { ...EMOTION_ARMS.SADNESS.pressButton(-1, 'front', 0), bend: 1 } : 'pressButton';
  const armL = emotionArmBlend('SADNESS', -1, press, onSleeve, ease.out(touch), 0.5, 0.12);
  drawEmotion(g, 'SADNESS', x, SAD_AT[1], s, {
    // two small shuffle steps that end with the feet together (phase 2π) instead of stopping mid-stride
    // (the shuffle goes screen-left, toward the CEO: the feet turn that way and back — the walk default pointed them right)
    t: t + OFF.SADNESS, face, headTurn: look.ht, headTilt: close ? -0.06 : 0, walk: walkK < 1 && walkK > 0 ? { phase: walkK * 2 * Math.PI } : null,
    feetTurn: -0.45 * Math.sin(walkK * Math.PI),
    armL, armR: 'pressButton',
  });
}
