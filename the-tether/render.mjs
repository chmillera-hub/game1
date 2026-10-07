// Render film.html to MP4: N parallel headless pages each encode a slice of
// frames, then the slices are concatenated and muxed with build/mix.wav.
//   node render.mjs [fps=30] [workers=4] [start=0] [end=duration]
import { createRequire } from "module";
import { execSync, spawn } from "child_process";
import { mkdirSync, writeFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";
const { chromium } = createRequire(execSync("npm root -g").toString().trim() + "/")("playwright");

const here = dirname(fileURLToPath(import.meta.url));
const build = resolve(here, "build");
const [fps = 30, workers = 4, t0arg, t1arg] = process.argv.slice(2).map(Number);
mkdirSync(build + "/segments", { recursive: true });

const browser = await chromium.launch();
const probe = await browser.newPage();
await probe.goto("file://" + resolve(here, "film.html"));
const duration = await probe.evaluate(() => window.DURATION);
await probe.close();
const f0 = Math.round((t0arg || 0) * fps), f1 = Math.round((t1arg || duration) * fps);
const per = Math.ceil((f1 - f0) / workers);
const started = Date.now();

async function work(w) {
  const a = f0 + w * per, b = Math.min(f1, a + per);
  const out = `${build}/segments/seg${w}.mp4`;
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-tune", "film", "-pix_fmt", "yuv420p", out], { stdio: ["pipe", "inherit", "inherit"] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on("pageerror", e => console.error("pageerror", e));
  await page.goto("file://" + resolve(here, "film.html"));
  await page.evaluate(() => document.fonts.ready);
  for (let f = a; f < b; f++) {
    const url = await page.evaluate(t => { render(t); return document.getElementById("c").toDataURL("image/jpeg", 0.96); }, f / fps);
    if (!ff.stdin.write(Buffer.from(url.slice(url.indexOf(",") + 1), "base64")))
      await new Promise(r => ff.stdin.once("drain", r));
    if (w === 0 && (f - a) % 300 === 0) console.log(`worker0 ${f - a}/${b - a}  ${((Date.now() - started) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await page.close();
  return out;
}
const segs = await Promise.all([...Array(workers).keys()].map(work));
await browser.close();
writeFileSync(`${build}/segments/list.txt`, segs.map(s => `file '${s}'`).join("\n"));
const name = t0arg || t1arg ? `${build}/preview_${t0arg || 0}-${t1arg || duration}.mp4` : resolve(here, "the-tether.mp4");
const ss = (f0 / fps).toFixed(3), len = ((f1 - f0) / fps).toFixed(3);
execSync(`ffmpeg -y -loglevel error -f concat -safe 0 -i ${build}/segments/list.txt -ss ${ss} -t ${len} -i ${build}/mix.wav ` +
  `-map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest "${name}"`);
console.log(`wrote ${name} in ${((Date.now() - started) / 1000).toFixed(0)}s`);
