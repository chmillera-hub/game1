// Screens and touch controls: title, campaign setup, map, army and loadouts, war room,
// battle, rewards, shop, rest, events, help and codex.
(function (root) {
  'use strict';
  const AG = root.AG;
  const D = AG.Data;
  const { UNITS, ABILITIES, TALENTS, MASTERY, SKILLS, GEAR, ENCHANTS, RELICS, DIFFICULTIES, ACTS, COMMAND, LEVEL_COST, SKILL_SLOTS, GEAR_SLOTS, TALENT_SLOTS } = D;
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
  // Battle speed, 1x or 2x: the fast-forward button switches it (an old 4x setting plays
  // at 2x). At 1x a battle plays at about half the animations' full pace, easy to follow.
  const speedOf = () => (UI.prefs.speed > 1 || UI.prefs.fast ? 2 : 1);
  const BASE_PACE = 0.512;
  const paceOf = () => speedOf() * BASE_PACE;
  const pause = (ms) => sleep(ms / paceOf());
  const stars = (n) => (n > 1 ? '★'.repeat(n) : '');
  const cap1 = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const PREFS_KEY = 'arena-gauntlet-prefs';

  const UI = {
    run: null,
    board: null,
    battle: null,
    wr: null,
    prefs: { fast: false, speed: 1, threat: false, manualFacing: false, autoBattle: true, guide: true },
  };
  try {
    Object.assign(UI.prefs, JSON.parse(root.localStorage.getItem(PREFS_KEY) || '{}'));
  } catch (e) {
    /* storage unavailable */
  }
  // These are no longer settings: your army always fights on its own, units face the
  // nearest enemy, and placing a unit always asks about its kit.
  Object.assign(UI.prefs, { autoBattle: true, manualFacing: false, guide: true });
  function savePrefs() {
    try {
      root.localStorage.setItem(PREFS_KEY, JSON.stringify(UI.prefs));
    } catch (e) {
      /* storage unavailable */
    }
  }

  const sfx = (n) => AG.Audio && AG.Audio.play(n);
  // The background music's mood: 'camp' between battles, 'battle' or 'boss' in one.
  const music = (mood) => AG.Music && AG.Music.set(mood);

  // ------------------------------------------------------------ shared bits

  let toastTimer = 0;
  function toast(msg, ms) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (t.hidden = true), ms || 2400);
  }

  function hideToast() {
    clearTimeout(toastTimer);
    $('#toast').hidden = true;
  }

  // The army's Supply in the War Room, pinned to the top of a sheet as you scroll it.
  function budgetBar(used, cap, label) {
    const left = cap - used;
    return `<div class="budget pin ${left < 0 ? 'over' : ''}">${ic('command')} ${left < 0 ? `<b>${-left}</b> over budget` : `Supply left: <b>${left}</b>`}
      <span class="grow"></span><span class="small muted">${label || 'Army'} ${used}/${cap}</span></div>`;
  }

  // A bubble over what you just tapped: what it cost and the Supply left, fading in a moment.
  // `rect` is where the tapped button was (the sheet redraws under it), `was` and `now` the
  // Supply left before and after.
  function supplyPop(rect, was, now) {
    for (const old of $$('.sup-pop')) old.remove();
    const took = was - now;
    const el = document.createElement('div');
    el.className = `sup-pop ${now < 0 ? 'over' : took < 0 ? 'back' : ''}`;
    el.setAttribute('aria-hidden', 'true');
    el.innerHTML = `${took > 0 ? `<b>+${took}</b> Supply` : took < 0 ? `<b>−${-took}</b> Supply` : 'Free'} · ${now < 0 ? `<b>${-now}</b> over` : `<b>${now}</b> left`}`;
    document.body.appendChild(el);
    const bar = $('#sheet .budget.pin');
    // Never over the pinned bar itself: its number is the one to read.
    const floor = bar ? bar.getBoundingClientRect().bottom + 6 : 8;
    const x = rect.left + rect.width / 2 - el.offsetWidth / 2;
    el.style.left = Math.max(8, Math.min(innerWidth - el.offsetWidth - 8, x)) + 'px';
    el.style.top = Math.max(floor, rect.top - el.offsetHeight - 6) + 'px';
    setTimeout(() => el.remove(), 1800);
    if (bar) bar.classList.add('bump');
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

  // `back`: the sheet has its own Back (or Done) button, so no X: an X there would close
  // everything at once. A tap outside the sheet still closes it all.
  function sheetHead(title, sub, back) {
    return `<div class="sheet-head"><div class="grow"><h3>${title}</h3>${sub ? `<div class="small muted">${sub}</div>` : ''}</div>
      ${back ? '' : `<button class="btn icon-only ghost" data-close aria-label="Close">${ic('close')}</button>`}</div>`;
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
        `${sheetHead(esc(title), null, true)}<p class="muted">${text}</p>
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
        return (a.range[0] === a.range[1] ? String(a.range[0]) : a.range[0] + '-' + a.range[1]) + (a.straight ? ' straight' : '');
      case 'line':
        return 'Line ' + a.len;
      case 'charge':
        return 'Charge ' + a.len;
      case 'cone':
        return (a.fan ? 'Spray ' : 'Cone ') + a.len;
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
    return `<div class="stats">${power}${st(pct(u.armor), 'Armor')}${st(pct(u.res), 'M.Res')}${st(u.facing < 0 ? '-' : pct(u.block), 'Block')}${st(E.cooldown(u), 'CD', 'Cooldown: after acting, it passes this many of its turns. Moving alone is free.')}${st(u.move, 'Move')}${st(rangeLabel(a), 'Range')}${st(u.spd || '-', 'SPD', 'Speed: in each cycle of turns, faster units go first')}</div>`;
  }

  // A shove or pull in a preview: where it goes and what it hits.
  function shoveText(k) {
    if (k === 'resist') return 'stands firm';
    const s = UI.battle && UI.battle.s;
    const moved = k.n ? `${k.pull ? 'dragged' : 'shoved'} ${k.n} tile${k.n > 1 ? 's' : ''}` : k.pull ? 'not dragged' : 'not moved';
    const other = k.other != null && s && s.byId[k.other];
    const into = {
      rock: `slams into the ${obstacleName().toLowerCase()}: <b>${k.dmg}</b>`,
      edge: `slams into the edge: <b>${k.dmg}</b>`,
      unit: `crashes into ${other ? esc(other.team === 'P' ? other.name : UNITS[other.type].name) : 'a unit'}: <b>${k.dmg}</b> each`,
      water: `splashes into the water: <b>${k.dmg}</b>, then climbs out rooted`,
      lava: `falls into the lava: <b>${k.dmg}</b>, then climbs out burning`,
    }[k.end];
    return into ? `${moved}, ${into}` : moved;
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
    if (fx.knock) bits.push(`shoves the target back ${fx.knock} tile${fx.knock > 1 ? 's' : ''}`);
    if (fx.pull) bits.push(`drags the target ${fx.pull} tile${fx.pull > 1 ? 's' : ''} toward it`);
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

  // Charges left and the act's own cooldown: how long until it can be used again.
  function usesText(a) {
    const bits = [];
    if (a.uses) {
      const left = a.left === Infinity || a.left == null ? a.uses : a.left;
      bits.push(`${left} of ${a.uses} use${a.uses > 1 ? 's' : ''} left`);
    }
    if (a.cd) bits.push(a.cdLeft > 0 ? `usable again in ${a.cdLeft} of its turns` : `after each use it waits ${a.cd} of its turns`);
    return bits.length ? ' ' + cap1(bits.join('; ')) + '.' : '';
  }

  // Plain-language rules text for one of a unit's acts.
  function actText(u, a) {
    const base = a.fixed != null ? Math.round(a.fixed * (a.dmg === 'magic' ? 1 + (u.props.magicMult || 0) : 1)) : Math.round(u.pow * (a.mult || 1));
    const dt = a.dmg === 'magic' ? 'magic' : 'physical';
    const area = a.dmg && ['cleave', 'quake', 'cross', 'nova', 'blast', 'line', 'cone', 'leap'].includes(a.kind);
    const ff = !area ? '' : E.hitsAllies(u, a) ? ' Hits allies in the area too.' : ' Spares allies.';
    let t;
    switch (a.kind) {
      case 'strike': {
        const where = rangeText(a.range) + (a.straight ? ' in a straight, open line' : '');
        t = a.dmg ? `${base} ${dt} damage to one enemy ${where}.` : `Targets one enemy ${where}.`;
        break;
      }
      case 'cleave':
        t = `${base} ${dt} damage to every adjacent ${E.hitsAllies(u, a) ? 'unit, friend or foe' : 'enemy'}.`;
        break;
      case 'quake':
        t = `${base} ${dt} damage to an adjacent enemy and every unit beside it.${ff}`;
        break;
      case 'blast':
        t = `${a.dmg ? base + ' ' + dt + ' damage to' : 'Affects enemies in'} a ${a.pattern === 'square' ? '3x3' : '5-tile'} area ${rangeText(a.range)}.${ff}`;
        break;
      case 'line':
        t = `${base} ${dt} damage to every unit in a straight line up to ${a.len} tiles.${E.hitsAllies(u, a) ? ' Hits allies too.' : ' Passes through allies.'}`;
        break;
      case 'cone':
        t = a.fan
          ? `${base} ${dt} damage in a spray: the row of three right in front of it${a.len > 2 ? ` (${a.len - 1} rows deep)` : ''}, and one tile beyond the middle.${ff}`
          : `${base} ${dt} damage across a cone ${a.len} tiles deep.${ff}`;
        break;
      case 'cross':
        t = `${base} ${dt} damage in all four directions, up to ${a.len} tiles.${ff}`;
        break;
      case 'nova':
        t = a.dmg ? `${base} ${dt} damage to everyone within ${a.radius} tile${a.radius > 1 ? 's' : ''}.${ff}` : `Affects every enemy within ${a.radius} tile${a.radius > 1 ? 's' : ''}.`;
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
      case 'charge':
        t = `Charges up to ${a.len} tiles in a straight line, through every unit in the way, and strikes each enemy it passes for ${base} ${dt} damage. It stops on the farthest open tile.`;
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
        if (a.straight) reach = reach.filter(([x, y]) => x === ux || y === uy);
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
      case 'charge':
        hit = E.lineTiles(ms, ux, uy, 0, a.len - 1);
        land = [ux, uy - a.len];
        break;
      case 'cone':
        hit = E.coneTiles(ms, ux, uy, 0, a.len, a.fan);
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
    pact: 'Shadow Pact (its Level 3 mastery): the first 2 enemies it slays each battle rise as skeletons on your side.',
    shadowstep: 'Slips through enemy units.',
    stoneskin: 'Immune to poison and paralysis.',
    flying: 'Flies over units, water, lava and rocks.',
    immobile: 'Rooted in place: cannot move.',
    shieldwall: 'Full block from the sides.',
    retaliate: 'Strikes back for half its damage when hit in melee.',
    bloodrage: 'Its basic attack heals it 5 HP per enemy struck.',
    bloodlust: 'Slaying an enemy resets its cooldown: it is ready again next turn.',
    secondwind: 'Once per battle, survives a fatal blow with 1 HP.',
    phoenix: 'The first time it falls, it rises again with half HP.',
    steadfast: 'Immune to paralysis, roots, shoves and pulls.',
    poisonproof: 'Immune to poison.',
    paraproof: 'Immune to paralysis.',
    undead: 'Undead: immune to poison.',
    aura_barrier: 'Barrier Aura: allies within reach gain +25% armor and +25% magic resistance.',
    aegisfield: 'Its aura also softens physical blows by 15%.',
    steelfield: 'Its aura also grants +10% armor.',
    auramend: 'Allies in its aura have +2 Regen.',
    purge: 'Allies in its aura are cured of roots and burns at the start of each of its turns.',
    thornwall: 'Its shrubs are tougher and prick melee attackers.',
    ironwood: 'Its shrubs have 40% armor and magic resistance.',
    ridedown: 'After moving 3 or more tiles, its basic attack shoves the target back 1 tile.',
    stormcaller: 'At the start of each of its turns, lightning strikes the nearest enemy within 3 tiles for 5.',
    midas: 'Every enemy it slays earns 6 gold.',
    thunderstep: 'Enemies next to where it stops moving take 6 magic damage.',
    volatile: 'Explodes when destroyed, hurting everything next to it.',
    trollblood: 'Regenerates unless magic or fire hurt it since its last turn.',
    cart: `Rolls ${UNITS.cart.move} tile${UNITS.cart.move > 1 ? 's' : ''} toward the left edge after every enemy turn, and escapes there.`,
    big: 'Huge: cannot be shoved or dragged.',
    martyr: 'When it falls, heals allies within 2 tiles for 20.',
    structure: 'A structure: you can win without destroying it.',
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
    if (P.totemRage) out.push('At the start of their turn, its allies within 2 tiles fly into a frenzy: 25% more damage. Topple it and the frenzy fades.');
    const coins = u.bounty || (u.team !== 'P' && u.salvage);
    if (coins) out.push(`Break it and your army picks up ${coins} gold, paid with the battle's gold when you win.`);
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
    if (u.regen) out.push(`Regen ${u.regen}: heals ${u.regen} HP each time it takes a turn (not when it sits one out).`);
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
    if (u.boss) out.push('Boss: immune to paralysis, shoves and pulls.');
    return [...new Set(out)];
  }

  function hpClass(f) {
    return f > 0.5 ? '' : f > 0.25 ? 'mid' : 'low';
  }

  function statusChips(u) {
    const chips = [];
    if (u.para > 0) chips.push(`<span class="chip warn">Paralyzed ${u.para}</span>`);
    if (u.poison) {
      // Poisons from several sources add up: the total a turn, and how many are running.
      const n = E.poisonStacks(u).length;
      chips.push(`<span class="chip poison">Poisoned ${u.poison.turns} · ${u.poison.dmg} a turn${n > 1 ? ` (${n} sources)` : ''}</span>`);
    }
    if (u.burn) chips.push(`<span class="chip warn">Burning ${u.burn.turns}</span>`);
    if (u.root > 0) chips.push(`<span class="chip good">Rooted ${u.root}</span>`);
    if (u.weak > 0) chips.push(`<span class="chip magic">Weakened ${u.weak}</span>`);
    if (u.mark > 0) chips.push(`<span class="chip bad">Marked ${u.mark}</span>`);
    if (u.frenzy > 0) chips.push(`<span class="chip bad" title="Frenzy: +25% damage for ${u.frenzy} more of its turns">Frenzy ${u.frenzy} (+25% damage)</span>`);
    if (u.shield > 0) chips.push(`<span class="chip">${ic('shield')} Shield ${u.shield}</span>`);
    // Grown in this battle.
    if (u.champion) chips.push(`<span class="chip warn">${ic('crown')} Champion</span>`);
    if (u.trophies) chips.push(`<span class="chip warn">${ic('star')} Trophies ${u.trophies} · +${u.trophies * 10}%</span>`);
    if (u.fury) chips.push(`<span class="chip bad">Fury +${u.fury * 5}%</span>`);
    if (u.harvest) chips.push(`<span class="chip magic">Souls ${u.harvest} · +${u.harvest * 10}%</span>`);
    if (u.braced) chips.push(`<span class="chip">${ic('shield')} Holding the line</span>`);
    if (u.charge) chips.push(`<span class="chip magic">Charge ${u.charge} · +${u.charge * 25}%</span>`);
    if (u.runes) chips.push(`<span class="chip magic">Runes ${u.runes}</span>`);
    if (u.sink) chips.push(`<span class="chip magic">Spell sunk · +50%</span>`);
    if (u.spree) chips.push(`<span class="chip warn">On a spree · x2</span>`);
    if (u.illusion) chips.push(`<span class="chip">Mirror image</span>`);
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
    // The enchantment: tap it to read what it does.
    if (u.enchant && ENCHANTS[u.enchant]) chips.push(`<button type="button" class="chip magic tap" data-ench="${u.enchant}" title="${esc(ENCHANTS[u.enchant].desc)}">${ic('gem')} ${esc(ENCHANTS[u.enchant].name)}</button>`);
    // A Level 3 unit's mastery (a Witch's Shadow Pact, which raises skeletons): tap it too.
    if (u.level >= 3 && MASTERY[u.type]) chips.push(`<button type="button" class="chip mastery tap" data-mastery="${u.type}" title="${esc(MASTERY[u.type].desc)}">${ic('star')} ${esc(MASTERY[u.type].name)}</button>`);
    // Regen counts a Mending Light aura it stands in during a battle.
    const regen = o.status && UI.battle && u.alive ? E.regenOf(UI.battle.s, u) : u.regen;
    if (regen) chips.push(`<span class="chip good" title="Heals ${regen} HP each time it takes a turn">${ic('heart')} Regen ${regen}</span>`);
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
    return `<div class="act-row">${patternSVG(a, u.team)}<p class="ability"><b>${a.dmg ? dmgIcon(a.dmg) : ''}${esc(ability ? a.name : actLabel(a, 0))}${ability ? ' <span class="tag">ability</span>' : ''}.</b> ${esc(actText(u, a))}</p></div>`;
  }

  // What an act is called on screen: a unit's own main act is its basic attack (or basic
  // ability, when it heals or helps instead); only the abilities it picks go by name.
  function actLabel(a, i) {
    if (i || a.kind === 'none') return a.name;
    return a.dmg ? 'Basic attack' : 'Basic ability';
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
    </div>`;
  }

  function commanderSheet() {
    const run = UI.run;
    const li = R.levelInfo(run);
    const rows = COMMAND.slice(1)
      .map((c, i) => {
        const lv = i + 1;
        return `<tr class="${lv === li.lv ? 'cur' : lv < li.lv ? 'past' : ''}"><td>${lv}</td><td>${c.xp}</td><td>${c.supply}</td></tr>`;
      })
      .join('');
    openSheet(
      `${sheetHead('Commander level', `${li.max ? 'Maximum level reached.' : `${li.xp} XP · ${li.to - li.xp} XP to level ${li.lv + 1}`}`)}
      <p class="muted">Victories earn XP. Each commander level raises the Supply you can spend in every battle. Field as many units as your Supply pays for. Elites, bosses and bonus goals pay more XP.</p>
      <table class="lvtable"><thead><tr><th>Level</th><th>XP</th><th>Supply</th></tr></thead><tbody>${rows}</tbody></table>
      <p class="small muted">Right now: ${R.supplyFor(run)} Supply, after relics and bonuses.</p>
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
    music('camp');
    stopDiorama();
    $('#battle').hidden = true;
    if (UI.board) UI.board.stop();
    const v = $('#view');
    // Redrawing the same screen (after a pick or a purchase) keeps its scroll position;
    // a new screen starts at the top. A screen is known by its heading.
    const heading = () => {
      const h = v.querySelector('h2');
      return h ? h.textContent : null;
    };
    const was = v.hidden ? null : heading();
    const top = v.scrollTop;
    const winY = root.scrollY || 0;
    v.hidden = false;
    v.className = 'screen ' + (cls || '');
    v.innerHTML = html;
    if (was && was === heading()) {
      v.scrollTop = top;
      if (winY) root.scrollTo(0, winY);
    } else v.scrollTop = 0;
    drawPortraits(v);
    bindRelics(v);
    bindResbar(v);
    bindRecruitInfo(v);
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
    b.onDragMove = (h) => UI.boardDragMove && UI.boardDragMove(h);
    b.onDragEnd = (h, moved) => UI.boardDragEnd && UI.boardDragEnd(h, moved);
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
    // No zoom buttons: pinch (or the mouse wheel) zooms, a drag pans.
    t.innerHTML = extra || '';
    relicBar();
  }

  // Your relics as small round badges over the board, in the War Room and in battle: tap
  // one to see what it does.
  const RELIC_ICON = {
    war_horn: 'banner', lucky_coin: 'gold', phalanx_standard: 'shield', lone_wolf: 'target', powder_keg: 'fire', firecrackers: 'star',
    coin_purse: 'gold', healing_salve: 'heart', scout_map: 'eye', drill_manual: 'book', pathfinder: 'boot', vampire_fang: 'heart',
    sappers_kit: 'fire', mana_crystal: 'magic', bloodstone: 'heart', thorned_mail: 'block', executioner_hood: 'skull',
    plague_mask: 'skull', wildfire_oil: 'fire', trophy_rack: 'crown', storm_jar: 'magic', blood_pact: 'heart', phoenix_feather: 'fire',
    guild_seal: 'bag', legion_banner: 'banner', sands_of_haste: 'hourglass', recruiters_bell: 'army', gamblers_dice: 'star',
    shadow_cloak: 'eye', mirror_aegis: 'shield', warlord_helm: 'crown', alchemist_stone: 'gem', necro_bell: 'crossbones',
    glass_crown: 'crown', tyrant_heart: 'command', titan_gauntlet: 'swords', eternal_flame: 'fire', kings_ransom: 'gold',
    crown_command: 'crown', sacred_chalice: 'heart', echo_drum: 'banner', cursed_blade: 'sword',
    iron_ram: 'shield', tide_conch: 'star', anchor_stone: 'block',
    worldbreaker: 'swords', mountain_heart: 'heart', storm_banner: 'banner', blood_moon: 'heart',
  };

  // A relic's tier for its card, flagged when it is cursed (a big upside with a real cost).
  function relicTier(r) {
    return `${r.tier}${r.cursed ? ' · <span class="cursed">Cursed</span>' : ''}`;
  }
  function relicBar() {
    const bar = $('#relicBar');
    const run = UI.run;
    const ids = run && !(UI.battle && UI.battle.exhibition) ? run.relics.filter((id) => RELICS[id]) : [];
    bar.innerHTML = ids
      .map((id) => `<button class="relic-dot tier-${RELICS[id].tier}" data-relic="${id}" aria-label="${esc(RELICS[id].name)}">${ic(RELIC_ICON[id] || 'gem')}</button>`)
      .join('');
    bar.classList.toggle('dense', ids.length > 14);
    bar.classList.toggle('packed', ids.length > 22);
    for (const b of $$('[data-relic]', bar))
      b.onclick = () => {
        const r = RELICS[b.dataset.relic];
        toast(`${r.name}: ${r.desc}`, 3500);
      };
  }

  // Each army's Supply in small badges by its own back row: the enemy's at the top right,
  // yours at the bottom left. In battle, what is still standing of what has taken the
  // field (25/40), and any reinforcements still to come; in the War Room, what you are
  // fielding against what the enemy brings. Pass null to hide them.
  function supplyBadges(sides) {
    for (const team of ['P', 'E']) {
      const el = $(team === 'P' ? '#supP' : '#supE');
      if (!el) continue;
      const x = sides && sides[team];
      el.hidden = !x;
      if (!x) continue;
      el.innerHTML = `<span class="sup-who">${esc(x.label)}</span><b>${x.left != null ? `${x.left}<small>/${x.total}</small>` : x.total}</b><span class="sup-unit">Supply</span>${x.coming ? `<span class="sup-more">+${x.coming} coming</span>` : ''}`;
      el.title = x.tip || (x.left != null ? `${x.label}: ${x.left} of ${x.total} Supply still standing${x.coming ? `, ${x.coming} more on the way` : ''}` : `${x.label}: ${x.total} Supply${x.coming ? `, ${x.coming} more in reinforcements` : ''}`);
    }
    // The relic row wraps before the enemy's badge in the top-right corner instead of running under it.
    const e = $('#supE');
    const bar = $('#relicBar');
    if (bar) bar.style.right = `${Math.max(56, e && !e.hidden ? e.offsetWidth + 8 : 0)}px`;
  }

  // A side's Supply in battle: still standing, all that has taken the field, still to come.
  function battleSupply(s, team) {
    let left = 0;
    let total = 0;
    for (const u of s.units) {
      if (u.team !== team || !u.supply) continue;
      total += u.supply;
      if (u.alive && !u.escaped) left += u.supply;
    }
    let coming = 0;
    for (const w of s.waves || []) if ((w.team || 'E') === team && w.state === 'pending') for (const sp of w.units) coming += sp.supply || 0;
    return { left, total, coming };
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
    const hall = R.loadHall();
    const run = UI.run;
    const pendingBattle = run && run.pending && run.pending.type === 'battle';
    const v = showView(
      `<div class="wrap">
        <div class="title-grid">
          <div class="wrap" style="margin:0;gap:14px">
            <p class="eyebrow">A tactics roguelike</p>
            <h1 class="wordmark">Arena<br>Gauntlet</h1>
            <p class="lab-tag">${ic('star')} Experiment: the fun pass</p>
            <p class="tagline">Scout the enemy, spend your Supply on the perfect counter, and fight through three acts of isometric battles. Lose, re-plan, and try again.</p>
            <div class="title-actions">
              ${run ? `<button class="btn primary" id="tCont">${ic('flag')} Continue · ${ACTS[run.act].short}${pendingBattle ? ' · ' + esc(run.pending.enc.name) : ''}</button>` : ''}
              <button class="btn ${run ? '' : 'primary'}" id="tNew">${ic('swords')} New campaign</button>
              <div class="row"><button class="btn grow" id="tHelp">${ic('help')} How to play</button>
              <button class="btn grow" id="tCodex">${ic('book')} Codex</button></div>
              ${hall.legends.length + hall.queue.length ? `<button class="btn" id="tHall">${ic('crown')} Hall of Fame · ${hall.legends.length + hall.queue.length}${hall.queue.length ? ` (${hall.queue.length} waiting to climb)` : ''}</button>` : ''}
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
    if ($('#tHall', v)) $('#tHall', v).onclick = () => hallScreen(title);
    requestAnimationFrame(() => startDiorama($('#diorama')));
  }

  // ------------------------------------------------------------ new campaign

  // A new campaign drafts its army: five units, a relic, a skill and a piece of gear, each
  // one of three. Back undoes a pick; Start over deals a fresh draft.
  function newCampaign() {
    let seed = ((Math.random() * 2 ** 31) >>> 0) + 1;
    const picks = [];
    const steps = R.DRAFT_STEPS;
    const HEAD = { unit: 'Choose a unit', relic: 'Choose a relic', skill: 'Choose a skill', gear: 'Choose gear' };
    const WHY = {
      unit: 'Five units make your starting army, on top of your Cleric: every army has one, the only unit that heals. It fights in every battle, free of Supply, and you choose where it stands. Every unit comes with a talent of its class, a different one for each unit of a class.',
      relic: 'A relic works for the whole campaign.',
      skill: 'A skill goes in a unit\'s skill slot. Only skills one of your units can use are offered.',
      gear: 'Gear goes in a unit\'s gear slot. Only gear one of your units can use is offered.',
    };
    const option = (kind, id, i, offer) => {
      const attrs = `data-dpick="${i}" data-choose`;
      if (kind === 'unit') {
        // Every number up front: HP, damage, armor, magic resistance, block, cooldown,
        // move, range and speed, and the talent it brings.
        const T = UNITS[id];
        const u = recruitStats(id, null);
        return recruitCard(id, null, attrs, `<div class="small"><b>${esc(cap1(T.role))} · ${u.maxHp} HP</b></div>${statsHTML(u)}`, offer.talents && offer.talents[i]);
      }
      if (kind === 'relic') return relicCard(id, attrs);
      return itemCard(kind, id, attrs);
    };
    // The army so far: your Cleric, already in place (tap it for the details), then the
    // picks still to come as empty places.
    const armyHTML = () => {
      const ct = R.draftClericTalent(seed);
      const cleric = `<span class="draft-core" role="button" tabindex="0" data-rinfo="cleric::${ct || ''}" title="Your Cleric: free, in every battle. Tap for the details."><canvas data-p="cleric:P"></canvas><small>Cleric</small></span>`;
      // Each unit you have drafted opens its details too: attacks, abilities and talent,
      // to choose the relic, skill and gear by.
      const brought = R.draftBrought(seed, picks.slice(0, 5));
      const units =
        cleric +
        [0, 1, 2, 3, 4]
          .map((i) =>
            picks[i]
              ? `<span class="draft-unit" role="button" tabindex="0" data-rinfo="${picks[i]}::${brought[i] || ''}" title="${esc(UNITS[picks[i]].name)}: tap for the details" aria-label="${esc(UNITS[picks[i]].name)} details"><canvas data-p="${picks[i]}:P"></canvas></span>`
              : '<span class="draft-empty"></span>'
          )
          .join('');
      const clericLine = `<p class="small muted draft-core-note">${ic('heart')} <b>Your Cleric</b> is already in: the only unit that heals, free of Supply, and in every battle${ct && TALENTS[ct] ? `. It comes with the <b class="talent-name">${esc(TALENTS[ct].name)}</b> talent` : ''}. Tap it for the details.</p>`;
      const thing = (i, icon, name) => (picks[i] ? `<span class="chip">${ic(icon)} ${esc(name(picks[i]))}</span>` : `<span class="chip draft-todo">${ic(icon)} …</span>`);
      return `<div class="draft-army"><div class="unit-strip">${units}</div>
        <div class="chips">${thing(5, 'gem', (id) => RELICS[id].name)}${thing(6, 'scroll', (id) => SKILLS[id].name)}${thing(7, 'sword', (id) => GEAR[id].name)}<span class="chip warn">${ic('gold')} ${R.DRAFT_GOLD}</span></div></div>${
          picks.length < 5 ? clericLine : `<p class="small muted draft-core-note">${ic('help')} Tap any unit above for its details: attacks, abilities and the talent it comes with.</p>`
        }`;
    };
    const render = () => {
      const step = picks.length;
      const offer = R.draftOffer(seed, step, picks);
      // Each pick is a new heading, so the page starts at the top.
      const body = offer
        ? `<div><p class="eyebrow">New campaign · pick ${step + 1} of ${steps.length}</p><h2>${HEAD[offer.kind]}${offer.kind === 'unit' ? ` (${step + 1} of 5)` : ''}</h2></div>
          ${armyHTML()}
          <p class="muted">${WHY[offer.kind]}</p>
          <div class="choice-grid">${offer.options.map((id, i) => option(offer.kind, id, i, offer)).join('')}</div>`
        : `<div><p class="eyebrow">New campaign · your army</p><h2>Ready to march</h2></div>
          ${armyHTML()}
          <p class="muted">You start with ${R.DRAFT_GOLD} gold, ${COMMAND[1].supply} Supply per battle. Field as many units as your Supply pays for. There is no difficulty setting: each round you choose an easy, a medium or an elite battle.</p>
          <button class="btn primary wide" id="ncGo">${ic('swords')} March to the Borderlands</button>
          <h3>Your army</h3>
          <div class="army-list">${picks
            .slice(0, 5)
            .map((t, i) => `<div class="army-row tappable" role="button" tabindex="0" data-rinfo="${t}::${R.draftBrought(seed, picks.slice(0, 5))[i] || ''}"><canvas class="portrait" data-p="${t}:P"></canvas><div class="nm"><b>${esc(UNITS[t].name)}</b><div class="small muted">${esc(UNITS[t].desc)}</div></div><span class="chip warn">${UNITS[t].cost}</span></div>`)
            .join('')}</div>
          <div class="army-list">${[
            ['scroll', 'gem', RELICS[picks[5]], 'Relic'],
            ['skill', 'scroll', SKILLS[picks[6]], `Skill · ${SKILLS[picks[6]].cost} Supply`],
            ['gear', 'sword', GEAR[picks[7]], `Gear · ${GEAR[picks[7]].cost} Supply`],
          ]
            .map(([cls, icon, d, kind]) => `<div class="army-row"><div class="itemico ${cls}">${ic(icon)}</div><div class="nm"><b>${esc(d.name)}</b> <span class="small muted">${kind}</span><div class="small muted">${esc(d.desc)}</div></div></div>`)
            .join('')}</div>`;
      const v = showView(
        `<div class="wrap">
          <div class="row"><button class="btn ghost" id="ncBack">${ic('undo')} Back</button><span class="grow"></span><button class="btn ghost" id="ncAgain">Start over</button></div>
          ${body}
        </div>`
      );
      $('#ncBack', v).onclick = () => {
        if (!picks.length) return title();
        picks.pop();
        sfx('click');
        render();
      };
      $('#ncAgain', v).onclick = () => {
        seed = ((Math.random() * 2 ** 31) >>> 0) + 1;
        picks.length = 0;
        sfx('click');
        render();
      };
      for (const b of $$('[data-dpick]', v))
        b.onclick = () => {
          picks.push(offer.options[+b.dataset.dpick]);
          sfx('select');
          render();
        };
      if ($('#ncGo', v))
        $('#ncGo', v).onclick = () => {
          R.clearSave();
          UI.run = R.newRun({ seed, draft: { units: picks.slice(0, 5), relic: picks[5], items: [['skill', picks[6]], ['gear', picks[7]]] } });
          R.save(UI.run);
          sfx('turn');
          // How to play is one tap away in the menu; it never pops up on its own.
          route();
        };
    };
    render();
  }

  // ------------------------------------------------------------ the road

  const STEP_INFO = {
    fight: { icon: 'swords', name: 'Battle' },
    event: { icon: 'event', name: 'Event' },
    shop: { icon: 'bag', name: 'Merchant' },
    boss: { icon: 'crown', name: 'Boss' },
    mega: { icon: 'skull', name: 'Final challenge' },
  };

  // The act's road as a strip of steps: done, here, and still to come.
  function roadHTML(run) {
    return `<div class="road">${run.plan
      .map((st, i) => `<span class="road-step ${i < run.step ? 'done' : i === run.step ? 'here' : ''}" title="${STEP_INFO[st.kind].name}">${ic(i < run.step ? 'check' : STEP_INFO[st.kind].icon)}</span>`)
      .join('<span class="road-link"></span>')}</div>`;
  }

  // A small picture of a challenge's battlefield: the ground, the enemy army and any loot.
  function drawThumb(cv, enc, palette) {
    const b = new AG.Render.Board(cv);
    b.resize(cv.clientWidth || 280, cv.clientHeight || 150);
    b.setBoard(enc.w, enc.h, enc.terrain, palette);
    b.setObjectives(enc.loot, enc.hold);
    b.syncFromState(E.createBattle(R.battleConfig(UI.run, [], enc)));
    b.frame();
  }

  // Each round: three battles to choose from, easy, medium and elite, each with a look at
  // the field, its goals and what it pays. The boss (and the final challenge) comes alone.
  // A defeat brings you back here, with the same three on offer.
  function challengeScreen() {
    const run = UI.run;
    UI.battle = null;
    UI.wr = null;
    const act = ACTS[run.act];
    const st = R.curStep(run);
    const offer = run.offer || [];
    const mega = st && st.kind === 'mega';
    const head = mega ? 'The final challenge' : st.kind === 'boss' ? 'The boss awaits' : 'Choose your next battle';
    const sub = mega
      ? 'The campaign is already won. This fight is not meant to be won: it is for a super victory.'
      : st.kind === 'boss'
        ? `Defeat ${esc(UNITS[R.bossOf(run)].name)} to ${run.act >= 3 ? 'win the campaign' : 'end the act'}.`
        : `Round ${st.round + 1} of ${R.FIGHTS}. Easy pays less, elite pays more and drops a relic (now and then an easy or medium one does too). What each pays is set now: losing or reloading never changes it. Lose, and you come back here to choose again.`;
    const card = (o, i) => {
      const rw = R.challengeReward(run, o);
      const pays = mega
        ? 'A super victory, and a place in legend.'
        : [`${ic('gold')} ~${rw.gold} gold`, `${ic('crown')} ${rw.xp} XP`, rw.spoils ? `pick 1 of ${rw.spoils} spoils` : '', rw.relic ? `${ic('gem')} ${rw.lucky ? 'a lucky relic: ' : 'relic: '}${RELICS[rw.relic] ? esc(RELICS[rw.relic].name) : 'yes'}` : '', rw.bossRelic ? `${ic('gem')} a boss relic` : '']
            .filter(Boolean)
            .join(' · ');
      return `<button class="card challenge tier-${o.tier}" data-ch="${i}" data-choose>
        <div class="ch-top"><span class="tier-chip tier-${o.tier}">${R.TIERS[o.tier].name}</span>${o.attempts ? `<span class="small muted">${o.attempts} ${o.attempts === 1 ? 'try' : 'tries'} so far</span>` : ''}</div>
        <canvas class="ch-thumb" data-thumb="${i}"></canvas>
        <div class="title">${esc(o.enc.name)}</div>
        <div class="ch-goals">${objectivesHTML(o.enc)}</div>
        <div class="ch-sup">${ic('army')} Enemy army <b>${R.encSupply(o.enc).army}</b> Supply${R.encSupply(o.enc).waves ? ` <span class="muted">(+${R.encSupply(o.enc).waves} in reinforcements)</span>` : ''} · yours <b>${R.supplyFor(run)}</b></div>
        <div class="ch-pay">${pays}</div>
      </button>`;
    };
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">${act.short} · ${esc(act.name)}</p><h2>${head}</h2></div>
        <div class="row">${resbar(run)}<span class="grow"></span>
          <button class="btn" id="chRelics">${ic('gem')} ${run.relics.length}</button>
          <button class="btn" id="chArmy">${ic('army')} Army</button>
          <button class="btn icon-only" id="chMenu" aria-label="Menu">${ic('menu')}</button></div>
        ${roadHTML(run)}
        <p class="muted">${sub}</p>
        <div class="cards challenges">${offer.map(card).join('')}</div>
        ${mega ? `<div class="row end"><button class="btn" id="chClaim">${ic('crown')} Claim your victory instead</button></div>` : ''}
      </div>`
    );
    for (const cv of $$('[data-thumb]', v)) drawThumb(cv, offer[+cv.dataset.thumb].enc, act.palette);
    // A tap that lands in the first moments (a second tap on the Continue that brought you
    // here) never picks a battle for you.
    const shownAt = performance.now();
    for (const b of $$('[data-ch]', v))
      b.onclick = () => {
        if (performance.now() - shownAt < 700) return;
        if (R.chooseChallenge(run, +b.dataset.ch)) {
          sfx('select');
          route();
        }
      };
    if ($('#chClaim', v)) $('#chClaim', v).onclick = () => claimSheet(run);
    $('#chArmy', v).onclick = () => armySheet(() => challengeScreen());
    $('#chMenu', v).onclick = () => menuSheet();
    $('#chRelics', v).onclick = () => relicSheet();
  }

  // Calling it a day at the final challenge: the campaign is won, and the Hall of Fame
  // already keeps the army that last fought the final challenge.
  function claimSheet(run) {
    R.claimVictory(run);
    route();
  }

  // The Act III boss is down: the campaign is won. Claim it, or take on the final challenge.
  function summitScreen() {
    const run = UI.run;
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">The Spire is silent</p><h2>Campaign won</h2></div>
        <p>${esc(UNITS[R.bossOf(run)].name)} is slain, and the arena bows to your warband. The victory is yours whatever you choose now.</p>
        <div class="panel summit">
          <p><b>Something stirs beyond the Spire: the Eclipse Wyrm,</b> with the Lich at its side and the Death Knight, its reaper, at the front. It is not meant to be beaten. Throw everything this army has at it for a super victory, as often as you like, or call it a day.</p>
          <div class="actions"><button class="btn" id="smClaim">${ic('crown')} Claim victory</button><button class="btn primary" id="smFace" data-choose>${ic('skull')} Face the Eclipse Wyrm</button></div>
        </div>
      </div>`
    );
    $('#smClaim', v).onclick = () => {
      R.endRun(run);
      route();
    };
    $('#smFace', v).onclick = () => {
      R.faceFinal(run);
      sfx('select');
      route();
    };
  }

  // In the War Room, the menu says where the battle came from, and lets you go back to the
  // other battles on offer (not for an event's battle, which has no others).
  function wrMenuLine(inBattle) {
    const p = UI.run && UI.run.pending;
    if (inBattle || !UI.wr || !p || p.type !== 'battle') return '';
    if (p.fromEvent) return `<div class="origin event">${battleOrigin(UI.run).html}</div>`;
    if (p.tier === 'boss') return '';
    return `<button class="btn wide" id="muOther">${ic('undo')} ${p.tier === 'mega' ? 'Back to the final choice' : 'Choose another battle'}</button>`;
  }

  function menuSheet(inBattle) {
    // A Hall of Fame match has no campaign to save or retreat from: just leave it.
    const ex = inBattle && UI.battle && UI.battle.exhibition;
    openSheet(
      `${sheetHead('Menu')}
      <div class="army-list">
        <button class="btn wide" id="muHelp">${ic('help')} How to play</button>
        <button class="btn wide" id="muCodex">${ic('book')} Codex</button>
        <button class="btn wide" id="muSound">${ic(AG.Audio.enabled ? 'sound' : 'mute')} Sound: ${AG.Audio.enabled ? 'on' : 'off'}</button>
        ${AG.Music ? `<button class="btn wide" id="muMusic">${ic(AG.Music.enabled ? 'sound' : 'mute')} Music: ${AG.Music.enabled ? 'on' : 'off'}</button>` : ''}
        ${inBattle && !ex ? (UI.battle && UI.battle.s.won ? `<button class="btn wide" id="muFinish">${ic('check')} Finish the battle (the win is yours)</button>` : `<button class="btn wide danger" id="muRetreat">${ic('flag')} Retreat and re-plan</button>`) : ''}
        ${ex ? `<button class="btn wide" id="muLeave">${ic('undo')} Leave the match (no result)</button>` : `<button class="btn wide" id="muTitle">Save and quit to title</button>`}
        ${wrMenuLine(inBattle)}
        ${!inBattle ? `<button class="btn wide danger" id="muAbandon">Abandon campaign</button>` : ''}
        ${!inBattle && R.loadHall().legends.concat(R.loadHall().queue).length ? `<button class="btn wide danger" id="muHallReset">${ic('crown')} Reset Hall of Fame</button>` : ''}
      </div>`,
      (sh) => {
        $('#muHelp', sh).onclick = () => helpSheet();
        if ($('#muOther', sh))
          $('#muOther', sh).onclick = () => {
            closeSheet();
            R.backToChoice(UI.run);
            if (UI.board) UI.board.stop();
            route();
          };
        $('#muCodex', sh).onclick = () => codexSheet();
        $('#muSound', sh).onclick = () => {
          AG.Audio.toggle();
          menuSheet(inBattle);
        };
        if ($('#muMusic', sh))
          $('#muMusic', sh).onclick = () => {
            AG.Music.toggle();
            menuSheet(inBattle);
          };
        if ($('#muLeave', sh))
          $('#muLeave', sh).onclick = () => {
            closeSheet();
            const back = ex.onLeave;
            UI.battle = null;
            back();
          };
        if ($('#muTitle', sh)) $('#muTitle', sh).onclick = () => {
          closeSheet();
          if (UI.board) UI.board.stop();
          UI.battle = null;
          UI.wr = null;
          title();
        };
        if ($('#muFinish', sh))
          $('#muFinish', sh).onclick = () => {
            closeSheet();
            finishCleanup();
          };
        if ($('#muRetreat', sh))
          $('#muRetreat', sh).onclick = async () => {
            closeSheet();
            if (!(await confirmSheet('Retreat?', 'The battle counts as lost. You go back to the war room to change your army and try again, as many times as you like.', 'Retreat', 'Keep fighting', true))) return;
            const B = UI.battle;
            if (!B) return;
            // Let the unit in motion finish first.
            B.paused = true;
            for (let i = 0; i < 100 && B.busy && UI.battle === B; i++) await sleep(50);
            if (UI.battle !== B || B.s.over) return;
            E.forfeit(B.s);
            E.drainEvents(B.s);
            battleOver();
          };
        if ($('#muHallReset', sh))
          $('#muHallReset', sh).onclick = async () => {
            closeSheet();
            if (!(await confirmSheet('Reset the Hall of Fame?', 'Every army in it goes, for good, the ones waiting to climb and the house armies too. Updates to the game never do this: only you can.', 'Reset', 'Keep them', true))) return;
            R.resetHall();
            toast('The Hall of Fame is empty.');
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
    const legend = r.tier === 'legendary';
    return `<button class="card${r.cursed ? ' cursed' : ''}${legend ? ' legendary' : ''}" ${attrs || ''}><div class="kind">${ic(legend ? 'crown' : 'gem')} ${legend ? 'Legendary relic' : 'Relic · ' + relicTier(r)}</div><div class="title">${esc(r.name)}</div><div class="desc">${esc(r.desc)}</div></button>`;
  }

  function relicSheet() {
    const run = UI.run;
    openSheet(
      `${sheetHead('Relics', 'Passive bonuses that last the whole campaign.')}
      <div class="army-list">${run.relics
        .map((id) => `<div class="card${RELICS[id].cursed ? ' cursed' : ''}${RELICS[id].tier === 'legendary' ? ' legendary' : ''}"><div class="kind">${ic('gem')} ${relicTier(RELICS[id])}</div><div class="title">${esc(RELICS[id].name)}</div><div class="desc">${esc(RELICS[id].desc)}</div></div>`)
        .join('')}</div>`
    );
  }

  // ------------------------------------------------------------ army and items

  function itemKindLabel(it) {
    return it.kind === 'skill' ? 'Skill' : it.kind === 'gear' ? 'Gear' : it.kind === 'talent' ? `${UNITS[TALENTS[it.id].cls].name} talent` : 'Enchantment scroll';
  }

  const ITEM_ICON = { skill: 'scroll', gear: 'sword', talent: 'star', scroll: 'gem' };

  const SLOT_KEY = { skill: 'skills', gear: 'gear', talent: 'talents' };

  // Owned items of a kind that unit r could put in a slot: free ones, and ones another unit
  // holds (equipping one moves it).
  function slotOptions(run, r, kind) {
    const held = r.load.talents.map((uid) => R.itemByUid(run, uid).id);
    const n = { free: 0, elsewhere: 0 };
    for (const it of run.items) {
      if (it.kind !== kind || (kind === 'talent' && TALENTS[it.id].cls !== r.type)) continue;
      if (!D.eligible(r.type, R.itemDef(it))) continue;
      const holder = R.itemHolder(run, it.uid);
      if (holder && holder.id === r.id) continue;
      if (kind === 'talent' && held.includes(it.id)) continue;
      if (holder) n.elsewhere++;
      else n.free++;
    }
    n.total = n.free + n.elsewhere;
    return n;
  }

  function kindPlural(kind, r) {
    return kind === 'talent' ? `${UNITS[r.type].name} talents` : kind === 'skill' ? 'skills' : kind === 'scroll' ? 'enchantment scrolls' : 'gear';
  }

  function slotOptionsText(kind, r, n) {
    if (!n.total) return `No ${kindPlural(kind, r)} you could equip yet`;
    const away = n.elsewhere === 1 ? '1 on another unit' : `${n.elsewhere} on other units`;
    return n.free && n.elsewhere ? `${n.free} free, ${away}` : n.free ? `${n.free} free` : away;
  }

  // How many of a reward's kind you already own, to weigh taking or buying it.
  function ownedNote(run, kind, id) {
    if (!run) return '';
    if (kind === 'recruit') {
      const same = run.roster.filter((u) => u.type === id).length;
      return `<div class="owned">${ic('army')}<span>${same ? `You have ${same} of these` : 'None of these yet'} · ${run.roster.length} unit${run.roster.length === 1 ? '' : 's'} in all</span></div>`;
    }
    const cls = kind === 'talent' ? TALENTS[id].cls : null;
    const mine = run.items.filter((i) => i.kind === kind && (!cls || TALENTS[i.id].cls === cls));
    const same = mine.filter((i) => i.id === id).length;
    const what = mine.length === 1 && kind !== 'gear' ? kindPlural(kind, { type: cls }).replace(/s$/, '') : kindPlural(kind, { type: cls });
    return `<div class="owned">${ic(ITEM_ICON[kind])}<span>${mine.length ? `You have ${mine.length} ${what}${same ? ` (${same} of this one)` : ''}` : `You have no ${what} yet`}</span></div>`;
  }

  // Where a talent goes: any talent slot of one class.
  function talentWhere(t) {
    return `Only for the ${UNITS[t.cls].name}. It fits any of its talent slots: one at Level 1, two at Level 2, three at Level 3.`;
  }

  function itemCost(it) {
    const d = R.itemDef(it);
    return it.kind === 'scroll' ? `+${d.surcharge} Supply on its unit` : costTag(d);
  }

  // What an item costs to field: free ones still take a slot, and a side-grade is a trade
  // (Auto leaves those to you).
  function costTag(d) {
    return d.cost ? `${d.cost} Supply` : d.side ? 'Free · side-grade' : 'Free (0 Supply)';
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
            <div class="chips" style="justify-content:flex-end">${r.core ? '<span class="chip good" title="Fights in every battle, free of Supply">Always fights</span>' : ''}${r.enchant ? `<span class="chip magic">${ic('gem')} ${esc(ENCHANTS[r.enchant].name)}</span>` : ''}${deployed && !r.core ? '<span class="chip good">Deployed</span>' : ''}
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
              <div class="itemico ${kind}">${ic(ITEM_ICON[kind])}</div>
              <div class="nm" style="min-width:0"><b>${esc(d.name)}</b><div class="small muted">${esc(d.desc)}</div></div>
              <div class="chips" style="justify-content:flex-end"><span class="chip warn">${esc(itemCost(it))}</span>${holder ? `<span class="chip good">${esc(holder.name)}</span>` : kind === 'scroll' ? '<span class="chip magic">Bind</span>' : '<span class="chip">Free</span>'}</div></button>`;
          })
          .join('')}</div>`;
      };
      body =
        group('talent', 'Talents') + group('skill', 'Skills') + group('gear', 'Gear') + group('scroll', 'Enchantment scrolls') ||
        '<p class="muted">No talents, skills, gear or scrolls yet. Win battles, visit merchants and explore events to find them.</p>';
    } else {
      body = `<div class="army-list">${run.relics
        .map((id) => `<div class="card${RELICS[id].cursed ? ' cursed' : ''}${RELICS[id].tier === 'legendary' ? ' legendary' : ''}"><div class="kind">${ic('gem')} ${relicTier(RELICS[id])}</div><div class="title">${esc(RELICS[id].name)}</div><div class="desc">${esc(RELICS[id].desc)}</div></div>`)
        .join('')}</div>`;
    }
    openSheet(
      `${sheetHead('Your army', `${run.roster.length} unit${run.roster.length === 1 ? '' : 's'} · ${ic('gold')} ${run.gold} gold · Commander Lv ${R.commanderLevel(run)}`)}
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
      `${sheetHead(esc(d.name), `${itemKindLabel(it)} · ${esc(itemCost(it))}`, true)}
      <p>${esc(d.desc)}</p>
      ${it.kind === 'talent' ? `<p class="small muted">${esc(talentWhere(d))}</p>` : ''}
      ${d.req ? `<p class="small muted">Only for units that ${{ damage: 'deal damage', phys: 'deal physical damage', magic: 'use magic', ranged: 'attack at range', mobile: 'can move', facing: 'have a facing', slow: 'have a cooldown of 2 or more', recovers: 'have a cooldown' }[d.req] || 'qualify'}.</p>` : ''}
      ${it.kind === 'scroll'
        ? `<p class="hint warn">Binding is permanent: the enchantment stays with that unit for the rest of the campaign and adds ${d.surcharge} Supply to its cost. A unit can hold only one enchantment.</p>`
        : `<p class="small muted">${holder ? `Slotted into ${esc(holder.name)}.` : 'Not slotted into anyone. Equip it from a unit\'s loadout.'}</p>`}
      <div class="actions">
        ${it.kind === 'scroll' ? `<button class="btn primary" id="isBind">${ic('gem')} Bind to a unit</button>` : ''}
        ${it.kind === 'talent' && !holder ? `<button class="btn primary" id="isEquip">${ic('star')} Give to a unit</button>` : ''}
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
        if ($('#isEquip', sh))
          $('#isEquip', sh).onclick = async () => {
            UI.onSheetClose = null;
            const rid = await pickUnit('Give ' + d.name, talentWhere(d), (u) => u.type === d.cls);
            if (rid) {
              const r = R.unitById(run, rid);
              if (R.assignItem(run, rid, uid)) {
                R.save(run);
                if (UI.wr) renderWarRoom();
                toast(`${r.name} now has ${d.name}.`);
              } else toast(`${r.name} has no free talent slot, or already has ${d.name}. Level it up or empty a slot in its loadout.`);
            }
            UI.onSheetClose = after;
            itemSheet(uid, back);
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
      <span class="pk-head"><b>${esc(ab.name)}${on ? ` <span class="got-tag">✓ ${locked ? 'Picked' : 'Chosen'}</span>` : ''}</b><span class="cost">${ab.cost ? '+' + ab.cost : 'free'}</span></span>
      <span class="pk-body">${shape ? patternSVG(shape, 'P') : ''}<span class="pk-desc">${esc(ab.desc)}</span></span></button>`;
  }

  // A loadout section listing every talent, skill or piece of gear you own that fits this
  // unit: equipped first (gold), then free ones (one row per kind, with how many copies),
  // then ones another unit holds (a tap moves it here). Up to the slots its level gives.
  function kitSection(run, r, kind) {
    const key = SLOT_KEY[kind];
    const n = R.slotsFor(r.load.lv)[key];
    const most = (kind === 'talent' ? TALENT_SLOTS : kind === 'skill' ? SKILL_SLOTS : GEAR_SLOTS)[3];
    const held = r.load[key];
    const heldIds = held.map((uid) => R.itemByUid(run, uid).id);
    const fits = (it) => D.eligible(r.type, R.itemDef(it)) && (kind !== 'talent' || TALENTS[it.id].cls === r.type);
    const rowHTML = (it, state, extra) => {
      const d = R.itemDef(it);
      const on = state === 'on';
      const tag = (d.rarity === 'legendary' ? `<span class="legend-tag">${ic('crown')} Legendary</span>` : '') + (on ? '<span class="got-tag">✓ Equipped</span>' : extra || '');
      return `<button class="slot kit ${on ? 'full' : ''} ${!on && held.length >= n ? 'capped' : ''}" data-kit="${on ? 'off' : 'on'}:${kind}:${it.uid}">
        <span class="itemico ${kind}">${ic(ITEM_ICON[kind])}</span>
        <span class="sl-body"><span class="sl-name"><b>${esc(d.name)}</b>${tag}</span><span class="small muted">${esc(d.desc)}</span>${on ? '<span class="small sl-hint">Tap to take it off.</span>' : ''}</span>
        <span class="cost">+${d.cost}</span></button>`;
    };
    const rows = held.map((uid) => rowHTML(R.itemByUid(run, uid), 'on'));
    const listed = new Set(kind === 'talent' ? heldIds : []);
    const free = R.freeItems(run, kind).filter(fits);
    for (const it of free) {
      if (listed.has(it.id)) continue;
      listed.add(it.id);
      const copies = free.filter((x) => x.id === it.id).length;
      rows.push(rowHTML(it, 'free', copies > 1 ? `<span class="chip">×${copies}</span>` : ''));
    }
    for (const it of run.items) {
      if (it.kind !== kind || listed.has(it.id) || !fits(it)) continue;
      const holder = R.itemHolder(run, it.uid);
      if (!holder || holder.id === r.id) continue;
      listed.add(it.id);
      rows.push(rowHTML(it, 'elsewhere', `<span class="chip">on ${esc(holder.name)}</span>`));
    }
    const title = kind === 'talent' ? `${ic('star')} ${UNITS[r.type].name} talents` : kind === 'skill' ? 'Skills' : 'Gear';
    const more = n < most ? ` · ${kind === 'gear' ? 'Level 3 adds a second slot' : kind === 'skill' ? 'Level 2 adds a second slot' : `Level ${r.load.lv + 1} adds a slot`}` : '';
    const none = kind === 'talent' ? `You own no ${esc(UNITS[r.type].name)} talents yet. Every new unit brings one, and you find more in shops and battle spoils.` : `You own no ${kind === 'skill' ? 'skills' : 'gear'} this unit can use yet. Find them in battle spoils, shops and events.`;
    return `<div class="lo-sec"><div class="eyebrow">${title} · ${held.length} of ${n} slot${n > 1 ? 's' : ''} used</div>
      <p class="small muted">Everything you own that fits it. Tap to equip, up to ${n} at Level ${r.load.lv}${more}.</p>
      <div class="slots">${rows.length ? rows.join('') : `<p class="small muted">${none}</p>`}</div></div>`;
  }

  function slotButton(run, r, kind, i) {
    const uid = r.load[SLOT_KEY[kind]][i];
    const it = uid && R.itemByUid(run, uid);
    const d = it && R.itemDef(it);
    // Equipped: gold, tagged, and already working; a tap only swaps or removes it.
    if (d)
      return `<button class="slot full" data-slot="${kind}:${i}">
      <span class="itemico ${kind}">${ic(ITEM_ICON[kind])}</span>
      <span class="sl-body"><span class="sl-name"><b>${esc(d.name)}</b><span class="got-tag">✓ Equipped</span></span><span class="small muted">${esc(d.desc)}</span><span class="small sl-hint">Working already. Tap to swap or remove it.</span></span>
      <span class="cost">+${d.cost}</span></button>`;
    const n = slotOptions(run, r, kind);
    return `<button class="slot ${n.total ? '' : 'none'}" data-slot="${kind}:${i}" ${n.total ? '' : 'disabled'}>
      <span class="itemico ${kind}">${ic(ITEM_ICON[kind])}</span>
      <span class="sl-body"><b class="muted">Empty ${kind} slot</b><span class="small muted">${slotOptionsText(kind, r, n)}${n.total ? ' · tap to equip' : ''}</span></span>
      ${n.total ? `<span class="avail" title="${n.total} you could equip here">${n.total}</span>` : ''}</button>`;
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
    // Only a unit on the field can be kitted out; on the bench it is the bare unit.
    const editable = !!(wr && wr.dep.has(rid));
    const after = UI.onSheetClose;
    let budget = '';
    if (wr) {
      const used = wrUsed();
      const deployed = wr.dep.has(rid);
      const total = deployed ? used : used + cost;
      budget = budgetBar(total, wr.supply, deployed ? 'Army' : 'Army with this unit');
    }
    const lvBtn = (lv) => `<button class="btn ${L.lv === lv ? 'on' : ''}" data-lv="${lv}"><b>Lv ${lv}</b><span>${lv === 1 ? 'base' : '+' + LEVEL_COST[lv]}</span></button>`;
    // The level picks: the free option and the actives. Talents have their own slots.
    const picks = (tier) => T.abilities[tier].filter((id) => !TALENTS[id]);
    const pickHead = (tier) => (picks(tier).length > 1 ? ` · pick 1 of ${picks(tier).length}` : '');
    const scrolls = run.items.filter((i) => i.kind === 'scroll' && D.eligible(r.type, ENCHANTS[i.id]));
    // What you change most comes first: the cost, the level, the slots, the picks. The
    // unit's numbers and attacks follow.
    const html = `${sheetHead(esc(r.name), `${esc(T.name)} · fielding costs <b class="cost-big">${cost}</b> Supply`, true)}
      ${budget}
      ${editable ? '' : `<p class="hint">${ic('help')} Not on the field: units on the bench carry nothing. Place it on the board in the War Room to give it levels, talents, skills and gear.</p>`}
      <div class="costline">${R.costBreakdown(run, r)
        .filter((x) => x.cost)
        .map((x) => `<span class="cb">${esc(costLabel(x.label))} <b>${x.cost}</b></span>`)
        .join('<span class="cb-op">+</span>')}<span class="cb-op">=</span><span class="cb"><b>${cost}</b></span></div>
      ${unitInfoHTML(u, { name: r.name })}
      <div class="lo-sec"><div class="eyebrow">Level</div>
        <div class="lv-seg">${lvBtn(1)}${lvBtn(2)}${lvBtn(3)}</div>
        <p class="small muted">Level 2: +20% HP, +15% damage, a second ability, a second talent slot and a second skill slot. Level 3: +40% HP, +30% damage, its Mastery, a third talent slot and a second gear slot.</p></div>
      ${kitSection(run, r, 'talent')}
      ${kitSection(run, r, 'skill')}
      ${kitSection(run, r, 'gear')}
      <div class="lo-sec"><div class="eyebrow">Ability${pickHead(1)}</div>
        <div class="picks">${picks(1).map((id) => abilityCard(r, 1, id, false)).join('')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Level 2 ability${pickHead(2)}${L.lv < 2 ? ' <span class="lockline">unlocks at Level 2</span>' : ''}</div>
        <div class="picks">${picks(2).map((id) => abilityCard(r, 2, id, L.lv < 2)).join('')}</div></div>
      <div class="lo-sec"><div class="eyebrow">Mastery${L.lv < 3 ? ' <span class="lockline">unlocks at Level 3</span>' : ''}</div>
        <div class="pick static ${L.lv < 3 ? 'locked' : 'on'}"><span class="pk-head"><b>${esc(MASTERY[r.type].name)}</b></span><span class="pk-desc">${esc(MASTERY[r.type].desc)}</span></div></div>
      <div class="lo-sec"><div class="eyebrow">Enchantment</div>
        ${r.enchant
          ? `<div class="pick static on ench"><span class="pk-head"><b>${ic('gem')} ${esc(ENCHANTS[r.enchant].name)}</b><span class="cost">+${ENCHANTS[r.enchant].surcharge}</span></span><span class="pk-desc">${esc(ENCHANTS[r.enchant].desc)} Bound for good.</span></div>`
          : `<p class="small muted">None. ${scrolls.length ? `You have ${scrolls.length} scroll${scrolls.length > 1 ? 's' : ''} that could be bound to this unit.` : 'Enchantment scrolls bind a permanent bonus to one unit.'}</p>
            ${scrolls.length ? `<button class="btn" id="loBind">${ic('gem')} Bind a scroll…</button>` : ''}`}</div>
      <div class="lo-sec"><div class="eyebrow">Stats</div>${statsHTML(u)}</div>
      <div class="lo-sec"><div class="eyebrow">In battle</div>${actsHTML(u)}
        ${traitLines(u).length ? `<ul class="tips">${traitLines(u).map((t) => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}</div>
      <p class="small muted">Battles: ${r.battles} · Enemies slain: ${r.kills}</p>
      <div class="actions">
        ${editable ? loadoutFieldButtons(rid) : ''}
        <button class="btn primary" id="loDone">${ic('check')} Done</button>
      </div>`;
    const left = () => wr.supply - wrUsed();
    // After a change: the sheet redrawn, and a bubble over the button tapped (`b`, with the
    // Supply left before the change) saying what it cost and what is left.
    const changed = (b, was) => {
      const rect = b && b.getBoundingClientRect();
      R.save(run);
      if (UI.wr) renderWarRoom();
      sfx('click');
      loadoutSheet(rid, back);
      if (rect && wr) supplyPop(rect, was, left());
    };
    refreshSheet(html, (sh) => {
      if (!editable) for (const b of $$('[data-lv], [data-ab], [data-slot], [data-kit]', sh)) b.disabled = true;
      for (const b of $$('[data-lv]', sh))
        b.onclick = () => {
          const was = left();
          R.setLevel(run, rid, +b.dataset.lv);
          changed(b, was);
        };
      for (const b of $$('[data-ab]', sh))
        b.onclick = () => {
          const [tier, id] = b.dataset.ab.split(':');
          if (+tier === 2 && L.lv < 2) toast('This pick applies once the unit is Level 2.');
          const was = left();
          R.setAbility(run, rid, +tier, id);
          changed(b, was);
        };
      // Back from a picker, the sheet returns to where you were.
      const here = () => {
        const top = sh.scrollTop;
        return () => {
          loadoutSheet(rid, back);
          $('#sheet').scrollTop = top;
        };
      };
      for (const b of $$('[data-slot]', sh))
        b.onclick = () => {
          const [kind, i] = b.dataset.slot.split(':');
          itemPicker(rid, kind, +i, here());
        };
      // Everything you own that fits, listed in place: a tap equips or unequips it.
      for (const b of $$('[data-kit]', sh))
        b.onclick = () => {
          const [op, kind, uid] = b.dataset.kit.split(':');
          const was = left();
          if (op === 'off') R.unassignItem(run, uid);
          else {
            const n = R.slotsFor(L.lv)[SLOT_KEY[kind]];
            if (L[SLOT_KEY[kind]].length >= n) {
              toast(`${n > 1 ? `All ${n} ${kind} slots are` : `Its one ${kind} slot is`} in use at Level ${L.lv}. Tap the equipped one${n > 1 ? 's' : ''} to take ${n > 1 ? 'one' : 'it'} off first, or raise its level for more slots.`, 3600);
              return;
            }
            if (!R.assignItem(run, rid, uid)) return toast('That does not fit this unit.');
          }
          changed(b, was);
        };
      if ($('#loBind', sh))
        $('#loBind', sh).onclick = async () => {
          const pick = scrolls.length === 1 ? scrolls[0] : null;
          const ret = here();
          if (pick) return bindFlow(pick.uid, rid, ret);
          openSheet(
            `${sheetHead('Choose a scroll', null, true)}<div class="army-list">${scrolls
              .map((s) => `<button class="army-row" data-sc="${s.uid}"><div class="itemico scroll">${ic('gem')}</div><div class="nm"><b>${esc(ENCHANTS[s.id].name)}</b><div class="small muted">${esc(ENCHANTS[s.id].desc)}</div></div><span class="chip warn">+${ENCHANTS[s.id].surcharge}</span></button>`)
              .join('')}</div><div class="actions"><button class="btn" id="scBack">Back</button></div>`,
            (s2) => {
              for (const b of $$('[data-sc]', s2)) b.onclick = () => bindFlow(b.dataset.sc, rid, ret);
              $('#scBack', s2).onclick = ret;
            }
          );
        };
      $('#loDone', sh).onclick = () => (back ? back() : closeSheet());
      if ($('#loFocus', sh))
        $('#loFocus', sh).onclick = () => {
          const ft = wrFocusTarget(UI.wr.s);
          const mine = ft && ft.ally && ft.ally.rid === rid;
          run.pending.focus = mine ? null : { kind: 'ally', rid, label: r.name };
          toast(mine ? 'Priority cleared. Your army fights on normal orders.' : `Priority: ${r.name}. From the first turn, your army ${focusVerb(run.pending.focus)}.`, 3200);
          changed();
        };
      if ($('#loRemove', sh))
        $('#loRemove', sh).onclick = () => {
          if (wrBench(rid) && back) back();
        };
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
    const cur = r.load[SLOT_KEY[kind]][idx];
    // Talents only list this class's; another class's would never fit.
    const list = run.items.filter((i) => i.kind === kind && (kind !== 'talent' || TALENTS[i.id].cls === r.type));
    const heldIds = r.load.talents.filter((x) => x !== cur).map((x) => R.itemByUid(run, x).id);
    const rows = list
      .map((it) => {
        const d = R.itemDef(it);
        const ok = D.eligible(r.type, d) && !(kind === 'talent' && heldIds.includes(it.id));
        const holder = R.itemHolder(run, it.uid);
        const mine = holder && holder.id === rid;
        return `<button class="army-row item-row" data-pick="${it.uid}" ${ok && !mine ? '' : 'disabled style="opacity:.45"'}>
          <div class="itemico ${kind}">${ic(ITEM_ICON[kind])}</div>
          <div class="nm" style="min-width:0"><b>${esc(d.name)}</b><div class="small muted">${esc(d.desc)}</div></div>
          <div class="chips" style="justify-content:flex-end"><span class="chip warn">+${d.cost}</span>${mine ? '<span class="chip good">Equipped</span>' : holder ? `<span class="chip">on ${esc(holder.name)}</span>` : ''}${!ok ? '<span class="chip bad">Not usable</span>' : ''}</div></button>`;
      })
      .join('');
    openSheet(
      `${sheetHead(`Equip ${kind}`, `${esc(r.name)} the ${esc(UNITS[r.type].name)}. Taking an item from another unit moves it here.`, true)}
      ${list.length ? `<div class="army-list">${rows}</div>` : `<p class="muted">${kind === 'talent' ? `You own no ${esc(UNITS[r.type].name)} talents yet. Find them in battle spoils and shops.` : `You own no ${kind === 'skill' ? 'skills' : 'gear'} yet. Find them in battle spoils, shops and events.`}</p>`}
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
    // Everything it carries, spelled out: abilities, mastery, talents, skills, gear and
    // enchantment, each with what it does.
    const picks = [];
    if (u.a1 && ABILITIES[u.a1]) picks.push(['Ability', ABILITIES[u.a1]]);
    if (u.a2 && u.level >= 2 && ABILITIES[u.a2]) picks.push(['Level 2 ability', ABILITIES[u.a2]]);
    if (u.level >= 3 && MASTERY[u.type]) picks.push(['Mastery', MASTERY[u.type]]);
    for (const id of u.talents || []) if (TALENTS[id]) picks.push(['Talent', TALENTS[id]]);
    for (const id of u.skills || []) if (SKILLS[id]) picks.push(['Skill', SKILLS[id]]);
    for (const id of u.gear || []) if (GEAR[id]) picks.push(['Gear', GEAR[id]]);
    if (u.enchant && ENCHANTS[u.enchant]) picks.push(['Enchantment', ENCHANTS[u.enchant]]);
    const traits = traitLines(u, (UI.battle && UI.battle.s) || (UI.wr && UI.wr.s))
      .map((t) => `<li>${esc(t)}</li>`)
      .join('');
    openSheet(
      `${sheetHead(esc(u.name), `${sideLabel(u.team)} ${T.name} · Level ${u.level}`, true)}
      ${unitInfoHTML(u, { status: !!live })}
      ${statsHTML(u)}
      ${actsHTML(u)}
      ${picks.length ? `<div class="eyebrow">Loadout</div><div class="picks">${picks.map(([kind, p]) => `<div class="pick static on"><span class="pk-head"><b>${esc(p.name)}</b><span class="small muted">${kind}</span></span><span class="pk-desc">${esc(p.desc)}</span></div>`).join('')}</div>` : ''}
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
        'Stops straight-line attacks such as a Witch\'s lightning; arcing shots and spells fly over it.',
        `It cannot be destroyed. A unit shoved or dragged into it slams into it for ${E.IMPACT.rock} damage.`,
        'Make it the priority and your army gathers around it and holds there.'
      );
    } else if (t === E.T_WATER || t === E.T_LAVA) {
      const water = t === E.T_WATER;
      name(water ? 'Deep Water' : 'Lava', null, water ? 'water' : 'lava');
      f.lines.push(
        `${water ? 'Too deep' : 'Too hot'} to walk through. Flying units cross it, but nobody can stop on it.`,
        water
          ? `Attacks pass over it. A unit on foot shoved or dragged into it splashes in for ${E.IMPACT.water} damage, climbs out onto the nearest dry tile and is rooted for 1 turn (the water puts out burns).`
          : `Attacks pass over it. A unit on foot shoved or dragged into it falls in for ${E.IMPACT.lava} damage, climbs out onto the nearest dry tile and burns.`
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
      f.lines.push(`Start ${h.need} of your turns in a row with one of your units standing on it to complete the mission.${h.count ? ` Held for ${h.count} so far.` : ''}`);
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
    // Plain empty ground: nothing to say but that it can be a spot to gather at.
    if (!f.lines.length && t === E.T_GRASS && !E.at(s, x, y)) {
      name('Open ground', 'target');
      f.open = true;
      f.lines.push('Nothing here. Make it the priority and your army gathers here: a corner to huddle in, a choke point, a flank.');
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

  // Everyone under the finger, front to back: the sprites, then whoever stands on the tile.
  function unitsUnderFinger(hit, s) {
    const out = (hit.stack || []).map((st) => s.byId[st.uid]).filter((v) => v && v.alive);
    const ground = hit.tile ? E.at(s, hit.tile.x, hit.tile.y) : null;
    if (ground && ground.alive && !out.includes(ground)) out.push(ground);
    return out;
  }

  // The unit a tap picks: the one in front, or, tapping the same spot again, the one behind
  // it (a barricade hidden by a Lightning Ward, say). Call once per tap.
  function pickAt(hit, s) {
    const front = unitInFront(hit, s);
    if (!front) return (UI.lastPick = null);
    const list = unitsUnderFinger(hit, s);
    if (!list.includes(front)) list.unshift(front);
    const last = UI.lastPick;
    let pick = front;
    if (last && list.length > 1 && Math.hypot(hit.px - last.px, hit.py - last.py) < 30 && Date.now() - last.t < 6000) {
      const i = list.findIndex((v) => v.uid === last.uid);
      if (i >= 0) pick = list[(i + 1) % list.length];
    }
    const next = list.length > 1 ? list[(list.indexOf(pick) + 1) % list.length] : null;
    UI.lastPick = { px: hit.px, py: hit.py, uid: pick.uid, t: Date.now(), behind: next ? next.uid : null };
    return pick;
  }

  // "Tap again for the Barricade behind it.", when the unit just tapped hides another.
  function behindHint(s, uid) {
    const lp = UI.lastPick;
    if (!lp || lp.uid !== uid || !lp.behind || Date.now() - lp.t > 6000) return '';
    const b = s.byId[lp.behind];
    if (!b || !b.alive) return '';
    return `<p class="small muted">${ic('eye')} Something behind: tap the same spot again for ${esc(b.team === 'P' ? b.name : 'the ' + UNITS[b.type].name)}.</p>`;
  }

  // ------------------------------------------------------------ objectives

  function objectivesHTML(enc, s) {
    if (enc.exhibition)
      return `<div class="objectives"><div class="obj primary">${ic('crown')}<span><b>Hall of Fame match.</b> <b style="color:var(--blue)">${esc(enc.exhibition.a)}</b> (blue, from the south) against <b style="color:var(--red)">${esc(enc.exhibition.b)}</b> (red). The last army standing wins.</span></div><div class="obj"><span class="ban-badge inline">${ic('close')}</span><span><b>No priority.</b> Both armies fight on their own, so the result is theirs alone.</span></div></div>`;
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
    // A mission done is the win: both sides' fatigue timers switch on, and the battle goes on
    // while your army grabs what else it can.
    if (s && s.routed) status = ` <span class="reward">${ic('check')} Done: the win is yours! Both sides tire now (enemy −${E.fatigueHit(s, 'E')}, yours −${E.fatigueHit(s, 'P')}, one more each unit turn). Grab what else you can, or Finish now.</span>`;
    else if (info.key !== 'rout') status += ` <span class="small muted">Do it and the win is yours: both sides start to tire.</span>`;
    const lines = [`<div class="obj primary ${s && s.routed ? 'done' : ''}">${ic('flag')}<span><b>${esc(info.short)}.</b> ${esc(info.primary)}${status}</span></div>`];
    const wl = wavesLine(enc, s);
    if (wl) lines.push(wl);
    for (const o of info.bonus) {
      const state = s ? bonusState(s, o.b) : '';
      lines.push(`<div class="obj bonus ${state}">${ic(state === 'done' ? 'check' : 'star')}<span>${esc(o.text)} <span class="reward">Reward: ${esc(o.reward)}.</span></span></div>`);
    }
    return `<div class="objectives">${lines.join('')}</div>`;
  }

  // Mid-battle: a bonus goal already met ('done'), out of reach ('failed'), or still open ('').
  function bonusState(s, b) {
    if (b.type === 'loot' && s.loot.some((l) => l.id === b.lootId && l.taken)) return 'done';
    if (b.type === 'swift' && (s.won ? s.won.turn : s.turn) > b.turns) return 'failed';
    if (b.type === 'flawless' && (s.won ? s.won.lost > 0 : s.units.some((u) => u.team === 'P' && !u.nonCombat && !u.alive))) return 'failed';
    // Once the win is yours, speed and losses are settled.
    if (s.won && (b.type === 'swift' || b.type === 'flawless')) return 'done';
    if (b.type === 'muster') return s.units.some((u) => u.rid === b.rid) ? 'done' : 'failed';
    if (b.type === 'plunder' && s.units.some((u) => u.type === 'cart' && u.escaped)) return 'failed';
    if (b.type === 'blockade' && s.stats.blocked >= b.n) return 'done';
    if (b.type === 'ambush' && (s.stats.waveKills || 0) >= b.n) return 'done';
    return '';
  }

  // The battle's goals in a few short lines, pinned to the top of the battle panel so they
  // stay in view whatever the panel shows below and however far it scrolls.
  function goalBarHTML(B) {
    const s = B.s;
    const enc = B.enc;
    if (B.exhibition) return `<div class="goalbar"><div class="gl primary">${ic('crown')}<span><b>Hall of Fame match.</b> Last army standing wins.</span></div></div>`;
    const info = R.objectiveInfo(UI.run, enc);
    const tag = (t, cls) => ` <span class="${cls || 'gl-tag'}">${t}</span>`;
    let status = '';
    if (s.cleanup) status = tag(`${ic('check')} Won. Cleanup: ${E.cleanupLeft(s)} left · your fatigue −${E.fatigueHit(s, 'P')}`, 'gl-tag done');
    else if (s.routed) status = tag(`${ic('check')} Won. Fatigue: enemy −${E.fatigueHit(s, 'E')} · yours −${E.fatigueHit(s, 'P')}`, 'gl-tag done');
    else if (s.hold) status = tag(`${s.hold.count}/${s.hold.need}`);
    else if (s.surviveTurns) status = tag(`${Math.max(0, s.surviveTurns - s.turn + 1)} to go`);
    else if (enc.layout === 'convoy') {
      const carts = s.units.filter((u) => u.type === 'cart');
      status = tag(`${carts.filter((u) => !u.alive && !u.escaped).length}/${carts.length} broken${carts.some((u) => u.escaped) ? ` · ${carts.filter((u) => u.escaped).length} escaped` : ''}`);
    } else if (info.key === 'totems' || info.key === 'raze') {
      const goals = s.units.filter((u) => u.team === 'E' && u.goal);
      status = tag(`${goals.filter((u) => !u.alive).length}/${goals.length} down`);
    } else {
      const vip = (info.key === 'boss' || info.key === 'commander') && s.units.find((u) => u.team === 'E' && u.vip && u.alive);
      if (vip) status = tag(`${esc(UNITS[vip.type].name)} ${vip.hp}/${vip.maxHp} HP`);
      else status = tag(`${s.units.filter((u) => u.alive && u.team === 'E' && E.counts(u)).length} enemies left`);
    }
    const lines = [`<div class="gl primary ${s.routed || s.cleanup ? 'done' : ''}">${ic('flag')}<span><b>${esc(info.short)}</b>${status}</span></div>`];
    // Gold waiting in the field: wreckage and barricades, broken for their pouches.
    const pouches = s.units.filter((u) => u.team === 'E' && u.bounty > 0 && u.structure);
    if (pouches.length) {
      const left = pouches.filter((u) => u.alive);
      const name = pouches.every((u) => u.type === 'wreckage') ? 'Wreckage' : pouches.every((u) => u.type === 'barricade') ? 'Barricades' : 'Gold';
      lines.push(`<div class="gl gold ${left.length ? '' : 'done'}">${ic('gold')}<span>${name}: ${pouches.length - left.length}/${pouches.length} broken${tag(left.length ? `${left.reduce((t, u) => t + u.bounty, 0)} gold left` : 'all taken', 'reward')}</span></div>`);
    }
    for (const o of info.bonus) {
      const state = bonusState(s, o.b);
      const prog = o.b.type === 'ambush' && state !== 'done' ? ` (${s.stats.waveKills || 0}/${o.b.n})` : o.b.type === 'swift' && !state && !s.won ? ` (turn ${s.turn})` : '';
      lines.push(`<div class="gl bonus ${state}">${ic(state === 'done' ? 'check' : state === 'failed' ? 'close' : 'star')}<span>${esc(o.short || o.text)}${prog}${state === 'failed' ? '' : tag(esc(o.reward), 'reward')}</span></div>`);
    }
    const waves = E.waveSummary(s).filter((w) => w.team === 'E');
    if (waves.length) {
      const next = Math.min(...waves.map((w) => w.turn));
      const n = waves.filter((w) => w.turn === next).reduce((t, w) => t + w.types.length, 0);
      lines.push(`<div class="gl waves">${ic('hourglass')}<span>Reinforcements: ${n} on turn ${next}${waves.length > 1 ? `, ${waves.reduce((t, w) => t + w.types.length, 0) - n} more later` : ''}</span></div>`);
    }
    return `<div class="goalbar" aria-label="Battle goals">${lines.join('')}</div>`;
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

  // Where the battle in the War Room came from, so none seems to come out of nowhere: the
  // challenge you picked this round (and that Other battles takes you back to the choice),
  // the act's boss, or an event (which cannot be swapped for another).
  function battleOrigin(run) {
    const p = run.pending;
    if (!p || p.type !== 'battle') return { short: '', html: '' };
    if (p.fromEvent) {
      const ev = p.eventTitle || 'an event';
      return { short: 'Event battle', html: `${ic('book')}<span><b>Event battle</b>, from ${p.eventTitle ? `<b>${esc(ev)}</b>` : 'an event'}: your choice there led here. It cannot be swapped for another battle: win it, or retreat and re-plan as often as you like.</span>` };
    }
    const st = R.curStep(run);
    if (p.tier === 'mega') return { short: 'Final challenge', html: `${ic('skull')}<span><b>The final challenge</b>, which you chose to face. Back takes you to the choice to call it a day.</span>` };
    if (p.tier === 'boss') return { short: 'Boss battle', html: `${ic('crown')}<span><b>The act's boss</b>: the one battle this round, no choice to make.</span>` };
    const round = st && st.kind === 'fight' ? `Round ${st.round + 1} of ${R.FIGHTS}` : 'This round';
    return { short: `${R.TIERS[p.tier] ? R.TIERS[p.tier].name : ''} battle`, html: `${ic('flag')}<span><b>${round}: you picked the ${R.TIERS[p.tier] ? R.TIERS[p.tier].name.toLowerCase() : ''} battle.</b> Other battles (below, or in the menu) takes you back to the three on offer.</span>` };
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
    music('camp');
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
    // Your plan for this battle, or the army of your last one; a quest's unit joins it. That
    // unit always fights: it cannot leave the field.
    const dep = new Map(R.startingPlan(run, enc).map((d) => [d.rid, { x: d.x, y: d.y, facing: d.facing }]));
    const star = R.bonusUnit(run, enc);
    // Units on the bench are bare: their kit goes back to the pack until they take the field.
    for (const r of run.roster) if (!dep.has(r.id)) R.stripLoad(run, r);
    R.save(run);
    const core = R.coreUnit(run);
    UI.wr = { supply: R.supplyFor(run), dep, sel: null, tab: 'army', inspect: null, rows, enc, auto: 0, star: star ? star.id : null, core: core ? core.id : null };
    UI.boardTap = wrTap;
    UI.boardLong = wrLong;
    UI.boardDragMove = wrDragMove;
    UI.boardDragEnd = wrDragEnd;
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
    return wr.rows.includes(y) && R.deployOpen(wr.enc, x, y);
  }

  function wrRidAt(x, y) {
    for (const [rid, d] of UI.wr.dep) if (d.x === x && d.y === y) return rid;
    return null;
  }

  function isAttacker(type) {
    const T = UNITS[type];
    return !!(T.act.dmg || (T.act.fx && T.act.fx.poison));
  }

  // A tap and a press-and-hold on the same element: `tap` on a quick tap, `hold` once held
  // still for about half a second (or on a right click); the tap that ends a hold is
  // swallowed.
  function tapHold(el, tap, hold) {
    let timer = 0;
    let held = false;
    let from = null;
    const cancel = () => clearTimeout(timer);
    el.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      held = false;
      from = [e.clientX, e.clientY];
      cancel();
      timer = setTimeout(() => {
        held = true;
        hold();
      }, 450);
    });
    el.addEventListener('pointermove', (e) => from && Math.hypot(e.clientX - from[0], e.clientY - from[1]) > 10 && cancel());
    for (const ev of ['pointerup', 'pointercancel', 'pointerleave']) el.addEventListener(ev, cancel);
    el.addEventListener('click', (e) => {
      if (held) {
        held = false;
        e.preventDefault();
        return;
      }
      tap();
    });
    el.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      if (!held) {
        held = true;
        hold();
      }
    });
  }

  // A cost line's label, short: "Knight (Level 1)" is just "Knight".
  function costLabel(label) {
    return label.replace(' (Level 1)', '').replace(' (enchantment)', '');
  }

  // Choose a unit's ability for one level.
  function abilityPicker(rid, tier, back) {
    const run = UI.run;
    const r = R.unitById(run, rid);
    const picks = UNITS[r.type].abilities[tier].filter((id) => !TALENTS[id]);
    openSheet(
      `${sheetHead(tier === 1 ? 'Ability' : 'Level 2 ability', `${esc(r.name)} the ${esc(UNITS[r.type].name)}: pick one.`, true)}
      <div class="picks">${picks.map((id) => abilityCard(r, tier, id, false)).join('')}</div>
      <div class="actions"><button class="btn" id="apBack">Back</button></div>`,
      (sh) => {
        for (const b of $$('[data-ab]', sh))
          b.onclick = () => {
            R.setAbility(run, rid, tier, b.dataset.ab.split(':')[1]);
            R.save(run);
            sfx('select');
            back();
          };
        $('#apBack', sh).onclick = () => back();
      }
    );
  }

  function renderWarRoom() {
    const run = UI.run;
    const wr = UI.wr;
    if (!wr || !run.pending || run.pending.type !== 'battle') return;
    for (const rid of [...wr.dep.keys()]) if (!R.unitById(run, rid)) wr.dep.delete(rid);
    // The plan as it stands is kept, so stepping away (or losing) does not undo it.
    run.pending.lastDep = wrDepArray();
    R.save(run);
    wr.supply = R.supplyFor(run);
    const enc = wr.enc;
    const s = E.createBattle(R.battleConfig(run, wrDepArray()));
    wr.s = s;
    const b = UI.board;
    b.syncFromState(s);
    // A picked-up unit wriggles in the hand until it is put down.
    b.carry(wr.sel && wr.dep.has(wr.sel) ? wr.sel : null);
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
    if (wr.spot && !wr.sel && !wr.inspect && !wr.tile) ov.select = [wr.spot.x, wr.spot.y];
    b.ov = ov;
    // A priority picked here: its marker on the board, and the battle starts with it.
    const focusT = wrFocusTarget(s);
    if (!focusT) run.pending.focus = null;
    b.focus = focusT ? { x: focusT.x, y: focusT.y } : null;
    const focusLine = focusT
      ? `<div class="focusline">${ic('target')}<span>Priority: <b>${esc(run.pending.focus.label)}</b>${missionTarget(focusT.unit) ? ' ' + vipCheck : ''}. From the first turn, your army ${focusVerb(run.pending.focus)}.</span><button class="btn" id="wrUnfocus">Clear</button></div>`
      : '';

    const used = wrUsed();
    const left = wr.supply - used;
    const gold = Math.max(0, left) * R.LEAN_GOLD * (R.hasRelic(run, 'alchemist_stone') ? 3 : 1);
    const pips = [];
    for (let i = 0; i < Math.max(wr.supply, used); i++) pips.push(`<span class="pip ${i < used ? (i >= wr.supply ? 'over' : 'used') : ''}"></span>`);
    const attempt = run.pending.attempt || 0;

    const foeSup = R.encSupply(enc);
    supplyBadges({ P: { label: 'Your army', left: wrUsed(), total: wr.supply, tip: `Your army: ${wrUsed()} of your ${wr.supply} Supply fielded` }, E: { label: 'Enemy', total: foeSup.army, coming: foeSup.waves } });
    $('#topbar').innerHTML = `<div class="title"><b>War Room</b><span>${esc(enc.name)} · ${battleOrigin(run).short || encKindLabel(enc)}${attempt ? ' · attempt ' + (attempt + 1) : ''}</span></div>
      <button class="btn icon-only" id="wrArmy" aria-label="Army">${ic('army')}</button>
      <button class="btn icon-only" id="wrMenu" aria-label="Menu">${ic('menu')}</button>`;
    $('#wrArmy').onclick = () => armySheet(() => renderWarRoom());
    $('#wrMenu').onclick = () => menuSheet(false);

    let body = '';
    if (wr.tab === 'army') {
      // The unit a bonus goal asks for comes first, where you cannot miss it.
      const star = R.bonusUnit(run, enc);
      const first = [star, R.coreUnit(run)].filter((u, i, a) => u && a.indexOf(u) === i);
      body = `<div class="roster">${[...first, ...run.roster.filter((u) => !first.includes(u))]
        .map((u) => {
          const deployed = wr.dep.has(u.id);
          const cost = R.unitCost(run, u);
          const cant = !deployed && cost > left;
          const featured = u === star;
          // The badge reads base cost, plus what its loadout adds (only units on the field
          // carry anything).
          const bare = R.bareCost(run, u);
          return `<button class="rcard ${deployed ? 'deployed' : ''} ${wr.sel === u.id ? 'sel' : ''} ${cant ? 'dim' : ''}" data-rid="${u.id}">
            <span class="cost" title="${cost > bare ? `${bare} base + ${cost - bare} from its loadout` : 'Base cost'}">${bare}${cost > bare ? `<i>+${cost - bare}</i>` : ''}</span>${featured ? '<span class="flag feat">Quest</span>' : u.core ? '<span class="flag core" title="Always fights, free of Supply">Always</span>' : u.enchant ? `<span class="flag ench">${ic('gem')}</span>` : ''}
            <canvas data-p="${u.type}:P"></canvas>
            <span class="nm">${esc(u.name)} ${levelBadge(u.load.lv)}</span>
            <span class="ty">${UNITS[u.type].name}</span></button>`;
        })
        .join('')}</div>`;
    } else {
      const tips = R.scoutTips(enc);
      body = `<div class="intel">
        <div class="intel-list">${s.units
          .filter((u) => u.team === 'E' && focusable(u))
          .map(
            (u) => `<button class="rcard ${wr.inspect === u.uid ? 'sel' : ''} ${missionTarget(u) ? 'vip' : ''}" data-uid="${u.uid}">${missionTarget(u) ? `<span class="flag vip">${ic('crown')} ${missionTarget(u) === 'boss' ? 'Boss' : 'Commander'}</span>` : ''}
              <canvas data-p="${u.type}:E"></canvas>
              <span class="nm">${esc(UNITS[u.type].name)} ${u.level > 1 ? levelBadge(u.level) : ''}</span>
              <span class="ty">${u.bounty ? `${ic('gold')} ${u.bounty} gold inside` : esc(u.a1 ? ABILITIES[u.a1].name : u.acts.length > 1 ? u.acts[1].name : pct(u.armor) + ' arm · ' + pct(u.res) + ' res')}</span></button>`
          )
          .join('')}</div>
        ${reinforcementsHTML(s)}
        ${tips.length ? `<ul class="tips">${tips.map((t) => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}
      </div>`;
    }

    let selBlock = '';
    // How to set up the board: below Begin battle, so the goals come first.
    let helpBlock = '';
    if (wr.spot && !wr.sel && !wr.inspect && !wr.tile && !wrRidAt(wr.spot.x, wr.spot.y)) {
      selBlock = `<div class="hint">${ic('target')} Tile picked. Tap a unit card to put that unit here (one already on the field moves here). Tap the tile again to cancel.</div>`;
    } else if (wr.sel && R.unitById(run, wr.sel)) {
      const held = R.unitById(run, wr.sel);
      selBlock = `<div class="hint">${ic('army')} <b>${esc(held.name)}</b> the ${esc(UNITS[held.type].name)} is picked up. Drag it to an open blue tile and let go, or tap one.</div>
        <div class="actions"><button class="btn" id="wrPutBack">${ic('undo')} Put it back</button></div>`;
    } else if (wr.inspect && s.byId[wr.inspect]) {
      const u = s.byId[wr.inspect];
      const isFocus = focusT && focusT.unit === u;
      const canFocus = focusable(u);
      selBlock = `<div class="hint">${
        u.bounty
          ? `${ic('gold')} ${esc(UNITS[u.type].name)}: ${u.hp} HP, ${pct(u.armor)} armor. It cannot fight back. Break it and your army picks up <b>${u.bounty} gold</b>, paid with the battle's gold when you win.`
          : `${missionTarget(u) === 'Commander' ? `${ic('crown')} <b>Enemy Commander</b>, ${/^[AEIOU]/.test(UNITS[u.type].name) ? 'an' : 'a'} ` : 'Enemy '}${esc(UNITS[u.type].name)}${u.level > 1 ? ' (Level ' + u.level + ')' : ''}: ${pct(u.armor)} armor, ${pct(u.res)} magic resistance. Red tiles on the board: everywhere it could hit on its next turn, splash included.`
      }</div>
        ${behindHint(s, u.uid)}
        ${u.bounty ? '' : actsHTML(u)}
        <div class="actions">${canFocus ? (isFocus ? `<button class="btn" id="wrUnfocus">${ic('close')} Clear priority</button>` : `<button class="btn primary" id="wrFocus">${ic('target')} Priority${missionTarget(u) ? ' ' + vipBadge(missionTarget(u)) : ''}</button>`) : ''}<button class="btn" id="wrEInfo">${ic('help')} Details</button></div>
        ${canFocus ? vipNote(s, u, isFocus) : ''}
        ${canFocus && !isFocus ? `<p class="small muted">${u.bounty ? 'Priority: from the first turn, your whole army goes for the barricade and breaks it for the gold.' : 'Priority: from the first turn, your whole army goes all out for it, whatever the cost.'}</p>` : ''}`;
    } else if (tileF) {
      const loot = E.lootAt(s, wr.tile.x, wr.tile.y);
      const shrine = !loot && isShrine(s, wr.tile.x, wr.tile.y);
      const open = !loot && !shrine && (tileF.open || isObstacle(s, wr.tile.x, wr.tile.y));
      const isFocus = focusT && ((loot && focusT.loot === loot) || (shrine && focusT.hold) || (open && focusT.tile && focusT.x === wr.tile.x && focusT.y === wr.tile.y));
      const why = shrine
        ? 'Priority: from the first turn, your army makes for the shrine: one unit stands on it and stays, the rest guard it.'
        : open
          ? isObstacle(s, wr.tile.x, wr.tile.y)
            ? `Priority: from the first turn, your army gathers around the ${obstacleName().toLowerCase()} and holds there, attacking whatever comes in reach.`
            : 'Priority: from the first turn, your army moves here and huddles as close as it can, attacking whatever comes in reach.'
          : 'Priority: from the first turn, your army heads for it and takes it.';
      selBlock = tileInfoHTML(tileF) + (loot || shrine || open ? `<div class="actions">${isFocus ? `<button class="btn" id="wrUnfocus">${ic('close')} Clear priority</button>` : `<button class="btn primary" id="wrFocus">${ic('target')} Priority</button>`}</div>${isFocus ? '' : `<p class="small muted">${why}</p>`}` : '');
    } else if (wr.dep.size === 0) {
      helpBlock = `<div class="hint wr-help">Study the enemy, then tap unit cards to put them in the battle (tap again to take one out). Tap a unit on the board (or hold its card) for its full loadout: level, abilities, talents, skills, gear and stats. Long-press a unit on the board and drag it to move it. Tap an empty blue tile, then a unit card, to put that unit there. Every point of Supply counts. Tap an enemy, a building or a chest to look at it, and to make it your army's priority.</div>`;
    } else helpBlock = `<div class="small muted wr-help">Tap a card to put a unit in or take it out; hold a card, or tap the unit on the board, for its full loadout. To move a unit, long-press it and drag it to an open blue tile; or tap an empty blue tile, then a card. Tap an enemy or a chest to make it your army's priority.</div>`;

    // Every deployed unit's cost, when the Supply bar is tapped.
    const costList = wr.costOpen
      ? `<div class="armycost">${[...wr.dep.keys()]
          .map((rid) => {
            const r = R.unitById(run, rid);
            return `<button class="ac-row" data-acrid="${rid}"><span>${esc(r.name)} <span class="muted">${esc(UNITS[r.type].name)}</span></span><span class="ac-parts">${R.costBreakdown(run, r)
              .filter((x) => x.cost)
              .map((x) => `${esc(costLabel(x.label))} ${x.cost}`)
              .join(' + ')}</span><b>${R.unitCost(run, r)}</b></button>`;
          })
          .join('')}${wr.dep.size ? '' : '<div class="small muted">No units deployed yet.</div>'}</div>`
      : '';

    const over = used > wr.supply;
    // The unit strips keep where you scrolled them to when the panel redraws.
    wr.stripX = wr.stripX || {};
    for (const el of $$('#cmd .roster, #cmd .intel-list')) wr.stripX[el.className] = el.scrollLeft;
    $('#cmd').innerHTML = `
      <div class="origin ${run.pending.fromEvent ? 'event' : ''}">${battleOrigin(run).html}</div>
      <button class="cp-meter tap" id="wrMeter" aria-label="What each unit costs"><span class="res">${ic('command')}<span class="num">${used}/${wr.supply}</span></span><div class="pips">${pips.join('')}</div>
        <span class="res" title="Units on the field">${ic('army')}<span class="num">${wr.dep.size}</span></span></button>
      <div class="small ${over ? 'bad-text' : 'muted'}">${
        over ? `Over budget by ${used - wr.supply} Supply: lower a level, drop an item, or remove a unit.` : left > 0 ? `${left} unspent → <b style="color:var(--brass-hi)">+${gold} gold</b> if you win` : 'Every point of Supply committed.'
      } <span class="muted">· Tap the bar to ${wr.costOpen ? 'hide' : 'see'} what each unit costs.</span></div>
      ${costList}
      <div class="tabs"><button class="btn ${wr.tab === 'army' ? 'on' : ''}" id="wrTabA">${ic('army')} Your army</button>
        <button class="btn ${wr.tab === 'intel' ? 'on' : ''}" id="wrTabI">${ic('eye')} Enemy (${s.units.filter((u) => u.team === 'E' && E.counts(u)).length})</button></div>
      ${body}
      ${selBlock}
      ${focusLine}
      ${objectivesHTML(enc)}
      <div class="actions"><button class="btn" id="wrAuto">${ic('star')} ${wr.auto ? 'Suggest another' : 'Auto'}</button><button class="btn" id="wrClear" ${wr.dep.size ? '' : 'disabled'}>Clear</button>${run.pending.fromEvent ? '' : `<button class="btn" id="wrBack">${ic('undo')} Other battles</button>`}</div>
      <div class="actions sticky"><button class="btn primary" id="wrFight" ${wr.dep.size && !over ? '' : 'disabled'}>${ic('swords')} ${UI.prefs.autoBattle ? 'Begin battle' : 'Fight'}</button></div>
      ${helpBlock}`;
    const cmd = $('#cmd');
    drawPortraits(cmd);
    for (const el of $$('.roster, .intel-list', cmd)) el.scrollLeft = wr.stripX[el.className] || 0;
    $('#wrTabA').onclick = () => {
      wr.tab = 'army';
      renderWarRoom();
    };
    $('#wrTabI').onclick = () => {
      wr.tab = 'intel';
      renderWarRoom();
    };
    for (const c of $$('.rcard[data-rid]', cmd)) tapHold(c, () => wrCard(c.dataset.rid), () => wrLoadout(c.dataset.rid));
    for (const c of $$('.rcard[data-uid]', cmd))
      c.onclick = () => {
        wr.inspect = wr.inspect === +c.dataset.uid ? null : +c.dataset.uid;
        wr.sel = null;
        wr.tile = null;
        renderWarRoom();
      };
    $('#wrMeter').onclick = () => {
      wr.costOpen = !wr.costOpen;
      sfx('click');
      renderWarRoom();
    };
    for (const b of $$('[data-acrid]', cmd)) b.onclick = () => wrLoadout(b.dataset.acrid);
    if ($('#wrPutBack'))
      $('#wrPutBack').onclick = () => {
        wr.sel = null;
        sfx('click');
        renderWarRoom();
      };
    if ($('#wrEInfo')) $('#wrEInfo').onclick = () => battleUnitSheet(s.byId[wr.inspect]);
    if ($('#wrFocus'))
      $('#wrFocus').onclick = () => {
        const u = wr.inspect && s.byId[wr.inspect];
        const l = !u && wr.tile && E.lootAt(s, wr.tile.x, wr.tile.y);
        const shrine = !u && !l && wr.tile && isShrine(s, wr.tile.x, wr.tile.y);
        if (u) run.pending.focus = { kind: 'unit', x: u.x, y: u.y, label: focusName(u), vip: missionTarget(u) };
        else if (l) run.pending.focus = { kind: 'loot', x: l.x, y: l.y, label: `the ${R.LOOT_NAMES[l.kind]}` };
        else if (shrine) run.pending.focus = { kind: 'hold', x: wr.tile.x, y: wr.tile.y, label: 'the shrine' };
        else if (wr.tile && isRallySpot(s, wr.tile.x, wr.tile.y))
          run.pending.focus = { kind: 'tile', x: wr.tile.x, y: wr.tile.y, label: isObstacle(s, wr.tile.x, wr.tile.y) ? `the ${obstacleName().toLowerCase()}` : 'the marked spot' };
        else return;
        wr.sel = null;
        toast(`Priority: ${run.pending.focus.label}. ${u && missionTarget(u) ? `Confirmed: that is the ${missionTarget(u)}, the mission's target. ` : ''}From the first turn, your army ${focusVerb(run.pending.focus)}.`, 3600);
        sfx('click');
        wr.inspect = null;
        wr.tile = null;
        renderWarRoom();
      };
    for (const el of $$('#wrUnfocus'))
      el.onclick = () => {
        run.pending.focus = null;
        toast('Priority cleared. Your army fights on normal orders.');
        sfx('click');
        renderWarRoom();
      };
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
      const star = R.bonusUnit(run, wr.enc);
      if (star && wr.dep.has(star.id)) why += ` ${star.name} the ${UNITS[star.type].name} is in for the bonus goal.`;
      if (n('magic') + n('phys')) toast(`Auto: ${got}. ${why}`, 5000);
    };
    $('#wrClear').onclick = () => {
      for (const rid of [...wr.dep.keys()]) {
        if (rid === wr.star || rid === wr.core) continue;
        wr.dep.delete(rid);
        R.stripLoad(run, R.unitById(run, rid));
      }
      R.save(run);
      wr.sel = null;
      renderWarRoom();
    };
    if ($('#wrBack'))
      $('#wrBack').onclick = () => {
        R.backToChoice(run);
        if (UI.board) UI.board.stop();
        route();
      };
    $('#wrFight').onclick = () => wrFight();
  }

  // A tap on a unit card puts the unit in the battle, or takes it out again: quick to try
  // armies out. Holding the card opens its loadout instead (wrPick).
  function wrCard(rid) {
    const wr = UI.wr;
    wr.tile = null;
    // A blue tile picked first: this unit goes there (one already on the field moves there).
    const spot = wr.spot && !wrRidAt(wr.spot.x, wr.spot.y) && isDeployTile(wr.spot.x, wr.spot.y) ? wr.spot : null;
    wr.spot = null;
    if (spot) {
      const d = wr.dep.get(rid);
      if (d) {
        d.x = spot.x;
        d.y = spot.y;
        sfx('step');
        renderWarRoom();
        return;
      }
      wr.dep.set(rid, { x: spot.x, y: spot.y, facing: 0 });
      wr.inspect = null;
      sfx('select');
      const over = wrUsed() - wr.supply;
      if (over > 0) toast(`Over budget by ${over} Supply. Lower a level or drop an item to fight.`);
      renderWarRoom();
      wrGuide(rid);
      return;
    }
    if (wr.dep.has(rid)) {
      wrBench(rid);
      return;
    }
    wrAdd(rid);
  }

  // A unit's loadout in the War Room: make it the rally point, or take it off the field.
  function loadoutFieldButtons(rid) {
    const ft = UI.wr && UI.wr.s ? wrFocusTarget(UI.wr.s) : null;
    const mine = ft && ft.ally && ft.ally.rid === rid;
    return `<button class="btn" id="loFocus">${ic(mine ? 'close' : 'target')} ${mine ? 'Clear priority' : 'Priority'}</button>${UI.wr && (rid === UI.wr.star || rid === UI.wr.core) ? '' : `<button class="btn danger" id="loRemove">${ic('close')} Take off the field</button>`}`;
  }

  // The priority picked in the War Room, found on the field as it stands: an enemy unit or
  // building at that spot, or loot there. Null when there is none (or it no longer fits).
  function wrFocusTarget(s) {
    const f = UI.run.pending && UI.run.pending.focus;
    if (!f) return null;
    if (f.kind === 'unit') {
      const u = s.units.find((v) => v.alive && v.team === 'E' && v.x === f.x && v.y === f.y);
      return u ? { unit: u, x: u.x, y: u.y } : null;
    }
    if (f.kind === 'hold') return isShrine(s, f.x, f.y) ? { hold: true, x: f.x, y: f.y } : null;
    if (f.kind === 'ally') {
      const u = s.units.find((v) => v.alive && v.team === 'P' && v.rid === f.rid);
      return u ? { tile: true, ally: u, x: u.x, y: u.y } : null;
    }
    if (f.kind === 'tile') return [E.T_GRASS, E.T_ROCK].includes(s.terrain[E.idx(s, f.x, f.y)]) ? { tile: true, x: f.x, y: f.y } : null;
    const l = E.lootAt(s, f.x, f.y);
    return l ? { loot: l, x: l.x, y: l.y } : null;
  }

  // Take a unit off the field: back to the bench, bare. A quest's unit stays.
  function wrBench(rid) {
    const wr = UI.wr;
    const r = R.unitById(UI.run, rid);
    if (rid === wr.star) {
      toast(`${r.name} insists on fighting this battle (the quest). They stay on the field.`);
      return false;
    }
    if (rid === wr.core) {
      toast(`${r.name} the Cleric fights in every battle, free of Supply, and stays on the field. Long-press and drag them to choose where they stand.`, 4000);
      return false;
    }
    wr.dep.delete(rid);
    R.stripLoad(UI.run, r);
    R.save(UI.run);
    if (wr.sel === rid) wr.sel = null;
    sfx('click');
    renderWarRoom();
    return true;
  }

  // Pick a unit up: its loadout opens below the army, and a blue tile puts it there.
  function wrPick(rid) {
    const wr = UI.wr;
    wr.sel = rid;
    wr.inspect = null;
    wr.tile = null;
    sfx('select');
    renderWarRoom();
  }

  // Put a unit in the battle on the first free blue tile that suits it.
  function wrAdd(rid) {
    const run = UI.run;
    const wr = UI.wr;
    const r = R.unitById(run, rid);
    const taken = new Set([...wr.dep.values()].map((d) => d.x + ',' + d.y));
    const slot = R.deploySlots(run, wr.enc, R.isFront(r.type), taken)[0];
    if (!slot) {
      toast('Your deployment zone is full.');
      return;
    }
    wr.dep.set(rid, { x: slot.x, y: slot.y, facing: 0 });
    wr.inspect = null;
    sfx('select');
    const over = wrUsed() - wr.supply;
    if (over > 0) toast(`Over budget by ${over} Supply. Lower a level or drop an item to fight.`);
    renderWarRoom();
    wrGuide(rid);
  }

  function wrTap(hit) {
    const wr = UI.wr;
    if (!wr) return;
    const s = wr.s;
    // A picked blue tile lasts until the next tap (a card tap uses it).
    const hadSpot = wr.spot;
    wr.spot = null;
    // Any tap closes the feature panel; tapping the same feature again keeps it closed.
    const shown = wr.tile;
    wr.tile = null;
    const raw = hit.tile;
    const tileUnit = raw ? E.at(s, raw.x, raw.y) : null;
    let t = raw;
    // With a unit picked up, an open blue tile under the finger is where it goes.
    const placing = wr.sel && raw && !tileUnit && isDeployTile(raw.x, raw.y);
    // Otherwise the unit in front, or tapping again, the one behind it.
    const spriteUnit = placing ? null : pickAt(hit, s);
    if (spriteUnit) t = { x: spriteUnit.x, y: spriteUnit.y };
    // A rock or chest in front of everything else: say what it is.
    if (!placing && !unitInFront(hit, s) && (hit.props || []).length) t = null;
    if (!t) return wrMiss(hit, shown);
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
      wr.inspect = null;
      // Holding a unit: an occupied tile is no place to drop it. Units never swap.
      if (wr.sel && wr.sel !== rid) {
        toast('That tile is taken. Drop it on an open blue tile.');
        wr.sel = null;
        sfx('click');
        renderWarRoom();
        return;
      }
      // The held unit itself: put it back down where it was.
      if (wr.sel === rid) {
        wr.sel = null;
        sfx('click');
        renderWarRoom();
        return;
      }
      // A quick tap: its full loadout. (Long-press picks it up to move it.)
      return wrLoadout(rid);
    }
    if (isDeployTile(t.x, t.y)) {
      if (wr.sel) return wrPlace(t.x, t.y);
      // An empty blue tile first: the next unit card you tap goes there. Again: never mind.
      wr.spot = hadSpot && hadSpot.x === t.x && hadSpot.y === t.y ? null : { x: t.x, y: t.y };
      wr.inspect = null;
      sfx('click');
      renderWarRoom();
      return;
    }
    wrMiss(hit, shown);
  }

  // Put the picked unit down on a free blue tile (from the bench too, room allowing), and
  // let it go so the next tap does not move it again.
  function wrPlace(x, y) {
    const wr = UI.wr;
    const rid = wr.sel;
    const d = wr.dep.get(rid);
    if (d) {
      d.x = x;
      d.y = y;
    } else {
      wr.dep.set(rid, { x, y, facing: 0 });
      const over = wrUsed() - wr.supply;
      if (over > 0) toast(`Over budget by ${over} Supply. Lower a level or drop an item to fight.`);
    }
    wr.sel = null;
    sfx('step');
    renderWarRoom();
    if (!d) wrGuide(rid);
  }

  // A unit just put on the field: walk through its kit one question at a time, its level,
  // its ability picks, then each talent, skill and gear slot. Each question can be passed
  // over with Continue (keeping what it has, or leaving the slot empty); one with nothing to
  // choose from is skipped; Exit leaves the whole setup there.
  function wrGuide(rid) {
    const run = UI.run;
    const wr = UI.wr;
    if (!UI.prefs.guide || !wr || !wr.dep.has(rid)) return;
    const r = R.unitById(run, rid);
    const T = UNITS[r.type];
    const done = new Set();
    const left = () => wr.supply - wrUsed();
    // What a change would cost, found by trying it.
    const costOf = (apply, undo) => {
      const before = R.unitCost(run, r);
      apply();
      const c = R.unitCost(run, r) - before;
      undo();
      return c;
    };
    // The questions as the unit stands now (a higher level opens more of them).
    const questions = () => {
      const L = r.load;
      const out = [];
      const lv0 = L.lv;
      if (!done.has('lv'))
        out.push({ key: 'lv', title: 'Level', opts: [2, 3].filter((lv) => lv > lv0).map((lv) => ({
          val: lv, name: `Level ${lv}`,
          desc: lv === 2 ? '+20% HP, +15% damage, a second ability, a second talent slot and a skill slot.' : '+40% HP, +30% damage, its Mastery, a third talent slot and a second gear slot.',
          cost: costOf(() => R.setLevel(run, rid, lv), () => R.setLevel(run, rid, lv0)),
        })), skip: `keep Level ${lv0}` });
      for (const tier of [1, 2]) {
        if (r.load.lv < tier) continue;
        const cur = r.load['a' + tier];
        const ids = T.abilities[tier].filter((id) => !TALENTS[id] && id !== cur);
        out.push({ key: 'a' + tier, title: tier === 1 ? 'Ability' : 'Level 2 ability', opts: ids.map((id) => ({ val: id, name: ABILITIES[id].name, desc: ABILITIES[id].desc, cost: ABILITIES[id].cost - (ABILITIES[cur] ? ABILITIES[cur].cost : 0) })), skip: `keep ${ABILITIES[cur] ? ABILITIES[cur].name : 'the free one'}` });
      }
      const sl = R.slotsFor(r.load.lv);
      for (const kind of ['talent', 'skill', 'gear']) {
        const n = kind === 'talent' ? sl.talents : kind === 'skill' ? sl.skills : sl.gear;
        const held = r.load[SLOT_KEY[kind]];
        // One question per kind: a pick asks about the next open slot, Continue skips them all.
        if (held.length >= n) continue;
        const heldIds = held.map((x) => R.itemByUid(run, x).id);
        // One option per kind of item you have free that fits, however many copies.
        const seen = new Set();
        const opts = [];
        for (const it of R.freeItems(run, kind)) {
          const d2 = R.itemDef(it);
          if (seen.has(it.id) || !D.eligible(r.type, d2) || (kind === 'talent' && (TALENTS[it.id].cls !== r.type || heldIds.includes(it.id)))) continue;
          seen.add(it.id);
          opts.push({ val: it.uid, name: d2.name, desc: d2.desc, cost: d2.cost });
        }
        out.push({ key: kind, slot: true, title: `${cap1(kind)}${n > 1 ? ` (slot ${held.length + 1} of ${n})` : ''}`, kind, opts, skip: n - held.length > 1 ? `leave its ${kind} slots empty` : 'leave it empty' });
      }
      return out;
    };
    const finish = () => {
      UI.onSheetClose = null;
      closeSheet();
      if (UI.wr !== wr) return;
      wr.sel = null;
      R.save(run);
      renderWarRoom();
    };
    const step = () => {
      const q = questions().find((x) => !done.has(x.key) && x.opts.length);
      if (!q) return finish();
      const room = left();
      const kindIcon = q.kind ? `<span class="itemico ${q.kind}">${ic(ITEM_ICON[q.kind])}</span>` : '';
      openSheet(
        `${sheetHead(`${esc(r.name)} the ${esc(T.name)}`, 'Kit it out', true)}
        ${budgetBar(wrUsed(), wr.supply)}
        <div class="guide-q">${kindIcon}<b>${esc(q.title)}</b><span class="small muted">Pick one, or Continue to ${esc(q.skip)} and move on.</span></div>
        <div class="picks">${q.opts
          .map((o, i) => {
            const over = o.cost > room;
            return `<button class="pick ${over ? 'locked' : ''}" data-gopt="${i}" ${over ? 'disabled' : ''}>
              <span class="pk-head"><b>${esc(o.name)}</b><span class="cost">${o.cost > 0 ? '+' + o.cost : o.cost < 0 ? String(o.cost) : 'free'}</span></span>
              <span class="pk-desc">${esc(o.desc)}${over ? ' <b class="bad-text">Not enough Supply.</b>' : ''}</span></button>`;
          })
          .join('')}</div>
        <div class="actions"><button class="btn" id="gDone">${ic('close')} Exit</button><button class="btn primary" id="gNo">Continue ${ic('play')}</button></div>`,
        (sh) => {
          for (const b of $$('[data-gopt]', sh))
            b.onclick = () => {
              const o = q.opts[+b.dataset.gopt];
              const rect = b.getBoundingClientRect();
              const was = left();
              if (q.key === 'lv') R.setLevel(run, rid, o.val);
              else if (q.key === 'a1' || q.key === 'a2') R.setAbility(run, rid, +q.key[1], o.val);
              else R.assignItem(run, rid, o.val);
              if (!q.slot) done.add(q.key);
              R.save(run);
              sfx('select');
              renderWarRoom();
              step();
              supplyPop(rect, was, left());
            };
          $('#gNo', sh).onclick = () => {
            done.add(q.key);
            sfx('click');
            step();
          };
          $('#gDone', sh).onclick = finish;
        }
      );
      UI.onSheetClose = finish;
    };
    step();
  }

  // A tap that found no blue tile. With a unit picked up, the nearest free blue tile within
  // reach of the finger takes it (corner tiles are small targets); failing that (a tap on
  // the empty space around the board, or far from the blue tiles), the unit is let go.
  // With nothing picked up, explain the rock or chest there.
  function wrMiss(hit, shown) {
    const wr = UI.wr;
    if (!wr.sel) return wrFeature(hit, shown);
    const free = [];
    for (const y of wr.rows) for (let x = 0; x < wr.enc.w; x++) if (isDeployTile(x, y) && !wrRidAt(x, y)) free.push({ x, y });
    const m = snap({ px: hit.px, py: hit.py, tile: null, unitTile: null }, free);
    if (m) return wrPlace(m.x, m.y);
    wr.sel = null;
    sfx('click');
    renderWarRoom();
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
    // Your unit: pick it up. Drag it to an open blue tile and let go (or let go where it
    // is, then tap an open blue tile). The board holds still meanwhile.
    if (u.team === 'P' && u.rid) {
      wrPick(u.rid);
      wr.drag = { rid: u.rid };
      sfx('select');
      try {
        if (navigator.vibrate) navigator.vibrate(15);
      } catch (e) {}
      return 'drag';
    }
    battleUnitSheet(u);
  }

  // A blue tile a dragged unit may land on: open, or the one it stands on.
  function wrDropOK(rid, t) {
    if (!t || !isDeployTile(t.x, t.y)) return false;
    const there = wrRidAt(t.x, t.y);
    return !there || there === rid;
  }

  // Dragging: the unit follows the finger tile by tile over open blue tiles.
  function wrDragMove(hit) {
    const wr = UI.wr;
    if (!wr || !wr.drag) return;
    const b = UI.board;
    const t = hit && hit.tile;
    const v = [...b.vis.values()].find((x) => x.rid === wr.drag.rid);
    if (wrDropOK(wr.drag.rid, t)) {
      b.ov = Object.assign({}, b.ov, { ghost: [t.x, t.y], select: [t.x, t.y] });
      if (v) {
        v.x = t.x;
        v.y = t.y;
      }
      wr.drag.to = { x: t.x, y: t.y };
    } else if (t) b.ov = Object.assign({}, b.ov, { ghost: [t.x, t.y] });
  }

  // Let go: it lands on the last open blue tile it crossed. Let go without moving and it
  // stays picked up, so a tap on an open blue tile can put it down too.
  function wrDragEnd(hit, moved) {
    const wr = UI.wr;
    if (!wr || !wr.drag) return;
    const d = wr.drag;
    wr.drag = null;
    if (!moved) {
      toast(`${R.unitById(UI.run, d.rid).name} picked up: drag it to an open blue tile, or tap one.`, 2600);
      renderWarRoom();
      return;
    }
    const tile = hit && hit.tile;
    const onUnit = tile && wrRidAt(tile.x, tile.y) && wrRidAt(tile.x, tile.y) !== d.rid;
    // On another unit: back where it was (units never swap). Just past the blue tiles: the
    // last open blue tile it crossed.
    const t = wrDropOK(d.rid, tile) ? tile : onUnit ? null : d.to;
    if (t && wr.dep.has(d.rid)) return wrPlace(t.x, t.y);
    wr.sel = null;
    if (onUnit) toast('That tile is taken: it goes back. Units never swap places.');
    renderWarRoom();
  }

  // Hold a unit (its card, or itself on the board): its full loadout, stats and all.
  function wrLoadout(rid) {
    sfx('select');
    loadoutSheet(rid, () => {
      UI.onSheetClose = null;
      closeSheet();
      if (UI.wr) renderWarRoom();
    });
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
    if (!dep.some((d) => isAttacker(R.unitById(run, d.rid).type))) {
      toast('Deploy at least one unit that can deal damage.');
      return;
    }
    run.pending.lastDep = dep;
    run.lastPlan = dep;
    R.save(run);
    startBattle(dep);
  }

  // ------------------------------------------------------------ battle

  async function startBattle(dep) {
    hideToast(); // what the War Room said is no use on the battlefield
    music(UI.run.pending.enc.kind === 'boss' ? 'boss' : 'battle');
    const run = UI.run;
    const enc = run.pending.enc;
    const diff = DIFFICULTIES.find((d) => d.id === run.difficulty) || DIFFICULTIES[1];
    const s = E.createBattle(R.battleConfig(run, dep));
    E.drainEvents(s);
    UI.wr = null;
    UI.battle = { s, dep, enc, mode: 'idle', sel: null, target: null, ai: 0, busy: false, temp: diff.temp, confirmEnd: false };
    // A priority picked in the War Room holds from the first turn.
    const pf = wrFocusTarget(s);
    const lb = pf && run.pending.focus.label;
    if (pf) UI.battle.focus = pf.unit ? { uid: pf.unit.uid, label: lb } : pf.ally ? { ally: pf.ally.uid, label: lb } : pf.hold ? { hold: true, label: lb } : pf.tile ? { tile: true, x: pf.x, y: pf.y, label: lb } : { loot: pf.loot.id, label: lb };
    const b = UI.board;
    b.clearUnits();
    b.ov = {};
    b.speed = paceOf();
    b.focus = null;
    b.syncFromState(s);
    b.setObjectives(s.loot, s.hold);
    b.activeSide = 'P';
    b.focus = focusSpot(UI.battle);
    UI.boardTap = btTap;
    UI.boardLong = btLong;
    UI.boardDragMove = UI.boardDragEnd = null;
    battleTools();
    UI.battle.log = [];
    showBanner(s.side === 'E' ? 'Enemy moves first' : 'Your turn', s.side === 'E');
    sfx(s.side === 'E' ? 'enemyturn' : 'turn');
    renderBattle();
    // The enemy opens the battle; then the sides take turns, one unit each, in the order
    // of each side's unit queue.
    UI.battle.busy = true;
    await pause(800);
    if (UI.battle && UI.battle.s === s) await runBattle();
  }

  // Nothing beside the board in battle: speed and pause sit in the top bar, by the menu.
  function battleTools() {
    boardTools('');
  }

  // The top bar's speed button: 1x or 2x.
  function toggleSpeed() {
    UI.prefs.speed = speedOf() > 1 ? 1 : 2;
    UI.prefs.fast = UI.prefs.speed > 1;
    savePrefs();
    UI.board.speed = paceOf();
    sfx('click');
    renderBattle();
  }

  // Play turns until the battle ends, or until it is your turn and you command by hand.
  async function runBattle() {
    const B = UI.battle;
    if (!B || B.running) return;
    B.running = true;
    try {
      while (UI.battle === B && !B.s.over) {
        if (B.paused) {
          B.busy = false;
          renderBattle();
          while (B.paused && UI.battle === B) await sleep(120);
          continue;
        }
        if (B.s.side === 'P' && !UI.prefs.autoBattle && !B.exhibition) {
          B.busy = false;
          B.mode = 'idle';
          B.sel = null;
          sfx('select');
          renderBattle();
          return;
        }
        await sideMoves(B.s.side);
      }
      if (UI.battle === B && B.s.over) battleOver();
    } finally {
      B.running = false;
    }
  }

  // The AI's orders for a side: yours chase your priority target, if you set one.
  function aiOpts(B, team) {
    if (B.exhibition) return { stance: 'balanced', temp: 0.3 };
    return team === 'E' ? { stance: B.enc.stance, temp: B.temp } : { stance: 'balanced', temp: 0.3, focus: B.focus };
  }

  // Where the priority target is now, for its marker on the board.
  function focusSpot(B) {
    const f = B && B.focus && AI.focusOf(B.s, 'P', B.focus);
    return f ? { x: f.x, y: f.y } : null;
  }

  // Your army goes all out for what you picked: an enemy unit or building, or loot.
  function setFocus(B) {
    if (B.exhibition) return;
    const s = B.s;
    const u = B.mode === 'inspect' && B.sel ? s.byId[B.sel] : null;
    const l = !u && B.mode === 'tile' && B.tile ? E.lootAt(s, B.tile.x, B.tile.y) : null;
    const shrine = !u && !l && B.mode === 'tile' && B.tile && isShrine(s, B.tile.x, B.tile.y);
    const open = !u && !l && !shrine && B.mode === 'tile' && B.tile && isRallySpot(s, B.tile.x, B.tile.y);
    if (isShrub(u)) B.focus = { tile: true, x: u.x, y: u.y, label: 'the shrub' };
    else if (u && u.team === 'P') B.focus = { ally: u.uid, label: u.name };
    else if (u) B.focus = { uid: u.uid, label: focusName(u) };
    else if (l) B.focus = { loot: l.id, label: `the ${R.LOOT_NAMES[l.kind]}` };
    else if (shrine) B.focus = { hold: true, label: 'the shrine' };
    else if (open) B.focus = { tile: true, x: B.tile.x, y: B.tile.y, label: isObstacle(s, B.tile.x, B.tile.y) ? `the ${obstacleName().toLowerCase()}` : 'the marked spot' };
    else return;
    toast(`Priority: ${B.focus.label}. ${missionTarget(u) ? `Confirmed: that is the ${missionTarget(u)}, the mission's target. ` : ''}Your army ${focusVerb(B.focus)}, whatever the cost.`, 3800);
    sfx('click');
    B.paused = false;
    B.mode = 'idle';
    B.sel = null;
    B.tile = null;
    renderBattle();
    if (!B.running) runBattle();
  }

  function clearFocus(B) {
    B.focus = null;
    UI.board.focus = null;
    toast('Priority cleared. Your army is back to normal orders.');
    renderBattle();
  }

  // A priority that has been met, or is gone, ends: back to normal orders.
  function checkFocus(B) {
    if (!B.focus || AI.focusOf(B.s, 'P', B.focus)) return;
    const was = B.focus;
    const v = was.uid && B.s.byId[was.uid];
    B.focus = null;
    UI.board.focus = null;
    if (B.s.over) return;
    if (was.ally) return toast(`${was.label} is down: rally over.`);
    const how = was.loot != null ? 'is yours' : v && v.escaped ? 'got away' : 'is down';
    toast(`Priority ${how === 'got away' ? 'over' : 'done'}: ${was.label} ${how}.`);
  }

  // One side turn played by the AI: the side's due unit moves, acts and faces.
  async function sideMoves(team) {
    const B = UI.battle;
    const s = B.s;
    const b = UI.board;
    B.busy = true;
    // Watching, a unit or tile you tapped to look at stays open while the battle plays on.
    const looking = (UI.prefs.autoBattle || B.exhibition) && (B.mode === 'inspect' || B.mode === 'tile');
    if (!B.paused && !looking) {
      B.mode = 'idle';
      B.sel = null;
    }
    const opts = aiOpts(B, team);
    const plan = AI.chooseActivation(s, team, opts);
    const u = (plan && s.byId[plan.uid]) || (s.due && s.byId[s.due]);
    if (u) {
      B.acting = u.uid;
      renderBattle();
      b.ov = Object.assign({}, b.ov, { select: [u.x, u.y] });
      await pause(380);
      if (UI.battle !== B) return; // you left the battle meanwhile
    }
    AI.runPlan(s, plan, opts);
    b.ov = {};
    await play(true);
    B.acting = null;
    checkFocus(B);
    b.focus = focusSpot(B);
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
      const uses = a.uses ? ` <span class="uses">${a.cdLeft > 0 ? `⏳${a.cdLeft}` : `${a.left}/${a.uses}`}</span>` : '';
      let why = '';
      if (a.left <= 0) why = 'no uses left';
      else if (a.cdLeft > 0) why = `cooling down: usable again in ${a.cdLeft} turn${a.cdLeft === 1 ? '' : 's'}`;
      else if (!usable) why = a.asMove ? 'already moved' : 'already acted';
      else if (!n) why = 'no targets';
      const icon = a.dmg ? dmgIcon(a.dmg) : ic(i === 0 ? 'target' : 'star');
      out.push(`<button class="btn act ${i === 0 ? 'primary' : ''}" data-act="${i}" ${n ? '' : 'disabled'} title="${esc(why)}">${icon} ${esc(actLabel(a, i))}${uses}</button>`);
    });
    return out.join('');
  }

  // The top bar's clock: turns to go before fatigue sets in, then each side's next fatigue
  // hit (the two sides count apart).
  function turnLine(s) {
    const tired = ['E', 'P'].filter((t) => E.tiring(s, t)).map((t) => `${t === 'E' ? 'enemy' : 'yours'} −${E.fatigueHit(s, t)}`);
    const clock = tired.length ? `<span class="overtime">Fatigue: ${tired.join(' · ')}</span>${tired.length < 2 && s.overtime && !s.inOvertime ? ` · all at ${s.overtime}` : ''}` : s.overtime ? `fatigue at ${s.overtime}` : '';
    if (s.cleanup) return `Turn ${s.turn} · <span class="reward">Cleanup: ${E.cleanupLeft(s)} left</span> · ${clock}`;
    if (s.won) return `Turn ${s.turn} · <span class="reward">Won</span> · ${clock}`;
    if (clock) return `Turn ${s.turn} · ${clock}`;
    return `Turn ${Math.min(s.turn, s.turnLimit)} of ${s.turnLimit}`;
  }

  // Whose a unit is: yours or the enemy's, or in a Hall of Fame match, which army's.
  function sideLabel(team) {
    const ex = UI.battle && UI.battle.exhibition;
    if (ex) return esc((team === 'P' ? ex.a : ex.b).name) + ':';
    return team === 'P' ? 'Your' : 'Enemy';
  }

  // A unit as the battle log names it.
  function logName(v) {
    // In a Hall of Fame match both armies are somebody's heroes: everyone goes by name.
    if (v.name && (v.team === 'P' || (UI.battle && UI.battle.exhibition))) return `${v.name} (${UNITS[v.type].name})`;
    return v.team === 'P' ? UNITS[v.type].name : `Enemy ${UNITS[v.type].name}`;
  }

  const SIT_OUT = { cooldown: 'cooling down', para: 'paralyzed', idle: 'nothing in reach' };
  // "Cass, Osric and Jarek pass (cooling down)." for units that passed in a row.
  function passLine(passes) {
    // "Enemy" once, and repeats counted: "Enemy Orc Warrior ×2 and Orc Shaman pass".
    const foe = passes.every(([n]) => n.startsWith('Enemy '));
    const counts = new Map();
    for (const [n] of passes) {
      const k = foe ? n.slice(6) : n;
      counts.set(k, (counts.get(k) || 0) + 1);
    }
    const names = [...counts].map(([n, c]) => esc(n) + (c > 1 ? ` ×${c}` : ''));
    const list = names.length === 1 ? names[0] : names.slice(0, -1).join(', ') + ' and ' + names[names.length - 1];
    const who = (foe ? 'Enemy ' : '') + list;
    const whys = [...new Set(passes.map(([, w]) => w))];
    const why = whys.length === 1 ? ` (${SIT_OUT[whys[0]]})` : '';
    return `<span class="muted">${who} ${passes.length === 1 ? 'passes' : 'pass'}${why}.</span>`;
  }

  // Turn a batch of engine events into battle log lines, newest first.
  function logEvents(ev) {
    const B = UI.battle;
    if (!B || !B.log) return;
    const s = B.s;
    const batch = (B.logBatch = (B.logBatch || 0) + 1);
    let line = null;
    const add = (l) => {
      B.log.unshift(l);
      B.log.length = Math.min(B.log.length, 30);
    };
    const finish = () => {
      if (!line) return;
      const v = s.byId[line.uid];
      const bits = [];
      if (line.act) bits.push(esc(line.act));
      else if (line.moved) bits.push('moves');
      if (line.dmg) bits.push(`<b>${line.dmg}</b> damage`);
      if (line.heal) bits.push(`<b>+${line.heal}</b> HP`);
      for (const n of line.notes) bits.push(esc(n));
      for (const k of line.kills) bits.push(`<span class="kill">${esc(k)} falls</span>`);
      if (bits.length) add({ team: v.team, html: `<b>${esc(logName(v))}</b>: ${bits.join(' · ')}` });
      line = null;
    };
    for (const e of ev) {
      const v = e.uid && s.byId[e.uid];
      if (e.t === 'move' || e.t === 'action') {
        if (!line || line.uid !== e.uid) {
          finish();
          line = { uid: e.uid, moved: false, act: null, dmg: 0, heal: 0, kills: [], notes: [] };
        }
        if (e.t === 'move') line.moved = true;
        else line.act = e.ai ? e.name : e.dmg ? 'basic attack' : 'basic ability';
      } else if (e.t === 'heal' && e.why === 'regen' && v) {
        finish();
        add({ team: v.team, html: `<span class="muted">${esc(logName(v))} regenerates ${e.amount} HP.</span>` });
      } else if ((e.t === 'dunk' || e.t === 'crash' || e.t === 'slam') && line && v) {
        // Where a shove or pull landed, on the line of the unit that did it.
        const o = e.other && s.byId[e.other];
        line.notes.push(
          e.t === 'dunk' ? `${logName(v)} ${e.lava ? 'into the lava' : 'into the water'}` : e.t === 'crash' ? `${logName(v)} crashes into ${o ? logName(o) : 'a unit'}` : `${logName(v)} slams into ${e.why === 'edge' ? 'the edge' : 'the rock'}`
        );
      } else if (e.t === 'resist' && e.status && line && v) {
        // A status shrugged off, on the line of the unit that tried it: why the poison did nothing.
        const note = `${logName(v)} immune to ${{ poison: 'poison', para: 'paralysis', root: 'roots' }[e.status]}${e.why ? ` (${e.why})` : ''}`;
        if (!line.notes.includes(note)) line.notes.push(note);
      } else if (e.t === 'summon' && e.raise && v) {
        // A slain foe rises as a skeleton for the side that slew it: say who did it, and why.
        const by = s.byId[e.by];
        finish();
        add({ team: v.team, html: `A <b>Skeleton</b> rises for ${v.team === 'P' ? 'your army' : 'the enemy'}: ${e.why === 'pact' ? `${by ? `<b>${esc(logName(by))}</b>'s ` : ''}Shadow Pact (a Level 3 Witch raises the first 2 foes she slays)` : "the Necromancer's Bell (1 in 3 slain foes rise)"}.` });
      } else if (e.t === 'channel' && v) {
        finish();
        add({ team: v.team, html: `<b>${esc(logName(v))}</b> calls down the <b>${esc(e.name)}</b>: the marked 3x3 is hit as its next turn starts. Get out of the way!` });
      } else if (e.t === 'fizzle' && v) {
        finish();
        add({ team: v.team, html: `<b>${esc(logName(v))}</b> falls: its meteor never comes.` });
      } else if (e.t === 'loot' && v) {
        finish();
        add({ team: v.team, html: `<b>${esc(logName(v))}</b> takes the ${esc(R.LOOT_NAMES[e.kind])}.` });
      } else if (e.t === 'dmg' && e.dmgType === 'fatigue' && v) {
        finish();
        const dead = !v.alive && ev.some((d) => d.t === 'death' && d.uid === v.uid);
        add({ team: v.team, fatigue: { uid: v.uid, amount: e.amount, dead }, html: `<span class="muted">${esc(logName(v))} loses ${e.amount} HP to fatigue.</span>${dead ? ` <span class="kill">${esc(logName(v))} falls</span>` : ''}` });
      } else if (e.t === 'dmg' && line && e.src === line.uid) line.dmg += e.amount || 0;
      else if (e.t === 'heal' && line && e.amount > 0) line.heal += e.amount;
      else if (e.t === 'death' && line && e.src === line.uid && v) line.kills.push(v.team === 'P' ? v.name : UNITS[v.type].name);
      else if (e.t === 'done') finish();
      else if (e.t === 'sitout' && v && v.team && SIT_OUT[e.why]) {
        finish();
        const last = B.log[0];
        // A unit that tired as its turn came and then passes: one line for both, so a run of
        // passes reads one unit at a time with each fatigue hit (15, 16, 17...).
        if (last && last.fatigue && last.fatigue.uid === v.uid) {
          last.html = `<span class="muted">${esc(logName(v))} passes (${SIT_OUT[e.why]}) and loses ${last.fatigue.amount} HP to fatigue.</span>`;
          last.fatigue = null;
          continue;
        }
        // Several units passing in a row make one line, not one each.
        if (last && last.passes && last.team === v.team && last.batch === batch) {
          last.passes.push([logName(v), e.why]);
          last.html = passLine(last.passes);
        } else {
          const passes = [[logName(v), e.why]];
          add({ team: v.team, passes, batch, html: passLine(passes) });
        }
      } else if (e.t === 'routed') {
        finish();
        const was = e.was || {};
        const on = [!was.E && 'the enemy', !was.P && 'your army'].filter(Boolean);
        add({ team: 'O', html: `<b class="overtime">Mission done: the win is yours!</b> ${on.length ? `${on.length > 1 ? 'Both sides\' fatigue switches on, each' : `Fatigue switches on for ${on[0]}`} from 1: each unit loses HP as its turn comes, passing or not, one more every time its side takes a turn.` : ''}${was.E || was.P ? ` ${was.E && was.P ? 'Both sides were' : was.E ? 'The enemy was' : 'Your army was'} already tiring and carr${was.E && was.P ? 'y' : 'ies'} on as before.` : ''} The battle goes on, reinforcements and all: grab what else you can (gold, loot, an ambush bonus) before fatigue wears your army down (it cannot cost you the win), or tap Finish now.` });
      } else if (e.t === 'cleanup') {
        finish();
        add({ team: 'O', html: `<b class="overtime">The enemy army is beaten: the win is yours.</b> Your army collects what is left (${e.left}), ${e.was ? `its fatigue still counting on (next −${e.next})` : 'but its fatigue sets in now: each of your units loses HP as its turn comes, passing or not, 1, then 2, 3 and so on'}, one more every time one of your units takes its turn. It goes on until everything is collected or your army has fallen.` });
      } else if (e.t === 'overtime') {
        finish();
        const was = e.was || {};
        if (!was.E && !was.P) add({ team: 'O', html: `<b class="overtime">Fatigue triggered!</b> Each side's fatigue starts at 1: one unit at a time, as its turn comes (passing or not), a unit loses its side's next number, one more every time that side takes a turn.` });
        else if (was.E && was.P) add({ team: 'O', html: `<b class="overtime">Turn ${e.turn}: fatigue for everyone.</b> Both sides already tire, so nothing changes.` });
        else add({ team: 'O', html: `<b class="overtime">Turn ${e.turn}: fatigue for everyone.</b> ${was.E ? 'Your army' : 'The enemy'} now tires too, from 1. ${was.E ? 'The enemy\'s' : 'Yours'} carries on as before.` });
      } else if (e.t === 'pass' && !e.auto && e.uid && s.byId[e.uid]) {
        finish();
        add({ team: e.side, html: `<span class="muted">${esc(logName(s.byId[e.uid]))} holds its ground.</span>` });
      }
    }
    finish();
  }

  // Whose turns come next, both sides interleaved as their turns alternate. Every unit
  // shows: one cooling down (the number is its cooldown) or paralyzed passes its turn when
  // it comes, and the next in line acts.
  function queueHTML(s, n) {
    const a = E.upcoming(s, s.side, n);
    const b = E.upcoming(s, E.other(s.side), n);
    const items = [];
    for (let i = 0; i < n; i++) {
      for (const x of [a[i], b[i]]) {
        if (!x) continue;
        for (const p of x.passes) if (s.byId[p.uid] && items.length < n) items.push(p);
        if (x.uid && s.byId[x.uid] && items.length < n) items.push(x);
      }
    }
    let now = false;
    return `<div class="queue">${items
      .map((x) => {
        const v = s.byId[x.uid];
        const name = esc(v.team === 'P' ? v.name : UNITS[v.type].name);
        const tag = !x.why ? '' : x.why === 'cooldown' ? `<b class="q-cd" title="Cooling down: passes this turn">${x.wait}</b>` : x.why === 'para' ? `<b class="q-cd para" title="Paralyzed: passes this turn">${x.para}</b>` : '';
        const tip = x.why === 'cooldown' ? ` · cooling down (${x.wait}): passes this turn` : x.why === 'para' ? ' · paralyzed: passes this turn' : x.why ? ' · never acts: passes every turn' : '';
        const cls = x.why ? 'pass' : now ? '' : 'now';
        if (!x.why) now = true;
        return `<div class="q-item team-${v.team} ${cls}" title="${esc(logName(v))} · Speed ${v.spd}${tip}"><canvas class="portrait" data-p="${v.type}:${v.team}"></canvas>${tag}<span>${name}</span></div>`;
      })
      .join('')}</div>`;
  }

  // While your army fights on its own: who is acting, who is next, what just happened.
  // An enemy unit or building your army could be told to go after.
  // The enemy a mission asks you to kill, if `u` is it: 'Commander' (the crowned one) or
  // 'boss'. Null for anyone else.
  function missionTarget(u) {
    return u && u.team === 'E' && u.vip && u.alive !== false ? (UNITS[u.type].boss ? 'boss' : 'Commander') : null;
  }

  // What the priority is called: the Commander says so, so you know you picked the right one.
  function focusName(u) {
    return missionTarget(u) === 'Commander' ? `the Commander (${UNITS[u.type].name})` : `the ${UNITS[u.type].name}`;
  }

  const vipBadge = (t) => `<span class="vip-badge">${ic('crown')} ${t === 'boss' ? 'Boss' : 'Commander'}</span>`;
  // On the priority line, which already names it: a check that it is the right one.
  const vipCheck = `<span class="vip-badge">${ic('check')} Mission target</span>`;

  // Under Priority, for an enemy you are looking at: it is the mission's target (crowned
  // badge, and a check once it is the priority), or it is not and the target is elsewhere.
  function vipNote(s, u, isFocus) {
    const t = missionTarget(u);
    if (t)
      return `<p class="vip-note">${ic(isFocus ? 'check' : 'crown')}<span>${isFocus ? `<b>Confirmed:</b> your army's priority is the ${t === 'boss' ? 'boss' : '<b>Commander</b>'}, the mission's target.` : `This is the ${t === 'boss' ? 'boss' : '<b>Commander</b>, the crowned one'}: ${t === 'boss' ? 'slay it' : 'kill it'} and the mission is won.`}</span></p>`;
    if (u.bounty || u.team !== 'E') return '';
    const vip = s.units.find((v) => missionTarget(v) === 'Commander');
    return vip ? `<p class="vip-note not">${ic('help')}<span>Not the Commander. The Commander is the crowned ${esc(UNITS[vip.type].name)}${vip.type === u.type ? ' (another one)' : ''}.</span></p>` : '';
  }

  // What the army does about a priority, for the lines that name it.
  function focusVerb(f) {
    if (f.ally || f.kind === 'ally') return 'gathers around them, wherever they go';
    if (f.tile || f.kind === 'tile') return 'gathers there and holds';
    if (f.hold || f.kind === 'hold') return 'takes the shrine and holds it';
    return 'goes all out for it';
  }

  // The shrine a battle asks you to hold.
  function isShrine(s, x, y) {
    return !!(s.hold && s.hold.x === x && s.hold.y === y);
  }

  // Ground a unit could stand on, with nothing on it now.
  function isOpenGround(s, x, y) {
    return s.terrain[E.idx(s, x, y)] === E.T_GRASS && !E.at(s, x, y);
  }

  // A boulder (a tree, a basalt spire): nobody stands on it, but the army can gather round it.
  function isObstacle(s, x, y) {
    return s.terrain[E.idx(s, x, y)] === E.T_ROCK;
  }

  function obstacleName() {
    return OBSTACLE_NAME[(UI.board && UI.board.palette.obstacle) || 'rock'] || 'Boulder';
  }

  // A summoned shrub: a priority on it is a spot to gather at, not something to cut down.
  function isShrub(u) {
    return !!u && u.type === 'shrub';
  }

  // A spot the army can gather at: open ground or a boulder.
  function isRallySpot(s, x, y) {
    return isOpenGround(s, x, y) || isObstacle(s, x, y);
  }

  // A tile that can be a priority: loot lying there, the shrine, open ground or a boulder.
  function tileFocusable(s, t) {
    return !!(t && (E.lootAt(s, t.x, t.y) || isShrine(s, t.x, t.y) || isRallySpot(s, t.x, t.y)));
  }

  function tileIsFocus(B, t) {
    const f = B.focus;
    if (!f || !t) return false;
    if (f.hold) return isShrine(B.s, t.x, t.y);
    if (f.tile) return f.x === t.x && f.y === t.y;
    const l = E.lootAt(B.s, t.x, t.y);
    return !!(l && f.loot === l.id);
  }

  // An enemy to go all out for, or one of your own units to rally on.
  function canFocusUnit(B, u) {
    return !B.s.over && u.alive && (isShrub(u) || (focusable(u) && !(u.team === 'P' && u.nonCombat)));
  }

  // Walls, rocks and kegs are never a priority; a barricade with gold inside is.
  function focusable(u) {
    return !u.traits.has('scenery') || u.bounty > 0;
  }

  const NO_HALL_FOCUS = 'Priority is off in Hall of Fame matches. Whichever army you steered would almost always win, and the ranking would mean nothing. Both armies fight on their own.';

  // Make this your army's priority, or stop, while watching an auto battle. In a Hall of
  // Fame match it shows, crossed out: priority is banned there, on purpose.
  function focusButton(B, can, is, u) {
    if (!can || B.s.over) return '';
    if (B.exhibition) return `<button class="btn banned" id="btNoFocus" aria-label="Priority is off in Hall of Fame matches"><span class="ban-label">${ic('target')} Priority</span><span class="ban-badge">${ic('close')}</span></button>`;
    return is
      ? `<button class="btn" id="btUnfocus">${ic('close')} Clear priority</button>`
      : `<button class="btn primary" id="btFocus">${ic('target')} Priority${missionTarget(u) ? ' ' + vipBadge(missionTarget(u)) : ''}</button>`;
  }

  function autoPanelHTML(B) {
    const s = B.s;
    const actor = B.acting && s.byId[B.acting];
    return `${actor && actor.alive ? unitInfoHTML(actor, { status: true }) : ''}
      <div class="eyebrow">Turn order</div>
      ${queueHTML(s, 10)}
      ${B.log.length ? `<ul class="blog">${B.log.slice(0, 4).map((l) => `<li class="team-${l.team}">${l.html}</li>`).join('')}</ul>` : ''}
      ${s.won && !s.over ? `<div class="hint">${ic('check')} <b>${s.cleanup ? 'The enemy army is beaten' : 'Mission done'}: the win is yours.</b> ${s.cleanup ? `Your army is collecting what is left (${E.cleanupLeft(s)}): buildings with gold or a goal in them, and loot.` : 'The battle goes on while your army grabs what else it can, and every enemy it cuts down still earns a gold or two.'} Its fatigue is on (next −${E.fatigueHit(s, 'P')}, one more every turn it takes), but it cannot cost you the battle.</div><div class="actions"><button class="btn" id="btFinish">${ic('check')} Finish now</button></div>` : ''}
      ${B.focus ? `<div class="focusline">${ic('target')}<span>Priority: <b>${esc(B.focus.label)}</b>${B.focus.uid && missionTarget(s.byId[B.focus.uid]) ? ' ' + vipCheck : ''}. Your army ${focusVerb(B.focus)}.</span><button class="btn" id="btUnfocus">Clear</button></div>` : ''}
      <div class="eyebrow">Mission details</div>
      ${objectivesHTML(B.enc, s)}
      ${B.paused ? `<div class="actions"><button class="btn primary" id="btPause">${ic('play')} Resume</button></div>` : ''}
      <p class="small muted">${B.exhibition ? `Tap a unit to look at it while the battle plays on. <b>Priority is off</b> in Hall of Fame matches: both armies fight on their own.` : 'Tap a unit or a chest to look at it while the battle plays on, and make it your army\'s <b>Priority</b>.'} ${ic('pause')} pauses, ${ic('fast')} changes the speed.</p>`;
  }

  function renderBattle() {
    const B = UI.battle;
    if (!B) return;
    const s = B.s;
    const b = UI.board;
    const ov = {};
    b.activeSide = s.side === 'P' && !B.busy ? 'P' : null;
    b.readySet = new Set(usefulReady(s).map((x) => x.uid));
    b.focus = focusSpot(B);
    const u = B.sel ? s.byId[B.sel] : null;
    const A = u ? activationOf(u) : null;
    let panel = '';
    const auto = UI.prefs.autoBattle || !!B.exhibition;
    const endBtn = (primary) =>
      auto ? '' : `<button class="btn ${primary ? 'primary' : ''}" id="btEnd" ${s.side !== 'P' || B.busy ? 'disabled' : ''}>${B.confirmEnd ? 'Confirm pass' : 'Pass'}</button>`;
    const inProgress = !!(s.act && (s.act.moved || s.act.acted));
    const tileF = B.mode === 'tile' && B.tile ? tileFacts(s, B.tile.x, B.tile.y, B.enc) : null;
    if (B.mode === 'tile' && !tileF) B.mode = 'idle';

    // Watching an auto battle, the panel follows the fight unless you tapped a unit or a
    // tile to look at (the battle plays on meanwhile).
    if (auto && !((B.mode === 'inspect' && u && u.alive) || (B.mode === 'tile' && tileF))) {
      panel = autoPanelHTML(B);
      if (B.acting && s.byId[B.acting]) ov.select = [s.byId[B.acting].x, s.byId[B.acting].y];
    } else if (!auto && (s.side !== 'P' || B.busy)) {
      const actor = B.acting && s.byId[B.acting];
      panel = actor && actor.alive
        ? `${unitInfoHTML(actor, { status: true })}<div class="hint">Enemy turn: their ${esc(UNITS[actor.type].name)}. Your turn comes next.</div>`
        : `<div class="hint">${s.side === 'P' ? 'Resolving…' : 'The enemy is choosing a unit. The fast-forward button speeds things up.'}</div>`;
    } else if (B.mode === 'unit' && u) {
      const moved = A && A.moved;
      const acted = A && A.acted;
      const faced = A && A.face != null;
      if (!moved) ov.move = [...E.reachable(s, u).values()].filter((r) => r.d > 0).map((r) => [r.x, r.y]);
      const main = acted ? [] : E.actUsable(s, u, 0) ? E.targetsFrom(s, u, 0) : [];
      if (!acted && directKinds(u.act.kind)) ov.targets = main.map((t) => [t.x, t.y]);
      ov.select = [u.x, u.y];
      const anyTargets = E.allTargets(s, u).length > 0;
      const keep = faced ? ' It ends its turn facing the way you set.' : '';
      let hint;
      if (!moved && !acted) hint = faced ? 'Facing set. Move, act, or tap Done to end its turn here.' : `Tap a blue tile to move${main.length && directKinds(u.act.kind) ? ', a red enemy to attack' : ''}, or choose an action below.`;
      else if (moved && !acted) hint = (anyTargets ? 'Moved. Choose an action, or tap Done.' : 'Moved. Nothing in reach from here. Tap Done.') + keep;
      else if (moreToDo(s, u)) hint = 'Action used. You may still move, or tap Done.' + keep;
      else hint = `Action used. Tap Done to end its turn${faced ? ' facing the way you set' : UI.prefs.manualFacing ? ' and pick a facing' : ': it turns to the nearest enemy'}, or Face to ${faced ? 'change the facing' : 'pick the facing yourself'}.`;
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
          ${moved || acted || faced ? `<button class="btn" id="btDone">${ic('check')} Done</button>` : ''}
          ${u.facing >= 0 ? `<button class="btn" id="btFace">${ic('rotate')} Face</button>` : ''}
          ${E.canUndo(s) && moved ? `<button class="btn" id="btUndo">${ic('undo')} Undo move</button>` : ''}
          <button class="btn icon-only" id="btInfo" aria-label="Details">${ic('help')}</button>
          <button class="btn ghost icon-only" id="btDesel" aria-label="Deselect">${ic('close')}</button>
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
          ${B.mode === 'confirm' ? `<button class="btn primary" id="btConfirm">${ic('check')} ${esc(actLabel(act, B.ai))}</button>` : ''}
          <button class="btn" id="btCancel">Cancel</button>
        </div>
        ${B.mode === 'confirm' ? '<p class="small muted">Tap the target again, or the button, to confirm.</p>' : ''}`;
    } else if (B.mode === 'facing' && u) {
      ov.select = [u.x, u.y];
      ov.facing = { x: u.x, y: u.y, current: B.facing };
      panel = `${unitInfoHTML(u, { status: true })}
        <div class="hint">${B.facePlan ? `Tap an arrow to choose where ${esc(u.name)} faces when its turn ends.` : `Choose where ${esc(u.name)} faces: tap an arrow.`} The front blocks best, the sides half as well, the back never.</div>
        <div class="actions"><button class="btn primary" id="btKeep">${ic('check')} ${B.facePlan ? 'Set facing' : 'Confirm facing'}</button>${B.faceBack ? '<button class="btn" id="btFaceBack">Back</button>' : ''}</div>`;
    } else if (B.mode === 'inspect' && u && u.alive) {
      const th = AI.unitThreat(s, u);
      ov.range = th.hit;
      ov.move = th.move.filter(([x, y]) => x !== u.x || y !== u.y);
      ov.select = [u.x, u.y];
      // Watching, the buttons come first so Priority is in view without scrolling.
      const watchBtns = auto
        ? `<div class="actions">${focusButton(B, canFocusUnit(B, u), B.focus && (B.focus.uid === u.uid || B.focus.ally === u.uid || (isShrub(u) && B.focus.tile && B.focus.x === u.x && B.focus.y === u.y)), u)}${B.paused ? `<button class="btn ${canFocusUnit(B, u) ? '' : 'primary'}" id="btPause">${ic('play')} Resume</button>` : ''}<button class="btn" id="btInfo">${ic('help')} Details</button><button class="btn ghost icon-only" id="btDesel" aria-label="Close">${ic('close')}</button></div>${canFocusUnit(B, u) && !B.exhibition ? vipNote(s, u, !!(B.focus && B.focus.uid === u.uid)) : ''}`
        : '';
      panel = `${unitInfoHTML(u, { status: true })}${watchBtns}${behindHint(s, u.uid)}${statsHTML(u)}${underfootHTML(s, u, B.enc)}
        ${u.bounty ? '' : actsHTML(u)}
        <div class="hint">${
          u.bounty
            ? `${ic('gold')} ${esc(UNITS[u.type].desc)} It holds <b>${u.bounty} gold</b> for your army, paid with the battle's gold when you win.${canFocusUnit(B, u) ? ' Make it the Priority and your whole army goes to break it.' : ''}`
            : isShrub(u)
            ? `${esc(UNITS[u.type].desc)} Make it the Priority and your army gathers around it and holds there.`
            : u.team === 'E'
            ? `Blue: where it can move. Red: everywhere it could hit when it next acts${u.wait > 0 ? ` (cooling down: it passes its next ${u.wait === 1 ? 'turn' : u.wait + ' turns'})` : ''}.`
            : inProgress && s.act.uid !== u.uid
              ? `${esc(s.byId[s.act.uid].name)} is mid-turn. Finish it first: one unit a turn.`
              : u.wait > 0
                ? `Cooling down: it passes its next ${u.wait === 1 ? 'turn' : u.wait + ' turns'}, losing 1 off its cooldown each time.`
                : u.para > 0
                  ? `Paralyzed: it passes its next ${u.para === 1 ? 'turn' : u.para + ' turns'}.`
                  : 'Cannot act right now.'
        }</div>
        ${auto
          ? ''
          : `<div class="actions">${s.act && s.act.uid !== u.uid ? `<button class="btn primary" id="btBack">Back to ${esc(s.byId[s.act.uid].name)}</button>` : ''}<button class="btn" id="btInfo">${ic('help')} Details</button>${s.act ? '' : `<button class="btn ghost" id="btDesel">${ic('close')}</button>${endBtn(false)}`}</div>`}`;
    } else if (B.mode === 'tile') {
      ov.select = [B.tile.x, B.tile.y];
      if (tileF.zone) ov.range = tileF.zone;
      panel = `${tileInfoHTML(tileF)}
        <div class="actions">${auto ? `${focusButton(B, tileFocusable(s, B.tile), tileIsFocus(B, B.tile))}${B.paused ? `<button class="btn ${tileFocusable(s, B.tile) ? '' : 'primary'}" id="btPause">${ic('play')} Resume</button>` : ''}` : ''}<button class="btn ghost" id="btDesel">${ic('close')}</button>${endBtn(false)}</div>`;
    } else {
      B.mode = 'idle';
      const ready = usefulReady(s);
      panel = `<div class="hint">${
        ready.length
          ? `${esc(ready[0].name)}'s turn (units go in speed order): tap it to move, act, or both. Long-press any unit for details.`
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
    B.goalLine = goal;
    const sideName = B.exhibition ? (s.side === 'P' ? B.exhibition.a.name : B.exhibition.b.name) : s.side === 'P' ? 'Your turn' : 'Enemy turn';
    $('#topbar').innerHTML = `<div class="title"><b>${B.paused && auto ? 'Paused' : esc(sideName)}</b>
      <span>${turnLine(s)} · ${esc(goal)}</span></div>
      ${s.side === 'P' && !B.busy && B.mode !== 'idle' && !inProgress ? endBtn(false) : ''}
      <button class="btn icon-only speedbtn ${speedOf() > 1 ? 'on' : ''}" id="btFast" aria-label="Battle speed: ${speedOf()}x">${ic('fast')}<small>${speedOf()}×</small></button>
      ${auto ? `<button class="btn icon-only ${B.paused ? 'on' : ''}" id="btPauseT" aria-label="${B.paused ? 'Resume' : 'Pause'}">${ic(B.paused ? 'play' : 'pause')}</button>` : ''}
      <button class="btn icon-only" id="btMenu" aria-label="Menu">${ic('menu')}</button>`;
    const ex = B.exhibition;
    supplyBadges({
      P: Object.assign({ label: ex ? ex.a.name || ex.a : 'Your army' }, battleSupply(s, 'P')),
      E: Object.assign({ label: ex ? ex.b.name || ex.b : 'Enemy' }, battleSupply(s, 'E')),
    });
    $('#cmd').innerHTML = goalBarHTML(B) + panel;
    // A new view (a unit or tile tapped, or back to the fight) starts at the top, under the
    // goals, not wherever the last one was scrolled to.
    const view = `${B.mode}:${B.sel || ''}:${B.tile ? B.tile.x + ',' + B.tile.y : ''}`;
    if (view !== B.view) $('#cmd').scrollTop = 0;
    B.view = view;
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
      if (e.frenzy) bits.push('frenzy (+25% damage)');
      if (e.rally) bits.push(v.wait > 0 ? `cooldown ${v.wait} → ${v.wait - 1}` : 'rallied');
      if (e.para) bits.push(e.para === 'resist' ? 'immune to paralysis' : `paralyzed ${e.para}`);
      if (e.poison) bits.push(e.poison === 'resist' ? 'immune to poison' : `poison ${e.poison.dmg}×${e.poison.turns}`);
      if (e.burn) bits.push(`burn ${e.burn.dmg}×${e.burn.turns}`);
      if (e.root) bits.push(e.root === 'resist' ? 'cannot be rooted' : `rooted ${e.root}`);
      if (e.weak) bits.push(`weakened ${e.weak}`);
      if (e.mark) bits.push(`marked ${e.mark}`);
      if (e.knock) bits.push(shoveText(e.knock));
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
    // Watching an auto battle: pause, resume, or jump to the result.
    on('btPause', () => togglePause(B));
    on('btFinish', () => finishCleanup());
    on('btPauseT', () => togglePause(B));
    on('btFast', toggleSpeed);
    on('btFocus', () => setFocus(B));
    on('btNoFocus', () => toast(NO_HALL_FOCUS, 4500));
    on('btUnfocus', () => clearFocus(B));
    on('btUndo', async () => {
      if (B.busy) return;
      E.undoMove(s);
      await play();
      renderBattle();
    });
    on('btDone', () => enterFacing());
    // Face: pick by hand where the unit ends up facing, before or after it moves and acts.
    on('btFace', () => {
      if (!E.beginActivation(s, B.sel)) return;
      enterFacing(true);
    });
    on('btFaceBack', () => {
      B.mode = 'unit';
      renderBattle();
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
    on('btKeep', () => chooseFacing(B.facing));
    on('btInfo', () => battleUnitSheet(s.byId[B.sel], true));
    on('btBack', () => s.act && selectUnit(s.byId[s.act.uid]));
    for (const c of $$('#cmd .rcard[data-uid]')) c.onclick = () => selectUnit(s.byId[+c.dataset.uid]);
  }

  async function play(keepBusy) {
    const B = UI.battle;
    if (!B) return;
    B.busy = true;
    UI.board.activeSide = null;
    const ev = E.drainEvents(B.s);
    logEvents(ev);
    // Just a banner, nothing to tap away: the battle log has the details.
    const routedEv = ev.find((e) => e.t === 'routed');
    if (routedEv) showBanner('Mission done: you win!', false);
    const ot = ev.find((e) => e.t === 'overtime');
    const otWas = (ot && ot.was) || {};
    if (ot && !otWas.E && !otWas.P) showBanner('Fatigue triggered!', true);
    else if (ot && (!otWas.E || !otWas.P)) showBanner(otWas.E ? 'Your army tires too!' : 'Enemy tires too!', true);
    if (ev.some((e) => e.t === 'cleanup')) showBanner('Army beaten!', false);
    // The top bar catches up with the banner at once, not after the moves play out.
    const line = (routedEv || ev.some((e) => e.t === 'overtime' || e.t === 'cleanup')) && $('#topbar .title span');
    if (line) line.innerHTML = `${turnLine(B.s)} · ${esc(B.goalLine || '')}`;
    await UI.board.playEvents(ev, B.s);
    UI.board.syncFromState(B.s);
    // Your own passes need no news; the enemy's, and turns you had to skip, do.
    // The battle log tells of passes in an auto battle; by hand, a toast does.
    const passes = B.s.over || UI.prefs.autoBattle ? [] : ev.filter((e) => e.t === 'pass' && (e.side === 'E' || e.auto));
    if (passes.length) {
      const mine = passes.filter((e) => e.side === 'P').length;
      toast(mine ? `None of your units could act, so your turn passed${mine > 1 ? ' ' + mine + ' times' : ''}.` : 'The enemy passes.');
      await pause(600);
    }
    if (!keepBusy) B.busy = false;
  }

  // After every move: the battle may be over, or the enemy may be up.
  async function nextMove() {
    const B = UI.battle;
    if (!B) return;
    const s = B.s;
    if (s.over) return battleOver();
    if (s.side === 'E' || UI.prefs.autoBattle) return runBattle();
    B.mode = 'idle';
    B.sel = null;
    renderBattle();
  }

  async function deselect() {
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
    // A facing set for a turn that never happened turns back.
    if (s.events.length) await play();
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
    if (act && act.uid !== v.uid && !inProgress) {
      E.cancelActivation(s);
      if (s.events.length) await play();
    }
    B.sel = v.uid;
    B.target = null;
    B.ai = 0;
    B.confirmEnd = false;
    // One unit a turn: once it has moved or acted, the others can only be looked at.
    B.mode = (s.act && s.act.uid === v.uid) || (ownReady && !inProgress) ? 'unit' : 'inspect';
    // Zoomed in, the view only moves if the unit is off screen.
    UI.board.ensureVisible(v.x, v.y);
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
    if (!B || B.s.over) return;
    if (UI.prefs.autoBattle) return watchTap(B, hit);
    if (B.busy) return;
    const s = B.s;
    if (s.side !== 'P') return;
    const u = B.sel ? s.byId[B.sel] : null;
    if (B.mode === 'facing' && u) {
      const d = UI.board.facingFromHit(hit, u.x, u.y);
      if (d >= 0) chooseFacing(d);
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
          if (A && (A.moved || A.acted || A.face != null)) enterFacing();
          else deselect();
          return;
        }
        return selectUnit(other);
      }
      // 4. A near miss: snap to the closest legal move. Anywhere else, the unit stays
      // picked (the ✕ lets it go).
      const m = snap({ px: hit.px, py: hit.py, tile: null, unitTile: null }, moves);
      if (m) return doMove(m.x, m.y);
      return;
    }
    const other = pickAt(hit, s);
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

  // Watching an auto battle: pause or resume, or jump to the result.
  function togglePause(B) {
    if (!B || B.s.over) return;
    B.paused = !B.paused;
    if (!B.paused) {
      B.mode = 'idle';
      B.sel = null;
      B.tile = null;
    }
    sfx('click');
    renderBattle();
    if (!B.paused && !B.running) runBattle();
  }

  // While your army fights on its own, a tap shows what is there without stopping the
  // battle: Priority works on the move. The pause button stops it.
  function watchTap(B, hit) {
    const s = B.s;
    const v = pickAt(hit, s);
    let spot = v ? null : featureAt(hit, s, B.enc);
    // The same tile again: close it, like a tap beside the board.
    if (spot && B.mode === 'tile' && B.tile && B.tile.x === spot.x && B.tile.y === spot.y) spot = null;
    if (v || spot) {
      B.sel = v ? v.uid : null;
      B.mode = v ? 'inspect' : 'tile';
      B.tile = spot;
      sfx('select');
    } else if (B.mode !== 'idle') {
      B.mode = 'idle';
      B.sel = null;
      B.tile = null;
    } else return;
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
    // The turn waits for Done (or Face), even when there is nothing left to do.
    B.mode = 'unit';
    renderBattle();
  }

  // Whether the selected unit could still move or act this turn.
  function moreToDo(s, u) {
    const A = activationOf(u);
    const canMove = !(A && A.moved) && u.move > 0 && !u.traits.has('immobile') && E.reachable(s, u).size > 1;
    const canAct = !(A && A.acted) && E.allTargets(s, u).length > 0;
    return canMove || canAct;
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

  // The unit is done: it keeps a facing set with Face, or turns toward the nearest enemy
  // on its own, unless the player picks it now (Face, or manual facing in the menu).
  function enterFacing(manual) {
    const B = UI.battle;
    const s = B.s;
    const u = s.byId[B.sel];
    if (!u) return;
    if (u.facing < 0) {
      finishUnit(-1);
      return;
    }
    const A = activationOf(u);
    const set = A && A.face != null ? A.face : null;
    if (!manual && set != null) {
      finishUnit(set);
      return;
    }
    if (!manual && !UI.prefs.manualFacing) {
      finishUnit(AI.nearestFacing(s, u));
      return;
    }
    B.mode = 'facing';
    // From the Face button: a unit with more to do keeps going after the pick.
    B.faceBack = !!manual;
    B.facePlan = !!manual && moreToDo(s, u);
    B.facing = set != null ? set : AI.smartFacing(s, u);
    renderBattle();
  }

  // A facing picked mid-turn turns the unit now and holds when the turn ends; otherwise
  // the pick ends the turn.
  async function chooseFacing(d) {
    const B = UI.battle;
    if (!B.facePlan) return finishUnit(d);
    if (B.busy || !E.turnUnit(B.s, B.sel, d)) return;
    B.mode = 'unit';
    sfx('click');
    await play();
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
  // Mid-cleanup: stop collecting and take the win now.
  async function finishCleanup() {
    const B = UI.battle;
    if (!B || !B.s.won || B.s.over) return;
    // Let the unit in motion finish first.
    B.paused = true;
    for (let i = 0; i < 100 && B.busy && UI.battle === B; i++) await sleep(50);
    if (UI.battle !== B || B.s.over) return;
    E.endCleanup(B.s);
    E.drainEvents(B.s);
    battleOver();
  }

  async function battleOver() {
    const B = UI.battle;
    if (!B || B.ending) return;
    B.ending = true;
    B.busy = true;
    UI.board.focus = null;
    music(null); // quiet for the victory or defeat fanfare
    const s = B.s;
    if (B.exhibition) return exhibitionOver(B);
    const won = s.winner === 'P';
    const endEv = s.end;
    showBanner(won ? 'Victory' : 'Defeat', !won);
    sfx(won ? 'victory' : 'defeat');
    renderBattle();
    await sleep(1500);
    // Every win pauses here, with the run as it was before the rewards, so it can be fought
    // again (for a bonus goal missed, more gold, the loot left behind).
    const goals = won ? R.goalResults(UI.run, s, B.dep) : [];
    const before = won ? R.snapshot(UI.run) : null;
    const haul = won ? haulOf(s, B.enc) : null;
    const res = R.finishBattle(UI.run, s, B.dep);
    UI.battle = null;
    if (won) return victorySheet(goals, before, haul);
    const reason = s.timeout
      ? 'The turn limit ran out and the enemy held stronger.'
      : endEv && endEv.forfeit
        ? 'You sounded the retreat.'
        : 'Your army was broken.';
    // The final challenge: try it again, as often as you like, or call it a day.
    if (UI.run.pending && UI.run.pending.tier === 'mega') return megaDefeat(reason);
    // A battle an event started is fought again from the war room; a challenge sends you
    // back to the round's choice, where it is still on offer beside the others.
    const fromEvent = UI.run.pending && UI.run.pending.fromEvent;
    const again = () => {
      if (fromEvent) return warRoom();
      R.backToChoice(UI.run);
      route();
    };
    openSheet(
      `${sheetHead('Defeat')}
      <p>${reason} The enemy holds the field, but your campaign goes on: there is no limit on retries.</p>
      <p class="muted">${fromEvent ? 'Re-plan your army against the same enemy.' : 'Back to the choice of battles: try this one again with a new plan, or pick another, maybe an easier one.'} Swap units, change levels and abilities, move your archers back, bring the counter they fear.</p>
      <div class="actions"><button class="btn" id="dfTitle">Main menu</button><button class="btn primary" id="dfRetry">${ic('swords')} ${fromEvent ? 'Re-plan and fight' : 'Back to the battles'}</button></div>`,
      (sh) => {
        $('#dfRetry', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          again();
        };
        $('#dfTitle', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          if (!fromEvent) R.backToChoice(UI.run);
          title();
        };
      }
    );
    UI.onSheetClose = again;
    void res;
  }

  // A Hall of Fame match is over: say who won, then back to the Hall.
  async function exhibitionOver(B) {
    const { a, b, onDone, onResult } = B.exhibition;
    const winner = B.s.winner === 'P' ? a : b;
    // Saved as soon as the match ends, so closing the app here keeps the result.
    const note = onResult ? onResult(B.s.winner) : '';
    showBanner(`${winner.name} wins`, B.s.winner !== 'P');
    sfx('victory');
    renderBattle();
    await sleep(1500);
    UI.battle = null;
    openSheet(
      `${sheetHead('Match over')}
      <p><b>${esc(winner.name)}</b> ${B.s.timeout ? 'held the stronger army when time ran out' : 'is the last army standing'}.</p>
      ${note ? `<div class="panel hall-log"><div>${note}</div></div>` : ''}
      <div class="actions"><button class="btn primary" id="exGo" data-close>Back to the Hall</button></div>`
    );
    UI.onSheetClose = () => onDone(B.s.winner);
  }

  // Lost to the final challenge. Try again goes straight back to the War Room with the same
  // plan; calling it a day ends the (already won) campaign, with a choice of which army the
  // Hall of Fame keeps.
  function megaDefeat(reason) {
    const run = UI.run;
    const i = run.pending.offerIndex || 0;
    const tries = run.pending.attempt || 1;
    const toChoice = () => {
      R.backToChoice(run);
      route();
    };
    openSheet(
      `${sheetHead('Defeat')}
      <p>${reason} The final challenge still stands, after ${tries} ${tries === 1 ? 'try' : 'tries'}. It is not meant to be beaten: try again as often as you like, with any plan.</p>
      <p class="muted">Your campaign is already won, and the army that just fought here has taken its place in the Hall of Fame. Whatever you try last is the one it keeps.</p>
      <div class="actions"><button class="btn" id="mdClaim">${ic('crown')} Call it a day</button><button class="btn primary" id="mdRetry">${ic('swords')} Try again</button></div>`,
      (sh) => {
        $('#mdRetry', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          R.backToChoice(run);
          R.chooseChallenge(run, i);
          sfx('select');
          route();
        };
        $('#mdClaim', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          R.backToChoice(run);
          claimSheet(run);
        };
      }
    );
    UI.onSheetClose = toChoice;
  }

  // Watch two Hall of Fame armies fight it out, both on the AI. onDone gets 'P' (a won) or
  // 'E' (b won); onLeave runs when you walk out before the end. onResult, if given, runs the
  // moment the match ends and returns a line for the result sheet.
  async function startExhibition(a, b, onDone, onLeave, onResult) {
    hideToast();
    music('battle');
    const cfg = R.hallBattleConfig(a, b, ((Math.random() * 2 ** 31) >>> 0) + 1);
    const s = E.createBattle(cfg);
    E.drainEvents(s);
    const enc = { name: `${a.name} vs ${b.name}`, w: cfg.w, h: cfg.h, terrain: cfg.terrain, units: [], bonus: [], loot: [], kind: 'battle', primary: 'rout', stance: 'balanced', exhibition: { a: a.name, b: b.name } };
    const bd = showBattleLayout();
    clearBanner();
    bd.clearUnits();
    bd.ov = {};
    bd.zoom = 1;
    bd.panX = 0;
    bd.panY = 0;
    bd.readySet = null;
    bd.setBoard(cfg.w, cfg.h, cfg.terrain, 'grass');
    UI.wr = null;
    UI.battle = { s, dep: [], enc, mode: 'idle', sel: null, target: null, ai: 0, busy: false, temp: 0.3, confirmEnd: false, exhibition: { a, b, onDone, onLeave: onLeave || (() => onDone(null)), onResult }, log: [] };
    bd.speed = paceOf();
    bd.focus = null;
    bd.syncFromState(s);
    bd.setObjectives([], null);
    bd.activeSide = 'P';
    UI.boardTap = btTap;
    UI.boardLong = btLong;
    UI.boardDragMove = UI.boardDragEnd = null;
    battleTools();
    showBanner(`${a.name} vs ${b.name}`, false);
    renderBattle();
    UI.battle.busy = true;
    await pause(900);
    if (UI.battle && UI.battle.s === s) await runBattle();
  }

  // ------------------------------------------------------------ hall of fame

  // A Hall army as a small picture, facing you in its formation: drawn once per army and
  // kept, so redrawing the Hall (every tap) costs nothing. Null if it cannot be drawn.
  const hallPics = new Map();
  function hallPic(l) {
    const key = [l.id, l.level, l.superWon ? 1 : 0, l.units.map((it) => it.spec.type + it.x + ',' + it.y).join(' ')].join(':');
    if (!hallPics.has(key)) hallPics.set(key, armyPic(l.units));
    return hallPics.get(key);
  }

  // An army as the Hall keeps it ({ spec, x, y }), drawn as a picture: { url, w, h }, or null.
  function armyPic(army) {
    try {
      const units = army.map((it) => ({ type: it.spec.type, x: it.x, y: it.y }));
      const rows = new Set(units.map((u) => u.y)).size;
      const w = 300;
      const h = 70 + 22 * (rows - 1);
      const cv = document.createElement('canvas');
      AG.Render.formation(cv, units, { w, h });
      return { url: cv.toDataURL('image/png'), w, h };
    } catch (e) {
      return null;
    }
  }

  function armyPicHTML(army) {
    const pic = armyPic(army);
    const names = army.map((it) => UNITS[it.spec.type].name).join(', ');
    return pic ? `<img class="hall-pic" src="${pic.url}" width="${pic.w}" height="${pic.h}" alt="${esc(names)}">` : `<p class="small muted">${esc(names)}</p>`;
  }

  // Every army that won a campaign, best first. The newest starts at the bottom and climbs:
  // it fights the army right above it, and each win swaps them, until it loses or tops the Hall.
  // Any two ranked armies can also skirmish, whenever you like: if the lower one wins, they
  // swap places.
  function hallScreen(back, state) {
    const st = state || { pick: [], log: [] };
    const h = R.loadHall();
    const L = h.legends;
    const Q = h.queue;
    const all = L.concat(Q);
    const climber = R.hallClimber(h);
    const next = climber && R.hallNext(h, climber.id);
    st.pick = st.pick.filter((id) => all.some((l) => l.id === id));
    const relicNames = (l) => (l.relics || []).filter((id) => RELICS[id]).map((id) => RELICS[id].name).join(', ');
    const many = (name) => name + (/(s|x|ch|sh)$/.test(name) ? 'es' : 's');
    // A house army's picks, the same on every unit: " · Grappling Hook, Venom Blades".
    const squad = (l) => l.units.filter((it) => it.spec.type === l.type);
    const housepicks = (l) => {
      const sp = squad(l)[0] && squad(l)[0].spec;
      const names = sp ? [sp.a1, sp.level >= 2 && sp.a2].filter((id) => id && ABILITIES[id]).map((id) => ABILITIES[id].name) : [];
      return names.length ? ' · ' + esc(names.join(', ')) : '';
    };
    const row = (l, i) => {
      const specs = l.units.map((it) => it.spec);
      const unitNames = specs.map((sp) => `${UNITS[sp.type].name}${sp.level > 1 ? ' (Level ' + sp.level + ')' : ''}`).join(', ');
      const pic = hallPic(l);
      // Its army in formation; a strip of portraits if the picture cannot be drawn.
      const army = pic
        ? `<img class="hall-pic" src="${pic.url}" width="${pic.w}" height="${pic.h}" alt="${esc(unitNames)}" title="${esc(unitNames)}">`
        : `<span class="unit-strip">${specs.map((sp) => `<canvas data-p="${sp.type}:P" title="${esc(UNITS[sp.type].name)}${sp.level > 1 ? ' · Level ' + sp.level : ''}"></canvas>`).join('')}</span>`;
      const picked = st.pick.indexOf(l.id);
      const tag = (l === climber ? '<span class="chip warn">Climbing</span>' : '') + (picked >= 0 ? `<span class="chip ${picked ? 'bad' : 'good'}">${picked ? 'Red' : 'Blue'}</span>` : '');
      const waiting = i < 0;
      return `<button class="hall-row ${l === climber ? 'climbing' : ''} ${picked >= 0 ? 'picked' : ''} ${waiting ? 'waiting' : ''} ${l.superWon ? 'slayer' : ''}" data-legend="${l.id}">
        <span class="rank">${waiting ? ic('hourglass') : '#' + (i + 1)}</span>
        <span class="grow"><span class="nm"><b>${esc(l.name)}</b>${l.superWon ? ` <span class="chip slayer" title="Beat the final challenge, the Eclipse Wyrm">${ic('crossbones')} Wyrm slayer</span>` : ''} <span class="hall-rec" title="${l.wins} won, ${l.losses} lost"><span class="w">${l.wins}W</span><span class="l">${l.losses}L</span></span> ${tag}</span>
          <span class="small muted"><b class="hall-sup">${ic('army')} ${R.armySupply(l)} Supply</b> · ${l.house ? `House army: ${squad(l).length} ${esc(many(UNITS[l.type] ? UNITS[l.type].name : 'unit'))}${squad(l).length < l.units.length ? ' and a Barrier Ward' : ''}, Level ${(l.units[0] && l.units[0].spec.level) || 1}${housepicks(l)}` : `${esc(l.date || '')} · Commander Lv ${l.level || 1} · ${l.units.length} units${relicNames(l) ? ' · ' + esc(relicNames(l)) : ''}`}</span>
          ${army}</span>
      </button>`;
    };
    const climbPanel = climber
      ? `<div class="panel hall-climb">
          <p><b>${esc(climber.name)}</b> is climbing from #${L.indexOf(climber) + 1}. Next up: <b>${esc(next.name)}</b>, #${L.indexOf(next) + 1}. Win, and they swap places; lose, and the climb ends there.</p>
          <div class="row"><button class="btn primary grow" id="hlWatch" ${st.busy ? 'disabled' : ''}>${ic('eye')} Watch the match</button><button class="btn grow" id="hlSim" ${st.busy ? 'disabled' : ''}>${ic('skip')} ${st.busy ? 'Climbing…' : 'Simulate the climb'}</button></div>
        </div>`
      : Q.length
        ? `<div class="panel hall-climb">
          <p><b>${esc(Q[0].name)}</b> is next in line${Q.length > 1 ? ` (${Q.length} armies waiting)` : ''}. Start its climb: it enters at #${L.length + 1} and fights its way up, one match at a time.</p>
          <div class="row"><button class="btn primary grow" id="hlStart">${ic('swords')} Start the climb</button></div>
        </div>`
        : '';
    const pickA = all.find((l) => l.id === st.pick[0]);
    const pickB = all.find((l) => l.id === st.pick[1]);
    // Two ranked armies: a skirmish for their places. One still waiting in line has no place
    // yet, so a match with it is a friendly one.
    const ranked = pickA && pickB && L.includes(pickA) && L.includes(pickB);
    const rankOf = (l) => L.indexOf(l) + 1;
    const [hi, lo] = ranked ? (rankOf(pickA) < rankOf(pickB) ? [pickA, pickB] : [pickB, pickA]) : [];
    const goPanel =
      pickA && pickB
        ? `<div class="panel hall-go">
          <p>${
            ranked
              ? `<b>Skirmish:</b> #${rankOf(hi)} <b>${esc(hi.name)}</b> vs #${rankOf(lo)} <b>${esc(lo.name)}</b>. If ${esc(lo.name)} wins, they swap places; if ${esc(hi.name)} wins, nothing moves.`
              : `<b>Friendly match:</b> ${esc(pickA.name)} vs ${esc(pickB.name)}. ${esc((L.includes(pickA) ? pickB : pickA).name)} is still waiting in line and has no place yet, so nobody moves.`
          }</p>
          <div class="row"><button class="btn primary grow" id="hlFriendly" ${st.busy ? 'disabled' : ''}>${ic('eye')} Watch it</button><button class="btn grow" id="hlSkSim" ${st.busy ? 'disabled' : ''}>${ic('skip')} ${st.busy ? 'Fighting…' : 'Simulate it'}</button></div>
        </div>`
        : '';
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">Every army that won a campaign</p><h2>Hall of Fame</h2></div>
        <p class="muted">Each campaign you win saves its final army here, with its gear, talents and relics, the moment you win. New armies wait in line until you start their climb, whenever you like: it enters at the bottom and climbs by beating the army right above it, one match at a time, until it loses or reaches the top. Any two ranked armies can skirmish at any time too: if the lower-ranked one wins, they swap places. Armies stay here through every update of the game, fighting by the rules of the day; only Reset Hall of Fame clears it.</p>
        ${climbPanel}
        ${st.log.length ? `<div class="panel hall-log">${st.log.map((t) => `<div>${t}</div>`).join('')}</div>` : ''}
        <div class="hall-list">${L.length ? L.map(row).join('') : '<p class="muted">No army yet. Win a campaign to enter yours.</p>'}</div>
        ${Q.length ? `<div class="eyebrow">Waiting to climb</div><div class="hall-list">${Q.map((l) => row(l, -1)).join('')}</div>` : ''}
        ${all.length > 1 && !(pickA && pickB) ? `<p class="small muted">${pickA ? `${esc(pickA.name)} picked. Tap a second army to fight it.` : `Tap two armies for a skirmish: if the lower-ranked one wins, they swap places; if the higher one wins, nothing moves.${Q.length ? ' An army still waiting in line has no place yet, so a match with it is a friendly one.' : ''}`}</p>` : ''}
        ${goPanel}
        <div class="row end">
          ${all.length ? `<button class="btn danger" id="hlReset">Reset Hall of Fame</button>` : ''}
          <button class="btn" id="hlBack">Back</button>
        </div>
      </div>`
    );
    const again = () => hallScreen(back, st);
    $('#hlBack', v).onclick = () => back();
    if ($('#hlReset', v))
      $('#hlReset', v).onclick = async () => {
        if (!(await confirmSheet('Reset the Hall of Fame?', 'Every army in it goes, for good, the ones waiting to climb and the house armies too. Updates to the game never do this: only you can.', 'Reset', 'Keep them', true))) return;
        R.resetHall();
        hallScreen(back, { pick: [], log: [] });
      };
    if ($('#hlStart', v))
      $('#hlStart', v).onclick = () => {
        const l = R.hallStart();
        if (l) {
          st.log = [`${ic('swords')} <b>${esc(l.name)}</b> enters the Hall at #${R.loadHall().legends.findIndex((x) => x.id === l.id) + 1} and starts its climb.`];
          sfx('click');
        }
        again();
      };
    for (const el of $$('[data-legend]', v))
      el.onclick = () => {
        const id = el.dataset.legend;
        const at = st.pick.indexOf(id);
        if (at >= 0) st.pick.splice(at, 1);
        else st.pick = [...st.pick, id].slice(-2);
        sfx('click');
        again();
      };
    const climbMsg = (a, b, winner) => (winner === 'P' ? `${ic('check')} <b>${esc(a.name)}</b> beat ${esc(b.name)} and takes #${R.loadHall().legends.findIndex((l) => l.id === a.id) + 1}.` : `${ic('close')} <b>${esc(a.name)}</b> fell to ${esc(b.name)}. The climb ends at #${R.loadHall().legends.findIndex((l) => l.id === a.id) + 1}.`);
    if ($('#hlWatch', v))
      $('#hlWatch', v).onclick = () =>
        startExhibition(
          climber,
          next,
          (winner) => {
            R.hallResult(climber.id, next.id, winner);
            st.log = [climbMsg(climber, next, winner)];
            again();
          },
          again
        );
    if ($('#hlSim', v))
      $('#hlSim', v).onclick = async () => {
        st.busy = true;
        st.log = [];
        again();
        const id = climber.id;
        for (let guard = 0; guard < 200; guard++) {
          const hall = R.loadHall();
          const me = hall.legends.find((l) => l.id === id);
          const foe = R.hallNext(hall, id);
          if (!me || !foe) break;
          await sleep(60); // let the screen show the last result first
          const winner = R.playHallMatch(me, foe, ((Math.random() * 2 ** 31) >>> 0) + 1);
          R.hallResult(id, foe.id, winner);
          st.log.push(climbMsg(me, foe, winner));
          if (UI.battle || !$('#hlBack')) return void (st.busy = false); // you left the screen
          again();
        }
        st.busy = false;
        again();
      };
    // A skirmish (or friendly match) is over: record it and say what moved.
    const matchResult = (a, b, winner) => {
      st.pick = [];
      const r = ranked ? R.hallSkirmish(a.id, b.id, winner) : null;
      const w = winner === 'P' ? a : b;
      const l = w === a ? b : a;
      st.log = [
        r
          ? r.swapped
            ? `${ic('swords')} Skirmish: <b>${esc(w.name)}</b> beat ${esc(l.name)} and takes #${r.rank}. ${esc(l.name)} drops to #${r.loserRank}.`
            : `${ic('shield')} Skirmish: <b>${esc(w.name)}</b> beat ${esc(l.name)} and holds #${r.rank}. Nothing moves.`
          : `${ic('swords')} Friendly match: <b>${esc(w.name)}</b> beat ${esc(l.name)}. Places unchanged.`,
      ];
      return st.log[0];
    };
    if ($('#hlFriendly', v))
      $('#hlFriendly', v).onclick = () => startExhibition(pickA, pickB, () => again(), again, (winner) => matchResult(pickA, pickB, winner));
    if ($('#hlSkSim', v))
      $('#hlSkSim', v).onclick = async () => {
        st.busy = true;
        again();
        await sleep(60); // let the screen show it first
        const winner = R.playHallMatch(pickA, pickB, ((Math.random() * 2 ** 31) >>> 0) + 1);
        st.busy = false;
        matchResult(pickA, pickB, winner);
        sfx('click');
        if (!UI.battle && $('#hlBack')) again();
      };
  }

  // What a won battle gathered: gold from enemy buildings (of all there was), and the loot
  // (but for loot a bonus goal already names).
  function haulOf(s, enc) {
    const pouches = s.units.filter((u) => u.team === 'E' && (u.structure || u.nonCombat) && !u.traits.has('summon') && (u.bounty || u.salvage));
    const goalLoot = new Set(((enc && enc.bonus) || []).filter((b) => b.type === 'loot').map((b) => b.lootId));
    return {
      lap: s.stats.lapGold || 0,
      gold: s.stats.bounty || 0,
      total: pouches.reduce((t, u) => t + (u.bounty || u.salvage), 0),
      loot: (s.loot || []).filter((l) => !goalLoot.has(l.id)).map((l) => ({ kind: l.kind, taken: !!l.taken })),
    };
  }

  // Victory: keep the win and go on to the rewards, or fight the battle again for a better
  // haul (more gold, the loot left behind, a bonus goal missed). The rewards are already
  // saved, so leaving the app here keeps the win.
  function victorySheet(goals, before, haul) {
    const missed = goals.filter((g) => !g.done).length;
    const rows = [];
    if (haul.total) rows.push(`<div class="obj bonus ${haul.gold >= haul.total ? 'done' : ''}">${ic('gold')}<span>Gold from buildings: <b>${haul.gold}</b> of ${haul.total}</span></div>`);
    if (haul.lap) rows.push(`<div class="obj bonus done">${ic('gold')}<span>Gold from foes your army cut down: <b>${haul.lap}</b></span></div>`);
    for (const l of haul.loot) rows.push(`<div class="obj bonus ${l.taken ? 'done' : 'failed'}">${ic(l.taken ? 'check' : 'close')}<span>${esc(R.LOOT_NAMES[l.kind] || 'Loot')} ${l.taken ? 'taken' : 'left behind'}</span></div>`);
    for (const g of goals) rows.push(`<div class="obj bonus ${g.done ? 'done' : 'failed'}">${ic(g.done ? 'check' : 'close')}<span>${esc(g.text)} <span class="reward">${esc(g.reward)}</span></span></div>`);
    openSheet(
      `${sheetHead('Victory')}
      <p>${missed ? `You won, but missed ${missed === 1 ? 'a bonus goal' : missed + ' bonus goals'}.` : 'You won!'}</p>
      ${rows.length ? `<div class="panel objectives">${rows.join('')}</div>` : ''}
      <p class="muted">Want a better haul? Retry to change your army and fight it again for more gold, the loot or a bonus goal: this victory and its rewards are set aside, and the battle starts over. Or keep the win and continue to your rewards.</p>
      <div class="actions"><button class="btn" id="mgRetry">${ic('swords')} Retry battle</button><button class="btn primary" id="mgGo">Continue</button></div>`,
      (sh) => {
        $('#mgRetry', sh).onclick = () => {
          UI.onSheetClose = null;
          closeSheet();
          UI.run = R.restore(before);
          warRoom();
        };
        $('#mgGo', sh).onclick = () => closeSheet();
      }
    );
    UI.onSheetClose = () => route();
  }

  // ------------------------------------------------------------ rewards

  function itemCard(kind, id, attrs, extra) {
    if (kind === 'scroll') {
      const d = ENCHANTS[id];
      return `<button class="card" ${attrs || ''}><div class="kind">${ic('gem')} Enchantment scroll · +${d.surcharge} Supply</div><div class="title">${esc(d.name)}</div><div class="desc">${esc(d.desc)} Bind it to one unit, forever.</div>${extra || ''}</button>`;
    }
    if (kind === 'talent') {
      const t = TALENTS[id];
      // Talents are the rarer, build-shaping finds: their own colour, a stronger one when rare.
      return `<button class="card talent ${t.tier === 2 ? 'rare' : ''}" ${attrs || ''}><div class="kind">${ic('star')} ${esc(UNITS[t.cls].name)} talent${t.tier === 2 ? ' · rare' : ''} · ${t.cost} Supply</div><div class="title">${esc(t.name)}</div><div class="desc">${esc(t.desc)}</div>${extra || ''}</button>`;
    }
    const d = kind === 'skill' ? SKILLS[id] : GEAR[id];
    const legend = d.rarity === 'legendary';
    return `<button class="card${d.cursed ? ' cursed' : ''}${legend ? ' legendary' : ''}" ${attrs || ''}><div class="kind">${ic(legend ? 'crown' : kind === 'skill' ? 'scroll' : 'sword')} ${legend ? 'Legendary ' + kind : kind === 'skill' ? 'Skill' : 'Gear'} · ${costTag(d)}${d.cursed ? ' · <span class="cursed">Cursed</span>' : ''}</div><div class="title">${esc(d.name)}</div><div class="desc">${esc(d.desc)}</div>${extra || ''}</button>`;
  }

  // A toast line for a unit that just joined, with the talent it came with.
  function joinedText(u) {
    return `${u.name} the ${UNITS[u.type].name} joins your army.${R.talentNote(UI.run, u)}`;
  }

  // A unit on offer. An enchanted one shows its enchantment in a box of its own, and the
  // Details button opens the unit's numbers, attacks and enchantment without taking it.
  // talent: the one it brings, named by the offer (older offers: a random one).
  function recruitCard(unit, enchant, attrs, extra, talent) {
    const T = UNITS[unit];
    const E2 = enchant && ENCHANTS[enchant];
    const legend = T.rarity === 'legendary';
    return `<button class="card ${legend ? 'legendary' : ''}" ${attrs || ''}>
      <div class="card-head"><canvas class="portrait" data-p="${unit}:P"></canvas>
      <div class="grow"><div class="kind">${legend ? `${ic('crown')} Legendary recruit` : `Recruit · ${T.rarity}`} · ${T.cost} Supply</div><div class="title">${T.name}${E2 ? ` <span class="ench-cost">${ic('gem')} +${E2.surcharge} Supply</span>` : ''}</div></div>
      <span class="card-info" role="button" tabindex="0" data-rinfo="${unit}:${enchant || ''}:${talent || ''}" aria-label="Details">${ic('help')}</span></div>
      <div class="desc">${esc(T.desc)}</div>
      ${E2 ? `<div class="ench-box"><b>${ic('gem')} Enchanted: ${esc(E2.name)}</b><span>${esc(E2.desc)}</span><span class="small">Bound to this unit for good: fielding it costs ${E2.surcharge} more Supply.</span></div>` : ''}
      ${talentLine(T, talent, 'div')}${extra || ''}</button>`;
  }

  // The talent a unit comes with, in the talents' own teal (a star, the name, a tinted box),
  // so it reads as a talent and not as more about the unit's own attacks.
  function talentLine(T, talent, tag) {
    const d = talent && TALENTS[talent];
    return `<${tag} class="talent-line small">${ic('star')}<span>${d ? `Comes with the <b class="talent-name">${esc(d.name)}</b> talent: ${esc(d.desc)}` : `Comes with a random ${esc(T.name)} <b class="talent-name">talent</b>.`}</span></${tag}>`;
  }

  // A Level 1 unit of a type as it would join, enchantment included: its battle numbers.
  function recruitStats(unit, enchant) {
    const T = UNITS[unit];
    const spec = { type: unit, level: 1, a1: T.abilities ? T.abilities[1][0] : null, a2: T.abilities ? T.abilities[2][0] : null, talents: [], skills: [], gear: [], enchant: enchant || null, name: T.name };
    return R.unitStats(UI.run, spec, 'P');
  }

  // A recruit's details before you take it (or a unit you just drafted): numbers, attacks,
  // traits, its enchantment and the talent it comes with, when that is settled.
  function recruitInfoSheet(unit, enchant, talent) {
    const T = UNITS[unit];
    const E2 = enchant && ENCHANTS[enchant];
    const u = recruitStats(unit, enchant);
    const after = UI.onSheetClose;
    UI.onSheetClose = null;
    openSheet(
      `${sheetHead(esc(T.name), `Recruit · ${T.rarity} · ${T.cost} Supply${E2 ? ` (+${E2.surcharge} enchanted)` : ''} · <b>${u.maxHp} HP</b>`, true)}
      ${E2 ? `<div class="ench-box"><b>${ic('gem')} Enchanted: ${esc(E2.name)}</b><span>${esc(E2.desc)}</span><span class="small">Bound to this unit for good: fielding it costs ${E2.surcharge} more Supply. The numbers below include it.</span></div>` : ''}
      <p class="muted">${esc(T.desc)}</p>
      ${statsHTML(u)}
      ${actsHTML(u)}
      ${traitLines(u).length ? `<ul class="tips">${traitLines(u).map((t) => `<li>${esc(t)}</li>`).join('')}</ul>` : ''}
      ${talentLine(T, talent, 'p')}
      <div class="actions"><button class="btn" data-close>Back</button></div>`
    );
    UI.onSheetClose = after;
  }

  // The Details buttons on recruit cards: they open the details and do not pick the card.
  function bindRecruitInfo(el) {
    for (const b of $$('[data-rinfo]', el)) {
      const open = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const [unit, enchant, talent] = b.dataset.rinfo.split(':');
        sfx('click');
        recruitInfoSheet(unit, enchant || null, talent || null);
      };
      b.addEventListener('click', open);
      b.addEventListener('keydown', (e) => (e.key === 'Enter' || e.key === ' ') && open(e));
    }
  }

  // Reward cards: what you got anyway is lit up as collected; a choice waiting for you has a
  // soft aura that fades in and out (data-choose) until you pick, then the pick lights up
  // and the rest go grey.
  const GOT = 'data-got="✓ Collected" disabled';
  function pickState(taken, chosen) {
    return !taken ? 'data-choose' : chosen ? 'data-got="✓ Chosen" disabled' : 'data-passed disabled';
  }

  function spoilCard(sp, i, taken, chosen) {
    const attrs = `data-spoil="${i}" ${pickState(taken, chosen)}`;
    if (sp.type === 'recruit') return recruitCard(sp.unit, sp.enchant, attrs, ownedNote(UI.run, 'recruit', sp.unit), sp.talent);
    if (sp.type === 'skill' || sp.type === 'gear' || sp.type === 'talent' || sp.type === 'scroll') return itemCard(sp.type, sp.id, attrs, ownedNote(UI.run, sp.type, sp.id));
    return `<button class="card" ${attrs}><div class="kind">${ic('gold')} Gold</div><div class="title">${sp.amount} gold</div></button>`;
  }

  function levelUpHTML(from, to) {
    if (!to || to <= from) return '';
    const a = COMMAND[from];
    const b = COMMAND[to];
    return `<div class="levelup" data-got="✓ Collected">${ic('crown')}<div><b>Commander level ${to}!</b><div class="small">Supply ${a.supply} → ${b.supply}</div></div></div>`;
  }

  // `picked`: called right after a pick. Once nothing is left to choose (picks are final),
  // the screen moves on by itself after a moment, so the pick can be seen lighting up.
  function rewardScreen(picked) {
    const run = UI.run;
    const p = run.pending;
    const bossDone = !p.bossRelics || p.bossRelicTaken;
    const li = R.levelInfo(run);
    const v = showView(
      `<div class="wrap">
        <div class="reward-head"><p class="eyebrow">${p.kind === 'boss' ? 'The champion falls' : 'The field is yours'}</p><h2>Victory</h2></div>
        ${levelUpHTML(p.lvFrom, p.lvTo)}
        <div class="panel loot" data-got="✓ Collected">
          <span class="res xp">${ic('crown')} +${p.xp} XP <span class="small muted">(${li.max ? 'max level' : `${li.xp - li.from}/${li.to - li.from} to Lv ${li.lv + 1}`})</span></span>
          <span class="res gold">${ic('gold')} +${p.gold} gold${p.firstTry ? ' <span class="small muted">(first-try bonus included)</span>' : ''}</span>
          ${p.lean ? `<span class="res gold">${ic('command')} +${p.lean} gold for ${p.unspent} unspent Supply</span>` : ''}
          ${p.midas ? `<span class="res gold">${ic('gold')} +${p.midas} gold picked up in battle</span>` : ''}
          ${p.bounty ? `<span class="res gold">${ic('gold')} +${p.bounty} gold from broken buildings</span>` : ''}
          ${p.lap ? `<span class="res gold">${ic('gold')} +${p.lap} gold from foes your army cut down</span>` : ''}
          <span class="res">${ic('gold')} ${run.gold} total</span>
        </div>
        ${(p.objectives || []).some((o) => o.done) ? `<div class="panel objectives" data-got="✓ Collected">${p.objectives
          .filter((o) => o.done)
          .map((o) => `<div class="obj bonus done">${ic('check')}<span>${esc(o.text)} <span class="reward">${esc(o.got)}</span></span></div>`)
          .join('')}</div>` : ''}
        ${(p.objectives || []).some((o) => !o.done) ? `<div class="panel objectives missed">${p.objectives
          .filter((o) => !o.done)
          .map((o) => `<div class="obj bonus failed">${ic('close')}<span>${esc(o.text)}</span></div>`)
          .join('')}</div>` : ''}
        ${p.prisoner && R.unitById(run, p.prisoner) ? `<div class="gotline" data-got="✓ Collected">${ic('check')}<span>The prisoner ${esc(R.unitById(run, p.prisoner).name)} the ${UNITS[R.unitById(run, p.prisoner).type].name} is free and joins your army.${esc(R.talentNote(run, R.unitById(run, p.prisoner)))}</span></div>` : ''}
        ${p.relicGained ? `<div><div class="eyebrow">${p.relicLucky ? 'A lucky find: a relic' : 'Relic claimed'}</div><div class="cards">${relicCard(p.relicGained, GOT)}</div></div>` : ''}
        ${p.lootRelic ? `<div><div class="eyebrow">From the relic cache</div><div class="cards">${relicCard(p.lootRelic, GOT)}</div></div>` : ''}
        ${p.tome && p.tome.length ? `<div><div class="eyebrow">${p.tomeTaken ? 'The tome is read' : 'The Lost Tome: choose a skill'}</div>
          <div class="cards">${p.tome.map((id, i) => itemCard('skill', id, `data-tome="${i}" ${pickState(p.tomeTaken, p.tomePick === i)}`, ownedNote(run, 'skill', id))).join('')}</div></div>` : ''}
        ${p.bossRelics && p.bossRelics.length ? `<div><div class="eyebrow">${p.bossRelicTaken ? 'Boss relic claimed' : 'Choose a boss relic'}</div><div class="cards">${p.bossRelics.map((id) => relicCard(id, `data-boss="${id}" ${pickState(p.bossRelicTaken, p.bossPick === id)}`)).join('')}</div></div>` : ''}
        <div><div class="eyebrow">${p.spoilTaken ? 'Spoils claimed' : 'Choose your spoils'}</div>
          <div class="cards">${p.spoils.map((sp, i) => spoilCard(sp, i, p.spoilTaken, p.spoilPick === i)).join('')}</div>
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
          rewardScreen(true);
        }
      };
    for (const b of $$('[data-spoil]', v))
      b.onclick = () => {
        const i = +b.dataset.spoil;
        const sp = p.spoils[i];
        if (R.takeSpoil(run, i)) {
          sfx('coin');
          if (sp.type === 'recruit') toast(joinedText(run.roster[run.roster.length - 1]));
          else if (sp.type !== 'gold') toast(`Added to your pack. Equip it from a unit's loadout.`);
          rewardScreen(true);
        }
      };
    $('#rwArmy', v).onclick = () => armySheet(() => rewardScreen());
    if ($('#rwSkip', v))
      $('#rwSkip', v).onclick = () => {
        R.skipSpoils(run);
        rewardScreen(true);
      };
    for (const b of $$('[data-tome]', v))
      b.onclick = () => {
        if (R.takeTome(run, +b.dataset.tome)) {
          sfx('coin');
          rewardScreen(true);
        }
      };
    if ($('#rwTomeSkip', v))
      $('#rwTomeSkip', v).onclick = () => {
        R.skipTome(run);
        rewardScreen(true);
      };
    let gone = false;
    const go = () => {
      if (gone) return;
      gone = true;
      const wasBoss = p.kind === 'boss';
      R.completeNode(run);
      if (wasBoss && !run.over) toast(`${ACTS[run.act].short}: ${ACTS[run.act].name}`);
      route();
    };
    $('#rwGo', v).onclick = go;
    if (picked && p.spoilTaken && bossDone && (!p.tome || p.tomeTaken)) {
      $('#rwGo', v).innerHTML = `${p.kind === 'boss' && run.act >= 3 ? 'Claim victory' : 'Continue'} ${ic('fast')}`;
      // Still on this screen (no sheet open over it, nothing else tapped): on to the next.
      setTimeout(() => {
        if (UI.run === run && run.pending === p && $('#rwGo') && $('#modal').hidden) go();
      }, 1100);
    }
  }

  // ------------------------------------------------------------ shop

  function shopScreen() {
    const run = UI.run;
    const p = run.pending;
    const card = (it, i) => {
      const can = R.canBuy(run, it);
      const price = `<div class="price">${ic('gold')} ${it.sold ? 'Sold' : it.price}</div>`;
      // What you can still buy has the soft aura of a choice waiting for you; sold items
      // and what you cannot afford stay plain.
      const dis = `data-buy="${i}" ${can ? 'data-choose' : 'disabled'}`;
      if (it.kind === 'recruit') return recruitCard(it.unit, it.enchant, dis, ownedNote(run, 'recruit', it.unit) + price, it.talent);
      if (it.kind === 'skill' || it.kind === 'gear' || it.kind === 'talent' || it.kind === 'scroll') return itemCard(it.kind, it.id, dis, ownedNote(run, it.kind, it.id) + price);
      if (it.kind === 'relic')
        return `<button class="card${RELICS[it.relic].cursed ? ' cursed' : ''}${RELICS[it.relic].tier === 'legendary' ? ' legendary' : ''}" ${dis}><div class="kind">${ic(RELICS[it.relic].tier === 'legendary' ? 'crown' : 'gem')} ${RELICS[it.relic].tier === 'legendary' ? 'Legendary relic' : 'Relic · ' + relicTier(RELICS[it.relic])}</div><div class="title">${esc(RELICS[it.relic].name)}</div><div class="desc">${esc(RELICS[it.relic].desc)}</div>${price}</button>`;
      if (it.kind === 'supply')
        return `<button class="card" ${dis}><div class="kind">${ic('command')} Service</div><div class="title">Supply Cache</div><div class="desc">+1 Supply in every battle for the rest of the campaign.</div>${price}</button>`;
      return `<button class="card" ${dis}><div class="kind">${ic('crown')} Service</div><div class="title">War Manual</div><div class="desc">Gain 10 XP toward your next commander level.</div>${price}</button>`;
    };
    // Six things, one of each kind, so one list: each card says what it is. Resupply brings
    // out a fresh stock, a little dearer each time.
    const reroll = R.rerollPrice(run);
    const v = showView(
      `<div class="wrap">
        <div class="row"><div class="grow"><p class="eyebrow">Merchant</p><h2>The Wandering Market</h2></div></div>
        <div class="row">${resbar(run)}<span class="grow"></span><button class="btn" id="shArmy">${ic('army')} Army</button></div>
        <div class="cards">${p.stock.map((it, i) => card(it, i)).join('')}</div>
        <div class="row end"><button class="btn" id="shReroll" ${run.gold >= reroll ? '' : 'disabled'}>${ic('rotate')} Resupply · ${ic('gold')} ${reroll}</button><button class="btn primary" id="shLeave">Leave the market</button></div>
      </div>`
    );
    $('#shReroll', v).onclick = () => {
      if (R.rerollShop(run)) {
        sfx('coin');
        shopScreen();
      }
    };
    for (const b of $$('[data-buy]', v))
      b.onclick = () => {
        const i = +b.dataset.buy;
        const it = p.stock[i];
        const before = R.commanderLevel(run);
        if (R.buy(run, i)) {
          sfx('coin');
          if (it.kind === 'manual' && R.commanderLevel(run) > before) toast(`Commander level ${R.commanderLevel(run)}! Supply ${R.supplyFor(run)}.`);
          if (it.kind === 'recruit') toast(joinedText(run.roster[run.roster.length - 1]));
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

  // The relics you hold, at the top of every event, so a choice that asks for one (the
  // Merchant Caravan's trade) can be weighed: tap one for what it does.
  // Plain circles in their rarity's colour (common grey, uncommon green, rare blue, boss
  // orange, legendary gold): tap one for its name and what it does.
  function eventRelics(run) {
    const ids = run.relics.filter((id) => RELICS[id]);
    if (!ids.length) return '';
    return `<div class="ev-relics"><span class="eyebrow">${ic('gem')} Your relics</span><div class="dots">${ids
      .map((id) => `<button class="relic-dot big tier-${RELICS[id].tier}" data-evrelic="${id}" aria-label="${esc(RELICS[id].name)}">${ic(RELIC_ICON[id] || 'gem')}</button>`)
      .join('')}</div></div>`;
  }

  // The Merchant Caravan's trade: one block, your common relics as circles. Tap the one to
  // give up (you confirm it, with what each relic does).
  function swapBlock(run, swaps) {
    const offer = RELICS[(run.pending.ctx || {}).relic];
    if (!swaps.length || !offer) return '';
    const live = swaps.filter((c) => c.enabled && c.id.startsWith('swap:'));
    return `<div class="choice swap-block" ${live.length ? 'data-choose' : ''}><b>Trade a common relic for the ${esc(offer.name)}</b>
      <span>${esc(offer.desc)}</span>
      ${live.length ? `<span class="small">Tap the relic to give up:</span><div class="dots">${live
        .map((c) => {
          const id = c.id.slice(5);
          return `<button class="relic-dot big tier-${RELICS[id].tier}" data-swap="${esc(c.id)}" aria-label="${esc(RELICS[id].name)}">${ic(RELIC_ICON[id] || 'gem')}</button>`;
        })
        .join('')}</div>` : `<span class="small">The merchant only takes a common relic, and you have none.</span>`}</div>`;
  }

  function eventScreen() {
    const run = UI.run;
    const p = run.pending;
    const ev = R.eventDef(p.eventId);
    const choices = R.eventChoices(run);
    const v = showView(
      `<div class="wrap">
        <div class="row">${resbar(run)}</div>
        ${eventRelics(run)}
        <div class="parch-card">
          <p class="eyebrow" style="color:#7a5a2c">On the road</p>
          <h2>${esc(ev.title)}</h2>
          <p>${esc(ev.text)}</p>
          ${p.result ? `<p class="result">${esc(p.result)}</p>` : choices
            .filter((c) => !c.id.startsWith('swap'))
            .map((c) => `<button class="choice" data-choice="${esc(c.id)}" ${c.enabled ? 'data-choose' : 'disabled'}><b>${esc(c.label)}</b><span>${esc(c.detail)}</span></button>`)
            .join('') + swapBlock(run, choices.filter((c) => c.id.startsWith('swap')))}
        </div>
        ${p.result ? `<div class="row end"><button class="btn" id="evArmy">${ic('army')} Army</button><button class="btn primary" id="evGo">Continue</button></div>` : ''}
      </div>`
    );
    for (const b of $$('[data-choice]', v))
      b.onclick = async () => {
        const c = choices.find((x) => x.id === b.dataset.choice);
        let rid = null;
        if (c.pick) {
          rid = await pickUnit(c.label, esc(c.detail), (u) => R.eventPickOk(run, c.pick, u));
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
    for (const b of $$('[data-evrelic]', v))
      b.onclick = () => {
        const r = RELICS[b.dataset.evrelic];
        toast(`${r.name} (${r.tier}): ${r.desc}`, 4000);
      };
    for (const b of $$('[data-swap]', v))
      b.onclick = async () => {
        const give = RELICS[b.dataset.swap.slice(5)];
        const get = RELICS[p.ctx.relic];
        if (!(await confirmSheet(`Trade the ${give.name}?`, `You give up <b>${esc(give.name)}</b>: ${esc(give.desc)}<br><br>You get <b>${esc(get.name)}</b>: ${esc(get.desc)}`, 'Trade it', 'Keep it'))) return;
        if (R.chooseEvent(run, b.dataset.swap, null) == null) return toast('That trade is not available.');
        sfx('coin');
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
    // A won campaign enters its final army in the Hall of Fame, at the bottom.
    const hall = R.loadHall();
    const place = run.legendId ? R.hallPlace(hall, run.legendId) : null;
    const legend = place ? hall.legends.concat(hall.queue).find((l) => l.id === run.legendId) : null;
    const hallText = !place
      ? ''
      : place.inLine
        ? `Your army is saved in the <b>Hall of Fame</b> as <b>${esc(legend.name)}</b>, waiting to climb${place.inLine > 1 ? ` (#${place.inLine} in line)` : ''}. ${hall.legends.every((l) => l.house) ? `The house armies hold the Hall for now: a few Level 3 Scouts, Knights, Archers or Witches each, behind a Level 3 Barrier Ward (${R.loadHall().legends.filter((l) => l.house).map((l) => R.armySupply(l)).join(', ')} Supply), veterans with both picks. Can you climb past them all? ` : ''}Start its climb now, or come back any time from the title screen.`
        : `Your army enters the <b>Hall of Fame</b> as <b>${esc(legend.name)}</b>, at #${place.rank} of ${hall.legends.length}. ${R.hallNext(hall, legend.id) ? 'Watch it climb: it fights the army above it, and each win moves it up one place.' : hall.legends.length === 1 ? 'It is the first army in the Hall. Win again, and the next one will have to beat it.' : 'Its climb is over.'}`;
    const hallPanel = legend
      ? `<div class="panel hall-climb"><p>${ic('crown')} ${hallText}${legend.superWon ? ` It wears the <span class="chip slayer">${ic('crossbones')} Wyrm slayer</span> badge there, for good.` : ''}</p>
          <div class="row"><button class="btn primary grow" id="enHall">${ic('crown')} ${place.inLine || R.hallNext(hall, legend.id) ? 'Climb the Hall of Fame' : 'Hall of Fame'}</button></div></div>`
      : '';
    const v = showView(
      `<div class="wrap">
        <div><p class="eyebrow">${run.superWon ? 'Beyond the Spire' : run.won ? 'The Spire is silent' : 'The campaign is over'}</p>
        <h2>${run.superWon ? 'Super victory' : run.won ? 'Campaign won' : 'Campaign ended'}</h2></div>
        <p class="muted">${run.superWon ? 'The Eclipse Wyrm falls. Nobody was supposed to do that. Your warband is legend.' : run.won ? 'The Ashen Tyrant is slain and the arena bows to your warband.' : `Your march ended in ${ACTS[run.act].short}, ${esc(ACTS[run.act].name)}.`}</p>
        <div class="end-stats">
          <div class="stat"><b>${st.battles}</b><span>Battles won</span></div>
          <div class="stat"><b>${st.losses}</b><span>Retries</span></div>
          <div class="stat"><b>${st.firstTry}</b><span>First-try wins</span></div>
          <div class="stat"><b>${R.commanderLevel(run)}</b><span>Commander level</span></div>
          <div class="stat"><b>${st.kills}</b><span>Enemies slain</span></div>
          <div class="stat"><b>${st.gold}</b><span>Gold earned</span></div>
        </div>
        ${hallPanel}
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
    if ($('#enHall', v)) $('#enHall', v).onclick = () => hallScreen(endScreen);
  }

  // ------------------------------------------------------------ help and codex

  function helpSheet() {
    openSheet(
      `${sheetHead('How to play')}
      <div class="help">
        <h4>The campaign</h4>
        <p>March through three acts. Each act has four rounds: in each you choose one of three battles, easy, medium or elite, from a look at the field, its goals and what it pays (elite battles are hard, pay more and drop a relic). One event and one merchant wait somewhere in the middle, and a boss ends the act. Lose as often as you need: a defeat brings you back to the round's choice. Beat the Act III boss to win; after that, an optional final challenge waits for a super victory.</p>
        <h4>Hall of Fame</h4>
        <p>Every won campaign enters its final army, kit and relics included, at the bottom of the Hall of Fame. It climbs by fighting the army right above it, both sides on the AI: a win swaps them, a loss or reaching #1 ends the climb. Watch the matches or simulate the climb; tap two armies for a friendly match. Find it on the title screen.</p>
        <h4>Supply and the war room</h4>
        <p>Before every battle you see the whole enemy army. Spend <b>Supply</b> to build your answer to it. Everything costs Supply: each unit, its level, its abilities, its skills and gear, and any enchantment on it. Two Level 1 Knights or one Level 2 Knight with better tricks? That choice is the heart of the game. Unspent Supply pays a little gold if you win.</p>
        <h4>Levels, abilities, skills and gear</h4>
        <ul>
          <li>Every unit picks 1 of 3 abilities at Level 1, and 1 of 3 more at Level 2. Stronger picks cost more Supply.</li>
          <li><b>Active abilities</b> have 1 to 3 uses a battle that never come back, and most a cooldown of their own: after a use they wait that many of the unit's turns. Using one is the unit's action for the turn, instead of its attack.</li>
          <li>${ic('star')} <b>Talents</b> are class passives. Every class has at least three. Each new unit brings one you do not own yet (only once you own them all does one repeat), and you find more in shops and battle spoils, only for classes in your army. A unit has one talent slot per level (three at Level 3); mix and match any you own. Each copy fits one unit at a time.</li>
          <li>Level 2 (+2 Supply): +20% HP, +15% damage, the second ability and a second skill slot. Level 3 (+5): +40% HP, +30% damage, a Mastery and a second gear slot.</li>
          <li>Skills and gear are items you own. Slot each one into a single unit. They cost Supply only when that unit fights.</li>
          <li><b>Setup guide</b>: put a unit on the board and it asks about its kit, one question at a time (level, abilities, talents, skills, gear). Answer No to skip one, or Done to stop.</li>
          <li><b>The bench is bare</b>: units on the bench are plain base units. Levels, abilities, talents, skills and gear go on a unit once it is on the board; taking it off sends everything back to your pack. A card's cost badge shows the base price and a small +N for its loadout. Your plan for a battle stays put if you lose or step away, and a new battle opens with your last army.</li>
          <li>Enchantment scrolls bind a permanent bonus to one unit, forever. That unit costs a little more Supply to field.</li>
        </ul>
        <h4>Commander level</h4>
        <p>Victories earn XP. Each commander level raises your Supply. There is no limit on units in a battle: field as many as your Supply pays for. Elites, bosses and bonus goals pay extra XP.</p>
        <h4>Taking turns</h4>
        <ul>
          <li><b>Auto battle</b>: you set up the army in the war room (units, levels, talents, skills, gear, where they stand) and tap <b>Begin battle</b>. Your army then fights on its own; you watch. Lost? Change the army and try again, as often as you like.</li>
          <li>The sides take turns, and the enemy goes first. Each turn, one unit acts: it moves, attacks or uses an ability, and faces.</li>
          <li><b>Turn order</b>: each side's units take its turns in a rotation, faster units first (<b>SPD</b> on their cards). A Scout (SPD 8) goes before a Knight (SPD 2). The strip under the board shows who goes next.</li>
          <li>Acting starts a unit's <b>cooldown</b> (CD on its card). Its turns still come, but it passes that many of them: it passes at once, its cooldown drops by one, and the next unit in line goes. Moving alone never starts a cooldown. Paralyzed units, and units with nothing in reach, pass too. The turn order shows every unit's turn: a unit about to pass is greyed out with its cooldown on its portrait. Poison, burns, regen and fatigue come on passed turns too.</li>
          <li><b>A unit's turn, step by step</b>: what comes with a unit's turn always comes in this order: its fatigue hit, then poison, then burns, then fire underfoot, then regen; only then does it act, or pass with its cooldown dropping by one ("PASS COOLDOWN 2→1" over its head). Each step shows over the unit's head on its own beat ("-16 FATIGUE", then "-5 POISON", then "+3 REGEN"), never two at once, even at 2× speed, and the numbers stack top to bottom in the order they happened instead of landing on each other.</li>
          <li>Durations such as "roots for 2 turns" count the affected unit's own turns. The turn counter counts rounds: the enemy's move, then yours.</li>
          <li><b>Regen</b> heals a unit whenever its turn comes, acting or passing. It comes from a few talents, gear and units, and it all adds up; only the rare boss relic Sacred Chalice gives your whole army regen. A unit card shows it as ${ic('heart')} Regen.</li>
          <li><b>A mission done is the win</b>: breaking the cage, the gate, the warbanner, the totems or the wagons, holding the shrine, slaying the commander or the boss, or outlasting the waves wins the battle there and then: nothing after it can take the win away. The battle goes on, though: both sides' fatigue switches on (see Fatigue), so the enemy wears down while your army grabs what else it can, a few more barricades, the loot or a bonus goal, before fatigue wears it down too. Reinforcements keep marching in (until turn ${R.OVERTIME}), so the ambush bonus is still there to chase, or you can leave them be and go for the gold. And every enemy unit your army cuts down, before the win or after, is worth a coin or two: 1 gold, 2 for a big one (3 Supply or more). Tap <b>Finish now</b> whenever you like. "Lose no unit" and "win within N turns" goals are judged at the moment the mission was done. Rushing the mission is a way to beat an army too tough to grind down.</li>
          <li><b>Cleanup</b>: when the enemy army falls with loot or gold-bearing or goal buildings still on the field, the win is yours at once and the battle goes on while your army collects them: buildings, guards still at their posts, loot. Your fatigue switches on that moment, from 1 (or carries on, if it was on already). It cannot cost you the battle, and there is no time limit: it ends when nothing worth having is left, when your army has fallen, or when you tap Finish now. Flawless and fast-win goals count from the moment the army fell.</li>
          <li><b>Fatigue</b>: each side has its own fatigue timer, off at first. Once a side's timer is on, each of its units loses HP whenever its turn comes, acting or passing, past armor and shields, before it moves, acts or passes: never a whole side at once, always one unit at a time. A side's first hit is 1, then 2, 3 and so on, one more every time one of its units takes its turn: five of your units passing in a row at 15 lose 15, 16, 17, 18 and 19. The two sides count apart, and nothing resets or doubles a count. Your timer switches on when you do the mission or the enemy army falls; the enemy's when you do the mission. On turn ${R.OVERTIME} every timer still off switches on, and one already on carries on untouched. From turn ${R.OVERTIME} no more reinforcements come. The top bar shows each side's next hit. Big units and regen last longest, so a tough tank can win a long battle on its own. The last side standing wins.</li>
          <li><b>Nobody surrenders</b>: a battle ends only when one side has no units left. Units that cannot attack (a Furgon, a Barrier Ward) fight on, and the enemy must still bring them down; if neither side can hurt the other, fatigue settles it. Summoned shrubs do not count: they take no fatigue, and a side with only shrubs left has lost.</li>
          <li>A unit's own attack is its <b>basic attack</b> (its <b>basic ability</b> for healers and helpers); only the abilities it picks go by name.</li>
          <li><b>Triggers</b>: many talents and relics fire on an event rather than giving a flat bonus, and the board calls them out as they happen. <b>Critical!</b> hits deal double damage (Lucky Coin, the Lucky skill, every third shot of a Level 3 Archer). <b>Executed</b>: a foe left very low falls outright (never a boss). <b>Trophies</b> from kills add 10% damage each, up to five, and the killer grows a little bigger. Some things go out with a bang when they fall (Powder Keg, Powder Belt, Overload, Bramble Burst, Combustion), poison and fire can leap from the dead to their neighbours (Contagion, Plague Doctor's Mask, Wildfire Oil), and slain enemies can rise as skeletons on your side (Necromancer's Bell, Shadow Pact). Cursed relics give a big edge at a real cost.</li>
          <li><b>Poison</b> and burns tick at the start of the poisoned unit's own turn, for a set number of its turns. Poisons from different sources stack: each keeps its own damage and its own turns, and the unit takes them all added up (4 and 8 make 12) until each runs out. The same source poisoning again only refreshes its own poison. Poisoned units cannot heal. Buildings, wagons, cages, constructs (golems, wards) and the undead are immune to poison: "IMMUNE TO POISON" floats over a unit the poison did not take on. Poison damage floats up in magenta with a minus sign, like all damage; heals are green with a plus.</li>
          <li>While watching: ${ic('fast')} at the top switches the speed (1× or 2×), ${ic('pause')} pauses, and tapping a unit pauses and shows its details. Pinch to zoom, drag to move the board.</li>
          <li><b>Priority</b>: tap an enemy unit, a building, a barricade with gold, a chest, the shrine, any empty tile, a boulder, tree or shrub while watching, then ${ic('target')} Priority. Your army goes all out for it, whatever the cost: every unit attacks it, or heads for the chest and takes it. With the shrine, one unit stands on it and stays while the others guard it. With an empty tile, your army moves there and huddles as close as it can (a corner, a choke point), attacking whatever comes in reach, until you clear it. A boulder, tree or shrub works the same way: your army gathers around it without trying to cut it down. With one of your own units, the rest gather around it and follow it. Once it falls or is taken, your army is back to normal orders. Clear it any time from the panel. You can also pick it in the war room before the battle: tap the enemy or chest there, then ${ic('target')} Priority, and your army goes for it from the first turn. Without a priority, your army still heads for chests and takes one when it can spare the turn, unless it could kill an enemy instead; it leaves loot with sleeping guards alone until it can grab it in one move. It also plays for the mission: it goes for the Commander when killing it wins, hits the wagon nearest its way out first, and presses on toward the end of a "win within N turns" goal.</li>
        </ul>
        <h4>Damage, facing and defense</h4>
        <ul>
          <li>Physical attacks are reduced by <b>armor</b> and can be <b>blocked</b>: full block from the front, half from the side, never from behind.</li>
          <li><b>Friendly fire</b>: area attacks (cleaves, fireballs, volleys, lightning bolts, breaths) hit your own units in the area too, unless an upgrade makes them spare allies, like the <b>Disciplined</b> skill.</li>
          <li>When a unit finishes its turn it turns to face the nearest enemy.</li>
          <li>Magic ignores armor and block, but is reduced by <b>magic resistance</b>. No defense goes above 50%. Ghosts shrug off steel but fear magic; Mage Knights shrug off spells.</li>
          <li>Every attack shows its type: ${dmgIcon('phys')} a sword for <b>physical</b>, ${dmgIcon('magic')} a violet sparkle for <b>magic</b>. A unit's DMG stat carries the icon of its main attack, and magic damage numbers float up in violet.</li>
        </ul>
        <h4>Missions</h4>
        <ul>
          <li>Defeat every enemy, burn their banner, break a prison, kill a commander, hold a shrine, survive the waves, topple their totems, raze the buildings that send reinforcements, storm a castle gate, or stop a convoy of loot wagons. Defeating every enemy always wins too, once no more reinforcements are coming.</li>
          <li>Bonus goals pay extra: loot on the field, fast wins, flawless wins, ambushing reinforcements (cutting down a few of the enemies that arrive in waves), or winning with a unit that sat out your last battle. That unit insists on fighting: it starts on the field and cannot be taken off.</li>
          <li>War totems whip the enemies within 2 tiles into a frenzy (25% more damage) until they fall.</li>
          <li><b>Enemies never heal</b>, bosses included, and never rise again once they fall. You have your Cleric; they have nothing that mends, so every hit you land stays landed.</li>
        </ul>
        <h4>Pushes and pulls</h4>
        <ul>
          <li>Some attacks <b>shove</b> a unit away (Shield Bash, Ground Slam, Boulder Toss, Arcane Burst, Wing Buffet, the Bull Rush skill, a Gale Horn, an Orc Brute's maul) or <b>drag</b> it in (the Scout's Grapnel, a Grappling Hook or Chain Hook, a Magnetic Core, Void Grasp, Siren's Lure, a spider's web, Grukk's chain). It moves in a straight line, tile by tile.</li>
          <li><b>What stops it hurts</b>, past armor and block: a rock or the edge of the field ${E.IMPACT.rock}; another unit or a building ${E.IMPACT.unit}, and that one takes ${E.IMPACT.unit} too, friend or foe; water ${E.IMPACT.water}, and it climbs out onto the nearest dry tile, rooted for a turn (the water puts out burns); lava ${E.IMPACT.lava}, and it climbs out burning.</li>
          <li>Flyers sail over water and lava. Bosses, huge units and the steadfast (Unstoppable, Unshakable, Iron Will) never budge. A hook flies straight: along a row or column, with no rock or unit in between. A blocked blow shoves nobody.</li>
          <li>Relics: the Iron Ram adds 6 to every impact, the Tidecaller's Conch shoves and drags a tile further, and the Anchor Stone keeps your units from being moved at all.</li>
        </ul>
        <h4>Buildings and siege</h4>
        <ul>
          <li>Walls, gates, towers, totems, tents, crypts, dens, portals and barricades are <b>buildings</b>. Stone ones shrug off swords and spells alike; wooden ones burn, taking extra damage from fire and magic; dark portals unravel under magic but barely notice steel.</li>
          <li><b>Siege damage</b> breaks them fast: the Trebuchet (+150% to buildings), a Siege Hammer (triple), the Demolisher skill (double), a Blasting Charge, the Golem's Boulder Toss, or the Sapper's Kit relic.</li>
          <li><b>Barricades hold gold.</b> Break one and coins burst out: 12, 16 or 20 gold by act, paid with the battle's gold when you win. Your units break them when no enemy is within reach.</li>
          <li><b>Wreckage</b> litters the Act I boss's camp: four wrecked carts with 8 gold in each. Your army leaves them be until the boss and its retinue fall, then breaks what it can before its fatigue tells.</li>
          <li><b>Legendaries</b> (molten-gold cards): the Archmage's meteor, the Phoenix's fiery dive, the Frost Giant's glacier, the Sun Paladin's judgment and the Dragon Tyrant's breath, each a huge act and then a long cooldown, plus legendary skills and gear. None turn up before the second half of Act 2; from there they come more and more often, most of all late in Act 3 and from elites and bosses.</li>
          <li><b>Every enemy building pays a little.</b> Break a wall, tower, totem, banner, cage or gate and your army picks up 3 gold (5 for the gate and for tents, crypts, dens, portals and guardhouses). Not worth a detour, but never wasted.</li>
        </ul>
        <h4>Reinforcements</h4>
        <ul>
          <li>Some battles bring enemy reinforcements on set turns: from the far edge, or out of tents, crypts, dens, portals and guardhouses. The war room shows the schedule; badges on buildings count down the turns.</li>
          <li>They arrive after the enemy's move. A turn ahead, red tiles mark where they will appear: a unit standing on one <b>blocks</b> that arrival, but takes 10 damage.</li>
          <li>Destroy a building and everything it had left to send is cut off.</li>
        </ul>
        <h4>Controls</h4>
        <ul>
          <li>Each army's <b>Supply</b> shows in a small badge by its back row (the enemy's top right, yours bottom left): in battle what is still standing of what took the field, in the War Room what you field against what the enemy brings. Challenge cards and the Hall of Fame show it too.</li>
          <li>The battle's goals stay pinned at the top of the panel under the board: the mission and how it stands, gold still in the field, bonus goals and their rewards, and the next reinforcements. Their full wording is further down, under Mission details.</li>
          <li>Tap a rock, a chest, the shrine, a hazard or a red landing tile to see what it does.</li>
          <li>In the war room, tap a unit (or hold its card) for its full loadout and stats; long-press a unit on the board to pick it up (it pops up and wriggles in your hand) and drag it to an open blue tile to move it (the board holds still while you drag). Tap an empty blue tile, then a unit card, to put that unit there. Units never swap places. In battle, long-press any unit for everything about it.</li>
          <li>Pinch to zoom and drag to move the board.</li>
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
    if (!p) return challengeScreen();
    switch (p.type) {
      case 'battle':
        return warRoom();
      case 'reward':
        return rewardScreen();
      case 'shop':
        return shopScreen();
      case 'event':
        return eventScreen();
      case 'summit':
        return summitScreen();
    }
    return challengeScreen();
  }

  function init() {
    $('#modal').addEventListener('click', (e) => {
      if (e.target.id === 'modal') closeSheet();
    });
    root.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !$('#modal').hidden) closeSheet();
    });
    root.addEventListener('resize', updateRotateHint);
    // A message box goes the moment you tap it (and the tap stops there), or when you tap
    // anything else (that tap still does what it does).
    const toastEl = $('#toast');
    toastEl.addEventListener('click', (e) => {
      e.stopPropagation();
      hideToast();
    });
    root.addEventListener('pointerdown', (e) => !toastEl.hidden && !toastEl.contains(e.target) && hideToast(), true);
    // An enchantment chip, wherever a unit card shows one: tap it for what it does.
    root.document.addEventListener('click', (e) => {
      const chip = e.target.closest && e.target.closest('[data-ench], [data-mastery]');
      const ench = chip && chip.dataset.ench && ENCHANTS[chip.dataset.ench];
      const mast = chip && chip.dataset.mastery && MASTERY[chip.dataset.mastery];
      if (!ench && !mast) return;
      e.stopPropagation();
      e.preventDefault();
      if (ench) toast(`${ench.name} (enchantment): ${ench.desc}`, 4500);
      else toast(`${mast.name} (Level 3 mastery): ${mast.desc}`, 4500);
    }, true);
    const unlock = () => {
      if (AG.Audio) AG.Audio.unlock();
      if (AG.Music) AG.Music.kick();
    };
    root.addEventListener('pointerdown', unlock, { once: true });
    root.addEventListener('keydown', unlock, { once: true });
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
