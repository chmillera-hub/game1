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

  // Hold a placed piece to pick it up (it wiggles), then tap a free square.
  const pos = async (x, y) => page.evaluate(([x, y]) => {
    const r = document.querySelector('.cell[data-x="' + x + '"][data-y="' + y + '"]').getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2];
  }, [x, y]);
  const free = await page.evaluate(() => {
    const run = AG.App.run, enc = AG.Encounters[run.battle.enc];
    const { board } = AG.parseBoard(enc.map, enc.legend);
    for (let i = 0; i < board.n; i++) {
      const x = i % board.w, y = (i / board.w) | 0;
      if (board.deploy[i] && !run.battle.formation.some((e) => e.x === x && e.y === y)) return [x, y];
    }
    return null;
  });
  // Press, move and release with a finger on the phone run, a mouse otherwise.
  const cdp = mobile ? await ctx.newCDPSession(page) : null;
  const press = async (x, y) => (cdp ? cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] }) : (await page.mouse.move(x, y), page.mouse.down()));
  const drag = async (x, y) => (cdp ? cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y }] }) : page.mouse.move(x, y, { steps: 6 }));
  const release = async () => (cdp ? cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }) : page.mouse.up());
  const tap = async (x, y) => (cdp ? (await press(x, y), release()) : page.mouse.click(x, y));
  if (free) {
    const first = await page.evaluate(() => { const e = AG.App.run.battle.formation[0]; return [e.x, e.y]; });
    await page.locator('.cell[data-x="' + first[0] + '"]').first().scrollIntoViewIfNeeded();
    const [px, py] = await pos(first[0], first[1]);
    await press(px, py);
    await page.waitForTimeout(600);
    await release();
    await page.waitForTimeout(150);
    if (!(await page.locator('.token.lifted').count())) errors.push('long press did not pick the piece up');
    await shot('07b-lifted');
    const [fx, fy] = await pos(free[0], free[1]);
    await tap(fx, fy);
    await page.waitForTimeout(200);
    const moved = await page.evaluate(([x, y]) => AG.App.run.battle.formation[0].x === x && AG.App.run.battle.formation[0].y === y, free);
    if (!moved) errors.push('the picked-up piece was not set down on the tapped square');
    if (await page.locator('.token.lifted').count()) errors.push('the piece stayed lifted after being set down');
    // Hold, then drag it back while still pressing.
    const [qx, qy] = await pos(free[0], free[1]);
    await press(qx, qy);
    await page.waitForTimeout(600);
    const [bx, by] = await pos(first[0], first[1]);
    await drag((qx + bx) / 2, (qy + by) / 2);
    await drag(bx, by);
    await release();
    await page.waitForTimeout(200);
    const back = await page.evaluate(([x, y]) => AG.App.run.battle.formation[0].x === x && AG.App.run.battle.formation[0].y === y, first);
    if (!back) errors.push('holding and dragging did not move the piece');
  }

  // Mark an enemy as the priority.
  await page.getByRole('button', { name: /Set priority/ }).click();
  await page.locator('.token.e').first().click();
  await page.waitForTimeout(250);
  if (!(await page.locator('.token.prio').count())) errors.push('the marked enemy shows no priority reticle');
  if (!(await page.getByRole('button', { name: /Priority: / }).count())) errors.push('the priority button does not name the target');
  const pr = await page.evaluate(() => AG.App.run.battle.priority);
  if (!pr) errors.push('no priority stored for the battle');
  await shotFull('07c-priority');

  // Open a placed piece's loadout.
  await page.locator('.token.p').first().click();
  await page.waitForTimeout(200);
  if (mobile) {
    // Tapping an already selected piece opens its details straight away.
    if (!(await page.locator('.modal').count())) await page.getByRole('button', { name: /Upgrades/ }).click();
    await page.waitForTimeout(250);
    await shot('08-loadout');
    if (!(await page.locator('.modal .meter.supply .left').count())) errors.push('the loadout shows no supply left');
    await page.locator('.modal .close').click();
  } else {
    await shot('08-loadout');
    if (!(await page.locator('.side .meter.supply .left').count())) errors.push('the loadout shows no supply left');
  }
  if (!(await page.locator('.setup-main > .meters .left').count())) errors.push('the war room shows no supply left');

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
    // Taking the only choice moves on by itself.
    await page.locator('.offers .offer').first().click();
    await page.waitForTimeout(1300);
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
