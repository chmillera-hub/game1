// What the board shows as a unit's turn comes: one step at a time, in the engine's order
// (fatigue, poison, burns, regen, then its pass), and floating numbers that never land on
// each other. Plays real battles, with fatigue, poison, burns and regen forced in, through
// the board's own event playback; no browser needed.
// Run: node tests/beats.test.js [battles]
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js', 'run.js', 'sprites.js', 'render.js']);
const R = AG.Run;
const D = AG.Data;
const N = +process.argv[2] || 24;

let passed = 0;
async function test(name, fn) {
  try {
    await fn();
    passed++;
  } catch (e) {
    console.error('FAIL', name);
    throw e;
  }
}

// What shows over a unit's head, in the order a turn brings it.
const RANK = { fatigue: 0, poison: 1, burn: 2, fire: 2.5, regen: 3, sitout: 4, pass: 4 };
const SHOWS = new Set(['dmg', 'heal', 'sitout', 'pass', 'healblock', 'scorch', 'curse', 'absorb', 'resist', 'cleanse', 'shield', 'status']);
const shows = (e) => !!e.uid && SHOWS.has(e.t) && !(e.t === 'sitout' && e.why === 'passive') && !(e.t === 'pass' && e.auto);
const kind = (e) => (e.t === 'dmg' ? e.dmgType : e.t === 'heal' && e.why === 'regen' ? 'regen' : e.t);

// A board that records what it would play, beat by beat, instead of drawing it.
function recorder() {
  const b = Object.create(AG.Render.Board.prototype);
  Object.assign(b, { tw: 64, th: 32, unit: 64 / 48, texts: [], vis: new Map(), speed: 1.024, log: [] });
  b.center = (x, y) => [(x - y) * 32 + 400, (x + y) * 16 + 100];
  b.animMove = async (ev) => b.log.push({ ends: ev.uid });
  b.animAction = async (ev) => b.log.push({ ends: ev.uid });
  b.applyImpacts = async (group) => b.log.push({ evs: group });
  b.beatWait = async () => (b.log[b.log.length - 1].held = true);
  return b;
}

function battle(i) {
  const run = R.newRun({ seed: 900 + i * 7, warband: D.WARBANDS[i % D.WARBANDS.length].id });
  run.xp = 120;
  const enc = R.genEncounter(run, { id: `b${i}`, row: 1 + (i % 3), kind: i % 4 === 3 ? 'elite' : 'battle' });
  run.pending = { type: 'battle', nodeId: 'x', enc, attempt: 0, tier: i % 4 === 3 ? 'elite' : 'medium' };
  const cfg = R.battleConfig(run, R.autoDeploy(run, 0));
  cfg.overtime = 2;
  const s = AG.Engine.createBattle(cfg);
  let k = 0;
  for (const u of s.units) {
    if (!u.alive || u.structure || u.nonCombat) continue;
    u.maxHp *= 3;
    u.hp = u.maxHp - 30;
    const m = k++ % 3;
    if (m !== 1) u.poison = { turns: 99, dmg: 1, src: 0 };
    if (m !== 2) u.burn = { turns: 99, dmg: 1, src: 0 };
    if (m === 1) u.regen = 2; // poison stops healing: regen goes on the unpoisoned
  }
  const events = [];
  for (let guard = 0; guard < 8000 && !s.over; guard++) {
    AG.AI.playTurn(s, s.side, { stance: 'balanced', temp: 0.6 });
    events.push(...s.events);
    s.events.length = 0;
  }
  assert.ok(s.over, 'the battle ended');
  return { s, events };
}

const seen = { battles: 0, beats: 0, steps: 0, ordered: 0 };
(async () => {
  await test(`real battles played through the board: one step a beat, in order (${N} battles)`, async () => {
    for (let i = 0; i < N; i++) {
      const { s, events } = battle(i);
      const b = recorder();
      await b.playEvents(events, s);
      const open = new Map(); // uid -> the rank of the last step shown in its turn so far
      for (const entry of b.log) {
        if (entry.ends) {
          open.delete(entry.ends);
          continue;
        }
        const evs = entry.evs;
        const shown = evs.filter(shows);
        if (!shown.length) continue;
        seen.beats++;
        assert.ok(entry.held, `battle ${i}: a beat that shows something is held for its moment`);
        // One thing per unit a beat (fire underfoot with its burn, a poison tick with the
        // poison it leaves, aside).
        const per = new Map();
        for (const e of shown) per.set(e.uid, (per.get(e.uid) || []).concat(kind(e)));
        for (const [uid, ks] of per) {
          const real = ks.filter((k) => k !== 'scorch' && k !== 'curse' && k !== 'status');
          assert.ok(real.length <= 1, `battle ${i}: unit ${uid} shows ${ks.join(' + ')} at once`);
        }
        for (let j = 0; j < evs.length; j++) {
          const e = evs[j];
          if (['move', 'action', 'done'].includes(e.t)) open.delete(e.uid);
          // Fire underfoot: the burn that comes with a scorch, after any burn the unit carries.
          const fire = e.t === 'dmg' && j > 0 && evs[j - 1].t === 'scorch' && evs[j - 1].uid === e.uid;
          const r = fire ? RANK.fire : RANK[kind(e)];
          if (r == null || !e.uid || (e.t === 'pass' && e.auto)) continue;
          seen.steps++;
          const prev = open.get(e.uid);
          if (prev != null) {
            assert.ok(r > prev, `battle ${i}: unit ${e.uid} shows ${kind(e)} after a later step of its turn`);
            seen.ordered++;
          }
          if (r === 4) open.delete(e.uid);
          else open.set(e.uid, r);
        }
      }
      seen.battles++;
    }
    assert.ok(seen.ordered > 200, 'plenty of turns with several steps');
  });

  await test('floating numbers never land on each other: a unit\'s run of steps and a crowd hit at once', async () => {
    const b = recorder();
    const frames = [];
    const step = (ms) => {
      for (let t = 0; t < ms; t += 16) {
        for (const x of b.texts) x.life += 0.016;
        b.texts = b.texts.filter((x) => x.life < x.max);
        frames.push(b.texts.map((x) => ({ text: x.text, tag: x.tag, x: x.x, y: b.textY(x), w: x.w, big: x.big })));
      }
    };
    // A unit's turn at 2x: fatigue, poison, burn, then its pass, a beat apart; its
    // neighbour's turn straight after; then an area hit on five units side by side, each
    // with a number and a status word.
    const beat = 439;
    for (const [text, tag] of [['-16', 'FATIGUE'], ['-5', 'POISON'], ['-4', 'BURN'], ['PASS', 'COOLDOWN 2→1']]) {
      b.addText(4, 4, text, '#fff', { height: 40, tag });
      step(beat);
    }
    for (const [text, tag] of [['-17', 'FATIGUE'], ['-5', 'POISON'], ['+2', 'REGEN']]) {
      b.addText(5, 4, text, '#fff', { height: 40, tag });
      step(beat);
    }
    for (let x = 2; x <= 6; x++) {
      b.addText(x, 6, '-12', '#fff', { height: 40, tag: x === 4 ? 'FROM BEHIND' : '' });
      b.addText(x, 6, 'POISONED', '#fff', { height: 40, dy: -b.tw * 0.25 });
    }
    step(1500);
    for (const live of frames)
      for (let i = 0; i < live.length; i++)
        for (let j = i + 1; j < live.length; j++) {
          const p = live[i];
          const q = live[j];
          const cover = Math.abs(p.x - q.x) < (p.w + q.w) / 2 && Math.abs(p.y - q.y) < 0.8 * b.textGap(p, q);
          assert.ok(!cover, `"${p.text} ${p.tag}" covers "${q.text} ${q.tag}"`);
        }
    // Over one head the stack reads top to bottom in the order it came.
    const one = frames.find((f) => f.filter((t) => t.x === b.center(4, 4)[0]).length >= 3);
    assert.ok(one, 'a stack of three over one unit');
    const ys = one.filter((t) => t.x === b.center(4, 4)[0]).map((t) => t.y);
    assert.deepStrictEqual(ys, ys.slice().sort((p, q) => p - q), 'older above newer');
  });

  console.log(`beats: ${passed} tests passed · ${seen.battles} battles, ${seen.beats} beats, ${seen.steps} turn steps (${seen.ordered} checked against the step before)`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
