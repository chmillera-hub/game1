// Scene 8 - dawn arrival: the carved stone, the spring, the message in the hut.
import { W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, mix, rgba, withCam, handheld, blurLayer, vignette, glow } from '../lib/core.mjs';
import { expr, lipsync } from '../lib/face.mjs';
import { POSES, blendPose, walkPose } from '../lib/body.mjs';
import { head } from '../lib/cast.mjs';
import { beach, spring, hutInterior } from '../lib/env.mjs';
import { boat, carvedStone } from '../lib/props.mjs';
import { waterPour, glint } from '../lib/fx.mjs';
import { track, alive, placeFig } from './s03.mjs';

const W_ = ctx => (id, w) => ctx.word(id, w).start;

export default {
  s08a(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 2, 81);
    const up = w('s08a_2', 'one,') - 0.35, run = seg(t, up, up + 0.5);
    beach(g, { tod: 6, t, horizonY: 470, shoreY: 700, camX: hh.x + run * 40, camY: hh.y, zoom: 1.02 + t * 0.01 });
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.01 }, g2 => {
      boat(g2, { x: 560, y: 690, s: 0.75, roll: 0.18, light: LIGHT.dawn });
      carvedStone(g2, { x: 250, y: 800, s: 0.75, lines: ['WATER', '40 PACES'], arrow: true, light: LIGHT.dawn, size: 50 });
      let p = track(t, [[0, expr('reading', { gazeX: -0.3, gazeY: -0.5 })],
        [w('s08a_1', 'forty'), expr('surprised', { gazeX: -0.3, gazeY: -0.4, eyeOpen: 1.2, browRaise: 0.5 })],
        [w('s08a_1', 'paces.') + 0.3, expr('smile', { gazeX: 0.6, eyeOpen: 1.2, browRaise: 0.4 })],
        [up + 0.3, expr('laugh', { gazeX: 0.6 })]], 0.4);
      p = lipsync(alive(p, t, 82), ctx.mouth('mira', t));
      if (t < up) {
        const tr = seg(t, 0.3, 0.9) * (1 - seg(t, 2.6, up));
        const pose = blendPose(POSES.kneel, blendPose(POSES.kneel, POSES.brush, 0.7), tr);
        placeFig(g2, 'mira', pose, { s: 0.95, t, costume: 'island', light: 'dawn', lightX: 0.6, facing: -1, breathe: 0.6 },
          { ...p, yaw: -0.15, pitch: -0.25 * tr, rim: 0.5 }, 470, 470 + Math.sin(t * 2) * 2);
      } else {
        const rt = t - up, x = 470 + rt * rt * 60 + rt * 110;
        const pose = blendPose(POSES.stand, walkPose((rt * 2.2) % 1), seg(rt, 0, 0.3));
        placeFig(g2, 'mira', pose, { s: 0.95, t, costume: 'island', light: 'dawn', lightX: 0.6, facing: 1, breathe: 1 },
          { ...p, yaw: 0.1, rim: 0.5 }, x, 430 - Math.abs(Math.sin(rt * 7)) * 14);
      }
    });
    vignette(g, 0.3);
  },

  s08b(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.5, 83);
    spring(g, { t, tod: 7, camX: hh.x, camY: hh.y, zoom: 1.03 + t * 0.006 });
    const lower = seg(t, 2.3, 3.0), look = seg(t, w('s08b_2', 'all') - 0.3, w('s08b_2', 'this...') + 0.4);
    let p = track(t, [[0, expr('relief', { eyeOpen: 0.4, gazeY: -0.3 })],
      [w('s08b_1', 'fresh') - 0.1, expr('cryingSmile', { tears: 0.6, gazeY: -0.2 })],
      [w('s08b_1', 'water.') + 0.4, expr('cryingSmile', { tears: 0.9, lowerLid: 0.6, smile: 0.8 })],
      [w('s08b_2', 'someone'), expr('moved', { tears: 0.8, gazeX: -0.5, gazeY: 0.25 })],
      [w('s08b_2', 'all'), expr('wonder', { tears: 0.7, gazeX: 0.6, gazeY: 0.3 })],
      [w('s08b_2', 'us?'), expr('moved', { tears: 0.9, gazeX: 0.2, gazeY: 0.1, browInner: 0.7, tearDrop: 0 })]], 0.6);
    p = lipsync(alive(p, t, 84, { blinkRate: 0.7, sac: 0.4 }), ctx.mouth('grandpa', t));
    const td = clamp((t - 1.6) / 2.2);
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.01 }, g2 => {
      waterPour(g2, { x0: 360, y0: 560, x1: 330, y1: 880, t, flow: 1, width: 16 });
      const pose = blendPose(POSES.drink, POSES.cuppedHands, lower);
      placeFig(g2, 'grandpa', pose, { s: 1.15, t, costume: 'island', light: 'shade', lightX: -0.6, facing: -1, wet: 0.3, breathe: 0.8 },
        { ...p, yaw: -0.1 + lerp(-0.25, 0.35, look) * lower, pitch: lerp(-0.25, 0.1, lower), tearDrop: td, tearSide: 1, rim: 0.5, wet: 0.4,
          roll: Math.sin(t * 6) * 0.015 * (1 - lower) }, 470, 440);
    });
    vignette(g, 0.35);
  },

  s08c(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1, 85);
    hutInterior(g, { t, tod: 7.5, camX: hh.x, camY: hh.y - t * 4, zoom: 1.04 + t * 0.008 });
    withCam(g, { x: W / 2 + hh.x * 0.6, y: H / 2 + hh.y * 0.6, zoom: 1 + t * 0.008 }, g2 => {
      carvedStone(g2, { x: 360, y: 400, s: 0.62, shape: 'slab', lines: ['IF YOU ARE', 'READING THIS', 'YOU ARE NOT', 'ALONE'], light: LIGHT.interior, size: 52 });
      // warm shaft of light that finds the last word as she reads it
      glow(g2, 360, 330, 140, PAL.beam, 0.15 + 0.2 * seg(t, w('s08c_2', 'alone.') - 0.2, w('s08c_2', 'alone.') + 0.6));
    });
    const not = w('s08c_2', 'not');
    let p = track(t, [[0, expr('reading', { gazeY: 0.6, gazeX: 0 })],
      [w('s08c_1', 'reading'), expr('reading', { gazeY: 0.55, gazeX: 0.2, browRaise: 0.2 })],
      [w('s08c_1', 'this...') + 0.3, expr('wonder', { gazeY: 0.5, browInner: 0.4, tears: 0.3 })],
      [w('s08c_2', 'you'), expr('moved', { gazeY: 0.5, tears: 0.5, lipTremble: 0.5, browInner: 0.7 })],
      [not, expr('moved', { gazeY: 0.55, tears: 0.8, lipTremble: 0.8, browInner: 0.9 })],
      [w('s08c_2', 'alone.') + 0.6, expr('cryingSmile', { gazeY: 0.45, tears: 1, lipTremble: 0.6, smile: 0.3 })]], 0.6);
    p = lipsync(alive(p, t, 86, { blinkRate: 0.6, sac: 0.25 }), ctx.mouth('mira', t));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.015 }, g2 => {
      placeFig(g2, 'mira', POSES.stand, { s: 3, t, costume: 'island', light: 'interior', lightX: -0.7, facing: -1, breathe: 1 }, { ...p, yaw: 0.05, pitch: 0.35, light: LIGHT.interior, lightX: -0.7, rim: 0.4,
        tearDrop: clamp((t - not - 0.4) / 1.6), tearSide: -1, t }, 380, 650);
    });
    vignette(g, 0.4);
  },
};
