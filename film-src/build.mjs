// Assemble the film from src/ into one self-contained HTML page.
//   node film-src/build.mjs            -> ../the-last-thing-on-my-mind.html (full document)
//   node film-src/build.mjs --fragment -> prints the body-only fragment (for hosts that add their own <html>/<head>)
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, 'src');
const head = readFileSync(join(src, '00-head.html'), 'utf8');
const scripts = readdirSync(src).filter(f => f.endsWith('.js')).sort()
  .map(f => `// ---- ${f}\n${readFileSync(join(src, f), 'utf8')}`).join('\n');
const fragment = `${head}<script>\n"use strict";\n${scripts}\n</script>\n`;

if (process.argv.includes('--fragment')) { process.stdout.write(fragment); process.exit(0); }

const cut = fragment.indexOf('</style>') + '</style>'.length;
const page = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="description" content="A short film in light and sound: ninety-nine years, one bed, and the emotional family that lived inside me the whole time.">
${fragment.slice(0, cut)}
</head>
<body>
${fragment.slice(cut)}
</body>
</html>
`;
const out = join(here, '..', 'the-last-thing-on-my-mind.html');
writeFileSync(out, page);
console.log(`built ${out} (${page.length} bytes)`);
