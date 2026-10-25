/* Browser smoke test: plays through the title, the draft, the opening, the
   tower, the war room (auto-deploy), a battle and its result, failing on any
   page error.
   node tests/smoke.js [outDir] [--mobile] */
'use strict';
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const outDir = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : path.join(__dirname, '..', '..', 'shots');
  const mobile = process.argv.includes('--mobile');
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext(mobile
    ? { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true }
    : { viewport: { width: 1360, height: 900 } });
  const page = await ctx.newPage();
  const errors = (globalThis.__errors = []);
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message + '\n' + (e.stack || '')));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  const url = 'file://' + path.join(__dirname, '..', 'index.html');
  const tag = mobile ? 'm-' : 'd-';
  const overflow = async (name) => {
    const o = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, w: window.innerWidth }));
    if (o.sw > o.w + 1) errors.push('horizontal overflow on ' + name + ': ' + o.sw + ' > ' + o.w);
  };
  const shot = async (name) => { await overflow(name); return page.screenshot({ path: path.join(outDir, tag + name + '.png'), fullPage: false }); };
  const shotFull = async (name) => { await overflow(name); return page.screenshot({ path: path.join(outDir, tag + name + '.png'), fullPage: true }); };

  await page.goto(url);
  await page.waitForTimeout(2500);
  await shot('01-title');

  await page.getByRole('button', { name: 'New run' }).click();
  await page.waitForTimeout(300);
  await shot('02-draft');
  // Draft five units: take the first offer each time.
  for (let i = 0; i < 5; i++) {
    await page.locator('.offers .offer').first().click();
    await page.waitForTimeout(200);
  }
  await shotFull('03-boon');
  await page.locator('.offer').filter({ hasText: 'Quartermaster' }).click();
  await page.waitForTimeout(300);
  await shot('04-act');
  await page.getByRole('button', { name: 'Enter the tower' }).click();
  await page.waitForTimeout(500);
  await shotFull('05-tower');

  // Take the medium fight on the first floor.
  await page.locator('.fight.medium .btn.primary').click();
  await page.waitForTimeout(600);
  await shotFull('06-setup-empty');
  await page.getByRole('button', { name: 'Auto-deploy' }).click();
  await page.waitForTimeout(300);
  const placed = await page.evaluate(() => AG.App.run.battle.formation.length);
  if (!placed) errors.push('auto-deploy placed nothing');
  await shotFull('07-setup-placed');

  // Open a placed piece's loadout.
  await page.locator('.token.p').first().click();
  await page.waitForTimeout(200);
  if (mobile) {
    await page.getByRole('button', { name: /Upgrades/ }).click();
    await page.waitForTimeout(250);
    await shot('08-loadout');
    await page.locator('.modal .close').click();
  } else {
    await shot('08-loadout');
  }

  await page.getByRole('button', { name: /Begin battle/ }).click();
  await page.waitForTimeout(2500);
  await shot('09-battle');
  await page.getByRole('button', { name: '4×' }).click();
  await page.waitForTimeout(3500);
  await shot('10-battle-later');
  await page.getByRole('button', { name: /Skip to result/ }).click();
  await page.waitForSelector('.end-card', { timeout: 60000 });
  await page.waitForTimeout(400);
  await shot('11-end');
  const won = await page.locator('.end-card .big.win').count();
  await page.locator('.end-card .btn.primary').click();
  await page.waitForTimeout(500);
  await shotFull(won ? '12-reward' : '12-retry');
  if (won) {
    await page.locator('.offers .offer').first().click();
    await page.getByRole('button', { name: 'Continue' }).click();
    await page.waitForTimeout(400);
    const floor = await page.evaluate(() => AG.App.run.floor);
    if (floor !== 1) errors.push('expected floor 2 after the first win, got ' + (floor + 1));
    await shotFull('13-tower-2');
  }

  await browser.close();
  if (errors.length) {
    console.log('ERRORS:\n' + errors.join('\n'));
    process.exit(1);
  }
  console.log('smoke ok (' + (won ? 'won' : 'lost') + '), screenshots in ' + outDir);
})().catch((e) => { console.error(e); console.log('ERRORS SO FAR:\n' + (globalThis.__errors || []).join('\n')); process.exit(1); });
