// Scene 3 - Captain the crab (light comedic beat).
import { W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, mix, rgba, ellipse, withCam, handheld, blurLayer, vignette } from '../lib/core.mjs';
import { figure, head, headSocket } from '../lib/cast.mjs';
import { expr, blend, blinkAt, saccade, lipsync } from '../lib/face.mjs';
import { POSES, blendPose, drawHand } from '../lib/body.mjs';
import { tideline, beach } from '../lib/env.mjs';
import { crab } from '../lib/props.mjs';
import { directiveLevel } from '../lib/overlays.mjs';

// expression track: keys [[time, params]], blends over `bl` seconds into each key
export function track(t, keys, bl = 0.5) {
  let p = keys[0][1];
  for (let i = 1; i < keys.length; i++) { const [tk, e] = keys[i]; if (t <= tk - bl / 2) break; p = blend(p, e, seg(t, tk - bl / 2, tk + bl / 2)); }
  return p;
}
export function alive(p, t, seed, { blinkRate = 1, sac = 1 } = {}) {
  const s = saccade(t, seed, sac);
  return { ...p, blink: Math.max(p.blink ?? 0, blinkAt(t, seed, blinkRate)), gazeX: (p.gazeX ?? 0) + s.x, gazeY: (p.gazeY ?? 0) + s.y, t };
}
// place a figure so its head lands at (hx, hy)
export function placeFig(g, who, pose, o, face, hx, hy) {
  const hs = headSocket(who, pose, { ...o, x: 0, y: 0 });
  figure(g, who, pose, { ...o, x: hx - hs.x, y: hy - hs.y }, face);
}
const irisCol = (ctx, t) => mix('#ffcf7a', PAL.hud, directiveLevel(ctx, t));

function foam(g, t, reach) { // a froth tongue sliding up the sand toward the crab
  const y = lerp(640, 820, reach);
  g.save(); g.fillStyle = rgba('#e8f4f2', 0.55); g.beginPath(); g.moveTo(-20, 600);
  for (let x = -20; x <= W + 20; x += 40) g.lineTo(x, y + noise1(x * 0.02 + t * 0.8, 3) * 18);
  g.lineTo(W + 20, 600); g.closePath(); g.fill();
  g.strokeStyle = rgba('#ffffff', 0.85); g.lineWidth = 5; g.beginPath();
  for (let x = -20; x <= W + 20; x += 40) { const yy = y + noise1(x * 0.02 + t * 0.8, 3) * 18; x < 0 ? g.moveTo(x, yy) : g.lineTo(x, yy); }
  g.stroke(); g.restore();
}

export default {
  s03a(g, t, ctx) {
    const hh = handheld(t, 3, 31);
    tideline(g, { t, tod: 7.5, zoom: 1 + t * 0.02, camX: hh.x, camY: hh.y });
    foam(g, t, 0.35 + 0.35 * Math.sin(clamp(t / 2.4) * Math.PI * 0.9));
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, zoom: 1 + t * 0.03 }, g2 => {
      crab(g2, { x: 360, y: 905, s: 2.4, t, flipped: true, legs: 1 + 0.4 * Math.sin(t * 3), eyeYaw: Math.sin(t * 5) * 0.6, clawRaise: 0.5 + 0.5 * Math.sin(t * 7) });
    });
    vignette(g, 0.35);
  },
  s03b(g, t, ctx) {
    const hh = handheld(t, 4, 32), oh = ctx.word('s03b_1', 'Oh!').start, lit1 = ctx.word('s03b_1', 'little').start;
    blurLayer(g, 'bg03b', 5, x => beach(x, { t, tod: 7.4, horizonY: 640, camX: hh.x * 0.3, camY: 60 }));
    const lean = seg(t, oh + 0.1, oh + 0.6, ease.outCubic);
    const pose = blendPose(POSES.stand, POSES.reachDown, lean * 0.35);
    let p = track(t, [[0, expr('neutral', { gazeX: 0.3 })], [0.45, expr('neutral', { gazeY: -0.7, gazeX: 0.1 })],
      [oh, expr('surprised', { gazeY: -0.75, browRaise: 0.9, eyeOpen: 1.3 })], [lit1, expr('tender', { gazeY: -0.8, smile: 0.3 })]], 0.35);
    p = lipsync(alive(p, t, 7), ctx.mouth('keeper', t));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.015, rot: hh.rot }, g2 =>
      placeFig(g2, 'keeper', pose, { s: 2.0, t, costume: 'new', light: 'day', lightX: -0.6 },
        { ...p, pitch: -0.25 - lean * 0.15, glow: 0.6, glowColor: '#ffcf7a', wind: 0.3, rim: 0.4 }, 360, 430 + lean * 40));
    vignette(g, 0.3);
  },
  s03c(g, t, ctx) {
    const hh = handheld(t, 2.5, 33);
    tideline(g, { t, tod: 7.5, zoom: 1.04, camX: hh.x, camY: hh.y });
    // flip: 0.5..1.2; scurry 1.3..2.4; stop & look back 2.6..
    const flip = seg(t, 0.55, 1.15), cx = 330 + seg(t, 1.3, 2.4) * 170;
    const walk = clamp(1 - Math.abs((t - 1.85) / 0.6)) > 0 ? 1 : 0;
    const look = seg(t, 2.6, 3.0, ease.outBack);
    // hand comes in from top-left
    const hin = seg(t, 0.0, 0.5, ease.outCubic) * (1 - seg(t, 1.3, 2.0));
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, zoom: 1.04 }, g2 => {
      g2.save();
      if (flip < 1) { g2.translate(cx, 880); g2.rotate(-flip * Math.PI); g2.translate(-cx, -880); }
      crab(g2, { x: cx, y: 905, s: 2.2, t, flipped: flip < 0.5, legs: flip < 0.5 ? 1 : 0.2,
        walk: t > 1.3 && t < 2.45 ? 1 : 0, eyeYaw: lerp(0.3, -1, look) + Math.sin(t * 2) * 0.1 * look, clawRaise: look * 0.4 * (0.5 + 0.5 * Math.sin(t * 6)) });
      g2.restore();
      const hx = lerp(80, 300, hin) + flip * 20, hy = lerp(560, 820, hin) - flip * 40;
      if (hin > 0.01) drawHand(g2, { x: hx - 140, y: hy - 140, s: 1.5, rot: -0.9 + flip * 0.6, side: 'R', who: 'keeper', shape: flip > 0 && flip < 1 ? 'pinch' : 'open', light: LIGHT.day });
    });
    vignette(g, 0.3);
  },
  s03d(g, t, ctx) {
    const hh = handheld(t, 3, 34);
    const w = (l, k) => ctx.word(l, k).start;
    const cap = w('s03d_4', 'Captain.');
    if (t > cap + 0.7) { // cut-in: Captain raises a claw
      const u = t - cap - 0.7;
      tideline(g, { t, tod: 7.5, zoom: 1.1 + u * 0.03 });
      crab(g, { x: 450, y: 905, s: 1.9, t, eyeYaw: -0.6 + Math.sin(u * 3) * 0.15, clawRaise: seg(u, 0.1, 0.4, ease.outBack) });
      vignette(g, 0.3); return;
    }
    blurLayer(g, 'bg03d', 7, x => beach(x, { t, tod: 7.6, horizonY: 700, camY: 40 }));
    const pr = w('s03d_2', 'practice.'), pr2 = w('s03d_3', 'Practice.');
    const wry = expr('wry', { smile: 0.35, mouthAsym: 0.5, browR: 0.5, gazeY: -0.35 });
    const laugh = expr('laugh', { lowerLid: 0.8, eyeOpen: 0.45 });
    let p = track(t, [[0, wry], [w('s03d_1', 'help.'), { ...wry, browR: 0.7, gazeY: -0.2 }],
      [w('s03d_1', 'Close'), expr('wry', { smile: 0.45, mouthAsym: 0.6, browR: 0.8, gazeX: 0.25 })],
      [w('s03d_2', 'Logging'), expr('neutral', { browL: 0.4, gazeX: 0.45, gazeY: 0.2, smile: 0.15 })],
      [pr, laugh], [pr + 1.2, expr('smile', { lowerLid: 0.55 })], [pr2, expr('smile', { smile: 0.8, lowerLid: 0.6 })],
      [w('s03d_4', 'call'), expr('fond', { gazeY: -0.75 })]], 0.5);
    p = alive(p, t, 9);
    if (t > pr && t < pr + 1.3) p.mouthOpen = Math.max(p.mouthOpen ?? 0, 0.25 + 0.2 * Math.abs(Math.sin((t - pr) * 14)) * (1 - (t - pr) / 1.3));
    p = lipsync(p, ctx.mouth('keeper', t));
    const lookDown = seg(t, w('s03d_4', 'call') - 0.3, cap);
    const lb = t > pr && t < pr + 1.0 ? Math.sin((t - pr) * 14) * 4 * (1 - (t - pr)) : 0; // laugh bob
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.008, rot: hh.rot }, g2 => {
      placeFig(g2, 'keeper', POSES.stand, { s: 2.9, t, costume: 'new', light: 'day', lightX: -0.6 },
        { ...p, roll: 0.13, pitch: -lookDown * 0.3, glow: 0.65, glowColor: irisCol(ctx, t), wind: 0.25, rim: 0.4 }, 360, 420 + lb + lookDown * 20);
    });
    vignette(g, 0.3);
  },
};
