/* Drive the real UI up many floors of a run: the draft, the opening, battle
   floors (Auto-deploy, skip to the result, retry or take an easier fight),
   events, the merchant and rewards. Fails on any page error.
   node tests/longrun.js [floors] [--mobile] */
'use strict';
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const floors = +(process.argv.find((a) => /^\d+$/.test(a)) || 10);
  const mobile = process.argv.includes('--mobile');
  const browser = await chromium.launch();
  const ctx = await browser.newContext(mobile
    ? { viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true, isMobile: true }
    : { viewport: { width: 1280, height: 860 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto('file://' + path.join(__dirname, '..', 'index.html'));
  await page.waitForTimeout(600);
  await page.evaluate(() => { try { localStorage.clear(); } catch (e) { /* ignore */ } });
  await page.getByRole('button', { name: 'New run' }).click();
  for (let i = 0; i < 5; i++) await page.locator('.offers .offer').first().click();
  await page.locator('.offer').filter({ hasText: 'Quartermaster' }).click();
  await page.getByRole('button', { name: 'Enter the tower' }).click();
  const log = [];
  let losses = 0, cleared = 0;
  for (let step = 0; step < floors * 12 && cleared < floors; step++) {
    const screen = await page.evaluate(() => (AG.App.view === 'battle' ? 'battle' : AG.App.run ? AG.App.run.screen : 'title'));
    if (screen === 'tower') {
      const f = await page.evaluate(() => ({ floor: AG.App.run.floor, type: AG.Run.currentFloor(AG.App.run).type }));
      log.push('floor ' + (f.floor + 1) + ' ' + f.type);
      if (f.type === 'battle') await page.locator('.fight.' + (losses >= 2 ? 'easy' : 'medium') + ' .btn.primary').click();
      else await page.locator('.floor-card .btn').first().click();
    } else if (screen === 'setup') {
      if (await page.getByRole('button', { name: 'Got it' }).count()) await page.getByRole('button', { name: 'Got it' }).click();
      await page.getByRole('button', { name: 'Auto-deploy' }).click();
      await page.getByRole('button', { name: /Begin battle/ }).click();
      await page.waitForTimeout(300);
      await page.getByRole('button', { name: /Skip to result/ }).click();
      await page.waitForSelector('.end-card', { timeout: 120000 });
      const won = await page.locator('.end-card .big.win').count();
      log.push('  ' + (won ? 'won' : 'lost') + ' ' + (await page.evaluate(() => AG.App.battle && AG.App.battle.s.encounter)));
      if (won) { losses = 0; cleared++; await page.locator('.end-card .btn.primary').click(); continue; }
      losses++;
      // Auto-deploy always fields the same army, so a stubborn fight gets a
      // test-only nudge of extra supply to keep the climb going.
      if (losses >= 4) await page.evaluate(() => { AG.App.run.supplyBonus += 3; });
      const another = page.locator('.end-card').getByRole('button', { name: 'Choose another fight' });
      if (losses === 2 && await another.count()) await another.click();
      else if (losses > 3 && await page.locator('.end-card').getByRole('button', { name: /Walk away|Choose another fight/ }).count()) {
        await page.locator('.end-card').getByRole('button', { name: /Walk away|Choose another fight/ }).click();
      } else await page.locator('.end-card .btn.primary').click();
      if (losses > 12) { log.push('  stuck'); break; }
    } else if (screen === 'reward') {
      const offers = page.locator('.offer:not(.taken):not(.gone)');
      if (await offers.count()) await offers.first().click();
      await page.waitForTimeout(100);
      await page.getByRole('button', { name: /^(Continue|Skip)$/ }).click();
    } else if (screen === 'event') {
      const cont = page.getByRole('button', { name: 'Climb on' });
      if (await cont.count()) { await cont.click(); cleared++; continue; }
      await page.locator('.choice:not([disabled])').first().click();
      await page.waitForTimeout(150);
      if (await page.locator('.modal .offer').count()) await page.locator('.modal .offer').first().click();
      log.push('  event');
    } else if (screen === 'shop') {
      const buyable = page.locator('.offers .offer:not(.gone)').first();
      if (await buyable.count()) await buyable.click();
      if (await page.locator('.modal .offer').count()) await page.locator('.modal .offer').first().click();
      await page.getByRole('button', { name: 'Leave and climb on' }).click();
      cleared++;
    } else if (screen === 'actIntro') {
      await page.getByRole('button', { name: 'Enter the tower' }).click();
    } else if (screen === 'victory') {
      log.push(screen);
      break;
    } else {
      errors.push('stuck on screen ' + screen);
      break;
    }
    await page.waitForTimeout(150);
  }
  console.log(log.join('\n'));
  await browser.close();
  if (errors.length) { console.log('ERRORS:\n' + errors.join('\n')); process.exit(1); }
  console.log('long run ok');
})().catch((e) => { console.error(e); process.exit(1); });
