// Loads the browser game scripts into Node for headless tests.
const path = require('path');

const FILES = ['rng.js', 'data.js', 'engine.js', 'ai.js', 'run.js'];

module.exports = function load(files = FILES) {
  for (const f of files) {
    const p = path.join(__dirname, '..', 'js', f);
    try {
      require(p);
    } catch (e) {
      if (e.code === 'MODULE_NOT_FOUND' && e.message.includes(f)) continue;
      throw e;
    }
  }
  return globalThis.AG;
};
