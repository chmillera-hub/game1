// Render individual frames for review: node stills.mjs 30 54.5 90 ...
import { createRequire } from "module";
import { execSync } from "child_process";
const { chromium } = createRequire(execSync("npm root -g").toString().trim() + "/")("playwright");
import { mkdirSync, writeFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const here = dirname(fileURLToPath(import.meta.url));
const out = resolve(here, "build/stills");
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on("pageerror", e => errors.push(String(e)));
page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
await page.goto("file://" + resolve(here, "film.html"));
await page.evaluate(() => document.fonts.ready);
for (const a of process.argv.slice(2)) {
  const t = parseFloat(a);
  const url = await page.evaluate(t => { render(t); return document.getElementById("c").toDataURL("image/jpeg", 0.9); }, t);
  writeFileSync(`${out}/t${t.toFixed(1).padStart(6, "0")}.jpg`, Buffer.from(url.split(",")[1], "base64"));
}
if (errors.length) console.log("ERRORS:\n" + errors.join("\n"));
await browser.close();
