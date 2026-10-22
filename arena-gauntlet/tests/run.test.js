// Plays whole campaigns with the AI on both sides. Run: node tests/run.test.js [runs] [difficulty]
const assert = require('assert');
const AG = require('./load')();
const R = AG.Run;
const E = AG.Engine;
const N = +process.argv[2] || 20;
const DIFF = process.argv[3] || 'knight';

function playBattle(run) {
  const p = run.pending;
  const node = R.getNode(run, p.nodeId);
  const cp = R.cpFor(run, node, false, p.enc.kind);
  const dep = R.suggestDeployment(run, cp);
  assert.ok(dep.length > 0, 'deployment possible');
  const used = dep.reduce((t, d) => t + R.deployCost(run, d.rid), 0);
  assert.ok(used <= cp, 'within CP');
  const rows = R.deployRows(run, p.enc);
  for (const d of dep) assert.ok(rows.includes(d.y) && p.enc.terrain[d.y * p.enc.w + d.x] === 0, 'valid deploy tile');
  const s = E.createBattle(R.battleConfig(run, dep));
  let guard = 0;
  while (!s.over && guard++ < 100) {
    AG.AI.playTurn(s, s.side, { stance: s.side === 'E' ? p.enc.stance : 'balanced', temp: 0.6 });
    s.events.length = 0;
  }
  assert.ok(s.over, 'battle ended');
  return R.finishBattle(run, s, dep);
}

function pickUnit(run, pick) {
  const ok = run.roster.filter((u) => {
    if (pick.talent) return R.canLearn(u, pick.talent);
    if (pick.filter === 'promote') return u.rank < 3;
    if (pick.filter === 'transmute') return ['common', 'uncommon'].includes(AG.Data.UNITS[u.type].rarity);
    return true;
  });
  return ok.length ? ok[0].id : null;
}

const results = { won: 0, lost: 0, acts: [0, 0, 0, 0, 0], battles: 0 };
for (let i = 0; i < N; i++) {
  const run = R.newRun({ seed: 9000 + i, warband: AG.Data.WARBANDS[i % 4].id, difficulty: DIFF });
  const rng = new AG.RNG(i + 1);
  let steps = 0;
  while (!run.over && steps++ < 400) {
    if (!run.pending) {
      const opts = R.availableNodes(run);
      assert.ok(opts.length, 'map has a way forward');
      assert.ok(R.enterNode(run, rng.pick(opts).id));
      continue;
    }
    const p = run.pending;
    if (p.type === 'battle') {
      const r = playBattle(run);
      results.battles++;
      continue;
    }
    if (p.type === 'reward') {
      if (p.bossRelics && !p.bossRelicTaken) R.takeBossRelic(run, p.bossRelics[0]);
      const idx = rng.int(p.spoils.length);
      const sp = p.spoils[idx];
      let rid = null;
      if (sp.type === 'talent') rid = pickUnit(run, { talent: sp.talent });
      if (sp.type === 'promote') rid = pickUnit(run, { filter: 'promote' });
      if (!R.takeSpoil(run, idx, rid)) R.skipSpoils(run);
      R.completeNode(run);
      continue;
    }
    if (p.type === 'shop') {
      for (let k = 0; k < p.stock.length; k++) {
        const it = p.stock[k];
        if (!R.canBuy(run, it) || rng.chance(0.5)) continue;
        const rid = it.kind === 'talent' ? pickUnit(run, { talent: it.talent }) : null;
        R.buy(run, k, rid);
      }
      R.completeNode(run);
      continue;
    }
    if (p.type === 'rest') {
      if (run.banners < run.maxBanners || run.roster.some((u) => u.wounded)) assert.ok(R.rest(run, 'rest'));
      else {
        const rid = pickUnit(run, { filter: 'promote' });
        if (!rid || !R.rest(run, 'train', rid)) R.rest(run, 'rest');
      }
      R.completeNode(run);
      continue;
    }
    if (p.type === 'treasure') {
      R.takeTreasure(run);
      R.completeNode(run);
      continue;
    }
    if (p.type === 'event') {
      const choices = R.eventChoices(run).filter((c) => c.enabled);
      const c = rng.pick(choices);
      const rid = c.pick ? pickUnit(run, c.pick) : null;
      let res = R.chooseEvent(run, c.id, rid);
      if (res == null) res = R.chooseEvent(run, choices[choices.length - 1].id, null);
      assert.ok(res != null, 'event resolved');
      if (run.pending.type === 'event') R.completeNode(run);
      continue;
    }
    throw new Error('unknown pending ' + p.type);
  }
  assert.ok(run.over, 'run finished');
  JSON.parse(JSON.stringify(run));
  if (run.won) results.won++;
  else results.lost++;
  results.acts[run.won ? 4 : run.act]++;
  console.log(`run ${i} ${run.warband.padEnd(9)} ${run.won ? 'WON ' : 'lost'} act ${run.act} roster=${run.roster.length} relics=${run.relics.length} gold=${run.gold} battles=${run.stats.battles}`);
}
console.log(`runs: won ${results.won}, lost ${results.lost}; reached act1=${results.acts[1]} act2=${results.acts[2]} act3=${results.acts[3]} cleared=${results.acts[4]}; battles=${results.battles}`);
