// Registry of all vignettes: merges every v_*.js module in this folder.
'use strict';
const fs = require('fs');
const path = require('path');
const all = {};
for (const f of fs.readdirSync(__dirname).sort()) {
  if (!/^v_.*\.js$/.test(f)) continue;
  Object.assign(all, require(path.join(__dirname, f)));
}
module.exports = all;
