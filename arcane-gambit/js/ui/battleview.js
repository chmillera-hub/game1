/* The battle screen: steps the engine one unit-turn at a time and plays the
   resulting events as animation, with the turn queue, the acting unit's
   reasoning, a notation log and a report at the end. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;
  const B = AG.B;

  const SPEEDS = [{ k: 1, label: '1×' }, { k: 0.5, label: '2×' }, { k: 0.25, label: '4×' }];

  UI.BattleScreen = function (App) {
    const s = App.battle.s;
    const enc = AG.Encounters[s.encounter];
    const isSandbox = App.mode === 'sandbox';
    const root = h('div.battle');
    let alive = true;
    let paused = false, stepOnce = false, skipping = false;
    let resume = null;
    const disp = {}; // what each token currently shows, as of the last played event
    for (const u of s.units) disp[u.uid] = { hp: u.hp, shield: u.shield, st: Object.keys(u.st) };

    const view = new UI.BoardView({ board: s.board, theme: enc.theme, maxCell: 72, onToken: inspect, onCell: () => {} });
    view.k = App.prefs.speed || 0.5;

    // ------------------------------------------------------------ layout
    const roundEl = h('span.round-badge', 'Round 0');
    const stormEl = h('span.storm-warn');
    const queueEl = h('div.queue', { 'aria-label': 'Turn order' });
    const thought = h('div.thought', h('div.ic', '♟'), h('div.who', 'Ready'), h('div.what', 'Your pieces move by themselves. Watch them think.'));
    const playBtn = h('button.btn.icon', { type: 'button', 'aria-label': 'Pause', on: { click: togglePause } }, '❚❚');
    const stepBtn = h('button.btn.small', { type: 'button', on: { click: step } }, 'Step');
    const seg = h('div.seg', { role: 'group', 'aria-label': 'Speed' });
    for (const sp of SPEEDS) {
      seg.appendChild(h('button', { type: 'button', class: sp.k === view.k ? 'on' : '', on: { click: () => setSpeed(sp.k) } }, sp.label));
    }
    const skipBtn = h('button.btn.small', { type: 'button', title: 'Keys: Space pause, → step, 1–3 speed, S skip', on: { click: skip } }, 'Skip to result ⏭');
    const altsBtn = h('button.btn.small.ghost', {
      type: 'button', 'aria-pressed': App.prefs.showAlts ? 'true' : 'false',
      'data-tip': 'Also show the runner-up options each unit weighed, and how much worse it judged them.',
      on: { click: () => { App.prefs.showAlts = !App.prefs.showAlts; App.savePrefs(); altsBtn.setAttribute('aria-pressed', App.prefs.showAlts ? 'true' : 'false'); altsBtn.textContent = App.prefs.showAlts ? 'Hide alternatives' : 'Show alternatives'; } },
    }, App.prefs.showAlts ? 'Hide alternatives' : 'Show alternatives');
    const logEl = h('div.log', { 'aria-live': 'off' });
    const boardWrap = h('div.board-wrap', view.el);
    const controls = h('div.controls', playBtn, stepBtn, seg, altsBtn, h('span.spacer'), skipBtn);
    root.appendChild(h('div.screen-head',
      h('div.stack', { style: { gap: '4px' } },
        h('div.row', h('span.eyebrow', enc.name), roundEl, stormEl),
      ),
    ));
    root.appendChild(h('div.battle-grid',
      h('div.battle-main', queueEl, thought, boardWrap, controls),
      h('div.panel.battle-side', h('div.eyebrow', 'Battle log'), logEl),
    ));

    // -------------------------------------------------------- helpers
    function unitView(uid) {
      const u = B.U(s, uid);
      const d = disp[uid] || {};
      return Object.assign({}, u, { hp: d.hp != null ? d.hp : u.hp, shield: d.shield != null ? d.shield : u.shield, st: d.st || Object.keys(u.st), alive: true });
    }
    function refreshToken(uid) { if (view.tokens.has(uid)) view.updateToken(unitView(uid)); }
    function sq(x, y) { return AG.squareName(s.board, x, y); }
    function log(cls, parts) {
      const ln = h('div.ln.' + cls, parts);
      logEl.appendChild(ln);
      while (logEl.childNodes.length > 400) logEl.removeChild(logEl.firstChild);
      logEl.scrollTop = logEl.scrollHeight;
    }
    function renderQueue(activeUid) {
      UI.clear(queueEl);
      const q = B.projectedQueue(s);
      const add = (uid, cls) => {
        const u = B.U(s, uid);
        if (!u || !u.alive) return;
        queueEl.appendChild(h('div.qchip.' + (u.side === 0 ? 'p' : 'e') + (cls ? '.' + cls : ''), { 'data-tip': u.name + ' · SPD ' + B.spd(s, u) },
          UI.icon(u), h('span.spd', B.spd(s, u))));
      };
      if (activeUid) add(activeUid, 'now');
      for (const uid of q.now) if (uid !== activeUid) add(uid);
      queueEl.appendChild(h('div.qsep', 'next'));
      const nx = h('div.row.qnext', { style: { gap: '6px', flexWrap: 'nowrap' } });
      for (const uid of q.next) {
        const u = B.U(s, uid);
        nx.appendChild(h('div.qchip.' + (u.side === 0 ? 'p' : 'e'), UI.icon(u)));
      }
      queueEl.appendChild(nx);
      const now = queueEl.querySelector('.now');
      if (now && now.scrollIntoView) { try { now.scrollIntoView({ block: 'nearest', inline: 'center' }); } catch (e) { /* ignore */ } }
    }
    // Fatigue status: when the storm arrives, or how hard it is hitting.
    function stormText(round) {
      const at = s.rules.storm;
      if (round >= at) {
        stormEl.textContent = '⚡ Arcane Storm: ' + (round - at + 1) + ' damage to every unit each round';
        stormEl.className = 'storm-warn';
      } else {
        stormEl.textContent = at - round <= 2 ? '⚡ Arcane Storm in ' + (at - round) : 'Storm from round ' + at;
        stormEl.className = at - round <= 2 ? 'storm-warn' : 'faint';
      }
      stormEl.setAttribute('data-tip', 'Fatigue: from round ' + at + ' (sooner if three rounds pass without anyone being hurt) every unit takes 1 damage at the start of the round, then 2, then 3… so every battle ends.');
    }
    function showThought(uid, reason, alts, at) {
      const u = B.U(s, uid);
      const where = at || [u.x, u.y];
      UI.clear(thought);
      thought.appendChild(h('div.ic.qchip.' + (u.side === 0 ? 'p' : 'e'), { style: { width: '40px', height: '40px' } }, UI.icon(u)));
      thought.appendChild(h('div.who', (u.side === 0 ? 'Your ' : 'Enemy ') + u.name + ' · ', h('span.sq', sq(where[0], where[1]))));
      thought.appendChild(h('div.what', reason));
      if (App.prefs.showAlts && alts && alts.length) {
        thought.appendChild(h('div.alts', h('span.faint', 'Also weighed: '), alts.map((a, i) => h('span', (i ? ' · ' : '') + a.label + ' ', h('span.mono.faint', '(' + (a.delta <= -99 ? 'far worse' : a.delta.toFixed(1)) + ')')))));
      }
    }
    function inspect(uid) {
      const u = B.U(s, uid);
      if (!u) return;
      UI.modal(() => UI.inspector(u, { live: true, state: s }), {});
    }

    // ------------------------------------------------------- controls
    function togglePause() {
      paused = !paused;
      playBtn.textContent = paused ? '▶' : '❚❚';
      playBtn.setAttribute('aria-label', paused ? 'Play' : 'Pause');
      if (!paused && resume) { const r = resume; resume = null; r(); }
    }
    function step() {
      stepOnce = true;
      if (paused && resume) { const r = resume; resume = null; r(); }
      else if (!paused) togglePause();
    }
    function setSpeed(k) {
      view.k = k;
      App.prefs.speed = k;
      App.savePrefs();
      Array.from(seg.children).forEach((b, i) => b.classList.toggle('on', SPEEDS[i].k === k));
    }
    async function skip() {
      if (skipping || s.over) return;
      skipping = true;
      skipBtn.disabled = true;
      UI.clear(thought);
      thought.appendChild(h('div.ic', '⏭'));
      thought.appendChild(h('div.who', 'Resolving'));
      thought.appendChild(h('div.what', 'Playing out the rest of the battle…'));
      if (paused) togglePause();
    }
    const wait = (ms) => (skipping ? Promise.resolve() : UI.wait(ms * view.k));

    // ------------------------------------------------------- playback
    async function play(evs) {
      for (const e of evs) {
        if (!alive) return;
        if (skipping) { applyQuiet(e); continue; }
        switch (e.type) {
          case 'round':
            roundEl.textContent = 'Round ' + e.round;
            stormText(e.round);
            log('sys', 'Round ' + e.round);
            await view.banner('Round ' + e.round, e.storm ? 'storm' : '');
            break;
          case 'stormEarly':
            stormText(e.round);
            log('sys', 'Stalemate: the Arcane Storm gathers early');
            await view.banner('Stalemate!', 'storm');
            break;
          case 'storm':
            stormText(s.round);
            if (!e.label) log('sys', 'Arcane Storm: ' + e.dmg + ' damage to everything');
            await view.banner(e.label || 'Arcane Storm ' + e.dmg, 'storm');
            break;
          case 'queue':
            renderQueue(s.active);
            break;
          case 'turn':
            view.setFlag('active', e.uid);
            renderQueue(e.uid);
            break;
          case 'think': {
            const u = B.U(s, e.uid);
            showThought(e.uid, e.reason, e.alts, e.from);
            const from = e.from || [u.x, u.y];
            const dest = e.mv >= 0 ? '→' + sq(e.mv % s.board.w, (e.mv / s.board.w) | 0) : '';
            log(u.side === 0 ? 'p' : 'e', [UI.icon(u) + ' ', h('b', u.name), ' ', h('span.sq', sq(from[0], from[1]) + dest), ' ', e.reason]);
            await wait(520);
            break;
          }
          case 'skip': {
            const u = B.U(s, e.uid);
            view.floatOn(e.uid, e.why === 'frozen' ? '🧊 frozen' : '💫 stunned', 'note');
            showThought(e.uid, (e.why === 'frozen' ? 'Frozen solid' : 'Stunned') + ': loses this turn.');
            log(u.side === 0 ? 'p' : 'e', [UI.icon(u) + ' ', h('b', u.name), ' is ' + e.why + ' and loses its turn.']);
            await wait(500);
            break;
          }
          case 'move':
            await view.animMove(e.uid, e.to, e.kind, e.path);
            break;
          case 'swap':
            await view.animSwap(e.a, e.b, e.pa, e.pb);
            break;
          case 'attack':
            if (e.melee) await view.lunge(e.uid, e.to);
            else await view.projectile(e.from, e.to, e.vfx, e.vfx === 'shell');
            break;
          case 'ability': {
            const A = AG.Abilities[e.id];
            view.callout(e.uid, A.icon + ' ' + A.name);
            await view.flash(e.uid, UI.VFX[A.vfx] || '#fff');
            break;
          }
          case 'aoe':
            await view.aoe(e.cells, e.r, e.vfx);
            break;
          case 'chain':
            await view.zap(e.from, e.to, 'lightning');
            break;
          case 'beam':
            await view.zap(e.from, e.to, 'beam');
            break;
          case 'dmg': {
            disp[e.uid] = Object.assign(disp[e.uid] || {}, { hp: e.hp, shield: e.shield });
            if (view.tokens.has(e.uid)) {
              view.floatOn(e.uid, '−' + e.amt + (e.absorbed ? ' ⛨' : ''), 'dmg' + (e.amt >= 6 ? ' big' : ''));
              // Make synergies visible: Charge +2, Shatter +2, Marked +1...
              const plus = (e.mods || []).filter((m) => m.amt > 0);
              if (plus.length) view.floatOn(e.uid, plus.map((m) => m.label + ' +' + m.amt).join(' · '), 'note bonus', 1.35);
              view.shake(e.uid);
              refreshToken(e.uid);
            }
            await wait(e.kind === 'storm' || e.kind === 'dot' ? 160 : 120);
            break;
          }
          case 'heal':
            disp[e.uid] = Object.assign(disp[e.uid] || {}, { hp: e.hp });
            view.floatOn(e.uid, '+' + e.amt, 'heal');
            refreshToken(e.uid);
            if (!e.quiet) await wait(160);
            break;
          case 'shield':
            disp[e.uid] = Object.assign(disp[e.uid] || {}, { shield: e.shield });
            view.floatOn(e.uid, '+' + e.amt + ' ⛨', 'shield');
            refreshToken(e.uid);
            if (!e.quiet) await wait(160);
            break;
          case 'status': {
            disp[e.uid] = Object.assign(disp[e.uid] || {}, { st: e.st });
            refreshToken(e.uid);
            const S = UI.STATUS[e.key];
            if (S && !e.removed) view.floatOn(e.uid, S.icon + ' ' + S.name, 'note', 1.1);
            break;
          }
          case 'buff':
            view.floatOn(e.uid, '+ATK (' + e.label + ')', 'note', 1.1);
            break;
          case 'death': {
            const u = B.U(s, e.uid);
            log('death', [UI.icon(u) + ' ', h('b', u.name), ' falls.']);
            await view.fadeOut(e.uid, false);
            break;
          }
          case 'fall': {
            const u = B.U(s, e.uid);
            view.floatOn(e.uid, 'into the abyss!', 'note');
            log('death', [UI.icon(u) + ' ', h('b', u.name), ' is knocked into the chasm.']);
            await view.fadeOut(e.uid, true);
            break;
          }
          case 'vanish':
            view.removeToken(e.uid);
            break;
          case 'summon':
            disp[e.uid] = { hp: e.unit.hp, shield: e.unit.shield, st: e.unit.st };
            await view.fadeIn(Object.assign({}, B.U(s, e.uid), { hp: e.unit.hp, x: e.unit.x, y: e.unit.y, st: e.unit.st }));
            break;
          case 'promote':
            disp[e.uid] = Object.assign(disp[e.uid] || {}, { hp: e.unit.hp });
            refreshToken(e.uid);
            view.floatOn(e.uid, '♛ Promoted!', 'note big', 1.2);
            log(e.unit.side === 0 ? 'p' : 'e', [h('b', e.unit.name), ' is promoted!']);
            await view.flash(e.uid, '#f1d08a');
            break;
          case 'revive':
            disp[e.uid] = Object.assign(disp[e.uid] || {}, { hp: e.hp });
            refreshToken(e.uid);
            view.floatOn(e.uid, e.label + '!', 'note big', 1.2);
            await view.flash(e.uid, '#86d08a');
            break;
          case 'negate':
            view.floatOn(e.uid, e.label === 'Zen' ? 'Dodged!' : e.label + '!', 'note');
            await wait(150);
            break;
          case 'resist':
            view.floatOn(e.uid, 'Immune', 'note');
            break;
          case 'bump':
            view.shake(e.uid);
            break;
          case 'note':
            view.floatOn(e.uid, e.text, 'note', 1.1);
            break;
          case 'timeout':
            await view.banner('Out of time', 'storm');
            break;
          case 'survived':
            await view.banner('Survived!');
            break;
          default:
            break;
        }
      }
    }
    function applyQuiet(e) {
      if (e.type === 'dmg' || e.type === 'heal' || e.type === 'shield' || e.type === 'revive') {
        disp[e.uid] = Object.assign(disp[e.uid] || {}, e.hp != null ? { hp: e.hp } : {}, e.shield != null ? { shield: e.shield } : {});
      } else if (e.type === 'status') disp[e.uid] = Object.assign(disp[e.uid] || {}, { st: e.st });
      else if (e.type === 'summon') disp[e.uid] = { hp: e.unit.hp, shield: e.unit.shield, st: e.unit.st };
      else if (e.type === 'round') roundEl.textContent = 'Round ' + e.round;
    }
    function syncAll() {
      for (const u of s.units) if (u.alive) disp[u.uid] = { hp: u.hp, shield: u.shield, st: Object.keys(u.st) };
      view.sync(s.units.filter((u) => u.alive).map((u) => unitView(u.uid)));
    }

    async function loop() {
      await UI.wait(350);
      while (alive && !s.over) {
        if (paused && !skipping) {
          await new Promise((r) => { resume = r; });
          if (!alive) return;
        }
        const r = B.step(s);
        const evs = s.ev.splice(0, s.ev.length);
        if (skipping) {
          for (const e of evs) applyQuiet(e);
          if (s.turnCount % 6 === 0) await UI.wait(0);
          continue;
        }
        try {
          await play(evs);
        } catch (err) {
          // A display hiccup must never stall the battle itself.
          console.warn('playback error', err);
        }
        if (r && r.kind === 'turn') syncAll();
        if (stepOnce) {
          stepOnce = false;
          if (!paused) togglePause();
        }
      }
      if (!alive) return;
      syncAll();
      view.setFlag('active', -1);
      finish();
    }

    // ------------------------------------------------------------ report
    function finish() {
      const won = s.winner === 0;
      if (App.battle && App.battle.replay) {
        const m = UI.modal(h('div.end-card',
          h('div.big.' + (won ? 'win' : 'lose'), won ? 'Victory' : 'Defeat'),
          h('p.muted', 'That was a replay; nothing changed. Battles always play out the same way for the same setup, so change something before you retry.'),
          report(),
          h('div.row', { style: { justifyContent: 'center' } }, h('button.btn.primary', { type: 'button', on: { click: () => { m.close(); App.afterBattle(false); } } },
            !isSandbox && App.run.screen === 'reward' ? 'Collect rewards' : 'Back to the war room')),
        ), { dismissable: false });
        return;
      }
      let outcome;
      if (!isSandbox) outcome = won ? AG.Run.battleWon(App.run, s) : { dmg: AG.Run.battleLost(App.run, s) };
      else App.run.stats[won ? 'wins' : 'losses']++;
      App.save();
      log('sys', won ? 'Victory' : 'Defeat');
      const card = h('div.end-card',
        h('div.big.' + (won ? 'win' : 'lose'), won ? 'Victory' : 'Defeat'),
        h('p.muted', won ? 'Won in ' + AG.plural(s.round, 'round') + '.' : lossText(outcome)),
        report(),
      );
      const buttons = h('div.row', { style: { justifyContent: 'center' } });
      card.appendChild(buttons);
      const m = UI.modal(card, { dismissable: false });
      if (won) {
        buttons.appendChild(h('button.btn.primary', { type: 'button', on: { click: () => { m.close(); App.afterBattle(true); } } }, isSandbox ? 'Back to setup' : 'Collect rewards'));
        buttons.appendChild(h('button.btn', { type: 'button', on: { click: () => { m.close(); App.replay(); } } }, 'Watch again'));
        if (isSandbox) buttons.appendChild(h('button.btn', { type: 'button', on: { click: () => { m.close(); App.go('sandbox'); } } }, 'Other fights'));
      } else if (!isSandbox && App.run.screen === 'gameover') {
        buttons.appendChild(h('button.btn.primary', { type: 'button', on: { click: () => { m.close(); App.afterBattle(false); } } }, 'Your Resolve breaks…'));
      } else {
        buttons.appendChild(h('button.btn.primary', { type: 'button', on: { click: () => { m.close(); App.afterBattle(false); } } }, 'Adjust & retry'));
        buttons.appendChild(h('button.btn', { type: 'button', on: { click: () => { m.close(); App.replay(); } } }, 'Watch again'));
        if (isSandbox) buttons.appendChild(h('button.btn', { type: 'button', on: { click: () => { m.close(); App.go('sandbox'); } } }, 'Other fights'));
      }
    }
    function lossText(o) {
      if (isSandbox || !o) return 'Your army was defeated. Adjust it and try again.';
      const run = App.run;
      if (run.mode === 'casual') return 'Your army was defeated. (Casual mode: no Resolve lost.)';
      return 'Your Resolve drops by ' + o.dmg + ' (' + run.resolve + '/' + run.maxResolve + ' left). The enemy holds the board; rethink your army and try again.';
    }
    function report() {
      const st = s.stats || {};
      const mine = s.units.filter((u) => u.side === 0 && st[u.uid]);
      const foes = s.units.filter((u) => u.side === 1 && st[u.uid]);
      let max = 1;
      for (const u of s.units) { const r = st[u.uid]; if (r) max = Math.max(max, r.dealt, r.taken, r.healed); }
      const row = (u) => {
        const r = st[u.uid];
        const bar = (cls, label, n) => h('div.rep-bar.' + cls, h('span', label), h('span.track', h('i', { style: { width: (100 * n) / max + '%' } })), h('span.n', n));
        return h('div.rep-row',
          h('div.ic.qchip.' + (u.side === 0 ? 'p' : 'e'), { style: { width: '34px', height: '34px', fontSize: '18px' } }, UI.icon(u)),
          h('div.nm', u.name, r.kills ? h('span.faint', AG.plural(r.kills, 'kill')) : null, !u.alive ? h('span.dead', 'fell') : null),
          h('div.rep-bars', { style: { gridColumn: '2' } },
            bar('dealt', 'dealt', r.dealt), bar('taken', 'taken', r.taken), r.healed ? bar('healed', 'healed', r.healed) : null),
        );
      };
      const mineRows = mine.filter((u) => !u.summoned || st[u.uid].dealt > 0).sort((a, b) => st[b.uid].dealt + st[b.uid].healed - (st[a.uid].dealt + st[a.uid].healed));
      const foeRows = foes.sort((a, b) => st[b.uid].dealt - st[a.uid].dealt).slice(0, 3);
      return h('div.report', { style: { textAlign: 'left' } },
        h('div.sec-title', 'Your army'),
        mineRows.map(row),
        foeRows.length ? h('div.sec-title', 'Their biggest threats') : null,
        foeRows.map(row),
      );
    }

    function fit() {
      const w = boardWrap.clientWidth || Math.min(window.innerWidth - 32, 760);
      view.fit(w, Math.max(300, window.innerHeight * (window.innerWidth < 980 ? 0.56 : 0.7)));
    }
    function onKey(e) {
      if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') || document.querySelector('.modal-back')) return;
      if (e.key === ' ') { e.preventDefault(); togglePause(); }
      else if (e.key === 'ArrowRight' || e.key === '.') step();
      else if (e.key === '1' || e.key === '2' || e.key === '3') setSpeed(SPEEDS[+e.key - 1].k);
      else if (e.key === 's' || e.key === 'S') skip();
    }
    root.onMount = function () {
      fit();
      App.onResize = fit;
      stormText(0);
      syncAll();
      renderQueue(0);
      log('sys', enc.name);
      document.addEventListener('keydown', onKey);
      loop();
    };
    root.onUnmount = function () {
      alive = false;
      document.removeEventListener('keydown', onKey);
      if (resume) resume();
    };
    return root;
  };
})(globalThis.AG = globalThis.AG || {});
