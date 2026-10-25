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
  const render = () => page.evaluate(() => { AG.App.view = null; AG.App.render(); });
  await page.goto('file://' + path.join(__dirname, '..', 'index.html'));
  await page.waitForTimeout(800);
  await page.evaluate(() => { try { localStorage.clear(); } catch (e) { /* ignore */ } });

  // The draft, two picks in.
  await page.evaluate(() => {
    const App = AG.App;
    App.run = AG.Run.newRun({ seed: 1234 });
    App.mode = 'run';
    for (let i = 0; i < 2; i++) AG.Run.draftPick(App.run, App.run.draft.options[0]);
    App.go('draft');
  });
  await page.waitForTimeout(300);
  await shot('draft', true);
  await page.evaluate(() => {
    const run = AG.App.run;
    while (run.draft) AG.Run.draftPick(run, run.draft.options[0]);
    AG.App.go('boon');
  });
  await page.waitForTimeout(300);
  await shot('boon', true);
  await page.evaluate(() => {
    const App = AG.App;
    AG.Run.takeBoon(App.run, 'armory');
    App.run.units.push('pyromancer', 'golem', 'frostWitch', 'necromancer', 'druid');
    App.run.relics.push('warBanner', 'ironRations', 'hourglass');
    App.run.gold = 300;
    App.go('actIntro');
  });
  await page.waitForTimeout(300);
  await shot('act-intro');
  await page.getByRole('button', { name: 'Enter the tower' }).click();
  await page.waitForTimeout(300);
  await shot('tower', true);
  // Answer the pickers an event choice or a shop service opens.
  async function resolvePicks() {
    for (let k = 0; k < 3; k++) {
      if (await page.locator('.modal .offer').count()) await page.locator('.modal .offer').first().click();
      else if (await page.locator('.modal .opt').count()) await page.locator('.modal .opt').first().click();
      else break;
      await page.waitForTimeout(200);
    }
  }
  // The event and the shop floors.
  for (const floor of [3, 4]) {
    await page.evaluate((floor) => {
      const run = AG.App.run;
      run.floor = floor;
      AG.Run.prepareFloor(run);
      run.screen = 'tower';
    }, floor);
    await render();
    await page.waitForTimeout(250);
    await shot('tower-floor' + (floor + 1), true);
    await page.locator('.floor-card .btn.primary').click();
    await page.waitForTimeout(300);
    const type = floor === 3 ? 'event' : 'shop';
    await shot(type, true);
    if (type === 'shop') {
      // Refresh once (20 gold), then buy the first thing that is affordable.
      const before = await page.evaluate(() => AG.App.run.gold);
      await page.getByRole('button', { name: /Refresh the wares · 20 gold/ }).click();
      await page.waitForTimeout(200);
      const after = await page.evaluate(() => ({ gold: AG.App.run.gold, n: AG.App.run.shop.items.length }));
      if (after.gold !== before - 20 || after.n !== 6) throw new Error('refresh: ' + JSON.stringify({ before, after }));
      await page.getByRole('button', { name: /Refresh the wares · 30 gold/ }).waitFor();
      await page.locator('.offers .offer:not(.gone):not(.poor)').first().click();
      await page.waitForTimeout(200);
      if (await page.locator('.modal').count()) await shot('shop-picker');
      await resolvePicks();
      await shot('shop-after', true);
      await page.getByRole('button', { name: 'Leave and climb on' }).click();
    } else {
      const btn = page.locator('.choice:not([disabled])').last();
      await btn.click();
      await page.waitForTimeout(300);
      await resolvePicks();
      await page.waitForTimeout(300);
      await shot('event-result', true);
    }
  }
  // The boss floor, then the boss war room with the danger overlay.
  await page.evaluate(() => {
    const run = AG.App.run;
    run.act = 2;
    AG.Run.startAct(run, 2);
    run.floor = 7;
    run.screen = 'tower';
  });
  await render();
  await page.waitForTimeout(300);
  await shot('tower-boss', true);
  await page.locator('.floor-card .btn.fight').click();
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

  // The summit: a beaten Grandmaster, three champions already in the Hall.
  await page.evaluate(() => {
    const App = AG.App;
    const run = App.run;
    const Run = AG.Run;
    run.act = 3;
    const enc = AG.Encounters.grandmaster;
    const mk = (units) => Run.autoArmy({ units, ranks: {}, relics: [], supplyBonus: 0 }, enc);
    run.finalArmy = { army: Run.armyFor(run, Run.autoArmy(run, enc)), relics: run.relics.slice(), enc: 'grandmaster' };
    run.stats.endedAt = Date.now();
    const champ = (n, units, relics) => ({ id: 'c' + n, name: 'Run ' + n, date: Date.now() - n * 86400000, army: mk(units), relics, enc: 'grandmaster', heart: n === 1, wins: 20 + n, losses: n });
    Run.saveHall({ entries: [champ(1, ['knight', 'archmage', 'cleric', 'squire'], ['stormHeart']), champ(2, ['golem', 'pyromancer', 'squire'], []), champ(3, ['squire', 'scout'], ['warBanner'])], runs: 3 });
    run.screen = 'victory';
  });
  await render();
  await page.waitForTimeout(300);
  await shot('victory', true);
  // The mega boss's war room.
  await page.getByRole('button', { name: /Face the Heart/ }).click();
  await page.waitForTimeout(400);
  await page.getByRole('button', { name: 'Auto-deploy' }).click();
  await page.waitForTimeout(300);
  await shot('mega-setup', true);
  await page.getByRole('button', { name: '← Back' }).click();
  await page.waitForTimeout(300);
  // The Hall of Fame climb: watch the first duel at 4×, then skip.
  await page.getByRole('button', { name: /enter the Hall of Fame/i }).click();
  await page.waitForTimeout(300);
  await shot('climb', true);
  await page.locator('.screen-head ~ .row').getByRole('button', { name: /Watch the duel/ }).click();
  await page.waitForTimeout(1500);
  await shot('duel');
  await page.getByRole('button', { name: /Skip to result/ }).click();
  await page.waitForSelector('.end-card', { timeout: 60000 });
  await page.waitForTimeout(300);
  await shot('duel-end');
  await page.locator('.end-card .btn.primary').click();
  await page.waitForTimeout(300);
  if (await page.getByRole('button', { name: 'Resolve the rest instantly' }).count()) {
    await page.getByRole('button', { name: 'Resolve the rest instantly' }).click();
    await page.waitForTimeout(500);
  }
  await shot('climb-result', true);
  const placed = await page.evaluate(() => AG.App.run.climb.placed && AG.Run.loadHall().entries.length);
  if (placed !== 4) errors.push('expected four Hall of Fame entries after the climb, got ' + placed);
  const saved = await page.evaluate(() => AG.Run.load(false));
  if (saved) errors.push('a finished run should not stay saved');
  await page.evaluate(() => AG.App.toTitle());
  await page.waitForTimeout(300);
  await shot('title-after');
  await page.getByRole('button', { name: /Hall of Fame/ }).click();
  await page.waitForTimeout(300);
  await shot('hall', true);
  await page.locator('.hall-row .btn').first().click();
  await page.waitForTimeout(300);
  await shot('hall-formation');
  await page.locator('.modal .close').click();
  // Skirmish picker, and the mega boss there.
  await page.evaluate(() => AG.App.openSandbox());
  await page.waitForTimeout(300);
  await shot('sandbox', true);
  await page.locator('.enc-item').filter({ hasText: 'Heart of the Board' }).click();
  await page.waitForTimeout(400);
  await shot('sandbox-mega', true);
  await browser.close();
  const real = errors.filter((e) => !/playback error/.test(e));
  if (real.length) { console.log('ERRORS:\n' + real.join('\n')); process.exit(1); }
  console.log('tour ok, screenshots in ' + outDir);
})().catch((e) => { console.error(e); process.exit(1); });
