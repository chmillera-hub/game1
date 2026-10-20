// s01 - Keeper wakes on the beach. Shots s01a s01b s01c s01d.
import { W, H, PAL, LIGHT, TAU, clamp, lerp, seg, env, ease, noise1, fbm1, hash, rgba, mix, glow, vignette,
  withCam, handheld, cached, titleCard, smoothstep, ellipse } from '../lib/core.mjs';
import { figure, head } from '../lib/cast.mjs';
import { POSES, blendPose } from '../lib/body.mjs';
import { expr, blend, blinkAt, saccade, lipsync } from '../lib/face.mjs';
import { surfClose, beach, islandWide } from '../lib/env.mjs';
import { sandSlide, scanRing, glint } from '../lib/fx.mjs';
import { gull } from '../lib/props.mjs';
import { directiveLevel } from '../lib/overlays.mjs';

// expression track: keys [[time, name, overrides]] -> blended params (0.5 s blends)
export function track(t, keys, bl = 0.5) {
  let p = expr(keys[0][1], keys[0][2]);
  for (let i = 1; i < keys.length; i++) {
    const [tk, n, ov, b] = keys[i]; const k = seg(t, tk, tk + (b ?? bl), ease.inOutSine);
    if (k <= 0) break; p = blend(p, expr(n, ov), k);
  }
  return p;
}
const W_ = (ctx, l, w) => ctx.word(l, w).start;
const ringColor = (ctx, t) => mix('#ffb84a', PAL.hud, directiveLevel(ctx, t) * 0.85);

export default {
  // ECU lying cheek-down in wet sand at dawn. Frame 0 = fully lit poster frame.
  s01a(g, t, ctx) {
    const tSys = W_(ctx, 's01a_3', 'systems'), tSand = W_(ctx, 's01a_3', 'sand'), tPrim = W_(ctx, 's01a_4', 'primary');
    const tHelp = W_(ctx, 's01a_5', 'help'), tPpl = W_(ctx, 's01a_5', 'people');
    const hh = handheld(t, 3, 11), z = 1 + 0.06 * seg(t, 0, ctx.dur, ease.inOutSine);
    surfClose(g, { tod: 5.6 + t * 0.006, t, zoom: z, camX: hh.x, camY: hh.y });
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, zoom: z, rot: hh.rot }, (g) => {
      const hx = 370, hy = 440;
      // wet contact shadow / dark sand under the face (face lies along x, cheek on the sand at the bottom)
      g.fillStyle = rgba('#4a3a3c', 0.35); g.beginPath(); ellipse(g, hx + 10, hy + 190, 300, 50); g.fill();
      // eyes: closed -> flutter on 'Systems' -> slow open by 'online'/'Solar'
      const fl = t > tSys && t < tSys + 0.9 ? 0.25 * Math.max(0, Math.sin((t - tSys) * 22)) : 0;
      const open = seg(t, tSys + 0.7, tSys + 2.4, ease.inOutSine);
      const eye = Math.max(fl, open * 0.85);
      const breathe = Math.sin(t * TAU / 4.5);
      let p = track(t, [[0, 'sleep'], [tSys + 0.6, 'tired'], [tSand + 1.2, 'neutral'], [tPrim, 'focused', { browRaise: 0.15 }],
        [tHelp - 0.2, 'tender', { browInner: 0.4 }], [tPpl + 0.3, 'hopeful', { browInner: 0.35 }]]);
      p = lipsync(p, ctx.mouth('keeper', t));
      const sc = saccade(t, 3, open);
      const sandK = 0.9 * (1 - seg(t, tSand + 0.1, tSand + 1.4));
      head(g, 'keeper', { ...p, x: hx, y: hy + breathe * 3, s: 1.5, roll: -1.08 + breathe * 0.004, yaw: 0.08, pitch: 0,
        eyeOpen: eye * (p.eyeOpen ?? 1), blink: open > 0.9 ? blinkAt(t, 7, 0.8) : 0,
        gazeX: sc.x * 0.3 + lerp(0, -0.25, seg(t, tPrim, tPrim + 1)), gazeY: sc.y * 0.3,
        glow: open * (0.75 + 0.25 * Math.sin(t * 3)) * (t < tSys + 2.4 ? 0.5 + 0.5 * (Math.sin(t * 37) > -0.3) : 1),
        glowColor: ringColor(ctx, t), sand: sandK, wet: 0.6, t, wind: 0.3, wetHair: 0.7, light: LIGHT.dawn, lightX: 0.6, rim: 0.7 });
      // sand beading off the cheek
      if (t > tSand - 0.1) sandSlide(g, { x: hx - 20, y: hy + 40, w: 170, h: 130, t: t - tSand, k: env(t, tSand, tSand + 2.2, 0.15, 0.6), n: 34, color: '#d9b98a' });
      // foam lapping near the face (bottom edge)
      const s = 0.5 + 0.5 * Math.sin(t * TAU / 5.2);
      g.fillStyle = rgba(PAL.foam, 0.6); g.beginPath(); g.moveTo(-60, H + 60);
      for (let x = -60; x <= W + 60; x += 40) g.lineTo(x, 930 + s * 60 + (x - 300) * (x - 300) * 0.0004 + noise1(x * 0.02 + t * 0.4, 9) * 14);
      g.lineTo(W + 60, H + 60); g.closePath(); g.fill();
    });
    // warm dawn bloom from screen-right
    glow(g, 760, 200, 520, '#ffcf9a', 0.35); vignette(g, 0.35, '#2a1830');
  },

  // MS sitting up in the shallows, scanning
  s01b(g, t, ctx) {
    const tScan = W_(ctx, 's01b_1', 'scanning'), tZero = W_(ctx, 's01b_2', 'zero');
    const hh = handheld(t, 4, 21);
    beach(g, { tod: 5.75, t, horizonY: 470, shoreY: 760, camX: hh.x, camY: hh.y, zoom: 1.02 });
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, rot: hh.rot }, (g) => {
      const up = seg(t, 0.1, 1.6, ease.inOutSine);
      const pose = up < 0.5 ? blendPose(POSES.lieSide, POSES.pushUp, up * 2) : blendPose(POSES.pushUp, POSES.sitGround, up * 2 - 1);
      // scan ring under figure
      const k = clamp((t - tScan) / (tZero + 0.6 - tScan));
      scanRing(g, { cx: 380, cy: 905, r: 520, k, squash: 0.22 });
      // shallow water sheet around
      const s = Math.sin(t * TAU / 4);
      g.fillStyle = rgba('#9fc7d4', 0.35); g.beginPath(); ellipse(g, 380, 910 + s * 6, 330, 40); g.fill();
      const look = t < 2 ? 0 : t < 3.4 ? -0.7 * seg(t, 2, 2.8) : lerp(-0.7, 0.7, seg(t, 3.4, 4.6)) * (1 - seg(t, 5.3, 6.2) * 1);
      let p = track(t, [[0, 'tired'], [1.4, 'focused'], [tZero, 'worried', { browInner: 0.5 }]]);
      const sc = saccade(t, 5);
      figure(g, 'keeper', pose, { x: 380, y: 960, s: 0.6, facing: 1, costume: 'new', t, light: 'dawn', lightX: 0.6, wet: 0.8, breathe: 1 },
        { ...p, yaw: look - 0.25, gazeX: look * 0.5 + sc.x * 0.2, gazeY: sc.y * 0.2, blink: blinkAt(t, 13), glow: 0.85,
          glowColor: ringColor(ctx, t), t, wind: 0.3, wetHair: 0.8 });
      // water streaming off (drips falling from body)
      const dk = 1 - seg(t, 1.5, 5);
      for (let i = 0; i < 14; i++) { const ph = (t * (1.2 + hash(i) * 0.8) + hash(i + 3)) % 1;
        const x = 330 + hash(i + 7) * 120, y = 700 + hash(i + 9) * 120 + ph * 180;
        g.strokeStyle = rgba('#e8f6ff', 0.7 * dk * (1 - ph)); g.lineWidth = 2; g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 12); g.stroke(); }
    });
    glow(g, 720, 380, 420, '#ffcf9a', 0.25); vignette(g, 0.3, '#2a1830');
  },

  // CU reaction: Zero. / Then who am I supposed to help?
  s01c(g, t, ctx) {
    const tZ = W_(ctx, 's01c_1', 'zero'), tThen = W_(ctx, 's01c_2', 'then'), tHelp = W_(ctx, 's01c_2', 'help');
    const bg = cached('s01c_bg', (x) => { beach(x, { tod: 5.8, t: 0, horizonY: 600, shoreY: 900 }); x.filter = 'blur(10px)'; x.drawImage(x.canvas, 0, 0); x.filter = 'none'; });
    const hh = handheld(t, 3, 31), z = 1.04 + 0.05 * seg(t, 0, ctx.dur);
    withCam(g, { x: W / 2 - hh.x * 0.4, y: H / 2, zoom: z }, (g) => g.drawImage(bg, 0, 0), 0.5);
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, zoom: z, rot: hh.rot }, (g) => {
      // shoulders
      g.fillStyle = mix('#2d4a5c', '#ffd2a8', 0.15); g.beginPath(); g.moveTo(80, H); g.bezierCurveTo(90, 780, 230, 700, 360, 700);
      g.bezierCurveTo(490, 700, 630, 780, 640, H); g.fill();
      g.fillStyle = '#c86a3a'; g.fillRect(110, 860, 500, 24);
      g.fillStyle = '#1e2c38'; g.beginPath(); g.ellipse(360, 700, 95, 34, 0, 0, Math.PI*2); g.fill();
      const br = Math.sin(t * TAU / 4.2);
      let p = track(t, [[0, 'focused'], [0.3, 'surprised', { browRaise: 0.35, eyeOpen: 1.1, mouthOpen: 0 }],
        [tZ + 0.4, 'worried', { browInner: 0.8, mouthOpen: 0.15 }], [tThen - 0.4, 'sad', { browInner: 0.9 }],
        [tHelp - 0.2, 'worried', { browInner: 1, eyeOpen: 1.05 }]], 0.6);
      p = lipsync(p, ctx.mouth('keeper', t));
      // slow blink at ~2.4s, gaze drops to sand then drifts out to horizon on the question
      const slow = env(t, 2.3, 2.95, 0.25, 0.35);
      const gy = lerp(0, -0.75, seg(t, tZ + 0.6, tZ + 1.2)) * (1 - seg(t, tThen, tThen + 1.2));
      const gx = lerp(0, -0.6, seg(t, tThen, tThen + 1.4));
      const sc = saccade(t, 9);
      head(g, 'keeper', { ...p, x: 360, y: 470 + br * 3, s: 1.2, yaw: -0.12 + gx * 0.25, pitch: gy * 0.25, roll: 0.02 + 0.03 * seg(t, tThen, tHelp),
        blink: Math.max(slow, blinkAt(t, 17, 0.7)), gazeX: gx + sc.x * 0.2, gazeY: gy + sc.y * 0.2,
        glow: 0.8, glowColor: ringColor(ctx, t), t, wind: 0.35, wetHair: 0.5, wet: 0.3, light: LIGHT.dawn, lightX: 0.6, rim: 0.6 });
    });
    vignette(g, 0.35, '#2a1830');
  },

  // EWS title card
  s01d(g, t, ctx) {
    const u = seg(t, 0, ctx.dur, ease.linear);
    islandWide(g, { tod: 5.55 + u * 0.45, t, horizonY: 640, keeperTiny: true, zoom: 1.02 + 0.02 * u, camY: -10 * u });
    // light spreading on the water
    g.save(); g.globalCompositeOperation = 'lighter';
    const k = seg(t, 1.2, 4.5);
    const gr = g.createLinearGradient(0, 640, 0, 1000); gr.addColorStop(0, rgba('#ffcf8a', 0.35 * k)); gr.addColorStop(1, rgba('#ffcf8a', 0));
    g.fillStyle = gr; g.beginPath(); g.moveTo(560, 640); g.lineTo(720, 640); g.lineTo(720, 1000); g.lineTo(140, 1000); g.closePath(); g.fill(); g.restore();
    for (let i = 0; i < 3; i++) gull(g, { x: 120 + i * 90 + t * (14 + i * 4), y: 330 + i * 40 + Math.sin(t * 0.8 + i) * 8, s: 0.5 - i * 0.08, flap: t * (0.7 + i * 0.1) + i * 0.3 });
    const a = env(t, 0.6, ctx.dur - 0.3, 1.1, 1.0);
    titleCard(g, 'FOR SOMEONE,', 300, a, 48);
    titleCard(g, 'SOMEDAY', 372, a, 48);
  },
};
