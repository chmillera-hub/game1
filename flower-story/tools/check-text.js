#!/usr/bin/env node
/* ==========================================================================
   check-text.js — verify every story line in docs/SCRIPT.md appears verbatim
   in the scene file that owns it. Lines marked invented/optional are skipped.
   node tools/check-text.js        (exit 1 if anything is missing)
   ========================================================================== */
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const script = fs.readFileSync(path.join(root, 'docs/SCRIPT.md'), 'utf8');

// scene id → file content
const files = fs.readdirSync(path.join(root, 'scenes')).filter((f) => f.endsWith('.js'));
const byId = {};
for (const f of files) {
  const src = fs.readFileSync(path.join(root, 'scenes', f), 'utf8');
  const m = src.match(/id:\s*'([^']+)'/);
  if (m) byId[m[1]] = { file: f, src: src.replace(/\\'/g, "'").replace(/\\u2019/g, '’').replace(/\\u2014/g, '—').replace(/\\u2026/g, '…') };
}

const sections = script.split(/\n## /).slice(1);
let missing = 0, checked = 0;
for (const sec of sections) {
  const head = sec.split('\n')[0];
  const m = head.match(/^(\d\d) · ([\w-]+)/);
  if (!m) continue;
  const id = m[2];
  const scene = byId[id];
  const required = [];
  let skipNext = false;
  for (const line of sec.split('\n').slice(1)) {
    if (skipNext) { skipNext = /·\s*$/.test(line.trim()); continue; }
    if (/invented|Optional|optional/.test(line)) { skipNext = /:\s*$/.test(line.trim()); continue; }
    if (!/^\s*-|Narration|Inner voice|Title text|Dialogue|“|"/.test(line)) continue;
    const quotes = line.match(/"([^"]+)"/g);
    if (!quotes) continue;
    for (const q of quotes) {
      const text = q.slice(1, -1).trim();
      if (text.length < 4 || /^Embarrassment’s Flowers$/.test(text)) continue;
      required.push(text);
    }
  }
  if (!required.length) continue;
  if (!scene) { console.log(`✗ ${id}: no scene file`); missing += required.length; continue; }
  const lost = [];
  for (const r of required) {
    checked++;
    // tolerate the text being split across bubbles/lines on sentence boundaries
    const pieces = r.split(/(?<=[.!?…—])\s+/).filter(Boolean);
    const ok = scene.src.includes(r) || pieces.every((p) => scene.src.includes(p.replace(/^…/, '').replace(/…$/, '').trim()));
    if (!ok) lost.push(r);
  }
  if (lost.length) {
    missing += lost.length;
    console.log(`✗ ${id} (${scene.file}): ${lost.length} line(s) not found verbatim`);
    for (const l of lost) console.log('    · ' + l);
  } else console.log(`✓ ${id} (${required.length} lines)`);
}
console.log(`${checked} lines checked, ${missing} missing`);
process.exit(missing ? 1 : 0);
