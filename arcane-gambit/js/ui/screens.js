/* Every screen outside the war room and the battle itself. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;
  const Run = AG.Run;
  const S = (UI.Screens = {});
  const T = '︎';

  const NODE = {
    battle: { icon: '⚔' + T, name: 'Battle', d: 'A fight. Win to choose a new unit or rune.' },
    elite: { icon: '☠' + T, name: 'Elite', d: 'A hard fight. Win for a relic as well.' },
    boss: { icon: '♚' + T, name: 'Boss', d: 'The master of this board.' },
    event: { icon: '?', name: 'Unknown', d: 'Something happens. Usually a choice.' },
    shop: { icon: '¤', name: 'Merchant', d: 'Spend gold on units, runes, relics and training.' },
    rest: { icon: '♨' + T, name: 'Camp', d: 'Recover Resolve or train a unit type.' },
    treasure: { icon: '◆' + T, name: 'Treasure', d: 'A free relic and some gold.' },
  };
  UI.NODE = NODE;

  // --------------------------------------------------------------- shared
  function unitOffer(def, opts) {
    const d = AG.Units[def];
    const u = AG.B.makeUnit(def, 0, 0, 0, {});
    return h('button.offer' + (opts.cls ? '.' + opts.cls : ''), { type: 'button', on: { click: opts.onClick } },
      h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', opts.kind || 'New unit'), h('span.rarity.' + d.rarity, d.rarity)),
      h('div.nm', h('span.ic', d.icon), d.name),
      h('div.mono.muted', { style: { fontSize: '13px' } }, d.cost + ' supply · HP ' + u.maxHp + ' · ATK ' + u.atk + ' · SPD ' + u.spd + (u.armor ? ' · Armor ' + u.armor : '')),
      h('div.d', d.blurb),
      h('div.d', UI.moveText(u)),
      opts.price != null ? h('div.price', opts.price + ' gold') : null,
      h('span.btn.small.ghost', { role: 'presentation', on: { click: (e) => { e.stopPropagation(); UI.modal(UI.inspector(u, { showTalents: true }), {}); } } }, 'Details'),
    );
  }
  function runeOffer(id, opts) {
    const R = AG.Runes[id];
    return h('button.offer' + (opts.cls ? '.' + opts.cls : ''), { type: 'button', on: { click: opts.onClick } },
      h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', 'Rune'), h('span.rarity.' + R.rarity, R.rarity)),
      h('div.nm', h('span.ic.rune', R.icon), R.name),
      h('div.d', R.desc),
      h('div.mono.muted', { style: { fontSize: '13px' } }, '+' + R.cost + ' supply when socketed'),
      opts.price != null ? h('div.price', opts.price + ' gold') : null,
    );
  }
  function relicOffer(id, opts) {
    const R = AG.Relics[id];
    return h('button.offer' + (opts.cls ? '.' + opts.cls : ''), { type: 'button', on: { click: opts.onClick } },
      h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', 'Relic'), h('span.rarity.' + R.rarity, R.rarity)),
      h('div.nm', h('span.ic.relic', R.icon), R.name),
      h('div.d', R.desc),
      opts.price != null ? h('div.price', opts.price + ' gold') : null,
    );
  }
  UI.unitOffer = unitOffer;

  // Pick one of your unit types (for training).
  UI.pickUnit = function (title, defs, run, onPick) {
    const m = UI.modal(function (close) {
      const list = h('div.army-grid');
      for (const def of defs) {
        const d = AG.Units[def];
        const r = run.ranks[def] || 0;
        list.appendChild(h('button.offer', { type: 'button', on: { click: () => { close(); onPick(def); } } },
          h('div.nm', h('span.ic', d.icon), d.name, h('span.faint', ' ' + '★'.repeat(r))),
          h('div.d', AG.RANKS[r] + ' → ' + AG.RANKS[r + 1] + ': ' + AG.rankDesc(r + 1, def) + '.'),
        ));
      }
      return h('div.stack', list);
    }, { title, wide: true });
    return m;
  };

  // ------------------------------------------------------------------ title
  S.title = function (App) {
    const save = Run.load(false);
    const live = save && save.screen !== 'gameover' && save.screen !== 'victory';
    const demoHost = h('div.title-demo');
    const menu = h('div.title-menu',
      live ? h('button.btn.primary', { type: 'button', on: { click: () => App.continueRun() } }, 'Continue · Act ' + save.act + ', floor ' + save.floor) : null,
      h('button.btn' + (live ? '' : '.primary'), { type: 'button', on: { click: () => App.newRunDialog(live) } }, 'New run'),
      h('button.btn', { type: 'button', on: { click: () => App.openSandbox() } }, 'Skirmish (everything unlocked)'),
      h('button.btn.ghost', { type: 'button', on: { click: () => App.help() } }, 'How to play'),
    );
    const root = h('div.title-screen',
      h('div.logo', 'Arcane Gambit', h('small', 'Wizard chess · auto-battler · roguelike')),
      demoHost,
      menu,
      h('p.title-foot', 'Draft wizard-chess pieces within a supply budget, place them, and press Begin. Your pieces then think for themselves, one at a time, fastest first. Win, recruit, upgrade, climb three boards.'),
    );
    root.onMount = function () { root._demo = UI.demo(demoHost); };
    root.onUnmount = function () { if (root._demo) root._demo.stop(); };
    return root;
  };

  // A small self-playing battle behind the title menu.
  UI.demo = function (host) {
    let alive = true;
    const pairs = [
      ['goblinSkirmish', ['knight', 'scout', 'cleric']],
      ['wolfFord', ['golem', 'pyromancer', 'squire']],
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

  // ----------------------------------------------------------------- boon
  S.boon = function (App) {
    const run = App.run;
    const grid = h('div.offers');
    for (const id of run.boons || []) {
      const b = Run.BOONS[id];
      grid.appendChild(h('button.offer', { type: 'button', on: { click: () => take(id) } },
        h('span.kind', 'Opening'), h('div.nm', b.name), h('div.d', b.desc)));
    }
    function take(id) {
      const b = Run.BOONS[id];
      if (b.pick === 'trainable') {
        UI.pickUnit('Train which unit?', run.units.slice(), run, (def) => { Run.takeBoon(run, id, def); App.go('actIntro'); });
        return;
      }
      Run.takeBoon(run, id);
      App.go('actIntro');
    }
    return h('div.stack', { style: { gap: '18px', maxWidth: '980px', margin: '0 auto' } },
      h('div.screen-head', h('div.stack', { style: { gap: '6px' } }, h('span.eyebrow', 'A new run'), h('h2', 'Choose your opening'), h('p.flavor', 'Your army starts with a Squire, Knight, Scout, Cleric and Apprentice, 40 Resolve and a little gold. Pick one advantage to begin with.'))),
      grid,
    );
  };

  // ------------------------------------------------------------ act intro
  S.actIntro = function (App) {
    const run = App.run;
    const A = Run.ACTS[run.act];
    const boss = AG.encounterList((e) => e.act === run.act && e.tier === 'boss')[0];
    const bossUnit = boss ? AG.Units[AG.parseBoard(boss.map, boss.legend).spawns.map((s) => s.def).find((d) => AG.Units[d].boss)] : null;
    return h('div.title-screen',
      h('span.eyebrow', 'Act ' + ['I', 'II', 'III'][run.act - 1]),
      h('div.logo', { style: { fontSize: 'clamp(44px, 9vw, 92px)' } }, A.name),
      h('p.flavor', A.blurb + (bossUnit ? ' At the top waits ' + bossUnit.name + '.' : '')),
      h('button.btn.primary', { type: 'button', on: { click: () => App.go('map') } }, 'To the map'),
    );
  };

  // ------------------------------------------------------------------ map
  S.map = function (App) {
    const run = App.run;
    const map = run.map;
    const reach = new Set(Run.reachable(run));
    const nodes = Object.keys(map.nodes).map((k) => map.nodes[k]);
    const ROWH = 74, PADT = 48;
    const height = (map.rows + 1) * ROWH + PADT;
    const W = 100;
    const pos = (n) => {
      if (n.id === 'boss') return [50, PADT / 2 + 8];
      const jitter = ((n.r * 7 + n.c * 13) % 5) - 2;
      return [10 + (n.c * 80) / (map.cols - 1) + jitter, height - (n.r * ROWH + PADT)];
    };
    const wrap = h('div.map', { style: { height: height + 'px' } });
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + height);
    svg.setAttribute('preserveAspectRatio', 'none');
    for (const n of nodes) {
      for (const m of n.next) {
        const a = pos(n), b = pos(map.nodes[m]);
        const line = document.createElementNS(svgNS, 'line');
        line.setAttribute('x1', a[0]); line.setAttribute('y1', a[1]);
        line.setAttribute('x2', b[0]); line.setAttribute('y2', b[1]);
        const walked = n.visited && map.nodes[m].visited;
        const open = run.pos === n.id && reach.has(m);
        line.setAttribute('stroke', walked ? '#d6aa52' : open ? '#f1d08a' : '#3c4962');
        line.setAttribute('stroke-width', walked || open ? '2.4' : '1.4');
        line.setAttribute('vector-effect', 'non-scaling-stroke');
        if (!walked && !open) line.setAttribute('stroke-dasharray', '4 5');
        svg.appendChild(line);
      }
    }
    wrap.appendChild(svg);
    for (const n of nodes) {
      const [x, y] = pos(n);
      const N = NODE[n.type] || NODE.battle;
      const isReach = reach.has(n.id);
      const cls = ['mnode', n.type];
      if (isReach) cls.push('reach');
      if (n.visited) cls.push('done');
      if (run.pos === n.id) cls.push('cur');
      if (!isReach && !n.visited && run.pos && n.r <= (map.nodes[run.pos] ? map.nodes[run.pos].r : -1)) cls.push('past');
      const btn = h('button', {
        type: 'button', class: cls.join(' '), style: { left: x + '%', top: y + 'px' },
        'data-tip': N.d, 'data-tip-title': N.name + (n.visited ? ' (visited)' : ''), 'aria-label': N.name + (isReach ? ', available' : ''),
        disabled: !isReach,
        on: { click: () => { if (isReach) App.enterNode(n.id); } },
      }, N.icon);
      wrap.appendChild(btn);
    }
    const legend = h('div.map-legend');
    for (const k of ['battle', 'elite', 'event', 'shop', 'rest', 'treasure', 'boss']) {
      legend.appendChild(h('span', h('b', NODE[k].icon), NODE[k].name));
    }
    const side = h('div.panel.stack',
      h('div.eyebrow', 'Act ' + ['I', 'II', 'III'][run.act - 1] + ' · ' + Run.ACTS[run.act].name),
      h('p.muted', reach.size ? 'Choose where to go next. Paths only lead upward.' : 'The way on is blocked.'),
      legend,
      h('div.row', h('button.btn.small', { type: 'button', on: { click: () => App.armyView() } }, 'View army'), h('button.btn.small.ghost', { type: 'button', on: { click: () => App.help() } }, 'How to play')),
    );
    const root = h('div', App.hud(), h('div.map-wrap', h('div', wrap), side));
    root.onMount = function () {
      const cur = wrap.querySelector('.reach') || wrap.querySelector('.cur');
      if (cur && cur.scrollIntoView) { try { cur.scrollIntoView({ block: 'center' }); } catch (e) { /* ignore */ } }
    };
    return root;
  };

  // --------------------------------------------------------------- reward
  S.reward = function (App) {
    const run = App.run;
    const p = run.pending;
    if (!p) { App.go('map'); return h('div'); }
    const body = h('div.stack', { style: { gap: '16px' } });
    const gains = h('div.row');
    if (p.gold) gains.appendChild(h('span.chip.brass', '+' + p.gold + ' gold'));
    if (p.heal) gains.appendChild(h('span.chip', { style: { color: 'var(--heal)' } }, '+' + p.heal + ' Resolve'));
    if (p.relic) gains.appendChild(h('span.chip.brass', AG.Relics[p.relic].icon + ' ' + AG.Relics[p.relic].name));
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
    body.appendChild(h('div.row', h('button.btn.primary', { type: 'button', disabled: !!(p.relicChoices && p.relicChoices.length && !p.relicTaken), on: { click: () => { Run.finishReward(run); App.save(); App.render(); } } }, doneLabel)));
    return h('div', App.hud(), h('div.screen-head', h('h2', p.title)), body);
  };

  // ----------------------------------------------------------------- shop
  S.shop = function (App) {
    const run = App.run;
    const shop = run.shop;
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
      } } }, h('span.kind', 'Service'), h('div.nm', '★ Drill instructor'), h('div.d', 'Train one unit type a rank: Veteran (+HP, +1 ATK), then Elite (+HP, +1 SPD, a second talent slot).'), shop.train.used ? null : h('div.price', price(shop.train.price) + ' gold')),
      h('button.offer' + (shop.heal.used ? '.gone' : ''), { type: 'button', on: { click: () => !shop.heal.used && buy('heal') } }, h('span.kind', 'Service'), h('div.nm', '♥ Tonic'), h('div.d', 'Recover ' + shop.heal.amt + ' Resolve.'), shop.heal.used ? null : h('div.price', price(shop.heal.price) + ' gold')),
    );
    return h('div', App.hud(),
      h('div.screen-head', h('div.stack', { style: { gap: '4px' } }, h('span.eyebrow', 'Merchant'), h('h2', 'The Travelling Armoury'), h('p.flavor', 'You have ' + run.gold + ' gold.'))),
      h('div.stack', { style: { gap: '14px' } },
        h('div.sec-title', 'Units'), units, h('div.sec-title', 'Runes'), runes,
        shop.relics.length ? h('div.sec-title', 'Relics') : null, shop.relics.length ? relics : null,
        h('div.sec-title', 'Services'), svc,
        h('div.row', h('button.btn.primary', { type: 'button', on: { click: () => { run.shop = null; App.go('map'); } } }, 'Leave')),
      ),
    );
  };

  // ----------------------------------------------------------------- camp
  S.rest = function (App) {
    const run = App.run;
    const heal = Math.round(run.maxResolve * Run.REST_HEAL);
    const body = h('div.stack', { style: { gap: '16px', maxWidth: '760px' } });
    if (run.rested) {
      body.appendChild(h('div.result', run.restText));
      body.appendChild(h('div.row', h('button.btn.primary', { type: 'button', on: { click: () => App.go('map') } }, 'Break camp')));
    } else {
      const t = Run.trainable(run);
      body.appendChild(h('div.offers',
        h('button.offer', { type: 'button', on: { click: () => { Run.rest(run, 'recover'); App.save(); App.render(); } } },
          h('span.kind', 'Rest'), h('div.nm', '♥ Recover'), h('div.d', 'Recover ' + heal + ' Resolve (' + run.resolve + '/' + run.maxResolve + ' now).')),
        h('button.offer' + (t.length ? '' : '.gone'), { type: 'button', on: { click: () => {
          if (!t.length) return;
          UI.pickUnit('Train which unit?', t, run, (def) => { Run.rest(run, 'train', def); App.save(); App.render(); });
        } } }, h('span.kind', 'Drill'), h('div.nm', '★ Train'), h('div.d', 'Train one unit type a rank. Elite units can take two talents.')),
      ));
    }
    return h('div', App.hud(),
      h('div.screen-head', h('div.stack', { style: { gap: '4px' } }, h('span.eyebrow', 'Camp'), h('h2', 'A fire in the margins'), h('p.flavor', 'The pieces gather round. You have time for one thing before dawn.'))),
      body);
  };

  // ---------------------------------------------------------------- event
  S.event = function (App) {
    const run = App.run;
    const ev = AG.eventById(run.event.id);
    const body = h('div.event-card');
    body.appendChild(h('p.story', ev.text));
    if (run.event.result) {
      body.appendChild(h('div.result', run.event.result));
      body.appendChild(h('div.row', h('button.btn.primary', { type: 'button', on: { click: () => App.go('map') } }, 'Continue')));
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
    return h('div', App.hud(), h('div.screen-head', h('div.stack', { style: { gap: '4px' } }, h('span.eyebrow', 'Event'), h('h2', ev.name))), body);
  };

  // ------------------------------------------------------------ the end
  function summary(run) {
    const mvp = Object.entries(run.stats.mvp || {}).sort((a, b) => b[1] - a[1])[0];
    return h('div.row', { style: { justifyContent: 'center' } },
      h('span.chip', 'Act ' + run.act + ', floor ' + run.floor),
      h('span.chip', run.stats.wins + ' wins · ' + run.stats.losses + ' defeats'),
      h('span.chip', run.units.length + ' unit types'),
      h('span.chip', run.relics.length + ' relics'),
      mvp ? h('span.chip.brass', 'MVP: ' + AG.Units[mvp[0]].name) : null,
    );
  }
  S.gameover = function (App) {
    const run = App.run;
    return h('div.title-screen',
      h('div.logo', { style: { color: 'var(--garnet-2)', fontSize: 'clamp(48px, 10vw, 100px)' } }, 'Resolve Broken'),
      h('p.flavor', 'Your army scatters. The board resets. Somewhere, a goblin is laughing.'),
      summary(run),
      h('div.row', { style: { justifyContent: 'center' } },
        h('button.btn.primary', { type: 'button', on: { click: () => { Run.clear(); App.newRunDialog(false); } } }, 'New run'),
        h('button.btn', { type: 'button', on: { click: () => { Run.clear(); App.toTitle(); } } }, 'Title'),
      ),
    );
  };
  S.victory = function (App) {
    const run = App.run;
    return h('div.title-screen',
      h('div.logo', { style: { fontSize: 'clamp(48px, 10vw, 100px)' } }, 'Checkmate'),
      h('p.flavor', 'The Mad Grandmaster topples. Every board you crossed is yours.' + (run.mode === 'casual' ? ' (Casual run.)' : '')),
      summary(run),
      h('div.row', { style: { justifyContent: 'center' } },
        h('button.btn.primary', { type: 'button', on: { click: () => { Run.clear(); App.newRunDialog(false); } } }, 'New run'),
        h('button.btn', { type: 'button', on: { click: () => { Run.clear(); App.toTitle(); } } }, 'Title'),
      ),
    );
  };

  // -------------------------------------------------------------- sandbox
  S.sandbox = function (App) {
    const run = App.run;
    const list = h('div.enc-list');
    for (const act of [1, 2, 3]) {
      const items = h('div.enc-items');
      for (const e of AG.encounterList((x) => x.act === act)) {
        items.appendChild(h('button.enc-item', { type: 'button', on: { click: () => App.sandboxFight(e.id) } },
          h('span.t', e.name, h('span.tier' + (e.tier === 'elite' ? '.elite' : e.tier === 'boss' ? '.boss' : ''), e.tier)),
          h('span.d', e.supply + ' supply · ' + e.slots + ' units · ' + AG.parseBoard(e.map, e.legend).board.w + '×' + e.map.length + ' board'),
        ));
      }
      list.appendChild(h('div.enc-act', h('div.sec-title', 'Act ' + ['I', 'II', 'III'][act - 1] + ' · ' + Run.ACTS[act].name), items));
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
      }, h('span.ic', R.icon), R.name));
    }
    return h('div',
      h('div.hud', h('button.brand', { type: 'button', on: { click: () => App.toTitle() } }, 'Arcane Gambit'), h('span.chip.arcane', 'Skirmish'), h('span.spacer'),
        h('button.btn.small.ghost', { type: 'button', on: { click: () => App.help() } }, 'How to play')),
      h('div.screen-head', h('div.stack', { style: { gap: '4px' } }, h('h2', 'Skirmish'), h('p.flavor', 'Every unit and two of each rune are unlocked. Pick any fight, try any army, lose as often as you like.'))),
      h('div.meters', { style: { marginBottom: '14px' } }, stepper('Extra supply', 'supplyBonus', 20), stepper('Extra units', 'slotBonus', 4),
        h('span.chip', run.stats.wins + ' wins · ' + run.stats.losses + ' losses')),
      h('details.relic-details', { style: { marginBottom: '14px' }, open: !!App.sandboxRelicsOpen, on: { toggle: (e) => { App.sandboxRelicsOpen = e.target.open; } } },
        h('summary', 'Relics in play (' + run.relics.length + ')'),
        relicBox),
      list,
    );
  };

  // -------------------------------------------------------------- army view
  UI.armyView = function (run) {
    UI.modal(function () {
      const grid = h('div.army-grid');
      for (const def of run.units) {
        const d = AG.Units[def];
        const u = AG.B.makeUnit(def, 0, 0, 0, { rank: run.ranks[def] || 0 });
        grid.appendChild(h('button.offer', { type: 'button', on: { click: () => UI.modal(UI.inspector(u, { showTalents: true }), {}) } },
          h('div.row', { style: { justifyContent: 'space-between' } }, h('span.kind', AG.RANKS[run.ranks[def] || 0]), h('span.rarity.' + d.rarity, d.rarity)),
          h('div.nm', h('span.ic', d.icon), d.name, run.ranks[def] ? h('span.faint', ' ' + '★'.repeat(run.ranks[def])) : null),
          h('div.mono.muted', { style: { fontSize: '13px' } }, d.cost + ' supply · HP ' + u.maxHp + ' · ATK ' + u.atk + ' · SPD ' + u.spd),
          h('div.d', d.blurb),
        ));
      }
      const counts = Run.runeCounts(run);
      const runes = h('div.offers');
      for (const id of Object.keys(counts)) runes.appendChild(runeOffer(id, { onClick: () => {}, kind: 'Rune' })).appendChild(h('span.chip', '×' + counts[id]));
      const relics = h('div.offers');
      for (const id of run.relics || []) relics.appendChild(relicOffer(id, { onClick: () => {} }));
      return h('div.stack',
        h('div.sec-title', 'Units (' + run.units.length + ')'), grid,
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
        h('li', 'Each fight gives you a supply budget and a number of unit slots. Units, talents and runes all cost supply.'),
        h('li', 'Tap a unit in your army, then a gold square on your side of the board. To move a placed piece, tap it and then another gold square (with a mouse you can also drag it).'),
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
        h('li', 'Climb three boards. Each map branches: battles, elites, events, merchants, camps and treasure, with a boss at the top.'),
        h('li', 'Winning lets you recruit a new unit type or take a rune. Elites and bosses also give relics.'),
        h('li', 'Losing costs Resolve (more for each enemy left standing), then you can rethink your army and retry. At 0 Resolve the run ends. Casual mode skips the Resolve loss.'),
        h('li', 'Camps let you rest or train a unit type to Veteran and then Elite.'),
      ),
      h('h4', 'Reading the board'),
      h('ul',
        h('li', 'Gold-rimmed ivory pieces are yours; garnet pieces are the enemy. The bar under a piece is its health; blue is shield.'),
        h('li', 'Small icons show afflictions: 🔥 burning, 🧪 poisoned, ❄️ chilled (slower), 🧊 frozen (skips a turn, takes +2 damage), ⛓️ rooted, 🎯 marked, ⛧ hexed, ❗ taunted, 🌫️ stealthed.'),
        h('li', 'Squares are named like chess: files a, b, c… from the left, ranks 1, 2, 3… up from your edge.'),
      ),
    ), { title: 'How to play', wide: true });
  };
})(globalThis.AG = globalThis.AG || {});
