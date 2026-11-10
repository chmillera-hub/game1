// Tables from the balance lab's rows. Run: node tests/balance-report.js [file ...]
//   BY=primary   one more table, by mission       MIN=20   hide cells with fewer rows
const fs = require('fs');
const files = process.argv.slice(2).length ? process.argv.slice(2) : ['balance-rows.jsonl'];
const rows = [];
for (const f of files) for (const line of fs.readFileSync(f, 'utf8').split('\n')) if (line.trim()) rows.push(JSON.parse(line));
const MIN = +process.env.MIN || 1;

const pct = (a, b) => (b ? String(Math.round((100 * a) / b)).padStart(3) + '%' : '   -');
const avg = (list, f) => (list.length ? list.reduce((t, r) => t + f(r), 0) / list.length : 0);
const TIER_ORDER = ['easy', 'medium', 'elite', 'boss', 'mega'];
const cands = [...new Set(rows.map((r) => r.cand))];

function table(title, groups) {
  console.log('\n' + title);
  console.log('  ' + 'army'.padEnd(14) + groups.map((g) => g.name.padStart(15)).join(''));
  console.log('  ' + ''.padEnd(14) + groups.map(() => '   win full   n'.padStart(15)).join(''));
  for (const c of cands) {
    const cells = groups.map((g) => {
      const list = g.rows.filter((r) => r.cand === c);
      if (list.length < MIN) return ''.padStart(15);
      return ` ${pct(list.filter((r) => r.won).length, list.length)} ${pct(list.filter((r) => r.full).length, list.length)} ${String(list.length).padStart(4)}`.padStart(15);
    });
    console.log('  ' + c.padEnd(14) + cells.join(''));
  }
}

// Win and collect-everything rates, by tier and act.
for (const tier of TIER_ORDER) {
  const list = rows.filter((r) => r.tier === tier);
  if (!list.length) continue;
  const acts = [...new Set(list.map((r) => r.act))].sort();
  table(`${tier.toUpperCase()}: wins and "collected everything", by act`, acts.map((a) => ({ name: 'act ' + a, rows: list.filter((r) => r.act === a) })).concat([{ name: 'all', rows: list }]));
}

// The shape of each army, and how much of everything on offer it brought home.
console.log('\nArmies: units fielded, average level, Supply used, share of everything on offer collected, units lost in wins');
for (const c of cands) {
  const list = rows.filter((r) => r.cand === c);
  const wins = list.filter((r) => r.won);
  console.log(`  ${c.padEnd(14)} units ${avg(list, (r) => r.n).toFixed(1).padStart(4)}  level ${avg(list, (r) => +r.lv).toFixed(2)}  Supply ${avg(list, (r) => r.used).toFixed(1).padStart(4)}/${avg(list, (r) => r.supply).toFixed(1)}  haul ${Math.round(100 * avg(list, (r) => r.haul))}%  lost ${wins.length ? avg(wins, (r) => r.lost).toFixed(1) : '-'} of ${wins.length ? avg(wins, (r) => r.units).toFixed(1) : '-'}  turns ${wins.length ? avg(wins, (r) => r.turns).toFixed(0) : '-'}`);
}

// Bonus goals: how often each kind is met in a win, by army.
const goalKinds = [...new Set(rows.flatMap((r) => r.goalTypes))].sort();
console.log('\nBonus goals met in wins (and building gold all collected)');
console.log('  ' + 'army'.padEnd(14) + goalKinds.map((g) => g.padStart(11)).join('') + 'gold'.padStart(11));
for (const c of cands) {
  const wins = rows.filter((r) => r.cand === c && r.won);
  const cells = goalKinds.map((g) => {
    let a = 0;
    let b = 0;
    for (const r of wins) r.goalTypes.forEach((t, i) => {
      if (t !== g) return;
      b++;
      if (r.met[i]) a++;
    });
    return pct(a, b).padStart(11);
  });
  const withGold = wins.filter((r) => r.goldTotal > 0);
  console.log('  ' + c.padEnd(14) + cells.join('') + pct(withGold.filter((r) => r.goldGot >= r.goldTotal).length, withGold.length).padStart(11));
}

if (process.env.BY === 'primary') {
  for (const tier of ['medium', 'elite']) {
    const list = rows.filter((r) => r.tier === tier);
    const kinds = [...new Set(list.map((r) => r.primary))].sort();
    table(`${tier.toUpperCase()}: by mission`, kinds.map((k) => ({ name: k, rows: list.filter((r) => r.primary === k) })));
  }
}
if (process.env.BY === 'enc') {
  for (const tier of TIER_ORDER) {
    const list = rows.filter((r) => r.tier === tier);
    const kinds = [...new Set(list.map((r) => r.enc))].sort();
    for (let i = 0; i < kinds.length; i += 5) table(`${tier.toUpperCase()}: by enemy`, kinds.slice(i, i + 5).map((k) => ({ name: k.slice(0, 14), rows: list.filter((r) => r.enc === k) })));
  }
}
