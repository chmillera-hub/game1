/* Turning unit data into words and pictures: rules text, the move/attack
   diagram, status icons, inspector panels, roster cards. */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;

  // Afflictions, each with a colour and a small white sign on a round badge.
  UI.STATUS = {
    burn: { name: 'Burning', tone: '#ff6a1a', d: (s) => 'Takes ' + s.d + ' damage at the start of its turn (' + s.t + ' more).' },
    poison: { name: 'Poisoned', tone: '#3daa2a', d: (s) => 'Takes ' + s.d + ' damage at the start of its turn (' + s.t + ' more).' },
    chill: { name: 'Chilled', tone: '#36b4f0', d: (s) => '−' + s.a + ' SPD, so it acts later in the round.' },
    frozen: { name: 'Frozen', tone: '#1f5fe0', d: () => 'Skips its next turn and takes +2 damage from every hit.' },
    stunned: { name: 'Stunned', tone: '#f5c400', d: () => 'Skips its next turn.' },
    rooted: { name: 'Rooted', tone: '#8a5a2b', d: () => 'Cannot move on its next turn.' },
    marked: { name: 'Marked', tone: '#e2242c', d: (s) => 'Takes +' + s.a + ' damage from every hit.' },
    cursed: { name: 'Hexed', tone: '#8b2cd8', d: (s) => 'Takes +' + s.a + ' damage from every hit' + (s.dot ? ' and ' + s.dot + ' each turn.' : '.') },
    taunt: { name: 'Taunted', tone: '#ff4a1c', d: () => 'Must attack the unit that taunted it if it can.' },
    stealth: { name: 'Stealthed', tone: '#6b6b78', d: () => 'Enemies cannot target it until it strikes.' },
    emp: { name: 'Empowered', tone: '#f5b400', d: (s) => 'Its next attack deals +' + s.a + '.' },
    haste: { name: 'Hasted', tone: '#10a4d6', d: (s) => '+' + s.a + ' SPD until the end of next round.' },
    weak: { name: 'Weakened', tone: '#7d7d8c', d: (s) => 'Its next attack deals ' + s.a + ' less.' },
    corrode: { name: 'Corroded', tone: '#7f8f1c', d: () => '−1 armor.' },
  };
  const NS = 'http://www.w3.org/2000/svg';
  const D = AG.Art.D;
  const W = (d) => '<path fill="#fff" d="' + d + '"/>';
  const K = (d) => '<path fill="#16161b" d="' + d + '"/>';
  const WL = (d, w) => '<path fill="none" stroke="#fff" stroke-width="' + (w || 9) + '" stroke-linecap="round" stroke-linejoin="round" d="' + d + '"/>';
  const SIGN = {
    burn: () => W(D.flame(50, 80, 46, 62, 3)),
    poison: () => W(D.drop(50, 18, 40, 62)),
    chill: () => WL('M50 20V80M24 35L76 65M24 65L76 35', 8),
    frozen: () => W(D.regular(50, 50, 27, 6, 0)) + WL('M50 34V66M36 42L64 58M36 58L64 42', 5).replace('#fff', '#1f5fe0'),
    stunned: () => K(D.star(50, 52, 31, 13, 5)),
    rooted: () => WL('M28 74C28 44 72 58 72 26M28 26C38 46 62 54 72 74', 8),
    marked: () => '<circle cx="50" cy="50" r="18" fill="none" stroke="#fff" stroke-width="8"/>' + WL('M50 16V34M50 66V84M16 50H34M66 50H84', 8),
    cursed: () => WL(D.star(50, 53, 30, 12, 5).replace(/Z$/, '') + 'Z', 6),
    taunt: () => '<rect x="43" y="18" width="14" height="40" rx="5" fill="#fff"/><circle cx="50" cy="73" r="8" fill="#fff"/>',
    stealth: () => WL('M18 50C34 28 66 28 82 50C66 72 34 72 18 50Z', 7) + '<circle cx="50" cy="50" r="9" fill="#fff"/>' + WL('M24 76L76 24', 8),
    emp: () => K(D.poly([[50, 16], [76, 48], [61, 48], [61, 82], [39, 82], [39, 48], [24, 48]])),
    haste: () => WL('M26 26L48 50L26 74M52 26L74 50L52 74', 10),
    weak: () => W(D.poly([[50, 84], [76, 52], [61, 52], [61, 18], [39, 18], [39, 52], [24, 52]])),
    corrode: () => W(D.drop(50, 18, 36, 58)) + '<circle cx="50" cy="58" r="7" fill="#7f8f1c"/>',
  };
  UI.statusIcon = function (k) {
    const S = UI.STATUS[k];
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('class', 'sti');
    svg.setAttribute('aria-hidden', 'true');
    svg.innerHTML = '<circle cx="50" cy="50" r="44" fill="' + (S ? S.tone : '#777') + '" stroke="#16161b" stroke-width="8"/>' + (SIGN[k] ? SIGN[k]() : '');
    return svg;
  };
  // Small interface icons drawn in ink: play, pause, skip, shield, speaker, mute, swords.
  const UIC = {
    play: '<path d="M30 18L82 50L30 82Z" fill="currentColor"/>',
    pause: '<rect x="24" y="18" width="18" height="64" rx="3" fill="currentColor"/><rect x="58" y="18" width="18" height="64" rx="3" fill="currentColor"/>',
    skip: '<path d="M14 20L50 50L14 80ZM50 20L86 50L50 80Z" fill="currentColor"/><rect x="84" y="20" width="10" height="60" fill="currentColor"/>',
    shield: '<path d="M50 8L86 20C86 54 72 78 50 92C28 78 14 54 14 20Z" fill="#5b8cff" stroke="#16161b" stroke-width="8" stroke-linejoin="round"/>',
    speaker: '<path d="M14 38H32L56 18V82L32 62H14Z" fill="currentColor"/><path d="M68 34C76 42 76 58 68 66M78 24C92 38 92 62 78 76" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>',
    mute: '<path d="M14 38H32L56 18V82L32 62H14Z" fill="currentColor"/><path d="M68 38L90 62M90 38L68 62" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>',
    swords: '<g fill="currentColor"><path d="M12 8L28 10L70 52L62 60L20 18Z"/><path d="M88 8L72 10L30 52L38 60L80 18Z"/><path d="M52 58L60 50L74 64L66 72Z"/><path d="M48 58L40 50L26 64L34 72Z"/><circle cx="76" cy="80" r="8"/><circle cx="24" cy="80" r="8"/><path d="M64 66L72 74L80 80L74 82Z"/><path d="M36 66L28 74L20 80L26 82Z"/></g>',
  };
  UI.uiIcon = function (name) {
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('class', 'ui');
    svg.setAttribute('aria-hidden', 'true');
    svg.innerHTML = UIC[name] || '';
    return svg;
  };
  // A symbol (rune, relic, ability) set as text, never as a colour emoji.
  UI.glyph = function (s) {
    return h('span.glyph', String(s).replace(/([←-⯿])(?!︎)/g, '$1︎'));
  };
  // The figurine for a unit; small by default (thicker lines, no fine detail).
  UI.icon = function (u, size) {
    return UI.piece(u, { cls: size === 'lg' ? '' : size === 'md' ? 'md' : 'sm' });
  };
  // Rarity colour for the tile behind a figure.
  UI.rarityClass = function (def) {
    const d = AG.Units[def] || {};
    if (d.boss) return 'r-boss';
    if (d.pool === 'enemy') return d.big ? 'r-rare' : 'r-enemy';
    return d.rarity === 'uncommon' ? 'r-uncommon' : d.rarity === 'rare' ? 'r-rare' : '';
  };

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
  UI.patternDiagram = function (u, cell) {
    cell = cell || 13;
    const mr = AG.AI.moveRange(u);
    const ar = AG.AI.attackRange(u.at);
    const R = Math.max(2, Math.min(4, Math.max(u.mv && u.mv.type === 'leap' ? 2 : mr, ar)));
    const mc = moveCells(u, R), ac = attackCells(u, R);
    const size = R * 2 + 1;
    const grid = h('div.pattern', { style: { gridTemplateColumns: 'repeat(' + size + ', ' + cell + 'px)', '--pcell': cell + 'px' }, 'aria-hidden': 'true' });
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
      h('div.ic.' + side + (UI.rarityClass(u.def) ? '.' + UI.rarityClass(u.def) : ''), UI.icon(u, 'lg')),
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
      if (u.shield) row.appendChild(h('span.chip.arcane', UI.uiIcon('shield'), u.shield + ' shield'));
      for (const k in u.st) {
        const S = UI.STATUS[k];
        if (S) row.appendChild(h('span.chip', { 'data-tip': S.d(u.st[k]), 'data-tip-title': S.name }, UI.statusIcon(k), S.name));
      }
      parts.push(row);
    }
    parts.push(h('div.pattern-block',
      UI.patternDiagram(u),
      h('div.legend',
        h('div', h('span.k.m'), h('span', UI.moveText(u))),
        h('div', h('span.k.a'), h('span', UI.attackText(u))),
      ),
    ));
    if (u.abil.length) {
      parts.push(h('div.sec-title', 'Abilities'));
      for (const a of u.abil) {
        const A = AG.Abilities[a.id];
        let cd = a.p.cd != null ? a.p.cd : A.cd;
        if (u.pas.spellweaver) cd = Math.max(1, cd - 1);
        const left = live && u.cd[a.id] ? ' · ready in ' + u.cd[a.id] : live ? ' · ready' : '';
        parts.push(h('div.ab', h('div.t', UI.glyph(A.icon), A.name, h('span.cd', 'every ' + AG.plural(cd, 'turn') + left)), h('div.d', A.desc(a.p))));
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
        h('span.t', UI.glyph(R.icon), R.name + (free[k] > 1 || (on && free[k] > 0) ? ' ×' + (free[k] + (on ? 1 : 0)) : '')), h('span.c', '+' + R.cost),
        h('span.d', useless ? 'This unit already has this effect.' : R.desc)));
    }
    wrap.appendChild(rl);
    if (L.onRemove) wrap.appendChild(h('div.row', h('button.btn.small.danger', { type: 'button', on: { click: L.onRemove } }, 'Remove from board')));
    return wrap;
  };

  UI.relicIcon = function (id) {
    const R = AG.Relics[id];
    return h('span.relic', { 'data-tip': R.desc, 'data-tip-title': R.name, tabindex: '0', 'aria-label': R.name + ': ' + R.desc }, UI.glyph(R.icon));
  };

  UI.rosterCard = function (def, opts) {
    const d = AG.Units[def];
    const u = opts.unit || AG.B.makeUnit(def, 0, 0, 0, { rank: opts.rank || 0 });
    const card = h('button.rcard' + (opts.sel ? '.sel' : '') + (opts.cant ? '.cant' : ''), { type: 'button', 'aria-label': d.name + ', ' + d.cost + ' supply' },
      h('span.ic' + (UI.rarityClass(def) ? '.' + UI.rarityClass(def) : ''), UI.icon(def, 'md')),
      h('span.nm', d.name, opts.rank ? h('span.stars', ' ' + '★'.repeat(opts.rank)) : null),
      h('span.st', h('small', 'HP '), u.maxHp, h('small', ' ATK '), u.atk, h('small', ' SPD '), u.spd),
      h('span.cost', d.cost),
    );
    return card;
  };
})(globalThis.AG = globalThis.AG || {});
