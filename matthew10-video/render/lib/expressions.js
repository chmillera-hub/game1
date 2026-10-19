'use strict';
// Expression presets: partial pose parameters blended over time.
// Conventions: browIn/browOut > 0 raise, browKnit > 0 pulls together,
// lid > 0 droops the upper lids, squint raises the lower lids,
// smile -1..1, press tightens lips, wide widens the eyes, wet = tears welling.

const EXPR = {
  neutral: {},
  attentive: { browIn: 0.12, browOut: 0.1, wide: 0.05 },
  soft_smile: { smile: 0.32, squint: 0.12, browIn: 0.08 },
  smile: { smile: 0.75, squint: 0.3, browOut: 0.12, blush: 0.15 },
  warm: { smile: 0.5, squint: 0.25, browIn: 0.25, lid: 0.08 },
  // A performed smile: big mouth, eyes not joining in (no squint), brows lifted.
  fake_smile: { smile: 0.95, squint: -0.1, wide: 0.25, browOut: 0.32, browIn: 0.18, jawOpen: 0.28, teeth: 1 },
  polite: { smile: 0.28, squint: 0.0, browIn: 0.1, browOut: 0.12 },
  fading: { smile: 0.06, browIn: 0.15, lid: 0.12 },
  thinking: { browIn: 0.15, browKnit: 0.2, smile: -0.05, press: 0.15, lid: 0.1 },
  sad: { smile: -0.42, browIn: 0.72, browOut: -0.28, browKnit: 0.3, lid: 0.25 },
  hurt: { smile: -0.3, browIn: 0.85, browOut: -0.1, browKnit: 0.42, lid: 0.12, press: 0.25, wet: 0.35 },
  stung: { smile: -0.18, browIn: 0.7, browOut: 0.25, browKnit: 0.2, wide: 0.28, jawOpen: 0.08 },
  vulnerable: { smile: -0.15, browIn: 0.62, browKnit: 0.3, lid: 0.1, wet: 0.25 },
  anxious: { smile: -0.12, browIn: 0.58, browKnit: 0.5, press: 0.4, wide: 0.12, shoulderUp: 0.35 },
  overwhelmed: { smile: -0.35, browIn: 0.8, browKnit: 0.75, lid: 0.15, squint: 0.35, press: 0.5, shoulderUp: 0.6 },
  earnest: { browIn: 0.55, browOut: 0.15, browKnit: 0.35, smile: -0.05, wide: 0.08 },
  resolved: { smile: 0.04, browIn: 0.12, browKnit: 0.15, lid: 0.12, press: 0.18 },
  steady: { smile: 0.0, browIn: 0.05, browKnit: 0.1, lid: 0.05 },
  tender: { smile: 0.28, browIn: 0.42, lid: 0.18, squint: 0.15, wet: 0.35 },
  crying: { smile: -0.45, browIn: 0.95, browKnit: 0.55, lid: 0.3, squint: 0.3, wet: 0.85, blush: 0.4, press: 0.2 },
  relief: { smile: 0.42, browIn: 0.45, lid: 0.28, squint: 0.3, wet: 0.6, blush: 0.25 },
  surprised: { wide: 0.6, browIn: 0.65, browOut: 0.7, jawOpen: 0.22 },
  moved: { smile: 0.35, browIn: 0.6, lid: 0.12, wet: 0.75, blush: 0.3 },
  joy: { smile: 0.85, squint: 0.42, browIn: 0.3, browOut: 0.2, wet: 0.5, blush: 0.3 },
  tired: { lid: 0.38, browIn: 0.2, smile: -0.1, slump: 0.3 },
  hollow: { lid: 0.3, smile: -0.08, browIn: 0.1 },
  unsettled: { browIn: 0.4, browKnit: 0.3, wide: 0.15, smile: -0.12, press: 0.1 },
  // Mom
  bright: { smile: 0.72, squint: 0.15, browOut: 0.28, browIn: 0.15 },
  brittle: { smile: 0.35, squint: -0.05, browIn: 0.3, browOut: 0.15, press: 0.3 },
  dismissive: { smile: 0.28, browIn: 0.35, browOut: 0.15, lid: 0.22, asym: 0.15 },
  placating: { smile: 0.2, browIn: 0.5, browKnit: 0.2, lid: 0.1 },
  tight: { smile: -0.08, press: 0.6, browIn: -0.15, browKnit: 0.35, lid: 0.12 },
  exasperated: { smile: -0.2, browIn: 0.3, browOut: 0.4, lid: 0.3, press: 0.2 },
  cracking: { smile: -0.35, browIn: 0.85, browKnit: 0.45, lid: 0.2, wet: 0.65, press: 0.25 },
  // Dad
  closed: { smile: -0.15, browIn: -0.25, browKnit: 0.35, lid: 0.28, press: 0.25 },
  irritated: { smile: -0.3, browIn: -0.55, browKnit: 0.7, lid: 0.22, press: 0.45 },
  weary: { smile: -0.2, browIn: 0.2, browOut: -0.1, lid: 0.4, press: 0.15 },
  // Jordan
  awkward: { smile: -0.06, press: 0.5, browIn: 0.35, asym: 0.3, lid: 0.1 },
  guilty: { smile: -0.2, browIn: 0.55, browKnit: 0.25, lid: 0.25, press: 0.35 },
  // Greg
  chipper: { smile: 0.72, squint: 0.1, browOut: 0.35, browIn: 0.25 },
  patronizing: { smile: 0.45, asym: 0.28, browIn: 0.35, browOut: 0.4, lid: 0.25 },
  impatient: { smile: 0.18, browIn: -0.2, browKnit: 0.3, lid: 0.15, press: 0.3 },
};

module.exports = { EXPR };
