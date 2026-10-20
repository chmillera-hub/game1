// Scene 6 - years pass, grief, realization, power-down.
import { W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, mix, rgba, vgrad, ellipse, withCam, handheld, blurLayer, vignette, cached, glow } from '../lib/core.mjs';
import { expr, lipsync } from '../lib/face.mjs';
import { POSES, blendPose } from '../lib/body.mjs';
import { head } from '../lib/cast.mjs';
import { islandWide, hutDoorway, palmUp, towerBase, ISLAND } from '../lib/env.mjs';
import { crab, beam } from '../lib/props.mjs';
import { rain, faceDrops, dayCounter, powerReadout, leavesVines } from '../lib/fx.mjs';
import { track, alive, placeFig } from './s03.mjs';
import { directiveLevel } from '../lib/overlays.mjs';

const irisCol = (ctx, t) => mix('#ffcf7a', PAL.hud, directiveLevel(ctx, t));
const W_ = ctx => (id, w) => ctx.word(id, w).start;

export default {
  // ------------------------------------------------ time-lapse years
  s06a(g, t, ctx) {
    const w = W_(ctx);
    const days = t * 1.6, tod = (6 + days * 24) % 24;
    const storm = clamp(Math.max(0, Math.sin(t * 0.9 + 1)) ** 6 * 1.4);
    const ka = (t * 0.25) % 1;
    islandWide(g, { t: t * 3, tod, hut: 1, tower: 1, lantern: 0, palmGrowth: seg(t, 0, ctx.dur, ease.linear) * 0.85 + 0.15,
      storm, keeperTiny: { x: ISLAND.tower[0] + 30 + Math.sin(t * 2) * 10, y: ISLAND.tower[1] }, zoom: 1.02 + t * 0.004 });
    if (storm > 0.2) rain(g, { t, intensity: storm * 0.7 });
    // HUD log counter
    const cs = [['s06a_1', 'DAY 400'], ['s06a_2', 'DAY 2,000'], ['s06a_3', 'DAY 7,300']];
    for (const [id, txt] of cs) { const L = ctx.line(id), a = clamp((t - ctx.word(id, 'day').start + 0.05) / 0.2) * clamp((L.end + 0.5 - t) / 0.3);
      if (a > 0) dayCounter(g, { text: txt, k: a, y: H * 0.12 }); }
    vignette(g, 0.3);
  },

  // ------------------------------------------------ grief in the rain
  s06b(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 2, 61);
    const dEnd = ctx.word('s06b_3', 'data.').end, drop = seg(t, dEnd + 0.1, dEnd + 1.6, ease.inOutSine);
    blurLayer(g, 's06b_bg', 3, x => hutDoorway(x, { t, rain: 1 }));
    rain(g, { t, intensity: 0.8 });
    let p = track(t, [[0, expr('tired', { gazeX: -0.3, gazeY: -0.15 })],
      [w('s06b_1', 'directive...'), expr('sad', { gazeX: -0.2, gazeY: 0.25, browInner: 0.6 })],
      [w('s06b_1', 'ever'), expr('pained', { gazeX: -0.35, gazeY: 0.0, browInner: 0.8 })],
      [w('s06b_2', 'help?'), expr('pained', { gazeX: -0.1, gazeY: 0.2, browInner: 1, eyeOpen: 0.85, lipTremble: 0.5 })],
      [w('s06b_3', 'insufficient'), expr('sad', { gazeX: 0, gazeY: 0.1, browInner: 0.9, eyeOpen: 0.9 })],
      [dEnd + 0.4, expr('sad', { eyeOpen: 0, mouthPress: 0.8, smile: -0.35, browInner: 0.9 })]], 0.7);
    p = lipsync(alive(p, t, 61, { blinkRate: 0.6, sac: 0.5 }), ctx.mouth('keeper', t));
    const tearP = ((t + 1.2) / 3.2) % 1;
    const pose = blendPose(POSES.sitDoorway, POSES.sitRest, drop * 0.5);
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.008 }, g2 => {
      placeFig(g2, 'keeper', pose, { s: 1.7, t, costume: 'worn', light: 'rain', lightX: -0.4, facing: 1, wet: 1, breathe: 0.7 },
        { ...p, yaw: 0.05, pitch: -0.1 - drop * 0.25, glow: 0.45, glowColor: irisCol(ctx, t), wet: 1, wetHair: 1, tears: 0.6,
          tearDrop: tearP, tearSide: (Math.floor((t + 1.2) / 3.2) % 2) ? 1 : -1, rim: 0.5 }, 330, 430 + drop * 40);
      faceDrops(g2, { x: 250, y: 420 + drop * 40, w: 170, h: 180, t, k: 0.8 });
      crab(g2, { x: 600, y: 1080, s: 1.1, t, eyeYaw: -0.6 + Math.sin(t * 0.7) * 0.2, clawRaise: drop * 0.2, light: LIGHT.rain });
    });
    vignette(g, 0.45);
  },

  // ------------------------------------------------ the tall palm
  s06c(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 2, 62);
    palmUp(g, { tod: 7.5, t, camX: hh.x, camY: hh.y - t * 3, zoom: 1.02 + t * 0.006 });
    const up = seg(t, w('s06c_1', 'tree') - 0.4, w('s06c_1', 'tree') + 0.4);
    let p = track(t, [[0, expr('tired', { gazeY: 0.3, gazeX: 0.1 })],
      [w('s06c_1', 'planted'), expr('wonder', { gazeY: 0.6, eyeOpen: 1 })],
      [w('s06c_1', 'first'), expr('tender', { gazeY: 0.5 })],
      [w('s06c_2', 'shade.'), expr('tender', { gazeY: -0.4, gazeX: -0.2 })],
      [w('s06c_2', 'grew'), expr('awe', { gazeY: 0.7, smile: 0.2 })]], 0.6);
    p = lipsync(alive(p, t, 62, { sac: 0.6 }), ctx.mouth('keeper', t));
    const pitch = 0.15 + up * 0.25 - env2(t, w('s06c_2', 'sit'), w('s06c_2', 'it') - 0.2) * 0.3 + seg(t, w('s06c_2', 'grew') - 0.3, w('s06c_2', 'grew') + 0.5) * 0.1;
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.01 }, g2 =>
      placeFig(g2, 'keeper', POSES.standLookUp, { s: 1.15, t, costume: 'worn', light: 'dawn', lightX: 0.6, facing: -1 },
        { ...p, pitch, glow: 0.5, wind: 0.5, windDir: -1, rim: 0.7 }, 430, 620));
    vignette(g, 0.3);
  },

  // ------------------------------------------------ realization CU
  s06d(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.5, 63);
    g.drawImage(cached('s06d_bg', x => {
      x.fillStyle = vgrad(x, 0, 0, 0, H, [[0, '#9fc7b0'], [0.5, '#d9d6a8'], [1, '#6f8a6a']]); x.fillRect(0, 0, W, H);
      for (let i = 0; i < 9; i++) { x.fillStyle = rgba(i % 2 ? '#fff4c8' : '#b8e0c0', 0.35); x.beginPath(); ellipse(x, (i * 197) % W, 120 + (i * 131) % 700, 50 + i * 4, 50 + i * 4); x.fill(); }
      x.fillStyle = rgba('#3f5a4a', 0.35); for (let i = 0; i < 5; i++) { x.beginPath(); ellipse(x, i * 170, -40, 140, 90, 0.4); x.fill(); }
    }), 0, 0);
    let p = track(t, [[0, expr('sad', { gazeY: -0.2, gazeX: -0.1, browInner: 0.5 })],
      [w('s06d_1', 'maybe'), expr('wonder', { gazeY: 0.25, eyeOpen: 1.05, browRaise: 0.3 })],
      [w('s06d_1', 'help'), expr('hopeful', { gazeY: 0.3, browRaise: 0.35, tears: 0.6 })],
      [w('s06d_2', 'people'), expr('tender', { gazeX: 0.25, gazeY: 0.15, tears: 0.7 })],
      [w('s06d_3', 'matter,'), expr('moved', { gazeY: 0.2, smile: 0.4, tears: 0.85 })],
      [w('s06d_3', 'them.'), expr('cryingSmile', { gazeY: 0.15, smile: 0.55, tears: 0.9, lowerLid: 0.3 })],
      [w('s06d_4', 'updating'), expr('relief', { gazeY: 0.25, smile: 0.5, tears: 0.8 })]], 0.8);
    p = lipsync(alive(p, t, 63, { sac: 0.5, blinkRate: 0.8 }), ctx.mouth('keeper', t));
    const z = 1 + t * 0.012;
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y - 60, zoom: z }, g2 => {
      placeFig(g2, 'keeper', POSES.stand, { s: 2.6, t, costume: 'worn', light: 'shade', lightX: 0.5, facing: 1 },
        { ...p, yaw: -0.4 + Math.sin(t * 0.3) * 0.03, pitch: (p.gazeY ?? 0) * 0.15, roll: Math.sin(t * 0.4) * 0.02,
          rim: 0.6, glow: 0.55, glowColor: irisCol(ctx, t), wind: 0.3 }, 360, 440);
    });
    vignette(g, 0.35);
  },

  // ------------------------------------------------ power down
  s06e(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.5, 64);
    const ky = w('s06e_3', 'light'), meE = ctx.line('s06e_3').end;
    const dim = seg(t, meE + 0.2, meE + 2.6, ease.inOutSine), lapse = seg(t, meE + 2.8, ctx.dur - 0.2, ease.linear);
    const tl = t + lapse * 40; // accelerated time for the lapse
    const bA = -2.2 + Math.sin(tl * 0.55) * 1.0;
    towerBase(g, { tod: 18.7 + lapse * 1.5, t: tl, camX: hh.x * 0.5, camY: hh.y });
    beam(g, { x: 170, y: 60, angle: bA, length: 900, spread: 0.13, intensity: 0.8 });
    const look = seg(t, ky - 0.4, ky + 0.3) * (1 - seg(t, meE + 0.4, meE + 2.4));
    let p = track(t, [[0, expr('tired', { gazeX: 0.4, gazeY: 0 })],
      [w('s06e_1', 'four'), expr('tired', { gazeX: 0.2, gazeY: -0.3, browInner: 0.4 })],
      [w('s06e_2', 'alright.'), expr('tender', { gazeX: 0.4, smile: 0.25, eyeOpen: 0.8 })],
      [ky, expr('hopeful', { gazeY: 0.8, gazeX: -0.2, smile: 0.35 })],
      [meE + 0.5, expr('tender', { gazeY: 0, smile: 0.25, eyeOpen: 0.7 })]], 0.6);
    p = lipsync(alive(p, t, 64, { blinkRate: 0.5, sac: 0.4 * (1 - dim) }), ctx.mouth('keeper', t));
    p.eyeOpen = lerp(p.eyeOpen ?? 1, 0, dim); if (dim > 0.01) p.blink = (p.blink ?? 0) * (1 - dim);
    const pose = POSES.sitGround;
    const dormant = lapse > 0.5;
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.006 }, g2 => {
      placeFig(g2, 'keeper', pose, { s: 0.85, t: t, costume: dormant ? 'dormant' : 'worn', light: 'dusk', lightX: 0.7, facing: -1,
        sand: lapse, vines: lapse, breathe: 1 - dim },
        { ...p, pitch: look * 0.5 - dim * 0.45, glow: 0.55 * (1 - dim), rim: 0.6 * (1 - lapse * 0.5), glowColor: irisCol(ctx, t) }, 400, 560 + dim * 30);
      if (lapse > 0) leavesVines(g2, { x: 290, y: 540, w: 240, h: 380, k: lapse, seed: 6 });
      crab(g2, { x: 240, y: 960, s: 0.8, t, eyeYaw: 0.5 - look * 0.4, clawRaise: look * 0.3, legs: 1 - lapse, light: LIGHT.dusk });
    });
    if (lapse > 0) { g.fillStyle = rgba('#d9c39a', 0.15 * Math.sin(lapse * 40) ** 2); g.fillRect(0, 0, W, H); }
    const pa = env2(t, w('s06e_1', 'power:') - 0.1, ctx.line('s06e_1').end + 0.5);
    if (pa > 0) powerReadout(g, { pct: 4, k: pa, x: W / 2, y: H * 0.18, size: 26 });
    vignette(g, 0.4);
  },
};

function env2(t, a, b) { return clamp((t - a) / 0.25) * clamp((b - t) / 0.3); }
