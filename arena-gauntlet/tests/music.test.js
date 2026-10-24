// The background music's notation: every bar the right length, every note and chord real.
// Run: node tests/music.test.js
const assert = require('assert');
const AG = require('./load')(['music.js']);
const M = AG.Music;

assert.deepStrictEqual(M.check(), [], 'the tracks are written correctly');
for (const [mood, list] of Object.entries(M.MOODS)) {
  assert.ok(list.length >= 1, mood);
  for (const id of list) assert.ok(M.TRACKS[id], `${mood}: ${id}`);
}
assert.ok(M.MOODS.camp.length >= 2 && M.MOODS.battle.length >= 2, 'camp and battle each rotate between tracks');
for (const [id, T] of Object.entries(M.TRACKS)) {
  const loop = T.loopBars * T.bar * T.step;
  assert.ok(loop > 15 && loop < 90, `${id}: a loop of ${loop.toFixed(1)}s`);
}
console.log(`music: ${Object.keys(M.TRACKS).length} tracks check out (${Object.entries(M.TRACKS).map(([id, T]) => `${id} ${(T.loopBars * T.bar * T.step).toFixed(0)}s`).join(', ')})`);
