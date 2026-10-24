/* Browser smoke test: plays through the title, a new run, the map, the war
   room, a battle and the reward screen, failing on any page error.
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
  await page.getByRole('button', { name: /Standard/ }).click();
  await page.waitForTimeout(300);
  await shot('02-boon');
  await page.locator('.offer').filter({ hasText: 'Quartermaster' }).click();
  await page.waitForTimeout(300);
  await shot('03-act');
  await page.getByRole('button', { name: 'To the map' }).click();
  await page.waitForTimeout(500);
  await shotFull('04-map');

  // Enter the first reachable battle.
  await page.locator('.mnode.reach').first().click();
  await page.waitForTimeout(600);
  await shotFull('05-setup-empty');

  // Place three units: tap a card then a deploy square.
  const cards = ['Knight', 'Scout', 'Cleric'];
  for (const name of cards) {
    await page.locator('.rcard').filter({ hasText: name }).first().click();
    const cell = page.locator('.cell.deploy').filter({ hasNot: page.locator('xxx') });
    const n = await cell.count();
    // Pick a free deploy square near the middle.
    const free = await page.evaluate(() => {
      const taken = new Set(Array.from(document.querySelectorAll('.token.p')).map((t) => t.style.transform));
      const cells = Array.from(document.querySelectorAll('.cell.deploy'));
      return cells.map((c, i) => ({ i, x: +c.dataset.x, y: +c.dataset.y })).filter((c) => true);
    });
    const w = await page.evaluate(() => document.querySelectorAll('.files span').length);
    const order = free.sort((a, b) => a.y - b.y || Math.abs(a.x - (w - 1) / 2) - Math.abs(b.x - (w - 1) / 2));
    let placed = false;
    for (const c of order) {
      // Ask the game which squares are taken (screen hit-tests miss squares that are scrolled out of view).
      const occupied = await page.evaluate(([x, y]) => {
        const run = AG.App.run;
        if (run.battle.formation.some((e) => e.x === x && e.y === y)) return true;
        const enc = AG.Encounters[run.battle.enc];
        return AG.parseBoard(enc.map, enc.legend).spawns.some((sp) => sp.x === x && sp.y === y);
      }, [c.x, c.y]);
      if (occupied) continue;
      await page.locator('.cell[data-x="' + c.x + '"][data-y="' + c.y + '"]').click();
      placed = true;
      break;
    }
    if (!placed) errors.push('could not place ' + name + ' (deploy squares ' + n + ')');
    await page.waitForTimeout(150);
  }
  await shotFull('06-setup-placed');

  // Give the Knight a talent through the inspector.
  await page.locator('.token.p').first().click();
  await page.waitForTimeout(200);
  if (mobile) {
    await page.getByRole('button', { name: /Upgrades/ }).click();
    await page.waitForTimeout(250);
    await shot('07-loadout');
    await page.locator('.modal .close').click();
  } else {
    await shot('07-loadout');
  }

  await page.getByRole('button', { name: /Begin battle/ }).click();
  await page.waitForTimeout(2500);
  await shot('08-battle');
  await page.getByRole('button', { name: '4×' }).click();
  await page.waitForTimeout(3500);
  await shot('09-battle-later');
  await page.getByRole('button', { name: /Skip to result/ }).click();
  await page.waitForSelector('.end-card', { timeout: 60000 });
  await page.waitForTimeout(400);
  await shot('10-end');
  const won = await page.locator('.end-card .big.win').count();
  await page.locator('.end-card .btn.primary').click();
  await page.waitForTimeout(500);
  await shotFull(won ? '11-reward' : '11-retry');

  await browser.close();
  if (errors.length) {
    console.log('ERRORS:\n' + errors.join('\n'));
    process.exit(1);
  }
  console.log('smoke ok (' + (won ? 'won' : 'lost') + '), screenshots in ' + outDir);
})().catch((e) => { console.error(e); console.log('ERRORS SO FAR:\n' + (globalThis.__errors || []).join('\n')); process.exit(1); });
