// Renders <name>-explainer.html to an MP4 by stepping time frame by frame.
//   node explainer/render.mjs open-gate                -> explainer/video-only.mp4
//   node explainer/render.mjs open-gate --stills 3,10  -> PNG stills at those seconds
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
let playwright;
try {
    playwright = require('playwright');
} catch {
    playwright = require(path.join(process.execPath, '../../lib/node_modules/playwright'));
}

const dir = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const name = args[0] && !args[0].startsWith('--') ? args.shift() : 'open-gate';
const page_url = pathToFileURL(path.join(dir, `${name}-explainer.html`)).href + '?render';
const FPS = 30;
const stillsArg = args.indexOf('--stills');

const browser = await playwright.chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(page_url);
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.DURATION);

const grab = times => page.evaluate(ts => {
    const c = document.getElementById('stage');
    return ts.map(t => { window.render(t); return c.toDataURL('image/png'); });
}, times);
const decode = url => Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');

if (stillsArg !== -1) {
    const times = args[stillsArg + 1].split(',').map(Number);
    const outDir = args[stillsArg + 2] || dir;
    (await grab(times)).forEach((url, i) =>
        writeFileSync(path.join(outDir, `still-${times[i]}.png`), decode(url)));
    await browser.close();
    process.exit(0);
}

const silent = path.join(dir, 'video-only.mp4');
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS),
    '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', silent],
    { stdio: ['pipe', 'inherit', 'inherit'] });

const total = Math.round(duration * FPS);
for (let f = 0; f < total; f += 30) {
    const times = [];
    for (let k = f; k < Math.min(total, f + 30); k++) times.push(k / FPS);
    for (const url of await grab(times)) {
        if (!ff.stdin.write(decode(url))) await new Promise(r => ff.stdin.once('drain', r));
    }
    process.stdout.write(`\rframes ${Math.min(total, f + 30)}/${total}`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('\nwrote', silent);
