// Scene 9 - the waking. Emotional climax: lives on faces.
import { cached, W, H, PAL, LIGHT, clamp, lerp, seg, ease, noise1, mix, rgba, ellipse, withCam, handheld, blurLayer, vignette, glow, vgrad } from '../lib/core.mjs';
import { head, headSocket } from '../lib/cast.mjs';
import { expr, lipsync } from '../lib/face.mjs';
import { POSES, blendPose, walkPose, drawHand, handPos } from '../lib/body.mjs';
import { towerBase } from '../lib/env.mjs';
import { crab } from '../lib/props.mjs';
import { glint, leavesVines } from '../lib/fx.mjs';
import { directiveLevel } from '../lib/overlays.mjs';
import { track, alive, placeFig } from './s03.mjs';

const AMBER = '#ffcf7a';
const irisCol = (ctx, t) => mix(AMBER, PAL.hud, directiveLevel(ctx, t));
const W_ = ctx => (id, w) => ctx.word(id, w).start;
const TOD = 8.2;

// soft out-of-focus morning backdrop for close-ups (tower base, sea)
function bgSoft(g, t, key, { camX = 0, camY = 0, zoom = 1.25, blur = 7 } = {}) {
  const c = cached('s09soft:' + key, x => { const tmp = cached('s09raw:' + key, y => towerBase(y, { tod: TOD, t: 0, camX, camY, zoom }));
    x.filter = `blur(${blur}px)`; x.drawImage(tmp, 0, 0); });
  const d = Math.sin(t * 0.3) * 6; g.drawImage(c, -12 + d, -12, W + 24, H + 24);
  g.save(); g.globalCompositeOperation = 'soft-light'; g.fillStyle = rgba('#ffd9a8', 0.25); g.fillRect(0, 0, W, H); g.restore();
}
// warm sun bloom from upper right
function sunBloom(g, a = 0.5) { glow(g, 640, 120, 420, '#ffe2b0', a); }

// Keeper CU face with iris glow / directive tint
// close-up with shoulders: place a full figure so its head lands at (x,y) with head scale s
function bust(g, who, o, face, x, y, s) {
  const pose = POSES.stand, facing = o.facing ?? 1, hs0 = headSocket(who, pose, { s: 1, x: 0, y: 0, facing }).s;
  placeFig(g, who, pose, { light: 'day', lightX: 0.6, ...o, s: s / hs0, breathe: 1 },
    { ...face, yaw: (face.yaw ?? 0) - 0.25 * facing }, x, y);
}
function keeperCU(g, t, ctx, p, x, y, s, extra = {}) {
  const f = { rim: 0.5, sand: 0.25, wind: 0.25, windDir: -1, ...p, ...extra, t, glowColor: irisCol(ctx, t) };
  bust(g, 'keeper', { t, costume: 'dormant', facing: -1, sand: 0.4, vines: 0.2 }, f, x, y, s);
}
function miraCU(g, t, p, x, y, s, extra = {}) {
  bust(g, 'mira', { t, costume: 'island', facing: 1 }, { rim: 0.4, wind: 0.3, windDir: -1, ...p, ...extra, t }, x, y, s);
}

export default {
  // ------------------------------------------------ WS approach
  s09a(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 2, 91), z = 1 + t * 0.008;
    towerBase(g, { tod: TOD, t, camX: hh.x * 0.5, camY: hh.y * 0.5, zoom: z });
    const careful = w('s09a_1', 'careful,'), okay = w('s09a_2', "it's");
    // Mira walks in from the right, slows, stops near Keeper
    const walkK = seg(t, 0, 3.4, ease.out);
    const mx = lerp(760, 470, walkK);
    const mPose = walkK < 0.98 ? blendPose(walkPose((t * 0.9) % 1), POSES.stand, seg(t, 2.6, 3.4)) : blendPose(POSES.stand, POSES.brush, seg(t, 4.8, 6.4) * 0.6);
    // Grandpa follows, reaches out on "Careful"
    const gx = lerp(820, 630, seg(t, 0, 2.6, ease.out));
    const gPose = blendPose(blendPose(walkPose((t * 0.8 + 0.3) % 1), POSES.stand, seg(t, 1.6, 2.6)), POSES.brush, env(t, careful - 0.2, okay + 0.6));
    const turnBack = env(t, careful + 0.3, okay + 0.5);
    let pm = track(t, [[0, expr('awe', { gazeX: -0.6, gazeY: -0.1 })],
      [careful + 0.4, expr('surprised', { eyeOpen: 1.05, mouthOpen: 0, gazeX: 0.7, browRaise: 0.4 })],
      [okay, expr('tender', { gazeX: 0.6, smile: 0.3 })],
      [w('s09a_2', 'been'), expr('hopeful', { gazeX: -0.7, gazeY: -0.2, smile: 0.25 })]], 0.5);
    pm = lipsync(alive(pm, t, 92), ctx.mouth('mira', t));
    let pg = track(t, [[0, expr('worried', { gazeX: -0.5 })], [okay + 0.4, expr('worried', { gazeX: -0.6, browInner: 0.5, smile: 0.05 })]], 0.6);
    pg = lipsync(alive(pg, t, 93, { blinkRate: 0.8 }), ctx.mouth('grandpa', t));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: z, rot: hh.rot }, g2 => {
      placeFig(g2, 'keeper', POSES.sitRest, { s: 0.62, t, costume: 'dormant', light: 'day', lightX: 0.6, breathe: 0, sand: 1, vines: 1 },
        { ...expr('sleep'), pitch: -0.35, glow: 0, t }, 300, 650);
      leavesVines(g2, { x: 230, y: 640, w: 170, h: 280, k: 1, seed: 9 });
      crab(g2, { x: 360, y: 870, s: 0.45, t, eyeYaw: noise1(t * 0.6, 4) * 0.6 + (t > 2.5 ? 0.5 : 0), clawRaise: env(t, 3.6, 4.6) * 0.5, light: LIGHT.day });
      placeFig(g2, 'grandpa', gPose, { s: 0.6, t, costume: 'island', facing: -1, light: 'day', lightX: 0.6 },
        { ...pg, yaw: -0.15 }, gx, 470);
      placeFig(g2, 'mira', mPose, { s: 0.62, t, costume: 'island', facing: -1, light: 'day', lightX: 0.6 },
        { ...pm, yaw: turnBack * 0.9 - 0.1 }, mx, 600 + Math.abs(Math.sin(t * 0.9 * Math.PI * 2)) * 4 * (1 - walkK));
    });
    sunBloom(g, 0.35); vignette(g, 0.35);
  },

  // ------------------------------------------------ insert: brushing sand off the solar plate
  s09b(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.5, 95), restored = w('s09b_1', 'restored.');
    bgSoft(g, t, 's09b_bg', { camX: -60, camY: 60, zoom: 1.4, blur: 10 });
    const cx = 360 + hh.x, cy = 520 + hh.y + t * 2;
    // shoulder plate: dark-blue solar cells on a curved pauldron
    g.save(); g.translate(cx, cy); g.rotate(-0.12 + t * 0.004);
    const PW = 460, PH = 270;
    g.fillStyle = mix(PAL.kSuitFaded ?? '#4f6b74', '#000', 0.15); g.beginPath(); g.roundRect(-PW / 2 - 40, PH / 2 - 10, PW + 80, 260, 40); g.fill();
    g.beginPath(); g.roundRect(-PW / 2, -PH / 2, PW, PH, 46); g.fillStyle = PAL.kPanel ?? '#1d2f5a'; g.fill();
    g.lineWidth = 4; g.strokeStyle = PAL.ink; g.stroke();
    g.save(); g.clip();
    const gr = g.createLinearGradient(-PW / 2, -PH / 2, PW / 2, PH / 2);
    gr.addColorStop(0, 'rgba(120,160,230,0.35)'); gr.addColorStop(0.5, 'rgba(20,30,70,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.3)');
    g.fillStyle = gr; g.fillRect(-PW, -PH, PW * 2, PH * 2);
    g.strokeStyle = PAL.kPanelGrid ?? '#3c5c9a'; g.lineWidth = 2;
    for (let i = -4; i <= 4; i++) { g.beginPath(); g.moveTo(i * 52, -PH); g.lineTo(i * 52, PH); g.stroke(); }
    for (let j = -2; j <= 2; j++) { g.beginPath(); g.moveTo(-PW, j * 52); g.lineTo(PW, j * 52); g.stroke(); }
    // sheen that blooms when clean
    const lit = seg(t, 1.4, 2.6);
    if (lit > 0) { const sx = lerp(-PW, PW, seg(t, 1.4, 3.2)); const sg = g.createLinearGradient(sx - 120, 0, sx + 120, 0);
      sg.addColorStop(0, 'rgba(255,240,200,0)'); sg.addColorStop(0.5, `rgba(255,240,200,${0.55 * lit})`); sg.addColorStop(1, 'rgba(255,240,200,0)');
      g.fillStyle = sg; g.fillRect(-PW, -PH, PW * 2, PH * 2); }
    // sand + leaf debris, wiped away left->right behind the hand
    const wipe = seg(t, 0.3, 1.9, ease.inOut), wx = lerp(-PW / 2 - 60, PW / 2 + 80, wipe);
    g.save(); g.beginPath(); g.rect(wx, -PH, PW * 2, PH * 2); g.clip();
    g.fillStyle = 'rgba(214,190,140,0.92)'; g.beginPath();
    for (let x = -PW / 2; x <= PW / 2; x += 30) g.lineTo(x, -40 + noise1(x * 0.05, 3) * 30);
    g.lineTo(PW / 2, PH); g.lineTo(-PW / 2, PH); g.fill();
    for (let i = 0; i < 6; i++) { g.fillStyle = i % 2 ? '#7a8a44' : '#5f6e36'; g.beginPath(); ellipse(g, -180 + i * 70, -60 + (i % 3) * 30, 34, 12, i * 0.7); g.fill(); }
    g.restore();
    g.restore();
    // falling sand beads at the hand's leading edge
    for (let i = 0; i < 14; i++) { const ph = (t * 1.7 + i / 14) % 1; if (wipe <= 0 || wipe >= 1) break;
      const x = cx + wx + 20 + (i % 5) * 8, y = cy + ph * 260; g.fillStyle = rgba('#d9c08a', 1 - ph); g.beginPath(); ellipse(g, x, y, 3, 3); g.fill(); }
    // Mira's small hand brushing across
    const hx = cx + wx + 40, hy = cy - 40 + Math.sin(t * 9) * 8 * (1 - seg(t, 1.8, 2.2));
    const away = seg(t, 2.0, 3.0);
    drawHand(g, { x: hx - 40 + away * 200, y: hy - 260 - away * 300, s: 2.4, rot: 2.6 - Math.sin(t * 9) * 0.1, side: 'R', who: 'mira', shape: 'brush', light: LIGHT.day, lightDir: [0.6, -0.8] });
    // sunlight hits: glint on "restored"
    glint(g, { x: cx + 120, y: cy - 70, s: 2.2, k: env(t, restored - 0.3, restored + 1.0, 0.25, 0.6) });
    glint(g, { x: cx - 90, y: cy + 10, s: 1.2, k: env(t, restored - 0.1, restored + 0.8, 0.25, 0.5) });
    sunBloom(g, 0.4 + 0.3 * seg(t, 1.4, 2.6)); vignette(g, 0.4);
  },

  // ------------------------------------------------ ECU eyes: boot
  s09c(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.2, 97);
    const scan = w('s09c_1', 'scanning'), people = w('s09c_2', 'people'), two = w('s09c_2', 'two.');
    bgSoft(g, t, 's09c_bg', { camX: 40, zoom: 1.5, blur: 12 });
    // boot flicker of the iris ring
    const fl = t < scan - 0.1 ? 0 : t < scan + 1.2 ? (Math.sin(t * 47) > 0.1 ? 0.35 + 0.65 * Math.abs(Math.sin(t * 13)) : 0.05) * seg(t, scan - 0.1, scan + 0.2) : 1;
    const glowV = lerp(0, 0.95, fl) * (0.92 + 0.08 * Math.sin(t * 6));
    let p = track(t, [[0, expr('sleep', { gazeY: -0.2 })],
      [scan + 0.9, expr('tired', { eyeOpen: 0.45, gazeX: -0.6 })],
      [scan + 1.6, expr('neutral', { eyeOpen: 0.85, gazeX: 0.6, pupil: 0.8 })],
      [people + 0.1, expr('wonder', { eyeOpen: 1.1, gazeX: -0.45, gazeY: -0.05, pupil: 1.0, mouthOpen: 0 })],
      [two, expr('wonder', { eyeOpen: 1.15, gazeX: -0.35, gazeY: 0.0, pupil: 1.3, mouthOpen: 0.05, browRaise: 0.5 })]], 0.6);
    // flutter while waking
    const flutter = t > scan + 0.3 && t < scan + 1.4 ? Math.max(0, Math.sin(t * 22)) * 0.5 : 0;
    p = alive(p, t, 98, { blinkRate: 0.6, sac: t > scan + 1.6 ? 0.6 : 0 });
    p.blink = Math.max(p.blink, flutter);
    // focus pull: background blur deeper as focus locks
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.012 }, g2 => {
      keeperCU(g2, t, ctx, p, 360, 470, 2.7, { glow: glowV, pitch: -0.05 + seg(t, scan + 1, scan + 2) * 0.05, rim: 0.4 });
    });
    // tiny HUD focus brackets on lock
    const lk = env(t, two - 0.1, ctx.dur, 0.2, 0.01) * (0.6 + 0.4 * Math.sin(t * 20));
    if (lk > 0) { g.save(); g.strokeStyle = rgba(PAL.hud, 0.6 * lk); g.lineWidth = 2; const s = lerp(90, 60, seg(t, two, two + 0.4));
      for (const [x, y] of [[180, 470], [540, 470]]) { g.strokeRect(x - s / 2 + hh.x, y - s / 2 + hh.y, s, s); } g.restore(); }
    vignette(g, 0.45);
  },

  // ------------------------------------------------ CU Keeper "Hello."
  s09d(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.4, 99), hello = w('s09d_1', 'hello.');
    const hurt = w('s09d_2', 'are'), water = w('s09d_2', 'water,'), north = w('s09d_2', 'north...');
    bgSoft(g, t, 's09d_bg', { camX: 50, zoom: 1.3, blur: 8 });
    let p = track(t, [[0, expr('wonder', { gazeX: -0.35, mouthOpen: 0.05 })],
      [hello - 0.3, expr('moved', { browInner: 0.8, browRaise: 0.3, gazeX: -0.35, tears: 0.6, lipTremble: 0.4, smile: 0.25, mouthPress: 0 })],
      [hello + 1.0, expr('tender', { gazeX: -0.35, tears: 0.6, lipTremble: 0.25, smile: 0.35 })],
      [hurt, expr('worried', { gazeX: -0.25, gazeY: -0.2, eyeOpen: 1.1, tears: 0.5 })],
      [water, expr('worried', { gazeX: 0.5, browInner: 0.5, tears: 0.4 })],
      [north + 0.4, expr('hopeful', { gazeX: -0.35, tears: 0.4, smile: 0.1 })]], 0.5);
    p = lipsync(alive(p, t, 100, { blinkRate: 0.7, sac: 0.5 }), ctx.mouth('keeper', t));
    const nodN = Math.sin(seg(t, north - 0.1, north + 0.5) * Math.PI) * 0.12; // head points north
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.01 }, g2 => {
      keeperCU(g2, t, ctx, p, 360, 470, 1.2, { glow: 0.85, yaw: -0.15 + seg(t, water - 0.2, water + 0.3) * 0.3 * (1 - seg(t, north + 0.3, north + 0.9)),
        pitch: -0.05 + nodN, roll: 0.05 * env(t, hello - 0.3, hello + 1.3) });
    });
    vignette(g, 0.4);
  },

  // ------------------------------------------------ CU Mira, smiling through tears
  s09e(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.6, 101), found = w('s09e_1', 'found'), every = w('s09e_1', 'everything.');
    const light = w('s09e_2', 'light.');
    bgSoft(g, t, 's09e_bg', { camX: -80, zoom: 1.3, blur: 8 });
    let p = track(t, [[0, expr('cryingSmile', { gazeX: 0.35, tearDrop: 0, tears: 0.9 })],
      [found, expr('cryingSmile', { gazeX: 0.35, tearDrop: 0.2, smile: 0.7 })],
      [every, expr('cryingSmile', { gazeX: 0.3, smile: 0.8, tearDrop: 0.7, browInner: 0.7 })],
      [light - 0.3, expr('cryingSmile', { gazeX: 0.25, gazeY: 0.45, smile: 0.6, tearDrop: 1, lowerLid: 0.3 })],
      [ctx.line('s09e_2').end + 0.2, expr('fond', { gazeX: 0.35, tears: 0.9, smile: 0.65 })]], 0.5);
    p = lipsync(alive(p, t, 102, { blinkRate: 1.2 }), ctx.mouth('mira', t));
    const nod = Math.sin(seg(t, found - 0.1, found + 0.7) * Math.PI * 2) * 0.12 + Math.sin(seg(t, every, every + 0.8) * Math.PI * 2) * 0.1;
    const breath = Math.sin(t * 2.2) * 0.02;
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.01 }, g2 => {
      miraCU(g2, t, p, 370, 480, 1.25, { yaw: 0.2, pitch: -nod + breath + seg(t, light - 0.5, light) * 0.15 * (1 - seg(t, light + 0.6, light + 1.2)), tearSide: -1 });
    });
    sunBloom(g, 0.3); vignette(g, 0.4);
  },

  // ------------------------------------------------ CU Keeper looks up at the lantern, then back
  s09f(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.2, 103), it = w('s09f_1', 'it...'), helped = w('s09f_1', 'helped?');
    bgSoft(g, t, 's09f_bg', { camX: 50, camY: -40, zoom: 1.3, blur: 8 });
    const up = env(t, 0.0, it - 0.05, 0.35, 0.4);
    let p = track(t, [[0, expr('wonder', { gazeX: -0.3 })], [0.3, expr('awe', { gazeY: 0.9, gazeX: 0.2 })],
      [it, expr('moved', { gazeX: -0.35, browInner: 0.9, tears: 0.75, lipTremble: 0.6, smile: 0 })],
      [helped + 0.5, expr('moved', { gazeX: -0.35, browInner: 0.95, tears: 0.85, lipTremble: 0.5, smile: 0.2, eyeOpen: 0.95 })]], 0.4);
    p = lipsync(alive(p, t, 104, { blinkRate: 0.6, sac: 0.4 }), ctx.mouth('keeper', t));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1.05 + t * 0.015 }, g2 => {
      keeperCU(g2, t, ctx, p, 360, 480 + up * 10, 1.25, { glow: 0.85, yaw: -0.1, pitch: up * 0.45 });
    });
    glow(g, 560, -40, 260, '#ffe7b0', 0.35 * up);
    vignette(g, 0.4);
  },

  // ------------------------------------------------ two-shot: Mira holds Keeper's hand; tear on "complete"
  s09g(g, t, ctx) {
    const w = W_(ctx), hh = handheld(t, 1.4, 105), saved = w('s09g_1', 'saved'), status = w('s09g_2', 'directive'), complete = w('s09g_3', 'complete.');
    bgSoft(g, t, 's09g_bg', { camX: -20, zoom: 1.15, blur: 6 });
    const z = 1 + t * 0.012;
    const take = seg(t, 0.2, 1.3);
    let pk = track(t, [[0, expr('moved', { gazeX: 0.4, gazeY: -0.1, tears: 0.7 })],
      [saved + 0.3, expr('moved', { gazeX: 0.45, browInner: 0.9, tears: 0.85, lipTremble: 0.5, smile: 0.25 })],
      [status, expr('moved', { gazeX: 0.2, gazeY: -0.4, browInner: 0.8, tears: 0.9, smile: 0.35, eyeOpen: 0.7 })],
      [complete, expr('tender', { gazeX: 0.4, gazeY: -0.3, smile: 0.6, eyeOpen: 0.45, lowerLid: 0.45, tears: 1, browInner: 0.7 })]], 0.8);
    pk = alive(pk, t, 106, { blinkRate: 0.5, sac: 0.35 });
    pk.tearDrop = seg(t, complete - 0.1, complete + 1.3, ease.inOut); pk.tearSide = -1;
    let pm = track(t, [[0, expr('tender', { gazeX: -0.5, gazeY: -0.2 })],
      [saved - 0.2, expr('determined', { gazeX: -0.6, smile: 0.25, browInner: 0.3, tears: 0.7 })],
      [ctx.line('s09g_1').end + 0.2, expr('cryingSmile', { gazeX: -0.6, tearDrop: 0, tears: 0.8, smile: 0.55, lipTremble: 0.2 })],
      [complete, expr('cryingSmile', { gazeX: -0.6, gazeY: 0.1, tearDrop: 0, tears: 0.9, smile: 0.75 })]], 0.6);
    pm = lipsync(alive(pm, t, 107), ctx.mouth('mira', t));
    withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: z, rot: hh.rot }, g2 => {
      placeFig(g2, 'keeper', POSES.sitGround, { s: 1.15, t, costume: 'dormant', light: 'day', lightX: 0.6, breathe: 0.5, sand: 0.5, vines: 0.4, panelGlint: 0.3 + 0.3 * Math.sin(t * 1.5) ** 2 },
        { ...pk, glow: 0.85, glowColor: irisCol(ctx, t), yaw: 0.1, pitch: -0.1 * seg(t, status, complete), rim: 0.5, sand: 0.2 }, 230, 380);
      const mp = blendPose(POSES.kneel, POSES.holdHands, take);
      placeFig(g2, 'mira', mp, { s: 1.15, t, costume: 'island', facing: -1, light: 'day', lightX: 0.6 },
        { ...pm, yaw: 0.05, rim: 0.4, pitch: 0.12 }, 540, 470);
      // clasped hands insert at centre: Keeper's hand resting, Mira's two hands closing around it
      const cx = 380, cy = 760;
      g2.save(); g2.globalAlpha = take;
      drawHand(g2, { x: cx - 120, y: cy - 20, s: 1.1, rot: -1.45, side: 'R', who: 'keeper', shape: 'relaxed', light: LIGHT.day, lightDir: [0.6, -0.8], costume: 'dormant' });
      drawHand(g2, { x: cx + 110 - take * 30, y: cy + 30, s: 0.9, rot: 1.6, side: 'L', who: 'mira', shape: 'hold', light: LIGHT.day, lightDir: [0.6, -0.8] });
      drawHand(g2, { x: cx + 100 - take * 30, y: cy - 50, s: 0.85, rot: 1.9 - Math.sin(t * 1.3) * 0.05, side: 'L', who: 'mira', shape: 'hold', light: LIGHT.day, lightDir: [0.6, -0.8] });
      g2.restore();
    });
    sunBloom(g, 0.35 + 0.2 * seg(t, complete, complete + 1)); vignette(g, 0.4);
  },

  // ------------------------------------------------ Grandpa cap at chest -> CU Keeper
  s09h(g, t, ctx) {
    const w = W_(ctx), cut = ctx.line('s09h_2').start - 0.35, hh = handheld(t, 1.4, 109);
    if (t < cut) {
      bgSoft(g, t, 's09h_bg1', { camX: 80, camY: -40, zoom: 1.3, blur: 9 });
      let pg = track(t, [[0, expr('moved', { gazeX: -0.4, gazeY: -0.3, tears: 0.4, lipTremble: 0 })],
        [w('s09h_1', 'how') - 0.2, expr('tender', { gazeX: -0.45, gazeY: -0.35, browInner: 0.7, smile: 0.2, tears: 0.5 })],
        [w('s09h_1', 'waiting'), expr('sad', { gazeX: -0.45, gazeY: -0.3, browInner: 0.9, smile: 0, tears: 0.6 })],
        [ctx.line('s09h_1').end, expr('moved', { gazeX: -0.45, gazeY: -0.35, tears: 0.6, mouthPress: 0.4 })]], 0.6);
      pg = lipsync(alive(pg, t, 110, { blinkRate: 0.7 }), ctx.mouth('grandpa', t));
      withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + t * 0.012 }, g2 => {
        placeFig(g2, 'grandpa', POSES.capChest, { s: 1.45, t, costume: 'island', facing: -1, light: 'day', lightX: 0.6, capInHand: true },
          { ...pg, cap: false, yaw: -0.1, pitch: -0.12 + Math.sin(t * 1.9) * 0.015, rim: 0.4 }, 380, 430);
      });
    } else {
      const tt = t - cut, ready = w('s09h_3', 'getting');
      bgSoft(g, t, 's09h_bg2', { camX: 50, zoom: 1.3, blur: 8 });
      let p = track(t, [[cut, expr('moved', { gazeX: 0.45, gazeY: 0.2, tears: 0.7 })],
        [w('s09h_2', 'i') + 0.1, expr('tender', { gazeX: 0.45, gazeY: 0.2, smile: 0.3, tears: 0.6 })],
        [w('s09h_2', 'waiting.'), expr('fond', { gazeX: 0.2, gazeY: 0.0, smile: 0.35, tears: 0.6 })],
        [ready - 0.1, expr('smile', { gazeX: -0.45, gazeY: -0.05, smile: 0.75, tears: 0.6, lowerLid: 0.45 })]], 0.5);
      p = lipsync(alive(p, t, 111, { blinkRate: 0.6, sac: 0.4 }), ctx.mouth('keeper', t));
      withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + tt * 0.012 }, g2 => {
        keeperCU(g2, t, ctx, p, 360, 470, 1.2, { glow: 0.85, yaw: lerp(0.15, -0.15, seg(t, ready - 0.4, ready + 0.3)), roll: -0.04 * seg(t, ready, ready + 0.6) });
      });
    }
    vignette(g, 0.4);
  },

  // ------------------------------------------------ naming exchange, alternating CUs
  s09i(g, t, ctx) {
    const w = W_(ctx);
    const c1 = ctx.line('s09i_2').start - 0.3, c2 = ctx.line('s09i_3').start - 0.35, c3 = ctx.line('s09i_4').start - 0.5;
    const miraShot = t < c1 || (t >= c2 && t < c3);
    if (miraShot) {
      const t0 = t < c1 ? 0 : c2, hh = handheld(t, 1.5, 113);
      bgSoft(g, t, 's09i_bgm', { camX: -80, zoom: 1.3, blur: 8 });
      const kp = w('s09i_3', 'keeper.'), kept = w('s09i_3', 'kept'), lightW = w('s09i_3', 'light');
      let p = track(t, [[0, expr('hopeful', { gazeX: 0.35, tears: 0.6, smile: 0.2, browRaise: 0.3 })],
        [w('s09i_1', 'name?'), expr('hopeful', { gazeX: 0.35, tears: 0.6, smile: 0.3, browRaise: 0.5, browInner: 0.5 })],
        [c2, expr('determined', { gazeX: 0.35, smile: 0.4, tears: 0.6, browInner: -0.1 })],
        [kp, expr('smile', { gazeX: 0.35, smile: 0.95, eyeOpen: 1.05, browRaise: 0.4, tears: 0.5 })],
        [kept, expr('laugh', { gazeX: 0.3, smile: 1, tears: 0.5, mouthOpen: 0.2 })],
        [lightW, expr('smile', { gazeX: 0.2, gazeY: 0.4, smile: 0.9, tears: 0.5 })]], 0.4);
      p = lipsync(alive(p, t, 114), ctx.mouth('mira', t));
      const tilt = t < c1 ? 0.08 * seg(t, 0.5, 1.2) : -0.06 * seg(t, kp - 0.3, kp + 0.3);
      const bounce = Math.sin(seg(t, kp - 0.1, kp + 0.4) * Math.PI) * 0.1;
      withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + (t - t0) * 0.012 }, g2 => {
        miraCU(g2, t, p, 370, 480, 1.25, { yaw: 0.2, roll: tilt, pitch: bounce + seg(t, lightW - 0.3, lightW + 0.2) * 0.15 });
      });
      sunBloom(g, 0.3);
    } else {
      const t0 = t < c2 ? c1 : c3, hh = handheld(t, 1.3, 115);
      bgSoft(g, t, 's09i_bgk', { camX: 50, zoom: 1.3, blur: 8 });
      let p;
      if (t < c2) {
        p = track(t, [[c1, expr('tender', { gazeX: -0.4, smile: 0.15, tears: 0.5 })],
          [w('s09i_2', 'never'), expr('neutral', { gazeX: -0.1, gazeY: -0.35, smile: 0.1, eyeOpen: 0.85, tears: 0.5, blush: 0.2 })],
          [w('s09i_2', 'there'), expr('sad', { gazeX: 0.3, gazeY: -0.3, smile: 0.05, tears: 0.6, eyeOpen: 0.8 })],
          [w('s09i_2', 'anything.'), expr('tender', { gazeX: -0.4, gazeY: -0.1, smile: 0.15, tears: 0.6, browInner: 0.6 })]], 0.6);
      } else {
        const kw = w('s09i_4', 'keeper.');
        p = track(t, [[c3, expr('surprised', { gazeX: -0.4, mouthOpen: 0, eyeOpen: 1.15, tears: 0.6, browRaise: 0.5 })],
          [kw - 0.15, expr('smile', { gazeX: -0.4, smile: 0.6, tears: 0.6, eyeOpen: 0.9 })],
          [kw + 0.35, expr('smile', { eyeOpen: 0, smile: 0.85, lowerLid: 0.6, tears: 0.7, browInner: 0.4, blush: 0.25 })],
          [ctx.line('s09i_4').end + 0.5, expr('smile', { gazeX: -0.4, smile: 0.85, eyeOpen: 0.75, lowerLid: 0.5, tears: 0.7, blush: 0.25 })]], 0.5);
      }
      p = lipsync(alive(p, t, 116, { blinkRate: 0.6, sac: 0.4 }), ctx.mouth('keeper', t));
      const shy = t < c2 ? env(t, w('s09i_2', 'never') - 0.2, w('s09i_2', 'there')) : 0;
      withCam(g, { x: W / 2 + hh.x, y: H / 2 + hh.y, zoom: 1 + (t - t0) * 0.012 }, g2 => {
        keeperCU(g2, t, ctx, p, 360, 470, 1.2, { glow: 0.85 + 0.1 * Math.sin(t * 2), yaw: -0.15 + shy * 0.2, pitch: -shy * 0.15, roll: t > c3 ? 0.05 : 0 });
      });
    }
    vignette(g, 0.4);
  },
};

function env(t, a, b, fin = 0.3, fout = 0.3) { return Math.min(seg(t, a, a + fin, ease.inOutSine), 1 - seg(t, b - fout, b, ease.inOutSine)); }
