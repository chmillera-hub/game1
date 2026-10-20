// Scene 5 - night, the sacrifice: chest panel, cell into the lantern, beam.
import { W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, mix, rgba, vgrad, ellipse, withCam, handheld, vignette, glow, canvas } from '../lib/core.mjs';
import { expr, lipsync } from '../lib/face.mjs';
import { POSES, blendPose } from '../lib/body.mjs';
import { figure, head } from '../lib/cast.mjs';
import { pointNight } from '../lib/env.mjs';
import { tower, powerCell, beam } from '../lib/props.mjs';
import { shipLight, stars } from '../lib/fx.mjs';
import { track, alive, placeFig } from './s03.mjs';
import { directiveLevel } from '../lib/overlays.mjs';

const irisCol = (ctx, t) => mix('#ffcf7a', PAL.hud, directiveLevel(ctx, t));

export default {
  s05a(g, t, ctx) {
    const w = (l, k) => ctx.word(l, k).start, hh = handheld(t, 1.5, 51);
    const z = 1.0 + t * 0.006;
    pointNight(g, { t, tod: 22.5, camX: hh.x, camY: hh.y, zoom: z, lantern: 0 });
    // 'disappears' - the dark deepens a touch
    const dk = seg(t, w('s05a_1', 'disappears.'), w('s05a_1', 'disappears.') + 1.2);
    // distant ship slides along horizon on 'pass', gone by 'know'
    const p0 = w('s05a_2', 'ship') - 0.3, p1 = w('s05a_2', 'know') + 0.4;
    const sk = Math.min(seg(t, p0, p0 + 0.6), 1 - seg(t, p1 - 0.8, p1));
    withCam(g, { x: W / 2 + hh.x * 0.4, y: H / 2, zoom: z }, g2 => {
      shipLight(g2, { x: lerp(620, 300, clamp((t - p0) / (p1 - p0))), y: 716, t, k: sk });
    }, 0.4);
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: z }, g2 => {
      tower(g2, { x: 190, y: 905, s: 0.55, build: 1, lantern: 0, light: LIGHT.night, t });
      // Keeper silhouette on the point, eyes glowing; head follows the ship
      const follow = seg(t, p0, p1) ;
      figure(g2, 'keeper', POSES.stand, { x: 470, y: 892, s: 0.26, t, costume: 'worn', light: 'night', lightX: 0.6, facing: -1 },
        { ...alive(expr('neutral', { gazeX: lerp(-0.3, 0.4, follow) }), t, 7), yaw: lerp(-0.1, 0.3, follow), glow: 1, glowColor: '#ffcf7a' });
      // eye glints readable at this size
      glow(g2, 470 - 4, 892 - 0.26 * 940, 14, '#ffcf7a', 0.55);
      // 'roof' / 'way through' faint memory of the hut and channel - small reed hut silhouette on the hill
    });
    g.fillStyle = `rgba(2,6,16,${0.18 * dk})`; g.fillRect(0, 0, W, H);
    vignette(g, 0.5);
  },

  s05b(g, t, ctx) {
    const w = (l, k) => ctx.word(l, k).start, hh = handheld(t, 2.2, 52);
    const open = seg(t, 0.4, 1.4, ease.outCubic);
    const warn = w('s05b_1', 'warning.'), shorten = w('s05b_1', 'shorten'), pct = w('s05b_1', 'percent.');
    const stay = w('s05b_2', 'stay'), light = w('s05b_3', 'light');
    const cellOut = seg(t, shorten - 0.1, shorten + 1.4, ease.inOut);
    // hesitation tremble strongest between 'Removing' and 'percent'
    const trem = Math.min(seg(t, w('s05b_1', 'removing') - 0.3, w('s05b_1', 'removing')), 1 - seg(t, pct, pct + 1.5));
    const pose = { ...blendPose(POSES.chestOpen, POSES.holdUp, seg(t, light - 0.4, light + 0.6) * 0.25) };
    pose.aR = pose.aR.map((v, i) => v + (i === 1 ? noise1(t * 11, 5) * 4 * trem : 0));
    let p = track(t, [
      [0, expr('focused', { gazeY: -0.55, eyeOpen: 0.85 })],
      [warn, expr('worried', { gazeY: -0.5, browKnit: 0.8, browInner: 0.4 })],
      [shorten, expr('pained', { gazeY: -0.6, browKnit: 1, browInner: 0.6, mouthPress: 0.6 })],
      [pct + 0.4, expr('sad', { gazeY: -0.4, gazeX: 0.2, browKnit: 0.5 })],
      [w('s05b_2', 'i'), expr('tender', { gazeY: -0.2, gazeX: 0.1 })],
      [stay, expr('tender', { gazeY: -0.65, gazeX: 0.25, eyeOpen: 0.75, smile: 0.15 })],
      [light, expr('determined', { gazeY: 0.75, gazeX: 0.4, eyeOpen: 1.05, smile: 0.25, browInner: 0.1 })],
    ], 0.6);
    p = lipsync(alive(p, t, 21, { sac: 0.5 }), ctx.mouth('keeper', t));
    const lookUp = seg(t, light - 0.3, light + 0.5);
    // dark night backdrop, blurred
    pointNight(g, { t, tod: 22.5, camX: 60 + hh.x, camY: -120, zoom: 1.15 });
    g.fillStyle = 'rgba(4,8,20,0.45)'; g.fillRect(0, 0, W, H);
    const cellK = open * (0.85 + 0.15 * Math.sin(t * 7) * (1 - cellOut * 0.5));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.012, rot: hh.rot }, g2 => {
      placeFig(g2, 'keeper', pose, { s: 2.0, t, costume: 'worn', light: 'night', lightX: 0.6, facing: 1, chestOpen: open, cellOut },
        { ...p, pitch: lerp(-0.35, 0.3, lookUp), yaw: lerp(-0.05, 0.25, lookUp), glow: 0.85, glowColor: irisCol(ctx, t), rim: 0.5, lipTremble: trem * 0.4, t }, 350, 330);
      // under-light from the cells onto face and chest (gold, cyan core)
      glow(g2, 330, 720, 330, PAL.cellGlow, 0.45 * cellK);
      glow(g2, 330, 720, 120, PAL.hud, 0.25 * cellK);
      glow(g2, 350, 420, 200, PAL.cellGlow, 0.18 * cellK);
    });
    vignette(g, 0.55);
  },

  s05c(g, t, ctx) {
    const hh = handheld(t, 1.5, 53);
    const place = 1.2, ign = 1.9;
    const lan = seg(t, ign, ign + 0.5, ease.outCubic);
    const phi = Math.PI * 0.85 + Math.max(0, t - ign) * 1.15, cph = Math.cos(phi); // rotating beam: left -> toward camera -> right
    const ang = cph < 0 ? Math.PI + 0.05 : -0.05;
    const z = 1 + t * 0.01;
    pointNight(g, { t, tod: 22.5, camX: hh.x, camY: 120 + hh.y, zoom: z, lantern: lan, beamAngle: lan > 0 ? (cph < 0 ? 2.9 : 0.24) : null });
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: z }, g2 => {
      const L = mix('#8fa6d6', '#ffd98a', lan) ;
      const top = tower(g2, { x: 360, y: 1110, s: 1.45, build: 1, lantern: lan, beamAngle: null, light: lan > 0.4 ? LIGHT.beam : LIGHT.night, t });
      // Keeper on the top ledge, reaching the cell into the lantern housing
      const reach = seg(t, 0.2, place, ease.inOut);
      figure(g2, 'keeper', blendPose(POSES.stand, POSES.holdUp, reach), { x: 470, y: top.ly + 95, s: 0.24, t, costume: 'worn', light: lan > 0.3 ? 'beam' : 'night', lightX: -0.8, facing: -1 },
        { ...alive(expr(lan > 0.5 ? 'awe' : 'focused', { gazeY: 0.5 }), t, 9), glow: 1 });
      const cx = lerp(450, 362, reach), cy = lerp(top.ly + 10, top.ly, reach);
      if (lan > 0) beam(g2, { x: top.lx, y: top.ly, angle: ang, length: 150 + 1300 * Math.abs(cph), spread: 0.1 + 0.08 * (1 - Math.abs(cph)), intensity: lan * (0.5 + 0.5 * Math.abs(cph)) });
      if (lan > 0 && Math.sin(phi) < 0) glow(g2, top.lx, top.ly, 260, PAL.beamHot, lan * 0.6 * (1 - Math.abs(cph)));
      if (t < ign + 0.2) powerCell(g2, { x: cx, y: cy, s: 0.4, glow: 1 - lan });
    });
    // big warm bloom on ignition
    const bloom = Math.max(0, Math.exp(-Math.max(0, t - ign) * 2.2)) * seg(t, ign - 0.1, ign + 0.15);
    glow(g, 360, 300, 900, PAL.beam, 0.75 * bloom);
    glow(g, 360, 300, 500, PAL.beamHot, 0.25 * lan + 0.4 * bloom);
    vignette(g, 0.4);
  },

  s05d(g, t, ctx) {
    const hh = handheld(t, 1.5, 54), w = k => ctx.word('s05d_1', k).start;
    // backdrop: night sky with beam cone passing
    g.fillStyle = vgrad(g, 0, 0, 0, H, [[0, '#070d24'], [0.55, '#122040'], [1, '#08101e']]); g.fillRect(0, 0, W, H);
    stars(g, { t, k: 0.8, horizonY: H * 0.7, seed: 5 });
    const ph = (t + 0.9) / 3.0; // beam passes ~ every 3 s
    const sweep = (ph % 1);
    beam(g, { x: -200, y: 120, angle: lerp(0.9, -0.2, sweep), length: 1600, spread: 0.12, intensity: 0.5 });
    let p = track(t, [
      [0, expr('tender', { eyeOpen: 0.6, smile: 0.25, gazeX: -0.2, gazeY: 0.15 })],
      [w('no.'), expr('tender', { eyeOpen: 0.55, smile: 0.35, gazeX: -0.1 })],
      [w('helpful.'), expr('smile', { eyeOpen: 0.55, lowerLid: 0.45, smile: 0.7, gazeX: -0.25, gazeY: 0.2 })],
    ], 0.7);
    p = lipsync(alive(p, t, 31, { blinkRate: 0.7, sac: 0.4 }), ctx.mouth('keeper', t));
    const shakeNo = Math.sin(clamp((t - w('no.')) / 0.6) * Math.PI * 2) * 0.08 * (t > w('no.') && t < w('no.') + 0.6 ? 1 : 0);
    const face = { ...p, x: 360 + hh.x, y: 430 + hh.y + Math.sin(t * 1.4) * 3, s: 1.15 + t * 0.012, yaw: -0.15 + shakeNo,
      pitch: 0.08, roll: -0.03, glow: 0.7, glowColor: '#ffcf7a', wind: 0.4, windDir: 1, rim: 0.6, t };
    const drawK = (gg, light, lx) => placeFig(gg, 'keeper', POSES.stand, { s: 2.6, t, costume: 'worn', light, lightX: lx, facing: 1, chestOpen: 0 },
      { ...face, x: undefined, y: undefined, s: undefined, yaw: face.yaw - 0.25 }, face.x, face.y);
    drawK(g, 'night', 0.6);
    // beam-lit pass: same head in beam light, revealed through a moving band
    const bx = lerp(-300, W + 300, sweep);
    const c = canvas('s05d:lit'); const x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H); x.globalCompositeOperation = 'source-over';
    drawK(x, 'beam', -0.9);
    x.globalCompositeOperation = 'destination-in';
    const gr = x.createLinearGradient(bx - 260, 0, bx + 260, 0);
    gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(0.5, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = gr; x.fillRect(0, 0, W, H); x.globalCompositeOperation = 'source-over';
    g.drawImage(c, 0, 0);
    glow(g, bx, 380, 260, PAL.beam, 0.22);
    vignette(g, 0.45);
  },
};
