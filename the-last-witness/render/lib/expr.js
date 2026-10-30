// Facial expression presets, gesture poses and phoneme → viseme mapping.
'use strict';

// Expression parameters (all blendable):
//  browIn  inner brow raise (+) / lower (-)     browOut outer brow raise
//  furrow  brows pulled together and down       asym    one brow higher (+ = screen-right brow up)
//  lidUp   upper-lid openness (1 = normal)      lidLow  lower-lid raise / squint 0..1
//  smile   mouth corners up (+) / down (-)      open    resting jaw opening
//  press   lips pressed                          cheek   cheek raise
//  pitch   head down (+) / up (-) bias           roll    head tilt bias (rad)
const EXPR = {
  neutral:       {},
  attentive:     { browOut: 0.15, browIn: 0.12, lidUp: 1.08 },
  warm:          { smile: 0.35, cheek: 0.3, lidLow: 0.2, browIn: 0.12 },
  gentle_smile:  { smile: 0.5, cheek: 0.4, lidLow: 0.28, browIn: 0.15 },
  smile:         { smile: 0.85, cheek: 0.7, lidLow: 0.42, open: 0.06 },
  amused:        { smile: 0.6, asym: 0.35, browOut: 0.2, lidLow: 0.32, cheek: 0.5 },
  laugh:         { smile: 1, open: 0.5, lidLow: 0.75, browIn: 0.25, cheek: 1, pitch: -0.08 },
  sad:           { smile: -0.45, browIn: 0.7, browOut: -0.25, lidUp: 0.8, pitch: 0.14 },
  grief:         { smile: -0.7, browIn: 1, browOut: -0.35, lidUp: 0.62, lidLow: 0.3, open: 0.1, pitch: 0.24 },
  pained:        { furrow: 0.6, browIn: 0.55, lidLow: 0.5, smile: -0.4, lidUp: 0.75 },
  worried:       { browIn: 0.8, furrow: 0.3, smile: -0.22, lidUp: 1.05 },
  fearful:       { browIn: 0.9, browOut: 0.45, lidUp: 1.3, smile: -0.3, open: 0.12 },
  awe:           { browIn: 0.5, browOut: 0.7, lidUp: 1.25, open: 0.18, pitch: -0.08 },
  wonder:        { browOut: 0.5, browIn: 0.4, lidUp: 1.15, smile: 0.22, open: 0.08 },
  thoughtful:    { furrow: 0.3, asym: 0.3, lidUp: 0.86, smile: -0.05, press: 0.3 },
  curious:       { asym: 0.6, browOut: 0.3, lidUp: 1.1, smile: 0.12, roll: 0.07 },
  determined:    { furrow: 0.6, lidUp: 0.9, lidLow: 0.25, press: 0.5, smile: -0.1, pitch: -0.05 },
  resolute:      { furrow: 0.4, lidUp: 0.95, press: 0.4, smile: 0.06 },
  serious:       { furrow: 0.35, lidUp: 0.92, smile: -0.1 },
  exhausted:     { lidUp: 0.55, browIn: 0.3, smile: -0.2, pitch: 0.2 },
  peaceful:      { lidUp: 0.62, smile: 0.3, browIn: 0.05 },
  surprised:     { browOut: 1, browIn: 0.8, lidUp: 1.35, open: 0.3 },
  tender:        { smile: 0.35, browIn: 0.45, lidUp: 0.86, lidLow: 0.22, roll: 0.06 },
  hopeful:       { browIn: 0.45, browOut: 0.3, smile: 0.35, lidUp: 1.05, pitch: -0.08 },
  contemplative: { lidUp: 0.76, furrow: 0.15, pitch: 0.1 },
  hesitant:      { browIn: 0.5, furrow: 0.2, press: 0.5, smile: -0.15, lidUp: 0.9 },
  relief:        { browIn: 0.4, smile: 0.45, lidUp: 0.72, pitch: -0.05 },
  bittersweet:   { smile: 0.3, browIn: 0.7, lidUp: 0.85, lidLow: 0.25 },
  sleepy:        { lidUp: 0.45, browOut: -0.1 },
  lonely:        { browIn: 0.6, smile: -0.25, lidUp: 0.8, pitch: 0.12 },
};
const PARAMS = ['browIn', 'browOut', 'furrow', 'asym', 'lidUp', 'lidLow', 'smile', 'open', 'press', 'cheek', 'pitch', 'roll'];
const DEFAULTS = { lidUp: 1 };

function exprParams(name, intensity = 0.7) {
  const e = EXPR[name] || EXPR.neutral;
  const out = {};
  for (const p of PARAMS) {
    const base = DEFAULTS[p] ?? 0;
    const v = e[p] ?? base;
    out[p] = base + (v - base) * intensity;
  }
  return out;
}

// ---- phonemes → visemes ----
// viseme = [open, wide, round, teeth]
const VIS = {
  rest: [0, 0, 0, 0],
  mbp: [0, 0.05, 0, 0],
  fv: [0.07, 0.25, 0, 0.9],
  aa: [0.78, 0.35, 0, 0.35],
  ee: [0.32, 0.75, 0, 0.7],
  ih: [0.38, 0.45, 0, 0.5],
  uh: [0.4, 0.25, 0.1, 0.3],
  oh: [0.48, 0, 0.8, 0.15],
  oo: [0.24, 0, 1, 0.05],
  r: [0.26, 0.05, 0.55, 0.3],
  cons: [0.2, 0.4, 0, 0.8],
  th: [0.18, 0.35, 0, 0.6],
};
const PH = {};
for (const c of 'mbp') PH[c] = 'mbp';
for (const c of 'fv') PH[c] = 'fv';
for (const c of 'ɑaæʌɐ') PH[c] = 'aa';
for (const c of 'ɔɒo') PH[c] = 'oh';
for (const c of 'uʊw') PH[c] = 'oo';
for (const c of 'eɛiɪj') PH[c] = 'ee';
for (const c of 'əɚɜᵻᵊ') PH[c] = 'uh';
for (const c of 'ɹr') PH[c] = 'r';
for (const c of 'θð') PH[c] = 'th';
for (const c of 'tdnszʃʒʧʤkɡgŋhlxɾʔç') PH[c] = 'cons';
function visemeOf(ph) {
  const k = PH[ph];
  return k ? VIS[k] : null; // null: stress/length marks or spaces (carry neighbour)
}

module.exports = { EXPR, PARAMS, exprParams, VIS, visemeOf };
