/* Drive the real UI through many floors of a run: battles (re-using the
   last army, skipping to the result), events, shops, camps and rewards.
   Fails on any page error. node tests/longrun.js [floors] [--mobile] */
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
  await page.getByRole('button', { name: 'New run' }).click();
  await page.getByRole('button', { name: /Casual/ }).click();
  await page.locator('.offer').filter({ hasText: 'Quartermaster' }).click();
  await page.getByRole('button', { name: 'To the map' }).click();
  const log = [];
  let firstBattle = true;
  for (let step = 0; step < floors * 4 && log.filter((l) => l.startsWith('floor')).length < floors; step++) {
    const screen = await page.evaluate(() => (AG.App.view === 'battle' ? 'battle' : AG.App.run ? AG.App.run.screen : 'title'));
    if (screen === 'map') {
      await page.locator('.mnode.reach').first().click();
      const t = await page.evaluate(() => AG.App.run.map.nodes[AG.App.run.pos].type);
      log.push('floor ' + t);
    } else if (screen === 'setup') {
      if (await page.getByRole('button', { name: 'Got it' }).count()) await page.getByRole('button', { name: 'Got it' }).click();
      const last = page.getByRole('button', { name: /Use last army/ });
      if (!firstBattle && await last.count()) await last.click();
      else {
        // Fill the board from the roster: tap a card, then the first free deploy square.
        for (let k = 0; k < 6; k++) {
          const cards = page.locator('.rcard:not(.cant)');
          if (!(await cards.count())) break;
          await cards.nth(k % (await cards.count())).click();
          const free = await page.evaluate(() => {
            const cells = Array.from(document.querySelectorAll('.cell.deploy'));
            for (const c of cells) {
              const r = c.getBoundingClientRect();
              const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
              if (el && !el.closest('.token')) return [+c.dataset.x, +c.dataset.y];
            }
            return null;
          });
          if (!free) break;
          await page.locator('.cell[data-x="' + free[0] + '"][data-y="' + free[1] + '"]').click();
        }
      }
      firstBattle = false;
      const begin = page.getByRole('button', { name: /Begin battle/ });
      if (await begin.isDisabled()) { await page.getByRole('button', { name: 'Clear board' }).click(); continue; }
      await begin.click();
      await page.waitForTimeout(300);
      await page.getByRole('button', { name: /Skip to result/ }).click();
      await page.waitForSelector('.end-card', { timeout: 120000 });
      const won = await page.locator('.end-card .big.win').count();
      log.push('  ' + (won ? 'won' : 'lost') + ' ' + (await page.evaluate(() => AG.App.battle && AG.App.battle.s.encounter)));
      await page.locator('.end-card .btn.primary').click();
    } else if (screen === 'reward') {
      const offers = page.locator('.offer:not(.taken):not(.gone)');
      if (await offers.count()) await offers.first().click();
      await page.waitForTimeout(100);
      const cont = page.getByRole('button', { name: /^(Continue|Skip)$/ });
      await cont.click();
    } else if (screen === 'event') {
      const cont = page.getByRole('button', { name: 'Continue' });
      if (await cont.count()) { await cont.click(); continue; }
      await page.locator('.choice:not([disabled])').first().click();
      await page.waitForTimeout(150);
      if (await page.locator('.modal .offer').count()) await page.locator('.modal .offer').first().click();
      log.push('  event');
    } else if (screen === 'shop') {
      const buyable = page.locator('.offers .offer:not(.gone)').first();
      if (await buyable.count()) await buyable.click();
      if (await page.locator('.modal .offer').count()) await page.locator('.modal .offer').first().click();
      await page.getByRole('button', { name: 'Leave' }).click();
    } else if (screen === 'rest') {
      const brk = page.getByRole('button', { name: 'Break camp' });
      if (await brk.count()) { await brk.click(); continue; }
      await page.locator('.offer').filter({ hasText: 'Recover' }).click();
    } else if (screen === 'actIntro') {
      await page.getByRole('button', { name: 'To the map' }).click();
    } else if (screen === 'gameover' || screen === 'victory') {
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
