/* Every screen outside the war room and the battle itself. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;
  const Run = AG.Run;
  const S = (UI.Screens = {});
  const T = '︎';
  const ROMAN = ['I', 'II', 'III'];
  const FLOOR = {
    battle: { icon: '⚔' + T, name: 'Battle' },
    event: { icon: '?', name: 'Event' },
    shop: { icon: '¤', name: 'Merchant' },
    boss: { icon: '♚' + T, name: 'Boss' },
  };
  const RARITY_NAME = { common: 'Common', uncommon: 'Uncommon', rare: 'Rare' };

  // --------------------------------------------------------------- shared
  function unitOffer(def, opts) {
    const d = AG.Units[def];
    const u = AG.B.makeUnit(def, 0, 0, 0, { rank: opts.rank || 0 });
    return h('button.offer' + (opts.cls ? '.' + opts.cls : ''), { type: 'button', on: { click: opts.onClick } },
      h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', opts.kind || 'New unit'), h('span.rarity.' + d.rarity, d.rarity)),
      h('div.nm', h('span.ic' + (UI.rarityClass(def) ? '.' + UI.rarityClass(def) : ''), UI.icon(def, 'lg')), d.name),
      h('div.mono.muted', { style: { fontSize: '13px' } }, d.cost + ' supply · HP ' + u.maxHp + ' · ATK ' + u.atk + ' · SPD ' + u.spd + (u.armor ? ' · Armor ' + u.armor : '')),
      h('div.d', d.blurb),
      h('div.offer-pattern', UI.patternDiagram(u, 10), h('div.d', UI.moveText(u))),
      opts.price != null ? h('div.price', opts.price + ' gold') : null,
      h('span.btn.small.ghost', { role: 'presentation', on: { click: (e) => { e.stopPropagation(); UI.modal(UI.inspector(u, { showTalents: true }), {}); } } }, 'Details'),
    );
  }
  function runeOffer(id, opts) {
    const R = AG.Runes[id];
    return h('button.offer' + (opts.cls ? '.' + opts.cls : ''), { type: 'button', on: { click: opts.onClick } },
      h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', 'Rune'), h('span.rarity.' + R.rarity, R.rarity)),
      h('div.nm', h('span.ic.rune', UI.glyph(R.icon)), R.name),
      h('div.d', R.desc),
      h('div.mono.muted', { style: { fontSize: '13px' } }, '+' + R.cost + ' supply when socketed'),
      opts.price != null ? h('div.price', opts.price + ' gold') : null,
    );
  }
  function relicOffer(id, opts) {
    const R = AG.Relics[id];
    return h('button.offer' + (opts.cls ? '.' + opts.cls : ''), { type: 'button', on: { click: opts.onClick } },
      h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', 'Relic'), h('span.rarity.' + R.rarity, R.rarity)),
      h('div.nm', h('span.ic.relic', UI.glyph(R.icon)), R.name),
      h('div.d', R.desc),
      opts.price != null ? h('div.price', opts.price + ' gold') : null,
    );
  }
  UI.unitOffer = unitOffer;

  // Pick one of your unit types (for training).
  UI.pickUnit = function (title, defs, run, onPick) {
    return UI.modal(function (close) {
      const list = h('div.army-grid');
      for (const def of defs) {
        const d = AG.Units[def];
        const r = run.ranks[def] || 0;
        list.appendChild(h('button.offer', { type: 'button', on: { click: () => { close(); onPick(def); } } },
          h('div.nm', h('span.ic' + (UI.rarityClass(def) ? '.' + UI.rarityClass(def) : ''), UI.icon(def, 'lg')), d.name, h('span.faint', ' ' + '★'.repeat(r))),
          h('div.d', AG.RANKS[r] + ' → ' + AG.RANKS[r + 1] + ': ' + AG.rankDesc(r + 1, def) + '.'),
        ));
      }
      return h('div.stack', list);
    }, { title, wide: true });
  };

  // Where a saved run stands, for the Continue button.
  UI.runWhere = function (run) {
    if (run.screen === 'draft' || run.screen === 'boon') return 'drafting';
    if (run.screen === 'victory' || run.screen === 'climb') return 'Act III cleared';
    return 'Act ' + ROMAN[run.act - 1] + ', floor ' + (run.floor + 1);
  };

  /* A small static board: the squares, the enemy where it stands, the deploy
     zone bracketed. opts.army places white pieces too; opts.noFoes leaves
     the enemy out; opts.px is the square size. */
  UI.miniBoard = function (enc, opts) {
    opts = opts || {};
    const { board, spawns } = AG.parseBoard(enc.map, enc.legend);
    const px = opts.px || 22;
    const at = {};
    if (!opts.noFoes) for (const sp of spawns) at[sp.y * board.w + sp.x] = { def: sp.def, side: 1 };
    for (const e of opts.army || []) at[e.y * board.w + e.x] = { def: e.def, side: 0 };
    const grid = h('div.mini-board', { style: { gridTemplateColumns: 'repeat(' + board.w + ', ' + px + 'px)', '--mc': px + 'px' } });
    for (let y = 0; y < board.h; y++) {
      for (let x = 0; x < board.w; x++) {
        const i = y * board.w + x;
        const t = board.terr[i];
        const cls = t === AG.TER.FLOOR ? ((x + y) % 2 ? 'd' : 'l') + (board.deploy[i] && !opts.army ? '.dp' : '') : t === AG.TER.WALL ? 'wall' : t === AG.TER.PIT ? 'pit' : 'void';
        const c = h('div.mc.' + cls);
        if (at[i]) c.appendChild(UI.piece(at[i].def, { side: at[i].side, cls: 'sm' }));
        grid.appendChild(c);
      }
    }
    return h('div.mini-frame.theme-' + (enc.theme || 'classic'), grid);
  };
  // The enemy line-up of an encounter: each kind once, with a count.
  function foeList(enc) {
    const counts = {};
    const order = [];
    for (const sp of AG.parseBoard(enc.map, enc.legend).spawns) {
      if (!counts[sp.def]) order.push(sp.def);
      counts[sp.def] = (counts[sp.def] || 0) + 1;
    }
    order.sort((a, b) => (AG.Units[b].boss ? 1 : 0) - (AG.Units[a].boss ? 1 : 0) || (AG.Units[b].big ? 1 : 0) - (AG.Units[a].big ? 1 : 0));
    return h('div.foes', order.map((def) => h('span.foe', { 'data-tip': AG.Units[def].blurb || '', 'data-tip-title': AG.Units[def].name, tabindex: '0', 'aria-label': AG.Units[def].name + (counts[def] > 1 ? ' ×' + counts[def] : '') },
      UI.piece(def, { side: 1, cls: 'sm' }), counts[def] > 1 ? h('b', '×' + counts[def]) : null)));
  }
  function bossOf(enc) {
    const sp = AG.parseBoard(enc.map, enc.legend).spawns.find((x) => AG.Units[x.def].boss);
    return sp ? sp.def : null;
  }
  function screenHead(eyebrow, title, flavor) {
    return h('div.screen-head', h('div.stack', { style: { gap: '4px' } }, eyebrow ? h('span.eyebrow', eyebrow) : null, h('h2', title), flavor ? h('p.flavor', flavor) : null));
  }

  // ------------------------------------------------------------------ title
  S.title = function (App) {
    const save = Run.load(false);
    const hall = Run.loadHall();
    const demoHost = h('div.title-demo');
    const menu = h('div.title-menu',
      save ? h('button.btn.primary', { type: 'button', on: { click: () => App.continueRun() } }, 'Continue · ' + UI.runWhere(save)) : null,
      h('button.btn' + (save ? '' : '.primary'), { type: 'button', on: { click: () => App.newRun(!!save) } }, 'New run'),
      h('button.btn', { type: 'button', on: { click: () => App.showHall() } }, 'Hall of Fame' + (hall.entries.length ? ' (' + hall.entries.length + ')' : '')),
      h('button.btn', { type: 'button', on: { click: () => App.openSandbox() } }, 'Skirmish (everything unlocked)'),
      h('button.btn.ghost', { type: 'button', on: { click: () => App.help() } }, 'How to play'),
    );
    // A row of pieces behind the name, as on Chess Evolved's title bar.
    const frieze = h('div.frieze', { 'aria-hidden': 'true' });
    for (const def of ['squire', 'cleric', 'golem', 'pyromancer', 'chronomancer', 'archmage', 'phoenix', 'ranger', 'knight', 'frostWitch', 'squire']) {
      frieze.appendChild(UI.piece(def, { side: 0, glow: '' }));
    }
    const root = h('div.title-screen',
      h('div.frieze-band', frieze, h('h1.logo', 'Arcane Gambit', h('small', 'Wizard chess · auto-battler · roguelike'))),
      demoHost,
      menu,
      h('p.title-foot', 'Draft wizard-chess pieces, place as many as your supply allows, and press Begin. Your pieces then think for themselves, one at a time, fastest first. Climb three towers of ever harder fights; lose as often as you like.'),
    );
    root.onMount = function () { root._demo = UI.demo(demoHost); };
    root.onUnmount = function () { if (root._demo) root._demo.stop(); };
    return root;
  };

  // A small self-playing battle behind the title menu.
  UI.demo = function (host) {
    let alive = true;
    const pairs = [
      ['goblinSkirmish', ['knight', 'scout', 'cleric', 'squire']],
      ['wolfFord', ['golem', 'pyromancer', 'squire', 'squire']],
      ['slimeCellar', ['frostWitch', 'knight', 'apprentice']],
      ['thornwood', ['berserker', 'ranger', 'cleric', 'scout']],
    ];
    let n = Math.floor(Math.random() * pairs.length);
    async function one() {
      const [encId, units] = pairs[n++ % pairs.length];
      const enc = AG.Encounters[encId];
      const army = UI.adaptArmy(units.map((d, i) => ({ def: d, x: i, y: 0, talents: [], rune: null })), AG.parseBoard(enc.map, enc.legend).board);
      const s = AG.B.create(enc, army.map((e) => Object.assign({ rank: 0 }, e)), { record: true });
      const view = new UI.BoardView({ board: s.board, theme: enc.theme, maxCell: 54 });
      view.k = 0.6;
      UI.clear(host);
      host.appendChild(h('div.board-wrap', view.el));
      const avail = host.getBoundingClientRect().width || Math.min(window.innerWidth - 32, 520);
      view.fit(Math.min(avail, 520), Math.min(360, window.innerHeight * 0.42));
      view.sync(s.units);
      const caption = h('p.hint', { style: { minHeight: '2.6em', marginTop: '8px' } }, '');
      host.appendChild(caption);
      let guard = 0;
      while (alive && !s.over && guard++ < 400) {
        const r = AG.B.step(s);
        const evs = s.ev.splice(0);
        for (const e of evs) {
          if (!alive) return;
          if (e.type === 'turn') view.setFlag('active', e.uid);
          else if (e.type === 'think') { const u = AG.B.U(s, e.uid); caption.textContent = u.name + ': ' + e.reason; await UI.wait(380); }
          else if (e.type === 'move') await view.animMove(e.uid, e.to, e.kind, e.path);
          else if (e.type === 'attack') { if (e.melee) await view.lunge(e.uid, e.to); else await view.projectile(e.from, e.to, e.vfx, e.vfx === 'shell'); }
          else if (e.type === 'aoe') await view.aoe(e.cells, e.r, e.vfx);
          else if (e.type === 'dmg') view.floatOn(e.uid, '−' + e.amt, 'dmg');
          else if (e.type === 'death') await view.fadeOut(e.uid);
          else if (e.type === 'summon') await view.fadeIn(AG.B.U(s, e.uid));
        }
        if (r && r.kind === 'turn') view.sync(s.units.filter((u) => u.alive));
      }
      await UI.wait(1400);
    }
    (async function () { while (alive) { try { await one(); } catch (e) { alive = false; } } })();
    return { stop() { alive = false; } };
  };

  // ------------------------------------------------------------------ draft
  // Five picks, each one of three: two commons, two uncommons, a rare.
  S.draft = function (App) {
    const run = App.run;
    const d = run.draft;
    if (!d) { App.go('boon'); return h('div'); }
    const rarity = Run.DRAFT[d.step];
    const steps = h('ol.draft-steps', { 'aria-label': 'Draft picks' });
    Run.DRAFT.forEach(function (r, i) {
      const def = d.picks[i];
      steps.appendChild(h('li.draft-step.' + r + (i === d.step ? '.cur' : '') + (def ? '.done' : ''),
        h('span.ic' + (def && UI.rarityClass(def) ? '.' + UI.rarityClass(def) : ''), def ? UI.piece(def, { side: 0, cls: 'md' }) : UI.glyph('?')),
        h('span.rarity.' + r, RARITY_NAME[r]),
        h('span.nm', def ? AG.Units[def].name : i === d.step ? 'choosing…' : ''),
      ));
    });
    const offers = h('div.offers');
    for (const def of d.options) {
      offers.appendChild(unitOffer(def, {
        kind: RARITY_NAME[rarity] + ' · pick 1 of 3',
        onClick: () => { Run.draftPick(run, def); App.save(); App.render(); try { window.scrollTo(0, 0); } catch (e) { /* ignore */ } },
      }));
    }
    const army = h('div.row', { style: { gap: '6px' } }, h('span.eyebrow', 'Your army so far'),
      run.units.map((def) => h('span.chip', UI.icon(def), AG.Units[def].name)));
    return h('div', App.hud(),
      screenHead('A new run · pick ' + (d.step + 1) + ' of ' + Run.DRAFT.length, 'Draft your army',
        'Choose the unit types you start with: two commons, two uncommons and one rare, each from a choice of three. Every run also brings Squires.'),
      h('div.stack', { style: { gap: '16px' } }, steps, army, h('div.sec-title', 'Choose a ' + RARITY_NAME[rarity].toLowerCase() + ' unit'), offers),
    );
  };

  // ------------------------------------------------------------- opening
  // Pick one advantage, with the whole army in view.
  S.boon = function (App) {
    const run = App.run;
    const grid = h('div.offers');
    for (const id of run.boons || []) {
      const b = Run.BOONS[id];
      grid.appendChild(h('button.offer.boon', { type: 'button', on: { click: () => take(id) } },
        h('span.kind', 'Opening'), h('div.nm', b.name), h('div.d', b.desc)));
    }
    function take(id) {
      const b = Run.BOONS[id];
      if (b.pick === 'trainable') {
        UI.pickUnit('Train which unit?', Run.trainable(run), run, (def) => { Run.takeBoon(run, id, def); App.save(); App.render(); });
        return;
      }
      Run.takeBoon(run, id);
      App.save();
      App.render();
    }
    return h('div', App.hud(),
      screenHead('A new run', 'Choose your opening', 'Your army is drafted. Pick one advantage to start the climb with; your units are listed below (tap one for every detail).'),
      h('div.stack', { style: { gap: '16px' } },
        grid,
        h('div.sec-title', 'Your army · ' + AG.plural(run.units.length, 'unit type')),
        UI.armyGrid(run),
        run.runes.length ? h('div.row', { style: { gap: '6px' } }, h('span.eyebrow', 'Runes'), run.runes.map((r) => h('span.chip', UI.glyph(AG.Runes[r].icon), AG.Runes[r].name))) : null,
      ),
    );
  };

  // ------------------------------------------------------------ act intro
  S.actIntro = function (App) {
    const run = App.run;
    const A = Run.ACTS[run.act];
    const boss = AG.Encounters[Run.bossFor(run)];
    const bossDef = boss ? bossOf(boss) : null;
    const counts = {};
    for (const t of Run.FLOORS) counts[t] = (counts[t] || 0) + 1;
    return h('div.title-screen',
      h('span.eyebrow', 'Act ' + ROMAN[run.act - 1]),
      bossDef ? h('div', { style: { width: '120px', height: '120px' } }, UI.piece(bossDef, { side: 1 })) : null,
      h('div.logo', { style: { fontSize: 'clamp(40px, 8vw, 84px)' } }, A.name),
      h('p.flavor', A.blurb + (bossDef ? ' At the top of the tower waits ' + AG.Units[bossDef].name + '.' : '')),
      h('p.hint', Run.FLOORS.length + ' floors: ' + counts.battle + ' battles (easy, medium or hard on each), an event and a merchant halfway up, and the boss at the top.'),
      h('button.btn.primary', { type: 'button', on: { click: () => App.go('tower') } }, 'Enter the tower'),
    );
  };

  // ----------------------------------------------------------------- tower
  function fightCard(run, o, onFight) {
    const enc = AG.Encounters[o.enc];
    const D = Run.DIFF[o.diff];
    const board = AG.parseBoard(enc.map, enc.legend).board;
    const supply = Run.limits(run, enc).supply + (run.nextSupply || 0);
    const gold = (D.gold[0] + run.act * 2) + '–' + (D.gold[1] + run.act * 2) + ' gold';
    const prize = gold + ' · choose 1 of ' + D.offers + (D.luck ? ' (rarer finds)' : '') + (D.relic ? ' · a relic' : '');
    const mods = o.diff === 'easy' ? 'Enemies have 20% less health.' : o.diff === 'hard' ? 'Enemies have 30% more health and +1 ATK.' : o.diff === 'elite' ? 'An elite: a tougher band led by a heavy.' : 'A fair fight.';
    const px = Math.max(14, Math.min(26, Math.floor(232 / Math.max(board.w, board.h))));
    return h('div.fight.' + o.diff,
      h('div.row', { style: { justifyContent: 'space-between' } }, h('span.tier.' + o.diff, D.name), h('span.mono.muted', board.w + '×' + board.h + ' · ' + supply + ' supply')),
      h('h3', enc.name),
      h('div.fight-board', UI.miniBoard(enc, { px })),
      foeList(enc),
      h('p.d', mods),
      h('p.prize', prize),
      h('button.btn.primary', { type: 'button', on: { click: onFight } }, UI.uiIcon('swords'), 'Fight'),
    );
  }
  function towerColumn(App) {
    const run = App.run;
    const boss = AG.Encounters[Run.bossFor(run)];
    const bossDef = bossOf(boss);
    const list = h('ol.tower', { 'aria-label': 'The tower, top floor first' });
    for (let i = run.tower.length - 1; i >= 0; i--) {
      const fl = run.tower[i];
      const F = FLOOR[fl.type];
      let sub = '';
      if (fl.type === 'battle') {
        const o = fl.done && fl.options && fl.choice >= 0 ? fl.options[fl.choice] : null;
        sub = o ? Run.DIFF[o.diff].name + ' · ' + AG.Encounters[o.enc].name : Run.ELITE_FLOORS.indexOf(i) >= 0 ? 'Easy, medium or elite' : 'Easy, medium or hard';
      } else if (fl.type === 'event') sub = 'Something happens';
      else if (fl.type === 'shop') sub = 'Units, runes, relics, training';
      else sub = bossDef ? AG.Units[bossDef].name : boss.name;
      list.appendChild(h('li.floor.' + fl.type + (fl.done ? '.done' : '') + (i === run.floor ? '.cur' : ''),
        h('span.fn', String(i + 1)),
        h('span.fi', fl.type === 'boss' && bossDef ? UI.piece(bossDef, { side: 1, cls: 'sm' }) : UI.glyph(F.icon)),
        h('span.ft', h('b', F.name), h('small', sub)),
        fl.done ? h('span.ok', { 'aria-label': 'cleared' }, '✓') : null,
      ));
    }
    return h('div.panel.tower-panel',
      h('div.eyebrow', 'Act ' + ROMAN[run.act - 1] + ' · ' + Run.ACTS[run.act].name),
      list,
      h('div.row', h('button.btn.small', { type: 'button', on: { click: () => App.armyView() } }, 'View army'), h('button.btn.small.ghost', { type: 'button', on: { click: () => App.help() } }, 'How to play')),
    );
  }
  S.tower = function (App) {
    const run = App.run;
    const f = Run.currentFloor(run);
    if (!f) { App.go('actIntro'); return h('div'); }
    const where = 'Act ' + ROMAN[run.act - 1] + ' · floor ' + (run.floor + 1) + ' of ' + run.tower.length;
    const main = h('div.floor-main');
    const enter = () => { Run.enterFloor(run); App.save(); App.render(); try { window.scrollTo(0, 0); } catch (e) { /* ignore */ } };
    if (run.nextSupply) {
      main.appendChild(h('p.result', (run.nextSupply > 0 ? '+' : '−') + Math.abs(run.nextSupply) + ' supply in your next battle.'));
    }
    if (f.type === 'battle') {
      main.appendChild(screenHead(where, 'Choose your fight', 'Easy fights pay less; hard fights and elites pay more and turn up rarer finds. Each floor up, the enemy is a little stronger. Losing costs nothing: retry, or come back down and pick another.'));
      const cards = h('div.fights');
      f.options.forEach(function (o, i) {
        if (o.enc) cards.appendChild(fightCard(run, o, () => { Run.chooseFight(run, i); App.save(); App.render(); try { window.scrollTo(0, 0); } catch (e) { /* ignore */ } }));
      });
      main.appendChild(cards);
    } else if (f.type === 'event') {
      main.appendChild(screenHead(where, 'An event', 'Halfway up the tower something is waiting: a stranger, a shrine, a choice.'));
      main.appendChild(h('div.floor-card', h('div.fc-ic', UI.glyph('?')), h('div.stack', { style: { gap: '8px' } }, h('p', 'Events offer units, runes, gold or a fight, sometimes at a price.'), h('div.row', h('button.btn.primary', { type: 'button', on: { click: enter } }, 'Step inside')))));
    } else if (f.type === 'shop') {
      main.appendChild(screenHead(where, 'The merchant', 'A travelling armoury has set up on the stairs.'));
      main.appendChild(h('div.floor-card', h('div.fc-ic', UI.glyph('¤')), h('div.stack', { style: { gap: '8px' } }, h('p', 'You have ' + run.gold + ' gold. Units, runes, relics, and a drill instructor who can train one unit type.'), h('div.row', h('button.btn.primary', { type: 'button', on: { click: enter } }, 'Browse the wares')))));
    } else {
      const enc = AG.Encounters[Run.bossFor(run)];
      const bossDef = bossOf(enc);
      const B = bossDef ? AG.Units[bossDef] : null;
      main.appendChild(screenHead(where, enc.name, enc.flavor));
      main.appendChild(h('div.floor-card.boss',
        bossDef ? h('div.fc-boss', UI.piece(bossDef, { side: 1 })) : null,
        h('div.stack', { style: { gap: '10px' } },
          B ? h('p', h('b', B.name + '. '), B.blurb) : null,
          h('div.fight-board', UI.miniBoard(enc, { px: 24 })),
          foeList(enc),
          h('p.mono.muted', Run.limits(run, enc).supply + (run.nextSupply || 0) + ' supply · 60–75 gold, a choice of three relics' + (run.act < 3 ? '' : ' · the end of the climb')),
          h('div.row', h('button.btn.fight', { type: 'button', on: { click: enter } }, UI.uiIcon('swords'), 'Face ' + (B ? B.name : 'the boss'))),
        ),
      ));
    }
    return h('div', App.hud(), h('div.tower-wrap', main, towerColumn(App)));
  };

  // --------------------------------------------------------------- reward
  S.reward = function (App) {
    const run = App.run;
    const p = run.pending;
    if (!p) { App.go('tower'); return h('div'); }
    const body = h('div.stack', { style: { gap: '16px' } });
    const gains = h('div.row');
    if (p.gold) gains.appendChild(h('span.chip.brass', '+' + p.gold + ' gold'));
    if (p.relic) gains.appendChild(h('span.chip.brass', UI.glyph(AG.Relics[p.relic].icon), AG.Relics[p.relic].name));
    body.appendChild(gains);
    if (p.relic) body.appendChild(h('div.offers', relicOffer(p.relic, { kind: 'Relic', cls: 'taken', onClick: () => {} })));
    if (p.relicChoices && p.relicChoices.length) {
      body.appendChild(h('div.sec-title', 'Choose a relic'));
      const g = h('div.offers');
      for (const id of p.relicChoices) {
        g.appendChild(relicOffer(id, {
          cls: p.relicTaken === id ? 'taken' : p.relicTaken ? 'gone' : '',
          onClick: () => { if (!p.relicTaken) { Run.claimRelic(run, id); App.save(); App.render(); } },
        }));
      }
      body.appendChild(g);
    }
    if (p.offers && p.offers.length) {
      body.appendChild(h('div.sec-title', p.offerTaken >= 0 ? 'Added to your army' : 'Choose one to add to your army'));
      const g = h('div.offers');
      p.offers.forEach(function (o, i) {
        const cls = p.offerTaken === i ? 'taken' : p.offerTaken >= 0 ? 'gone' : '';
        const click = () => { if (p.offerTaken < 0) { Run.claimOffer(run, i); App.save(); App.render(); } };
        g.appendChild(o.kind === 'unit' ? unitOffer(o.def, { cls, onClick: click }) : runeOffer(o.id, { cls, onClick: click }));
      });
      body.appendChild(g);
    }
    const doneLabel = p.offers && p.offers.length && p.offerTaken < 0 ? 'Skip' : 'Continue';
    body.appendChild(h('div.row', h('button.btn.primary', {
      type: 'button', disabled: !!(p.relicChoices && p.relicChoices.length && !p.relicTaken),
      on: { click: () => { Run.finishReward(run); App.save(); App.render(); try { window.scrollTo(0, 0); } catch (e) { /* ignore */ } } },
    }, doneLabel)));
    return h('div', App.hud(), h('div.screen-head', h('h2', p.title)), body);
  };

  // ----------------------------------------------------------------- shop
  S.shop = function (App) {
    const run = App.run;
    const shop = run.shop;
    if (!shop) { App.go('tower'); return h('div'); }
    const price = (n) => Run.price(run, n);
    const buy = (kind, i, picked) => {
      if (Run.buy(run, kind, i, picked)) { App.save(); App.render(); UI.toast('Bought.'); }
      else UI.toast('You cannot afford that.');
    };
    const units = h('div.offers');
    shop.units.forEach((it, i) => units.appendChild(unitOffer(it.def, { cls: it.sold ? 'gone' : '', price: it.sold ? null : price(it.price), kind: it.sold ? 'Sold' : 'Recruit', onClick: () => !it.sold && buy('units', i) })));
    const runes = h('div.offers');
    shop.runes.forEach((it, i) => runes.appendChild(runeOffer(it.id, { cls: it.sold ? 'gone' : '', price: it.sold ? null : price(it.price), onClick: () => !it.sold && buy('runes', i) })));
    const relics = h('div.offers');
    shop.relics.forEach((it, i) => relics.appendChild(relicOffer(it.id, { cls: it.sold ? 'gone' : '', price: it.sold ? null : price(it.price), onClick: () => !it.sold && buy('relics', i) })));
    const svc = h('div.offers',
      h('button.offer' + (shop.train.used ? '.gone' : ''), { type: 'button', on: { click: () => {
        if (shop.train.used) return;
        const t = Run.trainable(run);
        if (!t.length) { UI.toast('Every unit is fully trained.'); return; }
        if (run.gold < price(shop.train.price)) { UI.toast('You cannot afford that.'); return; }
        UI.pickUnit('Train which unit?', t, run, (def) => buy('train', 0, def));
      } } }, h('span.kind', 'Service'), h('div.nm', h('span.ic', UI.glyph('★')), 'Drill instructor'), h('div.d', 'Train one unit type a rank: Veteran (+HP, +1 ATK), then Elite (+HP, +1 SPD, a second talent slot).'), shop.train.used ? null : h('div.price', price(shop.train.price) + ' gold')),
    );
    return h('div', App.hud(),
      screenHead('Merchant', 'The Travelling Armoury', 'You have ' + run.gold + ' gold.'),
      h('div.stack', { style: { gap: '14px' } },
        h('div.sec-title', 'Units'), units, h('div.sec-title', 'Runes'), runes,
        shop.relics.length ? h('div.sec-title', 'Relics') : null, shop.relics.length ? relics : null,
        h('div.sec-title', 'Services'), svc,
        h('div.row', h('button.btn.primary', { type: 'button', on: { click: () => { Run.advance(run); App.save(); App.render(); } } }, 'Leave and climb on')),
      ),
    );
  };

  // ---------------------------------------------------------------- event
  S.event = function (App) {
    const run = App.run;
    if (!run.event) { App.go('tower'); return h('div'); }
    const ev = AG.eventById(run.event.id);
    const body = h('div.event-card');
    body.appendChild(h('p.story', ev.text));
    if (run.event.result) {
      body.appendChild(h('div.result', run.event.result));
      body.appendChild(h('div.row', h('button.btn.primary', { type: 'button', on: { click: () => { Run.advance(run); App.save(); App.render(); } } }, 'Climb on')));
    } else {
      const ch = h('div.choices');
      ev.choices.forEach(function (c, i) {
        const av = Run.choiceAvailable(run, c);
        ch.appendChild(h('button.choice', { type: 'button', disabled: av !== true, on: { click: () => choose(c, i) } },
          h('span.t', c.label), c.desc || av !== true ? h('span.d', av !== true ? av : c.desc) : null));
      });
      body.appendChild(ch);
    }
    function choose(c, i) {
      const go = (picked) => {
        Run.resolveEvent(run, i, picked);
        App.save();
        App.render();
      };
      if (c.pick === 'trainable') UI.pickUnit('Train which unit?', Run.trainable(run), run, go);
      else if (c.pick === 'rune') {
        UI.modal(function (close) {
          const g = h('div.offers');
          for (const id of Array.from(new Set(run.runes))) g.appendChild(runeOffer(id, { onClick: () => { close(); go(id); } }));
          return g;
        }, { title: 'Which rune?', wide: true });
      } else go(null);
    }
    return h('div', App.hud(), screenHead('Event', ev.name), body);
  };

  // ---------------------------------------------------------- the summit
  function summary(run) {
    const mvp = Object.entries(run.stats.mvp || {}).sort((a, b) => b[1] - a[1])[0];
    return h('div.row', { style: { justifyContent: 'center' } },
      h('span.chip', run.stats.wins + ' wins · ' + run.stats.losses + ' defeats'),
      h('span.chip', run.units.length + ' unit types'),
      h('span.chip', run.relics.length + ' relics'),
      mvp && AG.Units[mvp[0]] ? h('span.chip.brass', 'MVP: ' + AG.Units[mvp[0]].name) : null,
    );
  }
  S.victory = function (App) {
    const run = App.run;
    const mega = AG.Units[Run.MEGA];
    const climb = () => { Run.startClimb(run); App.save(); App.render(); try { window.scrollTo(0, 0); } catch (e) { /* ignore */ } };
    const cards = h('div.summit');
    if (!run.megaWon) {
      cards.appendChild(h('div.summit-card.mega',
        h('div.fc-boss', UI.piece(Run.MEGA, { side: 1 })),
        h('div.stack', { style: { gap: '8px' } },
          h('span.eyebrow', 'Optional · not meant to be won'),
          h('h3', mega.name),
          h('p', 'Behind the Grandmaster’s board waits the position every game ends in. It takes at most 20 damage a round, every attack or spell you make costs that piece 1 health, it grows stronger every round, and you have 20 rounds. Only a maxed-out army stands a chance.'),
          h('div.row', h('button.btn', { type: 'button', on: { click: () => { Run.startMega(run); App.save(); App.render(); } } }, UI.uiIcon('swords'), 'Face ' + mega.name)),
        )));
    }
    cards.appendChild(h('div.summit-card',
      h('div.fc-ic', UI.glyph('♔' + T)),
      h('div.stack', { style: { gap: '8px' } },
        h('span.eyebrow', 'Hall of Fame'),
        h('h3', 'Enshrine your army'),
        h('p', 'The army that beat the Grandmaster is saved. It starts at the bottom of the Hall of Fame and duels each champion above it, one by one, until it loses' + (run.megaWon ? '' : '. Entering ends the run, so face ' + mega.name + ' first if you mean to') + '.'),
        h('div.row', h('button.btn.primary', { type: 'button', on: { click: climb } }, 'Enter the Hall of Fame')),
      )));
    return h('div.title-screen',
      h('div', { style: { width: '120px', height: '120px' } }, UI.piece(run.megaWon ? Run.MEGA : 'ebonKing', { side: 1, glow: 'g-gold' })),
      h('div.logo.win', { style: { fontSize: 'clamp(44px, 9vw, 96px)' } }, run.megaWon ? 'Zugzwang falls' : 'Checkmate'),
      h('p.flavor', run.megaWon ? 'You beat the position that cannot be beaten. Nobody is going to believe you.' : 'The Mad Grandmaster topples. All three towers are yours.'),
      summary(run),
      cards,
    );
  };

  // ------------------------------------------------------- Hall of Fame
  // One entry: rank, name, its army as figurines, relics and a few facts.
  function hallRow(e, rank, opts) {
    opts = opts || {};
    const counts = {};
    const order = [];
    for (const a of e.army) { if (!counts[a.def]) order.push(a.def); counts[a.def] = (counts[a.def] || 0) + 1; }
    const army = h('div.foes', order.map((def) => h('span.foe', { 'data-tip-title': AG.Units[def].name, 'data-tip': counts[def] + ' on the board' },
      UI.piece(def, { side: 0, cls: 'sm' }), counts[def] > 1 ? h('b', '×' + counts[def]) : null)));
    const relics = h('div.relic-row', (e.relics || []).map((id) => AG.Relics[id] ? UI.relicIcon(id) : null));
    let date = '';
    try { date = new Date(e.date).toLocaleDateString(); } catch (err) { /* ignore */ }
    return h('li.hall-row' + (opts.cls ? '.' + opts.cls : ''),
      h('span.hr-rank', rank != null ? '#' + (rank + 1) : ''),
      h('div.hr-body',
        h('div.row', { style: { gap: '8px' } }, h('b.hr-name', e.name), opts.tag ? h('span.chip' + (opts.tagCls ? '.' + opts.tagCls : ''), opts.tag) : null,
          e.heart ? h('span.chip.brass', 'Beat Zugzwang') : null, h('span.faint.mono', date + ' · ' + e.army.length + ' units · ' + e.wins + 'W ' + e.losses + 'L')),
        army,
        relics.childNodes.length ? relics : null,
      ),
      opts.button || h('button.btn.small.ghost', { type: 'button', on: { click: () => showArmy(e) } }, 'Formation'),
    );
  }
  function showArmy(e) {
    UI.modal(h('div.stack', { style: { alignItems: 'center' } },
      UI.miniBoard(Run.duelEncounter(e.enc), { px: 40, army: e.army, noFoes: true }),
      h('p.hint', 'As it stood against the Mad Grandmaster. In a duel the defender’s side is mirrored.')), { title: e.name });
  }
  S.hall = function (App) {
    const hall = Run.loadHall();
    const list = h('ol.hall');
    hall.entries.forEach((e, i) => list.appendChild(hallRow(e, i)));
    const back = () => { if (App.run && App.hallFrom) { App.mode = App.hallFrom; App.hallFrom = null; App.render(); } else App.toTitle(); };
    return h('div',
      h('div.hud', h('button.brand', { type: 'button', on: { click: () => App.toTitle() } }, 'Arcane Gambit'), h('span.chip.brass', 'Hall of Fame'), h('span.spacer'),
        h('button.btn.small', { type: 'button', on: { click: back } }, '← Back')),
      screenHead('Champions', 'Hall of Fame', 'Every run that beat the Mad Grandmaster keeps the army it won with. A new champion starts at the bottom and duels its way up until it loses. The top ' + Run.HALL_SIZE + ' stay.'),
      hall.entries.length ? list : h('p.result', 'No champions yet. Beat the Mad Grandmaster at the top of Act III and your army will be the first.'),
    );
  };

  // The climb: watch (or resolve) each duel from the bottom up.
  S.climb = function (App) {
    const run = App.run;
    const c = run.climb;
    if (!c) { App.go('victory'); return h('div'); }
    const hall = Run.loadHall();
    const me = Run.hallEntry(run, c.number);
    if (c.placed) {
      const made = c.rank < Run.HALL_SIZE;
      const list = h('ol.hall');
      hall.entries.forEach((e, i) => list.appendChild(hallRow(e, i, e.id === c.entryId ? { cls: 'me', tag: 'This run', tagCls: 'arcane' } : {})));
      const wins = c.results.filter(Boolean).length;
      return h('div', App.hud(),
        h('div.title-screen', { style: { gap: '14px' } },
          h('div.logo.win', { style: { fontSize: 'clamp(40px, 8vw, 84px)' } }, made ? '#' + (c.rank + 1) : 'Unranked'),
          h('p.flavor', !c.opponents.length ? 'The Hall of Fame was empty. Your army is its first champion.'
            : made ? (c.rank === 0 ? 'Your army beat every champion in the Hall. It stands at the top.' : 'Your army won ' + AG.plural(wins, 'duel') + ' and takes place #' + (c.rank + 1) + '.')
              : 'Your army lost its first duel and the Hall is full. Not this time.'),
          h('div.row', { style: { justifyContent: 'center' } },
            h('button.btn.primary', { type: 'button', on: { click: () => App.newRun(false) } }, 'New run'),
            h('button.btn', { type: 'button', on: { click: () => App.toTitle() } }, 'Title'),
          ),
        ),
        h('div.sec-title', 'Hall of Fame'),
        list,
      );
    }
    const opp = Run.climbOpponent(run);
    const list = h('ol.hall');
    const beaten = {};
    c.opponents.slice(0, c.results.length).forEach((id) => { beaten[id] = true; });
    hall.entries.forEach(function (e, i) {
      const isOpp = opp && e.id === opp.id;
      list.appendChild(hallRow(e, i, isOpp ? { cls: 'opp', tag: 'Next opponent', tagCls: 'garnet' } : beaten[e.id] ? { cls: 'beaten', tag: 'Beaten' } : {}));
      if (isOpp) {
        list.appendChild(hallRow(me, null, { cls: 'me', tag: 'Your run', tagCls: 'arcane',
          button: h('button.btn.primary.small', { type: 'button', on: { click: () => App.startDuel() } }, UI.uiIcon('swords'), 'Watch the duel') }));
      }
    });
    const resolveAll = () => {
      while (!run.climb.placed) {
        const o = Run.climbOpponent(run);
        if (!o) { Run.finishClimb(run); break; }
        Run.climbResult(run, Run.duelWinner(run.finalArmy, o));
      }
      App.save();
      App.render();
    };
    return h('div', App.hud(),
      screenHead('Hall of Fame · duel ' + (c.results.length + 1) + ' of up to ' + c.opponents.length, 'Climb the Hall',
        'Your army takes the near side of the Grandmaster’s board; the champion above it takes the far side, mirrored. Speed ties go to you; if time runs out, the champion keeps its place.'),
      h('div.row', { style: { marginBottom: '12px' } },
        h('button.btn.primary', { type: 'button', on: { click: () => App.startDuel() } }, UI.uiIcon('swords'), 'Watch the duel'),
        h('button.btn', { type: 'button', on: { click: resolveAll } }, 'Resolve the rest instantly')),
      list,
    );
  };

  // -------------------------------------------------------------- sandbox
  S.sandbox = function (App) {
    const run = App.run;
    const list = h('div.enc-list');
    const tierCls = (t) => (t === 'elite' ? '.elite' : t === 'boss' || t === 'mega' ? '.boss' : '');
    for (const act of [1, 2, 3]) {
      const items = h('div.enc-items');
      for (const e of AG.encounterList((x) => x.act === act)) {
        items.appendChild(h('button.enc-item', { type: 'button', on: { click: () => App.sandboxFight(e.id) } },
          h('span.t', e.name, h('span.tier' + tierCls(e.tier), e.tier)),
          h('span.d', e.supply + ' supply · ' + AG.parseBoard(e.map, e.legend).board.w + '×' + e.map.length + ' board'),
        ));
      }
      list.appendChild(h('div.enc-act', h('div.sec-title', 'Act ' + ROMAN[act - 1] + ' · ' + Run.ACTS[act].name), items));
    }
    const stepper = (label, key, max) => h('div.meter',
      h('span.lbl', label),
      h('button.btn.small.icon', { type: 'button', 'aria-label': 'Less', on: { click: () => { run[key] = Math.max(0, (run[key] || 0) - 1); App.save(); App.render(); } } }, '−'),
      h('span.v', '+' + (run[key] || 0)),
      h('button.btn.small.icon', { type: 'button', 'aria-label': 'More', on: { click: () => { run[key] = Math.min(max, (run[key] || 0) + 1); App.save(); App.render(); } } }, '+'),
    );
    const relicBox = h('div.relic-picks');
    for (const id of AG.relicList()) {
      const R = AG.Relics[id];
      const on = run.relics.indexOf(id) >= 0;
      relicBox.appendChild(h('button.relic-pick' + (on ? '.on' : ''), {
        type: 'button', 'aria-pressed': on ? 'true' : 'false', 'data-tip': R.desc, 'data-tip-title': R.name,
        on: { click: () => {
          const k = run.relics.indexOf(id);
          if (k >= 0) run.relics.splice(k, 1); else run.relics.push(id);
          App.save(); App.render();
        } },
      }, h('span.ic', UI.glyph(R.icon)), R.name));
    }
    return h('div',
      h('div.hud', h('button.brand', { type: 'button', on: { click: () => App.toTitle() } }, 'Arcane Gambit'), h('span.chip.arcane', 'Skirmish'), h('span.spacer'),
        h('button.btn.small.ghost', { type: 'button', on: { click: () => App.help() } }, 'How to play')),
      screenHead(null, 'Skirmish', 'Every unit and two of each rune are unlocked. Pick any fight, try any army, lose as often as you like.'),
      h('div.meters', { style: { marginBottom: '14px' } }, stepper('Extra supply', 'supplyBonus', 30),
        h('span.chip', run.stats.wins + ' wins · ' + run.stats.losses + ' losses')),
      h('details.relic-details', { style: { marginBottom: '14px' }, open: !!App.sandboxRelicsOpen, on: { toggle: (e) => { App.sandboxRelicsOpen = e.target.open; } } },
        h('summary', 'Relics in play (' + run.relics.length + ')'),
        relicBox),
      list,
    );
  };

  // -------------------------------------------------------------- army view
  // Every unit type the run owns, with its rank; tap for full details.
  UI.armyGrid = function (run) {
    const grid = h('div.army-grid');
    for (const def of run.units) {
      const d = AG.Units[def];
      const u = AG.B.makeUnit(def, 0, 0, 0, { rank: run.ranks[def] || 0 });
      grid.appendChild(h('button.offer', { type: 'button', on: { click: () => UI.modal(UI.inspector(u, { showTalents: true }), {}) } },
        h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', AG.RANKS[run.ranks[def] || 0]), h('span.rarity.' + d.rarity, d.rarity)),
        h('div.nm', h('span.ic' + (UI.rarityClass(def) ? '.' + UI.rarityClass(def) : ''), UI.icon(def, 'lg')), d.name, run.ranks[def] ? h('span.faint', ' ' + '★'.repeat(run.ranks[def])) : null),
        h('div.mono.muted', { style: { fontSize: '13px' } }, d.cost + ' supply · HP ' + u.maxHp + ' · ATK ' + u.atk + ' · SPD ' + u.spd + (u.armor ? ' · Armor ' + u.armor : '')),
        h('div.d', d.blurb),
        h('div.offer-pattern', UI.patternDiagram(u, 10), h('div.d', UI.moveText(u))),
      ));
    }
    return grid;
  };
  UI.armyView = function (run) {
    UI.modal(function () {
      const counts = Run.runeCounts(run);
      const runes = h('div.offers');
      for (const id of Object.keys(counts)) runes.appendChild(runeOffer(id, { onClick: () => {}, kind: 'Rune' })).appendChild(h('span.chip', '×' + counts[id]));
      const relics = h('div.offers');
      for (const id of run.relics || []) relics.appendChild(relicOffer(id, { onClick: () => {} }));
      return h('div.stack',
        h('div.sec-title', 'Units (' + run.units.length + ')'), UI.armyGrid(run),
        h('div.sec-title', 'Runes'), Object.keys(counts).length ? runes : h('p.hint', 'No runes yet.'),
        run.relics && run.relics.length ? h('div.sec-title', 'Relics') : null, run.relics && run.relics.length ? relics : null,
      );
    }, { title: 'Your army', wide: true });
  };

  // ------------------------------------------------------------------ help
  UI.help = function () {
    UI.modal(h('div.help',
      h('p', 'Arcane Gambit is wizard chess where you are the general, not the player. You choose the army and where it stands; the pieces fight by themselves.'),
      h('h4', 'Before each battle'),
      h('ul',
        h('li', 'Each fight gives you a supply budget. Units, talents and runes all cost supply. There is no limit on how many units you bring beyond the supply and the blue squares to stand on; Auto-deploy fills the board for you.'),
        h('li', 'Tap a unit in your army, then a blue-bracketed square on your side of the board. To move a placed piece, tap it and then another blue square (with a mouse you can also drag it).'),
        h('li', 'Tap a placed piece to give it a talent (one per unit, two once it is Elite) and a rune from your satchel.'),
        h('li', 'Tap any enemy to read exactly how it moves, attacks and what its traits do.'),
      ),
      h('h4', 'During battle'),
      h('ul',
        h('li', 'Every round, every unit acts once in order of speed: fastest first, ties to your side. The strip at the top shows the queue.'),
        h('li', 'On its turn a unit may move and then attack or use an ability. The AI tries every option, simulates the result and picks the best. Its reasoning shows above the board.'),
        h('li', 'Movement is chess-like: knights leap, bishops slide diagonally, rooks along ranks and files, and wizards teleport.'),
        h('li', 'Chasms swallow anything knocked into them that cannot fly. Walls block movement and line of sight.'),
        h('li', 'Fatigue: from round 12 an Arcane Storm hits every unit at the start of each round for 1, then 2, then 3 and so on, so nothing stalls forever. If three rounds pass without anyone being hurt, the storm arrives early.'),
      ),
      h('h4', 'The run'),
      h('ul',
        h('li', 'Start by drafting your army: two commons, two uncommons and a rare, each one of three. Every run also brings Squires. Then choose an opening advantage.'),
        h('li', 'Climb three towers of eight floors. On each battle floor choose an easy, medium or hard fight (on two floors per act, an elite instead of hard): harder fights pay more gold and rarer finds, and elites a relic. An event and a merchant wait halfway up, and a boss at the top.'),
        h('li', 'Losing costs nothing. Battles always play out the same way for the same setup, so read the report, change something and retry, as often as you like, or go back and choose another fight.'),
        h('li', 'After the last boss you may face Zugzwang, a mega boss that is not meant to be beaten. Then your final army enters the Hall of Fame, duelling the champions of earlier runs from the bottom up.'),
      ),
      h('h4', 'Reading the board'),
      h('ul',
        h('li', 'White pieces are yours; black pieces are the enemy. A coloured glow marks rarity: blue uncommon, purple rare, red for the enemy’s heavies, gold for bosses. The bar under a piece is its health; blue is shield.'),
        h('li', 'When you select a piece, blue brackets show where it can move, red brackets what it can strike, and white brackets squares where it can do both.'),
        h('li', 'Small badges show afflictions: ', ['burn', 'poison', 'chill', 'frozen', 'rooted', 'marked', 'cursed', 'taunt', 'stealth'].map((k, i) => [i ? ', ' : '', UI.statusIcon(k), ' ' + UI.STATUS[k].name.toLowerCase()]), '. Frozen units skip a turn and take +2 damage; chilled ones act later.'),
        h('li', 'Squares are named like chess: files a, b, c… from the left, ranks 1, 2, 3… up from your edge.'),
      ),
      h('p.hint', 'Battle keys: Space pauses, → steps one turn, 1–4 set the speed, S skips to the result.'),
    ), { title: 'How to play', wide: true });
  };
})(globalThis.AG = globalThis.AG || {});
