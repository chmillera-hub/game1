// Build: inline the CSS and JS into the page shell.
//   node mobius-lab/build.mjs              -> ../mobius-lab.html (standalone page)
//   node mobius-lab/build.mjs --artifact   -> also dist/mobius-lab.artifact.html (fragment for claude.ai artifacts)
import fs from 'fs';
import path from 'path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const src = f => fs.readFileSync(path.join(dir, 'src', f), 'utf8');
const order = ['core.js', 'ch1_finger.js', 'ch2_scissors.js', 'ch2b_tape.js', 'ch3_spin.js', 'ch4_music.js', 'ch5_gears.js', 'ch6_forge.js', 'ch7_ribbon.js', 'ch8_drain.js', 'verdict.js', 'main.js'];
const js = order.map(f => `/* ---- ${f} ---- */\n` + src(f)).join('\n');
if (js.includes('</script')) throw new Error('JS contains </script');
const frag = src('shell.html').replace('/*__CSS__*/', () => src('styles.css')).replace('//__JS__', () => js);
const cut = frag.indexOf('<header class="masthead">');
const full = `<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n${frag.slice(0, cut)}</head>\n<body>\n${frag.slice(cut)}</body>\n</html>\n`;
fs.writeFileSync(path.join(dir, '..', 'mobius-lab.html'), full);
if (process.argv.includes('--artifact')) {
  fs.mkdirSync(path.join(dir, 'dist'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'dist', 'mobius-lab.artifact.html'), frag);
}
console.log(`built mobius-lab.html (${(full.length / 1024).toFixed(1)} KB)`);
