#!/usr/bin/env node
/* ==========================================================================
   build.js — bundle the film into ONE self-contained HTML file.

   node tools/build.js                       → ../the-hikers-and-the-flower.html
   node tools/build.js --out some/file.html
   node tools/build.js --fragment --out f.html   (no <!DOCTYPE>/<html>/<head>/<body>
                                                  wrappers — for hosts that add their own)
   Fonts are inlined as base64 data URIs; every <script src> is inlined.
   ========================================================================== */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const flag = (k) => args.includes('--' + k);
const val = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 && args[i + 1] ? args[i + 1] : d; };
const out = path.resolve(val('out', path.join(root, '..', 'the-hikers-and-the-flower.html')));
const fragment = flag('fragment');

let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

// 1. fonts → data URIs
html = html.replace(/url\((fonts\/[^)]+\.woff2)\)/g, (m, rel) => {
  const buf = fs.readFileSync(path.join(root, rel));
  return `url(data:font/woff2;base64,${buf.toString('base64')})`;
});

// 2. scripts → inline
const missing = [];
html = html.replace(/<script src="([^"]+)"><\/script>/g, (m, src) => {
  const f = path.join(root, src);
  if (!fs.existsSync(f)) { missing.push(src); return `<!-- missing: ${src} -->`; }
  const code = fs.readFileSync(f, 'utf8').replace(/<\/script/gi, '<\\/script');
  return `<script>/* ${src} */\n${code}\n</script>`;
});
html = html.replace(/<!-- \/?BUILD:SCRIPTS -->\n?/g, '');

// 3. optional fragment form: drop document wrappers, keep <title> first
if (fragment) {
  const title = (html.match(/<title>[\s\S]*?<\/title>/) || [''])[0];
  html = html
    .replace(/<!DOCTYPE html>\s*/i, '')
    .replace(/<html[^>]*>\s*/i, '')
    .replace(/<\/html>\s*/i, '')
    .replace(/<head>\s*/i, '')
    .replace(/<\/head>\s*/i, '')
    .replace(/<body>\s*/i, '')
    .replace(/<\/body>\s*/i, '')
    .replace(/<meta charset="UTF-8">\s*/i, '')
    .replace(/<meta name="viewport"[^>]*>\s*/i, '')
    .replace(/<title>[\s\S]*?<\/title>\s*/, '');
  html = title + '\n' + html;
}

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, html);
const kb = (fs.statSync(out).size / 1024).toFixed(0);
console.log(`built ${path.relative(process.cwd(), out)} (${kb} KB)${fragment ? ' [fragment]' : ''}`);
if (missing.length) console.log('missing (skipped): ' + missing.join(', '));
