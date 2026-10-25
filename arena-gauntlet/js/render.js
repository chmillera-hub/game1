// Isometric board renderer and battle animator.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});
  const S = AG.Sprites;
  const { DIRS, UNITS } = AG.Data;

  const PALETTES = {
    grass: {
      a: '#6b9a46', b: '#618e40', edgeL: '#3f5d2a', edgeR: '#344f23', soil: '#5a4630', line: 'rgba(25,45,12,0.28)',
      water: '#3a78a3', waterHi: '#8cc6e8', lava: '#c9521d', lavaHi: '#ffb347', obstacle: 'rock',
    },
    swamp: {
      a: '#58754a', b: '#506b43', edgeL: '#33472c', edgeR: '#2a3b24', soil: '#463a2a', line: 'rgba(15,30,15,0.3)',
      water: '#2e5b5f', waterHi: '#7fb8b0', lava: '#c9521d', lavaHi: '#ffb347', obstacle: 'tree',
    },
    ember: {
      a: '#6c625b', b: '#625952', edgeL: '#433a35', edgeR: '#382f2b', soil: '#2f2622', line: 'rgba(20,10,5,0.32)',
      water: '#3a5f7a', waterHi: '#8cb6d0', lava: '#cf4f1b', lavaHi: '#ffc04d', obstacle: 'basalt',
    },
  };

  // How tall each act's obstacle is drawn, in sprite units (for tapping it).
  const OBSTACLE_HEIGHT = { rock: 24, tree: 44, basalt: 38 };

  const now = () => (root.performance ? root.performance.now() : Date.now());
  // Frame pacing: 30 frames a second while something moves, 10 when nothing does. A
  // tactics board needs no more, and phones stay cool.
  const BUSY_FRAME_MS = 33;
  // Poison is magenta everywhere (numbers, bubbles, the health bar), so it never reads as the
  // green of healing.
  const POISON = '#ff6fdc';
  // How far a unit's Barrier aura reaches (0: it has none).
  const auraOf = (u) => (u.traits && u.traits.has && u.traits.has('aura_barrier') ? AG.Engine.auraRadius(u) : 0);
  const POISON_FX = ['#ff6fdc', '#b23fd6', '#5e1f80'];
  const IDLE_FRAME_MS = 100;
  const lerp = (a, b, t) => a + (b - a) * t;
  const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

  class Board {
    constructor(canvas) {
      this.cv = canvas;
      this.g = canvas.getContext('2d');
      this.dpr = 1;
      this.cssW = 1;
      this.cssH = 1;
      this.w = 9;
      this.h = 9;
      this.terrain = new Array(81).fill(0);
      this.palette = PALETTES.grass;
      this.vis = new Map();
      // The War Room unit in your hand: { rid, up, down } (when it was picked up, put down).
      this.held = null;
      this.ov = {};
      this.fx = [];
      this.texts = [];
      this.time = 0;
      this.last = now();
      this.speed = 1;
      this.shakeT = 0;
      this.zoom = 1;
      this.panX = 0;
      this.panY = 0;
      this.loot = [];
      this.hold = null;
      this.tfx = [];
      this.exitX = null;
      this.staticCv = document.createElement('canvas');
      this.staticDirty = true;
      this.activeSide = null;
      this.onTap = null;
      this.onLongPress = null;
      this.sfx = (name) => AG.Audio && AG.Audio.play(name);
      this.running = false;
      this.reduced = !!(root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches);
      this.bindInput();
    }

    // ---------------------------------------------------------- layout

    setBoard(w, h, terrain, paletteName) {
      this.w = w;
      this.h = h;
      this.terrain = terrain.slice();
      this.palette = PALETTES[paletteName] || PALETTES.grass;
      this.paletteName = paletteName;
      this.layoutH = this.cssH;
      this.computeLayout();
      this.staticDirty = true;
    }

    resize(cssW, cssH) {
      // Twice the CSS pixels is plenty sharp for painted sprites, and far cheaper than 3x.
      const dpr = Math.min(root.devicePixelRatio || 1, 2);
      if (cssW === this.cssW && cssH === this.cssH && dpr === this.dpr) return;
      // Only the height changed (the panel below grew or shrank): the board stays where it
      // is while it still fits, so picking a unit never nudges the view.
      const keep = this.layoutH && cssW === this.cssW && dpr === this.dpr;
      this.dpr = dpr;
      this.cssW = Math.max(1, cssW);
      this.cssH = Math.max(1, cssH);
      this.cv.width = Math.round(this.cssW * dpr);
      this.cv.height = Math.round(this.cssH * dpr);
      this.cv.style.width = this.cssW + 'px';
      this.cv.style.height = this.cssH + 'px';
      if (!keep) this.layoutH = this.cssH;
      this.computeLayout();
      if (keep && ((this.zoom === 1 && this.boardBottom > this.cssH + 1) || this.baseFor(this.cssH) !== this.baseTw)) {
        this.layoutH = this.cssH;
        this.computeLayout();
      }
      this.staticDirty = true;
    }

    // Tile width that fits the board in this width and height.
    baseFor(h) {
      const span = (this.w + this.h) / 2;
      return Math.max(8, Math.min((this.cssW - 6) / span, (h - 4) / (span * 0.5 + 0.17 + 0.92 + 0.1)));
    }

    computeLayout() {
      const W = this.w;
      const H = this.h;
      const span = (W + H) / 2;
      const ratio = 0.5;
      const depth = 0.17;
      const head = 0.92;
      const layoutH = this.layoutH || this.cssH;
      const base = this.baseFor(layoutH);
      this.baseTw = base;
      const tw = base * this.zoom;
      this.tw = tw;
      this.th = tw * ratio;
      this.depth = tw * depth;
      this.unit = tw / 48;
      const boardH = span * this.th + this.depth;
      const total = boardH + head * tw;
      this.boardW = span * tw;
      this.boardTotalH = total;
      const top = (layoutH - total) / 2 + head * tw;
      this.clampPan();
      this.ox = this.cssW / 2 - ((W - H) * tw) / 4 + this.panX;
      this.oy = top + this.th / 2 + this.panY;
      this.boardBottom = top - head * tw + total + this.panY;
    }

    // The board can be dragged anywhere, even mostly off screen, as long as a corner of it
    // (about two tiles) stays in view.
    clampPan() {
      const mx = Math.max(0, (this.boardW + this.cssW) / 2 - Math.min(this.boardW, this.tw * 2));
      const my = Math.max(0, (this.boardTotalH + this.cssH) / 2 - Math.min(this.boardTotalH, this.tw * 1.5));
      this.panX = Math.max(-mx, Math.min(mx, this.panX));
      this.panY = Math.max(-my, Math.min(my, this.panY));
    }

    setZoom(z, px, py) {
      z = Math.max(1, Math.min(2.6, z));
      const ax = px == null ? this.cssW / 2 : px;
      const ay = py == null ? this.cssH / 2 : py;
      const [gx, gy] = this.toGrid(ax, ay);
      this.zoom = z;
      if (z === 1) {
        this.panX = 0;
        this.panY = 0;
      }
      this.computeLayout();
      const [sx, sy] = this.center(gx, gy);
      this.panX += ax - sx;
      this.panY += ay - sy;
      this.computeLayout();
      this.staticDirty = true;
    }

    panBy(dx, dy) {
      this.panX += dx;
      this.panY += dy;
      this.computeLayout();
      this.staticDirty = true;
    }

    // Pan only as far as needed to bring a tile into view, away from the edges.
    ensureVisible(x, y) {
      if (this.zoom <= 1) return;
      const [sx, sy] = this.center(x, y);
      const mx = this.tw * 0.8;
      const top = this.tw * 1.4;
      const bottom = this.th * 1.2;
      let dx = 0;
      let dy = 0;
      if (sx < mx) dx = mx - sx;
      else if (sx > this.cssW - mx) dx = this.cssW - mx - sx;
      if (sy < top) dy = top - sy;
      else if (sy > this.cssH - bottom) dy = this.cssH - bottom - sy;
      if (dx || dy) this.panBy(dx, dy);
    }

    center(x, y) {
      return [this.ox + ((x - y) * this.tw) / 2, this.oy + ((x + y) * this.th) / 2];
    }

    toGrid(px, py) {
      const dx = (px - this.ox) / (this.tw / 2);
      const dy = (py - this.oy) / (this.th / 2);
      return [(dx + dy) / 2, (dy - dx) / 2];
    }

    // The tile under a point. A little past the board's edge (on its rim, or just beyond the
    // tip of a corner tile) still counts as the edge tile.
    tileAt(px, py) {
      const [fx, fy] = this.toGrid(px, py);
      const slack = 0.6;
      if (fx < -0.5 - slack || fy < -0.5 - slack || fx > this.w - 0.5 + slack || fy > this.h - 0.5 + slack) return null;
      const x = Math.min(this.w - 1, Math.max(0, Math.round(fx)));
      const y = Math.min(this.h - 1, Math.max(0, Math.round(fy)));
      return { x, y, fx, fy };
    }

    // ---------------------------------------------------------- input

    bindInput() {
      const pts = new Map();
      let tap = null;
      let pinch = null;
      let timer = 0;
      const pos = (e) => {
        const r = this.cv.getBoundingClientRect();
        return [e.clientX - r.left, e.clientY - r.top];
      };
      const cancelTap = () => {
        clearTimeout(timer);
        tap = null;
        this.ov.press = null;
      };
      this.cv.addEventListener('pointerdown', (e) => {
        this.touched = now();
        const [x, y] = pos(e);
        pts.set(e.pointerId, { x, y });
        try {
          this.cv.setPointerCapture(e.pointerId);
        } catch (err) {
          /* capture unsupported */
        }
        if (pts.size === 2) {
          cancelTap();
          const [a, b] = [...pts.values()];
          pinch = { d: Math.hypot(a.x - b.x, a.y - b.y) || 1, z: this.zoom };
          return;
        }
        if (pts.size > 2) return;
        tap = { x, y, lx: x, ly: y, long: false, panning: false };
        this.ov.press = this.hit(x, y);
        clearTimeout(timer);
        timer = setTimeout(() => {
          if (!tap || tap.panning) return;
          tap.long = true;
          this.ov.press = null;
          // A long press that picks something up starts a drag: the board stays put and
          // the finger carries it.
          if (this.onLongPress && this.onLongPress(this.hit(tap.x, tap.y)) === 'drag') tap.drag = true;
        }, 480);
      });
      this.cv.addEventListener('pointermove', (e) => {
        if (!pts.has(e.pointerId)) return;
        this.touched = now();
        const [x, y] = pos(e);
        pts.set(e.pointerId, { x, y });
        if (pinch && pts.size >= 2) {
          const [a, b] = [...pts.values()];
          const d = Math.hypot(a.x - b.x, a.y - b.y) || 1;
          this.setZoom(pinch.z * (d / pinch.d), (a.x + b.x) / 2, (a.y + b.y) / 2);
          return;
        }
        if (!tap) return;
        if (tap.drag) {
          tap.lx = x;
          tap.ly = y;
          if (this.onDragMove) this.onDragMove(this.hit(x, y));
          return;
        }
        if (!tap.panning && Math.hypot(x - tap.x, y - tap.y) > 10) {
          clearTimeout(timer);
          this.ov.press = null;
          tap.panning = true;
        }
        if (tap.panning) {
          this.panBy(x - tap.lx, y - tap.ly);
          tap.lx = x;
          tap.ly = y;
        }
      });
      const up = (e) => {
        pts.delete(e.pointerId);
        if (pinch) {
          if (pts.size < 2) pinch = null;
          tap = null;
          return;
        }
        clearTimeout(timer);
        const t = tap;
        tap = null;
        this.ov.press = null;
        if (t && t.drag) {
          if (this.onDragEnd) this.onDragEnd(e.type === 'pointercancel' ? null : this.hit(t.lx, t.ly), Math.hypot(t.lx - t.x, t.ly - t.y) > 10);
          return;
        }
        if (!t || t.long || t.panning || e.type === 'pointercancel') return;
        if (this.onTap) this.onTap(this.hit(t.x, t.y));
      };
      this.cv.addEventListener('pointerup', up);
      this.cv.addEventListener('pointercancel', up);
      this.cv.addEventListener('contextmenu', (e) => e.preventDefault());
      this.cv.addEventListener(
        'wheel',
        (e) => {
          e.preventDefault();
          this.touched = now();
          const [x, y] = pos(e);
          this.setZoom(this.zoom * (e.deltaY < 0 ? 1.12 : 1 / 1.12), x, y);
        },
        { passive: false }
      );
    }

    // What a tap at (px, py) points at: the tile under the finger and any unit sprite there.
    // What lies under a point: the tile, the front-most sprite, and every sprite there,
    // front to back (a unit can peek out from behind a bigger one).
    hit(px, py) {
      const tile = this.tileAt(px, py);
      const stack = [];
      const half = this.tw * 0.3;
      const under = (x, y, hgt) => {
        const [cx, cy] = this.center(x, y);
        return px >= cx - half && px <= cx + half && py <= cy + this.th * 0.35 && py >= cy - hgt;
      };
      const list = [...this.vis.values()].filter((v) => v.alpha > 0.3).sort((a, b) => b.x + b.y - (a.x + a.y) || b.x - a.x);
      for (const v of list) {
        if (under(v.x, v.y, (S.HEIGHT[v.type] || 40) * this.unit * (v.scale || 1))) stack.push({ x: Math.round(v.x), y: Math.round(v.y), uid: v.uid });
      }
      // Things drawn standing up that are not units: obstacles and loot, front to back. `d`
      // is how far the finger is from the middle of the drawing.
      const props = [];
      const prop = (x, y, hgt) => {
        if (!under(x, y, hgt)) return;
        const [cx, cy] = this.center(x, y);
        props.push({ x, y, d: Math.hypot(px - cx, py - (cy - hgt / 2)) });
      };
      const ob = OBSTACLE_HEIGHT[this.palette.obstacle] || 24;
      for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) if (this.terrain[y * this.w + x] === 1) prop(x, y, ob * this.unit);
      for (const l of this.loot) if (!l.taken) prop(l.x, l.y, 24 * this.unit);
      props.sort((a, b) => b.x + b.y - (a.x + a.y) || b.x - a.x);
      if (tile) {
        const [cx, cy] = this.center(tile.x, tile.y);
        tile.d = Math.hypot(px - cx, py - cy);
      }
      return { tile, unitTile: stack[0] || null, stack, props, px, py, grid: this.toGrid(px, py) };
    }

    // ---------------------------------------------------------- units

    syncFromState(s, opts) {
      const seen = new Set();
      for (const u of s.units) {
        seen.add(u.uid);
        let v = this.vis.get(u.uid);
        if (!u.alive) {
          if (v && !v.dying) this.vis.delete(u.uid);
          continue;
        }
        if (!v || v.type !== u.type || v.team !== u.team) {
          v = this.makeVis(u);
          this.vis.set(u.uid, v);
        }
        if (!v.moving) {
          v.x = u.x;
          v.y = u.y;
        }
        v.facing = u.facing;
        v.hp = u.hp;
        v.maxHp = u.maxHp;
        v.wait = u.wait;
        v.activated = u.activated;
        v.aura = auraOf(u);
        v.alpha = v.dying ? v.alpha : 1;
        this.copyStatus(v, u);
      }
      for (const uid of [...this.vis.keys()]) if (!seen.has(uid) && !(opts && opts.keep)) this.vis.delete(uid);
      this.tfx = (s.tfx || []).map((f) => Object.assign({}, f));
      this.exitX = s.units.some((u) => u.alive && u.traits && u.traits.has('cart')) ? s.cartExit : null;
      this.waves = s.waves ? AG.Engine.waveSummary(s) : [];
    }

    copyStatus(v, u) {
      v.para = u.para || 0;
      v.poison = !!u.poison;
      v.burn = !!u.burn;
      v.root = u.root || 0;
      v.weak = u.weak || 0;
      v.mark = u.mark || 0;
      v.frenzy = u.frenzy || 0;
      v.shield = u.shield || 0;
      v.level = u.level || 1;
    }

    makeVis(u) {
      const v = {
        uid: u.uid, type: u.type, team: u.team, x: u.x, y: u.y, facing: u.facing, hp: u.hp, maxHp: u.maxHp,
        wait: u.wait || 0, boss: !!u.boss, vip: !!u.vip,
        nonCombat: !!u.nonCombat, scenery: !!(u.traits && u.traits.has && u.traits.has('scenery')),
        alpha: 1, ox: 0, oy: 0, hop: 0, scale: 1, shake: 0, flash: 0,
        phase: (u.uid * 1.7) % 6.28, activated: !!u.activated, ghost: !!u.ghost, rid: u.rid,
        aura: auraOf(u),
      };
      this.copyStatus(v, u);
      return v;
    }

    clearUnits() {
      this.vis.clear();
      this.held = null;
      this.fx = [];
      this.texts = [];
      this.tfx = [];
      this.exitX = null;
      this.waves = [];
    }

    // Loot on the field and the shrine to hold, if the mission has them.
    setObjectives(loot, hold) {
      this.loot = (loot || []).map((l) => Object.assign({}, l));
      this.hold = hold ? Object.assign({ count: 0 }, hold) : null;
    }

    // ---------------------------------------------------------- loop

    // 30 frames a second while something moves (effects, numbers, a unit walking, a finger
    // on the board); otherwise 10, plenty for the idle bobbing.
    start() {
      if (this.running) return;
      this.running = true;
      this.last = now();
      this.lastDraw = 0;
      const loop = () => {
        if (!this.running) return;
        const t = now();
        if (t - this.lastDraw >= (this.busy(t) ? BUSY_FRAME_MS : IDLE_FRAME_MS) - 2) {
          this.frame();
          this.lastDraw = t;
        }
        this.raf = requestAnimationFrame(loop);
      };
      this.raf = requestAnimationFrame(loop);
    }

    busy(t) {
      if (this.fx.length || this.texts.length || this.shakeT > 0 || this.staticDirty || this.held || t - (this.touched || 0) < 400) return true;
      for (const v of this.vis.values()) if (v.moving || v.hop || v.ox || v.oy || v.shake || v.flash || v.alpha < 1) return true;
      return false;
    }

    stop() {
      this.running = false;
      cancelAnimationFrame(this.raf);
    }

    frame() {
      const t = now();
      const dt = Math.min(0.05, (t - this.last) / 1000);
      this.last = t;
      this.time += dt;
      const g = this.g;
      if (this.staticDirty) this.renderStatic();
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.clearRect(0, 0, this.cv.width, this.cv.height);
      let sx = 0;
      let sy = 0;
      if (this.shakeT > 0) {
        this.shakeT -= dt;
        const m = this.shakeT * 18 * this.dpr;
        sx = (Math.random() - 0.5) * m;
        sy = (Math.random() - 0.5) * m;
      }
      g.drawImage(this.staticCv, sx, sy);
      g.setTransform(this.dpr, 0, 0, this.dpr, sx, sy);
      this.drawLiquids(g);
      this.drawOverlays(g);
      this.drawWaveMarks(g);
      this.drawObjects(g);
      this.drawWaveBadges(g);
      this.drawSmoke(g);
      this.drawEffects(g, dt);
      this.drawTexts(g, dt);
      this.drawFacingArrows(g);
    }

    // ---------------------------------------------------------- static board

    diamondPath(g, cx, cy, inset) {
      const hw = this.tw / 2 - inset;
      const hh = this.th / 2 - inset / 2;
      g.beginPath();
      g.moveTo(cx, cy - hh);
      g.lineTo(cx + hw, cy);
      g.lineTo(cx, cy + hh);
      g.lineTo(cx - hw, cy);
      g.closePath();
    }

    renderStatic() {
      this.staticDirty = false;
      const c = this.staticCv;
      c.width = this.cv.width;
      c.height = this.cv.height;
      const g = c.getContext('2d');
      g.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
      const P = this.palette;
      const W = this.w;
      const H = this.h;
      // soft shadow under the board
      const [lx, ly] = this.center(0, H - 1);
      const [rx, ry] = this.center(W - 1, 0);
      const [bx, by] = this.center(W - 1, H - 1);
      g.fillStyle = 'rgba(0,0,0,0.28)';
      g.beginPath();
      g.ellipse((lx + rx) / 2, by + this.depth + this.th * 0.2, (rx - lx) / 2 + this.tw * 0.6, this.th * 1.2, 0, 0, Math.PI * 2);
      g.fill();
      void ly;
      void ry;
      for (let s = 0; s <= W + H - 2; s++) {
        for (let x = 0; x < W; x++) {
          const y = s - x;
          if (y < 0 || y >= H) continue;
          this.drawTile(g, x, y, P);
        }
      }
    }

    drawTile(g, x, y, P) {
      const [cx, cy] = this.center(x, y);
      const hw = this.tw / 2;
      const hh = this.th / 2;
      const d = this.depth;
      const t = this.terrain[y * this.w + x];
      if (y === this.h - 1) {
        g.fillStyle = P.edgeL;
        g.beginPath();
        g.moveTo(cx - hw, cy);
        g.lineTo(cx, cy + hh);
        g.lineTo(cx, cy + hh + d);
        g.lineTo(cx - hw, cy + d);
        g.closePath();
        g.fill();
        g.fillStyle = 'rgba(0,0,0,0.18)';
        g.fillRect(cx - hw, cy + d * 0.55, hw, 1);
      }
      if (x === this.w - 1) {
        g.fillStyle = P.edgeR;
        g.beginPath();
        g.moveTo(cx, cy + hh);
        g.lineTo(cx + hw, cy);
        g.lineTo(cx + hw, cy + d);
        g.lineTo(cx, cy + hh + d);
        g.closePath();
        g.fill();
      }
      let fill = (x + y) % 2 ? P.a : P.b;
      if (t === 2) fill = P.water;
      if (t === 3) fill = P.lava;
      this.diamondPath(g, cx, cy, 0);
      g.fillStyle = fill;
      g.fill();
      if (t === 0 || t === 1) {
        // grass tufts / speckles, deterministic per tile
        const seed = (x * 73 + y * 151) % 97;
        g.fillStyle = 'rgba(255,255,255,0.07)';
        for (let i = 0; i < 3; i++) {
          const px = cx + (((seed * (i + 3)) % 23) / 23 - 0.5) * hw;
          const py = cy + (((seed * (i + 7)) % 19) / 19 - 0.5) * hh * 0.9;
          g.fillRect(px, py, Math.max(1, this.tw * 0.03), Math.max(1, this.tw * 0.012));
        }
      }
      g.strokeStyle = P.line;
      g.lineWidth = 1;
      this.diamondPath(g, cx, cy, 0.5);
      g.stroke();
    }

    drawLiquids(g) {
      const P = this.palette;
      for (let y = 0; y < this.h; y++)
        for (let x = 0; x < this.w; x++) {
          const t = this.terrain[y * this.w + x];
          if (t !== 2 && t !== 3) continue;
          const [cx, cy] = this.center(x, y);
          const ph = this.time * (t === 3 ? 1.2 : 1.8) + x * 1.3 + y * 0.7;
          g.save();
          this.diamondPath(g, cx, cy, 1);
          g.clip();
          if (t === 3) {
            const gl = 0.25 + 0.15 * Math.sin(ph);
            g.fillStyle = 'rgba(255,190,80,' + gl + ')';
            g.beginPath();
            g.ellipse(cx + Math.sin(ph) * this.tw * 0.1, cy, this.tw * 0.22, this.th * 0.22, 0, 0, Math.PI * 2);
            g.fill();
            g.fillStyle = P.lavaHi;
            g.globalAlpha = 0.6;
            g.fillRect(cx - this.tw * 0.15 + Math.cos(ph * 0.7) * 3, cy + Math.sin(ph) * 2, this.tw * 0.06, this.tw * 0.03);
            g.globalAlpha = 1;
          } else {
            g.strokeStyle = P.waterHi;
            g.globalAlpha = 0.45;
            g.lineWidth = 1;
            for (let i = 0; i < 2; i++) {
              const o = ((ph * 0.25 + i * 0.5) % 1) - 0.5;
              g.beginPath();
              g.moveTo(cx - this.tw * 0.18 + o * this.tw * 0.2, cy + (i - 0.5) * this.th * 0.4);
              g.lineTo(cx + this.tw * 0.02 + o * this.tw * 0.2, cy + (i - 0.5) * this.th * 0.4 + this.th * 0.08);
              g.stroke();
            }
            g.globalAlpha = 1;
          }
          g.restore();
        }
    }

    // ---------------------------------------------------------- overlays

    tileFill(g, x, y, fill, stroke, inset, lw) {
      const [cx, cy] = this.center(x, y);
      this.diamondPath(g, cx, cy, inset == null ? 2 : inset);
      if (fill) {
        g.fillStyle = fill;
        g.fill();
      }
      if (stroke) {
        g.strokeStyle = stroke;
        g.lineWidth = lw || 1.5;
        g.stroke();
      }
    }

    drawOverlays(g) {
      const o = this.ov;
      const pulse = 0.5 + 0.5 * Math.sin(this.time * 5);
      this.drawAuras(g);
      if (this.hold) this.drawHold(g);
      if (this.exitX != null) this.drawExit(g);
      this.drawHazards(g);
      if (o.deploy)
        for (const [x, y] of o.deploy) this.tileFill(g, x, y, 'rgba(90,160,255,0.16)', 'rgba(150,200,255,0.55)', 3, 1);
      if (o.danger)
        for (const [x, y, lvl] of o.danger) this.tileFill(g, x, y, lvl > 1 ? 'rgba(200,60,220,0.2)' : 'rgba(230,50,40,0.22)', null, 1);
      if (o.range) for (const [x, y] of o.range) this.tileFill(g, x, y, 'rgba(255,45,35,0.34)', 'rgba(255,110,90,0.85)', 3, 1.3);
      if (o.move) for (const [x, y] of o.move) this.tileFill(g, x, y, 'rgba(70,150,255,0.3)', 'rgba(150,205,255,0.85)', 2.5, 1.2);
      if (o.heal) for (const [x, y] of o.heal) this.tileFill(g, x, y, 'rgba(90,220,120,0.22)', 'rgba(140,240,160,0.6)', 2.5, 1);
      if (o.targets)
        for (const [x, y] of o.targets) this.tileFill(g, x, y, 'rgba(255,70,50,' + (0.18 + pulse * 0.14) + ')', 'rgba(255,140,120,0.95)', 2.5, 1.5);
      if (o.aoe)
        for (const [x, y, kind] of o.aoe)
          this.tileFill(g, x, y, kind === 'ally' ? 'rgba(255,200,40,0.5)' : kind === 'heal' ? 'rgba(110,240,140,0.45)' : 'rgba(255,150,40,0.45)', 'rgba(255,230,160,0.9)', 1.5, 1.4);
      if (o.path && o.path.length > 1) {
        g.fillStyle = 'rgba(230,245,255,0.9)';
        for (let i = 1; i < o.path.length; i++) {
          const [cx, cy] = this.center(o.path[i].x, o.path[i].y);
          g.beginPath();
          g.arc(cx, cy, Math.max(1.5, this.tw * 0.05), 0, Math.PI * 2);
          g.fill();
        }
      }
      if (o.select) this.tileFill(g, o.select[0], o.select[1], 'rgba(255,215,90,0.25)', 'rgba(255,220,110,' + (0.6 + pulse * 0.4) + ')', 1.5, 2);
      if (o.ghost) this.tileFill(g, o.ghost[0], o.ghost[1], 'rgba(255,255,255,0.18)', 'rgba(255,255,255,0.7)', 2, 1.2);
      if (o.press && o.press.tile) this.tileFill(g, o.press.tile.x, o.press.tile.y, 'rgba(255,255,255,0.15)', 'rgba(255,255,255,0.75)', 2, 1.2);
      if (this.focus) this.drawFocus(g);
    }

    // Barrier Ward auras: the ground they cover, tinted (cyan for yours, rose for the
    // enemy's) with a thin rim. Still, so it costs next to nothing to draw. Overlapping
    // auras of one side merge into one area.
    drawAuras(g) {
      const by = { P: [], E: [] };
      for (const v of this.vis.values()) if (v.aura && !v.dying && by[v.team]) by[v.team].push(v);
      if (!by.P.length && !by.E.length) return;
      const hw = this.tw / 2;
      const hh = this.th / 2;
      for (const team of ['P', 'E']) {
        const wards = by[team];
        if (!wards.length) continue;
        const inside = (x, y) => x >= 0 && y >= 0 && x < this.w && y < this.h && wards.some((v) => Math.abs(v.x - x) + Math.abs(v.y - y) <= v.aura);
        const tiles = [];
        for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) if (inside(x, y)) tiles.push([x, y]);
        g.beginPath();
        for (const [x, y] of tiles) {
          const [cx, cy] = this.center(x, y);
          g.moveTo(cx, cy - hh);
          g.lineTo(cx + hw, cy);
          g.lineTo(cx, cy + hh);
          g.lineTo(cx - hw, cy);
          g.closePath();
        }
        g.fillStyle = team === 'P' ? 'rgba(120,235,255,0.17)' : 'rgba(255,110,170,0.15)';
        g.fill();
        // The rim: tile edges with no aura tile on the other side.
        g.beginPath();
        for (const [x, y] of tiles) {
          const [cx, cy] = this.center(x, y);
          if (!inside(x + 1, y)) (g.moveTo(cx + hw, cy), g.lineTo(cx, cy + hh));
          if (!inside(x - 1, y)) (g.moveTo(cx, cy - hh), g.lineTo(cx - hw, cy));
          if (!inside(x, y + 1)) (g.moveTo(cx, cy + hh), g.lineTo(cx - hw, cy));
          if (!inside(x, y - 1)) (g.moveTo(cx, cy - hh), g.lineTo(cx + hw, cy));
        }
        // Dashed, so it never reads as the deployment zone's tile outlines.
        g.strokeStyle = team === 'P' ? 'rgba(175,245,255,0.95)' : 'rgba(255,160,205,0.9)';
        g.lineWidth = 2.2;
        g.setLineDash([this.tw * 0.12, this.tw * 0.08]);
        g.stroke();
        g.setLineDash([]);
      }
    }

    // The player's priority target: a pulsing amber crosshair.
    drawFocus(g) {
      const [cx, cy] = this.center(this.focus.x, this.focus.y);
      const p = 0.5 + 0.5 * Math.sin(this.time * 4);
      const rx = this.tw * (0.34 + 0.05 * p);
      const ry = this.th * (0.34 + 0.05 * p);
      g.save();
      g.strokeStyle = 'rgba(255,170,40,' + (0.7 + 0.3 * p) + ')';
      g.fillStyle = 'rgba(255,170,40,' + (0.1 + 0.08 * p) + ')';
      g.lineWidth = Math.max(1.5, this.tw * 0.035);
      g.beginPath();
      g.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      g.fill();
      g.stroke();
      g.beginPath();
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        g.moveTo(cx + dx * rx * 0.7, cy + dy * ry * 0.7);
        g.lineTo(cx + dx * rx * 1.3, cy + dy * ry * 1.3);
      }
      g.stroke();
      g.restore();
    }

    drawHold(g) {
      const h = this.hold;
      const [cx, cy] = this.center(h.x, h.y);
      const p = 0.5 + 0.5 * Math.sin(this.time * 3);
      g.save();
      g.strokeStyle = 'rgba(255,214,110,' + (0.55 + 0.35 * p) + ')';
      g.fillStyle = 'rgba(255,214,110,' + (0.12 + 0.1 * p) + ')';
      g.lineWidth = Math.max(1.5, this.tw * 0.04);
      g.beginPath();
      g.ellipse(cx, cy, this.tw * 0.36, this.th * 0.36, 0, 0, Math.PI * 2);
      g.fill();
      g.stroke();
      g.beginPath();
      g.ellipse(cx, cy, this.tw * 0.22, this.th * 0.22, 0, 0, Math.PI * 2);
      g.stroke();
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2 + this.time * 0.4;
        g.fillStyle = 'rgba(255,230,160,0.9)';
        g.fillRect(cx + Math.cos(a) * this.tw * 0.29 - 1, cy + Math.sin(a) * this.th * 0.29 - 1, 2, 2);
      }
      const label = h.count + '/' + h.need;
      g.font = '800 ' + Math.round(Math.max(10, this.tw * 0.2)) + 'px "Alegreya Sans", system-ui, sans-serif';
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.lineWidth = 3;
      g.strokeStyle = 'rgba(15,10,20,0.85)';
      g.strokeText(label, cx, cy + this.th * 0.62);
      g.fillStyle = '#ffe3a0';
      g.fillText(label, cx, cy + this.th * 0.62);
      g.restore();
    }

    // The left edge loot wagons flee toward.
    drawExit(g) {
      const k = 0.5 + 0.5 * Math.sin(this.time * 3);
      for (let y = 0; y < this.h; y++) {
        const x = this.exitX;
        if (this.terrain[y * this.w + x] !== 0) continue;
        this.tileFill(g, x, y, 'rgba(255,200,80,' + (0.08 + 0.06 * k) + ')', 'rgba(255,210,120,0.35)', 3, 1);
        const [cx, cy] = this.center(x, y);
        const [ax, ay] = this.center(x - 0.35, y);
        g.strokeStyle = 'rgba(255,220,140,' + (0.45 + 0.35 * k) + ')';
        g.lineWidth = Math.max(1.2, this.tw * 0.035);
        g.beginPath();
        g.moveTo(cx + (cx - ax) * 0.2, cy + (cy - ay) * 0.2 - this.th * 0.12);
        g.lineTo(ax, ay);
        g.lineTo(cx + (cx - ax) * 0.2, cy + (cy - ay) * 0.2 + this.th * 0.12);
        g.stroke();
      }
    }

    // Fire and caltrops lie on the ground; smoke is drawn over the units.
    drawHazards(g) {
      for (const f of this.tfx) {
        const [cx, cy] = this.center(f.x, f.y);
        if (f.kind === 'fire') {
          const ph = this.time * 6 + f.x * 1.7 + f.y;
          this.tileFill(g, f.x, f.y, 'rgba(255,110,30,' + (0.22 + 0.08 * Math.sin(ph)) + ')', 'rgba(255,170,60,0.55)', 2, 1);
          for (let i = 0; i < 3; i++) {
            const fx = cx + (i - 1) * this.tw * 0.14;
            const fh = this.tw * (0.16 + 0.06 * Math.sin(ph + i * 2));
            g.fillStyle = i === 1 ? 'rgba(255,220,120,0.85)' : 'rgba(255,120,40,0.8)';
            g.beginPath();
            g.moveTo(fx - this.tw * 0.05, cy + this.th * 0.05);
            g.quadraticCurveTo(fx, cy - fh, fx + this.tw * 0.05, cy + this.th * 0.05);
            g.fill();
          }
        } else if (f.kind === 'caltrops') {
          g.strokeStyle = f.team === 'P' ? 'rgba(150,200,255,0.9)' : 'rgba(255,150,140,0.9)';
          g.lineWidth = Math.max(1, this.tw * 0.025);
          for (let i = 0; i < 5; i++) {
            const a = i * 1.26 + f.x;
            const px = cx + Math.cos(a) * this.tw * 0.15;
            const py = cy + Math.sin(a) * this.th * 0.15;
            const s = this.tw * 0.04;
            g.beginPath();
            g.moveTo(px - s, py);
            g.lineTo(px + s, py);
            g.moveTo(px, py - s * 1.3);
            g.lineTo(px, py + s * 0.4);
            g.stroke();
          }
        }
      }
    }

    drawSmoke(g) {
      for (const f of this.tfx) {
        if (f.kind !== 'smoke') continue;
        const [cx, cy] = this.center(f.x, f.y);
        for (let i = 0; i < 4; i++) {
          const a = this.time * 0.6 + i * 1.6 + f.x * 0.9 + f.y * 0.4;
          const px = cx + Math.cos(a) * this.tw * 0.14;
          const py = cy - this.tw * (0.12 + 0.1 * i) + Math.sin(a * 1.3) * this.th * 0.12;
          g.fillStyle = 'rgba(205,210,220,' + (0.22 - i * 0.03) + ')';
          g.beginPath();
          g.ellipse(px, py, this.tw * (0.3 - i * 0.03), this.th * (0.42 - i * 0.04), 0, 0, Math.PI * 2);
          g.fill();
        }
      }
    }

    // Tiles where reinforcements land after the enemy's next move, with a ghost of who is coming.
    drawWaveMarks(g) {
      if (!this.waves || !this.waves.length) return;
      const pulse = 0.5 + 0.5 * Math.sin(this.time * 4);
      const occupied = new Map();
      for (const v of this.vis.values()) if (v.alpha > 0.5) occupied.set(Math.round(v.x) + ',' + Math.round(v.y), v);
      for (const w of this.waves) {
        if (!w.marks) continue;
        w.marks.forEach(([x, y], k) => {
          const o = occupied.get(x + ',' + y);
          const blocking = o && o.team !== w.team;
          this.tileFill(
            g, x, y,
            blocking ? 'rgba(255,214,106,' + (0.16 + 0.1 * pulse) + ')' : 'rgba(255,70,50,' + (0.14 + 0.1 * pulse) + ')',
            blocking ? 'rgba(255,224,140,0.95)' : 'rgba(255,120,90,' + (0.55 + 0.35 * pulse) + ')',
            2.5, 1.5
          );
          if (o) return;
          const type = w.types[k];
          const [cx, cy] = this.center(x, y);
          g.save();
          g.globalAlpha = 0.3 + 0.08 * pulse;
          g.translate(cx, cy);
          g.scale(w.team === 'E' ? -this.unit : this.unit, this.unit);
          S.drawUnit(g, type, w.team, 'front', this.time, null);
          g.restore();
          const top = cy - (S.HEIGHT[type] || 40) * this.unit - this.tw * (0.1 + 0.06 * pulse);
          const c = this.tw * 0.09;
          g.save();
          g.strokeStyle = 'rgba(255,150,120,' + (0.65 + 0.35 * pulse) + ')';
          g.lineWidth = Math.max(1.5, this.tw * 0.04);
          g.lineCap = 'round';
          g.beginPath();
          g.moveTo(cx - c, top - c);
          g.lineTo(cx, top);
          g.lineTo(cx + c, top - c);
          g.stroke();
          g.restore();
        });
      }
    }

    // A countdown over each building that still has reinforcements to send.
    drawWaveBadges(g) {
      if (!this.waves || !this.waves.length) return;
      const next = new Map();
      // A marked wave lands after the enemy's next move: show it as imminent.
      for (const w of this.waves) if (w.src) next.set(w.src, Math.min(next.has(w.src) ? next.get(w.src) : 99, w.marks ? 0 : w.in));
      for (const [uid, n] of next) {
        const v = this.vis.get(uid);
        if (!v || v.alpha < 0.3) continue;
        const [cx, cy] = this.center(v.x, v.y);
        const top = cy - (S.HEIGHT[v.type] || 40) * this.unit * (v.scale || 1);
        const r = Math.max(7, this.tw * 0.12);
        const by = top - Math.max(3, this.tw * 0.075) - 4 - r * 1.3;
        const soon = n <= 0;
        g.save();
        g.fillStyle = soon ? '#c93c36' : '#2b2230';
        g.strokeStyle = soon ? '#ffd0c8' : '#ff9a8a';
        g.lineWidth = 1.5;
        g.beginPath();
        g.arc(cx, by, r, 0, Math.PI * 2);
        g.fill();
        g.stroke();
        g.fillStyle = '#ffffff';
        g.font = '800 ' + Math.round(r * 1.25) + 'px "Alegreya Sans", system-ui, sans-serif';
        g.textAlign = 'center';
        g.textBaseline = 'middle';
        g.fillText(soon ? '!' : String(n), cx, by + 0.5);
        g.restore();
      }
    }

    drawLootItem(g, l) {
      const [cx, cy] = this.center(l.x, l.y);
      g.save();
      g.translate(cx, cy);
      g.scale(this.unit, this.unit);
      S.ellipse(g, 0, 1, 12, 5, 'rgba(0,0,0,0.25)', 0);
      S.drawLoot(g, l.kind, this.time);
      g.restore();
    }

    // ---------------------------------------------------------- held unit

    // Pick a War Room unit up (its rid) or put it down (null). Held, it pops up off its tile
    // and wriggles, so it shows from under the finger; put down, it drops back with a bump.
    carry(rid) {
      const h = this.held;
      if (rid) {
        if (!h || h.rid !== rid || h.down != null) this.held = { rid, up: this.time, down: null };
      } else if (h && h.down == null) h.down = this.time;
    }

    // How a held unit is drawn this frame: raised, a little bigger, rocking side to side.
    carryPose(v) {
      const h = this.held;
      if (!h || v.rid == null || v.rid !== h.rid) return null;
      const t = this.time;
      const tw = this.tw;
      if (h.down != null) {
        const d = (t - h.down) / 0.18;
        if (d >= 1) {
          this.held = null;
          this.particles(v.x, v.y, 6, ['#c9b9a0', '#8a7a64', '#e8dcc8'], { lift: 2, rise: 0.4, speed: 0.5, max: 0.4 });
          return null;
        }
        const e = (1 - d) * (1 - d);
        return { lift: e * tw * 0.5, dx: 0, rot: 0, scale: 1 + 0.14 * e };
      }
      // Up with a little overshoot, then the wriggle.
      const k = Math.min(1, (t - h.up) / 0.16);
      const e = 1 + 2.2 * Math.pow(k - 1, 3) + 1.2 * Math.pow(k - 1, 2);
      return {
        lift: e * tw * (0.5 + 0.05 * Math.sin(t * 8.5)),
        dx: e * tw * 0.035 * Math.sin(t * 23),
        rot: e * 0.16 * Math.sin(t * 17),
        scale: 1 + 0.14 * e,
      };
    }

    // ---------------------------------------------------------- objects (units + obstacles)

    drawObjects(g) {
      const items = [];
      for (let y = 0; y < this.h; y++)
        for (let x = 0; x < this.w; x++) if (this.terrain[y * this.w + x] === 1) items.push({ k: x + y, x, obstacle: true, y });
      for (const v of this.vis.values()) {
        v.pose = this.carryPose(v);
        // In the hand, it is above the board: drawn last.
        items.push({ k: v.pose ? 1e9 : v.x + v.y + 0.01, x: v.x, v });
      }
      for (const l of this.loot) if (!l.taken) items.push({ k: l.x + l.y, x: l.x, loot: l });
      items.sort((a, b) => a.k - b.k || a.x - b.x);
      const bars = [];
      for (const it of items) {
        if (it.obstacle) this.drawObstacle(g, it.x, it.y);
        else if (it.loot) this.drawLootItem(g, it.loot);
        else {
          this.drawUnit(g, it.v);
          if (!it.v.ghost && (!it.v.scenery || it.v.hp < it.v.maxHp)) bars.push(it.v);
        }
      }
      for (const v of bars) this.drawBar(g, v);
    }

    drawObstacle(g, x, y) {
      const [cx, cy] = this.center(x, y);
      const u = this.unit;
      g.save();
      g.translate(cx, cy);
      g.scale(u, u);
      const kind = this.palette.obstacle;
      S.ellipse(g, 0, 2, 17, 7, 'rgba(0,0,0,0.25)', 0);
      if (kind === 'tree') {
        S.rect(g, -3, -16, 6, 16, 1.5, '#5a4128');
        S.circle(g, -7, -22, 9, '#2c4f2c');
        S.circle(g, 7, -22, 9, '#2c4f2c');
        S.circle(g, 0, -31, 11, '#3a6436');
        S.circle(g, -3, -26, 7, '#467a40', 0);
      } else if (kind === 'basalt') {
        S.poly(g, [-14, 0, -11, -14, -6, -30, 1, -20, 5, -36, 11, -18, 15, 0], '#3a3330');
        S.poly(g, [-6, -30, -3, -14, 1, -20], '#4c4440', 0);
        S.line(g, 3, -16, 5, -8, 1, '#ff7a2a', false);
      } else {
        S.poly(g, [-15, 0, -13, -10, -6, -17, 3, -15, 9, -20, 15, -10, 16, 0], '#8b8780');
        S.poly(g, [-6, -17, 3, -15, 9, -20, 6, -12, -4, -11], '#a5a199', 0);
        S.poly(g, [-15, 0, -11, -4, 0, -2, 16, 0], '#6d6a64', 0);
      }
      g.restore();
    }

    drawUnit(g, v) {
      const [cx0, cy0] = this.center(v.x, v.y);
      const cx = cx0 + v.ox + (v.shake ? Math.sin(this.time * 70) * v.shake * this.tw * 0.04 : 0);
      // Shoved into water or lava: sunk to the waist, bobbing, until it climbs out.
      const cy = cy0 + v.oy + (v.dunk ? this.th * 0.35 + Math.sin(this.time * 12) * this.th * 0.04 : 0);
      const tc = S.TEAMS[v.team] || S.TEAMS.P;
      const u = this.unit;
      g.save();
      g.globalAlpha = v.alpha * (v.ghost ? 0.55 : 1) * (v.dunk ? 0.75 : 1);
      // shadow and base ring
      const rx = this.tw * 0.3;
      const ry = this.th * 0.3;
      g.fillStyle = 'rgba(0,0,0,0.3)';
      g.beginPath();
      g.ellipse(cx, cy + 1, rx * 1.05, ry * 1.05, 0, 0, Math.PI * 2);
      g.fill();
      const ready =
        this.activeSide === v.team && !v.nonCombat && v.wait === 0 && v.para === 0 && !v.activated && !v.ghost && (!this.readySet || this.readySet.has(v.uid));
      if (!v.nonCombat) {
        g.lineWidth = Math.max(1.5, this.tw * 0.045);
        g.strokeStyle = tc.ring;
        g.fillStyle = tc.glow + (ready ? 0.3 + 0.2 * Math.sin(this.time * 4) : 0.16) + ')';
        g.beginPath();
        g.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
        g.fill();
        g.stroke();
        if (ready) {
          g.strokeStyle = 'rgba(255,225,130,' + (0.55 + 0.35 * Math.sin(this.time * 4)) + ')';
          g.lineWidth = 1.2;
          g.beginPath();
          g.ellipse(cx, cy, rx + 2.5, ry + 1.5, 0, 0, Math.PI * 2);
          g.stroke();
        }
        if (v.frenzy > 0) {
          g.fillStyle = 'rgba(255,70,30,' + (0.18 + 0.12 * Math.sin(this.time * 9)) + ')';
          g.beginPath();
          g.ellipse(cx, cy, rx * 1.2, ry * 1.2, 0, 0, Math.PI * 2);
          g.fill();
        }
        if (v.facing >= 0) {
          const [dx, dy] = DIRS[v.facing];
          const vx = ((dx - dy) * this.tw) / 2;
          const vy = ((dx + dy) * this.th) / 2;
          const len = Math.hypot(vx, vy);
          const nx = vx / len;
          const ny = vy / len;
          const tipX = cx + nx * rx * 1.25;
          const tipY = cy + ny * ry * 1.6;
          const bX = cx + nx * rx * 0.75;
          const bY = cy + ny * ry * 0.85;
          const px = -ny * this.tw * 0.07;
          const py = nx * this.tw * 0.07;
          g.fillStyle = tc.light;
          g.strokeStyle = S.OUT;
          g.lineWidth = 1;
          g.beginPath();
          g.moveTo(tipX, tipY);
          g.lineTo(bX + px, bY + py * 0.5);
          g.lineTo(bX - px, bY - py * 0.5);
          g.closePath();
          g.fill();
          g.stroke();
        }
      }
      // sprite
      const f = v.facing;
      const view = f === 0 || f === 3 ? 'back' : 'front';
      const flip = f === 2 || f === 3 || (f < 0 && v.team === 'E');
      const p = v.pose;
      const lift = v.hop + (p ? p.lift : 0);
      g.translate(cx + (p ? p.dx : 0), cy - lift);
      if (p) {
        g.rotate(p.rot);
        g.scale(p.scale, p.scale);
      }
      if (flip) g.scale(-1, 1);
      this.drawSprite(g, v, view);
      g.restore();
      this.drawStatusFx(g, v, cx, cy - lift);
    }

    // A unit's painted sprite, feet at the origin, facing right.
    drawSprite(g, v, view) {
      const sc = this.unit * (v.scale || 1);
      g.scale(sc, sc);
      if (v.para > 0) g.filter = 'saturate(0.4) brightness(1.15)';
      S.drawUnit(g, v.type, v.team, view, this.time + v.phase, null);
      if (v.para > 0) g.filter = 'none';
    }

    // Roots, burns, shields and marks shown on the unit itself.
    drawStatusFx(g, v, cx, cy) {
      if (v.alpha < 0.3) return;
      const h = (S.HEIGHT[v.type] || 40) * this.unit * (v.scale || 1);
      const t = this.time + v.phase;
      g.save();
      g.globalAlpha = v.alpha;
      if (v.root > 0) {
        g.strokeStyle = '#5fbf4a';
        g.lineWidth = Math.max(1.2, this.tw * 0.03);
        for (let i = 0; i < 3; i++) {
          const a = (i / 3) * Math.PI * 2 + 0.4;
          const x0 = cx + Math.cos(a) * this.tw * 0.18;
          const y0 = cy + Math.sin(a) * this.th * 0.18;
          g.beginPath();
          g.moveTo(x0, y0);
          g.quadraticCurveTo(x0 + this.tw * 0.06, y0 - h * 0.25, x0 - this.tw * 0.02, y0 - h * 0.38);
          g.stroke();
        }
      }
      if (v.burn) {
        for (let i = 0; i < 2; i++) {
          const fx = cx + (i ? 0.12 : -0.1) * this.tw;
          const fy = cy - h * (0.35 + 0.2 * i);
          const fh = this.tw * (0.09 + 0.03 * Math.sin(t * 9 + i));
          g.fillStyle = 'rgba(255,140,40,0.9)';
          g.beginPath();
          g.moveTo(fx - fh * 0.45, fy);
          g.quadraticCurveTo(fx, fy - fh * 2, fx + fh * 0.45, fy);
          g.fill();
        }
      }
      if (v.shield > 0) {
        g.strokeStyle = 'rgba(140,200,255,' + (0.55 + 0.2 * Math.sin(t * 3)) + ')';
        g.fillStyle = 'rgba(140,200,255,0.12)';
        g.lineWidth = Math.max(1, this.tw * 0.025);
        g.beginPath();
        g.ellipse(cx, cy - h * 0.48, this.tw * 0.32, h * 0.58, 0, 0, Math.PI * 2);
        g.fill();
        g.stroke();
      }
      if (v.mark > 0) {
        const my = cy - h - this.tw * 0.32;
        const r = this.tw * 0.09;
        g.strokeStyle = '#ff5a4a';
        g.lineWidth = Math.max(1, this.tw * 0.025);
        g.beginPath();
        g.arc(cx, my, r, 0, Math.PI * 2);
        g.moveTo(cx - r * 1.5, my);
        g.lineTo(cx + r * 1.5, my);
        g.moveTo(cx, my - r * 1.5);
        g.lineTo(cx, my + r * 1.5);
        g.stroke();
      }
      g.restore();
    }

    drawBar(g, v) {
      if (v.alpha < 0.2 || v.type === 'shrub') {
        if (v.type === 'shrub' && v.alpha > 0.2) this.drawThinBar(g, v);
        return;
      }
      const [cx0, cy0] = this.center(v.x, v.y);
      const cx = cx0 + v.ox;
      const p = v.pose;
      const top = cy0 + v.oy - v.hop - (p ? p.lift : 0) - (S.HEIGHT[v.type] || 40) * this.unit * (v.scale || 1) * (p ? p.scale : 1);
      const bw = Math.max(18, this.tw * (v.boss ? 0.8 : v.vip ? 0.62 : 0.52));
      const bh = Math.max(3, this.tw * 0.075);
      const x = cx - bw / 2;
      const y = top - bh - 3;
      const frac = Math.max(0, Math.min(1, v.hp / v.maxHp));
      g.save();
      g.globalAlpha = v.alpha;
      g.fillStyle = 'rgba(12,10,16,0.85)';
      g.fillRect(x - 1, y - 1, bw + 2, bh + 2);
      g.fillStyle = v.poison ? '#c64fd0' : frac > 0.5 ? '#5fcf68' : frac > 0.25 ? '#e3b23c' : '#e0533d';
      g.fillRect(x, y, bw * frac, bh);
      g.fillStyle = 'rgba(255,255,255,0.25)';
      g.fillRect(x, y, bw * frac, Math.max(1, bh * 0.35));
      g.strokeStyle = (S.TEAMS[v.team] || S.TEAMS.P).ring;
      g.lineWidth = 1;
      g.strokeRect(x - 1, y - 1, bw + 2, bh + 2);
      const icon = Math.max(7, this.tw * 0.17);
      let ix = x - icon * 0.7;
      const iy = y + bh / 2;
      if (v.wait > 0) {
        g.fillStyle = '#2b3448';
        g.strokeStyle = '#9fb4d8';
        g.beginPath();
        g.arc(ix, iy, icon * 0.55, 0, Math.PI * 2);
        g.fill();
        g.stroke();
        g.fillStyle = '#e8eefc';
        g.font = '700 ' + Math.round(icon * 0.8) + 'px "Alegreya Sans", system-ui, sans-serif';
        g.textAlign = 'center';
        g.textBaseline = 'middle';
        g.fillText(String(v.wait), ix, iy + 0.5);
        ix -= icon * 1.15;
      }
      if (v.para > 0) {
        g.fillStyle = '#ffd84a';
        g.strokeStyle = S.OUT;
        g.lineWidth = 1;
        const s = icon * 0.5;
        g.beginPath();
        g.moveTo(ix + s * 0.2, iy - s);
        g.lineTo(ix - s * 0.6, iy + s * 0.1);
        g.lineTo(ix, iy + s * 0.1);
        g.lineTo(ix - s * 0.2, iy + s);
        g.lineTo(ix + s * 0.6, iy - s * 0.1);
        g.lineTo(ix, iy - s * 0.1);
        g.closePath();
        g.fill();
        g.stroke();
        ix -= icon;
      }
      const icons = [];
      if (v.root > 0) icons.push('#5fbf4a');
      if (v.burn) icons.push('#ff8a2a');
      if (v.weak > 0) icons.push('#b08cff');
      if (v.shield > 0) icons.push('#8cc8ff');
      for (const c of icons) {
        g.fillStyle = c;
        g.strokeStyle = S.OUT;
        g.lineWidth = 1;
        g.beginPath();
        g.arc(ix, iy, icon * 0.38, 0, Math.PI * 2);
        g.fill();
        g.stroke();
        ix -= icon * 0.95;
      }
      if (v.level > 1) {
        const s = Math.max(3, this.tw * 0.07);
        for (let i = 0; i < v.level; i++) this.star(g, x + bw + s * 1.4 + i * s * 1.9, iy, s);
      }
      if (v.boss || v.vip) {
        g.fillStyle = '#e6b83c';
        g.strokeStyle = S.OUT;
        const s = icon * 0.6;
        g.beginPath();
        g.moveTo(cx - s, y - 3);
        g.lineTo(cx - s, y - 3 - s);
        g.lineTo(cx - s / 2, y - 3 - s * 0.55);
        g.lineTo(cx, y - 3 - s * 1.15);
        g.lineTo(cx + s / 2, y - 3 - s * 0.55);
        g.lineTo(cx + s, y - 3 - s);
        g.lineTo(cx + s, y - 3);
        g.closePath();
        g.fill();
        g.stroke();
      }
      g.restore();
    }

    drawThinBar(g, v) {
      const [cx, cy] = this.center(v.x, v.y);
      const bw = this.tw * 0.36;
      const y = cy - 24 * this.unit;
      g.fillStyle = 'rgba(12,10,16,0.7)';
      g.fillRect(cx - bw / 2 - 1, y - 1, bw + 2, 4);
      g.fillStyle = '#8ccf5a';
      g.fillRect(cx - bw / 2, y, (bw * v.hp) / v.maxHp, 2);
    }

    star(g, x, y, r) {
      g.fillStyle = '#f1c94e';
      g.strokeStyle = S.OUT;
      g.lineWidth = 0.8;
      g.beginPath();
      for (let i = 0; i < 10; i++) {
        const a = -Math.PI / 2 + (i * Math.PI) / 5;
        const rr = i % 2 ? r * 0.45 : r;
        g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
      }
      g.closePath();
      g.fill();
      g.stroke();
    }

    // Four arrows around a unit for choosing its facing.
    drawFacingArrows(g) {
      const fa = this.ov.facing;
      if (!fa) return;
      const [cx, cy] = this.center(fa.x, fa.y);
      for (let d = 0; d < 4; d++) {
        const [dx, dy] = DIRS[d];
        const vx = ((dx - dy) * this.tw) / 2;
        const vy = ((dx + dy) * this.th) / 2;
        const ax = cx + vx * 0.95;
        const ay = cy + vy * 0.95;
        const len = Math.hypot(vx, vy);
        const nx = vx / len;
        const ny = vy / len;
        const s = this.tw * 0.22;
        const sel = fa.current === d;
        g.fillStyle = sel ? '#ffd86a' : 'rgba(250,244,230,0.85)';
        g.strokeStyle = S.OUT;
        g.lineWidth = 1.5;
        g.beginPath();
        g.moveTo(ax + nx * s, ay + ny * s * 0.9);
        g.lineTo(ax - ny * s * 0.7 - nx * s * 0.2, ay + nx * s * 0.45 - ny * s * 0.2);
        g.lineTo(ax + ny * s * 0.7 - nx * s * 0.2, ay - nx * s * 0.45 - ny * s * 0.2);
        g.closePath();
        g.fill();
        g.stroke();
      }
    }

    facingFromHit(hitInfo, ux, uy) {
      const [fx, fy] = hitInfo.grid;
      const dx = fx - ux;
      const dy = fy - uy;
      if (Math.abs(dx) < 0.25 && Math.abs(dy) < 0.25) return -1;
      return AG.Engine.dirFromDelta(dx, dy);
    }

    // ---------------------------------------------------------- effects

    addText(x, y, text, color, opts) {
      const [cx, cy] = this.center(x, y);
      const o = opts || {};
      const top = cy - (o.height || 40) * this.unit - this.tw * 0.15;
      this.texts.push({ x: cx + (o.dx || 0), y: top + (o.dy || 0), text, color, life: 0, max: o.max || 1.1, big: !!o.big });
    }

    drawTexts(g, dt) {
      const keep = [];
      for (const t of this.texts) {
        t.life += dt;
        if (t.life >= t.max) continue;
        keep.push(t);
        const k = t.life / t.max;
        const y = t.y - k * this.tw * 0.55;
        const a = k < 0.75 ? 1 : 1 - (k - 0.75) / 0.25;
        const pop = k < 0.12 ? 0.7 + k * 2.5 : 1;
        const size = Math.round(Math.max(11, this.tw * (t.big ? 0.36 : 0.27)) * pop);
        g.save();
        g.globalAlpha = a;
        g.font = '800 ' + size + 'px "Alegreya Sans", system-ui, sans-serif';
        g.textAlign = 'center';
        g.textBaseline = 'middle';
        g.lineWidth = Math.max(2.5, size * 0.2);
        g.strokeStyle = 'rgba(15,10,20,0.9)';
        g.strokeText(t.text, t.x, y);
        g.fillStyle = t.color;
        g.fillText(t.text, t.x, y);
        g.restore();
      }
      this.texts = keep;
    }

    drawEffects(g, dt) {
      const keep = [];
      for (const e of this.fx) {
        e.life += dt * (e.realtime ? 1 : this.speed);
        if (e.life >= e.max) {
          if (e.done) e.done();
          continue;
        }
        keep.push(e);
        e.draw(g, e.life / e.max, e);
      }
      this.fx = keep;
    }

    // Add an effect; resolves when it finishes.
    effect(max, draw, extra) {
      return new Promise((resolve) => {
        const e = Object.assign({ life: 0, max, draw, done: resolve }, extra || {});
        this.fx.push(e);
      });
    }

    wait(ms) {
      return new Promise((r) => setTimeout(r, ms / this.speed));
    }

    tween(ms, fn) {
      return this.effect(ms / 1000, (g, k) => fn(k));
    }

    pt(x, y, lift) {
      const [cx, cy] = this.center(x, y);
      return [cx, cy - (lift == null ? 18 : lift) * this.unit];
    }

    particles(x, y, n, colors, opts) {
      const o = opts || {};
      const [cx, cy] = this.pt(x, y, o.lift);
      const ps = [];
      for (let i = 0; i < n; i++) {
        const a = Math.random() * Math.PI * 2;
        const sp = (o.speed || 1) * this.tw * (0.4 + Math.random() * 0.9);
        ps.push({ x: cx, y: cy, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp * 0.6 - (o.rise || 0) * this.tw, c: colors[i % colors.length], r: (o.size || 1) * this.tw * (0.03 + Math.random() * 0.04) });
      }
      const max = o.max || 0.6;
      this.effect(max, (g, k) => {
        for (const p of ps) {
          const t = k * max;
          const px = p.x + p.vx * t;
          const py = p.y + p.vy * t + (o.gravity || 0) * this.tw * t * t;
          g.globalAlpha = 1 - k;
          g.fillStyle = p.c;
          g.beginPath();
          g.arc(px, py, p.r * (1 - k * 0.5), 0, Math.PI * 2);
          g.fill();
        }
        g.globalAlpha = 1;
      });
    }

    // Gold coins that fountain out of a tile, spin in the air and land on the ground around it.
    coins(x, y, n) {
      const [cx, cy] = this.pt(x, y, 14);
      const ground = this.center(x, y)[1];
      const grav = this.tw * 7;
      const cs = [];
      for (let i = 0; i < n; i++) {
        const a = -Math.PI / 2 + (Math.random() - 0.5) * 2;
        const sp = this.tw * (2.4 + Math.random() * 1.2);
        const c = { vx: Math.cos(a) * sp * 0.85, vy: Math.sin(a) * sp, spin: Math.random() * 6, rate: 12 + Math.random() * 8, r: this.tw * (0.09 + Math.random() * 0.03), d: Math.random() * 0.15 };
        const drop = ground + (Math.random() - 0.4) * this.th * 0.6 - cy;
        c.land = (-c.vy + Math.sqrt(c.vy * c.vy + 2 * grav * drop)) / grav;
        cs.push(c);
      }
      const max = 1.4;
      this.effect(max, (g, k) => {
        const T = k * max;
        g.globalAlpha = k > 0.75 ? (1 - k) / 0.25 : 1;
        for (const c of cs) {
          if (T < c.d) continue;
          const t = Math.min(T - c.d, c.land);
          const px = cx + c.vx * t;
          const py = cy + c.vy * t + (grav * t * t) / 2;
          // Spinning in the air: the coin turns edge-on and back. On the ground it lies flat.
          const down = t >= c.land;
          const rx = down ? c.r : c.r * Math.max(0.18, Math.abs(Math.cos(c.spin + c.rate * t)));
          const ry = down ? c.r * 0.55 : c.r;
          g.fillStyle = '#9a6a1c';
          g.beginPath();
          g.ellipse(px, py + c.r * 0.18, rx, ry, 0, 0, Math.PI * 2);
          g.fill();
          g.fillStyle = '#ffcf4a';
          g.beginPath();
          g.ellipse(px, py, rx, ry, 0, 0, Math.PI * 2);
          g.fill();
          g.fillStyle = '#fff3b0';
          g.beginPath();
          g.ellipse(px - rx * 0.3, py - ry * 0.3, rx * 0.35, ry * 0.3, 0, 0, Math.PI * 2);
          g.fill();
        }
        g.globalAlpha = 1;
      });
    }

    ring(x, y, color, radiusTiles, ms, lift) {
      const [cx, cy] = this.center(x, y);
      return this.effect(ms / 1000, (g, k) => {
        g.save();
        g.globalAlpha = 1 - k;
        g.strokeStyle = color;
        g.lineWidth = Math.max(1.5, this.tw * 0.06 * (1 - k));
        g.beginPath();
        g.ellipse(cx, cy - (lift || 0), radiusTiles * this.tw * 0.7 * ease(k) + 2, radiusTiles * this.th * 0.7 * ease(k) + 1, 0, 0, Math.PI * 2);
        g.stroke();
        g.restore();
      });
    }

    flashTiles(tiles, color, ms) {
      return this.effect(ms / 1000, (g, k) => {
        for (const [x, y] of tiles) this.tileFill(g, x, y, color.replace('ALPHA', String(0.55 * (1 - k))), null, 1);
      });
    }

    projectile(from, to, kind, ms) {
      const [x0, y0] = this.pt(from[0], from[1], 24);
      const [x1, y1] = this.pt(to[0], to[1], 16);
      const dist = Math.hypot(x1 - x0, y1 - y0);
      const arc = kind === 'arrow' ? dist * 0.35 : kind === 'rock' ? dist * 0.5 : kind === 'knife' ? dist * 0.08 : dist * 0.35;
      const trail = [];
      return this.effect(ms / 1000, (g, k) => {
        const px = lerp(x0, x1, k);
        const py = lerp(y0, y1, k) - Math.sin(k * Math.PI) * arc;
        const k2 = Math.min(1, k + 0.04);
        const qx = lerp(x0, x1, k2);
        const qy = lerp(y0, y1, k2) - Math.sin(k2 * Math.PI) * arc;
        const ang = Math.atan2(qy - py, qx - px);
        g.save();
        if (kind === 'arrow' || kind === 'knife') {
          g.translate(px, py);
          g.rotate(kind === 'knife' ? k * 20 : ang);
          g.strokeStyle = '#2a1c10';
          g.lineWidth = Math.max(1.2, this.tw * 0.035);
          const L = this.tw * (kind === 'knife' ? 0.12 : 0.28);
          g.beginPath();
          g.moveTo(-L, 0);
          g.lineTo(L * 0.6, 0);
          g.stroke();
          g.fillStyle = '#e8eef5';
          g.beginPath();
          g.moveTo(L, 0);
          g.lineTo(L * 0.55, -L * 0.18);
          g.lineTo(L * 0.55, L * 0.18);
          g.fill();
          if (kind === 'arrow') {
            g.fillStyle = '#e6e0d0';
            g.fillRect(-L, -L * 0.12, L * 0.3, L * 0.24);
          }
        } else {
          trail.push([px, py]);
          if (trail.length > 10) trail.shift();
          const COLS = {
            fire: ['255,150,40', '#ffd27a'], orb: ['255,120,220', '#ffd2f2'], holy: ['255,225,120', '#fff6c8'], frost: ['120,200,255', '#e0f6ff'],
            green: ['110,240,140', '#d8ffe0'], web: ['235,235,235', '#ffffff'], rock: ['150,135,110', '#9a8a70'],
          };
          const col = COLS[kind] || ['170,110,255', '#e0c8ff'];
          for (let i = 0; i < trail.length; i++) {
            const a = i / trail.length;
            g.fillStyle = 'rgba(' + col[0] + ',' + a * 0.5 + ')';
            g.beginPath();
            g.arc(trail[i][0], trail[i][1], this.tw * 0.08 * a, 0, Math.PI * 2);
            g.fill();
          }
          S.glow(g, px, py, this.tw * 0.25, 'rgba(' + col[0] + ',', 0.8);
          g.fillStyle = col[1];
          g.beginPath();
          g.arc(px, py, this.tw * 0.07, 0, Math.PI * 2);
          g.fill();
        }
        g.restore();
      });
    }

    bolt(points, color, ms, width) {
      const pts = points.map(([x, y]) => this.pt(x, y, 18));
      return this.effect(ms / 1000, (g, k) => {
        g.save();
        g.globalAlpha = k < 0.7 ? 1 : 1 - (k - 0.7) / 0.3;
        for (const [w, c] of [[(width || 1) * this.tw * 0.12, color.replace('A', '0.35')], [(width || 1) * this.tw * 0.04, '#ffffff']]) {
          g.strokeStyle = c;
          g.lineWidth = Math.max(1, w);
          g.lineJoin = 'round';
          g.beginPath();
          g.moveTo(pts[0][0], pts[0][1]);
          for (let i = 1; i < pts.length; i++) {
            const [ax, ay] = pts[i - 1];
            const [bx, by] = pts[i];
            for (let j = 1; j <= 3; j++) {
              const t = j / 3;
              const jit = j < 3 ? (Math.random() - 0.5) * this.tw * 0.25 : 0;
              g.lineTo(lerp(ax, bx, t) + jit, lerp(ay, by, t) + jit * 0.5);
            }
          }
          g.stroke();
        }
        g.restore();
      });
    }

    // ---------------------------------------------------------- event playback

    async playEvents(events, state) {
      for (let i = 0; i < events.length; ) {
        const ev = events[i];
        if (ev.t === 'move') {
          await this.animMove(ev);
          i++;
          continue;
        }
        if (ev.t === 'action') {
          const group = [];
          i++;
          while (i < events.length && !['action', 'move', 'turn', 'end', 'done', 'teleport'].includes(events[i].t)) group.push(events[i++]);
          await this.animAction(ev, group, state);
          continue;
        }
        if (ev.t === 'teleport') {
          const v = this.vis.get(ev.uid);
          if (v) {
            v.x = ev.x;
            v.y = ev.y;
            v.facing = ev.facing;
          }
          i++;
          continue;
        }
        const group = [];
        while (i < events.length && !['action', 'move', 'teleport'].includes(events[i].t)) group.push(events[i++]);
        await this.applyImpacts(group, state, true);
      }
    }

    async animMove(ev) {
      const v = this.vis.get(ev.uid);
      if (!v) return;
      v.moving = true;
      const step = this.reduced ? 40 : 135;
      for (let i = 1; i < ev.path.length; i++) {
        const a = ev.path[i - 1];
        const b = ev.path[i];
        const d = AG.Engine.dirFromDelta(b.x - a.x, b.y - a.y);
        if (v.facing >= 0) v.facing = d;
        if (i === 1) this.sfx('step');
        await this.tween(step, (k) => {
          v.x = lerp(a.x, b.x, k);
          v.y = lerp(a.y, b.y, k);
          v.hop = Math.sin(k * Math.PI) * this.tw * (v.type === 'wisp' || v.type === 'dragon' ? 0.02 : 0.08);
        });
      }
      v.x = ev.path[ev.path.length - 1].x;
      v.y = ev.path[ev.path.length - 1].y;
      v.hop = 0;
      v.facing = ev.facing;
      v.moving = false;
    }

    async animAction(ev, group, state) {
      const v = this.vis.get(ev.uid);
      const faceEv = group.find((e) => e.t === 'face' && e.uid === ev.uid);
      if (v && faceEv) v.facing = faceEv.facing;
      const u = state && state.byId[ev.uid];
      const type = u ? u.type : v ? v.type : 'knight';
      const from = [ev.x, ev.y];
      const tgt = ev.target;
      const tiles = ev.tiles || [];
      const fast = this.reduced;
      const dist = tgt ? Math.abs(tgt.x - ev.x) + Math.abs(tgt.y - ev.y) : 0;
      const travel = (d) => (fast ? 120 : 240 + 25 * d);
      const lunge = async (tx, ty) => {
        if (!v) return;
        const [ax, ay] = this.center(v.x, v.y);
        const [bx, by] = this.center(tx, ty);
        await this.tween(fast ? 40 : 110, (k) => {
          v.ox = (bx - ax) * 0.35 * k;
          v.oy = (by - ay) * 0.35 * k;
        });
        const back = this.tween(fast ? 40 : 130, (k) => {
          v.ox = (bx - ax) * 0.35 * (1 - k);
          v.oy = (by - ay) * 0.35 * (1 - k);
        });
        return back;
      };
      // What a ranged single-target act throws.
      const missile = () => {
        if (!ev.dmg) return type === 'spider' ? 'web' : 'hex';
        if (ev.dmg === 'magic') {
          if (type === 'cleric') return 'holy';
          if (type === 'necromancer') return 'green';
          if (type === 'lich' || type === 'specter') return 'frost';
          return 'hex';
        }
        if (type === 'golem' || type === 'golem_king' || type === 'trebuchet') return 'rock';
        if (type === 'scout' || type === 'cutthroat') return 'knife';
        return 'arrow';
      };
      const beam = (x, y, color) => {
        const [cx, cy] = this.center(x, y);
        this.effect(0.6, (g, k) => {
          g.save();
          g.globalAlpha = Math.sin(k * Math.PI) * 0.75;
          const gr = g.createLinearGradient(cx, cy, cx, cy - this.tw * 1.6);
          gr.addColorStop(0, color + '0.85)');
          gr.addColorStop(1, color + '0)');
          g.fillStyle = gr;
          g.fillRect(cx - this.tw * 0.18, cy - this.tw * 1.6, this.tw * 0.36, this.tw * 1.6);
          g.restore();
        });
      };
      switch (ev.kind) {
        case 'strike': {
          if (dist > 1) {
            const m = missile();
            this.sfx(m === 'arrow' ? 'bow' : m === 'knife' ? 'throw' : m === 'rock' ? 'slam' : m === 'holy' ? 'heal' : 'zap');
            await this.projectile(from, [tgt.x, tgt.y], m, travel(dist));
            if (m === 'holy') this.ring(tgt.x, tgt.y, 'rgba(255,230,140,0.9)', 0.8, 320);
            if (m === 'web') this.particles(tgt.x, tgt.y, 8, ['#ffffff', '#dddddd'], { lift: 10, speed: 0.4, max: 0.6 });
            if (m === 'rock') this.particles(tgt.x, tgt.y, 10, ['#a08a6a', '#6f5f48'], { lift: 8, gravity: 2.5, rise: 0.5 });
            await this.applyImpacts(group, state);
          } else {
            this.sfx('swing');
            const back = await lunge(tgt.x, tgt.y);
            if (ev.name === 'Blasting Charge') {
              this.sfx('boom');
              this.shakeT = 0.3;
              this.flashTiles([[tgt.x, tgt.y]], 'rgba(255,150,40,ALPHA)', 420);
              this.particles(tgt.x, tgt.y, 20, ['#ffd27a', '#ff8a2a', '#5a4a3a', '#2a2420'], { lift: 8, rise: 0.9, speed: 1.2, max: 0.8 });
            } else this.slash(tgt.x, tgt.y);
            await this.applyImpacts(group, state);
            await back;
          }
          break;
        }
        case 'cleave':
        case 'quake': {
          this.sfx(ev.kind === 'quake' ? 'slam' : 'swing');
          const back = await lunge(tgt.x, tgt.y);
          if (ev.kind === 'quake') {
            this.shakeT = 0.25;
            this.ring(tgt.x, tgt.y, 'rgba(200,170,120,0.9)', 1.4, 380);
            this.particles(tgt.x, tgt.y, 14, ['#a08a6a', '#6f5f48'], { lift: 2, gravity: 2.5, rise: 0.6 });
          } else {
            for (const [x, y] of tiles) this.slash(x, y);
          }
          await this.applyImpacts(group, state);
          await back;
          break;
        }
        case 'blast': {
          if (ev.dmg === 'phys') {
            const stones = type === 'trebuchet';
            this.sfx(stones ? 'slam' : 'bow');
            await Promise.all(tiles.map((t, i) => this.wait(i * 45).then(() => this.projectile(from, t, stones ? 'rock' : 'arrow', fast ? 120 : 330))));
            this.flashTiles(tiles, 'rgba(255,240,200,ALPHA)', 260);
            if (stones) for (const [x, y] of tiles) this.particles(x, y, 5, ['#a08a6a', '#6f5f48'], { lift: 6, gravity: 2.5, rise: 0.4 });
          } else if (!ev.dmg) {
            this.sfx('grow');
            await this.projectile(from, [tgt.x, tgt.y], 'green', fast ? 150 : 360);
            this.flashTiles(tiles, 'rgba(90,200,80,ALPHA)', 450);
            for (const [x, y] of tiles) this.particles(x, y, 6, ['#5aa046', '#8fd06a', '#3d7f33'], { lift: 4, rise: 0.4, max: 0.6 });
          } else {
            const charm = type === 'enchantress';
            this.sfx(charm ? 'charm' : 'fireball');
            await this.projectile(from, [tgt.x, tgt.y], charm ? 'orb' : 'fire', fast ? 150 : 380);
            if (charm) {
              this.flashTiles(tiles, 'rgba(255,130,220,ALPHA)', 450);
              for (const [x, y] of tiles) this.particles(x, y, 6, ['#ffc4ee', '#ff7ad0', '#fff'], { lift: 10, speed: 0.6, max: 0.7 });
            } else {
              this.sfx('boom');
              this.shakeT = 0.18;
              this.flashTiles(tiles, 'rgba(255,140,40,ALPHA)', 420);
              for (const [x, y] of tiles) this.particles(x, y, 8, ['#ffd27a', '#ff8a2a', '#c4401c'], { lift: 8, rise: 0.5, max: 0.6 });
            }
          }
          await this.applyImpacts(group, state);
          break;
        }
        case 'line': {
          this.sfx('zap');
          const pts = [from].concat(tiles);
          await this.wait(fast ? 20 : 80);
          this.bolt(pts, 'rgba(170,90,255,A)', 380, 1.2);
          this.flashTiles(tiles, 'rgba(160,90,255,ALPHA)', 380);
          await this.wait(fast ? 40 : 120);
          await this.applyImpacts(group, state);
          break;
        }
        case 'cross': {
          this.sfx('zap');
          for (let d = 0; d < 4; d++) {
            const [dx, dy] = DIRS[d];
            const pts = [from];
            for (const t of tiles) if ((t[0] - ev.x) * dy === (t[1] - ev.y) * dx && Math.sign(t[0] - ev.x) === dx && Math.sign(t[1] - ev.y) === dy) pts.push(t);
            if (pts.length > 1) this.bolt(pts, 'rgba(170,90,255,A)', 420, 1);
          }
          this.flashTiles(tiles, 'rgba(160,90,255,ALPHA)', 420);
          await this.wait(fast ? 40 : 160);
          await this.applyImpacts(group, state);
          break;
        }
        case 'cone': {
          // A Lightning Ward's lash: forked bolts to every tile, storm blue.
          if (type === 'lightning') {
            this.sfx('zap');
            for (const t of tiles) this.bolt([from, t], 'rgba(150,210,255,A)', 380, 1);
            this.flashTiles(tiles, 'rgba(140,200,255,ALPHA)', 380);
            await this.wait(fast ? 40 : 140);
            await this.applyImpacts(group, state);
            break;
          }
          this.sfx('breath');
          const [x0, y0] = this.pt(ev.x, ev.y, 30);
          const parts = [];
          for (let i = 0; i < 40; i++) {
            const tt = tiles[i % tiles.length];
            const [x1, y1] = this.pt(tt[0], tt[1], 10);
            parts.push({ x1: x1 + (Math.random() - 0.5) * this.tw * 0.4, y1: y1 + (Math.random() - 0.5) * this.th * 0.4, d: Math.random() * 0.4, c: ['#ffd27a', '#ff8a2a', '#e04a1c'][i % 3] });
          }
          await this.effect(fast ? 0.15 : 0.5, (g, k) => {
            for (const p of parts) {
              const t = Math.max(0, Math.min(1, (k - p.d) / 0.6));
              if (t <= 0) continue;
              g.globalAlpha = 1 - t * 0.6;
              g.fillStyle = p.c;
              g.beginPath();
              g.arc(lerp(x0, p.x1, t), lerp(y0, p.y1, t), this.tw * (0.05 + t * 0.1), 0, Math.PI * 2);
              g.fill();
            }
            g.globalAlpha = 1;
          });
          this.flashTiles(tiles, 'rgba(255,120,30,ALPHA)', 380);
          await this.applyImpacts(group, state);
          break;
        }
        case 'nova':
        case 'detonate': {
          const r = Math.max(...tiles.map(([x, y]) => Math.abs(x - ev.x) + Math.abs(y - ev.y)), 1);
          if (ev.kind === 'detonate') {
            this.sfx('boom');
            this.shakeT = 0.3;
            this.flashTiles(tiles.concat([[ev.x, ev.y]]), 'rgba(255,150,40,ALPHA)', 480);
            this.particles(ev.x, ev.y, 26, ['#ffd27a', '#ff8a2a', '#5a4a3a', '#2a2420'], { lift: 8, rise: 0.9, speed: 1.3, max: 0.8 });
          } else if (ev.dmg === 'phys') {
            this.sfx('slam');
            this.shakeT = 0.22;
            this.ring(ev.x, ev.y, 'rgba(200,170,120,0.9)', r + 0.6, 380);
            this.particles(ev.x, ev.y, 14, ['#a08a6a', '#6f5f48'], { lift: 2, gravity: 2.5, rise: 0.6 });
          } else if (!ev.dmg && type !== 'wisp') {
            this.sfx('enemyturn');
            this.ring(ev.x, ev.y, 'rgba(255,90,70,0.95)', r + 0.3, 520);
            this.wait(120).then(() => this.ring(ev.x, ev.y, 'rgba(255,150,120,0.7)', r * 0.6 + 0.3, 420));
          } else if (type === 'wisp') {
            this.sfx('poison');
            this.ring(ev.x, ev.y, 'rgba(255,111,220,0.9)', r + 0.3, 420);
            for (const [x, y] of tiles) if (Math.random() < 0.6) this.particles(x, y, 3, POISON_FX, { lift: 4, rise: 0.4, speed: 0.3, max: 0.8 });
          } else {
            this.sfx('zap');
            this.ring(ev.x, ev.y, 'rgba(255,225,90,0.95)', r + 0.3, 420);
            const targets = group.filter((e) => e.t === 'dmg').map((e) => state.byId[e.uid]).filter(Boolean);
            for (const t of targets) this.bolt([from, [t.x, t.y]], 'rgba(255,220,80,A)', 300, 0.9);
          }
          await this.wait(fast ? 40 : 200);
          await this.applyImpacts(group, state);
          break;
        }
        case 'pray':
        case 'drum':
        case 'rally': {
          const drum = ev.kind === 'drum';
          this.sfx(drum ? 'slam' : 'heal');
          if (v && !drum) beam(v.x, v.y, ev.kind === 'rally' ? 'rgba(255,200,90,' : 'rgba(255,230,140,');
          const col = drum ? 'rgba(255,90,60,0.9)' : ev.kind === 'rally' ? 'rgba(255,200,90,0.95)' : 'rgba(255,230,140,0.9)';
          this.ring(ev.x, ev.y, col, 2.5, 500);
          if (drum) this.wait(fast ? 60 : 220).then(() => (this.sfx('slam'), this.ring(ev.x, ev.y, col, 2.5, 500)));
          await this.wait(fast ? 40 : 260);
          await this.applyImpacts(group, state);
          break;
        }
        case 'heal':
        case 'revive': {
          this.sfx('heal');
          beam(tgt.x, tgt.y, 'rgba(255,230,140,');
          this.particles(tgt.x, tgt.y, 10, ['#fff3b0', '#ffe08a', '#ffffff'], { lift: 10, rise: 0.8, speed: 0.3, max: 0.8 });
          await this.wait(fast ? 40 : 260);
          await this.applyImpacts(group, state);
          break;
        }
        case 'shield': {
          this.sfx('charm');
          this.ring(tgt.x, tgt.y, 'rgba(140,200,255,0.95)', 0.9, 420, 20 * this.unit);
          await this.wait(fast ? 30 : 200);
          await this.applyImpacts(group, state);
          break;
        }
        case 'hazard': {
          const self = tgt.x === ev.x && tgt.y === ev.y;
          if (ev.hz === 'fire') {
            this.sfx('fireball');
            if (!self) await this.projectile(from, [tgt.x, tgt.y], 'fire', fast ? 150 : 360);
            for (const [x, y] of tiles) this.particles(x, y, 6, ['#ffd27a', '#ff8a2a'], { lift: 4, rise: 0.8, max: 0.6 });
          } else if (ev.hz === 'caltrops') {
            this.sfx('throw');
            await this.projectile(from, [tgt.x, tgt.y], 'knife', fast ? 120 : 280);
          } else {
            this.sfx('throw');
            if (!self) await this.projectile(from, [tgt.x, tgt.y], 'web', fast ? 120 : 300);
            for (const [x, y] of tiles) this.particles(x, y, 8, ['#d8dce4', '#b8bcc6', '#ffffff'], { lift: 8, rise: 0.3, speed: 0.6, max: 0.9, size: 2 });
          }
          await this.applyImpacts(group, state);
          break;
        }
        case 'grow':
        case 'raise': {
          this.sfx('grow');
          const raise = ev.kind === 'raise';
          if (raise) beam(tgt.x, tgt.y, 'rgba(110,255,140,');
          this.particles(tgt.x, tgt.y, 10, raise ? ['#9dffad', '#5fd17a', '#d8ffe0'] : ['#5aa046', '#8fd06a', '#3d7f33'], { lift: 4, rise: 0.5, max: 0.6 });
          await this.wait(fast ? 20 : 120);
          await this.applyImpacts(group, state);
          break;
        }
        case 'leap': {
          const le = group.find((e) => e.t === 'leap');
          if (v && le) {
            this.sfx('step');
            v.moving = true;
            await this.tween(fast ? 120 : 360, (k) => {
              v.x = lerp(le.fx, le.x, k);
              v.y = lerp(le.fy, le.y, k);
              v.hop = Math.sin(k * Math.PI) * this.tw * 0.6;
            });
            v.x = le.x;
            v.y = le.y;
            v.hop = 0;
            v.moving = false;
            this.sfx('slam');
            this.shakeT = 0.15;
            this.particles(le.x, le.y, 10, ['#a08a6a', '#6f5f48'], { lift: 2, gravity: 2.5, rise: 0.5 });
          }
          for (const [x, y] of tiles.slice(1)) if (state && state.units.some((o) => o.x === x && o.y === y && o.team !== (u && u.team))) this.slash(x, y);
          await this.applyImpacts(group, state);
          break;
        }
        case 'blink':
        case 'shadowstrike': {
          const be = group.find((e) => e.t === 'blink');
          if (v && be) {
            this.sfx('charm');
            this.particles(be.fx, be.fy, 10, ['#c9b6ff', '#8f6cff', '#ffffff'], { lift: 14, speed: 0.6, max: 0.5 });
            await this.tween(fast ? 60 : 140, (k) => (v.alpha = 1 - k));
            v.x = be.x;
            v.y = be.y;
            this.particles(be.x, be.y, 10, ['#c9b6ff', '#8f6cff', '#ffffff'], { lift: 14, speed: 0.6, max: 0.5 });
            await this.tween(fast ? 60 : 140, (k) => (v.alpha = k));
            v.alpha = 1;
          }
          if (ev.kind === 'shadowstrike') {
            this.sfx('swing');
            const back = await lunge(tgt.x, tgt.y);
            this.slash(tgt.x, tgt.y);
            await this.applyImpacts(group, state);
            await back;
          } else await this.applyImpacts(group, state);
          break;
        }
        default:
          await this.applyImpacts(group, state);
      }
      await this.wait(fast ? 60 : 220);
    }

    slash(x, y) {
      const [cx, cy] = this.pt(x, y, 20);
      this.effect(0.22, (g, k) => {
        g.save();
        g.globalAlpha = 1 - k;
        g.strokeStyle = '#fff6d8';
        g.lineWidth = Math.max(1.5, this.tw * 0.05);
        g.beginPath();
        g.arc(cx, cy, this.tw * 0.28, -2.4 + k * 1.2, -0.6 + k * 1.2);
        g.stroke();
        g.restore();
      });
    }

    // Apply damage numbers, deaths, heals and statuses for a group of events.
    async applyImpacts(group, state, standalone) {
      let any = false;
      const STATUS_TEXT = {
        para: ['PARALYZED', '#ffd84a'], poison: ['POISONED', POISON], burn: ['BURNING', '#ffb060'], root: ['ROOTED', '#8fe07a'],
        weak: ['WEAKENED', '#c8a8ff'], mark: ['MARKED', '#ff8a7a'], frenzy: ['FRENZY', '#ff7a5a'],
      };
      for (const e of group) {
        const v = this.vis.get(e.uid);
        const h = v ? (S.HEIGHT[v.type] || 40) * (v.scale || 1) : 40;
        switch (e.t) {
          case 'face':
            if (v) v.facing = e.facing;
            break;
          case 'dmg': {
            if (!v) break;
            any = true;
            v.hp = Math.max(0, v.hp - e.amount);
            v.shake = 1;
            setTimeout(() => (v.shake = 0), 220);
            const col = e.dmgType === 'magic' ? '#d7b4ff' : e.dmgType === 'poison' ? POISON : e.dmgType === 'burn' ? '#ffb060' : e.dmgType === 'true' ? '#ffb0a0' : e.dmgType === 'fatigue' ? '#ffd27a' : '#ffffff';
            // Damage counts down (-6), healing up (+6), so the two never look alike.
            this.addText(v.x, v.y, '-' + e.amount, col, { height: h, big: e.amount >= 25 });
            if (e.cat === 'back' && e.dmgType === 'phys') {
              const src = state && state.byId[e.src];
              const stab = src && src.props && src.props.backMult;
              this.addText(v.x, v.y, stab ? 'BACKSTAB' : 'FROM BEHIND', '#ffcf6a', { height: h, dy: -this.tw * 0.28, max: 0.9 });
            }
            this.sfx(e.dmgType === 'poison' ? 'poison' : e.dmgType === 'magic' || e.dmgType === 'burn' ? 'magichit' : 'hit');
            if (e.dmgType === 'poison') this.particles(v.x, v.y, 7, POISON_FX, { lift: 14, rise: 0.4, speed: 0.3, max: 0.7 });
            if (e.dmgType === 'burn') this.particles(v.x, v.y, 5, ['#ffd27a', '#ff8a2a'], { lift: 14, rise: 0.6, speed: 0.3, max: 0.6 });
            break;
          }
          case 'block':
            if (!v) break;
            any = true;
            this.addText(v.x, v.y, 'BLOCK', '#a9d1ff', { height: h });
            this.sfx('block');
            this.particles(v.x, v.y, 6, ['#ffffff', '#cfe3ff'], { lift: 18, speed: 0.6, max: 0.35 });
            break;
          case 'absorb':
            if (!v) break;
            any = true;
            v.shield = e.left;
            this.addText(v.x, v.y, 'SHIELD -' + e.amount, '#8cc8ff', { height: h });
            this.sfx('block');
            break;
          case 'shield':
            if (v) {
              v.shield = e.amount;
              this.addText(v.x, v.y, 'SHIELD ' + e.amount, '#8cc8ff', { height: h, dy: -this.tw * 0.25 });
            }
            break;
          case 'heal':
            if (!v) break;
            any = true;
            v.hp = Math.min(v.maxHp, v.hp + e.amount);
            this.addText(v.x, v.y, '+' + e.amount, '#8ef08e', { height: h, dy: e.why === 'drain' ? this.tw * 0.15 : 0 });
            if (e.why !== 'drain') this.particles(v.x, v.y, 6, ['#b7ffb0', '#6fdc6f', '#fff3b0'], { lift: 10, rise: 0.8, speed: 0.25, max: 0.8 });
            break;
          case 'healblock':
            if (v) this.addText(v.x, v.y, 'NO HEAL', POISON, { height: h, max: 0.9 });
            break;
          case 'noregen':
            if (v) this.addText(v.x, v.y, 'NO REGEN', '#ffb060', { height: h, max: 0.9 });
            break;
          case 'status': {
            if (!v) break;
            const st = STATUS_TEXT[e.status];
            if (e.status === 'para') v.para = e.turns;
            else if (e.status === 'poison') v.poison = true;
            else if (e.status === 'burn') v.burn = true;
            else v[e.status] = e.turns;
            if (st) this.addText(v.x, v.y, st[0], st[1], { height: h, dy: -this.tw * 0.25 });
            break;
          }
          case 'resist':
            if (v) this.addText(v.x, v.y, e.why === 'steady' ? 'STEADY' : 'IMMUNE', '#e8e2d0', { height: h, dy: -this.tw * 0.25 });
            break;
          case 'cleanse':
            if (v) {
              v.para = 0;
              v.poison = false;
              v.burn = false;
              v.root = 0;
              this.addText(v.x, v.y, 'CURED', '#fff3b0', { height: h, dy: -this.tw * 0.25 });
            }
            break;
          case 'cure':
            if (v) {
              if (e.status === 'burn') v.burn = false;
              else v.poison = false;
            }
            break;
          case 'rally':
            if (v) {
              v.wait = e.wait;
              v.para = 0;
              v.root = 0;
              this.addText(v.x, v.y, 'RALLY', '#ffd86a', { height: h, dy: -this.tw * 0.25 });
            }
            break;
          case 'death': {
            if (!v) break;
            any = true;
            v.dying = true;
            const mat = UNITS[v.type] && UNITS[v.type].material;
            if (mat && v.type !== 'barrel') {
              // A building comes down in a cloud of rubble, splinters or sparks.
              this.sfx('crumble');
              this.shakeT = Math.max(this.shakeT, 0.22);
              const bits = mat === 'wood' ? ['#8a5a30', '#5a3d22', '#c9a26a'] : mat === 'arcane' ? ['#b98cff', '#5a2a8a', '#ecdcff'] : ['#9a958c', '#6d6a64', '#c9c3b8'];
              this.particles(v.x, v.y, 22, bits, { lift: 14, gravity: 2.2, rise: 0.7, speed: 1, max: 0.9 });
            } else this.sfx('death');
            this.particles(v.x, v.y, 12, ['#b9b2a8', '#7f786f', '#e8e2d8'], { lift: 12, rise: 0.4, speed: 0.6, max: 0.7 });
            this.tween(450, (k) => {
              v.alpha = 1 - k;
              v.oy = k * this.tw * 0.08;
            }).then(() => {
              if (v.dying) this.vis.delete(e.uid);
            });
            break;
          }
          case 'waveWarn':
            if (e.marks && e.marks.length) {
              this.flashTiles(e.marks, 'rgba(255,90,60,ALPHA)', 600);
              this.addText(e.marks[0][0], e.marks[0][1], 'INCOMING', '#ff9a8a', { height: 20 });
            }
            break;
          case 'wave': {
            any = true;
            this.sfx('horn');
            const src = state && state.byId[e.src];
            if (src) this.ring(src.x, src.y, 'rgba(255,120,90,0.9)', 1.2, 420);
            for (const id of e.uids || []) {
              const u = state && state.byId[id];
              if (!u || this.vis.has(id)) continue;
              const nv = this.makeVis(u);
              nv.alpha = 0;
              nv.oy = -this.tw * 0.4;
              this.vis.set(id, nv);
              this.particles(u.x, u.y, 10, ['#c9b9a0', '#8a7a64', '#e8dcc8'], { lift: 2, rise: 0.5, speed: 0.7, max: 0.6 });
              this.tween(this.reduced ? 60 : 380, (k) => {
                nv.alpha = k;
                nv.oy = -this.tw * 0.4 * (1 - ease(k));
              });
            }
            const first = (e.uids || []).map((id) => state && state.byId[id]).find(Boolean);
            const spot = first || src;
            if (spot) this.addText(spot.x, spot.y, 'REINFORCEMENTS', '#ff9a8a', { height: 40, big: true });
            await this.wait(this.reduced ? 60 : 380);
            break;
          }
          case 'spawnBlock':
            if (v) {
              any = true;
              this.sfx('block');
              this.addText(v.x, v.y, 'BLOCKED', '#ffd86a', { height: h, dy: -this.tw * 0.3, big: true });
              this.ring(v.x, v.y, 'rgba(255,216,106,0.95)', 0.9, 360);
            }
            break;
          case 'waveCancel': {
            const u = state && state.byId[e.uid];
            if (u) {
              any = true;
              this.addText(u.x, u.y, 'CUT OFF', '#ffd86a', { height: 40, dy: -this.tw * 0.3 });
            }
            break;
          }
          case 'totem':
            if (v) this.ring(v.x, v.y, 'rgba(255,130,90,0.85)', 2.4, 520);
            break;
          case 'revive': {
            const u = state && state.byId[e.uid];
            let rv = v;
            if (!rv && u) {
              rv = this.makeVis(u);
              this.vis.set(u.uid, rv);
            }
            if (rv) {
              rv.dying = false;
              rv.alpha = 1;
              rv.oy = 0;
              rv.hp = e.hp;
              this.addText(rv.x, rv.y, e.why === 'phoenix' ? 'REBORN' : 'RISEN', '#ffcf6a', { height: h, big: true });
              this.particles(rv.x, rv.y, 16, ['#ffcf6a', '#ff8a2a', '#fff'], { lift: 10, rise: 1, max: 0.9 });
              any = true;
            }
            break;
          }
          case 'secondwind':
            if (v) this.addText(v.x, v.y, 'SECOND WIND', '#ffcf6a', { height: h, dy: -this.tw * 0.25 });
            break;
          case 'thorns':
            if (v) this.addText(v.x, v.y, 'THORNS', '#ffb0a0', { height: h, dy: -this.tw * 0.25, max: 0.8 });
            break;
          case 'retaliate': {
            const t = state && state.byId[e.target];
            if (v && t) {
              this.addText(v.x, v.y, 'COUNTER', '#ffcf6a', { height: h, dy: -this.tw * 0.25, max: 0.8 });
              const [ax, ay] = this.center(v.x, v.y);
              const [bx, by] = this.center(t.x, t.y);
              await this.tween(100, (k) => {
                v.ox = (bx - ax) * 0.3 * k;
                v.oy = (by - ay) * 0.3 * k;
              });
              this.slash(t.x, t.y);
              this.tween(120, (k) => {
                v.ox = (bx - ax) * 0.3 * (1 - k);
                v.oy = (by - ay) * 0.3 * (1 - k);
              });
            }
            break;
          }
          case 'push':
            if (v) {
              const x0 = v.x;
              const y0 = v.y;
              // A pull: the hook's chain (or the web, or the dark hand) reels it in.
              const by = e.pull && this.vis.get(e.by);
              if (by) {
                const [ax, ay] = this.pt(by.x, by.y, 18);
                this.sfx('throw');
                this.effect(this.reduced ? 0.06 : 0.22, (g, k) => {
                  const [bx, bY] = this.pt(v.x, v.y, 18);
                  g.save();
                  g.globalAlpha = 1 - k * 0.7;
                  g.strokeStyle = '#d6d9e2';
                  g.lineWidth = Math.max(1.5, this.tw * 0.035);
                  g.setLineDash([this.tw * 0.07, this.tw * 0.045]);
                  g.beginPath();
                  g.moveTo(ax, ay);
                  g.lineTo(bx, bY);
                  g.stroke();
                  g.restore();
                });
              }
              v.moving = true;
              await this.tween(this.reduced ? 40 : 170, (k) => {
                v.x = lerp(x0, e.x, k);
                v.y = lerp(y0, e.y, k);
              });
              v.x = e.x;
              v.y = e.y;
              v.moving = false;
              any = true;
            }
            break;
          case 'slam':
            if (v) {
              this.sfx('slam');
              this.shakeT = Math.max(this.shakeT, 0.12);
              this.addText(v.x, v.y, 'SLAM', '#ffb0a0', { height: h, dy: -this.tw * 0.25, max: 0.8 });
              this.particles(v.x, v.y, 8, ['#d9c7a0', '#8f7c5c'], { lift: 8, speed: 0.6, max: 0.45 });
            }
            break;
          // Shoved into another unit: a thud, dust between them, and both reel.
          case 'crash': {
            const o = this.vis.get(e.other);
            this.sfx('slam');
            this.shakeT = Math.max(this.shakeT, 0.14);
            if (v) this.addText(v.x, v.y, 'CRASH', '#ffb0a0', { height: h, dy: -this.tw * 0.25, max: 0.8 });
            if (v && o) this.particles((v.x + o.x) / 2, (v.y + o.y) / 2, 10, ['#d9c7a0', '#a08c6a', '#ffffff'], { lift: 12, speed: 0.7, max: 0.5 });
            if (o) {
              o.shake = 1;
              setTimeout(() => (o.shake = 0), 220);
            }
            any = true;
            break;
          }
          // Shoved into water or lava: the splash, a moment under, then it climbs out.
          case 'splash':
            if (v) {
              const cols = e.lava ? ['#ff9a3c', '#ffd36a', '#c4361b'] : ['#d8f0ff', '#7cc0ff', '#ffffff'];
              this.sfx(e.lava ? 'sizzle' : 'splash');
              this.particles(v.x, v.y, 16, cols, { lift: 2, rise: 0.9, speed: 0.9, max: 0.7, gravity: 1.4 });
              this.ring(v.x, v.y, e.lava ? 'rgba(255,140,60,0.9)' : 'rgba(170,220,255,0.9)', 0.7, 420, 0);
              this.addText(v.x, v.y, e.lava ? 'INTO THE LAVA' : 'SPLASH', e.lava ? '#ffb070' : '#a8dcff', { height: h, dy: -this.tw * 0.55, max: 0.9 });
              v.dunk = true;
              await this.tween(this.reduced ? 40 : 260, () => {});
              any = true;
            }
            break;
          case 'climb':
            if (v) {
              const x0 = v.x;
              const y0 = v.y;
              v.moving = true;
              v.dunk = false;
              await this.tween(this.reduced ? 40 : 240, (k) => {
                v.x = lerp(x0, e.x, k);
                v.y = lerp(y0, e.y, k);
              });
              v.x = e.x;
              v.y = e.y;
              v.moving = false;
              any = true;
            }
            break;
          case 'leap':
          case 'blink':
            if (v && !v.moving) {
              v.x = e.x;
              v.y = e.y;
            }
            break;
          case 'summon': {
            const u = state && state.byId[e.uid];
            if (u) {
              const nv = this.makeVis(u);
              nv.scale = 0.2;
              this.vis.set(u.uid, nv);
              this.tween(260, (k) => (nv.scale = 0.2 + 0.8 * ease(k)));
              if (e.raise) this.particles(u.x, u.y, 10, ['#9dffad', '#e6dfc9'], { lift: 2, rise: 0.8, max: 0.7 });
            }
            break;
          }
          case 'wither':
            if (v) {
              v.dying = true;
              if (e.crumble) this.particles(v.x, v.y, 10, ['#e6dfc9', '#b9b19a'], { lift: 10, gravity: 2.5, speed: 0.6, max: 0.6 });
              this.tween(300, (k) => (v.alpha = 1 - k)).then(() => this.vis.delete(e.uid));
            }
            break;
          case 'hazard':
            for (const [x, y] of e.tiles || []) {
              this.tfx = this.tfx.filter((f) => !(f.x === x && f.y === y && f.kind === e.kind));
              this.tfx.push({ kind: e.kind, x, y, team: e.team });
            }
            break;
          case 'trap':
            this.tfx = this.tfx.filter((f) => !(f.x === e.x && f.y === e.y && f.kind === 'caltrops'));
            if (v) {
              any = true;
              this.sfx('hit');
              this.addText(v.x, v.y, 'CALTROPS', '#ffb0a0', { height: h, dy: -this.tw * 0.25 });
            }
            break;
          case 'scorch':
            if (v) this.particles(v.x, v.y, 6, ['#ffd27a', '#ff8a2a', '#c4401c'], { lift: 6, rise: 0.8, max: 0.5 });
            break;
          case 'boom':
            any = true;
            this.sfx('boom');
            this.shakeT = 0.32;
            this.flashTiles(e.tiles || [[e.x, e.y]], 'rgba(255,150,40,ALPHA)', 480);
            this.ring(e.x, e.y, 'rgba(255,200,120,0.95)', 1.5, 420);
            this.particles(e.x, e.y, 24, ['#ffd27a', '#ff8a2a', '#5a4a3a', '#2a2420'], { lift: 8, rise: 0.9, speed: 1.3, max: 0.8 });
            await this.wait(this.reduced ? 40 : 160);
            break;
          case 'escape':
            if (v) {
              any = true;
              v.dying = true;
              this.addText(e.x, e.y, 'ESCAPED', '#ffd86a', { height: h, big: true });
              const x0 = v.x;
              await this.tween(this.reduced ? 60 : 380, (k) => {
                v.x = x0 - k * 1.2;
                v.alpha = 1 - k;
              });
              this.vis.delete(e.uid);
            }
            break;
          case 'zap': {
            const src = state && state.byId[e.uid];
            if (src) {
              this.sfx('zap');
              for (const id of e.targets || []) {
                const t = state.byId[id];
                if (t) this.bolt([[src.x, src.y], [t.x, t.y]], 'rgba(150,200,255,A)', 260, 0.8);
              }
            }
            break;
          }
          // A unit whose turn came but who passes it: cooling down (its cooldown ticks down),
          // paralyzed, or with nothing in reach. The Barrier Ward, which never acts, passes quietly.
          case 'gold': {
            const gx = v ? v.x : e.x;
            const gy = v ? v.y : e.y;
            if (gx == null) break;
            this.sfx('coin');
            this.addText(gx, gy, '+' + e.amount + ' GOLD', '#ffd86a', { height: h, dy: -this.tw * 0.3, big: !!e.coins });
            // A broken barricade spills its coins.
            if (e.coins) {
              any = true;
              this.coins(gx, gy, Math.min(14, 4 + Math.round(e.amount / 2)));
              this.particles(gx, gy, 10, ['#fff3b0', '#ffd86a'], { lift: 14, rise: 0.6, speed: 0.9, max: 0.6 });
              this.ring(gx, gy, 'rgba(255,215,100,0.9)', 0.9, 380, 6);
            }
            break;
          }
          case 'done':
            if (v) {
              v.wait = e.wait;
              v.activated = true;
            }
            break;
          case 'loot': {
            const l = this.loot.find((k) => k.id === e.id);
            if (l) l.taken = true;
            any = true;
            this.sfx('coin');
            this.addText(e.x, e.y, { chest: 'WAR CHEST', tome: 'LOST TOME', relic: 'RELIC' }[e.kind] || 'LOOT', '#ffd86a', { height: h, big: true });
            this.particles(e.x, e.y, 16, ['#ffe08a', '#ffcf4a', '#ffffff', '#c9a0ff'], { lift: 10, rise: 0.9, max: 0.9 });
            break;
          }
          case 'hold':
            if (this.hold) {
              this.hold.count = e.count;
              if (e.count > 0) {
                any = true;
                this.addText(this.hold.x, this.hold.y, 'SHRINE ' + e.count + '/' + e.need, '#ffe3a0', { height: 30 });
              }
            }
            break;
        }
      }
      if (standalone && any) await this.wait(450);
    }
  }

  // Small static portrait of a unit for cards and lists.
  function portrait(canvas, type, team, opts) {
    const o = opts || {};
    const dpr = Math.min(root.devicePixelRatio || 1, 3);
    const w = canvas.clientWidth || +canvas.getAttribute('width') || 56;
    const h = canvas.clientHeight || +canvas.getAttribute('height') || 56;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    const g = canvas.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    const hgt = S.HEIGHT[type] || 40;
    const span = Math.max(hgt + 10, 54);
    const sc = Math.min(h / span, w / 50) * (o.zoom || 1);
    const cx = w / 2;
    const cy = h - 6 * sc;
    const tc = S.TEAMS[team] || S.TEAMS.P;
    if (type !== 'shrub') {
      g.fillStyle = tc.glow + '0.22)';
      g.strokeStyle = tc.ring;
      g.lineWidth = Math.max(1.2, sc * 1.4);
      g.beginPath();
      g.ellipse(cx, cy, 14 * sc, 6 * sc, 0, 0, Math.PI * 2);
      g.fill();
      g.stroke();
    }
    g.save();
    g.translate(cx, cy);
    g.scale(team === 'E' ? -sc : sc, sc);
    if (o.gray) g.filter = 'grayscale(0.8) brightness(0.8)';
    S.drawUnit(g, type, team, 'front', o.t || 1.1, null);
    g.restore();
  }

  // A whole army as one picture, facing you like a team photo: its front line nearest and
  // largest, the rows behind it stepping back (every other one half a tile over, so a unit
  // right behind another still shows), each unit where it stood from left to right.
  // `units`: [{ type, x, y }], with smaller y nearer the front, as on the field.
  function formation(canvas, units, opts) {
    const o = opts || {};
    const dpr = Math.min(root.devicePixelRatio || 1, 2);
    const w = o.w || canvas.clientWidth || 300;
    const h = o.h || canvas.clientHeight || 90;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    const g = canvas.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    if (!units.length) return;
    const xs = units.map((u) => u.x);
    const x0 = Math.min(...xs);
    const cols = Math.max(...xs) - x0 + 1;
    const ys = [...new Set(units.map((u) => u.y))].sort((a, b) => a - b);
    const depth = (u) => ys.indexOf(u.y);
    const step = 22;
    const front = h - 9;
    const cell = Math.min(40, (w - 16) / (cols + (ys.length > 1 ? 0.5 : 0)));
    const tallest = Math.max(...units.map((u) => S.HEIGHT[u.type] || 40));
    const sc = Math.min(cell / 24, (h - 12 - (ys.length - 1) * step) / tallest);
    const left = (w - cell * (cols + (ys.length > 1 ? 0.5 : 0))) / 2;
    // The ground they stand on.
    const gy = front - ((ys.length - 1) * step) / 2;
    const ground = g.createRadialGradient(w / 2, gy, 4, w / 2, gy, w / 2);
    ground.addColorStop(0, 'rgba(110, 165, 74, 0.5)');
    ground.addColorStop(1, 'rgba(110, 165, 74, 0)');
    g.fillStyle = ground;
    g.beginPath();
    g.ellipse(w / 2, gy, w / 2 - 2, ((ys.length - 1) * step) / 2 + 14, 0, 0, Math.PI * 2);
    g.fill();
    // Back rows first, so the front line stands in front of them.
    const order = units.map((u, i) => ({ u, i })).sort((a, b) => depth(b.u) - depth(a.u) || a.u.x - b.u.x);
    for (const { u, i } of order) {
      const d = depth(u);
      const k = 1 - 0.1 * d;
      const cx = w / 2 + (left + (u.x - x0 + 0.5 + (d % 2) * 0.5) * cell - w / 2) * (1 - 0.05 * d);
      const cy = front - d * step;
      g.fillStyle = 'rgba(0, 0, 0, 0.35)';
      g.beginPath();
      g.ellipse(cx, cy, 11 * sc * k, 4 * sc * k, 0, 0, Math.PI * 2);
      g.fill();
      g.save();
      g.translate(cx, cy);
      g.scale(sc * k, sc * k);
      S.drawUnit(g, u.type, u.team || 'P', 'front', 1.1 + i * 0.37, null);
      g.restore();
    }
  }

  AG.Render = { Board, PALETTES, portrait, formation };
})(typeof window !== 'undefined' ? window : globalThis);
