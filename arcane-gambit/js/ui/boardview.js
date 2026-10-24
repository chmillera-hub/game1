/* Board renderer: squares, pieces and every animation used in battle.
   Pieces are absolutely positioned and moved with transforms; effects are
   short-lived elements on an overlay. Animation helpers return promises and
   scale with this.k (1 = normal speed, 0.25 = 4x). */
(function (AG) {
  'use strict';
  const UI = AG.UI;
  const h = UI.h;
  const { FLOOR, WALL, PIT } = AG.TER;

  const VFX = {
    slash: '#fff3d6', stab: '#fff3d6', claw: '#ffd9c2', smash: '#ffe0b0', gore: '#ffd0a0', fist: '#fff3d6', cleave: '#ffe0b0',
    whirl: '#ffe0b0', lance: '#fff3d6', pierce: '#fff3d6', bite: '#ffb4b4', dart: '#f1e7cf', arrow: '#f1e7cf', rock: '#c9b9a6',
    shell: '#ffb36b', bolt: '#ffd27a', beam: '#ff7ad9', arcane: '#c4a7ff', fire: '#ff9d4d', frost: '#a5e6ff', lightning: '#fff27a',
    storm: '#bb93ff', shadow: '#c39be6', holy: '#fff1b8', smite: '#fff1b8', nature: '#a6e07c', thorn: '#a6e07c', psychic: '#ff9ee8',
    time: '#7fe0ff', goo: '#9fe08a', heal: '#86d08a', rally: '#f1d08a', taunt: '#f39185', bone: '#efe8d8', meteor: '#ff7a3d', blast: '#ffb36b',
  };
  UI.VFX = VFX;
  const MELEE = { slash: 1, stab: 1, claw: 1, smash: 1, gore: 1, fist: 1, cleave: 1, whirl: 1, lance: 1, pierce: 1, bite: 1 };

  function BoardView(opts) {
    this.opts = opts;
    this.board = opts.board;
    this.k = 1;
    this.cell = 56;
    this.tokens = new Map();
    this.build();
  }
  UI.BoardView = BoardView;

  BoardView.prototype.build = function () {
    const b = this.board;
    const theme = this.opts.theme || 'classic';
    this.cellsEl = h('div.cells');
    this.cellEls = [];
    for (let y = 0; y < b.h; y++) {
      for (let x = 0; x < b.w; x++) {
        const i = y * b.w + x;
        const t = b.terr[i];
        const cls = t === FLOOR ? 'floor ' + ((x + y) % 2 === 0 ? 'l' : 'd') : t === WALL ? 'wall' : t === PIT ? 'pit' : 'void';
        const c = h('div.cell', { class: cls, dataset: { x: String(x), y: String(y) } });
        this.cellEls.push(c);
        this.cellsEl.appendChild(c);
      }
    }
    this.tokensEl = h('div.tokens');
    this.fxEl = h('div.fx');
    this.boardEl = h('div.board', this.cellsEl, this.tokensEl, this.fxEl);
    this.filesEl = h('div.files');
    this.ranksEl = h('div.ranks');
    for (let x = 0; x < b.w; x++) this.filesEl.appendChild(h('span', String.fromCharCode(97 + x)));
    for (let y = 0; y < b.h; y++) this.ranksEl.appendChild(h('span', String(b.h - y)));
    this.el = h('div.board-frame.theme-' + theme, this.boardEl, this.filesEl, this.ranksEl);
    this.el.classList.add('theme-' + theme);
    const self = this;
    this.cellsEl.addEventListener('click', function (e) {
      const c = e.target.closest('.cell');
      if (!c || self.suppressClick) return;
      if (self.opts.onCell) self.opts.onCell(+c.dataset.x, +c.dataset.y, e);
    });
    this.setCell(this.opts.cell || 56);
  };

  BoardView.prototype.setCell = function (px) {
    this.cell = px;
    const b = this.board;
    this.el.style.setProperty('--cell', px + 'px');
    this.cellsEl.style.gridTemplateColumns = 'repeat(' + b.w + ', ' + px + 'px)';
    this.boardEl.style.width = b.w * px + 'px';
    this.boardEl.style.height = b.h * px + 'px';
    this.filesEl.style.gridTemplateColumns = 'repeat(' + b.w + ', ' + px + 'px)';
    this.ranksEl.style.gridTemplateRows = 'repeat(' + b.h + ', ' + px + 'px)';
    for (const [uid, t] of this.tokens) this.place(t, t.x, t.y);
  };

  // Size squares to the space available (and to the screen height).
  BoardView.prototype.fit = function (availW, maxH) {
    const b = this.board;
    const padW = availW < 520 ? 24 : 32, padH = availW < 520 ? 24 : 32;
    let c = Math.floor((availW - padW) / b.w);
    if (maxH) c = Math.min(c, Math.floor((maxH - padH) / b.h));
    c = Math.max(26, Math.min(this.opts.maxCell || 68, c));
    if (c !== this.cell) this.setCell(c);
  };

  BoardView.prototype.center = function (x, y) {
    return [(x + 0.5) * this.cell, (y + 0.5) * this.cell];
  };
  BoardView.prototype.cellAt = function (clientX, clientY) {
    const r = this.boardEl.getBoundingClientRect();
    const x = Math.floor((clientX - r.left) / this.cell), y = Math.floor((clientY - r.top) / this.cell);
    if (x < 0 || y < 0 || x >= this.board.w || y >= this.board.h) return null;
    return { x, y };
  };

  // ------------------------------------------------------- highlights
  BoardView.prototype.mark = function (cls, list) {
    for (const c of this.cellEls) c.classList.remove(cls);
    if (list) for (const i of list) if (this.cellEls[i]) this.cellEls[i].classList.add(cls);
  };
  BoardView.prototype.markDeploy = function () {
    const out = [];
    for (let i = 0; i < this.board.n; i++) if (this.board.deploy[i]) out.push(i);
    this.mark('deploy', out);
  };

  // ------------------------------------------------------------ tokens
  BoardView.prototype.place = function (t, x, y) {
    t.x = x; t.y = y;
    t.el.style.transform = 'translate(' + x * this.cell + 'px,' + y * this.cell + 'px)';
  };
  BoardView.prototype.makeToken = function (u) {
    const el = h('div.token.' + (u.side === 0 ? 'p' : 'e'), { role: 'button', tabindex: '-1' },
      h('div.piece', UI.icon(u)),
      h('div.stealth-veil'),
      h('div.sts'),
      h('div.rank'),
      h('div.bars', h('i'), h('b')),
      h('div.hpnum'),
    );
    const t = { uid: u.uid, el, x: u.x, y: u.y, side: u.side };
    const self = this;
    el.addEventListener('pointerdown', function (e) { self.onTokenDown(t, e); });
    el.addEventListener('click', function (e) {
      if (self.suppressClick) return;
      e.stopPropagation();
      if (self.opts.onToken) self.opts.onToken(t.uid, e);
    });
    this.tokensEl.appendChild(el);
    this.tokens.set(u.uid, t);
    this.place(t, u.x, u.y);
    this.updateToken(u);
    return t;
  };
  BoardView.prototype.updateToken = function (u) {
    const t = this.tokens.get(u.uid);
    if (!t) return;
    const el = t.el;
    el.classList.toggle('p', u.side === 0);
    el.classList.toggle('e', u.side !== 0);
    t.side = u.side;
    el.querySelector('.piece').textContent = UI.icon(u);
    el.classList.toggle('big', !!u.big || !!u.boss);
    el.classList.toggle('summoned', !!u.summoned && !u.object && !u.big);
    el.classList.toggle('object', !!u.object);
    const st = Array.isArray(u.st) ? u.st : Object.keys(u.st || {});
    el.classList.toggle('stealth', st.indexOf('stealth') >= 0);
    const icons = st.filter((k) => k !== 'stealth' && UI.STATUS[k]).slice(0, 4).map((k) => UI.STATUS[k].icon).join('');
    el.querySelector('.sts').textContent = icons;
    el.querySelector('.rank').textContent = u.rank ? '★'.repeat(u.rank) : '';
    const hpPct = Math.max(0, Math.min(100, (100 * u.hp) / u.maxHp));
    const shPct = Math.max(0, Math.min(100 - hpPct, (100 * (u.shield || 0)) / u.maxHp));
    el.querySelector('.bars i').style.width = hpPct + '%';
    const sb = el.querySelector('.bars b');
    sb.style.left = hpPct + '%';
    sb.style.width = shPct + '%';
    el.querySelector('.hpnum').textContent = u.hp + (u.shield ? '+' + u.shield : '');
    el.setAttribute('aria-label', u.name + ' ' + u.hp + ' of ' + u.maxHp + ' HP');
    t.data = u;
  };
  BoardView.prototype.removeToken = function (uid) {
    const t = this.tokens.get(uid);
    if (!t) return;
    if (t.el.parentNode) t.el.parentNode.removeChild(t.el);
    this.tokens.delete(uid);
  };
  // Make the pieces match a list of units exactly.
  BoardView.prototype.sync = function (units) {
    const seen = new Set();
    for (const u of units) {
      if (!u.alive && u.alive !== undefined) continue;
      seen.add(u.uid);
      const t = this.tokens.get(u.uid) || this.makeToken(u);
      if (t.x !== u.x || t.y !== u.y) this.place(t, u.x, u.y);
      t.el.style.opacity = '';
      this.updateToken(u);
    }
    for (const uid of Array.from(this.tokens.keys())) if (!seen.has(uid)) this.removeToken(uid);
  };
  BoardView.prototype.setFlag = function (cls, uid) {
    for (const [id, t] of this.tokens) t.el.classList.toggle(cls, id === uid);
  };

  // ------------------------------------------------------------ dragging
  BoardView.prototype.onTokenDown = function (t, e) {
    if (!this.opts.canDrag || !this.opts.canDrag(t.uid)) return;
    const self = this;
    const sx = e.clientX, sy = e.clientY;
    let dragging = false;
    const r0 = this.boardEl.getBoundingClientRect();
    function move(ev) {
      const dx = ev.clientX - sx, dy = ev.clientY - sy;
      if (!dragging && Math.abs(dx) + Math.abs(dy) > 8) {
        dragging = true;
        t.el.classList.add('dragging');
        try { t.el.setPointerCapture(e.pointerId); } catch (er) { /* ignore */ }
      }
      if (dragging) {
        const px = ev.clientX - r0.left - self.cell / 2, py = ev.clientY - r0.top - self.cell / 2;
        t.el.style.transform = 'translate(' + px + 'px,' + py + 'px)';
        const c = self.cellAt(ev.clientX, ev.clientY);
        self.mark('drop-ok', c && self.opts.canDrop && self.opts.canDrop(t.uid, c.x, c.y) ? [c.y * self.board.w + c.x] : null);
        ev.preventDefault();
      }
    }
    function up(ev) {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      window.removeEventListener('pointercancel', up);
      if (!dragging) return;
      t.el.classList.remove('dragging');
      self.mark('drop-ok', null);
      self.suppressClick = true;
      setTimeout(function () { self.suppressClick = false; }, 60);
      const c = self.cellAt(ev.clientX, ev.clientY);
      self.place(t, t.x, t.y);
      if (c && self.opts.onDrop) self.opts.onDrop(t.uid, c.x, c.y);
    }
    window.addEventListener('pointermove', move, { passive: false });
    window.addEventListener('pointerup', up);
    window.addEventListener('pointercancel', up);
  };

  // ---------------------------------------------------------- animations
  BoardView.prototype.d = function (ms) { return UI.reducedMotion() ? Math.min(ms, 60) * this.k : ms * this.k; };
  function done(anim) { return anim && anim.finished ? anim.finished.catch(function () {}) : Promise.resolve(); }
  const tr = (x, y, extra) => 'translate(' + x + 'px,' + y + 'px)' + (extra || '');

  BoardView.prototype.animMove = function (uid, to, kind, path) {
    const t = this.tokens.get(uid);
    if (!t) return Promise.resolve();
    const c = this.cell;
    const fx = t.x * c, fy = t.y * c, tx = to[0] * c, ty = to[1] * c;
    let anim;
    if (kind === 'leap') {
      const mx = (fx + tx) / 2, my = (fy + ty) / 2 - c * 0.6;
      anim = t.el.animate([
        { transform: tr(fx, fy, ' scale(1)') },
        { transform: tr(mx, my, ' scale(1.25)'), offset: 0.5 },
        { transform: tr(tx, ty, ' scale(1)') },
      ], { duration: this.d(360), easing: 'ease-in-out' });
    } else if (kind === 'blink') {
      anim = t.el.animate([
        { transform: tr(fx, fy), opacity: 1 },
        { transform: tr(fx, fy, ' scale(0.3)'), opacity: 0, offset: 0.45 },
        { transform: tr(tx, ty, ' scale(0.3)'), opacity: 0, offset: 0.55 },
        { transform: tr(tx, ty), opacity: 1 },
      ], { duration: this.d(340) });
    } else if (kind === 'walk' && path && path.length > 1) {
      const frames = [{ transform: tr(fx, fy) }];
      for (const p of path) frames.push({ transform: tr(p[0] * c, p[1] * c) });
      anim = t.el.animate(frames, { duration: this.d(Math.max(240, 130 * path.length)), easing: 'linear' });
    } else {
      const dist = Math.max(Math.abs(to[0] - t.x), Math.abs(to[1] - t.y));
      const dur = kind === 'push' ? 170 : Math.max(220, 90 * dist + 140);
      anim = t.el.animate([{ transform: tr(fx, fy) }, { transform: tr(tx, ty) }], { duration: this.d(dur), easing: kind === 'push' ? 'ease-out' : 'ease-in-out' });
    }
    this.place(t, to[0], to[1]);
    return done(anim);
  };

  BoardView.prototype.animSwap = function (a, b, pa, pb) {
    return Promise.all([this.animMove(a, pa, 'blink'), this.animMove(b, pb, 'blink')]);
  };

  BoardView.prototype.lunge = function (uid, at) {
    const t = this.tokens.get(uid);
    if (!t) return Promise.resolve();
    const c = this.cell;
    const fx = t.x * c, fy = t.y * c;
    const dx = Math.sign(at[0] - t.x) * c * 0.32, dy = Math.sign(at[1] - t.y) * c * 0.32;
    return done(t.el.animate([
      { transform: tr(fx, fy) }, { transform: tr(fx + dx, fy + dy, ' scale(1.08)'), offset: 0.4 }, { transform: tr(fx, fy) },
    ], { duration: this.d(240), easing: 'ease-out' }));
  };

  BoardView.prototype.projectile = function (from, to, vfx, lob) {
    const [x0, y0] = this.center(from[0], from[1]);
    const [x1, y1] = this.center(to[0], to[1]);
    const color = VFX[vfx] || '#ffd27a';
    const p = h('div.proj', { style: { color } });
    this.fxEl.appendChild(p);
    const dist = Math.hypot(to[0] - from[0], to[1] - from[1]);
    const dur = this.d(160 + 45 * dist);
    let frames;
    if (lob) {
      const mx = (x0 + x1) / 2, my = (y0 + y1) / 2 - this.cell * (0.6 + dist * 0.2);
      frames = [{ transform: tr(x0, y0) }, { transform: tr(mx, my, ' scale(1.4)'), offset: 0.5 }, { transform: tr(x1, y1) }];
    } else frames = [{ transform: tr(x0, y0) }, { transform: tr(x1, y1) }];
    const anim = p.animate(frames, { duration: dur, easing: lob ? 'ease-in-out' : 'linear' });
    return done(anim).then(function () { p.remove(); });
  };

  BoardView.prototype.zap = function (from, to, vfx) {
    const [x0, y0] = this.center(from[0], from[1]);
    const [x1, y1] = this.center(to[0], to[1]);
    const len = Math.hypot(x1 - x0, y1 - y0);
    const ang = Math.atan2(y1 - y0, x1 - x0);
    const z = h('div.zap', { style: { color: VFX[vfx] || VFX.lightning, left: x0 + 'px', top: y0 + 'px', width: len + 'px', transform: 'rotate(' + ang + 'rad)' } });
    this.fxEl.appendChild(z);
    const anim = z.animate([{ opacity: 0 }, { opacity: 1, offset: 0.2 }, { opacity: 1, offset: 0.6 }, { opacity: 0 }], { duration: this.d(300) });
    return done(anim).then(function () { z.remove(); });
  };

  BoardView.prototype.aoe = function (cells, r, vfx) {
    const c = this.cell;
    const color = VFX[vfx] || VFX.blast;
    const ps = [];
    for (const [x, y] of cells) {
      const size = (r * 2 + 1) * c;
      const ring = h('div.ring', { style: { color, left: (x - r) * c + 'px', top: (y - r) * c + 'px', width: size + 'px', height: size + 'px' } });
      this.fxEl.appendChild(ring);
      const anim = ring.animate([{ transform: 'scale(0.3)', opacity: 0 }, { transform: 'scale(1)', opacity: 0.95, offset: 0.45 }, { transform: 'scale(1.05)', opacity: 0 }], { duration: this.d(420), easing: 'ease-out' });
      ps.push(done(anim).then(function () { ring.remove(); }));
    }
    return Promise.all(ps);
  };

  BoardView.prototype.flash = function (uid, color) {
    const t = this.tokens.get(uid);
    if (!t) return Promise.resolve();
    const piece = t.el.querySelector('.piece');
    return done(piece.animate([{ filter: 'brightness(1)' }, { filter: 'brightness(2.2) drop-shadow(0 0 6px ' + (color || '#fff') + ')' }, { filter: 'brightness(1)' }], { duration: this.d(260) }));
  };
  BoardView.prototype.shake = function (uid) {
    const t = this.tokens.get(uid);
    if (!t) return Promise.resolve();
    const piece = t.el.querySelector('.piece');
    return done(piece.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-4px)' }, { transform: 'translateX(4px)' }, { transform: 'translateX(-2px)' }, { transform: 'translateX(0)' }], { duration: this.d(220) }));
  };

  BoardView.prototype.float = function (x, y, text, cls, lift) {
    const [cx, cy] = this.center(x, y);
    const f = h('div.float', { class: cls || 'note', style: { left: cx + 'px', top: cy - this.cell * 0.15 + 'px' } }, text);
    this.fxEl.appendChild(f);
    const rise = this.cell * (lift || 0.75);
    const anim = f.animate([
      { transform: 'translate(-50%,-50%) scale(0.7)', opacity: 0 },
      { transform: 'translate(-50%,-80%) scale(1.1)', opacity: 1, offset: 0.2 },
      { transform: 'translate(-50%,-' + (50 + (rise / this.cell) * 100) + '%) scale(1)', opacity: 0 },
    ], { duration: Math.max(500, this.d(900)), easing: 'ease-out' });
    done(anim).then(function () { f.remove(); });
  };
  BoardView.prototype.floatOn = function (uid, text, cls, lift) {
    const t = this.tokens.get(uid);
    if (t) this.float(t.x, t.y, text, cls, lift);
  };

  BoardView.prototype.callout = function (uid, text) {
    const t = this.tokens.get(uid);
    if (!t) return;
    const [cx, cy] = this.center(t.x, t.y);
    const el = h('div.callout', { style: { left: cx + 'px', top: cy - this.cell * 0.5 + 'px' } }, text);
    this.fxEl.appendChild(el);
    const anim = el.animate([{ opacity: 0, transform: 'translate(-50%,-80%)' }, { opacity: 1, transform: 'translate(-50%,-100%)', offset: 0.15 }, { opacity: 1, offset: 0.8 }, { opacity: 0 }], { duration: Math.max(700, this.d(1300)) });
    done(anim).then(function () { el.remove(); });
  };

  BoardView.prototype.banner = function (text, cls) {
    const el = h('div.banner' + (cls ? '.' + cls : ''), text);
    this.boardEl.appendChild(el);
    const anim = el.animate([{ opacity: 0, transform: 'translate(-50%,-30%) scale(0.9)' }, { opacity: 1, transform: 'translate(-50%,-50%) scale(1)', offset: 0.2 }, { opacity: 1, offset: 0.75 }, { opacity: 0, transform: 'translate(-50%,-60%)' }], { duration: Math.max(500, this.d(1000)) });
    return done(anim).then(function () { el.remove(); });
  };

  BoardView.prototype.fadeOut = function (uid, fall) {
    const t = this.tokens.get(uid);
    if (!t) return Promise.resolve();
    const self = this;
    const c = this.cell;
    const anim = t.el.animate([
      { transform: tr(t.x * c, t.y * c), opacity: 1 },
      { transform: tr(t.x * c, t.y * c + (fall ? c * 0.2 : 0), fall ? ' scale(0.1)' : ' scale(0.6)'), opacity: 0 },
    ], { duration: this.d(fall ? 420 : 360), easing: 'ease-in' });
    t.el.style.opacity = '0';
    return done(anim).then(function () { self.removeToken(uid); });
  };
  BoardView.prototype.fadeIn = function (u) {
    const t = this.tokens.get(u.uid) || this.makeToken(u);
    const c = this.cell;
    return done(t.el.animate([{ transform: tr(t.x * c, t.y * c, ' scale(0.2)'), opacity: 0 }, { transform: tr(t.x * c, t.y * c), opacity: 1 }], { duration: this.d(320), easing: 'ease-out' }));
  };
})(globalThis.AG = globalThis.AG || {});
