// Scene 4 - preparation montage.
import { W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, mix, rgba, vgrad, ellipse, withCam, handheld, blurLayer, vignette, cached } from '../lib/core.mjs';
import { expr, lipsync } from '../lib/face.mjs';
import { POSES, blendPose, drawHand, walkPose } from '../lib/body.mjs';
import { figure } from '../lib/cast.mjs';
import { beach, spring, clearing, islandWide, reef, ISLAND } from '../lib/env.mjs';
import { carvedStone, mapStone, bush, shellTool, hut } from '../lib/props.mjs';
import { waterPour, splash, chips, rain } from '../lib/fx.mjs';
import { track, alive, placeFig } from './s03.mjs';
import { directiveLevel } from '../lib/overlays.mjs';

const irisCol = (ctx, t) => mix('#ffcf7a', PAL.hud, directiveLevel(ctx, t));
const sandBg = (g) => g.drawImage(cached('s04sand', x => {
  x.fillStyle = vgrad(x, 0, 0, 0, H, [[0, '#c9b48e'], [0.5, '#d8c39a'], [1, '#bfa47c']]); x.fillRect(0, 0, W, H);
  for (let i = 0; i < 9; i++) { x.fillStyle = rgba('#a88d66', 0.25); x.beginPath(); ellipse(x, (i * 173) % W, 120 + i * 130, 90, 14); x.fill(); }
}), 0, 0);

export default {
  s04a(g, t, ctx) {
    const hh = handheld(t, 3, 41), w = k => ctx.word(k[0], k[1]).start;
    blurLayer(g, 'bg04a', 4, x => beach(x, { t, tod: 9, horizonY: 700, camX: 40 + t * 3, camY: 40 }));
    const det = seg(t, w(['s04a_2', 'then']) - 0.4, w(['s04a_2', 'whoever']) + 0.3);
    let p = track(t, [[0, expr('focused', { gazeX: 0.5, gazeY: 0.05, browInner: 0.3 })],
      [w(['s04a_1', 'now...']), expr('worried', { gazeX: 0.45, gazeY: -0.15 })],
      [w(['s04a_2', 'then']), expr('determined', { gazeX: 0.55, eyeOpen: 0.85, smile: 0 })],
      [w(['s04a_2', 'whoever']), expr('determined', { gazeX: 0.55, eyeOpen: 0.85, smile: 0.35, browInner: -0.2 })]], 0.6);
    p = lipsync(alive(p, t, 11, { sac: 0.6 }), ctx.mouth('keeper', t));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.012, rot: hh.rot }, g2 =>
      placeFig(g2, 'keeper', POSES.standWind, { s: 2.3, t, costume: 'new', light: 'day', lightX: 0.5, facing: 1 },
        { ...p, yaw: 0.15, pitch: det * 0.18, glow: 0.6, wind: 0.9, windDir: -1, rim: 0.6 }, 330, 430 - det * 10));
    vignette(g, 0.3);
  },
  s04b(g, t, ctx) {
    const hh = handheld(t, 2, 42), pour = ctx.word('s04b_1', 'pouring').start;
    spring(g, { t, zoom: 1.05 + t * 0.02, camX: hh.x, camY: 40 + hh.y });
    const flow = seg(t, pour - 0.6, pour, ease.outCubic);
    const bob = Math.sin(t * 1.3) * 3, hx = 360, hy = 790 + bob;
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y + 40, zoom: 1.05 + t * 0.02 }, g2 => {
      drawHand(g2, { x: hx - 120, y: hy - 60, s: 2, rot: -1.25, side: 'L', who: 'keeper', shape: 'cupped', light: LIGHT.shade });
      waterPour(g2, { x0: 360, y0: 560, x1: hx, y1: hy - 10, t, flow, width: 20 });
      drawHand(g2, { x: hx + 120, y: hy - 60, s: 2, rot: 1.25, side: 'R', who: 'keeper', shape: 'cupped', light: LIGHT.shade });
      if (flow > 0.8) { // overflow over the hand edges
        splash(g2, { x: hx, y: hy - 20, s: 1.3, t, k: flow });
        for (const sd of [-1, 1]) waterPour(g2, { x0: hx + sd * 70, y0: hy, x1: hx + sd * 95, y1: hy + 200, t: t + sd, flow: (flow - 0.8) * 5 * 0.6, width: 10 });
      }
    });
    vignette(g, 0.35);
  },
  s04c(g, t, ctx) {
    const hh = handheld(t, 2, 43), c0 = ctx.word('s04c_1', 'carved').start, c1 = ctx.word('s04c_1', 'stone.').end;
    sandBg(g);
    const prog = seg(t, c0 - 0.1, c1 + 0.3, ease.linear);
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1.02 + t * 0.02 }, g2 => {
      carvedStone(g2, { x: 360, y: 760, s: 1.1, lines: ['WATER', '40 PACES'], arrow: true, progress: prog, light: LIGHT.day, size: 58 });
      // tool hand follows the carving front
      const parts = 3, P = prog * parts, row = Math.min(2, Math.floor(P)), fr = P - row;
      const tx = 360 + (fr - 0.5) * 300, ty = 760 + (-390 + 58 * 0.55 + 40 + row * 72) * 1.1;
      const strike = (t * 4) % 1, peck = Math.max(0, 1 - strike * 3) * 12;
      chips(g2, { x: tx, y: ty, t: ((t * 4) % 1) / 4 * 2.4, s: 1, seed: Math.floor(t * 4) });
      shellTool(g2, { x: tx + 10, y: ty - 10 - peck, s: 1.3, rot: -0.6 });
      drawHand(g2, { x: tx + 120, y: ty - 120 - peck, s: 1.4, rot: 2.3, side: 'R', who: 'keeper', shape: 'hold', light: LIGHT.day });
    });
    vignette(g, 0.3);
  },
  s04d(g, t, ctx) {
    const hh = handheld(t, 2.5, 44), heal = ctx.word('s04d_1', 'heal,').start, hurt = ctx.word('s04d_1', 'hurt.').start;
    clearing(g, { t, tod: 11, camX: hh.x, camY: hh.y, zoom: 1.02 });
    withCam(g, { x: W / 2 - hh.x, y: H / 2 - hh.y, zoom: 1.02 }, g2 => {
      bush(g2, { x: 175, y: 850, s: 1.1, berry: 'blue', t, light: LIGHT.day });
      bush(g2, { x: 545, y: 850, s: 1.1, berry: 'red', t, light: LIGHT.day });
      const drop = (tk) => seg(t, tk - 0.35, tk, ease.in);
      const d1 = drop(heal), d2 = drop(hurt);
      if (d1 > 0) carvedStone(g2, { x: 175, y: lerp(820, 905, d1), s: 0.42, lines: ['EAT'], icon: 'check', progress: seg(t, heal, heal + 0.6), light: LIGHT.day });
      if (d2 > 0) carvedStone(g2, { x: 545, y: lerp(820, 905, d2), s: 0.42, lines: ['NO'], icon: 'x', progress: seg(t, hurt, hurt + 0.6), light: LIGHT.day });
      // Keeper crouches by the blue bush, then steps to the red one
      const mv = seg(t, heal + 0.35, hurt - 0.4);
      const kx = lerp(290, 420, mv), walking = mv > 0 && mv < 1;
      const pose = walking ? walkPose((t * 1.6) % 1) : POSES.crouch;
      const p = alive(expr('focused', { gazeY: -0.6, gazeX: mv > 0.5 ? 0.3 : -0.3, smile: 0.1 }), t, 12);
      figure(g2, 'keeper', pose, { x: kx, y: 905, s: 0.62, t, costume: 'new', light: 'day', facing: mv > 0.5 ? 1 : -1 }, { ...p, glow: 0.5, wind: 0.3 });
    });
    vignette(g, 0.3);
  },
  s04e(g, t, ctx) {
    const build = seg(t, 0.1, 2.0, ease.linear), shower = Math.min(seg(t, 1.6, 1.9), 1 - seg(t, 2.8, 3.2));
    islandWide(g, { t: t * 6, tod: 8 + t * 2.5, hut: build, tower: 0, lantern: 0, palmGrowth: 0.6, zoom: 1.35 + t * 0.02, camX: -100, camY: 50,
      keeperTiny: { x: ISLAND.hut[0] + Math.sin(t * 23) * 40, y: ISLAND.hut[1] + 6 } });
    if (shower > 0) {
      g.fillStyle = rgba('#2b3a4c', 0.3 * shower); g.fillRect(0, 0, W, H);
      rain(g, { t, intensity: shower * 0.8 });
      // dry warm patch under the roof
      g.save(); g.globalAlpha = shower; g.fillStyle = rgba('#ffd9a6', 0.35); g.beginPath();
      ellipse(g, ISLAND.hut[0] - 85, ISLAND.hut[1] - 8, 28, 10); g.fill(); g.restore();
    }
    vignette(g, 0.3);
  },
  s04f(g, t, ctx) {
    const cut = ctx.word('s04f_1', 'so').start - 0.1, hh = handheld(t, 2, 46);
    if (t < cut) {
      reef(g, { t, tod: 12, zoom: 1.03 + t * 0.02, camX: hh.x, camY: hh.y });
      const p = alive(expr('focused', { gazeY: -0.8 }), t, 13);
      g.save();
      figure(g, 'keeper', POSES.standLookUp ? blendPose(POSES.stand, POSES.reachDown, 0.25) : POSES.stand,
        { x: 360, y: 1060, s: 0.7, t, costume: 'new', light: 'noon' }, { ...p, pitch: -0.4, glow: 0.5 });
      g.restore();
      // water surface over the legs
      g.fillStyle = rgba('#3fa6b0', 0.55); g.fillRect(0, 760 + Math.sin(t * 2) * 4, W, H);
      g.strokeStyle = rgba('#e8fbff', 0.7); g.lineWidth = 3; g.beginPath(); ellipse(g, 360, 762 + Math.sin(t * 2) * 4, 70 + (t * 30) % 40, 10); g.stroke();
    } else {
      const u = t - cut;
      sandBg(g);
      withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y - 40, zoom: 1.05 + u * 0.02 }, g2 => {
        mapStone(g2, { x: 360, y: 820, s: 1.6, progress: seg(u, 0, 2.2, ease.linear), light: LIGHT.day });
        shellTool(g2, { x: 360 + Math.sin(u * 3) * 120, y: 520 + Math.cos(u * 2) * 60, s: 1.2, rot: -0.6 });
      });
    }
    vignette(g, 0.3);
  },
  s04g(g, t, ctx) {
    const hh = handheld(t, 2.5, 47), w = (l, k) => ctx.word(l, k).start;
    blurLayer(g, 'bg04g', 7, x => beach(x, { t, tod: 16.5, horizonY: 640, camY: 30 }));
    const rec = w('s04g_1', 'received.'), lift = 3.3, nt = w('s04g_2', 'Not');
    let p = track(t, [[0, expr('focused', { gazeY: -0.6 })], [0.8, expr('sad', { gazeY: -0.75, browInner: 0.4 })],
      [rec, expr('worried', { gazeY: -0.85, browKnit: 0.8, browInner: 0.7, mouthPress: 0.4 })],
      [lift, expr('hopeful', { gazeX: 0.5, gazeY: 0.2 })],
      [nt, expr('determined', { gazeX: 0.5, gazeY: 0.15, smile: 0.4, eyeOpen: 0.85 })]], 0.6);
    p = lipsync(alive(p, t, 14, { blinkRate: t < lift ? 0.6 : 1 }), ctx.mouth('keeper', t));
    const up = seg(t, lift - 0.4, lift + 0.6);
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.01, rot: hh.rot }, g2 => {
      placeFig(g2, 'keeper', POSES.stand, { s: 2.9, t, costume: 'worn', light: 'dusk', lightX: 0.6 },
        { ...p, pitch: lerp(-0.2, 0.1, up), yaw: lerp(0, 0.2, up), glow: 0.6, glowColor: irisCol(ctx, t), wind: 0.4, rim: 0.6 }, 360, 400);
      // paused hand + shell tool low in frame
      shellTool(g2, { x: 540, y: 1080, s: 1.3, rot: -0.5 });
      drawHand(g2, { x: 620, y: 960, s: 1.5, rot: 2.4, side: 'R', who: 'keeper', shape: 'hold', light: LIGHT.dusk, costume: 'worn' });
    });
    vignette(g, 0.3);
  },
};
