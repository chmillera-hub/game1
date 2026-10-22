// Screens and touch controls: title, campaign setup, map, army and loadouts, war room,
// battle, rewards, shop, rest, events, help and codex.
(function (root) {
  'use strict';
  const AG = root.AG;
  const D = AG.Data;
  const { UNITS, ABILITIES, MASTERY, SKILLS, GEAR, ENCHANTS, RELICS, WARBANDS, DIFFICULTIES, ACTS, COMMAND, LEVEL_COST, SKILL_SLOTS, GEAR_SLOTS } = D;
  const R = AG.Run;
  const E = AG.Engine;
  const AI = AG.AI;

  const $ = (sel, el) => (el || document).querySelector(sel);
  const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));
  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const ic = (name) => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  const pct = (v) => Math.round(v * 100) + '%';
  // Damage types at a glance: a sword for physical, a violet sparkle for magic.
  const DMG_TYPES = {
    phys: { icon: 'sword', tip: 'Physical damage: armor and block reduce it' },
    magic: { icon: 'magic', tip: 'Magic damage: magic resistance reduces it' },
  };
  const dmgIcon = (type) => (DMG_TYPES[type] ? `<span class="dt dt-${type}" title="${DMG_TYPES[type].tip}">${ic(DMG_TYPES[type].icon)}</span>` : '');
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const stars = (n) => (n > 1 ? '★'.repeat(n) : '');
  const cap1 = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const PREFS_KEY = 'arena-gauntlet-prefs';

  const UI = {
    run: null,
    board: null,
    battle: null,
    wr: null,
    mapSel: null,
    prefs: { fast: false, threat: false, manualFacing: false },
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

  // Re-render a sheet in place, keeping the scroll position.
  function refreshSheet(html, bind) {
    const sh = $('#sheet');
    const top = sh.scrollTop;
    openSheet(html, bind);
    sh.scrollTop = top;
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
      UI.onSheetClose = null;
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

  function unitSub(r) {
    return `${UNITS[r.type].name} · Lv ${r.load.lv}${r.enchant ? ' · ' + ENCHANTS[r.enchant].name : ''}`;
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
          <div class="nm"><b>${esc(u.name)}</b><div class="small muted">${esc(unitSub(u))}</div></div>
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

  // ------------------------------------------------------------ describing units

  function rangeLabel(a) {
    switch (a.kind) {
      case 'strike':
      case 'cleave':
      case 'quake':
      case 'blast':
      case 'grow':
      case 'heal':
      case 'shield':
      case 'hazard':
      case 'raise':
      case 'leap':
      case 'blink':
      case 'shadowstrike':
        return a.range[0] === a.range[1] ? String(a.range[0]) : a.range[0] + '-' + a.range[1];
      case 'line':
        return 'Line ' + a.len;
      case 'cone':
        return 'Cone ' + a.len;
      case 'cross':
        return 'Cross ' + a.len;
      case 'nova':
      case 'pray':
      case 'drum':
      case 'rally':
      case 'detonate':
        return 'Aura ' + a.radius;
      default:
        return '-';
    }
  }

  function rangeText(r) {
    if (r[1] === 0) return 'on itself';
    if (r[0] === 1 && r[1] === 1) return 'next to it';
    if (r[0] <= 1) return 'up to ' + r[1] + ' tiles away';
    return r[0] + '-' + r[1] + ' tiles away';
  }

  function statsHTML(u) {
    const a = u.act;
    const heal = a.kind === 'pray' || a.kind === 'drum';
    const poisoner = a.fx && a.fx.poison && !a.dmg;
    const powLabel = heal ? 'Heal' : poisoner ? 'Poison' : 'DMG';
    const powVal = heal ? E.healAmount(u, a) : poisoner ? E.poisonDamage(u, a) : u.pow || '-';
    const st = (v, l, title, cls) => `<div class="stat ${cls || ''}"${title ? ` title="${title}"` : ''}><b>${v}</b><span>${l}</span></div>`;
    const dt = !heal && !poisoner && DMG_TYPES[a.dmg] ? a.dmg : null;
    const power = dt ? st(dmgIcon(dt) + powVal, powLabel, DMG_TYPES[dt].tip, 'dmg-' + dt) : st(powVal, powLabel);
    return `<div class="stats">${power}${st(pct(u.armor), 'Armor')}${st(pct(u.res), 'M.Res')}${st(u.facing < 0 ? '-' : pct(u.block), 'Block')}${st(E.cooldown(u), 'CD', 'Cooldown: after acting, it can go again this many turns later')}${st(u.move, 'Move')}${st(rangeLabel(a), 'Range')}</div>`;
  }

  function fxText(u, a) {
    const fx = E.hitFx(u, a);
    const bits = [];
    if (fx.para) bits.push(`paralyzes for ${fx.para} turn${fx.para > 1 ? 's' : ''}`);
    if (fx.poison) bits.push(`poisons for ${fx.poison[0]} turns (${fx.poison[1]} a turn, no healing)`);
    if (fx.burn) bits.push(`burns for ${fx.burn[0]} turns (${fx.burn[1]} a turn)`);
    if (fx.root) bits.push(`roots for ${fx.root} turn${fx.root > 1 ? 's' : ''}`);
    if (fx.weak) bits.push(`weakens for ${fx.weak} turns (-30% damage)`);
    if (fx.mark) bits.push(`marks for ${fx.mark} turns (+25% damage taken)`);
    if (fx.knock) bits.push('knocks back 1 tile');
    return bits.length ? ' ' + cap1(bits.join(', ')) + '.' : '';
  }

  const VS_NAME = { structure: 'buildings and wagons', greenskin: 'orcs and goblins', big: 'huge foes', caster: 'spellcasters', spirit: 'spirits' };
  const vsName = (k) => VS_NAME[k] || k;

  // Bonus damage and armor piercing that belong to one act.
  function edgeText(a) {
    const bits = [];
    if (a.vs) for (const k in a.vs) bits.push(`+${pct(a.vs[k])} against ${vsName(k)}`);
    if (a.pierce) bits.push(`ignores ${pct(a.pierce)} of armor`);
    return bits.length ? ' ' + cap1(bits.join(', ')) + '.' : '';
  }

  function usesText(a) {
    if (!a.uses) return '';
    const left = a.left === Infinity || a.left == null ? a.uses : a.left;
    return ` ${left} of ${a.uses} use${a.uses > 1 ? 's' : ''} left.`;
  }

  // Plain-language rules text for one of a unit's acts.
  function actText(u, a) {
    const base = a.fixed != null ? Math.round(a.fixed * (a.dmg === 'magic' ? 1 + (u.props.magicMult || 0) : 1)) : Math.round(u.pow * (a.mult || 1));
    const dt = a.dmg === 'magic' ? 'magic' : 'physical';
    const ff = a.ff ? ' Hits allies too.' : '';
    let t;
    switch (a.kind) {
      case 'strike':
        t = a.dmg ? `${base} ${dt} damage to one enemy ${rangeText(a.range)}.` : `Targets one enemy ${rangeText(a.range)}.`;
        break;
      case 'cleave':
        t = `${base} ${dt} damage to every adjacent enemy.`;
        break;
      case 'quake':
        t = `${base} ${dt} damage to an adjacent enemy and every enemy beside it.`;
        break;
      case 'blast':
        t = `${a.dmg ? base + ' ' + dt + ' damage to' : 'Affects enemies in'} a ${a.pattern === 'square' ? '3x3' : '5-tile'} area ${rangeText(a.range)}.${ff}`;
        break;
      case 'line':
        t = `${base} ${dt} damage to every unit in a straight line up to ${a.len} tiles.${a.ff ? ' Hits allies too.' : ' Passes through allies.'}`;
        break;
      case 'cone':
        t = `${base} ${dt} damage across a cone ${a.len} tiles deep.${ff}`;
        break;
      case 'cross':
        t = `${base} ${dt} damage to enemies in all four directions, up to ${a.len} tiles.`;
        break;
      case 'nova':
        t = a.dmg ? `${base} ${dt} damage to every enemy within ${a.radius} tile${a.radius > 1 ? 's' : ''}.` : `Affects every enemy within ${a.radius} tile${a.radius > 1 ? 's' : ''}.`;
        break;
      case 'pray':
        t = `Heals ${E.healAmount(u, a)} HP to every ally within ${a.radius} tiles.${a.cleanse ? ' Also cures poison, burns, paralysis and roots.' : ''}`;
        break;
      case 'drum':
        t = `Allies within ${a.radius} tiles ${a.noHeal ? '' : 'heal ' + E.healAmount(u, a) + ' and '}fly into a frenzy: +25% damage for 2 turns.`;
        break;
      case 'heal':
        t = `Heals one ally ${rangeText(a.range)} for ${E.healAmount(u, a)}${a.cure ? ' and cures poison and burns' : ''}.`;
        break;
      case 'shield':
        t = `An ally ${rangeText(a.range)} gains a shield that absorbs ${a.amount || 15} damage.`;
        break;
      case 'rally':
        t = `Allies within ${a.radius} tiles take 1 turn off their cooldowns and shake off paralysis and roots.`;
        break;
      case 'grow':
        t = `Raises a shrub on an empty tile up to ${a.range[1]} tiles away. Up to ${3 + (u.props.shrubs || 0)} at once.`;
        break;
      case 'raise':
        t = `Raises a skeleton on an empty tile up to ${a.range[1]} tiles away, ${a.max || 3} at most. They crumble when it dies.`;
        break;
      case 'revive':
        t = `An ally that fell within ${a.range[1]} tiles rises again with ${Math.round((a.pct || 0.4) * 100)}% HP.`;
        break;
      case 'detonate':
        t = `Explodes: ${base} magic damage to everything next to it, friend or foe. It dies.`;
        break;
      case 'leap':
        t = `Leaps ${a.range[0]}-${a.range[1]} tiles over anything and strikes every adjacent enemy for ${base}.`;
        break;
      case 'blink':
        t = `Instead of walking, teleports up to ${a.range[1]} tiles. It can still attack afterward.`;
        break;
      case 'shadowstrike':
        t = `Teleports behind an enemy ${rangeText(a.range)} and strikes its back for ${base}.`;
        break;
      case 'hazard': {
        const where = a.range[1] === 0 ? 'around itself' : `${a.pattern === 'single' ? 'an empty tile' : 'a 5-tile area'} ${a.range[0] === 0 ? 'up to ' + a.range[1] + ' tiles away' : rangeText(a.range)}`;
        if (a.hz === 'smoke') t = `Smoke ${where} for ${a.turns} turns: units inside cannot be targeted from more than 1 tile away.`;
        else if (a.hz === 'fire') t = `Sets ${where} ablaze for ${a.turns} turns: enemies that enter it or start their turn in it take ${a.dmgFixed || 8}.`;
        else t = `Caltrops on ${where}: the first enemy to step there stops, takes 6 and is rooted.`;
        break;
      }
      default:
        t = UNITS[u.type].desc;
    }
    return t + edgeText(a) + fxText(u, a) + usesText(a);
  }

  // ------------------------------------------------------------ attack patterns

  const FRIENDLY_KINDS = new Set(['heal', 'shield', 'revive', 'pray', 'drum', 'rally', 'grow', 'raise', 'blink']);

  // A small top-down map of one attack, built from the engine's own geometry: the unit
  // (facing up), the tiles it can aim at, and everything a single use hits.
  function patternSVG(a, team) {
    if (!a || !a.kind || a.kind === 'none') return '';
    const N = 17;
    const ms = { w: N, h: N, terrain: new Array(N * N).fill(0), occ: new Array(N * N).fill(0), byId: {} };
    const ux = 8;
    const uy = 11;
    const r = a.range || [1, 1];
    const dist = r[0] === r[1] ? r[0] : Math.min(r[1], Math.max(r[0], Math.ceil((r[0] + r[1]) / 2)));
    const ring = (r0, r1) => E.radiusTiles(ms, ux, uy, r1, r0 === 0).filter(([x, y]) => E.manhattan(ux, uy, x, y) >= r0);
    const ahead = [ux, uy - dist];
    let reach = [];
    let hit = [];
    let aim = null;
    let land = null;
    switch (a.kind) {
      case 'strike':
      case 'heal':
      case 'shield':
      case 'revive':
      case 'grow':
      case 'raise':
        reach = ring(r[0], r[1]);
        aim = ahead;
        hit = [aim];
        break;
      case 'blast':
      case 'hazard':
        reach = ring(r[0], r[1]);
        aim = ahead;
        hit = E.patternTiles(ms, a.pattern || 'single', aim[0], aim[1]);
        break;
      case 'quake':
        reach = ring(r[0], r[1]);
        aim = ahead;
        hit = E.radiusTiles(ms, aim[0], aim[1], 1, true);
        break;
      case 'cleave':
        hit = E.radiusTiles(ms, ux, uy, 1);
        break;
      case 'line':
        hit = E.lineTiles(ms, ux, uy, 0, a.len);
        break;
      case 'cone':
        hit = E.coneTiles(ms, ux, uy, 0, a.len);
        break;
      case 'cross':
        for (let d = 0; d < 4; d++) hit.push(...E.lineTiles(ms, ux, uy, d, a.len));
        break;
      case 'nova':
      case 'detonate':
      case 'rally':
        hit = E.radiusTiles(ms, ux, uy, a.radius);
        break;
      case 'pray':
      case 'drum':
        hit = E.radiusTiles(ms, ux, uy, a.radius, true);
        break;
      case 'leap':
        reach = ring(r[0], r[1]);
        land = ahead;
        hit = E.radiusTiles(ms, land[0], land[1], 1);
        break;
      case 'blink':
        reach = ring(r[0], r[1]);
        land = ahead;
        break;
      case 'shadowstrike':
        reach = ring(r[0], r[1]);
        aim = ahead;
        hit = [aim];
        land = [aim[0], aim[1] - 1];
        break;
      default:
        return '';
    }
    const selfHit = a.kind === 'pray' || a.kind === 'drum';
    hit = hit.filter(([x, y]) => selfHit || x !== ux || y !== uy);
    // Crop to what matters, keeping the unit centered left to right.
    const all = [[ux, uy], ...reach, ...hit, ...(land ? [land] : [])];
    const half = Math.max(2, ...all.map(([x]) => Math.abs(x - ux))) + 1;
    const minX = ux - half;
    const maxX = ux + half;
    const minY = Math.min(...all.map(([, y]) => y)) - 1;
    const maxY = Math.max(uy + 1, ...all.map(([, y]) => y + 1));
    const cols = maxX - minX + 1;
    const rows = maxY - minY + 1;
    const cs = Math.max(5, Math.min(12, Math.floor(Math.min(96 / cols, 104 / rows))));
    const W = cols * cs;
    const H = rows * cs;
    const friendly = FRIENDLY_KINDS.has(a.kind);
    const key = (x, y) => x + ',' + y;
    const inReach = new Set(reach.map(([x, y]) => key(x, y)));
    const inHit = new Set(hit.map(([x, y]) => key(x, y)));
    const cell = (x, y, fill, extra) =>
      `<rect x="${(x - minX) * cs + 0.5}" y="${(y - minY) * cs + 0.5}" width="${cs - 1}" height="${cs - 1}" rx="${Math.max(1, cs * 0.18)}" fill="${fill}"${extra || ''}/>`;
    const parts = [];
    for (let y = minY; y <= maxY; y++)
      for (let x = minX; x <= maxX; x++) {
        const k = key(x, y);
        const fill = inHit.has(k)
          ? friendly ? '#5fcf68' : '#e2574c'
          : inReach.has(k)
            ? friendly ? 'rgba(110,220,140,0.3)' : 'rgba(255,120,100,0.32)'
            : 'rgba(255,255,255,0.07)';
        parts.push(cell(x, y, fill));
      }
    if (land) parts.push(cell(land[0], land[1], 'rgba(140,200,255,0.4)', ' stroke="#8cc8ff" stroke-width="1.4"'));
    if (aim) parts.push(cell(aim[0], aim[1], 'none', ' stroke="#fff6d8" stroke-width="1.2"'));
    const cx = (ux - minX + 0.5) * cs;
    const cy = (uy - minY + 0.5) * cs;
    const tc = team === 'E' ? '#ff5d52' : '#5ea2ff';
    const rr = cs * 0.34;
    parts.push(`<circle cx="${cx}" cy="${cy}" r="${rr}" fill="${tc}" stroke="#fff" stroke-width="1"/>`);
    parts.push(`<path d="M${cx - rr * 0.8} ${cy - rr * 0.9} L${cx} ${cy - rr * 2} L${cx + rr * 0.8} ${cy - rr * 0.9}Z" fill="#fff"/>`);
    return `<svg class="pattern" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(a.name)}: attack pattern">${parts.join('')}</svg>`;
  }

  const PATTERN_LEGEND = '<p class="small muted pattern-legend">Diagrams: the dot is the unit, facing up. Pale tiles: where it can aim. Bright tiles: what one use hits.</p>';

  const TRAIT_TEXT = {
    shadowstep: 'Slips through enemy units.',
    stoneskin: 'Immune to poison and paralysis.',
    flying: 'Flies over units, water, lava and rocks.',
    immobile: 'Rooted in place: cannot move.',
    shieldwall: 'Full block from the sides.',
    retaliate: 'Strikes back for half power when hit in melee.',
    bloodrage: 'Cleave heals 5 HP per enemy struck.',
    bloodlust: 'Slaying an enemy resets its cooldown: it is ready again next turn.',
    secondwind: 'Once per battle, survives a fatal blow with 1 HP.',
    phoenix: 'The first time it falls, it rises again with half HP.',
    steadfast: 'Immune to paralysis, roots and knockback.',
    poisonproof: 'Immune to poison.',
    paraproof: 'Immune to paralysis.',
    undead: 'Undead: immune to poison.',
    aura_barrier: 'Barrier Aura: allies within reach gain +25% magic resistance and are immune to poison and paralysis.',
    aegisfield: 'Its aura also softens physical blows by 15%.',
    steelfield: 'Its aura also grants +10% armor.',
    auramend: 'Allies in its aura heal 3 HP at the start of each of its turns.',
    purge: 'Allies in its aura are cured of roots and burns at the start of each of its turns.',
    thornwall: 'Its shrubs are tougher and prick melee attackers.',
    ironwood: 'Its shrubs have 40% armor and magic resistance.',
    ridedown: 'After moving 3 or more tiles, its Lance knocks the target back.',
    stormcaller: 'At the start of each of its turns, lightning strikes the nearest enemy within 3 tiles for 5.',
    midas: 'Every enemy it slays earns 6 gold.',
    thunderstep: 'Enemies next to where it stops moving take 6 magic damage.',
    volatile: 'Explodes when destroyed, hurting everything next to it.',
    trollblood: 'Regenerates unless magic or fire hurt it since its last turn.',
    cart: `Rolls ${UNITS.cart.move} tile${UNITS.cart.move > 1 ? 's' : ''} toward the left edge after every enemy turn, and escapes there.`,
    big: 'Huge: cannot be knocked back.',
    martyr: 'When it falls, heals allies within 2 tiles for 20.',
    structure: 'A structure: it does not need to fall for a rout.',
    spawner: 'Sends reinforcements every few turns until it is destroyed.',
  };

  const MATERIAL_TEXT = {
    stone: 'Stone building: resists swords and spells alike. Siege damage breaks it fast.',
    wood: 'Wooden building: fire and magic deal extra damage to it.',
    arcane: 'Arcane rift: steel barely scratches it, but magic unravels it.',
    iron: 'Iron building: siege damage breaks it fastest.',
  };

  // s, when given, adds what a building still has to send.
  function traitLines(u, s) {
    const out = [];
    const mat = UNITS[u.type].material;
    if (mat && MATERIAL_TEXT[mat]) out.push(MATERIAL_TEXT[mat]);
    for (const t of u.traits) if (TRAIT_TEXT[t]) out.push(TRAIT_TEXT[t]);
    const P = u.props;
    if (P.totemHeal) out.push(`At the start of their turn, its allies within 2 tiles heal ${P.totemHeal} HP.`);
    if (s && u.traits.has('spawner')) {
      const waves = s.waves.filter((w) => w.src === u.uid && w.state === 'pending');
      if (waves.length) {
        const n = waves.reduce((t, w) => t + w.units.length, 0);
        const next = waves[0];
        out.push(`${n} more on the way. Next: ${next.units.map((x) => UNITS[x.type].name).join(', ')} at the end of turn ${next.turn}.`);
      } else out.push('It has nobody left to send.');
    }
    if (P.guard) out.push(`Adjacent allies take ${pct(P.guard)} less damage.`);
    if (P.magicGuard) out.push(`Adjacent allies take ${pct(P.magicGuard)} less magic damage.`);
    if (P.regen) out.push(`Heals ${P.regen} HP at the start of each of its turns.`);
    if (P.lifesteal) out.push(`Heals for ${pct(P.lifesteal)} of the damage it deals.`);
    if (P.thorns) out.push(`Melee attackers take ${P.thorns} damage.`);
    if (P.backMult) out.push(`+${pct(P.backMult)} damage from behind.`);
    if (P.flankMult) out.push(`+${pct(P.flankMult)} damage from the side or behind.`);
    if (P.chargeMult) out.push(`Charge: +${pct(P.chargeMult)} damage after moving 3 or more tiles.`);
    if (P.execMult) out.push(`+${pct(P.execMult)} damage to targets below half HP.`);
    if (P.rageMult) out.push(`+${pct(P.rageMult)} damage while below half HP.`);
    if (P.pierce) out.push(`Ignores ${pct(P.pierce)} of armor.`);
    if (P.packMult) out.push(`+${pct(P.packMult)} damage when an ally flanks the same target.`);
    if (P.bonusMagic) out.push(`Hits deal ${P.bonusMagic} bonus magic damage.`);
    if (P.dmgMult) out.push(`+${pct(P.dmgMult)} damage.`);
    if (P.vs) for (const k in P.vs) out.push(`+${pct(P.vs[k])} damage against ${vsName(k)}.`);
    if (P.vsArmored) out.push(`+${pct(P.vsArmored)} damage against armored targets.`);
    if (u.boss) out.push('Boss: immune to paralysis and knockback.');
    return [...new Set(out)];
  }

  function hpClass(f) {
    return f > 0.5 ? '' : f > 0.25 ? 'mid' : 'low';
  }

  function statusChips(u) {
    const chips = [];
    if (u.para > 0) chips.push(`<span class="chip warn">Paralyzed ${u.para}</span>`);
    if (u.poison) chips.push(`<span class="chip good">Poisoned ${u.poison.turns}</span>`);
    if (u.burn) chips.push(`<span class="chip warn">Burning ${u.burn.turns}</span>`);
    if (u.root > 0) chips.push(`<span class="chip good">Rooted ${u.root}</span>`);
    if (u.weak > 0) chips.push(`<span class="chip magic">Weakened ${u.weak}</span>`);
    if (u.mark > 0) chips.push(`<span class="chip bad">Marked ${u.mark}</span>`);
    if (u.frenzy > 0) chips.push(`<span class="chip bad">Frenzy ${u.frenzy}</span>`);
    if (u.shield > 0) chips.push(`<span class="chip">${ic('shield')} Shield ${u.shield}</span>`);
    return chips;
  }

  function unitInfoHTML(u, opts) {
    const o = opts || {};
    const T = UNITS[u.type];
    const f = u.hp / u.maxHp;
    const chips = [];
    if (o.status) {
      const B = UI.battle;
      const acting = B && B.s.act && B.s.act.uid === u.uid;
      chips.push(...statusChips(u));
      if (acting) chips.push('<span class="chip warn">Acting</span>');
      else if (u.wait > 0) chips.push(`<span class="chip">${ic('hourglass')} Cooldown ${u.wait}</span>`);
      else if (!u.nonCombat && u.para === 0 && u.team === (B && B.s.side)) chips.push('<span class="chip good">Ready</span>');
    }
    if (u.enchant) chips.push(`<span class="chip magic">${ic('gem')} ${esc(ENCHANTS[u.enchant].name)}</span>`);
    return `<div class="unitcard">
      <canvas class="portrait" data-p="${u.type}:${u.team}"></canvas>
      <div class="name"><b class="team-${u.team}">${esc(o.name || u.name)}</b><span class="stars">${stars(u.level)}</span>
        <span class="small muted">${T.name !== (o.name || u.name) ? esc(T.name) : ''}${u.level ? ' · Lv ' + u.level : ''}</span></div>
      <div class="hp"><div class="hpbar ${hpClass(f)}"><i style="width:${Math.round(f * 100)}%"></i></div><span>${u.hp}/${u.maxHp}</span></div>
    </div>
    ${chips.length ? `<div class="chips">${chips.join('')}</div>` : ''}`;
  }

  // The attack and every active ability of a unit, as rules text with a pattern diagram.
  function actsHTML(u) {
    const rows = u.acts.map((a, i) => actRow(u, a, i > 0));
    return rows.join('') + (u.acts.some((a) => a.kind !== 'none') ? PATTERN_LEGEND : '');
  }

  function actRow(u, a, ability) {
    return `<div class="act-row">${patternSVG(a, u.team)}<p class="ability"><b>${a.dmg ? dmgIcon(a.dmg) : ''}${esc(a.name)}${ability ? ' <span class="tag">ability</span>' : ''}.</b> ${esc(actText(u, a))}</p></div>`;
  }

  function levelBadge(lv) {
    return `<span class="lvl lv${lv}">Lv${lv}</span>`;
  }

  function resbar(run) {
    const li = R.levelInfo(run);
    const frac = li.max ? 1 : (li.xp - li.from) / (li.to - li.from);
    return `<div class="resbar">
      <span class="res gold" title="Gold">${ic('gold')}<span class="num">${run.gold}</span></span>
      <button class="res cmdlv" data-cmd title="Commander level">${ic('crown')}<span class="num">Lv ${li.lv}</span>
        <span class="xpbar"><i style="width:${Math.round(frac * 100)}%"></i></span></button>
      <span class="res" title="Supply each battle">${ic('command')}<span class="num">${R.supplyFor(run)}</span></span>
      <span class="res" title="Units allowed on the field">${ic('army')}<span class="num">${R.unitCap(run)}</span></span>
    </div>`;
  }

  function commanderSheet() {
    const run = UI.run;
    const li = R.levelInfo(run);
    const rows = COMMAND.slice(1)
      .map((c, i) => {
        const lv = i + 1;
        return `<tr class="${lv === li.lv ? 'cur' : lv < li.lv ? 'past' : ''}"><td>${lv}</td><td>${c.xp}</td><td>${c.supply}</td><td>${c.cap}</td></tr>`;
      })
      .join('');
    openSheet(
      `${sheetHead('Commander level', `${li.max ? 'Maximum level reached.' : `${li.xp} XP · ${li.to - li.xp} XP to level ${li.lv + 1}`}`)}
      <p class="muted">Victories earn XP. Each commander level raises the Supply you can spend in every battle, and sometimes how many units may take the field. Elites, bosses and bonus goals pay more XP.</p>
      <table class="lvtable"><thead><tr><th>Level</th><th>XP</th><th>Supply</th><th>Units</th></tr></thead><tbody>${rows}</tbody></table>
      <p class="small muted">Right now: ${R.supplyFor(run)} Supply and ${R.unitCap(run)} units, after relics and bonuses.</p>
      <div class="actions"><button class="btn primary" data-close>Got it</button></div>`
    );
  }

  function bindResbar(el) {
    for (const b of $$('[data-cmd]', el)) b.addEventListener('click', () => commanderSheet());
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
    bindResbar(v);
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
    // Hiding the battle screen restarts a CSS animation, so a finished banner
    // would replay over the next War Room.
    b.onanimationend = clearBanner;
  }

  function clearBanner() {
    $('#banner').className = 'banner';
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
      { uid: 1, type: 'knight', team: 'P', x: 2, y: 3, facing: 0, hp: 52, maxHp: 52, level: 2 },
      { uid: 2, type: 'archer', team: 'P', x: 3, y: 4, facing: 0, hp: 34, maxHp: 34 },
      { uid: 3, type: 'pyromancer', team: 'P', x: 1, y: 4, facing: 0, hp: 28, maxHp: 28 },
      { uid: 4, type: 'orc', team: 'E', x: 2, y: 2, facing: 2, hp: 46, maxHp: 46 },
      { uid: 5, type: 'brute', team: 'E', x: 3, y: 1, facing: 2, hp: 64, maxHp: 64 },
      { uid: 6, type: 'goblin_archer', team: 'E', x: 1, y: 0, facing: 2, hp: 22, maxHp: 22 },
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
        b.projectile([3, 4], [3, 1], 'arrow', 320).then(() => b.addText(3, 1, '13', '#fff', { height: 52 }));
      } else if (k === 1) {
        const v = b.vis.get(1);
        b.tween(120, (t) => (v.oy = -t * b.th * 0.35)).then(() => {
          b.addText(2, 2, 'BLOCK', '#a9d1ff', { height: 43 });
          b.tween(140, (t) => (v.oy = -(1 - t) * b.th * 0.35));
        });
      } else {
        b.projectile([1, 4], [2, 1], 'fire', 420).then(() => {
          b.flashTiles([[2, 1], [1, 1], [3, 1], [2, 0], [2, 2]], 'rgba(255,140,40,ALPHA)', 420);
          b.addText(3, 1, '18', '#d7b4ff', { height: 52 });
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
    const pendingBattle = run && run.pending && run.pending.type === 'battle';
    const v = showView(
      `<div class="wrap">
        <div class="title-grid">
          <div class="wrap" style="margin:0;gap:14px">
            <p class="eyebrow">A tactics roguelike</p>
            <h1 class="wordmark">Arena<br>Gauntlet</h1>
            <p class="tagline">Scout the enemy, spend your Supply on the perfect counter, and fight through three acts of isometric battles. Lose, re-plan, and try again.</p>
            <div class="title-actions">
              ${run ? `<button class="btn primary" id="tCont">${ic('flag')} Continue · ${ACTS[run.act].short}${pendingBattle ? ' · ' + esc(run.pending.enc.name) : ''}</button>` : ''}
              <button class="btn ${run ? '' : 'primary'}" id="tNew">${ic('swords')} New campaign</button>
              <div class="row"><button class="btn grow" id="tHelp">${ic('help')} How to play</button>
              <button class="btn grow" id="tCodex">${ic('book')} Codex</button></div>
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
    const itemName = ([kind, id]) => (kind === 'skill' ? SKILLS[id] : GEAR[id]).name;
    const render = () => {
      const v = showView(
        `<div class="wrap">
          <div class="row"><button class="btn ghost" id="ncBack">Back</button></div>
          <div><p class="eyebrow">New campaign</p><h2>Choose your warband</h2></div>
          <p class="muted">You start with 5 units, ${COMMAND[1].supply} Supply per battle and room for ${COMMAND[1].cap} units on the field. Choose wisely who fights.</p>
          <div class="choice-grid">${WARBANDS.map(
            (w) => `<button class="card ${w.id === wb ? 'selected' : ''}" data-wb="${w.id}">
              <div class="unit-strip">${w.units.map((t) => `<canvas data-p="${t}:P"></canvas>`).join('')}</div>
              <div class="title">${esc(w.name)}</div>
              <div class="desc">${esc(w.desc)}</div>
              <div class="small">${w.units.map((t) => UNITS[t].name).join(', ')}</div>
              <div class="chips"><span class="chip magic">${ic('gem')} ${esc(RELICS[w.relic].name)}</span>${(w.items || []).map((it) => `<span class="chip">${ic(it[0] === 'skill' ? 'scroll' : 'sword')} ${esc(itemName(it))}</span>`).join('')}<span class="chip warn">${ic('gold')} ${w.gold}</span></div>
            </button>`
          ).join('')}</div>
          <h3>Difficulty</h3>
          <div class="seg">${DIFFICULTIES.map(
            (d) => `<button class="card ${d.id === diff ? 'selected' : ''}" data-diff="${d.id}"><div class="title" style="font-size:1.15rem">${d.name}</div><div class="desc small">${esc(d.desc)}</div></button>`
          ).join('')}</div>
          <button class="btn primary wide" id="ncGo">${ic('swords')} March to the Borderlands</button>
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
        if (!UI.prefs.seenHelp2) {
          UI.prefs.seenHelp2 = true;
          savePrefs();
          helpSheet();
        }
      };
    };
    render();
  }

  // ------------------------------------------------------------ map

  const NODE_INFO = {
    battle: { icon: 'swords', name: 'Battle', desc: 'A standard enemy warband. Victory pays XP, gold and spoils.' },
    elite: { icon: 'skull', name: 'Elite', desc: 'A tougher warband. Pays more XP and a relic.' },
    event: { icon: 'event', name: 'Unknown', desc: 'Something waits on the road.' },
    shop: { icon: 'bag', name: 'Merchant', desc: 'Recruits, skills, gear, enchantments and relics for gold.' },
    rest: { icon: 'fire', name: 'Campfire', desc: 'Drill for XP, study a skill, or tinker with gear.' },
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
    const bossName = UNITS[R.bossOf(run)].name;
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
        ${n.id === 'boss' ? `<text y="${r + 18}" text-anchor="middle" font-family="Grenze Gotisch, Georgia, serif" font-size="17" fill="#5b3417">${esc(bossName)}</text>` : ''}
        <circle r="${r + 10}" fill="transparent"/>
      </g>`;
    }
    return `<svg class="mapsvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Campaign map">${lines}${nodes}</svg>`;
  }

  function nodeDesc(run, n) {
    const info = NODE_INFO[n.kind];
    if (n.kind === 'boss') {
      const b = UNITS[R.bossOf(run)];
      return `${b.name}. ${b.desc}`;
    }
    if (n.kind === 'battle' || n.kind === 'elite') return `${info.desc} Victory: +${R.battleXp(run, n.kind)} XP.`;
    return info.desc;
  }

  function mapFoot(run) {
    const n = UI.mapSel && R.getNode(run, UI.mapSel);
    if (!n) return `<span class="muted grow">Tap a glowing stop on the map to choose your path.</span>`;
    const info = NODE_INFO[n.kind];
    return `<div class="grow" style="min-width:0"><b>${info.name}</b><div class="small muted">${esc(nodeDesc(run, n))}</div></div>
      <button class="btn primary" id="mGo">${ic(info.icon)} Enter</button>`;
  }

  function mapScreen() {
    const run = UI.run;
    UI.battle = null;
    UI.wr = null;
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
    for (const g of $$('[data-node]', v)) {
      const pick = () => {
        const id = g.dataset.node;
        if (!avail.includes(id)) {
          const n = R.getNode(run, id);
          toast(NODE_INFO[n.kind].name + ': ' + nodeDesc(run, n));
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
        <button class="btn wide" id="muCodex">${ic('book')} Codex</button>
        <button class="btn wide" id="muSound">${ic(AG.Audio.enabled ? 'sound' : 'mute')} Sound: ${AG.Audio.enabled ? 'on' : 'off'}</button>
        <button class="btn wide" id="muFacing">${ic('rotate')} Facing: ${UI.prefs.manualFacing ? 'you pick it with arrows' : 'toward the nearest enemy'}</button>
        ${inBattle ? `<button class="btn wide danger" id="muRetreat">${ic('flag')} Retreat and re-plan</button>` : ''}
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
        $('#muFacing', sh).onclick = () => {
          UI.prefs.manualFacing = !UI.prefs.manualFacing;
          savePrefs();
          menuSheet(inBattle);
        };
        $('#muTitle', sh).onclick = () => {
          closeSheet();
          if (UI.board) UI.board.stop();
          UI.battle = null;
          UI.wr = null;
          title();
        };
        if ($('#muRetreat', sh))
          $('#muRetreat', sh).onclick = async () => {
            closeSheet();
            if (!(await confirmSheet('Retreat?', 'The battle counts as lost. You go back to the war room to change your army and try again, as many times as you like.', 'Retreat', 'Keep fighting', true))) return;
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

  function relicCard(id, attrs) {
    const r = RELICS[id];
    return `<button class="card" ${attrs || ''}><div class="kind">${ic('gem')} Relic · ${r.tier}</div><div class="title">${esc(r.name)}</div><div class="desc">${esc(r.desc)}</div></button>`;
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

  // ------------------------------------------------------------ army and items

  function itemKindLabel(it) {
    return it.kind === 'skill' ? 'Skill' : it.kind === 'gear' ? 'Gear' : 'Enchantment scroll';
  }

  function itemCost(it) {
    const d = R.itemDef(it);
    return it.kind === 'scroll' ? `+${d.surcharge} Supply on its unit` : `${d.cost} Supply`;
  }

  function armySheet(after, tab) {
    const run = UI.run;
    const t = tab || UI.armyTab || 'units';
    UI.armyTab = t;
    let body = '';
    if (t === 'units') {
      body = `<div class="army-list">${run.roster
        .map((r) => {
          const deployed = UI.wr && UI.wr.dep.has(r.id);
          return `<button class="army-row" data-rid="${r.id}">
            <canvas class="portrait" data-p="${r.type}:P"></canvas>
            <div class="nm" style="min-width:0"><b>${esc(r.name)}</b> ${levelBadge(r.load.lv)}
              <div class="small muted">${esc(UNITS[r.type].name)} · ${esc(ABILITIES[r.load.a1].name)}${r.load.lv >= 2 ? ' · ' + esc(ABILITIES[r.load.a2].name) : ''}</div></div>
            <div class="chips" style="justify-content:flex-end">${r.enchant ? `<span class="chip magic">${ic('gem')} ${esc(ENCHANTS[r.enchant].name)}</span>` : ''}${deployed ? '<span class="chip good">Deployed</span>' : ''}
              <span class="chip warn">${ic('command')} ${R.unitCost(run, r)}</span></div></button>`;
        })
        .join('')}</div>`;
    } else if (t === 'items') {
      const group = (kind, title) => {
        const list = run.items.filter((i) => i.kind === kind);
        if (!list.length) return '';
        return `<div class="eyebrow">${title}</div><div class="army-list">${list
          .map((it) => {
            const d = R.itemDef(it);
            const holder = R.itemHolder(run, it.uid);
            return `<button class="army-row item-row" data-item="${it.uid}">
              <div class="itemico ${kind}">${ic(kind === 'skill' ? 'scroll' : kind === 'gear' ? 'sword' : 'gem')}</div>
              <div class="nm" style="min-width:0"><b>${esc(d.name)}</b><div class="small muted">${esc(d.desc)}</div></div>
              <div class="chips" style="justify-content:flex-end"><span class="chip warn">${esc(itemCost(it))}</span>${holder ? `<span class="chip good">${esc(holder.name)}</span>` : kind === 'scroll' ? '<span class="chip magic">Bind</span>' : '<span class="chip">Free</span>'}</div></button>`;
          })
          .join('')}</div>`;
      };
      body =
        group('skill', 'Skills') + group('gear', 'Gear') + group('scroll', 'Enchantment scrolls') ||
        '<p class="muted">No skills, gear or scrolls yet. Win battles, visit merchants, rest at campfires and explore events to find them.</p>';
    } else {
      body = `<div class="army-list">${run.relics
        .map((id) => `<div class="card"><div class="kind">${ic('gem')} ${RELICS[id].tier}</div><div class="title">${esc(RELICS[id].name)}</div><div class="desc">${esc(RELICS[id].desc)}</div></div>`)
        .join('')}</div>`;
    }
    openSheet(
      `${sheetHead('Your army', `${run.roster.length}/${R.MAX_ROSTER} units · ${ic('gold')} ${run.gold} gold · Commander Lv ${R.commanderLevel(run)}`)}
      <div class="tabs"><button class="btn ${t === 'units' ? 'on' : ''}" data-tab="units">${ic('army')} Units</button>
        <button class="btn ${t === 'items' ? 'on' : ''}" data-tab="items">${ic('bag')} Items (${run.items.length})</button>
        <button class="btn ${t === 'relics' ? 'on' : ''}" data-tab="relics">${ic('gem')} Relics</button></div>
      ${t === 'units' ? '<p class="small muted">Tap a unit to set its level, abilities, skills and gear. Loadouts carry over between battles.</p>' : ''}
      ${body}`,
      (sh) => {
        for (const b of $$('[data-tab]', sh)) b.onclick = () => armySheet(after, b.dataset.tab);
        for (const b of $$('[data-rid]', sh)) b.onclick = () => loadoutSheet(b.dataset.rid, () => armySheet(after));
        for (const b of $$('[data-item]', sh)) b.onclick = () => itemSheet(b.dataset.item, () => armySheet(after, 'items'));
      }
    );
    UI.onSheetClose = after || null;
  }

  function itemSheet(uid, back) {
    const run = UI.run;
    const it = R.itemByUid(run, uid);
    if (!it) return back && back();
    const d = R.itemDef(it);
    const holder = R.itemHolder(run, uid);
    const after = UI.onSheetClose;
    openSheet(
      `${sheetHead(esc(d.name), `${itemKindLabel(it)} · ${esc(itemCost(it))}`)}
      <p>${esc(d.desc)}</p>
      ${d.req ? `<p class="small muted">Only for units that ${{ damage: 'deal damage', phys: 'deal physical damage', magic: 'use magic', ranged: 'attack at range', mobile: 'can move', facing: 'have a facing', slow: 'have a cooldown of 3 or more', recovers: 'have a cooldown of 2 or more' }[d.req] || 'qualify'}.</p>` : ''}
      ${it.kind === 'scroll'
        ? `<p class="hint warn">Binding is permanent: the enchantment stays with that unit for the rest of the campaign and adds ${d.surcharge} Supply to its cost. A unit can hold only one enchantment.</p>`
        : `<p class="small muted">${holder ? `Slotted into ${esc(holder.name)}.` : 'Not slotted into anyone. Equip it from a unit\'s loadout.'}</p>`}
      <div class="actions">
        ${it.kind === 'scroll' ? `<button class="btn primary" id="isBind">${ic('gem')} Bind to a unit</button>` : ''}
        ${holder ? `<button class="btn" id="isFree">Unequip from ${esc(holder.name)}</button>` : ''}
        <button class="btn" id="isBack">Back</button>
      </div>`,
      (sh) => {
        if ($('#isBind', sh))
          $('#isBind', sh).onclick = async () => {
            UI.onSheetClose = null;
            const rid = await pickUnit('Bind ' + d.name, 'Choose a unit without an enchantment. This cannot be undone.', (u) => !u.enchant && D.eligible(u.type, d));
            if (!rid) return itemSheet(uid, back);
            const r = R.unitById(run, rid);
            UI.onSheetClose = null;
            if (!(await confirmSheet(`Bind ${d.name} to ${r.name}?`, `${esc(d.desc)} It is permanent, and fielding ${esc(r.name)} will cost ${d.surcharge} more Supply.`, 'Bind forever', 'Not yet'))) return itemSheet(uid, back);
            if (R.applyScroll(run, uid, rid)) {
              sfx('coin');
              toast(`${r.name} is now bound with ${d.name}.`);
              if (UI.wr) renderWarRoom();
            }
            UI.onSheetClose = after;
            back && back();
          };
        if ($('#isFree', sh))
          $('#isFree', sh).onclick = () => {
            R.unassignItem(run, uid);
            R.save(run);
            if (UI.wr) renderWarRoom();
            itemSheet(uid, back);
          };
        $('#isBack', sh).onclick = () => back && back();
      }
    );
    UI.onSheetClose = after;
  }

  // ------------------------------------------------------------ loadout editor

  function abilityCard(r, tier, id, locked) {
    const ab = ABILITIES[id];
    const on = r.load[tier === 1 ? 'a1' : 'a2'] === id;
    // Show the shape of a new active, or of the main attack when the pick reshapes it.
    const m = ab.mod;
    const shape = m.active ? m.active : m.act && (m.act.kind || m.act.pattern) ? Object.assign({}, UNITS[r.type].act, m.act) : null;
    return `<button class="pick ${on ? 'on' : ''} ${locked ? 'locked' : ''}" data-ab="${tier}:${id}">
      <span class="pk-head"><b>${esc(ab.name)}</b><span class="cost">${ab.cost ? '+' + ab.cost : 'free'}</span></span>
      <span class="pk-body">${shape ? patternSVG(shape, 'P') : ''}<span class="pk-desc">${esc(ab.desc)}</span></span></button>`;
  }

  function slotButton(run, r, kind, i) {
    const key = kind === 'skill' ? 'skills' : 'gear';
    const uid = r.load[key][i];
    const it = uid && R.itemByUid(run, uid);
    const d = it && R.itemDef(it);
    return `<button class="slot ${d ? 'full' : ''}" data-slot="${kind}:${i}">
      <span class="itemico ${kind}">${ic(kind === 'skill' ? 'scroll' : 'sword')}</span>
      <span class="sl-body">${d ? `<b>${esc(d.name)}</b><span class="small muted">${esc(d.desc)}</span>` : `<b class="muted">Empty ${kind} slot</b><span class="small muted">Tap to equip</span>`}</span>
      ${d ? `<span class="cost">+${d.cost}</span>` : ''}</button>`;
  }

  // Edit one unit's level, ability picks, skills and gear. Costs update live.
  function loadoutSheet(rid, back) {
    const run = UI.run;
    const r = R.unitById(run, rid);
    if (!r) return back && back();
    R.normalizeLoad(run, r);
    const T = UNITS[r.type];
    const L = r.load;
    const u = R.unitStats(run, r, 'P');
    const cost = R.unitCost(run, r);
    const wr = UI.wr && UI.run.pending && UI.run.pending.type === 'battle' ? UI.wr : null;
    const after = UI.onSheetClose;
    let budget = '';
    if (wr) {
      const used = wrUsed();
      const deployed = wr.dep.has(rid);
      const total = deployed ? used : used + cost;
      budget = `<div class="budget ${total > wr.supply ? 'over' : ''}">${ic('command')} ${deployed ? 'Army' : 'Army with this unit'}: <b>${total}/${wr.supply}</b> Supply${total > wr.supply ? ' · over budget' : ''}</div>`;
    }
    const lvBtn = (lv) => `<button class="btn ${L.lv === lv ? 'on' : ''}" data-lv="${lv}"><b>Lv ${lv}</b><span>${lv === 1 ? 'base' : '+' + LEVEL_COST[lv]}</span></button>`;
    const sl = R.slotsFor(L.lv);
    const scrolls = run.items.filter((i) => i.kind === 'scroll' && D.eligible(r.type, ENCHANTS[i.id]));
    const breakdown = R.costBreakdown(run, r)
      .map((x) => `<tr><td>${esc(x.label)}</td><td>${x.cost ? x.cost : 'free'}</td></tr>`)
      .join('');
    const html = `${sheetHead(esc(r.name), `${esc(T.name)} · fielding costs <b class="cost-big">${cost}</b> Supply`)}
      ${budget}
      ${unitInfoHTML(u, { name: r.name })}
      ${statsHTML(u)}
      <div class="lo-sec"><div class="eyebrow">Level</div>
        <div class="lv-seg">${lvBtn(1)}${lvBtn(2)}${lvBtn(3)}</div>
        <p class="small muted">Level 2: +20% HP, +15% power, a second ability and a second skill slot. Level 3: +40% HP, +30% power, its Mastery and a second gear slot.</p></div>
      <div class="lo-sec"><div class="eyebrow">Ability · pick 1 of 3</div>
        <div class="picks">${T.abilities[1].map((id) => abilityCard(r, 1, id, false)).join('')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Level 2 ability · pick 1 of 3${L.lv < 2 ? ' <span class="lockline">unlocks at Level 2</span>' : ''}</div>
        <div class="picks">${T.abilities[2].map((id) => abilityCard(r, 2, id, L.lv < 2)).join('')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Mastery${L.lv < 3 ? ' <span class="lockline">unlocks at Level 3</span>' : ''}</div>
        <div class="pick static ${L.lv < 3 ? 'locked' : 'on'}"><span class="pk-head"><b>${esc(MASTERY[r.type].name)}</b></span><span class="pk-desc">${esc(MASTERY[r.type].desc)}</span></div></div>
      <div class="lo-sec"><div class="eyebrow">Skills · ${sl.skills} slot${sl.skills > 1 ? 's' : ''}</div>
        <div class="slots">${[...Array(SKILL_SLOTS[3]).keys()].map((i) => (i < sl.skills ? slotButton(run, r, 'skill', i) : `<div class="slot locked"><span class="itemico skill">${ic('scroll')}</span><span class="sl-body"><b class="muted">Skill slot</b><span class="small muted">Unlocks at Level 2</span></span></div>`)).join('')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Gear · ${sl.gear} slot${sl.gear > 1 ? 's' : ''}</div>
        <div class="slots">${[...Array(GEAR_SLOTS[3]).keys()].map((i) => (i < sl.gear ? slotButton(run, r, 'gear', i) : `<div class="slot locked"><span class="itemico gear">${ic('sword')}</span><span class="sl-body"><b class="muted">Gear slot</b><span class="small muted">Unlocks at Level 3</span></span></div>`)).join('')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Enchantment</div>
        ${r.enchant
          ? `<div class="pick static on ench"><span class="pk-head"><b>${ic('gem')} ${esc(ENCHANTS[r.enchant].name)}</b><span class="cost">+${ENCHANTS[r.enchant].surcharge}</span></span><span class="pk-desc">${esc(ENCHANTS[r.enchant].desc)} Bound for good.</span></div>`
          : `<p class="small muted">None. ${scrolls.length ? `You have ${scrolls.length} scroll${scrolls.length > 1 ? 's' : ''} that could be bound to this unit.` : 'Enchantment scrolls bind a permanent power to one unit.'}</p>
            ${scrolls.length ? `<button class="btn" id="loBind">${ic('gem')} Bind a scroll…</button>` : ''}`}</div>
      <div class="lo-sec"><div class="eyebrow">In battle</div>${actsHTML(u)}
        ${traitLines(u).length ? `<ul class="tips">${traitLines(u).map((t) => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}</div>
      <div class="lo-sec"><div class="eyebrow">Supply cost</div><table class="costtable">${breakdown}<tr class="tot"><td>Total</td><td>${cost}</td></tr></table></div>
      <p class="small muted">Battles: ${r.battles} · Enemies slain: ${r.kills}</p>
      <div class="actions">
        <button class="btn" id="loDismiss" ${run.roster.length <= 2 ? 'disabled' : ''}>Dismiss (+15 gold)</button>
        <button class="btn primary" id="loDone">${ic('check')} Done</button>
      </div>`;
    const changed = () => {
      R.save(run);
      if (UI.wr) renderWarRoom();
      sfx('click');
      loadoutSheet(rid, back);
    };
    refreshSheet(html, (sh) => {
      for (const b of $$('[data-lv]', sh))
        b.onclick = () => {
          R.setLevel(run, rid, +b.dataset.lv);
          changed();
        };
      for (const b of $$('[data-ab]', sh))
        b.onclick = () => {
          const [tier, id] = b.dataset.ab.split(':');
          if (+tier === 2 && L.lv < 2) toast('This pick applies once the unit is Level 2.');
          R.setAbility(run, rid, +tier, id);
          changed();
        };
      for (const b of $$('[data-slot]', sh))
        b.onclick = () => {
          const [kind, i] = b.dataset.slot.split(':');
          itemPicker(rid, kind, +i, () => loadoutSheet(rid, back));
        };
      if ($('#loBind', sh))
        $('#loBind', sh).onclick = async () => {
          const pick = scrolls.length === 1 ? scrolls[0] : null;
          if (pick) return bindFlow(pick.uid, rid, () => loadoutSheet(rid, back));
          openSheet(
            `${sheetHead('Choose a scroll')}<div class="army-list">${scrolls
              .map((s) => `<button class="army-row" data-sc="${s.uid}"><div class="itemico scroll">${ic('gem')}</div><div class="nm"><b>${esc(ENCHANTS[s.id].name)}</b><div class="small muted">${esc(ENCHANTS[s.id].desc)}</div></div><span class="chip warn">+${ENCHANTS[s.id].surcharge}</span></button>`)
              .join('')}</div><div class="actions"><button class="btn" id="scBack">Back</button></div>`,
            (s2) => {
              for (const b of $$('[data-sc]', s2)) b.onclick = () => bindFlow(b.dataset.sc, rid, () => loadoutSheet(rid, back));
              $('#scBack', s2).onclick = () => loadoutSheet(rid, back);
            }
          );
        };
      $('#loDismiss', sh).onclick = async () => {
        UI.onSheetClose = null;
        const ok = await confirmSheet('Dismiss ' + r.name + '?', 'They leave your army for good, and their skills and gear return to your pack. You get 15 gold.', 'Dismiss', 'Keep', true);
        if (ok && R.dismiss(run, rid)) {
          R.save(run);
          if (UI.wr) {
            UI.wr.dep.delete(rid);
            UI.wr.sel = null;
            renderWarRoom();
          }
          UI.onSheetClose = after;
          return back ? back() : closeSheet();
        }
        UI.onSheetClose = after;
        loadoutSheet(rid, back);
      };
      $('#loDone', sh).onclick = () => (back ? back() : closeSheet());
    });
    UI.onSheetClose = after;
  }

  async function bindFlow(uid, rid, back) {
    const run = UI.run;
    const it = R.itemByUid(run, uid);
    const r = R.unitById(run, rid);
    const d = ENCHANTS[it.id];
    const after = UI.onSheetClose;
    UI.onSheetClose = null;
    const ok = await confirmSheet(`Bind ${d.name} to ${r.name}?`, `${esc(d.desc)} This is permanent, and fielding ${esc(r.name)} will cost ${d.surcharge} more Supply.`, 'Bind forever', 'Not yet');
    UI.onSheetClose = after;
    if (ok && R.applyScroll(run, uid, rid)) {
      sfx('coin');
      toast(`${r.name} is now bound with ${d.name}.`);
      if (UI.wr) renderWarRoom();
    }
    back();
  }

  // Choose which owned skill or gear goes into a slot.
  function itemPicker(rid, kind, idx, back) {
    const run = UI.run;
    const r = R.unitById(run, rid);
    const key = kind === 'skill' ? 'skills' : 'gear';
    const cur = r.load[key][idx];
    const list = run.items.filter((i) => i.kind === kind);
    const rows = list
      .map((it) => {
        const d = R.itemDef(it);
        const ok = D.eligible(r.type, d);
        const holder = R.itemHolder(run, it.uid);
        const mine = holder && holder.id === rid;
        return `<button class="army-row item-row" data-pick="${it.uid}" ${ok && !mine ? '' : 'disabled style="opacity:.45"'}>
          <div class="itemico ${kind}">${ic(kind === 'skill' ? 'scroll' : 'sword')}</div>
          <div class="nm" style="min-width:0"><b>${esc(d.name)}</b><div class="small muted">${esc(d.desc)}</div></div>
          <div class="chips" style="justify-content:flex-end"><span class="chip warn">+${d.cost}</span>${mine ? '<span class="chip good">Equipped</span>' : holder ? `<span class="chip">on ${esc(holder.name)}</span>` : ''}${!ok ? '<span class="chip bad">Not usable</span>' : ''}</div></button>`;
      })
      .join('');
    openSheet(
      `${sheetHead(`Equip ${kind}`, `${esc(r.name)} the ${esc(UNITS[r.type].name)}. Taking an item from another unit moves it here.`)}
      ${list.length ? `<div class="army-list">${rows}</div>` : `<p class="muted">You own no ${kind === 'skill' ? 'skills' : 'gear'} yet. Find them in battle spoils, shops, campfires and events.</p>`}
      <div class="actions">${cur ? `<button class="btn" id="ipClear">Empty this slot</button>` : ''}<button class="btn" id="ipBack">Back</button></div>`,
      (sh) => {
        for (const b of $$('[data-pick]', sh))
          b.onclick = () => {
            if (b.disabled) return;
            if (cur) R.unassignItem(run, cur);
            if (!R.assignItem(run, rid, b.dataset.pick)) toast('That item does not fit this unit.');
            R.save(run);
            if (UI.wr) renderWarRoom();
            sfx('select');
            back();
          };
        if ($('#ipClear', sh))
          $('#ipClear', sh).onclick = () => {
            R.unassignItem(run, cur);
            R.save(run);
            if (UI.wr) renderWarRoom();
            back();
          };
        $('#ipBack', sh).onclick = () => back();
      }
    );
  }

  // Details for a unit on the battlefield (either side).
  function battleUnitSheet(u, live) {
    const T = UNITS[u.type];
    const picks = [];
    if (u.a1) picks.push(ABILITIES[u.a1]);
    if (u.a2) picks.push(ABILITIES[u.a2]);
    if (u.level >= 3 && MASTERY[u.type]) picks.push(MASTERY[u.type]);
    for (const id of u.skills || []) picks.push(SKILLS[id]);
    for (const id of u.gear || []) picks.push(GEAR[id]);
    const traits = traitLines(u, (UI.battle && UI.battle.s) || (UI.wr && UI.wr.s))
      .map((t) => `<li>${esc(t)}</li>`)
      .join('');
    openSheet(
      `${sheetHead(esc(u.name), `${u.team === 'P' ? 'Your' : 'Enemy'} ${T.name} · Level ${u.level}`)}
      ${unitInfoHTML(u, { status: !!live })}
      ${statsHTML(u)}
      ${actsHTML(u)}
      ${picks.length ? `<div class="chips">${picks.map((p) => `<span class="chip magic" title="${esc(p.desc)}">${esc(p.name)}</span>`).join('')}</div>` : ''}
      ${traits ? `<ul class="tips">${traits}</ul>` : ''}
      <p class="small muted">${esc(T.desc)}</p>
      ${u.team === 'E' ? `<p class="hint">${esc(T.tip)}</p>` : ''}
      <div class="actions"><button class="btn" data-close>Close</button></div>`
    );
  }

  // ------------------------------------------------------------ board features

  const OBSTACLE_NAME = { rock: 'Boulder', tree: 'Tree', basalt: 'Basalt Spire' };

  // What a tile holds besides units, in plain words: terrain, loot, the shrine, hazards and
  // reinforcement landing points. Null for open ground with nothing on it.
  function tileFacts(s, x, y, enc) {
    const t = s.terrain[E.idx(s, x, y)];
    const f = { title: null, icon: null, swatch: null, lines: [], zone: null };
    const name = (title, icon, swatch) => {
      if (f.title) return;
      f.title = title;
      f.icon = icon || null;
      f.swatch = swatch || null;
    };
    if (t === E.T_ROCK) {
      const kind = UI.board.palette.obstacle || 'rock';
      name(OBSTACLE_NAME[kind] || 'Boulder', null, kind);
      f.lines.push(
        'Blocks the way: nobody can stand here, and only flying units pass over it.',
        'Stops straight-line attacks such as Dark Lightning; arcing shots and spells fly over it.',
        'It cannot be destroyed. A unit knocked into it is slammed for 6 damage.'
      );
    } else if (t === E.T_WATER || t === E.T_LAVA) {
      const water = t === E.T_WATER;
      name(water ? 'Deep Water' : 'Lava', null, water ? 'water' : 'lava');
      f.lines.push(
        `${water ? 'Too deep' : 'Too hot'} to walk through. Flying units cross it, but nobody can stop on it.`,
        'Attacks pass over it. A unit on foot knocked toward it is slammed for 6 damage instead.'
      );
    }
    const loot = (s.loot || []).find((l) => !l.taken && l.x === x && l.y === y);
    if (loot) {
      name(R.LOOT_NAMES[loot.kind], { chest: 'chest', tome: 'book', relic: 'gem' }[loot.kind]);
      const bonus = R.objectiveInfo(UI.run, enc).bonus.find((o) => o.b.type === 'loot' && o.b.lootId === loot.id);
      f.lines.push(`Move a unit onto it and spend that unit's action to take it.${bonus ? ' Reward: ' + bonus.reward + '.' : ''}`);
      const guards = s.units.filter((u) => u.alive && u.post && u.post.x === x && u.post.y === y);
      if (guards.length) {
        const who = `${guards.length > 1 ? guards.length + ' ' : 'a '}${UNITS[guards[0].type].name}${guards.length > 1 ? 's' : ''}`;
        if (guards.some((g) => !AI.dormant(s, g))) f.lines.push(`Its guards are awake: ${who}.`);
        else {
          f.lines.push(`Guarded by ${who}, asleep until one of your units comes within 3 tiles of it (the red tiles) or strikes them.`);
          f.zone = E.radiusTiles(s, x, y, 3, true);
        }
      }
    }
    const h = s.hold;
    if (h && h.x === x && h.y === y) {
      name('Shrine', 'flag');
      f.lines.push(`Start ${h.need} of your turns in a row with one of your units standing on it to win.${h.count ? ` Held for ${h.count} so far.` : ''}`);
    }
    for (const fx of s.tfx || []) {
      if (fx.x !== x || fx.y !== y) continue;
      const mine = fx.team === 'P';
      const left = `${fx.turns} more turn${fx.turns === 1 ? '' : 's'}`;
      if (fx.kind === 'fire') {
        name('Wall of Fire', 'fire');
        f.lines.push(`${mine ? 'Your fire: enemy' : 'Enemy fire: your'} units that step in or start their turn here take ${fx.dmg || 6} magic damage. Burns for ${left}.`);
      } else if (fx.kind === 'smoke') {
        name('Smoke', 'eye');
        f.lines.push(`Nobody inside can be targeted from more than 1 tile away. Clears in ${left}.`);
      } else if (fx.kind === 'caltrops') {
        name('Caltrops', 'target');
        f.lines.push(`${mine ? 'Your caltrops: the first enemy' : 'Enemy caltrops: the first of your units'} to step here stops, takes 6 damage and is rooted for 1 turn. They stay for ${left}.`);
      }
    }
    for (const w of E.waveSummary(s)) {
      const k = (w.marks || []).findIndex(([mx, my]) => mx === x && my === y);
      if (k < 0) continue;
      name('Landing Point', 'hourglass');
      f.lines.push(`Reinforcements: ${w.team === 'E' ? 'an enemy' : 'your'} ${UNITS[w.types[k]].name} lands here after the enemy's next move. One of your units standing here blocks it, but takes ${E.BLOCK_DMG} damage.`);
    }
    return f.lines.length ? f : null;
  }

  // A line for a unit standing on something worth knowing: the shrine, loot, a hazard or a
  // landing point.
  function underfootHTML(s, u, enc) {
    const f = tileFacts(s, u.x, u.y, enc);
    return f ? `<div class="small muted">Standing on: <b>${esc(f.title)}</b>. ${esc(f.lines[0])}</div>` : '';
  }

  function tileInfoHTML(f) {
    const mark = f.icon ? `<span class="ti-icon">${ic(f.icon)}</span>` : `<span class="ti-swatch ${f.swatch || ''}"></span>`;
    return `<div class="tileinfo"><div class="ti-head">${mark}<b>${esc(f.title)}</b></div><ul>${f.lines.map((l) => `<li>${esc(l)}</li>`).join('')}</ul></div>`;
  }

  // The board feature a tap landed on, when it is not a unit: whichever drawing (a rock,
  // a chest, or the flat tile itself) has its middle nearest the finger.
  function featureAt(hit, s, enc) {
    const cands = [...(hit.props || []), ...(hit.tile ? [hit.tile] : [])].filter((t) => tileFacts(s, t.x, t.y, enc));
    cands.sort((a, b) => (a.d || 0) - (b.d || 0));
    return cands.length ? { x: cands[0].x, y: cands[0].y } : null;
  }

  // Whoever stands in front under the finger, unless a rock or a chest drawn nearer the
  // viewer covers them.
  function unitInFront(hit, s) {
    const prop = (hit.props || [])[0];
    const sprite = hit.unitTile ? s.byId[hit.unitTile.uid] : null;
    const u = sprite && sprite.alive ? sprite : hit.tile ? E.at(s, hit.tile.x, hit.tile.y) : null;
    return u && !(prop && prop.x + prop.y > u.x + u.y) ? u : null;
  }

  // ------------------------------------------------------------ objectives

  function objectivesHTML(enc, s) {
    const info = R.objectiveInfo(UI.run, enc);
    let status = '';
    if (s && s.hold) status = ` <span class="reward">${s.hold.count}/${s.hold.need}</span>`;
    if (s && s.surviveTurns) status = ` <span class="reward">${Math.max(0, s.surviveTurns - s.turn + 1)} to go</span>`;
    if (s && enc.layout === 'convoy') {
      const carts = s.units.filter((u) => u.type === 'cart');
      status = ` <span class="reward">${carts.filter((u) => !u.alive && !u.escaped).length} broken · ${carts.filter((u) => u.escaped).length} escaped</span>`;
    }
    if (s && (info.key === 'totems' || info.key === 'raze')) {
      const goals = s.units.filter((u) => u.team === 'E' && u.goal);
      status = ` <span class="reward">${goals.filter((u) => !u.alive).length}/${goals.length} down</span>`;
    }
    const lines = [`<div class="obj primary">${ic('flag')}<span><b>${esc(info.short)}.</b> ${esc(info.primary)}${status}</span></div>`];
    const wl = wavesLine(enc, s);
    if (wl) lines.push(wl);
    for (const o of info.bonus) {
      let state = '';
      if (s) {
        const b = o.b;
        if (b.type === 'loot' && s.loot.some((l) => l.id === b.lootId && l.taken)) state = 'done';
        if (b.type === 'swift' && s.turn > b.turns) state = 'failed';
        if (b.type === 'flawless' && s.units.some((u) => u.team === 'P' && !u.nonCombat && !u.alive)) state = 'failed';
        if (b.type === 'muster') state = s.units.some((u) => u.rid === b.rid) ? 'done' : 'failed';
        if (b.type === 'plunder' && s.units.some((u) => u.type === 'cart' && u.escaped)) state = 'failed';
        if (b.type === 'blockade' && s.stats.blocked >= b.n) state = 'done';
      }
      lines.push(`<div class="obj bonus ${state}">${ic(state === 'done' ? 'check' : 'star')}<span>${esc(o.text)} <span class="reward">Reward: ${esc(o.reward)}.</span></span></div>`);
    }
    return `<div class="objectives">${lines.join('')}</div>`;
  }

  // When the next enemy reinforcements arrive, and how many are still to come.
  function wavesLine(enc, s) {
    const waves = s
      ? E.waveSummary(s).filter((w) => w.team === 'E')
      : (enc.waves || []).map((w) => ({ turn: w.turn, types: w.units.map((u) => u.type), src: w.from }));
    if (!waves.length) return '';
    const next = Math.min(...waves.map((w) => w.turn));
    const n = waves.filter((w) => w.turn === next).reduce((t, w) => t + w.types.length, 0);
    const rest = waves.reduce((t, w) => t + w.types.length, 0) - n;
    // Waves mark their landing tiles a turn ahead.
    const now = !!s && waves.some((w) => w.turn === next && w.marks);
    const when = now ? "after the enemy's next move. Red tiles show where; a unit standing on one blocks that arrival but takes 10 damage" : `on turn ${next}, after the enemy moves`;
    const more = rest > 0 ? ` ${rest} more after that${waves.some((w) => w.src) ? ' unless their buildings fall' : ''}.` : '';
    return `<div class="obj waves ${now ? 'now' : ''}">${ic('hourglass')}<span><b>Reinforcements.</b> ${n} arriving ${when}.${more}</span></div>`;
  }

  // ------------------------------------------------------------ war room

  function encKindLabel(enc) {
    return enc.kind === 'boss' ? 'Boss battle' : enc.kind === 'elite' ? 'Elite battle' : 'Battle';
  }

  // The enemy's reinforcement schedule, for the scout report.
  function reinforcementsHTML(s) {
    const waves = s.waves.filter((w) => w.team === 'E' && w.state === 'pending');
    if (!waves.length) return '';
    const rows = [];
    const bySrc = new Map();
    for (const w of waves) {
      const k = w.src || 0;
      if (!bySrc.has(k)) bySrc.set(k, []);
      bySrc.get(k).push(w);
    }
    for (const [src, list] of bySrc) {
      const names = (w) => w.units.map((u) => UNITS[u.type].name + (u.level > 1 ? ` (Lv ${u.level})` : '')).join(', ');
      if (src) {
        const b = s.byId[src];
        rows.push(`<li><b>${esc(UNITS[b.type].name)}</b> (${esc(UNITS[b.type].material || 'stone')}): ${list.map((w) => `${esc(names(w))} on turn ${w.turn}`).join(' · ')}. Destroy it to stop the rest.</li>`);
      } else rows.push(...list.map((w) => `<li><b>Turn ${w.turn}:</b> ${esc(names(w))}, from the far edge.</li>`));
    }
    return `<div class="reinf"><div class="eyebrow">${ic('hourglass')} Reinforcements</div><ul>${rows.join('')}</ul></div>`;
  }

  function warRoom() {
    const run = UI.run;
    const p = run.pending;
    const enc = p.enc;
    const b = showBattleLayout();
    clearBanner();
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
    const rows = R.deployRows(run, enc);
    const dep = new Map();
    for (const d of p.lastDep || []) {
      const r = R.unitById(run, d.rid);
      if (!r || !rows.includes(d.y) || enc.terrain[d.y * enc.w + d.x] !== 0) continue;
      if ([...dep.values()].some((o) => o.x === d.x && o.y === d.y)) continue;
      if (dep.size >= R.unitCap(run)) break;
      dep.set(d.rid, { x: d.x, y: d.y, facing: d.facing != null ? d.facing : 0 });
    }
    UI.wr = { supply: R.supplyFor(run), cap: R.unitCap(run), dep, sel: null, tab: 'army', inspect: null, rows, enc, auto: 0 };
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
    const T = UNITS[type];
    return !!(T.act.dmg || (T.act.fx && T.act.fx.poison));
  }

  function renderWarRoom() {
    const run = UI.run;
    const wr = UI.wr;
    if (!wr || !run.pending || run.pending.type !== 'battle') return;
    for (const rid of [...wr.dep.keys()]) if (!R.unitById(run, rid)) wr.dep.delete(rid);
    wr.supply = R.supplyFor(run);
    wr.cap = R.unitCap(run);
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
    const tileF = wr.tile && !wr.sel && !wr.inspect ? tileFacts(s, wr.tile.x, wr.tile.y, enc) : null;
    if (tileF) {
      ov.select = [wr.tile.x, wr.tile.y];
      if (tileF.zone) ov.range = tileF.zone;
    }
    b.ov = ov;

    const used = wrUsed();
    const left = wr.supply - used;
    const gold = Math.max(0, left) * R.LEAN_GOLD * (R.hasRelic(run, 'alchemist_stone') ? 3 : 1);
    const pips = [];
    for (let i = 0; i < Math.max(wr.supply, used); i++) pips.push(`<span class="pip ${i < used ? (i >= wr.supply ? 'over' : 'used') : ''}"></span>`);
    const attempt = run.pending.attempt || 0;

    $('#topbar').innerHTML = `<div class="title"><b>War Room</b><span>${esc(enc.name)} · ${encKindLabel(enc)}${attempt ? ' · attempt ' + (attempt + 1) : ''}</span></div>
      <button class="btn icon-only" id="wrArmy" aria-label="Army">${ic('army')}</button>
      <button class="btn icon-only" id="wrMenu" aria-label="Menu">${ic('menu')}</button>`;
    $('#wrArmy').onclick = () => armySheet(() => renderWarRoom());
    $('#wrMenu').onclick = () => menuSheet(false);

    let body = '';
    if (wr.tab === 'army') {
      body = `<div class="roster">${run.roster
        .map((u) => {
          const deployed = wr.dep.has(u.id);
          const cost = R.unitCost(run, u);
          const cant = !deployed && (cost > left || wr.dep.size >= wr.cap);
          const featured = (enc.bonus || []).some((x) => x.type === 'muster' && x.rid === u.id);
          return `<button class="rcard ${deployed ? 'deployed' : ''} ${wr.sel === u.id ? 'sel' : ''} ${cant ? 'dim' : ''}" data-rid="${u.id}">
            <span class="cost">${cost}</span>${featured ? '<span class="flag feat">Bonus</span>' : u.enchant ? `<span class="flag ench">${ic('gem')}</span>` : ''}
            <canvas data-p="${u.type}:P"></canvas>
            <span class="nm">${esc(u.name)} ${levelBadge(u.load.lv)}</span>
            <span class="ty">${UNITS[u.type].name}</span></button>`;
        })
        .join('')}</div>`;
    } else {
      const tips = R.scoutTips(enc);
      body = `<div class="intel">
        <div class="intel-list">${s.units
          .filter((u) => u.team === 'E' && !u.traits.has('scenery'))
          .map(
            (u) => `<button class="rcard ${wr.inspect === u.uid ? 'sel' : ''}" data-uid="${u.uid}">
              <canvas data-p="${u.type}:E"></canvas>
              <span class="nm">${esc(UNITS[u.type].name)} ${u.level > 1 ? levelBadge(u.level) : ''}</span>
              <span class="ty">${esc(u.a1 ? ABILITIES[u.a1].name : u.acts.length > 1 ? u.acts[1].name : pct(u.armor) + ' arm · ' + pct(u.res) + ' res')}</span></button>`
          )
          .join('')}</div>
        ${reinforcementsHTML(s)}
        ${tips.length ? `<ul class="tips">${tips.map((t) => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}
      </div>`;
    }

    let selBlock = '';
    if (wr.sel && wr.dep.has(wr.sel)) {
      const r = R.unitById(run, wr.sel);
      const L = r.load;
      selBlock = `<div class="selunit"><div><b>${esc(r.name)}</b> ${levelBadge(L.lv)} <span class="small muted">${esc(UNITS[r.type].name)} · ${esc(ABILITIES[L.a1].name)}${L.lv >= 2 ? ' · ' + esc(ABILITIES[L.a2].name) : ''} · ${R.unitCost(run, r)} Supply</span></div>
        <div class="small muted">Tap a blue tile to move it, or another of your units to swap places. Tap it again for its loadout.</div></div>
        <div class="actions"><button class="btn primary" id="wrLoad">${ic('up')} Loadout</button>
        <button class="btn" id="wrTurn">${ic('rotate')} Turn</button>
        <button class="btn danger" id="wrRemove">${ic('close')} Remove</button></div>`;
    } else if (wr.inspect && s.byId[wr.inspect]) {
      const u = s.byId[wr.inspect];
      selBlock = `<div class="hint">Enemy ${esc(UNITS[u.type].name)}${u.level > 1 ? ' (Level ' + u.level + ')' : ''}: ${pct(u.armor)} armor, ${pct(u.res)} magic resistance. Red tiles on the board: everywhere it could hit on its next turn, splash included.</div>
        ${actsHTML(u)}
        <div class="actions"><button class="btn" id="wrEInfo">${ic('help')} Details</button></div>`;
    } else if (tileF) {
      selBlock = tileInfoHTML(tileF);
    } else if (wr.dep.size === 0) {
      selBlock = `<div class="hint">Study the enemy, then tap units to deploy them into the blue zone. Tap a deployed unit again to change its level, abilities, skills and gear. Every point of Supply counts.</div>`;
    }

    const overCap = wr.dep.size > wr.cap;
    const over = used > wr.supply;
    $('#cmd').innerHTML = `
      <div class="cp-meter"><span class="res">${ic('command')}<span class="num">${used}/${wr.supply}</span></span><div class="pips">${pips.join('')}</div>
        <span class="res" title="Units on the field">${ic('army')}<span class="num">${wr.dep.size}/${wr.cap}</span></span></div>
      <div class="small ${over || overCap ? 'bad-text' : 'muted'}">${
        over ? `Over budget by ${used - wr.supply} Supply: lower a level, drop an item, or remove a unit.` : overCap ? 'Too many units for your commander level.' : left > 0 ? `${left} unspent → <b style="color:var(--brass-hi)">+${gold} gold</b> if you win` : 'Every point of Supply committed.'
      }</div>
      ${objectivesHTML(enc)}
      <div class="tabs"><button class="btn ${wr.tab === 'army' ? 'on' : ''}" id="wrTabA">${ic('army')} Your army</button>
        <button class="btn ${wr.tab === 'intel' ? 'on' : ''}" id="wrTabI">${ic('eye')} Enemy (${s.units.filter((u) => u.team === 'E' && E.counts(u)).length})</button></div>
      ${body}
      ${selBlock}
      <div class="actions"><button class="btn" id="wrAuto">${ic('star')} ${wr.auto ? 'Suggest another' : 'Auto'}</button><button class="btn" id="wrClear" ${wr.dep.size ? '' : 'disabled'}>Clear</button>
        <button class="btn primary" id="wrFight" ${wr.dep.size && !over && !overCap ? '' : 'disabled'}>${ic('swords')} Fight</button></div>`;
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
    for (const c of $$('.rcard[data-rid]', cmd)) {
      c.onclick = () => wrCard(c.dataset.rid);
      c.oncontextmenu = (e) => {
        e.preventDefault();
        loadoutSheet(c.dataset.rid, () => closeSheet());
      };
    }
    for (const c of $$('.rcard[data-uid]', cmd))
      c.onclick = () => {
        wr.inspect = wr.inspect === +c.dataset.uid ? null : +c.dataset.uid;
        wr.sel = null;
        wr.tile = null;
        renderWarRoom();
      };
    if ($('#wrLoad')) $('#wrLoad').onclick = () => loadoutSheet(wr.sel, () => closeSheet());
    if ($('#wrTurn'))
      $('#wrTurn').onclick = () => {
        const d = wr.dep.get(wr.sel);
        d.facing = (d.facing + 1) % 4;
        renderWarRoom();
      };
    if ($('#wrRemove'))
      $('#wrRemove').onclick = () => {
        wr.dep.delete(wr.sel);
        wr.sel = null;
        renderWarRoom();
      };
    if ($('#wrEInfo')) $('#wrEInfo').onclick = () => battleUnitSheet(s.byId[wr.inspect]);
    $('#wrAuto').onclick = async () => {
      if (!wr.auto && run.roster.some((r) => r.load.lv > 1 || r.load.skills.length || r.load.gear.length)) {
        const ok = await confirmSheet('Auto-build an army?', 'Auto picks units, levels and items for this enemy. It resets the levels and items of your units first.', 'Build it', 'Cancel');
        if (!ok) return;
      }
      wr.auto++;
      wr.dep.clear();
      for (const d of R.autoDeploy(run, wr.auto - 1)) wr.dep.set(d.rid, { x: d.x, y: d.y, facing: 0 });
      wr.sel = null;
      R.save(run);
      sfx('click');
      renderWarRoom();
      // Say what Auto went for, and why.
      const p = R.damageProfile(wr.enc);
      const types = [...wr.dep.keys()].map((rid) => UNITS[R.unitById(run, rid).type].act.dmg);
      const n = (t) => types.filter((x) => x === t).length;
      const plural = (k, w) => `${k} ${w} attacker${k === 1 ? '' : 's'}`;
      const got = n('magic') && n('phys') ? `${plural(n('magic'), 'magic')} and ${plural(n('phys'), 'physical')}` : n('magic') ? plural(n('magic'), 'magic') : plural(n('phys'), 'physical');
      const a = `armor ${Math.round(p.armor * 100)}%`;
      const r = `magic resistance ${Math.round(p.res * 100)}%`;
      const owned = (t) => run.roster.some((x) => UNITS[x.type].act.dmg === t);
      let why;
      if (p.lean === 'mixed') why = `Their ${a} and ${r} are close, so both damage types work.`;
      else {
        const t = p.lean;
        const name = t === 'magic' ? 'Magic' : 'Steel';
        why = `${name} hits harder here (their ${a}, ${r}).`;
        if (!n(t)) why += owned(t) ? ` Your ${t === 'magic' ? 'magic' : 'physical'} units did not fit this time.` : ` You have no ${t === 'magic' ? 'magic' : 'physical'} attackers yet.`;
      }
      if (n('magic') + n('phys')) toast(`Auto: ${got}. ${why}`, 5000);
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
    wr.tile = null;
    if (wr.dep.has(rid)) {
      if (wr.sel === rid) {
        loadoutSheet(rid, () => closeSheet());
        return;
      }
      wr.sel = rid;
      wr.inspect = null;
      sfx('click');
      renderWarRoom();
      return;
    }
    const r = R.unitById(run, rid);
    if (wr.dep.size >= wr.cap) {
      toast(`Only ${wr.cap} units may take the field. Remove one first, or raise your commander level.`);
      return;
    }
    const taken = new Set([...wr.dep.values()].map((d) => d.x + ',' + d.y));
    const slot = R.deploySlots(run, wr.enc, R.isFront(r.type), taken)[0];
    if (!slot) {
      toast('Your deployment zone is full.');
      return;
    }
    wr.dep.set(rid, { x: slot.x, y: slot.y, facing: 0 });
    wr.sel = rid;
    wr.inspect = null;
    sfx('select');
    const over = wrUsed() - wr.supply;
    if (over > 0) toast(`Over budget by ${over} Supply. Lower a level or drop an item to fight.`);
    renderWarRoom();
  }

  function wrTap(hit) {
    const wr = UI.wr;
    if (!wr) return;
    const s = wr.s;
    // Any tap closes the feature panel; tapping the same feature again keeps it closed.
    const shown = wr.tile;
    wr.tile = null;
    const raw = hit.tile;
    const tileUnit = raw ? E.at(s, raw.x, raw.y) : null;
    const spriteUnit = hit.unitTile ? s.byId[hit.unitTile.uid] : null;
    let t = raw;
    // With a unit picked up, an open blue tile under the finger is where it goes.
    const placing = wr.sel && wr.dep.has(wr.sel) && raw && !tileUnit && isDeployTile(raw.x, raw.y);
    if (!placing && spriteUnit) t = { x: spriteUnit.x, y: spriteUnit.y };
    // A rock or chest in front of everything else: say what it is.
    if (!placing && !unitInFront(hit, s) && (hit.props || []).length) t = null;
    if (!t) return wrFeature(hit, shown);
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
    wrFeature(hit, shown);
  }

  // A tap on the board that is not about a unit: explain the rock, chest or shrine under
  // it, or clear the selection.
  function wrFeature(hit, shown) {
    const wr = UI.wr;
    const spot = featureAt(hit, wr.s, wr.enc);
    wr.sel = null;
    wr.inspect = null;
    wr.tile = spot && !(shown && shown.x === spot.x && shown.y === spot.y) ? spot : null;
    if (wr.tile) sfx('click');
    renderWarRoom();
  }

  function wrLong(hit) {
    const wr = UI.wr;
    if (!wr) return;
    const t = hit.unitTile || hit.tile;
    if (!t) return;
    const u = E.at(wr.s, t.x, t.y);
    if (!u) return;
    if (u.team === 'P' && u.rid) loadoutSheet(u.rid, () => closeSheet());
    else battleUnitSheet(u);
  }

  async function wrFight() {
    const run = UI.run;
    const wr = UI.wr;
    const dep = wrDepArray();
    if (!dep.length) return;
    if (wrUsed() > wr.supply) {
      toast('You are over your Supply budget.');
      return;
    }
    if (dep.length > wr.cap) {
      toast(`Only ${wr.cap} units may take the field.`);
      return;
    }
    if (!dep.some((d) => isAttacker(R.unitById(run, d.rid).type))) {
      toast('Deploy at least one unit that can deal damage.');
      return;
    }
    run.pending.lastDep = dep;
    R.save(run);
    startBattle(dep);
  }

  // ------------------------------------------------------------ battle

  async function startBattle(dep) {
    const run = UI.run;
    const enc = run.pending.enc;
    const diff = DIFFICULTIES.find((d) => d.id === run.difficulty) || DIFFICULTIES[1];
    const s = E.createBattle(R.battleConfig(run, dep));
    E.drainEvents(s);
    UI.wr = null;
    UI.battle = { s, dep, enc, mode: 'idle', sel: null, target: null, ai: 0, busy: false, temp: diff.temp, confirmEnd: false };
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
      toast(UI.prefs.threat ? 'Showing every tile an enemy unit could strike on its next turn.' : 'Enemy reach hidden.');
      renderBattle();
    };
    $('#btFast').onclick = () => {
      UI.prefs.fast = !UI.prefs.fast;
      savePrefs();
      b.speed = UI.prefs.fast ? 2 : 1;
      $('#btFast').classList.toggle('on', UI.prefs.fast);
    };
    showBanner(s.side === 'E' ? 'Enemy moves first' : 'Your turn', s.side === 'E');
    sfx(s.side === 'E' ? 'enemyturn' : 'turn');
    renderBattle();
    // The enemy opens the battle; then the sides take turns, one unit each.
    if (s.side === 'E') {
      UI.battle.busy = true;
      await sleep(UI.prefs.fast ? 300 : 800);
      if (UI.battle && UI.battle.s === s) await enemyMoves();
    }
  }

  // Ready units that can actually do something this turn.
  function usefulReady(s) {
    return E.readyUnits(s, 'P').filter((u) => E.usefulUnit(s, u));
  }

  // Acts aimed by tapping an enemy directly.
  function directKinds(kind) {
    return kind === 'strike' || kind === 'cleave' || kind === 'quake' || kind === 'shadowstrike';
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

  // Buttons for the attack and each active ability, with charges and availability.
  function actButtons(u) {
    const s = UI.battle.s;
    const out = [];
    u.acts.forEach((a, i) => {
      if (a.kind === 'none') return;
      const usable = E.actUsable(s, u, i);
      const n = usable ? E.targetsFrom(s, u, i).length : 0;
      const uses = a.uses ? ` <span class="uses">${a.left}/${a.uses}</span>` : '';
      let why = '';
      if (a.left <= 0) why = 'no uses left';
      else if (!usable) why = a.asMove ? 'already moved' : 'already acted';
      else if (!n) why = 'no targets';
      const icon = a.dmg ? dmgIcon(a.dmg) : ic(i === 0 ? 'target' : 'star');
      out.push(`<button class="btn act ${i === 0 ? 'primary' : ''}" data-act="${i}" ${n ? '' : 'disabled'} title="${esc(why)}">${icon} ${esc(a.name)}${uses}</button>`);
    });
    return out.join('');
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
      `<button class="btn ${primary ? 'primary' : ''}" id="btEnd" ${s.side !== 'P' || B.busy ? 'disabled' : ''}>${B.confirmEnd ? 'Confirm pass' : 'Pass'}</button>`;
    const inProgress = !!(s.act && (s.act.moved || s.act.acted));
    const tileF = B.mode === 'tile' && B.tile ? tileFacts(s, B.tile.x, B.tile.y, B.enc) : null;
    if (B.mode === 'tile' && !tileF) B.mode = 'idle';

    if (s.side !== 'P' || B.busy) {
      const actor = B.acting && s.byId[B.acting];
      panel = actor && actor.alive
        ? `${unitInfoHTML(actor, { status: true })}<div class="hint">Enemy turn: their ${esc(UNITS[actor.type].name)}. Your turn comes next.</div>`
        : `<div class="hint">${s.side === 'P' ? 'Resolving…' : 'The enemy is choosing a unit. The fast-forward button speeds things up.'}</div>`;
    } else if (B.mode === 'unit' && u) {
      const moved = A && A.moved;
      const acted = A && A.acted;
      if (!moved) ov.move = [...E.reachable(s, u).values()].filter((r) => r.d > 0).map((r) => [r.x, r.y]);
      const main = acted ? [] : E.actUsable(s, u, 0) ? E.targetsFrom(s, u, 0) : [];
      if (!acted && directKinds(u.act.kind)) ov.targets = main.map((t) => [t.x, t.y]);
      ov.select = [u.x, u.y];
      const anyTargets = E.allTargets(s, u).length > 0;
      let hint;
      if (!moved && !acted) hint = `Tap a blue tile to move${main.length && directKinds(u.act.kind) ? ', a red enemy to attack' : ''}, or choose an action below.`;
      else if (moved && !acted) hint = anyTargets ? 'Moved. Choose an action, or tap Done.' : 'Moved. Nothing in reach from here. Tap Done.';
      else hint = moved ? `Action used. Tap Done${UI.prefs.manualFacing ? ' to choose a facing' : ': it turns to the nearest enemy'}.` : 'Action used. You may still move, or tap Done.';
      const loot = !acted && E.lootAt(s, u.x, u.y);
      if (loot) hint = `${esc(u.name)} stands on the ${R.LOOT_NAMES[loot.kind]}. Taking it uses this unit's action.`;
      if (u.root > 0 && !moved) hint = `Rooted for ${u.root} more turn${u.root > 1 ? 's' : ''}: it can act and turn, but not move.`;
      panel = `${unitInfoHTML(u, { status: true })}${statsHTML(u)}${loot ? '' : underfootHTML(s, u, B.enc)}
        <div class="hint">${hint}</div>
        <div class="actions acts">
          ${loot ? `<button class="btn primary" id="btLoot">${ic('chest')} Take the ${R.LOOT_NAMES[loot.kind]}</button>` : ''}
          ${actButtons(u)}
        </div>
        <div class="actions">
          ${E.canUndo(s) && moved ? `<button class="btn" id="btUndo">${ic('undo')} Undo move</button>` : ''}
          ${moved || acted ? `<button class="btn" id="btDone">${ic('check')} Done</button>` : `<button class="btn" id="btFace">${ic('rotate')} Face only</button>`}
          <button class="btn" id="btInfo">${ic('help')}</button>
          <button class="btn ghost" id="btDesel">${ic('close')}</button>
        </div>`;
    } else if ((B.mode === 'aim' || B.mode === 'confirm') && u) {
      const act = u.acts[B.ai] || u.act;
      const targets = E.targetsFrom(s, u, B.ai);
      ov.targets = [];
      for (const t of targets) ov.targets.push(...targetTiles(u, t));
      ov.select = [u.x, u.y];
      let prev = '';
      if (B.mode === 'confirm' && B.target) {
        const pv = E.previewAction(s, u, B.target);
        const healish = act.kind === 'pray' || act.kind === 'heal' || act.kind === 'shield' || act.kind === 'drum' || act.kind === 'rally';
        ov.aoe = pv.tiles.map(([x, y]) => {
          const o = E.at(s, x, y);
          return [x, y, healish ? 'heal' : o && o.team === u.team && o !== u ? 'ally' : 'foe'];
        });
        if (B.target.kind === 'unit' || B.target.kind === 'tile') ov.targets = ov.targets.filter(([x, y]) => x !== B.target.x || y !== B.target.y);
        prev = previewHTML(u, act, pv);
      }
      panel = `${unitInfoHTML(u, { status: true })}
        ${actRow(u, act, false)}
        ${B.mode === 'confirm' ? prev : `<div class="hint">Choose a target: tap a red tile${act.kind === 'line' || act.kind === 'cone' ? ' or a unit in that direction' : ''}.</div>`}
        <div class="actions">
          ${B.mode === 'confirm' ? `<button class="btn primary" id="btConfirm">${ic('check')} ${esc(act.name)}</button>` : ''}
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
      panel = `${unitInfoHTML(u, { status: true })}${statsHTML(u)}${underfootHTML(s, u, B.enc)}
        ${actsHTML(u)}
        <div class="hint">${
          u.team === 'E'
            ? `Blue: where it can move. Red: everywhere it could hit when it next acts${u.wait > 1 ? ` (it cools down for ${u.wait - 1} more of its turns)` : ''}.`
            : inProgress && s.act.uid !== u.uid
              ? `${esc(s.byId[s.act.uid].name)} is mid-turn. Finish it first: one unit a turn.`
              : u.wait > 0
                ? `Cooling down: ready ${u.wait === 1 ? 'next turn' : 'in ' + u.wait + ' turns'}.`
                : u.para > 0
                  ? `Paralyzed: it sits out ${u.para === 1 ? 'this turn' : 'this turn and ' + (u.para - 1) + ' more'}.`
                  : 'Cannot act right now.'
        }</div>
        <div class="actions">${s.act && s.act.uid !== u.uid ? `<button class="btn primary" id="btBack">Back to ${esc(s.byId[s.act.uid].name)}</button>` : ''}<button class="btn" id="btInfo">${ic('help')} Details</button>${s.act ? '' : `<button class="btn ghost" id="btDesel">${ic('close')}</button>${endBtn(false)}`}</div>`;
    } else if (B.mode === 'tile') {
      ov.select = [B.tile.x, B.tile.y];
      if (tileF.zone) ov.range = tileF.zone;
      panel = `${tileInfoHTML(tileF)}
        <div class="actions"><button class="btn ghost" id="btDesel">${ic('close')}</button>${endBtn(false)}</div>`;
    } else {
      B.mode = 'idle';
      const ready = usefulReady(s);
      panel = `<div class="hint">${
        ready.length
          ? 'Your turn: pick one glowing unit to move, act, or both. Then the enemy picks one. Long-press any unit for details.'
          : 'None of your units can act right now. Pass.'
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

    const info = R.objectiveInfo(UI.run, B.enc);
    const goals = info.key === 'totems' || info.key === 'raze' ? s.units.filter((x) => x.team === 'E' && x.goal) : [];
    const goal = s.hold
      ? `${info.short} ${s.hold.count}/${s.hold.need}`
      : s.surviveTurns
        ? `Survive ${Math.max(0, s.surviveTurns - s.turn + 1)} more`
        : goals.length
          ? `${info.short} ${goals.filter((x) => !x.alive).length}/${goals.length}`
          : info.short;
    $('#topbar').innerHTML = `<div class="title"><b>${s.side === 'P' && !B.busy ? 'Your turn' : 'Enemy turn'}</b>
      <span>Turn ${Math.min(s.turn, s.turnLimit)} of ${s.turnLimit} · ${esc(goal)}</span></div>
      ${s.side === 'P' && !B.busy && B.mode !== 'idle' && !inProgress ? endBtn(false) : ''}
      <button class="btn icon-only" id="btMenu" aria-label="Menu">${ic('menu')}</button>`;
    $('#cmd').innerHTML = panel;
    drawPortraits($('#cmd'));
    bindBattlePanel();
  }

  function previewHTML(u, act, pv) {
    const s = UI.battle.s;
    const healish = act.kind === 'pray' || act.kind === 'heal' || act.kind === 'shield' || act.kind === 'drum' || act.kind === 'rally';
    const lines = pv.effects.map((e) => {
      const v = s.byId[e.uid];
      const who = e.self ? 'Itself' : `${v.team === 'P' ? 'Your' : 'Enemy'} ${esc(UNITS[v.type].name)}`;
      const bits = [];
      if (e.dmg != null) {
        // One flex item, so the type icon stays with its number.
        bits.push(`<span>${act.dmg ? dmgIcon(act.dmg) : ''}<b>${e.dmg}</b></span> ${act.dmg === 'magic' ? 'magic' : act.dmg === 'phys' ? 'physical' : ''} dmg`);
        if (e.block > 0) bits.push(`${pct(e.block)} block (${e.cat})`);
        else if (act.dmg === 'phys' && !e.self) bits.push(e.cat === 'back' ? 'from behind' : 'no block');
        if (e.kill) bits.push(`<span class="kill">${e.block > 0 ? 'can kill' : 'kills'}</span>`);
      }
      if (e.heal != null) bits.push(e.heal > 0 ? `<b>+${e.heal}</b> HP` : v.poison ? 'poisoned: no healing' : 'full HP');
      if (e.cleanse) bits.push('cures');
      if (e.shield) bits.push(`shield ${e.shield}`);
      if (e.frenzy) bits.push('frenzy');
      if (e.rally) bits.push(v.wait > 0 ? `cooldown ${v.wait} → ${v.wait - 1}` : 'rallied');
      if (e.para) bits.push(e.para === 'resist' ? 'immune to paralysis' : `paralyzed ${e.para}`);
      if (e.poison) bits.push(e.poison === 'resist' ? 'immune to poison' : `poison ${e.poison.dmg}×${e.poison.turns}`);
      if (e.burn) bits.push(`burn ${e.burn.dmg}×${e.burn.turns}`);
      if (e.root) bits.push(e.root === 'resist' ? 'cannot be rooted' : `rooted ${e.root}`);
      if (e.weak) bits.push(`weakened ${e.weak}`);
      if (e.mark) bits.push(`marked ${e.mark}`);
      if (e.knock) bits.push(e.knock === 'resist' ? 'stands firm' : 'knocked back');
      const ff = e.friendly && !healish && !e.self;
      return `<div class="line ${ff ? 'ff' : ''}">${who}: ${bits.join(' · ') || 'no effect'}${ff ? ' (friendly fire)' : ''}</div>`;
    });
    if (act.kind === 'grow') lines.push('<div class="line">Raise a shrub here.</div>');
    if (act.kind === 'raise') lines.push('<div class="line">Raise a skeleton here.</div>');
    if (act.kind === 'blink') lines.push('<div class="line">Teleport here. You can still attack afterward.</div>');
    if (act.kind === 'revive') lines.push(`<div class="line">${esc(s.byId[UI.battle.target.uid].name)} rises with ${Math.round((act.pct || 0.4) * 100)}% HP.</div>`);
    if (act.kind === 'hazard') lines.push(`<div class="line">${act.hz === 'smoke' ? 'Smoke' : act.hz === 'fire' ? 'Fire' : 'Caltrops'} on ${pv.tiles.length} tile${pv.tiles.length > 1 ? 's' : ''} for ${act.turns} turns.</div>`);
    if (act.kind === 'leap') lines.unshift('<div class="line">Leap here, then strike every adjacent enemy.</div>');
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
    on('btEnd', () => passMove());
    on('btDesel', () => deselect());
    on('btUndo', async () => {
      if (B.busy) return;
      E.undoMove(s);
      await play();
      renderBattle();
    });
    on('btDone', () => enterFacing());
    // Turning in place is a deliberate choice: pick the facing by hand.
    on('btFace', () => {
      if (!E.beginActivation(s, B.sel)) return;
      enterFacing(true);
    });
    for (const btn of $$('#cmd [data-act]'))
      btn.onclick = () => {
        const u = s.byId[B.sel];
        const ai = +btn.dataset.act;
        const targets = E.targetsFrom(s, u, ai);
        B.ai = ai;
        if (targets.length === 1 && (targets[0].kind === 'self' || !directKinds(u.acts[ai].kind))) {
          B.mode = 'confirm';
          B.target = targets[0];
        } else {
          B.mode = 'aim';
          B.target = null;
        }
        sfx('click');
        renderBattle();
      };
    on('btCancel', () => {
      B.mode = 'unit';
      B.target = null;
      B.ai = 0;
      renderBattle();
    });
    on('btConfirm', () => doAction());
    on('btLoot', () => doLoot());
    on('btKeep', () => finishUnit(B.facing));
    on('btInfo', () => battleUnitSheet(s.byId[B.sel], true));
    on('btBack', () => s.act && selectUnit(s.byId[s.act.uid]));
    for (const c of $$('#cmd .rcard[data-uid]')) c.onclick = () => selectUnit(s.byId[+c.dataset.uid]);
  }

  async function play(keepBusy) {
    const B = UI.battle;
    B.busy = true;
    UI.board.activeSide = null;
    const ev = E.drainEvents(B.s);
    await UI.board.playEvents(ev, B.s);
    UI.board.syncFromState(B.s);
    // Your own passes need no news; the enemy's, and turns you had to skip, do.
    const passes = B.s.over ? [] : ev.filter((e) => e.t === 'pass' && (e.side === 'E' || e.auto));
    if (passes.length) {
      const mine = passes.filter((e) => e.side === 'P').length;
      toast(mine ? `None of your units could act, so your turn passed${mine > 1 ? ' ' + mine + ' times' : ''}.` : 'The enemy passes.');
      await sleep(UI.prefs.fast ? 250 : 600);
    }
    if (!keepBusy) B.busy = false;
  }

  // After every move: the battle may be over, or the enemy may be up.
  async function nextMove() {
    const B = UI.battle;
    if (!B) return;
    const s = B.s;
    if (s.over) return battleOver();
    if (s.side === 'E') return enemyMoves();
    B.mode = 'idle';
    B.sel = null;
    renderBattle();
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
    B.tile = null;
    B.target = null;
    B.ai = 0;
    renderBattle();
  }

  async function selectUnit(v) {
    const B = UI.battle;
    const s = B.s;
    if (!v || B.busy) return;
    const act = s.act;
    const inProgress = act && (act.moved || act.acted);
    const ownReady = v.team === 'P' && E.canActivate(s, v);
    if (act && act.uid !== v.uid && !inProgress) E.cancelActivation(s);
    B.sel = v.uid;
    B.target = null;
    B.ai = 0;
    B.confirmEnd = false;
    // One unit a turn: once it has moved or acted, the others can only be looked at.
    B.mode = (s.act && s.act.uid === v.uid) || (ownReady && !inProgress) ? 'unit' : 'inspect';
    if (UI.board.zoom > 1) UI.board.centerOn(v.x, v.y);
    sfx('select');
    renderBattle();
  }

  // Map a tap to the nearest candidate tile (within about half a tile).
  function snap(hit, cands) {
    if (!cands.length) return null;
    const b = UI.board;
    for (const st of hit.stack || (hit.unitTile ? [hit.unitTile] : [])) {
      const m = cands.find((c) => c.x === st.x && c.y === st.y);
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
      for (const t of E.targetsFrom(s, u, B.ai)) for (const [x, y] of targetTiles(u, t)) cands.push({ x, y, t });
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
      B.ai = 0;
      renderBattle();
      return;
    }
    if (B.mode === 'unit' && u) {
      const A = activationOf(u);
      const tileUnit = hit.tile ? E.at(s, hit.tile.x, hit.tile.y) : null;
      const spriteUnit = hit.unitTile ? s.byId[hit.unitTile.uid] : null;
      // 1. An enemy under the finger that the main attack can hit: aim at it. Sprites come
      // first, front to back, then whoever stands on the tile beneath the finger.
      if (!(A && A.acted) && directKinds(u.act.kind) && E.actUsable(s, u, 0)) {
        const tgts = E.targetsFrom(s, u, 0);
        const under = (hit.stack || []).map((st) => s.byId[st.uid]);
        for (const cand of [...under, tileUnit]) {
          if (!cand || cand.team === u.team) continue;
          const t = tgts.find((k) => k.uid === cand.uid);
          if (t) {
            B.mode = 'confirm';
            B.ai = 0;
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
    const other = unitInFront(hit, s);
    if (other) return selectUnit(other);
    if (s.act && (s.act.moved || s.act.acted)) return selectUnit(s.byId[s.act.uid]);
    // Rocks, loot, the shrine, hazards and landing points explain themselves.
    const spot = featureAt(hit, s, B.enc);
    E.cancelActivation(s);
    B.mode = spot ? 'tile' : 'idle';
    B.tile = spot;
    B.sel = null;
    if (spot) sfx('select');
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
    if (s.over) return battleOver();
    if (!u.alive) {
      E.endTurn(s);
      await play();
      return nextMove();
    }
    B.mode = 'unit';
    renderBattle();
  }

  async function afterAct(u) {
    const B = UI.battle;
    const s = B.s;
    if (s.over) return battleOver();
    if (!u.alive) {
      E.endTurn(s);
      await play();
      return nextMove();
    }
    const A = activationOf(u);
    const canMove = A && !A.moved && u.move > 0 && !u.traits.has('immobile') && E.reachable(s, u).size > 1;
    const canAct = A && !A.acted && E.allTargets(s, u).length > 0;
    if (canMove || canAct) {
      B.mode = 'unit';
      renderBattle();
    } else enterFacing();
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
    B.ai = 0;
    await play();
    await afterAct(u);
  }

  async function doLoot() {
    const B = UI.battle;
    const s = B.s;
    const u = s.byId[B.sel];
    if (!u || B.busy) return;
    if (!E.beginActivation(s, u.uid) || !E.takeLoot(s, u.uid)) return;
    await play();
    await afterAct(u);
  }

  // The unit is done: it turns toward the nearest enemy on its own, unless the player
  // picks the facing (Face only, or manual facing chosen in the menu).
  function enterFacing(manual) {
    const B = UI.battle;
    const s = B.s;
    const u = s.byId[B.sel];
    if (!u) return;
    if (u.facing < 0) {
      finishUnit(-1);
      return;
    }
    if (!manual && !UI.prefs.manualFacing) {
      finishUnit(AI.nearestFacing(s, u));
      return;
    }
    B.mode = 'facing';
    B.facing = AI.smartFacing(s, u);
    renderBattle();
  }

  // The unit is done, and so is your turn: the enemy picks a unit next.
  async function finishUnit(d) {
    const B = UI.battle;
    const s = B.s;
    if (!s.act) E.beginActivation(s, B.sel);
    E.finishActivation(s, d);
    E.endTurn(s);
    B.mode = 'idle';
    B.sel = null;
    B.target = null;
    B.ai = 0;
    await play();
    await nextMove();
  }

  // Skip your turn: the enemy moves next.
  async function passMove() {
    const B = UI.battle;
    if (!B || B.busy || B.s.side !== 'P') return;
    const s = B.s;
    if (s.act && (s.act.moved || s.act.acted)) return enterFacing();
    if (usefulReady(s).length && !B.confirmEnd) {
      B.confirmEnd = true;
      toast('Pass this turn? The enemy moves next. Tap again to pass.');
      renderBattle();
      return;
    }
    B.confirmEnd = false;
    E.cancelActivation(s);
    B.mode = 'idle';
    B.sel = null;
    B.target = null;
    E.pass(s);
    await play();
    await nextMove();
  }

  // The enemy's turn: one unit. If none of yours can act, it goes again.
  async function enemyMoves() {
    const B = UI.battle;
    const s = B.s;
    const b = UI.board;
    B.busy = true;
    B.mode = 'idle';
    B.sel = null;
    let guard = 0;
    while (!s.over && s.side === 'E' && guard++ < 400) {
      const plan = AI.chooseActivation(s, 'E', { stance: B.enc.stance, temp: B.temp });
      const u = plan && s.byId[plan.uid];
      if (u && plan.kind !== 'turn') {
        B.acting = u.uid;
        renderBattle();
        b.ov = { select: [u.x, u.y] };
        await sleep(UI.prefs.fast ? 140 : 380);
      }
      AI.runPlan(s, plan, { stance: B.enc.stance });
      b.ov = {};
      await play(true);
    }
    B.acting = null;
    B.busy = false;
    if (s.over) return battleOver();
    sfx('select');
    renderBattle();
  }

  async function battleOver() {
    const B = UI.battle;
    if (!B || B.ending) return;
    B.ending = true;
    B.busy = true;
    const s = B.s;
    const won = s.winner === 'P';
    const endEv = s.end;
    showBanner(won ? 'Victory' : 'Defeat', !won);
    sfx(won ? 'victory' : 'defeat');
    renderBattle();
    await sleep(1500);
    const res = R.finishBattle(UI.run, s, B.dep);
    UI.battle = null;
    if (won) {
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
      <p>${reason} The enemy holds the field, but your campaign goes on: there is no limit on retries.</p>
      <p class="muted">Re-plan your army against the same enemy. Swap units, change levels and abilities, move your archers back, bring the counter they fear.</p>
      <div class="actions"><button class="btn" id="dfTitle">Main menu</button><button class="btn primary" id="dfRetry">${ic('swords')} Re-plan and fight</button></div>`,
      (sh) => {
        $('#dfRetry', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          warRoom();
        };
        $('#dfTitle', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          title();
        };
      }
    );
    UI.onSheetClose = () => warRoom();
    void res;
  }

  // ------------------------------------------------------------ rewards

  function itemCard(kind, id, attrs, extra) {
    if (kind === 'scroll') {
      const d = ENCHANTS[id];
      return `<button class="card" ${attrs || ''}><div class="kind">${ic('gem')} Enchantment scroll · +${d.surcharge} Supply</div><div class="title">${esc(d.name)}</div><div class="desc">${esc(d.desc)} Bind it to one unit, forever.</div>${extra || ''}</button>`;
    }
    const d = kind === 'skill' ? SKILLS[id] : GEAR[id];
    return `<button class="card" ${attrs || ''}><div class="kind">${ic(kind === 'skill' ? 'scroll' : 'sword')} ${kind === 'skill' ? 'Skill' : 'Gear'} · ${d.cost} Supply</div><div class="title">${esc(d.name)}</div><div class="desc">${esc(d.desc)}</div>${extra || ''}</button>`;
  }

  function recruitCard(unit, enchant, attrs, extra) {
    const T = UNITS[unit];
    return `<button class="card" ${attrs || ''}>
      <div class="card-head"><canvas class="portrait" data-p="${unit}:P"></canvas>
      <div><div class="kind">Recruit · ${T.rarity} · ${T.cost} Supply</div><div class="title">${T.name}</div></div></div>
      ${enchant ? `<div class="chips"><span class="chip magic">${ic('gem')} ${esc(ENCHANTS[enchant].name)} +${ENCHANTS[enchant].surcharge}</span></div>` : ''}
      <div class="desc">${esc(T.desc)}${enchant ? ' ' + esc(ENCHANTS[enchant].desc) : ''}</div>${extra || ''}</button>`;
  }

  function spoilCard(sp, i, taken) {
    const attrs = `data-spoil="${i}" ${taken ? 'disabled' : ''}`;
    if (sp.type === 'recruit') return recruitCard(sp.unit, sp.enchant, attrs);
    if (sp.type === 'skill' || sp.type === 'gear' || sp.type === 'scroll') return itemCard(sp.type, sp.id, attrs);
    return `<button class="card" ${attrs}><div class="kind">${ic('gold')} Gold</div><div class="title">${sp.amount} gold</div></button>`;
  }

  function levelUpHTML(from, to) {
    if (!to || to <= from) return '';
    const a = COMMAND[from];
    const b = COMMAND[to];
    return `<div class="levelup">${ic('crown')}<div><b>Commander level ${to}!</b><div class="small">Supply ${a.supply} → ${b.supply}${b.cap > a.cap ? ` · units on the field ${a.cap} → ${b.cap}` : ''}</div></div></div>`;
  }

  function rewardScreen() {
    const run = UI.run;
    const p = run.pending;
    const bossDone = !p.bossRelics || p.bossRelicTaken;
    const li = R.levelInfo(run);
    const v = showView(
      `<div class="wrap">
        <div class="reward-head"><p class="eyebrow">${p.kind === 'boss' ? 'The champion falls' : 'The field is yours'}</p><h2>Victory</h2></div>
        ${levelUpHTML(p.lvFrom, p.lvTo)}
        <div class="panel loot">
          <span class="res xp">${ic('crown')} +${p.xp} XP <span class="small muted">(${li.max ? 'max level' : `${li.xp - li.from}/${li.to - li.from} to Lv ${li.lv + 1}`})</span></span>
          <span class="res gold">${ic('gold')} +${p.gold} gold${p.firstTry ? ' <span class="small muted">(first-try bonus included)</span>' : ''}</span>
          ${p.lean ? `<span class="res gold">${ic('command')} +${p.lean} gold for ${p.unspent} unspent Supply</span>` : ''}
          ${p.midas ? `<span class="res gold">${ic('gold')} +${p.midas} gold from Midas Touch</span>` : ''}
          <span class="res">${ic('gold')} ${run.gold} total</span>
        </div>
        ${p.objectives && p.objectives.length ? `<div class="panel objectives">${p.objectives
          .map((o) => `<div class="obj bonus ${o.done ? 'done' : 'failed'}">${ic(o.done ? 'check' : 'close')}<span>${esc(o.text)}${o.done ? ` <span class="reward">${esc(o.got)}</span>` : ''}</span></div>`)
          .join('')}</div>` : ''}
        ${p.prisoner && R.unitById(run, p.prisoner) ? `<p class="small good-text">The prisoner ${esc(R.unitById(run, p.prisoner).name)} the ${UNITS[R.unitById(run, p.prisoner).type].name} is free and joins your army.</p>` : ''}
        ${p.prisonerGold ? `<p class="small muted">The freed prisoner could not join a full army, but leaves you ${p.prisonerGold} gold in thanks.</p>` : ''}
        ${p.relicGained ? `<div><div class="eyebrow">Relic claimed</div><div class="cards">${relicCard(p.relicGained, 'disabled style="opacity:1"')}</div></div>` : ''}
        ${p.lootRelic ? `<div><div class="eyebrow">From the relic cache</div><div class="cards">${relicCard(p.lootRelic, 'disabled style="opacity:1"')}</div></div>` : ''}
        ${p.tome && p.tome.length ? `<div><div class="eyebrow">${p.tomeTaken ? 'The tome is read' : 'The Lost Tome: choose a skill'}</div>
          <div class="cards">${p.tome.map((id, i) => itemCard('skill', id, `data-tome="${i}" ${p.tomeTaken ? 'disabled' : ''}`)).join('')}</div></div>` : ''}
        ${p.bossRelics && p.bossRelics.length ? `<div><div class="eyebrow">${p.bossRelicTaken ? 'Boss relic claimed' : 'Choose a boss relic'}</div><div class="cards">${p.bossRelics.map((id) => relicCard(id, `data-boss="${id}" ${p.bossRelicTaken ? 'disabled' : ''}`)).join('')}</div></div>` : ''}
        <div><div class="eyebrow">${p.spoilTaken ? 'Spoils claimed' : 'Choose your spoils'}</div>
          <div class="cards">${p.spoils.map((sp, i) => spoilCard(sp, i, p.spoilTaken)).join('')}</div>
          <p class="small muted">Skills and gear go to your pack: slot them into units from the War Room or the Army screen.</p></div>
        <div class="row end">
          <button class="btn" id="rwArmy">${ic('army')} Army</button>
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
      b.onclick = () => {
        const i = +b.dataset.spoil;
        const sp = p.spoils[i];
        if (sp.type === 'recruit' && run.roster.length >= R.MAX_ROSTER) {
          toast('Your army is full. Dismiss a unit from the Army screen first.');
          return;
        }
        if (R.takeSpoil(run, i)) {
          sfx('coin');
          if (sp.type === 'recruit') toast(`${run.roster[run.roster.length - 1].name} the ${UNITS[sp.unit].name} joins your army.`);
          else if (sp.type !== 'gold') toast(`Added to your pack. Equip it from a unit's loadout.`);
          rewardScreen();
        }
      };
    $('#rwArmy', v).onclick = () => armySheet(() => rewardScreen());
    if ($('#rwSkip', v))
      $('#rwSkip', v).onclick = () => {
        R.skipSpoils(run);
        rewardScreen();
      };
    for (const b of $$('[data-tome]', v))
      b.onclick = () => {
        if (R.takeTome(run, +b.dataset.tome)) {
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
      if (it.kind === 'recruit') return recruitCard(it.unit, it.enchant, dis, price);
      if (it.kind === 'skill' || it.kind === 'gear' || it.kind === 'scroll') return itemCard(it.kind, it.id, dis, price);
      if (it.kind === 'relic')
        return `<button class="card" ${dis}><div class="kind">${ic('gem')} Relic · ${RELICS[it.relic].tier}</div><div class="title">${esc(RELICS[it.relic].name)}</div><div class="desc">${esc(RELICS[it.relic].desc)}</div>${price}</button>`;
      if (it.kind === 'supply')
        return `<button class="card" ${dis}><div class="kind">${ic('command')} Service</div><div class="title">Supply Cache</div><div class="desc">+1 Supply in every battle for the rest of the campaign.</div>${price}</button>`;
      return `<button class="card" ${dis}><div class="kind">${ic('crown')} Service</div><div class="title">War Manual</div><div class="desc">Gain 10 XP toward your next commander level.</div>${price}</button>`;
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
        ${section('Skills', ['skill'])}
        ${section('Gear', ['gear'])}
        ${section('Enchantments', ['scroll'])}
        ${section('Relics', ['relic'])}
        ${section('Services', ['supply', 'manual'])}
        <div class="row end"><button class="btn primary" id="shLeave">Leave the market</button></div>
      </div>`
    );
    for (const b of $$('[data-buy]', v))
      b.onclick = () => {
        const i = +b.dataset.buy;
        const it = p.stock[i];
        const before = R.commanderLevel(run);
        if (R.buy(run, i)) {
          sfx('coin');
          if (it.kind === 'manual' && R.commanderLevel(run) > before) toast(`Commander level ${R.commanderLevel(run)}! Supply ${R.supplyFor(run)}.`);
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
    const xp = 12 + 2 * (run.act - 1);
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">Campfire</p><h2>A night by the fire</h2></div>
        <div class="row">${resbar(run)}</div>
        ${p.done ? `<p class="hint">${p.done === 'drill' ? 'Your soldiers drill until dawn. Your command grows sharper.' : 'A quiet night of study and repair. The new item is in your pack.'}</p>${p.levels ? levelUpHTML(p.levels.from, p.levels.to) : ''}` : `
        <div class="cards">
          <button class="card" id="rsDrill"><div class="kind">${ic('crown')} Drill</div><div class="title">Drill the troops</div><div class="desc">Gain ${xp} XP toward your next commander level: more Supply, and in time more units on the field.</div></button>
        </div>
        <div><div class="eyebrow">Or study: take one skill</div><div class="cards">${p.skills.map((id, i) => itemCard('skill', id, `data-study="${i}"`)).join('')}</div></div>
        <div><div class="eyebrow">Or tinker: take one piece of gear</div><div class="cards">${p.gear.map((id, i) => itemCard('gear', id, `data-tinker="${i}"`)).join('')}</div></div>`}
        <div class="row end"><button class="btn" id="rsArmy">${ic('army')} Army</button><button class="btn primary" id="rsGo" ${p.done ? '' : 'disabled'}>Break camp</button></div>
      </div>`
    );
    if ($('#rsDrill', v))
      $('#rsDrill', v).onclick = () => {
        R.rest(run, 'drill');
        sfx('heal');
        restScreen();
      };
    for (const b of $$('[data-study]', v))
      b.onclick = () => {
        if (R.rest(run, 'study', +b.dataset.study)) {
          sfx('coin');
          restScreen();
        }
      };
    for (const b of $$('[data-tinker]', v))
      b.onclick = () => {
        if (R.rest(run, 'tinker', +b.dataset.tinker)) {
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
            .map((c) => `<button class="choice" data-choice="${esc(c.id)}" ${c.enabled ? '' : 'disabled'}><b>${esc(c.label)}</b><span>${esc(c.detail)}</span></button>`)
            .join('')}
        </div>
        ${p.result ? `<div class="row end"><button class="btn" id="evArmy">${ic('army')} Army</button><button class="btn primary" id="evGo">Continue</button></div>` : ''}
      </div>`
    );
    for (const b of $$('[data-choice]', v))
      b.onclick = async () => {
        const c = choices.find((x) => x.id === b.dataset.choice);
        let rid = null;
        if (c.pick) {
          rid = await pickUnit(c.label, esc(c.detail), (u) => ['common', 'uncommon'].includes(UNITS[u.type].rarity));
          if (!rid) return;
        }
        const before = R.commanderLevel(run);
        const out = R.chooseEvent(run, c.id, rid);
        if (out == null) {
          toast('That choice is not available.');
          return;
        }
        sfx('click');
        if (R.commanderLevel(run) > before) toast(`Commander level ${R.commanderLevel(run)}! Supply ${R.supplyFor(run)}.`);
        if (run.pending && run.pending.type === 'battle') {
          toast(out);
          route();
          return;
        }
        eventScreen();
      };
    if ($('#evArmy', v)) $('#evArmy', v).onclick = () => armySheet(() => eventScreen());
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
        <div><p class="eyebrow">${run.won ? 'The Spire is silent' : 'The campaign is over'}</p>
        <h2>${run.won ? 'Campaign won' : 'Campaign ended'}</h2></div>
        <p class="muted">${run.won ? 'The Ashen Tyrant is slain and the arena bows to your warband.' : `Your march ended in ${ACTS[run.act].short}, ${esc(ACTS[run.act].name)}.`}</p>
        <div class="end-stats">
          <div class="stat"><b>${st.battles}</b><span>Battles won</span></div>
          <div class="stat"><b>${st.losses}</b><span>Retries</span></div>
          <div class="stat"><b>${st.firstTry}</b><span>First-try wins</span></div>
          <div class="stat"><b>${R.commanderLevel(run)}</b><span>Commander level</span></div>
          <div class="stat"><b>${st.kills}</b><span>Enemies slain</span></div>
          <div class="stat"><b>${st.gold}</b><span>Gold earned</span></div>
        </div>
        <div class="roster">${run.roster
          .map((u) => `<div class="rcard"><canvas data-p="${u.type}:P"></canvas><span class="nm">${esc(u.name)}</span><span class="ty">${UNITS[u.type].name}${u.enchant ? ' · ' + esc(ENCHANTS[u.enchant].name) : ''}</span></div>`)
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
        <p>March through three acts on a branching map: battles, elites, merchants, campfires, events and treasure. Each act ends with a boss. You can lose as often as you need: a defeat sends you back to the war room to re-plan against the same enemy.</p>
        <h4>Supply and the war room</h4>
        <p>Before every battle you see the whole enemy army. Spend <b>Supply</b> to build your answer to it. Everything costs Supply: each unit, its level, its abilities, its skills and gear, and any enchantment on it. Two Level 1 Knights or one Level 2 Knight with better tricks? That choice is the heart of the game. Unspent Supply pays a little gold if you win.</p>
        <h4>Levels, abilities, skills and gear</h4>
        <ul>
          <li>Every unit picks 1 of 3 abilities at Level 1, and 1 of 3 more at Level 2. Stronger picks cost more Supply.</li>
          <li>Level 2 (+2 Supply): +20% HP, +15% power, the second ability and a second skill slot. Level 3 (+5): +40% HP, +30% power, a Mastery and a second gear slot.</li>
          <li>Skills and gear are items you own. Slot each one into a single unit. They cost Supply only when that unit fights.</li>
          <li>Enchantment scrolls bind a permanent power to one unit, forever. That unit costs a little more Supply to field.</li>
        </ul>
        <h4>Commander level</h4>
        <p>Victories earn XP. Each commander level raises your Supply, and some raise how many units may take the field. Elites, bosses and bonus goals pay extra XP.</p>
        <h4>Taking turns</h4>
        <ul>
          <li>The sides take turns, and the enemy goes first (a boss waits for its side's second turn). On your turn you pick <b>one unit</b>: it moves, acts, or both, then turns toward the nearest enemy. Then the enemy picks one of theirs.</li>
          <li>Acting starts that unit's <b>cooldown</b> (CD on its card). It counts down by 1 at the start of each of your turns, and at 0 the unit is ready again. A Cooldown 1 unit can go every turn; a Witch (Cooldown 3) every third turn. Moving without acting costs half.</li>
          <li>Any unit that is not cooling down can be picked. If none can do anything, your turn passes on its own. You can also <b>Pass</b> on purpose.</li>
          <li>The turn counter counts rounds: the enemy's move, then yours. Durations such as "roots for 2 turns" count the turns of the side they affect.</li>
        </ul>
        <h4>Damage, facing and defense</h4>
        <ul>
          <li>Physical attacks are reduced by <b>armor</b> and can be <b>blocked</b>: full block from the front, half from the side, never from behind.</li>
          <li>When a unit finishes its turn it turns to face the nearest enemy. To pick facings yourself with arrows, switch <b>Facing</b> in the menu; <b>Face only</b> always lets you turn a unit by hand.</li>
          <li>Magic ignores armor and block, but is reduced by <b>magic resistance</b>. No defense goes above 50%. Ghosts shrug off steel but fear magic; Mage Knights shrug off spells.</li>
          <li>Every attack shows its type: ${dmgIcon('phys')} a sword for <b>physical</b>, ${dmgIcon('magic')} a violet sparkle for <b>magic</b>. A unit's Power carries the icon of its main attack, and magic damage numbers float up in violet.</li>
        </ul>
        <h4>Missions</h4>
        <ul>
          <li>Rout the enemy, burn their banner, break a prison, kill a commander, hold a shrine, survive the waves, topple their totems, raze the buildings that send reinforcements, storm a castle gate, or stop a convoy of loot wagons. Routing always wins once no more reinforcements are coming.</li>
          <li>Bonus goals pay extra: loot on the field, fast wins, flawless wins, blocking reinforcements, or fielding a unit that sat out your last battle.</li>
        </ul>
        <h4>Buildings and siege</h4>
        <ul>
          <li>Walls, gates, towers, totems, tents, crypts, dens, portals and barricades are <b>buildings</b>. Stone ones shrug off swords and spells alike; wooden ones burn, taking extra damage from fire and magic; dark portals unravel under magic but barely notice steel.</li>
          <li><b>Siege damage</b> breaks them fast: the Trebuchet (+150% to buildings), a Siege Hammer (triple), the Demolisher skill (double), a Blasting Charge, the Golem's Boulder Toss, or the Sapper's Kit relic.</li>
        </ul>
        <h4>Reinforcements</h4>
        <ul>
          <li>Some battles bring enemy reinforcements on set turns: from the far edge, or out of tents, crypts, dens, portals and guardhouses. The war room shows the schedule; badges on buildings count down the turns.</li>
          <li>They arrive after the enemy's move. A turn ahead, red tiles mark where they will appear: a unit standing on one <b>blocks</b> that arrival, but takes 10 damage.</li>
          <li>Destroy a building and everything it had left to send is cut off.</li>
        </ul>
        <h4>Controls</h4>
        <ul>
          <li>Tap a unit, tap a blue tile to move, tap a red enemy to attack, then tap again to confirm. Use the buttons for abilities.</li>
          <li>Tap a rock, a chest, the shrine, a hazard or a red landing tile to see what it does.</li>
          <li>In the war room, tap a deployed unit again to open its loadout. Long-press any unit for details.</li>
          <li>Pinch, drag, or use + and − to zoom. The eye button shows every tile an enemy unit could strike on its next turn.</li>
          <li>Battles play best with your phone turned sideways.</li>
        </ul>
      </div>
      <div class="actions"><button class="btn primary" data-close>Got it</button></div>`
    );
  }

  function codexSheet(tab) {
    const t = tab || 'units';
    let body = '';
    if (t === 'units' || t === 'enemies') {
      const types = t === 'units' ? D.RECRUITABLE : Object.keys(UNITS).filter((k) => ['enemy', 'boss'].includes(UNITS[k].rarity) || (UNITS[k].material && k !== 'cage' && k !== 'warbanner'));
      body = `<div class="codex-grid">${types
        .map((type) => {
          const u = R.unitStats(null, { type, level: 1 }, t === 'units' ? 'P' : 'E');
          const T = UNITS[type];
          const ab = T.abilities
            ? `<div class="small"><b>Level 1:</b> ${T.abilities[1].map((id) => esc(ABILITIES[id].name)).join(' / ')}<br><b>Level 2:</b> ${T.abilities[2].map((id) => esc(ABILITIES[id].name)).join(' / ')}<br><b>Mastery:</b> ${esc(MASTERY[type].name)}</div>`
            : '';
          return `<div class="card"><div class="card-head"><canvas class="portrait" data-p="${type}:${t === 'units' ? 'P' : 'E'}"></canvas>
            <div><div class="kind">${T.rarity}${T.cost ? ' · ' + T.cost + ' Supply' : ''}</div><div class="title">${T.name}</div></div></div>
            ${statsHTML(u)}${actsHTML(u)}${ab}
            <p class="small muted">${esc(T.tip)}</p></div>`;
        })
        .join('')}</div>`;
    } else {
      const src = t === 'skills' ? SKILLS : t === 'gear' ? GEAR : ENCHANTS;
      body = `<div class="army-list">${Object.values(src)
        .map((d) => `<div class="card"><div class="kind">${t === 'enchant' ? `+${d.surcharge} Supply surcharge` : `${d.cost} Supply`}</div><div class="title">${esc(d.name)}</div><div class="desc">${esc(d.desc)}</div></div>`)
        .join('')}</div>`;
    }
    openSheet(
      `${sheetHead('Codex', 'Every unit you can recruit, every foe you will face, and every skill, piece of gear and enchantment.')}
      <div class="tabs wrap-tabs">${[['units', 'Units'], ['enemies', 'Foes'], ['skills', 'Skills'], ['gear', 'Gear'], ['enchant', 'Enchant']]
        .map(([k, l]) => `<button class="btn ${t === k ? 'on' : ''}" data-cx="${k}">${l}</button>`)
        .join('')}</div>
      ${body}`,
      (sh) => {
        for (const b of $$('[data-cx]', sh)) b.onclick = () => codexSheet(b.dataset.cx);
      }
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
