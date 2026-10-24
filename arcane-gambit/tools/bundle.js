/* Inline the stylesheet and every script into a single HTML file.
   node tools/bundle.js [out.html] [--fragment]
   --fragment leaves out the doctype/html/head/body wrapper (for hosts that
   add their own document skeleton). */
'use strict';
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const args = process.argv.slice(2);
const fragment = args.includes('--fragment');
const out = args.find((a) => !a.startsWith('--')) || path.join(root, 'dist', 'arcane-gambit.html');

const index = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const scripts = [...index.matchAll(/<script src="([^"]+)"><\/script>/g)].map((m) => m[1]);
const css = fs.readFileSync(path.join(root, 'css', 'style.css'), 'utf8');
const fonts = (index.match(/<link rel="stylesheet" href="(https:\/\/fonts[^"]+)">/) || [])[1];
const js = scripts.map((src) => '/* ' + src + ' */\n' + fs.readFileSync(path.join(root, src), 'utf8')).join('\n');
const safe = (s) => s.replace(/<\/(script|style)/gi, '<\\/$1');

const head = [
  '<title>Arcane Gambit</title>',
  '<meta name="claude:viewport-fit-sides" content="cover">',
  '<meta name="description" content="An auto-battling wizard chess roguelike: draft pieces within a supply budget, place them, and watch them think.">',
  '<link rel="preconnect" href="https://fonts.googleapis.com">',
  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
  fonts ? '<link rel="stylesheet" href="' + fonts + '">' : '',
  '<style>\n' + safe(css) + '\n</style>',
].filter(Boolean).join('\n');
const body = '<main id="app" aria-live="polite"></main>\n<script>\n' + safe(js) + '\n</script>';

const html = fragment
  ? head + '\n' + body + '\n'
  : '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + head + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n';

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, html);
console.log('wrote ' + out + ' (' + Math.round(html.length / 1024) + ' KB, ' + scripts.length + ' scripts)');
