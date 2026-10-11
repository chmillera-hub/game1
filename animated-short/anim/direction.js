// "Yeah. I know." -- staging, acting and camera, beat by beat.
// Times come from the voice timeline: s(id)/e(id) = start/end of a line, m(name) = a mark.

module.exports = function direct(st) {
  const s = (id, o = 0) => st.S(id) + o;
  const e = (id, o = 0) => st.E(id) + o;
  const m = (n, o = 0) => st.M(n) + o;
  const M = 'marcus', T = 'theo', P = 'priya';
  const ALL = [M, P, T];

  // =====================================================================
  // SCENE 1 -- game night. The first frame is already the scene (no fade).
  // =====================================================================
  st.shot(0, { who: 'wide', z: 1.0, dz: 0.012 });
  st.pose(ALL, -1, 'controller', 0.01);
  st.look(ALL, -1, 'tv');
  st.expr(M, -1, 'grin', 0.01, { smile: 0.55, smirk: 0.4 });
  st.expr(P, -1, 'focused', 0.01, { smile: 0.25, press: 0.2 });
  st.expr(T, -1, 'focusTongue', 0.01);
  st.set(M, -1, { lean: 0.02, shoulder: 0.15 }, 0.01);
  st.set(T, -1, { shoulder: 0.35, headPitch: 0.08 }, 0.01);
  // little "steering" sways while they play
  [[0.5, -0.04], [1.1, 0.05], [1.7, -0.03], [2.3, 0.04]].forEach(([t, l]) => st.set(T, t, { lean: l }, 0.35));
  [[0.8, 0.04], [1.6, -0.02], [2.4, 0.03]].forEach(([t, l]) => st.set(M, t, { lean: l }, 0.4));
  [[0.9, 0.02], [1.9, -0.025]].forEach(([t, l]) => st.set(P, t, { lean: l }, 0.4));
  st.light(0.55, { tvFlash: 0.35 }, 0.05); st.light(0.7, { tvFlash: 0 }, 0.3);
  st.light(1.5, { tvFlash: 0.3 }, 0.05); st.light(1.65, { tvFlash: 0 }, 0.3);
  st.pose(T, 1.2, 'controllerUp', 0.3); st.pose(T, 1.8, 'controller', 0.3);
  st.expr(P, 1.0, 'excited', 0.3);
  st.look(P, 1.6, T, { dur: 0.15, head: 0.4 }); st.look(P, 2.1, 'tv', { dur: 0.15 });

  // Theo's character dies
  const die = s('T1', -0.35);
  st.light(die, { tvFlash: 0.7 }, 0.06); st.light(die + 0.1, { tvFlash: 0 }, 0.6);
  st.shot(die, { who: T, z: 2.2, dz: 0.01 });
  st.expr(T, die, 'dismay', 0.15);
  st.set(T, die, { shoulder: 0.5, lean: 0 }, 0.2);
  st.pose(T, s('T1', 0.9), 'controllerDrop', 0.5);
  st.set(T, s('T1', 0.95), { headPitch: -0.22, slump: 0.4, shoulder: 0 }, 0.5);
  st.expr(T, e('T1', -0.1), 'selfLaugh', 0.35);
  st.set(T, e('T1', -0.1), { headPitch: 0, laugh: 0.3 }, 0.4);
  st.set(T, e('T1', 0.8), { laugh: 0 }, 0.4);
  st.expr(M, die, 'happy', 0.3); st.look(M, die + 0.2, T, { head: 0.5 });
  st.pose(M, die + 0.3, 'controllerDrop', 0.5);
  st.set(M, die + 0.3, { lean: -0.03, shoulder: 0 }, 0.6);

  // Priya, sympathetic
  st.shot(s('P1', -0.1), { who: [P, T], dz: 0.008 });
  st.look(P, s('P1', -0.2), T, { head: 0.7 });
  st.expr(P, s('P1', -0.2), 'happy', 0.3, { browL: 0.45, browR: 0.45, angL: 0.35, angR: 0.35 });
  st.pose(P, s('P1', 0.1), 'controllerDrop', 0.5);
  st.look(T, s('P1', 0.4), P, { head: 0.6 });

  // Marcus: the jab
  st.shot(s('M1', -0.15), { who: M, z: 2.3, dz: 0.01 });
  st.expr(M, s('M1', -0.2), 'grin', 0.3);
  st.look(M, s('M1', -0.25), T, { head: 0.75 });
  st.set(M, s('M1', -0.1), { lean: -0.05, headTilt: 0.06 }, 0.5);
  st.look(T, s('M1', 0), M, { head: 0.6 });
  st.expr(T, s('M1', 0), 'happy', 0.4, { smile: 0.4 });
  st.pose(M, s('M1b', -0.2), 'gestureR', 0.4);
  st.nod(M, s('M1b', 0.55), 1, 0.12, 0.3);
  // he laughs and glances at Priya for the group laugh
  st.expr(M, e('M1b', -0.05), 'laugh', 0.2);
  st.set(M, e('M1b', -0.05), { laugh: 0.9, headPitch: -0.15 }, 0.2);
  st.look(M, e('M1b', 0.1), P, { head: 0.4, dur: 0.15 });
  st.pose(M, e('M1b', 0.1), 'controllerDrop', 0.5);
  st.expr(P, s('M1b', 0.4), 'awkward', 0.4, { smile: 0.4 });

  // Theo -- the smile fades
  const tq = e('M1b', 0.25);
  st.shot(tq, { who: T, z: 2.9, dz: 0.012 });
  st.expr(T, tq + 0.1, 'smileFade', 0.7);
  st.look(T, tq + 0.55, 'lap', { dur: 0.5, head: 0.7 });
  st.expr(T, s('T2', -0.3), 'hurt', 0.8);
  st.set(T, s('T2', -0.3), { slump: 0.55, laugh: 0, talkAnim: 0.2 }, 0.8);
  st.set(T, s('T2', 0.3), { shoulder: 0.35 }, 0.3);
  st.set(T, s('T2', 0.9), { shoulder: 0 }, 0.5);
  st.hold(T, s('T2', -0.2), e('T2', 0.6));
  st.blink(T, e('T2', 0.8));

  // the silence: Marcus's laugh dies
  const sil = m('silence', 0.05);
  st.set(M, s('T2', 0.15), { laugh: 0 }, 0.35);
  st.shot(sil + 0.1, { who: M, z: 3.0, dz: 0.012 });
  st.expr(M, s('T2', 0.2), 'frozen', 0.25);
  st.set(M, s('T2', 0.2), { headPitch: 0, lean: 0 }, 0.4);
  st.look(M, s('T2', 0.25), T, { head: 0.6, dur: 0.12 });
  st.hold(M, s('T2', 0.2), sil + 1.4);
  st.expr(M, sil + 0.8, 'uneasy', 1.4, { smile: 0.12 });
  st.blink(M, sil + 1.5);
  st.look(M, sil + 1.6, P, { head: 0.3, dur: 0.12 });
  st.look(M, sil + 2.2, 'tv', { head: 0.6, dur: 0.3 });

  // Priya's eyes dart between them
  const pd = sil + 2.5;
  st.shot(pd, { who: P, z: 3.0 });
  st.expr(P, sil, 'uneasy', 0.6, { press: 0.6 });
  st.look(P, pd + 0.0, T, { head: 0.15, dur: 0.1, blink: false });
  st.look(P, pd + 0.55, M, { head: 0.15, dur: 0.1, blink: false });
  st.look(P, pd + 1.05, T, { head: 0.15, dur: 0.1, blink: false });
  st.look(P, pd + 1.6, 'tv', { head: 0.2, dur: 0.2 });
  st.set(P, pd + 0.2, { blush: 0.35 }, 1.2);

  // Narration over a very still room
  st.shot(s('N1', -0.15), { who: 'wide', z: 1.0, dz: 0.006 });
  st.pose(M, s('N1', 0.6), 'neckRub', 0.8);
  st.expr(M, s('N1', 0.4), 'awkward', 0.8, { smile: 0.1 });
  st.set(M, s('N1', 0.4), { blush: 0.35 }, 1.5);
  st.look(T, s('N1', 0), 'hands', { head: 0.7 });

  st.shot(s('N2', -0.1), { who: M, z: 2.4, dz: 0.014 });
  st.pose(M, s('N2', 1.4), 'controllerDrop', 0.9);
  st.look(M, s('N2', 0.8), 'downR', { head: 0.4, dur: 0.4 });
  st.look(M, e('N2', -0.6), T, { head: 0.35, dur: 0.3 });
  st.blink(M, e('N2', 0.2));

  st.shot(s('N3', -0.15), { who: T, z: 3.1, dz: 0.012 });
  st.expr(T, s('N3', 0), 'sad', 1.0);
  st.pose(T, s('N3', 0.4), 'lap', 0.9);
  st.items(s('N3', 0.85), ['snacks', 'controller2']);
  st.nod(T, e('N3', -0.2), 1, 0.07, 0.6);

  st.shot(s('N4', -0.1), { who: 'wide', z: 1.08, dy: -10, dz: 0.004 });
  st.look(P, s('N4', 0.3), M, { head: 0.2, dur: 0.12 });
  st.look(P, s('N4', 1.4), T, { head: 0.25, dur: 0.12 });
  st.look(P, s('N4', 2.6), 'downL', { head: 0.3, dur: 0.3 });
  st.look(M, s('N4', 1.0), 'tv', { head: 0.6 });
  st.look(P, e('N4', -1.2), M, { head: 0.2, dur: 0.1 });
  st.look(P, e('N4', -0.6), T, { head: 0.2, dur: 0.1 });
  st.pose(M, s('N4', 2.0), 'controllerDrop', 0.8);

  // Priya leaves
  st.shot(s('P2', -0.15), { who: P, z: 2.6 });
  st.expr(P, s('P2', -0.2), 'awkward', 0.4, { smile: 0.3 });
  st.look(P, s('P2', -0.1), M, { head: 0.4 });
  st.look(P, s('P2', 0.9), 'down', { head: 0.4 });
  st.pose(P, s('P2', 0.3), 'lap', 0.6);
  st.items(s('P2', 0.6), ['snacks', 'controller2', 'controller3']);
  st.set(P, e('P2', -0.2), { sit: 0, x: 600, slump: 0 }, 0.9);
  st.pose(P, e('P2', -0.2), 'hang', 0.8);
  st.look(M, e('P2', 0), P, { head: 0.5 });
  st.shot(e('P2', 0.25), { who: [P, T], dz: 0.006 });
  st.look(P, s('P3', -0.3), T, { head: 0.6 });
  st.expr(P, s('P3', -0.3), 'worried', 0.5, { smile: 0.1 });
  st.pose(P, s('P3', -0.4), 'touchR', 0.6);
  st.set(P, s('P3', -0.4), { lean: 0.06 }, 0.6);
  st.look(T, s('P3', 0.1), P, { head: 0.6, oy: -0.5 });
  st.expr(T, s('P3', 0.3), 'gentle', 0.5, { smile: 0.12 });
  st.nod(T, e('P3', 0.2), 1, 0.12, 0.5);
  st.order(m('priya_exit', -0.6), [M, T, P]);
  st.pose(P, m('priya_exit', 0.1), 'hang', 0.5);
  st.set(P, m('priya_exit', 0.1), { lean: 0 }, 0.4);
  st.shot(m('priya_exit', 0.2), { who: 'wide', z: 1.0 });
  st.set(P, m('priya_exit', 0.3), { walk: 1 }, 0.25);
  st.move(P, m('priya_exit', 0.3), 1450, 2.0, 'in');
  st.look(P, m('priya_exit', 0.3), 'right', { head: 0.8 });
  st.look(T, m('priya_exit', 0.6), 'down', { head: 0.6, dur: 0.4 });
  st.look(M, m('priya_exit', 1.6), T, { head: 0.6 });
  st.show(P, m('priya_exit', 2.5), false);
  st.expr(M, m('priya_exit', 0.5), 'uneasy', 0.8);
  st.blink(M, m('door', 0.02)); st.blink(T, m('door', 0.05));
  st.set(T, m('door', 0), { shoulder: 0.2 }, 0.08); st.set(T, m('door', 0.15), { shoulder: 0 }, 0.4);

  // Marcus turns off the TV
  st.pose(M, m('tv_off', -0.7), 'controllerUp', 0.5);
  st.look(M, m('tv_off', -0.6), 'tv', { head: 0.7 });
  st.light(m('tv_off'), { tvFlash: 0.4 }, 0.04);
  st.light(m('tv_off', 0.06), { tv: 0, tvFlash: 0 }, 0.35);
  st.pose(M, m('tv_off', 0.6), 'lap', 0.7);
  st.items(m('tv_off', 0.95), ['snacks', 'controller2', 'controller3', 'controller']);
  st.set(M, m('tv_off', 0.6), { slump: 0.3 }, 1.0);

  // =====================================================================
  // SCENE 2 -- the conversation. Lamp light only, an empty seat between them.
  // =====================================================================
  st.shot(s('M2', -0.6), { who: [M, T], dz: 0.005 });
  st.expr(M, s('M2', -0.3), 'awkward', 0.4, { smile: 0.35 });
  st.look(M, s('M2', -0.2), T, { head: 0.6 });
  st.pose(M, s('M2', -0.1), 'neckRub', 0.6);
  st.set(M, s('M2', 0.0), { laugh: 0.25 }, 0.2); st.set(M, s('M2', 0.6), { laugh: 0 }, 0.3);
  st.look(M, e('M2', -0.2), 'downR', { head: 0.3 });
  st.shot(s('M2b', -0.1), { who: M, z: 2.5, dz: 0.01 });
  st.look(M, s('M2b', 0.2), T, { head: 0.6 });
  st.pose(M, e('M2b', 0.3), 'lap', 0.7);
  st.expr(T, s('M2', 0), 'calm', 0.6);
  st.look(T, s('M2', 0.3), 'hands', { head: 0.6 });

  st.shot(s('T3', -0.2), { who: T, z: 2.6, dz: 0.01 });
  st.look(T, s('T3', 0.2), 'hands', { head: 0.6 });
  st.set(T, s('T3', -0.3), { talkAnim: 0.4 }, 0.3);
  st.look(T, e('T3', 0.3), M, { head: 0.6, dur: 0.35 });
  st.expr(T, s('T4', -0.2), 'firm', 0.5, { smile: -0.08 });
  st.set(T, s('T4', -0.3), { shoulder: 0.15 }, 0.3); st.set(T, s('T4', 0.4), { shoulder: 0 }, 0.6);

  st.shot(s('M3', -0.25), { who: M, z: 2.6 });
  st.expr(M, s('M3', -0.3), 'confused', 0.35);
  st.set(M, s('M3', -0.3), { headTilt: -0.05, headPitch: -0.05 }, 0.4);
  st.expr(M, e('M3', -0.1), 'defensive', 0.6, { furrow: 0.5, angL: -0.35, angR: -0.35 });
  st.pose(M, s('M3', 0.2), 'knees', 0.6);

  // Theo names it
  st.shot(s('T5', -0.25), { who: T, z: 2.4, dz: 0.008 });
  st.set(T, s('T5', -0.3), { talkAnim: 0.8, headTilt: 0 }, 0.3);
  st.expr(T, s('T5', -0.2), 'calm', 0.4);
  st.look(T, s('T5', 0), 'downL', { head: 0.5, dur: 0.4 });
  st.pose(T, s('T5', 0.8), 'gestureR', 0.5);
  st.shake(T, s('T5', 0.6), 2, 0.07, 0.4);
  st.look(T, s('T5', 2.6), M, { head: 0.5 });
  st.expr(T, e('T5', -1.2), 'smileFade', 0.5, { smile: 0.15, angL: 0.35, angR: 0.35 });
  st.pose(T, e('T5', 0.1), 'handUp', 0.5);
  st.expr(T, s('T6', 0), 'calm', 0.4);
  st.look(T, s('T6', 0.0), 'hands', { head: 0.3, oy: -0.4 });
  st.look(T, s('T6', 1.6), M, { head: 0.5 });
  st.pose(T, e('T6', 0.2), 'lap', 0.7);
  st.expr(T, s('T7', 0), 'sad', 0.8, { lidU: 0.25 });

  // Marcus hears it -- the guard goes up
  st.shot(s('T7', 1.3), { who: M, z: 2.7, dz: 0.012 });
  st.expr(M, s('T7', 1.2), 'stunned', 0.3);
  st.blink(M, s('T7', 1.6));
  st.expr(M, e('T7', -0.4), 'defensive', 0.7);
  st.pose(M, e('T7', -0.3), 'crossed', 0.7);
  st.set(M, e('T7', -0.3), { lean: -0.04, slump: 0, headPitch: -0.08 }, 0.7);
  st.look(M, e('T7', 0.2), 'left', { head: 0.4 });
  st.look(M, s('M4', 0.9), T, { head: 0.6, dur: 0.2 });
  st.set(M, s('M4', 0), { talkAnim: 1.4, shoulder: 0.25 }, 0.3);
  st.nod(M, s('M4', 1.4), 2, 0.1, 0.35);
  st.set(M, e('M4', 0.2), { talkAnim: 1, shoulder: 0.1 }, 0.5);

  // Theo doesn't back down
  st.shot(s('T8', -0.2), { who: T, z: 2.7 });
  st.expr(T, s('T8', -0.2), 'firm', 0.3);
  st.look(T, s('T8', -0.2), M, { head: 0.6 });
  st.shake(T, s('T8', 0.0), 2, 0.09, 0.28);
  st.set(T, s('T8', 0), { slump: 0, talkAnim: 0.6 }, 0.6);
  st.expr(T, s('T9', -0.1), 'gentle', 0.6, { smile: 0.12 });
  st.set(T, s('T9', 0), { headTilt: 0.07 }, 0.6);
  st.pose(T, s('T9', 0.1), 'gestureL', 0.5);
  st.pose(T, e('T9', 0.6), 'lap', 0.8);

  // the beat: Marcus, arms crossed, softening
  st.shot(e('T9', 0.15), { who: M, z: 2.8, dz: 0.01 });
  st.blink(M, e('T9', 0.5));
  st.look(M, e('T9', 0.7), 'down', { head: 0.4, dur: 0.4 });
  st.expr(M, e('T9', 0.6), 'uneasy', 1.2, { press: 0.4 });
  st.set(M, e('T9', 0.6), { headPitch: 0, lean: 0 }, 1.0);

  st.shot(s('T10', -0.15), { who: [M, T], dz: 0.008 });
  st.set(T, s('T10', 0), { lean: -0.04, headTilt: 0.05 }, 0.8);
  st.expr(T, s('T10', 0), 'gentle', 0.5);
  st.look(M, s('T10', 0.8), T, { head: 0.5 });
  st.shot(s('T11', -0.15), { who: T, z: 2.8, dz: 0.012 });
  st.expr(T, s('T11', 0.2), 'earnest', 0.6, { smile: 0.05 });
  st.pose(M, s('T11', 0.4), 'clasped', 1.4);

  // Marcus looks away -- music enters
  st.shot(e('T11', 0.2), { who: M, z: 3.0, dz: 0.016 });
  st.look(M, e('T11', 0.5), 'window', { head: 0.8, dur: 0.6 });
  st.expr(M, e('T11', 0.4), 'worried', 1.6, { press: 0.55, lidU: 0.22 });
  st.set(M, e('T11', 0.4), { tear: 0.15, talkAnim: 0.5 }, 2.0);
  st.blink(M, s('N5', 1.2));
  st.expr(M, s('N6', 0.4), 'sad', 1.5);
  st.look(M, s('N6', 0.8), 'downR', { head: 0.5, dur: 0.6 });
  st.set(M, s('N6', 0.6), { slump: 0.35 }, 1.5);

  // his story
  st.expr(M, s('M5', -0.2), 'sad', 0.5, { lidU: 0.3 });
  st.look(M, s('M5', 0), 'hands', { head: 0.5 });
  st.expr(M, e('M5', -0.6), 'sad', 0.4, { smile: 0.18, smirk: 0.35 });
  st.shot(s('M6', -0.15), { who: M, z: 2.6, dz: 0.01 });
  st.expr(M, s('M6', 0.3), 'amused', 0.5, { smile: 0.35, lidL: 0.3 });
  st.set(M, s('M6', 0.3), { headTilt: 0.05 }, 0.5);
  st.look(M, s('M6', 0.4), 'upL', { head: 0.3, dur: 0.4 });
  st.look(M, s('M6', 2.4), T, { head: 0.6, dur: 0.4 });
  st.expr(M, s('M6', 2.4), 'sincere', 0.6);
  st.set(M, s('M6', 2.4), { headTilt: 0 }, 0.6);
  st.shot(e('M6', -1.1), { who: T, z: 2.8 });
  st.expr(T, e('M6', -1.1), 'gentle', 0.6, { smile: 0.05 });
  st.nod(T, e('M6', 0.1), 1, 0.08, 0.6);

  st.shot(s('M7', -0.15), { who: M, z: 2.9, dz: 0.012 });
  st.look(M, s('M7', 0.1), 'downL', { head: 0.4, dur: 0.5 });
  st.expr(M, s('M7', 0), 'sad', 0.6);
  st.nod(M, e('M7', -0.5), 1, 0.08, 0.5);
  st.expr(M, s('M8', 0.2), 'guilty', 0.8, { lidU: 0.3 });
  st.blink(M, s('M8', 0.9));
  st.look(M, e('M8', -0.6), 'down', { head: 0.4 });
  st.look(M, s('M9', 1.4), T, { head: 0.5, dur: 0.3 });
  st.set(M, s('M9', 0), { talkAnim: 0.3 }, 0.3);

  st.shot(s('M9', 1.3), { who: T, z: 3.0, dz: 0.01 });
  st.expr(T, s('M9', 1.5), 'stunned', 0.5);
  st.hold(T, s('M9', 1.4), e('M9', 1.2));
  st.blink(T, e('M9', 1.3));

  st.shot(s('M10', -0.15), { who: M, z: 3.0, dz: 0.012 });
  st.expr(M, s('M10', 0), 'guilty', 0.6);
  st.set(M, s('M10', 0), { tear: 0.35 }, 2.5);
  st.look(M, s('M10', 0.3), 'down', { head: 0.5 });
  st.shake(M, s('M10', 1.6), 3, 0.05, 0.5);

  st.shot(s('T12', -0.2), { who: T, z: 2.9 });
  st.expr(T, s('T12', -0.4), 'worried', 0.6, { lidU: 0.15 });
  st.set(T, s('T12', -0.4), { lean: -0.05, talkAnim: 0.3 }, 0.8);

  st.shot(s('M11', -0.15), { who: M, z: 3.0, dz: 0.01 });
  st.look(M, s('M11', -0.2), T, { head: 0.4 });
  st.nod(M, s('M11', 0.2), 1, 0.1, 0.5);
  st.expr(M, s('M11', 0.3), 'relieved', 0.5, { smile: 0.15 });
  st.look(M, s('M12', -0.2), 'down', { head: 0.5, dur: 0.5 });
  st.expr(M, s('M12', 0), 'guilty', 0.6, { press: 0.6 });
  st.set(M, s('M12', 0), { tear: 0.45 }, 1.0);
  st.blink(M, e('M12', 0.4));

  st.shot(e('M12', 0.5), { who: [M, T], dz: 0.006 });
  st.look(T, e('M12', 0.6), M, { head: 0.6 });

  st.shot(s('T13', -0.1), { who: T, z: 2.8, dz: 0.01 });
  st.expr(T, s('T13', 0), 'stunned', 0.5, { angL: 0.6, angR: 0.6 });

  st.shot(s('M13', -0.15), { who: M, z: 2.8 });
  st.look(M, s('M13', 0), T, { head: 0.5 });
  st.expr(M, s('M13', 0.2), 'sheepish', 0.5, { smile: 0.22 });
  st.set(M, s('M13', 0.1), { laugh: 0.2 }, 0.2); st.set(M, s('M13', 0.5), { laugh: 0 }, 0.3);
  st.pose(M, s('M13', 0.6), 'faceRub', 0.6);
  st.pose(M, e('M13', 0.4), 'clasped', 0.7);
  st.look(M, e('M13', 0.1), 'downR', { head: 0.3 });
  st.set(M, e('M13', 0), { tear: 0.2, slump: 0.2 }, 1.5);

  // the turn -- humor finds the door
  st.shot(s('T14', -0.2), { who: T, z: 2.7, dz: 0.01 });
  st.expr(T, s('T14', 0), 'gentle', 0.6, { smile: 0.3 });
  st.set(T, s('T14', 0.2), { headTilt: 0.08, talkAnim: 0.8, lean: -0.03 }, 0.6);
  st.expr(T, s('T14', 2.4), 'amused', 0.6, { smile: 0.45, browL: 0.45 });

  st.shot(s('M14', -0.2), { who: M, z: 2.8 });
  st.look(M, s('M14', -0.3), T, { head: 0.4, oy: 0.3 });
  st.pose(M, s('M14', -0.2), 'shrug', 0.4);
  st.set(M, s('M14', -0.2), { shoulder: 0.6 }, 0.35); st.set(M, s('M14', 0.5), { shoulder: 0 }, 0.5);
  st.expr(M, s('M14', -0.2), 'sheepish', 0.4, { blush: 0.35 });
  st.pose(M, e('M14', 0.3), 'clasped', 0.6);

  st.shot(s('T15', -0.2), { who: T, z: 2.6 });
  st.expr(T, s('T15', 0), 'amused', 0.5);
  st.shake(T, s('T15', 0.6), 4, 0.06, 0.45);
  st.shot(e('T15', 0.15), { who: [M, T], z: 1.32, dz: 0.006 });
  st.expr(M, st.S('LM2'), 'laugh', 0.25, { mouthOpen: 0.2 });
  st.set(M, st.S('LM2'), { laugh: 0.5, headPitch: -0.1, slump: 0, tear: 0 }, 0.25);
  st.expr(T, st.S('LT2'), 'laugh', 0.25, { mouthOpen: 0.15 });
  st.set(T, st.S('LT2'), { laugh: 0.4 }, 0.25);
  st.set([M, T], e('T15', 1.4), { laugh: 0, headPitch: 0 }, 0.5);
  st.expr(M, e('T15', 1.4), 'warm', 0.6, { smile: 0.35 });
  st.expr(T, e('T15', 1.4), 'warm', 0.6, { smile: 0.3 });
  st.look(M, e('T15', 1.0), T, { head: 0.6 });

  // ...but he holds the line
  st.shot(s('T16', -0.2), { who: T, z: 2.6, dz: 0.008 });
  st.expr(T, s('T16', 0.1), 'sincere', 0.6);
  st.set(T, s('T16', 0), { headTilt: 0, lean: 0 }, 0.6);
  st.pose(T, s('T16', 0.5), 'chest', 0.5);
  st.pose(T, s('T16', 2.4), 'gestureL', 0.5);
  st.expr(T, e('T16', -1.2), 'sincere', 0.4, { smile: 0.18 });
  st.pose(T, s('T17', 0.6), 'lap', 0.6);
  st.expr(T, s('T17', 0.3), 'sincere', 0.5, { smile: 0 });
  st.shot(e('T17', -2.2), { who: M, z: 2.7, dz: 0.01 });
  st.expr(M, e('T17', -2.2), 'sincere', 0.6);
  st.nod(M, e('T17', -1.2), 2, 0.07, 0.6);

  // Marcus: the exaggerated "worst version"
  st.shot(s('M15', -0.2), { who: M, z: 2.5 });
  st.expr(M, s('M15', 0), 'confused', 0.4, { smile: 0.15 });
  st.pose(M, s('M15', 0.1), 'openBoth', 0.5);
  st.set(M, s('M15', 0), { talkAnim: 1.3 }, 0.3);
  st.look(M, s('M15', 0.2), T, { head: 0.6 });
  st.expr(M, s('M15', 1.4), 'grin', 0.4, { smile: 0.4 });
  // full sincerity, played dead serious
  st.shot(s('M15b', -0.3), { who: M, z: 3.2, dz: 0.02 });
  st.expr(M, s('M15b', -0.35), 'earnest', 0.3, { lidU: -0.06, browL: 0.6, browR: 0.6, angL: 0.55, angR: 0.55, smile: 0.08 });
  st.set(M, s('M15b', -0.35), { headTurn: 0.25, headTilt: 0.09, lean: 0.05, talkAnim: 0.1 }, 0.4);
  st.pose(M, s('M15b', -0.3), 'chest', 0.5);
  st.hold(M, s('M15b', -0.4), e('M15b', 1.2));
  st.look(M, s('M15b', -0.3), T, { head: 0.7, blink: false });

  st.shot(e('M15b', 0.15), { who: T, z: 3.0 });
  st.expr(T, e('M15b', 0.0), 'wideEyed', 0.2);
  st.set(T, e('M15b', 0.0), { lean: 0.07, headPitch: -0.06 }, 0.3);
  st.blink(T, e('M15b', 0.7)); st.blink(T, e('M15b', 0.98));
  st.expr(T, s('T18', -0.2), 'deadpan', 0.35, { smirk: 0.15 });
  st.set(T, s('T18', -0.2), { talkAnim: 0.2 }, 0.3);
  st.look(T, s('T18', -0.1), M, { head: 0.6 });

  st.shot(e('T18', 0.05), { who: [M, T], z: 1.32, dz: 0.008 });
  st.set(M, st.S('LM3'), { headTurn: 0, laugh: 1, headPitch: -0.2, talkAnim: 1, lean: 0, headTilt: 0 }, 0.2);
  st.expr(M, st.S('LM3'), 'laugh', 0.2);
  st.pose(M, st.S('LM3'), 'lap', 0.5);
  st.expr(T, st.S('LT3'), 'laugh', 0.25);
  st.set(T, st.S('LT3'), { laugh: 0.8, headPitch: 0.15, lean: 0 }, 0.25);
  st.set([M, T], e('T18', 1.5), { laugh: 0, headPitch: 0 }, 0.5);
  st.expr([M, T], e('T18', 1.5), 'warm', 0.5);

  st.shot(s('T19', -0.15), { who: T, z: 2.5, dz: 0.008 });
  st.expr(T, s('T19', 0), 'warm', 0.4, { smile: 0.4 });
  st.set(T, s('T19', 0), { talkAnim: 0.9 }, 0.3);
  st.pose(T, s('T19', 0.3), 'gestureR', 0.5);
  st.look(T, s('T19', 2.0), 'downR', { head: 0.3, dur: 0.3 });
  st.look(T, s('T19', 3.0), M, { head: 0.6 });
  st.pose(T, e('T19', -0.4), 'lap', 0.6);
  st.expr(T, s('T20', 0), 'sincere', 0.5, { smile: 0.12 });
  st.pose(T, e('T20', -1.6), 'chest', 0.5);
  st.nod(T, e('T20', -0.9), 1, 0.1, 0.5);
  st.shot(e('T20', -1.3), { who: M, z: 2.7 });
  st.expr(M, e('T20', -1.3), 'warm', 0.6, { smile: 0.3 });
  st.nod(M, e('T20', -0.4), 1, 0.1, 0.5);

  // Deal -- and the gap closes
  st.expr(M, s('M16', -0.2), 'warm', 0.4, { smile: 0.55 });
  const fb = m('fistbump');
  st.shot(fb - 0.25, { who: [M, T], dz: 0.004 });
  st.move(M, fb - 0.1, 385, 0.7); st.move(T, fb, 700, 0.7);
  st.pose(T, fb, 'lap', 0.4);
  st.set(M, fb + 0.55, { rx: 0.68, ry: 0.42, rhx: 0.6, rhy: 1 }, 0.35, 'out');
  st.each(M, (p) => p.shapeR.set(fb + 0.6, 'fist'));
  st.set(T, fb + 0.6, { lx: -0.7, ly: 0.42 }, 0.3, 'out');
  st.each(T, (p) => p.shapeL.set(fb + 0.65, 'fist'));
  st.look(T, fb + 0.4, M, { head: 0.6, oy: 0.3 });
  st.expr(T, fb + 0.4, 'warm', 0.4, { smile: 0.5 });
  st.pose(M, fb + 1.35, 'lap', 0.6); st.pose(T, fb + 1.4, 'lap', 0.6);
  st.set([M, T], fb + 0.9, { laugh: 0.15 }, 0.2); st.set([M, T], fb + 1.3, { laugh: 0 }, 0.3);

  st.shot(s('M17', -0.3), { who: M, z: 2.8, dz: 0.014 });
  st.expr(M, s('M17', -0.2), 'sincere', 0.6, { lidU: 0.2 });
  st.look(M, s('M17', -0.2), 'down', { head: 0.3 });
  st.look(M, s('M17', 1.8), T, { head: 0.6, dur: 0.4 });
  st.set(M, s('M17', 0), { tear: 0.3, talkAnim: 0.4 }, 1.5);
  st.hold(M, s('M17', 1.8), e('M17', 1.0));

  st.shot(s('T21', -0.35), { who: T, z: 3.0, dz: 0.012 });
  st.expr(T, s('T21', -0.5), 'warm', 0.8, { smile: 0.35 });
  st.set(T, s('T21', -0.5), { tear: 0.35, talkAnim: 0.2 }, 1.0);
  st.nod(T, e('T21', 0.2), 1, 0.12, 0.7);

  st.shot(s('N7', -0.2), { who: [M, T], dz: -0.01 });
  st.expr(M, s('N7', 0), 'warm', 0.6, { smile: 0.45 });
  st.look(M, s('N7', 1.8), 'tv', { head: 0.6, dur: 0.5 });
  st.look(T, s('N7', 2.2), 'lap', { head: 0.4, dur: 0.6 });
  st.set([M, T], s('N7', 1.0), { tear: 0 }, 2.0);

  // =====================================================================
  // SCENE 3 -- the next morning
  // =====================================================================
  const s3 = m('s3') - 0.03; // instant changes land before the first frame of the scene
  st.light(s3, { tv: 0, lamp: 0, morning: 1, rain: 0, tvFlash: 0 }, 0.01);
  st.items(s3, ['mug', 'jam']);
  st.shot(s3, { who: 'wide', z: 1.0, dz: 0.004 });
  st.show(P, s3, false);
  st.order(s3, [M, T]);
  st.move(T, s3, 1380, 0.01);
  st.set(T, s3, { sit: 0, slump: 0, lean: 0, tear: 0, laugh: 0 }, 0.01);
  st.pose(T, s3, 'plate', 0.01);
  st.pose(M, s3, 'mugLap', 0.01);
  st.expr(M, s3, 'neutral', 0.01, { smile: 0.1, lidU: 0.2 });
  st.expr(T, s3, 'happy', 0.01, { smile: 0.4 });
  st.set(M, s3, { slump: 0.1, tear: 0, laugh: 0, blush: 0 }, 0.01);
  st.look(M, s3, 'tv', { head: 0.5 });
  st.set(T, s3 + 0.3, { walk: 1 }, 0.2);
  st.move(T, s3 + 0.3, 700, 1.9, 'out');
  st.look(T, s3 + 0.3, M, { head: 0.6 });
  st.set(T, s3 + 2.0, { walk: 0 }, 0.3);
  st.set(T, s3 + 2.2, { sit: 1 }, 0.7);
  st.pose(T, s3 + 2.5, 'plateLap', 0.5);
  st.look(M, s3 + 0.9, T, { head: 0.6, oy: 0.35 });
  st.expr(M, s3 + 1.6, 'skeptical', 0.6, { smile: 0.0, browL: 0.45 });

  st.shot(s('M18', -0.2), { who: [M, T], dz: 0.006 });
  st.look(M, s('M18', -0.3), T, { head: 0.6, oy: 0.55 });
  st.expr(M, s('M18', -0.2), 'deadpan', 0.4);
  st.look(M, e('M18', 0.1), T, { head: 0.7 });
  st.look(T, s('M18', 0.1), M, { head: 0.6 });
  st.shot(s('M19', -0.15), { who: M, z: 2.7, dz: 0.012 });
  st.set(M, s('M19', 0), { talkAnim: 0.5 }, 0.3);
  st.look(M, s('M19', 0.6), T, { head: 0.6, oy: 0.5 });
  st.look(M, e('M19', -0.4), T, { head: 0.7 });
  st.shot(e('M19', 0.1), { who: T, z: 2.8 });
  st.expr(T, e('M19', 0.1), 'skeptical', 0.4);
  st.hold(T, e('M19', 0.1), e('M19', 1.4));
  st.shot(s('M20', -0.1), { who: M, z: 2.9, dz: 0.012 });
  st.expr(M, s('M20', 0), 'sincere', 0.5, { lidU: 0.25 });
  st.nod(M, e('M20', -0.3), 1, 0.12, 0.5);
  st.expr(M, e('M20', 0), 'proud', 0.5);

  st.shot(s('T22', -0.2), { who: T, z: 2.6 });
  st.expr(T, s('T22', 0), 'amused', 0.5, { smile: 0.5 });
  st.set(T, s('T22', 0.2), { headTilt: 0.06 }, 0.5);
  st.shot(e('T22', 0.05), { who: [M, T], z: 1.45, dz: 0.006 });
  st.expr(M, st.S('LM4'), 'laugh', 0.2);
  st.set(M, st.S('LM4'), { laugh: 0.8, headPitch: -0.12 }, 0.2);
  st.expr(T, st.S('LT4'), 'laugh', 0.25);
  st.set(T, st.S('LT4'), { laugh: 0.7, headTilt: 0 }, 0.25);
  st.set([M, T], e('T22', 1.4), { laugh: 0, headPitch: 0 }, 0.5);
  st.expr([M, T], e('T22', 1.4), 'warm', 0.5, { smile: 0.5 });

  // narration: a quiet, silly little coda
  st.shot(s('N8', -0.2), { who: 'wide', z: 1.12, dy: 40, dz: -0.006 });
  st.pose(M, s('N8', 0.4), 'sip', 0.7);
  st.look(M, s('N8', 0.4), 'tv', { head: 0.5 });
  st.pose(M, s('N8', 2.0), 'mugLap', 0.6);
  st.look(T, s('N8', 1.0), 'lap', { head: 0.4 });
  st.set(T, s('N8', 3.0), { propX: -0.35 }, 0.6);
  st.set(T, s('N8', 3.0), { lx: -0.55, rx: -0.15 }, 0.6);
  st.look(T, s('N8', 3.0), M, { head: 0.6 });
  st.expr(T, s('N8', 3.0), 'happy', 0.4, { smile: 0.6 });
  st.look(M, s('N8', 3.5), T, { head: 0.5, oy: 0.4 });
  st.expr(M, s('N8', 3.6), 'skeptical', 0.4, { smile: 0.1 });
  st.shake(M, s('N9', 0.2), 3, 0.08, 0.4);
  st.set(T, s('N9', 0.4), { laugh: 0.5 }, 0.2); st.set(T, s('N9', 1.3), { laugh: 0 }, 0.4);
  st.expr(T, s('N9', 0.4), 'laugh', 0.3); st.expr(T, s('N9', 1.4), 'happy', 0.4);
  st.expr(M, s('N10', 0.3), 'amused', 0.5);
  st.set(M, s('N10', 0.6), { lean: 0.05 }, 0.8);
  st.set(T, s('N10', 0.8), { lean: -0.04 }, 0.8);
  st.look([M, T], s('N10', 1.5), 'tv', { head: 0.4, dur: 0.6 });
  st.set(T, s('N10', 1.2), { propX: 0, lx: -0.24, rx: 0.24 }, 0.7);
  st.expr(M, s('N11', 0), 'warm', 0.6, { smile: 0.4 });
  st.expr(T, s('N11', 0), 'warm', 0.6, { smile: 0.45 });
  st.look(T, s('N11', 1.2), M, { head: 0.5 });
  st.look(M, s('N11', 1.6), T, { head: 0.5 });
  st.shot(m('end', 0.0), { who: 'wide', z: 1.0, dz: 0.004 });
};
