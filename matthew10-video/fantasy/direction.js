'use strict';
// Direction for the fantasy version: which still is on screen when (cut on the
// words the narrator says), how the camera moves, which effects play, and how
// each animated face acts. Everything is keyed to the recorded line and word
// timings, so re-recording a line keeps the cuts on their words.

const fs = require('fs');
const path = require('path');
const lib = (p) => require(path.join(__dirname, '..', 'render', 'lib', p));
const S = lib('stage');
const { Actor } = lib('anim');
const { BASE } = lib('cast');
const { wordTimes } = lib('text');
const { clamp, smooth, lerp } = lib('util');
const V = require('./vfx');

const W = S.W, H = S.H;
const norm = (s) => s.toLowerCase().replace(/[^a-z']/g, '');

function loadDirection(BUILD, REAL) {
  const timeline = JSON.parse(fs.readFileSync(path.join(BUILD, 'timeline.json'), 'utf8'));
  const lips = JSON.parse(fs.readFileSync(path.join(BUILD, 'lipsync.json'), 'utf8'));
  const byId = Object.fromEntries(timeline.lines.map((l) => [l.id, l]));
  const scene = Object.fromEntries(timeline.scenes.map((s) => [s.id, s]));
  const L = (id) => { if (!byId[id]) throw new Error('no line ' + id); return byId[id]; };
  const wtc = {};
  const words = (id) => (wtc[id] ||= wordTimes(L(id)));
  // time of a word in a line: by index, or the first word starting with the given text
  const wi = (id, w) => {
    const ws = words(id);
    if (typeof w === 'number') return ws[Math.max(0, Math.min(ws.length - 1, w))];
    const k = ws.findIndex((x) => norm(x.w).startsWith(norm(w)));
    if (k < 0) throw new Error(`no word "${w}" in ${id}`);
    return ws[k];
  };
  const at = (id, w, d = 0) => wi(id, w).s + d;
  const end = (id, d = 0) => L(id).end + d;
  const start = (id, d = 0) => L(id).start + d;

  // ------------------------------------------------------------ faces in the stills
  const meta = {};
  const faceInfo = (img) => {
    if (!(img in meta)) {
      const p = path.join(REAL, 'base', img + '.json');
      meta[img] = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null;
    }
    return meta[img];
  };
  // a face box in frame coordinates (photos are cover-fitted to the frame)
  const face = (img, i = 0) => {
    const m = faceInfo(img);
    if (!m || !m.faces || !m.faces[i]) return null;
    const s = Math.max(W / m.w, H / m.h), ox = (W - m.w * s) / 2, oy = (H - m.h * s) / 2;
    const [x0, y0, x1, y1] = m.faces[i].bbox.map((v, k) => (k % 2 ? oy + v * s : ox + v * s));
    return { x0, y0, x1, y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, w: x1 - x0, h: y1 - y0 };
  };

  // ------------------------------------------------------------ performances
  const actors = {};
  function actor(key, who, opts = {}) {
    const a = new Actor(key, BASE[who] || {}, { seed: opts.seed });
    if (!opts.mute) for (const l of timeline.lines) if (l.who === who && lips[l.id]) a.say(l.start, lips[l.id], l.end - l.start);
    actors[key] = a;
    return a;
  }
  // the Light's voice level drives the orb
  const light = actor('light', 'ai');

  const g0 = actor('glass:maya', 'maya');
  g0.expr(0, 'polite', 0.01).expr(at('N4', 'smiled') - 0.2, 'brittle', 0.8)
    .expr(end('N4', 0.2), 'fading', 1.0).expr(end('N4', 1.2), 'tired', 1.0)
    .look(end('N4', 0.6), { gazeY: 0.25, pitch: 0.08 }, 0.9);

  const fm = actor('feast:mom', 'mom');
  fm.expr(0, 'bright', 0.01).expr(end('L1', 0.3), 'polite', 0.8).expr(start('L3', -0.3), 'placating', 0.5)
    .expr(end('L4', 0.2), 'awkward', 0.6).look(end('L4', 0.4), { yaw: -0.15, gazeX: -0.3 }, 0.6);
  const fd = actor('feast:dad', 'dad');
  fd.expr(0, 'closed', 0.01).expr(start('L4', -0.2), 'irritated', 0.4).expr(end('L4', 0.3), 'closed', 0.8)
    .look(end('L4', 0.5), { yaw: 0.18, gazeX: 0.35, pitch: 0.06 }, 0.7);
  const fj = actor('feast:jordan', 'jordan');
  fj.expr(0, 'awkward', 0.01).look(start('L4', 0.5), { pitch: 0.12, gazeY: 0.35 }, 0.8);
  const fy = actor('feast:maya', 'maya');
  fy.expr(0, 'anxious', 0.01).look(0, { gazeY: 0.35, pitch: 0.12 }, 0.01)
    .look(start('L2', -0.5), { gazeY: 0, pitch: 0 }, 0.6).expr(start('L2', -0.4), 'earnest', 0.6)
    .expr(at('L2', 'pretending') - 0.3, 'cracking', 0.8).expr(end('L2', 0.6), 'vulnerable', 1.0)
    .set('wet', at('L2', 'autistic'), 0.45, 1.2);

  const mr = actor('mirrors:refl', 'maya', { mute: true, seed: 77 });
  mr.expr(0, 'bright', 0.01);
  mr.idleAmp = 0.5;
  const mm = actor('mirrors:maya', 'maya');
  mm.expr(0, 'hollow', 0.01).expr(start('L5', -0.6), 'unsettled', 0.6).expr(end('L5', 0.3), 'vulnerable', 0.8)
    .expr(at('N12', 'small') - 0.2, 'surprised', 0.5).expr(at('N12', 'made'), 'attentive', 0.8)
    .expr(start('L6', 1.5), 'vulnerable', 1.0).expr(at('L6', 'same') - 0.3, 'moved', 1.0)
    .expr(start('L7', -0.3), 'cracking', 0.6).expr(start('L8', 0.3), 'tender', 1.0)
    .look(start('L6', -0.2), { gazeX: 0.25, yaw: 0.08 }, 0.6);

  const cm = actor('cross:maya', 'maya');
  cm.expr(0, 'crying', 0.01).expr(at('N14', 'performance'), 'cracking', 0.8).expr(at('N14', 'find') - 0.2, 'relief', 1.2);

  const gm = actor('guild:maya', 'maya');
  gm.expr(0, 'overwhelmed', 0.01).expr(start('L9', -0.3), 'earnest', 0.5).expr(start('L10', 0.6), 'stung', 0.6)
    .expr(at('L10', 'push') - 0.2, 'hurt', 0.8)
    // the storm: eyes squeezed shut
    .expr(start('N16', -0.2), 'overwhelmed', 0.4).set('lid', start('N16', 0.2), 0.9, 0.5).set('squint', start('N16', 0.2), 0.35, 0.5);
  const gg = actor('guild:greg', 'greg');
  gg.expr(0, 'polite', 0.01).expr(start('L10', -0.2), 'dismissive', 0.5);

  const sm = actor('sparrows:maya', 'maya');
  sm.expr(0, 'surprised', 0.01).expr(at('N19', 'hairs'), 'moved', 1.2).expr(end('N19', 0.4), 'tender', 1.0)
    .look(0, { gazeY: -0.4, pitch: -0.1 }, 0.01);

  const pm = actor('pool:mom', 'mom');
  pm.expr(0, 'tight', 0.01).expr(start('L14', -0.4), 'guilty', 0.7);
  const py = actor('pool:maya', 'maya');
  py.expr(0, 'earnest', 0.01).expr(at('L12', 'but') - 0.1, 'resolved', 0.6).expr(start('L13', -0.3), 'hurt', 0.6)
    .expr(at('L13', 'space') - 0.4, 'resolved', 0.8).expr(start('L15', -0.3), 'tender', 0.8)
    .set('wet', start('L13'), 0.5, 1.0).look(0, { gazeY: 0.3, pitch: 0.12 }, 0.01);

  const rm = actor('flight:maya', 'maya');
  rm.expr(0, 'weary', 0.01).expr(at('L16', 'stopped') - 0.3, 'moved', 1.0).expr(start('N24', 0.2), 'relief', 1.2);

  const hp = actor('haven:priya', 'priya');
  hp.expr(0, 'warm', 0.01);
  const hm = actor('haven:maya', 'maya');
  hm.expr(0, 'surprised', 0.01).expr(start('L18', -0.4), 'relief', 0.7).expr(end('L18', 0.2), 'joy', 0.8)
    .expr(start('L19', 0.2), 'moved', 1.0).set('wet', start('L19', 1.0), 0.4, 1.5)
    .expr(start('N27', 0.4), 'tender', 1.2).expr(at('N27', 'people') - 0.3, 'soft_smile', 1.4);

  // a point of the picture (frame coordinates at zoom 1) as it appears through the camera
  const proj = (cam, x, y) => (cam ? [W / 2 + cam.dx + cam.z * (x - cam.x), H / 2 + cam.dy + cam.z * (y - cam.y)] : [x, y]);
  const zoom = (cam) => (cam ? cam.z : 1);

  // ------------------------------------------------------------ shots
  // cam: zoom z0 -> z1 toward a focus (default: the first face, else the centre),
  // optionally panning to f1. Shots cut on words; the scene changes dissolve.
  const shots = [];
  const cut = (t, img, o = {}) => shots.push({ t, img, cam: { z0: 1.0, z1: 1.06, ...(o.cam || {}) }, ...o });
  const sc = scene;

  // ---- the city of glass
  cut(0, 'city_wide', {
    cam: { z0: 1.0, z1: 1.12, f: [540, 980] },
    fx: (ctx, t) => { V.aurora(ctx, t, { alpha: 0.28 }); V.snow(ctx, t, { n: 70, speed: 40, wind: 25, alpha: 0.55, size: 2.4 }); },
  });
  cut(start('N2', -0.3), 'law_door', {
    cam: { z0: 1.0, z1: 1.08, f: [540, 1100], f1: [540, 800] },
    fx: (ctx, t) => { V.snow(ctx, t, { n: 110, speed: 70, alpha: 0.7 }); V.motes(ctx, t, { n: 20, rgb: [255, 210, 150], alpha: 0.5 }); },
  });
  cut(start('N3', -0.3), 'smiling_crowd', {
    cam: { z0: 1.04, z1: 1.1, f: [420, 960], f1: [660, 960] },
    fx: (ctx, t) => { V.snow(ctx, t, { n: 60, speed: 45, alpha: 0.5, seed: 4 }); V.flicker(ctx, t, { amount: 0.05, rgb: [255, 190, 120] }); },
  });
  cut(start('N4', -0.3), 'maya_smile', {
    cam: { z0: 1.0, z1: 1.1 },
    fx: (ctx, t) => V.snow(ctx, t, { n: 50, speed: 35, alpha: 0.45, seed: 5, size: 2.6 }),
  });

  // ---- the feast
  const feastFx = (ctx, t) => V.flicker(ctx, t, { amount: 0.07 });
  cut(sc.feast.start, 'feast_hall', { trans: ['dissolve', 1.0], cam: { z0: 1.0, z1: 1.07, f: [540, 1050] }, fx: feastFx });
  cut(start('L1', -0.35), 'mom_feast', { cam: { z0: 1.02, z1: 1.08 }, fx: feastFx });
  const emberFx = (ctx, t, sh, cam) => {
    feastFx(ctx, t);
    const f = face('maya_ember');
    const [x, y] = proj(cam, f ? f.cx : W / 2, f ? f.y1 + f.h * 1.0 : H * 0.62);
    // the truth burns brighter while she says it
    const k = 0.55 + 0.45 * smooth((t - start('L2')) / 1.5) - 0.25 * smooth((t - end('L2', 0.5)) / 2);
    V.ember(ctx, t, { x, y, r: (f ? f.w * 0.16 : 50) * zoom(cam), k });
  };
  cut(start('N6', -0.3), 'maya_ember', { cam: { z0: 1.0, z1: 1.12 }, fx: emberFx });
  cut(start('L3', -0.35), 'mom_feast', { cam: { z0: 1.06, z1: 1.1 }, fx: feastFx });
  cut(start('L4', -0.35), 'dad_feast', { cam: { z0: 1.0, z1: 1.06 }, fx: feastFx });
  cut(end('L4', 0.4), 'feast_hall', { cam: { z0: 1.08, z1: 1.12, f: [540, 1050] }, fx: feastFx });   // the silence
  cut(start('N7', -0.1), 'crack_floor', {
    cam: { z0: 1.0, z1: 1.1, f: [540, 1150] },
    fx: (ctx, t, sh, cam) => {
      feastFx(ctx, t);
      const [x, y] = proj(cam, 540, 1180);
      V.cracks(ctx, t, { x, y, t0: at('N7', 'glass') - 0.4, dur: 1.8, n: 8, len: 1000 * zoom(cam), seed: 21 });
    },
    shake: [[at('N7', 'crack') - 0.1, 0.8, 6]],
  });

  // ---- the sword
  const tStrike = end('N8', 0.05);                 // right after "...but a sword" (as in music.py and mix.py)
  cut(start('N8', -0.2), 'sword_sky', {
    cam: { z0: 1.0, z1: 1.14, f: [540, 700], f1: [540, 1050] },
    fx: (ctx, t, sh, cam) => {
      V.lightning(ctx, t, [start('N8', 1.0), at('N8', 'did') - 0.3, at('N8', 'peace', 0) + 2.2]);
      // the sword's light runs down the blade into the strike
      const u = clamp((t - start('N8')) / (tStrike - start('N8')));
      V.withAdd(ctx, () => {
        const [x, y] = proj(cam, 530, lerp(380, 1500, u * u)), r = 260 * zoom(cam);
        const g = ctx.createRadialGradient(x, y, 0, x, y, r);
        g.addColorStop(0, `rgba(235,245,255,${0.5 * u})`); g.addColorStop(1, 'rgba(235,245,255,0)');
        ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
      });
      V.motes(ctx, t, { n: 30, rgb: [220, 230, 255], alpha: 0.5, rise: -60, seed: 9 });
      V.flash(ctx, clamp((t - (tStrike - 0.35)) / 0.35) * 0.9);
    },
  });
  cut(tStrike, 'sword_impact', {
    trans: ['flash', 0.5],
    cam: { z0: 1.12, z1: 1.04, f: [540, 1000] },
    fx: (ctx, t, sh, cam) => {
      const [x, y] = proj(cam, 540, 1250);
      V.shockwave(ctx, t, { x, y, t0: tStrike, dur: 1.6 });
      V.snow(ctx, t, { n: 90, speed: -60, wind: 0, alpha: 0.6, seed: 12 });
      V.motes(ctx, t, { n: 40, rgb: [255, 240, 220], alpha: 0.6, rise: 40, seed: 13 });
    },
    shake: [[tStrike, 1.4, 22]],
  });
  // the hall splits: the family on one side, Maya on the other
  const tSplit = at('N9', 'turn') - 0.2;
  cut(start('N9', -0.1), 'feast_hall', {
    // across the table: the family on the far side, Maya's chair in the foreground
    cam: { z0: 1.12, z1: 1.04, f: [540, 1050] }, split: { t0: tSplit, y: 1270 },
    fx: (ctx, t) => { V.flicker(ctx, t, { amount: 0.06, rgb: [150, 190, 255] }); },
    shake: [[tSplit, 1.0, 10]],
  });
  cut(at('N9', 'man\'s', 0) - 0.15, 'shadows_wall', {
    cam: { z0: 1.0, z1: 1.1, f: [540, 900] },
    fx: (ctx, t) => V.flicker(ctx, t, { amount: 0.14, rate: 5, seed: 3 }),
  });
  cut(start('N10', -0.2), 'frozen_faces', {
    cam: { z0: 1.0, z1: 1.08 },
    fx: (ctx, t) => { V.grade(ctx, [120, 170, 230], 0.12); V.motes(ctx, t, { n: 24, rgb: [200, 230, 255], alpha: 0.4, rise: 8, seed: 14 }); },
  });
  cut(at('N10', 'numb') - 0.2, 'ice_floe', {
    cam: { z0: 1.02, z1: 1.1, f: [470, 1000], f1: [600, 1000] },
    fx: (ctx, t) => { V.aurora(ctx, t, { alpha: 0.3 }); V.snow(ctx, t, { n: 50, speed: 30, alpha: 0.4, seed: 15 }); },
  });

  // ---- the hall of mirrors
  cut(sc.mirrors.start, 'mirror_hall', {
    trans: ['dissolve', 1.0], cam: { z0: 1.0, z1: 1.12, f: [540, 1000] },
    fx: (ctx, t) => V.flicker(ctx, t, { amount: 0.06 }),
  });
  cut(end('N11', 0.15), 'mirror_refl', { cam: { z0: 1.02, z1: 1.08 }, fx: (ctx) => V.mirrorGlass(ctx) });
  cut(start('L5', -0.5), 'maya_mirror', { cam: { z0: 1.0, z1: 1.08 }, fx: (ctx, t) => V.flicker(ctx, t, { amount: 0.05 }) });
  const orbAt = (img) => {
    const f = face(img);
    return f ? [Math.min(W - 150, f.cx + f.w * 0.62), f.cy + f.h * 0.1] : [W * 0.7, H * 0.42];   // beside her face, inside the frame
  };
  const tOrb = at('N12', 'light') - 0.4;
  const lightFx = (ctx, t, sh, cam) => {
    const [x, y] = proj(cam, ...orbAt('maya_light'));
    V.orb(ctx, t, { x, y, r: 40 * zoom(cam), level: light.speechAt(t).open, alpha: smooth((t - tOrb) / 1.2) });
  };
  cut(start('N12', -0.2), 'maya_light', { cam: { z0: 1.0, z1: 1.06 }, fx: lightFx });
  // the Light's first answer: out to the hall (the orb small beside her), back in for "That isn't the same"
  cut(at('L6', 'room') - 0.2, 'mirror_hall', {
    cam: { z0: 1.12, z1: 1.2, f: [540, 1050] },
    fx: (ctx, t, sh, cam) => {
      V.flicker(ctx, t, { amount: 0.05 });
      const [x, y] = proj(cam, 610, 980);
      V.orb(ctx, t, { x, y, r: 12 * zoom(cam), level: light.speechAt(t).open });
    },
  });
  cut(at('L6', 'that') - 0.2, 'maya_light', { cam: { z0: 1.12, z1: 1.18 }, fx: lightFx });
  cut(start('L7', -0.3), 'maya_light', { cam: { z0: 1.22, z1: 1.28 }, fx: lightFx });
  cut(start('L8', -0.3), 'maya_light', { cam: { z0: 1.08, z1: 1.12 }, fx: lightFx });

  // ---- the cross
  const tBreak = at('N13', 'lose') - 0.1;          // "...will lose it"
  cut(sc.cross.start, 'figure_cross', {
    trans: ['dissolve', 1.0], cam: { z0: 1.0, z1: 1.1, f: [540, 900] },
    fx: (ctx, t) => { V.rays(ctx, t, { x: 560, y: 300, angle: Math.PI * 0.55, spread: 1.2, alpha: 0.2 }); V.motes(ctx, t, { n: 40, seed: 16 }); },
  });
  cut(at('N13', 'finds') - 0.3, 'mask_shatter', {
    cam: { z0: 1.0, z1: 1.16 },
    fx: (ctx, t) => {
      V.shards(ctx, t, { x: 540, y: 900, t0: tBreak, n: 30 });
      V.flash(ctx, Math.pow(clamp(1 - (t - tBreak) / 0.5), 2) * 0.8 * (t >= tBreak ? 1 : 0));
      V.motes(ctx, t, { n: 30, rgb: [255, 240, 220], alpha: 0.6, seed: 17 });
    },
    shake: [[tBreak, 0.8, 9]],
  });
  // "...will find it": her own face, in the light
  cut(wi('N13', words('N13').length - 2).s - 0.2, 'true_face', {   // "find" in the closing "will find it"
    trans: ['dissolve', 0.6],
    cam: { z0: 1.0, z1: 1.1 },
    fx: (ctx, t) => { V.motes(ctx, t, { n: 50, seed: 18, alpha: 0.8 }); V.rays(ctx, t, { x: 540, y: -100, angle: Math.PI / 2, spread: 0.7, alpha: 0.14, seed: 19 }); },
  });

  // ---- the guildhall
  const tStorm = start('N16');
  const guildFx = (ctx, t) => {
    const fl = 0.5 + 0.5 * Math.sin(t * 37) * Math.sin(t * 11.3);
    V.flicker(ctx, t, { amount: 0.09 + 0.08 * (fl > 0.85 ? 1 : 0), rgb: [255, 230, 170], rate: 11, seed: 6 });
    V.motes(ctx, t, { n: 25, rgb: [255, 230, 190], alpha: 0.35, rise: 25, seed: 20 });
  };
  cut(sc.guild.start, 'guildhall', { trans: ['dissolve', 0.9], cam: { z0: 1.0, z1: 1.1, f: [540, 900] }, fx: guildFx });
  cut(end('N15', 0.3), 'maya_guild', { cam: { z0: 1.0, z1: 1.08 }, fx: guildFx });
  cut(start('L10', -0.35), 'guildmaster', { cam: { z0: 1.0, z1: 1.06 }, fx: guildFx });
  cut(tStorm - 0.25, 'overwhelm', {
    cam: { z0: 1.0, z1: 1.18 },
    fx: (ctx, t) => {
      guildFx(ctx, t);
      const k = smooth((t - tStorm) / 1.6) * (1 - smooth((t - (sc.guild.end - 0.6)) / 0.6));
      V.glare(ctx, t, { k: k * (0.75 + 0.25 * Math.sin(t * 13)) });
    },
    shake: [[tStorm + 0.4, 3.5, 7]],
  });

  // ---- the sparrows
  const warmDust = (ctx, t) => V.motes(ctx, t, { n: 45, rgb: [255, 214, 150], alpha: 0.55, rise: 10, seed: 22 });
  cut(sc.sparrows.start, 'market', { trans: ['dissolve', 1.0], cam: { z0: 1.0, z1: 1.08, f: [540, 1000] }, fx: warmDust });
  cut(at('N17', 'sparrows') - 0.2, 'two_sparrows', { cam: { z0: 1.0, z1: 1.1 }, fx: warmDust });
  cut(at('N18', 'yet') - 0.15, 'sparrow_fall', { cam: { z0: 1.0, z1: 1.12, f: [540, 700], f1: [540, 1150] }, fx: warmDust });
  const tCatch = at('N18', 'outside') - 0.2;
  cut(tCatch, 'hand_catch', {
    trans: ['dissolve', 0.5], cam: { z0: 1.04, z1: 1.12 },
    fx: (ctx, t, sh, cam) => {
      // the bird held in light: a radiance gathers beneath it and rays open out
      const k = smooth((t - tCatch) / 0.8);
      const [x, y] = proj(cam, 590, 1180), z = zoom(cam);
      V.withAdd(ctx, () => {
        const g = ctx.createRadialGradient(x, y, 0, x, y, 520 * z);
        g.addColorStop(0, `rgba(255,214,140,${0.55 * k})`); g.addColorStop(0.45, `rgba(255,190,110,${0.22 * k})`); g.addColorStop(1, 'rgba(255,190,110,0)');
        ctx.fillStyle = g; ctx.fillRect(x - 520 * z, y - 520 * z, 1040 * z, 1040 * z);
      });
      V.rays(ctx, t, { x, y, angle: -Math.PI / 2, spread: 6.2, n: 12, len: 1400, alpha: 0.12 * k, seed: 23 });
      warmDust(ctx, t);
    },
  });
  cut(start('N19', -0.2), 'hair_stars', {
    cam: { z0: 1.0, z1: 1.08 },
    fx: (ctx, t, sh, cam) => {
      const f = face('hair_stars');
      if (!f) return;
      const [cx, cy] = proj(cam, f.cx, f.y0 - f.h * 0.05), z = zoom(cam);
      V.twinkles(ctx, t, { cx, cy, rx: f.w * 1.25 * z, ry: f.h * 0.75 * z, n: 46, k: (t - at('N19', 'hairs') + 0.3) / 1.2 });
    },
  });
  cut(start('N20', -0.2), 'flock_rise', {
    cam: { z0: 1.0, z1: 1.1, f: [540, 1000] },
    fx: (ctx, t) => { V.flock(ctx, t, { n: 46, t0: start('N20', 0.2), from: [540, 1150], spread: 900, rise: 420, size: 16 }); warmDust(ctx, t); },
  });

  // ---- the scrying pool
  const poolFx = (ctx, t, sh, cam) => {
    const [x, y] = proj(cam, 540, 1180);
    V.rings(ctx, t, { x, y, rmax: 360 * zoom(cam) });
    V.motes(ctx, t, { n: 20, rgb: [190, 220, 255], alpha: 0.35, rise: 14, seed: 24 });
  };
  cut(sc.pool.start, 'pool', { trans: ['dissolve', 1.0], cam: { z0: 1.0, z1: 1.08, f: [540, 1100] }, fx: poolFx });
  const momPool = { cam: { z0: 1.0, z1: 1.05 }, water: true, fx: (ctx) => V.grade(ctx, [70, 120, 200], 0.12) };
  const mayaPool = { cam: { z0: 1.0, z1: 1.06 }, fx: (ctx, t) => V.motes(ctx, t, { n: 16, rgb: [190, 220, 255], alpha: 0.3, rise: 14, seed: 25 }) };
  cut(start('L11', -0.4), 'mom_pool', { trans: ['dissolve', 0.4], ...momPool });
  cut(start('L12', -0.35), 'maya_pool', mayaPool);
  cut(start('L14', -0.35), 'mom_pool', { ...momPool, cam: { z0: 1.06, z1: 1.1 } });
  cut(start('L15', -0.35), 'maya_pool', { ...mayaPool, cam: { z0: 1.08, z1: 1.14 } });
  cut(start('N22', -0.3), 'pool', {
    trans: ['dissolve', 0.6], cam: { z0: 1.08, z1: 1.14, f: [540, 1100] },
    fx: (ctx, t, sh, cam) => {
      const [x, y] = proj(cam, 540, 1180);
      V.rings(ctx, t, { x, y, rmax: 360 * zoom(cam), alpha: 0.35 * (1 - smooth((t - start('N22')) / 2)) });   // the water stills
    },
  });

  // ---- the road
  cut(sc.flight.start, 'gate_night', {
    trans: ['dissolve', 1.0], cam: { z0: 1.0, z1: 1.1, f: [540, 1000] },
    fx: (ctx, t) => V.snow(ctx, t, { n: 130, speed: 80, wind: 20, alpha: 0.7, seed: 26 }),
  });
  const bridgeOrb = (ctx, t, sh, cam) => {
    const [x, y] = proj(cam, 560, 820);
    V.orb(ctx, t, { x, y, r: 16 * zoom(cam), level: light.speechAt(t).open });
  };
  cut(at('N23', 'hated') - 0.7, 'bridge', { trans: ['dissolve', 0.8], cam: { z0: 1.0, z1: 1.1, f: [540, 900] }, fx: bridgeOrb });
  cut(at('N23', 'stands') - 0.4, 'figure_dawn', {
    trans: ['dissolve', 0.8], cam: { z0: 1.0, z1: 1.12, f: [540, 950] },
    fx: (ctx, t) => { V.rays(ctx, t, { x: 540, y: 900, angle: -Math.PI / 2, spread: 6.2, n: 14, len: 1500, alpha: 0.14, seed: 27 }); V.motes(ctx, t, { n: 40, seed: 28 }); },
  });
  cut(start('L16', -0.3), 'maya_road', {
    cam: { z0: 1.0, z1: 1.08 },
    fx: (ctx, t, sh, cam) => {
      const [x, y] = proj(cam, ...orbAt('maya_road'));
      V.orb(ctx, t, { x, y, r: 34 * zoom(cam), level: light.speechAt(t).open });
    },
  });
  cut(start('N24', -0.2), 'figure_dawn', {
    cam: { z0: 1.12, z1: 1.2, f: [540, 950] },
    fx: (ctx, t) => { V.rays(ctx, t, { x: 540, y: 900, angle: -Math.PI / 2, spread: 6.2, n: 14, len: 1500, alpha: 0.16, seed: 27 }); V.motes(ctx, t, { n: 40, seed: 28 }); },
  });

  // ---- the next town
  const softFx = (ctx, t) => V.motes(ctx, t, { n: 30, rgb: [255, 220, 170], alpha: 0.45, rise: 8, seed: 29 });
  cut(sc.haven.start, 'haven', {
    trans: ['dissolve', 1.2], cam: { z0: 1.0, z1: 1.1, f: [540, 1000] },
    fx: (ctx, t) => { V.rays(ctx, t, { x: 900, y: 200, angle: Math.PI * 0.7, spread: 0.8, alpha: 0.12, seed: 30 }); softFx(ctx, t); },
  });
  cut(start('L17', -0.35), 'priya', { cam: { z0: 1.0, z1: 1.06 }, fx: softFx });
  cut(start('L18', -0.4), 'maya_haven', { cam: { z0: 1.0, z1: 1.08 }, fx: softFx });
  cut(start('N26', -0.2), 'sparrow_letter', { cam: { z0: 1.0, z1: 1.1 }, fx: softFx });
  cut(start('L19', -0.3), 'maya_haven', { cam: { z0: 1.12, z1: 1.2 }, fx: softFx });
  cut(start('N27', -0.3), 'maya_window', {
    trans: ['dissolve', 0.8], cam: { z0: 1.0, z1: 1.12 },
    fx: (ctx, t) => { V.rays(ctx, t, { x: 1000, y: 300, angle: Math.PI * 0.75, spread: 0.6, alpha: 0.14, seed: 31 }); softFx(ctx, t); },
  });

  shots.sort((a, b) => a.t - b.t);
  shots.forEach((s, i) => { s.i = i; s.t1 = i + 1 < shots.length ? shots[i + 1].t : timeline.duration + 1; });
  const shotIndex = (t) => { let k = 0; for (let i = 0; i < shots.length; i++) if (t >= shots[i].t) k = i; return k; };
  const sceneAt = (t) => { let s = timeline.scenes[0]; for (const x of timeline.scenes) if (t >= x.start) s = x; return s; };

  return { timeline, lips, L, at, start, end, words, shots, shotIndex, sceneAt, actors, face, faceInfo };
}

module.exports = { loadDirection };
