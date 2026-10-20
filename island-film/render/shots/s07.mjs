// Scene 7 - the storm, the light, the marked channel.
import { W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, mix, rgba, withCam, handheld, blurLayer, vignette, glow } from '../lib/core.mjs';
import { expr, lipsync, blend } from '../lib/face.mjs';
import { POSES, blendPose } from '../lib/body.mjs';
import { head } from '../lib/cast.mjs';
import { stormSea, reefChannel } from '../lib/env.mjs';
import { boat, markerStone, beam } from '../lib/props.mjs';
import { rain, faceDrops, lightning } from '../lib/fx.mjs';
import { track, alive, placeFig } from './s03.mjs';

const W_ = ctx => (id, w) => ctx.word(id, w).start;
// <=3 lightning flashes per shot
const flash = (t, times) => times.reduce((m, a) => Math.max(m, t > a ? Math.exp(-(t - a) * 7) * (t - a < 0.08 ? 1 : 0.8) : 0), 0);
const lightStorm = (fl) => ({ ...LIGHT.storm, key: mix(LIGHT.storm.key, '#e8f2ff', fl * 0.7) });

export default {
  s07a(g, t, ctx) {
    const w = W_(ctx), fl = flash(t, [0.4, 5.2, 8.0]);
    const roll = Math.sin(t * 1.3) * 0.09 + noise1(t * 0.7, 3) * 0.04, heave = Math.sin(t * 1.3 + 0.8) * 26;
    const look = seg(t, w('s07a_2', 'look!') - 0.2, w('s07a_2', 'look!') + 0.4);
    const push = seg(t, 4.2, 6.4) * 0.12;
    stormSea(g, { t, lightning: fl, rain: 1, roll: roll * 0.4, zoom: 1.02 + push * 0.5 });
    // the distant light, appearing on "light!"
    const la = seg(t, w('s07a_2', 'light!') - 0.3, w('s07a_2', 'light!') + 0.4);
    if (la > 0) { const ang = Math.PI + 0.25 + Math.sin(t * 0.9) * 0.35; glow(g, 120, 470, 26, PAL.beam, la);
      beam(g, { x: 120, y: 470, angle: ang - Math.PI, length: 600, spread: 0.06, intensity: la * 0.55 }); }
    const hh = handheld(t, 6, 71);
    withCam(g, { x: W / 2 + hh.x + push * 300, y: H / 2 + hh.y - push * 200, zoom: 1 + push }, g2 => {
      g2.save(); g2.translate(360, 860 + heave); g2.rotate(roll); g2.translate(-360, -860);
      const L = lightStorm(fl);
      boat(g2, { x: 360, y: 860, s: 1.55, roll: 0, sail: 0, light: L });
      // Mira at the mast (left of mast), Grandpa at stern tiller (right)
      let pm = track(t, [[0, expr('scared', { gazeX: 0.4, browInner: 0.9 })],
        [w('s07a_1', 'mast!'), expr('scared', { gazeX: 0.5, eyeOpen: 1.1, mouthPress: 0.6 })],
        [w('s07a_2', 'grandpa!') - 0.3, expr('surprised', { gazeX: -0.6, gazeY: 0.1 })],
        [w('s07a_2', 'light!'), expr('hopeful', { gazeX: -0.8, eyeOpen: 1.25, browRaise: 0.6, smile: 0.3 })],
        [w('s07a_3', 'nothing'), expr('determined', { gazeX: -0.7, browRaise: 0.2 })]], 0.5);
      pm = lipsync(alive(pm, t, 72, { sac: 0.6 }), ctx.mouth('mira', t));
      const mPose = blendPose(POSES.cling, POSES.point, look * 0.7);
      placeFig(g2, 'mira', mPose, { s: 0.5, t, costume: 'storm', hood: 1, light: L, lightX: -0.3, facing: -1, wet: 1, breathe: 1 },
        { ...pm, yaw: -0.2 * look, hood: 1, wet: 1, rim: 0.6 + fl * 0.4, roll: noise1(t * 2, 4) * 0.05 }, 300, 560);
      let pg = track(t, [[0, expr('determined', { gazeX: -0.5, browInner: -0.4 })],
        [w('s07a_1', 'hold'), expr('shout', { gazeX: -0.6 })],
        [w('s07a_2', 'look!'), expr('worried', { gazeX: -0.7, browInner: 0.4 })],
        [w('s07a_3', 'out'), expr('surprised', { gazeX: -0.9, gazeY: 0.1, eyeOpen: 1.15 })],
        [w('s07a_3', 'nothing'), expr('worried', { gazeX: -0.9, browInner: 0.7, eyeOpen: 1.1 })]], 0.5);
      pg = lipsync(alive(pg, t, 73, { sac: 0.5 }), ctx.mouth('grandpa', t));
      placeFig(g2, 'grandpa', POSES.tiller, { s: 0.42, t, costume: 'storm', light: L, lightX: -0.3, facing: -1, wet: 1, breathe: 1 },
        { ...pg, yaw: -0.15 - 0.25 * look, wet: 1, rim: 0.6 + fl * 0.4 }, 480, 470);
      g2.restore();
    });
    // foreground wave crest
    g.fillStyle = rgba('#0c1824', 0.9); g.beginPath(); g.moveTo(0, H);
    for (let x = 0; x <= W; x += 40) g.lineTo(x, 1150 - 60 * Math.max(0, Math.sin(x * 0.006 + t * 1.6)) + noise1(x * 0.01 + t, 9) * 20);
    g.lineTo(W, H); g.fill();
    rain(g, { t, intensity: 1, angle: 0.3 });
    lightning(g, { k: fl * 0.7, x: 520, seed: Math.floor(t * 0.4) });
    vignette(g, 0.5);
  },

  s07b(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 3, 74);
    // beam sweeps right->left across the face, peaking on "There is now"
    const sweep = seg(t, 0.4, 2.6, ease.inOutSine), bx = lerp(820, -120, sweep);
    const onFace = Math.exp(-(((bx - 360) / 170) ** 2)), lit2 = Math.max(onFace, seg(t, 1.2, 1.9) * 0.45);
    blurLayer(g, 's07b_bg', 6, x => stormSea(x, { t, rain: 1 }));
    g.fillStyle = rgba('#0a1420', 0.35); g.fillRect(0, 0, W, H);
    const there = w('s07b_1', 'there');
    let p = track(t, [[0, expr('worried', { gazeX: -0.3, gazeY: 0.1, browInner: 0.6 })],
      [0.75, expr('surprised', { gazeX: -0.15, gazeY: 0.25, eyeOpen: 1.3, mouthOpen: 0.45, pupil: 0.8 })],
      [there, expr('awe', { gazeX: -0.1, gazeY: 0.25, eyeOpen: 1.2, pupil: 0.85 })],
      [2.4, expr('awe', { gazeX: -0.1, gazeY: 0.2, smile: 0.55, mouthAsym: 0.2, lowerLid: 0.3, tears: 0.3 })]], 0.5);
    p = lipsync(alive(p, t, 75, { sac: 0.3, blinkRate: 0.6 }), ctx.mouth('grandpa', t));
    const light = { ...LIGHT.storm, key: mix(LIGHT.storm.key, PAL.beam, lit2), rim: PAL.beamHot };
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.02 }, g2 => {
      placeFig(g2, 'grandpa', POSES.tiller, { s: 2.9, t, costume: 'storm', light, lightX: lerp(1, -1, sweep), facing: -1, wet: 1, breathe: 1 }, { ...p, yaw: 0.1, pitch: 0.1 + seg(t, 0.6, 1.2) * 0.08, light, lightX: lerp(1, -1, sweep),
        rim: 0.5 + onFace * 0.5, wet: 1, t }, 360, 470);
      faceDrops(g2, { x: 220, y: 380, w: 280, h: 260, t, k: 0.9 });
    });
    // the beam band itself
    g.save(); g.globalCompositeOperation = 'lighter';
    const gr = g.createLinearGradient(bx - 200, 0, bx + 200, 0);
    gr.addColorStop(0, 'rgba(255,217,138,0)'); gr.addColorStop(0.5, rgba(PAL.beam, 0.35)); gr.addColorStop(1, 'rgba(255,217,138,0)');
    g.fillStyle = gr; g.fillRect(0, 0, W, H); g.restore();
    rain(g, { t, intensity: 0.6, angle: 0.25 });
    vignette(g, 0.5);
  },

  s07c(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 3, 76);
    const ang = 0.15 + Math.sin(t * 0.8) * 0.45, fl = flash(t, [0.2]);
    reefChannel(g, { t, beamAngle: ang, lightning: fl, rain: 1, camX: hh.x - t * 8, camY: hh.y, zoom: 1.02 + t * 0.01 });
    const lightK = clamp(1 - Math.abs(Math.sin(t * 0.8) * 0.45 + 0.15 - 0.4) * 2);
    // marker stones: white-painted, glinting as the beam passes, revealed on "marked"
    const mk = seg(t, w('s07c_1', 'marked') - 0.6, w('s07c_1', 'path,'));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.012 }, g2 => {
      const marks = [[180, 760, 0.7, true], [540, 740, 0.65, false], [230, 640, 0.45, false], [490, 630, 0.42, true], [300, 580, 0.3, false], [430, 575, 0.3, false]];
      for (const [x, y, s, pole] of marks) { markerStone(g2, { x, y, s, pole });
        glow(g2, x, y - 20 * s, 60 * s, PAL.beamHot, (0.25 + lightK * 0.5) * (0.4 + mk * 0.6)); }
      const bxp = lerp(360, 380, t / 4), by = lerp(820, 690, seg(t, 0, 3.8, ease.linear));
      const bs = lerp(0.55, 0.4, t / 4), roll = Math.sin(t * 1.5) * 0.07;
      g2.save(); g2.translate(bxp, by); g2.rotate(roll); g2.translate(-bxp, -by);
      boat(g2, { x: bxp, y: by, s: bs, light: LIGHT.storm });
      placeFig(g2, 'mira', blendPose(POSES.cling, POSES.point, seg(t, w('s07c_1', 'look!') - 0.4, w('s07c_1', 'look!'))),
        { s: 0.22, t, costume: 'storm', hood: 1, light: 'storm', facing: 1, wet: 1 },
        lipsync(alive(expr('surprised'), t, 77), ctx.mouth('mira', t)), bxp - 30 * bs, by - 170 * bs);
      placeFig(g2, 'grandpa', POSES.tiller, { s: 0.22, t, costume: 'storm', light: 'storm', facing: 1, wet: 1 },
        alive(expr('focused'), t, 78), bxp + 90 * bs, by - 165 * bs);
      g2.restore();
    });
    rain(g, { t, intensity: 0.8, angle: 0.25 });
    vignette(g, 0.45);
  },
};
