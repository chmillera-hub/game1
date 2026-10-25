// The player's priority target: the army goes all out for it, then back to normal.
// Run: node tests/priority.test.js
const assert = require('assert');
const AG = require('./load')(['rng.js', 'data.js', 'engine.js', 'ai.js']);
const E = AG.Engine;
const AI = AG.AI;

let passed = 0;
function test(name, fn) {
  try {
    fn();
    passed++;
  } catch (e) {
    console.error('FAIL', name);
    throw e;
  }
}

function battle(units, opts = {}) {
  const w = 9;
  const h = 9;
  return E.createBattle(Object.assign({ w, h, terrain: new Array(w * h).fill(0), units, relics: { P: [], E: [] }, seed: 7, queue: true }, opts));
}

// Play until the player has had `n` turns, the player's AI using `focus`.
function play(s, n, focus) {
  for (let turns = 0, g = 0; turns < n && !s.over && g < 500; g++) {
    const team = s.side;
    AI.playTurn(s, team, { stance: 'balanced', temp: 0, focus: team === 'P' ? focus : null });
    if (team === 'P') turns++;
  }
}

const army = () => [
  { type: 'knight', team: 'P', x: 3, y: 8 },
  { type: 'archer', team: 'P', x: 5, y: 8 },
  { type: 'orc', team: 'E', x: 4, y: 3 },
  { type: 'orc', team: 'E', x: 5, y: 3 },
];
const chest = { loot: [{ id: 'c1', kind: 'chest', x: 0, y: 2 }] };

test('left alone, the army heads for a chest and takes it', () => {
  const s = battle(army(), { loot: [{ id: 'c1', kind: 'chest', x: 8, y: 5 }] });
  play(s, 8, null);
  assert.ok(s.loot[0].taken);
  assert.strictEqual(s.byId[s.loot[0].by].team, 'P');
});

// An archer that can reach a chest this turn, with an orc in range: `orcHp` sets how
// close the orc is to falling.
function chestOrOrc(orcHp) {
  const s = battle(
    [
      { type: 'archer', team: 'P', x: 4, y: 8 },
      { type: 'orc', team: 'E', x: 4, y: 4 },
      { type: 'golem', team: 'E', x: 8, y: 0 },
    ],
    { loot: [{ id: 'c1', kind: 'chest', x: 2, y: 8 }] }
  );
  E.pass(s);
  s.units[1].hp = orcHp;
  const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0 });
  return plan.kind === 'moveLoot' || plan.kind === 'loot' ? 'chest' : plan.target && s.byId[plan.target.uid] ? s.byId[plan.target.uid].type : plan.kind;
}

test('a chest in reach beats an ordinary hit', () => {
  assert.strictEqual(chestOrOrc(46), 'chest');
});

test('but a kill comes first', () => {
  assert.strictEqual(chestOrOrc(5), 'orc');
});

test('an enemy as the priority comes before any chest', () => {
  const s = battle(army(), { loot: [{ id: 'c1', kind: 'chest', x: 3, y: 7 }] });
  E.pass(s);
  const ctx = AI.makeCtx(s, 'P', { focus: { uid: s.units[3].uid } });
  assert.strictEqual(ctx.lootField, null, 'no drift toward the chest');
  const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0, focus: { uid: s.units[3].uid } });
  assert.ok(plan.kind !== 'loot' && plan.kind !== 'moveLoot');
});

test('nobody wanders up to loot with sleeping guards', () => {
  const s = battle(
    [
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'orc', team: 'E', x: 4, y: 2 },
      { type: 'specter', team: 'E', x: 0, y: 1, post: { x: 0, y: 0 } },
    ],
    { loot: [{ id: 't1', kind: 'tome', x: 0, y: 0 }] }
  );
  const g = s.units[2];
  assert.ok(AI.dormant(s, g), 'the guard sleeps');
  assert.strictEqual(AI.makeCtx(s, 'P', {}).lootField, null);
});

test('made the priority, a unit goes and takes the chest', () => {
  const s = battle(army(), chest);
  play(s, 8, { loot: 'c1' });
  assert.ok(s.loot[0].taken, 'the chest is taken');
  assert.strictEqual(s.byId[s.loot[0].by].team, 'P');
  assert.strictEqual(AI.focusOf(s, 'P', { loot: 'c1' }), null, 'and the priority is done');
});

test('made the priority, an enemy is struck first even when another is the better hit', () => {
  const units = [
    { type: 'archer', team: 'P', x: 4, y: 8 },
    { type: 'scout', team: 'E', x: 4, y: 5, hp: 5 },
    { type: 'knight', team: 'E', x: 1, y: 4 },
  ];
  const first = (focus) => {
    const s = battle(units.map((u) => Object.assign({}, u)));
    E.pass(s); // the enemy's first turn
    s.units[1].hp = 4; // a nearly dead scout: the obvious kill
    const plan = AI.chooseActivation(s, 'P', { stance: 'balanced', temp: 0, focus });
    return plan.target && s.byId[plan.target.uid] ? s.byId[plan.target.uid].type : plan.kind;
  };
  assert.strictEqual(first(null), 'scout', 'normally it finishes the scout');
  const s = battle(units);
  assert.strictEqual(first({ uid: s.units[2].uid }), 'knight', 'with the knight as priority, it shoots the knight');
});

test('once the priority target falls, the army goes back to normal', () => {
  const s = battle(army());
  const target = s.units[3];
  play(s, 30, { uid: target.uid });
  assert.ok(!target.alive || s.over, 'the target went down');
  assert.strictEqual(AI.focusOf(s, 'P', { uid: target.uid }), null);
  const ctx = AI.makeCtx(s, 'P', { focus: { uid: target.uid } });
  assert.strictEqual(ctx.focus, null, 'no pull toward a fallen target');
});

test('an ally or a taken chest is never a priority', () => {
  const s = battle(army(), chest);
  assert.strictEqual(AI.focusOf(s, 'P', { uid: s.units[0].uid }), null);
  s.loot[0].taken = true;
  assert.strictEqual(AI.focusOf(s, 'P', { loot: 'c1' }), null);
});

test('foes keep out of a Lightning Ward\'s reach unless they can hit a living unit from there', () => {
  // A ward sits between the orcs and a knight far behind it: the orcs do not walk into the
  // pulse just to stand there, or to hack at the ward.
  const s = battle([
    { type: 'lightning', team: 'P', x: 4, y: 4 },
    { type: 'knight', team: 'P', x: 0, y: 8 },
    { type: 'orc', team: 'E', x: 4, y: 0 },
    { type: 'orc', team: 'E', x: 5, y: 0 },
  ]);
  const [ward, kn] = s.units;
  let entered = 0;
  for (let g = 0; g < 60 && !s.over; g++) {
    const team = s.side;
    if (team === 'P') {
      E.pass(s);
      continue;
    }
    AI.playTurn(s, 'E', { stance: 'aggressive', temp: 0 });
    // Once the knight falls only the ward is left, and then it is fair game.
    if (!kn.alive) break;
    for (const o of s.units.filter((u) => u.team === 'E' && u.alive)) {
      const inReach = Math.abs(o.x - ward.x) + Math.abs(o.y - ward.y) <= 2;
      const canHit = Math.abs(o.x - kn.x) + Math.abs(o.y - kn.y) <= 1;
      if (inReach && !canHit) entered++;
    }
  }
  assert.strictEqual(entered, 0, 'never parked inside the pulse with nothing living to hit');
  assert.ok(kn.hp < kn.maxHp, 'they went around it for the knight');
});

test('the shrine as priority: the army takes it, drives off squatters and holds it', () => {
  // A shrine off to the side, enemies in the middle that would draw the army to them.
  const make = () =>
    battle(
      [
        { type: 'knight', team: 'P', x: 3, y: 8 },
        { type: 'knight', team: 'P', x: 4, y: 8 },
        { type: 'archer', team: 'P', x: 5, y: 8 },
        { type: 'orc', team: 'E', x: 5, y: 2 },
        { type: 'orc', team: 'E', x: 6, y: 2 },
      ],
      { objective: 'hold', hold: { x: 0, y: 4, need: 6, count: 0 } }
    );
  const f = { hold: true, label: 'the shrine' };
  assert.deepStrictEqual(AI.focusOf(make(), 'P', f), { hold: true, x: 0, y: 4 });
  const run = (focus) => {
    const s = make();
    let best = 0;
    for (let t = 0; t < 16 && !s.over; t++) {
      play(s, 1, focus);
      best = Math.max(best, s.hold.count);
    }
    return { s, best };
  };
  const a = run(f);
  const b = run(null);
  assert.ok(a.best >= 2, `with the priority a unit of yours holds it turn after turn (${a.best})`);
  assert.ok(a.best > b.best, `more than on normal orders (${a.best} vs ${b.best})`);
  const on = E.at(a.s, 0, 4);
  assert.ok(on && on.team === 'P', 'and it is still yours at the end');
});

test('a spot on open ground as priority: the army huddles there and stays', () => {
  const make = () =>
    battle([
      { type: 'knight', team: 'P', x: 3, y: 8 },
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'archer', team: 'P', x: 5, y: 8 },
      { type: 'orc', team: 'E', x: 4, y: 1 },
      { type: 'orc', team: 'E', x: 5, y: 1 },
    ]);
  const f = { tile: true, x: 8, y: 8, label: 'the marked spot' };
  assert.deepStrictEqual(AI.focusOf(make(), 'P', f), { tile: true, x: 8, y: 8 });
  assert.strictEqual(AI.focusOf(make(), 'E', f), null, 'only your army gathers there');
  const spread = (focus) => {
    const s = make();
    play(s, 6, focus);
    const mine = s.units.filter((u) => u.alive && u.team === 'P');
    return mine.reduce((t, u) => t + Math.abs(u.x - 8) + Math.abs(u.y - 8), 0) / mine.length;
  };
  const huddled = spread(f);
  const normal = spread(null);
  assert.ok(huddled <= 2, `huddled in the corner (average ${huddled.toFixed(1)} tiles away)`);
  assert.ok(huddled < normal, `closer than on normal orders (${huddled.toFixed(1)} vs ${normal.toFixed(1)})`);
});

test('one of your units as priority: the army gathers around it', () => {
  const make = () =>
    battle([
      { type: 'knight', team: 'P', x: 0, y: 8 },
      { type: 'knight', team: 'P', x: 4, y: 8 },
      { type: 'archer', team: 'P', x: 8, y: 8 },
      { type: 'cleric', team: 'P', x: 8, y: 7 },
      { type: 'orc', team: 'E', x: 4, y: 0 },
    ]);
  const s0 = make();
  const leader = s0.units[0];
  const f = { ally: leader.uid, label: 'the knight' };
  assert.deepStrictEqual(AI.focusOf(s0, 'P', f), { tile: true, ally: leader, x: 0, y: 8 });
  assert.strictEqual(AI.focusOf(s0, 'E', f), null, 'the enemy does not rally on your unit');
  const spread = (focus) => {
    const s = make();
    play(s, 6, focus);
    const lead = s.units[0];
    const rest = s.units.filter((u) => u.alive && u.team === 'P' && u !== lead);
    return rest.reduce((t, u) => t + Math.abs(u.x - lead.x) + Math.abs(u.y - lead.y), 0) / rest.length;
  };
  const rallied = spread(f);
  const normal = spread(null);
  assert.ok(rallied <= 2.5, `gathered around it (average ${rallied.toFixed(1)} tiles away)`);
  assert.ok(rallied < normal, `closer than on normal orders (${rallied.toFixed(1)} vs ${normal.toFixed(1)})`);
  // It falls: the rally is over.
  const s = make();
  s.units[0].alive = false;
  assert.strictEqual(AI.focusOf(s, 'P', f), null);
});

console.log(`priority: ${passed} tests passed`);
