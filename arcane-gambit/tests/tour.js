/* Visit every screen of a run in the browser by driving the run state
   directly, screenshot each one, and fail on page errors or sideways
   overflow. node tests/tour.js [outDir] [--mobile] */
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
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message + '\n' + (e.stack || '')));
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errors.push('console ' + m.type() + ': ' + m.text()); });
  const tag = (mobile ? 'm' : 'd') + '-tour-';
  const shot = async (name, full) => {
    const o = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, w: window.innerWidth }));
    if (o.sw > o.w + 1) errors.push('horizontal overflow on ' + name + ': ' + o.sw + ' > ' + o.w);
    await page.screenshot({ path: path.join(outDir, tag + name + '.png'), fullPage: !!full });
  };
  await page.goto('file://' + path.join(__dirname, '..', 'index.html'));
  await page.waitForTimeout(800);
  // Start a run programmatically.
  await page.evaluate(() => {
    const App = AG.App;
    App.run = AG.Run.newRun({ seed: 1234, mode: 'standard' });
    App.mode = 'run';
    AG.Run.takeBoon(App.run, 'armory');
    App.run.units.push('pyromancer', 'golem', 'frostWitch', 'chronomancer', 'necromancer', 'druid');
    App.run.relics.push('warBanner', 'ironRations', 'hourglass');
    App.run.gold = 300;
    App.go('actIntro');
  });
  await page.waitForTimeout(300);
  await shot('act-intro');
  // Each kind of map node.
  for (const type of ['shop', 'rest', 'event', 'treasure']) {
    await page.evaluate((type) => {
      const App = AG.App;
      const run = App.run;
      const node = Object.values(run.map.nodes).find((n) => n.r === 1) || Object.values(run.map.nodes)[0];
      node.type = type;
      run.pos = null;
      AG.Run.enter(run, node.id);
      App.view = null;
      App.render();
    }, type);
    await page.waitForTimeout(300);
    await shot(type, true);
    if (type === 'shop') {
      await page.locator('.offer').filter({ hasText: 'Drill instructor' }).click();
      await page.waitForTimeout(200);
      await shot('shop-train-picker');
      await page.locator('.modal .offer').first().click();
      await page.waitForTimeout(200);
      await shot('shop-after', true);
    }
    if (type === 'event') {
      const btn = page.locator('.choice:not([disabled])').first();
      await btn.click();
      await page.waitForTimeout(300);
      if (await page.locator('.modal .offer').count()) await page.locator('.modal .offer').first().click();
      await page.waitForTimeout(300);
      await shot('event-result', true);
    }
  }
  // Boss war room with the danger overlay and a selected enemy.
  await page.evaluate(() => {
    const App = AG.App;
    const run = App.run;
    run.act = 2;
    AG.Run.startBattle(run, 'lichVault', 'boss', null);
    run.battle.formation = [];
    App.view = null;
    App.render();
  });
  await page.waitForTimeout(400);
  await page.getByRole('button', { name: 'Show enemy reach' }).click();
  await page.waitForTimeout(200);
  await page.locator('.token.e').nth(1).click();
  await page.waitForTimeout(300);
  if (mobile) await page.locator('.modal .close').click().catch(() => {});
  await shot('boss-setup', true);
  // Army view and help.
  await page.getByRole('button', { name: 'Army' }).click();
  await page.waitForTimeout(300);
  await shot('army');
  await page.locator('.modal .close').click();
  await page.locator('.hud button[aria-label="How to play"]').click();
  await page.waitForTimeout(300);
  await shot('help');
  await page.locator('.modal .close').click();
  // Game over and victory.
  for (const sc of ['gameover', 'victory']) {
    await page.evaluate((sc) => { AG.App.run.screen = sc; AG.App.view = null; AG.App.render(); }, sc);
    await page.waitForTimeout(300);
    await shot(sc);
  }
  // Skirmish picker.
  await page.evaluate(() => AG.App.openSandbox());
  await page.waitForTimeout(300);
  await shot('sandbox', true);
  await page.locator('.enc-item').filter({ hasText: 'Mad Grandmaster' }).click();
  await page.waitForTimeout(400);
  await shot('sandbox-setup', true);
  await browser.close();
  const real = errors.filter((e) => !/playback error/.test(e));
  if (real.length) { console.log('ERRORS:\n' + real.join('\n')); process.exit(1); }
  console.log('tour ok, screenshots in ' + outDir);
})().catch((e) => { console.error(e); process.exit(1); });
