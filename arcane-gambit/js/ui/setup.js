/* The war room: pick units within the supply and slot limits, give them
   talents and runes, and place them on your side of the board. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;
  const B = AG.B;
  const Run = AG.Run;

  function deployCells(board) {
    const out = [];
    for (let i = 0; i < board.n; i++) if (board.deploy[i]) out.push(i);
    return out;
  }

  // Re-use the last army on a new board: front-liners to the front row, the
  // rest behind, both centred.
  function adaptArmy(prev, board) {
    const cells = deployCells(board);
    const rows = Array.from(new Set(cells.map((i) => (i / board.w) | 0))).sort((a, b) => a - b);
    const mid = (board.w - 1) / 2;
    const byCenter = (a, b) => Math.abs((a % board.w) - mid) - Math.abs((b % board.w) - mid);
    const front = cells.filter((i) => ((i / board.w) | 0) === rows[0]).sort(byCenter);
    const back = cells.filter((i) => ((i / board.w) | 0) !== rows[0]).sort((a, b) => ((a / board.w) | 0) - ((b / board.w) | 0) || byCenter(a, b));
    const minY = Math.min.apply(null, prev.map((e) => e.y));
    const sorted = prev.slice().sort((a, b) => a.y - b.y || Math.abs(a.x - mid) - Math.abs(b.x - mid));
    const used = new Set();
    const out = [];
    for (const e of sorted) {
      const pool = e.y === minY ? front.concat(back) : back.concat(front);
      const c = pool.find((i) => !used.has(i));
      if (c == null) break;
      used.add(c);
      out.push({ def: e.def, x: c % board.w, y: (c / board.w) | 0, talents: (e.talents || []).slice(), rune: e.rune || null });
    }
    return out;
  }
  UI.adaptArmy = adaptArmy;

  UI.SetupScreen = function (App) {
    const run = App.run;
    const enc = AG.Encounters[run.battle.enc];
    const parsed = AG.parseBoard(enc.map, enc.legend);
    const board = parsed.board;
    if (!run.battle.formation) run.battle.formation = [];
    const F = run.battle.formation;
    // Saved formations can predate a map change: keep only legal placements.
    for (let i = F.length - 1; i >= 0; i--) {
      const e = F[i];
      const legal = AG.inBounds(board, e.x, e.y) && board.deploy[e.y * board.w + e.x] && run.units.indexOf(e.def) >= 0 &&
        F.findIndex((o) => o.x === e.x && o.y === e.y) === i && AG.Units[e.def];
      if (!legal) F.splice(i, 1);
      else {
        e.talents = (e.talents || []).filter((t) => AG.Talents[t] && AG.Talents[t].unit === e.def);
        if (e.rune && !AG.Runes[e.rune]) e.rune = null;
      }
    }
    const narrow = () => window.innerWidth < 980;
    let sel = { kind: null };
    let preview = null;
    let showDanger = false;

    const root = h('div.setup');
    const view = new UI.BoardView({
      board, theme: enc.theme, maxCell: 72,
      onCell: onCell, onToken: onToken,
      canDrag: (uid) => uid <= F.length,
      canDrop: (uid, x, y) => !!board.deploy[y * board.w + x],
      onDrop: onDrop,
    });

    // -------------------------------------------------------- derived
    function rebuildPreview() {
      preview = B.create(enc, Run.armyFor(run, F), Object.assign({ record: false }, Run.battleOpts(run)));
      B.buildQueue(preview);
    }
    function entryAt(x, y) { return F.findIndex((e) => e.x === x && e.y === y); }
    function previewUnitForEntry(i) { return preview.units[i]; }
    function enemyUnits() { return preview.units.filter((u) => u.side === 1); }

    // -------------------------------------------------------- actions
    function place(def, x, y) {
      const v = Run.validate(run, enc, F.concat([{ def, x, y, talents: [], rune: null }]));
      if (F.length >= v.lim.slots) { UI.toast('No unit slots left (' + v.lim.slots + ' max).'); return false; }
      const cost = Run.formationCost(run, F) + AG.Units[def].cost;
      if (cost > v.lim.supply) { UI.toast('Not enough supply: ' + AG.Units[def].name + ' costs ' + AG.Units[def].cost + '.'); return false; }
      F.push({ def, x, y, talents: [], rune: null });
      sel = { kind: 'placed', i: F.length - 1 };
      changed();
      return true;
    }
    function onCell(x, y) {
      const i = y * board.w + x;
      const at = entryAt(x, y);
      if (at >= 0) { onPlaced(at); return; }
      if (!board.deploy[i]) {
        if (sel.kind) { sel = { kind: null }; refresh(); }
        return;
      }
      if (sel.kind === 'card') place(sel.def, x, y);
      else if (sel.kind === 'placed') { F[sel.i].x = x; F[sel.i].y = y; changed(); }
      else UI.toast('Pick a unit from your army below, then tap a gold square.');
    }
    function onToken(uid) {
      if (uid <= F.length) { onPlaced(uid - 1); return; }
      const k = enemyUnits().indexOf(B.U(preview, uid));
      if (k < 0) return;
      sel = { kind: 'enemy', k };
      refresh();
      if (narrow()) openInspector();
    }
    function onPlaced(i) {
      if (sel.kind === 'placed' && sel.i === i) { if (narrow()) openInspector(); return; }
      sel = { kind: 'placed', i };
      refresh();
    }
    function onDrop(uid, x, y) {
      const i = uid - 1;
      if (!board.deploy[y * board.w + x]) return;
      const other = entryAt(x, y);
      if (other >= 0 && other !== i) { F[other].x = F[i].x; F[other].y = F[i].y; }
      F[i].x = x; F[i].y = y;
      sel = { kind: 'placed', i };
      changed();
    }
    function removeEntry(i) {
      F.splice(i, 1);
      sel = { kind: null };
      changed();
    }
    function toggleTalent(i, tid) {
      const e = F[i];
      const k = e.talents.indexOf(tid);
      const slots = Run.talentSlots(run, e.def);
      if (k >= 0) e.talents.splice(k, 1);
      else {
        const lim = Run.limits(run, enc);
        const add = Run.talentCost(run, tid) - (e.talents.length >= slots ? Run.talentCost(run, e.talents[0]) : 0);
        if (Run.formationCost(run, F) + add > lim.supply) { UI.toast('Not enough supply for ' + AG.Talents[tid].name + '.'); return; }
        if (e.talents.length >= slots) e.talents.shift();
        e.talents.push(tid);
      }
      changed();
    }
    function setRune(i, rid) {
      const e = F[i];
      if (rid) {
        const lim = Run.limits(run, enc);
        const add = AG.Runes[rid].cost - (e.rune ? AG.Runes[e.rune].cost : 0);
        if (Run.formationCost(run, F) + add > lim.supply) { UI.toast('Not enough supply for ' + AG.Runes[rid].name + '.'); return; }
      }
      e.rune = rid;
      changed();
    }
    function changed() {
      App.saveSoon();
      refresh();
    }

    // -------------------------------------------------------- rendering
    const head = h('div.screen-head',
      h('div.stack', { style: { gap: '4px' } },
        h('div.row', { style: { gap: '8px' } },
          h('span.tier' + (run.battle.tier === 'elite' ? '.elite' : run.battle.tier === 'boss' ? '.boss' : ''), run.battle.tier === 'battle' ? 'Battle' : run.battle.tier === 'event' ? 'Challenge' : run.battle.tier),
          run.battle.attempts ? h('span.chip.garnet', 'Attempt ' + (run.battle.attempts + 1)) : null,
          h('span.chip', board.w + '×' + board.h + ' board'),
        ),
        h('h2', enc.name),
        h('p.flavor', enc.flavor),
        enc.objective && enc.objective.type === 'assassinate' ? h('p', { style: { color: 'var(--brass-2)', fontWeight: 700 } }, 'Objective: defeat the marked commander. The rest of the army falls with it.') : null,
      ),
    );
    const meters = h('div.meters');
    const queueEl = h('div.queue', { 'aria-label': 'Turn order preview' });
    const selBar = h('div.row');
    const rosterEl = h('div.roster');
    const actions = h('div.row.setup-actions');
    const tools = h('div.row');
    const errorsEl = h('div.errors');
    const sideEl = h('div.panel.side');
    const boardWrap = h('div.board-wrap', view.el);

    const main = h('div.setup-main',
      meters,
      h('div', h('div.eyebrow', 'Turn order · fastest first'), queueEl),
      boardWrap,
      actions,
      errorsEl,
      selBar,
      h('div.row', h('div.eyebrow', 'Your army'), h('span.hint', 'Tap a unit, then a gold square. Tap a placed piece, then another square, to move it.')),
      rosterEl,
      tools,
    );
    root.appendChild(head);
    if (!App.prefs.seenWarRoom) {
      const coach = h('div.coach',
        h('div.coach-steps',
          h('div', h('b', '1. Draft'), ' Tap a unit in your army below. Units, talents and runes all cost supply; the fight limits how many units you may bring.'),
          h('div', h('b', '2. Deploy'), ' Tap a gold square to place it. Tap a placed piece for talents and runes, or to move it. Tap enemies to see exactly what they do.'),
          h('div', h('b', '3. Watch'), ' Press Begin. Every unit acts once per round, fastest first, and thinks for itself. If you lose, rethink and retry.'),
        ),
        h('button.btn.small', { type: 'button', on: { click: () => { App.prefs.seenWarRoom = true; App.savePrefs(); coach.remove(); } } }, 'Got it'),
      );
      root.appendChild(coach);
    }
    root.appendChild(h('div.setup-grid', main, sideEl));

    function renderMeters() {
      const v = Run.validate(run, enc, F);
      UI.clear(meters);
      const sp = Math.min(100, (100 * v.cost) / Math.max(1, v.lim.supply));
      meters.appendChild(h('div.meter' + (v.cost > v.lim.supply ? '.over' : ''),
        h('span.lbl', 'Supply'), h('span.bar', h('i', { style: { width: sp + '%' } })), h('span.v', v.cost + '/' + v.lim.supply)));
      meters.appendChild(h('div.meter' + (F.length > v.lim.slots ? '.over' : ''),
        h('span.lbl', 'Units'), h('span.v', F.length + '/' + v.lim.slots)));
      if (App.mode === 'sandbox' && run.relics && run.relics.length) {
        const rr = h('div.relic-row');
        for (const id of run.relics) rr.appendChild(UI.relicIcon(id));
        meters.appendChild(rr);
      }
    }
    function renderQueue() {
      UI.clear(queueEl);
      for (const uid of preview.queue) {
        const u = B.U(preview, uid);
        queueEl.appendChild(h('div.qchip.' + (u.side === 0 ? 'p' : 'e'), { 'data-tip': u.name + ' · SPD ' + B.spd(preview, u), 'aria-label': u.name },
          UI.icon(u), h('span.spd', B.spd(preview, u))));
      }
    }
    function renderRoster() {
      UI.clear(rosterEl);
      const lim = Run.limits(run, enc);
      const left = lim.supply - Run.formationCost(run, F);
      const units = run.units.slice().sort((a, b) => AG.Units[a].cost - AG.Units[b].cost || AG.Units[a].name.localeCompare(AG.Units[b].name));
      for (const def of units) {
        const card = UI.rosterCard(def, {
          rank: run.ranks[def] || 0,
          sel: sel.kind === 'card' && sel.def === def,
          cant: AG.Units[def].cost > left || F.length >= lim.slots,
        });
        card.addEventListener('click', function () {
          if (card.dataset.dragged) return;
          sel = sel.kind === 'card' && sel.def === def ? { kind: null } : { kind: 'card', def };
          refresh();
        });
        enableCardDrag(card, def);
        rosterEl.appendChild(card);
      }
    }
    function renderSelBar() {
      UI.clear(selBar);
      if (sel.kind === 'placed') {
        const e = F[sel.i];
        const u = previewUnitForEntry(sel.i);
        selBar.appendChild(h('span.chip.brass', UI.icon(u) + ' ' + u.name + ' · ' + AG.squareName(board, e.x, e.y)));
        if (e.talents.length) selBar.appendChild(h('span.chip', e.talents.map((t) => AG.Talents[t].name).join(', ')));
        if (e.rune) selBar.appendChild(h('span.chip', AG.Runes[e.rune].icon + ' ' + AG.Runes[e.rune].name));
        selBar.appendChild(h('button.btn.small', { type: 'button', on: { click: openInspector } }, narrow() ? 'Upgrades & details' : 'Details'));
        selBar.appendChild(h('button.btn.small.danger', { type: 'button', on: { click: () => removeEntry(sel.i) } }, 'Remove'));
        selBar.appendChild(h('span.hint', 'Tap a gold square to move it.'));
      } else if (sel.kind === 'card') {
        const d = AG.Units[sel.def];
        selBar.appendChild(h('span.chip.brass', d.icon + ' ' + d.name + ' · ' + d.cost + ' supply'));
        selBar.appendChild(h('span.hint', 'Tap a gold square to deploy.'));
        selBar.appendChild(h('button.btn.small', { type: 'button', on: { click: openInspector } }, 'Details'));
      }
    }
    function inspectorContent() {
      if (sel.kind === 'placed') {
        const i = sel.i;
        const e = F[i];
        const u = previewUnitForEntry(i);
        return UI.inspector(u, {
          loadout: {
            entry: e,
            slots: Run.talentSlots(run, e.def),
            talentCost: (t) => Run.talentCost(run, t),
            runesFree: Run.runesFree(run, F, i),
            onTalent: (t) => toggleTalent(i, t),
            onRune: (r) => setRune(i, r),
            onRemove: () => removeEntry(i),
          },
        });
      }
      if (sel.kind === 'enemy') {
        const u = enemyUnits()[sel.k];
        return u ? UI.inspector(u, {}) : h('p', '');
      }
      if (sel.kind === 'card') {
        const u = B.makeUnit(sel.def, 0, 0, 0, { rank: run.ranks[sel.def] || 0 });
        return h('div.stack', UI.inspector(u, { showTalents: true }), h('p.hint', 'Talents and runes are chosen after you place the unit.'));
      }
      // Nothing selected: a briefing on the enemy.
      const list = h('div.stack', { style: { gap: '6px' } });
      enemyUnits().forEach(function (u, k) {
        list.appendChild(h('button.opt', { type: 'button', on: { click: () => { sel = { kind: 'enemy', k }; refresh(); if (narrow()) openInspector(); } } },
          h('span.t', UI.icon(u) + ' ' + u.name), h('span.c', 'HP ' + u.maxHp + ' · ATK ' + u.atk + ' · SPD ' + u.spd), h('span.d', AG.Units[u.def].blurb || '')));
      });
      return h('div.stack',
        h('div.sec-title', 'Enemy forces'),
        list,
        h('p.hint', 'Speed decides the turn order: every unit acts once per round, fastest first. Ties go to your side.'),
        h('p.hint', 'Fatigue: from round ' + (enc.storm || 12) + ' (or after three rounds with no damage) an Arcane Storm hits every unit each round for 1, then 2, then 3…, so stalemates end.'),
      );
    }
    let modalRef = null;
    function openInspector() {
      if (!narrow()) { refresh(); return; }
      if (modalRef) modalRef.close();
      modalRef = UI.modal(function () { return h('div', inspectorContent()); }, { onClose: () => { modalRef = null; } });
    }
    // Show where the selected piece can go and what it threatens, plus the
    // optional danger overlay of every square the enemy can hit on turn one.
    function renderReach(u) {
      let mv = [], at = [];
      if (u) {
        const info = AG.AI.reachInfo(preview, u, false);
        mv = info.move;
        at = info.attack;
      }
      const both = mv.filter((i) => at.indexOf(i) >= 0);
      view.mark('hl-move', mv.filter((i) => both.indexOf(i) < 0));
      view.mark('hl-attack', at.filter((i) => both.indexOf(i) < 0));
      view.mark('hl-both', both);
      // Heat map: how many enemies could strike each square on their first turn.
      const heat = new Uint8Array(board.n);
      if (showDanger) for (const e of enemyUnits()) for (const i of AG.AI.reachInfo(preview, e, true).attack) heat[i]++;
      const lv = [[], [], []];
      for (let i = 0; i < board.n; i++) if (heat[i]) lv[Math.min(3, heat[i]) - 1].push(i);
      view.mark('danger1', lv[0]);
      view.mark('danger2', lv[1]);
      view.mark('danger3', lv[2]);
    }
    function renderSide() {
      UI.clear(sideEl);
      sideEl.appendChild(inspectorContent());
    }
    function renderActions() {
      UI.clear(actions);
      UI.clear(tools);
      UI.clear(errorsEl);
      const v = Run.validate(run, enc, F);
      if (!v.ok && F.length) errorsEl.textContent = v.errors.join(' ');
      actions.appendChild(h('button.btn.primary', { type: 'button', disabled: !v.ok, on: { click: begin } }, '⚔ Begin battle'));
      actions.appendChild(h('span.mini-meter.mono' + (v.cost > v.lim.supply ? '.over' : ''), v.cost + '/' + v.lim.supply + ' supply · ' + F.length + '/' + v.lim.slots + ' units'));
      if (!F.length && run.lastArmy && run.lastArmy.length) {
        tools.appendChild(h('button.btn.small', { type: 'button', on: { click: useLast } }, '↺ Use last army'));
      }
      tools.appendChild(h('button.btn.small' + (showDanger ? '.on-toggle' : ''), {
        type: 'button', 'aria-pressed': showDanger ? 'true' : 'false',
        'data-tip': 'Shades every square the enemy could strike on its first turn. Darker means more enemies can reach it.',
        on: { click: () => { showDanger = !showDanger; refresh(); } },
      }, showDanger ? 'Hide enemy reach' : 'Show enemy reach'));
      if (F.length) tools.appendChild(h('button.btn.small', { type: 'button', on: { click: () => { F.length = 0; sel = { kind: null }; changed(); } } }, 'Clear board'));
      if (App.mode === 'sandbox') tools.appendChild(h('button.btn.small.ghost', { type: 'button', on: { click: () => App.go('sandbox') } }, '← Other fights'));
    }
    function useLast() {
      const army = adaptArmy(run.lastArmy, board);
      // Drop anything the run no longer owns or can afford.
      const counts = Run.runeCounts(run);
      for (const e of army) {
        if (run.units.indexOf(e.def) < 0) continue;
        if (e.rune && !(counts[e.rune] > 0)) e.rune = null;
        if (e.rune) counts[e.rune]--;
        e.talents = e.talents.slice(0, Run.talentSlots(run, e.def));
        F.push(e);
      }
      const lim = Run.limits(run, enc);
      while (F.length > lim.slots) F.pop();
      while (Run.formationCost(run, F) > lim.supply && F.length) {
        const e = F[F.length - 1];
        if (e.rune) e.rune = null;
        else if (e.talents.length) e.talents.pop();
        else F.pop();
      }
      UI.toast('Last army deployed. Check the supply before you begin.');
      changed();
    }
    function begin() {
      const v = Run.validate(run, enc, F);
      if (!v.ok) { UI.toast(v.errors[0]); return; }
      App.startBattle();
    }
    function refresh() {
      rebuildPreview();
      view.sync(preview.units);
      view.markDeploy();
      const selEnemy = sel.kind === 'enemy' ? enemyUnits()[sel.k] : null;
      view.setFlag('selected', sel.kind === 'placed' ? sel.i + 1 : selEnemy ? selEnemy.uid : -1);
      renderReach(sel.kind === 'placed' ? preview.units[sel.i] : selEnemy);
      renderMeters();
      renderQueue();
      renderRoster();
      renderSelBar();
      renderSide();
      renderActions();
      if (modalRef) { UI.clear(modalRef.box.lastChild); modalRef.box.lastChild.appendChild(inspectorContent()); }
    }

    // Drag a roster card straight onto the board.
    function enableCardDrag(card, def) {
      card.addEventListener('pointerdown', function (e) {
        // Touch uses tap-to-select, tap-to-place so swipes can still scroll.
        if (e.pointerType === 'touch' || (e.button !== 0 && e.pointerType === 'mouse')) return;
        const sx = e.clientX, sy = e.clientY;
        let ghost = null;
        function move(ev) {
          if (!ghost && Math.abs(ev.clientX - sx) + Math.abs(ev.clientY - sy) > 10) {
            ghost = h('div.qchip.p', { style: { position: 'fixed', zIndex: 70, pointerEvents: 'none', width: view.cell * 0.8 + 'px', height: view.cell * 0.8 + 'px', fontSize: view.cell * 0.4 + 'px' } }, AG.Units[def].icon);
            document.body.appendChild(ghost);
            card.dataset.dragged = '1';
          }
          if (ghost) {
            ghost.style.left = ev.clientX - view.cell * 0.4 + 'px';
            ghost.style.top = ev.clientY - view.cell * 0.4 + 'px';
            const c = view.cellAt(ev.clientX, ev.clientY);
            view.mark('drop-ok', c && board.deploy[c.y * board.w + c.x] && entryAt(c.x, c.y) < 0 ? [c.y * board.w + c.x] : null);
            ev.preventDefault();
          }
        }
        function up(ev) {
          window.removeEventListener('pointermove', move);
          window.removeEventListener('pointerup', up);
          window.removeEventListener('pointercancel', up);
          if (!ghost) return;
          ghost.remove();
          view.mark('drop-ok', null);
          setTimeout(function () { delete card.dataset.dragged; }, 50);
          const c = view.cellAt(ev.clientX, ev.clientY);
          if (c && board.deploy[c.y * board.w + c.x] && entryAt(c.x, c.y) < 0) place(def, c.x, c.y);
        }
        window.addEventListener('pointermove', move, { passive: false });
        window.addEventListener('pointerup', up);
        window.addEventListener('pointercancel', up);
      });
    }

    function fit() {
      const w = boardWrap.clientWidth || Math.min(window.innerWidth - 32, 760);
      view.fit(w, Math.max(320, window.innerHeight * (narrow() ? 0.62 : 0.72)));
    }
    root.onMount = function () {
      fit();
      refresh();
      App.onResize = fit;
    };
    return root;
  };
})(globalThis.AG = globalThis.AG || {});
