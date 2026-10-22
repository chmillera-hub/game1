// Screens and touch controls: title, campaign setup, map, war room, battle, rewards,
// shop, rest, events, army management, help and codex.
(function (root) {
  'use strict';
  const AG = root.AG;
  const { UNITS, TALENTS, RELICS, WARBANDS, DIFFICULTIES, ACTS, MAX_TALENTS } = AG.Data;
  const R = AG.Run;
  const E = AG.Engine;
  const AI = AG.AI;

  const $ = (sel, el) => (el || document).querySelector(sel);
  const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));
  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const ic = (name) => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  const pct = (v) => Math.round(v * 100) + '%';
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const stars = (n) => (n > 1 ? '★'.repeat(n) : '');
  const PREFS_KEY = 'arena-gauntlet-prefs';

  const UI = {
    run: null,
    board: null,
    battle: null,
    wr: null,
    mapSel: null,
    prefs: { fast: false, threat: false },
  };
  try {
    Object.assign(UI.prefs, JSON.parse(root.localStorage.getItem(PREFS_KEY) || '{}'));
  } catch (e) {
    /* storage unavailable */
  }
  function savePrefs() {
    try {
      root.localStorage.setItem(PREFS_KEY, JSON.stringify(UI.prefs));
    } catch (e) {
      /* storage unavailable */
    }
  }

  const sfx = (n) => AG.Audio && AG.Audio.play(n);

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
      const [type, team, gray] = cv.dataset.p.split(':');
      AG.Render.portrait(cv, type, team || 'P', { gray: gray === 'g' });
    }
  }

  function openSheet(html, bind) {
    const m = $('#modal');
    const sh = $('#sheet');
    sh.innerHTML = html;
    m.hidden = false;
    sh.scrollTop = 0;
    drawPortraits(sh);
    for (const b of $$('[data-close]', sh)) b.addEventListener('click', closeSheet);
    if (bind) bind(sh);
  }

  function closeSheet() {
    $('#modal').hidden = true;
    $('#sheet').innerHTML = '';
    if (UI.onSheetClose) {
      const f = UI.onSheetClose;
      UI.onSheetClose = null;
      f();
    }
  }

  function sheetHead(title, sub) {
    return `<div class="sheet-head"><div class="grow"><h3>${title}</h3>${sub ? `<div class="small muted">${sub}</div>` : ''}</div>
      <button class="btn icon-only ghost" data-close aria-label="Close">${ic('close')}</button></div>`;
  }

  function confirmSheet(title, text, okLabel, cancelLabel, danger) {
    return new Promise((resolve) => {
      let done = false;
      const finish = (v) => {
        if (done) return;
        done = true;
        UI.onSheetClose = null;
        closeSheet();
        resolve(v);
      };
      openSheet(
        `${sheetHead(esc(title))}<p class="muted">${text}</p>
        <div class="actions"><button class="btn" id="cfNo">${esc(cancelLabel || 'Cancel')}</button>
        <button class="btn ${danger ? 'danger' : 'primary'}" id="cfYes">${esc(okLabel || 'Confirm')}</button></div>`,
        (sh) => {
          $('#cfYes', sh).onclick = () => finish(true);
          $('#cfNo', sh).onclick = () => finish(false);
        }
      );
      UI.onSheetClose = () => {
        if (!done) {
          done = true;
          resolve(false);
        }
      };
    });
  }

  // Ask the player to pick one of their units. Resolves to a roster id or null.
  function pickUnit(title, note, filter) {
    return new Promise((resolve) => {
      let done = false;
      const run = UI.run;
      const rows = run.roster
        .map((u) => {
          const ok = filter(u);
          return `<button class="army-row" data-rid="${u.id}" ${ok ? '' : 'disabled style="opacity:.45"'}>
          <canvas class="portrait" data-p="${u.type}:P"></canvas>
          <div class="nm"><b>${esc(u.name)}</b> <span class="stars">${stars(u.rank)}</span>
            <div class="small muted">${UNITS[u.type].name}${u.talents.length ? ' · ' + u.talents.map((t) => TALENTS[t].name).join(', ') : ''}</div></div>
          <div>${ok ? ic('check') : ''}</div></button>`;
        })
        .join('');
      openSheet(`${sheetHead(esc(title), note)}<div class="army-list">${rows}</div>`, (sh) => {
        for (const b of $$('.army-row', sh))
          b.addEventListener('click', () => {
            if (b.disabled) return;
            done = true;
            UI.onSheetClose = null;
            closeSheet();
            resolve(b.dataset.rid);
          });
      });
      UI.onSheetClose = () => {
        if (!done) resolve(null);
      };
    });
  }

  function computed(r) {
    return R.unitStats(r, UI.run ? UI.run.relics : [], 'P');
  }

  function rangeLabel(u) {
    const a = u.act;
    switch (a.kind) {
      case 'strike':
      case 'cleave':
      case 'quake':
      case 'blast':
      case 'grow':
        return a.range[0] === a.range[1] ? String(a.range[0]) : a.range[0] + '-' + a.range[1];
      case 'line':
        return 'Line ' + a.len;
      case 'cone':
        return 'Cone ' + a.len;
      case 'cross':
        return 'Cross ' + a.len;
      case 'nova':
      case 'pray':
        return 'Aura ' + a.radius;
      default:
        return '-';
    }
  }

  function statsHTML(u) {
    const heal = u.act.kind === 'pray';
    const powLabel = heal ? 'Heal' : u.act.fx && u.act.fx.poison ? 'Poison' : 'Power';
    const powVal = heal ? E.healAmount(u) : u.act.fx && u.act.fx.poison ? E.poisonDamage(u) : u.pow || '-';
    return `<div class="stats">
      <div class="stat"><b>${powVal}</b><span>${powLabel}</span></div>
      <div class="stat"><b>${pct(u.armor)}</b><span>Armor</span></div>
      <div class="stat"><b>${u.facing < 0 ? '-' : pct(u.block)}</b><span>Block</span></div>
      <div class="stat"><b>${u.rec}</b><span>Recover</span></div>
      <div class="stat"><b>${u.move}</b><span>Move</span></div>
      <div class="stat"><b>${rangeLabel(u)}</b><span>Range</span></div>
    </div>`;
  }

  function rangeText(r) {
    if (r[0] === 1 && r[1] === 1) return 'next to it';
    if (r[0] === 1) return 'up to ' + r[1] + ' tiles away';
    return r[0] + '-' + r[1] + ' tiles away';
  }

  function abilityText(u) {
    const a = u.act;
    const p = u.pow;
    const ff = a.ff ? ' Hits allies too.' : '';
    switch (a.kind) {
      case 'strike':
        return `${p} ${a.dmg === 'magic' ? 'magic' : 'physical'} damage to one enemy ${rangeText(a.range)}.`;
      case 'cleave':
        return `${p} physical damage to every adjacent enemy.`;
      case 'quake':
        return `${p} physical damage to an adjacent enemy and every enemy beside it.`;
      case 'blast':
        return `${a.dmg ? p + ' magic damage to' : 'Strikes'} a ${a.pattern === 'square' ? '3x3' : '5-tile'} burst ${rangeText(a.range)}.${
          a.fx && a.fx.para ? ` Paralyzes enemies for ${a.fx.para} turn${a.fx.para > 1 ? 's' : ''}.` : ''
        }${ff}`;
      case 'line':
        return `${p} magic damage to every unit in a straight line up to ${a.len} tiles.${a.ff ? ' Hits allies too.' : ' Passes through allies.'}`;
      case 'cone':
        return `${p} magic damage across a cone ${a.len} tiles deep.${ff}`;
      case 'cross':
        return `${p} magic damage to enemies in all four directions, up to ${a.len} tiles.`;
      case 'nova':
        return a.dmg
          ? `${p} magic damage to every enemy within ${a.radius} tiles.`
          : `Poisons every enemy within ${a.radius} tiles for ${a.fx.poison} turns: ${E.poisonDamage(u)} damage a turn, and no healing.`;
      case 'pray':
        return `Heals ${E.healAmount(u)} HP to every ally within ${a.radius} tiles.${a.cleanse ? ' Also cures poison and paralysis.' : ''}`;
      case 'grow':
        return `Raises a shrub on an empty tile up to ${a.range[1]} tiles away. Up to 3 at once.`;
      default:
        return UNITS[u.type].desc;
    }
  }

  const TRAIT_TEXT = {
    backstab: 'Backstab: +50% damage from behind.',
    deathmark: 'Deathmark: double damage from behind.',
    shadowstep: 'Shadowstep: moves through enemy units.',
    stoneskin: 'Stoneskin: immune to poison and paralysis.',
    guardian: 'Guardian: adjacent allies take 20% less damage.',
    bulwark: 'Bulwark: Guardian protection is 35%.',
    charge: 'Charge: +30% damage after moving 3+ tiles first.',
    trample: 'Trample: Charge bonus is +60%.',
    rage: 'Rage: +30% damage below half HP.',
    bloodrage: 'Bloodrage: Cleave heals 5 per enemy struck.',
    flying: 'Flying: passes over units, water, lava and rocks.',
    immobile: 'Rooted: cannot move.',
    regrowth: 'Regrowth: heals 4 HP each turn.',
    aura_barrier: 'Barrier Aura: allies within 2 tiles take half magic damage and are immune to poison and paralysis.',
    aegisfield: 'Aegis Field: aura reaches 3 tiles and softens physical blows by 15%.',
    shieldwall: 'Shield Wall: full block from the sides.',
    pierce: 'Bodkin Arrows: ignores half of armor.',
    ambush: 'Ambusher: +50% damage from behind.',
    thornwall: 'Thornwall: shrubs are tougher and prick melee attackers.',
    spellward: 'Spellward: takes half magic damage.',
  };

  function traitLines(u) {
    const out = [];
    for (const t of u.traits) if (TRAIT_TEXT[t]) out.push(TRAIT_TEXT[t]);
    if (u.boss) out.push('Boss: immune to paralysis.');
    return out;
  }

  function hpClass(f) {
    return f > 0.5 ? '' : f > 0.25 ? 'mid' : 'low';
  }

  function unitInfoHTML(u, opts) {
    const o = opts || {};
    const T = UNITS[u.type];
    const f = u.hp / u.maxHp;
    const chips = [];
    if (o.status) {
      const B = UI.battle;
      const acting = B && B.s.act && B.s.act.uid === u.uid;
      if (u.para > 0) chips.push(`<span class="chip warn">Paralyzed ${u.para}</span>`);
      if (u.poison) chips.push(`<span class="chip good">Poisoned ${u.poison.turns}</span>`);
      if (acting) chips.push('<span class="chip warn">Acting</span>');
      else if (u.activated) chips.push('<span class="chip">Done this turn</span>');
      else if (u.wait > 0) chips.push(`<span class="chip">${ic('hourglass')} Recovering ${u.wait}</span>`);
      else if (!u.nonCombat && u.act.kind !== 'none' && u.para === 0) chips.push('<span class="chip good">Ready</span>');
    }
    if (o.wounded) chips.push('<span class="chip bad">Wounded</span>');
    for (const t of u.tal) chips.push(`<span class="chip magic">${esc(TALENTS[t].name)}</span>`);
    return `<div class="unitcard">
      <canvas class="portrait" data-p="${u.type}:${u.team}"></canvas>
      <div class="name"><b class="team-${u.team}">${esc(o.name || u.name)}</b><span class="stars">${stars(u.rank)}</span>
        <span class="small muted">${T.name !== (o.name || u.name) ? esc(T.name) : ''}</span></div>
      <div class="hp"><div class="hpbar ${hpClass(f)}"><i style="width:${Math.round(f * 100)}%"></i></div><span>${u.hp}/${u.maxHp}</span></div>
    </div>
    ${chips.length ? `<div class="chips">${chips.join('')}</div>` : ''}`;
  }

  function resbar(run) {
    return `<div class="resbar">
      <span class="res gold" title="Gold">${ic('gold')}<span class="num">${run.gold}</span></span>
      <span class="res lives" title="Banners left">${ic('banner')}<span class="num">${run.banners}/${run.maxBanners}</span></span>
      <span class="res" title="Army size">${ic('army')}<span class="num">${run.roster.length}/${R.MAX_ROSTER}</span></span>
    </div>`;
  }

  function relicChips(run) {
    return run.relics.map((id) => `<button class="relic" data-relic="${id}">${ic('gem')}${esc(RELICS[id].name)}</button>`).join('');
  }

  function bindRelics(el) {
    for (const b of $$('[data-relic]', el))
      b.addEventListener('click', () => {
        const r = RELICS[b.dataset.relic];
        toast(r.name + ': ' + r.desc, 3600);
      });
  }

  // ------------------------------------------------------------ views

  function showView(html, cls) {
    stopDiorama();
    $('#battle').hidden = true;
    if (UI.board) UI.board.stop();
    const v = $('#view');
    v.hidden = false;
    v.className = 'screen ' + (cls || '');
    v.innerHTML = html;
    v.scrollTop = 0;
    drawPortraits(v);
    bindRelics(v);
    return v;
  }

  function ensureBoard() {
    if (UI.board) return UI.board;
    const b = new AG.Render.Board($('#board'));
    UI.board = b;
    const wrap = $('#boardWrap');
    const fit = () => b.resize(wrap.clientWidth, wrap.clientHeight);
    if (root.ResizeObserver) new ResizeObserver(fit).observe(wrap);
    root.addEventListener('resize', fit);
    fit();
    b.onTap = (h) => UI.boardTap && UI.boardTap(h);
    b.onLongPress = (h) => UI.boardLong && UI.boardLong(h);
    return b;
  }

  function showBattleLayout() {
    stopDiorama();
    $('#view').hidden = true;
    $('#battle').hidden = false;
    const b = ensureBoard();
    const wrap = $('#boardWrap');
    b.resize(wrap.clientWidth, wrap.clientHeight);
    b.start();
    updateRotateHint();
    return b;
  }

  function updateRotateHint() {
    const h = $('#rotateHint');
    if (!h) return;
    const portrait = root.innerHeight > root.innerWidth * 1.1 && root.innerWidth < 700;
    h.hidden = !portrait || UI.prefs.hideRotate;
  }

  function boardTools(extra) {
    const t = $('#boardTools');
    t.innerHTML = `${extra || ''}
      <button class="btn icon-only" id="zIn" aria-label="Zoom in">${ic('plus')}</button>
      <button class="btn icon-only" id="zOut" aria-label="Zoom out">${ic('minus')}</button>`;
    $('#zIn').onclick = () => UI.board.setZoom(UI.board.zoom * 1.35);
    $('#zOut').onclick = () => UI.board.setZoom(UI.board.zoom / 1.35);
  }

  function showBanner(text, enemy) {
    const b = $('#banner');
    b.textContent = text;
    b.className = 'banner' + (enemy ? ' enemy' : '');
    void b.offsetWidth;
    b.classList.add('show');
  }

  // ------------------------------------------------------------ title

  let diorama = null;
  function stopDiorama() {
    if (!diorama) return;
    diorama.board.stop();
    clearInterval(diorama.timer);
    root.removeEventListener('resize', diorama.fit);
    diorama = null;
  }

  function startDiorama(cv) {
    stopDiorama();
    const b = new AG.Render.Board(cv);
    const terrain = new Array(25).fill(0);
    terrain[2 * 5 + 0] = 1;
    terrain[2 * 5 + 4] = 2;
    b.setBoard(5, 5, terrain, 'grass');
    const list = [
      { uid: 1, type: 'knight', team: 'P', x: 2, y: 3, facing: 0, hp: 52, maxHp: 52 },
      { uid: 2, type: 'archer', team: 'P', x: 3, y: 4, facing: 0, hp: 34, maxHp: 34 },
      { uid: 3, type: 'pyromancer', team: 'P', x: 1, y: 4, facing: 0, hp: 28, maxHp: 28 },
      { uid: 4, type: 'knight', team: 'E', x: 2, y: 2, facing: 2, hp: 52, maxHp: 52 },
      { uid: 5, type: 'golem', team: 'E', x: 3, y: 1, facing: 2, hp: 74, maxHp: 74 },
      { uid: 6, type: 'witch', team: 'E', x: 1, y: 0, facing: 2, hp: 28, maxHp: 28 },
    ];
    for (const u of list) b.vis.set(u.uid, b.makeVis(u));
    b.interactive = false;
    const fit = () => b.resize(cv.clientWidth, cv.clientHeight);
    fit();
    b.start();
    let step = 0;
    const beat = () => {
      const k = step++ % 3;
      if (k === 0) {
        b.projectile([3, 4], [3, 1], 'arrow', 320).then(() => b.addText(3, 1, '10', '#fff', { height: 44 }));
      } else if (k === 1) {
        const v = b.vis.get(1);
        b.tween(120, (t) => (v.oy = -t * b.th * 0.35)).then(() => {
          b.addText(2, 2, 'BLOCK', '#a9d1ff', { height: 43 });
          b.tween(140, (t) => (v.oy = -(1 - t) * b.th * 0.35));
        });
      } else {
        b.projectile([1, 4], [2, 1], 'fire', 420).then(() => {
          b.flashTiles(
            [[2, 1], [1, 1], [3, 1], [2, 0], [2, 2]],
            'rgba(255,140,40,ALPHA)',
            420
          );
          b.addText(3, 1, '16', '#d7b4ff', { height: 44 });
        });
      }
    };
    diorama = { board: b, timer: setInterval(beat, 2200), fit };
    root.addEventListener('resize', fit);
  }

  function title() {
    UI.battle = null;
    if (!UI.run) UI.run = R.load();
    const meta = R.loadMeta();
    const run = UI.run;
    const v = showView(
      `<div class="wrap">
        <div class="title-grid">
          <div class="wrap" style="margin:0;gap:14px">
            <p class="eyebrow">A tactics roguelike</p>
            <h1 class="wordmark">Arena<br>Gauntlet</h1>
            <p class="tagline">Scout the enemy army, field the counter, and fight your way through three acts of isometric arena battles.</p>
            <div class="title-actions">
              ${run ? `<button class="btn primary" id="tCont">${ic('flag')} Continue · ${ACTS[run.act].short}</button>` : ''}
              <button class="btn ${run ? '' : 'primary'}" id="tNew">${ic('swords')} New campaign</button>
              <div class="row"><button class="btn grow" id="tHelp">${ic('help')} How to play</button>
              <button class="btn grow" id="tCodex">${ic('book')} Units</button></div>
            </div>
            <p class="meta-line">${meta.runs ? `Campaigns fought: ${meta.runs} · Victories: ${meta.wins}` : 'Inspired by the classic isometric arena tactics games.'}</p>
          </div>
          <canvas class="diorama" id="diorama" aria-hidden="true"></canvas>
        </div>
      </div>`,
      'title-screen'
    );
    if ($('#tCont', v)) $('#tCont', v).onclick = () => route();
    $('#tNew', v).onclick = async () => {
      if (UI.run && !(await confirmSheet('Abandon campaign?', 'Starting over ends your current campaign for good.', 'Start over', 'Keep it', true))) return;
      newCampaign();
    };
    $('#tHelp', v).onclick = () => helpSheet();
    $('#tCodex', v).onclick = () => codexSheet();
    requestAnimationFrame(() => startDiorama($('#diorama')));
  }

  // ------------------------------------------------------------ new campaign

  function newCampaign() {
    let wb = WARBANDS[0].id;
    let diff = 'knight';
    const render = () => {
      const v = showView(
        `<div class="wrap">
          <div class="row"><button class="btn ghost" id="ncBack">Back</button></div>
          <div><p class="eyebrow">New campaign</p><h2>Choose your warband</h2></div>
          <div class="choice-grid">${WARBANDS.map(
            (w) => `<button class="card ${w.id === wb ? 'selected' : ''}" data-wb="${w.id}">
              <div class="unit-strip">${w.units.map((t) => `<canvas data-p="${t}:P"></canvas>`).join('')}</div>
              <div class="title">${esc(w.name)}</div>
              <div class="desc">${esc(w.desc)}</div>
              <div class="small">${w.units.map((t) => UNITS[t].name).join(', ')}</div>
              <div class="chips"><span class="chip magic">${ic('gem')} ${esc(RELICS[w.relic].name)}</span><span class="chip warn">${ic('gold')} ${w.gold}</span></div>
            </button>`
          ).join('')}</div>
          <h3>Difficulty</h3>
          <div class="seg">${DIFFICULTIES.map(
            (d) => `<button class="card ${d.id === diff ? 'selected' : ''}" data-diff="${d.id}"><div class="title" style="font-size:1.15rem">${d.name}</div><div class="desc small">${esc(d.desc)}</div></button>`
          ).join('')}</div>
          <button class="btn primary wide" id="ncGo">${ic('swords')} March to the arena</button>
        </div>`
      );
      $('#ncBack', v).onclick = () => title();
      for (const b of $$('[data-wb]', v))
        b.onclick = () => {
          wb = b.dataset.wb;
          sfx('click');
          render();
        };
      for (const b of $$('[data-diff]', v))
        b.onclick = () => {
          diff = b.dataset.diff;
          sfx('click');
          render();
        };
      $('#ncGo', v).onclick = () => {
        R.clearSave();
        UI.run = R.newRun({ warband: wb, difficulty: diff });
        R.save(UI.run);
        sfx('turn');
        mapScreen();
        if (!UI.prefs.seenHelp) {
          UI.prefs.seenHelp = true;
          savePrefs();
          helpSheet();
        }
      };
    };
    render();
  }

  // ------------------------------------------------------------ map

  const NODE_INFO = {
    battle: { icon: 'swords', name: 'Battle', desc: 'A standard enemy warband.' },
    elite: { icon: 'skull', name: 'Elite', desc: 'A tougher warband. Victory earns a relic.' },
    event: { icon: 'event', name: 'Unknown', desc: 'Something waits on the road.' },
    shop: { icon: 'bag', name: 'Merchant', desc: 'Spend gold on recruits, talents and relics.' },
    rest: { icon: 'fire', name: 'Campfire', desc: 'Rest to heal wounds and raise a Banner, or train a unit.' },
    treasure: { icon: 'chest', name: 'Treasure', desc: 'A relic and some gold for the taking.' },
    boss: { icon: 'crown', name: 'Boss', desc: '' },
  };

  function isWide() {
    return root.innerWidth > root.innerHeight * 1.15;
  }

  function mapSVG(run, avail) {
    const rows = R.ROWS;
    const horiz = isWide();
    let W;
    let H;
    let pos;
    if (horiz) {
      const colW = 104;
      const rowH = 62;
      const left = 54;
      const top = 40;
      W = left * 2 + rows * colW + 40;
      H = top * 2 + (R.COLS - 1) * rowH + 18;
      pos = (n) => (n.id === 'boss' ? [left + rows * colW + 20, H / 2 - 9] : [left + n.row * colW + n.jx * 18, top + n.col * rowH]);
    } else {
      const rowH = 86;
      const top = 56;
      W = 500;
      H = top * 2 + rows * rowH;
      pos = (n) => (n.id === 'boss' ? [W / 2, top] : [70 + n.col * 90 + n.jx * 24, top + (rows - n.row) * rowH]);
    }
    const visited = new Set(run.visited.filter((v) => v.startsWith(run.act + ':')).map((v) => v.slice(2)));
    let lines = '';
    let nodes = '';
    for (const n of run.map.nodes) {
      const [x, y] = pos(n);
      for (const id of n.next) {
        const m = run.map.nodes.find((k) => k.id === id);
        const [x2, y2] = pos(m);
        const walked = visited.has(n.id) && (visited.has(id) || run.cur === id);
        lines += `<line x1="${x}" y1="${y}" x2="${x2}" y2="${y2}" stroke="${walked ? '#5a3c1e' : '#8b6d45'}" stroke-width="${walked ? 3.5 : 2}" stroke-dasharray="${walked ? '' : '5 6'}" stroke-linecap="round" opacity="${walked ? 0.95 : 0.6}"/>`;
      }
    }
    for (const n of run.map.nodes) {
      const [x, y] = pos(n);
      const info = NODE_INFO[n.kind];
      const isAvail = avail.includes(n.id);
      const isVisited = visited.has(n.id);
      const isPos = run.pos === n.id;
      const sel = UI.mapSel === n.id;
      const r = n.id === 'boss' ? 30 : 21;
      const fill = isVisited ? '#6b4f2e' : n.kind === 'elite' ? '#f3d6c8' : n.id === 'boss' ? '#f1d9a4' : '#f6ecd4';
      const stroke = isAvail ? '#a3331f' : isVisited ? '#3e2a14' : '#7b5d36';
      const col = isVisited ? '#f3e6c8' : n.kind === 'elite' || n.id === 'boss' ? '#8a1f15' : '#4a3520';
      const dim = !isAvail && !isVisited && !isPos ? 0.72 : 1;
      nodes += `<g class="node" data-node="${n.id}" transform="translate(${x},${y})" opacity="${dim}" ${isAvail ? 'tabindex="0" role="button"' : ''} aria-label="${info.name}">
        ${isAvail ? `<circle r="${r + 7}" fill="none" stroke="#a3331f" stroke-width="2" opacity="0.7"><animate attributeName="r" values="${r + 3};${r + 9};${r + 3}" dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.6s" repeatCount="indefinite"/></circle>` : ''}
        ${sel ? `<circle r="${r + 6}" fill="rgba(163,51,31,0.18)" stroke="#a3331f" stroke-width="3"/>` : ''}
        <circle r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${isAvail || isPos ? 3 : 2}"/>
        ${isPos ? `<circle r="${r - 4}" fill="none" stroke="#f3e6c8" stroke-width="1.5"/>` : ''}
        <svg x="${-r * 0.55}" y="${-r * 0.55}" width="${r * 1.1}" height="${r * 1.1}" viewBox="0 0 24 24" fill="none" stroke="${col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><use href="#i-${info.icon}"/></svg>
        ${n.id === 'boss' ? `<text y="${r + 18}" text-anchor="middle" font-family="Grenze Gotisch, Georgia, serif" font-size="17" fill="#5b3417">${esc(UNITS[ACTS[run.act].boss].name)}</text>` : ''}
        <circle r="${r + 10}" fill="transparent"/>
      </g>`;
    }
    return `<svg class="mapsvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Campaign map">${lines}${nodes}</svg>`;
  }

  function mapFoot(run) {
    const n = UI.mapSel && R.getNode(run, UI.mapSel);
    if (!n) return `<span class="muted grow">Tap a glowing stop on the map to choose your path.</span>`;
    const info = NODE_INFO[n.kind];
    const desc = n.kind === 'boss' ? `${UNITS[ACTS[run.act].boss].name}. ${UNITS[ACTS[run.act].boss].desc}` : info.desc;
    return `<div class="grow" style="min-width:0"><b>${info.name}</b><div class="small muted">${esc(desc)}</div></div>
      <button class="btn primary" id="mGo">${ic(info.icon)} Enter</button>`;
  }

  function mapScreen() {
    const run = UI.run;
    UI.battle = null;
    const act = ACTS[run.act];
    const avail = R.availableNodes(run).map((n) => n.id);
    if (UI.mapSel && !avail.includes(UI.mapSel)) UI.mapSel = null;
    if (!UI.mapSel && avail.length === 1) UI.mapSel = avail[0];
    const wide = isWide();
    const v = showView(
      `<div class="map-head">
        <div class="act"><span class="eyebrow">${act.short}</span><h2>${esc(act.name)}</h2></div>
        <div class="controls">${resbar(run)}
          <button class="btn" id="mRelics">${ic('gem')} ${run.relics.length}</button>
          <button class="btn" id="mArmy">${ic('army')} Army</button>
          <button class="btn icon-only" id="mMenu" aria-label="Menu">${ic('menu')}</button></div>
      </div>
      <div class="map-body"><div class="parchment ${wide ? 'horiz' : ''}">${mapSVG(run, avail)}
        <div class="legend">${['battle', 'elite', 'event', 'shop', 'rest', 'treasure']
          .map((k) => `<span>${ic(NODE_INFO[k].icon)} ${NODE_INFO[k].name}</span>`)
          .join('')}</div></div></div>
      <div class="map-foot"><div class="inner ${wide ? 'horiz' : ''}" id="mFoot">${mapFoot(run)}</div></div>`,
      'map-screen'
    );
    UI.mapWide = wide;
    const bindFoot = () => {
      const go = $('#mGo', v);
      if (go)
        go.onclick = () => {
          const id = UI.mapSel;
          UI.mapSel = null;
          if (R.enterNode(run, id)) {
            sfx('select');
            route();
          }
        };
    };
    for (const g of $$('[data-node]', v)) {
      const pick = () => {
        const id = g.dataset.node;
        if (!avail.includes(id)) {
          const n = R.getNode(run, id);
          toast(NODE_INFO[n.kind].name + (n.kind === 'boss' ? ': ' + UNITS[act.boss].name : ': ' + NODE_INFO[n.kind].desc));
          return;
        }
        UI.mapSel = id;
        sfx('click');
        mapScreen();
      };
      g.addEventListener('click', pick);
      g.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') pick();
      });
    }
    bindFoot();
    $('#mArmy', v).onclick = () => armySheet(() => mapScreen());
    $('#mMenu', v).onclick = () => menuSheet();
    $('#mRelics', v).onclick = () => relicSheet();
    const focus = $(`[data-node="${UI.mapSel || avail[0] || run.pos}"]`, v);
    if (focus && focus.scrollIntoView) setTimeout(() => focus.scrollIntoView({ block: 'center' }), 30);
  }

  function menuSheet(inBattle) {
    openSheet(
      `${sheetHead('Menu')}
      <div class="army-list">
        <button class="btn wide" id="muHelp">${ic('help')} How to play</button>
        <button class="btn wide" id="muCodex">${ic('book')} Units</button>
        <button class="btn wide" id="muSound">${ic(AG.Audio.enabled ? 'sound' : 'mute')} Sound: ${AG.Audio.enabled ? 'on' : 'off'}</button>
        ${inBattle ? `<button class="btn wide danger" id="muRetreat">${ic('flag')} Retreat (lose a Banner)</button>` : ''}
        <button class="btn wide" id="muTitle">Save and quit to title</button>
        ${!inBattle ? `<button class="btn wide danger" id="muAbandon">Abandon campaign</button>` : ''}
      </div>`,
      (sh) => {
        $('#muHelp', sh).onclick = () => helpSheet();
        $('#muCodex', sh).onclick = () => codexSheet();
        $('#muSound', sh).onclick = () => {
          AG.Audio.toggle();
          menuSheet(inBattle);
        };
        $('#muTitle', sh).onclick = () => {
          closeSheet();
          if (UI.board) UI.board.stop();
          title();
        };
        if ($('#muRetreat', sh))
          $('#muRetreat', sh).onclick = async () => {
            closeSheet();
            if (!(await confirmSheet('Retreat?', 'Retreating counts as a defeat: you lose a Banner and must fight this battle again.', 'Retreat', 'Keep fighting', true))) return;
            const B = UI.battle;
            if (!B || B.busy) return;
            E.forfeit(B.s);
            E.drainEvents(B.s);
            battleOver();
          };
        if ($('#muAbandon', sh))
          $('#muAbandon', sh).onclick = async () => {
            closeSheet();
            if (!(await confirmSheet('Abandon campaign?', 'This ends the campaign for good.', 'Abandon', 'Keep going', true))) return;
            UI.run.over = true;
            UI.run.won = false;
            R.recordMeta(UI.run);
            R.clearSave();
            UI.run = null;
            title();
          };
      }
    );
  }

  function relicSheet() {
    const run = UI.run;
    openSheet(
      `${sheetHead('Relics', 'Passive bonuses that last the whole campaign.')}
      <div class="army-list">${run.relics
        .map((id) => `<div class="card"><div class="kind">${ic('gem')} ${RELICS[id].tier}</div><div class="title">${esc(RELICS[id].name)}</div><div class="desc">${esc(RELICS[id].desc)}</div></div>`)
        .join('')}</div>`
    );
  }

  // ------------------------------------------------------------ army

  function armySheet(after) {
    const run = UI.run;
    const rows = run.roster
      .map((u) => {
        const c = R.promoteCost(run, u);
        return `<button class="army-row" data-rid="${u.id}">
          <canvas class="portrait" data-p="${u.type}:P"></canvas>
          <div class="nm" style="min-width:0"><b>${esc(u.name)}</b> <span class="stars">${stars(u.rank)}</span>
            <div class="small muted">${UNITS[u.type].name} · ${UNITS[u.type].cost} CP${u.talents.length ? ' · ' + u.talents.map((t) => TALENTS[t].name).join(', ') : ''}</div></div>
          <div class="chips" style="justify-content:flex-end">${u.wounded ? '<span class="chip bad">Wounded</span>' : ''}${
            c != null ? `<span class="chip ${run.gold >= c ? 'warn' : ''}">${ic('up')} ${c}</span>` : ''
          }</div></button>`;
      })
      .join('');
    openSheet(
      `${sheetHead('Your army', `${run.roster.length}/${R.MAX_ROSTER} units · ${ic('gold')} ${run.gold} gold · Promote for gold to raise a unit's rank.`)}
      <div class="army-list">${rows}</div>`,
      (sh) => {
        for (const b of $$('[data-rid]', sh)) b.onclick = () => unitSheet(b.dataset.rid, after);
      }
    );
    UI.onSheetClose = after || null;
  }

  function unitSheet(rid, after) {
    const run = UI.run;
    const r = R.unitById(run, rid);
    if (!r) return;
    const u = computed(r);
    const T = UNITS[r.type];
    const c = R.promoteCost(run, r);
    const talents = r.talents.map((t) => `<li><b>${esc(TALENTS[t].name)}</b>: ${esc(TALENTS[t].desc)}</li>`).join('');
    const traits = traitLines(u)
      .map((t) => `<li>${esc(t)}</li>`)
      .join('');
    openSheet(
      `${sheetHead(esc(r.name), `${T.name} · Rank ${['I', 'II', 'III'][r.rank - 1]} · ${T.cost} CP to deploy`)}
      ${unitInfoHTML(u, { name: r.name, wounded: r.wounded })}
      ${statsHTML(u)}
      <p class="ability"><b>${esc(u.act.name)}.</b> ${esc(abilityText(u))}</p>
      ${traits ? `<ul class="tips">${traits}</ul>` : ''}
      <div><div class="eyebrow">Talents (${r.talents.length}/${MAX_TALENTS})</div>${talents ? `<ul class="tips">${talents}</ul>` : '<p class="small muted">None yet. Win battles, visit shrines and merchants to teach talents.</p>'}</div>
      ${r.rank < 3 && T.star3 ? `<p class="small muted">At Rank III: <b>${esc(T.star3.name)}</b>. ${esc(T.star3.desc)}</p>` : ''}
      ${r.wounded ? '<p class="small" style="color:var(--red)">Wounded: starts battles at half HP. Sit out a battle, rest, or buy healing to recover.</p>' : ''}
      <p class="small muted">Battles: ${r.battles} · Enemies slain: ${r.kills}</p>
      <div class="actions">
        ${c != null ? `<button class="btn primary" id="usPromote" ${run.gold < c ? 'disabled' : ''}>${ic('up')} Promote to Rank ${['I', 'II', 'III'][r.rank]} · ${c} gold</button>` : ''}
        <button class="btn" id="usDismiss" ${run.roster.length <= 2 ? 'disabled' : ''}>Dismiss (+15 gold)</button>
        <button class="btn" id="usBack">Back</button>
      </div>`,
      (sh) => {
        if ($('#usPromote', sh))
          $('#usPromote', sh).onclick = () => {
            if (R.promote(run, rid)) {
              R.save(run);
              sfx('coin');
              toast(`${r.name} is now Rank ${['I', 'II', 'III'][r.rank - 1]}.`);
              unitSheet(rid, after);
              if (UI.wr) renderWarRoom();
            }
          };
        $('#usDismiss', sh).onclick = async () => {
          UI.onSheetClose = null;
          const ok = await confirmSheet('Dismiss ' + r.name + '?', 'They leave your army for good. You get 15 gold.', 'Dismiss', 'Keep', true);
          if (ok && R.dismiss(run, rid)) {
            R.save(run);
            if (UI.wr) UI.wr.dep.delete(rid);
          }
          armySheet(after);
          if (UI.wr) renderWarRoom();
        };
        $('#usBack', sh).onclick = () => armySheet(after);
      }
    );
    UI.onSheetClose = after || null;
  }

  // Details for a unit on the battlefield (either side).
  function battleUnitSheet(u, extra) {
    const T = UNITS[u.type];
    const traits = traitLines(u)
      .map((t) => `<li>${esc(t)}</li>`)
      .join('');
    const talents = [...u.tal].map((t) => `<li><b>${esc(TALENTS[t].name)}</b>: ${esc(TALENTS[t].desc)}</li>`).join('');
    openSheet(
      `${sheetHead(esc(u.name), `${u.team === 'P' ? 'Your' : 'Enemy'} ${T.name} · Rank ${['I', 'II', 'III'][u.rank - 1]}`)}
      ${unitInfoHTML(u, { status: !!extra })}
      ${statsHTML(u)}
      <p class="ability"><b>${esc(u.act.name)}.</b> ${esc(abilityText(u))}</p>
      ${traits ? `<ul class="tips">${traits}</ul>` : ''}
      ${talents ? `<ul class="tips">${talents}</ul>` : ''}
      <p class="small muted">${esc(T.desc)}</p>
      ${u.team === 'E' ? `<p class="hint">${esc(T.tip)}</p>` : ''}
      <div class="actions"><button class="btn" data-close>Close</button></div>`
    );
  }

  // ------------------------------------------------------------ objectives

  function objectivesHTML(enc, s) {
    const info = R.objectiveInfo(UI.run, enc);
    let status = '';
    if (s && s.hold) status = ` <span class="reward">${s.hold.count}/${s.hold.need}</span>`;
    if (s && s.surviveTurns) status = ` <span class="reward">${Math.max(0, s.surviveTurns - s.turn + 1)} to go</span>`;
    const lines = [`<div class="obj primary">${ic('flag')}<span><b>${esc(info.short)}.</b> ${esc(info.primary)}${status}</span></div>`];
    for (const o of info.bonus) {
      let state = '';
      if (s) {
        const b = o.b;
        if (b.type === 'loot' && s.loot.some((l) => l.id === b.lootId && l.taken)) state = 'done';
        if (b.type === 'swift' && s.turn > b.turns) state = 'failed';
        if (b.type === 'flawless' && s.units.some((u) => u.team === 'P' && !u.nonCombat && !u.alive)) state = 'failed';
        if (b.type === 'muster') state = s.units.some((u) => u.rid === b.rid) ? 'done' : 'failed';
      }
      lines.push(`<div class="obj bonus ${state}">${ic(state === 'done' ? 'check' : 'star')}<span>${esc(o.text)} <span class="reward">Reward: ${esc(o.reward)}.</span></span></div>`);
    }
    return `<div class="objectives">${lines.join('')}</div>`;
  }

  // ------------------------------------------------------------ war room

  function encKindLabel(enc) {
    return enc.kind === 'boss' ? 'Boss battle' : enc.kind === 'elite' ? 'Elite battle' : 'Battle';
  }

  function warRoom() {
    const run = UI.run;
    const p = run.pending;
    const enc = p.enc;
    const node = R.getNode(run, p.nodeId);
    const b = showBattleLayout();
    b.clearUnits();
    b.ov = {};
    b.zoom = 1;
    b.panX = 0;
    b.panY = 0;
    b.speed = 1;
    b.activeSide = null;
    b.readySet = null;
    b.setBoard(enc.w, enc.h, enc.terrain, ACTS[run.act].palette);
    b.setObjectives(enc.loot, enc.hold);
    const cp = R.cpFor(run, node, false, enc.kind);
    const rows = R.deployRows(run, enc);
    const dep = new Map();
    let used = 0;
    for (const d of p.lastDep || []) {
      const r = R.unitById(run, d.rid);
      if (!r || !rows.includes(d.y) || enc.terrain[d.y * enc.w + d.x] !== 0) continue;
      if (used + UNITS[r.type].cost > cp) continue;
      if ([...dep.values()].some((o) => o.x === d.x && o.y === d.y)) continue;
      used += UNITS[r.type].cost;
      dep.set(d.rid, { x: d.x, y: d.y, facing: d.facing != null ? d.facing : 0 });
    }
    UI.wr = { cp, dep, sel: null, tab: 'army', inspect: null, rows, enc };
    UI.boardTap = wrTap;
    UI.boardLong = wrLong;
    boardTools();
    renderWarRoom();
  }

  function wrDepArray() {
    return [...UI.wr.dep.entries()].map(([rid, d]) => ({ rid, x: d.x, y: d.y, facing: d.facing }));
  }

  function wrUsed() {
    let t = 0;
    for (const rid of UI.wr.dep.keys()) t += R.deployCost(UI.run, rid);
    return t;
  }

  function isDeployTile(x, y) {
    const wr = UI.wr;
    return wr.rows.includes(y) && x >= 0 && x < wr.enc.w && wr.enc.terrain[y * wr.enc.w + x] === 0;
  }

  function wrRidAt(x, y) {
    for (const [rid, d] of UI.wr.dep) if (d.x === x && d.y === y) return rid;
    return null;
  }

  function isAttacker(type) {
    const a = UNITS[type].act;
    return !!(a.dmg || (a.fx && a.fx.poison));
  }

  function renderWarRoom() {
    const run = UI.run;
    const wr = UI.wr;
    if (!wr || !run.pending || run.pending.type !== 'battle') return;
    for (const rid of [...wr.dep.keys()]) if (!R.unitById(run, rid)) wr.dep.delete(rid);
    const enc = wr.enc;
    const s = E.createBattle(R.battleConfig(run, wrDepArray()));
    wr.s = s;
    const b = UI.board;
    b.syncFromState(s);
    const ov = { deploy: [] };
    for (const y of wr.rows) for (let x = 0; x < enc.w; x++) if (isDeployTile(x, y)) ov.deploy.push([x, y]);
    if (wr.sel && wr.dep.has(wr.sel)) {
      const d = wr.dep.get(wr.sel);
      ov.select = [d.x, d.y];
    }
    if (wr.inspect) {
      const v = s.byId[wr.inspect];
      if (v) {
        const th = AI.unitThreat(s, v);
        ov.range = th.hit;
        ov.move = th.move.filter(([x, y]) => x !== v.x || y !== v.y);
        ov.select = [v.x, v.y];
      }
    }
    b.ov = ov;

    const used = wrUsed();
    const unspent = wr.cp - used;
    const gold = unspent * R.EFFICIENCY_GOLD * (R.hasRelic(run, 'alchemist_stone') ? 2 : 1);
    const pips = [];
    for (let i = 0; i < Math.max(wr.cp, used); i++) pips.push(`<span class="pip ${i < used ? (i >= wr.cp ? 'over' : 'used') : ''}"></span>`);

    $('#topbar').innerHTML = `<div class="title"><b>War Room</b><span>${esc(enc.name)} · ${encKindLabel(enc)}${enc.objective === 'boss' ? ' · slay the boss' : ''}</span></div>
      <button class="btn icon-only" id="wrArmy" aria-label="Army">${ic('army')}</button>
      <button class="btn icon-only" id="wrMenu" aria-label="Menu">${ic('menu')}</button>`;
    $('#wrArmy').onclick = () => armySheet(() => renderWarRoom());
    $('#wrMenu').onclick = () => menuSheet(false);

    let body = '';
    if (wr.tab === 'army') {
      body = `<div class="roster">${run.roster
        .map((u) => {
          const deployed = wr.dep.has(u.id);
          const cost = UNITS[u.type].cost;
          const cant = !deployed && cost > unspent;
          const featured = (enc.bonus || []).some((x) => x.type === 'muster' && x.rid === u.id);
          return `<button class="rcard ${deployed ? 'deployed' : ''} ${wr.sel === u.id ? 'sel' : ''} ${cant ? 'dim' : ''}" data-rid="${u.id}">
            <span class="cost">${cost}</span>${u.wounded ? '<span class="flag">Hurt</span>' : featured ? '<span class="flag feat">Bonus</span>' : ''}
            <canvas data-p="${u.type}:P"></canvas>
            <span class="nm">${esc(u.name)} <span class="stars">${stars(u.rank)}</span></span>
            <span class="ty">${UNITS[u.type].name}</span></button>`;
        })
        .join('')}</div>`;
    } else {
      const tips = R.scoutTips(enc);
      body = `<div class="intel">
        <div class="intel-list">${s.units
          .filter((u) => u.team === 'E')
          .map(
            (u) => `<button class="rcard ${wr.inspect === u.uid ? 'sel' : ''}" data-uid="${u.uid}">
              <canvas data-p="${u.type}:E"></canvas>
              <span class="nm">${esc(UNITS[u.type].name)} <span class="stars">${stars(u.rank)}</span></span>
              <span class="ty">${u.tal.size ? [...u.tal].map((t) => TALENTS[t].name).join(', ') : u.hp + ' HP'}</span></button>`
          )
          .join('')}</div>
        ${tips.length ? `<ul class="tips">${tips.map((t) => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}
      </div>`;
    }

    let selBlock = '';
    if (wr.sel && wr.dep.has(wr.sel)) {
      const r = R.unitById(run, wr.sel);
      const u = s.units.find((x) => x.rid === wr.sel);
      selBlock = `<div class="hint">${esc(r.name)} the ${UNITS[r.type].name} · ${u ? u.hp + '/' + u.maxHp + ' HP · ' : ''}tap a blue tile to move, or another of your units to swap places.</div>
        <div class="actions"><button class="btn" id="wrTurn">${ic('rotate')} Turn</button>
        <button class="btn" id="wrInfo">${ic('help')} Details</button>
        <button class="btn danger" id="wrRemove">${ic('close')} Remove</button></div>`;
    } else if (wr.inspect && s.byId[wr.inspect]) {
      const u = s.byId[wr.inspect];
      selBlock = `<div class="hint">Enemy ${esc(UNITS[u.type].name)}: <b>${esc(u.act.name)}</b>. ${esc(abilityText(u))} Red tiles show where it can strike next turn.</div>
        <div class="actions"><button class="btn" id="wrEInfo">${ic('help')} Details</button></div>`;
    } else if (wr.dep.size === 0) {
      selBlock = `<div class="hint">Study the enemy, then tap units in your army to deploy them into the blue zone. Points you leave unspent turn into gold if you win.</div>`;
    }

    $('#cmd').innerHTML = `
      <div class="cp-meter"><span class="res">${ic('command')}<span class="num">${used}/${wr.cp}</span></span><div class="pips">${pips.join('')}</div></div>
      <div class="small ${unspent < 0 ? '' : 'muted'}">${
        unspent > 0 ? `${unspent} unspent → <b style="color:var(--brass-hi)">+${gold} gold</b> if you win` : unspent === 0 ? 'Every Command Point committed.' : 'Over budget.'
      }</div>
      ${objectivesHTML(enc)}
      <div class="tabs"><button class="btn ${wr.tab === 'army' ? 'on' : ''}" id="wrTabA">${ic('army')} Your army</button>
        <button class="btn ${wr.tab === 'intel' ? 'on' : ''}" id="wrTabI">${ic('eye')} Enemy (${enc.units.length})</button></div>
      ${body}
      ${selBlock}
      <div class="actions"><button class="btn" id="wrAuto">Auto</button><button class="btn" id="wrClear" ${wr.dep.size ? '' : 'disabled'}>Clear</button>
        <button class="btn primary" id="wrFight" ${wr.dep.size ? '' : 'disabled'}>${ic('swords')} Fight</button></div>`;
    const cmd = $('#cmd');
    drawPortraits(cmd);
    $('#wrTabA').onclick = () => {
      wr.tab = 'army';
      renderWarRoom();
    };
    $('#wrTabI').onclick = () => {
      wr.tab = 'intel';
      renderWarRoom();
    };
    for (const c of $$('.rcard[data-rid]', cmd)) c.onclick = () => wrCard(c.dataset.rid);
    for (const c of $$('.rcard[data-uid]', cmd))
      c.onclick = () => {
        wr.inspect = wr.inspect === +c.dataset.uid ? null : +c.dataset.uid;
        wr.sel = null;
        renderWarRoom();
      };
    if ($('#wrTurn'))
      $('#wrTurn').onclick = () => {
        const d = wr.dep.get(wr.sel);
        d.facing = (d.facing + 1) % 4;
        renderWarRoom();
      };
    if ($('#wrInfo')) $('#wrInfo').onclick = () => unitSheet(wr.sel, () => renderWarRoom());
    if ($('#wrRemove'))
      $('#wrRemove').onclick = () => {
        wr.dep.delete(wr.sel);
        wr.sel = null;
        renderWarRoom();
      };
    if ($('#wrEInfo')) $('#wrEInfo').onclick = () => battleUnitSheet(s.byId[wr.inspect]);
    $('#wrAuto').onclick = () => {
      wr.dep.clear();
      for (const d of R.suggestDeployment(run, wr.cp)) wr.dep.set(d.rid, { x: d.x, y: d.y, facing: 0 });
      wr.sel = null;
      sfx('click');
      renderWarRoom();
    };
    $('#wrClear').onclick = () => {
      wr.dep.clear();
      wr.sel = null;
      renderWarRoom();
    };
    $('#wrFight').onclick = () => wrFight();
  }

  function wrCard(rid) {
    const run = UI.run;
    const wr = UI.wr;
    if (wr.dep.has(rid)) {
      wr.sel = wr.sel === rid ? null : rid;
      wr.inspect = null;
      sfx('click');
      renderWarRoom();
      return;
    }
    const r = R.unitById(run, rid);
    const cost = UNITS[r.type].cost;
    const left = wr.cp - wrUsed();
    if (cost > left) {
      toast(`Not enough Command Points: ${r.name} needs ${cost}, you have ${left} left.`);
      return;
    }
    const taken = new Set([...wr.dep.values()].map((d) => d.x + ',' + d.y));
    const front = ['tank', 'melee', 'skirmisher', 'monster'].includes(UNITS[r.type].role) || r.type === 'lightning';
    const slot = R.deploySlots(run, wr.enc, front, taken)[0];
    if (!slot) {
      toast('Your deployment zone is full.');
      return;
    }
    wr.dep.set(rid, { x: slot.x, y: slot.y, facing: 0 });
    wr.sel = rid;
    wr.inspect = null;
    sfx('select');
    renderWarRoom();
  }

  function wrTap(hit) {
    const wr = UI.wr;
    if (!wr) return;
    const s = wr.s;
    const raw = hit.tile;
    const tileUnit = raw ? E.at(s, raw.x, raw.y) : null;
    const spriteUnit = hit.unitTile ? s.byId[hit.unitTile.uid] : null;
    let t = raw;
    // With a unit picked up, an open blue tile under the finger is where it goes.
    const placing = wr.sel && wr.dep.has(wr.sel) && raw && !tileUnit && isDeployTile(raw.x, raw.y);
    if (!placing && spriteUnit) t = { x: spriteUnit.x, y: spriteUnit.y };
    if (!t) return;
    const unit = E.at(s, t.x, t.y);
    if (unit && unit.team === 'E') {
      wr.inspect = wr.inspect === unit.uid ? null : unit.uid;
      wr.sel = null;
      sfx('click');
      renderWarRoom();
      return;
    }
    const rid = wrRidAt(t.x, t.y);
    if (rid) {
      if (wr.sel && wr.sel !== rid && wr.dep.has(wr.sel)) {
        const a = wr.dep.get(wr.sel);
        const bpos = wr.dep.get(rid);
        const ax = a.x;
        const ay = a.y;
        a.x = bpos.x;
        a.y = bpos.y;
        bpos.x = ax;
        bpos.y = ay;
        wr.sel = null;
        sfx('step');
      } else {
        wr.sel = wr.sel === rid ? null : rid;
        sfx('click');
      }
      wr.inspect = null;
      renderWarRoom();
      return;
    }
    if (isDeployTile(t.x, t.y)) {
      if (wr.sel && wr.dep.has(wr.sel)) {
        const d = wr.dep.get(wr.sel);
        d.x = t.x;
        d.y = t.y;
        sfx('step');
      } else toast('Pick a unit from your army first, then tap a blue tile.');
      renderWarRoom();
      return;
    }
    wr.sel = null;
    wr.inspect = null;
    renderWarRoom();
  }

  function wrLong(hit) {
    const wr = UI.wr;
    if (!wr) return;
    const t = hit.unitTile || hit.tile;
    if (!t) return;
    const u = E.at(wr.s, t.x, t.y);
    if (!u) return;
    if (u.team === 'P' && u.rid) unitSheet(u.rid, () => renderWarRoom());
    else battleUnitSheet(u);
  }

  async function wrFight() {
    const run = UI.run;
    const wr = UI.wr;
    const dep = wrDepArray();
    if (!dep.length) return;
    if (wrUsed() > wr.cp) {
      toast('You are over your Command Point budget.');
      return;
    }
    if (!dep.some((d) => isAttacker(R.unitById(run, d.rid).type))) {
      toast('Deploy at least one unit that can deal damage.');
      return;
    }
    const wounded = dep.filter((d) => R.unitById(run, d.rid).wounded);
    if (wounded.length && !(await confirmSheet('Field wounded units?', `${wounded.map((d) => esc(R.unitById(run, d.rid).name)).join(', ')} will start at half HP.`, 'Fight anyway', 'Back'))) return;
    run.pending.lastDep = dep;
    R.save(run);
    startBattle(dep);
  }

  // ------------------------------------------------------------ battle

  function startBattle(dep) {
    const run = UI.run;
    const enc = run.pending.enc;
    const diff = DIFFICULTIES.find((d) => d.id === run.difficulty) || DIFFICULTIES[1];
    const s = E.createBattle(R.battleConfig(run, dep));
    E.drainEvents(s);
    UI.wr = null;
    UI.battle = { s, dep, enc, mode: 'idle', sel: null, target: null, busy: false, temp: diff.temp, confirmEnd: false };
    const b = UI.board;
    b.clearUnits();
    b.ov = {};
    b.speed = UI.prefs.fast ? 2 : 1;
    b.syncFromState(s);
    b.setObjectives(s.loot, s.hold);
    b.activeSide = 'P';
    UI.boardTap = btTap;
    UI.boardLong = btLong;
    boardTools(
      `<button class="btn icon-only ${UI.prefs.threat ? 'on' : ''}" id="btThreat" aria-label="Show enemy reach">${ic('eye')}</button>
       <button class="btn icon-only ${UI.prefs.fast ? 'on' : ''}" id="btFast" aria-label="Fast animations">${ic('fast')}</button>`
    );
    $('#btThreat').onclick = () => {
      UI.prefs.threat = !UI.prefs.threat;
      savePrefs();
      $('#btThreat').classList.toggle('on', UI.prefs.threat);
      toast(UI.prefs.threat ? 'Showing tiles the enemy can strike next turn.' : 'Enemy reach hidden.');
      renderBattle();
    };
    $('#btFast').onclick = () => {
      UI.prefs.fast = !UI.prefs.fast;
      savePrefs();
      b.speed = UI.prefs.fast ? 2 : 1;
      $('#btFast').classList.toggle('on', UI.prefs.fast);
    };
    showBanner('Your Turn');
    sfx('turn');
    renderBattle();
  }

  // Ready units that can actually do something this turn.
  function usefulReady(s) {
    return E.readyUnits(s, 'P').filter(
      (u) => (u.move > 0 && !u.traits.has('immobile') && E.reachable(s, u).size > 1) || E.targetsFrom(s, u).length > 0
    );
  }

  function directKinds(kind) {
    return kind === 'strike' || kind === 'cleave' || kind === 'quake';
  }

  function activationOf(u) {
    const s = UI.battle.s;
    return s.act && s.act.uid === u.uid ? s.act : null;
  }

  function targetTiles(u, t) {
    const s = UI.battle.s;
    if (t.kind === 'unit' || t.kind === 'tile') return [[t.x, t.y]];
    if (t.kind === 'self') return [[u.x, u.y]];
    return E.affectedTiles(s, u, t).filter(([x, y]) => E.at(s, x, y));
  }

  function renderBattle() {
    const B = UI.battle;
    if (!B) return;
    const s = B.s;
    const b = UI.board;
    const ov = {};
    b.activeSide = s.side === 'P' && !B.busy ? 'P' : null;
    b.readySet = new Set(usefulReady(s).map((x) => x.uid));
    if (UI.prefs.threat && s.side === 'P' && !s.over) {
      const m = AI.threatMap(s, 'P');
      ov.danger = [];
      for (let i = 0; i < m.length; i++) if (m[i]) ov.danger.push([i % s.w, Math.floor(i / s.w), m[i]]);
    }
    const u = B.sel ? s.byId[B.sel] : null;
    const A = u ? activationOf(u) : null;
    let panel = '';
    const endBtn = (primary) =>
      `<button class="btn ${primary ? 'primary' : ''}" id="btEnd" ${s.side !== 'P' || B.busy ? 'disabled' : ''}>${B.confirmEnd ? 'Confirm end turn' : 'End turn'}</button>`;

    if (s.side !== 'P' || B.busy) {
      panel = `<div class="hint">${s.side === 'P' ? 'Resolving…' : 'The enemy is moving. Tap the fast-forward button to speed things up.'}</div>`;
    } else if (B.mode === 'unit' && u) {
      const moved = A && A.moved;
      const acted = A && A.acted;
      if (!moved) ov.move = [...E.reachable(s, u).values()].filter((r) => r.d > 0).map((r) => [r.x, r.y]);
      const targets = acted ? [] : E.targetsFrom(s, u);
      if (!acted && directKinds(u.act.kind)) ov.targets = targets.map((t) => [t.x, t.y]);
      ov.select = [u.x, u.y];
      let hint;
      if (!moved && !acted)
        hint = directKinds(u.act.kind)
          ? `Tap a blue tile to move${targets.length ? ', or a red enemy to attack' : ''}.`
          : `Tap a blue tile to move, or use ${esc(u.act.name)}.`;
      else if (moved && !acted) hint = targets.length ? `Moved. ${directKinds(u.act.kind) ? 'Tap a red enemy to attack' : 'Use ' + esc(u.act.name)}, or tap Done.` : 'Moved. No targets in reach from here. Tap Done.';
      else hint = 'Action used. You may still move, or tap Done.';
      const loot = !acted && E.lootAt(s, u.x, u.y);
      if (loot) hint = `${esc(u.name)} stands on the ${R.LOOT_NAMES[loot.kind]}. Taking it uses this unit's action${targets.length ? ', so it cannot attack this turn' : ''}.`;
      panel = `${unitInfoHTML(u, { status: true })}${statsHTML(u)}
        <p class="ability"><b>${esc(u.act.name)}.</b> ${esc(abilityText(u))}</p>
        <div class="hint">${hint}</div>
        <div class="actions">
          ${loot ? `<button class="btn primary" id="btLoot">${ic('chest')} Take the ${R.LOOT_NAMES[loot.kind]}</button>` : ''}
          ${!acted && targets.length ? `<button class="btn ${loot ? '' : 'primary'}" id="btAim">${ic('target')} ${esc(u.act.name)}</button>` : ''}
          ${moved && !acted ? `<button class="btn" id="btUndo">${ic('undo')} Undo move</button>` : ''}
          ${moved || acted ? `<button class="btn" id="btDone">${ic('check')} Done</button>` : `<button class="btn" id="btFace">${ic('rotate')} Turn only</button>`}
          <button class="btn ghost" id="btDesel">${ic('close')}</button>
        </div>`;
    } else if ((B.mode === 'aim' || B.mode === 'confirm') && u) {
      const targets = E.targetsFrom(s, u);
      ov.targets = [];
      for (const t of targets) ov.targets.push(...targetTiles(u, t));
      ov.select = [u.x, u.y];
      let prev = '';
      if (B.mode === 'confirm' && B.target) {
        const pv = E.previewAction(s, u, B.target);
        ov.aoe = pv.tiles.map(([x, y]) => {
          const o = E.at(s, x, y);
          return [x, y, u.act.kind === 'pray' ? 'heal' : o && o.team === u.team && o !== u ? 'ally' : 'foe'];
        });
        if (B.target.kind === 'unit' || B.target.kind === 'tile') ov.targets = ov.targets.filter(([x, y]) => x !== B.target.x || y !== B.target.y);
        prev = previewHTML(u, pv);
      }
      panel = `${unitInfoHTML(u, { status: true })}
        ${B.mode === 'confirm' ? prev : `<div class="hint">Choose a target for ${esc(u.act.name)}: tap a red tile${u.act.kind === 'line' || u.act.kind === 'cone' ? ' or a unit in that direction' : ''}.</div>`}
        <div class="actions">
          ${B.mode === 'confirm' ? `<button class="btn primary" id="btConfirm">${ic('check')} ${esc(u.act.name)}</button>` : ''}
          <button class="btn" id="btCancel">Cancel</button>
        </div>
        ${B.mode === 'confirm' ? '<p class="small muted">Tap the target again, or the button, to confirm.</p>' : ''}`;
    } else if (B.mode === 'facing' && u) {
      ov.select = [u.x, u.y];
      ov.facing = { x: u.x, y: u.y, current: B.facing };
      panel = `${unitInfoHTML(u, { status: true })}
        <div class="hint">Choose where ${esc(u.name)} faces: tap an arrow. The front blocks best, the sides half as well, the back never.</div>
        <div class="actions"><button class="btn primary" id="btKeep">${ic('check')} Confirm facing</button></div>`;
    } else if (B.mode === 'inspect' && u && u.alive) {
      const th = AI.unitThreat(s, u);
      ov.range = th.hit;
      ov.move = th.move.filter(([x, y]) => x !== u.x || y !== u.y);
      ov.select = [u.x, u.y];
      panel = `${unitInfoHTML(u, { status: true })}${statsHTML(u)}
        <p class="ability"><b>${esc(u.act.name)}.</b> ${esc(abilityText(u))}</p>
        <div class="hint">${u.team === 'E' ? 'Blue: where it can move. Red: where it can strike next turn.' : u.wait > 0 ? `Recovering for ${u.wait} more turn${u.wait > 1 ? 's' : ''}.` : u.activated ? 'Already acted this turn.' : 'Cannot act right now.'}</div>
        <div class="actions">${s.act && s.act.uid !== u.uid ? `<button class="btn primary" id="btBack">Back to ${esc(s.byId[s.act.uid].name)}</button>` : ''}<button class="btn" id="btInfo">${ic('help')} Details</button>${s.act ? '' : `<button class="btn ghost" id="btDesel">${ic('close')}</button>${endBtn(false)}`}</div>`;
    } else {
      B.mode = 'idle';
      const ready = usefulReady(s);
      panel = `<div class="hint">${
        ready.length
          ? 'Tap a glowing unit to command it. Long-press any unit for details.'
          : 'All your units have acted or are recovering. End your turn.'
      }</div>
        ${ready.length ? `<div class="roster">${ready
          .map(
            (r) => `<button class="rcard" data-uid="${r.uid}"><canvas data-p="${r.type}:P"></canvas>
            <span class="nm">${esc(r.name)}</span><span class="ty">${r.hp}/${r.maxHp} HP</span></button>`
          )
          .join('')}</div>` : ''}
        ${objectivesHTML(B.enc, s)}
        <div class="actions">${endBtn(!ready.length)}</div>`;
    }
    b.ov = ov;

    const alive = (team) => s.units.filter((x) => x.alive && x.team === team && !x.nonCombat).length;
    const info = R.objectiveInfo(UI.run, B.enc);
    const goal = s.hold ? `${info.short} ${s.hold.count}/${s.hold.need}` : s.surviveTurns ? `Survive ${Math.max(0, s.surviveTurns - s.turn + 1)} more` : info.short;
    void alive;
    $('#topbar').innerHTML = `<div class="title"><b>${s.side === 'P' ? 'Your turn' : 'Enemy turn'}</b>
      <span>Turn ${Math.min(s.turn, s.turnLimit)} of ${s.turnLimit} · ${esc(goal)}</span></div>
      ${s.side === 'P' && !B.busy && B.mode !== 'idle' ? endBtn(false) : ''}
      <button class="btn icon-only" id="btMenu" aria-label="Menu">${ic('menu')}</button>`;
    $('#cmd').innerHTML = panel;
    drawPortraits($('#cmd'));
    bindBattlePanel();
  }

  function previewHTML(u, pv) {
    const s = UI.battle.s;
    const lines = pv.effects.map((e) => {
      const v = s.byId[e.uid];
      const who = `${v.team === 'P' ? 'Your' : 'Enemy'} ${esc(UNITS[v.type].name)}`;
      const bits = [];
      if (e.dmg != null) {
        bits.push(`<b>${e.dmg}</b> dmg`);
        if (e.block > 0) bits.push(`${pct(e.block)} block (${e.cat})`);
        else if (u.act.dmg === 'phys') bits.push(e.cat === 'back' ? 'from behind' : 'no block');
        if (e.kill) bits.push(`<span class="kill">${e.block > 0 ? 'can kill' : 'kills'}</span>`);
      }
      if (e.heal != null) bits.push(e.heal > 0 ? `<b>+${e.heal}</b> HP` : v.poison ? 'poisoned: no healing' : 'full HP');
      if (e.cleanse) bits.push('cures');
      if (e.para) bits.push(e.para === 'resist' ? 'immune to paralysis' : `paralyzed ${e.para}`);
      if (e.poison) bits.push(e.poison === 'resist' ? 'immune to poison' : `poison ${e.poison.dmg}×${e.poison.turns}`);
      return `<div class="line ${e.friendly && u.act.kind !== 'pray' ? 'ff' : ''}">${who}: ${bits.join(' · ') || 'no effect'}${e.friendly && u.act.kind !== 'pray' ? ' (friendly fire)' : ''}</div>`;
    });
    if (u.act.kind === 'grow') lines.push('<div class="line">Raise a shrub here.</div>');
    return `<div class="preview">${lines.join('') || '<div class="line">No units affected.</div>'}</div>`;
  }

  function bindBattlePanel() {
    const B = UI.battle;
    const s = B.s;
    const on = (id, fn) => {
      const el = $('#' + id);
      if (el) el.onclick = fn;
    };
    on('btMenu', () => menuSheet(true));
    on('btEnd', () => endTurn());
    on('btDesel', () => deselect());
    on('btUndo', async () => {
      if (B.busy) return;
      E.undoMove(s);
      await play();
      renderBattle();
    });
    on('btDone', () => enterFacing());
    on('btFace', () => {
      if (!E.beginActivation(s, B.sel)) return;
      enterFacing();
    });
    on('btAim', () => {
      const u = s.byId[B.sel];
      const targets = E.targetsFrom(s, u);
      if (targets.length === 1 && (targets[0].kind === 'self' || !directKinds(u.act.kind))) {
        B.mode = 'confirm';
        B.target = targets[0];
      } else {
        B.mode = 'aim';
        B.target = null;
      }
      sfx('click');
      renderBattle();
    });
    on('btCancel', () => {
      B.mode = 'unit';
      B.target = null;
      renderBattle();
    });
    on('btConfirm', () => doAction());
    on('btLoot', () => doLoot());
    on('btKeep', () => finishUnit(B.facing));
    on('btInfo', () => battleUnitSheet(s.byId[B.sel], true));
    on('btBack', () => s.act && selectUnit(s.byId[s.act.uid]));
    for (const c of $$('#cmd .rcard[data-uid]')) c.onclick = () => selectUnit(s.byId[+c.dataset.uid]);
  }

  async function play() {
    const B = UI.battle;
    B.busy = true;
    UI.board.activeSide = null;
    const ev = E.drainEvents(B.s);
    await UI.board.playEvents(ev, B.s);
    UI.board.syncFromState(B.s);
    B.busy = false;
  }

  function deselect() {
    const B = UI.battle;
    const s = B.s;
    if (s.act && (s.act.moved || s.act.acted)) {
      if (B.sel !== s.act.uid) {
        selectUnit(s.byId[s.act.uid]);
        return;
      }
      enterFacing();
      return;
    }
    E.cancelActivation(s);
    B.mode = 'idle';
    B.sel = null;
    B.target = null;
    renderBattle();
  }

  async function selectUnit(v) {
    const B = UI.battle;
    const s = B.s;
    if (!v || B.busy) return;
    const act = s.act;
    const inProgress = act && (act.moved || act.acted);
    const ownReady = v.team === 'P' && E.canActivate(s, v);
    if (act && act.uid !== v.uid) {
      // Commanding a different unit closes the current one; just looking does not.
      if (inProgress && ownReady) await finishUnit(AI.smartFacing(s, s.byId[act.uid]), true);
      else if (!inProgress) E.cancelActivation(s);
    }
    B.sel = v.uid;
    B.target = null;
    B.confirmEnd = false;
    B.mode = (s.act && s.act.uid === v.uid) || ownReady ? 'unit' : 'inspect';
    if (UI.board.zoom > 1) UI.board.centerOn(v.x, v.y);
    sfx('select');
    renderBattle();
  }

  // Map a tap to the nearest candidate tile (within about half a tile).
  function snap(hit, cands) {
    if (!cands.length) return null;
    const b = UI.board;
    if (hit.unitTile) {
      const m = cands.find((c) => c.x === hit.unitTile.x && c.y === hit.unitTile.y);
      if (m) return m;
    }
    if (hit.tile) {
      const m = cands.find((c) => c.x === hit.tile.x && c.y === hit.tile.y);
      if (m) return m;
    }
    let best = null;
    let bd = b.tw * 0.5;
    for (const c of cands) {
      const [cx, cy] = b.center(c.x, c.y);
      const d = Math.hypot((cx - hit.px) * 0.8, (cy - hit.py) * 1.6);
      if (d < bd) {
        bd = d;
        best = c;
      }
    }
    return best;
  }

  // The unit the player sees under their finger: the front-most sprite, else the tile's unit.
  function unitAtHit(hit) {
    const s = UI.battle.s;
    if (hit.unitTile) {
      const u = s.byId[hit.unitTile.uid];
      if (u && u.alive) return u;
    }
    return hit.tile ? E.at(s, hit.tile.x, hit.tile.y) : null;
  }

  function btTap(hit) {
    const B = UI.battle;
    if (!B || B.busy || B.s.over) return;
    const s = B.s;
    if (s.side !== 'P') return;
    const u = B.sel ? s.byId[B.sel] : null;
    if (B.mode === 'facing' && u) {
      const d = UI.board.facingFromHit(hit, u.x, u.y);
      if (d >= 0) finishUnit(d);
      return;
    }
    if ((B.mode === 'aim' || B.mode === 'confirm') && u) {
      const cands = [];
      for (const t of E.targetsFrom(s, u)) for (const [x, y] of targetTiles(u, t)) cands.push({ x, y, t });
      const c = snap(hit, cands);
      if (c) {
        if (B.mode === 'confirm' && B.target && E.sameTarget(c.t, B.target)) return doAction();
        B.mode = 'confirm';
        B.target = c.t;
        sfx('select');
        renderBattle();
        return;
      }
      B.mode = 'unit';
      B.target = null;
      renderBattle();
      return;
    }
    if (B.mode === 'unit' && u) {
      const A = activationOf(u);
      const tileUnit = hit.tile ? E.at(s, hit.tile.x, hit.tile.y) : null;
      const spriteUnit = hit.unitTile ? s.byId[hit.unitTile.uid] : null;
      // 1. An enemy under the finger (sprite or tile) that this unit can strike: aim at it.
      if (!(A && A.acted) && directKinds(u.act.kind)) {
        const tgts = E.targetsFrom(s, u);
        for (const cand of [tileUnit, spriteUnit]) {
          if (!cand || cand.team === u.team) continue;
          const t = tgts.find((k) => k.uid === cand.uid);
          if (t) {
            B.mode = 'confirm';
            B.target = t;
            sfx('select');
            renderBattle();
            return;
          }
        }
      }
      // 2. The ground tile under the finger is a legal move: move there.
      const moves = A && A.moved ? [] : [...E.reachable(s, u).values()].filter((r) => r.d > 0);
      if (hit.tile) {
        const m = moves.find((r) => r.x === hit.tile.x && r.y === hit.tile.y);
        if (m) return doMove(m.x, m.y);
      }
      // 3. A unit there: select it, or finish with this one.
      const other = spriteUnit || tileUnit;
      if (other && other.alive) {
        if (other.uid === u.uid) {
          if (A && (A.moved || A.acted)) enterFacing();
          else deselect();
          return;
        }
        return selectUnit(other);
      }
      // 4. A near miss: snap to the closest legal move.
      const m = snap({ px: hit.px, py: hit.py, tile: null, unitTile: null }, moves);
      if (m) return doMove(m.x, m.y);
      if (!A || (!A.moved && !A.acted)) deselect();
      return;
    }
    const other = unitAtHit(hit);
    if (other) return selectUnit(other);
    if (s.act && (s.act.moved || s.act.acted)) return selectUnit(s.byId[s.act.uid]);
    B.mode = 'idle';
    B.sel = null;
    renderBattle();
  }

  function btLong(hit) {
    const B = UI.battle;
    if (!B) return;
    const u = unitAtHit(hit);
    if (u) battleUnitSheet(u, true);
  }

  async function doMove(x, y) {
    const B = UI.battle;
    const s = B.s;
    const u = s.byId[B.sel];
    if (!E.beginActivation(s, u.uid)) return;
    if (!E.moveUnit(s, u.uid, x, y)) return;
    await play();
    B.mode = 'unit';
    renderBattle();
  }

  async function doAction() {
    const B = UI.battle;
    const s = B.s;
    const u = s.byId[B.sel];
    if (!u || !B.target || B.busy) return;
    if (!E.beginActivation(s, u.uid) || !E.performAction(s, u.uid, B.target)) {
      toast('That action is not possible from here.');
      B.mode = 'unit';
      renderBattle();
      return;
    }
    B.target = null;
    await play();
    if (s.over) return battleOver();
    if (!u.alive) {
      B.mode = 'idle';
      B.sel = null;
      renderBattle();
      return;
    }
    const A = activationOf(u);
    if (A && !A.moved && u.move > 0 && !u.traits.has('immobile') && E.reachable(s, u).size > 1) {
      B.mode = 'unit';
      renderBattle();
    } else enterFacing();
  }

  async function doLoot() {
    const B = UI.battle;
    const s = B.s;
    const u = s.byId[B.sel];
    if (!u || B.busy) return;
    if (!E.beginActivation(s, u.uid) || !E.takeLoot(s, u.uid)) return;
    await play();
    renderBattle();
    if (s.over) return battleOver();
    const A = activationOf(u);
    if (A && !A.moved && u.move > 0 && !u.traits.has('immobile') && E.reachable(s, u).size > 1) {
      B.mode = 'unit';
      renderBattle();
    } else enterFacing();
  }

  function enterFacing() {
    const B = UI.battle;
    const s = B.s;
    const u = s.byId[B.sel];
    if (!u) return;
    if (u.facing < 0) {
      finishUnit(-1);
      return;
    }
    B.mode = 'facing';
    B.facing = AI.smartFacing(s, u);
    renderBattle();
  }

  async function finishUnit(d, silent) {
    const B = UI.battle;
    const s = B.s;
    if (!s.act) {
      E.beginActivation(s, B.sel);
    }
    E.finishActivation(s, d);
    await play();
    B.mode = 'idle';
    B.sel = null;
    B.target = null;
    if (!silent) renderBattle();
  }

  async function endTurn() {
    const B = UI.battle;
    if (!B || B.busy || B.s.side !== 'P') return;
    const s = B.s;
    const ready = usefulReady(s).filter((u) => !(s.act && s.act.uid === u.uid));
    if (ready.length && !B.confirmEnd) {
      B.confirmEnd = true;
      toast(`${ready.length} unit${ready.length > 1 ? 's' : ''} can still act. Tap again to end your turn.`);
      renderBattle();
      return;
    }
    B.confirmEnd = false;
    if (s.act) {
      const cur = s.byId[s.act.uid];
      if (s.act.moved || s.act.acted) E.finishActivation(s, AI.smartFacing(s, cur));
      else E.cancelActivation(s);
    }
    B.mode = 'idle';
    B.sel = null;
    B.target = null;
    E.endTurn(s);
    renderBattle();
    await play();
    if (s.over) return battleOver();
    await enemyTurn();
  }

  async function enemyTurn() {
    const B = UI.battle;
    const s = B.s;
    const b = UI.board;
    B.busy = true;
    showBanner('Enemy Turn', true);
    sfx('enemyturn');
    renderBattle();
    await sleep(UI.prefs.fast ? 350 : 700);
    let guard = 0;
    while (!s.over && s.side === 'E' && guard++ < 40) {
      const plan = AI.chooseActivation(s, 'E', { stance: B.enc.stance, temp: B.temp });
      if (!plan) break;
      const u = s.byId[plan.uid];
      if (plan.kind === 'turn') {
        E.beginActivation(s, plan.uid);
        E.finishActivation(s, plan.facing);
      } else {
        b.ov = { select: [u.x, u.y] };
        await sleep(UI.prefs.fast ? 120 : 300);
        if (!AI.executePlan(s, plan, { stance: B.enc.stance })) u.activated = true;
      }
      b.ov = {};
      B.busy = true;
      const ev = E.drainEvents(s);
      await b.playEvents(ev, s);
      b.syncFromState(s);
    }
    if (!s.over) {
      E.endTurn(s);
      await b.playEvents(E.drainEvents(s), s);
      b.syncFromState(s);
    }
    B.busy = false;
    if (s.over) return battleOver();
    showBanner('Your Turn');
    sfx('turn');
    renderBattle();
  }

  async function battleOver() {
    const B = UI.battle;
    if (!B || B.ending) return;
    B.ending = true;
    B.busy = true;
    const s = B.s;
    const won = s.winner === 'P';
    const endEv = s.events.find((e) => e.t === 'end');
    showBanner(won ? 'Victory' : 'Defeat', !won);
    sfx(won ? 'victory' : 'defeat');
    renderBattle();
    await sleep(1500);
    const res = R.finishBattle(UI.run, s, B.dep);
    UI.battle = null;
    if (won || UI.run.over) {
      route();
      return;
    }
    const reason = s.timeout
      ? 'The turn limit ran out and the enemy held stronger.'
      : endEv && endEv.forfeit
        ? 'You sounded the retreat.'
        : endEv && endEv.surrender
          ? 'None of your remaining units could fight.'
          : 'Your army was broken.';
    openSheet(
      `${sheetHead('Defeat')}
      <p>${reason} You lose a Banner: <b>${res.bannersLeft}</b> left.</p>
      <p class="muted">The enemy holds the field. Re-plan your army and try again: study their reach, flank their shields, and bring the right counters.</p>
      <div class="actions"><button class="btn primary" id="dfRetry">${ic('swords')} Re-plan and fight</button></div>`,
      (sh) => {
        $('#dfRetry', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          warRoom();
        };
      }
    );
    UI.onSheetClose = () => warRoom();
  }

  // ------------------------------------------------------------ rewards

  function spoilCard(sp, i, taken) {
    if (sp.type === 'recruit') {
      const T = UNITS[sp.unit];
      return `<button class="card" data-spoil="${i}" ${taken ? 'disabled' : ''}>
        <div class="card-head"><canvas class="portrait" data-p="${sp.unit}:P"></canvas>
        <div><div class="kind">Recruit · ${T.rarity}</div><div class="title">${T.name} <span class="stars">${stars(sp.rank)}</span></div></div></div>
        <div class="desc">${esc(T.desc)}</div><div class="small muted">${T.cost} CP to deploy</div></button>`;
    }
    if (sp.type === 'talent') {
      const t = TALENTS[sp.talent];
      return `<button class="card" data-spoil="${i}" ${taken ? 'disabled' : ''}>
        <div class="kind">${ic('scroll')} Talent</div><div class="title">${esc(t.name)}</div>
        <div class="desc">${esc(t.desc)} Teach it to one unit.</div></button>`;
    }
    if (sp.type === 'promote') {
      return `<button class="card" data-spoil="${i}" ${taken ? 'disabled' : ''}>
        <div class="kind">${ic('up')} Promotion</div><div class="title">Field Promotion</div>
        <div class="desc">Raise one unit a rank for free: +20% HP and power per rank, and a signature ability at Rank III.</div></button>`;
    }
    return `<button class="card" data-spoil="${i}" ${taken ? 'disabled' : ''}><div class="kind">${ic('gold')} Gold</div><div class="title">${sp.amount} gold</div></button>`;
  }

  function relicCard(id, attrs) {
    const r = RELICS[id];
    return `<button class="card" ${attrs || ''}><div class="kind">${ic('gem')} Relic · ${r.tier}</div><div class="title">${esc(r.name)}</div><div class="desc">${esc(r.desc)}</div></button>`;
  }

  function rewardScreen() {
    const run = UI.run;
    const p = run.pending;
    const bossDone = !p.bossRelics || p.bossRelicTaken;
    const v = showView(
      `<div class="wrap">
        <div class="reward-head"><p class="eyebrow">${p.kind === 'boss' ? 'The champion falls' : 'The field is yours'}</p><h2>Victory</h2></div>
        <div class="panel loot">
          <span class="res gold">${ic('gold')} +${p.gold} gold</span>
          ${p.eff ? `<span class="res gold">${ic('command')} +${p.eff} gold for ${p.unspent} unspent Command</span>` : '<span class="small muted">No unspent Command Points this time.</span>'}
          <span class="res">${ic('gold')} ${run.gold} total</span>
        </div>
        ${p.fallen && p.fallen.length ? `<p class="small" style="color:var(--red)">${esc(p.fallen.join(', '))} fell in battle${R.hasRelic(run, 'field_kit') ? ', but your surgeon patched them up.' : '. Wounded units start their next battle at half HP unless they sit one out or rest.'}</p>` : ''}
        ${p.kind === 'boss' ? '<p class="small" style="color:var(--green)">Your army recovers: all wounds healed and a Banner restored.</p>' : ''}
        ${p.objectives && p.objectives.length ? `<div class="panel objectives">${p.objectives
          .map((o) => `<div class="obj bonus ${o.done ? 'done' : 'failed'}">${ic(o.done ? 'check' : 'close')}<span>${esc(o.text)}${o.done ? ` <span class="reward">${esc(o.got)}</span>` : ''}</span></div>`)
          .join('')}</div>` : ''}
        ${p.prisoner && R.unitById(run, p.prisoner) ? `<p class="small" style="color:var(--green)">The prisoner ${esc(R.unitById(run, p.prisoner).name)} the ${UNITS[R.unitById(run, p.prisoner).type].name} is free and joins your army.</p>` : ''}
        ${p.prisonerGold ? `<p class="small muted">The freed prisoner could not join a full army, but leaves you ${p.prisonerGold} gold in thanks.</p>` : ''}
        ${p.relicGained ? `<div><div class="eyebrow">Relic claimed</div><div class="cards">${relicCard(p.relicGained, 'disabled style="opacity:1"')}</div></div>` : ''}
        ${p.lootRelic ? `<div><div class="eyebrow">From the relic cache</div><div class="cards">${relicCard(p.lootRelic, 'disabled style="opacity:1"')}</div></div>` : ''}
        ${p.tome && p.tome.length ? `<div><div class="eyebrow">${p.tomeTaken ? 'The tome is read' : 'The Lost Tome: choose a talent to teach'}</div>
          <div class="cards">${p.tome
            .map((t, i) => `<button class="card" data-tome="${i}" ${p.tomeTaken ? 'disabled' : ''}><div class="kind">${ic('scroll')} Talent</div><div class="title">${esc(TALENTS[t].name)}</div><div class="desc">${esc(TALENTS[t].desc)}</div></button>`)
            .join('')}</div></div>` : ''}
        ${p.bossRelics && p.bossRelics.length ? `<div><div class="eyebrow">${p.bossRelicTaken ? 'Boss relic claimed' : 'Choose a boss relic'}</div><div class="cards">${p.bossRelics.map((id) => relicCard(id, `data-boss="${id}" ${p.bossRelicTaken ? 'disabled' : ''}`)).join('')}</div></div>` : ''}
        <div><div class="eyebrow">${p.spoilTaken ? 'Spoils claimed' : 'Choose your spoils'}</div>
          <div class="cards">${p.spoils.map((sp, i) => spoilCard(sp, i, p.spoilTaken)).join('')}</div></div>
        <div class="row end">
          ${!p.spoilTaken ? `<button class="btn" id="rwSkip">Skip spoils (+10 gold)</button>` : ''}
          ${p.tome && !p.tomeTaken ? `<button class="btn" id="rwTomeSkip">Skip the tome (+10 gold)</button>` : ''}
          <button class="btn primary" id="rwGo" ${p.spoilTaken && bossDone && (!p.tome || p.tomeTaken) ? '' : 'disabled'}>${p.kind === 'boss' && run.act >= 3 ? 'Claim victory' : 'Continue'}</button>
        </div>
      </div>`
    );
    for (const b of $$('[data-boss]', v))
      b.onclick = () => {
        if (R.takeBossRelic(run, b.dataset.boss)) {
          sfx('coin');
          rewardScreen();
        }
      };
    for (const b of $$('[data-spoil]', v))
      b.onclick = async () => {
        const i = +b.dataset.spoil;
        const sp = p.spoils[i];
        let rid = null;
        if (sp.type === 'recruit' && run.roster.length >= R.MAX_ROSTER) {
          toast('Your army is full. Dismiss a unit in the Army screen first.');
          return;
        }
        if (sp.type === 'talent') {
          rid = await pickUnit('Teach ' + TALENTS[sp.talent].name, esc(TALENTS[sp.talent].desc), (u) => R.canLearn(u, sp.talent));
          if (!rid) return;
        }
        if (sp.type === 'promote') {
          rid = await pickUnit('Field Promotion', 'Choose a unit to raise one rank.', (u) => u.rank < 3);
          if (!rid) return;
        }
        if (R.takeSpoil(run, i, rid)) {
          sfx('coin');
          if (sp.type === 'recruit') toast(`${run.roster[run.roster.length - 1].name} the ${UNITS[sp.unit].name} joins your army.`);
          rewardScreen();
        }
      };
    if ($('#rwSkip', v))
      $('#rwSkip', v).onclick = () => {
        R.skipSpoils(run);
        rewardScreen();
      };
    for (const b of $$('[data-tome]', v))
      b.onclick = async () => {
        const t = p.tome[+b.dataset.tome];
        const rid = await pickUnit('Teach ' + TALENTS[t].name, esc(TALENTS[t].desc), (u) => R.canLearn(u, t));
        if (rid && R.takeTome(run, +b.dataset.tome, rid)) {
          sfx('coin');
          rewardScreen();
        }
      };
    if ($('#rwTomeSkip', v))
      $('#rwTomeSkip', v).onclick = () => {
        R.skipTome(run);
        rewardScreen();
      };
    $('#rwGo', v).onclick = () => {
      const wasBoss = p.kind === 'boss';
      R.completeNode(run);
      if (wasBoss && !run.over) toast(`${ACTS[run.act].short}: ${ACTS[run.act].name}`);
      route();
    };
  }

  // ------------------------------------------------------------ shop

  function shopScreen() {
    const run = UI.run;
    const p = run.pending;
    const card = (it, i) => {
      const can = R.canBuy(run, it);
      const price = `<div class="price">${ic('gold')} ${it.sold ? 'Sold' : it.price}</div>`;
      const dis = `data-buy="${i}" ${can ? '' : 'disabled'}`;
      if (it.kind === 'recruit') {
        const T = UNITS[it.unit];
        return `<button class="card" ${dis}><div class="card-head"><canvas class="portrait" data-p="${it.unit}:P"></canvas>
          <div><div class="kind">Recruit · ${T.rarity}</div><div class="title">${T.name} <span class="stars">${stars(it.rank)}</span></div></div></div>
          <div class="desc">${esc(T.desc)}</div>${price}</button>`;
      }
      if (it.kind === 'talent')
        return `<button class="card" ${dis}><div class="kind">${ic('scroll')} Talent</div><div class="title">${esc(TALENTS[it.talent].name)}</div><div class="desc">${esc(TALENTS[it.talent].desc)}</div>${price}</button>`;
      if (it.kind === 'relic')
        return `<button class="card" ${dis}><div class="kind">${ic('gem')} Relic · ${RELICS[it.relic].tier}</div><div class="title">${esc(RELICS[it.relic].name)}</div><div class="desc">${esc(RELICS[it.relic].desc)}</div>${price}</button>`;
      if (it.kind === 'heal')
        return `<button class="card" ${dis}><div class="kind">${ic('heart')} Service</div><div class="title">Field Surgeon</div><div class="desc">Heal every wounded unit.</div>${price}</button>`;
      return `<button class="card" ${dis}><div class="kind">${ic('banner')} Service</div><div class="title">New Standard</div><div class="desc">Restore one Banner.</div>${price}</button>`;
    };
    const section = (title, kinds) => {
      const items = p.stock.map((it, i) => [it, i]).filter(([it]) => kinds.includes(it.kind));
      return items.length ? `<div><div class="eyebrow">${title}</div><div class="cards">${items.map(([it, i]) => card(it, i)).join('')}</div></div>` : '';
    };
    const v = showView(
      `<div class="wrap">
        <div class="row"><div class="grow"><p class="eyebrow">Merchant</p><h2>The Wandering Market</h2></div></div>
        <div class="row">${resbar(run)}<span class="grow"></span><button class="btn" id="shArmy">${ic('army')} Army</button></div>
        ${section('Recruits', ['recruit'])}
        ${section('Talents', ['talent'])}
        ${section('Relics', ['relic'])}
        ${section('Services', ['heal', 'banner'])}
        <div class="row end"><button class="btn primary" id="shLeave">Leave the market</button></div>
      </div>`
    );
    for (const b of $$('[data-buy]', v))
      b.onclick = async () => {
        const i = +b.dataset.buy;
        const it = p.stock[i];
        let rid = null;
        if (it.kind === 'talent') {
          rid = await pickUnit('Teach ' + TALENTS[it.talent].name, esc(TALENTS[it.talent].desc), (u) => R.canLearn(u, it.talent));
          if (!rid) return;
        }
        if (R.buy(run, i, rid)) {
          sfx('coin');
          shopScreen();
        }
      };
    $('#shArmy', v).onclick = () => armySheet(() => shopScreen());
    $('#shLeave', v).onclick = () => {
      R.completeNode(run);
      route();
    };
  }

  // ------------------------------------------------------------ rest, treasure, event

  function restScreen() {
    const run = UI.run;
    const p = run.pending;
    const wounded = run.roster.filter((u) => u.wounded).length;
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">Campfire</p><h2>A night by the fire</h2></div>
        <p class="muted">${wounded ? `${wounded} of your units are wounded.` : 'Your soldiers are in good health.'} Banners: ${run.banners}/${run.maxBanners}.</p>
        ${p.done ? `<p class="hint">${p.done === 'rest' ? 'Your army rests. Wounds are healed and spirits rise.' : 'Training pays off.'}</p>` : `<div class="cards">
          <button class="card" id="rsRest"><div class="kind">${ic('fire')} Rest</div><div class="title">Rest</div><div class="desc">Heal all wounds and restore 1 Banner.</div></button>
          <button class="card" id="rsTrain" ${run.roster.some((u) => u.rank < 3) ? '' : 'disabled'}><div class="kind">${ic('up')} Train</div><div class="title">Train</div><div class="desc">Promote one unit by a rank for free.</div></button>
        </div>`}
        <div class="row end"><button class="btn" id="rsArmy">${ic('army')} Army</button><button class="btn primary" id="rsGo" ${p.done ? '' : 'disabled'}>Break camp</button></div>
      </div>`
    );
    if ($('#rsRest', v))
      $('#rsRest', v).onclick = () => {
        R.rest(run, 'rest');
        sfx('heal');
        restScreen();
      };
    if ($('#rsTrain', v))
      $('#rsTrain', v).onclick = async () => {
        const rid = await pickUnit('Train', 'Choose a unit to promote.', (u) => u.rank < 3);
        if (rid && R.rest(run, 'train', rid)) {
          sfx('coin');
          restScreen();
        }
      };
    $('#rsArmy', v).onclick = () => armySheet(() => restScreen());
    $('#rsGo', v).onclick = () => {
      R.completeNode(run);
      route();
    };
  }

  function treasureScreen() {
    const run = UI.run;
    const p = run.pending;
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">Treasure</p><h2>A forgotten cache</h2></div>
        <div class="cards">${p.relic ? relicCard(p.relic, 'disabled style="opacity:1"') : ''}
          <div class="card"><div class="kind">${ic('gold')} Coin</div><div class="title">${p.gold} gold</div></div></div>
        <div class="row end">${p.taken ? '' : `<button class="btn primary" id="trTake">${ic('chest')} Take it all</button>`}
          <button class="btn ${p.taken ? 'primary' : ''}" id="trGo" ${p.taken ? '' : 'disabled'}>Continue</button></div>
      </div>`
    );
    if ($('#trTake', v))
      $('#trTake', v).onclick = () => {
        R.takeTreasure(run);
        sfx('coin');
        treasureScreen();
      };
    $('#trGo', v).onclick = () => {
      R.completeNode(run);
      route();
    };
  }

  function eventScreen() {
    const run = UI.run;
    const p = run.pending;
    const ev = R.eventDef(p.eventId);
    const choices = R.eventChoices(run);
    const v = showView(
      `<div class="wrap">
        <div class="row">${resbar(run)}</div>
        <div class="parch-card">
          <p class="eyebrow" style="color:#7a5a2c">On the road</p>
          <h2>${esc(ev.title)}</h2>
          <p>${esc(ev.text)}</p>
          ${p.result ? `<p class="result">${esc(p.result)}</p>` : choices
            .map(
              (c) => `<button class="choice" data-choice="${esc(c.id)}" ${c.enabled ? '' : 'disabled'}><b>${esc(c.label)}</b><span>${esc(c.detail)}</span></button>`
            )
            .join('')}
        </div>
        ${p.result ? `<div class="row end"><button class="btn primary" id="evGo">Continue</button></div>` : ''}
      </div>`
    );
    for (const b of $$('[data-choice]', v))
      b.onclick = async () => {
        const c = choices.find((x) => x.id === b.dataset.choice);
        let rid = null;
        if (c.pick) {
          const filter = c.pick.talent
            ? (u) => R.canLearn(u, c.pick.talent)
            : c.pick.filter === 'promote'
              ? (u) => u.rank < 3
              : (u) => ['common', 'uncommon'].includes(UNITS[u.type].rarity);
          rid = await pickUnit(c.label, esc(c.detail), filter);
          if (!rid) return;
        }
        const out = R.chooseEvent(run, c.id, rid);
        if (out == null) {
          toast('That choice is not available.');
          return;
        }
        sfx('click');
        if (run.pending && run.pending.type === 'battle') {
          toast(out);
          route();
          return;
        }
        eventScreen();
      };
    if ($('#evGo', v))
      $('#evGo', v).onclick = () => {
        R.completeNode(run);
        route();
      };
  }

  // ------------------------------------------------------------ end of run

  function endScreen() {
    const run = UI.run;
    const st = run.stats;
    R.clearSave();
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">${run.won ? 'The Spire is silent' : 'Your banners have fallen'}</p>
        <h2>${run.won ? 'Campaign won' : 'Campaign lost'}</h2></div>
        <p class="muted">${run.won ? 'The Ashen Tyrant is slain and the arena bows to your warband.' : `Your march ended in ${ACTS[run.act].short}, ${esc(ACTS[run.act].name)}.`}</p>
        <div class="end-stats">
          <div class="stat"><b>${st.battles}</b><span>Battles won</span></div>
          <div class="stat"><b>${st.elites}</b><span>Elites</span></div>
          <div class="stat"><b>${st.bosses}</b><span>Bosses</span></div>
          <div class="stat"><b>${st.kills}</b><span>Enemies slain</span></div>
          <div class="stat"><b>${st.gold}</b><span>Gold earned</span></div>
          <div class="stat"><b>${st.efficiency}</b><span>Efficiency gold</span></div>
        </div>
        <div class="roster">${run.roster
          .map((u) => `<div class="rcard"><canvas data-p="${u.type}:P"></canvas><span class="nm">${esc(u.name)}</span><span class="ty">${UNITS[u.type].name} <span class="stars">${stars(u.rank)}</span></span></div>`)
          .join('')}</div>
        <div class="row end"><button class="btn primary" id="enNew">${ic('swords')} New campaign</button><button class="btn" id="enTitle">Title</button></div>
      </div>`
    );
    $('#enNew', v).onclick = () => {
      UI.run = null;
      newCampaign();
    };
    $('#enTitle', v).onclick = () => {
      UI.run = null;
      title();
    };
  }

  // ------------------------------------------------------------ help and codex

  function helpSheet() {
    openSheet(
      `${sheetHead('How to play')}
      <div class="help">
        <h4>The campaign</h4>
        <p>March through three acts on a branching map. Each act ends with a boss. Banners are your lives: lose a battle and you lose a Banner, then try the same fight again with a new plan.</p>
        <h4>The war room</h4>
        <p>Before every battle you see the whole enemy army and where it stands. Spend Command Points to deploy units into your blue zone. Every point you leave unspent pays 4 gold if you win, so a sharp counter-pick also funds your next promotion.</p>
        <h4>Your turn</h4>
        <ul>
          <li>Each ready unit (glowing ring) can move once and use its action once, in either order.</li>
          <li>Then choose which way it faces. Its back is its weak side.</li>
          <li>After acting, a unit recovers for turns equal to its Recover stat. Moving without acting costs half.</li>
        </ul>
        <h4>Facing, block and armor</h4>
        <ul>
          <li>Physical attacks can be blocked: full Block from the front, half from the side, never from behind.</li>
          <li>Armor reduces physical damage. Magic ignores both armor and block.</li>
          <li>Fireballs, lightning and dragon fire hit your own units too.</li>
        </ul>
        <h4>Missions</h4>
        <ul>
          <li>Each battle has a goal: rout the enemy, burn their War Banner, break a prison cage, assassinate a Commander, hold a shrine, or survive. Routing the enemy always wins.</li>
          <li>Bonus goals pay extra. Loot on the field (a war chest, a tome, a relic) goes to the unit that stands on it and spends its action. Specters guard the best loot and take half damage from physical attacks.</li>
          <li>Some missions feature a unit that sat out your last battle. Field it and win, and it earns a free promotion.</li>
        </ul>
        <h4>Growing your army</h4>
        <p>After each victory, choose a new recruit, a talent for one unit, or a promotion. Spend gold in the Army screen to promote units to Rank II and III. Units that fall are wounded and start their next battle at half HP unless they sit one out or rest.</p>
        <h4>Controls</h4>
        <ul>
          <li>Tap a unit, tap a blue tile to move, tap a red enemy to aim, then tap again to confirm.</li>
          <li>Long-press any unit for its details. Pinch, drag, or use + and − to zoom.</li>
          <li>The eye button shows every tile the enemy can strike next turn.</li>
          <li>Battles play best with your phone turned sideways.</li>
        </ul>
      </div>
      <div class="actions"><button class="btn primary" data-close>Got it</button></div>`
    );
  }

  function codexSheet() {
    const types = AG.Data.RECRUITABLE;
    openSheet(
      `${sheetHead('Units', 'Every unit you can recruit, and every unit you will face.')}
      <div class="codex-grid">${types
        .map((t) => {
          const u = R.unitStats({ type: t, rank: 1 }, [], 'P');
          const T = UNITS[t];
          return `<div class="card"><div class="card-head"><canvas class="portrait" data-p="${t}:P"></canvas>
            <div><div class="kind">${T.rarity} · ${T.cost} CP</div><div class="title">${T.name}</div></div></div>
            ${statsHTML(u)}<p class="ability"><b>${esc(T.act.name)}.</b> ${esc(abilityText(u))}</p>
            <p class="small muted">${esc(T.tip)}</p></div>`;
        })
        .join('')}</div>`
    );
  }

  // ------------------------------------------------------------ router

  function route() {
    const run = UI.run;
    if (!run) return title();
    if (run.over) return endScreen();
    const p = run.pending;
    if (!p) return mapScreen();
    switch (p.type) {
      case 'battle':
        return warRoom();
      case 'reward':
        return rewardScreen();
      case 'shop':
        return shopScreen();
      case 'rest':
        return restScreen();
      case 'event':
        return eventScreen();
      case 'treasure':
        return treasureScreen();
    }
    return mapScreen();
  }

  function init() {
    $('#modal').addEventListener('click', (e) => {
      if (e.target.id === 'modal') closeSheet();
    });
    root.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !$('#modal').hidden) closeSheet();
    });
    root.addEventListener('resize', () => {
      updateRotateHint();
      if (!$('#view').hidden && UI.mapWide != null && $('.map-screen') && isWide() !== UI.mapWide) mapScreen();
    });
    const unlock = () => AG.Audio && AG.Audio.unlock();
    root.addEventListener('pointerdown', unlock, { once: true });
    $('#rotateHint').addEventListener('click', () => {
      UI.prefs.hideRotate = true;
      savePrefs();
      updateRotateHint();
    });
  }

  UI.init = init;
  UI.route = route;
  UI.title = title;
  UI.toast = toast;
  AG.UI = UI;
})(window);
