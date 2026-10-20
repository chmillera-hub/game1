// s02 - Day one: solar body, time-lapse, the hands.
import { W, H, PAL, LIGHT, TAU, clamp, lerp, seg, env, ease, noise1, hash, rgba, mix, glow, vignette, withCam, handheld, cached, ellipse } from '../lib/core.mjs';
import { figure, head, headSocket } from '../lib/cast.mjs';
import { POSES, blendPose } from '../lib/body.mjs';
import { expr, blend, blinkAt, saccade, lipsync } from '../lib/face.mjs';
import { beach, skyAt, sunPos } from '../lib/env.mjs';
import { sandGust, sandSlide, glint } from '../lib/fx.mjs';
import { directiveLevel } from '../lib/overlays.mjs';
import { track } from './s01.mjs';

const W_ = (ctx, l, w) => ctx.word(l, w).start;
const ringColor = (ctx, t) => mix('#ffb84a', PAL.hud, directiveLevel(ctx, t) * 0.85);

export default {
  s02a(g, t, ctx) {
    const tSun = W_(ctx, 's02a_2', 'sun'), tFeeds = W_(ctx, 's02a_2', 'feeds'), tSand = W_(ctx, 's02a_2', 'sand');
    const hh = handheld(t, 4, 41), z = 1 + 0.05 * seg(t, 0, ctx.dur);
    beach(g, { tod: 7, t, horizonY: 600, shoreY: 900, camX: hh.x, camY: hh.y, zoom: z });
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, zoom: z, rot: hh.rot }, (g) => {
      const lift = seg(t, tSun - 0.6, tSun + 0.6);
      const gustK = env(t, tSand - 0.3, tSand + 2.0, 0.3, 0.6);
      const pose = blendPose(blendPose(POSES.stand, POSES.standLookUp, lift * (1 - gustK * 0.6)), POSES.standWind, gustK * 0.7);
      const O = { x: 360, y: 1350, s: 1.05, facing: 1, costume: 'new', t, light: 'day', lightX: 0.6, breathe: 1,
        panelGlint: env(t, tFeeds - 0.1, tFeeds + 1.3, 0.2, 0.6) };
      let p = track(t, [[0, 'neutral'], [tSun - 0.5, 'relief', { eyeOpen: 0.7 }], [tSand - 0.2, 'focused', { eyeOpen: 0.75, lowerLid: 0.4 }], [tSand + 1.6, 'wry']]);
      const sc = saccade(t, 4);
      figure(g, 'keeper', pose, O, { ...p, gazeX: sc.x * 0.2, gazeY: 0.4 * lift + sc.y * 0.2, blink: blinkAt(t, 21), glow: 0.7,
        glowColor: ringColor(ctx, t), t, wind: 0.5 + gustK * 0.5, windDir: 1 });
      const hs = headSocket('keeper', pose, O);
      // solar cell shimmer along the shoulders
      const gk = env(t, tFeeds, tFeeds + 1.4, 0.2, 0.7);
      for (let i = 0; i < 3; i++) glint(g, { x: hs.x + (i - 1) * 150 * hs.s + 40, y: hs.y + 300 * hs.s, s: 0.8, k: gk * clamp(Math.sin((t - tFeeds) * 5 + i * 1.7) * 0.5 + 0.6) });
      sandSlide(g, { x: hs.x - 230 * hs.s, y: hs.y + 260 * hs.s, w: 460 * hs.s, h: 380 * hs.s, t: t - tSand, k: env(t, tSand + 0.2, tSand + 2, 0.2, 0.5), n: 50, color: '#e6cfa2' });
    });
    sandGust(g, { t, k: env(t, tSand - 0.3, tSand + 1.9, 0.25, 0.6), y: 640, dir: 1, n: 50 });
    vignette(g, 0.28);
  },

  // WS time-lapse: sun arcs, shadow sweeps, Keeper motionless on a rock
  s02b(g, t, ctx) {
    const u = seg(t, 0.3, ctx.dur - 0.2, ease.linear);
    const tod = (7 + u * 24) % 24, P = skyAt(tod);
    beach(g, { tod, t: t * 6, horizonY: 560, shoreY: 820, clouds: 1, zoom: 1.02 });
    const day = clamp(1 - (P.dark ?? 0));
    const sp = sunPos(tod, 560);
    // rock + shadow sweeping opposite the sun
    const rx = 360, ry = 990;
    const ang = (sp.x - rx) > 0 ? Math.PI : 0, len = 140 + (1 - clamp(sp.up ?? 0.5)) * 160;
    g.save(); g.globalAlpha = 0.35 * day; g.fillStyle = '#3a3050';
    const dx = clamp((rx - sp.x) / 400, -1, 1);
    g.beginPath(); ellipse(g, rx + dx * len * 0.6, ry + 6, 60 + Math.abs(dx) * len * 0.6, 18); g.fill(); g.restore();
    g.fillStyle = mix('#7d7068', P.shadow, 0.3); g.beginPath(); g.moveTo(rx - 120, ry + 10); g.bezierCurveTo(rx - 110, ry - 70, rx + 90, ry - 90, rx + 125, ry + 10); g.closePath(); g.fill();
    g.strokeStyle = PAL.ink; g.lineWidth = 2; g.stroke();
    const li = { key: P.key, shadow: P.shadow, rim: P.horizon, amb: 0.4 };
    figure(g, 'keeper', POSES.sitKneesUp, { x: rx, y: ry - 30, s: 0.42, facing: 1, costume: 'new', t: 0, light: li, lightX: clamp((sp.x - rx) / 300, -1, 1), breathe: 0 },
      { ...expr('neutral'), eyeOpen: 0.9, blink: blinkAt(t * 0.3, 2), glow: 0.6 * day + 0.3, glowColor: ringColor(ctx, t), t: 0, wind: 0.2 });
    // night darkening wash on figure
    vignette(g, 0.3);
  },

  // MCU: hands
  s02c(g, t, ctx) {
    const tNever = W_(ctx, 's02c_1', 'never'), tEff = W_(ctx, 's02c_2', 'efficient'), tE2 = W_(ctx, 's02c_3', 'efficient'), tHelpful = W_(ctx, 's02c_3', 'helpful');
    const bg = cached('s02c_bg', (x) => { beach(x, { tod: 9, t: 0, horizonY: 640, shoreY: 940 }); x.filter = 'blur(9px)'; x.drawImage(x.canvas, 0, 0); x.filter = 'none'; });
    const hh = handheld(t, 3, 51), z = 1 + 0.05 * seg(t, 0, ctx.dur);
    withCam(g, { x: W / 2 - hh.x * 0.5, y: H / 2, zoom: z }, (g) => g.drawImage(bg, 0, 0), 0.5);
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, zoom: z, rot: hh.rot }, (g) => {
      const look = 1 - seg(t, tNever, tNever + 0.7) * 0.85 + seg(t, tE2 - 0.3, tE2 + 0.6) * 0.5;
      const drop = seg(t, tE2 + 0.3, tE2 + 1.2) * (1 - seg(t, tHelpful + 0.6, ctx.dur));
      const pose = { ...blendPose(POSES.stand, POSES.handsLook, 0.75 + 0.25 * look),
        ...(Math.sin(t * TAU / 3.2) > 0.4 ? { hR: 'relaxed', hL: 'relaxed' } : {}), shrug: -6 * drop };
      const O0 = { x: 0, y: 0, s: 1.5, facing: 1 };
      const hs0 = headSocket('keeper', pose, O0);
      const O = { ...O0, x: 380 - hs0.x, y: 420 - hs0.y, costume: 'new', t, light: 'day', lightX: 0.5, breathe: 1 };
      let p = track(t, [[0, 'focused', { browInner: 0.2 }], [tNever - 0.2, 'worried', { browInner: 0.6 }], [tEff, 'sad', { browInner: 0.7 }],
        [tE2 - 0.3, 'tender', { smile: 0.35, browInner: 0.6, lowerLid: 0.3 }], [tHelpful, 'fond', { smile: 0.4, browInner: 0.5 }]]);
      p = lipsync(p, ctx.mouth('keeper', t));
      const shake = Math.sin(clamp((t - tE2) / 1.0) * TAU) * 0.14 * (t > tE2 && t < tE2 + 1 ? 1 : 0);
      const sc = saccade(t, 6);
      figure(g, 'keeper', pose, O, { ...p, yaw: shake - 0.1, gazeY: lerp(0, -0.8, look) + sc.y * 0.2, gazeX: sc.x * 0.2 + 0.1,
        pitch: -0.3 * look, blink: blinkAt(t, 33, 0.8), glow: 0.75, glowColor: ringColor(ctx, t), t, wind: 0.25 });
    });
    vignette(g, 0.3);
  },
};
