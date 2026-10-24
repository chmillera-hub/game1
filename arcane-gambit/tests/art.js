/* Every unit, and every alternate form a unit can take, has a figurine
   whose drawing runs cleanly. In the browser a drawing that throws falls
   back to a placeholder pawn without complaint, so check them here.
   node tests/art.js */
'use strict';
const path = require('path');
const H = require('./harness');
const AG = H.load();
for (const f of ['js/ui/pieces.js', 'js/art/player.js', 'js/art/enemy.js', 'js/art/enemy3.js']) {
  require(path.join(__dirname, '..', f));
}
const Art = AG.Art;

// Every art id the game can ask for: units, promotions, talent forms.
const ids = new Set(Object.keys(AG.Units));
for (const d of Object.values(AG.Units)) {
  const p = d.passives && d.passives.promotion;
  if (p && p.art) ids.add(p.art);
}
ids.add('druidBear');

const problems = [];
for (const id of ids) {
  const art = Art.artId(id);
  if (art === '_fallback') { problems.push(id + ': no drawing'); continue; }
  const P = new Art.Pen('pc-' + art);
  try { Art.pieces[art](P, Art.D); } catch (e) { problems.push(id + ': throws ' + e.message); continue; }
  const svg = P.out();
  if (!svg) problems.push(id + ': draws nothing');
  if (/NaN|undefined|Infinity/.test(svg)) problems.push(id + ': bad numbers in its path data');
  const open = (svg.match(/<clipPath/g) || []).length, close = (svg.match(/<\/clipPath>/g) || []).length;
  if (open !== close) problems.push(id + ': unbalanced clip paths');
}
// Drawings no unit uses are probably leftovers.
const unused = Object.keys(Art.pieces).filter((k) => k !== '_fallback' && !ids.has(k) &&
  !Object.values(Art.alias).includes(k));
for (const k of unused) problems.push(k + ': drawing not used by any unit');

console.log(ids.size + ' figurines checked' + (problems.length ? ', ' + problems.length + ' problems:\n  ' + problems.join('\n  ') : ', all draw cleanly'));
process.exit(problems.length ? 1 : 0);
