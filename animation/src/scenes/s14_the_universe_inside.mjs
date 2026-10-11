// s14 · the_universe_inside · VOID_FACE / backOfMind
// The revelation: Fear's POV pushes into the dark hood, the cosmos kindles, a long drift through the stars,
// then the change happens on Fear's face (close): the fear lets go of its body on 'wasn't afraid', a soft "o"
// on 'wonder' that becomes a small trembling smile by 'amazement' (held at face size), the two-shot under the
// starry hood, "Why are you showing me this?" and the hand sliding off its shoulder in the same close, a raised
// wide that keeps the whole hood in frame while it turns back to the distance, and Fear turning (eyes, then head,
// then body) to look where the Void looks.

import { createCanvas } from '@napi-rs/canvas';
import { W, H, clamp, lerp, ease, smoothstep, blinkAt, applyCamera, drift, vignette, fbm } from '../engine.mjs';
import { withSpeech, star } from '../face.mjs';
import { drawFear } from '../chars/fear.mjs';
import { drawVoid, drawVoidGlow, drawVoidArm, drawVoidHand, toVoidLocal, voidRig, VOID_HANDS } from '../chars/void.mjs';
import { drawCosmos, drawCosmosGlyph, vfbm, hrand } from '../fx/cosmos.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawCage } from '../sets/props.mjs';

export const id = 's14';

// ---------------------------------------------------------------- staging constants (data/staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const LOOK_FEAR = { headTurn: -0.3, headDown: 0.8 };
const COSMOS_OPTS = { seed: 7, glyphs: 1 };
const CAGE_B = [430, 1630, 0.952];
const THRESH = [440, 1648, 0.97];
const VOID_ARM_B = { bend: 1 };
const APPROACH_SHOULDER = [120, -40];
const SLEEVE_CLIP_Y = 1100;
// The resting hand in s14 (QA: s13's contact pose — fingers splayed and curled across Fear's scarf and chest —
// read as a claw during the wonder). Here the fingers are together and only softly curved, they come DOWN onto
// the top of the shoulder (fingertip contact nudged up/in by SH_NUDGE, Fear-local units, still exact), and Fear's
// big head is redrawn over them, so the hand rests on the shoulder behind the head. The open padlock's shackle
// now hangs clear below the hand (it used to peek out at the fingers' edge and read as in front of them).
// The hand is first seen at s14b05, 17 s after s13's last view of it, so the change never meets a cut.
const REST_HAND = { angle: 2.3, open: 0.04, gentle: 0.5 };
const SH_NUDGE = [-4, -8];

// ---------------------------------------------------------------- sound
export const sfx = [
  { at: 's14b01+0.35', name: 'shimmer', gain: -17 },            // the hush before the first light
  { at: 's14b01+0.78', name: 'twinkle', gain: -18 },            // the single first star (note at 0.02)
  { at: 's14b01+2.2', name: 'twinkle', gain: -21 },             // "then hundreds"
  { at: 's14b02+4.08', name: 'twinkle', gain: -19 },            // '...of lights'
  { at: 's14b03+2.58', name: 'twinkle', gain: -21 },            // '...and stars'
  { at: 's14b04+1.75', name: 'shimmer', gain: -15 },            // glyphs bloom, swell peaks near 'meaning'
  { at: 's14b06+5.06', name: 'twinkle', gain: -21 },            // 'wonder' (the hands open, the soft "o")
  { at: 's14b09+0.12', name: 'cloth_rustle', gain: -17 },       // the hand slides off the shoulder
  { at: 's14b09+1.85', name: 'cloth_rustle', gain: -21, rate: 0.85 }, // the hood turns back to the distance
  { at: 's14b10+2.2', name: 'footsteps', gain: -19, until: 's14b10+2.7', fade: 0.15 }, // Fear's small turning step
];

// ---------------------------------------------------------------- helpers
function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, 720, 1280); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, 720, 1280); }
  g.restore();
}
function starlight(g, x, y, r, k) {
  if (k <= 0) return;
  g.save(); g.globalCompositeOperation = 'screen';
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, `rgba(176,150,255,${0.30 * k})`); gr.addColorStop(0.55, `rgba(110,200,255,${0.12 * k})`);
  gr.addColorStop(1, 'rgba(110,200,255,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore();
}
const sleeveFront = (g, pose) => {
  g.save(); g.beginPath(); g.rect(-1e4, SLEEVE_CLIP_Y, 2e4, 2e4); g.clip();
  drawVoidArm(g, ...VOID_B, pose, 'L', 'sleeve'); g.restore();
};
const rotAbout = (p, o, a) => {
  const c = Math.cos(a), s = Math.sin(a), dx = p[0] - o[0], dy = p[1] - o[1];
  return [o[0] + dx * c - dy * s, o[1] + dx * s + dy * c];
};
// living camera: drift in SCREEN px whatever the zoom
function cam(x, y, zoom, t, amp = 2.5) {
  if (!amp) return { x, y, zoom };
  const d = drift(t, amp, 14);
  return { x: x + d.dx / zoom, y: y + d.dy / zoom, zoom, rot: d.dr * 0.5 };
}
const zoomExp = (z0, z1, k) => z0 * Math.pow(z1 / z0, k);

let off = null;   // offscreen for the hood → full-screen cosmos crossfade
function offscreen() {
  if (!off) off = createCanvas(W, H);
  const o = off.getContext('2d');
  o.setTransform(1, 0, 0, 1, 0, 0); o.globalAlpha = 1; o.globalCompositeOperation = 'source-over';
  o.clearRect(0, 0, W, H);
  return o;
}


// ---------------------------------------------------------------- shot boundaries (cuts)
const CUT_TWO = 's14b07+0.35';    // close (the smile held at face size) → two-shot under the starry hood
const CUT_CLOSE = 's14b07+1.7';  // two-shot → close (the swallow, the question)
const CUT_WIDE = 's14b09+1.5';   // close (the hand leaves the shoulder) → raised wide (the hood turns)
const CUT_MED = 's14b10+1.6';    // raised wide → Fear turns to look where the Void looks

// ---------------------------------------------------------------- tracks
function cosmosAt(t, S) {
  return S.k(t, [
    // the single first star kindles WITH its twinkle (sfx b01+0.78, first note +0.02): reveal crosses the
    // module's first-star threshold (0.015) at ≈ +0.66 and is half-lit by +0.8 (was already visible at +0.45)
    ['scene.start', 0], ['s14b01+0.6', 0], ['s14b01+0.95', 0.055, 'out'],
    ['s14b01+1.5', 0.07], ['s14b01.end', 0.3, 'in'],                      // another… then hundreds
    ['s14b02.end', 0.62], ['s14b03.end', 0.85], ['s14b04+1.5', 1.0],
    ['s14b09+1.5', 1.0], ['s14b10+2.0', 0.6],                               // still bright while the hood turns
  ]);
}

/** The Void's pose for this instant (hand on Fear's shoulder until b09, then lifted away). */
function voidPose(t, S, cosmos, fear) {
  const head = S.k(t, [['s14b09+1.8', LOOK_FEAR], ['s14b09+3.8', STARE_B]]);
  // withdrawal = s13's approach in reverse: the fingertips slide off the shoulder (settle), the hand rises
  // beside the cage's right bars to s13's waypoint (ascend) while it slips back into the sleeve (show), and
  // only then the empty sleeve swings back to rest (reach) — the hand never passes over the TIME-OUT sign.
  // (verify pass: the slide-off now plays in the close at zoom ≈3, where s13's 0.6 s settle crossed ≈400 screen px
  // in 0.4 s — a flick; 1.0 s keeps the giant hand gentle and lets Fear's eyes follow it to the frame edge)
  const settle = S.k(t, [['s14b09+0.1', 1], ['s14b09+1.1', 0, 'inOut']]);
  const ascend = S.k(t, [['s14b09+0.8', 0], ['s14b09+1.95', 1, 'inOut']]);
  const show = S.k(t, [['s14b09+1.6', 1], ['s14b09+2.35', 0, 'inOut']]);
  const reach = S.k(t, [['s14b09+2.25', 1], ['s14b09+3.25', 0, 'inOut']]);
  const [fx, fy, fs] = THRESH;
  // Fear's near (right) shoulder, following crouch and lean (staging §1.5), nudged onto its top (SH_NUDGE)
  let sh = [fx + (36 + SH_NUDGE[0]) * fs, fy - (130 - 20 * fear.crouch - SH_NUDGE[1]) * fs];
  sh = rotAbout(sh, [fx, fy], fear.leanScreen);
  const ap = [sh[0] + APPROACH_SHOULDER[0] * fs, sh[1] + APPROACH_SHOULDER[1] * fs];
  const WP1 = [ap[0] + 15, ap[1] - 235];                 // = s13's waypoint beside the cage's right bars
  const tA = [lerp(ap[0], WP1[0], ascend), lerp(ap[1], WP1[1], ascend)];
  const tgt = [lerp(tA[0], sh[0], settle), lerp(tA[1], sh[1], settle)];
  const angle = lerp(REST_HAND.angle, Math.PI / 2 + 0.3, ease.sine(clamp(ascend * 1.15)));
  return {
    t, ...head, idle: 0.5, cosmos, cosmosOpts: COSMOS_OPTS, glow: 1.2,
    shadowSpread: S.k(t, [['s14b04', 1], ['s14b06', 0.8]]),
    handL: { ...VOID_HANDS.shoulder(toVoidLocal(...VOID_B, ...tgt), -1), ...VOID_ARM_B, open: REST_HAND.open,
      gentle: REST_HAND.gentle, angle, elbow: 0.8 * reach, show, reach, defer: 'hand' },
  };
}

// face-channel shorthands (every key carries every field, so the blends never jump)
const BR = (browUp, browIn, browSquish = 0, browUpL = 0, browUpR = 0) => ({ browUp, browIn, browSquish, browUpL, browUpR });
const LD = (lidU, lidL, lidTilt) => ({ lidU, lidL, lidTilt });
const MO = (open, smile, round, wide, pressed, tremble) => ({ open, smile, round, wide, pressed, tremble });
const GZ = (lookX, lookY) => ({ lookX, lookY });
const AR = (lx, ly, rx, ry) => ({ lx, ly, rx, ry });

/** Fear on the threshold: body + face for this instant. */
function fearState(t, S) {
  const K = (keys, e) => S.k(t, keys, e);

  // ---------- body
  const crouch = K([
    ['s14b05', 0.3],
    ['s14b10+0.2', 0.3], ['s14b10+1.2', 0, 'inOut'],                       // straightens up as the Void stares
  ]);
  const leanScreen = K([['s14b09+0.4', 0], ['s14b09+1.2', 0.09, 'outCubic'], ['s14b09+2.4', 0, 'inOut'],
    ['s14b10+2.2', 0], ['s14b10+3.05', -0.035, 'inOut']]);                 // leans after the hand; cranes toward the glow
  const facing = t < S.T('s14b10+2.52') ? 1 : -1;
  const headTurn = K([
    ['s14b05', 0.25],
    ['s14b06+4.9', 0.25], ['s14b06+5.9', 0.32],                             // 'wonder': turns a touch into the light
    ['s14b07+1.0', 0.25],
    ['s14b09+0.25', 0.25], ['s14b09+0.7', 0.45],                            // glance at its own shoulder
    ['s14b09+1.4', 0.3], ['s14b09+2.2', 0.25],
    // follows the Void's gaze (QA r2: the old 0.25 → −0.7 turn, started 0.35 s after the cut, didn't read): a held
    // beat still on the hood after the cut, then the eyes lead (b10+1.95), the head comes round 0.2 s later to a
    // clear 3/4 toward the far glow — the way the hood turned (screen-left and up) — and the body turns under it
    // (facing flips at +2.52 inside a blink). QA r3: at −1.0 the rig's 3/4 view (narrow far eye, big near eye on
    // the right) read at phone size as looking up-RIGHT, back at the sleeve; −0.45 with the pupils hard left keeps
    // both eyes open and the look unmistakably up-left at the glow. (headTurn/lookX are screen-space: fear.mjs
    // un-mirrors the face, so they need no sign change across the flip.)
    ['s14b10+2.15', 0.25], ['s14b10+3.0', -0.45, 'inOut'],
  ]);
  const tiltScreen = K([
    ['s14b05', -0.15],
    ['s14b06+2.6', -0.15], ['s14b06+3.3', -0.12],
    ['s14b06+4.9', -0.12], ['s14b06+5.9', -0.18],                            // the head tips up toward the light
    ['s14b07+1.2', -0.14],
    ['s14b08', -0.14], ['s14b08.end', -0.23],                               // tilts a few degrees as it asks
    ['s14b09+0.25', -0.2], ['s14b09+0.8', 0.07],                            // dips toward the shoulder
    ['s14b09+1.6', -0.13],
    ['s14b10+2.15', -0.14], ['s14b10+3.0', 0.05, 'inOut'],                 // crown tips away: chin up, over its shoulder
  ]) + fbm(t * 0.35, 21) * 0.015;
  const headDY = K([
    ['s14b06+2.75', 0], ['s14b06+2.95', -3], ['s14b06+3.2', -0.5], ['s14b06+3.4', -2.5], ['s14b06+3.7', 0], // breath of a laugh
    ['s14b06+4.9', 0], ['s14b06+5.9', -3], ['s14b07+0.6', -3.4], ['s14b07+1.5', 0],                         // lifts on 'wonder'
    ['s14b07+2.0', 0], ['s14b07+2.12', 3.2], ['s14b07+2.3', 0],             // swallow
    ['s14b07+2.3', 0], ['s14b07+2.5', -1.8], ['s14b07+2.8', 0],             // small breath in, then the question
    ['s14b10+2.42', 0], ['s14b10+2.52', 2.5], ['s14b10+2.72', 0],           // weight shift on the turn
  ]);

  // arms (first seen at b05, 17 s after s13's last view of Fear): the self-hug from s13 relaxes a little; on
  // 'wasn't afraid' the arms uncross and drop, hanging loose; on 'wonder' they open out from the sides, palms out,
  // and rise a little more on 'amazement' (held through the cut); for the question the hands meet low in front.
  // At the end the hands clasp at the scarf (= s15). The elbow sides (IK bends) change only while both arms hang
  // dead straight (b06+3.1, and b07+1.05 in the two-shot), so no elbow ever flips on screen: the hug keeps s13's
  // bends, the open arms have both elbows down, the hands-in-front pose has both elbows out.
  // (The padlock hangs at Fear-local ≈ (72,−106): the right hand stays clear of it.)
  const A = K([
    ['s14b05', AR(-20, -106, 14, -118)],
    ['s14b05+3.8', AR(-24, -100, 19, -103)],
    ['s14b06+1.5', AR(-24, -100, 19, -103)],
    ['s14b06+3.1', AR(-39, -36, 37, -36)],                                  // 'wasn't afraid': uncross, drop loose
    ['s14b06+4.9', AR(-39, -37, 37, -37)],
    // (the right one opens less: its side is under the Void's hand, and its palm must stay below the padlock)
    ['s14b06+5.9', AR(-68, -80, 50, -56), 'inOut'],                         // 'wonder': arms open out, palms out
    ['s14b06+6.4', AR(-69, -81, 51, -57)],
    ['s14b06+7.2', AR(-73, -91, 55, -63)],                                  // 'amazement': they rise a little
    ['s14b07+0.6', AR(-74, -93, 56, -64)],
    ['s14b07+1.05', AR(-39, -36, 37, -36), 'inOut'],                        // (two-shot) down, straight: the elbows
    ['s14b07+1.6', AR(-12, -67, 12, -67), 'inOut'],                         // switch sides; the hands meet low in front
    ['s14b09+0.5', AR(-12, -67, 12, -67)],
    ['s14b09+1.1', AR(-16, -69, 20, -70), 'inOut'],                         // part a little as it leans after the hand
    ['s14b09+2.4', AR(-12, -67, 12, -67), 'inOut'],
  ]);
  const clasp = K([['s14b10+3.2', 0], ['s14b10+4.0', 1, 'inOut']]);
  const palm = K([['s14b06+5.0', 0], ['s14b06+5.5', 1], ['s14b07+0.9', 1], ['s14b07+1.2', 0]]) > 0.5;
  let armL, armR;
  if (facing > 0) {
    // elbow sides switch only at the two instants when both arms hang dead straight (b06+3.1, b07+1.05)
    const open = t >= S.T('s14b06+3.1') && t < S.T('s14b07+1.05');
    const out = t >= S.T('s14b07+1.05');
    armL = { target: [A.lx, A.ly], bend: out ? -1 : 1, front: true, hand: palm ? 'palm' : 'open' };
    armR = { target: [A.rx, A.ry], bend: open ? -1 : 1, front: true, hand: palm ? 'palm' : 'open' };
  } else {
    armL = { target: [lerp(-12, -7, clasp), lerp(-67, -127, clasp)], bend: -1, front: true, hand: clasp > 0.5 ? 'fist' : 'open' };
    armR = { target: [lerp(12, 7, clasp), lerp(-67, -124, clasp)], bend: 1, front: true, hand: clasp > 0.5 ? 'fist' : 'open' };
  }

  // ---------- face channels
  const brows = K([
    ['s14b05', BR(0.12, 0.85, 0.45)],
    ['s14b05+0.4', BR(0.12, 0.85, 0.45)],
    ['s14b05+1.9', BR(0.48, 0.38)],                                         // un-knot, open
    ['s14b06+1.4', BR(0.5, 0.34)],
    ['s14b06+2.6', BR(0.6, 0.24)],                                          // 'wasn't afraid': the knot is gone
    ['s14b06+3.1', BR(0.62, 0.18)],
    ['s14b06+4.6', BR(0.62, 0.2)],
    ['s14b06+5.4', BR(0.86, 0.3)],                                          // 'wonder': brows lift high
    ['s14b06+6.6', BR(0.8, 0.4)],                                           // 'amazement': lifted, softly moved
    ['s14b07+1.5', BR(0.66, 0.4)],
    ['s14b07+1.95', BR(0.7, 0.5)],                                          // gathering itself to speak
    ['s14b08+0.1', BR(0.55, 0.48)],                                         // gently raised, asking
    ['s14b08.end', BR(0.6, 0.5)],
    ['s14b09+0.25', BR(0.6, 0.5)],
    ['s14b09+0.7', BR(0.22, 0.72, 0.15)],                                   // dip: missing the hand
    ['s14b09+1.6', BR(0.3, 0.6, 0.1, 0.18, -0.05)],                         // puzzled, watching the hood turn
    ['s14b10+2.0', BR(0.32, 0.55, 0.1, 0.15, 0)],
    ['s14b10+2.35', BR(0.5, 0.4)],                                          // the eyes find the glow
    ['s14b10+2.75', BR(0.5, 0.4)],
    ['s14b10+3.15', BR(-0.2, 0.05, 0.55)],                                  // narrow to see (peering)
    ['s14b10+3.4', BR(-0.2, 0.05, 0.55)],
    ['s14b10+3.85', BR(0.7, 0.45)],                                         // widen: they're looking back
  ]);
  const lids = K([
    ['s14b05', LD(0.1, 0.14, 0.34)],
    ['s14b05+1.2', LD(0.12, 0.14, 0.3)],
    ['s14b05+2.7', LD(-0.12, 0.05, 0.08)],                                  // heavy lids rise, softly
    ['s14b06+2.8', LD(-0.12, 0.05, 0.08)],
    ['s14b06+3.2', LD(-0.08, 0.16, 0.05)],                                  // the breath of a laugh lifts the cheeks
    ['s14b06+4.5', LD(-0.12, 0.08, 0.04)],
    ['s14b06+5.3', LD(-0.26, 0.02, 0.02)],                                  // 'wonder': upper lids high, eyes wide
    ['s14b06+6.5', LD(-0.18, 0.2, 0.04)],                                   // the smile lifts the lower lids; uppers stay high
    ['s14b07+1.2', LD(-0.14, 0.16, 0.05)],
    ['s14b08', LD(-0.08, 0.12, 0.12)],
    ['s14b09+0.3', LD(-0.08, 0.12, 0.12)],
    ['s14b09+0.7', LD(0.22, 0.1, 0.25)],                                    // eyes drop to the shoulder
    ['s14b09+1.5', LD(-0.02, 0.05, 0.15)],
    ['s14b10+2.7', LD(-0.04, 0.05, 0.1)],
    ['s14b10+3.15', LD(0.15, 0.5, -0.12)],                                  // narrow: lower lids rise, peering
    ['s14b10+3.4', LD(0.15, 0.5, -0.12)],
    ['s14b10+3.85', LD(-0.2, 0.0, 0.1)],                                    // widen
  ]);
  const mouth = K([
    ['s14b05', MO(0.07, -0.32, 0, 0.05, 0, 0)],
    ['s14b05+1.5', MO(0.07, -0.3, 0, 0.05, 0, 0)],
    ['s14b05+2.8', MO(0.27, -0.06, 0.34, -0.05, 0, 0.1)],                   // falls open
    // lower lip quivers: the rig's lip tremble is ~0.07·mouthW·tremble, i.e. 1.4 screen px at 0.32 in this
    // close (invisible on a phone); 0.62 gives a readable ~2.7 px quiver while the mouth stays soft and open
    ['s14b05+3.6', MO(0.25, -0.08, 0.32, -0.05, 0, 0.62)],
    ['s14b06+1.6', MO(0.22, -0.06, 0.3, -0.05, 0, 0.55)],
    ['s14b06+2.75', MO(0.2, -0.04, 0.28, -0.05, 0, 0.3)],
    ['s14b06+2.95', MO(0.32, 0.12, 0.12, 0.1, 0, 0.1)],                     // a breath of a laugh
    ['s14b06+3.25', MO(0.16, 0.04, 0.2, 0, 0, 0.15)],
    ['s14b06+3.45', MO(0.25, 0.1, 0.1, 0.08, 0, 0.1)],
    ['s14b06+3.9', MO(0.12, 0.03, 0.2, 0, 0, 0.12)],
    ['s14b06+4.45', MO(0.11, 0.02, 0.2, 0, 0, 0.1)],
    ['s14b06+5.1', MO(0.32, 0.0, 0.62, -0.1, 0, 0.18)],                     // 'It felt wonder': a soft "o"
    ['s14b06+5.45', MO(0.3, 0.06, 0.56, -0.08, 0, 0.25)],
    ['s14b06+6.15', MO(0.15, 0.42, 0.14, 0.06, 0, 0.6)],                    // ...that melts into a small smile
    ['s14b06+7.2', MO(0.13, 0.56, 0.06, 0.1, 0, 0.62)],                     // 'amazement': trembling, held
    ['s14b07+0.35', MO(0.13, 0.54, 0.06, 0.1, 0, 0.55)],
    ['s14b07+1.5', MO(0.12, 0.3, 0.12, 0.04, 0, 0.25)],
    // b07 (close again, from +1.7): the smile lingers as the lips come together; it swallows; one small breath in;
    // then it asks
    ['s14b07+1.85', MO(0.06, 0.12, 0.12, 0, 0, 0.1)],
    ['s14b07+2.0', MO(0.0, 0.02, 0.0, 0, 0.3, 0)],
    ['s14b07+2.12', MO(0.0, -0.02, 0.0, -0.1, 0.65, 0)],                    // swallow
    ['s14b07+2.3', MO(0.04, 0.0, 0.1, 0, 0.1, 0)],
    ['s14b07+2.55', MO(0.12, 0.0, 0.25, 0, 0, 0)],                          // small breath in
    ['s14b08', MO(0.06, 0.06, 0.1, 0, 0, 0.12)],
    ['s14b08.end', MO(0.06, 0.04, 0.1, 0, 0, 0.12)],
    ['s14b08.end+0.4', MO(0.1, 0.0, 0.15, 0, 0, 0.1)],                      // lips parted, waiting
    ['s14b09+0.3', MO(0.1, 0.0, 0.15, 0, 0, 0.1)],
    ['s14b09+0.8', MO(0.03, -0.18, 0.0, -0.08, 0.2, 0.05)],                 // missing it
    ['s14b09+1.8', MO(0.07, -0.12, 0.1, 0, 0, 0)],
    ['s14b10+2.7', MO(0.06, -0.08, 0.1, 0, 0, 0)],
    ['s14b10+3.15', MO(0.0, -0.05, 0.0, -0.05, 0.3, 0)],                    // squinting
    ['s14b10+3.4', MO(0.0, -0.05, 0.0, -0.05, 0.3, 0)],
    ['s14b10+3.85', MO(0.2, 0.0, 0.4, -0.05, 0, 0.1)],                      // widen: a soft "oh"
  ]);
  const eyes = K([
    ['s14b05', { pupil: 0.82, sparkle: 0.85 }],
    ['s14b05+0.5', { pupil: 0.82, sparkle: 0.9 }],
    ['s14b05+2.6', { pupil: 1.32, sparkle: 1 }],
    ['s14b06+4.6', { pupil: 1.32, sparkle: 1 }],
    ['s14b06+5.4', { pupil: 1.45, sparkle: 1 }],                            // 'wonder': the pupils bloom
    ['s14b07+1.2', { pupil: 1.32, sparkle: 1 }],
    ['s14b09+1.0', { pupil: 1.28, sparkle: 1 }],
    ['s14b10+2.0', { pupil: 1.15, sparkle: 0.85 }],
    ['s14b10+3.15', { pupil: 0.95, sparkle: 0.45 }],
    ['s14b10+3.85', { pupil: 1.3, sparkle: 0.6 }],
  ]);
  // gaze (with micro-saccades that "search the stars")
  const gaze = K([
    ['s14b05', GZ(0.35, -1)],
    ['s14b08+0.5', GZ(0.35, -1)], ['s14b08+0.58', GZ(0.5, -0.92)],
    ['s14b08+1.32', GZ(0.5, -0.92)], ['s14b08+1.4', GZ(0.26, -1)],
    ['s14b08.end+0.6', GZ(0.26, -1)], ['s14b08.end+0.68', GZ(0.38, -0.98)],
    ['s14b09+0.2', GZ(0.38, -0.98)], ['s14b09+0.45', GZ(0.8, 0.4)],          // glance at its own shoulder
    ['s14b09+1.0', GZ(0.8, 0.4)], ['s14b09+1.3', GZ(0.62, -0.7)],             // up the withdrawing arm
    ['s14b09+1.7', GZ(0.5, -0.9)], ['s14b09+3.4', GZ(0.32, -1)],              // to the hood as it turns
    ['s14b10+1.95', GZ(0.32, -1)], ['s14b10+2.2', GZ(-0.72, -0.58)],         // eyes lead to where it looks
    ['s14b10+3.0', GZ(-0.8, -0.64)],                                         // the head has come round
  ]);
  const searching = S.talking('FEAR', t) * 0.05;
  const micro = (s) => fbm(t * 0.45, s) * (0.05 + searching);
  // tears of wonder
  const tears = K([['s14b05', 0.38], ['s14b05+0.6', 0.4], ['s14b05+2.4', 0.92], ['s14b09', 0.9], ['s14b10+3.0', 0.82], ['s14b10+3.6', 0.95]]);
  // both drops run down the screen-LEFT cheek (the right cheek is the hand's side). One spills (b05+2.45, squeezed
  // out by a quick blink), then a second (b05+4.25); the track restarts only after the first drop has faded out
  const drop = (a, b) => clamp((t - S.T(a)) / (S.T(b) - S.T(a)), 0, 1);
  const d1 = drop('s14b05+2.45', 's14b05+4.15'), d2 = drop('s14b05+4.25', 's14b05+5.95');
  const tearL = t < S.T('s14b05+4.2') ? d1 : d2;
  const tearR = 0;
  const stream = K([['s14b05+2.7', 0], ['s14b05+4.6', 0.32], ['s14b09', 0.3], ['s14b10.end', 0.24]]);
  const blush = K([['s14b06+5.3', 0], ['s14b06+6.4', 0.6], ['s14b07+0.5', 0.6], ['s14b08.end', 0.45], ['s14b10', 0.3]]);
  // wide eyes through the wonder: no slow blinks (they read as sleepy) — one quick blink squeezes out the first
  // tear, one rides the breath of a laugh, one after 'amazement' while the smile holds
  const blink = Math.max(
    blinkAt(t, S.T('s14b05+2.3'), 0.16),
    blinkAt(t, S.T('s14b06+3.55'), 0.16),
    blinkAt(t, S.T('s14b06+7.45'), 0.18),
    blinkAt(t, S.T('s14b07+2.04'), 0.2),      // with the swallow
    blinkAt(t, S.T('s14b08.end+0.2'), 0.3),   // waiting for an answer
    blinkAt(t, S.T('s14b09+1.08'), 0.18),     // gaze shift up the arm
    blinkAt(t, S.T('s14b09+3.05'), 0.18),
    blinkAt(t, S.T('s14b10+2.42'), 0.24),     // the head comes round: lids shut across the facing flip at +2.52
    blinkAt(t, S.T('s14b10+3.42'), 0.17),     // "did I see that right?"
  );

  let face = {
    ...brows, ...lids, ...mouth, ...eyes,
    lookX: gaze.lookX + micro(31), lookY: gaze.lookY + micro(37) * 0.6,
    tears, tearL, tearR, stream, blush, blink, noAutoBlink: true,
  };
  face = withSpeech(face, S.lip('FEAR', t), 0.72);   // a whisper, barely above a breath

  return {
    crouch, leanScreen, facing,
    pose: {
      t, facing, crouch, tremble: 0, lean: leanScreen * facing, headTilt: tiltScreen * facing, headTurn, headDY,
      breathe: 0.9, armL, armR, face,
    },
  };
}

// ---------------------------------------------------------------- the back-of-the-mind stage
// PERFORMANCE: in the static closes and the pull-back everything behind Fear (set, Void, cage, the sleeve in
// front of the cage) is still, so it is rendered once into a world-space "plate" (cached, keyed by shot/zoom
// bucket, built at a FIXED time so any frame renders identically in any order) and blitted under the live
// camera; Fear, the glow, the starlight, the hand and the low mist stay live. The glow is rendered at 1/4 res.
const plates = new Map();
function getPlate(key, rect, res, build) {
  let p = plates.get(key);
  if (p) return p;
  if (plates.size >= 5) plates.delete(plates.keys().next().value);
  const ww = rect[2] - rect[0], wh = rect[3] - rect[1];
  const c = createCanvas(Math.ceil(ww * res), Math.ceil(wh * res));
  const pg = c.getContext('2d');
  pg.scale(c.width / ww, c.height / wh);
  pg.translate(-rect[0], -rect[1]);
  build(pg);
  p = { c, rect };
  plates.set(key, p);
  return p;
}
/** world rect seen by a camera at (x, y, zoom), grown by `m` screen px for drift */
const frameRect = (x, y, z, m = 8) => [x - (360 + m) / z, y - (640 + m) / z, x + (360 + m) / z, y + (640 + m) / z];
const unionRect = (a, b) => [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])];

let glowC = null;
function glowLowRes(g, camera, vp) {
  if (!(vp.cosmos > 0.005)) return;
  if (!glowC) glowC = createCanvas(W / 4, H / 4);
  const o = glowC.getContext('2d');
  o.setTransform(1, 0, 0, 1, 0, 0);
  o.globalCompositeOperation = 'source-over'; o.globalAlpha = 1;
  o.clearRect(0, 0, W / 4, H / 4);
  o.scale(0.25, 0.25);
  applyCamera(o, camera);
  drawVoidGlow(o, ...VOID_B, vp);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'screen';
  g.drawImage(glowC, 0, 0, W, H); g.restore();
}


/** Fear's head outline as a path, built in the current (camera) space: replicates drawFear's transform chain
 *  (fear.mjs: feet → scale → facing → lean → neck (NECK_Y −148 + crouch·20 + breath·1.2 + headDY) → headTilt →
 *  head ellipse (turn·3, −66) 74×68), grown by `grow` units. tremble is 0 in s14 (no shiver offsets). */
function headPath(g, fx, fy, fs, p, grow = 0, shift = [0, 0]) {
  const facing = p.facing || 1;
  const br = Math.sin(p.t * 2 * Math.PI * (p.breathRate || 0.28)) * (p.breathe ?? 1);
  g.save();
  g.translate(fx, fy); g.scale(fs, fs); g.scale(facing, 1);
  g.rotate(p.lean || 0);
  g.translate(p.headDX || 0, -148 + (p.crouch || 0) * 20 + br * 1.2 + (p.headDY || 0));
  g.rotate(p.headTilt || 0);
  const cx = clamp(p.headTurn ?? 0, -1, 1) * facing * 3;
  g.ellipse(cx + shift[0] * facing, -66 + shift[1], 74 + grow, 68 + grow, 0, 0, Math.PI * 2);
  g.restore();
}


/** A faint cool rim of cosmos light on the hood side (upper right) of Fear's head: a crescent inside the head. */
function fearRim(g, fx, fy, fs, pose, k) {
  if (k <= 0.01) return;
  g.save();
  g.beginPath(); headPath(g, fx, fy, fs, pose, 0); g.clip();
  g.globalCompositeOperation = 'screen';
  for (const [d, a] of [[13, 0.1], [6, 0.2]]) {
    g.beginPath();
    headPath(g, fx, fy, fs, pose, 0);
    headPath(g, fx, fy, fs, pose, 0, [-0.5 * d, 0.86 * d]);   // the head moved AWAY from the light (up-right)
    g.fillStyle = `rgba(165,195,255,${a * k})`;
    g.fill('evenodd');
  }
  g.restore();
}

/** The resting hand, softened: the cosmos glow is drawn over it (it was drawn under it, leaving a pitch-black
 *  claw) and, once the cosmos is revealed, a few faint stars twinkle on the back of the hand and along the
 *  middle finger (placed along the wrist → fingertip line, well inside the silhouette, so no clip is needed). */
const HAND_STARS = [[0.24, -0.1, 2.6, 0.0], [0.38, 0.13, 2.0, 1.7], [0.5, -0.05, 2.8, 3.1], [0.66, 0.02, 1.9, 4.4],
  [0.84, 0.0, 1.7, 5.6], [0.3, 0.02, 1.6, 2.4]];
function drawHandSoft(g, camera, vp, t, cosmos, fearPose) {
  g.save();
  applyCamera(g, camera);
  if (fearPose) {
    // the fingers rest on the shoulder BEHIND Fear's big head: the hand is clipped out of the head (grown by
    // half the head's 3.2-unit outline, so the outline stays whole and no gap opens)
    g.beginPath(); g.rect(-1e4, -1e4, 3e4, 3e4); headPath(g, ...THRESH, fearPose, 1.6); g.clip('evenodd');
  }
  drawVoidHand(g, ...VOID_B, vp, 'L');
  const k = clamp((cosmos - 0.55) / 0.45) * clamp((vp.handL.show - 0.85) / 0.15);
  if (k > 0.02) {
    const h = voidRig(vp).handL, s = VOID_B[2];
    const wr = [VOID_B[0] + h.wrist[0] * s, VOID_B[1] + h.wrist[1] * s];
    const tip = [VOID_B[0] + h.tip[0] * s, VOID_B[1] + h.tip[1] * s];
    const ux = tip[0] - wr[0], uy = tip[1] - wr[1], len = Math.hypot(ux, uy) || 1;
    const nx = -uy / len, ny = ux / len, hw = 34 * s;
    for (const [a, b, r, ph] of HAND_STARS) {
      const tw = 0.5 + 0.5 * Math.sin(t * (1.1 + ph * 0.13) + ph * 2.1);
      g.fillStyle = `rgba(232,224,255,${k * (0.2 + 0.6 * tw * tw * tw)})`;
      star(g, wr[0] + ux * a + nx * b * hw, wr[1] + uy * a + ny * b * hw, r * (0.75 + 0.35 * tw));
    }
  }
  g.restore();
}

/**
 * opts: cosmos, starK, fear (false = no Fear/cage, hood POV),
 *       plate: { key, rect, res, tb }  (static background), tb: frozen time for the set + cage (pull-back),
 *       hoodOff: the hood is out of frame (its cosmos is not drawn)
 */
function drawStage(g, t, S, camera, opts = {}) {
  const cosmos = opts.cosmos;
  const fear = fearState(t, S);
  const vp = voidPose(t, S, cosmos, fear);
  const tb = opts.plate ? opts.plate.tb : opts.tb ?? t;
  const st = { t, lightsDim: 0.35, mist: 0.5, alarm: 0 };
  const handOut = vp.handL.show > 0.001 || vp.handL.reach > 0.001;
  const noArm = !!(opts.plate && opts.plate.noArm);
  const back = (c, tt, v) => {
    drawHQ(c, 'backOfMind', { ...st, t: tt });
    // hoodOff: the hood is far above the frame — skip its cosmos (the glow still uses the real value);
    // noArm: a plate without the left arm (it moves): the sleeve is drawn live in front of the cage instead
    let vv = opts.hoodOff ? { ...v, cosmos: 0 } : v;
    if (noArm) vv = { ...vv, handL: { ...v.handL, defer: true } };
    drawVoid(c, ...VOID_B, vv);
    if (opts.fear === false) return;
    const cst = { t: tt, door: 0.9, locked: 0, rust: 0, dim: 0 };
    drawCage(c, ...CAGE_B, { ...cst, layer: 'back' });
    drawCage(c, ...CAGE_B, { ...cst, layer: 'front' });
    if (!noArm && (v.handL.show > 0.001 || v.handL.reach > 0.001)) sleeveFront(c, v);
  };
  g.save();
  applyCamera(g, camera);
  if (opts.plate) {
    const P = opts.plate;
    // the plate's Void pose is evaluated AT the frozen instant (not "this frame's pose at tb"): shadowSpread
    // eases through b05, so a plate first built mid-shot used to differ from one built at the shot's start,
    // i.e. the picture depended on which frame a render process happened to reach first (chunked renders)
    const pl = getPlate(P.key, P.rect, P.res, (pg) => back(pg, P.tb, voidPose(P.tb, S, cosmosAt(P.tb, S), fearState(P.tb, S))));
    g.drawImage(pl.c, pl.rect[0], pl.rect[1], pl.rect[2] - pl.rect[0], pl.rect[3] - pl.rect[1]);
    // (noArm plates are only used where the whole visible sleeve lies below SLEEVE_CLIP_Y, i.e. in front of the cage)
    if (noArm && handOut) sleeveFront(g, vp);
  } else {
    back(g, tb, vp);
  }
  if (opts.fear !== false) {
    const [fx, fy, fs] = THRESH;
    drawFear(g, fx, fy, fs, fear.pose);
  }
  g.restore();
  if (opts.fear !== false) {
    const [fx, fy, fs] = THRESH;
    // the hand on the shoulder, behind Fear's head; the glow and the starlight fall on both
    if (vp.handL.show > 0.001) drawHandSoft(g, camera, vp, t, cosmos, fear.pose);
    glowLowRes(g, camera, vp);
    g.save();
    applyCamera(g, camera);
    const sk = opts.starK ?? cosmos;
    starlight(g, fx + 25 * fs, fy - 250 * fs, 190 * fs, sk);
    fearRim(g, fx, fy, fs, fear.pose, sk);
    drawHQForeground(g, 'backOfMind', st);
    g.restore();
  } else {
    g.save(); applyCamera(g, camera); drawHQForeground(g, 'backOfMind', st); g.restore();
  }
}

// ---------------------------------------------------------------- shots
// close on Fear (b05, b07–b08). Staging gives {450,1430,3.0}; pushed to 3.3 and down to y 1500 so the face
// sits on the upper third and the TIME-OUT sign leaves the top of the frame (it fought the face for attention)
const CLOSE = [445, 1500, 3.3];
// the two-shot from the side after 'amazement' (b07). Staging gives {560,1000,0.85}, which crops the bowed hood
// at the frame top; a little higher and wider keeps the whole starry hood above tiny Fear
const TWO_A = [556, 935, 0.83], TWO_B = [560, 922, 0.8];
// the close eases back to this as the hand leaves the shoulder (b09): Fear's face, its right shoulder and the
// space it leans into
const CLOSE_OUT = [462, 1502, 2.95];
// the raised wide for the hood's turn (b09–b10): the whole hood stays in frame from LOOK_FEAR to STARE_B
// (peak y≈56 in STARE_B), the far glow screen-left, Fear's face above the bottom 15 %
const WIDE = [560, 868, 0.75];
// Fear follows the Void's gaze (b10 → end): medium, the far glow up-left where Fear turns to, the Void's empty
// sleeve and robe on the right; a slow push-in while it looks
const MED_A = [336, 1300, 1.78], MED_B = [338, 1302, 1.86];

function hoodPOV(g, t, S, cosmos) {
  // Fear's POV pushing slowly into the bowed hood: {679,336,4.5} → {679,336,7.0}
  const k = S.k(t, [['scene.start', 0], ['s14b02+0.5', 1]]);
  const z = zoomExp(4.5, 7.0, k);
  drawStage(g, t, S, cam(679, 336, z, t, 1.5), { cosmos, fear: false });
}

// The full-screen shot's "bits and pieces of meaning", laid out here instead of by drawCosmos (called with
// glyphs 0): the same table, order, fade-in, drift, pulse and sprites as src/fx/cosmos.mjs's glyph layer, with ONE
// change — the music note moves from (0.4, 0.62), where it drifted under the b04 caption box (play-time captions
// at y ≈ 972–1072, x ≈ 147–553; only its dot showed below the box, on the very line about meaning), to the open
// violet haze right of the heart, between the pencil, the key and the lower galaxy (screen ≈ (498,647) → (483,609)).
const FULL_GLYPHS = [
  { name: 'heart', col: '#ff9fc6', nx: -0.06, ny: 0.2, sz: 1.12 },
  { name: 'sun', col: '#ffd57a', nx: 0.55, ny: -0.28, sz: 1.15 },
  { name: 'fear', col: '#cdbdf5', nx: -0.42, ny: 0.34, sz: 1.2 },
  { name: 'note', col: '#9fe8ff', nx: 0.36, ny: 0.02, sz: 0.95 },        // cosmos.mjs: (0.4, 0.62)
  { name: 'house', col: '#ffcf8a', nx: -0.6, ny: -0.6, sz: 1.0 },
  { name: 'handprint', col: '#ffc6a8', nx: 0.6, ny: -0.74, sz: 0.85 },
  { name: 'speech', col: '#e9e3ff', nx: -0.18, ny: -0.5, sz: 0.85 },
  { name: 'key', col: '#ffd36b', nx: 0.68, ny: 0.06, sz: 0.78 },
  { name: 'notebook', col: '#ffe9b8', nx: -0.72, ny: -0.02, sz: 0.9 },
  { name: 'leaf', col: '#9ff0b5', nx: -0.3, ny: 0.76, sz: 0.8 },
  { name: 'pencil', col: '#ffe3a3', nx: 0.14, ny: -0.16, sz: 0.72 },
];
function cosmosGlyphsFull(g, cx, cy, rx, ry, t, reveal, amt, seed = 7) {
  const gk0 = smoothstep(0.58, 0.98, reveal) * amt;
  if (!(gk0 > 0.003)) return;
  const m = g.getTransform();
  const S0 = Math.min(rx, ry), R = S0 * (Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) || 1);
  const N = FULL_GLYPHS.length;
  const small = clamp((260 - R) / 200);
  const nGf = clamp(4 + R / 38, 5, N), nG = Math.min(N, Math.ceil(nGf + 0.5));
  const gsz = S0 * lerp(0.09, 0.115, small);
  g.save();
  g.beginPath(); g.rect(cx - rx, cy - ry, rx * 2, ry * 2); g.clip();
  g.globalCompositeOperation = 'source-over';
  for (let i = 0; i < nG; i++) {
    const G = FULL_GLYPHS[i];
    const ga = smoothstep(i * 0.04, i * 0.04 + 0.55, gk0) * clamp(nGf + 0.5 - i);
    if (ga <= 0.003) continue;
    const sd = seed * 13 + i * 17;
    const x = cx + (G.nx + vfbm(t * 0.045 + i * 2.3, sd) * 0.07 + Math.sin(t * 0.07 + i) * 0.025) * rx;
    const y = cy + (G.ny + vfbm(t * 0.04 + i * 3.7, sd + 1) * 0.06 + Math.cos(t * 0.06 + i * 1.7) * 0.02) * ry;
    const rot = vfbm(t * 0.05 + i, sd + 2) * 0.35;
    const pulse = 0.85 + 0.15 * Math.sin(t * (0.6 + hrand(i, seed) * 0.5) + i * 1.3);
    const depth = lerp(0.68, 1, clamp((G.sz - 0.7) / 0.5));
    drawCosmosGlyph(g, G.name, x, y, gsz * G.sz, G.col, { alpha: ga * pulse * depth, rot });
  }
  g.restore();
}

function cosmosFull(g, t, S, cosmos) {
  // full-screen universe: a slow drift (≈0.3 px/frame) and a 1.00 → 1.06 scale over b02–b04
  const u = S.k(t, [['s14b02-0.5', 0], ['s14b05', 1]], 'linear');
  const sc = S.k(t, [['s14b02-0.5', 1], ['s14b04.end', 1.06]]);
  const cx = lerp(395, 325, u), cy = lerp(685, 595, u);
  g.fillStyle = '#020108';
  g.fillRect(0, 0, W, H);
  // the glyphs are b04's discovery ("bits and pieces of meaning"): they arrive with the line, full by 'meaning'
  const glyphs = S.k(t, [['s14b04-0.4', 0], ['s14b04+2.72', 1, 'inOut']]);
  const rx = 410 * sc, ry = 700 * sc;
  drawCosmos(g, cx, cy, rx, ry, t, { reveal: cosmos, seed: 7, glyphs: 0 });
  cosmosGlyphsFull(g, cx, cy, rx, ry, t, cosmos, glyphs);
  // on 'meaning' the heart (the cosmos module's glyph 0, near the centre) glows briefly brighter
  const pulse = S.k(t, [['s14b04+2.62', 0], ['s14b04+3.0', 1, 'out'], ['s14b04+4.6', 0, 'sine']]);
  if (pulse > 0.002) {
    const hx = cx + (-0.06 + vfbm(t * 0.045, 91) * 0.07 + Math.sin(t * 0.07) * 0.025) * rx;
    const hy = cy + (0.2 + vfbm(t * 0.04, 92) * 0.06 + Math.cos(t * 0.06) * 0.02) * ry;
    const r = 120;
    g.save(); g.globalCompositeOperation = 'screen';
    const gr = g.createRadialGradient(hx, hy, 0, hx, hy, r);
    gr.addColorStop(0, `rgba(255,170,215,${0.42 * pulse})`); gr.addColorStop(0.35, `rgba(255,140,200,${0.16 * pulse})`);
    gr.addColorStop(1, 'rgba(255,140,200,0)');
    g.fillStyle = gr; g.fillRect(hx - r, hy - r, 2 * r, 2 * r); g.restore();
  }
}


// b06 → b07: the close breathes out, anchored on Fear's face, to a big close-up that still holds the face at
// ≈ 2.7 (≥ 2.6) through 'amazement': the open hands, the smile and the blush stay at face size for ≈ 2.5 s, and
// only after the line (b06.end + 0.7) does it cut to the two-shot under the starry hood (QA: the old move reached
// 2.3 on 'wonder' and cut on 'amazement' to a wide where Fear's face was ≈ 45 px).
const FACE_P = [440, 1454];
const CLOSE_PUSH = 1.05, Z_A = CLOSE[2] * CLOSE_PUSH;     // the close's zoom when the pull-back starts
const Z_M = 2.7;                                           // the big close-up the close breathes out to
const S0 = [360 + (FACE_P[0] - CLOSE[0]) * Z_A, 640 + (FACE_P[1] - CLOSE[1]) * Z_A];
const S_M = [356, 540];                                    // Fear's face on screen at the end of the move
function pullCam(k) {
  const zoom = zoomExp(Z_A, Z_M, k);
  const sx = lerp(S0[0], S_M[0], k), sy = lerp(S0[1], S_M[1], k);
  return { x: FACE_P[0] - (sx - 360) / zoom, y: FACE_P[1] - (sy - 640) / zoom, zoom };
}
const pullCamAtZoom = (z) => pullCam(clamp(Math.log(z / Z_A) / Math.log(Z_M / Z_A)));

// "a soft shimmer passes through them" (b06, VOID): a faint band of light crossing the stars in the hood
// opening, clipped inside the opening so the hood shell itself stays unlit (staging §5.4)
const HOOD_LF = (() => { const r = voidRig({ ...LOOK_FEAR }); return { x: VOID_B[0] + r.face[0] * VOID_B[2],
  y: VOID_B[1] + r.face[1] * VOID_B[2], rx: r.faceRx * VOID_B[2], ry: r.faceRy * VOID_B[2] }; })();
function hoodShimmer(g, camera, k) {
  if (k <= 0 || k >= 1) return;
  const { x, y, rx, ry } = HOOD_LF;
  const a = Math.sin(Math.PI * k);                         // fades in and out as it passes
  const p = lerp(-1.4, 1.4, k);                            // band centre along the diagonal (opening radii)
  g.save(); applyCamera(g, camera);
  g.beginPath(); g.ellipse(x, y + ry * 0.08, rx * 0.8, ry * 0.82, 0, 0, Math.PI * 2); g.clip();
  g.globalCompositeOperation = 'screen';
  const ux = 0.6, uy = 0.8, cx = x + ux * p * rx, cy = y + uy * p * ry, w = rx * 0.9;
  const gr = g.createLinearGradient(cx - ux * w, cy - uy * w, cx + ux * w, cy + uy * w);
  gr.addColorStop(0, 'rgba(190,170,255,0)'); gr.addColorStop(0.5, `rgba(210,195,255,${0.42 * a})`);
  gr.addColorStop(1, 'rgba(150,220,255,0)');
  g.fillStyle = gr; g.fillRect(x - rx * 2, y - ry * 2, rx * 4, ry * 4);
  g.restore();
}

export function render(g, t, S) {
  const cosmos = cosmosAt(t, S);
  const T = (a) => S.T(a);
  const cold = S.k(t, [['s14b01', 0.65], ['s14b02.end', 0.3]]);
  const vig = S.k(t, [['s14b01', 0.55], ['s14b02.end', 0.4]]);

  if (t < T('s14b02+0.5')) {
    // 1. the hood POV; crossfade (1.0 s) into the full-screen cosmos
    hoodPOV(g, t, S, cosmos);
    const x = smoothstep(T('s14b02-0.5'), T('s14b02+0.5'), t);
    if (x > 0) {
      const o = offscreen();
      cosmosFull(o, t, S, cosmos);
      g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = x; g.imageSmoothingQuality = 'high'; g.drawImage(off, 0, 0); g.restore();
    }
  } else if (t < T('s14b05')) {
    // 2. drifting through the stars (b02–b04)
    cosmosFull(g, t, S, cosmos);
  } else if (t < T('s14b06+2.8')) {
    // 3. reverse: close on Fear, lit by starlight; the change happens on its face (b05), the breath of a laugh
    // after 'afraid' (b06) — one continuous shot with the faintest push-in
    const z = CLOSE[2] * S.k(t, [['s14b05', 1], ['s14b06+2.8', CLOSE_PUSH, 'sine']]);
    const plate = { key: 'b05', rect: frameRect(CLOSE[0], CLOSE[1], CLOSE[2]), res: CLOSE[2] * CLOSE_PUSH, tb: T('s14b05') };
    drawStage(g, t, S, cam(CLOSE[0], CLOSE[1], z, t, 2), { cosmos, plate });
  } else if (t < T(CUT_TWO)) {
    // 4a. the same shot breathes out, slowly, anchored on the face (≈ 2.7 by the end): the open hands, the soft
    // "o" on 'wonder', the trembling smile on 'amazement' and the blush all hold at face size until after the line
    const k = S.k(t, [['s14b06+2.8', 0], [CUT_TWO, 1, 'sine']]);
    const pb = pullCam(k);
    const tb = T('s14b05');   // same frozen instant as shot 3's plate: the shot runs on without a pop
    // background plates per zoom bucket (each rendered at its bucket's highest zoom, then shrunk)
    const R = 0.84, kb = Math.floor(Math.log(Z_A / pb.zoom) / Math.log(1 / R) + 1e-9);
    const zHi = Z_A * Math.pow(R, kb), zLo = zHi * R;
    const a = pullCamAtZoom(zHi), b2 = pullCamAtZoom(Math.max(zLo, Z_M * 0.98));
    const plate = { key: 'pb' + kb, rect: unionRect(frameRect(a.x, a.y, a.zoom), frameRect(b2.x, b2.y, b2.zoom)), res: zHi, tb };
    drawStage(g, t, S, cam(pb.x, pb.y, pb.zoom, t, 2), { cosmos, plate, tb });
  } else if (t < T(CUT_CLOSE)) {
    // 4b. the two-shot from the side: tiny Fear under the whole starry hood bowed above it; a soft shimmer
    // passes through the stars; the camera keeps easing back a little
    const k = S.k(t, [[CUT_TWO, 0], [CUT_CLOSE, 1, 'out']]);
    const c = cam(lerp(TWO_A[0], TWO_B[0], k), lerp(TWO_A[1], TWO_B[1], k), zoomExp(TWO_A[2], TWO_B[2], k), t, 2);
    drawStage(g, t, S, c, { cosmos });
    hoodShimmer(g, c, S.k(t, [[CUT_TWO, 0], [CUT_CLOSE, 1, 'linear']]));
  } else if (t < T(CUT_WIDE)) {
    // 5. close on Fear: the swallow, the breath, "Why are you showing me this?" (b07–b08); then the same close
    // carries the hand leaving (b09, QA: the reaction played in a wide at ≈ 40 px): the fingertips slide off its
    // shoulder and out of frame, its eyes drop to the shoulder, it leans after the hand, the brows dip — while the
    // camera eases back and right a little to give the lean room. Plate without the Void's left arm (it moves
    // from b09): the frame top is y ≥ 1300, so the whole visible sleeve lies in front of the cage (drawn live).
    const k1 = S.k(t, [[CUT_CLOSE, 0], ['s14b09', 1]]);
    const k2 = S.k(t, [['s14b09+0.2', 0], [CUT_WIDE, 1, 'sine']]);
    const z = lerp(CLOSE[2] * lerp(1, 1.05, k1), CLOSE_OUT[2], k2);
    const cx = lerp(CLOSE[0], CLOSE_OUT[0], k2), cy = lerp(CLOSE[1] - 4, CLOSE_OUT[1], k2);
    const plate = { key: 'b07', rect: unionRect(frameRect(CLOSE[0], CLOSE[1] - 4, CLOSE[2]), frameRect(...CLOSE_OUT)),
      res: CLOSE[2] * 1.05, tb: T(CUT_CLOSE), noArm: true };
    drawStage(g, t, S, cam(cx, cy, z, t, 2), { cosmos, hoodOff: true, plate });
  } else if (t < T(CUT_MED)) {
    // 6b. raised wide: the empty sleeve returns to rest and the hood turns from Fear back to the distance — the
    // whole hood in frame, the cosmos in it, the far glow screen-left — held into b10 ("And the Void stared…")
    drawStage(g, t, S, cam(WIDE[0], WIDE[1], WIDE[2], t, 2), { cosmos });
  } else {
    // 7. Fear follows the Void's gaze: the eyes lead, the head comes round to the far glow, the body turns
    const k = S.k(t, [[CUT_MED, 0], ['scene.end+0.9', 1, 'linear']]);
    const z = zoomExp(MED_A[2], MED_B[2], k);
    const starK = S.k(t, [['s14b10', 1], ['s14b10+2.6', 0.5]]);
    // plate: everything behind Fear is still now (hood turned, hand gone, sleeve at rest)
    const plate = { key: 'med', rect: unionRect(frameRect(...MED_A), frameRect(...MED_B)), res: MED_B[2], tb: T(CUT_MED) };
    drawStage(g, t, S, cam(lerp(MED_A[0], MED_B[0], k), lerp(MED_A[1], MED_B[1], k), z, t, 2), { cosmos, starK, hoodOff: true, plate });
  }

  grade(g, cold, 0);
  vignette(g, vig);
}
