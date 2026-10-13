// s18 · the_rusted_cage · backOfMind · dissolve in (and out to s19)
// Time has passed. The cage is only a leftover now: rust, a gate that creaks a few degrees and settles, a
// flake of rust drifting down, a single star glinting in a fold of the Void's robe. No characters: the
// performance is in the still-life and the camera (close → slow lateral drift → rise toward the far glow).
import { W, H, clamp, lerp, ease, applyCamera, drift, vignette } from '../engine.mjs';
import { drawHQ, drawHQForeground } from '../sets/hq.mjs';
import { drawVoid } from '../chars/void.mjs';
import { drawCage, CAGE_PRESETS } from '../sets/props.mjs';

export const id = 's18';

// --- staging constants (data/staging.md §1.4)
const VOID_B = [700, 1600, 0.9];
const STARE_B = { headTurn: -0.65, headDown: 0.12 };
const COSMOS_RESIDUE = 0.5;
const CAGE_B = [430, 1630, 0.952];

export const sfx = [
  // the rusted gate creaks a few degrees and settles (door 0.93 → 1 over s18b01+0.1 → +1.6; file swell 0.1–1.5)
  { at: 's18b01', name: 'rust_creak', gain: -16 },
  // the single faint star glinting in a fold of the robe (very soft, under the narration)
  { at: 's18b03+0.28', name: 'twinkle', gain: -25 },
];

function grade(g, cold, warm) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  if (cold > 0) { g.globalCompositeOperation = 'multiply'; g.fillStyle = `rgba(150,165,255,${0.35 * cold})`; g.fillRect(0, 0, W, H); }
  if (warm > 0) { g.globalCompositeOperation = 'soft-light'; g.fillStyle = `rgba(255,170,90,${0.45 * warm})`; g.fillRect(0, 0, W, H); }
  g.restore();
}

// bloom + 4-point star at the robe fold (world coords of the current camera)
const FOLD = [VOID_B[0] - 127 * VOID_B[2], VOID_B[1] - 236 * VOID_B[2]];
function foldGlint(g, t, k, flash) {
  if (k <= 0.005) return;
  const [x, y] = FOLD;
  const tw = 0.5 + 0.5 * Math.sin(t * 2.1 + 0.4) * Math.sin(t * 0.83 + 1.3);
  const a = k * (0.45 + 0.35 * tw) + 0.5 * flash;
  g.save();
  g.globalCompositeOperation = 'lighter';
  const r = 30 + 10 * flash;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, `rgba(215,205,255,${0.42 * a})`); gr.addColorStop(0.35, `rgba(150,120,255,${0.14 * a})`);
  gr.addColorStop(1, 'rgba(138,108,255,0)');
  g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r);
  const L = 9 + 4 * tw + 7 * flash, w = 1.6;
  g.fillStyle = `rgba(245,240,255,${Math.min(1, 0.85 * a)})`;
  g.beginPath();
  g.moveTo(x - L, y); g.lineTo(x, y - w); g.lineTo(x + L, y); g.lineTo(x, y + w); g.closePath();
  g.moveTo(x, y - L * 1.15); g.lineTo(x + w, y); g.lineTo(x, y + L * 1.15); g.lineTo(x - w, y); g.closePath();
  g.fill();
  g.beginPath(); g.arc(x, y, 2.2, 0, Math.PI * 2); g.fill();
  g.restore();
}

// one rust flake drifting down from the front of the top ring, in front of the bars (where the dark robe
// behind gives it contrast), tumbling (its lit face catches the far glow), then resting on the ground.
// (The prop's own flake is ~15 px, rust-on-rust along the gate at the frame edge: it does not read.)
const FL0 = [404, 1342], FL1 = [436, 1671];
function rustFlake(g, k) {
  if (k <= 0) return;
  const kk = clamp(k);
  const fall = kk * kk * (3 - 2 * kk) * 0.25 + kk * 0.75;            // a soft start, then a steady drift
  const x = lerp(FL0[0], FL1[0], fall) + 11 * Math.sin(kk * 7.5) * Math.min(1, kk * 5) * (1 - kk * 0.6);
  const y = lerp(FL0[1], FL1[1], fall);
  const spin = kk * 9.5;
  const face = Math.cos(spin * 1.3);
  const landed = kk >= 1;
  g.save();
  g.translate(x, y);
  g.scale(1.35, 1.35);
  g.rotate(landed ? 0.35 : spin * 0.7);
  g.scale(1, landed ? 0.42 : 0.35 + 0.65 * Math.abs(face));
  g.globalAlpha *= clamp(kk * 10) * (landed ? 0.75 : 1);
  g.fillStyle = face > 0 ? '#d98a4c' : '#8a4422';
  g.strokeStyle = '#3a1a0c'; g.lineWidth = 0.9;
  g.beginPath(); g.moveTo(-6.5, -1.5); g.lineTo(0.5, -4.4); g.lineTo(6.6, 0.2); g.lineTo(2.4, 3.6); g.lineTo(-3.8, 3.0); g.closePath();
  g.fill(); g.stroke();
  if (face > 0.2 && !landed) { // the lit face glints faintly in the far light
    g.fillStyle = `rgba(255,214,160,${0.6 * (face - 0.2)})`;
    g.beginPath(); g.moveTo(-3.5, -1.2); g.lineTo(0.6, -3.0); g.lineTo(3.2, -0.6); g.closePath(); g.fill();
  }
  g.restore();
}

/** ease that accelerates over the first 40 % and then cruises at constant speed (no stop at the end) */
function rampIn(k) {
  const p = 0.4, v = 1 / (1 - p / 2);
  return k < p ? (v * k * k) / (2 * p) : v * (k - p / 2);
}

export function render(g, t, S) {
  // ---------------- camera
  // b01: close on the cage (a whisper of push-in for life); b02: slow lateral drift past the cage (left → right);
  // b03: as the fold-star kindles, the camera rises up-left toward the far glow (the front of the mind)
  // and keeps going gently into the dissolve to s19.
  // One continuous curve instead of drift → stop → reverse → fast rise: the drift right (b02) eases out while
  // the rise begins (after "hanging open", b02+3.4), so the path bends up and then up-left toward the far glow,
  // easing IN and cruising on into the dissolve (the s19 dissolve hides the end of the move, so it never stops
  // on screen). The old sine rise (b03+0.5 → {400,1150,1.25}) peaked at ~220 px/s on screen; this peaks at
  // ~85 px/s. It ends short of the plan's {400,1150,1.25} ({430,1230,1.42} at S.end+0.9): the far glow still
  // sits upper-left, above the cage, as the image dissolves.
  const cx = S.k(t, [
    ['scene.start', 420], ['s18b02', 420],
    ['s18b03+0.4', 520, 'sine'],
    ['scene.end+0.9', 430, rampIn],
  ]);
  const cy = S.k(t, [['s18b02+3.4', 1400], ['scene.end+0.9', 1230, rampIn]]);
  const cz = S.k(t, [
    ['scene.start', 1.585], ['s18b02', 1.62, 'sine'],
    ['s18b02+3.4', 1.6, 'sine'],
    ['scene.end+0.9', 1.42, rampIn],
  ]);
  const d = drift(t, 2.5);
  const cam = { x: cx + d.dx / cz, y: cy + d.dy / cz, zoom: cz, rot: d.dr * 0.5 };

  const st = { t, lightsDim: 0.2, mist: 0.45, consoleGlow: 1, alarm: 0 };

  // the gate: a few degrees, an outBack settle (its own weight), then still
  const door = S.k(t, [['s18b01+0.1', 0.93], ['s18b01+1.6', 1.0, 'outBack']]);
  // one flake of rust tumbles from the gate's top rail to the ground in front of the cage
  const flakeK = S.k(t, [['s18b02+0.5', 0], ['s18b02+4.0', 1, 'linear']]);
  // the star in the fold: kindles (0.6 s) and stays, faintly twinkling (the Void module animates the twinkle)
  const foldStar = S.k(t, [['s18b03+0.3', 0], ['s18b03+0.9', 1, 'out']]);

  g.save();
  applyCamera(g, cam);
  drawHQ(g, 'backOfMind', st);
  // the Void: only its robe in frame, at the frame's right edge (the hood is far above, out of frame). Its left arm
  // hangs behind the robe here: at rest the sleeve's open cuff hung right above the cage and, dark on dark, read as a
  // black disc floating in the air. (No hand shows; nothing of the Void moves.)
  drawVoid(g, ...VOID_B, {
    t, ...STARE_B, idle: 0.3, shadowSpread: 0.4,
    cosmos: COSMOS_RESIDUE, cosmosOpts: { seed: 7, glyphs: 0 },
    foldStar,
    handL: { target: [-170, -620], reach: 1, show: 0, front: false },
  });
  drawCage(g, ...CAGE_B, {
    t, ...CAGE_PRESETS.rustedOpen, door,
  });
  rustFlake(g, flakeK);
  // the fold-star sits right behind the cage's rightmost bar (sx≈466): its light blooms over the bar so the
  // glint still reads at phone size (the robe module's own star stays underneath)
  foldGlint(g, t, foldStar, S.k(t, [['s18b03+0.3', 0], ['s18b03+0.75', 1, 'out'], ['s18b03+1.6', 0, 'sine']]));
  drawHQForeground(g, 'backOfMind', st);
  // the floor sinks into darkness before the stage edge (world y 1778) so the close never shows the seam
  const fg = g.createLinearGradient(0, 1690, 0, 1790);
  fg.addColorStop(0, 'rgba(7,6,14,0)'); fg.addColorStop(1, 'rgba(7,6,14,1)');
  g.fillStyle = fg; g.fillRect(-500, 1690, 2000, 400);
  g.restore();

  grade(g, 0, 0.25);
  vignette(g, 0.4);
}
