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
    prefs: { speed: 1, music: 0.5, sfx: 0.7, muted: false }, onResize: null,
  });

  App.start = function (hot) {
    App.root = document.getElementById('app');
    App.loadPrefs();
    UI.initTips();
    UI.Sound.init(App.prefs);
    // M mutes and unmutes everything.
    document.addEventListener('keydown', function (e) {
      if ((e.key === 'm' || e.key === 'M') && !e.ctrlKey && !e.metaKey && !e.altKey && !(e.target && /INPUT|TEXTAREA/.test(e.target.tagName))) App.toggleMute();
    });
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
    // Battles used to start at double speed; the normal pace is now half that.
    if (App.prefs.paceV !== 2) {
      App.prefs.speed = 1;
      App.prefs.paceV = 2;
      App.savePrefs();
    }
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
    renderScreen();
    UI.Sound.music(App.musicFor());
  };
  function renderScreen() {
    if (App.mode === 'hall') return App.mount(UI.Screens.hall(App));
    if (App.mode === 'title' || !App.run) return App.mount(UI.Screens.title(App));
    if (App.view === 'battle' && App.battle) return App.mount(UI.BattleScreen(App));
    const sc = App.run.screen;
    if (sc === 'setup' && App.run.battle) return App.mount(withHud(UI.SetupScreen(App)));
    const fn = UI.Screens[sc];
    if (fn && sc !== 'title' && sc !== 'hall') return App.mount(fn(App));
    App.run.screen = App.mode === 'sandbox' ? 'sandbox' : App.run.tower ? 'tower' : App.run.draft ? 'draft' : 'boon';
    App.mount(UI.Screens[App.run.screen](App));
  }
  // The background music for what is on screen.
  App.musicFor = function () {
    const run = App.run;
    if (App.view === 'battle' && App.battle) {
      if (App.battle.duel) return 'battle';
      const enc = App.battle.encounter || AG.Encounters[App.battle.s.encounter];
      return enc.tier === 'mega' ? 'mega' : enc.tier === 'boss' ? 'boss' : 'battle';
    }
    if (App.mode !== 'run' || !run) return 'calm';
    if (run.screen === 'victory' || run.screen === 'climb') return 'victory';
    if (run.screen === 'setup' && run.battle && run.battle.tier === 'mega') return 'mega';
    return 'calm';
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
        App.soundButton(),
        h('button.btn.small.ghost', { type: 'button', on: { click: App.help } }, '?'),
      );
    }
    const relics = h('div.relic-row');
    for (const id of run.relics) relics.appendChild(UI.relicIcon(id));
    const where = run.tower && run.screen !== 'victory' && run.screen !== 'climb'
      ? ['I', 'II', 'III'][run.act - 1] + ' · floor ' + (run.floor + 1) + '/' + run.tower.length
      : run.tower ? 'Summit' : 'Drafting';
    return h('div.hud',
      h('button.brand', { type: 'button', 'aria-label': 'Back to title', on: { click: App.toTitle } }, 'Arcane Gambit'),
      h('span.stat', h('span.lbl', 'Act'), h('span.v.num', where)),
      h('span.stat.gold', h('span.lbl', 'Gold'), h('span.v.num', run.gold)),
      run.supplyBonus ? h('span.stat', { 'data-tip': 'Extra supply in every battle, on top of your relics.' }, h('span.lbl', 'Supply'), h('span.v.num', '+' + run.supplyBonus)) : null,
      relics,
      h('span.spacer'),
      h('button.btn.small', { type: 'button', on: { click: App.armyView } }, 'Army'),
      App.soundButton(),
      h('button.btn.small.ghost', { type: 'button', 'aria-label': 'How to play', on: { click: App.help } }, '?'),
    );
  };

  // ---------------------------------------------------------------- sound
  App.soundButton = function () {
    return h('button.btn.small.ghost.sound-btn', { type: 'button', 'aria-label': 'Sound settings', 'data-tip': 'Music and sound effects (M mutes)', on: { click: App.soundPanel } },
      UI.uiIcon(App.prefs.muted ? 'mute' : 'speaker'));
  };
  App.toggleMute = function () {
    App.prefs.muted = !App.prefs.muted;
    UI.Sound.configure(App.prefs);
    App.savePrefs();
    for (const b of document.querySelectorAll('.sound-btn')) { UI.clear(b).appendChild(UI.uiIcon(App.prefs.muted ? 'mute' : 'speaker')); }
    UI.toast(App.prefs.muted ? 'Sound off.' : 'Sound on.');
  };
  App.soundPanel = function () {
    UI.modal(function () {
      const slider = (label, key) => h('label.vol', h('span', label),
        h('input', { type: 'range', min: '0', max: '100', value: String(Math.round(App.prefs[key] * 100)), 'aria-label': label,
          on: { input: (e) => { App.prefs[key] = e.target.value / 100; UI.Sound.configure(App.prefs); }, change: () => { App.savePrefs(); if (key === 'sfx') UI.Sound.fx('coin'); } } }));
      const mute = h('input', { type: 'checkbox', checked: !!App.prefs.muted, on: { change: (e) => { if (!!e.target.checked !== !!App.prefs.muted) App.toggleMute(); } } });
      return h('div.stack',
        slider('Music', 'music'),
        slider('Effects', 'sfx'),
        h('label.row', mute, 'Mute everything'),
        h('p.hint', 'All of it is generated as you play: a different mood for each act’s tower, for battles, bosses and the Heart. Press M anywhere to mute or unmute.'),
      );
    }, { title: 'Sound' });
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
  // A new run starts with the draft. One in progress is abandoned (after asking).
  App.newRun = function (hasSave) {
    const start = () => {
      Run.clear();
      App.run = Run.newRun();
      App.mode = 'run';
      App.go('draft');
    };
    if (!hasSave) { start(); return; }
    UI.modal(function (close) {
      return h('div.stack',
        h('p', 'Starting a new run abandons the one in progress.'),
        h('div.row',
          h('button.btn.primary', { type: 'button', on: { click: () => { close(); start(); } } }, 'Abandon it and start'),
          h('button.btn', { type: 'button', on: { click: close } }, 'Keep it')),
      );
    }, { title: 'New run' });
  };
  App.showHall = function () {
    App.hallFrom = App.mode !== 'title' && App.mode !== 'hall' ? App.mode : null;
    App.mode = 'hall';
    App.view = null;
    App.battle = null;
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
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
    const tier = AG.Encounters[encId].tier;
    run.battle = { enc: encId, tier: tier === 'early' || tier === 'normal' ? 'battle' : tier, attempts: 0, ramp: 0, formation: run.formations[encId] ? AG.deepCopy(run.formations[encId]) : [] };
    App.go('setup');
  };
  // Everything needed to rebuild the same battle, kept for replays (after a
  // win the run has already moved on to its rewards).
  App.lastSetup = null;
  function makeBattle(setup) {
    const enc = setup.encounter || AG.Encounters[setup.enc];
    return AG.B.create(enc, setup.army, Object.assign({ record: true }, setup.opts));
  }
  App.startBattle = function () {
    const run = App.run;
    const F = run.battle.formation;
    run.lastArmy = AG.deepCopy(F);
    run.formations[run.battle.enc] = AG.deepCopy(F);
    App.save();
    App.lastSetup = { enc: run.battle.enc, army: Run.armyFor(run, F), opts: AG.deepCopy(Run.battleOpts(run)), changes: [] };
    App.battle = { s: makeBattle(App.lastSetup), replay: false };
    App.view = 'battle';
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  };
  // A Hall of Fame duel: this run's final army against the next champion up.
  App.startDuel = function () {
    const run = App.run;
    const opp = Run.climbOpponent(run);
    if (!opp) return;
    const encounter = Run.duelEncounter();
    App.lastSetup = { encounter, army: Run.arenaArmy(run.finalArmy), opts: Run.duelOpts(run.finalArmy, opp), changes: [] };
    App.battle = { s: makeBattle(App.lastSetup), replay: false, duel: opp, encounter };
    App.view = 'battle';
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  };
  App.afterDuel = function (won) {
    Run.climbResult(App.run, won);
    App.view = null;
    App.battle = null;
    App.save();
    App.render();
    try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  };
  App.replay = function () {
    if (!App.lastSetup) return;
    App.battle = { s: makeBattle(App.lastSetup), replay: true, encounter: App.lastSetup.encounter };
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
  // Leave a fight that has not been won: back down the tower to choose
  // another, away from an event's fight, or back from the mega boss.
  App.leaveFight = function () {
    const run = App.run;
    const tier = run.battle && run.battle.tier;
    if (Run.DIFF[tier] || tier === 'boss') Run.backToTower(run);
    else Run.leaveFight(run);
    App.go(run.screen);
  };
  App.armyView = function () { UI.armyView(App.run); };
  App.help = function () { UI.help(); };
})(globalThis.AG = globalThis.AG || {});
