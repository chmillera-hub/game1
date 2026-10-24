/* App controller: which screen is showing, the HUD, saving, and the flows
   between screens. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;
  const Run = AG.Run;
  const PREFS_KEY = 'arcane-gambit/prefs/v1';

  const App = (AG.App = {
    run: null, mode: 'title', view: null, battle: null, root: null, current: null,
    prefs: { speed: 0.5 }, onResize: null,
  });

  App.start = function (hot) {
    App.root = document.getElementById('app');
    App.loadPrefs();
    UI.initTips();
    let t = 0;
    window.addEventListener('resize', function () {
      clearTimeout(t);
      t = setTimeout(function () { if (App.onResize) App.onResize(); }, 80);
    });
    if (hot && hot.run && hot.mode && hot.mode !== 'title') {
      App.run = hot.run;
      App.mode = hot.mode;
      App.render();
      return;
    }
    App.toTitle();
  };
  App.snapshot = function () { return { run: App.run, mode: App.mode }; };

  App.loadPrefs = function () {
    try { Object.assign(App.prefs, JSON.parse(localStorage.getItem(PREFS_KEY) || '{}')); } catch (e) { /* defaults */ }
  };
  App.savePrefs = function () {
    try { localStorage.setItem(PREFS_KEY, JSON.stringify(App.prefs)); } catch (e) { /* ignore */ }
  };
  App.save = function () { if (App.run) Run.save(App.run); };
  let saveTimer = 0;
  App.saveSoon = function () { clearTimeout(saveTimer); saveTimer = setTimeout(App.save, 300); };

  // ------------------------------------------------------------ rendering
  App.mount = function (el) {
    if (App.current && App.current.onUnmount) App.current.onUnmount();
    UI.clear(App.root);
    App.onResize = null;
    App.root.appendChild(el);
    App.current = el;
    if (el.onMount) el.onMount();
  };
  function withHud(inner) {
    const wrap = h('div', App.hud(), inner);
    wrap.onMount = inner.onMount;
    wrap.onUnmount = inner.onUnmount;
    return wrap;
  }
  App.render = function () {
    UI.hideTip();
    if (App.mode === 'title' || !App.run) return App.mount(UI.Screens.title(App));
    if (App.view === 'battle' && App.battle) return App.mount(UI.BattleScreen(App));
    const sc = App.run.screen;
    if (sc === 'setup') return App.mount(withHud(UI.SetupScreen(App)));
    const fn = UI.Screens[sc];
    if (fn) return App.mount(fn(App));
    App.run.screen = App.mode === 'sandbox' ? 'sandbox' : 'map';
    App.mount(UI.Screens[App.run.screen](App));
  };
  App.go = function (screen) {
    App.view = null;
    App.battle = null;
    if (App.run) App.run.screen = screen;
    App.save();
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  };

  App.hud = function () {
    const run = App.run;
    if (App.mode === 'sandbox') {
      return h('div.hud',
        h('button.brand', { type: 'button', on: { click: App.toTitle } }, 'Arcane Gambit'),
        h('span.chip.arcane', 'Skirmish'),
        h('span.spacer'),
        h('button.btn.small', { type: 'button', on: { click: () => App.go('sandbox') } }, '← All fights'),
        h('button.btn.small.ghost', { type: 'button', on: { click: App.help } }, '?'),
      );
    }
    const relics = h('div.relic-row');
    for (const id of run.relics) relics.appendChild(UI.relicIcon(id));
    return h('div.hud',
      h('button.brand', { type: 'button', 'aria-label': 'Back to title', on: { click: App.toTitle } }, 'Arcane Gambit'),
      h('span.stat.resolve', { 'data-tip': 'Lose Resolve when you lose a battle. At 0 the run ends.', 'data-tip-title': 'Resolve' }, h('span.lbl', 'Resolve'), h('span.v.num', run.resolve + '/' + run.maxResolve)),
      h('span.stat.gold', h('span.lbl', 'Gold'), h('span.v.num', run.gold)),
      h('span.stat', h('span.lbl', 'Act'), h('span.v.num', ['I', 'II', 'III'][run.act - 1] + ' · floor ' + run.floor)),
      run.mode === 'casual' ? h('span.chip.arcane', 'Casual') : null,
      relics,
      h('span.spacer'),
      h('button.btn.small', { type: 'button', on: { click: App.armyView } }, 'Army'),
      h('button.btn.small.ghost', { type: 'button', 'aria-label': 'How to play', on: { click: App.help } }, '?'),
    );
  };

  // ---------------------------------------------------------------- flows
  App.toTitle = function () {
    App.mode = 'title';
    App.view = null;
    App.battle = null;
    App.run = null;
    App.render();
  };
  App.continueRun = function () {
    const run = Run.load(false);
    if (!run) { App.toTitle(); return; }
    App.run = run;
    App.mode = 'run';
    App.view = null;
    App.render();
  };
  App.newRunDialog = function (hasSave) {
    const m = UI.modal(function (close) {
      const start = (mode) => {
        close();
        Run.clear();
        App.run = Run.newRun({ mode });
        App.mode = 'run';
        App.view = null;
        App.save();
        App.render();
      };
      return h('div.stack',
        hasSave ? h('p', { style: { color: 'var(--garnet-2)' } }, 'Starting a new run abandons the one in progress.') : null,
        h('div.offers',
          h('button.offer', { type: 'button', on: { click: () => start('standard') } }, h('span.kind', 'Standard'), h('div.nm', 'The full climb'),
            h('div.d', 'Each defeat costs Resolve; at 0 the run ends. Retry any fight as often as your Resolve allows.')),
          h('button.offer', { type: 'button', on: { click: () => start('casual') } }, h('span.kind', 'Casual'), h('div.nm', 'Tinker freely'),
            h('div.d', 'Defeats cost nothing. Rearrange and retry until it clicks.')),
        ),
      );
    }, { title: 'New run', wide: true });
    return m;
  };
  App.openSandbox = function () {
    const run = Run.load(true) || Run.sandbox();
    run.units = AG.playerUnitIds();
    const fresh = Run.sandbox();
    run.runes = fresh.runes;
    App.run = run;
    App.mode = 'sandbox';
    App.go('sandbox');
  };
  App.sandboxFight = function (encId) {
    const run = App.run;
    const enc = AG.Encounters[encId];
    const tier = enc.tier === 'early' || enc.tier === 'normal' ? 'battle' : enc.tier;
    run.battle = { enc: encId, tier, attempts: 0, ramp: 0, formation: run.formations[encId] ? AG.deepCopy(run.formations[encId]) : [] };
    App.go('setup');
  };
  App.enterNode = function (id) {
    Run.enter(App.run, id);
    App.save();
    App.view = null;
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  };
  // Everything needed to rebuild the same battle, kept for replays (after a
  // win the run has already moved on to its rewards).
  App.lastSetup = null;
  function makeBattle(setup) {
    const enc = AG.Encounters[setup.enc];
    return AG.B.create(enc, setup.army, Object.assign({ record: true }, setup.opts));
  }
  App.startBattle = function () {
    const run = App.run;
    const F = run.battle.formation;
    run.lastArmy = AG.deepCopy(F);
    run.formations[run.battle.enc] = AG.deepCopy(F);
    App.save();
    App.lastSetup = { enc: run.battle.enc, army: Run.armyFor(run, F), opts: AG.deepCopy(Run.battleOpts(run)) };
    App.battle = { s: makeBattle(App.lastSetup), replay: false };
    App.view = 'battle';
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  };
  App.replay = function () {
    if (!App.lastSetup) return;
    App.battle = { s: makeBattle(App.lastSetup), replay: true };
    App.view = 'battle';
    App.render();
  };
  App.afterBattle = function () {
    App.view = null;
    App.battle = null;
    if (App.mode === 'sandbox') App.run.screen = 'setup';
    App.save();
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  };
  App.armyView = function () { UI.armyView(App.run); };
  App.help = function () { UI.help(); };
})(globalThis.AG = globalThis.AG || {});
