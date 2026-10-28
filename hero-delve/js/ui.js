// Hero Delve: the screens. Town (your party, the stash, the way into the tower), the party
// and its kit, and the delve itself: the party plays a floor out on its own while you watch,
// pause, speed it up, or point it at something (a priority).
(function (root) {
  'use strict';
  const AG = root.AG;
  const D = AG.Data;
  const E = AG.Engine;
  const AI = AG.AI;
  const DV = AG.Delve;
  const { UNITS, ABILITIES, TALENTS, MASTERY } = D;

  const $ = (sel, el) => (el || document).querySelector(sel);
  const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const ic = (name) => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const sfx = (n) => AG.Audio && AG.Audio.play(n);
  const PREFS_KEY = 'hero-delve-prefs';

  const UI = (AG.UI = { p: null, board: null, B: null, prefs: { speed: 1 } });
  try {
    Object.assign(UI.prefs, JSON.parse(root.localStorage.getItem(PREFS_KEY) || '{}'));
  } catch (e) {
    /* storage blocked */
  }
  const savePrefs = () => {
    try {
      root.localStorage.setItem(PREFS_KEY, JSON.stringify(UI.prefs));
    } catch (e) {
      /* storage blocked */
    }
  };

  // ------------------------------------------------------------ shared bits

  let toastTimer = 0;
  function toast(msg, ms) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (t.hidden = true), ms || 2400);
  }

  function drawPortraits(el) {
    for (const cv of $$('canvas[data-p]', el)) {
      const [type, team] = cv.dataset.p.split(':');
      AG.Render.portrait(cv, type, team || 'P', {});
    }
  }

  function openSheet(html, bind) {
    const sh = $('#sheet');
    sh.innerHTML = html;
    $('#modal').hidden = false;
    sh.scrollTop = 0;
    drawPortraits(sh);
    for (const b of $$('[data-close]', sh)) b.addEventListener('click', closeSheet);
    if (bind) bind(sh);
  }

  function refreshSheet(html, bind) {
    const sh = $('#sheet');
    const top = sh.scrollTop;
    openSheet(html, bind);
    sh.scrollTop = top;
  }

  function closeSheet() {
    $('#modal').hidden = true;
    $('#sheet').innerHTML = '';
    const f = UI.onSheetClose;
    UI.onSheetClose = null;
    if (f) f();
  }

  function sheetHead(title, sub) {
    return `<div class="sheet-head"><div class="grow"><h3>${title}</h3>${sub ? `<div class="small muted">${sub}</div>` : ''}</div>
      <button class="btn icon-only ghost" data-close aria-label="Close">${ic('close')}</button></div>`;
  }

  function showView(html) {
    $('#battle').hidden = true;
    if (UI.board) UI.board.stop();
    const v = $('#view');
    v.hidden = false;
    v.innerHTML = html;
    v.scrollTop = 0;
    drawPortraits(v);
    return v;
  }

  function startSound() {
    if (AG.Audio) AG.Audio.unlock();
  }

  // ------------------------------------------------------------ town

  function title() {
    UI.B = null;
    const p = UI.p;
    const run = p.run;
    const party = DV.heroes(p);
    const v = showView(`<div class="wrap delve-town">
      <div class="delve-hero-banner">
        <p class="eyebrow">Hero Delve</p>
        <h1>The Forgotten Tower</h1>
        <p class="muted">Five floors down, the Countess waits. Pick your party, kit them out, and send them in: they fight on their own while you watch, pause, or point them at something.</p>
      </div>
      <div class="delve-party-strip">${party
        .map((h) => `<button class="delve-mini" data-hero="${h.id}"><canvas data-p="${h.type}:P"></canvas><b>${esc(h.name)}</b><small>${esc(UNITS[h.type].name)}</small>${run && run.hp[h.id] != null ? hpMini(run.hp[h.id]) : ''}</button>`)
        .join('')}</div>
      <div class="actions delve-main-actions">
        ${run
          ? `<button class="btn primary" id="tContinue">${ic('play')} Continue · ${esc(DV.FLOOR_DEFS[run.floor].name)}</button>
             <button class="btn" id="tAbandon">${ic('flag')} Abandon this delve</button>`
          : `<button class="btn primary" id="tEnter">${ic('swords')} Enter the tower</button>`}
        <button class="btn" id="tParty">${ic('army')} Party &amp; gear</button>
        <button class="btn" id="tHelp">${ic('help')} How it works</button>
      </div>
      <p class="small muted">Stash: ${p.stash.length} items · Delves: ${p.stats.runs} · Countess slain: ${p.stats.clears} · Deepest: ${p.stats.best ? 'Level ' + p.stats.best : '—'}</p>
    </div>`);
    for (const b of $$('[data-hero]', v)) b.onclick = () => heroSheet(DV.heroes(p).find((h) => h.id === b.dataset.hero), title);
    const on = (id, f) => $('#' + id, v) && ($('#' + id, v).onclick = f);
    on('tEnter', () => {
      startSound();
      DV.startRun(p);
      delve();
    });
    on('tContinue', () => {
      startSound();
      delve();
    });
    on('tAbandon', () => {
      DV.endRun(p);
      title();
    });
    on('tParty', () => partyScreen());
    on('tHelp', () => help());
  }

  function hpMini(frac) {
    if (frac <= 0) return '<span class="chip bad">Fallen</span>';
    return `<span class="hpmini"><i style="width:${Math.round(frac * 100)}%"></i></span>`;
  }

  function help() {
    openSheet(`${sheetHead('How it works')}
      <ul class="tips">
        <li><b>Your party</b>: four heroes of any class, plus your Cleric, who always comes. All are Level 3, with their level picks, three class talents, two skills and two pieces of gear.</li>
        <li><b>The stash</b>: skills and gear you own. An item can be on one hero at a time. Packs you wipe out drop more, better the deeper you go; the Countess always drops a legendary.</li>
        <li><b>The delve</b>: tap Begin and your party walks the floor on its own. Monster packs sleep in their rooms until your heroes come within 5 tiles in sight of them (or hit one): then the whole pack wakes and the fight is on. Turns alternate, one unit a side.</li>
        <li><b>Watching</b>: pause any time, speed it up, or tap something. Tap a monster and Priority to send everyone after it; tap a floor tile to send the party there; tap a hero to rally round them.</li>
        <li><b>Floors</b>: clear every monster on a floor and the party takes the stairs down. Hurt heroes stay hurt; a hero who fell gets back up at the shrine on the stairs with ${Math.round(DV.SHRINE_HP * 100)}% HP. Use the town portal between floors to swap kit, then carry on.</li>
        <li><b>Level 5</b>: the Countess. She burns, she raises the dead, and she has a guard. Slay her to beat the tower.</li>
      </ul>
      <div class="actions"><button class="btn primary" data-close>${ic('check')} Got it</button></div>`);
  }

  // ------------------------------------------------------------ party and kit

  function partyScreen() {
    const p = UI.p;
    const v = showView(`<div class="wrap">
      <div class="row"><div class="grow"><p class="eyebrow">Your party</p><h2>Party &amp; gear</h2></div>
        <button class="btn" id="pBack">${ic('undo')} Town</button></div>
      <p class="muted">Tap a hero to change their class, level picks, talents, skills and gear. The Cleric always comes.</p>
      <div class="delve-roster">${DV.heroes(p).map((h, i) => heroCard(h, i)).join('')}</div>
      <div class="actions"><button class="btn" id="pAuto">${ic('star')} Fill empty slots</button></div>
      <h3>Stash</h3>
      <div class="delve-stash">${stashList()}</div>
    </div>`);
    $('#pBack', v).onclick = title;
    $('#pAuto', v).onclick = () => {
      DV.autoKit(p);
      DV.save(p);
      partyScreen();
      toast('Every empty slot filled with the best free fit.');
    };
    for (const b of $$('[data-hero]', v)) b.onclick = () => heroSheet(DV.heroes(p).find((h) => h.id === b.dataset.hero), partyScreen);
  }

  function heroCard(h) {
    const p = UI.p;
    const names = (ids, table) => ids.map((id) => (table[id] ? table[id].name : id));
    const kit = [
      ...names(h.talents, TALENTS),
      ...h.skills.map((uid) => DV.itemDef(DV.itemByUid(p, uid))).filter(Boolean).map((d) => d.name),
      ...h.gear.map((uid) => DV.itemDef(DV.itemByUid(p, uid))).filter(Boolean).map((d) => d.name),
    ];
    return `<button class="delve-card" data-hero="${h.id}">
      <canvas data-p="${h.type}:P"></canvas>
      <span class="nm"><b>${esc(h.name)}</b> <span class="muted">${esc(UNITS[h.type].name)}${h.type === 'cleric' ? ' · always comes' : ''}</span></span>
      <span class="small">${kit.length ? esc(kit.join(' · ')) : '<span class="muted">No kit yet</span>'}</span>
    </button>`;
  }

  function stashList() {
    const p = UI.p;
    if (!p.stash.length) return '<p class="muted">Empty.</p>';
    return p.stash
      .slice()
      .sort((a, b) => (a.kind === b.kind ? DV.itemDef(a).name.localeCompare(DV.itemDef(b).name) : a.kind === 'skill' ? -1 : 1))
      .map((it) => {
        const d = DV.itemDef(it);
        const h = DV.holderOf(p, it.uid);
        return `<div class="delve-item ${d.rarity === 'legendary' ? 'legend' : ''}"><b>${esc(d.name)}</b> <span class="chip">${it.kind}</span>${h ? ` <span class="chip good">${esc(h.name)}</span>` : ''}<div class="small muted">${esc(d.desc)}</div></div>`;
      })
      .join('');
  }

  // A hero's battle numbers, kit included.
  function heroStats(h) {
    const s = { w: 1, h: 1, units: [], byId: {}, occ: [0], nextUid: 1, relics: { P: new Set(), E: new Set() } };
    return E.addUnit(s, Object.assign(DV.specOf(UI.p, h), { team: 'P', x: 0, y: 0 }));
  }

  function heroSheet(h, back) {
    const p = UI.p;
    DV.normalize(p, h);
    const u = heroStats(h);
    const T = UNITS[h.type];
    const pick = (tier) =>
      DV.picks(h.type, tier)
        .map((id) => {
          const a = ABILITIES[id];
          const on = h['a' + tier] === id;
          return `<button class="pick ${on ? 'on' : ''}" data-pick="${tier}:${id}"><span class="pk-head"><b>${esc(a.name)}</b>${on ? ` <span class="chip good">${ic('check')}</span>` : ''}</span><span class="pk-desc">${esc(a.desc)}</span></button>`;
        })
        .join('');
    const talents = DV.classTalents(h.type)
      .map((id) => {
        const t = TALENTS[id];
        const on = h.talents.includes(id);
        return `<button class="pick ${on ? 'on' : ''}" data-tal="${id}"><span class="pk-head"><b>${esc(t.name)}</b>${on ? ` <span class="chip good">${ic('check')}</span>` : ''}</span><span class="pk-desc">${esc(t.desc)}</span></button>`;
      })
      .join('');
    const items = (kind, key) => {
      const list = p.stash.filter((it) => it.kind === kind && D.eligible(h.type, DV.itemDef(it)));
      if (!list.length) return '<p class="small muted">Nothing in the stash this hero can use.</p>';
      return list
        .map((it) => {
          const d = DV.itemDef(it);
          const on = h[key].includes(it.uid);
          const other = !on && DV.holderOf(p, it.uid);
          return `<button class="pick ${on ? 'on' : ''} ${d.rarity === 'legendary' ? 'legend' : ''}" data-item="${key}:${it.uid}"><span class="pk-head"><b>${esc(d.name)}</b>${on ? ` <span class="chip good">${ic('check')}</span>` : other ? ` <span class="chip">${esc(other.name)}</span>` : ''}</span><span class="pk-desc">${esc(d.desc)}</span></button>`;
        })
        .join('');
    };
    const slots = (n, max) => `<span class="lockline">${n}/${max}</span>`;
    refreshSheet(
      `${sheetHead(`${esc(h.name)} · ${esc(T.name)}`, `Level 3 · ${u.maxHp} HP · ${u.pow} power · ${Math.round(u.armor * 100)}% physical / ${Math.round(u.res * 100)}% magic resistance · Move ${u.move}`)}
      <div class="lo-sec"><canvas class="hero-big" data-p="${h.type}:P"></canvas><p class="small">${esc(T.desc)}</p>
        ${h.type !== 'cleric' ? `<button class="btn" id="hClass">${ic('rotate')} Change class</button>` : ''}</div>
      <div class="lo-sec"><div class="eyebrow">Ability</div><div class="picks">${pick(1)}</div></div>
      <div class="lo-sec"><div class="eyebrow">Level 2 ability</div><div class="picks">${pick(2)}</div></div>
      <div class="lo-sec"><div class="eyebrow">Mastery</div><div class="pick static on"><span class="pk-head"><b>${esc(MASTERY[h.type].name)}</b></span><span class="pk-desc">${esc(MASTERY[h.type].desc)}</span></div></div>
      <div class="lo-sec"><div class="eyebrow">Talents ${slots(h.talents.length, DV.SLOTS.talents)}</div><div class="picks">${talents || '<p class="small muted">None for this class.</p>'}</div></div>
      <div class="lo-sec"><div class="eyebrow">Skills ${slots(h.skills.length, DV.SLOTS.skills)}</div><div class="picks">${items('skill', 'skills')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Gear ${slots(h.gear.length, DV.SLOTS.gear)}</div><div class="picks">${items('gear', 'gear')}</div></div>
      <div class="actions"><button class="btn primary" data-close>${ic('check')} Done</button></div>`,
      (sh) => {
        UI.onSheetClose = back;
        const redraw = () => {
          DV.save(p);
          heroSheet(h, back);
        };
        for (const b of $$('[data-pick]', sh))
          b.onclick = () => {
            const [tier, id] = b.dataset.pick.split(':');
            h['a' + tier] = id;
            redraw();
          };
        for (const b of $$('[data-tal]', sh))
          b.onclick = () => {
            const id = b.dataset.tal;
            if (h.talents.includes(id)) h.talents = h.talents.filter((x) => x !== id);
            else if (h.talents.length < DV.SLOTS.talents) h.talents.push(id);
            else return toast('All three talent slots are full: take one off first.');
            redraw();
          };
        for (const b of $$('[data-item]', sh))
          b.onclick = () => {
            const [key, uid] = b.dataset.item.split(':');
            if (h[key].includes(uid)) h[key] = h[key].filter((x) => x !== uid);
            else {
              if (h[key].length >= DV.SLOTS[key]) return toast(`Both ${key === 'gear' ? 'gear' : 'skill'} slots are full: take one off first.`);
              const other = DV.holderOf(p, uid);
              if (other) other[key] = other[key].filter((x) => x !== uid);
              h[key].push(uid);
            }
            redraw();
          };
        const cls = $('#hClass', sh);
        if (cls) cls.onclick = () => classPicker(h, back);
      }
    );
  }

  function classPicker(h, back) {
    const p = UI.p;
    const slot = p.party.indexOf(h);
    refreshSheet(
      `${sheetHead('Change class', `${esc(h.name)} is replaced by a fresh hero of the class you pick, kitted from what is free.`)}
      <div class="delve-classes">${DV.CLASSES.map(
        (t) => `<button class="delve-card ${t === h.type ? 'on' : ''}" data-cls="${t}"><canvas data-p="${t}:P"></canvas><span class="nm"><b>${esc(UNITS[t].name)}</b> <span class="muted">${esc(UNITS[t].rarity)}</span></span><span class="small">${esc(UNITS[t].desc)}</span></button>`
      ).join('')}</div>`,
      (sh) => {
        UI.onSheetClose = back;
        for (const b of $$('[data-cls]', sh))
          b.onclick = () => {
            const nh = DV.setClass(p, slot, b.dataset.cls);
            heroSheet(nh, back);
          };
      }
    );
  }

  // ------------------------------------------------------------ the delve

  function ensureBoard() {
    if (UI.board) return UI.board;
    const b = new AG.Render.Board($('#board'));
    UI.board = b;
    const wrap = $('#boardWrap');
    const fit = () => {
      b.resize(wrap.clientWidth, wrap.clientHeight);
      if (UI.B) frameParty(true);
    };
    if (root.ResizeObserver) new ResizeObserver(fit).observe(wrap);
    root.addEventListener('resize', fit);
    fit();
    b.onTap = (hit) => tapBoard(hit);
    return b;
  }

  // Zoomed in close enough to read the units, on the party.
  function frameParty(now) {
    const B = UI.B;
    const b = UI.board;
    if (!B || !b) return;
    const want = Math.max(1, Math.min(b.maxZoom, 46 / b.baseTw));
    if (Math.abs(b.zoom - want) > 0.01) b.setZoom(want);
    const c = partyCenter(B.s);
    if (c) b.lookAt(c.x, c.y, now);
  }

  function partyCenter(s) {
    const us = s.units.filter((u) => u.alive && u.team === 'P' && !u.nonCombat);
    if (!us.length) return null;
    return { x: us.reduce((t, u) => t + u.x, 0) / us.length, y: us.reduce((t, u) => t + u.y, 0) / us.length };
  }

  function delve() {
    const p = UI.p;
    if (!p.run) return title();
    const { s, fl } = DV.floorBattle(p);
    const B = (UI.B = { s, fl, seen: new Uint8Array(fl.w * fl.h), known: new Set(), idle: 0, focus: null, paused: true, started: false, sel: null, log: [], loot: [], token: {} });
    $('#view').hidden = true;
    $('#battle').hidden = false;
    const b = ensureBoard();
    b.maxZoom = 4;
    b.clearUnits();
    b.setBoard(fl.w, fl.h, fl.terrain, 'dungeon');
    b.setObjectives([], null);
    DV.reveal(s, fl, B.seen);
    b.setSeen(B.seen);
    b.syncFromState(s);
    b.speed = UI.prefs.speed;
    b.start();
    frameParty(true);
    banner(`${DV.FLOOR_DEFS[p.run.floor].name}`);
    hud();
  }

  function banner(text, enemy) {
    const el = $('#banner');
    el.textContent = text;
    el.className = 'banner' + (enemy ? ' enemy' : '');
    void el.offsetWidth;
    el.classList.add('show');
  }

  function awakeFoes(s) {
    return s.units.filter((u) => u.alive && u.team === 'E' && !u.asleep && !u.nonCombat);
  }

  // The orders for a side: the monsters press on; the party follows your priority if you set
  // one, else walks on to the next pack (or breaks a stalled fight).
  function aiOpts(B, team) {
    if (team === 'E') return { stance: 'aggressive', temp: 0.4 };
    const mine = B.focus && AI.focusOf(B.s, 'P', B.focus) ? B.focus : null;
    if (B.focus && !mine) B.focus = null;
    return { stance: 'balanced', temp: 0.3, focus: mine || DV.exploreTarget(B.s, B.idle) };
  }

  async function runLoop() {
    const B = UI.B;
    if (!B || B.running) return;
    B.running = true;
    const s = B.s;
    const b = UI.board;
    try {
      while (UI.B === B && !s.over) {
        if (B.paused) {
          await sleep(120);
          continue;
        }
        const fighting = awakeFoes(s).length > 0;
        // Walking between fights goes twice as fast.
        b.speed = UI.prefs.speed * (fighting ? 1 : 2.5);
        const team = s.side;
        const opts = aiOpts(B, team);
        const plan = AI.chooseActivation(s, team, opts);
        AI.runPlan(s, plan, opts);
        const ev = E.drainEvents(s);
        B.idle = ev.some((e) => e.t === 'dmg') ? 0 : B.idle + 1;
        if (DV.reveal(s, B.fl, B.seen)) b.setSeen(B.seen);
        logEvents(B, ev);
        await b.playEvents(ev, s);
        if (UI.B !== B) return;
        b.syncFromState(s);
        for (const d of DV.packsDown(s, B.known)) {
          const got = DV.rollLoot(UI.p, AG.derive(UI.p.run.seed, 'loot:' + UI.p.run.floor + ':' + d.pack), UI.p.run.floor, d.boss);
          for (const it of got) {
            B.loot.push(it);
            const d2 = DV.itemDef(it);
            pushLog(B, `${ic('chest')} Loot: <b>${esc(d2.name)}</b> (${it.kind})`, 'O');
            toast(`Loot! ${d2.name}`);
            sfx('coin');
          }
        }
        const f = B.focus && AI.focusOf(s, 'P', B.focus);
        b.focus = f ? { x: f.x, y: f.y } : null;
        const c = partyCenter(s);
        if (c) b.lookAt(c.x, c.y);
        hud();
      }
      if (UI.B === B && s.over) floorOver(B);
    } finally {
      B.running = false;
    }
  }

  function pushLog(B, html, team) {
    B.log.unshift({ html, team: team || 'O' });
    B.log.length = Math.min(B.log.length, 30);
  }

  function nameOf(u) {
    return u.team === 'P' ? `${esc(u.name || UNITS[u.type].name)}` : `${esc(UNITS[u.type].name)}`;
  }

  function logEvents(B, ev) {
    const s = B.s;
    for (const e of ev) {
      if (e.t === 'wake') {
        const us = e.uids.map((id) => s.byId[id]).filter(Boolean);
        const boss = us.find((u) => u.boss);
        pushLog(B, boss ? `<b>${esc(UNITS[boss.type].name)}</b> rises to meet you!` : `A pack wakes: ${us.map((u) => esc(UNITS[u.type].name)).join(', ')}`, 'E');
        banner(boss ? UNITS[boss.type].name : 'Ambush!', true);
        sfx('horn');
      } else if (e.t === 'death') {
        const u = s.byId[e.uid];
        if (!u || u.nonCombat) continue;
        pushLog(B, `${nameOf(u)} ${u.team === 'P' ? 'falls!' : 'is slain.'}`, u.team === 'P' ? 'E' : 'P');
      } else if (e.t === 'status' && e.status === 'held') {
        const u = s.byId[e.uid];
        if (u) pushLog(B, `${nameOf(u)} is caught in a Shackler's net.`, 'E');
      }
    }
  }

  // ---- the heads-up display: floor and controls on top, the party and info below.

  function hud() {
    const B = UI.B;
    if (!B) return;
    const s = B.s;
    const p = UI.p;
    const fighting = awakeFoes(s).length > 0;
    const left = s.units.filter((u) => u.alive && u.team === 'E' && !u.nonCombat).length;
    const state = !B.started ? 'Ready' : B.paused ? 'Paused' : fighting ? 'Fighting' : 'Exploring';
    $('#topbar').innerHTML = `<div class="title"><b>${esc(DV.FLOOR_DEFS[p.run.floor].name)}</b>
      <span>${state} · ${left} monster${left === 1 ? '' : 's'} left on this floor</span></div>
      ${B.started ? `<button class="btn icon-only speedbtn ${UI.prefs.speed > 1 ? 'on' : ''}" id="dFast" aria-label="Speed ${UI.prefs.speed}x">${ic('fast')}<small>${UI.prefs.speed}×</small></button>
      <button class="btn icon-only ${B.paused ? 'on' : ''}" id="dPause" aria-label="${B.paused ? 'Resume' : 'Pause'}">${ic(B.paused ? 'play' : 'pause')}</button>` : ''}
      <button class="btn icon-only" id="dMenu" aria-label="Menu">${ic('menu')}</button>`;
    const sel = B.sel && s.byId[B.sel];
    const party = s.units.filter((u) => u.team === 'P' && !u.nonCombat && u.rid);
    $('#cmd').innerHTML = `
      ${!B.started ? `<div class="hint">${ic('swords')} Your party stands at the way in. Monster packs sleep in the rooms ahead until your heroes come near. <b>Begin</b> and they explore and fight on their own; pause or set a priority any time.</div>
        <div class="actions sticky"><button class="btn primary" id="dBegin">${ic('play')} Begin</button></div>` : ''}
      ${B.focus ? focusLine(B) : ''}
      ${sel ? selPanel(B, sel) : ''}
      <div class="delve-frames">${party.map((u) => frame(u)).join('')}</div>
      ${B.log.length ? `<ul class="blog">${B.log.slice(0, 5).map((l) => `<li class="team-${l.team}">${l.html}</li>`).join('')}</ul>` : ''}`;
    drawPortraits($('#cmd'));
    const on = (id, f) => $('#' + id) && ($('#' + id).onclick = f);
    on('dBegin', () => {
      B.started = true;
      B.paused = false;
      startSound();
      hud();
      runLoop();
    });
    on('dPause', () => {
      B.paused = !B.paused;
      hud();
      if (!B.paused) runLoop();
    });
    on('dFast', () => {
      UI.prefs.speed = UI.prefs.speed >= 4 ? 1 : UI.prefs.speed * 2;
      savePrefs();
      hud();
    });
    on('dMenu', () => menu());
    on('dFocus', () => setFocus(B));
    on('dUnfocus', () => {
      B.focus = null;
      UI.board.focus = null;
      hud();
    });
    on('dDesel', () => {
      B.sel = null;
      B.tile = null;
      hud();
    });
    on('dInfo', () => unitInfo(s.byId[B.sel]));
    for (const f of $$('#cmd [data-uid]'))
      f.onclick = () => {
        B.sel = +f.dataset.uid;
        B.tile = null;
        hud();
      };
  }

  function frame(u) {
    const f = Math.max(0, u.hp / u.maxHp);
    const st = [];
    if (!u.alive) st.push('<span class="chip bad">Fallen</span>');
    else {
      if (u.heldBy) st.push('<span class="chip warn">Netted</span>');
      else if (u.para > 0) st.push('<span class="chip warn">Paralyzed</span>');
      if (u.poison) st.push('<span class="chip poison">Poison</span>');
      if (u.burn) st.push('<span class="chip warn">Burning</span>');
    }
    return `<button class="delve-frame ${u.alive ? '' : 'down'} ${UI.B.sel === u.uid ? 'sel' : ''}" data-uid="${u.uid}">
      <canvas data-p="${u.type}:P"></canvas>
      <span class="fr-body"><b>${esc(u.name || UNITS[u.type].name)}</b>
        <span class="hpbar ${f < 0.3 ? 'low' : f < 0.6 ? 'mid' : ''}"><i style="width:${Math.round(f * 100)}%"></i></span>
        <span class="small">${u.alive ? `${u.hp}/${u.maxHp}` : ''} ${st.join(' ')}</span></span>
    </button>`;
  }

  function focusLine(B) {
    const f = AI.focusOf(B.s, 'P', B.focus);
    if (!f) return '';
    const label = f.unit ? UNITS[f.unit.type].name : f.ally ? `rally on ${f.ally.name || UNITS[f.ally.type].name}` : 'that spot';
    return `<div class="focusline">${ic('target')}<span>Priority: <b>${esc(label)}</b></span><button class="btn" id="dUnfocus">Clear</button></div>`;
  }

  function selPanel(B, u) {
    if (!u) return '';
    const f = Math.max(0, u.hp / u.maxHp);
    const verb = u.team === 'P' ? 'Rally on' : 'Priority';
    return `<div class="delve-sel"><canvas data-p="${u.type}:${u.team}"></canvas>
      <div class="grow"><b>${nameOf(u)}</b> <span class="muted">${esc(UNITS[u.type].name)} · Lv ${u.level}${u.asleep ? ' · asleep' : ''}</span>
        <span class="hpbar ${f < 0.3 ? 'low' : f < 0.6 ? 'mid' : ''}"><i style="width:${Math.round(f * 100)}%"></i></span>
        <span class="small">${u.hp}/${u.maxHp} HP</span></div>
      <div class="col"><button class="btn" id="dInfo">${ic('eye')}</button>${u.alive ? `<button class="btn primary" id="dFocus">${ic('target')} ${verb}</button>` : ''}<button class="btn ghost" id="dDesel">${ic('close')}</button></div></div>`;
  }

  function unitInfo(u) {
    if (!u) return;
    const T = UNITS[u.type];
    const acts = u.acts.filter((a) => a.kind !== 'none').map((a) => `<li><b>${esc(a.name)}</b>${a.uses ? ` (${a.left === Infinity ? '' : a.left + ' left'})` : ''}</li>`).join('');
    openSheet(`${sheetHead(`${nameOf(u)}`, `${esc(T.name)} · Level ${u.level} · ${u.hp}/${u.maxHp} HP · ${Math.round(u.armor * 100)}% physical / ${Math.round(u.res * 100)}% magic resistance`)}
      <p>${esc(T.desc)}</p>${T.tip && u.team === 'E' ? `<p class="hint">${esc(T.tip)}</p>` : ''}
      <div class="eyebrow">Actions</div><ul class="tips">${acts}</ul>
      <div class="actions"><button class="btn primary" data-close>${ic('check')} Back</button></div>`);
  }

  function tapBoard(hit) {
    const B = UI.B;
    if (!B) return;
    const s = B.s;
    const uid = hit.unitTile && hit.unitTile.uid;
    const u = uid && s.byId[uid];
    if (u && u.alive && (u.team === 'P' || !B.seen || B.seen[u.y * s.w + u.x])) {
      B.sel = u.uid;
      B.tile = null;
      sfx('click');
      hud();
      return;
    }
    if (hit.tile && B.seen[hit.tile.y * s.w + hit.tile.x] && s.terrain[hit.tile.y * s.w + hit.tile.x] !== 1) {
      B.sel = null;
      B.focus = { tile: true, x: hit.tile.x, y: hit.tile.y };
      UI.board.focus = { x: hit.tile.x, y: hit.tile.y };
      toast('The party heads there. Clear the priority to let them roam again.');
      hud();
      return;
    }
    B.sel = null;
    hud();
  }

  function setFocus(B) {
    const u = B.s.byId[B.sel];
    if (!u || !u.alive) return;
    B.focus = u.team === 'P' ? { ally: u.uid } : { uid: u.uid };
    const f = AI.focusOf(B.s, 'P', B.focus);
    UI.board.focus = f ? { x: f.x, y: f.y } : null;
    B.sel = null;
    sfx('select');
    hud();
  }

  function menu() {
    const B = UI.B;
    const was = B.paused;
    B.paused = true;
    hud();
    openSheet(`${sheetHead('Paused')}
      <div class="actions col">
        <button class="btn primary" data-close>${ic('play')} Back to the delve</button>
        <button class="btn" id="mHelp">${ic('help')} How it works</button>
        <button class="btn" id="mTown">${ic('undo')} Town portal (start this floor over later)</button>
      </div>`, (sh) => {
      UI.onSheetClose = () => {
        if (UI.B === B && B.started) {
          B.paused = was;
          hud();
          if (!B.paused) runLoop();
        }
      };
      $('#mHelp', sh).onclick = help;
      $('#mTown', sh).onclick = () => {
        UI.onSheetClose = null;
        closeSheet();
        UI.B = null;
        title();
      };
    });
  }

  function floorOver(B) {
    const p = UI.p;
    const s = B.s;
    const floor = p.run.floor;
    const loot = B.loot.map((it) => `<li>${ic('chest')} <b>${esc(DV.itemDef(it).name)}</b> <span class="muted">(${it.kind})</span></li>`).join('');
    if (s.winner !== 'P') {
      DV.endRun(p);
      openSheet(`${sheetHead('Your party has fallen', `${esc(DV.FLOOR_DEFS[floor].name)} of the Forgotten Tower`)}
        <p>The tower keeps its secrets for now. Everything you found stays in your stash.</p>
        ${loot ? `<div class="eyebrow">Found on this floor</div><ul class="tips">${loot}</ul>` : ''}
        <div class="actions"><button class="btn primary" data-close>${ic('undo')} Back to town</button></div>`, () => {
        UI.onSheetClose = () => title();
      });
      return;
    }
    const res = DV.finishFloor(p, s);
    const fallen = s.units.filter((u) => u.team === 'P' && u.rid && !u.alive);
    if (res.done) {
      openSheet(`${sheetHead('The Countess is slain!', 'The Forgotten Tower is beaten.')}
        <p>Her tower falls quiet. Your party walks out into the light with everything it found.</p>
        ${loot ? `<div class="eyebrow">Found on this floor</div><ul class="tips">${loot}</ul>` : ''}
        <div class="actions"><button class="btn primary" data-close>${ic('crown')} Back to town</button></div>`, () => {
        UI.onSheetClose = () => title();
      });
      return;
    }
    openSheet(`${sheetHead(`${esc(DV.FLOOR_DEFS[floor].name)} cleared`, `Stairs down to ${esc(DV.FLOOR_DEFS[res.floor].name)}`)}
      ${fallen.length ? `<p>${fallen.map((u) => esc(u.name)).join(', ')} ${fallen.length > 1 ? 'get' : 'gets'} back up at the shrine by the stairs, with ${Math.round(DV.SHRINE_HP * 100)}% HP.</p>` : '<p>Everyone made it. Hurt heroes stay hurt: the Cleric patches them up as you walk.</p>'}
      ${loot ? `<div class="eyebrow">Found on this floor</div><ul class="tips">${loot}</ul>` : '<p class="muted">Nothing dropped this time.</p>'}
      <div class="actions col">
        <button class="btn primary" id="fDown">${ic('play')} Take the stairs down</button>
        <button class="btn" id="fTown">${ic('undo')} Town portal: swap kit, then come back</button>
      </div>`, (sh) => {
      // Closed any other way, it is the town portal: the delve waits on the next floor.
      UI.onSheetClose = () => title();
      $('#fDown', sh).onclick = () => {
        UI.onSheetClose = null;
        closeSheet();
        delve();
      };
      $('#fTown', sh).onclick = () => closeSheet();
    });
  }

  function init() {
    UI.p = DV.load() || DV.newProfile();
    DV.save(UI.p);
    $('#modal').addEventListener('click', (e) => {
      if (e.target.id === 'modal') closeSheet();
    });
  }

  Object.assign(UI, { init, title, partyScreen, heroSheet, delve, hud, help });
})(window);
