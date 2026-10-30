// The film: actors, blocking, camera, acting beats, props, cues — all timed to the voice schedule.
'use strict';
const { clamp, lerp, smooth, easeInOut, easeOut, easeIn, rgba, noise1, TAU, capsule, mix, shade } = require('./core');
const { Stage, env } = require('./stage');
const { headWorld, skeleton, drawHand, HANDS } = require('./rig');
const { PROPS } = require('./chars');
const P = require('./props');
const { fonts } = require('./text');

function buildFilm(sched) {
  const st = new Stage(sched);
  const t = (id) => st.t0(id), e = (id) => st.t1(id), w = (id, word, k) => st.W(id, word, k), we = (id, word, k) => st.WE(id, word, k);
  const D = st.duration;
  // props usable in hands
  for (const id in st.cast) st.cast[id].props = { ...PROPS, clipboard: P.clipboard, bread: P.bread, key: P.key };

  // ---------------------------------------------------------------- actors
  const ARM_REST = (C, side, k = 0.96) => ({ tx: side * 14, ty: (C.body.upper + C.body.fore) * k, hand: 'relax' });
  const cast = st.cast;
  const maya = st.actor('maya', 'maya', { x: 430, y: 1430, s: 1.05, pose: 'sit', hideLegs: false, facing: 0.3, head: { yaw: 0.15, pitch: 0.35, tilt: -3 }, gaze: [0.05, 0.75] }, { breathPeriod: 4.6 });
  const eli = st.actor('eli', 'eli', { x: 1250, y: 1560, s: 0.8, pose: 'stand', facing: -0.45, lean: -2, head: { yaw: -0.25, pitch: 0.35, tilt: 0 }, gaze: [0.1, 0.7] }, { breathPeriod: 4.0 });
  const inner = st.actor('innerMaya', 'innerMaya', { x: 230, y: 1500, s: 0.92, pose: 'stand', facing: 0.4, head: { yaw: 0.3, pitch: 0, tilt: 0 }, gaze: [0.2, 0], hidden: true }, { breathPeriod: 4.4 });
  const anger = st.actor('anger', 'anger', { x: 700, y: 1335, pose: 'sit', hideLegs: false, facing: 0.1, head: { yaw: 0.1, pitch: 0.15, tilt: 0 }, gaze: [0.1, 0.4] }, { breathPeriod: 3.4, talkMotion: 1.5 });
  const annoy = st.actor('annoy', 'annoy', { x: 380, y: 1560, pose: 'stand', facing: 0.45, head: { yaw: 0.55, pitch: -0.1, tilt: 2 }, gaze: [0.4, -0.15] }, { breathPeriod: 4.2, talkMotion: 0.8 });
  const fear = st.actor('fear', 'fear', { x: 1150, y: 1620, pose: 'stand', facing: -0.2, lean: 4, head: { yaw: -0.2, pitch: 0.1, tilt: 0 }, gaze: [-0.2, 0.1] }, { breathPeriod: 2.6, talkMotion: 1.4, sway: 1.6 });
  const sad = st.actor('sadness', 'sadness', { x: 170, y: 1700, pose: 'floorHug', facing: 0.25, lean: 10, head: { yaw: 0.2, pitch: 0.5, tilt: -6 }, gaze: [0.1, 0.8] }, { breathPeriod: 5.2, talkMotion: 0.5, sway: 0.7 });
  const nana = st.actor('nana', 'nana', { x: 720, y: 1600, pose: 'stand', facing: -0.35, lean: 6, head: { yaw: -0.4, pitch: 0.35, tilt: -4 }, gaze: [-0.3, 0.6] }, { breathPeriod: 4.8, talkMotion: 0.8 });
  const kid = st.actor('youngMaya', 'youngMaya', { x: 430, y: 1560, s: 1, pose: 'stand', facing: 0.4, head: { yaw: 0.4, pitch: 0.3, tilt: 4 }, gaze: [0.3, 0.6] }, { breathPeriod: 3.2 });

  // lip-sync assignment: Maya's hearth lines go to the inner self
  st.speak('maya', (l) => l.sp === 'maya' && l.sc !== 'hearth');
  st.speak('innerMaya', (l) => l.sp === 'maya' && l.sc === 'hearth');
  st.speak('eli', (l) => l.sp === 'eli');
  st.speak('anger', (l) => l.sp === 'anger', 1.1);
  st.speak('annoy', (l) => l.sp === 'annoy', 0.9);
  st.speak('fear', (l) => l.sp === 'fear', 1.05);
  st.speak('sadness', (l) => l.sp === 'sad', 0.75);
  st.speak('nana', (l) => l.sp === 'nana', 0.9);
  // listeners acknowledge the person they're hearing
  st.listen('maya', (l) => l.sp === 'eli');
  st.listen('eli', (l) => l.sp === 'maya' && l.sc !== 'hearth');
  st.listen('innerMaya', (l) => ['annoy', 'fear', 'sad', 'anger'].includes(l.sp));
  st.listen('fear', (l) => l.sp === 'maya' && l.sc === 'hearth');
  st.listen('sadness', (l) => l.sp === 'maya' && l.sc === 'hearth');
  st.listen('annoy', (l) => l.sp === 'maya' && l.sc === 'hearth');

  // helper: world position of an actor's eye at time T (for camera targets)
  const eyeAt = (id, T, side = -1) => {
    const a = st.actors[id], S = a.sample(T), C = st.cast[a.rig];
    const [hx, hy, hh] = headWorld(C, S);
    const yaw = S.head.yaw || 0, sc = (S.s || 1) * (C.scale || 1);
    return [hx + Math.sin(side * C.eyes.spacing + yaw * 0.62) * C.head.w * 0.49 * sc, hy + C.head.h * (C.eyes.y ?? 0.03) * sc];
  };
  const headAt = (id, T) => { const a = st.actors[id]; return headWorld(st.cast[a.rig], a.sample(T)); };

  st.lightMod = (envName, T, id, S, L, eo) => {
    if (envName === 'hearth') {
      const fire = clamp(eo.fire ?? 1, 0, 2);
      const dx = 1525 - S.x, near = clamp(1 - (Math.abs(dx) - 120) / 950, 0, 1) * fire / 1.2;
      if (near > 0.05) {
        L.rimDir = Math.atan2(-160, dx); L.rimColor = '#ffab55'; L.rimAmt = Math.max(L.rimAmt || 0, 0.9 * near);
        L.keyColor = mix(L.keyColor, '#ffb36b', 0.45 * near); L.keyAmt = Math.max(L.keyAmt || 0, 0.65 * near); L.keyDir = Math.atan2(-120, dx);
      }
      const door = eo.doorOpen ?? 0;
      if (door > 0.15 && S.x < 620) { L.rimDir = Math.atan2(-420, 200 - S.x); L.rimColor = '#ffd27a'; L.rimAmt = Math.max(L.rimAmt || 0, 0.75 * door); }
      if (eo.view === 'night' && S.x > 380 && S.x < 920) { L.rimDir = -0.4; L.rimColor = '#a9c2f2'; L.rimAmt = 0.95; L.ambient = '#e8ecff'; L.ambientAmt = 0.1; }
    }
    if (envName === 'kitchen' && id === 'maya') { L.rimDir = Math.atan2(-420, -320); L.rimColor = '#ffc68a'; L.rimAmt = Math.max(L.rimAmt || 0, 0.6); }
    if (envName === 'nanaKitchen' || envName === 'memory') { L.rimAmt = Math.max(L.rimAmt || 0, 0.45); }
  };

  // ================================================================ SCENE 1 — kitchen, dusk
  const k0 = 0, k1 = e('E3') + 2.1;
  st.scene('kitchen1', k0, k1, 'intimate grief');
  st.amb('room_tone', 0, k1, 0.6);
  st.amb('clock_tick', 0, k1, 0.45);
  const kitchenOpt = (T) => ({ dusk: clamp(0.18 + T / 600, 0, 0.5), lamp: 1 });

  // Maya holds Nana's mug in both hands on the table
  const MUG = [430 + 10, 1372]; // world, bottom centre of mug
  const mugHands = (C, S) => {
    // hand targets relative to shoulders (local, seated root at the hip)
    return {
      L: { tx: 58, ty: 196, hand: 'cup', view: 'back', rotAbs: -8, thumb: -1, bend: -1, locked: true, foreK: 0.62, follow: 0.45 },
      R: { tx: -42, ty: 196, hand: 'cup', view: 'back', rotAbs: 188, thumb: 1, bend: 1, locked: true, foreK: 0.62, follow: 0.45 },
    };
  };
  maya.set(0, { 'arms.L': mugHands().L, 'arms.R': mugHands().R }, 0.01);
  maya.expr(0, 'sad', 0.01, 1, { glisten: 0.45 });
  // thumb rub: tiny hand motion (opening seconds)
  maya.set(1.2, { 'arms.R': { ...mugHands().R, tx: -46, ty: 193 } }, 1.0);
  maya.set(2.3, { 'arms.R': { ...mugHands().R, tx: -40, ty: 197 } }, 1.0);

  // Eli: leaning on the counter, phone in his right hand, left hand on the counter edge behind him
  const ELI_PHONE = { tx: -70, ty: 150, hand: 'grip', view: 'back', rotAbs: -100, bend: 1, holding: 'phoneHeld' };
  const ELI_BACK = { tx: -10, ty: 300, hand: 'relax', behind: true };
  cast.eli.props.phoneHeld = (ctx, C, o) => {
    ctx.save(); ctx.translate(C.body.hand * 0.55, 0); ctx.rotate(Math.PI / 2);
    ctx.fillStyle = '#1d1f24'; P.roundRectPath(ctx, -22, -40, 44, 80, 7); ctx.fill();
    ctx.fillStyle = 'rgba(140,170,210,0.8)'; P.roundRectPath(ctx, -18, -35, 36, 70, 5); ctx.fill();
    ctx.restore();
    const [tx, ty] = o.hand.thumb; ctx.fillStyle = C.skin;
    ctx.beginPath(); capsule(ctx, tx - 14, ty * 0.92, 6.5, tx + 2, ty * 0.92, 5.5); ctx.fill();
  };
  eli.set(0, { 'arms.R': ELI_PHONE, 'arms.L': ELI_BACK }, 0.01);
  eli.expr(0, 'avoid', 0.01);

  // Shot 1a: opening close-up — Maya, the mug, the first still of the film
  st.shot({ t0: 0, env: 'kitchen', envOpt: kitchenOpt, actors: ['maya'], armsFront: ['maya'], cam: [[0, 455, 1205, 2.45], [0, 455, 1195, 2.6, t('E1')]],
    front: (ctx, T) => P.mug(ctx, MUG[0], MUG[1], 1, null, { steam: true, t: T }) });
  st.title(0, 3.6, [{ text: 'THE FAMILY INSIDE', font: '58px InterXB', spacing: 10 }, { text: 'a short film about grief', font: 'italic 36px InterItalic', color: '#f3e3cc' }], 250, { fadeIn: 0, fadeOut: 0.8 });
  st.label(0.2, 'maya', { dur: 3.6, side: -1, dy: 120 });
  // Maya: tiny sigh, eyes on the mug
  maya.set(1.6, { head: { yaw: 0.12, pitch: 0.42, tilt: -4 } }, 1.4);
  maya.blink(2.6);

  // Shot 1b: wide two-shot — Eli speaks from the counter
  const s1b = t('E1') - 0.35;
  st.shot({ t0: s1b, env: 'kitchen', envOpt: kitchenOpt, actors: ['eli', 'maya'], armsFront: ['maya'], cam: [[s1b, 880, 1210, 0.9], [s1b, 880, 1200, 0.95, 4]],
    front: (ctx, T) => P.mug(ctx, MUG[0], MUG[1], 1, null, { steam: true, t: T }) });
  st.label(s1b, 'eli', { dur: 3.0 });
  eli.look(t('E1') - 0.2, 0.1, 0.65).head(t('E1') - 0.2, -0.25, 0.3, 0);
  eli.look(w('E1', 'still'), -0.6, 0.15, 0.25).head(w('E1', 'still'), -0.5, 0.05, 3, 0.5);   // glances up at her
  eli.expr(w('E1', 'still'), 'neutral', 0.4, 1, { browIn: 0.15, brow: 0.1 });
  eli.expr(w('E1', 'Mae'), 'soft', 0.5, 0.6, { browIn: 0.3 });                       // "Mae..." softer
  eli.look(we('E1', 'Mae') + 0.1, -0.2, 0.4, 0.3);
  eli.look(w('E1', 'month') - 0.15, -0.55, 0.1, 0.25);
  maya.look(t('E1') + 0.3, 0.05, 0.75);

  // Shot 1c: Maya MCU — "It's her mug."
  const s1c = t('M1') - 0.75;
  st.shot({ t0: s1c, env: 'kitchen', envOpt: kitchenOpt, actors: ['maya'], armsFront: ['maya'], cam: [[s1c, 470, 1240, 2.5], [s1c, 470, 1235, 2.6, 2.5]],
    front: (ctx, T) => P.mug(ctx, MUG[0], MUG[1], 1, null, { steam: true, t: T }) });
  maya.expr(s1c, 'hurt', 0.6, 0.7, { glisten: 0.5 });
  maya.look(w('M1', 'her') - 0.05, 0.55, -0.05, 0.3).head(w('M1', 'her') - 0.1, 0.35, 0.05, 2, 0.7);  // lifts eyes to him on "her"

  // Shot 1d: Eli MCU — "It's a mug. Crying over it won't bring her back. You need to move on."
  const s1d = t('E2') - 0.4;
  st.shot({ t0: s1d, env: 'kitchen', envOpt: kitchenOpt, actors: ['eli'], cam: [[s1d, 1240, 920, 2.25], [s1d, 1240, 925, 2.35, 5]] });
  eli.set(s1d + 0.1, { shrug: 0.6 }, 0.25).set(s1d + 0.45, { shrug: 0 }, 0.5);          // sigh
  eli.set(t('E2') + 0.1, { 'arms.R': { tx: -50, ty: 250, hand: 'relax', bend: 1, hideHand: true } }, 0.7); // pockets the phone
  eli.set(we('E2', 'mug'), { shrug: 0.5 }, 0.2).set(we('E2', 'mug') + 0.35, { shrug: 0 }, 0.4);
  eli.expr(t('E2'), 'avoid', 0.4, 1, { smile: -0.05 });
  eli.look(w('E3', 'Crying') - 0.1, 0.45, 0.45, 0.3).head(w('E3', 'Crying') - 0.2, 0.15, 0.25, -3, 0.7);   // says it to the floor/away
  eli.look(w('E3', 'You') - 0.05, -0.55, 0.05, 0.22).head(w('E3', 'You') - 0.1, -0.35, 0.05, 0, 0.5);    // brief look at her
  eli.look(w('E3', 'move') + 0.05, 0.2, 0.55, 0.3);                                                  // can't hold it
  eli.expr(w('E3', 'move'), 'guilty', 0.6, 0.5);

  // Shot 1e: push in on Maya's eyes, then through the eye into the inner world
  const s1e = e('E3') + 0.25;
  const eyeT = s1e + 0.2;
  maya.expr(s1e - 0.1, 'hurt', 0.5, 1.1, { browSq: 0.45, press: 0.55, glisten: 0.75, lidU: 0.3 });
  maya.look(s1e + 0.3, 0.45, 0.05, 0.25);
  const ey = [470, 1095];
  st.shot({ t0: s1e, env: 'kitchen', envOpt: kitchenOpt, actors: ['maya'], armsFront: ['maya'],
    cam: (() => { const eyeW = eyeAt('maya', s1e + 1, 1); return [[s1e, 470, 1110, 3.0], [s1e, eyeW[0], eyeW[1], 6.5, 1.5], [s1e + 1.5, eyeW[0] + 1, eyeW[1] + 1, 26, 0.75, easeIn]]; })(),
    front: (ctx, T) => P.mug(ctx, MUG[0], MUG[1], 1, null, { steam: true, t: T }) });
  st.sfx(s1e + 1.45, 'whoosh_soft', 0.8);

  // ================================================================ SCENE 2 — the inner hearth
  const h0 = s1e + 2.25;
  const h1 = t('M5') - 1.3;
  st.scene('hearth1', h0, h1, 'warm inner room');
  st.amb('fire_crackle', h0, h1, 0.6);
  const hearthState = { fire: 1, doorOpen: 0, view: 'kitchen', cornerLight: 0 };
  const fireTrack = [];
  const fireAt = (T) => { let v = 1; for (const [a, b, val, r] of fireTrack) { if (T >= a && T <= b) v = lerp(v, val, smooth((T - a) / r) * (1 - smooth((T - (b - r)) / r))); } return v; };
  const doorTrack = [];
  const doorAt = (T) => { let v = 0; for (const [a, dur, val] of doorTrack) if (T >= a) v = lerp(v, val, smooth((T - a) / dur)); return v; };
  const viewKeys = [];
  const viewAt = (T) => { let v = 'kitchen'; for (const [a, val] of viewKeys) if (T >= a) v = val; return v; };
  const cornerKeys = [];
  const cornerAt = (T) => { let v = 0; for (const [a, dur, val] of cornerKeys) if (T >= a) v = lerp(v, val, smooth((T - a) / dur)); return v; };
  const hearthOpt = (extra) => (T) => ({ fire: fireAt(T), doorOpen: doorAt(T), view: viewAt(T), cornerLight: cornerAt(T), ...(typeof extra === 'function' ? extra(T) : extra || {}) });

  // blocking at the start of the hearth
  annoy.set(h0, { x: 380, y: 1560 }, 0.01);
  const CLIP_L = { tx: 50, ty: 150, hand: 'grip', view: 'back', bend: -1, holding: 'clipboard', rotAbs: -30, thumb: -1 };
  const PENCIL_R = { tx: -60, ty: 220, hand: 'pinch', view: 'back', bend: 1, holding: 'pencil', rotAbs: -150 };
  annoy.set(h0, { 'arms.L': CLIP_L, 'arms.R': PENCIL_R }, 0.01);
  annoy.expr(h0, 'annoyed', 0.01, 0.6);
  anger.set(h0, { 'arms.L': { tx: 110, ty: 150, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -110, ty: 140, hand: 'fist', view: 'back', bend: 1 }, armOrder: 'RL' }, 0.01);
  anger.expr(h0, 'grumpy', 0.01, 1);
  sad.expr(h0, 'sad', 0.01, 1);
  sad.set(h0, { 'arms.L': { tx: 60, ty: 120, hand: 'soft', view: 'back', bend: -1, rotAbs: 10 }, 'arms.R': { tx: -60, ty: 120, hand: 'soft', view: 'back', bend: 1, rotAbs: 170 } }, 0.01);
  fear.expr(h0, 'worried', 0.01, 1);
  fear.set(h0, { 'arms.L': { tx: 60, ty: 150, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -60, ty: 150, hand: 'fist', view: 'back', bend: 1 } }, 0.01);
  // Fear paces back and forth in front of the hearth until Anger erupts
  {
    let x = 1150, dir = 1, tt = h0;
    while (tt < t('G1') - 1) {
      const nx = dir > 0 ? 1320 : 1010;
      const dur = Math.abs(nx - x) / 150;
      fear.walk(tt, tt + dur, nx, undefined, 30);
      fear.set(tt, { facing: dir * 0.6 }, 0.3).head(tt, dir * 0.5, 0.15, 0, 0.4);
      x = nx; dir = -dir; tt += dur + 0.6;
    }
  }

  // Shot 2a: from the round window (match cut from the eye), pull back to the wide room
  const wv = [650, 640];
  st.shot({ t0: h0, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'annoy', 'anger', 'fear'], trans: { type: 'flash', dur: 0.7, color: '#fff2d8', amt: 0.9 },
    cam: [[h0, wv[0], wv[1], 3.2], [h0 + 0.3, 790, 1060, 0.74, 4.6, easeInOut]] });
  st.label(h0 + 1.5, 'annoy', { dur: 4.2 });
  st.label(h0 + 1.9, 'anger', { dur: 4.2 });
  st.label(h0 + 2.3, 'fear', { dur: 4.2, dy: -40 });
  st.label(h0 + 4.4, 'sadness', { dur: 3.8 });

  // Shot 2b: Annoyance at the window — "Hold on. 'Move on'?"
  const s2b = t('A1') - 0.45;
  st.shot({ t0: s2b, env: 'hearth', envOpt: hearthOpt(), actors: ['annoy'], cam: [[s2b, 470, 860, 2.0], [s2b, 470, 870, 2.12, 9]] });
  annoy.look(s2b, 0.55, -0.1).head(s2b, 0.6, -0.08, 2);
  annoy.expr(t('A1'), 'skeptical', 0.3, 1.1);
  annoy.set(w('A1', 'Move') - 0.1, { 'arms.R': { ...PENCIL_R, tx: -40, ty: 196 } }, 0.12).set(w('A1', 'Move') + 0.1, { 'arms.R': PENCIL_R }, 0.12);
  st.sfx(w('A1', 'Move') - 0.05, 'pencil_tap', 0.7);
  annoy.look(t('A2') + 0.05, -0.15, 0, 0.25).head(t('A2'), 0.0, 0, -3, 0.5);           // turns from the window
  annoy.expr(w('A2', 'whose'), 'annoyed', 0.4, 1, { browR: 0.55 });
  // N3/N4: narration while she studies the window, takes notes; "laser focus": leans in, eyes narrow
  annoy.look(t('N3') + 0.2, 0.55, -0.12).head(t('N3'), 0.6, -0.08, 2, 0.6);
  annoy.set(t('N3') + 0.6, { 'arms.R': { ...PENCIL_R, tx: -30, ty: 200 } }, 0.3);
  annoy.set(t('N3') + 1.0, { 'arms.L': { ...CLIP_L, note: 1 } }, 0.6);
  annoy.expr(w('N3', 'ignored'), 'annoyed', 0.5, 1.2);
  for (const tk of [t('N3') + 2.3, t('N3') + 3.4, t('N4') + 1.6]) {   // writes / taps while she watches
    annoy.set(tk, { 'arms.R': { ...PENCIL_R, tx: -24, ty: 186 } }, 0.12).set(tk + 0.14, { 'arms.R': { ...PENCIL_R, tx: -30, ty: 200 } }, 0.12);
    st.sfx(tk + 0.1, 'pencil_tap', 0.35);
  }
  annoy.look(t('N3') + 2.0, 0.1, 0.7, 0.25).look(t('N3') + 3.0, 0.55, -0.12, 0.25);
  annoy.set(w('N4', 'laser'), { lean: 9, glow: 1.6 }, 0.6).expr(w('N4', 'laser'), 'annoyed', 0.4, 1.3, { lidU: 0.6, lidL: 0.25 });
  annoy.set(we('N4', 'dismissive'), { lean: 0, glow: 1 }, 0.6);

  // Shot 2c: "Somebody should ask him. Why did you say that?" — turns to the room
  const s2c = t('A3') - 0.3;
  st.shot({ t0: s2c, env: 'hearth', envOpt: hearthOpt(), actors: ['anger', 'annoy'], cam: [[s2c, 560, 980, 1.35], [s2c, 570, 990, 1.42, 4]] });
  annoy.set(s2c, { facing: -0.1 }, 0.5).head(s2c, -0.2, 0, 0, 0.6).look(s2c + 0.1, 0.4, 0.2);
  annoy.set(w('A3', 'Why'), { 'arms.R': { tx: -20, ty: 120, hand: 'pinch', view: 'back', bend: 1, holding: 'pencil', rotAbs: -40 } }, 0.35);
  annoy.expr(w('A3', 'Why'), 'skeptical', 0.4, 1);

  // Shot 2d: nobody answers — wide
  const s2d = e('A3') + 0.4;
  st.shot({ t0: s2d, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'annoy', 'anger', 'fear'], cam: [[s2d, 705, 1110, 0.8], [s2d, 705, 1110, 0.83, 3]] });
  annoy.set(t('A4') - 0.2, { 'arms.R': { tx: -14, ty: 300, hand: 'pinch', view: 'back', bend: 1, holding: 'pencil' } }, 0.6);
  annoy.expr(t('A4'), 'annoyed', 0.5, 1, { lidU: 0.5 });
  annoy.look(t('A4'), 0.6, 0.1, 0.3).head(t('A4'), 0.4, 0, 3, 0.5);
  annoy.look(w('A4', 'Anybody') - 0.1, 0.0, 0.0, 0.4).head(w('A4', 'Anybody') - 0.1, 0.05, 0.05, -2, 0.6);   // deadpan to camera-ish
  anger.look(t('A4') - 0.5, -0.4, 0.2, 0.3).head(t('A4') - 0.5, -0.3, 0.1, 0, 0.6);  // Anger notices
  anger.expr(t('A4'), 'grumpy', 0.4, 1.3);


  // helper: arm target (relative to shoulder) so the hand reaches world point (wx, wy) at time T
  const reach = (id, T, side, wx, wy) => {
    const a = st.actors[id], S = a.sample(T), C = st.cast[a.rig];
    const sk = skeleton(C, S);
    const sc = (S.s || 1) * (C.scale || 1);
    const sh = side < 0 ? sk.shL : sk.shR;
    return { tx: (wx - S.x) / sc - sh[0], ty: (wy - S.y) / sc - sh[1] };
  };
  const shoulderWorld = (id, T, side) => {
    const a = st.actors[id], S = a.sample(T), C = st.cast[a.rig];
    const sk = skeleton(C, S), sc = (S.s || 1) * (C.scale || 1);
    const sh = side < 0 ? sk.shL : sk.shR;
    return [S.x + sh[0] * sc, S.y + sh[1] * sc];
  };
  const hearth = env('hearth');
  const vis = [];  // [t0, t1, fn(T) -> vision object]
  const drawVisions = (ctx, T) => { for (const [a, b, f] of vis) if (T >= a && T <= b && hearth.drawVision) hearth.drawVision(ctx, T, f(T)); };

  // ================================================================ SCENE 3 — Anger
  const g0 = t('G1') - 0.5;
  fireTrack.push([w('G1', 'HEY') - 0.05, t('N7') - 0.5, 2, 0.35]);
  fireTrack.push([t('N7') - 0.5, e('N8') + 1.0, 1.6, 0.6]);
  anger.set(g0 + 0.1, { y: 1240 }, 0.35, easeOut);                       // springs up behind the table
  anger.set(w('G1', 'HEY') - 0.08, { flame: 1.4, 'arms.L': { tx: 40, ty: 230, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -40, ty: 230, hand: 'fist', view: 'back', bend: 1 } }, 0.12);
  anger.expr(w('G1', 'HEY') - 0.1, 'furious', 0.12, 1.1);
  st.sfx(w('G1', 'HEY') - 0.02, 'flame_burst', 1.0);
  st.sfx(w('G1', 'HEY'), 'fire_roar', 0.8);
  anger.look(w('G1', 'talking') - 0.3, -0.6, 0.0, 0.2).head(w('G1', 'talking') - 0.3, -0.45, 0, -4, 0.3);
  anger.set(w('G1', 'talking') - 0.3, { 'arms.L': { tx: -115, ty: -20, hand: 'point', view: 'back', bend: -1, rotAbs: 200 } }, 0.25);   // points at Annoyance
  anger.look(w('G1', 'anybody') - 0.1, 0.0, 0.05, 0.2).head(w('G1', 'anybody') - 0.15, 0.05, -0.05, 3, 0.4);
  anger.set(w('G1', 'listening') - 0.2, { 'arms.L': { tx: 10, ty: -60, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -10, ty: -60, hand: 'fist', view: 'back', bend: 1 }, flame: 1.7 }, 0.25);
  anger.set(e('G1') + 0.2, { 'arms.L': { tx: 60, ty: 120, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -60, ty: 120, hand: 'fist', view: 'back', bend: 1 }, flame: 1.1 }, 0.5);
  st.shot({ t0: g0, env: 'hearth', envOpt: hearthOpt(), actors: ['anger'], cam: [[g0, 700, 1060, 2.2], [w('G1', 'HEY') - 0.05, 700, 1030, 2.45, 0.12], [w('G1', 'HEY') + 0.2, 700, 1030, 2.35, 1.5]],
    handheld: 3 });
  // everyone startles (seen in the wide that follows)
  const startle = w('G1', 'HEY');
  fear.set(startle, { y: 1585, lean: -6, 'arms.L': { tx: 50, ty: 40, hand: 'open', view: 'palm', bend: -1 }, 'arms.R': { tx: -50, ty: 40, hand: 'open', view: 'palm', bend: 1 } }, 0.15)
    .set(startle + 0.25, { y: 1620 }, 0.3);
  fear.expr(startle, 'fear', 0.15, 1.2).look(startle, -0.4, 0.1, 0.1).head(startle, -0.4, 0, 0, 0.3);
  sad.set(startle, { head: { yaw: 0.35, pitch: -0.1, tilt: 0 } }, 0.3).look(startle, 0.6, -0.2, 0.15).expr(startle, 'worried', 0.3, 1);
  annoy.expr(startle, 'surprised', 0.15, 0.8).look(startle, 0.5, 0.15, 0.12).head(startle, 0.35, 0, 0, 0.3);

  // N5: wide — the room after the eruption
  const s3b = t('N5') - 0.3;
  st.shot({ t0: s3b, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'annoy', 'anger', 'fear'], cam: [[s3b, 705, 1080, 0.79], [s3b, 705, 1080, 0.82, 3.5]] });
  annoy.expr(t('N5') + 0.6, 'annoyed', 0.8, 0.6, { brow: 0.2 });
  fear.expr(t('N5') + 0.8, 'fear', 0.8, 0.8);
  anger.look(t('N5') + 0.3, 0.6, 0.1, 0.3).head(t('N5') + 0.3, 0.5, 0, 0, 0.6);   // eyes the fire
  sad.set(t('N5'), { lean: 14 }, 0.8).set(t('N5') + 0.9, { lean: 8 }, 0.9).set(t('N5') + 1.9, { lean: 13 }, 0.9);
  fear.look(t('N5') + 1.2, -0.6, 0.2, 0.25).look(t('N5') + 2.2, 0.4, 0.0, 0.25);
  annoy.look(t('N5') + 1.6, 0.6, 0.2, 0.3);

  // N6: Anger at the hearth pumping the bellows — "It amplifies that voice"
  const s3c = t('N6') - 0.25;
  anger.set(s3c, { x: 1300, y: 1610, pose: 'stand', hideLegs: false, facing: 0.65, lean: 6, flame: 1.2 }, 0.01);
  anger.head(s3c, 0.6, 0.1, 0, 0.01).look(s3c, 0.6, 0.15, 0.01);
  const pump = (T) => 0.5 + 0.5 * Math.cos(clamp((T - s3c - 0.3) / 0.65, 0, 3.4) * Math.PI);
  const BEL = { x: 215, y: -320, s: 0.9 };
  // bellows handle positions (actor-local) for open amount p: back ends of the two boards
  const handle = (p, sd) => {
    const a = (0.18 + 0.32 * p) * sd, x = -100, y = sd * 26;
    return [BEL.x + BEL.s * (x * Math.cos(a) - y * Math.sin(a)), BEL.y + BEL.s * (x * Math.sin(a) + y * Math.cos(a))];
  };
  for (let k = 0; k < 3; k++) st.sfx(s3c + 0.3 + 0.65 + k * 1.3, 'bellows', 0.8);
  st.shot({ t0: s3c, env: 'hearth', envOpt: hearthOpt({ bellowsHidden: true }), actors: ['anger'], cam: [[s3c, 1400, 1180, 1.55], [s3c, 1410, 1170, 1.65, 3]],
    beforeActor: (ctx, T, id, S) => {
      if (id !== 'anger') return;
      const pu = pump(T);
      const sk = skeleton(cast.anger, S);
      const hT = handle(pu, -1), hB = handle(pu, 1);
      S.arms = { ...S.arms,
        L: { tx: hT[0] - sk.shL[0], ty: hT[1] - sk.shL[1], hand: 'fist', view: 'back', bend: -1, foreK: 0.9 },
        R: { tx: hB[0] - sk.shR[0], ty: hB[1] - sk.shR[1], hand: 'fist', view: 'back', bend: 1, foreK: 0.9 } };
      S.preArms = (c2) => P.bellows(c2, BEL.x, BEL.y, BEL.s, pu, S._light);
    } });

  // N7–N8: the words rise in the smoke above the mantel
  const words7 = [['NAME-CALLING', w('N7', 'Name-calling')], ['LABELING WITHOUT CONSENT', w('N7', 'Labeling')], ['DISMISSIVENESS', w('N7', 'Dismissiveness')], ['INVALIDATION', w('N7', 'Invalidation')]];
  const words8 = [['MINIMIZING LIVED EXPERIENCE', w('N8', 'Minimizing')], ['HUMANITY', w('N8', 'humanity')]];
  vis.push([t('N7') - 0.4, t('N8') - 0.1, (T) => ({ kind: 'words', items: words7.map(([text, t0]) => ({ text, t0 })), alpha: 1 - smooth((T - (t('N8') - 0.6)) / 0.5) }) ]);
  vis.push([t('N8') - 0.3, e('N8') + 1.0, (T) => ({ kind: 'words', items: words8.map(([text, t0]) => ({ text, t0 })), alpha: 1 - smooth((T - e('N8') - 0.4) / 0.6) }) ]);
  const s3d = t('N7') - 0.35;
  anger.set(s3d, { 'arms.L': { tx: 30, ty: 240, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -30, ty: 240, hand: 'fist', view: 'back', bend: 1 }, facing: 0.2, lean: 0 }, 0.4);
  anger.head(s3d, 0.25, -0.5, 0, 0.6).look(s3d, 0.2, -0.75, 0.3).expr(s3d, 'angry', 0.6, 1);
  st.shot({ t0: s3d, env: 'hearth', envOpt: hearthOpt(), actors: ['anger'], cam: [[s3d, 1500, 820, 1.25], [s3d, 1500, 760, 1.35, e('N8') - s3d]], over: drawVisions });
  // under the anger, hurt — on "humanity"
  const s3e = w('N8', 'humanity') - 0.5;
  anger.head(s3e, -0.1, 0.25, -3, 0.8).look(s3e + 0.1, -0.2, 0.55, 0.4);
  anger.expr(s3e, 'hurt', 0.9, 1.0, { browSq: 0.5 });
  anger.set(s3e, { flame: 0.45 }, 1.2);
  st.shot({ t0: s3e, env: 'hearth', envOpt: hearthOpt(), actors: ['anger'], cam: [[s3e, 1290, 980, 2.3], [s3e, 1290, 990, 2.45, 3.5]], trans: { type: 'dissolve', dur: 0.4 } });

  // M2: the door opens; the self (inner Maya) steps in — "Okay. Okay... I'm here. I'm listening."
  const s3f = t('M2') - 2.35;
  doorTrack.push([s3f + 0.1, 1.4, 1]);
  doorTrack.push([e('M2') + 0.6, 1.2, 0]);
  st.sfx(s3f + 0.1, 'door_creak', 0.6);
  inner.set(s3f + 0.55, { hidden: false, x: 200, y: 1495, s: 0.86 }, 0.01);
  inner.set(s3f + 0.55, { glow: 0 }, 0.01).set(s3f + 0.6, { glow: 1 }, 0.8);
  inner.expr(s3f + 0.5, 'worried', 0.01, 0.5).look(s3f + 0.6, 0.6, 0.0).head(s3f + 0.6, 0.45, 0, 0);
  inner.walk(s3f + 0.9, t('M2') + 0.6, 650, 1650, 36);
  inner.set(s3f + 0.9, { s: 1.0 }, t('M2') + 0.6 - s3f - 0.9);
  inner.set(t('M2') - 0.2, { 'arms.L': { tx: -14, ty: 300, hand: 'relax' }, 'arms.R': { tx: 95, ty: 135, hand: 'open', view: 'palm', bend: 1, rotAbs: -75, foreK: 0.85 } }, 0.5);
  inner.expr(t('M2'), 'tender', 0.5, 0.8);
  inner.look(w('M2', "I'm") - 0.1, 0.65, 0.05).head(w('M2', "I'm") - 0.1, 0.55, 0, 3, 0.6);
  inner.set(w('M2', 'listening') - 0.2, { 'arms.R': { tx: -70, ty: 90, hand: 'flat', view: 'back', bend: 1, rotAbs: 180 }, 'arms.L': { tx: -14, ty: 300, hand: 'relax' } }, 0.5);
  anger.set(s3f, { x: 1300, y: 1610, facing: -0.5, flame: 1.2 }, 0.01).head(s3f + 0.8, -0.6, 0, 0, 0.6).look(s3f + 0.8, -0.7, 0.05);
  anger.expr(s3f + 0.8, 'angry', 0.5, 0.9);
  for (const id of ['annoy', 'fear', 'sadness']) st.actors[id].look(s3f + 0.7, -0.5, 0.05).head(s3f + 0.7, -0.4, 0, 0);
  st.label(s3f + 0.6, 'innerMaya', { text: 'Maya (the self)', emoji: '✨', dur: 3.2 });
  st.shot({ t0: s3f, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'annoy', 'fear', 'anger', 'innerMaya'], cam: [[s3f, 520, 1150, 0.95], [s3f + 1.2, 580, 1180, 1.08, 3.5]] });

  // G2: Anger's flames go out — "...Took you long enough."
  const s3g = t('G2') - 0.65;
  anger.set(s3g, { flame: 0.0 }, 1.3).set(s3g, { 'arms.L': { tx: 120, ty: 145, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -120, ty: 140, hand: 'fist', view: 'back', bend: 1 }, armOrder: 'RL' }, 0.7);
  anger.set(s3g, { shrug: 0.5 }, 0.3).set(s3g + 0.35, { shrug: 0 }, 0.7);
  anger.expr(s3g + 0.2, 'grumpy', 0.6, 0.8, { browIn: 0.1 });
  anger.look(t('G2'), -0.75, 0.15, 0.3).head(t('G2'), -0.25, 0.1, 2, 0.6);
  fireTrack.push([s3g, s3g + 1.5, 0.75, 0.6]);
  st.shot({ t0: s3g, env: 'hearth', envOpt: hearthOpt(), actors: ['anger'], cam: [[s3g, 1290, 990, 2.2], [s3g, 1290, 995, 2.3, 2]] });

  // M3 / A5 / M4: Maya and Annoyance
  const s3h = t('M3') - 0.55;
  inner.set(s3h, { x: 700, y: 1600, s: 0.95, facing: -0.75, 'arms.L': { tx: -14, ty: 300, hand: 'relax' }, 'arms.R': { tx: 14, ty: 300, hand: 'relax' } }, 0.01);
  inner.head(s3h, -0.8, -0.1, 0, 0.01).look(s3h, -0.75, -0.15, 0.01).expr(s3h, 'listening', 0.01);
  annoy.set(s3h, { facing: 0.35, 'arms.R': { ...PENCIL_R, tx: -20, ty: 190 } }, 0.01).head(s3h, 0.45, 0, 0, 0.01).look(s3h, 0.5, 0.05, 0.01).expr(s3h, 'annoyed', 0.01, 0.8);
  st.shot({ t0: s3h, env: 'hearth', envOpt: hearthOpt(), actors: ['annoy', 'innerMaya'], cam: [[s3h, 540, 1080, 1.4], [s3h, 545, 1085, 1.48, 6]] });
  annoy.set(t('A5') - 0.1, { 'arms.L': { ...CLIP_L, ty: 110, tx: 80, note: 1 } }, 0.5);    // shows her the note
  annoy.expr(w('A5', 'deadline') - 0.2, 'annoyed', 0.4, 1.1, { browR: 0.4 });
  annoy.expr(e('A5') + 0.4, 'relieved', 0.9, 0.9);                                     // relief at being heard
  annoy.set(e('A5') + 0.4, { glow: 0.6 }, 1.2);
  inner.expr(t('A5'), 'hurt', 0.5, 0.6).look(w('A5', 'deadline'), -0.45, 0.25, 0.3);
  inner.head(t('M4') - 0.1, -0.5, 0.35, 0, 0.45).head(t('M4') + 0.4, -0.5, 0.0, 0, 0.45).head(w('M4', 'He') - 0.05, -0.5, 0.3, -3, 0.5); // slow nod
  inner.look(w('M4', 'He'), -0.35, 0.5, 0.3);

  // N9: wide — Anger back at the table, calm
  const s3i = t('N9') - 0.35;
  anger.set(s3i, { x: 700, y: 1335, pose: 'sit', hideLegs: false, facing: 0.1, flame: 0, 'arms.L': { tx: 70, ty: 200, hand: 'flat', view: 'back', bend: -1, rotAbs: 10 }, 'arms.R': { tx: -70, ty: 200, hand: 'flat', view: 'back', bend: 1, rotAbs: 170 }, armOrder: 'LR' }, 0.01);
  anger.head(s3i, 0.35, 0.2, 0, 0.01).look(s3i, 0.4, 0.2, 0.01).expr(s3i, 'relieved', 0.01, 0.5);
  inner.set(s3i, { x: 960, y: 1440, pose: 'sit', hideLegs: false, s: 0.95, facing: -0.3, 'arms.L': { tx: 60, ty: 210, hand: 'flat', view: 'back', bend: -1, rotAbs: 0, foreK: 0.65 }, 'arms.R': { tx: -50, ty: 215, hand: 'flat', view: 'back', bend: 1, rotAbs: 175, foreK: 0.65 } }, 0.01);
  inner.head(s3i, -0.3, 0.1, 0, 0.01).look(s3i, -0.4, 0.1, 0.01).expr(s3i, 'soft', 0.01);
  fear.set(s3i, { x: 1300, y: 1620, facing: -0.4, glow: 1, 'arms.L': { tx: 60, ty: 150, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -60, ty: 150, hand: 'fist', view: 'back', bend: 1 } }, 0.01).head(s3i, -0.4, 0.1, 0, 0.01).look(s3i, -0.5, 0.1, 0.01).expr(s3i, 'worried', 0.01, 0.6);
  st.shot({ t0: s3i, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'annoy', 'anger', 'innerMaya', 'fear'], armsFront: ['anger', 'innerMaya'],
    cam: [[s3i, 705, 1100, 0.79], [s3i, 715, 1130, 0.86, e('N9') - s3i + 1]] });
  anger.blink(w('N9', 'shout'));

  // ================================================================ SCENE 4 — the boundary (kitchen)
  const b0 = t('M5') - 1.3;
  st.scene('kitchen2', b0, t('F1') - 0.35, 'tender, honest');
  st.amb('room_tone', b0, t('F1') - 0.35, 0.6);
  st.amb('clock_tick', b0, t('F1') - 0.35, 0.35);
  maya.set(b0, { head: { yaw: 0.35, pitch: 0.05, tilt: 0 } }, 0.01).look(b0, 0.1, 0.5, 0.01).expr(b0, 'hurt', 0.01, 0.7);
  maya.look(b0 + 0.6, 0.55, 0.0, 0.3).head(b0 + 0.5, 0.45, 0.0, 0, 0.6);
  maya.expr(t('M5'), 'determined', 0.6, 0.8, { browIn: 0.35 });
  eli.set(b0, { 'arms.R': { tx: -50, ty: 250, hand: 'relax', bend: 1, hideHand: true } }, 0.01);
  eli.look(b0, 0.3, 0.5, 0.01).head(b0, 0.0, 0.25, 0, 0.01).expr(b0, 'avoid', 0.01);
  st.shot({ t0: b0, env: 'kitchen', envOpt: kitchenOpt, actors: ['maya'], armsFront: ['maya'], trans: { type: 'dissolve', dur: 0.7 },
    cam: [[b0, 470, 1235, 2.5], [b0, 470, 1228, 2.62, e('M5') - b0]], front: (ctx, T) => P.mug(ctx, MUG[0], MUG[1], 1, null, { t: T }) });

  const s4b = t('E4') - 0.45;
  eli.look(s4b + 0.05, -0.6, 0.05, 0.2).head(s4b, -0.4, 0.05, 0, 0.4);       // caught: looks at her
  eli.expr(s4b, 'surprised', 0.3, 0.4);
  eli.look(w('E4', 'know') + 0.05, 0.4, 0.35, 0.25).head(w('E4', 'know'), 0.05, 0.2, -2, 0.6);  // looks away
  eli.set(w('E4', 'know'), { shrug: 0.6 }, 0.25).set(w('E4', 'know') + 0.4, { shrug: 0 }, 0.5);
  eli.expr(w('E4', 'Because'), 'guilty', 0.5, 0.8);
  eli.look(w('E4', 'month') - 0.1, -0.45, 0.1, 0.3);
  st.shot({ t0: s4b, env: 'kitchen', envOpt: kitchenOpt, actors: ['eli'], cam: [[s4b, 1240, 925, 2.3], [s4b, 1240, 930, 2.4, 3]] });

  // M6–M8: she sets the mug down, keeps her hands near it
  const s4c = t('M6') - 0.55;
  const MUG2 = [470, 1374];
  const mugSet = s4c + 0.2;
  const muggy = (T) => (T < mugSet + 0.45 ? [lerp(MUG[0], MUG2[0], smooth((T - mugSet) / 0.45)), MUG[1] - 8 * Math.sin(clamp((T - mugSet) / 0.45, 0, 1) * Math.PI)] : MUG2);
  maya.set(mugSet, { 'arms.L': { tx: 95, ty: 196, hand: 'cup', view: 'back', rotAbs: -8, thumb: -1, bend: -1, locked: true, foreK: 0.62, follow: 0.45 }, 'arms.R': { tx: -2, ty: 196, hand: 'cup', view: 'back', rotAbs: 188, thumb: 1, bend: 1, locked: true, foreK: 0.62 } }, 0.45);
  maya.set(mugSet + 0.7, { 'arms.L': { tx: 70, ty: 205, hand: 'flat', view: 'back', rotAbs: -5, bend: -1, foreK: 0.62 }, 'arms.R': { tx: 10, ty: 200, hand: 'soft', view: 'back', rotAbs: 175, thumb: 1, bend: 1, foreK: 0.62 } }, 0.6);
  st.sfx(mugSet + 0.42, 'mug_set', 0.8);
  maya.look(s4c, 0.0, 0.7, 0.3).head(s4c, 0.25, 0.3, 0, 0.5);
  maya.look(t('M6') + 0.05, 0.55, 0.0, 0.3).head(t('M6'), 0.45, 0.0, 2, 0.5).expr(t('M6'), 'soft', 0.5, 0.9);
  maya.expr(t('M7'), 'determined', 0.4, 0.9, { browIn: 0.25 });
  maya.expr(t('M8'), 'tearful', 0.8, 0.85);
  maya.look(w('M8', 'miss') - 0.2, 0.35, 0.3, 0.35);                               // eyes drop on "miss her"
  st.shot({ t0: s4c, env: 'kitchen', envOpt: kitchenOpt, actors: ['maya'], armsFront: ['maya'], cam: [[s4c, 480, 1255, 2.4], [s4c, 480, 1235, 2.7, e('M8') - s4c]],
    front: (ctx, T) => { const [mx, my] = muggy(T); P.mug(ctx, mx, my, 1, null, { t: T }); } });

  // E5–E6: Eli's long pause, then the truth
  const s4d = t('E5') - 2.0;
  eli.look(s4d + 0.2, -0.5, 0.05, 0.3).head(s4d, -0.35, 0.05, 0, 0.6).expr(s4d, 'hurt', 1.0, 0.6, { press: 0.6 });
  eli.set(s4d + 0.4, { 'arms.R': { tx: -55, ty: -95, hand: 'soft', view: 'back', bend: 1, behind: true, rotAbs: -150 } }, 0.7);
  eli.set(t('E5') + 0.4, { 'arms.R': { tx: -40, ty: 250, hand: 'relax', bend: 1 } }, 0.8);
  eli.look(s4d + 1.0, 0.1, 0.65, 0.4).head(s4d + 0.9, -0.1, 0.4, -3, 0.9);           // looks down
  eli.expr(s4d + 1.0, 'tearful', 1.0, 0.75);
  eli.set(s4d + 1.2, { shrug: 0.3 }, 0.6).set(t('E5'), { shrug: 0 }, 0.8);
  eli.look(w('E5', 'Mae') - 0.2, -0.45, 0.15, 0.3).head(w('E5', 'Mae') - 0.3, -0.35, 0.1, 0, 0.5);  // looks up at her on "Mae"
  eli.look(t('E6') + 0.2, 0.0, 0.5, 0.4).head(t('E6'), -0.1, 0.35, -2, 0.7);
  eli.expr(t('E6'), 'cry', 1.0, 0.8);
  eli.tear(lerp(t('E6'), e('E6'), 0.45), 1, 3.6);
  st.sfx(e('E6') + 0.15, 'sniff', 0.5);
  st.shot({ t0: s4d, env: 'kitchen', envOpt: kitchenOpt, actors: ['eli'], cam: [[s4d, 1240, 915, 2.4], [s4d, 1240, 905, 2.9, e('E6') - s4d + 0.4]] });

  // M9: her face softens
  const s4e = t('M9') - 1.25;
  maya.expr(s4e, 'surprised', 0.4, 0.3).expr(s4e + 0.5, 'tender', 1.0, 1.1);
  maya.look(s4e, 0.55, 0.0, 0.3).head(s4e + 0.2, 0.45, 0.0, 4, 1.0);
  st.shot({ t0: s4e, env: 'kitchen', envOpt: kitchenOpt, actors: ['maya'], armsFront: ['maya'], cam: [[s4e, 480, 1170, 2.75], [s4e, 480, 1160, 2.9, 3]],
    front: (ctx, T) => P.mug(ctx, MUG2[0], MUG2[1], 1, null, { t: T }) });

  // N10: Eli crosses to the table and sits; insert — the inner door opens a crack
  const s4f = t('N10') - 1.0;
  eli.expr(s4f, 'relieved', 0.8, 0.8).look(s4f, -0.5, 0.2).head(s4f, -0.4, 0.1, 0);
  eli.set(s4f + 0.2, { facing: -0.6, lean: 0 }, 0.4);
  eli.walk(s4f + 0.4, s4f + 2.4, 905, 1600, 32);
  eli.set(s4f + 0.4, { s: 0.92 }, 2.0);
  eli.set(s4f + 2.45, { pose: 'sit', hideLegs: false, y: 1440, facing: -0.45 }, 0.35);
  eli.set(s4f + 2.5, { 'arms.L': { tx: 60, ty: 200, hand: 'soft', view: 'back', bend: -1, rotAbs: -10 }, 'arms.R': { tx: -40, ty: 205, hand: 'flat', view: 'back', bend: 1, rotAbs: 190 } }, 0.6);
  st.sfx(s4f + 2.3, 'chair_scrape', 0.7);
  st.sfx(s4f + 0.5, 'footsteps_wood', 0.5);
  maya.look(s4f + 0.5, 0.6, -0.05).head(s4f + 0.5, 0.45, 0, 0).expr(s4f + 1, 'soft', 0.8);
  maya.look(s4f + 2.4, 0.5, 0.05, 0.4);
  st.shot({ t0: s4f, env: 'kitchen', envOpt: kitchenOpt, actors: ['eli', 'maya'], armsFront: ['maya', 'eli'], cam: [[s4f, 830, 1210, 0.92], [s4f, 700, 1230, 1.2, e('N10') - s4f]],
    front: (ctx, T) => P.mug(ctx, MUG2[0], MUG2[1], 1, null, { t: T }) });
  const s4g = w('N10', 'open') - 0.3;
  doorTrack.push([s4g + 0.1, 1.6, 0.55]);
  st.sfx(s4g + 0.1, 'door_creak', 0.35);
  st.shot({ t0: s4g, env: 'hearth', envOpt: hearthOpt(), actors: [], cam: [[s4g, 230, 1170, 1.7], [s4g, 230, 1180, 1.85, 2]], trans: { type: 'dissolve', dur: 0.35 } });
  const s4h = we('N10', 'one') + 0.1;

  // ================================================================ SCENE 5 — Fear
  const f0 = t('E7') - 2.4;
  const buzzT = f0 + 0.35;
  st.sfx(buzzT, 'phone_buzz', 0.9);
  const PH = [690, 1376];
  eli.look(buzzT + 0.15, -0.15, 0.7, 0.2).head(buzzT + 0.1, -0.2, 0.35, 0, 0.5).expr(buzzT, 'neutral', 0.5);
  maya.look(buzzT + 0.3, 0.3, 0.6, 0.3);
  eli.set(buzzT + 0.6, { 'arms.R': { ...reach('eli', buzzT + 0.6, 1, PH[0] + 20, PH[1] - 10), hand: 'flat', view: 'back', bend: 1, rotAbs: 200 } }, 0.5);
  eli.expr(t('E7'), 'sad', 0.6, 0.7);
  eli.look(w('E7', 'Saturday') - 0.15, -0.6, 0.0, 0.3).head(w('E7', 'Saturday') - 0.25, -0.45, 0.05, 0, 0.5);
  maya.look(w('E7', 'Saturday'), 0.6, -0.02, 0.25).expr(w('E7', 'Saturday'), 'worried', 0.4, 0.8);
  st.shot({ t0: s4h, env: 'kitchen', envOpt: kitchenOpt, actors: ['eli', 'maya'], armsFront: ['maya', 'eli'], cam: [[s4h, 690, 1225, 1.45], [s4h, 690, 1220, 1.65, f0 - s4h + 3.2]], trans: { type: 'dissolve', dur: 0.35 },
    front: (ctx, T) => {
      P.mug(ctx, MUG2[0], MUG2[1], 1, null, { t: T });
      const bz = T >= buzzT && T < buzzT + 1.4 ? (Math.sin((T - buzzT) * Math.PI / 0.35) > 0 ? 1 : 0) * (T - buzzT < 1.1 ? 1 : 0) : 0;
      P.phone(ctx, PH[0], PH[1], 0.5, bz, T, T > buzzT ? ['Realtor', 'Walkthrough Sat 10am.', 'Please have the house cleared.'] : null);
    } });

  // F1: Fear panics
  const s5b = t('F1') - 0.35;
  fear.set(s5b, { x: 1170, y: 1620, facing: -0.25, lean: 4, glow: 1 }, 0.01).head(s5b, -0.2, 0.1, 0, 0.01).look(s5b, -0.2, 0.05, 0.01);
  fear.set(s5b + 0.1, { y: 1570, glow: 1.9 }, 0.15).set(s5b + 0.3, { y: 1620 }, 0.3);
  fear.set(s5b + 0.1, { 'arms.L': { tx: 30, ty: -150, hand: 'grip', view: 'back', bend: 1, rotAbs: -55 }, 'arms.R': { tx: -30, ty: -150, hand: 'grip', view: 'back', bend: -1, rotAbs: -125 } }, 0.25); // hands to his temples, elbows out
  fear.expr(s5b + 0.05, 'fear', 0.15, 1.3);
  const nos = ['No', 'no', 'no'];
  [[w('F1', 'No', 0), -0.35], [w('F1', 'no', 1), 0.35], [w('F1', 'no', 2), -0.35], [w('F1', 'no', 2) + 0.25, 0.1]].forEach(([tt, yw]) => fear.head(tt - 0.05, yw, 0.05, 0, 0.18));
  fear.set(w('F1', "can't") - 0.2, { 'arms.L': { tx: 60, ty: 90, hand: 'open', view: 'palm', bend: -1 }, 'arms.R': { tx: -60, ty: 90, hand: 'open', view: 'palm', bend: 1 } }, 0.3);
  fear.look(w('F1', "can't"), 0.0, 0.0, 0.2).head(w('F1', "can't"), 0.0, 0, 0, 0.3);
  st.shot({ t0: s5b, env: 'hearth', envOpt: hearthOpt(), actors: ['fear'], cam: [[s5b, 1170, 900, 1.9], [s5b, 1170, 880, 2.05, 3.2]], handheld: 2 });
  st.scene('hearth2', s5b, t('NA1') - 2.4, 'fear, then tenderness with sadness');
  st.amb('fire_crackle', s5b, t('S4') + 3, 0.55);

  // N11–N13: visions — the tiger, the roller coaster
  const s5c = t('N11') - 0.25;
  fear.set(s5c, { x: 1150, glow: 1.3, 'arms.L': { tx: 70, ty: 160, hand: 'fist', view: 'back', bend: -1 }, 'arms.R': { tx: -70, ty: 160, hand: 'fist', view: 'back', bend: 1 } }, 0.4);
  fear.expr(s5c, 'worried', 0.5, 1.1).head(s5c, 0.4, -0.25, 0, 0.6).look(s5c, 0.5, -0.55, 0.3);
  vis.push([t('N12') - 0.3, e('N12') + 0.7, (T) => ({ kind: 'tiger', p: clamp((T - t('N12') + 0.1) / (e('N12') - t('N12') + 0.4), 0, 1), alpha: smooth((T - t('N12') + 0.3) / 0.3) * (1 - smooth((T - e('N12') - 0.3) / 0.4)) })]);
  vis.push([t('N13') - 0.2, e('N13') + 0.6, (T) => ({ kind: 'coaster', p: clamp((T - t('N13')) / (e('N13') - t('N13')), 0, 1), alpha: smooth((T - t('N13') + 0.2) / 0.3) * (1 - smooth((T - e('N13') - 0.2) / 0.4)) })]);
  fear.set(w('N12', 'jumping') - 0.05, { lean: -10, 'arms.L': { tx: 60, ty: 20, hand: 'open', view: 'palm', bend: -1 }, 'arms.R': { tx: -50, ty: 30, hand: 'open', view: 'palm', bend: 1 } }, 0.2);
  fear.expr(w('N12', 'jumping') - 0.05, 'fear', 0.15, 1.3);
  fear.set(t('N13') + 0.3, { lean: 2, 'arms.L': { tx: 60, ty: 110, hand: 'grip', view: 'back', bend: -1 }, 'arms.R': { tx: -60, ty: 110, hand: 'grip', view: 'back', bend: 1 } }, 0.6);
  fear.head(t('N13'), 0.35, -0.45, 0, 1.5).look(t('N13'), 0.4, -0.75, 1.5);
  st.shot({ t0: s5c, env: 'hearth', envOpt: hearthOpt(), actors: ['fear'], cam: [[s5c, 1380, 900, 1.3], [t('N12') - 0.4, 1420, 820, 1.3, 1.0], [t('N13'), 1450, 760, 1.35, 3]], over: drawVisions });

  // N14: Fear's worry looks for who is unprotected
  const s5d = t('N14') - 0.25;
  fear.set(s5d, { lean: 4, 'arms.L': { tx: 70, ty: 150, hand: 'grip', view: 'back', bend: -1 }, 'arms.R': { tx: -40, ty: 160, hand: 'grip', view: 'back', bend: 1 } }, 0.5);
  fear.expr(s5d, 'worried', 0.5, 1).head(s5d, -0.4, 0.1, 0, 0.6).look(s5d, -0.7, 0.15, 0.3);
  fear.look(w('N14', 'emotional') - 0.2, -0.8, 0.3, 0.4).head(w('N14', 'emotional') - 0.3, -0.6, 0.2, -4, 0.7);
  for (let k = 0; k < 9; k++) {   // wringing hands
    const tk = s5d + 0.4 + k * 0.5, sw = k % 2 ? 1 : -1;
    fear.set(tk, { 'arms.L': { tx: 70 + sw * 10, ty: 150 - sw * 8, hand: 'grip', view: 'back', bend: -1 }, 'arms.R': { tx: -40 + sw * 10, ty: 160 + sw * 8, hand: 'grip', view: 'back', bend: 1 } }, 0.45);
  }
  inner.set(s5d, { pose: 'stand', hideLegs: false, x: 930, y: 1630, s: 0.95, facing: 0.55, 'arms.L': { tx: -14, ty: 300, hand: 'relax' }, 'arms.R': { tx: 14, ty: 300, hand: 'relax' } }, 0.01);
  inner.head(s5d, 0.5, 0, 0, 0.01).look(s5d, 0.55, 0, 0.01).expr(s5d, 'listening', 0.01);
  st.shot({ t0: s5d, env: 'hearth', envOpt: hearthOpt(), actors: ['fear'], cam: [[s5d, 1160, 930, 1.9], [s5d, 1160, 940, 2.0, 5]] });

  // M10: Maya approaches — "Fear... who are you protecting?"
  const s5e = t('M10') - 0.6;
  fear.set(s5e, { x: 1190, facing: -0.55 }, 0.01).head(s5e, -0.55, 0.05, 0, 0.01).look(s5e, -0.55, 0.05, 0.01);
  inner.set(t('M10'), { 'arms.R': { tx: 60, ty: 200, hand: 'open', view: 'palm', bend: 1, rotAbs: -20 } }, 0.6);
  inner.expr(t('M10'), 'tender', 0.6, 0.9);
  st.shot({ t0: s5e, env: 'hearth', envOpt: hearthOpt(), actors: ['innerMaya', 'fear'], cam: [[s5e, 1060, 1050, 1.5], [s5e, 1060, 1055, 1.58, 3]] });

  // F2–F3: "Her." (glance to the corner) — insert of Sadness alone — "Nobody's sat with her since the funeral."
  const s5f = t('F2') - 0.45;
  fear.expr(s5f, 'sad', 0.6, 1.0).set(s5f, { glow: 0.9 }, 0.8);
  fear.look(s5f + 0.25, -1.0, 0.3, 0.35).head(s5f + 0.2, -0.75, 0.15, -3, 0.6);       // glances toward the corner
  fear.look(e('F2') + 0.1, -0.55, 0.05, 0.3).head(e('F2'), -0.55, 0.05, 0, 0.5);       // back to Maya
  st.shot({ t0: s5f, env: 'hearth', envOpt: hearthOpt(), actors: ['fear'], cam: [[s5f, 1190, 890, 2.3], [s5f, 1190, 895, 2.4, 2]] });
  const s5g = e('F2') + 0.15;
  st.shot({ t0: s5g, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness'], cam: [[s5g, 190, 1420, 2.3], [s5g, 190, 1430, 2.45, 1.4]], trans: { type: 'dissolve', dur: 0.25 } });
  sad.blink(s5g + 0.6);
  const s5h = t('F3') - 0.2;
  fear.expr(t('F3'), 'sadDeep', 0.7, 0.8);
  fear.look(w('F3', 'funeral') - 0.15, -0.45, 0.4, 0.4);
  st.shot({ t0: s5h, env: 'hearth', envOpt: hearthOpt(), actors: ['fear'], cam: [[s5h, 1190, 890, 2.4], [s5h, 1190, 895, 2.55, 2.5]], trans: { type: 'dissolve', dur: 0.25 } });

  // F4: "...pour out like water" — vision over Sadness's corner
  const s5i = t('F4') - 0.3;
  fear.look(t('F4') + 0.1, -0.55, 0.05, 0.3).expr(t('F4'), 'worried', 0.5, 1.1);
  fear.set(t('F4'), { 'arms.L': { tx: 80, ty: 120, hand: 'soft', view: 'palm', bend: -1 }, 'arms.R': { tx: -40, ty: 170, hand: 'grip', view: 'back', bend: 1 } }, 0.5);
  st.shot({ t0: s5i, env: 'hearth', envOpt: hearthOpt(), actors: ['innerMaya', 'fear'], cam: [[s5i, 1060, 1050, 1.6], [s5i, 1070, 1040, 1.7, 2.5]] });
  const s5j = w('F4', 'pour') - 0.35;
  vis.push([s5j, e('F4') + 1.0, (T) => ({ kind: 'water', p: clamp((T - s5j) / 2.4, 0, 1), alpha: smooth((T - s5j) / 0.3) * (1 - smooth((T - e('F4') - 0.4) / 0.5)), x: 120, y: 1470, scale: 1.0 })]);
  st.sfx(w('F4', 'pour'), 'water_pour', 0.6);
  sad.look(s5j + 0.3, 0.1, 0.85, 0.5).expr(s5j, 'sadDeep', 0.8, 0.9);
  st.shot({ t0: s5j, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness'], cam: [[s5j, 220, 1420, 1.55], [s5j, 220, 1440, 1.75, 2.6]], over: drawVisions, trans: { type: 'dissolve', dur: 0.3 } });

  // N15 / M11 / F5 — the plan changes
  const s5k = t('N15') - 0.45;
  inner.look(s5k, 0.55, 0.0, 0.01).head(s5k, 0.5, 0, 0, 0.01).expr(s5k, 'tender', 0.01, 0.8);
  inner.look(w('N15', 'other') - 0.1, -0.9, 0.25, 0.4).head(w('N15', 'other') - 0.2, -0.3, 0.1, 0, 0.8);  // looks over to the corner
  inner.look(w('N15', 'before') - 0.1, 0.55, 0.0, 0.35).head(w('N15', 'before') - 0.2, 0.5, 0, 0, 0.6);
  fear.look(s5k, -0.55, 0.05, 0.01).head(s5k, -0.55, 0.05, 0, 0.01).expr(s5k, 'worried', 0.01, 0.9);
  st.shot({ t0: s5k, env: 'hearth', envOpt: hearthOpt(), actors: ['fear', 'innerMaya'], cam: [[s5k, 1060, 1060, 1.45], [s5k, 1060, 1050, 1.6, e('F5') - s5k]] });
  inner.expr(t('M11'), 'warm', 0.5, 0.9);
  const touchT = w('M11', 'sit') - 0.5;
  inner.set(touchT, { 'arms.R': { ...reach('innerMaya', touchT, 1, ...(() => { const sw = shoulderWorld('fear', touchT, -1); return [sw[0] + 6, sw[1] + 50]; })()), hand: 'soft', view: 'back', bend: -1, rotAbs: 10 } }, 0.6);
  fear.set(t('F5') - 0.6, { glow: 0.55, shrug: -0.3, lean: 0, 'arms.L': { tx: -14, ty: 320, hand: 'relax' }, 'arms.R': { tx: 14, ty: 320, hand: 'relax' } }, 0.9);
  fear.expr(t('F5') - 0.5, 'relieved', 0.8, 1.1, { smile: 0.3 });
  fear.blink(t('F5') - 0.3);

  // ================================================================ SCENE 6 — Sadness
  const s6a = t('S1') - 3.6;
  cornerKeys.push([s6a + 0.5, 3.0, 0.55]);
  inner.set(s6a, { 'arms.R': { tx: 14, ty: 300, hand: 'relax' } }, 0.5);
  inner.set(s6a + 0.3, { facing: -0.6 }, 0.4).head(s6a + 0.3, -0.6, 0.1, 0, 0.5).look(s6a + 0.3, -0.6, 0.2);
  inner.walk(s6a + 0.6, s6a + 2.7, 440, 1715, 34);
  st.sfx(s6a + 0.7, 'footsteps_wood', 0.4);
  inner.set(s6a + 2.62, { pose: 'floorCross', y: 1722, x: 430, s: 0.92, facing: -0.4, 'arms.L': { tx: -50, ty: 212, hand: 'flat', view: 'back', bend: -1, rotAbs: 100, foreK: 0.8 }, 'arms.R': { tx: 32, ty: 212, hand: 'flat', view: 'back', bend: 1, rotAbs: 80, foreK: 0.8 } }, 0.01);
  st.sfx(s6a + 2.8, 'cloth_rustle', 0.5);
  inner.expr(s6a + 2.66, 'tender', 0.8, 0.8).head(s6a + 2.66, -0.78, 0.2, -4, 0.01).look(s6a + 2.66, -0.8, 0.35, 0.01);
  sad.expr(s6a, 'sadDeep', 0.6, 0.9).look(s6a, 0.0, 0.85, 0.4).head(s6a, 0.15, 0.55, -6, 0.6);
  sad.look(s6a + 2.0, 0.5, 0.5, 0.3);                                                  // notices her, then looks away
  sad.look(s6a + 2.8, 0.05, 0.85, 0.4);
  st.shot({ t0: s6a, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'innerMaya'], cam: [[s6a, 640, 1260, 0.95], [s6a + 0.4, 520, 1300, 1.08, 2.4]] });
  st.shot({ t0: s6a + 2.65, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'innerMaya'], cam: [[s6a + 2.65, 320, 1430, 1.7], [s6a + 2.65, 320, 1425, 1.82, 4]] });
  sad.expr(t('S1'), 'sadDeep', 0.5, 1.0);
  sad.look(w('S1', 'heavy') - 0.1, 0.25, 0.75, 0.3);

  // M12–M13
  const s6b = t('M12') - 0.45;
  inner.expr(s6b, 'tender', 0.5, 1.0);
  inner.head(w('M12', 'is'), -0.78, 0.25, -6, 0.6);
  inner.look(t('M13'), -0.8, 0.4, 0.3);
  st.shot({ t0: s6b, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'innerMaya'], cam: [[s6b, 420, 1400, 2.4], [s6b, 420, 1395, 2.55, e('M13') - s6b]] });

  // S2: first eye contact, then the memory of Nana's hands
  const s6c = t('S2') - 0.5;
  sad.head(s6c + 0.2, 0.45, 0.05, 2, 1.2).look(s6c + 0.4, 0.7, -0.1, 0.8);              // slowly looks up at Maya
  sad.expr(s6c + 0.3, 'tearful', 1.2, 1.0);
  st.shot({ t0: s6c, env: 'hearth', envOpt: hearthOpt(), actors: ['innerMaya', 'sadness'], cam: [[s6c, 255, 1445, 2.3], [s6c, 255, 1440, 2.42, 3]] });
  const s6h = w('S2', 'I', 1) - 0.25;
  st.shot({ t0: s6h, env: 'hospital', envOpt: { chairEmpty: true }, actors: [], cam: [[s6h, 640, 1230, 2.0], [s6h, 640, 1225, 2.2, 3]], trans: { type: 'dissolve', dur: 0.5 }, grade: { color: '#8aa0c8', alpha: 0.25, mode: 'soft-light' },
    over: (ctx, T) => P.handsCloseup(ctx, st.cast, 640, 1215, 1.05, T, 1, { keyDir: -1.2, keyColor: '#ffd9a0', keyAmt: 0.6, shadowColor: '#202a40', shadowAmt: 0.4, rimAmt: 0.3, rimDir: -2.5, rimColor: '#a8c0e8', ambient: '#c8d4ec', ambientAmt: 0.2 }) });
  const s6d = e('S2') + 0.25;
  sad.expr(t('S3'), 'cry', 0.8, 0.8).tear(lerp(t('S3'), e('S3'), 0.5), 1, 3.4);
  st.shot({ t0: s6d, env: 'hearth', envOpt: hearthOpt(), actors: ['innerMaya', 'sadness'], cam: [[s6d, 255, 1445, 2.4], [s6d, 255, 1440, 2.5, 3]], trans: { type: 'dissolve', dur: 0.4 } });

  // M14–M15
  const s6e = t('M14') - 0.5;
  inner.expr(s6e, 'tearful', 0.8, 0.9);
  inner.look(s6e, -0.8, 0.3, 0.3).head(s6e, -0.78, 0.2, -5, 0.6);
  inner.head(t('M15') - 0.1, -0.75, 0.1, -7, 0.8).expr(t('M15'), 'tender', 0.6, 1.0, { smile: 0.3, glisten: 0.9 });
  st.shot({ t0: s6e, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'innerMaya'], cam: [[s6e, 420, 1395, 2.6], [s6e, 420, 1390, 2.8, 3.5]] });

  // NA1: the memory — Nana and little Maya baking bread
  const m0 = t('NA1') - 2.4;
  st.scene('memory1', m0, e('NA1') + 0.8, 'warm golden memory');
  st.scene('hearth3', e('NA1') + 0.8, t('S4') - 0.5, 'tender comfort');
  st.amb('room_tone', m0, e('NA1') + 0.8, 0.4);
  const memOpt = {};
  nana.set(m0, { x: 700, y: 1600, s: 1.06 }, 0.01);
  kid.set(m0, { x: 430, y: 1560 }, 0.01);
  const DOUGH = [620, 1395];
  nana.set(m0, { 'arms.L': { ...reach('nana', m0, -1, DOUGH[0] - 40, DOUGH[1] - 20), hand: 'flat', view: 'back', bend: -1, rotAbs: 20, locked: true }, 'arms.R': { ...reach('nana', m0, 1, DOUGH[0] + 30, DOUGH[1] - 25), hand: 'flat', view: 'back', bend: 1, rotAbs: 160, locked: true } }, 0.01);
  nana.expr(m0, 'warm', 0.01, 1);
  kid.set(m0, { 'arms.L': { ...reach('youngMaya', m0, -1, DOUGH[0] - 70, DOUGH[1] - 30) }, 'arms.R': { ...reach('youngMaya', m0, 1, DOUGH[0] - 30, DOUGH[1] - 40), hand: 'flat', view: 'back', bend: 1, rotAbs: 30 } }, 0.01);
  kid.expr(m0, 'smile', 0.01, 1);
  // little Maya pats the dough too fast
  for (let k = 0; k < 6; k++) {
    const tk = m0 + 0.4 + k * 0.32;
    kid.set(tk, { 'arms.R': { ...reach('youngMaya', m0, 1, DOUGH[0] - 30, DOUGH[1] - 80), hand: 'flat', view: 'back', bend: 1, rotAbs: 30 } }, 0.14);
    kid.set(tk + 0.16, { 'arms.R': { ...reach('youngMaya', m0, 1, DOUGH[0] - 30, DOUGH[1] - 30), hand: 'flat', view: 'back', bend: 1, rotAbs: 30 } }, 0.14);
  }
  nana.look(m0 + 0.6, -0.5, 0.45, 0.3).head(m0 + 0.6, -0.45, 0.25, -6, 0.6);
  nana.expr(t('NA1') - 0.3, 'smile', 0.6, 0.85);
  // Nana rests her hand over the girl's hand
  nana.set(t('NA1') + 0.2, { 'arms.L': { ...reach('nana', t('NA1'), -1, DOUGH[0] - 40, DOUGH[1] - 40), hand: 'soft', view: 'back', bend: -1, rotAbs: 200, locked: true } }, 0.8);
  kid.look(t('NA1') + 0.3, 0.6, -0.4, 0.3).head(t('NA1') + 0.2, 0.55, -0.2, 6, 0.6).expr(t('NA1') + 0.4, 'smallSmile', 0.6);
  // then offers a warm piece of bread, palm up
  const offerT = w('NA1', 'Bread') - 0.1;
  nana.set(offerT, { 'arms.R': { tx: -100, ty: 190, hand: { base: 'soft', curl: [0.2, 0.25, 0.3, 0.35] }, view: 'palm', bend: 1, rotAbs: 195, holding: 'bread', thumb: -1, locked: true } }, 0.8);
  kid.look(offerT + 0.6, 0.4, 0.3, 0.3).expr(offerT + 0.7, 'smile', 0.6, 1.1);
  st.label(m0 + 0.2, 'nana', { dur: 3.4 });
  st.label(m0 + 0.2, 'youngMaya', { dur: 3.6, text: 'Maya, age 7', emoji: '' });
  st.shot({ t0: m0, env: 'memory', envOpt: memOpt, actors: ['nana', 'youngMaya'], armsFront: ['nana', 'youngMaya'], cam: [[m0, 600, 1150, 1.25], [m0, 610, 1130, 1.45, e('NA1') - m0 + 1]], trans: { type: 'dissolve', dur: 0.7 },
    grade: { color: '#ffcf8a', alpha: 0.25, mode: 'soft-light' }, vignette: 0.55 });

  // N16–N18: back in the corner — Sadness rests her head on Maya's shoulder
  const s6f = t('N16') - 1.1;
  cornerKeys.push([s6f, 2.5, 1.0]);
  sad.set(s6f + 0.6, { lean: 6, x: 225, head: { yaw: 0.55, pitch: 0.15, tilt: 16 } }, 1.4);
  sad.look(s6f + 0.6, 0.3, 0.4, 0.5).expr(s6f + 0.6, 'tender', 1.2, 0.9);
  sad.blink(s6f + 1.2);
  inner.head(s6f + 0.8, -0.5, 0.2, -10, 1.2).look(s6f + 0.8, -0.5, 0.55, 0.5).expr(s6f + 0.8, 'tender', 1.2, 1.0, { smile: 0.35 });
  const SADH = (T) => { const a = st.actors.sadness.sample(T); return [a.x + 20, a.y - 150]; };
  inner.set(s6f + 0.9, { 'arms.L': { ...reach('innerMaya', s6f + 0.9, -1, ...SADH(s6f + 2.0)), hand: 'soft', view: 'back', bend: 1, rotAbs: 170, locked: true, foreK: 0.85 } }, 1.0);
  sad.expr(t('N18'), 'tender', 1.0, 1.0, { smile: 0.25 });
  st.shot({ t0: s6f, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'innerMaya'], cam: [[s6f, 330, 1420, 1.8], [s6f, 330, 1400, 2.1, e('N18') - s6f + 1]], trans: { type: 'dissolve', dur: 0.6 } });

  // ================================================================ SCENE 7 — reflection
  const r0 = t('S4') - 0.5;
  st.scene('reflect', r0, e('R12') + 0.6, 'reflection, slow build to hope');
  st.amb('fire_crackle', r0, e('R12') + 0.6, 0.28);
  sad.head(r0, 0.55, -0.1, 8, 0.8).look(r0 + 0.1, 0.65, -0.35, 0.4);                   // looks up at Maya
  sad.expr(t('S4'), 'tender', 0.6, 0.8, { browIn: 0.5 });
  st.shot({ t0: r0, env: 'hearth', envOpt: hearthOpt(), actors: ['innerMaya', 'sadness'], cam: [[r0, 255, 1445, 2.35], [r0, 255, 1440, 2.45, 3]] });
  const s7b = t('R1') - 1.3;
  inner.look(s7b, 0.6, -0.2, 0.6).head(s7b, 0.1, -0.1, -6, 1.2).expr(s7b, 'tender', 1.2, 0.7);         // gazes off, thinking
  inner.look(w('R1', 'sadness') - 0.2, -0.55, 0.5, 0.5).head(w('R1', 'sadness') - 0.3, -0.5, 0.2, -9, 0.9);
  st.title(t('R1') - 1.0, e('R1') + 1.4, [{ text: 'What does grief mean for you?', font: 'italic 54px InterItalic', color: '#fff4e2' }], 300);
  st.shot({ t0: s7b, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'innerMaya'], cam: [[s7b, 330, 1420, 2.0], [s7b, 330, 1400, 2.25, 3.5]] });
  // R2 — memory: the bread, given and received
  const s7c = t('R2') - 0.3;
  nana.set(s7c, { 'arms.R': { tx: -110, ty: 175, hand: { base: 'soft', curl: [0.2, 0.25, 0.3, 0.35] }, view: 'palm', bend: 1, rotAbs: 195, holding: 'bread', thumb: -1, locked: true } }, 0.01);
  nana.expr(s7c, 'smile', 0.01, 1).look(s7c, -0.5, 0.35, 0.01);
  kid.expr(s7c, 'smile', 0.01, 1.2).look(s7c, 0.45, 0.2, 0.01).head(s7c, 0.5, 0.0, 6, 0.01);
  kid.set(s7c + 1.5, { 'arms.R': { ...reach('youngMaya', s7c + 1.5, 1, 575, 1290), hand: 'pinch', view: 'back', bend: 1, rotAbs: -20 } }, 0.8);
  kid.look(s7c + 2.6, 0.55, -0.5, 0.3).head(s7c + 2.6, 0.6, -0.3, 8, 0.6);
  nana.look(s7c + 2.8, -0.55, 0.25, 0.3).expr(s7c + 2.8, 'smile', 0.5, 1.1);
  st.shot({ t0: s7c, env: 'memory', envOpt: memOpt, actors: ['nana', 'youngMaya'], armsFront: ['nana', 'youngMaya'], cam: [[s7c, 580, 1120, 1.5], [s7c, 600, 1100, 1.7, e('R2') - s7c]], trans: { type: 'dissolve', dur: 0.6 },
    grade: { color: '#ffcf8a', alpha: 0.25, mode: 'soft-light' }, vignette: 0.55 });
  // R3 — hospital hands
  const s7d = t('R3') - 0.35;
  st.shot({ t0: s7d, env: 'hospital', envOpt: { chairEmpty: true }, actors: [], cam: [[s7d, 640, 1230, 2.1], [s7d, 640, 1225, 2.35, 2.5]], trans: { type: 'dissolve', dur: 0.6 }, grade: { color: '#8aa0c8', alpha: 0.25, mode: 'soft-light' },
    over: (ctx, T) => P.handsCloseup(ctx, st.cast, 640, 1215, 1.05, T, 0.8, { keyDir: -1.2, keyColor: '#ffd9a0', keyAmt: 0.6, shadowColor: '#202a40', shadowAmt: 0.4, rimAmt: 0.3, rimDir: -2.5, rimColor: '#a8c0e8', ambient: '#c8d4ec', ambientAmt: 0.2 }) });
  // R4–R6 — Maya at the round window: the night city, all those lives
  const s7e = t('R4') - 0.4;
  viewKeys.push([s7e, 'night']);
  inner.set(s7e, { pose: 'stand', hideLegs: false, x: 520, y: 1560, s: 0.95, facing: 0.75, lean: 0, 'arms.L': { tx: -14, ty: 300, hand: 'relax' }, 'arms.R': { tx: 14, ty: 300, hand: 'relax' } }, 0.01);
  inner.head(s7e, 0.85, -0.2, 0, 0.01).look(s7e, 0.6, -0.3, 0.01).expr(s7e, 'tender', 0.01, 0.7);
  inner.look(w('R4', 'means'), 0.65, -0.2, 0.6).look(w('R4', 'will'), 0.6, -0.35, 0.6);
  inner.set(w('R5', 'myself') - 0.4, { 'arms.R': { tx: -80, ty: 110, hand: 'flat', view: 'back', bend: 1, rotAbs: 175 } }, 0.7);  // hand on her chest
  inner.head(w('R5', 'myself') - 0.4, 0.55, 0.3, -4, 0.8).look(w('R5', 'myself') - 0.3, 0.3, 0.7, 0.5);
  inner.expr(t('R6'), 'tender', 1.2, 0.9, { lidU: 0.55 });
  inner.blink(t('R6') - 0.2);
  st.shot({ t0: s7e, env: 'hearth', envOpt: hearthOpt(), actors: ['innerMaya'], cam: [[s7e, 640, 840, 1.25], [s7e, 620, 900, 1.6, e('R6') - s7e]], trans: { type: 'dissolve', dur: 0.5 }, vignette: 0.45 });
  // R7–R8 — who bore witness: the empty chair, the candle
  const s7h = t('R7') - 0.35;
  const candleOn = w('R8', 'meaning') - 0.2;
  st.shot({ t0: s7h, env: 'hospital', envOpt: (T) => ({ chairEmpty: true, candle: T > candleOn }), actors: [], cam: [[s7h, 1100, 1300, 1.25], [s7h, 1080, 1280, 1.5, e('R8') - s7h]], trans: { type: 'dissolve', dur: 0.5 },
    grade: { color: '#7e94bf', alpha: 0.28, mode: 'soft-light' }, vignette: 0.55 });
  // R9 — back to the two of them; Sadness nods
  const s7j = t('R9') - 0.7;
  inner.set(s7j, { pose: 'floorCross', y: 1722, x: 430, s: 0.92, facing: -0.4, 'arms.R': { tx: 32, ty: 212, hand: 'flat', view: 'back', bend: 1, rotAbs: 80, foreK: 0.8 } }, 0.01);
  inner.set(s7j, { 'arms.L': { ...reach('innerMaya', s7j, -1, ...SADH(s7j)), hand: 'soft', view: 'back', bend: 1, rotAbs: 170, locked: true, foreK: 0.85 } }, 0.01);
  inner.head(s7j, -0.5, 0.2, -10, 0.01).look(s7j, -0.5, 0.5, 0.01).expr(s7j, 'tender', 0.01, 1);
  sad.head(s7j, 0.5, -0.05, 6, 0.01).look(s7j, 0.65, -0.3, 0.01).expr(s7j, 'tender', 0.01, 1);
  sad.head(w('R9', 'does') - 0.1, 0.5, 0.3, 6, 0.4).head(w('R9', 'does') + 0.35, 0.5, -0.05, 6, 0.5);   // nod
  st.shot({ t0: s7j, env: 'hearth', envOpt: hearthOpt(), actors: ['sadness', 'innerMaya'], cam: [[s7j, 330, 1415, 2.0], [s7j, 330, 1405, 2.2, 4]], trans: { type: 'dissolve', dur: 0.5 } });
  // R10 — the photo on the mantel
  const s7k = t('R10') - 0.3;
  st.shot({ t0: s7k, env: 'hearth', envOpt: hearthOpt(), actors: [], cam: [[s7k, 1340, 905, 3.0], [s7k, 1340, 900, 3.6, e('R10') - s7k]], trans: { type: 'dissolve', dur: 0.7 },
    over: (ctx, T) => photo(ctx, T, 1340, 900) });
  // R11–R12 — the family at the window as dawn comes
  const s7l = t('R11') - 0.4;
  viewKeys.push([s7l, 'dawn']);
  const fam = (T0) => {
    inner.set(T0, { pose: 'stand', hideLegs: false, x: 690, y: 1830, s: 1.0, facing: 0.1, lean: 0, 'arms.L': { tx: -14, ty: 300, hand: 'relax' }, 'arms.R': { tx: 14, ty: 300, hand: 'relax' } }, 0.01);
    inner.head(T0, 0.05, -0.15, 0, 0.01).look(T0, 0.0, -0.3, 0.01).expr(T0, 'warm', 0.01, 0.8);
    anger.set(T0, { pose: 'stand', hideLegs: false, x: 960, y: 1860, s: 1.05, facing: -0.15, flame: 0, 'arms.L': { tx: -10, ty: 220, hand: 'relax' }, 'arms.R': { tx: 10, ty: 220, hand: 'relax' } }, 0.01);
    anger.head(T0, -0.1, -0.2, 0, 0.01).look(T0, 0, -0.35, 0.01).expr(T0, 'soft', 0.01, 0.8);
    fear.set(T0, { x: 1190, y: 1800, s: 0.97, facing: -0.2, lean: 0, glow: 0.6, 'arms.L': { tx: -14, ty: 330, hand: 'relax' }, 'arms.R': { tx: 14, ty: 330, hand: 'relax' } }, 0.01);
    fear.head(T0, -0.15, -0.2, 0, 0.01).look(T0, -0.05, -0.4, 0.01).expr(T0, 'relieved', 0.01, 0.9);
    annoy.set(T0, { x: 400, y: 1800, s: 0.97, facing: 0.25, glow: 0.6, lean: 0, 'arms.L': { tx: 50, ty: 150, hand: 'grip', view: 'back', bend: -1, holding: 'clipboard', rotAbs: -30, thumb: -1, note: 0 }, 'arms.R': { tx: 14, ty: 320, hand: 'relax' } }, 0.01);
    annoy.head(T0, 0.25, -0.2, 0, 0.01).look(T0, 0.2, -0.35, 0.01).expr(T0, 'soft', 0.01, 0.8);
    sad.set(T0, { pose: 'stand', x: 545, y: 1880, s: 1.05, lean: 0, facing: 0.2, 'arms.L': { tx: -10, ty: 210, hand: 'soft' }, 'arms.R': { tx: 10, ty: 210, hand: 'soft' } }, 0.01);
    sad.head(T0, 0.2, -0.25, 0, 0.01).look(T0, 0.1, -0.5, 0.01).expr(T0, 'tender', 0.01, 0.8);
  };
  fam(s7l);
  fear.look(s7l + 1.5, -0.6, 0.1, 0.3).look(s7l + 2.6, 0.0, -0.4, 0.3);
  annoy.look(s7l + 2.0, 0.6, 0.05, 0.3).look(s7l + 3.2, 0.2, -0.35, 0.3);
  anger.set(s7l + 2.4, { lean: -4 }, 0.8).look(s7l + 2.4, 0.5, -0.1, 0.3);
  sad.look(s7l + 3.0, 0.5, -0.4, 0.3);
  inner.look(w('R12', 'world') - 0.2, 0.0, -0.45, 0.6).expr(w('R12', 'soul'), 'warm', 1.0, 1.1);
  sad.expr(w('R12', 'world'), 'smallSmile', 1.0, 0.8);
  st.shot({ t0: s7l, env: 'hearth', envOpt: hearthOpt({ fire: 0.9 }), actors: [], foreground: ['annoy', 'fear', 'innerMaya', 'anger', 'sadness'], cam: [[s7l, 790, 1240, 1.0], [s7l, 790, 1180, 0.84, e('R12') - s7l + 1]], trans: { type: 'dissolve', dur: 0.6 },
    grade: (T) => ({ color: '#ffd9a0', alpha: 0.12 + 0.25 * smooth((T - w('R12', 'world')) / 1.5), mode: 'soft-light' }) });

  // ================================================================ SCENE 8 — Saturday at Nana's house
  const p0 = e('R12') + 1.3;
  st.scene('porch', p0, t('E8') - 4.6, 'gentle morning');
  st.amb('birds_morning', p0, t('E8') - 4.4, 0.6);
  const porchOpen = p0 + 3.7;
  maya.set(p0, { pose: 'stand', hideLegs: false, x: 905, y: 1640, s: 1, facing: -0.75, lean: 0, 'arms.L': { tx: -14, ty: 310, hand: 'relax' }, 'arms.R': { tx: 14, ty: 310, hand: 'relax' } }, 0.01);
  maya.head(p0, -0.75, 0.0, 0, 0.01).look(p0, -0.6, 0.05, 0.01).expr(p0, 'worried', 0.01, 0.6);
  eli.set(p0, { pose: 'stand', hideLegs: false, x: 1150, y: 1660, s: 1, facing: -0.6, lean: 0, 'arms.L': { tx: -14, ty: 320, hand: 'relax' }, 'arms.R': { tx: 14, ty: 320, hand: 'relax' } }, 0.01);
  eli.head(p0, -0.6, 0.05, 0, 0.01).look(p0, -0.5, 0.1, 0.01).expr(p0, 'sad', 0.01, 0.6);
  // out of habit, she knocks — two soft raps — and nobody answers
  const KN = [640, 1010];
  maya.set(p0 + 0.35, { 'arms.L': { ...reach('maya', p0 + 0.35, -1, KN[0] + 20, KN[1]), hand: 'fist', view: 'back', bend: 1, rotAbs: 185 } }, 0.45);
  for (const [k, tk] of [[0, p0 + 0.85], [1, p0 + 1.11]]) {
    maya.set(tk - 0.08, { 'arms.L': { ...reach('maya', p0 + 0.35, -1, KN[0] + 34, KN[1]), hand: 'fist', view: 'back', bend: 1, rotAbs: 185 } }, 0.08);
    maya.set(tk, { 'arms.L': { ...reach('maya', p0 + 0.35, -1, KN[0] + 2, KN[1]), hand: 'fist', view: 'back', bend: 1, rotAbs: 185 } }, 0.06);
  }
  st.sfx(p0 + 0.85, 'door_knock', 0.9);
  maya.set(p0 + 1.55, { 'arms.L': { tx: -14, ty: 300, hand: 'soft' } }, 0.6);
  maya.expr(p0 + 1.4, 'sad', 0.6, 0.9).look(p0 + 1.4, -0.4, 0.3, 0.4);
  maya.look(p0 + 2.0, 0.65, 0.0, 0.3).head(p0 + 1.9, 0.1, 0.05, 0, 0.6);         // looks to Eli
  eli.look(p0 + 2.1, -0.5, 0.0, 0.3).head(p0 + 2.0, -0.4, 0.05, 0, 0.5).expr(p0 + 2.1, 'tender', 0.6, 0.6);
  eli.head(p0 + 2.5, -0.4, 0.3, 0, 0.4).head(p0 + 2.9, -0.4, 0.05, 0, 0.4);       // a small nod: go on
  maya.head(p0 + 2.6, -0.75, 0.0, 0, 0.5).look(p0 + 2.6, -0.55, 0.1, 0.3);
  maya.set(p0 + 2.6, { 'arms.L': { ...reach('maya', p0 + 2.6, -1, 818, 1122), hand: 'pinch', view: 'back', bend: 1, holding: 'key', rotAbs: 180 } }, 0.7);
  st.sfx(p0 + 3.25, 'door_unlock', 0.8);
  st.sfx(porchOpen, 'door_creak', 0.8);
  maya.set(porchOpen - 0.15, { 'arms.L': { ...reach('maya', porchOpen, -1, 772, 1110), hand: 'flat', view: 'palm', bend: 1, rotAbs: 175 } }, 0.25);
  maya.set(porchOpen + 0.45, { 'arms.L': { ...reach('maya', porchOpen, -1, 712, 1110), hand: 'flat', view: 'palm', bend: 1, rotAbs: 175 } }, 0.5);
  maya.set(porchOpen + 1.1, { 'arms.L': { tx: -14, ty: 310, hand: 'relax' } }, 0.8);
  maya.look(porchOpen + 0.6, -0.4, 0.05, 0.3).expr(porchOpen + 0.6, 'tender', 1.0, 0.7);
  st.shot({ t0: p0, env: 'porch', envOpt: (T) => ({ doorOpen: smooth((T - porchOpen) / 1.9) * 0.95 }), actors: ['eli', 'maya'], cam: [[p0, 820, 1170, 0.95], [p0, 790, 1150, 1.08, 5.6]], trans: { type: 'dissolve', dur: 0.6 } });

  // inside: the recipe tin
  const n0 = t('E8') - 4.6;
  st.scene('nanahouse', n0, t('N19') - 1.3, 'gentle, bittersweet, hopeful');
  st.amb('room_tone', n0, D, 0.4);
  st.amb('birds_morning', n0, D, 0.25);
  const tinOpenT = n0 + 1.0;
  eli.set(n0, { x: 1175, y: 1600, s: 1, facing: -0.55, 'arms.R': { tx: 14, ty: 320, hand: 'relax' } }, 0.01);
  eli.set(n0, { 'arms.L': { ...reach('eli', n0, -1, 1022, 1090), hand: 'pinch', view: 'back', bend: 1, rotAbs: 200 } }, 0.01);
  eli.head(n0, -0.6, 0.45, 0, 0.01).look(n0, -0.5, 0.8, 0.01).expr(n0, 'sad', 0.01, 0.6);
  maya.set(n0, { x: 700, y: 1610, s: 1, facing: 0.5, 'arms.L': { tx: -14, ty: 310, hand: 'relax' }, 'arms.R': { tx: 14, ty: 310, hand: 'relax' } }, 0.01);
  maya.head(n0, 0.5, 0.2, 0, 0.01).look(n0, 0.55, 0.4, 0.01).expr(n0, 'sad', 0.01, 0.6);
  st.sfx(tinOpenT, 'tin_open', 0.8);
  const cardUp = n0 + 2.2;
  st.sfx(cardUp - 0.2, 'paper_rustle', 0.7);
  // card in both hands in front of his chest (local coordinates of Eli)
  const CARD = { x: 20, y: -690, w: 150, h: 100 };
  const cardHands = (T) => ({
    'arms.L': { tx: CARD.x - CARD.w / 2 + 8 - (-120), ty: CARD.y + 10 + 752, hand: 'pinch', view: 'back', bend: -1, rotAbs: -70, locked: true },
    'arms.R': { tx: CARD.x + CARD.w / 2 - 8 - 120, ty: CARD.y + 10 + 752, hand: 'pinch', view: 'back', bend: 1, rotAbs: 250, locked: true },
  });
  eli.set(cardUp, { ...(() => { const sk = skeleton(cast.eli, eli.sample(cardUp)); return {
    'arms.L': { tx: CARD.x - CARD.w / 2 + 10 - sk.shL[0], ty: CARD.y + 12 - sk.shL[1], hand: 'pinch', view: 'back', bend: -1, rotAbs: -80, locked: true, foreK: 0.55, upperK: 0.9 },
    'arms.R': { tx: CARD.x + CARD.w / 2 - 10 - sk.shR[0], ty: CARD.y + 12 - sk.shR[1], hand: 'pinch', view: 'back', bend: 1, rotAbs: 260, locked: true, foreK: 0.55, upperK: 0.9 } }; })(), facing: 0.15 }, 0.9);
  eli.head(cardUp, 0.1, 0.35, 0, 0.8).look(cardUp + 0.2, 0.0, 0.65, 0.4);
  const CARD2 = { x: 10, y: -610 };
  // card path: lifted out of the open tin, up to his chest; later held lower while they talk
  const cardAt = (T, S) => {
    const sc = (S.s || 1) * (cast.eli.scale || 1);
    const tin = [(1000 - S.x) / sc, (1095 - S.y) / sc];
    if (T < cardUp) return null;
    const u = smooth((T - cardUp) / 0.9);
    return [lerp(tin[0], CARD.x, u), lerp(tin[1], CARD.y, u), lerp(0.5, -0.04, u)];
  };
  const cardDraw = (ctx, T, S, fixed) => {
    const c = fixed || cardAt(T, S);
    if (!c) return;
    ctx.save(); ctx.globalAlpha = smooth((T - cardUp) / 0.15);
    P.recipeCard(ctx, c[0], c[1], CARD.w, CARD.h, c[2], cast.eli, [[c[0] - CARD.w / 2 - 4, c[1] + 6, -0.25], [c[0] + CARD.w / 2 + 4, c[1] + 6, Math.PI + 0.25]], T);
    ctx.restore();
  };
  const nanaKitchenOpt = (T) => ({ tinOpen: smooth((T - tinOpenT) / 0.8) });
  st.shot({ t0: n0, env: 'nanaKitchen', envOpt: nanaKitchenOpt, actors: ['maya', 'eli'], cam: [[n0, 870, 1110, 1.25], [n0, 900, 1060, 1.5, 4.4]], trans: { type: 'dissolve', dur: 0.5 },
    beforeActor: (ctx, T, id, S) => { if (id === 'eli') S.overArms = (c2) => cardDraw(c2, T, S); } });

  // E8–E9: reading the card
  const s8c = t('E8') - 0.3;
  eli.expr(t('E8'), 'tender', 0.6, 0.9, { glisten: 0.6 });
  eli.look(w('E8', 'Mae') - 0.1, -0.6, 0.05, 0.25).head(w('E8', 'Mae') - 0.15, -0.3, 0.1, 0, 0.5);
  eli.look(w('E8', 'her') - 0.05, 0.0, 0.7, 0.3).head(w('E8', 'her') - 0.15, 0.05, 0.4, 0, 0.5);
  eli.look(w('E9', 'two') - 0.1, -0.55, 0.05, 0.3).head(w('E9', 'two') - 0.2, -0.3, 0.1, 0, 0.5);
  eli.expr(t('E9'), 'cry', 0.6, 0.75, { smile: 0.1 }).tear(lerp(t('E9'), e('E9'), 0.55), 1, 2.4);
  st.shot({ t0: s8c, env: 'nanaKitchen', envOpt: nanaKitchenOpt, actors: ['eli'], cam: [[s8c, 1065, 1000, 2.2], [s8c, 1065, 1000, 2.4, e('E9') - s8c]],
    beforeActor: (ctx, T, id, S) => { if (id === 'eli') S.overArms = (c2) => cardDraw(c2, T, S); } });
  // insert: the card
  const s8i = w('E9', 'for') - 0.2;
  st.shot({ t0: s8i, env: 'nanaKitchen', envOpt: nanaKitchenOpt, actors: [], cam: [[s8i, 0, 0, 1], [s8i, 0, 0, 1.05, 2]], trans: { type: 'dissolve', dur: 0.25 },
    screen: (ctx, T) => {
      ctx.fillStyle = 'rgba(30,22,18,0.55)'; ctx.fillRect(0, 0, 1080, 1920);
      const zz = 1 + 0.04 * (T - s8i);
      ctx.save(); ctx.translate(540, 820); ctx.scale(zz, zz);
      // his hands come in from the bottom corners: fingers behind the card, thumbs on the front
      for (const sd of [-1, 1]) {
        ctx.save();
        ctx.fillStyle = '#4f565f'; ctx.strokeStyle = 'rgba(30,32,36,0.6)'; ctx.lineWidth = 5;
        ctx.beginPath(); capsule(ctx, sd * 620, 1150, 135, sd * 440, 330, 95); ctx.fill(); ctx.stroke();
        ctx.fillStyle = '#2b2f35'; ctx.beginPath(); ctx.ellipse(sd * 442, 300, 92, 34, sd * 0.2, 0, TAU); ctx.fill();
        ctx.translate(sd * 438, 300); ctx.rotate(-Math.PI / 2 + sd * 0.12);
        drawHand(ctx, cast.eli, { ...HANDS.grip, curl: [0.15, 0.2, 0.25, 0.3], spread: 0.1 }, sd > 0 ? 1 : -1, 'back', { keyDir: -2, keyColor: '#fff0d6', keyAmt: 0.6, shadowColor: '#4c5560', shadowAmt: 0.25 }, 330);
        ctx.restore();
      }
      P.recipeCard(ctx, 0, 0, 900, 600, -0.04, cast.eli, [[-452, 170, -0.45], [452, 170, Math.PI + 0.45]], T, 4.2);
      ctx.restore();
    } });

  // M16: Maya's hand on his shoulder — "Tell me what you remember."
  const s8d = t('M16') - 0.45;
  eli.set(s8d, { x: 1100, facing: -0.3 }, 0.6);
  eli.set(s8d, (() => { const sk = skeleton(cast.eli, { ...eli.sample(s8d), facing: -0.3 }); return {
    'arms.L': { tx: CARD2.x - CARD.w / 2 + 10 - sk.shL[0], ty: CARD2.y + 12 - sk.shL[1], hand: 'pinch', view: 'back', bend: -1, rotAbs: -80, locked: true, foreK: 0.55, upperK: 0.9 },
    'arms.R': { tx: CARD2.x + CARD.w / 2 - 10 - sk.shR[0], ty: CARD2.y + 12 - sk.shR[1], hand: 'pinch', view: 'back', bend: 1, rotAbs: 260, locked: true, foreK: 0.55, upperK: 0.9 } }; })(), 0.6);
  maya.set(s8d - 0.6, { x: 790, facing: 0.6 }, 0.6);
  maya.set(s8d, { 'arms.R': { ...reach('maya', s8d, 1, ...(() => { const sw = shoulderWorld('eli', s8d, -1); return [sw[0] + 4, sw[1] + 30]; })()), hand: 'soft', view: 'back', bend: -1, rotAbs: 10, locked: true } }, 0.7);
  maya.expr(s8d, 'tender', 0.6, 1.0, { glisten: 0.7 }).look(s8d, 0.55, 0.0, 0.3).head(s8d, 0.45, 0.05, 4, 0.6);
  eli.look(t('M16') + 0.3, -0.55, 0.0, 0.3).head(t('M16') + 0.2, -0.45, 0.05, 0, 0.6);
  st.shot({ t0: s8d, env: 'nanaKitchen', envOpt: nanaKitchenOpt, actors: ['eli', 'maya'], cam: [[s8d, 950, 1060, 1.6], [s8d, 950, 1060, 1.7, 3]],
    beforeActor: (ctx, T, id, S) => { if (id === 'eli') S.overArms = (c2) => cardDraw(c2, T, S, [CARD2.x, lerp(CARD.y, CARD2.y, smooth((T - s8d) / 0.6)), -0.04]); } });

  // E10: a laugh through tears
  const s8e = t('E10') - 0.35;
  eli.expr(t('E10'), 'laughCry', 0.6, 0.9);
  eli.set(w('E10', 'bread') - 0.1, { shrug: 0.25 }, 0.2).set(w('E10', 'bread') + 0.2, { shrug: 0 }, 0.3);
  eli.look(w('E10', 'rushing') - 0.2, -0.5, -0.05, 0.3);
  maya.expr(w('E10', 'rushing'), 'laughCry', 0.5, 1.0).tear(we('E10', 'rushing') + 0.3, 1, 3.4);
  maya.head(e('E10') + 0.1, 0.4, 0.15, 8, 0.4).head(e('E10') + 0.5, 0.45, 0.0, 4, 0.5);
  st.shot({ t0: s8e, env: 'nanaKitchen', envOpt: nanaKitchenOpt, actors: ['eli', 'maya'], cam: [[s8e, 950, 1040, 1.7], [s8e, 950, 1020, 1.95, e('E10') - s8e + 1.4]],
    beforeActor: (ctx, T, id, S) => { if (id === 'eli') S.overArms = (c2) => cardDraw(c2, T, S, [CARD2.x, CARD2.y, -0.04]); } });

  // N19–N20 + end card: the family by the window, morning light
  const s8f = t('N19') - 1.3;
  fam(s8f);
  anger.set(s8f + 0.5, { 'arms.R': { ...reach('anger', s8f + 0.5, 1, ...(() => { const sw = shoulderWorld('fear', s8f + 0.5, -1); return [sw[0] - 4, sw[1] + 210]; })()), hand: 'soft', view: 'back', bend: -1, rotAbs: 10, locked: true } }, 0.9);
  sad.set(s8f + 0.8, { 'arms.R': { tx: 40, ty: 170, hand: 'soft', view: 'back', bend: 1 } }, 0.6);
  for (const a of [inner, anger, fear, annoy, sad]) a.expr(w('N19', 'family') - 0.2, 'smallSmile', 1.0, 0.9);
  inner.look(w('N19', 'family'), -0.3, 0.2, 0.4).head(w('N19', 'family'), -0.2, 0.1, -3, 0.8);
  fear.look(w('N19', 'family') + 0.3, -0.5, 0.1, 0.4);
  anger.look(w('N19', 'family') + 0.4, 0.4, -0.05, 0.4);
  annoy.look(w('N20', 'every') + 0.1, 0.5, 0.0, 0.4).expr(w('N20', 'every'), 'smile', 0.8, 0.6);
  sad.set(w('N19', 'family'), { lean: 6 }, 0.8);
  inner.look(w('N20', 'matters') - 0.4, 0.4, 0.15, 0.4).head(w('N20', 'matters') - 0.5, 0.25, 0.05, 3, 0.8);
  st.shot({ t0: s8f, env: 'hearth', envOpt: hearthOpt({ view: 'nana', fire: 0.9 }), actors: [], foreground: ['annoy', 'fear', 'innerMaya', 'anger', 'sadness'], cam: [[s8f, 790, 1290, 1.12], [s8f, 790, 1200, 0.84, D - s8f]], trans: { type: 'dissolve', dur: 0.7 },
    grade: { color: '#ffd9a0', alpha: 0.2, mode: 'soft-light' } });
  st.title(e('N20') + 0.8, D, [{ text: 'What does grief', font: 'italic 66px InterItalic', lh: 84 }, { text: 'mean for you?', font: 'italic 66px InterItalic', lh: 120 }, { text: 'THE FAMILY INSIDE', font: '34px InterXB', spacing: 8, color: '#f6e2c4' }], 300, { fadeIn: 1.0, fadeOut: 0.01 });

  // photo of Nana and little Maya on the mantel
  function photo(ctx, T, x, y) {
    ctx.save();
    ctx.translate(x, y);
    const fw = 120, fh = 150;
    ctx.fillStyle = '#6b4a2e'; ctx.fillRect(-fw / 2 - 10, -fh - 10, fw + 20, fh + 20);
    ctx.fillStyle = '#e8d9b8'; ctx.fillRect(-fw / 2, -fh, fw, fh);
    ctx.beginPath(); ctx.rect(-fw / 2 + 6, -fh + 6, fw - 12, fh - 12); ctx.clip();
    const g = ctx.createLinearGradient(0, -fh, 0, 0); g.addColorStop(0, '#d9c9a0'); g.addColorStop(1, '#b89a6c'); ctx.fillStyle = g; ctx.fillRect(-fw, -fh, fw * 2, fh);
    const { drawCharacter } = require('./rig');
    const neutral = (a) => { const S = st.actors[a].sample(1); return S; };
    const Sn = { ...neutral('nana'), x: 24, y: 44, s: 0.16, pose: 'stand', facing: -0.2, head: { yaw: -0.25, pitch: 0, tilt: 3 }, gaze: [-0.1, 0], blink: 0, mouth: { open: 0 }, face: { ...neutral('nana').face, smile: 0.6, lidL: 0.25 }, arms: { L: { tx: -14, ty: 290 }, R: { tx: 14, ty: 290 } }, tears: [] };
    const Sk = { ...neutral('youngMaya'), x: -30, y: 6, s: 0.16, pose: 'stand', facing: 0.2, head: { yaw: 0.25, pitch: 0, tilt: -4 }, gaze: [0.1, 0], blink: 0, mouth: { open: 0 }, face: { ...neutral('youngMaya').face, smile: 0.8, lidL: 0.3 }, arms: { L: { tx: -14, ty: 200 }, R: { tx: 14, ty: 200 } }, tears: [] };
    drawCharacter(ctx, cast.nana, Sn, null, T);
    drawCharacter(ctx, cast.youngMaya, Sk, null, T);
    ctx.fillStyle = 'rgba(255,220,160,0.18)'; ctx.fillRect(-fw, -fh, fw * 2, fh);
    ctx.restore();
  }

  st.scene('end', t('N19') - 1.3, D, 'warm resolution, the family together');
  st.amb('fire_crackle', t('N19') - 1.3, D, 0.35);

  // kitchen: warm pool under the pendant lamp + lift the deep shadow under the table; chairs under the sitters
  const kitchenFX = (ctx) => {
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    const g = ctx.createRadialGradient(430, 1180, 20, 430, 1180, 520);
    g.addColorStop(0, 'rgba(255,190,110,0.22)'); g.addColorStop(1, 'rgba(255,190,110,0)');
    ctx.fillStyle = g; ctx.fillRect(-100, 650, 1060, 1000);
    const g2 = ctx.createLinearGradient(0, 1430, 0, 2300);
    g2.addColorStop(0, 'rgba(120,80,50,0.0)'); g2.addColorStop(0.15, 'rgba(120,80,50,0.32)'); g2.addColorStop(1, 'rgba(120,80,50,0.38)');
    ctx.fillStyle = g2; ctx.fillRect(-300, 1430, 2200, 900);
    ctx.restore();
  };
  for (const sh of st.shots) {
    if (sh.env !== 'kitchen') continue;
    const f0 = sh.front;
    sh.front = (ctx, T, stg, eo, states) => { kitchenFX(ctx); if (f0) f0(ctx, T, stg, eo, states); };
    const u0 = sh.under;
    sh.under = (ctx, T, stg, eo) => {
      if (u0) u0(ctx, T, stg, eo);
      for (const id of ['maya', 'eli']) {
        const S = st.actors[id].sample(T);
        if (S.pose === 'sit' && !S.hidden) P.chair(ctx, S.x, S.y + 8, S.y + 300 * (S.s || 1), S.s || 1, S.facing || 0);
      }
    };
  }

  return st;
}

module.exports = { buildFilm };
