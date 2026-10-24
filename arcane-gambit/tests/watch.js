/* Watch one battle play out in the terminal.
   node tests/watch.js <encounterId> unit[:talent[,talent]][@rune] ... [--boards] [--events]
   e.g. node tests/watch.js goblinSkirmish knight scout cleric */
'use strict';
const H = require('./harness');
const AG = H.load();

const args = process.argv.slice(2);
const encId = args[0] || 'goblinSkirmish';
const enc = AG.Encounters[encId];
if (!enc) { console.error('No encounter ' + encId); process.exit(1); }
const flags = new Set(args.filter((a) => a.startsWith('--')));
const units = args.slice(1).filter((a) => !a.startsWith('--'));
const entries = (units.length ? units : ['knight', 'scout', 'cleric']).map((spec) => {
  const [head, rune] = spec.split('@');
  const [def, tal] = head.split(':');
  return { def, talents: tal ? tal.split(',') : [], rune: rune || null };
});
const army = H.autoPlace(AG, enc, entries);
H.runBattle(AG, enc, army, { verbose: true, boards: flags.has('--boards'), events: flags.has('--events') });
