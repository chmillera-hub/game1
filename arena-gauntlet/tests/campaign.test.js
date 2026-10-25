// The road through a campaign: rounds of three challenges, one event and one merchant an
// act, the bosses, and the optional final challenge. Run: node tests/campaign.test.js
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;

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

// Win the battle at hand without fighting it (the reward logic runs as after a real win).
function win(run) {
  const s = AG.Engine.createBattle(R.battleConfig(run, R.autoDeploy(run, 0)));
  s.over = true;
  s.winner = 'P';
  R.finishBattle(run, s, R.autoDeploy(run, 0));
  const p = run.pending;
  if (p.bossRelics && !p.bossRelicTaken) R.takeBossRelic(run, p.bossRelics[0]);
  if (p.tome && !p.tomeTaken) R.skipTome(run);
  if (!p.spoilTaken) R.skipSpoils(run);
  R.completeNode(run);
}

// Win one of the challenges on offer; the reward screen it leads to.
function winAt(run, i) {
  R.chooseChallenge(run, i);
  const dep = R.autoDeploy(run, 0);
  const s = AG.Engine.createBattle(R.battleConfig(run, dep));
  s.over = true;
  s.winner = 'P';
  R.finishBattle(run, s, dep);
  return run.pending;
}

function lose(run) {
  const s = AG.Engine.createBattle(R.battleConfig(run, R.autoDeploy(run, 0)));
  s.over = true;
  s.winner = 'E';
  R.finishBattle(run, s, R.autoDeploy(run, 0));
  R.backToChoice(run);
}

// Get past whatever the current step is.
function advance(run, tier) {
  const p = run.pending;
  if (!p) {
    const i = run.offer.findIndex((o) => o.tier === tier);
    assert.ok(R.chooseChallenge(run, i < 0 ? 0 : i));
    return win(run);
  }
  if (p.type === 'shop') return R.completeNode(run);
  if (p.type === 'event') {
    const c = R.eventChoices(run).filter((x) => x.enabled && !x.pick).pop();
    R.chooseEvent(run, c.id, null);
    if (run.pending.type === 'battle') return win(run);
    return R.completeNode(run);
  }
  throw new Error('unexpected ' + p.type);
}

test('each act: four rounds of three challenges, one event and one merchant in the middle, then the boss', () => {
  for (let seed = 1; seed <= 20; seed++) {
    const run = R.newRun({ seed, warband: 'vanguard' });
    const kinds = run.plan.map((p) => p.kind);
    assert.strictEqual(kinds.filter((k) => k === 'fight').length, 4);
    assert.strictEqual(kinds.filter((k) => k === 'event').length, 1);
    assert.strictEqual(kinds.filter((k) => k === 'shop').length, 1);
    assert.strictEqual(kinds[kinds.length - 1], 'boss');
    assert.strictEqual(kinds[0], 'fight', 'it opens with a battle');
    assert.ok(kinds.indexOf('event') > 0 && kinds.indexOf('event') < kinds.length - 2, 'the event sits in the middle');
    assert.ok(kinds.indexOf('shop') > 1 && kinds.indexOf('shop') < kinds.length - 1, 'so does the merchant');
    assert.deepStrictEqual(run.offer.map((o) => o.tier), ['easy', 'medium', 'elite']);
    assert.strictEqual(new Set(run.offer.map((o) => o.enc.name)).size, 3, 'three different battles');
  }
});

test('easy is smaller than medium; elite pays more and drops a relic', () => {
  let easier = 0;
  for (let seed = 1; seed <= 20; seed++) {
    const run = R.newRun({ seed, warband: 'vanguard' });
    const [e, m, el] = run.offer;
    if (e.enc.budget < m.enc.budget) easier++;
    const re = R.challengeReward(run, e);
    const rm = R.challengeReward(run, m);
    const rel = R.challengeReward(run, el);
    assert.ok(re.gold <= rm.gold && rm.gold < rel.gold && re.xp < rm.xp && rm.xp < rel.xp);
    assert.ok(rel.relic && !rel.lucky && (!rm.relic || rm.lucky) && (!re.relic || re.lucky));
    assert.ok(re.spoils < rm.spoils);
  }
  assert.ok(easier >= 18, `easy battles are smaller (${easier}/20)`);
});

test('easy and medium wins now and then carry a relic (6% and 10%), shown on the card', () => {
  const N = 300;
  const got = { 0: 0, 1: 0 };
  for (let seed = 1; seed <= N; seed++) {
    for (const i of [0, 1]) {
      const run = R.newRun({ seed, warband: 'vanguard' });
      const rw = R.challengeReward(run, run.offer[i]);
      const had = run.relics.length;
      const p = winAt(run, i);
      assert.strictEqual(p.relicGained || null, rw.relic || null, 'the relic on the card is the one you get');
      if (rw.relic) {
        assert.ok(rw.lucky && p.relicLucky && run.relics.length === had + 1);
        got[i]++;
      }
    }
  }
  assert.ok(got[0] >= N * 0.02 && got[0] <= N * 0.11, `easy: ${got[0]}/${N}`);
  assert.ok(got[1] >= N * 0.05 && got[1] <= N * 0.16, `medium: ${got[1]}/${N}`);
});

test('what a battle pays is set when the cards are dealt: losing, retrying or reloading never changes it', () => {
  for (let seed = 1; seed <= 30; seed++) {
    for (const i of [0, 1, 2]) {
      const direct = R.newRun({ seed, warband: 'vanguard' });
      const card = JSON.stringify(direct.offer[i].reward);
      const a = winAt(direct, i);
      // The same run, reloaded from its save, lost twice, then won.
      const other = JSON.parse(JSON.stringify(R.newRun({ seed, warband: 'vanguard' })));
      assert.strictEqual(JSON.stringify(other.offer[i].reward), card, 'a reload deals the same card');
      for (let k = 0; k < 2; k++) {
        R.chooseChallenge(other, i);
        lose(other);
      }
      const b = winAt(other, i);
      assert.deepStrictEqual(b.spoils, a.spoils, `seed ${seed} card ${i}: same spoils`);
      assert.strictEqual(b.relicGained, a.relicGained, 'same relic');
      assert.strictEqual(b.gold + 10, a.gold, 'same gold, less the first-try bonus');
    }
  }
});

test('a defeat goes back to the same three challenges; the lost one counts its tries', () => {
  const run = R.newRun({ seed: 4, warband: 'vanguard' });
  const names = run.offer.map((o) => o.enc.name);
  R.chooseChallenge(run, 2);
  lose(run);
  assert.strictEqual(run.pending, null);
  assert.deepStrictEqual(run.offer.map((o) => o.enc.name), names);
  assert.strictEqual(run.offer[2].attempts, 1);
  R.chooseChallenge(run, 0);
  assert.strictEqual(run.pending.tier, 'easy');
  win(run);
  assert.notDeepStrictEqual(run.offer && run.offer.map((o) => o.enc.name), names, 'on to the next step');
});

test('the whole road: three acts, then the campaign is won and the final challenge is optional', () => {
  const run = R.newRun({ seed: 11, warband: 'vanguard' });
  let guard = 0;
  while (!run.won && guard++ < 60) advance(run, 'medium');
  assert.ok(run.won && run.act === 3, 'won after the Act III boss');
  assert.strictEqual(run.pending.type, 'summit');
  assert.ok(!run.over, 'the final challenge is still open');
  assert.ok(R.faceFinal(run));
  assert.strictEqual(run.offer.length, 1);
  assert.strictEqual(run.offer[0].tier, 'mega');
  assert.ok(run.offer[0].enc.units.some((u) => u.type === 'void_wyrm'));
  R.chooseChallenge(run, 0);
  lose(run);
  assert.ok(run.won && !run.over && run.offer[0].attempts === 1, 'a loss keeps the win and the offer');
  R.chooseChallenge(run, 0);
  win(run);
  assert.ok(run.over && run.superWon, 'a super victory');
});

// Anything in an enemy army that heals: a Cleric or Furgon, or a healing ability, skill or gear.
function healing(enc) {
  const D = AG.Data;
  const heals = (m) => !!m && ((m.props && (m.props.regen || m.props.lifesteal || m.props.healMult || m.props.killHeal)) || (m.active && ['heal', 'revive'].includes(m.active.kind)) || (m.traits || []).some((t) => ['bloodrage', 'auramend', 'martyr', 'phoenix', 'ogre', 'rallykill', 'harvest', 'undying', 'parasite', 'mossy'].includes(t)));
  const out = [];
  const specs = enc.units.concat(...(enc.waves || []).map((w) => w.units));
  for (const u of specs) {
    const T = D.UNITS[u.type];
    if (['cleric', 'furgon'].includes(u.type)) out.push(u.type);
    if ((T.props && (T.props.regen || T.props.lifesteal || T.props.totemHeal)) || (T.act.kind === 'drum' && !T.act.noHeal)) out.push(u.type + ' itself');
    for (const id of [u.a1, (u.level || 1) >= 2 ? u.a2 : null]) if (id && heals(D.ABILITIES[id].mod)) out.push(id);
    for (const id of (u.skills || []).concat(u.gear || [])) if (heals(D.itemDef(D.SKILLS[id] ? 'skill' : 'gear', id).mod)) out.push(id);
  }
  return out;
}

test('enemies never heal: no healers anywhere in a campaign, bosses and the final challenge included', () => {
  for (const seed of [3, 11, 29, 47]) {
    const run = R.newRun({ seed, warband: 'ember' });
    const seen = new Set();
    let bosses = 0;
    const look = () => {
      const encs = (run.offer || []).map((o) => o.enc).concat(run.pending && run.pending.enc ? [run.pending.enc] : []);
      for (const enc of encs) {
        if (seen.has(enc)) continue;
        seen.add(enc);
        if (enc.kind === 'boss') bosses++;
        assert.deepStrictEqual(healing(enc), [], `seed ${seed} ${enc.name}`);
      }
    };
    let guard = 0;
    while (!run.won && guard++ < 60) {
      look();
      advance(run, guard % 3 === 0 ? 'elite' : 'medium');
    }
    R.faceFinal(run);
    look();
    assert.ok(bosses >= 4, 'three bosses and the final challenge checked');
  }
});

test('a campaign enemy never rises again: a Level 3 Skeleton Archer keeps its mastery but not its Undying', () => {
  const E = AG.Engine;
  const s = E.createBattle({ w: 9, h: 9, terrain: new Array(81).fill(0), relics: { P: [], E: [] }, seed: 3, queue: true, units: [
    { type: 'skelarcher', team: 'P', x: 4, y: 8, level: 3 },
    { type: 'skelarcher', team: 'E', x: 4, y: 0, level: 3, foe: true },
  ] });
  const [mine, foe] = s.units;
  assert.ok(mine.phoenix, 'yours still rises again');
  assert.ok(!foe.phoenix, 'a campaign enemy does not');
});

test('claiming the victory instead ends the campaign as won', () => {
  const run = R.newRun({ seed: 12, warband: 'vanguard' });
  let guard = 0;
  while (!run.won && guard++ < 60) advance(run, 'easy');
  R.endRun(run);
  assert.ok(run.over && run.won && !run.superWon);
});

test('the merchant: six things, relics dearer than anything else, and a resupply that costs 20, 30, 40', () => {
  for (let seed = 1; seed <= 15; seed++) {
    const run = R.newRun({ seed, warband: 'vanguard' });
    run.gold = 1000;
    let guard = 0;
    while (!(run.pending && run.pending.type === 'shop') && guard++ < 20) advance(run, 'medium');
    const p = run.pending;
    assert.ok(p.stock.length <= 6, 'six at most');
    const relic = p.stock.find((it) => it.kind === 'relic');
    const others = p.stock.filter((it) => it.kind !== 'relic').map((it) => it.price);
    if (relic) assert.ok(relic.price >= 1.5 * Math.min(...others) && relic.price > Math.max(...others.filter((x, i) => p.stock.filter((it) => it.kind !== 'relic')[i].kind !== 'recruit')), 'relics cost the most');
    const before = run.gold;
    assert.strictEqual(R.rerollPrice(run), 20);
    assert.ok(R.rerollShop(run));
    assert.strictEqual(R.rerollPrice(run), 30);
    assert.ok(R.rerollShop(run));
    assert.strictEqual(R.rerollPrice(run), 40);
    assert.strictEqual(run.gold, before - 50);
    assert.ok(p.stock.length <= 6 && p.stock.every((it) => !it.sold));
  }
});

console.log(`campaign: ${passed} tests passed`);
