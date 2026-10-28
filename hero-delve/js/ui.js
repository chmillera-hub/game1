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

  const UI = (AG.UI = { p: null, board: null, B: null, prefs: { speed: 1, autoPause: true } });
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
        .map((h) => `<button class="delve-mini" data-hero="${h.id}" ${owed(h) ? 'data-choose' : ''}><canvas data-p="${h.type}:P"></canvas><b>${esc(h.name)}</b><small>Lv ${h.lv} ${esc(UNITS[h.type].name)}</small>${xpMini(h)}${owed(h) ? `<span class="pts">+${owed(h)}</span>` : ''}</button>`)
        .join('')}</div>
      <div class="actions delve-main-actions">
        ${run
          ? `<button class="btn primary" id="tContinue">${ic('play')} Continue · ${esc(DV.FLOOR_DEFS[run.floor].name)}</button>
             <button class="btn" id="tAbandon">${ic('flag')} Abandon this delve</button>`
          : `<button class="btn primary" id="tEnter">${ic('swords')} Enter the tower</button>`}
        <button class="btn" id="tParty">${ic('army')} Party &amp; gear</button>
        <button class="btn" id="tTrainer" ${(p.prestige || 0) > 0 ? 'data-choose' : ''}>${ic('crown')} Prestige Trainer · ${p.prestige || 0} point${p.prestige === 1 ? '' : 's'}</button>
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
    on('tTrainer', () => trainer());
    on('tHelp', () => help());
  }

  // ---- the Prestige Trainer: prestige points (XP past the top level) buy skills and gear.
  function trainer() {
    const p = UI.p;
    const items = DV.stock(p);
    const pts = p.prestige || 0;
    const v = showView(`<div class="wrap">
      <div class="row"><div class="grow"><p class="eyebrow">Town</p><h2>Prestige Trainer</h2></div>
        <button class="btn" id="trBack">${ic('undo')} Town</button></div>
      <p class="muted">Heroes at Level ${DV.MAX_LV} earn a prestige point for the party every ${DV.PRESTIGE_XP} XP instead of a level. Spend them here on skills and gear; new stock comes in after every floor you clear.</p>
      <div class="row"><b class="pts-big">${pts}</b><span class="grow muted">prestige point${pts === 1 ? '' : 's'}</span>
        <button class="btn" id="trRestock" ${pts >= 1 ? '' : 'disabled'}>${ic('rotate')} New stock · 1 point</button></div>
      <div class="picks">${items.length ? items
        .map((x, i) => {
          const d = DV.itemDef(x);
          const price = DV.priceOf(d);
          const users = DV.heroes(p).filter((h) => D.eligible(h.type, d)).map((h) => h.name);
          return `<div class="pick ${d.rarity === 'legendary' ? 'legend' : ''}"><span class="pk-head"><b>${esc(d.name)}</b> <span class="chip">${x.kind}</span></span>
            <span class="pk-desc">${esc(d.desc)}</span>
            <span class="small muted">${users.length ? 'For ' + esc(users.join(', ')) : 'Nobody in your party can use this'}</span>
            <button class="btn ${pts >= price ? 'primary' : ''}" data-buy="${i}" ${pts >= price ? '' : 'disabled'}>${ic('crown')} Buy · ${price}</button></div>`;
        })
        .join('') : '<p class="muted">Sold out: new stock after the next floor you clear.</p>'}</div>
    </div>`);
    $('#trBack', v).onclick = title;
    $('#trRestock', v).onclick = () => {
      if (DV.buyRestock(p)) trainer();
    };
    for (const b of $$('[data-buy]', v))
      b.onclick = () => {
        const it = DV.buy(p, +b.dataset.buy);
        if (!it) return;
        sfx('coin');
        toast(`${DV.itemDef(it).name} is in your stash.`);
        trainer();
      };
  }

  // Skill points waiting on you (a hero on Auto-spend saves its own for a talent to come).
  function owed(h) {
    return h.auto ? 0 : DV.pointsLeft(h);
  }

  // Items found on this delve that nobody holds, this hero could use, and you have not yet
  // looked at on its sheet.
  function newFor(h) {
    const p = UI.p;
    if (!p.run) return [];
    const seen = new Set(p.run.seen || []);
    return p.run.loot
      .map((uid) => DV.itemByUid(p, uid))
      .filter((it) => it && !seen.has(it.uid) && !DV.holderOf(p, it.uid) && D.eligible(h.type, DV.itemDef(it)));
  }

  // Everything waiting on you across the party: skill points and new finds.
  function pending() {
    const heroes = DV.heroes(UI.p);
    const points = heroes.reduce((t, h) => t + owed(h), 0);
    const items = new Set(heroes.flatMap((h) => newFor(h).map((it) => it.uid))).size;
    return { points, items, total: points + items };
  }

  function pendingBadges(h) {
    const pts = owed(h);
    const n = newFor(h).length;
    return `${pts ? `<span class="pts">+${pts}</span>` : ''}${n ? `<span class="pts newloot">${n} new</span>` : ''}`;
  }

  function xpMini(h) {
    // At the top level the bar fills toward the next prestige point instead, in gold.
    const top = h.lv >= DV.MAX_LV;
    const f = top ? h.xp / DV.PRESTIGE_XP : h.xp / DV.xpToNext(h.lv);
    return `<span class="xpmini ${top ? 'prestige' : ''}" title="${top ? 'Prestige' : 'XP'}"><i style="width:${Math.round(Math.min(1, f) * 100)}%"></i></span>`;
  }

  function help() {
    openSheet(`${sheetHead('How it works')}
      <ul class="tips">
        <li><b>Your party</b>: four heroes of any class, plus your Cleric, who always comes. They start at Level 1 and grow as they fight: every monster slain gives the whole party XP. The top level is ${DV.MAX_LV}, about where a party stands as it starts down to Level 5.</li>
        <li><b>Levels</b>: each level makes a hero tougher and stronger and gives a <b>skill point</b> for class talents (from Level 2, the stronger ones from Level 5) or training (Vitality, Might). Level 3 opens a second gear slot, Level 4 the class's second ability, Level 5 a second skill slot, Level 7 its mastery, Level 8 a third gear slot, Level 9 a third skill slot.</li>
        <li><b>Upgrading</b>: when someone levels up or loot drops, their frame glows with a <b>+1</b> (skill points) or <b>new</b> (items they could use), and a ${ic('star')} appears at the top. After a fight the game pauses for you (you can turn that off in the menu): tap the hero, spend the points, put the loot on, then ${ic('play')} to carry on. Turn a hero's <b>Auto</b> on and it does this itself.</li>
        <li><b>Prestige</b>: a hero at Level ${DV.MAX_LV} earns a prestige point for the party every ${DV.PRESTIGE_XP} XP instead of a level. Spend them at the <b>Prestige Trainer</b> in town on skills and gear.</li>
        <li><b>Loot</b>: packs you wipe out drop skills and gear, better the deeper you go. A floor's Champion always drops something good; the Countess a legendary. Changes made mid-floor take hold once the fight in hand is over.</li>
        <li><b>Buildings</b>: some packs keep a building in their room. A <b>crypt, den or portal</b> sends out more monsters every ${E.SPAWN_EVERY} rounds while your party is near, until it is broken; what it makes is worth no XP and drops nothing, so break it (the floor is not clear until you do). A <b>war totem</b> whips the monsters near it into a frenzy. Siege units, the Trebuchet above all, hit buildings hard.</li>
        <li><b>Rounds</b>: every unit gets one turn a round, the fastest first, whichever side. A unit cooling down still gets its turn and may move, but not act; its cooldown drops by one each round.</li>
        <li><b>Fatigue</b>: from round ${E.FATIGUE_AT} of any fight, every unit on both sides loses a share of its own health as its turn comes: 3% of its HP, then 6%, 9% and so on. Nothing lasts for ever, and a party of tanks and healers can win by outlasting what it cannot kill.</li>
        <li><b>Levels on health bars</b>: grey is well below your party, white about even, amber a level above, <b>red two or more above</b>. Your party leaves red packs for later while there is anything else to fight, and walks round them where it can. Each floor has a <b>Champion</b>, a crowned monster far tougher than the rest.</li>
        <li><b>Watching</b>: pause any time, speed it up, or tap something. Tap a monster and Priority to send everyone after it (red or not); tap a floor tile to send the party there; tap a hero to rally round them or open their kit. <b>Retreat</b> runs for the way in.</li>
        <li><b>No lost floors</b>: a hero who falls gets up at the way in once the fight is over (win it, or get away). Run far enough from a pack and it gives up the chase, goes home, heals and sleeps; the ones you killed stay dead. If the whole party falls, it gets up at the way in and the monsters it was fighting heal. You never lose XP or items: a strong pack just takes longer.</li>
        <li><b>Floors</b>: clear every monster on a floor and the party takes the stairs down. Level 5 holds the Countess: slay her to beat the tower.</li>
      </ul>
      <div class="actions"><button class="btn primary" data-close>${ic('check')} Got it</button></div>`);
  }

  // ------------------------------------------------------------ party and kit

  function partyScreen(stairs) {
    const p = UI.p;
    const v = showView(`<div class="wrap">
      <div class="row"><div class="grow"><p class="eyebrow">Your party</p><h2>Party &amp; gear</h2></div>
        ${stairs && p.run ? `<button class="btn primary" id="pDown">${ic('play')} Down to ${esc(DV.FLOOR_DEFS[p.run.floor].name)}</button>` : ''}
        <button class="btn" id="pBack">${ic('undo')} Town</button></div>
      <p class="muted">Tap a hero to spend skill points and change their abilities, skills, gear or class. The Cleric always comes.</p>
      <div class="delve-roster">${DV.heroes(p).map((h, i) => heroCard(h, i)).join('')}</div>
      <div class="actions"><button class="btn" id="pAuto">${ic('star')} Fill empty slots</button></div>
      <h3>Stash</h3>
      <div class="delve-stash">${stashList()}</div>
    </div>`);
    $('#pBack', v).onclick = title;
    if ($('#pDown', v)) $('#pDown', v).onclick = () => delve();
    $('#pAuto', v).onclick = () => {
      DV.autoKit(p);
      DV.save(p);
      partyScreen(stairs);
      toast('Every empty slot filled with the best free fit.');
    };
    for (const b of $$('[data-hero]', v)) b.onclick = () => heroSheet(DV.heroes(p).find((h) => h.id === b.dataset.hero), () => partyScreen(stairs));
  }

  function heroCard(h) {
    const p = UI.p;
    const names = (ids, table) => ids.map((id) => (table[id] ? table[id].name : id));
    const kit = [
      ...names(h.talents, TALENTS),
      ...h.skills.map((uid) => DV.itemDef(DV.itemByUid(p, uid))).filter(Boolean).map((d) => d.name),
      ...h.gear.map((uid) => DV.itemDef(DV.itemByUid(p, uid))).filter(Boolean).map((d) => d.name),
    ];
    return `<button class="delve-card" data-hero="${h.id}" ${owed(h) || newFor(h).length ? 'data-choose' : ''}>
      <canvas data-p="${h.type}:P"></canvas>
      <span class="nm"><b>${esc(h.name)}</b> <span class="muted">Lv ${h.lv} ${esc(UNITS[h.type].name)}${h.type === 'cleric' ? ' · always comes' : ''}</span>${owed(h) ? ` <span class="chip good">+${owed(h)} point${owed(h) > 1 ? 's' : ''}</span>` : ''}${newFor(h).length ? ` <span class="chip warn">${newFor(h).length} new item${newFor(h).length > 1 ? 's' : ''}</span>` : ''}${xpMini(h)}</span>
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
    const B = UI.B;
    const inDelve = !!B;
    const pts = DV.pointsLeft(h);
    const sl = DV.slotsOf(h);
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
        const need = DV.talentLevel(id);
        const locked = !on && h.lv < need;
        const can = DV.canLearn(h, id);
        const tag = on ? `<span class="chip good">${ic('check')} learned</span>` : locked ? `<span class="chip">Level ${need}</span>` : `<span class="chip ${can ? 'good' : ''}">${t.cost} point${t.cost > 1 ? 's' : ''}</span>`;
        return `<button class="pick ${on ? 'on' : ''} ${locked ? 'locked' : ''}" data-tal="${id}" ${can ? 'data-choose' : ''} ${locked ? 'disabled' : ''}><span class="pk-head"><b>${esc(t.name)}</b> ${tag}</span><span class="pk-desc">${esc(t.desc)}</span></button>`;
      })
      .join('');
    const training = Object.entries(DV.TRAIN)
      .map(([k, t]) => `<div class="train-row"><span class="grow"><b>${t.name}</b> <span class="muted">${t.desc} a point</span></span>
        <button class="btn icon-only" data-untrain="${k}" ${h.train[k] ? '' : 'disabled'} aria-label="One point back">−</button><b class="train-n">${h.train[k]}</b>
        <button class="btn icon-only" data-train="${k}" ${pts > 0 ? 'data-choose' : 'disabled'} aria-label="Spend a point">+</button></div>`)
      .join('');
    const items = (kind, key) => {
      const list = p.stash.filter((it) => it.kind === kind && D.eligible(h.type, DV.itemDef(it)));
      if (!list.length) return '<p class="small muted">Nothing in the stash this hero can use.</p>';
      return list
        .map((it) => {
          const d = DV.itemDef(it);
          const on = h[key].includes(it.uid);
          const other = !on && DV.holderOf(p, it.uid);
          const isNew = fresh.has(it.uid);
          return `<button class="pick ${on ? 'on' : ''} ${d.rarity === 'legendary' ? 'legend' : ''}" data-item="${key}:${it.uid}"><span class="pk-head"><b>${esc(d.name)}</b>${isNew ? ' <span class="chip warn">new</span>' : ''}${on ? ` <span class="chip good">${ic('check')}</span>` : other ? ` <span class="chip">${esc(other.name)}</span>` : ''}</span><span class="pk-desc">${esc(d.desc)}</span></button>`;
        })
        .join('');
    };
    const nextAt = (f, from) => {
      for (let l = from + 1; l <= DV.MAX_LV; l++) if (f(l) > f(from)) return l;
      return 0;
    };
    const slots = (n, max, f) => {
      const nx = nextAt(f, h.lv);
      return `<span class="lockline">${n}/${max}${nx ? ` · another at Level ${nx}` : ''}</span>`;
    };
    const xpLine = h.lv >= DV.MAX_LV ? `Top level · ${h.xp}/${DV.PRESTIGE_XP} XP to a prestige point` : `${h.xp}/${DV.xpToNext(h.lv)} XP to Level ${h.lv + 1}`;
    // The new finds it could use are shown now: no longer new.
    const fresh = new Set(newFor(h).map((it) => it.uid));
    if (p.run && fresh.size) {
      p.run.seen = (p.run.seen || []).concat([...fresh]);
      DV.save(p);
    }
    const fight = inDelve && B.s.inCombat;
    refreshSheet(
      `${sheetHead(`${esc(h.name)} · Level ${h.lv} ${esc(T.name)}`, `${u.maxHp} HP · ${u.pow} power · ${Math.round(u.armor * 100)}% physical / ${Math.round(u.res * 100)}% magic resistance · Move ${u.move}`)}
      ${fight ? `<div class="hint">${ic('swords')} A fight is on: what you change here takes hold once it is over.</div>` : ''}
      <div class="lo-sec"><canvas class="hero-big" data-p="${h.type}:P"></canvas>
        <div class="xpline">${xpMini(h)}<span class="small muted">${xpLine}</span></div>
        <p class="small">${esc(T.desc)}</p>
        ${h.type !== 'cleric' && !inDelve ? `<button class="btn" id="hClass">${ic('rotate')} Change class</button>` : ''}</div>
      <div class="lo-sec pts-sec ${pts > 0 ? 'has-points' : ''}"><div class="row"><div class="grow"><div class="eyebrow">Skill points</div>
        <b class="pts-big">${pts}</b> <span class="small muted">to spend · one a level${h.auto ? ' · on Auto, the hero spends them (saving for a talent to come) and fills empty slots' : ''}</span></div>
        <label class="toggle small" title="Spends skill points and fills empty slots with new finds"><input type="checkbox" id="hAuto" ${h.auto ? 'checked' : ''}> Auto</label>
        <button class="btn" id="hRespec" ${DV.pointsSpent(h) ? '' : 'disabled'}>${ic('undo')} Reset</button></div></div>
      <div class="lo-sec"><div class="eyebrow">Talents</div><div class="picks">${talents || '<p class="small muted">None for this class.</p>'}</div></div>
      <div class="lo-sec"><div class="eyebrow">Training</div>${training}</div>
      <div class="lo-sec"><div class="eyebrow">Ability</div><div class="picks">${pick(1)}</div></div>
      <div class="lo-sec"><div class="eyebrow">Level 4 ability ${h.lv < 4 ? '<span class="chip">locked</span>' : ''}</div><div class="picks ${h.lv < 4 ? 'dim' : ''}">${pick(2)}</div></div>
      <div class="lo-sec"><div class="eyebrow">Mastery ${h.lv < 8 ? '<span class="chip">Level 8</span>' : ''}</div><div class="pick static ${h.lv >= 8 ? 'on' : 'dim'}"><span class="pk-head"><b>${esc(MASTERY[h.type].name)}</b></span><span class="pk-desc">${esc(MASTERY[h.type].desc)}</span></div></div>
      <div class="lo-sec"><div class="eyebrow">Skills ${slots(h.skills.length, sl.skills, DV.skillSlots)}</div><div class="picks">${items('skill', 'skills')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Gear ${slots(h.gear.length, sl.gear, DV.gearSlots)}</div><div class="picks">${items('gear', 'gear')}</div></div>
      <div class="actions sticky"><button class="btn primary" data-close>${ic('check')} Done</button></div>`,
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
            else if (!DV.learn(p, h, id)) return toast(h.lv < DV.talentLevel(id) ? `Opens at Level ${DV.talentLevel(id)}.` : `Needs ${TALENTS[id].cost} skill point${TALENTS[id].cost > 1 ? 's' : ''}.`);
            sfx('select');
            redraw();
          };
        for (const b of $$('[data-train]', sh))
          b.onclick = () => {
            if (DV.train(p, h, b.dataset.train)) sfx('select');
            redraw();
          };
        for (const b of $$('[data-untrain]', sh))
          b.onclick = () => {
            const k = b.dataset.untrain;
            if (h.train[k] > 0) h.train[k]--;
            redraw();
          };
        $('#hAuto', sh).onchange = (e) => {
          h.auto = e.target.checked;
          if (h.auto) {
            DV.autoSpend(h);
            DV.fillSlots(p, h);
          }
          redraw();
        };
        $('#hRespec', sh).onclick = () => {
          DV.respec(p, h);
          h.auto = false;
          toast('Every point back: spend them as you like.');
          redraw();
        };
        for (const b of $$('[data-item]', sh))
          b.onclick = () => {
            const [key, uid] = b.dataset.item.split(':');
            if (h[key].includes(uid)) h[key] = h[key].filter((x) => x !== uid);
            else {
              if (h[key].length >= sl[key]) return toast(`All ${key === 'gear' ? 'gear' : 'skill'} slots are full: take one off first.`);
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
      `${sheetHead('Change class', `${esc(h.name)} is replaced by a hero of the class you pick, at the same level (Level ${h.lv}), with every skill point to spend again and kit from what is free.`)}
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
    const B = (UI.B = { s, fl, seen: new Uint8Array(fl.w * fl.h), known: new Set(), credited: new Set(), idle: 0, focus: null, paused: true, started: false, sel: null, log: [], loot: [], token: {} });
    $('#view').hidden = true;
    $('#battle').hidden = false;
    const b = ensureBoard();
    b.maxZoom = 4;
    b.clearUnits();
    b.setBoard(fl.w, fl.h, fl.terrain, 'dungeon');
    b.setObjectives([], null);
    DV.reveal(s, fl, B.seen);
    b.setSeen(B.seen);
    b.partyLv = DV.partyLevelIn(s);
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

  // The orders for a side: the monsters press on; the party follows your priority if you set
  // one, else walks on to the next pack (or breaks a stalled fight).
  function aiOpts(B, team) {
    if (team === 'E') return { stance: 'aggressive', temp: 0.4 };
    const mine = B.focus && AI.focusOf(B.s, 'P', B.focus) ? B.focus : null;
    if (B.focus && !mine) B.focus = null;
    return { stance: 'balanced', temp: 0.3, focus: mine || DV.exploreTarget(B.s, B.idle) };
  }

  // Events the board need not play out: the party's slow healing while it walks, and its
  // heroes passing their turns between fights.
  function quiet(s, e) {
    if (e.t === 'heal' && e.why === 'rest') return true;
    if (!s.inCombat && (e.t === 'pass' || e.t === 'sitout')) return true;
    return false;
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
        // Walking between fights goes two and a half times as fast.
        b.speed = UI.prefs.speed * (s.inCombat ? 1 : 2.5);
        b.activeSide = s.side;
        b.readySet = new Set(s.due ? [s.due] : []);
        const team = s.side;
        const opts = aiOpts(B, team);
        const plan = AI.chooseActivation(s, team, opts);
        AI.runPlan(s, plan, opts);
        afterStep(B);
        const ev = E.drainEvents(s);
        B.calmed = false;
        B.idle = DV.idleAfter(s, ev, B.idle);
        if (DV.reveal(s, B.fl, B.seen)) b.setSeen(B.seen);
        logEvents(B, ev);
        await b.playEvents(ev.filter((e) => !quiet(s, e)), s);
        if (UI.B !== B) return;
        b.partyLv = DV.partyLevelIn(s);
        b.syncFromState(s);
        // A fight just ended with level ups or loot waiting: stop for you to see to them.
        if (B.calmed && UI.prefs.autoPause) {
          DV.refreshParty(UI.p, s);
          b.syncFromState(s);
          const pend = pending();
          if (pend.total > (B.ack || 0)) {
            B.ack = pend.total;
            B.paused = true;
            banner(pend.points ? 'Level up!' : 'New loot!');
            sfx('levelup');
          }
        }
        if (!pending().total) B.ack = 0;
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

  // After every turn: XP for the slain (and level ups), loot from packs wiped out, and the
  // heroes brought up to date once a fight is over (new levels, points, kit).
  function afterStep(B) {
    const s = B.s;
    const p = UI.p;
    for (const k of DV.creditKills(p, s, B.credited)) {
      if (UI.board) UI.board.addText(k.x, k.y, `+${k.xp} XP`, '#c9a6ff', { dy: -UI.board.tw * 0.3, max: 1.4 });
      for (const id of k.ups) {
        const h = DV.heroes(p).find((x) => x.id === id);
        pushLog(B, `${ic('star')} <b>${esc(h.name)}</b> reaches Level ${h.lv}!${owed(h) ? ' A skill point to spend.' : ''}`, 'P');
      }
      if (k.ups.length) {
        sfx('levelup');
        toast(k.ups.length > 1 ? 'Level up! Your party grows stronger.' : `Level up! ${DV.heroes(p).find((x) => x.id === k.ups[0]).name} grows stronger.`);
      }
    }
    for (const d of DV.packsDown(s, B.known)) {
      const got = DV.rollLoot(p, AG.derive(p.run.seed, 'loot:' + p.run.floor + ':' + d.pack), p.run.floor, d.kind);
      if (d.champ) pushLog(B, `${ic('crown')} The Champion falls!`, 'P');
      for (const it of got) {
        B.loot.push(it);
        const d2 = DV.itemDef(it);
        pushLog(B, `${ic('chest')} Loot: <b>${esc(d2.name)}</b> (${it.kind})`, 'O');
        toast(`Loot! ${d2.name}`);
        sfx('coin');
      }
    }
    DV.refreshParty(p, s);
  }

  function pushLog(B, html, team) {
    B.log.unshift({ html, team: team || 'O' });
    B.log.length = Math.min(B.log.length, 30);
  }

  function nameOf(u) {
    return u.team === 'P' || u.champ ? `${esc(u.name || UNITS[u.type].name)}` : `${esc(UNITS[u.type].name)}`;
  }

  function logEvents(B, ev) {
    const s = B.s;
    for (const e of ev) {
      if (e.t === 'wake') {
        const us = e.uids.map((id) => s.byId[id]).filter(Boolean);
        const boss = us.find((u) => u.boss);
        const champ = us.find((u) => u.champ);
        const lv = Math.max(...us.map((u) => u.dlv || 1));
        const deadly = DV.danger(lv, DV.partyLevelIn(s)) === 'deadly';
        pushLog(B, boss ? `<b>${esc(UNITS[boss.type].name)}</b> rises to meet you!` : champ ? `${ic('crown')} <b>${esc(champ.name)}</b>, Champion ${esc(UNITS[champ.type].name)}, wakes! (Level ${champ.dlv})` : `A pack wakes (Level ${lv}): ${us.map((u) => esc(UNITS[u.type].name)).join(', ')}`, 'E');
        banner(boss ? UNITS[boss.type].name : champ ? champ.name : deadly ? 'Too strong! Retreat?' : 'Ambush!', true);
        if (deadly && !boss) toast('That pack is well above your level: tap Retreat to run for the way in.', 3600);
        sfx('horn');
      } else if (e.t === 'summon' && e.spawn) {
        const b = s.byId[e.by];
        const u = s.byId[e.uid];
        B.spawnSeen = B.spawnSeen || new Set();
        if (b && u && !B.spawnSeen.has(b.uid)) {
          B.spawnSeen.add(b.uid);
          pushLog(B, `The ${esc(UNITS[b.type].name)} sends out a ${esc(UNITS[u.type].name)}, and will keep at it. What it makes is worth no XP: <b>break the ${esc(UNITS[b.type].name)}</b>.`, 'E');
        }
      } else if (e.t === 'reset' && e.why === 'leash') {
        pushLog(B, 'The pack gives up the chase: it goes home, heals and sleeps again.', 'O');
      } else if (e.t === 'reset' && e.why === 'stale') {
        pushLog(B, 'The fight goes quiet: the pack loses interest and goes home.', 'O');
      } else if (e.t === 'wipe') {
        pushLog(B, 'Your party is wiped out! Everyone gets up at the way in; the monsters heal.', 'E');
        banner('Back at the way in', true);
        if (B.focus && B.focus.retreat) B.focus = null;
      } else if (e.t === 'calm') {
        pushLog(B, 'The fight is over. Abilities ready again; the fallen get up at the way in.', 'P');
        if (B.focus && B.focus.retreat) B.focus = null;
        B.calmed = true;
      } else if (e.t === 'fatigue') {
        pushLog(B, `Round ${E.FATIGUE_AT} of the fight: <b>fatigue</b> sets in. Every unit loses a share of its health each turn, more each time: heal to outlast it.`, 'E');
        banner('Fatigue!', true);
      } else if (e.t === 'revive' && e.why === 'respawn') {
        const u = s.byId[e.uid];
        if (u) pushLog(B, `${nameOf(u)} gets up at the way in and runs to catch up.`, 'P');
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
    const fighting = s.inCombat;
    const left = s.units.filter((u) => u.alive && u.team === 'E' && !u.nonCombat).length;
    const fat = fighting ? E.fatigueIn(s) : null;
    const fatText = fat == null ? '' : fat > 0 ? ` · fatigue in ${fat}` : ' · <b class="fat">fatigue!</b>';
    const state = !B.started ? 'Ready' : B.paused ? 'Paused' : fighting ? `Fighting · round ${s.turn - s.fightFrom + 1}${fatText}` : 'Exploring';
    const pend = pending();
    const plv = DV.partyLevelIn(s);
    $('#topbar').innerHTML = `<div class="title"><b>${esc(DV.FLOOR_DEFS[p.run.floor].name)} <span class="muted">· party Lv ${Math.round(plv * 10) / 10}</span></b>
      <span>${state} · ${left} monster${left === 1 ? '' : 's'} left on this floor</span></div>
      ${B.started ? `<button class="btn icon-only speedbtn ${UI.prefs.speed > 1 ? 'on' : ''}" id="dFast" aria-label="Speed ${UI.prefs.speed}x">${ic('fast')}<small>${UI.prefs.speed}×</small></button>
      <button class="btn icon-only ${B.paused ? 'on' : ''}" id="dPause" aria-label="${B.paused ? 'Resume' : 'Pause'}">${ic(B.paused ? 'play' : 'pause')}</button>` : ''}
      ${pend.total ? `<button class="btn icon-only speedbtn upgrade" id="dUpgrade" data-choose aria-label="Upgrade your heroes">${ic('star')}<small>${pend.total}</small></button>` : ''}
      <button class="btn icon-only" id="dMenu" aria-label="Menu">${ic('menu')}</button>`;
    const sel = B.sel && s.byId[B.sel];
    const party = s.units.filter((u) => u.team === 'P' && !u.nonCombat && u.rid);
    $('#cmd').innerHTML = `
      ${!B.started ? `<div class="hint">${ic('swords')} Your party stands at the way in. Monster packs sleep in the rooms ahead until your heroes come near. <b>Begin</b> and they explore and fight on their own; pause or set a priority any time.</div>
        <div class="actions sticky"><button class="btn primary" id="dBegin">${ic('play')} Begin</button></div>` : ''}
      ${B.started && B.paused && pend.total ? `<div class="hint up-hint">${ic('star')} ${pend.points ? `<b>${pend.points} skill point${pend.points > 1 ? 's' : ''}</b> to spend` : ''}${pend.points && pend.items ? ' and ' : ''}${pend.items ? `<b>${pend.items} new item${pend.items > 1 ? 's' : ''}</b> to equip` : ''}: tap a hero below (or ${ic('star')} at the top), then ${ic('play')} to carry on.</div>` : ''}
      ${fighting && B.started ? roundStrip(s) : ''}
      ${fighting && B.started && !(B.focus && B.focus.retreat) ? `<div class="actions"><button class="btn" id="dRetreat">${ic('undo')} Retreat to the way in</button></div>` : ''}
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
    on('dUpgrade', () => menu());
    on('dRetreat', () => {
      const st = B.fl.start;
      B.focus = { tile: true, retreat: true, x: st.cx, y: st.cy };
      UI.board.focus = { x: st.cx, y: st.cy };
      toast('Run! Get far enough from their lair and the monsters give up the chase.');
      hud();
    });
    on('dKit', () => {
      const u = s.byId[B.sel];
      const h = u && DV.heroes(p).find((x) => x.id === u.rid);
      if (h) openKit(B, h);
    });
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
        const u = s.byId[+f.dataset.uid];
        const h = u && DV.heroes(p).find((x) => x.id === u.rid);
        // Something waiting on this hero: straight to its sheet.
        if (h && (owed(h) || newFor(h).length)) return openKit(B, h);
        B.sel = +f.dataset.uid;
        B.tile = null;
        hud();
      };
  }

  // A hero's sheet from the delve: the game waits while it is open, as it was before after.
  function openKit(B, h) {
    const was = B.paused;
    B.paused = true;
    hud();
    heroSheet(h, () => {
      DV.refreshParty(UI.p, B.s);
      UI.board.syncFromState(B.s);
      if (UI.B === B && B.started) {
        B.paused = was;
        if (!B.paused) runLoop();
      }
      hud();
    });
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
    const h = DV.heroes(UI.p).find((x) => x.id === u.rid);
    const waiting = h && (owed(h) || newFor(h).length);
    const turn = UI.B.s.due === u.uid;
    return `<button class="delve-frame ${u.alive ? '' : 'down'} ${UI.B.sel === u.uid ? 'sel' : ''} ${turn ? 'turn' : ''}" data-uid="${u.uid}" ${waiting ? 'data-choose' : ''}>
      <canvas data-p="${u.type}:P"></canvas>
      <span class="fr-body"><b>${esc(u.name || UNITS[u.type].name)} <span class="lvtag">${h ? h.lv : u.dlv}</span>${h ? pendingBadges(h) : ''}</b>
        <span class="hpbar ${f < 0.3 ? 'low' : f < 0.6 ? 'mid' : ''}"><i style="width:${Math.round(f * 100)}%"></i></span>
        ${h ? xpMini(h) : ''}
        <span class="small">${u.alive ? `${u.hp}/${u.maxHp}` : 'Back after the fight'} ${st.join(' ')}</span></span>
    </button>`;
  }

  // Who goes next in this round, then the next: fastest first, both sides mixed.
  function roundStrip(s) {
    const { now, next } = E.roundOrder(s);
    const list = now.concat(['|'], next).slice(0, 12);
    return `<div class="round-strip"><span class="small muted">Round ${s.turn - s.fightFrom + 1}</span>${list
      .map((id) => {
        if (id === '|') return '<span class="rs-sep" title="Next round"></span>';
        const u = s.byId[id];
        if (!u) return '';
        return `<span class="rs-u team-${u.team} ${id === s.due ? 'now' : ''} ${u.wait > 0 || u.para > 0 ? 'rest' : ''}"><canvas data-p="${u.type}:${u.team}"></canvas></span>`;
      })
      .join('')}</div>`;
  }

  function focusLine(B) {
    const f = AI.focusOf(B.s, 'P', B.focus);
    if (!f) return '';
    if (B.focus.retreat) return `<div class="focusline">${ic('undo')}<span><b>Retreating</b> to the way in</span><button class="btn" id="dUnfocus">Stop</button></div>`;
    const label = f.unit ? nameOf(f.unit) : f.ally ? `rally on ${f.ally.name || UNITS[f.ally.type].name}` : 'that spot';
    return `<div class="focusline">${ic('target')}<span>Priority: <b>${esc(label)}</b></span><button class="btn" id="dUnfocus">Clear</button></div>`;
  }

  function selPanel(B, u) {
    if (!u) return '';
    const f = Math.max(0, u.hp / u.maxHp);
    const verb = u.team === 'P' ? 'Rally on' : 'Priority';
    const dz = u.team === 'E' ? DV.danger(u.dlv || 1, DV.partyLevelIn(B.s)) : null;
    const dzText = { low: 'an easy fight', even: 'about your level', high: 'a level above you', deadly: 'too strong for now' }[dz];
    return `<div class="delve-sel"><canvas data-p="${u.type}:${u.team}"></canvas>
      <div class="grow"><b>${nameOf(u)}</b> <span class="muted">${u.champ ? 'Champion ' : ''}${esc(UNITS[u.type].name)} · <span class="lv-${dz || 'hero'}">Level ${u.dlv || u.level}</span>${u.asleep ? ' · asleep' : ''}</span>
        <span class="hpbar ${f < 0.3 ? 'low' : f < 0.6 ? 'mid' : ''}"><i style="width:${Math.round(f * 100)}%"></i></span>
        <span class="small">${u.alive ? `${u.hp}/${u.maxHp} HP` : 'Fallen: back after the fight'}${dzText ? ` · <span class="lv-${dz}">${dzText}</span>` : ''}</span></div>
      <div class="col"><button class="btn" id="dInfo">${ic('eye')}</button>${u.team === 'P' && u.rid ? `<button class="btn" id="dKit">${ic('army')} Kit</button>` : ''}${u.alive ? `<button class="btn primary" id="dFocus">${ic('target')} ${verb}</button>` : ''}<button class="btn ghost" id="dDesel">${ic('close')}</button></div></div>`;
  }

  function unitInfo(u) {
    if (!u) return;
    const T = UNITS[u.type];
    const acts = u.acts.filter((a) => a.kind !== 'none').map((a) => `<li><b>${esc(a.name)}</b>${a.uses ? ` (${a.left === Infinity ? '' : a.left + ' left'})` : ''}</li>`).join('');
    openSheet(`${sheetHead(`${nameOf(u)}`, `${u.champ ? 'Champion ' : ''}${esc(T.name)} · Level ${u.dlv || u.level} · ${u.hp}/${u.maxHp} HP · ${u.pow} power · ${Math.round(u.armor * 100)}% physical / ${Math.round(u.res * 100)}% magic resistance`)}
      <p>${esc(T.desc)}</p>${T.tip && u.team === 'E' ? `<p class="hint">${esc(T.tip)}</p>` : ''}
      ${E.SPAWN_OF[u.type] ? `<p class="hint">In the tower: while your party is near it sends out a ${esc(UNITS[E.SPAWN_OF[u.type]].name)} every ${E.SPAWN_EVERY} rounds, ${E.SPAWN_CAP} at a time at most. What it makes is worth no XP and drops nothing; breaking it pays, and the floor is not clear until it is broken. Siege units (the Trebuchet above all) hit buildings hard.</p>` : ''}
      ${u.spawned ? '<p class="hint">Sent out by a building: worth no XP, drops nothing.</p>' : ''}
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
      <div class="eyebrow">Your party: tap a hero for their skill points, items and kit</div>
      <div class="delve-roster">${DV.heroes(UI.p).map((h) => heroCard(h)).join('')}</div>
      <div class="actions col">
        <button class="btn primary" data-close>${ic('play')} Back to the delve</button>
        <label class="toggle"><input type="checkbox" id="mAutoPause" ${UI.prefs.autoPause ? 'checked' : ''}> Pause after a fight when there is a level up or loot to see to</label>
        <button class="btn" id="mHelp">${ic('help')} How it works</button>
        <button class="btn" id="mTown">${ic('undo')} Town portal (this floor starts over when you come back; XP and items are kept)</button>
      </div>`, (sh) => {
      UI.onSheetClose = () => {
        if (UI.B === B && B.started) {
          B.paused = was;
          hud();
          if (!B.paused) runLoop();
        }
      };
      $('#mHelp', sh).onclick = help;
      $('#mAutoPause', sh).onchange = (e) => {
        UI.prefs.autoPause = e.target.checked;
        savePrefs();
      };
      for (const b of $$('[data-hero]', sh))
        b.onclick = () => {
          const back = UI.onSheetClose;
          heroSheet(DV.heroes(UI.p).find((h) => h.id === b.dataset.hero), () => {
            DV.refreshParty(UI.p, B.s);
            UI.board.syncFromState(B.s);
            if (back) back();
          });
        };
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
    const floor = p.run.floor;
    // Whatever fell last still pays out.
    afterStep(B);
    const loot = B.loot.map((it) => `<li>${ic('chest')} <b>${esc(DV.itemDef(it).name)}</b> <span class="muted">(${it.kind})</span></li>`).join('');
    const res = DV.finishFloor(p, B.s);
    const levels = `<p class="small">${DV.heroes(p).map((h) => `${esc(h.name)} <b>Lv ${h.lv}</b>${owed(h) ? ` <span class="chip good">+${owed(h)}</span>` : ''}`).join(' · ')}</p>`;
    if (res.done) {
      sfx('victory');
      openSheet(`${sheetHead('The Countess is slain!', 'The Forgotten Tower is beaten.')}
        <p>Her tower falls quiet. Your party walks out into the light with everything it found.</p>${levels}
        ${loot ? `<div class="eyebrow">Found on this floor</div><ul class="tips">${loot}</ul>` : ''}
        <div class="actions"><button class="btn primary" data-close>${ic('crown')} Back to town</button></div>`, () => {
        UI.onSheetClose = () => title();
      });
      return;
    }
    openSheet(`${sheetHead(`${esc(DV.FLOOR_DEFS[floor].name)} cleared`, `Stairs down to ${esc(DV.FLOOR_DEFS[res.floor].name)}`)}
      <p>Everyone rests on the stairs: the next floor starts with the whole party up, at full health.</p>${levels}
      ${loot ? `<div class="eyebrow">Found on this floor</div><ul class="tips">${loot}</ul>` : '<p class="muted">Nothing dropped this time.</p>'}
      <div class="actions col">
        <button class="btn primary" id="fDown">${ic('play')} Take the stairs down</button>
        <button class="btn" id="fParty">${ic('army')} Party &amp; kit first</button>
        <button class="btn" id="fTown">${ic('undo')} Town portal</button>
      </div>`, (sh) => {
      // Closed any other way, it is the town portal: the delve waits on the next floor.
      UI.onSheetClose = () => title();
      $('#fDown', sh).onclick = () => {
        UI.onSheetClose = null;
        closeSheet();
        delve();
      };
      $('#fParty', sh).onclick = () => {
        UI.onSheetClose = null;
        closeSheet();
        UI.B = null;
        partyScreen(true);
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
