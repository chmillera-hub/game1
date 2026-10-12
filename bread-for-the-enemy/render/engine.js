// Timeline evaluation: acting keyframes -> per-frame character state, with
// procedural life (blinks, saccades, breathing, speech nods, tremble, lip-sync).
'use strict';
const L = require('./lib');
const { clamp, lerp, smooth } = L;

// ------------------------------------------------------------- emotion presets
const D = {
  browInner: 0, browOuter: 0, browHeight: 0, browFurrow: 0, browInnerL: 0, browInnerR: 0, browHL: 0, browHR: 0,
  lid: 0.9, lidLower: 0.08, lidTilt: 0, pupil: 1,
  mouthSmile: 0, mouthBase: 0, mouthWide: 0, mouthPress: 0, mouthAsym: 0, mouthTremble: 0,
  cheekRaise: 0, tears: 0, tearFlow: 0, blush: 0, pale: 0, tremble: 0,
  pitchOff: 0, rollOff: 0, yawOff: 0, breath: 1, blinkRate: 1, saccade: 1, blind: 0, lean: 0, shoulder: 0,
};
const EMO = {
  neutral: {},
  calm: { lid: 0.82, mouthSmile: 0.08 },
  warm: { mouthSmile: 0.4, lid: 0.8, lidLower: 0.25, browInner: 0.15, cheekRaise: 0.3 },
  smile: { mouthSmile: 0.62, lidLower: 0.4, cheekRaise: 0.5, lid: 0.8 },
  joy: { mouthSmile: 0.8, lidLower: 0.5, browHeight: 0.3, mouthBase: 0.2, cheekRaise: 0.65, lid: 0.85 },
  tender: { rollOff: 0.05, mouthSmile: 0.22, lid: 0.68, browInner: 0.35, lidTilt: -0.2, lidLower: 0.15, breath: 0.85 },
  tender_smile: { rollOff: 0.06, mouthSmile: 0.5, lid: 0.7, browInner: 0.3, lidLower: 0.35, cheekRaise: 0.35 },
  warm_smile: { mouthSmile: 0.58, lid: 0.74, lidLower: 0.38, browInner: 0.22, cheekRaise: 0.45 },
  gentle_smile: { rollOff: 0.05, mouthSmile: 0.45, lid: 0.72, lidLower: 0.35, browInner: 0.25, cheekRaise: 0.35 },
  sorrow_love: { mouthSmile: 0.05, browInner: 0.65, lid: 0.66, lidTilt: -0.35, tears: 0.3, pitchOff: 0.04 },
  sad: { mouthSmile: -0.35, browInner: 0.7, browOuter: -0.3, lid: 0.7, lidTilt: -0.4 },
  grief: { shoulder: -0.18, mouthSmile: -0.5, browInner: 0.95, browOuter: -0.35, lid: 0.5, lidTilt: -0.5, mouthTremble: 0.45, tears: 0.7, pitchOff: 0.12, breath: 1.5, blinkRate: 1.4 },
  cry: { shoulder: -0.12, mouthSmile: -0.55, browInner: 1.0, lid: 0.55, lidLower: 0.45, mouthBase: 0.12, mouthTremble: 0.7, tears: 1, tearFlow: 1, browFurrow: 0.35, breath: 1.8, tremble: 0.25, blinkRate: 1.6 },
  sob_smile: { mouthSmile: 0.32, browInner: 0.9, lid: 0.55, lidLower: 0.5, tears: 1, tearFlow: 0.8, mouthTremble: 0.6, breath: 1.7, tremble: 0.15, cheekRaise: 0.3 },
  cry_anger: { shoulder: 0.12, browFurrow: 0.8, browInner: -0.15, lid: 0.85, lidLower: 0.45, mouthPress: 0.55, mouthSmile: -0.4, tears: 0.6, mouthTremble: 0.4, breath: 1.6, tremble: 0.2 },
  fury_cry: { shoulder: 0.2, browFurrow: 1, browInner: -0.5, lid: 1.02, lidLower: 0.35, mouthSmile: -0.45, mouthWide: 0.35, tears: 1, tearFlow: 0.8, tremble: 0.4, breath: 2, blinkRate: 0.6 },
  anger: { shoulder: 0.12, browFurrow: 0.85, browInner: -0.65, browOuter: 0.2, lid: 0.9, lidLower: 0.3, lidTilt: 0.4, mouthSmile: -0.32, mouthPress: 0.3, breath: 1.4 },
  cold: { browFurrow: 0.3, browInner: -0.25, lid: 0.72, lidLower: 0.25, mouthSmile: -0.15, mouthPress: 0.5, blinkRate: 0.6, saccade: 0.5 },
  cold_pain: { browFurrow: 0.35, browInner: 0.2, lid: 0.72, lidLower: 0.25, mouthSmile: -0.2, mouthPress: 0.45, tears: 0.3 },
  bitter: { browFurrow: 0.4, browInner: -0.2, lid: 0.7, mouthSmile: -0.2, mouthAsym: 0.4, lidLower: 0.3 },
  bitter_laugh: { mouthAsym: 0.45, mouthSmile: 0.15, browInner: 0.5, lid: 0.7, lidLower: 0.4, tears: 0.6, mouthBase: 0.08, rollOff: -0.05 },
  conflicted: { browInner: 0.45, browFurrow: 0.4, lid: 0.72, mouthSmile: -0.25, mouthPress: 0.4, saccade: 1.8 },
  resolve: { browFurrow: 0.5, browInner: -0.3, lid: 0.85, mouthPress: 0.6, mouthSmile: -0.1, pitchOff: -0.04 },
  determined: { browFurrow: 0.55, browInner: -0.35, lid: 0.86, mouthPress: 0.5, mouthSmile: -0.1, pitchOff: -0.03 },
  shock: { browHeight: 0.9, browInner: 0.55, lid: 1.25, pupil: 0.75, mouthBase: 0.3, mouthSmile: -0.1, blinkRate: 0.3, saccade: 0.3 },
  dread: { shoulder: 0.15, browInner: 0.8, browHeight: 0.35, lid: 1.08, pupil: 0.8, mouthBase: 0.1, mouthSmile: -0.3, pale: 0.4, blinkRate: 0.4 },
  horror_quiet: { browInner: 0.9, lid: 0.75, mouthBase: 0.08, mouthSmile: -0.4, pale: 0.5, pitchOff: 0.1 },
  fear: { shoulder: 0.22, browInner: 0.95, browHeight: 0.7, lid: 1.2, pupil: 0.75, mouthBase: 0.22, mouthWide: 0.3, tremble: 0.35 },
  terror: { shoulder: 0.3, browInner: 1, browHeight: 0.85, lid: 1.3, pupil: 0.65, mouthBase: 0.35, mouthWide: 0.45, tremble: 0.55, tears: 0.7, breath: 2.2 },
  awe: { browHeight: 0.6, browInner: 0.4, lid: 1.08, mouthBase: 0.22, mouthSmile: 0.1, pupil: 1.15, blinkRate: 0.4 },
  awe_tears: { browHeight: 0.45, browInner: 0.55, lid: 0.95, mouthBase: 0.12, mouthSmile: 0.28, pupil: 1.15, tears: 1, tearFlow: 0.8, blinkRate: 0.6 },
  pained: { browInner: 0.7, browFurrow: 0.5, lid: 0.62, lidLower: 0.3, mouthSmile: -0.4, mouthPress: 0.3 },
  ashamed: { shoulder: -0.15, browInner: 0.6, lid: 0.5, mouthSmile: -0.3, pitchOff: 0.12, saccade: 0.6 },
  guilt: { shoulder: -0.15, browInner: 0.7, lid: 0.55, mouthSmile: -0.3, tears: 0.45, pitchOff: 0.1 },
  haunted: { browInner: 0.6, lid: 0.86, pupil: 0.85, mouthSmile: -0.25, mouthBase: 0.04, blinkRate: 0.5, saccade: 0.3 },
  puzzled: { browInnerL: 0.45, browHL: 0.4, browInnerR: -0.15, lid: 0.8, rollOff: 0.07, mouthSmile: 0.05 },
  squint: { lid: 0.52, lidLower: 0.5, browFurrow: 0.35, browInner: 0.1, mouthSmile: 0.05, pitchOff: -0.02 },
  hopeful: { browInner: 0.4, browHeight: 0.3, lid: 0.95, mouthSmile: 0.25 },
  weary: { shoulder: -0.12, lid: 0.58, browInner: 0.35, mouthSmile: -0.1, pitchOff: 0.08, breath: 0.8 },
  moved: { browInner: 0.75, lid: 0.68, lidLower: 0.3, tears: 0.8, mouthSmile: 0.08, mouthTremble: 0.3 },
  earnest: { lean: 0.05, browInner: 0.45, browHeight: 0.2, lid: 0.95, mouthSmile: 0.0 },
  stunned: { lid: 1.1, browHeight: 0.45, mouthBase: 0.14, blinkRate: 0.3 },
  soft: { browInner: 0.4, lid: 0.64, mouthSmile: 0.05 },
  tender_cry: { mouthSmile: 0.22, lid: 0.66, browInner: 0.55, lidLower: 0.3, tears: 1, tearFlow: 0.7, mouthTremble: 0.3 },
  peace_tears: { mouthSmile: 0.36, lid: 0.7, lidLower: 0.32, browInner: 0.3, tears: 0.7, tearFlow: 0.3, breath: 0.8 },
  fear_for: { browInner: 0.9, lid: 0.95, mouthSmile: -0.3, mouthTremble: 0.25, tears: 0.6 },
  fervent: { lean: 0.04, browHeight: 0.4, browInner: 0.3, lid: 1.04, mouthSmile: 0.1, pupil: 1.1 },
  triumph: { browHeight: 0.5, lid: 1.0, mouthSmile: 0.4, pupil: 1.12, pitchOff: -0.05 },
  stern: { browFurrow: 0.5, lid: 0.8, mouthSmile: -0.2, mouthPress: 0.4 },
  unsettled: { browInner: 0.5, browFurrow: 0.4, lid: 0.95, mouthSmile: -0.2, saccade: 2.2 },
  uneasy: { browInner: 0.5, lid: 0.72, mouthSmile: -0.15, saccade: 1.5 },
  compassion: { rollOff: 0.05, browInner: 0.55, lid: 0.72, lidLower: 0.2, mouthSmile: 0.15, tears: 0.35, blinkRate: 0.5 },
  broken_wonder: { browInner: 0.9, lid: 1.0, tears: 1, tearFlow: 0.8, mouthBase: 0.2, mouthSmile: 0.1, blind: 0.15, blinkRate: 0.3 },
  laugh_sob: { mouthSmile: 0.3, mouthBase: 0.15, browInner: 0.9, lid: 0.6, lidLower: 0.5, tears: 0.8, tearFlow: 0.5, tremble: 0.3, breath: 1.8 },
  broken: { shoulder: -0.22, browInner: 1, lid: 0.55, mouthSmile: -0.5, mouthTremble: 0.6, tears: 0.7, tearFlow: 0.3, pitchOff: 0.1, breath: 1.6 },
  anguish: { shoulder: 0.1, browInner: 1, browFurrow: 0.6, lid: 0.75, lidLower: 0.4, mouthSmile: -0.6, mouthWide: 0.3, tears: 0.8, tearFlow: 0.5, tremble: 0.3, breath: 1.9 },
  peace: { mouthSmile: 0.3, lid: 0.7, browInner: 0.1 },
  sad: { mouthSmile: -0.35, browInner: 0.7, browOuter: -0.3, lid: 0.66, lidTilt: -0.4, pitchOff: 0.08, shoulder: -0.1 },
  // Asher keeping his distance: half-lidded, one brow up, mouth pulled to one side
  dismissive: { browHL: 0.32, browInnerR: -0.18, browFurrow: 0.25, lid: 0.6, lidLower: 0.28, mouthAsym: 0.42, mouthSmile: -0.12, mouthPress: 0.3, pitchOff: -0.05, rollOff: -0.05, saccade: 0.6, blinkRate: 0.7 },
  skeptical: { browHL: 0.45, browInnerR: -0.25, browFurrow: 0.3, lid: 0.7, lidLower: 0.3, mouthAsym: 0.3, mouthPress: 0.4, mouthSmile: -0.08, pitchOff: -0.03, rollOff: 0.05 },
  annoyed: { browFurrow: 0.7, browInner: -0.35, lid: 0.64, lidLower: 0.32, mouthPress: 0.6, mouthSmile: -0.28, mouthAsym: 0.2, pitchOff: 0.03, breath: 1.3 },
  sad_hurt: { browInner: 0.85, browFurrow: 0.15, lid: 0.64, lidTilt: -0.3, mouthSmile: -0.35, mouthPress: 0.3, tears: 0.35, pitchOff: 0.06, shoulder: -0.08 },
  sorrow_kind: { rollOff: 0.04, browInner: 0.6, lid: 0.66, lidTilt: -0.2, mouthSmile: 0.05, tears: 0.25, pitchOff: 0.05, blinkRate: 0.7 },
  // young Paul giving the order he will regret: anger on the brow, pain around the eyes
  torn_order: { shoulder: 0.1, browFurrow: 0.65, browInner: 0.5, lid: 0.82, lidLower: 0.38, lidTilt: 0.1, mouthSmile: -0.5, mouthPress: 0.25, pale: 0.12, breath: 1.5, blinkRate: 1.3 },
  torn_sad: { shoulder: -0.08, browInner: 0.85, browFurrow: 0.35, lid: 0.6, lidTilt: -0.35, mouthSmile: -0.45, mouthTremble: 0.2, tears: 0.35, pitchOff: 0.1, breath: 1.3 },
  second_guess: { browInner: 0.75, browFurrow: 0.3, lid: 0.86, mouthSmile: -0.32, mouthBase: 0.05, saccade: 1.6, tears: 0.35 },
  resign_order: { browInner: 0.55, browFurrow: 0.5, lid: 0.62, mouthPress: 0.6, mouthSmile: -0.3, tears: 0.25, pitchOff: 0.07, shoulder: -0.06 },
};
// per-character emotion overrides could go here
const NUM = Object.keys(D);

// ------------------------------------------------------------- pose library
// Wrist targets in body units relative to neck base, character facing screen-right.
// n = near arm (screen-left when facing right), f = far arm.
// hand: shape preset (render/hands.js). palm: which way the palm faces, in body terms
// (fwd/back/up/down/in = toward the body's midline/out). fdir: optional finger direction in body
// terms, blended with the forearm direction (fk). The thumb side then follows from anatomy.
const HANG = { in: 1, back: 0.3 };
const LAP = { down: 0.75, in: 0.55 };
const LAPDIR = { fwd: 0.7, in: 0.45, down: 0.45 };
const POSES = {
  default: { n: { w: [-2.02, 5.38], hand: 'relax', palm: HANG }, f: { w: [1.93, 5.38], hand: 'relax', palm: HANG } },
  rest: { n: { w: [-0.9, 4.85], hand: 'relax', palm: LAP, fdir: LAPDIR }, f: { w: [1.05, 4.95], hand: 'relax', palm: LAP, fdir: LAPDIR }, front: true },
  hold_bread: { n: { w: [-1.3, 2.85], hand: 'cup', palm: { up: 0.65, in: 0.75 }, fdir: { in: 0.5, fwd: 0.6, up: 0.4 } },
    f: { w: [1.35, 2.85], hand: 'cup', palm: { up: 0.65, in: 0.75 }, fdir: { in: 0.5, fwd: 0.6, up: 0.4 } }, front: true, bread: { at: [0.02, 2.4], r: 1.1 } },
  break_bread: { n: { w: [-1.85, 2.9], hand: 'hold', palm: { in: 0.8, up: 0.35 }, fdir: { fwd: 0.6, in: 0.5, up: 0.3 } },
    f: { w: [1.9, 2.85], hand: 'hold', palm: { in: 0.8, up: 0.35 }, fdir: { fwd: 0.6, in: 0.5, up: 0.3 } }, front: true, halves: { r0: 0.95 } },
  give_bread: { n: { w: [-1.01, 4.70], hand: 'relax', palm: HANG }, f: { w: [2.94, 2.52], hand: 'pinch', palm: { up: 1 }, fdir: { fwd: 0.7, in: 0.4 } }, front: true },
  reach: { n: { w: [-1.85, 5.21], hand: 'relax', palm: HANG }, f: { w: [3.02, 3.02], hand: 'open', palm: { up: 0.8, fwd: 0.5 } }, front: true },
  // the classic open stance: both arms out from the body, palms up, offering
  open_palms: { n: { w: [-2.5, 3.95], hand: 'offer', palm: { up: 0.85, fwd: 0.35 }, fdir: { fwd: 0.75, out: 0.4, down: 0.25 }, fk: 0.6 },
    f: { w: [2.5, 3.95], hand: 'offer', palm: { up: 0.85, fwd: 0.35 }, fdir: { fwd: 0.75, out: 0.4, down: 0.25 }, fk: 0.6 }, front: true },
  open_arms: { n: { w: [-2.6, 4.15], hand: 'offer', palm: { up: 0.8, fwd: 0.4 }, fdir: { fwd: 0.7, out: 0.45, down: 0.25 }, fk: 0.6 },
    f: { w: [2.6, 4.15], hand: 'offer', palm: { up: 0.8, fwd: 0.4 }, fdir: { fwd: 0.7, out: 0.45, down: 0.25 }, fk: 0.6 }, front: true },
  open_low: { n: { w: [-2.3, 4.55], hand: 'offer', palm: { up: 0.75, fwd: 0.5 }, fdir: { out: 0.4, fwd: 0.7, down: 0.3 }, fk: 0.6 },
    f: { w: [2.3, 4.55], hand: 'offer', palm: { up: 0.75, fwd: 0.5 }, fdir: { out: 0.4, fwd: 0.7, down: 0.3 }, fk: 0.6 }, front: true },
  hold: { n: { w: [-1.68, 5.04], hand: 'grip', palm: HANG }, f: { w: [0.7, 3.25], hand: 'cup', palm: { up: 0.75, in: 0.6 }, fdir: { in: 0.8, fwd: 0.35 } }, front: true,
    jar: { arm: 'n', h: 1.9 }, bread: { arm: 'f', r: 1.0 } },
  hold_nervous: { n: { w: [-1.68, 5.04], hand: 'grip', palm: HANG }, f: { w: [0.62, 3.55], hand: 'cup', palm: { up: 0.75, in: 0.6 }, fdir: { in: 0.8, fwd: 0.35 } }, front: true,
    jar: { arm: 'n', h: 1.9 }, bread: { arm: 'f', r: 0.95 }, fidget: { arm: 'f', amp: [0.1, 0.3], period: 3.4, pats: 2 }, sway: 0.02 },
  hold_half: { n: { w: [-1.85, 5.12], hand: 'relax', palm: HANG }, f: { w: [0.85, 3.7], hand: 'cup', palm: { in: 0.75, up: 0.55, back: 0.1 }, fdir: { in: 0.75, fwd: 0.4 } }, front: true,
    half: { arm: 'f', r: 0.9 } },
  knock: { n: { w: [-1.93, 5.21], hand: 'relax', palm: HANG }, f: { w: [3.36, 1.18], hand: 'fist', palm: { in: 0.6, down: 0.5 }, fdir: { fwd: 1, up: 0.3 } }, front: true },
  empty: { n: { w: [-1.8, 5.2], hand: 'relax', palm: HANG }, f: { w: [1.9, 5.2], hand: 'relax', palm: HANG }, front: false },
  drop_bread: { n: { w: [-1.93, 5.21], hand: 'open', palm: HANG }, f: { w: [1.34, 5.04], hand: 'open', palm: { in: 0.8, back: 0.4 } }, front: true },
  kneel: { n: { w: [-1.25, 4.4], hand: 'relax', palm: LAP, fdir: LAPDIR }, f: { w: [1.45, 4.35], hand: 'relax', palm: LAP, fdir: LAPDIR }, front: true },
  kneel_offer: { n: { w: [-1.15, 4.15], hand: 'cup', palm: { up: 0.65, in: 0.6 }, fdir: { in: 0.6, fwd: 0.5 } },
    f: { w: [3.45, 3.05], hand: 'offer', palm: { up: 1.0, fwd: 0.15 }, fdir: { fwd: 0.85, in: 0.35 }, fk: 0.5 }, front: true, half: { arm: 'f', r: 0.9 }, half2: { arm: 'n', r: 0.85 } },
  kneel_eat: { n: { w: [-1.0, 3.9], hand: 'cup', palm: { up: 0.65, in: 0.6 }, fdir: { in: 0.6, fwd: 0.5 } },
    f: { w: [0.9, 2.55], hand: 'hold', palm: { in: 0.6, back: 0.45, up: 0.2 }, fdir: { up: 0.65, in: 0.45, fwd: 0.2 } }, front: true, half: { arm: 'f', r: 0.8 }, half2: { arm: 'n', r: 0.8 } },
  write: { n: { w: [-0.55, 4.55], hand: 'relax', palm: { down: 1 }, fdir: LAPDIR }, f: { w: [1.3, 4.2], hand: 'pen', palm: { down: 0.6, in: 0.6 }, fdir: { fwd: 0.6, in: 0.5 } },
    front: true, shackles: true, parchment: true },
  lean: { n: { w: [-0.55, 4.4], hand: 'relax', palm: LAP, fdir: LAPDIR }, f: { w: [1.5, 4.2], hand: 'relax', palm: LAP, fdir: LAPDIR }, front: true, shackles: true, lean: 0.12 },
  take_bread: { n: { w: [-0.4, 4.25], hand: 'relax', palm: LAP, fdir: LAPDIR }, f: { w: [2.1, 3.35], hand: 'cup', palm: { up: 0.75, in: 0.5 }, fdir: { fwd: 0.6, in: 0.5 } },
    front: true, shackles: true, half: { arm: 'f', r: 0.88 } },
  eat: { n: { w: [-0.5, 4.25], hand: 'relax', palm: LAP, fdir: LAPDIR }, f: { w: [1.0, 2.35], hand: 'hold', palm: { in: 0.6, back: 0.45, up: 0.2 }, fdir: { up: 0.65, in: 0.45, fwd: 0.2 } },
    front: true, shackles: true, half: { arm: 'f', r: 0.8 } },
  grip: { n: { w: [-0.4, 4.25], hand: 'relax', palm: LAP, fdir: LAPDIR }, f: { w: [2.5, 3.55], hand: 'grip', palm: { down: 0.6, in: 0.5, fwd: 0.2 }, fdir: { fwd: 0.8, in: 0.3 } }, front: true, shackles: true },
  bound: { n: { w: [-0.45, 4.55], hand: 'fist', palm: { in: 1 }, fdir: { down: 0.7, fwd: 0.4 } }, f: { w: [0.35, 4.55], hand: 'fist', palm: { in: 1 }, fdir: { down: 0.7, fwd: 0.4 } }, front: true, rope: true },
  scroll: { n: { w: [-1.85, 5.04], hand: 'relax', palm: HANG }, f: { w: [2.1, 3.1], hand: 'grip', palm: { in: 0.8, up: 0.35 }, fdir: { fwd: 0.6, up: 0.45 } }, front: true, scroll: true },
  walk: { n: { w: [-1.85, 5.21], hand: 'relax', palm: HANG }, f: { w: [2.02, 5.04], hand: 'relax', palm: HANG } },
  kneel_shield: { n: { w: [-1.05, -0.55], hand: 'open', palm: { fwd: 0.75, up: 0.45, out: 0.2 }, fdir: { up: 0.8, in: 0.45 } },
    f: { w: [2.15, 4.75], hand: 'open', palm: { down: 1 }, fdir: { fwd: 0.85, out: 0.25 }, fk: 0.7 }, front: true },
  kneel_up: { n: { w: [-1.75, 3.9], hand: 'offer', palm: { up: 0.85, fwd: 0.4 }, fdir: { fwd: 0.6, out: 0.45 } }, f: { w: [2.05, 3.75], hand: 'offer', palm: { up: 0.85, fwd: 0.4 }, fdir: { fwd: 0.6, out: 0.45 } }, front: true },
  peek: { n: { w: [-1.85, 5.21], hand: 'relax', palm: HANG }, f: { w: [1.85, 5.21], hand: 'relax', palm: HANG } },
  // a guard holding a spear in the near hand
  guard_spear: { n: { w: [-1.6, 4.4], hand: 'grip', palm: { in: 0.9, fwd: 0.3 }, fdir: { fwd: 0.8, in: 0.3 } }, f: { w: [1.9, 5.2], hand: 'relax', palm: HANG }, front: true, spear: { arm: 'n' } },
};

// ------------------------------------------------------------- state engine
class Actor {
  constructor(who, kfs, seed) {
    this.who = who;
    this.kfs = (kfs || []).slice().sort((a, b) => a.t - b.t);
    this.seed = seed;
    // precompute blink times
    const r = L.rng(seed * 7919 + 13);
    this.blinks = [];
    let t = r() * 2;
    while (t < 2000) { this.blinks.push(t); t += 2.0 + r() * 3.4; }
    // extra blinks on look changes
    let lastLook = null;
    for (const k of this.kfs) {
      if (k.state.look && k.state.look !== lastLook && lastLook !== null) this.blinks.push(k.t + 0.02);
      if (k.state.look) lastLook = k.state.look;
    }
    this.blinks.sort((a, b) => a - b);
    this.nods = this.kfs.filter((k) => k.state.nod).map((k) => k.t);
    this.dry = null;
  }
  // Tears appear as fast as the acting asks, but once the crying stops they dry slowly
  // (streaks fade over ~7 s, wet eyes over ~5 s) instead of vanishing or lingering forever.
  dried(t, raw) {
    if (!this.dry) {
      const dt = 0.05, n = Math.ceil((this.duration || 900) / dt) + 2;
      const tf = new Float32Array(n), te = new Float32Array(n);
      let a = 0, b = 0;
      for (let i = 0; i < n; i++) {
        const v = this.eval(i * dt, null, true);
        a = Math.max(v.tearFlow, a - dt / 7.0);
        b = Math.max(v.tears, b - dt / 5.0);
        tf[i] = a; te[i] = b;
      }
      this.dry = { dt, tf, te };
    }
    const d = this.dry, x = clamp(t / d.dt, 0, d.tf.length - 1.001), i = Math.floor(x), f = x - i;
    raw.tearFlow = lerp(d.tf[i], d.tf[i + 1], f);
    raw.tears = lerp(d.te[i], d.te[i + 1], f);
  }
  // evaluate numeric channels + discrete look/pose with blend info
  eval(t, lookMap, rawOnly) {
    const cur = {};
    for (const k of NUM) cur[k] = { from: D[k], to: D[k], t0: -1e9, dur: 0.001 };
    const ease = (x) => smooth(x);
    const val = (c, tt) => (c.dur <= 0.002 ? (tt >= c.t0 ? c.to : c.from) : lerp(c.from, c.to, ease((tt - c.t0) / c.dur)));
    let look = { from: 'default', to: 'default', t0: -1e9, dur: 0.001 };
    let pose = { from: 'default', to: 'default', t0: -1e9, dur: 0.001 };
    let emoName = 'neutral';
    for (const k of this.kfs) {
      if (k.t > t) break;
      const dur = Math.max(0.001, k.dur);
      const s = k.state;
      let target = null;
      if (s.emo) { target = Object.assign({}, D, EMO[s.emo] || {}); emoName = s.emo; }
      const setCh = (name, v) => {
        const c = cur[name];
        const now = val(c, k.t);
        c.from = now; c.to = v; c.t0 = k.t; c.dur = dur;
      };
      if (target) for (const n of NUM) if (s[n] === undefined) setCh(n, target[n]);
      for (const n of NUM) if (s[n] !== undefined) setCh(n, s[n]);
      if (s.look) {
        const p = ease((k.t - look.t0) / look.dur) >= 1 ? look.to : look.to; // snap from current target
        look = { from: p === s.look ? look.from : look.to, to: s.look, t0: k.t, dur: dur <= 0.002 ? 0.001 : Math.max(0.15, dur * 0.8) };
      }
      if (s.pose) {
        pose = { from: pose.to, to: s.pose, t0: k.t, dur };
      }
    }
    const out = { emo: emoName };
    for (const n of NUM) out[n] = val(cur[n], t);
    if (!rawOnly) this.dried(t, out);
    out.lookFrom = look.from; out.lookTo = look.to; out.lookK = look.dur <= 0.002 ? 1 : ease((t - look.t0) / look.dur);
    out.poseFrom = pose.from; out.poseTo = pose.to; out.poseK = pose.dur <= 0.002 ? 1 : ease((t - pose.t0) / pose.dur);
    return out;
  }
  blink(t, rate) {
    // closure amount 0..1
    let c = 0;
    for (let i = 0; i < this.blinks.length; i++) {
      const b = this.blinks[i];
      if (b > t + 0.01) break;
      if (rate < 0.5 && (i % 2 === 1)) continue; // fewer blinks when rate low
      const d = t - b;
      if (d < 0 || d > 0.3) continue;
      let v;
      if (d < 0.07) v = d / 0.07; else if (d < 0.1) v = 1; else v = 1 - (d - 0.1) / 0.16;
      c = Math.max(c, clamp(v));
    }
    // extra blinks when rate high (crying): half-phase blinks
    if (rate > 1.3) {
      const ph = (t * 0.45 * rate + this.seed * 0.37) % 1;
      if (ph < 0.06) c = Math.max(c, Math.sin(ph / 0.06 * Math.PI));
    }
    return c;
  }
}

class World {
  constructor(tl) {
    this.tl = tl;
    this.actors = {};
    let seed = 1;
    for (const who of ['jesus', 'paul', 'asher', 'yosef', 'saul', 'child', 'guard', 'phoebe']) {
      this.actors[who] = new Actor(who, tl.acts[who], seed++);
      this.actors[who].duration = (tl.duration || 900) + 2;
    }
    // line starts per speaker (for the breath before each line)
    this.starts = {};
    for (const ln of tl.lines) for (const w of Object.keys(ln.mouth || {})) (this.starts[w] = this.starts[w] || []).push(ln.start);
    // lines by speaker
    this.lines = tl.lines;
  }
  speaking(who, t) {
    // returns {open, wide, close, loud} if who is voicing a line at t
    for (const ln of this.lines) {
      if (t < ln.start - 0.05 || t > ln.end + 0.1) continue;
      const m = ln.mouth[who];
      if (!m) continue;
      const lt = t - ln.start - (m.offset || 0);
      const i = lt * 60;
      if (i < 0 || i >= m.open.length - 1) continue;
      const i0 = Math.floor(i), f = i - i0;
      const g = (arr) => lerp(arr[i0], arr[Math.min(arr.length - 1, i0 + 1)], f);
      // emphasis: smoothed loudness over ~0.3s window
      let em = 0, n = 0;
      for (let k = -9; k <= 9; k += 3) { const j = i0 + k; if (j >= 0 && j < m.loud.length) { em += m.loud[j]; n++; } }
      em /= Math.max(1, n);
      return { open: g(m.open), wide: g(m.wide), close: g(m.close), loud: g(m.loud), emph: em, line: ln, lt };
    }
    return null;
  }
  nearLine(who, t) {
    // time until the next line by `who` starts (before) / since the last one ended (after)
    let before = null, after = null;
    for (const ln of this.lines) {
      if (!ln.mouth[who]) continue;
      if (ln.start > t && (before === null || ln.start - t < before)) before = ln.start - t;
      if (ln.end < t && (after === null || t - ln.end < after)) after = t - ln.end;
      if (t >= ln.start && t <= ln.end) return null;
    }
    return { before: before === null ? 99 : before, after: after === null ? 99 : after };
  }
  // full facial + body state for a character at time t in the context of a shot
  state(who, t, shotLook = {}) {
    const A = this.actors[who];
    const e = A.eval(t, shotLook);
    const F = {};
    for (const k of NUM) F[k] = e[k];
    // gaze & head from look targets (resolved via shot map)
    const resolve = (name) => shotLook[name] || shotLook.default || { gx: 0, gy: 0, yaw: 0, pitch: 0 };
    const a = resolve(e.lookFrom), b = resolve(e.lookTo);
    const k = e.lookK;
    // eyes lead, head follows (eyes faster)
    const ke = clamp(k * 2.2), kh = smooth(k);
    F.gazeX = lerp(a.gx, b.gx, ke);
    F.gazeY = lerp(a.gy, b.gy, ke);
    F.yaw = lerp(a.yaw || 0, b.yaw || 0, kh) + F.yawOff;
    F.yawLook = F.yaw;
    F.pitch = lerp(a.pitch || 0, b.pitch || 0, kh) + F.pitchOff;
    F.roll = F.rollOff + lerp(a.roll || 0, b.roll || 0, kh);
    // saccades
    const sr = F.saccade;
    if (sr > 0.05) {
      const seg = Math.floor(t * (0.9 + 0.6 * sr) + A.seed * 3.1);
      const fr = (t * (0.9 + 0.6 * sr) + A.seed * 3.1) - seg;
      const prev = [L.hash(seg * 31 + A.seed), L.hash(seg * 17 + A.seed * 5)];
      const cur = [L.hash((seg + 1) * 31 + A.seed), L.hash((seg + 1) * 17 + A.seed * 5)];
      const m = clamp((fr - 0.85) / 0.15);
      F.gazeX += lerp(prev[0], cur[0], m) * 0.07 * sr;
      F.gazeY += lerp(prev[1], cur[1], m) * 0.045 * sr;
    }
    // speech (+ an inhale just before a line, a lip press just after one)
    const near = this.nearLine(who, t);
    let inh = 0;
    for (const st0 of this.starts[who] || []) {
      const d = t - st0;
      if (d > -0.45 && d < 0) inh = Math.max(inh, L.smooth((d + 0.45) / 0.45));
      else if (d >= 0 && d < 0.8) inh = Math.max(inh, 1 - L.smooth(d / 0.8));
    }
    F.breathInhale = inh * 0.7;
    if (near) {
      if (near.before > 0 && near.before < 0.4) {
        const k = Math.sin(clamp(1 - near.before / 0.4) * Math.PI * 0.5);
        F.mouthBase = Math.max(F.mouthBase, 0.09 * k);
      }
      if (near.after > 0 && near.after < 0.7) {
        const k = Math.sin(clamp(near.after / 0.7) * Math.PI);
        F.mouthPress = Math.max(F.mouthPress, 0.45 * k);
      }
    }
    const sp = this.speaking(who, t);
    F.mouthOpen = F.mouthBase;
    if (sp) {
      F.mouthOpen = Math.max(F.mouthBase * 0.6, sp.open * 0.95 + F.mouthBase * 0.3);
      F.mouthWide = lerp(F.mouthWide, sp.wide, 0.75);
      F.mouthPress *= 0.2;
      // nods & brows on emphasis
      F.pitch += 0.03 * (sp.emph - 0.5) + 0.008 * Math.sin(t * 2.6 + A.seed);
      F.yaw += 0.012 * Math.sin(t * 1.7 + A.seed);
      F.browHeight += 0.18 * clamp(sp.emph - 0.55, 0, 1);
      F.speaking = 1;
    } else F.speaking = 0;
    // reaction nods (a slow, small down-and-up of the head)
    for (const tn of A.nods) {
      const u = (t - tn) / 0.95;
      if (u > 0 && u < 1) F.pitch += 0.13 * Math.sin(Math.PI * u) * (1 - 0.3 * u);
    }
    // blink
    const bl = A.blink(t, F.blinkRate);
    const lookDown = clamp(F.gazeY, 0, 1);
    F.lidL = F.lidR = 1;
    F.lid = F.lid * (1 - bl) * (1 - 0.32 * lookDown) + (F.lid < 0.1 ? 0 : 0);
    // tremble & breathing
    const tr = F.tremble;
    F.headDX = tr * 0.025 * L.noise1(t * 2.6, A.seed + 11);
    F.headDY = tr * 0.02 * L.noise1(t * 2.2, A.seed + 23);
    F.roll += tr * 0.018 * L.noise1(t * 1.9, A.seed + 5);
    const br = F.breath;
    const bphase = t * (0.26 * br) * L.TAU + A.seed;
    F.breathV = Math.sin(bphase) * (0.5 + 0.5 * clamp(br - 1)) + (F.breathInhale || 0) * 0.8;
    F._trem = L.noise1(t * 6.5, A.seed + 41) * 1.0;
    F._irisShake = F.tears * L.noise1(t * 3.0, A.seed + 3);
    // hair sway from head motion: compare with a slightly earlier state
    F.pose = e.poseTo; F.poseTo = e.poseTo; F.poseFrom = e.poseFrom; F.poseK = e.poseK;
    F.emo = e.emo;
    return F;
  }
  headLag(who, t, shotLook) {
    const a = this.state(who, t, shotLook), b = this.state(who, t - 0.18, shotLook);
    return [-(a.yaw - b.yaw) * 1.6 + 0.04 * L.noise1(t * 0.7, 9), (a.pitch - b.pitch) * 0.6];
  }
}

module.exports = { World, EMO, POSES, D };
