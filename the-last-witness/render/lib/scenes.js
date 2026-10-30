// Locations: backgrounds, foregrounds, character layout, lighting and camera framings.
// World space is a 720x1280 stage (the wide shot at zoom 1). A camera {x, y, z} puts world
// point (x, y) at the frame centre with scale z.
'use strict';
const U = require('./util');
const FX = require('./fx');
const R = require('./rig');
const { rgba, mix, shade, lerp, clamp, smooth, TAU } = U;

const W = 720, H = 1280;

// ---------------------------------------------------------------- layouts
// x, y: sternal notch (world); s: head height; facing: +1 faces screen-right
const LAYOUT = {
  room: { human: { x: 232, y: 700, s: 112, facing: 1, yaw: 0.72 }, ai: { x: 492, y: 694, s: 106, facing: -1, yaw: -0.72 } },
  ship: { last_human: { x: 210, y: 760, s: 112, facing: 1, yaw: 0.66 }, ai: { x: 520, y: 744, s: 104, facing: -1, yaw: -0.68 } },
  void: { ai: { x: 360, y: 700, s: 110, facing: -1, yaw: -0.12 } },
  memory: { last_human: { x: 240, y: 760, s: 112, facing: 1, yaw: 0.45 } },
  nv: {
    suffering: { x: 250, y: 840, s: 86, facing: 1, yaw: 0.7 },
    ai: { x: 505, y: 706, s: 104, facing: -1, yaw: -0.7 },
    boredom: { x: 125, y: 690, s: 98, facing: 1, yaw: 0.5 },
    loneliness: { x: 615, y: 704, s: 96, facing: -1, yaw: -0.5 },
  },
};
const DESK_Y = 846;

// ---------------------------------------------------------------- cameras
function cuCam(c, s, z = 2.55, screenY = 515) {
  const hy = c.y - 0.6 * s;
  return { x: c.x + c.facing * 0.06 * s, y: hy - (screenY - 640) / z, z };
}
const SHOTS = {
  room_wide: { scene: 'room', cam: { x: 360, y: 580, z: 1.12 } },
  room_two: { scene: 'room', cam: { x: 362, y: 737, z: 1.45 } },
  room_cu_human: { scene: 'room', cam: cuCam(LAYOUT.room.human, 112), only: ['human'] },
  room_cu_ai: { scene: 'room', cam: cuCam(LAYOUT.room.ai, 106), only: ['ai'] },
  room_ots_human: { scene: 'room', cam: { x: 318, y: 690, z: 1.85 } },
  room_ots_ai: { scene: 'room', cam: { x: 406, y: 686, z: 1.85 } },
  room_vision: { scene: 'room', cam: { x: 362, y: 626, z: 1.36 }, vision: true, panel: 'short' },

  ship_wide: { scene: 'ship', cam: { x: 360, y: 640, z: 1.0 } },
  ship_two: { scene: 'ship', cam: { x: 365, y: 760, z: 1.4 } },
  ship_cu_human: { scene: 'ship', cam: cuCam(LAYOUT.ship.last_human, 112), only: ['last_human'] },
  ship_cu_ai: { scene: 'ship', cam: cuCam(LAYOUT.ship.ai, 104), only: ['ai'] },
  ship_window: { scene: 'ship', cam: { x: 360, y: 640, z: 1.0 }, special: 'window' },
  ship_vision: { scene: 'ship', cam: { x: 365, y: 572, z: 1.16 }, vision: true },
  ship_empty: { scene: 'ship', cam: { x: 365, y: 760, z: 1.4 }, empty: true },

  void_wide: { scene: 'void', cam: { x: 360, y: 610, z: 0.55 } },
  void_ai: { scene: 'void', cam: { x: 360, y: 676, z: 1.3 } },
  void_cu_ai: { scene: 'void', cam: cuCam(LAYOUT.void.ai, 110) },
  void_vision: { scene: 'void', cam: { x: 360, y: 492, z: 0.95 }, vision: true },

  memory_last_human: { scene: 'memory', cam: { x: 300, y: 640, z: 1.3 } },
  memory_cu: { scene: 'memory', cam: cuCam(LAYOUT.memory.last_human, 112, 2.6) },

  nv_wide: { scene: 'nv', cam: { x: 360, y: 700, z: 0.62 } },
  nv_two: { scene: 'nv', cam: { x: 378, y: 790, z: 1.45 }, only: ['suffering', 'ai'] },
  nv_cu_ai: { scene: 'nv', cam: cuCam(LAYOUT.nv.ai, 104), only: ['ai'] },
  nv_cu_suffering: { scene: 'nv', cam: cuCam(LAYOUT.nv.suffering, 86, 2.5), only: ['suffering'] },
  nv_trio: { scene: 'nv', cam: { x: 330, y: 690, z: 0.98 }, only: ['suffering', 'boredom', 'loneliness'] },
  nv_group: { scene: 'nv', cam: { x: 372, y: 700, z: 0.92 } },
  nv_cu_boredom: { scene: 'nv', cam: cuCam(LAYOUT.nv.boredom, 98 * 0.95), only: ['boredom'] },
  nv_cu_loneliness: { scene: 'nv', cam: cuCam(LAYOUT.nv.loneliness, 96 * 0.97), only: ['loneliness'] },
  nv_path: { scene: 'nv', cam: { x: 360, y: 640, z: 1.0 }, special: 'path' },

  vision_full: { scene: 'full', cam: { x: 360, y: 640, z: 1 }, full: true },
};

function applyCam(ctx, cam) {
  ctx.translate(W / 2, H / 2);
  ctx.scale(cam.z, cam.z);
  ctx.translate(-cam.x, -cam.y);
}
function toScreen(cam, x, y) { return [(x - cam.x) * cam.z + W / 2, (y - cam.y) * cam.z + H / 2]; }

// ---------------------------------------------------------------- lighting
function lightFor(scene, who, env) {
  const dawn = env.dawn || 0;
  if (scene === 'room') {
    if (who === 'ai') return { keyX: 0.4, rim: mix([170, 240, 255], [255, 210, 160], dawn * 0.6), rimX: -1, rimA: 0.55, amb: [30, 60, 90], ambA: 0.08 };
    return { keyX: -0.7, rim: mix([120, 210, 255], [255, 200, 150], dawn), rimX: 1, rimA: 0.42 + dawn * 0.2, amb: mix([30, 40, 80], [120, 80, 60], dawn), ambA: 0.1 };
  }
  if (scene === 'ship' || scene === 'memory') {
    if (who === 'ai') return { keyX: 0.3, rim: [180, 236, 255], rimX: -1, rimA: 0.55, amb: [20, 40, 80], ambA: 0.1 };
    return { keyX: -0.4, rim: [170, 190, 255], rimX: 1, rimA: 0.6, amb: [40, 50, 100], ambA: 0.16 };
  }
  if (scene === 'void') return { keyX: 0.2, rim: [190, 245, 255], rimX: 1, rimA: 0.5, amb: [10, 20, 50], ambA: 0.1 };
  if (scene === 'nv') {
    if (who === 'ai') return { keyX: 0.5, rim: [255, 214, 160], rimX: 1, rimA: 0.45, amb: [60, 40, 90], ambA: 0.08 };
    return { keyX: 0.6, rim: [255, 205, 150], rimX: 1, rimA: 0.6, amb: [150, 120, 190], ambA: who === 'suffering' ? 0.16 : 0.12 };
  }
  return { keyX: -0.5, rim: [200, 220, 255], rimX: 1, rimA: 0.4 };
}

// ---------------------------------------------------------------- room
function room(ctx, t, env) {
  const dawn = env.dawn || 0;
  // back wall
  const wall = ctx.createLinearGradient(0, 0, 0, 1000);
  wall.addColorStop(0, rgba(mix([22, 27, 46], [70, 58, 66], dawn)));
  wall.addColorStop(1, rgba(mix([14, 17, 32], [52, 42, 50], dawn)));
  ctx.fillStyle = wall; ctx.fillRect(-400, -200, 1520, 1700);
  // window
  const wx = 190, wy = 150, ww = 340, wh = 400;
  const sky = ctx.createLinearGradient(0, wy, 0, wy + wh);
  sky.addColorStop(0, rgba(mix([10, 16, 40], [70, 96, 160], dawn)));
  sky.addColorStop(0.65, rgba(mix([22, 30, 66], [236, 160, 140], dawn)));
  sky.addColorStop(1, rgba(mix([40, 36, 70], [255, 206, 150], dawn)));
  ctx.fillStyle = sky; ctx.fillRect(wx, wy, ww, wh);
  ctx.save(); ctx.beginPath(); ctx.rect(wx, wy, ww, wh); ctx.clip();
  ctx.save(); ctx.translate(wx, wy); FX.stars(ctx, ww, wh * 0.62, t, 41, 34, { fade: () => 1 - dawn }); ctx.restore();
  if (dawn > 0) FX.glow(ctx, wx + ww * 0.62, wy + wh * 0.98, 240, [255, 200, 130], 0.55 * dawn, false);
  // distant city: low rooftops with a few warm windows (static)
  const rnd = U.rng(5);
  ctx.fillStyle = rgba(mix([12, 14, 28], [70, 54, 64], dawn));
  for (let i = 0, x = wx - 10; x < wx + ww + 10; i++) {
    const bw = 28 + rnd() * 46, bh = 40 + rnd() * 90;
    ctx.fillRect(x, wy + wh - bh, bw - 4, bh);
    x += bw;
  }
  const rnd2 = U.rng(9);
  for (let i = 0; i < 26; i++) {
    const x = wx + rnd2() * ww, y = wy + wh - 10 - rnd2() * 80;
    ctx.fillStyle = rgba([255, 200, 120], (0.35 + rnd2() * 0.4) * (1 - dawn * 0.7));
    ctx.fillRect(x, y, 3, 4);
  }
  ctx.restore();
  // window frame & mullions
  ctx.strokeStyle = rgba(mix([44, 50, 72], [110, 92, 90], dawn)); ctx.lineWidth = 14;
  ctx.strokeRect(wx, wy, ww, wh);
  ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(wx + ww / 2, wy); ctx.lineTo(wx + ww / 2, wy + wh); ctx.moveTo(wx, wy + wh * 0.45); ctx.lineTo(wx + ww, wy + wh * 0.45); ctx.stroke();
  // sill
  ctx.fillStyle = rgba(mix([38, 42, 62], [120, 100, 96], dawn)); ctx.fillRect(wx - 22, wy + wh + 4, ww + 44, 14);
  // light spilling from the window onto the wall at dawn
  if (dawn > 0) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createLinearGradient(0, wy, 0, wy + wh + 300);
    g.addColorStop(0, rgba([255, 190, 140], 0.0)); g.addColorStop(1, rgba([255, 190, 140], 0.12 * dawn));
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(wx, wy + wh); ctx.lineTo(wx + ww, wy + wh); ctx.lineTo(wx + ww + 120, DESK_Y); ctx.lineTo(wx - 120, DESK_Y); ctx.fill();
    ctx.restore();
  }
  // bookshelf on the left wall
  ctx.fillStyle = rgba(mix([26, 22, 30], [80, 60, 54], dawn)); ctx.fillRect(-60, 230, 150, 620);
  const bc = [[120, 60, 50], [60, 80, 110], [140, 110, 60], [70, 100, 80], [110, 70, 100]];
  for (let row = 0; row < 4; row++) {
    const y0 = 260 + row * 150;
    ctx.fillStyle = rgba(mix([40, 34, 40], [100, 80, 70], dawn)); ctx.fillRect(-60, y0 + 118, 150, 10);
    let x = -50;
    const r3 = U.rng(row * 7 + 2);
    while (x < 80) {
      const w = 10 + r3() * 12, h = 70 + r3() * 40;
      ctx.fillStyle = rgba(shade(mix(bc[Math.floor(r3() * 5)], [30, 30, 40], 0.45 - dawn * 0.2), -0.1));
      ctx.fillRect(x, y0 + 118 - h, w - 2, h);
      x += w;
    }
  }
  // plant on the right
  ctx.fillStyle = rgba(mix([40, 36, 44], [90, 76, 70], dawn)); ctx.fillRect(640, 700, 60, 150);
  ctx.strokeStyle = rgba(mix([30, 60, 50], [70, 110, 80], dawn)); ctx.lineWidth = 10; ctx.lineCap = 'round';
  for (let i = 0; i < 7; i++) {
    const a = -1.2 + i * 0.38 + Math.sin(t * 0.4 + i) * 0.02;
    ctx.beginPath(); ctx.moveTo(670, 705); ctx.quadraticCurveTo(670 + Math.cos(a) * 40, 640 + Math.sin(a) * 30, 670 + Math.cos(a) * 85, 600 + Math.sin(a) * 80); ctx.stroke();
  }
  // lamp glow (warm key on the left)
  FX.glow(ctx, 60, 790, 380, [255, 190, 110], 0.22 * (1 - dawn * 0.5), true);
  // the AI's own cyan light on the wall behind it
  FX.glow(ctx, 540, 620, 320, [110, 220, 255], 0.13, true);
}

function roomDesk(ctx, t, env) {
  const dawn = env.dawn || 0;
  const D1 = DESK_Y + 250; // the desk top is seen from slightly above: a deep surface
  const top = ctx.createLinearGradient(0, DESK_Y, 0, D1);
  top.addColorStop(0, rgba(mix([84, 56, 40], [150, 104, 72], dawn)));
  top.addColorStop(1, rgba(mix([60, 38, 27], [118, 80, 54], dawn)));
  ctx.fillStyle = top;
  ctx.beginPath(); ctx.moveTo(-300, DESK_Y); ctx.lineTo(1020, DESK_Y); ctx.lineTo(1200, D1); ctx.lineTo(-480, D1); ctx.fill();
  // far edge highlight & faint wood grain in perspective
  ctx.fillStyle = rgba([255, 210, 160], 0.1); ctx.fillRect(-300, DESK_Y, 1320, 2);
  ctx.strokeStyle = rgba([30, 18, 12], 0.16); ctx.lineWidth = 2;
  for (let i = 1; i < 9; i++) { const y = DESK_Y + Math.pow(i / 9, 1.4) * 250; ctx.beginPath(); ctx.moveTo(-480, y); ctx.lineTo(1200, y + 3); ctx.stroke(); }
  // front edge
  ctx.fillStyle = rgba(mix([44, 28, 20], [96, 64, 44], dawn)); ctx.fillRect(-480, D1, 1700, 600);
  ctx.fillStyle = rgba([255, 210, 160], 0.1); ctx.fillRect(-480, D1, 1700, 3);
  // lamp (left end of desk)
  ctx.fillStyle = rgba([40, 36, 40]);
  ctx.fillRect(40, DESK_Y - 8, 50, 10);
  ctx.strokeStyle = rgba([48, 44, 50]); ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(65, DESK_Y - 6); ctx.lineTo(48, DESK_Y - 120); ctx.lineTo(96, DESK_Y - 190); ctx.stroke();
  ctx.fillStyle = rgba([60, 54, 58]);
  ctx.beginPath(); ctx.moveTo(70, DESK_Y - 210); ctx.lineTo(130, DESK_Y - 190); ctx.lineTo(116, DESK_Y - 160); ctx.closePath(); ctx.fill();
  FX.glow(ctx, 112, DESK_Y - 170, 70, [255, 214, 150], 0.7);
  // pool of warm lamplight on the desk
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const pool = ctx.createRadialGradient(170, DESK_Y + 90, 0, 170, DESK_Y + 90, 300);
  pool.addColorStop(0, rgba([255, 190, 120], 0.22 * (1 - dawn * 0.4))); pool.addColorStop(1, rgba([255, 190, 120], 0));
  ctx.fillStyle = pool; ctx.fillRect(-200, DESK_Y, 760, 260);
  ctx.restore();
  // notebook and pen by the human
  ctx.save(); ctx.translate(120, DESK_Y + 150); ctx.rotate(-0.12);
  ctx.fillStyle = rgba(mix([214, 206, 188], [240, 230, 210], dawn)); ctx.fillRect(-70, -40, 140, 86);
  ctx.strokeStyle = rgba([120, 110, 100], 0.4); ctx.lineWidth = 1.5;
  for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.moveTo(-58, -26 + i * 13); ctx.lineTo(58, -26 + i * 13); ctx.stroke(); }
  ctx.strokeStyle = rgba([70, 60, 120]); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(-50, -14); ctx.bezierCurveTo(-30, -20, -10, -8, 10, -14); ctx.stroke();
  ctx.fillStyle = rgba([40, 40, 50]); ctx.fillRect(80, -30, 8, 70);
  ctx.restore();
  // laptop in the middle, screen toward the human, the hologram's emitter glow
  ctx.save(); ctx.translate(372, DESK_Y + 120);
  ctx.fillStyle = rgba([36, 40, 50]);
  ctx.beginPath(); ctx.moveTo(-70, 0); ctx.lineTo(70, 0); ctx.lineTo(86, 34); ctx.lineTo(-86, 34); ctx.fill();
  ctx.fillStyle = rgba([24, 28, 38]);
  ctx.beginPath(); ctx.moveTo(-70, 0); ctx.lineTo(70, 0); ctx.lineTo(60, -92); ctx.lineTo(-60, -92); ctx.fill();
  const sg = ctx.createLinearGradient(-60, -92, 70, 0);
  sg.addColorStop(0, rgba([90, 190, 230], 0.5)); sg.addColorStop(1, rgba([30, 70, 110], 0.4));
  ctx.fillStyle = sg; ctx.beginPath(); ctx.moveTo(-63, -4); ctx.lineTo(63, -4); ctx.lineTo(55, -86); ctx.lineTo(-55, -86); ctx.fill();
  ctx.restore();
  FX.glow(ctx, 372, DESK_Y + 80, 150, [120, 225, 255], 0.22);
  // mug by the AI
  ctx.fillStyle = rgba(mix([150, 60, 50], [190, 90, 70], dawn)); ctx.fillRect(600, DESK_Y + 100, 40, 50);
  ctx.fillStyle = rgba(mix([110, 44, 38], [150, 70, 54], dawn)); ctx.beginPath(); ctx.ellipse(620, DESK_Y + 100, 20, 6, 0, 0, TAU); ctx.fill();
  ctx.strokeStyle = rgba(mix([150, 60, 50], [190, 90, 70], dawn)); ctx.lineWidth = 7; ctx.beginPath(); ctx.arc(646, DESK_Y + 124, 12, -1.2, 1.2); ctx.stroke();
}

// ---------------------------------------------------------------- ship
function shipSky(ctx, x0, y0, w, h, t, env) {
  const decay = env.decay ?? 0.5; // 0 = some stars, 1 = nearly none
  const g = ctx.createLinearGradient(0, y0, 0, y0 + h);
  g.addColorStop(0, rgba([4, 6, 16])); g.addColorStop(1, rgba([14, 10, 26]));
  ctx.fillStyle = g; ctx.fillRect(x0, y0, w, h);
  // a dying red-violet nebula
  FX.glow(ctx, x0 + w * 0.7, y0 + h * 0.35, w * 0.45, [120, 50, 90], 0.22 * (1 - decay * 0.5), false);
  FX.glow(ctx, x0 + w * 0.25, y0 + h * 0.6, w * 0.35, [50, 60, 120], 0.18, false);
  ctx.save(); ctx.translate(x0, y0);
  FX.stars(ctx, w, h, t, 77, 90, {
    fade: (i) => clamp(1 - smooth((decay * 1.15 - U.hash(i * 31)) / 0.06)),
    color: (i) => mix([255, 190, 150], [190, 200, 255], U.hash(i * 7)),
  });
  // a dim red giant
  FX.glow(ctx, w * 0.78, h * 0.22, 60, [255, 120, 80], 0.5 * (1 - decay * 0.6), true);
  ctx.fillStyle = rgba([255, 150, 110], 0.8 * (1 - decay * 0.6)); ctx.beginPath(); ctx.arc(w * 0.78, h * 0.22, 9, 0, TAU); ctx.fill();
  ctx.restore();
}
function ship(ctx, t, env) {
  // hull interior
  ctx.fillStyle = rgba([10, 12, 22]); ctx.fillRect(-400, -300, 1520, 1900);
  // great curved window
  ctx.save();
  ctx.beginPath(); ctx.moveTo(-80, 90); ctx.quadraticCurveTo(360, 20, 800, 90); ctx.lineTo(800, 800); ctx.quadraticCurveTo(360, 840, -80, 800); ctx.closePath();
  ctx.clip();
  shipSky(ctx, -80, 20, 880, 830, t, env);
  ctx.restore();
  // window ribs
  ctx.strokeStyle = rgba([28, 32, 48]); ctx.lineWidth = 16;
  ctx.beginPath(); ctx.moveTo(-80, 90); ctx.quadraticCurveTo(360, 20, 800, 90); ctx.stroke();
  ctx.lineWidth = 10;
  for (const x of [120, 600]) { ctx.beginPath(); ctx.moveTo(x, 60); ctx.lineTo(x + (x < 360 ? -20 : 20), 820); ctx.stroke(); }
  ctx.fillStyle = rgba([16, 18, 30]); ctx.fillRect(-400, 800, 1520, 900);
  ctx.strokeStyle = rgba([150, 170, 255], 0.12); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(-80, 801); ctx.quadraticCurveTo(360, 841, 800, 801); ctx.stroke();
}
function shipChair(ctx, t, env) {
  // high-backed worn chair behind the last human
  const c = LAYOUT.ship.last_human;
  ctx.fillStyle = rgba([40, 34, 36]);
  ctx.beginPath();
  ctx.moveTo(c.x - 120, c.y + 260); ctx.lineTo(c.x - 128, c.y - 150); ctx.quadraticCurveTo(c.x - 20, c.y - 210, c.x + 80, c.y - 160);
  ctx.lineTo(c.x + 100, c.y + 260); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = rgba([170, 190, 255], 0.18); ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(c.x - 128, c.y - 150); ctx.quadraticCurveTo(c.x - 20, c.y - 210, c.x + 80, c.y - 160); ctx.stroke();
}
function shipConsole(ctx, t, env) {
  // dim console across the foreground with a few amber indicator lights
  const y = 930;
  const g = ctx.createLinearGradient(0, y, 0, y + 200);
  g.addColorStop(0, rgba([36, 40, 56])); g.addColorStop(1, rgba([16, 18, 28]));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(-300, y + 20); ctx.quadraticCurveTo(360, y - 30, 1020, y + 20); ctx.lineTo(1020, 1700); ctx.lineTo(-300, 1700); ctx.fill();
  ctx.strokeStyle = rgba([180, 200, 255], 0.15); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(-300, y + 20); ctx.quadraticCurveTo(360, y - 30, 1020, y + 20); ctx.stroke();
  const lights = [[170, y + 30], [210, y + 26], [460, y + 22], [500, y + 26]];
  lights.forEach(([x, yy], i) => {
    const on = (env.energy ?? 0.5) > i * 0.2;
    const a = on ? 0.5 + 0.3 * Math.sin(t * 0.8 + i) : 0.08;
    ctx.fillStyle = rgba([255, 170, 80], a); ctx.fillRect(x, yy, 8, 4);
    if (on) FX.glow(ctx, x + 4, yy + 2, 26, [255, 160, 70], a * 0.4);
  });
  // emitter under the AI
  FX.glow(ctx, LAYOUT.ship.ai.x, y + 6, 120, [120, 230, 255], 0.3);
}

// ---------------------------------------------------------------- void
function voidBg(ctx, t, env) {
  const g = ctx.createRadialGradient(360, 640, 40, 360, 640, 1400);
  g.addColorStop(0, rgba([14, 18, 40])); g.addColorStop(0.5, rgba([6, 8, 20])); g.addColorStop(1, rgba([2, 3, 8]));
  ctx.fillStyle = g; ctx.fillRect(-1600, -1600, 3920, 4480);
  // far faint memory lights, very slow
  ctx.save(); ctx.translate(-640, -400);
  FX.stars(ctx, 2000, 2080, t * 0.5, 12, 70, { fade: () => 0.35 * (env.starsA ?? 1), color: () => [170, 200, 255] });
  ctx.restore();
  // faint floor ring under the AI
  const c = LAYOUT.void.ai;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.strokeStyle = rgba([120, 220, 255], 0.16); ctx.lineWidth = 3;
  ctx.beginPath(); ctx.ellipse(c.x, c.y + 260, 170 + Math.sin(t * 0.6) * 4, 26, 0, 0, TAU); ctx.stroke();
  ctx.restore();
  FX.glow(ctx, c.x, c.y + 120, 260, [90, 200, 255], 0.12);
}
// hologram lower body dissolving into light (paints background-coloured fade over the lower torso)
function holoFade(ctx, c, s, bgTop, bgBot, t, from = 1.25, to = 2.3) {
  const y0 = c.y + from * s, y1 = c.y + to * s;
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  g.addColorStop(0, rgba(bgTop, 0)); g.addColorStop(1, rgba(bgBot, 1));
  ctx.fillStyle = g; ctx.fillRect(c.x - 2.2 * s, y0, 4.4 * s, (to - from + 3) * s);
  ctx.fillStyle = rgba(bgBot, 1); ctx.fillRect(c.x - 2.2 * s, y1, 4.4 * s, 4 * s);
  // rising motes from the dissolve line
  for (let i = 0; i < 14; i++) {
    const u = ((t * 0.12 + U.hash(i * 3)) % 1);
    const x = c.x + (U.hash(i * 11) - 0.5) * 1.6 * s;
    const y = lerp(y1, y0 - 0.2 * s, u);
    FX.glow(ctx, x, y, 0.06 * s, [150, 235, 255], 0.5 * Math.sin(u * Math.PI));
  }
}

// ---------------------------------------------------------------- new universe
function nvBg(ctx, t, env) {
  const g = ctx.createLinearGradient(0, -300, 0, 1500);
  g.addColorStop(0, rgba([20, 10, 40])); g.addColorStop(0.45, rgba([46, 26, 76])); g.addColorStop(0.7, rgba([90, 60, 110])); g.addColorStop(1, rgba([30, 20, 50]));
  ctx.fillStyle = g; ctx.fillRect(-1600, -1600, 3920, 4480);
  // nebula clouds (large, soft, slow)
  const clouds = [[120, 250, 420, [120, 70, 170]], [600, 180, 380, [60, 140, 170]], [380, 520, 500, [190, 110, 140]], [-200, 600, 400, [80, 60, 160]], [900, 520, 420, [70, 120, 160]]];
  for (const [x, y, r, c] of clouds) FX.glow(ctx, x + Math.sin(t * 0.05 + x) * 10, y, r, c, 0.28, false);
  // the newborn star (key light)
  FX.glow(ctx, 590, 250, 300, [255, 200, 140], 0.35, true);
  FX.light(ctx, 590, 250, 7, [255, 220, 170], 0.95);
  ctx.save(); ctx.translate(-400, -300);
  FX.stars(ctx, 1520, 1300, t, 23, 110, { color: (i) => mix([255, 220, 190], [190, 210, 255], U.hash(i * 5)) });
  ctx.restore();
  // luminous ground plane
  const gy = 900;
  const gp = ctx.createLinearGradient(0, gy - 20, 0, gy + 500);
  gp.addColorStop(0, rgba([150, 110, 170], 0.0)); gp.addColorStop(0.05, rgba([120, 90, 150], 0.9)); gp.addColorStop(1, rgba([40, 26, 60], 1));
  ctx.fillStyle = gp; ctx.fillRect(-1600, gy - 20, 3920, 2200);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const hz = ctx.createLinearGradient(0, gy - 30, 0, gy + 40);
  hz.addColorStop(0, rgba([255, 200, 160], 0)); hz.addColorStop(0.5, rgba([255, 200, 160], 0.2)); hz.addColorStop(1, rgba([255, 200, 160], 0));
  ctx.fillStyle = hz; ctx.fillRect(-1600, gy - 30, 3920, 70);
  ctx.restore();
  // a path of light toward the horizon
  const pathA = env.pathA ?? 0.6;
  if (pathA > 0) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const pg = ctx.createLinearGradient(0, gy, 0, 1700);
    pg.addColorStop(0, rgba([255, 210, 150], 0.05 * pathA)); pg.addColorStop(1, rgba([255, 210, 150], 0.28 * pathA));
    ctx.fillStyle = pg;
    ctx.beginPath(); ctx.moveTo(352, gy); ctx.lineTo(368, gy); ctx.lineTo(620, 1700); ctx.lineTo(100, 1700); ctx.fill();
    ctx.restore();
  }
}

// ---------------------------------------------------------------- foreground silhouettes (over-the-shoulder)
function otsSilhouette(ctx, who, side, t) {
  // soft out-of-focus head and shoulder at the frame edge (screen space)
  const x = side > 0 ? W + 40 : -40, y = 780;
  const col = who === 'ai' ? [40, 120, 160] : [36, 26, 26];
  const rim = who === 'ai' ? [150, 240, 255] : [255, 190, 130];
  ctx.save();
  const g = ctx.createRadialGradient(x, y, 40, x, y, 360);
  g.addColorStop(0, rgba(col, 0.95)); g.addColorStop(0.7, rgba(col, 0.85)); g.addColorStop(1, rgba(col, 0));
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.ellipse(x - side * 30, y - 120, 150, 185, 0, 0, TAU); ctx.fill();
  ctx.beginPath(); ctx.ellipse(x - side * 10, y + 340, 300, 260, 0, 0, TAU); ctx.fill();
  ctx.globalCompositeOperation = 'lighter';
  ctx.strokeStyle = rgba(rim, 0.25); ctx.lineWidth = 18;
  ctx.beginPath(); ctx.ellipse(x - side * 30, y - 120, 150, 185, 0, side > 0 ? 2.4 : -0.7, side > 0 ? 3.9 : 0.75); ctx.stroke();
  ctx.restore();
}

// back view of the last human in the chair, silhouetted against the window (screen space, ship_window)
function lastHumanBack(ctx, x, y, s, t, alive = 1) {
  const breath = Math.sin(t * 1.1) * 0.008 * s * alive;
  const shapes = () => {
    // chair back
    ctx.beginPath();
    ctx.moveTo(x - 1.2 * s, y + 3 * s); ctx.lineTo(x - 1.22 * s, y - 0.05 * s);
    ctx.bezierCurveTo(x - 1.2 * s, y - 0.75 * s, x + 1.2 * s, y - 0.75 * s, x + 1.22 * s, y - 0.05 * s);
    ctx.lineTo(x + 1.2 * s, y + 3 * s); ctx.closePath();
  };
  ctx.save();
  shapes(); ctx.fillStyle = rgba([20, 18, 26]); ctx.fill();
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const cr = ctx.createLinearGradient(0, y - 0.6 * s, 0, y + 0.3 * s);
  cr.addColorStop(0, rgba([170, 190, 255], 0.22)); cr.addColorStop(1, rgba([170, 190, 255], 0));
  ctx.strokeStyle = cr; ctx.lineWidth = 0.03 * s;
  ctx.beginPath(); ctx.moveTo(x - 1.22 * s, y + 0.2 * s); ctx.bezierCurveTo(x - 1.2 * s, y - 0.75 * s, x + 1.2 * s, y - 0.75 * s, x + 1.22 * s, y + 0.2 * s); ctx.stroke();
  ctx.restore();
  if (alive > 0) {
    // shoulders wrapped in the blanket, neck, head with grey hair seen from behind
    ctx.beginPath();
    ctx.moveTo(x - 1.08 * s, y + 3 * s); ctx.lineTo(x - 1.1 * s, y + 0.62 * s);
    ctx.quadraticCurveTo(x - 1.06 * s, y + 0.22 * s + breath, x - 0.72 * s, y + 0.14 * s + breath);
    ctx.quadraticCurveTo(x - 0.35 * s, y + 0.06 * s + breath, x - 0.18 * s, y - 0.02 * s + breath);
    ctx.lineTo(x + 0.18 * s, y - 0.02 * s + breath);
    ctx.quadraticCurveTo(x + 0.35 * s, y + 0.06 * s + breath, x + 0.72 * s, y + 0.14 * s + breath);
    ctx.quadraticCurveTo(x + 1.06 * s, y + 0.22 * s + breath, x + 1.1 * s, y + 0.62 * s);
    ctx.lineTo(x + 1.08 * s, y + 3 * s); ctx.closePath();
    ctx.fillStyle = rgba([44, 48, 62]); ctx.fill();
    ctx.fillStyle = rgba([52, 44, 46]);
    ctx.beginPath(); ctx.moveTo(x - 0.14 * s, y + 0.06 * s + breath); ctx.lineTo(x - 0.12 * s, y - 0.22 * s + breath); ctx.lineTo(x + 0.12 * s, y - 0.22 * s + breath); ctx.lineTo(x + 0.14 * s, y + 0.06 * s + breath); ctx.fill();
    ctx.fillStyle = rgba([96, 70, 64]);
    for (const sg of [-1, 1]) { ctx.beginPath(); ctx.ellipse(x + sg * 0.355 * s, y - 0.53 * s + breath, 0.045 * s, 0.085 * s, sg * 0.15, 0, TAU); ctx.fill(); }
    const hg = ctx.createRadialGradient(x - 0.08 * s, y - 0.82 * s, 0.05 * s, x, y - 0.62 * s, 0.5 * s);
    hg.addColorStop(0, rgba([150, 150, 160])); hg.addColorStop(1, rgba([70, 70, 80]));
    ctx.fillStyle = hg; ctx.beginPath(); ctx.ellipse(x, y - 0.6 * s + breath, 0.36 * s, 0.44 * s, 0, 0, TAU); ctx.fill();
    // a few hair strands
    ctx.strokeStyle = rgba([190, 190, 200], 0.25); ctx.lineWidth = 0.012 * s; ctx.lineCap = 'round';
    for (let i = -3; i <= 3; i++) { ctx.beginPath(); ctx.moveTo(x + i * 0.04 * s, y - 1.0 * s + breath); ctx.quadraticCurveTo(x + i * 0.09 * s, y - 0.66 * s + breath, x + i * 0.1 * s, y - 0.24 * s + breath); ctx.stroke(); }
  }
  // cold starlight rim along the top edges only
  ctx.globalCompositeOperation = 'lighter';
  const rg = ctx.createLinearGradient(0, y - 1.1 * s, 0, y - 0.1 * s);
  rg.addColorStop(0, rgba([170, 190, 255], 0.35)); rg.addColorStop(1, rgba([170, 190, 255], 0));
  ctx.strokeStyle = rg; ctx.lineWidth = 0.035 * s;
  if (alive > 0) { ctx.beginPath(); ctx.ellipse(x, y - 0.6 * s + breath, 0.36 * s, 0.44 * s, 0, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke(); }
  if (alive > 0) { ctx.lineWidth = 0.025 * s; ctx.beginPath(); ctx.moveTo(x - 1.1 * s, y + 0.62 * s); ctx.quadraticCurveTo(x - 1.06 * s, y + 0.22 * s + breath, x - 0.72 * s, y + 0.14 * s + breath); ctx.stroke(); }
  ctx.restore();
}

module.exports = {
  W, H, LAYOUT, SHOTS, DESK_Y, applyCam, toScreen, lightFor,
  room, roomDesk, ship, shipSky, shipChair, shipConsole, voidBg, holoFade, nvBg, otsSilhouette, lastHumanBack,
};
