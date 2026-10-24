/* Headless helpers: load the engine into Node, auto-place armies, print
   battles as text. Used by the simulation and balance scripts. */
'use strict';
const path = require('path');

const ENGINE_FILES = [
  'js/core/util.js',
  'js/core/board.js',
  'js/core/battle.js',
  'js/data/passives.js',
  'js/data/abilities.js',
  'js/data/units.js',
  'js/data/upgrades.js',
  'js/data/relics.js',
  'js/core/ai.js',
  'js/data/encounters.js',
  'js/data/encounters2.js',
  'js/data/events.js',
  'js/game/run.js',
];

function load() {
  if (globalThis.AG && globalThis.AG.__loaded) return globalThis.AG;
  const fs = require('fs');
  for (const f of ENGINE_FILES) {
    const p = path.join(__dirname, '..', f);
    if (fs.existsSync(p)) require(p);
  }
  globalThis.AG.__loaded = true;
  return globalThis.AG;
}

// Front ranks for fighters, back ranks for shooters and healers.
function autoPlace(AG, enc, entries) {
  const { board } = AG.parseBoard(enc.map, enc.legend);
  const cells = [];
  for (let i = 0; i < board.n; i++) if (board.deploy[i]) cells.push(i);
  const rows = [...new Set(cells.map((i) => (i / board.w) | 0))].sort((a, b) => a - b);
  const front = cells.filter((i) => ((i / board.w) | 0) === rows[0]);
  const back = cells.filter((i) => ((i / board.w) | 0) !== rows[0]);
  const mid = board.w / 2 - 0.5;
  const byCenter = (a, b) => Math.abs((a % board.w) - mid) - Math.abs((b % board.w) - mid);
  front.sort(byCenter);
  back.sort((a, b) => ((b / board.w) | 0) - ((a / board.w) | 0) || byCenter(a, b));
  back.reverse();
  back.sort(byCenter);
  const out = [];
  const used = new Set();
  for (const e of entries) {
    const role = AG.Units[e.def].role || 'melee';
    const wantFront = role === 'melee' || role === 'tank' || role === 'assassin';
    const pool = wantFront ? front.concat(back) : back.concat(front);
    const cell = pool.find((c) => !used.has(c));
    if (cell == null) break;
    used.add(cell);
    out.push(Object.assign({}, e, { x: cell % board.w, y: (cell / board.w) | 0 }));
  }
  return out;
}

function boardText(AG, s) {
  const b = s.board;
  const lines = [];
  for (let y = 0; y < b.h; y++) {
    let row = String(b.h - y).padStart(2) + ' ';
    for (let x = 0; x < b.w; x++) {
      const i = y * b.w + x;
      const id = s.occ[i];
      if (id) {
        const u = AG.B.U(s, id);
        const ch = (u.def[0] || '?');
        row += u.side === 0 ? ch.toUpperCase() : ch.toLowerCase();
      } else {
        const t = b.terr[i];
        row += t === 0 ? '.' : t === 1 ? '#' : t === 2 ? '~' : ' ';
      }
    }
    lines.push(row);
  }
  lines.push('   ' + [...Array(b.w)].map((_, i) => String.fromCharCode(97 + i)).join(''));
  return lines.join('\n');
}

function unitLine(AG, s, u) {
  const st = Object.keys(u.st).join(',');
  return (u.side === 0 ? 'P ' : 'E ') + u.name + '#' + u.uid + ' ' + AG.squareName(s.board, u.x, u.y) +
    ' hp ' + u.hp + '/' + u.maxHp + (u.shield ? '+' + u.shield : '') + ' atk ' + u.atk + ' spd ' + AG.B.spd(s, u) + (st ? ' [' + st + ']' : '');
}

function runBattle(AG, enc, army, opts) {
  opts = opts || {};
  const s = AG.B.create(enc, army, { relics: opts.relics || [], record: true });
  const log = opts.verbose ? console.log : () => {};
  log('== ' + enc.name + ' ==');
  log(boardText(AG, s));
  let steps = 0;
  const t0 = Date.now();
  let maxTurn = 0;
  while (!s.over && steps < 3000) {
    const t1 = Date.now();
    const r = AG.B.step(s);
    const dt = Date.now() - t1;
    if (dt > maxTurn) maxTurn = dt;
    steps++;
    if (r && r.kind === 'round') log('--- Round ' + s.round + ' ---');
    if (r && r.kind === 'turn') {
      const u = AG.B.U(s, r.uid);
      if (r.skipped) log('  ' + u.name + ' loses its turn.');
      else if (r.plan) log('  ' + (u.side === 0 ? '[P] ' : '[E] ') + u.name + ': ' + r.plan.reason + '  (' + dt + 'ms)');
      if (opts.events) for (const e of s.ev) if (e.type !== 'think' && e.type !== 'turn') log('      ' + JSON.stringify(e));
    }
    s.ev.length = 0;
    if (opts.boards && r && r.kind === 'turn') log(boardText(AG, s));
  }
  log('Result: ' + (s.winner === 0 ? 'VICTORY' : 'DEFEAT') + ' in ' + s.round + ' rounds, ' + steps + ' steps, ' + (Date.now() - t0) + 'ms (slowest turn ' + maxTurn + 'ms)');
  if (opts.verbose) for (const u of s.units) if (u.alive) log('   ' + unitLine(AG, s, u));
  return { s, winner: s.winner, rounds: s.round, ms: Date.now() - t0, maxTurn };
}

module.exports = { load, autoPlace, boardText, runBattle, unitLine };
