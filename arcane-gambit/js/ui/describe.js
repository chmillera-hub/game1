/* Turning unit data into words and pictures: rules text, the move/attack
   diagram, status icons, inspector panels, roster cards. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;

  UI.STATUS = {
    burn: { icon: '🔥', name: 'Burning', d: (s) => 'Takes ' + s.d + ' damage at the start of its turn (' + s.t + ' more).' },
    poison: { icon: '🧪', name: 'Poisoned', d: (s) => 'Takes ' + s.d + ' damage at the start of its turn (' + s.t + ' more).' },
    chill: { icon: '❄️', name: 'Chilled', d: (s) => '−' + s.a + ' SPD, so it acts later in the round.' },
    frozen: { icon: '🧊', name: 'Frozen', d: () => 'Skips its next turn and takes +2 damage from every hit.' },
    stunned: { icon: '💫', name: 'Stunned', d: () => 'Skips its next turn.' },
    rooted: { icon: '⛓️', name: 'Rooted', d: () => 'Cannot move on its next turn.' },
    marked: { icon: '🎯', name: 'Marked', d: (s) => 'Takes +' + s.a + ' damage from every hit.' },
    cursed: { icon: '⛧', name: 'Hexed', d: (s) => 'Takes +' + s.a + ' damage from every hit' + (s.dot ? ' and ' + s.dot + ' each turn.' : '.') },
    taunt: { icon: '❗', name: 'Taunted', d: () => 'Must attack the unit that taunted it if it can.' },
    stealth: { icon: '🌫️', name: 'Stealthed', d: () => 'Enemies cannot target it until it strikes.' },
    emp: { icon: '⚔️', name: 'Empowered', d: (s) => 'Its next attack deals +' + s.a + '.' },
    haste: { icon: '⏩', name: 'Hasted', d: (s) => '+' + s.a + ' SPD until the end of next round.' },
    weak: { icon: '🔻', name: 'Weakened', d: (s) => 'Its next attack deals ' + s.a + ' less.' },
    corrode: { icon: '🫗', name: 'Corroded', d: () => '−1 armor.' },
  };

  UI.icon = function (u) { return u.icon || (AG.Units[u.def] && AG.Units[u.def].icon) || '?'; };

  // ------------------------------------------------------------- text
  UI.moveText = function (u) {
    const mv = u.mv || { type: 'none' };
    let t;
    const fly = u.flying ? ' Flies over units and chasms.' : '';
    switch (mv.type) {
      case 'walk': t = (u.flying ? 'Flies' : 'Walks') + ' up to ' + AG.plural(mv.n, 'square') + (mv.dirs === 'orth' ? ' (no diagonals)' : '') + '.' + (u.flying ? ' Passes over units and chasms.' : ' Can pass through allies.'); break;
      case 'slide': t = 'Slides up to ' + AG.plural(mv.n, 'square') + ' in a straight line ' + (mv.dirs === 'orth' ? 'along ranks and files, like a rook.' : mv.dirs === 'diag' ? 'diagonally, like a bishop.' : 'in any direction, like a queen.') + fly; break;
      case 'leap': t = 'Leaps in an L like a chess knight, over anything in the way' + (mv.step ? ', or steps one square.' : '.') + fly; break;
      case 'blink': t = 'Teleports up to ' + AG.plural(mv.n, 'square') + '.'; break;
      case 'shadow': t = 'Shadowsteps beside any enemy within ' + mv.n + ', or steps one square.'; break;
      default: t = 'Never moves.';
    }
    if (u.mv2 && u.mv2.type === 'blink') t += ' Can also teleport up to ' + u.mv2.n + '.';
    return t;
  };

  function patternText(ap) {
    switch (ap.pattern) {
      case 'melee': return 'Strikes an adjacent enemy, diagonals included';
      case 'melee4': return 'Strikes an enemy directly beside it (no diagonals)';
      case 'offsets': return 'Strikes enemies a knight’s leap away';
      case 'reach': return 'Pike reach: strikes up to ' + ap.range + ' squares away in straight lines, past allies';
      case 'ranged': return 'Shoots any enemy within ' + ap.range + (ap.los === false ? '' : ' it can see') + (ap.minRange > 1 ? ' (not closer than ' + ap.minRange + ')' : '');
      case 'line': return 'Shoots the first unit along ' + (ap.dirs === 'orth' ? 'its rank or file' : ap.dirs === 'diag' ? 'a diagonal' : 'a rank, file or diagonal') + ', up to ' + ap.range + (ap.pierce ? ', piercing everything in the line' : '');
      case 'lob': return 'Lobs shells ' + (ap.minRange || 1) + '–' + ap.range + ' squares away, over walls and units';
      default: return 'Attacks';
    }
  }
  UI.attackText = function (u) {
    const at = u.at;
    if (!at) return 'Does not attack.';
    let t = patternText(at);
    if (at.also) for (const ap of at.also) t += '. Also: ' + patternText(ap).toLowerCase();
    t += '.';
    const ex = [];
    if (at.hits > 1) ex.push('Strikes ' + at.hits + ' times.');
    if (at.splash) ex.push('Splashes ' + at.splash + ' onto everything next to the target, allies too.');
    if (at.blast) ex.push('Also hits enemies next to the target for ' + at.blast + '.');
    if (at.chain) ex.push('Lightning jumps to ' + at.chain.n + ' more nearby enemies' + (at.chain.falloff ? ', losing 1 damage each jump.' : '.'));
    if (at.whirl) ex.push('Hits every adjacent enemy.');
    else if (at.cleave) ex.push('Cleaves a second adjacent enemy for ' + at.cleave + '.');
    if (at.lifesteal) ex.push('Heals for ' + (at.lifesteal >= 1 ? 'all' : Math.round(at.lifesteal * 100) + '%') + ' of the damage it deals.');
    if (at.ignoreArmor) ex.push('Ignores armor.');
    if (at.capture) ex.push('Kills capture the square, like chess.');
    const fx = at.fx || {};
    if (fx.burn) ex.push('Sets the target alight: ' + fx.burn.d + ' a turn for ' + fx.burn.t + ' turns.');
    if (fx.poison) ex.push('Poisons: ' + fx.poison.d + ' a turn for ' + fx.poison.t + ' turns.');
    if (fx.chill) ex.push('Chills: −' + fx.chill + ' SPD.');
    if (fx.freezeChilled) ex.push('Freezes targets that were already chilled.');
    if (fx.mark) ex.push('Marks the target (+1 damage from every hit).');
    if (fx.root) ex.push('Roots the target.');
    if (fx.knock) ex.push('Knocks the target back a square.');
    return t + (ex.length ? ' ' + ex.join(' ') : '');
  };

  // ------------------------------------------------------- diagram
  function moveCells(u, R) {
    const out = new Set();
    const mv = u.mv || { type: 'none' };
    const add = (x, y) => { if (Math.abs(x) <= R && Math.abs(y) <= R && (x || y)) out.add(x + ',' + y); };
    const specs = [mv].concat(u.mv2 ? [u.mv2] : []);
    for (const m of specs) {
      if (m.type === 'walk' || m.type === 'blink' || m.type === 'shadow') {
        const n = m.type === 'shadow' ? 1 : m.n;
        for (let y = -n; y <= n; y++) for (let x = -n; x <= n; x++) {
          if (m.dirs === 'orth' && Math.abs(x) + Math.abs(y) > n) continue;
          add(x, y);
        }
      } else if (m.type === 'slide') {
        for (const [dx, dy] of AG.dirsFor(m.dirs)) for (let k = 1; k <= m.n; k++) add(dx * k, dy * k);
      } else if (m.type === 'leap') {
        for (const [dx, dy] of m.offsets || AG.KNIGHT) add(dx, dy);
        if (m.step) for (const [dx, dy] of AG.DIRS8) add(dx, dy);
      }
    }
    return out;
  }
  function attackCells(u, R) {
    const out = new Set();
    if (!u.at) return out;
    const add = (x, y) => { if (Math.abs(x) <= R && Math.abs(y) <= R && (x || y)) out.add(x + ',' + y); };
    for (const ap of [u.at].concat(u.at.also || [])) {
      switch (ap.pattern) {
        case 'melee': for (const [dx, dy] of AG.DIRS8) add(dx, dy); break;
        case 'melee4': for (const [dx, dy] of AG.DIRS4) add(dx, dy); break;
        case 'offsets': for (const [dx, dy] of ap.offsets || AG.KNIGHT) add(dx, dy); break;
        case 'reach':
        case 'line': for (const [dx, dy] of AG.dirsFor(ap.dirs)) for (let k = 1; k <= ap.range; k++) add(dx * k, dy * k); break;
        case 'ranged':
        case 'lob':
          for (let y = -ap.range; y <= ap.range; y++) for (let x = -ap.range; x <= ap.range; x++) {
            if (Math.max(Math.abs(x), Math.abs(y)) >= (ap.minRange || 1)) add(x, y);
          }
          break;
        default: break;
      }
    }
    return out;
  }
  UI.patternDiagram = function (u) {
    const mr = AG.AI.moveRange(u);
    const ar = AG.AI.attackRange(u.at);
    const R = Math.max(2, Math.min(4, Math.max(u.mv && u.mv.type === 'leap' ? 2 : mr, ar)));
    const mc = moveCells(u, R), ac = attackCells(u, R);
    const size = R * 2 + 1;
    const grid = h('div.pattern', { style: { gridTemplateColumns: 'repeat(' + size + ', 13px)' }, 'aria-hidden': 'true' });
    for (let y = -R; y <= R; y++) {
      for (let x = -R; x <= R; x++) {
        const k = x + ',' + y;
        let cls = (x + y) % 2 === 0 ? '' : 'alt';
        if (!x && !y) cls = 'me';
        else if (mc.has(k) && ac.has(k)) cls = 'ma';
        else if (mc.has(k)) cls += ' m';
        else if (ac.has(k)) cls += ' a';
        grid.appendChild(h('i', { class: cls }));
      }
    }
    return grid;
  };

  // ------------------------------------------------------ inspector
  // u: a unit object (B.makeUnit result or a live battle unit).
  UI.inspector = function (u, opts) {
    opts = opts || {};
    const d = AG.Units[u.def];
    const side = u.side === 0 ? 'p' : 'e';
    const head = h('div.insp-head',
      h('div.ic.' + side, UI.icon(u)),
      h('h3', u.name, u.rank ? h('span.faint', ' ' + '★'.repeat(u.rank)) : null),
      h('div.row', { style: { gap: '6px' } },
        d.cost != null && u.side === 0 ? h('span.chip.brass', d.cost + ' supply') : null,
        d.rarity ? h('span.rarity.' + d.rarity, d.rarity) : null,
        u.boss ? h('span.chip.garnet', 'Boss') : null,
        u.objective ? h('span.chip.garnet', 'Objective') : null,
        u.summoned ? h('span.chip', 'Summoned') : null,
      ),
    );
    const live = opts.live;
    const stats = h('div.statline',
      h('div', h('div.k', 'HP'), h('div.v', live ? u.hp + '/' + u.maxHp : u.maxHp)),
      h('div', h('div.k', 'ATK'), h('div.v', u.at ? u.atk : '–')),
      h('div', h('div.k', 'SPD'), h('div.v', live ? AG.B.spd(opts.state, u) : u.spd)),
      h('div', h('div.k', 'Armor'), h('div.v', u.armor)),
    );
    const parts = [head];
    if (d.blurb) parts.push(h('p.muted', { style: { fontSize: '14px' } }, d.blurb));
    parts.push(stats);
    if (live && (u.shield || Object.keys(u.st).length)) {
      const row = h('div.row', { style: { gap: '6px' } });
      if (u.shield) row.appendChild(h('span.chip', { style: { color: 'var(--shield)' } }, '⛨ ' + u.shield + ' shield'));
      for (const k in u.st) {
        const S = UI.STATUS[k];
        if (S) row.appendChild(h('span.chip', { 'data-tip': S.d(u.st[k]), 'data-tip-title': S.name }, S.icon + ' ' + S.name));
      }
      parts.push(row);
    }
    parts.push(h('div.pattern-block',
      UI.patternDiagram(u),
      h('div.legend',
        h('div', h('span.k', { style: { background: 'var(--arcane)' } }), UI.moveText(u)),
        h('div', h('span.k', { style: { background: 'rgba(255,107,94,.8)', borderRadius: '2px' } }), UI.attackText(u)),
      ),
    ));
    if (u.abil.length) {
      parts.push(h('div.sec-title', 'Abilities'));
      for (const a of u.abil) {
        const A = AG.Abilities[a.id];
        let cd = a.p.cd != null ? a.p.cd : A.cd;
        if (u.pas.spellweaver) cd = Math.max(1, cd - 1);
        const left = live && u.cd[a.id] ? ' · ready in ' + u.cd[a.id] : live ? ' · ready' : '';
        parts.push(h('div.ab', h('div.t', A.icon + ' ' + A.name, h('span.cd', 'every ' + AG.plural(cd, 'turn') + left)), h('div.d', A.desc(a.p))));
      }
    }
    const pk = Object.keys(u.pas).filter((k) => AG.Passives[k]);
    if (pk.length) {
      parts.push(h('div.sec-title', 'Traits'));
      for (const k of pk) {
        const P = AG.Passives[k];
        parts.push(h('div.ab.passive', h('div.t', P.name), h('div.d', P.desc(u.pas[k] || {}))));
      }
    }
    if (u.immune && u.immune.length) {
      parts.push(h('p.faint', { style: { fontSize: '13px' } }, 'Immune to ' + (u.immune.indexOf('all') >= 0 ? 'all afflictions' : u.immune.map((k) => (UI.STATUS[k] ? UI.STATUS[k].name : k).toLowerCase().replace('burning', 'burn').replace('poisoned', 'poison').replace('frozen', 'freeze').replace('chilled', 'chill')).join(', ')) + '.'));
    }
    if (opts.loadout) parts.push(UI.loadoutPanel(u, opts.loadout));
    else if (d.talents && opts.showTalents) {
      parts.push(h('div.sec-title', 'Talents'));
      for (const tid of d.talents) {
        const T = AG.Talents[tid];
        parts.push(h('div.ab', h('div.t', T.name, h('span.cd', '+' + T.cost + ' supply')), h('div.d', T.desc)));
      }
    }
    return h('div.insp', parts);
  };

  // Talent & rune pickers for a placed unit during setup.
  UI.loadoutPanel = function (u, L) {
    const d = AG.Units[u.def];
    const wrap = h('div.stack', { style: { gap: '8px' } });
    wrap.appendChild(h('div.sec-title', 'Talents · ' + (L.slots > 1 ? 'pick up to 2 (Elite)' : 'pick 1')));
    const tl = h('div.opts');
    for (const tid of d.talents) {
      const T = AG.Talents[tid];
      const on = L.entry.talents.indexOf(tid) >= 0;
      const cost = L.talentCost(tid);
      tl.appendChild(h('button.opt' + (on ? '.on' : ''), { type: 'button', 'aria-pressed': on ? 'true' : 'false', on: { click: () => L.onTalent(tid) } },
        h('span.t', T.name), h('span.c', '+' + cost), h('span.d', T.desc)));
    }
    wrap.appendChild(tl);
    wrap.appendChild(h('div.sec-title', 'Rune'));
    const rl = h('div.opts');
    const free = L.runesFree;
    const ids = Object.keys(free).filter((k) => free[k] > 0 || L.entry.rune === k);
    rl.appendChild(h('button.opt' + (!L.entry.rune ? '.on' : ''), { type: 'button', on: { click: () => L.onRune(null) } }, h('span.t', 'No rune'), h('span.c', '')));
    if (!ids.length) rl.appendChild(h('p.hint', 'You have no spare runes. Win them in battle or buy them in shops.'));
    for (const k of ids) {
      const R = AG.Runes[k];
      const on = L.entry.rune === k;
      const useless = !on && !AG.runeHasEffect(L.entry.def, k, L.entry.talents);
      rl.appendChild(h('button.opt' + (on ? '.on' : '') + (useless ? '.off' : ''), { type: 'button', disabled: useless, on: { click: () => { if (!useless) L.onRune(k); } } },
        h('span.t', R.icon + ' ' + R.name + (free[k] > 1 || (on && free[k] > 0) ? ' ×' + (free[k] + (on ? 1 : 0)) : '')), h('span.c', '+' + R.cost),
        h('span.d', useless ? 'This unit already has this effect.' : R.desc)));
    }
    wrap.appendChild(rl);
    if (L.onRemove) wrap.appendChild(h('div.row', h('button.btn.small.danger', { type: 'button', on: { click: L.onRemove } }, 'Remove from board')));
    return wrap;
  };

  UI.relicIcon = function (id) {
    const R = AG.Relics[id];
    return h('span.relic', { 'data-tip': R.desc, 'data-tip-title': R.name, tabindex: '0', 'aria-label': R.name + ': ' + R.desc }, R.icon);
  };

  UI.rosterCard = function (def, opts) {
    const d = AG.Units[def];
    const u = opts.unit || AG.B.makeUnit(def, 0, 0, 0, { rank: opts.rank || 0 });
    const card = h('button.rcard' + (opts.sel ? '.sel' : '') + (opts.cant ? '.cant' : ''), { type: 'button', 'aria-label': d.name + ', ' + d.cost + ' supply' },
      h('span.ic', d.icon),
      h('span.nm', d.name, opts.rank ? h('span.stars', ' ' + '★'.repeat(opts.rank)) : null),
      h('span.st', h('small', 'HP '), u.maxHp, h('small', ' ATK '), u.atk, h('small', ' SPD '), u.spd),
      h('span.cost', d.cost),
    );
    return card;
  };
})(globalThis.AG = globalThis.AG || {});
